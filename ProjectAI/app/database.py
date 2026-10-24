from sqlmodel import SQLModel, Session, create_engine

sqlite_url = "sqlite:///./project.db"
engine = create_engine(sqlite_url, echo=False)

def create_db_and_tables():
    # Важно: модели должны быть импортированы ДО вызова create_all
    from app.models import Dataset, PipelineStep, Run, RunStep, Blocker, AgentDecision
    SQLModel.metadata.create_all(engine)

def get_session():
    with Session(engine) as session:
        yield session