"""Report-only event resolution source-lag scorecard reducer."""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable
from dataclasses import asdict, dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
import hashlib
import json
import re
from typing import Any


__all__ = (
    "DEFAULT_RESEARCH_EVENT_RESOLUTION_SOURCE_LAG_SCORECARD_REPORT_CONFIG_VERSION",
    "ResearchEventResolutionSourceLagObservation",
    "ResearchEventResolutionSourceLagScorecardConfig",
    "ResearchEventResolutionSourceLagScorecardReasonCodeCount",
    "ResearchEventResolutionSourceLagScorecardReport",
    "ResearchEventResolutionSourceLagScorecardRow",
    "build_research_event_resolution_source_lag_scorecard_report",
    "research_event_resolution_source_lag_scorecard_report_digest",
    "research_event_resolution_source_lag_scorecard_report_payload",
)


DEFAULT_RESEARCH_EVENT_RESOLUTION_SOURCE_LAG_SCORECARD_REPORT_CONFIG_VERSION = (
    "research-event-resolution-source-lag-scorecard-report-v0"
)
QUANTUM = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
COUNT_QUANTUM = Decimal("1.000000")
SECONDS_PER_DAY = Decimal("86400.000000")
MICROSECONDS_PER_SECOND = Decimal("1000000.000000")
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
STATUS_VALUES = ("pass", "watch", "block")
STATUS_WEIGHT = {
    "block": Decimal("2.000000"),
    "watch": Decimal("1.000000"),
    "pass": Decimal("0.000000"),
}
PHASE_FLAG_FIELDS = ("paper_only", "report_only", "readonly")
NO_OBSERVATIONS_REASON = "resolution_source_lag_no_observations"
FINGERPRINT_RE = re.compile(r"^sha256:[0-9a-f]{12,64}$")
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
REASON_CODE_RE = re.compile(r"^[a-z0-9][a-z0-9_]{0,95}$")
PUBLIC_ID_RE = re.compile(r"^[a-z0-9][a-z0-9_.-]{0,127}$")
RAW_PUBLIC_FRAGMENTS = (
    "://",
    "candidate",
    "market",
    "source_url",
    "source_text",
    "dsn",
    "table",
    "token",
    "postgres",
    "mysql",
    "sqlite",
    "wal" "let",
    "au" "th",
    "ord" "er",
    "tra" "de",
    "exec" "ution",
    "recomm" "endation",
    "siz" "ing",
    "ques" "tion",
    "sl" "ug",
    "secret",
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
class ResearchEventResolutionSourceLagScorecardConfig(_FinalPublicDataclass):
    config_version: str = (
        DEFAULT_RESEARCH_EVENT_RESOLUTION_SOURCE_LAG_SCORECARD_REPORT_CONFIG_VERSION
    )
    watch_lag_seconds: Decimal = Decimal("900.000000")
    block_lag_seconds: Decimal = Decimal("3600.000000")
    min_evidence_count: Decimal = Decimal("2.000000")
    min_parser_confidence: Decimal = Decimal("0.650000")
    dispute_block_count: Decimal = Decimal("1.000000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchEventResolutionSourceLagScorecardConfig,
            "config",
        )
        _require_public_id("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_EVENT_RESOLUTION_SOURCE_LAG_SCORECARD_REPORT_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported value")
        for field_name in (
            "watch_lag_seconds",
            "block_lag_seconds",
            "min_evidence_count",
            "dispute_block_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "min_parser_confidence",
            _require_probability_decimal(
                "min_parser_confidence",
                self.min_parser_confidence,
            ),
        )
        _require_at_most("watch_lag_seconds", self.watch_lag_seconds, self.block_lag_seconds)
        _require_hard_flags("config", self)
        _reject_unsafe_public_payload("config", self)


@dataclass(frozen=True)
class ResearchEventResolutionSourceLagObservation(_FinalPublicDataclass):
    event_fingerprint: str
    reference_available_at: datetime
    resolution_available_at: datetime
    evidence_count: Decimal
    parser_confidence: Decimal
    dispute_count: Decimal
    reason_codes: tuple[str, ...] = ()
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchEventResolutionSourceLagObservation,
            "observation",
        )
        _require_event_fingerprint("event_fingerprint", self.event_fingerprint)
        object.__setattr__(
            self,
            "reference_available_at",
            _as_utc("reference_available_at", self.reference_available_at),
        )
        object.__setattr__(
            self,
            "resolution_available_at",
            _as_utc("resolution_available_at", self.resolution_available_at),
        )
        if self.resolution_available_at < self.reference_available_at:
            raise ValueError("resolution_available_at must not precede reference_available_at")
        for field_name in ("evidence_count", "dispute_count"):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "parser_confidence",
            _require_probability_decimal("parser_confidence", self.parser_confidence),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_input_reason_codes(self.reason_codes),
        )
        _require_hard_flags("observation", self)
        _reject_unsafe_public_payload("observation", self)


@dataclass(frozen=True)
class ResearchEventResolutionSourceLagScorecardRow(_FinalPublicDataclass):
    event_fingerprint: str
    reference_available_at: datetime
    resolution_available_at: datetime
    source_lag_seconds: Decimal
    evidence_count: Decimal
    parser_confidence: Decimal
    dispute_count: Decimal
    status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchEventResolutionSourceLagScorecardRow,
            "row",
        )
        _require_event_fingerprint("event_fingerprint", self.event_fingerprint)
        object.__setattr__(
            self,
            "reference_available_at",
            _as_utc("reference_available_at", self.reference_available_at),
        )
        object.__setattr__(
            self,
            "resolution_available_at",
            _as_utc("resolution_available_at", self.resolution_available_at),
        )
        if self.resolution_available_at < self.reference_available_at:
            raise ValueError("resolution_available_at must not precede reference_available_at")
        for field_name in ("source_lag_seconds", "evidence_count", "dispute_count"):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "parser_confidence",
            _require_probability_decimal("parser_confidence", self.parser_confidence),
        )
        _require_status("status", self.status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes),
        )
        _validate_row(self)
        _require_hard_flags("row", self)
        _reject_unsafe_public_payload("row", self)


@dataclass(frozen=True)
class ResearchEventResolutionSourceLagScorecardReasonCodeCount(_FinalPublicDataclass):
    reason_code: str
    count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchEventResolutionSourceLagScorecardReasonCodeCount,
            "reason_code_count",
        )
        _require_reason_code("reason_code", self.reason_code)
        object.__setattr__(
            self,
            "count",
            _require_positive_decimal("count", self.count),
        )
        _require_hard_flags("reason_code_count", self)
        _reject_unsafe_public_payload("reason_code_count", self)


@dataclass(frozen=True)
class ResearchEventResolutionSourceLagScorecardReport(_FinalPublicDataclass):
    generated_at: datetime
    config_version: str
    status: str
    event_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    mean_source_lag_seconds: Decimal
    max_source_lag_seconds: Decimal
    rows: tuple[ResearchEventResolutionSourceLagScorecardRow, ...]
    observations: tuple[ResearchEventResolutionSourceLagObservation, ...]
    reason_codes: tuple[str, ...]
    reason_code_counts: tuple[ResearchEventResolutionSourceLagScorecardReasonCodeCount, ...]
    derived_validation_digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchEventResolutionSourceLagScorecardReport,
            "report",
        )
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_id("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_EVENT_RESOLUTION_SOURCE_LAG_SCORECARD_REPORT_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported value")
        _require_status("status", self.status)
        for field_name in ("event_count", "pass_count", "watch_count", "block_count"):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in ("mean_source_lag_seconds", "max_source_lag_seconds"):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        object.__setattr__(
            self,
            "observations",
            _normalize_observations(self.observations),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes),
        )
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        _require_sha256_digest("derived_validation_digest", self.derived_validation_digest)
        _validate_report(self)
        _require_hard_flags("report", self)
        _reject_unsafe_public_payload("report", self)
        expected = _report_digest_from_payload(_report_payload(self, include_digest=False))
        if self.derived_validation_digest != expected:
            raise ValueError("derived_validation_digest must match report payload")

    @property
    def payload(self) -> dict[str, object]:
        return research_event_resolution_source_lag_scorecard_report_payload(self)


_PUBLIC_DATACLASS_TYPES = (
    ResearchEventResolutionSourceLagScorecardConfig,
    ResearchEventResolutionSourceLagObservation,
    ResearchEventResolutionSourceLagScorecardRow,
    ResearchEventResolutionSourceLagScorecardReasonCodeCount,
    ResearchEventResolutionSourceLagScorecardReport,
)


def build_research_event_resolution_source_lag_scorecard_report(
    observations: Iterable[ResearchEventResolutionSourceLagObservation],
    *,
    generated_at: datetime,
    config: ResearchEventResolutionSourceLagScorecardConfig | None = None,
) -> ResearchEventResolutionSourceLagScorecardReport:
    if config is None:
        config = ResearchEventResolutionSourceLagScorecardConfig()
    if type(config) is not ResearchEventResolutionSourceLagScorecardConfig:
        raise ValueError(
            "config must be a ResearchEventResolutionSourceLagScorecardConfig",
        )
    _require_hard_flags("config", config)
    generated_at = _as_utc("generated_at", generated_at)
    normalized_observations = _normalize_observations(observations)
    for item in normalized_observations:
        if item.reference_available_at > generated_at:
            raise ValueError("reference_available_at must not be after generated_at")
        if item.resolution_available_at > generated_at:
            raise ValueError("resolution_available_at must not be after generated_at")
    rows = tuple(
        sorted(
            (_row_from_observation(item, config=config) for item in normalized_observations),
            key=_row_sort_key,
        ),
    )
    reason_codes = _report_reason_codes(rows)
    reason_code_counts = _reason_code_counts(rows)
    values: dict[str, object] = {
        "generated_at": generated_at,
        "config_version": config.config_version,
        "status": _rollup_status(tuple(row.status for row in rows)),
        "event_count": _decimal_count(len(rows)),
        "pass_count": _status_count(rows, "pass"),
        "watch_count": _status_count(rows, "watch"),
        "block_count": _status_count(rows, "block"),
        "mean_source_lag_seconds": _mean(
            tuple(row.source_lag_seconds for row in rows),
        ),
        "max_source_lag_seconds": max(
            (row.source_lag_seconds for row in rows),
            default=ZERO,
        ),
        "rows": rows,
        "observations": normalized_observations,
        "reason_codes": reason_codes,
        "reason_code_counts": reason_code_counts,
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    return ResearchEventResolutionSourceLagScorecardReport(
        **values,
        derived_validation_digest=_report_digest_from_payload(
            _json_ready(values),
        ),
    )


def research_event_resolution_source_lag_scorecard_report_payload(
    report: ResearchEventResolutionSourceLagScorecardReport,
) -> dict[str, object]:
    if type(report) is not ResearchEventResolutionSourceLagScorecardReport:
        raise ValueError(
            "report must be a ResearchEventResolutionSourceLagScorecardReport",
        )
    _require_payload_safe_value("report", report)
    _rebuild_public_dataclass("report", report)
    payload = _report_payload(report, include_digest=True)
    _reject_unsafe_public_payload("payload", payload, allow_json_containers=True)
    return payload


def research_event_resolution_source_lag_scorecard_report_digest(
    report: ResearchEventResolutionSourceLagScorecardReport,
) -> str:
    if type(report) is not ResearchEventResolutionSourceLagScorecardReport:
        raise ValueError(
            "report must be a ResearchEventResolutionSourceLagScorecardReport",
        )
    _require_payload_safe_value("report", report)
    return _report_digest_from_payload(_report_payload(report, include_digest=False))


def _row_from_observation(
    observation: ResearchEventResolutionSourceLagObservation,
    *,
    config: ResearchEventResolutionSourceLagScorecardConfig,
) -> ResearchEventResolutionSourceLagScorecardRow:
    source_lag_seconds = _source_lag_seconds(
        observation.reference_available_at,
        observation.resolution_available_at,
    )
    reason_codes = _row_reason_codes(
        observation,
        source_lag_seconds=source_lag_seconds,
        config=config,
    )
    return ResearchEventResolutionSourceLagScorecardRow(
        event_fingerprint=observation.event_fingerprint,
        reference_available_at=observation.reference_available_at,
        resolution_available_at=observation.resolution_available_at,
        source_lag_seconds=source_lag_seconds,
        evidence_count=observation.evidence_count,
        parser_confidence=observation.parser_confidence,
        dispute_count=observation.dispute_count,
        status=_row_status(reason_codes),
        reason_codes=reason_codes,
    )


def _row_reason_codes(
    observation: ResearchEventResolutionSourceLagObservation,
    *,
    source_lag_seconds: Decimal,
    config: ResearchEventResolutionSourceLagScorecardConfig,
) -> tuple[str, ...]:
    reason_codes = [f"input_{reason_code}" for reason_code in observation.reason_codes]
    if source_lag_seconds >= config.block_lag_seconds:
        reason_codes.append("resolution_lag_block")
    elif source_lag_seconds >= config.watch_lag_seconds:
        reason_codes.append("resolution_lag_watch")
    if observation.evidence_count < config.min_evidence_count:
        reason_codes.append("thin_evidence_watch")
    if observation.parser_confidence < config.min_parser_confidence:
        reason_codes.append("low_parser_confidence_watch")
    if observation.dispute_count >= config.dispute_block_count:
        reason_codes.append("source_dispute_block")
    if not any(
        reason_code.endswith("_block") or reason_code.endswith("_watch")
        for reason_code in _scored_reason_codes(tuple(reason_codes))
    ):
        reason_codes.append("resolution_source_lag_clear")
    return _normalize_reason_codes(tuple(reason_codes))


def _row_status(reason_codes: tuple[str, ...]) -> str:
    scored_reason_codes = _scored_reason_codes(reason_codes)
    if any(reason_code.endswith("_block") for reason_code in scored_reason_codes):
        return "block"
    if any(reason_code.endswith("_watch") for reason_code in scored_reason_codes):
        return "watch"
    return "pass"


def _scored_reason_codes(reason_codes: tuple[str, ...]) -> tuple[str, ...]:
    return tuple(
        reason_code
        for reason_code in reason_codes
        if not reason_code.startswith("input_")
    )


def _rollup_status(statuses: tuple[str, ...]) -> str:
    if not statuses:
        return "block"
    if any(status == "block" for status in statuses):
        return "block"
    if any(status == "watch" for status in statuses):
        return "watch"
    return "pass"


def _report_reason_codes(
    rows: tuple[ResearchEventResolutionSourceLagScorecardRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return (NO_OBSERVATIONS_REASON,)
    reason_codes = [
        f"resolution_source_lag_scorecard_{_rollup_status(tuple(row.status for row in rows))}",
    ]
    row_reason_codes = frozenset(
        reason_code
        for row in rows
        for reason_code in row.reason_codes
    )
    for reason_code in (
        "low_parser_confidence_watch",
        "resolution_lag_block",
        "resolution_lag_watch",
        "source_dispute_block",
        "thin_evidence_watch",
    ):
        if reason_code in row_reason_codes:
            reason_codes.append(reason_code)
    for reason_code in sorted(
        reason_code
        for reason_code in row_reason_codes
        if reason_code.startswith("input_")
    ):
        reason_codes.append(reason_code)
    return _normalize_reason_codes(tuple(reason_codes))


def _reason_code_counts(
    rows: tuple[ResearchEventResolutionSourceLagScorecardRow, ...],
) -> tuple[ResearchEventResolutionSourceLagScorecardReasonCodeCount, ...]:
    if not rows:
        return (
            ResearchEventResolutionSourceLagScorecardReasonCodeCount(
                reason_code=NO_OBSERVATIONS_REASON,
                count=COUNT_QUANTUM,
            ),
        )
    counter: Counter[str] = Counter()
    for row in rows:
        counter.update(row.reason_codes)
    return tuple(
        ResearchEventResolutionSourceLagScorecardReasonCodeCount(
            reason_code=reason_code,
            count=_decimal_count(count),
        )
        for reason_code, count in sorted(counter.items(), key=lambda item: (-item[1], item[0]))
    )


def _source_lag_seconds(
    reference_available_at: datetime,
    resolution_available_at: datetime,
) -> Decimal:
    delta = _as_utc(
        "resolution_available_at",
        resolution_available_at,
    ) - _as_utc("reference_available_at", reference_available_at)
    with localcontext(DECIMAL_CONTEXT):
        seconds = (
            Decimal(delta.days) * SECONDS_PER_DAY
            + Decimal(delta.seconds)
            + (Decimal(delta.microseconds) / MICROSECONDS_PER_SECOND)
        )
    return _quantize(seconds)


def _row_sort_key(
    row: ResearchEventResolutionSourceLagScorecardRow,
) -> tuple[Decimal, Decimal, str]:
    return (
        -STATUS_WEIGHT[row.status],
        -row.source_lag_seconds,
        row.event_fingerprint,
    )


def _normalize_observations(
    observations: Iterable[ResearchEventResolutionSourceLagObservation],
) -> tuple[ResearchEventResolutionSourceLagObservation, ...]:
    if isinstance(observations, (str, bytes)):
        raise ValueError("observations must be an iterable")
    try:
        values = tuple(observations)
    except TypeError as exc:
        raise ValueError("observations must be an iterable") from exc
    seen: set[str] = set()
    for item in values:
        if type(item) is not ResearchEventResolutionSourceLagObservation:
            raise ValueError(
                "observations must contain ResearchEventResolutionSourceLagObservation values",
            )
        _require_hard_flags("observation", item)
        if item.event_fingerprint in seen:
            raise ValueError("observations must not repeat event_fingerprint")
        seen.add(item.event_fingerprint)
    return tuple(sorted(values, key=lambda item: item.event_fingerprint))


def _normalize_rows(
    rows: Iterable[ResearchEventResolutionSourceLagScorecardRow],
) -> tuple[ResearchEventResolutionSourceLagScorecardRow, ...]:
    if isinstance(rows, (str, bytes)):
        raise ValueError("rows must be an iterable")
    try:
        values = tuple(rows)
    except TypeError as exc:
        raise ValueError("rows must be an iterable") from exc
    seen: set[str] = set()
    for item in values:
        if type(item) is not ResearchEventResolutionSourceLagScorecardRow:
            raise ValueError(
                "rows must contain ResearchEventResolutionSourceLagScorecardRow values",
            )
        _require_hard_flags("row", item)
        if item.event_fingerprint in seen:
            raise ValueError("rows must not repeat event_fingerprint")
        seen.add(item.event_fingerprint)
    expected = tuple(sorted(values, key=_row_sort_key))
    if values != expected:
        raise ValueError("rows must use canonical sequence")
    return values


def _normalize_reason_code_counts(
    rows: Iterable[ResearchEventResolutionSourceLagScorecardReasonCodeCount],
) -> tuple[ResearchEventResolutionSourceLagScorecardReasonCodeCount, ...]:
    if isinstance(rows, (str, bytes)):
        raise ValueError("reason_code_counts must be an iterable")
    try:
        values = tuple(rows)
    except TypeError as exc:
        raise ValueError("reason_code_counts must be an iterable") from exc
    seen: set[str] = set()
    for item in values:
        if type(item) is not ResearchEventResolutionSourceLagScorecardReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "ResearchEventResolutionSourceLagScorecardReasonCodeCount values",
            )
        _require_hard_flags("reason_code_count", item)
        if item.reason_code in seen:
            raise ValueError("reason_code_counts must not repeat reason_code")
        seen.add(item.reason_code)
    expected = tuple(sorted(values, key=lambda item: (-item.count, item.reason_code)))
    if values != expected:
        raise ValueError("reason_code_counts must use canonical sequence")
    return values


def _validate_row(row: ResearchEventResolutionSourceLagScorecardRow) -> None:
    expected_lag = _source_lag_seconds(
        row.reference_available_at,
        row.resolution_available_at,
    )
    if row.source_lag_seconds != expected_lag:
        raise ValueError("source_lag_seconds must match row timestamps")
    if row.status != _row_status(row.reason_codes):
        raise ValueError("status must match reason_codes")


def _validate_report(report: ResearchEventResolutionSourceLagScorecardReport) -> None:
    rows = report.rows
    if report.event_count != _decimal_count(len(rows)):
        raise ValueError("event_count must match rows")
    for status in STATUS_VALUES:
        field_name = "block_count" if status == "block" else f"{status}_count"
        if getattr(report, field_name) != _status_count(rows, status):
            raise ValueError(f"{field_name} must match rows")
    if report.status != _rollup_status(tuple(row.status for row in rows)):
        raise ValueError("status must match rows")
    if report.mean_source_lag_seconds != _mean(
        tuple(row.source_lag_seconds for row in rows),
    ):
        raise ValueError("mean_source_lag_seconds must match rows")
    if report.max_source_lag_seconds != max(
        (row.source_lag_seconds for row in rows),
        default=ZERO,
    ):
        raise ValueError("max_source_lag_seconds must match rows")
    if report.reason_codes != _report_reason_codes(rows):
        raise ValueError("reason_codes must match rows")
    if report.reason_code_counts != _reason_code_counts(rows):
        raise ValueError("reason_code_counts must match rows")
    row_fingerprints = tuple(sorted(row.event_fingerprint for row in rows))
    observation_fingerprints = tuple(
        observation.event_fingerprint for observation in report.observations
    )
    if row_fingerprints != observation_fingerprints:
        raise ValueError("observations must match rows")


def _status_count(
    rows: tuple[ResearchEventResolutionSourceLagScorecardRow, ...],
    status: str,
) -> Decimal:
    return _decimal_count(sum(1 for row in rows if row.status == status))


def _mean(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return _quantize(sum(values, ZERO) / _decimal_count(len(values)))


def _decimal_count(value: int) -> Decimal:
    return _quantize(Decimal(value))


def _require_exact_type(value: object, expected_type: type[object], label: str) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{label} must be exactly {expected_type.__name__}")


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in PHASE_FLAG_FIELDS:
        if getattr(value, field_name) is not True:
            raise ValueError(f"{field_name} must be True for {label}")


def _as_utc(label: str, value: datetime) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{label} must be a datetime")
    if value.tzinfo is None:
        raise ValueError(f"{label} must be timezone-aware")
    return value.astimezone(UTC)


def _require_decimal(label: str, value: Decimal) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{label} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{label} must be finite")
    return _quantize(value)


def _require_nonnegative_decimal(label: str, value: Decimal) -> Decimal:
    normalized = _require_decimal(label, value)
    if normalized < ZERO:
        raise ValueError(f"{label} must be nonnegative")
    return normalized


def _require_positive_decimal(label: str, value: Decimal) -> Decimal:
    normalized = _require_nonnegative_decimal(label, value)
    if normalized <= ZERO:
        raise ValueError(f"{label} must be positive")
    return normalized


def _require_probability_decimal(label: str, value: Decimal) -> Decimal:
    normalized = _require_nonnegative_decimal(label, value)
    if normalized > ONE:
        raise ValueError(f"{label} must be no greater than 1")
    return normalized


def _require_at_most(label: str, value: Decimal, ceiling: Decimal) -> None:
    if value > ceiling:
        raise ValueError(f"{label} must be no greater than its ceiling")


def _quantize(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(QUANTUM)


def _require_public_id(label: str, value: str) -> None:
    if type(value) is not str:
        raise ValueError(f"{label} must be a string")
    if not PUBLIC_ID_RE.fullmatch(value):
        raise ValueError(f"{label} must be a canonical public identifier")
    _reject_raw_public_text(label, value)


def _require_event_fingerprint(label: str, value: str) -> None:
    if type(value) is not str:
        raise ValueError(f"{label} must be a string")
    if not FINGERPRINT_RE.fullmatch(value):
        raise ValueError(f"{label} must be a redacted sha256 fingerprint")
    _reject_raw_public_text(label, value)


def _require_reason_code(label: str, value: str) -> None:
    if type(value) is not str:
        raise ValueError(f"{label} must be a string")
    if not REASON_CODE_RE.fullmatch(value):
        raise ValueError(f"{label} must be a canonical reason code")
    _reject_raw_public_text(label, value)


def _normalize_input_reason_codes(reason_codes: Iterable[str]) -> tuple[str, ...]:
    values = _normalize_reason_codes(reason_codes)
    for reason_code in values:
        if reason_code.startswith("input_"):
            raise ValueError("reason_codes must not include input_ prefix")
    return values


def _normalize_reason_codes(reason_codes: Iterable[str]) -> tuple[str, ...]:
    if isinstance(reason_codes, (str, bytes)):
        raise ValueError("reason_codes must be an iterable")
    try:
        values = tuple(reason_codes)
    except TypeError as exc:
        raise ValueError("reason_codes must be an iterable") from exc
    for value in values:
        _require_reason_code("reason_codes", value)
    normalized = tuple(sorted(frozenset(values)))
    if len(normalized) != len(values):
        raise ValueError("reason_codes must not repeat values")
    return normalized


def _require_status(label: str, value: str) -> None:
    if type(value) is not str or value not in STATUS_VALUES:
        raise ValueError(f"{label} must be pass, watch, or block")


def _require_sha256_digest(label: str, value: str) -> None:
    if type(value) is not str or not SHA256_RE.fullmatch(value):
        raise ValueError(f"{label} must be a lowercase sha256 digest")


def _reject_raw_public_text(label: str, value: str) -> None:
    lowered = value.lower()
    if any(fragment in lowered for fragment in RAW_PUBLIC_FRAGMENTS):
        raise ValueError(f"{label} contains raw private surface text")


def _reject_unsafe_public_payload(
    label: str,
    value: object,
    *,
    allow_json_containers: bool = False,
) -> None:
    for key, item in _iter_public_items(value, allow_json_containers=allow_json_containers):
        _reject_raw_public_text(f"{label}.{key}", key)
        if type(item) is str:
            _reject_raw_public_text(f"{label}.{key}", item)


def _iter_public_items(
    value: object,
    *,
    allow_json_containers: bool,
) -> tuple[tuple[str, object], ...]:
    if is_dataclass(value) and not isinstance(value, type):
        items: list[tuple[str, object]] = []
        for field in fields(value):
            item = getattr(value, field.name)
            items.append((field.name, item))
            items.extend(
                _iter_public_items(item, allow_json_containers=allow_json_containers),
            )
        return tuple(items)
    if type(value) is tuple:
        items = []
        for item in value:
            items.extend(
                _iter_public_items(item, allow_json_containers=allow_json_containers),
            )
        return tuple(items)
    if allow_json_containers and type(value) is dict:
        items = []
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("payload keys must be strings")
            items.append((key, item))
            items.extend(
                _iter_public_items(item, allow_json_containers=allow_json_containers),
            )
        return tuple(items)
    if allow_json_containers and type(value) is list:
        items = []
        for item in value:
            items.extend(
                _iter_public_items(item, allow_json_containers=allow_json_containers),
            )
        return tuple(items)
    return ()


def _require_payload_safe_value(label: str, value: object) -> None:
    if is_dataclass(value) and not isinstance(value, type):
        if type(value) not in _PUBLIC_DATACLASS_TYPES:
            raise ValueError(f"{label} contains unsupported dataclass")
        for field in fields(value):
            _require_payload_safe_value(f"{label}.{field.name}", getattr(value, field.name))
        return
    if type(value) is Decimal:
        _require_decimal(label, value)
        return
    if type(value) is datetime:
        _as_utc(label, value)
        return
    if type(value) is tuple:
        for index, item in enumerate(value):
            _require_payload_safe_value(f"{label}[{index}]", item)
        return
    if type(value) in (bool, str):
        if type(value) is str:
            _reject_raw_public_text(label, value)
        return
    if value is None:
        return
    if type(value) in (int, float, list, dict, set):
        raise ValueError(f"{label} must come from public dataclass fields")
    raise ValueError(f"{label} contains unsupported value")


def _rebuild_public_dataclass(label: str, value: object) -> None:
    kwargs = {field.name: getattr(value, field.name) for field in fields(value)}
    try:
        type(value)(**kwargs)
    except Exception as exc:
        raise ValueError(f"{label} failed derived_validation_digest validation") from exc


def _json_ready(value: Any) -> Any:
    if is_dataclass(value) and not isinstance(value, type):
        return _json_ready(asdict(value))
    if type(value) is Decimal:
        _require_decimal("decimal", value)
        return str(value)
    if type(value) is datetime:
        return _as_utc("datetime", value).isoformat()
    if type(value) is tuple:
        return [_json_ready(item) for item in value]
    if type(value) is list:
        return [_json_ready(item) for item in value]
    if type(value) is dict:
        ready: dict[str, object] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("payload keys must be strings")
            ready[key] = _json_ready(item)
        return ready
    if type(value) in (bool, str) or value is None:
        return value
    if type(value) in (int, float):
        raise ValueError("payload must not contain numeric primitives")
    raise ValueError("payload contains unsupported value")


def _report_payload(
    report: ResearchEventResolutionSourceLagScorecardReport,
    *,
    include_digest: bool,
) -> dict[str, object]:
    payload = _json_ready(
        {
            "generated_at": report.generated_at,
            "config_version": report.config_version,
            "status": report.status,
            "event_count": report.event_count,
            "pass_count": report.pass_count,
            "watch_count": report.watch_count,
            "block_count": report.block_count,
            "mean_source_lag_seconds": report.mean_source_lag_seconds,
            "max_source_lag_seconds": report.max_source_lag_seconds,
            "rows": report.rows,
            "observations": report.observations,
            "reason_codes": report.reason_codes,
            "reason_code_counts": report.reason_code_counts,
            "paper_only": report.paper_only,
            "report_only": report.report_only,
            "readonly": report.readonly,
        },
    )
    if type(payload) is not dict:
        raise ValueError("payload must be a JSON object")
    if include_digest:
        payload["derived_validation_digest"] = report.derived_validation_digest
    _reject_unsafe_public_payload("payload", payload, allow_json_containers=True)
    return payload


def _report_digest_from_payload(payload: dict[str, object]) -> str:
    ready = _json_ready(payload)
    encoded = json.dumps(ready, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()
