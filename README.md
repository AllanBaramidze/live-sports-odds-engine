# Live Sports Odds Engine

## Overview
The Live Sports Odds Engine is an automated ETL pipeline and analysis tool designed to identify betting value by comparing market prices against quantitative sports analytics. 

By pulling live prediction data and pregame metrics from ESPN and correlating them with live market odds and orderbook depth from Polymarket, this engine calculates implied probabilities to determine if the current market "price is right."

## Tech Stack
* **Language:** Python
* **Database:** PostgreSQL (managed via SQLAlchemy)
* **Caching/Live Data:** Valkey (for high-frequency live odds)
* **Infrastructure:** Docker, standard cron jobs (deployed via VPS/Droplet)

## Data Sources
1. **ESPN Analytics:** Ingests pregame predictions, live win probabilities, projected spreads, and expected team totals. (Utilizing the [Public ESPN API](https://github.com/pseudo-r/Public-ESPN-API)).
2. **Polymarket:** Tracks live betting odds, orderbook depth, and derived on-pull metrics by matching events using custom-generated URL slugs (e.g., `nba-nyk-sas-2026-06-13`).

## Core Architecture

### 1. Ingestion Pipeline (`espn_schedule.py`)
Handles the daily retrieval of sports schedules, parsing game details, and fetching pregame probabilities (Implied Win %, Spread, Expected Points). It normalizes team short names to reliably map to Polymarket slugs.

### 2. Database Schema
A relational PostgreSQL database that stores the foundational data needed for historical backtesting and live comparisons:
* `Sports` & `Leagues`
* `Matches` (Unique ESPN IDs)
* `Teams` & `ShortNames` (For cross-platform mapping)
* `Pregame Predictions` 

### 3. Live Price Matching (In Development)
A high-speed layer utilizing Valkey to hold rapidly changing state data:
* Live Polymarket odds vs. Live ESPN Win Probability
* Orderbook depth analysis for market liquidity and resistance

## Deployment
This project is containerized using `docker-compose` (running Postgres and Valkey) and is designed to be hosted on a cloud server (e.g., DigitalOcean Droplet). Automated ingestion is handled via standard system cron jobs triggering the Python ETL scripts.

## Roadmap / To-Do
- [ ] Finalize live Polymarket data ingestion and orderbook parsing.
- [ ] Implement Valkey for high-speed live odds caching.
- [ ] Build the comparative logic engine (Price vs. Probability).
- [ ] Set up production Droplet with automated cron scheduling.
