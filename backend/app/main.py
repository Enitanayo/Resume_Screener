from fastapi import FastAPI
from .core.logging_config import setup_logging
import logging

from .api import router

app = FastAPI(title="Resume Screening MVP v2")

app.include_router(router)

@app.on_event("startup")
def on_startup():
    setup_logging()
    logging.info("Application starting up (v2 - Appwrite + Qdrant)...")

@app.get("/health")
def health_check():
    return {"status": "ok", "version": "v2"}
