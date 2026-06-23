"""Pure paper research packet quality reducer."""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from decimal import Decimal

from polymarket_alpha_lab.paper_research_packet import PaperResearchPacketReport


__all__ = (
    "DEFAULT_PAPER_RESEARCH_PACKET_QUALITY_CONFIG_VERSION",
    "PaperResearchPacketQualityConfig",
    "PaperResearchPacketQualityCheckRow",
    "PaperResearchPacketQualityReasonCodeCount",
    "PaperResearchPacketQualityReport",
    "build_paper_research_packet_quality_report",
)


ZERO = Decimal("0")
ONE = Decimal("1")
QUANTUM = Decimal("0.000001")
CHECK_NAMES = ("source_freshness", "packet_population", "skip_pressure")
QUALITY_STATUSES = ("pass", "watch", "blocked")
DEFAULT_PAPER_RESEARCH_PACKET_QUALITY_CONFIG_VERSION = (
    "paper-research-packet-quality-v0"
)


@dataclass(frozen=True)
class PaperResearchPacketQualityConfig:
    config_version: str = DEFAULT_PAPER_RESEARCH_PACKET_QUALITY_CONFIG_VERSION
    max_source_age_seconds: int = 21_600
    blocked_source_age_seconds: int = 86_400
    min_included_count: int = 1
    max_skipped_share: Decimal = Decimal("0.500000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("config_version", self.config_version)
        _require_positive_int("max_source_age_seconds", self.max_source_age_seconds)
        _require_positive_int(
            "blocked_source_age_seconds",
            self.blocked_source_age_seconds,
        )
        _require_positive_int("min_included_count", self.min_included_count)
        if self.blocked_source_age_seconds <= self.max_source_age_seconds:
            raise ValueError(
                "blocked_source_age_seconds must exceed max_source_age_seconds",
            )
        object.__setattr__(
            self,
            "max_skipped_share",
            _normalize_probability("max_skipped_share", self.max_skipped_share),
        )
        _validate_hard_flags("config", self)


@dataclass(frozen=True)
class PaperResearchPacketQualityCheckRow:
    check_name: str
    status: str
    observed_value: int | Decimal | None
    threshold: int | Decimal | None
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_check_name("check_name", self.check_name)
        _require_status("status", self.status)
        object.__setattr__(
            self,
            "observed_value",
            _normalize_measure_value("observed_value", self.observed_value),
        )
        object.__setattr__(
            self,
            "threshold",
            _normalize_measure_value("threshold", self.threshold),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        _validate_hard_flags("check row", self)


@dataclass(frozen=True)
class PaperResearchPacketQualityReasonCodeCount:
    reason_code: str
    count: int
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("reason_code", self.reason_code)
        _require_positive_int("count", self.count)
        _validate_hard_flags("reason count row", self)


@dataclass(frozen=True)
class PaperResearchPacketQualityReport:
    generated_at: datetime
    config_version: str
    source_generated_at: datetime
    source_config_version: str
    input_row_count: int
    packet_row_count: int
    included_count: int
    skipped_count: int
    high_priority_count: int
    medium_priority_count: int
    low_priority_count: int
    source_age_seconds: int
    included_share: Decimal | None
    skipped_share: Decimal | None
    check_count: int
    pass_count: int
    watch_count: int
    blocked_count: int
    quality_status: str
    check_rows: tuple[PaperResearchPacketQualityCheckRow, ...]
    reason_code_counts: tuple[PaperResearchPacketQualityReasonCodeCount, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        object.__setattr__(
            self,
            "source_generated_at",
            _as_utc("source_generated_at", self.source_generated_at),
        )
        _require_canonical_string("config_version", self.config_version)
        _require_canonical_string("source_config_version", self.source_config_version)
        if self.source_generated_at > self.generated_at:
            raise ValueError("source generated_at must not be after generated_at")
        for field_name in (
            "input_row_count",
            "packet_row_count",
            "included_count",
            "skipped_count",
            "high_priority_count",
            "medium_priority_count",
            "low_priority_count",
            "source_age_seconds",
            "check_count",
            "pass_count",
            "watch_count",
            "blocked_count",
        ):
            _require_nonnegative_int(field_name, getattr(self, field_name))
        object.__setattr__(
            self,
            "included_share",
            _normalize_ratio("included_share", self.included_share),
        )
        object.__setattr__(
            self,
            "skipped_share",
            _normalize_ratio("skipped_share", self.skipped_share),
        )
        _require_status("quality_status", self.quality_status)
        object.__setattr__(self, "check_rows", _normalize_check_rows(self.check_rows))
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        _validate_report_consistency(self)
        _validate_hard_flags("quality report", self)


def build_paper_research_packet_quality_report(
    packet_report: PaperResearchPacketReport,
    *,
    config: PaperResearchPacketQualityConfig,
    generated_at: datetime,
) -> PaperResearchPacketQualityReport:
    if type(packet_report) is not PaperResearchPacketReport:
        raise ValueError("packet_report must be a PaperResearchPacketReport")
    if type(config) is not PaperResearchPacketQualityConfig:
        raise ValueError("config must be a PaperResearchPacketQualityConfig")
    _validate_hard_flags("packet report", packet_report)
    _validate_hard_flags("config", config)

    generated_at_utc = _as_utc("generated_at", generated_at)
    source_generated_at = _as_utc("source_generated_at", packet_report.generated_at)
    if source_generated_at > generated_at_utc:
        raise ValueError("source generated_at must not be after generated_at")

    source_age_seconds = _timedelta_seconds(generated_at_utc - source_generated_at)
    included_share = _ratio(packet_report.included_count, packet_report.packet_row_count)
    skipped_share = _ratio(packet_report.skipped_count, packet_report.packet_row_count)
    check_rows = _build_check_rows(
        packet_report=packet_report,
        config=config,
        source_age_seconds=source_age_seconds,
        included_share=included_share,
        skipped_share=skipped_share,
    )
    reason_code_counts = _reason_code_counts(check_rows, packet_report.packet_rows)

    return PaperResearchPacketQualityReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        source_generated_at=source_generated_at,
        source_config_version=packet_report.config_version,
        input_row_count=packet_report.input_row_count,
        packet_row_count=packet_report.packet_row_count,
        included_count=packet_report.included_count,
        skipped_count=packet_report.skipped_count,
        high_priority_count=packet_report.high_priority_count,
        medium_priority_count=packet_report.medium_priority_count,
        low_priority_count=packet_report.low_priority_count,
        source_age_seconds=source_age_seconds,
        included_share=included_share,
        skipped_share=skipped_share,
        check_count=len(check_rows),
        pass_count=_status_count(check_rows, "pass"),
        watch_count=_status_count(check_rows, "watch"),
        blocked_count=_status_count(check_rows, "blocked"),
        quality_status=_quality_status(check_rows),
        check_rows=check_rows,
        reason_code_counts=reason_code_counts,
    )


def _build_check_rows(
    *,
    packet_report: PaperResearchPacketReport,
    config: PaperResearchPacketQualityConfig,
    source_age_seconds: int,
    included_share: Decimal | None,
    skipped_share: Decimal | None,
) -> tuple[PaperResearchPacketQualityCheckRow, ...]:
    return (
        _source_freshness_check(config=config, source_age_seconds=source_age_seconds),
        _packet_population_check(packet_report=packet_report, config=config),
        _skip_pressure_check(config=config, skipped_share=skipped_share),
    )


def _source_freshness_check(
    *,
    config: PaperResearchPacketQualityConfig,
    source_age_seconds: int,
) -> PaperResearchPacketQualityCheckRow:
    if source_age_seconds > config.blocked_source_age_seconds:
        return PaperResearchPacketQualityCheckRow(
            check_name="source_freshness",
            status="blocked",
            observed_value=source_age_seconds,
            threshold=config.blocked_source_age_seconds,
            reason_codes=("source_report_expired",),
        )
    if source_age_seconds > config.max_source_age_seconds:
        return PaperResearchPacketQualityCheckRow(
            check_name="source_freshness",
            status="watch",
            observed_value=source_age_seconds,
            threshold=config.max_source_age_seconds,
            reason_codes=("source_report_stale",),
        )
    return PaperResearchPacketQualityCheckRow(
        check_name="source_freshness",
        status="pass",
        observed_value=source_age_seconds,
        threshold=config.max_source_age_seconds,
        reason_codes=("source_freshness_passed",),
    )


def _packet_population_check(
    *,
    packet_report: PaperResearchPacketReport,
    config: PaperResearchPacketQualityConfig,
) -> PaperResearchPacketQualityCheckRow:
    if packet_report.packet_row_count == 0:
        return PaperResearchPacketQualityCheckRow(
            check_name="packet_population",
            status="blocked",
            observed_value=packet_report.included_count,
            threshold=config.min_included_count,
            reason_codes=("packet_rows_missing",),
        )
    if packet_report.included_count < config.min_included_count:
        return PaperResearchPacketQualityCheckRow(
            check_name="packet_population",
            status="blocked",
            observed_value=packet_report.included_count,
            threshold=config.min_included_count,
            reason_codes=("included_count_below_minimum",),
        )
    return PaperResearchPacketQualityCheckRow(
        check_name="packet_population",
        status="pass",
        observed_value=packet_report.included_count,
        threshold=config.min_included_count,
        reason_codes=("packet_population_passed",),
    )


def _skip_pressure_check(
    *,
    config: PaperResearchPacketQualityConfig,
    skipped_share: Decimal | None,
) -> PaperResearchPacketQualityCheckRow:
    if skipped_share is None:
        return PaperResearchPacketQualityCheckRow(
            check_name="skip_pressure",
            status="pass",
            observed_value=None,
            threshold=config.max_skipped_share,
            reason_codes=("skip_pressure_passed",),
        )
    if skipped_share > config.max_skipped_share:
        return PaperResearchPacketQualityCheckRow(
            check_name="skip_pressure",
            status="watch",
            observed_value=skipped_share,
            threshold=config.max_skipped_share,
            reason_codes=("skipped_share_above_threshold",),
        )
    return PaperResearchPacketQualityCheckRow(
        check_name="skip_pressure",
        status="pass",
        observed_value=skipped_share,
        threshold=config.max_skipped_share,
        reason_codes=("skip_pressure_passed",),
    )


def _reason_code_counts(
    check_rows: tuple[PaperResearchPacketQualityCheckRow, ...],
    packet_rows: tuple[object, ...],
) -> tuple[PaperResearchPacketQualityReasonCodeCount, ...]:
    counts: Counter[str] = Counter()
    for row in check_rows:
        for reason_code in row.reason_codes:
            counts[reason_code] += 1
    for row in packet_rows:
        for reason_code in row.reason_codes:
            counts[reason_code] += 1
    return tuple(
        PaperResearchPacketQualityReasonCodeCount(reason_code=reason_code, count=count)
        for reason_code, count in sorted(counts.items(), key=lambda item: (-item[1], item[0]))
    )


def _quality_status(check_rows: tuple[PaperResearchPacketQualityCheckRow, ...]) -> str:
    if any(row.status == "blocked" for row in check_rows):
        return "blocked"
    if any(row.status == "watch" for row in check_rows):
        return "watch"
    return "pass"


def _status_count(
    check_rows: tuple[PaperResearchPacketQualityCheckRow, ...],
    status: str,
) -> int:
    return sum(1 for row in check_rows if row.status == status)


def _validate_report_consistency(report: PaperResearchPacketQualityReport) -> None:
    if report.check_count != len(report.check_rows):
        raise ValueError("check_count must match check_rows")
    if tuple(row.check_name for row in report.check_rows) != CHECK_NAMES:
        raise ValueError("check_rows must be deterministic")
    if report.pass_count != _status_count(report.check_rows, "pass"):
        raise ValueError("pass_count must match check_rows")
    if report.watch_count != _status_count(report.check_rows, "watch"):
        raise ValueError("watch_count must match check_rows")
    if report.blocked_count != _status_count(report.check_rows, "blocked"):
        raise ValueError("blocked_count must match check_rows")
    if report.check_count != report.pass_count + report.watch_count + report.blocked_count:
        raise ValueError("check_count must match status counts")
    if report.quality_status != _quality_status(report.check_rows):
        raise ValueError("quality_status must match check_rows")
    if report.packet_row_count != report.included_count + report.skipped_count:
        raise ValueError("packet_row_count must match included_count and skipped_count")
    if report.packet_row_count == 0:
        if report.included_share is not None:
            raise ValueError("included_share must be None when packet_row_count is zero")
        if report.skipped_share is not None:
            raise ValueError("skipped_share must be None when packet_row_count is zero")
    else:
        if report.included_share != _ratio(report.included_count, report.packet_row_count):
            raise ValueError("included_share must match packet_row_count")
        if report.skipped_share != _ratio(report.skipped_count, report.packet_row_count):
            raise ValueError("skipped_share must match packet_row_count")
    if report.input_row_count < report.packet_row_count:
        raise ValueError("input_row_count must cover packet_row_count")
    if (
        report.high_priority_count
        + report.medium_priority_count
        + report.low_priority_count
        != report.included_count
    ):
        raise ValueError("priority counts must match included_count")


def _normalize_check_rows(
    rows: object,
) -> tuple[PaperResearchPacketQualityCheckRow, ...]:
    normalized = _normalize_tuple(rows, "check_rows")
    for row in normalized:
        if type(row) is not PaperResearchPacketQualityCheckRow:
            raise ValueError("check_rows must contain quality check rows")
        _validate_hard_flags("check row", row)
    return normalized


def _normalize_reason_code_counts(
    rows: object,
) -> tuple[PaperResearchPacketQualityReasonCodeCount, ...]:
    normalized = _normalize_tuple(rows, "reason_code_counts")
    for row in normalized:
        if type(row) is not PaperResearchPacketQualityReasonCodeCount:
            raise ValueError("reason_code_counts must contain quality reason count rows")
        _validate_hard_flags("reason count row", row)
    sorted_rows = tuple(sorted(normalized, key=lambda row: (-row.count, row.reason_code)))
    if normalized != sorted_rows:
        raise ValueError("reason_code_counts must be deterministically sorted")
    return normalized


def _normalize_tuple(value: object, field_name: str) -> tuple[object, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError(f"{field_name} must be an iterable")
    try:
        return tuple(value)
    except TypeError as exc:
        raise ValueError(f"{field_name} must be an iterable") from exc


def _normalize_reason_codes(field_name: str, value: object) -> tuple[str, ...]:
    normalized = _normalize_tuple(value, field_name)
    if not normalized:
        raise ValueError(f"{field_name} must contain at least one value")
    seen: set[str] = set()
    for item in normalized:
        _require_canonical_string(field_name, item)
        if item in seen:
            raise ValueError(f"{field_name} must not contain duplicates")
        seen.add(item)
    return normalized


def _normalize_measure_value(field_name: str, value: object) -> int | Decimal | None:
    if value is None:
        return None
    if type(value) is int:
        return value
    if type(value) is Decimal:
        return _quantize_decimal(field_name, value)
    raise ValueError(f"{field_name} must be an int or Decimal")


def _normalize_ratio(field_name: str, value: object) -> Decimal | None:
    if value is None:
        return None
    return _normalize_probability(field_name, value)


def _ratio(count: int, total: int) -> Decimal | None:
    if total == 0:
        return None
    return (Decimal(count) / Decimal(total)).quantize(QUANTUM)


def _timedelta_seconds(value: timedelta) -> int:
    if value < timedelta(0):
        raise ValueError("source generated_at must not be after generated_at")
    return value.days * 86_400 + value.seconds


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")


def _require_positive_int(field_name: str, value: object) -> None:
    if type(value) is not int:
        raise ValueError(f"{field_name} must be an int")
    if value <= 0:
        raise ValueError(f"{field_name} must be positive")


def _require_nonnegative_int(field_name: str, value: object) -> None:
    if type(value) is not int:
        raise ValueError(f"{field_name} must be an int")
    if value < 0:
        raise ValueError(f"{field_name} must be nonnegative")


def _require_decimal(field_name: str, value: object) -> None:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")


def _quantize_decimal(field_name: str, value: object) -> Decimal:
    _require_decimal(field_name, value)
    return value.quantize(QUANTUM)


def _normalize_probability(field_name: str, value: object) -> Decimal:
    probability = _quantize_decimal(field_name, value)
    if probability < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    if probability > ONE:
        raise ValueError(f"{field_name} must be at most 1")
    return probability


def _require_check_name(field_name: str, value: object) -> None:
    _require_canonical_string(field_name, value)
    if value not in CHECK_NAMES:
        raise ValueError(f"{field_name} must be a known quality check")


def _require_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in QUALITY_STATUSES:
        raise ValueError(f"{field_name} must be pass, watch, or blocked")


def _validate_hard_flags(field_name: str, value: object) -> None:
    for flag_name in ("paper_only", "report_only", "readonly"):
        if getattr(value, flag_name, None) is not True:
            raise ValueError(f"{field_name} must be {flag_name}")
