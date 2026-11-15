from datetime import datetime, timezone
from sqlmodel import Session, select
from app.database import engine
from app.models import Dataset, PipelineStep, Run, RunStep, Blocker, AgentDecision
from agents.collect import CollectAgent
from agents.eda import EDAAgent
from agents.baseline import BaselineAgent
from agents.report import ReportAgent

def execute_pipeline():
    print("🚀 Запуск zero-touch пайплайна...")
    
    with Session(engine) as session:
        # 1. Достаем датасет
        dataset = session.exec(select(Dataset).where(Dataset.name == "titanic")).first()
        if not dataset:
            print("❌ Датасет не найден в БД!")
            return

        # 2. Создаем новый прогон (Run)
        run = Run(
            dataset_id=dataset.id,
            status="running",
            human_minutes=0.0, # Время человека = 0, так как все делает ИИ
            notes="Автоматический прогон (RandomForest + CV)"
        )
        session.add(run)
        session.commit()
        session.refresh(run)
        
        print(f"✅ Создан прогон ID: {run.id}")

        # 3. Настраиваем агентов
        agents = [
            ("collect", CollectAgent(url=dataset.source_url)),
            ("eda", EDAAgent()),
            ("baseline", BaselineAgent()),
            ("report", ReportAgent())
        ]

        context = {} # Сюда агенты будут передавать данные друг другу

        # 4. Запускаем шаги по очереди
        for step_code, agent in agents:
            step_db = session.exec(select(PipelineStep).where(PipelineStep.code == step_code)).first()
            
            print(f"Шаг '{step_code}'...")
            start_time = datetime.now(timezone.utc)
            
            result = agent.run(context) # запуск агента
            
            end_time = datetime.now(timezone.utc)
            
            # 5. Записываем результат шага в БД
            run_step = RunStep(
                run_id=run.id,
                step_id=step_db.id,
                status=result["status"],
                started_at=start_time,
                finished_at=end_time,
                output_path=result.get("output_path"),
                error_text=result.get("error")
            )
            session.add(run_step)
            
            # Если упало - логируем блокер и останавливаем пайплайн
            if result["status"] == "failed":
                print(f"❌ Ошибка на шаге {step_code}: {result.get('error')}")
                blocker = Blocker(
                    run_id=run.id,
                    step_id=step_db.id,
                    description=result.get("error"),
                    severity="high"
                )
                session.add(blocker)
                run.status = "failed"
                break
                
            # Передаем контекст между агентами
            if step_code == "collect":
                context["data_path"] = result["output_path"]
            elif step_code == "eda":
                context["eda_profile_path"] = result["output_path"]
            elif step_code == "baseline":
                context["baseline_metrics_path"] = result["output_path"]
                # Передаем картинку дальше
                if "feature_importance_img" in context:
                    # Оставляем в контексте, она сама дойдет до эндпоинта PDF
                    pass 
                
                # Сохраняем метрику в Run (среднее)
                run.metric_name = result.get("metric_name")
                run.metric_value = result.get("metric_value")
                
                # --- ДОБАВЛЕНО: Логирование решения агента (выбор фичей) ---
                if "decision_features" in context:
                    decision = AgentDecision(
                        run_id=run.id,
                        step_id=step_db.id,
                        decision=f"Выбраны признаки: {context['decision_features']}",
                        reasoning="Выбраны базовые признаки для RandomForest."
                    )
                    session.add(decision)
                    context.pop("decision_features")
                
                print(f"📊 Метрика: {run.metric_name} = {run.metric_value:.4f}")

            elif step_code == "report":
                # --- ДОБАВЛЕНО: Логирование промпта и ответа LLM в agent_decisions ---
                if "llm_decision" in context:
                    llm_data = context["llm_decision"]
                    decision = AgentDecision(
                        run_id=run.id,
                        step_id=step_db.id,
                        decision=f"Ответ LLM: {llm_data['response'][:100]}...",  # первые 100 символов
                        reasoning=f"Промпт: {llm_data['prompt']}\n\nПолный ответ LLM: {llm_data['response']}"
                    )
                    session.add(decision)
                    context.pop("llm_decision")

        # 6. Финализируем прогон
        run.finished_at = datetime.now(timezone.utc)
        if run.status != "failed":
            run.status = "success"
            print("Пайплайн успешно завершен!")
        
        session.add(run)
        session.commit()

if __name__ == "__main__":
    execute_pipeline()