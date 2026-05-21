import requests
from glom import glom


HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}


def DiscoverySchedule():
    """
    Discovery function of the schedule API.
    """
    url = 'https://site.api.espn.com/apis/site/v2/sports/basketball/nba/scoreboard'
    response = requests.get(url, headers=HEADERS)  # Added headers
    data = response.json()
    for game in data['events']:
        print(game)
    games = ("events", [{'id': 'id', 'date': 'date', 'name': 'name', 'shortName': 'shortName', 'seasonPhase': 'season.slug'}])
    games_data = glom(data, games)

    return games_data


def DiscoveryWinProbability(games_data):
    if not games_data:
        print("No games scheduled for today.")
        return

    gameid = games_data[0]['id']


    url = f"https://site.api.espn.com/apis/site/v2/sports/basketball/nba/summary?event={gameid}"

    indetail = requests.get(url, headers=HEADERS)

    # Safety guard: Check if the request actually succeeded before parsing JSON
    if indetail.status_code != 200:
        print(f"ESPN rejected the request. Status code: {indetail.status_code}")
        return

    data = indetail.json()
    print("Successfully fetched game details!")

    # Print out the available top-level keys so you see what data you can now target
    print(data.keys())


if __name__ == '__main__':
    schedule = DiscoverySchedule()

    DiscoveryWinProbability(schedule)