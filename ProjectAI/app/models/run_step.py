from datetime import datetime
from typing import Optional
from sqlmodel import SQLModel, Field

class RunStep(SQLModel, table=True):
    __tablename__ = "run_steps"
    id: Optional[int] = Field(default=None, primary_key=True)
    run_id: int = Field(foreign_key="runs.id")
    step_id: int = Field(foreign_key="pipeline_steps.id")
    status: str = Field(default="running")
    started_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None
    tokens_used: int = 0
    output_path: Optional[str] = None
    error_text: Optional[str] = None