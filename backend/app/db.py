from sqlmodel import SQLModel, create_engine, Session
from .models import * # Import models to register them
import os
from dotenv import load_dotenv

load_dotenv('backend/.env')

DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///./resume.db")

engine = create_engine(DATABASE_URL, echo=True)

def get_session():
    with Session(engine) as session:
        yield session

def create_db_and_tables():
    from sqlalchemy import text
    with engine.connect() as conn:
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        conn.commit()
    SQLModel.metadata.create_all(engine)
