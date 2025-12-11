import httpx
from fastapi import HTTPException
from ..config import settings


class AnalysisServiceClient:
    def __init__(self):
        self.base_url = settings.analysis_service_url
        self.client = httpx.AsyncClient(timeout=settings.timeout_seconds)

    async def analyze_file(self, work_id: int, student_name: str, assignment_id: str,
                           file_name: str, file_hash: str, file_content: str = None):
        """Запускает анализ файла"""
        try:
            data = {
                "work_id": work_id,
                "student_name": student_name,
                "assignment_id": assignment_id,
                "file_name": file_name,
                "file_hash": file_hash,
                "file_content": file_content
            }

            response = await self.client.post(
                f"{self.base_url}/api/v1/analyze",
                json=data
            )

            if response.status_code != 200:
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"Analysis service error: {response.text}"
                )

            return response.json()

        except httpx.RequestError as e:
            raise HTTPException(
                status_code=503,
                detail=f"Analysis service unavailable: {str(e)}"
            )

    async def get_report(self, work_id: int):
        """Получает отчет по работе"""
        try:
            response = await self.client.get(f"{self.base_url}/api/v1/works/{work_id}/report")
            if response.status_code == 404:
                return None
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError:
            return None
        except httpx.RequestError as e:
            raise HTTPException(
                status_code=503,
                detail=f"Analysis service unavailable: {str(e)}"
            )

    async def get_reports_by_assignment(self, assignment_id: str):
        """Получает отчеты по заданию"""
        try:
            response = await self.client.get(f"{self.base_url}/api/v1/assignment/{assignment_id}/reports")
            response.raise_for_status()
            return response.json()
        except httpx.RequestError as e:
            raise HTTPException(
                status_code=503,
                detail=f"Analysis service unavailable: {str(e)}"
            )

    async def close(self):
        await self.client.aclose()