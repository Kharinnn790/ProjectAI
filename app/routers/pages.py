from fastapi import APIRouter, Request, Depends, BackgroundTasks
from fastapi.responses import HTMLResponse, RedirectResponse, Response, StreamingResponse
from fastapi.templating import Jinja2Templates
from sqlmodel import Session, select
from app.database import get_session
from app.models import Run, Dataset, RunStep, PipelineStep
from run_pipeline import execute_pipeline
from weasyprint import HTML
from fastapi import UploadFile, File
import shutil
import io
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

@router.post("/upload")
async def upload_dataset(
    file: UploadFile = File(...),
    session: Session = Depends(get_session)
):
    # Проверяем, что это CSV
    if not file.filename.endswith('.csv'):
        return HTMLResponse("Ошибка: файл должен быть в формате CSV", status_code=400)
        
    # Сохраняем файл
    os.makedirs("data/raw", exist_ok=True)
    file_path = f"data/raw/{file.filename}"
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
        
    # Создаем запись в БД
    dataset_name = file.filename.replace(".csv", "")
    new_dataset = Dataset(
        name=dataset_name,
        source_url=file_path, # В качестве URL используем локальный путь
        task_type="classification",
        target_column="Survived", # По умолчанию для теста
        rows_count=0
    )
    session.add(new_dataset)
    session.commit()
    
    return RedirectResponse(url="/", status_code=303)

@router.get("/runs/{run_id}/pdf")
def download_pdf(run_id: int, request: Request, session: Session = Depends(get_session)):
    
    import base64
    import os
    
    run = session.get(Run, run_id)
    if not run:
        return HTMLResponse("Run not found", status_code=404)
        
    ds = session.get(Dataset, run.dataset_id)
    
    steps = session.exec(select(RunStep).where(RunStep.run_id == run_id).order_by(RunStep.id)).all()
    steps_data = []
    for s in steps:
        p_step = session.get(PipelineStep, s.step_id)
        steps_data.append({"step": s, "code": p_step.code if p_step else "unknown"})
        
    # Читаем картинку и кодируем в base64
    img_base64 = None
    img_path = "app/static/feature_importance.png"
    if os.path.exists(img_path):
        with open(img_path, "rb") as f:
            img_base64 = base64.b64encode(f.read()).decode("utf-8")
    
    # Рендерим шаблон, передавая base64 напрямую
    html_content = templates.get_template("report_pdf.html").render(
        request=request, 
        run=run, 
        steps=steps_data, 
        dataset_name=ds.name if ds else "Unknown",
        img_base64=img_base64  # <--- ВОТ СЮДА
    )
    
    pdf_bytes = HTML(string=html_content).write_pdf()
    
    return StreamingResponse(
        io.BytesIO(pdf_bytes),
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=report_run_{run_id}.pdf"}
    )