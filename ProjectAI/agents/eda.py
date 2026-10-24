import os
import json
import pandas as pd
from .base import BaseAgent

class EDAAgent(BaseAgent):
    def __init__(self):
        self.output_dir = "data/eda"
        self.output_path = os.path.join(self.output_dir, "profile.json")

    def run(self, context: dict) -> dict:
        try:
            os.makedirs(self.output_dir, exist_ok=True)
            
            # Берем путь к данным из контекста (его передаст предыдущий агент)
            data_path = context.get("data_path")
            if not data_path or not os.path.exists(data_path):
                raise FileNotFoundError("Датасет не найден")

            df = pd.read_csv(data_path)
            
            # Собираем профиль
            profile = {
                "rows": len(df),
                "columns": len(df.columns),
                "missing_values": df.isnull().sum().to_dict(),
                "dtypes": df.dtypes.astype(str).to_dict()
            }
            
            with open(self.output_path, "w", encoding="utf-8") as f:
                json.dump(profile, f, ensure_ascii=False, indent=2)
                
            return {
                "status": "success",
                "output_path": self.output_path
            }
        except Exception as e:
            return {
                "status": "failed",
                "error": str(e)
            }