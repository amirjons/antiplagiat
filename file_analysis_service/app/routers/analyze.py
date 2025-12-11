from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends
from sqlalchemy.orm import Session
import asyncio

from ..database.connection import get_db
from ..database import crud
from ..schemas.report import ReportCreate, AnalysisRequest, ReportResponse
from ..services.plagiarism_checker import PlagiarismChecker
from ..services.word_cloud import WordCloudGenerator
from ..config import settings

router = APIRouter()


async def analyze_file_background(
        analysis_request: AnalysisRequest,
        db: Session
):
    """Фоновая задача для анализа файла"""
    try:
        # Проверяем на плагиат
        is_plagiarism, score, original_author, matched_work_id = await PlagiarismChecker.check_plagiarism(
            file_hash=analysis_request.file_hash,
            assignment_id=analysis_request.assignment_id,
            student_name=analysis_request.student_name,
            file_service_url=settings.file_service_url
        )

        # Генерируем облако слов (если есть текст)
        word_cloud_url = None
        if analysis_request.file_content:
            word_cloud_generator = WordCloudGenerator()
            word_cloud_url = word_cloud_generator.generate_from_text(analysis_request.file_content)

        # Создаем отчет
        report_data = ReportCreate(
            work_id=analysis_request.work_id,
            student_name=analysis_request.student_name,
            assignment_id=analysis_request.assignment_id,
            file_name=analysis_request.file_name,
            is_plagiarism=is_plagiarism,
            plagiarism_score=score,
            original_author=original_author,
            matched_work_id=matched_work_id,
            word_cloud_url=word_cloud_url,
            report_data={
                "file_hash": analysis_request.file_hash,
                "analysis_method": "hash_comparison",
                "plagiarism_detected": is_plagiarism
            }
        )

        # Сохраняем отчет в БД
        db_report = crud.create_report(db, report_data)

        print(f"Analysis completed for work {analysis_request.work_id}. Plagiarism: {is_plagiarism}")

    except Exception as e:
        print(f"Error in background analysis: {str(e)}")


@router.post("/analyze", response_model=dict)
async def analyze_file(
        request: AnalysisRequest,
        background_tasks: BackgroundTasks,
        db: Session = Depends(get_db)
):
    """
    Запускает анализ файла на плагиат.
    Анализ выполняется в фоновом режиме.
    """
    # Проверяем, не анализировалась ли уже эта работа
    existing_report = crud.get_report_by_work_id(db, request.work_id)
    if existing_report:
        return {
            "message": "Analysis already exists for this work",
            "report_id": existing_report.id,
            "status": "completed"
        }

    # Запускаем фоновую задачу
    background_tasks.add_task(analyze_file_background, request, db)

    return {
        "message": "Analysis started",
        "work_id": request.work_id,
        "status": "processing"
    }


@router.get("/analyze/status/{work_id}")
async def get_analysis_status(work_id: int, db: Session = Depends(get_db)):
    """Получает статус анализа работы"""
    report = crud.get_report_by_work_id(db, work_id)
    if report:
        return {
            "work_id": work_id,
            "status": "completed",
            "report_id": report.id,
            "is_plagiarism": report.is_plagiarism,
            "plagiarism_score": report.plagiarism_score
        }
    else:
        return {
            "work_id": work_id,
            "status": "processing",
            "message": "Analysis in progress or not started"
        }