"""
TODO:
    Create Test api fetches to see what information needs to called like full schedules, rosters, win probabilities, etc.
"""

# Fake a bare-minimum Django configuration so the client doesn't crash on import
from django.conf import settings
if not settings.configured:
    settings.configure(
        DEBUG=True,
        SECRET_KEY="temporary_key_for_ingest_script",
        ESPN_CLIENT={} # Bypasses the config lookups smoothly
    )

#  Now import your client from the espn_service folder
from clients.espn_client import get_espn_client

def main():
    # Get client instance
    client = get_espn_client()

    print('Scoreboard')
    # call get_scoreboard() NBA ex. for specific date
    sb_response = client.get_scoreboard(sport="basketball", league="nba", date="20260613")

    if sb_response.is_success:
        # raw python dict from espns JSON
        events = sb_response.data.get("events", [])
        print(f"Found {len(events)} games today.")

        # loop through
        for event in events:
            event_id = event.get("id") # ESPN payload uses 'id'
            short_name = event.get("shortName")
            print(f"\nGame: {short_name} (ID: {event_id})")

            # print('Events')
            # # call get_event()
            # sb_event = client.get_event(sport="basketball", league="nba", event_id=event_id)
            # print(sb_event)

            print('pregame predictor')
            sb_prediction = client.get_game_predictor(sport="basketball", league="nba", event_id=event_id, competition_id=event_id)
            print(sb_prediction)




            print("  -> Fetching Play-by-Play situation...")
            play_response = client.get_game_situation(sport="basketball", league="nba", event_id=event_id)
            if play_response.is_success:
                print(f"  -> Situation Data grabbed successfully.")
            else:
                print(f"  -> Situation fetch failed: {play_response.status_code}")
    else:
        print(f"Fetch failed with status code: {sb_response.status_code}")



if __name__ == "__main__":
    main()