from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional


class WorkBase(BaseModel):
    student_name: str = Field(..., min_length=1, max_length=100)
    assignment_id: str = Field(..., min_length=1, max_length=50)
    file_name: str = Field(..., min_length=1, max_length=255)
    file_hash: str = Field(..., min_length=64, max_length=64)
    file_path: str = Field(..., min_length=1, max_length=500)
    file_size: int = Field(..., ge=1)


class WorkCreate(WorkBase):
    pass


class WorkResponse(WorkBase):
    id: int
    uploaded_at: datetime

    class Config:
        from_attributes = True


class WorkListResponse(BaseModel):
    works: list[WorkResponse]
    total: int