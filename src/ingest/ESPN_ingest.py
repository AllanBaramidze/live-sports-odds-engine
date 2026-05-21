from logging import config

import requests
from glom import glom


HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

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

class ESPNIngest:
    def __init__(self, league_key):
        config = ESPN_CONSTS.get(league_key)
        self.sport = config['sport']
        self.league = config['league']


    def ingest(self, resource="scoreboard"):
        """
        ingests data from ESPNs scoreboards for the given league, getting game_id, data, name, shortName, seasonPhase
        :param resource:
        :return:
        """
        URL = f'https://site.api.espn.com/apis/site/v2/sports/{self.sport}/{self.league}/{resource}'  # Site API v2 (Scores, Teams, Standings)
        response = requests.get(URL, headers=HEADERS)
        data = response.json()
        games = ("events",[{'id': 'id', 'date': 'date', 'name': 'name', 'shortName': 'shortName', 'seasonPhase': 'season.slug'}])
        games_data = glom(data, games)
        for game in games_data:
            print(game)
        return games_data

    def ingest_pregame(self):
        # events/{id}/competitions/{id}/predictor , ESPN game predictor
        # events/{id}/competitions/{id}/probabilities, Win probabilities
        # also need to get gameID from ingest
        resource = {
            'pregame':f'events/{id}/competitions/{id}/predictor',
            'live_game': f'events/{id}/competitions/{id}/probabilities'
        }
        URL = f'https: // sports.core.api.espn.com / v2 / sports / {self.sport} / leagues / {self.league} / {resource}'
        data = requests.get(URL, headers=HEADERS)



if __name__ == '__main__':
    ingest('mlb') # Works
    ingest('nba') # Works
