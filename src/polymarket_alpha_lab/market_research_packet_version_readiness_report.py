"""Pure market research packet version readiness report."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from typing import Any

from polymarket_alpha_lab.team_paper_guard import (
    json_ready_no_floats,
    reject_unsafe_surface_fields,
    require_paper_only_flags,
)


DEFAULT_MARKET_RESEARCH_PACKET_VERSION_READINESS_REPORT_CONFIG_VERSION = (
    "market-research-packet-version-readiness-report-v0"
)
MARKET_RESEARCH_PACKET_VERSION_READINESS_BANDS = (
    "ready",
    "attention",
    "blocker",
)

READY_REASON = "market_research_packet_version_readiness_ready"
ATTENTION_REASON = "market_research_packet_version_readiness_attention"
BLOCKER_REASON = "market_research_packet_version_readiness_blocker"
NO_MARKETS_REASON = "market_research_packet_version_readiness_no_markets"
REVISION_GAP_ATTENTION_REASON = "packet_revision_gap_attention"
REVISION_GAP_BLOCKER_REASON = "packet_revision_gap_blocker"
STALE_SECTION_ATTENTION_REASON = "stale_section_count_attention"
STALE_SECTION_BLOCKER_REASON = "stale_section_count_blocker"
MISSING_REQUIRED_SECTION_BLOCKER_REASON = "missing_required_section_blocker"
CHANGED_AFTER_FORECAST_ATTENTION_REASON = "changed_after_forecast_attention"
MANUAL_ACK_REQUIRED_BLOCKER_REASON = "manual_ack_required_blocker"

REASON_PRIORITY = (
    BLOCKER_REASON,
    REVISION_GAP_BLOCKER_REASON,
    MISSING_REQUIRED_SECTION_BLOCKER_REASON,
    STALE_SECTION_BLOCKER_REASON,
    MANUAL_ACK_REQUIRED_BLOCKER_REASON,
    ATTENTION_REASON,
    REVISION_GAP_ATTENTION_REASON,
    STALE_SECTION_ATTENTION_REASON,
    CHANGED_AFTER_FORECAST_ATTENTION_REASON,
    READY_REASON,
    NO_MARKETS_REASON,
)
BAND_RANK = {
    "blocker": Decimal("0.000000"),
    "attention": Decimal("1.000000"),
    "ready": Decimal("2.000000"),
}
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
QUANT = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
FOUR = Decimal("4.000000")


class _FinalDataclass:
    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        for base in cls.__bases__:
            if base is not _FinalDataclass and issubclass(base, _FinalDataclass):
                raise TypeError(f"{base.__name__} may not be subclassed")


@dataclass(frozen=True)
class MarketResearchPacketVersionReadinessConfig(_FinalDataclass):
    config_version: str = (
        DEFAULT_MARKET_RESEARCH_PACKET_VERSION_READINESS_REPORT_CONFIG_VERSION
    )
    attention_revision_gap_threshold: Decimal = Decimal("1.000000")
    blocker_revision_gap_threshold: Decimal = Decimal("3.000000")
    attention_stale_section_threshold: Decimal = Decimal("1.000000")
    blocker_stale_section_threshold: Decimal = Decimal("3.000000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, MarketResearchPacketVersionReadinessConfig, "config")
        _require_public_string("config_version", self.config_version)
        for field_name in (
            "attention_revision_gap_threshold",
            "blocker_revision_gap_threshold",
            "attention_stale_section_threshold",
            "blocker_stale_section_threshold",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_count(field_name, getattr(self, field_name)),
            )
        if self.blocker_revision_gap_threshold < self.attention_revision_gap_threshold:
            raise ValueError(
                "blocker_revision_gap_threshold must be greater than or equal to "
                "attention_revision_gap_threshold",
            )
        if self.blocker_stale_section_threshold < self.attention_stale_section_threshold:
            raise ValueError(
                "blocker_stale_section_threshold must be greater than or equal to "
                "attention_stale_section_threshold",
            )
        reject_unsafe_surface_fields("market research packet version readiness config", self)
        require_paper_only_flags("market research packet version readiness config", self)


@dataclass(frozen=True)
class MarketResearchPacketVersionReadinessInput(_FinalDataclass):
    market_key: str
    packet_revision: Decimal
    latest_source_revision: Decimal
    stale_section_count: Decimal
    missing_required_section_count: Decimal
    changed_after_forecast: bool
    manual_ack_required: bool
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, MarketResearchPacketVersionReadinessInput, "packet")
        _require_public_string("market_key", self.market_key)
        for field_name in (
            "packet_revision",
            "latest_source_revision",
            "stale_section_count",
            "missing_required_section_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_count(field_name, getattr(self, field_name)),
            )
        if self.latest_source_revision < self.packet_revision:
            raise ValueError(
                "latest_source_revision must be greater than or equal to packet_revision",
            )
        _require_bool("changed_after_forecast", self.changed_after_forecast)
        _require_bool("manual_ack_required", self.manual_ack_required)
        reject_unsafe_surface_fields("market research packet version readiness packet", self)
        require_paper_only_flags("market research packet version readiness packet", self)


@dataclass(frozen=True)
class MarketResearchPacketVersionReadinessRow(_FinalDataclass):
    market_key: str
    packet_revision: Decimal
    latest_source_revision: Decimal
    packet_current: bool
    revision_gap: Decimal
    stale_section_count: Decimal
    missing_required_section_count: Decimal
    changed_after_forecast: bool
    manual_ack_required: bool
    readiness_band: str
    reason_codes: tuple[str, ...]
    completeness_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, MarketResearchPacketVersionReadinessRow, "row")
        _require_public_string("market_key", self.market_key)
        for field_name in (
            "packet_revision",
            "latest_source_revision",
            "revision_gap",
            "stale_section_count",
            "missing_required_section_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_count(field_name, getattr(self, field_name)),
            )
        if self.latest_source_revision < self.packet_revision:
            raise ValueError(
                "latest_source_revision must be greater than or equal to packet_revision",
            )
        _require_bool("packet_current", self.packet_current)
        _require_bool("changed_after_forecast", self.changed_after_forecast)
        _require_bool("manual_ack_required", self.manual_ack_required)
        _require_band("readiness_band", self.readiness_band)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes),
        )
        object.__setattr__(
            self,
            "completeness_ratio",
            _require_ratio("completeness_ratio", self.completeness_ratio),
        )
        _validate_row(self)
        reject_unsafe_surface_fields("market research packet version readiness row", self)
        require_paper_only_flags("market research packet version readiness row", self)


@dataclass(frozen=True)
class MarketResearchPacketVersionReadinessReport(_FinalDataclass):
    generated_at: datetime
    config_version: str
    report_band: str
    reason_codes: tuple[str, ...]
    market_count: Decimal
    ready_market_count: Decimal
    attention_market_count: Decimal
    blocker_market_count: Decimal
    packet_current_market_count: Decimal
    stale_packet_market_count: Decimal
    missing_required_section_market_count: Decimal
    changed_after_forecast_market_count: Decimal
    manual_ack_required_market_count: Decimal
    packet_current_ratio: Decimal
    ready_ratio: Decimal
    attention_ratio: Decimal
    blocker_ratio: Decimal
    manual_ack_required_ratio: Decimal
    max_revision_gap: Decimal
    max_stale_section_count: Decimal
    rows: tuple[MarketResearchPacketVersionReadinessRow, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, MarketResearchPacketVersionReadinessReport, "report")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_string("config_version", self.config_version)
        _require_band("report_band", self.report_band)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes),
        )
        for field_name in (
            "market_count",
            "ready_market_count",
            "attention_market_count",
            "blocker_market_count",
            "packet_current_market_count",
            "stale_packet_market_count",
            "missing_required_section_market_count",
            "changed_after_forecast_market_count",
            "manual_ack_required_market_count",
            "max_revision_gap",
            "max_stale_section_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_count(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "packet_current_ratio",
            "ready_ratio",
            "attention_ratio",
            "blocker_ratio",
            "manual_ack_required_ratio",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio(field_name, getattr(self, field_name)),
            )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        _validate_report(self)
        reject_unsafe_surface_fields("market research packet version readiness report", self)
        require_paper_only_flags("market research packet version readiness report", self)


def build_market_research_packet_version_readiness_report(
    packets: Iterable[MarketResearchPacketVersionReadinessInput],
    *,
    config: MarketResearchPacketVersionReadinessConfig,
    generated_at: datetime,
) -> MarketResearchPacketVersionReadinessReport:
    if type(config) is not MarketResearchPacketVersionReadinessConfig:
        raise ValueError("config must be a MarketResearchPacketVersionReadinessConfig")
    require_paper_only_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    normalized_packets = _normalize_packets(packets)
    rows = tuple(
        sorted(
            (_row_from_packet(packet, config=config) for packet in normalized_packets),
            key=_row_sort_key,
        ),
    )
    market_count = _count(len(rows))
    ready_market_count = _band_count(rows, "ready")
    attention_market_count = _band_count(rows, "attention")
    blocker_market_count = _band_count(rows, "blocker")
    packet_current_market_count = _bool_count(tuple(row.packet_current for row in rows))
    manual_ack_required_market_count = _bool_count(
        tuple(row.manual_ack_required for row in rows),
    )
    return MarketResearchPacketVersionReadinessReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        report_band=_report_band(rows),
        reason_codes=_report_reason_codes(rows),
        market_count=market_count,
        ready_market_count=ready_market_count,
        attention_market_count=attention_market_count,
        blocker_market_count=blocker_market_count,
        packet_current_market_count=packet_current_market_count,
        stale_packet_market_count=_bool_count(
            tuple(not row.packet_current for row in rows),
        ),
        missing_required_section_market_count=_positive_count(
            tuple(row.missing_required_section_count for row in rows),
        ),
        changed_after_forecast_market_count=_bool_count(
            tuple(row.changed_after_forecast for row in rows),
        ),
        manual_ack_required_market_count=manual_ack_required_market_count,
        packet_current_ratio=_safe_ratio(packet_current_market_count, market_count),
        ready_ratio=_safe_ratio(ready_market_count, market_count),
        attention_ratio=_safe_ratio(attention_market_count, market_count),
        blocker_ratio=_safe_ratio(blocker_market_count, market_count),
        manual_ack_required_ratio=_safe_ratio(
            manual_ack_required_market_count,
            market_count,
        ),
        max_revision_gap=_max_decimal(tuple(row.revision_gap for row in rows)),
        max_stale_section_count=_max_decimal(
            tuple(row.stale_section_count for row in rows),
        ),
        rows=rows,
    )


def market_research_packet_version_readiness_payload(
    report: MarketResearchPacketVersionReadinessReport,
) -> dict[str, Any]:
    if type(report) is not MarketResearchPacketVersionReadinessReport:
        raise ValueError("report must be a MarketResearchPacketVersionReadinessReport")
    require_paper_only_flags("report", report)
    reject_unsafe_surface_fields("market research packet version readiness report", report)
    return json_ready_no_floats(report)


def _row_from_packet(
    packet: MarketResearchPacketVersionReadinessInput,
    *,
    config: MarketResearchPacketVersionReadinessConfig,
) -> MarketResearchPacketVersionReadinessRow:
    revision_gap = _nonnegative_difference(
        packet.latest_source_revision,
        packet.packet_revision,
    )
    reason_codes = _row_reason_codes(
        revision_gap=revision_gap,
        stale_section_count=packet.stale_section_count,
        missing_required_section_count=packet.missing_required_section_count,
        changed_after_forecast=packet.changed_after_forecast,
        manual_ack_required=packet.manual_ack_required,
        config=config,
    )
    band = _row_band(reason_codes)
    return MarketResearchPacketVersionReadinessRow(
        market_key=packet.market_key,
        packet_revision=packet.packet_revision,
        latest_source_revision=packet.latest_source_revision,
        packet_current=revision_gap == ZERO,
        revision_gap=revision_gap,
        stale_section_count=packet.stale_section_count,
        missing_required_section_count=packet.missing_required_section_count,
        changed_after_forecast=packet.changed_after_forecast,
        manual_ack_required=packet.manual_ack_required,
        readiness_band=band,
        reason_codes=reason_codes,
        completeness_ratio=_completeness_ratio(
            packet_current=revision_gap == ZERO,
            has_no_stale_sections=packet.stale_section_count == ZERO,
            has_no_missing_required_sections=(
                packet.missing_required_section_count == ZERO
            ),
            forecast_clean=not packet.changed_after_forecast,
        ),
    )


def _row_reason_codes(
    *,
    revision_gap: Decimal,
    stale_section_count: Decimal,
    missing_required_section_count: Decimal,
    changed_after_forecast: bool,
    manual_ack_required: bool,
    config: MarketResearchPacketVersionReadinessConfig,
) -> tuple[str, ...]:
    blocker_codes: list[str] = []
    attention_codes: list[str] = []
    if revision_gap >= config.blocker_revision_gap_threshold:
        blocker_codes.append(REVISION_GAP_BLOCKER_REASON)
    elif revision_gap >= config.attention_revision_gap_threshold:
        attention_codes.append(REVISION_GAP_ATTENTION_REASON)
    if missing_required_section_count > ZERO:
        blocker_codes.append(MISSING_REQUIRED_SECTION_BLOCKER_REASON)
    if stale_section_count >= config.blocker_stale_section_threshold:
        blocker_codes.append(STALE_SECTION_BLOCKER_REASON)
    elif stale_section_count >= config.attention_stale_section_threshold:
        attention_codes.append(STALE_SECTION_ATTENTION_REASON)
    if manual_ack_required:
        blocker_codes.append(MANUAL_ACK_REQUIRED_BLOCKER_REASON)
    if changed_after_forecast:
        attention_codes.append(CHANGED_AFTER_FORECAST_ATTENTION_REASON)
    reason_codes = tuple(blocker_codes + attention_codes)
    if not reason_codes:
        reason_codes = (READY_REASON,)
    return _normalize_reason_codes(reason_codes)


def _row_band(reason_codes: tuple[str, ...]) -> str:
    if any(reason.endswith("_blocker") for reason in reason_codes):
        return "blocker"
    if any(reason.endswith("_attention") for reason in reason_codes):
        return "attention"
    return "ready"


def _report_band(rows: tuple[MarketResearchPacketVersionReadinessRow, ...]) -> str:
    if not rows:
        return "attention"
    if any(row.readiness_band == "blocker" for row in rows):
        return "blocker"
    if any(row.readiness_band == "attention" for row in rows):
        return "attention"
    return "ready"


def _report_reason_codes(
    rows: tuple[MarketResearchPacketVersionReadinessRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return (NO_MARKETS_REASON,)
    report_band = _report_band(rows)
    codes = [f"market_research_packet_version_readiness_{report_band}"]
    codes.extend(
        reason
        for row in rows
        for reason in row.reason_codes
        if reason != READY_REASON
    )
    return _normalize_reason_codes(tuple(codes))


def _completeness_ratio(
    *,
    packet_current: bool,
    has_no_stale_sections: bool,
    has_no_missing_required_sections: bool,
    forecast_clean: bool,
) -> Decimal:
    passed = sum(
        1
        for value in (
            packet_current,
            has_no_stale_sections,
            has_no_missing_required_sections,
            forecast_clean,
        )
        if value
    )
    return _safe_ratio(_count(passed), FOUR)


def _normalize_packets(
    packets: Iterable[MarketResearchPacketVersionReadinessInput],
) -> tuple[MarketResearchPacketVersionReadinessInput, ...]:
    if isinstance(packets, (str, bytes)):
        raise ValueError("packets must be an iterable")
    try:
        values = tuple(packets)
    except TypeError as exc:
        raise ValueError("packets must be an iterable") from exc
    seen: set[str] = set()
    for packet in values:
        if type(packet) is not MarketResearchPacketVersionReadinessInput:
            raise ValueError(
                "packets must contain MarketResearchPacketVersionReadinessInput values",
            )
        require_paper_only_flags("packet", packet)
        if packet.market_key in seen:
            raise ValueError("market_key values must be unique")
        seen.add(packet.market_key)
    return values


def _normalize_rows(
    rows: tuple[MarketResearchPacketVersionReadinessRow, ...],
) -> tuple[MarketResearchPacketVersionReadinessRow, ...]:
    if type(rows) not in (tuple, list):
        raise ValueError("rows must be a tuple or list")
    normalized = tuple(rows)
    seen: set[str] = set()
    for row in normalized:
        if type(row) is not MarketResearchPacketVersionReadinessRow:
            raise ValueError(
                "rows must contain MarketResearchPacketVersionReadinessRow values",
            )
        require_paper_only_flags("row", row)
        if row.market_key in seen:
            raise ValueError("market_key values must be unique")
        seen.add(row.market_key)
    if normalized != tuple(sorted(normalized, key=_row_sort_key)):
        raise ValueError("rows must be sorted deterministically")
    return normalized


def _validate_row(row: MarketResearchPacketVersionReadinessRow) -> None:
    if row.revision_gap != _nonnegative_difference(
        row.latest_source_revision,
        row.packet_revision,
    ):
        raise ValueError("revision_gap must match revisions")
    if row.packet_current != (row.revision_gap == ZERO):
        raise ValueError("packet_current must match revision_gap")
    if row.readiness_band != _row_band(row.reason_codes):
        raise ValueError("readiness_band must match reason_codes")


def _validate_report(report: MarketResearchPacketVersionReadinessReport) -> None:
    if report.market_count != _count(len(report.rows)):
        raise ValueError("market_count must match rows")
    if report.ready_market_count != _band_count(report.rows, "ready"):
        raise ValueError("ready_market_count must match rows")
    if report.attention_market_count != _band_count(report.rows, "attention"):
        raise ValueError("attention_market_count must match rows")
    if report.blocker_market_count != _band_count(report.rows, "blocker"):
        raise ValueError("blocker_market_count must match rows")
    if (
        report.ready_market_count
        + report.attention_market_count
        + report.blocker_market_count
        != report.market_count
    ):
        raise ValueError("readiness band counts must match market_count")
    if report.packet_current_market_count != _bool_count(
        tuple(row.packet_current for row in report.rows),
    ):
        raise ValueError("packet_current_market_count must match rows")
    if report.stale_packet_market_count != _bool_count(
        tuple(not row.packet_current for row in report.rows),
    ):
        raise ValueError("stale_packet_market_count must match rows")
    if report.missing_required_section_market_count != _positive_count(
        tuple(row.missing_required_section_count for row in report.rows),
    ):
        raise ValueError("missing_required_section_market_count must match rows")
    if report.changed_after_forecast_market_count != _bool_count(
        tuple(row.changed_after_forecast for row in report.rows),
    ):
        raise ValueError("changed_after_forecast_market_count must match rows")
    if report.manual_ack_required_market_count != _bool_count(
        tuple(row.manual_ack_required for row in report.rows),
    ):
        raise ValueError("manual_ack_required_market_count must match rows")
    if report.report_band != _report_band(report.rows):
        raise ValueError("report_band must match rows")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")
    if report.packet_current_ratio != _safe_ratio(
        report.packet_current_market_count,
        report.market_count,
    ):
        raise ValueError("packet_current_ratio must match rows")
    if report.ready_ratio != _safe_ratio(report.ready_market_count, report.market_count):
        raise ValueError("ready_ratio must match rows")
    if report.attention_ratio != _safe_ratio(
        report.attention_market_count,
        report.market_count,
    ):
        raise ValueError("attention_ratio must match rows")
    if report.blocker_ratio != _safe_ratio(
        report.blocker_market_count,
        report.market_count,
    ):
        raise ValueError("blocker_ratio must match rows")
    if report.manual_ack_required_ratio != _safe_ratio(
        report.manual_ack_required_market_count,
        report.market_count,
    ):
        raise ValueError("manual_ack_required_ratio must match rows")


def _row_sort_key(
    row: MarketResearchPacketVersionReadinessRow,
) -> tuple[Decimal, Decimal, Decimal, str]:
    return (
        BAND_RANK[row.readiness_band],
        -row.revision_gap,
        -row.stale_section_count,
        row.market_key,
    )


def _band_count(
    rows: tuple[MarketResearchPacketVersionReadinessRow, ...],
    band: str,
) -> Decimal:
    return _count(sum(1 for row in rows if row.readiness_band == band))


def _bool_count(values: tuple[bool, ...]) -> Decimal:
    return _count(sum(1 for value in values if value))


def _positive_count(values: tuple[Decimal, ...]) -> Decimal:
    return _count(sum(1 for value in values if value > ZERO))


def _max_decimal(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return ZERO
    return max(values).quantize(QUANT)


def _count(value: int) -> Decimal:
    if type(value) is not int:
        raise ValueError("count value must be an int")
    if value < 0:
        raise ValueError("count value must be nonnegative")
    return Decimal(value).quantize(QUANT)


def _safe_ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return (numerator / denominator).quantize(QUANT)


def _nonnegative_difference(first: Decimal, second: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        value = first - second
    if value < ZERO:
        return ZERO
    return value.quantize(QUANT)


def _require_nonnegative_count(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{field_name} must be an integer")
    return normalized.quantize(QUANT)


def _require_ratio(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    if normalized > ONE:
        raise ValueError(f"{field_name} must not exceed 1")
    return normalized.quantize(QUANT)


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return value.quantize(QUANT)


def _require_bool(field_name: str, value: object) -> None:
    if type(value) is not bool:
        raise ValueError(f"{field_name} must be a bool")


def _require_band(field_name: str, value: object) -> None:
    if type(value) is not str or value not in MARKET_RESEARCH_PACKET_VERSION_READINESS_BANDS:
        allowed = ", ".join(MARKET_RESEARCH_PACKET_VERSION_READINESS_BANDS)
        raise ValueError(f"{field_name} must be one of: {allowed}")


def _normalize_reason_codes(values: tuple[str, ...]) -> tuple[str, ...]:
    if type(values) is not tuple:
        raise ValueError("reason_codes must be a tuple")
    normalized: list[str] = []
    for value in values:
        if type(value) is not str or not value:
            raise ValueError("reason_codes must contain non-empty strings")
        if value not in REASON_PRIORITY:
            raise ValueError(f"unknown reason_code: {value}")
        if value not in normalized:
            normalized.append(value)
    return tuple(sorted(normalized, key=REASON_PRIORITY.index))


def _require_public_string(field_name: str, value: object) -> None:
    if type(value) is not str or not value.strip():
        raise ValueError(f"{field_name} must be a non-empty string")


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


def _require_exact_type(value: object, expected_type: type[object], label: str) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{label} must be exactly {expected_type.__name__}")


__all__ = (
    "DEFAULT_MARKET_RESEARCH_PACKET_VERSION_READINESS_REPORT_CONFIG_VERSION",
    "MARKET_RESEARCH_PACKET_VERSION_READINESS_BANDS",
    "MarketResearchPacketVersionReadinessConfig",
    "MarketResearchPacketVersionReadinessInput",
    "MarketResearchPacketVersionReadinessReport",
    "MarketResearchPacketVersionReadinessRow",
    "build_market_research_packet_version_readiness_report",
    "market_research_packet_version_readiness_payload",
)
