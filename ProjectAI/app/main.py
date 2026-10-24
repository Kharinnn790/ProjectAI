from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.database import create_db_and_tables, engine
from sqlmodel import Session, select
from app.models import Dataset, PipelineStep

@asynccontextmanager
async def lifespan(app: FastAPI):
    create_db_and_tables()
    with Session(engine) as session:
        # Заливаем Titanic, если ещё нет
        if not session.exec(select(Dataset).where(Dataset.name == "titanic")).first():
            session.add(Dataset(
                name="titanic",
                source_url="https://raw.githubusercontent.com/datasciencedojo/datasets/master/titanic.csv",
                task_type="classification",
                target_column="Survived",
                rows_count=891
            ))
        # Заливаем шаги пайплайна
        steps = [
            ("collect", "Сбор данных", 1),
            ("eda", "Разведочный анализ", 2),
            ("baseline", "Baseline-модель", 3),
            ("report", "Отчёт", 4),
        ]
        for code, title, order in steps:
            if not session.exec(select(PipelineStep).where(PipelineStep.code == code)).first():
                session.add(PipelineStep(code=code, title=title, order_index=order))
        session.commit()
    yield

app = FastAPI(lifespan=lifespan)

from app.routers import pages
app.include_router(pages.router)