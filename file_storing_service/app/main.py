from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import os
import hashlib
from datetime import datetime

app = FastAPI(title="File Storing Service", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

UPLOAD_DIR = "/app/uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# Простое хранилище в памяти
works_db = []
next_id = 1


@app.post("/upload")
async def upload_file(
        file: UploadFile = File(...),
        student_name: str = Form(...),
        assignment_id: str = Form(...)
):
    global next_id

    try:
        file_content = await file.read()
        file_hash = hashlib.sha256(file_content).hexdigest()

        # Извлекаем текст для анализа
        extracted_text = ""
        if file.filename.endswith(('.txt', '.pdf', '.doc', '.docx')):
            try:
                if file.filename.endswith('.txt'):
                    extracted_text = file_content.decode('utf-8', errors='ignore')
            except:
                pass

        # Проверяем на дубликат
        for work in works_db:
            if work["file_hash"] == file_hash:
                if work["student_name"] == student_name and work["assignment_id"] == assignment_id:
                    return {
                        "message": "Файл уже был загружен ранее",
                        "work_id": work["id"],
                        "status": "already_uploaded"
                    }
                break

        # Сохраняем файл
        file_path = os.path.join(UPLOAD_DIR, f"{file_hash}_{file.filename}")
        with open(file_path, "wb") as f:
            f.write(file_content)

        # Сохраняем метаданные
        work_data = {
            "id": next_id,
            "student_name": student_name,
            "assignment_id": assignment_id,
            "file_name": file.filename,
            "file_hash": file_hash,
            "file_path": file_path,
            "file_size": len(file_content),
            "file_text": extracted_text,  # Сохраняем текст для сравнения
            "uploaded_at": datetime.now().isoformat()
        }

        works_db.append(work_data)
        next_id += 1

        return work_data

    except Exception as e:
        print(f"Ошибка загрузки: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Ошибка загрузки: {str(e)}")

@app.get("/files/{work_id}/text")
async def get_file_text(work_id: int):
    """Получает текст файла для анализа плагиата"""
    for work in works_db:
        if work["id"] == work_id:
            if "file_text" in work and work["file_text"]:
                return {"text": work["file_text"]}
            else:
                # Попробуем прочитать файл
                try:
                    with open(work["file_path"], "rb") as f:
                        content = f.read()
                        if work["file_name"].endswith('.txt'):
                            text = content.decode('utf-8', errors='ignore')
                            return {"text": text}
                except:
                    return {"text": ""}
    raise HTTPException(status_code=404, detail="Работа не найдена")


@app.get("/works/{work_id}")
async def get_work(work_id: int):
    for work in works_db:
        if work["id"] == work_id:
            return work
    raise HTTPException(status_code=404, detail="Работа не найдена")


@app.get("/assignment/{assignment_id}/works")
async def get_assignment_works(assignment_id: str):
    result = [w for w in works_db if w["assignment_id"] == assignment_id]
    return {"works": result, "total": len(result)}


@app.get("/health")
async def health():
    return {"status": "healthy", "service": "file-storing"}

@app.get("/works")
async def get_all_works():
    """Получает все работы в системе (для глобальной проверки плагиата)"""
    return {"works": works_db, "total": len(works_db)}