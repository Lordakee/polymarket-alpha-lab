"""Deterministic, report-only strategy calibration drift watch reports."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, field, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal
from hashlib import sha256
import json
import re
from typing import Any


DEFAULT_RESEARCH_STRATEGY_CALIBRATION_DRIFT_WATCH_CONFIG_VERSION = (
    "research-strategy-calibration-drift-watch-report-v0"
)

_QUANT = Decimal("0.000001")
_ZERO = Decimal("0.000000")
_ONE = Decimal("1.000000")
_SECONDS_PER_DAY = Decimal("86400")
_MICROSECONDS_PER_SECOND = Decimal("1000000")
_DIGEST_RE = re.compile(r"^[0-9a-f]{64}$")
_PUBLIC_IDENTIFIER_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,127}$")
_STATUSES = frozenset(("pass", "watch", "block"))
_UNSAFE_PUBLIC_TERMS = (
    "raw",
    "candidate",
    "market",
    "slug",
    "question",
    "source_ref",
    "source-url",
    "source_url",
    "source-text",
    "source_text",
    "http://",
    "https://",
    "dsn",
    "database",
    "table",
    "token",
    "secret",
    "auth",
    "wallet",
    "order",
    "trade",
    "trading",
    "private_key",
    "private key",
    "b" + "uy",
    "s" + "ell",
    "re" + "commend",
    "pos" + "ition",
)
_ROW_REASON_SEQUENCE = (
    "brier_score_drift_block",
    "brier_score_drift_watch",
    "calibration_error_drift_block",
    "calibration_error_drift_watch",
    "calibration_drift_block",
    "calibration_drift_watch",
    "calibration_drift_watch_pass",
    "insufficient_resolved_samples",
    "pending_sample_share_block",
    "pending_sample_share_watch",
    "stale_resolved_samples_block",
    "stale_resolved_samples_watch",
)
_REPORT_REASON_SEQUENCE = (
    "no_calibration_drift_watch_aggregates",
    "calibration_drift_watch_report_block_rows",
    "calibration_drift_watch_report_watch_rows",
    "calibration_drift_watch_report_pass",
)

__all__ = (
    "DEFAULT_RESEARCH_STRATEGY_CALIBRATION_DRIFT_WATCH_CONFIG_VERSION",
    "ResearchStrategyCalibrationDriftWatchConfig",
    "ResearchStrategyCalibrationAggregate",
    "ResearchStrategyCalibrationDriftWatchRow",
    "ResearchStrategyCalibrationDriftWatchDigest",
    "ResearchStrategyCalibrationDriftWatchReport",
    "build_research_strategy_calibration_drift_watch_report",
    "research_strategy_calibration_drift_watch_report_payload",
    "research_strategy_calibration_drift_watch_digest_payload",
)


class _FinalPublicDataclass:
    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        for base in cls.__bases__:
            if base is not _FinalPublicDataclass and issubclass(
                base,
                _FinalPublicDataclass,
            ):
                raise TypeError(f"{base.__name__} may not be subclassed")


@dataclass(frozen=True)
class ResearchStrategyCalibrationDriftWatchConfig(_FinalPublicDataclass):
    config_version: str = DEFAULT_RESEARCH_STRATEGY_CALIBRATION_DRIFT_WATCH_CONFIG_VERSION
    min_resolved_sample_count: Decimal = Decimal("30.000000")
    watch_brier_score_delta: Decimal = Decimal("0.030000")
    block_brier_score_delta: Decimal = Decimal("0.070000")
    watch_expected_calibration_error_delta: Decimal = Decimal("0.025000")
    block_expected_calibration_error_delta: Decimal = Decimal("0.060000")
    watch_pending_sample_share: Decimal = Decimal("0.600000")
    block_pending_sample_share: Decimal = Decimal("0.800000")
    watch_resolved_age_seconds: Decimal = Decimal("604800.000000")
    block_resolved_age_seconds: Decimal = Decimal("1209600.000000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchStrategyCalibrationDriftWatchConfig, "config")
        object.__setattr__(
            self,
            "config_version",
            _require_public_identifier("config_version", self.config_version),
        )
        object.__setattr__(
            self,
            "min_resolved_sample_count",
            _require_nonnegative_count_decimal(
                "min_resolved_sample_count",
                self.min_resolved_sample_count,
            ),
        )
        for name in (
            "watch_brier_score_delta",
            "block_brier_score_delta",
            "watch_expected_calibration_error_delta",
            "block_expected_calibration_error_delta",
            "watch_pending_sample_share",
            "block_pending_sample_share",
        ):
            object.__setattr__(
                self,
                name,
                _require_ratio_decimal(name, getattr(self, name)),
            )
        for name in ("watch_resolved_age_seconds", "block_resolved_age_seconds"):
            object.__setattr__(
                self,
                name,
                _require_nonnegative_decimal(name, getattr(self, name)),
            )
        if self.watch_brier_score_delta > self.block_brier_score_delta:
            raise ValueError("watch_brier_score_delta must not exceed block_brier_score_delta")
        if (
            self.watch_expected_calibration_error_delta
            > self.block_expected_calibration_error_delta
        ):
            raise ValueError(
                "watch_expected_calibration_error_delta must not exceed "
                "block_expected_calibration_error_delta",
            )
        if self.watch_pending_sample_share > self.block_pending_sample_share:
            raise ValueError("watch_pending_sample_share must not exceed block_pending_sample_share")
        if self.watch_resolved_age_seconds > self.block_resolved_age_seconds:
            raise ValueError(
                "watch_resolved_age_seconds must not exceed block_resolved_age_seconds",
            )
        _require_hard_flags("config", self)
        _reject_unsafe_public_payload("config", self)


@dataclass(frozen=True)
class ResearchStrategyCalibrationAggregate(_FinalPublicDataclass):
    research_team: str
    domain: str
    measured_at: datetime
    latest_resolved_at: datetime
    pending_sample_count: Decimal
    resolved_sample_count: Decimal
    low_confidence_count: Decimal
    medium_confidence_count: Decimal
    high_confidence_count: Decimal
    baseline_brier_score: Decimal
    current_brier_score: Decimal
    baseline_expected_calibration_error: Decimal
    current_expected_calibration_error: Decimal
    reason_codes: tuple[str, ...] = ()
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchStrategyCalibrationAggregate, "aggregate")
        object.__setattr__(
            self,
            "research_team",
            _require_public_identifier("research_team", self.research_team),
        )
        object.__setattr__(
            self,
            "domain",
            _require_public_identifier("domain", self.domain),
        )
        object.__setattr__(
            self,
            "measured_at",
            _as_utc("measured_at", self.measured_at),
        )
        object.__setattr__(
            self,
            "latest_resolved_at",
            _as_utc("latest_resolved_at", self.latest_resolved_at),
        )
        if self.latest_resolved_at > self.measured_at:
            raise ValueError("latest_resolved_at must not be after measured_at")
        for name in (
            "pending_sample_count",
            "resolved_sample_count",
            "low_confidence_count",
            "medium_confidence_count",
            "high_confidence_count",
        ):
            object.__setattr__(
                self,
                name,
                _require_nonnegative_count_decimal(name, getattr(self, name)),
            )
        for name in (
            "baseline_brier_score",
            "current_brier_score",
            "baseline_expected_calibration_error",
            "current_expected_calibration_error",
        ):
            object.__setattr__(
                self,
                name,
                _require_ratio_decimal(name, getattr(self, name)),
            )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes, _ROW_REASON_SEQUENCE),
        )
        _require_hard_flags("aggregate", self)
        _reject_unsafe_public_payload("aggregate", self)


@dataclass(frozen=True)
class ResearchStrategyCalibrationDriftWatchRow(_FinalPublicDataclass):
    research_team: str
    domain: str
    measured_at: datetime
    latest_resolved_at: datetime
    latest_resolved_age_seconds: Decimal
    pending_sample_count: Decimal
    resolved_sample_count: Decimal
    total_sample_count: Decimal
    pending_sample_share: Decimal
    low_confidence_count: Decimal
    medium_confidence_count: Decimal
    high_confidence_count: Decimal
    low_confidence_share: Decimal
    medium_confidence_share: Decimal
    high_confidence_share: Decimal
    baseline_brier_score: Decimal
    current_brier_score: Decimal
    brier_score_delta: Decimal
    absolute_brier_score_delta: Decimal
    baseline_expected_calibration_error: Decimal
    current_expected_calibration_error: Decimal
    expected_calibration_error_delta: Decimal
    absolute_expected_calibration_error_delta: Decimal
    status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchStrategyCalibrationDriftWatchRow, "row")
        object.__setattr__(
            self,
            "research_team",
            _require_public_identifier("research_team", self.research_team),
        )
        object.__setattr__(
            self,
            "domain",
            _require_public_identifier("domain", self.domain),
        )
        object.__setattr__(
            self,
            "measured_at",
            _as_utc("measured_at", self.measured_at),
        )
        object.__setattr__(
            self,
            "latest_resolved_at",
            _as_utc("latest_resolved_at", self.latest_resolved_at),
        )
        if self.latest_resolved_at > self.measured_at:
            raise ValueError("latest_resolved_at must not be after measured_at")
        for name in (
            "latest_resolved_age_seconds",
            "pending_sample_count",
            "resolved_sample_count",
            "total_sample_count",
            "low_confidence_count",
            "medium_confidence_count",
            "high_confidence_count",
        ):
            object.__setattr__(
                self,
                name,
                _require_nonnegative_count_decimal(name, getattr(self, name)),
            )
        for name in (
            "pending_sample_share",
            "low_confidence_share",
            "medium_confidence_share",
            "high_confidence_share",
            "baseline_brier_score",
            "current_brier_score",
            "absolute_brier_score_delta",
            "baseline_expected_calibration_error",
            "current_expected_calibration_error",
            "absolute_expected_calibration_error_delta",
        ):
            object.__setattr__(
                self,
                name,
                _require_ratio_decimal(name, getattr(self, name)),
            )
        for name in ("brier_score_delta", "expected_calibration_error_delta"):
            object.__setattr__(
                self,
                name,
                _require_bounded_delta_decimal(name, getattr(self, name)),
            )
        object.__setattr__(self, "status", _require_status(self.status))
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes, _ROW_REASON_SEQUENCE),
        )
        _validate_row(self)
        _require_hard_flags("row", self)
        _reject_unsafe_public_payload("row", self)


@dataclass(frozen=True)
class ResearchStrategyCalibrationDriftWatchDigest(_FinalPublicDataclass):
    generated_at: datetime
    config_version: str
    aggregate_count: Decimal
    pending_sample_count: Decimal
    resolved_sample_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    average_absolute_brier_score_delta: Decimal
    max_absolute_brier_score_delta: Decimal
    average_absolute_expected_calibration_error_delta: Decimal
    max_absolute_expected_calibration_error_delta: Decimal
    max_latest_resolved_age_seconds: Decimal
    status: str
    reason_codes: tuple[str, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True
    payload: dict[str, Any] = field(default_factory=dict, compare=False)

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchStrategyCalibrationDriftWatchDigest, "digest")
        _normalize_summary_fields(self)
        _validate_summary_counts(self)
        object.__setattr__(self, "status", _require_status(self.status))
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes, _REPORT_REASON_SEQUENCE),
        )
        if self.status != _summary_status_from_counts(
            block_count=self.block_count,
            watch_count=self.watch_count,
            aggregate_count=self.aggregate_count,
        ):
            raise ValueError("status must match summary counts")
        if self.reason_codes != _report_reason_codes(
            block_count=self.block_count,
            watch_count=self.watch_count,
            aggregate_count=self.aggregate_count,
        ):
            raise ValueError("reason_codes must match status")
        _require_hard_flags("digest", self)
        _reject_unsafe_public_payload("digest", self)
        _finalize_digest_payload(self)


@dataclass(frozen=True)
class ResearchStrategyCalibrationDriftWatchReport(_FinalPublicDataclass):
    generated_at: datetime
    config_version: str
    aggregate_count: Decimal
    pending_sample_count: Decimal
    resolved_sample_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    average_absolute_brier_score_delta: Decimal
    max_absolute_brier_score_delta: Decimal
    average_absolute_expected_calibration_error_delta: Decimal
    max_absolute_expected_calibration_error_delta: Decimal
    max_latest_resolved_age_seconds: Decimal
    status: str
    reason_codes: tuple[str, ...]
    digest: ResearchStrategyCalibrationDriftWatchDigest
    rows: tuple[ResearchStrategyCalibrationDriftWatchRow, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True
    payload: dict[str, Any] = field(default_factory=dict, compare=False)

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchStrategyCalibrationDriftWatchReport, "report")
        _normalize_summary_fields(self)
        object.__setattr__(self, "status", _require_status(self.status))
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes, _REPORT_REASON_SEQUENCE),
        )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        if type(self.digest) is not ResearchStrategyCalibrationDriftWatchDigest:
            raise ValueError("digest must be a ResearchStrategyCalibrationDriftWatchDigest")
        _validate_report(self)
        _validate_summary_counts(self)
        _require_hard_flags("report", self)
        _reject_unsafe_public_payload("report", self)
        _finalize_report_payload(self)


def build_research_strategy_calibration_drift_watch_report(
    aggregates: Iterable[object],
    *,
    config: ResearchStrategyCalibrationDriftWatchConfig,
    generated_at: datetime,
) -> ResearchStrategyCalibrationDriftWatchReport:
    if type(config) is not ResearchStrategyCalibrationDriftWatchConfig:
        raise ValueError("config must be a ResearchStrategyCalibrationDriftWatchConfig")
    _require_hard_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    items = _normalize_aggregates(aggregates)
    for item in items:
        if item.measured_at > generated_at_utc:
            raise ValueError("measured_at must not be after generated_at")
        if item.latest_resolved_at > generated_at_utc:
            raise ValueError("latest_resolved_at must not be after generated_at")
    rows = tuple(
        sorted(
            (_row_from_aggregate(item, config, generated_at_utc) for item in items),
            key=_row_key,
        ),
    )
    summary = _summary_values(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        rows=rows,
    )
    digest = ResearchStrategyCalibrationDriftWatchDigest(**summary)
    return ResearchStrategyCalibrationDriftWatchReport(
        **summary,
        digest=digest,
        rows=rows,
    )


def research_strategy_calibration_drift_watch_report_payload(
    report: ResearchStrategyCalibrationDriftWatchReport | dict[str, Any],
) -> dict[str, Any]:
    if type(report) is ResearchStrategyCalibrationDriftWatchReport:
        _require_hard_flags("report", report)
        _validate_payload_digest("report", report.payload)
        return report.payload
    if type(report) is dict:
        _validate_payload_digest("report", report)
        digest_payload = report.get("digest")
        if type(digest_payload) is not dict:
            raise ValueError("digest must be a payload object")
        _validate_payload_digest("digest", digest_payload)
        return report
    raise ValueError("report must be a ResearchStrategyCalibrationDriftWatchReport")


def research_strategy_calibration_drift_watch_digest_payload(
    digest: ResearchStrategyCalibrationDriftWatchDigest | dict[str, Any],
) -> dict[str, Any]:
    if type(digest) is ResearchStrategyCalibrationDriftWatchDigest:
        _require_hard_flags("digest", digest)
        _validate_payload_digest("digest", digest.payload)
        return digest.payload
    if type(digest) is dict:
        _validate_payload_digest("digest", digest)
        return digest
    raise ValueError("digest must be a ResearchStrategyCalibrationDriftWatchDigest")


def _row_from_aggregate(
    item: ResearchStrategyCalibrationAggregate,
    config: ResearchStrategyCalibrationDriftWatchConfig,
    generated_at: datetime,
) -> ResearchStrategyCalibrationDriftWatchRow:
    brier_delta = _quantize(item.current_brier_score - item.baseline_brier_score)
    error_delta = _quantize(
        item.current_expected_calibration_error
        - item.baseline_expected_calibration_error,
    )
    total_sample_count = _quantize(item.pending_sample_count + item.resolved_sample_count)
    confidence_sample_count = _quantize(
        item.low_confidence_count
        + item.medium_confidence_count
        + item.high_confidence_count,
    )
    pending_sample_share = _safe_ratio(item.pending_sample_count, total_sample_count)
    latest_age_seconds = _age_seconds(generated_at, item.latest_resolved_at)
    status, reason_codes = _row_status_and_reasons(
        resolved_sample_count=item.resolved_sample_count,
        pending_sample_share=pending_sample_share,
        latest_resolved_age_seconds=latest_age_seconds,
        absolute_brier_score_delta=_absolute_decimal(brier_delta),
        absolute_expected_calibration_error_delta=_absolute_decimal(error_delta),
        config=config,
    )
    return ResearchStrategyCalibrationDriftWatchRow(
        research_team=item.research_team,
        domain=item.domain,
        measured_at=item.measured_at,
        latest_resolved_at=item.latest_resolved_at,
        latest_resolved_age_seconds=latest_age_seconds,
        pending_sample_count=item.pending_sample_count,
        resolved_sample_count=item.resolved_sample_count,
        total_sample_count=total_sample_count,
        pending_sample_share=pending_sample_share,
        low_confidence_count=item.low_confidence_count,
        medium_confidence_count=item.medium_confidence_count,
        high_confidence_count=item.high_confidence_count,
        low_confidence_share=_safe_ratio(item.low_confidence_count, confidence_sample_count),
        medium_confidence_share=_safe_ratio(
            item.medium_confidence_count,
            confidence_sample_count,
        ),
        high_confidence_share=_safe_ratio(item.high_confidence_count, confidence_sample_count),
        baseline_brier_score=item.baseline_brier_score,
        current_brier_score=item.current_brier_score,
        brier_score_delta=brier_delta,
        absolute_brier_score_delta=_absolute_decimal(brier_delta),
        baseline_expected_calibration_error=item.baseline_expected_calibration_error,
        current_expected_calibration_error=item.current_expected_calibration_error,
        expected_calibration_error_delta=error_delta,
        absolute_expected_calibration_error_delta=_absolute_decimal(error_delta),
        status=status,
        reason_codes=reason_codes,
    )


def _row_status_and_reasons(
    *,
    resolved_sample_count: Decimal,
    pending_sample_share: Decimal,
    latest_resolved_age_seconds: Decimal,
    absolute_brier_score_delta: Decimal,
    absolute_expected_calibration_error_delta: Decimal,
    config: ResearchStrategyCalibrationDriftWatchConfig,
) -> tuple[str, tuple[str, ...]]:
    status = "pass"
    reasons: list[str] = []

    if absolute_brier_score_delta >= config.block_brier_score_delta:
        status = "block"
        reasons.append("brier_score_drift_block")
    elif absolute_brier_score_delta >= config.watch_brier_score_delta:
        status = "watch"
        reasons.append("brier_score_drift_watch")

    if absolute_expected_calibration_error_delta >= (
        config.block_expected_calibration_error_delta
    ):
        status = "block"
        reasons.append("calibration_error_drift_block")
    elif absolute_expected_calibration_error_delta >= (
        config.watch_expected_calibration_error_delta
    ):
        if status != "block":
            status = "watch"
        reasons.append("calibration_error_drift_watch")

    if resolved_sample_count < config.min_resolved_sample_count:
        status = "block"
        reasons.append("insufficient_resolved_samples")

    if pending_sample_share >= config.block_pending_sample_share:
        status = "block"
        reasons.append("pending_sample_share_block")
    elif pending_sample_share >= config.watch_pending_sample_share:
        if status != "block":
            status = "watch"
        reasons.append("pending_sample_share_watch")

    if latest_resolved_age_seconds >= config.block_resolved_age_seconds:
        status = "block"
        reasons.append("stale_resolved_samples_block")
    elif latest_resolved_age_seconds >= config.watch_resolved_age_seconds:
        if status != "block":
            status = "watch"
        reasons.append("stale_resolved_samples_watch")

    if status == "block":
        reasons.append("calibration_drift_block")
    elif status == "watch":
        reasons.append("calibration_drift_watch")
    else:
        reasons.append("calibration_drift_watch_pass")
    return status, _normalize_reason_codes(tuple(reasons), _ROW_REASON_SEQUENCE)


def _summary_values(
    *,
    generated_at: datetime,
    config_version: str,
    rows: tuple[ResearchStrategyCalibrationDriftWatchRow, ...],
) -> dict[str, Any]:
    block_count = _decimal_count(sum(1 for row in rows if row.status == "block"))
    watch_count = _decimal_count(sum(1 for row in rows if row.status == "watch"))
    aggregate_count = _decimal_count(len(rows))
    status = _summary_status_from_counts(
        block_count=block_count,
        watch_count=watch_count,
        aggregate_count=aggregate_count,
    )
    return {
        "generated_at": generated_at,
        "config_version": config_version,
        "aggregate_count": aggregate_count,
        "pending_sample_count": sum((row.pending_sample_count for row in rows), _ZERO),
        "resolved_sample_count": sum((row.resolved_sample_count for row in rows), _ZERO),
        "pass_count": _decimal_count(sum(1 for row in rows if row.status == "pass")),
        "watch_count": watch_count,
        "block_count": block_count,
        "average_absolute_brier_score_delta": _mean(
            tuple(row.absolute_brier_score_delta for row in rows),
        ),
        "max_absolute_brier_score_delta": _max_decimal(
            tuple(row.absolute_brier_score_delta for row in rows),
        ),
        "average_absolute_expected_calibration_error_delta": _mean(
            tuple(row.absolute_expected_calibration_error_delta for row in rows),
        ),
        "max_absolute_expected_calibration_error_delta": _max_decimal(
            tuple(row.absolute_expected_calibration_error_delta for row in rows),
        ),
        "max_latest_resolved_age_seconds": _max_decimal(
            tuple(row.latest_resolved_age_seconds for row in rows),
        ),
        "status": status,
        "reason_codes": _report_reason_codes(
            block_count=block_count,
            watch_count=watch_count,
            aggregate_count=aggregate_count,
        ),
    }


def _normalize_summary_fields(
    value: (
        ResearchStrategyCalibrationDriftWatchDigest
        | ResearchStrategyCalibrationDriftWatchReport
    ),
) -> None:
    object.__setattr__(value, "generated_at", _as_utc("generated_at", value.generated_at))
    object.__setattr__(
        value,
        "config_version",
        _require_public_identifier("config_version", value.config_version),
    )
    for name in (
        "aggregate_count",
        "pending_sample_count",
        "resolved_sample_count",
        "pass_count",
        "watch_count",
        "block_count",
        "max_latest_resolved_age_seconds",
    ):
        object.__setattr__(
            value,
            name,
            _require_nonnegative_count_decimal(name, getattr(value, name)),
        )
    for name in (
        "average_absolute_brier_score_delta",
        "max_absolute_brier_score_delta",
        "average_absolute_expected_calibration_error_delta",
        "max_absolute_expected_calibration_error_delta",
    ):
        object.__setattr__(
            value,
            name,
            _require_ratio_decimal(name, getattr(value, name)),
        )


def _validate_summary_counts(
    value: (
        ResearchStrategyCalibrationDriftWatchDigest
        | ResearchStrategyCalibrationDriftWatchReport
    ),
) -> None:
    if value.pass_count + value.watch_count + value.block_count != value.aggregate_count:
        raise ValueError("status counts must match aggregate_count")
    if value.max_absolute_brier_score_delta < value.average_absolute_brier_score_delta:
        raise ValueError("max_absolute_brier_score_delta must be at least average")
    if (
        value.max_absolute_expected_calibration_error_delta
        < value.average_absolute_expected_calibration_error_delta
    ):
        raise ValueError(
            "max_absolute_expected_calibration_error_delta must be at least average",
        )


def _validate_report(report: ResearchStrategyCalibrationDriftWatchReport) -> None:
    if report.rows != tuple(sorted(report.rows, key=_row_key)):
        raise ValueError("rows must be sorted by research team and domain")
    if len({(row.research_team, row.domain) for row in report.rows}) != len(report.rows):
        raise ValueError("rows must contain unique research team and domain pairs")
    if report.aggregate_count != _decimal_count(len(report.rows)):
        raise ValueError("aggregate_count must match rows")
    if report.pending_sample_count != sum(
        (row.pending_sample_count for row in report.rows),
        _ZERO,
    ):
        raise ValueError("pending_sample_count must match rows")
    if report.resolved_sample_count != sum(
        (row.resolved_sample_count for row in report.rows),
        _ZERO,
    ):
        raise ValueError("resolved_sample_count must match rows")
    if report.pass_count != _decimal_count(sum(1 for row in report.rows if row.status == "pass")):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _decimal_count(
        sum(1 for row in report.rows if row.status == "watch"),
    ):
        raise ValueError("watch_count must match rows")
    if report.block_count != _decimal_count(
        sum(1 for row in report.rows if row.status == "block"),
    ):
        raise ValueError("block_count must match rows")
    if report.average_absolute_brier_score_delta != _mean(
        tuple(row.absolute_brier_score_delta for row in report.rows),
    ):
        raise ValueError("average_absolute_brier_score_delta must match rows")
    if report.max_absolute_brier_score_delta != _max_decimal(
        tuple(row.absolute_brier_score_delta for row in report.rows),
    ):
        raise ValueError("max_absolute_brier_score_delta must match rows")
    if report.average_absolute_expected_calibration_error_delta != _mean(
        tuple(row.absolute_expected_calibration_error_delta for row in report.rows),
    ):
        raise ValueError(
            "average_absolute_expected_calibration_error_delta must match rows",
        )
    if report.max_absolute_expected_calibration_error_delta != _max_decimal(
        tuple(row.absolute_expected_calibration_error_delta for row in report.rows),
    ):
        raise ValueError("max_absolute_expected_calibration_error_delta must match rows")
    if report.max_latest_resolved_age_seconds != _max_decimal(
        tuple(row.latest_resolved_age_seconds for row in report.rows),
    ):
        raise ValueError("max_latest_resolved_age_seconds must match rows")
    if report.status != _summary_status_from_counts(
        block_count=report.block_count,
        watch_count=report.watch_count,
        aggregate_count=report.aggregate_count,
    ):
        raise ValueError("status must match rows")
    if report.reason_codes != _report_reason_codes(
        block_count=report.block_count,
        watch_count=report.watch_count,
        aggregate_count=report.aggregate_count,
    ):
        raise ValueError("reason_codes must match rows")
    if not _digest_matches_report(report.digest, report):
        raise ValueError("digest must match report summary")


def _validate_row(row: ResearchStrategyCalibrationDriftWatchRow) -> None:
    if row.total_sample_count != row.pending_sample_count + row.resolved_sample_count:
        raise ValueError("total_sample_count must match sample counts")
    if row.pending_sample_share != _safe_ratio(
        row.pending_sample_count,
        row.total_sample_count,
    ):
        raise ValueError("pending_sample_share must match sample counts")
    confidence_sample_count = _quantize(
        row.low_confidence_count
        + row.medium_confidence_count
        + row.high_confidence_count,
    )
    if row.low_confidence_share != _safe_ratio(
        row.low_confidence_count,
        confidence_sample_count,
    ):
        raise ValueError("low_confidence_share must match confidence counts")
    if row.medium_confidence_share != _safe_ratio(
        row.medium_confidence_count,
        confidence_sample_count,
    ):
        raise ValueError("medium_confidence_share must match confidence counts")
    if row.high_confidence_share != _safe_ratio(
        row.high_confidence_count,
        confidence_sample_count,
    ):
        raise ValueError("high_confidence_share must match confidence counts")
    expected_brier_delta = _quantize(row.current_brier_score - row.baseline_brier_score)
    expected_error_delta = _quantize(
        row.current_expected_calibration_error
        - row.baseline_expected_calibration_error,
    )
    if row.brier_score_delta != expected_brier_delta:
        raise ValueError("brier_score_delta must match scores")
    if row.expected_calibration_error_delta != expected_error_delta:
        raise ValueError("expected_calibration_error_delta must match scores")
    if row.absolute_brier_score_delta != _absolute_decimal(row.brier_score_delta):
        raise ValueError("absolute_brier_score_delta must match brier_score_delta")
    if row.absolute_expected_calibration_error_delta != _absolute_decimal(
        row.expected_calibration_error_delta,
    ):
        raise ValueError(
            "absolute_expected_calibration_error_delta must match "
            "expected_calibration_error_delta",
        )
    if row.status != _row_status_from_reason_codes(row.reason_codes):
        raise ValueError("status must match reason_codes")


def _digest_matches_report(
    digest: ResearchStrategyCalibrationDriftWatchDigest,
    report: ResearchStrategyCalibrationDriftWatchReport,
) -> bool:
    names = (
        "generated_at",
        "config_version",
        "aggregate_count",
        "pending_sample_count",
        "resolved_sample_count",
        "pass_count",
        "watch_count",
        "block_count",
        "average_absolute_brier_score_delta",
        "max_absolute_brier_score_delta",
        "average_absolute_expected_calibration_error_delta",
        "max_absolute_expected_calibration_error_delta",
        "max_latest_resolved_age_seconds",
        "status",
        "reason_codes",
    )
    return all(getattr(digest, name) == getattr(report, name) for name in names)


def _finalize_digest_payload(digest: ResearchStrategyCalibrationDriftWatchDigest) -> None:
    base_payload = _digest_payload_base(digest)
    expected_digest = _payload_digest(base_payload)
    supplied = digest.derived_validation_digest
    if supplied == "":
        object.__setattr__(digest, "derived_validation_digest", expected_digest)
    elif supplied != expected_digest:
        raise ValueError("derived_validation_digest must match report fields")
    payload = dict(base_payload)
    payload["derived_validation_digest"] = digest.derived_validation_digest
    _reject_unsafe_public_payload("digest.payload", payload)
    object.__setattr__(digest, "payload", payload)


def _finalize_report_payload(report: ResearchStrategyCalibrationDriftWatchReport) -> None:
    base_payload = _report_payload_base(report)
    expected_digest = _payload_digest(base_payload)
    supplied = report.derived_validation_digest
    if supplied == "":
        object.__setattr__(report, "derived_validation_digest", expected_digest)
    elif supplied != expected_digest:
        raise ValueError("derived_validation_digest must match report fields")
    payload = dict(base_payload)
    payload["derived_validation_digest"] = report.derived_validation_digest
    _reject_unsafe_public_payload("report.payload", payload)
    object.__setattr__(report, "payload", payload)


def _digest_payload_base(digest: ResearchStrategyCalibrationDriftWatchDigest) -> dict[str, Any]:
    return {
        "generated_at": digest.generated_at.isoformat(),
        "config_version": digest.config_version,
        "aggregate_count": _decimal_string(digest.aggregate_count),
        "pending_sample_count": _decimal_string(digest.pending_sample_count),
        "resolved_sample_count": _decimal_string(digest.resolved_sample_count),
        "pass_count": _decimal_string(digest.pass_count),
        "watch_count": _decimal_string(digest.watch_count),
        "block_count": _decimal_string(digest.block_count),
        "average_absolute_brier_score_delta": _decimal_string(
            digest.average_absolute_brier_score_delta,
        ),
        "max_absolute_brier_score_delta": _decimal_string(
            digest.max_absolute_brier_score_delta,
        ),
        "average_absolute_expected_calibration_error_delta": _decimal_string(
            digest.average_absolute_expected_calibration_error_delta,
        ),
        "max_absolute_expected_calibration_error_delta": _decimal_string(
            digest.max_absolute_expected_calibration_error_delta,
        ),
        "max_latest_resolved_age_seconds": _decimal_string(
            digest.max_latest_resolved_age_seconds,
        ),
        "status": digest.status,
        "reason_codes": list(digest.reason_codes),
        "paper_only": digest.paper_only,
        "report_only": digest.report_only,
        "readonly": digest.readonly,
    }


def _report_payload_base(report: ResearchStrategyCalibrationDriftWatchReport) -> dict[str, Any]:
    return {
        "generated_at": report.generated_at.isoformat(),
        "config_version": report.config_version,
        "aggregate_count": _decimal_string(report.aggregate_count),
        "pending_sample_count": _decimal_string(report.pending_sample_count),
        "resolved_sample_count": _decimal_string(report.resolved_sample_count),
        "pass_count": _decimal_string(report.pass_count),
        "watch_count": _decimal_string(report.watch_count),
        "block_count": _decimal_string(report.block_count),
        "average_absolute_brier_score_delta": _decimal_string(
            report.average_absolute_brier_score_delta,
        ),
        "max_absolute_brier_score_delta": _decimal_string(
            report.max_absolute_brier_score_delta,
        ),
        "average_absolute_expected_calibration_error_delta": _decimal_string(
            report.average_absolute_expected_calibration_error_delta,
        ),
        "max_absolute_expected_calibration_error_delta": _decimal_string(
            report.max_absolute_expected_calibration_error_delta,
        ),
        "max_latest_resolved_age_seconds": _decimal_string(
            report.max_latest_resolved_age_seconds,
        ),
        "status": report.status,
        "reason_codes": list(report.reason_codes),
        "digest": report.digest.payload,
        "rows": [_row_payload(row) for row in report.rows],
        "paper_only": report.paper_only,
        "report_only": report.report_only,
        "readonly": report.readonly,
    }


def _row_payload(row: ResearchStrategyCalibrationDriftWatchRow) -> dict[str, Any]:
    return {
        "team_digest": _public_digest(row.research_team),
        "domain_digest": _public_digest(row.domain),
        "measured_at": row.measured_at.isoformat(),
        "latest_resolved_at": row.latest_resolved_at.isoformat(),
        "latest_resolved_age_seconds": _decimal_string(row.latest_resolved_age_seconds),
        "pending_sample_count": _decimal_string(row.pending_sample_count),
        "resolved_sample_count": _decimal_string(row.resolved_sample_count),
        "total_sample_count": _decimal_string(row.total_sample_count),
        "pending_sample_share": _decimal_string(row.pending_sample_share),
        "low_confidence_count": _decimal_string(row.low_confidence_count),
        "medium_confidence_count": _decimal_string(row.medium_confidence_count),
        "high_confidence_count": _decimal_string(row.high_confidence_count),
        "low_confidence_share": _decimal_string(row.low_confidence_share),
        "medium_confidence_share": _decimal_string(row.medium_confidence_share),
        "high_confidence_share": _decimal_string(row.high_confidence_share),
        "baseline_brier_score": _decimal_string(row.baseline_brier_score),
        "current_brier_score": _decimal_string(row.current_brier_score),
        "brier_score_delta": _decimal_string(row.brier_score_delta),
        "absolute_brier_score_delta": _decimal_string(row.absolute_brier_score_delta),
        "baseline_expected_calibration_error": _decimal_string(
            row.baseline_expected_calibration_error,
        ),
        "current_expected_calibration_error": _decimal_string(
            row.current_expected_calibration_error,
        ),
        "expected_calibration_error_delta": _decimal_string(
            row.expected_calibration_error_delta,
        ),
        "absolute_expected_calibration_error_delta": _decimal_string(
            row.absolute_expected_calibration_error_delta,
        ),
        "status": row.status,
        "reason_codes": list(row.reason_codes),
        "paper_only": row.paper_only,
        "report_only": row.report_only,
        "readonly": row.readonly,
    }


def _normalize_aggregates(
    aggregates: Iterable[object],
) -> tuple[ResearchStrategyCalibrationAggregate, ...]:
    if isinstance(aggregates, (str, bytes)) or not isinstance(aggregates, Iterable):
        raise ValueError("aggregates must be an iterable")
    items = tuple(aggregates)
    for item in items:
        if type(item) is not ResearchStrategyCalibrationAggregate:
            raise ValueError(
                "aggregates must contain ResearchStrategyCalibrationAggregate values",
            )
        _require_hard_flags("aggregate", item)
    if len({(item.research_team, item.domain) for item in items}) != len(items):
        raise ValueError("aggregates must contain unique research team and domain pairs")
    return items


def _normalize_rows(
    rows: object,
) -> tuple[ResearchStrategyCalibrationDriftWatchRow, ...]:
    if type(rows) not in (list, tuple):
        raise ValueError("rows must be a list or tuple")
    clean = tuple(rows)
    for row in clean:
        if type(row) is not ResearchStrategyCalibrationDriftWatchRow:
            raise ValueError(
                "rows must contain ResearchStrategyCalibrationDriftWatchRow values",
            )
        _require_hard_flags("row", row)
    return clean


def _normalize_reason_codes(
    value: object,
    allowed_sequence: tuple[str, ...],
) -> tuple[str, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("reason_codes must be a list or tuple")
    clean: list[str] = []
    allowed = frozenset(allowed_sequence)
    for item in value:
        if type(item) is not str:
            raise ValueError("reason_codes must contain strings")
        code = _require_public_identifier("reason_codes", item)
        if code not in allowed:
            raise ValueError("reason_codes contains an unknown reason code")
        if code not in clean:
            clean.append(code)
    return tuple(code for code in allowed_sequence if code in clean)


def _row_status_from_reason_codes(reason_codes: tuple[str, ...]) -> str:
    if "calibration_drift_block" in reason_codes:
        return "block"
    if "calibration_drift_watch" in reason_codes:
        return "watch"
    return "pass"


def _summary_status_from_counts(
    *,
    block_count: Decimal,
    watch_count: Decimal,
    aggregate_count: Decimal,
) -> str:
    if aggregate_count == _ZERO or block_count > _ZERO:
        return "block"
    if watch_count > _ZERO:
        return "watch"
    return "pass"


def _report_reason_codes(
    *,
    block_count: Decimal,
    watch_count: Decimal,
    aggregate_count: Decimal,
) -> tuple[str, ...]:
    if aggregate_count == _ZERO:
        return ("no_calibration_drift_watch_aggregates",)
    reasons: list[str] = []
    if block_count > _ZERO:
        reasons.append("calibration_drift_watch_report_block_rows")
    if watch_count > _ZERO:
        reasons.append("calibration_drift_watch_report_watch_rows")
    if not reasons:
        reasons.append("calibration_drift_watch_report_pass")
    return tuple(reasons)


def _row_key(row: ResearchStrategyCalibrationDriftWatchRow) -> tuple[str, str]:
    return (row.research_team, row.domain)


def _age_seconds(generated_at: datetime, observed_at: datetime) -> Decimal:
    delta = generated_at - observed_at
    if delta.days < 0:
        raise ValueError("observed_at must not be after generated_at")
    return _quantize(
        Decimal(delta.days) * _SECONDS_PER_DAY
        + Decimal(delta.seconds)
        + (Decimal(delta.microseconds) / _MICROSECONDS_PER_SECOND),
    )


def _mean(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return _ZERO
    return _quantize(sum(values, _ZERO) / Decimal(len(values)))


def _max_decimal(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return _ZERO
    return max(values)


def _decimal_count(value: int) -> Decimal:
    return _quantize(Decimal(value))


def _safe_ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == _ZERO:
        return _ZERO
    return _quantize(numerator / denominator)


def _absolute_decimal(value: Decimal) -> Decimal:
    if value < _ZERO:
        return _quantize(-value)
    return _quantize(value)


def _quantize(value: Decimal) -> Decimal:
    return value.quantize(_QUANT)


def _require_ratio_decimal(field_name: str, value: object) -> Decimal:
    clean = _require_decimal(field_name, value)
    if clean < _ZERO:
        raise ValueError(f"{field_name} must be >= 0.000000")
    if clean > _ONE:
        raise ValueError(f"{field_name} must be <= 1.000000")
    return clean


def _require_bounded_delta_decimal(field_name: str, value: object) -> Decimal:
    clean = _require_decimal(field_name, value)
    if clean < -_ONE:
        raise ValueError(f"{field_name} must be >= -1.000000")
    if clean > _ONE:
        raise ValueError(f"{field_name} must be <= 1.000000")
    return clean


def _require_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    clean = _require_decimal(field_name, value)
    if clean < _ZERO:
        raise ValueError(f"{field_name} must be >= 0.000000")
    return clean


def _require_nonnegative_count_decimal(field_name: str, value: object) -> Decimal:
    clean = _require_decimal(field_name, value)
    if clean < _ZERO:
        raise ValueError(f"{field_name} must be >= 0.000000")
    if clean != clean.to_integral_value():
        raise ValueError(f"{field_name} must be an integral Decimal")
    return clean


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be exactly Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    if value.as_tuple().exponent < -6:
        raise ValueError(f"{field_name} must use six decimal places or fewer")
    return _quantize(value)


def _decimal_string(value: Decimal) -> str:
    return format(_quantize(value), "f")


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_public_identifier(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if _PUBLIC_IDENTIFIER_RE.fullmatch(value) is None:
        raise ValueError(f"{field_name} must be a canonical public identifier")
    _reject_unsafe_public_payload(field_name, value)
    return value


def _require_status(value: object) -> str:
    if type(value) is not str or value not in _STATUSES:
        raise ValueError("status must be pass, watch, or block")
    return value


def _require_exact_type(value: object, expected_type: type[object], field_name: str) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{field_name} must be exactly {expected_type.__name__}")


def _require_hard_flags(field_name: str, value: object) -> None:
    if getattr(value, "paper_only", None) is not True:
        raise ValueError("paper_only must be True")
    if getattr(value, "report_only", None) is not True:
        raise ValueError("report_only must be True")
    if getattr(value, "readonly", None) is not True:
        raise ValueError("readonly must be True")


def _reject_unsafe_public_payload(label: str, value: object) -> None:
    if is_dataclass(value) and not isinstance(value, type):
        for item in fields(value):
            _reject_unsafe_public_payload(
                f"{label}.{item.name}",
                getattr(value, item.name),
            )
        return
    if type(value) is str:
        lower_value = value.lower()
        if any(term in lower_value for term in _UNSAFE_PUBLIC_TERMS):
            raise ValueError("unsafe public payload")
        return
    if isinstance(value, Decimal):
        if type(value) is not Decimal:
            raise ValueError("unsafe public payload")
        if not value.is_finite():
            raise ValueError("unsafe public payload")
        return
    if isinstance(value, datetime):
        if type(value) is not datetime:
            raise ValueError("unsafe public payload")
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("unsafe public payload")
        return
    if value is None or type(value) is bool:
        return
    if type(value) in (int, float):
        raise ValueError("unsafe public payload")
    if isinstance(value, dict):
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("unsafe public payload")
            _reject_unsafe_public_payload(f"{label}.key", key)
            if key in {"paper_only", "report_only", "readonly"} and item is not True:
                raise ValueError("unsafe public payload")
            _reject_unsafe_public_payload(f"{label}.{key}", item)
        return
    if isinstance(value, (list, tuple)):
        for item in value:
            _reject_unsafe_public_payload(label, item)
        return
    raise ValueError("unsafe public payload")


def _public_digest(value: str) -> str:
    return f"sha256:{sha256(value.encode('utf-8')).hexdigest()}"


def _payload_digest(payload: dict[str, Any]) -> str:
    encoded = json.dumps(
        payload,
        allow_nan=False,
        separators=(",", ":"),
        sort_keys=True,
    )
    return sha256(encoded.encode("utf-8")).hexdigest()


def _validate_payload_digest(label: str, payload: dict[str, Any]) -> None:
    if type(payload) is not dict:
        raise ValueError(f"{label} payload must be a JSON object")
    _reject_unsafe_public_payload(label, payload)
    supplied = payload.get("derived_validation_digest")
    if type(supplied) is not str or _DIGEST_RE.fullmatch(supplied) is None:
        raise ValueError("derived_validation_digest must be a lowercase sha256 digest")
    base_payload = {
        key: value
        for key, value in payload.items()
        if key != "derived_validation_digest"
    }
    if _payload_digest(base_payload) != supplied:
        raise ValueError("derived_validation_digest must match payload fields")
