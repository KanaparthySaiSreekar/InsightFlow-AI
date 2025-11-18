from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.db.database import get_db
from app.models.user import User
from app.models.llm_config import LLMConfig
from app.schemas.llm_config import LLMConfigCreate, LLMConfigUpdate, LLMConfigResponse
from app.core.deps import get_current_user
from app.core.security import encrypt_api_key, decrypt_api_key

router = APIRouter(prefix="/llm-config", tags=["LLM Configuration"])


@router.post("/", response_model=LLMConfigResponse, status_code=status.HTTP_201_CREATED)
def create_llm_config(
    config_data: LLMConfigCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Create or update LLM configuration for user."""
    # Encrypt the API key
    encrypted_key = encrypt_api_key(config_data.api_key)

    # Deactivate all previous configs for this user
    db.query(LLMConfig).filter(LLMConfig.user_id == current_user.id).update(
        {"is_active": 0}
    )

    # Create new config
    new_config = LLMConfig(
        user_id=current_user.id,
        provider=config_data.provider,
        encrypted_api_key=encrypted_key,
        is_active=1,
    )

    db.add(new_config)
    db.commit()
    db.refresh(new_config)

    return new_config


@router.get("/", response_model=List[LLMConfigResponse])
def get_llm_configs(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get all LLM configurations for current user."""
    configs = db.query(LLMConfig).filter(LLMConfig.user_id == current_user.id).all()
    return configs


@router.get("/active", response_model=LLMConfigResponse)
def get_active_config(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get the active LLM configuration."""
    config = (
        db.query(LLMConfig)
        .filter(LLMConfig.user_id == current_user.id, LLMConfig.is_active == 1)
        .first()
    )

    if not config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No active LLM configuration found. Please set up your API key.",
        )

    return config


@router.put("/{config_id}", response_model=LLMConfigResponse)
def update_llm_config(
    config_id: int,
    config_data: LLMConfigUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Update an existing LLM configuration."""
    config = (
        db.query(LLMConfig)
        .filter(LLMConfig.id == config_id, LLMConfig.user_id == current_user.id)
        .first()
    )

    if not config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Configuration not found",
        )

    # Update fields
    config.provider = config_data.provider
    config.encrypted_api_key = encrypt_api_key(config_data.api_key)

    db.commit()
    db.refresh(config)

    return config


@router.delete("/{config_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_llm_config(
    config_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Delete an LLM configuration."""
    config = (
        db.query(LLMConfig)
        .filter(LLMConfig.id == config_id, LLMConfig.user_id == current_user.id)
        .first()
    )

    if not config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Configuration not found",
        )

    db.delete(config)
    db.commit()

    return None
