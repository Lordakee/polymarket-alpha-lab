"""Pure report-only probability/cost volatility frontier reducer."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import asdict, dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, localcontext
from hashlib import sha256
import json
from typing import Any


__all__ = (
    "PROBABILITY_COST_VOLATILITY_FRONTIER_STATUSES",
    "DEFAULT_RESEARCH_MARKET_PROBABILITY_COST_VOLATILITY_FRONTIER_REPORT_CONFIG_VERSION",
    "ResearchMarketProbabilityCostVolatilityFrontierConfig",
    "ResearchMarketProbabilityCostVolatilityFrontierInput",
    "ResearchMarketProbabilityCostVolatilityFrontierReasonCodeCount",
    "ResearchMarketProbabilityCostVolatilityFrontierReport",
    "ResearchMarketProbabilityCostVolatilityFrontierRow",
    "build_research_market_probability_cost_volatility_frontier_report",
    "research_market_probability_cost_volatility_frontier_report_payload",
    "validate_research_market_probability_cost_volatility_frontier_report_payload",
)


DEFAULT_RESEARCH_MARKET_PROBABILITY_COST_VOLATILITY_FRONTIER_REPORT_CONFIG_VERSION = (
    "research-market-probability-cost-volatility-frontier-report-v0"
)
PASS_STATUS = "pass"
WATCH_STATUS = "watch"
BLOCK_STATUS = "block"
PROBABILITY_COST_VOLATILITY_FRONTIER_STATUSES = (
    PASS_STATUS,
    WATCH_STATUS,
    BLOCK_STATUS,
)
STATUS_RANK = {
    BLOCK_STATUS: Decimal("0.000000"),
    WATCH_STATUS: Decimal("1.000000"),
    PASS_STATUS: Decimal("2.000000"),
}
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
EIGHT = Decimal("8.000000")
QUANTUM = Decimal("0.000001")
DECIMAL_CONTEXT = Context(prec=64)


def _join_parts(*parts: str) -> str:
    return "".join(parts)


UNSAFE_PUBLIC_FRAGMENTS = (
    _join_parts("ra", "w"),
    _join_parts("can", "didate", "_", "id"),
    _join_parts("ma", "rket", "_", "id"),
    _join_parts("ma", "rket", "_", "sl", "ug"),
    _join_parts("ma", "rket", "-", "sl", "ug"),
    _join_parts("sl", "ug"),
    _join_parts("ques", "tion"),
    _join_parts("sour", "ce", "_", "ur", "l"),
    _join_parts("sour", "ce", "_", "tex", "t"),
    _join_parts("d", "sn"),
    _join_parts("tab", "le", "_", "name"),
    _join_parts("to", "ken"),
    _join_parts("wal", "let"),
    _join_parts("au", "th"),
    _join_parts("or", "der"),
    _join_parts("tra", "de"),
    _join_parts("tra", "ding"),
    _join_parts("li", "ve"),
    _join_parts("net", "work"),
    _join_parts("pos", "ition"),
    _join_parts("siz", "ing"),
    _join_parts("reco", "mmend"),
    _join_parts("bu", "y"),
    _join_parts("se", "ll"),
    _join_parts("priv", "ate"),
    _join_parts("sec", "ret"),
    _join_parts("cred", "ential"),
    "://",
    "?",
    "@",
    "=",
)


@dataclass(frozen=True)
class ResearchMarketProbabilityCostVolatilityFrontierConfig:
    config_version: str = (
        DEFAULT_RESEARCH_MARKET_PROBABILITY_COST_VOLATILITY_FRONTIER_REPORT_CONFIG_VERSION
    )
    minimum_pass_sanitized_edge_probability: Decimal = Decimal("0.050000")
    minimum_watch_sanitized_edge_probability: Decimal = Decimal("0.020000")
    maximum_pass_edge_stability_delta: Decimal = Decimal("0.006000")
    maximum_watch_edge_stability_delta: Decimal = Decimal("0.020000")
    maximum_pass_fee_pressure_ratio: Decimal = Decimal("0.010000")
    maximum_watch_fee_pressure_ratio: Decimal = Decimal("0.030000")
    maximum_pass_spread_pressure_ratio: Decimal = Decimal("0.020000")
    maximum_watch_spread_pressure_ratio: Decimal = Decimal("0.060000")
    maximum_pass_slippage_pressure_ratio: Decimal = Decimal("0.010000")
    maximum_watch_slippage_pressure_ratio: Decimal = Decimal("0.040000")
    maximum_pass_volatility_pressure_ratio: Decimal = Decimal("0.050000")
    maximum_watch_volatility_pressure_ratio: Decimal = Decimal("0.160000")
    maximum_pass_total_pressure_ratio: Decimal = Decimal("0.070000")
    maximum_watch_total_pressure_ratio: Decimal = Decimal("0.220000")
    minimum_pass_net_cost_adjusted_edge_probability: Decimal = Decimal("0.015000")
    minimum_watch_net_cost_adjusted_edge_probability: Decimal = Decimal("0.000000")
    minimum_pass_frontier_score: Decimal = Decimal("0.750000")
    minimum_watch_frontier_score: Decimal = Decimal("0.450000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchMarketProbabilityCostVolatilityFrontierConfig "
            "does not support subclassing",
        )

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchMarketProbabilityCostVolatilityFrontierConfig,
            "config",
        )
        _require_public_label("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_MARKET_PROBABILITY_COST_VOLATILITY_FRONTIER_REPORT_CONFIG_VERSION
        ):
            raise ValueError("config_version must match supported value")
        for field_name in (
            "minimum_pass_sanitized_edge_probability",
            "minimum_watch_sanitized_edge_probability",
            "maximum_pass_edge_stability_delta",
            "maximum_watch_edge_stability_delta",
            "maximum_pass_fee_pressure_ratio",
            "maximum_watch_fee_pressure_ratio",
            "maximum_pass_spread_pressure_ratio",
            "maximum_watch_spread_pressure_ratio",
            "maximum_pass_slippage_pressure_ratio",
            "maximum_watch_slippage_pressure_ratio",
            "maximum_pass_volatility_pressure_ratio",
            "maximum_watch_volatility_pressure_ratio",
            "maximum_pass_total_pressure_ratio",
            "maximum_watch_total_pressure_ratio",
            "minimum_pass_net_cost_adjusted_edge_probability",
            "minimum_watch_net_cost_adjusted_edge_probability",
            "minimum_pass_frontier_score",
            "minimum_watch_frontier_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        _require_minimum_pair(
            "sanitized_edge_probability",
            self.minimum_pass_sanitized_edge_probability,
            self.minimum_watch_sanitized_edge_probability,
        )
        _require_maximum_pair(
            "edge_stability_delta",
            self.maximum_pass_edge_stability_delta,
            self.maximum_watch_edge_stability_delta,
        )
        for name in (
            "fee_pressure_ratio",
            "spread_pressure_ratio",
            "slippage_pressure_ratio",
            "volatility_pressure_ratio",
            "total_pressure_ratio",
        ):
            _require_maximum_pair(
                name,
                getattr(self, f"maximum_pass_{name}"),
                getattr(self, f"maximum_watch_{name}"),
            )
        _require_minimum_pair(
            "net_cost_adjusted_edge_probability",
            self.minimum_pass_net_cost_adjusted_edge_probability,
            self.minimum_watch_net_cost_adjusted_edge_probability,
        )
        _require_minimum_pair(
            "frontier_score",
            self.minimum_pass_frontier_score,
            self.minimum_watch_frontier_score,
        )
        _require_hard_flags("config", self)
        _reject_unsafe_public_payload("config", self)


@dataclass(frozen=True)
class ResearchMarketProbabilityCostVolatilityFrontierInput:
    private_event_ref: str
    private_group_ref: str
    observed_at: datetime
    sanitized_probability_edge: Decimal
    prior_sanitized_probability_edge: Decimal
    fee_pressure_ratio: Decimal
    spread_pressure_ratio: Decimal
    slippage_pressure_ratio: Decimal
    volatility_pressure_ratio: Decimal
    reason_codes: tuple[str, ...] = ()
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchMarketProbabilityCostVolatilityFrontierInput "
            "does not support subclassing",
        )

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchMarketProbabilityCostVolatilityFrontierInput,
            "input",
        )
        for field_name in ("private_event_ref", "private_group_ref"):
            _require_private_ref(field_name, getattr(self, field_name))
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in (
            "sanitized_probability_edge",
            "prior_sanitized_probability_edge",
            "fee_pressure_ratio",
            "spread_pressure_ratio",
            "slippage_pressure_ratio",
            "volatility_pressure_ratio",
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
class ResearchMarketProbabilityCostVolatilityFrontierRow:
    public_row_ref: str
    observed_at: datetime
    sanitized_probability_edge: Decimal
    prior_sanitized_probability_edge: Decimal
    edge_stability_delta: Decimal
    edge_strength_score: Decimal
    edge_stability_score: Decimal
    fee_pressure_ratio: Decimal
    fee_pressure_score: Decimal
    spread_pressure_ratio: Decimal
    spread_pressure_score: Decimal
    slippage_pressure_ratio: Decimal
    slippage_pressure_score: Decimal
    volatility_pressure_ratio: Decimal
    volatility_pressure_score: Decimal
    total_pressure_ratio: Decimal
    total_pressure_score: Decimal
    net_cost_adjusted_edge_probability: Decimal
    net_cost_adjusted_edge_score: Decimal
    frontier_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchMarketProbabilityCostVolatilityFrontierRow "
            "does not support subclassing",
        )

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchMarketProbabilityCostVolatilityFrontierRow,
            "row",
        )
        _require_public_label("public_row_ref", self.public_row_ref)
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in (
            "sanitized_probability_edge",
            "prior_sanitized_probability_edge",
            "edge_stability_delta",
            "edge_strength_score",
            "edge_stability_score",
            "fee_pressure_ratio",
            "fee_pressure_score",
            "spread_pressure_ratio",
            "spread_pressure_score",
            "slippage_pressure_ratio",
            "slippage_pressure_score",
            "volatility_pressure_ratio",
            "volatility_pressure_score",
            "total_pressure_score",
            "net_cost_adjusted_edge_score",
            "frontier_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "total_pressure_ratio",
            _require_nonnegative_decimal(
                "total_pressure_ratio",
                self.total_pressure_ratio,
            ),
        )
        object.__setattr__(
            self,
            "net_cost_adjusted_edge_probability",
            _require_decimal(
                "net_cost_adjusted_edge_probability",
                self.net_cost_adjusted_edge_probability,
            ),
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
class ResearchMarketProbabilityCostVolatilityFrontierReasonCodeCount:
    reason_code: str
    count: Decimal
    row_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchMarketProbabilityCostVolatilityFrontierReasonCodeCount "
            "does not support subclassing",
        )

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchMarketProbabilityCostVolatilityFrontierReasonCodeCount,
            "reason_count",
        )
        _require_reason_code("reason_code", self.reason_code)
        object.__setattr__(
            self,
            "count",
            _require_nonnegative_count("count", self.count),
        )
        object.__setattr__(
            self,
            "row_ratio",
            _require_ratio_decimal("row_ratio", self.row_ratio),
        )
        _require_hard_flags("reason_count", self)
        _reject_unsafe_public_payload("reason_count", self)


@dataclass(frozen=True)
class ResearchMarketProbabilityCostVolatilityFrontierReport:
    generated_at: datetime
    config_version: str
    status: str
    input_count: Decimal
    row_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    weak_edge_strength_count: Decimal
    unstable_edge_count: Decimal
    high_fee_pressure_count: Decimal
    wide_spread_pressure_count: Decimal
    high_slippage_pressure_count: Decimal
    high_volatility_pressure_count: Decimal
    high_total_pressure_count: Decimal
    weak_net_cost_adjusted_edge_count: Decimal
    average_frontier_score: Decimal
    min_net_cost_adjusted_edge_probability: Decimal
    max_total_pressure_ratio: Decimal
    max_edge_stability_delta: Decimal
    reason_codes: tuple[str, ...]
    reason_code_counts: tuple[
        ResearchMarketProbabilityCostVolatilityFrontierReasonCodeCount,
        ...,
    ]
    rows: tuple[ResearchMarketProbabilityCostVolatilityFrontierRow, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchMarketProbabilityCostVolatilityFrontierReport "
            "does not support subclassing",
        )

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchMarketProbabilityCostVolatilityFrontierReport,
            "report",
        )
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_label("config_version", self.config_version)
        _require_status("status", self.status)
        for field_name in (
            "input_count",
            "row_count",
            "pass_count",
            "watch_count",
            "block_count",
            "weak_edge_strength_count",
            "unstable_edge_count",
            "high_fee_pressure_count",
            "wide_spread_pressure_count",
            "high_slippage_pressure_count",
            "high_volatility_pressure_count",
            "high_total_pressure_count",
            "weak_net_cost_adjusted_edge_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_count(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "average_frontier_score",
            _require_ratio_decimal("average_frontier_score", self.average_frontier_score),
        )
        for field_name in ("max_total_pressure_ratio", "max_edge_stability_delta"):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "min_net_cost_adjusted_edge_probability",
            _require_decimal(
                "min_net_cost_adjusted_edge_probability",
                self.min_net_cost_adjusted_edge_probability,
            ),
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


def build_research_market_probability_cost_volatility_frontier_report(
    inputs: Iterable[ResearchMarketProbabilityCostVolatilityFrontierInput],
    *,
    config: ResearchMarketProbabilityCostVolatilityFrontierConfig,
    generated_at: datetime,
) -> ResearchMarketProbabilityCostVolatilityFrontierReport:
    if type(config) is not ResearchMarketProbabilityCostVolatilityFrontierConfig:
        raise ValueError(
            "config must be a ResearchMarketProbabilityCostVolatilityFrontierConfig",
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
                    _private_digest(value.private_event_ref, value.private_group_ref),
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
                        public_row_ref=_public_row_ref(index),
                    ),
                )
                for index, (private_digest, value) in enumerate(keyed_inputs, start=1)
            ),
            key=lambda item: _row_sort_key(item[1]),
        ),
    )
    rows = tuple(row for _, row in keyed_rows)
    return ResearchMarketProbabilityCostVolatilityFrontierReport(
        generated_at=generated_at,
        config_version=config.config_version,
        status=_report_status(rows),
        input_count=_count_decimal(len(normalized)),
        row_count=_count_decimal(len(rows)),
        pass_count=_status_count(rows, PASS_STATUS),
        watch_count=_status_count(rows, WATCH_STATUS),
        block_count=_status_count(rows, BLOCK_STATUS),
        weak_edge_strength_count=_non_pass_reason_count(
            rows,
            "frontier_edge_strength",
        ),
        unstable_edge_count=_non_pass_reason_count(rows, "frontier_edge_stability"),
        high_fee_pressure_count=_non_pass_reason_count(rows, "frontier_fee_pressure"),
        wide_spread_pressure_count=_non_pass_reason_count(
            rows,
            "frontier_spread_pressure",
        ),
        high_slippage_pressure_count=_non_pass_reason_count(
            rows,
            "frontier_slippage_pressure",
        ),
        high_volatility_pressure_count=_non_pass_reason_count(
            rows,
            "frontier_volatility_pressure",
        ),
        high_total_pressure_count=_non_pass_reason_count(
            rows,
            "frontier_total_pressure",
        ),
        weak_net_cost_adjusted_edge_count=_non_pass_reason_count(
            rows,
            "frontier_net_cost_adjusted_edge",
        ),
        average_frontier_score=_average_row_decimal(rows, "frontier_score"),
        min_net_cost_adjusted_edge_probability=_min_row_decimal(
            rows,
            "net_cost_adjusted_edge_probability",
        ),
        max_total_pressure_ratio=_max_row_decimal(rows, "total_pressure_ratio"),
        max_edge_stability_delta=_max_row_decimal(rows, "edge_stability_delta"),
        reason_codes=_report_reason_codes(rows),
        reason_code_counts=_report_reason_code_counts(rows),
        rows=rows,
    )


def research_market_probability_cost_volatility_frontier_report_payload(
    report: ResearchMarketProbabilityCostVolatilityFrontierReport,
) -> dict[str, Any]:
    if type(report) is not ResearchMarketProbabilityCostVolatilityFrontierReport:
        raise ValueError(
            "report must be a ResearchMarketProbabilityCostVolatilityFrontierReport",
        )
    _require_hard_flags("report", report)
    _reject_unsafe_public_payload("report", report)
    payload = _json_value(report)
    if type(payload) is not dict:
        raise ValueError("report must serialize to a JSON object")
    validate_research_market_probability_cost_volatility_frontier_report_payload(payload)
    return payload


def validate_research_market_probability_cost_volatility_frontier_report_payload(
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
    value: ResearchMarketProbabilityCostVolatilityFrontierInput,
    *,
    config: ResearchMarketProbabilityCostVolatilityFrontierConfig,
    public_row_ref: str,
) -> ResearchMarketProbabilityCostVolatilityFrontierRow:
    edge_stability_delta = _quantize_decimal(
        abs(value.sanitized_probability_edge - value.prior_sanitized_probability_edge),
    )
    total_pressure_ratio = _quantize_decimal(
        value.fee_pressure_ratio
        + value.spread_pressure_ratio
        + value.slippage_pressure_ratio
        + value.volatility_pressure_ratio,
    )
    net_cost_adjusted_edge_probability = _quantize_decimal(
        value.sanitized_probability_edge
        - value.fee_pressure_ratio
        - value.spread_pressure_ratio
        - value.slippage_pressure_ratio,
    )
    edge_strength_score = _score_for_minimum(
        value.sanitized_probability_edge,
        config.minimum_pass_sanitized_edge_probability,
        config.minimum_watch_sanitized_edge_probability,
    )
    edge_stability_score = _score_for_maximum(
        edge_stability_delta,
        config.maximum_pass_edge_stability_delta,
        config.maximum_watch_edge_stability_delta,
    )
    fee_pressure_score = _score_for_maximum(
        value.fee_pressure_ratio,
        config.maximum_pass_fee_pressure_ratio,
        config.maximum_watch_fee_pressure_ratio,
    )
    spread_pressure_score = _score_for_maximum(
        value.spread_pressure_ratio,
        config.maximum_pass_spread_pressure_ratio,
        config.maximum_watch_spread_pressure_ratio,
    )
    slippage_pressure_score = _score_for_maximum(
        value.slippage_pressure_ratio,
        config.maximum_pass_slippage_pressure_ratio,
        config.maximum_watch_slippage_pressure_ratio,
    )
    volatility_pressure_score = _score_for_maximum(
        value.volatility_pressure_ratio,
        config.maximum_pass_volatility_pressure_ratio,
        config.maximum_watch_volatility_pressure_ratio,
    )
    total_pressure_score = _score_for_maximum(
        total_pressure_ratio,
        config.maximum_pass_total_pressure_ratio,
        config.maximum_watch_total_pressure_ratio,
    )
    net_cost_adjusted_edge_score = _score_for_minimum(
        net_cost_adjusted_edge_probability,
        config.minimum_pass_net_cost_adjusted_edge_probability,
        config.minimum_watch_net_cost_adjusted_edge_probability,
    )
    frontier_score = _frontier_score(
        edge_strength_score=edge_strength_score,
        edge_stability_score=edge_stability_score,
        fee_pressure_score=fee_pressure_score,
        spread_pressure_score=spread_pressure_score,
        slippage_pressure_score=slippage_pressure_score,
        volatility_pressure_score=volatility_pressure_score,
        total_pressure_score=total_pressure_score,
        net_cost_adjusted_edge_score=net_cost_adjusted_edge_score,
    )
    component_statuses = (
        _status_for_minimum(
            value.sanitized_probability_edge,
            config.minimum_pass_sanitized_edge_probability,
            config.minimum_watch_sanitized_edge_probability,
        ),
        _status_for_maximum(
            edge_stability_delta,
            config.maximum_pass_edge_stability_delta,
            config.maximum_watch_edge_stability_delta,
        ),
        _status_for_maximum(
            value.fee_pressure_ratio,
            config.maximum_pass_fee_pressure_ratio,
            config.maximum_watch_fee_pressure_ratio,
        ),
        _status_for_maximum(
            value.spread_pressure_ratio,
            config.maximum_pass_spread_pressure_ratio,
            config.maximum_watch_spread_pressure_ratio,
        ),
        _status_for_maximum(
            value.slippage_pressure_ratio,
            config.maximum_pass_slippage_pressure_ratio,
            config.maximum_watch_slippage_pressure_ratio,
        ),
        _status_for_maximum(
            value.volatility_pressure_ratio,
            config.maximum_pass_volatility_pressure_ratio,
            config.maximum_watch_volatility_pressure_ratio,
        ),
        _status_for_maximum(
            total_pressure_ratio,
            config.maximum_pass_total_pressure_ratio,
            config.maximum_watch_total_pressure_ratio,
        ),
        _status_for_minimum(
            net_cost_adjusted_edge_probability,
            config.minimum_pass_net_cost_adjusted_edge_probability,
            config.minimum_watch_net_cost_adjusted_edge_probability,
        ),
    )
    status = _frontier_status(
        component_statuses=component_statuses,
        frontier_score=frontier_score,
        config=config,
    )
    return ResearchMarketProbabilityCostVolatilityFrontierRow(
        public_row_ref=public_row_ref,
        observed_at=value.observed_at,
        sanitized_probability_edge=value.sanitized_probability_edge,
        prior_sanitized_probability_edge=value.prior_sanitized_probability_edge,
        edge_stability_delta=edge_stability_delta,
        edge_strength_score=edge_strength_score,
        edge_stability_score=edge_stability_score,
        fee_pressure_ratio=value.fee_pressure_ratio,
        fee_pressure_score=fee_pressure_score,
        spread_pressure_ratio=value.spread_pressure_ratio,
        spread_pressure_score=spread_pressure_score,
        slippage_pressure_ratio=value.slippage_pressure_ratio,
        slippage_pressure_score=slippage_pressure_score,
        volatility_pressure_ratio=value.volatility_pressure_ratio,
        volatility_pressure_score=volatility_pressure_score,
        total_pressure_ratio=total_pressure_ratio,
        total_pressure_score=total_pressure_score,
        net_cost_adjusted_edge_probability=net_cost_adjusted_edge_probability,
        net_cost_adjusted_edge_score=net_cost_adjusted_edge_score,
        frontier_score=frontier_score,
        status=status,
        reason_codes=_row_reason_codes(
            value.reason_codes,
            status=status,
            edge_strength_status=component_statuses[0],
            edge_stability_status=component_statuses[1],
            fee_pressure_status=component_statuses[2],
            spread_pressure_status=component_statuses[3],
            slippage_pressure_status=component_statuses[4],
            volatility_pressure_status=component_statuses[5],
            total_pressure_status=component_statuses[6],
            net_cost_adjusted_edge_status=component_statuses[7],
        ),
    )


def _frontier_score(
    *,
    edge_strength_score: Decimal,
    edge_stability_score: Decimal,
    fee_pressure_score: Decimal,
    spread_pressure_score: Decimal,
    slippage_pressure_score: Decimal,
    volatility_pressure_score: Decimal,
    total_pressure_score: Decimal,
    net_cost_adjusted_edge_score: Decimal,
) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return _quantize_decimal(
            (
                edge_strength_score
                + edge_stability_score
                + fee_pressure_score
                + spread_pressure_score
                + slippage_pressure_score
                + volatility_pressure_score
                + total_pressure_score
                + net_cost_adjusted_edge_score
            )
            / EIGHT,
        )


def _frontier_status(
    *,
    component_statuses: tuple[str, ...],
    frontier_score: Decimal,
    config: ResearchMarketProbabilityCostVolatilityFrontierConfig,
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
    edge_strength_status: str,
    edge_stability_status: str,
    fee_pressure_status: str,
    spread_pressure_status: str,
    slippage_pressure_status: str,
    volatility_pressure_status: str,
    total_pressure_status: str,
    net_cost_adjusted_edge_status: str,
) -> tuple[str, ...]:
    reason_codes = [f"input_{reason_code}" for reason_code in input_reason_codes]
    reason_codes.extend(
        (
            f"frontier_status_{status}",
            f"frontier_edge_strength_{edge_strength_status}",
            f"frontier_edge_stability_{edge_stability_status}",
            f"frontier_fee_pressure_{fee_pressure_status}",
            f"frontier_spread_pressure_{spread_pressure_status}",
            f"frontier_slippage_pressure_{slippage_pressure_status}",
            f"frontier_volatility_pressure_{volatility_pressure_status}",
            f"frontier_total_pressure_{total_pressure_status}",
            f"frontier_net_cost_adjusted_edge_{net_cost_adjusted_edge_status}",
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
    inputs: Iterable[ResearchMarketProbabilityCostVolatilityFrontierInput],
) -> tuple[ResearchMarketProbabilityCostVolatilityFrontierInput, ...]:
    if isinstance(inputs, (str, bytes)) or not isinstance(inputs, Iterable):
        raise ValueError("inputs must be an iterable")
    normalized = tuple(inputs)
    for value in normalized:
        if type(value) is not ResearchMarketProbabilityCostVolatilityFrontierInput:
            raise ValueError(
                "inputs must contain ResearchMarketProbabilityCostVolatilityFrontierInput",
            )
        _require_hard_flags("input", value)
    return normalized


def _normalize_rows(
    rows: Iterable[ResearchMarketProbabilityCostVolatilityFrontierRow],
) -> tuple[ResearchMarketProbabilityCostVolatilityFrontierRow, ...]:
    if isinstance(rows, (str, bytes)) or not isinstance(rows, Iterable):
        raise ValueError("rows must be an iterable")
    normalized = tuple(rows)
    for row in normalized:
        if type(row) is not ResearchMarketProbabilityCostVolatilityFrontierRow:
            raise ValueError(
                "rows must contain ResearchMarketProbabilityCostVolatilityFrontierRow",
            )
        _require_hard_flags("row", row)
    return tuple(sorted(normalized, key=_row_sort_key))


def _normalize_reason_code_counts(
    counts: Iterable[ResearchMarketProbabilityCostVolatilityFrontierReasonCodeCount],
) -> tuple[ResearchMarketProbabilityCostVolatilityFrontierReasonCodeCount, ...]:
    if isinstance(counts, (str, bytes)) or not isinstance(counts, Iterable):
        raise ValueError("reason_code_counts must be an iterable")
    normalized = tuple(counts)
    for count in normalized:
        if (
            type(count)
            is not ResearchMarketProbabilityCostVolatilityFrontierReasonCodeCount
        ):
            raise ValueError(
                "reason_code_counts must contain "
                "ResearchMarketProbabilityCostVolatilityFrontierReasonCodeCount",
            )
        _require_hard_flags("reason_count", count)
    return tuple(sorted(normalized, key=lambda item: (-item.count, item.reason_code)))


def _validate_row_consistency(
    row: ResearchMarketProbabilityCostVolatilityFrontierRow,
) -> None:
    if f"frontier_status_{row.status}" not in row.reason_codes:
        raise ValueError("status must match reason_codes")
    if row.edge_stability_delta != _quantize_decimal(
        abs(row.sanitized_probability_edge - row.prior_sanitized_probability_edge),
    ):
        raise ValueError("edge_stability_delta must match edge values")
    expected_total_pressure_ratio = _quantize_decimal(
        row.fee_pressure_ratio
        + row.spread_pressure_ratio
        + row.slippage_pressure_ratio
        + row.volatility_pressure_ratio,
    )
    if row.total_pressure_ratio != expected_total_pressure_ratio:
        raise ValueError("total_pressure_ratio must match pressure fields")
    expected_net_edge = _quantize_decimal(
        row.sanitized_probability_edge
        - row.fee_pressure_ratio
        - row.spread_pressure_ratio
        - row.slippage_pressure_ratio,
    )
    if row.net_cost_adjusted_edge_probability != expected_net_edge:
        raise ValueError(
            "net_cost_adjusted_edge_probability must match direct pressure fields",
        )
    expected_frontier_score = _frontier_score(
        edge_strength_score=row.edge_strength_score,
        edge_stability_score=row.edge_stability_score,
        fee_pressure_score=row.fee_pressure_score,
        spread_pressure_score=row.spread_pressure_score,
        slippage_pressure_score=row.slippage_pressure_score,
        volatility_pressure_score=row.volatility_pressure_score,
        total_pressure_score=row.total_pressure_score,
        net_cost_adjusted_edge_score=row.net_cost_adjusted_edge_score,
    )
    if row.frontier_score != expected_frontier_score:
        raise ValueError("frontier_score must match component scores")


def _validate_report_consistency(
    report: ResearchMarketProbabilityCostVolatilityFrontierReport,
) -> None:
    if report.input_count != report.row_count:
        raise ValueError("input_count must match row_count")
    if report.row_count != _count_decimal(len(report.rows)):
        raise ValueError("row_count must match rows")
    if report.pass_count + report.watch_count + report.block_count != report.row_count:
        raise ValueError("status counts must match row_count")
    expected_counts = {
        "weak_edge_strength_count": _non_pass_reason_count(
            report.rows,
            "frontier_edge_strength",
        ),
        "unstable_edge_count": _non_pass_reason_count(
            report.rows,
            "frontier_edge_stability",
        ),
        "high_fee_pressure_count": _non_pass_reason_count(
            report.rows,
            "frontier_fee_pressure",
        ),
        "wide_spread_pressure_count": _non_pass_reason_count(
            report.rows,
            "frontier_spread_pressure",
        ),
        "high_slippage_pressure_count": _non_pass_reason_count(
            report.rows,
            "frontier_slippage_pressure",
        ),
        "high_volatility_pressure_count": _non_pass_reason_count(
            report.rows,
            "frontier_volatility_pressure",
        ),
        "high_total_pressure_count": _non_pass_reason_count(
            report.rows,
            "frontier_total_pressure",
        ),
        "weak_net_cost_adjusted_edge_count": _non_pass_reason_count(
            report.rows,
            "frontier_net_cost_adjusted_edge",
        ),
        "average_frontier_score": _average_row_decimal(report.rows, "frontier_score"),
        "min_net_cost_adjusted_edge_probability": _min_row_decimal(
            report.rows,
            "net_cost_adjusted_edge_probability",
        ),
        "max_total_pressure_ratio": _max_row_decimal(report.rows, "total_pressure_ratio"),
        "max_edge_stability_delta": _max_row_decimal(report.rows, "edge_stability_delta"),
    }
    for field_name, expected_value in expected_counts.items():
        if getattr(report, field_name) != expected_value:
            raise ValueError(f"{field_name} must match rows")
    if report.status != _report_status(report.rows):
        raise ValueError("status must match rows")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")
    if report.reason_code_counts != _report_reason_code_counts(report.rows):
        raise ValueError("reason_code_counts must match rows")


def _report_status(
    rows: tuple[ResearchMarketProbabilityCostVolatilityFrontierRow, ...],
) -> str:
    if not rows:
        return BLOCK_STATUS
    if any(row.status == BLOCK_STATUS for row in rows):
        return BLOCK_STATUS
    if any(row.status == WATCH_STATUS for row in rows):
        return WATCH_STATUS
    return PASS_STATUS


def _report_reason_codes(
    rows: tuple[ResearchMarketProbabilityCostVolatilityFrontierRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return ("frontier_no_inputs",)
    reason_codes: list[str] = []
    for row in rows:
        reason_codes.extend(row.reason_codes)
    return _normalize_reason_codes("reason_codes", tuple(reason_codes))


def _report_reason_code_counts(
    rows: tuple[ResearchMarketProbabilityCostVolatilityFrontierRow, ...],
) -> tuple[ResearchMarketProbabilityCostVolatilityFrontierReasonCodeCount, ...]:
    counts: dict[str, Decimal] = {}
    report_reason_codes = _report_reason_codes(rows)
    for reason_code in report_reason_codes:
        counts[reason_code] = ZERO
    if not rows:
        counts["frontier_no_inputs"] = ONE
    for row in rows:
        for reason_code in row.reason_codes:
            counts[reason_code] = _quantize_decimal(counts.get(reason_code, ZERO) + ONE)
    row_count = _count_decimal(len(rows))
    return tuple(
        sorted(
            (
                ResearchMarketProbabilityCostVolatilityFrontierReasonCodeCount(
                    reason_code=reason_code,
                    count=count,
                    row_ratio=_row_ratio(count, row_count),
                )
                for reason_code, count in counts.items()
            ),
            key=lambda item: (-item.count, item.reason_code),
        ),
    )


def _status_count(
    rows: tuple[ResearchMarketProbabilityCostVolatilityFrontierRow, ...],
    status: str,
) -> Decimal:
    return _count_decimal(sum(1 for row in rows if row.status == status))


def _non_pass_reason_count(
    rows: tuple[ResearchMarketProbabilityCostVolatilityFrontierRow, ...],
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
    rows: tuple[ResearchMarketProbabilityCostVolatilityFrontierRow, ...],
    field_name: str,
) -> Decimal:
    if not rows:
        return ZERO
    return max(getattr(row, field_name) for row in rows)


def _min_row_decimal(
    rows: tuple[ResearchMarketProbabilityCostVolatilityFrontierRow, ...],
    field_name: str,
) -> Decimal:
    if not rows:
        return ZERO
    return min(getattr(row, field_name) for row in rows)


def _average_row_decimal(
    rows: tuple[ResearchMarketProbabilityCostVolatilityFrontierRow, ...],
    field_name: str,
) -> Decimal:
    if not rows:
        return ZERO
    total = ZERO
    for row in rows:
        total = _quantize_decimal(total + getattr(row, field_name))
    with localcontext(DECIMAL_CONTEXT):
        return _quantize_decimal(total / Decimal(len(rows)))


def _row_ratio(count: Decimal, row_count: Decimal) -> Decimal:
    if row_count == ZERO:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return _quantize_decimal(count / row_count)


def _count_decimal(value: int) -> Decimal:
    return _quantize_decimal(Decimal(value))


def _require_minimum_pair(name: str, pass_value: Decimal, watch_value: Decimal) -> None:
    if pass_value < watch_value:
        raise ValueError(f"pass {name} must be at least watch")


def _require_maximum_pair(name: str, pass_value: Decimal, watch_value: Decimal) -> None:
    if pass_value > watch_value:
        raise ValueError(f"pass {name} must not exceed watch")


def _require_ratio_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_nonnegative_decimal(field_name, value)
    if normalized > ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return normalized


def _require_nonnegative_count(field_name: str, value: object) -> Decimal:
    normalized = _require_nonnegative_decimal(field_name, value)
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{field_name} must be integral")
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
    if type(value) is not str or value not in PROBABILITY_COST_VOLATILITY_FRONTIER_STATUSES:
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


def _row_sort_key(
    row: ResearchMarketProbabilityCostVolatilityFrontierRow,
) -> tuple[Decimal, Decimal, Decimal, str]:
    return (
        STATUS_RANK[row.status],
        row.frontier_score,
        row.net_cost_adjusted_edge_probability,
        row.public_row_ref,
    )


def _private_digest(*parts: str) -> str:
    return sha256("\x1f".join(parts).encode("utf-8")).hexdigest()


def _public_row_ref(index: int) -> str:
    return f"frontier_row_{index:03d}"


def _report_derived_validation_digest(
    report: ResearchMarketProbabilityCostVolatilityFrontierReport,
) -> str:
    return _payload_derived_validation_digest(_public_payload_without_digest(report))


def _public_payload_without_digest(
    report: ResearchMarketProbabilityCostVolatilityFrontierReport,
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
