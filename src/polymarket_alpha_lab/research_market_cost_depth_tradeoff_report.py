"""Report-only cost and depth balance scoring for manual research review."""

from __future__ import annotations

from dataclasses import asdict, dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal, ROUND_HALF_UP, localcontext
from hashlib import sha256
import json
import re
from typing import Any, Mapping, Sequence


DEFAULT_RESEARCH_MARKET_COST_DEPTH_TRADEOFF_REPORT_CONFIG_VERSION = (
    "cost-depth-balance-report-v0"
)
QUANTUM = Decimal("0.000001")
COUNT_QUANTUM = Decimal("1")
ZERO = Decimal("0").quantize(QUANTUM)
ONE = Decimal("1").quantize(QUANTUM)
DECIMAL_CONTEXT_PRECISION = 28
STATUSES = ("pass", "watch", "block")
STATUS_WEIGHT = {"block": 0, "watch": 1, "pass": 2}
PUBLIC_IDENTIFIER_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,127}$")
DIGEST_RE = re.compile(r"^[0-9a-f]{64}$")
FLAG_FIELDS = ("paper_only", "report_only", "readonly")
REPORT_PAYLOAD_FIELDS = (
    "generated_at",
    "config_version",
    "input_count",
    "row_count",
    "pass_count",
    "watch_count",
    "block_count",
    "average_cost_pressure",
    "min_depth_score",
    "max_book_age_seconds",
    "max_settlement_friction",
    "status",
    "reason_codes",
    "rows",
    "derived_validation_digest",
    "paper_only",
    "report_only",
    "readonly",
)
DIGEST_PAYLOAD_FIELDS = (
    "generated_at",
    "config_version",
    "report_digest",
    "report_status",
    "row_count",
    "pass_count",
    "watch_count",
    "block_count",
    "average_cost_pressure",
    "min_depth_score",
    "max_book_age_seconds",
    "max_settlement_friction",
    "reason_codes",
    "paper_only",
    "report_only",
    "readonly",
)
ROW_PAYLOAD_FIELDS = (
    "public_case_key",
    "observed_at",
    "spread",
    "fee_drag",
    "slippage_cushion",
    "near_depth",
    "mid_depth",
    "far_depth",
    "book_age_seconds",
    "volatility",
    "settlement_friction",
    "depth_score",
    "depth_gap",
    "slippage_shortfall",
    "cost_pressure",
    "status",
    "reason_codes",
    "paper_only",
    "report_only",
    "readonly",
)
UNSAFE_PUBLIC_FRAGMENTS = (
    "candidate",
    "market_id",
    "market_slug",
    "slug",
    "question",
    "source_url",
    "source_text",
    "url",
    "table",
    "d" + "sn",
    "tok" + "en",
    "wal" + "let",
    "or" + "der",
    "tra" + "de",
    "live",
    "pos" + "ition",
    "size",
    "rec" + "ommend",
    "buy",
    "sell",
)
REASON_CODE_ORDER = (
    "no_cost_depth_observations",
    "cost_depth_balance_pass",
    "cost_depth_balance_watch",
    "cost_depth_balance_block",
    "spread_pass",
    "spread_watch",
    "spread_block",
    "fee_drag_pass",
    "fee_drag_watch",
    "fee_drag_block",
    "slippage_shortfall_pass",
    "slippage_shortfall_watch",
    "slippage_shortfall_block",
    "depth_band_pass",
    "depth_band_watch",
    "depth_band_block",
    "book_age_pass",
    "book_age_watch",
    "book_age_block",
    "volatility_pass",
    "volatility_watch",
    "volatility_block",
    "settlement_friction_pass",
    "settlement_friction_watch",
    "settlement_friction_block",
)


@dataclass(frozen=True)
class CostDepthTradeoffConfig:
    config_version: str = DEFAULT_RESEARCH_MARKET_COST_DEPTH_TRADEOFF_REPORT_CONFIG_VERSION
    watch_cost_pressure_threshold: Decimal = Decimal("0.040000")
    block_cost_pressure_threshold: Decimal = Decimal("0.080000")
    watch_spread_threshold: Decimal = Decimal("0.020000")
    block_spread_threshold: Decimal = Decimal("0.050000")
    watch_fee_drag_threshold: Decimal = Decimal("0.010000")
    block_fee_drag_threshold: Decimal = Decimal("0.025000")
    watch_slippage_shortfall_threshold: Decimal = Decimal("0.010000")
    block_slippage_shortfall_threshold: Decimal = Decimal("0.030000")
    min_pass_depth_score: Decimal = Decimal("0.750000")
    min_watch_depth_score: Decimal = Decimal("0.400000")
    watch_book_age_seconds: Decimal = Decimal("600")
    block_book_age_seconds: Decimal = Decimal("3600")
    watch_volatility_threshold: Decimal = Decimal("0.120000")
    block_volatility_threshold: Decimal = Decimal("0.250000")
    watch_settlement_friction_threshold: Decimal = Decimal("0.020000")
    block_settlement_friction_threshold: Decimal = Decimal("0.050000")
    near_depth_target: Decimal = Decimal("1000.000000")
    mid_depth_target: Decimal = Decimal("500.000000")
    far_depth_target: Decimal = Decimal("250.000000")
    near_depth_weight: Decimal = Decimal("0.500000")
    mid_depth_weight: Decimal = Decimal("0.300000")
    far_depth_weight: Decimal = Decimal("0.200000")
    depth_gap_cost_weight: Decimal = Decimal("0.040000")
    book_age_cost_weight: Decimal = Decimal("0.010000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, CostDepthTradeoffConfig, "config")
        _require_public_identifier("config_version", self.config_version)
        for field_name in (
            "watch_cost_pressure_threshold",
            "block_cost_pressure_threshold",
            "watch_spread_threshold",
            "block_spread_threshold",
            "watch_fee_drag_threshold",
            "block_fee_drag_threshold",
            "watch_slippage_shortfall_threshold",
            "block_slippage_shortfall_threshold",
            "min_pass_depth_score",
            "min_watch_depth_score",
            "watch_volatility_threshold",
            "block_volatility_threshold",
            "watch_settlement_friction_threshold",
            "block_settlement_friction_threshold",
            "near_depth_weight",
            "mid_depth_weight",
            "far_depth_weight",
            "depth_gap_cost_weight",
            "book_age_cost_weight",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "watch_book_age_seconds",
            "block_book_age_seconds",
            "near_depth_target",
            "mid_depth_target",
            "far_depth_target",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_positive_decimal(field_name, getattr(self, field_name)),
            )
        _require_increasing(
            "watch_cost_pressure_threshold",
            self.watch_cost_pressure_threshold,
            "block_cost_pressure_threshold",
            self.block_cost_pressure_threshold,
        )
        _require_increasing(
            "watch_spread_threshold",
            self.watch_spread_threshold,
            "block_spread_threshold",
            self.block_spread_threshold,
        )
        _require_increasing(
            "watch_fee_drag_threshold",
            self.watch_fee_drag_threshold,
            "block_fee_drag_threshold",
            self.block_fee_drag_threshold,
        )
        _require_increasing(
            "watch_slippage_shortfall_threshold",
            self.watch_slippage_shortfall_threshold,
            "block_slippage_shortfall_threshold",
            self.block_slippage_shortfall_threshold,
        )
        if self.min_pass_depth_score <= self.min_watch_depth_score:
            raise ValueError("min_pass_depth_score must exceed min_watch_depth_score")
        _require_increasing(
            "watch_book_age_seconds",
            self.watch_book_age_seconds,
            "block_book_age_seconds",
            self.block_book_age_seconds,
        )
        _require_increasing(
            "watch_volatility_threshold",
            self.watch_volatility_threshold,
            "block_volatility_threshold",
            self.block_volatility_threshold,
        )
        _require_increasing(
            "watch_settlement_friction_threshold",
            self.watch_settlement_friction_threshold,
            "block_settlement_friction_threshold",
            self.block_settlement_friction_threshold,
        )
        weight_sum = _quantize(
            self.near_depth_weight + self.mid_depth_weight + self.far_depth_weight,
        )
        if weight_sum != ONE:
            raise ValueError("depth weights must sum to 1")
        _require_hard_flags("config", self)
        _reject_unsafe_public_payload("config", self)


@dataclass(frozen=True)
class CostDepthTradeoffObservation:
    public_case_key: str
    observed_at: datetime
    spread: Decimal
    fee_drag: Decimal
    slippage_cushion: Decimal
    near_depth: Decimal
    mid_depth: Decimal
    far_depth: Decimal
    volatility: Decimal
    settlement_friction: Decimal
    upstream_reason_codes: tuple[str, ...] = ()
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, CostDepthTradeoffObservation, "observation")
        _require_public_identifier("public_case_key", self.public_case_key)
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in (
            "spread",
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
        for field_name in ("near_depth", "mid_depth", "far_depth"):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "upstream_reason_codes",
            _normalize_reason_codes(
                self.upstream_reason_codes,
                allow_empty=True,
                allow_public_input_codes=True,
            ),
        )
        _require_hard_flags("observation", self)
        _reject_unsafe_public_payload("observation", self)


@dataclass(frozen=True)
class CostDepthTradeoffRow:
    public_case_key: str
    observed_at: datetime
    spread: Decimal
    fee_drag: Decimal
    slippage_cushion: Decimal
    near_depth: Decimal
    mid_depth: Decimal
    far_depth: Decimal
    book_age_seconds: Decimal
    volatility: Decimal
    settlement_friction: Decimal
    depth_score: Decimal
    depth_gap: Decimal
    slippage_shortfall: Decimal
    cost_pressure: Decimal
    status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, CostDepthTradeoffRow, "row")
        _require_public_identifier("public_case_key", self.public_case_key)
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in (
            "spread",
            "fee_drag",
            "slippage_cushion",
            "book_age_seconds",
            "volatility",
            "settlement_friction",
            "depth_score",
            "depth_gap",
            "slippage_shortfall",
            "cost_pressure",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "spread",
            "fee_drag",
            "slippage_cushion",
            "volatility",
            "settlement_friction",
            "depth_score",
            "depth_gap",
            "slippage_shortfall",
            "cost_pressure",
        ):
            if getattr(self, field_name) > ONE:
                raise ValueError(f"{field_name} must be at most one")
        for field_name in ("near_depth", "mid_depth", "far_depth"):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        _require_status("status", self.status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes, allow_empty=False),
        )
        _validate_row(self)
        _require_hard_flags("row", self)
        _reject_unsafe_public_payload("row", self)


@dataclass(frozen=True)
class CostDepthTradeoffReport:
    generated_at: datetime
    config_version: str
    input_count: Decimal
    row_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    average_cost_pressure: Decimal | None
    min_depth_score: Decimal | None
    max_book_age_seconds: Decimal
    max_settlement_friction: Decimal
    status: str
    reason_codes: tuple[str, ...]
    rows: tuple[CostDepthTradeoffRow, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, CostDepthTradeoffReport, "report")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_identifier("config_version", self.config_version)
        for field_name in ("input_count", "row_count", "pass_count", "watch_count", "block_count"):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_count_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in ("max_book_age_seconds", "max_settlement_friction"):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        if self.max_settlement_friction > ONE:
            raise ValueError("max_settlement_friction must be at most one")
        object.__setattr__(
            self,
            "average_cost_pressure",
            _require_optional_ratio_decimal(
                "average_cost_pressure",
                self.average_cost_pressure,
            ),
        )
        object.__setattr__(
            self,
            "min_depth_score",
            _require_optional_ratio_decimal("min_depth_score", self.min_depth_score),
        )
        _require_status("status", self.status)
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes, allow_empty=False),
        )
        _require_hard_flags("report", self)
        _validate_report(self)
        _reject_unsafe_public_payload("report", self)
        expected_digest = _report_derived_validation_digest(self)
        if self.derived_validation_digest:
            _require_sha256_digest("derived_validation_digest", self.derived_validation_digest)
            if self.derived_validation_digest != expected_digest:
                raise ValueError("derived_validation_digest must match report fields")
        else:
            object.__setattr__(self, "derived_validation_digest", expected_digest)

    @property
    def payload(self) -> dict[str, Any]:
        return research_market_cost_depth_tradeoff_report_payload(self)


@dataclass(frozen=True)
class CostDepthTradeoffReportDigest:
    generated_at: datetime
    config_version: str
    report_digest: str
    report_status: str
    row_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    average_cost_pressure: Decimal | None
    min_depth_score: Decimal | None
    max_book_age_seconds: Decimal
    max_settlement_friction: Decimal
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, CostDepthTradeoffReportDigest, "digest")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_identifier("config_version", self.config_version)
        _require_sha256_digest("report_digest", self.report_digest)
        _require_status("report_status", self.report_status)
        for field_name in ("row_count", "pass_count", "watch_count", "block_count"):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_count_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "average_cost_pressure",
            _require_optional_ratio_decimal(
                "average_cost_pressure",
                self.average_cost_pressure,
            ),
        )
        object.__setattr__(
            self,
            "min_depth_score",
            _require_optional_ratio_decimal("min_depth_score", self.min_depth_score),
        )
        for field_name in ("max_book_age_seconds", "max_settlement_friction"):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        if self.max_settlement_friction > ONE:
            raise ValueError("max_settlement_friction must be at most one")
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes, allow_empty=False),
        )
        _require_hard_flags("digest", self)
        _reject_unsafe_public_payload("digest", self)

    @property
    def payload(self) -> dict[str, Any]:
        return research_market_cost_depth_tradeoff_report_payload(self)


def build_research_market_cost_depth_tradeoff_report(
    observations: Sequence[CostDepthTradeoffObservation],
    *,
    config: CostDepthTradeoffConfig,
    generated_at: datetime,
) -> CostDepthTradeoffReport:
    """Build a local, read-only cost and depth balance report."""

    if type(config) is not CostDepthTradeoffConfig:
        raise ValueError("config must be a CostDepthTradeoffConfig")
    _require_hard_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    normalized = _normalize_observations(observations, generated_at_utc)
    rows = tuple(
        sorted(
            (_row_for_observation(item, config, generated_at_utc) for item in normalized),
            key=_row_key,
        ),
    )
    values: dict[str, object] = {
        "generated_at": generated_at_utc,
        "config_version": config.config_version,
        "input_count": _count(len(normalized)),
        "row_count": _count(len(rows)),
        "pass_count": _count(_status_count(rows, "pass")),
        "watch_count": _count(_status_count(rows, "watch")),
        "block_count": _count(_status_count(rows, "block")),
        "average_cost_pressure": _average_or_none(
            tuple(row.cost_pressure for row in rows),
        ),
        "min_depth_score": min((row.depth_score for row in rows), default=None),
        "max_book_age_seconds": max((row.book_age_seconds for row in rows), default=ZERO),
        "max_settlement_friction": max(
            (row.settlement_friction for row in rows),
            default=ZERO,
        ),
        "status": _report_status(rows),
        "reason_codes": _report_reason_codes(rows),
        "rows": rows,
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    return CostDepthTradeoffReport(
        **values,
        derived_validation_digest=_derived_validation_digest(values),
    )


def research_market_cost_depth_tradeoff_report_payload(
    value: CostDepthTradeoffReport | CostDepthTradeoffReportDigest | dict[str, Any],
) -> dict[str, Any]:
    if type(value) is CostDepthTradeoffReport:
        _require_hard_flags("report", value)
        if value.derived_validation_digest != _report_derived_validation_digest(value):
            raise ValueError("derived_validation_digest must match report fields")
        payload = _json_ready(value)
    elif type(value) is CostDepthTradeoffReportDigest:
        _require_hard_flags("digest", value)
        payload = _json_ready(value)
    elif type(value) is dict:
        payload = _json_ready(value)
    else:
        raise ValueError(
            "value must be a CostDepthTradeoffReport or CostDepthTradeoffReportDigest",
        )
    if type(payload) is not dict:
        raise ValueError("payload must be a JSON object")
    _require_hard_flags("payload", _DictFlags(payload))
    _reject_unsafe_public_payload("payload", payload, allow_json_containers=True)
    _validate_payload_digest_if_present(payload)
    _validate_public_payload_shape(payload)
    return payload


def research_market_cost_depth_tradeoff_report_digest(
    report: CostDepthTradeoffReport,
) -> CostDepthTradeoffReportDigest:
    if type(report) is not CostDepthTradeoffReport:
        raise ValueError("report must be a CostDepthTradeoffReport")
    _require_hard_flags("report", report)
    if report.derived_validation_digest != _report_derived_validation_digest(report):
        raise ValueError("derived_validation_digest must match report fields")
    return CostDepthTradeoffReportDigest(
        generated_at=report.generated_at,
        config_version=report.config_version,
        report_digest=report.derived_validation_digest,
        report_status=report.status,
        row_count=report.row_count,
        pass_count=report.pass_count,
        watch_count=report.watch_count,
        block_count=report.block_count,
        average_cost_pressure=report.average_cost_pressure,
        min_depth_score=report.min_depth_score,
        max_book_age_seconds=report.max_book_age_seconds,
        max_settlement_friction=report.max_settlement_friction,
        reason_codes=report.reason_codes,
    )


@dataclass(frozen=True)
class _DictFlags:
    value: Mapping[str, Any]

    @property
    def paper_only(self) -> object:
        return self.value.get("paper_only")

    @property
    def report_only(self) -> object:
        return self.value.get("report_only")

    @property
    def readonly(self) -> object:
        return self.value.get("readonly")


def _row_for_observation(
    observation: CostDepthTradeoffObservation,
    config: CostDepthTradeoffConfig,
    generated_at: datetime,
) -> CostDepthTradeoffRow:
    book_age_seconds = _age_seconds(generated_at, observation.observed_at)
    depth_score = _depth_score(observation, config)
    depth_gap = _quantize(ONE - depth_score)
    slippage_shortfall = _quantize(max(ZERO, observation.volatility - observation.slippage_cushion))
    cost_pressure = _cost_pressure(
        observation=observation,
        depth_gap=depth_gap,
        slippage_shortfall=slippage_shortfall,
        book_age_seconds=book_age_seconds,
        config=config,
    )
    status = _row_status(
        spread=observation.spread,
        fee_drag=observation.fee_drag,
        slippage_shortfall=slippage_shortfall,
        depth_score=depth_score,
        book_age_seconds=book_age_seconds,
        volatility=observation.volatility,
        settlement_friction=observation.settlement_friction,
        cost_pressure=cost_pressure,
        config=config,
    )
    return CostDepthTradeoffRow(
        public_case_key=observation.public_case_key,
        observed_at=observation.observed_at,
        spread=observation.spread,
        fee_drag=observation.fee_drag,
        slippage_cushion=observation.slippage_cushion,
        near_depth=observation.near_depth,
        mid_depth=observation.mid_depth,
        far_depth=observation.far_depth,
        book_age_seconds=book_age_seconds,
        volatility=observation.volatility,
        settlement_friction=observation.settlement_friction,
        depth_score=depth_score,
        depth_gap=depth_gap,
        slippage_shortfall=slippage_shortfall,
        cost_pressure=cost_pressure,
        status=status,
        reason_codes=_row_reason_codes(
            upstream_reason_codes=observation.upstream_reason_codes,
            status=status,
            spread=observation.spread,
            fee_drag=observation.fee_drag,
            slippage_shortfall=slippage_shortfall,
            depth_score=depth_score,
            book_age_seconds=book_age_seconds,
            volatility=observation.volatility,
            settlement_friction=observation.settlement_friction,
            config=config,
        ),
    )


def _depth_score(
    observation: CostDepthTradeoffObservation,
    config: CostDepthTradeoffConfig,
) -> Decimal:
    near_score = _capped_ratio(observation.near_depth, config.near_depth_target)
    mid_score = _capped_ratio(observation.mid_depth, config.mid_depth_target)
    far_score = _capped_ratio(observation.far_depth, config.far_depth_target)
    return _quantize(
        near_score * config.near_depth_weight
        + mid_score * config.mid_depth_weight
        + far_score * config.far_depth_weight,
    )


def _cost_pressure(
    *,
    observation: CostDepthTradeoffObservation,
    depth_gap: Decimal,
    slippage_shortfall: Decimal,
    book_age_seconds: Decimal,
    config: CostDepthTradeoffConfig,
) -> Decimal:
    age_pressure = _capped_ratio(book_age_seconds, config.block_book_age_seconds)
    with localcontext() as context:
        context.prec = DECIMAL_CONTEXT_PRECISION
        value = (
            observation.spread
            + observation.fee_drag
            + observation.settlement_friction
            + slippage_shortfall
            + (depth_gap * config.depth_gap_cost_weight)
            + (age_pressure * config.book_age_cost_weight)
        )
    return _clamp_ratio(value)


def _row_status(
    *,
    spread: Decimal,
    fee_drag: Decimal,
    slippage_shortfall: Decimal,
    depth_score: Decimal,
    book_age_seconds: Decimal,
    volatility: Decimal,
    settlement_friction: Decimal,
    cost_pressure: Decimal,
    config: CostDepthTradeoffConfig,
) -> str:
    if (
        cost_pressure >= config.block_cost_pressure_threshold
        or spread >= config.block_spread_threshold
        or fee_drag >= config.block_fee_drag_threshold
        or slippage_shortfall >= config.block_slippage_shortfall_threshold
        or depth_score < config.min_watch_depth_score
        or book_age_seconds >= config.block_book_age_seconds
        or volatility >= config.block_volatility_threshold
        or settlement_friction >= config.block_settlement_friction_threshold
    ):
        return "block"
    if (
        cost_pressure >= config.watch_cost_pressure_threshold
        or spread >= config.watch_spread_threshold
        or fee_drag >= config.watch_fee_drag_threshold
        or slippage_shortfall >= config.watch_slippage_shortfall_threshold
        or depth_score < config.min_pass_depth_score
        or book_age_seconds >= config.watch_book_age_seconds
        or volatility >= config.watch_volatility_threshold
        or settlement_friction >= config.watch_settlement_friction_threshold
    ):
        return "watch"
    return "pass"


def _row_reason_codes(
    *,
    upstream_reason_codes: tuple[str, ...],
    status: str,
    spread: Decimal,
    fee_drag: Decimal,
    slippage_shortfall: Decimal,
    depth_score: Decimal,
    book_age_seconds: Decimal,
    volatility: Decimal,
    settlement_friction: Decimal,
    config: CostDepthTradeoffConfig,
) -> tuple[str, ...]:
    reason_codes = [
        f"cost_depth_balance_{status}",
        _high_value_reason(
            "spread",
            spread,
            config.watch_spread_threshold,
            config.block_spread_threshold,
        ),
        _high_value_reason(
            "fee_drag",
            fee_drag,
            config.watch_fee_drag_threshold,
            config.block_fee_drag_threshold,
        ),
        _high_value_reason(
            "slippage_shortfall",
            slippage_shortfall,
            config.watch_slippage_shortfall_threshold,
            config.block_slippage_shortfall_threshold,
        ),
        _depth_reason(depth_score, config),
        _high_value_reason(
            "book_age",
            book_age_seconds,
            config.watch_book_age_seconds,
            config.block_book_age_seconds,
        ),
        _high_value_reason(
            "volatility",
            volatility,
            config.watch_volatility_threshold,
            config.block_volatility_threshold,
        ),
        _high_value_reason(
            "settlement_friction",
            settlement_friction,
            config.watch_settlement_friction_threshold,
            config.block_settlement_friction_threshold,
        ),
    ]
    reason_codes.extend(f"input_{code}" for code in upstream_reason_codes)
    return _normalize_reason_codes(tuple(reason_codes), allow_empty=False)


def _high_value_reason(
    prefix: str,
    value: Decimal,
    watch_threshold: Decimal,
    block_threshold: Decimal,
) -> str:
    if value >= block_threshold:
        return f"{prefix}_block"
    if value >= watch_threshold:
        return f"{prefix}_watch"
    return f"{prefix}_pass"


def _depth_reason(depth_score: Decimal, config: CostDepthTradeoffConfig) -> str:
    if depth_score < config.min_watch_depth_score:
        return "depth_band_block"
    if depth_score < config.min_pass_depth_score:
        return "depth_band_watch"
    return "depth_band_pass"


def _report_status(rows: tuple[CostDepthTradeoffRow, ...]) -> str:
    if not rows or any(row.status == "block" for row in rows):
        return "block"
    if any(row.status == "watch" for row in rows):
        return "watch"
    return "pass"


def _report_reason_codes(rows: tuple[CostDepthTradeoffRow, ...]) -> tuple[str, ...]:
    if not rows:
        return ("no_cost_depth_observations",)
    if all(row.status == "pass" for row in rows):
        return ("cost_depth_balance_pass",)
    return _normalize_reason_codes(
        tuple(code for row in rows for code in row.reason_codes),
        allow_empty=False,
    )


def _normalize_observations(
    observations: Sequence[CostDepthTradeoffObservation],
    generated_at: datetime,
) -> tuple[CostDepthTradeoffObservation, ...]:
    if isinstance(observations, (str, bytes)) or not isinstance(observations, Sequence):
        raise ValueError("observations must be a sequence")
    normalized = tuple(observations)
    seen_keys: set[str] = set()
    for item in normalized:
        if type(item) is not CostDepthTradeoffObservation:
            raise ValueError("observations must contain CostDepthTradeoffObservation values")
        _require_hard_flags("observation", item)
        if item.observed_at > generated_at:
            raise ValueError("observed_at must not be after generated_at")
        if item.public_case_key in seen_keys:
            raise ValueError("observations must contain unique public_case_key values")
        seen_keys.add(item.public_case_key)
    return normalized


def _normalize_rows(rows: Sequence[CostDepthTradeoffRow]) -> tuple[CostDepthTradeoffRow, ...]:
    if isinstance(rows, (str, bytes)) or not isinstance(rows, Sequence):
        raise ValueError("rows must be a sequence")
    normalized = tuple(rows)
    for row in normalized:
        if type(row) is not CostDepthTradeoffRow:
            raise ValueError("rows must contain CostDepthTradeoffRow values")
        _require_hard_flags("row", row)
    return tuple(sorted(normalized, key=_row_key))


def _row_key(row: CostDepthTradeoffRow) -> tuple[int, Decimal, Decimal, str]:
    return (
        STATUS_WEIGHT[row.status],
        -row.cost_pressure,
        -row.book_age_seconds,
        row.public_case_key,
    )


def _status_count(rows: tuple[CostDepthTradeoffRow, ...], status: str) -> int:
    return sum(1 for row in rows if row.status == status)


def _validate_row(row: CostDepthTradeoffRow) -> None:
    if row.depth_score + row.depth_gap != ONE:
        raise ValueError("depth_gap must match depth_score")
    if f"cost_depth_balance_{row.status}" not in row.reason_codes:
        raise ValueError("row status must match reason_codes")
    if row.status == "pass" and any(code.endswith("_block") for code in row.reason_codes):
        raise ValueError("pass rows must not include block reason codes")


def _validate_report(report: CostDepthTradeoffReport) -> None:
    if report.row_count != _count(len(report.rows)):
        raise ValueError("row_count must match rows")
    if report.input_count < report.row_count:
        raise ValueError("input_count must cover rows")
    if report.pass_count != _count(_status_count(report.rows, "pass")):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _count(_status_count(report.rows, "watch")):
        raise ValueError("watch_count must match rows")
    if report.block_count != _count(_status_count(report.rows, "block")):
        raise ValueError("block_count must match rows")
    if report.average_cost_pressure != _average_or_none(
        tuple(row.cost_pressure for row in report.rows),
    ):
        raise ValueError("average_cost_pressure must match rows")
    if report.min_depth_score != min((row.depth_score for row in report.rows), default=None):
        raise ValueError("min_depth_score must match rows")
    if report.max_book_age_seconds != max(
        (row.book_age_seconds for row in report.rows),
        default=ZERO,
    ):
        raise ValueError("max_book_age_seconds must match rows")
    if report.max_settlement_friction != max(
        (row.settlement_friction for row in report.rows),
        default=ZERO,
    ):
        raise ValueError("max_settlement_friction must match rows")
    if report.status != _report_status(report.rows):
        raise ValueError("status must match rows")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")


def _require_exact_type(value: object, expected_type: type[object], label: str) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{label} must be exactly {expected_type.__name__}")


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in FLAG_FIELDS:
        if getattr(value, field_name) is not True:
            raise ValueError(f"{field_name} must be True for {label}")


def _require_public_identifier(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not PUBLIC_IDENTIFIER_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a public identifier")
    if value.isdecimal():
        raise ValueError(f"{field_name} must be a public identifier")
    _reject_unsafe_public_string(field_name, value)
    return value


def _require_status(field_name: str, value: object) -> str:
    if type(value) is not str or value not in STATUSES:
        raise ValueError(f"{field_name} must be one of pass, watch, block")
    return value


def _require_sha256_digest(field_name: str, value: object) -> str:
    if type(value) is not str or not DIGEST_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a lowercase sha256 digest")
    return value


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return _quantize(value)


def _require_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _require_positive_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_nonnegative_decimal(field_name, value)
    if normalized <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _require_ratio_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_nonnegative_decimal(field_name, value)
    if normalized > ONE:
        raise ValueError(f"{field_name} must be at most one")
    return normalized


def _require_optional_ratio_decimal(field_name: str, value: object) -> Decimal | None:
    if value is None:
        return None
    return _require_ratio_decimal(field_name, value)


def _require_nonnegative_count_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_nonnegative_decimal(field_name, value)
    if normalized != normalized.quantize(COUNT_QUANTUM):
        raise ValueError(f"{field_name} must be a whole Decimal count")
    return normalized.quantize(COUNT_QUANTUM)


def _require_increasing(
    lower_name: str,
    lower_value: Decimal,
    upper_name: str,
    upper_value: Decimal,
) -> None:
    if lower_value >= upper_value:
        raise ValueError(f"{lower_name} must be below {upper_name}")


def _normalize_reason_codes(
    reason_codes: Sequence[str],
    *,
    allow_empty: bool,
    allow_public_input_codes: bool = False,
) -> tuple[str, ...]:
    if isinstance(reason_codes, (str, bytes)) or not isinstance(reason_codes, Sequence):
        raise ValueError("reason_codes must be a sequence")
    normalized: list[str] = []
    for reason_code in reason_codes:
        _require_public_identifier("reason_code", reason_code)
        if (
            reason_code not in REASON_CODE_ORDER
            and not reason_code.startswith("input_")
            and not allow_public_input_codes
        ):
            raise ValueError("reason_code must be supported")
        if reason_code not in normalized:
            normalized.append(reason_code)
    if not normalized and not allow_empty:
        raise ValueError("reason_codes must be nonempty")
    ordered = [
        reason_code for reason_code in REASON_CODE_ORDER if reason_code in normalized
    ]
    extras = sorted(
        reason_code for reason_code in normalized if reason_code not in REASON_CODE_ORDER
    )
    return tuple(ordered + extras)


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _age_seconds(generated_at: datetime, observed_at: datetime) -> Decimal:
    delta = generated_at - observed_at
    return _quantize(
        Decimal(delta.days * 86_400)
        + Decimal(delta.seconds)
        + (Decimal(delta.microseconds) / Decimal("1000000")),
    )


def _capped_ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator <= ZERO:
        raise ValueError("denominator must be positive")
    return _quantize(min(ONE, numerator / denominator))


def _clamp_ratio(value: Decimal) -> Decimal:
    normalized = _quantize(value)
    if normalized < ZERO:
        return ZERO
    if normalized > ONE:
        return ONE
    return normalized


def _average_or_none(values: tuple[Decimal, ...]) -> Decimal | None:
    if not values:
        return None
    return _quantize(sum(values, ZERO) / Decimal(len(values)))


def _count(value: int) -> Decimal:
    if value < 0:
        raise ValueError("count must be nonnegative")
    return Decimal(value).quantize(COUNT_QUANTUM)


def _quantize(value: Decimal) -> Decimal:
    return value.quantize(QUANTUM, rounding=ROUND_HALF_UP)


def _report_derived_validation_digest(report: CostDepthTradeoffReport) -> str:
    values = asdict(report)
    values.pop("derived_validation_digest", None)
    return _derived_validation_digest(values)


def _derived_validation_digest(values: Mapping[str, object]) -> str:
    payload = _json_ready(values)
    _reject_unsafe_public_payload(
        "derived_validation_digest payload",
        payload,
        allow_json_containers=True,
    )
    canonical = json.dumps(
        payload,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    )
    return sha256(canonical.encode("utf-8")).hexdigest()


def _validate_payload_digest_if_present(payload: dict[str, Any]) -> None:
    if "derived_validation_digest" not in payload:
        if "report_digest" in payload:
            _require_sha256_digest("report_digest", payload["report_digest"])
            return
        raise ValueError("derived_validation_digest must be present")
    digest = payload["derived_validation_digest"]
    _require_sha256_digest("derived_validation_digest", digest)
    values = dict(payload)
    values.pop("derived_validation_digest", None)
    expected = _derived_validation_digest(values)
    if digest != expected:
        raise ValueError("derived_validation_digest must match payload fields")


def _validate_public_payload_shape(payload: dict[str, Any]) -> None:
    if "report_digest" in payload and "derived_validation_digest" not in payload:
        _require_exact_payload_fields("digest payload", payload, DIGEST_PAYLOAD_FIELDS)
        _require_public_identifier("config_version", payload["config_version"])
        _require_sha256_digest("report_digest", payload["report_digest"])
        _require_status("report_status", payload["report_status"])
        _normalize_reason_codes(payload["reason_codes"], allow_empty=False)
        return

    _require_exact_payload_fields("report payload", payload, REPORT_PAYLOAD_FIELDS)
    _require_public_identifier("config_version", payload["config_version"])
    _require_status("status", payload["status"])
    _normalize_reason_codes(payload["reason_codes"], allow_empty=False)
    rows = payload["rows"]
    if type(rows) is not list:
        raise ValueError("rows must be a list")
    for row in rows:
        if type(row) is not dict:
            raise ValueError("rows must contain public row objects")
        _require_exact_payload_fields("row payload", row, ROW_PAYLOAD_FIELDS)
        _require_public_identifier("public_case_key", row["public_case_key"])
        _require_status("status", row["status"])
        _normalize_reason_codes(row["reason_codes"], allow_empty=False)


def _require_exact_payload_fields(
    label: str,
    payload: Mapping[str, object],
    allowed_fields: tuple[str, ...],
) -> None:
    allowed = set(allowed_fields)
    actual = set(payload)
    unexpected = sorted(actual - allowed)
    if unexpected:
        raise ValueError(f"{label} has unexpected public field")
    missing = [field_name for field_name in allowed_fields if field_name not in payload]
    if missing:
        raise ValueError(f"{label} is missing public field")


def _json_ready(value: Any) -> Any:
    if value is None:
        return None
    if is_dataclass(value) and not isinstance(value, type):
        return _json_ready(asdict(value))
    if type(value) is Decimal:
        if not value.is_finite():
            raise ValueError("Decimal payload value must be finite")
        return str(value)
    if type(value) is datetime:
        return _as_utc("datetime payload value", value).isoformat()
    if type(value) is bool or type(value) is str:
        return value
    if type(value) is int or isinstance(value, float):
        raise ValueError("numeric payload values must be Decimal strings")
    if isinstance(value, Mapping):
        ready: dict[str, Any] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            ready[key] = _json_ready(item)
        return ready
    if isinstance(value, (list, tuple)):
        return [_json_ready(item) for item in value]
    raise ValueError("payload value is not JSON serializable")


def _reject_unsafe_public_payload(
    label: str,
    value: object,
    path: str = "",
    *,
    allow_json_containers: bool = False,
) -> None:
    current_path = path or label
    if is_dataclass(value) and not isinstance(value, type):
        for field in fields(value):
            _reject_unsafe_public_key(field.name, current_path)
            _reject_unsafe_public_payload(
                label,
                getattr(value, field.name),
                field.name if not path else f"{path}.{field.name}",
                allow_json_containers=allow_json_containers,
            )
        return
    if isinstance(value, Mapping):
        if not allow_json_containers:
            raise ValueError(f"{current_path} must remain constructor-normalized")
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            _reject_unsafe_public_key(key, current_path)
            _reject_unsafe_public_payload(
                label,
                item,
                key if not path else f"{path}.{key}",
                allow_json_containers=True,
            )
        return
    if isinstance(value, (list, tuple)):
        if type(value) is list and not allow_json_containers:
            raise ValueError(f"{current_path} must remain constructor-normalized")
        for index, item in enumerate(value):
            _reject_unsafe_public_payload(
                label,
                item,
                f"{current_path}[{index}]",
                allow_json_containers=allow_json_containers,
            )
        return
    if type(value) is str:
        _reject_unsafe_public_string(current_path, value)
        return
    if value is None or type(value) is bool or type(value) is Decimal or type(value) is datetime:
        return
    raise ValueError(f"{current_path} is not a supported public payload value")


def _reject_unsafe_public_key(key: str, path: str) -> None:
    lowered = key.lower()
    if any(fragment in lowered for fragment in UNSAFE_PUBLIC_FRAGMENTS):
        raise ValueError(f"{path}.{key} has unsafe public field")


def _reject_unsafe_public_string(field_name: str, value: str) -> None:
    lowered = value.lower()
    if "://" in lowered or "?" in lowered or "@" in lowered:
        raise ValueError(f"{field_name} has unsafe public value")
    if any(fragment in lowered for fragment in UNSAFE_PUBLIC_FRAGMENTS):
        raise ValueError(f"{field_name} has unsafe public value")


__all__ = (
    "DEFAULT_RESEARCH_MARKET_COST_DEPTH_TRADEOFF_REPORT_CONFIG_VERSION",
    "CostDepthTradeoffConfig",
    "CostDepthTradeoffObservation",
    "CostDepthTradeoffReport",
    "CostDepthTradeoffReportDigest",
    "CostDepthTradeoffRow",
    "build_research_market_cost_depth_tradeoff_report",
    "research_market_cost_depth_tradeoff_report_digest",
    "research_market_cost_depth_tradeoff_report_payload",
)
