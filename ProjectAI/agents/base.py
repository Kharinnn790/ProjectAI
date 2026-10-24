import time
from abc import ABC, abstractmethod

class BaseAgent(ABC):
    @abstractmethod
    def run(self, context: dict) -> dict:
        """
        Запускает агента.
        Возвращает словарь с результатами:
        {
            "status": "success" | "failed",
            "output_path": "путь/к/файлу",
            "error": "текст ошибки, если есть",
            "metric_name": "...",
            "metric_value": ...
        }
        """
        pass