"""Pure report-only fee/depth exit-tail guard reducer for manual research."""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable
from dataclasses import asdict, dataclass, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
import json
from typing import Any


DEFAULT_RESEARCH_MARKET_FEE_DEPTH_EXIT_TAIL_GUARD_REPORT_CONFIG_VERSION = (
    "research-market-fee-depth-exit-tail-guard-report-v0"
)
FEE_DEPTH_EXIT_TAIL_GUARD_STATUSES = ("pass", "watch", "block")

ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
QUANT = Decimal("0.000001")
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
SAFE_TEXT_CHARS = frozenset("abcdefghijklmnopqrstuvwxyz0123456789._-")
HEX_CHARS = frozenset("0123456789abcdef")

EMPTY_REASON = "no_fee_depth_exit_tail_guard_observations"
EXIT_SHORTFALL_PASS_REASON = "exit_depth_shortfall_pass"
EXIT_SHORTFALL_WATCH_REASON = "exit_depth_shortfall_watch"
EXIT_SHORTFALL_BLOCK_REASON = "exit_depth_shortfall_block"
FEE_DEPTH_PASS_REASON = "fee_depth_burden_pass"
FEE_DEPTH_WATCH_REASON = "fee_depth_burden_watch"
FEE_DEPTH_BLOCK_REASON = "fee_depth_burden_block"
TAIL_PRESSURE_PASS_REASON = "exit_tail_pressure_pass"
TAIL_PRESSURE_WATCH_REASON = "exit_tail_pressure_watch"
TAIL_PRESSURE_BLOCK_REASON = "exit_tail_pressure_block"
STALE_DEPTH_PASS_REASON = "stale_depth_age_pass"
STALE_DEPTH_WATCH_REASON = "stale_depth_age_watch"
STALE_DEPTH_BLOCK_REASON = "stale_depth_age_block"
MANUAL_PRESSURE_PASS_REASON = "manual_guard_pressure_pass"
MANUAL_PRESSURE_WATCH_REASON = "manual_guard_pressure_watch"
MANUAL_PRESSURE_BLOCK_REASON = "manual_guard_pressure_block"
GUARD_SCORE_PASS_REASON = "exit_tail_guard_score_pass"
GUARD_SCORE_WATCH_REASON = "exit_tail_guard_score_watch"
GUARD_SCORE_BLOCK_REASON = "exit_tail_guard_score_block"

PASS_REASON_CODES = (
    EXIT_SHORTFALL_PASS_REASON,
    FEE_DEPTH_PASS_REASON,
    TAIL_PRESSURE_PASS_REASON,
    STALE_DEPTH_PASS_REASON,
    MANUAL_PRESSURE_PASS_REASON,
    GUARD_SCORE_PASS_REASON,
)
WATCH_REASON_CODES = (
    EXIT_SHORTFALL_WATCH_REASON,
    FEE_DEPTH_WATCH_REASON,
    TAIL_PRESSURE_WATCH_REASON,
    STALE_DEPTH_WATCH_REASON,
    MANUAL_PRESSURE_WATCH_REASON,
    GUARD_SCORE_WATCH_REASON,
)
BLOCK_REASON_CODES = (
    EXIT_SHORTFALL_BLOCK_REASON,
    FEE_DEPTH_BLOCK_REASON,
    TAIL_PRESSURE_BLOCK_REASON,
    STALE_DEPTH_BLOCK_REASON,
    MANUAL_PRESSURE_BLOCK_REASON,
    GUARD_SCORE_BLOCK_REASON,
)
BASE_REASON_CODES = PASS_REASON_CODES + WATCH_REASON_CODES + BLOCK_REASON_CODES
REPORT_REASON_CODE_ORDER = BLOCK_REASON_CODES + WATCH_REASON_CODES + PASS_REASON_CODES
UNSAFE_PUBLIC_FRAGMENTS = (
    "candidate_id",
    "condition_id",
    "market_id",
    "market_" "slug",
    "slug",
    "question",
    "source_" "url",
    "source_" "text",
    "url",
    "dsn",
    "table",
    "token",
    "wal" "let",
    "au" "th",
    "private",
    "secret",
    "credential",
    "or" "der",
    "tra" "de",
    "li" "ve",
    "buy",
    "sell",
    "size",
    "siz" "ing",
    "recom" "mendation",
)


__all__ = (
    "DEFAULT_RESEARCH_MARKET_FEE_DEPTH_EXIT_TAIL_GUARD_REPORT_CONFIG_VERSION",
    "FEE_DEPTH_EXIT_TAIL_GUARD_STATUSES",
    "ResearchMarketFeeDepthExitTailGuardConfig",
    "ResearchMarketFeeDepthExitTailGuardObservation",
    "ResearchMarketFeeDepthExitTailGuardReasonCodeCount",
    "ResearchMarketFeeDepthExitTailGuardReport",
    "ResearchMarketFeeDepthExitTailGuardRow",
    "build_research_market_fee_depth_exit_tail_guard_report",
    "research_market_fee_depth_exit_tail_guard_report_digest",
    "research_market_fee_depth_exit_tail_guard_report_payload",
)


@dataclass(frozen=True)
class ResearchMarketFeeDepthExitTailGuardConfig:
    config_version: str = (
        DEFAULT_RESEARCH_MARKET_FEE_DEPTH_EXIT_TAIL_GUARD_REPORT_CONFIG_VERSION
    )
    max_pass_exit_shortfall_ratio: Decimal = Decimal("0.050000")
    max_watch_exit_shortfall_ratio: Decimal = Decimal("0.250000")
    max_pass_fee_depth_burden_ratio: Decimal = Decimal("0.010000")
    max_watch_fee_depth_burden_ratio: Decimal = Decimal("0.030000")
    max_pass_tail_pressure_score: Decimal = Decimal("0.100000")
    max_watch_tail_pressure_score: Decimal = Decimal("0.350000")
    max_pass_stale_depth_age_seconds: Decimal = Decimal("120.000000")
    max_watch_stale_depth_age_seconds: Decimal = Decimal("600.000000")
    max_pass_manual_guard_pressure: Decimal = Decimal("0.200000")
    max_watch_manual_guard_pressure: Decimal = Decimal("0.600000")
    pass_guard_score: Decimal = Decimal("0.750000")
    watch_guard_score: Decimal = Decimal("0.450000")
    depth_coverage_weight: Decimal = Decimal("0.350000")
    fee_depth_weight: Decimal = Decimal("0.200000")
    tail_pressure_weight: Decimal = Decimal("0.200000")
    freshness_weight: Decimal = Decimal("0.150000")
    manual_pressure_weight: Decimal = Decimal("0.100000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchMarketFeeDepthExitTailGuardConfig does not support subclassing",
        )

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchMarketFeeDepthExitTailGuardConfig, "config")
        _require_public_text("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_MARKET_FEE_DEPTH_EXIT_TAIL_GUARD_REPORT_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "max_pass_exit_shortfall_ratio",
            "max_watch_exit_shortfall_ratio",
            "max_pass_fee_depth_burden_ratio",
            "max_watch_fee_depth_burden_ratio",
            "max_pass_tail_pressure_score",
            "max_watch_tail_pressure_score",
            "max_pass_manual_guard_pressure",
            "max_watch_manual_guard_pressure",
            "pass_guard_score",
            "watch_guard_score",
            "depth_coverage_weight",
            "fee_depth_weight",
            "tail_pressure_weight",
            "freshness_weight",
            "manual_pressure_weight",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "max_pass_stale_depth_age_seconds",
            "max_watch_stale_depth_age_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_positive_decimal(field_name, getattr(self, field_name)),
            )
        _validate_config(self)
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class ResearchMarketFeeDepthExitTailGuardObservation:
    research_case_key: str
    observed_at: datetime
    last_depth_update_at: datetime
    exit_exposure_probability: Decimal
    near_exit_depth: Decimal
    far_exit_depth: Decimal
    taker_fee_bps: Decimal
    spread_bps: Decimal
    tail_loss_probability: Decimal
    tail_loss_impact: Decimal
    manual_guard_pressure: Decimal
    reason_codes: tuple[str, ...] = ()
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchMarketFeeDepthExitTailGuardObservation "
            "does not support subclassing",
        )

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchMarketFeeDepthExitTailGuardObservation, "input")
        _require_public_text("research_case_key", self.research_case_key)
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        object.__setattr__(
            self,
            "last_depth_update_at",
            _as_utc("last_depth_update_at", self.last_depth_update_at),
        )
        object.__setattr__(
            self,
            "exit_exposure_probability",
            _require_positive_ratio_decimal(
                "exit_exposure_probability",
                self.exit_exposure_probability,
            ),
        )
        for field_name in ("near_exit_depth", "far_exit_depth"):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        if self.near_exit_depth + self.far_exit_depth <= ZERO:
            raise ValueError("exit depth must provide positive aggregate depth")
        for field_name in (
            "taker_fee_bps",
            "spread_bps",
            "tail_loss_probability",
            "tail_loss_impact",
            "manual_guard_pressure",
        ):
            object.__setattr__(
                self,
                field_name,
                (
                    _require_nonnegative_decimal(field_name, getattr(self, field_name))
                    if field_name in ("taker_fee_bps", "spread_bps")
                    else _require_ratio_decimal(field_name, getattr(self, field_name))
                ),
            )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_input_reason_codes(self.reason_codes),
        )
        _require_hard_flags("input", self)


@dataclass(frozen=True)
class ResearchMarketFeeDepthExitTailGuardRow:
    guard_group_ref: str
    observed_at: datetime
    last_depth_update_at: datetime
    stale_depth_age_seconds: Decimal
    exit_exposure_probability: Decimal
    near_exit_depth: Decimal
    far_exit_depth: Decimal
    total_exit_depth: Decimal
    taker_fee_bps: Decimal
    spread_bps: Decimal
    fee_depth_burden_ratio: Decimal
    net_exit_depth: Decimal
    depth_coverage_ratio: Decimal
    exit_shortfall_ratio: Decimal
    tail_loss_probability: Decimal
    tail_loss_impact: Decimal
    tail_pressure_score: Decimal
    manual_guard_pressure: Decimal
    stale_depth_pressure: Decimal
    depth_coverage_score: Decimal
    fee_depth_score: Decimal
    tail_pressure_guard_score: Decimal
    freshness_score: Decimal
    manual_pressure_score: Decimal
    exit_tail_guard_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchMarketFeeDepthExitTailGuardRow does not support subclassing",
        )

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchMarketFeeDepthExitTailGuardRow, "row")
        _require_public_text("guard_group_ref", self.guard_group_ref)
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        object.__setattr__(
            self,
            "last_depth_update_at",
            _as_utc("last_depth_update_at", self.last_depth_update_at),
        )
        for field_name in (
            "stale_depth_age_seconds",
            "near_exit_depth",
            "far_exit_depth",
            "total_exit_depth",
            "taker_fee_bps",
            "spread_bps",
            "fee_depth_burden_ratio",
            "net_exit_depth",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "exit_exposure_probability",
            _require_positive_ratio_decimal(
                "exit_exposure_probability",
                self.exit_exposure_probability,
            ),
        )
        for field_name in (
            "depth_coverage_ratio",
            "exit_shortfall_ratio",
            "tail_loss_probability",
            "tail_loss_impact",
            "tail_pressure_score",
            "manual_guard_pressure",
            "stale_depth_pressure",
            "depth_coverage_score",
            "fee_depth_score",
            "tail_pressure_guard_score",
            "freshness_score",
            "manual_pressure_score",
            "exit_tail_guard_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        _require_status("status", self.status)
        object.__setattr__(self, "reason_codes", _normalize_row_reason_codes(self.reason_codes))
        _require_hard_flags("row", self)
        _validate_row(self)


@dataclass(frozen=True)
class ResearchMarketFeeDepthExitTailGuardReasonCodeCount:
    reason_code: str
    count: Decimal
    row_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchMarketFeeDepthExitTailGuardReasonCodeCount "
            "does not support subclassing",
        )

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchMarketFeeDepthExitTailGuardReasonCodeCount,
            "reason_code_count",
        )
        _require_output_reason_code("reason_code", self.reason_code)
        object.__setattr__(self, "count", _require_positive_decimal("count", self.count))
        object.__setattr__(
            self,
            "row_ratio",
            _require_ratio_decimal("row_ratio", self.row_ratio),
        )
        _require_hard_flags("reason_code_count", self)


@dataclass(frozen=True)
class ResearchMarketFeeDepthExitTailGuardReport:
    generated_at: datetime
    config_version: str
    input_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    average_exit_tail_guard_score: Decimal | None
    min_depth_coverage_ratio: Decimal
    max_exit_shortfall_ratio: Decimal
    max_fee_depth_burden_ratio: Decimal
    max_tail_pressure_score: Decimal
    max_stale_depth_age_seconds: Decimal
    max_manual_guard_pressure: Decimal
    status: str
    rows: tuple[ResearchMarketFeeDepthExitTailGuardRow, ...]
    reason_code_counts: tuple[ResearchMarketFeeDepthExitTailGuardReasonCodeCount, ...]
    reason_codes: tuple[str, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchMarketFeeDepthExitTailGuardReport does not support subclassing",
        )

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchMarketFeeDepthExitTailGuardReport, "report")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_text("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_MARKET_FEE_DEPTH_EXIT_TAIL_GUARD_REPORT_CONFIG_VERSION
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
            "average_exit_tail_guard_score",
            _require_optional_ratio_decimal(
                "average_exit_tail_guard_score",
                self.average_exit_tail_guard_score,
            ),
        )
        for field_name in (
            "min_depth_coverage_ratio",
            "max_exit_shortfall_ratio",
            "max_fee_depth_burden_ratio",
            "max_tail_pressure_score",
            "max_manual_guard_pressure",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "max_stale_depth_age_seconds",
            _require_nonnegative_decimal(
                "max_stale_depth_age_seconds",
                self.max_stale_depth_age_seconds,
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
            _normalize_report_reason_codes(self.reason_codes),
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


def build_research_market_fee_depth_exit_tail_guard_report(
    observations: Iterable[ResearchMarketFeeDepthExitTailGuardObservation],
    *,
    config: ResearchMarketFeeDepthExitTailGuardConfig,
    generated_at: datetime,
) -> ResearchMarketFeeDepthExitTailGuardReport:
    if type(config) is not ResearchMarketFeeDepthExitTailGuardConfig:
        raise ValueError("config must be a ResearchMarketFeeDepthExitTailGuardConfig")
    _require_hard_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    normalized = _normalize_observations(observations)
    for item in normalized:
        if item.observed_at > generated_at_utc:
            raise ValueError("observed_at must not be after generated_at")
        if item.last_depth_update_at > generated_at_utc:
            raise ValueError("last_depth_update_at must not be after generated_at")
    rows = tuple(
        _row_from_observation(
            guard_group_ref=f"fee_depth_tail_guard_{index:03d}",
            observation=item,
            config=config,
            generated_at=generated_at_utc,
        )
        for index, item in enumerate(sorted(normalized, key=_observation_sort_key), start=1)
    )
    reason_codes = _summary_reason_codes(rows)
    return ResearchMarketFeeDepthExitTailGuardReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        input_count=_decimal_count(len(rows)),
        pass_count=_decimal_count(_status_count(rows, "pass")),
        watch_count=_decimal_count(_status_count(rows, "watch")),
        block_count=_decimal_count(_status_count(rows, "block")),
        average_exit_tail_guard_score=_average_score(rows),
        min_depth_coverage_ratio=_min_or_zero(
            tuple(row.depth_coverage_ratio for row in rows),
        ),
        max_exit_shortfall_ratio=_max_or_zero(
            tuple(row.exit_shortfall_ratio for row in rows),
        ),
        max_fee_depth_burden_ratio=_max_or_zero(
            tuple(row.fee_depth_burden_ratio for row in rows),
        ),
        max_tail_pressure_score=_max_or_zero(
            tuple(row.tail_pressure_score for row in rows),
        ),
        max_stale_depth_age_seconds=_max_or_zero(
            tuple(row.stale_depth_age_seconds for row in rows),
        ),
        max_manual_guard_pressure=_max_or_zero(
            tuple(row.manual_guard_pressure for row in rows),
        ),
        status=_summary_status(rows),
        rows=rows,
        reason_code_counts=_reason_code_counts(rows, reason_codes),
        reason_codes=reason_codes,
    )


def research_market_fee_depth_exit_tail_guard_report_payload(
    report: ResearchMarketFeeDepthExitTailGuardReport | dict[str, Any],
) -> dict[str, Any]:
    if type(report) is ResearchMarketFeeDepthExitTailGuardReport:
        _require_hard_flags("report", report)
        if report.derived_validation_digest != _derived_report_digest(report):
            raise ValueError("derived_validation_digest must match report fields")
        payload = _payload_value(report)
    elif type(report) is dict:
        payload = _payload_value(report)
    else:
        raise ValueError("report must be a ResearchMarketFeeDepthExitTailGuardReport")
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    _reject_unsafe_public_payload("public payload", payload)
    _require_public_payload_schema(payload)
    _reject_public_numerics(payload)
    _require_hard_flags("public payload", _PayloadFlags(payload))
    supplied_digest = payload.get("derived_validation_digest")
    _require_hex_digest("derived_validation_digest", supplied_digest)
    if supplied_digest != _payload_validation_digest(payload):
        raise ValueError("derived_validation_digest does not match public payload")
    return payload


def research_market_fee_depth_exit_tail_guard_report_digest(
    report: ResearchMarketFeeDepthExitTailGuardReport,
) -> str:
    if type(report) is not ResearchMarketFeeDepthExitTailGuardReport:
        raise ValueError("report must be a ResearchMarketFeeDepthExitTailGuardReport")
    _require_hard_flags("report", report)
    expected_digest = _derived_report_digest(report)
    if report.derived_validation_digest != expected_digest:
        raise ValueError("derived_validation_digest must match report fields")
    return expected_digest


@dataclass(frozen=True)
class _PayloadFlags:
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


def _row_from_observation(
    *,
    guard_group_ref: str,
    observation: ResearchMarketFeeDepthExitTailGuardObservation,
    config: ResearchMarketFeeDepthExitTailGuardConfig,
    generated_at: datetime,
) -> ResearchMarketFeeDepthExitTailGuardRow:
    stale_depth_age_seconds = _age_seconds(generated_at, observation.last_depth_update_at)
    total_exit_depth = _quantize(observation.near_exit_depth + observation.far_exit_depth)
    fee_depth_burden_ratio = _quantize(
        (observation.taker_fee_bps + observation.spread_bps) / Decimal("10000"),
    )
    net_exit_depth = _quantize(max(ZERO, total_exit_depth - fee_depth_burden_ratio))
    depth_coverage_ratio = _bounded_ratio(
        net_exit_depth,
        observation.exit_exposure_probability,
    )
    exit_shortfall_ratio = _shortfall_ratio(
        net_exit_depth,
        observation.exit_exposure_probability,
    )
    tail_pressure_score = _quantize(
        observation.tail_loss_probability * observation.tail_loss_impact,
    )
    stale_depth_pressure = _bounded_ratio(
        stale_depth_age_seconds,
        config.max_watch_stale_depth_age_seconds,
    )
    depth_coverage_score = _quantize(ONE - exit_shortfall_ratio)
    fee_depth_score = _inverse_ratio_score(
        fee_depth_burden_ratio,
        config.max_watch_fee_depth_burden_ratio,
    )
    tail_pressure_guard_score = _inverse_ratio_score(
        tail_pressure_score,
        config.max_watch_tail_pressure_score,
    )
    freshness_score = _inverse_ratio_score(
        stale_depth_age_seconds,
        config.max_watch_stale_depth_age_seconds,
    )
    manual_pressure_score = _inverse_ratio_score(
        observation.manual_guard_pressure,
        config.max_watch_manual_guard_pressure,
    )
    exit_tail_guard_score = _exit_tail_guard_score(
        depth_coverage_score=depth_coverage_score,
        fee_depth_burden_ratio=fee_depth_burden_ratio,
        tail_pressure_score=tail_pressure_score,
        stale_depth_age_seconds=stale_depth_age_seconds,
        manual_guard_pressure=observation.manual_guard_pressure,
        config=config,
    )
    reason_codes = _row_reason_codes(
        exit_shortfall_ratio=exit_shortfall_ratio,
        fee_depth_burden_ratio=fee_depth_burden_ratio,
        tail_pressure_score=tail_pressure_score,
        stale_depth_age_seconds=stale_depth_age_seconds,
        manual_guard_pressure=observation.manual_guard_pressure,
        exit_tail_guard_score=exit_tail_guard_score,
        input_reason_codes=observation.reason_codes,
        config=config,
    )
    return ResearchMarketFeeDepthExitTailGuardRow(
        guard_group_ref=guard_group_ref,
        observed_at=observation.observed_at,
        last_depth_update_at=observation.last_depth_update_at,
        stale_depth_age_seconds=stale_depth_age_seconds,
        exit_exposure_probability=observation.exit_exposure_probability,
        near_exit_depth=observation.near_exit_depth,
        far_exit_depth=observation.far_exit_depth,
        total_exit_depth=total_exit_depth,
        taker_fee_bps=observation.taker_fee_bps,
        spread_bps=observation.spread_bps,
        fee_depth_burden_ratio=fee_depth_burden_ratio,
        net_exit_depth=net_exit_depth,
        depth_coverage_ratio=depth_coverage_ratio,
        exit_shortfall_ratio=exit_shortfall_ratio,
        tail_loss_probability=observation.tail_loss_probability,
        tail_loss_impact=observation.tail_loss_impact,
        tail_pressure_score=tail_pressure_score,
        manual_guard_pressure=observation.manual_guard_pressure,
        stale_depth_pressure=stale_depth_pressure,
        depth_coverage_score=depth_coverage_score,
        fee_depth_score=fee_depth_score,
        tail_pressure_guard_score=tail_pressure_guard_score,
        freshness_score=freshness_score,
        manual_pressure_score=manual_pressure_score,
        exit_tail_guard_score=exit_tail_guard_score,
        status=_status_from_reason_codes(reason_codes),
        reason_codes=reason_codes,
    )


def _row_reason_codes(
    *,
    exit_shortfall_ratio: Decimal,
    fee_depth_burden_ratio: Decimal,
    tail_pressure_score: Decimal,
    stale_depth_age_seconds: Decimal,
    manual_guard_pressure: Decimal,
    exit_tail_guard_score: Decimal,
    input_reason_codes: tuple[str, ...],
    config: ResearchMarketFeeDepthExitTailGuardConfig,
) -> tuple[str, ...]:
    reasons = [
        _threshold_reason(
            exit_shortfall_ratio,
            pass_threshold=config.max_pass_exit_shortfall_ratio,
            watch_threshold=config.max_watch_exit_shortfall_ratio,
            pass_reason=EXIT_SHORTFALL_PASS_REASON,
            watch_reason=EXIT_SHORTFALL_WATCH_REASON,
            block_reason=EXIT_SHORTFALL_BLOCK_REASON,
        ),
        _threshold_reason(
            fee_depth_burden_ratio,
            pass_threshold=config.max_pass_fee_depth_burden_ratio,
            watch_threshold=config.max_watch_fee_depth_burden_ratio,
            pass_reason=FEE_DEPTH_PASS_REASON,
            watch_reason=FEE_DEPTH_WATCH_REASON,
            block_reason=FEE_DEPTH_BLOCK_REASON,
        ),
        _threshold_reason(
            tail_pressure_score,
            pass_threshold=config.max_pass_tail_pressure_score,
            watch_threshold=config.max_watch_tail_pressure_score,
            pass_reason=TAIL_PRESSURE_PASS_REASON,
            watch_reason=TAIL_PRESSURE_WATCH_REASON,
            block_reason=TAIL_PRESSURE_BLOCK_REASON,
        ),
        _threshold_reason(
            stale_depth_age_seconds,
            pass_threshold=config.max_pass_stale_depth_age_seconds,
            watch_threshold=config.max_watch_stale_depth_age_seconds,
            pass_reason=STALE_DEPTH_PASS_REASON,
            watch_reason=STALE_DEPTH_WATCH_REASON,
            block_reason=STALE_DEPTH_BLOCK_REASON,
        ),
        _threshold_reason(
            manual_guard_pressure,
            pass_threshold=config.max_pass_manual_guard_pressure,
            watch_threshold=config.max_watch_manual_guard_pressure,
            pass_reason=MANUAL_PRESSURE_PASS_REASON,
            watch_reason=MANUAL_PRESSURE_WATCH_REASON,
            block_reason=MANUAL_PRESSURE_BLOCK_REASON,
        ),
        _score_reason(exit_tail_guard_score, config=config),
    ]
    reasons.extend(f"input_{reason_code}" for reason_code in input_reason_codes)
    return tuple(reasons)


def _threshold_reason(
    value: Decimal,
    *,
    pass_threshold: Decimal,
    watch_threshold: Decimal,
    pass_reason: str,
    watch_reason: str,
    block_reason: str,
) -> str:
    if value >= watch_threshold:
        return block_reason
    if value >= pass_threshold:
        return watch_reason
    return pass_reason


def _score_reason(
    exit_tail_guard_score: Decimal,
    *,
    config: ResearchMarketFeeDepthExitTailGuardConfig,
) -> str:
    if exit_tail_guard_score < config.watch_guard_score:
        return GUARD_SCORE_BLOCK_REASON
    if exit_tail_guard_score < config.pass_guard_score:
        return GUARD_SCORE_WATCH_REASON
    return GUARD_SCORE_PASS_REASON


def _status_from_reason_codes(reason_codes: tuple[str, ...]) -> str:
    if any(reason_code in BLOCK_REASON_CODES for reason_code in reason_codes):
        return "block"
    if any(reason_code in WATCH_REASON_CODES for reason_code in reason_codes):
        return "watch"
    return "pass"


def _summary_status(rows: tuple[ResearchMarketFeeDepthExitTailGuardRow, ...]) -> str:
    if not rows:
        return "block"
    statuses = tuple(row.status for row in rows)
    if "block" in statuses:
        return "block"
    if "watch" in statuses:
        return "watch"
    return "pass"


def _summary_reason_codes(
    rows: tuple[ResearchMarketFeeDepthExitTailGuardRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return (EMPTY_REASON,)
    present = {
        reason_code
        for row in rows
        for reason_code in row.reason_codes
        if reason_code not in PASS_REASON_CODES
    }
    if not present:
        return PASS_REASON_CODES
    ordered = tuple(reason_code for reason_code in REPORT_REASON_CODE_ORDER if reason_code in present)
    input_reasons = tuple(sorted(reason_code for reason_code in present if reason_code.startswith("input_")))
    return ordered + input_reasons


def _reason_code_counts(
    rows: tuple[ResearchMarketFeeDepthExitTailGuardRow, ...],
    reason_codes: tuple[str, ...],
) -> tuple[ResearchMarketFeeDepthExitTailGuardReasonCodeCount, ...]:
    if not rows:
        return (
            ResearchMarketFeeDepthExitTailGuardReasonCodeCount(
                reason_code=EMPTY_REASON,
                count=ONE,
                row_ratio=ZERO,
            ),
        )
    counts: Counter[str] = Counter(
        reason_code
        for row in rows
        for reason_code in row.reason_codes
        if reason_code in reason_codes
    )
    total = _decimal_count(len(rows))
    return tuple(
        ResearchMarketFeeDepthExitTailGuardReasonCodeCount(
            reason_code=reason_code,
            count=_decimal_count(counts[reason_code]),
            row_ratio=_ratio(_decimal_count(counts[reason_code]), total),
        )
        for reason_code in reason_codes
    )


def _normalize_observations(
    observations: Iterable[ResearchMarketFeeDepthExitTailGuardObservation],
) -> tuple[ResearchMarketFeeDepthExitTailGuardObservation, ...]:
    if isinstance(observations, (str, bytes)):
        raise ValueError("observations must be an iterable")
    try:
        values = tuple(observations)
    except TypeError as exc:
        raise ValueError("observations must be an iterable") from exc
    seen: set[str] = set()
    for item in values:
        if type(item) is not ResearchMarketFeeDepthExitTailGuardObservation:
            raise ValueError(
                "observations must contain ResearchMarketFeeDepthExitTailGuardObservation",
            )
        _require_hard_flags("input", item)
        if item.research_case_key in seen:
            raise ValueError("research_case_key values must be unique")
        seen.add(item.research_case_key)
    return values


def _observation_sort_key(
    observation: ResearchMarketFeeDepthExitTailGuardObservation,
) -> str:
    return observation.research_case_key


def _status_count(
    rows: tuple[ResearchMarketFeeDepthExitTailGuardRow, ...],
    status: str,
) -> int:
    return sum(row.status == status for row in rows)


def _average_score(
    rows: tuple[ResearchMarketFeeDepthExitTailGuardRow, ...],
) -> Decimal | None:
    if not rows:
        return None
    return _quantize(
        sum((row.exit_tail_guard_score for row in rows), ZERO) / Decimal(len(rows)),
    )


def _min_or_zero(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return ZERO
    return _quantize(min(values))


def _max_or_zero(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return ZERO
    return _quantize(max(values))


def _exit_tail_guard_score(
    *,
    depth_coverage_score: Decimal,
    fee_depth_burden_ratio: Decimal,
    tail_pressure_score: Decimal,
    stale_depth_age_seconds: Decimal,
    manual_guard_pressure: Decimal,
    config: ResearchMarketFeeDepthExitTailGuardConfig,
) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        fee_score = ONE - min(ONE, fee_depth_burden_ratio / config.max_watch_fee_depth_burden_ratio)
        tail_score = ONE - min(ONE, tail_pressure_score / config.max_watch_tail_pressure_score)
        freshness_score = ONE - min(
            ONE,
            stale_depth_age_seconds / config.max_watch_stale_depth_age_seconds,
        )
        manual_score = ONE - min(ONE, manual_guard_pressure / config.max_watch_manual_guard_pressure)
        return _quantize(
            (depth_coverage_score * config.depth_coverage_weight)
            + (fee_score * config.fee_depth_weight)
            + (tail_score * config.tail_pressure_weight)
            + (freshness_score * config.freshness_weight)
            + (manual_score * config.manual_pressure_weight),
        )


def _inverse_ratio_score(value: Decimal, maximum: Decimal) -> Decimal:
    return _quantize(ONE - _bounded_ratio(value, maximum))


def _bounded_ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator <= ZERO:
        raise ValueError("ratio denominator must be positive")
    with localcontext(DECIMAL_CONTEXT):
        return _quantize(min(ONE, numerator / denominator))


def _shortfall_ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    return _quantize(ONE - _bounded_ratio(numerator, denominator))


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return _quantize(numerator / denominator)


def _age_seconds(later: datetime, earlier: datetime) -> Decimal:
    delta = later - earlier
    return _quantize(
        Decimal(delta.days * 86400)
        + Decimal(delta.seconds)
        + (Decimal(delta.microseconds) / Decimal("1000000")),
    )


def _validate_config(config: ResearchMarketFeeDepthExitTailGuardConfig) -> None:
    _require_greater(
        "max_watch_exit_shortfall_ratio",
        config.max_watch_exit_shortfall_ratio,
        "max_pass_exit_shortfall_ratio",
        config.max_pass_exit_shortfall_ratio,
    )
    _require_greater(
        "max_watch_fee_depth_burden_ratio",
        config.max_watch_fee_depth_burden_ratio,
        "max_pass_fee_depth_burden_ratio",
        config.max_pass_fee_depth_burden_ratio,
    )
    _require_greater(
        "max_watch_tail_pressure_score",
        config.max_watch_tail_pressure_score,
        "max_pass_tail_pressure_score",
        config.max_pass_tail_pressure_score,
    )
    _require_greater(
        "max_watch_stale_depth_age_seconds",
        config.max_watch_stale_depth_age_seconds,
        "max_pass_stale_depth_age_seconds",
        config.max_pass_stale_depth_age_seconds,
    )
    _require_greater(
        "max_watch_manual_guard_pressure",
        config.max_watch_manual_guard_pressure,
        "max_pass_manual_guard_pressure",
        config.max_pass_manual_guard_pressure,
    )
    _require_greater(
        "pass_guard_score",
        config.pass_guard_score,
        "watch_guard_score",
        config.watch_guard_score,
    )
    weight_sum = _quantize(
        config.depth_coverage_weight
        + config.fee_depth_weight
        + config.tail_pressure_weight
        + config.freshness_weight
        + config.manual_pressure_weight,
    )
    if weight_sum != ONE:
        raise ValueError("exit tail guard score weights must sum to 1")


def _validate_row(row: ResearchMarketFeeDepthExitTailGuardRow) -> None:
    if row.total_exit_depth != _quantize(row.near_exit_depth + row.far_exit_depth):
        raise ValueError("total_exit_depth must match depth inputs")
    if row.net_exit_depth != _quantize(
        max(ZERO, row.total_exit_depth - row.fee_depth_burden_ratio),
    ):
        raise ValueError("net_exit_depth must match depth and fee inputs")
    if row.tail_pressure_score != _quantize(
        row.tail_loss_probability * row.tail_loss_impact,
    ):
        raise ValueError("tail_pressure_score must match tail inputs")
    if row.status != _status_from_reason_codes(row.reason_codes):
        raise ValueError("status must match reason_codes")


def _validate_report(report: ResearchMarketFeeDepthExitTailGuardReport) -> None:
    if report.input_count != _decimal_count(len(report.rows)):
        raise ValueError("input_count must match rows")
    if report.pass_count != _decimal_count(_status_count(report.rows, "pass")):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _decimal_count(_status_count(report.rows, "watch")):
        raise ValueError("watch_count must match rows")
    if report.block_count != _decimal_count(_status_count(report.rows, "block")):
        raise ValueError("block_count must match rows")
    if report.average_exit_tail_guard_score != _average_score(report.rows):
        raise ValueError("average_exit_tail_guard_score must match rows")
    if report.min_depth_coverage_ratio != _min_or_zero(
        tuple(row.depth_coverage_ratio for row in report.rows),
    ):
        raise ValueError("min_depth_coverage_ratio must match rows")
    if report.max_exit_shortfall_ratio != _max_or_zero(
        tuple(row.exit_shortfall_ratio for row in report.rows),
    ):
        raise ValueError("max_exit_shortfall_ratio must match rows")
    if report.max_fee_depth_burden_ratio != _max_or_zero(
        tuple(row.fee_depth_burden_ratio for row in report.rows),
    ):
        raise ValueError("max_fee_depth_burden_ratio must match rows")
    if report.max_tail_pressure_score != _max_or_zero(
        tuple(row.tail_pressure_score for row in report.rows),
    ):
        raise ValueError("max_tail_pressure_score must match rows")
    if report.max_stale_depth_age_seconds != _max_or_zero(
        tuple(row.stale_depth_age_seconds for row in report.rows),
    ):
        raise ValueError("max_stale_depth_age_seconds must match rows")
    if report.max_manual_guard_pressure != _max_or_zero(
        tuple(row.manual_guard_pressure for row in report.rows),
    ):
        raise ValueError("max_manual_guard_pressure must match rows")
    if report.status != _summary_status(report.rows):
        raise ValueError("status must match rows")
    if report.reason_codes != _summary_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")
    if report.reason_code_counts != _reason_code_counts(report.rows, report.reason_codes):
        raise ValueError("reason_code_counts must match rows")


def _normalize_rows(
    value: object,
) -> tuple[ResearchMarketFeeDepthExitTailGuardRow, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("rows must be a list or tuple")
    rows = tuple(value)
    expected_refs = tuple(f"fee_depth_tail_guard_{index:03d}" for index in range(1, len(rows) + 1))
    if tuple(row.guard_group_ref for row in rows) != expected_refs:
        raise ValueError("rows must use sequential guard_group_ref values")
    for row in rows:
        if type(row) is not ResearchMarketFeeDepthExitTailGuardRow:
            raise ValueError("rows must contain ResearchMarketFeeDepthExitTailGuardRow")
        _require_hard_flags("row", row)
    return rows


def _normalize_reason_code_counts(
    value: object,
) -> tuple[ResearchMarketFeeDepthExitTailGuardReasonCodeCount, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("reason_code_counts must be a list or tuple")
    rows = tuple(value)
    seen: set[str] = set()
    for row in rows:
        if type(row) is not ResearchMarketFeeDepthExitTailGuardReasonCodeCount:
            raise ValueError("reason_code_counts must contain reason code counts")
        _require_hard_flags("reason_code_count", row)
        if row.reason_code in seen:
            raise ValueError("reason_code_counts reason_code values must be unique")
        seen.add(row.reason_code)
    return rows


def _normalize_input_reason_codes(value: object) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ValueError("reason_codes must be a tuple")
    normalized: list[str] = []
    for reason_code in value:
        _require_public_text("reason_codes", reason_code)
        normalized.append(reason_code)
    return tuple(sorted(set(normalized)))


def _normalize_row_reason_codes(value: object) -> tuple[str, ...]:
    if type(value) is not tuple or not value:
        raise ValueError("reason_codes must be a nonempty tuple")
    seen: set[str] = set()
    normalized: list[str] = []
    for reason_code in value:
        _require_output_reason_code("reason_codes", reason_code)
        if reason_code in seen:
            raise ValueError("reason_codes must be unique")
        seen.add(reason_code)
        normalized.append(reason_code)
    return tuple(normalized)


def _normalize_report_reason_codes(value: object) -> tuple[str, ...]:
    return _normalize_row_reason_codes(value)


def _require_output_reason_code(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if value == EMPTY_REASON or value in BASE_REASON_CODES:
        return value
    if value.startswith("input_"):
        _require_public_text(field_name, value)
        return value
    raise ValueError(f"{field_name} must be a supported reason code")


def _require_status(field_name: str, value: object) -> str:
    if type(value) is not str or value not in FEE_DEPTH_EXIT_TAIL_GUARD_STATUSES:
        raise ValueError(f"{field_name} must be one of pass, watch, block")
    return value


def _require_exact_type(value: object, expected_type: type[object], field_name: str) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{field_name} must be exactly {expected_type.__name__}")


def _require_hard_flags(label: str, value: object) -> None:
    if getattr(value, "paper_only", None) is not True:
        raise ValueError(f"paper_only must be True for {label}")
    if getattr(value, "report_only", None) is not True:
        raise ValueError(f"report_only must be True for {label}")
    if getattr(value, "readonly", None) is not True:
        raise ValueError(f"readonly must be True for {label}")


def _require_public_text(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not _is_safe_public_text(value):
        raise ValueError(f"{field_name} must be a safe public identifier")
    if _has_unsafe_public_fragment(value):
        raise ValueError(f"unsafe public value in {field_name}")
    return value


def _is_safe_public_text(value: str) -> bool:
    if not value or len(value) > 96:
        return False
    if value[0] not in "abcdefghijklmnopqrstuvwxyz0123456789":
        return False
    return all(character in SAFE_TEXT_CHARS for character in value)


def _require_greater(
    greater_field_name: str,
    greater_value: Decimal,
    lower_field_name: str,
    lower_value: Decimal,
) -> None:
    if greater_value <= lower_value:
        raise ValueError(f"{greater_field_name} must exceed {lower_field_name}")


def _require_optional_ratio_decimal(field_name: str, value: object) -> Decimal | None:
    if value is None:
        return None
    return _require_ratio_decimal(field_name, value)


def _require_positive_ratio_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_ratio_decimal(field_name, value)
    if normalized <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _require_ratio_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_nonnegative_decimal(field_name, value)
    if normalized > ONE:
        raise ValueError(f"{field_name} must be at most 1.000000")
    return normalized


def _require_positive_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_nonnegative_decimal(field_name, value)
    if normalized <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _require_nonnegative_whole_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_nonnegative_decimal(field_name, value)
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{field_name} must be a whole number")
    return normalized


def _require_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    normalized = _quantize_decimal(field_name, value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _quantize_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return value.quantize(QUANT)


def _quantize(value: Decimal) -> Decimal:
    return value.quantize(QUANT)


def _decimal_count(value: int) -> Decimal:
    if type(value) is not int or value < 0:
        raise ValueError("count source must be a nonnegative int")
    return Decimal(value).quantize(QUANT)


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _payload_value(value: object) -> object:
    if is_dataclass(value) and not isinstance(value, type):
        return _payload_value(asdict(value))
    if type(value) is Decimal:
        if not value.is_finite():
            raise ValueError("payload Decimal value must be finite")
        return format(value, "f")
    if type(value) is datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("payload datetime value must be timezone-aware")
        return value.astimezone(UTC).isoformat()
    if isinstance(value, float):
        raise ValueError("public payload numerics must be Decimal-derived strings")
    if type(value) is int:
        raise ValueError("public payload numerics must be Decimal-derived strings")
    if type(value) is str or type(value) is bool or value is None:
        return value
    if isinstance(value, dict):
        ready: dict[str, object] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("payload keys must be strings")
            ready[key] = _payload_value(item)
        return ready
    if isinstance(value, (list, tuple)):
        return [_payload_value(item) for item in value]
    raise ValueError("value is not payload serializable")


def _derived_report_digest(report: ResearchMarketFeeDepthExitTailGuardReport) -> str:
    payload = _payload_value(report)
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    return _payload_validation_digest(payload)


def _payload_validation_digest(payload: dict[str, Any]) -> str:
    unsigned_payload = dict(payload)
    unsigned_payload.pop("derived_validation_digest", None)
    encoded = json.dumps(unsigned_payload, sort_keys=True, separators=(",", ":")).encode()
    return sha256(encoded).hexdigest()


def _require_hex_digest(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if len(value) != 64 or any(character not in HEX_CHARS for character in value):
        raise ValueError(f"{field_name} must be a lowercase sha256 hex digest")
    return value


def _reject_public_numerics(value: object) -> None:
    if isinstance(value, float) or type(value) is int:
        raise ValueError("public payload numerics must be Decimal-derived strings")
    if isinstance(value, dict):
        for item in value.values():
            _reject_public_numerics(item)
        return
    if isinstance(value, list):
        for item in value:
            _reject_public_numerics(item)


def _reject_unsafe_public_payload(label: str, value: object) -> None:
    if type(value) is str:
        if _has_unsafe_public_fragment(value):
            raise ValueError(f"unsafe public value in {label}")
        return
    if isinstance(value, dict):
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("payload keys must be strings")
            if _has_unsafe_public_fragment(key):
                raise ValueError(f"unsafe public field in {label}")
            _reject_unsafe_public_payload(label, item)
        return
    if isinstance(value, list):
        for item in value:
            _reject_unsafe_public_payload(label, item)


def _has_unsafe_public_fragment(value: str) -> bool:
    normalized = value.lower()
    return any(fragment in normalized for fragment in UNSAFE_PUBLIC_FRAGMENTS)


def _require_public_payload_schema(payload: dict[str, Any]) -> None:
    expected_keys = {
        "generated_at",
        "config_version",
        "input_count",
        "pass_count",
        "watch_count",
        "block_count",
        "average_exit_tail_guard_score",
        "min_depth_coverage_ratio",
        "max_exit_shortfall_ratio",
        "max_fee_depth_burden_ratio",
        "max_tail_pressure_score",
        "max_stale_depth_age_seconds",
        "max_manual_guard_pressure",
        "status",
        "rows",
        "reason_code_counts",
        "reason_codes",
        "derived_validation_digest",
        "paper_only",
        "report_only",
        "readonly",
    }
    if set(payload) != expected_keys:
        raise ValueError("unexpected public payload field")
    if type(payload.get("rows")) is not list:
        raise ValueError("rows must be a public payload list")
    if type(payload.get("reason_code_counts")) is not list:
        raise ValueError("reason_code_counts must be a public payload list")
    if type(payload.get("reason_codes")) is not list:
        raise ValueError("reason_codes must be a public payload list")
