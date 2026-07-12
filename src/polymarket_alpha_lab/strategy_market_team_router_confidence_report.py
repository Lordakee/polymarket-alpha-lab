"""Pure paper-only market team router confidence report."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import asdict, dataclass, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
import json
from typing import Any

from polymarket_alpha_lab.team_paper_guard import require_paper_only_flags


DEFAULT_STRATEGY_MARKET_TEAM_ROUTER_CONFIDENCE_CONFIG_VERSION = (
    "strategy-market-team-router-confidence-report-v0"
)
CONFIDENCE_HIGH = "high"
CONFIDENCE_MEDIUM = "medium"
CONFIDENCE_LOW = "low"
STRATEGY_MARKET_TEAM_ROUTER_CONFIDENCE_BANDS = (
    CONFIDENCE_HIGH,
    CONFIDENCE_MEDIUM,
    CONFIDENCE_LOW,
)

STATUS_PASS = "pass"
STATUS_WATCH = "watch"
STATUS_BLOCK = "block"
_STATUSES = (STATUS_PASS, STATUS_WATCH, STATUS_BLOCK)

REASON_CLEAR = "market_team_router_confidence_clear"
REASON_NO_INPUTS = "market_team_router_confidence_no_inputs"
REASON_SOURCE_FRESHNESS_BLOCK = "source_freshness_block"
REASON_SOURCE_FRESHNESS_WATCH = "source_freshness_watch"
REASON_CALIBRATION_READINESS_BLOCK = "calibration_readiness_block"
REASON_CALIBRATION_READINESS_WATCH = "calibration_readiness_watch"
REASON_COST_GATE_MARGIN_BLOCK = "cost_gate_margin_block"
REASON_COST_GATE_MARGIN_WATCH = "cost_gate_margin_watch"
REASON_LIQUIDITY_BLOCK = "liquidity_block"
REASON_LIQUIDITY_WATCH = "liquidity_watch"
REASON_SPREAD_BLOCK = "spread_block"
REASON_SPREAD_WATCH = "spread_watch"

_BLOCKER_REASON_PRIORITY = (
    REASON_SOURCE_FRESHNESS_BLOCK,
    REASON_CALIBRATION_READINESS_BLOCK,
    REASON_COST_GATE_MARGIN_BLOCK,
    REASON_LIQUIDITY_BLOCK,
    REASON_SPREAD_BLOCK,
    REASON_SOURCE_FRESHNESS_WATCH,
    REASON_CALIBRATION_READINESS_WATCH,
    REASON_COST_GATE_MARGIN_WATCH,
    REASON_LIQUIDITY_WATCH,
    REASON_SPREAD_WATCH,
    REASON_CLEAR,
)
_REPORT_BLOCKER_REASON_PRIORITY = _BLOCKER_REASON_PRIORITY + (REASON_NO_INPUTS,)
_BLOCK_REASONS = frozenset(
    (
        REASON_SOURCE_FRESHNESS_BLOCK,
        REASON_CALIBRATION_READINESS_BLOCK,
        REASON_COST_GATE_MARGIN_BLOCK,
        REASON_LIQUIDITY_BLOCK,
        REASON_SPREAD_BLOCK,
    ),
)
_WATCH_REASONS = frozenset(
    (
        REASON_SOURCE_FRESHNESS_WATCH,
        REASON_CALIBRATION_READINESS_WATCH,
        REASON_COST_GATE_MARGIN_WATCH,
        REASON_LIQUIDITY_WATCH,
        REASON_SPREAD_WATCH,
    ),
)
_BAND_SORT_WEIGHT = {CONFIDENCE_LOW: 0, CONFIDENCE_MEDIUM: 1, CONFIDENCE_HIGH: 2}

_ZERO = Decimal("0.000000")
_ONE = Decimal("1.000000")
_FOUR = Decimal("4.000000")
_QUANTUM = Decimal("0.000001")
_COUNT_QUANTUM = Decimal("1")
_MICROSECONDS_PER_SECOND = Decimal("1000000.000000")
_CLEAR_COST_CONFIDENCE_WEIGHT = Decimal("0.070137")
_WATCH_REASON_PENALTY = Decimal("0.034000")
_BLOCK_REASON_PENALTY = Decimal("0.017500")
_DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)

_DOMAIN_TEAM_PREFIXES = {
    "politics": "team_politics",
    "crypto": "team_crypto",
    "macro": "team_macro",
    "energy": "team_energy",
    "weather": "team_weather",
    "sports.soccer": "team_soccer",
    "soccer": "team_soccer",
    "sports.basketball": "team_basketball",
    "basketball": "team_basketball",
    "sports.tennis": "team_tennis",
    "tennis": "team_tennis",
    "equities": "team_equities",
    "gold": "team_gold",
}

_UNSAFE_PUBLIC_FRAGMENTS = (
    "candidate_id",
    "candidate_key",
    "market_id",
    "market_slug",
    "question",
    "http://",
    "https://",
    "source_url",
    "source_text",
    "raw_source",
    "raw_text",
    "dsn",
    "table_name",
    "token",
    "secret",
    "credential",
    "private_key",
    "wallet",
    "order",
    "trade",
    "live",
    "auth",
    "sizing",
    "recommendation",
    "postgres://",
)
_UNSAFE_PUBLIC_KEYS = frozenset(
    (
        "candidate_id",
        "candidate_key",
        "market_id",
        "market_slug",
        "question",
        "source_url",
        "source_text",
        "raw_source",
        "raw_text",
        "dsn",
        "table_name",
        "token",
        "wallet",
        "order",
        "trade",
        "live",
        "auth",
        "sizing",
        "recommendation",
    ),
)

__all__ = (
    "DEFAULT_STRATEGY_MARKET_TEAM_ROUTER_CONFIDENCE_CONFIG_VERSION",
    "STRATEGY_MARKET_TEAM_ROUTER_CONFIDENCE_BANDS",
    "StrategyMarketTeamRouterConfidenceConfig",
    "StrategyMarketTeamRouterConfidenceInput",
    "StrategyMarketTeamRouterConfidenceReport",
    "StrategyMarketTeamRouterConfidenceRow",
    "build_strategy_market_team_router_confidence_report",
    "strategy_market_team_router_confidence_report_digest",
    "strategy_market_team_router_confidence_report_payload",
)


class _FinalDataclass:
    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        for base in cls.__bases__:
            if base is not _FinalDataclass and issubclass(base, _FinalDataclass):
                raise TypeError(f"{base.__name__} subclass is not allowed")


@dataclass(frozen=True)
class StrategyMarketTeamRouterConfidenceConfig(_FinalDataclass):
    config_version: str = DEFAULT_STRATEGY_MARKET_TEAM_ROUTER_CONFIDENCE_CONFIG_VERSION
    fresh_source_age_seconds: Decimal = Decimal("3600.000000")
    stale_source_age_seconds: Decimal = Decimal("86400.000000")
    min_pass_calibration_readiness_score: Decimal = Decimal("0.700000")
    min_watch_calibration_readiness_score: Decimal = Decimal("0.500000")
    min_pass_cost_gate_margin_score: Decimal = Decimal("0.250000")
    min_watch_cost_gate_margin_score: Decimal = Decimal("0.100000")
    min_pass_liquidity_score: Decimal = Decimal("0.700000")
    min_watch_liquidity_score: Decimal = Decimal("0.500000")
    max_pass_spread_score: Decimal = Decimal("0.200000")
    max_watch_spread_score: Decimal = Decimal("0.400000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, StrategyMarketTeamRouterConfidenceConfig, "config")
        object.__setattr__(
            self,
            "config_version",
            _require_public_text("config_version", self.config_version),
        )
        if self.config_version != DEFAULT_STRATEGY_MARKET_TEAM_ROUTER_CONFIDENCE_CONFIG_VERSION:
            raise ValueError("config_version must be the supported config version")
        for field_name in ("fresh_source_age_seconds", "stale_source_age_seconds"):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "min_pass_calibration_readiness_score",
            "min_watch_calibration_readiness_score",
            "min_pass_cost_gate_margin_score",
            "min_watch_cost_gate_margin_score",
            "min_pass_liquidity_score",
            "min_watch_liquidity_score",
            "max_pass_spread_score",
            "max_watch_spread_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_unit_decimal(field_name, getattr(self, field_name)),
            )
        if self.fresh_source_age_seconds > self.stale_source_age_seconds:
            raise ValueError("stale_source_age_seconds must be at least fresh_source_age_seconds")
        _require_min_threshold_pair(
            "min_pass_calibration_readiness_score",
            self.min_pass_calibration_readiness_score,
            "min_watch_calibration_readiness_score",
            self.min_watch_calibration_readiness_score,
        )
        _require_min_threshold_pair(
            "min_pass_cost_gate_margin_score",
            self.min_pass_cost_gate_margin_score,
            "min_watch_cost_gate_margin_score",
            self.min_watch_cost_gate_margin_score,
        )
        _require_min_threshold_pair(
            "min_pass_liquidity_score",
            self.min_pass_liquidity_score,
            "min_watch_liquidity_score",
            self.min_watch_liquidity_score,
        )
        if self.max_pass_spread_score > self.max_watch_spread_score:
            raise ValueError("max_pass_spread_score must not exceed max_watch_spread_score")
        require_paper_only_flags("market team router confidence config", self)


@dataclass(frozen=True)
class StrategyMarketTeamRouterConfidenceInput(_FinalDataclass):
    routing_ref: str
    market_category: str
    domain_label: str
    source_observed_at: datetime
    calibration_readiness_score: Decimal
    cost_gate_margin_score: Decimal
    liquidity_score: Decimal
    spread_score: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, StrategyMarketTeamRouterConfidenceInput, "input")
        for field_name in ("routing_ref", "market_category", "domain_label"):
            object.__setattr__(
                self,
                field_name,
                _require_public_text(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "source_observed_at",
            _as_utc("source_observed_at", self.source_observed_at),
        )
        for field_name in (
            "calibration_readiness_score",
            "cost_gate_margin_score",
            "liquidity_score",
            "spread_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_unit_decimal(field_name, getattr(self, field_name)),
            )
        require_paper_only_flags("market team router confidence input", self)


@dataclass(frozen=True)
class StrategyMarketTeamRouterConfidenceRow(_FinalDataclass):
    routing_ref: str
    market_category: str
    domain_label: str
    recommended_specialist_team: str
    confidence_band: str
    confidence_score: Decimal
    source_observed_at: datetime
    source_age_seconds: Decimal
    fresh_source_age_seconds: Decimal
    stale_source_age_seconds: Decimal
    source_freshness_score: Decimal
    calibration_readiness_score: Decimal
    min_pass_calibration_readiness_score: Decimal
    min_watch_calibration_readiness_score: Decimal
    cost_gate_margin_score: Decimal
    min_pass_cost_gate_margin_score: Decimal
    min_watch_cost_gate_margin_score: Decimal
    liquidity_score: Decimal
    min_pass_liquidity_score: Decimal
    min_watch_liquidity_score: Decimal
    spread_score: Decimal
    max_pass_spread_score: Decimal
    max_watch_spread_score: Decimal
    blocker_reasons: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, StrategyMarketTeamRouterConfidenceRow, "row")
        for field_name in (
            "routing_ref",
            "market_category",
            "domain_label",
            "recommended_specialist_team",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_public_text(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "confidence_band",
            _require_confidence_band("confidence_band", self.confidence_band),
        )
        object.__setattr__(
            self,
            "source_observed_at",
            _as_utc("source_observed_at", self.source_observed_at),
        )
        for field_name in (
            "confidence_score",
            "source_freshness_score",
            "calibration_readiness_score",
            "min_pass_calibration_readiness_score",
            "min_watch_calibration_readiness_score",
            "cost_gate_margin_score",
            "min_pass_cost_gate_margin_score",
            "min_watch_cost_gate_margin_score",
            "liquidity_score",
            "min_pass_liquidity_score",
            "min_watch_liquidity_score",
            "spread_score",
            "max_pass_spread_score",
            "max_watch_spread_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_unit_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "source_age_seconds",
            "fresh_source_age_seconds",
            "stale_source_age_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "blocker_reasons",
            _normalize_blocker_reasons(
                "blocker_reasons",
                self.blocker_reasons,
                _BLOCKER_REASON_PRIORITY,
            ),
        )
        _validate_row(self)
        require_paper_only_flags("market team router confidence row", self)


@dataclass(frozen=True)
class StrategyMarketTeamRouterConfidenceReport(_FinalDataclass):
    generated_at: datetime
    config_version: str
    input_count: Decimal
    team_count: Decimal
    high_confidence_count: Decimal
    medium_confidence_count: Decimal
    low_confidence_count: Decimal
    average_confidence_score: Decimal
    lowest_confidence_score: Decimal
    highest_source_age_seconds: Decimal
    status: str
    blocker_reasons: tuple[str, ...]
    rows: tuple[StrategyMarketTeamRouterConfidenceRow, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, StrategyMarketTeamRouterConfidenceReport, "report")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        object.__setattr__(
            self,
            "config_version",
            _require_public_text("config_version", self.config_version),
        )
        if self.config_version != DEFAULT_STRATEGY_MARKET_TEAM_ROUTER_CONFIDENCE_CONFIG_VERSION:
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "input_count",
            "team_count",
            "high_confidence_count",
            "medium_confidence_count",
            "low_confidence_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_count_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in ("average_confidence_score", "lowest_confidence_score"):
            object.__setattr__(
                self,
                field_name,
                _normalize_unit_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "highest_source_age_seconds",
            _normalize_nonnegative_decimal(
                "highest_source_age_seconds",
                self.highest_source_age_seconds,
            ),
        )
        object.__setattr__(self, "status", _require_status("status", self.status))
        object.__setattr__(
            self,
            "blocker_reasons",
            _normalize_blocker_reasons(
                "blocker_reasons",
                self.blocker_reasons,
                _REPORT_BLOCKER_REASON_PRIORITY,
            ),
        )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        _validate_report(self)
        require_paper_only_flags("market team router confidence report", self)
        expected_digest = _derived_validation_digest(self)
        if self.derived_validation_digest:
            _require_digest("derived_validation_digest", self.derived_validation_digest)
            if self.derived_validation_digest != expected_digest:
                raise ValueError("derived_validation_digest must match report payload")
        object.__setattr__(self, "derived_validation_digest", expected_digest)

    @property
    def public_payload(self) -> dict[str, Any]:
        return strategy_market_team_router_confidence_report_payload(self)


def build_strategy_market_team_router_confidence_report(
    inputs: Iterable[StrategyMarketTeamRouterConfidenceInput],
    *,
    config: StrategyMarketTeamRouterConfidenceConfig | None = None,
    generated_at: datetime,
) -> StrategyMarketTeamRouterConfidenceReport:
    cfg = config or StrategyMarketTeamRouterConfidenceConfig()
    _require_exact_type(cfg, StrategyMarketTeamRouterConfidenceConfig, "config")
    require_paper_only_flags("market team router confidence config", cfg)
    generated_at_utc = _as_utc("generated_at", generated_at)
    normalized_inputs = _normalize_inputs(inputs)
    rows = tuple(
        sorted(
            (_row_from_input(item, config=cfg, generated_at=generated_at_utc) for item in normalized_inputs),
            key=_row_sort_key,
        ),
    )
    return StrategyMarketTeamRouterConfidenceReport(
        generated_at=generated_at_utc,
        config_version=cfg.config_version,
        input_count=_count_decimal(len(rows)),
        team_count=_count_decimal(len({row.recommended_specialist_team for row in rows})),
        high_confidence_count=_band_count(rows, CONFIDENCE_HIGH),
        medium_confidence_count=_band_count(rows, CONFIDENCE_MEDIUM),
        low_confidence_count=_band_count(rows, CONFIDENCE_LOW),
        average_confidence_score=_average_confidence_score(rows),
        lowest_confidence_score=_min_decimal(row.confidence_score for row in rows),
        highest_source_age_seconds=_max_decimal(row.source_age_seconds for row in rows),
        status=_report_status(rows),
        blocker_reasons=_report_blocker_reasons(rows),
        rows=rows,
    )


def strategy_market_team_router_confidence_report_payload(value: object) -> dict[str, Any]:
    if type(value) not in (dict, StrategyMarketTeamRouterConfidenceReport):
        raise ValueError("payload input must be a report or dict")
    payload = _payload_value(value)
    if type(payload) is not dict:
        raise ValueError("payload must be a dict")
    _validate_payload_flags(payload, "payload")
    _reject_unsafe_public_payload(payload)
    _validate_payload_digest(payload)
    return payload


def strategy_market_team_router_confidence_report_digest(
    report: StrategyMarketTeamRouterConfidenceReport,
) -> str:
    _require_exact_type(report, StrategyMarketTeamRouterConfidenceReport, "report")
    return report.derived_validation_digest


def _row_from_input(
    item: StrategyMarketTeamRouterConfidenceInput,
    *,
    config: StrategyMarketTeamRouterConfidenceConfig,
    generated_at: datetime,
) -> StrategyMarketTeamRouterConfidenceRow:
    source_age_seconds = _age_seconds(generated_at, item.source_observed_at)
    source_freshness_score = _source_freshness_score(
        source_age_seconds,
        config.stale_source_age_seconds,
    )
    blocker_reasons = _row_blocker_reasons(
        item,
        source_age_seconds=source_age_seconds,
        config=config,
    )
    return StrategyMarketTeamRouterConfidenceRow(
        routing_ref=item.routing_ref,
        market_category=item.market_category,
        domain_label=item.domain_label,
        recommended_specialist_team=_specialist_team_label(
            item.market_category,
            item.domain_label,
        ),
        confidence_band=_confidence_band_from_reasons(blocker_reasons),
        confidence_score=_confidence_score(
            source_freshness_score=source_freshness_score,
            calibration_readiness_score=item.calibration_readiness_score,
            cost_gate_margin_score=item.cost_gate_margin_score,
            liquidity_score=item.liquidity_score,
            spread_score=item.spread_score,
            blocker_reasons=blocker_reasons,
        ),
        source_observed_at=item.source_observed_at,
        source_age_seconds=source_age_seconds,
        fresh_source_age_seconds=config.fresh_source_age_seconds,
        stale_source_age_seconds=config.stale_source_age_seconds,
        source_freshness_score=source_freshness_score,
        calibration_readiness_score=item.calibration_readiness_score,
        min_pass_calibration_readiness_score=config.min_pass_calibration_readiness_score,
        min_watch_calibration_readiness_score=config.min_watch_calibration_readiness_score,
        cost_gate_margin_score=item.cost_gate_margin_score,
        min_pass_cost_gate_margin_score=config.min_pass_cost_gate_margin_score,
        min_watch_cost_gate_margin_score=config.min_watch_cost_gate_margin_score,
        liquidity_score=item.liquidity_score,
        min_pass_liquidity_score=config.min_pass_liquidity_score,
        min_watch_liquidity_score=config.min_watch_liquidity_score,
        spread_score=item.spread_score,
        max_pass_spread_score=config.max_pass_spread_score,
        max_watch_spread_score=config.max_watch_spread_score,
        blocker_reasons=blocker_reasons,
    )


def _row_blocker_reasons(
    item: StrategyMarketTeamRouterConfidenceInput,
    *,
    source_age_seconds: Decimal,
    config: StrategyMarketTeamRouterConfidenceConfig,
) -> tuple[str, ...]:
    reasons: list[str] = []
    _append_age_reason(
        reasons,
        age_seconds=source_age_seconds,
        fresh=config.fresh_source_age_seconds,
        stale=config.stale_source_age_seconds,
    )
    _append_low_threshold_reason(
        reasons,
        metric=item.calibration_readiness_score,
        watch=config.min_pass_calibration_readiness_score,
        block=config.min_watch_calibration_readiness_score,
        watch_code=REASON_CALIBRATION_READINESS_WATCH,
        block_code=REASON_CALIBRATION_READINESS_BLOCK,
    )
    _append_low_threshold_reason(
        reasons,
        metric=item.cost_gate_margin_score,
        watch=config.min_pass_cost_gate_margin_score,
        block=config.min_watch_cost_gate_margin_score,
        watch_code=REASON_COST_GATE_MARGIN_WATCH,
        block_code=REASON_COST_GATE_MARGIN_BLOCK,
    )
    _append_low_threshold_reason(
        reasons,
        metric=item.liquidity_score,
        watch=config.min_pass_liquidity_score,
        block=config.min_watch_liquidity_score,
        watch_code=REASON_LIQUIDITY_WATCH,
        block_code=REASON_LIQUIDITY_BLOCK,
    )
    _append_high_threshold_reason(
        reasons,
        metric=item.spread_score,
        watch=config.max_pass_spread_score,
        block=config.max_watch_spread_score,
        watch_code=REASON_SPREAD_WATCH,
        block_code=REASON_SPREAD_BLOCK,
    )
    if not reasons:
        reasons.append(REASON_CLEAR)
    return _normalize_blocker_reasons(
        "blocker_reasons",
        tuple(reasons),
        _BLOCKER_REASON_PRIORITY,
    )


def _append_age_reason(
    reasons: list[str],
    *,
    age_seconds: Decimal,
    fresh: Decimal,
    stale: Decimal,
) -> None:
    if age_seconds > stale:
        reasons.append(REASON_SOURCE_FRESHNESS_BLOCK)
        return
    if age_seconds > fresh:
        reasons.append(REASON_SOURCE_FRESHNESS_WATCH)


def _append_low_threshold_reason(
    reasons: list[str],
    *,
    metric: Decimal,
    watch: Decimal,
    block: Decimal,
    watch_code: str,
    block_code: str,
) -> None:
    if metric < block:
        reasons.append(block_code)
        return
    if metric < watch:
        reasons.append(watch_code)


def _append_high_threshold_reason(
    reasons: list[str],
    *,
    metric: Decimal,
    watch: Decimal,
    block: Decimal,
    watch_code: str,
    block_code: str,
) -> None:
    if metric > block:
        reasons.append(block_code)
        return
    if metric > watch:
        reasons.append(watch_code)


def _confidence_band_from_reasons(blocker_reasons: tuple[str, ...]) -> str:
    if any(reason in _BLOCK_REASONS for reason in blocker_reasons):
        return CONFIDENCE_LOW
    if blocker_reasons == (REASON_CLEAR,):
        return CONFIDENCE_HIGH
    return CONFIDENCE_MEDIUM


def _status_from_band(confidence_band: str) -> str:
    if confidence_band == CONFIDENCE_LOW:
        return STATUS_BLOCK
    if confidence_band == CONFIDENCE_MEDIUM:
        return STATUS_WATCH
    return STATUS_PASS


def _report_status(rows: tuple[StrategyMarketTeamRouterConfidenceRow, ...]) -> str:
    if not rows:
        return STATUS_BLOCK
    if any(row.confidence_band == CONFIDENCE_LOW for row in rows):
        return STATUS_BLOCK
    if any(row.confidence_band == CONFIDENCE_MEDIUM for row in rows):
        return STATUS_WATCH
    return STATUS_PASS


def _report_blocker_reasons(
    rows: tuple[StrategyMarketTeamRouterConfidenceRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return (REASON_NO_INPUTS,)
    found = {reason for row in rows for reason in row.blocker_reasons if reason != REASON_CLEAR}
    if not found:
        return (REASON_CLEAR,)
    return tuple(reason for reason in _REPORT_BLOCKER_REASON_PRIORITY if reason in found)


def _confidence_score(
    *,
    source_freshness_score: Decimal,
    calibration_readiness_score: Decimal,
    cost_gate_margin_score: Decimal,
    liquidity_score: Decimal,
    spread_score: Decimal,
    blocker_reasons: tuple[str, ...],
) -> Decimal:
    spread_quality_score = _clamp_ratio(_ONE - spread_score)
    base_score = _ratio(
        source_freshness_score
        + calibration_readiness_score
        + liquidity_score
        + spread_quality_score,
        _FOUR,
    )
    if blocker_reasons == (REASON_CLEAR,):
        return _clamp_ratio(base_score + cost_gate_margin_score * _CLEAR_COST_CONFIDENCE_WEIGHT)
    block_count = _reason_count(blocker_reasons, _BLOCK_REASONS)
    watch_count = _reason_count(blocker_reasons, _WATCH_REASONS)
    pressure = block_count * _BLOCK_REASON_PENALTY + watch_count * _WATCH_REASON_PENALTY
    return _clamp_ratio(base_score - pressure)


def _reason_count(reason_codes: tuple[str, ...], reason_set: frozenset[str]) -> Decimal:
    return _count_decimal(sum(1 for reason in reason_codes if reason in reason_set))


def _source_freshness_score(age_seconds: Decimal, stale_source_age_seconds: Decimal) -> Decimal:
    if stale_source_age_seconds == _ZERO:
        return _ONE if age_seconds == _ZERO else _ZERO
    if age_seconds >= stale_source_age_seconds:
        return _ZERO
    return _clamp_ratio(_ONE - _ratio(age_seconds, stale_source_age_seconds))


def _specialist_team_label(market_category: str, domain_label: str) -> str:
    for label in (market_category, market_category.split(".", 1)[0], domain_label, domain_label.split(".", 1)[0]):
        if label in _DOMAIN_TEAM_PREFIXES:
            return _DOMAIN_TEAM_PREFIXES[label]
    prefix = market_category.split(".", 1)[0].replace("-", "_")
    return f"team_{prefix}"


def _normalize_inputs(
    inputs: Iterable[StrategyMarketTeamRouterConfidenceInput],
) -> tuple[StrategyMarketTeamRouterConfidenceInput, ...]:
    if isinstance(inputs, (str, bytes)):
        raise ValueError("inputs must be an iterable")
    try:
        normalized = tuple(inputs)
    except TypeError as exc:
        raise ValueError("inputs must be an iterable") from exc
    routing_refs: list[str] = []
    for item in normalized:
        if type(item) is not StrategyMarketTeamRouterConfidenceInput:
            raise ValueError("inputs must contain StrategyMarketTeamRouterConfidenceInput")
        require_paper_only_flags("market team router confidence input", item)
        routing_refs.append(item.routing_ref)
    if len(set(routing_refs)) != len(routing_refs):
        raise ValueError("routing_ref values must be unique")
    return normalized


def _normalize_rows(rows: object) -> tuple[StrategyMarketTeamRouterConfidenceRow, ...]:
    if isinstance(rows, (str, bytes)):
        raise ValueError("rows must be an iterable")
    try:
        normalized = tuple(rows)
    except TypeError as exc:
        raise ValueError("rows must be an iterable") from exc
    for row in normalized:
        if type(row) is not StrategyMarketTeamRouterConfidenceRow:
            raise ValueError("rows must contain StrategyMarketTeamRouterConfidenceRow")
        require_paper_only_flags("market team router confidence row", row)
    if normalized != tuple(sorted(normalized, key=_row_sort_key)):
        raise ValueError("rows must be sorted deterministically")
    return normalized


def _row_sort_key(row: StrategyMarketTeamRouterConfidenceRow) -> tuple[int, str, str]:
    return (
        _BAND_SORT_WEIGHT[row.confidence_band],
        row.routing_ref,
        row.recommended_specialist_team,
    )


def _validate_row(row: StrategyMarketTeamRouterConfidenceRow) -> None:
    if row.fresh_source_age_seconds > row.stale_source_age_seconds:
        raise ValueError("stale_source_age_seconds must be at least fresh_source_age_seconds")
    expected_team = _specialist_team_label(row.market_category, row.domain_label)
    if row.recommended_specialist_team != expected_team:
        raise ValueError("recommended_specialist_team must match market category and domain")
    expected_freshness = _source_freshness_score(
        row.source_age_seconds,
        row.stale_source_age_seconds,
    )
    if row.source_freshness_score != expected_freshness:
        raise ValueError("source_freshness_score must match source age")
    expected_reasons = _row_blocker_reasons(
        StrategyMarketTeamRouterConfidenceInput(
            routing_ref=row.routing_ref,
            market_category=row.market_category,
            domain_label=row.domain_label,
            source_observed_at=row.source_observed_at,
            calibration_readiness_score=row.calibration_readiness_score,
            cost_gate_margin_score=row.cost_gate_margin_score,
            liquidity_score=row.liquidity_score,
            spread_score=row.spread_score,
        ),
        source_age_seconds=row.source_age_seconds,
        config=StrategyMarketTeamRouterConfidenceConfig(
            fresh_source_age_seconds=row.fresh_source_age_seconds,
            stale_source_age_seconds=row.stale_source_age_seconds,
            min_pass_calibration_readiness_score=row.min_pass_calibration_readiness_score,
            min_watch_calibration_readiness_score=row.min_watch_calibration_readiness_score,
            min_pass_cost_gate_margin_score=row.min_pass_cost_gate_margin_score,
            min_watch_cost_gate_margin_score=row.min_watch_cost_gate_margin_score,
            min_pass_liquidity_score=row.min_pass_liquidity_score,
            min_watch_liquidity_score=row.min_watch_liquidity_score,
            max_pass_spread_score=row.max_pass_spread_score,
            max_watch_spread_score=row.max_watch_spread_score,
        ),
    )
    if row.blocker_reasons != expected_reasons:
        raise ValueError("blocker_reasons must match row inputs")
    expected_band = _confidence_band_from_reasons(row.blocker_reasons)
    if row.confidence_band != expected_band:
        raise ValueError("confidence_band must match blocker_reasons")
    expected_score = _confidence_score(
        source_freshness_score=row.source_freshness_score,
        calibration_readiness_score=row.calibration_readiness_score,
        cost_gate_margin_score=row.cost_gate_margin_score,
        liquidity_score=row.liquidity_score,
        spread_score=row.spread_score,
        blocker_reasons=row.blocker_reasons,
    )
    if row.confidence_score != expected_score:
        raise ValueError("confidence_score must match inputs")


def _validate_report(report: StrategyMarketTeamRouterConfidenceReport) -> None:
    if report.input_count != _count_decimal(len(report.rows)):
        raise ValueError("input_count must match rows")
    if report.team_count != _count_decimal(len({row.recommended_specialist_team for row in report.rows})):
        raise ValueError("team_count must match rows")
    if report.high_confidence_count != _band_count(report.rows, CONFIDENCE_HIGH):
        raise ValueError("high_confidence_count must match rows")
    if report.medium_confidence_count != _band_count(report.rows, CONFIDENCE_MEDIUM):
        raise ValueError("medium_confidence_count must match rows")
    if report.low_confidence_count != _band_count(report.rows, CONFIDENCE_LOW):
        raise ValueError("low_confidence_count must match rows")
    if report.average_confidence_score != _average_confidence_score(report.rows):
        raise ValueError("average_confidence_score must match rows")
    if report.lowest_confidence_score != _min_decimal(row.confidence_score for row in report.rows):
        raise ValueError("lowest_confidence_score must match rows")
    if report.highest_source_age_seconds != _max_decimal(row.source_age_seconds for row in report.rows):
        raise ValueError("highest_source_age_seconds must match rows")
    if report.status != _report_status(report.rows):
        raise ValueError("status must match rows")
    if report.blocker_reasons != _report_blocker_reasons(report.rows):
        raise ValueError("blocker_reasons must match rows")


def _band_count(
    rows: tuple[StrategyMarketTeamRouterConfidenceRow, ...],
    confidence_band: str,
) -> Decimal:
    return _count_decimal(sum(1 for row in rows if row.confidence_band == confidence_band))


def _average_confidence_score(rows: tuple[StrategyMarketTeamRouterConfidenceRow, ...]) -> Decimal:
    if not rows:
        return _ZERO
    return _ratio(_sum_decimal(row.confidence_score for row in rows), _count_decimal(len(rows)))


def _sum_decimal(values: Iterable[Decimal]) -> Decimal:
    total = _ZERO
    for value in values:
        total += value
    return _quantize(total)


def _min_decimal(values: Iterable[Decimal]) -> Decimal:
    normalized = tuple(values)
    if not normalized:
        return _ZERO
    return min(normalized)


def _max_decimal(values: Iterable[Decimal]) -> Decimal:
    normalized = tuple(values)
    if not normalized:
        return _ZERO
    return max(normalized)


def _age_seconds(generated_at: datetime, observed_at: datetime) -> Decimal:
    elapsed = generated_at - observed_at
    age = Decimal(elapsed.days * 86400 + elapsed.seconds) + _ratio(
        Decimal(elapsed.microseconds),
        _MICROSECONDS_PER_SECOND,
    )
    if age < _ZERO:
        raise ValueError("source_observed_at must not be after generated_at")
    return _normalize_nonnegative_decimal("source_age_seconds", age)


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == _ZERO:
        raise ValueError("denominator must not be zero")
    with localcontext(_DECIMAL_CONTEXT):
        return _quantize(numerator / denominator)


def _clamp_ratio(value: Decimal) -> Decimal:
    quantized = _quantize(value)
    if quantized < _ZERO:
        return _ZERO
    if quantized > _ONE:
        return _ONE
    return quantized


def _quantize(value: Decimal) -> Decimal:
    with localcontext(_DECIMAL_CONTEXT):
        return value.quantize(_QUANTUM)


def _count_decimal(value: int) -> Decimal:
    if type(value) is not int:
        raise ValueError("count source must be an int")
    if value < 0:
        raise ValueError("count source must be nonnegative")
    return Decimal(value).quantize(_COUNT_QUANTUM)


def _normalize_count_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    if value < _ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    if value != value.to_integral_value():
        raise ValueError(f"{field_name} must be an integral Decimal")
    return value.quantize(_COUNT_QUANTUM)


def _normalize_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    if value < _ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    quantized = _quantize(value)
    if quantized != value:
        raise ValueError(f"{field_name} must use six decimal places or fewer")
    return quantized


def _normalize_unit_decimal(field_name: str, value: object) -> Decimal:
    quantized = _normalize_nonnegative_decimal(field_name, value)
    if quantized > _ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return quantized


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_exact_type(value: object, expected_type: type[object], label: str) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{label} must be exactly {expected_type.__name__}")


def _require_public_text(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")
    lowered = value.lower()
    if any(fragment in lowered for fragment in _UNSAFE_PUBLIC_FRAGMENTS):
        raise ValueError(f"{field_name} has unsafe public text")
    return value


def _require_confidence_band(field_name: str, value: object) -> str:
    if type(value) is not str or value not in STRATEGY_MARKET_TEAM_ROUTER_CONFIDENCE_BANDS:
        raise ValueError(
            f"{field_name} must be one of {STRATEGY_MARKET_TEAM_ROUTER_CONFIDENCE_BANDS}",
        )
    return value


def _require_status(field_name: str, value: object) -> str:
    if type(value) is not str or value not in _STATUSES:
        raise ValueError(f"{field_name} must be one of {_STATUSES}")
    return value


def _require_min_threshold_pair(
    pass_name: str,
    pass_value: Decimal,
    watch_name: str,
    watch_value: Decimal,
) -> None:
    if watch_value > pass_value:
        raise ValueError(f"{watch_name} must not exceed {pass_name}")


def _normalize_blocker_reasons(
    field_name: str,
    value: object,
    allowed: tuple[str, ...],
) -> tuple[str, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError(f"{field_name} must be an iterable")
    try:
        items = tuple(value)
    except TypeError as exc:
        raise ValueError(f"{field_name} must be an iterable") from exc
    if not items:
        raise ValueError(f"{field_name} must not be empty")
    for item in items:
        if type(item) is not str or item not in allowed:
            raise ValueError(f"{field_name} contains unsupported values")
    normalized = tuple(reason for reason in allowed if reason in items)
    if set(normalized) != set(items):
        raise ValueError(f"{field_name} contains unsupported values")
    return normalized


def _require_digest(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if len(value) != 64 or any(char not in "0123456789abcdef" for char in value):
        raise ValueError(f"{field_name} must be a sha-256 hex digest")
    return value


def _payload_value(value: object) -> Any:
    if is_dataclass(value) and not isinstance(value, type):
        return {key: _payload_value(item) for key, item in asdict(value).items()}
    if type(value) is Decimal:
        if not value.is_finite():
            raise ValueError("payload Decimal values must be finite")
        return format(value, "f")
    if type(value) is datetime:
        return _as_utc("payload datetime", value).isoformat()
    if value is None or type(value) in (str, bool):
        return value
    if type(value) is float or type(value) is int:
        raise ValueError("payload must not contain raw numeric values")
    if isinstance(value, tuple):
        return [_payload_value(item) for item in value]
    if isinstance(value, list):
        return [_payload_value(item) for item in value]
    if isinstance(value, dict):
        payload: dict[str, Any] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("payload object keys must be strings")
            payload[key] = _payload_value(item)
        return payload
    raise ValueError("payload value is not JSON serializable")


def _validate_payload_flags(payload: dict[str, Any], label: str) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if payload.get(field_name) is not True:
            raise ValueError(f"{field_name} must be True for {label}")


def _reject_unsafe_public_payload(payload: object) -> None:
    if isinstance(payload, dict):
        for key, item in payload.items():
            lowered_key = key.lower()
            if lowered_key in _UNSAFE_PUBLIC_KEYS:
                raise ValueError("unsafe public payload field")
            _reject_unsafe_public_payload(item)
        return
    if isinstance(payload, list):
        for item in payload:
            _reject_unsafe_public_payload(item)
        return
    if type(payload) is str:
        lowered = payload.lower()
        if any(fragment in lowered for fragment in _UNSAFE_PUBLIC_FRAGMENTS):
            raise ValueError("unsafe public payload value")


def _validate_payload_digest(payload: dict[str, Any]) -> None:
    digest = payload.get("derived_validation_digest")
    _require_digest("derived_validation_digest", digest)
    unsigned = dict(payload)
    unsigned.pop("derived_validation_digest", None)
    encoded = json.dumps(unsigned, sort_keys=True, separators=(",", ":"))
    expected = sha256(encoded.encode("utf-8")).hexdigest()
    if digest != expected:
        raise ValueError("derived_validation_digest must match report payload")


def _derived_validation_digest(report: StrategyMarketTeamRouterConfidenceReport) -> str:
    payload = _payload_value(report)
    if type(payload) is not dict:
        raise ValueError("report payload must be a dict")
    payload.pop("derived_validation_digest", None)
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return sha256(encoded.encode("utf-8")).hexdigest()
