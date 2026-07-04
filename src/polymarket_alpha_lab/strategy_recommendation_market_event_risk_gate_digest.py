"""Pure Phase 1 report reducer for recommendation event-risk gating."""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable
from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from typing import Any

from polymarket_alpha_lab.team_paper_guard import (
    json_ready_no_floats,
    require_paper_only_flags,
)


DEFAULT_STRATEGY_RECOMMENDATION_MARKET_EVENT_RISK_GATE_DIGEST_CONFIG_VERSION = (
    "strategy-recommendation-market-event-risk-gate-digest-v0"
)
REDACTED_EVENT_REFERENCE = "<redacted-event-risk-reference>"

QUANTUM = Decimal("0.000001")
COUNT_QUANTUM = Decimal("1")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
SIGNAL_COUNT = Decimal("5")
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)

SELECTED_SIDES = ("yes", "no")
GATE_STATUSES = ("paper_candidate", "paper_watch", "blocked")
REPORT_STATUSES = ("clear", "watch", "blocked")
STATUS_RANK = {
    "blocked": Decimal("0"),
    "paper_watch": Decimal("1"),
    "paper_candidate": Decimal("2"),
}
PASS_REASON = "market_event_risk_gate_passed"
CLEAR_REASON = "market_event_risk_gate_clear"
GENERATED_RISK_REASONS = frozenset(
    (
        "event_cluster_correlation_blocked",
        "event_cluster_correlation_watch",
        "event_risk_score_blocked",
        "event_risk_score_watch",
        "market_event_dependency_blocked",
        "market_event_dependency_watch",
        "outcome_lag_signal_blocked",
        "outcome_lag_signal_watch",
        "resolution_ambiguity_blocked",
        "resolution_ambiguity_watch",
        "source_conflict_blocked",
        "source_conflict_watch",
    ),
)
SENSITIVE_TEXT_FRAGMENTS = (
    "sec" + "ret",
    "tok" + "en",
    "creden" + "tial",
    "pass" + "word",
    "post" + "gres://",
    "post" + "gresql://",
    "supa" + "base",
    "priv" + "ate_key",
    "priv" + "ate-key",
    "api" + "_key",
    "bearer ",
    "wall" + "et",
    "ord" + "er",
    "can" + "cel",
    "repl" + "ace",
    "au" + "th",
)
SENSITIVE_TEXT_MARKERS = ("://", "@")


@dataclass(frozen=True)
class StrategyRecommendationMarketEventRiskGateDigestConfig:
    config_version: str = (
        DEFAULT_STRATEGY_RECOMMENDATION_MARKET_EVENT_RISK_GATE_DIGEST_CONFIG_VERSION
    )
    event_risk_watch_score: Decimal = Decimal("0.400000")
    event_risk_block_score: Decimal = Decimal("0.700000")
    max_event_cluster_correlation: Decimal = Decimal("0.800000")
    max_market_event_dependency: Decimal = Decimal("0.750000")
    max_resolution_ambiguity: Decimal = Decimal("0.650000")
    max_source_conflict: Decimal = Decimal("0.600000")
    max_outcome_lag_signal: Decimal = Decimal("0.550000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not StrategyRecommendationMarketEventRiskGateDigestConfig:
            raise ValueError(
                "config must be a StrategyRecommendationMarketEventRiskGateDigestConfig",
            )
        _require_public_string("config_version", self.config_version)
        for field_name in (
            "event_risk_watch_score",
            "event_risk_block_score",
            "max_event_cluster_correlation",
            "max_market_event_dependency",
            "max_resolution_ambiguity",
            "max_source_conflict",
            "max_outcome_lag_signal",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        if self.event_risk_watch_score > self.event_risk_block_score:
            raise ValueError(
                "event_risk_watch_score must be less than or equal to event_risk_block_score",
            )
        require_paper_only_flags("config", self)


@dataclass(frozen=True)
class StrategyRecommendationMarketEventRiskGateInput:
    candidate_id: str
    recommendation_id: str
    market_slug: str
    selected_side: str
    event_cluster_id: str
    risk_observed_at: datetime
    event_cluster_correlation: Decimal
    market_event_dependency: Decimal
    resolution_ambiguity: Decimal
    source_conflict: Decimal
    outcome_lag_signal: Decimal
    event_reference: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not StrategyRecommendationMarketEventRiskGateInput:
            raise ValueError(
                "candidate must be a StrategyRecommendationMarketEventRiskGateInput",
            )
        for field_name in (
            "candidate_id",
            "recommendation_id",
            "market_slug",
            "event_cluster_id",
        ):
            _require_public_string(field_name, getattr(self, field_name))
        _require_member("selected_side", self.selected_side, SELECTED_SIDES)
        object.__setattr__(
            self,
            "risk_observed_at",
            _as_utc("risk_observed_at", self.risk_observed_at),
        )
        for field_name in (
            "event_cluster_correlation",
            "market_event_dependency",
            "resolution_ambiguity",
            "source_conflict",
            "outcome_lag_signal",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "event_reference",
            _redact_event_reference(self.event_reference),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        require_paper_only_flags("candidate", self)


@dataclass(frozen=True)
class StrategyRecommendationMarketEventRiskGateRow:
    candidate_id: str
    recommendation_id: str
    market_slug: str
    selected_side: str
    event_cluster_id: str
    risk_observed_at: datetime
    event_cluster_correlation: Decimal
    market_event_dependency: Decimal
    resolution_ambiguity: Decimal
    source_conflict: Decimal
    outcome_lag_signal: Decimal
    event_risk_score: Decimal
    gate_status: str
    event_reference: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not StrategyRecommendationMarketEventRiskGateRow:
            raise ValueError("row must be a StrategyRecommendationMarketEventRiskGateRow")
        for field_name in (
            "candidate_id",
            "recommendation_id",
            "market_slug",
            "event_cluster_id",
        ):
            _require_public_string(field_name, getattr(self, field_name))
        _require_member("selected_side", self.selected_side, SELECTED_SIDES)
        object.__setattr__(
            self,
            "risk_observed_at",
            _as_utc("risk_observed_at", self.risk_observed_at),
        )
        for field_name in (
            "event_cluster_correlation",
            "market_event_dependency",
            "resolution_ambiguity",
            "source_conflict",
            "outcome_lag_signal",
            "event_risk_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        _require_member("gate_status", self.gate_status, GATE_STATUSES)
        object.__setattr__(
            self,
            "event_reference",
            _redact_event_reference(self.event_reference),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        _validate_row(self)
        require_paper_only_flags("row", self)


@dataclass(frozen=True)
class StrategyRecommendationMarketEventRiskGateReasonCodeCount:
    reason_code: str
    count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not StrategyRecommendationMarketEventRiskGateReasonCodeCount:
            raise ValueError(
                "reason count must be a StrategyRecommendationMarketEventRiskGateReasonCodeCount",
            )
        _require_public_string("reason_code", self.reason_code)
        object.__setattr__(
            self,
            "count",
            _normalize_positive_count("count", self.count),
        )
        require_paper_only_flags("reason count", self)


@dataclass(frozen=True)
class StrategyRecommendationMarketEventRiskGateReport:
    generated_at: datetime
    config_version: str
    candidate_count: Decimal
    paper_candidate_count: Decimal
    watch_candidate_count: Decimal
    blocked_candidate_count: Decimal
    max_event_risk_score: Decimal
    max_event_cluster_correlation: Decimal
    max_market_event_dependency: Decimal
    max_resolution_ambiguity: Decimal
    max_source_conflict: Decimal
    max_outcome_lag_signal: Decimal
    status: str
    reason_codes: tuple[str, ...]
    reason_code_counts: tuple[StrategyRecommendationMarketEventRiskGateReasonCodeCount, ...]
    rows: tuple[StrategyRecommendationMarketEventRiskGateRow, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not StrategyRecommendationMarketEventRiskGateReport:
            raise ValueError(
                "report must be a StrategyRecommendationMarketEventRiskGateReport",
            )
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_string("config_version", self.config_version)
        for field_name in (
            "candidate_count",
            "paper_candidate_count",
            "watch_candidate_count",
            "blocked_candidate_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_count(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "max_event_risk_score",
            "max_event_cluster_correlation",
            "max_market_event_dependency",
            "max_resolution_ambiguity",
            "max_source_conflict",
            "max_outcome_lag_signal",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        _require_member("status", self.status, REPORT_STATUSES)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_report_reason_codes(self.reason_codes),
        )
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        _validate_report(self)
        require_paper_only_flags("report", self)


def build_strategy_recommendation_market_event_risk_gate_digest(
    candidates: Iterable[StrategyRecommendationMarketEventRiskGateInput],
    *,
    config: StrategyRecommendationMarketEventRiskGateDigestConfig,
    generated_at: datetime,
) -> StrategyRecommendationMarketEventRiskGateReport:
    if type(config) is not StrategyRecommendationMarketEventRiskGateDigestConfig:
        raise ValueError(
            "config must be a StrategyRecommendationMarketEventRiskGateDigestConfig",
        )
    require_paper_only_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    inputs = _normalize_inputs(candidates)
    _reject_future_inputs(inputs, generated_at_utc)
    rows = tuple(
        sorted(
            (_row_from_input(candidate, config=config) for candidate in inputs),
            key=_row_sort_key,
        ),
    )
    return StrategyRecommendationMarketEventRiskGateReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        candidate_count=_count(len(rows)),
        paper_candidate_count=_status_count(rows, "paper_candidate"),
        watch_candidate_count=_status_count(rows, "paper_watch"),
        blocked_candidate_count=_status_count(rows, "blocked"),
        max_event_risk_score=_max_decimal(row.event_risk_score for row in rows),
        max_event_cluster_correlation=_max_decimal(
            row.event_cluster_correlation for row in rows
        ),
        max_market_event_dependency=_max_decimal(
            row.market_event_dependency for row in rows
        ),
        max_resolution_ambiguity=_max_decimal(row.resolution_ambiguity for row in rows),
        max_source_conflict=_max_decimal(row.source_conflict for row in rows),
        max_outcome_lag_signal=_max_decimal(row.outcome_lag_signal for row in rows),
        status=_report_status(rows),
        reason_codes=_report_reason_codes(rows),
        reason_code_counts=_reason_code_counts(rows),
        rows=rows,
    )


def strategy_recommendation_market_event_risk_gate_digest_payload(
    report: StrategyRecommendationMarketEventRiskGateReport,
) -> dict[str, Any]:
    if type(report) is not StrategyRecommendationMarketEventRiskGateReport:
        raise ValueError(
            "report must be a StrategyRecommendationMarketEventRiskGateReport",
        )
    require_paper_only_flags("report", report)
    payload = json_ready_no_floats(report)
    if type(payload) is not dict:
        raise ValueError("report must serialize to a JSON object")
    return payload


def _row_from_input(
    candidate: StrategyRecommendationMarketEventRiskGateInput,
    *,
    config: StrategyRecommendationMarketEventRiskGateDigestConfig,
) -> StrategyRecommendationMarketEventRiskGateRow:
    event_risk_score = _event_risk_score(candidate)
    risk_reasons = _risk_reason_codes(
        candidate=candidate,
        event_risk_score=event_risk_score,
        config=config,
    )
    reason_codes = _normalize_reason_codes(
        "reason_codes",
        candidate.reason_codes
        + risk_reasons
        + (() if risk_reasons else (PASS_REASON,)),
    )
    return StrategyRecommendationMarketEventRiskGateRow(
        candidate_id=candidate.candidate_id,
        recommendation_id=candidate.recommendation_id,
        market_slug=candidate.market_slug,
        selected_side=candidate.selected_side,
        event_cluster_id=candidate.event_cluster_id,
        risk_observed_at=candidate.risk_observed_at,
        event_cluster_correlation=candidate.event_cluster_correlation,
        market_event_dependency=candidate.market_event_dependency,
        resolution_ambiguity=candidate.resolution_ambiguity,
        source_conflict=candidate.source_conflict,
        outcome_lag_signal=candidate.outcome_lag_signal,
        event_risk_score=event_risk_score,
        gate_status=_gate_status(reason_codes),
        event_reference=candidate.event_reference,
        reason_codes=reason_codes,
    )


def _event_risk_score(candidate: StrategyRecommendationMarketEventRiskGateInput) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return _quantize(
            (
                candidate.event_cluster_correlation
                + candidate.market_event_dependency
                + candidate.resolution_ambiguity
                + candidate.source_conflict
                + candidate.outcome_lag_signal
            )
            / SIGNAL_COUNT,
        )


def _risk_reason_codes(
    *,
    candidate: StrategyRecommendationMarketEventRiskGateInput,
    event_risk_score: Decimal,
    config: StrategyRecommendationMarketEventRiskGateDigestConfig,
) -> tuple[str, ...]:
    reasons: list[str] = []
    _append_score_reason(
        reasons,
        "event_risk_score",
        event_risk_score,
        config.event_risk_watch_score,
        config.event_risk_block_score,
    )
    _append_signal_reason(
        reasons,
        "event_cluster_correlation",
        candidate.event_cluster_correlation,
        config.event_risk_watch_score,
        config.max_event_cluster_correlation,
    )
    _append_signal_reason(
        reasons,
        "market_event_dependency",
        candidate.market_event_dependency,
        config.event_risk_watch_score,
        config.max_market_event_dependency,
    )
    _append_signal_reason(
        reasons,
        "resolution_ambiguity",
        candidate.resolution_ambiguity,
        config.event_risk_watch_score,
        config.max_resolution_ambiguity,
    )
    _append_signal_reason(
        reasons,
        "source_conflict",
        candidate.source_conflict,
        config.event_risk_watch_score,
        config.max_source_conflict,
    )
    _append_signal_reason(
        reasons,
        "outcome_lag_signal",
        candidate.outcome_lag_signal,
        config.event_risk_watch_score,
        config.max_outcome_lag_signal,
    )
    return _normalize_reason_codes("risk reason_codes", tuple(reasons), allow_empty=True)


def _append_score_reason(
    reasons: list[str],
    prefix: str,
    value: Decimal,
    watch_threshold: Decimal,
    block_threshold: Decimal,
) -> None:
    if value >= block_threshold:
        reasons.append(f"{prefix}_blocked")
    elif value >= watch_threshold:
        reasons.append(f"{prefix}_watch")


def _append_signal_reason(
    reasons: list[str],
    prefix: str,
    value: Decimal,
    watch_threshold: Decimal,
    block_threshold: Decimal,
) -> None:
    if value >= block_threshold:
        reasons.append(f"{prefix}_blocked")
    elif value >= watch_threshold:
        reasons.append(f"{prefix}_watch")


def _gate_status(reason_codes: tuple[str, ...]) -> str:
    if any(reason.endswith("_blocked") for reason in reason_codes):
        return "blocked"
    if any(reason.endswith("_watch") for reason in reason_codes):
        return "paper_watch"
    return "paper_candidate"


def _report_status(
    rows: tuple[StrategyRecommendationMarketEventRiskGateRow, ...],
) -> str:
    if any(row.gate_status == "blocked" for row in rows):
        return "blocked"
    if any(row.gate_status == "paper_watch" for row in rows):
        return "watch"
    return "clear"


def _report_reason_codes(
    rows: tuple[StrategyRecommendationMarketEventRiskGateRow, ...],
) -> tuple[str, ...]:
    risk_reasons = tuple(
        sorted(
            {
                reason
                for row in rows
                for reason in row.reason_codes
                if reason in GENERATED_RISK_REASONS
            },
        ),
    )
    if risk_reasons:
        return risk_reasons
    return (CLEAR_REASON,)


def _reason_code_counts(
    rows: tuple[StrategyRecommendationMarketEventRiskGateRow, ...],
) -> tuple[StrategyRecommendationMarketEventRiskGateReasonCodeCount, ...]:
    counter: Counter[str] = Counter()
    for row in rows:
        counter.update(row.reason_codes)
    return tuple(
        StrategyRecommendationMarketEventRiskGateReasonCodeCount(
            reason_code=reason_code,
            count=_count(count),
        )
        for reason_code, count in sorted(counter.items(), key=lambda item: (-item[1], item[0]))
    )


def _normalize_inputs(
    candidates: Iterable[StrategyRecommendationMarketEventRiskGateInput],
) -> tuple[StrategyRecommendationMarketEventRiskGateInput, ...]:
    if isinstance(candidates, (str, bytes)):
        raise ValueError("candidates must be an iterable")
    try:
        rows = tuple(candidates)
    except TypeError as exc:
        raise ValueError("candidates must be an iterable") from exc
    seen_recommendation_ids: set[str] = set()
    for row in rows:
        if type(row) is not StrategyRecommendationMarketEventRiskGateInput:
            raise ValueError(
                "candidates must contain StrategyRecommendationMarketEventRiskGateInput values",
            )
        require_paper_only_flags("candidate", row)
        if row.recommendation_id in seen_recommendation_ids:
            raise ValueError("candidates must not contain duplicate recommendation_id values")
        seen_recommendation_ids.add(row.recommendation_id)
    return rows


def _reject_future_inputs(
    candidates: tuple[StrategyRecommendationMarketEventRiskGateInput, ...],
    generated_at: datetime,
) -> None:
    for candidate in candidates:
        if candidate.risk_observed_at > generated_at:
            raise ValueError("risk_observed_at must not be after generated_at")


def _normalize_rows(
    rows: Iterable[StrategyRecommendationMarketEventRiskGateRow],
) -> tuple[StrategyRecommendationMarketEventRiskGateRow, ...]:
    if isinstance(rows, (str, bytes)):
        raise ValueError("rows must be an iterable")
    try:
        normalized = tuple(rows)
    except TypeError as exc:
        raise ValueError("rows must be an iterable") from exc
    seen_recommendation_ids: set[str] = set()
    for row in normalized:
        if type(row) is not StrategyRecommendationMarketEventRiskGateRow:
            raise ValueError(
                "rows must contain StrategyRecommendationMarketEventRiskGateRow values",
            )
        require_paper_only_flags("row", row)
        if row.recommendation_id in seen_recommendation_ids:
            raise ValueError("rows must not contain duplicate recommendation_id values")
        seen_recommendation_ids.add(row.recommendation_id)
    if normalized != tuple(sorted(normalized, key=_row_sort_key)):
        raise ValueError("rows must use deterministic sort")
    return normalized


def _normalize_reason_code_counts(
    rows: Iterable[StrategyRecommendationMarketEventRiskGateReasonCodeCount],
) -> tuple[StrategyRecommendationMarketEventRiskGateReasonCodeCount, ...]:
    if isinstance(rows, (str, bytes)):
        raise ValueError("reason_code_counts must be an iterable")
    try:
        normalized = tuple(rows)
    except TypeError as exc:
        raise ValueError("reason_code_counts must be an iterable") from exc
    seen: set[str] = set()
    for row in normalized:
        if type(row) is not StrategyRecommendationMarketEventRiskGateReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain StrategyRecommendationMarketEventRiskGateReasonCodeCount values",
            )
        require_paper_only_flags("reason count", row)
        if row.reason_code in seen:
            raise ValueError("reason_code_counts must not contain duplicate values")
        seen.add(row.reason_code)
    if normalized != tuple(sorted(normalized, key=lambda row: (-row.count, row.reason_code))):
        raise ValueError("reason_code_counts must use deterministic sort")
    return normalized


def _validate_row(row: StrategyRecommendationMarketEventRiskGateRow) -> None:
    expected_score = _quantize(
        (
            row.event_cluster_correlation
            + row.market_event_dependency
            + row.resolution_ambiguity
            + row.source_conflict
            + row.outcome_lag_signal
        )
        / SIGNAL_COUNT,
    )
    if row.event_risk_score != expected_score:
        raise ValueError("event_risk_score must match event risk signals")
    if row.gate_status != _gate_status(row.reason_codes):
        raise ValueError("gate_status must match reason_codes")
    if row.event_reference != REDACTED_EVENT_REFERENCE:
        raise ValueError("event_reference must be redacted")


def _validate_report(report: StrategyRecommendationMarketEventRiskGateReport) -> None:
    rows = report.rows
    if report.candidate_count != _count(len(rows)):
        raise ValueError("candidate_count must match rows")
    if report.paper_candidate_count != _status_count(rows, "paper_candidate"):
        raise ValueError("paper_candidate_count must match rows")
    if report.watch_candidate_count != _status_count(rows, "paper_watch"):
        raise ValueError("watch_candidate_count must match rows")
    if report.blocked_candidate_count != _status_count(rows, "blocked"):
        raise ValueError("blocked_candidate_count must match rows")
    if report.candidate_count != (
        report.paper_candidate_count
        + report.watch_candidate_count
        + report.blocked_candidate_count
    ):
        raise ValueError("candidate_count must match status counts")
    if report.max_event_risk_score != _max_decimal(row.event_risk_score for row in rows):
        raise ValueError("max_event_risk_score must match rows")
    if report.max_event_cluster_correlation != _max_decimal(
        row.event_cluster_correlation for row in rows
    ):
        raise ValueError("max_event_cluster_correlation must match rows")
    if report.max_market_event_dependency != _max_decimal(
        row.market_event_dependency for row in rows
    ):
        raise ValueError("max_market_event_dependency must match rows")
    if report.max_resolution_ambiguity != _max_decimal(
        row.resolution_ambiguity for row in rows
    ):
        raise ValueError("max_resolution_ambiguity must match rows")
    if report.max_source_conflict != _max_decimal(row.source_conflict for row in rows):
        raise ValueError("max_source_conflict must match rows")
    if report.max_outcome_lag_signal != _max_decimal(row.outcome_lag_signal for row in rows):
        raise ValueError("max_outcome_lag_signal must match rows")
    if report.status != _report_status(rows):
        raise ValueError("status must match rows")
    if report.reason_codes != _report_reason_codes(rows):
        raise ValueError("reason_codes must match rows")
    if report.reason_code_counts != _reason_code_counts(rows):
        raise ValueError("reason_code_counts must match rows")


def _row_sort_key(
    row: StrategyRecommendationMarketEventRiskGateRow,
) -> tuple[Decimal, Decimal, Decimal, str, str]:
    return (
        STATUS_RANK[row.gate_status],
        -_reason_suffix_count(row, "_blocked"),
        -row.event_risk_score,
        row.candidate_id,
        row.recommendation_id,
    )


def _reason_suffix_count(
    row: StrategyRecommendationMarketEventRiskGateRow,
    suffix: str,
) -> Decimal:
    return _count(sum(1 for reason in row.reason_codes if reason.endswith(suffix)))


def _status_count(
    rows: tuple[StrategyRecommendationMarketEventRiskGateRow, ...],
    status: str,
) -> Decimal:
    return _count(sum(1 for row in rows if row.gate_status == status))


def _max_decimal(values: Iterable[Decimal]) -> Decimal:
    items = tuple(values)
    if not items:
        return ZERO
    return max(items)


def _count(value: int) -> Decimal:
    if type(value) is not int or value < 0:
        raise ValueError("count must be a nonnegative int")
    return Decimal(value).quantize(COUNT_QUANTUM)


def _normalize_report_reason_codes(value: object) -> tuple[str, ...]:
    reason_codes = _normalize_reason_codes("reason_codes", value)
    if reason_codes == (CLEAR_REASON,):
        return reason_codes
    for reason_code in reason_codes:
        if reason_code not in GENERATED_RISK_REASONS:
            raise ValueError("reason_codes must contain only event risk gate reasons")
    return reason_codes


def _normalize_reason_codes(
    field_name: str,
    value: object,
    *,
    allow_empty: bool = False,
) -> tuple[str, ...]:
    if type(value) not in (list, tuple):
        raise ValueError(f"{field_name} must be a list or tuple")
    reason_codes = tuple(value)
    if not allow_empty and not reason_codes:
        raise ValueError(f"{field_name} must not be empty")
    for reason_code in reason_codes:
        _require_public_string(field_name, reason_code)
    if len(reason_codes) != len(set(reason_codes)):
        raise ValueError(f"{field_name} must not contain duplicate values")
    return tuple(sorted(reason_codes))


def _normalize_positive_count(field_name: str, value: object) -> Decimal:
    normalized = _normalize_nonnegative_count(field_name, value)
    if normalized <= Decimal("0"):
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _normalize_nonnegative_count(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    quantized = value.quantize(COUNT_QUANTUM)
    if quantized != value:
        raise ValueError(f"{field_name} must be integral")
    if quantized < Decimal("0"):
        raise ValueError(f"{field_name} must be nonnegative")
    return quantized


def _normalize_probability(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    with localcontext(DECIMAL_CONTEXT):
        quantized = value.quantize(QUANTUM)
    if quantized < ZERO or quantized > ONE:
        raise ValueError(f"{field_name} must be between zero and one")
    return quantized


def _quantize(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(QUANTUM)


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _redact_event_reference(value: object) -> str:
    _require_canonical_string("event_reference", value)
    return REDACTED_EVENT_REFERENCE


def _require_member(field_name: str, value: object, allowed: tuple[str, ...]) -> None:
    if type(value) is not str or value not in allowed:
        raise ValueError(f"{field_name} must be one of {allowed}")


def _require_public_string(field_name: str, value: object) -> None:
    _require_canonical_string(field_name, value)
    assert type(value) is str
    lowered = value.lower()
    if any(fragment in lowered for fragment in SENSITIVE_TEXT_FRAGMENTS):
        raise ValueError(f"{field_name} must not expose sensitive text")
    if all(marker in value for marker in SENSITIVE_TEXT_MARKERS):
        raise ValueError(f"{field_name} must not expose sensitive text")


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")
    if any(character.isspace() for character in value):
        raise ValueError(f"{field_name} must not contain whitespace")


__all__ = (
    "DEFAULT_STRATEGY_RECOMMENDATION_MARKET_EVENT_RISK_GATE_DIGEST_CONFIG_VERSION",
    "StrategyRecommendationMarketEventRiskGateDigestConfig",
    "StrategyRecommendationMarketEventRiskGateInput",
    "StrategyRecommendationMarketEventRiskGateReasonCodeCount",
    "StrategyRecommendationMarketEventRiskGateReport",
    "StrategyRecommendationMarketEventRiskGateRow",
    "build_strategy_recommendation_market_event_risk_gate_digest",
    "strategy_recommendation_market_event_risk_gate_digest_payload",
)
