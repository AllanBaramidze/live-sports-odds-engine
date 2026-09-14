"""
Holds Database operations that take a Session as an argument.
It never creates sessions or commits. It knows nothing about ESPN's HTTP API.
"""

from typing import Any
from sqlalchemy.orm import Session
from sqlalchemy.dialects.postgresql import insert
from db.models import Matches



class MatchRepository:
    def __init__(self, session: Session):
        self.session = session

    # Bulk Upsert Match
    def upsert_match(self, match_list: list[dict[str, Any]]) -> None:
        """
        Inserts new matches or updates existing ones on espn_id conflict
        :param match_list:
        :return:
        """
        if not match_list:
            return

        stmt = insert(Matches).values(match_list)

        # Columns to update on conflict
        update_cols = {
            "date": stmt.excluded.date,
            "matchup": stmt.excluded.matchup,
            "home_team": stmt.excluded.home_team,
            "away_team": stmt.excluded.away_team,
            "game_status": stmt.excluded.game_status,
            "poly_slug": stmt.excluded.poly_slug,
        }

        upsert_stmt = stmt.on_conflict_do_update(index_elements=["espn_id"], set_=update_cols)
        self.session.execute(upsert_stmt)

    # Delete Matches Based on Completion
    #TODO  def delete_matches(self, date: str) -> None:


# Querying Matches
# Get by ESPN ID
# Get by Poly Slug
# Get by SCHEDULED
# Get by FINISHED