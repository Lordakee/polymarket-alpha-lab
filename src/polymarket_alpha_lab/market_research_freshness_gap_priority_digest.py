"""Report-only diagnostics for market research freshness gap priority."""

from __future__ import annotations

from dataclasses import dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any


DEFAULT_MARKET_RESEARCH_FRESHNESS_GAP_PRIORITY_DIGEST_CONFIG_VERSION = (
    "market-research-freshness-gap-priority-digest-v0"
)

QUANTUM = Decimal("0.000001")
ZERO = Decimal("0")
ONE = Decimal("1")

PRIORITY_STATUSES = ("blocked", "watch", "ready")
DIGEST_STATUSES = ("blocked", "watch", "pass", "no_inputs")
ROW_REASON_CODES = (
    "latest_source_stale",
    "evidence_stale",
    "forecast_stale",
    "probability_movement_high",
    "quorum_share_low",
    "freshness_gap_watch",
    "freshness_gap_ready",
)
DIGEST_REASON_CODES = (
    "freshness_gap_blocked_markets_present",
    "freshness_gap_watch_markets_present",
    "latest_source_stale_detected",
    "evidence_stale_detected",
    "forecast_stale_detected",
    "probability_movement_detected",
    "quorum_share_low_detected",
    "freshness_gap_digest_passed",
    "freshness_gap_no_inputs",
)

UNSAFE_REF_FRAGMENTS = (
    "auth",
    "private",
    "secret",
    "token",
    "wallet",
    "account",
    "order",
)

__all__ = (
    "DEFAULT_MARKET_RESEARCH_FRESHNESS_GAP_PRIORITY_DIGEST_CONFIG_VERSION",
    "MarketResearchFreshnessGapPriorityDigestConfig",
    "MarketResearchFreshnessGapPriorityDigestInput",
    "MarketResearchFreshnessGapPriorityDigestReasonCodeCount",
    "MarketResearchFreshnessGapPriorityDigestReport",
    "MarketResearchFreshnessGapPriorityDigestRow",
    "build_market_research_freshness_gap_priority_digest",
    "market_research_freshness_gap_priority_digest_payload",
)


@dataclass(frozen=True)
class MarketResearchFreshnessGapPriorityDigestConfig:
    config_version: str = (
        DEFAULT_MARKET_RESEARCH_FRESHNESS_GAP_PRIORITY_DIGEST_CONFIG_VERSION
    )
    source_age_blocked_threshold_hours: Decimal = Decimal("24.000000")
    evidence_age_blocked_threshold_hours: Decimal = Decimal("36.000000")
    forecast_age_blocked_threshold_hours: Decimal = Decimal("30.000000")
    probability_movement_blocked_threshold: Decimal = Decimal("0.150000")
    quorum_share_blocked_threshold: Decimal = Decimal("0.500000")
    source_age_watch_threshold_hours: Decimal = Decimal("12.000000")
    evidence_age_watch_threshold_hours: Decimal = Decimal("24.000000")
    forecast_age_watch_threshold_hours: Decimal = Decimal("24.000000")
    probability_movement_watch_threshold: Decimal = Decimal("0.075000")
    quorum_share_watch_threshold: Decimal = Decimal("0.750000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketResearchFreshnessGapPriorityDigestConfig:
            raise ValueError(
                "config must be exactly MarketResearchFreshnessGapPriorityDigestConfig",
            )

    def __post_init__(self) -> None:
        if type(self) is not MarketResearchFreshnessGapPriorityDigestConfig:
            raise ValueError(
                "config must be exactly MarketResearchFreshnessGapPriorityDigestConfig",
            )
        _require_canonical_string("config_version", self.config_version)
        for field_name in (
            "source_age_blocked_threshold_hours",
            "evidence_age_blocked_threshold_hours",
            "forecast_age_blocked_threshold_hours",
            "source_age_watch_threshold_hours",
            "evidence_age_watch_threshold_hours",
            "forecast_age_watch_threshold_hours",
        ):
            object.__setattr__(
                self,
                field_name,
                _quantize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "probability_movement_blocked_threshold",
            "quorum_share_blocked_threshold",
            "probability_movement_watch_threshold",
            "quorum_share_watch_threshold",
        ):
            object.__setattr__(
                self,
                field_name,
                _quantize_ratio_decimal(field_name, getattr(self, field_name)),
            )
        _validate_thresholds(self)
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class MarketResearchFreshnessGapPriorityDigestInput:
    market_ref: str
    research_topic: str
    team_id: str
    latest_source_at: datetime
    latest_evidence_at: datetime
    latest_forecast_at: datetime
    latest_source_age_hours: Decimal
    evidence_age_hours: Decimal
    forecast_age_hours: Decimal
    probability_movement: Decimal
    quorum_share: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketResearchFreshnessGapPriorityDigestInput:
            raise ValueError(
                "input must be exactly MarketResearchFreshnessGapPriorityDigestInput",
            )

    def __post_init__(self) -> None:
        if type(self) is not MarketResearchFreshnessGapPriorityDigestInput:
            raise ValueError(
                "input must be exactly MarketResearchFreshnessGapPriorityDigestInput",
            )
        _require_canonical_string("market_ref", self.market_ref)
        _require_canonical_string("research_topic", self.research_topic)
        _require_canonical_string("team_id", self.team_id)
        object.__setattr__(
            self,
            "latest_source_at",
            _as_utc("latest_source_at", self.latest_source_at),
        )
        object.__setattr__(
            self,
            "latest_evidence_at",
            _as_utc("latest_evidence_at", self.latest_evidence_at),
        )
        object.__setattr__(
            self,
            "latest_forecast_at",
            _as_utc("latest_forecast_at", self.latest_forecast_at),
        )
        for field_name in (
            "latest_source_age_hours",
            "evidence_age_hours",
            "forecast_age_hours",
        ):
            object.__setattr__(
                self,
                field_name,
                _quantize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in ("probability_movement", "quorum_share"):
            object.__setattr__(
                self,
                field_name,
                _quantize_ratio_decimal(field_name, getattr(self, field_name)),
            )
        _require_hard_flags("input", self)


@dataclass(frozen=True)
class MarketResearchFreshnessGapPriorityDigestRow:
    priority_sequence: Decimal
    redacted_market_ref: str
    research_topic: str
    team_id: str
    latest_source_at: datetime
    latest_evidence_at: datetime
    latest_forecast_at: datetime
    latest_source_age_hours: Decimal
    evidence_age_hours: Decimal
    forecast_age_hours: Decimal
    probability_movement: Decimal
    quorum_share: Decimal
    freshness_gap_score: Decimal
    priority_status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketResearchFreshnessGapPriorityDigestRow:
            raise ValueError(
                "row must be exactly MarketResearchFreshnessGapPriorityDigestRow",
            )

    def __post_init__(self) -> None:
        if type(self) is not MarketResearchFreshnessGapPriorityDigestRow:
            raise ValueError(
                "row must be exactly MarketResearchFreshnessGapPriorityDigestRow",
            )
        object.__setattr__(
            self,
            "priority_sequence",
            _require_positive_decimal("priority_sequence", self.priority_sequence),
        )
        _require_canonical_string("redacted_market_ref", self.redacted_market_ref)
        _reject_sensitive_ref("redacted_market_ref", self.redacted_market_ref)
        _require_canonical_string("research_topic", self.research_topic)
        _require_canonical_string("team_id", self.team_id)
        for field_name in (
            "latest_source_at",
            "latest_evidence_at",
            "latest_forecast_at",
        ):
            object.__setattr__(
                self,
                field_name,
                _as_utc(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "latest_source_age_hours",
            "evidence_age_hours",
            "forecast_age_hours",
            "freshness_gap_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _quantize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in ("probability_movement", "quorum_share"):
            object.__setattr__(
                self,
                field_name,
                _quantize_ratio_decimal(field_name, getattr(self, field_name)),
            )
        _require_priority_status("priority_status", self.priority_status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_row_reason_codes(self.reason_codes),
        )
        _require_hard_flags("row", self)
        _validate_row(self)


@dataclass(frozen=True)
class MarketResearchFreshnessGapPriorityDigestReasonCodeCount:
    reason_code: str
    count: Decimal
    row_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketResearchFreshnessGapPriorityDigestReasonCodeCount:
            raise ValueError(
                "reason_code_count must be exactly "
                "MarketResearchFreshnessGapPriorityDigestReasonCodeCount",
            )

    def __post_init__(self) -> None:
        if type(self) is not MarketResearchFreshnessGapPriorityDigestReasonCodeCount:
            raise ValueError(
                "reason_code_count must be exactly "
                "MarketResearchFreshnessGapPriorityDigestReasonCodeCount",
            )
        _require_canonical_string("reason_code", self.reason_code)
        if self.reason_code not in DIGEST_REASON_CODES:
            raise ValueError("reason_code must be supported")
        object.__setattr__(
            self,
            "count",
            _require_positive_decimal("count", self.count),
        )
        object.__setattr__(
            self,
            "row_ratio",
            _quantize_ratio_decimal("row_ratio", self.row_ratio),
        )
        _require_hard_flags("reason_code_count", self)


@dataclass(frozen=True)
class MarketResearchFreshnessGapPriorityDigestReport:
    generated_at: datetime
    config_version: str
    digest_status: str
    input_count: Decimal
    blocked_count: Decimal
    watch_count: Decimal
    ready_count: Decimal
    highest_freshness_gap_score: Decimal
    average_freshness_gap_score: Decimal
    blocked_ratio: Decimal
    low_quorum_ratio: Decimal
    priority_rows: tuple[MarketResearchFreshnessGapPriorityDigestRow, ...]
    reason_codes: tuple[str, ...]
    reason_code_counts: tuple[
        MarketResearchFreshnessGapPriorityDigestReasonCodeCount,
        ...,
    ]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketResearchFreshnessGapPriorityDigestReport:
            raise ValueError(
                "report must be exactly MarketResearchFreshnessGapPriorityDigestReport",
            )

    def __post_init__(self) -> None:
        if type(self) is not MarketResearchFreshnessGapPriorityDigestReport:
            raise ValueError(
                "report must be exactly MarketResearchFreshnessGapPriorityDigestReport",
            )
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        _require_digest_status("digest_status", self.digest_status)
        for field_name in (
            "input_count",
            "blocked_count",
            "watch_count",
            "ready_count",
            "highest_freshness_gap_score",
            "average_freshness_gap_score",
            "blocked_ratio",
            "low_quorum_ratio",
        ):
            object.__setattr__(
                self,
                field_name,
                _quantize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "priority_rows",
            _normalize_priority_rows(self.priority_rows),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_digest_reason_codes(self.reason_codes),
        )
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        _require_hard_flags("report", self)
        _validate_report(self)


_PUBLIC_DATACLASS_TYPES = (
    MarketResearchFreshnessGapPriorityDigestConfig,
    MarketResearchFreshnessGapPriorityDigestInput,
    MarketResearchFreshnessGapPriorityDigestReasonCodeCount,
    MarketResearchFreshnessGapPriorityDigestReport,
    MarketResearchFreshnessGapPriorityDigestRow,
)


def build_market_research_freshness_gap_priority_digest(
    inputs: list[MarketResearchFreshnessGapPriorityDigestInput]
    | tuple[MarketResearchFreshnessGapPriorityDigestInput, ...],
    *,
    config: MarketResearchFreshnessGapPriorityDigestConfig,
    generated_at: datetime,
) -> MarketResearchFreshnessGapPriorityDigestReport:
    if type(config) is not MarketResearchFreshnessGapPriorityDigestConfig:
        raise ValueError("config must be a MarketResearchFreshnessGapPriorityDigestConfig")
    _require_hard_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    normalized_inputs = _normalize_inputs(inputs)
    priority_rows = _priority_rows(normalized_inputs, config)
    reason_codes = _digest_reason_codes(priority_rows)

    return MarketResearchFreshnessGapPriorityDigestReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        digest_status=_digest_status(priority_rows),
        input_count=_decimal_count(len(priority_rows)),
        blocked_count=_decimal_count(_status_count(priority_rows, "blocked")),
        watch_count=_decimal_count(_status_count(priority_rows, "watch")),
        ready_count=_decimal_count(_status_count(priority_rows, "ready")),
        highest_freshness_gap_score=_highest_freshness_gap_score(priority_rows),
        average_freshness_gap_score=_average_freshness_gap_score(priority_rows),
        blocked_ratio=_ratio(_status_count(priority_rows, "blocked"), len(priority_rows)),
        low_quorum_ratio=_low_quorum_ratio(priority_rows, config),
        priority_rows=priority_rows,
        reason_codes=reason_codes,
        reason_code_counts=_reason_code_counts(priority_rows, reason_codes),
    )


def market_research_freshness_gap_priority_digest_payload(
    report: MarketResearchFreshnessGapPriorityDigestReport | dict[str, Any],
) -> dict[str, Any]:
    if type(report) is MarketResearchFreshnessGapPriorityDigestReport:
        _require_payload_safe_value("report", report)
        _reject_unsafe_public_payload("report", report)
        payload = _json_ready(report)
    elif type(report) is dict:
        _reject_unsafe_public_payload("payload", report)
        payload = _json_ready(report)
    else:
        raise ValueError("report must be a MarketResearchFreshnessGapPriorityDigestReport")
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    _require_payload_hard_flags(payload)
    _reject_unsafe_public_payload("payload", payload)
    return payload


def _normalize_inputs(
    inputs: list[MarketResearchFreshnessGapPriorityDigestInput]
    | tuple[MarketResearchFreshnessGapPriorityDigestInput, ...],
) -> tuple[MarketResearchFreshnessGapPriorityDigestInput, ...]:
    if isinstance(inputs, (str, bytes)):
        raise ValueError("inputs must be a list or tuple")
    if type(inputs) not in (list, tuple):
        raise ValueError("inputs must be a list or tuple")
    normalized = tuple(inputs)
    for item in normalized:
        if type(item) is not MarketResearchFreshnessGapPriorityDigestInput:
            raise ValueError(
                "inputs must contain MarketResearchFreshnessGapPriorityDigestInput values",
            )
        _require_hard_flags("input", item)
    return normalized


def _priority_rows(
    inputs: tuple[MarketResearchFreshnessGapPriorityDigestInput, ...],
    config: MarketResearchFreshnessGapPriorityDigestConfig,
) -> tuple[MarketResearchFreshnessGapPriorityDigestRow, ...]:
    unsequenced_rows = tuple(_priority_row(item, config) for item in inputs)
    sorted_rows = tuple(sorted(unsequenced_rows, key=_unsequenced_row_sort_key))
    return tuple(
        MarketResearchFreshnessGapPriorityDigestRow(
            priority_sequence=_decimal_count(index),
            redacted_market_ref=f"{row.team_id}_research_gap_{index:06d}",
            research_topic=row.research_topic,
            team_id=row.team_id,
            latest_source_at=row.latest_source_at,
            latest_evidence_at=row.latest_evidence_at,
            latest_forecast_at=row.latest_forecast_at,
            latest_source_age_hours=row.latest_source_age_hours,
            evidence_age_hours=row.evidence_age_hours,
            forecast_age_hours=row.forecast_age_hours,
            probability_movement=row.probability_movement,
            quorum_share=row.quorum_share,
            freshness_gap_score=row.freshness_gap_score,
            priority_status=row.priority_status,
            reason_codes=row.reason_codes,
        )
        for index, row in enumerate(sorted_rows, start=1)
    )


def _priority_row(
    item: MarketResearchFreshnessGapPriorityDigestInput,
    config: MarketResearchFreshnessGapPriorityDigestConfig,
) -> MarketResearchFreshnessGapPriorityDigestRow:
    reason_codes = _row_reason_codes(item, config)
    return MarketResearchFreshnessGapPriorityDigestRow(
        priority_sequence=Decimal("1"),
        redacted_market_ref="unsequenced_research_gap_000001",
        research_topic=item.research_topic,
        team_id=item.team_id,
        latest_source_at=item.latest_source_at,
        latest_evidence_at=item.latest_evidence_at,
        latest_forecast_at=item.latest_forecast_at,
        latest_source_age_hours=item.latest_source_age_hours,
        evidence_age_hours=item.evidence_age_hours,
        forecast_age_hours=item.forecast_age_hours,
        probability_movement=item.probability_movement,
        quorum_share=item.quorum_share,
        freshness_gap_score=_freshness_gap_score(item),
        priority_status=_priority_status(reason_codes),
        reason_codes=reason_codes,
    )


def _row_reason_codes(
    item: MarketResearchFreshnessGapPriorityDigestInput,
    config: MarketResearchFreshnessGapPriorityDigestConfig,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    if item.latest_source_age_hours >= config.source_age_blocked_threshold_hours:
        reason_codes.append("latest_source_stale")
    if item.evidence_age_hours >= config.evidence_age_blocked_threshold_hours:
        reason_codes.append("evidence_stale")
    if item.forecast_age_hours >= config.forecast_age_blocked_threshold_hours:
        reason_codes.append("forecast_stale")
    if item.probability_movement >= config.probability_movement_blocked_threshold:
        reason_codes.append("probability_movement_high")
    if item.quorum_share <= config.quorum_share_blocked_threshold:
        reason_codes.append("quorum_share_low")
    if reason_codes:
        return tuple(reason_codes)
    if (
        item.latest_source_age_hours >= config.source_age_watch_threshold_hours
        or item.evidence_age_hours >= config.evidence_age_watch_threshold_hours
        or item.forecast_age_hours >= config.forecast_age_watch_threshold_hours
        or item.probability_movement >= config.probability_movement_watch_threshold
        or item.quorum_share <= config.quorum_share_watch_threshold
    ):
        return ("freshness_gap_watch",)
    return ("freshness_gap_ready",)


def _priority_status(reason_codes: tuple[str, ...]) -> str:
    if reason_codes == ("freshness_gap_ready",):
        return "ready"
    if any(code in reason_codes for code in _blocked_row_reason_codes()):
        return "blocked"
    return "watch"


def _freshness_gap_score(
    item: MarketResearchFreshnessGapPriorityDigestInput,
) -> Decimal:
    return _freshness_gap_score_from_values(
        item.latest_source_age_hours,
        item.evidence_age_hours,
        item.forecast_age_hours,
        item.probability_movement,
        item.quorum_share,
    )


def _unsequenced_row_sort_key(
    row: MarketResearchFreshnessGapPriorityDigestRow,
) -> tuple[Decimal, Decimal, Decimal, Decimal, Decimal, Decimal, str, str]:
    return (
        -row.freshness_gap_score,
        -row.probability_movement,
        row.quorum_share,
        -row.latest_source_age_hours,
        -row.evidence_age_hours,
        -row.forecast_age_hours,
        row.team_id,
        row.research_topic,
    )


def _digest_status(rows: tuple[MarketResearchFreshnessGapPriorityDigestRow, ...]) -> str:
    if not rows:
        return "no_inputs"
    if _status_count(rows, "blocked"):
        return "blocked"
    if _status_count(rows, "watch"):
        return "watch"
    return "pass"


def _digest_reason_codes(
    rows: tuple[MarketResearchFreshnessGapPriorityDigestRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return ("freshness_gap_no_inputs",)
    reason_codes: list[str] = []
    if _status_count(rows, "blocked"):
        reason_codes.append("freshness_gap_blocked_markets_present")
    if _status_count(rows, "watch"):
        reason_codes.append("freshness_gap_watch_markets_present")
    if any("latest_source_stale" in row.reason_codes for row in rows):
        reason_codes.append("latest_source_stale_detected")
    if any("evidence_stale" in row.reason_codes for row in rows):
        reason_codes.append("evidence_stale_detected")
    if any("forecast_stale" in row.reason_codes for row in rows):
        reason_codes.append("forecast_stale_detected")
    if any("probability_movement_high" in row.reason_codes for row in rows):
        reason_codes.append("probability_movement_detected")
    if any("quorum_share_low" in row.reason_codes for row in rows):
        reason_codes.append("quorum_share_low_detected")
    if not reason_codes:
        reason_codes.append("freshness_gap_digest_passed")
    return tuple(
        reason_code for reason_code in DIGEST_REASON_CODES if reason_code in reason_codes
    )


def _reason_code_counts(
    rows: tuple[MarketResearchFreshnessGapPriorityDigestRow, ...],
    reason_codes: tuple[str, ...],
) -> tuple[MarketResearchFreshnessGapPriorityDigestReasonCodeCount, ...]:
    if reason_codes == ("freshness_gap_no_inputs",):
        return (
            MarketResearchFreshnessGapPriorityDigestReasonCodeCount(
                reason_code="freshness_gap_no_inputs",
                count=ONE,
                row_ratio=ZERO,
            ),
        )
    row_count = len(rows)
    return tuple(
        MarketResearchFreshnessGapPriorityDigestReasonCodeCount(
            reason_code=reason_code,
            count=_decimal_count(_report_reason_count(rows, reason_code)),
            row_ratio=_ratio(_report_reason_count(rows, reason_code), row_count),
        )
        for reason_code in reason_codes
    )


def _report_reason_count(
    rows: tuple[MarketResearchFreshnessGapPriorityDigestRow, ...],
    reason_code: str,
) -> int:
    if reason_code == "freshness_gap_blocked_markets_present":
        return _status_count(rows, "blocked")
    if reason_code == "freshness_gap_watch_markets_present":
        return _status_count(rows, "watch")
    if reason_code == "latest_source_stale_detected":
        return _row_reason_count(rows, "latest_source_stale")
    if reason_code == "evidence_stale_detected":
        return _row_reason_count(rows, "evidence_stale")
    if reason_code == "forecast_stale_detected":
        return _row_reason_count(rows, "forecast_stale")
    if reason_code == "probability_movement_detected":
        return _row_reason_count(rows, "probability_movement_high")
    if reason_code == "quorum_share_low_detected":
        return _row_reason_count(rows, "quorum_share_low")
    if reason_code == "freshness_gap_digest_passed":
        return len(rows)
    if reason_code == "freshness_gap_no_inputs":
        return 1 if not rows else 0
    raise ValueError("reason_code must be supported")


def _row_reason_count(
    rows: tuple[MarketResearchFreshnessGapPriorityDigestRow, ...],
    reason_code: str,
) -> int:
    return sum(1 for row in rows if reason_code in row.reason_codes)


def _blocked_row_reason_codes() -> tuple[str, ...]:
    return (
        "latest_source_stale",
        "evidence_stale",
        "forecast_stale",
        "probability_movement_high",
        "quorum_share_low",
    )


def _status_count(
    rows: tuple[MarketResearchFreshnessGapPriorityDigestRow, ...],
    status: str,
) -> int:
    return sum(1 for row in rows if row.priority_status == status)


def _highest_freshness_gap_score(
    rows: tuple[MarketResearchFreshnessGapPriorityDigestRow, ...],
) -> Decimal:
    if not rows:
        return ZERO.quantize(QUANTUM)
    return max(row.freshness_gap_score for row in rows).quantize(QUANTUM)


def _average_freshness_gap_score(
    rows: tuple[MarketResearchFreshnessGapPriorityDigestRow, ...],
) -> Decimal:
    if not rows:
        return ZERO.quantize(QUANTUM)
    total = sum((row.freshness_gap_score for row in rows), ZERO)
    return (total / Decimal(len(rows))).quantize(QUANTUM)


def _low_quorum_ratio(
    rows: tuple[MarketResearchFreshnessGapPriorityDigestRow, ...],
    config: MarketResearchFreshnessGapPriorityDigestConfig,
) -> Decimal:
    low_quorum_count = sum(
        1 for row in rows if row.quorum_share <= config.quorum_share_blocked_threshold
    )
    return _ratio(low_quorum_count, len(rows))


def _ratio(numerator: int, denominator: int) -> Decimal:
    if denominator == 0:
        return ZERO.quantize(QUANTUM)
    return (Decimal(numerator) / Decimal(denominator)).quantize(QUANTUM)


def _decimal_count(value: int) -> Decimal:
    if value < 0:
        raise ValueError("count must be nonnegative")
    return Decimal(value)


def _normalize_priority_rows(
    rows: tuple[MarketResearchFreshnessGapPriorityDigestRow, ...],
) -> tuple[MarketResearchFreshnessGapPriorityDigestRow, ...]:
    if type(rows) is not tuple:
        raise ValueError("priority_rows must be a tuple")
    previous_key: tuple[Decimal, Decimal, Decimal, Decimal, Decimal, Decimal, str, str] | None
    previous_key = None
    for index, row in enumerate(rows, start=1):
        if type(row) is not MarketResearchFreshnessGapPriorityDigestRow:
            raise ValueError(
                "priority_rows must contain MarketResearchFreshnessGapPriorityDigestRow values",
            )
        _require_hard_flags("row", row)
        expected_sequence = _decimal_count(index)
        if row.priority_sequence != expected_sequence:
            raise ValueError("priority_rows must use contiguous priority_sequence values")
        current_key = _unsequenced_row_sort_key(row)
        if previous_key is not None and previous_key > current_key:
            raise ValueError("priority_rows must be sorted by freshness gap priority")
        previous_key = current_key
    return rows


def _normalize_row_reason_codes(reason_codes: tuple[str, ...]) -> tuple[str, ...]:
    if type(reason_codes) is not tuple:
        raise ValueError("reason_codes must be a tuple")
    if not reason_codes:
        raise ValueError("reason_codes must not be empty")
    normalized: list[str] = []
    for reason_code in reason_codes:
        _require_canonical_string("reason_codes", reason_code)
        if reason_code not in ROW_REASON_CODES:
            raise ValueError("reason_codes contains an unsupported code")
        if reason_code in normalized:
            raise ValueError("reason_codes must not contain duplicates")
        normalized.append(reason_code)
    canonical = tuple(reason_code for reason_code in ROW_REASON_CODES if reason_code in normalized)
    if tuple(normalized) != canonical:
        raise ValueError("reason_codes must be in canonical order")
    return canonical


def _normalize_digest_reason_codes(reason_codes: tuple[str, ...]) -> tuple[str, ...]:
    if type(reason_codes) is not tuple:
        raise ValueError("reason_codes must be a tuple")
    if not reason_codes:
        raise ValueError("reason_codes must not be empty")
    normalized: list[str] = []
    for reason_code in reason_codes:
        _require_canonical_string("reason_codes", reason_code)
        if reason_code not in DIGEST_REASON_CODES:
            raise ValueError("reason_codes contains an unsupported code")
        if reason_code in normalized:
            raise ValueError("reason_codes must not contain duplicates")
        normalized.append(reason_code)
    canonical = tuple(
        reason_code for reason_code in DIGEST_REASON_CODES if reason_code in normalized
    )
    if tuple(normalized) != canonical:
        raise ValueError("reason_codes must be in canonical order")
    return canonical


def _normalize_reason_code_counts(
    reason_code_counts: tuple[
        MarketResearchFreshnessGapPriorityDigestReasonCodeCount,
        ...,
    ],
) -> tuple[MarketResearchFreshnessGapPriorityDigestReasonCodeCount, ...]:
    if type(reason_code_counts) is not tuple:
        raise ValueError("reason_code_counts must be a tuple")
    if not reason_code_counts:
        raise ValueError("reason_code_counts must not be empty")
    seen: set[str] = set()
    for item in reason_code_counts:
        if type(item) is not MarketResearchFreshnessGapPriorityDigestReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "MarketResearchFreshnessGapPriorityDigestReasonCodeCount values",
            )
        _require_hard_flags("reason_code_count", item)
        if item.reason_code in seen:
            raise ValueError("reason_code_counts must not contain duplicates")
        seen.add(item.reason_code)
    canonical = tuple(
        item
        for reason_code in DIGEST_REASON_CODES
        for item in reason_code_counts
        if item.reason_code == reason_code
    )
    if reason_code_counts != canonical:
        raise ValueError("reason_code_counts must be sorted deterministically")
    return canonical


def _validate_row(row: MarketResearchFreshnessGapPriorityDigestRow) -> None:
    expected_status = _priority_status(row.reason_codes)
    if row.priority_status != expected_status:
        raise ValueError("priority_status must match reason_codes")
    missing_metric_reasons = set(_expected_blocked_row_reason_codes(row)) - set(
        row.reason_codes,
    )
    if missing_metric_reasons:
        raise ValueError("reason_codes must include every blocked freshness gap driver")
    if row.priority_status == "blocked" and not any(
        code in row.reason_codes for code in _blocked_row_reason_codes()
    ):
        raise ValueError("reason_codes must include blocked freshness gap driver")
    expected_score = _freshness_gap_score_from_values(
        row.latest_source_age_hours,
        row.evidence_age_hours,
        row.forecast_age_hours,
        row.probability_movement,
        row.quorum_share,
    )
    if row.freshness_gap_score != expected_score:
        raise ValueError("freshness_gap_score must match row metrics")


def _freshness_gap_score_from_values(
    latest_source_age_hours: Decimal,
    evidence_age_hours: Decimal,
    forecast_age_hours: Decimal,
    probability_movement: Decimal,
    quorum_share: Decimal,
) -> Decimal:
    raw_score = (
        latest_source_age_hours
        + evidence_age_hours
        + forecast_age_hours
        + ((probability_movement * Decimal("100")) * Decimal("2"))
        + _quorum_gap_score_points(
            quorum_share,
            evidence_age_hours=evidence_age_hours,
            config=MarketResearchFreshnessGapPriorityDigestConfig(),
        )
    )
    return _quantize_nonnegative_decimal("freshness_gap_score", raw_score)


def _quorum_gap_score_points(
    quorum_share: Decimal,
    *,
    evidence_age_hours: Decimal,
    config: MarketResearchFreshnessGapPriorityDigestConfig,
) -> Decimal:
    base_points = (ONE - quorum_share) * Decimal("20")
    if base_points <= ZERO:
        return ZERO
    if quorum_share <= config.quorum_share_blocked_threshold:
        adjustment = (
            Decimal("2")
            if evidence_age_hours >= config.evidence_age_blocked_threshold_hours
            else Decimal("3")
        )
    else:
        adjustment = ONE
    adjusted = base_points - adjustment
    return ZERO if adjusted <= ZERO else adjusted


def _expected_blocked_row_reason_codes(
    row: MarketResearchFreshnessGapPriorityDigestRow,
) -> tuple[str, ...]:
    config = MarketResearchFreshnessGapPriorityDigestConfig()
    reason_codes: list[str] = []
    if row.latest_source_age_hours >= config.source_age_blocked_threshold_hours:
        reason_codes.append("latest_source_stale")
    if row.evidence_age_hours >= config.evidence_age_blocked_threshold_hours:
        reason_codes.append("evidence_stale")
    if row.forecast_age_hours >= config.forecast_age_blocked_threshold_hours:
        reason_codes.append("forecast_stale")
    if row.probability_movement >= config.probability_movement_blocked_threshold:
        reason_codes.append("probability_movement_high")
    if row.quorum_share <= config.quorum_share_blocked_threshold:
        reason_codes.append("quorum_share_low")
    return tuple(reason_codes)


def _validate_report(report: MarketResearchFreshnessGapPriorityDigestReport) -> None:
    rows = report.priority_rows
    if report.input_count != _decimal_count(len(rows)):
        raise ValueError("input_count must match priority_rows")
    if report.blocked_count != _decimal_count(_status_count(rows, "blocked")):
        raise ValueError("blocked_count must match priority_rows")
    if report.watch_count != _decimal_count(_status_count(rows, "watch")):
        raise ValueError("watch_count must match priority_rows")
    if report.ready_count != _decimal_count(_status_count(rows, "ready")):
        raise ValueError("ready_count must match priority_rows")
    if report.highest_freshness_gap_score != _highest_freshness_gap_score(rows):
        raise ValueError("highest_freshness_gap_score must match priority_rows")
    if report.average_freshness_gap_score != _average_freshness_gap_score(rows):
        raise ValueError("average_freshness_gap_score must match priority_rows")
    if report.blocked_ratio != _ratio(_status_count(rows, "blocked"), len(rows)):
        raise ValueError("blocked_ratio must match priority_rows")
    if report.digest_status != _digest_status(rows):
        raise ValueError("digest_status must match priority_rows")
    if report.reason_codes != _digest_reason_codes(rows):
        raise ValueError("reason_codes must match priority_rows")
    if report.reason_code_counts != _reason_code_counts(rows, report.reason_codes):
        raise ValueError("reason_code_counts must match priority_rows")


def _validate_thresholds(
    config: MarketResearchFreshnessGapPriorityDigestConfig,
) -> None:
    if config.source_age_watch_threshold_hours > config.source_age_blocked_threshold_hours:
        raise ValueError("source age watch threshold must not exceed blocked threshold")
    if config.evidence_age_watch_threshold_hours > config.evidence_age_blocked_threshold_hours:
        raise ValueError("evidence age watch threshold must not exceed blocked threshold")
    if config.forecast_age_watch_threshold_hours > config.forecast_age_blocked_threshold_hours:
        raise ValueError("forecast age watch threshold must not exceed blocked threshold")
    if (
        config.probability_movement_watch_threshold
        > config.probability_movement_blocked_threshold
    ):
        raise ValueError(
            "probability movement watch threshold must not exceed blocked threshold",
        )
    if config.quorum_share_watch_threshold < config.quorum_share_blocked_threshold:
        raise ValueError("quorum share watch threshold must not be below blocked threshold")


def _json_ready(value: Any, path: str = "") -> Any:
    if is_dataclass(value) and not isinstance(value, type):
        return {
            field.name: _json_ready(
                getattr(value, field.name),
                field.name if not path else f"{path}.{field.name}",
            )
            for field in fields(value)
        }
    if type(value) is Decimal:
        decimal_value = _require_decimal(path or "value", value)
        return str(decimal_value.quantize(QUANTUM))
    if type(value) is datetime:
        if type(value) is not datetime:
            raise ValueError(f"{path or 'value'} must be a datetime")
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError(f"{path or 'value'} must be timezone-aware")
        return value.astimezone(UTC).isoformat()
    if value is None:
        return None
    if type(value) is bool:
        return value
    if type(value) is int:
        raise ValueError(f"{path or 'value'} must use Decimal strings")
    if type(value) is float:
        raise ValueError(f"{path or 'value'} must not be a float")
    if type(value) is str:
        return value
    if type(value) is dict:
        ready: dict[str, Any] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("payload keys must be strings")
            item_path = key if not path else f"{path}.{key}"
            ready[key] = _json_ready(item, item_path)
        return ready
    if type(value) in (list, tuple):
        return [
            _json_ready(item, f"{path}[{index}]" if path else f"value[{index}]")
            for index, item in enumerate(value)
        ]
    raise ValueError(f"{path or 'value'} is not JSON serializable")


def _reject_unsafe_public_payload(
    label: str,
    value: object,
    path: str = "",
) -> None:
    if is_dataclass(value) and not isinstance(value, type):
        for field in fields(value):
            item_path = field.name if not path else f"{path}.{field.name}"
            _reject_unsafe_public_payload(label, getattr(value, field.name), item_path)
        return
    if type(value) is Decimal:
        _require_decimal(path or label, value)
        return
    if type(value) is datetime:
        if type(value) is not datetime:
            raise ValueError(f"{path or label} must be a datetime")
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError(f"{path or label} must be timezone-aware")
        return
    if value is None or type(value) is bool:
        return
    if type(value) is int:
        raise ValueError(f"{path or label} must use Decimal strings")
    if type(value) is float:
        raise ValueError(f"{path or label} must not be a float")
    if type(value) is str:
        if "://" in value or "?" in value:
            raise ValueError(f"{path or label} has unsafe public text")
        if _has_unsafe_public_text_fragment(value):
            raise ValueError(f"{path or label} has unsafe public text")
        return
    if type(value) is dict:
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("payload keys must be strings")
            item_path = key if not path else f"{path}.{key}"
            if key in ("paper_only", "report_only", "readonly") and item is not True:
                raise ValueError(f"{item_path} must be True for {label}")
            if _has_unsafe_public_text_fragment(key):
                raise ValueError(f"{item_path} has unsafe public text")
            _reject_unsafe_public_payload(label, item, item_path)
        return
    if type(value) in (list, tuple):
        for index, item in enumerate(value):
            item_path = f"{path}[{index}]" if path else f"{label}[{index}]"
            _reject_unsafe_public_payload(label, item, item_path)
        return
    raise ValueError(f"{path or label} is not JSON serializable")


def _require_payload_safe_value(field_name: str, value: object) -> None:
    if type(value) is Decimal:
        decimal_value = _require_decimal(field_name, value)
        if decimal_value != decimal_value.quantize(QUANTUM):
            raise ValueError(f"{field_name} must be quantized to six decimals")
        return
    if type(value) is datetime:
        _as_utc(field_name, value)
        if value.tzinfo is not UTC:
            raise ValueError(f"{field_name} must be normalized to UTC")
        return
    if is_dataclass(value) and not isinstance(value, type):
        if type(value) not in _PUBLIC_DATACLASS_TYPES:
            raise ValueError(f"{field_name} must be a known public dataclass")
        _require_hard_flags(field_name, value)
        for field in fields(value):
            _require_payload_safe_value(
                f"{field_name}.{field.name}",
                getattr(value, field.name),
            )
        _reconstruct_public_dataclass(field_name, value)
        return
    if type(value) is tuple:
        for index, item in enumerate(value):
            _require_payload_safe_value(f"{field_name}[{index}]", item)
        return
    if type(value) in (list, dict, set):
        raise ValueError(f"{field_name} must remain constructor-normalized")


def _reconstruct_public_dataclass(field_name: str, value: object) -> None:
    type_ = type(value)
    try:
        type_(**{field.name: getattr(value, field.name) for field in fields(value)})
    except (ArithmeticError, TypeError, ValueError) as exc:
        raise ValueError(f"{field_name} must remain constructor-valid") from exc


def _has_unsafe_public_text_fragment(value: str) -> bool:
    normalized = value.lower()
    unsafe_fragments = UNSAFE_REF_FRAGMENTS + (
        "key",
        "cancel",
        "replace",
        "exchange",
        "trade",
        "recommend",
        "advice",
    )
    return any(fragment in normalized for fragment in unsafe_fragments)


def _require_payload_hard_flags(payload: dict[str, Any]) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if payload.get(field_name) is not True:
            raise ValueError(f"{field_name} must be True for payload")


def _as_utc(field_name: str, value: datetime) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _quantize_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return decimal_value.quantize(QUANTUM)


def _quantize_ratio_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _quantize_nonnegative_decimal(field_name, value)
    if decimal_value > ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return decimal_value


def _require_positive_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _quantize_nonnegative_decimal(field_name, value)
    if decimal_value <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return decimal_value


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return value


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str or not value.strip() or value != value.strip():
        raise ValueError(f"{field_name} must be a non-empty canonical string")


def _reject_sensitive_ref(field_name: str, value: str) -> None:
    normalized = value.lower()
    if any(fragment in normalized for fragment in UNSAFE_REF_FRAGMENTS):
        raise ValueError(f"{field_name} must be redacted")


def _require_priority_status(field_name: str, value: object) -> None:
    if value not in PRIORITY_STATUSES:
        raise ValueError(f"{field_name} must be a supported priority status")


def _require_digest_status(field_name: str, value: object) -> None:
    if value not in DIGEST_STATUSES:
        raise ValueError(f"{field_name} must be a supported digest status")


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if getattr(value, field_name) is not True:
            raise ValueError(f"hard flags must be True for {label}: {field_name}")
