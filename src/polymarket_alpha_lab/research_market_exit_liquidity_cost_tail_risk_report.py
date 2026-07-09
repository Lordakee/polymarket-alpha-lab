"""Pure report-only exit liquidity cost tail risk reducer."""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable, Mapping
from dataclasses import dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
import json
import re
from typing import Any


__all__ = (
    "MARKET_EXIT_LIQUIDITY_COST_TAIL_RISK_STATUSES",
    "DEFAULT_RESEARCH_MARKET_EXIT_LIQUIDITY_COST_TAIL_RISK_REPORT_CONFIG_VERSION",
    "ResearchMarketExitLiquidityCostTailRiskConfig",
    "ResearchMarketExitLiquidityCostTailRiskObservation",
    "ResearchMarketExitLiquidityCostTailRiskReasonCodeCount",
    "ResearchMarketExitLiquidityCostTailRiskReport",
    "ResearchMarketExitLiquidityCostTailRiskRow",
    "build_research_market_exit_liquidity_cost_tail_risk_report",
    "research_market_exit_liquidity_cost_tail_risk_report_digest",
    "research_market_exit_liquidity_cost_tail_risk_report_payload",
)


DEFAULT_RESEARCH_MARKET_EXIT_LIQUIDITY_COST_TAIL_RISK_REPORT_CONFIG_VERSION = (
    "research-market-exit-liquidity-cost-tail-risk-report-v0"
)

MARKET_EXIT_LIQUIDITY_COST_TAIL_RISK_STATUSES = ("pass", "watch", "block")
STATUS_PASS = "pass"
STATUS_WATCH = "watch"
STATUS_BLOCK = "block"
MISSING_INPUTS_REASON = "missing_exit_liquidity_cost_tail_risk_observations"
QUANTUM = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
THREE = Decimal("3.000000")
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
PUBLIC_LABEL_RE = re.compile(r"^[a-z0-9][a-z0-9_.-]{0,127}$")
PRIVATE_REF_RE = re.compile(r"^[^\x00-\x1f\x7f]{1,512}$")
REASON_CODE_RE = re.compile(r"^[a-z0-9][a-z0-9_]{0,127}$")
HEX_DIGEST_RE = re.compile(r"^[0-9a-f]{64}$")
PHASE_FLAG_FIELDS = ("paper_only", "report_only", "readonly")


def _join_parts(*parts: str) -> str:
    return "".join(parts)


UNSAFE_PUBLIC_FRAGMENTS = (
    _join_parts("ra", "w"),
    _join_parts("can", "didate"),
    _join_parts("can", "didate", "_", "id"),
    _join_parts("can", "didate", "-", "id"),
    _join_parts("ma", "rket", "_", "id"),
    _join_parts("ma", "rket", "-", "id"),
    _join_parts("ma", "rket", "_", "sl", "ug"),
    _join_parts("ma", "rket", "-", "sl", "ug"),
    _join_parts("sl", "ug"),
    _join_parts("ques", "tion"),
    _join_parts("sour", "ce", "_", "url"),
    _join_parts("sour", "ce", "-", "url"),
    _join_parts("sour", "ce", "_", "text"),
    _join_parts("sour", "ce", "-", "text"),
    _join_parts("d", "sn"),
    _join_parts("tab", "le"),
    _join_parts("to", "ken"),
    _join_parts("wal", "let"),
    _join_parts("au", "th"),
    _join_parts("or", "der"),
    _join_parts("tra", "de"),
    _join_parts("li", "ve"),
    _join_parts("reco", "mmend"),
    _join_parts("reco", "mmend", "ation"),
    _join_parts("siz", "ing"),
    "://",
)


class _FinalDataclass:
    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        for base in cls.__bases__:
            if base is not _FinalDataclass and issubclass(base, _FinalDataclass):
                raise TypeError(f"{base.__name__} may not be subclassed")


@dataclass(frozen=True)
class ResearchMarketExitLiquidityCostTailRiskConfig(_FinalDataclass):
    config_version: str = (
        DEFAULT_RESEARCH_MARKET_EXIT_LIQUIDITY_COST_TAIL_RISK_REPORT_CONFIG_VERSION
    )
    pass_max_expected_exit_cost_rate: Decimal = Decimal("0.030000")
    block_max_expected_exit_cost_rate: Decimal = Decimal("0.100000")
    pass_max_tail_cost_rate: Decimal = Decimal("0.060000")
    block_max_tail_cost_rate: Decimal = Decimal("0.120000")
    pass_max_tail_risk_score: Decimal = Decimal("0.250000")
    block_min_tail_risk_score: Decimal = Decimal("0.650000")
    pass_min_liquidity_safety_margin: Decimal = Decimal("0.650000")
    block_max_liquidity_safety_margin: Decimal = Decimal("0.350000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchMarketExitLiquidityCostTailRiskConfig,
            "config",
        )
        _require_public_label("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_MARKET_EXIT_LIQUIDITY_COST_TAIL_RISK_REPORT_CONFIG_VERSION
        ):
            raise ValueError("config_version must match supported value")
        for field_name in (
            "pass_max_expected_exit_cost_rate",
            "block_max_expected_exit_cost_rate",
            "pass_max_tail_cost_rate",
            "block_max_tail_cost_rate",
            "pass_max_tail_risk_score",
            "block_min_tail_risk_score",
            "pass_min_liquidity_safety_margin",
            "block_max_liquidity_safety_margin",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_probability_decimal(field_name, getattr(self, field_name)),
            )
        if self.block_max_expected_exit_cost_rate <= self.pass_max_expected_exit_cost_rate:
            raise ValueError(
                "block_max_expected_exit_cost_rate must exceed pass threshold",
            )
        if self.block_max_tail_cost_rate <= self.pass_max_tail_cost_rate:
            raise ValueError("block_max_tail_cost_rate must exceed pass threshold")
        if self.block_min_tail_risk_score <= self.pass_max_tail_risk_score:
            raise ValueError("block_min_tail_risk_score must exceed pass threshold")
        if (
            self.pass_min_liquidity_safety_margin
            <= self.block_max_liquidity_safety_margin
        ):
            raise ValueError(
                "pass_min_liquidity_safety_margin must exceed block threshold",
            )
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class ResearchMarketExitLiquidityCostTailRiskObservation(_FinalDataclass):
    input_research_ref: str
    observed_at: datetime
    exit_fee_rate: Decimal
    exit_spread_rate: Decimal
    expected_slippage_rate: Decimal
    tail_slippage_rate: Decimal
    depth_shortfall_rate: Decimal
    liquidity_stress_score: Decimal
    volatility_stress_score: Decimal
    resolution_tail_risk_score: Decimal
    reason_codes: tuple[str, ...] = ()
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchMarketExitLiquidityCostTailRiskObservation,
            "observation",
        )
        _require_private_reference("input_research_ref", self.input_research_ref)
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in (
            "exit_fee_rate",
            "exit_spread_rate",
            "expected_slippage_rate",
            "tail_slippage_rate",
            "depth_shortfall_rate",
            "liquidity_stress_score",
            "volatility_stress_score",
            "resolution_tail_risk_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_probability_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes),
        )
        _require_hard_flags("observation", self)


@dataclass(frozen=True)
class ResearchMarketExitLiquidityCostTailRiskRow(_FinalDataclass):
    public_row_ref: str
    input_ref_digest: str
    observed_at: datetime
    exit_fee_rate: Decimal
    exit_spread_rate: Decimal
    expected_slippage_rate: Decimal
    tail_slippage_rate: Decimal
    depth_shortfall_rate: Decimal
    expected_exit_cost_rate: Decimal
    tail_cost_rate: Decimal
    tail_cost_delta_rate: Decimal
    tail_risk_score: Decimal
    liquidity_safety_margin: Decimal
    status: str
    reason_codes: tuple[str, ...]
    row_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchMarketExitLiquidityCostTailRiskRow, "row")
        _require_public_label("public_row_ref", self.public_row_ref)
        _require_hex_digest("input_ref_digest", self.input_ref_digest)
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in (
            "exit_fee_rate",
            "exit_spread_rate",
            "expected_slippage_rate",
            "tail_slippage_rate",
            "depth_shortfall_rate",
            "expected_exit_cost_rate",
            "tail_cost_rate",
            "tail_cost_delta_rate",
            "tail_risk_score",
            "liquidity_safety_margin",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_probability_decimal(field_name, getattr(self, field_name)),
            )
        _require_status("status", self.status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes),
        )
        _require_hard_flags("row", self)
        _validate_row(self)
        expected_digest = _row_validation_digest(self)
        if self.row_validation_digest:
            _require_hex_digest("row_validation_digest", self.row_validation_digest)
            if self.row_validation_digest != expected_digest:
                raise ValueError("row_validation_digest must match row fields")
        else:
            object.__setattr__(self, "row_validation_digest", expected_digest)


@dataclass(frozen=True)
class ResearchMarketExitLiquidityCostTailRiskReasonCodeCount(_FinalDataclass):
    reason_code: str
    count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchMarketExitLiquidityCostTailRiskReasonCodeCount,
            "reason_code_count",
        )
        object.__setattr__(self, "reason_code", _normalize_reason_code(self.reason_code))
        object.__setattr__(
            self,
            "count",
            _require_positive_decimal("count", self.count),
        )
        _require_hard_flags("reason_code_count", self)


@dataclass(frozen=True)
class ResearchMarketExitLiquidityCostTailRiskReport(_FinalDataclass):
    generated_at: datetime
    config_version: str
    observation_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    max_expected_exit_cost_rate: Decimal
    max_tail_cost_rate: Decimal
    max_tail_risk_score: Decimal
    min_liquidity_safety_margin: Decimal
    average_expected_exit_cost_rate: Decimal | None
    average_tail_cost_rate: Decimal | None
    average_tail_risk_score: Decimal | None
    status: str
    rows: tuple[ResearchMarketExitLiquidityCostTailRiskRow, ...]
    reason_code_counts: tuple[ResearchMarketExitLiquidityCostTailRiskReasonCodeCount, ...]
    reason_codes: tuple[str, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchMarketExitLiquidityCostTailRiskReport, "report")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_label("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_MARKET_EXIT_LIQUIDITY_COST_TAIL_RISK_REPORT_CONFIG_VERSION
        ):
            raise ValueError("config_version must match supported value")
        for field_name in (
            "observation_count",
            "pass_count",
            "watch_count",
            "block_count",
            "max_expected_exit_cost_rate",
            "max_tail_cost_rate",
            "max_tail_risk_score",
            "min_liquidity_safety_margin",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "average_expected_exit_cost_rate",
            "average_tail_cost_rate",
            "average_tail_risk_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_optional_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        _require_status("status", self.status)
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        object.__setattr__(self, "reason_codes", _normalize_reason_codes(self.reason_codes))
        _require_hard_flags("report", self)
        _validate_report(self)
        expected_digest = _report_validation_digest(self)
        if self.derived_validation_digest:
            _require_hex_digest("derived_validation_digest", self.derived_validation_digest)
            if self.derived_validation_digest != expected_digest:
                raise ValueError("derived_validation_digest must match report fields")
        else:
            object.__setattr__(self, "derived_validation_digest", expected_digest)


def build_research_market_exit_liquidity_cost_tail_risk_report(
    observations: Iterable[object],
    *,
    config: ResearchMarketExitLiquidityCostTailRiskConfig,
    generated_at: datetime,
) -> ResearchMarketExitLiquidityCostTailRiskReport:
    if type(config) is not ResearchMarketExitLiquidityCostTailRiskConfig:
        raise ValueError("config must be a ResearchMarketExitLiquidityCostTailRiskConfig")
    _require_hard_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    items = _normalize_observations(observations)
    for item in items:
        if item.observed_at > generated_at_utc:
            raise ValueError("observed_at must not be after generated_at")
    rows_without_refs = tuple(_row_from_observation(item, config=config) for item in items)
    rows = tuple(
        _replace_row_ref(row, public_row_ref=f"exit_liquidity_cost_tail_risk_row_{index:03d}")
        for index, row in enumerate(sorted(rows_without_refs, key=_row_sort_key), start=1)
    )
    reason_codes = _summary_reason_codes(rows)
    return ResearchMarketExitLiquidityCostTailRiskReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        observation_count=_decimal_count(len(rows)),
        pass_count=_decimal_count(_status_count(rows, STATUS_PASS)),
        watch_count=_decimal_count(_status_count(rows, STATUS_WATCH)),
        block_count=_decimal_count(_status_count(rows, STATUS_BLOCK)),
        max_expected_exit_cost_rate=_maximum_row_value(rows, "expected_exit_cost_rate"),
        max_tail_cost_rate=_maximum_row_value(rows, "tail_cost_rate"),
        max_tail_risk_score=_maximum_row_value(rows, "tail_risk_score"),
        min_liquidity_safety_margin=_minimum_row_value(rows, "liquidity_safety_margin"),
        average_expected_exit_cost_rate=_average_row_value(
            rows,
            "expected_exit_cost_rate",
        ),
        average_tail_cost_rate=_average_row_value(rows, "tail_cost_rate"),
        average_tail_risk_score=_average_row_value(rows, "tail_risk_score"),
        status=_summary_status(reason_codes),
        rows=rows,
        reason_code_counts=_reason_code_counts(rows, reason_codes),
        reason_codes=reason_codes,
    )


def research_market_exit_liquidity_cost_tail_risk_report_payload(
    report: ResearchMarketExitLiquidityCostTailRiskReport | Mapping[str, object],
) -> dict[str, Any]:
    if type(report) is ResearchMarketExitLiquidityCostTailRiskReport:
        _require_hard_flags("report", report)
        expected_digest = _report_validation_digest(report)
        if report.derived_validation_digest != expected_digest:
            raise ValueError("derived_validation_digest must match report fields")
        payload = _report_payload(report)
        _validate_public_payload(payload)
        return payload
    if type(report) is dict:
        _validate_public_payload(report)
        return dict(report)
    raise ValueError(
        "report must be a ResearchMarketExitLiquidityCostTailRiskReport or payload dict",
    )


def research_market_exit_liquidity_cost_tail_risk_report_digest(
    report: ResearchMarketExitLiquidityCostTailRiskReport,
) -> str:
    if type(report) is not ResearchMarketExitLiquidityCostTailRiskReport:
        raise ValueError("report must be a ResearchMarketExitLiquidityCostTailRiskReport")
    _require_hard_flags("report", report)
    expected_digest = _report_validation_digest(report)
    if report.derived_validation_digest != expected_digest:
        raise ValueError("derived_validation_digest must match report fields")
    return expected_digest


def _row_from_observation(
    observation: ResearchMarketExitLiquidityCostTailRiskObservation,
    *,
    config: ResearchMarketExitLiquidityCostTailRiskConfig,
) -> ResearchMarketExitLiquidityCostTailRiskRow:
    expected_exit_cost_rate = _quantize(
        observation.exit_fee_rate
        + observation.exit_spread_rate
        + observation.expected_slippage_rate,
    )
    tail_cost_rate = _quantize(
        observation.exit_fee_rate
        + observation.exit_spread_rate
        + observation.tail_slippage_rate
        + observation.depth_shortfall_rate,
    )
    tail_cost_delta_rate = _max_decimal(ZERO, _quantize(tail_cost_rate - expected_exit_cost_rate))
    tail_risk_score = _ratio(
        observation.liquidity_stress_score
        + observation.volatility_stress_score
        + observation.resolution_tail_risk_score,
        THREE,
    )
    liquidity_safety_margin = _max_decimal(
        ZERO,
        _quantize(ONE - tail_cost_rate - tail_risk_score),
    )
    status = _row_status(
        expected_exit_cost_rate=expected_exit_cost_rate,
        tail_cost_rate=tail_cost_rate,
        tail_risk_score=tail_risk_score,
        liquidity_safety_margin=liquidity_safety_margin,
        config=config,
    )
    return ResearchMarketExitLiquidityCostTailRiskRow(
        public_row_ref="exit_liquidity_cost_tail_risk_row_pending",
        input_ref_digest=_private_reference_digest(observation.input_research_ref),
        observed_at=observation.observed_at,
        exit_fee_rate=observation.exit_fee_rate,
        exit_spread_rate=observation.exit_spread_rate,
        expected_slippage_rate=observation.expected_slippage_rate,
        tail_slippage_rate=observation.tail_slippage_rate,
        depth_shortfall_rate=observation.depth_shortfall_rate,
        expected_exit_cost_rate=expected_exit_cost_rate,
        tail_cost_rate=tail_cost_rate,
        tail_cost_delta_rate=tail_cost_delta_rate,
        tail_risk_score=tail_risk_score,
        liquidity_safety_margin=liquidity_safety_margin,
        status=status,
        reason_codes=_row_reason_codes(
            expected_exit_cost_rate=expected_exit_cost_rate,
            tail_cost_rate=tail_cost_rate,
            tail_cost_delta_rate=tail_cost_delta_rate,
            tail_risk_score=tail_risk_score,
            liquidity_safety_margin=liquidity_safety_margin,
            input_reason_codes=observation.reason_codes,
            config=config,
        ),
    )


def _replace_row_ref(
    row: ResearchMarketExitLiquidityCostTailRiskRow,
    *,
    public_row_ref: str,
) -> ResearchMarketExitLiquidityCostTailRiskRow:
    return ResearchMarketExitLiquidityCostTailRiskRow(
        public_row_ref=public_row_ref,
        input_ref_digest=row.input_ref_digest,
        observed_at=row.observed_at,
        exit_fee_rate=row.exit_fee_rate,
        exit_spread_rate=row.exit_spread_rate,
        expected_slippage_rate=row.expected_slippage_rate,
        tail_slippage_rate=row.tail_slippage_rate,
        depth_shortfall_rate=row.depth_shortfall_rate,
        expected_exit_cost_rate=row.expected_exit_cost_rate,
        tail_cost_rate=row.tail_cost_rate,
        tail_cost_delta_rate=row.tail_cost_delta_rate,
        tail_risk_score=row.tail_risk_score,
        liquidity_safety_margin=row.liquidity_safety_margin,
        status=row.status,
        reason_codes=row.reason_codes,
    )


def _row_status(
    *,
    expected_exit_cost_rate: Decimal,
    tail_cost_rate: Decimal,
    tail_risk_score: Decimal,
    liquidity_safety_margin: Decimal,
    config: ResearchMarketExitLiquidityCostTailRiskConfig,
) -> str:
    if (
        expected_exit_cost_rate <= config.pass_max_expected_exit_cost_rate
        and tail_cost_rate <= config.pass_max_tail_cost_rate
        and tail_risk_score <= config.pass_max_tail_risk_score
        and liquidity_safety_margin >= config.pass_min_liquidity_safety_margin
    ):
        return STATUS_PASS
    if (
        expected_exit_cost_rate >= config.block_max_expected_exit_cost_rate
        or tail_cost_rate >= config.block_max_tail_cost_rate
        or tail_risk_score >= config.block_min_tail_risk_score
        or liquidity_safety_margin <= config.block_max_liquidity_safety_margin
    ):
        return STATUS_BLOCK
    return STATUS_WATCH


def _row_reason_codes(
    *,
    expected_exit_cost_rate: Decimal,
    tail_cost_rate: Decimal,
    tail_cost_delta_rate: Decimal,
    tail_risk_score: Decimal,
    liquidity_safety_margin: Decimal,
    input_reason_codes: tuple[str, ...],
    config: ResearchMarketExitLiquidityCostTailRiskConfig,
) -> tuple[str, ...]:
    reasons: list[str] = []
    if expected_exit_cost_rate <= config.pass_max_expected_exit_cost_rate:
        reasons.append("expected_exit_cost_within_pass_band")
    elif expected_exit_cost_rate >= config.block_max_expected_exit_cost_rate:
        reasons.append("expected_exit_cost_above_block_band")
    else:
        reasons.append("expected_exit_cost_watch_band")
    if tail_cost_rate <= config.pass_max_tail_cost_rate:
        reasons.append("tail_cost_within_pass_band")
    elif tail_cost_rate >= config.block_max_tail_cost_rate:
        reasons.append("tail_cost_above_block_band")
    else:
        reasons.append("tail_cost_watch_band")
    if tail_risk_score <= config.pass_max_tail_risk_score:
        reasons.append("tail_risk_low")
    elif tail_risk_score >= config.block_min_tail_risk_score:
        reasons.append("tail_risk_block")
    else:
        reasons.append("tail_risk_watch")
    if liquidity_safety_margin >= config.pass_min_liquidity_safety_margin:
        reasons.append("liquidity_safety_margin_pass")
    elif liquidity_safety_margin <= config.block_max_liquidity_safety_margin:
        reasons.append("liquidity_safety_margin_block")
    else:
        reasons.append("liquidity_safety_margin_watch")
    if tail_cost_delta_rate > ZERO:
        reasons.append("tail_cost_delta_observed")
    for reason_code in input_reason_codes:
        reasons.append(f"input_{reason_code}")
    return tuple(sorted(set(reasons)))


def _normalize_observations(
    observations: Iterable[object],
) -> tuple[ResearchMarketExitLiquidityCostTailRiskObservation, ...]:
    if isinstance(observations, (str, bytes)):
        raise ValueError("observations must be an iterable of observation records")
    normalized: list[ResearchMarketExitLiquidityCostTailRiskObservation] = []
    seen_refs: set[str] = set()
    for item in observations:
        if type(item) is not ResearchMarketExitLiquidityCostTailRiskObservation:
            raise ValueError(
                "observations must contain "
                "ResearchMarketExitLiquidityCostTailRiskObservation",
            )
        _require_hard_flags("observation", item)
        if item.input_research_ref in seen_refs:
            raise ValueError("input_research_ref values must be unique")
        seen_refs.add(item.input_research_ref)
        normalized.append(item)
    return tuple(normalized)


def _normalize_rows(
    rows: tuple[ResearchMarketExitLiquidityCostTailRiskRow, ...],
) -> tuple[ResearchMarketExitLiquidityCostTailRiskRow, ...]:
    if type(rows) is not tuple:
        raise ValueError("rows must be a tuple")
    for row in rows:
        if type(row) is not ResearchMarketExitLiquidityCostTailRiskRow:
            raise ValueError(
                "rows must contain ResearchMarketExitLiquidityCostTailRiskRow values",
            )
        _require_hard_flags("row", row)
    expected_refs = tuple(
        f"exit_liquidity_cost_tail_risk_row_{index:03d}"
        for index in range(1, len(rows) + 1)
    )
    actual_refs = tuple(row.public_row_ref for row in rows)
    if rows and actual_refs != expected_refs:
        raise ValueError("rows must use sequential public_row_ref values")
    return rows


def _normalize_reason_code_counts(
    rows: tuple[ResearchMarketExitLiquidityCostTailRiskReasonCodeCount, ...],
) -> tuple[ResearchMarketExitLiquidityCostTailRiskReasonCodeCount, ...]:
    if type(rows) is not tuple:
        raise ValueError("reason_code_counts must be a tuple")
    for row in rows:
        if type(row) is not ResearchMarketExitLiquidityCostTailRiskReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "ResearchMarketExitLiquidityCostTailRiskReasonCodeCount values",
            )
        _require_hard_flags("reason_code_count", row)
    expected = tuple(sorted(row.reason_code for row in rows))
    actual = tuple(row.reason_code for row in rows)
    if actual != expected:
        raise ValueError("reason_code_counts must be sorted by reason_code")
    if len(set(actual)) != len(actual):
        raise ValueError("reason_code_counts must not contain duplicate reason_codes")
    return rows


def _normalize_reason_codes(value: tuple[str, ...]) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ValueError("reason_codes must be a tuple")
    normalized = tuple(sorted({_normalize_reason_code(item) for item in value}))
    return normalized


def _normalize_reason_code(value: str) -> str:
    if type(value) is not str:
        raise ValueError("reason_code must be a string")
    if not REASON_CODE_RE.fullmatch(value):
        raise ValueError("reason_code must be a lowercase identifier")
    _reject_unsafe_public_text("reason_code", value)
    return value


def _row_sort_key(row: ResearchMarketExitLiquidityCostTailRiskRow) -> tuple[object, ...]:
    return (
        _status_sort_value(row.status),
        row.liquidity_safety_margin,
        -row.tail_cost_rate,
        -row.tail_risk_score,
        row.input_ref_digest,
        row.observed_at.isoformat(),
    )


def _status_sort_value(status: str) -> int:
    if status == STATUS_BLOCK:
        return 0
    if status == STATUS_WATCH:
        return 1
    return 2


def _status_count(
    rows: tuple[ResearchMarketExitLiquidityCostTailRiskRow, ...],
    status: str,
) -> int:
    return sum(1 for row in rows if row.status == status)


def _summary_reason_codes(
    rows: tuple[ResearchMarketExitLiquidityCostTailRiskRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return (MISSING_INPUTS_REASON,)
    reasons: set[str] = set()
    for row in rows:
        reasons.update(row.reason_codes)
    return tuple(sorted(reasons))


def _summary_status(reason_codes: tuple[str, ...]) -> str:
    if MISSING_INPUTS_REASON in reason_codes:
        return STATUS_BLOCK
    if any("block" in reason_code for reason_code in reason_codes):
        return STATUS_BLOCK
    if any("watch" in reason_code for reason_code in reason_codes):
        return STATUS_WATCH
    return STATUS_PASS


def _reason_code_counts(
    rows: tuple[ResearchMarketExitLiquidityCostTailRiskRow, ...],
    reason_codes: tuple[str, ...],
) -> tuple[ResearchMarketExitLiquidityCostTailRiskReasonCodeCount, ...]:
    if not rows:
        return (
            ResearchMarketExitLiquidityCostTailRiskReasonCodeCount(
                reason_code=MISSING_INPUTS_REASON,
                count=ONE,
            ),
        )
    counter: Counter[str] = Counter()
    for row in rows:
        counter.update(row.reason_codes)
    return tuple(
        ResearchMarketExitLiquidityCostTailRiskReasonCodeCount(
            reason_code=reason_code,
            count=_decimal_count(counter[reason_code]),
        )
        for reason_code in reason_codes
        if counter[reason_code] > 0
    )


def _maximum_row_value(
    rows: tuple[ResearchMarketExitLiquidityCostTailRiskRow, ...],
    field_name: str,
) -> Decimal:
    if not rows:
        return ZERO
    return max(_require_decimal(field_name, getattr(row, field_name)) for row in rows)


def _minimum_row_value(
    rows: tuple[ResearchMarketExitLiquidityCostTailRiskRow, ...],
    field_name: str,
) -> Decimal:
    if not rows:
        return ZERO
    return min(_require_decimal(field_name, getattr(row, field_name)) for row in rows)


def _average_row_value(
    rows: tuple[ResearchMarketExitLiquidityCostTailRiskRow, ...],
    field_name: str,
) -> Decimal | None:
    if not rows:
        return None
    return _ratio(
        sum((_require_decimal(field_name, getattr(row, field_name)) for row in rows), ZERO),
        _decimal_count(len(rows)),
    )


def _validate_row(row: ResearchMarketExitLiquidityCostTailRiskRow) -> None:
    expected_exit_cost_rate = _quantize(
        row.exit_fee_rate + row.exit_spread_rate + row.expected_slippage_rate,
    )
    if row.expected_exit_cost_rate != expected_exit_cost_rate:
        raise ValueError("expected_exit_cost_rate must match component fields")
    tail_cost_rate = _quantize(
        row.exit_fee_rate
        + row.exit_spread_rate
        + row.tail_slippage_rate
        + row.depth_shortfall_rate,
    )
    if row.tail_cost_rate != tail_cost_rate:
        raise ValueError("tail_cost_rate must match component fields")
    if row.tail_cost_delta_rate != _max_decimal(
        ZERO,
        _quantize(row.tail_cost_rate - row.expected_exit_cost_rate),
    ):
        raise ValueError("tail_cost_delta_rate must match cost fields")
    if row.liquidity_safety_margin != _max_decimal(
        ZERO,
        _quantize(ONE - row.tail_cost_rate - row.tail_risk_score),
    ):
        raise ValueError("liquidity_safety_margin must match cost and risk fields")


def _validate_report(report: ResearchMarketExitLiquidityCostTailRiskReport) -> None:
    rows = report.rows
    reason_codes = _summary_reason_codes(rows)
    if report.observation_count != _decimal_count(len(rows)):
        raise ValueError("observation_count must match rows")
    if report.pass_count != _decimal_count(_status_count(rows, STATUS_PASS)):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _decimal_count(_status_count(rows, STATUS_WATCH)):
        raise ValueError("watch_count must match rows")
    if report.block_count != _decimal_count(_status_count(rows, STATUS_BLOCK)):
        raise ValueError("block_count must match rows")
    if report.max_expected_exit_cost_rate != _maximum_row_value(
        rows,
        "expected_exit_cost_rate",
    ):
        raise ValueError("max_expected_exit_cost_rate must match rows")
    if report.max_tail_cost_rate != _maximum_row_value(rows, "tail_cost_rate"):
        raise ValueError("max_tail_cost_rate must match rows")
    if report.max_tail_risk_score != _maximum_row_value(rows, "tail_risk_score"):
        raise ValueError("max_tail_risk_score must match rows")
    if report.min_liquidity_safety_margin != _minimum_row_value(
        rows,
        "liquidity_safety_margin",
    ):
        raise ValueError("min_liquidity_safety_margin must match rows")
    if report.average_expected_exit_cost_rate != _average_row_value(
        rows,
        "expected_exit_cost_rate",
    ):
        raise ValueError("average_expected_exit_cost_rate must match rows")
    if report.average_tail_cost_rate != _average_row_value(rows, "tail_cost_rate"):
        raise ValueError("average_tail_cost_rate must match rows")
    if report.average_tail_risk_score != _average_row_value(rows, "tail_risk_score"):
        raise ValueError("average_tail_risk_score must match rows")
    if report.reason_codes != reason_codes:
        raise ValueError("reason_codes must match rows")
    if report.reason_code_counts != _reason_code_counts(rows, reason_codes):
        raise ValueError("reason_code_counts must match rows")
    if report.status != _summary_status(reason_codes):
        raise ValueError("status must match reason_codes")


def _report_payload(report: ResearchMarketExitLiquidityCostTailRiskReport) -> dict[str, Any]:
    payload = _payload_value(report)
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    return payload


def _row_validation_digest(row: ResearchMarketExitLiquidityCostTailRiskRow) -> str:
    payload = _payload_value(row)
    if type(payload) is not dict:
        raise ValueError("row payload must be a JSON object")
    payload.pop("row_validation_digest", None)
    return _payload_digest(payload)


def _report_validation_digest(report: ResearchMarketExitLiquidityCostTailRiskReport) -> str:
    payload = _report_payload(report)
    payload.pop("derived_validation_digest", None)
    return _payload_digest(payload)


def _payload_digest(payload: dict[str, Any]) -> str:
    encoded = json.dumps(
        payload,
        allow_nan=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    return sha256(encoded.encode("utf-8")).hexdigest()


def _payload_value(value: Any) -> Any:
    if value is None:
        return None
    if is_dataclass(value) and not isinstance(value, type):
        return {
            field.name: _payload_value(getattr(value, field.name))
            for field in fields(value)
        }
    if type(value) is Decimal:
        if not value.is_finite():
            raise ValueError("Decimal value must be finite")
        return str(value)
    if type(value) is datetime:
        return value.astimezone(UTC).isoformat()
    if type(value) in (float, int):
        raise ValueError("Decimal-derived string values must not use numeric literals")
    if type(value) in (str, bool):
        return value
    if type(value) is tuple:
        return [_payload_value(item) for item in value]
    if type(value) is list:
        return [_payload_value(item) for item in value]
    if type(value) is dict:
        ready: dict[str, Any] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            ready[key] = _payload_value(item)
        return ready
    raise ValueError("value is not JSON serializable")


def _validate_public_payload(payload: Mapping[str, object]) -> None:
    if type(payload) is not dict:
        raise ValueError("payload must be a dict")
    _reject_unsafe_public_payload(payload)
    _reject_numeric_literals(payload)
    _validate_payload_statuses(payload)
    for field_name in PHASE_FLAG_FIELDS:
        if payload.get(field_name) is not True:
            raise ValueError(f"{field_name} must be True for payload")
    digest_value = payload.get("derived_validation_digest")
    if type(digest_value) is not str or not HEX_DIGEST_RE.fullmatch(digest_value):
        raise ValueError("derived_validation_digest must be a SHA-256 hex digest")
    digest_payload = dict(payload)
    digest_payload.pop("derived_validation_digest", None)
    if _payload_digest(digest_payload) != digest_value:
        raise ValueError("derived_validation_digest must match payload fields")


def _validate_payload_statuses(value: object) -> None:
    if isinstance(value, Mapping):
        for key, item in value.items():
            if key == "status":
                _require_status("status", item)
            _validate_payload_statuses(item)
        return
    if isinstance(value, (list, tuple)):
        for item in value:
            _validate_payload_statuses(item)


def _reject_unsafe_public_payload(value: object) -> None:
    if isinstance(value, Mapping):
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            _reject_unsafe_public_text("payload key", key)
            _reject_unsafe_public_payload(item)
        return
    if isinstance(value, (list, tuple)):
        for item in value:
            _reject_unsafe_public_payload(item)
        return
    if type(value) is str:
        _reject_unsafe_public_text("payload value", value)


def _reject_unsafe_public_text(label: str, value: str) -> None:
    normalized = value.lower()
    if any(fragment in normalized for fragment in UNSAFE_PUBLIC_FRAGMENTS):
        raise ValueError(f"unsafe public surface in {label}")


def _reject_numeric_literals(value: object) -> None:
    if isinstance(value, Mapping):
        for item in value.values():
            _reject_numeric_literals(item)
        return
    if isinstance(value, (list, tuple)):
        for item in value:
            _reject_numeric_literals(item)
        return
    if type(value) in (float, int):
        raise ValueError("Decimal-derived string values must not use numeric literals")


def _private_reference_digest(value: str) -> str:
    return sha256(value.encode("utf-8")).hexdigest()


def _require_exact_type(value: object, expected_type: type[object], label: str) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{label} must be exactly {expected_type.__name__}")


def _require_public_label(field_name: str, value: str) -> None:
    if type(value) is not str or not PUBLIC_LABEL_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a safe public label")
    _reject_unsafe_public_text(field_name, value)


def _require_private_reference(field_name: str, value: str) -> None:
    if type(value) is not str or not PRIVATE_REF_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a non-empty private reference")


def _require_status(field_name: str, value: str) -> None:
    if type(value) is not str or value not in MARKET_EXIT_LIQUIDITY_COST_TAIL_RISK_STATUSES:
        raise ValueError(f"{field_name} must be pass, watch, or block")


def _require_hex_digest(field_name: str, value: str) -> None:
    if type(value) is not str or not HEX_DIGEST_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a SHA-256 hex digest")


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in PHASE_FLAG_FIELDS:
        if getattr(value, field_name) is not True:
            raise ValueError(f"{field_name} must be True for {label}")


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
    return _quantize(value)


def _require_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value < ZERO:
        raise ValueError(f"{field_name} must be non-negative")
    return decimal_value


def _require_positive_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_nonnegative_decimal(field_name, value)
    if decimal_value <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return decimal_value


def _require_optional_nonnegative_decimal(
    field_name: str,
    value: object,
) -> Decimal | None:
    if value is None:
        return None
    return _require_nonnegative_decimal(field_name, value)


def _require_probability_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value < ZERO or decimal_value > ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return decimal_value


def _quantize(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(QUANTUM)


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator <= ZERO:
        raise ValueError("denominator must be positive")
    with localcontext(DECIMAL_CONTEXT):
        return _quantize(numerator / denominator)


def _decimal_count(value: int) -> Decimal:
    if type(value) is not int or value < 0:
        raise ValueError("count must be a non-negative integer")
    return _quantize(Decimal(value))


def _max_decimal(left: Decimal, right: Decimal) -> Decimal:
    if left >= right:
        return left
    return right
