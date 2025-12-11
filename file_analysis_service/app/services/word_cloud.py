import requests
import json
import re
from typing import List, Dict
from ..config import settings


class WordCloudGenerator:
    def __init__(self):
        self.quickchart_url = settings.quickchart_url

    def generate_from_text(self, text: str, width: int = 800, height: int = 600) -> str:
        """
        Генерирует облако слов из текста и возвращает URL изображения
        """
        try:
            # Очищаем текст от спецсимволов и приводим к нижнему регистру
            text = re.sub(r'[^\w\s]', '', text.lower())
            words = text.split()

            # Удаляем стоп-слова (самые частые и неинформативные)
            stop_words = {'the', 'and', 'that', 'for', 'with', 'this', 'from', 'have', 'was',
                          'were', 'are', 'you', 'your', 'they', 'their', 'what', 'which', 'who'}

            # Считаем частоту слов
            word_counts = {}
            for word in words:
                if word not in stop_words and len(word) > 2:
                    word_counts[word] = word_counts.get(word, 0) + 1

            # Берем топ-30 слов
            top_words = sorted(word_counts.items(), key=lambda x: x[1], reverse=True)[:30]

            if not top_words:
                return None

            # Формируем данные для облака слов
            word_cloud_data = []
            for word, count in top_words:
                word_cloud_data.append({
                    "text": word,
                    "value": count
                })

            # Конфигурация для QuickChart
            config = {
                "type": "wordCloud",
                "data": {
                    "labels": [item["text"] for item in word_cloud_data],
                    "datasets": [{
                        "label": "",
                        "data": [item["value"] for item in word_cloud_data],
                        "color": "random-light",
                        "backgroundColor": "hsl(0, 0%, 0%)"
                    }]
                },
                "options": {
                    "title": {
                        "display": True,
                        "text": "Word Cloud",
                        "fontSize": 24
                    },
                    "rotation": 0.5
                }
            }

            # Формируем URL для QuickChart
            encoded_config = json.dumps(config)
            url = f"{self.quickchart_url}/wordcloud?f=png&w={width}&h={height}&c={encoded_config}"

            return url

        except Exception as e:
            print(f"Error generating word cloud: {e}")
            return None