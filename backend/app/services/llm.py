import os
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv('backend/.env')
import logging
from tenacity import retry, stop_after_attempt, wait_exponential

logger = logging.getLogger(__name__)

class LLMService:
    def __init__(self):
        api_key = os.environ.get("GOOGLE_API_KEY") or os.environ.get("GEMINI_API_KEY")
        if api_key:
            genai.configure(api_key=api_key)
            self.model = genai.GenerativeModel('gemini-2.5-flash')
            self.has_llm = True
        else:
            logger.warning("No Gemini API Key found. Explanation service disabled.")
            self.has_llm = False

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    def explain_match(self, job_title: str, requirements: str, candidate_text: str, score: float) -> str:
        if not self.has_llm:
             return "LLM Explanation unavailable (No API Key). details: Candidate skills and experience were compared against job requirements."
        
        # Construct a concise prompt
        prompt = f"""
        Role: HR Assistant. 
        Task: Explain why this candidate got a score of {score:.2f} (0-1 scale) for the role of '{job_title}'.
        
        Job Requirements: {requirements}
        
        Candidate Summary/Snippet:
        {candidate_text[:3000]}
        
        Output:
        Provide a 3-bullet point summary explaining the score. Focus on:
        1. Key skills matched.
        2. Missing critical requirements (if any).
        3. Experience level alignment.
        Keep it professional and concise.
        """
        
        try:
            response = self.model.generate_content(prompt)
            return response.text.strip()
        except Exception as e:
            logger.error(f"LLM generation failed: {e}")
            return "Explanation generation failed currently."

llm_service = LLMService()
