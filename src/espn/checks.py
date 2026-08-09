import httpx
import asyncio

sport = 'baseball'
league = 'mlb'
resource = 'scoreboard'


r = httpx.get(f'https://site.api.espn.com/apis/site/v2/sports/{sport}/{league}/{resource}')
data = r.json()


