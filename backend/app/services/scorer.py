from typing import List, Dict
from .util import cos_sim
import numpy as np

class ScoringService:
    def calculate_match(self, job_embedding: List[float], candidate_embedding: List[float], 
                       job_requirements_embedding: List[float], candidate_skills_embedding: List[float],
                       job_skills: List[str], candidate_text: str) -> Dict:
        """
        Refined Scoring (Phase 5):
        1. Semantic Skills Match (Skills Vector vs Requirements Vector) - 60%
        2. Overall Context Match (Resume Vector vs Job Vector) - 20%
        3. Hard Keyword Match (Exact skill hits) - 20%
        """
        
        # 1. Semantic Skills Match (60%)
        skills_score = 0.0
        if job_requirements_embedding and candidate_skills_embedding:
            # use util.cos_sim
            try:
                # cos_sim returns a matrix (1x1 for single vectors)
                score_matrix = cos_sim(job_requirements_embedding, candidate_skills_embedding)
                skills_score = float(score_matrix[0][0])
            except Exception:
                skills_score = 0.0
        
        # 2. Overall Context Match (20%)
        context_score = 0.0
        if job_embedding and candidate_embedding:
            try:
                score_matrix = cos_sim(job_embedding, candidate_embedding)
                context_score = float(score_matrix[0][0])
            except Exception:
                context_score = 0.0
        
        # 3. Hard Keyword Match (20%)
        keyword_score = 0.0
        matched_skills = []
        if job_skills and candidate_text:
            text_lower = candidate_text.lower()
            matches = 0
            for skill in job_skills:
                if skill.lower() in text_lower:
                    matches += 1
                    matched_skills.append(skill)
            
            if len(job_skills) > 0:
                keyword_score = matches / len(job_skills)
        
        # Weighted Sum
        final_score = (skills_score * 0.6) + (context_score * 0.2) + (keyword_score * 0.2)
        
        return {
            "total_score": round(max(0.0, final_score), 2),
            "skills_semantic_score": round(max(0.0, skills_score), 2),
            "context_score": round(max(0.0, context_score), 2),
            "keyword_score": round(keyword_score, 2),
            "matched_skills": matched_skills
        }

scoring_service = ScoringService()
