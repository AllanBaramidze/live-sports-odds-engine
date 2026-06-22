import logging
from typing import Any, Optional
from polymarket import Market


logger = logging.getLogger(__name__)


def get_match_market(client: Any, poly_slug: str, search_query: Optional[str] = None) -> list[dict[str, Any]]:
    """
    Returns the market by slug. If it's a grouped event (like Soccer),
    uses search_query to recover the event ID and returns all associated markets.
    """
    try:
        market = client.get_market(slug=poly_slug)
        return [parse_market_to_dict(market)]

    except Exception as e: # either Event or Not an Active Market / Event
        if not search_query:
            raise ValueError(f"Lookup failed for '{poly_slug}'. No search_query provided.") from e

        recovered_event_id = find_sports_error_catcher(client, search_query, poly_slug)

        if not recovered_event_id:
            raise ValueError(f"Fallback search failed for '{search_query}'.")

        event = client.get_event(id=recovered_event_id)

        # Cleaner list comprehension
        return [parse_market_to_dict(m) for m in event.markets] if event.markets else []


def get_teams(client: Any, league: str) -> dict[str, dict[str, Any]]:
    """
    Returns the teams by league, helps with creating the poly slugs.
    """
    teams_paginator = client.list_teams(league=league, page_size=10)

    all_teams = [team for page in teams_paginator for team in page.items]

    return {
        team.name: {
            "id": team.id,
            "name": team.name,
            "abbreviation": team.abbreviation,
        }
        for team in all_teams
    }


def find_sports_error_catcher(client: Any, search_query: str, target_slug: str) -> Optional[str]:
    """
    Searches Polymarket for a query and returns the Event ID if the slug matches.
    """
    search_results = client.search(q=search_query, page_size=5)

    for page in search_results:
        for item in page.items:
            for event in item.events:
                if event.slug == target_slug:
                    return event.id

    # Replaced print with logger
    logger.warning(f"No match found for slug: {target_slug}")
    return None



def parse_market_to_dict(market: Market) -> dict[str, Any]:
    start_time = None
    if market.sports and market.sports.game_start_time:
        start_time = market.sports.game_start_time.isoformat()

    return {
        "id": market.id,
        "slug": market.slug,
        "condition_id": market.condition_id,
        "question": market.question,
        "state": {
            "is_active": market.state.active,
            "is_closed": market.state.closed,
            "is_accepting_orders": market.state.accepting_orders
        },
        "game_start_time": start_time,
        "outcomes": {
            # Safely labeled as Yes/No outcomes for universal sport compatibility
            "yes_outcome": {
                "label": market.outcomes.yes.label,
                "token_id": market.outcomes.yes.token_id,
                "current_price": float(market.outcomes.yes.price) if market.outcomes.yes.price else 0.0
            },
            "no_outcome": {
                "label": market.outcomes.no.label,
                "token_id": market.outcomes.no.token_id,
                "current_price": float(market.outcomes.no.price) if market.outcomes.no.price else 0.0
            }
        },
        "prices": {
            "best_bid": float(market.prices.best_bid) if market.prices.best_bid else 0.0,
            "best_ask": float(market.prices.best_ask) if market.prices.best_ask else 0.0,
            "last_trade_price": float(market.prices.last_trade_price) if market.prices.last_trade_price else 0.0,
            "spread": float(market.prices.spread) if market.prices.spread else 0.0
        },
        "metrics": {
            "volume": float(market.metrics.volume) if market.metrics.volume else 0.0,
            "liquidity": float(market.metrics.liquidity) if market.metrics.liquidity else 0.0
        }
    }

def main():
    from polymarket import PublicClient

    with PublicClient() as client:
        # Pass the active client into your utility functions
        market_info = get_match_market(
            client=client,
            poly_slug="fifwc-jor-alg-2026-06-22",
            search_query="Jordan vs Algeria"
        )

        for market in market_info:
            print(f"Question: {market['question']}")
            print(f"Yes Price: {market['outcomes']['yes_outcome']['current_price']}")
            print(f"No Price:  {market['outcomes']['no_outcome']['current_price']}\n")


if __name__ == "__main__":
    main()


