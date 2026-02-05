from fastapi import FastAPI
from .db import create_db_and_tables
from .core.logging_config import setup_logging
import logging

from .api import router

app = FastAPI(title="Resume Screening MVP")

app.include_router(router)

@app.on_event("startup")
def on_startup():
    setup_logging()
    logging.info("Application starting up...")
    # In production, use Alembic. For MVP, this allows quick iteration.
    create_db_and_tables()

@app.get("/health")
def health_check():
    return {"status": "ok"}
