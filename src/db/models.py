from sqlalchemy import Column, Integer, String, DateTime, UniqueConstraint
from src.db.database import Base

class Matches(Base):
    __tablename__ = 'matches'

    id = Column(Integer, primary_key=True)
    espn_id = Column(String(255), unique=True, nullable=False)
    date = Column(DateTime, nullable=False)
    sport = Column(String(100), nullable=False)
    league = Column(String(100), nullable=False)
    matchup = Column(String(255), nullable=False)
    home_team = Column(String(100), nullable=False)
    away_team = Column(String(100), nullable=False)
    poly_slug = Column(String(255),unique=True, nullable=False)

    def __repr__(self):
        return f"<Game: {self.matchup} - {self.date}>"