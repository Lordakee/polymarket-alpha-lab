"""Pure Phase 1 reducer for strategy team source reliability weights."""

from __future__ import annotations

import hashlib
from collections.abc import Iterable
from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from typing import Any


__all__ = (
    "StrategyTeamSourceReliabilityWeightDigestConfig",
    "StrategyTeamSourceReliabilityWeightDigestReport",
    "StrategyTeamSourceReliabilityWeightDigestRow",
    "StrategyTeamSourceReliabilityWeightReasonRollup",
    "StrategyTeamSourceReliabilityWeightSource",
    "build_strategy_team_source_reliability_weight_digest",
    "strategy_team_source_reliability_weight_digest_payload",
)


DEFAULT_CONFIG_VERSION = "strategy-team-source-reliability-weight-digest-v0"
COUNT_QUANTUM = Decimal("1")
RATIO_QUANTUM = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)

ROW_STATUSES = ("pass", "watch", "block")
REPORT_STATUSES = ("pass", "watch", "blocked")
EMPTY_REASON_CODE = "strategy_team_source_reliability_weight_digest_empty"
PASS_REASON_CODE = "source_reliability_weight_pass"
WATCH_REASON_CODE = "source_reliability_weight_watch"
BLOCK_REASON_CODE = "source_reliability_weight_block"
REPORT_REASON_PRIORITY = (
    PASS_REASON_CODE,
    WATCH_REASON_CODE,
    BLOCK_REASON_CODE,
    "source_reliability_low",
    "source_coverage_low",
    "source_stale",
    "source_dispute_ratio_high",
)
STATUS_PRIORITY = {"pass": 0, "watch": 1, "block": 2}
SENSITIVE_MARKERS = (
    "secret",
    "password",
    "passwd",
    "api_key",
    "apikey",
    "private_key",
    "access_key",
    "access_token",
    "refresh_token",
    "bearer ",
    "://",
    "@",
)
UNSAFE_PUBLIC_PAYLOAD_FIELD_FRAGMENTS = (
    "api_key",
    "apikey",
    "private_key",
    "access_key",
    "access_token",
    "refresh_token",
)
UNSAFE_PUBLIC_PAYLOAD_FIELD_TOKENS = (
    "auth",
    "wallet",
    "account",
    "order",
    "trade",
    "broker",
    "signing",
    "submit",
    "cancel",
)

RELIABILITY_PART = Decimal("0.443333")
COVERAGE_PART = Decimal("0.293333")
FRESHNESS_PART = Decimal("0.100000")
DISPUTE_PART = Decimal("0.112000")
TEAM_SIGNAL_PART = Decimal("0.050000")


@dataclass(frozen=True)
class StrategyTeamSourceReliabilityWeightDigestConfig:
    config_version: str = DEFAULT_CONFIG_VERSION
    min_pass_weighted_reliability_score: Decimal = Decimal("0.500000")
    min_watch_weighted_reliability_score: Decimal = Decimal("0.250000")
    min_source_reliability: Decimal = Decimal("0.600000")
    min_source_coverage_ratio: Decimal = Decimal("0.600000")
    max_source_age_seconds: Decimal = Decimal("86400.000000")
    max_dispute_ratio: Decimal = Decimal("0.200000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("config_version", self.config_version)
        for field_name in (
            "min_pass_weighted_reliability_score",
            "min_watch_weighted_reliability_score",
            "min_source_reliability",
            "min_source_coverage_ratio",
            "max_dispute_ratio",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "max_source_age_seconds",
            _normalize_positive_decimal(
                "max_source_age_seconds",
                self.max_source_age_seconds,
            ),
        )
        if (
            self.min_pass_weighted_reliability_score
            < self.min_watch_weighted_reliability_score
        ):
            raise ValueError(
                "min_pass_weighted_reliability_score must not be below watch",
            )
        _require_safety_flags("config", self)
        _reject_unsafe_public_payload_fields("config", self)


@dataclass(frozen=True)
class StrategyTeamSourceReliabilityWeightSource:
    team_id: str
    source_id: str
    observed_at: datetime
    source_reliability: Decimal
    evidence_count: Decimal
    settled_evidence_count: Decimal
    corroboration_count: Decimal
    dispute_count: Decimal
    source_age_seconds: Decimal
    team_signal_weight: Decimal
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("team_id", self.team_id)
        _require_canonical_string("source_id", self.source_id)
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        object.__setattr__(
            self,
            "source_reliability",
            _normalize_probability("source_reliability", self.source_reliability),
        )
        object.__setattr__(
            self,
            "evidence_count",
            _normalize_positive_count("evidence_count", self.evidence_count),
        )
        for field_name in (
            "settled_evidence_count",
            "corroboration_count",
            "dispute_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_count(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "source_age_seconds",
            _normalize_nonnegative_decimal(
                "source_age_seconds",
                self.source_age_seconds,
            ),
        )
        object.__setattr__(
            self,
            "team_signal_weight",
            _normalize_probability("team_signal_weight", self.team_signal_weight),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes, require_nonempty=True),
        )
        if self.settled_evidence_count > self.evidence_count:
            raise ValueError("settled_evidence_count must not exceed evidence_count")
        if self.corroboration_count > self.evidence_count:
            raise ValueError("corroboration_count must not exceed evidence_count")
        if self.dispute_count > self.settled_evidence_count:
            raise ValueError("dispute_count must not exceed settled_evidence_count")
        _require_safety_flags("source", self)
        _reject_unsafe_public_payload_fields("source", self)


@dataclass(frozen=True)
class StrategyTeamSourceReliabilityWeightDigestRow:
    team_id: str
    source_id: str
    observed_at: datetime
    source_reliability: Decimal
    evidence_count: Decimal
    settled_evidence_count: Decimal
    corroboration_count: Decimal
    dispute_count: Decimal
    source_age_seconds: Decimal
    team_signal_weight: Decimal
    source_coverage_ratio: Decimal
    dispute_ratio: Decimal
    freshness_weight: Decimal
    reliability_weight: Decimal
    weighted_reliability_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("team_id", self.team_id)
        _require_canonical_string("source_id", self.source_id)
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in (
            "source_reliability",
            "team_signal_weight",
            "source_coverage_ratio",
            "dispute_ratio",
            "freshness_weight",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "evidence_count",
            _normalize_positive_count("evidence_count", self.evidence_count),
        )
        for field_name in (
            "settled_evidence_count",
            "corroboration_count",
            "dispute_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_count(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "source_age_seconds",
            _normalize_nonnegative_decimal(
                "source_age_seconds",
                self.source_age_seconds,
            ),
        )
        for field_name in ("reliability_weight", "weighted_reliability_score"):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        _require_member("status", self.status, ROW_STATUSES)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes, require_nonempty=True),
        )
        _validate_row(self)
        _require_safety_flags("row", self)
        _reject_unsafe_public_payload_fields("row", self)


@dataclass(frozen=True)
class StrategyTeamSourceReliabilityWeightReasonRollup:
    reason_code: str
    source_count: Decimal
    source_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("reason_code", self.reason_code)
        object.__setattr__(
            self,
            "source_count",
            _normalize_nonnegative_count("source_count", self.source_count),
        )
        object.__setattr__(
            self,
            "source_ratio",
            _normalize_probability("source_ratio", self.source_ratio),
        )
        _require_safety_flags("rollup", self)
        _reject_unsafe_public_payload_fields("rollup", self)


@dataclass(frozen=True)
class StrategyTeamSourceReliabilityWeightDigestReport:
    generated_at: datetime
    config_version: str
    source_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    average_reliability_weight: Decimal
    average_weighted_reliability_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    rows: tuple[StrategyTeamSourceReliabilityWeightDigestRow, ...]
    reason_rollups: tuple[StrategyTeamSourceReliabilityWeightReasonRollup, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        for field_name in ("source_count", "pass_count", "watch_count", "block_count"):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_count(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "average_reliability_weight",
            "average_weighted_reliability_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        _require_member("status", self.status, REPORT_STATUSES)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes, require_nonempty=True),
        )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        object.__setattr__(self, "reason_rollups", _normalize_rollups(self.reason_rollups))
        _require_safety_flags("report", self)
        _reject_unsafe_public_payload_fields("report", self)
        if self.derived_validation_digest == "":
            object.__setattr__(
                self,
                "derived_validation_digest",
                _derived_validation_digest(self),
            )
        else:
            object.__setattr__(
                self,
                "derived_validation_digest",
                _normalize_derived_validation_digest(
                    "derived_validation_digest",
                    self.derived_validation_digest,
                ),
            )
        _validate_report(self)


def build_strategy_team_source_reliability_weight_digest(
    sources: Iterable[object],
    *,
    config: StrategyTeamSourceReliabilityWeightDigestConfig,
    generated_at: datetime,
) -> StrategyTeamSourceReliabilityWeightDigestReport:
    if type(config) is not StrategyTeamSourceReliabilityWeightDigestConfig:
        raise ValueError(
            "config must be a StrategyTeamSourceReliabilityWeightDigestConfig",
        )
    _require_safety_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    source_rows = _normalize_sources(sources)
    rows = tuple(
        sorted(
            (_row_from_source(source, config=config) for source in source_rows),
            key=_row_sort_key,
        ),
    )
    return StrategyTeamSourceReliabilityWeightDigestReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        source_count=_count(len(rows)),
        pass_count=_status_count(rows, "pass"),
        watch_count=_status_count(rows, "watch"),
        block_count=_status_count(rows, "block"),
        average_reliability_weight=_average(
            tuple(row.reliability_weight for row in rows),
        ),
        average_weighted_reliability_score=_average(
            tuple(row.weighted_reliability_score for row in rows),
        ),
        status=_report_status(rows),
        reason_codes=_report_reason_codes(rows),
        rows=rows,
        reason_rollups=_reason_rollups(rows),
    )


def strategy_team_source_reliability_weight_digest_payload(
    report: StrategyTeamSourceReliabilityWeightDigestReport,
) -> dict[str, Any]:
    if type(report) is not StrategyTeamSourceReliabilityWeightDigestReport:
        raise ValueError(
            "report must be a StrategyTeamSourceReliabilityWeightDigestReport",
        )
    _require_safety_flags("report", report)
    _reject_unsafe_public_payload_fields("report", report)
    _validate_report(report)
    return {
        "generated_at": report.generated_at.isoformat(),
        "config_version": report.config_version,
        "source_count": _count_payload(report.source_count),
        "pass_count": _count_payload(report.pass_count),
        "watch_count": _count_payload(report.watch_count),
        "block_count": _count_payload(report.block_count),
        "average_reliability_weight": _decimal_payload(
            report.average_reliability_weight,
        ),
        "average_weighted_reliability_score": _decimal_payload(
            report.average_weighted_reliability_score,
        ),
        "status": report.status,
        "reason_codes": list(report.reason_codes),
        "rows": [_row_payload(row) for row in report.rows],
        "reason_rollups": [_rollup_payload(rollup) for rollup in report.reason_rollups],
        "derived_validation_digest": report.derived_validation_digest,
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }


def _row_payload(row: StrategyTeamSourceReliabilityWeightDigestRow) -> dict[str, Any]:
    _require_safety_flags("row", row)
    return {
        "team_id": row.team_id,
        "source_id": row.source_id,
        "observed_at": row.observed_at.isoformat(),
        "source_reliability": _decimal_payload(row.source_reliability),
        "evidence_count": _count_payload(row.evidence_count),
        "settled_evidence_count": _count_payload(row.settled_evidence_count),
        "corroboration_count": _count_payload(row.corroboration_count),
        "dispute_count": _count_payload(row.dispute_count),
        "source_age_seconds": _decimal_payload(row.source_age_seconds),
        "team_signal_weight": _decimal_payload(row.team_signal_weight),
        "source_coverage_ratio": _decimal_payload(row.source_coverage_ratio),
        "dispute_ratio": _decimal_payload(row.dispute_ratio),
        "freshness_weight": _decimal_payload(row.freshness_weight),
        "reliability_weight": _decimal_payload(row.reliability_weight),
        "weighted_reliability_score": _decimal_payload(row.weighted_reliability_score),
        "status": row.status,
        "reason_codes": list(row.reason_codes),
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }


def _rollup_payload(
    rollup: StrategyTeamSourceReliabilityWeightReasonRollup,
) -> dict[str, Any]:
    _require_safety_flags("rollup", rollup)
    return {
        "reason_code": rollup.reason_code,
        "source_count": _count_payload(rollup.source_count),
        "source_ratio": _decimal_payload(rollup.source_ratio),
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }


def _row_from_source(
    source: StrategyTeamSourceReliabilityWeightSource,
    *,
    config: StrategyTeamSourceReliabilityWeightDigestConfig,
) -> StrategyTeamSourceReliabilityWeightDigestRow:
    source_coverage_ratio = _ratio(source.settled_evidence_count, source.evidence_count)
    dispute_ratio = (
        ZERO
        if source.settled_evidence_count == ZERO
        else _ratio(source.dispute_count, source.settled_evidence_count)
    )
    freshness_weight = _freshness_weight(source.source_age_seconds, config=config)
    reliability_weight = _reliability_weight(
        source_reliability=source.source_reliability,
        source_coverage_ratio=source_coverage_ratio,
        freshness_weight=freshness_weight,
        dispute_ratio=dispute_ratio,
        team_signal_weight=source.team_signal_weight,
    )
    weighted_reliability_score = _multiply(
        source.source_reliability,
        reliability_weight,
    )
    status, terminal_reason = _status_and_reason(
        weighted_reliability_score=weighted_reliability_score,
        source=source,
        source_coverage_ratio=source_coverage_ratio,
        dispute_ratio=dispute_ratio,
        config=config,
    )
    return StrategyTeamSourceReliabilityWeightDigestRow(
        team_id=source.team_id,
        source_id=source.source_id,
        observed_at=source.observed_at,
        source_reliability=source.source_reliability,
        evidence_count=source.evidence_count,
        settled_evidence_count=source.settled_evidence_count,
        corroboration_count=source.corroboration_count,
        dispute_count=source.dispute_count,
        source_age_seconds=source.source_age_seconds,
        team_signal_weight=source.team_signal_weight,
        source_coverage_ratio=source_coverage_ratio,
        dispute_ratio=dispute_ratio,
        freshness_weight=freshness_weight,
        reliability_weight=reliability_weight,
        weighted_reliability_score=weighted_reliability_score,
        status=status,
        reason_codes=_normalize_reason_codes(
            (
                *source.reason_codes,
                terminal_reason,
                *_quality_reason_codes(
                    source=source,
                    source_coverage_ratio=source_coverage_ratio,
                    freshness_weight=freshness_weight,
                    dispute_ratio=dispute_ratio,
                    config=config,
                ),
            ),
            require_nonempty=True,
        ),
    )


def _freshness_weight(
    source_age_seconds: Decimal,
    *,
    config: StrategyTeamSourceReliabilityWeightDigestConfig,
) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        value = ONE - (source_age_seconds / config.max_source_age_seconds)
    if value < ZERO:
        return ZERO
    return _quantize_ratio(value)


def _reliability_weight(
    *,
    source_reliability: Decimal,
    source_coverage_ratio: Decimal,
    freshness_weight: Decimal,
    dispute_ratio: Decimal,
    team_signal_weight: Decimal,
) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        value = (
            source_reliability * RELIABILITY_PART
            + source_coverage_ratio * COVERAGE_PART
            + freshness_weight * FRESHNESS_PART
            + (ONE - dispute_ratio) * DISPUTE_PART
            + team_signal_weight * TEAM_SIGNAL_PART
        )
    if value < ZERO:
        return ZERO
    return _quantize_ratio(value)


def _status_and_reason(
    *,
    weighted_reliability_score: Decimal,
    source: StrategyTeamSourceReliabilityWeightSource,
    source_coverage_ratio: Decimal,
    dispute_ratio: Decimal,
    config: StrategyTeamSourceReliabilityWeightDigestConfig,
) -> tuple[str, str]:
    if (
        weighted_reliability_score < config.min_watch_weighted_reliability_score
        or source.source_reliability < config.min_source_reliability
        or source_coverage_ratio < config.min_source_coverage_ratio
        or source.source_age_seconds > config.max_source_age_seconds
        or dispute_ratio > config.max_dispute_ratio
    ):
        return "block", BLOCK_REASON_CODE
    if weighted_reliability_score >= config.min_pass_weighted_reliability_score:
        return "pass", PASS_REASON_CODE
    return "watch", WATCH_REASON_CODE


def _quality_reason_codes(
    *,
    source: StrategyTeamSourceReliabilityWeightSource,
    source_coverage_ratio: Decimal,
    freshness_weight: Decimal,
    dispute_ratio: Decimal,
    config: StrategyTeamSourceReliabilityWeightDigestConfig,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    if source.source_reliability < config.min_source_reliability:
        reason_codes.append("source_reliability_low")
    elif source.source_reliability >= Decimal("0.800000"):
        reason_codes.append("source_reliability_strong")
    if source_coverage_ratio < config.min_source_coverage_ratio:
        reason_codes.append("source_coverage_low")
    else:
        reason_codes.append("source_coverage_met")
    if freshness_weight == ZERO:
        reason_codes.append("source_stale")
    else:
        reason_codes.append("source_fresh")
    if dispute_ratio > config.max_dispute_ratio:
        reason_codes.append("source_dispute_ratio_high")
    else:
        reason_codes.append("source_dispute_ratio_contained")
    return tuple(reason_codes)


def _normalize_sources(
    sources: Iterable[object],
) -> tuple[StrategyTeamSourceReliabilityWeightSource, ...]:
    if isinstance(sources, (str, bytes)):
        raise ValueError("sources must be an iterable")
    try:
        rows = tuple(sources)
    except TypeError as exc:
        raise ValueError("sources must be an iterable") from exc
    normalized = tuple(_source_from_row(row) for row in rows)
    seen: set[tuple[str, str]] = set()
    for row in normalized:
        key = (row.team_id, row.source_id)
        if key in seen:
            raise ValueError("duplicate team_id/source_id")
        seen.add(key)
    return normalized


def _source_from_row(row: object) -> StrategyTeamSourceReliabilityWeightSource:
    if type(row) is not StrategyTeamSourceReliabilityWeightSource:
        raise ValueError(
            "sources must contain StrategyTeamSourceReliabilityWeightSource",
        )
    _require_safety_flags("source", row)
    return row


def _normalize_rows(
    rows: object,
) -> tuple[StrategyTeamSourceReliabilityWeightDigestRow, ...]:
    if type(rows) is not tuple:
        raise ValueError("rows must be a tuple")
    normalized = tuple(rows)
    for row in normalized:
        if type(row) is not StrategyTeamSourceReliabilityWeightDigestRow:
            raise ValueError(
                "rows must contain StrategyTeamSourceReliabilityWeightDigestRow",
            )
        _require_safety_flags("row", row)
    if normalized != tuple(sorted(normalized, key=_row_sort_key)):
        raise ValueError("rows must be deterministically sorted")
    return normalized


def _normalize_rollups(
    rollups: object,
) -> tuple[StrategyTeamSourceReliabilityWeightReasonRollup, ...]:
    if type(rollups) is not tuple:
        raise ValueError("reason_rollups must be a tuple")
    normalized = tuple(rollups)
    for rollup in normalized:
        if type(rollup) is not StrategyTeamSourceReliabilityWeightReasonRollup:
            raise ValueError(
                "reason_rollups must contain StrategyTeamSourceReliabilityWeightReasonRollup",
            )
        _require_safety_flags("rollup", rollup)
    if normalized != tuple(sorted(normalized, key=_rollup_sort_key)):
        raise ValueError("reason_rollups must be deterministically sorted")
    return normalized


def _row_sort_key(
    row: StrategyTeamSourceReliabilityWeightDigestRow,
) -> tuple[int, Decimal, Decimal, str, str]:
    return (
        STATUS_PRIORITY[row.status],
        -row.weighted_reliability_score,
        -row.reliability_weight,
        row.team_id,
        row.source_id,
    )


def _rollup_sort_key(
    rollup: StrategyTeamSourceReliabilityWeightReasonRollup,
) -> tuple[Decimal, str]:
    return (-rollup.source_count, rollup.reason_code)


def _status_count(
    rows: tuple[StrategyTeamSourceReliabilityWeightDigestRow, ...],
    status: str,
) -> Decimal:
    return _count(sum(1 for row in rows if row.status == status))


def _average(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return ZERO
    return _ratio(sum(values, ZERO), _count(len(values)))


def _report_status(rows: tuple[StrategyTeamSourceReliabilityWeightDigestRow, ...]) -> str:
    if any(row.status == "block" for row in rows):
        return "blocked"
    if any(row.status == "watch" for row in rows) or not rows:
        return "watch"
    return "pass"


def _report_reason_codes(
    rows: tuple[StrategyTeamSourceReliabilityWeightDigestRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return (EMPTY_REASON_CODE,)
    observed: set[str] = set()
    for row in rows:
        observed.update(row.reason_codes)
    return tuple(
        reason_code
        for reason_code in REPORT_REASON_PRIORITY
        if reason_code in observed
    )


def _reason_rollups(
    rows: tuple[StrategyTeamSourceReliabilityWeightDigestRow, ...],
) -> tuple[StrategyTeamSourceReliabilityWeightReasonRollup, ...]:
    if not rows:
        return ()
    counts: dict[str, Decimal] = {}
    source_count = _count(len(rows))
    for row in rows:
        for reason_code in row.reason_codes:
            counts[reason_code] = counts.get(reason_code, ZERO) + ONE
    return tuple(
        sorted(
            (
                StrategyTeamSourceReliabilityWeightReasonRollup(
                    reason_code=reason_code,
                    source_count=count,
                    source_ratio=_ratio(count, source_count),
                )
                for reason_code, count in counts.items()
            ),
            key=_rollup_sort_key,
        ),
    )


def _validate_row(row: StrategyTeamSourceReliabilityWeightDigestRow) -> None:
    if row.settled_evidence_count > row.evidence_count:
        raise ValueError("settled_evidence_count must not exceed evidence_count")
    if row.corroboration_count > row.evidence_count:
        raise ValueError("corroboration_count must not exceed evidence_count")
    if row.dispute_count > row.settled_evidence_count:
        raise ValueError("dispute_count must not exceed settled_evidence_count")
    if row.source_coverage_ratio != _ratio(
        row.settled_evidence_count,
        row.evidence_count,
    ):
        raise ValueError("source_coverage_ratio must match evidence counts")
    expected_dispute_ratio = (
        ZERO
        if row.settled_evidence_count == ZERO
        else _ratio(row.dispute_count, row.settled_evidence_count)
    )
    if row.dispute_ratio != expected_dispute_ratio:
        raise ValueError("dispute_ratio must match dispute counts")
    if row.weighted_reliability_score != _multiply(
        row.source_reliability,
        row.reliability_weight,
    ):
        raise ValueError(
            "weighted_reliability_score must match reliability fields",
        )


def _validate_report(report: StrategyTeamSourceReliabilityWeightDigestReport) -> None:
    if report.source_count != _count(len(report.rows)):
        raise ValueError("source_count must match rows")
    if report.pass_count != _status_count(report.rows, "pass"):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _status_count(report.rows, "watch"):
        raise ValueError("watch_count must match rows")
    if report.block_count != _status_count(report.rows, "block"):
        raise ValueError("block_count must match rows")
    if report.average_reliability_weight != _average(
        tuple(row.reliability_weight for row in report.rows),
    ):
        raise ValueError("average_reliability_weight must match rows")
    if report.average_weighted_reliability_score != _average(
        tuple(row.weighted_reliability_score for row in report.rows),
    ):
        raise ValueError("average_weighted_reliability_score must match rows")
    if report.status != _report_status(report.rows):
        raise ValueError("status must match rows")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")
    if report.reason_rollups != _reason_rollups(report.rows):
        raise ValueError("reason_rollups must match rows")
    if report.derived_validation_digest != _derived_validation_digest(report):
        raise ValueError("derived_validation_digest must match report fields")


def _as_utc(name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{name} must be exactly datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{name} must be timezone-aware")
    return value.astimezone(UTC)


def _normalize_reason_codes(
    reason_codes: object,
    *,
    require_nonempty: bool,
) -> tuple[str, ...]:
    if type(reason_codes) is not tuple:
        raise ValueError("reason_codes must be a tuple")
    normalized: list[str] = []
    for reason_code in reason_codes:
        _require_canonical_string("reason_code", reason_code)
        if reason_code not in normalized:
            normalized.append(reason_code)
    if require_nonempty and not normalized:
        raise ValueError("reason_codes must be nonempty")
    return tuple(normalized)


def _normalize_derived_validation_digest(name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{name} must be a string")
    if len(value) != 64 or value.lower() != value:
        raise ValueError(f"{name} must be a lowercase sha256 digest")
    try:
        int(value, 16)
    except ValueError as exc:
        raise ValueError(f"{name} must be a lowercase sha256 digest") from exc
    return value


def _require_canonical_string(name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{name} must be a canonical nonblank string")
    if _has_sensitive_marker(value):
        raise ValueError(f"{name} must not contain sensitive material")


def _has_sensitive_marker(value: str) -> bool:
    lowered = value.lower()
    return any(marker in lowered for marker in SENSITIVE_MARKERS)


def _require_member(name: str, value: object, allowed: tuple[str, ...]) -> None:
    if value not in allowed:
        raise ValueError(f"{name} must be a known value")


def _normalize_probability(name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(name, value)
    if normalized < ZERO or normalized > ONE:
        raise ValueError(f"{name} must be between 0 and 1")
    return normalized


def _normalize_positive_decimal(name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(name, value)
    if normalized <= ZERO:
        raise ValueError(f"{name} must be positive")
    return normalized


def _normalize_nonnegative_decimal(name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(name, value)
    if normalized < ZERO:
        raise ValueError(f"{name} must be nonnegative")
    return normalized


def _normalize_decimal(name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{name} must be finite")
    return _quantize_ratio(value)


def _normalize_positive_count(name: str, value: object) -> Decimal:
    normalized = _normalize_nonnegative_count(name, value)
    if normalized <= ZERO:
        raise ValueError(f"{name} must be positive")
    return normalized


def _normalize_nonnegative_count(name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{name} must be finite")
    with localcontext(DECIMAL_CONTEXT):
        normalized = value.quantize(COUNT_QUANTUM)
    if normalized != value:
        raise ValueError(f"{name} must be integral")
    if normalized < ZERO:
        raise ValueError(f"{name} must be nonnegative")
    return normalized


def _count(value: int) -> Decimal:
    return Decimal(value).quantize(COUNT_QUANTUM)


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO:
        raise ValueError("denominator must be positive")
    with localcontext(DECIMAL_CONTEXT):
        value = numerator / denominator
    return _quantize_ratio(value)


def _multiply(left: Decimal, right: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return _quantize_ratio(left * right)


def _quantize_ratio(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(RATIO_QUANTUM)


def _decimal_payload(value: Decimal) -> str:
    return format(value, "f")


def _count_payload(value: Decimal) -> str:
    return format(value.quantize(COUNT_QUANTUM), "f")


def _require_safety_flags(name: str, value: object) -> None:
    if getattr(value, "paper_only", None) is not True:
        raise ValueError(f"{name} paper_only must be True")
    if getattr(value, "report_only", None) is not True:
        raise ValueError(f"{name} report_only must be True")
    if getattr(value, "readonly", None) is not True:
        raise ValueError(f"{name} readonly must be True")


def _reject_unsafe_public_payload_fields(label: str, value: object) -> None:
    for key in _public_payload_keys(value):
        if _is_unsafe_public_payload_key(key):
            raise ValueError(f"unsafe public payload field in {label}: {key}")


def _is_unsafe_public_payload_key(key: str) -> bool:
    normalized = key.lower()
    if any(fragment in normalized for fragment in UNSAFE_PUBLIC_PAYLOAD_FIELD_FRAGMENTS):
        return True
    tokens = _public_payload_key_tokens(normalized)
    return any(token in tokens for token in UNSAFE_PUBLIC_PAYLOAD_FIELD_TOKENS)


def _public_payload_key_tokens(key: str) -> tuple[str, ...]:
    tokens: list[str] = []
    current: list[str] = []
    for character in key:
        if ("a" <= character <= "z") or ("0" <= character <= "9"):
            current.append(character)
            continue
        if current:
            tokens.append("".join(current))
            current = []
    if current:
        tokens.append("".join(current))
    return tuple(tokens)


def _public_payload_keys(value: object) -> tuple[str, ...]:
    if hasattr(value, "__dataclass_fields__") and not isinstance(value, type):
        declared_keys = tuple(value.__dataclass_fields__.keys())
        object_values = vars(value)
        extra_keys = tuple(key for key in object_values if key not in declared_keys)
        keys: list[str] = [*declared_keys, *extra_keys]
        for key in (*declared_keys, *extra_keys):
            keys.extend(_public_payload_keys(getattr(value, key)))
        return tuple(keys)
    if isinstance(value, dict):
        keys = []
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("public payload keys must be strings")
            keys.append(key)
            keys.extend(_public_payload_keys(item))
        return tuple(keys)
    if isinstance(value, (list, tuple)):
        keys = []
        for item in value:
            keys.extend(_public_payload_keys(item))
        return tuple(keys)
    return ()


def _derived_validation_digest(
    report: StrategyTeamSourceReliabilityWeightDigestReport,
) -> str:
    digest_material = _digest_sequence(
        (
            f"generated_at={report.generated_at.isoformat()}",
            f"config_version={report.config_version}",
            f"source_count={_count_payload(report.source_count)}",
            f"pass_count={_count_payload(report.pass_count)}",
            f"watch_count={_count_payload(report.watch_count)}",
            f"block_count={_count_payload(report.block_count)}",
            (
                "average_reliability_weight="
                f"{_decimal_payload(report.average_reliability_weight)}"
            ),
            (
                "average_weighted_reliability_score="
                f"{_decimal_payload(report.average_weighted_reliability_score)}"
            ),
            f"status={report.status}",
            f"reason_codes={_digest_tuple(report.reason_codes)}",
            f"rows={_digest_tuple(tuple(_row_digest_material(row) for row in report.rows))}",
            (
                "reason_rollups="
                f"{_digest_tuple(tuple(_rollup_digest_material(rollup) for rollup in report.reason_rollups))}"
            ),
            f"paper_only={report.paper_only}",
            f"report_only={report.report_only}",
            f"readonly={report.readonly}",
        ),
    )
    return hashlib.sha256(digest_material.encode("utf-8")).hexdigest()


def _row_digest_material(row: StrategyTeamSourceReliabilityWeightDigestRow) -> str:
    return _digest_sequence(
        (
            f"team_id={row.team_id}",
            f"source_id={row.source_id}",
            f"observed_at={row.observed_at.isoformat()}",
            f"source_reliability={_decimal_payload(row.source_reliability)}",
            f"evidence_count={_count_payload(row.evidence_count)}",
            f"settled_evidence_count={_count_payload(row.settled_evidence_count)}",
            f"corroboration_count={_count_payload(row.corroboration_count)}",
            f"dispute_count={_count_payload(row.dispute_count)}",
            f"source_age_seconds={_decimal_payload(row.source_age_seconds)}",
            f"team_signal_weight={_decimal_payload(row.team_signal_weight)}",
            f"source_coverage_ratio={_decimal_payload(row.source_coverage_ratio)}",
            f"dispute_ratio={_decimal_payload(row.dispute_ratio)}",
            f"freshness_weight={_decimal_payload(row.freshness_weight)}",
            f"reliability_weight={_decimal_payload(row.reliability_weight)}",
            (
                "weighted_reliability_score="
                f"{_decimal_payload(row.weighted_reliability_score)}"
            ),
            f"status={row.status}",
            f"reason_codes={_digest_tuple(row.reason_codes)}",
            f"paper_only={row.paper_only}",
            f"report_only={row.report_only}",
            f"readonly={row.readonly}",
        ),
    )


def _rollup_digest_material(
    rollup: StrategyTeamSourceReliabilityWeightReasonRollup,
) -> str:
    return _digest_sequence(
        (
            f"reason_code={rollup.reason_code}",
            f"source_count={_count_payload(rollup.source_count)}",
            f"source_ratio={_decimal_payload(rollup.source_ratio)}",
            f"paper_only={rollup.paper_only}",
            f"report_only={rollup.report_only}",
            f"readonly={rollup.readonly}",
        ),
    )


def _digest_tuple(values: tuple[str, ...]) -> str:
    return _digest_sequence(values)


def _digest_sequence(values: tuple[str, ...]) -> str:
    return "".join(f"{len(value)}:{value}" for value in values)
