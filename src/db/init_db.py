from src.db.database import Base, engine
from src.db import models

def init_db():
    """Create tables in the database Postgres"""
    Base.metadata.create_all(bind=engine)

if __name__ == "__main__":
    init_db()