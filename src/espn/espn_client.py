import os
import httpx
import pprint
from datetime import datetime, timedelta
from espn.espn_utils import clean_event_data
from enum import StrEnum
from db.database import get_session
from db.repository import MatchRepository


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
    Sport.HOCKEY: League.NHL,
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
        """
        Fetches events for the current date and the following day from the given URL endpoint.

        This method builds a date range covering today and tomorrow and sends a GET request
        to the predefined endpoint with these dates as parameters. The events data is then
        cleaned and processed before being returned.

        :raises httpx.HTTPStatusError: If the HTTP response status is not successful.
        :raises httpx.RequestError: If there are connection issues or other request-related errors.
        :param params: A dictionary containing query parameters for the HTTP GET request.
                        The 'dates' parameter specifies the range in 'YYYYMMDD' format for
                        today and tomorrow.
                        The 'limit' parameter restricts the number of events to 500.
                        This parameter is built programmatically and not user-supplied.

        :return: A list of dictionaries containing cleaned event data. Each dictionary
                 represents an event associated with the specified sport and league.
        :rtype: list[dict]
        """

        # Date Range Handler Here for the URL Endpoint Scheduler to Get T(0) and T(0) + 1
        today = datetime.now().astimezone().date()
        yesterday = today - timedelta(days=1)
        tomorrow = today + timedelta(days=1)
        # Games that have been previously ingested are being missed because they are technically outside the window

        start = yesterday.strftime("%Y%m%d")
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

    def insert_matches(self) -> int:
        """
        Fetches events from ESPN and bulk-upserts them into the database.
        :return: Number of matches inserted/updated
        """
        events = self.get_events()
        if not events:
            print("No events to insert.")
            return 0

        with get_session() as session:
            repo = MatchRepository(session)
            repo.upsert_match(events)

        # print(f"Upserted {len(events)} matches.")
        return len(events)

if __name__ == "__main__":
    client = ESPNClient(Sport.BASEBALL, League.MLB)
    inserted = client.insert_matches()
    pprint.pprint(f"Inserted/updated {inserted} matches.")