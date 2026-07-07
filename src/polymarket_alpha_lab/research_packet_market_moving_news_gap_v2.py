"""Phase 1 market-moving news coverage gap detector."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from numbers import Number
from typing import Any


DEFAULT_RESEARCH_PACKET_MARKET_MOVING_NEWS_GAP_V2_CONFIG_VERSION = (
    "research-packet-market-moving-news-gap-v2"
)

PASS_REASON = "research_packet_market_moving_news_gap_v2_passed"
LATEST_UPDATE_MISSING_REASON = (
    "research_packet_market_moving_news_gap_v2_latest_update_missing"
)
LATEST_UPDATE_STALE_REASON = (
    "research_packet_market_moving_news_gap_v2_latest_update_stale"
)
OFFICIAL_SOURCE_MISSING_REASON = (
    "research_packet_market_moving_news_gap_v2_official_source_missing"
)
WEAK_INDEPENDENT_SOURCES_REASON = (
    "research_packet_market_moving_news_gap_v2_weak_independent_sources"
)
CONTRADICTION_ELEVATED_REASON = (
    "research_packet_market_moving_news_gap_v2_contradiction_elevated"
)
CONTRADICTION_SEVERE_REASON = (
    "research_packet_market_moving_news_gap_v2_contradiction_severe"
)
PROBABILITY_MOVE_LARGE_REASON = (
    "research_packet_market_moving_news_gap_v2_probability_move_large"
)
MARKET_CLOSE_NEAR_REASON = (
    "research_packet_market_moving_news_gap_v2_market_close_near"
)

ROW_REASON_CODES = (
    LATEST_UPDATE_MISSING_REASON,
    LATEST_UPDATE_STALE_REASON,
    OFFICIAL_SOURCE_MISSING_REASON,
    WEAK_INDEPENDENT_SOURCES_REASON,
    CONTRADICTION_ELEVATED_REASON,
    CONTRADICTION_SEVERE_REASON,
    PROBABILITY_MOVE_LARGE_REASON,
    MARKET_CLOSE_NEAR_REASON,
)
REPORT_REASON_CODES = (PASS_REASON,) + ROW_REASON_CODES
BLOCKED_REASONS = frozenset(
    (
        LATEST_UPDATE_MISSING_REASON,
        LATEST_UPDATE_STALE_REASON,
        OFFICIAL_SOURCE_MISSING_REASON,
        CONTRADICTION_SEVERE_REASON,
        PROBABILITY_MOVE_LARGE_REASON,
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
class ResearchPacketMarketMovingNewsGapV2Config:
    config_version: str = DEFAULT_RESEARCH_PACKET_MARKET_MOVING_NEWS_GAP_V2_CONFIG_VERSION
    max_latest_update_age_seconds: Decimal = Decimal("1800.000000")
    min_independent_source_count: Decimal = Decimal("2.000000")
    severe_contradiction_threshold: Decimal = Decimal("0.750000")
    probability_move_threshold: Decimal = Decimal("0.050000")
    urgent_market_close_horizon_seconds: Decimal = Decimal("21600.000000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchPacketMarketMovingNewsGapV2Config does not support subclassing",
        )

    def __post_init__(self) -> None:
        _require_public_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_PACKET_MARKET_MOVING_NEWS_GAP_V2_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "max_latest_update_age_seconds",
            "min_independent_source_count",
            "urgent_market_close_horizon_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_positive_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "severe_contradiction_threshold",
            "probability_move_threshold",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        _require_hard_flags(self)


@dataclass(frozen=True)
class ResearchPacketMarketMovingNewsGapV2Packet:
    market_id: str
    packet_id: str
    event_category: str
    captured_at: datetime
    latest_update_at: datetime | None
    official_source_count: Decimal
    independent_source_count: Decimal
    contradiction_severity: Decimal
    probability_move_abs: Decimal
    market_close_at: datetime
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchPacketMarketMovingNewsGapV2Packet does not support subclassing",
        )

    def __post_init__(self) -> None:
        for field_name in ("market_id", "packet_id", "event_category"):
            _require_public_string(field_name, getattr(self, field_name))
        object.__setattr__(self, "captured_at", _as_utc("captured_at", self.captured_at))
        object.__setattr__(
            self,
            "latest_update_at",
            _as_optional_utc("latest_update_at", self.latest_update_at),
        )
        object.__setattr__(
            self,
            "market_close_at",
            _as_utc("market_close_at", self.market_close_at),
        )
        for field_name in ("official_source_count", "independent_source_count"):
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
        _require_hard_flags(self)


@dataclass(frozen=True)
class ResearchPacketMarketMovingNewsGapV2ReasonCodeCount:
    reason_code: str
    packet_count: Decimal
    packet_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchPacketMarketMovingNewsGapV2ReasonCodeCount "
            "does not support subclassing",
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
class ResearchPacketMarketMovingNewsGapV2Row:
    market_id: str
    packet_id: str
    event_category: str
    captured_at: datetime
    latest_update_at: datetime | None
    latest_update_age_seconds: Decimal | None
    official_source_count: Decimal
    independent_source_count: Decimal
    contradiction_severity: Decimal
    probability_move_abs: Decimal
    market_close_at: datetime
    market_close_horizon_seconds: Decimal
    gap_status: str
    reason_codes: tuple[str, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchPacketMarketMovingNewsGapV2Row does not support subclassing",
        )

    def __post_init__(self) -> None:
        for field_name in ("market_id", "packet_id", "event_category"):
            _require_public_string(field_name, getattr(self, field_name))
        object.__setattr__(self, "captured_at", _as_utc("captured_at", self.captured_at))
        object.__setattr__(
            self,
            "latest_update_at",
            _as_optional_utc("latest_update_at", self.latest_update_at),
        )
        object.__setattr__(
            self,
            "latest_update_age_seconds",
            _normalize_optional_nonnegative_decimal(
                "latest_update_age_seconds",
                self.latest_update_age_seconds,
            ),
        )
        for field_name in ("official_source_count", "independent_source_count"):
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
            "market_close_at",
            _as_utc("market_close_at", self.market_close_at),
        )
        object.__setattr__(
            self,
            "market_close_horizon_seconds",
            _normalize_nonnegative_decimal(
                "market_close_horizon_seconds",
                self.market_close_horizon_seconds,
            ),
        )
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
class ResearchPacketMarketMovingNewsGapV2Report:
    generated_at: datetime
    config_version: str
    report_status: str
    packet_count: Decimal
    pass_packet_count: Decimal
    watch_packet_count: Decimal
    blocked_packet_count: Decimal
    attention_packet_count: Decimal
    attention_packet_ratio: Decimal
    missing_latest_update_packet_count: Decimal
    stale_latest_update_packet_count: Decimal
    missing_official_source_packet_count: Decimal
    weak_independent_source_packet_count: Decimal
    contradiction_packet_count: Decimal
    severe_contradiction_packet_count: Decimal
    probability_movement_packet_count: Decimal
    market_close_urgent_packet_count: Decimal
    max_latest_update_age_seconds: Decimal
    max_contradiction_severity: Decimal
    max_probability_move_abs: Decimal
    min_market_close_horizon_seconds: Decimal
    latest_update_age_threshold_seconds: Decimal
    min_independent_source_count: Decimal
    severe_contradiction_threshold: Decimal
    probability_move_threshold: Decimal
    urgent_market_close_horizon_seconds: Decimal
    reason_codes: tuple[str, ...]
    reason_code_counts: tuple[ResearchPacketMarketMovingNewsGapV2ReasonCodeCount, ...]
    rows: tuple[ResearchPacketMarketMovingNewsGapV2Row, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchPacketMarketMovingNewsGapV2Report does not support subclassing",
        )

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_PACKET_MARKET_MOVING_NEWS_GAP_V2_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        _require_member("report_status", self.report_status, REPORT_STATUSES)
        for field_name in (
            "packet_count",
            "pass_packet_count",
            "watch_packet_count",
            "blocked_packet_count",
            "attention_packet_count",
            "missing_latest_update_packet_count",
            "stale_latest_update_packet_count",
            "missing_official_source_packet_count",
            "weak_independent_source_packet_count",
            "contradiction_packet_count",
            "severe_contradiction_packet_count",
            "probability_movement_packet_count",
            "market_close_urgent_packet_count",
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
            "probability_move_threshold",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "max_latest_update_age_seconds",
            "min_market_close_horizon_seconds",
            "latest_update_age_threshold_seconds",
            "min_independent_source_count",
            "urgent_market_close_horizon_seconds",
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


def build_research_packet_market_moving_news_gap_v2_report(
    packets: list[ResearchPacketMarketMovingNewsGapV2Packet]
    | tuple[ResearchPacketMarketMovingNewsGapV2Packet, ...],
    *,
    config: ResearchPacketMarketMovingNewsGapV2Config,
    generated_at: datetime,
) -> ResearchPacketMarketMovingNewsGapV2Report:
    if type(config) is not ResearchPacketMarketMovingNewsGapV2Config:
        raise ValueError("config must be a ResearchPacketMarketMovingNewsGapV2Config")
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
    return ResearchPacketMarketMovingNewsGapV2Report(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        report_status=_report_status(rows),
        packet_count=packet_count,
        pass_packet_count=_status_count(rows, "pass"),
        watch_packet_count=_status_count(rows, "watch"),
        blocked_packet_count=_status_count(rows, "blocked"),
        attention_packet_count=attention_count,
        attention_packet_ratio=_safe_ratio(attention_count, packet_count),
        missing_latest_update_packet_count=_reason_count(
            rows,
            LATEST_UPDATE_MISSING_REASON,
        ),
        stale_latest_update_packet_count=_reason_count(
            rows,
            LATEST_UPDATE_STALE_REASON,
        ),
        missing_official_source_packet_count=_reason_count(
            rows,
            OFFICIAL_SOURCE_MISSING_REASON,
        ),
        weak_independent_source_packet_count=_reason_count(
            rows,
            WEAK_INDEPENDENT_SOURCES_REASON,
        ),
        contradiction_packet_count=_count_decimal(
            sum(1 for row in rows if row.contradiction_severity > ZERO),
        ),
        severe_contradiction_packet_count=_reason_count(
            rows,
            CONTRADICTION_SEVERE_REASON,
        ),
        probability_movement_packet_count=_reason_count(
            rows,
            PROBABILITY_MOVE_LARGE_REASON,
        ),
        market_close_urgent_packet_count=_reason_count(
            rows,
            MARKET_CLOSE_NEAR_REASON,
        ),
        max_latest_update_age_seconds=max(
            (
                row.latest_update_age_seconds
                for row in rows
                if row.latest_update_age_seconds is not None
            ),
            default=ZERO,
        ),
        max_contradiction_severity=max(
            (row.contradiction_severity for row in rows),
            default=ZERO,
        ),
        max_probability_move_abs=max((row.probability_move_abs for row in rows), default=ZERO),
        min_market_close_horizon_seconds=min(
            (row.market_close_horizon_seconds for row in rows),
            default=ZERO,
        ),
        latest_update_age_threshold_seconds=config.max_latest_update_age_seconds,
        min_independent_source_count=config.min_independent_source_count,
        severe_contradiction_threshold=config.severe_contradiction_threshold,
        probability_move_threshold=config.probability_move_threshold,
        urgent_market_close_horizon_seconds=config.urgent_market_close_horizon_seconds,
        reason_codes=_report_reason_codes(rows),
        reason_code_counts=_reason_code_counts(rows),
        rows=rows,
    )


def research_packet_market_moving_news_gap_v2_payload(value: object) -> dict[str, Any]:
    if type(value) is ResearchPacketMarketMovingNewsGapV2Report:
        revalidated = _revalidate_report(value)
        payload = _payload_value(revalidated)
        validate_research_packet_market_moving_news_gap_v2_public_payload(payload)
        return payload
    if type(value) is dict:
        validate_research_packet_market_moving_news_gap_v2_public_payload(value)
        return dict(value)
    raise ValueError("value must be a ResearchPacketMarketMovingNewsGapV2Report or dict")


def validate_research_packet_market_moving_news_gap_v2_public_payload(
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
    packet: ResearchPacketMarketMovingNewsGapV2Packet,
    *,
    config: ResearchPacketMarketMovingNewsGapV2Config,
    generated_at: datetime,
) -> ResearchPacketMarketMovingNewsGapV2Row:
    latest_update_age_seconds = (
        None
        if packet.latest_update_at is None
        else _duration_seconds(generated_at, packet.latest_update_at)
    )
    market_close_horizon_seconds = _duration_seconds(packet.market_close_at, generated_at)
    reason_codes = _row_reason_codes(
        packet=packet,
        config=config,
        latest_update_age_seconds=latest_update_age_seconds,
        market_close_horizon_seconds=market_close_horizon_seconds,
    )
    return ResearchPacketMarketMovingNewsGapV2Row(
        market_id=packet.market_id,
        packet_id=packet.packet_id,
        event_category=packet.event_category,
        captured_at=packet.captured_at,
        latest_update_at=packet.latest_update_at,
        latest_update_age_seconds=latest_update_age_seconds,
        official_source_count=packet.official_source_count,
        independent_source_count=packet.independent_source_count,
        contradiction_severity=packet.contradiction_severity,
        probability_move_abs=packet.probability_move_abs,
        market_close_at=packet.market_close_at,
        market_close_horizon_seconds=market_close_horizon_seconds,
        gap_status=_row_status(reason_codes),
        reason_codes=reason_codes,
    )


def _row_reason_codes(
    *,
    packet: ResearchPacketMarketMovingNewsGapV2Packet,
    config: ResearchPacketMarketMovingNewsGapV2Config,
    latest_update_age_seconds: Decimal | None,
    market_close_horizon_seconds: Decimal,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    if latest_update_age_seconds is None:
        reason_codes.append(LATEST_UPDATE_MISSING_REASON)
    elif latest_update_age_seconds > config.max_latest_update_age_seconds:
        reason_codes.append(LATEST_UPDATE_STALE_REASON)
    if packet.official_source_count == ZERO:
        reason_codes.append(OFFICIAL_SOURCE_MISSING_REASON)
    if packet.independent_source_count < config.min_independent_source_count:
        reason_codes.append(WEAK_INDEPENDENT_SOURCES_REASON)
    if packet.contradiction_severity >= config.severe_contradiction_threshold:
        reason_codes.append(CONTRADICTION_SEVERE_REASON)
    elif packet.contradiction_severity > ZERO:
        reason_codes.append(CONTRADICTION_ELEVATED_REASON)
    if packet.probability_move_abs >= config.probability_move_threshold:
        reason_codes.append(PROBABILITY_MOVE_LARGE_REASON)
    if market_close_horizon_seconds <= config.urgent_market_close_horizon_seconds:
        reason_codes.append(MARKET_CLOSE_NEAR_REASON)
    if not reason_codes:
        reason_codes.append(PASS_REASON)
    return tuple(reason_codes)


def _row_status(reason_codes: tuple[str, ...]) -> str:
    if any(reason_code in BLOCKED_REASONS for reason_code in reason_codes):
        return "blocked"
    if reason_codes == (PASS_REASON,):
        return "pass"
    return "watch"


def _report_status(rows: tuple[ResearchPacketMarketMovingNewsGapV2Row, ...]) -> str:
    if any(row.gap_status == "blocked" for row in rows):
        return "blocked"
    if any(row.gap_status == "watch" for row in rows):
        return "watch"
    return "pass"


def _report_reason_codes(
    rows: tuple[ResearchPacketMarketMovingNewsGapV2Row, ...],
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
    rows: tuple[ResearchPacketMarketMovingNewsGapV2Row, ...],
) -> tuple[ResearchPacketMarketMovingNewsGapV2ReasonCodeCount, ...]:
    row_count = _count_decimal(len(rows))
    return tuple(
        ResearchPacketMarketMovingNewsGapV2ReasonCodeCount(
            reason_code=reason_code,
            packet_count=_reason_count(rows, reason_code),
            packet_ratio=_safe_ratio(_reason_count(rows, reason_code), row_count),
        )
        for reason_code in ROW_REASON_CODES
        if _reason_count(rows, reason_code) > ZERO
    )


def _normalize_packets(
    value: object,
) -> tuple[ResearchPacketMarketMovingNewsGapV2Packet, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("packets must be a list or tuple")
    packets = tuple(value)
    seen: set[tuple[str, str]] = set()
    for packet in packets:
        if type(packet) is not ResearchPacketMarketMovingNewsGapV2Packet:
            raise ValueError(
                "packets must contain ResearchPacketMarketMovingNewsGapV2Packet values",
            )
        _require_hard_flags(packet)
        key = (packet.market_id, packet.packet_id)
        if key in seen:
            raise ValueError("packets must be unique by market_id and packet_id")
        seen.add(key)
    return packets


def _normalize_rows(
    value: object,
) -> tuple[ResearchPacketMarketMovingNewsGapV2Row, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("rows must be a list or tuple")
    rows = tuple(value)
    seen: set[tuple[str, str]] = set()
    for row in rows:
        if type(row) is not ResearchPacketMarketMovingNewsGapV2Row:
            raise ValueError("rows must contain ResearchPacketMarketMovingNewsGapV2Row values")
        _require_hard_flags(row)
        key = (row.market_id, row.packet_id)
        if key in seen:
            raise ValueError("rows must be unique by market_id and packet_id")
        seen.add(key)
    if rows != tuple(sorted(rows, key=_row_sort_key)):
        raise ValueError("rows must use deterministic sequence")
    return rows


def _normalize_reason_code_counts(
    value: object,
) -> tuple[ResearchPacketMarketMovingNewsGapV2ReasonCodeCount, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("reason_code_counts must be a list or tuple")
    counts = tuple(value)
    seen: set[str] = set()
    for item in counts:
        if type(item) is not ResearchPacketMarketMovingNewsGapV2ReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "ResearchPacketMarketMovingNewsGapV2ReasonCodeCount values",
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


def _validate_packet_times(
    packets: tuple[ResearchPacketMarketMovingNewsGapV2Packet, ...],
    *,
    generated_at: datetime,
) -> None:
    for packet in packets:
        for field_name in ("captured_at", "latest_update_at"):
            value = getattr(packet, field_name)
            if value is not None and value > generated_at:
                raise ValueError(f"{field_name} must not be after generated_at")
        if packet.market_close_at < generated_at:
            raise ValueError("market_close_at must not be before generated_at")


def _validate_row(row: ResearchPacketMarketMovingNewsGapV2Row) -> None:
    if row.latest_update_at is None and row.latest_update_age_seconds is not None:
        raise ValueError("latest_update_age_seconds must be absent without latest_update_at")
    if row.latest_update_at is not None and row.latest_update_age_seconds is None:
        raise ValueError("latest_update_age_seconds is required with latest_update_at")
    if row.gap_status != _row_status(row.reason_codes):
        raise ValueError("gap_status must match reason_codes")
    if row.derived_validation_digest != _row_derived_validation_digest(row):
        raise ValueError("derived_validation_digest must match row fields")


def _validate_report(report: ResearchPacketMarketMovingNewsGapV2Report) -> None:
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
        ("missing_latest_update_packet_count", LATEST_UPDATE_MISSING_REASON),
        ("stale_latest_update_packet_count", LATEST_UPDATE_STALE_REASON),
        ("missing_official_source_packet_count", OFFICIAL_SOURCE_MISSING_REASON),
        ("weak_independent_source_packet_count", WEAK_INDEPENDENT_SOURCES_REASON),
        ("severe_contradiction_packet_count", CONTRADICTION_SEVERE_REASON),
        ("probability_movement_packet_count", PROBABILITY_MOVE_LARGE_REASON),
        ("market_close_urgent_packet_count", MARKET_CLOSE_NEAR_REASON),
    ):
        if getattr(report, field_name) != _reason_count(rows, reason_code):
            raise ValueError(f"{field_name} must match rows")
    if report.contradiction_packet_count != _count_decimal(
        sum(1 for row in rows if row.contradiction_severity > ZERO),
    ):
        raise ValueError("contradiction_packet_count must match rows")
    if report.max_latest_update_age_seconds != max(
        (
            row.latest_update_age_seconds
            for row in rows
            if row.latest_update_age_seconds is not None
        ),
        default=ZERO,
    ):
        raise ValueError("max_latest_update_age_seconds must match rows")
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
    if report.min_market_close_horizon_seconds != min(
        (row.market_close_horizon_seconds for row in rows),
        default=ZERO,
    ):
        raise ValueError("min_market_close_horizon_seconds must match rows")
    if report.report_status != _report_status(rows):
        raise ValueError("report_status must match rows")
    if report.reason_codes != _report_reason_codes(rows):
        raise ValueError("reason_codes must match rows")
    if report.reason_code_counts != _reason_code_counts(rows):
        raise ValueError("reason_code_counts must match rows")
    if report.derived_validation_digest != _report_derived_validation_digest(report):
        raise ValueError("derived_validation_digest must match report fields")


def _row_sort_key(
    row: ResearchPacketMarketMovingNewsGapV2Row,
) -> tuple[Decimal, Decimal, Decimal, Decimal, str, str]:
    reason_count = _count_decimal(len(tuple(code for code in row.reason_codes if code != PASS_REASON)))
    return (
        STATUS_RANK[row.gap_status],
        -reason_count,
        -max(row.contradiction_severity, row.probability_move_abs),
        row.market_close_horizon_seconds,
        row.market_id,
        row.packet_id,
    )


def _status_count(
    rows: tuple[ResearchPacketMarketMovingNewsGapV2Row, ...],
    status: str,
) -> Decimal:
    return _count_decimal(sum(1 for row in rows if row.gap_status == status))


def _reason_count(
    rows: tuple[ResearchPacketMarketMovingNewsGapV2Row, ...],
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
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
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
    report: ResearchPacketMarketMovingNewsGapV2Report,
) -> ResearchPacketMarketMovingNewsGapV2Report:
    if type(report) is not ResearchPacketMarketMovingNewsGapV2Report:
        raise ValueError("report must be a ResearchPacketMarketMovingNewsGapV2Report")
    for row in report.rows:
        _validate_row(row)
    _validate_report(report)
    return report


def _row_derived_validation_digest(row: ResearchPacketMarketMovingNewsGapV2Row) -> str:
    return _digest_payload(_row_payload_for_digest(row))


def _report_derived_validation_digest(report: ResearchPacketMarketMovingNewsGapV2Report) -> str:
    return _digest_payload(_report_payload_for_digest(report))


def _public_row_digest(payload: dict[str, Any]) -> str:
    return _digest_payload(_without_top_digest(payload))


def _public_report_digest(payload: dict[str, Any]) -> str:
    return _digest_payload(_without_top_digest(payload))


def _row_payload_for_digest(row: ResearchPacketMarketMovingNewsGapV2Row) -> dict[str, Any]:
    payload = _payload_value(row)
    return _without_top_digest(payload)


def _report_payload_for_digest(report: ResearchPacketMarketMovingNewsGapV2Report) -> dict[str, Any]:
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
        return {item.name: _payload_value(getattr(value, item.name)) for item in fields(value)}
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


__all__ = (
    "DEFAULT_RESEARCH_PACKET_MARKET_MOVING_NEWS_GAP_V2_CONFIG_VERSION",
    "ResearchPacketMarketMovingNewsGapV2Config",
    "ResearchPacketMarketMovingNewsGapV2Packet",
    "ResearchPacketMarketMovingNewsGapV2ReasonCodeCount",
    "ResearchPacketMarketMovingNewsGapV2Report",
    "ResearchPacketMarketMovingNewsGapV2Row",
    "build_research_packet_market_moving_news_gap_v2_report",
    "research_packet_market_moving_news_gap_v2_payload",
    "validate_research_packet_market_moving_news_gap_v2_public_payload",
)
