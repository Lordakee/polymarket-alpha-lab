# Polymarket Alpha Lab

Polymarket Alpha Lab is a research-first project for finding, scoring, and validating Polymarket markets before any capital is committed.

The long-term goal is an automated system that can screen markets, research candidates, propose trades, and eventually execute only after validation gates and risk controls have been proven. The first version is intentionally not a trading bot. It is a planning and research workspace for:

- market discovery and metadata normalization
- order book and liquidity quality scoring
- strategy research around measurable edges
- paper-trading journals, risk gates, and rejection review
- future backtesting and signal validation

## Phase 1 Scope

This repository currently contains the project design, research notes, implementation plans, a read-only market scanner, research packet assembly, bid/ask paper-fill simulation, JSONL paper-trade journaling, paper-only risk gates, rejected-candidate logs, paper position ledgers, executable NAV marks, paper-only portfolio analytics, exposure reports, and executable-NAV drawdown reports.

The current phase does not contain:

- account authentication
- private key handling
- automated order placement
- live trading logic
- compliance or legal analysis

These are Phase 1 scope boundaries. They are not permanent non-goals. Future execution work is tracked in the automated investment roadmap and must pass documented validation gates before live capital is introduced.

## Recommended Direction

The strongest first product is a market-quality and edge-scanning system:

1. Use official Polymarket APIs for market, event, order book, historical price, and trade data.
2. Rank markets by tradability, liquidity, rule clarity, activity, and time structure.
3. Start with measurable edges: spread quality, liquidity rewards, multi-outcome pricing inconsistencies, related-market constraints, and post-fill drift.
4. Validate everything through paper trading before execution automation is considered.

## Level 0 Usage

Run the current read-only scanner with:

```bash
.venv/bin/python -m pip install -e '.[dev]'
.venv/bin/polymarket-alpha-lab scan --limit 25 --output artifacts/market-scores.json
```

The scan uses public Polymarket market-data endpoints only. It does not authenticate, handle private keys, place orders, or trade. Raw API payloads are archived under `data/raw/`, and ranked candidate output is written to `artifacts/market-scores.json`; both directories are ignored by git.

## Level 1A Status

Level 1A adds research packets, bid/ask order-book-walk paper-fill simulation, and JSONL paper-trade journals. It remains paper-only: no account authentication, no private-key handling, no order placement, no order cancellation, no user WebSocket, no heartbeat, no live trading, and no compliance/legal/geographic-access analysis.

## Level 1A Python API

Node 3 is exposed through Python APIs rather than new CLI commands:

- Build research packets with `build_research_packet(...)`, which returns `ResearchPacket`.
- Simulate bid/ask paper fills with `PaperOrder(...)` and `simulate_order_book_fill(...)`, which returns `PaperFill`.
- Persist JSONL journal entries with `PaperTradeRecord.from_packet_and_fill(...)` and `PaperTradeJournal(path).append(record)`.

## Level 1B Node 1 Status

Level 1B Node 1 adds configurable paper-only risk gates and append-only rejected-candidate logs. It does not place orders, authenticate, handle private keys, cancel orders, open user WebSockets, run heartbeat logic, or create live-trading proposals.

## Level 1B Node 1 Python API

Node 1 is exposed through Python APIs:

- Configure entry gates with `RiskGateConfig(...)`.
- Evaluate packets with `evaluate_research_packet_risk(packet, config)`.
- Persist rejected candidates with `RejectedCandidateRecord.from_packet_and_decision(...)` and `RejectedCandidateLog(path).append(record)`.

## Level 1B Node 2 Status

Level 1B Node 2 adds a paper-only position ledger and executable NAV marks derived from accepted paper-trade journal records and supplied public order book snapshots. It does not fetch order books, place orders, authenticate, handle private keys, cancel orders, open user WebSockets, run heartbeat logic, reconcile exchange account positions, or create live-trading proposals.

## Level 1B Node 2 Python API

Node 2 is exposed through Python APIs:

- Build paper portfolios with `build_paper_portfolio(records, starting_cash=Decimal("10000"))`, which returns `PaperPortfolio`.
- Mark open positions with `mark_paper_nav(portfolio, books_by_token_id, marked_at=datetime.now(UTC))`, which returns `PaperNavSnapshot`.
- Persist executable NAV snapshots with `PaperNavLog(path).append(snapshot)`.

## Level 1B Node 3 Status

Level 1B Node 3 adds paper-only portfolio analytics, exposure concentration, liquidity-risk, report-only threshold breaches, and executable-NAV drawdown reports derived from paper portfolio and NAV artifacts. It does not fetch market, order-book, or account data, place or cancel orders, authenticate, handle private keys, open user WebSockets, run heartbeat logic, use a trading SDK, create trade proposals, reconcile exchange accounts, scrape websites, or perform compliance/legal/geographic analysis.

## Level 1B Node 3 Python API

Node 3 is exposed through Python APIs:

- Configure report thresholds with `PaperAnalyticsConfig(...)`.
- Build paper analytics reports with `build_paper_analytics_report(portfolio, snapshot, config=..., generated_at=...)`, which returns `PaperAnalyticsReport`.
- Build executable-NAV drawdown points with `build_paper_drawdown_points(snapshots)`.
- Persist report snapshots with `PaperAnalyticsLog(path).append(report)`.

## Automation Roadmap

The recommended staged path is:

1. Level 0: read-only data ingestion, normalization, and market scoring.
2. Level 1: automated research packets and bid/ask paper trading.
3. Level 2: AI-generated trade proposals with explicit human approval.
4. Level 3: small, risk-limited live pilots for whitelisted strategies.
5. Level 4: strategy-specific automated execution after live pilot gates are met.

See:

- `docs/superpowers/specs/2026-06-13-automated-investment-roadmap.md`
- `docs/research/validation-gates.md`

## Repository Layout

```text
.
├── AGENTS.md
├── README.md
├── docs
│   ├── research
│   │   ├── data-api-research.md
│   │   ├── risk-system-research.md
│   │   ├── strategy-research.md
│   │   └── validation-gates.md
│   ├── sources.md
│   └── superpowers
│       ├── plans
│       │   ├── 2026-06-13-level-0-market-intelligence.md
│       │   ├── 2026-06-13-level-1-research-packets-paper-trading.md
│       │   ├── 2026-06-13-level-1b-paper-analytics-risk-exposure.md
│       │   ├── 2026-06-13-level-1b-rejections-risk-gates.md
│       │   ├── 2026-06-13-level-1b-positions-nav.md
│       │   └── 2026-06-13-project-bootstrap.md
│       └── specs
│           ├── 2026-06-13-automated-investment-roadmap.md
│           └── 2026-06-13-polymarket-alpha-lab-design.md
├── pyproject.toml
├── src
│   └── polymarket_alpha_lab
│       ├── __init__.py
│       ├── analytics.py
│       ├── api.py
│       ├── archive.py
│       ├── cli.py
│       ├── domain.py
│       ├── journal.py
│       ├── normalize.py
│       ├── paper.py
│       ├── pipeline.py
│       ├── positions.py
│       ├── rejections.py
│       ├── research.py
│       ├── risk.py
│       └── scoring.py
└── tests
    ├── test_analytics.py
    ├── test_analytics_scope.py
    ├── test_api.py
    ├── test_archive.py
    ├── test_cli.py
    ├── test_domain.py
    ├── test_init.py
    ├── test_journal.py
    ├── test_normalize.py
    ├── test_paper.py
    ├── test_pipeline.py
    ├── test_positions.py
    ├── test_rejections.py
    ├── test_research.py
    ├── test_risk_gates.py
    └── test_scoring.py
```

## Useful Commands

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -e '.[dev]'
.venv/bin/python -m pytest
.venv/bin/polymarket-alpha-lab scan --limit 25
codegraph status .
codegraph files
```

After CodeGraph is initialized, use it before text search when locating source:

```bash
codegraph explore "MarketSnapshot MarketScore"
codegraph node src/polymarket_alpha_lab/domain.py
```
