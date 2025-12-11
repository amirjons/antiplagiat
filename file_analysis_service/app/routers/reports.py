from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session

from ..database.connection import get_db
from ..database import crud
from ..schemas.report import ReportResponse

router = APIRouter()


@router.get("/reports/{report_id}", response_model=ReportResponse)
async def get_report(report_id: int, db: Session = Depends(get_db)):
    """Получает отчет по ID"""
    report = crud.get_report_by_id(db, report_id)
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    return report


@router.get("/works/{work_id}/report")
async def get_report_by_work(work_id: int, db: Session = Depends(get_db)):
    """Получает отчет по ID работы"""
    report = crud.get_report_by_work_id(db, work_id)
    if not report:
        raise HTTPException(status_code=404, detail="Report not found for this work")
    return report


@router.get("/assignment/{assignment_id}/reports")
async def get_reports_by_assignment(assignment_id: str, db: Session = Depends(get_db)):
    """Получает все отчеты по заданию"""
    reports = crud.get_reports_by_assignment(db, assignment_id)

    # Форматируем ответ как требуется в ТЗ
    reports_data = []
    for report in reports:
        reports_data.append({
            "work_id": report.work_id,
            "student_name": report.student_name,
            "file_name": report.file_name,
            "is_plagiarism": report.is_plagiarism,
            "plagiarism_score": report.plagiarism_score,
            "original_author": report.original_author,
            "word_cloud_url": report.word_cloud_url,
            "created_at": report.created_at.isoformat() if report.created_at else None
        })

    return {
        "assignment_id": assignment_id,
        "reports": reports_data,
        "total": len(reports)
    }