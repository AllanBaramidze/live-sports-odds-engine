from datetime import datetime, timezone


def clean_event_data(data, sport, league):
    events = data.get("events", [])  # Gets Games Info
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    mapped_games = []
    for event in events:
        # Only include games scheduled for today
        event_date = event["date"][:10]
        if event_date != today:
            continue

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
            "game_status": game_status
        })
    return mapped_games
