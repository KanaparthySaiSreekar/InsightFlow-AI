from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.database import Base


class Project(Base):
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    duckdb_file_path = Column(String, nullable=False)  # Path to .duckdb file
    schema_json = Column(Text, nullable=True)  # JSON string of AI-generated schema
    original_filename = Column(String, nullable=True)  # Original uploaded file name
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    user = relationship("User", back_populates="projects")
    chats = relationship("Chat", back_populates="project", cascade="all, delete-orphan")
