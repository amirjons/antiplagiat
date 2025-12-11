from fastapi import APIRouter, UploadFile, File, Form, HTTPException, BackgroundTasks
import hashlib
import asyncio

from ..services.file_client import FileServiceClient
from ..services.analysis_client import AnalysisServiceClient

router = APIRouter()


@router.post("/upload")
async def upload_work(
        background_tasks: BackgroundTasks,
        file: UploadFile = File(...),
        student_name: str = Form(...),
        assignment_id: str = Form(...)
):
    """
    Загружает работу студента.

    Процесс:
    1. Сохраняет файл в File Storing Service
    2. Запускает анализ в фоновом режиме
    """
    # Проверяем размер файла (максимум 10MB)
    file_content = await file.read()
    if len(file_content) > 10 * 1024 * 1024:  # 10MB
        raise HTTPException(status_code=400, detail="File too large. Max size is 10MB")

    # Шаг 1: Загружаем файл в File Storing Service
    file_service = FileServiceClient()
    try:
        # Возвращаем указатель на начало файла для повторного чтения
        await file.seek(0)
        work_data = await file_service.upload_file(file, student_name, assignment_id)

        if not work_data:
            raise HTTPException(status_code=500, detail="Failed to upload file")

        work_id = work_data["id"]
        file_hash = work_data["file_hash"]

        # Шаг 2: Запускаем анализ в фоновом режиме
        analysis_service = AnalysisServiceClient()

        # Читаем содержимое файла для анализа текста
        await file.seek(0)
        file_content_for_analysis = await file.read()

        # Для текстовых файлов извлекаем текст для облака слов
        file_text = None
        if file.filename.endswith('.txt'):
            try:
                file_text = file_content_for_analysis.decode('utf-8', errors='ignore')
            except:
                pass

        # Добавляем фоновую задачу для анализа
        background_tasks.add_task(
            process_analysis,
            work_id,
            student_name,
            assignment_id,
            file.filename,
            file_hash,
            file_text
        )

        return {
            "message": "File uploaded successfully. Analysis started.",
            "work_id": work_id,
            "status": "processing",
            "file_hash": file_hash
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        await file_service.close()


async def process_analysis(work_id: int, student_name: str, assignment_id: str,
                           file_name: str, file_hash: str, file_text: str = None):
    """Фоновая задача для запуска анализа"""
    analysis_service = AnalysisServiceClient()
    try:
        await analysis_service.analyze_file(
            work_id=work_id,
            student_name=student_name,
            assignment_id=assignment_id,
            file_name=file_name,
            file_hash=file_hash,
            file_content=file_text
        )
        print(f"Analysis started for work {work_id}")
    except Exception as e:
        print(f"Failed to start analysis for work {work_id}: {str(e)}")
    finally:
        await analysis_service.close()


@router.get("/works/{work_id}")
async def get_work_info(work_id: int):
    """Получает информацию о работе"""
    file_service = FileServiceClient()
    try:
        work_data = await file_service.get_work(work_id)
        if not work_data:
            raise HTTPException(status_code=404, detail="Work not found")
        return work_data
    finally:
        await file_service.close()