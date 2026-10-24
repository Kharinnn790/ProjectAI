from typing import Optional
from sqlmodel import SQLModel, Field, Column

class Blocker(SQLModel, table=True):
    __tablename__ = "blockers"
    id: Optional[int] = Field(default=None, primary_key=True)
    run_id: int = Field(foreign_key="runs.id")
    step_id: int = Field(foreign_key="pipeline_steps.id")
    description: str
    severity: str = Field(default="medium")
    resolved: bool = Field(default=False)
    resolution: Optional[str] = None