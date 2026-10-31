from fastapi import APIRouter, Request, Depends, BackgroundTasks
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlmodel import Session, select
from app.database import get_session
from app.models import Run, Dataset, RunStep, PipelineStep
from run_pipeline import execute_pipeline
import os

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

@router.get("/", response_class=HTMLResponse)
def index(request: Request, session: Session = Depends(get_session)):
    runs = session.exec(select(Run).order_by(Run.id.desc())).all()
    runs_data = []
    for r in runs:
        ds = session.get(Dataset, r.dataset_id)
        runs_data.append({"run": r, "dataset_name": ds.name if ds else "Unknown"})
    return templates.TemplateResponse(request=request, name="index.html", context={"runs": runs_data})

@router.post("/run")
def trigger_run(background_tasks: BackgroundTasks):
    # Запускаем пайплайн в фоне, чтобы не блокировать веб-сервер
    background_tasks.add_task(execute_pipeline)
    return RedirectResponse(url="/", status_code=303)

@router.get("/runs/{run_id}", response_class=HTMLResponse)
def run_detail(request: Request, run_id: int, session: Session = Depends(get_session)):
    run = session.get(Run, run_id)
    if not run:
        return HTMLResponse("Run not found", status_code=404)
    steps = session.exec(select(RunStep).where(RunStep.run_id == run_id).order_by(RunStep.id)).all()
    steps_data = []
    for s in steps:
        p_step = session.get(PipelineStep, s.step_id)
        steps_data.append({"step": s, "code": p_step.code if p_step else "unknown"})
    return templates.TemplateResponse(request=request, name="detail.html", context={"run": run, "steps": steps_data})

