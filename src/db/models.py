from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from db.database import Base

class Matches(Base):
    __tablename__ = 'matches'

    id = Column(Integer, primary_key=True)
    espn_id = Column(String(255), unique=True, nullable=False)
    date = Column(DateTime, nullable=False, index=True)
    sport = Column(String(100), nullable=False)
    league = Column(String(100), nullable=False)
    matchup = Column(String(255), nullable=False)
    home_team = Column(String(100), nullable=False)
    away_team = Column(String(100), nullable=False)
    game_status = Column(String(100), nullable=False)
    poly_slug = Column(String(255),unique=True, nullable=False)

    observations = relationship("Observations", back_populates="match")

    def __repr__(self):
        return f"<Game: {self.matchup} - {self.date}>"


class Observations(Base):
    __tablename__ = 'observations'

    id = Column(Integer, primary_key=True)
    match_id = Column(Integer, ForeignKey('matches.id'), nullable=False, index=True)
    observed_at = Column(DateTime, nullable=False, index=True)
    home_odds = Column(String(50))
    away_odds = Column(String(50))
    draw_odds = Column(String(50))
    over_under_line = Column(String(50))
    over_odds = Column(String(50))
    under_odds = Column(String(50))
    source = Column(String(100), nullable=False)

    match = relationship("Matches", back_populates="observations")

    def __repr__(self):
        return f"<Observation: match_id={self.match_id} at {self.observed_at}>"



