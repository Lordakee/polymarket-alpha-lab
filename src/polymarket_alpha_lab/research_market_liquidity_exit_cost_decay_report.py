"""Pure report-only liquidity exit cost decay reducer for manual research."""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, InvalidOperation, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
import json
import re
from typing import Any


__all__ = (
    "MARKET_LIQUIDITY_EXIT_COST_DECAY_STATUSES",
    "DEFAULT_RESEARCH_MARKET_LIQUIDITY_EXIT_COST_DECAY_REPORT_CONFIG_VERSION",
    "ResearchMarketLiquidityExitCostDecayConfig",
    "ResearchMarketLiquidityExitCostDecayObservation",
    "ResearchMarketLiquidityExitCostDecayReasonCodeCount",
    "ResearchMarketLiquidityExitCostDecayReport",
    "ResearchMarketLiquidityExitCostDecayRow",
    "build_research_market_liquidity_exit_cost_decay_report",
    "research_market_liquidity_exit_cost_decay_report_digest",
    "research_market_liquidity_exit_cost_decay_report_payload",
)


DEFAULT_RESEARCH_MARKET_LIQUIDITY_EXIT_COST_DECAY_REPORT_CONFIG_VERSION = (
    "research-market-liquidity-exit-cost-decay-report-v0"
)

MARKET_LIQUIDITY_EXIT_COST_DECAY_STATUSES = ("pass", "watch", "block")
STATUS_PASS = "pass"
STATUS_WATCH = "watch"
STATUS_BLOCK = "block"
MISSING_INPUTS_REASON = "no_liquidity_exit_cost_decay_observations"
QUANTUM = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
PUBLIC_LABEL_RE = re.compile(r"^[a-z0-9][a-z0-9_.-]{0,127}$")
PRIVATE_REF_RE = re.compile(r"^[^\x00-\x1f\x7f]{1,512}$")
REASON_CODE_RE = re.compile(r"^[a-z0-9][a-z0-9_]{0,127}$")
HEX_DIGEST_RE = re.compile(r"^[0-9a-f]{64}$")
DECIMAL_STRING_RE = re.compile(r"^(?:0|[1-9][0-9]*)\.[0-9]{6}$")
PHASE_FLAG_FIELDS = ("paper_only", "report_only", "readonly")
REPORT_PAYLOAD_KEYS = frozenset(
    (
        "generated_at",
        "config_version",
        "observation_count",
        "pass_count",
        "watch_count",
        "block_count",
        "average_total_exit_cost_rate",
        "average_liquidity_decay_ratio",
        "average_liquidity_exit_cost_decay_score",
        "max_quote_age_seconds",
        "max_total_exit_cost_rate",
        "max_liquidity_decay_ratio",
        "min_exit_depth_ratio",
        "status",
        "rows",
        "reason_code_counts",
        "reason_codes",
        "paper_only",
        "report_only",
        "readonly",
        "derived_validation_digest",
    ),
)
ROW_PAYLOAD_KEYS = frozenset(
    (
        "public_row_ref",
        "internal_liquidity_ref_digest",
        "observed_at",
        "quote_age_seconds",
        "exit_fee_rate",
        "exit_spread_rate",
        "exit_slippage_rate",
        "total_exit_cost_rate",
        "baseline_exit_depth",
        "current_exit_depth",
        "exit_depth_ratio",
        "liquidity_decay_ratio",
        "exit_cost_score",
        "liquidity_decay_score",
        "quote_freshness_score",
        "exit_depth_score",
        "liquidity_exit_cost_decay_score",
        "status",
        "reason_codes",
        "paper_only",
        "report_only",
        "readonly",
        "row_validation_digest",
    ),
)
REASON_CODE_COUNT_PAYLOAD_KEYS = frozenset(
    (
        "reason_code",
        "count",
        "row_ratio",
        "paper_only",
        "report_only",
        "readonly",
    ),
)
REPORT_DECIMAL_STRING_FIELDS = frozenset(
    (
        "observation_count",
        "pass_count",
        "watch_count",
        "block_count",
        "max_quote_age_seconds",
        "max_total_exit_cost_rate",
        "max_liquidity_decay_ratio",
        "min_exit_depth_ratio",
    ),
)
REPORT_OPTIONAL_DECIMAL_STRING_FIELDS = frozenset(
    (
        "average_total_exit_cost_rate",
        "average_liquidity_decay_ratio",
        "average_liquidity_exit_cost_decay_score",
    ),
)
ROW_DECIMAL_STRING_FIELDS = frozenset(
    (
        "quote_age_seconds",
        "exit_fee_rate",
        "exit_spread_rate",
        "exit_slippage_rate",
        "total_exit_cost_rate",
        "baseline_exit_depth",
        "current_exit_depth",
        "exit_depth_ratio",
        "liquidity_decay_ratio",
        "exit_cost_score",
        "liquidity_decay_score",
        "quote_freshness_score",
        "exit_depth_score",
        "liquidity_exit_cost_decay_score",
    ),
)


def _join_parts(*parts: str) -> str:
    return "".join(parts)


UNSAFE_PUBLIC_FRAGMENTS = (
    _join_parts("ra", "w"),
    _join_parts("can", "didate"),
    _join_parts("can", "didate", "_", "id"),
    _join_parts("con", "dition", "_", "id"),
    _join_parts("ma", "rket", "_", "id"),
    _join_parts("ma", "rket", "-", "id"),
    _join_parts("ma", "rket", "_", "sl", "ug"),
    _join_parts("ma", "rket", "-", "sl", "ug"),
    _join_parts("sl", "ug"),
    _join_parts("ques", "tion"),
    _join_parts("sour", "ce", "_", "url"),
    _join_parts("sour", "ce", "_", "text"),
    _join_parts("d", "sn"),
    _join_parts("tab", "le"),
    _join_parts("to", "ken"),
    _join_parts("wal", "let"),
    _join_parts("au", "th"),
    _join_parts("or", "der"),
    _join_parts("tra", "de"),
    _join_parts("li", "ve"),
    _join_parts("reco", "mmend"),
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
class ResearchMarketLiquidityExitCostDecayConfig(_FinalDataclass):
    config_version: str = (
        DEFAULT_RESEARCH_MARKET_LIQUIDITY_EXIT_COST_DECAY_REPORT_CONFIG_VERSION
    )
    max_pass_exit_cost_rate: Decimal = Decimal("0.030000")
    max_watch_exit_cost_rate: Decimal = Decimal("0.070000")
    max_pass_liquidity_decay_ratio: Decimal = Decimal("0.250000")
    max_watch_liquidity_decay_ratio: Decimal = Decimal("0.600000")
    max_pass_quote_age_seconds: Decimal = Decimal("300.000000")
    max_watch_quote_age_seconds: Decimal = Decimal("900.000000")
    min_pass_exit_depth_ratio: Decimal = Decimal("0.750000")
    min_watch_exit_depth_ratio: Decimal = Decimal("0.400000")
    pass_liquidity_exit_cost_decay_score: Decimal = Decimal("0.750000")
    watch_liquidity_exit_cost_decay_score: Decimal = Decimal("0.450000")
    exit_cost_pressure_weight: Decimal = Decimal("0.350000")
    liquidity_decay_weight: Decimal = Decimal("0.250000")
    quote_freshness_weight: Decimal = Decimal("0.200000")
    exit_depth_weight: Decimal = Decimal("0.200000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchMarketLiquidityExitCostDecayConfig, "config")
        _require_public_label("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_MARKET_LIQUIDITY_EXIT_COST_DECAY_REPORT_CONFIG_VERSION
        ):
            raise ValueError("config_version must match supported value")
        for field_name in (
            "max_pass_exit_cost_rate",
            "max_watch_exit_cost_rate",
            "max_pass_liquidity_decay_ratio",
            "max_watch_liquidity_decay_ratio",
            "min_pass_exit_depth_ratio",
            "min_watch_exit_depth_ratio",
            "pass_liquidity_exit_cost_decay_score",
            "watch_liquidity_exit_cost_decay_score",
            "exit_cost_pressure_weight",
            "liquidity_decay_weight",
            "quote_freshness_weight",
            "exit_depth_weight",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_probability_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in ("max_pass_quote_age_seconds", "max_watch_quote_age_seconds"):
            object.__setattr__(
                self,
                field_name,
                _require_positive_decimal(field_name, getattr(self, field_name)),
            )
        if self.max_watch_exit_cost_rate <= self.max_pass_exit_cost_rate:
            raise ValueError("max_watch_exit_cost_rate must exceed pass threshold")
        if self.max_watch_liquidity_decay_ratio <= self.max_pass_liquidity_decay_ratio:
            raise ValueError(
                "max_watch_liquidity_decay_ratio must exceed pass threshold",
            )
        if self.max_watch_quote_age_seconds <= self.max_pass_quote_age_seconds:
            raise ValueError("max_watch_quote_age_seconds must exceed pass threshold")
        if self.min_pass_exit_depth_ratio <= self.min_watch_exit_depth_ratio:
            raise ValueError("min_pass_exit_depth_ratio must exceed watch threshold")
        if (
            self.pass_liquidity_exit_cost_decay_score
            <= self.watch_liquidity_exit_cost_decay_score
        ):
            raise ValueError(
                "pass_liquidity_exit_cost_decay_score must exceed watch threshold",
            )
        weight_sum = _quantize(
            self.exit_cost_pressure_weight
            + self.liquidity_decay_weight
            + self.quote_freshness_weight
            + self.exit_depth_weight,
        )
        if weight_sum != ONE:
            raise ValueError("liquidity exit cost decay score weights must sum to 1")
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class ResearchMarketLiquidityExitCostDecayObservation(_FinalDataclass):
    internal_liquidity_ref: str
    observed_at: datetime
    exit_fee_rate: Decimal
    exit_spread_rate: Decimal
    exit_slippage_rate: Decimal
    baseline_exit_depth: Decimal
    current_exit_depth: Decimal
    reason_codes: tuple[str, ...] = ()
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchMarketLiquidityExitCostDecayObservation,
            "observation",
        )
        _require_private_reference("internal_liquidity_ref", self.internal_liquidity_ref)
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in ("exit_fee_rate", "exit_spread_rate", "exit_slippage_rate"):
            object.__setattr__(
                self,
                field_name,
                _require_probability_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "baseline_exit_depth",
            _require_positive_decimal("baseline_exit_depth", self.baseline_exit_depth),
        )
        object.__setattr__(
            self,
            "current_exit_depth",
            _require_nonnegative_decimal("current_exit_depth", self.current_exit_depth),
        )
        if self.current_exit_depth > self.baseline_exit_depth:
            raise ValueError("current_exit_depth must not exceed baseline_exit_depth")
        object.__setattr__(self, "reason_codes", _normalize_reason_codes(self.reason_codes))
        _require_hard_flags("observation", self)


@dataclass(frozen=True)
class ResearchMarketLiquidityExitCostDecayRow(_FinalDataclass):
    public_row_ref: str
    internal_liquidity_ref_digest: str
    observed_at: datetime
    quote_age_seconds: Decimal
    exit_fee_rate: Decimal
    exit_spread_rate: Decimal
    exit_slippage_rate: Decimal
    total_exit_cost_rate: Decimal
    baseline_exit_depth: Decimal
    current_exit_depth: Decimal
    exit_depth_ratio: Decimal
    liquidity_decay_ratio: Decimal
    exit_cost_score: Decimal
    liquidity_decay_score: Decimal
    quote_freshness_score: Decimal
    exit_depth_score: Decimal
    liquidity_exit_cost_decay_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    row_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchMarketLiquidityExitCostDecayRow, "row")
        _require_public_label("public_row_ref", self.public_row_ref)
        _require_hex_digest(
            "internal_liquidity_ref_digest",
            self.internal_liquidity_ref_digest,
        )
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in (
            "quote_age_seconds",
            "exit_fee_rate",
            "exit_spread_rate",
            "exit_slippage_rate",
            "total_exit_cost_rate",
            "baseline_exit_depth",
            "current_exit_depth",
            "exit_depth_ratio",
            "liquidity_decay_ratio",
            "exit_cost_score",
            "liquidity_decay_score",
            "quote_freshness_score",
            "exit_depth_score",
            "liquidity_exit_cost_decay_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "exit_fee_rate",
            "exit_spread_rate",
            "exit_slippage_rate",
            "exit_depth_ratio",
            "liquidity_decay_ratio",
            "exit_cost_score",
            "liquidity_decay_score",
            "quote_freshness_score",
            "exit_depth_score",
            "liquidity_exit_cost_decay_score",
        ):
            _require_probability_decimal(field_name, getattr(self, field_name))
        _require_status("status", self.status)
        object.__setattr__(self, "reason_codes", _normalize_reason_codes(self.reason_codes))
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
class ResearchMarketLiquidityExitCostDecayReasonCodeCount(_FinalDataclass):
    reason_code: str
    count: Decimal
    row_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchMarketLiquidityExitCostDecayReasonCodeCount,
            "reason_code_count",
        )
        object.__setattr__(self, "reason_code", _normalize_reason_code(self.reason_code))
        object.__setattr__(
            self,
            "count",
            _require_positive_decimal("count", self.count),
        )
        object.__setattr__(
            self,
            "row_ratio",
            _require_probability_decimal("row_ratio", self.row_ratio),
        )
        _require_hard_flags("reason_code_count", self)


@dataclass(frozen=True)
class ResearchMarketLiquidityExitCostDecayReport(_FinalDataclass):
    generated_at: datetime
    config_version: str
    observation_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    average_total_exit_cost_rate: Decimal | None
    average_liquidity_decay_ratio: Decimal | None
    average_liquidity_exit_cost_decay_score: Decimal | None
    max_quote_age_seconds: Decimal
    max_total_exit_cost_rate: Decimal
    max_liquidity_decay_ratio: Decimal
    min_exit_depth_ratio: Decimal
    status: str
    rows: tuple[ResearchMarketLiquidityExitCostDecayRow, ...]
    reason_code_counts: tuple[ResearchMarketLiquidityExitCostDecayReasonCodeCount, ...]
    reason_codes: tuple[str, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchMarketLiquidityExitCostDecayReport, "report")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_label("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_MARKET_LIQUIDITY_EXIT_COST_DECAY_REPORT_CONFIG_VERSION
        ):
            raise ValueError("config_version must match supported value")
        for field_name in (
            "observation_count",
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
            "average_total_exit_cost_rate",
            "average_liquidity_decay_ratio",
            "average_liquidity_exit_cost_decay_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_optional_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "max_quote_age_seconds",
            "max_total_exit_cost_rate",
            "max_liquidity_decay_ratio",
            "min_exit_depth_ratio",
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


def build_research_market_liquidity_exit_cost_decay_report(
    observations: Iterable[object],
    *,
    config: ResearchMarketLiquidityExitCostDecayConfig,
    generated_at: datetime,
) -> ResearchMarketLiquidityExitCostDecayReport:
    if type(config) is not ResearchMarketLiquidityExitCostDecayConfig:
        raise ValueError("config must be a ResearchMarketLiquidityExitCostDecayConfig")
    _require_hard_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    items = _normalize_observations(observations)
    for item in items:
        if item.observed_at > generated_at_utc:
            raise ValueError("observed_at must not be after generated_at")
    rows_without_refs = tuple(
        _row_from_observation(item, config=config, generated_at=generated_at_utc)
        for item in items
    )
    sorted_rows = tuple(
        sorted(
            rows_without_refs,
            key=lambda row: (
                _status_sort_value(row.status),
                row.liquidity_exit_cost_decay_score,
                -row.total_exit_cost_rate,
                row.internal_liquidity_ref_digest,
                row.observed_at.isoformat(),
            ),
        ),
    )
    rows = tuple(
        _replace_row_ref(row, public_row_ref=f"liquidity_exit_cost_decay_row_{index:03d}")
        for index, row in enumerate(sorted_rows, start=1)
    )
    reason_codes = _summary_reason_codes(rows)
    return ResearchMarketLiquidityExitCostDecayReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        observation_count=_decimal_count(len(rows)),
        pass_count=_decimal_count(_status_count(rows, STATUS_PASS)),
        watch_count=_decimal_count(_status_count(rows, STATUS_WATCH)),
        block_count=_decimal_count(_status_count(rows, STATUS_BLOCK)),
        average_total_exit_cost_rate=_average_row_value(rows, "total_exit_cost_rate"),
        average_liquidity_decay_ratio=_average_row_value(rows, "liquidity_decay_ratio"),
        average_liquidity_exit_cost_decay_score=_average_row_value(
            rows,
            "liquidity_exit_cost_decay_score",
        ),
        max_quote_age_seconds=_maximum_row_value(rows, "quote_age_seconds"),
        max_total_exit_cost_rate=_maximum_row_value(rows, "total_exit_cost_rate"),
        max_liquidity_decay_ratio=_maximum_row_value(rows, "liquidity_decay_ratio"),
        min_exit_depth_ratio=_minimum_row_value(rows, "exit_depth_ratio"),
        status=_summary_status(rows),
        rows=rows,
        reason_code_counts=_reason_code_counts(rows, reason_codes),
        reason_codes=reason_codes,
    )


def research_market_liquidity_exit_cost_decay_report_payload(
    report: ResearchMarketLiquidityExitCostDecayReport | Mapping[str, object],
) -> dict[str, Any]:
    if type(report) is ResearchMarketLiquidityExitCostDecayReport:
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
        "report must be a ResearchMarketLiquidityExitCostDecayReport or payload dict",
    )


def research_market_liquidity_exit_cost_decay_report_digest(
    report: ResearchMarketLiquidityExitCostDecayReport,
) -> str:
    if type(report) is not ResearchMarketLiquidityExitCostDecayReport:
        raise ValueError("report must be a ResearchMarketLiquidityExitCostDecayReport")
    _require_hard_flags("report", report)
    expected_digest = _report_validation_digest(report)
    if report.derived_validation_digest != expected_digest:
        raise ValueError("derived_validation_digest must match report fields")
    return expected_digest


def _row_from_observation(
    observation: ResearchMarketLiquidityExitCostDecayObservation,
    *,
    config: ResearchMarketLiquidityExitCostDecayConfig,
    generated_at: datetime,
) -> ResearchMarketLiquidityExitCostDecayRow:
    quote_age_seconds = _age_seconds(generated_at, observation.observed_at)
    total_exit_cost_rate = _quantize(
        observation.exit_fee_rate
        + observation.exit_spread_rate
        + observation.exit_slippage_rate,
    )
    exit_depth_ratio = _ratio(observation.current_exit_depth, observation.baseline_exit_depth)
    liquidity_decay_ratio = _quantize(ONE - exit_depth_ratio)
    exit_cost_score = _inverse_ratio_score(
        total_exit_cost_rate,
        config.max_watch_exit_cost_rate,
    )
    liquidity_decay_score = _inverse_ratio_score(
        liquidity_decay_ratio,
        config.max_watch_liquidity_decay_ratio,
    )
    quote_freshness_score = _inverse_ratio_score(
        quote_age_seconds,
        config.max_watch_quote_age_seconds,
    )
    exit_depth_score = _capped_ratio_score(
        exit_depth_ratio,
        config.min_pass_exit_depth_ratio,
    )
    liquidity_exit_cost_decay_score = _liquidity_exit_cost_decay_score(
        exit_cost_score=exit_cost_score,
        liquidity_decay_score=liquidity_decay_score,
        quote_freshness_score=quote_freshness_score,
        exit_depth_score=exit_depth_score,
        config=config,
    )
    status = _row_status(
        total_exit_cost_rate=total_exit_cost_rate,
        liquidity_decay_ratio=liquidity_decay_ratio,
        quote_age_seconds=quote_age_seconds,
        exit_depth_ratio=exit_depth_ratio,
        liquidity_exit_cost_decay_score=liquidity_exit_cost_decay_score,
        config=config,
    )
    return ResearchMarketLiquidityExitCostDecayRow(
        public_row_ref="liquidity_exit_cost_decay_row_pending",
        internal_liquidity_ref_digest=_private_reference_digest(
            observation.internal_liquidity_ref,
        ),
        observed_at=observation.observed_at,
        quote_age_seconds=quote_age_seconds,
        exit_fee_rate=observation.exit_fee_rate,
        exit_spread_rate=observation.exit_spread_rate,
        exit_slippage_rate=observation.exit_slippage_rate,
        total_exit_cost_rate=total_exit_cost_rate,
        baseline_exit_depth=observation.baseline_exit_depth,
        current_exit_depth=observation.current_exit_depth,
        exit_depth_ratio=exit_depth_ratio,
        liquidity_decay_ratio=liquidity_decay_ratio,
        exit_cost_score=exit_cost_score,
        liquidity_decay_score=liquidity_decay_score,
        quote_freshness_score=quote_freshness_score,
        exit_depth_score=exit_depth_score,
        liquidity_exit_cost_decay_score=liquidity_exit_cost_decay_score,
        status=status,
        reason_codes=_row_reason_codes(
            total_exit_cost_rate=total_exit_cost_rate,
            liquidity_decay_ratio=liquidity_decay_ratio,
            quote_age_seconds=quote_age_seconds,
            exit_depth_ratio=exit_depth_ratio,
            status=status,
            input_reason_codes=observation.reason_codes,
            config=config,
        ),
    )


def _replace_row_ref(
    row: ResearchMarketLiquidityExitCostDecayRow,
    *,
    public_row_ref: str,
) -> ResearchMarketLiquidityExitCostDecayRow:
    return ResearchMarketLiquidityExitCostDecayRow(
        public_row_ref=public_row_ref,
        internal_liquidity_ref_digest=row.internal_liquidity_ref_digest,
        observed_at=row.observed_at,
        quote_age_seconds=row.quote_age_seconds,
        exit_fee_rate=row.exit_fee_rate,
        exit_spread_rate=row.exit_spread_rate,
        exit_slippage_rate=row.exit_slippage_rate,
        total_exit_cost_rate=row.total_exit_cost_rate,
        baseline_exit_depth=row.baseline_exit_depth,
        current_exit_depth=row.current_exit_depth,
        exit_depth_ratio=row.exit_depth_ratio,
        liquidity_decay_ratio=row.liquidity_decay_ratio,
        exit_cost_score=row.exit_cost_score,
        liquidity_decay_score=row.liquidity_decay_score,
        quote_freshness_score=row.quote_freshness_score,
        exit_depth_score=row.exit_depth_score,
        liquidity_exit_cost_decay_score=row.liquidity_exit_cost_decay_score,
        status=row.status,
        reason_codes=row.reason_codes,
    )


def _liquidity_exit_cost_decay_score(
    *,
    exit_cost_score: Decimal,
    liquidity_decay_score: Decimal,
    quote_freshness_score: Decimal,
    exit_depth_score: Decimal,
    config: ResearchMarketLiquidityExitCostDecayConfig,
) -> Decimal:
    return _quantize(
        exit_cost_score * config.exit_cost_pressure_weight
        + liquidity_decay_score * config.liquidity_decay_weight
        + quote_freshness_score * config.quote_freshness_weight
        + exit_depth_score * config.exit_depth_weight,
    )


def _row_status(
    *,
    total_exit_cost_rate: Decimal,
    liquidity_decay_ratio: Decimal,
    quote_age_seconds: Decimal,
    exit_depth_ratio: Decimal,
    liquidity_exit_cost_decay_score: Decimal,
    config: ResearchMarketLiquidityExitCostDecayConfig,
) -> str:
    if (
        liquidity_exit_cost_decay_score < config.watch_liquidity_exit_cost_decay_score
        or total_exit_cost_rate >= config.max_watch_exit_cost_rate
        or liquidity_decay_ratio >= config.max_watch_liquidity_decay_ratio
        or quote_age_seconds >= config.max_watch_quote_age_seconds
        or exit_depth_ratio <= config.min_watch_exit_depth_ratio
    ):
        return STATUS_BLOCK
    if (
        liquidity_exit_cost_decay_score < config.pass_liquidity_exit_cost_decay_score
        or total_exit_cost_rate >= config.max_pass_exit_cost_rate
        or liquidity_decay_ratio >= config.max_pass_liquidity_decay_ratio
        or quote_age_seconds >= config.max_pass_quote_age_seconds
        or exit_depth_ratio <= config.min_pass_exit_depth_ratio
    ):
        return STATUS_WATCH
    return STATUS_PASS


def _row_reason_codes(
    *,
    total_exit_cost_rate: Decimal,
    liquidity_decay_ratio: Decimal,
    quote_age_seconds: Decimal,
    exit_depth_ratio: Decimal,
    status: str,
    input_reason_codes: tuple[str, ...],
    config: ResearchMarketLiquidityExitCostDecayConfig,
) -> tuple[str, ...]:
    reason_codes: set[str] = {f"liquidity_exit_cost_decay_{status}"}
    reason_codes.add(
        _upper_threshold_reason(
            "exit_cost_pressure",
            total_exit_cost_rate,
            config.max_pass_exit_cost_rate,
            config.max_watch_exit_cost_rate,
        ),
    )
    reason_codes.add(
        _upper_threshold_reason(
            "liquidity_decay",
            liquidity_decay_ratio,
            config.max_pass_liquidity_decay_ratio,
            config.max_watch_liquidity_decay_ratio,
        ),
    )
    reason_codes.add(
        _upper_threshold_reason(
            "quote_freshness",
            quote_age_seconds,
            config.max_pass_quote_age_seconds,
            config.max_watch_quote_age_seconds,
        ),
    )
    reason_codes.add(
        _lower_threshold_reason(
            "exit_depth",
            exit_depth_ratio,
            config.min_pass_exit_depth_ratio,
            config.min_watch_exit_depth_ratio,
        ),
    )
    for reason_code in input_reason_codes:
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
    if value <= watch_threshold:
        return f"{prefix}_block"
    if value <= pass_threshold:
        return f"{prefix}_watch"
    return f"{prefix}_pass"


def _normalize_observations(
    observations: Iterable[object],
) -> tuple[ResearchMarketLiquidityExitCostDecayObservation, ...]:
    if isinstance(observations, (str, bytes)):
        raise ValueError("observations must be an iterable of observation records")
    normalized: list[ResearchMarketLiquidityExitCostDecayObservation] = []
    seen_refs: set[str] = set()
    for item in observations:
        if type(item) is not ResearchMarketLiquidityExitCostDecayObservation:
            raise ValueError(
                "observations must contain "
                "ResearchMarketLiquidityExitCostDecayObservation",
            )
        _require_hard_flags("observation", item)
        if item.internal_liquidity_ref in seen_refs:
            raise ValueError("internal_liquidity_ref values must be unique")
        seen_refs.add(item.internal_liquidity_ref)
        normalized.append(item)
    return tuple(normalized)


def _normalize_rows(
    rows: tuple[ResearchMarketLiquidityExitCostDecayRow, ...],
) -> tuple[ResearchMarketLiquidityExitCostDecayRow, ...]:
    if type(rows) is not tuple:
        raise ValueError("rows must be a tuple")
    for row in rows:
        if type(row) is not ResearchMarketLiquidityExitCostDecayRow:
            raise ValueError(
                "rows must contain ResearchMarketLiquidityExitCostDecayRow values",
            )
        _require_hard_flags("row", row)
    expected_refs = tuple(
        f"liquidity_exit_cost_decay_row_{index:03d}"
        for index in range(1, len(rows) + 1)
    )
    actual_refs = tuple(row.public_row_ref for row in rows)
    if rows and actual_refs != expected_refs:
        raise ValueError("rows must use sequential public_row_ref values")
    return rows


def _normalize_reason_code_counts(
    rows: tuple[ResearchMarketLiquidityExitCostDecayReasonCodeCount, ...],
) -> tuple[ResearchMarketLiquidityExitCostDecayReasonCodeCount, ...]:
    if type(rows) is not tuple:
        raise ValueError("reason_code_counts must be a tuple")
    for row in rows:
        if type(row) is not ResearchMarketLiquidityExitCostDecayReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "ResearchMarketLiquidityExitCostDecayReasonCodeCount values",
            )
        _require_hard_flags("reason_code_count", row)
    sorted_rows = tuple(sorted(rows, key=lambda row: row.reason_code))
    if rows != sorted_rows:
        raise ValueError("reason_code_counts must be sorted by reason_code")
    return rows


def _reason_code_counts(
    rows: tuple[ResearchMarketLiquidityExitCostDecayRow, ...],
    reason_codes: tuple[str, ...],
) -> tuple[ResearchMarketLiquidityExitCostDecayReasonCodeCount, ...]:
    if not rows:
        return (
            ResearchMarketLiquidityExitCostDecayReasonCodeCount(
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
        ResearchMarketLiquidityExitCostDecayReasonCodeCount(
            reason_code=reason_code,
            count=_decimal_count(count),
            row_ratio=_quantize(_decimal_count(count) / total),
        )
        for reason_code, count in sorted(counts.items(), key=lambda item: item[0])
    )


def _summary_reason_codes(
    rows: tuple[ResearchMarketLiquidityExitCostDecayRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return (MISSING_INPUTS_REASON,)
    if all(row.status == STATUS_PASS for row in rows):
        return ("liquidity_exit_cost_decay_pass",)
    return tuple(sorted({reason for row in rows for reason in row.reason_codes}))


def _summary_status(rows: tuple[ResearchMarketLiquidityExitCostDecayRow, ...]) -> str:
    if not rows or any(row.status == STATUS_BLOCK for row in rows):
        return STATUS_BLOCK
    if any(row.status == STATUS_WATCH for row in rows):
        return STATUS_WATCH
    return STATUS_PASS


def _status_count(
    rows: tuple[ResearchMarketLiquidityExitCostDecayRow, ...],
    status: str,
) -> int:
    return sum(1 for row in rows if row.status == status)


def _status_sort_value(status: str) -> int:
    if status == STATUS_BLOCK:
        return 0
    if status == STATUS_WATCH:
        return 1
    return 2


def _maximum_row_value(
    rows: tuple[ResearchMarketLiquidityExitCostDecayRow, ...],
    field_name: str,
) -> Decimal:
    if not rows:
        return ZERO
    return max(getattr(row, field_name) for row in rows)


def _minimum_row_value(
    rows: tuple[ResearchMarketLiquidityExitCostDecayRow, ...],
    field_name: str,
) -> Decimal:
    if not rows:
        return ZERO
    return min(getattr(row, field_name) for row in rows)


def _average_row_value(
    rows: tuple[ResearchMarketLiquidityExitCostDecayRow, ...],
    field_name: str,
) -> Decimal | None:
    if not rows:
        return None
    with localcontext(DECIMAL_CONTEXT):
        return _quantize(sum((getattr(row, field_name) for row in rows), ZERO) / len(rows))


def _validate_row(row: ResearchMarketLiquidityExitCostDecayRow) -> None:
    if row.baseline_exit_depth <= ZERO:
        raise ValueError("baseline_exit_depth must be positive")
    if row.current_exit_depth > row.baseline_exit_depth:
        raise ValueError("current_exit_depth must not exceed baseline_exit_depth")
    expected_total = _quantize(
        row.exit_fee_rate + row.exit_spread_rate + row.exit_slippage_rate,
    )
    if row.total_exit_cost_rate != expected_total:
        raise ValueError("total_exit_cost_rate must match exit cost fields")
    expected_exit_depth_ratio = _ratio(row.current_exit_depth, row.baseline_exit_depth)
    if row.exit_depth_ratio != expected_exit_depth_ratio:
        raise ValueError("exit_depth_ratio must match depth fields")
    if row.liquidity_decay_ratio != _quantize(ONE - row.exit_depth_ratio):
        raise ValueError("liquidity_decay_ratio must match depth fields")
    if f"liquidity_exit_cost_decay_{row.status}" not in row.reason_codes:
        raise ValueError("status must match reason_codes")


def _validate_report(report: ResearchMarketLiquidityExitCostDecayReport) -> None:
    if report.observation_count != _decimal_count(len(report.rows)):
        raise ValueError("observation_count must match rows")
    if report.pass_count != _decimal_count(_status_count(report.rows, STATUS_PASS)):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _decimal_count(_status_count(report.rows, STATUS_WATCH)):
        raise ValueError("watch_count must match rows")
    if report.block_count != _decimal_count(_status_count(report.rows, STATUS_BLOCK)):
        raise ValueError("block_count must match rows")
    if report.average_total_exit_cost_rate != _average_row_value(
        report.rows,
        "total_exit_cost_rate",
    ):
        raise ValueError("average_total_exit_cost_rate must match rows")
    if report.average_liquidity_decay_ratio != _average_row_value(
        report.rows,
        "liquidity_decay_ratio",
    ):
        raise ValueError("average_liquidity_decay_ratio must match rows")
    if report.average_liquidity_exit_cost_decay_score != _average_row_value(
        report.rows,
        "liquidity_exit_cost_decay_score",
    ):
        raise ValueError("average_liquidity_exit_cost_decay_score must match rows")
    if report.max_quote_age_seconds != _maximum_row_value(report.rows, "quote_age_seconds"):
        raise ValueError("max_quote_age_seconds must match rows")
    if report.max_total_exit_cost_rate != _maximum_row_value(
        report.rows,
        "total_exit_cost_rate",
    ):
        raise ValueError("max_total_exit_cost_rate must match rows")
    if report.max_liquidity_decay_ratio != _maximum_row_value(
        report.rows,
        "liquidity_decay_ratio",
    ):
        raise ValueError("max_liquidity_decay_ratio must match rows")
    if report.min_exit_depth_ratio != _minimum_row_value(report.rows, "exit_depth_ratio"):
        raise ValueError("min_exit_depth_ratio must match rows")
    if report.status != _summary_status(report.rows):
        raise ValueError("status must match rows")
    if report.reason_codes != _summary_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")
    if report.reason_code_counts != _reason_code_counts(report.rows, report.reason_codes):
        raise ValueError("reason_code_counts must match rows")


def _row_validation_digest(row: ResearchMarketLiquidityExitCostDecayRow) -> str:
    values = _row_payload(row, include_digest=False)
    return _payload_digest(values)


def _report_validation_digest(report: ResearchMarketLiquidityExitCostDecayReport) -> str:
    values = _report_payload(report, include_digest=False)
    return _payload_digest(values)


def _private_reference_digest(value: str) -> str:
    return sha256(value.encode("utf-8")).hexdigest()


def _payload_digest(payload: Mapping[str, Any]) -> str:
    _reject_unsafe_public_payload(payload)
    encoded = json.dumps(
        payload,
        allow_nan=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    return sha256(encoded.encode("utf-8")).hexdigest()


def _report_payload(
    report: ResearchMarketLiquidityExitCostDecayReport,
    *,
    include_digest: bool = True,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "generated_at": report.generated_at.isoformat(),
        "config_version": report.config_version,
        "observation_count": _decimal_string(report.observation_count),
        "pass_count": _decimal_string(report.pass_count),
        "watch_count": _decimal_string(report.watch_count),
        "block_count": _decimal_string(report.block_count),
        "average_total_exit_cost_rate": _optional_decimal_string(
            report.average_total_exit_cost_rate,
        ),
        "average_liquidity_decay_ratio": _optional_decimal_string(
            report.average_liquidity_decay_ratio,
        ),
        "average_liquidity_exit_cost_decay_score": _optional_decimal_string(
            report.average_liquidity_exit_cost_decay_score,
        ),
        "max_quote_age_seconds": _decimal_string(report.max_quote_age_seconds),
        "max_total_exit_cost_rate": _decimal_string(report.max_total_exit_cost_rate),
        "max_liquidity_decay_ratio": _decimal_string(report.max_liquidity_decay_ratio),
        "min_exit_depth_ratio": _decimal_string(report.min_exit_depth_ratio),
        "status": report.status,
        "rows": [_row_payload(row) for row in report.rows],
        "reason_code_counts": [
            _reason_code_count_payload(row) for row in report.reason_code_counts
        ],
        "reason_codes": list(report.reason_codes),
        "paper_only": report.paper_only,
        "report_only": report.report_only,
        "readonly": report.readonly,
    }
    if include_digest:
        payload["derived_validation_digest"] = report.derived_validation_digest
    return payload


def _row_payload(
    row: ResearchMarketLiquidityExitCostDecayRow,
    *,
    include_digest: bool = True,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "public_row_ref": row.public_row_ref,
        "internal_liquidity_ref_digest": row.internal_liquidity_ref_digest,
        "observed_at": row.observed_at.isoformat(),
        "quote_age_seconds": _decimal_string(row.quote_age_seconds),
        "exit_fee_rate": _decimal_string(row.exit_fee_rate),
        "exit_spread_rate": _decimal_string(row.exit_spread_rate),
        "exit_slippage_rate": _decimal_string(row.exit_slippage_rate),
        "total_exit_cost_rate": _decimal_string(row.total_exit_cost_rate),
        "baseline_exit_depth": _decimal_string(row.baseline_exit_depth),
        "current_exit_depth": _decimal_string(row.current_exit_depth),
        "exit_depth_ratio": _decimal_string(row.exit_depth_ratio),
        "liquidity_decay_ratio": _decimal_string(row.liquidity_decay_ratio),
        "exit_cost_score": _decimal_string(row.exit_cost_score),
        "liquidity_decay_score": _decimal_string(row.liquidity_decay_score),
        "quote_freshness_score": _decimal_string(row.quote_freshness_score),
        "exit_depth_score": _decimal_string(row.exit_depth_score),
        "liquidity_exit_cost_decay_score": _decimal_string(
            row.liquidity_exit_cost_decay_score,
        ),
        "status": row.status,
        "reason_codes": list(row.reason_codes),
        "paper_only": row.paper_only,
        "report_only": row.report_only,
        "readonly": row.readonly,
    }
    if include_digest:
        payload["row_validation_digest"] = row.row_validation_digest
    return payload


def _reason_code_count_payload(
    row: ResearchMarketLiquidityExitCostDecayReasonCodeCount,
) -> dict[str, Any]:
    return {
        "reason_code": row.reason_code,
        "count": _decimal_string(row.count),
        "row_ratio": _decimal_string(row.row_ratio),
        "paper_only": row.paper_only,
        "report_only": row.report_only,
        "readonly": row.readonly,
    }


def _validate_public_payload(payload: Mapping[str, object]) -> None:
    if type(payload) is not dict:
        raise ValueError("report payload must be a dict")
    _reject_unsafe_public_payload(payload)
    _validate_public_payload_schema(payload)
    _require_no_public_numeric_literals(payload)
    for field_name in PHASE_FLAG_FIELDS:
        if payload.get(field_name) is not True:
            raise ValueError(f"{field_name} must be True")
    digest = payload.get("derived_validation_digest")
    if type(digest) is not str or not HEX_DIGEST_RE.fullmatch(digest):
        raise ValueError("derived_validation_digest must be a sha256 hex digest")
    digest_payload = dict(payload)
    digest_payload.pop("derived_validation_digest")
    if _payload_digest(digest_payload) != digest:
        raise ValueError("derived_validation_digest must match report fields")


def _validate_public_payload_schema(payload: Mapping[str, object]) -> None:
    _require_exact_payload_keys("report", payload, REPORT_PAYLOAD_KEYS)
    _require_payload_phase_flags("report", payload)
    if type(payload.get("generated_at")) is not str:
        raise ValueError("public schema generated_at must be a string")
    if type(payload.get("config_version")) is not str:
        raise ValueError("public schema config_version must be a string")
    _require_status("status", payload.get("status"))
    _require_payload_decimal_strings("report", payload, REPORT_DECIMAL_STRING_FIELDS)
    _require_payload_optional_decimal_strings(
        "report",
        payload,
        REPORT_OPTIONAL_DECIMAL_STRING_FIELDS,
    )
    rows = payload.get("rows")
    if type(rows) is not list:
        raise ValueError("public schema rows must be a list")
    for row in rows:
        _validate_public_row_payload(row)
    reason_code_counts = payload.get("reason_code_counts")
    if type(reason_code_counts) is not list:
        raise ValueError("public schema reason_code_counts must be a list")
    for reason_code_count in reason_code_counts:
        _validate_public_reason_code_count_payload(reason_code_count)
    _require_payload_reason_code_list("report", payload.get("reason_codes"))


def _validate_public_row_payload(value: object) -> None:
    if type(value) is not dict:
        raise ValueError("public schema rows must contain dicts")
    _require_exact_payload_keys("row", value, ROW_PAYLOAD_KEYS)
    _require_payload_phase_flags("row", value)
    _require_public_label("public_row_ref", value.get("public_row_ref"))
    _require_hex_digest(
        "internal_liquidity_ref_digest",
        value.get("internal_liquidity_ref_digest"),
    )
    if type(value.get("observed_at")) is not str:
        raise ValueError("public schema observed_at must be a string")
    _require_payload_decimal_strings("row", value, ROW_DECIMAL_STRING_FIELDS)
    _require_status("status", value.get("status"))
    _require_payload_reason_code_list("row", value.get("reason_codes"))
    _require_hex_digest("row_validation_digest", value.get("row_validation_digest"))


def _validate_public_reason_code_count_payload(value: object) -> None:
    if type(value) is not dict:
        raise ValueError("public schema reason_code_counts must contain dicts")
    _require_exact_payload_keys(
        "reason_code_count",
        value,
        REASON_CODE_COUNT_PAYLOAD_KEYS,
    )
    _require_payload_phase_flags("reason_code_count", value)
    _normalize_reason_code(value.get("reason_code"))
    _require_payload_decimal_string("count", value.get("count"))
    _require_payload_decimal_string("row_ratio", value.get("row_ratio"))


def _require_exact_payload_keys(
    label: str,
    payload: Mapping[str, object],
    expected_keys: frozenset[str],
) -> None:
    if set(payload) != expected_keys:
        raise ValueError(f"public schema {label} keys must match expected fields")


def _require_payload_phase_flags(label: str, payload: Mapping[str, object]) -> None:
    for field_name in PHASE_FLAG_FIELDS:
        if payload.get(field_name) is not True:
            raise ValueError(f"{label} {field_name} must be True")


def _require_payload_decimal_strings(
    label: str,
    payload: Mapping[str, object],
    field_names: frozenset[str],
) -> None:
    for field_name in field_names:
        try:
            _require_payload_decimal_string(field_name, payload[field_name])
        except KeyError as exc:
            raise ValueError(f"public schema {label} keys must match expected fields") from exc


def _require_payload_optional_decimal_strings(
    label: str,
    payload: Mapping[str, object],
    field_names: frozenset[str],
) -> None:
    for field_name in field_names:
        try:
            value = payload[field_name]
        except KeyError as exc:
            raise ValueError(f"public schema {label} keys must match expected fields") from exc
        if value is not None:
            _require_payload_decimal_string(field_name, value)


def _require_payload_decimal_string(field_name: str, value: object) -> str:
    if type(value) is not str or not DECIMAL_STRING_RE.fullmatch(value):
        raise ValueError(f"public schema {field_name} must be a Decimal-derived string")
    return value


def _require_payload_reason_code_list(label: str, value: object) -> None:
    if type(value) is not list:
        raise ValueError(f"public schema {label} reason_codes must be a list")
    for reason_code in value:
        _normalize_reason_code(reason_code)


def _require_no_public_numeric_literals(value: object) -> None:
    if type(value) in (int, float, Decimal):
        raise ValueError("public numeric values must be Decimal-derived strings")
    if isinstance(value, Mapping):
        for item in value.values():
            _require_no_public_numeric_literals(item)
    elif isinstance(value, list):
        for item in value:
            _require_no_public_numeric_literals(item)


def _reject_unsafe_public_payload(value: object) -> None:
    if isinstance(value, Mapping):
        for key, item in value.items():
            _reject_unsafe_public_text(str(key))
            _reject_unsafe_public_payload(item)
        return
    if isinstance(value, list):
        for item in value:
            _reject_unsafe_public_payload(item)
        return
    if isinstance(value, str):
        _reject_unsafe_public_text(value)


def _reject_unsafe_public_text(value: str) -> None:
    lowered = value.lower()
    if any(fragment in lowered for fragment in UNSAFE_PUBLIC_FRAGMENTS):
        raise ValueError("unsafe public payload surface")


def _as_utc(field_name: str, value: datetime) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_exact_type(value: object, expected_type: type[object], label: str) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{label} must be exactly {expected_type.__name__}")


def _require_public_label(field_name: str, value: object) -> str:
    if type(value) is not str or not PUBLIC_LABEL_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a public label")
    return value


def _require_private_reference(field_name: str, value: object) -> str:
    if type(value) is not str or not PRIVATE_REF_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a non-empty private reference")
    return value


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    try:
        normalized = +value
    except InvalidOperation as exc:
        raise ValueError(f"{field_name} must be finite") from exc
    return _quantize(normalized)


def _require_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _require_positive_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _require_nonnegative_whole_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_nonnegative_decimal(field_name, value)
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{field_name} must be a whole count")
    return normalized


def _require_probability_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_nonnegative_decimal(field_name, value)
    if normalized > ONE:
        raise ValueError(f"{field_name} must be no greater than 1.000000")
    return normalized


def _require_optional_nonnegative_decimal(
    field_name: str,
    value: object,
) -> Decimal | None:
    if value is None:
        return None
    return _require_nonnegative_decimal(field_name, value)


def _require_status(field_name: str, value: object) -> str:
    if type(value) is not str or value not in MARKET_LIQUIDITY_EXIT_COST_DECAY_STATUSES:
        raise ValueError(f"{field_name} must be pass, watch, or block")
    return value


def _normalize_reason_codes(reason_codes: tuple[str, ...]) -> tuple[str, ...]:
    if type(reason_codes) is not tuple:
        raise ValueError("reason_codes must be a tuple")
    return tuple(sorted({_normalize_reason_code(reason_code) for reason_code in reason_codes}))


def _normalize_reason_code(value: object) -> str:
    if type(value) is not str or not REASON_CODE_RE.fullmatch(value):
        raise ValueError("reason_codes must contain reason code strings")
    _reject_unsafe_public_text(value)
    return value


def _require_hex_digest(field_name: str, value: object) -> str:
    if type(value) is not str or not HEX_DIGEST_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a sha256 hex digest")
    return value


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in PHASE_FLAG_FIELDS:
        if getattr(value, field_name, None) is not True:
            raise ValueError(f"{label} {field_name} must be True")


def _inverse_ratio_score(value: Decimal, zero_at: Decimal) -> Decimal:
    if zero_at <= ZERO:
        raise ValueError("zero_at must be positive")
    return _quantize(max(ZERO, ONE - (value / zero_at)))


def _capped_ratio_score(value: Decimal, full_at: Decimal) -> Decimal:
    if full_at <= ZERO:
        raise ValueError("full_at must be positive")
    return _quantize(min(ONE, value / full_at))


def _age_seconds(generated_at: datetime, observed_at: datetime) -> Decimal:
    delta = generated_at - observed_at
    return _quantize(
        Decimal(delta.days * 86_400)
        + Decimal(delta.seconds)
        + (Decimal(delta.microseconds) / Decimal("1000000")),
    )


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator <= ZERO:
        raise ValueError("denominator must be positive")
    with localcontext(DECIMAL_CONTEXT):
        return _quantize(numerator / denominator)


def _decimal_count(value: int) -> Decimal:
    return _quantize(Decimal(value))


def _decimal_string(value: Decimal) -> str:
    return format(_quantize(value), "f")


def _optional_decimal_string(value: Decimal | None) -> str | None:
    if value is None:
        return None
    return _decimal_string(value)


def _quantize(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(QUANTUM)
