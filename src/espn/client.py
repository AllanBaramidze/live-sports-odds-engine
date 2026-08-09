from enum import StrEnum


class Sport(StrEnum):
    BASEBALL = 'baseball',
    BASKETBALL = 'basketball',
    FOOTBALL = 'football',
    SOCCER = 'soccer',

class League(StrEnum):
    NFL = 'nfl',
    MLB = 'mlb',
    MLS = 'mls',
    NBA = 'nba',
    ESP = "lal"

LEAGUE_SPORT_DICT = {
    Sport.BASEBALL: League.MLB,
    Sport.BASKETBALL: League.NBA,
    Sport.FOOTBALL: League.NFL,
    Sport.SOCCER: League.MLS,
}

