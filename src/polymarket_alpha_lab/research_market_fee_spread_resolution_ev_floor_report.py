"""Pure report-only fee/spread/resolution EV floor reducer."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import asdict, dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, localcontext
from hashlib import sha256
import json
from typing import Any


__all__ = (
    "EV_FLOOR_STATUSES",
    "DEFAULT_RESEARCH_MARKET_FEE_SPREAD_RESOLUTION_EV_FLOOR_REPORT_CONFIG_VERSION",
    "ResearchMarketFeeSpreadResolutionEvFloorConfig",
    "ResearchMarketFeeSpreadResolutionEvFloorInput",
    "ResearchMarketFeeSpreadResolutionEvFloorReasonCodeCount",
    "ResearchMarketFeeSpreadResolutionEvFloorReport",
    "ResearchMarketFeeSpreadResolutionEvFloorRow",
    "build_research_market_fee_spread_resolution_ev_floor_report",
    "research_market_fee_spread_resolution_ev_floor_report_payload",
    "validate_research_market_fee_spread_resolution_ev_floor_report_payload",
)


DEFAULT_RESEARCH_MARKET_FEE_SPREAD_RESOLUTION_EV_FLOOR_REPORT_CONFIG_VERSION = (
    "research-market-fee-spread-resolution-ev-floor-report-v1"
)
PASS_STATUS = "pass"
WATCH_STATUS = "watch"
BLOCK_STATUS = "block"
EV_FLOOR_STATUSES = (PASS_STATUS, WATCH_STATUS, BLOCK_STATUS)
STATUS_RANK = {
    BLOCK_STATUS: Decimal("0.000000"),
    WATCH_STATUS: Decimal("1.000000"),
    PASS_STATUS: Decimal("2.000000"),
}
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
TWO = Decimal("2.000000")
QUANTUM = Decimal("0.000001")
DECIMAL_CONTEXT = Context(prec=64)


def _join_parts(*parts: str) -> str:
    return "".join(parts)


UNSAFE_PUBLIC_FRAGMENTS = (
    _join_parts("ra", "w"),
    _join_parts("can", "didate", "_", "id"),
    _join_parts("ma", "rket", "_", "id"),
    _join_parts("ma", "rket", "_", "sl", "ug"),
    _join_parts("sl", "ug"),
    _join_parts("ques", "tion"),
    _join_parts("sour", "ce", "_", "ur", "l"),
    _join_parts("sour", "ce", "_", "tex", "t"),
    _join_parts("d", "sn"),
    _join_parts("tab", "le", "_", "name"),
    _join_parts("to", "ken"),
    _join_parts("wal", "let"),
    _join_parts("or", "der"),
    _join_parts("tra", "de"),
    _join_parts("li", "ve"),
    _join_parts("reco", "mmend"),
    _join_parts("pos", "ition"),
    _join_parts("siz", "ing"),
    _join_parts("exec", "ution"),
    _join_parts("ap", "i", "_", "key"),
    _join_parts("priv", "ate", "_", "key"),
    _join_parts("au", "th"),
    "://",
    "?",
    "@",
    "=",
)


@dataclass(frozen=True)
class ResearchMarketFeeSpreadResolutionEvFloorConfig:
    config_version: str = (
        DEFAULT_RESEARCH_MARKET_FEE_SPREAD_RESOLUTION_EV_FLOOR_REPORT_CONFIG_VERSION
    )
    pass_ev_floor_threshold: Decimal = Decimal("0.030000")
    watch_ev_floor_threshold: Decimal = Decimal("0.005000")
    block_total_drag_threshold: Decimal = Decimal("0.120000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchMarketFeeSpreadResolutionEvFloorConfig,
            "config",
        )
        _require_public_label("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_MARKET_FEE_SPREAD_RESOLUTION_EV_FLOOR_REPORT_CONFIG_VERSION
        ):
            raise ValueError("config_version must match supported value")
        for field_name in (
            "pass_ev_floor_threshold",
            "watch_ev_floor_threshold",
            "block_total_drag_threshold",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        if self.pass_ev_floor_threshold < self.watch_ev_floor_threshold:
            raise ValueError(
                "pass_ev_floor_threshold must be at least watch_ev_floor_threshold",
            )
        if self.block_total_drag_threshold <= ZERO:
            raise ValueError("block_total_drag_threshold must be positive")
        _require_hard_flags("config", self)
        _reject_unsafe_public_payload("config", self)


@dataclass(frozen=True)
class ResearchMarketFeeSpreadResolutionEvFloorInput:
    private_research_ref: str
    observed_at: datetime
    gross_expected_value_edge: Decimal
    fee_drag_ratio: Decimal
    spread_width_ratio: Decimal
    resolution_friction_ratio: Decimal
    resolution_uncertainty_ratio: Decimal
    reason_codes: tuple[str, ...] = ()
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchMarketFeeSpreadResolutionEvFloorInput,
            "input",
        )
        _require_private_ref("private_research_ref", self.private_research_ref)
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        object.__setattr__(
            self,
            "gross_expected_value_edge",
            _require_decimal(
                "gross_expected_value_edge",
                self.gross_expected_value_edge,
            ),
        )
        for field_name in (
            "fee_drag_ratio",
            "spread_width_ratio",
            "resolution_friction_ratio",
            "resolution_uncertainty_ratio",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, allow_empty=True),
        )
        _require_hard_flags("input", self)


@dataclass(frozen=True)
class ResearchMarketFeeSpreadResolutionEvFloorRow:
    public_row_ref: str
    observed_at: datetime
    gross_expected_value_edge: Decimal
    fee_drag_ratio: Decimal
    spread_width_ratio: Decimal
    spread_cost_ratio: Decimal
    resolution_friction_ratio: Decimal
    resolution_uncertainty_ratio: Decimal
    total_fee_spread_resolution_drag: Decimal
    ev_floor: Decimal
    status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchMarketFeeSpreadResolutionEvFloorRow, "row")
        _require_public_label("public_row_ref", self.public_row_ref)
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in (
            "gross_expected_value_edge",
            "ev_floor",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "fee_drag_ratio",
            "spread_width_ratio",
            "spread_cost_ratio",
            "resolution_friction_ratio",
            "resolution_uncertainty_ratio",
            "total_fee_spread_resolution_drag",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        _require_status("status", self.status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        _validate_row_consistency(self)
        _require_hard_flags("row", self)
        _reject_unsafe_public_payload("row", self)


@dataclass(frozen=True)
class ResearchMarketFeeSpreadResolutionEvFloorReasonCodeCount:
    reason_code: str
    count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchMarketFeeSpreadResolutionEvFloorReasonCodeCount,
            "reason_count",
        )
        _require_reason_code("reason_code", self.reason_code)
        object.__setattr__(
            self,
            "count",
            _require_nonnegative_decimal("count", self.count),
        )
        _require_hard_flags("reason_count", self)


@dataclass(frozen=True)
class ResearchMarketFeeSpreadResolutionEvFloorReport:
    generated_at: datetime
    config_version: str
    status: str
    input_count: Decimal
    row_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    average_ev_floor: Decimal
    top_ev_floor: Decimal
    min_ev_floor: Decimal
    max_total_drag: Decimal
    reason_codes: tuple[str, ...]
    reason_code_counts: tuple[ResearchMarketFeeSpreadResolutionEvFloorReasonCodeCount, ...]
    rows: tuple[ResearchMarketFeeSpreadResolutionEvFloorRow, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchMarketFeeSpreadResolutionEvFloorReport, "report")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_label("config_version", self.config_version)
        _require_status("status", self.status)
        for field_name in (
            "input_count",
            "row_count",
            "pass_count",
            "watch_count",
            "block_count",
            "max_total_drag",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in ("average_ev_floor", "top_ev_floor", "min_ev_floor"):
            object.__setattr__(
                self,
                field_name,
                _require_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        _validate_report_consistency(self)
        _require_hard_flags("report", self)
        _reject_unsafe_public_payload("report", self)
        if self.derived_validation_digest == "":
            object.__setattr__(
                self,
                "derived_validation_digest",
                _report_derived_validation_digest(self),
            )
        else:
            _require_sha256_digest(
                "derived_validation_digest",
                self.derived_validation_digest,
            )
            if self.derived_validation_digest != _report_derived_validation_digest(self):
                raise ValueError(
                    "derived_validation_digest does not match public payload",
                )

    @property
    def public_payload(self) -> dict[str, Any]:
        return research_market_fee_spread_resolution_ev_floor_report_payload(self)


def build_research_market_fee_spread_resolution_ev_floor_report(
    inputs: Iterable[ResearchMarketFeeSpreadResolutionEvFloorInput],
    *,
    config: ResearchMarketFeeSpreadResolutionEvFloorConfig,
    generated_at: datetime,
) -> ResearchMarketFeeSpreadResolutionEvFloorReport:
    if type(config) is not ResearchMarketFeeSpreadResolutionEvFloorConfig:
        raise ValueError(
            "config must be a ResearchMarketFeeSpreadResolutionEvFloorConfig",
        )
    generated_at = _as_utc("generated_at", generated_at)
    _require_hard_flags("config", config)
    normalized = _normalize_inputs(inputs)
    for value in normalized:
        if value.observed_at > generated_at:
            raise ValueError("observed_at must not be after generated_at")
    keyed_inputs = tuple(
        sorted(
            (
                (
                    _private_digest(value.private_research_ref),
                    value,
                )
                for value in normalized
            ),
            key=lambda item: item[0],
        ),
    )
    rows = tuple(
        sorted(
            (
                _row_from_input(
                    value,
                    config=config,
                    public_row_ref=_public_row_ref(index),
                )
                for index, (_, value) in enumerate(keyed_inputs, start=1)
            ),
            key=_row_sort_key,
        ),
    )
    return ResearchMarketFeeSpreadResolutionEvFloorReport(
        generated_at=generated_at,
        config_version=config.config_version,
        status=_report_status(rows),
        input_count=_count_decimal(len(normalized)),
        row_count=_count_decimal(len(rows)),
        pass_count=_status_count(rows, PASS_STATUS),
        watch_count=_status_count(rows, WATCH_STATUS),
        block_count=_status_count(rows, BLOCK_STATUS),
        average_ev_floor=_average_row_decimal(rows, "ev_floor"),
        top_ev_floor=_max_row_decimal(rows, "ev_floor"),
        min_ev_floor=_min_row_decimal(rows, "ev_floor"),
        max_total_drag=_max_row_decimal(rows, "total_fee_spread_resolution_drag"),
        reason_codes=_report_reason_codes(rows),
        reason_code_counts=_report_reason_code_counts(rows),
        rows=rows,
    )


def research_market_fee_spread_resolution_ev_floor_report_payload(
    report: ResearchMarketFeeSpreadResolutionEvFloorReport,
) -> dict[str, Any]:
    if type(report) is not ResearchMarketFeeSpreadResolutionEvFloorReport:
        raise ValueError(
            "report must be a ResearchMarketFeeSpreadResolutionEvFloorReport",
        )
    _require_hard_flags("report", report)
    _reject_unsafe_public_payload("report", report)
    payload = _json_value(report)
    if type(payload) is not dict:
        raise ValueError("report must serialize to a JSON object")
    validate_research_market_fee_spread_resolution_ev_floor_report_payload(payload)
    return payload


def validate_research_market_fee_spread_resolution_ev_floor_report_payload(
    payload: dict[str, Any],
) -> dict[str, Any]:
    if type(payload) is not dict:
        raise ValueError("payload must be a dict")
    _require_payload_hard_flags(payload)
    _reject_unsafe_public_payload("payload", payload)
    provided_digest = payload.get("derived_validation_digest")
    _require_sha256_digest("derived_validation_digest", provided_digest)
    if provided_digest != _payload_derived_validation_digest(payload):
        raise ValueError("derived_validation_digest does not match public payload")
    return payload


def _row_from_input(
    value: ResearchMarketFeeSpreadResolutionEvFloorInput,
    *,
    config: ResearchMarketFeeSpreadResolutionEvFloorConfig,
    public_row_ref: str,
) -> ResearchMarketFeeSpreadResolutionEvFloorRow:
    spread_cost_ratio = _quantize_decimal(value.spread_width_ratio / TWO)
    total_drag = _quantize_decimal(
        value.fee_drag_ratio
        + spread_cost_ratio
        + value.resolution_friction_ratio
        + value.resolution_uncertainty_ratio,
    )
    ev_floor = _quantize_decimal(value.gross_expected_value_edge - total_drag)
    status = _ev_floor_status(
        ev_floor=ev_floor,
        total_drag=total_drag,
        config=config,
    )
    return ResearchMarketFeeSpreadResolutionEvFloorRow(
        public_row_ref=public_row_ref,
        observed_at=value.observed_at,
        gross_expected_value_edge=value.gross_expected_value_edge,
        fee_drag_ratio=value.fee_drag_ratio,
        spread_width_ratio=value.spread_width_ratio,
        spread_cost_ratio=spread_cost_ratio,
        resolution_friction_ratio=value.resolution_friction_ratio,
        resolution_uncertainty_ratio=value.resolution_uncertainty_ratio,
        total_fee_spread_resolution_drag=total_drag,
        ev_floor=ev_floor,
        status=status,
        reason_codes=_row_reason_codes(
            value.reason_codes,
            status=status,
            ev_floor=ev_floor,
            fee_drag_ratio=value.fee_drag_ratio,
            spread_cost_ratio=spread_cost_ratio,
            resolution_friction_ratio=value.resolution_friction_ratio,
            resolution_uncertainty_ratio=value.resolution_uncertainty_ratio,
            total_drag=total_drag,
            config=config,
        ),
    )


def _ev_floor_status(
    *,
    ev_floor: Decimal,
    total_drag: Decimal,
    config: ResearchMarketFeeSpreadResolutionEvFloorConfig,
) -> str:
    if total_drag >= config.block_total_drag_threshold:
        return BLOCK_STATUS
    if ev_floor >= config.pass_ev_floor_threshold:
        return PASS_STATUS
    if ev_floor >= config.watch_ev_floor_threshold:
        return WATCH_STATUS
    return BLOCK_STATUS


def _row_reason_codes(
    input_reason_codes: tuple[str, ...],
    *,
    status: str,
    ev_floor: Decimal,
    fee_drag_ratio: Decimal,
    spread_cost_ratio: Decimal,
    resolution_friction_ratio: Decimal,
    resolution_uncertainty_ratio: Decimal,
    total_drag: Decimal,
    config: ResearchMarketFeeSpreadResolutionEvFloorConfig,
) -> tuple[str, ...]:
    reason_codes = [f"input_{reason_code}" for reason_code in input_reason_codes]
    if ev_floor > ZERO:
        reason_codes.append("ev_floor_positive_floor")
    else:
        reason_codes.append("ev_floor_non_positive_floor")
    if fee_drag_ratio > ZERO:
        reason_codes.append("ev_floor_fee_drag_applied")
    if spread_cost_ratio > ZERO:
        reason_codes.append("ev_floor_spread_drag_applied")
    if resolution_friction_ratio > ZERO:
        reason_codes.append("ev_floor_resolution_friction_applied")
    if resolution_uncertainty_ratio > ZERO:
        reason_codes.append("ev_floor_resolution_uncertainty_applied")
    if total_drag >= config.block_total_drag_threshold:
        reason_codes.append("ev_floor_total_drag_block")
    if ev_floor < config.watch_ev_floor_threshold:
        reason_codes.append("ev_floor_below_watch_floor")
    reason_codes.append(f"ev_floor_status_{status}")
    return _normalize_reason_codes("reason_codes", tuple(reason_codes))


def _normalize_inputs(
    inputs: Iterable[ResearchMarketFeeSpreadResolutionEvFloorInput],
) -> tuple[ResearchMarketFeeSpreadResolutionEvFloorInput, ...]:
    if isinstance(inputs, (str, bytes)) or not isinstance(inputs, Iterable):
        raise ValueError("inputs must be an iterable")
    normalized = tuple(inputs)
    for value in normalized:
        if type(value) is not ResearchMarketFeeSpreadResolutionEvFloorInput:
            raise ValueError(
                "inputs must contain ResearchMarketFeeSpreadResolutionEvFloorInput",
            )
        _require_hard_flags("input", value)
    return normalized


def _normalize_rows(
    rows: Iterable[ResearchMarketFeeSpreadResolutionEvFloorRow],
) -> tuple[ResearchMarketFeeSpreadResolutionEvFloorRow, ...]:
    if isinstance(rows, (str, bytes)) or not isinstance(rows, Iterable):
        raise ValueError("rows must be an iterable")
    normalized = tuple(rows)
    for row in normalized:
        if type(row) is not ResearchMarketFeeSpreadResolutionEvFloorRow:
            raise ValueError("rows must contain ResearchMarketFeeSpreadResolutionEvFloorRow")
        _require_hard_flags("row", row)
    return tuple(sorted(normalized, key=_row_sort_key))


def _normalize_reason_code_counts(
    counts: Iterable[ResearchMarketFeeSpreadResolutionEvFloorReasonCodeCount],
) -> tuple[ResearchMarketFeeSpreadResolutionEvFloorReasonCodeCount, ...]:
    if isinstance(counts, (str, bytes)) or not isinstance(counts, Iterable):
        raise ValueError("reason_code_counts must be an iterable")
    normalized = tuple(counts)
    for count in normalized:
        if type(count) is not ResearchMarketFeeSpreadResolutionEvFloorReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "ResearchMarketFeeSpreadResolutionEvFloorReasonCodeCount",
            )
        _require_hard_flags("reason_count", count)
    return tuple(sorted(normalized, key=lambda item: (-item.count, item.reason_code)))


def _validate_row_consistency(row: ResearchMarketFeeSpreadResolutionEvFloorRow) -> None:
    expected_spread_cost = _quantize_decimal(row.spread_width_ratio / TWO)
    if row.spread_cost_ratio != expected_spread_cost:
        raise ValueError("spread_cost_ratio must match spread_width_ratio")
    expected_total_drag = _quantize_decimal(
        row.fee_drag_ratio
        + row.spread_cost_ratio
        + row.resolution_friction_ratio
        + row.resolution_uncertainty_ratio,
    )
    if row.total_fee_spread_resolution_drag != expected_total_drag:
        raise ValueError("total_fee_spread_resolution_drag must match components")
    if row.ev_floor != _quantize_decimal(
        row.gross_expected_value_edge - row.total_fee_spread_resolution_drag,
    ):
        raise ValueError("ev_floor must match gross edge minus total drag")
    if f"ev_floor_status_{row.status}" not in row.reason_codes:
        raise ValueError("status must match reason_codes")


def _validate_report_consistency(
    report: ResearchMarketFeeSpreadResolutionEvFloorReport,
) -> None:
    if report.input_count != report.row_count:
        raise ValueError("input_count must match row_count")
    if report.row_count != _count_decimal(len(report.rows)):
        raise ValueError("row_count must match rows")
    if report.pass_count + report.watch_count + report.block_count != report.row_count:
        raise ValueError("status counts must match row_count")
    if report.average_ev_floor != _average_row_decimal(report.rows, "ev_floor"):
        raise ValueError("average_ev_floor must match rows")
    if report.top_ev_floor != _max_row_decimal(report.rows, "ev_floor"):
        raise ValueError("top_ev_floor must match rows")
    if report.min_ev_floor != _min_row_decimal(report.rows, "ev_floor"):
        raise ValueError("min_ev_floor must match rows")
    if report.max_total_drag != _max_row_decimal(
        report.rows,
        "total_fee_spread_resolution_drag",
    ):
        raise ValueError("max_total_drag must match rows")
    if report.status != _report_status(report.rows):
        raise ValueError("status must match rows")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")
    if report.reason_code_counts != _report_reason_code_counts(report.rows):
        raise ValueError("reason_code_counts must match rows")


def _report_status(rows: tuple[ResearchMarketFeeSpreadResolutionEvFloorRow, ...]) -> str:
    if not rows:
        return BLOCK_STATUS
    if any(row.status == BLOCK_STATUS for row in rows):
        return BLOCK_STATUS
    if any(row.status == WATCH_STATUS for row in rows):
        return WATCH_STATUS
    return PASS_STATUS


def _report_reason_codes(
    rows: tuple[ResearchMarketFeeSpreadResolutionEvFloorRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return ("ev_floor_no_inputs",)
    reason_codes: list[str] = []
    for row in rows:
        reason_codes.extend(row.reason_codes)
    return _normalize_reason_codes("reason_codes", tuple(reason_codes))


def _report_reason_code_counts(
    rows: tuple[ResearchMarketFeeSpreadResolutionEvFloorRow, ...],
) -> tuple[ResearchMarketFeeSpreadResolutionEvFloorReasonCodeCount, ...]:
    counts: dict[str, Decimal] = {}
    for reason_code in _report_reason_codes(rows):
        counts[reason_code] = ZERO
    if not rows:
        counts["ev_floor_no_inputs"] = ONE
    for row in rows:
        for reason_code in row.reason_codes:
            counts[reason_code] = _quantize_decimal(counts.get(reason_code, ZERO) + ONE)
    return tuple(
        sorted(
            (
                ResearchMarketFeeSpreadResolutionEvFloorReasonCodeCount(
                    reason_code=reason_code,
                    count=count,
                )
                for reason_code, count in counts.items()
            ),
            key=lambda item: (-item.count, item.reason_code),
        ),
    )


def _status_count(
    rows: tuple[ResearchMarketFeeSpreadResolutionEvFloorRow, ...],
    status: str,
) -> Decimal:
    return _count_decimal(sum(1 for row in rows if row.status == status))


def _max_row_decimal(
    rows: tuple[ResearchMarketFeeSpreadResolutionEvFloorRow, ...],
    field_name: str,
) -> Decimal:
    if not rows:
        return ZERO
    return max(getattr(row, field_name) for row in rows)


def _min_row_decimal(
    rows: tuple[ResearchMarketFeeSpreadResolutionEvFloorRow, ...],
    field_name: str,
) -> Decimal:
    if not rows:
        return ZERO
    return min(getattr(row, field_name) for row in rows)


def _average_row_decimal(
    rows: tuple[ResearchMarketFeeSpreadResolutionEvFloorRow, ...],
    field_name: str,
) -> Decimal:
    if not rows:
        return ZERO
    total = ZERO
    for row in rows:
        total = _quantize_decimal(total + getattr(row, field_name))
    with localcontext(DECIMAL_CONTEXT):
        return _quantize_decimal(total / Decimal(len(rows)))


def _count_decimal(value: int) -> Decimal:
    return _quantize_decimal(Decimal(value))


def _require_ratio_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_nonnegative_decimal(field_name, value)
    if normalized > ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return normalized


def _require_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return _quantize_decimal(value)


def _quantize_decimal(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(QUANTUM)


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be UTC-aware")
    return value.astimezone(UTC)


def _require_private_ref(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")


def _require_public_label(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")
    if len(value) > 128:
        raise ValueError(f"{field_name} must be at most 128 characters")
    allowed = set("ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789_.-")
    if any(character not in allowed for character in value):
        raise ValueError(f"{field_name} must be a public label")
    if _contains_unsafe_public_fragment(value):
        raise ValueError(f"{field_name} has unsafe public payload")


def _require_reason_code(field_name: str, value: object) -> None:
    _require_public_label(field_name, value)
    if not value.replace("_", "-").replace(".", "-").replace("-", "").isalnum():
        raise ValueError(f"{field_name} must be a reason code")


def _normalize_reason_codes(
    field_name: str,
    values: Iterable[str],
    *,
    allow_empty: bool = False,
) -> tuple[str, ...]:
    if isinstance(values, (str, bytes)) or not isinstance(values, Iterable):
        raise ValueError(f"{field_name} must be an iterable")
    normalized = tuple(sorted(set(values)))
    if not normalized and not allow_empty:
        raise ValueError(f"{field_name} must not be empty")
    for value in normalized:
        _require_reason_code(field_name, value)
    return normalized


def _require_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in EV_FLOOR_STATUSES:
        raise ValueError(f"{field_name} must be pass, watch, or block")


def _require_sha256_digest(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a sha256 digest")
    if len(value) != 64 or any(character not in "0123456789abcdef" for character in value):
        raise ValueError(f"{field_name} must be a lowercase sha256 digest")


def _require_exact_type(value: object, expected_type: type[object], field_name: str) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{field_name} must be exactly {expected_type.__name__}")


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if getattr(value, field_name, None) is not True:
            raise ValueError(f"{field_name} must be True for {label}")


def _require_payload_hard_flags(payload: Mapping[str, Any]) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if payload.get(field_name) is not True:
            raise ValueError(f"{field_name} must be True for payload")


def _row_sort_key(
    row: ResearchMarketFeeSpreadResolutionEvFloorRow,
) -> tuple[Decimal, Decimal, str]:
    return (
        STATUS_RANK[row.status],
        -row.ev_floor,
        row.public_row_ref,
    )


def _public_row_ref(index: int) -> str:
    return f"ev-floor-row-{index:06d}"


def _private_digest(value: str) -> str:
    canonical = json.dumps(
        {"ref": value},
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    )
    return sha256(canonical.encode("utf-8")).hexdigest()


def _report_values_without_digest(
    report: ResearchMarketFeeSpreadResolutionEvFloorReport,
) -> dict[str, Any]:
    values = asdict(report)
    values.pop("derived_validation_digest", None)
    return values


def _report_derived_validation_digest(
    report: ResearchMarketFeeSpreadResolutionEvFloorReport,
) -> str:
    payload = _json_value(_report_values_without_digest(report))
    _reject_unsafe_public_payload("digest_payload", payload)
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return sha256(canonical.encode("utf-8")).hexdigest()


def _payload_derived_validation_digest(payload: Mapping[str, Any]) -> str:
    digest_payload = dict(payload)
    digest_payload.pop("derived_validation_digest", None)
    _reject_unsafe_public_payload("digest_payload", digest_payload)
    canonical = json.dumps(digest_payload, sort_keys=True, separators=(",", ":"))
    return sha256(canonical.encode("utf-8")).hexdigest()


def _json_value(value: Any) -> Any:
    if value is None:
        return None
    if is_dataclass(value) and not isinstance(value, type):
        return _json_value(asdict(value))
    if type(value) is Decimal:
        if not value.is_finite():
            raise ValueError("Decimal payload value must be finite")
        return str(value)
    if type(value) is datetime:
        return _as_utc("datetime payload value", value).isoformat()
    if type(value) is bool or type(value) is str:
        return value
    if type(value) is int or isinstance(value, float):
        raise ValueError("numeric payload values must be Decimal strings")
    if isinstance(value, Mapping):
        ready: dict[str, Any] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            ready[key] = _json_value(item)
        return ready
    if isinstance(value, (list, tuple)):
        return [_json_value(item) for item in value]
    raise ValueError("payload value is not JSON serializable")


def _reject_unsafe_public_payload(
    label: str,
    value: object,
    path: str = "",
) -> None:
    current_path = path or label
    if is_dataclass(value) and not isinstance(value, type):
        for field in fields(value):
            _reject_unsafe_public_key(field.name, current_path)
            _reject_unsafe_public_payload(
                label,
                getattr(value, field.name),
                field.name if not path else f"{path}.{field.name}",
            )
        return
    if isinstance(value, Mapping):
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            _reject_unsafe_public_key(key, current_path)
            _reject_unsafe_public_payload(
                label,
                item,
                key if not path else f"{path}.{key}",
            )
        return
    if isinstance(value, (list, tuple)):
        for index, item in enumerate(value):
            _reject_unsafe_public_payload(label, item, f"{current_path}[{index}]")
        return
    if type(value) is str:
        _reject_unsafe_public_string(current_path, value)
        return
    if (
        value is None
        or type(value) is bool
        or type(value) is Decimal
        or type(value) is datetime
    ):
        return
    raise ValueError(f"{current_path} is not a supported public payload value")


def _reject_unsafe_public_key(key: str, path: str) -> None:
    if _contains_unsafe_public_fragment(key):
        raise ValueError(f"{path}.{key} has unsafe public payload")


def _reject_unsafe_public_string(field_name: str, value: str) -> None:
    if _contains_unsafe_public_fragment(value):
        raise ValueError(f"{field_name} has unsafe public payload")


def _contains_unsafe_public_fragment(value: str) -> bool:
    lowered = value.lower()
    return any(fragment in lowered for fragment in UNSAFE_PUBLIC_FRAGMENTS)
