from datetime import datetime, timezone
from typing import Optional, Dict, Any
from sqlmodel import SQLModel, Field, Column
from sqlalchemy import Column, JSON

class Run(SQLModel, table=True):
    __tablename__ = "runs"
    id: Optional[int] = Field(default=None, primary_key=True)
    dataset_id: int = Field(foreign_key="datasets.id")
    started_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    finished_at: Optional[datetime] = None
    status: str = Field(default="running")
    agent_model: Optional[str] = None
    params: Dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSON))
    metric_name: Optional[str] = None
    metric_value: Optional[float] = None
    human_minutes: Optional[float] = None
    notes: Optional[str] = None