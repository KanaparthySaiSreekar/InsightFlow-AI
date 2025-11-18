from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
import json
from app.db.database import get_db
from app.models.user import User
from app.models.project import Project
from app.models.chat import Chat
from app.models.message import Message
from app.models.llm_config import LLMConfig
from app.schemas.chat import (
    ChatCreate,
    ChatResponse,
    MessageCreate,
    MessageResponse,
    ChatQueryRequest,
    ChatQueryResponse,
)
from app.core.deps import get_current_user
from app.core.security import decrypt_api_key
from app.services.duckdb_manager import DuckDBManager
from app.services.llm_service import LLMService

router = APIRouter(prefix="/chat", tags=["Chat"])


@router.post("/", response_model=ChatResponse, status_code=status.HTTP_201_CREATED)
def create_chat(
    chat_data: ChatCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Create a new chat session."""
    # Verify project belongs to user
    project = (
        db.query(Project)
        .filter(Project.id == chat_data.project_id, Project.user_id == current_user.id)
        .first()
    )

    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found",
        )

    # Create chat
    new_chat = Chat(
        user_id=current_user.id,
        project_id=chat_data.project_id,
        title=chat_data.title or "New Chat",
    )

    db.add(new_chat)
    db.commit()
    db.refresh(new_chat)

    return new_chat


@router.get("/", response_model=List[ChatResponse])
def get_chats(
    project_id: int = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get all chats for the current user, optionally filtered by project."""
    query = db.query(Chat).filter(Chat.user_id == current_user.id)

    if project_id:
        query = query.filter(Chat.project_id == project_id)

    chats = query.order_by(Chat.updated_at.desc()).all()
    return chats


@router.get("/{chat_id}", response_model=ChatResponse)
def get_chat(
    chat_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get a specific chat with all messages."""
    chat = (
        db.query(Chat)
        .filter(Chat.id == chat_id, Chat.user_id == current_user.id)
        .first()
    )

    if not chat:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chat not found",
        )

    return chat


@router.post("/query", response_model=ChatQueryResponse)
def query_data(
    query_data: ChatQueryRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Send a query to the chatbot and get a response."""
    # Get chat
    chat = (
        db.query(Chat)
        .filter(Chat.id == query_data.chat_id, Chat.user_id == current_user.id)
        .first()
    )

    if not chat:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chat not found",
        )

    # Get project
    project = db.query(Project).filter(Project.id == chat.project_id).first()

    # Get active LLM config
    llm_config = (
        db.query(LLMConfig)
        .filter(LLMConfig.user_id == current_user.id, LLMConfig.is_active == 1)
        .first()
    )

    if not llm_config:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No active LLM configuration. Please configure your API key.",
        )

    # Store user message
    user_message = Message(
        chat_id=chat.id,
        role="user",
        content=query_data.query,
    )
    db.add(user_message)
    db.commit()

    try:
        # Decrypt API key
        api_key = decrypt_api_key(llm_config.encrypted_api_key)
        llm_service = LLMService(llm_config.provider, api_key)

        # Get schema
        schema_json = json.loads(project.schema_json) if project.schema_json else {}

        # Get chat history (last 5 messages)
        chat_history = []
        previous_messages = (
            db.query(Message)
            .filter(Message.chat_id == chat.id)
            .order_by(Message.created_at.desc())
            .limit(5)
            .all()
        )
        for msg in reversed(previous_messages):
            chat_history.append({"role": msg.role, "content": msg.content})

        # Generate SQL
        sql_result = llm_service.text_to_sql(query_data.query, schema_json, chat_history)

        if not sql_result["success"]:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to generate SQL: {sql_result.get('error')}",
            )

        sql_query = sql_result["sql"]

        # Execute SQL
        with DuckDBManager(project.duckdb_file_path) as duck_db:
            query_result = duck_db.execute_query(sql_query)

            # If SQL fails, try to fix it
            if not query_result["success"]:
                fix_result = llm_service.fix_sql_error(
                    sql_query, query_result["error"], schema_json
                )

                if fix_result["success"]:
                    sql_query = fix_result["sql"]
                    query_result = duck_db.execute_query(sql_query)

            if not query_result["success"]:
                # Store error message
                assistant_message = Message(
                    chat_id=chat.id,
                    role="assistant",
                    content=f"I encountered an error: {query_result['error']}",
                    sql_query=sql_query,
                    error_message=query_result["error"],
                )
                db.add(assistant_message)
                db.commit()
                db.refresh(assistant_message)

                return ChatQueryResponse(
                    message=assistant_message,
                    data=None,
                    visualization_type=None,
                )

            # Interpret results
            interpret_result = llm_service.interpret_results(
                query_data.query, sql_query, query_result["data"]
            )

            interpretation = interpret_result.get("interpretation", {})
            answer = interpretation.get("answer", f"Found {query_result['row_count']} results.")
            viz_type = interpretation.get("visualization_type", "table")

            # Store assistant message
            assistant_message = Message(
                chat_id=chat.id,
                role="assistant",
                content=answer,
                sql_query=sql_query,
                query_result=json.dumps(query_result["data"]),
            )
            db.add(assistant_message)
            db.commit()
            db.refresh(assistant_message)

            return ChatQueryResponse(
                message=assistant_message,
                data=query_result["data"],
                visualization_type=viz_type,
            )

    except Exception as e:
        # Store error
        assistant_message = Message(
            chat_id=chat.id,
            role="assistant",
            content=f"An error occurred: {str(e)}",
            error_message=str(e),
        )
        db.add(assistant_message)
        db.commit()
        db.refresh(assistant_message)

        raise HTTPException(
            status_code=500,
            detail=str(e),
        )


@router.delete("/{chat_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_chat(
    chat_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Delete a chat."""
    chat = (
        db.query(Chat)
        .filter(Chat.id == chat_id, Chat.user_id == current_user.id)
        .first()
    )

    if not chat:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chat not found",
        )

    db.delete(chat)
    db.commit()

    return None
