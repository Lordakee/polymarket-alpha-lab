"""Pure report-only cost shock resilience reducer for manual research."""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable, Mapping
from dataclasses import dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation
from hashlib import sha256
import json
import re
from typing import Any


COST_SHOCK_RESILIENCE_STATUSES = ("pass", "watch", "block")
DEFAULT_RESEARCH_MARKET_COST_SHOCK_RESILIENCE_REPORT_CONFIG_VERSION = (
    "research-market-cost-shock-resilience-report-v0"
)
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
QUANTUM = Decimal("0.000001")
LABEL_RE = re.compile(r"^[a-z0-9][a-z0-9_.-]{0,127}$")
REASON_CODE_RE = re.compile(r"^[a-z0-9][a-z0-9_]{0,127}$")
DECIMAL_TEXT_RE = re.compile(r"^(0|[1-9][0-9]*)\.[0-9]{6}$")
UNSAFE_PUBLIC_FRAGMENTS = (
    "raw",
    "candidate" + "_" + "id",
    "candidate-id",
    "candidateid",
    "condition" + "_" + "id",
    "condition-id",
    "conditionid",
    "market" + "_" + "id",
    "market-id",
    "marketid",
    "market" + "_" + "slug",
    "market-slug",
    "marketslug",
    "slug",
    "ques" + "tion",
    "url",
    "source" + "_" + "text",
    "source-text",
    "sourcetext",
    "dsn",
    "table",
    "to" + "ken",
    "wal" + "let",
    "or" + "der",
    "tra" + "de",
    "li" + "ve",
    "b" + "uy",
    "s" + "ell",
    "posi" + "tion",
    "siz" + "ing",
    "recommenda" + "tion",
    "execu" + "tion",
)
REPORT_PAYLOAD_KEYS = (
    "generated_at",
    "config_version",
    "input_count",
    "pass_count",
    "watch_count",
    "block_count",
    "average_cost_shock_resilience_score",
    "max_spread_widening",
    "max_depth_decay",
    "max_fee_drag",
    "min_slippage_cushion",
    "max_volatility",
    "max_book_age_seconds",
    "max_settlement_friction",
    "status",
    "rows",
    "reason_code_counts",
    "reason_codes",
    "derived_validation_digest",
    "paper_only",
    "report_only",
    "readonly",
)
ROW_PAYLOAD_KEYS = (
    "resilience_group_ref",
    "observed_at",
    "last_book_update_at",
    "current_spread",
    "stressed_spread",
    "spread_widening",
    "spread_resilience_score",
    "baseline_depth",
    "stressed_depth",
    "depth_decay",
    "depth_resilience_score",
    "fee_drag",
    "fee_resilience_score",
    "slippage_cushion",
    "slippage_resilience_score",
    "volatility",
    "volatility_resilience_score",
    "book_age_seconds",
    "book_age_resilience_score",
    "settlement_friction",
    "settlement_resilience_score",
    "cost_shock_resilience_score",
    "status",
    "reason_codes",
    "paper_only",
    "report_only",
    "readonly",
)
REASON_CODE_COUNT_PAYLOAD_KEYS = (
    "reason_code",
    "count",
    "row_ratio",
    "paper_only",
    "report_only",
    "readonly",
)


__all__ = (
    "COST_SHOCK_RESILIENCE_STATUSES",
    "DEFAULT_RESEARCH_MARKET_COST_SHOCK_RESILIENCE_REPORT_CONFIG_VERSION",
    "ResearchMarketCostShockResilienceConfig",
    "ResearchMarketCostShockResilienceObservation",
    "ResearchMarketCostShockResilienceReasonCodeCount",
    "ResearchMarketCostShockResilienceReport",
    "ResearchMarketCostShockResilienceRow",
    "build_research_market_cost_shock_resilience_report",
    "research_market_cost_shock_resilience_report_digest",
    "research_market_cost_shock_resilience_report_payload",
)


@dataclass(frozen=True)
class ResearchMarketCostShockResilienceConfig:
    config_version: str = (
        DEFAULT_RESEARCH_MARKET_COST_SHOCK_RESILIENCE_REPORT_CONFIG_VERSION
    )
    max_pass_spread_widening: Decimal = Decimal("0.020000")
    max_watch_spread_widening: Decimal = Decimal("0.060000")
    max_pass_depth_decay: Decimal = Decimal("0.150000")
    max_watch_depth_decay: Decimal = Decimal("0.450000")
    max_pass_fee_drag: Decimal = Decimal("0.010000")
    max_watch_fee_drag: Decimal = Decimal("0.030000")
    min_pass_slippage_cushion: Decimal = Decimal("0.120000")
    min_watch_slippage_cushion: Decimal = Decimal("0.050000")
    max_pass_volatility: Decimal = Decimal("0.200000")
    max_watch_volatility: Decimal = Decimal("0.500000")
    max_pass_book_age_seconds: Decimal = Decimal("120.000000")
    max_watch_book_age_seconds: Decimal = Decimal("600.000000")
    max_pass_settlement_friction: Decimal = Decimal("0.010000")
    max_watch_settlement_friction: Decimal = Decimal("0.030000")
    pass_resilience_score: Decimal = Decimal("0.750000")
    watch_resilience_score: Decimal = Decimal("0.450000")
    spread_weight: Decimal = Decimal("0.150000")
    depth_weight: Decimal = Decimal("0.200000")
    fee_weight: Decimal = Decimal("0.150000")
    slippage_weight: Decimal = Decimal("0.150000")
    volatility_weight: Decimal = Decimal("0.150000")
    book_age_weight: Decimal = Decimal("0.100000")
    settlement_weight: Decimal = Decimal("0.100000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchMarketCostShockResilienceConfig does not support subclassing",
        )

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchMarketCostShockResilienceConfig, "config")
        _require_label("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_MARKET_COST_SHOCK_RESILIENCE_REPORT_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "max_pass_spread_widening",
            "max_watch_spread_widening",
            "max_pass_depth_decay",
            "max_watch_depth_decay",
            "max_pass_fee_drag",
            "max_watch_fee_drag",
            "min_pass_slippage_cushion",
            "min_watch_slippage_cushion",
            "max_pass_volatility",
            "max_watch_volatility",
            "max_pass_settlement_friction",
            "max_watch_settlement_friction",
            "pass_resilience_score",
            "watch_resilience_score",
            "spread_weight",
            "depth_weight",
            "fee_weight",
            "slippage_weight",
            "volatility_weight",
            "book_age_weight",
            "settlement_weight",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "max_pass_book_age_seconds",
            "max_watch_book_age_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_positive_decimal(field_name, getattr(self, field_name)),
            )
        if self.max_watch_spread_widening <= self.max_pass_spread_widening:
            raise ValueError("max_watch_spread_widening must exceed pass threshold")
        if self.max_watch_depth_decay <= self.max_pass_depth_decay:
            raise ValueError("max_watch_depth_decay must exceed pass threshold")
        if self.max_watch_fee_drag <= self.max_pass_fee_drag:
            raise ValueError("max_watch_fee_drag must exceed pass threshold")
        if self.min_pass_slippage_cushion <= self.min_watch_slippage_cushion:
            raise ValueError("min_pass_slippage_cushion must exceed watch threshold")
        if self.max_watch_volatility <= self.max_pass_volatility:
            raise ValueError("max_watch_volatility must exceed pass threshold")
        if self.max_watch_book_age_seconds <= self.max_pass_book_age_seconds:
            raise ValueError("max_watch_book_age_seconds must exceed pass threshold")
        if self.max_watch_settlement_friction <= self.max_pass_settlement_friction:
            raise ValueError("max_watch_settlement_friction must exceed pass threshold")
        if self.pass_resilience_score <= self.watch_resilience_score:
            raise ValueError("pass_resilience_score must exceed watch threshold")
        weight_sum = _quantize(
            self.spread_weight
            + self.depth_weight
            + self.fee_weight
            + self.slippage_weight
            + self.volatility_weight
            + self.book_age_weight
            + self.settlement_weight,
        )
        if weight_sum != ONE:
            raise ValueError("cost shock resilience weights must sum to 1")
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class ResearchMarketCostShockResilienceObservation:
    shock_case_key: str
    observed_at: datetime
    last_book_update_at: datetime
    current_spread: Decimal
    stressed_spread: Decimal
    baseline_depth: Decimal
    stressed_depth: Decimal
    fee_drag: Decimal
    slippage_cushion: Decimal
    volatility: Decimal
    settlement_friction: Decimal
    reason_codes: tuple[str, ...] = ()
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchMarketCostShockResilienceObservation does not support subclassing",
        )

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchMarketCostShockResilienceObservation,
            "observation",
        )
        _require_label("shock_case_key", self.shock_case_key)
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        object.__setattr__(
            self,
            "last_book_update_at",
            _as_utc("last_book_update_at", self.last_book_update_at),
        )
        for field_name in (
            "current_spread",
            "stressed_spread",
            "fee_drag",
            "slippage_cushion",
            "volatility",
            "settlement_friction",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        if self.stressed_spread < self.current_spread:
            raise ValueError("stressed_spread must be at least current_spread")
        object.__setattr__(
            self,
            "baseline_depth",
            _require_positive_decimal("baseline_depth", self.baseline_depth),
        )
        object.__setattr__(
            self,
            "stressed_depth",
            _require_nonnegative_decimal("stressed_depth", self.stressed_depth),
        )
        if self.stressed_depth > self.baseline_depth:
            raise ValueError("stressed_depth must not exceed baseline_depth")
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, allow_empty=True),
        )
        _require_hard_flags("observation", self)


@dataclass(frozen=True)
class ResearchMarketCostShockResilienceRow:
    resilience_group_ref: str
    observed_at: datetime
    last_book_update_at: datetime
    current_spread: Decimal
    stressed_spread: Decimal
    spread_widening: Decimal
    spread_resilience_score: Decimal
    baseline_depth: Decimal
    stressed_depth: Decimal
    depth_decay: Decimal
    depth_resilience_score: Decimal
    fee_drag: Decimal
    fee_resilience_score: Decimal
    slippage_cushion: Decimal
    slippage_resilience_score: Decimal
    volatility: Decimal
    volatility_resilience_score: Decimal
    book_age_seconds: Decimal
    book_age_resilience_score: Decimal
    settlement_friction: Decimal
    settlement_resilience_score: Decimal
    cost_shock_resilience_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchMarketCostShockResilienceRow does not support subclassing",
        )

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchMarketCostShockResilienceRow, "row")
        _require_public_label("resilience_group_ref", self.resilience_group_ref)
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        object.__setattr__(
            self,
            "last_book_update_at",
            _as_utc("last_book_update_at", self.last_book_update_at),
        )
        for field_name in (
            "current_spread",
            "stressed_spread",
            "spread_widening",
            "depth_decay",
            "spread_resilience_score",
            "depth_resilience_score",
            "fee_drag",
            "fee_resilience_score",
            "slippage_cushion",
            "slippage_resilience_score",
            "volatility",
            "volatility_resilience_score",
            "book_age_resilience_score",
            "settlement_friction",
            "settlement_resilience_score",
            "cost_shock_resilience_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in ("baseline_depth", "stressed_depth", "book_age_seconds"):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        if self.baseline_depth <= ZERO:
            raise ValueError("baseline_depth must be positive")
        if self.stressed_spread < self.current_spread:
            raise ValueError("stressed_spread must be at least current_spread")
        if self.stressed_depth > self.baseline_depth:
            raise ValueError("stressed_depth must not exceed baseline_depth")
        _require_status("status", self.status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, allow_empty=False),
        )
        _require_hard_flags("row", self)
        _validate_row(self)


@dataclass(frozen=True)
class ResearchMarketCostShockResilienceReasonCodeCount:
    reason_code: str
    count: Decimal
    row_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchMarketCostShockResilienceReasonCodeCount "
            "does not support subclassing",
        )

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchMarketCostShockResilienceReasonCodeCount,
            "reason_code_count",
        )
        _require_reason_code("reason_code", self.reason_code)
        object.__setattr__(
            self,
            "count",
            _require_positive_whole_decimal("count", self.count),
        )
        object.__setattr__(
            self,
            "row_ratio",
            _require_ratio_decimal("row_ratio", self.row_ratio),
        )
        _require_hard_flags("reason_code_count", self)


@dataclass(frozen=True)
class ResearchMarketCostShockResilienceReport:
    generated_at: datetime
    config_version: str
    input_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    average_cost_shock_resilience_score: Decimal | None
    max_spread_widening: Decimal
    max_depth_decay: Decimal
    max_fee_drag: Decimal
    min_slippage_cushion: Decimal
    max_volatility: Decimal
    max_book_age_seconds: Decimal
    max_settlement_friction: Decimal
    status: str
    rows: tuple[ResearchMarketCostShockResilienceRow, ...]
    reason_code_counts: tuple[ResearchMarketCostShockResilienceReasonCodeCount, ...]
    reason_codes: tuple[str, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchMarketCostShockResilienceReport does not support subclassing",
        )

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchMarketCostShockResilienceReport, "report")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_label("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_MARKET_COST_SHOCK_RESILIENCE_REPORT_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in ("input_count", "pass_count", "watch_count", "block_count"):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_whole_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "average_cost_shock_resilience_score",
            _require_optional_ratio_decimal(
                "average_cost_shock_resilience_score",
                self.average_cost_shock_resilience_score,
            ),
        )
        for field_name in (
            "max_spread_widening",
            "max_depth_decay",
            "max_fee_drag",
            "min_slippage_cushion",
            "max_volatility",
            "max_settlement_friction",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "max_book_age_seconds",
            _require_nonnegative_decimal(
                "max_book_age_seconds",
                self.max_book_age_seconds,
            ),
        )
        _require_status("status", self.status)
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, allow_empty=False),
        )
        _require_hard_flags("report", self)
        _validate_report(self)
        expected_digest = _derived_report_digest(self)
        if self.derived_validation_digest:
            _require_hex_digest("derived_validation_digest", self.derived_validation_digest)
            if self.derived_validation_digest != expected_digest:
                raise ValueError("derived_validation_digest must match report fields")
        else:
            object.__setattr__(self, "derived_validation_digest", expected_digest)


def build_research_market_cost_shock_resilience_report(
    observations: Iterable[object],
    *,
    config: ResearchMarketCostShockResilienceConfig,
    generated_at: datetime,
) -> ResearchMarketCostShockResilienceReport:
    if type(config) is not ResearchMarketCostShockResilienceConfig:
        raise ValueError("config must be a ResearchMarketCostShockResilienceConfig")
    _require_hard_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    normalized = _normalize_observations(observations)
    for item in normalized:
        if item.observed_at > generated_at_utc:
            raise ValueError("observed_at must not be after generated_at")
        if item.last_book_update_at > generated_at_utc:
            raise ValueError("last_book_update_at must not be after generated_at")
    rows = tuple(
        _row_from_observation(
            resilience_group_ref=f"cost_shock_group_{index:03d}",
            observation=item,
            config=config,
            generated_at=generated_at_utc,
        )
        for index, item in enumerate(sorted(normalized, key=_observation_sort_key), start=1)
    )
    reason_codes = _summary_reason_codes(rows)
    return ResearchMarketCostShockResilienceReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        input_count=_decimal_count(len(rows)),
        pass_count=_decimal_count(_status_count(rows, "pass")),
        watch_count=_decimal_count(_status_count(rows, "watch")),
        block_count=_decimal_count(_status_count(rows, "block")),
        average_cost_shock_resilience_score=_average_score(rows),
        max_spread_widening=_max_or_zero(tuple(row.spread_widening for row in rows)),
        max_depth_decay=_max_or_zero(tuple(row.depth_decay for row in rows)),
        max_fee_drag=_max_or_zero(tuple(row.fee_drag for row in rows)),
        min_slippage_cushion=_min_or_zero(tuple(row.slippage_cushion for row in rows)),
        max_volatility=_max_or_zero(tuple(row.volatility for row in rows)),
        max_book_age_seconds=_max_or_zero(tuple(row.book_age_seconds for row in rows)),
        max_settlement_friction=_max_or_zero(
            tuple(row.settlement_friction for row in rows),
        ),
        status=_summary_status(rows),
        rows=rows,
        reason_code_counts=_reason_code_counts(rows, reason_codes),
        reason_codes=reason_codes,
    )


def research_market_cost_shock_resilience_report_payload(
    report: ResearchMarketCostShockResilienceReport,
) -> dict[str, Any]:
    if type(report) is not ResearchMarketCostShockResilienceReport:
        raise ValueError("report must be a ResearchMarketCostShockResilienceReport")
    _require_hard_flags("report", report)
    _validate_report(report)
    expected_digest = _derived_report_digest(report)
    if report.derived_validation_digest != expected_digest:
        raise ValueError("derived_validation_digest must match report fields")
    payload = _payload_value(report)
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    _validate_public_payload_schema(payload)
    _reject_unsafe_public_payload("report payload", payload)
    return payload


def research_market_cost_shock_resilience_report_digest(
    report: ResearchMarketCostShockResilienceReport,
) -> str:
    if type(report) is not ResearchMarketCostShockResilienceReport:
        raise ValueError("report must be a ResearchMarketCostShockResilienceReport")
    _require_hard_flags("report", report)
    _validate_report(report)
    expected_digest = _derived_report_digest(report)
    if report.derived_validation_digest != expected_digest:
        raise ValueError("derived_validation_digest must match report fields")
    return expected_digest


def _row_from_observation(
    *,
    resilience_group_ref: str,
    observation: ResearchMarketCostShockResilienceObservation,
    config: ResearchMarketCostShockResilienceConfig,
    generated_at: datetime,
) -> ResearchMarketCostShockResilienceRow:
    spread_widening = _quantize(observation.stressed_spread - observation.current_spread)
    depth_decay = _quantize(
        (observation.baseline_depth - observation.stressed_depth)
        / observation.baseline_depth,
    )
    book_age_seconds = _age_seconds(generated_at, observation.last_book_update_at)
    spread_resilience_score = _inverse_ratio_score(
        spread_widening,
        config.max_watch_spread_widening,
    )
    depth_resilience_score = _inverse_ratio_score(
        depth_decay,
        config.max_watch_depth_decay,
    )
    fee_resilience_score = _inverse_ratio_score(
        observation.fee_drag,
        config.max_watch_fee_drag,
    )
    slippage_resilience_score = _bounded_ratio(
        observation.slippage_cushion,
        config.min_pass_slippage_cushion,
    )
    volatility_resilience_score = _inverse_ratio_score(
        observation.volatility,
        config.max_watch_volatility,
    )
    book_age_resilience_score = _inverse_ratio_score(
        book_age_seconds,
        config.max_watch_book_age_seconds,
    )
    settlement_resilience_score = _inverse_ratio_score(
        observation.settlement_friction,
        config.max_watch_settlement_friction,
    )
    cost_shock_resilience_score = _cost_shock_resilience_score(
        spread_resilience_score=spread_resilience_score,
        depth_resilience_score=depth_resilience_score,
        fee_resilience_score=fee_resilience_score,
        slippage_resilience_score=slippage_resilience_score,
        volatility_resilience_score=volatility_resilience_score,
        book_age_resilience_score=book_age_resilience_score,
        settlement_resilience_score=settlement_resilience_score,
        config=config,
    )
    status = _row_status(
        spread_widening=spread_widening,
        depth_decay=depth_decay,
        fee_drag=observation.fee_drag,
        slippage_cushion=observation.slippage_cushion,
        volatility=observation.volatility,
        book_age_seconds=book_age_seconds,
        settlement_friction=observation.settlement_friction,
        cost_shock_resilience_score=cost_shock_resilience_score,
        config=config,
    )
    return ResearchMarketCostShockResilienceRow(
        resilience_group_ref=resilience_group_ref,
        observed_at=observation.observed_at,
        last_book_update_at=observation.last_book_update_at,
        current_spread=observation.current_spread,
        stressed_spread=observation.stressed_spread,
        spread_widening=spread_widening,
        spread_resilience_score=spread_resilience_score,
        baseline_depth=observation.baseline_depth,
        stressed_depth=observation.stressed_depth,
        depth_decay=depth_decay,
        depth_resilience_score=depth_resilience_score,
        fee_drag=observation.fee_drag,
        fee_resilience_score=fee_resilience_score,
        slippage_cushion=observation.slippage_cushion,
        slippage_resilience_score=slippage_resilience_score,
        volatility=observation.volatility,
        volatility_resilience_score=volatility_resilience_score,
        book_age_seconds=book_age_seconds,
        book_age_resilience_score=book_age_resilience_score,
        settlement_friction=observation.settlement_friction,
        settlement_resilience_score=settlement_resilience_score,
        cost_shock_resilience_score=cost_shock_resilience_score,
        status=status,
        reason_codes=_row_reason_codes(
            observation=observation,
            spread_widening=spread_widening,
            depth_decay=depth_decay,
            book_age_seconds=book_age_seconds,
            status=status,
            config=config,
        ),
    )


def _cost_shock_resilience_score(
    *,
    spread_resilience_score: Decimal,
    depth_resilience_score: Decimal,
    fee_resilience_score: Decimal,
    slippage_resilience_score: Decimal,
    volatility_resilience_score: Decimal,
    book_age_resilience_score: Decimal,
    settlement_resilience_score: Decimal,
    config: ResearchMarketCostShockResilienceConfig,
) -> Decimal:
    return _quantize(
        spread_resilience_score * config.spread_weight
        + depth_resilience_score * config.depth_weight
        + fee_resilience_score * config.fee_weight
        + slippage_resilience_score * config.slippage_weight
        + volatility_resilience_score * config.volatility_weight
        + book_age_resilience_score * config.book_age_weight
        + settlement_resilience_score * config.settlement_weight,
    )


def _row_status(
    *,
    spread_widening: Decimal,
    depth_decay: Decimal,
    fee_drag: Decimal,
    slippage_cushion: Decimal,
    volatility: Decimal,
    book_age_seconds: Decimal,
    settlement_friction: Decimal,
    cost_shock_resilience_score: Decimal,
    config: ResearchMarketCostShockResilienceConfig,
) -> str:
    if (
        cost_shock_resilience_score < config.watch_resilience_score
        or spread_widening >= config.max_watch_spread_widening
        or depth_decay >= config.max_watch_depth_decay
        or fee_drag >= config.max_watch_fee_drag
        or slippage_cushion < config.min_watch_slippage_cushion
        or volatility >= config.max_watch_volatility
        or book_age_seconds >= config.max_watch_book_age_seconds
        or settlement_friction >= config.max_watch_settlement_friction
    ):
        return "block"
    if (
        cost_shock_resilience_score < config.pass_resilience_score
        or spread_widening >= config.max_pass_spread_widening
        or depth_decay >= config.max_pass_depth_decay
        or fee_drag >= config.max_pass_fee_drag
        or slippage_cushion < config.min_pass_slippage_cushion
        or volatility >= config.max_pass_volatility
        or book_age_seconds >= config.max_pass_book_age_seconds
        or settlement_friction >= config.max_pass_settlement_friction
    ):
        return "watch"
    return "pass"


def _row_reason_codes(
    *,
    observation: ResearchMarketCostShockResilienceObservation,
    spread_widening: Decimal,
    depth_decay: Decimal,
    book_age_seconds: Decimal,
    status: str,
    config: ResearchMarketCostShockResilienceConfig,
) -> tuple[str, ...]:
    reason_codes = {
        f"cost_shock_resilience_{status}",
        _upper_threshold_reason(
            "spread_widening",
            spread_widening,
            config.max_pass_spread_widening,
            config.max_watch_spread_widening,
        ),
        _upper_threshold_reason(
            "depth_decay",
            depth_decay,
            config.max_pass_depth_decay,
            config.max_watch_depth_decay,
        ),
        _upper_threshold_reason(
            "fee_drag",
            observation.fee_drag,
            config.max_pass_fee_drag,
            config.max_watch_fee_drag,
        ),
        _lower_threshold_reason(
            "slippage_cushion",
            observation.slippage_cushion,
            config.min_pass_slippage_cushion,
            config.min_watch_slippage_cushion,
        ),
        _upper_threshold_reason(
            "volatility",
            observation.volatility,
            config.max_pass_volatility,
            config.max_watch_volatility,
        ),
        _upper_threshold_reason(
            "book_age",
            book_age_seconds,
            config.max_pass_book_age_seconds,
            config.max_watch_book_age_seconds,
        ),
        _upper_threshold_reason(
            "settlement_friction",
            observation.settlement_friction,
            config.max_pass_settlement_friction,
            config.max_watch_settlement_friction,
        ),
    }
    for reason_code in observation.reason_codes:
        reason_codes.add(f"input_{reason_code}")
    return tuple(sorted(reason_codes))


def _upper_threshold_reason(
    prefix: str,
    value: Decimal,
    pass_threshold: Decimal,
    watch_threshold: Decimal,
) -> str:
    if value >= watch_threshold:
        return f"{prefix}_block"
    if value >= pass_threshold:
        return f"{prefix}_watch"
    return f"{prefix}_pass"


def _lower_threshold_reason(
    prefix: str,
    value: Decimal,
    pass_threshold: Decimal,
    watch_threshold: Decimal,
) -> str:
    if value < watch_threshold:
        return f"{prefix}_block"
    if value < pass_threshold:
        return f"{prefix}_watch"
    return f"{prefix}_pass"


def _normalize_observations(
    observations: Iterable[object],
) -> tuple[ResearchMarketCostShockResilienceObservation, ...]:
    if isinstance(observations, (str, bytes)):
        raise ValueError("observations must be an iterable")
    try:
        values = tuple(observations)
    except TypeError as exc:
        raise ValueError("observations must be an iterable") from exc
    for value in values:
        if type(value) is not ResearchMarketCostShockResilienceObservation:
            raise ValueError(
                "observations must contain "
                "ResearchMarketCostShockResilienceObservation values",
            )
        _require_hard_flags("observation", value)
    keys = tuple(value.shock_case_key for value in values)
    if len(set(keys)) != len(keys):
        raise ValueError("shock_case_key values must be unique")
    return values


def _normalize_rows(
    rows: tuple[ResearchMarketCostShockResilienceRow, ...],
) -> tuple[ResearchMarketCostShockResilienceRow, ...]:
    if type(rows) is not tuple:
        raise ValueError("rows must be a tuple")
    for index, row in enumerate(rows):
        if type(row) is not ResearchMarketCostShockResilienceRow:
            raise ValueError(
                "rows must contain ResearchMarketCostShockResilienceRow values",
            )
        _require_hard_flags(f"rows[{index}]", row)
    if rows != tuple(sorted(rows, key=lambda row: row.resilience_group_ref)):
        raise ValueError("rows must be sorted by resilience_group_ref")
    return rows


def _normalize_reason_code_counts(
    counts: tuple[ResearchMarketCostShockResilienceReasonCodeCount, ...],
) -> tuple[ResearchMarketCostShockResilienceReasonCodeCount, ...]:
    if type(counts) is not tuple:
        raise ValueError("reason_code_counts must be a tuple")
    for index, count in enumerate(counts):
        if type(count) is not ResearchMarketCostShockResilienceReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "ResearchMarketCostShockResilienceReasonCodeCount values",
            )
        _require_hard_flags(f"reason_code_counts[{index}]", count)
    if counts != tuple(sorted(counts, key=lambda count: count.reason_code)):
        raise ValueError("reason_code_counts must be sorted by reason_code")
    return counts


def _validate_row(row: ResearchMarketCostShockResilienceRow) -> None:
    _require_exact_type(row, ResearchMarketCostShockResilienceRow, "row")
    _require_public_label("resilience_group_ref", row.resilience_group_ref)
    _require_utc_datetime("observed_at", row.observed_at)
    _require_utc_datetime("last_book_update_at", row.last_book_update_at)
    for field_name in (
        "current_spread",
        "stressed_spread",
        "spread_widening",
        "depth_decay",
        "spread_resilience_score",
        "depth_resilience_score",
        "fee_drag",
        "fee_resilience_score",
        "slippage_cushion",
        "slippage_resilience_score",
        "volatility",
        "volatility_resilience_score",
        "book_age_resilience_score",
        "settlement_friction",
        "settlement_resilience_score",
        "cost_shock_resilience_score",
    ):
        _require_canonical_decimal(
            field_name,
            getattr(row, field_name),
            _require_ratio_decimal(field_name, getattr(row, field_name)),
        )
    for field_name in ("baseline_depth", "stressed_depth", "book_age_seconds"):
        _require_canonical_decimal(
            field_name,
            getattr(row, field_name),
            _require_nonnegative_decimal(field_name, getattr(row, field_name)),
        )
    if row.baseline_depth <= ZERO:
        raise ValueError("baseline_depth must be positive")
    if row.stressed_spread < row.current_spread:
        raise ValueError("stressed_spread must be at least current_spread")
    if row.stressed_depth > row.baseline_depth:
        raise ValueError("stressed_depth must not exceed baseline_depth")
    _require_status("status", row.status)
    if row.reason_codes != _normalize_reason_codes(
        "reason_codes",
        row.reason_codes,
        allow_empty=False,
    ):
        raise ValueError("reason_codes must be canonical")
    _require_hard_flags("row", row)
    if row.spread_widening != _quantize(row.stressed_spread - row.current_spread):
        raise ValueError("spread_widening must match spread fields")
    if row.depth_decay != _quantize(
        (row.baseline_depth - row.stressed_depth) / row.baseline_depth,
    ):
        raise ValueError("depth_decay must match depth fields")
    if f"cost_shock_resilience_{row.status}" not in row.reason_codes:
        raise ValueError("status must match reason_codes")


def _validate_reason_code_count(
    count: ResearchMarketCostShockResilienceReasonCodeCount,
    label: str,
) -> None:
    _require_exact_type(
        count,
        ResearchMarketCostShockResilienceReasonCodeCount,
        label,
    )
    _require_reason_code(f"{label}.reason_code", count.reason_code)
    _require_canonical_decimal(
        f"{label}.count",
        count.count,
        _require_positive_whole_decimal(f"{label}.count", count.count),
    )
    _require_canonical_decimal(
        f"{label}.row_ratio",
        count.row_ratio,
        _require_ratio_decimal(f"{label}.row_ratio", count.row_ratio),
    )
    _require_hard_flags(label, count)


def _validate_report(report: ResearchMarketCostShockResilienceReport) -> None:
    _require_exact_type(report, ResearchMarketCostShockResilienceReport, "report")
    _require_utc_datetime("generated_at", report.generated_at)
    _require_label("config_version", report.config_version)
    if (
        report.config_version
        != DEFAULT_RESEARCH_MARKET_COST_SHOCK_RESILIENCE_REPORT_CONFIG_VERSION
    ):
        raise ValueError("config_version must be the supported config version")
    for field_name in ("input_count", "pass_count", "watch_count", "block_count"):
        _require_canonical_decimal(
            field_name,
            getattr(report, field_name),
            _require_nonnegative_whole_decimal(field_name, getattr(report, field_name)),
        )
    if report.average_cost_shock_resilience_score is not None:
        _require_canonical_decimal(
            "average_cost_shock_resilience_score",
            report.average_cost_shock_resilience_score,
            _require_ratio_decimal(
                "average_cost_shock_resilience_score",
                report.average_cost_shock_resilience_score,
            ),
        )
    for field_name in (
        "max_spread_widening",
        "max_depth_decay",
        "max_fee_drag",
        "min_slippage_cushion",
        "max_volatility",
        "max_settlement_friction",
    ):
        _require_canonical_decimal(
            field_name,
            getattr(report, field_name),
            _require_ratio_decimal(field_name, getattr(report, field_name)),
        )
    _require_canonical_decimal(
        "max_book_age_seconds",
        report.max_book_age_seconds,
        _require_nonnegative_decimal(
            "max_book_age_seconds",
            report.max_book_age_seconds,
        ),
    )
    _require_status("status", report.status)
    rows = _normalize_rows(report.rows)
    for row in rows:
        _validate_row(row)
    reason_code_counts = _normalize_reason_code_counts(report.reason_code_counts)
    for index, count in enumerate(reason_code_counts):
        _validate_reason_code_count(count, f"reason_code_counts[{index}]")
    if report.reason_codes != _normalize_reason_codes(
        "reason_codes",
        report.reason_codes,
        allow_empty=False,
    ):
        raise ValueError("reason_codes must be canonical")
    _require_hard_flags("report", report)
    if report.input_count != _decimal_count(len(report.rows)):
        raise ValueError("input_count must match rows")
    if report.pass_count != _decimal_count(_status_count(report.rows, "pass")):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _decimal_count(_status_count(report.rows, "watch")):
        raise ValueError("watch_count must match rows")
    if report.block_count != _decimal_count(_status_count(report.rows, "block")):
        raise ValueError("block_count must match rows")
    if report.average_cost_shock_resilience_score != _average_score(report.rows):
        raise ValueError("average_cost_shock_resilience_score must match rows")
    if report.max_spread_widening != _max_or_zero(
        tuple(row.spread_widening for row in report.rows),
    ):
        raise ValueError("max_spread_widening must match rows")
    if report.max_depth_decay != _max_or_zero(
        tuple(row.depth_decay for row in report.rows),
    ):
        raise ValueError("max_depth_decay must match rows")
    if report.max_fee_drag != _max_or_zero(tuple(row.fee_drag for row in report.rows)):
        raise ValueError("max_fee_drag must match rows")
    if report.min_slippage_cushion != _min_or_zero(
        tuple(row.slippage_cushion for row in report.rows),
    ):
        raise ValueError("min_slippage_cushion must match rows")
    if report.max_volatility != _max_or_zero(
        tuple(row.volatility for row in report.rows),
    ):
        raise ValueError("max_volatility must match rows")
    if report.max_book_age_seconds != _max_or_zero(
        tuple(row.book_age_seconds for row in report.rows),
    ):
        raise ValueError("max_book_age_seconds must match rows")
    if report.max_settlement_friction != _max_or_zero(
        tuple(row.settlement_friction for row in report.rows),
    ):
        raise ValueError("max_settlement_friction must match rows")
    if report.status != _summary_status(report.rows):
        raise ValueError("status must match rows")
    if report.reason_codes != _summary_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")
    if report.reason_code_counts != _reason_code_counts(report.rows, report.reason_codes):
        raise ValueError("reason_code_counts must match rows")


def _validate_public_payload_schema(payload: dict[str, Any]) -> None:
    _require_payload_keys(
        payload,
        REPORT_PAYLOAD_KEYS,
        "canonical report payload schema",
    )
    _require_payload_datetime_text("generated_at", payload["generated_at"])
    _require_payload_text("config_version", payload["config_version"])
    for field_name in (
        "input_count",
        "pass_count",
        "watch_count",
        "block_count",
        "max_spread_widening",
        "max_depth_decay",
        "max_fee_drag",
        "min_slippage_cushion",
        "max_volatility",
        "max_book_age_seconds",
        "max_settlement_friction",
    ):
        _require_payload_decimal_text(field_name, payload[field_name])
    _require_payload_decimal_text(
        "average_cost_shock_resilience_score",
        payload["average_cost_shock_resilience_score"],
        allow_none=True,
    )
    _require_payload_status("status", payload["status"])
    rows = _require_payload_list("rows", payload["rows"])
    for row_payload in rows:
        _validate_public_row_payload(row_payload)
    counts = _require_payload_list(
        "reason_code_counts",
        payload["reason_code_counts"],
    )
    for count_payload in counts:
        _validate_public_reason_code_count_payload(count_payload)
    _require_payload_text_list("reason_codes", payload["reason_codes"])
    _require_payload_digest_text(
        "derived_validation_digest",
        payload["derived_validation_digest"],
    )
    _require_payload_hard_flags("report payload", payload)


def _validate_public_row_payload(value: object) -> None:
    if type(value) is not dict:
        raise ValueError("row payload must use canonical row payload schema")
    _require_payload_keys(
        value,
        ROW_PAYLOAD_KEYS,
        "canonical row payload schema",
    )
    _require_payload_text("resilience_group_ref", value["resilience_group_ref"])
    _require_payload_datetime_text("observed_at", value["observed_at"])
    _require_payload_datetime_text(
        "last_book_update_at",
        value["last_book_update_at"],
    )
    for field_name in (
        "current_spread",
        "stressed_spread",
        "spread_widening",
        "spread_resilience_score",
        "baseline_depth",
        "stressed_depth",
        "depth_decay",
        "depth_resilience_score",
        "fee_drag",
        "fee_resilience_score",
        "slippage_cushion",
        "slippage_resilience_score",
        "volatility",
        "volatility_resilience_score",
        "book_age_seconds",
        "book_age_resilience_score",
        "settlement_friction",
        "settlement_resilience_score",
        "cost_shock_resilience_score",
    ):
        _require_payload_decimal_text(field_name, value[field_name])
    _require_payload_status("status", value["status"])
    _require_payload_text_list("reason_codes", value["reason_codes"])
    _require_payload_hard_flags("row payload", value)


def _validate_public_reason_code_count_payload(value: object) -> None:
    if type(value) is not dict:
        raise ValueError(
            "reason code count payload must use "
            "canonical reason code count payload schema",
        )
    _require_payload_keys(
        value,
        REASON_CODE_COUNT_PAYLOAD_KEYS,
        "canonical reason code count payload schema",
    )
    _require_payload_text("reason_code", value["reason_code"])
    _require_payload_decimal_text("count", value["count"])
    _require_payload_decimal_text("row_ratio", value["row_ratio"])
    _require_payload_hard_flags("reason code count payload", value)


def _summary_status(rows: tuple[ResearchMarketCostShockResilienceRow, ...]) -> str:
    if not rows or any(row.status == "block" for row in rows):
        return "block"
    if any(row.status == "watch" for row in rows):
        return "watch"
    return "pass"


def _summary_reason_codes(
    rows: tuple[ResearchMarketCostShockResilienceRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return ("no_cost_shock_resilience_observations",)
    if all(row.status == "pass" for row in rows):
        return ("cost_shock_resilience_pass",)
    return tuple(sorted({code for row in rows for code in row.reason_codes}))


def _reason_code_counts(
    rows: tuple[ResearchMarketCostShockResilienceRow, ...],
    reason_codes: tuple[str, ...],
) -> tuple[ResearchMarketCostShockResilienceReasonCodeCount, ...]:
    if not rows:
        return (
            ResearchMarketCostShockResilienceReasonCodeCount(
                reason_code=reason_codes[0],
                count=ONE,
                row_ratio=ZERO,
            ),
        )
    counts: Counter[str] = Counter()
    for row in rows:
        counts.update(row.reason_codes)
    total = _decimal_count(len(rows))
    return tuple(
        ResearchMarketCostShockResilienceReasonCodeCount(
            reason_code=reason_code,
            count=_decimal_count(count),
            row_ratio=_quantize(_decimal_count(count) / total),
        )
        for reason_code, count in sorted(counts.items(), key=lambda item: item[0])
    )


def _average_score(rows: tuple[ResearchMarketCostShockResilienceRow, ...]) -> Decimal | None:
    if not rows:
        return None
    return _quantize(
        sum((row.cost_shock_resilience_score for row in rows), ZERO)
        / _decimal_count(len(rows)),
    )


def _bounded_ratio(value: Decimal, denominator: Decimal) -> Decimal:
    if denominator <= ZERO:
        raise ValueError("denominator must be positive")
    return _quantize(min(ONE, value / denominator))


def _inverse_ratio_score(value: Decimal, zero_at: Decimal) -> Decimal:
    if zero_at <= ZERO:
        raise ValueError("zero_at must be positive")
    return _quantize(max(ZERO, ONE - (value / zero_at)))


def _age_seconds(generated_at: datetime, observed_at: datetime) -> Decimal:
    delta = generated_at - observed_at
    return _quantize(
        Decimal(delta.days * 86_400)
        + Decimal(delta.seconds)
        + (Decimal(delta.microseconds) / Decimal("1000000")),
    )


def _max_or_zero(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return ZERO
    return max(values)


def _min_or_zero(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return ZERO
    return min(values)


def _status_count(rows: tuple[ResearchMarketCostShockResilienceRow, ...], status: str) -> int:
    return sum(1 for row in rows if row.status == status)


def _observation_sort_key(
    value: ResearchMarketCostShockResilienceObservation,
) -> tuple[str, datetime]:
    return value.shock_case_key, value.observed_at


def _payload_value(value: object) -> object:
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, datetime):
        return value.isoformat()
    if is_dataclass(value) and not isinstance(value, type):
        return {
            field.name: _payload_value(getattr(value, field.name))
            for field in fields(value)
        }
    if isinstance(value, tuple):
        return [_payload_value(item) for item in value]
    if isinstance(value, list):
        return [_payload_value(item) for item in value]
    if isinstance(value, Mapping):
        return {str(key): _payload_value(item) for key, item in value.items()}
    if type(value) is float:
        raise ValueError("payload value must not be a float")
    return value


def _derived_report_digest(report: ResearchMarketCostShockResilienceReport) -> str:
    payload = _payload_value(report)
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    digest_payload = dict(payload)
    digest_payload["derived_validation_digest"] = ""
    _reject_unsafe_public_payload("report digest payload", digest_payload)
    encoded = json.dumps(digest_payload, sort_keys=True, separators=(",", ":"))
    return sha256(encoded.encode("utf-8")).hexdigest()


def _as_utc(field_name: str, value: datetime) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_exact_type(value: object, expected_type: type[object], field_name: str) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{field_name} must be {expected_type.__name__}")


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    try:
        return +value
    except InvalidOperation as exc:
        raise ValueError(f"{field_name} must be finite") from exc


def _require_positive_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return _quantize(normalized)


def _require_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return _quantize(normalized)


def _require_positive_whole_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_positive_decimal(field_name, value)
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{field_name} must be a whole count")
    return _quantize(normalized)


def _require_nonnegative_whole_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_nonnegative_decimal(field_name, value)
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{field_name} must be a whole count")
    return _quantize(normalized)


def _require_ratio_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < ZERO or normalized > ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return _quantize(normalized)


def _require_optional_ratio_decimal(field_name: str, value: object) -> Decimal | None:
    if value is None:
        return None
    return _require_ratio_decimal(field_name, value)


def _decimal_count(value: int) -> Decimal:
    if type(value) is not int:
        raise ValueError("count source must be an int")
    if value < 0:
        raise ValueError("count source must be nonnegative")
    return _quantize(Decimal(value))


def _quantize(value: Decimal) -> Decimal:
    return value.quantize(QUANTUM)


def _require_canonical_decimal(
    field_name: str,
    value: object,
    normalized: Decimal,
) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if value != normalized or not value.same_quantum(QUANTUM):
        raise ValueError(f"{field_name} must be quantized to six decimal places")
    return normalized


def _require_utc_datetime(field_name: str, value: object) -> datetime:
    normalized = _as_utc(field_name, value)
    if value != normalized or value.tzinfo is not UTC:
        raise ValueError(f"{field_name} must be normalized to UTC")
    return normalized


def _require_status(field_name: str, value: object) -> str:
    if type(value) is not str or value not in COST_SHOCK_RESILIENCE_STATUSES:
        raise ValueError(f"{field_name} must be pass, watch, or block")
    return value


def _require_label(field_name: str, value: object) -> str:
    if type(value) is not str or not LABEL_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a canonical label")
    return value


def _require_public_label(field_name: str, value: object) -> str:
    label = _require_label(field_name, value)
    if _is_unsafe_public_text(label):
        raise ValueError(f"{field_name} has unsafe public text")
    return label


def _require_reason_code(field_name: str, value: object) -> str:
    if type(value) is not str or not REASON_CODE_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a reason code")
    if _is_unsafe_public_text(value):
        raise ValueError(f"{field_name} has unsafe public text")
    return value


def _normalize_reason_codes(
    field_name: str,
    values: tuple[str, ...],
    *,
    allow_empty: bool,
) -> tuple[str, ...]:
    if type(values) is not tuple:
        raise ValueError(f"{field_name} must be a tuple")
    normalized = tuple(sorted(_require_reason_code(field_name, value) for value in values))
    if not allow_empty and not normalized:
        raise ValueError(f"{field_name} must not be empty")
    return normalized


def _require_hard_flags(label: str, value: object) -> None:
    if getattr(value, "paper_only", None) is not True:
        raise ValueError(f"{label}.paper_only must be True")
    if getattr(value, "report_only", None) is not True:
        raise ValueError(f"{label}.report_only must be True")
    if getattr(value, "readonly", None) is not True:
        raise ValueError(f"{label}.readonly must be True")


def _require_hex_digest(field_name: str, value: object) -> str:
    if type(value) is not str or len(value) != 64:
        raise ValueError(f"{field_name} must be a SHA-256 hex digest")
    try:
        int(value, 16)
    except ValueError as exc:
        raise ValueError(f"{field_name} must be a SHA-256 hex digest") from exc
    return value


def _require_payload_keys(
    payload: dict[str, Any],
    expected_keys: tuple[str, ...],
    schema_label: str,
) -> None:
    if type(payload) is not dict or tuple(payload.keys()) != expected_keys:
        raise ValueError(f"payload must use {schema_label}")


def _require_payload_text(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    return value


def _require_payload_datetime_text(field_name: str, value: object) -> str:
    text = _require_payload_text(field_name, value)
    if not text.endswith("+00:00"):
        raise ValueError(f"{field_name} must be a UTC datetime string")
    return text


def _require_payload_decimal_text(
    field_name: str,
    value: object,
    *,
    allow_none: bool = False,
) -> str | None:
    if value is None and allow_none:
        return None
    text = _require_payload_text(field_name, value)
    if not DECIMAL_TEXT_RE.fullmatch(text):
        raise ValueError(f"{field_name} must be a canonical decimal string")
    return text


def _require_payload_status(field_name: str, value: object) -> str:
    return _require_status(field_name, value)


def _require_payload_list(field_name: str, value: object) -> list[object]:
    if type(value) is not list:
        raise ValueError(f"{field_name} must be a list")
    return value


def _require_payload_text_list(field_name: str, value: object) -> list[object]:
    values = _require_payload_list(field_name, value)
    for item in values:
        _require_payload_text(field_name, item)
    return values


def _require_payload_digest_text(field_name: str, value: object) -> str:
    return _require_hex_digest(field_name, value)


def _require_payload_hard_flags(label: str, payload: dict[str, Any]) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if payload[field_name] is not True:
            raise ValueError(f"{label}.{field_name} must be True")


def _reject_unsafe_public_payload(label: str, value: object) -> None:
    if isinstance(value, Mapping):
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError(f"{label} keys must be strings")
            if _is_unsafe_public_text(key):
                raise ValueError(f"{label} exposes unsafe public key")
            _reject_unsafe_public_payload(f"{label}.{key}", item)
    elif isinstance(value, list):
        for item in value:
            _reject_unsafe_public_payload(label, item)
    elif type(value) is str and _is_unsafe_public_text(value):
        raise ValueError(f"{label} exposes unsafe public text")


def _is_unsafe_public_text(value: str) -> bool:
    normalized = value.lower()
    return any(fragment in normalized for fragment in UNSAFE_PUBLIC_FRAGMENTS)
