from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, BackgroundTasks
from sqlmodel import Session, select
from typing import List, Optional
import shutil
import os
from datetime import datetime

from .db import get_session
from .models import Job, JobCreate, Candidate, CandidateBase
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

UPLOAD_DIR = "backend/uploads"

@router.post("/jobs/", response_model=Job)
def create_job(job: JobCreate, session: Session = Depends(get_session)):
    db_job = Job.model_validate(job)
    session.add(db_job)
    session.commit()
    session.refresh(db_job)
    return db_job

@router.get("/jobs/", response_model=List[Job])
def read_jobs(session: Session = Depends(get_session)):
    jobs = session.exec(select(Job)).all()
    return jobs

@router.get("/jobs/{job_id}", response_model=Job)
def read_job(job_id: int, session: Session = Depends(get_session)):
    job = session.get(Job, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job

@router.delete("/jobs/{job_id}")
def delete_job(job_id: int, session: Session = Depends(get_session)):
    job = session.get(Job, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    # Delete associated candidates first (Manual Cascade)
    candidates = session.exec(select(Candidate).where(Candidate.job_id == job_id)).all()
    for candidate in candidates:
        session.delete(candidate)
        
    session.delete(job)
    session.commit()
    return {"message": "Job and associated candidates deleted successfully"}

@router.post("/jobs/{job_id}/apply")
def apply_to_job(
    job_id: int,
    file: UploadFile = File(...),
    background_tasks: BackgroundTasks = None, # Type hint fix later
    session: Session = Depends(get_session)
):
    job = session.get(Job, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    # Save file
    file_ext = os.path.splitext(file.filename)[1]
    logger.info(f"Uploading file extension: {file_ext}")
    filename = f"{job_id}_{datetime.now().timestamp()}{file_ext}"
    filename = filename.replace(".","_",1)
    
    file_path = os.path.join(UPLOAD_DIR, filename)
    logger.info(f"Saving resume to: {file_path}")
    
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
        
    # Create Candidate record
    # Note: parsing happens in background
    candidate = Candidate(
        job_id=job_id,
        email="pending@process.ing", # Placeholder until parsed
        resume_path=file_path,
        name=file.filename
    )
    session.add(candidate)
    session.commit()
    session.refresh(candidate)
    
    # Trigger background parsing task
    if background_tasks:
        from .worker import process_application
        background_tasks.add_task(process_application, candidate.id)
    
    return {"message": "Application received", "candidate_id": candidate.id}

@router.get("/jobs/{job_id}/candidates", response_model=List[Candidate])
def get_candidates(job_id: int, session: Session = Depends(get_session)):
    # Return candidates sorted by match_score desc (nulls last)
    statement = select(Candidate).where(Candidate.job_id == job_id).order_by(Candidate.match_score.desc().nulls_last())
    candidates = session.exec(statement).all()
    return candidates
