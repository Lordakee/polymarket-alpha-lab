"""Report-only event resolution signal timeliness triage."""

from __future__ import annotations

from dataclasses import asdict, dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_UP, localcontext
from hashlib import sha256
import json
import re
from typing import Any, Mapping, Sequence


DEFAULT_EVENT_RESOLUTION_SIGNAL_TIMELINESS_CONFIG_VERSION = (
    "event-resolution-signal-timeliness-report-v1"
)

QUANTUM = Decimal("0.000001")
ZERO = Decimal("0")
ONE = Decimal("1")
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_UP)

STATUS_PASS = "pass"
STATUS_WATCH = "watch"
STATUS_BLOCK = "block"
STATUSES = frozenset((STATUS_PASS, STATUS_WATCH, STATUS_BLOCK))
STATUS_RANK = {
    STATUS_BLOCK: Decimal("0"),
    STATUS_WATCH: Decimal("1"),
    STATUS_PASS: Decimal("2"),
}

AUTHORITY_TIER_SCORES = {
    "official": Decimal("1.000000"),
    "primary": Decimal("0.800000"),
    "secondary": Decimal("0.600000"),
    "weak": Decimal("0.400000"),
}

REASON_CODE_SEQUENCE = (
    "empty_signals",
    "fresh_authoritative_signal",
    "signal_age_watch",
    "signal_age_block",
    "low_authority_watch",
    "high_contradiction_pressure",
    "high_ambiguity_risk",
    "low_verification_coverage",
    "deadline_approaching",
    "deadline_critical",
    "high_timeliness_score",
    "timely_resolution_signal_pass",
)

PUBLIC_IDENTIFIER_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,127}$")
RESOLUTION_KEY_RE = re.compile(r"^resolution_[A-Za-z0-9_.-]{1,116}$")
DIGEST_RE = re.compile(r"^[0-9a-f]{64}$")
UNSAFE_PUBLIC_TERMS = (
    "candidate",
    "market",
    "slug",
    "question",
    "url",
    "text",
    "dsn",
    "table",
    "token",
    "wallet",
    "order",
    "trade",
    "live",
)


@dataclass(frozen=True)
class EventResolutionSignalTimelinessConfig:
    config_version: str = DEFAULT_EVENT_RESOLUTION_SIGNAL_TIMELINESS_CONFIG_VERSION
    watch_age_to_cadence_ratio: Decimal = Decimal("1.000000")
    block_age_to_cadence_ratio: Decimal = Decimal("2.000000")
    watch_contradiction_pressure: Decimal = Decimal("0.350000")
    block_contradiction_pressure: Decimal = Decimal("0.700000")
    watch_ambiguity_risk: Decimal = Decimal("0.350000")
    block_ambiguity_risk: Decimal = Decimal("0.700000")
    minimum_pass_verification_coverage: Decimal = Decimal("0.800000")
    block_verification_coverage: Decimal = Decimal("0.250000")
    minimum_pass_authority_score: Decimal = Decimal("0.700000")
    minimum_pass_timeliness_score: Decimal = Decimal("0.750000")
    watch_deadline_proximity_seconds: Decimal = Decimal("86400.000000")
    block_deadline_proximity_seconds: Decimal = Decimal("3600.000000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not EventResolutionSignalTimelinessConfig:
            raise TypeError(
                "EventResolutionSignalTimelinessConfig does not support subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(self, EventResolutionSignalTimelinessConfig, "config")
        _require_public_identifier("config_version", self.config_version)
        if self.config_version != DEFAULT_EVENT_RESOLUTION_SIGNAL_TIMELINESS_CONFIG_VERSION:
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "watch_age_to_cadence_ratio",
            "block_age_to_cadence_ratio",
            "watch_deadline_proximity_seconds",
            "block_deadline_proximity_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "watch_contradiction_pressure",
            "block_contradiction_pressure",
            "watch_ambiguity_risk",
            "block_ambiguity_risk",
            "minimum_pass_verification_coverage",
            "block_verification_coverage",
            "minimum_pass_authority_score",
            "minimum_pass_timeliness_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        if self.block_age_to_cadence_ratio <= self.watch_age_to_cadence_ratio:
            raise ValueError("block_age_to_cadence_ratio must exceed watch threshold")
        if self.block_contradiction_pressure < self.watch_contradiction_pressure:
            raise ValueError("block_contradiction_pressure must meet watch threshold")
        if self.block_ambiguity_risk < self.watch_ambiguity_risk:
            raise ValueError("block_ambiguity_risk must meet watch threshold")
        if self.block_verification_coverage >= self.minimum_pass_verification_coverage:
            raise ValueError("block_verification_coverage must be below pass threshold")
        if self.block_deadline_proximity_seconds > self.watch_deadline_proximity_seconds:
            raise ValueError("block_deadline_proximity_seconds must not exceed watch threshold")
        _require_hard_flags("config", self)
        _reject_unsafe_public_payload("config", self)


@dataclass(frozen=True)
class EventResolutionSignalTimelinessInput:
    resolution_key: str
    latest_signal_at: datetime
    expected_update_cadence_seconds: Decimal
    authority_tier: str
    contradiction_pressure: Decimal
    ambiguity_risk: Decimal
    verification_coverage: Decimal
    resolution_deadline_at: datetime
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not EventResolutionSignalTimelinessInput:
            raise TypeError(
                "EventResolutionSignalTimelinessInput does not support subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(self, EventResolutionSignalTimelinessInput, "input")
        _require_resolution_key("resolution_key", self.resolution_key)
        object.__setattr__(
            self,
            "latest_signal_at",
            _as_utc("latest_signal_at", self.latest_signal_at),
        )
        object.__setattr__(
            self,
            "expected_update_cadence_seconds",
            _require_positive_decimal(
                "expected_update_cadence_seconds",
                self.expected_update_cadence_seconds,
            ),
        )
        _require_authority_tier("authority_tier", self.authority_tier)
        for field_name in (
            "contradiction_pressure",
            "ambiguity_risk",
            "verification_coverage",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "resolution_deadline_at",
            _as_utc("resolution_deadline_at", self.resolution_deadline_at),
        )
        _require_hard_flags("input", self)
        _reject_unsafe_public_payload("input", self)


@dataclass(frozen=True)
class EventResolutionSignalTimelinessRow:
    resolution_key: str
    latest_signal_at: datetime
    latest_signal_age_seconds: Decimal
    expected_update_cadence_seconds: Decimal
    age_to_cadence_ratio: Decimal
    authority_tier: str
    authority_score: Decimal
    contradiction_pressure: Decimal
    ambiguity_risk: Decimal
    verification_coverage: Decimal
    resolution_deadline_at: datetime
    deadline_proximity_seconds: Decimal
    timeliness_score: Decimal
    timeliness_status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not EventResolutionSignalTimelinessRow:
            raise TypeError(
                "EventResolutionSignalTimelinessRow does not support subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(self, EventResolutionSignalTimelinessRow, "row")
        _require_resolution_key("resolution_key", self.resolution_key)
        object.__setattr__(
            self,
            "latest_signal_at",
            _as_utc("latest_signal_at", self.latest_signal_at),
        )
        for field_name in (
            "latest_signal_age_seconds",
            "expected_update_cadence_seconds",
            "age_to_cadence_ratio",
            "deadline_proximity_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        _require_authority_tier("authority_tier", self.authority_tier)
        for field_name in (
            "authority_score",
            "contradiction_pressure",
            "ambiguity_risk",
            "verification_coverage",
            "timeliness_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "resolution_deadline_at",
            _as_utc("resolution_deadline_at", self.resolution_deadline_at),
        )
        _require_status("timeliness_status", self.timeliness_status)
        object.__setattr__(self, "reason_codes", _normalize_reason_codes(self.reason_codes))
        _validate_row_consistency(self)
        _require_hard_flags("row", self)
        _reject_unsafe_public_payload("row", self)


@dataclass(frozen=True)
class EventResolutionSignalTimelinessReport:
    generated_at: datetime
    config_version: str
    status: str
    signal_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    average_timeliness_score: Decimal
    max_age_to_cadence_ratio: Decimal
    max_contradiction_pressure: Decimal
    max_ambiguity_risk: Decimal
    min_verification_coverage: Decimal
    min_deadline_proximity_seconds: Decimal
    reason_codes: tuple[str, ...]
    rows: tuple[EventResolutionSignalTimelinessRow, ...]
    derived_validation_digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not EventResolutionSignalTimelinessReport:
            raise TypeError(
                "EventResolutionSignalTimelinessReport does not support subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(self, EventResolutionSignalTimelinessReport, "report")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_identifier("config_version", self.config_version)
        if self.config_version != DEFAULT_EVENT_RESOLUTION_SIGNAL_TIMELINESS_CONFIG_VERSION:
            raise ValueError("config_version must be the supported config version")
        _require_status("status", self.status)
        for field_name in ("signal_count", "pass_count", "watch_count", "block_count"):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "average_timeliness_score",
            "max_contradiction_pressure",
            "max_ambiguity_risk",
            "min_verification_coverage",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "max_age_to_cadence_ratio",
            "min_deadline_proximity_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(self, "reason_codes", _normalize_reason_codes(self.reason_codes))
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        _require_sha256_digest("derived_validation_digest", self.derived_validation_digest)
        _validate_report_consistency(self)
        _require_hard_flags("report", self)
        _reject_unsafe_public_payload("report", self)
        expected_digest = _derived_validation_digest(_report_values_without_digest(self))
        if self.derived_validation_digest != expected_digest:
            raise ValueError("derived_validation_digest does not match report payload")


def build_research_event_resolution_signal_timeliness_report(
    signals: Sequence[EventResolutionSignalTimelinessInput],
    *,
    generated_at: datetime,
    config: EventResolutionSignalTimelinessConfig | None = None,
) -> EventResolutionSignalTimelinessReport:
    if config is None:
        config = EventResolutionSignalTimelinessConfig()
    if type(config) is not EventResolutionSignalTimelinessConfig:
        raise ValueError("config must be an EventResolutionSignalTimelinessConfig")
    _require_hard_flags("config", config)
    generated_at = _as_utc("generated_at", generated_at)
    normalized = _normalize_signals(signals)
    rows = tuple(
        sorted(
            (
                _row_from_signal(signal, generated_at=generated_at, config=config)
                for signal in normalized
            ),
            key=_row_sort_key,
        ),
    )
    values: dict[str, object] = {
        "generated_at": generated_at,
        "config_version": config.config_version,
        "status": _report_status(rows),
        "signal_count": _count_decimal(len(rows)),
        "pass_count": _status_count(rows, STATUS_PASS),
        "watch_count": _status_count(rows, STATUS_WATCH),
        "block_count": _status_count(rows, STATUS_BLOCK),
        "average_timeliness_score": _average(
            tuple(row.timeliness_score for row in rows),
        ),
        "max_age_to_cadence_ratio": _max_decimal(rows, "age_to_cadence_ratio"),
        "max_contradiction_pressure": _max_decimal(rows, "contradiction_pressure"),
        "max_ambiguity_risk": _max_decimal(rows, "ambiguity_risk"),
        "min_verification_coverage": _min_decimal(
            rows,
            "verification_coverage",
            default=ONE,
        ),
        "min_deadline_proximity_seconds": _min_decimal(
            rows,
            "deadline_proximity_seconds",
            default=ZERO,
        ),
        "reason_codes": _report_reason_codes(rows),
        "rows": rows,
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    return EventResolutionSignalTimelinessReport(
        **values,
        derived_validation_digest=_derived_validation_digest(values),
    )


def research_event_resolution_signal_timeliness_report_payload(
    report: EventResolutionSignalTimelinessReport,
) -> dict[str, Any]:
    if type(report) is not EventResolutionSignalTimelinessReport:
        raise ValueError("report must be an EventResolutionSignalTimelinessReport")
    _require_hard_flags("report", report)
    payload = _json_ready(report)
    if type(payload) is not dict:
        raise ValueError("report must serialize to a JSON object")
    _reject_unsafe_public_payload("payload", payload, allow_json_containers=True)
    return payload


def research_event_resolution_signal_timeliness_report_json(
    report: EventResolutionSignalTimelinessReport,
) -> str:
    payload = research_event_resolution_signal_timeliness_report_payload(report)
    return json.dumps(payload, ensure_ascii=True, separators=(",", ":"), sort_keys=True)


def _row_from_signal(
    signal: EventResolutionSignalTimelinessInput,
    *,
    generated_at: datetime,
    config: EventResolutionSignalTimelinessConfig,
) -> EventResolutionSignalTimelinessRow:
    if signal.latest_signal_at > generated_at:
        raise ValueError("latest_signal_at must not be after generated_at")
    latest_signal_age_seconds = _seconds_between(generated_at, signal.latest_signal_at)
    deadline_proximity_seconds = _deadline_seconds(generated_at, signal.resolution_deadline_at)
    raw_age_ratio = _raw_ratio(
        latest_signal_age_seconds,
        signal.expected_update_cadence_seconds,
    )
    age_to_cadence_ratio = _quantize_decimal(raw_age_ratio)
    authority_score = AUTHORITY_TIER_SCORES[signal.authority_tier]
    timeliness_score = _timeliness_score(
        raw_age_ratio=raw_age_ratio,
        authority_score=authority_score,
        verification_coverage=signal.verification_coverage,
        contradiction_pressure=signal.contradiction_pressure,
        ambiguity_risk=signal.ambiguity_risk,
    )
    status = _row_status(
        age_to_cadence_ratio=age_to_cadence_ratio,
        authority_score=authority_score,
        contradiction_pressure=signal.contradiction_pressure,
        ambiguity_risk=signal.ambiguity_risk,
        verification_coverage=signal.verification_coverage,
        deadline_proximity_seconds=deadline_proximity_seconds,
        timeliness_score=timeliness_score,
        config=config,
    )
    return EventResolutionSignalTimelinessRow(
        resolution_key=signal.resolution_key,
        latest_signal_at=signal.latest_signal_at,
        latest_signal_age_seconds=latest_signal_age_seconds,
        expected_update_cadence_seconds=signal.expected_update_cadence_seconds,
        age_to_cadence_ratio=age_to_cadence_ratio,
        authority_tier=signal.authority_tier,
        authority_score=authority_score,
        contradiction_pressure=signal.contradiction_pressure,
        ambiguity_risk=signal.ambiguity_risk,
        verification_coverage=signal.verification_coverage,
        resolution_deadline_at=signal.resolution_deadline_at,
        deadline_proximity_seconds=deadline_proximity_seconds,
        timeliness_score=timeliness_score,
        timeliness_status=status,
        reason_codes=_row_reason_codes(
            age_to_cadence_ratio=age_to_cadence_ratio,
            authority_score=authority_score,
            contradiction_pressure=signal.contradiction_pressure,
            ambiguity_risk=signal.ambiguity_risk,
            verification_coverage=signal.verification_coverage,
            deadline_proximity_seconds=deadline_proximity_seconds,
            timeliness_score=timeliness_score,
            status=status,
            config=config,
        ),
    )


def _row_status(
    *,
    age_to_cadence_ratio: Decimal,
    authority_score: Decimal,
    contradiction_pressure: Decimal,
    ambiguity_risk: Decimal,
    verification_coverage: Decimal,
    deadline_proximity_seconds: Decimal,
    timeliness_score: Decimal,
    config: EventResolutionSignalTimelinessConfig,
) -> str:
    if (
        age_to_cadence_ratio >= config.block_age_to_cadence_ratio
        or contradiction_pressure >= config.block_contradiction_pressure
        or ambiguity_risk >= config.block_ambiguity_risk
        or verification_coverage <= config.block_verification_coverage
        or deadline_proximity_seconds <= config.block_deadline_proximity_seconds
    ):
        return STATUS_BLOCK
    if (
        age_to_cadence_ratio >= config.watch_age_to_cadence_ratio
        or authority_score < config.minimum_pass_authority_score
        or contradiction_pressure >= config.watch_contradiction_pressure
        or ambiguity_risk >= config.watch_ambiguity_risk
        or verification_coverage < config.minimum_pass_verification_coverage
        or deadline_proximity_seconds <= config.watch_deadline_proximity_seconds
        or timeliness_score < config.minimum_pass_timeliness_score
    ):
        return STATUS_WATCH
    return STATUS_PASS


def _row_reason_codes(
    *,
    age_to_cadence_ratio: Decimal,
    authority_score: Decimal,
    contradiction_pressure: Decimal,
    ambiguity_risk: Decimal,
    verification_coverage: Decimal,
    deadline_proximity_seconds: Decimal,
    timeliness_score: Decimal,
    status: str,
    config: EventResolutionSignalTimelinessConfig,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    if (
        age_to_cadence_ratio < config.watch_age_to_cadence_ratio
        and authority_score >= Decimal("1.000000")
    ):
        reason_codes.append("fresh_authoritative_signal")
    if age_to_cadence_ratio >= config.block_age_to_cadence_ratio:
        reason_codes.append("signal_age_block")
    elif age_to_cadence_ratio >= config.watch_age_to_cadence_ratio:
        reason_codes.append("signal_age_watch")
    if authority_score < config.minimum_pass_authority_score:
        reason_codes.append("low_authority_watch")
    if contradiction_pressure >= config.watch_contradiction_pressure:
        reason_codes.append("high_contradiction_pressure")
    if ambiguity_risk >= config.watch_ambiguity_risk:
        reason_codes.append("high_ambiguity_risk")
    if verification_coverage < config.minimum_pass_verification_coverage:
        reason_codes.append("low_verification_coverage")
    if deadline_proximity_seconds <= config.block_deadline_proximity_seconds:
        reason_codes.append("deadline_critical")
    elif deadline_proximity_seconds <= config.watch_deadline_proximity_seconds:
        reason_codes.append("deadline_approaching")
    if timeliness_score >= config.minimum_pass_timeliness_score:
        reason_codes.append("high_timeliness_score")
    if status == STATUS_PASS:
        reason_codes.append("timely_resolution_signal_pass")
    return _normalize_reason_codes(tuple(reason_codes))


def _timeliness_score(
    *,
    raw_age_ratio: Decimal,
    authority_score: Decimal,
    verification_coverage: Decimal,
    contradiction_pressure: Decimal,
    ambiguity_risk: Decimal,
) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        freshness_score = ONE - min(raw_age_ratio, ONE)
        value = (
            (freshness_score * Decimal("0.500000"))
            + (authority_score * Decimal("0.250000"))
            + (verification_coverage * Decimal("0.250000"))
            - ((contradiction_pressure + ambiguity_risk) * Decimal("0.125000"))
        )
    return _clamp_ratio(value)


def _validate_row_consistency(row: EventResolutionSignalTimelinessRow) -> None:
    if row.timeliness_status == STATUS_PASS:
        if "timely_resolution_signal_pass" not in row.reason_codes:
            raise ValueError("pass rows must include timely_resolution_signal_pass")
    if row.timeliness_status == STATUS_BLOCK:
        block_reasons = {
            "signal_age_block",
            "high_contradiction_pressure",
            "high_ambiguity_risk",
            "low_verification_coverage",
            "deadline_critical",
        }
        if not any(reason_code in row.reason_codes for reason_code in block_reasons):
            raise ValueError("block rows must include a block reason")


def _validate_report_consistency(report: EventResolutionSignalTimelinessReport) -> None:
    if report.signal_count != _count_decimal(len(report.rows)):
        raise ValueError("signal_count must match rows")
    if report.pass_count != _status_count(report.rows, STATUS_PASS):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _status_count(report.rows, STATUS_WATCH):
        raise ValueError("watch_count must match rows")
    if report.block_count != _status_count(report.rows, STATUS_BLOCK):
        raise ValueError("block_count must match rows")
    if report.pass_count + report.watch_count + report.block_count != report.signal_count:
        raise ValueError("status counts must match signal_count")
    if report.average_timeliness_score != _average(
        tuple(row.timeliness_score for row in report.rows),
    ):
        raise ValueError("average_timeliness_score must match rows")
    if report.max_age_to_cadence_ratio != _max_decimal(report.rows, "age_to_cadence_ratio"):
        raise ValueError("max_age_to_cadence_ratio must match rows")
    if report.max_contradiction_pressure != _max_decimal(report.rows, "contradiction_pressure"):
        raise ValueError("max_contradiction_pressure must match rows")
    if report.max_ambiguity_risk != _max_decimal(report.rows, "ambiguity_risk"):
        raise ValueError("max_ambiguity_risk must match rows")
    if report.min_verification_coverage != _min_decimal(
        report.rows,
        "verification_coverage",
        default=ONE,
    ):
        raise ValueError("min_verification_coverage must match rows")
    if report.min_deadline_proximity_seconds != _min_decimal(
        report.rows,
        "deadline_proximity_seconds",
        default=ZERO,
    ):
        raise ValueError("min_deadline_proximity_seconds must match rows")
    if report.status != _report_status(report.rows):
        raise ValueError("status must match row statuses")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")


def _normalize_signals(
    signals: Sequence[EventResolutionSignalTimelinessInput],
) -> tuple[EventResolutionSignalTimelinessInput, ...]:
    if isinstance(signals, (str, bytes)) or not isinstance(signals, Sequence):
        raise ValueError("signals must be a sequence")
    normalized: list[EventResolutionSignalTimelinessInput] = []
    for signal in signals:
        if type(signal) is not EventResolutionSignalTimelinessInput:
            raise ValueError(
                "signals must contain EventResolutionSignalTimelinessInput",
            )
        _require_hard_flags("input", signal)
        normalized.append(signal)
    return tuple(
        sorted(
            normalized,
            key=lambda item: (item.resolution_key, item.latest_signal_at),
        ),
    )


def _normalize_rows(
    rows: Sequence[EventResolutionSignalTimelinessRow],
) -> tuple[EventResolutionSignalTimelinessRow, ...]:
    if isinstance(rows, (str, bytes)) or not isinstance(rows, Sequence):
        raise ValueError("rows must be a sequence")
    normalized: list[EventResolutionSignalTimelinessRow] = []
    for row in rows:
        if type(row) is not EventResolutionSignalTimelinessRow:
            raise ValueError("rows must contain EventResolutionSignalTimelinessRow")
        _require_hard_flags("row", row)
        normalized.append(row)
    return tuple(sorted(normalized, key=_row_sort_key))


def _report_status(rows: tuple[EventResolutionSignalTimelinessRow, ...]) -> str:
    if not rows:
        return STATUS_BLOCK
    if any(row.timeliness_status == STATUS_BLOCK for row in rows):
        return STATUS_BLOCK
    if any(row.timeliness_status == STATUS_WATCH for row in rows):
        return STATUS_WATCH
    return STATUS_PASS


def _report_reason_codes(
    rows: tuple[EventResolutionSignalTimelinessRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return ("empty_signals",)
    reason_codes: list[str] = []
    for row in rows:
        reason_codes.extend(row.reason_codes)
    return _normalize_reason_codes(tuple(reason_codes))


def _status_count(
    rows: tuple[EventResolutionSignalTimelinessRow, ...],
    status: str,
) -> Decimal:
    return _count_decimal(sum(1 for row in rows if row.timeliness_status == status))


def _average(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return _quantize_decimal(ZERO)
    with localcontext(DECIMAL_CONTEXT):
        return _quantize_decimal(sum(values, ZERO) / Decimal(len(values)))


def _max_decimal(
    rows: tuple[EventResolutionSignalTimelinessRow, ...],
    field_name: str,
) -> Decimal:
    if not rows:
        return _quantize_decimal(ZERO)
    return max(getattr(row, field_name) for row in rows)


def _min_decimal(
    rows: tuple[EventResolutionSignalTimelinessRow, ...],
    field_name: str,
    *,
    default: Decimal,
) -> Decimal:
    if not rows:
        return _quantize_decimal(default)
    return min(getattr(row, field_name) for row in rows)


def _seconds_between(later: datetime, earlier: datetime) -> Decimal:
    later = _as_utc("later", later)
    earlier = _as_utc("earlier", earlier)
    delta = later - earlier
    if delta.days < 0:
        raise ValueError("earlier datetime must not be after later datetime")
    whole_seconds = Decimal(delta.days * 86400 + delta.seconds)
    fractional_seconds = Decimal(delta.microseconds) / Decimal("1000000")
    return _quantize_decimal(whole_seconds + fractional_seconds)


def _deadline_seconds(generated_at: datetime, deadline_at: datetime) -> Decimal:
    generated_at = _as_utc("generated_at", generated_at)
    deadline_at = _as_utc("deadline_at", deadline_at)
    if deadline_at <= generated_at:
        return _quantize_decimal(ZERO)
    return _seconds_between(deadline_at, generated_at)


def _raw_ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return numerator / denominator


def _count_decimal(value: int) -> Decimal:
    if value < 0:
        raise ValueError("count must be nonnegative")
    return _quantize_decimal(Decimal(value))


def _clamp_ratio(value: Decimal) -> Decimal:
    normalized = _quantize_decimal(value)
    if normalized < ZERO:
        return _quantize_decimal(ZERO)
    if normalized > ONE:
        return _quantize_decimal(ONE)
    return normalized


def _require_positive_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_nonnegative_decimal(field_name, value)
    if normalized <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _require_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _require_ratio_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < ZERO or normalized > ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return normalized


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return _quantize_decimal(value)


def _quantize_decimal(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(QUANTUM, rounding=ROUND_HALF_UP)


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_resolution_key(field_name: str, value: object) -> str:
    value = _require_public_identifier(field_name, value)
    if not RESOLUTION_KEY_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a redacted resolution key")
    return value


def _require_public_identifier(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not PUBLIC_IDENTIFIER_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a public identifier")
    _reject_unsafe_public_string(field_name, value)
    return value


def _require_authority_tier(field_name: str, value: object) -> str:
    if type(value) is not str or value not in AUTHORITY_TIER_SCORES:
        raise ValueError(f"{field_name} must be a supported authority tier")
    _reject_unsafe_public_string(field_name, value)
    return value


def _require_status(field_name: str, value: object) -> str:
    if type(value) is not str or value not in STATUSES:
        raise ValueError(f"{field_name} must be pass, watch, or block")
    return value


def _require_sha256_digest(field_name: str, value: object) -> str:
    if type(value) is not str or not DIGEST_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a lowercase sha256 digest")
    return value


def _normalize_reason_codes(reason_codes: Sequence[str]) -> tuple[str, ...]:
    if isinstance(reason_codes, (str, bytes)) or not isinstance(reason_codes, Sequence):
        raise ValueError("reason_codes must be a sequence")
    normalized: list[str] = []
    for reason_code in reason_codes:
        _require_public_identifier("reason_code", reason_code)
        if reason_code not in REASON_CODE_SEQUENCE:
            raise ValueError("reason_code must be supported")
        if reason_code not in normalized:
            normalized.append(reason_code)
    return tuple(
        reason_code
        for reason_code in REASON_CODE_SEQUENCE
        if reason_code in normalized
    )


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if getattr(value, field_name, None) is not True:
            raise ValueError(f"{field_name} must be True for {label}")


def _require_exact_type(value: object, type_: type[object], label: str) -> None:
    if type(value) is not type_:
        raise ValueError(f"{label} must be exactly {type_.__name__}")


def _row_sort_key(
    row: EventResolutionSignalTimelinessRow,
) -> tuple[Decimal, Decimal, Decimal, str]:
    return (
        STATUS_RANK[row.timeliness_status],
        -row.timeliness_score,
        -row.age_to_cadence_ratio,
        row.resolution_key,
    )


def _report_values_without_digest(
    report: EventResolutionSignalTimelinessReport,
) -> dict[str, object]:
    values = asdict(report)
    values.pop("derived_validation_digest", None)
    return values


def _derived_validation_digest(values: Mapping[str, object]) -> str:
    payload = _json_ready(values)
    _reject_unsafe_public_payload(
        "derived_validation_digest payload",
        payload,
        allow_json_containers=True,
    )
    encoded = json.dumps(payload, ensure_ascii=True, separators=(",", ":"), sort_keys=True)
    return sha256(encoded.encode("utf-8")).hexdigest()


def _json_ready(value: Any) -> Any:
    if value is None:
        return None
    if is_dataclass(value) and not isinstance(value, type):
        return _json_ready(asdict(value))
    if type(value) is Decimal:
        if not value.is_finite():
            raise ValueError("Decimal payload value must be finite")
        return str(value)
    if type(value) is datetime:
        return _as_utc("datetime payload value", value).isoformat()
    if type(value) is bool or type(value) is str:
        return value
    if type(value) is int or isinstance(value, float):
        raise ValueError("numeric payload values must be Decimal strings")
    if isinstance(value, Mapping):
        ready: dict[str, Any] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            ready[key] = _json_ready(item)
        return ready
    if isinstance(value, (list, tuple)):
        return [_json_ready(item) for item in value]
    raise ValueError("payload value is not JSON serializable")


def _reject_unsafe_public_payload(
    label: str,
    value: object,
    path: str = "",
    *,
    allow_json_containers: bool = False,
) -> None:
    current_path = path or label
    if is_dataclass(value) and not isinstance(value, type):
        for field in fields(value):
            _reject_unsafe_public_key(field.name, current_path)
            _reject_unsafe_public_payload(
                label,
                getattr(value, field.name),
                field.name if not path else f"{path}.{field.name}",
                allow_json_containers=allow_json_containers,
            )
        return
    if isinstance(value, Mapping):
        if not allow_json_containers:
            raise ValueError(f"{current_path} must remain constructor-normalized")
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            _reject_unsafe_public_key(key, current_path)
            _reject_unsafe_public_payload(
                label,
                item,
                key if not path else f"{path}.{key}",
                allow_json_containers=True,
            )
        return
    if isinstance(value, (list, tuple)):
        if type(value) is list and not allow_json_containers:
            raise ValueError(f"{current_path} must remain constructor-normalized")
        for index, item in enumerate(value):
            _reject_unsafe_public_payload(
                label,
                item,
                f"{current_path}[{index}]",
                allow_json_containers=allow_json_containers,
            )
        return
    if type(value) is str:
        _reject_unsafe_public_string(current_path, value)
        return
    if (
        value is None
        or type(value) is bool
        or type(value) is Decimal
        or type(value) is datetime
    ):
        return
    raise ValueError(f"{current_path} is not a supported public payload value")


def _reject_unsafe_public_key(key: str, path: str) -> None:
    lowered = key.lower()
    if any(term in lowered for term in UNSAFE_PUBLIC_TERMS):
        raise ValueError(f"{path}.{key} has unsafe public field")


def _reject_unsafe_public_string(field_name: str, value: str) -> None:
    lowered = value.lower()
    if "://" in lowered or "?" in lowered or "@" in lowered:
        raise ValueError(f"{field_name} has unsafe public value")
    if any(term in lowered for term in UNSAFE_PUBLIC_TERMS):
        raise ValueError(f"{field_name} has unsafe public value")


__all__ = (
    "DEFAULT_EVENT_RESOLUTION_SIGNAL_TIMELINESS_CONFIG_VERSION",
    "EventResolutionSignalTimelinessConfig",
    "EventResolutionSignalTimelinessInput",
    "EventResolutionSignalTimelinessReport",
    "EventResolutionSignalTimelinessRow",
    "build_research_event_resolution_signal_timeliness_report",
    "research_event_resolution_signal_timeliness_report_json",
    "research_event_resolution_signal_timeliness_report_payload",
)
