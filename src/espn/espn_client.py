import os
import httpx
import pprint
from datetime import datetime, timedelta
from espn.espn_utils import clean_event_data
from enum import StrEnum



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

    def get_events(self) -> list[dict]:

        # Date Range Handler Here for the URL Endpoint Scheduler to Get T(0) and T(0) + 1
        today = datetime.now().astimezone().date()
        tomorrow = today + timedelta(days=1)

        start = today.strftime("%Y%m%d")
        end = tomorrow.strftime("%Y%m%d")
        params = {"dates": f"{start}-{end}", "limit": 500}

        # Error Handling for URL response
        try:
            r = httpx.get(self.URLschedule, params=params, timeout=10)
            r.raise_for_status()
        except httpx.HTTPStatusError as e:
            print(f"HTTP error fetching events: {e}")
            return []
        except httpx.RequestError as e:
            print(f"Request error fetching events: {e}")
            return []

        data = r.json() # pass data into clean_event_data
        return clean_event_data(data, self.sport, self.league)


if __name__ == "__main__":
    client = ESPNClient(Sport.BASEBALL, League.MLB)
    events = client.get_events()
    pprint.pprint(events)