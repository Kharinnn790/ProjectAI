from sqlmodel import SQLModel, Field, Column
from sqlalchemy import DateTime
from typing import Optional
from datetime import datetime, timezone

class Dataset(SQLModel, table=True):
    __tablename__ = "datasets"
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    source_url: Optional[str] = None
    task_type: Optional[str] = None
    target_column: Optional[str] = None
    rows_count: Optional[int] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))