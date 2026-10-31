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
            data_path = context.get("data_path")
            
            df = pd.read_csv(data_path)
            
            # Умный анализ: определяем типы колонок
            cat_cols = df.select_dtypes(include=['object']).columns.tolist()
            num_cols = df.select_dtypes(include=['number']).columns.tolist()
            
            profile = {
                "rows": len(df),
                "columns": len(df.columns),
                "missing_values": df.isnull().sum().to_dict(),
                "categorical_columns": cat_cols,
                "numeric_columns": num_cols,
                # Пример умного решения: для каждой категориальной колонки считаем уникальные значения
                "categorical_cardinality": {col: int(df[col].nunique()) for col in cat_cols}
            }
            
            with open(self.output_path, "w", encoding="utf-8") as f:
                json.dump(profile, f, ensure_ascii=False, indent=2)
                
            return {
                "status": "success",
                "output_path": self.output_path
            }
        except Exception as e:
            return {"status": "failed", "error": str(e)}