from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.database import Base


class Message(Base):
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, index=True)
    chat_id = Column(Integer, ForeignKey("chats.id"), nullable=False)
    role = Column(String, nullable=False)  # 'user' or 'assistant'
    content = Column(Text, nullable=False)  # The actual message
    sql_query = Column(Text, nullable=True)  # Generated SQL (if applicable)
    query_result = Column(Text, nullable=True)  # JSON string of query results
    error_message = Column(Text, nullable=True)  # Error if SQL failed
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    chat = relationship("Chat", back_populates="messages")
