import os
import hashlib
from typing import Tuple
from ..config import settings


class LocalStorage:
    def __init__(self):
        self.upload_dir = settings.upload_dir
        os.makedirs(self.upload_dir, exist_ok=True)

    def save_file(self, file_content: bytes, file_name: str) -> Tuple[str, str]:
        """Сохраняет файл и возвращает путь и хэш"""
        # Создаем уникальное имя файла
        file_hash = hashlib.sha256(file_content).hexdigest()
        extension = os.path.splitext(file_name)[1]
        unique_name = f"{file_hash}{extension}"

        # Сохраняем файл
        file_path = os.path.join(self.upload_dir, unique_name)
        with open(file_path, "wb") as f:
            f.write(file_content)

        return file_path, file_hash

    def get_file(self, file_name: str) -> bytes:
        """Получает содержимое файла"""
        file_path = os.path.join(self.upload_dir, file_name)
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File {file_name} not found")

        with open(file_path, "rb") as f:
            return f.read()

    def file_exists(self, file_hash: str) -> bool:
        """Проверяет существует ли файл с таким хэшем"""
        # Ищем файл по хэшу в имени
        for file in os.listdir(self.upload_dir):
            if file_hash in file:
                return True
        return False