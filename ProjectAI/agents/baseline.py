import os
import json
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score
from .base import BaseAgent

class BaselineAgent(BaseAgent):
    def __init__(self):
        self.output_dir = "data/baseline"
        self.output_path = os.path.join(self.output_dir, "metrics.json")

    def run(self, context: dict) -> dict:
        try:
            os.makedirs(self.output_dir, exist_ok=True)
            data_path = context.get("data_path")
            print(f"  [Baseline] Читаю данные из: {data_path}")
            
            # Явно указываем кодировку и разделитель
            df = pd.read_csv(data_path, sep=",", encoding="utf-8")
            
            # Простейший препроцессинг
            df = df[['Survived', 'Pclass', 'Sex']].dropna()
            df['Sex'] = df['Sex'].map({'male': 0, 'female': 1})
            
            X = df[['Pclass', 'Sex']]
            y = df['Survived']
            
            X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
            
            model = LogisticRegression()
            model.fit(X_train, y_train)
            
            preds = model.predict(X_test)
            acc = accuracy_score(y_test, preds)
            
            metrics = {"accuracy": float(acc)}
            with open(self.output_path, "w", encoding="utf-8") as f:
                json.dump(metrics, f, indent=2)
                
            return {
                "status": "success",
                "output_path": self.output_path,
                "metric_name": "accuracy",
                "metric_value": float(acc)
            }
        except Exception as e:
            return {
                "status": "failed",
                "error": str(e)
            }