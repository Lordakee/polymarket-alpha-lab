"""Paper-only live-layer strategy cycle orchestrator (Stage 1b).

This is the first live-layer orchestrator. It runs a self-contained, read-only
scan (approach b2): fetch the public Gamma market list, normalize each market,
optionally rank by the deterministic Level 0 scorer, truncate to a per-cycle
budget, then evaluate each binary market through the frozen Stage 1a leaves
(naive forecast + cost-aware snapshot builder) and the cost-aware event
strategy, finally aggregating into a deterministic project-screening research
queue.

The orchestrator performs live network reads but its OUTPUT
``PaperStrategyCycleReport`` is paper-only/report-only: it is a research audit
envelope, never a trade instruction. ``paper_only is True`` /
``report_only is True`` are hard-enforced on the report with ``is``.

Protocol-only (Q5): this module does NOT import ``api``. It depends on a local
``MarketDataClient`` Protocol; ``cli.py`` constructs the concrete
``PolymarketPublicClient`` and injects it. This sets a tighter live-layer
precedent than ``pipeline.py``.

Per-market isolation is mandatory: every market's fetch/normalize/snapshot path
is wrapped in ``try/except``. A single bad market is recorded as a
``blocked_fetch_error`` cycle-layer status (or the snapshot builder's own
``blocked_*`` status) and the cycle continues.

Phase 1 boundary: read-only Gamma ``/markets`` and CLOB ``/book`` fetches only.
No orders, auth, wallets, private keys, credentials, relayers, account/position
reads, or exchange writes.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any, Callable, Protocol, runtime_checkable

from polymarket_alpha_lab.archive import RawArchive
from polymarket_alpha_lab.book_imbalance_forecast import (
    PaperBookImbalanceForecastConfig,
    build_paper_book_imbalance_forecast,
)
# Stage 8 (additive/default-off): the LLM forecast provider routes through a
# caller-supplied read-only probability-model transport (Zhipu GLM via stdlib
# urllib, same research-fetch class as api.py) and the pure transform leaf.
# ``llm_research_transport`` is permitted in this scope contract because the
# read-only GLM estimate IS the cycle's Stage 8 job (analogous to how Stage 4
# permitted ``journal``/``paper_execution``).
from polymarket_alpha_lab.llm_forecast import (
    PaperLLMForecastConfig,
    build_paper_llm_forecast,
)
from polymarket_alpha_lab.llm_research_transport import GLMChatTransport
from polymarket_alpha_lab.cost_aware_event_strategy import (
    PaperCostAwareEventCostAssumptions,
    PaperCostAwareEventStrategyConfig,
    PaperCostAwareEventStrategyReport,
    build_paper_cost_aware_event_strategy_report,
)
from polymarket_alpha_lab.cost_aware_snapshot_builder import (
    PaperCostAwareSnapshotConfig,
    build_paper_cost_aware_event_market_snapshot,
)
from polymarket_alpha_lab.domain import NormalizedMarket
from polymarket_alpha_lab.forecast_provider import (
    PaperForecastConfig,
    build_paper_naive_forecast,
)
from polymarket_alpha_lab.json_recovery import from_jsonable
from polymarket_alpha_lab.normalize import normalize_gamma_market, normalize_order_book
from polymarket_alpha_lab.paper_execution import (
    PaperExecutionConfig,
    execute_paper_trade_from_screening,
)
from polymarket_alpha_lab.pipeline import MarketScanConfig
from polymarket_alpha_lab.project_screening import (
    PaperProjectScreeningConfig,
    PaperProjectScreeningReport,
    build_paper_project_screening_report,
)
from polymarket_alpha_lab.scoring import score_market


__all__ = (
    "PaperStrategyCycleConfig",
    "PaperStrategyCycleReport",
    "PaperStrategyCycleLog",
    "run_strategy_cycle",
)


ZERO = Decimal("0")

# Mirrors cost_aware_snapshot_builder.YES_NAMES / NO_NAMES verbatim. The cycle
# must resolve YES/NO tokens the SAME way the snapshot builder does, otherwise
# every market would hit blocked_book_token_mismatch.
YES_NAMES = {"yes", "true", "long"}
NO_NAMES = {"no", "false", "short"}


@runtime_checkable
class MarketDataClient(Protocol):
    """Read-only public market-data surface (Protocol-only; Q5).

    The concrete client (a Gamma + CLOB reader) is constructed in ``cli.py``
    and injected into ``run_strategy_cycle``. This module never imports ``api``.
    """

    def list_markets(self, *, active: bool, closed: bool, limit: int, search: str | None = None) -> Any:
        """Return the raw public Gamma market list payload."""

    def get_order_book(self, *, token_id: str) -> Any:
        """Return the raw public CLOB order book payload for one token id."""


@dataclass(frozen=True)
class PaperStrategyCycleConfig:
    config_version: str
    forecast_config: PaperForecastConfig
    snapshot_config: PaperCostAwareSnapshotConfig
    strategy_config: PaperCostAwareEventStrategyConfig
    screening_config: PaperProjectScreeningConfig
    cost_assumptions: PaperCostAwareEventCostAssumptions
    max_markets_per_cycle: int = 50
    prefilter_by_score: bool = True
    forecast_provider: str = "naive"
    book_imbalance_config: PaperBookImbalanceForecastConfig | None = None
    # Stage 8 (additive/default-off): when forecast_provider == "llm" the cycle
    # routes each binary market through a caller-supplied read-only
    # probability-model transport and the pure LLM forecast leaf. Both must be
    # supplied together when the dispatch selects "llm"; default None keeps
    # Stage 1b/2/3/4 behavior unchanged.
    llm_transport: GLMChatTransport | None = None
    llm_forecast_config: PaperLLMForecastConfig | None = None
    # Stage 4 (additive/default-off): when paper_execution_config is set,
    # run_strategy_cycle runs an inline paper-execution pass after screening.
    # Records must flow to an injected durable DB sink. The journal path remains
    # a legacy read/export setting for downstream compatibility; it is not a
    # valid paper-execution write sink.
    paper_execution_config: PaperExecutionConfig | None = None
    paper_trade_journal_path: Path | None = None
    market_search: str | None = None

    def __post_init__(self) -> None:
        _require_canonical_string("config_version", self.config_version)
        _require_config_instance(
            "forecast_config",
            self.forecast_config,
            PaperForecastConfig,
        )
        _require_config_instance(
            "snapshot_config",
            self.snapshot_config,
            PaperCostAwareSnapshotConfig,
        )
        _require_config_instance(
            "strategy_config",
            self.strategy_config,
            PaperCostAwareEventStrategyConfig,
        )
        _require_config_instance(
            "screening_config",
            self.screening_config,
            PaperProjectScreeningConfig,
        )
        _require_config_instance(
            "cost_assumptions",
            self.cost_assumptions,
            PaperCostAwareEventCostAssumptions,
        )
        _require_positive_int("max_markets_per_cycle", self.max_markets_per_cycle)
        if not isinstance(self.prefilter_by_score, bool):
            raise ValueError("prefilter_by_score must be a bool")
        _require_canonical_string("forecast_provider", self.forecast_provider)
        if self.forecast_provider not in ("naive", "book_imbalance", "llm"):
            raise ValueError(
                "forecast_provider must be one of "
                "('naive', 'book_imbalance', 'llm')",
            )
        if self.book_imbalance_config is not None and not isinstance(
            self.book_imbalance_config,
            PaperBookImbalanceForecastConfig,
        ):
            raise ValueError(
                "book_imbalance_config must be a "
                "PaperBookImbalanceForecastConfig",
            )
        # C1 fix: run_strategy_cycle dereferences book_imbalance_config without a
        # None guard, so it must be supplied when the dispatch selects that provider.
        if (
            self.forecast_provider == "book_imbalance"
            and self.book_imbalance_config is None
        ):
            raise ValueError(
                "book_imbalance_config is required when "
                "forecast_provider == 'book_imbalance'",
            )
        if self.llm_transport is not None and not isinstance(
            self.llm_transport,
            GLMChatTransport,
        ):
            raise ValueError("llm_transport must be a GLMChatTransport")
        if self.llm_forecast_config is not None and not isinstance(
            self.llm_forecast_config,
            PaperLLMForecastConfig,
        ):
            raise ValueError(
                "llm_forecast_config must be a PaperLLMForecastConfig",
            )
        # C1 fix (Stage 8): run_strategy_cycle dereferences llm_transport and
        # llm_forecast_config in the dispatch branch, so both must be supplied
        # when forecast_provider selects "llm".
        if (
            self.forecast_provider == "llm"
            and (self.llm_transport is None or self.llm_forecast_config is None)
        ):
            raise ValueError(
                "llm_transport and llm_forecast_config are required when "
                "forecast_provider == 'llm'",
            )
        if self.paper_execution_config is not None and not isinstance(
            self.paper_execution_config,
            PaperExecutionConfig,
        ):
            raise ValueError(
                "paper_execution_config must be a PaperExecutionConfig",
            )
        if self.paper_trade_journal_path is not None:
            if self.paper_execution_config is None:
                raise ValueError(
                    "paper_trade_journal_path requires paper_execution_config",
                )
            if not isinstance(
                self.paper_trade_journal_path,
                Path,
            ):
                raise ValueError("paper_trade_journal_path must be a Path")


@dataclass(frozen=True)
class PaperStrategyCycleReport:
    generated_at: datetime
    config_version: str
    scan_market_count: int
    considered_count: int
    snapshot_ready_count: int
    cost_aware_report_count: int
    blocked_counts: tuple[tuple[str, int], ...]
    screening_report: PaperProjectScreeningReport | None
    cost_aware_reports: tuple[PaperCostAwareEventStrategyReport, ...] = ()
    paper_only: bool = True
    report_only: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc(self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        for field_name in (
            "scan_market_count",
            "considered_count",
            "snapshot_ready_count",
            "cost_aware_report_count",
        ):
            _require_nonnegative_int(field_name, getattr(self, field_name))
        object.__setattr__(
            self,
            "blocked_counts",
            _normalize_blocked_counts(self.blocked_counts),
        )
        object.__setattr__(
            self,
            "cost_aware_reports",
            _normalize_cost_aware_reports(self.cost_aware_reports),
        )
        if self.screening_report is not None and not isinstance(
            self.screening_report,
            PaperProjectScreeningReport,
        ):
            raise ValueError(
                "screening_report must be a PaperProjectScreeningReport or None",
            )
        # Count invariants (spec Validation rules).
        if self.snapshot_ready_count > self.considered_count:
            raise ValueError(
                "snapshot_ready_count must be <= considered_count",
            )
        if self.considered_count > self.scan_market_count:
            raise ValueError(
                "considered_count must be <= scan_market_count",
            )
        if self.cost_aware_report_count != self.snapshot_ready_count:
            raise ValueError(
                "cost_aware_report_count must equal snapshot_ready_count",
            )
        if (
            self.cost_aware_reports
            and self.cost_aware_report_count != len(self.cost_aware_reports)
        ):
            raise ValueError(
                "cost_aware_report_count must equal len(cost_aware_reports)",
            )
        if (self.screening_report is None) != (self.cost_aware_report_count == 0):
            raise ValueError(
                "screening_report must be None if and only if "
                "cost_aware_report_count is zero",
            )
        blocked_total = sum(count for _status, count in self.blocked_counts)
        if blocked_total + self.snapshot_ready_count != self.considered_count:
            raise ValueError(
                "blocked_counts plus snapshot_ready_count must equal "
                "considered_count",
            )
        if self.paper_only is not True:
            raise ValueError("paper_only must be True")
        if self.report_only is not True:
            raise ValueError("report_only must be True")


@dataclass(frozen=True)
class PaperStrategyCycleLog:
    path: Path | str

    def __post_init__(self) -> None:
        object.__setattr__(self, "path", _normalize_log_path(self.path))

    def append(self, report: PaperStrategyCycleReport) -> None:
        if not isinstance(report, PaperStrategyCycleReport):
            raise ValueError("report must be a PaperStrategyCycleReport")
        _validate_report_tree(report)
        line = (
            json.dumps(
                _json_ready(asdict(report)),
                allow_nan=False,
                sort_keys=True,
            )
            + "\n"
        )
        path = _normalize_log_path(self.path)
        _validate_log_parent(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as handle:
            handle.write(line)

    @staticmethod
    def read(path: Path | str) -> tuple[PaperStrategyCycleReport, ...]:
        """Read a strategy-cycle JSONL log back into fully-typed reports.

        Reverses ``append``'s ``_json_ready(asdict(...))`` serialization using
        the shared recursive ``json_recovery.from_jsonable`` helper. Unlike
        Stage 5's flat ``PaperTradeRecord`` reader, ``PaperStrategyCycleReport``
        has a validating ``__post_init__`` that checks the nested
        ``screening_report`` via ``isinstance`` and normalizes
        ``blocked_counts: tuple[tuple[str, int], ...]`` -- a flat coercion would
        raise on every report with a populated screening tree or blocked
        markets. ``from_jsonable`` reconstructs the FULL nested dataclass tree
        (including the PaperProjectScreeningReport subtree and the C2 deep
        tuple-of-tuples) so ``__post_init__`` re-validates each report. Blank
        lines are skipped; a non-JSON line raises ``ValueError`` with the line
        number. An empty file yields an empty tuple.
        """
        target = Path(path)
        records: list[PaperStrategyCycleReport] = []
        with target.open("r", encoding="utf-8") as handle:
            for line_number, raw_line in enumerate(handle, start=1):
                stripped = raw_line.strip()
                if not stripped:
                    continue
                try:
                    row = json.loads(stripped)
                except json.JSONDecodeError as exc:
                    raise ValueError(
                        f"strategy cycle log line {line_number} is not valid JSON: {exc}"
                    ) from exc
                records.append(from_jsonable(PaperStrategyCycleReport, row))
        return tuple(records)


def run_strategy_cycle(
    *,
    client: MarketDataClient,
    scan_config: MarketScanConfig,
    cycle_config: PaperStrategyCycleConfig,
    generated_at: datetime | None = None,
    paper_trade_record_sink: Callable[[object], object] | None = None,
) -> PaperStrategyCycleReport:
    if not isinstance(client, MarketDataClient):
        raise ValueError("client must be a MarketDataClient")
    if not isinstance(scan_config, MarketScanConfig):
        raise ValueError("scan_config must be a MarketScanConfig")
    if not isinstance(cycle_config, PaperStrategyCycleConfig):
        raise ValueError("cycle_config must be a PaperStrategyCycleConfig")
    if generated_at is not None and not isinstance(generated_at, datetime):
        raise ValueError("generated_at must be a datetime or None")
    if paper_trade_record_sink is not None and not callable(paper_trade_record_sink):
        raise ValueError("paper_trade_record_sink must be callable or None")
    if (
        cycle_config.paper_execution_config is not None
        and paper_trade_record_sink is None
    ):
        raise ValueError(
            "paper_trade_record_sink is required when paper execution is enabled",
        )

    if generated_at is not None:
        timestamp = _as_utc(generated_at)
    else:
        timestamp = datetime.now(UTC).astimezone(UTC)

    # 1. Fetch + archive the market list (read-only Gamma /markets).
    archive = RawArchive(scan_config.archive_root)
    markets_payload = client.list_markets(
        active=True,
        closed=False,
        limit=scan_config.limit,
        search=cycle_config.market_search,
    )
    market_raw_archive_entry = archive.write(
        source="gamma_markets",
        name="markets",
        payload=markets_payload,
        captured_at=timestamp,
    )

    # 2. Normalize (skip malformed -- not counted as blocked) + optional
    #    score prefilter + truncate. Deterministic stable two-pass sort.
    normalized: list[NormalizedMarket] = []
    for raw in _iter_dicts(markets_payload):
        try:
            nm = normalize_gamma_market(raw, captured_at=timestamp)
        except Exception:
            continue
        normalized.append(nm)
    if cycle_config.prefilter_by_score:
        base = sorted(
            normalized,
            key=lambda nm: (nm.market.condition_id, nm.market.market_slug),
        )
        scored = sorted(
            base,
            key=lambda nm: _total_score(score_market(nm, {})),
            reverse=True,
        )
    else:
        scored = sorted(
            normalized,
            key=lambda nm: (nm.market.condition_id, nm.market.market_slug),
        )
    retained = scored[: cycle_config.max_markets_per_cycle]

    # 3. Per-market strategy evaluation (try/except isolates failures).
    # Each retained market records exactly one status: a cycle-layer
    # "blocked_non_binary_market"/"blocked_fetch_error", the snapshot
    # builder's own "blocked_*" status, or "snapshot_ready".
    statuses: list[str] = []
    collected_reports: list[PaperCostAwareEventStrategyReport] = []
    # Stage 4: stash per-market context for the inline paper-execution pass.
    # Only populated when paper execution is enabled (default-off). Keyed by
    # market_slug with first-occurrence wins (mirrors the screening dedupe).
    paper_pass_enabled = cycle_config.paper_execution_config is not None
    paper_trade_context: dict[str, tuple[Any, ...]] = {}
    for nm in retained:
        try:
            if len(nm.tokens) != 2:
                # Non-binary: record a cycle-layer status. Do NOT call the
                # builder with fabricated books.
                statuses.append("blocked_non_binary_market")
                continue
            # Mirror cost_aware_snapshot_builder's YES/NO resolution verbatim.
            yes_token_id, no_token_id = _resolve_token_ids(nm)
            yes_book_raw = client.get_order_book(token_id=yes_token_id)
            no_book_raw = client.get_order_book(token_id=no_token_id)
            # C2b: token-unique archive names (pipeline precedent name=f"book-{token_id}").
            yes_archive_entry = archive.write(
                source="clob_book",
                name=f"book-{yes_token_id}",
                payload=yes_book_raw,
                captured_at=timestamp,
            )
            no_archive_entry = archive.write(
                source="clob_book",
                name=f"book-{no_token_id}",
                payload=no_book_raw,
                captured_at=timestamp,
            )
            yes_book = normalize_order_book(yes_book_raw, captured_at=timestamp)
            no_book = normalize_order_book(no_book_raw, captured_at=timestamp)
            # cost_aware_snapshot_builder enforces isinstance(forecast, PaperForecast),
            # so a book_imbalance forecast is rejected downstream until that leaf
            # accepts both forecast types.
            forecast: Any
            if cycle_config.forecast_provider == "naive":
                forecast = build_paper_naive_forecast(
                    nm,
                    yes_book,
                    no_book,
                    config=cycle_config.forecast_config,
                    generated_at=timestamp,
                )
            elif cycle_config.forecast_provider == "book_imbalance":
                bi_config = cycle_config.book_imbalance_config
                if bi_config is None:
                    raise ValueError("book_imbalance_config is required")
                forecast = build_paper_book_imbalance_forecast(
                    nm,
                    yes_book,
                    no_book,
                    config=bi_config,
                    generated_at=timestamp,
                )
            else:  # "llm"
                llm_config = cycle_config.llm_forecast_config
                if cycle_config.llm_transport is None or llm_config is None:
                    raise ValueError(
                        "llm_transport and llm_forecast_config are required",
                    )
                outcome_names = tuple(token.outcome_name for token in nm.tokens)
                question_for_estimate = nm.market.question[
                    : llm_config.max_question_chars
                ]
                # Stage 10: enrich the GLM prompt with market metadata so the
                # probability estimate is grounded in volume / liquidity /
                # end_time / rules. Decimal fields are str()-coerced (never
                # float). spread is intentionally excluded here -- the
                # cost-aware snapshot is built downstream of this dispatch, but
                # the live books ARE available here (fetched earlier in the loop).
                market_context = {
                    "current_yes_ask": (
                        str(yes_book.asks[0].price)
                        if yes_book.asks
                        else "unknown"
                    ),
                    "current_spread": (
                        str(yes_book.asks[0].price - yes_book.bids[0].price)
                        if yes_book.asks and yes_book.bids
                        else "unknown"
                    ),
                    "volume_24h": (
                        str(nm.market.volume_24h)
                        if nm.market.volume_24h
                        else "unknown"
                    ),
                    "liquidity": (
                        str(nm.market.liquidity)
                        if nm.market.liquidity
                        else "unknown"
                    ),
                    "end_time": (
                        nm.market.end_time.isoformat()
                        if nm.market.end_time
                        else "unknown"
                    ),
                    "rules": (nm.rules_text or "unknown")[:500],
                }
                try:
                    llm_result = cycle_config.llm_transport.estimate(
                        market_question=question_for_estimate,
                        outcome_names=outcome_names,
                        market_context=market_context,
                    )
                    forecast = build_paper_llm_forecast(
                        nm,
                        result=llm_result,
                        config=llm_config,
                        generated_at=timestamp,
                    )
                except Exception:
                    bi_config = cycle_config.book_imbalance_config
                    if bi_config is None:
                        raise
                    forecast = build_paper_book_imbalance_forecast(
                        nm, yes_book, no_book,
                        config=bi_config,
                        generated_at=timestamp,
                    )
            attempt = build_paper_cost_aware_event_market_snapshot(
                nm,
                yes_book,
                no_book,
                forecast,
                config=cycle_config.snapshot_config,
                generated_at=timestamp,
            )
            if attempt.status == "snapshot_ready":
                snapshot = attempt.snapshot
                # Builder contract: snapshot_ready implies snapshot is not None.
                # Guard for type safety; reaching here is a builder violation.
                if snapshot is None:
                    raise ValueError(
                        "snapshot_ready attempt must carry a snapshot",
                    )
                report = build_paper_cost_aware_event_strategy_report(
                    snapshot,
                    cost_assumptions=cycle_config.cost_assumptions,
                    config=cycle_config.strategy_config,
                    generated_at=timestamp,
                )
                collected_reports.append(report)
                if paper_pass_enabled:
                    # setdefault: first-occurrence wins to match the screening
                    # dedupe (keeps the first report per market_slug).
                    paper_trade_context.setdefault(
                        nm.market.market_slug,
                        (
                            nm,
                            yes_book,
                            no_book,
                            yes_archive_entry,
                            no_archive_entry,
                            report,
                        ),
                    )
                statuses.append("snapshot_ready")
            else:
                statuses.append(attempt.status)
        except Exception:
            statuses.append("blocked_fetch_error")
            continue

    snapshot_ready_count = statuses.count("snapshot_ready")

    # 4. Screening aggregate. C1b: project_screening raises on duplicate
    #    market_slug, so dedupe (keep first) before aggregation.
    deduped = _dedupe_by_market_slug(collected_reports)
    screening = (
        build_paper_project_screening_report(
            reports=tuple(deduped),
            config=cycle_config.screening_config,
            generated_at=timestamp,
        )
        if deduped
        else None
    )

    # 4b. Inline paper-execution pass (Stage 4, additive/default-off). Turn
    #     each screening_ready candidate into an auditable PaperTradeRecord
    #     against the in-memory book captured during the cycle, then persist it
    #     through the required injected DB sink. Per-candidate try/except
    #     isolation applies to paper execution itself; sink failures propagate.
    #     Default-off: when paper_execution_config is None this block is skipped.
    if cycle_config.paper_execution_config is not None and screening is not None:
        if paper_trade_record_sink is None:
            raise ValueError(
                "paper_trade_record_sink is required when paper execution is enabled",
            )
        paper_pass_config = cycle_config.paper_execution_config
        for candidate in screening.candidates:
            if candidate.screening_status != "screening_ready":
                continue
            context = paper_trade_context.get(candidate.market_slug)
            if context is None:
                continue
            (
                nm,
                yes_book,
                no_book,
                yes_archive_entry,
                no_archive_entry,
                cost_aware_report,
            ) = context
            if candidate.scoring_side == "yes":
                chosen_book = yes_book
                chosen_archive_entry = yes_archive_entry
            else:
                chosen_book = no_book
                chosen_archive_entry = no_archive_entry
            try:
                paper_result = execute_paper_trade_from_screening(
                    candidate=candidate,
                    cost_aware_report=cost_aware_report,
                    market=nm,
                    book=chosen_book,
                    raw_book_archive_entry=chosen_archive_entry,
                    market_raw_archive_entry=market_raw_archive_entry,
                    config=paper_pass_config,
                    generated_at=timestamp,
                )
            except Exception:
                continue
            if paper_result.record is not None:
                paper_trade_record_sink(paper_result.record)

    # 5. Assemble + validate invariants in __post_init__.
    return PaperStrategyCycleReport(
        generated_at=timestamp,
        config_version=cycle_config.config_version,
        scan_market_count=len(normalized),
        considered_count=len(retained),
        snapshot_ready_count=snapshot_ready_count,
        cost_aware_report_count=len(collected_reports),
        blocked_counts=_deterministic_blocked_counts(statuses),
        screening_report=screening,
        cost_aware_reports=tuple(collected_reports),
    )


def _total_score(scores: list[Any]) -> Decimal:
    """Aggregate a market's per-token MarketScore values into one comparable.

    Mirrors pipeline.py's ``ScoredCandidate.total_score`` derivation: pipeline
    ranks each (market, token) by the raw ``MarketScore.total`` Decimal
    (domain.MarketScore.total weighted sum) and sorts ``ranked`` by
    ``(score.total, token_id)`` descending. Here we collapse the per-token
    scores for one market to their maximum (the market's representative
    candidate score), preserving pipeline's raw-``score.total`` sort semantics.
    """

    best = ZERO
    for score in scores:
        total = score.total
        if total > best:
            best = total
    return best


def _resolve_token_ids(market: NormalizedMarket) -> tuple[str, str]:
    """Resolve (YES, NO) token ids mirroring cost_aware_snapshot_builder verbatim.

    YES_NAMES={yes,true,long}/NO_NAMES={no,false,short}, then outcome_index
    0/1 fallback. Divergence from the builder triggers
    ``blocked_book_token_mismatch`` on every market. Only called for binary
    markets, so both indices 0/1 exist and both ids are non-empty.
    """

    yes_token = next(
        (
            token
            for token in market.tokens
            if token.outcome_name.strip().lower() in YES_NAMES
        ),
        None,
    )
    no_token = next(
        (
            token
            for token in market.tokens
            if token.outcome_name.strip().lower() in NO_NAMES
        ),
        None,
    )
    if yes_token is None or no_token is None:
        indexed_tokens = {token.outcome_index: token for token in market.tokens}
        yes_token = yes_token or indexed_tokens.get(0)
        no_token = no_token or indexed_tokens.get(1)
    # Only binary markets reach here, so outcome_index 0/1 always exist; the
    # guard is type safety mirroring the builder's unresolvable check (the
    # degenerate shared-token-id case is surfaced by the builder as
    # blocked_unresolvable_outcome_pair when it is called with the books).
    if yes_token is None or no_token is None:
        raise ValueError("unresolvable outcome pair")
    return yes_token.token_id, no_token.token_id


def _dedupe_by_market_slug(
    reports: list[PaperCostAwareEventStrategyReport],
) -> list[PaperCostAwareEventStrategyReport]:
    """Keep the first report per market_slug (C1b).

    ``build_paper_project_screening_report`` raises on duplicate market_slug;
    dedupe preserves mandatory per-market isolation at the aggregation boundary
    while keeping every report counted in cost_aware_report_count.
    """

    seen: set[str] = set()
    deduped: list[PaperCostAwareEventStrategyReport] = []
    for report in reports:
        slug = report.market_slug
        if slug in seen:
            continue
        seen.add(slug)
        deduped.append(report)
    return deduped


def _deterministic_blocked_counts(statuses: list[str]) -> tuple[tuple[str, int], ...]:
    counts: dict[str, int] = {}
    for status in statuses:
        if status == "snapshot_ready":
            continue
        counts[status] = counts.get(status, 0) + 1
    return tuple(sorted(counts.items()))


def _iter_dicts(payload: Any) -> list[dict[str, Any]]:
    if isinstance(payload, list):
        return [item for item in payload if isinstance(item, dict)]
    if isinstance(payload, dict) and isinstance(payload.get("data"), list):
        return [item for item in payload["data"] if isinstance(item, dict)]
    return []


def _as_utc(value: datetime) -> datetime:
    if not isinstance(value, datetime):
        raise ValueError("datetime value is required")
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


def _require_canonical_string(field_name: str, value: str) -> None:
    if not isinstance(value, str):
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")


def _require_nonnegative_int(field_name: str, value: int) -> None:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(f"{field_name} must be an int")
    if value < 0:
        raise ValueError(f"{field_name} must be nonnegative")


def _require_positive_int(field_name: str, value: int) -> None:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(f"{field_name} must be an int")
    if value <= 0:
        raise ValueError(f"{field_name} must be positive")


def _require_config_instance(field_name: str, value: object, expected: type) -> None:
    if not isinstance(value, expected):
        raise ValueError(f"{field_name} must be a {expected.__name__}")


def _normalize_blocked_counts(
    value: tuple[tuple[str, int], ...],
) -> tuple[tuple[str, int], ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError("blocked_counts must be an iterable")
    try:
        items = tuple(value)
    except TypeError as exc:
        raise ValueError("blocked_counts must be an iterable") from exc
    normalized: list[tuple[str, int]] = []
    for item in items:
        if not isinstance(item, tuple) or len(item) != 2:
            raise ValueError("blocked_counts entries must be (status, count) pairs")
        status, count = item
        _require_canonical_string("blocked_counts status", status)
        _require_positive_int("blocked_counts count", count)
        normalized.append((status, count))
    statuses = [status for status, _count in normalized]
    if len(set(statuses)) != len(statuses):
        raise ValueError("blocked_counts statuses must be unique")
    if statuses != sorted(statuses):
        raise ValueError("blocked_counts must be sorted by status")
    return tuple(normalized)


def _normalize_cost_aware_reports(
    value: tuple[PaperCostAwareEventStrategyReport, ...],
) -> tuple[PaperCostAwareEventStrategyReport, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError("cost_aware_reports must be an iterable")
    try:
        reports = tuple(value)
    except TypeError as exc:
        raise ValueError("cost_aware_reports must be an iterable") from exc
    for report in reports:
        if type(report) is not PaperCostAwareEventStrategyReport:
            raise ValueError(
                "cost_aware_reports entries must be "
                "PaperCostAwareEventStrategyReport",
            )
        if report.paper_only is not True:
            raise ValueError("cost_aware_reports paper_only must be True")
        if report.report_only is not True:
            raise ValueError("cost_aware_reports report_only must be True")
    return reports


def _validate_report_tree(report: PaperStrategyCycleReport) -> None:
    # Reconstruct the cycle report, passing the nested screening_report through
    # by reference (it is a validated frozen PaperProjectScreeningReport). This
    # re-runs __post_init__, re-checking every count invariant and the nested
    # isinstance guard.
    PaperStrategyCycleReport(
        generated_at=report.generated_at,
        config_version=report.config_version,
        scan_market_count=report.scan_market_count,
        considered_count=report.considered_count,
        snapshot_ready_count=report.snapshot_ready_count,
        cost_aware_report_count=report.cost_aware_report_count,
        blocked_counts=report.blocked_counts,
        screening_report=report.screening_report,
        cost_aware_reports=report.cost_aware_reports,
        paper_only=report.paper_only,
        report_only=report.report_only,
    )


def _json_ready(value: Any) -> Any:
    if isinstance(value, Decimal):
        _require_finite_decimal("JSON Decimal value", value)
        return str(value)
    if isinstance(value, datetime):
        return _as_utc(value).isoformat()
    if isinstance(value, bool) or value is None or isinstance(value, (int, str)):
        return value
    if isinstance(value, float):
        raise ValueError("JSON value must not be a float")
    if isinstance(value, (tuple, list)):
        return [_json_ready(item) for item in value]
    if isinstance(value, dict):
        ready: dict[str, Any] = {}
        for item_key, item_value in value.items():
            if not isinstance(item_key, str):
                raise ValueError("JSON object keys must be strings")
            ready[item_key] = _json_ready(item_value)
        return ready
    raise ValueError("value is not JSON serializable")


def _require_finite_decimal(field_name: str, value: Decimal) -> None:
    if not isinstance(value, Decimal):
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")


def _normalize_log_path(value: Path | str) -> Path:
    if isinstance(value, str):
        if not value.strip():
            raise ValueError("path must be nonblank")
        path = Path(value)
    elif isinstance(value, Path):
        path = value
    else:
        raise ValueError("path must be a Path or string")
    if path.exists() and path.is_dir():
        raise ValueError("path must not be an existing directory")
    _validate_log_parent(path)
    return path


def _validate_log_parent(path: Path) -> None:
    parent = path.parent
    while not parent.exists():
        if parent == parent.parent:
            break
        parent = parent.parent
    if parent.exists() and not parent.is_dir():
        raise ValueError("parent path must be a directory")
