import os
import httpx
import dotenv
import pprint
from datetime import datetime
from dotenv import load_dotenv
from pathlib import Path
from espn.espn_utils import clean_event_data
from enum import StrEnum

# Load env vars for DB connection
load_dotenv(Path(__file__).resolve().parent.parent.parent / ".env.local")


class Sport(StrEnum):
    BASEBALL = 'baseball'
    BASKETBALL = 'basketball'
    FOOTBALL = 'football'
    SOCCER = 'soccer'
    HOCKEY = 'hockey'

class League(StrEnum):
    NFL = 'nfl'
    MLB = 'mlb'
    NBA = 'nba'
    NHL = 'nhl'
    MLS = 'mls'

LEAGUE_SPORT_DICT = {
    Sport.BASEBALL: League.MLB,
    Sport.BASKETBALL: League.NBA,
    Sport.FOOTBALL: League.NFL,
    Sport.SOCCER: League.MLS,
}

class ESPNClient:
    def __init__(self, sport: Sport, league: League):
        self.sport = sport
        self.league = league
        self.URLschedule = f"https://site.api.espn.com/apis/site/v2/sports/{sport}/{league}/scoreboard"


    def test_connection(self) -> bool: # Test Connection to ESPN API
        try:
            response = httpx.get(self.URLschedule, timeout=10)
            success = response.status_code == 200
        except httpx.RequestException as e:
            print(f"Connection Failed: {e}")
            return False

        print(f"Connection {'Successful' if success else 'Failed'}: {response.status_code}")
        return success

    # Clean Old Event Data
    def clean_data(self):
        pass

    # Returns a List of Events for the Day, based on Sport & League
    def get_events(self) -> list[dict]:
        try:
            r = httpx.get(self.URLschedule, timeout=10)
            r.raise_for_status()
        except httpx.HTTPStatusError as e:
            print(f"HTTP error fetching events: {e}")
            return []
        except httpx.RequestError as e:
            print(f"Request error fetching events: {e}")
            return []

        data = r.json()
        return clean_event_data(data, self.sport, self.league)

    # Ingest Events into matches Database
    def ingest_events(self):
        pass

if __name__ == "__main__":
    client = ESPNClient(Sport.BASEBALL, League.MLB)
    events = client.get_events()
    pprint.pprint(events)