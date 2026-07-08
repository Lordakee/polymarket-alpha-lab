"""Pure public-safe confidence floor report for event-domain evidence research."""

from __future__ import annotations

import hashlib
import json
from dataclasses import InitVar, dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation
from typing import Any


__all__ = (
    "DEFAULT_RESEARCH_EVENT_EVIDENCE_CONFIDENCE_FLOOR_CONFIG_VERSION",
    "ResearchEventEvidenceConfidenceFloorConfig",
    "ResearchEventEvidenceConfidenceFloorObservation",
    "ResearchEventEvidenceConfidenceFloorReasonCodeCount",
    "ResearchEventEvidenceConfidenceFloorReport",
    "ResearchEventEvidenceConfidenceFloorRow",
    "build_research_event_evidence_confidence_floor_report",
    "research_event_evidence_confidence_floor_report_digest",
    "research_event_evidence_confidence_floor_report_payload",
)


DEFAULT_RESEARCH_EVENT_EVIDENCE_CONFIDENCE_FLOOR_CONFIG_VERSION = (
    "event-evidence-confidence-floor-report-v0"
)

STATUS_PASS = "pass"
STATUS_WATCH = "watch"
STATUS_BLOCK = "block"
STATUSES = (STATUS_PASS, STATUS_WATCH, STATUS_BLOCK)

PASS_REASON = "event_domain_evidence_confidence_floor_pass"
NO_INPUTS_REASON = "event_domain_evidence_confidence_floor_no_inputs"
FLOOR_BELOW_WATCH_REASON = "event_domain_evidence_confidence_floor_below_watch"
FLOOR_BETWEEN_REASON = "event_domain_evidence_confidence_floor_between_watch_and_pass"
EVIDENCE_FRESHNESS_BELOW_WATCH_REASON = "event_domain_evidence_freshness_below_watch"
EVIDENCE_FRESHNESS_WATCH_REASON = "event_domain_evidence_freshness_watch"
SOURCE_RELIABILITY_BELOW_WATCH_REASON = "event_domain_source_reliability_below_watch"
SOURCE_RELIABILITY_WATCH_REASON = "event_domain_source_reliability_watch"
CONTRADICTION_HIGH_REASON = "event_domain_contradiction_pressure_high"
CONTRADICTION_ELEVATED_REASON = "event_domain_contradiction_pressure_elevated"
CATALYST_HIGH_REASON = "event_domain_catalyst_pressure_high"
CATALYST_ELEVATED_REASON = "event_domain_catalyst_pressure_elevated"
RESOLUTION_PROXIMITY_HIGH_REASON = "event_domain_resolution_proximity_high"
RESOLUTION_PROXIMITY_WATCH_REASON = "event_domain_resolution_proximity_watch"

REASON_CODE_SEQUENCE = (
    FLOOR_BELOW_WATCH_REASON,
    EVIDENCE_FRESHNESS_BELOW_WATCH_REASON,
    SOURCE_RELIABILITY_BELOW_WATCH_REASON,
    CONTRADICTION_HIGH_REASON,
    CATALYST_HIGH_REASON,
    RESOLUTION_PROXIMITY_HIGH_REASON,
    FLOOR_BETWEEN_REASON,
    EVIDENCE_FRESHNESS_WATCH_REASON,
    SOURCE_RELIABILITY_WATCH_REASON,
    CONTRADICTION_ELEVATED_REASON,
    CATALYST_ELEVATED_REASON,
    RESOLUTION_PROXIMITY_WATCH_REASON,
    PASS_REASON,
    NO_INPUTS_REASON,
)
BLOCK_REASONS = (
    FLOOR_BELOW_WATCH_REASON,
    EVIDENCE_FRESHNESS_BELOW_WATCH_REASON,
    SOURCE_RELIABILITY_BELOW_WATCH_REASON,
    CONTRADICTION_HIGH_REASON,
    CATALYST_HIGH_REASON,
    RESOLUTION_PROXIMITY_HIGH_REASON,
)

NEXT_STEPS = {
    STATUS_PASS: "pass_report_only_event_evidence_confidence_floor",
    STATUS_WATCH: "watch_report_only_event_evidence_confidence_floor",
    STATUS_BLOCK: "block_report_only_event_evidence_confidence_floor",
}

ZERO = Decimal("0")
ONE = Decimal("1")
RATIO_QUANTUM = Decimal("0.000001")


@dataclass(frozen=True)
class ResearchEventEvidenceConfidenceFloorConfig:
    config_version: str = DEFAULT_RESEARCH_EVENT_EVIDENCE_CONFIDENCE_FLOOR_CONFIG_VERSION
    pass_confidence_floor_threshold: Decimal = Decimal("0.700000")
    watch_confidence_floor_threshold: Decimal = Decimal("0.500000")
    min_pass_evidence_freshness: Decimal = Decimal("0.750000")
    min_watch_evidence_freshness: Decimal = Decimal("0.500000")
    min_pass_source_reliability: Decimal = Decimal("0.750000")
    min_watch_source_reliability: Decimal = Decimal("0.500000")
    max_pass_contradiction_pressure: Decimal = Decimal("0.200000")
    max_watch_contradiction_pressure: Decimal = Decimal("0.550000")
    max_pass_catalyst_pressure: Decimal = Decimal("0.300000")
    max_watch_catalyst_pressure: Decimal = Decimal("0.650000")
    max_pass_resolution_proximity: Decimal = Decimal("0.400000")
    max_watch_resolution_proximity: Decimal = Decimal("0.750000")
    evidence_freshness_weight: Decimal = Decimal("0.300000")
    source_reliability_weight: Decimal = Decimal("0.300000")
    contradiction_pressure_weight: Decimal = Decimal("0.200000")
    catalyst_pressure_weight: Decimal = Decimal("0.100000")
    resolution_proximity_weight: Decimal = Decimal("0.100000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchEventEvidenceConfidenceFloorConfig:
            raise TypeError(
                "ResearchEventEvidenceConfidenceFloorConfig does not support "
                "subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchEventEvidenceConfidenceFloorConfig:
            raise ValueError(
                "config must be exactly ResearchEventEvidenceConfidenceFloorConfig",
            )
        _require_public_string("config_version", self.config_version)
        for field_name in (
            "pass_confidence_floor_threshold",
            "watch_confidence_floor_threshold",
            "min_pass_evidence_freshness",
            "min_watch_evidence_freshness",
            "min_pass_source_reliability",
            "min_watch_source_reliability",
            "max_pass_contradiction_pressure",
            "max_watch_contradiction_pressure",
            "max_pass_catalyst_pressure",
            "max_watch_catalyst_pressure",
            "max_pass_resolution_proximity",
            "max_watch_resolution_proximity",
            "evidence_freshness_weight",
            "source_reliability_weight",
            "contradiction_pressure_weight",
            "catalyst_pressure_weight",
            "resolution_proximity_weight",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        if self.pass_confidence_floor_threshold <= self.watch_confidence_floor_threshold:
            raise ValueError(
                "pass_confidence_floor_threshold must be greater than "
                "watch_confidence_floor_threshold",
            )
        _require_pass_at_least_watch(
            "min_pass_evidence_freshness",
            self.min_pass_evidence_freshness,
            "min_watch_evidence_freshness",
            self.min_watch_evidence_freshness,
        )
        _require_pass_at_least_watch(
            "min_pass_source_reliability",
            self.min_pass_source_reliability,
            "min_watch_source_reliability",
            self.min_watch_source_reliability,
        )
        _require_watch_at_least_pass(
            "max_watch_contradiction_pressure",
            self.max_watch_contradiction_pressure,
            "max_pass_contradiction_pressure",
            self.max_pass_contradiction_pressure,
        )
        _require_watch_at_least_pass(
            "max_watch_catalyst_pressure",
            self.max_watch_catalyst_pressure,
            "max_pass_catalyst_pressure",
            self.max_pass_catalyst_pressure,
        )
        _require_watch_at_least_pass(
            "max_watch_resolution_proximity",
            self.max_watch_resolution_proximity,
            "max_pass_resolution_proximity",
            self.max_pass_resolution_proximity,
        )
        weight_sum = _quantize(
            self.evidence_freshness_weight
            + self.source_reliability_weight
            + self.contradiction_pressure_weight
            + self.catalyst_pressure_weight
            + self.resolution_proximity_weight,
        )
        if weight_sum != ONE:
            raise ValueError("weights must sum to 1.000000")
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class ResearchEventEvidenceConfidenceFloorObservation:
    event_domain: str
    observed_at: datetime
    aggregate_evidence_freshness: Decimal
    source_reliability: Decimal
    contradiction_pressure: Decimal
    catalyst_pressure: Decimal
    resolution_proximity: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchEventEvidenceConfidenceFloorObservation:
            raise TypeError(
                "ResearchEventEvidenceConfidenceFloorObservation does not support "
                "subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchEventEvidenceConfidenceFloorObservation:
            raise ValueError(
                "observation must be exactly "
                "ResearchEventEvidenceConfidenceFloorObservation",
            )
        _require_public_domain("event_domain", self.event_domain)
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in (
            "aggregate_evidence_freshness",
            "source_reliability",
            "contradiction_pressure",
            "catalyst_pressure",
            "resolution_proximity",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        _require_hard_flags("observation", self)


@dataclass(frozen=True)
class ResearchEventEvidenceConfidenceFloorRow:
    event_domain: str
    observed_at: datetime
    observation_age_seconds: Decimal
    aggregate_evidence_freshness: Decimal
    source_reliability: Decimal
    contradiction_pressure: Decimal
    catalyst_pressure: Decimal
    resolution_proximity: Decimal
    confidence_floor: Decimal
    status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True
    validation_config: InitVar[ResearchEventEvidenceConfidenceFloorConfig | None] = None

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchEventEvidenceConfidenceFloorRow:
            raise TypeError(
                "ResearchEventEvidenceConfidenceFloorRow does not support subclassing",
            )

    def __post_init__(
        self,
        validation_config: ResearchEventEvidenceConfidenceFloorConfig | None,
    ) -> None:
        if type(self) is not ResearchEventEvidenceConfidenceFloorRow:
            raise ValueError("row must be exactly ResearchEventEvidenceConfidenceFloorRow")
        _require_public_domain("event_domain", self.event_domain)
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        object.__setattr__(
            self,
            "observation_age_seconds",
            _require_nonnegative_decimal(
                "observation_age_seconds",
                self.observation_age_seconds,
            ),
        )
        for field_name in (
            "aggregate_evidence_freshness",
            "source_reliability",
            "contradiction_pressure",
            "catalyst_pressure",
            "resolution_proximity",
            "confidence_floor",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        _require_status("status", self.status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        _require_hard_flags("row", self)
        _validate_row(self, validation_config)


@dataclass(frozen=True)
class ResearchEventEvidenceConfidenceFloorReasonCodeCount:
    reason_code: str
    count: Decimal
    domain_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchEventEvidenceConfidenceFloorReasonCodeCount:
            raise TypeError(
                "ResearchEventEvidenceConfidenceFloorReasonCodeCount does not support "
                "subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchEventEvidenceConfidenceFloorReasonCodeCount:
            raise ValueError(
                "reason code count must be exactly "
                "ResearchEventEvidenceConfidenceFloorReasonCodeCount",
            )
        _require_reason_code("reason_code", self.reason_code)
        object.__setattr__(
            self,
            "count",
            _require_nonnegative_decimal("count", self.count),
        )
        object.__setattr__(
            self,
            "domain_ratio",
            _require_ratio_decimal("domain_ratio", self.domain_ratio),
        )
        _require_hard_flags("reason code count", self)


@dataclass(frozen=True)
class ResearchEventEvidenceConfidenceFloorReport:
    generated_at: datetime
    config_version: str
    status: str
    next_step: str
    domain_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    average_confidence_floor: Decimal | None
    average_evidence_freshness: Decimal | None
    average_source_reliability: Decimal | None
    max_contradiction_pressure: Decimal | None
    max_catalyst_pressure: Decimal | None
    max_resolution_proximity: Decimal | None
    lowest_confidence_floor: Decimal | None
    rows: tuple[ResearchEventEvidenceConfidenceFloorRow, ...]
    reason_code_counts: tuple[ResearchEventEvidenceConfidenceFloorReasonCodeCount, ...]
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchEventEvidenceConfidenceFloorReport:
            raise TypeError(
                "ResearchEventEvidenceConfidenceFloorReport does not support "
                "subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchEventEvidenceConfidenceFloorReport:
            raise ValueError(
                "report must be exactly ResearchEventEvidenceConfidenceFloorReport",
            )
        object.__setattr__(
            self,
            "generated_at",
            _as_utc("generated_at", self.generated_at),
        )
        _require_public_string("config_version", self.config_version)
        _require_status("status", self.status)
        _require_public_string("next_step", self.next_step)
        for field_name in (
            "domain_count",
            "pass_count",
            "watch_count",
            "block_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "average_confidence_floor",
            "average_evidence_freshness",
            "average_source_reliability",
            "max_contradiction_pressure",
            "max_catalyst_pressure",
            "max_resolution_proximity",
            "lowest_confidence_floor",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_optional_ratio_decimal(field_name, getattr(self, field_name)),
            )
        if type(self.rows) is not tuple:
            raise ValueError("rows must be a tuple")
        for row in self.rows:
            if type(row) is not ResearchEventEvidenceConfidenceFloorRow:
                raise ValueError(
                    "rows must contain ResearchEventEvidenceConfidenceFloorRow",
                )
            _require_hard_flags("row", row)
        if type(self.reason_code_counts) is not tuple:
            raise ValueError("reason_code_counts must be a tuple")
        for item in self.reason_code_counts:
            if type(item) is not ResearchEventEvidenceConfidenceFloorReasonCodeCount:
                raise ValueError(
                    "reason_code_counts must contain "
                    "ResearchEventEvidenceConfidenceFloorReasonCodeCount",
                )
            _require_hard_flags("reason code count", item)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        _require_hard_flags("report", self)
        _validate_report(self)


def build_research_event_evidence_confidence_floor_report(
    observations: list[ResearchEventEvidenceConfidenceFloorObservation]
    | tuple[ResearchEventEvidenceConfidenceFloorObservation, ...],
    *,
    config: ResearchEventEvidenceConfidenceFloorConfig,
    generated_at: datetime,
) -> ResearchEventEvidenceConfidenceFloorReport:
    if type(config) is not ResearchEventEvidenceConfidenceFloorConfig:
        raise ValueError("config must be a ResearchEventEvidenceConfidenceFloorConfig")
    _require_hard_flags("config", config)
    report_time = _as_utc("generated_at", generated_at)
    observation_rows = _normalize_observations(observations, report_time)
    built_rows = tuple(
        _build_row(item, config=config, generated_at=report_time)
        for item in observation_rows
    )
    rows = _ranked_rows(built_rows)
    reason_code_counts = _reason_code_counts(rows)
    if not rows:
        reason_code_counts = (
            ResearchEventEvidenceConfidenceFloorReasonCodeCount(
                reason_code=NO_INPUTS_REASON,
                count=ONE.quantize(RATIO_QUANTUM),
                domain_ratio=ONE.quantize(RATIO_QUANTUM),
            ),
        )
    reason_codes = tuple(item.reason_code for item in reason_code_counts)
    status = _report_status(rows)
    return ResearchEventEvidenceConfidenceFloorReport(
        generated_at=report_time,
        config_version=config.config_version,
        status=status,
        next_step=NEXT_STEPS[status],
        domain_count=_count(len(rows)),
        pass_count=_count(_status_count(rows, STATUS_PASS)),
        watch_count=_count(_status_count(rows, STATUS_WATCH)),
        block_count=_count(_status_count(rows, STATUS_BLOCK)),
        average_confidence_floor=_average_or_none(row.confidence_floor for row in rows),
        average_evidence_freshness=_average_or_none(
            row.aggregate_evidence_freshness for row in rows
        ),
        average_source_reliability=_average_or_none(
            row.source_reliability for row in rows
        ),
        max_contradiction_pressure=max(
            (row.contradiction_pressure for row in rows),
            default=None,
        ),
        max_catalyst_pressure=max((row.catalyst_pressure for row in rows), default=None),
        max_resolution_proximity=max(
            (row.resolution_proximity for row in rows),
            default=None,
        ),
        lowest_confidence_floor=min((row.confidence_floor for row in rows), default=None),
        rows=rows,
        reason_code_counts=reason_code_counts,
        reason_codes=reason_codes,
    )


def research_event_evidence_confidence_floor_report_payload(
    report: ResearchEventEvidenceConfidenceFloorReport,
) -> dict[str, Any]:
    if type(report) is not ResearchEventEvidenceConfidenceFloorReport:
        raise ValueError("report must be a ResearchEventEvidenceConfidenceFloorReport")
    _require_hard_flags("report", report)
    payload = _payload_value(report)
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    _require_hard_flags("payload", _DictFlags(payload))
    return payload


def research_event_evidence_confidence_floor_report_digest(
    report: ResearchEventEvidenceConfidenceFloorReport,
) -> str:
    payload = research_event_evidence_confidence_floor_report_payload(report)
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


@dataclass(frozen=True)
class _DictFlags:
    value: dict[str, Any]

    @property
    def paper_only(self) -> object:
        return self.value.get("paper_only")

    @property
    def report_only(self) -> object:
        return self.value.get("report_only")

    @property
    def readonly(self) -> object:
        return self.value.get("readonly")


def _build_row(
    item: ResearchEventEvidenceConfidenceFloorObservation,
    *,
    config: ResearchEventEvidenceConfidenceFloorConfig,
    generated_at: datetime,
) -> ResearchEventEvidenceConfidenceFloorRow:
    confidence_floor = _confidence_floor(item, config)
    reason_codes = _row_reason_codes(
        aggregate_evidence_freshness=item.aggregate_evidence_freshness,
        source_reliability=item.source_reliability,
        contradiction_pressure=item.contradiction_pressure,
        catalyst_pressure=item.catalyst_pressure,
        resolution_proximity=item.resolution_proximity,
        confidence_floor=confidence_floor,
        config=config,
    )
    return ResearchEventEvidenceConfidenceFloorRow(
        event_domain=item.event_domain,
        observed_at=item.observed_at,
        observation_age_seconds=_datetime_delta_seconds(generated_at, item.observed_at),
        aggregate_evidence_freshness=item.aggregate_evidence_freshness,
        source_reliability=item.source_reliability,
        contradiction_pressure=item.contradiction_pressure,
        catalyst_pressure=item.catalyst_pressure,
        resolution_proximity=item.resolution_proximity,
        confidence_floor=confidence_floor,
        status=_row_status(reason_codes),
        reason_codes=reason_codes,
        validation_config=config,
    )


def _normalize_observations(
    observations: list[ResearchEventEvidenceConfidenceFloorObservation]
    | tuple[ResearchEventEvidenceConfidenceFloorObservation, ...],
    generated_at: datetime,
) -> tuple[ResearchEventEvidenceConfidenceFloorObservation, ...]:
    if type(observations) not in (list, tuple):
        raise ValueError("observations must be a list or tuple")
    items = tuple(observations)
    seen: set[str] = set()
    for item in items:
        if type(item) is not ResearchEventEvidenceConfidenceFloorObservation:
            raise ValueError(
                "observations must contain "
                "ResearchEventEvidenceConfidenceFloorObservation",
            )
        _require_hard_flags("observation", item)
        if item.observed_at > generated_at:
            raise ValueError("observed_at must be on or before generated_at")
        if item.event_domain in seen:
            raise ValueError("event_domain must not repeat")
        seen.add(item.event_domain)
    return items


def _row_reason_codes(
    *,
    aggregate_evidence_freshness: Decimal,
    source_reliability: Decimal,
    contradiction_pressure: Decimal,
    catalyst_pressure: Decimal,
    resolution_proximity: Decimal,
    confidence_floor: Decimal,
    config: ResearchEventEvidenceConfidenceFloorConfig,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    if confidence_floor < config.watch_confidence_floor_threshold:
        reason_codes.append(FLOOR_BELOW_WATCH_REASON)
    elif confidence_floor < config.pass_confidence_floor_threshold:
        reason_codes.append(FLOOR_BETWEEN_REASON)
    if aggregate_evidence_freshness < config.min_watch_evidence_freshness:
        reason_codes.append(EVIDENCE_FRESHNESS_BELOW_WATCH_REASON)
    elif aggregate_evidence_freshness < config.min_pass_evidence_freshness:
        reason_codes.append(EVIDENCE_FRESHNESS_WATCH_REASON)
    if source_reliability < config.min_watch_source_reliability:
        reason_codes.append(SOURCE_RELIABILITY_BELOW_WATCH_REASON)
    elif source_reliability < config.min_pass_source_reliability:
        reason_codes.append(SOURCE_RELIABILITY_WATCH_REASON)
    if contradiction_pressure > config.max_watch_contradiction_pressure:
        reason_codes.append(CONTRADICTION_HIGH_REASON)
    elif contradiction_pressure > config.max_pass_contradiction_pressure:
        reason_codes.append(CONTRADICTION_ELEVATED_REASON)
    if catalyst_pressure > config.max_watch_catalyst_pressure:
        reason_codes.append(CATALYST_HIGH_REASON)
    elif catalyst_pressure > config.max_pass_catalyst_pressure:
        reason_codes.append(CATALYST_ELEVATED_REASON)
    if resolution_proximity > config.max_watch_resolution_proximity:
        reason_codes.append(RESOLUTION_PROXIMITY_HIGH_REASON)
    elif resolution_proximity > config.max_pass_resolution_proximity:
        reason_codes.append(RESOLUTION_PROXIMITY_WATCH_REASON)
    if not reason_codes:
        reason_codes.append(PASS_REASON)
    return tuple(
        reason_code
        for reason_code in REASON_CODE_SEQUENCE
        if reason_code in reason_codes
    )


def _row_status(reason_codes: tuple[str, ...]) -> str:
    if any(reason_code in BLOCK_REASONS for reason_code in reason_codes):
        return STATUS_BLOCK
    if reason_codes == (PASS_REASON,):
        return STATUS_PASS
    return STATUS_WATCH


def _report_status(rows: tuple[ResearchEventEvidenceConfidenceFloorRow, ...]) -> str:
    if not rows:
        return STATUS_BLOCK
    if any(row.status == STATUS_BLOCK for row in rows):
        return STATUS_BLOCK
    if any(row.status == STATUS_WATCH for row in rows):
        return STATUS_WATCH
    return STATUS_PASS


def _ranked_rows(
    rows: tuple[ResearchEventEvidenceConfidenceFloorRow, ...],
) -> tuple[ResearchEventEvidenceConfidenceFloorRow, ...]:
    return tuple(
        sorted(
            rows,
            key=lambda row: (
                _status_rank(row.status),
                row.confidence_floor,
                -row.contradiction_pressure,
                -row.catalyst_pressure,
                -row.resolution_proximity,
                row.event_domain,
            ),
        ),
    )


def _status_rank(value: str) -> int:
    return {STATUS_BLOCK: 0, STATUS_WATCH: 1, STATUS_PASS: 2}[value]


def _reason_code_counts(
    rows: tuple[ResearchEventEvidenceConfidenceFloorRow, ...],
) -> tuple[ResearchEventEvidenceConfidenceFloorReasonCodeCount, ...]:
    total = _count(len(rows))
    counts: dict[str, Decimal] = {}
    for row in rows:
        for reason_code in row.reason_codes:
            counts[reason_code] = counts.get(reason_code, ZERO) + ONE
    return tuple(
        ResearchEventEvidenceConfidenceFloorReasonCodeCount(
            reason_code=reason_code,
            count=_count(counts[reason_code]),
            domain_ratio=_ratio(counts[reason_code], total),
        )
        for reason_code in REASON_CODE_SEQUENCE
        if reason_code in counts
    )


def _confidence_floor(
    item: ResearchEventEvidenceConfidenceFloorObservation,
    config: ResearchEventEvidenceConfidenceFloorConfig,
) -> Decimal:
    contradiction_signal = ONE - item.contradiction_pressure
    catalyst_signal = ONE - item.catalyst_pressure
    resolution_signal = ONE - item.resolution_proximity
    return _require_ratio_decimal(
        "confidence_floor",
        (
            item.aggregate_evidence_freshness * config.evidence_freshness_weight
            + item.source_reliability * config.source_reliability_weight
            + contradiction_signal * config.contradiction_pressure_weight
            + catalyst_signal * config.catalyst_pressure_weight
            + resolution_signal * config.resolution_proximity_weight
        ),
    )


def _validate_row(
    row: ResearchEventEvidenceConfidenceFloorRow,
    config: ResearchEventEvidenceConfidenceFloorConfig | None,
) -> None:
    cfg = config or ResearchEventEvidenceConfidenceFloorConfig()
    if type(cfg) is not ResearchEventEvidenceConfidenceFloorConfig:
        raise ValueError(
            "validation_config must be a ResearchEventEvidenceConfidenceFloorConfig",
        )
    synthetic = ResearchEventEvidenceConfidenceFloorObservation(
        event_domain=row.event_domain,
        observed_at=row.observed_at,
        aggregate_evidence_freshness=row.aggregate_evidence_freshness,
        source_reliability=row.source_reliability,
        contradiction_pressure=row.contradiction_pressure,
        catalyst_pressure=row.catalyst_pressure,
        resolution_proximity=row.resolution_proximity,
    )
    expected_confidence_floor = _confidence_floor(synthetic, cfg)
    if row.confidence_floor != expected_confidence_floor:
        raise ValueError("confidence_floor must match row inputs")
    expected_reason_codes = _row_reason_codes(
        aggregate_evidence_freshness=row.aggregate_evidence_freshness,
        source_reliability=row.source_reliability,
        contradiction_pressure=row.contradiction_pressure,
        catalyst_pressure=row.catalyst_pressure,
        resolution_proximity=row.resolution_proximity,
        confidence_floor=row.confidence_floor,
        config=cfg,
    )
    if row.reason_codes != expected_reason_codes:
        raise ValueError("reason_codes must match row inputs")
    expected_status = _row_status(expected_reason_codes)
    if row.status != expected_status:
        raise ValueError("status must match reason_codes")


def _validate_report(report: ResearchEventEvidenceConfidenceFloorReport) -> None:
    rows = report.rows
    if rows != _ranked_rows(rows):
        raise ValueError("rows must be ranked deterministically")
    expected_domain_count = _count(len(rows))
    expected_pass_count = _count(_status_count(rows, STATUS_PASS))
    expected_watch_count = _count(_status_count(rows, STATUS_WATCH))
    expected_block_count = _count(_status_count(rows, STATUS_BLOCK))
    if report.domain_count != expected_domain_count:
        raise ValueError("domain_count must match rows")
    if report.pass_count != expected_pass_count:
        raise ValueError("pass_count must match rows")
    if report.watch_count != expected_watch_count:
        raise ValueError("watch_count must match rows")
    if report.block_count != expected_block_count:
        raise ValueError("block_count must match rows")
    if report.average_confidence_floor != _average_or_none(
        row.confidence_floor for row in rows
    ):
        raise ValueError("average_confidence_floor must match rows")
    if report.average_evidence_freshness != _average_or_none(
        row.aggregate_evidence_freshness for row in rows
    ):
        raise ValueError("average_evidence_freshness must match rows")
    if report.average_source_reliability != _average_or_none(
        row.source_reliability for row in rows
    ):
        raise ValueError("average_source_reliability must match rows")
    if report.max_contradiction_pressure != max(
        (row.contradiction_pressure for row in rows),
        default=None,
    ):
        raise ValueError("max_contradiction_pressure must match rows")
    if report.max_catalyst_pressure != max(
        (row.catalyst_pressure for row in rows),
        default=None,
    ):
        raise ValueError("max_catalyst_pressure must match rows")
    if report.max_resolution_proximity != max(
        (row.resolution_proximity for row in rows),
        default=None,
    ):
        raise ValueError("max_resolution_proximity must match rows")
    if report.lowest_confidence_floor != min(
        (row.confidence_floor for row in rows),
        default=None,
    ):
        raise ValueError("lowest_confidence_floor must match rows")
    expected_reason_code_counts = _reason_code_counts(rows)
    if not rows:
        expected_reason_code_counts = (
            ResearchEventEvidenceConfidenceFloorReasonCodeCount(
                reason_code=NO_INPUTS_REASON,
                count=ONE.quantize(RATIO_QUANTUM),
                domain_ratio=ONE.quantize(RATIO_QUANTUM),
            ),
        )
    if report.reason_code_counts != expected_reason_code_counts:
        raise ValueError("reason_code_counts must match rows")
    expected_reason_codes = tuple(item.reason_code for item in expected_reason_code_counts)
    if report.reason_codes != expected_reason_codes:
        raise ValueError("reason_codes must match reason_code_counts")
    expected_status = _report_status(rows)
    if report.status != expected_status:
        raise ValueError("status must match rows")
    if report.next_step != NEXT_STEPS[report.status]:
        raise ValueError("next_step must match status")


def _status_count(
    rows: tuple[ResearchEventEvidenceConfidenceFloorRow, ...],
    status: str,
) -> int:
    return sum(1 for row in rows if row.status == status)


def _average_or_none(values: Any) -> Decimal | None:
    items = tuple(values)
    if not items:
        return None
    return _ratio(sum(items, ZERO), _count(len(items)))


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO:
        return ZERO.quantize(RATIO_QUANTUM)
    return _quantize(numerator / denominator)


def _count(value: int) -> Decimal:
    return Decimal(value).quantize(RATIO_QUANTUM)


def _datetime_delta_seconds(generated_at: datetime, observed_at: datetime) -> Decimal:
    delta = generated_at - observed_at
    whole_seconds = Decimal(delta.days * 86400 + delta.seconds)
    fractional_seconds = Decimal(delta.microseconds) / Decimal("1000000")
    return _require_nonnegative_decimal(
        "observation_age_seconds",
        whole_seconds + fractional_seconds,
    )


def _require_pass_at_least_watch(
    pass_name: str,
    pass_value: Decimal,
    watch_name: str,
    watch_value: Decimal,
) -> None:
    if pass_value < watch_value:
        raise ValueError(f"{pass_name} must be at least {watch_name}")


def _require_watch_at_least_pass(
    watch_name: str,
    watch_value: Decimal,
    pass_name: str,
    pass_value: Decimal,
) -> None:
    if watch_value < pass_value:
        raise ValueError(f"{watch_name} must be at least {pass_name}")


def _require_public_domain(field_name: str, value: object) -> str:
    normalized = _require_public_string(field_name, value)
    parts = normalized.replace("-", "_").split("_")
    if parts[-1:] == ["id"]:
        raise ValueError(f"{field_name} must describe a public-safe domain")
    return normalized


def _require_public_string(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a str")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be non-empty and normalized")
    for char in value:
        is_letter = "a" <= char <= "z"
        is_digit = "0" <= char <= "9"
        if not (is_letter or is_digit or char in "_-"):
            raise ValueError(f"{field_name} must be public-safe")
    return value


def _require_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in STATUSES:
        raise ValueError(f"{field_name} must be one of pass, watch, block")


def _require_reason_code(field_name: str, value: object) -> str:
    _require_public_string(field_name, value)
    if value not in REASON_CODE_SEQUENCE:
        raise ValueError(f"{field_name} is not recognized")
    return value


def _normalize_reason_codes(
    field_name: str,
    values: tuple[str, ...],
) -> tuple[str, ...]:
    if type(values) is not tuple:
        raise ValueError(f"{field_name} must be a tuple")
    normalized = tuple(_require_reason_code(field_name, value) for value in values)
    if not normalized:
        raise ValueError(f"{field_name} must not be empty")
    if len(set(normalized)) != len(normalized):
        raise ValueError(f"{field_name} must not contain duplicates")
    return tuple(
        reason_code for reason_code in REASON_CODE_SEQUENCE if reason_code in normalized
    )


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


def _require_optional_ratio_decimal(field_name: str, value: object) -> Decimal | None:
    if value is None:
        return None
    return _require_ratio_decimal(field_name, value)


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    try:
        return _quantize(value)
    except InvalidOperation as exc:
        raise ValueError(f"{field_name} must be quantizable") from exc


def _quantize(value: Decimal) -> Decimal:
    return value.quantize(RATIO_QUANTUM)


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if getattr(value, field_name, None) is not True:
            raise ValueError(f"{label}.{field_name} must be True")


def _payload_value(value: object) -> Any:
    if isinstance(value, Decimal):
        return format(_quantize(value), "f")
    if isinstance(value, datetime):
        return value.isoformat().replace("+00:00", "Z")
    if is_dataclass(value):
        return {
            field.name: _payload_value(getattr(value, field.name))
            for field in fields(value)
        }
    if isinstance(value, tuple):
        return [_payload_value(item) for item in value]
    if value is None or type(value) in (str, bool):
        return value
    raise ValueError(f"payload value has unsupported type {type(value).__name__}")
