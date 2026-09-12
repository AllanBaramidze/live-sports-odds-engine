from datetime import datetime, timezone
from zoneinfo import ZoneInfo
from traceback import print_tb

import httpx

# Polymarket uses ET for all US sports slugs
POLYMARKET_TZ = ZoneInfo("America/New_York")


def to_slug_date(utc_date_str: str) -> str:
    """Convert an ESPN UTC timestamp to the local game date used in Polymarket slugs."""
    dt = datetime.fromisoformat(utc_date_str.replace("Z", "+00:00"))
    local_dt = dt.astimezone(POLYMARKET_TZ)
    return local_dt.strftime("%Y-%m-%d")


def clean_event_data(data, sport, league):
    events = data.get("events", [])  # Gets Games Info
    mapped_games = []
    for event in events:
        status_type = event["status"]["type"]

        # Skip games that are already final/completed
        if status_type.get("state") == "post" or status_type.get("completed") is True:
            continue

        espn_id = event["id"]
        date = event["date"]
        matchup = event["name"]
        game_status = status_type["description"]

        home_team = ""
        away_team = ""

        # competitions is a list, each with competitors inside
        competitions = event.get("competitions", [])
        if competitions:
            competitors = competitions[0].get("competitors", [])
            for team in competitors:
                if team["homeAway"] == "home":
                    home_team = team["team"]["displayName"]
                elif team["homeAway"] == "away":
                    away_team = team["team"]["displayName"]

        mapped_games.append({
            "espn_id": espn_id,
            "date": date,
            "league": league.value,
            "sport": sport.value,
            "matchup": matchup,
            "home_team": home_team,
            "away_team": away_team,
            "game_status": game_status,
            "poly_slug": poly_slug(league.value, away_team, home_team, to_slug_date(date))
        })
    return mapped_games


def poly_slug(league: str, away_team: str, home_team: str, slug_date: str): #
    """
    Takes the Matchup, finds the event slug and returns it.
    Polymarket format: {league}-{away_abbr}-{home_abbr}-{YYYY-MM-DD}
    'matchup': 'St. Louis Cardinals at Los Angeles Dodgers'
    :return:
    """

    url_home = f"https://gamma-api.polymarket.com/teams?league={league}&name={home_team}" # GET Search
    url_away = f"https://gamma-api.polymarket.com/teams?league={league}&name={away_team}"


    resp_home = httpx.get(url_home) # GET Request
    resp_away = httpx.get(url_away)

    home_abbr = resp_home.json()[0]["abbreviation"]
    away_abbr = resp_away.json()[0]["abbreviation"]

    return f"{league}-{away_abbr}-{home_abbr}-{slug_date}"



if __name__ == "__main__":
    poly_slug("mlb", "St. Louis Cardinals", "Los Angeles Dodgers", datetime.now(timezone.utc))