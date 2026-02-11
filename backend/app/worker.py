import os
import tempfile
import logging
import json
from rq import Queue
from redis import Redis
from appwrite.services.databases import Databases
from appwrite.services.storage import Storage
from .core.config import settings
from .core.appwrite import appwrite_service
from .core.logging_config import setup_logging
from .services.gpt_parser import parser
from .services.embeddings import embedding_service
from .services.vector_store import vector_store
from .schemas import CandidateCreate, Application

# Determine if we should setup logging (running as worker)
if os.getenv("RQ_WORKER_LOGGING") == "true":
    setup_logging()

# Setup Redis connection
redis_conn = Redis.from_url(settings.REDIS_URL)
queue = Queue('resumes', connection=redis_conn)

logger = logging.getLogger(__name__)

def parse_resume_and_index(application_id: str):
    logger.info(f"Processing application: {application_id}")
    
    db = appwrite_service.get_database()
    storage = appwrite_service.get_storage()
    
    try:
        # 1. Get Application Document
        application_doc = db.get_document(
            database_id=settings.DATABASE_ID,
            collection_id=settings.APPLICATIONS_COLLECTION_ID,
            document_id=application_id
        )
        
        resume_file_id = application_doc['resume_file_id']
        candidate_id = application_doc['candidate_id']
        job_id = application_doc['job_id']
        
        # 2. Download Resume from Storage
        # get_file_download returns bytes
        file_bytes = storage.get_file_download(
            bucket_id=settings.RESUMES_BUCKET_ID,
            file_id=resume_file_id
        )
        
        # Save to temp file for parser
        # We need the extension to know how to parse
        file_meta = storage.get_file(
            bucket_id=settings.RESUMES_BUCKET_ID,
            file_id=resume_file_id
        )
        filename = file_meta['name']
        ext = os.path.splitext(filename)[1]
        
        with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as tmp_file:
            tmp_file.write(file_bytes)
            tmp_path = tmp_file.name
            
        # 3. Parse Resume
        logger.info(f"Parsing file: {tmp_path}")
        parsed_data = parser.parse(tmp_path)
        
        # Cleanup temp file
        os.remove(tmp_path)
        
        if "error" in parsed_data:
            logger.error(f"Parsing error: {parsed_data['error']}")
            db.update_document(
                database_id=settings.DATABASE_ID,
                collection_id=settings.APPLICATIONS_COLLECTION_ID,
                document_id=application_id,
                data={"status": "failed", "parsed_summary": json.dumps({"error": parsed_data["error"]})}
            )
            return

        # 4. Update Candidate Profile (if fields empty)
        candidate_doc = db.get_document(
            database_id=settings.DATABASE_ID,
            collection_id=settings.CANDIDATES_COLLECTION_ID,
            document_id=candidate_id
        )
        
        update_data = {}
        if not candidate_doc.get('email') and parsed_data.get('email'):
            update_data['email'] = parsed_data['email']
        if not candidate_doc.get('phone') and parsed_data.get('phone'):
            update_data['phone'] = parsed_data['phone']
        if not candidate_doc.get('name') or candidate_doc.get('name') == filename: # Update if name is just filename
             if parsed_data.get('name'):
                update_data['name'] = parsed_data['name']
        
        # Merge skills
        existing_skills = candidate_doc.get('skills', []) or []
        new_skills = parsed_data.get('skills', [])
        combined_skills = list(set(existing_skills + new_skills))
        if combined_skills:
            update_data['skills'] = combined_skills
            
        if parsed_data.get('experience_years'):
             # Update if experience is 0 or not present
             if not candidate_doc.get('experience_years'):
                 update_data['experience_years'] = float(parsed_data['experience_years'])

        if parsed_data.get('summary'):
             if not candidate_doc.get('summary'):
                 update_data['summary'] = parsed_data['summary']

        if update_data:
            db.update_document(
                database_id=settings.DATABASE_ID,
                collection_id=settings.CANDIDATES_COLLECTION_ID,
                document_id=candidate_id,
                data=update_data
            )

        # 5. Generate Embedding
        # Embed the raw text or the summary? Plan says resume text.
        text_to_embed = parsed_data.get('raw_text', '') or parsed_data.get('summary', '') or " "
        embedding = embedding_service.generate_embedding(text_to_embed)
        
        # 6. Upsert to Qdrant
        metadata = {
            "candidate_id": candidate_id,
            "application_id": application_id,
            "job_id": job_id,
            "resume_file_id": resume_file_id,
            "skills": combined_skills,
            "experience_years": parsed_data.get('experience_years', 0)
        }
        
        vector_id = vector_store.upsert_embedding(embedding, metadata)
        
        # 7. Update Application Status
        db.update_document(
            database_id=settings.DATABASE_ID,
            collection_id=settings.APPLICATIONS_COLLECTION_ID,
            document_id=application_id,
            data={
                "status": "processed",
                "parsed_summary": json.dumps(parsed_data.get('summary', '')),
                "embedding_id": vector_id
            }
        )
        
        logger.info(f"Successfully processed application {application_id}")

    except Exception as e:
        logger.error(f"Error processing application {application_id}: {e}")
        # Update status to error
        try:
             db.update_document(
                database_id=settings.DATABASE_ID,
                collection_id=settings.APPLICATIONS_COLLECTION_ID,
                document_id=application_id,
                data={"status": "error"}
            )
        except Exception:
            pass
