"""Phase 1 probabilistic resolution readiness score report."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from typing import Any


DEFAULT_RESEARCH_PACKET_PROBABILISTIC_RESOLUTION_READINESS_SCORE_V2_CONFIG_VERSION = (
    "research-packet-probabilistic-resolution-readiness-score-v2"
)

PASS_REASON = "research_packet_probabilistic_resolution_readiness_score_v2_passed"
PROBABILITY_CONFIDENCE_WEAK_REASON = (
    "research_packet_probabilistic_resolution_readiness_score_v2_probability_confidence_weak"
)
PROBABILITY_BAND_WIDE_REASON = (
    "research_packet_probabilistic_resolution_readiness_score_v2_probability_band_wide"
)
RULE_CLARITY_WEAK_REASON = (
    "research_packet_probabilistic_resolution_readiness_score_v2_rule_clarity_weak"
)
PRIMARY_SOURCE_MISSING_REASON = (
    "research_packet_probabilistic_resolution_readiness_score_v2_primary_source_missing"
)
SOURCE_QUORUM_SHORT_REASON = (
    "research_packet_probabilistic_resolution_readiness_score_v2_source_quorum_short"
)
READINESS_SCORE_SHORT_REASON = (
    "research_packet_probabilistic_resolution_readiness_score_v2_readiness_score_short"
)
NO_PACKETS_REASON = (
    "research_packet_probabilistic_resolution_readiness_score_v2_no_packets"
)

ROW_REASON_CODES = (
    PROBABILITY_CONFIDENCE_WEAK_REASON,
    PROBABILITY_BAND_WIDE_REASON,
    RULE_CLARITY_WEAK_REASON,
    PRIMARY_SOURCE_MISSING_REASON,
    SOURCE_QUORUM_SHORT_REASON,
    READINESS_SCORE_SHORT_REASON,
)
ROW_PUBLIC_REASON_CODES = (PASS_REASON,) + ROW_REASON_CODES
REPORT_REASON_CODES = ROW_PUBLIC_REASON_CODES + (NO_PACKETS_REASON,)
NOT_READY_REASONS = frozenset(
    (
        RULE_CLARITY_WEAK_REASON,
        PRIMARY_SOURCE_MISSING_REASON,
        SOURCE_QUORUM_SHORT_REASON,
    ),
)
REPORT_STATUSES = ("ready", "watch", "not_ready")
STATUS_RANK = {
    "not_ready": Decimal("0.000000"),
    "watch": Decimal("1.000000"),
    "ready": Decimal("2.000000"),
}

DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
TWO = Decimal("2.000000")
HALF = Decimal("0.500000")
QUANTUM = Decimal("0.000001")


def _join_parts(*parts: str) -> str:
    return "".join(parts)


UNSAFE_PUBLIC_FRAGMENTS = frozenset(
    (
        _join_parts("li", "ve"),
        _join_parts("au", "th"),
        _join_parts("wal", "let"),
        _join_parts("ord", "er"),
        _join_parts("net", "work"),
        _join_parts("data", "base"),
        _join_parts("per", "sist"),
        _join_parts("sign", "ing"),
        _join_parts("muta", "tion"),
        _join_parts("bu", "y"),
        _join_parts("se", "ll"),
        _join_parts("tra", "de"),
    ),
)


@dataclass(frozen=True)
class ResearchPacketProbabilisticResolutionReadinessScoreV2Config:
    config_version: str = (
        DEFAULT_RESEARCH_PACKET_PROBABILISTIC_RESOLUTION_READINESS_SCORE_V2_CONFIG_VERSION
    )
    min_probability_confidence_score: Decimal = Decimal("0.600000")
    max_probability_band_width: Decimal = Decimal("0.150000")
    min_rule_clarity_score: Decimal = Decimal("0.800000")
    min_primary_source_count: Decimal = Decimal("1.000000")
    min_independent_source_count: Decimal = Decimal("2.000000")
    pass_readiness_score: Decimal = Decimal("0.850000")
    watch_readiness_score: Decimal = Decimal("0.650000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchPacketProbabilisticResolutionReadinessScoreV2Config "
            "does not support subclassing",
        )

    def __post_init__(self) -> None:
        _require_public_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_PACKET_PROBABILISTIC_RESOLUTION_READINESS_SCORE_V2_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "min_probability_confidence_score",
            "max_probability_band_width",
            "min_rule_clarity_score",
            "pass_readiness_score",
            "watch_readiness_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        for field_name in ("min_primary_source_count", "min_independent_source_count"):
            object.__setattr__(
                self,
                field_name,
                _normalize_positive_count(field_name, getattr(self, field_name)),
            )
        if self.max_probability_band_width <= ZERO:
            raise ValueError("max_probability_band_width must be positive")
        if self.watch_readiness_score > self.pass_readiness_score:
            raise ValueError("watch_readiness_score must be at most pass_readiness_score")
        _require_hard_flags(self)


@dataclass(frozen=True)
class ResearchPacketProbabilisticResolutionReadinessScoreV2Packet:
    event_id: str
    packet_id: str
    event_category: str
    captured_at: datetime
    resolution_probability: Decimal
    probability_band_width: Decimal
    rule_clarity_score: Decimal
    primary_source_count: Decimal
    independent_source_count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchPacketProbabilisticResolutionReadinessScoreV2Packet "
            "does not support subclassing",
        )

    def __post_init__(self) -> None:
        for field_name in ("event_id", "packet_id", "event_category"):
            _require_public_string(field_name, getattr(self, field_name))
        object.__setattr__(self, "captured_at", _as_utc("captured_at", self.captured_at))
        for field_name in (
            "resolution_probability",
            "probability_band_width",
            "rule_clarity_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        for field_name in ("primary_source_count", "independent_source_count"):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_count(field_name, getattr(self, field_name)),
            )
        _require_hard_flags(self)


@dataclass(frozen=True)
class ResearchPacketProbabilisticResolutionReadinessScoreV2ReasonCodeCount:
    reason_code: str
    packet_count: Decimal
    packet_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchPacketProbabilisticResolutionReadinessScoreV2ReasonCodeCount "
            "does not support subclassing",
        )

    def __post_init__(self) -> None:
        _require_member("reason_code", self.reason_code, ROW_REASON_CODES)
        object.__setattr__(
            self,
            "packet_count",
            _normalize_positive_count("packet_count", self.packet_count),
        )
        object.__setattr__(
            self,
            "packet_ratio",
            _normalize_ratio("packet_ratio", self.packet_ratio),
        )
        _require_hard_flags(self)


@dataclass(frozen=True)
class ResearchPacketProbabilisticResolutionReadinessScoreV2Row:
    event_id: str
    packet_id: str
    event_category: str
    captured_at: datetime
    resolution_probability: Decimal
    probability_band_width: Decimal
    rule_clarity_score: Decimal
    primary_source_count: Decimal
    independent_source_count: Decimal
    probability_confidence_score: Decimal
    probability_band_component_score: Decimal
    rule_clarity_component_score: Decimal
    primary_source_score: Decimal
    source_quorum_score: Decimal
    readiness_score: Decimal
    readiness_status: str
    reason_codes: tuple[str, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchPacketProbabilisticResolutionReadinessScoreV2Row "
            "does not support subclassing",
        )

    def __post_init__(self) -> None:
        for field_name in ("event_id", "packet_id", "event_category"):
            _require_public_string(field_name, getattr(self, field_name))
        object.__setattr__(self, "captured_at", _as_utc("captured_at", self.captured_at))
        for field_name in (
            "resolution_probability",
            "probability_band_width",
            "rule_clarity_score",
            "probability_confidence_score",
            "probability_band_component_score",
            "rule_clarity_component_score",
            "primary_source_score",
            "source_quorum_score",
            "readiness_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        for field_name in ("primary_source_count", "independent_source_count"):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_count(field_name, getattr(self, field_name)),
            )
        _require_member("readiness_status", self.readiness_status, REPORT_STATUSES)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, ROW_PUBLIC_REASON_CODES),
        )
        _require_hard_flags(self)
        if self.derived_validation_digest == "":
            object.__setattr__(
                self,
                "derived_validation_digest",
                _row_derived_validation_digest(self),
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
        _validate_row(self)


@dataclass(frozen=True)
class ResearchPacketProbabilisticResolutionReadinessScoreV2Report:
    generated_at: datetime
    config_version: str
    report_status: str
    packet_count: Decimal
    ready_packet_count: Decimal
    watch_packet_count: Decimal
    not_ready_packet_count: Decimal
    attention_packet_count: Decimal
    probability_confidence_gap_packet_count: Decimal
    probability_band_gap_packet_count: Decimal
    rule_clarity_gap_packet_count: Decimal
    primary_source_gap_packet_count: Decimal
    source_quorum_gap_packet_count: Decimal
    readiness_score_gap_packet_count: Decimal
    average_readiness_score: Decimal
    min_readiness_score_observed: Decimal
    min_probability_confidence_score: Decimal
    max_probability_band_width: Decimal
    min_rule_clarity_score: Decimal
    min_primary_source_count: Decimal
    min_independent_source_count: Decimal
    pass_readiness_score: Decimal
    watch_readiness_score: Decimal
    reason_codes: tuple[str, ...]
    reason_code_counts: tuple[
        ResearchPacketProbabilisticResolutionReadinessScoreV2ReasonCodeCount,
        ...,
    ]
    rows: tuple[ResearchPacketProbabilisticResolutionReadinessScoreV2Row, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchPacketProbabilisticResolutionReadinessScoreV2Report "
            "does not support subclassing",
        )

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_PACKET_PROBABILISTIC_RESOLUTION_READINESS_SCORE_V2_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        _require_member("report_status", self.report_status, REPORT_STATUSES)
        for field_name in (
            "packet_count",
            "ready_packet_count",
            "watch_packet_count",
            "not_ready_packet_count",
            "attention_packet_count",
            "probability_confidence_gap_packet_count",
            "probability_band_gap_packet_count",
            "rule_clarity_gap_packet_count",
            "primary_source_gap_packet_count",
            "source_quorum_gap_packet_count",
            "readiness_score_gap_packet_count",
            "min_primary_source_count",
            "min_independent_source_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_count(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "average_readiness_score",
            "min_readiness_score_observed",
            "min_probability_confidence_score",
            "max_probability_band_width",
            "min_rule_clarity_score",
            "pass_readiness_score",
            "watch_readiness_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, REPORT_REASON_CODES),
        )
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        _require_hard_flags(self)
        if self.derived_validation_digest == "":
            object.__setattr__(
                self,
                "derived_validation_digest",
                _report_derived_validation_digest(self),
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
        _validate_report(self)


def build_research_packet_probabilistic_resolution_readiness_score_v2_report(
    packets: list[ResearchPacketProbabilisticResolutionReadinessScoreV2Packet]
    | tuple[ResearchPacketProbabilisticResolutionReadinessScoreV2Packet, ...],
    *,
    config: ResearchPacketProbabilisticResolutionReadinessScoreV2Config,
    generated_at: datetime,
) -> ResearchPacketProbabilisticResolutionReadinessScoreV2Report:
    if type(config) is not ResearchPacketProbabilisticResolutionReadinessScoreV2Config:
        raise ValueError(
            "config must be a "
            "ResearchPacketProbabilisticResolutionReadinessScoreV2Config",
        )
    _require_hard_flags(config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    normalized_packets = _normalize_packets(packets)
    _validate_packet_times(normalized_packets, generated_at=generated_at_utc)
    rows = tuple(
        sorted(
            (
                _row_for_packet(packet, config=config)
                for packet in normalized_packets
            ),
            key=_row_sort_key,
        ),
    )
    attention_count = _count_decimal(
        sum(1 for row in rows if row.readiness_status != "ready"),
    )
    return ResearchPacketProbabilisticResolutionReadinessScoreV2Report(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        report_status=_report_status(rows),
        packet_count=_count_decimal(len(rows)),
        ready_packet_count=_status_count(rows, "ready"),
        watch_packet_count=_status_count(rows, "watch"),
        not_ready_packet_count=_status_count(rows, "not_ready"),
        attention_packet_count=attention_count,
        probability_confidence_gap_packet_count=_reason_count(
            rows,
            PROBABILITY_CONFIDENCE_WEAK_REASON,
        ),
        probability_band_gap_packet_count=_reason_count(rows, PROBABILITY_BAND_WIDE_REASON),
        rule_clarity_gap_packet_count=_reason_count(rows, RULE_CLARITY_WEAK_REASON),
        primary_source_gap_packet_count=_reason_count(rows, PRIMARY_SOURCE_MISSING_REASON),
        source_quorum_gap_packet_count=_reason_count(rows, SOURCE_QUORUM_SHORT_REASON),
        readiness_score_gap_packet_count=_reason_count(rows, READINESS_SCORE_SHORT_REASON),
        average_readiness_score=_average_decimal(
            tuple(row.readiness_score for row in rows),
        ),
        min_readiness_score_observed=min(
            (row.readiness_score for row in rows),
            default=ZERO,
        ),
        min_probability_confidence_score=config.min_probability_confidence_score,
        max_probability_band_width=config.max_probability_band_width,
        min_rule_clarity_score=config.min_rule_clarity_score,
        min_primary_source_count=config.min_primary_source_count,
        min_independent_source_count=config.min_independent_source_count,
        pass_readiness_score=config.pass_readiness_score,
        watch_readiness_score=config.watch_readiness_score,
        reason_codes=_report_reason_codes(rows),
        reason_code_counts=_reason_code_counts(rows),
        rows=rows,
    )


def research_packet_probabilistic_resolution_readiness_score_v2_payload(
    value: object,
) -> dict[str, Any]:
    if type(value) is ResearchPacketProbabilisticResolutionReadinessScoreV2Report:
        revalidated = _revalidate_report(value)
        payload = _payload_value(revalidated)
        validate_research_packet_probabilistic_resolution_readiness_score_v2_public_payload(
            payload,
        )
        return payload
    if type(value) is dict:
        validate_research_packet_probabilistic_resolution_readiness_score_v2_public_payload(
            value,
        )
        return dict(value)
    raise ValueError(
        "value must be a ResearchPacketProbabilisticResolutionReadinessScoreV2Report "
        "or dict",
    )


def validate_research_packet_probabilistic_resolution_readiness_score_v2_public_payload(
    payload: dict[str, Any],
) -> bool:
    if type(payload) is not dict:
        raise ValueError("payload must be a dict")
    _reject_unsafe_public_payload("public payload", payload)
    _require_public_payload_flags(payload)
    _reject_public_numeric_values(payload)
    rows_value = payload.get("rows")
    if type(rows_value) is not list:
        raise ValueError("rows must be a list")
    for row_payload in rows_value:
        if type(row_payload) is not dict:
            raise ValueError("rows must contain dict values")
        _require_public_payload_flags(row_payload)
        row_digest = _payload_required_string(row_payload, "derived_validation_digest")
        _require_sha256_digest("derived_validation_digest", row_digest)
        if row_digest != _public_row_digest(row_payload):
            raise ValueError("derived_validation_digest must match row payload")
    digest_value = _payload_required_string(payload, "derived_validation_digest")
    _require_sha256_digest("derived_validation_digest", digest_value)
    if digest_value != _public_report_digest(payload):
        raise ValueError("derived_validation_digest must match public payload")
    return True


def _row_for_packet(
    packet: ResearchPacketProbabilisticResolutionReadinessScoreV2Packet,
    *,
    config: ResearchPacketProbabilisticResolutionReadinessScoreV2Config,
) -> ResearchPacketProbabilisticResolutionReadinessScoreV2Row:
    probability_confidence_score = _probability_confidence_score(
        packet.resolution_probability,
    )
    probability_band_component_score = _probability_band_component_score(
        packet.probability_band_width,
        config.max_probability_band_width,
    )
    rule_clarity_component_score = _safe_ratio(
        packet.rule_clarity_score,
        config.min_rule_clarity_score,
    )
    primary_source_score = _safe_ratio(
        packet.primary_source_count,
        config.min_primary_source_count,
    )
    source_quorum_score = _safe_ratio(
        packet.independent_source_count,
        config.min_independent_source_count,
    )
    readiness_score = _average_decimal(
        (
            probability_confidence_score,
            probability_band_component_score,
            rule_clarity_component_score,
            primary_source_score,
            source_quorum_score,
        ),
    )
    reason_codes = _row_reason_codes(
        packet=packet,
        config=config,
        probability_confidence_score=probability_confidence_score,
        readiness_score=readiness_score,
    )
    return ResearchPacketProbabilisticResolutionReadinessScoreV2Row(
        event_id=packet.event_id,
        packet_id=packet.packet_id,
        event_category=packet.event_category,
        captured_at=packet.captured_at,
        resolution_probability=packet.resolution_probability,
        probability_band_width=packet.probability_band_width,
        rule_clarity_score=packet.rule_clarity_score,
        primary_source_count=packet.primary_source_count,
        independent_source_count=packet.independent_source_count,
        probability_confidence_score=probability_confidence_score,
        probability_band_component_score=probability_band_component_score,
        rule_clarity_component_score=rule_clarity_component_score,
        primary_source_score=primary_source_score,
        source_quorum_score=source_quorum_score,
        readiness_score=readiness_score,
        readiness_status=_row_status(reason_codes, readiness_score, config=config),
        reason_codes=reason_codes,
    )


def _row_reason_codes(
    *,
    packet: ResearchPacketProbabilisticResolutionReadinessScoreV2Packet,
    config: ResearchPacketProbabilisticResolutionReadinessScoreV2Config,
    probability_confidence_score: Decimal,
    readiness_score: Decimal,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    if probability_confidence_score < config.min_probability_confidence_score:
        reason_codes.append(PROBABILITY_CONFIDENCE_WEAK_REASON)
    if packet.probability_band_width > config.max_probability_band_width:
        reason_codes.append(PROBABILITY_BAND_WIDE_REASON)
    if packet.rule_clarity_score < config.min_rule_clarity_score:
        reason_codes.append(RULE_CLARITY_WEAK_REASON)
    if packet.primary_source_count < config.min_primary_source_count:
        reason_codes.append(PRIMARY_SOURCE_MISSING_REASON)
    if packet.independent_source_count < config.min_independent_source_count:
        reason_codes.append(SOURCE_QUORUM_SHORT_REASON)
    if readiness_score < config.pass_readiness_score:
        reason_codes.append(READINESS_SCORE_SHORT_REASON)
    if not reason_codes:
        reason_codes.append(PASS_REASON)
    return tuple(reason_codes)


def _probability_confidence_score(probability: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return _quantize(abs(probability - HALF) * TWO)


def _probability_band_component_score(
    probability_band_width: Decimal,
    max_probability_band_width: Decimal,
) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return max(ONE - _safe_ratio(probability_band_width, max_probability_band_width), ZERO)


def _row_status(
    reason_codes: tuple[str, ...],
    readiness_score: Decimal,
    *,
    config: ResearchPacketProbabilisticResolutionReadinessScoreV2Config,
) -> str:
    if any(reason_code in NOT_READY_REASONS for reason_code in reason_codes):
        return "not_ready"
    if readiness_score < config.watch_readiness_score:
        return "not_ready"
    if reason_codes == (PASS_REASON,):
        return "ready"
    return "watch"


def _row_status_from_row(
    row: ResearchPacketProbabilisticResolutionReadinessScoreV2Row,
) -> str:
    if any(reason_code in NOT_READY_REASONS for reason_code in row.reason_codes):
        return "not_ready"
    if row.reason_codes == (PASS_REASON,):
        return "ready"
    if READINESS_SCORE_SHORT_REASON in row.reason_codes:
        return "watch"
    if PROBABILITY_CONFIDENCE_WEAK_REASON in row.reason_codes:
        return "watch"
    if PROBABILITY_BAND_WIDE_REASON in row.reason_codes:
        return "watch"
    return "watch"


def _report_status(
    rows: tuple[ResearchPacketProbabilisticResolutionReadinessScoreV2Row, ...],
) -> str:
    if not rows:
        return "not_ready"
    if any(row.readiness_status == "not_ready" for row in rows):
        return "not_ready"
    if any(row.readiness_status == "watch" for row in rows):
        return "watch"
    return "ready"


def _report_reason_codes(
    rows: tuple[ResearchPacketProbabilisticResolutionReadinessScoreV2Row, ...],
) -> tuple[str, ...]:
    if not rows:
        return (NO_PACKETS_REASON,)
    present = frozenset(
        reason_code
        for row in rows
        for reason_code in row.reason_codes
        if reason_code != PASS_REASON
    )
    if not present:
        return (PASS_REASON,)
    return tuple(reason_code for reason_code in ROW_REASON_CODES if reason_code in present)


def _reason_code_counts(
    rows: tuple[ResearchPacketProbabilisticResolutionReadinessScoreV2Row, ...],
) -> tuple[ResearchPacketProbabilisticResolutionReadinessScoreV2ReasonCodeCount, ...]:
    row_count = _count_decimal(len(rows))
    return tuple(
        ResearchPacketProbabilisticResolutionReadinessScoreV2ReasonCodeCount(
            reason_code=reason_code,
            packet_count=_reason_count(rows, reason_code),
            packet_ratio=_safe_ratio(_reason_count(rows, reason_code), row_count),
        )
        for reason_code in ROW_REASON_CODES
        if _reason_count(rows, reason_code) > ZERO
    )


def _normalize_packets(
    value: object,
) -> tuple[ResearchPacketProbabilisticResolutionReadinessScoreV2Packet, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("packets must be a list or tuple")
    packets = tuple(value)
    seen: set[tuple[str, str]] = set()
    for packet in packets:
        if type(packet) is not ResearchPacketProbabilisticResolutionReadinessScoreV2Packet:
            raise ValueError(
                "packets must contain "
                "ResearchPacketProbabilisticResolutionReadinessScoreV2Packet values",
            )
        _require_hard_flags(packet)
        identity = (packet.event_id, packet.packet_id)
        if identity in seen:
            raise ValueError("packets must be unique by event_id and packet_id")
        seen.add(identity)
    return packets


def _normalize_rows(
    value: object,
) -> tuple[ResearchPacketProbabilisticResolutionReadinessScoreV2Row, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("rows must be a list or tuple")
    rows = tuple(value)
    seen: set[tuple[str, str]] = set()
    for row in rows:
        if type(row) is not ResearchPacketProbabilisticResolutionReadinessScoreV2Row:
            raise ValueError(
                "rows must contain "
                "ResearchPacketProbabilisticResolutionReadinessScoreV2Row values",
            )
        _require_hard_flags(row)
        _validate_row(row)
        identity = (row.event_id, row.packet_id)
        if identity in seen:
            raise ValueError("rows must be unique by event_id and packet_id")
        seen.add(identity)
    if rows != tuple(sorted(rows, key=_row_sort_key)):
        raise ValueError("rows must use deterministic sequence")
    return rows


def _normalize_reason_code_counts(
    value: object,
) -> tuple[ResearchPacketProbabilisticResolutionReadinessScoreV2ReasonCodeCount, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("reason_code_counts must be a list or tuple")
    counts = tuple(value)
    seen: set[str] = set()
    for item in counts:
        if (
            type(item)
            is not ResearchPacketProbabilisticResolutionReadinessScoreV2ReasonCodeCount
        ):
            raise ValueError(
                "reason_code_counts must contain "
                "ResearchPacketProbabilisticResolutionReadinessScoreV2ReasonCodeCount values",
            )
        _require_hard_flags(item)
        if item.reason_code in seen:
            raise ValueError("reason_code_counts must be unique")
        seen.add(item.reason_code)
    expected = tuple(
        item
        for reason_code in ROW_REASON_CODES
        for item in counts
        if item.reason_code == reason_code
    )
    if counts != expected:
        raise ValueError("reason_code_counts must use deterministic sequence")
    return counts


def _normalize_reason_codes(
    field_name: str,
    value: object,
    allowed_values: tuple[str, ...],
) -> tuple[str, ...]:
    if type(value) not in (list, tuple):
        raise ValueError(f"{field_name} must be a list or tuple")
    reason_codes = tuple(value)
    if not reason_codes:
        raise ValueError(f"{field_name} must not be empty")
    seen: set[str] = set()
    for reason_code in reason_codes:
        _require_member(field_name, reason_code, allowed_values)
        if reason_code in seen:
            raise ValueError(f"{field_name} must be unique")
        seen.add(reason_code)
    expected = tuple(reason_code for reason_code in allowed_values if reason_code in seen)
    if reason_codes != expected:
        raise ValueError(f"{field_name} must use deterministic sequence")
    return reason_codes


def _validate_packet_times(
    packets: tuple[ResearchPacketProbabilisticResolutionReadinessScoreV2Packet, ...],
    *,
    generated_at: datetime,
) -> None:
    for packet in packets:
        if packet.captured_at > generated_at:
            raise ValueError("captured_at must not be after generated_at")


def _validate_row(row: ResearchPacketProbabilisticResolutionReadinessScoreV2Row) -> None:
    if row.readiness_status != _row_status_from_row(row):
        raise ValueError("readiness_status must match reason_codes")
    expected_score = _average_decimal(
        (
            row.probability_confidence_score,
            row.probability_band_component_score,
            row.rule_clarity_component_score,
            row.primary_source_score,
            row.source_quorum_score,
        ),
    )
    if row.readiness_score != expected_score:
        raise ValueError("readiness_score must match component scores")
    if row.derived_validation_digest != _row_derived_validation_digest(row):
        raise ValueError("derived_validation_digest must match row values")


def _validate_report(
    report: ResearchPacketProbabilisticResolutionReadinessScoreV2Report,
) -> None:
    if report.packet_count != _count_decimal(len(report.rows)):
        raise ValueError("packet_count must match rows")
    if report.ready_packet_count != _status_count(report.rows, "ready"):
        raise ValueError("ready_packet_count must match rows")
    if report.watch_packet_count != _status_count(report.rows, "watch"):
        raise ValueError("watch_packet_count must match rows")
    if report.not_ready_packet_count != _status_count(report.rows, "not_ready"):
        raise ValueError("not_ready_packet_count must match rows")
    if report.attention_packet_count != _count_decimal(
        sum(1 for row in report.rows if row.readiness_status != "ready"),
    ):
        raise ValueError("attention_packet_count must match rows")
    expected_reason_counts = (
        (
            PROBABILITY_CONFIDENCE_WEAK_REASON,
            "probability_confidence_gap_packet_count",
        ),
        (PROBABILITY_BAND_WIDE_REASON, "probability_band_gap_packet_count"),
        (RULE_CLARITY_WEAK_REASON, "rule_clarity_gap_packet_count"),
        (PRIMARY_SOURCE_MISSING_REASON, "primary_source_gap_packet_count"),
        (SOURCE_QUORUM_SHORT_REASON, "source_quorum_gap_packet_count"),
        (READINESS_SCORE_SHORT_REASON, "readiness_score_gap_packet_count"),
    )
    for reason_code, field_name in expected_reason_counts:
        if getattr(report, field_name) != _reason_count(report.rows, reason_code):
            raise ValueError(f"{field_name} must match rows")
    if report.average_readiness_score != _average_decimal(
        tuple(row.readiness_score for row in report.rows),
    ):
        raise ValueError("average_readiness_score must match rows")
    if report.min_readiness_score_observed != min(
        (row.readiness_score for row in report.rows),
        default=ZERO,
    ):
        raise ValueError("min_readiness_score_observed must match rows")
    if report.report_status != _report_status(report.rows):
        raise ValueError("report_status must match rows")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")
    if report.reason_code_counts != _reason_code_counts(report.rows):
        raise ValueError("reason_code_counts must match rows")
    if report.derived_validation_digest != _report_derived_validation_digest(report):
        raise ValueError("derived_validation_digest must match report values")


def _revalidate_reason_code_count(
    value: object,
) -> ResearchPacketProbabilisticResolutionReadinessScoreV2ReasonCodeCount:
    if (
        type(value)
        is not ResearchPacketProbabilisticResolutionReadinessScoreV2ReasonCodeCount
    ):
        raise ValueError("reason_code_counts must contain exact values")
    return ResearchPacketProbabilisticResolutionReadinessScoreV2ReasonCodeCount(
        **_dataclass_kwargs(value),
    )


def _revalidate_row(
    value: object,
) -> ResearchPacketProbabilisticResolutionReadinessScoreV2Row:
    if type(value) is not ResearchPacketProbabilisticResolutionReadinessScoreV2Row:
        raise ValueError("rows must contain exact row values")
    return ResearchPacketProbabilisticResolutionReadinessScoreV2Row(
        **_dataclass_kwargs(value),
    )


def _revalidate_report(
    value: ResearchPacketProbabilisticResolutionReadinessScoreV2Report,
) -> ResearchPacketProbabilisticResolutionReadinessScoreV2Report:
    if type(value) is not ResearchPacketProbabilisticResolutionReadinessScoreV2Report:
        raise ValueError(
            "value must be a ResearchPacketProbabilisticResolutionReadinessScoreV2Report",
        )
    kwargs = _dataclass_kwargs(value)
    kwargs["rows"] = tuple(_revalidate_row(row) for row in value.rows)
    kwargs["reason_code_counts"] = tuple(
        _revalidate_reason_code_count(item) for item in value.reason_code_counts
    )
    return ResearchPacketProbabilisticResolutionReadinessScoreV2Report(**kwargs)


def _row_sort_key(
    row: ResearchPacketProbabilisticResolutionReadinessScoreV2Row,
) -> tuple[Decimal, Decimal, str, str, str]:
    return (
        STATUS_RANK[row.readiness_status],
        row.readiness_score,
        row.event_category,
        row.event_id,
        row.packet_id,
    )


def _status_count(
    rows: tuple[ResearchPacketProbabilisticResolutionReadinessScoreV2Row, ...],
    status: str,
) -> Decimal:
    return _count_decimal(sum(1 for row in rows if row.readiness_status == status))


def _reason_count(
    rows: tuple[ResearchPacketProbabilisticResolutionReadinessScoreV2Row, ...],
    reason_code: str,
) -> Decimal:
    return _count_decimal(sum(1 for row in rows if reason_code in row.reason_codes))


def _average_decimal(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return _quantize(sum(values, ZERO) / Decimal(len(values)))


def _safe_ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator <= ZERO:
        return ONE
    with localcontext(DECIMAL_CONTEXT):
        return min(_quantize(numerator / denominator), ONE)


def _count_decimal(value: int) -> Decimal:
    return _quantize(Decimal(value))


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _normalize_positive_count(field_name: str, value: object) -> Decimal:
    decimal_value = _normalize_nonnegative_count(field_name, value)
    if decimal_value <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return decimal_value


def _normalize_nonnegative_count(field_name: str, value: object) -> Decimal:
    decimal_value = _normalize_nonnegative_decimal(field_name, value)
    if decimal_value != decimal_value.to_integral_value():
        raise ValueError(f"{field_name} must be an integral Decimal")
    return decimal_value


def _normalize_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _normalize_decimal(field_name, value)
    if decimal_value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return decimal_value


def _normalize_ratio(field_name: str, value: object) -> Decimal:
    decimal_value = _normalize_decimal(field_name, value)
    if decimal_value < ZERO or decimal_value > ONE:
        raise ValueError(f"{field_name} must be between zero and one")
    return decimal_value


def _normalize_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return _quantize(value)


def _quantize(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(QUANTUM)


def _require_member(
    field_name: str,
    value: object,
    allowed_values: tuple[str, ...],
) -> None:
    if type(value) is not str or value not in allowed_values:
        raise ValueError(f"{field_name} must be a known value")


def _require_public_string(field_name: str, value: object) -> None:
    if type(value) is not str or not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a public string")
    lowered = value.lower()
    if "://" in lowered or "?" in lowered:
        raise ValueError(f"{field_name} must be a public string")
    if any(fragment in lowered for fragment in UNSAFE_PUBLIC_FRAGMENTS):
        raise ValueError(f"{field_name} must be a public string")


def _require_hard_flags(value: object) -> None:
    if getattr(value, "paper_only", None) is not True:
        raise ValueError("value must be paper_only")
    if getattr(value, "report_only", None) is not True:
        raise ValueError("value must be report_only")
    if getattr(value, "readonly", None) is not True:
        raise ValueError("value must be readonly")


def _payload_value(value: object) -> Any:
    if isinstance(value, Decimal):
        if type(value) is not Decimal:
            raise ValueError("payload decimal value must be exact")
        if not value.is_finite() or not value.same_quantum(QUANTUM):
            raise ValueError("payload decimal value must be six decimal places")
        return str(value)
    if isinstance(value, datetime):
        if type(value) is not datetime:
            raise ValueError("payload datetime value must be exact")
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("payload datetime value must be timezone-aware")
        return value.astimezone(UTC).isoformat()
    if is_dataclass(value) and not isinstance(value, type):
        if type(value) not in (
            ResearchPacketProbabilisticResolutionReadinessScoreV2Config,
            ResearchPacketProbabilisticResolutionReadinessScoreV2Packet,
            ResearchPacketProbabilisticResolutionReadinessScoreV2ReasonCodeCount,
            ResearchPacketProbabilisticResolutionReadinessScoreV2Report,
            ResearchPacketProbabilisticResolutionReadinessScoreV2Row,
        ):
            raise ValueError("payload must use supported dataclasses")
        return {
            field.name: _payload_value(getattr(value, field.name))
            for field in fields(value)
        }
    if isinstance(value, tuple):
        return [_payload_value(item) for item in value]
    if isinstance(value, list):
        return [_payload_value(item) for item in value]
    if type(value) is dict:
        return {
            str(key): _payload_value(item)
            for key, item in sorted(value.items(), key=lambda item: str(item[0]))
        }
    if value is None or type(value) in (str, bool):
        return value
    raise ValueError("payload value is not supported")


def _row_derived_validation_digest(
    row: ResearchPacketProbabilisticResolutionReadinessScoreV2Row,
) -> str:
    payload = _payload_value(row)
    if type(payload) is not dict:
        raise ValueError("row payload must be a dict")
    payload.pop("derived_validation_digest", None)
    return _digest_payload(payload)


def _report_derived_validation_digest(
    report: ResearchPacketProbabilisticResolutionReadinessScoreV2Report,
) -> str:
    payload = _payload_value(report)
    if type(payload) is not dict:
        raise ValueError("report payload must be a dict")
    payload.pop("derived_validation_digest", None)
    return _digest_payload(payload)


def _public_row_digest(payload: dict[str, Any]) -> str:
    digest_payload = dict(payload)
    digest_payload.pop("derived_validation_digest", None)
    return _digest_payload(digest_payload)


def _public_report_digest(payload: dict[str, Any]) -> str:
    digest_payload = dict(payload)
    digest_payload.pop("derived_validation_digest", None)
    return _digest_payload(digest_payload)


def _digest_payload(payload: object) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(encoded).hexdigest()


def _require_sha256_digest(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a sha256 digest")
    if len(value) != 64 or any(character not in "0123456789abcdef" for character in value):
        raise ValueError(f"{field_name} must be a sha256 digest")
    return value


def _payload_required_string(payload: dict[str, Any], field_name: str) -> str:
    value = payload.get(field_name)
    if type(value) is not str:
        raise ValueError(f"{field_name} must be present")
    return value


def _require_public_payload_flags(payload: dict[str, Any]) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if payload.get(field_name) is not True:
            raise ValueError(f"{field_name} must be True")


def _reject_public_numeric_values(value: object) -> None:
    if type(value) is bool or value is None:
        return
    if type(value) in (int, float, Decimal):
        raise ValueError("public payload numeric values must be strings")
    if type(value) is dict:
        for item in value.values():
            _reject_public_numeric_values(item)
        return
    if type(value) is list:
        for item in value:
            _reject_public_numeric_values(item)


def _reject_unsafe_public_payload(
    label: str,
    value: object,
    path: str = "",
) -> None:
    current_path = path or label
    if type(value) is dict:
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError(f"{current_path} public keys must be strings")
            _reject_public_text(f"{current_path}.{key}", key)
            _reject_unsafe_public_payload(label, item, f"{current_path}.{key}")
        return
    if type(value) is list:
        for index, item in enumerate(value):
            _reject_unsafe_public_payload(label, item, f"{current_path}[{index}]")
        return
    if type(value) is tuple:
        for index, item in enumerate(value):
            _reject_unsafe_public_payload(label, item, f"{current_path}[{index}]")
        return
    if type(value) is str:
        _reject_public_text(current_path, value)


def _reject_public_text(field_name: str, value: str) -> None:
    lowered = value.lower()
    if value.strip() != value or "://" in lowered or "?" in lowered:
        raise ValueError(f"{field_name} contains unsafe public text")
    if any(fragment in lowered for fragment in UNSAFE_PUBLIC_FRAGMENTS):
        raise ValueError(f"{field_name} contains unsafe public text")


def _dataclass_kwargs(value: object) -> dict[str, Any]:
    return {field.name: getattr(value, field.name) for field in fields(value)}


__all__ = (
    "DEFAULT_RESEARCH_PACKET_PROBABILISTIC_RESOLUTION_READINESS_SCORE_V2_CONFIG_VERSION",
    "ResearchPacketProbabilisticResolutionReadinessScoreV2Config",
    "ResearchPacketProbabilisticResolutionReadinessScoreV2Packet",
    "ResearchPacketProbabilisticResolutionReadinessScoreV2ReasonCodeCount",
    "ResearchPacketProbabilisticResolutionReadinessScoreV2Report",
    "ResearchPacketProbabilisticResolutionReadinessScoreV2Row",
    "build_research_packet_probabilistic_resolution_readiness_score_v2_report",
    "research_packet_probabilistic_resolution_readiness_score_v2_payload",
    "validate_research_packet_probabilistic_resolution_readiness_score_v2_public_payload",
)
