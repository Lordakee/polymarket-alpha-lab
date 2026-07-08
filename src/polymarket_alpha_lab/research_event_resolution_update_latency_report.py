"""Report-only event resolution update latency triage."""

from __future__ import annotations

from dataclasses import asdict, dataclass, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
import hashlib
import json
from typing import Any, Iterable, Mapping

from polymarket_alpha_lab.team_paper_guard import (
    json_ready_no_floats,
    require_paper_only_flags,
)


DEFAULT_RESEARCH_EVENT_RESOLUTION_UPDATE_LATENCY_REPORT_CONFIG_VERSION = (
    "research-event-resolution-update-latency-report-v1"
)

STATUSES = ("pass", "watch", "block")
ROW_REASON_CODES = (
    "resolution_update_latency_clear",
    "resolution_update_stale",
    "resolution_update_low_authority",
    "resolution_update_contradiction_pressure",
    "resolution_update_ambiguity_risk",
    "resolution_update_deadline_near",
)
REPORT_REASON_CODES = (
    "resolution_update_latency_empty",
    "resolution_update_latency_clear",
    "resolution_update_stale",
    "resolution_update_low_authority",
    "resolution_update_contradiction_pressure",
    "resolution_update_ambiguity_risk",
    "resolution_update_deadline_near",
)

DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
COUNT_QUANTUM = Decimal("1")
QUANTUM = Decimal("0.000001")
ZERO_COUNT = Decimal("0")
ZERO_QUANTIZED = Decimal("0.000000")
ONE_QUANTIZED = Decimal("1.000000")
SECONDS_PER_DAY = Decimal("86400")
MICROSECONDS_PER_SECOND = Decimal("1000000")

STATUS_RANK = {"block": 0, "watch": 1, "pass": 2}
PUBLIC_SURFACE_FRAGMENTS = (
    "candidate",
    "market",
    "slug",
    "question",
    "url",
    "text",
    "dsn",
    "table",
    "tok" + "en",
    "wal" + "let",
    "or" + "der",
    "tra" + "de",
    "li" + "ve",
)


@dataclass(frozen=True)
class ResearchEventResolutionUpdateLatencyConfig:
    config_version: str = (
        DEFAULT_RESEARCH_EVENT_RESOLUTION_UPDATE_LATENCY_REPORT_CONFIG_VERSION
    )
    expected_cadence_seconds: Decimal = Decimal("1800.000000")
    watch_latency_multiplier: Decimal = Decimal("1.500000")
    block_latency_multiplier: Decimal = Decimal("3.000000")
    authoritative_source_threshold: Decimal = Decimal("0.700000")
    contradiction_watch_threshold: Decimal = Decimal("0.300000")
    contradiction_block_threshold: Decimal = Decimal("0.700000")
    ambiguity_watch_threshold: Decimal = Decimal("0.300000")
    ambiguity_block_threshold: Decimal = Decimal("0.700000")
    deadline_watch_seconds: Decimal = Decimal("7200.000000")
    deadline_block_seconds: Decimal = Decimal("1800.000000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchEventResolutionUpdateLatencyConfig, "config")
        _require_supported_config_version(self.config_version)
        for field_name in (
            "expected_cadence_seconds",
            "deadline_watch_seconds",
            "deadline_block_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_positive_seconds_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "watch_latency_multiplier",
            "block_latency_multiplier",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_positive_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "authoritative_source_threshold",
            "contradiction_watch_threshold",
            "contradiction_block_threshold",
            "ambiguity_watch_threshold",
            "ambiguity_block_threshold",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        if self.block_latency_multiplier <= self.watch_latency_multiplier:
            raise ValueError("block_latency_multiplier must exceed watch_latency_multiplier")
        if self.contradiction_block_threshold < self.contradiction_watch_threshold:
            raise ValueError(
                "contradiction_block_threshold must be at least contradiction_watch_threshold",
            )
        if self.ambiguity_block_threshold < self.ambiguity_watch_threshold:
            raise ValueError(
                "ambiguity_block_threshold must be at least ambiguity_watch_threshold",
            )
        if self.deadline_block_seconds > self.deadline_watch_seconds:
            raise ValueError("deadline_block_seconds must not exceed deadline_watch_seconds")
        require_paper_only_flags("resolution update latency config", self)
        _reject_public_payload("resolution update latency config", self)


@dataclass(frozen=True)
class ResearchEventResolutionUpdateLatencyObservation:
    public_event_key: str
    last_verified_update_at: datetime
    deadline_at: datetime
    expected_cadence_seconds: Decimal | None = None
    source_authority_score: Decimal = Decimal("1.000000")
    contradiction_pressure: Decimal = Decimal("0.000000")
    ambiguity_risk: Decimal = Decimal("0.000000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchEventResolutionUpdateLatencyObservation,
            "observation",
        )
        _require_public_string("public_event_key", self.public_event_key)
        object.__setattr__(
            self,
            "last_verified_update_at",
            _as_utc("last_verified_update_at", self.last_verified_update_at),
        )
        object.__setattr__(self, "deadline_at", _as_utc("deadline_at", self.deadline_at))
        object.__setattr__(
            self,
            "expected_cadence_seconds",
            _normalize_optional_positive_seconds_decimal(
                "expected_cadence_seconds",
                self.expected_cadence_seconds,
            ),
        )
        for field_name in (
            "source_authority_score",
            "contradiction_pressure",
            "ambiguity_risk",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        require_paper_only_flags("resolution update latency observation", self)
        _reject_public_payload("resolution update latency observation", self)


@dataclass(frozen=True)
class ResearchEventResolutionUpdateLatencyRow:
    public_event_key: str
    status: str
    expected_cadence_seconds: Decimal
    last_verified_update_at: datetime
    deadline_at: datetime
    last_verified_update_age_seconds: Decimal
    deadline_proximity_seconds: Decimal
    source_authority_score: Decimal
    contradiction_pressure: Decimal
    ambiguity_risk: Decimal
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchEventResolutionUpdateLatencyRow, "row")
        _require_public_string("public_event_key", self.public_event_key)
        _require_status("status", self.status)
        object.__setattr__(
            self,
            "expected_cadence_seconds",
            _require_positive_seconds_decimal(
                "expected_cadence_seconds",
                self.expected_cadence_seconds,
            ),
        )
        object.__setattr__(
            self,
            "last_verified_update_at",
            _as_utc("last_verified_update_at", self.last_verified_update_at),
        )
        object.__setattr__(self, "deadline_at", _as_utc("deadline_at", self.deadline_at))
        for field_name in (
            "last_verified_update_age_seconds",
            "deadline_proximity_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_seconds_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "source_authority_score",
            "contradiction_pressure",
            "ambiguity_risk",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(
                "reason_codes",
                self.reason_codes,
                allowed=ROW_REASON_CODES,
                allow_empty=False,
            ),
        )
        require_paper_only_flags("resolution update latency row", self)
        _reject_public_payload("resolution update latency row", self)
        _validate_row(self)


@dataclass(frozen=True)
class ResearchEventResolutionUpdateLatencyReport:
    generated_at: datetime
    config_version: str
    status: str
    event_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    stale_count: Decimal
    low_authority_count: Decimal
    contradiction_pressure_count: Decimal
    ambiguity_risk_count: Decimal
    deadline_pressure_count: Decimal
    max_last_verified_update_age_seconds: Decimal
    average_last_verified_update_age_seconds: Decimal
    rows: tuple[ResearchEventResolutionUpdateLatencyRow, ...]
    reason_codes: tuple[str, ...]
    derived_validation_digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchEventResolutionUpdateLatencyReport, "report")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_supported_config_version(self.config_version)
        _require_status("status", self.status)
        for field_name in (
            "event_count",
            "pass_count",
            "watch_count",
            "block_count",
            "stale_count",
            "low_authority_count",
            "contradiction_pressure_count",
            "ambiguity_risk_count",
            "deadline_pressure_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_count_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "max_last_verified_update_age_seconds",
            "average_last_verified_update_age_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_seconds_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(
                "reason_codes",
                self.reason_codes,
                allowed=REPORT_REASON_CODES,
                allow_empty=False,
            ),
        )
        _require_sha256_digest("derived_validation_digest", self.derived_validation_digest)
        require_paper_only_flags("resolution update latency report", self)
        _reject_public_payload("resolution update latency report", self)
        _validate_report(self)
        expected_digest = _report_digest_from_values(_report_values_without_digest(self))
        if self.derived_validation_digest != expected_digest:
            raise ValueError("derived_validation_digest does not match report payload")

    @property
    def payload(self) -> dict[str, Any]:
        return research_event_resolution_update_latency_report_to_payload(self)


def build_research_event_resolution_update_latency_report(
    observations: Iterable[ResearchEventResolutionUpdateLatencyObservation],
    *,
    config: ResearchEventResolutionUpdateLatencyConfig | None = None,
    generated_at: datetime,
) -> ResearchEventResolutionUpdateLatencyReport:
    if config is None:
        config = ResearchEventResolutionUpdateLatencyConfig()
    if type(config) is not ResearchEventResolutionUpdateLatencyConfig:
        raise ValueError("config must be a ResearchEventResolutionUpdateLatencyConfig")
    require_paper_only_flags("resolution update latency config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    normalized_observations = _normalize_observations(observations)
    _validate_observation_times(normalized_observations, generated_at_utc)

    rows = _sort_rows(
        tuple(
            _row_from_observation(
                observation,
                config=config,
                generated_at=generated_at_utc,
            )
            for observation in normalized_observations
        ),
    )
    age_values = tuple(row.last_verified_update_age_seconds for row in rows)
    values: dict[str, object] = {
        "generated_at": generated_at_utc,
        "config_version": config.config_version,
        "status": _report_status(rows),
        "event_count": _count(len(rows)),
        "pass_count": _status_count(rows, "pass"),
        "watch_count": _status_count(rows, "watch"),
        "block_count": _status_count(rows, "block"),
        "stale_count": _reason_count(rows, "resolution_update_stale"),
        "low_authority_count": _reason_count(rows, "resolution_update_low_authority"),
        "contradiction_pressure_count": _reason_count(
            rows,
            "resolution_update_contradiction_pressure",
        ),
        "ambiguity_risk_count": _reason_count(
            rows,
            "resolution_update_ambiguity_risk",
        ),
        "deadline_pressure_count": _reason_count(
            rows,
            "resolution_update_deadline_near",
        ),
        "max_last_verified_update_age_seconds": max(age_values, default=ZERO_QUANTIZED),
        "average_last_verified_update_age_seconds": _average_seconds(age_values),
        "rows": rows,
        "reason_codes": _report_reason_codes(rows),
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    return ResearchEventResolutionUpdateLatencyReport(
        **values,
        derived_validation_digest=_report_digest_from_values(values),
    )


def research_event_resolution_update_latency_report_to_payload(
    report: ResearchEventResolutionUpdateLatencyReport,
) -> dict[str, Any]:
    if type(report) is not ResearchEventResolutionUpdateLatencyReport:
        raise ValueError("report must be a ResearchEventResolutionUpdateLatencyReport")
    require_paper_only_flags("resolution update latency report", report)
    _reject_public_payload("resolution update latency report", report)
    payload = json_ready_no_floats(report)
    if type(payload) is not dict:
        raise ValueError("resolution update latency report payload must be a JSON object")
    _reject_public_payload("resolution update latency report payload", payload)
    return payload


def _row_from_observation(
    observation: ResearchEventResolutionUpdateLatencyObservation,
    *,
    config: ResearchEventResolutionUpdateLatencyConfig,
    generated_at: datetime,
) -> ResearchEventResolutionUpdateLatencyRow:
    cadence_seconds = observation.expected_cadence_seconds or config.expected_cadence_seconds
    age_seconds = _duration_seconds(observation.last_verified_update_at, generated_at)
    deadline_seconds = _deadline_proximity_seconds(generated_at, observation.deadline_at)
    reason_codes = _row_reason_codes(
        age_seconds=age_seconds,
        cadence_seconds=cadence_seconds,
        source_authority_score=observation.source_authority_score,
        contradiction_pressure=observation.contradiction_pressure,
        ambiguity_risk=observation.ambiguity_risk,
        deadline_proximity_seconds=deadline_seconds,
        config=config,
    )
    return ResearchEventResolutionUpdateLatencyRow(
        public_event_key=observation.public_event_key,
        status=_row_status(
            reason_codes=reason_codes,
            age_seconds=age_seconds,
            cadence_seconds=cadence_seconds,
            contradiction_pressure=observation.contradiction_pressure,
            ambiguity_risk=observation.ambiguity_risk,
            deadline_proximity_seconds=deadline_seconds,
            config=config,
        ),
        expected_cadence_seconds=cadence_seconds,
        last_verified_update_at=observation.last_verified_update_at,
        deadline_at=observation.deadline_at,
        last_verified_update_age_seconds=age_seconds,
        deadline_proximity_seconds=deadline_seconds,
        source_authority_score=observation.source_authority_score,
        contradiction_pressure=observation.contradiction_pressure,
        ambiguity_risk=observation.ambiguity_risk,
        reason_codes=reason_codes,
    )


def _row_reason_codes(
    *,
    age_seconds: Decimal,
    cadence_seconds: Decimal,
    source_authority_score: Decimal,
    contradiction_pressure: Decimal,
    ambiguity_risk: Decimal,
    deadline_proximity_seconds: Decimal,
    config: ResearchEventResolutionUpdateLatencyConfig,
) -> tuple[str, ...]:
    reasons: list[str] = []
    if age_seconds >= _watch_latency_seconds(cadence_seconds, config):
        reasons.append("resolution_update_stale")
    if source_authority_score < config.authoritative_source_threshold:
        reasons.append("resolution_update_low_authority")
    if contradiction_pressure >= config.contradiction_watch_threshold:
        reasons.append("resolution_update_contradiction_pressure")
    if ambiguity_risk >= config.ambiguity_watch_threshold:
        reasons.append("resolution_update_ambiguity_risk")
    if deadline_proximity_seconds <= config.deadline_watch_seconds:
        reasons.append("resolution_update_deadline_near")
    if not reasons:
        return ("resolution_update_latency_clear",)
    return _normalize_reason_codes(
        "reason_codes",
        tuple(reasons),
        allowed=ROW_REASON_CODES,
        allow_empty=False,
    )


def _row_status(
    *,
    reason_codes: tuple[str, ...],
    age_seconds: Decimal,
    cadence_seconds: Decimal,
    contradiction_pressure: Decimal,
    ambiguity_risk: Decimal,
    deadline_proximity_seconds: Decimal,
    config: ResearchEventResolutionUpdateLatencyConfig,
) -> str:
    if (
        age_seconds >= _block_latency_seconds(cadence_seconds, config)
        or contradiction_pressure >= config.contradiction_block_threshold
        or ambiguity_risk >= config.ambiguity_block_threshold
        or deadline_proximity_seconds <= config.deadline_block_seconds
    ):
        return "block"
    if reason_codes != ("resolution_update_latency_clear",):
        return "watch"
    return "pass"


def _report_status(rows: tuple[ResearchEventResolutionUpdateLatencyRow, ...]) -> str:
    if any(row.status == "block" for row in rows):
        return "block"
    if any(row.status == "watch" for row in rows):
        return "watch"
    return "pass"


def _report_reason_codes(
    rows: tuple[ResearchEventResolutionUpdateLatencyRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return ("resolution_update_latency_empty",)
    issue_codes = tuple(
        reason_code
        for reason_code in REPORT_REASON_CODES
        if reason_code
        not in (
            "resolution_update_latency_empty",
            "resolution_update_latency_clear",
        )
        and any(reason_code in row.reason_codes for row in rows)
    )
    if issue_codes:
        return issue_codes
    return ("resolution_update_latency_clear",)


def _normalize_observations(
    observations: Iterable[ResearchEventResolutionUpdateLatencyObservation],
) -> tuple[ResearchEventResolutionUpdateLatencyObservation, ...]:
    if isinstance(observations, str | bytes):
        raise ValueError("observations must be an iterable")
    try:
        normalized = tuple(observations)
    except TypeError as exc:
        raise ValueError("observations must be an iterable") from exc
    seen: set[str] = set()
    for observation in normalized:
        if type(observation) is not ResearchEventResolutionUpdateLatencyObservation:
            raise ValueError("observations must contain exact observation values")
        require_paper_only_flags("resolution update latency observation", observation)
        if observation.public_event_key in seen:
            raise ValueError("public_event_key values must be unique")
        seen.add(observation.public_event_key)
    return tuple(
        sorted(
            normalized,
            key=lambda observation: (
                observation.public_event_key,
                observation.last_verified_update_at,
                observation.deadline_at,
            ),
        ),
    )


def _validate_observation_times(
    observations: tuple[ResearchEventResolutionUpdateLatencyObservation, ...],
    generated_at: datetime,
) -> None:
    for observation in observations:
        if observation.last_verified_update_at > generated_at:
            raise ValueError("last_verified_update_at must be <= generated_at")


def _sort_rows(
    rows: tuple[ResearchEventResolutionUpdateLatencyRow, ...],
) -> tuple[ResearchEventResolutionUpdateLatencyRow, ...]:
    return tuple(sorted(rows, key=_row_sort_key))


def _row_sort_key(
    row: ResearchEventResolutionUpdateLatencyRow,
) -> tuple[int, Decimal, Decimal, str]:
    return (
        STATUS_RANK[row.status],
        row.deadline_proximity_seconds,
        -row.last_verified_update_age_seconds,
        row.public_event_key,
    )


def _normalize_rows(
    rows: Iterable[ResearchEventResolutionUpdateLatencyRow],
) -> tuple[ResearchEventResolutionUpdateLatencyRow, ...]:
    if isinstance(rows, str | bytes):
        raise ValueError("rows must be an iterable")
    try:
        normalized = tuple(rows)
    except TypeError as exc:
        raise ValueError("rows must be an iterable") from exc
    seen: set[str] = set()
    for row in normalized:
        if type(row) is not ResearchEventResolutionUpdateLatencyRow:
            raise ValueError("rows must contain exact resolution update latency rows")
        require_paper_only_flags("resolution update latency row", row)
        if row.public_event_key in seen:
            raise ValueError("rows public_event_key values must be unique")
        seen.add(row.public_event_key)
    if normalized != _sort_rows(normalized):
        raise ValueError("rows must use deterministic sorting")
    return normalized


def _validate_row(row: ResearchEventResolutionUpdateLatencyRow) -> None:
    if row.status == "pass" and row.reason_codes != ("resolution_update_latency_clear",):
        raise ValueError("pass rows must have the clear reason code")
    if row.status != "pass" and row.reason_codes == ("resolution_update_latency_clear",):
        raise ValueError("non-pass rows must not have the clear reason code")


def _validate_report(report: ResearchEventResolutionUpdateLatencyReport) -> None:
    if report.event_count != _count(len(report.rows)):
        raise ValueError("event_count must match rows")
    for status in STATUSES:
        field_name = f"{status}_count"
        if getattr(report, field_name) != _status_count(report.rows, status):
            raise ValueError(f"{field_name} must match rows")
    expected_reason_count_fields = {
        "stale_count": "resolution_update_stale",
        "low_authority_count": "resolution_update_low_authority",
        "contradiction_pressure_count": "resolution_update_contradiction_pressure",
        "ambiguity_risk_count": "resolution_update_ambiguity_risk",
        "deadline_pressure_count": "resolution_update_deadline_near",
    }
    for field_name, reason_code in expected_reason_count_fields.items():
        if getattr(report, field_name) != _reason_count(report.rows, reason_code):
            raise ValueError(f"{field_name} must match rows")
    age_values = tuple(row.last_verified_update_age_seconds for row in report.rows)
    if report.max_last_verified_update_age_seconds != max(
        age_values,
        default=ZERO_QUANTIZED,
    ):
        raise ValueError("max_last_verified_update_age_seconds must match rows")
    if report.average_last_verified_update_age_seconds != _average_seconds(age_values):
        raise ValueError("average_last_verified_update_age_seconds must match rows")
    if report.status != _report_status(report.rows):
        raise ValueError("status must match rows")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")


def _status_count(
    rows: tuple[ResearchEventResolutionUpdateLatencyRow, ...],
    status: str,
) -> Decimal:
    return _count(sum(1 for row in rows if row.status == status))


def _reason_count(
    rows: tuple[ResearchEventResolutionUpdateLatencyRow, ...],
    reason_code: str,
) -> Decimal:
    return _count(sum(1 for row in rows if reason_code in row.reason_codes))


def _count(value: int) -> Decimal:
    if type(value) is not int:
        raise ValueError("count value must be an int")
    if value < 0:
        raise ValueError("count value must be nonnegative")
    return Decimal(value).quantize(COUNT_QUANTUM)


def _average_seconds(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return ZERO_QUANTIZED
    with localcontext(DECIMAL_CONTEXT):
        return (sum(values, ZERO_QUANTIZED) / Decimal(len(values))).quantize(QUANTUM)


def _duration_seconds(start: datetime, end: datetime) -> Decimal:
    start_utc = _as_utc("start", start)
    end_utc = _as_utc("end", end)
    delta = end_utc - start_utc
    seconds = (
        Decimal(delta.days) * SECONDS_PER_DAY
        + Decimal(delta.seconds)
        + (Decimal(delta.microseconds) / MICROSECONDS_PER_SECOND)
    )
    if seconds < ZERO_QUANTIZED:
        raise ValueError("duration seconds must be nonnegative")
    return seconds.quantize(QUANTUM)


def _deadline_proximity_seconds(generated_at: datetime, deadline_at: datetime) -> Decimal:
    if deadline_at <= generated_at:
        return ZERO_QUANTIZED
    return _duration_seconds(generated_at, deadline_at)


def _watch_latency_seconds(
    cadence_seconds: Decimal,
    config: ResearchEventResolutionUpdateLatencyConfig,
) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return (cadence_seconds * config.watch_latency_multiplier).quantize(QUANTUM)


def _block_latency_seconds(
    cadence_seconds: Decimal,
    config: ResearchEventResolutionUpdateLatencyConfig,
) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return (cadence_seconds * config.block_latency_multiplier).quantize(QUANTUM)


def _normalize_optional_positive_seconds_decimal(
    field_name: str,
    value: object,
) -> Decimal | None:
    if value is None:
        return None
    return _require_positive_seconds_decimal(field_name, value)


def _require_positive_seconds_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_nonnegative_seconds_decimal(field_name, value)
    if decimal_value <= ZERO_QUANTIZED:
        raise ValueError(f"{field_name} must be positive")
    return decimal_value


def _require_nonnegative_seconds_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    with localcontext(DECIMAL_CONTEXT):
        quantized = decimal_value.quantize(QUANTUM)
    if quantized < ZERO_QUANTIZED:
        raise ValueError(f"{field_name} must be nonnegative")
    return quantized


def _require_positive_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    with localcontext(DECIMAL_CONTEXT):
        quantized = decimal_value.quantize(QUANTUM)
    if quantized <= ZERO_QUANTIZED:
        raise ValueError(f"{field_name} must be positive")
    return quantized


def _require_nonnegative_count_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value < ZERO_COUNT:
        raise ValueError(f"{field_name} must be nonnegative")
    quantized = decimal_value.quantize(COUNT_QUANTUM)
    if decimal_value != quantized:
        raise ValueError(f"{field_name} must be a whole-count Decimal")
    return quantized


def _require_ratio_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    with localcontext(DECIMAL_CONTEXT):
        quantized = decimal_value.quantize(QUANTUM)
    if quantized < ZERO_QUANTIZED or quantized > ONE_QUANTIZED:
        raise ValueError(f"{field_name} must be between zero and one")
    return quantized


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return value


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _normalize_reason_codes(
    field_name: str,
    value: Iterable[str],
    *,
    allowed: tuple[str, ...],
    allow_empty: bool,
) -> tuple[str, ...]:
    if isinstance(value, str | bytes):
        raise ValueError(f"{field_name} must be an iterable")
    try:
        reason_codes = tuple(value)
    except TypeError as exc:
        raise ValueError(f"{field_name} must be an iterable") from exc
    if not allow_empty and not reason_codes:
        raise ValueError(f"{field_name} must not be empty")
    for reason_code in reason_codes:
        _require_public_string(field_name, reason_code)
        if reason_code not in allowed:
            raise ValueError(f"{field_name} must contain known reason codes")
    if len(set(reason_codes)) != len(reason_codes):
        raise ValueError(f"{field_name} must be unique")
    expected = tuple(reason_code for reason_code in allowed if reason_code in reason_codes)
    if reason_codes != expected:
        raise ValueError(f"{field_name} must use deterministic sorting")
    return reason_codes


def _require_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in STATUSES:
        raise ValueError(f"{field_name} must be pass, watch, or block")


def _require_supported_config_version(value: object) -> None:
    _require_public_string("config_version", value)
    if value != DEFAULT_RESEARCH_EVENT_RESOLUTION_UPDATE_LATENCY_REPORT_CONFIG_VERSION:
        raise ValueError("config_version must be the supported config version")


def _require_public_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value:
        raise ValueError(f"{field_name} must not be empty")
    if value.strip() != value:
        raise ValueError(f"{field_name} must be stripped")
    if "\n" in value or "\r" in value or "\t" in value:
        raise ValueError(f"{field_name} must be single line")
    if _has_public_surface_fragment(value):
        raise ValueError(f"{field_name} contains an unsafe public surface")


def _require_sha256_digest(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a lowercase sha256 digest")
    if len(value) != 64 or any(char not in "0123456789abcdef" for char in value):
        raise ValueError(f"{field_name} must be a lowercase sha256 digest")


def _require_exact_type(value: object, expected_type: type[object], label: str) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{label} must be exactly {expected_type.__name__}")


def _reject_public_payload(label: str, value: object) -> None:
    if is_dataclass(value) and not isinstance(value, type):
        _reject_public_payload(label, asdict(value))
        return
    if isinstance(value, Mapping):
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            if _has_public_surface_fragment(key):
                raise ValueError(f"unsafe public surface field in {label}")
            _reject_public_payload(label, item)
        return
    if isinstance(value, (list, tuple)):
        for item in value:
            _reject_public_payload(label, item)
        return
    if type(value) is str and _has_public_surface_fragment(value):
        raise ValueError(f"unsafe public surface value in {label}")


def _has_public_surface_fragment(value: str) -> bool:
    normalized = value.lower()
    return any(fragment in normalized for fragment in PUBLIC_SURFACE_FRAGMENTS)


def _report_values_without_digest(
    report: ResearchEventResolutionUpdateLatencyReport,
) -> dict[str, object]:
    values = asdict(report)
    values.pop("derived_validation_digest", None)
    return values


def _report_digest_from_values(values: Mapping[str, object]) -> str:
    payload = json_ready_no_floats(values)
    if type(payload) is not dict:
        raise ValueError("digest payload must be a JSON object")
    _reject_public_payload("digest payload", payload)
    canonical = json.dumps(
        payload,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


__all__ = (
    "DEFAULT_RESEARCH_EVENT_RESOLUTION_UPDATE_LATENCY_REPORT_CONFIG_VERSION",
    "ResearchEventResolutionUpdateLatencyConfig",
    "ResearchEventResolutionUpdateLatencyObservation",
    "ResearchEventResolutionUpdateLatencyReport",
    "ResearchEventResolutionUpdateLatencyRow",
    "build_research_event_resolution_update_latency_report",
    "research_event_resolution_update_latency_report_to_payload",
)
