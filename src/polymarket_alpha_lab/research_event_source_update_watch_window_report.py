"""Pure report for event source update watch windows."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, DecimalException, localcontext
from hashlib import sha256
import json
from typing import Any


DEFAULT_RESEARCH_EVENT_SOURCE_UPDATE_WATCH_WINDOW_REPORT_CONFIG_VERSION = (
    "research-event-source-update-watch-window-report-v0"
)

_DECIMAL_CONTEXT = Context(prec=64)
_QUANTUM = Decimal("0.000001")
_ZERO = Decimal("0.000000")
_ONE = Decimal("1.000000")
_DIGEST_FIELD = "derived_validation_digest"
_STATUSES = ("pass", "watch", "block")
_STATUS_RANK = {"pass": 0, "watch": 1, "block": 2}
_AUTHORITY_TIERS = ("official", "primary", "secondary", "low")
_AUTHORITY_PENALTY = {
    "official": Decimal("0.000000"),
    "primary": Decimal("0.100000"),
    "secondary": Decimal("0.250000"),
    "low": Decimal("0.500000"),
}
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
    "".join(("ques", "tion")),
    "".join(("d", "sn")),
    "".join(("table", "_", "name")),
    "".join(("private", "_", "tok", "en")),
    "".join(("tok", "en")),
    "".join(("data", "base")),
    "".join(("fi", "le")),
    "".join(("fi", "le", "_", "path")),
    "".join(("fi", "le", "-", "path")),
    "".join(("fi", "le", "system")),
    "".join(("secret")),
    "".join(("password")),
    "".join(("private", "_", "key")),
    "".join(("api", "_", "key")),
    "".join(("auth", "entication")),
    "".join(("auth", "orization")),
    "".join(("auth", "_", "tok", "en")),
    "".join(("bearer")),
    "".join(("credential")),
    "".join(("net", "work")),
    "".join(("per", "sist")),
    "".join(("per", "sistence")),
    "".join(("wall", "et")),
    "".join(("or", "der")),
    "".join(("li", "ve")),
    "".join(("recomm", "endation")),
    "".join(("exec", "ution")),
    "".join(("tra", "de")),
)

__all__ = (
    "DEFAULT_RESEARCH_EVENT_SOURCE_UPDATE_WATCH_WINDOW_REPORT_CONFIG_VERSION",
    "ResearchEventSourceUpdateWatchWindowConfig",
    "ResearchEventSourceUpdateWatchWindowInput",
    "ResearchEventSourceUpdateWatchWindowReport",
    "ResearchEventSourceUpdateWatchWindowRow",
    "build_research_event_source_update_watch_window_report",
    "research_event_source_update_watch_window_report_payload",
    "validate_research_event_source_update_watch_window_report_payload",
)


@dataclass(frozen=True)
class ResearchEventSourceUpdateWatchWindowConfig:
    config_version: str = (
        DEFAULT_RESEARCH_EVENT_SOURCE_UPDATE_WATCH_WINDOW_REPORT_CONFIG_VERSION
    )
    cadence_watch_overrun_ratio: Decimal = Decimal("1.000000")
    cadence_block_overrun_ratio: Decimal = Decimal("2.000000")
    stale_evidence_watch_age_seconds: Decimal = Decimal("3600.000000")
    stale_evidence_block_age_seconds: Decimal = Decimal("7200.000000")
    contradiction_watch_pressure: Decimal = Decimal("0.400000")
    contradiction_block_pressure: Decimal = Decimal("0.700000")
    resolution_deadline_watch_window_seconds: Decimal = Decimal("1800.000000")
    resolution_deadline_block_window_seconds: Decimal = Decimal("300.000000")
    watch_score_threshold: Decimal = Decimal("0.400000")
    block_score_threshold: Decimal = Decimal("0.700000")
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchEventSourceUpdateWatchWindowConfig does not support subclassing",
        )

    def __post_init__(self) -> None:
        _require_exact_type("config", self, ResearchEventSourceUpdateWatchWindowConfig)
        _require_canonical_string("config_version", self.config_version)
        for field_name in (
            "cadence_watch_overrun_ratio",
            "cadence_block_overrun_ratio",
            "stale_evidence_watch_age_seconds",
            "stale_evidence_block_age_seconds",
            "resolution_deadline_watch_window_seconds",
            "resolution_deadline_block_window_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "contradiction_watch_pressure",
            "contradiction_block_pressure",
            "watch_score_threshold",
            "block_score_threshold",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        _require_positive_decimal(
            "cadence_watch_overrun_ratio",
            self.cadence_watch_overrun_ratio,
        )
        _require_positive_decimal(
            "cadence_block_overrun_ratio",
            self.cadence_block_overrun_ratio,
        )
        _require_upper_threshold_pair(
            "cadence_watch_overrun_ratio",
            self.cadence_watch_overrun_ratio,
            "cadence_block_overrun_ratio",
            self.cadence_block_overrun_ratio,
        )
        _require_upper_threshold_pair(
            "stale_evidence_watch_age_seconds",
            self.stale_evidence_watch_age_seconds,
            "stale_evidence_block_age_seconds",
            self.stale_evidence_block_age_seconds,
        )
        _require_upper_threshold_pair(
            "contradiction_watch_pressure",
            self.contradiction_watch_pressure,
            "contradiction_block_pressure",
            self.contradiction_block_pressure,
        )
        _require_lower_seconds_pair(
            "resolution_deadline_watch_window_seconds",
            self.resolution_deadline_watch_window_seconds,
            "resolution_deadline_block_window_seconds",
            self.resolution_deadline_block_window_seconds,
        )
        _require_upper_threshold_pair(
            "watch_score_threshold",
            self.watch_score_threshold,
            "block_score_threshold",
            self.block_score_threshold,
        )
        _require_hard_flags(self)
        _reject_unsafe_public_surface("config", self)
        _require_or_set_digest(self)


@dataclass(frozen=True)
class ResearchEventSourceUpdateWatchWindowInput:
    event_scope: str
    authority_tier: str
    expected_update_cadence_seconds: Decimal
    stale_evidence_age_seconds: Decimal
    resolution_deadline_seconds: Decimal
    contradiction_pressure: Decimal
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchEventSourceUpdateWatchWindowInput does not support subclassing",
        )

    def __post_init__(self) -> None:
        _require_exact_type("input", self, ResearchEventSourceUpdateWatchWindowInput)
        _require_canonical_string("event_scope", self.event_scope)
        _require_member("authority_tier", self.authority_tier, _AUTHORITY_TIERS)
        object.__setattr__(
            self,
            "expected_update_cadence_seconds",
            _normalize_positive_decimal(
                "expected_update_cadence_seconds",
                self.expected_update_cadence_seconds,
            ),
        )
        for field_name in (
            "stale_evidence_age_seconds",
            "resolution_deadline_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "contradiction_pressure",
            _normalize_ratio("contradiction_pressure", self.contradiction_pressure),
        )
        _require_hard_flags(self)
        _reject_unsafe_public_surface("input", self)
        _require_or_set_digest(self)


@dataclass(frozen=True)
class ResearchEventSourceUpdateWatchWindowRow:
    event_scope: str
    authority_tier: str
    expected_update_cadence_seconds: Decimal
    stale_evidence_age_seconds: Decimal
    resolution_deadline_seconds: Decimal
    contradiction_pressure: Decimal
    cadence_overrun_ratio: Decimal
    stale_evidence_pressure: Decimal
    authority_pressure: Decimal
    deadline_proximity_pressure: Decimal
    next_update_watch_window_seconds: Decimal
    watch_window_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchEventSourceUpdateWatchWindowRow does not support subclassing",
        )

    def __post_init__(self) -> None:
        _require_exact_type("row", self, ResearchEventSourceUpdateWatchWindowRow)
        _require_canonical_string("event_scope", self.event_scope)
        _require_member("authority_tier", self.authority_tier, _AUTHORITY_TIERS)
        object.__setattr__(
            self,
            "expected_update_cadence_seconds",
            _normalize_positive_decimal(
                "expected_update_cadence_seconds",
                self.expected_update_cadence_seconds,
            ),
        )
        for field_name in (
            "stale_evidence_age_seconds",
            "resolution_deadline_seconds",
            "next_update_watch_window_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "contradiction_pressure",
            "stale_evidence_pressure",
            "authority_pressure",
            "deadline_proximity_pressure",
            "watch_window_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "cadence_overrun_ratio",
            _normalize_nonnegative_decimal(
                "cadence_overrun_ratio",
                self.cadence_overrun_ratio,
            ),
        )
        _require_status("status", self.status)
        object.__setattr__(self, "reason_codes", _normalize_reason_codes(self.reason_codes))
        _validate_row_consistency(self)
        _require_hard_flags(self)
        _reject_unsafe_public_surface("row", self)
        _require_or_set_digest(self)


@dataclass(frozen=True)
class ResearchEventSourceUpdateWatchWindowReport:
    generated_at: datetime
    config_version: str
    input_count: Decimal
    row_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    average_watch_window_score: Decimal
    max_watch_window_score: Decimal
    min_next_update_watch_window_seconds: Decimal
    max_stale_evidence_age_seconds: Decimal
    max_contradiction_pressure: Decimal
    status: str
    reason_codes: tuple[str, ...]
    rows: tuple[ResearchEventSourceUpdateWatchWindowRow, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchEventSourceUpdateWatchWindowReport does not support subclassing",
        )

    def __post_init__(self) -> None:
        _require_exact_type("report", self, ResearchEventSourceUpdateWatchWindowReport)
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        for field_name in (
            "input_count",
            "row_count",
            "pass_count",
            "watch_count",
            "block_count",
            "min_next_update_watch_window_seconds",
            "max_stale_evidence_age_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "average_watch_window_score",
            "max_watch_window_score",
            "max_contradiction_pressure",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        _require_status("status", self.status)
        object.__setattr__(self, "reason_codes", _normalize_reason_codes(self.reason_codes))
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        _validate_report_consistency(self)
        _require_hard_flags(self)
        _reject_unsafe_public_surface("report", self)
        _require_or_set_digest(self)


def build_research_event_source_update_watch_window_report(
    updates: Iterable[ResearchEventSourceUpdateWatchWindowInput],
    *,
    config: ResearchEventSourceUpdateWatchWindowConfig,
    generated_at: datetime,
) -> ResearchEventSourceUpdateWatchWindowReport:
    if type(config) is not ResearchEventSourceUpdateWatchWindowConfig:
        raise ValueError("config must be a ResearchEventSourceUpdateWatchWindowConfig")
    _require_hard_flags(config)
    _reject_unsafe_public_surface("config", config)
    _require_or_set_digest(config)
    generated_at = _as_utc("generated_at", generated_at)
    normalized = _normalize_inputs(updates)
    rows = tuple(
        sorted(
            (_row_from_input(value, config=config) for value in normalized),
            key=_row_sort_key,
        ),
    )

    return ResearchEventSourceUpdateWatchWindowReport(
        generated_at=generated_at,
        config_version=config.config_version,
        input_count=_decimal_count(len(normalized)),
        row_count=_decimal_count(len(rows)),
        pass_count=_status_count(rows, "pass"),
        watch_count=_status_count(rows, "watch"),
        block_count=_status_count(rows, "block"),
        average_watch_window_score=_average_decimal(
            tuple(row.watch_window_score for row in rows),
        ),
        max_watch_window_score=_max_decimal(
            tuple(row.watch_window_score for row in rows),
        ),
        min_next_update_watch_window_seconds=_min_decimal(
            tuple(row.next_update_watch_window_seconds for row in rows),
        ),
        max_stale_evidence_age_seconds=_max_decimal(
            tuple(row.stale_evidence_age_seconds for row in rows),
        ),
        max_contradiction_pressure=_max_decimal(
            tuple(row.contradiction_pressure for row in rows),
        ),
        status=_summary_status(rows),
        reason_codes=_report_reason_codes(rows),
        rows=rows,
    )


def research_event_source_update_watch_window_report_payload(
    report: ResearchEventSourceUpdateWatchWindowReport,
) -> dict[str, Any]:
    if type(report) is not ResearchEventSourceUpdateWatchWindowReport:
        raise ValueError("report must be a ResearchEventSourceUpdateWatchWindowReport")
    _require_hard_flags(report)
    _reject_unsafe_public_surface("report", report)
    _require_or_set_digest(report)
    for row in report.rows:
        _require_hard_flags(row)
        _reject_unsafe_public_surface("row", row)
        _require_or_set_digest(row)
    payload = _payload_value(report)
    validate_research_event_source_update_watch_window_report_payload(payload)
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    return payload


def validate_research_event_source_update_watch_window_report_payload(
    payload: object,
) -> bool:
    if type(payload) is not dict:
        raise ValueError("public payload must be a JSON object")
    _reject_unsafe_public_surface("public payload", payload)
    _require_public_payload_values(payload)
    _require_public_payload_contract(payload)
    _validate_payload_digest_tree(payload)
    _validate_public_payload_semantics(payload)
    return True


def _row_from_input(
    value: ResearchEventSourceUpdateWatchWindowInput,
    *,
    config: ResearchEventSourceUpdateWatchWindowConfig,
) -> ResearchEventSourceUpdateWatchWindowRow:
    cadence_overrun_ratio = _ratio(
        value.stale_evidence_age_seconds,
        value.expected_update_cadence_seconds,
    )
    stale_evidence_pressure = _bounded_ratio(
        value.stale_evidence_age_seconds,
        config.stale_evidence_block_age_seconds,
    )
    authority_pressure = _AUTHORITY_PENALTY[value.authority_tier]
    deadline_proximity_pressure = _deadline_pressure(
        value.resolution_deadline_seconds,
        config.resolution_deadline_watch_window_seconds,
    )
    watch_window_score = _watch_window_score(
        cadence_pressure=_bounded_ratio(
            cadence_overrun_ratio,
            config.cadence_block_overrun_ratio,
        ),
        stale_evidence_pressure=stale_evidence_pressure,
        authority_pressure=authority_pressure,
        contradiction_pressure=value.contradiction_pressure,
        deadline_proximity_pressure=deadline_proximity_pressure,
    )
    status = _row_status(
        config=config,
        cadence_overrun_ratio=cadence_overrun_ratio,
        stale_evidence_age_seconds=value.stale_evidence_age_seconds,
        contradiction_pressure=value.contradiction_pressure,
        resolution_deadline_seconds=value.resolution_deadline_seconds,
        watch_window_score=watch_window_score,
    )
    return ResearchEventSourceUpdateWatchWindowRow(
        event_scope=value.event_scope,
        authority_tier=value.authority_tier,
        expected_update_cadence_seconds=value.expected_update_cadence_seconds,
        stale_evidence_age_seconds=value.stale_evidence_age_seconds,
        resolution_deadline_seconds=value.resolution_deadline_seconds,
        contradiction_pressure=value.contradiction_pressure,
        cadence_overrun_ratio=cadence_overrun_ratio,
        stale_evidence_pressure=stale_evidence_pressure,
        authority_pressure=authority_pressure,
        deadline_proximity_pressure=deadline_proximity_pressure,
        next_update_watch_window_seconds=_next_update_watch_window_seconds(
            value.expected_update_cadence_seconds,
            value.stale_evidence_age_seconds,
        ),
        watch_window_score=watch_window_score,
        status=status,
        reason_codes=_row_reason_codes(
            config=config,
            authority_tier=value.authority_tier,
            cadence_overrun_ratio=cadence_overrun_ratio,
            stale_evidence_age_seconds=value.stale_evidence_age_seconds,
            contradiction_pressure=value.contradiction_pressure,
            resolution_deadline_seconds=value.resolution_deadline_seconds,
            watch_window_score=watch_window_score,
        ),
    )


def _row_status(
    *,
    config: ResearchEventSourceUpdateWatchWindowConfig,
    cadence_overrun_ratio: Decimal,
    stale_evidence_age_seconds: Decimal,
    contradiction_pressure: Decimal,
    resolution_deadline_seconds: Decimal,
    watch_window_score: Decimal,
) -> str:
    if (
        cadence_overrun_ratio >= config.cadence_block_overrun_ratio
        or stale_evidence_age_seconds >= config.stale_evidence_block_age_seconds
        or contradiction_pressure >= config.contradiction_block_pressure
        or resolution_deadline_seconds
        <= config.resolution_deadline_block_window_seconds
        or watch_window_score >= config.block_score_threshold
    ):
        return "block"
    if (
        cadence_overrun_ratio >= config.cadence_watch_overrun_ratio
        or stale_evidence_age_seconds >= config.stale_evidence_watch_age_seconds
        or contradiction_pressure >= config.contradiction_watch_pressure
        or resolution_deadline_seconds
        <= config.resolution_deadline_watch_window_seconds
        or watch_window_score >= config.watch_score_threshold
    ):
        return "watch"
    return "pass"


def _watch_window_score(
    *,
    cadence_pressure: Decimal,
    stale_evidence_pressure: Decimal,
    authority_pressure: Decimal,
    contradiction_pressure: Decimal,
    deadline_proximity_pressure: Decimal,
) -> Decimal:
    with localcontext(_DECIMAL_CONTEXT):
        return _normalize_ratio(
            "watch_window_score",
            cadence_pressure * Decimal("0.250000")
            + stale_evidence_pressure * Decimal("0.200000")
            + authority_pressure * Decimal("0.150000")
            + contradiction_pressure * Decimal("0.250000")
            + deadline_proximity_pressure * Decimal("0.150000"),
        )


def _deadline_pressure(
    resolution_deadline_seconds: Decimal,
    watch_window_seconds: Decimal,
) -> Decimal:
    if watch_window_seconds == _ZERO:
        return _ONE if resolution_deadline_seconds == _ZERO else _ZERO
    if resolution_deadline_seconds >= watch_window_seconds:
        return _ZERO
    with localcontext(_DECIMAL_CONTEXT):
        return _normalize_ratio(
            "deadline_proximity_pressure",
            (watch_window_seconds - resolution_deadline_seconds) / watch_window_seconds,
        )


def _bounded_ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == _ZERO:
        return _ONE if numerator > _ZERO else _ZERO
    with localcontext(_DECIMAL_CONTEXT):
        return _normalize_ratio("bounded_ratio", min(numerator / denominator, _ONE))


def _next_update_watch_window_seconds(
    expected_update_cadence_seconds: Decimal,
    stale_evidence_age_seconds: Decimal,
) -> Decimal:
    value = expected_update_cadence_seconds - stale_evidence_age_seconds
    if value <= _ZERO:
        return _ZERO
    return _quantize_decimal(value)


def _row_reason_codes(
    *,
    config: ResearchEventSourceUpdateWatchWindowConfig,
    authority_tier: str,
    cadence_overrun_ratio: Decimal,
    stale_evidence_age_seconds: Decimal,
    contradiction_pressure: Decimal,
    resolution_deadline_seconds: Decimal,
    watch_window_score: Decimal,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    if cadence_overrun_ratio >= config.cadence_block_overrun_ratio:
        reason_codes.append("cadence_overrun_block")
    elif cadence_overrun_ratio >= config.cadence_watch_overrun_ratio:
        reason_codes.append("cadence_overrun_watch")
    else:
        reason_codes.append("cadence_overrun_pass")
    if stale_evidence_age_seconds >= config.stale_evidence_block_age_seconds:
        reason_codes.append("stale_evidence_age_block")
    elif stale_evidence_age_seconds >= config.stale_evidence_watch_age_seconds:
        reason_codes.append("stale_evidence_age_watch")
    else:
        reason_codes.append("stale_evidence_age_pass")
    if contradiction_pressure >= config.contradiction_block_pressure:
        reason_codes.append("contradiction_pressure_block")
    elif contradiction_pressure >= config.contradiction_watch_pressure:
        reason_codes.append("contradiction_pressure_watch")
    else:
        reason_codes.append("contradiction_pressure_pass")
    if resolution_deadline_seconds <= config.resolution_deadline_block_window_seconds:
        reason_codes.append("resolution_deadline_proximity_block")
    elif resolution_deadline_seconds <= config.resolution_deadline_watch_window_seconds:
        reason_codes.append("resolution_deadline_proximity_watch")
    else:
        reason_codes.append("resolution_deadline_proximity_pass")
    reason_codes.append(f"authority_tier_{authority_tier}")
    if watch_window_score >= config.block_score_threshold:
        reason_codes.append("watch_window_score_block")
    elif watch_window_score >= config.watch_score_threshold:
        reason_codes.append("watch_window_score_watch")
    else:
        reason_codes.append("watch_window_score_pass")
    return _normalize_reason_codes(tuple(reason_codes))


def _report_reason_codes(
    rows: tuple[ResearchEventSourceUpdateWatchWindowRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return ("no_event_source_update_watch_window_inputs",)
    reason_codes: list[str] = []
    _append_status_reason(
        reason_codes,
        rows,
        "cadence_overrun",
        "cadence_overrun_watch",
        "cadence_overrun_block",
    )
    _append_status_reason(
        reason_codes,
        rows,
        "stale_evidence_age",
        "stale_evidence_age_watch",
        "stale_evidence_age_block",
    )
    _append_status_reason(
        reason_codes,
        rows,
        "contradiction_pressure",
        "contradiction_pressure_watch",
        "contradiction_pressure_block",
    )
    _append_status_reason(
        reason_codes,
        rows,
        "resolution_deadline_proximity",
        "resolution_deadline_proximity_watch",
        "resolution_deadline_proximity_block",
    )
    if any(row.authority_tier == "low" for row in rows):
        reason_codes.append("low_authority_tier_present")
    if any(row.status == "block" for row in rows):
        reason_codes.append("event_source_update_watch_window_row_block")
    elif any(row.status == "watch" for row in rows):
        reason_codes.append("event_source_update_watch_window_row_watch")
    else:
        reason_codes.append("event_source_update_watch_window_pass")
    return _normalize_reason_codes(tuple(reason_codes))


def _append_status_reason(
    reason_codes: list[str],
    rows: tuple[ResearchEventSourceUpdateWatchWindowRow, ...],
    base: str,
    watch_reason: str,
    block_reason: str,
) -> None:
    if any(block_reason in row.reason_codes for row in rows):
        reason_codes.append(f"{base}_block")
    elif any(watch_reason in row.reason_codes for row in rows):
        reason_codes.append(f"{base}_watch")


def _summary_status(rows: tuple[ResearchEventSourceUpdateWatchWindowRow, ...]) -> str:
    if not rows:
        return "block"
    return max((row.status for row in rows), key=lambda status: _STATUS_RANK[status])


def _row_sort_key(row: ResearchEventSourceUpdateWatchWindowRow) -> tuple[int, Decimal, str]:
    return (-_STATUS_RANK[row.status], -row.watch_window_score, row.event_scope)


def _normalize_inputs(
    values: Iterable[ResearchEventSourceUpdateWatchWindowInput],
) -> tuple[ResearchEventSourceUpdateWatchWindowInput, ...]:
    result: list[ResearchEventSourceUpdateWatchWindowInput] = []
    for value in values:
        if type(value) is not ResearchEventSourceUpdateWatchWindowInput:
            raise ValueError("updates must contain ResearchEventSourceUpdateWatchWindowInput")
        _require_hard_flags(value)
        _reject_unsafe_public_surface("input", value)
        _require_or_set_digest(value)
        result.append(value)
    return tuple(sorted(result, key=lambda value: value.event_scope))


def _normalize_rows(
    rows: tuple[ResearchEventSourceUpdateWatchWindowRow, ...],
) -> tuple[ResearchEventSourceUpdateWatchWindowRow, ...]:
    if not isinstance(rows, tuple):
        raise ValueError("rows must be a tuple")
    for row in rows:
        if type(row) is not ResearchEventSourceUpdateWatchWindowRow:
            raise ValueError("rows must contain ResearchEventSourceUpdateWatchWindowRow")
        _require_hard_flags(row)
        _reject_unsafe_public_surface("row", row)
        _require_or_set_digest(row)
    return tuple(sorted(rows, key=_row_sort_key))


def _status_count(
    rows: tuple[ResearchEventSourceUpdateWatchWindowRow, ...],
    status: str,
) -> Decimal:
    return _decimal_count(sum(1 for row in rows if row.status == status))


def _average_decimal(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return _ZERO
    with localcontext(_DECIMAL_CONTEXT):
        return _quantize_decimal(sum(values, _ZERO) / Decimal(len(values)))


def _max_decimal(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return _ZERO
    return _quantize_decimal(max(values))


def _min_decimal(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return _ZERO
    return _quantize_decimal(min(values))


def _validate_row_consistency(row: ResearchEventSourceUpdateWatchWindowRow) -> None:
    expected_next = _next_update_watch_window_seconds(
        row.expected_update_cadence_seconds,
        row.stale_evidence_age_seconds,
    )
    if row.next_update_watch_window_seconds != expected_next:
        raise ValueError("next_update_watch_window_seconds does not match row fields")
    if not any(
        reason_code.endswith(f"_{row.status}") for reason_code in row.reason_codes
    ):
        raise ValueError("status must be explained by reason_codes")


def _validate_report_consistency(
    report: ResearchEventSourceUpdateWatchWindowReport,
) -> None:
    if report.input_count != report.row_count:
        raise ValueError("input_count must match row_count")
    if report.row_count != _decimal_count(len(report.rows)):
        raise ValueError("row_count must match rows")
    if report.pass_count != _status_count(report.rows, "pass"):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _status_count(report.rows, "watch"):
        raise ValueError("watch_count must match rows")
    if report.block_count != _status_count(report.rows, "block"):
        raise ValueError("block_count must match rows")
    if report.status != _summary_status(report.rows):
        raise ValueError("status must match rows")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")
    if report.average_watch_window_score != _average_decimal(
        tuple(row.watch_window_score for row in report.rows),
    ):
        raise ValueError("average_watch_window_score must match rows")
    if report.max_watch_window_score != _max_decimal(
        tuple(row.watch_window_score for row in report.rows),
    ):
        raise ValueError("max_watch_window_score must match rows")
    if report.min_next_update_watch_window_seconds != _min_decimal(
        tuple(row.next_update_watch_window_seconds for row in report.rows),
    ):
        raise ValueError("min_next_update_watch_window_seconds must match rows")
    if report.max_stale_evidence_age_seconds != _max_decimal(
        tuple(row.stale_evidence_age_seconds for row in report.rows),
    ):
        raise ValueError("max_stale_evidence_age_seconds must match rows")
    if report.max_contradiction_pressure != _max_decimal(
        tuple(row.contradiction_pressure for row in report.rows),
    ):
        raise ValueError("max_contradiction_pressure must match rows")


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == _ZERO:
        return _ZERO
    with localcontext(_DECIMAL_CONTEXT):
        return _quantize_decimal(numerator / denominator)


def _decimal_count(value: int) -> Decimal:
    return _quantize_decimal(Decimal(value))


def _normalize_reason_codes(reason_codes: tuple[str, ...]) -> tuple[str, ...]:
    if not isinstance(reason_codes, tuple):
        raise ValueError("reason_codes must be a tuple")
    normalized: list[str] = []
    for reason_code in reason_codes:
        _require_canonical_string("reason_code", reason_code)
        if reason_code not in normalized:
            normalized.append(reason_code)
    return tuple(normalized)


def _require_public_payload_values(value: object) -> None:
    if type(value) is dict:
        for key, item in value.items():
            if key in ("paper_only", "report_only", "readonly") and item is not True:
                raise ValueError(f"{key} must be True")
            if key == _DIGEST_FIELD:
                _require_sha256(_DIGEST_FIELD, item)
            _require_public_payload_values(item)
    elif type(value) is list:
        for item in value:
            _require_public_payload_values(item)
    elif type(value) in (str, bool) or value is None:
        return
    else:
        raise ValueError("public payload values must be JSON strings or booleans")


def _require_public_payload_contract(payload: dict[str, Any]) -> None:
    _require_public_payload_flags(payload)
    _require_exact_public_payload_schema(
        "report payload",
        payload,
        ResearchEventSourceUpdateWatchWindowReport,
    )
    _require_status("status", payload.get("status"))
    rows = payload.get("rows")
    if type(rows) is not list:
        raise ValueError("rows must be a list")
    for row in rows:
        if type(row) is not dict:
            raise ValueError("rows must contain JSON objects")
        _require_public_payload_flags(row)
        _require_exact_public_payload_schema(
            "row payload",
            row,
            ResearchEventSourceUpdateWatchWindowRow,
        )
        _require_status("status", row.get("status"))


def _require_exact_public_payload_schema(
    label: str,
    payload: dict[str, Any],
    payload_type: type[object],
) -> None:
    expected_fields = frozenset(field.name for field in fields(payload_type))
    if type(payload) is not dict or frozenset(payload) != expected_fields:
        raise ValueError(f"{label} fields must match exact public schema")


def _require_public_payload_flags(payload: dict[str, Any]) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if payload.get(field_name) is not True:
            raise ValueError(f"{field_name} must be True")


def _validate_payload_digest_tree(payload: dict[str, Any]) -> None:
    rows = payload.get("rows")
    if type(rows) is not list:
        raise ValueError("rows must be a list")
    for row in rows:
        if type(row) is not dict:
            raise ValueError("rows must contain JSON objects")
        supplied = row.get(_DIGEST_FIELD)
        if type(supplied) is not str:
            raise ValueError("derived_validation_digest must be a string")
        expected = _payload_sha256(_without_digest(row))
        if supplied != expected:
            raise ValueError("derived_validation_digest does not match public payload row")
    supplied_report = payload.get(_DIGEST_FIELD)
    if type(supplied_report) is not str:
        raise ValueError("derived_validation_digest must be a string")
    expected_report = _payload_sha256(_without_digest(payload))
    if supplied_report != expected_report:
        raise ValueError("derived_validation_digest does not match public payload")


def _validate_public_payload_semantics(payload: dict[str, Any]) -> None:
    rows = tuple(_row_from_public_payload(row) for row in payload["rows"])
    validated_report = ResearchEventSourceUpdateWatchWindowReport(
        generated_at=_public_payload_datetime("generated_at", payload["generated_at"]),
        config_version=payload["config_version"],
        input_count=_public_payload_decimal("input_count", payload["input_count"]),
        row_count=_public_payload_decimal("row_count", payload["row_count"]),
        pass_count=_public_payload_decimal("pass_count", payload["pass_count"]),
        watch_count=_public_payload_decimal("watch_count", payload["watch_count"]),
        block_count=_public_payload_decimal("block_count", payload["block_count"]),
        average_watch_window_score=_public_payload_decimal(
            "average_watch_window_score",
            payload["average_watch_window_score"],
        ),
        max_watch_window_score=_public_payload_decimal(
            "max_watch_window_score",
            payload["max_watch_window_score"],
        ),
        min_next_update_watch_window_seconds=_public_payload_decimal(
            "min_next_update_watch_window_seconds",
            payload["min_next_update_watch_window_seconds"],
        ),
        max_stale_evidence_age_seconds=_public_payload_decimal(
            "max_stale_evidence_age_seconds",
            payload["max_stale_evidence_age_seconds"],
        ),
        max_contradiction_pressure=_public_payload_decimal(
            "max_contradiction_pressure",
            payload["max_contradiction_pressure"],
        ),
        status=payload["status"],
        reason_codes=_public_payload_reason_codes(
            "reason_codes",
            payload["reason_codes"],
        ),
        rows=rows,
        derived_validation_digest=payload[_DIGEST_FIELD],
        paper_only=payload["paper_only"],
        report_only=payload["report_only"],
        readonly=payload["readonly"],
    )
    if _payload_value(validated_report) != payload:
        raise ValueError("public payload must use canonical report values")


def _row_from_public_payload(
    payload: dict[str, Any],
) -> ResearchEventSourceUpdateWatchWindowRow:
    return ResearchEventSourceUpdateWatchWindowRow(
        event_scope=payload["event_scope"],
        authority_tier=payload["authority_tier"],
        expected_update_cadence_seconds=_public_payload_decimal(
            "expected_update_cadence_seconds",
            payload["expected_update_cadence_seconds"],
        ),
        stale_evidence_age_seconds=_public_payload_decimal(
            "stale_evidence_age_seconds",
            payload["stale_evidence_age_seconds"],
        ),
        resolution_deadline_seconds=_public_payload_decimal(
            "resolution_deadline_seconds",
            payload["resolution_deadline_seconds"],
        ),
        contradiction_pressure=_public_payload_decimal(
            "contradiction_pressure",
            payload["contradiction_pressure"],
        ),
        cadence_overrun_ratio=_public_payload_decimal(
            "cadence_overrun_ratio",
            payload["cadence_overrun_ratio"],
        ),
        stale_evidence_pressure=_public_payload_decimal(
            "stale_evidence_pressure",
            payload["stale_evidence_pressure"],
        ),
        authority_pressure=_public_payload_decimal(
            "authority_pressure",
            payload["authority_pressure"],
        ),
        deadline_proximity_pressure=_public_payload_decimal(
            "deadline_proximity_pressure",
            payload["deadline_proximity_pressure"],
        ),
        next_update_watch_window_seconds=_public_payload_decimal(
            "next_update_watch_window_seconds",
            payload["next_update_watch_window_seconds"],
        ),
        watch_window_score=_public_payload_decimal(
            "watch_window_score",
            payload["watch_window_score"],
        ),
        status=payload["status"],
        reason_codes=_public_payload_reason_codes(
            "reason_codes",
            payload["reason_codes"],
        ),
        derived_validation_digest=payload[_DIGEST_FIELD],
        paper_only=payload["paper_only"],
        report_only=payload["report_only"],
        readonly=payload["readonly"],
    )


def _public_payload_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a Decimal-derived string")
    try:
        parsed = Decimal(value)
        canonical = _decimal_payload(parsed)
    except DecimalException as exc:
        raise ValueError(f"{field_name} must be a Decimal-derived string") from exc
    if not parsed.is_finite() or canonical != value:
        raise ValueError(f"{field_name} must be a canonical Decimal-derived string")
    return parsed


def _public_payload_datetime(field_name: str, value: object) -> datetime:
    if type(value) is not str or not value.endswith("Z"):
        raise ValueError(f"{field_name} must be a canonical UTC datetime string")
    try:
        parsed = datetime.fromisoformat(f"{value[:-1]}+00:00")
    except ValueError as exc:
        raise ValueError(f"{field_name} must be a canonical UTC datetime string") from exc
    parsed = _as_utc(field_name, parsed)
    if _payload_value(parsed) != value:
        raise ValueError(f"{field_name} must be a canonical UTC datetime string")
    return parsed


def _public_payload_reason_codes(
    field_name: str,
    value: object,
) -> tuple[str, ...]:
    if type(value) is not list:
        raise ValueError(f"{field_name} must be a list")
    return tuple(value)


def _without_digest(value: dict[str, Any]) -> dict[str, Any]:
    return {key: item for key, item in value.items() if key != _DIGEST_FIELD}


def _payload_value(value: object) -> Any:
    if is_dataclass(value):
        payload: dict[str, Any] = {}
        for field in fields(value):
            payload[field.name] = _payload_value(getattr(value, field.name))
        return payload
    if isinstance(value, tuple):
        return [_payload_value(item) for item in value]
    if isinstance(value, datetime):
        return value.isoformat().replace("+00:00", "Z")
    if isinstance(value, Decimal):
        return _decimal_payload(value)
    if isinstance(value, (str, bool)) or value is None:
        return value
    raise ValueError(f"cannot serialize {type(value).__name__}")


def _require_or_set_digest(value: object) -> None:
    current = getattr(value, _DIGEST_FIELD, None)
    if current == "":
        object.__setattr__(value, _DIGEST_FIELD, _derived_validation_digest(value))
        return
    _require_sha256(_DIGEST_FIELD, current)
    if current != _derived_validation_digest(value):
        raise ValueError("derived_validation_digest does not match public payload")


def _derived_validation_digest(value: object) -> str:
    payload = _payload_value(value)
    if not isinstance(payload, dict):
        raise ValueError("digest payload must be a JSON object")
    payload.pop(_DIGEST_FIELD, None)
    return _payload_sha256(payload)


def _payload_sha256(payload: dict[str, Any]) -> str:
    return sha256(
        json.dumps(
            payload,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
        ).encode("utf-8"),
    ).hexdigest()


def _decimal_payload(value: Decimal) -> str:
    return format(_quantize_decimal(value), "f")


def _as_utc(field_name: str, value: datetime) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _normalize_positive_decimal(field_name: str, value: Decimal) -> Decimal:
    normalized = _normalize_nonnegative_decimal(field_name, value)
    if normalized <= _ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _normalize_nonnegative_decimal(field_name: str, value: Decimal) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized < _ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _normalize_ratio(field_name: str, value: Decimal) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized < _ZERO or normalized > _ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return normalized


def _normalize_decimal(field_name: str, value: Decimal) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return _quantize_decimal(value)


def _quantize_decimal(value: Decimal) -> Decimal:
    with localcontext(_DECIMAL_CONTEXT):
        return value.quantize(_QUANTUM)


def _require_positive_decimal(field_name: str, value: Decimal) -> None:
    if value <= _ZERO:
        raise ValueError(f"{field_name} must be positive")


def _require_upper_threshold_pair(
    watch_name: str,
    watch_value: Decimal,
    block_name: str,
    block_value: Decimal,
) -> None:
    if block_value <= watch_value:
        raise ValueError(f"{block_name} must exceed {watch_name}")


def _require_lower_seconds_pair(
    watch_name: str,
    watch_value: Decimal,
    block_name: str,
    block_value: Decimal,
) -> None:
    if block_value >= watch_value:
        raise ValueError(f"{block_name} must be below {watch_name}")


def _require_canonical_string(field_name: str, value: str) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value:
        raise ValueError(f"{field_name} must be non-empty")
    if value != value.strip():
        raise ValueError(f"{field_name} must be stripped")
    if any(character.isspace() for character in value):
        raise ValueError(f"{field_name} must not contain whitespace")
    lowered = value.lower()
    if value != lowered:
        raise ValueError(f"{field_name} must be lowercase")
    if any(fragment in lowered for fragment in _UNSAFE_PUBLIC_SURFACE_FRAGMENTS):
        raise ValueError(f"{field_name} contains unsafe public surface")


def _require_member(field_name: str, value: str, allowed: tuple[str, ...]) -> None:
    _require_canonical_string(field_name, value)
    if value not in allowed:
        raise ValueError(f"{field_name} must be one of {allowed}")


def _require_status(field_name: str, value: str) -> None:
    _require_member(field_name, value, _STATUSES)


def _require_exact_type(field_name: str, value: object, expected_type: type[object]) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{field_name} must be exactly {expected_type.__name__}")


def _require_hard_flags(value: object) -> None:
    if getattr(value, "paper_only", None) is not True:
        raise ValueError("paper_only must be True")
    if getattr(value, "report_only", None) is not True:
        raise ValueError("report_only must be True")
    if getattr(value, "readonly", None) is not True:
        raise ValueError("readonly must be True")


def _require_sha256(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if len(value) != 64 or any(character not in "0123456789abcdef" for character in value):
        raise ValueError(f"{field_name} must be a SHA-256 hex digest")


def _reject_unsafe_public_surface(label: str, value: object, path: str = "") -> None:
    if is_dataclass(value):
        for field in fields(value):
            _reject_unsafe_public_surface(label, getattr(value, field.name), field.name)
        return
    if isinstance(value, dict):
        for key, item in value.items():
            key_path = str(key) if not path else f"{path}.{key}"
            _reject_unsafe_public_text(label, str(key), key_path)
            _reject_unsafe_public_surface(label, item, key_path)
        return
    if isinstance(value, (tuple, list)):
        for index, item in enumerate(value):
            _reject_unsafe_public_surface(label, item, f"{path}[{index}]")
        return
    if isinstance(value, str):
        _reject_unsafe_public_text(label, value, path)


def _reject_unsafe_public_text(label: str, value: str, path: str) -> None:
    lowered = value.lower()
    if any(fragment in lowered for fragment in _UNSAFE_PUBLIC_SURFACE_FRAGMENTS):
        raise ValueError(f"{label} contains unsafe public surface at {path}")
