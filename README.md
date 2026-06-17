# Polymarket Alpha Lab

Polymarket Alpha Lab is a research-first project for finding, scoring, and validating Polymarket markets before any capital is committed.

The long-term goal is an automated system that can screen markets, research candidates, propose trades, and eventually execute only after validation gates and risk controls have been proven. The first version is intentionally not a trading bot. It is a planning and research workspace for:

- market discovery and metadata normalization
- order book and liquidity quality scoring
- strategy research around measurable edges
- paper-trading journals, risk gates, and rejection review
- future backtesting and signal validation

## Phase 1 Scope

This repository currently contains the project design, research notes, implementation plans, a read-only market scanner, research packet assembly, bid/ask paper-fill simulation, JSONL paper-trade journaling, paper-only risk gates, rejected-candidate logs, paper position ledgers, executable NAV marks, paper-only portfolio analytics, exposure reports, executable-NAV drawdown reports, paper-only analytics history validation, paper-only forecast evidence reports, paper-only cost-aware event strategy reports, paper-only project screening research queues, paper-only manual-review queues, human-review proposal packet artifacts, append-only proposal-review record artifacts, proposal-review summary report artifacts, proposal-review quality gate artifacts, proposal-review diagnostic artifacts, proposal-review coverage report artifacts, proposal-review dossier artifacts, proposal-review dossier batch health artifacts, proposal evidence comparison artifacts, proposal evidence comparison history artifacts, proposal evidence comparison history batch-health artifacts, proposal evidence comparison history batch-health trend artifacts, proposal evidence comparison history batch-health trend-batch artifacts, proposal evidence comparison history batch-health trend-batch health artifacts, and proposal evidence comparison history batch-health trend-batch health trend artifacts.

The current phase does not contain:

- account authentication
- private key handling
- automated order placement
- live trading logic
- compliance or legal analysis

These are Phase 1 scope boundaries. They are not permanent non-goals. Future execution work is tracked in the automated investment roadmap and must pass documented validation gates before live capital is introduced.

## Phase 1 Operational Freeze

Phase 1 decision behavior is frozen while markets are pending settlement. Do not tune screening weights or change strategy-cycle behavior while markets are pending settlement, and do not change forecast prompts/providers, paper-execution triggers, or sizing rules from unresolved NAV marks.

Allowed additions during the freeze are limited to `paper_only`, `report_only`, `readonly` observability over existing local artifacts. Boundary shorthand: no fetch, no auth, no wallet, no order, no rank, no recommend, no trade instruction, no financial advice.

## NAV Risk Metrics v0 Status

NAV Risk Metrics v0 is a paper-only/report-only risk summary over existing paper NAV logs. It consumes typed `PaperNavSnapshot` values normally read through the existing `PaperNavLog.read(...)`; it computes NAV time-series risk, latest mark-status counts, pending notional, and latest exposure concentration for audit visibility only.

The `nav-risk` command is separate from strategy-cycle, NAV marking, outcome tracking, and paper execution. It does not fetch market/account/order data, authenticate, handle wallets or private keys, place/sign/submit/cancel orders, rank investments, recommend trades, provide trade instruction, provide financial advice, or alter any strategy behavior.

## NAV Risk Metrics v0 Python API

- Configure the report with `PaperNavRiskMetricsConfig(config_version="nav-risk-metrics-v0")`.
- Build risk summaries with `build_paper_nav_risk_metrics_report(nav_snapshots, config=config, generated_at=...)`, which returns `PaperNavRiskMetricsReport`.
- Inspect latest exposure concentration with `PaperNavRiskExposureRow` values on `report.exposure_rows`.
- Print local metrics from the CLI with `polymarket-alpha-lab nav-risk --nav-log <path>`; the command reads local NAV JSONL logs only and preserves the same `paper_only`, `report_only`, `readonly` boundary: no fetch, no auth, no wallet, no order, no rank, no recommend, no trade instruction, no financial advice.

## Strategy Risk Audit v0 Status

Strategy Risk Audit v0 is a pure, paper-only/report-only audit over caller-supplied typed reports: `PerformanceSummary`, `PaperNavRiskMetricsReport`, and optional `OutcomeTrackingReport`. It reduces existing paper history, settlement evidence, nested forecast probability quality, NAV drawdown, and open-exposure observations into five gates: `paper_history`, `settlement_evidence`, `forecast_quality`, `nav_drawdown`, and `open_exposure`.

The report emits one status: `audit_ready` when every gate passes, `blocked_by_risk` when any risk gate fails, and `insufficient_evidence` when evidence is incomplete and no gate fails. `paper_only is True` and `report_only is True` are hard-enforced on every report.

Phase 1 boundary: this module is pure local report math. It does not score markets, select projects, tune strategy weights, size positions, read files, write logs, fetch, authenticate, handle wallets, construct or use API clients, perform live trading, place/sign/submit/cancel orders, make recommendations, rank investments, provide trade instruction, or provide financial advice.

## Strategy Risk Audit v0 Python API

- Configure the audit with `PaperStrategyRiskAuditConfig(...)`, including the minimum paper-history, settlement-evidence, forecast-probability-observation thresholds plus NAV drawdown and open-exposure limits.
- Build the audit with `build_paper_strategy_risk_audit_report(performance_summary=..., nav_risk_report=..., outcome_report=..., config=..., generated_at=...)`, which returns `PaperStrategyRiskAuditReport` from caller-supplied typed reports only.
- Inspect deterministic gate rows with `PaperStrategyRiskAuditGateResult` values on `report.gate_results`; gate names are `paper_history`, `settlement_evidence`, `forecast_quality`, `nav_drawdown`, and `open_exposure`, and the final `report.status` is one of `audit_ready`, `blocked_by_risk`, or `insufficient_evidence`.
- There is no file reader, log writer, fetch path, auth path, wallet path, API-client path, live-trading path, order path, recommendation path, ranking path, strategy-weight tuning, project selection, market scoring, position sizing, or financial-advice surface.

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

## Level 1B Node 4 Status

Level 1B Node 4 adds paper-only analytics history validation over existing `PaperAnalyticsReport` values, including validation-gate summaries, trend extrema, and evidence-readiness status for later human review. Its `paper_review_ready` status means the history artifact is ready for manual review only; it is not a proposal-generation, promotion, or live-execution signal. It does not fetch historical market, order-book, or account data, use external loaders, scrape websites, authenticate, handle private keys, place or cancel orders, open user WebSockets, run heartbeat logic, use a trading SDK, create trade proposals, reconcile exchange accounts, or perform compliance/legal/geographic analysis.

## Level 1B Node 4 Python API

Node 4 is exposed through Python APIs:

- Configure history thresholds with `PaperAnalyticsHistoryConfig(...)`.
- Build paper analytics history reports with `build_paper_analytics_history_report(reports, config=..., generated_at=...)`, which returns `PaperAnalyticsHistoryReport`.
- Inspect validation rows with `PaperAnalyticsHistoryGateResult` and trend rows with `PaperAnalyticsHistoryTrend`.
- Persist history snapshots with `PaperAnalyticsHistoryLog(path).append(report)`.

## Level 1B Node 5 Status

Level 1B Node 5 adds paper-only forecast evidence reports over supplied `PaperForecastEvidenceObservation` values, including probability bucket quality, executable-edge gap and hit-rate checks, residual exposure checks, and append-only JSONL snapshots. Its `paper_review_ready` status means the evidence artifact is ready for manual review only; it is not a promotion, trade, or live-execution signal. It does not fetch market, order-book, price history, or account data, use external loaders, scrape websites, authenticate, handle private keys, place or cancel orders, open user WebSockets, run heartbeat logic, use a trading SDK, reconcile exchange accounts, or perform compliance/legal/geographic analysis.

## Level 1B Node 5 Python API

Node 5 is exposed through Python APIs:

- Configure evidence thresholds with `PaperForecastEvidenceConfig(...)`.
- Create evidence rows with `PaperForecastEvidenceObservation(...)`.
- Build paper forecast evidence reports with `build_paper_forecast_evidence_report(observations, config=..., generated_at=...)`, which returns `PaperForecastEvidenceReport`.
- Inspect evidence gates with `PaperForecastEvidenceGateResult` and probability buckets with `PaperForecastEvidenceBucket`.
- Persist forecast evidence snapshots with `PaperForecastEvidenceLog(path).append(report)`.

## Level 1B Node 6 Status

Level 1B Node 6 adds paper-only manual-review queues over supplied `PaperManualReviewCandidate` values, `MarketScore` rows, `PaperAnalyticsHistoryReport`, and `PaperForecastEvidenceReport`. Its `paper_review_ready` status means a queue item is ready for human inspection only; it is not proposal generation, strategy promotion, a trade instruction, an approval workflow, or a live-execution signal. It does not fetch market, order-book, price-history, outcome, or account data, read external history, scrape websites, authenticate, handle private keys, place or cancel orders, open user WebSockets, run heartbeat logic, use a trading SDK, reconcile exchange accounts, or perform compliance/legal/geographic analysis.

## Level 1B Node 6 Python API

Node 6 is exposed through Python APIs:

- Configure review thresholds and boundary text with `PaperManualReviewConfig(...)`.
- Create queue candidates with `PaperManualReviewCandidate(...)`.
- Build paper manual-review queues with `build_paper_manual_review_queue(candidates, market_scores=..., analytics_history=..., forecast_evidence=..., config=..., generated_at=...)`, which returns `PaperManualReviewQueue`.
- Inspect ranked rows with `PaperManualReviewQueueItem`.
- Persist manual-review snapshots with `PaperManualReviewLog(path).append(queue)`.

## Cost-Aware Event Strategy v0 Status

Cost-Aware Event Strategy v0 adds a paper-only and report-only event-contract evaluator over caller-supplied fair probability, confidence, YES/NO bid/ask, ask depth, spread, resolution risk, and cost assumptions. It treats Polymarket markets as event probability YES/NO outcome-token contracts and evaluates buy-side research against executable YES/NO ask prices, not midpoint, last price, displayed probability, or chart price. Supplied bids are preserved in the report for audit context, but entry-edge math uses asks.

The report models taker fees and explicit non-fee costs for slippage, funding, finalization, time, and risk before computing net paper edge. A selected side only means the supplied inputs create a paper-review candidate under the configured thresholds; it is not a trade instruction, investment ranking, recommendation, financial advice, or live-execution signal.

It does not fetch market data, read account data, authenticate, handle wallets, private keys, or credentials, use API clients, use browser automation, place, submit, sign, or cancel orders, rank investments, recommend trades, provide financial advice, or perform compliance/legal/geographic analysis.

Boundary shorthand: no fetch, no auth, no wallet, no order, no rank, no recommend, no financial advice.

## Cost-Aware Event Strategy v0 Python API

Cost-Aware Event Strategy v0 is exposed through Python APIs:

- Create paper market snapshots with `PaperCostAwareEventMarketSnapshot(...)`.
- Configure explicit research costs with `PaperCostAwareEventCostAssumptions(...)`.
- Configure paper-review thresholds with `PaperCostAwareEventStrategyConfig(...)`.
- Build cost-aware event strategy reports with `build_paper_cost_aware_event_strategy_report(...)`, which returns `PaperCostAwareEventStrategyReport`.
- Inspect side results and gates with `PaperCostAwareEventSideResult` and `PaperCostAwareEventStrategyGateResult`.
- Optionally append already-built reports with `PaperCostAwareEventStrategyLog(path).append(report)`; there is no market fetcher, account reader, order API, JSONL reader, loader, replay, or from-file API.

## Project Screening v0 Status

Project Screening v0 adds a paper-only and report-only screening layer over already-built `PaperCostAwareEventStrategyReport` values. It turns supplied cost-aware event strategy reports into a deterministic human research queue for review workflow ergonomics. Queue sequence and screening scores are research-triage artifacts only; they are not investment rankings, not trade recommendations, not trade instructions, not financial advice, not approval workflow outputs, and not live-execution signals.

It consumes only caller-supplied cost-aware reports. It does not fetch market data, read account data, authenticate, handle wallets, private keys, or credentials, use API clients, use browser automation, place, submit, sign, or cancel orders, rank investments, recommend trades, provide financial advice, or perform compliance/legal/geographic analysis.

Boundary shorthand: no fetch, no auth, no wallet, no order, no rank, no recommend, no trade, no financial advice.

## Project Screening v0 Python API

Project Screening v0 is exposed through Python APIs:

- Configure screening thresholds and weights with `PaperProjectScreeningConfig(config_version="project-screening-v1")`.
- Build project screening reports from already-built `PaperCostAwareEventStrategyReport` values with `build_paper_project_screening_report(reports, config=config, generated_at=datetime.now(UTC))`, which returns `PaperProjectScreeningReport`.
- Inspect source candidate details with `PaperProjectScreeningCandidate`, queue rows with `PaperProjectScreeningQueueItem`, and screening gates with `PaperProjectScreeningGateResult`.
- Optionally append already-built screening reports with `PaperProjectScreeningLog(path).append(report)`; the only persistence surface is append-only JSONL for already-built reports. There are no data-fetch, exchange-state read, JSONL-read, replay, external-load, capital-action, or exchange-action helpers.

## Forecast Provider v0 Status

Forecast Provider v0 adds a paper-only and report-only naive forecast primitive that produces the `fair_probability_yes` and `confidence` values the Cost-Aware Event Strategy consumes but no module previously produced. The naive v0 baseline uses the executable YES ask as the fair probability and buckets confidence from book depth and spread; the `basis` field names the model (`yes_ask_naive_v0`) so downstream audits know this is a placeholder, not a real forecast model.

The forecast is research-triage only; it is not a trade instruction, investment ranking, recommendation, financial advice, or live-execution signal.

It consumes only caller-supplied markets and order books. It does not fetch market data, read account data, authenticate, handle wallets, private keys, or credentials, use API clients, use browser automation, place, submit, sign, or cancel orders, rank investments, recommend trades, provide financial advice, or perform compliance/legal/geographic analysis.

Boundary shorthand: no fetch, no auth, no wallet, no order, no rank, no recommend, no financial advice.

## Forecast Provider v0 Python API

Forecast Provider v0 is exposed through Python APIs:

- Configure naive forecast thresholds with `PaperForecastConfig(config_version="naive-forecast-v1")`.
- Build naive forecasts from caller-supplied markets and YES/NO order books with `build_paper_naive_forecast(market, yes_book, no_book, config=config, generated_at=datetime.now(UTC))`, which returns `PaperForecast`.
- Inspect the fair probability, confidence, basis, and reason codes via `PaperForecast`.
- Optionally append already-built forecasts with `PaperForecastLog(path).append(forecast)`; there is no market fetcher, account reader, order API, JSONL reader, loader, replay, or from-file API.

## Book-Imbalance Forecast v0 Status

Book-Imbalance Forecast v0 adds a paper-only and report-only improved forecast primitive that derives `fair_probability_yes` from YES order-book depth imbalance rather than from the executable ask alone. It quantizes the YES bid-vs-ask size imbalance first, then derives a bounded `nudge` off the executable YES ask, so the screening research queue carries non-zero-edge candidates instead of the naive baseline (`yes_ask_naive_v0`) whose stored edge is exactly 0. The `basis` field names the model (`book_imbalance_v0`) so downstream audits know this is a book-imbalance heuristic, not a real forecast model.

The forecast is research-triage only; it is not a trade instruction, investment ranking, recommendation, financial advice, or live-execution signal. `paper_only is True` and `report_only is True` are hard-enforced on every report.

It consumes only caller-supplied markets and order books. It does not fetch market data, read account data, authenticate, handle wallets, private keys, or credentials, use API clients, use browser automation, place, submit, sign, or cancel orders, rank investments, recommend trades, provide financial advice, or perform compliance/legal/geographic analysis.

Boundary shorthand: no fetch, no auth, no wallet, no order, no rank, no recommend, no financial advice.

## Book-Imbalance Forecast v0 Python API

Book-Imbalance Forecast v0 is exposed through Python APIs:

- Configure the imbalance heuristic thresholds with `PaperBookImbalanceForecastConfig(config_version="book-imbalance-v1")` (imbalance strength, max nudge, min book depth, and low/high confidence cutoffs).
- Build book-imbalance forecasts from caller-supplied markets and YES/NO order books with `build_paper_book_imbalance_forecast(market, yes_book, no_book, config=config, generated_at=datetime.now(UTC))`, which returns `PaperBookImbalanceForecast`. `no_book` is accepted for signature parity with the naive provider and for future cross-side sanity checks; it is not used by the v0 nudge math.
- Inspect the fair probability, confidence, `basis`, audit fields `yes_best_ask`, `yes_bid_size`, `yes_ask_size`, `imbalance`, and `nudge`, plus reason codes via `PaperBookImbalanceForecast`.
- Optionally append already-built forecasts with `PaperBookImbalanceForecastLog(path).append(forecast)`; there is no market fetcher, account reader, order API, JSONL reader, loader, replay, or from-file API.

## LLM Forecast v0 Status

LLM Forecast v0 adds a paper-only and report-only forecast primitive that produces a real epistemic P(YES) estimate from a probability model (Zhipu GLM-4-flash via stdlib urllib), rather than a microstructure heuristic. Unlike the naive (`yes_ask_naive_v0`) and book-imbalance (`book_imbalance_v0`) baselines, this estimate can pass calibration evidence gates, so it is the project's first "self-judge" primitive. It is split into two modules: `llm_research_transport` (the read-only outbound HTTPS network layer) and `llm_forecast` (the pure, network-free transform leaf). The `basis` field names the model (`llm_glm_v0`) so downstream audits know this is an LLM estimate, not a book heuristic.

The forecast is research-triage only; it is not a trade instruction, investment ranking, recommendation, financial advice, or live-execution signal. `paper_only is True` and `report_only is True` are hard-enforced on every report.

The transform leaf consumes only a caller-supplied market and an already-fetched probability-model result (dependency-injected); it does not fetch market data, read account data, authenticate, handle wallets, private keys, or credentials, use API clients, use browser automation, place, submit, sign, or cancel orders, rank investments, recommend trades, provide financial advice, or perform compliance/legal/geographic analysis. The transport layer performs a single read-only outbound HTTPS estimate to the public Zhipu endpoint (the same research-fetch class as `api.py`'s public Polymarket reads) and never authenticates to an exchange, reads accounts or positions, handles wallets or private keys, or places orders. The caller-supplied API token stays on the transport only and never reaches the forecast, logs, or archives.

Boundary shorthand: no fetch of private, account, wallet, credential, or order data; no auth, no wallet, no order, no rank, no recommend, no financial advice.

## LLM Forecast v0 Python API

LLM Forecast v0 is exposed through Python APIs:

- Configure the LLM forecast thresholds with `PaperLLMForecastConfig(config_version="llm-forecast-v1")` (model name, low/high confidence cutoffs, max question length).
- Build LLM forecasts from a caller-supplied market and an already-fetched probability-model result with `build_paper_llm_forecast(market, result=result, config=config, generated_at=datetime.now(UTC))`, which returns `PaperLLMForecast`. The `result` is typed against a leaf-local `_ProbabilityModelResult` Protocol so the leaf stays network-free; the transport's concrete result satisfies it structurally.
- Inspect the fair probability, confidence, `basis`, audit field `raw_p_yes` (pre-clamp), `model_name`, and reason codes via `PaperLLMForecast`. A `None` `raw_p_yes` falls back to `low_confidence_value` and records `("llm_parse_failed",)`; otherwise the value is clamped to `[0, 1]` and `("llm_probability_estimated",)` is recorded.
- Optionally append already-built forecasts with `PaperLLMForecastLog(path).append(forecast)`; there is no market fetcher, account reader, order API, JSONL reader, loader, replay, or from-file API.

## Cost-Aware Snapshot Builder v0 Status

Cost-Aware Snapshot Builder v0 adds a paper-only and report-only extractor that converts a caller-supplied `NormalizedMarket`, YES/NO order books, and a `PaperForecast` into the already-built `PaperCostAwareEventMarketSnapshot` that the Cost-Aware Event Strategy consumes. It resolves YES/NO by outcome name (with outcome index fallback) and derives spread and a v0 resolution-risk heuristic from market metadata.

The snapshot attempt envelope is research-triage only; it is not a trade instruction, investment ranking, recommendation, financial advice, or live-execution signal.

It consumes only caller-supplied markets, order books, and forecasts. It does not fetch market data, read account data, authenticate, handle wallets, private keys, or credentials, use API clients, use browser automation, place, submit, sign, or cancel orders, rank investments, recommend trades, provide financial advice, or perform compliance/legal/geographic analysis.

Boundary shorthand: no fetch, no auth, no wallet, no order, no rank, no recommend, no financial advice.

## Cost-Aware Snapshot Builder v0 Python API

Cost-Aware Snapshot Builder v0 is exposed through Python APIs:

- Configure snapshot extraction thresholds with `PaperCostAwareSnapshotConfig(config_version="snapshot-builder-v1")`.
- Build cost-aware market snapshot attempts from caller-supplied markets, YES/NO books, and a forecast with `build_paper_cost_aware_event_market_snapshot(market, yes_book, no_book, forecast, config=config, generated_at=datetime.now(UTC))`, which returns `PaperCostAwareSnapshotAttempt` whose `snapshot` field holds the already-built `PaperCostAwareEventMarketSnapshot` when `status == "snapshot_ready"`.
- Inspect per-attempt status and reason codes via `PaperCostAwareSnapshotAttempt`.
- Optionally append already-built attempts with `PaperCostAwareSnapshotLog(path).append(attempt)`; there is no market fetcher, account reader, order API, JSONL reader, loader, replay, or from-file API.

## Strategy Cycle v0 Status

Strategy Cycle v0 adds the first live-layer orchestrator: a paper-only and report-only research envelope that runs a self-contained read-only scan of the public Polymarket market universe. For each cycle it fetches the public Gamma market list, normalizes each market, archives the raw payloads, optionally ranks by the deterministic Level 0 scorer, truncates to a per-cycle budget, then evaluates each binary market through paired YES/NO order books, the frozen Stage 1a naive forecast, the cost-aware snapshot builder, and the cost-aware event strategy, finally aggregating into a deterministic project-screening research queue. Per-market isolation is mandatory: every market's fetch/normalize/snapshot path is wrapped in try/except, so one bad market is recorded as a cycle-layer or snapshot-builder `blocked_*` status and the cycle continues. This resolves the NormalizedMarket pipeline end to end.

The cycle's output `PaperStrategyCycleReport` is paper-only and report-only: it is a research audit envelope, never a trade instruction, investment ranking, recommendation, financial advice, or live-execution signal. `paper_only is True` and `report_only is True` are hard-enforced on the report.

It performs read-only public Gamma `/markets` and CLOB `/book` fetches only. It does not place, submit, sign, send, create, or cancel orders; does not authenticate; does not handle wallets, private keys, or credentials; does not read account, position, or exchange state; does not rank investments, recommend trades, or provide financial advice; and does not perform compliance/legal/geographic analysis.

Boundary shorthand: paper-only, report-only; read-only public Gamma/CLOB fetch only — no fetch of private, account, wallet, credential, or order data; no auth, no wallet, no order, no rank, no recommend, no financial advice.

## Strategy Cycle v0 Python API

Strategy Cycle v0 is exposed through Python APIs:

- Configure a cycle with `PaperStrategyCycleConfig(config_version=..., forecast_config=..., snapshot_config=..., strategy_config=..., screening_config=..., cost_assumptions=..., max_markets_per_cycle=50, prefilter_by_score=True)`.
- Run a paper-only strategy cycle with `run_strategy_cycle(*, client, scan_config, cycle_config, generated_at=None)`, which returns a `PaperStrategyCycleReport`. `client` is a caller-injected `MarketDataClient` (a local Protocol; this module does not import `api` — `cli.py` constructs the concrete public Gamma/CLOB reader and injects it).
- Inspect cycle counts, deterministic `blocked_counts`, and the nested `PaperProjectScreeningReport` via `PaperStrategyCycleReport`.
- Optionally append already-built cycle reports with `PaperStrategyCycleLog(path).append(report)`; there is no account reader, order API, wallet signer, JSONL reader, loader, replay, or from-file API.

## Paper Execution v0 Status

Paper Execution v0 closes the self-invest half of Phase 1: a paper-only and report-only leaf that turns each screening_ready candidate produced by the strategy cycle into an auditable paper trade. It runs INLINE inside `run_strategy_cycle` (never from replayed JSONL), where every snapshot_ready market's full in-memory context is available: the NormalizedMarket, both YES/NO OrderBookSnapshots, each book's RawArchiveEntry, the cost-aware event strategy report, and the project screening candidate. For each screening_ready candidate it walks `simulate_order_book_fill` against the chosen side's executable ask depth and journals a `PaperTradeRecord` to the configured paper trade journal. The evidence-gate chain (manual_review_queue / proposal_packet) is deliberately bypassed; paper-executed records carry a marker `strategy_type` (default `book_imbalance_screening_paper`) so they are filterable downstream.

The result is paper-only and report-only: it is a research/audit envelope, never a trade instruction, investment ranking, recommendation, financial advice, or live-execution signal. `paper_only is True` and `report_only is True` are hard-enforced on every result. Default-off: when `paper_execution_config is None` the cycle behaves byte-identically to Stage 1b/2/3 (no paper pass, no journal writes), and one bad paper execution never aborts the cycle (per-candidate try/except isolation, mirroring per-market isolation).

Phase 1 boundary: it only simulates a fill against the in-memory order book and appends to a paper journal. It does not fetch private, account, wallet, credential, or order data; no auth; no wallet; no order placement, submission, signing, sending, creation, or cancellation; no account, position, or exchange-state reads; no rank, no recommend, no financial advice; and no compliance/legal/geographic analysis.

Boundary shorthand: paper-only, report-only; simulate + journal only — no fetch of private/account/wallet/credential data, no auth, no wallet, no order, no rank, no recommend, no financial advice.

## Paper Execution v0 Python API

Paper Execution v0 is exposed through Python APIs:

- Configure the paper lane with `PaperExecutionConfig(config_version="paper-execution-v1", strategy_type="book_imbalance_screening_paper", paper_budget_size=Decimal("10.0000"), sizing_limiter="screening_book_depth", planned_exit_rule="hold_to_resolution", account_equity_before_trade=Decimal("10000.0000"), thesis_template=..., invalidating_conditions_template=..., rule_text=..., resolution_source_fallback="polymarket_event_resolution")` (frozen; all defaults paper-only/report-only).
- Execute one paper trade from a screening-ready candidate with `execute_paper_trade_from_screening(*, candidate, cost_aware_report, market, book, raw_book_archive_entry, market_raw_archive_entry, config, generated_at)`, which returns a `PaperExecutionResult` (paper-only/report-only; `fill` and `record` are populated on execution, otherwise a canonical `skipped_reason`).
- Inspect the per-attempt outcome via `PaperExecutionResult` (generated_at, market_slug, condition_id, token_id, side, fill, record, skipped_reason) and append results to a `PaperExecutionLog(path)`; the inline strategy-cycle pass instead journals the resulting `PaperTradeRecord` via `PaperTradeJournal`. There is no account reader, order API, wallet signer, live client, loader, replay, or from-file API.

## Paper Portfolio NAV v0 Status

Paper Portfolio NAV v0 gives paper trades an observable mark-to-market P&L. It reads a paper-trade journal back, rebuilds the portfolio, fetches the current public order book for every held token, and marks NAV -- closing the "did I make money?" loop. The only net-new logic is the composition: the new `PaperTradeJournal.read()` JSONL reader plus an orchestrator that chains the already-tested primitives (`build_paper_portfolio`, `normalize_order_book`, `mark_paper_nav`). An empty journal yields an empty portfolio, so no order books are fetched and the NAV collapses to `starting_cash`.

The result is paper-only and report-only: it is a research/audit NAV mark, never a trade instruction, investment ranking, recommendation, financial advice, or live-execution signal. `paper_only is True` is hard-enforced on every `PaperNavSnapshot`.

Phase 1 boundary: it only reads the local JSONL journal, performs read-only `get_order_book` fetches (already used by pipeline/strategy_cycle), and runs pure local NAV math. It does not fetch private, account, wallet, credential, or order data; no auth; no wallet; no order placement, submission, signing, sending, creation, or cancellation; no account, position, or exchange-state reads; no rank, no recommend, no financial advice; and no compliance/legal/geographic analysis.

Boundary shorthand: paper-only, report-only; read journal + read-only book fetch + pure NAV only -- no fetch of private/account/wallet/credential data, no auth, no wallet, no order, no rank, no recommend, no financial advice.

## Paper Portfolio NAV v0 Python API

- Read a paper-trade journal back into fully-typed records with `PaperTradeJournal.read(path)`, a static JSONL reader that reverses `PaperTradeJournal.append`'s serialization keyed to each field's resolved annotation (`Decimal` str -> `Decimal`, ISO str -> `datetime`, `list` -> `tuple` for `risk_tags`; `None` passes through for the optional `fill_*` fields). It skips blank lines, raises `ValueError` (with a line number) on non-JSON lines, and returns an empty tuple for an empty file. `build_paper_portfolio` re-validates every record.
- Mark the portfolio NAV end-to-end with `mark_paper_portfolio_nav(journal_path, *, starting_cash, client, marked_at, nav_log_path=None)`, which returns a `PaperNavSnapshot`. It reads the journal, builds the portfolio, fetches one book per held token via the injected client, marks NAV, and optionally appends the snapshot to a `PaperNavLog`. `starting_cash` must be a positive `Decimal` (`> 0`); the client is a local `MarketNavClient` Protocol (only `get_order_book(token_id=)`) so this module never imports `api` -- the concrete `PolymarketPublicClient` is constructed in `cli.py` and injected. `marked_at` is caller-supplied (deterministic for tests).
- Mark NAV from the CLI with `polymarket-alpha-lab portfolio-nav --journal <path> --starting-cash <Decimal> [--nav-log <path>]`, which prints a NAV summary (starting_cash, cash_balance, realized_pnl, exit_nav, unrealized_pnl, position_count). There is no account reader, order API, wallet signer, live-execution client, scheduler, or time-series replay.

## Performance Summary v0 Status

Performance Summary v0 closes the cumulative-history loop. The system already persists three JSONL streams per run (cycle reports via `PaperStrategyCycleLog`, paper trades via `PaperTradeJournal`, NAV snapshots via `PaperNavLog`). Stage 5 added a reader only for paper trades; Stage 6 adds readers for the other two plus a pure performance-summary aggregator so the user can see cumulative system performance over time (cycles run, markets scanned, candidates ready, paper trades executed, realized P&L, last NAV, time span).

The hard part is the reader. Unlike Stage 5's flat `PaperTradeRecord` (no `__post_init__`), `PaperStrategyCycleReport` and `PaperNavSnapshot` have validating `__post_init__` methods that check nested fields via `isinstance` and normalize nested tuples. A shared recursive helper, `json_recovery.from_jsonable(cls, row)`, reconstructs the FULL nested dataclass tree (resolving types via `get_type_hints`, recursing into nested dataclasses, deep-converting list to tuple at every level for `tuple[tuple[str, int], ...]`-style fields, and coercing `Decimal`/`datetime`). Each reader constructs `cls(**reconstructed)` so `__post_init__` re-validates.

The summary is paper-only and report-only: it is a research/audit aggregate, never a trade instruction, investment ranking, recommendation, financial advice, or live-execution signal. `paper_only is True` is hard-enforced on every `PerformanceSummary`.

Phase 1 boundary: read-only data analysis over local typed tuples only. It does not fetch market, order-book, price-history, account, wallet, or credential data; does not authenticate; does not handle private keys or credentials; does not place, submit, sign, send, create, or cancel orders; does not open WebSockets; does not use a trading SDK, broker client, or execution client; does not reconcile exchange accounts; and does not perform compliance/legal/geographic analysis.

Boundary shorthand: paper-only, report-only; local typed-tuple arithmetic only -- no fetch, no auth, no wallet, no order, no rank, no recommend, no financial advice.

## Performance Summary v0 Python API

- Read a strategy-cycle JSONL log back into fully-typed reports with `PaperStrategyCycleLog.read(path)`, a static JSONL reader that reverses `PaperStrategyCycleLog.append`'s serialization via the shared recursive `json_recovery.from_jsonable(PaperStrategyCycleReport, row)` helper. It reconstructs the full nested report tree (including the `PaperProjectScreeningReport` subtree and the deep `tuple[tuple[str, int], ...]` `blocked_counts`) so each report's validating `__post_init__` re-runs. It skips blank lines, raises `ValueError` (with a line number) on non-JSON lines, and returns an empty tuple for an empty file.
- Read a NAV JSONL log back into fully-typed snapshots with `PaperNavLog.read(path)`, a static JSONL reader using the same recursive helper to reconstruct each `PaperPositionMark` (Decimal/datetime/optional fields) so `PaperNavSnapshot.__post_init__` re-validates each snapshot. Same blank-line/empty/non-JSON handling.
- Aggregate the three history streams with `build_performance_summary(cycle_reports, trade_records, nav_snapshots, *, config, generated_at) -> PerformanceSummary`. Pure arithmetic: cycle count, summed scan/snapshot-ready/cost-aware counts, paper-trade count, NAV-snapshot count, the most-recent NAV snapshot's exit NAV / starting cash / cumulative realized P&L, and the min/max cycle `generated_at` span. Empty inputs collapse to zeros and `None`. `PerformanceSummaryConfig` carries only a canonical `config_version` string.
- Print a cumulative summary from the CLI with `polymarket-alpha-lab history --cycle-log <path> --trade-log <path> --nav-log <path>`, which reads the three JSONL logs, builds the summary, and prints cycle/market/candidate/trade/NAV counts plus the time span. There is no account reader, order API, wallet signer, live-execution client, scheduler, or time-series replay.

## Continuous Run v0 Status

Continuous Run v0 adds a synchronous loop orchestrator that chains strategy-cycle (with optional paper execution), cycle-report logging, and portfolio NAV marking, repeating for a configurable number of iterations with an optional sleep interval. Each iteration is wrapped in try/except so one bad cycle never kills the loop (on-cycle-error log-and-continue is the default). This is the operationalization primitive: it manufactures the longitudinal observations (cycles, trades, NAV snapshots) needed for Level 2 promotion gates.

The summary is paper-only and report-only: it is a research/audit aggregate, never a trade instruction, investment ranking, recommendation, financial advice, or live-execution signal. It does not place, submit, sign, or cancel orders; does not authenticate; does not handle wallets, private keys, or credentials; does not read account state; and does not perform compliance/legal/geographic analysis.

Boundary shorthand: paper-only, report-only, no auth, no wallet, no order, no rank, no recommend, no financial advice.

## Continuous Run v0 Python API

- Run a single-shot or repeating loop with `run_strategy_loop(*, client, scan_config, cycle_config, starting_cash, nav_log_path, cycle_report_log_path, repeat_mode="once", interval_seconds=0, max_iterations=1, on_cycle_error="log_and_continue")`, which returns a paper-only/report-only `RunLoopSummary`. Per iteration it (a) calls `run_strategy_cycle`, (b) appends the report to the cycle JSONL log via `PaperStrategyCycleLog`, and (c) when `cycle_config.paper_trade_journal_path` is set and the journal file exists, calls `mark_paper_portfolio_nav`. `starting_cash` must be a positive `Decimal`; `client` is the injected `MarketDataClient` Protocol (this module never imports `api`); `interval_seconds >= 0`; `max_iterations >= 1`.
- First-run journal skip: on the first iteration the paper-trade journal may not exist yet (paper execution default-off, or the cycle produced no screening-ready candidate), and `mark_paper_portfolio_nav` reads the journal via `PaperTradeJournal.read` which raises `FileNotFoundError` on a missing file. The runner pre-checks the path and defensively catches `FileNotFoundError`, skipping the NAV mark and counting it in `RunLoopSummary.nav_marks_skipped`. The iteration still completes (the cycle ran and was logged); the skip is a benign first-run condition, never a cycle failure.
- Isolate per-iteration failures with `on_cycle_error`: `"log_and_continue"` (default) increments `iterations_failed`, records `last_error`, and continues to the next iteration (a failed cycle skips the inter-iteration sleep); `"raise"` propagates the exception immediately. When `repeat_mode="interval"`, `time.sleep(interval_seconds)` runs between iterations only (never after the last, never after a failed one). The loop is synchronous by design (v0); async/scheduler is a later stage.
- Inspect the run with `RunLoopSummary` (frozen): `iterations_completed`, `iterations_failed`, `first_iteration_at`/`last_iteration_at`, `last_error`, `nav_marks_skipped`, with `paper_only is True` / `report_only is True` hard-enforced.
- Run from the CLI with `polymarket-alpha-lab run --starting-cash <Decimal> [--cycle-log <path>] [--nav-log <path>] [--repeat-interval <seconds>] [--max-iterations <n>] [--paper-execute --paper-journal <path>]`, which reuses the strategy-cycle scan/cycle args, maps `--repeat-interval 0` to single-shot, and prints completed/failed/skipped counts plus the time span. There is no account reader, order API, wallet signer, live-execution client, scheduler daemon, or async runtime.

## Outcome Tracker v0 Status

Outcome Tracker v0 (Stage 9) closes the self-judge verification loop. It reads paper-traded markets from the journal, re-lists the CLOSED slice from Gamma, and for each resolved market derives the winning side from `outcomePrices` (the resolved payout array paired with `outcomes`), then builds one `PaperForecastEvidenceObservation` per resolved trade LEG and feeds the forecast-evidence calibration report. This tells the user whether the LLM forecast's probability estimates are actually accurate over time. It is paper-only and report-only: it is a research/audit calibration aggregate, never a trade instruction, investment ranking, recommendation, financial advice, or live-execution signal.

Phase 1 boundary: read-only Gamma `/markets` re-list + pure Decimal computation. It does not place, submit, sign, or cancel orders; does not authenticate; does not handle wallets, private keys, or credentials; does not read account state; and does not perform compliance/legal/geographic analysis. The winning outcome is read from `outcomePrices` on the RAW Gamma payload (NEVER from `resolutionStatus`, which is unreliable); outcome labels are matched case-insensitively through the SAME `YES_NAMES`/`NO_NAMES` alias sets as the cost-aware snapshot builder (never direct string equality); and YES/NO legs are independent calibration points, so one resolved trade record produces exactly one observation (never deduplicated by `condition_id`).

Boundary shorthand: paper-only, report-only, no auth, no wallet, no order, no rank, no recommend, no financial advice.

## Outcome Tracker v0 Python API

- Configure the tracker with `OutcomeTrackingConfig(config_version="outcome-tracker-v1")` (frozen); its nested `forecast_evidence_config` defaults to a synced `PaperForecastEvidenceConfig`.
- Run a check with `check_outcomes(*, client, journal_path, config, generated_at)`, which returns a paper-only/report-only `OutcomeTrackingReport`. `client` is the injected `OutcomeTrackerClient` Protocol (this module never imports `api`; `cli.py` constructs the concrete `PolymarketPublicClient` and injects it). It reads `PaperTradeJournal.read(journal_path)` (a missing journal is treated as zero records — benign first-run condition), lists closed markets via `client.list_markets(active=False, closed=True, limit=500)`, and for each closed market with a parseable `outcomePrices` winner builds one observation (`predicted_probability = research_fair_value_estimate`, `actual_outcome_value = Decimal("1")` if the traded side won else `Decimal("0")`).
- Inspect the result with `OutcomeTrackingReport` (frozen): `generated_at`, `config_version`, `total_markets_checked`, `resolved_count`, `pending_count`, `observations` (tuple of `PaperForecastEvidenceObservation`), and `forecast_evidence_report` (`PaperForecastEvidenceReport | None`, None iff zero observations). Hard-enforced invariants: `resolved_count == len(observations)`, `resolved_count + pending_count == total_markets_checked`, and `paper_only is True` / `report_only is True`.
- Run from the CLI with `polymarket-alpha-lab check-outcomes --journal <path> [--evidence-log <path>]`, which builds the report and prints checked/resolved/pending/observation counts plus the forecast-evidence status. When `--evidence-log` is supplied and at least one observation resolved, the `PaperForecastEvidenceReport` is appended to that JSONL log via `PaperForecastEvidenceLog`. There is no account reader, order API, wallet signer, live-execution client, scheduler daemon, or async runtime.

## Level 2 Node 1 Status

Level 2 Node 1 adds reviewable proposal-packet artifacts over supplied paper-trading, analytics, forecast-evidence, and manual-review artifacts. A proposal packet is for human review only; it is not an approval workflow, trade instruction, order instruction, broker request, strategy-promotion signal, or live-execution signal. No order may leave the system without explicit human approval.

It does not fetch market, order-book, price-history, outcome, or account data; scrape websites; authenticate; handle private keys or credentials; place, submit, sign, or cancel orders; open user WebSockets; run heartbeat logic; use a trading SDK, broker client, or execution client; reconcile exchange accounts; import manual executions; or perform compliance/legal/geographic analysis.

## Level 2 Node 1 Python API

Node 1 is exposed through Python APIs:

- Configure proposal packet limits and boundary text with `TradeProposalPacketConfig(config_version="proposal-v1")`.
- Build proposal packets with `build_trade_proposal_packet(queue_item, side="buy", intended_order_type="limit", maximum_size=Decimal("25"), exposure_after_trade=Decimal("0.1200"), exit_rule="Exit if executable price reaches fair value or thesis invalidates.", reason_trade_could_be_wrong="Liquidity could disappear before exit.", config=config, generated_at=datetime.now(UTC))`, which returns `TradeProposalPacket`.
- Inspect proposal-only review fields with `TradeProposalPacket`.
- Persist proposal packet snapshots with `TradeProposalPacketLog(path).append(packet)`.

## Level 2 Node 2 Status

Level 2 Node 2 adds append-only proposal-review record artifacts over supplied `TradeProposalPacket` values. A proposal-review record captures a reviewer decision, rationale, reviewed packet identity, attestation, and boundary text for audit only; it is not an approval workflow, trade instruction, order instruction, broker request, order request, account action, strategy-promotion signal, or live-execution signal.

It does not fetch market, order-book, price-history, outcome, account, credential, or identity data; scrape websites; authenticate; handle private keys or credentials; place, submit, sign, send, create, or cancel orders; open user WebSockets; run heartbeat logic; use a trading SDK, broker client, execution client, or transport client; build broker or order request payloads; reconcile exchange accounts; import manual executions; or perform compliance/legal/geographic analysis.

## Level 2 Node 2 Python API

Node 2 is exposed through Python APIs:

- Configure proposal-review boundaries with `TradeProposalReviewConfig(config_version="review-v1")`.
- Build proposal-review records with `build_trade_proposal_review_record(packet, decision="approved", reviewer_label="human-reviewer", review_rationale="Reviewed packet fields and supporting evidence.", review_reason_codes=(), human_attestation=config.required_human_attestation, config=config, recorded_at=datetime.now(UTC))`, which returns `TradeProposalReviewRecord`.
- Inspect review-only audit fields with `TradeProposalReviewRecord`.
- Persist proposal-review snapshots with `TradeProposalReviewLog(path).append(record)`.

## Level 2 Node 3 Status

Level 2 Node 3 adds report-only proposal-review summary artifacts over supplied `TradeProposalReviewRecord` values. It tracks review volume, approved/rejected decision counts, rejected reason-code concentration, duplicate source proposal review volume, and market/strategy/risk-tag breakdowns for audit only; it is not an approval workflow, trade instruction, order instruction, broker request, order request, account action, strategy-promotion signal, or live-execution signal.

It does not fetch market, order-book, price-history, outcome, account, credential, or identity data; read external history or JSONL logs; scrape websites; authenticate; handle private keys or credentials; place, submit, sign, send, create, or cancel orders; open user WebSockets; run heartbeat logic; use a trading SDK, broker client, execution client, or transport client; build broker or order request payloads; reconcile exchange accounts; import manual executions; or perform compliance/legal/geographic analysis.

## Level 2 Node 3 Python API

Node 3 is exposed through Python APIs:

- Configure proposal-review summary boundaries with `TradeProposalReviewSummaryConfig(config_version="summary-v1")`.
- Build proposal-review summary reports with `build_trade_proposal_review_summary_report(records, config=config, generated_at=datetime.now(UTC))`, which returns `TradeProposalReviewSummaryReport`.
- Inspect reason-code rows with `TradeProposalReviewReasonCodeSummary` and grouped market/strategy/risk-tag rows with `TradeProposalReviewBucketSummary`.
- Persist proposal-review summary snapshots with `TradeProposalReviewSummaryLog(path).append(report)`.

## Level 2 Node 4 Status

Level 2 Node 4 adds report-only proposal-review quality gate artifacts over supplied `TradeProposalReviewSummaryReport` values. It tracks summary volume, review decision volume, rejection-rate stability, rejected reason-code concentration, and duplicate source proposal review volume for audit only; it is not an approval workflow, trade instruction, order instruction, broker request, order request, account action, strategy-promotion signal, or live-execution signal.

It does not fetch market, order-book, price-history, outcome, account, credential, or identity data; read external history or JSONL logs; scrape websites; authenticate; handle private keys or credentials; place, submit, sign, send, create, or cancel orders; open user WebSockets; run heartbeat logic; use a trading SDK, broker client, execution client, or transport client; build broker or order request payloads; reconcile exchange accounts; import manual executions; or perform compliance/legal/geographic analysis.

## Level 2 Node 4 Python API

Node 4 is exposed through Python APIs:

- Configure proposal-review quality gates with `TradeProposalReviewQualityConfig(config_version="quality-v1")`.
- Build proposal-review quality reports with `build_trade_proposal_review_quality_report(summaries, config=config, generated_at=datetime.now(UTC))`, which returns `TradeProposalReviewQualityReport`.
- Inspect quality gate rows with `TradeProposalReviewQualityGateResult` and rejected reason-code trends with `TradeProposalReviewQualityReasonTrend`.
- Persist proposal-review quality snapshots with `TradeProposalReviewQualityLog(path).append(report)`.

## Level 2 Node 5 Status

Level 2 Node 5 adds report-only proposal-review diagnostic artifacts over supplied `TradeProposalReviewRecord` values. It treats rejected human-review decisions as a proposal-quality investigation proxy only; it does not confirm realized false positives, import outcomes, compare fills, reconcile positions, settle decisions, or route proposals.

It does not fetch market, order-book, price-history, outcome, account, credential, or identity data; read external history or JSONL logs; scrape websites; authenticate; handle private keys or credentials; place, submit, sign, send, create, or cancel orders; open user WebSockets; run heartbeat logic; use a trading SDK, broker client, execution client, or transport client; build broker or order request payloads; reconcile exchange accounts; review settlement; import manual executions; or perform compliance/legal/geographic analysis.

## Level 2 Node 5 Python API

Node 5 is exposed through Python APIs:

- Configure proposal-review diagnostics with `TradeProposalReviewDiagnosticConfig(config_version="diagnostic-v1")`.
- Build proposal-review diagnostic reports with `build_trade_proposal_review_diagnostic_report(records, config=config, generated_at=datetime.now(UTC))`, which returns `TradeProposalReviewDiagnosticReport`.
- Inspect rejected reason-code proxy rows with `TradeProposalReviewDiagnosticReasonRow`, bucket rows with `TradeProposalReviewDiagnosticBucketRow`, and rejected source proposal rows with `TradeProposalReviewDiagnosticSourceRow`.
- Persist proposal-review diagnostic snapshots with `TradeProposalReviewDiagnosticLog(path).append(report)`.

## Level 2 Node 6 Status

Level 2 Node 6 adds report-only proposal-review coverage artifacts over supplied `TradeProposalPacket` and `TradeProposalReviewRecord` values. It treats proposal packets as the coverage denominator and review records as observed review evidence, reporting reviewed, unreviewed, duplicate-reviewed, conflicting-decision, and orphan-review coverage without selecting a winning decision or routing proposals.

It does not fetch market, order-book, price-history, outcome, account, credential, or identity data; read external history or JSONL logs; scrape websites; authenticate; handle private keys or credentials; place, submit, sign, send, create, or cancel orders; open user WebSockets; run heartbeat logic; use a trading SDK, broker client, execution client, or transport client; build broker or order request payloads; reconcile exchange accounts; review settlement; import manual executions; run approval workflows; select latest decisions; or perform compliance/legal/geographic analysis.

## Level 2 Node 6 Python API

Node 6 is exposed through Python APIs:

- Configure proposal-review coverage with `TradeProposalReviewCoverageConfig(config_version="coverage-v1")`.
- Build proposal-review coverage reports with `build_trade_proposal_review_coverage_report(proposals, records, config=config, generated_at=datetime.now(UTC))`, which returns `TradeProposalReviewCoverageReport`.
- Inspect coverage gates with `TradeProposalReviewCoverageGateResult`, bucket rows with `TradeProposalReviewCoverageBucketRow`, and packet rows with `TradeProposalReviewCoveragePacketRow`.
- Persist proposal-review coverage snapshots with `TradeProposalReviewCoverageLog(path).append(report)`.

## Level 2 Node 7 Status

Level 2 Node 7 adds report-only proposal-review dossier artifacts over supplied `TradeProposalReviewSummaryReport`, `TradeProposalReviewQualityReport`, `TradeProposalReviewDiagnosticReport`, and `TradeProposalReviewCoverageReport` values. It assembles review evidence, gaps, gate rows, source rows, and finding rows for audit only; it is not an approval workflow, trade instruction, order instruction, broker request, order request, account action, strategy-promotion signal, or live-execution signal.

It does not fetch market, order-book, price-history, outcome, account, credential, or identity data; read external history or JSONL logs; scrape websites; authenticate; handle private keys or credentials; place, submit, sign, send, create, or cancel orders; open user WebSockets; run heartbeat logic; use a trading SDK, broker client, execution client, or transport client; build broker or order request payloads; reconcile exchange accounts; perform reconciliation; review settlement; import manual executions; run approval workflows; select latest decisions; resolve conflicting reviews; rank investments; recommend trades; or perform compliance/legal/geographic analysis.

## Level 2 Node 7 Python API

Node 7 is exposed through Python APIs:

- Configure proposal-review dossiers with `TradeProposalReviewDossierConfig(config_version="dossier-v1")`.
- Build proposal-review dossier reports with `build_trade_proposal_review_dossier_report(summary=summary, quality=quality, diagnostics=diagnostics, coverage=coverage, config=config, generated_at=datetime.now(UTC))`, which returns `TradeProposalReviewDossierReport`.
- Inspect dossier gates with `TradeProposalReviewDossierGateResult`, source rows with `TradeProposalReviewDossierSourceRow`, and finding rows with `TradeProposalReviewDossierFindingRow`.
- Persist proposal-review dossier snapshots with `TradeProposalReviewDossierLog(path).append(report)`.

## Level 2 Node 8 Status

Level 2 Node 8 adds report-only proposal-review dossier batch health artifacts over supplied `TradeProposalReviewDossierReport` values. It treats supplied dossier reports as caller-provided audit inputs and summarizes dossier counts, status ratios, config-version rows, duplicate dossier fingerprints, finding summaries, source summaries, and gate rows for audit only; it is not an approval workflow, proposal approval step, approved-proposal selector, latest-decision selector, decision-resolution process, investment ranking, trade recommendation, trade instruction, order instruction, broker request, order request, account action, strategy-promotion signal, or live-execution signal.

It does not fetch market, order-book, price-history, outcome, account, credential, or identity data; read external history or JSONL logs; scrape websites; authenticate; handle credentials/private keys; place, submit, sign, send, create, or cancel orders; open user WebSockets; run heartbeat logic; use trading SDK/broker/execution/transport clients; build broker or order request payloads; reconcile exchange accounts; perform reconciliation; review settlement; approve proposals; select latest decisions; resolve conflicting reviews; rank investments; recommend trades; or perform compliance/legal/geographic analysis.

## Level 2 Node 8 Python API

Node 8 is exposed through Python APIs:

- Configure proposal-review dossier batches with `TradeProposalReviewDossierBatchConfig(config_version="dossier-batch-v1")`.
- Build proposal-review dossier batch health reports with `build_trade_proposal_review_dossier_batch_report(dossiers, config=config, generated_at=datetime.now(UTC))`, which returns `TradeProposalReviewDossierBatchReport`.
- Inspect batch gates with `TradeProposalReviewDossierBatchGateResult`, config rows with `TradeProposalReviewDossierBatchConfigVersionSummary`, duplicate rows with `TradeProposalReviewDossierBatchDuplicateSummary`, finding rows with `TradeProposalReviewDossierBatchFindingSummary`, and source rows with `TradeProposalReviewDossierBatchSourceSummary`.
- Persist proposal-review dossier batch snapshots with `TradeProposalReviewDossierBatchLog(path).append(report)`.

## Level 2 Node 9 Status

Level 2 Node 9 adds report-only proposal evidence comparison artifacts over supplied `PaperForecastEvidenceReport` and `TradeProposalReviewDossierBatchReport` values. It compares forecast evidence health and proposal-review dossier batch health for audit only; it is not an approval workflow, proposal approval step, approved-proposal selector, latest-decision selector, decision-resolution process, investment ranking, trade recommendation, strategy-promotion signal, trade instruction, order instruction, broker request, order request, account action, or live-execution signal.

It does not fetch market, order-book, price-history, outcome, account, credential, or identity data; read external history or JSONL logs; scrape websites; authenticate; handle credentials/private keys; place, submit, sign, send, create, or cancel orders; open user WebSockets; run heartbeat logic; use trading SDK/broker/execution/transport clients; build broker or order request payloads; reconcile exchange accounts; perform reconciliation; review settlement; import manual executions; approve proposals; select latest decisions; resolve conflicting reviews; rank investments; recommend trades; or perform compliance/legal/geographic analysis.

## Level 2 Node 9 Python API

Node 9 is exposed through Python APIs:

- Configure evidence comparisons with `TradeProposalEvidenceComparisonConfig(config_version="comparison-v1")`.
- Build evidence comparison reports with `build_trade_proposal_evidence_comparison_report(forecast_evidence=forecast, dossier_batch=batch, config=config, generated_at=datetime.now(UTC))`, which returns `TradeProposalEvidenceComparisonReport`.
- Inspect comparison gates with `TradeProposalEvidenceComparisonGateResult`, source rows with `TradeProposalEvidenceComparisonSourceRow`, metric rows with `TradeProposalEvidenceComparisonMetricRow`, and finding rows with `TradeProposalEvidenceComparisonFindingRow`.
- Persist comparison snapshots with `TradeProposalEvidenceComparisonLog(path).append(report)`.

## Level 2 Node 10 Status

Level 2 Node 10 adds report-only proposal evidence comparison history summaries over caller-supplied, in-memory `TradeProposalEvidenceComparisonReport` values from Node 9. It summarizes comparison statuses, divergence proxy rates, finding-code frequencies, config-version coverage, and source-status transitions for audit only; it is not an approval workflow, proposal approval step, approved-proposal selector, latest-decision selector, decision-resolution process, investment ranking, trade recommendation, strategy-promotion signal, trade instruction, order instruction, broker request, order request, account action, outcome loader, realized false-positive analysis, profitability analysis, compliance surface, geographic surface, or live-execution signal.

It rejects loader-shaped inputs such as paths, mappings, strings, and bytes. It does not fetch market, order-book, price-history, outcome, account, credential, identity, or settlement data; read external history or JSONL logs; provide JSONL readers, loaders, replay, or from-file APIs; scrape websites; use browsers or browser sessions; authenticate; handle wallets, credentials, or private keys; place, submit, sign, send, create, or cancel orders; open user WebSockets; run heartbeat logic; use trading SDK/broker/execution/transport clients; build broker or order request payloads; reconcile exchange accounts; perform reconciliation; review settlement; import manual executions; approve proposals; select latest decisions; resolve conflicting reviews; rank investments; recommend trades; or perform compliance/legal/geographic analysis.

## Level 2 Node 10 Python API

Node 10 is exposed through Python APIs:

- Configure comparison-history reports with `TradeProposalEvidenceComparisonHistoryConfig(config_version="comparison-history-v1")`.
- Build comparison-history reports from supplied, in-memory Node 9 `TradeProposalEvidenceComparisonReport` values with `build_trade_proposal_evidence_comparison_history_report(comparisons, config=config, generated_at=datetime.now(UTC))`, which returns `TradeProposalEvidenceComparisonHistoryReport`.
- Inspect history gates with `TradeProposalEvidenceComparisonHistoryGateResult`, status rows with `TradeProposalEvidenceComparisonHistoryStatusRow`, finding summaries with `TradeProposalEvidenceComparisonHistoryFindingSummary`, config-version summaries with `TradeProposalEvidenceComparisonHistoryConfigVersionSummary`, and source transitions with `TradeProposalEvidenceComparisonHistorySourceTransition`.
- Optionally append already-built comparison-history snapshots with `TradeProposalEvidenceComparisonHistoryLog(path).append(report)`; there is no JSONL reader, loader, replay, or from-file API.

## Level 2 Node 11 Status

Level 2 Node 11 adds report-only proposal evidence comparison history batch health artifacts over supplied `TradeProposalEvidenceComparisonHistoryReport` values. It summarizes history status frequencies, duplicate generated-at indicators, duplicate fingerprint indicators, config-version coverage, finding-code frequencies, source-transition coverage, and append-only JSONL persistence for audit only; it is not an approval workflow, proposal approval step, approved-proposal selector, latest-decision selector, decision-resolution process, investment ranking, trade recommendation, strategy-promotion signal, trade instruction, order instruction, broker request, order request, account action, outcome loader, realized false-positive analysis, profitability analysis, or live-execution signal.

It does not fetch market, order-book, price-history, outcome, account, credential, identity, or settlement data; read external history or JSONL logs; scrape websites; authenticate; handle credentials/private keys; place, submit, sign, send, create, or cancel orders; open user WebSockets; run heartbeat logic; use trading SDK/broker/execution/transport clients; build broker or order request payloads; reconcile exchange accounts; perform reconciliation; review settlement; import manual executions; approve proposals; select latest decisions; resolve conflicting reviews; rank investments; recommend trades; or perform compliance/legal/geographic analysis.

## Level 2 Node 11 Python API

Node 11 is exposed through Python APIs:

- Configure batch-health reports with `TradeProposalEvidenceComparisonHistoryBatchHealthConfig(config_version="history-batch-health-v1")`.
- Build batch-health reports with `build_trade_proposal_evidence_comparison_history_batch_health_report(history_reports, config=config, generated_at=datetime.now(UTC))`, which returns `TradeProposalEvidenceComparisonHistoryBatchHealthReport`.
- Inspect batch-health gates with `TradeProposalEvidenceComparisonHistoryBatchHealthGateResult`, status rows with `TradeProposalEvidenceComparisonHistoryBatchHealthStatusRow`, config-version summaries with `TradeProposalEvidenceComparisonHistoryBatchHealthConfigVersionSummary`, duplicate-generated-at summaries with `TradeProposalEvidenceComparisonHistoryBatchHealthDuplicateGeneratedAtSummary`, duplicate-fingerprint summaries with `TradeProposalEvidenceComparisonHistoryBatchHealthDuplicateFingerprintSummary`, finding summaries with `TradeProposalEvidenceComparisonHistoryBatchHealthFindingSummary`, and source-transition summaries with `TradeProposalEvidenceComparisonHistoryBatchHealthSourceTransitionSummary`.
- Persist batch-health snapshots with `TradeProposalEvidenceComparisonHistoryBatchHealthLog(path).append(report)`.

## Level 2 Node 12 Status

Level 2 Node 12 adds report-only proposal evidence comparison history batch-health trend artifacts over supplied `TradeProposalEvidenceComparisonHistoryBatchHealthReport` values. It summarizes batch-health status frequencies, gate-status frequencies, config-version coverage, duplicate generated-at indicators, duplicate fingerprint indicators, and first/last report time bounds for audit only, and it supports append-only JSONL persistence; it is not an approval workflow, proposal approval step, approved-proposal selector, latest-decision selector, decision-resolution process, investment ranking, trade recommendation, strategy-promotion signal, trade instruction, order instruction, broker request, order request, account action, outcome loader, realized false-positive analysis, profitability analysis, automatic order-placement authorization, or live-execution signal.

It rejects loader-shaped inputs such as paths, mappings, strings, bytes, generators, arbitrary iterables, and log-shaped objects. It does not fetch market, order-book, price-history, outcome, account, credential, identity, or settlement data; read external history or JSONL logs; provide JSONL readers, loaders, replay, or from-file APIs; scrape websites; use browsers or browser sessions; authenticate; handle wallets, credentials/private keys; place, submit, sign, send, create, or cancel orders; open user WebSockets; run heartbeat logic; use trading SDK/broker/execution/transport clients; build broker or order request payloads; reconcile exchange accounts; perform reconciliation; review settlement; import manual executions; approve proposals; select latest decisions; resolve conflicting reviews; rank investments; recommend trades; or perform compliance/legal/geographic analysis.

## Level 2 Node 12 Python API

Node 12 is exposed through Python APIs:

- Configure batch-health trend reports with `TradeProposalEvidenceComparisonHistoryBatchHealthTrendConfig(config_version="batch-health-trend-v1")`.
- Build batch-health trend reports from supplied, in-memory Node 11 `TradeProposalEvidenceComparisonHistoryBatchHealthReport` values with `build_trade_proposal_evidence_comparison_history_batch_health_trend_report(batch_health_reports, config=config, generated_at=datetime.now(UTC))`, which returns `TradeProposalEvidenceComparisonHistoryBatchHealthTrendReport`.
- Inspect trend gates with `TradeProposalEvidenceComparisonHistoryBatchHealthTrendGateResult`, status rows with `TradeProposalEvidenceComparisonHistoryBatchHealthTrendStatusRow`, config-version summaries with `TradeProposalEvidenceComparisonHistoryBatchHealthTrendConfigVersionSummary`, gate-status summaries with `TradeProposalEvidenceComparisonHistoryBatchHealthTrendGateStatusSummary`, duplicate-generated-at summaries with `TradeProposalEvidenceComparisonHistoryBatchHealthTrendDuplicateGeneratedAtSummary`, and duplicate-fingerprint summaries with `TradeProposalEvidenceComparisonHistoryBatchHealthTrendDuplicateFingerprintSummary`.
- Optionally append already-built batch-health trend snapshots with `TradeProposalEvidenceComparisonHistoryBatchHealthTrendLog(path).append(report)`; there is no JSONL reader, loader, replay, or from-file API.

## Level 2 Node 13 Status

Level 2 Node 13 adds report-only proposal evidence comparison history batch-health trend-batch artifacts over supplied `TradeProposalEvidenceComparisonHistoryBatchHealthTrendReport` values. It summarizes trend status frequencies, gate status frequencies, config-version coverage, duplicate generated-at indicators, duplicate fingerprint indicators, and first/last trend-report time bounds for audit only, and it supports append-only JSONL persistence. This is no-read, no-fetch, no-outcome, no-settlement, no-ranking, no-recommendation, no-approval, and no-execution scope; it is not an approval workflow, proposal approval step, approved-proposal selector, latest-decision selector, decision-resolution process, investment ranking, trade recommendation, strategy-promotion signal, trade instruction, order instruction, broker request, order request, account action, credential workflow, external-history loader, JSONL reader, scraping workflow, outcome loader, settlement review, reconciliation process, compliance/legal/geographic analysis, realized false-positive analysis, profitability analysis, automatic order-placement authorization, or live-execution signal.

It rejects loader-shaped inputs such as paths, mappings, strings, bytes, generators, arbitrary iterables, and log-shaped objects. It does not fetch data; read logs; scrape; authenticate; handle credentials/private keys; place or cancel orders; open WebSockets; run heartbeat logic; use trading SDK/broker/execution clients; build request payloads; approve proposals; select latest decisions; resolve conflicts; rank investments; recommend trades; perform outcome/settlement/reconciliation/profitability analysis; import manual executions; or perform compliance/legal/geographic analysis.

## Level 2 Node 13 Python API

Node 13 is exposed through Python APIs:

- Configure trend-batch reports with `TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchConfig(config_version="batch-health-trend-batch-v1")`.
- Build trend-batch reports from supplied, in-memory Node 12 `TradeProposalEvidenceComparisonHistoryBatchHealthTrendReport` values with `build_trade_proposal_evidence_comparison_history_batch_health_trend_batch_report(trend_reports, config=config, generated_at=datetime.now(UTC))`, which returns `TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchReport`.
- Inspect trend-batch gates with `TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchGateResult`, status rows with `TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchStatusRow`, config-version summaries with `TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchConfigVersionSummary`, gate-status summaries with `TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchGateStatusSummary`, duplicate-generated-at summaries with `TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchDuplicateGeneratedAtSummary`, and duplicate-fingerprint summaries with `TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchDuplicateFingerprintSummary`.
- Optionally append already-built trend-batch snapshots with `TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchLog(path).append(report)`; there is no JSONL reader, loader, replay, or from-file API.

## Level 2 Node 14 Status

Level 2 Node 14 adds report-only proposal evidence comparison history batch-health trend-batch health artifacts over supplied `TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchReport` values. It summarizes trend-batch status frequencies, Node 13 gate-status frequencies, config-version coverage, duplicate generated-at indicators, duplicate fingerprint indicators, and first/last trend-batch report time bounds for audit only, and it supports append-only JSONL persistence. This is no-read, no-fetch, no-outcome, no-settlement, no-ranking, no-recommendation, no-approval, and no-execution scope; it is not an approval workflow, proposal approval step, approved-proposal selector, latest-decision selector, decision-resolution process, investment ranking, trade recommendation, strategy-promotion signal, trade instruction, order instruction, broker request, order request, account action, credential workflow, external-history loader, JSONL reader, scraping workflow, outcome loader, settlement review, reconciliation process, compliance/legal/geographic analysis, realized false-positive analysis, profitability analysis, automatic order-placement authorization, or live-execution signal.

It rejects loader-shaped inputs such as paths, mappings, strings, bytes, generators, arbitrary iterables, and log-shaped objects. It does not fetch data; read logs; scrape; authenticate; handle credentials/private keys; place or cancel orders; open WebSockets; run heartbeat logic; use trading SDK/broker/execution clients; build request payloads; approve proposals; select latest decisions; resolve conflicts; rank investments; recommend trades; perform outcome/settlement/reconciliation/profitability analysis; import manual executions; or perform compliance/legal/geographic analysis.

## Level 2 Node 14 Python API

Node 14 is exposed through Python APIs:

- Configure trend-batch health reports with `TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthConfig(config_version="batch-health-trend-batch-health-v1")`.
- Build trend-batch health reports from supplied, in-memory Node 13 `TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchReport` values with `build_trade_proposal_evidence_comparison_history_batch_health_trend_batch_health_report(trend_batch_reports, config=config, generated_at=datetime.now(UTC))`, which returns `TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthReport`.
- Inspect trend-batch health gates with `TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthGateResult`, status rows with `TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthStatusRow`, config-version summaries with `TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthConfigVersionSummary`, gate-status summaries with `TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthGateStatusSummary`, duplicate-generated-at summaries with `TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthDuplicateGeneratedAtSummary`, and duplicate-fingerprint summaries with `TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthDuplicateFingerprintSummary`.
- Optionally append already-built trend-batch health snapshots with `TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthLog(path).append(report)`; there is no JSONL reader, loader, replay, or from-file API.

## Level 2 Node 15 Status

Level 2 Node 15 adds report-only proposal evidence comparison history batch-health trend-batch health trend artifacts over supplied `TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthReport` values. It summarizes trend-batch health status frequencies, Node 14 gate-status frequencies, config-version coverage, duplicate generated-at indicators, duplicate fingerprint indicators, and first/last trend-batch health report time bounds for audit only, and it supports append-only JSONL persistence. This is no-read, no-fetch, no-scrape, no-browser automation, no-account automation, no-API clients, no-outcome, no-settlement, no-reconciliation, no-ranking, no-recommendation, no-financial advice, no-approval, no-execution, no-order placement, no-JSONL readers, and no-external loaders scope; it is not an approval workflow, proposal approval step, approved-proposal selector, latest-decision selector, decision-resolution process, investment ranking, trade recommendation, strategy-promotion signal, trade instruction, order instruction, broker request, order request, account action, credential workflow, private-key handling, external-history loader, JSONL reader, scraping workflow, outcome loader, settlement review, reconciliation process, compliance/legal/geographic analysis, realized false-positive analysis, profitability analysis, automatic order-placement authorization, or live-execution signal.

It rejects loader-shaped inputs such as paths, mappings, strings, bytes, generators, arbitrary iterables, and log-shaped objects. It does not fetch data; read logs; scrape; use browser automation; use account automation; authenticate; handle credentials/private keys; place or cancel orders; open WebSockets; run heartbeat logic; use trading SDK/broker/execution clients; build request payloads; approve proposals; select latest decisions; resolve conflicts; rank investments; recommend trades; perform outcome/settlement/reconciliation/profitability analysis; import manual executions; or perform compliance/legal/geographic analysis.

## Level 2 Node 15 Python API

Node 15 is exposed through Python APIs:

- Configure trend-batch health trend reports with `TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthTrendConfig(config_version="batch-health-trend-batch-health-trend-v1")`.
- Build trend-batch health trend reports from supplied, in-memory Node 14 `TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthReport` values with `build_trade_proposal_evidence_comparison_history_batch_health_trend_batch_health_trend_report(trend_batch_health_reports, config=config, generated_at=datetime.now(UTC))`, which returns `TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthTrendReport`.
- Inspect trend-batch health trend gates with `TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthTrendGateResult`, status rows with `TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthTrendStatusRow`, config-version summaries with `TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthTrendConfigVersionSummary`, gate-status summaries with `TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthTrendGateStatusSummary`, duplicate-generated-at summaries with `TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthTrendDuplicateGeneratedAtSummary`, and duplicate-fingerprint summaries with `TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthTrendDuplicateFingerprintSummary`.
- Optionally append already-built trend-batch health trend snapshots with `TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthTrendLog(path).append(report)`; there is no JSONL reader, loader, replay, or from-file API.

## Proposal Evidence Comparison Artifact Registry

The proposal evidence comparison artifact registry is a static report-only registry with string metadata only. It describes the existing proposal evidence comparison artifact chain, builder names, report class names, upstream report class names, append-only-log availability, and report-only forbidden surfaces. It does not import artifact implementation modules and does not create reports.

The registry does not fetch, does not read JSONL, does not load, does not replay, does not scrape, does not use browser automation, does not use account automation, does not use API clients, does not place orders, does not rank investments, does not recommend trades, and does not provide financial advice.

Use `list_proposal_evidence_comparison_artifacts()` to inspect the static tuple and `get_proposal_evidence_comparison_artifact(artifact_id)` to look up one registry row by canonical artifact ID.

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
│       │   ├── 2026-06-13-level-1b-paper-forecast-evidence.md
│       │   ├── 2026-06-13-level-1b-paper-analytics-history-validation.md
│       │   ├── 2026-06-13-level-1b-rejections-risk-gates.md
│       │   ├── 2026-06-13-level-1b-positions-nav.md
│       │   ├── 2026-06-14-level-1b-paper-manual-review-queue.md
│       │   ├── 2026-06-14-level-2-proposal-packets.md
│       │   ├── 2026-06-15-level-2-proposal-evidence-comparison.md
│       │   ├── 2026-06-15-level-2-proposal-evidence-comparison-history.md
│       │   ├── 2026-06-15-level-2-proposal-evidence-comparison-history-batch-health.md
│       │   ├── 2026-06-15-level-2-proposal-evidence-comparison-history-batch-health-trend.md
│       │   ├── 2026-06-15-level-2-proposal-evidence-comparison-history-batch-health-trend-batch.md
│       │   ├── 2026-06-15-level-2-proposal-evidence-comparison-history-batch-health-trend-batch-health.md
│       │   ├── 2026-06-15-level-2-proposal-evidence-comparison-history-batch-health-trend-batch-health-trend.md
│       │   ├── 2026-06-15-level-2-proposal-review-coverage.md
│       │   ├── 2026-06-15-level-2-proposal-review-dossier-batch-health.md
│       │   ├── 2026-06-15-level-2-proposal-review-dossier.md
│       │   ├── 2026-06-14-level-2-proposal-review-diagnostics.md
│       │   ├── 2026-06-14-level-2-proposal-review-records.md
│       │   ├── 2026-06-14-level-2-proposal-review-quality-gates.md
│       │   ├── 2026-06-14-level-2-proposal-review-summary-reports.md
│       │   ├── 2026-06-16-cost-aware-event-strategy-v0.md
│       │   ├── 2026-06-16-project-screening-v0.md
│       │   └── 2026-06-13-project-bootstrap.md
│       └── specs
│           ├── 2026-06-13-automated-investment-roadmap.md
│           ├── 2026-06-16-cost-aware-event-strategy-v0.md
│           ├── 2026-06-16-project-screening-v0.md
│           └── 2026-06-13-polymarket-alpha-lab-design.md
├── pyproject.toml
├── src
│   └── polymarket_alpha_lab
│       ├── __init__.py
│       ├── analytics.py
│       ├── analytics_history.py
│       ├── api.py
│       ├── archive.py
│       ├── cli.py
│       ├── cost_aware_event_strategy.py
│       ├── domain.py
│       ├── forecast_evidence.py
│       ├── journal.py
│       ├── manual_review_queue.py
│       ├── normalize.py
│       ├── paper.py
│       ├── pipeline.py
│       ├── positions.py
│       ├── project_screening.py
│       ├── proposal_evidence_comparison.py
│       ├── proposal_evidence_comparison_history.py
│       ├── proposal_evidence_comparison_history_batch_health.py
│       ├── proposal_evidence_comparison_history_batch_health_trend.py
│       ├── proposal_evidence_comparison_history_batch_health_trend_batch.py
│       ├── proposal_evidence_comparison_history_batch_health_trend_batch_health.py
│       ├── proposal_evidence_comparison_history_batch_health_trend_batch_health_trend.py
│       ├── proposal_packet.py
│       ├── proposal_review.py
│       ├── proposal_review_coverage.py
│       ├── proposal_review_dossier_batch.py
│       ├── proposal_review_dossier.py
│       ├── proposal_review_diagnostics.py
│       ├── proposal_review_quality.py
│       ├── proposal_review_summary.py
│       ├── rejections.py
│       ├── research.py
│       ├── risk.py
│       └── scoring.py
└── tests
    ├── test_analytics.py
    ├── test_analytics_history.py
    ├── test_analytics_history_scope.py
    ├── test_analytics_scope.py
    ├── test_api.py
    ├── test_archive.py
    ├── test_cli.py
    ├── test_cost_aware_event_strategy.py
    ├── test_cost_aware_event_strategy_scope.py
    ├── test_domain.py
    ├── test_forecast_evidence.py
    ├── test_forecast_evidence_scope.py
    ├── test_init.py
    ├── test_journal.py
    ├── test_manual_review_queue.py
    ├── test_manual_review_queue_scope.py
    ├── test_normalize.py
    ├── test_paper.py
    ├── test_pipeline.py
    ├── test_positions.py
    ├── test_project_screening.py
    ├── test_project_screening_scope.py
    ├── test_proposal_evidence_comparison.py
    ├── test_proposal_evidence_comparison_scope.py
    ├── test_proposal_evidence_comparison_history.py
    ├── test_proposal_evidence_comparison_history_scope.py
    ├── test_proposal_evidence_comparison_history_batch_health.py
    ├── test_proposal_evidence_comparison_history_batch_health_scope.py
    ├── test_proposal_evidence_comparison_history_batch_health_trend.py
    ├── test_proposal_evidence_comparison_history_batch_health_trend_scope.py
    ├── test_proposal_evidence_comparison_history_batch_health_trend_batch.py
    ├── test_proposal_evidence_comparison_history_batch_health_trend_batch_scope.py
    ├── test_proposal_evidence_comparison_history_batch_health_trend_batch_health.py
    ├── test_proposal_evidence_comparison_history_batch_health_trend_batch_health_scope.py
    ├── test_proposal_evidence_comparison_history_batch_health_trend_batch_health_trend.py
    ├── test_proposal_evidence_comparison_history_batch_health_trend_batch_health_trend_scope.py
    ├── test_proposal_packet.py
    ├── test_proposal_packet_scope.py
    ├── test_proposal_review.py
    ├── test_proposal_review_coverage.py
    ├── test_proposal_review_coverage_scope.py
    ├── test_proposal_review_dossier_batch.py
    ├── test_proposal_review_dossier_batch_scope.py
    ├── test_proposal_review_dossier.py
    ├── test_proposal_review_dossier_scope.py
    ├── test_proposal_review_diagnostics.py
    ├── test_proposal_review_diagnostics_scope.py
    ├── test_proposal_review_quality.py
    ├── test_proposal_review_quality_scope.py
    ├── test_proposal_review_summary.py
    ├── test_proposal_review_summary_scope.py
    ├── test_proposal_review_scope.py
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
