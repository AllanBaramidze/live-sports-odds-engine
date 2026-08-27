import json
from datetime import datetime, timezone
import httpx
import asyncio

sport = 'baseball'
league = 'mlb'
resource = 'scoreboard'


r = httpx.get(f'https://site.api.espn.com/apis/site/v2/sports/{sport}/{league}/{resource}')
data = r.json()

# Test Print of the JSON
# print(json.dumps(data, indent=2))

day = data["day"]["date"] # Gets the Day of the Events

print(day) # What Day is being processed

games = len(data["events"]) # Gets the Amount of Games

print(games)

events = data.get("events",[])

for event in events:
    if event["date"].startswith(day):
        print(event)


