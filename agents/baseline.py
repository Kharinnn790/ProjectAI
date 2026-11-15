import os
import json
import io
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import base64
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import cross_val_score, StratifiedKFold
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
            
            # 1. Чтение данных
            df = pd.read_csv(data_path, sep=",", encoding="utf-8")
            
            # 2. Выбор признаков (как и просил преподаватель - без утечек)
            selected_features = ['Pclass', 'Sex', 'Age', 'SibSp', 'Parch', 'Fare']
            context["decision_features"] = selected_features
            
            # Простейший препроцессинг
            df = df[['Survived'] + selected_features].copy()
            df['Sex'] = df['Sex'].map({'male': 0, 'female': 1})
            # Заполняем пропуски в Age медианой
            df['Age'] = df['Age'].fillna(df['Age'].median())
            
            X = df[selected_features]
            y = df['Survived']
            
            # 3. Настройка RandomForest с GridSearch
            # ВАЖНО: Параметры подбираются ВНУТРИ кросс-валидации через GridSearchCV
            # Мы используем StratifiedKFold для честного разбиения (сохраняет пропорции классов)
            cv_strategy = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
            
            param_grid = {
                'n_estimators': [50, 100],
                'max_depth': [3, 5, 7],
                'min_samples_split': [2, 5]
            }
            
            base_model = RandomForestClassifier(random_state=42)
            
            # Подбор гиперпараметров
            from sklearn.model_selection import GridSearchCV
            grid_search = GridSearchCV(
                estimator=base_model,
                param_grid=param_grid,
                cv=cv_strategy,
                scoring='accuracy',
                n_jobs=-1 # Используем все ядра процессора
            )
            
            # Обучение с подбором параметров
            grid_search.fit(X, y)
            
            best_model = grid_search.best_estimator_

             # --- Генерация графика важности признаков ---
            importances = best_model.feature_importances_
            
            plt.figure(figsize=(8, 5))
            plt.barh(selected_features, importances, color='#3498db')
            plt.xlabel('Важность')
            plt.title('Важность признаков (RandomForest)')
            plt.tight_layout()
            
            # Сохраняем картинку
            img_path = "app/static/feature_importance.png"
            os.makedirs("app/static", exist_ok=True)
            
            # ВАЖНО: facecolor='white' делает фон непрозрачным, а bbox_inches='tight' убирает лишние поля
            plt.savefig(img_path, format='png', dpi=150, facecolor='white', bbox_inches='tight')
            plt.close()
            
            context["feature_importance_path"] = img_path

            # 4. Честная оценка на тех же фолдах через cross_val_score
            cv_scores = cross_val_score(best_model, X, y, cv=cv_strategy, scoring='accuracy')
            
            mean_accuracy = float(cv_scores.mean())
            std_accuracy = float(cv_scores.std())
            
            # Сохраняем метрики
            metrics = {
                "accuracy_mean": mean_accuracy,
                "accuracy_std": std_accuracy,
                "best_params": grid_search.best_params_,
                "cv_scores": cv_scores.tolist()
            }
            
            with open(self.output_path, "w", encoding="utf-8") as f:
                json.dump(metrics, f, indent=2)
                
            print(f"  [Baseline] Средняя accuracy (5-fold): {mean_accuracy:.4f} ± {std_accuracy:.4f}")
            print(f"  [Baseline] Лучшие параметры: {grid_search.best_params_}")
            
            # Возвращаем в контекст данные для записи в БДшке
            context["baseline_metrics"] = metrics
            
            return {
                "status": "success",
                "output_path": self.output_path,
                "metric_name": "accuracy_mean",
                "metric_value": mean_accuracy
            }
        except Exception as e:
            return {
                "status": "failed",
                "error": str(e)
            }