"""Phase 1 context source gap report."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from numbers import Number
from typing import Any


DEFAULT_RESEARCH_PACKET_MARKET_CONTEXT_SOURCE_GAP_V2_CONFIG_VERSION = (
    "research-packet-market-context-source-gap-v2"
)

PASS_REASON = "research_packet_market_context_source_gap_v2_passed"
MISSING_MACRO_SOURCE_REASON = (
    "research_packet_market_context_source_gap_v2_missing_macro_source"
)
MISSING_CONTEXT_SOURCE_REASON = (
    "research_packet_market_context_source_gap_v2_missing_context_source"
)
MISSING_OFFICIAL_ANCHOR_REASON = (
    "research_packet_market_context_source_gap_v2_missing_official_anchor"
)
STALE_OFFICIAL_ANCHOR_REASON = (
    "research_packet_market_context_source_gap_v2_stale_official_anchor"
)
WEAK_SOURCE_FAMILY_REASON = (
    "research_packet_market_context_source_gap_v2_weak_source_family_independence"
)
CONTRADICTION_ELEVATED_REASON = (
    "research_packet_market_context_source_gap_v2_contradiction_elevated"
)
CONTRADICTION_SEVERE_REASON = (
    "research_packet_market_context_source_gap_v2_contradiction_severe"
)
UNEXPLAINED_PROBABILITY_MOVEMENT_REASON = (
    "research_packet_market_context_source_gap_v2_unexplained_probability_movement"
)
MISSING_RESOLUTION_HORIZON_REASON = (
    "research_packet_market_context_source_gap_v2_missing_resolution_horizon"
)
NEAR_RESOLUTION_HORIZON_REASON = (
    "research_packet_market_context_source_gap_v2_near_resolution_horizon"
)

ROW_REASON_CODES = (
    MISSING_MACRO_SOURCE_REASON,
    MISSING_CONTEXT_SOURCE_REASON,
    MISSING_OFFICIAL_ANCHOR_REASON,
    STALE_OFFICIAL_ANCHOR_REASON,
    WEAK_SOURCE_FAMILY_REASON,
    CONTRADICTION_ELEVATED_REASON,
    CONTRADICTION_SEVERE_REASON,
    UNEXPLAINED_PROBABILITY_MOVEMENT_REASON,
    MISSING_RESOLUTION_HORIZON_REASON,
    NEAR_RESOLUTION_HORIZON_REASON,
)
REPORT_REASON_CODES = (PASS_REASON,) + ROW_REASON_CODES
BLOCKED_REASONS = frozenset(
    (
        MISSING_MACRO_SOURCE_REASON,
        MISSING_CONTEXT_SOURCE_REASON,
        MISSING_OFFICIAL_ANCHOR_REASON,
        STALE_OFFICIAL_ANCHOR_REASON,
        CONTRADICTION_SEVERE_REASON,
        UNEXPLAINED_PROBABILITY_MOVEMENT_REASON,
        MISSING_RESOLUTION_HORIZON_REASON,
    ),
)
REPORT_STATUSES = ("pass", "watch", "blocked")
STATUS_RANK = {
    "blocked": Decimal("0.000000"),
    "watch": Decimal("1.000000"),
    "pass": Decimal("2.000000"),
}

DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
QUANTUM = Decimal("0.000001")
MICROSECOND_DIVISOR = Decimal("1000000")


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
class ResearchPacketMarketContextSourceGapV2Config:
    config_version: str = DEFAULT_RESEARCH_PACKET_MARKET_CONTEXT_SOURCE_GAP_V2_CONFIG_VERSION
    max_official_anchor_age_seconds: Decimal = Decimal("3600.000000")
    min_independent_source_family_count: Decimal = Decimal("2.000000")
    severe_contradiction_threshold: Decimal = Decimal("0.750000")
    unexplained_probability_move_threshold: Decimal = Decimal("0.050000")
    near_resolution_horizon_seconds: Decimal = Decimal("86400.000000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchPacketMarketContextSourceGapV2Config does not support subclassing",
        )

    def __post_init__(self) -> None:
        _require_public_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_PACKET_MARKET_CONTEXT_SOURCE_GAP_V2_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "max_official_anchor_age_seconds",
            "min_independent_source_family_count",
            "near_resolution_horizon_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_positive_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "severe_contradiction_threshold",
            "unexplained_probability_move_threshold",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        _require_hard_flags(self)


@dataclass(frozen=True)
class ResearchPacketMarketContextSourceGapV2Packet:
    event_id: str
    packet_id: str
    event_category: str
    captured_at: datetime
    required_macro_source_count: Decimal
    present_macro_source_count: Decimal
    required_context_source_count: Decimal
    present_context_source_count: Decimal
    official_anchor_checked_at: datetime | None
    independent_source_family_count: Decimal
    contradiction_severity: Decimal
    probability_move_abs: Decimal
    movement_explanation: str | None
    resolution_at: datetime | None
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchPacketMarketContextSourceGapV2Packet does not support subclassing",
        )

    def __post_init__(self) -> None:
        for field_name in ("event_id", "packet_id", "event_category"):
            _require_public_string(field_name, getattr(self, field_name))
        object.__setattr__(self, "captured_at", _as_utc("captured_at", self.captured_at))
        object.__setattr__(
            self,
            "official_anchor_checked_at",
            _as_optional_utc(
                "official_anchor_checked_at",
                self.official_anchor_checked_at,
            ),
        )
        object.__setattr__(
            self,
            "resolution_at",
            _as_optional_utc("resolution_at", self.resolution_at),
        )
        for field_name in (
            "required_macro_source_count",
            "present_macro_source_count",
            "required_context_source_count",
            "present_context_source_count",
            "independent_source_family_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_count(field_name, getattr(self, field_name)),
            )
        for field_name in ("contradiction_severity", "probability_move_abs"):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "movement_explanation",
            _normalize_optional_public_string(
                "movement_explanation",
                self.movement_explanation,
            ),
        )
        _validate_packet(self)
        _require_hard_flags(self)


@dataclass(frozen=True)
class ResearchPacketMarketContextSourceGapV2ReasonCodeCount:
    reason_code: str
    packet_count: Decimal
    packet_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchPacketMarketContextSourceGapV2ReasonCodeCount does not support subclassing",
        )

    def __post_init__(self) -> None:
        _require_member("reason_code", self.reason_code, ROW_REASON_CODES)
        object.__setattr__(
            self,
            "packet_count",
            _normalize_positive_decimal("packet_count", self.packet_count),
        )
        object.__setattr__(
            self,
            "packet_ratio",
            _normalize_ratio("packet_ratio", self.packet_ratio),
        )
        _require_hard_flags(self)


@dataclass(frozen=True)
class ResearchPacketMarketContextSourceGapV2Row:
    event_id: str
    packet_id: str
    event_category: str
    captured_at: datetime
    official_anchor_checked_at: datetime | None
    official_anchor_age_seconds: Decimal | None
    resolution_at: datetime | None
    resolution_horizon_seconds: Decimal | None
    required_macro_source_count: Decimal
    present_macro_source_count: Decimal
    missing_macro_source_count: Decimal
    required_context_source_count: Decimal
    present_context_source_count: Decimal
    missing_context_source_count: Decimal
    independent_source_family_count: Decimal
    contradiction_severity: Decimal
    probability_move_abs: Decimal
    movement_explanation_present: bool
    gap_status: str
    reason_codes: tuple[str, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchPacketMarketContextSourceGapV2Row does not support subclassing",
        )

    def __post_init__(self) -> None:
        for field_name in ("event_id", "packet_id", "event_category"):
            _require_public_string(field_name, getattr(self, field_name))
        object.__setattr__(self, "captured_at", _as_utc("captured_at", self.captured_at))
        object.__setattr__(
            self,
            "official_anchor_checked_at",
            _as_optional_utc(
                "official_anchor_checked_at",
                self.official_anchor_checked_at,
            ),
        )
        object.__setattr__(
            self,
            "official_anchor_age_seconds",
            _normalize_optional_nonnegative_decimal(
                "official_anchor_age_seconds",
                self.official_anchor_age_seconds,
            ),
        )
        object.__setattr__(
            self,
            "resolution_at",
            _as_optional_utc("resolution_at", self.resolution_at),
        )
        object.__setattr__(
            self,
            "resolution_horizon_seconds",
            _normalize_optional_nonnegative_decimal(
                "resolution_horizon_seconds",
                self.resolution_horizon_seconds,
            ),
        )
        for field_name in (
            "required_macro_source_count",
            "present_macro_source_count",
            "missing_macro_source_count",
            "required_context_source_count",
            "present_context_source_count",
            "missing_context_source_count",
            "independent_source_family_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_count(field_name, getattr(self, field_name)),
            )
        for field_name in ("contradiction_severity", "probability_move_abs"):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        _require_bool("movement_explanation_present", self.movement_explanation_present)
        _require_member("gap_status", self.gap_status, REPORT_STATUSES)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, REPORT_REASON_CODES),
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
class ResearchPacketMarketContextSourceGapV2Report:
    generated_at: datetime
    config_version: str
    report_status: str
    packet_count: Decimal
    pass_packet_count: Decimal
    watch_packet_count: Decimal
    blocked_packet_count: Decimal
    attention_packet_count: Decimal
    attention_packet_ratio: Decimal
    missing_macro_source_packet_count: Decimal
    missing_context_source_packet_count: Decimal
    stale_official_anchor_packet_count: Decimal
    weak_source_family_packet_count: Decimal
    contradiction_packet_count: Decimal
    severe_contradiction_packet_count: Decimal
    unexplained_probability_movement_packet_count: Decimal
    near_resolution_horizon_packet_count: Decimal
    max_contradiction_severity: Decimal
    max_probability_move_abs: Decimal
    min_resolution_horizon_seconds: Decimal
    max_official_anchor_age_seconds: Decimal
    min_independent_source_family_count: Decimal
    severe_contradiction_threshold: Decimal
    unexplained_probability_move_threshold: Decimal
    near_resolution_horizon_seconds: Decimal
    reason_codes: tuple[str, ...]
    reason_code_counts: tuple[ResearchPacketMarketContextSourceGapV2ReasonCodeCount, ...]
    rows: tuple[ResearchPacketMarketContextSourceGapV2Row, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchPacketMarketContextSourceGapV2Report does not support subclassing",
        )

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_PACKET_MARKET_CONTEXT_SOURCE_GAP_V2_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        _require_member("report_status", self.report_status, REPORT_STATUSES)
        for field_name in (
            "packet_count",
            "pass_packet_count",
            "watch_packet_count",
            "blocked_packet_count",
            "attention_packet_count",
            "missing_macro_source_packet_count",
            "missing_context_source_packet_count",
            "stale_official_anchor_packet_count",
            "weak_source_family_packet_count",
            "contradiction_packet_count",
            "severe_contradiction_packet_count",
            "unexplained_probability_movement_packet_count",
            "near_resolution_horizon_packet_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_count(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "attention_packet_ratio",
            "max_contradiction_severity",
            "max_probability_move_abs",
            "severe_contradiction_threshold",
            "unexplained_probability_move_threshold",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "min_resolution_horizon_seconds",
            "max_official_anchor_age_seconds",
            "min_independent_source_family_count",
            "near_resolution_horizon_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
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


def build_research_packet_market_context_source_gap_v2_report(
    packets: list[ResearchPacketMarketContextSourceGapV2Packet]
    | tuple[ResearchPacketMarketContextSourceGapV2Packet, ...],
    *,
    config: ResearchPacketMarketContextSourceGapV2Config,
    generated_at: datetime,
) -> ResearchPacketMarketContextSourceGapV2Report:
    if type(config) is not ResearchPacketMarketContextSourceGapV2Config:
        raise ValueError("config must be a ResearchPacketMarketContextSourceGapV2Config")
    _require_hard_flags(config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    normalized_packets = _normalize_packets(packets)
    _validate_packet_times(normalized_packets, generated_at=generated_at_utc)
    rows = tuple(
        sorted(
            (
                _row_for_packet(packet, config=config, generated_at=generated_at_utc)
                for packet in normalized_packets
            ),
            key=_row_sort_key,
        ),
    )
    packet_count = _count_decimal(len(rows))
    attention_count = _count_decimal(sum(1 for row in rows if row.gap_status != "pass"))
    return ResearchPacketMarketContextSourceGapV2Report(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        report_status=_report_status(rows),
        packet_count=packet_count,
        pass_packet_count=_status_count(rows, "pass"),
        watch_packet_count=_status_count(rows, "watch"),
        blocked_packet_count=_status_count(rows, "blocked"),
        attention_packet_count=attention_count,
        attention_packet_ratio=_safe_ratio(attention_count, packet_count),
        missing_macro_source_packet_count=_reason_count(rows, MISSING_MACRO_SOURCE_REASON),
        missing_context_source_packet_count=_reason_count(rows, MISSING_CONTEXT_SOURCE_REASON),
        stale_official_anchor_packet_count=_reason_count(rows, STALE_OFFICIAL_ANCHOR_REASON),
        weak_source_family_packet_count=_reason_count(rows, WEAK_SOURCE_FAMILY_REASON),
        contradiction_packet_count=_count_decimal(
            sum(1 for row in rows if row.contradiction_severity > ZERO),
        ),
        severe_contradiction_packet_count=_reason_count(rows, CONTRADICTION_SEVERE_REASON),
        unexplained_probability_movement_packet_count=_reason_count(
            rows,
            UNEXPLAINED_PROBABILITY_MOVEMENT_REASON,
        ),
        near_resolution_horizon_packet_count=_reason_count(
            rows,
            NEAR_RESOLUTION_HORIZON_REASON,
        ),
        max_contradiction_severity=max(
            (row.contradiction_severity for row in rows),
            default=ZERO,
        ),
        max_probability_move_abs=max((row.probability_move_abs for row in rows), default=ZERO),
        min_resolution_horizon_seconds=min(
            (
                row.resolution_horizon_seconds
                for row in rows
                if row.resolution_horizon_seconds is not None
            ),
            default=ZERO,
        ),
        max_official_anchor_age_seconds=config.max_official_anchor_age_seconds,
        min_independent_source_family_count=config.min_independent_source_family_count,
        severe_contradiction_threshold=config.severe_contradiction_threshold,
        unexplained_probability_move_threshold=(
            config.unexplained_probability_move_threshold
        ),
        near_resolution_horizon_seconds=config.near_resolution_horizon_seconds,
        reason_codes=_report_reason_codes(rows),
        reason_code_counts=_reason_code_counts(rows),
        rows=rows,
    )


def research_packet_market_context_source_gap_v2_payload(value: object) -> dict[str, Any]:
    if type(value) is ResearchPacketMarketContextSourceGapV2Report:
        revalidated = _revalidate_report(value)
        payload = _payload_value(revalidated)
        validate_research_packet_market_context_source_gap_v2_public_payload(payload)
        return payload
    if type(value) is dict:
        validate_research_packet_market_context_source_gap_v2_public_payload(value)
        return dict(value)
    raise ValueError("value must be a ResearchPacketMarketContextSourceGapV2Report or dict")


def validate_research_packet_market_context_source_gap_v2_public_payload(
    payload: dict[str, Any],
) -> bool:
    if type(payload) is not dict:
        raise ValueError("payload must be a dict")
    _reject_unsafe_public_payload("payload", payload)
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
    packet: ResearchPacketMarketContextSourceGapV2Packet,
    *,
    config: ResearchPacketMarketContextSourceGapV2Config,
    generated_at: datetime,
) -> ResearchPacketMarketContextSourceGapV2Row:
    official_anchor_age_seconds = (
        None
        if packet.official_anchor_checked_at is None
        else _duration_seconds(generated_at, packet.official_anchor_checked_at)
    )
    resolution_horizon_seconds = (
        None
        if packet.resolution_at is None
        else max(_duration_seconds(packet.resolution_at, generated_at), ZERO)
    )
    missing_macro_source_count = max(
        packet.required_macro_source_count - packet.present_macro_source_count,
        ZERO,
    )
    missing_context_source_count = max(
        packet.required_context_source_count - packet.present_context_source_count,
        ZERO,
    )
    explanation_present = packet.movement_explanation is not None
    reason_codes = _row_reason_codes(
        packet=packet,
        config=config,
        official_anchor_age_seconds=official_anchor_age_seconds,
        resolution_horizon_seconds=resolution_horizon_seconds,
        missing_macro_source_count=missing_macro_source_count,
        missing_context_source_count=missing_context_source_count,
        movement_explanation_present=explanation_present,
    )
    return ResearchPacketMarketContextSourceGapV2Row(
        event_id=packet.event_id,
        packet_id=packet.packet_id,
        event_category=packet.event_category,
        captured_at=packet.captured_at,
        official_anchor_checked_at=packet.official_anchor_checked_at,
        official_anchor_age_seconds=official_anchor_age_seconds,
        resolution_at=packet.resolution_at,
        resolution_horizon_seconds=resolution_horizon_seconds,
        required_macro_source_count=packet.required_macro_source_count,
        present_macro_source_count=packet.present_macro_source_count,
        missing_macro_source_count=missing_macro_source_count,
        required_context_source_count=packet.required_context_source_count,
        present_context_source_count=packet.present_context_source_count,
        missing_context_source_count=missing_context_source_count,
        independent_source_family_count=packet.independent_source_family_count,
        contradiction_severity=packet.contradiction_severity,
        probability_move_abs=packet.probability_move_abs,
        movement_explanation_present=explanation_present,
        gap_status=_row_status(reason_codes),
        reason_codes=reason_codes,
    )


def _row_reason_codes(
    *,
    packet: ResearchPacketMarketContextSourceGapV2Packet,
    config: ResearchPacketMarketContextSourceGapV2Config,
    official_anchor_age_seconds: Decimal | None,
    resolution_horizon_seconds: Decimal | None,
    missing_macro_source_count: Decimal,
    missing_context_source_count: Decimal,
    movement_explanation_present: bool,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    if missing_macro_source_count > ZERO:
        reason_codes.append(MISSING_MACRO_SOURCE_REASON)
    if missing_context_source_count > ZERO:
        reason_codes.append(MISSING_CONTEXT_SOURCE_REASON)
    if packet.official_anchor_checked_at is None:
        reason_codes.append(MISSING_OFFICIAL_ANCHOR_REASON)
    elif (
        official_anchor_age_seconds is not None
        and official_anchor_age_seconds > config.max_official_anchor_age_seconds
    ):
        reason_codes.append(STALE_OFFICIAL_ANCHOR_REASON)
    if packet.independent_source_family_count < config.min_independent_source_family_count:
        reason_codes.append(WEAK_SOURCE_FAMILY_REASON)
    if packet.contradiction_severity >= config.severe_contradiction_threshold:
        reason_codes.append(CONTRADICTION_SEVERE_REASON)
    elif packet.contradiction_severity > ZERO:
        reason_codes.append(CONTRADICTION_ELEVATED_REASON)
    if (
        packet.probability_move_abs >= config.unexplained_probability_move_threshold
        and not movement_explanation_present
    ):
        reason_codes.append(UNEXPLAINED_PROBABILITY_MOVEMENT_REASON)
    if resolution_horizon_seconds is None:
        reason_codes.append(MISSING_RESOLUTION_HORIZON_REASON)
    elif resolution_horizon_seconds <= config.near_resolution_horizon_seconds:
        reason_codes.append(NEAR_RESOLUTION_HORIZON_REASON)
    if not reason_codes:
        reason_codes.append(PASS_REASON)
    return tuple(reason_codes)


def _row_status(reason_codes: tuple[str, ...]) -> str:
    if any(reason_code in BLOCKED_REASONS for reason_code in reason_codes):
        return "blocked"
    if reason_codes == (PASS_REASON,):
        return "pass"
    return "watch"


def _report_status(rows: tuple[ResearchPacketMarketContextSourceGapV2Row, ...]) -> str:
    if any(row.gap_status == "blocked" for row in rows):
        return "blocked"
    if any(row.gap_status == "watch" for row in rows):
        return "watch"
    return "pass"


def _report_reason_codes(
    rows: tuple[ResearchPacketMarketContextSourceGapV2Row, ...],
) -> tuple[str, ...]:
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
    rows: tuple[ResearchPacketMarketContextSourceGapV2Row, ...],
) -> tuple[ResearchPacketMarketContextSourceGapV2ReasonCodeCount, ...]:
    row_count = _count_decimal(len(rows))
    return tuple(
        ResearchPacketMarketContextSourceGapV2ReasonCodeCount(
            reason_code=reason_code,
            packet_count=_reason_count(rows, reason_code),
            packet_ratio=_safe_ratio(_reason_count(rows, reason_code), row_count),
        )
        for reason_code in ROW_REASON_CODES
        if _reason_count(rows, reason_code) > ZERO
    )


def _normalize_packets(
    value: object,
) -> tuple[ResearchPacketMarketContextSourceGapV2Packet, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("packets must be a list or tuple")
    packets = tuple(value)
    seen: set[tuple[str, str]] = set()
    for packet in packets:
        if type(packet) is not ResearchPacketMarketContextSourceGapV2Packet:
            raise ValueError(
                "packets must contain ResearchPacketMarketContextSourceGapV2Packet values",
            )
        _require_hard_flags(packet)
        key = (packet.event_id, packet.packet_id)
        if key in seen:
            raise ValueError("packets must be unique by event_id and packet_id")
        seen.add(key)
    return packets


def _normalize_rows(
    value: object,
) -> tuple[ResearchPacketMarketContextSourceGapV2Row, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("rows must be a list or tuple")
    rows = tuple(value)
    seen: set[tuple[str, str]] = set()
    for row in rows:
        if type(row) is not ResearchPacketMarketContextSourceGapV2Row:
            raise ValueError("rows must contain ResearchPacketMarketContextSourceGapV2Row values")
        _require_hard_flags(row)
        key = (row.event_id, row.packet_id)
        if key in seen:
            raise ValueError("rows must be unique by event_id and packet_id")
        seen.add(key)
    if rows != tuple(sorted(rows, key=_row_sort_key)):
        raise ValueError("rows must use deterministic sequence")
    return rows


def _normalize_reason_code_counts(
    value: object,
) -> tuple[ResearchPacketMarketContextSourceGapV2ReasonCodeCount, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("reason_code_counts must be a list or tuple")
    counts = tuple(value)
    seen: set[str] = set()
    for item in counts:
        if type(item) is not ResearchPacketMarketContextSourceGapV2ReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "ResearchPacketMarketContextSourceGapV2ReasonCodeCount values",
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


def _validate_packet(value: ResearchPacketMarketContextSourceGapV2Packet) -> None:
    if value.present_macro_source_count > value.required_macro_source_count:
        raise ValueError("present_macro_source_count must not exceed required_macro_source_count")
    if value.present_context_source_count > value.required_context_source_count:
        raise ValueError(
            "present_context_source_count must not exceed required_context_source_count",
        )


def _validate_packet_times(
    packets: tuple[ResearchPacketMarketContextSourceGapV2Packet, ...],
    *,
    generated_at: datetime,
) -> None:
    for packet in packets:
        for field_name in ("captured_at", "official_anchor_checked_at"):
            value = getattr(packet, field_name)
            if value is not None and value > generated_at:
                raise ValueError(f"{field_name} must not be after generated_at")


def _validate_row(row: ResearchPacketMarketContextSourceGapV2Row) -> None:
    if row.missing_macro_source_count != max(
        row.required_macro_source_count - row.present_macro_source_count,
        ZERO,
    ):
        raise ValueError("missing_macro_source_count must match source counts")
    if row.missing_context_source_count != max(
        row.required_context_source_count - row.present_context_source_count,
        ZERO,
    ):
        raise ValueError("missing_context_source_count must match source counts")
    if row.official_anchor_checked_at is None and row.official_anchor_age_seconds is not None:
        raise ValueError("official_anchor_age_seconds must be absent without anchor check")
    if row.official_anchor_checked_at is not None and row.official_anchor_age_seconds is None:
        raise ValueError("official_anchor_age_seconds is required with anchor check")
    if row.resolution_at is None and row.resolution_horizon_seconds is not None:
        raise ValueError("resolution_horizon_seconds must be absent without resolution_at")
    if row.resolution_at is not None and row.resolution_horizon_seconds is None:
        raise ValueError("resolution_horizon_seconds is required with resolution_at")
    if row.gap_status != _row_status(row.reason_codes):
        raise ValueError("gap_status must match reason_codes")
    if row.derived_validation_digest != _row_derived_validation_digest(row):
        raise ValueError("derived_validation_digest must match row fields")


def _validate_report(report: ResearchPacketMarketContextSourceGapV2Report) -> None:
    rows = report.rows
    packet_count = _count_decimal(len(rows))
    if report.packet_count != packet_count:
        raise ValueError("packet_count must match rows")
    for field_name, status in (
        ("pass_packet_count", "pass"),
        ("watch_packet_count", "watch"),
        ("blocked_packet_count", "blocked"),
    ):
        if getattr(report, field_name) != _status_count(rows, status):
            raise ValueError(f"{field_name} must match rows")
    if (
        report.pass_packet_count
        + report.watch_packet_count
        + report.blocked_packet_count
        != report.packet_count
    ):
        raise ValueError("status counts must match packet_count")
    if report.attention_packet_count != _count_decimal(
        sum(1 for row in rows if row.gap_status != "pass"),
    ):
        raise ValueError("attention_packet_count must match rows")
    if report.attention_packet_ratio != _safe_ratio(
        report.attention_packet_count,
        report.packet_count,
    ):
        raise ValueError("attention_packet_ratio must match counts")
    for field_name, reason_code in (
        ("missing_macro_source_packet_count", MISSING_MACRO_SOURCE_REASON),
        ("missing_context_source_packet_count", MISSING_CONTEXT_SOURCE_REASON),
        ("stale_official_anchor_packet_count", STALE_OFFICIAL_ANCHOR_REASON),
        ("weak_source_family_packet_count", WEAK_SOURCE_FAMILY_REASON),
        ("severe_contradiction_packet_count", CONTRADICTION_SEVERE_REASON),
        (
            "unexplained_probability_movement_packet_count",
            UNEXPLAINED_PROBABILITY_MOVEMENT_REASON,
        ),
        ("near_resolution_horizon_packet_count", NEAR_RESOLUTION_HORIZON_REASON),
    ):
        if getattr(report, field_name) != _reason_count(rows, reason_code):
            raise ValueError(f"{field_name} must match rows")
    if report.contradiction_packet_count != _count_decimal(
        sum(1 for row in rows if row.contradiction_severity > ZERO),
    ):
        raise ValueError("contradiction_packet_count must match rows")
    if report.max_contradiction_severity != max(
        (row.contradiction_severity for row in rows),
        default=ZERO,
    ):
        raise ValueError("max_contradiction_severity must match rows")
    if report.max_probability_move_abs != max(
        (row.probability_move_abs for row in rows),
        default=ZERO,
    ):
        raise ValueError("max_probability_move_abs must match rows")
    if report.min_resolution_horizon_seconds != min(
        (
            row.resolution_horizon_seconds
            for row in rows
            if row.resolution_horizon_seconds is not None
        ),
        default=ZERO,
    ):
        raise ValueError("min_resolution_horizon_seconds must match rows")
    if report.report_status != _report_status(rows):
        raise ValueError("report_status must match rows")
    if report.reason_codes != _report_reason_codes(rows):
        raise ValueError("reason_codes must match rows")
    if report.reason_code_counts != _reason_code_counts(rows):
        raise ValueError("reason_code_counts must match rows")
    if report.derived_validation_digest != _report_derived_validation_digest(report):
        raise ValueError("derived_validation_digest must match report fields")


def _row_sort_key(
    row: ResearchPacketMarketContextSourceGapV2Row,
) -> tuple[Decimal, Decimal, Decimal, str, str]:
    return (
        STATUS_RANK[row.gap_status],
        -_count_decimal(len(tuple(code for code in row.reason_codes if code != PASS_REASON))),
        -max(
            row.contradiction_severity,
            row.probability_move_abs,
        ),
        row.event_id,
        row.packet_id,
    )


def _status_count(
    rows: tuple[ResearchPacketMarketContextSourceGapV2Row, ...],
    status: str,
) -> Decimal:
    return _count_decimal(sum(1 for row in rows if row.gap_status == status))


def _reason_count(
    rows: tuple[ResearchPacketMarketContextSourceGapV2Row, ...],
    reason_code: str,
) -> Decimal:
    return _count_decimal(sum(1 for row in rows if reason_code in row.reason_codes))


def _count_decimal(value: int) -> Decimal:
    return _quantize_decimal(Decimal(value))


def _safe_ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return _quantize_decimal(numerator / denominator)


def _duration_seconds(later: datetime, earlier: datetime) -> Decimal:
    delta = later - earlier
    seconds = Decimal(delta.days * 86400 + delta.seconds)
    microseconds = Decimal(delta.microseconds) / MICROSECOND_DIVISOR
    with localcontext(DECIMAL_CONTEXT):
        return _quantize_decimal(seconds + microseconds)


def _normalize_positive_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_nonnegative_decimal(field_name, value)
    if normalized <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _normalize_positive_count(field_name: str, value: object) -> Decimal:
    normalized = _normalize_nonnegative_count(field_name, value)
    if normalized <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _normalize_nonnegative_count(field_name: str, value: object) -> Decimal:
    normalized = _normalize_nonnegative_decimal(field_name, value)
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{field_name} must be whole")
    return normalized


def _normalize_ratio(field_name: str, value: object) -> Decimal:
    normalized = _normalize_nonnegative_decimal(field_name, value)
    if normalized > ONE:
        raise ValueError(f"{field_name} must not exceed one")
    return normalized


def _normalize_optional_nonnegative_decimal(
    field_name: str,
    value: object,
) -> Decimal | None:
    if value is None:
        return None
    return _normalize_nonnegative_decimal(field_name, value)


def _normalize_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    normalized = _quantize_decimal(value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _quantize_decimal(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(QUANTUM)


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone aware")
    return value.astimezone(UTC)


def _as_optional_utc(field_name: str, value: object) -> datetime | None:
    if value is None:
        return None
    return _as_utc(field_name, value)


def _normalize_optional_public_string(field_name: str, value: object) -> str | None:
    if value is None:
        return None
    _require_public_string(field_name, value)
    return value


def _require_public_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if value == "" or value.strip() != value:
        raise ValueError(f"{field_name} must be canonical")
    if any(character.isspace() for character in value):
        raise ValueError(f"{field_name} must be canonical")
    _reject_public_text(field_name, value)


def _require_member(field_name: str, value: object, allowed_values: tuple[str, ...]) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if value not in allowed_values:
        raise ValueError(f"{field_name} must be supported")


def _require_bool(field_name: str, value: object) -> None:
    if type(value) is not bool:
        raise ValueError(f"{field_name} must be a bool")


def _require_hard_flags(value: object) -> None:
    for flag_name in ("paper_only", "report_only", "readonly"):
        if getattr(value, flag_name, None) is not True:
            raise ValueError(f"{flag_name} must be present and true")


def _require_public_payload_flags(value: dict[str, Any]) -> None:
    for flag_name in ("paper_only", "report_only", "readonly"):
        if value.get(flag_name) is not True:
            raise ValueError(f"{flag_name} must be present and true")


def _require_sha256_digest(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if len(value) != 64 or any(character not in "0123456789abcdef" for character in value):
        raise ValueError(f"{field_name} must be a sha256 hex digest")
    return value


def _payload_required_string(payload: dict[str, Any], key: str) -> str:
    if key not in payload:
        raise ValueError(f"{key} is required")
    value = payload[key]
    if type(value) is not str:
        raise ValueError(f"{key} must be a string")
    return value


def _revalidate_report(
    report: ResearchPacketMarketContextSourceGapV2Report,
) -> ResearchPacketMarketContextSourceGapV2Report:
    if type(report) is not ResearchPacketMarketContextSourceGapV2Report:
        raise ValueError("report must be a ResearchPacketMarketContextSourceGapV2Report")
    for row in report.rows:
        _validate_row(row)
    _validate_report(report)
    return report


def _row_derived_validation_digest(
    row: ResearchPacketMarketContextSourceGapV2Row,
) -> str:
    return _digest_payload(_row_payload_for_digest(row))


def _report_derived_validation_digest(
    report: ResearchPacketMarketContextSourceGapV2Report,
) -> str:
    return _digest_payload(_report_payload_for_digest(report))


def _public_row_digest(payload: dict[str, Any]) -> str:
    return _digest_payload(_without_top_digest(payload))


def _public_report_digest(payload: dict[str, Any]) -> str:
    return _digest_payload(_without_top_digest(payload))


def _row_payload_for_digest(row: ResearchPacketMarketContextSourceGapV2Row) -> dict[str, Any]:
    payload = _payload_value(row)
    return _without_top_digest(payload)


def _report_payload_for_digest(
    report: ResearchPacketMarketContextSourceGapV2Report,
) -> dict[str, Any]:
    payload = _payload_value(report)
    return _without_top_digest(payload)


def _without_top_digest(payload: dict[str, Any]) -> dict[str, Any]:
    result = dict(payload)
    result.pop("derived_validation_digest", None)
    return result


def _digest_payload(payload: dict[str, Any]) -> str:
    _reject_unsafe_public_payload("payload", payload)
    _reject_public_numeric_values(payload)
    encoded = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _payload_value(value: object) -> Any:
    if is_dataclass(value) and not isinstance(value, type):
        _require_hard_flags(value)
        return {
            item.name: _payload_value(getattr(value, item.name))
            for item in fields(value)
        }
    if type(value) is datetime:
        return value.isoformat()
    if type(value) is Decimal:
        return _decimal_payload(value)
    if type(value) is tuple:
        return [_payload_value(item) for item in value]
    if type(value) is list:
        return [_payload_value(item) for item in value]
    if type(value) is dict:
        return {_payload_key(key): _payload_value(item) for key, item in value.items()}
    if value is None or type(value) in (str, bool):
        return value
    raise ValueError("payload contains unsupported value")


def _payload_key(value: object) -> str:
    if type(value) is not str:
        raise ValueError("payload keys must be strings")
    _reject_public_text("payload key", value)
    return value


def _decimal_payload(value: Decimal | None) -> str | None:
    if value is None:
        return None
    return format(_quantize_decimal(value), "f")


def _reject_unsafe_public_payload(path: str, value: object) -> None:
    if type(value) is dict:
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError(f"{path} public keys must be strings")
            _reject_public_text(f"{path} key", key)
            _reject_unsafe_public_payload(f"{path}.{key}", item)
        return
    if type(value) in (list, tuple):
        for index, item in enumerate(value):
            _reject_unsafe_public_payload(f"{path}.{index}", item)
        return
    if type(value) is str:
        _reject_public_text(path, value)


def _reject_public_text(field_name: str, value: str) -> None:
    lowered = value.casefold()
    if any(fragment in lowered for fragment in UNSAFE_PUBLIC_FRAGMENTS):
        raise ValueError(f"{field_name} contains unsafe public text")


def _reject_public_numeric_values(value: object) -> None:
    if type(value) is dict:
        for item in value.values():
            _reject_public_numeric_values(item)
        return
    if type(value) in (list, tuple):
        for item in value:
            _reject_public_numeric_values(item)
        return
    if isinstance(value, Number) and type(value) is not bool:
        raise ValueError("public payload numerics must be decimal strings")
