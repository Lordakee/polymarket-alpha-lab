"""Pure readback reducer for persisted paper research packet history."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal

from polymarket_alpha_lab.paper_research_packet import (
    PaperResearchPacketReport,
    PaperResearchPacketRow,
)


__all__ = (
    "DEFAULT_PAPER_RESEARCH_PACKET_DB_HISTORY_CONFIG_VERSION",
    "PaperResearchPacketDbHistoryConfig",
    "PaperResearchPacketDbHistoryReport",
    "build_paper_research_packet_db_history_report",
)


DEFAULT_PAPER_RESEARCH_PACKET_DB_HISTORY_CONFIG_VERSION = (
    "paper-research-packet-db-history-v0"
)
DECIMAL_QUANTUM = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
RESEARCH_PRIORITIES = ("high", "medium", "low", "skip")
SIDES = ("yes", "no", "none")


@dataclass(frozen=True)
class PaperResearchPacketDbHistoryConfig:
    config_version: str = DEFAULT_PAPER_RESEARCH_PACKET_DB_HISTORY_CONFIG_VERSION
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("config_version", self.config_version)
        _require_hard_flags(self)


@dataclass(frozen=True)
class PaperResearchPacketDbHistoryReport:
    generated_at: datetime
    config_version: str
    report_count: int
    first_report_generated_at: datetime | None
    latest_report_generated_at: datetime | None
    duplicate_generated_at_count: int
    latest_packet_config_version: str | None
    latest_input_row_count: int | None
    latest_packet_row_count: int | None
    latest_included_count: int | None
    latest_skipped_count: int | None
    latest_high_priority_count: int | None
    latest_medium_priority_count: int | None
    latest_low_priority_count: int | None
    latest_top_packet_rank: int | None
    latest_top_packet_market_slug: str | None
    latest_top_packet_side: str | None
    latest_top_packet_research_priority: str | None
    latest_top_packet_recommendation_score: Decimal | None
    latest_top_packet_net_edge: Decimal | None
    latest_top_packet_allocated_notional: Decimal | None
    latest_top_packet_requested_notional: Decimal | None
    latest_top_packet_reason_codes: tuple[str, ...] | None
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        _require_nonnegative_int("report_count", self.report_count)
        object.__setattr__(
            self,
            "first_report_generated_at",
            _as_optional_utc(
                "first_report_generated_at",
                self.first_report_generated_at,
            ),
        )
        object.__setattr__(
            self,
            "latest_report_generated_at",
            _as_optional_utc(
                "latest_report_generated_at",
                self.latest_report_generated_at,
            ),
        )
        _require_nonnegative_int(
            "duplicate_generated_at_count",
            self.duplicate_generated_at_count,
        )
        if self.latest_packet_config_version is not None:
            _require_canonical_string(
                "latest_packet_config_version",
                self.latest_packet_config_version,
            )
        for field_name in (
            "latest_input_row_count",
            "latest_packet_row_count",
            "latest_included_count",
            "latest_skipped_count",
            "latest_high_priority_count",
            "latest_medium_priority_count",
            "latest_low_priority_count",
        ):
            _require_optional_nonnegative_int(field_name, getattr(self, field_name))
        _require_optional_positive_int(
            "latest_top_packet_rank",
            self.latest_top_packet_rank,
        )
        if self.latest_top_packet_market_slug is not None:
            _require_canonical_string(
                "latest_top_packet_market_slug",
                self.latest_top_packet_market_slug,
            )
        _require_optional_side("latest_top_packet_side", self.latest_top_packet_side)
        _require_optional_research_priority(
            "latest_top_packet_research_priority",
            self.latest_top_packet_research_priority,
        )
        object.__setattr__(
            self,
            "latest_top_packet_recommendation_score",
            _quantize_optional_score(
                "latest_top_packet_recommendation_score",
                self.latest_top_packet_recommendation_score,
            ),
        )
        object.__setattr__(
            self,
            "latest_top_packet_net_edge",
            _quantize_optional_decimal(
                "latest_top_packet_net_edge",
                self.latest_top_packet_net_edge,
            ),
        )
        object.__setattr__(
            self,
            "latest_top_packet_allocated_notional",
            _quantize_optional_nonnegative_decimal(
                "latest_top_packet_allocated_notional",
                self.latest_top_packet_allocated_notional,
            ),
        )
        object.__setattr__(
            self,
            "latest_top_packet_requested_notional",
            _quantize_optional_nonnegative_decimal(
                "latest_top_packet_requested_notional",
                self.latest_top_packet_requested_notional,
            ),
        )
        object.__setattr__(
            self,
            "latest_top_packet_reason_codes",
            _normalize_optional_reason_codes(
                "latest_top_packet_reason_codes",
                self.latest_top_packet_reason_codes,
            ),
        )
        _validate_history_report(self)
        _require_hard_flags(self)


def build_paper_research_packet_db_history_report(
    reports: object,
    *,
    config: PaperResearchPacketDbHistoryConfig,
    generated_at: datetime,
) -> PaperResearchPacketDbHistoryReport:
    """Reduce exact packet reports into deterministic chronological readback metrics."""

    if type(config) is not PaperResearchPacketDbHistoryConfig:
        raise ValueError("config must be a PaperResearchPacketDbHistoryConfig")
    _require_hard_flags(config)
    if type(generated_at) is not datetime:
        raise ValueError("generated_at must be a datetime")

    source_reports = _normalize_reports(reports)
    chronological_reports = _chronological_reports(source_reports)
    latest_report = chronological_reports[-1] if chronological_reports else None
    latest_top_packet = (
        latest_report.packet_rows[0]
        if latest_report is not None and latest_report.packet_rows
        else None
    )

    return PaperResearchPacketDbHistoryReport(
        generated_at=generated_at,
        config_version=config.config_version,
        report_count=len(chronological_reports),
        first_report_generated_at=(
            chronological_reports[0].generated_at if chronological_reports else None
        ),
        latest_report_generated_at=(
            latest_report.generated_at if latest_report is not None else None
        ),
        duplicate_generated_at_count=_duplicate_generated_at_count(
            chronological_reports,
        ),
        latest_packet_config_version=(
            latest_report.config_version if latest_report is not None else None
        ),
        latest_input_row_count=(
            latest_report.input_row_count if latest_report is not None else None
        ),
        latest_packet_row_count=(
            latest_report.packet_row_count if latest_report is not None else None
        ),
        latest_included_count=(
            latest_report.included_count if latest_report is not None else None
        ),
        latest_skipped_count=(
            latest_report.skipped_count if latest_report is not None else None
        ),
        latest_high_priority_count=(
            latest_report.high_priority_count if latest_report is not None else None
        ),
        latest_medium_priority_count=(
            latest_report.medium_priority_count if latest_report is not None else None
        ),
        latest_low_priority_count=(
            latest_report.low_priority_count if latest_report is not None else None
        ),
        latest_top_packet_rank=(
            latest_top_packet.packet_rank if latest_top_packet is not None else None
        ),
        latest_top_packet_market_slug=(
            latest_top_packet.market_slug if latest_top_packet is not None else None
        ),
        latest_top_packet_side=(
            latest_top_packet.side if latest_top_packet is not None else None
        ),
        latest_top_packet_research_priority=(
            latest_top_packet.research_priority if latest_top_packet is not None else None
        ),
        latest_top_packet_recommendation_score=(
            latest_top_packet.recommendation_score
            if latest_top_packet is not None
            else None
        ),
        latest_top_packet_net_edge=(
            latest_top_packet.net_edge if latest_top_packet is not None else None
        ),
        latest_top_packet_allocated_notional=(
            latest_top_packet.allocated_notional
            if latest_top_packet is not None
            else None
        ),
        latest_top_packet_requested_notional=(
            latest_top_packet.requested_notional
            if latest_top_packet is not None
            else None
        ),
        latest_top_packet_reason_codes=(
            latest_top_packet.reason_codes if latest_top_packet is not None else None
        ),
    )


def _normalize_reports(value: object) -> tuple[PaperResearchPacketReport, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("reports must be a list or tuple")
    reports = tuple(value)
    for report in reports:
        if type(report) is not PaperResearchPacketReport:
            raise ValueError("reports must contain PaperResearchPacketReport values")
        _validate_packet_report_value(report)
    return reports


def _validate_packet_report_value(report: PaperResearchPacketReport) -> None:
    _require_hard_flags(report)
    _as_utc("report generated_at", report.generated_at)
    _require_canonical_string("report config_version", report.config_version)
    for field_name in (
        "input_row_count",
        "packet_row_count",
        "included_count",
        "skipped_count",
        "high_priority_count",
        "medium_priority_count",
        "low_priority_count",
    ):
        _require_nonnegative_int(field_name, getattr(report, field_name))
    if type(report.packet_rows) is not tuple:
        raise ValueError("packet_rows must be a tuple")
    for row in report.packet_rows:
        if type(row) is not PaperResearchPacketRow:
            raise ValueError("packet_rows must contain PaperResearchPacketRow values")
        _require_hard_flags(row)
    _validate_packet_report_counts(report)


def _validate_packet_report_counts(report: PaperResearchPacketReport) -> None:
    if report.packet_row_count != len(report.packet_rows):
        raise ValueError("packet_row_count must match packet_rows")
    if report.input_row_count < report.packet_row_count:
        raise ValueError("input_row_count must cover packet_rows")
    if (
        report.included_count + report.skipped_count
        != report.packet_row_count
    ):
        raise ValueError("packet priority counts must match packet_row_count")
    if (
        report.high_priority_count
        + report.medium_priority_count
        + report.low_priority_count
        != report.included_count
    ):
        raise ValueError("priority counts must match included_count")


def _chronological_reports(
    reports: tuple[PaperResearchPacketReport, ...],
) -> tuple[PaperResearchPacketReport, ...]:
    return tuple(
        report
        for _, report in sorted(
            enumerate(reports),
            key=lambda item: (_as_utc("report generated_at", item[1].generated_at), item[0]),
        )
    )


def _duplicate_generated_at_count(
    reports: tuple[PaperResearchPacketReport, ...],
) -> int:
    counts: dict[datetime, int] = {}
    for report in reports:
        generated_at = _as_utc("report generated_at", report.generated_at)
        counts[generated_at] = counts.get(generated_at, 0) + 1
    return sum(count - 1 for count in counts.values() if count > 1)


def _validate_history_report(report: PaperResearchPacketDbHistoryReport) -> None:
    if report.report_count == 0:
        _validate_empty_history_report(report)
    else:
        _validate_nonempty_history_report(report)
    if report.duplicate_generated_at_count >= max(report.report_count, 1):
        raise ValueError("duplicate_generated_at_count must be below report_count")


def _validate_empty_history_report(
    report: PaperResearchPacketDbHistoryReport,
) -> None:
    if report.first_report_generated_at is not None:
        raise ValueError("first_report_generated_at must be absent without reports")
    if report.latest_report_generated_at is not None:
        raise ValueError("latest_report_generated_at must be absent without reports")
    if report.duplicate_generated_at_count != 0:
        raise ValueError("duplicate_generated_at_count must be zero without reports")
    for field_name in _LATEST_PACKET_FIELD_NAMES + _LATEST_TOP_PACKET_FIELD_NAMES:
        if getattr(report, field_name) is not None:
            raise ValueError(f"{field_name} must be absent without reports")


def _validate_nonempty_history_report(
    report: PaperResearchPacketDbHistoryReport,
) -> None:
    if report.first_report_generated_at is None:
        raise ValueError("first_report_generated_at is required with reports")
    if report.latest_report_generated_at is None:
        raise ValueError("latest_report_generated_at is required with reports")
    if report.latest_report_generated_at < report.first_report_generated_at:
        raise ValueError("latest_report_generated_at must not precede first report")
    for field_name in _LATEST_PACKET_FIELD_NAMES:
        if getattr(report, field_name) is None:
            raise ValueError(f"{field_name} is required with reports")
    _validate_latest_packet_counts(report)
    _validate_latest_top_packet_fields(report)


def _validate_latest_packet_counts(
    report: PaperResearchPacketDbHistoryReport,
) -> None:
    if report.latest_input_row_count is None or report.latest_packet_row_count is None:
        raise ValueError("latest packet counts are required with reports")
    if report.latest_input_row_count < report.latest_packet_row_count:
        raise ValueError("latest_input_row_count must cover latest_packet_row_count")
    if (
        report.latest_included_count is None
        or report.latest_skipped_count is None
        or report.latest_high_priority_count is None
        or report.latest_medium_priority_count is None
        or report.latest_low_priority_count is None
    ):
        raise ValueError("latest packet priority counts are required with reports")
    if (
        report.latest_included_count + report.latest_skipped_count
        != report.latest_packet_row_count
    ):
        raise ValueError("latest packet priority counts must match row count")
    if (
        report.latest_high_priority_count
        + report.latest_medium_priority_count
        + report.latest_low_priority_count
        != report.latest_included_count
    ):
        raise ValueError("latest priority counts must match included count")


def _validate_latest_top_packet_fields(
    report: PaperResearchPacketDbHistoryReport,
) -> None:
    if report.latest_packet_row_count is None:
        raise ValueError("latest_packet_row_count is required")
    required_top_fields = (
        "latest_top_packet_rank",
        "latest_top_packet_market_slug",
        "latest_top_packet_side",
        "latest_top_packet_research_priority",
        "latest_top_packet_recommendation_score",
        "latest_top_packet_net_edge",
        "latest_top_packet_reason_codes",
    )
    if report.latest_packet_row_count == 0:
        for field_name in _LATEST_TOP_PACKET_FIELD_NAMES:
            if getattr(report, field_name) is not None:
                raise ValueError(f"{field_name} must be absent without packet rows")
        return
    for field_name in required_top_fields:
        if getattr(report, field_name) is None:
            raise ValueError(f"{field_name} is required with packet rows")
    if (
        report.latest_top_packet_rank is not None
        and report.latest_top_packet_rank > report.latest_packet_row_count
    ):
        raise ValueError("latest_top_packet_rank must not exceed latest packet rows")


_LATEST_PACKET_FIELD_NAMES = (
    "latest_packet_config_version",
    "latest_input_row_count",
    "latest_packet_row_count",
    "latest_included_count",
    "latest_skipped_count",
    "latest_high_priority_count",
    "latest_medium_priority_count",
    "latest_low_priority_count",
)

_LATEST_TOP_PACKET_FIELD_NAMES = (
    "latest_top_packet_rank",
    "latest_top_packet_market_slug",
    "latest_top_packet_side",
    "latest_top_packet_research_priority",
    "latest_top_packet_recommendation_score",
    "latest_top_packet_net_edge",
    "latest_top_packet_allocated_notional",
    "latest_top_packet_requested_notional",
    "latest_top_packet_reason_codes",
)


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


def _as_optional_utc(field_name: str, value: object) -> datetime | None:
    if value is None:
        return None
    return _as_utc(field_name, value)


def _quantize_optional_nonnegative_decimal(
    field_name: str,
    value: object,
) -> Decimal | None:
    decimal_value = _quantize_optional_decimal(field_name, value)
    if decimal_value is not None and decimal_value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return decimal_value


def _quantize_optional_score(
    field_name: str,
    value: object,
) -> Decimal | None:
    decimal_value = _quantize_optional_nonnegative_decimal(field_name, value)
    if decimal_value is not None and decimal_value > ONE:
        raise ValueError(f"{field_name} must be at most 1")
    return decimal_value


def _quantize_optional_decimal(
    field_name: str,
    value: object,
) -> Decimal | None:
    if value is None:
        return None
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal or None")
    return _quantize_decimal(field_name, value)


def _quantize_decimal(field_name: str, value: Decimal) -> Decimal:
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    quantized = value.quantize(DECIMAL_QUANTUM)
    if value != quantized:
        raise ValueError(f"{field_name} must use 0.000001 precision")
    return quantized


def _normalize_optional_reason_codes(
    field_name: str,
    value: object,
) -> tuple[str, ...] | None:
    if value is None:
        return None
    if type(value) is not tuple:
        raise ValueError(f"{field_name} must be a tuple or None")
    if not value:
        raise ValueError(f"{field_name} must not be empty")
    seen: set[str] = set()
    for reason_code in value:
        _require_canonical_string("reason_code", reason_code)
        if reason_code in seen:
            raise ValueError(f"{field_name} must be unique")
        seen.add(reason_code)
    return value


def _require_optional_side(field_name: str, value: object) -> None:
    if value is None:
        return
    if type(value) is not str or value not in SIDES:
        raise ValueError(f"{field_name} must be yes, no, or none")


def _require_optional_research_priority(field_name: str, value: object) -> None:
    if value is None:
        return
    if type(value) is not str or value not in RESEARCH_PRIORITIES:
        raise ValueError(f"{field_name} must be high, medium, low, or skip")


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")


def _require_optional_nonnegative_int(field_name: str, value: object) -> None:
    if value is None:
        return
    _require_nonnegative_int(field_name, value)


def _require_optional_positive_int(field_name: str, value: object) -> None:
    if value is None:
        return
    _require_positive_int(field_name, value)


def _require_nonnegative_int(field_name: str, value: object) -> None:
    if type(value) is not int:
        raise ValueError(f"{field_name} must be an int")
    if value < 0:
        raise ValueError(f"{field_name} must be nonnegative")


def _require_positive_int(field_name: str, value: object) -> None:
    _require_nonnegative_int(field_name, value)
    if value == 0:
        raise ValueError(f"{field_name} must be positive")


def _require_hard_flags(value: object) -> None:
    if getattr(value, "paper_only", None) is not True:
        raise ValueError("paper_only must be True")
    if getattr(value, "report_only", None) is not True:
        raise ValueError("report_only must be True")
    if getattr(value, "readonly", None) is not True:
        raise ValueError("readonly must be True")
