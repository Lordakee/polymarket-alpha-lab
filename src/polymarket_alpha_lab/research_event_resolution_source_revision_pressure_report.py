"""Read-only event resolution source revision pressure report."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, InvalidOperation, localcontext
from hashlib import sha256
import json
from typing import Any

from polymarket_alpha_lab.team_paper_guard import require_paper_only_flags


DEFAULT_RESEARCH_EVENT_RESOLUTION_SOURCE_REVISION_PRESSURE_REPORT_CONFIG_VERSION = (
    "research-event-resolution-source-revision-pressure-report-v0"
)

_DECIMAL_CONTEXT = Context(prec=64)
_QUANTUM = Decimal("0.000001")
_ZERO = Decimal("0.000000")
_ONE = Decimal("1.000000")
_SECONDS_PER_DAY = Decimal("86400")
_MICROSECONDS_PER_SECOND = Decimal("1000000")
_STATUSES = ("pass", "watch", "block")
_STATUS_RANK = {
    "block": Decimal("0.000000"),
    "watch": Decimal("1.000000"),
    "pass": Decimal("2.000000"),
}
_DIGEST_FIELD = "derived_validation_digest"


def _join_parts(*parts: str) -> str:
    return "".join(parts)


_UNSAFE_PUBLIC_SURFACE_FRAGMENTS = (
    _join_parts("raw", "_", "candidate"),
    _join_parts("candidate", "_", "id"),
    _join_parts("candidate", "-", "id"),
    _join_parts("market", "_", "id"),
    _join_parts("market", "-", "id"),
    _join_parts("market", "_", "slug"),
    _join_parts("market", "-", "slug"),
    "slug",
    _join_parts("que", "stion"),
    _join_parts("source", "_", "url"),
    _join_parts("source", "-", "url"),
    _join_parts("source", " ", "url"),
    _join_parts("source", "_", "text"),
    _join_parts("source", "-", "text"),
    _join_parts("source", " ", "text"),
    "raw",
    "url",
    "dsn",
    _join_parts("ta", "ble"),
    _join_parts("to", "ken"),
    _join_parts("au", "th"),
    _join_parts("wall", "et"),
    _join_parts("or", "der"),
    _join_parts("tra", "de"),
    "http://",
    "https://",
    "://",
    "postgres://",
    "mysql://",
    "sqlite://",
)

_ROW_PAYLOAD_KEYS = (
    "event_key",
    "revision_key",
    "source_family",
    "status",
    "revision_count",
    "contradiction_revision_count",
    "material_revision_score",
    "origin_drift_score",
    "pressure_score",
    "revision_age_seconds",
    "review_required",
    "missing_review",
    "reason_codes",
    "paper_only",
    "report_only",
    "readonly",
)
_REPORT_PAYLOAD_KEYS = (
    "generated_at",
    "config_version",
    "revision_observation_count",
    "pass_count",
    "watch_count",
    "block_count",
    "pressure_event_count",
    "review_required_count",
    "missing_review_count",
    "max_revision_count",
    "max_contradiction_revision_count",
    "max_material_revision_score",
    "max_origin_drift_score",
    "max_pressure_score",
    "max_revision_age_seconds",
    "watch_ratio",
    "block_ratio",
    "status",
    "reason_codes",
    "rows",
    _DIGEST_FIELD,
    "paper_only",
    "report_only",
    "readonly",
)

__all__ = (
    "DEFAULT_RESEARCH_EVENT_RESOLUTION_SOURCE_REVISION_PRESSURE_REPORT_CONFIG_VERSION",
    "ResearchEventResolutionSourceRevisionPressureConfig",
    "ResearchEventResolutionSourceRevisionPressureInput",
    "ResearchEventResolutionSourceRevisionPressureReport",
    "ResearchEventResolutionSourceRevisionPressureRow",
    "build_research_event_resolution_source_revision_pressure_report",
    "research_event_resolution_source_revision_pressure_report_payload",
    "validate_research_event_resolution_source_revision_pressure_report_payload",
)


@dataclass(frozen=True)
class ResearchEventResolutionSourceRevisionPressureConfig:
    config_version: str = (
        DEFAULT_RESEARCH_EVENT_RESOLUTION_SOURCE_REVISION_PRESSURE_REPORT_CONFIG_VERSION
    )
    watch_revision_count: Decimal = Decimal("2.000000")
    block_revision_count: Decimal = Decimal("4.000000")
    watch_contradiction_revision_count: Decimal = Decimal("1.000000")
    block_contradiction_revision_count: Decimal = Decimal("2.000000")
    watch_material_revision_score: Decimal = Decimal("0.250000")
    block_material_revision_score: Decimal = Decimal("0.600000")
    watch_origin_drift_score: Decimal = Decimal("0.250000")
    block_origin_drift_score: Decimal = Decimal("0.600000")
    max_unreviewed_revision_age_seconds: Decimal = Decimal("86400.000000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            "config",
            self,
            ResearchEventResolutionSourceRevisionPressureConfig,
        )
        _require_public_identifier("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_EVENT_RESOLUTION_SOURCE_REVISION_PRESSURE_REPORT_CONFIG_VERSION
        ):
            raise ValueError("config_version must be supported")
        for field_name in (
            "watch_revision_count",
            "block_revision_count",
            "watch_contradiction_revision_count",
            "block_contradiction_revision_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_count(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "watch_material_revision_score",
            "block_material_revision_score",
            "watch_origin_drift_score",
            "block_origin_drift_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "max_unreviewed_revision_age_seconds",
            _normalize_nonnegative_decimal(
                "max_unreviewed_revision_age_seconds",
                self.max_unreviewed_revision_age_seconds,
            ),
        )
        _require_threshold_pair(
            "watch_revision_count",
            self.watch_revision_count,
            "block_revision_count",
            self.block_revision_count,
        )
        _require_threshold_pair(
            "watch_contradiction_revision_count",
            self.watch_contradiction_revision_count,
            "block_contradiction_revision_count",
            self.block_contradiction_revision_count,
        )
        _require_threshold_pair(
            "watch_material_revision_score",
            self.watch_material_revision_score,
            "block_material_revision_score",
            self.block_material_revision_score,
        )
        _require_threshold_pair(
            "watch_origin_drift_score",
            self.watch_origin_drift_score,
            "block_origin_drift_score",
            self.block_origin_drift_score,
        )
        require_paper_only_flags("source revision pressure config", self)
        _reject_unsafe_public_value("config", self)


@dataclass(frozen=True)
class ResearchEventResolutionSourceRevisionPressureInput:
    event_key: str
    revision_key: str
    source_family: str
    revision_count: Decimal
    contradiction_revision_count: Decimal
    material_revision_score: Decimal
    origin_drift_score: Decimal
    observed_at: datetime
    review_completed: bool
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            "input",
            self,
            ResearchEventResolutionSourceRevisionPressureInput,
        )
        for field_name in ("event_key", "revision_key", "source_family"):
            _require_public_identifier(field_name, getattr(self, field_name))
        for field_name in ("revision_count", "contradiction_revision_count"):
            object.__setattr__(
                self,
                field_name,
                _normalize_count(field_name, getattr(self, field_name)),
            )
        for field_name in ("material_revision_score", "origin_drift_score"):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        _require_bool("review_completed", self.review_completed)
        require_paper_only_flags("source revision pressure input", self)
        _reject_unsafe_public_value("input", self)


@dataclass(frozen=True)
class ResearchEventResolutionSourceRevisionPressureRow:
    event_key: str
    revision_key: str
    source_family: str
    status: str
    revision_count: Decimal
    contradiction_revision_count: Decimal
    material_revision_score: Decimal
    origin_drift_score: Decimal
    pressure_score: Decimal
    revision_age_seconds: Decimal
    review_required: bool
    missing_review: bool
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type("row", self, ResearchEventResolutionSourceRevisionPressureRow)
        for field_name in ("event_key", "revision_key", "source_family"):
            _require_public_identifier(field_name, getattr(self, field_name))
        _require_member("status", self.status, _STATUSES)
        for field_name in ("revision_count", "contradiction_revision_count"):
            object.__setattr__(
                self,
                field_name,
                _normalize_count(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "material_revision_score",
            "origin_drift_score",
            "pressure_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "revision_age_seconds",
            _normalize_nonnegative_decimal(
                "revision_age_seconds",
                self.revision_age_seconds,
            ),
        )
        _require_bool("review_required", self.review_required)
        _require_bool("missing_review", self.missing_review)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        _validate_row(self)
        require_paper_only_flags("source revision pressure row", self)
        _reject_unsafe_public_value("row", self)


@dataclass(frozen=True)
class ResearchEventResolutionSourceRevisionPressureReport:
    generated_at: datetime
    config_version: str
    revision_observation_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    pressure_event_count: Decimal
    review_required_count: Decimal
    missing_review_count: Decimal
    max_revision_count: Decimal
    max_contradiction_revision_count: Decimal
    max_material_revision_score: Decimal
    max_origin_drift_score: Decimal
    max_pressure_score: Decimal
    max_revision_age_seconds: Decimal
    watch_ratio: Decimal
    block_ratio: Decimal
    status: str
    reason_codes: tuple[str, ...]
    rows: tuple[ResearchEventResolutionSourceRevisionPressureRow, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_identifier("config_version", self.config_version)
        for field_name in (
            "revision_observation_count",
            "pass_count",
            "watch_count",
            "block_count",
            "pressure_event_count",
            "review_required_count",
            "missing_review_count",
            "max_revision_count",
            "max_contradiction_revision_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_count(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "max_material_revision_score",
            "max_origin_drift_score",
            "max_pressure_score",
            "watch_ratio",
            "block_ratio",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "max_revision_age_seconds",
            _normalize_nonnegative_decimal(
                "max_revision_age_seconds",
                self.max_revision_age_seconds,
            ),
        )
        _require_member("status", self.status, _STATUSES)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        _validate_report(self)
        require_paper_only_flags("source revision pressure report", self)
        _reject_unsafe_public_value("report", self)
        if self.derived_validation_digest == "":
            object.__setattr__(
                self,
                "derived_validation_digest",
                _payload_digest(_public_payload(self, include_digest=False)),
            )
        else:
            _require_sha256_digest(
                "derived_validation_digest",
                self.derived_validation_digest,
            )
            expected = _payload_digest(_public_payload(self, include_digest=False))
            if self.derived_validation_digest != expected:
                raise ValueError("derived_validation_digest does not match public payload")

    @property
    def public_payload(self) -> dict[str, Any]:
        return _public_payload(self, include_digest=True)


def build_research_event_resolution_source_revision_pressure_report(
    observations: Sequence[ResearchEventResolutionSourceRevisionPressureInput],
    *,
    config: ResearchEventResolutionSourceRevisionPressureConfig,
    generated_at: datetime,
) -> ResearchEventResolutionSourceRevisionPressureReport:
    if type(config) is not ResearchEventResolutionSourceRevisionPressureConfig:
        raise ValueError(
            "config must be a ResearchEventResolutionSourceRevisionPressureConfig",
        )
    require_paper_only_flags("source revision pressure config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    normalized = _normalize_observations(observations, generated_at=generated_at_utc)
    rows = _sort_rows(
        tuple(_row_from_observation(item, config, generated_at_utc) for item in normalized),
    )
    count = _decimal_count(len(rows))
    return ResearchEventResolutionSourceRevisionPressureReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        revision_observation_count=count,
        pass_count=_status_count(rows, "pass"),
        watch_count=_status_count(rows, "watch"),
        block_count=_status_count(rows, "block"),
        pressure_event_count=_decimal_count(sum(1 for row in rows if row.status != "pass")),
        review_required_count=_decimal_count(sum(1 for row in rows if row.review_required)),
        missing_review_count=_decimal_count(sum(1 for row in rows if row.missing_review)),
        max_revision_count=_max_decimal(tuple(row.revision_count for row in rows)),
        max_contradiction_revision_count=_max_decimal(
            tuple(row.contradiction_revision_count for row in rows),
        ),
        max_material_revision_score=_max_decimal(
            tuple(row.material_revision_score for row in rows),
        ),
        max_origin_drift_score=_max_decimal(tuple(row.origin_drift_score for row in rows)),
        max_pressure_score=_max_decimal(tuple(row.pressure_score for row in rows)),
        max_revision_age_seconds=_max_decimal(
            tuple(row.revision_age_seconds for row in rows),
        ),
        watch_ratio=_ratio(
            _decimal_count(sum(1 for row in rows if row.status != "pass")),
            count,
        ),
        block_ratio=_ratio(_status_count(rows, "block"), count),
        status=_report_status(rows),
        reason_codes=_report_reason_codes(rows),
        rows=rows,
    )


def research_event_resolution_source_revision_pressure_report_payload(
    report: ResearchEventResolutionSourceRevisionPressureReport,
) -> dict[str, Any]:
    if type(report) is not ResearchEventResolutionSourceRevisionPressureReport:
        raise ValueError(
            "report must be a ResearchEventResolutionSourceRevisionPressureReport",
        )
    require_paper_only_flags("source revision pressure report", report)
    payload = report.public_payload
    validate_research_event_resolution_source_revision_pressure_report_payload(payload)
    return payload


def validate_research_event_resolution_source_revision_pressure_report_payload(
    payload: dict[str, Any],
) -> bool:
    if type(payload) is not dict:
        raise ValueError("payload must be a JSON object")
    if _public_payload_has_unsafe_surface(payload):
        raise ValueError("unsafe public payload")
    _reject_unsafe_public_payload("payload", payload)
    _require_payload_keys("payload", payload, _REPORT_PAYLOAD_KEYS)
    rows = payload["rows"]
    if type(rows) is not list:
        raise ValueError("payload rows must be a list")
    for row in rows:
        if type(row) is not dict:
            raise ValueError("payload rows must contain JSON objects")
        _require_payload_keys("row payload", row, _ROW_PAYLOAD_KEYS)
    _reject_float_or_int_payload(payload)
    _validate_payload_digest(payload)
    return True


def _normalize_observations(
    value: object,
    *,
    generated_at: datetime,
) -> tuple[ResearchEventResolutionSourceRevisionPressureInput, ...]:
    if isinstance(value, (str, bytes)) or not isinstance(value, Sequence):
        raise ValueError("observations must be a sequence")
    observations = tuple(value)
    seen: set[tuple[str, str]] = set()
    for item in observations:
        if type(item) is not ResearchEventResolutionSourceRevisionPressureInput:
            raise ValueError("observations must contain source revision pressure inputs")
        require_paper_only_flags("source revision pressure input", item)
        if item.observed_at > generated_at:
            raise ValueError("observed_at must not be after generated_at")
        key = (item.event_key, item.revision_key)
        if key in seen:
            raise ValueError("revision_key must be unique per event_key")
        seen.add(key)
    return tuple(sorted(observations, key=lambda item: (item.event_key, item.revision_key)))


def _row_from_observation(
    item: ResearchEventResolutionSourceRevisionPressureInput,
    config: ResearchEventResolutionSourceRevisionPressureConfig,
    generated_at: datetime,
) -> ResearchEventResolutionSourceRevisionPressureRow:
    revision_age_seconds = _age_seconds(generated_at, item.observed_at)
    base_status = _base_status(item, config)
    pressure_score = _pressure_score(item, config)
    review_required = base_status != "pass"
    missing_review = review_required and not item.review_completed
    stale_unreviewed = (
        missing_review
        and revision_age_seconds >= config.max_unreviewed_revision_age_seconds
    )
    status = "block" if stale_unreviewed else base_status
    return ResearchEventResolutionSourceRevisionPressureRow(
        event_key=item.event_key,
        revision_key=item.revision_key,
        source_family=item.source_family,
        status=status,
        revision_count=item.revision_count,
        contradiction_revision_count=item.contradiction_revision_count,
        material_revision_score=item.material_revision_score,
        origin_drift_score=item.origin_drift_score,
        pressure_score=pressure_score,
        revision_age_seconds=revision_age_seconds,
        review_required=review_required,
        missing_review=missing_review,
        reason_codes=_row_reason_codes(
            item,
            config,
            status=status,
            review_required=review_required,
            missing_review=missing_review,
            stale_unreviewed=stale_unreviewed,
        ),
    )


def _base_status(
    item: ResearchEventResolutionSourceRevisionPressureInput,
    config: ResearchEventResolutionSourceRevisionPressureConfig,
) -> str:
    if (
        item.revision_count >= config.block_revision_count
        or item.contradiction_revision_count >= config.block_contradiction_revision_count
        or item.material_revision_score >= config.block_material_revision_score
        or item.origin_drift_score >= config.block_origin_drift_score
    ):
        return "block"
    if (
        item.revision_count >= config.watch_revision_count
        or item.contradiction_revision_count >= config.watch_contradiction_revision_count
        or item.material_revision_score >= config.watch_material_revision_score
        or item.origin_drift_score >= config.watch_origin_drift_score
    ):
        return "watch"
    return "pass"


def _pressure_score(
    item: ResearchEventResolutionSourceRevisionPressureInput,
    config: ResearchEventResolutionSourceRevisionPressureConfig,
) -> Decimal:
    return max(
        _cap_ratio(_ratio(item.revision_count, config.block_revision_count)),
        _cap_ratio(
            _ratio(
                item.contradiction_revision_count,
                config.block_contradiction_revision_count,
            ),
        ),
        item.material_revision_score,
        item.origin_drift_score,
    )


def _row_reason_codes(
    item: ResearchEventResolutionSourceRevisionPressureInput,
    config: ResearchEventResolutionSourceRevisionPressureConfig,
    *,
    status: str,
    review_required: bool,
    missing_review: bool,
    stale_unreviewed: bool,
) -> tuple[str, ...]:
    if status == "pass":
        return ("source_revision_pressure_clear",)
    reason_codes: list[str] = []
    _append_threshold_reason(
        reason_codes,
        item.revision_count,
        config.watch_revision_count,
        config.block_revision_count,
        "revision_count",
    )
    _append_threshold_reason(
        reason_codes,
        item.contradiction_revision_count,
        config.watch_contradiction_revision_count,
        config.block_contradiction_revision_count,
        "contradiction_revision",
    )
    _append_threshold_reason(
        reason_codes,
        item.material_revision_score,
        config.watch_material_revision_score,
        config.block_material_revision_score,
        "material_revision",
    )
    _append_threshold_reason(
        reason_codes,
        item.origin_drift_score,
        config.watch_origin_drift_score,
        config.block_origin_drift_score,
        "origin_drift",
    )
    if review_required:
        reason_codes.append("source_revision_review_required")
    if missing_review:
        reason_codes.append("missing_source_revision_review")
    if stale_unreviewed:
        reason_codes.append("stale_unreviewed_source_revision_block")
    return _normalize_reason_codes("reason_codes", tuple(reason_codes))


def _append_threshold_reason(
    reason_codes: list[str],
    value: Decimal,
    watch_threshold: Decimal,
    block_threshold: Decimal,
    reason_stem: str,
) -> None:
    if value >= block_threshold:
        reason_codes.append(f"{reason_stem}_block")
    elif value >= watch_threshold:
        reason_codes.append(f"{reason_stem}_watch")


def _report_status(
    rows: tuple[ResearchEventResolutionSourceRevisionPressureRow, ...],
) -> str:
    if any(row.status == "block" for row in rows):
        return "block"
    if any(row.status == "watch" for row in rows):
        return "watch"
    return "pass"


def _report_reason_codes(
    rows: tuple[ResearchEventResolutionSourceRevisionPressureRow, ...],
) -> tuple[str, ...]:
    if not rows or all(row.status == "pass" for row in rows):
        return ("source_revision_pressure_clear",)
    reason_codes: list[str] = []
    if any(
        "revision_count_watch" in row.reason_codes
        or "revision_count_block" in row.reason_codes
        for row in rows
    ):
        reason_codes.append("revision_count_pressure_present")
    if any(
        "contradiction_revision_watch" in row.reason_codes
        or "contradiction_revision_block" in row.reason_codes
        for row in rows
    ):
        reason_codes.append("contradiction_revision_pressure_present")
    if any(
        "material_revision_watch" in row.reason_codes
        or "material_revision_block" in row.reason_codes
        for row in rows
    ):
        reason_codes.append("material_revision_pressure_present")
    if any(
        "origin_drift_watch" in row.reason_codes
        or "origin_drift_block" in row.reason_codes
        for row in rows
    ):
        reason_codes.append("origin_drift_pressure_present")
    if any("source_revision_review_required" in row.reason_codes for row in rows):
        reason_codes.append("source_revision_review_required_present")
    if any("missing_source_revision_review" in row.reason_codes for row in rows):
        reason_codes.append("missing_source_revision_review_present")
    if any(row.status == "block" for row in rows):
        reason_codes.append("source_revision_pressure_block_present")
    elif any(row.status == "watch" for row in rows):
        reason_codes.append("source_revision_pressure_watch_present")
    else:
        reason_codes.append("source_revision_pressure_clear")
    return _normalize_reason_codes("reason_codes", tuple(reason_codes))


def _validate_row(row: ResearchEventResolutionSourceRevisionPressureRow) -> None:
    if row.missing_review and not row.review_required:
        raise ValueError("missing_review requires review_required")
    if row.status == "pass":
        if row.review_required or row.missing_review:
            raise ValueError("pass rows must not require review")
        if row.reason_codes != ("source_revision_pressure_clear",):
            raise ValueError("pass rows require clear reason")
    if row.status in ("watch", "block") and not row.review_required:
        raise ValueError("pressure rows require review_required")
    if row.status == "watch" and not any(
        reason_code.endswith("_watch") for reason_code in row.reason_codes
    ):
        raise ValueError("watch rows require watch reason")
    if row.status == "block" and not (
        any(reason_code.endswith("_block") for reason_code in row.reason_codes)
        or "stale_unreviewed_source_revision_block" in row.reason_codes
    ):
        raise ValueError("block rows require block reason")


def _validate_report(report: ResearchEventResolutionSourceRevisionPressureReport) -> None:
    if report.revision_observation_count != _decimal_count(len(report.rows)):
        raise ValueError("revision_observation_count must match rows")
    for status, field_name in (
        ("pass", "pass_count"),
        ("watch", "watch_count"),
        ("block", "block_count"),
    ):
        if getattr(report, field_name) != _status_count(report.rows, status):
            raise ValueError(f"{field_name} must match rows")
    if (
        report.pass_count + report.watch_count + report.block_count
        != report.revision_observation_count
    ):
        raise ValueError("status counts must sum to revision_observation_count")
    if report.pressure_event_count != _decimal_count(
        sum(1 for row in report.rows if row.status != "pass"),
    ):
        raise ValueError("pressure_event_count must match rows")
    if report.review_required_count != _decimal_count(
        sum(1 for row in report.rows if row.review_required),
    ):
        raise ValueError("review_required_count must match rows")
    if report.missing_review_count != _decimal_count(
        sum(1 for row in report.rows if row.missing_review),
    ):
        raise ValueError("missing_review_count must match rows")
    if report.max_revision_count != _max_decimal(
        tuple(row.revision_count for row in report.rows),
    ):
        raise ValueError("max_revision_count must match rows")
    if report.max_contradiction_revision_count != _max_decimal(
        tuple(row.contradiction_revision_count for row in report.rows),
    ):
        raise ValueError("max_contradiction_revision_count must match rows")
    if report.max_material_revision_score != _max_decimal(
        tuple(row.material_revision_score for row in report.rows),
    ):
        raise ValueError("max_material_revision_score must match rows")
    if report.max_origin_drift_score != _max_decimal(
        tuple(row.origin_drift_score for row in report.rows),
    ):
        raise ValueError("max_origin_drift_score must match rows")
    if report.max_pressure_score != _max_decimal(
        tuple(row.pressure_score for row in report.rows),
    ):
        raise ValueError("max_pressure_score must match rows")
    if report.max_revision_age_seconds != _max_decimal(
        tuple(row.revision_age_seconds for row in report.rows),
    ):
        raise ValueError("max_revision_age_seconds must match rows")
    if report.watch_ratio != _ratio(report.pressure_event_count, report.revision_observation_count):
        raise ValueError("watch_ratio must match rows")
    if report.block_ratio != _ratio(report.block_count, report.revision_observation_count):
        raise ValueError("block_ratio must match rows")
    if report.status != _report_status(report.rows):
        raise ValueError("status must match rows")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")


def _normalize_rows(
    value: object,
) -> tuple[ResearchEventResolutionSourceRevisionPressureRow, ...]:
    if isinstance(value, (str, bytes)) or not isinstance(value, Sequence):
        raise ValueError("rows must be a sequence")
    rows = tuple(value)
    seen: set[tuple[str, str]] = set()
    for row in rows:
        if type(row) is not ResearchEventResolutionSourceRevisionPressureRow:
            raise ValueError("rows must contain source revision pressure rows")
        require_paper_only_flags("source revision pressure row", row)
        key = (row.event_key, row.revision_key)
        if key in seen:
            raise ValueError("rows must be unique by event_key and revision_key")
        seen.add(key)
    return _sort_rows(rows)


def _sort_rows(
    rows: tuple[ResearchEventResolutionSourceRevisionPressureRow, ...],
) -> tuple[ResearchEventResolutionSourceRevisionPressureRow, ...]:
    return tuple(
        sorted(
            rows,
            key=lambda row: (
                _STATUS_RANK[row.status],
                row.event_key,
                row.revision_key,
                row.source_family,
            ),
        ),
    )


def _status_count(
    rows: tuple[ResearchEventResolutionSourceRevisionPressureRow, ...],
    status: str,
) -> Decimal:
    return _decimal_count(sum(1 for row in rows if row.status == status))


def _max_decimal(values: tuple[Decimal, ...]) -> Decimal:
    return max(values, default=_ZERO)


def _decimal_count(value: int) -> Decimal:
    if type(value) is not int or value < 0:
        raise ValueError("count source must be a nonnegative int")
    with localcontext(_DECIMAL_CONTEXT):
        return Decimal(value).quantize(_QUANTUM)


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == _ZERO:
        return _ZERO
    with localcontext(_DECIMAL_CONTEXT):
        return (numerator / denominator).quantize(_QUANTUM)


def _cap_ratio(value: Decimal) -> Decimal:
    return min(_ONE, max(_ZERO, value)).quantize(_QUANTUM)


def _age_seconds(generated_at: datetime, observed_at: datetime) -> Decimal:
    if generated_at < observed_at:
        raise ValueError("generated_at must be >= observed_at")
    delta = generated_at - observed_at
    with localcontext(_DECIMAL_CONTEXT):
        seconds = (
            Decimal(delta.days) * _SECONDS_PER_DAY
            + Decimal(delta.seconds)
            + (Decimal(delta.microseconds) / _MICROSECONDS_PER_SECOND)
        )
        return seconds.quantize(_QUANTUM)


def _normalize_count(field_name: str, value: object) -> Decimal:
    decimal_value = _normalize_nonnegative_decimal(field_name, value)
    if decimal_value != decimal_value.to_integral_value():
        raise ValueError(f"{field_name} must be a whole-number Decimal")
    return decimal_value


def _normalize_ratio(field_name: str, value: object) -> Decimal:
    decimal_value = _normalize_decimal(field_name, value)
    if decimal_value < _ZERO or decimal_value > _ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return decimal_value.quantize(_QUANTUM)


def _normalize_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _normalize_decimal(field_name, value)
    if decimal_value < _ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return decimal_value.quantize(_QUANTUM)


def _normalize_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    with localcontext(_DECIMAL_CONTEXT):
        try:
            return (+value).quantize(_QUANTUM)
        except InvalidOperation as exc:
            raise ValueError(f"{field_name} must be finite") from exc


def _require_threshold_pair(
    watch_field_name: str,
    watch_value: Decimal,
    block_field_name: str,
    block_value: Decimal,
) -> None:
    if watch_value <= _ZERO:
        raise ValueError(f"{watch_field_name} must be positive")
    if block_value <= watch_value:
        raise ValueError(f"{block_field_name} must exceed {watch_field_name}")


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_bool(field_name: str, value: object) -> None:
    if type(value) is not bool:
        raise ValueError(f"{field_name} must be a bool")


def _require_member(field_name: str, value: object, allowed_values: tuple[str, ...]) -> None:
    if type(value) is not str or value not in allowed_values:
        raise ValueError(f"{field_name} must be one of {allowed_values}")


def _require_exact_type(field_name: str, value: object, expected_type: type[object]) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{field_name} must be a {expected_type.__name__}")


def _require_public_identifier(field_name: str, value: object) -> None:
    if type(value) is not str or not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical public identifier")
    _reject_unsafe_text(field_name, value)
    if len(value) > 128:
        raise ValueError(f"{field_name} must be at most 128 characters")
    if not value[0].isalnum():
        raise ValueError(f"{field_name} must start with an alphanumeric character")
    allowed_extra = {"_", "-", "."}
    if any(not (character.isalnum() or character in allowed_extra) for character in value):
        raise ValueError(f"{field_name} must be a canonical public identifier")


def _normalize_reason_codes(field_name: str, values: object) -> tuple[str, ...]:
    if type(values) is not tuple:
        raise ValueError(f"{field_name} must be a tuple")
    normalized: list[str] = []
    seen: set[str] = set()
    for value in values:
        _require_public_identifier(field_name, value)
        if value not in seen:
            normalized.append(value)
            seen.add(value)
    if not normalized:
        raise ValueError(f"{field_name} must be nonempty")
    return tuple(normalized)


def _public_payload(
    report: ResearchEventResolutionSourceRevisionPressureReport,
    *,
    include_digest: bool,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "generated_at": report.generated_at.isoformat(),
        "config_version": report.config_version,
        "revision_observation_count": _decimal_payload(report.revision_observation_count),
        "pass_count": _decimal_payload(report.pass_count),
        "watch_count": _decimal_payload(report.watch_count),
        "block_count": _decimal_payload(report.block_count),
        "pressure_event_count": _decimal_payload(report.pressure_event_count),
        "review_required_count": _decimal_payload(report.review_required_count),
        "missing_review_count": _decimal_payload(report.missing_review_count),
        "max_revision_count": _decimal_payload(report.max_revision_count),
        "max_contradiction_revision_count": _decimal_payload(
            report.max_contradiction_revision_count,
        ),
        "max_material_revision_score": _decimal_payload(report.max_material_revision_score),
        "max_origin_drift_score": _decimal_payload(report.max_origin_drift_score),
        "max_pressure_score": _decimal_payload(report.max_pressure_score),
        "max_revision_age_seconds": _decimal_payload(report.max_revision_age_seconds),
        "watch_ratio": _decimal_payload(report.watch_ratio),
        "block_ratio": _decimal_payload(report.block_ratio),
        "status": report.status,
        "reason_codes": list(report.reason_codes),
        "rows": [_row_payload(row) for row in report.rows],
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    if include_digest:
        payload[_DIGEST_FIELD] = report.derived_validation_digest
    _reject_unsafe_public_payload("public payload", payload)
    return _arrange_payload_keys(payload, _REPORT_PAYLOAD_KEYS)


def _row_payload(row: ResearchEventResolutionSourceRevisionPressureRow) -> dict[str, Any]:
    return {
        "event_key": row.event_key,
        "revision_key": row.revision_key,
        "source_family": row.source_family,
        "status": row.status,
        "revision_count": _decimal_payload(row.revision_count),
        "contradiction_revision_count": _decimal_payload(
            row.contradiction_revision_count,
        ),
        "material_revision_score": _decimal_payload(row.material_revision_score),
        "origin_drift_score": _decimal_payload(row.origin_drift_score),
        "pressure_score": _decimal_payload(row.pressure_score),
        "revision_age_seconds": _decimal_payload(row.revision_age_seconds),
        "review_required": row.review_required,
        "missing_review": row.missing_review,
        "reason_codes": list(row.reason_codes),
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }


def _decimal_payload(value: Decimal) -> str:
    return str(value)


def _payload_digest(payload_without_digest: dict[str, Any]) -> str:
    encoded = json.dumps(
        payload_without_digest,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return sha256(encoded).hexdigest()


def _validate_payload_digest(payload: dict[str, Any]) -> None:
    digest = payload.get(_DIGEST_FIELD)
    _require_sha256_digest(_DIGEST_FIELD, digest)
    unsigned = dict(payload)
    unsigned.pop(_DIGEST_FIELD)
    expected = _payload_digest(_arrange_payload_keys(unsigned, _REPORT_PAYLOAD_KEYS))
    if digest != expected:
        raise ValueError("derived_validation_digest does not match public payload")


def _require_sha256_digest(field_name: str, value: object) -> None:
    if type(value) is not str or len(value) != 64:
        raise ValueError(f"{field_name} must be a lowercase sha256 digest")
    if any(character not in "0123456789abcdef" for character in value):
        raise ValueError(f"{field_name} must be a lowercase sha256 digest")


def _arrange_payload_keys(
    payload: dict[str, Any],
    key_sequence: tuple[str, ...],
) -> dict[str, Any]:
    arranged = {key: payload[key] for key in key_sequence if key in payload}
    for key, value in payload.items():
        if key not in arranged:
            arranged[key] = value
    return arranged


def _require_payload_keys(
    label: str,
    payload: dict[str, Any],
    expected_keys: tuple[str, ...],
) -> None:
    if tuple(payload) != expected_keys:
        raise ValueError(f"{label} keys must match public payload schema")


def _reject_float_or_int_payload(value: object) -> None:
    if type(value) in (float, int):
        raise ValueError("payload must not contain numeric JSON primitives")
    if isinstance(value, dict):
        for nested in value.values():
            _reject_float_or_int_payload(nested)
    elif isinstance(value, list):
        for nested in value:
            _reject_float_or_int_payload(nested)


def _public_payload_has_unsafe_surface(value: object) -> bool:
    if isinstance(value, dict):
        return any(
            _unsafe_text(str(key))
            or _public_payload_has_unsafe_surface(nested)
            for key, nested in value.items()
        )
    if isinstance(value, list):
        return any(_public_payload_has_unsafe_surface(nested) for nested in value)
    if type(value) is str:
        return _unsafe_text(value)
    return False


def _reject_unsafe_public_value(label: str, value: object) -> None:
    if is_dataclass(value) and not isinstance(value, type):
        for field in fields(value):
            _reject_unsafe_public_value(field.name, getattr(value, field.name))
        return
    if isinstance(value, dict):
        _reject_unsafe_public_payload(label, value)
        return
    if isinstance(value, tuple | list):
        for item in value:
            _reject_unsafe_public_value(label, item)
        return
    if type(value) is str:
        _reject_unsafe_text(label, value)


def _reject_unsafe_public_payload(label: str, payload: object) -> None:
    if isinstance(payload, dict):
        for key, value in payload.items():
            _reject_unsafe_text(label, str(key))
            _reject_unsafe_public_payload(label, value)
    elif isinstance(payload, list):
        for value in payload:
            _reject_unsafe_public_payload(label, value)
    elif type(payload) is str:
        _reject_unsafe_text(label, payload)


def _reject_unsafe_text(field_name: str, value: str) -> None:
    if _unsafe_text(value):
        raise ValueError(f"{field_name} contains unsafe public value")


def _unsafe_text(value: str) -> bool:
    lowered = value.lower()
    return any(fragment in lowered for fragment in _UNSAFE_PUBLIC_SURFACE_FRAGMENTS)
