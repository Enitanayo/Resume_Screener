from pydantic import BaseModel, Field, EmailStr
from typing import List, Optional, Any
from datetime import datetime

# Job Schemas
class JobBase(BaseModel):
    title: str
    description: str
    requirements: str
    is_active: bool = True
    recruiter_id: str

class JobCreate(JobBase):
    pass

class Job(JobBase):
    id: str = Field(alias="$id")
    created_at: str = Field(alias="$createdAt")
    updated_at: str = Field(alias="$updatedAt")

    class Config:
        populate_by_name = True

# Candidate Schemas
class CandidateBase(BaseModel):
    name: Optional[str] = None
    email: str
    phone: Optional[str] = None
    skills: List[str] = []
    experience_years: float = 0.0
    summary: Optional[str] = None
    linkedin_url: Optional[str] = None
    github_url: Optional[str] = None

class CandidateCreate(CandidateBase):
    pass

class Candidate(CandidateBase):
    id: str = Field(alias="$id")
    created_at: str = Field(alias="$createdAt")
    updated_at: str = Field(alias="$updatedAt")
    
    class Config:
        populate_by_name = True

# Application Schemas
class ApplicationBase(BaseModel):
    job_id: str
    candidate_id: str
    resume_file_id: str
    status: str = "pending" # pending, parsed, embedded, reviewed

class ApplicationCreate(ApplicationBase):
    pass

class Application(ApplicationBase):
    id: str = Field(alias="$id")
    created_at: str = Field(alias="$createdAt")
    updated_at: str = Field(alias="$updatedAt")
    parsed_summary: Optional[str] = None
    embedding_id: Optional[str] = None
    batch_id: Optional[str] = None
    match_score: Optional[float] = None # Not stored in DB, but returned in search
    
    class Config:
        populate_by_name = True
