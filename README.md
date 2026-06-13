# Polymarket Alpha Lab

Polymarket Alpha Lab is a research-first project for finding, scoring, and validating Polymarket markets before any capital is committed.

The first version is intentionally not a trading bot. It is a planning and research workspace for:

- market discovery and metadata normalization
- order book and liquidity quality scoring
- strategy research around measurable edges
- paper-trading journals and risk review
- future backtesting and signal validation

## Current Scope

This repository currently contains the project design, research notes, implementation plan, and a minimal Python domain model skeleton.

It does not contain:

- account authentication
- private key handling
- automated order placement
- live trading logic
- compliance or legal analysis

## Recommended Direction

The strongest first product is a market-quality and edge-scanning system:

1. Use official Polymarket APIs for market, event, order book, historical price, and trade data.
2. Rank markets by tradability, liquidity, rule clarity, activity, and time structure.
3. Start with measurable edges: spread quality, liquidity rewards, multi-outcome pricing inconsistencies, related-market constraints, and post-fill drift.
4. Validate everything through paper trading before execution automation is considered.

## Repository Layout

```text
.
├── AGENTS.md
├── README.md
├── docs
│   ├── research
│   │   ├── data-api-research.md
│   │   ├── risk-system-research.md
│   │   └── strategy-research.md
│   ├── sources.md
│   └── superpowers
│       ├── plans
│       │   └── 2026-06-13-project-bootstrap.md
│       └── specs
│           └── 2026-06-13-polymarket-alpha-lab-design.md
├── pyproject.toml
├── src
│   └── polymarket_alpha_lab
│       ├── __init__.py
│       └── domain.py
└── tests
    └── test_domain.py
```

## Useful Commands

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -e '.[dev]'
.venv/bin/python -m pytest
codegraph status .
codegraph files
```

After CodeGraph is initialized, use it before text search when locating source:

```bash
codegraph explore "MarketSnapshot MarketScore"
codegraph node src/polymarket_alpha_lab/domain.py
```
