from fastapi import APIRouter, HTTPException
from ..services.analysis_client import AnalysisServiceClient
from ..services.file_client import FileServiceClient

router = APIRouter()


@router.get("/works/{work_id}/report")
async def get_work_report(work_id: int):
    """Получает отчет по работе"""
    analysis_service = AnalysisServiceClient()
    file_service = FileServiceClient()

    try:
        # Получаем отчет из Analysis Service
        report = await analysis_service.get_report(work_id)
        if not report:
            raise HTTPException(status_code=404, detail="Report not found for this work")

        # Получаем информацию о работе из File Service
        work_info = await file_service.get_work(work_id)
        if work_info:
            report["work_info"] = work_info

        return report

    finally:
        await analysis_service.close()
        await file_service.close()


@router.get("/assignment/{assignment_id}/reports")
async def get_assignment_reports(assignment_id: str):
    """Получает все отчеты по заданию"""
    analysis_service = AnalysisServiceClient()

    try:
        reports = await analysis_service.get_reports_by_assignment(assignment_id)
        return reports
    finally:
        await analysis_service.close()


@router.get("/works/{work_id}/wordcloud")
async def get_word_cloud(work_id: int):
    """Получает облако слов для работы"""
    analysis_service = AnalysisServiceClient()

    try:
        # Получаем отчет
        report = await analysis_service.get_report(work_id)
        if not report:
            raise HTTPException(status_code=404, detail="Report not found")

        # Проверяем наличие URL облака слов
        word_cloud_url = report.get("word_cloud_url")
        if not word_cloud_url:
            raise HTTPException(status_code=404, detail="Word cloud not generated")

        return {
            "work_id": work_id,
            "word_cloud_url": word_cloud_url,
            "report_id": report.get("id")
        }
    finally:
        await analysis_service.close()