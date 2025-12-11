from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, Dict, Any


class ReportBase(BaseModel):
    work_id: int = Field(..., ge=1)
    student_name: str = Field(..., min_length=1, max_length=100)
    assignment_id: str = Field(..., min_length=1, max_length=50)
    file_name: str = Field(..., min_length=1, max_length=255)


class ReportCreate(ReportBase):
    is_plagiarism: bool = False
    plagiarism_score: float = Field(0.0, ge=0.0, le=1.0)
    original_author: Optional[str] = Field(None, min_length=1, max_length=100)
    matched_work_id: Optional[int] = Field(None, ge=1)
    word_cloud_url: Optional[str] = None
    report_data: Optional[Dict[str, Any]] = None


class ReportResponse(ReportCreate):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True


class AnalysisRequest(BaseModel):
    work_id: int = Field(..., ge=1)
    student_name: str = Field(..., min_length=1, max_length=100)
    assignment_id: str = Field(..., min_length=1, max_length=50)
    file_name: str = Field(..., min_length=1, max_length=255)
    file_hash: str = Field(..., min_length=64, max_length=64)
    file_content: Optional[str] = None  # Для текстовых файлов можно передать текст