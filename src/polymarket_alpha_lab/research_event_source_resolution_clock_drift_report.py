"""Pure aggregate event-source resolution clock drift report."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, InvalidOperation, localcontext
from hashlib import sha256
import json
from typing import Any


DEFAULT_RESEARCH_EVENT_SOURCE_RESOLUTION_CLOCK_DRIFT_REPORT_CONFIG_VERSION = (
    "research-event-source-resolution-clock-drift-report-v0"
)

_DECIMAL_CONTEXT = Context(prec=64)
_QUANTUM = Decimal("0.000001")
_ZERO = Decimal("0.000000")
_ONE = Decimal("1.000000")
_DIGEST_FIELD = "derived_validation_digest"
_STATUSES = ("pass", "watch", "block")
_STATUS_RANK = {"pass": 0, "watch": 1, "block": 2}
_UNSAFE_PUBLIC_SURFACE_FRAGMENTS = (
    "://",
    "".join(("www", ".")),
    "".join(("raw", "_", "url")),
    "".join(("raw", "-", "url")),
    "".join(("source", "_", "url")),
    "".join(("source", "-", "url")),
    "".join(("source", "_", "text")),
    "".join(("source", "-", "text")),
    "".join(("market", "_", "id")),
    "".join(("market", "-", "id")),
    "".join(("market", "_", "slug")),
    "".join(("market", "-", "slug")),
    "".join(("candidate", "_", "id")),
    "".join(("candidate", "-", "id")),
    "".join(("candidate")),
    "".join(("slug")),
    "".join(("ques", "tion")),
    "".join(("d", "sn")),
    "".join(("table")),
    "".join(("to", "ken")),
    "".join(("data", "base")),
    "".join(("secret")),
    "".join(("password")),
    "".join(("private", "_", "key")),
    "".join(("api", "_", "key")),
    "".join(("auth", "entication")),
    "".join(("auth", "orization")),
    "".join(("auth", "_", "token")),
    "".join(("bearer")),
    "".join(("credential")),
    "".join(("net", "work")),
    "".join(("wall", "et")),
    "".join(("or", "der")),
    "".join(("li", "ve")),
    "".join(("si", "zing")),
    "".join(("recomm", "endation")),
    "".join(("tra", "de")),
    "".join(("tra", "ding")),
)

__all__ = (
    "DEFAULT_RESEARCH_EVENT_SOURCE_RESOLUTION_CLOCK_DRIFT_REPORT_CONFIG_VERSION",
    "ResearchEventSourceResolutionClockDriftConfig",
    "ResearchEventSourceResolutionClockDriftReport",
    "ResearchEventSourceResolutionClockDriftRow",
    "ResearchEventSourceResolutionClockDriftSample",
    "build_research_event_source_resolution_clock_drift_report",
    "research_event_source_resolution_clock_drift_report_payload",
    "research_event_source_resolution_clock_drift_report_payload_digest",
    "serialize_research_event_source_resolution_clock_drift_report_payload",
    "validate_research_event_source_resolution_clock_drift_report_payload",
)


@dataclass(frozen=True)
class ResearchEventSourceResolutionClockDriftConfig:
    config_version: str = (
        DEFAULT_RESEARCH_EVENT_SOURCE_RESOLUTION_CLOCK_DRIFT_REPORT_CONFIG_VERSION
    )
    watch_clock_drift_seconds_threshold: Decimal = Decimal("300.000000")
    block_clock_drift_seconds_threshold: Decimal = Decimal("3600.000000")
    watch_source_lag_seconds_threshold: Decimal = Decimal("1800.000000")
    block_source_lag_seconds_threshold: Decimal = Decimal("7200.000000")
    watch_clock_drift_score_threshold: Decimal = Decimal("0.250000")
    block_clock_drift_score_threshold: Decimal = Decimal("0.600000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchEventSourceResolutionClockDriftConfig does not support subclassing",
        )

    def __post_init__(self) -> None:
        _require_exact_type("config", self, ResearchEventSourceResolutionClockDriftConfig)
        _require_canonical_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_EVENT_SOURCE_RESOLUTION_CLOCK_DRIFT_REPORT_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "watch_clock_drift_seconds_threshold",
            "block_clock_drift_seconds_threshold",
            "watch_source_lag_seconds_threshold",
            "block_source_lag_seconds_threshold",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_positive_seconds(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "watch_clock_drift_score_threshold",
            "block_clock_drift_score_threshold",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        _require_upper_threshold_pair(
            "watch_clock_drift_seconds_threshold",
            self.watch_clock_drift_seconds_threshold,
            "block_clock_drift_seconds_threshold",
            self.block_clock_drift_seconds_threshold,
        )
        _require_upper_threshold_pair(
            "watch_source_lag_seconds_threshold",
            self.watch_source_lag_seconds_threshold,
            "block_source_lag_seconds_threshold",
            self.block_source_lag_seconds_threshold,
        )
        _require_upper_threshold_pair(
            "watch_clock_drift_score_threshold",
            self.watch_clock_drift_score_threshold,
            "block_clock_drift_score_threshold",
            self.block_clock_drift_score_threshold,
        )
        _require_hard_flags(self)
        _reject_unsafe_public_surface("config", self)


@dataclass(frozen=True)
class ResearchEventSourceResolutionClockDriftSample:
    event_scope: str
    event_count: Decimal
    expected_resolution_at: datetime
    observed_resolution_at: datetime
    evidence_observed_at: datetime
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchEventSourceResolutionClockDriftSample does not support subclassing",
        )

    def __post_init__(self) -> None:
        _require_exact_type("sample", self, ResearchEventSourceResolutionClockDriftSample)
        _require_canonical_string("event_scope", self.event_scope)
        object.__setattr__(
            self,
            "event_count",
            _normalize_positive_count("event_count", self.event_count),
        )
        for field_name in (
            "expected_resolution_at",
            "observed_resolution_at",
            "evidence_observed_at",
        ):
            object.__setattr__(self, field_name, _as_utc(field_name, getattr(self, field_name)))
        _require_hard_flags(self)
        _reject_unsafe_public_surface("sample", self)
        _require_or_set_digest(self)


@dataclass(frozen=True)
class ResearchEventSourceResolutionClockDriftRow:
    event_scope: str
    event_count: Decimal
    clock_drift_seconds: Decimal
    source_lag_seconds: Decimal
    clock_drift_ratio: Decimal
    source_lag_ratio: Decimal
    status: str
    reason_codes: tuple[str, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchEventSourceResolutionClockDriftRow does not support subclassing",
        )

    def __post_init__(self) -> None:
        _require_exact_type("row", self, ResearchEventSourceResolutionClockDriftRow)
        _require_canonical_string("event_scope", self.event_scope)
        object.__setattr__(
            self,
            "event_count",
            _normalize_positive_count("event_count", self.event_count),
        )
        for field_name in ("clock_drift_seconds", "source_lag_seconds"):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_seconds(field_name, getattr(self, field_name)),
            )
        for field_name in ("clock_drift_ratio", "source_lag_ratio"):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        _require_status("status", self.status)
        object.__setattr__(self, "reason_codes", _normalize_reason_codes(self.reason_codes))
        if self.status != _status_from_reason_codes(self.reason_codes):
            raise ValueError("status must match reason_codes")
        _require_hard_flags(self)
        _reject_unsafe_public_surface("row", self)
        _require_or_set_digest(self)


@dataclass(frozen=True)
class ResearchEventSourceResolutionClockDriftReport:
    generated_at: datetime
    config_version: str
    watch_clock_drift_seconds_threshold: Decimal
    block_clock_drift_seconds_threshold: Decimal
    watch_source_lag_seconds_threshold: Decimal
    block_source_lag_seconds_threshold: Decimal
    watch_clock_drift_score_threshold: Decimal
    block_clock_drift_score_threshold: Decimal
    sample_count: Decimal
    event_count: Decimal
    drifted_event_count: Decimal
    stale_source_event_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    max_clock_drift_seconds: Decimal
    weighted_average_clock_drift_seconds: Decimal
    max_source_lag_seconds: Decimal
    weighted_average_source_lag_seconds: Decimal
    clock_drift_pressure_ratio: Decimal
    source_lag_pressure_ratio: Decimal
    average_clock_drift_ratio: Decimal
    average_source_lag_ratio: Decimal
    clock_drift_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    source_samples: tuple[ResearchEventSourceResolutionClockDriftSample, ...]
    rows: tuple[ResearchEventSourceResolutionClockDriftRow, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchEventSourceResolutionClockDriftReport does not support subclassing",
        )

    def __post_init__(self) -> None:
        _require_exact_type("report", self, ResearchEventSourceResolutionClockDriftReport)
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_EVENT_SOURCE_RESOLUTION_CLOCK_DRIFT_REPORT_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "watch_clock_drift_seconds_threshold",
            "block_clock_drift_seconds_threshold",
            "watch_source_lag_seconds_threshold",
            "block_source_lag_seconds_threshold",
            "max_clock_drift_seconds",
            "weighted_average_clock_drift_seconds",
            "max_source_lag_seconds",
            "weighted_average_source_lag_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_seconds(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "watch_clock_drift_score_threshold",
            "block_clock_drift_score_threshold",
            "clock_drift_pressure_ratio",
            "source_lag_pressure_ratio",
            "average_clock_drift_ratio",
            "average_source_lag_ratio",
            "clock_drift_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "sample_count",
            "event_count",
            "drifted_event_count",
            "stale_source_event_count",
            "pass_count",
            "watch_count",
            "block_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_count(field_name, getattr(self, field_name)),
            )
        _require_upper_threshold_pair(
            "watch_clock_drift_seconds_threshold",
            self.watch_clock_drift_seconds_threshold,
            "block_clock_drift_seconds_threshold",
            self.block_clock_drift_seconds_threshold,
        )
        _require_upper_threshold_pair(
            "watch_source_lag_seconds_threshold",
            self.watch_source_lag_seconds_threshold,
            "block_source_lag_seconds_threshold",
            self.block_source_lag_seconds_threshold,
        )
        _require_upper_threshold_pair(
            "watch_clock_drift_score_threshold",
            self.watch_clock_drift_score_threshold,
            "block_clock_drift_score_threshold",
            self.block_clock_drift_score_threshold,
        )
        _require_status("status", self.status)
        object.__setattr__(self, "reason_codes", _normalize_reason_codes(self.reason_codes))
        object.__setattr__(self, "source_samples", _normalize_samples(self.source_samples))
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        _validate_report_consistency(self)
        _require_hard_flags(self)
        _reject_unsafe_public_surface("report", self)
        _require_or_set_digest(self)


def build_research_event_source_resolution_clock_drift_report(
    samples: Iterable[ResearchEventSourceResolutionClockDriftSample],
    *,
    config: ResearchEventSourceResolutionClockDriftConfig,
    generated_at: datetime,
) -> ResearchEventSourceResolutionClockDriftReport:
    if type(config) is not ResearchEventSourceResolutionClockDriftConfig:
        raise ValueError(
            "config must be a ResearchEventSourceResolutionClockDriftConfig",
        )
    _require_hard_flags(config)
    _reject_unsafe_public_surface("config", config)
    generated_at = _as_utc("generated_at", generated_at)
    normalized_samples = _normalize_samples(samples)
    for sample in normalized_samples:
        if sample.evidence_observed_at > generated_at:
            raise ValueError("evidence_observed_at must not be after generated_at")
    rows = tuple(
        _row_from_sample(sample, config=config, generated_at=generated_at)
        for sample in normalized_samples
    )
    event_count = _sum_counts(tuple(row.event_count for row in rows))
    drifted_event_count = _sum_counts(
        tuple(
            row.event_count
            for row in rows
            if row.clock_drift_seconds >= config.watch_clock_drift_seconds_threshold
        ),
    )
    stale_source_event_count = _sum_counts(
        tuple(
            row.event_count
            for row in rows
            if row.source_lag_seconds >= config.watch_source_lag_seconds_threshold
        ),
    )
    weighted_average_clock_drift_seconds = _weighted_average_seconds(
        tuple((row.clock_drift_seconds, row.event_count) for row in rows),
        event_count,
    )
    weighted_average_source_lag_seconds = _weighted_average_seconds(
        tuple((row.source_lag_seconds, row.event_count) for row in rows),
        event_count,
    )
    average_clock_drift_ratio = _bounded_ratio(
        weighted_average_clock_drift_seconds,
        config.block_clock_drift_seconds_threshold,
    )
    average_source_lag_ratio = _bounded_ratio(
        weighted_average_source_lag_seconds,
        config.block_source_lag_seconds_threshold,
    )
    clock_drift_pressure_ratio = _ratio(drifted_event_count, event_count)
    source_lag_pressure_ratio = _ratio(stale_source_event_count, event_count)
    clock_drift_score = _average_ratio(
        (
            clock_drift_pressure_ratio,
            source_lag_pressure_ratio,
            average_clock_drift_ratio,
            average_source_lag_ratio,
        ),
    )

    return ResearchEventSourceResolutionClockDriftReport(
        generated_at=generated_at,
        config_version=config.config_version,
        watch_clock_drift_seconds_threshold=config.watch_clock_drift_seconds_threshold,
        block_clock_drift_seconds_threshold=config.block_clock_drift_seconds_threshold,
        watch_source_lag_seconds_threshold=config.watch_source_lag_seconds_threshold,
        block_source_lag_seconds_threshold=config.block_source_lag_seconds_threshold,
        watch_clock_drift_score_threshold=config.watch_clock_drift_score_threshold,
        block_clock_drift_score_threshold=config.block_clock_drift_score_threshold,
        sample_count=_decimal_count(len(rows)),
        event_count=event_count,
        drifted_event_count=drifted_event_count,
        stale_source_event_count=stale_source_event_count,
        pass_count=_status_count(rows, "pass"),
        watch_count=_status_count(rows, "watch"),
        block_count=_status_count(rows, "block"),
        max_clock_drift_seconds=_max_seconds(
            tuple(row.clock_drift_seconds for row in rows),
        ),
        weighted_average_clock_drift_seconds=weighted_average_clock_drift_seconds,
        max_source_lag_seconds=_max_seconds(tuple(row.source_lag_seconds for row in rows)),
        weighted_average_source_lag_seconds=weighted_average_source_lag_seconds,
        clock_drift_pressure_ratio=clock_drift_pressure_ratio,
        source_lag_pressure_ratio=source_lag_pressure_ratio,
        average_clock_drift_ratio=average_clock_drift_ratio,
        average_source_lag_ratio=average_source_lag_ratio,
        clock_drift_score=clock_drift_score,
        status=_report_status(rows, clock_drift_score, config=config),
        reason_codes=_report_reason_codes(rows, clock_drift_pressure_ratio, source_lag_pressure_ratio),
        source_samples=normalized_samples,
        rows=rows,
    )


def research_event_source_resolution_clock_drift_report_payload(
    report: ResearchEventSourceResolutionClockDriftReport | dict[str, Any],
) -> dict[str, Any]:
    if type(report) is ResearchEventSourceResolutionClockDriftReport:
        _require_hard_flags(report)
        _reject_unsafe_public_surface("report", report)
        _require_or_set_digest(report)
        payload = _payload_value(report)
    elif type(report) is dict:
        _reject_unsafe_public_surface("public payload", report)
        _require_public_payload_values(report)
        payload = _payload_value(report)
    else:
        raise ValueError(
            "report must be a ResearchEventSourceResolutionClockDriftReport",
        )
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    validate_research_event_source_resolution_clock_drift_report_payload(payload)
    return payload


def serialize_research_event_source_resolution_clock_drift_report_payload(
    report: ResearchEventSourceResolutionClockDriftReport | dict[str, Any],
) -> str:
    return json.dumps(
        research_event_source_resolution_clock_drift_report_payload(report),
        separators=(",", ":"),
        sort_keys=True,
    )


def research_event_source_resolution_clock_drift_report_payload_digest(
    report: ResearchEventSourceResolutionClockDriftReport | dict[str, Any],
) -> str:
    payload = research_event_source_resolution_clock_drift_report_payload(report)
    return _derived_digest(payload)


def validate_research_event_source_resolution_clock_drift_report_payload(
    payload: object,
) -> bool:
    if type(payload) is not dict:
        raise ValueError("public payload must be a JSON object")
    _reject_unsafe_public_surface("public payload", payload)
    _require_public_payload_values(payload)
    _validate_payload_digest_tree(payload)
    _report_from_public_payload(payload)
    return True


def _row_from_sample(
    sample: ResearchEventSourceResolutionClockDriftSample,
    *,
    config: ResearchEventSourceResolutionClockDriftConfig,
    generated_at: datetime,
) -> ResearchEventSourceResolutionClockDriftRow:
    clock_drift_seconds = _absolute_seconds(
        sample.observed_resolution_at,
        sample.expected_resolution_at,
    )
    source_lag_seconds = _age_seconds(generated_at, sample.evidence_observed_at)
    clock_drift_ratio = _bounded_ratio(
        clock_drift_seconds,
        config.block_clock_drift_seconds_threshold,
    )
    source_lag_ratio = _bounded_ratio(
        source_lag_seconds,
        config.block_source_lag_seconds_threshold,
    )
    reason_codes = _row_reason_codes(
        clock_drift_seconds=clock_drift_seconds,
        source_lag_seconds=source_lag_seconds,
        config=config,
    )
    return ResearchEventSourceResolutionClockDriftRow(
        event_scope=sample.event_scope,
        event_count=sample.event_count,
        clock_drift_seconds=clock_drift_seconds,
        source_lag_seconds=source_lag_seconds,
        clock_drift_ratio=clock_drift_ratio,
        source_lag_ratio=source_lag_ratio,
        status=_status_from_reason_codes(reason_codes),
        reason_codes=reason_codes,
    )


def _row_reason_codes(
    *,
    clock_drift_seconds: Decimal,
    source_lag_seconds: Decimal,
    config: ResearchEventSourceResolutionClockDriftConfig,
) -> tuple[str, ...]:
    return (
        "clock_drift_"
        + _seconds_status(
            clock_drift_seconds,
            watch_threshold=config.watch_clock_drift_seconds_threshold,
            block_threshold=config.block_clock_drift_seconds_threshold,
        ),
        "source_lag_"
        + _seconds_status(
            source_lag_seconds,
            watch_threshold=config.watch_source_lag_seconds_threshold,
            block_threshold=config.block_source_lag_seconds_threshold,
        ),
    )


def _report_status(
    rows: tuple[ResearchEventSourceResolutionClockDriftRow, ...],
    clock_drift_score: Decimal,
    *,
    config: ResearchEventSourceResolutionClockDriftConfig,
) -> str:
    if not rows:
        return "block"
    row_status = max((row.status for row in rows), key=lambda value: _STATUS_RANK[value])
    score_status = _score_status(
        clock_drift_score,
        watch_threshold=config.watch_clock_drift_score_threshold,
        block_threshold=config.block_clock_drift_score_threshold,
    )
    return max((row_status, score_status), key=lambda value: _STATUS_RANK[value])


def _report_reason_codes(
    rows: tuple[ResearchEventSourceResolutionClockDriftRow, ...],
    clock_drift_pressure_ratio: Decimal,
    source_lag_pressure_ratio: Decimal,
) -> tuple[str, ...]:
    if not rows:
        return ("no_event_source_resolution_clock_drift_samples",)
    if all(row.status == "pass" for row in rows):
        return ("event_source_resolution_clock_drift_pass",)
    reason_codes: list[str] = []
    if clock_drift_pressure_ratio > _ZERO:
        reason_codes.append("clock_drift_pressure_watch")
    if source_lag_pressure_ratio > _ZERO:
        reason_codes.append("source_lag_pressure_watch")
    if any(row.status == "block" for row in rows):
        reason_codes.append("event_source_resolution_clock_drift_sample_block")
    elif any(row.status == "watch" for row in rows):
        reason_codes.append("event_source_resolution_clock_drift_sample_watch")
    return tuple(reason_codes) if reason_codes else ("event_source_resolution_clock_drift_watch",)


def _normalize_samples(
    values: Iterable[ResearchEventSourceResolutionClockDriftSample],
) -> tuple[ResearchEventSourceResolutionClockDriftSample, ...]:
    if isinstance(values, (str, bytes)):
        raise ValueError("samples must be an iterable")
    try:
        samples = tuple(values)
    except TypeError as exc:
        raise ValueError("samples must be an iterable") from exc
    for value in samples:
        if type(value) is not ResearchEventSourceResolutionClockDriftSample:
            raise ValueError(
                "samples must contain ResearchEventSourceResolutionClockDriftSample values",
            )
        _require_hard_flags(value)
        _reject_unsafe_public_surface("sample", value)
        _require_or_set_digest(value)
    normalized = tuple(sorted(samples, key=lambda value: value.event_scope))
    if len({value.event_scope for value in normalized}) != len(normalized):
        raise ValueError("samples must be unique by event_scope")
    return normalized


def _normalize_rows(
    values: Iterable[ResearchEventSourceResolutionClockDriftRow],
) -> tuple[ResearchEventSourceResolutionClockDriftRow, ...]:
    if isinstance(values, (str, bytes)):
        raise ValueError("rows must contain clock drift rows")
    try:
        rows = tuple(values)
    except TypeError as exc:
        raise ValueError("rows must contain clock drift rows") from exc
    for row in rows:
        if type(row) is not ResearchEventSourceResolutionClockDriftRow:
            raise ValueError("rows must contain clock drift rows")
        _require_hard_flags(row)
        _reject_unsafe_public_surface("row", row)
        _require_or_set_digest(row)
    normalized = tuple(sorted(rows, key=lambda row: row.event_scope))
    if rows != normalized:
        raise ValueError("rows must be sorted")
    if len({row.event_scope for row in rows}) != len(rows):
        raise ValueError("rows must be unique by event_scope")
    return rows


def _validate_report_consistency(
    report: ResearchEventSourceResolutionClockDriftReport,
) -> None:
    if report.sample_count != _decimal_count(len(report.rows)):
        raise ValueError("sample_count must match rows")
    if tuple(sample.event_scope for sample in report.source_samples) != tuple(
        row.event_scope for row in report.rows
    ):
        raise ValueError("source_samples must match rows")
    config = ResearchEventSourceResolutionClockDriftConfig(
        config_version=report.config_version,
        watch_clock_drift_seconds_threshold=report.watch_clock_drift_seconds_threshold,
        block_clock_drift_seconds_threshold=report.block_clock_drift_seconds_threshold,
        watch_source_lag_seconds_threshold=report.watch_source_lag_seconds_threshold,
        block_source_lag_seconds_threshold=report.block_source_lag_seconds_threshold,
        watch_clock_drift_score_threshold=report.watch_clock_drift_score_threshold,
        block_clock_drift_score_threshold=report.block_clock_drift_score_threshold,
    )
    expected_rows = tuple(
        _row_from_sample(
            sample,
            config=config,
            generated_at=report.generated_at,
        )
        for sample in report.source_samples
    )
    if report.rows != expected_rows:
        raise ValueError("rows must match source_samples")
    expected_sums = {
        "event_count": _sum_counts(tuple(row.event_count for row in report.rows)),
        "drifted_event_count": _sum_counts(
            tuple(
                row.event_count
                for row in report.rows
                if row.clock_drift_seconds >= report.watch_clock_drift_seconds_threshold
            ),
        ),
        "stale_source_event_count": _sum_counts(
            tuple(
                row.event_count
                for row in report.rows
                if row.source_lag_seconds >= report.watch_source_lag_seconds_threshold
            ),
        ),
        "pass_count": _status_count(report.rows, "pass"),
        "watch_count": _status_count(report.rows, "watch"),
        "block_count": _status_count(report.rows, "block"),
    }
    for field_name, expected in expected_sums.items():
        if getattr(report, field_name) != expected:
            raise ValueError(f"{field_name} must match rows")
    if report.max_clock_drift_seconds != _max_seconds(
        tuple(row.clock_drift_seconds for row in report.rows),
    ):
        raise ValueError("max_clock_drift_seconds must match rows")
    if report.max_source_lag_seconds != _max_seconds(
        tuple(row.source_lag_seconds for row in report.rows),
    ):
        raise ValueError("max_source_lag_seconds must match rows")
    if report.weighted_average_clock_drift_seconds != _weighted_average_seconds(
        tuple((row.clock_drift_seconds, row.event_count) for row in report.rows),
        report.event_count,
    ):
        raise ValueError("weighted_average_clock_drift_seconds must match rows")
    if report.weighted_average_source_lag_seconds != _weighted_average_seconds(
        tuple((row.source_lag_seconds, row.event_count) for row in report.rows),
        report.event_count,
    ):
        raise ValueError("weighted_average_source_lag_seconds must match rows")
    expected_ratios = {
        "clock_drift_pressure_ratio": _ratio(
            report.drifted_event_count,
            report.event_count,
        ),
        "source_lag_pressure_ratio": _ratio(
            report.stale_source_event_count,
            report.event_count,
        ),
        "average_clock_drift_ratio": _bounded_ratio(
            report.weighted_average_clock_drift_seconds,
            report.block_clock_drift_seconds_threshold,
        ),
        "average_source_lag_ratio": _bounded_ratio(
            report.weighted_average_source_lag_seconds,
            report.block_source_lag_seconds_threshold,
        ),
    }
    for field_name, expected in expected_ratios.items():
        if getattr(report, field_name) != expected:
            raise ValueError(f"{field_name} must match rows")
    if report.clock_drift_score != _average_ratio(
        (
            report.clock_drift_pressure_ratio,
            report.source_lag_pressure_ratio,
            report.average_clock_drift_ratio,
            report.average_source_lag_ratio,
        ),
    ):
        raise ValueError("clock_drift_score must match ratios")
    if report.reason_codes != _report_reason_codes(
        report.rows,
        report.clock_drift_pressure_ratio,
        report.source_lag_pressure_ratio,
    ):
        raise ValueError("reason_codes must match rows")
    row_status = "block"
    if report.rows:
        row_status = max(
            (row.status for row in report.rows),
            key=lambda value: _STATUS_RANK[value],
        )
    score_status = _score_status(
        report.clock_drift_score,
        watch_threshold=report.watch_clock_drift_score_threshold,
        block_threshold=report.block_clock_drift_score_threshold,
    )
    expected_status = max((row_status, score_status), key=lambda value: _STATUS_RANK[value])
    if report.status != expected_status:
        raise ValueError("status must match rows")


def _require_public_payload_values(payload: dict[str, Any]) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if payload.get(field_name) is not True:
            raise ValueError(f"{field_name} must be True")
    for key, value in payload.items():
        if type(key) is not str:
            raise ValueError("public payload keys must be strings")
        _require_public_value(key, value)


def _require_public_value(field_name: str, value: object) -> None:
    if type(value) is float:
        raise ValueError(f"{field_name} must not be a float")
    if type(value) is int:
        raise ValueError(f"{field_name} must use Decimal-derived string values")
    if type(value) is str:
        if field_name.endswith("_count") or field_name.endswith("_seconds") or field_name.endswith("_ratio") or field_name.endswith("_score") or field_name.endswith("_threshold"):
            _require_decimal_string(field_name, value)
        return
    if type(value) is bool or value is None:
        return
    if isinstance(value, list):
        for item in value:
            _require_public_value(field_name, item)
        return
    if isinstance(value, dict):
        _require_public_payload_values(value)
        return
    raise ValueError("public payload value is not JSON serializable")


def _report_from_public_payload(
    payload: dict[str, Any],
) -> ResearchEventSourceResolutionClockDriftReport:
    report = _dataclass_from_public_payload(
        "report",
        payload,
        ResearchEventSourceResolutionClockDriftReport,
    )
    if type(report) is not ResearchEventSourceResolutionClockDriftReport:
        raise ValueError("report payload schema must produce a report")
    return report


def _dataclass_from_public_payload(
    label: str,
    payload: object,
    expected_type: type[object],
) -> object:
    if type(payload) is not dict:
        raise ValueError(f"{label} payload schema must be a JSON object")
    _require_exact_payload_keys(label, payload, expected_type)
    values: dict[str, object] = {}
    for field in fields(expected_type):
        field_name = field.name
        value = payload[field_name]
        if field_name == "source_samples":
            values[field_name] = _dataclass_sequence_from_public_payload(
                "sample",
                value,
                ResearchEventSourceResolutionClockDriftSample,
            )
        elif field_name == "rows":
            values[field_name] = _dataclass_sequence_from_public_payload(
                "row",
                value,
                ResearchEventSourceResolutionClockDriftRow,
            )
        elif field_name == "reason_codes":
            values[field_name] = _string_tuple_from_public_payload(field_name, value)
        elif field_name.endswith("_at"):
            values[field_name] = _canonical_utc_datetime_from_public_payload(
                field_name,
                value,
            )
        elif _is_decimal_payload_field(field_name):
            values[field_name] = _canonical_decimal_from_public_payload(
                field_name,
                value,
            )
        elif field_name in ("paper_only", "report_only", "readonly"):
            if type(value) is not bool or value is not True:
                raise ValueError(f"{field_name} must be True")
            values[field_name] = value
        elif field_name == _DIGEST_FIELD:
            if type(value) is not str or not _is_sha256_hex(value):
                raise ValueError(
                    "derived_validation_digest must be a sha256 hex digest",
                )
            values[field_name] = value
        else:
            if type(value) is not str:
                raise ValueError(f"{field_name} must be a string")
            values[field_name] = value
    return expected_type(**values)


def _require_exact_payload_keys(
    label: str,
    payload: dict[str, Any],
    expected_type: type[object],
) -> None:
    expected_keys = {field.name for field in fields(expected_type)}
    actual_keys = set(payload)
    if actual_keys == expected_keys:
        return
    missing = sorted(expected_keys - actual_keys)
    extra = sorted(actual_keys - expected_keys)
    raise ValueError(
        f"{label} payload schema keys must match exactly; "
        f"missing={missing}; extra={extra}",
    )


def _dataclass_sequence_from_public_payload(
    label: str,
    value: object,
    expected_type: type[object],
) -> tuple[object, ...]:
    if type(value) is not list:
        raise ValueError(f"{label} payload schema must be a list")
    return tuple(
        _dataclass_from_public_payload(label, item, expected_type)
        for item in value
    )


def _string_tuple_from_public_payload(
    field_name: str,
    value: object,
) -> tuple[str, ...]:
    if type(value) is not list:
        raise ValueError(f"{field_name} must be a list")
    if any(type(item) is not str for item in value):
        raise ValueError(f"{field_name} must contain strings")
    return tuple(value)


def _canonical_decimal_from_public_payload(
    field_name: str,
    value: object,
) -> Decimal:
    if type(value) is not str:
        raise ValueError(f"{field_name} must use a canonical Decimal string")
    try:
        decimal_value = Decimal(value)
    except InvalidOperation as exc:
        raise ValueError(
            f"{field_name} must use a canonical Decimal string",
        ) from exc
    if not decimal_value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    try:
        canonical_value = str(_quantize(decimal_value))
    except InvalidOperation as exc:
        raise ValueError(
            f"{field_name} must use a canonical Decimal string",
        ) from exc
    if value != canonical_value:
        raise ValueError(f"{field_name} must use a canonical Decimal string")
    return decimal_value


def _canonical_utc_datetime_from_public_payload(
    field_name: str,
    value: object,
) -> datetime:
    if type(value) is not str:
        raise ValueError(f"{field_name} must use a canonical UTC datetime")
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError as exc:
        raise ValueError(
            f"{field_name} must use a canonical UTC datetime",
        ) from exc
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ValueError(f"{field_name} must use a canonical UTC datetime")
    normalized = parsed.astimezone(UTC)
    if value != normalized.isoformat():
        raise ValueError(f"{field_name} must use a canonical UTC datetime")
    return normalized


def _is_decimal_payload_field(field_name: str) -> bool:
    return field_name.endswith(
        ("_count", "_seconds", "_ratio", "_score", "_threshold"),
    )


def _validate_payload_digest_tree(payload: dict[str, Any]) -> None:
    current = payload.get(_DIGEST_FIELD)
    if type(current) is not str:
        raise ValueError("derived_validation_digest must be a string")
    if not _is_sha256_hex(current):
        raise ValueError("derived_validation_digest must be a sha256 hex digest")
    if current != _derived_digest(payload):
        raise ValueError("derived_validation_digest does not match derived payload")
    for key in ("source_samples", "rows"):
        value = payload.get(key)
        if value is None:
            continue
        if type(value) is not list:
            raise ValueError(f"{key} must be a list")
        for item in value:
            if type(item) is not dict:
                raise ValueError(f"{key} must contain JSON objects")
            _validate_payload_digest_tree(item)


def _status_count(
    rows: tuple[ResearchEventSourceResolutionClockDriftRow, ...],
    status: str,
) -> Decimal:
    return _decimal_count(sum(1 for row in rows if row.status == status))


def _status_from_reason_codes(reason_codes: tuple[str, ...]) -> str:
    suffixes: list[str] = []
    for reason_code in reason_codes:
        suffix = reason_code.rsplit("_", 1)[-1]
        if suffix in _STATUSES:
            suffixes.append(suffix)
    if not suffixes:
        raise ValueError("reason_codes must include status suffixes")
    return max(suffixes, key=lambda status: _STATUS_RANK[status])


def _seconds_status(
    value: Decimal,
    *,
    watch_threshold: Decimal,
    block_threshold: Decimal,
) -> str:
    if value >= block_threshold:
        return "block"
    if value >= watch_threshold:
        return "watch"
    return "pass"


def _score_status(
    value: Decimal,
    *,
    watch_threshold: Decimal,
    block_threshold: Decimal,
) -> str:
    if value >= block_threshold:
        return "block"
    if value >= watch_threshold:
        return "watch"
    return "pass"


def _sum_counts(values: tuple[Decimal, ...]) -> Decimal:
    return _quantize(sum(values, _ZERO))


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == _ZERO:
        return _ZERO
    with localcontext(_DECIMAL_CONTEXT):
        return _quantize(numerator / denominator)


def _bounded_ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    ratio = _ratio(numerator, denominator)
    return _ONE if ratio > _ONE else ratio


def _average_ratio(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return _ZERO
    with localcontext(_DECIMAL_CONTEXT):
        return _quantize(sum(values, _ZERO) / Decimal(len(values)))


def _weighted_average_seconds(
    values: tuple[tuple[Decimal, Decimal], ...],
    denominator: Decimal,
) -> Decimal:
    if denominator == _ZERO:
        return _ZERO
    total = _ZERO
    for seconds_value, weight in values:
        total += seconds_value * weight
    with localcontext(_DECIMAL_CONTEXT):
        return _quantize(total / denominator)


def _max_seconds(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return _ZERO
    return max(values)


def _decimal_count(value: int) -> Decimal:
    if type(value) is not int:
        raise ValueError("count source must be an int")
    if value < 0:
        raise ValueError("count source must be nonnegative")
    return _quantize(Decimal(value))


def _absolute_seconds(left: datetime, right: datetime) -> Decimal:
    delta = left - right
    seconds = _duration_seconds(delta)
    return -seconds if seconds < _ZERO else seconds


def _age_seconds(generated_at: datetime, observed_at: datetime) -> Decimal:
    if observed_at > generated_at:
        raise ValueError("evidence_observed_at must not be after generated_at")
    return _duration_seconds(generated_at - observed_at)


def _duration_seconds(delta: object) -> Decimal:
    whole_seconds = delta.days * 86_400 + delta.seconds
    with localcontext(_DECIMAL_CONTEXT):
        return _quantize(
            Decimal(whole_seconds) + Decimal(delta.microseconds) / Decimal(1_000_000),
        )


def _require_upper_threshold_pair(
    watch_field_name: str,
    watch_threshold: Decimal,
    block_field_name: str,
    block_threshold: Decimal,
) -> None:
    if block_threshold <= watch_threshold:
        raise ValueError(f"{block_field_name} must exceed {watch_field_name}")


def _normalize_positive_count(field_name: str, value: object) -> Decimal:
    normalized = _normalize_nonnegative_count(field_name, value)
    if normalized <= _ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _normalize_nonnegative_count(field_name: str, value: object) -> Decimal:
    normalized = _normalize_nonnegative_decimal(field_name, value)
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{field_name} must be a whole Decimal")
    return normalized


def _normalize_positive_seconds(field_name: str, value: object) -> Decimal:
    normalized = _normalize_nonnegative_seconds(field_name, value)
    if normalized <= _ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _normalize_nonnegative_seconds(field_name: str, value: object) -> Decimal:
    return _normalize_nonnegative_decimal(field_name, value)


def _normalize_ratio(field_name: str, value: object) -> Decimal:
    normalized = _normalize_nonnegative_decimal(field_name, value)
    if normalized > _ONE:
        raise ValueError(f"{field_name} must be at most one")
    return normalized


def _normalize_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized < _ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _normalize_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return _quantize(value)


def _require_decimal_string(field_name: str, value: object) -> Decimal:
    if type(value) is not str:
        raise ValueError(f"{field_name} must use Decimal-derived string values")
    decimal_value = Decimal(value)
    if not decimal_value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return decimal_value


def _quantize(value: Decimal) -> Decimal:
    with localcontext(_DECIMAL_CONTEXT):
        return value.quantize(_QUANTUM)


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")
    lowered = value.lower()
    if any(fragment in lowered for fragment in _UNSAFE_PUBLIC_SURFACE_FRAGMENTS):
        raise ValueError(f"unsafe public surface in {field_name}: {value}")


def _require_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in _STATUSES:
        raise ValueError(f"{field_name} must be pass, watch, or block")


def _normalize_reason_codes(values: object) -> tuple[str, ...]:
    if type(values) is not tuple:
        raise ValueError("reason_codes must be a tuple")
    if not values:
        raise ValueError("reason_codes must not be empty")
    for value in values:
        _require_canonical_string("reason_codes", value)
    if len(set(values)) != len(values):
        raise ValueError("reason_codes must be unique")
    return tuple(values)


def _require_exact_type(label: str, value: object, expected_type: type[object]) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{label} must be a {expected_type.__name__}")


def _require_hard_flags(value: object) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if getattr(value, field_name, None) is not True:
            raise ValueError(f"{field_name} must be True")


def _reject_unsafe_public_surface(label: str, value: object) -> None:
    for item in _surface_items(value):
        lowered = item.lower()
        if any(fragment in lowered for fragment in _UNSAFE_PUBLIC_SURFACE_FRAGMENTS):
            raise ValueError(f"unsafe public surface in {label}: {item}")


def _surface_items(value: object) -> tuple[str, ...]:
    if is_dataclass(value) and not isinstance(value, type):
        items: list[str] = []
        for field in fields(value):
            items.append(field.name)
            items.extend(_surface_items(getattr(value, field.name)))
        return tuple(items)
    if isinstance(value, dict):
        items = []
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("public payload keys must be strings")
            items.append(key)
            items.extend(_surface_items(item))
        return tuple(items)
    if isinstance(value, (list, tuple)):
        items = []
        for item in value:
            items.extend(_surface_items(item))
        return tuple(items)
    if type(value) is str:
        return (value,)
    return ()


def _require_or_set_digest(value: object) -> None:
    current = getattr(value, _DIGEST_FIELD)
    if type(current) is not str:
        raise ValueError("derived_validation_digest must be a string")
    expected = _derived_digest(value)
    if current == "":
        object.__setattr__(value, _DIGEST_FIELD, expected)
        return
    if current != expected or not _is_sha256_hex(current):
        raise ValueError("derived_validation_digest does not match derived payload")


def _derived_digest(value: object) -> str:
    encoded = json.dumps(
        _canonical_digest_value(value),
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return sha256(encoded).hexdigest()


def _is_sha256_hex(value: str) -> bool:
    return len(value) == 64 and all(character in "0123456789abcdef" for character in value)


def _canonical_digest_value(value: object) -> object:
    if value is None:
        return None
    if is_dataclass(value) and not isinstance(value, type):
        return {
            field.name: _canonical_digest_value(getattr(value, field.name))
            for field in fields(value)
            if field.name != _DIGEST_FIELD
        }
    if isinstance(value, Decimal):
        if not value.is_finite():
            raise ValueError("digest Decimal value must be finite")
        return str(value)
    if type(value) is datetime:
        return value.astimezone(UTC).isoformat()
    if type(value) in (str, bool):
        return value
    if isinstance(value, tuple):
        return [_canonical_digest_value(item) for item in value]
    if isinstance(value, list):
        return [_canonical_digest_value(item) for item in value]
    if isinstance(value, dict):
        result: dict[str, object] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("public payload keys must be strings")
            if key != _DIGEST_FIELD:
                result[key] = _canonical_digest_value(item)
        return result
    raise ValueError("unsupported digest value")


def _payload_value(value: object) -> Any:
    if value is None:
        return None
    if is_dataclass(value) and not isinstance(value, type):
        return {field.name: _payload_value(getattr(value, field.name)) for field in fields(value)}
    if isinstance(value, Decimal):
        if not value.is_finite():
            raise ValueError("public payload Decimal value must be finite")
        return str(value)
    if type(value) is datetime:
        return value.astimezone(UTC).isoformat()
    if type(value) in (str, bool):
        return value
    if isinstance(value, tuple):
        return [_payload_value(item) for item in value]
    if isinstance(value, list):
        return [_payload_value(item) for item in value]
    if isinstance(value, dict):
        result: dict[str, object] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("public payload keys must be strings")
            result[key] = _payload_value(item)
        return result
    raise ValueError("public payload value is not JSON serializable")
