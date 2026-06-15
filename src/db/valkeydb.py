import redis
import logging
from src.db.database import Match
from src.db.pg_utils import get_db

# Connect
valkey = redis.Redis(host='localhost', port=6380, db=0, decode_responses=True)


def sync_matches_from_postgres():
    """
    Sync Valkey with Postgres:
    - Add new matches from Postgres
    - Remove matches from Valkey that no longer exist in Postgres
    """
    with get_db() as db:  # <-- THIS is the fix, no more next()
        matches = db.query(Match).all()

        postgres_espn_ids = {str(match.espn_id) for match in matches}
        valkey_espn_ids = {key.split(":")[1] for key in valkey.scan_iter("match:*")}

        stale_ids = valkey_espn_ids - postgres_espn_ids
        new_ids = postgres_espn_ids - valkey_espn_ids

        pipe = valkey.pipeline()

        for espn_id in stale_ids:
            pipe.delete(f"match:{espn_id}")

        for match in matches:
            if str(match.espn_id) in new_ids:
                pipe.hset(f"match:{match.espn_id}", mapping={
                    "polymarket_odds": "",
                    "espn_win_prob": "",
                })

        pipe.execute()

    logging.info(f"Sync complete: +{len(new_ids)} added, -{len(stale_ids)} removed, {len(postgres_espn_ids)} total")


def get_match(espn_id: str) -> dict:
    """Get all fields for a match"""
    return valkey.hgetall(f'match:{espn_id}')


def update_polymarket_odds(espn_id: str, odds: str):
    """Update live odds from Polymarket."""
    valkey.hset(f"match:{espn_id}", "polymarket_odds", odds)


def update_espn_win_prob(espn_id: str, prob: str):
    """Update live odds from Espn."""
    valkey.hset(f"match:{espn_id}", "espn_win_prob", prob)


def get_all_matches() -> dict:
    """Get all matches from valkey"""
    matches = {}
    for key in valkey.scan_iter("match:*"):
        espn_id = key.split(":")[1]
        matches[espn_id] = valkey.hgetall(key)
    return matches


if __name__ == "__main__":
    sync_matches_from_postgres()