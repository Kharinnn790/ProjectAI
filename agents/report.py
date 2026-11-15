import os
from datetime import datetime
from openai import OpenAI
from .base import BaseAgent

class ReportAgent(BaseAgent):
    def __init__(self):
        self.output_dir = "data/reports"
        
    def run(self, context: dict) -> dict:
        try:
            os.makedirs(self.output_dir, exist_ok=True)
            
            # 1. Берем данные из контекста (переданы из baseline.py)
            metrics = context.get("baseline_metrics", {})
            accuracy_mean = metrics.get("accuracy_mean")
            accuracy_std = metrics.get("accuracy_std", 0.0)
            best_params = metrics.get("best_params", {})
            
            if accuracy_mean is None:
                raise ValueError("Не найдены метрики (accuracy_mean) для отчета")

            # 2. Формируем промпт
            prompt = (
                f"Ты — ассистент по анализу данных. Напиши краткий вывод (2-3 предложения) "
                f"по результатам исследования датасета Titanic. "
                f"Модель RandomForest показала accuracy {accuracy_mean:.4f} (±{accuracy_std:.4f}) на 5-fold кросс-валидации. "
                f"Лучшие параметры: {best_params}. "
                f"Сделай акцент на том, что это хороший, стабильный результат."
            )
            
            # 3. Вызов реального API (OpenRouter)
            API_KEY = "pza_8bYobsKEcBXS-Wi80OjEK9CPLAYxKMLi" 
            
            client = OpenAI(
                base_url="https://openrouter.ai/api/v1",
                api_key=API_KEY,
            )
            
            print("  [Report] Отправка запроса к LLM (OpenRouter)...")
            
            try:
                completion = client.chat.completions.create(
                    # Бесплатная модель
                    model="meta-llama/llama-3.1-8b-instruct:free", 
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.3,
                )
                llm_response = completion.choices[0].message.content
                print("  [Report] Ответ от LLM успешно получен!")
            except Exception as api_error:
                print(f"  [Report] Ошибка API: {api_error}")
                llm_response = f"Не удалось получить ответ от LLM. Ошибка: {api_error}"
            
            # 4. Сохраняем промпт и ответ в контекст (для записи в agent_decisions)
            context["llm_decision"] = {
                "prompt": prompt,
                "response": llm_response
            }
            
            # 5. Формируем финальный текстовый отчет
            report_text = f"""# Отчет об исследовании
**Дата генерации:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
**Датасет:** Titanic

## Результаты модели
- **Алгоритм:** RandomForest (с подбором гиперпараметров)
- **Средняя Accuracy (5-fold CV):** {accuracy_mean:.4f} ± {accuracy_std:.4f}
- **Лучшие параметры:** {best_params}

## Выводы (сгенерировано ИИ)
{llm_response}
"""
            # Сохраняем отчет в файл
            report_filename = f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
            report_path = os.path.join(self.output_dir, report_filename)
            
            with open(report_path, "w", encoding="utf-8") as f:
                f.write(report_text)
                
            return {
                "status": "success",
                "output_path": report_path
            }
        except Exception as e:
            return {
                "status": "failed",
                "error": str(e)
            }