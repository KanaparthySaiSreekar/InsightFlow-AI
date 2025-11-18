import os
import shutil
from pathlib import Path
from typing import Optional
from fastapi import UploadFile, HTTPException
from app.config import settings


class FileHandler:
    """Handles file uploads and validation."""

    @staticmethod
    def validate_file(file: UploadFile) -> bool:
        """Validate file extension and size."""
        # Check extension
        file_ext = Path(file.filename).suffix.lower()
        if file_ext not in settings.ALLOWED_EXTENSIONS:
            raise HTTPException(
                status_code=400,
                detail=f"File type {file_ext} not allowed. Allowed types: {settings.ALLOWED_EXTENSIONS}",
            )
        return True

    @staticmethod
    async def save_upload_file(file: UploadFile, user_id: int, project_id: int) -> str:
        """Save uploaded file to disk."""
        FileHandler.validate_file(file)

        # Create user-specific directory
        user_upload_dir = os.path.join(settings.UPLOAD_DIR, f"user_{user_id}", f"project_{project_id}")
        os.makedirs(user_upload_dir, exist_ok=True)

        # Generate safe filename
        file_path = os.path.join(user_upload_dir, file.filename)

        # Save file
        try:
            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
        finally:
            file.file.close()

        return file_path

    @staticmethod
    def delete_file(file_path: str) -> bool:
        """Delete a file from disk."""
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                return True
            return False
        except Exception:
            return False

    @staticmethod
    def get_file_extension(filename: str) -> str:
        """Get file extension."""
        return Path(filename).suffix.lower()
