from sqlalchemy import Column, Integer, String, DateTime, Text
from sqlalchemy.sql import func
from ..database.connection import Base

class Work(Base):
    __tablename__ = "works"

    id = Column(Integer, primary_key=True, index=True)
    student_name = Column(String(100), nullable=False)
    assignment_id = Column(String(50), nullable=False)
    file_name = Column(String(255), nullable=False)
    file_hash = Column(String(64), nullable=False, unique=True)  # SHA256 hash
    file_path = Column(String(500), nullable=False)
    file_size = Column(Integer, nullable=False)
    uploaded_at = Column(DateTime(timezone=True), server_default=func.now())