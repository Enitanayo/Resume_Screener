import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    # Appwrite
    APPWRITE_ENDPOINT: str = os.getenv("APPWRITE_ENDPOINT", "https://cloud.appwrite.io/v1")
    APPWRITE_PROJECT_ID: str = os.getenv("APPWRITE_PROJECT_ID", "")
    APPWRITE_API_KEY: str = os.getenv("APPWRITE_API_KEY", "")
    
    # Qdrant
    QDRANT_URL: str = os.getenv("QDRANT_URL", "http://localhost:6333")
    QDRANT_API_KEY: str = os.getenv("QDRANT_API_KEY", "")

    # Redis
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")

    # Embeddings
    EMBEDDING_PROVIDER: str = os.getenv("EMBEDDING_PROVIDER", "mock")
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")

    # Worker
    WORKER_CONCURRENCY: int = int(os.getenv("WORKER_CONCURRENCY", "4"))

    # Uploads
    MAX_RESUME_FILE_SIZE_MB: int = int(os.getenv("MAX_RESUME_FILE_SIZE_MB", "10"))
    ALLOWED_RESUME_TYPES: list = os.getenv("ALLOWED_RESUME_TYPES", "pdf,docx,txt").split(",")
    
    # Collections (Hardcoded or could be envs)
    DATABASE_ID: str = "default" # Or use env if needed
    JOBS_COLLECTION_ID: str = "jobs"
    CANDIDATES_COLLECTION_ID: str = "candidates"
    APPLICATIONS_COLLECTION_ID: str = "applications"
    RESUMES_BUCKET_ID: str = "resumes"


settings = Settings()
