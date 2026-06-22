import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, Column, Integer, String, Date, DateTime, Float, Boolean
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.sql import func


load_dotenv()


DATABASE_URL = os.environ.get("DATABASE_URL")


if not DATABASE_URL:
    raise ValueError("DATABASE_URL environment variable is not set!")

engine = create_engine(DATABASE_URL)
Base = declarative_base()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

class Match(Base):
    __tablename__ = "matches"

    id = Column(Integer, primary_key=True, index=True)
    sport = Column(String)
    league = Column(String)
    date = Column(DateTime(timezone=True))
    espn_id = Column(String, unique=True, index=True)
    away_team = Column(String)
    away_team_win_percentage = Column(Float)
    home_team = Column(String)
    home_team_win_percentage = Column(Float)
    name = Column(String)
    short_name = Column(String)
    poly_slug = Column(String) # polymarket.com('/sports/nba/nba-nyk-sas-2026-06-13')
    status_name = Column(String)
    is_completed = Column(Boolean)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

# create tables
def init_db():
    Base.metadata.create_all(bind=engine)
    print("Database tables created successfully!")

# A helper function to manage database sessions safely
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

if __name__ == "__main__":
    init_db()