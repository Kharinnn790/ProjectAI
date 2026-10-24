import pytest
import os
import shutil
from sqlmodel import Session, select
from app.database import engine
from app.models import Run, Blocker
from run_pipeline import execute_pipeline

# Фикстура для очистки БД перед каждым тестом
@pytest.fixture(autouse=True)
def clean_db():
    with Session(engine) as session:
        # Удаляем все прогоны перед тестом
        runs = session.exec(select(Run)).all()
        for r in runs:
            session.delete(r)
        session.commit()
    yield

def test_pipeline_success():
    """Тест: успешный прогон на нормальных данных"""
    # Запускаем пайплайн
    execute_pipeline()
    
    with Session(engine) as session:
        # Берем последний прогон
        run = session.exec(select(Run).order_by(Run.id.desc())).first()
        
        assert run is not None, "Прогон не создался"
        assert run.status == "success", f"Ожидался success, получен {run.status}"
        assert run.metric_value is not None
        assert run.metric_value > 0.75, "Метрика ниже порога 0.75"

def test_pipeline_broken_csv():
    """Тест: падение пайплайна на битых данных (проверка zero-touch)"""
    from app.models import Dataset
    from sqlmodel import Session
    
    # 1. Временно меняем URL датасета в БД на несуществующий (битый)
    with Session(engine) as session:
        dataset = session.exec(select(Dataset).where(Dataset.name == "titanic")).first()
        original_url = dataset.source_url
        dataset.source_url = "http://broken-url-that-does-not-exist.com/data.csv"
        session.add(dataset)
        session.commit()
        
    try:
        # 2. Запускаем пайплайн (он должен упасть на шаге collect)
        execute_pipeline()
        
        with Session(engine) as session:
            run = session.exec(select(Run).order_by(Run.id.desc())).first()
            assert run.status == "failed", "Пайплайн должен был упасть на битых данных"
            
            # Проверяем, что создался блокер
            blocker = session.exec(select(Blocker).where(Blocker.run_id == run.id)).first()
            assert blocker is not None, "Блокер не был записан в БД"
            assert len(blocker.description) > 0, "Описание блокера пустое"
            
    finally:
        # 3. Возвращаем оригинальный URL обратно
        with Session(engine) as session:
            dataset = session.exec(select(Dataset).where(Dataset.name == "titanic")).first()
            dataset.source_url = original_url
            session.add(dataset)
            session.commit()