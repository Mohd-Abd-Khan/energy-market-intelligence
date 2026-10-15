# Energy Market Intelligence

<div align="center">

[![Python](https://img.shields.io/badge/Python-3.11%20%7C%203.12%20%7C%203.13-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![Dash](https://img.shields.io/badge/Plotly_Dash-Dark_SaaS-00f0ff?style=for-the-badge&logo=plotly&logoColor=white)](https://dash.plotly.com/)
[![EIA v2](https://img.shields.io/badge/EIA_v2-REST_API-10b981?style=for-the-badge&logo=fastapi&logoColor=white)](https://www.eia.gov/opendata/)
[![SQLite](https://img.shields.io/badge/SQLite-WAL_Repository-003B57?style=for-the-badge&logo=sqlite&logoColor=white)](https://www.sqlite.org/)
[![License](https://img.shields.io/badge/License-MIT-purple?style=for-the-badge)](LICENSE)

**An institutional-grade quantitative energy market analytics platform that ingests real-time commodity spot prices from the U.S. EIA v2 API, normalizes time-series metrics, flags price anomalies via Hampel filtering, fits ARIMA(1,1,1) probabilistic forecasting models, and serves an interactive SaaS dark-mode dashboard.**

[Key Features](#key-features) • [Architecture](#architecture) • [Tech Stack](#tech-stack) • [Quickstart](#quickstart) • [CLI Reference](#cli-reference) • [Engineering Decisions](#engineering-decisions)

</div>

---

## Overview

**Energy Market Intelligence** provides hedge funds, quantitative analysts, and energy traders with actionable spot price monitoring, volatility surface tracking, and statistical price forecasting across critical energy commodities:
* **WTI Crude Oil** (`RWTC` — Cushing, OK Spot Price, `$/bbl`)
* **Natural Gas** (`RNGWHHD` — Henry Hub Spot Price, `$/MMBtu`)
* **Conventional Gasoline** (`EMM_EPMR_PTE_NUS_DPG` — U.S. Regular Average, `$/gal`)

Built adhering to modern senior software engineering practices: strictly decoupled single-responsibility packages, zero mutable shared state, the Repository pattern over SQL storage, mathematically robust anomaly detection, and a reactive, glassmorphic dark UI.

---

## Dashboard Preview

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│  ⚡ QUANTITATIVE ENERGY INTELLIGENCE                                                   │
│  Energy Market Intelligence                        [● EIA v2 Stream Active] [95% CI]   │
│  Institutional-grade monitoring, volatility surface, and ARIMA(1,1,1) forecasting      │
├────────────────────────────────────────────────────────────────────────────────────────┤
│  [ Commodity: WTI Crude Oil ▼ ]        [ Date Range: 2024-01-01  ➜  2026-03-31 ]       │
├────────────────────────────────────────────────────────────────────────────────────────┤
│  ┌───────────────────────┐   ┌───────────────────────┐   ┌──────────────────────────┐  │
│  │ SPOT PRICE            │   │ WEEK-OVER-WEEK        │   │ 4-WEEK MOVING BASELINE   │  │
│  │ $71.48 $/bbl          │   │ +3.12%                │   │ $69.85 $/bbl             │  │
│  └───────────────────────┘   └───────────────────────┘   └──────────────────────────┘  │
├────────────────────────────────────────────────────────────────────────────────────────┤
│  WTI Crude Oil — Price Trajectory & Horizon Forecast                                   │
│  ┌──────────────────────────────────────────────────────────────────────────────────┐  │
│  │   80 ───.                                              ╱▔▔▔ 95% Confidence Band  │  │
│  │   75 ─── ╲      .───.                 .───────────────╱─── ARIMA Forecast        │  │
│  │   70 ─────╲────╱─────╲───────.───────╱                                           │  │
│  │   65 ──────'──'       '─────' ╲─────'                                            │  │
│  │       Jan 24     Jul 24     Jan 25     Jul 25     Jan 26     Forecast Horizon    │  │
│  └──────────────────────────────────────────────────────────────────────────────────┘  │
├────────────────────────────────────────────────────────────────────────────────────────┤
│  Normalized Volatility Surface (Z-score vs 4-Week Moving Window)                       │
│  ┌──────────────────────────────────────────────────────────────────────────────────┐  │
│  │   +2σ - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -  │  │
│  │   0.0 ──▄█▄───█▄────────█▄──▄█▄─────█▄───▄██▄──────────────────────────────────  │  │
│  │   -2σ - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -  │  │
│  └──────────────────────────────────────────────────────────────────────────────────┘  │
└────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## Key Features

- **Robust REST Ingestion Client (`ingestion/eia_client.py`)**:
  - Full support for the current **EIA v2 REST API** hierarchy (data routes + series facets + frequencies).
  - Transient error classification: automatically retries HTTP `429` (rate limits) and `5xx` with exponential backoff plus randomized jitter to prevent thundering-herd spikes.
  - Fail-fast exception translation: wraps network or parsing failures into a single domain exception (`EIAAPIError`).
  - Keep-alive connection pooling via reusable `requests.Session`.

- **Pure Transformation Pipeline (`transform/pipeline.py`)**:
  - Stateless, functional data transformations returning immutable DataFrames without side-effects.
  - **Hampel Filter Outlier Detection**: Computes a centered rolling window of median absolute deviations (MAD × 1.4826) at 3.5σ to catch localized spikes without mistaking genuine structural regime shifts for anomalies.
  - Dynamic analytics: period-over-period percentage changes (`pct_change`), trailing 4-week moving average (`rolling_avg_4w`), standard deviation, and rolling standardized Z-scores (`z_score`).

- **Decoupled Persistence Layer (`storage/repository.py`)**:
  - Strict **Repository Pattern**: No SQL escapes the repository layer; callers trade solely in pandas DataFrames.
  - Lambda-architecture table separation:
    - `raw_prices`: Immutable ledger of raw observations (`INSERT OR IGNORE`).
    - `processed_prices`: Rebuildable analytical view with full state overwrite (`ON CONFLICT DO UPDATE`).
  - SQLite with Write-Ahead Logging (`PRAGMA journal_mode=WAL`) and thread serialization locks for multi-threaded WSGI safety.

- **Econometric Forecasting Engine (`analytics/forecasting.py`)**:
  - **ARIMA(1,1,1)**: First-order autoregressive, once-differenced, moving-average time-series model fit via `statsmodels` to account for non-stationary commodity price drift.
  - Analytic 95% confidence intervals expanding over the forecast horizon.
  - Comparative ordinary least-squares (OLS) linear trend baseline model.
  - Exportable diagnostic metrics: Akaike Information Criterion (AIC), Bayesian Information Criterion (BIC), and estimated parameters.

- **SaaS Glassmorphism UI (`dashboard/`)**:
  - Designed with Linear/Stripe/Vercel-inspired dark mode ergonomics.
  - Pure function render logic decoupled from Dash callback triggers for headless unit-testability.
  - Transparent Plotly figures floating inside blurred acrylic panels with neon cyan accents (`#00f0ff`), emerald gains (`#10b981`), and coral warning levels (`#f43f5e`).

---

## Architecture

```
                      ┌────────────────────────────┐
                      │    U.S. EIA REST API v2    │
                      └─────────────┬──────────────┘
                                    │ HTTP GET (Session, Retries, Jitter)
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│ [ INGESTION LAYER ]              EIAClient                              │
│                                  Fetches raw JSON payload               │
└───────────────────────────────────┬─────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│ [ TRANSFORM LAYER ]              CommodityPipeline                      │
│                                  clean()  ──► Hampel MAD Filter (3.5σ)  │
│                                  enrich() ──► pct_change, rolling stats │
└───────────────────────────────────┬─────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│ [ STORAGE LAYER ]                CommodityRepository (SQLite WAL)       │
│                                  raw_prices (idempotent raw facts)      │
│                                  processed_prices (derived analytics)   │
└───────────────────────┬───────────────────────────┬─────────────────────┘
                        │                           │
                        ▼                           ▼
┌───────────────────────────────────┐       ┌─────────────────────────────┐
│ [ ANALYTICS LAYER ]               │       │ [ DASHBOARD LAYER ]         │
│ PriceForecaster (ARIMA 1,1,1)     │       │ Plotly Dash & Gunicorn WSGI │
│ Predicts horizon + 95% conf band  │       │ KPI Cards & Volatility      │
└───────────────────────┬───────────┘       └──────────────▲──────────────┘
                        │                                  │
                        └──────────────────────────────────┘
```

---

## Tech Stack

| Layer | Technology | Key Capabilities |
| :--- | :--- | :--- |
| **Ingestion** | Python `requests` | Session connection pooling, exponential backoff, jitter, Retry-After compliance |
| **Transform** | `pandas`, `numpy` | Vectorized rolling aggregations, Hampel outlier filter, NaN-safe coercion |
| **Analytics** | `statsmodels`, `scikit-learn` | ARIMA(1,1,1) maximum-likelihood estimation, AIC/BIC diagnostics, OLS trend line |
| **Storage** | `sqlite3` | Zero-configuration relational database, WAL concurrency mode, indexed queries |
| **Presentation**| `dash`, `plotly` | Declarative reactive callbacks, WebGL/SVG chart rendering, CSS glassmorphism |
| **Configuration**| `python-dotenv`, `dataclasses` | 12-Factor App config separation, immutable frozen dataclass, early validation |
| **Testing & CI** | `pytest`, `black`, `flake8` | Deterministic unit tests with in-memory fixtures, PEP 8 compliance |

---

## Quickstart

### 1. Clone the Repository

```bash
git clone https://github.com/Mohd-Abd-Khan/energy-market-intelligence.git
cd energy-market-intelligence
```

### 2. Set Up Virtual Environment

```bash
# macOS/Linux
python3 -m venv .venv
source .venv/bin/activate

# Windows (PowerShell)
python -m venv .venv
.venv\Scripts\Activate.ps1
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
pip install -r requirements-dev.txt   # for testing & linting
```

### 4. Configure Environment Variables

Register for a free EIA API key at [eia.gov/opendata](https://www.eia.gov/opendata/) (takes 30 seconds).

```bash
# Copy template
cp .env.example .env    # On Windows: copy .env.example .env
```

Open `.env` and set your key:
```ini
EIA_API_KEY=your_actual_eia_api_key_here
DB_PATH=data/commodity.db
DEFAULT_COMMODITY=WTI_CRUDE
LOOKBACK_DAYS=730
```

### 5. Ingest Market Data

Populate the database with historical observations and computed analytics:

```bash
python run_pipeline.py --refresh
```

Output:
```text
================================================================
SERIES            FETCHED  NEW RAW  PROCESSED  STATUS
----------------------------------------------------------------
WTI_CRUDE             104      104        104  ok
NATURAL_GAS           104      104        104  ok
GASOLINE              104      104        104  ok
----------------------------------------------------------------
TOTAL                 312      312        312
================================================================
Elapsed: 2.14s  |  DB: .../data/commodity.db
```

### 6. Launch the Dashboard

```bash
# Development server (with hot reload):
python -m dashboard.app

# Production deployment via WSGI (Linux/macOS):
gunicorn dashboard.app:server --bind 127.0.0.1:8050 --workers 2
```

Navigate to **`http://127.0.0.1:8050`** in your browser.

---

## CLI Reference

The pipeline orchestrator (`run_pipeline.py`) provides flexible CLI arguments:

```bash
# Ingest only Crude Oil
python run_pipeline.py --series WTI_CRUDE

# Ingest multiple specific series
python run_pipeline.py --series WTI_CRUDE GASOLINE

# Custom historical start window
python run_pipeline.py --start 2023-01-01

# Force re-fetching entire window (bypassing incremental cache)
python run_pipeline.py --refresh
```

---

## Engineering Decisions

### Why the Repository Pattern?
All SQL statements are isolated inside `CommodityRepository`. The ingestion pipeline, analytical models, and Plotly Dash UI have zero direct dependency on SQL or database drivers. To migrate from SQLite to PostgreSQL, Amazon Aurora, or Snowflake, only `storage/repository.py` requires modification.

### Why Separate Raw vs. Processed Tables?
- `raw_prices` stores immutable market observations (`series_id`, `date`, `value`). It uses `INSERT OR IGNORE` so duplicate ingestion runs are completely idempotent.
- `processed_prices` stores derived mathematical calculations (rolling averages, volatility, outliers). Because trailing window stats evolve as new observations arrive, this table is upserted (`ON CONFLICT DO UPDATE`).

### Hampel Filter vs. Global Standard Deviation
Traditional 3σ global filtering misidentifies prolonged macro regime changes (e.g., oil price cycles or supply disruptions) as constant outliers. The Hampel filter uses a centered rolling window of Medians and Median Absolute Deviations (MAD), isolating genuine short-term price spikes and bad ticks without flagging structural market trends.

---

## Testing & Quality Assurance

Run the comprehensive test suite offline in ~1 second:

```bash
# Run 32+ unit tests
pytest

# Check code formatting
black --check .

# Run linter
flake8 .
```

---

## Project Structure

```text
energy-market-intelligence/
├── analytics/
│   ├── __init__.py
│   └── forecasting.py             # ARIMA(1,1,1) & Linear Trend forecasters
├── assets/
│   ├── dashboard.png              # UI visual reference
│   └── style.css                  # Custom SaaS dark & glassmorphism theme
├── dashboard/
│   ├── __init__.py
│   ├── app.py                     # Dash entrypoint & WSGI server instance
│   ├── callbacks.py               # Pure render logic & Dash callback wiring
│   └── layout.py                  # Component layout tree & design tokens
├── data/
│   └── .gitkeep                   # Local SQLite storage folder
├── ingestion/
│   ├── __init__.py
│   └── eia_client.py              # EIA v2 API client with retry/backoff
├── storage/
│   ├── __init__.py
│   └── repository.py              # SQLite repository pattern implementation
├── tests/
│   ├── __init__.py
│   ├── conftest.py                # Pytest shared fixtures & synthetic series
│   ├── test_forecasting.py        # ARIMA & Linear regression test cases
│   ├── test_pipeline.py           # Data cleansing & enrichment tests
│   └── test_repository.py         # Database CRUD & idempotency tests
├── transform/
│   ├── __init__.py
│   └── pipeline.py                # Transformation pipeline & Hampel filter
├── .env.example                   # Committed environment variable template
├── .flake8                        # Flake8 style config
├── .gitignore                     # Git exclusions
├── config.py                      # Central settings & commodity catalog
├── LICENSE                        # MIT License
├── pyproject.toml                 # Packaging metadata & tool options
├── README.md                      # Comprehensive project documentation
├── requirements.txt               # Pinned runtime dependencies
├── requirements-dev.txt           # Testing & linting dependencies
└── run_pipeline.py                # End-to-end orchestration CLI
```

---

## License

This project is licensed under the [MIT License](LICENSE) © 2026 **Energy Intelligence Team**.
