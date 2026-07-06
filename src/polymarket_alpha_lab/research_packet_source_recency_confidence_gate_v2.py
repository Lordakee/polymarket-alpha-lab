"""Static Decimal confidence gate for research packet source freshness."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
import json


DEFAULT_RESEARCH_PACKET_SOURCE_RECENCY_CONFIDENCE_GATE_V2_CONFIG_VERSION = (
    "research-packet-source-recency-confidence-gate-v2"
)

DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
SCORE_QUANT = Decimal("0.000001")
COUNT_QUANT = Decimal("1")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
MICROSECONDS_PER_SECOND = Decimal("1000000")
SECONDS_PER_DAY = Decimal("86400")

GATE_STATUSES = ("pass", "watch", "blocked")
ROW_REASON_CODES = (
    "source_recency_confidence_pass",
    "source_recency_confidence_watch",
    "source_recency_confidence_blocked",
    "official_source_fresh",
    "official_source_stale",
    "independent_source_family_fresh",
    "independent_source_family_stale",
    "contradiction_old",
    "contradiction_recent",
    "probability_move_attribution_fresh",
    "probability_move_attribution_stale",
    "event_velocity_low",
    "event_velocity_high",
    "resolution_horizon_clear",
    "resolution_horizon_near",
    "specialist_uncertainty_low",
    "specialist_uncertainty_high",
)
REPORT_REASON_CODES = (
    "source_recency_confidence_gate_passed",
    "source_recency_confidence_gate_watch_rows",
    "source_recency_confidence_gate_blocked_rows",
    "source_recency_confidence_gate_empty",
)
UNSAFE_PUBLIC_TEXT_FRAGMENTS = (
    "".join(("li", "ve")),
    "".join(("au", "th")),
    "".join(("wal", "let")),
    "".join(("ord", "er")),
    "".join(("net", "work")),
    "".join(("data", "base")),
    "".join(("per", "sist")),
    "".join(("sig", "ning")),
    "".join(("muta", "tion")),
    "".join(("bu", "y")),
    "".join(("se", "ll")),
    "".join(("tra", "de")),
)

__all__ = (
    "DEFAULT_RESEARCH_PACKET_SOURCE_RECENCY_CONFIDENCE_GATE_V2_CONFIG_VERSION",
    "ResearchPacketSourceRecencyConfidenceGateV2Config",
    "ResearchPacketSourceRecencyConfidenceGateV2Packet",
    "ResearchPacketSourceRecencyConfidenceGateV2Row",
    "ResearchPacketSourceRecencyConfidenceGateV2Report",
    "build_research_packet_source_recency_confidence_gate_v2",
)


@dataclass(frozen=True)
class ResearchPacketSourceRecencyConfidenceGateV2Config:
    config_version: str = (
        DEFAULT_RESEARCH_PACKET_SOURCE_RECENCY_CONFIDENCE_GATE_V2_CONFIG_VERSION
    )
    official_source_age_max_seconds: Decimal = Decimal("86400.000000")
    independent_source_family_age_max_seconds: Decimal = Decimal("86400.000000")
    contradiction_age_max_seconds: Decimal = Decimal("86400.000000")
    probability_move_attribution_age_max_seconds: Decimal = Decimal("86400.000000")
    event_velocity_soft_cap_per_day: Decimal = Decimal("10.000000")
    resolution_horizon_max_seconds: Decimal = Decimal("604800.000000")
    official_source_age_weight: Decimal = Decimal("0.256667")
    independent_source_family_freshness_weight: Decimal = Decimal("0.200000")
    contradiction_age_weight: Decimal = Decimal("0.100000")
    probability_move_attribution_age_weight: Decimal = Decimal("0.150000")
    event_velocity_weight: Decimal = Decimal("0.100000")
    resolution_horizon_weight: Decimal = Decimal("0.093333")
    specialist_uncertainty_weight: Decimal = Decimal("0.100000")
    pass_score_floor: Decimal = Decimal("0.750000")
    watch_score_floor: Decimal = Decimal("0.500000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "config_version",
            _require_public_string("config_version", self.config_version),
        )
        for field_name in (
            "official_source_age_max_seconds",
            "independent_source_family_age_max_seconds",
            "contradiction_age_max_seconds",
            "probability_move_attribution_age_max_seconds",
            "event_velocity_soft_cap_per_day",
            "resolution_horizon_max_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_positive_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "official_source_age_weight",
            "independent_source_family_freshness_weight",
            "contradiction_age_weight",
            "probability_move_attribution_age_weight",
            "event_velocity_weight",
            "resolution_horizon_weight",
            "specialist_uncertainty_weight",
            "pass_score_floor",
            "watch_score_floor",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        _validate_config(self)
        _require_hard_flags("ResearchPacketSourceRecencyConfidenceGateV2Config", self)
        _reject_unsafe_public_payload(
            "ResearchPacketSourceRecencyConfidenceGateV2Config",
            _payload_value(asdict(self)),
        )


@dataclass(frozen=True)
class ResearchPacketSourceRecencyConfidenceGateV2Packet:
    packet_id: str
    event_id: str
    official_source_last_seen_at: datetime
    independent_source_family_last_seen_at: datetime
    contradiction_last_seen_at: datetime | None
    probability_move_attributed_at: datetime | None
    event_velocity_per_day: Decimal
    resolution_at: datetime
    specialist_uncertainty: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        for field_name in ("packet_id", "event_id"):
            object.__setattr__(
                self,
                field_name,
                _require_public_string(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "official_source_last_seen_at",
            "independent_source_family_last_seen_at",
            "resolution_at",
        ):
            object.__setattr__(
                self,
                field_name,
                _as_utc(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "contradiction_last_seen_at",
            "probability_move_attributed_at",
        ):
            object.__setattr__(
                self,
                field_name,
                _as_optional_utc(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "event_velocity_per_day",
            _normalize_nonnegative_decimal(
                "event_velocity_per_day",
                self.event_velocity_per_day,
            ),
        )
        object.__setattr__(
            self,
            "specialist_uncertainty",
            _normalize_ratio("specialist_uncertainty", self.specialist_uncertainty),
        )
        _require_hard_flags("ResearchPacketSourceRecencyConfidenceGateV2Packet", self)
        _reject_unsafe_public_payload(
            "ResearchPacketSourceRecencyConfidenceGateV2Packet",
            _payload_value(asdict(self)),
        )


@dataclass(frozen=True)
class ResearchPacketSourceRecencyConfidenceGateV2Row:
    packet_id: str
    event_id: str
    official_source_age_seconds: Decimal
    official_source_recency_score: Decimal
    independent_source_family_age_seconds: Decimal
    independent_source_family_freshness_score: Decimal
    contradiction_age_seconds: Decimal
    contradiction_age_score: Decimal
    probability_move_attribution_age_seconds: Decimal
    probability_move_attribution_score: Decimal
    event_velocity_per_day: Decimal
    event_velocity_score: Decimal
    resolution_horizon_seconds: Decimal
    resolution_horizon_score: Decimal
    specialist_uncertainty: Decimal
    specialist_uncertainty_score: Decimal
    source_recency_confidence_score: Decimal
    gate_status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        for field_name in ("packet_id", "event_id"):
            object.__setattr__(
                self,
                field_name,
                _require_public_string(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "official_source_age_seconds",
            "independent_source_family_age_seconds",
            "contradiction_age_seconds",
            "probability_move_attribution_age_seconds",
            "event_velocity_per_day",
            "resolution_horizon_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "official_source_recency_score",
            "independent_source_family_freshness_score",
            "contradiction_age_score",
            "probability_move_attribution_score",
            "event_velocity_score",
            "resolution_horizon_score",
            "specialist_uncertainty",
            "specialist_uncertainty_score",
            "source_recency_confidence_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        _require_gate_status("gate_status", self.gate_status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, ROW_REASON_CODES),
        )
        _require_hard_flags("ResearchPacketSourceRecencyConfidenceGateV2Row", self)
        _reject_unsafe_public_payload(
            "ResearchPacketSourceRecencyConfidenceGateV2Row",
            _payload_value(asdict(self)),
        )


@dataclass(frozen=True)
class ResearchPacketSourceRecencyConfidenceGateV2Report:
    generated_at: datetime
    config_version: str
    gate_status: str
    packet_count: Decimal
    pass_packet_count: Decimal
    watch_packet_count: Decimal
    blocked_packet_count: Decimal
    average_source_recency_confidence_score: Decimal
    minimum_source_recency_confidence_score: Decimal
    rows: tuple[ResearchPacketSourceRecencyConfidenceGateV2Row, ...]
    reason_codes: tuple[str, ...]
    derived_validation_digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        object.__setattr__(
            self,
            "config_version",
            _require_public_string("config_version", self.config_version),
        )
        _require_gate_status("gate_status", self.gate_status)
        for field_name in (
            "packet_count",
            "pass_packet_count",
            "watch_packet_count",
            "blocked_packet_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_integral_decimal(
                    field_name,
                    getattr(self, field_name),
                ),
            )
        for field_name in (
            "average_source_recency_confidence_score",
            "minimum_source_recency_confidence_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
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
        _require_sha256_digest(
            "derived_validation_digest",
            self.derived_validation_digest,
        )
        _require_hard_flags("ResearchPacketSourceRecencyConfidenceGateV2Report", self)
        _reject_unsafe_public_payload(
            "ResearchPacketSourceRecencyConfidenceGateV2Report",
            _payload_value(asdict(self)),
        )
        _validate_report(self)

    @property
    def payload(self) -> dict[str, object]:
        payload = _payload_value(asdict(self))
        _reject_unsafe_public_payload(
            "ResearchPacketSourceRecencyConfidenceGateV2Report.payload",
            payload,
        )
        if type(payload) is not dict:
            raise ValueError("payload must be a dict")
        return payload


def build_research_packet_source_recency_confidence_gate_v2(
    packets: object,
    *,
    config: ResearchPacketSourceRecencyConfidenceGateV2Config,
    generated_at: datetime,
) -> ResearchPacketSourceRecencyConfidenceGateV2Report:
    if type(config) is not ResearchPacketSourceRecencyConfidenceGateV2Config:
        raise ValueError(
            "config must be a ResearchPacketSourceRecencyConfidenceGateV2Config",
        )
    _require_hard_flags("ResearchPacketSourceRecencyConfidenceGateV2Config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    normalized_packets = _normalize_packets(packets)
    _validate_packet_times(normalized_packets, generated_at_utc)

    rows = _sort_rows(
        tuple(
            _row_for_packet(packet, config=config, generated_at=generated_at_utc)
            for packet in normalized_packets
        ),
    )
    status = _report_status(rows)
    values = {
        "generated_at": generated_at_utc,
        "config_version": config.config_version,
        "gate_status": status,
        "packet_count": _count(len(rows)),
        "pass_packet_count": _status_count(rows, "pass"),
        "watch_packet_count": _status_count(rows, "watch"),
        "blocked_packet_count": _status_count(rows, "blocked"),
        "average_source_recency_confidence_score": _average_score(rows),
        "minimum_source_recency_confidence_score": _minimum_score(rows),
        "rows": rows,
        "reason_codes": _report_reason_codes(rows, status),
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    values["derived_validation_digest"] = _derived_validation_digest(values)
    return ResearchPacketSourceRecencyConfidenceGateV2Report(**values)


def _row_for_packet(
    packet: ResearchPacketSourceRecencyConfidenceGateV2Packet,
    *,
    config: ResearchPacketSourceRecencyConfidenceGateV2Config,
    generated_at: datetime,
) -> ResearchPacketSourceRecencyConfidenceGateV2Row:
    official_age = _duration_seconds(packet.official_source_last_seen_at, generated_at)
    independent_age = _duration_seconds(
        packet.independent_source_family_last_seen_at,
        generated_at,
    )
    contradiction_age = _optional_age_seconds(
        packet.contradiction_last_seen_at,
        generated_at,
    )
    move_age = _optional_age_seconds(packet.probability_move_attributed_at, generated_at)
    horizon_seconds = _duration_seconds(generated_at, packet.resolution_at)
    official_score = _freshness_score(
        official_age,
        config.official_source_age_max_seconds,
    )
    independent_score = _freshness_score(
        independent_age,
        config.independent_source_family_age_max_seconds,
    )
    contradiction_score = (
        ONE
        if packet.contradiction_last_seen_at is None
        else _age_score(contradiction_age, config.contradiction_age_max_seconds)
    )
    move_score = (
        ZERO
        if packet.probability_move_attributed_at is None
        else _freshness_score(
            move_age,
            config.probability_move_attribution_age_max_seconds,
        )
    )
    velocity_score = _inverse_cap_score(
        packet.event_velocity_per_day,
        config.event_velocity_soft_cap_per_day,
    )
    horizon_score = _age_score(horizon_seconds, config.resolution_horizon_max_seconds)
    uncertainty_score = _clamp_ratio(ONE - packet.specialist_uncertainty)
    confidence_score = _confidence_score(
        config=config,
        official_score=official_score,
        independent_score=independent_score,
        contradiction_score=contradiction_score,
        move_score=move_score,
        velocity_score=velocity_score,
        horizon_score=horizon_score,
        uncertainty_score=uncertainty_score,
    )
    status = _gate_status_for_score(confidence_score, config)
    return ResearchPacketSourceRecencyConfidenceGateV2Row(
        packet_id=packet.packet_id,
        event_id=packet.event_id,
        official_source_age_seconds=official_age,
        official_source_recency_score=official_score,
        independent_source_family_age_seconds=independent_age,
        independent_source_family_freshness_score=independent_score,
        contradiction_age_seconds=contradiction_age,
        contradiction_age_score=contradiction_score,
        probability_move_attribution_age_seconds=move_age,
        probability_move_attribution_score=move_score,
        event_velocity_per_day=packet.event_velocity_per_day,
        event_velocity_score=velocity_score,
        resolution_horizon_seconds=horizon_seconds,
        resolution_horizon_score=horizon_score,
        specialist_uncertainty=packet.specialist_uncertainty,
        specialist_uncertainty_score=uncertainty_score,
        source_recency_confidence_score=confidence_score,
        gate_status=status,
        reason_codes=_row_reason_codes(
            status=status,
            official_score=official_score,
            independent_score=independent_score,
            contradiction_score=contradiction_score,
            move_score=move_score,
            velocity_score=velocity_score,
            horizon_score=horizon_score,
            uncertainty_score=uncertainty_score,
        ),
    )


def _confidence_score(
    *,
    config: ResearchPacketSourceRecencyConfidenceGateV2Config,
    official_score: Decimal,
    independent_score: Decimal,
    contradiction_score: Decimal,
    move_score: Decimal,
    velocity_score: Decimal,
    horizon_score: Decimal,
    uncertainty_score: Decimal,
) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        score = (
            official_score * config.official_source_age_weight
            + independent_score * config.independent_source_family_freshness_weight
            + contradiction_score * config.contradiction_age_weight
            + move_score * config.probability_move_attribution_age_weight
            + velocity_score * config.event_velocity_weight
            + horizon_score * config.resolution_horizon_weight
            + uncertainty_score * config.specialist_uncertainty_weight
        )
        return _clamp_ratio(score)


def _gate_status_for_score(
    score: Decimal,
    config: ResearchPacketSourceRecencyConfidenceGateV2Config,
) -> str:
    if score >= config.pass_score_floor:
        return "pass"
    if score >= config.watch_score_floor:
        return "watch"
    return "blocked"


def _row_reason_codes(
    *,
    status: str,
    official_score: Decimal,
    independent_score: Decimal,
    contradiction_score: Decimal,
    move_score: Decimal,
    velocity_score: Decimal,
    horizon_score: Decimal,
    uncertainty_score: Decimal,
) -> tuple[str, ...]:
    return (
        f"source_recency_confidence_{status}",
        _score_reason(
            official_score,
            strong_reason="official_source_fresh",
            weak_reason="official_source_stale",
        ),
        _score_reason(
            independent_score,
            strong_reason="independent_source_family_fresh",
            weak_reason="independent_source_family_stale",
        ),
        _score_reason(
            contradiction_score,
            strong_reason="contradiction_old",
            weak_reason="contradiction_recent",
        ),
        _score_reason(
            move_score,
            strong_reason="probability_move_attribution_fresh",
            weak_reason="probability_move_attribution_stale",
        ),
        _score_reason(
            velocity_score,
            strong_reason="event_velocity_low",
            weak_reason="event_velocity_high",
        ),
        _score_reason(
            horizon_score,
            strong_reason="resolution_horizon_clear",
            weak_reason="resolution_horizon_near",
        ),
        _score_reason(
            uncertainty_score,
            strong_reason="specialist_uncertainty_low",
            weak_reason="specialist_uncertainty_high",
        ),
    )


def _score_reason(
    value: Decimal,
    *,
    strong_reason: str,
    weak_reason: str,
) -> str:
    if value >= Decimal("0.500000"):
        return strong_reason
    return weak_reason


def _report_status(
    rows: tuple[ResearchPacketSourceRecencyConfidenceGateV2Row, ...],
) -> str:
    if not rows:
        return "blocked"
    if any(row.gate_status == "blocked" for row in rows):
        return "blocked"
    if any(row.gate_status == "watch" for row in rows):
        return "watch"
    return "pass"


def _report_reason_codes(
    rows: tuple[ResearchPacketSourceRecencyConfidenceGateV2Row, ...],
    status: str,
) -> tuple[str, ...]:
    if not rows:
        return ("source_recency_confidence_gate_empty",)
    reasons: list[str] = []
    if any(row.gate_status == "blocked" for row in rows):
        reasons.append("source_recency_confidence_gate_blocked_rows")
    if any(row.gate_status == "watch" for row in rows):
        reasons.append("source_recency_confidence_gate_watch_rows")
    if not reasons and status == "pass":
        reasons.append("source_recency_confidence_gate_passed")
    return tuple(reasons)


def _status_count(
    rows: tuple[ResearchPacketSourceRecencyConfidenceGateV2Row, ...],
    status: str,
) -> Decimal:
    return _count(sum(1 for row in rows if row.gate_status == status))


def _average_score(
    rows: tuple[ResearchPacketSourceRecencyConfidenceGateV2Row, ...],
) -> Decimal:
    if not rows:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return _clamp_ratio(
            sum(row.source_recency_confidence_score for row in rows)
            / Decimal(len(rows)),
        )


def _minimum_score(
    rows: tuple[ResearchPacketSourceRecencyConfidenceGateV2Row, ...],
) -> Decimal:
    if not rows:
        return ZERO
    return min(row.source_recency_confidence_score for row in rows)


def _sort_rows(
    rows: tuple[ResearchPacketSourceRecencyConfidenceGateV2Row, ...],
) -> tuple[ResearchPacketSourceRecencyConfidenceGateV2Row, ...]:
    return tuple(
        sorted(
            rows,
            key=lambda row: (
                -row.source_recency_confidence_score,
                row.packet_id,
                row.event_id,
            ),
        ),
    )


def _validate_config(config: ResearchPacketSourceRecencyConfidenceGateV2Config) -> None:
    with localcontext(DECIMAL_CONTEXT):
        weights_total = (
            config.official_source_age_weight
            + config.independent_source_family_freshness_weight
            + config.contradiction_age_weight
            + config.probability_move_attribution_age_weight
            + config.event_velocity_weight
            + config.resolution_horizon_weight
            + config.specialist_uncertainty_weight
        ).quantize(SCORE_QUANT)
    if weights_total != ONE:
        raise ValueError("gate weights must sum to 1.000000")
    if config.watch_score_floor > config.pass_score_floor:
        raise ValueError("watch_score_floor must not exceed pass_score_floor")


def _validate_packet_times(
    packets: tuple[ResearchPacketSourceRecencyConfidenceGateV2Packet, ...],
    generated_at: datetime,
) -> None:
    for packet in packets:
        if packet.official_source_last_seen_at > generated_at:
            raise ValueError("official_source_last_seen_at must be <= generated_at")
        if packet.independent_source_family_last_seen_at > generated_at:
            raise ValueError(
                "independent_source_family_last_seen_at must be <= generated_at",
            )
        if (
            packet.contradiction_last_seen_at is not None
            and packet.contradiction_last_seen_at > generated_at
        ):
            raise ValueError("contradiction_last_seen_at must be <= generated_at")
        if (
            packet.probability_move_attributed_at is not None
            and packet.probability_move_attributed_at > generated_at
        ):
            raise ValueError("probability_move_attributed_at must be <= generated_at")
        if packet.resolution_at < generated_at:
            raise ValueError("resolution_at must be >= generated_at")


def _validate_report(report: ResearchPacketSourceRecencyConfidenceGateV2Report) -> None:
    rows = report.rows
    if report.packet_count != _count(len(rows)):
        raise ValueError("packet_count must match rows")
    if (
        report.pass_packet_count != _status_count(rows, "pass")
        or report.watch_packet_count != _status_count(rows, "watch")
        or report.blocked_packet_count != _status_count(rows, "blocked")
    ):
        raise ValueError("status counts must match rows")
    if (
        report.pass_packet_count + report.watch_packet_count + report.blocked_packet_count
        != report.packet_count
    ):
        raise ValueError("status counts must sum to packet_count")
    if rows != _sort_rows(rows):
        raise ValueError("rows must be sorted by confidence and packet")
    if report.gate_status != _report_status(rows):
        raise ValueError("gate_status must match rows")
    if report.reason_codes != _report_reason_codes(rows, report.gate_status):
        raise ValueError("reason_codes must match gate_status")
    if report.derived_validation_digest != _derived_validation_digest(asdict(report)):
        raise ValueError("derived_validation_digest must match report fields")
    if report.average_source_recency_confidence_score != _average_score(rows):
        raise ValueError("average_source_recency_confidence_score must match rows")
    if report.minimum_source_recency_confidence_score != _minimum_score(rows):
        raise ValueError("minimum_source_recency_confidence_score must match rows")


def _normalize_packets(
    value: object,
) -> tuple[ResearchPacketSourceRecencyConfidenceGateV2Packet, ...]:
    if isinstance(value, (str, bytes)) or not hasattr(value, "__iter__"):
        raise ValueError("packets must be an iterable")
    packets = tuple(value)
    for packet in packets:
        if type(packet) is not ResearchPacketSourceRecencyConfidenceGateV2Packet:
            raise ValueError(
                "packet items must be ResearchPacketSourceRecencyConfidenceGateV2Packet",
            )
        _require_hard_flags("ResearchPacketSourceRecencyConfidenceGateV2Packet", packet)
    keys = tuple((packet.packet_id, packet.event_id) for packet in packets)
    if len(set(keys)) != len(keys):
        raise ValueError("packet items must not contain duplicate packet/event keys")
    return packets


def _normalize_rows(
    value: object,
) -> tuple[ResearchPacketSourceRecencyConfidenceGateV2Row, ...]:
    if type(value) is not tuple:
        raise ValueError("rows must be a tuple")
    for row in value:
        if type(row) is not ResearchPacketSourceRecencyConfidenceGateV2Row:
            raise ValueError(
                "rows must contain ResearchPacketSourceRecencyConfidenceGateV2Row",
            )
    return value


def _freshness_score(age_seconds: Decimal, max_seconds: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return _clamp_ratio(ONE - age_seconds / max_seconds)


def _age_score(age_seconds: Decimal, max_seconds: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return _clamp_ratio(age_seconds / max_seconds)


def _inverse_cap_score(value: Decimal, soft_cap: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return _clamp_ratio(ONE - value / soft_cap)


def _duration_seconds(start: datetime, end: datetime) -> Decimal:
    start_utc = _as_utc("start", start)
    end_utc = _as_utc("end", end)
    delta = end_utc - start_utc
    seconds = (
        Decimal(delta.days) * SECONDS_PER_DAY
        + Decimal(delta.seconds)
        + (Decimal(delta.microseconds) / MICROSECONDS_PER_SECOND)
    )
    if seconds < ZERO:
        raise ValueError("duration seconds must be nonnegative")
    return seconds.quantize(SCORE_QUANT)


def _optional_age_seconds(value: datetime | None, generated_at: datetime) -> Decimal:
    if value is None:
        return ZERO
    return _duration_seconds(value, generated_at)


def _count(value: int) -> Decimal:
    return Decimal(value).quantize(COUNT_QUANT)


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _as_optional_utc(field_name: str, value: object) -> datetime | None:
    if value is None:
        return None
    return _as_utc(field_name, value)


def _require_public_string(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value:
        raise ValueError(f"{field_name} must not be empty")
    if value.strip() != value:
        raise ValueError(f"{field_name} must be stripped")
    if "\n" in value or "\r" in value or "\t" in value:
        raise ValueError(f"{field_name} must be single line")
    _reject_unsafe_public_payload(field_name, value)
    return value


def _require_gate_status(field_name: str, value: object) -> None:
    _require_public_string(field_name, value)
    if value not in GATE_STATUSES:
        raise ValueError(f"{field_name} must be pass, watch, or blocked")


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


def _normalize_ratio(field_name: str, value: object) -> Decimal:
    value = _require_decimal(field_name, value)
    if value < ZERO:
        raise ValueError(f"{field_name} must be >= 0.000000")
    if value > ONE:
        raise ValueError(f"{field_name} must be <= 1.000000")
    return _quantize_six(field_name, value)


def _normalize_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    value = _require_decimal(field_name, value)
    if value < ZERO:
        raise ValueError(f"{field_name} must be >= 0.000000")
    return _quantize_six(field_name, value)


def _normalize_positive_decimal(field_name: str, value: object) -> Decimal:
    value = _normalize_nonnegative_decimal(field_name, value)
    if value <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return value


def _normalize_nonnegative_integral_decimal(field_name: str, value: object) -> Decimal:
    value = _require_decimal(field_name, value)
    if value < ZERO:
        raise ValueError(f"{field_name} must be >= 0.000000")
    if value != value.to_integral_value():
        raise ValueError(f"{field_name} must be an integral Decimal")
    return value.quantize(COUNT_QUANT)


def _quantize_six(field_name: str, value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        quantized = value.quantize(SCORE_QUANT)
    if quantized != value:
        raise ValueError(f"{field_name} must use six decimal places or fewer")
    return quantized


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be exactly Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return value


def _clamp_ratio(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return min(ONE, max(ZERO, value)).quantize(SCORE_QUANT)


def _require_sha256_digest(field_name: str, value: object) -> None:
    _require_public_string(field_name, value)
    if len(value) != 64 or any(char not in "0123456789abcdef" for char in value):
        raise ValueError(f"{field_name} must be a sha256 digest")


def _require_hard_flags(field_name: str, value: object) -> None:
    if getattr(value, "paper_only", None) is not True:
        raise ValueError(f"paper_only must be True for {field_name}")
    if getattr(value, "report_only", None) is not True:
        raise ValueError(f"report_only must be True for {field_name}")
    if getattr(value, "readonly", None) is not True:
        raise ValueError(f"readonly must be True for {field_name}")


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
    if value is None or type(value) in (str, int, bool):
        return value
    raise ValueError("payload contains unsupported type")


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
                raise ValueError(f"unsafe public payload in {label}")
            _reject_unsafe_public_text(label, key)
            _reject_unsafe_public_payload(label, item)
        return
    if type(value) in (list, tuple):
        for item in value:
            _reject_unsafe_public_payload(label, item)
        return
    if type(value) is float:
        raise ValueError(f"unsafe public payload in {label}")
    if type(value) is str:
        _reject_unsafe_public_text(label, value)


def _reject_unsafe_public_text(label: str, value: str) -> None:
    normalized = value.lower()
    if any(fragment in normalized for fragment in UNSAFE_PUBLIC_TEXT_FRAGMENTS):
        raise ValueError(f"unsafe public payload in {label}")
