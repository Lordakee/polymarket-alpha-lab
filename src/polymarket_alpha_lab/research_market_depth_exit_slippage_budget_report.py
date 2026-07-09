"""Pure report-only exit slippage budget report for depth research review."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
import json
import re
from typing import Any


__all__ = (
    "MARKET_DEPTH_EXIT_SLIPPAGE_BUDGET_STATUSES",
    "DEFAULT_RESEARCH_MARKET_DEPTH_EXIT_SLIPPAGE_BUDGET_REPORT_CONFIG_VERSION",
    "ResearchMarketDepthExitSlippageBudgetConfig",
    "ResearchMarketDepthExitSlippageBudgetObservation",
    "ResearchMarketDepthExitSlippageBudgetReport",
    "ResearchMarketDepthExitSlippageBudgetRow",
    "build_research_market_depth_exit_slippage_budget_report",
    "research_market_depth_exit_slippage_budget_report_digest",
    "research_market_depth_exit_slippage_budget_report_payload",
)


DEFAULT_RESEARCH_MARKET_DEPTH_EXIT_SLIPPAGE_BUDGET_REPORT_CONFIG_VERSION = (
    "research-market-depth-exit-slippage-budget-report-v0"
)

MARKET_DEPTH_EXIT_SLIPPAGE_BUDGET_STATUSES = ("pass", "watch", "block")
STATUS_PASS = "pass"
STATUS_WATCH = "watch"
STATUS_BLOCK = "block"
MISSING_INPUTS_REASON = "missing_depth_exit_slippage_budget_observations"
PASS_REASON = "exit_slippage_budget_pass"
QUANTUM = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
PUBLIC_LABEL_RE = re.compile(r"^[a-z0-9][a-z0-9_.-]{0,127}$")
REASON_CODE_RE = re.compile(r"^[a-z0-9][a-z0-9_]{0,127}$")
HEX_DIGEST_RE = re.compile(r"^[0-9a-f]{64}$")
PHASE_FLAG_FIELDS = ("paper_only", "report_only", "readonly")
REASON_PRIORITY = (
    "depth_coverage_block",
    "depth_decay_block",
    "exit_window_block",
    "fee_drag_block",
    "slippage_budget_block",
    "spread_block",
    "depth_coverage_watch",
    "depth_decay_watch",
    "exit_window_watch",
    "fee_drag_watch",
    "slippage_budget_watch",
    "spread_watch",
    PASS_REASON,
    MISSING_INPUTS_REASON,
)


def _join_parts(*parts: str) -> str:
    return "".join(parts)


UNSAFE_PUBLIC_FRAGMENTS = (
    _join_parts("ra", "w"),
    _join_parts("can", "didate", "_", "id"),
    _join_parts("condition", "_", "id"),
    _join_parts("ma", "rket", "_", "id"),
    _join_parts("ma", "rket", "_", "sl", "ug"),
    _join_parts("sl", "ug"),
    _join_parts("ques", "tion"),
    _join_parts("sour", "ce", "_", "url"),
    _join_parts("sour", "ce", "_", "text"),
    _join_parts("d", "sn"),
    _join_parts("tab", "le", "_", "name"),
    _join_parts("tab", "le"),
    _join_parts("to", "ken"),
    _join_parts("wal", "let"),
    _join_parts("or", "der"),
    _join_parts("tra", "de"),
    _join_parts("li", "ve"),
    _join_parts("reco", "mmend"),
    _join_parts("siz", "ing"),
    _join_parts("au", "th"),
    "://",
)


class _FinalDataclass:
    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        for base in cls.__bases__:
            if base is not _FinalDataclass and issubclass(base, _FinalDataclass):
                raise TypeError(f"{base.__name__} may not be subclassed")


@dataclass(frozen=True)
class ResearchMarketDepthExitSlippageBudgetConfig(_FinalDataclass):
    config_version: str = (
        DEFAULT_RESEARCH_MARKET_DEPTH_EXIT_SLIPPAGE_BUDGET_REPORT_CONFIG_VERSION
    )
    minimum_depth_coverage_ratio: Decimal = Decimal("1.000000")
    depth_coverage_watch_threshold: Decimal = Decimal("0.750000")
    depth_coverage_block_threshold: Decimal = Decimal("0.350000")
    slippage_budget_utilization_watch_threshold: Decimal = Decimal("0.750000")
    slippage_budget_utilization_block_threshold: Decimal = Decimal("1.250000")
    spread_watch_threshold: Decimal = Decimal("0.030000")
    spread_block_threshold: Decimal = Decimal("0.070000")
    depth_decay_watch_threshold: Decimal = Decimal("0.200000")
    depth_decay_block_threshold: Decimal = Decimal("0.600000")
    exit_window_watch_hours: Decimal = Decimal("24.000000")
    exit_window_block_hours: Decimal = Decimal("72.000000")
    fee_drag_watch_threshold: Decimal = Decimal("0.015000")
    fee_drag_block_threshold: Decimal = Decimal("0.040000")
    watch_exit_slippage_budget_risk_score: Decimal = Decimal("0.350000")
    block_exit_slippage_budget_risk_score: Decimal = Decimal("0.700000")
    depth_coverage_weight: Decimal = Decimal("0.300000")
    slippage_budget_weight: Decimal = Decimal("0.300000")
    spread_weight: Decimal = Decimal("0.100000")
    depth_decay_weight: Decimal = Decimal("0.100000")
    exit_window_weight: Decimal = Decimal("0.100000")
    fee_drag_weight: Decimal = Decimal("0.100000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchMarketDepthExitSlippageBudgetConfig, "config")
        _require_public_label("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_MARKET_DEPTH_EXIT_SLIPPAGE_BUDGET_REPORT_CONFIG_VERSION
        ):
            raise ValueError("config_version must match supported value")
        for field_name in (
            "minimum_depth_coverage_ratio",
            "slippage_budget_utilization_watch_threshold",
            "slippage_budget_utilization_block_threshold",
            "spread_watch_threshold",
            "spread_block_threshold",
            "depth_decay_watch_threshold",
            "depth_decay_block_threshold",
            "exit_window_watch_hours",
            "exit_window_block_hours",
            "fee_drag_watch_threshold",
            "fee_drag_block_threshold",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_positive_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "depth_coverage_watch_threshold",
            "depth_coverage_block_threshold",
            "watch_exit_slippage_budget_risk_score",
            "block_exit_slippage_budget_risk_score",
            "depth_coverage_weight",
            "slippage_budget_weight",
            "spread_weight",
            "depth_decay_weight",
            "exit_window_weight",
            "fee_drag_weight",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        if self.depth_coverage_block_threshold > self.depth_coverage_watch_threshold:
            raise ValueError(
                "depth_coverage_block_threshold must not exceed watch threshold",
            )
        _require_below(
            "slippage_budget_utilization_watch_threshold",
            self.slippage_budget_utilization_watch_threshold,
            self.slippage_budget_utilization_block_threshold,
        )
        _require_below("spread_watch_threshold", self.spread_watch_threshold, self.spread_block_threshold)
        _require_below(
            "depth_decay_watch_threshold",
            self.depth_decay_watch_threshold,
            self.depth_decay_block_threshold,
        )
        _require_below(
            "exit_window_watch_hours",
            self.exit_window_watch_hours,
            self.exit_window_block_hours,
        )
        _require_below(
            "fee_drag_watch_threshold",
            self.fee_drag_watch_threshold,
            self.fee_drag_block_threshold,
        )
        _require_below(
            "watch_exit_slippage_budget_risk_score",
            self.watch_exit_slippage_budget_risk_score,
            self.block_exit_slippage_budget_risk_score,
        )
        if _quantize(
            self.depth_coverage_weight
            + self.slippage_budget_weight
            + self.spread_weight
            + self.depth_decay_weight
            + self.exit_window_weight
            + self.fee_drag_weight,
        ) != ONE:
            raise ValueError("weights must sum to 1.000000")
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class ResearchMarketDepthExitSlippageBudgetObservation(_FinalDataclass):
    internal_observation_ref: str
    observed_at: datetime
    planned_exit_notional: Decimal
    available_exit_depth: Decimal
    estimated_exit_slippage_rate: Decimal
    slippage_budget_rate: Decimal
    bid_ask_spread_rate: Decimal
    depth_decay_rate: Decimal
    exit_window_hours: Decimal
    fee_drag_rate: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchMarketDepthExitSlippageBudgetObservation,
            "observation",
        )
        _require_private_reference("internal_observation_ref", self.internal_observation_ref)
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        object.__setattr__(
            self,
            "planned_exit_notional",
            _require_positive_decimal("planned_exit_notional", self.planned_exit_notional),
        )
        for field_name in (
            "available_exit_depth",
            "estimated_exit_slippage_rate",
            "bid_ask_spread_rate",
            "depth_decay_rate",
            "exit_window_hours",
            "fee_drag_rate",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "slippage_budget_rate",
            _require_positive_decimal("slippage_budget_rate", self.slippage_budget_rate),
        )
        _require_hard_flags("observation", self)


@dataclass(frozen=True)
class ResearchMarketDepthExitSlippageBudgetRow(_FinalDataclass):
    public_row_ref: str
    internal_observation_ref_digest: str
    observed_at: datetime
    planned_exit_notional: Decimal
    available_exit_depth: Decimal
    estimated_exit_slippage_rate: Decimal
    slippage_budget_rate: Decimal
    bid_ask_spread_rate: Decimal
    depth_decay_rate: Decimal
    exit_window_hours: Decimal
    fee_drag_rate: Decimal
    depth_coverage_ratio: Decimal
    slippage_budget_utilization_ratio: Decimal
    depth_coverage_risk_score: Decimal
    slippage_budget_risk_score: Decimal
    spread_risk_score: Decimal
    depth_decay_risk_score: Decimal
    exit_window_risk_score: Decimal
    fee_drag_risk_score: Decimal
    exit_slippage_budget_risk_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    row_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchMarketDepthExitSlippageBudgetRow, "row")
        _require_public_label("public_row_ref", self.public_row_ref)
        _require_hex_digest(
            "internal_observation_ref_digest",
            self.internal_observation_ref_digest,
        )
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        object.__setattr__(
            self,
            "planned_exit_notional",
            _require_positive_decimal("planned_exit_notional", self.planned_exit_notional),
        )
        for field_name in (
            "available_exit_depth",
            "estimated_exit_slippage_rate",
            "bid_ask_spread_rate",
            "depth_decay_rate",
            "exit_window_hours",
            "fee_drag_rate",
            "depth_coverage_ratio",
            "slippage_budget_utilization_ratio",
            "depth_coverage_risk_score",
            "slippage_budget_risk_score",
            "spread_risk_score",
            "depth_decay_risk_score",
            "exit_window_risk_score",
            "fee_drag_risk_score",
            "exit_slippage_budget_risk_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "slippage_budget_rate",
            _require_positive_decimal("slippage_budget_rate", self.slippage_budget_rate),
        )
        _require_status("status", self.status)
        object.__setattr__(self, "reason_codes", _normalize_reason_codes(self.reason_codes))
        _require_hard_flags("row", self)
        expected_digest = _row_validation_digest(self)
        if self.row_validation_digest:
            _require_hex_digest("row_validation_digest", self.row_validation_digest)
            if self.row_validation_digest != expected_digest:
                raise ValueError("row_validation_digest must match row fields")
        else:
            object.__setattr__(self, "row_validation_digest", expected_digest)


@dataclass(frozen=True)
class ResearchMarketDepthExitSlippageBudgetReport(_FinalDataclass):
    generated_at: datetime
    config_version: str
    observation_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    min_depth_coverage_ratio: Decimal
    max_slippage_budget_utilization_ratio: Decimal
    max_exit_slippage_budget_risk_score: Decimal
    average_exit_slippage_budget_risk_score: Decimal | None
    status: str
    rows: tuple[ResearchMarketDepthExitSlippageBudgetRow, ...]
    reason_codes: tuple[str, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchMarketDepthExitSlippageBudgetReport, "report")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_label("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_MARKET_DEPTH_EXIT_SLIPPAGE_BUDGET_REPORT_CONFIG_VERSION
        ):
            raise ValueError("config_version must match supported value")
        for field_name in (
            "observation_count",
            "pass_count",
            "watch_count",
            "block_count",
            "min_depth_coverage_ratio",
            "max_slippage_budget_utilization_ratio",
            "max_exit_slippage_budget_risk_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "average_exit_slippage_budget_risk_score",
            _require_optional_nonnegative_decimal(
                "average_exit_slippage_budget_risk_score",
                self.average_exit_slippage_budget_risk_score,
            ),
        )
        _require_status("status", self.status)
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
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


def build_research_market_depth_exit_slippage_budget_report(
    observations: Iterable[object],
    *,
    config: ResearchMarketDepthExitSlippageBudgetConfig,
    generated_at: datetime,
) -> ResearchMarketDepthExitSlippageBudgetReport:
    if type(config) is not ResearchMarketDepthExitSlippageBudgetConfig:
        raise ValueError("config must be a ResearchMarketDepthExitSlippageBudgetConfig")
    _require_hard_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    items = _normalize_observations(observations)
    rows_without_refs = tuple(_row_from_observation(item, config=config) for item in items)
    sorted_rows = tuple(
        sorted(
            rows_without_refs,
            key=lambda row: (
                -row.exit_slippage_budget_risk_score,
                row.internal_observation_ref_digest,
                row.observed_at.isoformat(),
            ),
        ),
    )
    rows = tuple(
        _replace_row_ref(row, public_row_ref=f"exit_slippage_budget_row_{index:03d}")
        for index, row in enumerate(sorted_rows, start=1)
    )
    reason_codes = _summary_reason_codes(rows)
    return ResearchMarketDepthExitSlippageBudgetReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        observation_count=_decimal_count(len(rows)),
        pass_count=_decimal_count(_status_count(rows, STATUS_PASS)),
        watch_count=_decimal_count(_status_count(rows, STATUS_WATCH)),
        block_count=_decimal_count(_status_count(rows, STATUS_BLOCK)),
        min_depth_coverage_ratio=_minimum_row_value(rows, "depth_coverage_ratio"),
        max_slippage_budget_utilization_ratio=_maximum_row_value(
            rows,
            "slippage_budget_utilization_ratio",
        ),
        max_exit_slippage_budget_risk_score=_maximum_row_value(
            rows,
            "exit_slippage_budget_risk_score",
        ),
        average_exit_slippage_budget_risk_score=_average_row_value(
            rows,
            "exit_slippage_budget_risk_score",
        ),
        status=_summary_status(reason_codes),
        rows=rows,
        reason_codes=reason_codes,
    )


def research_market_depth_exit_slippage_budget_report_payload(
    report: ResearchMarketDepthExitSlippageBudgetReport,
) -> dict[str, Any]:
    if type(report) is not ResearchMarketDepthExitSlippageBudgetReport:
        raise ValueError("report must be a ResearchMarketDepthExitSlippageBudgetReport")
    _require_hard_flags("report", report)
    expected_digest = _report_validation_digest(report)
    if report.derived_validation_digest != expected_digest:
        raise ValueError("derived_validation_digest must match report fields")
    payload = _report_payload(report)
    _reject_unsafe_public_payload(payload)
    return payload


def research_market_depth_exit_slippage_budget_report_digest(
    report: ResearchMarketDepthExitSlippageBudgetReport,
) -> str:
    if type(report) is not ResearchMarketDepthExitSlippageBudgetReport:
        raise ValueError("report must be a ResearchMarketDepthExitSlippageBudgetReport")
    _require_hard_flags("report", report)
    expected_digest = _report_validation_digest(report)
    if report.derived_validation_digest != expected_digest:
        raise ValueError("derived_validation_digest must match report fields")
    return expected_digest


def _row_from_observation(
    observation: ResearchMarketDepthExitSlippageBudgetObservation,
    *,
    config: ResearchMarketDepthExitSlippageBudgetConfig,
) -> ResearchMarketDepthExitSlippageBudgetRow:
    depth_coverage_ratio = _ratio(
        observation.available_exit_depth,
        observation.planned_exit_notional,
    )
    slippage_budget_utilization_ratio = _ratio(
        observation.estimated_exit_slippage_rate,
        observation.slippage_budget_rate,
    )
    depth_coverage_risk_score = _weighted_score(
        _depth_coverage_risk_factor(depth_coverage_ratio, config),
        config.depth_coverage_weight,
    )
    slippage_budget_risk_score = _weighted_score(
        _ceiling_risk_factor(
            slippage_budget_utilization_ratio,
            config.slippage_budget_utilization_block_threshold,
        ),
        config.slippage_budget_weight,
    )
    spread_risk_score = _weighted_score(
        _ceiling_risk_factor(observation.bid_ask_spread_rate, config.spread_block_threshold),
        config.spread_weight,
    )
    depth_decay_risk_score = _weighted_score(
        _ceiling_risk_factor(observation.depth_decay_rate, config.depth_decay_block_threshold),
        config.depth_decay_weight,
    )
    exit_window_risk_score = _weighted_score(
        _ceiling_risk_factor(observation.exit_window_hours, config.exit_window_block_hours),
        config.exit_window_weight,
    )
    fee_drag_risk_score = _weighted_score(
        _ceiling_risk_factor(observation.fee_drag_rate, config.fee_drag_block_threshold),
        config.fee_drag_weight,
    )
    risk_score = _quantize(
        depth_coverage_risk_score
        + slippage_budget_risk_score
        + spread_risk_score
        + depth_decay_risk_score
        + exit_window_risk_score
        + fee_drag_risk_score,
    )
    status = _row_status(
        observation=observation,
        depth_coverage_ratio=depth_coverage_ratio,
        slippage_budget_utilization_ratio=slippage_budget_utilization_ratio,
        risk_score=risk_score,
        config=config,
    )
    return ResearchMarketDepthExitSlippageBudgetRow(
        public_row_ref="exit_slippage_budget_row_pending",
        internal_observation_ref_digest=_private_reference_digest(
            observation.internal_observation_ref,
        ),
        observed_at=observation.observed_at,
        planned_exit_notional=observation.planned_exit_notional,
        available_exit_depth=observation.available_exit_depth,
        estimated_exit_slippage_rate=observation.estimated_exit_slippage_rate,
        slippage_budget_rate=observation.slippage_budget_rate,
        bid_ask_spread_rate=observation.bid_ask_spread_rate,
        depth_decay_rate=observation.depth_decay_rate,
        exit_window_hours=observation.exit_window_hours,
        fee_drag_rate=observation.fee_drag_rate,
        depth_coverage_ratio=depth_coverage_ratio,
        slippage_budget_utilization_ratio=slippage_budget_utilization_ratio,
        depth_coverage_risk_score=depth_coverage_risk_score,
        slippage_budget_risk_score=slippage_budget_risk_score,
        spread_risk_score=spread_risk_score,
        depth_decay_risk_score=depth_decay_risk_score,
        exit_window_risk_score=exit_window_risk_score,
        fee_drag_risk_score=fee_drag_risk_score,
        exit_slippage_budget_risk_score=risk_score,
        status=status,
        reason_codes=_row_reason_codes(
            observation=observation,
            depth_coverage_ratio=depth_coverage_ratio,
            slippage_budget_utilization_ratio=slippage_budget_utilization_ratio,
            status=status,
            config=config,
        ),
    )


def _replace_row_ref(
    row: ResearchMarketDepthExitSlippageBudgetRow,
    *,
    public_row_ref: str,
) -> ResearchMarketDepthExitSlippageBudgetRow:
    return ResearchMarketDepthExitSlippageBudgetRow(
        public_row_ref=public_row_ref,
        internal_observation_ref_digest=row.internal_observation_ref_digest,
        observed_at=row.observed_at,
        planned_exit_notional=row.planned_exit_notional,
        available_exit_depth=row.available_exit_depth,
        estimated_exit_slippage_rate=row.estimated_exit_slippage_rate,
        slippage_budget_rate=row.slippage_budget_rate,
        bid_ask_spread_rate=row.bid_ask_spread_rate,
        depth_decay_rate=row.depth_decay_rate,
        exit_window_hours=row.exit_window_hours,
        fee_drag_rate=row.fee_drag_rate,
        depth_coverage_ratio=row.depth_coverage_ratio,
        slippage_budget_utilization_ratio=row.slippage_budget_utilization_ratio,
        depth_coverage_risk_score=row.depth_coverage_risk_score,
        slippage_budget_risk_score=row.slippage_budget_risk_score,
        spread_risk_score=row.spread_risk_score,
        depth_decay_risk_score=row.depth_decay_risk_score,
        exit_window_risk_score=row.exit_window_risk_score,
        fee_drag_risk_score=row.fee_drag_risk_score,
        exit_slippage_budget_risk_score=row.exit_slippage_budget_risk_score,
        status=row.status,
        reason_codes=row.reason_codes,
    )


def _row_status(
    *,
    observation: ResearchMarketDepthExitSlippageBudgetObservation,
    depth_coverage_ratio: Decimal,
    slippage_budget_utilization_ratio: Decimal,
    risk_score: Decimal,
    config: ResearchMarketDepthExitSlippageBudgetConfig,
) -> str:
    if (
        depth_coverage_ratio <= config.depth_coverage_block_threshold
        or slippage_budget_utilization_ratio
        >= config.slippage_budget_utilization_block_threshold
        or observation.bid_ask_spread_rate >= config.spread_block_threshold
        or observation.depth_decay_rate >= config.depth_decay_block_threshold
        or observation.exit_window_hours >= config.exit_window_block_hours
        or observation.fee_drag_rate >= config.fee_drag_block_threshold
        or risk_score >= config.block_exit_slippage_budget_risk_score
    ):
        return STATUS_BLOCK
    if (
        depth_coverage_ratio < config.depth_coverage_watch_threshold
        or slippage_budget_utilization_ratio
        >= config.slippage_budget_utilization_watch_threshold
        or observation.bid_ask_spread_rate >= config.spread_watch_threshold
        or observation.depth_decay_rate >= config.depth_decay_watch_threshold
        or observation.exit_window_hours >= config.exit_window_watch_hours
        or observation.fee_drag_rate >= config.fee_drag_watch_threshold
        or risk_score >= config.watch_exit_slippage_budget_risk_score
    ):
        return STATUS_WATCH
    return STATUS_PASS


def _row_reason_codes(
    *,
    observation: ResearchMarketDepthExitSlippageBudgetObservation,
    depth_coverage_ratio: Decimal,
    slippage_budget_utilization_ratio: Decimal,
    status: str,
    config: ResearchMarketDepthExitSlippageBudgetConfig,
) -> tuple[str, ...]:
    if status == STATUS_PASS:
        return (PASS_REASON,)
    reasons: list[str] = []
    _add_band_reason(
        reasons,
        "depth_coverage",
        value=depth_coverage_ratio,
        watch=config.depth_coverage_watch_threshold,
        block=config.depth_coverage_block_threshold,
        lower_is_worse=True,
    )
    _add_band_reason(
        reasons,
        "slippage_budget",
        value=slippage_budget_utilization_ratio,
        watch=config.slippage_budget_utilization_watch_threshold,
        block=config.slippage_budget_utilization_block_threshold,
    )
    _add_band_reason(
        reasons,
        "spread",
        value=observation.bid_ask_spread_rate,
        watch=config.spread_watch_threshold,
        block=config.spread_block_threshold,
    )
    _add_band_reason(
        reasons,
        "depth_decay",
        value=observation.depth_decay_rate,
        watch=config.depth_decay_watch_threshold,
        block=config.depth_decay_block_threshold,
    )
    _add_band_reason(
        reasons,
        "exit_window",
        value=observation.exit_window_hours,
        watch=config.exit_window_watch_hours,
        block=config.exit_window_block_hours,
    )
    _add_band_reason(
        reasons,
        "fee_drag",
        value=observation.fee_drag_rate,
        watch=config.fee_drag_watch_threshold,
        block=config.fee_drag_block_threshold,
    )
    return tuple(sorted(reasons))


def _add_band_reason(
    reasons: list[str],
    prefix: str,
    *,
    value: Decimal,
    watch: Decimal,
    block: Decimal,
    lower_is_worse: bool = False,
) -> None:
    if lower_is_worse:
        if value <= block:
            reasons.append(f"{prefix}_block")
        elif value < watch:
            reasons.append(f"{prefix}_watch")
        return
    if value >= block:
        reasons.append(f"{prefix}_block")
    elif value >= watch:
        reasons.append(f"{prefix}_watch")


def _depth_coverage_risk_factor(
    depth_coverage_ratio: Decimal,
    config: ResearchMarketDepthExitSlippageBudgetConfig,
) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        factor = ONE - (depth_coverage_ratio / config.minimum_depth_coverage_ratio)
    return _clamped_ratio(factor)


def _ceiling_risk_factor(value: Decimal, ceiling: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        factor = value / ceiling
    return _clamped_ratio(factor)


def _weighted_score(factor: Decimal, weight: Decimal) -> Decimal:
    return _quantize(factor * weight)


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return _quantize(numerator / denominator)


def _normalize_observations(
    observations: Iterable[object],
) -> tuple[ResearchMarketDepthExitSlippageBudgetObservation, ...]:
    if isinstance(observations, (str, bytes)):
        raise ValueError("observations must be an iterable of observation records")
    normalized: list[ResearchMarketDepthExitSlippageBudgetObservation] = []
    seen_refs: set[str] = set()
    for item in observations:
        if type(item) is not ResearchMarketDepthExitSlippageBudgetObservation:
            raise ValueError(
                "observations must contain ResearchMarketDepthExitSlippageBudgetObservation",
            )
        _require_hard_flags("observation", item)
        if item.internal_observation_ref in seen_refs:
            raise ValueError("internal_observation_ref values must be unique")
        seen_refs.add(item.internal_observation_ref)
        normalized.append(item)
    return tuple(normalized)


def _summary_reason_codes(
    rows: tuple[ResearchMarketDepthExitSlippageBudgetRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return (MISSING_INPUTS_REASON,)
    unique_codes = {code for row in rows for code in row.reason_codes if code != PASS_REASON}
    if not unique_codes:
        return (PASS_REASON,)
    return tuple(sorted(unique_codes, key=_reason_priority))


def _summary_status(reason_codes: tuple[str, ...]) -> str:
    if MISSING_INPUTS_REASON in reason_codes:
        return STATUS_BLOCK
    if any(code.endswith("_block") for code in reason_codes):
        return STATUS_BLOCK
    if any(code.endswith("_watch") for code in reason_codes):
        return STATUS_WATCH
    return STATUS_PASS


def _reason_priority(reason_code: str) -> tuple[int, str]:
    if reason_code in REASON_PRIORITY:
        return (REASON_PRIORITY.index(reason_code), reason_code)
    return (len(REASON_PRIORITY), reason_code)


def _status_count(
    rows: tuple[ResearchMarketDepthExitSlippageBudgetRow, ...],
    status: str,
) -> int:
    return sum(1 for row in rows if row.status == status)


def _minimum_row_value(
    rows: tuple[ResearchMarketDepthExitSlippageBudgetRow, ...],
    field_name: str,
) -> Decimal:
    if not rows:
        return ZERO
    return min(getattr(row, field_name) for row in rows)


def _maximum_row_value(
    rows: tuple[ResearchMarketDepthExitSlippageBudgetRow, ...],
    field_name: str,
) -> Decimal:
    if not rows:
        return ZERO
    return max(getattr(row, field_name) for row in rows)


def _average_row_value(
    rows: tuple[ResearchMarketDepthExitSlippageBudgetRow, ...],
    field_name: str,
) -> Decimal | None:
    if not rows:
        return None
    with localcontext(DECIMAL_CONTEXT):
        return _quantize(sum(getattr(row, field_name) for row in rows) / Decimal(len(rows)))


def _normalize_rows(
    rows: tuple[ResearchMarketDepthExitSlippageBudgetRow, ...],
) -> tuple[ResearchMarketDepthExitSlippageBudgetRow, ...]:
    if type(rows) is not tuple:
        raise ValueError("rows must be a tuple")
    for row in rows:
        if type(row) is not ResearchMarketDepthExitSlippageBudgetRow:
            raise ValueError("rows must contain ResearchMarketDepthExitSlippageBudgetRow")
        _require_hard_flags("row", row)
    return rows


def _validate_report(report: ResearchMarketDepthExitSlippageBudgetReport) -> None:
    rows = report.rows
    if report.observation_count != _decimal_count(len(rows)):
        raise ValueError("observation_count must match rows")
    if report.pass_count != _decimal_count(_status_count(rows, STATUS_PASS)):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _decimal_count(_status_count(rows, STATUS_WATCH)):
        raise ValueError("watch_count must match rows")
    if report.block_count != _decimal_count(_status_count(rows, STATUS_BLOCK)):
        raise ValueError("block_count must match rows")
    if report.min_depth_coverage_ratio != _minimum_row_value(rows, "depth_coverage_ratio"):
        raise ValueError("min_depth_coverage_ratio must match rows")
    if report.max_slippage_budget_utilization_ratio != _maximum_row_value(
        rows,
        "slippage_budget_utilization_ratio",
    ):
        raise ValueError("max_slippage_budget_utilization_ratio must match rows")
    if report.max_exit_slippage_budget_risk_score != _maximum_row_value(
        rows,
        "exit_slippage_budget_risk_score",
    ):
        raise ValueError("max_exit_slippage_budget_risk_score must match rows")
    if report.average_exit_slippage_budget_risk_score != _average_row_value(
        rows,
        "exit_slippage_budget_risk_score",
    ):
        raise ValueError("average_exit_slippage_budget_risk_score must match rows")
    if report.reason_codes != _summary_reason_codes(rows):
        raise ValueError("reason_codes must match rows")
    if report.status != _summary_status(report.reason_codes):
        raise ValueError("status must match reason_codes")


def _report_payload(report: ResearchMarketDepthExitSlippageBudgetReport) -> dict[str, Any]:
    return {
        "generated_at": _payload_value(report.generated_at),
        "config_version": report.config_version,
        "observation_count": _payload_value(report.observation_count),
        "pass_count": _payload_value(report.pass_count),
        "watch_count": _payload_value(report.watch_count),
        "block_count": _payload_value(report.block_count),
        "min_depth_coverage_ratio": _payload_value(report.min_depth_coverage_ratio),
        "max_slippage_budget_utilization_ratio": _payload_value(
            report.max_slippage_budget_utilization_ratio,
        ),
        "max_exit_slippage_budget_risk_score": _payload_value(
            report.max_exit_slippage_budget_risk_score,
        ),
        "average_exit_slippage_budget_risk_score": _payload_value(
            report.average_exit_slippage_budget_risk_score,
        ),
        "status": report.status,
        "rows": [_row_payload(row) for row in report.rows],
        "reason_codes": list(report.reason_codes),
        "derived_validation_digest": report.derived_validation_digest,
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }


def _report_digest_payload(
    report: ResearchMarketDepthExitSlippageBudgetReport,
) -> dict[str, Any]:
    payload = _report_payload(report)
    payload.pop("derived_validation_digest")
    return payload


def _row_payload(row: ResearchMarketDepthExitSlippageBudgetRow) -> dict[str, Any]:
    return {
        "public_row_ref": row.public_row_ref,
        "internal_observation_ref_digest": row.internal_observation_ref_digest,
        "observed_at": _payload_value(row.observed_at),
        "planned_exit_notional": _payload_value(row.planned_exit_notional),
        "available_exit_depth": _payload_value(row.available_exit_depth),
        "estimated_exit_slippage_rate": _payload_value(row.estimated_exit_slippage_rate),
        "slippage_budget_rate": _payload_value(row.slippage_budget_rate),
        "bid_ask_spread_rate": _payload_value(row.bid_ask_spread_rate),
        "depth_decay_rate": _payload_value(row.depth_decay_rate),
        "exit_window_hours": _payload_value(row.exit_window_hours),
        "fee_drag_rate": _payload_value(row.fee_drag_rate),
        "depth_coverage_ratio": _payload_value(row.depth_coverage_ratio),
        "slippage_budget_utilization_ratio": _payload_value(
            row.slippage_budget_utilization_ratio,
        ),
        "depth_coverage_risk_score": _payload_value(row.depth_coverage_risk_score),
        "slippage_budget_risk_score": _payload_value(row.slippage_budget_risk_score),
        "spread_risk_score": _payload_value(row.spread_risk_score),
        "depth_decay_risk_score": _payload_value(row.depth_decay_risk_score),
        "exit_window_risk_score": _payload_value(row.exit_window_risk_score),
        "fee_drag_risk_score": _payload_value(row.fee_drag_risk_score),
        "exit_slippage_budget_risk_score": _payload_value(
            row.exit_slippage_budget_risk_score,
        ),
        "status": row.status,
        "reason_codes": list(row.reason_codes),
        "row_validation_digest": row.row_validation_digest,
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }


def _row_digest_payload(row: ResearchMarketDepthExitSlippageBudgetRow) -> dict[str, Any]:
    payload = _row_payload(row)
    payload.pop("row_validation_digest")
    return payload


def _row_validation_digest(row: ResearchMarketDepthExitSlippageBudgetRow) -> str:
    return _stable_digest(_row_digest_payload(row))


def _report_validation_digest(report: ResearchMarketDepthExitSlippageBudgetReport) -> str:
    return _stable_digest(_report_digest_payload(report))


def _private_reference_digest(value: str) -> str:
    return sha256(value.encode("utf-8")).hexdigest()


def _stable_digest(payload: dict[str, Any]) -> str:
    encoded = json.dumps(
        payload,
        allow_nan=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    return sha256(encoded.encode("utf-8")).hexdigest()


def _payload_value(value: object) -> object:
    if type(value) is Decimal:
        return format(value, "f")
    if type(value) is datetime:
        return value.isoformat()
    if value is None:
        return None
    if type(value) in (str, bool):
        return value
    if type(value) is tuple:
        return [_payload_value(item) for item in value]
    if type(value) is list:
        return [_payload_value(item) for item in value]
    if type(value) is dict:
        return {str(key): _payload_value(item) for key, item in value.items()}
    raise ValueError(f"unsupported payload value type: {type(value).__name__}")


def _reject_unsafe_public_payload(payload: dict[str, Any]) -> None:
    encoded = json.dumps(payload, allow_nan=False, sort_keys=True).lower()
    for fragment in UNSAFE_PUBLIC_FRAGMENTS:
        if fragment in encoded:
            raise ValueError("public payload contains unsafe private market data")


def _require_exact_type(value: object, expected_type: type[object], label: str) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{label} must be exactly {expected_type.__name__}")


def _require_public_label(field_name: str, value: object) -> None:
    if type(value) is not str or not PUBLIC_LABEL_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a public label")
    lowered = value.lower()
    if any(fragment in lowered for fragment in UNSAFE_PUBLIC_FRAGMENTS):
        raise ValueError(f"{field_name} must not contain private market data")


def _require_private_reference(field_name: str, value: object) -> None:
    if type(value) is not str or not value.strip():
        raise ValueError(f"{field_name} must be a non-empty string")


def _require_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in MARKET_DEPTH_EXIT_SLIPPAGE_BUDGET_STATUSES:
        raise ValueError(f"{field_name} must be pass, watch, or block")


def _normalize_reason_codes(value: object) -> tuple[str, ...]:
    if type(value) is not tuple or not value:
        raise ValueError("reason_codes must be a non-empty tuple")
    normalized: list[str] = []
    for item in value:
        if type(item) is not str or not REASON_CODE_RE.fullmatch(item):
            raise ValueError("reason_codes must contain public reason codes")
        lowered = item.lower()
        if any(fragment in lowered for fragment in UNSAFE_PUBLIC_FRAGMENTS):
            raise ValueError("reason_codes must not contain private market data")
        normalized.append(item)
    return tuple(normalized)


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in PHASE_FLAG_FIELDS:
        if getattr(value, field_name, None) is not True:
            raise ValueError(f"{label} must be {field_name}")


def _require_hex_digest(field_name: str, value: object) -> None:
    if type(value) is not str or not HEX_DIGEST_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a sha256 hex digest")


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return _quantize(value)


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


def _require_optional_nonnegative_decimal(
    field_name: str,
    value: object,
) -> Decimal | None:
    if value is None:
        return None
    return _require_nonnegative_decimal(field_name, value)


def _require_below(field_name: str, value: Decimal, ceiling: Decimal) -> None:
    if value >= ceiling:
        raise ValueError(f"{field_name} must be below block threshold")


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _quantize(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(QUANTUM)


def _clamped_ratio(value: Decimal) -> Decimal:
    normalized = _quantize(value)
    if normalized < ZERO:
        return ZERO
    if normalized > ONE:
        return ONE
    return normalized


def _decimal_count(value: int) -> Decimal:
    return Decimal(value).quantize(QUANTUM)
