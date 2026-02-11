# Migration Guide: v1 (SQL) -> v2 (Appwrite + Vector)

This specific branch `feature/appwrite-vector-backend` replaces the PostgreSQL database with Appwrite and adds Vector Search via Qdrant.

## Prerequisites

1.  **Appwrite Cloud Account**: Create a project and API Key.
2.  **Qdrant**: Run via Docker Compose (`docker-compose up`).
3.  **Redis**: Run via Docker Compose (`docker-compose up`).

## Setup Steps

1.  **Environment Variables**:
    Copy `.env.example` to `backend/.env` and fill in:
    -   `APPWRITE_ENDPOINT`, `APPWRITE_PROJECT_ID`, `APPWRITE_API_KEY`
    -   `QDRANT_URL`, `REDIS_URL`

2.  **Initialize Appwrite Schema**:
    Run the setup script to create Collections, Attributes, and Indexes.
    ```bash
    python scripts/setup_appwrite.py
    ```

3.  **Data Migration (If preserving old data)**:
    -   There is no automatic script to migrate existing SQL data to Appwrite in this PR.
    -   **Manual Strategy**:
        1.  Export `jobs` and `candidates` from Postgres to JSON/CSV.
        2.  Write a script to iterate over the export and call Appwrite API (similar to `setup_appwrite.py`) to insert documents.
        3.  Re-process resumes to generate embeddings (since v1 didn't have Qdrant embeddings).

## Running the Backend

1.  Start Docker Services:
    ```bash
    docker-compose up -d
    ```

2.  Start Backend API:
    ```bash
    uvicorn backend.app.main:app --reload
    ```

3.  Start Background Worker:
    ```bash
    # From project root
    rq worker resumes --url redis://localhost:6379/0
    ```
