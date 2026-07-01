import logging
from dataclasses import dataclass, asdict
from typing import Any, Dict, List, Optional
from datetime import datetime, timedelta

from polymarket import PublicClient
from django.conf import settings

if not settings.configured:
    settings.configure(DEBUG=True)

from clients.espn_client import get_espn_client
from src.utils.polymarket_utils import get_teams
from src.db.database import SessionLocal, Match, init_db

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

ESPN_CONFIG: Dict[str, Dict[str, str]] = {
    'nba': {'sport': 'basketball',
            'league': 'nba'},
    'mlb': {'sport': 'baseball',
            'league': 'mlb'},
}


@dataclass
class OrderedGame:
    """Represents a single game with win probabilities."""
    sport: str
    league: str
    espn_id: str
    date: str
    home_team: str
    away_team: str
    name: str
    short_name: str
    poly_slug: str
    status_name: str
    is_completed: bool
    home_team_win_percentage: Optional[float] = None
    away_team_win_percentage: Optional[float] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dict for database operations."""
        return asdict(self)


class ESPNScheduleIngest:
    """
    Handles ingestion and enrichment of daily sports schedules via ESPN API.
    """

    def __init__(self, sport: str, league: str) -> None:
        self.sport = sport
        self.league = league
        self.client = get_espn_client()

    def _parse_event(self, event: Dict[str, Any]) -> OrderedGame:
        """
        Parse a single ESPN event into an OrderedGame.

        Args:
            event: Raw event dict from the ESPN API.

        Returns:
            OrderedGame with no probabilities attached yet.
        """
        competitions = event.get("competitions", [])
        competition_data = competitions[0] if competitions else {}
        competitors_data = competition_data.get("competitors", [])

        home_team = next((t for t in competitors_data if t.get('homeAway') == 'home'), {})
        away_team = next((t for t in competitors_data if t.get('homeAway') == 'away'), {})

        home_team_name = home_team.get('team', {}).get('displayName', 'Unknown Home Team')
        away_team_name = away_team.get('team', {}).get('displayName', 'Unknown Away Team')

        status_data = event.get('status', {})
        status_type = status_data.get('type', {})

        # Build the Polymarket slug
        home_abbr = self._team_lookup.get(home_team_name, {}).get('abbreviation', 'UNK')
        away_abbr = self._team_lookup.get(away_team_name, {}).get('abbreviation', 'UNK')
        date_string = event.get('date', '')
        formatted_date = date_string[:10] if date_string else 'Unknown-Date'
        poly_slug = f"{self.league}-{away_abbr}-{home_abbr}-{formatted_date}"

        return OrderedGame(
            sport=self.sport,
            league=self.league,
            espn_id=event.get('id', ''),
            date=date_string,
            home_team=home_team_name,
            away_team=away_team_name,
            name=event.get('name', ''),
            short_name=event.get('shortName', ''),
            poly_slug=poly_slug,
            status_name=status_type.get('name', ''),
            is_completed=status_type.get('completed', False),
        )

    def ingest_schedule(self) -> List[OrderedGame]:
        """
        Fetch today's and tomorrow's schedule from ESPN.

        Returns:
            List of OrderedGame without probabilities.
        """
        # Fetch team mappings once and store for _parse_event
        logger.info("Fetching team mappings for %s...", self.league)
        with PublicClient() as poly_client:
            self._team_lookup = get_teams(client=poly_client, league=self.league)

        games: List[OrderedGame] = []
        today_str = datetime.now().strftime('%Y%m%d')
        tomorrow_str = (datetime.now() + timedelta(days=1)).strftime('%Y%m%d')

        for target_date in [today_str, tomorrow_str]:
            logger.info("Fetching schedule for %s - %s on %s...", self.sport, self.league, target_date)
            sb_response = self.client.get_scoreboard(
                sport=self.sport, league=self.league, date=target_date, limit=100
            )

            if not sb_response or not hasattr(sb_response, 'data'):
                logger.warning("Invalid or empty response for date %s", target_date)
                continue

            events = sb_response.data.get("events", [])
            for event in events:
                games.append(self._parse_event(event))

        logger.info("Successfully ingested %d total games.", len(games))
        return games

    def _fetch_away_win_probability(self, game: OrderedGame) -> Optional[float]:
        """
        Call ESPN predictor API for a single game.

        Returns:
            Away team win probability as a float, or None on failure.
        """
        prediction = self.client.get_game_predictor(
            sport=self.sport,
            league=self.league,
            event_id=game.espn_id,
            competition_id=game.espn_id,
        )

        pred_data = prediction.data if hasattr(prediction, 'data') else prediction
        statistics = pred_data.get("awayTeam", {}).get("statistics", [])

        for stat in statistics:
            if stat.get('name') == 'gameProjection':
                try:
                    return float(stat.get('value'))
                except (ValueError, TypeError):
                    logger.error("Failed to parse gameProjection for game %s", game.espn_id)
                    return None

        logger.warning("No gameProjection found for game %s", game.espn_id)
        return None

    def enrich_probabilities(self, games: List[OrderedGame]) -> List[OrderedGame]:
        """
        Enrich games with win probabilities. Skips completed games.

        Args:
            games: List of OrderedGame from ingest_schedule.

        Returns:
            Same list with probabilities populated for active/scheduled games.
        """
        if not games:
            logger.info("No games provided to enrich.")
            return []

        logger.info("Enriching %d games with win probabilities...", len(games))

        for game in games:
            if not game.espn_id:
                logger.warning("Game missing espn_id, skipping: %s", game.name)
                continue

            if game.is_completed:
                logger.info("Skipping enrichment for completed game %s", game.espn_id)
                continue

            away_prob = self._fetch_away_win_probability(game)
            if away_prob is not None:
                game.away_team_win_percentage = away_prob
                game.home_team_win_percentage = round(100.0 - away_prob, 3)

        return games

    def save_to_db(self, games: List[OrderedGame]) -> None:
        """Upsert games into the database."""
        if not games:
            logger.info("No games provided to save.")
            return

        with SessionLocal() as db:
            try:
                for game in games:
                    game_dict = game.to_dict()
                    existing = db.query(Match).filter(
                        Match.espn_id == game.espn_id
                    ).first()

                    if existing:
                        for key, value in game_dict.items():
                            setattr(existing, key, value)
                    else:
                        db.add(Match(**game_dict)) # dict unpacking

                db.commit()
                logger.info("Successfully saved %d games.", len(games))
            except Exception as e:
                db.rollback()
                logger.error("Failed to save to db: %s", e)

    def cleanup_finished_games(self) -> None:
        """Delete completed or postponed games older than 1 day."""
        db = SessionLocal()
        try:
            cutoff_date = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
            deleted_count = db.query(Match).filter(
                (Match.is_completed == True) | (Match.status_name == "STATUS_POSTPONED"),
                Match.date < cutoff_date,
            ).delete()

            db.commit()
            logger.info("Deleted %d old completed games.", deleted_count)
        except Exception as e:
            db.rollback()
            logger.error("Failed to delete games: %s", e)
        finally:
            db.close()

    def read_active_games(self) -> None:
        """Log all currently stored games."""
        db = SessionLocal()
        try:
            stored_games = db.query(Match).order_by(Match.date).all()
            logger.info("Currently stored games:")
            for g in stored_games:
                logger.info(
                    "%s vs %s on %s | Away(%.1f%%) Home(%.1f%%)",
                    g.away_team,
                    g.home_team,
                    g.date,
                    g.away_team_win_percentage or 0.0,
                    g.home_team_win_percentage or 0.0,
                )
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
        ingest = ESPNScheduleIngest(
            sport=league_config['sport'],
            league=league_config['league'],
        )

        schedule = ingest.ingest_schedule()
        enriched = ingest.enrich_probabilities(schedule)
        ingest.save_to_db(enriched)
        ingest.read_active_games()
        ingest.cleanup_finished_games()