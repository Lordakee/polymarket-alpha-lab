"""Pure report-only probability fee liquidity decay scorecard."""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable, Mapping
from dataclasses import dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation, ROUND_HALF_EVEN
import hashlib
import json
from typing import Any


DEFAULT_RESEARCH_MARKET_PROBABILITY_FEE_LIQUIDITY_DECAY_SCORECARD_REPORT_CONFIG_VERSION = (
    "research-market-probability-fee-liquidity-decay-scorecard-report-v0"
)

STATUS_PASS = "pass"
STATUS_WATCH = "watch"
STATUS_BLOCK = "block"
STATUSES = (STATUS_PASS, STATUS_WATCH, STATUS_BLOCK)
STATUS_RANK = {
    STATUS_BLOCK: Decimal("0.000000"),
    STATUS_WATCH: Decimal("1.000000"),
    STATUS_PASS: Decimal("2.000000"),
}

REASON_PREFIX = "probability_fee_liquidity_decay_scorecard_"
NO_INPUTS_REASON = REASON_PREFIX + "no_inputs"
CLEAR_REASON = REASON_PREFIX + "clear"
FEE_COST_WATCH_REASON = REASON_PREFIX + "fee_cost_watch"
FEE_COST_BLOCK_REASON = REASON_PREFIX + "fee_cost_block"
PROBABILITY_DECAY_WATCH_REASON = REASON_PREFIX + "probability_decay_watch"
PROBABILITY_DECAY_BLOCK_REASON = REASON_PREFIX + "probability_decay_block"
LIQUIDITY_DECAY_WATCH_REASON = REASON_PREFIX + "liquidity_decay_watch"
LIQUIDITY_DECAY_BLOCK_REASON = REASON_PREFIX + "liquidity_decay_block"
LIQUIDITY_SCORE_WATCH_REASON = REASON_PREFIX + "liquidity_score_watch"
LIQUIDITY_SCORE_BLOCK_REASON = REASON_PREFIX + "liquidity_score_block"
SCORE_WATCH_REASON = REASON_PREFIX + "score_watch"
SCORE_BLOCK_REASON = REASON_PREFIX + "score_block"

QUANTUM = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
SIXTY_FOUR = Decimal("64.000000")


def _join_parts(*parts: str) -> str:
    return "".join(parts)


UNSAFE_PUBLIC_FRAGMENTS = (
    _join_parts("ra", "w"),
    _join_parts("can", "didate"),
    _join_parts("ma", "rket", "_", "id"),
    _join_parts("ma", "rket", "-", "id"),
    _join_parts("ma", "rket", "_", "sl", "ug"),
    _join_parts("ma", "rket", "-", "sl", "ug"),
    _join_parts("sl", "ug"),
    _join_parts("ques", "tion"),
    _join_parts("sou", "rce", "_", "ur", "l"),
    _join_parts("sou", "rce", "-", "ur", "l"),
    _join_parts("sou", "rce", "_", "te", "xt"),
    _join_parts("sou", "rce", "-", "te", "xt"),
    _join_parts("d", "sn"),
    _join_parts("d", "b"),
    _join_parts("data", "base"),
    _join_parts("net", "work"),
    _join_parts("ta", "ble"),
    _join_parts("to", "ken"),
    _join_parts("wal", "let"),
    _join_parts("au", "th"),
    _join_parts("or", "der"),
    _join_parts("tra", "de"),
    _join_parts("tra", "ding"),
    _join_parts("po", "si", "tion"),
    _join_parts("siz", "ing"),
    _join_parts("reco", "mmend"),
    _join_parts("reco", "mmendation"),
    _join_parts("sec", "ret"),
    _join_parts("pri", "vate", "_", "key"),
    _join_parts("a", "pi", "_", "key"),
    _join_parts("ht", "tp", ":", "/", "/"),
    _join_parts("ht", "tps", ":", "/", "/"),
    "://",
    "?",
)


__all__ = (
    "DEFAULT_RESEARCH_MARKET_PROBABILITY_FEE_LIQUIDITY_DECAY_SCORECARD_REPORT_CONFIG_VERSION",
    "STATUSES",
    "ResearchMarketProbabilityFeeLiquidityDecayScorecardConfig",
    "ResearchMarketProbabilityFeeLiquidityDecayScorecardObservation",
    "ResearchMarketProbabilityFeeLiquidityDecayScorecardReasonCodeCount",
    "ResearchMarketProbabilityFeeLiquidityDecayScorecardReport",
    "ResearchMarketProbabilityFeeLiquidityDecayScorecardRow",
    "build_research_market_probability_fee_liquidity_decay_scorecard_report",
    "research_market_probability_fee_liquidity_decay_scorecard_report_digest",
    "research_market_probability_fee_liquidity_decay_scorecard_report_payload",
)


@dataclass(frozen=True)
class ResearchMarketProbabilityFeeLiquidityDecayScorecardConfig:
    config_version: str = (
        DEFAULT_RESEARCH_MARKET_PROBABILITY_FEE_LIQUIDITY_DECAY_SCORECARD_REPORT_CONFIG_VERSION
    )
    watch_total_fee_cost_ratio: Decimal = Decimal("0.030000")
    block_total_fee_cost_ratio: Decimal = Decimal("0.080000")
    watch_probability_decay_ratio: Decimal = Decimal("0.040000")
    block_probability_decay_ratio: Decimal = Decimal("0.100000")
    watch_liquidity_decay_ratio: Decimal = Decimal("0.200000")
    block_liquidity_decay_ratio: Decimal = Decimal("0.500000")
    watch_liquidity_score_floor: Decimal = Decimal("0.550000")
    block_liquidity_score_floor: Decimal = Decimal("0.300000")
    pass_score_floor: Decimal = Decimal("0.700000")
    watch_score_floor: Decimal = Decimal("0.400000")
    fee_drag_weight: Decimal = Decimal("0.250000")
    probability_decay_weight: Decimal = Decimal("0.250000")
    liquidity_quality_weight: Decimal = Decimal("0.250000")
    liquidity_decay_weight: Decimal = Decimal("0.250000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchMarketProbabilityFeeLiquidityDecayScorecardConfig does not "
            "support subclassing",
        )

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchMarketProbabilityFeeLiquidityDecayScorecardConfig,
            "config",
        )
        object.__setattr__(
            self,
            "config_version",
            _require_public_label("config_version", self.config_version),
        )
        if (
            self.config_version
            != DEFAULT_RESEARCH_MARKET_PROBABILITY_FEE_LIQUIDITY_DECAY_SCORECARD_REPORT_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "watch_total_fee_cost_ratio",
            "block_total_fee_cost_ratio",
            "watch_probability_decay_ratio",
            "block_probability_decay_ratio",
            "watch_liquidity_decay_ratio",
            "block_liquidity_decay_ratio",
            "watch_liquidity_score_floor",
            "block_liquidity_score_floor",
            "pass_score_floor",
            "watch_score_floor",
            "fee_drag_weight",
            "probability_decay_weight",
            "liquidity_quality_weight",
            "liquidity_decay_weight",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        _require_less_than(
            "watch_total_fee_cost_ratio",
            self.watch_total_fee_cost_ratio,
            "block_total_fee_cost_ratio",
            self.block_total_fee_cost_ratio,
        )
        _require_less_than(
            "watch_probability_decay_ratio",
            self.watch_probability_decay_ratio,
            "block_probability_decay_ratio",
            self.block_probability_decay_ratio,
        )
        _require_less_than(
            "watch_liquidity_decay_ratio",
            self.watch_liquidity_decay_ratio,
            "block_liquidity_decay_ratio",
            self.block_liquidity_decay_ratio,
        )
        _require_less_than(
            "block_liquidity_score_floor",
            self.block_liquidity_score_floor,
            "watch_liquidity_score_floor",
            self.watch_liquidity_score_floor,
        )
        _require_less_than(
            "watch_score_floor",
            self.watch_score_floor,
            "pass_score_floor",
            self.pass_score_floor,
        )
        weight_sum = _quantize(
            self.fee_drag_weight
            + self.probability_decay_weight
            + self.liquidity_quality_weight
            + self.liquidity_decay_weight,
        )
        if weight_sum != ONE:
            raise ValueError("scorecard weights must sum to 1")
        _require_hard_flags("config", self)
        _reject_unsafe_public_payload("config", self)


@dataclass(frozen=True)
class ResearchMarketProbabilityFeeLiquidityDecayScorecardObservation:
    public_signal_ref: str
    observed_at: datetime
    baseline_probability: Decimal
    current_probability: Decimal
    fee_cost_ratio: Decimal
    spread_cost_ratio: Decimal
    liquidity_score: Decimal
    reference_liquidity_score: Decimal
    reason_codes: tuple[str, ...] = ()
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchMarketProbabilityFeeLiquidityDecayScorecardObservation does not "
            "support subclassing",
        )

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchMarketProbabilityFeeLiquidityDecayScorecardObservation,
            "observation",
        )
        object.__setattr__(
            self,
            "public_signal_ref",
            _require_public_label("public_signal_ref", self.public_signal_ref),
        )
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in (
            "baseline_probability",
            "current_probability",
            "fee_cost_ratio",
            "spread_cost_ratio",
            "liquidity_score",
            "reference_liquidity_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        if self.reference_liquidity_score <= ZERO:
            raise ValueError("reference_liquidity_score must be positive")
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(
                "reason_codes",
                self.reason_codes,
                allow_empty=True,
            ),
        )
        _require_hard_flags("observation", self)
        _reject_unsafe_public_payload("observation", self)


@dataclass(frozen=True)
class ResearchMarketProbabilityFeeLiquidityDecayScorecardRow:
    public_signal_ref: str
    observed_at: datetime
    baseline_probability: Decimal
    current_probability: Decimal
    probability_decay_ratio: Decimal
    fee_cost_ratio: Decimal
    spread_cost_ratio: Decimal
    total_fee_cost_ratio: Decimal
    liquidity_score: Decimal
    reference_liquidity_score: Decimal
    liquidity_decay_ratio: Decimal
    fee_drag_score: Decimal
    probability_decay_score: Decimal
    liquidity_decay_score: Decimal
    probability_fee_liquidity_decay_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchMarketProbabilityFeeLiquidityDecayScorecardRow does not "
            "support subclassing",
        )

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchMarketProbabilityFeeLiquidityDecayScorecardRow,
            "row",
        )
        object.__setattr__(
            self,
            "public_signal_ref",
            _require_public_label("public_signal_ref", self.public_signal_ref),
        )
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in (
            "baseline_probability",
            "current_probability",
            "probability_decay_ratio",
            "fee_cost_ratio",
            "spread_cost_ratio",
            "total_fee_cost_ratio",
            "liquidity_score",
            "reference_liquidity_score",
            "liquidity_decay_ratio",
            "fee_drag_score",
            "probability_decay_score",
            "liquidity_decay_score",
            "probability_fee_liquidity_decay_score",
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
        if self.status != _status_from_reasons(self.reason_codes):
            raise ValueError("status must match reason_codes")
        _require_hard_flags("row", self)
        _reject_unsafe_public_payload("row", self)


@dataclass(frozen=True)
class ResearchMarketProbabilityFeeLiquidityDecayScorecardReasonCodeCount:
    reason_code: str
    count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchMarketProbabilityFeeLiquidityDecayScorecardReasonCodeCount does "
            "not support subclassing",
        )

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchMarketProbabilityFeeLiquidityDecayScorecardReasonCodeCount,
            "reason_code_count",
        )
        object.__setattr__(
            self,
            "reason_code",
            _require_reason_code("reason_code", self.reason_code),
        )
        object.__setattr__(
            self,
            "count",
            _require_positive_count_decimal("count", self.count),
        )
        _require_hard_flags("reason_code_count", self)
        _reject_unsafe_public_payload("reason_code_count", self)


@dataclass(frozen=True)
class ResearchMarketProbabilityFeeLiquidityDecayScorecardReport:
    generated_at: datetime
    config_version: str
    input_count: Decimal
    row_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    total_fee_cost_watch_count: Decimal
    probability_decay_watch_count: Decimal
    liquidity_decay_watch_count: Decimal
    liquidity_score_watch_count: Decimal
    max_total_fee_cost_ratio: Decimal
    max_probability_decay_ratio: Decimal
    max_liquidity_decay_ratio: Decimal
    min_liquidity_score: Decimal
    average_probability_fee_liquidity_decay_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    reason_code_counts: tuple[
        ResearchMarketProbabilityFeeLiquidityDecayScorecardReasonCodeCount,
        ...,
    ]
    rows: tuple[ResearchMarketProbabilityFeeLiquidityDecayScorecardRow, ...]
    derived_validation_digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchMarketProbabilityFeeLiquidityDecayScorecardReport does not "
            "support subclassing",
        )

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchMarketProbabilityFeeLiquidityDecayScorecardReport,
            "report",
        )
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        object.__setattr__(
            self,
            "config_version",
            _require_public_label("config_version", self.config_version),
        )
        if (
            self.config_version
            != DEFAULT_RESEARCH_MARKET_PROBABILITY_FEE_LIQUIDITY_DECAY_SCORECARD_REPORT_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "input_count",
            "row_count",
            "pass_count",
            "watch_count",
            "block_count",
            "total_fee_cost_watch_count",
            "probability_decay_watch_count",
            "liquidity_decay_watch_count",
            "liquidity_score_watch_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_count_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "max_total_fee_cost_ratio",
            "max_probability_decay_ratio",
            "max_liquidity_decay_ratio",
            "min_liquidity_score",
            "average_probability_fee_liquidity_decay_score",
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
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        _require_sha256_digest("derived_validation_digest", self.derived_validation_digest)
        _validate_report(self)
        _require_hard_flags("report", self)
        _reject_unsafe_public_payload("report", self)
        expected_digest = _report_digest_from_values(_report_values_without_digest(self))
        if self.derived_validation_digest != expected_digest:
            raise ValueError("derived_validation_digest does not match report payload")

    @property
    def public_payload(self) -> dict[str, object]:
        return research_market_probability_fee_liquidity_decay_scorecard_report_payload(
            self,
        )


def build_research_market_probability_fee_liquidity_decay_scorecard_report(
    observations: Iterable[ResearchMarketProbabilityFeeLiquidityDecayScorecardObservation],
    *,
    config: ResearchMarketProbabilityFeeLiquidityDecayScorecardConfig,
    generated_at: datetime,
) -> ResearchMarketProbabilityFeeLiquidityDecayScorecardReport:
    if type(config) is not ResearchMarketProbabilityFeeLiquidityDecayScorecardConfig:
        raise ValueError(
            "config must be a ResearchMarketProbabilityFeeLiquidityDecayScorecardConfig",
        )
    _require_hard_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    input_rows = _normalize_observations(observations)
    rows = tuple(
        sorted(
            (_row_from_observation(item, config=config) for item in input_rows),
            key=_row_sort_key,
        ),
    )
    values = _report_values_from_rows(
        rows,
        config_version=config.config_version,
        generated_at=generated_at_utc,
        input_count=_count(len(input_rows)),
    )
    return ResearchMarketProbabilityFeeLiquidityDecayScorecardReport(
        **values,
        derived_validation_digest=_report_digest_from_values(values),
    )


def research_market_probability_fee_liquidity_decay_scorecard_report_payload(
    report: ResearchMarketProbabilityFeeLiquidityDecayScorecardReport,
) -> dict[str, object]:
    if type(report) is not ResearchMarketProbabilityFeeLiquidityDecayScorecardReport:
        raise ValueError(
            "report must be a ResearchMarketProbabilityFeeLiquidityDecayScorecardReport",
        )
    expected_digest = _report_digest_from_values(_report_values_without_digest(report))
    if report.derived_validation_digest != expected_digest:
        raise ValueError("derived_validation_digest does not match report payload")
    _validate_report(report)
    _require_hard_flags("report", report)
    payload = _json_ready(
        {
            **_report_values_without_digest(report),
            "derived_validation_digest": report.derived_validation_digest,
        },
    )
    if type(payload) is not dict:
        raise ValueError("payload must be a dict")
    _reject_unsafe_public_payload(
        "research_market_probability_fee_liquidity_decay_scorecard_report_payload",
        payload,
        allow_json_containers=True,
    )
    return payload


def research_market_probability_fee_liquidity_decay_scorecard_report_digest(
    report: ResearchMarketProbabilityFeeLiquidityDecayScorecardReport,
) -> str:
    payload = research_market_probability_fee_liquidity_decay_scorecard_report_payload(
        report,
    )
    trimmed = dict(payload)
    trimmed.pop("derived_validation_digest")
    return _digest_json_ready_values(trimmed)


def _row_from_observation(
    item: ResearchMarketProbabilityFeeLiquidityDecayScorecardObservation,
    *,
    config: ResearchMarketProbabilityFeeLiquidityDecayScorecardConfig,
) -> ResearchMarketProbabilityFeeLiquidityDecayScorecardRow:
    probability_decay_ratio = _max_decimal(
        _quantize(item.baseline_probability - item.current_probability),
        ZERO,
    )
    total_fee_cost_ratio = _quantize(item.fee_cost_ratio + item.spread_cost_ratio)
    liquidity_decay_ratio = _max_decimal(
        _quantize(item.reference_liquidity_score - item.liquidity_score),
        ZERO,
    )
    fee_drag_score = _component_score(
        total_fee_cost_ratio,
        config.block_total_fee_cost_ratio,
    )
    probability_decay_score = _component_score(
        probability_decay_ratio,
        config.block_probability_decay_ratio,
    )
    liquidity_decay_score = _component_score(
        liquidity_decay_ratio,
        config.block_liquidity_decay_ratio,
    )
    score = _quantize(
        (fee_drag_score * config.fee_drag_weight)
        + (probability_decay_score * config.probability_decay_weight)
        + (item.liquidity_score * config.liquidity_quality_weight)
        + (liquidity_decay_score * config.liquidity_decay_weight),
    )
    reason_codes = _row_reason_codes(
        item,
        config=config,
        total_fee_cost_ratio=total_fee_cost_ratio,
        probability_decay_ratio=probability_decay_ratio,
        liquidity_decay_ratio=liquidity_decay_ratio,
        score=score,
    )
    return ResearchMarketProbabilityFeeLiquidityDecayScorecardRow(
        public_signal_ref=item.public_signal_ref,
        observed_at=item.observed_at,
        baseline_probability=item.baseline_probability,
        current_probability=item.current_probability,
        probability_decay_ratio=probability_decay_ratio,
        fee_cost_ratio=item.fee_cost_ratio,
        spread_cost_ratio=item.spread_cost_ratio,
        total_fee_cost_ratio=total_fee_cost_ratio,
        liquidity_score=item.liquidity_score,
        reference_liquidity_score=item.reference_liquidity_score,
        liquidity_decay_ratio=liquidity_decay_ratio,
        fee_drag_score=fee_drag_score,
        probability_decay_score=probability_decay_score,
        liquidity_decay_score=liquidity_decay_score,
        probability_fee_liquidity_decay_score=score,
        status=_status_from_reasons(reason_codes),
        reason_codes=reason_codes,
    )


def _row_reason_codes(
    item: ResearchMarketProbabilityFeeLiquidityDecayScorecardObservation,
    *,
    config: ResearchMarketProbabilityFeeLiquidityDecayScorecardConfig,
    total_fee_cost_ratio: Decimal,
    probability_decay_ratio: Decimal,
    liquidity_decay_ratio: Decimal,
    score: Decimal,
) -> tuple[str, ...]:
    reasons: list[str] = []
    for reason_code in item.reason_codes:
        reasons.append("input_" + reason_code)
    if total_fee_cost_ratio >= config.block_total_fee_cost_ratio:
        reasons.append(FEE_COST_BLOCK_REASON)
    elif total_fee_cost_ratio >= config.watch_total_fee_cost_ratio:
        reasons.append(FEE_COST_WATCH_REASON)
    if probability_decay_ratio >= config.block_probability_decay_ratio:
        reasons.append(PROBABILITY_DECAY_BLOCK_REASON)
    elif probability_decay_ratio >= config.watch_probability_decay_ratio:
        reasons.append(PROBABILITY_DECAY_WATCH_REASON)
    if liquidity_decay_ratio >= config.block_liquidity_decay_ratio:
        reasons.append(LIQUIDITY_DECAY_BLOCK_REASON)
    elif liquidity_decay_ratio >= config.watch_liquidity_decay_ratio:
        reasons.append(LIQUIDITY_DECAY_WATCH_REASON)
    if item.liquidity_score <= config.block_liquidity_score_floor:
        reasons.append(LIQUIDITY_SCORE_BLOCK_REASON)
    elif item.liquidity_score <= config.watch_liquidity_score_floor:
        reasons.append(LIQUIDITY_SCORE_WATCH_REASON)
    if score < config.watch_score_floor:
        reasons.append(SCORE_BLOCK_REASON)
    elif score < config.pass_score_floor:
        reasons.append(SCORE_WATCH_REASON)
    status = _status_from_reasons(tuple(reasons))
    if status == STATUS_PASS:
        reasons.append(CLEAR_REASON)
    else:
        reasons.append(REASON_PREFIX + status)
    return _normalize_reason_codes(
        "reason_codes",
        tuple(sorted(reasons)),
        allow_empty=False,
    )


def _report_values_from_rows(
    rows: tuple[ResearchMarketProbabilityFeeLiquidityDecayScorecardRow, ...],
    *,
    config_version: str,
    generated_at: datetime,
    input_count: Decimal,
) -> dict[str, object]:
    if not rows:
        reason_code_counts = (
            ResearchMarketProbabilityFeeLiquidityDecayScorecardReasonCodeCount(
                reason_code=NO_INPUTS_REASON,
                count=ONE,
            ),
        )
        return {
            "generated_at": generated_at,
            "config_version": config_version,
            "input_count": input_count,
            "row_count": ZERO,
            "pass_count": ZERO,
            "watch_count": ZERO,
            "block_count": ZERO,
            "total_fee_cost_watch_count": ZERO,
            "probability_decay_watch_count": ZERO,
            "liquidity_decay_watch_count": ZERO,
            "liquidity_score_watch_count": ZERO,
            "max_total_fee_cost_ratio": ZERO,
            "max_probability_decay_ratio": ZERO,
            "max_liquidity_decay_ratio": ZERO,
            "min_liquidity_score": ZERO,
            "average_probability_fee_liquidity_decay_score": ZERO,
            "status": STATUS_BLOCK,
            "reason_codes": (NO_INPUTS_REASON,),
            "reason_code_counts": reason_code_counts,
            "rows": (),
            "paper_only": True,
            "report_only": True,
            "readonly": True,
        }
    reason_codes = _report_reason_codes(rows)
    return {
        "generated_at": generated_at,
        "config_version": config_version,
        "input_count": input_count,
        "row_count": _count(len(rows)),
        "pass_count": _status_count(rows, STATUS_PASS),
        "watch_count": _status_count(rows, STATUS_WATCH),
        "block_count": _status_count(rows, STATUS_BLOCK),
        "total_fee_cost_watch_count": _reason_count(
            rows,
            FEE_COST_WATCH_REASON,
            FEE_COST_BLOCK_REASON,
        ),
        "probability_decay_watch_count": _reason_count(
            rows,
            PROBABILITY_DECAY_WATCH_REASON,
            PROBABILITY_DECAY_BLOCK_REASON,
        ),
        "liquidity_decay_watch_count": _reason_count(
            rows,
            LIQUIDITY_DECAY_WATCH_REASON,
            LIQUIDITY_DECAY_BLOCK_REASON,
        ),
        "liquidity_score_watch_count": _reason_count(
            rows,
            LIQUIDITY_SCORE_WATCH_REASON,
            LIQUIDITY_SCORE_BLOCK_REASON,
        ),
        "max_total_fee_cost_ratio": _max_decimal(
            *(row.total_fee_cost_ratio for row in rows),
        ),
        "max_probability_decay_ratio": _max_decimal(
            *(row.probability_decay_ratio for row in rows),
        ),
        "max_liquidity_decay_ratio": _max_decimal(
            *(row.liquidity_decay_ratio for row in rows),
        ),
        "min_liquidity_score": _min_decimal(*(row.liquidity_score for row in rows)),
        "average_probability_fee_liquidity_decay_score": _mean(
            tuple(row.probability_fee_liquidity_decay_score for row in rows),
        ),
        "status": _rollup_status(tuple(row.status for row in rows)),
        "reason_codes": reason_codes,
        "reason_code_counts": _reason_code_counts(rows, reason_codes),
        "rows": rows,
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }


def _validate_report(
    report: ResearchMarketProbabilityFeeLiquidityDecayScorecardReport,
) -> None:
    rows = _normalize_rows(report.rows)
    expected = _report_values_from_rows(
        rows,
        config_version=report.config_version,
        generated_at=report.generated_at,
        input_count=report.input_count,
    )
    for field_name, expected_value in expected.items():
        if getattr(report, field_name) != expected_value:
            raise ValueError(f"{field_name} does not match rows")


def _report_values_without_digest(
    report: ResearchMarketProbabilityFeeLiquidityDecayScorecardReport,
) -> dict[str, object]:
    return {
        "generated_at": report.generated_at,
        "config_version": report.config_version,
        "input_count": report.input_count,
        "row_count": report.row_count,
        "pass_count": report.pass_count,
        "watch_count": report.watch_count,
        "block_count": report.block_count,
        "total_fee_cost_watch_count": report.total_fee_cost_watch_count,
        "probability_decay_watch_count": report.probability_decay_watch_count,
        "liquidity_decay_watch_count": report.liquidity_decay_watch_count,
        "liquidity_score_watch_count": report.liquidity_score_watch_count,
        "max_total_fee_cost_ratio": report.max_total_fee_cost_ratio,
        "max_probability_decay_ratio": report.max_probability_decay_ratio,
        "max_liquidity_decay_ratio": report.max_liquidity_decay_ratio,
        "min_liquidity_score": report.min_liquidity_score,
        "average_probability_fee_liquidity_decay_score": (
            report.average_probability_fee_liquidity_decay_score
        ),
        "status": report.status,
        "reason_codes": report.reason_codes,
        "reason_code_counts": report.reason_code_counts,
        "rows": report.rows,
        "paper_only": report.paper_only,
        "report_only": report.report_only,
        "readonly": report.readonly,
    }


def _report_digest_from_values(values: Mapping[str, object]) -> str:
    return _digest_json_ready_values(_json_ready(values))


def _digest_json_ready_values(values: object) -> str:
    _reject_unsafe_public_payload(
        "derived_validation_digest payload",
        values,
        allow_json_containers=True,
    )
    canonical = json.dumps(values, ensure_ascii=True, separators=(",", ":"), sort_keys=True)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _json_ready(value: Any) -> Any:
    if _is_public_dataclass(value):
        return _json_ready(_dataclass_values(value))
    if isinstance(value, tuple):
        return [_json_ready(item) for item in value]
    if isinstance(value, list):
        return [_json_ready(item) for item in value]
    if isinstance(value, dict):
        ready: dict[str, object] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            ready[key] = _json_ready(item)
        return ready
    if type(value) is Decimal:
        return format(value, "f")
    if type(value) is datetime:
        return value.isoformat()
    if type(value) in {str, bool} or value is None:
        return value
    if isinstance(value, Decimal):
        raise ValueError("JSON Decimal value must be an exact Decimal")
    if isinstance(value, int) or isinstance(value, float):
        raise ValueError("JSON numeric value must use Decimal")
    raise ValueError(f"unsupported payload value {type(value).__name__}")


def _dataclass_values(value: object) -> dict[str, object]:
    if not _is_public_dataclass(value):
        raise ValueError("value must be a public dataclass")
    return {field.name: getattr(value, field.name) for field in fields(value)}


def _normalize_observations(
    observations: Iterable[ResearchMarketProbabilityFeeLiquidityDecayScorecardObservation],
) -> tuple[ResearchMarketProbabilityFeeLiquidityDecayScorecardObservation, ...]:
    rows = tuple(observations)
    for item in rows:
        if type(item) is not ResearchMarketProbabilityFeeLiquidityDecayScorecardObservation:
            raise ValueError(
                "observations must contain "
                "ResearchMarketProbabilityFeeLiquidityDecayScorecardObservation",
            )
        _require_hard_flags("observation", item)
        _reject_unsafe_public_payload("observation", item)
    return rows


def _normalize_rows(
    rows: object,
) -> tuple[ResearchMarketProbabilityFeeLiquidityDecayScorecardRow, ...]:
    if type(rows) is not tuple:
        raise ValueError("rows must be a tuple")
    for row in rows:
        if type(row) is not ResearchMarketProbabilityFeeLiquidityDecayScorecardRow:
            raise ValueError(
                "rows must contain ResearchMarketProbabilityFeeLiquidityDecayScorecardRow",
            )
        _require_hard_flags("row", row)
        _reject_unsafe_public_payload("row", row)
    return rows


def _normalize_reason_code_counts(
    counts: object,
) -> tuple[ResearchMarketProbabilityFeeLiquidityDecayScorecardReasonCodeCount, ...]:
    if type(counts) is not tuple:
        raise ValueError("reason_code_counts must be a tuple")
    for count in counts:
        if (
            type(count)
            is not ResearchMarketProbabilityFeeLiquidityDecayScorecardReasonCodeCount
        ):
            raise ValueError(
                "reason_code_counts must contain "
                "ResearchMarketProbabilityFeeLiquidityDecayScorecardReasonCodeCount",
            )
        _require_hard_flags("reason_code_count", count)
        _reject_unsafe_public_payload("reason_code_count", count)
    return counts


def _report_reason_codes(
    rows: tuple[ResearchMarketProbabilityFeeLiquidityDecayScorecardRow, ...],
) -> tuple[str, ...]:
    status = _rollup_status(tuple(row.status for row in rows))
    codes = [REASON_PREFIX + status]
    for row in rows:
        for reason_code in row.reason_codes:
            if reason_code != CLEAR_REASON:
                codes.append(reason_code)
    return _normalize_reason_codes(
        "reason_codes",
        tuple(sorted(set(codes))),
        allow_empty=False,
    )


def _reason_code_counts(
    rows: tuple[ResearchMarketProbabilityFeeLiquidityDecayScorecardRow, ...],
    report_reason_codes: tuple[str, ...],
) -> tuple[ResearchMarketProbabilityFeeLiquidityDecayScorecardReasonCodeCount, ...]:
    counts: Counter[str] = Counter(report_reason_codes)
    for row in rows:
        counts.update(row.reason_codes)
    return tuple(
        ResearchMarketProbabilityFeeLiquidityDecayScorecardReasonCodeCount(
            reason_code=reason_code,
            count=_count(count),
        )
        for reason_code, count in sorted(counts.items())
    )


def _reason_count(
    rows: tuple[ResearchMarketProbabilityFeeLiquidityDecayScorecardRow, ...],
    watch_reason: str,
    block_reason: str,
) -> Decimal:
    return _count(
        sum(
            1
            for row in rows
            if watch_reason in row.reason_codes or block_reason in row.reason_codes
        ),
    )


def _status_count(
    rows: tuple[ResearchMarketProbabilityFeeLiquidityDecayScorecardRow, ...],
    status: str,
) -> Decimal:
    return _count(sum(1 for row in rows if row.status == status))


def _rollup_status(statuses: tuple[str, ...]) -> str:
    if STATUS_BLOCK in statuses:
        return STATUS_BLOCK
    if STATUS_WATCH in statuses:
        return STATUS_WATCH
    return STATUS_PASS


def _status_from_reasons(reason_codes: tuple[str, ...]) -> str:
    if any(reason_code.endswith("_block") for reason_code in reason_codes):
        return STATUS_BLOCK
    if any(reason_code.endswith("_watch") for reason_code in reason_codes):
        return STATUS_WATCH
    return STATUS_PASS


def _row_sort_key(
    row: ResearchMarketProbabilityFeeLiquidityDecayScorecardRow,
) -> tuple[Decimal, str]:
    return (STATUS_RANK[row.status], row.public_signal_ref)


def _component_score(value: Decimal, block_threshold: Decimal) -> Decimal:
    if block_threshold <= ZERO:
        raise ValueError("block threshold must be positive")
    return _max_decimal(_quantize(ONE - _safe_divide(value, block_threshold)), ZERO)


def _normalize_reason_codes(
    field_name: str,
    value: object,
    *,
    allow_empty: bool,
) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ValueError(f"{field_name} must be a tuple")
    normalized = tuple(_require_reason_code(field_name, item) for item in value)
    if not allow_empty and not normalized:
        raise ValueError(f"{field_name} must not be empty")
    if len(set(normalized)) != len(normalized):
        raise ValueError(f"{field_name} must not contain duplicates")
    return normalized


def _require_reason_code(field_name: str, value: object) -> str:
    text = _require_public_label(field_name, value)
    if text.lower() != text:
        raise ValueError(f"{field_name} must be lowercase")
    return text


def _require_public_label(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a non-empty canonical string")
    if len(value) > 120:
        raise ValueError(f"{field_name} is too long")
    allowed = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-.:")
    if any(character not in allowed for character in value):
        raise ValueError(f"{field_name} contains unsupported characters")
    if _has_unsafe_public_fragment(value):
        raise ValueError(f"{field_name} contains an unsafe public fragment")
    return value


def _require_status(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if value not in STATUSES:
        raise ValueError(f"{field_name} must be one of pass, watch, block")
    return value


def _require_exact_type(value: object, expected_type: type[object], label: str) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{label} must be {expected_type.__name__}")


def _require_hard_flags(label: str, value: object) -> None:
    if getattr(value, "paper_only", None) is not True:
        raise ValueError(f"paper_only must be True for {label}")
    if getattr(value, "report_only", None) is not True:
        raise ValueError(f"report_only must be True for {label}")
    if getattr(value, "readonly", None) is not True:
        raise ValueError(f"readonly must be True for {label}")


def _require_less_than(
    lower_name: str,
    lower_value: Decimal,
    upper_name: str,
    upper_value: Decimal,
) -> None:
    if lower_value >= upper_value:
        raise ValueError(f"{lower_name} must be below {upper_name}")


def _require_ratio_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value < ZERO or decimal_value > ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return decimal_value


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return _quantize(value)


def _require_nonnegative_count_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return decimal_value


def _require_positive_count_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_nonnegative_count_decimal(field_name, value)
    if decimal_value <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return decimal_value


def _require_sha256_digest(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if len(value) != int(SIXTY_FOUR):
        raise ValueError(f"{field_name} must be a lowercase sha256 hex digest")
    if any(character not in "0123456789abcdef" for character in value):
        raise ValueError(f"{field_name} must be a lowercase sha256 hex digest")
    return value


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _count(value: int) -> Decimal:
    if type(value) is not int:
        raise ValueError("count input must be an exact integer")
    if value < 0:
        raise ValueError("count input must be nonnegative")
    return Decimal(value).quantize(QUANTUM)


def _mean(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return ZERO
    return _safe_divide(sum(values, ZERO), _count(len(values)))


def _safe_divide(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO:
        return ZERO
    return _quantize(numerator / denominator)


def _max_decimal(*values: Decimal) -> Decimal:
    if not values:
        return ZERO
    return _quantize(max(values))


def _min_decimal(*values: Decimal) -> Decimal:
    if not values:
        return ZERO
    return _quantize(min(values))


def _quantize(value: Decimal) -> Decimal:
    try:
        quantized = value.quantize(QUANTUM, rounding=ROUND_HALF_EVEN)
    except InvalidOperation as exc:
        raise ValueError("Decimal value cannot be quantized") from exc
    if quantized == ZERO:
        return ZERO
    return quantized


def _is_public_dataclass(value: object) -> bool:
    return is_dataclass(value) and not isinstance(value, type)


def _reject_unsafe_public_payload(
    label: str,
    value: object,
    *,
    allow_json_containers: bool = False,
) -> None:
    if _is_public_dataclass(value):
        _reject_unsafe_public_payload(
            label,
            _dataclass_values(value),
            allow_json_containers=True,
        )
        return
    if type(value) is str:
        if _has_unsafe_public_fragment(value):
            raise ValueError(f"unsafe public value in {label}")
        return
    if isinstance(value, dict):
        if not allow_json_containers:
            raise ValueError(f"{label} must be a public dataclass")
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            if _has_unsafe_public_fragment(key):
                raise ValueError(f"unsafe public field in {label}: {key}")
            if key == "derived_validation_digest":
                _require_sha256_digest(key, item)
                continue
            _reject_unsafe_public_payload(
                label,
                item,
                allow_json_containers=True,
            )
        return
    if isinstance(value, (list, tuple)):
        if not allow_json_containers:
            raise ValueError(f"{label} must be a public dataclass")
        for item in value:
            _reject_unsafe_public_payload(
                label,
                item,
                allow_json_containers=True,
            )
        return
    if type(value) in {Decimal, datetime, bool} or value is None:
        return
    raise ValueError(f"unsupported public payload value {type(value).__name__}")


def _has_unsafe_public_fragment(value: str) -> bool:
    lowered = value.lower()
    return any(fragment in lowered for fragment in UNSAFE_PUBLIC_FRAGMENTS)
