import hashlib
import httpx
from typing import Optional, Tuple, List
from ..config import settings


class PlagiarismChecker:
    @staticmethod
    async def check_plagiarism(
            file_hash: str,
            student_name: str,  # Убрали assignment_id из обязательных параметров
            file_service_url: str
    ) -> Tuple[bool, float, Optional[str], Optional[int]]:
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                # Запрашиваем все работы
                response = await client.get(f"{file_service_url}/works")

                if response.status_code == 200:
                    data = response.json()
                    works = data.get("works", [])

                    for work in works:
                        if (work["file_hash"] == file_hash and
                                work["student_name"] != student_name):
                            return True, 1.0, work["student_name"], work["id"]

                return False, 0.0, None, None
        except Exception as e:
            print(f"Error in plagiarism check: {e}")
            return False, 0.0, None, None