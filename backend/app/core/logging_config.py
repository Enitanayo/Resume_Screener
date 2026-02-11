import logging
import os
import sys
from datetime import datetime
from pathlib import Path

# Create logs directory at project root (or relative to this file)
# Assuming run from backend/ or project root. We want PROJECT_ROOT/backend/logs
# Let's anchor to this file: backend/app/core/logging_config.py -> backend/logs
BASE_DIR = Path(__file__).resolve().parent.parent.parent
LOGS_DIR = BASE_DIR / "logs"

def setup_logging():
    """
    Configures logging to write to a timestamped folder/file structure.
    Also logs to console.
    """
    now = datetime.now()
    timestamp_str = now.strftime("%Y-%m-%d_%H-%M-%S")
    
    # Create specific session folder
    session_log_dir = LOGS_DIR / timestamp_str
    session_log_dir.mkdir(parents=True, exist_ok=True)
    
    # Create log file path
    log_file = session_log_dir / f"{timestamp_str}.log"
    
    # Configure Root Logger
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    
    # Formatter
    formatter = logging.Formatter(
        "%(asctime)s - [%(name)s] - %(levelname)s - %(message)s"
    )
    
    # 1. File Handler
    file_handler = logging.FileHandler(log_file)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    
    # 2. Stream Handler (Console)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    logging.info(f"Logging initialized. Writing to {log_file}")
    
    # Quiet down some libraries
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    
    # Silence SQLModel/SQLAlchemy noise
    logging.getLogger("sqlalchemy").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.pool").setLevel(logging.WARNING)
    logging.getLogger("sqlmodel").setLevel(logging.WARNING)
    
    # Optional: Silence uvicorn access logs if they are too noisy, or keep INFO
    # logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    
    # Force uvicorn logs to propagate to root logger (so they appear in file)
    for log_name in ["uvicorn", "uvicorn.error", "uvicorn.access", "fastapi"]:
        log = logging.getLogger(log_name)
        log.propagate = True
        # Ensure they don't have duplicate handlers if uvicorn set them up
        # We can leave them; propagation means they go to root too.
        
    return logger
