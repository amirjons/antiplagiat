from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from datetime import datetime
import httpx
import urllib.parse
import re
import difflib

app = FastAPI(title="File Analysis Service", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class AnalysisRequest(BaseModel):
    work_id: int
    student_name: str
    assignment_id: str
    file_name: str
    file_hash: str
    file_content: str = ""


# Хранилище данных
all_works_cache = []  # Для текстового сравнения
reports_db = []
next_report_id = 1
FILE_SERVICE_URL = "http://file-storing:8001"
PLAGIARISM_THRESHOLD = 0.7  # Порог 70% для определения плагиата


def calculate_text_similarity_advanced(text1: str, text2: str) -> float:
    """Улучшенное вычисление схожести текстов"""
    if not text1 or not text2:
        return 0.0

    # 1. Очищаем текст
    text1 = text1.lower().strip()
    text2 = text2.lower().strip()

    # 2. Удаляем лишние пробелы
    text1 = ' '.join(text1.split())
    text2 = ' '.join(text2.split())

    # 3. Сравниваем разными методами
    similarities = []

    # Метод 1: SequenceMatcher
    seq_similarity = difflib.SequenceMatcher(None, text1, text2).ratio()
    similarities.append(seq_similarity)

    # Метод 2: Сравнение по токенам
    words1 = set(re.findall(r'\b\w+\b', text1))
    words2 = set(re.findall(r'\b\w+\b', text2))

    if words1 and words2:
        common_words = words1.intersection(words2)
        all_words = words1.union(words2)
        token_similarity = len(common_words) / len(all_words) if all_words else 0
        similarities.append(token_similarity)

    # Метод 3: Сравнение по шинглам
    def get_shingles(text, n=3):
        words = text.split()
        shingles = set()
        for i in range(len(words) - n + 1):
            shingle = ' '.join(words[i:i + n])
            shingles.add(shingle)
        return shingles

    shingles1 = get_shingles(text1, 3)
    shingles2 = get_shingles(text2, 3)

    if shingles1 and shingles2:
        common_shingles = shingles1.intersection(shingles2)
        all_shingles = shingles1.union(shingles2)
        shingle_similarity = len(common_shingles) / len(all_shingles) if all_shingles else 0
        similarities.append(shingle_similarity)

    # Возвращаем среднее значение
    return sum(similarities) / len(similarities) if similarities else 0.0


def calculate_text_similarity(text1: str, text2: str) -> float:
    """Вычисляет процент схожести двух текстов"""
    if not text1 or not text2:
        return 0.0

    # Используем SequenceMatcher для сравнения текстов
    similarity = difflib.SequenceMatcher(None, text1, text2).ratio()
    return similarity


@app.post("/analyze")
async def analyze_file(request: AnalysisRequest):
    global next_report_id, all_works_cache

    # Проверяем, не анализировалась ли уже работа
    for report in reports_db:
        if report["work_id"] == request.work_id:
            return {"message": "Анализ уже выполнен", "report_id": report["id"]}

    try:
        # Получаем все работы из File Storing Service
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(f"{FILE_SERVICE_URL}/works")

            max_similarity = 0.0
            original_author = None
            matched_work_id = None
            matched_file_name = None

            if response.status_code == 200:
                data = response.json()
                all_works = data.get("works", [])

                print(f"🔍 Проверка плагиата для работы {request.work_id}. Всего работ: {len(all_works)}")
                print(f"📝 Текст для анализа: {len(request.file_content)} символов")

                # Ищем самую похожую работу
                for work in all_works:
                    # Пропускаем текущую работу и работы того же студента
                    if work["id"] == request.work_id or work["student_name"] == request.student_name:
                        continue

                    # Получаем текст из кэша (если есть)
                    work_text = ""
                    for cached_work in all_works_cache:
                        if cached_work["id"] == work["id"]:
                            work_text = cached_work.get("text", "")
                            break

                    # Если текста нет в кэше, пытаемся получить из file-storing
                    if not work_text and request.file_content:
                        try:
                            file_response = await client.get(f"{FILE_SERVICE_URL}/download/{work['id']}")
                            if file_response.status_code == 200:
                                # Здесь нужна логика извлечения текста из файла
                                # Для простоты предположим, что это текстовый файл
                                try:
                                    work_text = file_response.content.decode('utf-8', errors='ignore')
                                except:
                                    work_text = ""
                        except:
                            work_text = ""

                    # Сравниваем тексты
                    if request.file_content and work_text:
                        similarity = calculate_text_similarity(request.file_content, work_text)
                        print(f"  • Сравнение с работой {work['id']} ({work['student_name']}): {similarity:.2%}")

                        if similarity > max_similarity:
                            max_similarity = similarity
                            original_author = work["student_name"]
                            matched_work_id = work["id"]
                            matched_file_name = work["file_name"]

            # Сохраняем текст текущей работы в кэш
            if request.file_content:
                current_work_data = {
                    "id": request.work_id,
                    "student_name": request.student_name,
                    "text": request.file_content,
                    "created_at": datetime.now().isoformat()
                }
                all_works_cache.append(current_work_data)

            # Определяем результат
            plagiarism_score = max_similarity
            is_plagiarism = plagiarism_score > PLAGIARISM_THRESHOLD

        # Генерация облака слов
        word_cloud_url = None
        if request.file_content:
            # Берем первые 1000 символов для облака слов
            text_for_cloud = request.file_content[:1000] if len(request.file_content) > 1000 else request.file_content

            words = re.findall(r'\b\w+\b', text_for_cloud.lower())

            if words:
                # Берем уникальные слова и соединяем через пробел
                unique_words = list(set(words))
                cloud_text = ' '.join(unique_words[:50])  # Максимум 50 слов

                # Кодируем для URL
                encoded_text = urllib.parse.quote(cloud_text)
                word_cloud_url = f"https://quickchart.io/wordcloud?text={encoded_text}&width=1000&height=800&format=png"

        # Создаем отчет
        report = {
            "id": next_report_id,
            "work_id": request.work_id,
            "student_name": request.student_name,
            "assignment_id": request.assignment_id,
            "file_name": request.file_name,
            "is_plagiarism": is_plagiarism,
            "plagiarism_score": plagiarism_score,  # Процент совпадения
            "original_author": original_author,
            "matched_work_id": matched_work_id,
            "matched_file_name": matched_file_name,
            "similarity_percentage": round(plagiarism_score * 100, 2),
            "word_cloud_url": word_cloud_url,
            "file_hash": request.file_hash,
            "created_at": datetime.now().isoformat()
        }

        reports_db.append(report)
        next_report_id += 1

        if is_plagiarism:
            print(f"⚠️  ОБНАРУЖЕН ПЛАГИАТ! Совпадение: {plagiarism_score:.2%} с работой {matched_work_id}")
        else:
            print(f"✅ Анализ для работы {request.work_id}: схожесть {plagiarism_score:.2%}")

        return {
            "message": "Анализ завершен",
            "work_id": request.work_id,
            "report_id": report["id"],
            "is_plagiarism": is_plagiarism,
            "similarity_percentage": round(plagiarism_score * 100, 2)
        }

    except Exception as e:
        print(f"❌ Ошибка анализа: {e}")
        raise HTTPException(status_code=500, detail=f"Ошибка анализа: {str(e)}")


@app.get("/works/{work_id}/report")
async def get_report(work_id: int):
    for report in reports_db:
        if report["work_id"] == work_id:
            return report
    raise HTTPException(status_code=404, detail="Отчет не найден")


@app.get("/assignment/{assignment_id}/reports")
async def get_assignment_reports(assignment_id: str):
    result = [r for r in reports_db if r["assignment_id"] == assignment_id]
    return {"reports": result, "total": len(result)}


@app.get("/health")
async def health():
    return {"status": "healthy", "service": "file-analysis"}


@app.get("/debug/works")
async def debug_works():
    return {"works": all_works_cache, "total": len(all_works_cache)}