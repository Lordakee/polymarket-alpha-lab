"""Pure report-only spread/fee/depth decay reducer."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import asdict, dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, localcontext
from hashlib import sha256
import json
from typing import Any


__all__ = (
    "SPREAD_FEE_DEPTH_DECAY_STATUSES",
    "DEFAULT_RESEARCH_MARKET_SPREAD_FEE_DEPTH_DECAY_REPORT_CONFIG_VERSION",
    "ResearchMarketSpreadFeeDepthDecayConfig",
    "ResearchMarketSpreadFeeDepthDecayInput",
    "ResearchMarketSpreadFeeDepthDecayReasonCodeCount",
    "ResearchMarketSpreadFeeDepthDecayReport",
    "ResearchMarketSpreadFeeDepthDecayRow",
    "build_research_market_spread_fee_depth_decay_report",
    "research_market_spread_fee_depth_decay_report_payload",
    "validate_research_market_spread_fee_depth_decay_report_payload",
)


DEFAULT_RESEARCH_MARKET_SPREAD_FEE_DEPTH_DECAY_REPORT_CONFIG_VERSION = (
    "research-market-spread-fee-depth-decay-report-v1"
)
PASS_STATUS = "pass"
WATCH_STATUS = "watch"
BLOCK_STATUS = "block"
SPREAD_FEE_DEPTH_DECAY_STATUSES = (PASS_STATUS, WATCH_STATUS, BLOCK_STATUS)
STATUS_RANK = {
    BLOCK_STATUS: Decimal("0.000000"),
    WATCH_STATUS: Decimal("1.000000"),
    PASS_STATUS: Decimal("2.000000"),
}
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
FIVE = Decimal("5.000000")
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
    _join_parts("sou", "rce", "_", "ur", "l"),
    _join_parts("sou", "rce", "_", "tex", "t"),
    _join_parts("d", "sn"),
    _join_parts("tab", "le", "_", "name"),
    _join_parts("to", "ken"),
    _join_parts("wal", "let"),
    _join_parts("au", "th"),
    _join_parts("or", "der"),
    _join_parts("tra", "de"),
    _join_parts("li", "ve"),
    _join_parts("reco", "mmend"),
    _join_parts("siz", "ing"),
    "://",
    "?",
    "@",
    "=",
)


@dataclass(frozen=True)
class ResearchMarketSpreadFeeDepthDecayConfig:
    config_version: str = (
        DEFAULT_RESEARCH_MARKET_SPREAD_FEE_DEPTH_DECAY_REPORT_CONFIG_VERSION
    )
    maximum_pass_spread_width_ratio: Decimal = Decimal("0.020000")
    maximum_watch_spread_width_ratio: Decimal = Decimal("0.060000")
    maximum_pass_fee_drag_ratio: Decimal = Decimal("0.010000")
    maximum_watch_fee_drag_ratio: Decimal = Decimal("0.030000")
    maximum_pass_depth_decay_ratio: Decimal = Decimal("0.250000")
    maximum_watch_depth_decay_ratio: Decimal = Decimal("0.600000")
    minimum_pass_current_depth_band: Decimal = Decimal("1000.000000")
    minimum_watch_current_depth_band: Decimal = Decimal("250.000000")
    maximum_pass_book_age_seconds: Decimal = Decimal("120.000000")
    maximum_watch_book_age_seconds: Decimal = Decimal("600.000000")
    minimum_pass_spread_fee_depth_decay_score: Decimal = Decimal("0.750000")
    minimum_watch_spread_fee_depth_decay_score: Decimal = Decimal("0.450000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchMarketSpreadFeeDepthDecayConfig, "config")
        _require_public_label("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_MARKET_SPREAD_FEE_DEPTH_DECAY_REPORT_CONFIG_VERSION
        ):
            raise ValueError("config_version must match supported value")
        for field_name in (
            "maximum_pass_spread_width_ratio",
            "maximum_watch_spread_width_ratio",
            "maximum_pass_fee_drag_ratio",
            "maximum_watch_fee_drag_ratio",
            "maximum_pass_depth_decay_ratio",
            "maximum_watch_depth_decay_ratio",
            "minimum_pass_spread_fee_depth_decay_score",
            "minimum_watch_spread_fee_depth_decay_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "minimum_pass_current_depth_band",
            "minimum_watch_current_depth_band",
            "maximum_pass_book_age_seconds",
            "maximum_watch_book_age_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_positive_decimal(field_name, getattr(self, field_name)),
            )
        if self.maximum_pass_spread_width_ratio > self.maximum_watch_spread_width_ratio:
            raise ValueError("maximum_pass_spread_width_ratio must not exceed watch")
        if self.maximum_pass_fee_drag_ratio > self.maximum_watch_fee_drag_ratio:
            raise ValueError("maximum_pass_fee_drag_ratio must not exceed watch")
        if self.maximum_pass_depth_decay_ratio > self.maximum_watch_depth_decay_ratio:
            raise ValueError("maximum_pass_depth_decay_ratio must not exceed watch")
        if self.minimum_pass_current_depth_band < self.minimum_watch_current_depth_band:
            raise ValueError("minimum_pass_current_depth_band must be at least watch")
        if self.maximum_pass_book_age_seconds > self.maximum_watch_book_age_seconds:
            raise ValueError("maximum_pass_book_age_seconds must not exceed watch")
        if (
            self.minimum_pass_spread_fee_depth_decay_score
            < self.minimum_watch_spread_fee_depth_decay_score
        ):
            raise ValueError(
                "minimum_pass_spread_fee_depth_decay_score must be at least watch",
            )
        _require_hard_flags("config", self)
        _reject_unsafe_public_payload("config", self)


@dataclass(frozen=True)
class ResearchMarketSpreadFeeDepthDecayInput:
    private_item_ref: str
    private_group_ref: str
    observed_at: datetime
    spread_width_ratio: Decimal
    fee_drag_ratio: Decimal
    current_depth_band: Decimal
    baseline_depth_band: Decimal
    reason_codes: tuple[str, ...] = ()
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchMarketSpreadFeeDepthDecayInput, "input")
        for field_name in ("private_item_ref", "private_group_ref"):
            _require_private_ref(field_name, getattr(self, field_name))
        object.__setattr__(
            self,
            "observed_at",
            _as_utc("observed_at", self.observed_at),
        )
        for field_name in ("spread_width_ratio", "fee_drag_ratio"):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "current_depth_band",
            _require_nonnegative_decimal("current_depth_band", self.current_depth_band),
        )
        object.__setattr__(
            self,
            "baseline_depth_band",
            _require_positive_decimal("baseline_depth_band", self.baseline_depth_band),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, allow_empty=True),
        )
        _require_hard_flags("input", self)


@dataclass(frozen=True)
class ResearchMarketSpreadFeeDepthDecayRow:
    public_row_ref: str
    observed_at: datetime
    book_age_seconds: Decimal
    spread_width_ratio: Decimal
    spread_width_score: Decimal
    fee_drag_ratio: Decimal
    fee_drag_score: Decimal
    current_depth_band: Decimal
    baseline_depth_band: Decimal
    depth_retention_ratio: Decimal
    depth_decay_ratio: Decimal
    depth_decay_score: Decimal
    current_depth_score: Decimal
    book_age_score: Decimal
    spread_fee_depth_decay_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchMarketSpreadFeeDepthDecayRow, "row")
        _require_public_label("public_row_ref", self.public_row_ref)
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in (
            "book_age_seconds",
            "current_depth_band",
            "baseline_depth_band",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        if self.baseline_depth_band <= ZERO:
            raise ValueError("baseline_depth_band must be positive")
        for field_name in (
            "spread_width_ratio",
            "spread_width_score",
            "fee_drag_ratio",
            "fee_drag_score",
            "depth_retention_ratio",
            "depth_decay_ratio",
            "depth_decay_score",
            "current_depth_score",
            "book_age_score",
            "spread_fee_depth_decay_score",
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
class ResearchMarketSpreadFeeDepthDecayReasonCodeCount:
    reason_code: str
    count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchMarketSpreadFeeDepthDecayReasonCodeCount,
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
class ResearchMarketSpreadFeeDepthDecayReport:
    generated_at: datetime
    config_version: str
    status: str
    input_count: Decimal
    row_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    wide_spread_count: Decimal
    high_fee_drag_count: Decimal
    depth_decay_count: Decimal
    thin_depth_count: Decimal
    stale_book_count: Decimal
    average_spread_fee_depth_decay_score: Decimal
    min_current_depth_band: Decimal
    max_spread_width_ratio: Decimal
    max_fee_drag_ratio: Decimal
    max_depth_decay_ratio: Decimal
    max_book_age_seconds: Decimal
    reason_codes: tuple[str, ...]
    reason_code_counts: tuple[ResearchMarketSpreadFeeDepthDecayReasonCodeCount, ...]
    rows: tuple[ResearchMarketSpreadFeeDepthDecayRow, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchMarketSpreadFeeDepthDecayReport, "report")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_label("config_version", self.config_version)
        _require_status("status", self.status)
        for field_name in (
            "input_count",
            "row_count",
            "pass_count",
            "watch_count",
            "block_count",
            "wide_spread_count",
            "high_fee_drag_count",
            "depth_decay_count",
            "thin_depth_count",
            "stale_book_count",
            "min_current_depth_band",
            "max_book_age_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "average_spread_fee_depth_decay_score",
            "max_spread_width_ratio",
            "max_fee_drag_ratio",
            "max_depth_decay_ratio",
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


def build_research_market_spread_fee_depth_decay_report(
    inputs: Iterable[ResearchMarketSpreadFeeDepthDecayInput],
    *,
    config: ResearchMarketSpreadFeeDepthDecayConfig,
    generated_at: datetime,
) -> ResearchMarketSpreadFeeDepthDecayReport:
    if type(config) is not ResearchMarketSpreadFeeDepthDecayConfig:
        raise ValueError("config must be a ResearchMarketSpreadFeeDepthDecayConfig")
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
    return ResearchMarketSpreadFeeDepthDecayReport(
        generated_at=generated_at,
        config_version=config.config_version,
        status=_report_status(rows),
        input_count=_count_decimal(len(normalized)),
        row_count=_count_decimal(len(rows)),
        pass_count=_status_count(rows, PASS_STATUS),
        watch_count=_status_count(rows, WATCH_STATUS),
        block_count=_status_count(rows, BLOCK_STATUS),
        wide_spread_count=_non_pass_reason_count(
            rows,
            "spread_fee_depth_decay_spread_width",
        ),
        high_fee_drag_count=_non_pass_reason_count(
            rows,
            "spread_fee_depth_decay_fee_drag",
        ),
        depth_decay_count=_non_pass_reason_count(
            rows,
            "spread_fee_depth_decay_depth_decay",
        ),
        thin_depth_count=_non_pass_reason_count(
            rows,
            "spread_fee_depth_decay_current_depth",
        ),
        stale_book_count=_non_pass_reason_count(
            rows,
            "spread_fee_depth_decay_book_age",
        ),
        average_spread_fee_depth_decay_score=_average_row_decimal(
            rows,
            "spread_fee_depth_decay_score",
        ),
        min_current_depth_band=_min_row_decimal(rows, "current_depth_band"),
        max_spread_width_ratio=_max_row_decimal(rows, "spread_width_ratio"),
        max_fee_drag_ratio=_max_row_decimal(rows, "fee_drag_ratio"),
        max_depth_decay_ratio=_max_row_decimal(rows, "depth_decay_ratio"),
        max_book_age_seconds=_max_row_decimal(rows, "book_age_seconds"),
        reason_codes=_report_reason_codes(rows),
        reason_code_counts=_report_reason_code_counts(rows),
        rows=rows,
    )


def research_market_spread_fee_depth_decay_report_payload(
    report: ResearchMarketSpreadFeeDepthDecayReport,
) -> dict[str, Any]:
    if type(report) is not ResearchMarketSpreadFeeDepthDecayReport:
        raise ValueError("report must be a ResearchMarketSpreadFeeDepthDecayReport")
    _require_hard_flags("report", report)
    _reject_unsafe_public_payload("report", report)
    payload = _json_value(report)
    if type(payload) is not dict:
        raise ValueError("report must serialize to a JSON object")
    validate_research_market_spread_fee_depth_decay_report_payload(payload)
    return payload


def validate_research_market_spread_fee_depth_decay_report_payload(
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
    value: ResearchMarketSpreadFeeDepthDecayInput,
    *,
    config: ResearchMarketSpreadFeeDepthDecayConfig,
    generated_at: datetime,
    public_row_ref: str,
) -> ResearchMarketSpreadFeeDepthDecayRow:
    book_age_seconds = _seconds_between(generated_at, value.observed_at, "observed_at")
    depth_retention_ratio = _depth_retention_ratio(
        value.current_depth_band,
        value.baseline_depth_band,
    )
    depth_decay_ratio = _quantize_decimal(ONE - depth_retention_ratio)
    spread_width_score = _score_for_maximum(
        value.spread_width_ratio,
        config.maximum_pass_spread_width_ratio,
        config.maximum_watch_spread_width_ratio,
    )
    fee_drag_score = _score_for_maximum(
        value.fee_drag_ratio,
        config.maximum_pass_fee_drag_ratio,
        config.maximum_watch_fee_drag_ratio,
    )
    depth_decay_score = _score_for_maximum(
        depth_decay_ratio,
        config.maximum_pass_depth_decay_ratio,
        config.maximum_watch_depth_decay_ratio,
    )
    current_depth_score = _score_for_minimum(
        value.current_depth_band,
        config.minimum_pass_current_depth_band,
        config.minimum_watch_current_depth_band,
    )
    book_age_score = _score_for_maximum(
        book_age_seconds,
        config.maximum_pass_book_age_seconds,
        config.maximum_watch_book_age_seconds,
    )
    combined_score = _spread_fee_depth_decay_score(
        spread_width_score=spread_width_score,
        fee_drag_score=fee_drag_score,
        depth_decay_score=depth_decay_score,
        current_depth_score=current_depth_score,
        book_age_score=book_age_score,
    )
    component_statuses = (
        _status_for_maximum(
            value.spread_width_ratio,
            config.maximum_pass_spread_width_ratio,
            config.maximum_watch_spread_width_ratio,
        ),
        _status_for_maximum(
            value.fee_drag_ratio,
            config.maximum_pass_fee_drag_ratio,
            config.maximum_watch_fee_drag_ratio,
        ),
        _status_for_maximum(
            depth_decay_ratio,
            config.maximum_pass_depth_decay_ratio,
            config.maximum_watch_depth_decay_ratio,
        ),
        _status_for_minimum(
            value.current_depth_band,
            config.minimum_pass_current_depth_band,
            config.minimum_watch_current_depth_band,
        ),
        _status_for_maximum(
            book_age_seconds,
            config.maximum_pass_book_age_seconds,
            config.maximum_watch_book_age_seconds,
        ),
    )
    status = _spread_fee_depth_decay_status(
        component_statuses=component_statuses,
        combined_score=combined_score,
        config=config,
    )
    return ResearchMarketSpreadFeeDepthDecayRow(
        public_row_ref=public_row_ref,
        observed_at=value.observed_at,
        book_age_seconds=book_age_seconds,
        spread_width_ratio=value.spread_width_ratio,
        spread_width_score=spread_width_score,
        fee_drag_ratio=value.fee_drag_ratio,
        fee_drag_score=fee_drag_score,
        current_depth_band=value.current_depth_band,
        baseline_depth_band=value.baseline_depth_band,
        depth_retention_ratio=depth_retention_ratio,
        depth_decay_ratio=depth_decay_ratio,
        depth_decay_score=depth_decay_score,
        current_depth_score=current_depth_score,
        book_age_score=book_age_score,
        spread_fee_depth_decay_score=combined_score,
        status=status,
        reason_codes=_row_reason_codes(
            value.reason_codes,
            status=status,
            spread_width_status=component_statuses[0],
            fee_drag_status=component_statuses[1],
            depth_decay_status=component_statuses[2],
            current_depth_status=component_statuses[3],
            book_age_status=component_statuses[4],
        ),
    )


def _spread_fee_depth_decay_score(
    *,
    spread_width_score: Decimal,
    fee_drag_score: Decimal,
    depth_decay_score: Decimal,
    current_depth_score: Decimal,
    book_age_score: Decimal,
) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return _quantize_decimal(
            (
                spread_width_score
                + fee_drag_score
                + depth_decay_score
                + current_depth_score
                + book_age_score
            )
            / FIVE,
        )


def _spread_fee_depth_decay_status(
    *,
    component_statuses: tuple[str, ...],
    combined_score: Decimal,
    config: ResearchMarketSpreadFeeDepthDecayConfig,
) -> str:
    if (
        BLOCK_STATUS in component_statuses
        or combined_score < config.minimum_watch_spread_fee_depth_decay_score
    ):
        return BLOCK_STATUS
    if (
        WATCH_STATUS in component_statuses
        or combined_score < config.minimum_pass_spread_fee_depth_decay_score
    ):
        return WATCH_STATUS
    return PASS_STATUS


def _row_reason_codes(
    input_reason_codes: tuple[str, ...],
    *,
    status: str,
    spread_width_status: str,
    fee_drag_status: str,
    depth_decay_status: str,
    current_depth_status: str,
    book_age_status: str,
) -> tuple[str, ...]:
    reason_codes = [f"input_{reason_code}" for reason_code in input_reason_codes]
    reason_codes.extend(
        (
            f"spread_fee_depth_decay_status_{status}",
            f"spread_fee_depth_decay_spread_width_{spread_width_status}",
            f"spread_fee_depth_decay_fee_drag_{fee_drag_status}",
            f"spread_fee_depth_decay_depth_decay_{depth_decay_status}",
            f"spread_fee_depth_decay_current_depth_{current_depth_status}",
            f"spread_fee_depth_decay_book_age_{book_age_status}",
        ),
    )
    return _normalize_reason_codes("reason_codes", tuple(reason_codes))


def _depth_retention_ratio(current_depth_band: Decimal, baseline_depth_band: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        raw_ratio = current_depth_band / baseline_depth_band
    if raw_ratio >= ONE:
        return ONE
    return _quantize_decimal(raw_ratio)


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
    inputs: Iterable[ResearchMarketSpreadFeeDepthDecayInput],
) -> tuple[ResearchMarketSpreadFeeDepthDecayInput, ...]:
    if isinstance(inputs, (str, bytes)) or not isinstance(inputs, Iterable):
        raise ValueError("inputs must be an iterable")
    normalized = tuple(inputs)
    for value in normalized:
        if type(value) is not ResearchMarketSpreadFeeDepthDecayInput:
            raise ValueError(
                "inputs must contain ResearchMarketSpreadFeeDepthDecayInput",
            )
        _require_hard_flags("input", value)
    return normalized


def _normalize_rows(
    rows: Iterable[ResearchMarketSpreadFeeDepthDecayRow],
) -> tuple[ResearchMarketSpreadFeeDepthDecayRow, ...]:
    if isinstance(rows, (str, bytes)) or not isinstance(rows, Iterable):
        raise ValueError("rows must be an iterable")
    normalized = tuple(rows)
    for row in normalized:
        if type(row) is not ResearchMarketSpreadFeeDepthDecayRow:
            raise ValueError("rows must contain ResearchMarketSpreadFeeDepthDecayRow")
        _require_hard_flags("row", row)
    return tuple(sorted(normalized, key=_row_sort_key))


def _normalize_reason_code_counts(
    counts: Iterable[ResearchMarketSpreadFeeDepthDecayReasonCodeCount],
) -> tuple[ResearchMarketSpreadFeeDepthDecayReasonCodeCount, ...]:
    if isinstance(counts, (str, bytes)) or not isinstance(counts, Iterable):
        raise ValueError("reason_code_counts must be an iterable")
    normalized = tuple(counts)
    for count in normalized:
        if type(count) is not ResearchMarketSpreadFeeDepthDecayReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "ResearchMarketSpreadFeeDepthDecayReasonCodeCount",
            )
        _require_hard_flags("reason_count", count)
    return tuple(sorted(normalized, key=lambda item: (-item.count, item.reason_code)))


def _validate_row_consistency(row: ResearchMarketSpreadFeeDepthDecayRow) -> None:
    if f"spread_fee_depth_decay_status_{row.status}" not in row.reason_codes:
        raise ValueError("status must match reason_codes")
    if row.depth_retention_ratio != _depth_retention_ratio(
        row.current_depth_band,
        row.baseline_depth_band,
    ):
        raise ValueError("depth_retention_ratio must match depth bands")
    if row.depth_decay_ratio != _quantize_decimal(ONE - row.depth_retention_ratio):
        raise ValueError("depth_decay_ratio must match depth retention")
    expected_score = _spread_fee_depth_decay_score(
        spread_width_score=row.spread_width_score,
        fee_drag_score=row.fee_drag_score,
        depth_decay_score=row.depth_decay_score,
        current_depth_score=row.current_depth_score,
        book_age_score=row.book_age_score,
    )
    if row.spread_fee_depth_decay_score != expected_score:
        raise ValueError("spread_fee_depth_decay_score must match component scores")


def _validate_report_consistency(
    report: ResearchMarketSpreadFeeDepthDecayReport,
) -> None:
    if report.input_count != report.row_count:
        raise ValueError("input_count must match row_count")
    if report.row_count != _count_decimal(len(report.rows)):
        raise ValueError("row_count must match rows")
    if report.pass_count + report.watch_count + report.block_count != report.row_count:
        raise ValueError("status counts must match row_count")
    if report.wide_spread_count != _non_pass_reason_count(
        report.rows,
        "spread_fee_depth_decay_spread_width",
    ):
        raise ValueError("wide_spread_count must match rows")
    if report.high_fee_drag_count != _non_pass_reason_count(
        report.rows,
        "spread_fee_depth_decay_fee_drag",
    ):
        raise ValueError("high_fee_drag_count must match rows")
    if report.depth_decay_count != _non_pass_reason_count(
        report.rows,
        "spread_fee_depth_decay_depth_decay",
    ):
        raise ValueError("depth_decay_count must match rows")
    if report.thin_depth_count != _non_pass_reason_count(
        report.rows,
        "spread_fee_depth_decay_current_depth",
    ):
        raise ValueError("thin_depth_count must match rows")
    if report.stale_book_count != _non_pass_reason_count(
        report.rows,
        "spread_fee_depth_decay_book_age",
    ):
        raise ValueError("stale_book_count must match rows")
    if report.average_spread_fee_depth_decay_score != _average_row_decimal(
        report.rows,
        "spread_fee_depth_decay_score",
    ):
        raise ValueError("average_spread_fee_depth_decay_score must match rows")
    if report.min_current_depth_band != _min_row_decimal(
        report.rows,
        "current_depth_band",
    ):
        raise ValueError("min_current_depth_band must match rows")
    if report.max_spread_width_ratio != _max_row_decimal(
        report.rows,
        "spread_width_ratio",
    ):
        raise ValueError("max_spread_width_ratio must match rows")
    if report.max_fee_drag_ratio != _max_row_decimal(report.rows, "fee_drag_ratio"):
        raise ValueError("max_fee_drag_ratio must match rows")
    if report.max_depth_decay_ratio != _max_row_decimal(report.rows, "depth_decay_ratio"):
        raise ValueError("max_depth_decay_ratio must match rows")
    if report.max_book_age_seconds != _max_row_decimal(report.rows, "book_age_seconds"):
        raise ValueError("max_book_age_seconds must match rows")
    if report.status != _report_status(report.rows):
        raise ValueError("status must match rows")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")
    if report.reason_code_counts != _report_reason_code_counts(report.rows):
        raise ValueError("reason_code_counts must match rows")


def _report_status(rows: tuple[ResearchMarketSpreadFeeDepthDecayRow, ...]) -> str:
    if not rows:
        return BLOCK_STATUS
    if any(row.status == BLOCK_STATUS for row in rows):
        return BLOCK_STATUS
    if any(row.status == WATCH_STATUS for row in rows):
        return WATCH_STATUS
    return PASS_STATUS


def _report_reason_codes(
    rows: tuple[ResearchMarketSpreadFeeDepthDecayRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return ("spread_fee_depth_decay_no_inputs",)
    reason_codes: list[str] = []
    for row in rows:
        reason_codes.extend(row.reason_codes)
    return _normalize_reason_codes("reason_codes", tuple(reason_codes))


def _report_reason_code_counts(
    rows: tuple[ResearchMarketSpreadFeeDepthDecayRow, ...],
) -> tuple[ResearchMarketSpreadFeeDepthDecayReasonCodeCount, ...]:
    counts: dict[str, Decimal] = {}
    for reason_code in _report_reason_codes(rows):
        counts[reason_code] = ZERO
    if not rows:
        counts["spread_fee_depth_decay_no_inputs"] = ONE
    for row in rows:
        for reason_code in row.reason_codes:
            counts[reason_code] = _quantize_decimal(counts.get(reason_code, ZERO) + ONE)
    return tuple(
        sorted(
            (
                ResearchMarketSpreadFeeDepthDecayReasonCodeCount(
                    reason_code=reason_code,
                    count=count,
                )
                for reason_code, count in counts.items()
            ),
            key=lambda item: (-item.count, item.reason_code),
        ),
    )


def _status_count(
    rows: tuple[ResearchMarketSpreadFeeDepthDecayRow, ...],
    status: str,
) -> Decimal:
    return _count_decimal(sum(1 for row in rows if row.status == status))


def _non_pass_reason_count(
    rows: tuple[ResearchMarketSpreadFeeDepthDecayRow, ...],
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
    rows: tuple[ResearchMarketSpreadFeeDepthDecayRow, ...],
    field_name: str,
) -> Decimal:
    if not rows:
        return ZERO
    return max(getattr(row, field_name) for row in rows)


def _min_row_decimal(
    rows: tuple[ResearchMarketSpreadFeeDepthDecayRow, ...],
    field_name: str,
) -> Decimal:
    if not rows:
        return ZERO
    return min(getattr(row, field_name) for row in rows)


def _average_row_decimal(
    rows: tuple[ResearchMarketSpreadFeeDepthDecayRow, ...],
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
    if type(value) is not str or value not in SPREAD_FEE_DEPTH_DECAY_STATUSES:
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


def _require_exact_type(value: object, type_: type[object], label: str) -> None:
    if type(value) is not type_:
        raise ValueError(f"{label} must be exactly {type_.__name__}")


def _require_sha256_digest(field_name: str, value: object) -> None:
    if type(value) is not str or len(value) != 64:
        raise ValueError(f"{field_name} must be a lowercase sha256 digest")
    allowed = set("0123456789abcdef")
    if any(character not in allowed for character in value):
        raise ValueError(f"{field_name} must be a lowercase sha256 digest")


def _row_sort_key(row: ResearchMarketSpreadFeeDepthDecayRow) -> tuple[Decimal, Decimal, str]:
    return (STATUS_RANK[row.status], row.spread_fee_depth_decay_score, row.public_row_ref)


def _private_digest(*parts: str) -> str:
    return sha256("\x1f".join(parts).encode("utf-8")).hexdigest()


def _public_row_ref(index: int) -> str:
    return f"spread_fee_depth_decay_group_{index:03d}"


def _report_derived_validation_digest(
    report: ResearchMarketSpreadFeeDepthDecayReport,
) -> str:
    return _payload_derived_validation_digest(_public_payload_without_digest(report))


def _public_payload_without_digest(
    report: ResearchMarketSpreadFeeDepthDecayReport,
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
