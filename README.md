# Resume Screening MVP (Backend v2)

This backend facilitates Resume Screening using **Appwrite** for data/auth and **Qdrant** for vector search.

## Features

-   **Resume Parsing**: Automatically extracts skills, experience, and contact info from PDF/DOCX resumes.
-   **Vector Search**: Embeds resume text and allows semantic search for candidates matching job descriptions.
-   **Batch Processing**: Recruiter can upload zip archives or multiple resumes for batch processing.
-   **RBAC**: Role-based access control (Recruiter vs Candidate).

## Tech Stack

-   **Framework**: FastAPI
-   **Database & Auth**: Appwrite Cloud
-   **Vector Store**: Qdrant (local via Docker)
-   **Background Tasks**: RQ (Redis Queue)
-   **Embeddings**: OpenAI (default) or Local (SentenceTransformers)

## Setup

1.  **Prerequisites**:
    -   Docker & Docker Compose
    -   Python 3.10+
    -   Appwrite Cloud Account (Project ID, API Key)

2.  **Environment Variables**:
    Copy `.env.example` to `backend/.env` and fill in the details.
    
    ```bash
    cp .env.example backend/.env
    ```

3.  **Start Services**:
    ```bash
    docker-compose up -d
    ```
    This starts Qdrant and Redis.

4.  **Install Dependencies**:
    ```bash
    pip install -r backend/requirements.txt
    ```

5.  **Initialize Appwrite**:
    Run the setup script to create collections and attributes.
    ```bash
    python scripts/setup_appwrite.py
    ```

6.  **Run Backend**:
    ```bash
    uvicorn backend.app.main:app --reload
    ```

7.  **Run Worker**:
    ```bash
    # Linux/Mac
    rq worker resumes --url redis://localhost:6379/0

    # Windows (os.fork() is not supported)
    rq worker resumes --worker-class rq.SimpleWorker --url redis://localhost:6379/0
    ```

## API Documentation

Access the Swagger UI at `http://localhost:8000/docs`.

## Testing

Run tests using pytest:

```bash
# Run v2 API tests
python -m pytest backend/tests/test_api_v2.py
```

## Migration

See `MIGRATION.md` for details on moving from v1.
