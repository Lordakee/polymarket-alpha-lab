"""Pure paper report for urgent source collection planning."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, localcontext
from hashlib import sha256
import json
from typing import Any


DEFAULT_RESEARCH_PACKET_URGENT_SOURCE_COLLECTION_PLAN_V2_CONFIG_VERSION = (
    "research-packet-urgent-source-collection-plan-v2"
)

_DECIMAL_CONTEXT = Context(prec=64)
_QUANTUM = Decimal("0.000001")
_ZERO = Decimal("0.000000")
_ONE = Decimal("1.000000")
_SECONDS_PER_DAY = Decimal("86400")
_MICROSECONDS_PER_SECOND = Decimal("1000000")
_DIGEST_FIELD = "derived_validation_digest"

_BASE_URGENCY_SCORE = Decimal("0.097321")
_HIGH_EVENT_VELOCITY_SCORE = Decimal("0.140000")
_MARKET_PROBABILITY_MOVED_SCORE = Decimal("0.120000")
_OFFICIAL_SOURCE_GAP_SCORE = Decimal("0.180000")
_CONTRADICTION_SEVERITY_SCORE = Decimal("0.033750")
_SOURCE_FRESHNESS_EXCEPTION_SCORE = Decimal("0.056250")
_RESOLUTION_HORIZON_URGENT_SCORE = Decimal("0.150000")
_SPECIALIST_UNCERTAINTY_SCORE = Decimal("0.112679")

_UNSAFE_PUBLIC_SURFACE_FRAGMENTS = (
    "".join(("li", "ve")),
    "".join(("au", "th")),
    "".join(("wall", "et")),
    "".join(("or", "der")),
    "".join(("net", "work")),
    "".join(("data", "base")),
    "".join(("per", "sist")),
    "".join(("sign", "ing")),
    "".join(("muta", "tion")),
    "".join(("b", "uy")),
    "".join(("s", "ell")),
    "".join(("tr", "ade")),
)

_WINDOWS = (
    "collect_now",
    "collect_within_1h",
    "collect_within_6h",
    "monitor_next_cycle",
)
_WINDOW_RANK = {
    "collect_now": 0,
    "collect_within_1h": 1,
    "collect_within_6h": 2,
    "monitor_next_cycle": 3,
}

_HIGH_EVENT_VELOCITY_REASON = "high_event_velocity"
_MARKET_PROBABILITY_MOVED_REASON = "market_probability_moved"
_OFFICIAL_SOURCE_GAP_REASON = "official_source_gap"
_CONTRADICTION_SEVERITY_REASON = "contradiction_severity_high"
_SOURCE_FRESHNESS_EXCEPTION_REASON = "source_freshness_exception"
_RESOLUTION_HORIZON_URGENT_REASON = "resolution_horizon_urgent"
_SPECIALIST_UNCERTAINTY_REASON = "specialist_uncertainty_high"
_MONITOR_REASON = "source_collection_monitor"
_EMPTY_REASON = "source_collection_plan_empty"
_PLAN_MONITOR_REASON = "source_collection_plan_monitor"

_REASON_SCORE = {
    _HIGH_EVENT_VELOCITY_REASON: _HIGH_EVENT_VELOCITY_SCORE,
    _MARKET_PROBABILITY_MOVED_REASON: _MARKET_PROBABILITY_MOVED_SCORE,
    _OFFICIAL_SOURCE_GAP_REASON: _OFFICIAL_SOURCE_GAP_SCORE,
    _CONTRADICTION_SEVERITY_REASON: _CONTRADICTION_SEVERITY_SCORE,
    _SOURCE_FRESHNESS_EXCEPTION_REASON: _SOURCE_FRESHNESS_EXCEPTION_SCORE,
    _RESOLUTION_HORIZON_URGENT_REASON: _RESOLUTION_HORIZON_URGENT_SCORE,
    _SPECIALIST_UNCERTAINTY_REASON: _SPECIALIST_UNCERTAINTY_SCORE,
}
_REPORT_REASON_SEQUENCE = (
    _HIGH_EVENT_VELOCITY_REASON,
    _MARKET_PROBABILITY_MOVED_REASON,
    _OFFICIAL_SOURCE_GAP_REASON,
    _CONTRADICTION_SEVERITY_REASON,
    _SOURCE_FRESHNESS_EXCEPTION_REASON,
    _RESOLUTION_HORIZON_URGENT_REASON,
    _SPECIALIST_UNCERTAINTY_REASON,
)


__all__ = (
    "DEFAULT_RESEARCH_PACKET_URGENT_SOURCE_COLLECTION_PLAN_V2_CONFIG_VERSION",
    "ResearchPacketUrgentSourceCollectionPlanV2Config",
    "ResearchPacketUrgentSourceCollectionPlanV2Packet",
    "ResearchPacketUrgentSourceCollectionPlanV2Row",
    "ResearchPacketUrgentSourceCollectionPlanV2Report",
    "build_research_packet_urgent_source_collection_plan_v2",
    "research_packet_urgent_source_collection_plan_v2_payload",
    "validate_research_packet_urgent_source_collection_plan_v2_payload",
)


@dataclass(frozen=True)
class ResearchPacketUrgentSourceCollectionPlanV2Config:
    config_version: str = (
        DEFAULT_RESEARCH_PACKET_URGENT_SOURCE_COLLECTION_PLAN_V2_CONFIG_VERSION
    )
    high_event_velocity_score: Decimal = Decimal("0.700000")
    high_market_probability_move_24h: Decimal = Decimal("0.080000")
    required_official_source_count: Decimal = Decimal("2.000000")
    max_source_age_seconds: Decimal = Decimal("3600.000000")
    urgent_resolution_horizon_seconds: Decimal = Decimal("86400.000000")
    high_contradiction_severity_score: Decimal = Decimal("0.500000")
    high_specialist_uncertainty_score: Decimal = Decimal("0.400000")
    collect_now_urgency_score: Decimal = Decimal("0.700000")
    collect_soon_urgency_score: Decimal = Decimal("0.400000")
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchPacketUrgentSourceCollectionPlanV2Config "
            "does not support subclassing",
        )

    def __post_init__(self) -> None:
        _require_exact_type(
            "config",
            self,
            ResearchPacketUrgentSourceCollectionPlanV2Config,
        )
        _require_canonical_string("config_version", self.config_version)
        for field_name in (
            "high_event_velocity_score",
            "high_market_probability_move_24h",
            "high_contradiction_severity_score",
            "high_specialist_uncertainty_score",
            "collect_now_urgency_score",
            "collect_soon_urgency_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "required_official_source_count",
            _normalize_count(
                "required_official_source_count",
                self.required_official_source_count,
            ),
        )
        for field_name in (
            "max_source_age_seconds",
            "urgent_resolution_horizon_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_positive_decimal(field_name, getattr(self, field_name)),
            )
        if self.required_official_source_count <= _ZERO:
            raise ValueError("required_official_source_count must be positive")
        if self.collect_now_urgency_score < self.collect_soon_urgency_score:
            raise ValueError(
                "collect_now_urgency_score must be at least collect_soon_urgency_score",
            )
        _require_hard_flags(self)
        _reject_unsafe_public_surface("config", self)
        _require_or_set_digest(self)


@dataclass(frozen=True)
class ResearchPacketUrgentSourceCollectionPlanV2Packet:
    event_slug: str
    condition_id: str
    packet_id: str
    observed_at: datetime
    resolution_deadline_at: datetime
    event_velocity_score: Decimal
    market_probability_move_24h: Decimal
    official_source_count: Decimal
    contradiction_severity_score: Decimal
    newest_source_age_seconds: Decimal
    source_freshness_exception_count: Decimal
    specialist_uncertainty_score: Decimal
    source_config_version: str
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchPacketUrgentSourceCollectionPlanV2Packet "
            "does not support subclassing",
        )

    def __post_init__(self) -> None:
        _require_exact_type(
            "packet",
            self,
            ResearchPacketUrgentSourceCollectionPlanV2Packet,
        )
        for field_name in (
            "event_slug",
            "condition_id",
            "packet_id",
            "source_config_version",
        ):
            _require_canonical_string(field_name, getattr(self, field_name))
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        object.__setattr__(
            self,
            "resolution_deadline_at",
            _as_utc("resolution_deadline_at", self.resolution_deadline_at),
        )
        for field_name in (
            "event_velocity_score",
            "market_probability_move_24h",
            "contradiction_severity_score",
            "specialist_uncertainty_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "official_source_count",
            "source_freshness_exception_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_count(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "newest_source_age_seconds",
            _normalize_nonnegative_decimal(
                "newest_source_age_seconds",
                self.newest_source_age_seconds,
            ),
        )
        if _seconds_between(self.observed_at, self.resolution_deadline_at) < _ZERO:
            raise ValueError("resolution_deadline_at must be at or after observed_at")
        _require_hard_flags(self)
        _reject_unsafe_public_surface("packet", self)
        _require_or_set_digest(self)


@dataclass(frozen=True)
class ResearchPacketUrgentSourceCollectionPlanV2Row:
    event_slug: str
    condition_id: str
    packet_id: str
    observed_at: datetime
    resolution_deadline_at: datetime
    collection_window: str
    urgency_score: Decimal
    event_velocity_score: Decimal
    market_probability_move_24h: Decimal
    official_source_count: Decimal
    official_source_gap: Decimal
    contradiction_severity_score: Decimal
    newest_source_age_seconds: Decimal
    source_freshness_exception_count: Decimal
    resolution_horizon_seconds: Decimal
    packet_age_seconds: Decimal
    specialist_uncertainty_score: Decimal
    source_config_version: str
    reason_codes: tuple[str, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchPacketUrgentSourceCollectionPlanV2Row "
            "does not support subclassing",
        )

    def __post_init__(self) -> None:
        _require_exact_type("row", self, ResearchPacketUrgentSourceCollectionPlanV2Row)
        for field_name in (
            "event_slug",
            "condition_id",
            "packet_id",
            "source_config_version",
        ):
            _require_canonical_string(field_name, getattr(self, field_name))
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        object.__setattr__(
            self,
            "resolution_deadline_at",
            _as_utc("resolution_deadline_at", self.resolution_deadline_at),
        )
        _require_window("collection_window", self.collection_window)
        for field_name in (
            "urgency_score",
            "event_velocity_score",
            "market_probability_move_24h",
            "contradiction_severity_score",
            "specialist_uncertainty_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "official_source_count",
            "official_source_gap",
            "source_freshness_exception_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_count(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "newest_source_age_seconds",
            "resolution_horizon_seconds",
            "packet_age_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes_preserving_sequence(self.reason_codes),
        )
        _validate_row_consistency(self)
        _require_hard_flags(self)
        _reject_unsafe_public_surface("row", self)
        _require_or_set_digest(self)


@dataclass(frozen=True)
class ResearchPacketUrgentSourceCollectionPlanV2Report:
    generated_at: datetime
    config_version: str
    input_count: Decimal
    row_count: Decimal
    collect_now_count: Decimal
    collect_within_1h_count: Decimal
    collect_within_6h_count: Decimal
    monitor_next_cycle_count: Decimal
    high_event_velocity_count: Decimal
    market_probability_movement_count: Decimal
    official_source_gap_count: Decimal
    contradiction_severity_count: Decimal
    source_freshness_exception_count: Decimal
    urgent_resolution_horizon_count: Decimal
    specialist_uncertainty_count: Decimal
    average_urgency_score: Decimal
    max_urgency_score: Decimal
    collect_now_urgency_score: Decimal
    collect_soon_urgency_score: Decimal
    reason_codes: tuple[str, ...]
    rows: tuple[ResearchPacketUrgentSourceCollectionPlanV2Row, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchPacketUrgentSourceCollectionPlanV2Report "
            "does not support subclassing",
        )

    def __post_init__(self) -> None:
        _require_exact_type("report", self, ResearchPacketUrgentSourceCollectionPlanV2Report)
        object.__setattr__(
            self,
            "generated_at",
            _as_utc("generated_at", self.generated_at),
        )
        _require_canonical_string("config_version", self.config_version)
        for field_name in (
            "input_count",
            "row_count",
            "collect_now_count",
            "collect_within_1h_count",
            "collect_within_6h_count",
            "monitor_next_cycle_count",
            "high_event_velocity_count",
            "market_probability_movement_count",
            "official_source_gap_count",
            "contradiction_severity_count",
            "source_freshness_exception_count",
            "urgent_resolution_horizon_count",
            "specialist_uncertainty_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_count(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "average_urgency_score",
            "max_urgency_score",
            "collect_now_urgency_score",
            "collect_soon_urgency_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        if self.collect_now_urgency_score < self.collect_soon_urgency_score:
            raise ValueError(
                "collect_now_urgency_score must be at least collect_soon_urgency_score",
            )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes_preserving_sequence(self.reason_codes),
        )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        _validate_report_consistency(self)
        _require_hard_flags(self)
        _reject_unsafe_public_surface("report", self)
        _require_or_set_digest(self)


def build_research_packet_urgent_source_collection_plan_v2(
    packets: Iterable[ResearchPacketUrgentSourceCollectionPlanV2Packet],
    *,
    config: ResearchPacketUrgentSourceCollectionPlanV2Config,
    generated_at: datetime,
) -> ResearchPacketUrgentSourceCollectionPlanV2Report:
    if type(config) is not ResearchPacketUrgentSourceCollectionPlanV2Config:
        raise ValueError(
            "config must be a ResearchPacketUrgentSourceCollectionPlanV2Config",
        )
    _require_hard_flags(config)
    _reject_unsafe_public_surface("config", config)
    _require_or_set_digest(config)
    generated_at = _as_utc("generated_at", generated_at)
    values = _normalize_packets(packets)
    _validate_generated_at_covers_values(generated_at, values)

    rows = tuple(
        sorted(
            (
                _row_from_packet(
                    packet,
                    config=config,
                    generated_at=generated_at,
                )
                for packet in values
            ),
            key=_row_sort_key,
        ),
    )
    input_count = _decimal_count(len(values))

    return ResearchPacketUrgentSourceCollectionPlanV2Report(
        generated_at=generated_at,
        config_version=config.config_version,
        input_count=input_count,
        row_count=_decimal_count(len(rows)),
        collect_now_count=_window_count(rows, "collect_now"),
        collect_within_1h_count=_window_count(rows, "collect_within_1h"),
        collect_within_6h_count=_window_count(rows, "collect_within_6h"),
        monitor_next_cycle_count=_window_count(rows, "monitor_next_cycle"),
        high_event_velocity_count=_reason_row_count(rows, _HIGH_EVENT_VELOCITY_REASON),
        market_probability_movement_count=_reason_row_count(
            rows,
            _MARKET_PROBABILITY_MOVED_REASON,
        ),
        official_source_gap_count=_reason_row_count(rows, _OFFICIAL_SOURCE_GAP_REASON),
        contradiction_severity_count=_reason_row_count(
            rows,
            _CONTRADICTION_SEVERITY_REASON,
        ),
        source_freshness_exception_count=_reason_row_count(
            rows,
            _SOURCE_FRESHNESS_EXCEPTION_REASON,
        ),
        urgent_resolution_horizon_count=_reason_row_count(
            rows,
            _RESOLUTION_HORIZON_URGENT_REASON,
        ),
        specialist_uncertainty_count=_reason_row_count(
            rows,
            _SPECIALIST_UNCERTAINTY_REASON,
        ),
        average_urgency_score=_average(row.urgency_score for row in rows),
        max_urgency_score=max((row.urgency_score for row in rows), default=_ZERO),
        collect_now_urgency_score=config.collect_now_urgency_score,
        collect_soon_urgency_score=config.collect_soon_urgency_score,
        reason_codes=_report_reason_codes(rows),
        rows=rows,
    )


def research_packet_urgent_source_collection_plan_v2_payload(
    report: ResearchPacketUrgentSourceCollectionPlanV2Report,
) -> dict[str, Any]:
    if type(report) is not ResearchPacketUrgentSourceCollectionPlanV2Report:
        raise ValueError(
            "report must be a ResearchPacketUrgentSourceCollectionPlanV2Report",
        )
    _require_hard_flags(report)
    _reject_unsafe_public_surface("report", report)
    _require_or_set_digest(report)
    for row in report.rows:
        _require_hard_flags(row)
        _reject_unsafe_public_surface("row", row)
        _require_or_set_digest(row)
    payload = _payload_value(report)
    validate_research_packet_urgent_source_collection_plan_v2_payload(payload)
    return payload


def validate_research_packet_urgent_source_collection_plan_v2_payload(
    payload: object,
) -> bool:
    if not isinstance(payload, dict):
        raise ValueError("public payload must be a JSON object")
    _reject_unsafe_public_surface("public payload", payload)
    _require_public_payload_values(payload)
    _validate_payload_digest_tree(payload)
    return True


def _row_from_packet(
    packet: ResearchPacketUrgentSourceCollectionPlanV2Packet,
    *,
    config: ResearchPacketUrgentSourceCollectionPlanV2Config,
    generated_at: datetime,
) -> ResearchPacketUrgentSourceCollectionPlanV2Row:
    packet_age_seconds = _seconds_between(packet.observed_at, generated_at)
    raw_horizon = _seconds_between(generated_at, packet.resolution_deadline_at)
    resolution_horizon_seconds = max(raw_horizon, _ZERO)
    official_source_gap = max(
        _quantize(config.required_official_source_count - packet.official_source_count),
        _ZERO,
    )
    reason_codes = _reason_codes_for_packet(
        packet,
        config=config,
        official_source_gap=official_source_gap,
        resolution_horizon_seconds=resolution_horizon_seconds,
    )
    urgency_score = _urgency_score(reason_codes)

    return ResearchPacketUrgentSourceCollectionPlanV2Row(
        event_slug=packet.event_slug,
        condition_id=packet.condition_id,
        packet_id=packet.packet_id,
        observed_at=packet.observed_at,
        resolution_deadline_at=packet.resolution_deadline_at,
        collection_window=_collection_window(
            urgency_score,
            reason_codes=reason_codes,
            config=config,
        ),
        urgency_score=urgency_score,
        event_velocity_score=packet.event_velocity_score,
        market_probability_move_24h=packet.market_probability_move_24h,
        official_source_count=packet.official_source_count,
        official_source_gap=official_source_gap,
        contradiction_severity_score=packet.contradiction_severity_score,
        newest_source_age_seconds=packet.newest_source_age_seconds,
        source_freshness_exception_count=packet.source_freshness_exception_count,
        resolution_horizon_seconds=resolution_horizon_seconds,
        packet_age_seconds=packet_age_seconds,
        specialist_uncertainty_score=packet.specialist_uncertainty_score,
        source_config_version=packet.source_config_version,
        reason_codes=reason_codes,
    )


def _reason_codes_for_packet(
    packet: ResearchPacketUrgentSourceCollectionPlanV2Packet,
    *,
    config: ResearchPacketUrgentSourceCollectionPlanV2Config,
    official_source_gap: Decimal,
    resolution_horizon_seconds: Decimal,
) -> tuple[str, ...]:
    reasons: list[str] = []
    if packet.event_velocity_score >= config.high_event_velocity_score:
        reasons.append(_HIGH_EVENT_VELOCITY_REASON)
    if packet.market_probability_move_24h >= config.high_market_probability_move_24h:
        reasons.append(_MARKET_PROBABILITY_MOVED_REASON)
    if official_source_gap > _ZERO:
        reasons.append(_OFFICIAL_SOURCE_GAP_REASON)
    if packet.contradiction_severity_score >= config.high_contradiction_severity_score:
        reasons.append(_CONTRADICTION_SEVERITY_REASON)
    if _has_source_freshness_exception(packet, config=config):
        reasons.append(_SOURCE_FRESHNESS_EXCEPTION_REASON)
    if (
        resolution_horizon_seconds <= config.urgent_resolution_horizon_seconds
        and reasons
    ):
        reasons.append(_RESOLUTION_HORIZON_URGENT_REASON)
    if packet.specialist_uncertainty_score >= config.high_specialist_uncertainty_score:
        reasons.append(_SPECIALIST_UNCERTAINTY_REASON)
    if not reasons:
        return (_MONITOR_REASON,)
    return tuple(reasons)


def _has_source_freshness_exception(
    packet: ResearchPacketUrgentSourceCollectionPlanV2Packet,
    *,
    config: ResearchPacketUrgentSourceCollectionPlanV2Config,
) -> bool:
    return (
        packet.newest_source_age_seconds > config.max_source_age_seconds
        or packet.source_freshness_exception_count > _ZERO
    )


def _urgency_score(reason_codes: tuple[str, ...]) -> Decimal:
    if reason_codes == (_MONITOR_REASON,):
        return _BASE_URGENCY_SCORE
    score = _BASE_URGENCY_SCORE
    for reason_code in reason_codes:
        score = _quantize(score + _REASON_SCORE.get(reason_code, _ZERO))
    return min(score, _ONE)


def _collection_window(
    urgency_score: Decimal,
    *,
    reason_codes: tuple[str, ...],
    config: ResearchPacketUrgentSourceCollectionPlanV2Config,
) -> str:
    if reason_codes == (_MONITOR_REASON,):
        return "monitor_next_cycle"
    if urgency_score >= config.collect_now_urgency_score:
        return "collect_now"
    if urgency_score >= config.collect_soon_urgency_score:
        return "collect_within_1h"
    return "collect_within_6h"


def _report_reason_codes(
    rows: tuple[ResearchPacketUrgentSourceCollectionPlanV2Row, ...],
) -> tuple[str, ...]:
    if not rows:
        return (_EMPTY_REASON,)
    present = frozenset(reason_code for row in rows for reason_code in row.reason_codes)
    if present == {_MONITOR_REASON}:
        return (_PLAN_MONITOR_REASON,)
    return tuple(reason_code for reason_code in _REPORT_REASON_SEQUENCE if reason_code in present)


def _normalize_packets(
    values: Iterable[ResearchPacketUrgentSourceCollectionPlanV2Packet],
) -> tuple[ResearchPacketUrgentSourceCollectionPlanV2Packet, ...]:
    if isinstance(values, (str, bytes)):
        raise ValueError("packets must be an iterable")
    try:
        normalized = tuple(values)
    except TypeError as exc:
        raise ValueError("packets must be an iterable") from exc
    seen_keys: set[tuple[str, str, str]] = set()
    for value in normalized:
        if type(value) is not ResearchPacketUrgentSourceCollectionPlanV2Packet:
            raise ValueError(
                "packets must contain ResearchPacketUrgentSourceCollectionPlanV2Packet "
                "values",
            )
        _require_hard_flags(value)
        _reject_unsafe_public_surface("packet", value)
        _require_or_set_digest(value)
        key = (value.event_slug, value.condition_id, value.packet_id)
        if key in seen_keys:
            raise ValueError("packets must not contain duplicate packet keys")
        seen_keys.add(key)
    return normalized


def _normalize_rows(
    values: Iterable[ResearchPacketUrgentSourceCollectionPlanV2Row],
) -> tuple[ResearchPacketUrgentSourceCollectionPlanV2Row, ...]:
    if isinstance(values, (str, bytes)):
        raise ValueError(
            "rows must contain ResearchPacketUrgentSourceCollectionPlanV2Row values",
        )
    try:
        rows = tuple(values)
    except TypeError as exc:
        raise ValueError(
            "rows must contain ResearchPacketUrgentSourceCollectionPlanV2Row values",
        ) from exc
    for row in rows:
        if type(row) is not ResearchPacketUrgentSourceCollectionPlanV2Row:
            raise ValueError(
                "rows must contain ResearchPacketUrgentSourceCollectionPlanV2Row values",
            )
        _require_hard_flags(row)
        _reject_unsafe_public_surface("row", row)
        _require_or_set_digest(row)
    if rows != tuple(sorted(rows, key=_row_sort_key)):
        raise ValueError("rows must use deterministic sort")
    if len(set(_row_identity(row) for row in rows)) != len(rows):
        raise ValueError("rows must be unique")
    return rows


def _validate_generated_at_covers_values(
    generated_at: datetime,
    values: tuple[ResearchPacketUrgentSourceCollectionPlanV2Packet, ...],
) -> None:
    for value in values:
        if _seconds_between(value.observed_at, generated_at) < _ZERO:
            raise ValueError("generated_at must be at or after every packet observation")


def _validate_row_consistency(
    row: ResearchPacketUrgentSourceCollectionPlanV2Row,
) -> None:
    if _seconds_between(row.observed_at, row.resolution_deadline_at) < _ZERO:
        raise ValueError("resolution_deadline_at must be at or after observed_at")
    if row.reason_codes == (_MONITOR_REASON,):
        if row.urgency_score != _BASE_URGENCY_SCORE:
            raise ValueError("urgency_score must match monitor reason")
        if row.collection_window != "monitor_next_cycle":
            raise ValueError("collection_window must match monitor reason")
    elif _MONITOR_REASON in row.reason_codes:
        raise ValueError("reason_codes must not mix monitor with collection reasons")
    elif row.urgency_score != _urgency_score(row.reason_codes):
        raise ValueError("urgency_score must match reason_codes")
    if row.official_source_gap > _ZERO and _OFFICIAL_SOURCE_GAP_REASON not in row.reason_codes:
        raise ValueError("reason_codes must include official source gap")


def _validate_report_consistency(
    report: ResearchPacketUrgentSourceCollectionPlanV2Report,
) -> None:
    if report.row_count != _decimal_count(len(report.rows)):
        raise ValueError("row_count must match rows")
    if report.input_count != report.row_count:
        raise ValueError("input_count must match rows")
    if report.collect_now_count != _window_count(report.rows, "collect_now"):
        raise ValueError("collect_now_count must match rows")
    if report.collect_within_1h_count != _window_count(report.rows, "collect_within_1h"):
        raise ValueError("collect_within_1h_count must match rows")
    if report.collect_within_6h_count != _window_count(report.rows, "collect_within_6h"):
        raise ValueError("collect_within_6h_count must match rows")
    if report.monitor_next_cycle_count != _window_count(report.rows, "monitor_next_cycle"):
        raise ValueError("monitor_next_cycle_count must match rows")
    if report.high_event_velocity_count != _reason_row_count(
        report.rows,
        _HIGH_EVENT_VELOCITY_REASON,
    ):
        raise ValueError("high_event_velocity_count must match rows")
    if report.market_probability_movement_count != _reason_row_count(
        report.rows,
        _MARKET_PROBABILITY_MOVED_REASON,
    ):
        raise ValueError("market_probability_movement_count must match rows")
    if report.official_source_gap_count != _reason_row_count(
        report.rows,
        _OFFICIAL_SOURCE_GAP_REASON,
    ):
        raise ValueError("official_source_gap_count must match rows")
    if report.contradiction_severity_count != _reason_row_count(
        report.rows,
        _CONTRADICTION_SEVERITY_REASON,
    ):
        raise ValueError("contradiction_severity_count must match rows")
    if report.source_freshness_exception_count != _reason_row_count(
        report.rows,
        _SOURCE_FRESHNESS_EXCEPTION_REASON,
    ):
        raise ValueError("source_freshness_exception_count must match rows")
    if report.urgent_resolution_horizon_count != _reason_row_count(
        report.rows,
        _RESOLUTION_HORIZON_URGENT_REASON,
    ):
        raise ValueError("urgent_resolution_horizon_count must match rows")
    if report.specialist_uncertainty_count != _reason_row_count(
        report.rows,
        _SPECIALIST_UNCERTAINTY_REASON,
    ):
        raise ValueError("specialist_uncertainty_count must match rows")
    if report.average_urgency_score != _average(row.urgency_score for row in report.rows):
        raise ValueError("average_urgency_score must match rows")
    if report.max_urgency_score != max(
        (row.urgency_score for row in report.rows),
        default=_ZERO,
    ):
        raise ValueError("max_urgency_score must match rows")
    for row in report.rows:
        expected_window = _collection_window_for_report(row, report)
        if row.collection_window != expected_window:
            raise ValueError("collection_window must match urgency thresholds")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")
    if report.rows != tuple(sorted(report.rows, key=_row_sort_key)):
        raise ValueError("rows must be sorted")
    if len(set(_row_identity(row) for row in report.rows)) != len(report.rows):
        raise ValueError("rows must be unique")


def _collection_window_for_report(
    row: ResearchPacketUrgentSourceCollectionPlanV2Row,
    report: ResearchPacketUrgentSourceCollectionPlanV2Report,
) -> str:
    if row.reason_codes == (_MONITOR_REASON,):
        return "monitor_next_cycle"
    if row.urgency_score >= report.collect_now_urgency_score:
        return "collect_now"
    if row.urgency_score >= report.collect_soon_urgency_score:
        return "collect_within_1h"
    return "collect_within_6h"


def _row_sort_key(
    row: ResearchPacketUrgentSourceCollectionPlanV2Row,
) -> tuple[int, Decimal, str, str, str]:
    return (
        _WINDOW_RANK[row.collection_window],
        -row.urgency_score,
        row.event_slug,
        row.condition_id,
        row.packet_id,
    )


def _row_identity(row: ResearchPacketUrgentSourceCollectionPlanV2Row) -> tuple[str, str, str]:
    return (row.event_slug, row.condition_id, row.packet_id)


def _window_count(
    rows: tuple[ResearchPacketUrgentSourceCollectionPlanV2Row, ...],
    collection_window: str,
) -> Decimal:
    return _decimal_count(sum(1 for row in rows if row.collection_window == collection_window))


def _reason_row_count(
    rows: tuple[ResearchPacketUrgentSourceCollectionPlanV2Row, ...],
    reason_code: str,
) -> Decimal:
    return _decimal_count(sum(1 for row in rows if reason_code in row.reason_codes))


def _average(values: Iterable[Decimal]) -> Decimal:
    numbers = tuple(values)
    if not numbers:
        return _ZERO
    with localcontext(_DECIMAL_CONTEXT):
        return _quantize(sum(numbers, _ZERO) / Decimal(len(numbers)))


def _seconds_between(start: datetime, end: datetime) -> Decimal:
    delta = end - start
    whole_seconds = Decimal(delta.days) * _SECONDS_PER_DAY + Decimal(delta.seconds)
    microseconds = Decimal(delta.microseconds) / _MICROSECONDS_PER_SECOND
    with localcontext(_DECIMAL_CONTEXT):
        return _quantize(whole_seconds + microseconds)


def _decimal_count(value: int) -> Decimal:
    return _quantize(Decimal(value))


def _normalize_reason_codes_preserving_sequence(value: Iterable[str]) -> tuple[str, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError("reason_codes must be an iterable of strings")
    try:
        normalized = tuple(value)
    except TypeError as exc:
        raise ValueError("reason_codes must be an iterable of strings") from exc
    if not normalized:
        raise ValueError("reason_codes must contain at least one value")
    if len(set(normalized)) != len(normalized):
        raise ValueError("reason_codes must not contain duplicates")
    for reason_code in normalized:
        _require_canonical_string("reason_codes", reason_code)
    return normalized


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")


def _require_window(field_name: str, value: object) -> None:
    if type(value) is not str or value not in _WINDOWS:
        raise ValueError(f"{field_name} must be a supported collection window")


def _normalize_count(field_name: str, value: object) -> Decimal:
    normalized = _normalize_nonnegative_decimal(field_name, value)
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{field_name} must be a whole Decimal")
    return normalized


def _normalize_ratio(field_name: str, value: object) -> Decimal:
    normalized = _normalize_nonnegative_decimal(field_name, value)
    if normalized > _ONE:
        raise ValueError(f"{field_name} must be at most one")
    return normalized


def _normalize_positive_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized <= _ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _normalize_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized < _ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _normalize_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    normalized = _quantize(value)
    if normalized != value:
        raise ValueError(f"{field_name} must be quantized to 0.000001")
    return normalized


def _quantize(value: Decimal) -> Decimal:
    with localcontext(_DECIMAL_CONTEXT):
        return value.quantize(_QUANTUM)


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_exact_type(label: str, value: object, expected_type: type[object]) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{label} must be a {expected_type.__name__}")


def _require_hard_flags(value: object) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if getattr(value, field_name) is not True:
            raise ValueError(f"{field_name} must be True")


def _reject_unsafe_public_surface(label: str, value: object) -> None:
    for item in _surface_items(value):
        lowered = item.lower()
        if any(fragment in lowered for fragment in _UNSAFE_PUBLIC_SURFACE_FRAGMENTS):
            raise ValueError(f"unsafe public surface in {label}: {item}")


def _surface_items(value: object) -> tuple[str, ...]:
    if is_dataclass(value) and not isinstance(value, type):
        items: list[str] = []
        for field in fields(value):
            items.append(field.name)
            items.extend(_surface_items(getattr(value, field.name)))
        return tuple(items)
    if isinstance(value, dict):
        items = []
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("public payload keys must be strings")
            items.append(key)
            items.extend(_surface_items(item))
        return tuple(items)
    if isinstance(value, (list, tuple)):
        items = []
        for item in value:
            items.extend(_surface_items(item))
        return tuple(items)
    if type(value) is str:
        return (value,)
    return ()


def _require_or_set_digest(value: object) -> None:
    current = getattr(value, _DIGEST_FIELD)
    if type(current) is not str:
        raise ValueError("derived_validation_digest must be a string")
    expected = _derived_digest(value)
    if current == "":
        object.__setattr__(value, _DIGEST_FIELD, expected)
        return
    if current != expected or not _is_sha256_hex(current):
        raise ValueError("derived_validation_digest does not match derived payload")


def _derived_digest(value: object) -> str:
    encoded = json.dumps(
        _canonical_digest_value(value),
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return sha256(encoded).hexdigest()


def _is_sha256_hex(value: str) -> bool:
    return len(value) == 64 and all(character in "0123456789abcdef" for character in value)


def _canonical_digest_value(value: object) -> object:
    if value is None:
        return None
    if is_dataclass(value) and not isinstance(value, type):
        return {
            field.name: _canonical_digest_value(getattr(value, field.name))
            for field in fields(value)
            if field.name != _DIGEST_FIELD
        }
    if isinstance(value, Decimal):
        if not value.is_finite():
            raise ValueError("digest Decimal value must be finite")
        return str(value)
    if type(value) is datetime:
        return value.astimezone(UTC).isoformat()
    if type(value) in (str, bool):
        return value
    if isinstance(value, tuple):
        return [_canonical_digest_value(item) for item in value]
    if isinstance(value, list):
        return [_canonical_digest_value(item) for item in value]
    if isinstance(value, dict):
        result: dict[str, object] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("public payload keys must be strings")
            if key != _DIGEST_FIELD:
                result[key] = _canonical_digest_value(item)
        return result
    raise ValueError("unsupported digest value")


def _payload_value(value: object) -> Any:
    if value is None:
        return None
    if is_dataclass(value) and not isinstance(value, type):
        return {field.name: _payload_value(getattr(value, field.name)) for field in fields(value)}
    if isinstance(value, Decimal):
        if not value.is_finite():
            raise ValueError("public payload Decimal value must be finite")
        return str(value)
    if type(value) is datetime:
        return value.astimezone(UTC).isoformat()
    if type(value) in (str, bool):
        return value
    if isinstance(value, tuple):
        return [_payload_value(item) for item in value]
    if isinstance(value, list):
        return [_payload_value(item) for item in value]
    if isinstance(value, dict):
        result: dict[str, Any] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("public payload keys must be strings")
            result[key] = _payload_value(item)
        return result
    raise ValueError("value is not public payload serializable")


def _require_public_payload_values(value: object, path: str = "payload") -> None:
    if type(value) in (float, int) or isinstance(value, Decimal):
        raise ValueError(f"public payload {path} must use Decimal string values")
    if isinstance(value, datetime):
        raise ValueError(f"public payload {path} must use ISO datetime string values")
    if type(value) is bool or value is None or type(value) is str:
        return
    if isinstance(value, dict):
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("public payload object keys must be strings")
            if key in ("paper_only", "report_only", "readonly") and item is not True:
                raise ValueError(f"{key} must be True for readonly public payload")
            _require_public_payload_values(item, f"{path}.{key}")
        return
    if isinstance(value, list):
        for index, item in enumerate(value):
            _require_public_payload_values(item, f"{path}[{index}]")
        return
    raise ValueError(f"{path} is not public payload serializable")


def _validate_payload_digest_tree(payload: dict[str, Any]) -> None:
    if _DIGEST_FIELD not in payload or type(payload[_DIGEST_FIELD]) is not str:
        raise ValueError("derived_validation_digest is required")
    expected = sha256(
        json.dumps(
            _strip_digest_fields(payload),
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8"),
    ).hexdigest()
    if payload[_DIGEST_FIELD] != expected:
        raise ValueError("derived_validation_digest does not match payload")
    rows = payload.get("rows")
    if rows is None:
        return
    if not isinstance(rows, list):
        raise ValueError("public payload rows must be a list")
    for row in rows:
        if not isinstance(row, dict):
            raise ValueError("public payload rows must contain objects")
        _validate_payload_digest_tree(row)


def _strip_digest_fields(value: object) -> object:
    if isinstance(value, dict):
        result: dict[str, object] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("public payload keys must be strings")
            if key != _DIGEST_FIELD:
                result[key] = _strip_digest_fields(item)
        return result
    if isinstance(value, list):
        return [_strip_digest_fields(item) for item in value]
    return value
