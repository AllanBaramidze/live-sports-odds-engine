import requests
from datetime import datetime
from typing import List, Dict, Optional

ESPN_CONSTS = {
    'nba': {
        'sport': 'basketball',
        'league': 'nba',
    },
    'mlb': {
        'sport': 'baseball',
        'league': 'mlb',
    }
}

class ESPNSchedule:
    def __init__(self, league_key):
        config = ESPN_CONSTS.get(league_key)
        self.sport = config['sport']
        self.league = config['league']
        self.base_url = "http://localhost:8000/api/v1"

    def ingest(self, date_str = None):
        """
        Docker Service to fetch the latest scoreboard.
        Queries the local docker DB for the clean result.
        :param date_str:
        :return:
        """
        if not date_str:
            date_str = datetime.today().strftime('%Y-%m-%d')

        # pull from ESPN
        ingest_url = f"{self.base_url}/ingest/scoreboard/"
        requests.post(ingest_url, json={"sport": self.sport, "league": self.league})

        # cleaned data from local DB
        query_url = f"{self.base_url}/events/"
        response = requests.get(query_url, params={"league": self.league, "date": date_str})
        data = response.json()

        # local API wraps results in 'results' array
        games_list = data.get("results", [])

        cleaned_games = []
        for game in games_list:
            game_data ={
                'game_id': game.get('id'),
                'espn_id': game.get('espn_id'),
                'date': game.get('date'),
                'name': game.get('name'),
                'shortName': game.get('shortName'),
                'status': game.get('status'),
            }
            cleaned_games.append(game_data)
            print(game_data)
        return cleaned_games

    def ingest_pregame(self, game_id):
        """
        Queries local docker DB for specific event's details
        :param game_id:
        :return:
        """
        # local detail endpoint
        detail_url = f"{self.base_url}/events/{game_id}/"

        try:
            response = requests.get(detail_url)
            if response.status_code == 200:
                game_detail = response.json()

                print(f"Retrieved details for db id: {game_id}")
                return game_detail
            else:
                print(f"Failed to retrieve details for db id: {game_id}")
                return None

        except requests.exceptions.RequestException as e:
            print(f"Failed: {e} ")


if __name__ == '__main__':
    # You must instantiate the class before calling its methods
    mlb_client = ESPNSchedule('mlb')
    print("--- Fetching MLB ---")
    mlb_games = mlb_client.ingest()

    nba_client = ESPNSchedule('nba')
    print("\n--- Fetching NBA ---")
    nba_games = nba_client.ingest()

    # Example of chaining the methods: getting details for the first NBA game found
    if nba_games:
        first_game_id = nba_games[0]['game_id']
        print(f"\n--- Fetching Pregame Data for Game ID {first_game_id} ---")
        nba_client.ingest_pregame(first_game_id)