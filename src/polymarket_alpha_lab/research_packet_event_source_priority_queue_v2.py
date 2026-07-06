"""Readonly Decimal priority queue report for event packet source collection."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
import json


DEFAULT_RESEARCH_PACKET_EVENT_SOURCE_PRIORITY_QUEUE_V2_CONFIG_VERSION = (
    "research-packet-event-source-priority-queue-v2"
)

DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
COUNT_QUANT = Decimal("1")
SCORE_QUANT = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")

PRIORITY_TIERS = ("high", "medium", "low")
REPORT_STATUSES = ("high_priority", "medium_priority", "low_priority")
ROW_REASON_CODES = (
    "source_priority_high",
    "source_priority_medium",
    "source_priority_low",
    "event_velocity_high",
    "official_source_gap_present",
    "source_family_gap_present",
    "contradiction_severity_high",
    "probability_movement_high",
    "resolution_horizon_near",
    "specialist_uncertainty_high",
)
REPORT_REASON_CODES = (
    "source_priority_high_present",
    "source_priority_medium_present",
    "source_priority_low_only",
    "event_velocity_high",
    "official_source_gap_present",
    "source_family_gap_present",
    "contradiction_severity_high",
    "probability_movement_high",
    "resolution_horizon_near",
    "specialist_uncertainty_high",
)
UNSAFE_PUBLIC_TEXT_FRAGMENTS = (
    "live",
    "auth",
    "wallet",
    "order",
    "network",
    "database",
    "persist",
    "signing",
    "mutation",
    "buy",
    "sell",
    "trade",
)

ROW_PAYLOAD_FIELDS = (
    "row_rank",
    "packet_id",
    "event_slug",
    "event_velocity_per_hour",
    "official_source_count",
    "official_source_gap",
    "independent_source_family_count",
    "source_family_gap",
    "contradiction_severity_score",
    "probability_movement_24h",
    "resolution_horizon_minutes",
    "specialist_uncertainty_score",
    "event_velocity_pressure",
    "official_source_gap_pressure",
    "source_family_independence_pressure",
    "contradiction_pressure",
    "probability_movement_pressure",
    "resolution_horizon_pressure",
    "specialist_uncertainty_pressure",
    "priority_score",
    "priority_tier",
    "reason_codes",
    "paper_only",
    "report_only",
    "readonly",
)
REPORT_PAYLOAD_FIELDS = (
    "generated_at",
    "config_version",
    "report_status",
    "packet_count",
    "high_priority_packet_count",
    "medium_priority_packet_count",
    "low_priority_packet_count",
    "event_velocity_count",
    "official_source_gap_count",
    "source_family_gap_count",
    "contradiction_severity_count",
    "probability_movement_count",
    "near_resolution_horizon_count",
    "specialist_uncertainty_count",
    "max_priority_score",
    "rows",
    "reason_codes",
    "derived_validation_digest",
    "paper_only",
    "report_only",
    "readonly",
)


__all__ = (
    "DEFAULT_RESEARCH_PACKET_EVENT_SOURCE_PRIORITY_QUEUE_V2_CONFIG_VERSION",
    "ResearchPacketEventSourcePriorityQueueV2Config",
    "ResearchPacketEventSourcePriorityQueueV2Input",
    "ResearchPacketEventSourcePriorityQueueV2Row",
    "ResearchPacketEventSourcePriorityQueueV2Report",
    "build_research_packet_event_source_priority_queue_v2_report",
    "research_packet_event_source_priority_queue_v2_report_payload",
)


@dataclass(frozen=True)
class ResearchPacketEventSourcePriorityQueueV2Config:
    config_version: str = (
        DEFAULT_RESEARCH_PACKET_EVENT_SOURCE_PRIORITY_QUEUE_V2_CONFIG_VERSION
    )
    event_velocity_weight: Decimal = Decimal("0.200000")
    official_source_gap_weight: Decimal = Decimal("0.180000")
    source_family_independence_weight: Decimal = Decimal("0.140000")
    contradiction_severity_weight: Decimal = Decimal("0.110000")
    probability_movement_weight: Decimal = Decimal("0.140000")
    resolution_horizon_weight: Decimal = Decimal("0.130000")
    specialist_uncertainty_weight: Decimal = Decimal("0.100000")
    high_event_velocity_per_hour: Decimal = Decimal("12.000000")
    min_official_source_count: Decimal = Decimal("2")
    min_independent_source_family_count: Decimal = Decimal("4")
    high_contradiction_severity_score: Decimal = Decimal("0.700000")
    high_probability_movement_24h: Decimal = Decimal("0.080000")
    near_resolution_horizon_minutes: Decimal = Decimal("720.000000")
    critical_resolution_horizon_minutes: Decimal = Decimal("60.000000")
    high_specialist_uncertainty_score: Decimal = Decimal("0.750000")
    high_priority_score_floor: Decimal = Decimal("0.700000")
    medium_priority_score_floor: Decimal = Decimal("0.250000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchPacketEventSourcePriorityQueueV2Config does not support subclassing",
        )

    def __post_init__(self) -> None:
        _require_exact_type("config", self, ResearchPacketEventSourcePriorityQueueV2Config)
        object.__setattr__(
            self,
            "config_version",
            _require_public_string("config_version", self.config_version),
        )
        for field_name in (
            "event_velocity_weight",
            "official_source_gap_weight",
            "source_family_independence_weight",
            "contradiction_severity_weight",
            "probability_movement_weight",
            "resolution_horizon_weight",
            "specialist_uncertainty_weight",
            "high_contradiction_severity_score",
            "high_probability_movement_24h",
            "high_specialist_uncertainty_score",
            "high_priority_score_floor",
            "medium_priority_score_floor",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_probability(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "high_event_velocity_per_hour",
            "near_resolution_horizon_minutes",
            "critical_resolution_horizon_minutes",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_positive_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "min_official_source_count",
            "min_independent_source_family_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_positive_count_decimal(field_name, getattr(self, field_name)),
            )
        _validate_config(self)
        _require_hard_flags("config", self)
        _reject_unsafe_public_payload("config", _payload_value(asdict(self)))


@dataclass(frozen=True)
class ResearchPacketEventSourcePriorityQueueV2Input:
    packet_id: str
    event_slug: str
    event_velocity_per_hour: Decimal
    official_source_count: Decimal
    independent_source_family_count: Decimal
    contradiction_severity_score: Decimal
    probability_movement_24h: Decimal
    resolution_horizon_minutes: Decimal
    specialist_uncertainty_score: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchPacketEventSourcePriorityQueueV2Input does not support subclassing",
        )

    def __post_init__(self) -> None:
        _require_exact_type("input", self, ResearchPacketEventSourcePriorityQueueV2Input)
        for field_name in ("packet_id", "event_slug"):
            object.__setattr__(
                self,
                field_name,
                _require_public_string(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "event_velocity_per_hour",
            _require_nonnegative_decimal(
                "event_velocity_per_hour",
                self.event_velocity_per_hour,
            ),
        )
        for field_name in (
            "official_source_count",
            "independent_source_family_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_count_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "contradiction_severity_score",
            "probability_movement_24h",
            "specialist_uncertainty_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_probability(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "resolution_horizon_minutes",
            _require_nonnegative_decimal(
                "resolution_horizon_minutes",
                self.resolution_horizon_minutes,
            ),
        )
        _require_hard_flags("input", self)
        _reject_unsafe_public_payload("input", _payload_value(asdict(self)))


@dataclass(frozen=True)
class ResearchPacketEventSourcePriorityQueueV2Row:
    row_rank: Decimal
    packet_id: str
    event_slug: str
    event_velocity_per_hour: Decimal
    official_source_count: Decimal
    official_source_gap: Decimal
    independent_source_family_count: Decimal
    source_family_gap: Decimal
    contradiction_severity_score: Decimal
    probability_movement_24h: Decimal
    resolution_horizon_minutes: Decimal
    specialist_uncertainty_score: Decimal
    event_velocity_pressure: Decimal
    official_source_gap_pressure: Decimal
    source_family_independence_pressure: Decimal
    contradiction_pressure: Decimal
    probability_movement_pressure: Decimal
    resolution_horizon_pressure: Decimal
    specialist_uncertainty_pressure: Decimal
    priority_score: Decimal
    priority_tier: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchPacketEventSourcePriorityQueueV2Row does not support subclassing",
        )

    def __post_init__(self) -> None:
        _require_exact_type("row", self, ResearchPacketEventSourcePriorityQueueV2Row)
        object.__setattr__(
            self,
            "row_rank",
            _require_positive_count_decimal("row_rank", self.row_rank),
        )
        for field_name in ("packet_id", "event_slug"):
            object.__setattr__(
                self,
                field_name,
                _require_public_string(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "event_velocity_per_hour",
            "resolution_horizon_minutes",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "official_source_count",
            "official_source_gap",
            "independent_source_family_count",
            "source_family_gap",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_count_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "contradiction_severity_score",
            "probability_movement_24h",
            "specialist_uncertainty_score",
            "event_velocity_pressure",
            "official_source_gap_pressure",
            "source_family_independence_pressure",
            "contradiction_pressure",
            "probability_movement_pressure",
            "resolution_horizon_pressure",
            "specialist_uncertainty_pressure",
            "priority_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_probability(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "priority_tier",
            _require_member("priority_tier", self.priority_tier, PRIORITY_TIERS),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, ROW_REASON_CODES),
        )
        _require_hard_flags("row", self)
        _reject_unsafe_public_payload("row", _payload_value(asdict(self)))
        _validate_row(self)


@dataclass(frozen=True)
class ResearchPacketEventSourcePriorityQueueV2Report:
    generated_at: datetime
    config_version: str
    report_status: str
    packet_count: Decimal
    high_priority_packet_count: Decimal
    medium_priority_packet_count: Decimal
    low_priority_packet_count: Decimal
    event_velocity_count: Decimal
    official_source_gap_count: Decimal
    source_family_gap_count: Decimal
    contradiction_severity_count: Decimal
    probability_movement_count: Decimal
    near_resolution_horizon_count: Decimal
    specialist_uncertainty_count: Decimal
    max_priority_score: Decimal
    rows: tuple[ResearchPacketEventSourcePriorityQueueV2Row, ...]
    reason_codes: tuple[str, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchPacketEventSourcePriorityQueueV2Report does not support subclassing",
        )

    def __post_init__(self) -> None:
        _require_exact_type("report", self, ResearchPacketEventSourcePriorityQueueV2Report)
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        object.__setattr__(
            self,
            "config_version",
            _require_public_string("config_version", self.config_version),
        )
        object.__setattr__(
            self,
            "report_status",
            _require_member("report_status", self.report_status, REPORT_STATUSES),
        )
        for field_name in (
            "packet_count",
            "high_priority_packet_count",
            "medium_priority_packet_count",
            "low_priority_packet_count",
            "event_velocity_count",
            "official_source_gap_count",
            "source_family_gap_count",
            "contradiction_severity_count",
            "probability_movement_count",
            "near_resolution_horizon_count",
            "specialist_uncertainty_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_count_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "max_priority_score",
            _require_probability("max_priority_score", self.max_priority_score),
        )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(
                "reason_codes",
                self.reason_codes,
                REPORT_REASON_CODES,
            ),
        )
        _require_hard_flags("report", self)
        _reject_unsafe_public_payload("report", _payload_value(asdict(self)))
        _validate_report(self)
        if self.derived_validation_digest == "":
            object.__setattr__(
                self,
                "derived_validation_digest",
                _derived_validation_digest(asdict(self)),
            )
        else:
            object.__setattr__(
                self,
                "derived_validation_digest",
                _require_sha256_digest(
                    "derived_validation_digest",
                    self.derived_validation_digest,
                ),
            )
        _validate_report_digest(self)

    @property
    def payload(self) -> dict[str, object]:
        return research_packet_event_source_priority_queue_v2_report_payload(self)


def build_research_packet_event_source_priority_queue_v2_report(
    inputs: object,
    *,
    config: ResearchPacketEventSourcePriorityQueueV2Config,
    generated_at: datetime,
) -> ResearchPacketEventSourcePriorityQueueV2Report:
    _require_exact_type("config", config, ResearchPacketEventSourcePriorityQueueV2Config)
    _require_hard_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    normalized_inputs = _normalize_inputs(inputs)
    rows_without_rank = tuple(
        _row_from_input(item, config=config, rank=ONE) for item in normalized_inputs
    )
    rows = tuple(
        _ranked_row(row, rank=index)
        for index, row in enumerate(_sort_rows(rows_without_rank), start=1)
    )
    return ResearchPacketEventSourcePriorityQueueV2Report(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        report_status=_report_status(rows),
        packet_count=_decimal_count(len(rows)),
        high_priority_packet_count=_tier_count(rows, "high"),
        medium_priority_packet_count=_tier_count(rows, "medium"),
        low_priority_packet_count=_tier_count(rows, "low"),
        event_velocity_count=_reason_count(rows, "event_velocity_high"),
        official_source_gap_count=_reason_count(rows, "official_source_gap_present"),
        source_family_gap_count=_reason_count(rows, "source_family_gap_present"),
        contradiction_severity_count=_reason_count(rows, "contradiction_severity_high"),
        probability_movement_count=_reason_count(rows, "probability_movement_high"),
        near_resolution_horizon_count=_reason_count(rows, "resolution_horizon_near"),
        specialist_uncertainty_count=_reason_count(rows, "specialist_uncertainty_high"),
        max_priority_score=max((row.priority_score for row in rows), default=ZERO),
        rows=rows,
        reason_codes=_report_reason_codes(rows),
    )


def research_packet_event_source_priority_queue_v2_report_payload(
    report: ResearchPacketEventSourcePriorityQueueV2Report | dict[str, object],
) -> dict[str, object]:
    if type(report) is ResearchPacketEventSourcePriorityQueueV2Report:
        _require_hard_flags("report", report)
        _validate_report(report)
        _validate_report_digest(report)
        payload = _payload_value(asdict(report))
        if type(payload) is not dict:
            raise ValueError("payload must be a dict")
        _reject_unsafe_public_payload("payload", payload)
        _require_public_payload_fields(payload)
        return payload
    if type(report) is dict:
        _reject_unsafe_public_payload("payload", report)
        _require_public_payload_fields(report)
        _validate_public_payload_digest(report)
        return _copy_json_object(report)
    raise ValueError(
        "report must be ResearchPacketEventSourcePriorityQueueV2Report or payload dict",
    )


def _row_from_input(
    item: ResearchPacketEventSourcePriorityQueueV2Input,
    *,
    config: ResearchPacketEventSourcePriorityQueueV2Config,
    rank: Decimal,
) -> ResearchPacketEventSourcePriorityQueueV2Row:
    official_gap = _count_gap(config.min_official_source_count, item.official_source_count)
    family_gap = _count_gap(
        config.min_independent_source_family_count,
        item.independent_source_family_count,
    )
    event_velocity_pressure = _capped_ratio(
        item.event_velocity_per_hour,
        config.high_event_velocity_per_hour,
    )
    official_gap_pressure = _capped_ratio(official_gap, config.min_official_source_count)
    family_independence_pressure = _capped_ratio(
        family_gap,
        config.min_independent_source_family_count,
    )
    contradiction_pressure = item.contradiction_severity_score
    probability_pressure = _capped_ratio(
        item.probability_movement_24h,
        config.high_probability_movement_24h,
    )
    horizon_pressure = _resolution_horizon_pressure(item.resolution_horizon_minutes, config)
    uncertainty_pressure = item.specialist_uncertainty_score
    priority_score = _priority_score(
        config=config,
        event_velocity_pressure=event_velocity_pressure,
        official_source_gap_pressure=official_gap_pressure,
        source_family_independence_pressure=family_independence_pressure,
        contradiction_pressure=contradiction_pressure,
        probability_movement_pressure=probability_pressure,
        resolution_horizon_pressure=horizon_pressure,
        specialist_uncertainty_pressure=uncertainty_pressure,
    )
    tier = _priority_tier(priority_score, config)
    return ResearchPacketEventSourcePriorityQueueV2Row(
        row_rank=rank,
        packet_id=item.packet_id,
        event_slug=item.event_slug,
        event_velocity_per_hour=item.event_velocity_per_hour,
        official_source_count=item.official_source_count,
        official_source_gap=official_gap,
        independent_source_family_count=item.independent_source_family_count,
        source_family_gap=family_gap,
        contradiction_severity_score=item.contradiction_severity_score,
        probability_movement_24h=item.probability_movement_24h,
        resolution_horizon_minutes=item.resolution_horizon_minutes,
        specialist_uncertainty_score=item.specialist_uncertainty_score,
        event_velocity_pressure=event_velocity_pressure,
        official_source_gap_pressure=official_gap_pressure,
        source_family_independence_pressure=family_independence_pressure,
        contradiction_pressure=contradiction_pressure,
        probability_movement_pressure=probability_pressure,
        resolution_horizon_pressure=horizon_pressure,
        specialist_uncertainty_pressure=uncertainty_pressure,
        priority_score=priority_score,
        priority_tier=tier,
        reason_codes=_row_reason_codes(
            item,
            config=config,
            official_gap=official_gap,
            family_gap=family_gap,
            tier=tier,
        ),
    )


def _ranked_row(
    row: ResearchPacketEventSourcePriorityQueueV2Row,
    *,
    rank: int,
) -> ResearchPacketEventSourcePriorityQueueV2Row:
    return ResearchPacketEventSourcePriorityQueueV2Row(
        row_rank=_decimal_count(rank),
        packet_id=row.packet_id,
        event_slug=row.event_slug,
        event_velocity_per_hour=row.event_velocity_per_hour,
        official_source_count=row.official_source_count,
        official_source_gap=row.official_source_gap,
        independent_source_family_count=row.independent_source_family_count,
        source_family_gap=row.source_family_gap,
        contradiction_severity_score=row.contradiction_severity_score,
        probability_movement_24h=row.probability_movement_24h,
        resolution_horizon_minutes=row.resolution_horizon_minutes,
        specialist_uncertainty_score=row.specialist_uncertainty_score,
        event_velocity_pressure=row.event_velocity_pressure,
        official_source_gap_pressure=row.official_source_gap_pressure,
        source_family_independence_pressure=row.source_family_independence_pressure,
        contradiction_pressure=row.contradiction_pressure,
        probability_movement_pressure=row.probability_movement_pressure,
        resolution_horizon_pressure=row.resolution_horizon_pressure,
        specialist_uncertainty_pressure=row.specialist_uncertainty_pressure,
        priority_score=row.priority_score,
        priority_tier=row.priority_tier,
        reason_codes=row.reason_codes,
    )


def _priority_score(
    *,
    config: ResearchPacketEventSourcePriorityQueueV2Config,
    event_velocity_pressure: Decimal,
    official_source_gap_pressure: Decimal,
    source_family_independence_pressure: Decimal,
    contradiction_pressure: Decimal,
    probability_movement_pressure: Decimal,
    resolution_horizon_pressure: Decimal,
    specialist_uncertainty_pressure: Decimal,
) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return (
            event_velocity_pressure * config.event_velocity_weight
            + official_source_gap_pressure * config.official_source_gap_weight
            + source_family_independence_pressure
            * config.source_family_independence_weight
            + contradiction_pressure * config.contradiction_severity_weight
            + probability_movement_pressure * config.probability_movement_weight
            + resolution_horizon_pressure * config.resolution_horizon_weight
            + specialist_uncertainty_pressure * config.specialist_uncertainty_weight
        ).quantize(SCORE_QUANT)


def _count_gap(required_count: Decimal, actual_count: Decimal) -> Decimal:
    gap = required_count - actual_count
    if gap <= ZERO:
        return ZERO.quantize(COUNT_QUANT)
    return gap.quantize(COUNT_QUANT)


def _resolution_horizon_pressure(
    horizon_minutes: Decimal,
    config: ResearchPacketEventSourcePriorityQueueV2Config,
) -> Decimal:
    if horizon_minutes <= config.critical_resolution_horizon_minutes:
        return ONE
    if horizon_minutes > config.near_resolution_horizon_minutes:
        return ZERO
    window = config.near_resolution_horizon_minutes - (
        config.critical_resolution_horizon_minutes
    )
    if window <= ZERO:
        return ONE
    with localcontext(DECIMAL_CONTEXT):
        return _clamp_probability(
            (config.near_resolution_horizon_minutes - horizon_minutes) / window,
        )


def _row_reason_codes(
    item: ResearchPacketEventSourcePriorityQueueV2Input,
    *,
    config: ResearchPacketEventSourcePriorityQueueV2Config,
    official_gap: Decimal,
    family_gap: Decimal,
    tier: str,
) -> tuple[str, ...]:
    reasons = [f"source_priority_{tier}"]
    if item.event_velocity_per_hour >= config.high_event_velocity_per_hour:
        reasons.append("event_velocity_high")
    if official_gap > ZERO:
        reasons.append("official_source_gap_present")
    if family_gap > ZERO:
        reasons.append("source_family_gap_present")
    if item.contradiction_severity_score >= config.high_contradiction_severity_score:
        reasons.append("contradiction_severity_high")
    if item.probability_movement_24h >= config.high_probability_movement_24h:
        reasons.append("probability_movement_high")
    if item.resolution_horizon_minutes <= config.near_resolution_horizon_minutes:
        reasons.append("resolution_horizon_near")
    if item.specialist_uncertainty_score >= config.high_specialist_uncertainty_score:
        reasons.append("specialist_uncertainty_high")
    return _normalize_reason_codes("reason_codes", tuple(reasons), ROW_REASON_CODES)


def _priority_tier(
    priority_score: Decimal,
    config: ResearchPacketEventSourcePriorityQueueV2Config,
) -> str:
    if priority_score >= config.high_priority_score_floor:
        return "high"
    if priority_score >= config.medium_priority_score_floor:
        return "medium"
    return "low"


def _sort_rows(
    rows: tuple[ResearchPacketEventSourcePriorityQueueV2Row, ...],
) -> tuple[ResearchPacketEventSourcePriorityQueueV2Row, ...]:
    return tuple(
        sorted(
            rows,
            key=lambda row: (
                -row.priority_score,
                row.resolution_horizon_minutes,
                row.packet_id,
            ),
        ),
    )


def _report_status(
    rows: tuple[ResearchPacketEventSourcePriorityQueueV2Row, ...],
) -> str:
    if any(row.priority_tier == "high" for row in rows):
        return "high_priority"
    if any(row.priority_tier == "medium" for row in rows):
        return "medium_priority"
    return "low_priority"


def _report_reason_codes(
    rows: tuple[ResearchPacketEventSourcePriorityQueueV2Row, ...],
) -> tuple[str, ...]:
    if any(row.priority_tier == "high" for row in rows):
        reasons = ["source_priority_high_present"]
    elif any(row.priority_tier == "medium" for row in rows):
        reasons = ["source_priority_medium_present"]
    else:
        reasons = ["source_priority_low_only"]
    for reason in ROW_REASON_CODES[3:]:
        if any(reason in row.reason_codes for row in rows):
            reasons.append(reason)
    return _normalize_reason_codes("reason_codes", tuple(reasons), REPORT_REASON_CODES)


def _normalize_inputs(
    value: object,
) -> tuple[ResearchPacketEventSourcePriorityQueueV2Input, ...]:
    try:
        rows = tuple(value)  # type: ignore[arg-type]
    except TypeError as exc:
        raise ValueError("inputs must be iterable") from exc
    for row in rows:
        _require_exact_type("input", row, ResearchPacketEventSourcePriorityQueueV2Input)
        _require_hard_flags("input", row)
    packet_ids = tuple(row.packet_id for row in rows)
    if len(set(packet_ids)) != len(packet_ids):
        raise ValueError("inputs must not contain duplicate packet_id")
    return rows


def _normalize_rows(
    value: object,
) -> tuple[ResearchPacketEventSourcePriorityQueueV2Row, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("rows must be a list or tuple")
    rows = tuple(value)
    for row in rows:
        _require_exact_type("row", row, ResearchPacketEventSourcePriorityQueueV2Row)
        _require_hard_flags("row", row)
    if rows != _sort_rows(rows):
        raise ValueError("rows must be sorted by priority_score")
    expected_ranks = tuple(_decimal_count(index) for index in range(1, len(rows) + 1))
    if tuple(row.row_rank for row in rows) != expected_ranks:
        raise ValueError("row_rank values must be sequential")
    return rows


def _validate_config(config: ResearchPacketEventSourcePriorityQueueV2Config) -> None:
    with localcontext(DECIMAL_CONTEXT):
        weight_total = (
            config.event_velocity_weight
            + config.official_source_gap_weight
            + config.source_family_independence_weight
            + config.contradiction_severity_weight
            + config.probability_movement_weight
            + config.resolution_horizon_weight
            + config.specialist_uncertainty_weight
        ).quantize(SCORE_QUANT)
    if weight_total != ONE:
        raise ValueError("weights must sum to 1.000000")
    if config.critical_resolution_horizon_minutes > config.near_resolution_horizon_minutes:
        raise ValueError(
            "critical_resolution_horizon_minutes must be <= near_resolution_horizon_minutes",
        )
    if config.medium_priority_score_floor > config.high_priority_score_floor:
        raise ValueError("medium_priority_score_floor must be <= high_priority_score_floor")


def _validate_row(row: ResearchPacketEventSourcePriorityQueueV2Row) -> None:
    if row.official_source_gap != row.official_source_gap.to_integral_value():
        raise ValueError("official_source_gap must be integral")
    if row.source_family_gap != row.source_family_gap.to_integral_value():
        raise ValueError("source_family_gap must be integral")
    if row.priority_tier not in row.reason_codes[0]:
        raise ValueError("priority_tier must match reason_codes")


def _validate_report(report: ResearchPacketEventSourcePriorityQueueV2Report) -> None:
    rows = report.rows
    if report.packet_count != _decimal_count(len(rows)):
        raise ValueError("packet_count must match rows")
    if report.high_priority_packet_count != _tier_count(rows, "high"):
        raise ValueError("high_priority_packet_count must match rows")
    if report.medium_priority_packet_count != _tier_count(rows, "medium"):
        raise ValueError("medium_priority_packet_count must match rows")
    if report.low_priority_packet_count != _tier_count(rows, "low"):
        raise ValueError("low_priority_packet_count must match rows")
    if (
        report.high_priority_packet_count
        + report.medium_priority_packet_count
        + report.low_priority_packet_count
        != report.packet_count
    ):
        raise ValueError("priority counts must sum to packet_count")
    if report.event_velocity_count != _reason_count(rows, "event_velocity_high"):
        raise ValueError("event_velocity_count must match rows")
    if report.official_source_gap_count != _reason_count(
        rows,
        "official_source_gap_present",
    ):
        raise ValueError("official_source_gap_count must match rows")
    if report.source_family_gap_count != _reason_count(
        rows,
        "source_family_gap_present",
    ):
        raise ValueError("source_family_gap_count must match rows")
    if report.contradiction_severity_count != _reason_count(
        rows,
        "contradiction_severity_high",
    ):
        raise ValueError("contradiction_severity_count must match rows")
    if report.probability_movement_count != _reason_count(
        rows,
        "probability_movement_high",
    ):
        raise ValueError("probability_movement_count must match rows")
    if report.near_resolution_horizon_count != _reason_count(
        rows,
        "resolution_horizon_near",
    ):
        raise ValueError("near_resolution_horizon_count must match rows")
    if report.specialist_uncertainty_count != _reason_count(
        rows,
        "specialist_uncertainty_high",
    ):
        raise ValueError("specialist_uncertainty_count must match rows")
    if report.max_priority_score != max((row.priority_score for row in rows), default=ZERO):
        raise ValueError("max_priority_score must match rows")
    if report.report_status != _report_status(rows):
        raise ValueError("report_status must match rows")
    if report.reason_codes != _report_reason_codes(rows):
        raise ValueError("reason_codes must match rows")


def _validate_report_digest(
    report: ResearchPacketEventSourcePriorityQueueV2Report,
) -> None:
    if report.derived_validation_digest != _derived_validation_digest(asdict(report)):
        raise ValueError("derived_validation_digest mismatch")


def _validate_public_payload_digest(payload: dict[str, object]) -> None:
    digest = payload.get("derived_validation_digest")
    if type(digest) is not str:
        raise ValueError("derived_validation_digest must be a string")
    _require_sha256_digest("derived_validation_digest", digest)
    if digest != _derived_validation_digest(payload):
        raise ValueError("derived_validation_digest mismatch")


def _tier_count(
    rows: tuple[ResearchPacketEventSourcePriorityQueueV2Row, ...],
    tier: str,
) -> Decimal:
    return _decimal_count(sum(1 for row in rows if row.priority_tier == tier))


def _reason_count(
    rows: tuple[ResearchPacketEventSourcePriorityQueueV2Row, ...],
    reason_code: str,
) -> Decimal:
    return _decimal_count(sum(1 for row in rows if reason_code in row.reason_codes))


def _decimal_count(value: int) -> Decimal:
    return Decimal(value).quantize(COUNT_QUANT)


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_exact_type(
    field_name: str,
    value: object,
    expected_type: type[object],
) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{field_name} must be exactly {expected_type.__name__}")


def _require_public_string(field_name: str, value: object) -> str:
    if type(value) is not str or not value:
        raise ValueError(f"{field_name} must be a non-empty string")
    if value.strip() != value:
        raise ValueError(f"{field_name} must not contain leading or trailing whitespace")
    _reject_unsafe_public_text(field_name, value, is_key=False)
    return value


def _require_member(
    field_name: str,
    value: object,
    allowed: tuple[str, ...],
) -> str:
    if type(value) is not str or value not in allowed:
        raise ValueError(f"{field_name} must be one of {allowed}")
    return value


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return value


def _require_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    value = _require_decimal(field_name, value)
    if value < ZERO:
        raise ValueError(f"{field_name} must be >= 0")
    return value.quantize(SCORE_QUANT)


def _require_positive_decimal(field_name: str, value: object) -> Decimal:
    value = _require_nonnegative_decimal(field_name, value)
    if value <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return value


def _require_probability(field_name: str, value: object) -> Decimal:
    value = _require_decimal(field_name, value)
    if value < ZERO:
        raise ValueError(f"{field_name} must be >= 0")
    if value > ONE:
        raise ValueError(f"{field_name} must be <= 1.000000")
    return value.quantize(SCORE_QUANT)


def _require_nonnegative_count_decimal(field_name: str, value: object) -> Decimal:
    value = _require_decimal(field_name, value)
    if value < ZERO:
        raise ValueError(f"{field_name} must be >= 0")
    if value != value.to_integral_value():
        raise ValueError(f"{field_name} must be integral")
    return value.quantize(COUNT_QUANT)


def _require_positive_count_decimal(field_name: str, value: object) -> Decimal:
    value = _require_nonnegative_count_decimal(field_name, value)
    if value <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return value


def _require_sha256_digest(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if len(value) != 64 or any(char not in "0123456789abcdef" for char in value):
        raise ValueError(f"{field_name} must be a sha256 digest")
    return value


def _require_hard_flags(field_name: str, value: object) -> None:
    if getattr(value, "paper_only", None) is not True:
        raise ValueError(f"paper_only must be True for {field_name}")
    if getattr(value, "report_only", None) is not True:
        raise ValueError(f"report_only must be True for {field_name}")
    if getattr(value, "readonly", None) is not True:
        raise ValueError(f"readonly must be True for {field_name}")


def _normalize_reason_codes(
    field_name: str,
    value: object,
    allowed: tuple[str, ...],
) -> tuple[str, ...]:
    if type(value) is not tuple or not value:
        raise ValueError(f"{field_name} must be a non-empty tuple")
    normalized = tuple(_require_public_string(field_name, item) for item in value)
    if len(set(normalized)) != len(normalized):
        raise ValueError(f"{field_name} must not contain duplicates")
    if any(item not in allowed for item in normalized):
        raise ValueError(f"{field_name} must contain known reason codes")
    return normalized


def _capped_ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator <= ZERO:
        raise ValueError("denominator must be positive")
    with localcontext(DECIMAL_CONTEXT):
        return _clamp_probability(numerator / denominator)


def _clamp_probability(value: Decimal) -> Decimal:
    if value < ZERO:
        return ZERO
    if value > ONE:
        return ONE
    return value.quantize(SCORE_QUANT)


def _payload_value(value: object) -> object:
    if hasattr(value, "__dataclass_fields__") and not isinstance(value, type):
        return _payload_value(asdict(value))
    if type(value) is Decimal:
        if not value.is_finite():
            raise ValueError("payload Decimal must be finite")
        return str(value)
    if type(value) is datetime:
        return _as_utc("payload datetime", value).isoformat()
    if type(value) is dict:
        return {key: _payload_value(item) for key, item in value.items()}
    if type(value) is tuple:
        return [_payload_value(item) for item in value]
    if type(value) is list:
        return [_payload_value(item) for item in value]
    if value is None or type(value) in (str, bool):
        return value
    raise ValueError("payload contains unsupported value")


def _derived_validation_digest(values: dict[str, object]) -> str:
    digest_payload = {
        key: _payload_value(item)
        for key, item in values.items()
        if key != "derived_validation_digest"
    }
    _reject_unsafe_public_payload("derived validation digest payload", digest_payload)
    encoded = json.dumps(
        digest_payload,
        allow_nan=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return sha256(encoded).hexdigest()


def _reject_unsafe_public_payload(label: str, value: object) -> None:
    if type(value) is dict:
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError(f"unsafe public key in {label}")
            _reject_unsafe_public_text(label, key, is_key=True)
            _reject_unsafe_public_payload(label, item)
        return
    if type(value) in (list, tuple):
        for item in value:
            _reject_unsafe_public_payload(label, item)
        return
    if type(value) in (float, int):
        raise ValueError(f"unsafe public value in {label}")
    if type(value) is str:
        _reject_unsafe_public_text(label, value, is_key=False)


def _reject_unsafe_public_text(label: str, value: str, *, is_key: bool) -> None:
    normalized = value.lower()
    if any(fragment in normalized for fragment in UNSAFE_PUBLIC_TEXT_FRAGMENTS):
        kind = "key" if is_key else "value"
        raise ValueError(f"unsafe public {kind} in {label}")


def _require_public_payload_fields(payload: dict[str, object]) -> None:
    if tuple(payload.keys()) != REPORT_PAYLOAD_FIELDS:
        raise ValueError("payload fields mismatch")
    rows = payload["rows"]
    if type(rows) is not list:
        raise ValueError("payload rows must be a list")
    for row in rows:
        if type(row) is not dict:
            raise ValueError("payload rows must contain dicts")
        if tuple(row.keys()) != ROW_PAYLOAD_FIELDS:
            raise ValueError("payload row fields mismatch")
    if payload["paper_only"] is not True:
        raise ValueError("paper_only must be True for payload")
    if payload["report_only"] is not True:
        raise ValueError("report_only must be True for payload")
    if payload["readonly"] is not True:
        raise ValueError("readonly must be True for payload")


def _copy_json_object(value: dict[str, object]) -> dict[str, object]:
    copied = json.loads(
        json.dumps(value, allow_nan=False, separators=(",", ":"), sort_keys=True),
    )
    if type(copied) is not dict:
        raise ValueError("payload must be a dict")
    return copied
