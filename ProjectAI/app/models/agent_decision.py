from datetime import datetime, timezone
from typing import Optional
from sqlmodel import SQLModel, Field, Column

class AgentDecision(SQLModel, table=True):
    __tablename__ = "agent_decisions"
    id: Optional[int] = Field(default=None, primary_key=True)
    run_id: int = Field(foreign_key="runs.id")
    step_id: int = Field(foreign_key="pipeline_steps.id")
    decision: str
    reasoning: Optional[str] = None
    prompt_hash: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))