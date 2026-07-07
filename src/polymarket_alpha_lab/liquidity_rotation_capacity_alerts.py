"""Pure report-only capacity alerts from supplied liquidity rotation summaries."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
import hashlib
from typing import Any

from polymarket_alpha_lab.team_paper_guard import (
    json_ready_no_floats,
    reject_unsafe_surface_fields,
    require_paper_only_flags,
)


DEFAULT_LIQUIDITY_ROTATION_CAPACITY_ALERTS_CONFIG_VERSION = (
    "liquidity-rotation-capacity-alerts-v0"
)
ROTATION_STATUSES = ("stable", "rotating_in", "rotating_out")
ALERT_STATUSES = ("pass", "watch", "blocked")
ROW_REASON_CODES = (
    "liquidity_rotation_capacity_clear",
    "liquidity_rotation_capacity_source_missing",
    "rotating_in_capacity_ready",
    "rotating_in_capacity_watch",
    "rotating_in_capacity_blocked",
    "rotating_out_capacity_release",
    "rotating_out_capacity_still_pressured",
    "stable_capacity_pressure_observed",
    "capacity_gap_present",
    "low_slot_coverage",
    "capacity_pressure_watch",
    "capacity_pressure_blocked",
)
REPORT_REASON_CODES = (
    "liquidity_rotation_capacity_clear",
    "liquidity_rotation_capacity_watch",
    "liquidity_rotation_capacity_blocked",
    "liquidity_rotation_capacity_source_missing",
)

COUNT_QUANTUM = Decimal("1")
RATIO_QUANTUM = Decimal("0.000001")
ZERO_COUNT = Decimal("0")
ZERO_RATIO = Decimal("0.000000")
ONE_RATIO = Decimal("1.000000")
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
STATUS_WEIGHT = {
    "blocked": Decimal("0.000000"),
    "watch": Decimal("1.000000"),
    "pass": Decimal("2.000000"),
}


@dataclass(frozen=True)
class LiquidityRotationCapacityAlertsConfig:
    config_version: str = DEFAULT_LIQUIDITY_ROTATION_CAPACITY_ALERTS_CONFIG_VERSION
    min_rotation_in_share_delta: Decimal = Decimal("0.050000")
    capacity_pressure_watch_ratio: Decimal = Decimal("1.000000")
    capacity_pressure_blocked_ratio: Decimal = Decimal("2.000000")
    min_slot_coverage_ratio: Decimal = Decimal("0.500000")
    blocked_capacity_gap_count: Decimal = Decimal("1")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("config_version", self.config_version)
        for field_name in (
            "min_rotation_in_share_delta",
            "capacity_pressure_watch_ratio",
            "capacity_pressure_blocked_ratio",
            "min_slot_coverage_ratio",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "blocked_capacity_gap_count",
            _normalize_nonnegative_count(
                "blocked_capacity_gap_count",
                self.blocked_capacity_gap_count,
            ),
        )
        if self.capacity_pressure_blocked_ratio < self.capacity_pressure_watch_ratio:
            raise ValueError(
                "capacity_pressure_blocked_ratio must be >= "
                "capacity_pressure_watch_ratio",
            )
        require_paper_only_flags("LiquidityRotationCapacityAlertsConfig", self)


@dataclass(frozen=True)
class LiquidityRotationCapacitySummary:
    category_id: str
    team_id: str
    rotation_status: str
    liquidity_share_ratio_delta: Decimal
    ending_liquidity_share_ratio: Decimal
    capacity_pressure_ratio: Decimal
    slot_coverage_ratio: Decimal
    capacity_gap_count: Decimal
    source_row_count: Decimal = Decimal("1")
    source_missing: bool = False
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("category_id", self.category_id)
        _require_canonical_string("team_id", self.team_id)
        _require_member("rotation_status", self.rotation_status, ROTATION_STATUSES)
        object.__setattr__(
            self,
            "liquidity_share_ratio_delta",
            _normalize_decimal(
                "liquidity_share_ratio_delta",
                self.liquidity_share_ratio_delta,
            ),
        )
        object.__setattr__(
            self,
            "ending_liquidity_share_ratio",
            _normalize_ratio(
                "ending_liquidity_share_ratio",
                self.ending_liquidity_share_ratio,
            ),
        )
        for field_name in ("capacity_pressure_ratio", "slot_coverage_ratio"):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "capacity_gap_count",
            _normalize_nonnegative_count("capacity_gap_count", self.capacity_gap_count),
        )
        object.__setattr__(
            self,
            "source_row_count",
            _normalize_nonnegative_count("source_row_count", self.source_row_count),
        )
        if type(self.source_missing) is not bool:
            raise ValueError("source_missing must be a bool")
        require_paper_only_flags("LiquidityRotationCapacitySummary", self)


@dataclass(frozen=True)
class LiquidityRotationCapacityAlertRow:
    redacted_category_ref: str
    redacted_team_ref: str
    rotation_status: str
    liquidity_share_ratio_delta: Decimal
    ending_liquidity_share_ratio: Decimal
    capacity_pressure_ratio: Decimal
    slot_coverage_ratio: Decimal
    capacity_gap_count: Decimal
    source_row_count: Decimal
    alert_status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_redacted_ref("redacted_category_ref", self.redacted_category_ref)
        _require_redacted_ref("redacted_team_ref", self.redacted_team_ref)
        _require_member("rotation_status", self.rotation_status, ROTATION_STATUSES)
        object.__setattr__(
            self,
            "liquidity_share_ratio_delta",
            _normalize_decimal(
                "liquidity_share_ratio_delta",
                self.liquidity_share_ratio_delta,
            ),
        )
        object.__setattr__(
            self,
            "ending_liquidity_share_ratio",
            _normalize_ratio(
                "ending_liquidity_share_ratio",
                self.ending_liquidity_share_ratio,
            ),
        )
        for field_name in ("capacity_pressure_ratio", "slot_coverage_ratio"):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in ("capacity_gap_count", "source_row_count"):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_count(field_name, getattr(self, field_name)),
            )
        _require_member("alert_status", self.alert_status, ALERT_STATUSES)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, ROW_REASON_CODES),
        )
        _validate_alert_row(self)
        require_paper_only_flags("LiquidityRotationCapacityAlertRow", self)


@dataclass(frozen=True)
class LiquidityRotationCapacityAlertsReport:
    generated_at: datetime
    config_version: str
    source_summary_count: Decimal
    alert_row_count: Decimal
    pass_alert_count: Decimal
    watch_alert_count: Decimal
    blocked_alert_count: Decimal
    source_missing_count: Decimal
    status: str
    reason_codes: tuple[str, ...]
    alert_rows: tuple[LiquidityRotationCapacityAlertRow, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        for field_name in (
            "source_summary_count",
            "alert_row_count",
            "pass_alert_count",
            "watch_alert_count",
            "blocked_alert_count",
            "source_missing_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_count(field_name, getattr(self, field_name)),
            )
        _require_member("status", self.status, ALERT_STATUSES)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(
                "reason_codes",
                self.reason_codes,
                REPORT_REASON_CODES,
            ),
        )
        object.__setattr__(self, "alert_rows", _normalize_alert_rows(self.alert_rows))
        _validate_report(self)
        if self.derived_validation_digest == "":
            object.__setattr__(
                self,
                "derived_validation_digest",
                _report_derived_validation_digest(self),
            )
        else:
            _require_validation_digest(
                "derived_validation_digest",
                self.derived_validation_digest,
            )
            if self.derived_validation_digest != _report_derived_validation_digest(self):
                raise ValueError("derived_validation_digest must match report fields")
        reject_unsafe_surface_fields("liquidity rotation capacity alerts report", self)
        require_paper_only_flags("LiquidityRotationCapacityAlertsReport", self)


def build_liquidity_rotation_capacity_alerts_report(
    summaries: Iterable[LiquidityRotationCapacitySummary],
    *,
    config: LiquidityRotationCapacityAlertsConfig,
    generated_at: datetime,
) -> LiquidityRotationCapacityAlertsReport:
    if type(config) is not LiquidityRotationCapacityAlertsConfig:
        raise ValueError("config must be a LiquidityRotationCapacityAlertsConfig")
    require_paper_only_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    normalized_summaries = _normalize_summaries(summaries)
    category_refs = _redaction_refs(
        tuple(summary.category_id for summary in normalized_summaries),
        label="category",
    )
    team_refs = _redaction_refs(
        tuple(summary.team_id for summary in normalized_summaries),
        label="team",
    )
    rows = tuple(
        sorted(
            (
                _alert_row(
                    summary,
                    redacted_category_ref=category_refs[summary.category_id],
                    redacted_team_ref=team_refs[summary.team_id],
                    config=config,
                )
                for summary in normalized_summaries
            ),
            key=_alert_row_sort_key,
        ),
    )
    status = _report_status(rows)
    return LiquidityRotationCapacityAlertsReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        source_summary_count=_count(len(normalized_summaries)),
        alert_row_count=_count(len(rows)),
        pass_alert_count=_status_count(rows, "pass"),
        watch_alert_count=_status_count(rows, "watch"),
        blocked_alert_count=_status_count(rows, "blocked"),
        source_missing_count=_source_missing_count(rows),
        status=status,
        reason_codes=_report_reason_codes(rows, status),
        alert_rows=rows,
    )


def liquidity_rotation_capacity_alerts_payload(
    report: LiquidityRotationCapacityAlertsReport,
) -> dict[str, Any]:
    if type(report) is not LiquidityRotationCapacityAlertsReport:
        raise ValueError("report must be a LiquidityRotationCapacityAlertsReport")
    require_paper_only_flags("report", report)
    reject_unsafe_surface_fields("liquidity rotation capacity alerts report", report)
    return json_ready_no_floats(report)


def _normalize_summaries(
    summaries: Iterable[LiquidityRotationCapacitySummary],
) -> tuple[LiquidityRotationCapacitySummary, ...]:
    if isinstance(summaries, (str, bytes)):
        raise ValueError("summaries must be an iterable")
    try:
        normalized = tuple(summaries)
    except TypeError as exc:
        raise ValueError("summaries must be an iterable") from exc
    seen: set[tuple[str, str]] = set()
    for summary in normalized:
        if type(summary) is not LiquidityRotationCapacitySummary:
            raise ValueError(
                "summaries must contain LiquidityRotationCapacitySummary values",
            )
        require_paper_only_flags("summary", summary)
        key = (summary.category_id, summary.team_id)
        if key in seen:
            raise ValueError("summaries must not contain duplicate category team pairs")
        seen.add(key)
    return normalized


def _redaction_refs(values: tuple[str, ...], *, label: str) -> dict[str, str]:
    return {
        value: f"<redacted-{label}-{index:03d}>"
        for index, value in enumerate(sorted(set(values)), start=1)
    }


def _alert_row(
    summary: LiquidityRotationCapacitySummary,
    *,
    redacted_category_ref: str,
    redacted_team_ref: str,
    config: LiquidityRotationCapacityAlertsConfig,
) -> LiquidityRotationCapacityAlertRow:
    alert_status, reason_codes = _alert_status_and_reasons(summary, config)
    return LiquidityRotationCapacityAlertRow(
        redacted_category_ref=redacted_category_ref,
        redacted_team_ref=redacted_team_ref,
        rotation_status=summary.rotation_status,
        liquidity_share_ratio_delta=summary.liquidity_share_ratio_delta,
        ending_liquidity_share_ratio=summary.ending_liquidity_share_ratio,
        capacity_pressure_ratio=summary.capacity_pressure_ratio,
        slot_coverage_ratio=summary.slot_coverage_ratio,
        capacity_gap_count=summary.capacity_gap_count,
        source_row_count=summary.source_row_count,
        alert_status=alert_status,
        reason_codes=reason_codes,
    )


def _alert_status_and_reasons(
    summary: LiquidityRotationCapacitySummary,
    config: LiquidityRotationCapacityAlertsConfig,
) -> tuple[str, tuple[str, ...]]:
    if summary.source_missing or summary.source_row_count == ZERO_COUNT:
        return "watch", ("liquidity_rotation_capacity_source_missing",)

    capacity_gap_present = summary.capacity_gap_count >= config.blocked_capacity_gap_count
    capacity_gap_present = capacity_gap_present and config.blocked_capacity_gap_count > ZERO_COUNT
    blocked_pressure = (
        summary.capacity_pressure_ratio >= config.capacity_pressure_blocked_ratio
    )
    watch_pressure = summary.capacity_pressure_ratio >= config.capacity_pressure_watch_ratio
    low_slot_coverage = summary.slot_coverage_ratio < config.min_slot_coverage_ratio
    significant_rotation_in = (
        summary.rotation_status == "rotating_in"
        and summary.liquidity_share_ratio_delta >= config.min_rotation_in_share_delta
    )

    if significant_rotation_in:
        if capacity_gap_present or blocked_pressure or low_slot_coverage:
            return (
                "blocked",
                _row_reason_codes(
                    "rotating_in_capacity_blocked",
                    capacity_gap_present=capacity_gap_present,
                    low_slot_coverage=low_slot_coverage,
                    watch_pressure=False,
                    blocked_pressure=blocked_pressure,
                ),
            )
        if watch_pressure:
            return (
                "watch",
                _row_reason_codes(
                    "rotating_in_capacity_watch",
                    capacity_gap_present=False,
                    low_slot_coverage=False,
                    watch_pressure=True,
                    blocked_pressure=False,
                ),
            )
        return "pass", ("rotating_in_capacity_ready",)

    if summary.rotation_status == "rotating_out":
        if capacity_gap_present or watch_pressure or blocked_pressure:
            return (
                "watch",
                _row_reason_codes(
                    "rotating_out_capacity_still_pressured",
                    capacity_gap_present=capacity_gap_present,
                    low_slot_coverage=False,
                    watch_pressure=watch_pressure and not blocked_pressure,
                    blocked_pressure=blocked_pressure,
                ),
            )
        return "pass", ("rotating_out_capacity_release",)

    if capacity_gap_present or watch_pressure or blocked_pressure:
        return (
            "watch",
            _row_reason_codes(
                "stable_capacity_pressure_observed",
                capacity_gap_present=capacity_gap_present,
                low_slot_coverage=False,
                watch_pressure=watch_pressure and not blocked_pressure,
                blocked_pressure=blocked_pressure,
            ),
        )
    return "pass", ("liquidity_rotation_capacity_clear",)


def _row_reason_codes(
    primary_code: str,
    *,
    capacity_gap_present: bool,
    low_slot_coverage: bool,
    watch_pressure: bool,
    blocked_pressure: bool,
) -> tuple[str, ...]:
    codes = [primary_code]
    if capacity_gap_present:
        codes.append("capacity_gap_present")
    if low_slot_coverage:
        codes.append("low_slot_coverage")
    if watch_pressure:
        codes.append("capacity_pressure_watch")
    if blocked_pressure:
        codes.append("capacity_pressure_blocked")
    return _normalize_reason_codes("reason_codes", tuple(codes), ROW_REASON_CODES)


def _report_status(rows: tuple[LiquidityRotationCapacityAlertRow, ...]) -> str:
    if any(row.alert_status == "blocked" for row in rows):
        return "blocked"
    if any(row.alert_status == "watch" for row in rows):
        return "watch"
    return "pass"


def _report_reason_codes(
    rows: tuple[LiquidityRotationCapacityAlertRow, ...],
    status: str,
) -> tuple[str, ...]:
    if not rows or status == "pass":
        return ("liquidity_rotation_capacity_clear",)
    codes = [f"liquidity_rotation_capacity_{status}"]
    if any(
        row.reason_codes == ("liquidity_rotation_capacity_source_missing",)
        for row in rows
    ):
        codes.append("liquidity_rotation_capacity_source_missing")
    return _normalize_reason_codes("reason_codes", tuple(codes), REPORT_REASON_CODES)


def _alert_row_sort_key(
    row: LiquidityRotationCapacityAlertRow,
) -> tuple[Decimal, Decimal, Decimal, str, str]:
    return (
        STATUS_WEIGHT[row.alert_status],
        -_abs_decimal(row.liquidity_share_ratio_delta),
        -row.capacity_pressure_ratio,
        row.redacted_category_ref,
        row.redacted_team_ref,
    )


def _status_count(
    rows: tuple[LiquidityRotationCapacityAlertRow, ...],
    status: str,
) -> Decimal:
    return _count(sum(1 for row in rows if row.alert_status == status))


def _source_missing_count(rows: tuple[LiquidityRotationCapacityAlertRow, ...]) -> Decimal:
    return _count(
        sum(
            1
            for row in rows
            if row.reason_codes == ("liquidity_rotation_capacity_source_missing",)
        ),
    )


def _validate_alert_row(row: LiquidityRotationCapacityAlertRow) -> None:
    source_missing = row.reason_codes == ("liquidity_rotation_capacity_source_missing",)
    if source_missing and row.alert_status != "watch":
        raise ValueError("source missing rows must use watch alert_status")
    if row.alert_status == "blocked" and row.reason_codes[0] != "rotating_in_capacity_blocked":
        raise ValueError("blocked rows must be rotating_in capacity alerts")
    if row.alert_status == "pass" and any(
        reason_code
        in (
            "capacity_gap_present",
            "low_slot_coverage",
            "capacity_pressure_watch",
            "capacity_pressure_blocked",
        )
        for reason_code in row.reason_codes
    ):
        raise ValueError("pass rows must not include capacity pressure reason codes")


def _validate_report(report: LiquidityRotationCapacityAlertsReport) -> None:
    if report.source_summary_count != report.alert_row_count:
        raise ValueError("source_summary_count must match alert_row_count")
    if report.alert_row_count != _count(len(report.alert_rows)):
        raise ValueError("alert_row_count must match alert_rows")
    if report.pass_alert_count != _status_count(report.alert_rows, "pass"):
        raise ValueError("pass_alert_count must match alert_rows")
    if report.watch_alert_count != _status_count(report.alert_rows, "watch"):
        raise ValueError("watch_alert_count must match alert_rows")
    if report.blocked_alert_count != _status_count(report.alert_rows, "blocked"):
        raise ValueError("blocked_alert_count must match alert_rows")
    if report.source_missing_count != _source_missing_count(report.alert_rows):
        raise ValueError("source_missing_count must match alert_rows")
    if report.alert_row_count != (
        report.pass_alert_count + report.watch_alert_count + report.blocked_alert_count
    ):
        raise ValueError("alert_row_count must match alert status counts")
    if report.status != _report_status(report.alert_rows):
        raise ValueError("status must match alert_rows")
    if report.reason_codes != _report_reason_codes(report.alert_rows, report.status):
        raise ValueError("reason_codes must match alert_rows")
    if report.alert_rows != tuple(sorted(report.alert_rows, key=_alert_row_sort_key)):
        raise ValueError("alert_rows must be deterministic")


def _report_derived_validation_digest(
    report: LiquidityRotationCapacityAlertsReport,
) -> str:
    return _validation_digest(
        (
            report.generated_at,
            report.config_version,
            report.source_summary_count,
            report.alert_row_count,
            report.pass_alert_count,
            report.watch_alert_count,
            report.blocked_alert_count,
            report.source_missing_count,
            report.status,
            report.reason_codes,
            tuple(_alert_row_digest_parts(row) for row in report.alert_rows),
            report.paper_only,
            report.report_only,
            report.readonly,
        ),
    )


def _alert_row_digest_parts(row: LiquidityRotationCapacityAlertRow) -> tuple[object, ...]:
    return (
        row.redacted_category_ref,
        row.redacted_team_ref,
        row.rotation_status,
        row.liquidity_share_ratio_delta,
        row.ending_liquidity_share_ratio,
        row.capacity_pressure_ratio,
        row.slot_coverage_ratio,
        row.capacity_gap_count,
        row.source_row_count,
        row.alert_status,
        row.reason_codes,
        row.paper_only,
        row.report_only,
        row.readonly,
    )


def _validation_digest(parts: tuple[object, ...]) -> str:
    material = "\n".join(_digest_part(part) for part in parts)
    return hashlib.sha256(material.encode("utf-8")).hexdigest()


def _digest_part(value: object) -> str:
    if type(value) is Decimal:
        if not value.is_finite():
            raise ValueError("validation_digest values must be finite")
        return f"decimal:{value}"
    if type(value) is datetime:
        return f"datetime:{_as_utc('validation_digest datetime', value).isoformat()}"
    if type(value) is str:
        return f"str:{len(value)}:{value}"
    if type(value) is bool:
        if value:
            return "bool:true"
        return "bool:false"
    if type(value) is tuple:
        return "tuple:[" + ",".join(_digest_part(item) for item in value) + "]"
    raise ValueError("validation_digest values must be canonical")


def _require_validation_digest(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if len(value) != 64 or any(character not in "0123456789abcdef" for character in value):
        raise ValueError(f"{field_name} must be a lowercase sha256 digest")


def _normalize_alert_rows(
    value: Iterable[LiquidityRotationCapacityAlertRow],
) -> tuple[LiquidityRotationCapacityAlertRow, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError("alert_rows must be an iterable")
    try:
        rows = tuple(value)
    except TypeError as exc:
        raise ValueError("alert_rows must be an iterable") from exc
    for row in rows:
        if type(row) is not LiquidityRotationCapacityAlertRow:
            raise ValueError(
                "alert_rows must contain LiquidityRotationCapacityAlertRow values",
            )
        require_paper_only_flags("alert row", row)
    return rows


def _normalize_reason_codes(
    field_name: str,
    value: object,
    allowed: tuple[str, ...],
) -> tuple[str, ...]:
    if type(value) not in (list, tuple):
        raise ValueError(f"{field_name} must be a list or tuple")
    reason_codes = tuple(value)
    if not reason_codes:
        raise ValueError(f"{field_name} must not be empty")
    for reason_code in reason_codes:
        _require_member(field_name, reason_code, allowed)
    if len(set(reason_codes)) != len(reason_codes):
        raise ValueError(f"{field_name} must be unique")
    if tuple(code for code in allowed if code in reason_codes) != reason_codes:
        raise ValueError(f"{field_name} must be deterministic")
    return reason_codes


def _count(value: int) -> Decimal:
    return Decimal(value).quantize(COUNT_QUANTUM)


def _normalize_nonnegative_count(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    quantized = value.quantize(COUNT_QUANTUM)
    if quantized != value:
        raise ValueError(f"{field_name} must be integral")
    if quantized < ZERO_COUNT:
        raise ValueError(f"{field_name} must be nonnegative")
    return quantized


def _normalize_ratio(field_name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized < ZERO_RATIO or normalized > ONE_RATIO:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return normalized


def _normalize_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized < ZERO_RATIO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _normalize_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(RATIO_QUANTUM)


def _abs_decimal(value: Decimal) -> Decimal:
    if value < ZERO_RATIO:
        return -value
    return value


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_redacted_ref(field_name: str, value: object) -> None:
    _require_canonical_string(field_name, value)
    if not str(value).startswith("<redacted-") or not str(value).endswith(">"):
        raise ValueError(f"{field_name} must be redacted")


def _require_member(field_name: str, value: object, allowed: tuple[str, ...]) -> None:
    if type(value) is not str or value not in allowed:
        raise ValueError(f"{field_name} must be one of {allowed}")


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")


__all__ = (
    "DEFAULT_LIQUIDITY_ROTATION_CAPACITY_ALERTS_CONFIG_VERSION",
    "ROTATION_STATUSES",
    "ALERT_STATUSES",
    "LiquidityRotationCapacityAlertsConfig",
    "LiquidityRotationCapacitySummary",
    "LiquidityRotationCapacityAlertRow",
    "LiquidityRotationCapacityAlertsReport",
    "build_liquidity_rotation_capacity_alerts_report",
    "liquidity_rotation_capacity_alerts_payload",
)
