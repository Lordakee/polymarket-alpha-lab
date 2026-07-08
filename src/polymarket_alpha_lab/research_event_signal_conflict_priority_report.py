from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any, Iterable


DEFAULT_CONFIG_VERSION = "research_event_signal_conflict_priority_report_v1"
STATUSES = ("pass", "watch", "block")

ZERO = Decimal("0")
ONE = Decimal("1")
COUNT_QUANTUM = Decimal("1")
RATIO_QUANTUM = Decimal("0.000001")


@dataclass(frozen=True)
class ResearchEventSignalConflictPriorityConfig:
    config_version: str = DEFAULT_CONFIG_VERSION
    watch_priority_score: Decimal = Decimal("0.345000")
    block_priority_score: Decimal = Decimal("0.750000")
    contradiction_pressure_weight: Decimal = Decimal("0.300000")
    stale_evidence_weight: Decimal = Decimal("0.200000")
    weak_source_reliability_weight: Decimal = Decimal("0.250000")
    catalyst_pressure_weight: Decimal = Decimal("0.150000")
    team_confidence_dispersion_weight: Decimal = Decimal("0.100000")
    contradiction_pressure_watch: Decimal = Decimal("0.400000")
    evidence_freshness_stale: Decimal = Decimal("0.300000")
    source_reliability_weak: Decimal = Decimal("0.500000")
    catalyst_pressure_watch: Decimal = Decimal("0.500000")
    team_confidence_dispersion_watch: Decimal = Decimal("0.300000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not ResearchEventSignalConflictPriorityConfig:
            raise TypeError(
                "ResearchEventSignalConflictPriorityConfig does not support subclassing",
            )
        _require_canonical_string("config_version", self.config_version)
        if self.config_version != DEFAULT_CONFIG_VERSION:
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "watch_priority_score",
            "block_priority_score",
            "contradiction_pressure_weight",
            "stale_evidence_weight",
            "weak_source_reliability_weight",
            "catalyst_pressure_weight",
            "team_confidence_dispersion_weight",
            "contradiction_pressure_watch",
            "evidence_freshness_stale",
            "source_reliability_weak",
            "catalyst_pressure_watch",
            "team_confidence_dispersion_watch",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_probability_decimal(field_name, getattr(self, field_name)),
            )
        if self.block_priority_score <= self.watch_priority_score:
            raise ValueError("block_priority_score must be greater than watch_priority_score")
        weight_total = _quantize_ratio(
            "weight_total",
            self.contradiction_pressure_weight
            + self.stale_evidence_weight
            + self.weak_source_reliability_weight
            + self.catalyst_pressure_weight
            + self.team_confidence_dispersion_weight,
        )
        if weight_total != ONE:
            raise ValueError("priority component weights must sum to 1")
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class ResearchEventSignalConflictPriorityObservation:
    event_domain: str
    contradiction_pressure: Decimal
    evidence_freshness: Decimal
    source_reliability: Decimal
    catalyst_pressure: Decimal
    team_confidence_dispersion: Decimal
    observed_at: datetime
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not ResearchEventSignalConflictPriorityObservation:
            raise TypeError(
                "ResearchEventSignalConflictPriorityObservation "
                "does not support subclassing",
            )
        _require_canonical_string("event_domain", self.event_domain)
        for field_name in (
            "contradiction_pressure",
            "evidence_freshness",
            "source_reliability",
            "catalyst_pressure",
            "team_confidence_dispersion",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_probability_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        _require_hard_flags("observation", self)


@dataclass(frozen=True)
class ResearchEventSignalConflictPriorityRow:
    event_domain: str
    observation_count: Decimal
    aggregate_contradiction_pressure: Decimal
    evidence_freshness: Decimal
    source_reliability: Decimal
    catalyst_pressure: Decimal
    team_confidence_dispersion: Decimal
    stale_evidence_pressure: Decimal
    weak_source_reliability_pressure: Decimal
    priority_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    first_observed_at: datetime
    last_observed_at: datetime
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not ResearchEventSignalConflictPriorityRow:
            raise TypeError(
                "ResearchEventSignalConflictPriorityRow does not support subclassing",
            )
        _require_canonical_string("event_domain", self.event_domain)
        object.__setattr__(
            self,
            "observation_count",
            _require_positive_whole_decimal("observation_count", self.observation_count),
        )
        for field_name in (
            "aggregate_contradiction_pressure",
            "evidence_freshness",
            "source_reliability",
            "catalyst_pressure",
            "team_confidence_dispersion",
            "stale_evidence_pressure",
            "weak_source_reliability_pressure",
            "priority_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_probability_decimal(field_name, getattr(self, field_name)),
            )
        _require_status("status", self.status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, allow_empty=False),
        )
        object.__setattr__(
            self,
            "first_observed_at",
            _as_utc("first_observed_at", self.first_observed_at),
        )
        object.__setattr__(
            self,
            "last_observed_at",
            _as_utc("last_observed_at", self.last_observed_at),
        )
        if self.first_observed_at > self.last_observed_at:
            raise ValueError("first_observed_at must be at or before last_observed_at")
        _require_hard_flags("row", self)


@dataclass(frozen=True)
class ResearchEventSignalConflictPriorityReasonCodeCount:
    reason_code: str
    count: Decimal

    def __post_init__(self) -> None:
        if type(self) is not ResearchEventSignalConflictPriorityReasonCodeCount:
            raise TypeError(
                "ResearchEventSignalConflictPriorityReasonCodeCount "
                "does not support subclassing",
            )
        _require_canonical_string("reason_code", self.reason_code)
        object.__setattr__(
            self,
            "count",
            _require_nonnegative_whole_decimal("count", self.count),
        )


@dataclass(frozen=True)
class ResearchEventSignalConflictPriorityReport:
    generated_at: datetime
    config_version: str
    domain_count: Decimal
    observation_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    max_priority_score: Decimal | None
    average_priority_score: Decimal | None
    watch_priority_score: Decimal
    block_priority_score: Decimal
    status: str
    rows: tuple[ResearchEventSignalConflictPriorityRow, ...]
    reason_code_counts: tuple[ResearchEventSignalConflictPriorityReasonCodeCount, ...]
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not ResearchEventSignalConflictPriorityReport:
            raise TypeError(
                "ResearchEventSignalConflictPriorityReport does not support subclassing",
            )
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        for field_name in (
            "domain_count",
            "observation_count",
            "pass_count",
            "watch_count",
            "block_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_whole_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in ("max_priority_score", "average_priority_score"):
            object.__setattr__(
                self,
                field_name,
                _require_optional_probability_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in ("watch_priority_score", "block_priority_score"):
            object.__setattr__(
                self,
                field_name,
                _require_probability_decimal(field_name, getattr(self, field_name)),
            )
        if self.block_priority_score <= self.watch_priority_score:
            raise ValueError("block_priority_score must be greater than watch_priority_score")
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


def build_research_event_signal_conflict_priority_report(
    observations: Iterable[ResearchEventSignalConflictPriorityObservation],
    *,
    generated_at: datetime,
    config: ResearchEventSignalConflictPriorityConfig
    | None = None,
) -> ResearchEventSignalConflictPriorityReport:
    selected_config = config or ResearchEventSignalConflictPriorityConfig()
    if type(selected_config) is not ResearchEventSignalConflictPriorityConfig:
        raise ValueError("config must be a ResearchEventSignalConflictPriorityConfig")
    _require_hard_flags("config", selected_config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    normalized_observations = _normalize_observations(observations)
    for observation in normalized_observations:
        if observation.observed_at > generated_at_utc:
            raise ValueError("observed_at cannot be in the future")

    grouped: dict[str, list[ResearchEventSignalConflictPriorityObservation]] = {}
    for observation in normalized_observations:
        grouped.setdefault(observation.event_domain, []).append(observation)

    rows = tuple(
        _row_from_observations(
            event_domain=event_domain,
            observations=tuple(grouped[event_domain]),
            config=selected_config,
        )
        for event_domain in sorted(grouped)
    )
    normalized_rows = _normalize_rows(rows)
    reason_codes = _summary_reason_codes(normalized_rows)

    return ResearchEventSignalConflictPriorityReport(
        generated_at=generated_at_utc,
        config_version=selected_config.config_version,
        domain_count=_decimal_count(len(normalized_rows)),
        observation_count=sum((row.observation_count for row in normalized_rows), ZERO),
        pass_count=_decimal_count(_status_count(normalized_rows, "pass")),
        watch_count=_decimal_count(_status_count(normalized_rows, "watch")),
        block_count=_decimal_count(_status_count(normalized_rows, "block")),
        max_priority_score=_max_priority_score(normalized_rows),
        average_priority_score=_average_priority_score(normalized_rows),
        watch_priority_score=selected_config.watch_priority_score,
        block_priority_score=selected_config.block_priority_score,
        status=_summary_status(normalized_rows),
        rows=normalized_rows,
        reason_code_counts=_reason_code_counts(normalized_rows, reason_codes),
        reason_codes=reason_codes,
    )


def research_event_signal_conflict_priority_report_payload(
    report: ResearchEventSignalConflictPriorityReport,
) -> dict[str, Any]:
    if type(report) is not ResearchEventSignalConflictPriorityReport:
        raise ValueError("report must be a ResearchEventSignalConflictPriorityReport")
    _require_hard_flags("report", report)
    payload = _payload_value(report)
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    return payload


def research_event_signal_conflict_priority_report_digest(
    report: ResearchEventSignalConflictPriorityReport,
) -> str:
    payload = research_event_signal_conflict_priority_report_payload(report)
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(encoded).hexdigest()


def _row_from_observations(
    *,
    event_domain: str,
    observations: tuple[ResearchEventSignalConflictPriorityObservation, ...],
    config: ResearchEventSignalConflictPriorityConfig,
) -> ResearchEventSignalConflictPriorityRow:
    if not observations:
        raise ValueError("observations must not be empty")
    aggregate_contradiction_pressure = _average_decimal(
        observation.contradiction_pressure for observation in observations
    )
    evidence_freshness = _average_decimal(
        observation.evidence_freshness for observation in observations
    )
    source_reliability = _average_decimal(
        observation.source_reliability for observation in observations
    )
    catalyst_pressure = _average_decimal(
        observation.catalyst_pressure for observation in observations
    )
    team_confidence_dispersion = _average_decimal(
        observation.team_confidence_dispersion for observation in observations
    )
    stale_evidence_pressure = _quantize_ratio(
        "stale_evidence_pressure",
        ONE - evidence_freshness,
    )
    weak_source_reliability_pressure = _quantize_ratio(
        "weak_source_reliability_pressure",
        ONE - source_reliability,
    )
    priority_score = _priority_score(
        config=config,
        aggregate_contradiction_pressure=aggregate_contradiction_pressure,
        stale_evidence_pressure=stale_evidence_pressure,
        weak_source_reliability_pressure=weak_source_reliability_pressure,
        catalyst_pressure=catalyst_pressure,
        team_confidence_dispersion=team_confidence_dispersion,
    )
    status = _row_status(priority_score, config=config)
    reason_codes = _row_reason_codes(
        status=status,
        aggregate_contradiction_pressure=aggregate_contradiction_pressure,
        evidence_freshness=evidence_freshness,
        source_reliability=source_reliability,
        catalyst_pressure=catalyst_pressure,
        team_confidence_dispersion=team_confidence_dispersion,
        config=config,
    )
    observed_values = tuple(observation.observed_at for observation in observations)
    return ResearchEventSignalConflictPriorityRow(
        event_domain=event_domain,
        observation_count=_decimal_count(len(observations)),
        aggregate_contradiction_pressure=aggregate_contradiction_pressure,
        evidence_freshness=evidence_freshness,
        source_reliability=source_reliability,
        catalyst_pressure=catalyst_pressure,
        team_confidence_dispersion=team_confidence_dispersion,
        stale_evidence_pressure=stale_evidence_pressure,
        weak_source_reliability_pressure=weak_source_reliability_pressure,
        priority_score=priority_score,
        status=status,
        reason_codes=reason_codes,
        first_observed_at=min(observed_values),
        last_observed_at=max(observed_values),
    )


def _priority_score(
    *,
    config: ResearchEventSignalConflictPriorityConfig,
    aggregate_contradiction_pressure: Decimal,
    stale_evidence_pressure: Decimal,
    weak_source_reliability_pressure: Decimal,
    catalyst_pressure: Decimal,
    team_confidence_dispersion: Decimal,
) -> Decimal:
    return _quantize_ratio(
        "priority_score",
        aggregate_contradiction_pressure * config.contradiction_pressure_weight
        + stale_evidence_pressure * config.stale_evidence_weight
        + weak_source_reliability_pressure * config.weak_source_reliability_weight
        + catalyst_pressure * config.catalyst_pressure_weight
        + team_confidence_dispersion * config.team_confidence_dispersion_weight,
    )


def _row_status(
    priority_score: Decimal,
    *,
    config: ResearchEventSignalConflictPriorityConfig,
) -> str:
    if priority_score >= config.block_priority_score:
        return "block"
    if priority_score >= config.watch_priority_score:
        return "watch"
    return "pass"


def _row_reason_codes(
    *,
    status: str,
    aggregate_contradiction_pressure: Decimal,
    evidence_freshness: Decimal,
    source_reliability: Decimal,
    catalyst_pressure: Decimal,
    team_confidence_dispersion: Decimal,
    config: ResearchEventSignalConflictPriorityConfig,
) -> tuple[str, ...]:
    reason_codes = [f"priority_score_{status}"]
    if aggregate_contradiction_pressure >= config.contradiction_pressure_watch:
        reason_codes.append("contradiction_pressure_elevated")
    if evidence_freshness <= config.evidence_freshness_stale:
        reason_codes.append("evidence_freshness_stale")
    if source_reliability <= config.source_reliability_weak:
        reason_codes.append("source_reliability_weak")
    if catalyst_pressure >= config.catalyst_pressure_watch:
        reason_codes.append("catalyst_pressure_elevated")
    if team_confidence_dispersion >= config.team_confidence_dispersion_watch:
        reason_codes.append("team_confidence_dispersion_elevated")
    return tuple(reason_codes)


def _normalize_observations(
    observations: Iterable[ResearchEventSignalConflictPriorityObservation],
) -> tuple[ResearchEventSignalConflictPriorityObservation, ...]:
    if isinstance(observations, (str, bytes)) or not isinstance(observations, Iterable):
        raise ValueError("observations must be an iterable")
    normalized = tuple(observations)
    for observation in normalized:
        if type(observation) is not ResearchEventSignalConflictPriorityObservation:
            raise ValueError(
                "observations must contain "
                "ResearchEventSignalConflictPriorityObservation values",
            )
        _require_hard_flags("observation", observation)
    return normalized


def _normalize_rows(
    rows: tuple[ResearchEventSignalConflictPriorityRow, ...],
) -> tuple[ResearchEventSignalConflictPriorityRow, ...]:
    if type(rows) not in (list, tuple):
        raise ValueError("rows must be a list or tuple")
    normalized = tuple(rows)
    seen_domains: set[str] = set()
    for row in normalized:
        if type(row) is not ResearchEventSignalConflictPriorityRow:
            raise ValueError(
                "rows must contain ResearchEventSignalConflictPriorityRow values",
            )
        if row.event_domain in seen_domains:
            raise ValueError("rows must not contain duplicate event_domain values")
        seen_domains.add(row.event_domain)
        _require_hard_flags("row", row)
    return tuple(
        sorted(
            normalized,
            key=lambda row: (-row.priority_score, row.event_domain),
        ),
    )


def _normalize_reason_code_counts(
    counts: tuple[ResearchEventSignalConflictPriorityReasonCodeCount, ...],
) -> tuple[ResearchEventSignalConflictPriorityReasonCodeCount, ...]:
    if type(counts) not in (list, tuple):
        raise ValueError("reason_code_counts must be a list or tuple")
    normalized = tuple(counts)
    seen: set[str] = set()
    for count in normalized:
        if type(count) is not ResearchEventSignalConflictPriorityReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "ResearchEventSignalConflictPriorityReasonCodeCount values",
            )
        if count.reason_code in seen:
            raise ValueError("reason_code_counts must not contain duplicates")
        seen.add(count.reason_code)
    return tuple(sorted(normalized, key=lambda count: count.reason_code))


def _normalize_reason_codes(
    field_name: str,
    reason_codes: tuple[str, ...],
    *,
    allow_empty: bool,
) -> tuple[str, ...]:
    if type(reason_codes) not in (list, tuple):
        raise ValueError(f"{field_name} must be a list or tuple")
    normalized = tuple(reason_codes)
    if not allow_empty and not normalized:
        raise ValueError(f"{field_name} must not be empty")
    seen: set[str] = set()
    for reason_code in normalized:
        _require_canonical_string(field_name, reason_code)
        if reason_code in seen:
            raise ValueError(f"{field_name} must not contain duplicates")
        seen.add(reason_code)
    return normalized


def _reason_code_counts(
    rows: tuple[ResearchEventSignalConflictPriorityRow, ...],
    reason_codes: tuple[str, ...],
) -> tuple[ResearchEventSignalConflictPriorityReasonCodeCount, ...]:
    return tuple(
        ResearchEventSignalConflictPriorityReasonCodeCount(
            reason_code=reason_code,
            count=_decimal_count(
                sum(
                    1
                    for row in rows
                    for row_reason_code in row.reason_codes
                    if row_reason_code == reason_code
                ),
            ),
        )
        for reason_code in reason_codes
    )


def _summary_reason_codes(
    rows: tuple[ResearchEventSignalConflictPriorityRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return ("no_signal_conflicts",)
    reason_codes: list[str] = []
    for row in rows:
        for reason_code in row.reason_codes:
            if reason_code not in reason_codes:
                reason_codes.append(reason_code)
    return tuple(reason_codes)


def _summary_status(
    rows: tuple[ResearchEventSignalConflictPriorityRow, ...],
) -> str:
    if any(row.status == "block" for row in rows):
        return "block"
    if any(row.status == "watch" for row in rows):
        return "watch"
    return "pass"


def _status_count(
    rows: tuple[ResearchEventSignalConflictPriorityRow, ...],
    status: str,
) -> int:
    return sum(1 for row in rows if row.status == status)


def _max_priority_score(
    rows: tuple[ResearchEventSignalConflictPriorityRow, ...],
) -> Decimal | None:
    if not rows:
        return None
    return max(row.priority_score for row in rows)


def _average_priority_score(
    rows: tuple[ResearchEventSignalConflictPriorityRow, ...],
) -> Decimal | None:
    if not rows:
        return None
    return _average_decimal(row.priority_score for row in rows)


def _average_decimal(values: Iterable[Decimal]) -> Decimal:
    normalized = tuple(values)
    if not normalized:
        raise ValueError("values must not be empty")
    total = sum(normalized, ZERO)
    return _quantize_ratio("average", total / Decimal(len(normalized)))


def _validate_report_consistency(
    report: ResearchEventSignalConflictPriorityReport,
) -> None:
    if report.domain_count != _decimal_count(len(report.rows)):
        raise ValueError("domain_count must match rows")
    if report.observation_count != sum((row.observation_count for row in report.rows), ZERO):
        raise ValueError("observation_count must match rows")
    if report.pass_count != _decimal_count(_status_count(report.rows, "pass")):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _decimal_count(_status_count(report.rows, "watch")):
        raise ValueError("watch_count must match rows")
    if report.block_count != _decimal_count(_status_count(report.rows, "block")):
        raise ValueError("block_count must match rows")
    if report.max_priority_score != _max_priority_score(report.rows):
        raise ValueError("max_priority_score must match rows")
    if report.average_priority_score != _average_priority_score(report.rows):
        raise ValueError("average_priority_score must match rows")
    if report.reason_codes != _summary_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")
    if report.status != _summary_status(report.rows):
        raise ValueError("status must match rows")


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
        return {str(key): _payload_value(item) for key, item in value.items()}
    return value


def _as_utc(field_name: str, value: datetime) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _decimal_count(value: int) -> Decimal:
    if type(value) is not int or value < 0:
        raise ValueError("count value must be a nonnegative int")
    return Decimal(value).quantize(COUNT_QUANTUM)


def _quantize_ratio(field_name: str, value: Decimal) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    return value.quantize(RATIO_QUANTUM)


def _require_probability_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    normalized = value.quantize(RATIO_QUANTUM)
    if normalized < ZERO or normalized > ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return normalized


def _require_optional_probability_decimal(
    field_name: str,
    value: object,
) -> Decimal | None:
    if value is None:
        return None
    return _require_probability_decimal(field_name, value)


def _require_nonnegative_whole_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    normalized = value.quantize(COUNT_QUANTUM)
    if value != normalized:
        raise ValueError(f"{field_name} must be a whole Decimal")
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _require_positive_whole_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_nonnegative_whole_decimal(field_name, value)
    if normalized <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _require_status(field_name: str, value: str) -> None:
    if value not in STATUSES:
        raise ValueError(f"{field_name} must be one of pass, watch, block")


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value != value.strip():
        raise ValueError(f"{field_name} must be a canonical non-empty string")
    allowed = set("abcdefghijklmnopqrstuvwxyz0123456789_-")
    if any(character not in allowed for character in value):
        raise ValueError(f"{field_name} must use lowercase public-safe characters")


def _field_value(value: object, field_name: str) -> object:
    if is_dataclass(value):
        for field in fields(value):
            if field.name == field_name:
                return getattr(value, field_name)
    if hasattr(value, field_name):
        return getattr(value, field_name)
    raise ValueError(f"{field_name} is required")


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if _field_value(value, field_name) is not True:
            raise ValueError(f"{label} {field_name} must be True")
