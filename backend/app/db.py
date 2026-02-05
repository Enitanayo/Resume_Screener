from sqlmodel import SQLModel, create_engine, Session
from .models import * # Import models to register them
import os

DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///./resume.db")

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False}, echo=True)

def get_session():
    with Session(engine) as session:
        yield session

def create_db_and_tables():
    SQLModel.metadata.create_all(engine)
