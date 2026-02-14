from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, Header #, status, BackgroundTasks
from typing import List, Optional
# import os
# import shutil
import uuid
# import json
# from datetime import datetime

from .core.config import settings
from .core.appwrite import appwrite_service
from .core.auth import get_current_user, require_recruiter
from .schemas import Job, JobCreate #, Candidate, CandidateCreate, Application, ApplicationCreate
from .worker import queue, parse_resume_and_index
from .services.vector_store import vector_store
from .services.embeddings import embedding_service
from appwrite.id import ID
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

# --- Jobs ---

@router.post("/jobs/", response_model=Job)
def create_job(job: JobCreate, user: dict = Depends(require_recruiter)):
    db = appwrite_service.get_database()
    
    # Appwrite expects data as dict
    job_data = job.dict()
    job_data['recruiter_id'] = user['$id']
    
    logger.info(f"Creating job: {job.title} for recruiter: {user['$id']}")

    doc = db.create_document(
        database_id=settings.DATABASE_ID,
        collection_id=settings.JOBS_COLLECTION_ID,
        document_id=ID.unique(),
        data=job_data
    )
    logger.info(f"Job created successfully: {doc['$id']}")
    return doc

@router.get("/jobs/", response_model=List[Job])
def read_jobs(user: dict = Depends(get_current_user)):
    db = appwrite_service.get_database()
    result = db.list_documents(
        database_id=settings.DATABASE_ID,
        collection_id=settings.JOBS_COLLECTION_ID
    )
    return result['documents']

@router.get("/jobs/{job_id}", response_model=Job)
def read_job(job_id: str, user: dict = Depends(get_current_user)):
    db = appwrite_service.get_database()
    try:
        doc = db.get_document(
            database_id=settings.DATABASE_ID,
            collection_id=settings.JOBS_COLLECTION_ID,
            document_id=job_id
        )
        return doc
    except Exception:
        raise HTTPException(status_code=404, detail="Job not found")

# --- Applications ---

@router.post("/apply")
def apply_to_job(
    job_id: str,
    file: UploadFile = File(...),
    name: Optional[str] = None,
    email: Optional[str] = None,
    phone: Optional[str] = None,
    user: dict = Depends(get_current_user) # Can be guest?
):
    # If user is not authenticated, we might need to handle guest apply. 
    # But current auth generic depends check calls get_current_user which raises 401.
    # Task says "if unauthenticated... allow one-off".
    # So we need a loose auth check here or remove Depends logic for this route and check manually.
    pass

@router.post("/jobs/{job_id}/apply")
async def apply_to_job_endpoint(
    job_id: str,
    file: UploadFile = File(...),
    name: Optional[str] = None,
    email: Optional[str] = None,
    phone: Optional[str] = None,
    x_appwrite_jwt: Optional[str] = Header(None) # Manual check to allow guest
):
    logger.info(f"Received application for job: {job_id}, file: {file.filename}")
    # 1. Check Auth (Candidate vs Guest)
    user_id = "guest"
    try:
        if x_appwrite_jwt:
            user = await get_current_user(x_appwrite_jwt)
            user_id = user['$id']
    except Exception:
        pass # Treat as guest

    db = appwrite_service.get_database()
    storage = appwrite_service.get_storage()

    # 2. Upload Resume to Appwrite Storage
    file_content = await file.read()
    # Appwrite Python SDK required 'InputFile' for uploads usually, or just bytes/path
    # check sdk usage: storage.create_file(bucket_id, file_id, file)
    # file needs to be InputFile.from_bytes or path
    from appwrite.input_file import InputFile
    
    input_file = InputFile.from_bytes(file_content, filename=file.filename, mime_type=file.content_type)
    
    uploaded_file = storage.create_file(
        bucket_id=settings.RESUMES_BUCKET_ID,
        file_id=ID.unique(),
        file=input_file
    )
    file_id = uploaded_file['$id']

    # 3. Create/Find Candidate
    candidate_id = None
    
    if user_id != "guest":
        # Check if candidate profile exists for this user
        # Assuming we store 'user_id' in candidate doc or use same ID?
        # Let's search candidates by 'email' (if provided) or store user link
        # For simplicity, let's create a candidate doc if not exists
        pass
        # We need a robust way to link user to candidate. 
        # For now, let's assume we create a candidate with ID = unique() and link it?
        # Or search by email.
    
    # If no email provided, and guest, we rely on parser.
    # Create Candidate Document (Stub)
    candidate_data = {
        "email": email or "pending@parsing",
        "name": name or file.filename,
        "phone": phone,
        "experience_years": 0.0,
        "skills": []
    }
    
    candidate_doc = db.create_document(
        database_id=settings.DATABASE_ID,
        collection_id=settings.CANDIDATES_COLLECTION_ID,
        document_id=ID.unique(),
        data=candidate_data
    )
    candidate_id = candidate_doc['$id']

    # 4. Create Application
    app_data = {
        "job_id": job_id,
        "candidate_id": candidate_id,
        "resume_file_id": file_id,
        "status": "pending"
    }
    
    application_doc = db.create_document(
        database_id=settings.DATABASE_ID,
        collection_id=settings.APPLICATIONS_COLLECTION_ID,
        document_id=ID.unique(),
        data=app_data
    )

    # 5. Enqueue Task
    queue.enqueue(parse_resume_and_index, application_doc['$id'])

    logger.info(f"Application processed successfully: {application_doc['$id']}")
    return {"message": "Application received", "application_id": application_doc['$id']}

# --- Match / Search ---

@router.post("/jobs/{job_id}/match")
def match_candidates(job_id: str, user: dict = Depends(require_recruiter)):
    db = appwrite_service.get_database()
    
    # Get Job Description
    job = db.get_document(
        database_id=settings.DATABASE_ID,
        collection_id=settings.JOBS_COLLECTION_ID,
        document_id=job_id
    )
    
    logger.info(f"Matching candidates for job: {job.get('title', job_id)} ({job_id})")
    
    # Generate Embedding for job description
    # Ideally should cache this
    query_text = f"{job['title']} {job['requirements']} {job['description']}"
    query_vec = embedding_service.generate_embedding(query_text)
    
    # Search Qdrant for embeddings similar to job description embedding filtering by job id SCORING HAPPENS HERE
    results = vector_store.search_vectors( 
        query_embedding=query_vec,
        top_k=50,
        filter_metadata={"job_id": job_id}  
    ) 
    
    logger.info(f"Found {len(results)} candidates for job {job_id}")

    # Fetch full candidate details from Appwrite or just return metadata
    # Metadata has basic info.
    
    response = []
    for hit in results:
        response.append({
            "candidate_id": hit['metadata']['candidate_id'],
            "score": hit['score'],
            "match_percentage": round(hit['score'] * 100, 2), # approx
            # Fetch Candidate Doc?
            # "details": ...
        })
        
    return response

# --- Batch Upload ---
@router.post("/recruiter/jobs/{job_id}/batch-upload")
async def batch_upload(
    job_id: str,
    files: List[UploadFile] = File(...),
    user: dict = Depends(require_recruiter)
):
    # TODO: Implement batch logic
    # Iterate files, upload to storage, create app/candidate, enqueue
    
    count = 0
    batch_id = str(uuid.uuid4()) # Logical batch ID? 
    # Maybe store batch_id in application doc to track?
    
    db = appwrite_service.get_database()
    storage = appwrite_service.get_storage()
    from appwrite.input_file import InputFile

    for file in files:
        file_content = await file.read()
        input_file = InputFile.from_bytes(file_content, filename=file.filename, mime_type=file.content_type)
        
        uploaded = storage.create_file(
            bucket_id=settings.RESUMES_BUCKET_ID,
            file_id=ID.unique(),
            file=input_file
        )
        
        # Create Candidate & App
        cand = db.create_document(
            database_id=settings.DATABASE_ID,
            collection_id=settings.CANDIDATES_COLLECTION_ID,
            document_id=ID.unique(),
            data={
                "name": file.filename,
                "email": "batch@pending",
                "experience_years": 0.0,
                "skills": []
            } 
        )
        
        app = db.create_document(
            database_id=settings.DATABASE_ID,
            collection_id=settings.APPLICATIONS_COLLECTION_ID,
            document_id=ID.unique(),
            data={
                "job_id": job_id,
                "candidate_id": cand['$id'],
                "resume_file_id": uploaded['$id'],
                "status": "pending",
                "batch_id": batch_id
            }
        )
        
        queue.enqueue(parse_resume_and_index, app['$id'])
        count += 1

    return {"message": f"Queued {count} files", "batch_id": batch_id}

@router.get("/recruiter/batch/{batch_id}")
def get_batch_status(batch_id: str, user: dict = Depends(require_recruiter)):
    db = appwrite_service.get_database()
    from appwrite.query import Query

    # List applications with this batch_id
    # We need an index on batch_id in Appwrite for this to be efficient, or just list and filter (slow)
    # Assuming Query.equal("batch_id", batch_id) works (index needed)
    
    try:
        result = db.list_documents(
            database_id=settings.DATABASE_ID,
            collection_id=settings.APPLICATIONS_COLLECTION_ID,
            queries=[Query.equal("batch_id", batch_id)]
        )
    except Exception as e:
        # If index missing, might fail
        logger.warning(f"Batch query failed (index missing?): {e}")
        return {"error": "Could not query batch status. Ensure index on batch_id exists."}

    total = result['total']
    documents = result['documents']
    
    processed = sum(1 for doc in documents if doc.get('status') == 'processed')
    pending = sum(1 for doc in documents if doc.get('status') == 'pending')
    errors = sum(1 for doc in documents if doc.get('status') == 'error' or doc.get('status') == 'failed')
    
    error_samples = [
        doc.get('parsed_summary') for doc in documents 
        if doc.get('status') == 'failed' and doc.get('parsed_summary')
    ][:5]

    return {
        "batch_id": batch_id,
        "total": total,
        "processed": processed,
        "pending": pending,
        "errors": errors,
        "error_samples": error_samples
    }
