from typing import Optional
from sqlmodel import SQLModel, Field, Column

class PipelineStep(SQLModel, table=True):
    __tablename__ = "pipeline_steps"
    id: Optional[int] = Field(default=None, primary_key=True)
    code: str
    title: str
    order_index: int