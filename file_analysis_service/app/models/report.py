from sqlalchemy import Column, Integer, String, DateTime, Float, Boolean, Text
from sqlalchemy.sql import func
from ..database.connection import Base


class Report(Base):
    __tablename__ = "reports"

    id = Column(Integer, primary_key=True, index=True)
    work_id = Column(Integer, nullable=False)
    student_name = Column(String(100), nullable=False)
    assignment_id = Column(String(50), nullable=False)
    file_name = Column(String(255), nullable=False)

    # Результаты анализа
    is_plagiarism = Column(Boolean, default=False)
    plagiarism_score = Column(Float, default=0.0)
    original_author = Column(String(100), nullable=True)
    matched_work_id = Column(Integer, nullable=True)

    # Облако слов
    word_cloud_url = Column(String(500), nullable=True)
    report_data = Column(Text, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())