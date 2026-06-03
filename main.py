from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from database import init_db, get_db
from models import JobCreateRequest, JobResponse, JobRecord
from queue_manager import enqueue_job

app = FastAPI(title="Shared Video Pipeline API")

@app.on_event("startup")
def on_startup():
    init_db()

@app.post("/jobs/", response_model=JobResponse)
def create_job(request: JobCreateRequest, db: Session = Depends(get_db)):
    # Create DB Record
    db_job = JobRecord(
        job_type=request.job_type,
        provider=request.provider,
        engine=request.engine,
        prompt=request.prompt,
        priority=request.priority,
        emergency=request.emergency,
        direct_to_vast=request.direct_to_vast,
        status="pending"
    )
    db.add(db_job)
    db.commit()
    db.refresh(db_job)

    # Enqueue based on logic
    queue_status = enqueue_job(
        job_record_id=db_job.id,
        job_type=db_job.job_type,
        priority=db_job.priority,
        emergency=db_job.emergency,
        direct_to_vast=db_job.direct_to_vast
    )
    
    # Update status to reflect queue state
    db_job.status = f"queued:{queue_status}"
    db.commit()
    db.refresh(db_job)

    return db_job

@app.get("/jobs/{job_id}", response_model=JobResponse)
def get_job(job_id: int, db: Session = Depends(get_db)):
    job = db.query(JobRecord).filter(JobRecord.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job

@app.get("/stats")
def get_stats():
    from queue_manager import get_queue_stats
    return get_queue_stats()
