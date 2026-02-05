from sqlmodel import Session, select
from .db import engine
from .models import Candidate, Job
from .services.gpt_parser import parser
from .services.embeddings import embedding_service
from .services.scorer import scoring_service
from .core.exceptions import ParserException
import json
import logging

logger = logging.getLogger(__name__)

def process_application(candidate_id: int):
    """
    Background task to process a candidate application.
    1. Extract text (Hybrid)
    2. Generate embedding
    3. Calculate score
    1. Extract text (Hybrid)
    2. Generate embedding
    3. Calculate score
    """
    logger.info(f"Processing candidate {candidate_id}...")
    with Session(engine) as session:
        candidate = session.get(Candidate, candidate_id)
        if not candidate:
            logger.error(f"Candidate {candidate_id} not found.")
            return

        job = session.get(Job, candidate.job_id)
        if not job:
            logger.error(f"Job {candidate.job_id} not found.")
            return

        try:
            logger.info(f"--- [Candidate {candidate_id}] START Processing ---")
            candidate.status = "processing"
            session.add(candidate)
            session.commit()
            
            # 1. Parse Resume (Hybrid: Regex + Gemini)
            logger.info(f"--- [Candidate {candidate_id}] Step 1: Parsing Resume ---")
            parsed_data = parser.parse(candidate.resume_path)
            
            if "error" in parsed_data:
                raise ParserException(parsed_data["error"])
                
            # Extract fields
            text = parsed_data.get("raw_text", "")
            candidate.extracted_text = text
            candidate.name = parsed_data.get("name", candidate.name) 
            candidate.email = parsed_data.get("email", candidate.email)
            candidate.phone = parsed_data.get("phone", candidate.phone)
            candidate.skills = parsed_data.get("skills", [])
            candidate.experience_years = parsed_data.get("experience_years", 0.0)
            
            logger.info(f"--- [Candidate {candidate_id}] Parsed Data: Name='{candidate.name}', SkillsCount={len(candidate.skills)}, Exp={candidate.experience_years}y ---")

            
            # 2. Embedding
            logger.info(f"--- [Candidate {candidate_id}] Step 2: Generating Embeddings ---")
            candidate_embedding = embedding_service.generate_embedding(text)
            candidate.embedding = candidate_embedding
            
            # Embed the job description on fly
            job_text = f"{job.title} {job.description} {job.requirements}"
            job_embedding = embedding_service.generate_embedding(job_text)
            
            # Specific Embeddings for Scoring
            requirements_embedding = embedding_service.generate_embedding(job.requirements)
            skills_text = ", ".join(candidate.skills) if candidate.skills else ""
            skills_embedding = embedding_service.generate_embedding(skills_text)
            
            logger.info(f"--- [Candidate {candidate_id}] Embeddings Generated. ---")
            
            # 3. Score
            logger.info(f"--- [Candidate {candidate_id}] Step 3: Scoring ---")
            job_skills = [s.strip() for s in job.requirements.split(',')]
            
            result = scoring_service.calculate_match(
                job_embedding=job_embedding, 
                candidate_embedding=candidate_embedding,
                job_requirements_embedding=requirements_embedding,
                candidate_skills_embedding=skills_embedding,
                job_skills=job_skills, 
                candidate_text=text
            )
            
            logger.info(f"--- [Candidate {candidate_id}] Scoring Result: Total={result['total_score']} (Skills={result['skills_semantic_score']}, Context={result['context_score']}, Keywords={result['keyword_score']}) ---")
            
            # 4. LLM Explanation
            logger.info(f"--- [Candidate {candidate_id}] Step 4: Generating Explanation ---")
            from .services.llm import llm_service
            explanation = llm_service.explain_match(job.title, job.requirements, text, result["total_score"])
            
            candidate.match_score = result["total_score"]
            candidate.score_breakdown = result
            candidate.summary = explanation
            candidate.status = "completed"
            
            session.add(candidate)
            session.commit()
            logger.info(f"--- [Candidate {candidate_id}] FINISHED Processing Successfully. ---")
            
        except Exception as e:
            logger.exception(f"--- [Candidate {candidate_id}] FAILED: {e} ---")
            candidate.summary = f"Error: {str(e)}"
            candidate.status = "failed"
            session.add(candidate)
            session.commit()
