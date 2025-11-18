from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import List, Optional
import json
from app.db.database import get_db
from app.models.user import User
from app.models.project import Project
from app.models.llm_config import LLMConfig
from app.schemas.project import ProjectCreate, ProjectResponse, SchemaUpdate
from app.core.deps import get_current_user
from app.core.security import decrypt_api_key
from app.services.duckdb_manager import DuckDBManager
from app.services.file_handler import FileHandler
from app.services.llm_service import LLMService

router = APIRouter(prefix="/projects", tags=["Projects"])


@router.post("/", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
async def create_project(
    name: str = Form(...),
    description: Optional[str] = Form(None),
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Create a new project by uploading a data file."""
    # Create project record first
    new_project = Project(
        user_id=current_user.id,
        name=name,
        description=description,
        duckdb_file_path="",  # Will be set after DuckDB creation
        original_filename=file.filename,
    )

    db.add(new_project)
    db.commit()
    db.refresh(new_project)

    try:
        # Save uploaded file
        file_path = await FileHandler.save_upload_file(file, current_user.id, new_project.id)

        # Create DuckDB instance
        db_path = DuckDBManager.create_db_for_user(current_user.id, new_project.id)
        new_project.duckdb_file_path = db_path

        # Ingest file into DuckDB
        file_ext = FileHandler.get_file_extension(file.filename)

        with DuckDBManager(db_path) as duck_db:
            if file_ext == ".csv":
                result = duck_db.ingest_csv(file_path)
            elif file_ext in [".xlsx", ".xls"]:
                result = duck_db.ingest_excel(file_path)
            elif file_ext == ".json":
                result = duck_db.ingest_json(file_path)
            else:
                raise HTTPException(
                    status_code=400,
                    detail=f"Unsupported file type: {file_ext}",
                )

            if not result["success"]:
                raise HTTPException(
                    status_code=500,
                    detail=f"Failed to ingest file: {result.get('error')}",
                )

            # Get schema information
            schema_info = duck_db.get_schema_info()

            # Generate AI schema using LLM
            llm_config = (
                db.query(LLMConfig)
                .filter(LLMConfig.user_id == current_user.id, LLMConfig.is_active == 1)
                .first()
            )

            if llm_config:
                # Decrypt API key
                api_key = decrypt_api_key(llm_config.encrypted_api_key)

                # Generate schema
                llm_service = LLMService(llm_config.provider, api_key)
                schema_result = llm_service.generate_schema(schema_info)

                if schema_result["success"]:
                    new_project.schema_json = json.dumps(schema_result["schema"])
                else:
                    # Store raw schema info if AI generation fails
                    new_project.schema_json = json.dumps({"tables": schema_info})
            else:
                # No LLM configured, store raw schema
                new_project.schema_json = json.dumps({"tables": schema_info})

        db.commit()
        db.refresh(new_project)

        return new_project

    except Exception as e:
        # Rollback on error
        db.delete(new_project)
        db.commit()
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create project: {str(e)}",
        )


@router.get("/", response_model=List[ProjectResponse])
def get_projects(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get all projects for the current user."""
    projects = db.query(Project).filter(Project.user_id == current_user.id).all()
    return projects


@router.get("/{project_id}", response_model=ProjectResponse)
def get_project(
    project_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get a specific project."""
    project = (
        db.query(Project)
        .filter(Project.id == project_id, Project.user_id == current_user.id)
        .first()
    )

    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found",
        )

    return project


@router.put("/{project_id}/schema", response_model=ProjectResponse)
def update_schema(
    project_id: int,
    schema_data: SchemaUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Update the schema for a project (user can edit AI-generated schema)."""
    project = (
        db.query(Project)
        .filter(Project.id == project_id, Project.user_id == current_user.id)
        .first()
    )

    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found",
        )

    project.schema_json = json.dumps(schema_data.schema_json)
    db.commit()
    db.refresh(project)

    return project


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_project(
    project_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Delete a project."""
    project = (
        db.query(Project)
        .filter(Project.id == project_id, Project.user_id == current_user.id)
        .first()
    )

    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found",
        )

    # Delete associated files (optional - could keep for recovery)
    # FileHandler.delete_file(project.duckdb_file_path)

    db.delete(project)
    db.commit()

    return None
