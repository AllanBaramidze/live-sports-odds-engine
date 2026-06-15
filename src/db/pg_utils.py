import logging
from contextlib import contextmanager
from src.db.database import SessionLocal, Match

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


@contextmanager
def get_db():
    """Context manager to ensure database sessions are closed automatically."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_all_matches():
    """Returns all Match records."""
    with get_db() as db:
        matches = db.query(Match).all()
        logger.info(f"Retrieved {len(matches)} matches from database.")
        return matches


def get_all_espn_ids():
    """Returns a flat list of ESPN IDs only."""
    with get_db() as db:
        # .with_entities is faster as it only selects the specific column
        results = db.query(Match.espn_id).all()
        espn_ids = [r.espn_id for r in results]
        logger.info(f"Retrieved {len(espn_ids)} ESPN IDs.")
        return espn_ids


if __name__ == "__main__":
    # Test calls
    all_matches = get_all_matches()
    ids = get_all_espn_ids()

    if ids:
        logger.debug(f"First ID: {ids[0]}")