from fastapi import FastAPI, UploadFile, File, Form, BackgroundTasks, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
import httpx
import hashlib
from fastapi.responses import HTMLResponse
import io
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse

app = FastAPI(
    title="AntiPlagiat API Gateway",
    description="Единая точка входа для системы проверки на плагиат",
    version="1.0.0"
)

@app.get("/", response_class=HTMLResponse)
async def web_interface(request: Request):
    """Главная страница с формой загрузки"""
    return templates.TemplateResponse("index.html", {"request": request})

app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")

def extract_text_from_file(file_bytes, filename):
    """Извлекает текст из разных форматов файлов"""
    if not file_bytes:
        return ""

    if filename.endswith('.txt'):
        try:
            return file_bytes.decode('utf-8', errors='ignore')
        except:
            return ""
    elif filename.endswith('.pdf'):
        try:
            # Пробуем PyPDF2
            import PyPDF2
            pdf_file = io.BytesIO(file_bytes)
            pdf_reader = PyPDF2.PdfReader(pdf_file)
            text = ""
            for page in pdf_reader.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
            if text.strip():
                return text

            # Если PyPDF2 не сработал, пробуем pdfplumber
            try:
                import pdfplumber
                with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
                    text = ""
                    for page in pdf.pages:
                        page_text = page.extract_text()
                        if page_text:
                            text += page_text + "\n"
                    return text
            except:
                return ""

        except Exception as e:
            print(f"Ошибка чтения PDF {filename}: {e}")
            return ""
    elif filename.endswith(('.doc', '.docx')):
        try:
            import docx
            doc = docx.Document(io.BytesIO(file_bytes))
            text = "\n".join([paragraph.text for paragraph in doc.paragraphs if paragraph.text])
            return text
        except Exception as e:
            print(f"Ошибка чтения DOCX {filename}: {e}")
            return ""
    else:
        # Для неизвестных форматов пытаемся декодировать как текст
        try:
            return file_bytes.decode('utf-8', errors='ignore')
        except:
            return ""

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

FILE_SERVICE_URL = "http://file-storing:8001"
ANALYSIS_SERVICE_URL = "http://file-analysis:8002"



@app.post("/upload")
async def upload_work(
        background_tasks: BackgroundTasks,
        file: UploadFile = File(...),
        student_name: str = Form(...),
        assignment_id: str = Form(...)
):
    """Загружает работу студента"""
    try:
        file_content = await file.read()
        file_hash = hashlib.sha256(file_content).hexdigest()

        # Извлекаем текст из файла
        extracted_text = extract_text_from_file(file_content, file.filename)

        # Шаг 1: Загружаем в File Storing Service
        async with httpx.AsyncClient(timeout=30.0) as client:
            files = {"file": (file.filename, file_content, file.content_type)}
            data = {"student_name": student_name, "assignment_id": assignment_id}

            response = await client.post(
                f"{FILE_SERVICE_URL}/upload",
                files=files,
                data=data
            )

            if response.status_code != 200:
                error_detail = response.json().get("detail", "Ошибка загрузки файла")
                raise HTTPException(status_code=response.status_code, detail=error_detail)

            work_data = response.json()
            work_id = work_data.get("id")

            if not work_id:
                raise HTTPException(status_code=500, detail="Не получили work_id")

            # Шаг 2: Запускаем анализ в фоне, передавая извлеченный текст
            background_tasks.add_task(
                start_analysis,
                work_id, student_name, assignment_id, file.filename, file_hash, extracted_text
            )

            return {
                "message": "Файл загружен, анализ начат",
                "work_id": work_id,
                "status": "processing",
                "file_type": file.filename.split('.')[-1] if '.' in file.filename else "unknown"
            }

    except httpx.RequestError as e:
        raise HTTPException(status_code=503, detail=f"Сервис недоступен: {str(e)}")


async def start_analysis(work_id, student_name, assignment_id, file_name, file_hash, extracted_text):
    """Запускает анализ в Analysis Service"""
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{ANALYSIS_SERVICE_URL}/analyze",
                json={
                    "work_id": work_id,
                    "student_name": student_name,
                    "assignment_id": assignment_id,
                    "file_name": file_name,
                    "file_hash": file_hash,
                    "file_content": extracted_text  # Передаем извлеченный текст
                }
            )

            if response.status_code != 200:
                print(f"Ошибка анализа: {response.status_code} - {response.text}")
            else:
                print(f"✅ Анализ запущен для работы {work_id}")
    except Exception as e:
        print(f"❌ Ошибка запуска анализа: {e}")


@app.get("/works/{work_id}/report")
async def get_report(work_id: int):
    """Получает отчет по работе"""
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(f"{ANALYSIS_SERVICE_URL}/works/{work_id}/report")
            return response.json()
    except httpx.RequestError as e:
        raise HTTPException(503, f"Сервис недоступен: {str(e)}")


@app.get("/assignment/{assignment_id}/reports")
async def get_assignment_reports(assignment_id: str):
    """Получает все отчеты по заданию"""
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(f"{ANALYSIS_SERVICE_URL}/assignment/{assignment_id}/reports")
            return response.json()
    except httpx.RequestError as e:
        raise HTTPException(503, f"Сервис недоступен: {str(e)}")


@app.get("/health")
async def health():
    return {"status": "healthy", "service": "api-gateway"}


@app.get("/works/{work_id}/view", response_class=HTMLResponse)
async def view_work_report(request: Request, work_id: int):
    """Страница просмотра отчета через /works/{id}/view"""
    return templates.TemplateResponse("report.html", {"request": request, "work_id": work_id})

@app.get("/report/{work_id}", response_class=HTMLResponse)
async def view_report(request: Request, work_id: int):
    """Страница просмотра отчёта"""
    return templates.TemplateResponse("report.html", {"request": request, "work_id": work_id})