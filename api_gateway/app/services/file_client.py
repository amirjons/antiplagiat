import httpx
from fastapi import UploadFile, HTTPException
from ..config import settings


class FileServiceClient:
    def __init__(self):
        self.base_url = settings.file_service_url
        self.client = httpx.AsyncClient(timeout=settings.timeout_seconds)

    async def upload_file(self, file: UploadFile, student_name: str, assignment_id: str):
        """Загружает файл в File Storing Service"""
        try:
            # Читаем содержимое файла
            file_content = await file.read()

            # Отправляем multipart/form-data запрос
            files = {
                "file": (file.filename, file_content, file.content_type)
            }
            data = {
                "student_name": student_name,
                "assignment_id": assignment_id
            }

            response = await self.client.post(
                f"{self.base_url}/api/v1/upload",
                files=files,
                data=data
            )

            if response.status_code != 201:
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"File service error: {response.text}"
                )

            return response.json()

        except httpx.RequestError as e:
            raise HTTPException(
                status_code=503,
                detail=f"File service unavailable: {str(e)}"
            )

    async def get_work(self, work_id: int):
        """Получает информацию о работе"""
        try:
            response = await self.client.get(f"{self.base_url}/api/v1/works/{work_id}")
            if response.status_code == 404:
                return None
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError:
            return None
        except httpx.RequestError as e:
            raise HTTPException(
                status_code=503,
                detail=f"File service unavailable: {str(e)}"
            )

    async def close(self):
        await self.client.aclose()