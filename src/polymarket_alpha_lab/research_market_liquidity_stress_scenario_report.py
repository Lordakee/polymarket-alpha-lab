"""Pure liquidity stress scenario report for caller-supplied research inputs.

The module is deterministic and side-effect free. Callers provide typed stress
scenario rows; the builder returns report-only status rows and reason codes.
"""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable
from dataclasses import InitVar, asdict, dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation
import hashlib
import json
from typing import Any


__all__ = (
    "DEFAULT_RESEARCH_MARKET_LIQUIDITY_STRESS_SCENARIO_CONFIG_VERSION",
    "ResearchMarketLiquidityStressScenarioConfig",
    "ResearchMarketLiquidityStressScenarioInput",
    "ResearchMarketLiquidityStressScenarioReasonCodeCount",
    "ResearchMarketLiquidityStressScenarioReport",
    "ResearchMarketLiquidityStressScenarioRow",
    "build_research_market_liquidity_stress_scenario_report",
    "research_market_liquidity_stress_scenario_report_payload",
)


DEFAULT_RESEARCH_MARKET_LIQUIDITY_STRESS_SCENARIO_CONFIG_VERSION = (
    "research-market-liquidity-stress-scenario-report-v0"
)
STATUSES = ("pass", "watch", "block")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
RATIO_QUANTUM = Decimal("0.000001")
DEFAULT_MIN_PASS_LIQUIDITY_SCORE = Decimal("0.750000")
DEFAULT_MIN_WATCH_LIQUIDITY_SCORE = Decimal("0.400000")

_UNSAFE_PUBLIC_FRAGMENTS = (
    "raw_market",
    "raw_source",
    "market_id",
    "source_id",
    "condition_id",
    "token_id",
    "source_url",
    "wallet",
    "auth",
    "order",
    "mutation",
    "network_url",
    "database",
    "db_",
    "persist",
    "signing",
    "private_key",
    "secret",
    "live trading",
    "live_mode",
    "buy",
    "sell",
    "position",
    "recommendation",
)


class _Missing:
    pass


_MISSING = _Missing()


@dataclass(frozen=True)
class ResearchMarketLiquidityStressScenarioConfig:
    config_version: str = DEFAULT_RESEARCH_MARKET_LIQUIDITY_STRESS_SCENARIO_CONFIG_VERSION
    min_pass_liquidity_score: Decimal = DEFAULT_MIN_PASS_LIQUIDITY_SCORE
    min_watch_liquidity_score: Decimal = DEFAULT_MIN_WATCH_LIQUIDITY_SCORE
    max_watch_depth_decline_ratio: Decimal = Decimal("0.250000")
    max_block_depth_decline_ratio: Decimal = Decimal("0.600000")
    max_watch_spread_widening_ratio: Decimal = Decimal("0.500000")
    max_block_spread_widening_ratio: Decimal = Decimal("1.500000")
    max_watch_fee_rate_bps: Decimal = Decimal("50.000000")
    max_block_fee_rate_bps: Decimal = Decimal("100.000000")
    watch_settlement_window_seconds: Decimal = Decimal("86400.000000")
    block_settlement_window_seconds: Decimal = Decimal("3600.000000")
    max_watch_information_shock_probability_move: Decimal = Decimal("0.080000")
    max_block_information_shock_probability_move: Decimal = Decimal("0.180000")
    depth_weight: Decimal = Decimal("0.300000")
    spread_weight: Decimal = Decimal("0.250000")
    fee_weight: Decimal = Decimal("0.150000")
    settlement_weight: Decimal = Decimal("0.150000")
    information_shock_weight: Decimal = Decimal("0.150000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_public_string("config_version", self.config_version)
        for field_name in (
            "min_pass_liquidity_score",
            "min_watch_liquidity_score",
            "max_watch_depth_decline_ratio",
            "max_block_depth_decline_ratio",
            "max_watch_information_shock_probability_move",
            "max_block_information_shock_probability_move",
            "depth_weight",
            "spread_weight",
            "fee_weight",
            "settlement_weight",
            "information_shock_weight",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_probability_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "max_watch_fee_rate_bps",
            "max_block_fee_rate_bps",
            "max_watch_spread_widening_ratio",
            "max_block_spread_widening_ratio",
            "watch_settlement_window_seconds",
            "block_settlement_window_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_positive_decimal(field_name, getattr(self, field_name)),
            )
        if self.min_pass_liquidity_score <= self.min_watch_liquidity_score:
            raise ValueError(
                "min_pass_liquidity_score must be greater than min_watch_liquidity_score",
            )
        if self.max_block_depth_decline_ratio <= self.max_watch_depth_decline_ratio:
            raise ValueError(
                "max_block_depth_decline_ratio must be greater than "
                "max_watch_depth_decline_ratio",
            )
        if self.max_block_spread_widening_ratio <= self.max_watch_spread_widening_ratio:
            raise ValueError(
                "max_block_spread_widening_ratio must be greater than "
                "max_watch_spread_widening_ratio",
            )
        if self.max_block_fee_rate_bps <= self.max_watch_fee_rate_bps:
            raise ValueError(
                "max_block_fee_rate_bps must be greater than max_watch_fee_rate_bps",
            )
        if self.watch_settlement_window_seconds <= self.block_settlement_window_seconds:
            raise ValueError(
                "watch_settlement_window_seconds must be greater than "
                "block_settlement_window_seconds",
            )
        if (
            self.max_block_information_shock_probability_move
            <= self.max_watch_information_shock_probability_move
        ):
            raise ValueError(
                "max_block_information_shock_probability_move must be greater than "
                "max_watch_information_shock_probability_move",
            )
        weight_sum = _quantize(
            self.depth_weight
            + self.spread_weight
            + self.fee_weight
            + self.settlement_weight
            + self.information_shock_weight,
        )
        if weight_sum != ONE:
            raise ValueError("component weights must sum to 1")
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class ResearchMarketLiquidityStressScenarioInput:
    scenario_key: str
    scenario_label: str
    baseline_depth_usd: Decimal
    stressed_depth_usd: Decimal
    baseline_spread_bps: Decimal
    stressed_spread_bps: Decimal
    fee_rate_bps: Decimal
    seconds_to_settlement: Decimal
    information_shock_probability_move: Decimal
    observed_at: datetime
    reason_codes: tuple[str, ...] = ()
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        for field_name in ("scenario_key", "scenario_label"):
            _require_public_string(field_name, getattr(self, field_name))
        for field_name in (
            "baseline_depth_usd",
            "baseline_spread_bps",
            "stressed_spread_bps",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_positive_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "stressed_depth_usd",
            "fee_rate_bps",
            "seconds_to_settlement",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "information_shock_probability_move",
            _require_probability_decimal(
                "information_shock_probability_move",
                self.information_shock_probability_move,
            ),
        )
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, allow_empty=True),
        )
        _require_hard_flags("scenario", self)
        _reject_unsafe_public_payload("scenario", _payload_value(self))


@dataclass(frozen=True)
class ResearchMarketLiquidityStressScenarioRow:
    scenario_key: str
    scenario_label: str
    baseline_depth_usd: Decimal
    stressed_depth_usd: Decimal
    depth_decline_ratio: Decimal
    baseline_spread_bps: Decimal
    stressed_spread_bps: Decimal
    spread_widening_ratio: Decimal
    fee_rate_bps: Decimal
    fee_friction_score: Decimal
    seconds_to_settlement: Decimal
    settlement_proximity_score: Decimal
    information_shock_probability_move: Decimal
    information_shock_score: Decimal
    observed_at: datetime
    liquidity_score: Decimal
    stress_status: str
    reason_codes: tuple[str, ...]
    config: InitVar[ResearchMarketLiquidityStressScenarioConfig | None] = None
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(
        self,
        config: ResearchMarketLiquidityStressScenarioConfig | None,
    ) -> None:
        for field_name in ("scenario_key", "scenario_label"):
            _require_public_string(field_name, getattr(self, field_name))
        for field_name in (
            "baseline_depth_usd",
            "baseline_spread_bps",
            "stressed_spread_bps",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_positive_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "stressed_depth_usd",
            "fee_rate_bps",
            "seconds_to_settlement",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "depth_decline_ratio",
            "fee_friction_score",
            "settlement_proximity_score",
            "information_shock_probability_move",
            "information_shock_score",
            "liquidity_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_probability_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "spread_widening_ratio",
            _require_nonnegative_decimal("spread_widening_ratio", self.spread_widening_ratio),
        )
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        _require_status("stress_status", self.stress_status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, allow_empty=False),
        )
        _require_hard_flags("row", self)
        _validate_row_consistency(self, config=config)
        _reject_unsafe_public_payload("row", _payload_value(self))


@dataclass(frozen=True)
class ResearchMarketLiquidityStressScenarioReasonCodeCount:
    reason_code: str
    count: Decimal
    scenario_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_reason_code("reason_code", self.reason_code)
        object.__setattr__(
            self,
            "count",
            _require_nonnegative_whole_decimal("count", self.count),
        )
        object.__setattr__(
            self,
            "scenario_ratio",
            _require_probability_decimal("scenario_ratio", self.scenario_ratio),
        )
        _require_hard_flags("reason_code_count", self)
        _reject_unsafe_public_payload("reason_code_count", _payload_value(self))


@dataclass(frozen=True)
class ResearchMarketLiquidityStressScenarioReport:
    generated_at: datetime
    config_version: str
    scenario_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    min_liquidity_score: Decimal
    max_depth_decline_ratio: Decimal
    max_spread_widening_ratio: Decimal
    max_fee_rate_bps: Decimal
    min_seconds_to_settlement: Decimal
    max_information_shock_probability_move: Decimal
    status: str
    rows: tuple[ResearchMarketLiquidityStressScenarioRow, ...]
    reason_code_counts: tuple[ResearchMarketLiquidityStressScenarioReasonCodeCount, ...]
    reason_codes: tuple[str, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_string("config_version", self.config_version)
        for field_name in (
            "scenario_count",
            "pass_count",
            "watch_count",
            "block_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_whole_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "min_liquidity_score",
            "max_depth_decline_ratio",
            "max_information_shock_probability_move",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_probability_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "max_spread_widening_ratio",
            "max_fee_rate_bps",
            "min_seconds_to_settlement",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
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
        _validate_report_consistency(self)
        expected_digest = _derived_validation_digest(self)
        if self.derived_validation_digest:
            _require_digest("derived_validation_digest", self.derived_validation_digest)
            if self.derived_validation_digest != expected_digest:
                raise ValueError("derived_validation_digest does not match report payload")
        else:
            object.__setattr__(self, "derived_validation_digest", expected_digest)
        _reject_unsafe_public_payload("report", _report_payload(self, include_digest=True))


def build_research_market_liquidity_stress_scenario_report(
    scenarios: Iterable[object],
    *,
    config: ResearchMarketLiquidityStressScenarioConfig,
    generated_at: datetime,
) -> ResearchMarketLiquidityStressScenarioReport:
    if type(config) is not ResearchMarketLiquidityStressScenarioConfig:
        raise ValueError("config must be a ResearchMarketLiquidityStressScenarioConfig")
    _require_hard_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    scenario_items = _normalize_scenarios(scenarios)
    for item in scenario_items:
        if item.observed_at > generated_at_utc:
            raise ValueError("observed_at must not be in the future")
    scenario_keys = tuple(item.scenario_key for item in scenario_items)
    if len(set(scenario_keys)) != len(scenario_keys):
        raise ValueError("scenario_key values must be unique")

    rows = tuple(
        _build_row(item, config=config)
        for item in sorted(scenario_items, key=lambda scenario: scenario.scenario_key)
    )
    reason_codes = _summary_reason_codes(rows)
    return ResearchMarketLiquidityStressScenarioReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        scenario_count=_decimal_count(len(rows)),
        pass_count=_decimal_count(_status_count(rows, "pass")),
        watch_count=_decimal_count(_status_count(rows, "watch")),
        block_count=_decimal_count(_status_count(rows, "block")),
        min_liquidity_score=_min_decimal(
            tuple(row.liquidity_score for row in rows),
            default=ZERO,
        ),
        max_depth_decline_ratio=_max_decimal(
            tuple(row.depth_decline_ratio for row in rows),
            default=ZERO,
        ),
        max_spread_widening_ratio=_max_decimal(
            tuple(row.spread_widening_ratio for row in rows),
            default=ZERO,
        ),
        max_fee_rate_bps=_max_decimal(tuple(row.fee_rate_bps for row in rows), default=ZERO),
        min_seconds_to_settlement=_min_decimal(
            tuple(row.seconds_to_settlement for row in rows),
            default=ZERO,
        ),
        max_information_shock_probability_move=_max_decimal(
            tuple(row.information_shock_probability_move for row in rows),
            default=ZERO,
        ),
        status=_summary_status(rows),
        rows=rows,
        reason_code_counts=_reason_code_counts(rows, reason_codes),
        reason_codes=reason_codes,
    )


def research_market_liquidity_stress_scenario_report_payload(
    report: ResearchMarketLiquidityStressScenarioReport | dict[str, object],
) -> dict[str, Any]:
    if type(report) is ResearchMarketLiquidityStressScenarioReport:
        _require_hard_flags("report", report)
        payload = _report_payload(report, include_digest=True)
        _reject_unsafe_public_payload("report", payload)
        return payload
    if type(report) is dict:
        _reject_unsafe_public_payload("report", report)
        _validate_payload_digest(report)
        return dict(report)
    raise ValueError("report must be a ResearchMarketLiquidityStressScenarioReport")


def _build_row(
    item: ResearchMarketLiquidityStressScenarioInput,
    *,
    config: ResearchMarketLiquidityStressScenarioConfig,
) -> ResearchMarketLiquidityStressScenarioRow:
    depth_decline_ratio = _bounded_ratio(
        item.baseline_depth_usd - item.stressed_depth_usd,
        item.baseline_depth_usd,
    )
    spread_widening_ratio = _nonnegative_ratio(
        item.stressed_spread_bps - item.baseline_spread_bps,
        item.baseline_spread_bps,
    )
    fee_friction_score = _capped_ratio(item.fee_rate_bps, config.max_block_fee_rate_bps)
    settlement_proximity_score = _settlement_proximity_score(
        item.seconds_to_settlement,
        config=config,
    )
    information_shock_score = _capped_ratio(
        item.information_shock_probability_move,
        config.max_block_information_shock_probability_move,
    )
    liquidity_score = _liquidity_score(
        depth_decline_ratio=depth_decline_ratio,
        spread_widening_ratio=spread_widening_ratio,
        fee_friction_score=fee_friction_score,
        settlement_proximity_score=settlement_proximity_score,
        information_shock_score=information_shock_score,
        config=config,
    )
    stress_status = _row_status(
        depth_decline_ratio=depth_decline_ratio,
        spread_widening_ratio=spread_widening_ratio,
        fee_rate_bps=item.fee_rate_bps,
        seconds_to_settlement=item.seconds_to_settlement,
        information_shock_probability_move=item.information_shock_probability_move,
        liquidity_score=liquidity_score,
        config=config,
    )
    return ResearchMarketLiquidityStressScenarioRow(
        scenario_key=item.scenario_key,
        scenario_label=item.scenario_label,
        baseline_depth_usd=item.baseline_depth_usd,
        stressed_depth_usd=item.stressed_depth_usd,
        depth_decline_ratio=depth_decline_ratio,
        baseline_spread_bps=item.baseline_spread_bps,
        stressed_spread_bps=item.stressed_spread_bps,
        spread_widening_ratio=spread_widening_ratio,
        fee_rate_bps=item.fee_rate_bps,
        fee_friction_score=fee_friction_score,
        seconds_to_settlement=item.seconds_to_settlement,
        settlement_proximity_score=settlement_proximity_score,
        information_shock_probability_move=item.information_shock_probability_move,
        information_shock_score=information_shock_score,
        observed_at=item.observed_at,
        liquidity_score=liquidity_score,
        stress_status=stress_status,
        reason_codes=_row_reason_codes(
            depth_decline_ratio=depth_decline_ratio,
            spread_widening_ratio=spread_widening_ratio,
            fee_rate_bps=item.fee_rate_bps,
            seconds_to_settlement=item.seconds_to_settlement,
            information_shock_probability_move=item.information_shock_probability_move,
            liquidity_score=liquidity_score,
            stress_status=stress_status,
            input_reason_codes=item.reason_codes,
            config=config,
        ),
        config=config,
    )


def _normalize_scenarios(
    scenarios: Iterable[object],
) -> tuple[ResearchMarketLiquidityStressScenarioInput, ...]:
    if isinstance(scenarios, (str, bytes)):
        raise ValueError("scenarios must be an iterable")
    try:
        values = tuple(scenarios)
    except TypeError as exc:
        raise ValueError("scenarios must be an iterable") from exc
    return tuple(_coerce_scenario(value) for value in values)


def _coerce_scenario(value: object) -> ResearchMarketLiquidityStressScenarioInput:
    if type(value) is ResearchMarketLiquidityStressScenarioInput:
        _require_hard_flags("scenario", value)
        return value
    _require_hard_flags("scenario", value)
    return ResearchMarketLiquidityStressScenarioInput(
        scenario_key=_field_value(value, "scenario_key"),
        scenario_label=_field_value(value, "scenario_label"),
        baseline_depth_usd=_field_value(value, "baseline_depth_usd"),
        stressed_depth_usd=_field_value(value, "stressed_depth_usd"),
        baseline_spread_bps=_field_value(value, "baseline_spread_bps"),
        stressed_spread_bps=_field_value(value, "stressed_spread_bps"),
        fee_rate_bps=_field_value(value, "fee_rate_bps"),
        seconds_to_settlement=_field_value(value, "seconds_to_settlement"),
        information_shock_probability_move=_field_value(
            value,
            "information_shock_probability_move",
        ),
        observed_at=_field_value(value, "observed_at"),
        reason_codes=_field_value(value, "reason_codes", default=()),
        paper_only=_field_value(value, "paper_only"),
        report_only=_field_value(value, "report_only"),
        readonly=_field_value(value, "readonly"),
    )


def _bounded_ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if numerator <= ZERO:
        return ZERO
    return _quantize(min(ONE, numerator / denominator))


def _nonnegative_ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if numerator <= ZERO:
        return ZERO
    return _quantize(numerator / denominator)


def _capped_ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if numerator <= ZERO:
        return ZERO
    return _quantize(min(ONE, numerator / denominator))


def _settlement_proximity_score(
    seconds_to_settlement: Decimal,
    *,
    config: ResearchMarketLiquidityStressScenarioConfig,
) -> Decimal:
    if seconds_to_settlement <= config.block_settlement_window_seconds:
        return ONE
    if seconds_to_settlement >= config.watch_settlement_window_seconds:
        return ZERO
    span = config.watch_settlement_window_seconds - config.block_settlement_window_seconds
    return _quantize(
        (config.watch_settlement_window_seconds - seconds_to_settlement) / span,
    )


def _liquidity_score(
    *,
    depth_decline_ratio: Decimal,
    spread_widening_ratio: Decimal,
    fee_friction_score: Decimal,
    settlement_proximity_score: Decimal,
    information_shock_score: Decimal,
    config: ResearchMarketLiquidityStressScenarioConfig,
) -> Decimal:
    stress_risk_score = (
        (depth_decline_ratio * config.depth_weight)
        + (min(ONE, spread_widening_ratio) * config.spread_weight)
        + (fee_friction_score * config.fee_weight)
        + (settlement_proximity_score * config.settlement_weight)
        + (information_shock_score * config.information_shock_weight)
    )
    return _quantize(max(ZERO, min(ONE, ONE - stress_risk_score)))


def _row_status(
    *,
    depth_decline_ratio: Decimal,
    spread_widening_ratio: Decimal,
    fee_rate_bps: Decimal,
    seconds_to_settlement: Decimal,
    information_shock_probability_move: Decimal,
    liquidity_score: Decimal,
    config: ResearchMarketLiquidityStressScenarioConfig,
) -> str:
    if (
        liquidity_score < config.min_watch_liquidity_score
        or depth_decline_ratio >= config.max_block_depth_decline_ratio
        or spread_widening_ratio >= config.max_block_spread_widening_ratio
        or fee_rate_bps >= config.max_block_fee_rate_bps
        or seconds_to_settlement <= config.block_settlement_window_seconds
        or information_shock_probability_move
        >= config.max_block_information_shock_probability_move
    ):
        return "block"
    if (
        liquidity_score < config.min_pass_liquidity_score
        or depth_decline_ratio > config.max_watch_depth_decline_ratio
        or spread_widening_ratio > config.max_watch_spread_widening_ratio
        or fee_rate_bps > config.max_watch_fee_rate_bps
        or seconds_to_settlement <= config.watch_settlement_window_seconds
        or information_shock_probability_move
        > config.max_watch_information_shock_probability_move
    ):
        return "watch"
    return "pass"


def _row_reason_codes(
    *,
    depth_decline_ratio: Decimal,
    spread_widening_ratio: Decimal,
    fee_rate_bps: Decimal,
    seconds_to_settlement: Decimal,
    information_shock_probability_move: Decimal,
    liquidity_score: Decimal,
    stress_status: str,
    input_reason_codes: tuple[str, ...],
    config: ResearchMarketLiquidityStressScenarioConfig,
) -> tuple[str, ...]:
    reason_codes: set[str] = set()
    for reason_code in input_reason_codes:
        reason_codes.add(f"input_{reason_code}")
    if depth_decline_ratio >= config.max_block_depth_decline_ratio:
        reason_codes.add("liquidity_depth_decline_severe_block")
    elif depth_decline_ratio > config.max_watch_depth_decline_ratio:
        reason_codes.add("liquidity_depth_decline_elevated_watch")
    if spread_widening_ratio >= config.max_block_spread_widening_ratio:
        reason_codes.add("liquidity_spread_widening_severe_block")
    elif spread_widening_ratio > config.max_watch_spread_widening_ratio:
        reason_codes.add("liquidity_spread_widening_elevated_watch")
    if fee_rate_bps >= config.max_block_fee_rate_bps:
        reason_codes.add("fee_friction_severe_block")
    elif fee_rate_bps > config.max_watch_fee_rate_bps:
        reason_codes.add("fee_friction_elevated_watch")
    if seconds_to_settlement <= config.block_settlement_window_seconds:
        reason_codes.add("settlement_window_imminent_block")
    elif seconds_to_settlement <= config.watch_settlement_window_seconds:
        reason_codes.add("settlement_window_near_watch")
    if (
        information_shock_probability_move
        >= config.max_block_information_shock_probability_move
    ):
        reason_codes.add("information_shock_severe_block")
    elif (
        information_shock_probability_move
        > config.max_watch_information_shock_probability_move
    ):
        reason_codes.add("information_shock_elevated_watch")
    if liquidity_score < config.min_watch_liquidity_score:
        reason_codes.add("liquidity_stress_score_low_block")
    elif liquidity_score < config.min_pass_liquidity_score:
        reason_codes.add("liquidity_stress_score_thin_watch")
    if stress_status == "pass":
        reason_codes.add("liquidity_stress_scenario_clear")
    return tuple(sorted(reason_codes))


def _summary_reason_codes(
    rows: tuple[ResearchMarketLiquidityStressScenarioRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return ("liquidity_stress_scenario_empty",)
    if all(row.stress_status == "pass" for row in rows):
        return ("liquidity_stress_scenario_pass",)
    return tuple(sorted({code for row in rows for code in row.reason_codes}))


def _summary_status(rows: tuple[ResearchMarketLiquidityStressScenarioRow, ...]) -> str:
    if not rows:
        return "watch"
    if any(row.stress_status == "block" for row in rows):
        return "block"
    if any(row.stress_status == "watch" for row in rows):
        return "watch"
    return "pass"


def _reason_code_counts(
    rows: tuple[ResearchMarketLiquidityStressScenarioRow, ...],
    reason_codes: tuple[str, ...],
) -> tuple[ResearchMarketLiquidityStressScenarioReasonCodeCount, ...]:
    if not rows:
        return (
            ResearchMarketLiquidityStressScenarioReasonCodeCount(
                reason_code=reason_codes[0],
                count=ONE,
                scenario_ratio=ZERO,
            ),
        )
    counts: Counter[str] = Counter()
    for row in rows:
        counts.update(row.reason_codes)
    scenario_count = _decimal_count(len(rows))
    return tuple(
        ResearchMarketLiquidityStressScenarioReasonCodeCount(
            reason_code=reason_code,
            count=_decimal_count(count),
            scenario_ratio=_quantize(Decimal(count) / scenario_count),
        )
        for reason_code, count in sorted(counts.items(), key=lambda item: item[0])
    )


def _status_count(
    rows: tuple[ResearchMarketLiquidityStressScenarioRow, ...],
    status: str,
) -> int:
    return sum(1 for row in rows if row.stress_status == status)


def _normalize_rows(
    rows: tuple[ResearchMarketLiquidityStressScenarioRow, ...],
) -> tuple[ResearchMarketLiquidityStressScenarioRow, ...]:
    if type(rows) is not tuple:
        raise ValueError("rows must be a tuple")
    for row in rows:
        if type(row) is not ResearchMarketLiquidityStressScenarioRow:
            raise ValueError(
                "rows must contain ResearchMarketLiquidityStressScenarioRow values",
            )
        _require_hard_flags("row", row)
    sorted_rows = tuple(sorted(rows, key=lambda row: row.scenario_key))
    if rows != sorted_rows:
        raise ValueError("rows must be sorted by scenario_key")
    return rows


def _normalize_reason_code_counts(
    counts: tuple[ResearchMarketLiquidityStressScenarioReasonCodeCount, ...],
) -> tuple[ResearchMarketLiquidityStressScenarioReasonCodeCount, ...]:
    if type(counts) is not tuple:
        raise ValueError("reason_code_counts must be a tuple")
    for count in counts:
        if type(count) is not ResearchMarketLiquidityStressScenarioReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "ResearchMarketLiquidityStressScenarioReasonCodeCount values",
            )
        _require_hard_flags("reason_code_count", count)
    sorted_counts = tuple(sorted(counts, key=lambda count: count.reason_code))
    if counts != sorted_counts:
        raise ValueError("reason_code_counts must be sorted by reason_code")
    return counts


def _validate_row_consistency(
    row: ResearchMarketLiquidityStressScenarioRow,
    *,
    config: ResearchMarketLiquidityStressScenarioConfig | None = None,
) -> None:
    if config is None:
        effective_config = ResearchMarketLiquidityStressScenarioConfig()
    else:
        if type(config) is not ResearchMarketLiquidityStressScenarioConfig:
            raise ValueError("config must be a ResearchMarketLiquidityStressScenarioConfig")
        _require_hard_flags("config", config)
        effective_config = config
    expected_depth_decline_ratio = _bounded_ratio(
        row.baseline_depth_usd - row.stressed_depth_usd,
        row.baseline_depth_usd,
    )
    if row.depth_decline_ratio != expected_depth_decline_ratio:
        raise ValueError("depth_decline_ratio must match depth fields")
    expected_spread_widening_ratio = _nonnegative_ratio(
        row.stressed_spread_bps - row.baseline_spread_bps,
        row.baseline_spread_bps,
    )
    if row.spread_widening_ratio != expected_spread_widening_ratio:
        raise ValueError("spread_widening_ratio must match spread fields")
    expected_status = _row_status(
        depth_decline_ratio=row.depth_decline_ratio,
        spread_widening_ratio=row.spread_widening_ratio,
        fee_rate_bps=row.fee_rate_bps,
        seconds_to_settlement=row.seconds_to_settlement,
        information_shock_probability_move=row.information_shock_probability_move,
        liquidity_score=row.liquidity_score,
        config=effective_config,
    )
    if row.stress_status != expected_status:
        raise ValueError("stress_status must match row criteria including liquidity_score")


def _validate_report_consistency(report: ResearchMarketLiquidityStressScenarioReport) -> None:
    if report.scenario_count != _decimal_count(len(report.rows)):
        raise ValueError("derived_validation_digest scenario_count must match rows")
    if report.pass_count != _decimal_count(_status_count(report.rows, "pass")):
        raise ValueError("derived_validation_digest pass_count must match rows")
    if report.watch_count != _decimal_count(_status_count(report.rows, "watch")):
        raise ValueError("derived_validation_digest watch_count must match rows")
    if report.block_count != _decimal_count(_status_count(report.rows, "block")):
        raise ValueError("derived_validation_digest block_count must match rows")
    if report.min_liquidity_score != _min_decimal(
        tuple(row.liquidity_score for row in report.rows),
        default=ZERO,
    ):
        raise ValueError("min_liquidity_score must match rows")
    if report.max_depth_decline_ratio != _max_decimal(
        tuple(row.depth_decline_ratio for row in report.rows),
        default=ZERO,
    ):
        raise ValueError("max_depth_decline_ratio must match rows")
    if report.max_spread_widening_ratio != _max_decimal(
        tuple(row.spread_widening_ratio for row in report.rows),
        default=ZERO,
    ):
        raise ValueError("max_spread_widening_ratio must match rows")
    if report.max_fee_rate_bps != _max_decimal(
        tuple(row.fee_rate_bps for row in report.rows),
        default=ZERO,
    ):
        raise ValueError("max_fee_rate_bps must match rows")
    if report.min_seconds_to_settlement != _min_decimal(
        tuple(row.seconds_to_settlement for row in report.rows),
        default=ZERO,
    ):
        raise ValueError("min_seconds_to_settlement must match rows")
    if report.max_information_shock_probability_move != _max_decimal(
        tuple(row.information_shock_probability_move for row in report.rows),
        default=ZERO,
    ):
        raise ValueError("max_information_shock_probability_move must match rows")
    if report.reason_codes != _summary_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")
    if report.status != _summary_status(report.rows):
        raise ValueError("status must match rows")


def _field_value(value: object, field_name: str, *, default: object = _MISSING) -> object:
    if is_dataclass(value) and not isinstance(value, type):
        for field in fields(value):
            if field.name == field_name:
                return getattr(value, field_name)
    if hasattr(value, field_name):
        return getattr(value, field_name)
    if default is not _MISSING:
        return default
    raise ValueError(f"{field_name} is required")


def _payload_value(value: object) -> object:
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, datetime):
        return value.isoformat()
    if is_dataclass(value) and not isinstance(value, type):
        return {field.name: _payload_value(getattr(value, field.name)) for field in fields(value)}
    if isinstance(value, tuple):
        return [_payload_value(item) for item in value]
    if isinstance(value, list):
        return [_payload_value(item) for item in value]
    if isinstance(value, dict):
        return {str(key): _payload_value(item) for key, item in value.items()}
    return value


def _report_payload(
    report: ResearchMarketLiquidityStressScenarioReport,
    *,
    include_digest: bool,
) -> dict[str, Any]:
    payload = _payload_value(asdict(report))
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    if not include_digest:
        payload.pop("derived_validation_digest", None)
    return payload


def _derived_validation_digest(report: ResearchMarketLiquidityStressScenarioReport) -> str:
    return _payload_digest(_report_payload(report, include_digest=False))


def _payload_digest(payload: dict[str, object]) -> str:
    encoded = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _validate_payload_digest(payload: dict[str, object]) -> None:
    digest = payload.get("derived_validation_digest")
    _require_digest("derived_validation_digest", digest)
    comparable = dict(payload)
    comparable.pop("derived_validation_digest", None)
    if digest != _payload_digest(comparable):
        raise ValueError("derived_validation_digest does not match report payload")


def _as_utc(field_name: str, value: datetime) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


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


def _require_probability_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < ZERO or normalized > ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return _quantize(normalized)


def _require_nonnegative_whole_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_nonnegative_decimal(field_name, value)
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{field_name} must be a whole count")
    return normalized


def _decimal_count(value: int) -> Decimal:
    if type(value) is not int:
        raise ValueError("count source must be an int")
    if value < 0:
        raise ValueError("count source must be nonnegative")
    return Decimal(value).quantize(RATIO_QUANTUM)


def _quantize(value: Decimal) -> Decimal:
    return value.quantize(RATIO_QUANTUM)


def _min_decimal(values: tuple[Decimal, ...], *, default: Decimal) -> Decimal:
    if not values:
        return default
    return min(values)


def _max_decimal(values: tuple[Decimal, ...], *, default: Decimal) -> Decimal:
    if not values:
        return default
    return max(values)


def _require_public_string(field_name: str, value: object) -> None:
    if type(value) is not str or not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a nonempty public string")
    if _has_unsafe_public_fragment(value):
        raise ValueError(f"{field_name} contains unsafe public value")


def _require_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in STATUSES:
        raise ValueError(f"{field_name} must be one of {STATUSES}")


def _normalize_reason_codes(
    field_name: str,
    values: object,
    *,
    allow_empty: bool,
) -> tuple[str, ...]:
    if type(values) is not tuple:
        raise ValueError(f"{field_name} must be a tuple")
    normalized: list[str] = []
    for value in values:
        _require_reason_code(field_name, value)
        normalized.append(value)
    if not allow_empty and not normalized:
        raise ValueError(f"{field_name} must be nonempty")
    return tuple(sorted(set(normalized)))


def _require_reason_code(field_name: str, value: object) -> None:
    if type(value) is not str or not value or value.strip() != value:
        raise ValueError(f"{field_name} must contain canonical strings")
    if value.lower() != value or " " in value:
        raise ValueError(f"{field_name} must contain lowercase reason codes")
    if _has_unsafe_public_fragment(value):
        raise ValueError(f"{field_name} contains unsafe public value")


def _require_digest(field_name: str, value: object) -> None:
    if type(value) is not str or len(value) != 64:
        raise ValueError(f"{field_name} must be a sha256 hex digest")
    if any(char not in "0123456789abcdef" for char in value):
        raise ValueError(f"{field_name} must be a sha256 hex digest")


def _require_hard_flags(label: str, value: object) -> None:
    for flag_name in ("paper_only", "report_only", "readonly"):
        if not hasattr(value, flag_name):
            raise ValueError(f"{label}.{flag_name} is required")
        if getattr(value, flag_name) is not True:
            raise ValueError(f"{label}.{flag_name} must be True")


def _reject_unsafe_public_payload(label: str, value: object, path: str = "") -> None:
    current_path = path or label
    if value is None or type(value) is bool:
        return
    if type(value) is str:
        if _has_unsafe_public_fragment(value):
            raise ValueError(f"unsafe public value in {current_path}")
        return
    if isinstance(value, Decimal):
        if type(value) is not Decimal:
            raise ValueError(f"{current_path} must be exactly Decimal")
        if not value.is_finite():
            raise ValueError(f"{current_path} must be finite")
        return
    if isinstance(value, datetime):
        if type(value) is not datetime:
            raise ValueError(f"{current_path} must be a datetime")
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError(f"{current_path} must be timezone-aware")
        return
    if type(value) in (int, float):
        raise ValueError(f"unsafe public numeric value in {current_path}")
    if is_dataclass(value) and not isinstance(value, type):
        _reject_unsafe_public_payload(label, _payload_value(value), current_path)
        return
    if isinstance(value, dict):
        for key, nested_value in value.items():
            if type(key) is not str:
                raise ValueError("unsafe public payload keys must be strings")
            if _has_unsafe_public_fragment(key):
                raise ValueError(f"unsafe public field in {label}: {key}")
            nested_path = key if not path else f"{path}.{key}"
            if key in {"paper_only", "report_only", "readonly"} and nested_value is not True:
                raise ValueError(f"{nested_path} must be True")
            _reject_unsafe_public_payload(label, nested_value, nested_path)
        return
    if isinstance(value, (list, tuple)):
        for index, nested_value in enumerate(value):
            nested_path = f"{current_path}[{index}]"
            _reject_unsafe_public_payload(label, nested_value, nested_path)
        return
    raise ValueError(f"{current_path} is not JSON serializable")


def _has_unsafe_public_fragment(value: str) -> bool:
    lowered = value.lower()
    return any(fragment in lowered for fragment in _UNSAFE_PUBLIC_FRAGMENTS)
