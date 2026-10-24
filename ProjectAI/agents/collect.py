import os
import urllib.request
from .base import BaseAgent

class CollectAgent(BaseAgent):
    def __init__(self, url: str):
        self.url = url
        self.output_dir = "data/raw"
        self.output_path = os.path.join(self.output_dir, "titanic.csv")

    def run(self, context: dict) -> dict:
        try:
            # Создаем папку, если ее нет
            os.makedirs(self.output_dir, exist_ok=True)
            
            # Скачиваем файл
            urllib.request.urlretrieve(self.url, self.output_path)
            
            return {
                "status": "success",
                "output_path": self.output_path
            }
        except Exception as e:
            return {
                "status": "failed",
                "error": str(e)
            }