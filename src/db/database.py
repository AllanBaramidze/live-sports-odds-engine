import os
from dotenv import load_dotenv
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

CURRENT_DIR = Path(__file__).resolve().parent

PROJECT_ROOT = CURRENT_DIR.parent.parent

ENV_LOCAL = PROJECT_ROOT / ".env.local"
ENV = PROJECT_ROOT / ".env"

load_dotenv(dotenv_path=ENV_LOCAL)

DATABASE_URL = os.getenv("POSTGRES_URL")

# Create Connection to DB
engine = create_engine(DATABASE_URL)

# Session Local
SessionLocal = sessionmaker(bind=engine)

# Base Class for SQLAlchemy Models (Create Table)
Base = declarative_base()

# Function to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()