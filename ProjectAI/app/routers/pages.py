from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlmodel import Session, select
from app.database import get_session
from app.models import Run, Dataset, RunStep, PipelineStep
import os

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

@router.get("/", response_class=HTMLResponse)
def index(request: Request, session: Session = Depends(get_session)):
    # Достаем все прогоны
    runs = session.exec(select(Run).order_by(Run.id.desc())).all()
    # Для каждого прогона достаем имя датасета
    runs_data = []
    for r in runs:
        ds = session.get(Dataset, r.dataset_id)
        runs_data.append({"run": r, "dataset_name": ds.name if ds else "Unknown"})
        
    return templates.TemplateResponse(
        request=request, name="index.html", context={"runs": runs_data}
    )

@router.get("/runs/{run_id}", response_class=HTMLResponse)
def run_detail(request: Request, run_id: int, session: Session = Depends(get_session)):
    run = session.get(Run, run_id)
    if not run:
        return HTMLResponse("Run not found", status_code=404)
        
    # Достаем шаги этого прогона
    steps = session.exec(select(RunStep).where(RunStep.run_id == run_id).order_by(RunStep.id)).all()
    steps_data = []
    for s in steps:
        p_step = session.get(PipelineStep, s.step_id)
        steps_data.append({"step": s, "code": p_step.code if p_step else "unknown"})
        
    return templates.TemplateResponse(
        request=request, name="detail.html", context={"run": run, "steps": steps_data}
    )