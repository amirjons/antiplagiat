from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Depends
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
import os

from ..database.connection import get_db
from ..database import crud
from ..schemas.work import WorkCreate, WorkResponse
from ..storage.local_storage import LocalStorage
from ..config import settings

router = APIRouter()
storage = LocalStorage()


@router.post("/upload", response_model=WorkResponse, status_code=201)
async def upload_file(
        file: UploadFile = File(...),
        student_name: str = Form(...),
        assignment_id: str = Form(...),
        db: Session = Depends(get_db)
):
    # Проверка размера файла
    file_content = await file.read()
    file_size = len(file_content)

    if file_size > settings.max_file_size_mb * 1024 * 1024:
        raise HTTPException(
            status_code=400,
            detail=f"File size exceeds {settings.max_file_size_mb}MB limit"
        )

    # Сохраняем файл
    try:
        file_path, file_hash = storage.save_file(file_content, file.filename)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error saving file: {str(e)}")

    # Проверяем, не загружен ли уже такой файл
    existing_work = crud.get_work_by_hash(db, file_hash)
    if existing_work:
        raise HTTPException(
            status_code=400,
            detail="This file has already been uploaded (duplicate hash)"
        )

    # Сохраняем метаданные в БД
    work_data = WorkCreate(
        student_name=student_name,
        assignment_id=assignment_id,
        file_name=file.filename,
        file_hash=file_hash,
        file_path=file_path,
        file_size=file_size
    )

    try:
        db_work = crud.create_work(db, work_data)
        return db_work
    except Exception as e:
        # Удаляем файл если не удалось сохранить в БД
        if os.path.exists(file_path):
            os.remove(file_path)
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


@router.get("/works/{work_id}", response_model=WorkResponse)
async def get_work(work_id: int, db: Session = Depends(get_db)):
    work = crud.get_work_by_id(db, work_id)
    if not work:
        raise HTTPException(status_code=404, detail="Work not found")
    return work


@router.get("/assignment/{assignment_id}/works")
async def get_works_by_assignment(assignment_id: str, db: Session = Depends(get_db)):
    works = crud.get_works_by_assignment(db, assignment_id)
    return {"works": works, "total": len(works)}


@router.get("/download/{work_id}")
async def download_file(work_id: int, db: Session = Depends(get_db)):
    work = crud.get_work_by_id(db, work_id)
    if not work:
        raise HTTPException(status_code=404, detail="Work not found")

    if not os.path.exists(work.file_path):
        raise HTTPException(status_code=404, detail="File not found on disk")

    return FileResponse(
        path=work.file_path,
        filename=work.file_name,
        media_type="application/octet-stream"
    )


@router.get("/health")
async def health():
    return {"status": "healthy"}