"""Pure report-only fee/spread/depth frontier reducer."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import asdict, dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, localcontext
from hashlib import sha256
import json
from typing import Any


__all__ = (
    "FEE_SPREAD_DEPTH_FRONTIER_STATUSES",
    "DEFAULT_RESEARCH_MARKET_FEE_SPREAD_DEPTH_FRONTIER_REPORT_CONFIG_VERSION",
    "ResearchMarketFeeSpreadDepthFrontierConfig",
    "ResearchMarketFeeSpreadDepthFrontierInput",
    "ResearchMarketFeeSpreadDepthFrontierReasonCodeCount",
    "ResearchMarketFeeSpreadDepthFrontierReport",
    "ResearchMarketFeeSpreadDepthFrontierRow",
    "build_research_market_fee_spread_depth_frontier_report",
    "research_market_fee_spread_depth_frontier_report_payload",
    "validate_research_market_fee_spread_depth_frontier_report_payload",
)


DEFAULT_RESEARCH_MARKET_FEE_SPREAD_DEPTH_FRONTIER_REPORT_CONFIG_VERSION = (
    "research-market-fee-spread-depth-frontier-report-v1"
)
PASS_STATUS = "pass"
WATCH_STATUS = "watch"
BLOCK_STATUS = "block"
FEE_SPREAD_DEPTH_FRONTIER_STATUSES = (PASS_STATUS, WATCH_STATUS, BLOCK_STATUS)
STATUS_RANK = {
    BLOCK_STATUS: Decimal("0.000000"),
    WATCH_STATUS: Decimal("1.000000"),
    PASS_STATUS: Decimal("2.000000"),
}
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
SEVEN = Decimal("7.000000")
QUANTUM = Decimal("0.000001")
DECIMAL_CONTEXT = Context(prec=64)


def _join_parts(*parts: str) -> str:
    return "".join(parts)


UNSAFE_PUBLIC_FRAGMENTS = (
    _join_parts("ra", "w"),
    _join_parts("can", "didate", "_", "id"),
    _join_parts("ma", "rket", "_", "id"),
    _join_parts("ma", "rket", "_", "sl", "ug"),
    _join_parts("ques", "tion"),
    _join_parts("ur", "l"),
    _join_parts("tex", "t"),
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
    "://",
    "?",
    "@",
    "=",
)


@dataclass(frozen=True)
class ResearchMarketFeeSpreadDepthFrontierConfig:
    config_version: str = (
        DEFAULT_RESEARCH_MARKET_FEE_SPREAD_DEPTH_FRONTIER_REPORT_CONFIG_VERSION
    )
    maximum_pass_fee_drag_ratio: Decimal = Decimal("0.010000")
    maximum_watch_fee_drag_ratio: Decimal = Decimal("0.030000")
    maximum_pass_spread_width_ratio: Decimal = Decimal("0.030000")
    maximum_watch_spread_width_ratio: Decimal = Decimal("0.080000")
    minimum_pass_total_depth_band: Decimal = Decimal("1000.000000")
    minimum_watch_total_depth_band: Decimal = Decimal("250.000000")
    minimum_pass_slippage_cushion_ratio: Decimal = Decimal("0.050000")
    minimum_watch_slippage_cushion_ratio: Decimal = Decimal("0.020000")
    maximum_pass_book_age_seconds: Decimal = Decimal("120.000000")
    maximum_watch_book_age_seconds: Decimal = Decimal("600.000000")
    maximum_pass_volatility_ratio: Decimal = Decimal("0.100000")
    maximum_watch_volatility_ratio: Decimal = Decimal("0.250000")
    maximum_pass_settlement_friction_ratio: Decimal = Decimal("0.050000")
    maximum_watch_settlement_friction_ratio: Decimal = Decimal("0.150000")
    minimum_pass_frontier_score: Decimal = Decimal("0.750000")
    minimum_watch_frontier_score: Decimal = Decimal("0.450000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchMarketFeeSpreadDepthFrontierConfig, "config")
        _require_public_label("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_MARKET_FEE_SPREAD_DEPTH_FRONTIER_REPORT_CONFIG_VERSION
        ):
            raise ValueError("config_version must match supported value")
        for field_name in (
            "maximum_pass_fee_drag_ratio",
            "maximum_watch_fee_drag_ratio",
            "maximum_pass_spread_width_ratio",
            "maximum_watch_spread_width_ratio",
            "minimum_pass_slippage_cushion_ratio",
            "minimum_watch_slippage_cushion_ratio",
            "maximum_pass_volatility_ratio",
            "maximum_watch_volatility_ratio",
            "maximum_pass_settlement_friction_ratio",
            "maximum_watch_settlement_friction_ratio",
            "minimum_pass_frontier_score",
            "minimum_watch_frontier_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "minimum_pass_total_depth_band",
            "minimum_watch_total_depth_band",
            "maximum_pass_book_age_seconds",
            "maximum_watch_book_age_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_positive_decimal(field_name, getattr(self, field_name)),
            )
        if self.maximum_pass_fee_drag_ratio > self.maximum_watch_fee_drag_ratio:
            raise ValueError("maximum_pass_fee_drag_ratio must not exceed watch")
        if self.maximum_pass_spread_width_ratio > self.maximum_watch_spread_width_ratio:
            raise ValueError("maximum_pass_spread_width_ratio must not exceed watch")
        if self.minimum_pass_total_depth_band < self.minimum_watch_total_depth_band:
            raise ValueError("minimum_pass_total_depth_band must be at least watch")
        if (
            self.minimum_pass_slippage_cushion_ratio
            < self.minimum_watch_slippage_cushion_ratio
        ):
            raise ValueError(
                "minimum_pass_slippage_cushion_ratio must be at least watch",
            )
        if self.maximum_pass_book_age_seconds > self.maximum_watch_book_age_seconds:
            raise ValueError("maximum_pass_book_age_seconds must not exceed watch")
        if self.maximum_pass_volatility_ratio > self.maximum_watch_volatility_ratio:
            raise ValueError("maximum_pass_volatility_ratio must not exceed watch")
        if (
            self.maximum_pass_settlement_friction_ratio
            > self.maximum_watch_settlement_friction_ratio
        ):
            raise ValueError(
                "maximum_pass_settlement_friction_ratio must not exceed watch",
            )
        if self.minimum_pass_frontier_score < self.minimum_watch_frontier_score:
            raise ValueError("minimum_pass_frontier_score must be at least watch")
        _require_hard_flags("config", self)
        _reject_unsafe_public_payload("config", self)


@dataclass(frozen=True)
class ResearchMarketFeeSpreadDepthFrontierInput:
    private_item_ref: str
    private_group_ref: str
    book_observed_at: datetime
    fee_drag_ratio: Decimal
    spread_width_ratio: Decimal
    near_depth_band: Decimal
    mid_depth_band: Decimal
    far_depth_band: Decimal
    slippage_cushion_ratio: Decimal
    volatility_ratio: Decimal
    settlement_friction_ratio: Decimal
    reason_codes: tuple[str, ...] = ()
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchMarketFeeSpreadDepthFrontierInput, "input")
        for field_name in ("private_item_ref", "private_group_ref"):
            _require_private_ref(field_name, getattr(self, field_name))
        object.__setattr__(
            self,
            "book_observed_at",
            _as_utc("book_observed_at", self.book_observed_at),
        )
        for field_name in (
            "fee_drag_ratio",
            "spread_width_ratio",
            "slippage_cushion_ratio",
            "volatility_ratio",
            "settlement_friction_ratio",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in ("near_depth_band", "mid_depth_band", "far_depth_band"):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, allow_empty=True),
        )
        _require_hard_flags("input", self)


@dataclass(frozen=True)
class ResearchMarketFeeSpreadDepthFrontierRow:
    public_row_ref: str
    book_observed_at: datetime
    book_age_seconds: Decimal
    fee_drag_ratio: Decimal
    fee_drag_score: Decimal
    spread_width_ratio: Decimal
    spread_width_score: Decimal
    near_depth_band: Decimal
    mid_depth_band: Decimal
    far_depth_band: Decimal
    total_depth_band: Decimal
    depth_band_score: Decimal
    slippage_cushion_ratio: Decimal
    slippage_cushion_score: Decimal
    volatility_ratio: Decimal
    volatility_score: Decimal
    settlement_friction_ratio: Decimal
    settlement_friction_score: Decimal
    book_age_score: Decimal
    frontier_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchMarketFeeSpreadDepthFrontierRow, "row")
        _require_public_label("public_row_ref", self.public_row_ref)
        object.__setattr__(
            self,
            "book_observed_at",
            _as_utc("book_observed_at", self.book_observed_at),
        )
        for field_name in (
            "book_age_seconds",
            "near_depth_band",
            "mid_depth_band",
            "far_depth_band",
            "total_depth_band",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "fee_drag_ratio",
            "fee_drag_score",
            "spread_width_ratio",
            "spread_width_score",
            "depth_band_score",
            "slippage_cushion_ratio",
            "slippage_cushion_score",
            "volatility_ratio",
            "volatility_score",
            "settlement_friction_ratio",
            "settlement_friction_score",
            "book_age_score",
            "frontier_score",
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
class ResearchMarketFeeSpreadDepthFrontierReasonCodeCount:
    reason_code: str
    count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchMarketFeeSpreadDepthFrontierReasonCodeCount,
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
class ResearchMarketFeeSpreadDepthFrontierReport:
    generated_at: datetime
    config_version: str
    status: str
    input_count: Decimal
    row_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    high_fee_drag_count: Decimal
    wide_spread_count: Decimal
    thin_depth_count: Decimal
    low_slippage_cushion_count: Decimal
    stale_book_count: Decimal
    high_volatility_count: Decimal
    high_settlement_friction_count: Decimal
    average_frontier_score: Decimal
    min_total_depth_band: Decimal
    max_fee_drag_ratio: Decimal
    max_spread_width_ratio: Decimal
    min_slippage_cushion_ratio: Decimal
    max_book_age_seconds: Decimal
    max_volatility_ratio: Decimal
    max_settlement_friction_ratio: Decimal
    reason_codes: tuple[str, ...]
    reason_code_counts: tuple[ResearchMarketFeeSpreadDepthFrontierReasonCodeCount, ...]
    rows: tuple[ResearchMarketFeeSpreadDepthFrontierRow, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchMarketFeeSpreadDepthFrontierReport, "report")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_label("config_version", self.config_version)
        _require_status("status", self.status)
        for field_name in (
            "input_count",
            "row_count",
            "pass_count",
            "watch_count",
            "block_count",
            "high_fee_drag_count",
            "wide_spread_count",
            "thin_depth_count",
            "low_slippage_cushion_count",
            "stale_book_count",
            "high_volatility_count",
            "high_settlement_friction_count",
            "min_total_depth_band",
            "max_book_age_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "average_frontier_score",
            "max_fee_drag_ratio",
            "max_spread_width_ratio",
            "min_slippage_cushion_ratio",
            "max_volatility_ratio",
            "max_settlement_friction_ratio",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
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


def build_research_market_fee_spread_depth_frontier_report(
    inputs: Iterable[ResearchMarketFeeSpreadDepthFrontierInput],
    *,
    config: ResearchMarketFeeSpreadDepthFrontierConfig,
    generated_at: datetime,
) -> ResearchMarketFeeSpreadDepthFrontierReport:
    if type(config) is not ResearchMarketFeeSpreadDepthFrontierConfig:
        raise ValueError("config must be a ResearchMarketFeeSpreadDepthFrontierConfig")
    generated_at = _as_utc("generated_at", generated_at)
    _require_hard_flags("config", config)
    normalized = _normalize_inputs(inputs)
    keyed_inputs = tuple(
        sorted(
            (
                (
                    _private_digest(value.private_item_ref, value.private_group_ref),
                    value,
                )
                for value in normalized
            ),
            key=lambda item: item[0],
        ),
    )
    keyed_rows = tuple(
        sorted(
            (
                (
                    private_digest,
                    _row_from_input(
                        value,
                        config=config,
                        generated_at=generated_at,
                        public_row_ref=_public_row_ref(index),
                    ),
                )
                for index, (private_digest, value) in enumerate(keyed_inputs, start=1)
            ),
            key=lambda item: _row_sort_key(item[1]),
        ),
    )
    rows = tuple(row for _, row in keyed_rows)
    return ResearchMarketFeeSpreadDepthFrontierReport(
        generated_at=generated_at,
        config_version=config.config_version,
        status=_report_status(rows),
        input_count=_count_decimal(len(normalized)),
        row_count=_count_decimal(len(rows)),
        pass_count=_status_count(rows, PASS_STATUS),
        watch_count=_status_count(rows, WATCH_STATUS),
        block_count=_status_count(rows, BLOCK_STATUS),
        high_fee_drag_count=_non_pass_reason_count(rows, "frontier_fee_drag"),
        wide_spread_count=_non_pass_reason_count(rows, "frontier_spread_width"),
        thin_depth_count=_non_pass_reason_count(rows, "frontier_depth_band"),
        low_slippage_cushion_count=_non_pass_reason_count(
            rows,
            "frontier_slippage_cushion",
        ),
        stale_book_count=_non_pass_reason_count(rows, "frontier_book_age"),
        high_volatility_count=_non_pass_reason_count(rows, "frontier_volatility"),
        high_settlement_friction_count=_non_pass_reason_count(
            rows,
            "frontier_settlement_friction",
        ),
        average_frontier_score=_average_row_decimal(rows, "frontier_score"),
        min_total_depth_band=_min_row_decimal(rows, "total_depth_band"),
        max_fee_drag_ratio=_max_row_decimal(rows, "fee_drag_ratio"),
        max_spread_width_ratio=_max_row_decimal(rows, "spread_width_ratio"),
        min_slippage_cushion_ratio=_min_ratio_row_decimal(
            rows,
            "slippage_cushion_ratio",
        ),
        max_book_age_seconds=_max_row_decimal(rows, "book_age_seconds"),
        max_volatility_ratio=_max_row_decimal(rows, "volatility_ratio"),
        max_settlement_friction_ratio=_max_row_decimal(
            rows,
            "settlement_friction_ratio",
        ),
        reason_codes=_report_reason_codes(rows),
        reason_code_counts=_report_reason_code_counts(rows),
        rows=rows,
    )


def research_market_fee_spread_depth_frontier_report_payload(
    report: ResearchMarketFeeSpreadDepthFrontierReport,
) -> dict[str, Any]:
    if type(report) is not ResearchMarketFeeSpreadDepthFrontierReport:
        raise ValueError("report must be a ResearchMarketFeeSpreadDepthFrontierReport")
    _require_hard_flags("report", report)
    _reject_unsafe_public_payload("report", report)
    payload = _json_value(report)
    if type(payload) is not dict:
        raise ValueError("report must serialize to a JSON object")
    validate_research_market_fee_spread_depth_frontier_report_payload(payload)
    return payload


def validate_research_market_fee_spread_depth_frontier_report_payload(
    payload: dict[str, Any],
) -> dict[str, Any]:
    if type(payload) is not dict:
        raise ValueError("payload must be a dict")
    _require_payload_hard_flags(payload)
    _reject_unsafe_public_payload("payload", payload)
    _validate_public_payload_schema(payload)
    provided_digest = payload.get("derived_validation_digest")
    _require_sha256_digest("derived_validation_digest", provided_digest)
    if provided_digest != _payload_derived_validation_digest(payload):
        raise ValueError("derived_validation_digest does not match public payload")
    return payload


def _row_from_input(
    value: ResearchMarketFeeSpreadDepthFrontierInput,
    *,
    config: ResearchMarketFeeSpreadDepthFrontierConfig,
    generated_at: datetime,
    public_row_ref: str,
) -> ResearchMarketFeeSpreadDepthFrontierRow:
    book_age_seconds = _seconds_between(
        generated_at,
        value.book_observed_at,
        "book_observed_at",
    )
    total_depth_band = _quantize_decimal(
        value.near_depth_band + value.mid_depth_band + value.far_depth_band,
    )
    fee_drag_score = _score_for_maximum(
        value.fee_drag_ratio,
        config.maximum_pass_fee_drag_ratio,
        config.maximum_watch_fee_drag_ratio,
    )
    spread_width_score = _score_for_maximum(
        value.spread_width_ratio,
        config.maximum_pass_spread_width_ratio,
        config.maximum_watch_spread_width_ratio,
    )
    depth_band_score = _score_for_minimum(
        total_depth_band,
        config.minimum_pass_total_depth_band,
        config.minimum_watch_total_depth_band,
    )
    slippage_cushion_score = _score_for_minimum(
        value.slippage_cushion_ratio,
        config.minimum_pass_slippage_cushion_ratio,
        config.minimum_watch_slippage_cushion_ratio,
    )
    book_age_score = _score_for_maximum(
        book_age_seconds,
        config.maximum_pass_book_age_seconds,
        config.maximum_watch_book_age_seconds,
    )
    volatility_score = _score_for_maximum(
        value.volatility_ratio,
        config.maximum_pass_volatility_ratio,
        config.maximum_watch_volatility_ratio,
    )
    settlement_friction_score = _score_for_maximum(
        value.settlement_friction_ratio,
        config.maximum_pass_settlement_friction_ratio,
        config.maximum_watch_settlement_friction_ratio,
    )
    frontier_score = _frontier_score(
        fee_drag_score=fee_drag_score,
        spread_width_score=spread_width_score,
        depth_band_score=depth_band_score,
        slippage_cushion_score=slippage_cushion_score,
        book_age_score=book_age_score,
        volatility_score=volatility_score,
        settlement_friction_score=settlement_friction_score,
    )
    component_statuses = (
        _status_for_maximum(
            value.fee_drag_ratio,
            config.maximum_pass_fee_drag_ratio,
            config.maximum_watch_fee_drag_ratio,
        ),
        _status_for_maximum(
            value.spread_width_ratio,
            config.maximum_pass_spread_width_ratio,
            config.maximum_watch_spread_width_ratio,
        ),
        _status_for_minimum(
            total_depth_band,
            config.minimum_pass_total_depth_band,
            config.minimum_watch_total_depth_band,
        ),
        _status_for_minimum(
            value.slippage_cushion_ratio,
            config.minimum_pass_slippage_cushion_ratio,
            config.minimum_watch_slippage_cushion_ratio,
        ),
        _status_for_maximum(
            book_age_seconds,
            config.maximum_pass_book_age_seconds,
            config.maximum_watch_book_age_seconds,
        ),
        _status_for_maximum(
            value.volatility_ratio,
            config.maximum_pass_volatility_ratio,
            config.maximum_watch_volatility_ratio,
        ),
        _status_for_maximum(
            value.settlement_friction_ratio,
            config.maximum_pass_settlement_friction_ratio,
            config.maximum_watch_settlement_friction_ratio,
        ),
    )
    status = _frontier_status(
        component_statuses=component_statuses,
        frontier_score=frontier_score,
        config=config,
    )
    return ResearchMarketFeeSpreadDepthFrontierRow(
        public_row_ref=public_row_ref,
        book_observed_at=value.book_observed_at,
        book_age_seconds=book_age_seconds,
        fee_drag_ratio=value.fee_drag_ratio,
        fee_drag_score=fee_drag_score,
        spread_width_ratio=value.spread_width_ratio,
        spread_width_score=spread_width_score,
        near_depth_band=value.near_depth_band,
        mid_depth_band=value.mid_depth_band,
        far_depth_band=value.far_depth_band,
        total_depth_band=total_depth_band,
        depth_band_score=depth_band_score,
        slippage_cushion_ratio=value.slippage_cushion_ratio,
        slippage_cushion_score=slippage_cushion_score,
        volatility_ratio=value.volatility_ratio,
        volatility_score=volatility_score,
        settlement_friction_ratio=value.settlement_friction_ratio,
        settlement_friction_score=settlement_friction_score,
        book_age_score=book_age_score,
        frontier_score=frontier_score,
        status=status,
        reason_codes=_row_reason_codes(
            value.reason_codes,
            status=status,
            fee_drag_status=component_statuses[0],
            spread_width_status=component_statuses[1],
            depth_band_status=component_statuses[2],
            slippage_cushion_status=component_statuses[3],
            book_age_status=component_statuses[4],
            volatility_status=component_statuses[5],
            settlement_friction_status=component_statuses[6],
        ),
    )


def _frontier_score(
    *,
    fee_drag_score: Decimal,
    spread_width_score: Decimal,
    depth_band_score: Decimal,
    slippage_cushion_score: Decimal,
    book_age_score: Decimal,
    volatility_score: Decimal,
    settlement_friction_score: Decimal,
) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return _quantize_decimal(
            (
                fee_drag_score
                + spread_width_score
                + depth_band_score
                + slippage_cushion_score
                + book_age_score
                + volatility_score
                + settlement_friction_score
            )
            / SEVEN,
        )


def _frontier_status(
    *,
    component_statuses: tuple[str, ...],
    frontier_score: Decimal,
    config: ResearchMarketFeeSpreadDepthFrontierConfig,
) -> str:
    if (
        BLOCK_STATUS in component_statuses
        or frontier_score < config.minimum_watch_frontier_score
    ):
        return BLOCK_STATUS
    if (
        WATCH_STATUS in component_statuses
        or frontier_score < config.minimum_pass_frontier_score
    ):
        return WATCH_STATUS
    return PASS_STATUS


def _row_reason_codes(
    input_reason_codes: tuple[str, ...],
    *,
    status: str,
    fee_drag_status: str,
    spread_width_status: str,
    depth_band_status: str,
    slippage_cushion_status: str,
    book_age_status: str,
    volatility_status: str,
    settlement_friction_status: str,
) -> tuple[str, ...]:
    reason_codes = [f"input_{reason_code}" for reason_code in input_reason_codes]
    reason_codes.extend(
        (
            f"frontier_status_{status}",
            f"frontier_fee_drag_{fee_drag_status}",
            f"frontier_spread_width_{spread_width_status}",
            f"frontier_depth_band_{depth_band_status}",
            f"frontier_slippage_cushion_{slippage_cushion_status}",
            f"frontier_book_age_{book_age_status}",
            f"frontier_volatility_{volatility_status}",
            f"frontier_settlement_friction_{settlement_friction_status}",
        ),
    )
    return _normalize_reason_codes("reason_codes", tuple(reason_codes))


def _score_for_maximum(value: Decimal, pass_value: Decimal, watch_value: Decimal) -> Decimal:
    if value <= pass_value:
        return ONE
    if value >= watch_value:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return _quantize_decimal((watch_value - value) / (watch_value - pass_value))


def _score_for_minimum(value: Decimal, pass_value: Decimal, watch_value: Decimal) -> Decimal:
    if value >= pass_value:
        return ONE
    if value <= watch_value:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return _quantize_decimal((value - watch_value) / (pass_value - watch_value))


def _status_for_maximum(value: Decimal, pass_value: Decimal, watch_value: Decimal) -> str:
    if value > watch_value:
        return BLOCK_STATUS
    if value > pass_value:
        return WATCH_STATUS
    return PASS_STATUS


def _status_for_minimum(value: Decimal, pass_value: Decimal, watch_value: Decimal) -> str:
    if value < watch_value:
        return BLOCK_STATUS
    if value < pass_value:
        return WATCH_STATUS
    return PASS_STATUS


def _normalize_inputs(
    inputs: Iterable[ResearchMarketFeeSpreadDepthFrontierInput],
) -> tuple[ResearchMarketFeeSpreadDepthFrontierInput, ...]:
    if isinstance(inputs, (str, bytes)) or not isinstance(inputs, Iterable):
        raise ValueError("inputs must be an iterable")
    normalized = tuple(inputs)
    for value in normalized:
        if type(value) is not ResearchMarketFeeSpreadDepthFrontierInput:
            raise ValueError(
                "inputs must contain ResearchMarketFeeSpreadDepthFrontierInput",
            )
        _require_hard_flags("input", value)
    return normalized


def _normalize_rows(
    rows: Iterable[ResearchMarketFeeSpreadDepthFrontierRow],
) -> tuple[ResearchMarketFeeSpreadDepthFrontierRow, ...]:
    if isinstance(rows, (str, bytes)) or not isinstance(rows, Iterable):
        raise ValueError("rows must be an iterable")
    normalized = tuple(rows)
    for row in normalized:
        if type(row) is not ResearchMarketFeeSpreadDepthFrontierRow:
            raise ValueError("rows must contain ResearchMarketFeeSpreadDepthFrontierRow")
        _require_hard_flags("row", row)
    return tuple(sorted(normalized, key=_row_sort_key))


def _normalize_reason_code_counts(
    counts: Iterable[ResearchMarketFeeSpreadDepthFrontierReasonCodeCount],
) -> tuple[ResearchMarketFeeSpreadDepthFrontierReasonCodeCount, ...]:
    if isinstance(counts, (str, bytes)) or not isinstance(counts, Iterable):
        raise ValueError("reason_code_counts must be an iterable")
    normalized = tuple(counts)
    for count in normalized:
        if type(count) is not ResearchMarketFeeSpreadDepthFrontierReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "ResearchMarketFeeSpreadDepthFrontierReasonCodeCount",
            )
        _require_hard_flags("reason_count", count)
    return tuple(sorted(normalized, key=lambda item: (-item.count, item.reason_code)))


def _validate_row_consistency(row: ResearchMarketFeeSpreadDepthFrontierRow) -> None:
    if f"frontier_status_{row.status}" not in row.reason_codes:
        raise ValueError("status must match reason_codes")
    if row.total_depth_band != _quantize_decimal(
        row.near_depth_band + row.mid_depth_band + row.far_depth_band,
    ):
        raise ValueError("total_depth_band must match depth bands")
    expected_frontier_score = _frontier_score(
        fee_drag_score=row.fee_drag_score,
        spread_width_score=row.spread_width_score,
        depth_band_score=row.depth_band_score,
        slippage_cushion_score=row.slippage_cushion_score,
        book_age_score=row.book_age_score,
        volatility_score=row.volatility_score,
        settlement_friction_score=row.settlement_friction_score,
    )
    if row.frontier_score != expected_frontier_score:
        raise ValueError("frontier_score must match component scores")


def _validate_report_consistency(
    report: ResearchMarketFeeSpreadDepthFrontierReport,
) -> None:
    if report.input_count != report.row_count:
        raise ValueError("input_count must match row_count")
    if report.row_count != _count_decimal(len(report.rows)):
        raise ValueError("row_count must match rows")
    if report.pass_count + report.watch_count + report.block_count != report.row_count:
        raise ValueError("status counts must match row_count")
    if report.high_fee_drag_count != _non_pass_reason_count(
        report.rows,
        "frontier_fee_drag",
    ):
        raise ValueError("high_fee_drag_count must match rows")
    if report.wide_spread_count != _non_pass_reason_count(
        report.rows,
        "frontier_spread_width",
    ):
        raise ValueError("wide_spread_count must match rows")
    if report.thin_depth_count != _non_pass_reason_count(
        report.rows,
        "frontier_depth_band",
    ):
        raise ValueError("thin_depth_count must match rows")
    if report.low_slippage_cushion_count != _non_pass_reason_count(
        report.rows,
        "frontier_slippage_cushion",
    ):
        raise ValueError("low_slippage_cushion_count must match rows")
    if report.stale_book_count != _non_pass_reason_count(
        report.rows,
        "frontier_book_age",
    ):
        raise ValueError("stale_book_count must match rows")
    if report.high_volatility_count != _non_pass_reason_count(
        report.rows,
        "frontier_volatility",
    ):
        raise ValueError("high_volatility_count must match rows")
    if report.high_settlement_friction_count != _non_pass_reason_count(
        report.rows,
        "frontier_settlement_friction",
    ):
        raise ValueError("high_settlement_friction_count must match rows")
    if report.average_frontier_score != _average_row_decimal(
        report.rows,
        "frontier_score",
    ):
        raise ValueError("average_frontier_score must match rows")
    if report.min_total_depth_band != _min_row_decimal(report.rows, "total_depth_band"):
        raise ValueError("min_total_depth_band must match rows")
    if report.max_fee_drag_ratio != _max_row_decimal(report.rows, "fee_drag_ratio"):
        raise ValueError("max_fee_drag_ratio must match rows")
    if report.max_spread_width_ratio != _max_row_decimal(
        report.rows,
        "spread_width_ratio",
    ):
        raise ValueError("max_spread_width_ratio must match rows")
    if report.min_slippage_cushion_ratio != _min_ratio_row_decimal(
        report.rows,
        "slippage_cushion_ratio",
    ):
        raise ValueError("min_slippage_cushion_ratio must match rows")
    if report.max_book_age_seconds != _max_row_decimal(report.rows, "book_age_seconds"):
        raise ValueError("max_book_age_seconds must match rows")
    if report.max_volatility_ratio != _max_row_decimal(report.rows, "volatility_ratio"):
        raise ValueError("max_volatility_ratio must match rows")
    if report.max_settlement_friction_ratio != _max_row_decimal(
        report.rows,
        "settlement_friction_ratio",
    ):
        raise ValueError("max_settlement_friction_ratio must match rows")
    if report.status != _report_status(report.rows):
        raise ValueError("status must match rows")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")
    if report.reason_code_counts != _report_reason_code_counts(report.rows):
        raise ValueError("reason_code_counts must match rows")


def _report_status(rows: tuple[ResearchMarketFeeSpreadDepthFrontierRow, ...]) -> str:
    if not rows:
        return BLOCK_STATUS
    if any(row.status == BLOCK_STATUS for row in rows):
        return BLOCK_STATUS
    if any(row.status == WATCH_STATUS for row in rows):
        return WATCH_STATUS
    return PASS_STATUS


def _report_reason_codes(
    rows: tuple[ResearchMarketFeeSpreadDepthFrontierRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return ("frontier_no_inputs",)
    reason_codes: list[str] = []
    for row in rows:
        reason_codes.extend(row.reason_codes)
    return _normalize_reason_codes("reason_codes", tuple(reason_codes))


def _report_reason_code_counts(
    rows: tuple[ResearchMarketFeeSpreadDepthFrontierRow, ...],
) -> tuple[ResearchMarketFeeSpreadDepthFrontierReasonCodeCount, ...]:
    counts: dict[str, Decimal] = {}
    for reason_code in _report_reason_codes(rows):
        counts[reason_code] = ZERO
    if not rows:
        counts["frontier_no_inputs"] = ONE
    for row in rows:
        for reason_code in row.reason_codes:
            counts[reason_code] = _quantize_decimal(counts.get(reason_code, ZERO) + ONE)
    return tuple(
        sorted(
            (
                ResearchMarketFeeSpreadDepthFrontierReasonCodeCount(
                    reason_code=reason_code,
                    count=count,
                )
                for reason_code, count in counts.items()
            ),
            key=lambda item: (-item.count, item.reason_code),
        ),
    )


def _status_count(
    rows: tuple[ResearchMarketFeeSpreadDepthFrontierRow, ...],
    status: str,
) -> Decimal:
    return _count_decimal(sum(1 for row in rows if row.status == status))


def _non_pass_reason_count(
    rows: tuple[ResearchMarketFeeSpreadDepthFrontierRow, ...],
    reason_prefix: str,
) -> Decimal:
    return _count_decimal(
        sum(
            1
            for row in rows
            if (
                f"{reason_prefix}_{WATCH_STATUS}" in row.reason_codes
                or f"{reason_prefix}_{BLOCK_STATUS}" in row.reason_codes
            )
        ),
    )


def _max_row_decimal(
    rows: tuple[ResearchMarketFeeSpreadDepthFrontierRow, ...],
    field_name: str,
) -> Decimal:
    if not rows:
        return ZERO
    return max(getattr(row, field_name) for row in rows)


def _min_row_decimal(
    rows: tuple[ResearchMarketFeeSpreadDepthFrontierRow, ...],
    field_name: str,
) -> Decimal:
    if not rows:
        return ZERO
    return min(getattr(row, field_name) for row in rows)


def _min_ratio_row_decimal(
    rows: tuple[ResearchMarketFeeSpreadDepthFrontierRow, ...],
    field_name: str,
) -> Decimal:
    if not rows:
        return ZERO
    return min(getattr(row, field_name) for row in rows)


def _average_row_decimal(
    rows: tuple[ResearchMarketFeeSpreadDepthFrontierRow, ...],
    field_name: str,
) -> Decimal:
    if not rows:
        return ZERO
    total = ZERO
    for row in rows:
        total = _quantize_decimal(total + getattr(row, field_name))
    with localcontext(DECIMAL_CONTEXT):
        return _quantize_decimal(total / Decimal(len(rows)))


def _seconds_between(later: datetime, earlier: datetime, earlier_name: str) -> Decimal:
    delta = later - earlier
    if delta.days < 0:
        raise ValueError(f"{earlier_name} must not be after generated_at")
    whole_seconds = Decimal(delta.days * 86400 + delta.seconds)
    fractional_seconds = Decimal(delta.microseconds) / Decimal("1000000")
    return _quantize_decimal(whole_seconds + fractional_seconds)


def _count_decimal(value: int) -> Decimal:
    return _quantize_decimal(Decimal(value))


def _require_ratio_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_nonnegative_decimal(field_name, value)
    if normalized > ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return normalized


def _require_positive_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized <= ZERO:
        raise ValueError(f"{field_name} must be positive")
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
    if type(value) is str and "-" in value:
        raise ValueError(f"{field_name} must use underscores")


def _require_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in FEE_SPREAD_DEPTH_FRONTIER_STATUSES:
        raise ValueError(f"{field_name} must be pass, watch, or block")


def _normalize_reason_codes(
    field_name: str,
    reason_codes: Iterable[str],
    *,
    allow_empty: bool = False,
) -> tuple[str, ...]:
    if isinstance(reason_codes, (str, bytes)) or not isinstance(reason_codes, Iterable):
        raise ValueError(f"{field_name} must be an iterable")
    normalized: list[str] = []
    for reason_code in reason_codes:
        _require_reason_code(field_name, reason_code)
        if reason_code not in normalized:
            normalized.append(reason_code)
    if not normalized and not allow_empty:
        raise ValueError(f"{field_name} must not be empty")
    return tuple(sorted(normalized))


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if getattr(value, field_name, None) is not True:
            raise ValueError(f"{label} {field_name} must be True")


def _require_payload_hard_flags(value: dict[str, Any]) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if value.get(field_name) is not True:
            raise ValueError(f"{field_name} must be True")


def _validate_public_payload_schema(payload: dict[str, Any]) -> None:
    _require_payload_keys(
        "payload",
        payload,
        (
            "generated_at",
            "config_version",
            "status",
            "input_count",
            "row_count",
            "pass_count",
            "watch_count",
            "block_count",
            "high_fee_drag_count",
            "wide_spread_count",
            "thin_depth_count",
            "low_slippage_cushion_count",
            "stale_book_count",
            "high_volatility_count",
            "high_settlement_friction_count",
            "average_frontier_score",
            "min_total_depth_band",
            "max_fee_drag_ratio",
            "max_spread_width_ratio",
            "min_slippage_cushion_ratio",
            "max_book_age_seconds",
            "max_volatility_ratio",
            "max_settlement_friction_ratio",
            "reason_codes",
            "reason_code_counts",
            "rows",
            "derived_validation_digest",
            "paper_only",
            "report_only",
            "readonly",
        ),
    )
    if type(payload["generated_at"]) is not str:
        raise ValueError("generated_at must be an ISO datetime string")
    _require_public_label("config_version", payload["config_version"])
    _require_status("status", payload["status"])
    for field_name in (
        "input_count",
        "row_count",
        "pass_count",
        "watch_count",
        "block_count",
        "high_fee_drag_count",
        "wide_spread_count",
        "thin_depth_count",
        "low_slippage_cushion_count",
        "stale_book_count",
        "high_volatility_count",
        "high_settlement_friction_count",
        "average_frontier_score",
        "min_total_depth_band",
        "max_fee_drag_ratio",
        "max_spread_width_ratio",
        "min_slippage_cushion_ratio",
        "max_book_age_seconds",
        "max_volatility_ratio",
        "max_settlement_friction_ratio",
    ):
        _require_payload_decimal_string(field_name, payload[field_name])
    _require_payload_reason_codes("reason_codes", payload["reason_codes"])
    _require_payload_reason_code_counts(payload["reason_code_counts"])
    _require_payload_rows(payload["rows"])


def _require_payload_keys(
    label: str,
    value: dict[str, Any],
    expected_keys: tuple[str, ...],
) -> None:
    if tuple(value.keys()) != expected_keys:
        raise ValueError(f"{label} keys must match report schema")


def _require_payload_decimal_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a Decimal-derived string")
    try:
        decimal_value = Decimal(value)
    except Exception as exc:
        raise ValueError(f"{field_name} must be a Decimal-derived string") from exc
    if not decimal_value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    if f"{_quantize_decimal(decimal_value):.6f}" != value:
        raise ValueError(f"{field_name} must be a Decimal-derived string")


def _require_payload_reason_codes(field_name: str, value: object) -> None:
    if not isinstance(value, list):
        raise ValueError(f"{field_name} must be a list")
    _normalize_reason_codes(field_name, tuple(value))


def _require_payload_reason_code_counts(value: object) -> None:
    if not isinstance(value, list):
        raise ValueError("reason_code_counts must be a list")
    for item in value:
        if type(item) is not dict:
            raise ValueError("reason_code_counts must contain dict items")
        _require_payload_keys(
            "reason_code_counts item",
            item,
            ("reason_code", "count", "paper_only", "report_only", "readonly"),
        )
        _require_reason_code("reason_code", item["reason_code"])
        _require_payload_decimal_string("count", item["count"])
        _require_payload_hard_flags(item)


def _require_payload_rows(value: object) -> None:
    if not isinstance(value, list):
        raise ValueError("rows must be a list")
    for item in value:
        if type(item) is not dict:
            raise ValueError("rows must contain dict items")
        _require_payload_keys(
            "rows item",
            item,
            (
                "public_row_ref",
                "book_observed_at",
                "book_age_seconds",
                "fee_drag_ratio",
                "fee_drag_score",
                "spread_width_ratio",
                "spread_width_score",
                "near_depth_band",
                "mid_depth_band",
                "far_depth_band",
                "total_depth_band",
                "depth_band_score",
                "slippage_cushion_ratio",
                "slippage_cushion_score",
                "volatility_ratio",
                "volatility_score",
                "settlement_friction_ratio",
                "settlement_friction_score",
                "book_age_score",
                "frontier_score",
                "status",
                "reason_codes",
                "paper_only",
                "report_only",
                "readonly",
            ),
        )
        _require_public_label("public_row_ref", item["public_row_ref"])
        if type(item["book_observed_at"]) is not str:
            raise ValueError("book_observed_at must be an ISO datetime string")
        for field_name in (
            "book_age_seconds",
            "fee_drag_ratio",
            "fee_drag_score",
            "spread_width_ratio",
            "spread_width_score",
            "near_depth_band",
            "mid_depth_band",
            "far_depth_band",
            "total_depth_band",
            "depth_band_score",
            "slippage_cushion_ratio",
            "slippage_cushion_score",
            "volatility_ratio",
            "volatility_score",
            "settlement_friction_ratio",
            "settlement_friction_score",
            "book_age_score",
            "frontier_score",
        ):
            _require_payload_decimal_string(field_name, item[field_name])
        _require_status("status", item["status"])
        _require_payload_reason_codes("reason_codes", item["reason_codes"])
        _require_payload_hard_flags(item)


def _require_exact_type(value: object, type_: type[object], label: str) -> None:
    if type(value) is not type_:
        raise ValueError(f"{label} must be exactly {type_.__name__}")


def _require_sha256_digest(field_name: str, value: object) -> None:
    if type(value) is not str or len(value) != 64:
        raise ValueError(f"{field_name} must be a lowercase sha256 digest")
    allowed = set("0123456789abcdef")
    if any(character not in allowed for character in value):
        raise ValueError(f"{field_name} must be a lowercase sha256 digest")


def _row_sort_key(
    row: ResearchMarketFeeSpreadDepthFrontierRow,
) -> tuple[Decimal, Decimal, str]:
    return (STATUS_RANK[row.status], row.frontier_score, row.public_row_ref)


def _private_digest(*parts: str) -> str:
    return sha256("\x1f".join(parts).encode("utf-8")).hexdigest()


def _public_row_ref(index: int) -> str:
    return f"frontier_group_{index:03d}"


def _report_derived_validation_digest(
    report: ResearchMarketFeeSpreadDepthFrontierReport,
) -> str:
    return _payload_derived_validation_digest(_public_payload_without_digest(report))


def _public_payload_without_digest(
    report: ResearchMarketFeeSpreadDepthFrontierReport,
) -> dict[str, Any]:
    payload = _json_value(report)
    if type(payload) is not dict:
        raise ValueError("report must serialize to a JSON object")
    payload.pop("derived_validation_digest", None)
    return payload


def _payload_derived_validation_digest(payload: dict[str, Any]) -> str:
    digest_payload = dict(payload)
    digest_payload.pop("derived_validation_digest", None)
    _reject_unsafe_public_payload("derived_validation_digest payload", digest_payload)
    encoded_payload = json.dumps(
        digest_payload,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    )
    return sha256(encoded_payload.encode("utf-8")).hexdigest()


def _contains_unsafe_public_fragment(value: str) -> bool:
    lowered = value.lower()
    return any(fragment in lowered for fragment in UNSAFE_PUBLIC_FRAGMENTS)


def _reject_unsafe_public_payload(value_label: str, value: object, path: str = "") -> None:
    current_path = path or value_label
    if is_dataclass(value) and not isinstance(value, type):
        _reject_unsafe_public_payload(value_label, asdict(value), current_path)
        return
    if type(value) is bool:
        return
    if type(value) in (int, float):
        raise ValueError(f"{value_label} has unsafe public numeric payload")
    if isinstance(value, dict):
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError(f"{value_label} has unsafe public payload")
            if _contains_unsafe_public_fragment(key):
                raise ValueError(f"{value_label} has unsafe public payload at {current_path}")
            if key in {"paper_only", "report_only", "readonly"} and item is not True:
                raise ValueError(f"{current_path}.{key} must be True")
            _reject_unsafe_public_payload(value_label, item, f"{current_path}.{key}")
        return
    if isinstance(value, (list, tuple)):
        for index, item in enumerate(value):
            _reject_unsafe_public_payload(value_label, item, f"{current_path}[{index}]")
        return
    if type(value) is str and _contains_unsafe_public_fragment(value):
        raise ValueError(f"{value_label} has unsafe public payload at {current_path}")


def _json_value(value: object) -> Any:
    if isinstance(value, Decimal):
        return f"{value:.6f}"
    if type(value) is datetime:
        return value.isoformat()
    if is_dataclass(value) and not isinstance(value, type):
        return {
            field.name: _json_value(getattr(value, field.name))
            for field in fields(value)
        }
    if isinstance(value, tuple):
        return [_json_value(item) for item in value]
    if isinstance(value, list):
        return [_json_value(item) for item in value]
    if isinstance(value, dict):
        return {key: _json_value(item) for key, item in value.items()}
    return value
