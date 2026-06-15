import logging
import pprint
from typing import Any, Dict, List, Optional

from django.conf import settings

# Configure Django settings before importing dependent local modules
if not settings.configured:
    settings.configure(DEBUG=True)

from clients.espn_client import get_espn_client

from src.db.database import SessionLocal, Match, init_db

# Configure module-level logger
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

ESPN_CONFIG: Dict[str, Dict[str, str]] = {
    'nba': {
        'sport': 'basketball',
        'league': 'nba',
    },
    'mlb': {
        'sport': 'baseball',
        'league': 'mlb',
    }
}


class ESPNScheduleIngest:
    """
    Handles the ingestion and enrichment of daily sports schedules via the ESPN API.
    """

    def __init__(self, sport: str, league: str) -> None:
        """
        Initialize the ingestion client for a specific sport and league.

        Args:
            sport (str): The name of the sport (e.g., 'basketball').
            league (str): The name of the league (e.g., 'nba').
        """
        self.sport = sport
        self.league = league
        self.client = get_espn_client()

    def ingest_schedule(self) -> List[Dict[str, Any]]:
        """
        Fetches and parses the daily schedule data from the ESPN scoreboard API.

        Returns:
            List[Dict[str, Any]]: A list of dictionaries, where each dictionary
            represents the core details of a scheduled game.
        """
        logger.info("Fetching schedule for %s - %s...", self.sport, self.league)

        sb_response = self.client.get_scoreboard(self.sport, self.league, None, 100)

        # Defensive check: ensure data exists before parsing
        if not sb_response or not hasattr(sb_response, 'data'):
            logger.warning("Invalid or empty response received from scoreboard API.")
            return []

        events: List[Dict[str, Any]] = sb_response.data.get("events", [])
        cleaned_games: List[Dict[str, Any]] = []

        for event in events:
            competitions = event.get("competitions", [])
            competition_data = competitions[0] if competitions else {}
            competitors_data = competition_data.get("competitors", [])

            home_team = next((t for t in competitors_data if t.get('homeAway') == 'home'), {})
            away_team = next((t for t in competitors_data if t.get('homeAway') == 'away'), {})

            home_team_name = home_team.get('team', {}).get('displayName', 'Unknown Home Team')
            away_team_name = away_team.get('team', {}).get('displayName', 'Unknown Away Team')

            status_data = event.get('status', {})
            status_type = status_data.get('type', {})
            completed_status = status_type.get('completed', False)
            is_game_finished = str(completed_status).lower() == 'true'

            game_data = {
                'sport': self.sport,
                'league': self.league,
                'espn_id': event.get('id'),
                'date': event.get('date'),
                'home_team': home_team_name,
                'away_team': away_team_name,
                'name': event.get('name'),
                'short_name': event.get('shortName'),
                'status_name': status_type.get('name'),
                'is_completed': is_game_finished,
            }
            cleaned_games.append(game_data)

        logger.info("Successfully ingested %d games.", len(cleaned_games))
        return cleaned_games

    def enrich_probabilities(self, cleaned_games: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Appends pregame win probabilities to a list of previously parsed games.

        :param cleaned_games: The list of game dictionaries from `ingest_schedule`.
        :return: List[Dict[str, Any]]: An ordered list of games enriched with home and away win percentages.
        """
        if not cleaned_games:
            logger.info("No games provided to enrich.")
            return []

        logger.info("Enriching %d games with win probabilities...", len(cleaned_games))
        ordered_enriched_games: List[Dict[str, Any]] = []

        for game in cleaned_games:
            game_id = game.get('espn_id')
            if not game_id:
                logger.warning("Game missing 'espn_id', skipping enrichment for: %s", game.get('name'))
                continue

            get_prediction = self.client.get_game_predictor(
                sport=self.sport,
                league=self.league,
                event_id=game_id,
                competition_id=game_id
            )

            pred_data = get_prediction.data if hasattr(get_prediction, 'data') else get_prediction
            away_team_data = pred_data.get("awayTeam", {})
            statistics_list = away_team_data.get("statistics", [])

            away_win_prob: Optional[float] = None
            for stat in statistics_list:
                if stat.get('name') == 'gameProjection':
                    try:
                        away_win_prob = float(stat.get('value'))
                    except (ValueError, TypeError):
                        logger.error("Failed to parse gameProjection value for game %s", game_id)
                    break

            home_win_prob: Optional[float] = None
            if away_win_prob is not None:
                home_win_prob = round(100.0 - away_win_prob, 3)

            ordered_game = {
                'sport': game['sport'],
                'league': game['league'],
                'date': game['date'],
                'espn_id': game['espn_id'],
                'away_team': game['away_team'],
                'away_team_win_percentage': away_win_prob,
                'home_team': game['home_team'],
                'home_team_win_percentage': home_win_prob,
                'name': game['name'],
                'short_name': game['short_name'],
                'status_name': game['status_name'],
                'is_completed': game['is_completed']
            }
            ordered_enriched_games.append(ordered_game)

        return ordered_enriched_games

    def save_to_db(self, enriched_games: List[Dict[str, Any]]) -> None:
        """
        Saves new games to db or updates existing games to db by espn_id.
        :param enriched_games:
        :return:
        """
        if not enriched_games:
            logger.info("No games provided to save.")
            return

        db = SessionLocal()

        try:
            for game_data in enriched_games:
                logger.info("Saving game %s. Is completed? %s", game_data['name'], game_data['is_completed'])
                # check if already exists
                existing_game = db.query(Match).filter(Match.espn_id == game_data.get('espn_id')).first()

                if existing_game:
                    # update with new data
                    for key, value in game_data.items():
                        setattr(existing_game, key, value)
                else:
                    # create new data
                    new_game = Match(**game_data)
                    db.add(new_game)

            db.commit()
            logger.info("Successfully saved %d games.", len(enriched_games))
        except Exception as e:
            db.rollback()
            logger.error("Failed to save to db: %s", e)
        finally:
            db.close()

    def cleanup_finished_games(self) -> None:
        """
        Deletes any games that have STATUS_COMPLETED flag set to True.
        :return:
        """
        db = SessionLocal()
        try:
            deleted_count = db.query(Match).filter( (Match.is_completed == True) |(Match.status_name == "STATUS_POSTPONED")).delete()
            db.commit()
            if deleted_count > 0:
                logger.info("Successfully deleted %d games.", deleted_count)
            else:
                logger.info("no deleted games.")

        except Exception as e:
            db.rollback()
            logger.error("Failed to delete games: %s", e)
        finally:
            db.close()

    def read_active_games(self) -> None:
        """
        Reads and logs the upcoming/active games.
        :return:
        """
        db = SessionLocal()
        try:
            stored_games = db.query(Match).order_by(Match.date).all()
            logger.info("Currently Stored Upcoming Games")
            for game in stored_games:
                logger.info("%s vs %s on %s | Win Probs: Away(%.1f%%) Home(%.1f%%)",
                    game.away_team, game.home_team, game.date,
                    game.away_team_win_percentage or 0.0,
                    game.home_team_win_percentage or 0.0)
        except Exception as e:
            logger.error("Failed to read games: %s", e)
        finally:
            db.close()



if __name__ == '__main__':
    init_db()

    target_league = 'mlb'
    league_config = ESPN_CONFIG.get(target_league)

    if not league_config:
        logger.error("Configuration for league '%s' not found.", target_league)
    else:
        nba_ingest = ESPNScheduleIngest(
            sport=league_config['sport'],
            league=league_config['league']
        )

        # Fetch
        base_schedule = nba_ingest.ingest_schedule()

        # Enrich
        final_enriched_games = nba_ingest.enrich_probabilities(base_schedule)

        # Write / Update the database
        nba_ingest.save_to_db(final_enriched_games)

        # Read to verify
        nba_ingest.read_active_games()

        # Clean up any completed games
        nba_ingest.cleanup_finished_games()