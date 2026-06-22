import logging
from datetime import datetime, timedelta

from django.conf import settings

if not settings.configured:
    settings.configure(
        DEBUG=True,
        SECRET_KEY="temporary_key_for_ingest_script",
        ESPN_CLIENT={}  # Bypasses the config lookups smoothly
    )

from clients.espn_client import get_espn_client

# logging
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


def test_get_scoreboard(client, sport="baseball", league="mlb", date=None):
    """
    Tests fetching the daily scoreboard.

    Returns:
        list: A list of event dictionaries to be used in subsequent tests, or empty list if failed.
    """
    logger.info(f" Testing Scoreboard ({sport}/{league} | Date: {date or 'Today'}) ")
    sb_response = client.get_scoreboard(sport=sport, league=league, date=date)

    if sb_response.is_success:
        events = sb_response.data.get("events", [])
        logger.info(f"Found {len(events)} games.")
        for event in events:
            logger.info(f"  -> Game: {event.get('shortName')} (ID: {event.get('id')})")
        return events
    else:
        logger.error(f"Scoreboard fetch failed: {sb_response.status_code}")
        return []


def test_yesterdays_completed_games(client, sport="baseball", league="mlb"):
    """
    Fetches yesterday's schedule and checks if the games are flagged as completed.
    """
    yesterday_str = (datetime.now() - timedelta(days=1)).strftime('%Y%m%d')
    logger.info(f"Testing Yesterday's Games Completion Status ({yesterday_str}) ")

    sb_response = client.get_scoreboard(sport=sport, league=league, date=yesterday_str)

    if sb_response.is_success:
        events = sb_response.data.get("events", [])
        logger.info(f"Found {len(events)} games from yesterday.")

        for event in events:
            event_id = event.get("id")
            short_name = event.get("shortName")

            # Safely navigate the JSON tree to find the completion status
            status_data = event.get('status', {})
            status_type = status_data.get('type', {})
            is_completed = status_type.get('completed', False)
            status_name = status_type.get('name', 'UNKNOWN_STATUS')

            logger.info(f"  -> {short_name} (ID: {event_id}) | Completed: {is_completed} | Status: {status_name}")
    else:
        logger.error(f"Failed to fetch yesterday's games: {sb_response.status_code}")


def test_get_predictor(client, sport="baseball", league="mlb", event_id=None):
    """
    Tests fetching the pregame predictor probabilities for a specific event.
    """
    if not event_id:
        logger.warning("Skipping Predictor Test: No event ID provided.")
        return

    logger.info(f" Testing Game Predictor (Event ID: {event_id}) ")
    sb_prediction = client.get_game_predictor(sport=sport, league=league, event_id=event_id, competition_id=event_id)

    if sb_prediction.is_success:
        logger.info("Predictor Data grabbed successfully.")
        # logger.debug(sb_prediction.data) # Uncomment to see full raw payload
    else:
        logger.error(f"Predictor fetch failed: {sb_prediction.status_code}")


def test_get_situation(client, sport="basketball", league="nba", event_id=None):
    """
    Tests fetching the play-by-play situation for a specific event.
    """
    if not event_id:
        logger.warning("Skipping Situation Test: No event ID provided.")
        return

    logger.info(f" Testing Game Situation (Event ID: {event_id}) ")
    play_response = client.get_game_situation(sport=sport, league=league, event_id=event_id)

    if play_response.is_success:
        logger.info("Situation Data grabbed successfully.")
    else:
        logger.error(f"Situation fetch failed: {play_response.status_code}")


def main():
    client = get_espn_client()


    # Test Yesterday's Completed Games
    test_yesterdays_completed_games(client, sport="baseball", league="mlb")

    # Test Today's Scoreboard
    today_events = test_get_scoreboard(client, sport="baseball", league="mlb", date=None)

    # Extract a sample event ID to use for the next tests (if any events exist today)
    sample_mlb_event_id = today_events[0].get("id") if today_events else None

    # Test MLB Predictor
    if sample_mlb_event_id:
        test_get_predictor(client, sport="baseball", league="mlb", event_id=sample_mlb_event_id)

    # Test MLB Situation
    sample_mlb_event_id = "401815833"  # TOR vs CHC
    # test_get_situation(client, sport="basketball", league="nba", event_id=sample_nba_event_id)


if __name__ == "__main__":
    main()