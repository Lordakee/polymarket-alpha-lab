"""Pure public-safe information half-life report by event domain.

Callers provide aggregate domain signals. The module returns deterministic,
report-only estimates and status reason codes without side effects.
"""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable
from dataclasses import dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation
from hashlib import sha256
import json
from typing import Any


__all__ = (
    "ResearchEventInformationHalfLifeConfig",
    "ResearchEventInformationHalfLifeDomainSignal",
    "ResearchEventInformationHalfLifeReasonCodeCount",
    "ResearchEventInformationHalfLifeReport",
    "ResearchEventInformationHalfLifeRow",
    "build_research_event_information_half_life_report",
    "research_event_information_half_life_report_digest",
    "research_event_information_half_life_report_payload",
)


DEFAULT_CONFIG_VERSION = "research-event-information-half-life-v0"
STATUSES = ("pass", "watch", "block")
ZERO = Decimal("0")
ONE = Decimal("1")
RATIO_QUANTUM = Decimal("0.000001")
DEFAULT_PASS_HALF_LIFE_SECONDS = Decimal("14400")
DEFAULT_WATCH_HALF_LIFE_SECONDS = Decimal("3600")


class _Missing:
    pass


_MISSING = _Missing()


@dataclass(frozen=True)
class ResearchEventInformationHalfLifeConfig:
    config_version: str = DEFAULT_CONFIG_VERSION
    pass_half_life_seconds: Decimal = DEFAULT_PASS_HALF_LIFE_SECONDS
    watch_half_life_seconds: Decimal = DEFAULT_WATCH_HALF_LIFE_SECONDS
    min_domain_observation_count: Decimal = Decimal("3")
    source_update_weight: Decimal = Decimal("0.350000")
    catalyst_frequency_weight: Decimal = Decimal("0.250000")
    contradiction_decay_weight: Decimal = Decimal("0.250000")
    resolution_proximity_weight: Decimal = Decimal("0.150000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchEventInformationHalfLifeConfig:
            raise TypeError(
                "ResearchEventInformationHalfLifeConfig does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchEventInformationHalfLifeConfig:
            raise ValueError("config must be exactly ResearchEventInformationHalfLifeConfig")
        _require_canonical_string("config_version", self.config_version)
        object.__setattr__(
            self,
            "pass_half_life_seconds",
            _require_positive_decimal(
                "pass_half_life_seconds",
                self.pass_half_life_seconds,
            ),
        )
        object.__setattr__(
            self,
            "watch_half_life_seconds",
            _require_positive_decimal(
                "watch_half_life_seconds",
                self.watch_half_life_seconds,
            ),
        )
        if self.pass_half_life_seconds <= self.watch_half_life_seconds:
            raise ValueError(
                "pass_half_life_seconds must be greater than watch_half_life_seconds",
            )
        object.__setattr__(
            self,
            "min_domain_observation_count",
            _require_positive_whole_decimal(
                "min_domain_observation_count",
                self.min_domain_observation_count,
            ),
        )
        for field_name in (
            "source_update_weight",
            "catalyst_frequency_weight",
            "contradiction_decay_weight",
            "resolution_proximity_weight",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_probability_decimal(field_name, getattr(self, field_name)),
            )
        weight_sum = _quantize(
            self.source_update_weight
            + self.catalyst_frequency_weight
            + self.contradiction_decay_weight
            + self.resolution_proximity_weight,
        )
        if weight_sum != ONE:
            raise ValueError(
                "source_update_weight, catalyst_frequency_weight, "
                "contradiction_decay_weight, and resolution_proximity_weight "
                "must sum to 1",
            )
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class ResearchEventInformationHalfLifeDomainSignal:
    event_domain: str
    aggregate_source_update_cadence_seconds: Decimal
    aggregate_catalyst_frequency_seconds: Decimal
    aggregate_contradiction_decay_seconds: Decimal
    resolution_proximity_seconds: Decimal
    domain_observation_count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchEventInformationHalfLifeDomainSignal:
            raise TypeError(
                "ResearchEventInformationHalfLifeDomainSignal does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchEventInformationHalfLifeDomainSignal:
            raise ValueError(
                "signal must be exactly ResearchEventInformationHalfLifeDomainSignal",
            )
        _require_domain_label("event_domain", self.event_domain)
        for field_name in (
            "aggregate_source_update_cadence_seconds",
            "aggregate_catalyst_frequency_seconds",
            "aggregate_contradiction_decay_seconds",
            "resolution_proximity_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_positive_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "domain_observation_count",
            _require_nonnegative_whole_decimal(
                "domain_observation_count",
                self.domain_observation_count,
            ),
        )
        _require_hard_flags("signal", self)


@dataclass(frozen=True)
class ResearchEventInformationHalfLifeRow:
    event_domain: str
    aggregate_source_update_cadence_seconds: Decimal
    aggregate_catalyst_frequency_seconds: Decimal
    aggregate_contradiction_decay_seconds: Decimal
    resolution_proximity_seconds: Decimal
    domain_observation_count: Decimal
    source_update_component_seconds: Decimal
    catalyst_frequency_component_seconds: Decimal
    contradiction_decay_component_seconds: Decimal
    resolution_proximity_component_seconds: Decimal
    estimated_half_life_seconds: Decimal
    status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchEventInformationHalfLifeRow:
            raise TypeError(
                "ResearchEventInformationHalfLifeRow does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchEventInformationHalfLifeRow:
            raise ValueError("row must be exactly ResearchEventInformationHalfLifeRow")
        _require_domain_label("event_domain", self.event_domain)
        for field_name in (
            "aggregate_source_update_cadence_seconds",
            "aggregate_catalyst_frequency_seconds",
            "aggregate_contradiction_decay_seconds",
            "resolution_proximity_seconds",
            "source_update_component_seconds",
            "catalyst_frequency_component_seconds",
            "contradiction_decay_component_seconds",
            "resolution_proximity_component_seconds",
            "estimated_half_life_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_positive_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "domain_observation_count",
            _require_nonnegative_whole_decimal(
                "domain_observation_count",
                self.domain_observation_count,
            ),
        )
        _require_status("status", self.status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, allow_empty=False),
        )
        _require_hard_flags("row", self)
        _validate_row_consistency(self)


@dataclass(frozen=True)
class ResearchEventInformationHalfLifeReasonCodeCount:
    reason_code: str
    count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchEventInformationHalfLifeReasonCodeCount:
            raise TypeError(
                "ResearchEventInformationHalfLifeReasonCodeCount does not support "
                "subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchEventInformationHalfLifeReasonCodeCount:
            raise ValueError(
                "reason_code_count must be exactly "
                "ResearchEventInformationHalfLifeReasonCodeCount",
            )
        _require_reason_code("reason_code", self.reason_code)
        object.__setattr__(
            self,
            "count",
            _require_positive_whole_decimal("count", self.count),
        )
        _require_hard_flags("reason_code_count", self)


@dataclass(frozen=True)
class ResearchEventInformationHalfLifeReport:
    generated_at: datetime
    config_version: str
    domain_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    average_estimated_half_life_seconds: Decimal | None
    status: str
    rows: tuple[ResearchEventInformationHalfLifeRow, ...]
    reason_code_counts: tuple[ResearchEventInformationHalfLifeReasonCodeCount, ...]
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchEventInformationHalfLifeReport:
            raise TypeError(
                "ResearchEventInformationHalfLifeReport does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchEventInformationHalfLifeReport:
            raise ValueError("report must be exactly ResearchEventInformationHalfLifeReport")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        for field_name in ("domain_count", "pass_count", "watch_count", "block_count"):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_whole_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "average_estimated_half_life_seconds",
            _require_optional_positive_decimal(
                "average_estimated_half_life_seconds",
                self.average_estimated_half_life_seconds,
            ),
        )
        _require_status("status", self.status)
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, allow_empty=False),
        )
        _require_hard_flags("report", self)
        _validate_report_consistency(self)


def build_research_event_information_half_life_report(
    domain_signals: Iterable[object],
    *,
    config: ResearchEventInformationHalfLifeConfig,
    generated_at: datetime,
) -> ResearchEventInformationHalfLifeReport:
    if type(config) is not ResearchEventInformationHalfLifeConfig:
        raise ValueError("config must be a ResearchEventInformationHalfLifeConfig")
    _require_hard_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    signal_items = _normalize_domain_signals(domain_signals)
    rows = tuple(
        _row_from_signal(signal, config=config)
        for signal in sorted(signal_items, key=lambda item: item.event_domain)
    )
    reason_codes = _summary_reason_codes(rows)
    return ResearchEventInformationHalfLifeReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        domain_count=_decimal_count(len(rows)),
        pass_count=_decimal_count(_status_count(rows, "pass")),
        watch_count=_decimal_count(_status_count(rows, "watch")),
        block_count=_decimal_count(_status_count(rows, "block")),
        average_estimated_half_life_seconds=_average_estimated_half_life_seconds(rows),
        status=_summary_status(reason_codes),
        rows=rows,
        reason_code_counts=_reason_code_counts(rows, reason_codes),
        reason_codes=reason_codes,
    )


def research_event_information_half_life_report_payload(
    report: ResearchEventInformationHalfLifeReport,
) -> dict[str, Any]:
    if type(report) is not ResearchEventInformationHalfLifeReport:
        raise ValueError("report must be a ResearchEventInformationHalfLifeReport")
    _require_hard_flags("report", report)
    payload = _payload_value(report)
    if not isinstance(payload, dict):
        raise ValueError("report payload must be a JSON object")
    return payload


def research_event_information_half_life_report_digest(
    report: ResearchEventInformationHalfLifeReport,
) -> str:
    payload = research_event_information_half_life_report_payload(report)
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return sha256(encoded.encode("utf-8")).hexdigest()


def _row_from_signal(
    signal: ResearchEventInformationHalfLifeDomainSignal,
    *,
    config: ResearchEventInformationHalfLifeConfig,
) -> ResearchEventInformationHalfLifeRow:
    source_update_component = _quantize(
        signal.aggregate_source_update_cadence_seconds * config.source_update_weight,
    )
    catalyst_frequency_component = _quantize(
        signal.aggregate_catalyst_frequency_seconds * config.catalyst_frequency_weight,
    )
    contradiction_decay_component = _quantize(
        signal.aggregate_contradiction_decay_seconds * config.contradiction_decay_weight,
    )
    resolution_proximity_component = _quantize(
        signal.resolution_proximity_seconds * config.resolution_proximity_weight,
    )
    estimated_half_life = _quantize(
        source_update_component
        + catalyst_frequency_component
        + contradiction_decay_component
        + resolution_proximity_component,
    )
    status = _row_status(
        estimated_half_life_seconds=estimated_half_life,
        domain_observation_count=signal.domain_observation_count,
        config=config,
    )
    return ResearchEventInformationHalfLifeRow(
        event_domain=signal.event_domain,
        aggregate_source_update_cadence_seconds=signal.aggregate_source_update_cadence_seconds,
        aggregate_catalyst_frequency_seconds=signal.aggregate_catalyst_frequency_seconds,
        aggregate_contradiction_decay_seconds=signal.aggregate_contradiction_decay_seconds,
        resolution_proximity_seconds=signal.resolution_proximity_seconds,
        domain_observation_count=signal.domain_observation_count,
        source_update_component_seconds=source_update_component,
        catalyst_frequency_component_seconds=catalyst_frequency_component,
        contradiction_decay_component_seconds=contradiction_decay_component,
        resolution_proximity_component_seconds=resolution_proximity_component,
        estimated_half_life_seconds=estimated_half_life,
        status=status,
        reason_codes=_row_reason_codes(
            status=status,
            estimated_half_life_seconds=estimated_half_life,
            resolution_proximity_seconds=signal.resolution_proximity_seconds,
            domain_observation_count=signal.domain_observation_count,
            config=config,
        ),
    )


def _normalize_domain_signals(
    domain_signals: Iterable[object],
) -> tuple[ResearchEventInformationHalfLifeDomainSignal, ...]:
    if isinstance(domain_signals, (str, bytes)):
        raise ValueError("domain_signals must be an iterable")
    try:
        values = tuple(domain_signals)
    except TypeError as exc:
        raise ValueError("domain_signals must be an iterable") from exc
    return tuple(_coerce_domain_signal(value) for value in values)


def _coerce_domain_signal(value: object) -> ResearchEventInformationHalfLifeDomainSignal:
    if type(value) is ResearchEventInformationHalfLifeDomainSignal:
        _require_hard_flags("signal", value)
        return value
    _require_hard_flags("signal", value)
    return ResearchEventInformationHalfLifeDomainSignal(
        event_domain=_field_value(value, "event_domain"),
        aggregate_source_update_cadence_seconds=_field_value(
            value,
            "aggregate_source_update_cadence_seconds",
        ),
        aggregate_catalyst_frequency_seconds=_field_value(
            value,
            "aggregate_catalyst_frequency_seconds",
        ),
        aggregate_contradiction_decay_seconds=_field_value(
            value,
            "aggregate_contradiction_decay_seconds",
        ),
        resolution_proximity_seconds=_field_value(value, "resolution_proximity_seconds"),
        domain_observation_count=_field_value(value, "domain_observation_count"),
        paper_only=_field_value(value, "paper_only"),
        report_only=_field_value(value, "report_only"),
        readonly=_field_value(value, "readonly"),
    )


def _row_status(
    *,
    estimated_half_life_seconds: Decimal,
    domain_observation_count: Decimal,
    config: ResearchEventInformationHalfLifeConfig,
) -> str:
    if estimated_half_life_seconds < config.watch_half_life_seconds:
        return "block"
    if estimated_half_life_seconds < config.pass_half_life_seconds:
        return "watch"
    if domain_observation_count < config.min_domain_observation_count:
        return "watch"
    return "pass"


def _row_reason_codes(
    *,
    status: str,
    estimated_half_life_seconds: Decimal,
    resolution_proximity_seconds: Decimal,
    domain_observation_count: Decimal,
    config: ResearchEventInformationHalfLifeConfig,
) -> tuple[str, ...]:
    reason_codes = {f"event_information_half_life_{status}"}
    if estimated_half_life_seconds >= config.pass_half_life_seconds:
        reason_codes.add("long_public_information_half_life")
    elif estimated_half_life_seconds >= config.watch_half_life_seconds:
        reason_codes.add("medium_public_information_half_life")
    else:
        reason_codes.add("short_public_information_half_life")
    reason_codes.add(
        "resolution_buffer_present"
        if resolution_proximity_seconds > config.watch_half_life_seconds
        else "near_resolution",
    )
    reason_codes.add(
        "sufficient_domain_observations"
        if domain_observation_count >= config.min_domain_observation_count
        else "insufficient_domain_observations",
    )
    return tuple(sorted(reason_codes))


def _summary_reason_codes(
    rows: tuple[ResearchEventInformationHalfLifeRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return ("no_event_domain_signals",)
    if all(row.status == "pass" for row in rows):
        return ("event_information_half_life_pass",)
    return tuple(sorted({reason_code for row in rows for reason_code in row.reason_codes}))


def _summary_status(reason_codes: tuple[str, ...]) -> str:
    if reason_codes == ("no_event_domain_signals",):
        return "block"
    if "event_information_half_life_block" in reason_codes:
        return "block"
    if "event_information_half_life_watch" in reason_codes:
        return "watch"
    return "pass"


def _reason_code_counts(
    rows: tuple[ResearchEventInformationHalfLifeRow, ...],
    reason_codes: tuple[str, ...],
) -> tuple[ResearchEventInformationHalfLifeReasonCodeCount, ...]:
    if not rows:
        return (
            ResearchEventInformationHalfLifeReasonCodeCount(
                reason_code=reason_codes[0],
                count=ONE,
            ),
        )
    counts: Counter[str] = Counter()
    for row in rows:
        counts.update(row.reason_codes)
    return tuple(
        ResearchEventInformationHalfLifeReasonCodeCount(
            reason_code=reason_code,
            count=_decimal_count(count),
        )
        for reason_code, count in sorted(counts.items(), key=lambda item: item[0])
    )


def _average_estimated_half_life_seconds(
    rows: tuple[ResearchEventInformationHalfLifeRow, ...],
) -> Decimal | None:
    if not rows:
        return None
    return _quantize(
        sum((row.estimated_half_life_seconds for row in rows), ZERO) / Decimal(len(rows)),
    )


def _status_count(rows: tuple[ResearchEventInformationHalfLifeRow, ...], status: str) -> int:
    return sum(1 for row in rows if row.status == status)


def _normalize_rows(
    rows: tuple[ResearchEventInformationHalfLifeRow, ...],
) -> tuple[ResearchEventInformationHalfLifeRow, ...]:
    if type(rows) is not tuple:
        raise ValueError("rows must be a tuple")
    for row in rows:
        if type(row) is not ResearchEventInformationHalfLifeRow:
            raise ValueError("rows must contain ResearchEventInformationHalfLifeRow values")
        _require_hard_flags("row", row)
    sorted_rows = tuple(sorted(rows, key=lambda row: row.event_domain))
    if rows != sorted_rows:
        raise ValueError("rows must be sorted by event_domain")
    return rows


def _normalize_reason_code_counts(
    counts: tuple[ResearchEventInformationHalfLifeReasonCodeCount, ...],
) -> tuple[ResearchEventInformationHalfLifeReasonCodeCount, ...]:
    if type(counts) is not tuple:
        raise ValueError("reason_code_counts must be a tuple")
    for count in counts:
        if type(count) is not ResearchEventInformationHalfLifeReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "ResearchEventInformationHalfLifeReasonCodeCount values",
            )
        _require_hard_flags("reason_code_count", count)
    sorted_counts = tuple(sorted(counts, key=lambda count: count.reason_code))
    if counts != sorted_counts:
        raise ValueError("reason_code_counts must be sorted by reason_code")
    return counts


def _validate_row_consistency(row: ResearchEventInformationHalfLifeRow) -> None:
    component_sum = _quantize(
        row.source_update_component_seconds
        + row.catalyst_frequency_component_seconds
        + row.contradiction_decay_component_seconds
        + row.resolution_proximity_component_seconds,
    )
    if row.estimated_half_life_seconds != component_sum:
        raise ValueError("estimated_half_life_seconds must match components")
    if f"event_information_half_life_{row.status}" not in row.reason_codes:
        raise ValueError("reason_codes must include status")


def _validate_report_consistency(report: ResearchEventInformationHalfLifeReport) -> None:
    if report.domain_count != _decimal_count(len(report.rows)):
        raise ValueError("domain_count must match rows")
    if report.pass_count != _decimal_count(_status_count(report.rows, "pass")):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _decimal_count(_status_count(report.rows, "watch")):
        raise ValueError("watch_count must match rows")
    if report.block_count != _decimal_count(_status_count(report.rows, "block")):
        raise ValueError("block_count must match rows")
    if (
        report.average_estimated_half_life_seconds
        != _average_estimated_half_life_seconds(report.rows)
    ):
        raise ValueError("average_estimated_half_life_seconds must match rows")
    if report.reason_codes != _summary_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")
    if report.status != _summary_status(report.reason_codes):
        raise ValueError("status must match reason_codes")


def _field_value(value: object, field_name: str, *, default: object = _MISSING) -> object:
    if is_dataclass(value):
        for field in fields(value):
            if field.name == field_name:
                return getattr(value, field_name)
    if hasattr(value, field_name):
        return getattr(value, field_name)
    if default is not _MISSING:
        return default
    raise ValueError(f"{field_name} is required")


def _payload_value(value: object) -> object:
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, datetime):
        return value.isoformat()
    if is_dataclass(value) and not isinstance(value, type):
        return {field.name: _payload_value(getattr(value, field.name)) for field in fields(value)}
    if isinstance(value, tuple):
        return [_payload_value(item) for item in value]
    if isinstance(value, list):
        return [_payload_value(item) for item in value]
    if isinstance(value, dict):
        return {
            str(key): _payload_value(value[key])
            for key in sorted(value, key=lambda item: str(item))
        }
    return value


def _as_utc(field_name: str, value: datetime) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    try:
        return +value
    except InvalidOperation as exc:
        raise ValueError(f"{field_name} must be finite") from exc


def _require_positive_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _require_optional_positive_decimal(field_name: str, value: object) -> Decimal | None:
    if value is None:
        return None
    return _require_positive_decimal(field_name, value)


def _require_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _require_probability_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < ZERO or normalized > ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return _quantize(normalized)


def _require_positive_whole_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_positive_decimal(field_name, value)
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{field_name} must be a whole count")
    return normalized


def _require_nonnegative_whole_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_nonnegative_decimal(field_name, value)
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{field_name} must be a whole count")
    return normalized


def _decimal_count(value: int) -> Decimal:
    if type(value) is not int:
        raise ValueError("count value must be an int")
    if value < 0:
        raise ValueError("count value must be nonnegative")
    return Decimal(value)


def _quantize(value: Decimal) -> Decimal:
    return value.quantize(RATIO_QUANTUM)


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str or not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a nonempty canonical string")


def _require_domain_label(field_name: str, value: object) -> None:
    _require_canonical_string(field_name, value)
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a domain label")
    allowed = set("abcdefghijklmnopqrstuvwxyz-")
    if (
        value != value.lower()
        or any(character not in allowed for character in value)
        or value.startswith("-")
        or value.endswith("-")
        or "--" in value
    ):
        raise ValueError(f"{field_name} must be a public domain label")


def _require_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in STATUSES:
        raise ValueError(f"{field_name} must be one of {STATUSES}")


def _normalize_reason_codes(
    field_name: str,
    values: object,
    *,
    allow_empty: bool,
) -> tuple[str, ...]:
    if type(values) is not tuple:
        raise ValueError(f"{field_name} must be a tuple")
    normalized: list[str] = []
    for value in values:
        _require_reason_code(field_name, value)
        normalized.append(value)
    if not allow_empty and not normalized:
        raise ValueError(f"{field_name} must be nonempty")
    return tuple(sorted(set(normalized)))


def _require_reason_code(field_name: str, value: object) -> None:
    _require_canonical_string(field_name, value)
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a reason code")
    if value != value.lower() or any(
        character not in "abcdefghijklmnopqrstuvwxyz_0123456789" for character in value
    ):
        raise ValueError(f"{field_name} must contain lowercase reason codes")


def _require_hard_flags(label: str, value: object) -> None:
    for flag_name in ("paper_only", "report_only", "readonly"):
        if not hasattr(value, flag_name):
            raise ValueError(f"{label}.{flag_name} is required")
        if getattr(value, flag_name) is not True:
            raise ValueError(f"{label}.{flag_name} must be True")
