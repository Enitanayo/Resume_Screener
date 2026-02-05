from typing import Optional, List
from datetime import datetime, timezone
from sqlmodel import Field, SQLModel, Relationship, JSON
from pgvector.sqlalchemy import Vector
from sqlalchemy import Column

class JobBase(SQLModel):
    title: str
    description: str
    requirements: str
    is_active: bool = True

class Job(JobBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    candidates: List["Candidate"] = Relationship(back_populates="job")

class CandidateBase(SQLModel):
    email: str
    name: Optional[str] = None
    phone: Optional[str] = None
    extracted_text: Optional[str] = None
    skills: Optional[List[str]] = Field(default=None, sa_column=Column(JSON))
    experience_years: Optional[float] = None
    status: str = Field(default="pending")

class Candidate(CandidateBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    job_id: Optional[int] = Field(default=None, foreign_key="job.id")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    resume_path: str
    
    # Embedding: 384 dimensions for all-MiniLM-L6-v2
    # For SQLite compatibility in MVP, we use JSON.
    # In Postgres with pgvector, use: sa_column=Column(Vector(384))
    embedding: Optional[List[float]] = Field(default=None, sa_column=Column(JSON))
    
    # Scoring
    match_score: Optional[float] = None
    score_breakdown: Optional[dict] = Field(default=None, sa_column=Column(JSON))
    summary: Optional[str] = None
    
    job: Optional[Job] = Relationship(back_populates="candidates")

class JobCreate(JobBase):
    pass

class CandidateCreate(CandidateBase):
    pass
