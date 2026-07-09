"""Report-only cost, liquidity, and edge-decay ladder reducer."""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable
from dataclasses import asdict, dataclass, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal, localcontext
import hashlib
import json
from typing import Any

from polymarket_alpha_lab.team_paper_guard import (
    reject_unsafe_surface_fields,
    require_paper_only_flags,
)


DEFAULT_RESEARCH_MARKET_COST_LIQUIDITY_EDGE_DECAY_LADDER_REPORT_CONFIG_VERSION = (
    "research-market-cost-liquidity-edge-decay-ladder-report-v0"
)
MARKET_COST_LIQUIDITY_EDGE_DECAY_LADDER_STATUSES = ("pass", "watch", "block")
QUANTUM = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
DECIMAL_CONTEXT_PRECISION = 28
STATUS_WEIGHT = {"block": 0, "watch": 1, "pass": 2}
REPORT_REASON_PRIORITY = (
    "edge_shortfall_block",
    "cost_drag_block",
    "liquidity_shortfall_block",
    "edge_decay_block",
    "edge_shortfall_watch",
    "cost_drag_watch",
    "liquidity_shortfall_watch",
    "edge_decay_watch",
)


def _join_parts(*parts: str) -> str:
    return "".join(parts)


UNSAFE_PUBLIC_FRAGMENTS = (
    _join_parts("ra", "w"),
    _join_parts("can", "didate"),
    _join_parts("ma", "rket", "_", "id"),
    _join_parts("ma", "rket", "-", "sl", "ug"),
    _join_parts("ma", "rket", "_", "sl", "ug"),
    _join_parts("ques", "tion"),
    _join_parts("sour", "ce", "_", "url"),
    _join_parts("sour", "ce", "_", "text"),
    _join_parts("d", "sn"),
    _join_parts("tab", "le", "_", "name"),
    _join_parts("tok", "en"),
    _join_parts("wal", "let"),
    _join_parts("au", "th"),
    _join_parts("or", "der"),
    _join_parts("tra", "de"),
    _join_parts("pos", "ition"),
    _join_parts("siz", "ing"),
    _join_parts("reco", "mmend"),
    _join_parts("bu", "y"),
    _join_parts("se", "ll"),
    "://",
)


@dataclass(frozen=True)
class ResearchMarketCostLiquidityEdgeDecayLadderConfig:
    config_version: str = (
        DEFAULT_RESEARCH_MARKET_COST_LIQUIDITY_EDGE_DECAY_LADDER_REPORT_CONFIG_VERSION
    )
    min_pass_net_edge_ratio: Decimal = Decimal("0.050000")
    min_watch_net_edge_ratio: Decimal = Decimal("0.020000")
    max_pass_cost_ratio: Decimal = Decimal("0.015000")
    max_watch_cost_ratio: Decimal = Decimal("0.050000")
    min_pass_liquidity_score: Decimal = Decimal("0.700000")
    min_watch_liquidity_score: Decimal = Decimal("0.300000")
    max_pass_decay_ratio: Decimal = Decimal("0.250000")
    max_watch_decay_ratio: Decimal = Decimal("0.600000")
    edge_weight: Decimal = Decimal("0.400000")
    cost_weight: Decimal = Decimal("0.250000")
    liquidity_weight: Decimal = Decimal("0.200000")
    decay_weight: Decimal = Decimal("0.150000")
    max_pass_ladder_risk_score: Decimal = Decimal("0.300000")
    max_watch_ladder_risk_score: Decimal = Decimal("0.700000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchMarketCostLiquidityEdgeDecayLadderConfig does not support "
            "subclassing",
        )

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchMarketCostLiquidityEdgeDecayLadderConfig,
            "config",
        )
        _require_public_label("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_MARKET_COST_LIQUIDITY_EDGE_DECAY_LADDER_REPORT_CONFIG_VERSION
        ):
            raise ValueError("config_version must match supported value")
        for field_name in (
            "min_pass_net_edge_ratio",
            "min_watch_net_edge_ratio",
            "max_pass_cost_ratio",
            "max_watch_cost_ratio",
            "min_pass_liquidity_score",
            "min_watch_liquidity_score",
            "max_pass_decay_ratio",
            "max_watch_decay_ratio",
            "edge_weight",
            "cost_weight",
            "liquidity_weight",
            "decay_weight",
            "max_pass_ladder_risk_score",
            "max_watch_ladder_risk_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        if self.min_pass_net_edge_ratio <= self.min_watch_net_edge_ratio:
            raise ValueError("min_pass_net_edge_ratio must exceed watch")
        if self.max_pass_cost_ratio >= self.max_watch_cost_ratio:
            raise ValueError("max_pass_cost_ratio must be below watch")
        if self.min_pass_liquidity_score <= self.min_watch_liquidity_score:
            raise ValueError("min_pass_liquidity_score must exceed watch")
        if self.max_pass_decay_ratio >= self.max_watch_decay_ratio:
            raise ValueError("max_pass_decay_ratio must be below watch")
        if self.max_pass_ladder_risk_score >= self.max_watch_ladder_risk_score:
            raise ValueError("max_pass_ladder_risk_score must be below watch")
        weight_sum = _quantize(
            self.edge_weight
            + self.cost_weight
            + self.liquidity_weight
            + self.decay_weight,
        )
        if weight_sum != ONE:
            raise ValueError("ladder weights must sum to 1")
        _require_hard_flags("config", self)
        _reject_unsafe_public_payload("config", self)


@dataclass(frozen=True)
class ResearchMarketCostLiquidityEdgeDecayLadderInput:
    public_ladder_ref: str
    observed_at: datetime
    gross_edge_ratio: Decimal
    fee_rate: Decimal
    spread_ratio: Decimal
    slippage_ratio: Decimal
    liquidity_score: Decimal
    edge_decay_ratio: Decimal
    reason_codes: tuple[str, ...] = ()
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchMarketCostLiquidityEdgeDecayLadderInput does not support "
            "subclassing",
        )

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchMarketCostLiquidityEdgeDecayLadderInput, "input")
        _require_public_label("public_ladder_ref", self.public_ladder_ref)
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in (
            "gross_edge_ratio",
            "fee_rate",
            "spread_ratio",
            "slippage_ratio",
            "liquidity_score",
            "edge_decay_ratio",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(
                "reason_codes",
                self.reason_codes,
                allow_empty=True,
            ),
        )
        _require_hard_flags("input", self)
        _reject_unsafe_public_payload("input", self)


@dataclass(frozen=True)
class ResearchMarketCostLiquidityEdgeDecayLadderRow:
    public_ladder_ref: str
    observed_at: datetime
    gross_edge_ratio: Decimal
    fee_rate: Decimal
    spread_ratio: Decimal
    slippage_ratio: Decimal
    total_cost_ratio: Decimal
    net_edge_ratio: Decimal
    liquidity_score: Decimal
    edge_decay_ratio: Decimal
    edge_shortfall_score: Decimal
    cost_drag_score: Decimal
    liquidity_shortfall_score: Decimal
    decay_pressure_score: Decimal
    ladder_risk_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchMarketCostLiquidityEdgeDecayLadderRow does not support subclassing",
        )

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchMarketCostLiquidityEdgeDecayLadderRow, "row")
        _require_public_label("public_ladder_ref", self.public_ladder_ref)
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in (
            "gross_edge_ratio",
            "fee_rate",
            "spread_ratio",
            "slippage_ratio",
            "total_cost_ratio",
            "net_edge_ratio",
            "liquidity_score",
            "edge_decay_ratio",
            "edge_shortfall_score",
            "cost_drag_score",
            "liquidity_shortfall_score",
            "decay_pressure_score",
            "ladder_risk_score",
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
            _normalize_reason_codes(
                "reason_codes",
                self.reason_codes,
                allow_empty=False,
            ),
        )
        _require_hard_flags("row", self)
        _reject_unsafe_public_payload("row", self)
        _validate_row(self)


@dataclass(frozen=True)
class ResearchMarketCostLiquidityEdgeDecayLadderReasonCodeCount:
    reason_code: str
    count: Decimal
    row_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchMarketCostLiquidityEdgeDecayLadderReasonCodeCount does not support "
            "subclassing",
        )

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchMarketCostLiquidityEdgeDecayLadderReasonCodeCount,
            "reason code count",
        )
        _require_public_label("reason_code", self.reason_code)
        object.__setattr__(
            self,
            "count",
            _require_nonnegative_decimal("count", self.count),
        )
        object.__setattr__(
            self,
            "row_ratio",
            _require_ratio_decimal("row_ratio", self.row_ratio),
        )
        _require_hard_flags("reason code count", self)
        _reject_unsafe_public_payload("reason code count", self)


@dataclass(frozen=True)
class ResearchMarketCostLiquidityEdgeDecayLadderReport:
    generated_at: datetime
    config_version: str
    input_count: Decimal
    row_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    average_ladder_risk_score: Decimal | None
    max_ladder_risk_score: Decimal
    max_total_cost_ratio: Decimal
    max_edge_decay_ratio: Decimal
    min_net_edge_ratio: Decimal
    min_liquidity_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    reason_code_counts: tuple[ResearchMarketCostLiquidityEdgeDecayLadderReasonCodeCount, ...]
    rows: tuple[ResearchMarketCostLiquidityEdgeDecayLadderRow, ...]
    derived_validation_digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchMarketCostLiquidityEdgeDecayLadderReport does not support "
            "subclassing",
        )

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchMarketCostLiquidityEdgeDecayLadderReport, "report")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_label("config_version", self.config_version)
        for field_name in (
            "input_count",
            "row_count",
            "pass_count",
            "watch_count",
            "block_count",
            "max_ladder_risk_score",
            "max_total_cost_ratio",
            "max_edge_decay_ratio",
            "min_net_edge_ratio",
            "min_liquidity_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        if self.average_ladder_risk_score is not None:
            object.__setattr__(
                self,
                "average_ladder_risk_score",
                _require_ratio_decimal(
                    "average_ladder_risk_score",
                    self.average_ladder_risk_score,
                ),
            )
        _require_status("status", self.status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(
                "reason_codes",
                self.reason_codes,
                allow_empty=False,
            ),
        )
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        _require_sha256_digest("derived_validation_digest", self.derived_validation_digest)
        _require_hard_flags("report", self)
        reject_unsafe_surface_fields("cost liquidity edge decay ladder report", self)
        _reject_unsafe_public_payload("report", self)
        _validate_report(self)
        if self.derived_validation_digest != _report_derived_validation_digest(self):
            raise ValueError("derived_validation_digest must match report payload")

    @property
    def payload(self) -> dict[str, Any]:
        return research_market_cost_liquidity_edge_decay_ladder_report_payload(self)


@dataclass(frozen=True)
class ResearchMarketCostLiquidityEdgeDecayLadderReportDigest:
    generated_at: datetime
    config_version: str
    report_digest: str
    report_status: str
    input_count: Decimal
    row_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    average_ladder_risk_score: Decimal | None
    max_ladder_risk_score: Decimal
    max_total_cost_ratio: Decimal
    max_edge_decay_ratio: Decimal
    min_net_edge_ratio: Decimal
    min_liquidity_score: Decimal
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchMarketCostLiquidityEdgeDecayLadderReportDigest does not support "
            "subclassing",
        )

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchMarketCostLiquidityEdgeDecayLadderReportDigest,
            "digest",
        )
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_label("config_version", self.config_version)
        _require_sha256_digest("report_digest", self.report_digest)
        _require_status("report_status", self.report_status)
        for field_name in (
            "input_count",
            "row_count",
            "pass_count",
            "watch_count",
            "block_count",
            "max_ladder_risk_score",
            "max_total_cost_ratio",
            "max_edge_decay_ratio",
            "min_net_edge_ratio",
            "min_liquidity_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        if self.average_ladder_risk_score is not None:
            object.__setattr__(
                self,
                "average_ladder_risk_score",
                _require_ratio_decimal(
                    "average_ladder_risk_score",
                    self.average_ladder_risk_score,
                ),
            )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(
                "reason_codes",
                self.reason_codes,
                allow_empty=False,
            ),
        )
        _require_hard_flags("digest", self)
        reject_unsafe_surface_fields("cost liquidity edge decay ladder digest", self)
        _reject_unsafe_public_payload("digest", self)

    @property
    def payload(self) -> dict[str, Any]:
        return research_market_cost_liquidity_edge_decay_ladder_report_payload(self)


def build_research_market_cost_liquidity_edge_decay_ladder_report(
    inputs: Iterable[ResearchMarketCostLiquidityEdgeDecayLadderInput],
    *,
    config: ResearchMarketCostLiquidityEdgeDecayLadderConfig,
    generated_at: datetime,
) -> ResearchMarketCostLiquidityEdgeDecayLadderReport:
    if type(config) is not ResearchMarketCostLiquidityEdgeDecayLadderConfig:
        raise ValueError(
            "config must be a ResearchMarketCostLiquidityEdgeDecayLadderConfig",
        )
    _require_hard_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    normalized = _normalize_inputs(inputs, generated_at_utc)
    rows = tuple(
        sorted(
            (_row_for_input(item, config) for item in normalized),
            key=_row_key,
        ),
    )
    values: dict[str, object] = {
        "generated_at": generated_at_utc,
        "config_version": config.config_version,
        "input_count": _decimal_count(len(normalized)),
        "row_count": _decimal_count(len(rows)),
        "pass_count": _status_count(rows, "pass"),
        "watch_count": _status_count(rows, "watch"),
        "block_count": _status_count(rows, "block"),
        "average_ladder_risk_score": _average_score(rows),
        "max_ladder_risk_score": _max_decimal(rows, "ladder_risk_score"),
        "max_total_cost_ratio": _max_decimal(rows, "total_cost_ratio"),
        "max_edge_decay_ratio": _max_decimal(rows, "edge_decay_ratio"),
        "min_net_edge_ratio": _min_decimal(rows, "net_edge_ratio"),
        "min_liquidity_score": _min_decimal(rows, "liquidity_score"),
        "status": _report_status(rows),
        "reason_codes": _report_reason_codes(rows),
        "reason_code_counts": _reason_code_counts(rows),
        "rows": rows,
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    return ResearchMarketCostLiquidityEdgeDecayLadderReport(
        **values,
        derived_validation_digest=_derived_validation_digest(values),
    )


def research_market_cost_liquidity_edge_decay_ladder_report_payload(
    value: ResearchMarketCostLiquidityEdgeDecayLadderReport
    | ResearchMarketCostLiquidityEdgeDecayLadderReportDigest
    | dict[str, Any],
) -> dict[str, Any]:
    if type(value) is ResearchMarketCostLiquidityEdgeDecayLadderReport:
        _require_hard_flags("report", value)
        if value.derived_validation_digest != _report_derived_validation_digest(value):
            raise ValueError("derived_validation_digest must match report payload")
        payload = _json_ready(value)
    elif type(value) is ResearchMarketCostLiquidityEdgeDecayLadderReportDigest:
        _require_hard_flags("digest", value)
        payload = _json_ready(value)
    elif type(value) is dict:
        payload = _json_ready(value)
    else:
        raise ValueError(
            "value must be a ResearchMarketCostLiquidityEdgeDecayLadderReport",
        )
    if type(payload) is not dict:
        raise ValueError("payload must be a JSON object")
    _require_hard_flags("payload", _DictFlags(payload))
    reject_unsafe_surface_fields("cost liquidity edge decay ladder payload", payload)
    _reject_unsafe_public_payload("payload", payload)
    _validate_payload_digest(payload)
    return payload


def research_market_cost_liquidity_edge_decay_ladder_report_digest(
    report: ResearchMarketCostLiquidityEdgeDecayLadderReport,
) -> ResearchMarketCostLiquidityEdgeDecayLadderReportDigest:
    if type(report) is not ResearchMarketCostLiquidityEdgeDecayLadderReport:
        raise ValueError(
            "report must be a ResearchMarketCostLiquidityEdgeDecayLadderReport",
        )
    _require_hard_flags("report", report)
    if report.derived_validation_digest != _report_derived_validation_digest(report):
        raise ValueError("derived_validation_digest must match report payload")
    return ResearchMarketCostLiquidityEdgeDecayLadderReportDigest(
        generated_at=report.generated_at,
        config_version=report.config_version,
        report_digest=report.derived_validation_digest,
        report_status=report.status,
        input_count=report.input_count,
        row_count=report.row_count,
        pass_count=report.pass_count,
        watch_count=report.watch_count,
        block_count=report.block_count,
        average_ladder_risk_score=report.average_ladder_risk_score,
        max_ladder_risk_score=report.max_ladder_risk_score,
        max_total_cost_ratio=report.max_total_cost_ratio,
        max_edge_decay_ratio=report.max_edge_decay_ratio,
        min_net_edge_ratio=report.min_net_edge_ratio,
        min_liquidity_score=report.min_liquidity_score,
        reason_codes=report.reason_codes,
    )


@dataclass(frozen=True)
class _DictFlags:
    value: dict[str, Any]

    @property
    def paper_only(self) -> object:
        return self.value.get("paper_only")

    @property
    def report_only(self) -> object:
        return self.value.get("report_only")

    @property
    def readonly(self) -> object:
        return self.value.get("readonly")


def _row_for_input(
    item: ResearchMarketCostLiquidityEdgeDecayLadderInput,
    config: ResearchMarketCostLiquidityEdgeDecayLadderConfig,
) -> ResearchMarketCostLiquidityEdgeDecayLadderRow:
    total_cost_ratio = _sum_ratio(item.fee_rate, item.spread_ratio, item.slippage_ratio)
    net_edge_ratio = _net_ratio(item.gross_edge_ratio, total_cost_ratio)
    edge_shortfall_score = _lower_value_risk_score(
        net_edge_ratio,
        pass_value=config.min_pass_net_edge_ratio,
        watch_value=config.min_watch_net_edge_ratio,
    )
    cost_drag_score = _higher_value_risk_score(
        total_cost_ratio,
        pass_value=config.max_pass_cost_ratio,
        watch_value=config.max_watch_cost_ratio,
    )
    liquidity_shortfall_score = _lower_value_risk_score(
        item.liquidity_score,
        pass_value=config.min_pass_liquidity_score,
        watch_value=config.min_watch_liquidity_score,
    )
    decay_pressure_score = _higher_value_risk_score(
        item.edge_decay_ratio,
        pass_value=config.max_pass_decay_ratio,
        watch_value=config.max_watch_decay_ratio,
    )
    ladder_risk_score = _weighted_score(
        edge_shortfall_score=edge_shortfall_score,
        cost_drag_score=cost_drag_score,
        liquidity_shortfall_score=liquidity_shortfall_score,
        decay_pressure_score=decay_pressure_score,
        config=config,
    )
    component_codes = _component_reason_codes(
        net_edge_ratio=net_edge_ratio,
        total_cost_ratio=total_cost_ratio,
        liquidity_score=item.liquidity_score,
        edge_decay_ratio=item.edge_decay_ratio,
        config=config,
    )
    status = _row_status(ladder_risk_score, component_codes, config)
    return ResearchMarketCostLiquidityEdgeDecayLadderRow(
        public_ladder_ref=item.public_ladder_ref,
        observed_at=item.observed_at,
        gross_edge_ratio=item.gross_edge_ratio,
        fee_rate=item.fee_rate,
        spread_ratio=item.spread_ratio,
        slippage_ratio=item.slippage_ratio,
        total_cost_ratio=total_cost_ratio,
        net_edge_ratio=net_edge_ratio,
        liquidity_score=item.liquidity_score,
        edge_decay_ratio=item.edge_decay_ratio,
        edge_shortfall_score=edge_shortfall_score,
        cost_drag_score=cost_drag_score,
        liquidity_shortfall_score=liquidity_shortfall_score,
        decay_pressure_score=decay_pressure_score,
        ladder_risk_score=ladder_risk_score,
        status=status,
        reason_codes=_row_reason_codes(status, component_codes, item.reason_codes),
    )


def _component_reason_codes(
    *,
    net_edge_ratio: Decimal,
    total_cost_ratio: Decimal,
    liquidity_score: Decimal,
    edge_decay_ratio: Decimal,
    config: ResearchMarketCostLiquidityEdgeDecayLadderConfig,
) -> tuple[str, ...]:
    codes: list[str] = []
    if net_edge_ratio <= config.min_watch_net_edge_ratio:
        codes.append("edge_shortfall_block")
    elif net_edge_ratio < config.min_pass_net_edge_ratio:
        codes.append("edge_shortfall_watch")
    if total_cost_ratio > config.max_watch_cost_ratio:
        codes.append("cost_drag_block")
    elif total_cost_ratio > config.max_pass_cost_ratio:
        codes.append("cost_drag_watch")
    if liquidity_score < config.min_watch_liquidity_score:
        codes.append("liquidity_shortfall_block")
    elif liquidity_score < config.min_pass_liquidity_score:
        codes.append("liquidity_shortfall_watch")
    if edge_decay_ratio > config.max_watch_decay_ratio:
        codes.append("edge_decay_block")
    elif edge_decay_ratio > config.max_pass_decay_ratio:
        codes.append("edge_decay_watch")
    return tuple(codes)


def _row_status(
    ladder_risk_score: Decimal,
    component_codes: tuple[str, ...],
    config: ResearchMarketCostLiquidityEdgeDecayLadderConfig,
) -> str:
    if any(code.endswith("_block") for code in component_codes):
        return "block"
    if ladder_risk_score > config.max_watch_ladder_risk_score:
        return "block"
    if any(code.endswith("_watch") for code in component_codes):
        return "watch"
    if ladder_risk_score > config.max_pass_ladder_risk_score:
        return "watch"
    return "pass"


def _row_reason_codes(
    status: str,
    component_codes: tuple[str, ...],
    input_codes: tuple[str, ...],
) -> tuple[str, ...]:
    codes = tuple(f"input_{code}" for code in input_codes) + (
        f"edge_decay_ladder_{status}",
        *component_codes,
    )
    return _normalize_reason_codes(
        "reason_codes",
        tuple(sorted(codes)),
        allow_empty=False,
    )


def _report_status(
    rows: tuple[ResearchMarketCostLiquidityEdgeDecayLadderRow, ...],
) -> str:
    if not rows or any(row.status == "block" for row in rows):
        return "block"
    if any(row.status == "watch" for row in rows):
        return "watch"
    return "pass"


def _report_reason_codes(
    rows: tuple[ResearchMarketCostLiquidityEdgeDecayLadderRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return ("no_edge_decay_ladder_inputs",)
    status = _report_status(rows)
    codes = [f"edge_decay_ladder_{status}"]
    row_codes = {code for row in rows for code in row.reason_codes}
    codes.extend(code for code in REPORT_REASON_PRIORITY if code in row_codes)
    return _normalize_reason_codes("reason_codes", tuple(codes), allow_empty=False)


def _reason_code_counts(
    rows: tuple[ResearchMarketCostLiquidityEdgeDecayLadderRow, ...],
) -> tuple[ResearchMarketCostLiquidityEdgeDecayLadderReasonCodeCount, ...]:
    if not rows:
        return (
            ResearchMarketCostLiquidityEdgeDecayLadderReasonCodeCount(
                reason_code="no_edge_decay_ladder_inputs",
                count=ONE,
                row_ratio=ZERO,
            ),
        )
    counts = Counter(code for row in rows for code in row.reason_codes)
    row_count = _decimal_count(len(rows))
    return tuple(
        ResearchMarketCostLiquidityEdgeDecayLadderReasonCodeCount(
            reason_code=code,
            count=_decimal_count(count),
            row_ratio=_safe_ratio(_decimal_count(count), row_count),
        )
        for code, count in sorted(counts.items())
    )


def _normalize_inputs(
    inputs: Iterable[ResearchMarketCostLiquidityEdgeDecayLadderInput],
    generated_at: datetime,
) -> tuple[ResearchMarketCostLiquidityEdgeDecayLadderInput, ...]:
    if isinstance(inputs, (str, bytes)):
        raise ValueError("inputs must be an iterable")
    try:
        normalized = tuple(inputs)
    except TypeError as exc:
        raise ValueError("inputs must be an iterable") from exc
    seen_refs: set[str] = set()
    for item in normalized:
        if type(item) is not ResearchMarketCostLiquidityEdgeDecayLadderInput:
            raise ValueError(
                "inputs must contain ResearchMarketCostLiquidityEdgeDecayLadderInput",
            )
        _require_hard_flags("input", item)
        if item.observed_at > generated_at:
            raise ValueError("observed_at must not be after generated_at")
        if item.public_ladder_ref in seen_refs:
            raise ValueError("public_ladder_ref must be unique")
        seen_refs.add(item.public_ladder_ref)
    return normalized


def _normalize_rows(
    rows: Iterable[ResearchMarketCostLiquidityEdgeDecayLadderRow],
) -> tuple[ResearchMarketCostLiquidityEdgeDecayLadderRow, ...]:
    if isinstance(rows, (str, bytes)):
        raise ValueError("rows must be an iterable")
    try:
        normalized = tuple(rows)
    except TypeError as exc:
        raise ValueError("rows must be an iterable") from exc
    for row in normalized:
        if type(row) is not ResearchMarketCostLiquidityEdgeDecayLadderRow:
            raise ValueError(
                "rows must contain ResearchMarketCostLiquidityEdgeDecayLadderRow",
            )
        _require_hard_flags("row", row)
    return tuple(sorted(normalized, key=_row_key))


def _normalize_reason_code_counts(
    items: Iterable[ResearchMarketCostLiquidityEdgeDecayLadderReasonCodeCount],
) -> tuple[ResearchMarketCostLiquidityEdgeDecayLadderReasonCodeCount, ...]:
    if isinstance(items, (str, bytes)):
        raise ValueError("reason_code_counts must be an iterable")
    try:
        normalized = tuple(items)
    except TypeError as exc:
        raise ValueError("reason_code_counts must be an iterable") from exc
    for item in normalized:
        if type(item) is not ResearchMarketCostLiquidityEdgeDecayLadderReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "ResearchMarketCostLiquidityEdgeDecayLadderReasonCodeCount",
            )
        _require_hard_flags("reason code count", item)
    return tuple(sorted(normalized, key=lambda item: item.reason_code))


def _row_key(row: ResearchMarketCostLiquidityEdgeDecayLadderRow) -> tuple[int, Decimal, str]:
    return (STATUS_WEIGHT[row.status], -row.ladder_risk_score, row.public_ladder_ref)


def _status_count(
    rows: tuple[ResearchMarketCostLiquidityEdgeDecayLadderRow, ...],
    status: str,
) -> Decimal:
    return _decimal_count(sum(1 for row in rows if row.status == status))


def _average_score(
    rows: tuple[ResearchMarketCostLiquidityEdgeDecayLadderRow, ...],
) -> Decimal | None:
    if not rows:
        return None
    return _safe_ratio(
        sum((row.ladder_risk_score for row in rows), ZERO),
        _decimal_count(len(rows)),
    )


def _min_decimal(
    rows: tuple[ResearchMarketCostLiquidityEdgeDecayLadderRow, ...],
    field_name: str,
) -> Decimal:
    if not rows:
        return ZERO
    return _require_nonnegative_decimal(
        field_name,
        min(getattr(row, field_name) for row in rows),
    )


def _max_decimal(
    rows: tuple[ResearchMarketCostLiquidityEdgeDecayLadderRow, ...],
    field_name: str,
) -> Decimal:
    if not rows:
        return ZERO
    return _require_nonnegative_decimal(
        field_name,
        max(getattr(row, field_name) for row in rows),
    )


def _validate_row(row: ResearchMarketCostLiquidityEdgeDecayLadderRow) -> None:
    if row.total_cost_ratio != _sum_ratio(
        row.fee_rate,
        row.spread_ratio,
        row.slippage_ratio,
    ):
        raise ValueError("total_cost_ratio must match cost inputs")
    if row.net_edge_ratio != _net_ratio(row.gross_edge_ratio, row.total_cost_ratio):
        raise ValueError("net_edge_ratio must match edge and cost")
    if f"edge_decay_ladder_{row.status}" not in row.reason_codes:
        raise ValueError("reason_codes must match status")


def _validate_report(report: ResearchMarketCostLiquidityEdgeDecayLadderReport) -> None:
    rows = report.rows
    if report.input_count != _decimal_count(len(rows)):
        raise ValueError("input_count must match rows")
    if report.row_count != _decimal_count(len(rows)):
        raise ValueError("row_count must match rows")
    if report.pass_count != _status_count(rows, "pass"):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _status_count(rows, "watch"):
        raise ValueError("watch_count must match rows")
    if report.block_count != _status_count(rows, "block"):
        raise ValueError("block_count must match rows")
    if report.average_ladder_risk_score != _average_score(rows):
        raise ValueError("average_ladder_risk_score must match rows")
    if report.max_ladder_risk_score != _max_decimal(rows, "ladder_risk_score"):
        raise ValueError("max_ladder_risk_score must match rows")
    if report.max_total_cost_ratio != _max_decimal(rows, "total_cost_ratio"):
        raise ValueError("max_total_cost_ratio must match rows")
    if report.max_edge_decay_ratio != _max_decimal(rows, "edge_decay_ratio"):
        raise ValueError("max_edge_decay_ratio must match rows")
    if report.min_net_edge_ratio != _min_decimal(rows, "net_edge_ratio"):
        raise ValueError("min_net_edge_ratio must match rows")
    if report.min_liquidity_score != _min_decimal(rows, "liquidity_score"):
        raise ValueError("min_liquidity_score must match rows")
    if report.status != _report_status(rows):
        raise ValueError("status must match rows")
    if report.reason_codes != _report_reason_codes(rows):
        raise ValueError("reason_codes must match rows")
    if report.reason_code_counts != _reason_code_counts(rows):
        raise ValueError("reason_code_counts must match rows")
    if rows != tuple(sorted(rows, key=_row_key)):
        raise ValueError("rows must be deterministic")


def _weighted_score(
    *,
    edge_shortfall_score: Decimal,
    cost_drag_score: Decimal,
    liquidity_shortfall_score: Decimal,
    decay_pressure_score: Decimal,
    config: ResearchMarketCostLiquidityEdgeDecayLadderConfig,
) -> Decimal:
    with localcontext() as context:
        context.prec = DECIMAL_CONTEXT_PRECISION
        value = (
            edge_shortfall_score * config.edge_weight
            + cost_drag_score * config.cost_weight
            + liquidity_shortfall_score * config.liquidity_weight
            + decay_pressure_score * config.decay_weight
        )
    return _require_ratio_decimal("ladder_risk_score", value)


def _higher_value_risk_score(
    value: Decimal,
    *,
    pass_value: Decimal,
    watch_value: Decimal,
) -> Decimal:
    if value <= pass_value:
        return ZERO
    if value >= watch_value:
        return ONE
    return _safe_ratio(value - pass_value, watch_value - pass_value)


def _lower_value_risk_score(
    value: Decimal,
    *,
    pass_value: Decimal,
    watch_value: Decimal,
) -> Decimal:
    if value >= pass_value:
        return ZERO
    if value <= watch_value:
        return ONE
    return _safe_ratio(pass_value - value, pass_value - watch_value)


def _safe_ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO:
        return ZERO
    with localcontext() as context:
        context.prec = DECIMAL_CONTEXT_PRECISION
        value = numerator / denominator
    return _require_ratio_decimal("ratio", value)


def _sum_ratio(*values: Decimal) -> Decimal:
    with localcontext() as context:
        context.prec = DECIMAL_CONTEXT_PRECISION
        total = sum(values, ZERO)
    return _require_ratio_decimal("ratio_sum", total)


def _net_ratio(gross_edge_ratio: Decimal, total_cost_ratio: Decimal) -> Decimal:
    with localcontext() as context:
        context.prec = DECIMAL_CONTEXT_PRECISION
        value = max(ZERO, gross_edge_ratio - total_cost_ratio)
    return _require_ratio_decimal("net_edge_ratio", value)


def _report_derived_validation_digest(
    report: ResearchMarketCostLiquidityEdgeDecayLadderReport,
) -> str:
    values = asdict(report)
    values.pop("derived_validation_digest", None)
    return _derived_validation_digest(values)


def _derived_validation_digest(values: dict[str, object]) -> str:
    payload = _json_ready(values)
    reject_unsafe_surface_fields("cost liquidity edge decay ladder digest", payload)
    _reject_unsafe_public_payload("digest", payload)
    canonical = json.dumps(
        payload,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _validate_payload_digest(payload: dict[str, Any]) -> None:
    digest = payload.get("derived_validation_digest")
    if digest is None:
        return
    _require_sha256_digest("derived_validation_digest", digest)
    values = dict(payload)
    values.pop("derived_validation_digest")
    if digest != _derived_validation_digest(values):
        raise ValueError("derived_validation_digest must match report payload")


def _json_ready(value: object) -> object:
    if value is None:
        return None
    if is_dataclass(value) and not isinstance(value, type):
        return _json_ready(asdict(value))
    if type(value) is Decimal:
        if not value.is_finite():
            raise ValueError("JSON Decimal value must be finite")
        return str(value)
    if isinstance(value, Decimal):
        raise ValueError("JSON Decimal value must be exactly Decimal")
    if type(value) is datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("JSON datetime value must be timezone-aware")
        return value.astimezone(UTC).isoformat()
    if isinstance(value, datetime):
        raise ValueError("JSON datetime value must be exactly datetime")
    if isinstance(value, float):
        raise ValueError("JSON value must not be a float")
    if type(value) is int:
        raise ValueError("JSON numeric value must use Decimal")
    if type(value) is bool:
        return value
    if type(value) is str:
        return value
    if isinstance(value, dict):
        ready: dict[str, object] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            ready[key] = _json_ready(item)
        return ready
    if isinstance(value, (list, tuple)):
        return [_json_ready(item) for item in value]
    raise ValueError("value is not JSON serializable")


def _normalize_reason_codes(
    field_name: str,
    value: object,
    *,
    allow_empty: bool,
) -> tuple[str, ...]:
    if type(value) not in (list, tuple):
        raise ValueError(f"{field_name} must be a list or tuple")
    codes = tuple(value)
    if not allow_empty and not codes:
        raise ValueError(f"{field_name} must not be empty")
    for code in codes:
        _require_public_label(field_name, code)
    if len(set(codes)) != len(codes):
        raise ValueError(f"{field_name} must be unique")
    if field_name == "reason_codes" and tuple(sorted(codes)) != codes:
        known_priority_codes = (
            "edge_decay_ladder_block",
            "edge_decay_ladder_watch",
            "edge_decay_ladder_pass",
            *REPORT_REASON_PRIORITY,
            "no_edge_decay_ladder_inputs",
        )
        priority_codes = tuple(code for code in codes if not code.startswith("input_"))
        input_codes = tuple(code for code in codes if code.startswith("input_"))
        if (
            tuple(code for code in known_priority_codes if code in priority_codes)
            != priority_codes
            or tuple(sorted(input_codes)) != input_codes
        ):
            raise ValueError(f"{field_name} must be deterministic")
        return codes
    if tuple(sorted(codes)) != codes:
        raise ValueError(f"{field_name} must be deterministic")
    return codes


def _require_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _normalize_decimal(field_name, value)
    if decimal_value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return decimal_value


def _require_ratio_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _normalize_decimal(field_name, value)
    if decimal_value < ZERO or decimal_value > ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return decimal_value


def _normalize_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return value.quantize(QUANTUM)


def _quantize(value: Decimal) -> Decimal:
    return _normalize_decimal("value", value)


def _decimal_count(value: int) -> Decimal:
    return Decimal(value).quantize(QUANTUM)


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_exact_type(value: object, expected_type: type[object], label: str) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{label} must be exactly {expected_type.__name__}")


def _require_status(field_name: str, value: object) -> None:
    if (
        type(value) is not str
        or value not in MARKET_COST_LIQUIDITY_EDGE_DECAY_LADDER_STATUSES
    ):
        raise ValueError(f"{field_name} must be pass, watch, or block")


def _require_sha256_digest(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if len(value) != 64 or any(character not in "0123456789abcdef" for character in value):
        raise ValueError(f"{field_name} must be a sha256 hex digest")


def _require_public_label(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")
    for character in value:
        if not (
            character.islower()
            or character.isdigit()
            or character in ("-", "_")
        ):
            raise ValueError(f"{field_name} must be a public label")
    _reject_unsafe_public_string(field_name, value)


def _require_hard_flags(label: str, value: object) -> None:
    require_paper_only_flags(label, value)


def _reject_unsafe_public_payload(label: str, value: object) -> None:
    if is_dataclass(value) and not isinstance(value, type):
        _reject_unsafe_public_payload(label, asdict(value))
        return
    if type(value) is str:
        _reject_unsafe_public_string(label, value)
        return
    if isinstance(value, dict):
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            _reject_unsafe_public_string(label, key)
            _reject_unsafe_public_payload(label, item)
        return
    if isinstance(value, (list, tuple)):
        for item in value:
            _reject_unsafe_public_payload(label, item)


def _reject_unsafe_public_string(label: str, value: str) -> None:
    normalized = value.lower()
    if any(fragment in normalized for fragment in UNSAFE_PUBLIC_FRAGMENTS):
        raise ValueError(f"unsafe public value in {label}")


__all__ = (
    "DEFAULT_RESEARCH_MARKET_COST_LIQUIDITY_EDGE_DECAY_LADDER_REPORT_CONFIG_VERSION",
    "MARKET_COST_LIQUIDITY_EDGE_DECAY_LADDER_STATUSES",
    "ResearchMarketCostLiquidityEdgeDecayLadderConfig",
    "ResearchMarketCostLiquidityEdgeDecayLadderInput",
    "ResearchMarketCostLiquidityEdgeDecayLadderReasonCodeCount",
    "ResearchMarketCostLiquidityEdgeDecayLadderReport",
    "ResearchMarketCostLiquidityEdgeDecayLadderReportDigest",
    "ResearchMarketCostLiquidityEdgeDecayLadderRow",
    "build_research_market_cost_liquidity_edge_decay_ladder_report",
    "research_market_cost_liquidity_edge_decay_ladder_report_digest",
    "research_market_cost_liquidity_edge_decay_ladder_report_payload",
)
