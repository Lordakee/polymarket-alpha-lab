"""Pure market-close recommendation readiness gate."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, localcontext
from hashlib import sha256
from typing import Any


DEFAULT_STRATEGY_RECOMMENDATION_MARKET_CLOSE_READINESS_GATE_V2_CONFIG_VERSION = (
    "strategy-recommendation-market-close-readiness-gate-v2"
)

QUANTUM = Decimal("0.000001")
ZERO = Decimal("0.000000")
DECIMAL_CONTEXT = Context(prec=64)

RECOMMENDATION_INTENTS = ("keep", "enter")
CLOSE_READINESS_STATUSES = ("blocked", "watch", "ready")
EMPTY_REASON_CODE = "strategy_recommendation_market_close_readiness_gate_v2_empty"

REPORT_REASON_PRIORITY = (
    "market_close_gate_blocked",
    "market_close_gate_watch",
    "market_close_gate_ready",
    "close_proximity_block_enter",
    "close_proximity_watch",
    "close_proximity_ready",
    "official_result_lag_blocked",
    "official_result_lag_watch",
    "official_result_lag_ready",
    "source_contradiction_blocked",
    "source_contradiction_watch",
    "source_contradiction_ready",
    "liquidity_exit_capacity_blocked",
    "liquidity_exit_capacity_watch",
    "liquidity_exit_capacity_ready",
    "settlement_ambiguity_blocked",
    "settlement_ambiguity_watch",
    "settlement_ambiguity_ready",
    "paper_cost_floor_blocked",
    "paper_cost_floor_watch",
    "paper_cost_floor_ready",
    EMPTY_REASON_CODE,
)

SENSITIVE_PUBLIC_TEXT = (
    "secret",
    "token",
    "wal" "let",
    "private",
    "password",
    "bearer",
    "au" "th",
    "ord" "er",
    "tr" "ade",
)


@dataclass(frozen=True)
class StrategyRecommendationMarketCloseReadinessGateV2Config:
    config_version: str = (
        DEFAULT_STRATEGY_RECOMMENDATION_MARKET_CLOSE_READINESS_GATE_V2_CONFIG_VERSION
    )
    near_close_watch_minutes: Decimal = Decimal("120.000000")
    near_close_block_enter_minutes: Decimal = Decimal("30.000000")
    max_ready_official_result_lag_minutes: Decimal = Decimal("15.000000")
    max_watch_official_result_lag_minutes: Decimal = Decimal("60.000000")
    max_ready_source_contradiction_score: Decimal = Decimal("0.050000")
    max_watch_source_contradiction_score: Decimal = Decimal("0.200000")
    min_ready_exit_capacity_ratio: Decimal = Decimal("2.000000")
    min_watch_exit_capacity_ratio: Decimal = Decimal("1.000000")
    max_ready_settlement_ambiguity_score: Decimal = Decimal("0.050000")
    max_watch_settlement_ambiguity_score: Decimal = Decimal("0.200000")
    min_ready_edge_after_paper_cost: Decimal = Decimal("0.020000")
    min_watch_edge_after_paper_cost: Decimal = Decimal("0.000000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_public_text("config_version", self.config_version)
        for field_name in (
            "near_close_watch_minutes",
            "near_close_block_enter_minutes",
            "max_ready_official_result_lag_minutes",
            "max_watch_official_result_lag_minutes",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "max_ready_source_contradiction_score",
            "max_watch_source_contradiction_score",
            "max_ready_settlement_ambiguity_score",
            "max_watch_settlement_ambiguity_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "min_ready_exit_capacity_ratio",
            "min_watch_exit_capacity_ratio",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "min_ready_edge_after_paper_cost",
            "min_watch_edge_after_paper_cost",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_decimal(field_name, getattr(self, field_name)),
            )
        _validate_config(self)
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class StrategyRecommendationMarketCloseReadinessGateV2Candidate:
    candidate_reference: str
    market_slug: str
    evaluated_at: datetime
    recommendation_intent: str
    minutes_to_close: Decimal
    official_result_lag_minutes: Decimal
    source_contradiction_score: Decimal
    exit_capacity_ratio: Decimal
    settlement_ambiguity_score: Decimal
    expected_edge_after_paper_cost: Decimal
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("candidate_reference", self.candidate_reference)
        _require_public_text("market_slug", self.market_slug)
        object.__setattr__(
            self,
            "evaluated_at",
            _as_utc("evaluated_at", self.evaluated_at),
        )
        _require_member(
            "recommendation_intent",
            self.recommendation_intent,
            RECOMMENDATION_INTENTS,
        )
        for field_name in (
            "minutes_to_close",
            "official_result_lag_minutes",
            "exit_capacity_ratio",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "source_contradiction_score",
            "settlement_ambiguity_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "expected_edge_after_paper_cost",
            _normalize_decimal(
                "expected_edge_after_paper_cost",
                self.expected_edge_after_paper_cost,
            ),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes, require_nonempty=True),
        )
        _require_hard_flags("candidate", self)


@dataclass(frozen=True)
class StrategyRecommendationMarketCloseReadinessGateV2Row:
    redacted_candidate_reference: str
    market_slug: str
    evaluated_at: datetime
    recommendation_intent: str
    minutes_to_close: Decimal
    official_result_lag_minutes: Decimal
    source_contradiction_score: Decimal
    exit_capacity_ratio: Decimal
    settlement_ambiguity_score: Decimal
    expected_edge_after_paper_cost: Decimal
    close_readiness_status: str
    safe_to_keep: bool
    safe_to_enter: bool
    readiness_digest: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_redacted_reference(self.redacted_candidate_reference)
        _require_public_text("market_slug", self.market_slug)
        object.__setattr__(
            self,
            "evaluated_at",
            _as_utc("evaluated_at", self.evaluated_at),
        )
        _require_member(
            "recommendation_intent",
            self.recommendation_intent,
            RECOMMENDATION_INTENTS,
        )
        for field_name in (
            "minutes_to_close",
            "official_result_lag_minutes",
            "exit_capacity_ratio",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "source_contradiction_score",
            "settlement_ambiguity_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "expected_edge_after_paper_cost",
            _normalize_decimal(
                "expected_edge_after_paper_cost",
                self.expected_edge_after_paper_cost,
            ),
        )
        _require_member(
            "close_readiness_status",
            self.close_readiness_status,
            CLOSE_READINESS_STATUSES,
        )
        _require_bool("safe_to_keep", self.safe_to_keep)
        _require_bool("safe_to_enter", self.safe_to_enter)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes, require_nonempty=True),
        )
        _validate_row(self)
        _require_hard_flags("row", self)


@dataclass(frozen=True)
class StrategyRecommendationMarketCloseReadinessGateV2Report:
    generated_at: datetime
    config_version: str
    candidate_count: Decimal
    ready_count: Decimal
    watch_count: Decimal
    blocked_count: Decimal
    enter_safe_count: Decimal
    keep_safe_count: Decimal
    min_minutes_to_close: Decimal
    max_official_result_lag_minutes: Decimal
    max_source_contradiction_score: Decimal
    min_exit_capacity_ratio: Decimal
    max_settlement_ambiguity_score: Decimal
    min_expected_edge_after_paper_cost: Decimal
    status: str
    report_digest: str
    reason_codes: tuple[str, ...]
    rows: tuple[StrategyRecommendationMarketCloseReadinessGateV2Row, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "generated_at",
            _as_utc("generated_at", self.generated_at),
        )
        _require_public_text("config_version", self.config_version)
        for field_name in (
            "candidate_count",
            "ready_count",
            "watch_count",
            "blocked_count",
            "enter_safe_count",
            "keep_safe_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_count_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "min_minutes_to_close",
            "max_official_result_lag_minutes",
            "max_source_contradiction_score",
            "min_exit_capacity_ratio",
            "max_settlement_ambiguity_score",
            "min_expected_edge_after_paper_cost",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_decimal(field_name, getattr(self, field_name)),
            )
        _require_member("status", self.status, CLOSE_READINESS_STATUSES)
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes, require_nonempty=True),
        )
        _validate_report(self)
        _require_hard_flags("report", self)


def build_strategy_recommendation_market_close_readiness_gate_v2(
    candidates: Iterable[object],
    *,
    config: StrategyRecommendationMarketCloseReadinessGateV2Config,
    generated_at: datetime,
) -> StrategyRecommendationMarketCloseReadinessGateV2Report:
    if type(config) is not StrategyRecommendationMarketCloseReadinessGateV2Config:
        raise ValueError(
            "config must be a StrategyRecommendationMarketCloseReadinessGateV2Config",
        )
    _require_hard_flags("config", config)
    generated_at = _as_utc("generated_at", generated_at)
    source_candidates = _normalize_candidates(candidates)
    rows = tuple(
        sorted(
            (
                _row_from_candidate(
                    candidate,
                    config=config,
                    generated_at=generated_at,
                )
                for candidate in source_candidates
            ),
            key=_row_sort_key,
        ),
    )
    candidate_count = _count_decimal(len(rows))
    ready_count = _status_count(rows, "ready")
    watch_count = _status_count(rows, "watch")
    blocked_count = _status_count(rows, "blocked")
    enter_safe_count = _safe_count(rows, "safe_to_enter")
    keep_safe_count = _safe_count(rows, "safe_to_keep")
    status = _report_status(rows)
    reason_codes = _report_reason_codes(rows)
    report_digest = _report_digest(
        generated_at=generated_at,
        config_version=config.config_version,
        candidate_count=candidate_count,
        ready_count=ready_count,
        watch_count=watch_count,
        blocked_count=blocked_count,
        enter_safe_count=enter_safe_count,
        keep_safe_count=keep_safe_count,
        status=status,
        reason_codes=reason_codes,
        rows=rows,
    )
    return StrategyRecommendationMarketCloseReadinessGateV2Report(
        generated_at=generated_at,
        config_version=config.config_version,
        candidate_count=candidate_count,
        ready_count=ready_count,
        watch_count=watch_count,
        blocked_count=blocked_count,
        enter_safe_count=enter_safe_count,
        keep_safe_count=keep_safe_count,
        min_minutes_to_close=_min_row_decimal(rows, "minutes_to_close"),
        max_official_result_lag_minutes=_max_row_decimal(
            rows,
            "official_result_lag_minutes",
        ),
        max_source_contradiction_score=_max_row_decimal(
            rows,
            "source_contradiction_score",
        ),
        min_exit_capacity_ratio=_min_row_decimal(rows, "exit_capacity_ratio"),
        max_settlement_ambiguity_score=_max_row_decimal(
            rows,
            "settlement_ambiguity_score",
        ),
        min_expected_edge_after_paper_cost=_min_row_decimal(
            rows,
            "expected_edge_after_paper_cost",
        ),
        status=status,
        report_digest=report_digest,
        reason_codes=reason_codes,
        rows=rows,
    )


def strategy_recommendation_market_close_readiness_gate_v2_payload(
    report: StrategyRecommendationMarketCloseReadinessGateV2Report,
) -> dict[str, Any]:
    if type(report) is not StrategyRecommendationMarketCloseReadinessGateV2Report:
        raise ValueError(
            "report must be a StrategyRecommendationMarketCloseReadinessGateV2Report",
        )
    _require_hard_flags("report", report)
    payload = _payload_value(report)
    if type(payload) is not dict:
        raise ValueError("report payload must be a dictionary")
    return payload


def _row_from_candidate(
    candidate: StrategyRecommendationMarketCloseReadinessGateV2Candidate,
    *,
    config: StrategyRecommendationMarketCloseReadinessGateV2Config,
    generated_at: datetime,
) -> StrategyRecommendationMarketCloseReadinessGateV2Row:
    if candidate.evaluated_at > generated_at:
        raise ValueError("evaluated_at must not be after generated_at")
    status = _close_readiness_status(candidate, config)
    reason_codes = _row_reason_codes(candidate, config, status)
    redacted_candidate_reference = _redacted_reference(candidate.candidate_reference)
    safe_to_keep = _safe_to_keep(status)
    safe_to_enter = _safe_to_enter(status)
    readiness_digest = _row_digest(
        redacted_candidate_reference=redacted_candidate_reference,
        market_slug=candidate.market_slug,
        evaluated_at=candidate.evaluated_at,
        recommendation_intent=candidate.recommendation_intent,
        minutes_to_close=candidate.minutes_to_close,
        official_result_lag_minutes=candidate.official_result_lag_minutes,
        source_contradiction_score=candidate.source_contradiction_score,
        exit_capacity_ratio=candidate.exit_capacity_ratio,
        settlement_ambiguity_score=candidate.settlement_ambiguity_score,
        expected_edge_after_paper_cost=candidate.expected_edge_after_paper_cost,
        close_readiness_status=status,
        safe_to_keep=safe_to_keep,
        safe_to_enter=safe_to_enter,
        reason_codes=reason_codes,
    )
    return StrategyRecommendationMarketCloseReadinessGateV2Row(
        redacted_candidate_reference=redacted_candidate_reference,
        market_slug=candidate.market_slug,
        evaluated_at=candidate.evaluated_at,
        recommendation_intent=candidate.recommendation_intent,
        minutes_to_close=candidate.minutes_to_close,
        official_result_lag_minutes=candidate.official_result_lag_minutes,
        source_contradiction_score=candidate.source_contradiction_score,
        exit_capacity_ratio=candidate.exit_capacity_ratio,
        settlement_ambiguity_score=candidate.settlement_ambiguity_score,
        expected_edge_after_paper_cost=candidate.expected_edge_after_paper_cost,
        close_readiness_status=status,
        safe_to_keep=safe_to_keep,
        safe_to_enter=safe_to_enter,
        readiness_digest=readiness_digest,
        reason_codes=reason_codes,
    )


def _close_readiness_status(
    candidate: StrategyRecommendationMarketCloseReadinessGateV2Candidate,
    config: StrategyRecommendationMarketCloseReadinessGateV2Config,
) -> str:
    states = (
        _close_proximity_state(candidate, config),
        _ceiling_state(
            candidate.official_result_lag_minutes,
            ready=config.max_ready_official_result_lag_minutes,
            watch=config.max_watch_official_result_lag_minutes,
        ),
        _ceiling_state(
            candidate.source_contradiction_score,
            ready=config.max_ready_source_contradiction_score,
            watch=config.max_watch_source_contradiction_score,
        ),
        _floor_state(
            candidate.exit_capacity_ratio,
            ready=config.min_ready_exit_capacity_ratio,
            watch=config.min_watch_exit_capacity_ratio,
        ),
        _ceiling_state(
            candidate.settlement_ambiguity_score,
            ready=config.max_ready_settlement_ambiguity_score,
            watch=config.max_watch_settlement_ambiguity_score,
        ),
        _floor_state(
            candidate.expected_edge_after_paper_cost,
            ready=config.min_ready_edge_after_paper_cost,
            watch=config.min_watch_edge_after_paper_cost,
        ),
    )
    if "blocked" in states:
        return "blocked"
    if "watch" in states:
        return "watch"
    return "ready"


def _row_reason_codes(
    candidate: StrategyRecommendationMarketCloseReadinessGateV2Candidate,
    config: StrategyRecommendationMarketCloseReadinessGateV2Config,
    status: str,
) -> tuple[str, ...]:
    reason_codes = [
        *candidate.reason_codes,
        f"market_close_gate_{status}",
        _close_proximity_reason_code(candidate, config),
        _dimension_reason_code(
            "official_result_lag",
            _ceiling_state(
                candidate.official_result_lag_minutes,
                ready=config.max_ready_official_result_lag_minutes,
                watch=config.max_watch_official_result_lag_minutes,
            ),
        ),
        _dimension_reason_code(
            "source_contradiction",
            _ceiling_state(
                candidate.source_contradiction_score,
                ready=config.max_ready_source_contradiction_score,
                watch=config.max_watch_source_contradiction_score,
            ),
        ),
        _dimension_reason_code(
            "liquidity_exit_capacity",
            _floor_state(
                candidate.exit_capacity_ratio,
                ready=config.min_ready_exit_capacity_ratio,
                watch=config.min_watch_exit_capacity_ratio,
            ),
        ),
        _dimension_reason_code(
            "settlement_ambiguity",
            _ceiling_state(
                candidate.settlement_ambiguity_score,
                ready=config.max_ready_settlement_ambiguity_score,
                watch=config.max_watch_settlement_ambiguity_score,
            ),
        ),
        _dimension_reason_code(
            "paper_cost_floor",
            _floor_state(
                candidate.expected_edge_after_paper_cost,
                ready=config.min_ready_edge_after_paper_cost,
                watch=config.min_watch_edge_after_paper_cost,
            ),
        ),
    ]
    return _unique_reason_codes(tuple(reason_codes))


def _close_proximity_reason_code(
    candidate: StrategyRecommendationMarketCloseReadinessGateV2Candidate,
    config: StrategyRecommendationMarketCloseReadinessGateV2Config,
) -> str:
    state = _close_proximity_state(candidate, config)
    if state == "blocked":
        return "close_proximity_block_enter"
    return f"close_proximity_{state}"


def _close_proximity_state(
    candidate: StrategyRecommendationMarketCloseReadinessGateV2Candidate,
    config: StrategyRecommendationMarketCloseReadinessGateV2Config,
) -> str:
    if (
        candidate.recommendation_intent == "enter"
        and candidate.minutes_to_close <= config.near_close_block_enter_minutes
    ):
        return "blocked"
    if candidate.minutes_to_close <= config.near_close_watch_minutes:
        return "watch"
    return "ready"


def _dimension_reason_code(prefix: str, state: str) -> str:
    return f"{prefix}_{state}"


def _ceiling_state(value: Decimal, *, ready: Decimal, watch: Decimal) -> str:
    if value <= ready:
        return "ready"
    if value <= watch:
        return "watch"
    return "blocked"


def _floor_state(value: Decimal, *, ready: Decimal, watch: Decimal) -> str:
    if value >= ready:
        return "ready"
    if value >= watch:
        return "watch"
    return "blocked"


def _safe_to_keep(status: str) -> bool:
    return status != "blocked"


def _safe_to_enter(status: str) -> bool:
    return status == "ready"


def _normalize_candidates(
    candidates: Iterable[object],
) -> tuple[StrategyRecommendationMarketCloseReadinessGateV2Candidate, ...]:
    if isinstance(candidates, (str, bytes)):
        raise ValueError("candidates must be an iterable")
    try:
        rows = tuple(candidates)
    except TypeError as exc:
        raise ValueError("candidates must be an iterable") from exc
    seen: set[str] = set()
    normalized: list[StrategyRecommendationMarketCloseReadinessGateV2Candidate] = []
    for row in rows:
        if type(row) is not StrategyRecommendationMarketCloseReadinessGateV2Candidate:
            raise ValueError(
                "candidates must contain "
                "StrategyRecommendationMarketCloseReadinessGateV2Candidate",
            )
        _require_hard_flags("candidate", row)
        if row.candidate_reference in seen:
            raise ValueError("duplicate candidate_reference")
        seen.add(row.candidate_reference)
        normalized.append(row)
    return tuple(normalized)


def _normalize_rows(
    value: object,
) -> tuple[StrategyRecommendationMarketCloseReadinessGateV2Row, ...]:
    if type(value) is not tuple:
        raise ValueError("rows must be a tuple")
    rows = tuple(value)
    for row in rows:
        if type(row) is not StrategyRecommendationMarketCloseReadinessGateV2Row:
            raise ValueError(
                "rows must contain StrategyRecommendationMarketCloseReadinessGateV2Row",
            )
        _require_hard_flags("row", row)
    return rows


def _row_sort_key(
    row: StrategyRecommendationMarketCloseReadinessGateV2Row,
) -> tuple[str, str]:
    return (row.market_slug, row.redacted_candidate_reference)


def _status_count(
    rows: tuple[StrategyRecommendationMarketCloseReadinessGateV2Row, ...],
    status: str,
) -> Decimal:
    return _count_decimal(
        sum(1 for row in rows if row.close_readiness_status == status),
    )


def _safe_count(
    rows: tuple[StrategyRecommendationMarketCloseReadinessGateV2Row, ...],
    field_name: str,
) -> Decimal:
    return _count_decimal(sum(1 for row in rows if getattr(row, field_name) is True))


def _max_row_decimal(
    rows: tuple[StrategyRecommendationMarketCloseReadinessGateV2Row, ...],
    field_name: str,
) -> Decimal:
    if not rows:
        return ZERO
    return max(getattr(row, field_name) for row in rows)


def _min_row_decimal(
    rows: tuple[StrategyRecommendationMarketCloseReadinessGateV2Row, ...],
    field_name: str,
) -> Decimal:
    if not rows:
        return ZERO
    return min(getattr(row, field_name) for row in rows)


def _report_status(
    rows: tuple[StrategyRecommendationMarketCloseReadinessGateV2Row, ...],
) -> str:
    if any(row.close_readiness_status == "blocked" for row in rows):
        return "blocked"
    if any(row.close_readiness_status == "watch" for row in rows) or not rows:
        return "watch"
    return "ready"


def _report_reason_codes(
    rows: tuple[StrategyRecommendationMarketCloseReadinessGateV2Row, ...],
) -> tuple[str, ...]:
    if not rows:
        return (EMPTY_REASON_CODE,)
    observed: set[str] = set()
    for row in rows:
        observed.update(row.reason_codes)
    prioritized = tuple(code for code in REPORT_REASON_PRIORITY if code in observed)
    extras = tuple(sorted(code for code in observed if code not in prioritized))
    return (*prioritized, *extras)


def _validate_config(
    config: StrategyRecommendationMarketCloseReadinessGateV2Config,
) -> None:
    if config.near_close_block_enter_minutes > config.near_close_watch_minutes:
        raise ValueError(
            "near_close_block_enter_minutes must not exceed near_close_watch_minutes",
        )
    if (
        config.max_ready_official_result_lag_minutes
        > config.max_watch_official_result_lag_minutes
    ):
        raise ValueError(
            "max_ready_official_result_lag_minutes must not exceed "
            "max_watch_official_result_lag_minutes",
        )
    if (
        config.max_ready_source_contradiction_score
        > config.max_watch_source_contradiction_score
    ):
        raise ValueError(
            "max_ready_source_contradiction_score must not exceed "
            "max_watch_source_contradiction_score",
        )
    if config.min_watch_exit_capacity_ratio > config.min_ready_exit_capacity_ratio:
        raise ValueError(
            "min_watch_exit_capacity_ratio must not exceed "
            "min_ready_exit_capacity_ratio",
        )
    if (
        config.max_ready_settlement_ambiguity_score
        > config.max_watch_settlement_ambiguity_score
    ):
        raise ValueError(
            "max_ready_settlement_ambiguity_score must not exceed "
            "max_watch_settlement_ambiguity_score",
        )
    if (
        config.min_watch_edge_after_paper_cost
        > config.min_ready_edge_after_paper_cost
    ):
        raise ValueError(
            "min_watch_edge_after_paper_cost must not exceed "
            "min_ready_edge_after_paper_cost",
        )


def _validate_row(
    row: StrategyRecommendationMarketCloseReadinessGateV2Row,
) -> None:
    expected_status = _row_status_from_reason_codes(row.reason_codes)
    if row.close_readiness_status != expected_status:
        raise ValueError("close_readiness_status must match reason_codes")
    if row.safe_to_keep is not _safe_to_keep(row.close_readiness_status):
        raise ValueError("safe_to_keep must match close_readiness_status")
    if row.safe_to_enter is not _safe_to_enter(row.close_readiness_status):
        raise ValueError("safe_to_enter must match close_readiness_status")
    if row.readiness_digest != _row_digest_from_row(row):
        raise ValueError("readiness_digest must match row inputs")


def _row_status_from_reason_codes(reason_codes: tuple[str, ...]) -> str:
    if "market_close_gate_blocked" in reason_codes:
        return "blocked"
    if "market_close_gate_watch" in reason_codes:
        return "watch"
    if "market_close_gate_ready" in reason_codes:
        return "ready"
    raise ValueError("reason_codes must include market close gate status")


def _validate_report(
    report: StrategyRecommendationMarketCloseReadinessGateV2Report,
) -> None:
    if report.candidate_count != _count_decimal(len(report.rows)):
        raise ValueError("candidate_count must match rows")
    if report.ready_count != _status_count(report.rows, "ready"):
        raise ValueError("ready_count must match rows")
    if report.watch_count != _status_count(report.rows, "watch"):
        raise ValueError("watch_count must match rows")
    if report.blocked_count != _status_count(report.rows, "blocked"):
        raise ValueError("blocked_count must match rows")
    if report.enter_safe_count != _safe_count(report.rows, "safe_to_enter"):
        raise ValueError("enter_safe_count must match rows")
    if report.keep_safe_count != _safe_count(report.rows, "safe_to_keep"):
        raise ValueError("keep_safe_count must match rows")
    if report.min_minutes_to_close != _min_row_decimal(report.rows, "minutes_to_close"):
        raise ValueError("min_minutes_to_close must match rows")
    if report.max_official_result_lag_minutes != _max_row_decimal(
        report.rows,
        "official_result_lag_minutes",
    ):
        raise ValueError("max_official_result_lag_minutes must match rows")
    if report.max_source_contradiction_score != _max_row_decimal(
        report.rows,
        "source_contradiction_score",
    ):
        raise ValueError("max_source_contradiction_score must match rows")
    if report.min_exit_capacity_ratio != _min_row_decimal(
        report.rows,
        "exit_capacity_ratio",
    ):
        raise ValueError("min_exit_capacity_ratio must match rows")
    if report.max_settlement_ambiguity_score != _max_row_decimal(
        report.rows,
        "settlement_ambiguity_score",
    ):
        raise ValueError("max_settlement_ambiguity_score must match rows")
    if report.min_expected_edge_after_paper_cost != _min_row_decimal(
        report.rows,
        "expected_edge_after_paper_cost",
    ):
        raise ValueError("min_expected_edge_after_paper_cost must match rows")
    if report.status != _report_status(report.rows):
        raise ValueError("status must match rows")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")
    if report.rows != tuple(sorted(report.rows, key=_row_sort_key)):
        raise ValueError("rows must be sorted")
    if report.report_digest != _report_digest_from_report(report):
        raise ValueError("report_digest must match report inputs")


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be exactly datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if getattr(value, field_name) is not True:
            raise ValueError(f"{field_name} must be True for {label}")


def _require_member(field_name: str, value: object, values: tuple[str, ...]) -> None:
    if type(value) is not str or value not in values:
        raise ValueError(f"{field_name} must be one of {values}")


def _require_bool(field_name: str, value: object) -> None:
    if type(value) is not bool:
        raise ValueError(f"{field_name} must be a bool")


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str or not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical string")


def _require_public_text(field_name: str, value: object) -> None:
    _require_canonical_string(field_name, value)
    _reject_unsafe_public_text(value)


def _require_redacted_reference(value: object) -> None:
    if type(value) is not str:
        raise ValueError("redacted_candidate_reference must be a string")
    prefix = "candidate_ref_"
    digest = value.removeprefix(prefix)
    if (
        value.startswith(prefix)
        and len(digest) == 16
        and all(character in "0123456789abcdef" for character in digest)
    ):
        return
    raise ValueError("redacted_candidate_reference must be a redacted candidate reference")


def _normalize_reason_codes(
    values: object,
    *,
    require_nonempty: bool,
) -> tuple[str, ...]:
    if type(values) is not tuple:
        raise ValueError("reason_codes must be a tuple")
    reason_codes = tuple(values)
    if require_nonempty and not reason_codes:
        raise ValueError("reason_codes is required")
    seen: set[str] = set()
    for reason_code in reason_codes:
        _require_canonical_reason_code("reason_codes", reason_code)
        if reason_code in seen:
            raise ValueError("reason_codes must be unique")
        seen.add(reason_code)
    return reason_codes


def _unique_reason_codes(values: tuple[str, ...]) -> tuple[str, ...]:
    seen: set[str] = set()
    unique: list[str] = []
    for value in values:
        if value not in seen:
            unique.append(value)
            seen.add(value)
    return _normalize_reason_codes(tuple(unique), require_nonempty=True)


def _require_canonical_reason_code(field_name: str, value: object) -> None:
    if type(value) is not str or not value:
        raise ValueError(f"{field_name} must contain canonical reason codes")
    if value != value.lower() or value.strip() != value:
        raise ValueError(f"{field_name} must contain canonical reason codes")
    for part in value.split("_"):
        if not part or not part.isalnum() or part != part.lower():
            raise ValueError(f"{field_name} must contain canonical reason codes")
    _reject_unsafe_public_text(value)


def _normalize_ratio(field_name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized < ZERO or normalized > Decimal("1.000000"):
        raise ValueError(f"{field_name} must be between 0 and 1")
    return normalized


def _normalize_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _normalize_count_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    if value != value.to_integral_value():
        raise ValueError(f"{field_name} must be a whole Decimal")
    if value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return value


def _normalize_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    if value.as_tuple().exponent < QUANTUM.as_tuple().exponent:
        raise ValueError(f"{field_name} must not exceed six decimal places")
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(QUANTUM)


def _count_decimal(value: int) -> Decimal:
    return Decimal(value)


def _redacted_reference(value: str) -> str:
    digest = sha256(value.encode("utf-8")).hexdigest()[:16]
    return f"candidate_ref_{digest}"


def _row_digest_from_row(
    row: StrategyRecommendationMarketCloseReadinessGateV2Row,
) -> str:
    return _row_digest(
        redacted_candidate_reference=row.redacted_candidate_reference,
        market_slug=row.market_slug,
        evaluated_at=row.evaluated_at,
        recommendation_intent=row.recommendation_intent,
        minutes_to_close=row.minutes_to_close,
        official_result_lag_minutes=row.official_result_lag_minutes,
        source_contradiction_score=row.source_contradiction_score,
        exit_capacity_ratio=row.exit_capacity_ratio,
        settlement_ambiguity_score=row.settlement_ambiguity_score,
        expected_edge_after_paper_cost=row.expected_edge_after_paper_cost,
        close_readiness_status=row.close_readiness_status,
        safe_to_keep=row.safe_to_keep,
        safe_to_enter=row.safe_to_enter,
        reason_codes=row.reason_codes,
    )


def _row_digest(
    *,
    redacted_candidate_reference: str,
    market_slug: str,
    evaluated_at: datetime,
    recommendation_intent: str,
    minutes_to_close: Decimal,
    official_result_lag_minutes: Decimal,
    source_contradiction_score: Decimal,
    exit_capacity_ratio: Decimal,
    settlement_ambiguity_score: Decimal,
    expected_edge_after_paper_cost: Decimal,
    close_readiness_status: str,
    safe_to_keep: bool,
    safe_to_enter: bool,
    reason_codes: tuple[str, ...],
) -> str:
    parts = (
        redacted_candidate_reference,
        market_slug,
        _as_utc("evaluated_at", evaluated_at).isoformat(),
        recommendation_intent,
        str(minutes_to_close),
        str(official_result_lag_minutes),
        str(source_contradiction_score),
        str(exit_capacity_ratio),
        str(settlement_ambiguity_score),
        str(expected_edge_after_paper_cost),
        close_readiness_status,
        str(safe_to_keep),
        str(safe_to_enter),
        ",".join(reason_codes),
    )
    return f"market_close_row_digest_{_digest(parts)}"


def _report_digest_from_report(
    report: StrategyRecommendationMarketCloseReadinessGateV2Report,
) -> str:
    return _report_digest(
        generated_at=report.generated_at,
        config_version=report.config_version,
        candidate_count=report.candidate_count,
        ready_count=report.ready_count,
        watch_count=report.watch_count,
        blocked_count=report.blocked_count,
        enter_safe_count=report.enter_safe_count,
        keep_safe_count=report.keep_safe_count,
        status=report.status,
        reason_codes=report.reason_codes,
        rows=report.rows,
    )


def _report_digest(
    *,
    generated_at: datetime,
    config_version: str,
    candidate_count: Decimal,
    ready_count: Decimal,
    watch_count: Decimal,
    blocked_count: Decimal,
    enter_safe_count: Decimal,
    keep_safe_count: Decimal,
    status: str,
    reason_codes: tuple[str, ...],
    rows: tuple[StrategyRecommendationMarketCloseReadinessGateV2Row, ...],
) -> str:
    parts = (
        _as_utc("generated_at", generated_at).isoformat(),
        config_version,
        str(candidate_count),
        str(ready_count),
        str(watch_count),
        str(blocked_count),
        str(enter_safe_count),
        str(keep_safe_count),
        status,
        ",".join(reason_codes),
        ",".join(row.readiness_digest for row in rows),
    )
    return f"market_close_report_digest_{_digest(parts)}"


def _digest(parts: tuple[str, ...]) -> str:
    payload = "\x1f".join(parts)
    return sha256(payload.encode("utf-8")).hexdigest()[:16]


def _payload_value(value: Any) -> Any:
    if value is None:
        return None
    if type(value) is bool:
        return value
    if type(value) in (float, int):
        raise ValueError("public payload numeric values must be Decimal strings")
    if type(value) is Decimal:
        if not value.is_finite():
            raise ValueError("public payload Decimal must be finite")
        return str(value)
    if type(value) is datetime:
        return _as_utc("payload datetime", value).isoformat()
    if type(value) is str:
        _reject_unsafe_public_text(value)
        return value
    if is_dataclass(value) and not isinstance(value, type):
        _require_hard_flags(type(value).__name__, value)
        return _payload_mapping(vars(value))
    if type(value) is dict:
        return _payload_mapping(value)
    if type(value) in (list, tuple):
        return [_payload_value(item) for item in value]
    raise ValueError("public payload value is not serializable")


def _payload_mapping(value: dict[Any, Any]) -> dict[str, Any]:
    payload: dict[str, Any] = {}
    for key, item in value.items():
        if type(key) is not str:
            raise ValueError("public payload keys must be strings")
        if key.startswith("_"):
            continue
        _reject_unsafe_public_text(key)
        payload[key] = _payload_value(item)
    return payload


def _reject_unsafe_public_text(value: str) -> None:
    lowered = value.lower()
    if any(fragment in lowered for fragment in SENSITIVE_PUBLIC_TEXT):
        raise ValueError("unsafe public text")


__all__ = (
    "DEFAULT_STRATEGY_RECOMMENDATION_MARKET_CLOSE_READINESS_GATE_V2_CONFIG_VERSION",
    "StrategyRecommendationMarketCloseReadinessGateV2Candidate",
    "StrategyRecommendationMarketCloseReadinessGateV2Config",
    "StrategyRecommendationMarketCloseReadinessGateV2Report",
    "StrategyRecommendationMarketCloseReadinessGateV2Row",
    "build_strategy_recommendation_market_close_readiness_gate_v2",
    "strategy_recommendation_market_close_readiness_gate_v2_payload",
)
