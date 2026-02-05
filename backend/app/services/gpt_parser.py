import os
import re
import json
import logging
import google.generativeai as genai
from dotenv import load_dotenv
from typing import Dict, List, Optional, Any

load_dotenv('backend/.env')
from pypdf import PdfReader
from docx import Document
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Constants
SECTION_HEADERS = {
    "skills": ["skills", "technical skills", "core competencies"],
    "experience": ["experience", "work experience", "employment"],
    "education": ["education", "academic"],
    "projects": ["projects"],
    "summary": ["about me", "summary", "profile"]
}

class ResumeParser:
    def __init__(self):
        api_key = os.environ.get("GOOGLE_API_KEY") or os.environ.get("GEMINI_API_KEY")
        if api_key:
            genai.configure(api_key=api_key)
            self.model = genai.GenerativeModel('gemini-2.5-flash')
            self.has_llm = True
        else:
            logger.warning("No Gemini API Key found. Falling back to Regex-only mode.")
            self.has_llm = False

    def parse(self, file_path: str) -> Dict[str, Any]:
        """
        Main entry point for parsing.
        """
        try:
            raw_text = self._extract_text(file_path)
        except Exception as e:
            logger.error(f"Text extraction failed: {e}")
            return {"error": f"Failed to read file: {str(e)}"}

        clean_text = self._clean_text(raw_text)
        
        # Layer 1: Deterministic Regex (Always run these)
        basics = {
            "email": self._extract_email(clean_text),
            "phone": self._extract_phone(clean_text),
            "links": self._extract_links(clean_text)
        }

        # Layer 2: LLM Extraction (with fallback)
        llm_data = {}
        if self.has_llm:
            try:
                llm_data = self._extract_with_gemini(clean_text)
            except Exception as e:
                logger.error(f"Gemini extraction failed: {e}")
                # Fallback to regex logic if LLM fails
                llm_data = self._extract_regex_fallback(clean_text)
        else:
            llm_data = self._extract_regex_fallback(clean_text)

        # Merge results (LLM overwrites Regex fallback, but Regex basics persist)
        # Note: If LLM returns None for email/phone, we prefer Regex result usually, 
        # but here we separate "basics" (reliable regex) vs "content" (LLM/Regex).
        
        # Consolidate
        result = {**basics, **llm_data}
        result["raw_text"] = clean_text # Store raw text for search/debugging
        
        return result

    def _extract_text(self, file_path: str) -> str:
        if not os.path.exists(file_path):
            raise FileNotFoundError(file_path)

        ext = os.path.splitext(file_path)[1].lower()
        if ext == ".pdf":
            text = ""
            try:
                reader = PdfReader(file_path)
                for page in reader.pages:
                    text += page.extract_text() + "\n"
            except Exception:
                pass # Simple fallback
            return text
        elif ext in [".docx", ".doc"]:
            doc = Document(file_path)
            return "\n".join(p.text for p in doc.paragraphs if p.text.strip())
        else:
            raise ValueError(f"Unsupported file type: {ext}")

    def _clean_text(self, text: str) -> str:
        text = text.replace("\t", " ")
        text = re.sub(r"[•●▪]", "-", text)
        text = re.sub(r"\n{2,}", "\n\n", text)
        return text.strip()

    # --- Layer 1: Regex Basics ---
    def _extract_email(self, text: str) -> Optional[str]:
        match = re.search(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+", text)
        return match.group(0) if match else None

    def _extract_phone(self, text: str) -> Optional[str]:
        # Broad regex for phone numbers
        match = re.search(r"(\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}", text)
        return match.group(0) if match else None

    def _extract_links(self, text: str) -> List[str]:
        return re.findall(r"(https?://\S+)", text)

    # --- Layer 2: Gemini LLM ---
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    def _extract_with_gemini(self, text: str) -> Dict[str, Any]:
        """
        Extracts structured data using Gemini Flash.
        Incudes retry logic for Rate Limits (429).
        """
        prompt = f"""
        You are an expert HR Resume Parser. Extract the following information from the resume text below.
        Return ONLY a raw JSON object. Do not use Markdown formatting.
        
        Keys required:
        - name: Full name of the candidate.
        - skills: List[str] of technical skills, languages, tools.
        - experience_years: Float estimate of total years of experience.
        - summary: A concise 2-sentence professional summary of the candidate.
        - education: List of degrees/universities.
        
        Resume Text:
        {text[:15000]} 
        """ 
        # Truncate to avoid token limits if extremely large, though Flash context is huge.

        response = self.model.generate_content(
            prompt,
            generation_config={"response_mime_type": "application/json"}
        )
        
        return json.loads(response.text)

    # --- Layer 3: Regex Fallback (From original gpt_parser) ---
    def _extract_regex_fallback(self, text: str) -> Dict[str, Any]:
        logger.info("Using Regex Fallback Strategy")
        
        # Name (First non-empty line assumption)
        lines = [l for l in text.split('\n') if l.strip()]
        name = lines[0].strip() if lines else "Unknown"
        
        # Experience Years (Simple date math)
        years = []
        for match in re.findall(r"(20\d{2})\s*-\s*(present|20\d{2})", text.lower()):
            start = int(match[0])
            end = 2024 if match[1] == "present" else int(match[1]) # Hardcoded 2024 for safety
            years.append(end - start)
        total_exp = round(sum(years), 1) if years else 0.0
        
        # Skills (Simple Keyword Match)
        # We can implement a larger list here if needed, or use the one from known skills
        known_skills = {
            "python", "sql", "javascript", "react", "java", "c++", "aws", "docker", 
            "kubernetes", "machine learning", "pytorch", "tensorflow", "git"
        }
        text_lower = text.lower()
        found_skills = [s for s in known_skills if s in text_lower]
        
        return {
            "name": name,
            "skills": sorted(found_skills),
            "experience_years": total_exp,
            "summary": "Extracted via Regex (LLM unavailable).",
            "education": [] 
        }

parser = ResumeParser()