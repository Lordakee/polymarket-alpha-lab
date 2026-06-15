# Polymarket Alpha Lab

Polymarket Alpha Lab is a research-first project for finding, scoring, and validating Polymarket markets before any capital is committed.

The long-term goal is an automated system that can screen markets, research candidates, propose trades, and eventually execute only after validation gates and risk controls have been proven. The first version is intentionally not a trading bot. It is a planning and research workspace for:

- market discovery and metadata normalization
- order book and liquidity quality scoring
- strategy research around measurable edges
- paper-trading journals, risk gates, and rejection review
- future backtesting and signal validation

## Phase 1 Scope

This repository currently contains the project design, research notes, implementation plans, a read-only market scanner, research packet assembly, bid/ask paper-fill simulation, JSONL paper-trade journaling, paper-only risk gates, rejected-candidate logs, paper position ledgers, executable NAV marks, paper-only portfolio analytics, exposure reports, executable-NAV drawdown reports, paper-only analytics history validation, paper-only forecast evidence reports, paper-only manual-review queues, human-review proposal packet artifacts, append-only proposal-review record artifacts, proposal-review summary report artifacts, proposal-review quality gate artifacts, proposal-review diagnostic artifacts, proposal-review coverage report artifacts, proposal-review dossier artifacts, proposal-review dossier batch health artifacts, proposal evidence comparison artifacts, proposal evidence comparison history artifacts, proposal evidence comparison history batch-health artifacts, proposal evidence comparison history batch-health trend artifacts, and proposal evidence comparison history batch-health trend-batch artifacts.

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
│       │   ├── 2026-06-15-level-2-proposal-review-coverage.md
│       │   ├── 2026-06-15-level-2-proposal-review-dossier-batch-health.md
│       │   ├── 2026-06-15-level-2-proposal-review-dossier.md
│       │   ├── 2026-06-14-level-2-proposal-review-diagnostics.md
│       │   ├── 2026-06-14-level-2-proposal-review-records.md
│       │   ├── 2026-06-14-level-2-proposal-review-quality-gates.md
│       │   ├── 2026-06-14-level-2-proposal-review-summary-reports.md
│       │   └── 2026-06-13-project-bootstrap.md
│       └── specs
│           ├── 2026-06-13-automated-investment-roadmap.md
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
│       ├── domain.py
│       ├── forecast_evidence.py
│       ├── journal.py
│       ├── manual_review_queue.py
│       ├── normalize.py
│       ├── paper.py
│       ├── pipeline.py
│       ├── positions.py
│       ├── proposal_evidence_comparison.py
│       ├── proposal_evidence_comparison_history.py
│       ├── proposal_evidence_comparison_history_batch_health.py
│       ├── proposal_evidence_comparison_history_batch_health_trend.py
│       ├── proposal_evidence_comparison_history_batch_health_trend_batch.py
│       ├── proposal_evidence_comparison_history_batch_health_trend_batch_health.py
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
