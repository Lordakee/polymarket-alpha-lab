"""Pure public spread volatility watch report for manual review."""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable
from dataclasses import dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
import json
import re
from typing import Any


DEFAULT_RESEARCH_MARKET_SPREAD_VOLATILITY_WATCH_CONFIG_VERSION = (
    "research-market-spread-volatility-watch-report-v0"
)

STATUS_PASS = "pass"
STATUS_WATCH = "watch"
STATUS_BLOCK = "block"
STATUSES = (STATUS_PASS, STATUS_WATCH, STATUS_BLOCK)

REASON_PREFIX = "spread_volatility_watch_"
NO_OBSERVATIONS_REASON = f"{REASON_PREFIX}no_observations"
CLEAR_REASON = f"{REASON_PREFIX}clear"
COMPOSITE_PRESSURE_BLOCK_REASON = f"{REASON_PREFIX}composite_pressure_block"
COMPOSITE_PRESSURE_WATCH_REASON = f"{REASON_PREFIX}composite_pressure_watch"
COST_RISK_PRESSURE_BLOCK_REASON = f"{REASON_PREFIX}cost_risk_pressure_block"
COST_RISK_PRESSURE_WATCH_REASON = f"{REASON_PREFIX}cost_risk_pressure_watch"
DEPTH_DECAY_BLOCK_REASON = f"{REASON_PREFIX}depth_decay_block"
DEPTH_DECAY_WATCH_REASON = f"{REASON_PREFIX}depth_decay_watch"
MANUAL_REVIEW_WATCH_REASON = f"{REASON_PREFIX}manual_review_watch"
QUOTE_AGE_BLOCK_REASON = f"{REASON_PREFIX}quote_age_block"
QUOTE_AGE_WATCH_REASON = f"{REASON_PREFIX}quote_age_watch"
SPREAD_INSTABILITY_BLOCK_REASON = f"{REASON_PREFIX}spread_instability_block"
SPREAD_INSTABILITY_WATCH_REASON = f"{REASON_PREFIX}spread_instability_watch"

REPORT_CLEAR_REASON = f"{REASON_PREFIX}report_clear"
REPORT_COMPOSITE_PRESSURE_REASON = f"{REASON_PREFIX}composite_pressure_detected"
REPORT_COST_RISK_REASON = f"{REASON_PREFIX}cost_risk_pressure_detected"
REPORT_DEPTH_DECAY_REASON = f"{REASON_PREFIX}depth_decay_detected"
REPORT_MANUAL_REVIEW_REASON = f"{REASON_PREFIX}manual_review_required"
REPORT_QUOTE_AGE_REASON = f"{REASON_PREFIX}quote_age_detected"
REPORT_SPREAD_INSTABILITY_REASON = f"{REASON_PREFIX}spread_instability_detected"

DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
QUANT = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
SECONDS_PER_DAY = Decimal("86400")
MICROSECONDS_PER_SECOND = Decimal("1000000")

HARD_FLAG_FIELDS = ("paper_only", "report_only", "readonly")
STATUS_SORT = {STATUS_BLOCK: 0, STATUS_WATCH: 1, STATUS_PASS: 2}
PUBLIC_LABEL_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,127}$")
PUBLIC_REASON_RE = re.compile(r"^[A-Za-z0-9_][A-Za-z0-9_.-]{0,191}$")

PUBLIC_DENY_FRAGMENTS = (
    "candidate_id",
    "condition_id",
    "market_id",
    "market_slug",
    "slug",
    "question",
    "url",
    "source_id",
    "source_text",
    "source_url",
    "raw",
    "://",
    "?",
    "dsn",
    "table",
    "token",
    "api_key",
    "secret",
    "credential",
    "session",
    "cookie",
    "bearer",
    "private" + "_key",
    "wal" + "let",
    "or" + "der",
    "tra" + "de",
    "bu" + "y",
    "se" + "ll",
    "recom" + "mend",
    "siz" + "ing",
)


__all__ = (
    "DEFAULT_RESEARCH_MARKET_SPREAD_VOLATILITY_WATCH_CONFIG_VERSION",
    "STATUSES",
    "ResearchMarketSpreadVolatilityWatchConfig",
    "ResearchMarketSpreadVolatilityWatchObservation",
    "ResearchMarketSpreadVolatilityWatchReasonCodeCount",
    "ResearchMarketSpreadVolatilityWatchReport",
    "ResearchMarketSpreadVolatilityWatchRow",
    "build_research_market_spread_volatility_watch_report",
    "research_market_spread_volatility_watch_report_digest",
    "research_market_spread_volatility_watch_report_payload",
)


@dataclass(frozen=True)
class ResearchMarketSpreadVolatilityWatchConfig:
    config_version: str = DEFAULT_RESEARCH_MARKET_SPREAD_VOLATILITY_WATCH_CONFIG_VERSION
    watch_spread_instability_ratio: Decimal = Decimal("0.020000")
    block_spread_instability_ratio: Decimal = Decimal("0.060000")
    watch_depth_decay_ratio: Decimal = Decimal("0.250000")
    block_depth_decay_ratio: Decimal = Decimal("0.650000")
    watch_quote_age_seconds: Decimal = Decimal("300.000000")
    block_quote_age_seconds: Decimal = Decimal("900.000000")
    watch_cost_risk_pressure_score: Decimal = Decimal("0.300000")
    block_cost_risk_pressure_score: Decimal = Decimal("0.700000")
    watch_composite_pressure: Decimal = Decimal("0.300000")
    block_composite_pressure: Decimal = Decimal("0.700000")
    spread_instability_weight: Decimal = Decimal("0.350000")
    depth_decay_weight: Decimal = Decimal("0.250000")
    quote_age_weight: Decimal = Decimal("0.200000")
    cost_risk_weight: Decimal = Decimal("0.200000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchMarketSpreadVolatilityWatchConfig:
            raise TypeError(
                "ResearchMarketSpreadVolatilityWatchConfig does not support subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchMarketSpreadVolatilityWatchConfig, "config")
        _require_public_label("config_version", self.config_version)
        if self.config_version != DEFAULT_RESEARCH_MARKET_SPREAD_VOLATILITY_WATCH_CONFIG_VERSION:
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "watch_spread_instability_ratio",
            "block_spread_instability_ratio",
            "watch_depth_decay_ratio",
            "block_depth_decay_ratio",
            "watch_cost_risk_pressure_score",
            "block_cost_risk_pressure_score",
            "watch_composite_pressure",
            "block_composite_pressure",
            "spread_instability_weight",
            "depth_decay_weight",
            "quote_age_weight",
            "cost_risk_weight",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in ("watch_quote_age_seconds", "block_quote_age_seconds"):
            object.__setattr__(
                self,
                field_name,
                _require_positive_decimal(field_name, getattr(self, field_name)),
            )
        _require_increasing_threshold(
            "watch_spread_instability_ratio",
            self.watch_spread_instability_ratio,
            "block_spread_instability_ratio",
            self.block_spread_instability_ratio,
        )
        _require_increasing_threshold(
            "watch_depth_decay_ratio",
            self.watch_depth_decay_ratio,
            "block_depth_decay_ratio",
            self.block_depth_decay_ratio,
        )
        _require_increasing_threshold(
            "watch_quote_age_seconds",
            self.watch_quote_age_seconds,
            "block_quote_age_seconds",
            self.block_quote_age_seconds,
        )
        _require_increasing_threshold(
            "watch_cost_risk_pressure_score",
            self.watch_cost_risk_pressure_score,
            "block_cost_risk_pressure_score",
            self.block_cost_risk_pressure_score,
        )
        _require_increasing_threshold(
            "watch_composite_pressure",
            self.watch_composite_pressure,
            "block_composite_pressure",
            self.block_composite_pressure,
        )
        weight_sum = _quantize(
            self.spread_instability_weight
            + self.depth_decay_weight
            + self.quote_age_weight
            + self.cost_risk_weight,
        )
        if weight_sum != ONE:
            raise ValueError("spread volatility weights must sum to 1.000000")
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class ResearchMarketSpreadVolatilityWatchObservation:
    public_cohort: str
    observed_at: datetime
    sample_count: Decimal
    aggregate_spread_instability_ratio: Decimal
    depth_decay_ratio: Decimal
    quote_age_seconds: Decimal
    cost_risk_pressure_score: Decimal
    reason_codes: tuple[str, ...] = ()
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchMarketSpreadVolatilityWatchObservation:
            raise TypeError(
                "ResearchMarketSpreadVolatilityWatchObservation does not support "
                "subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchMarketSpreadVolatilityWatchObservation, "observation")
        object.__setattr__(
            self,
            "public_cohort",
            _require_public_label("public_cohort", self.public_cohort),
        )
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        object.__setattr__(
            self,
            "sample_count",
            _require_positive_whole_decimal("sample_count", self.sample_count),
        )
        for field_name in (
            "aggregate_spread_instability_ratio",
            "depth_decay_ratio",
            "cost_risk_pressure_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "quote_age_seconds",
            _require_nonnegative_decimal("quote_age_seconds", self.quote_age_seconds),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_input_reason_codes(self.reason_codes, allow_empty=True),
        )
        _require_hard_flags("observation", self)


@dataclass(frozen=True)
class ResearchMarketSpreadVolatilityWatchRow:
    public_cohort: str
    observed_at: datetime
    age_seconds: Decimal
    sample_count: Decimal
    aggregate_spread_instability_ratio: Decimal
    depth_decay_ratio: Decimal
    quote_age_seconds: Decimal
    cost_risk_pressure_score: Decimal
    spread_instability_pressure: Decimal
    depth_decay_pressure: Decimal
    quote_age_pressure: Decimal
    cost_risk_pressure: Decimal
    composite_pressure: Decimal
    status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchMarketSpreadVolatilityWatchRow:
            raise TypeError(
                "ResearchMarketSpreadVolatilityWatchRow does not support subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchMarketSpreadVolatilityWatchRow, "row")
        object.__setattr__(
            self,
            "public_cohort",
            _require_public_label("public_cohort", self.public_cohort),
        )
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in ("age_seconds", "quote_age_seconds"):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "sample_count",
            _require_positive_whole_decimal("sample_count", self.sample_count),
        )
        for field_name in (
            "aggregate_spread_instability_ratio",
            "depth_decay_ratio",
            "cost_risk_pressure_score",
            "spread_instability_pressure",
            "depth_decay_pressure",
            "quote_age_pressure",
            "cost_risk_pressure",
            "composite_pressure",
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
            _normalize_reason_codes(self.reason_codes, allow_empty=False),
        )
        _validate_row_consistency(self)
        _require_hard_flags("row", self)


@dataclass(frozen=True)
class ResearchMarketSpreadVolatilityWatchReasonCodeCount:
    reason_code: str
    count: Decimal
    row_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchMarketSpreadVolatilityWatchReasonCodeCount:
            raise TypeError(
                "ResearchMarketSpreadVolatilityWatchReasonCodeCount does not support "
                "subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchMarketSpreadVolatilityWatchReasonCodeCount, "count")
        object.__setattr__(
            self,
            "reason_code",
            _require_reason_code("reason_code", self.reason_code),
        )
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


@dataclass(frozen=True)
class ResearchMarketSpreadVolatilityWatchReport:
    generated_at: datetime
    config_version: str
    observation_count: Decimal
    sample_count: Decimal
    row_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    spread_instability_watch_count: Decimal
    depth_decay_watch_count: Decimal
    quote_age_watch_count: Decimal
    cost_risk_pressure_count: Decimal
    mean_aggregate_spread_instability_ratio: Decimal
    mean_depth_decay_ratio: Decimal
    mean_quote_age_seconds: Decimal
    mean_cost_risk_pressure_score: Decimal
    mean_composite_pressure: Decimal
    max_composite_pressure: Decimal
    manual_review_required: bool
    status: str
    reason_codes: tuple[str, ...]
    reason_code_counts: tuple[ResearchMarketSpreadVolatilityWatchReasonCodeCount, ...]
    rows: tuple[ResearchMarketSpreadVolatilityWatchRow, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchMarketSpreadVolatilityWatchReport:
            raise TypeError(
                "ResearchMarketSpreadVolatilityWatchReport does not support subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchMarketSpreadVolatilityWatchReport, "report")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_label("config_version", self.config_version)
        for field_name in (
            "observation_count",
            "sample_count",
            "row_count",
            "pass_count",
            "watch_count",
            "block_count",
            "spread_instability_watch_count",
            "depth_decay_watch_count",
            "quote_age_watch_count",
            "cost_risk_pressure_count",
            "mean_aggregate_spread_instability_ratio",
            "mean_depth_decay_ratio",
            "mean_quote_age_seconds",
            "mean_cost_risk_pressure_score",
            "mean_composite_pressure",
            "max_composite_pressure",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        _require_bool("manual_review_required", self.manual_review_required)
        _require_status("status", self.status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes, allow_empty=False),
        )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        _validate_report_consistency(self)
        _require_hard_flags("report", self)
        expected_digest = _derived_report_digest(self)
        if self.derived_validation_digest:
            _require_hex_digest("derived_validation_digest", self.derived_validation_digest)
            if self.derived_validation_digest != expected_digest:
                raise ValueError("derived_validation_digest must match report fields")
        else:
            object.__setattr__(self, "derived_validation_digest", expected_digest)


def build_research_market_spread_volatility_watch_report(
    observations: Iterable[object],
    *,
    config: ResearchMarketSpreadVolatilityWatchConfig,
    generated_at: datetime,
) -> ResearchMarketSpreadVolatilityWatchReport:
    if type(config) is not ResearchMarketSpreadVolatilityWatchConfig:
        raise ValueError("config must be a ResearchMarketSpreadVolatilityWatchConfig")
    _require_hard_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    input_rows = _normalize_observations(observations)
    rows = tuple(
        sorted(
            (
                _row_from_observation(
                    row,
                    config=config,
                    generated_at=generated_at_utc,
                )
                for row in input_rows
            ),
            key=_row_sort_key,
        ),
    )
    reason_codes = _report_reason_codes(rows)
    return ResearchMarketSpreadVolatilityWatchReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        observation_count=_count(len(input_rows)),
        sample_count=sum((row.sample_count for row in rows), ZERO),
        row_count=_count(len(rows)),
        pass_count=_count(_status_count(rows, STATUS_PASS)),
        watch_count=_count(_status_count(rows, STATUS_WATCH)),
        block_count=_count(_status_count(rows, STATUS_BLOCK)),
        spread_instability_watch_count=_count(
            _reason_count(rows, SPREAD_INSTABILITY_WATCH_REASON)
            + _reason_count(rows, SPREAD_INSTABILITY_BLOCK_REASON),
        ),
        depth_decay_watch_count=_count(
            _reason_count(rows, DEPTH_DECAY_WATCH_REASON)
            + _reason_count(rows, DEPTH_DECAY_BLOCK_REASON),
        ),
        quote_age_watch_count=_count(
            _reason_count(rows, QUOTE_AGE_WATCH_REASON)
            + _reason_count(rows, QUOTE_AGE_BLOCK_REASON),
        ),
        cost_risk_pressure_count=_count(
            _reason_count(rows, COST_RISK_PRESSURE_WATCH_REASON)
            + _reason_count(rows, COST_RISK_PRESSURE_BLOCK_REASON),
        ),
        mean_aggregate_spread_instability_ratio=_mean(
            tuple(row.aggregate_spread_instability_ratio for row in rows),
        ),
        mean_depth_decay_ratio=_mean(tuple(row.depth_decay_ratio for row in rows)),
        mean_quote_age_seconds=_mean(tuple(row.quote_age_seconds for row in rows)),
        mean_cost_risk_pressure_score=_mean(
            tuple(row.cost_risk_pressure_score for row in rows),
        ),
        mean_composite_pressure=_mean(tuple(row.composite_pressure for row in rows)),
        max_composite_pressure=max((row.composite_pressure for row in rows), default=ZERO),
        manual_review_required=_manual_review_required(rows),
        status=_report_status(rows),
        reason_codes=reason_codes,
        reason_code_counts=_reason_code_counts(rows, reason_codes),
        rows=rows,
    )


def research_market_spread_volatility_watch_report_payload(
    report: ResearchMarketSpreadVolatilityWatchReport | dict[str, Any],
) -> dict[str, Any]:
    if type(report) is ResearchMarketSpreadVolatilityWatchReport:
        _require_hard_flags("report", report)
        _validate_report_consistency(report)
        expected_digest = _derived_report_digest(report)
        if report.derived_validation_digest != expected_digest:
            raise ValueError("derived_validation_digest must match report fields")
        payload = _payload_value(report)
    elif type(report) is dict:
        payload = _payload_value(report)
    else:
        raise ValueError("report must be a ResearchMarketSpreadVolatilityWatchReport")
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    _reject_unsafe_payload("payload", payload)
    _require_hard_flags("payload", _DictFlags(payload))
    return payload


def research_market_spread_volatility_watch_report_digest(
    report: ResearchMarketSpreadVolatilityWatchReport | dict[str, Any],
) -> str:
    payload = research_market_spread_volatility_watch_report_payload(report)
    digest_payload = dict(payload)
    digest_payload.pop("derived_validation_digest", None)
    encoded = json.dumps(digest_payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    digest = sha256(encoded.encode("utf-8")).hexdigest()
    if (
        "derived_validation_digest" in payload
        and payload["derived_validation_digest"] != digest
    ):
        raise ValueError("derived_validation_digest must match report fields")
    return digest


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


def _normalize_observations(
    observations: Iterable[object],
) -> tuple[ResearchMarketSpreadVolatilityWatchObservation, ...]:
    if isinstance(observations, (str, bytes)) or not isinstance(observations, Iterable):
        raise ValueError("observations must be an iterable")
    rows = tuple(observations)
    for row in rows:
        if type(row) is not ResearchMarketSpreadVolatilityWatchObservation:
            raise ValueError(
                "observations must contain "
                "ResearchMarketSpreadVolatilityWatchObservation",
            )
        _require_hard_flags("observation", row)
    return rows


def _row_from_observation(
    row: ResearchMarketSpreadVolatilityWatchObservation,
    *,
    config: ResearchMarketSpreadVolatilityWatchConfig,
    generated_at: datetime,
) -> ResearchMarketSpreadVolatilityWatchRow:
    age_seconds = _age_seconds(row.observed_at, generated_at)
    spread_pressure = _threshold_pressure(
        row.aggregate_spread_instability_ratio,
        watch_value=config.watch_spread_instability_ratio,
        block_value=config.block_spread_instability_ratio,
    )
    depth_pressure = _threshold_pressure(
        row.depth_decay_ratio,
        watch_value=config.watch_depth_decay_ratio,
        block_value=config.block_depth_decay_ratio,
    )
    quote_pressure = _threshold_pressure(
        row.quote_age_seconds,
        watch_value=config.watch_quote_age_seconds,
        block_value=config.block_quote_age_seconds,
    )
    cost_pressure = _threshold_pressure(
        row.cost_risk_pressure_score,
        watch_value=config.watch_cost_risk_pressure_score,
        block_value=config.block_cost_risk_pressure_score,
    )
    composite_pressure = _composite_pressure(
        spread_instability_pressure=spread_pressure,
        depth_decay_pressure=depth_pressure,
        quote_age_pressure=quote_pressure,
        cost_risk_pressure=cost_pressure,
        config=config,
    )
    status = _row_status(row, composite_pressure=composite_pressure, config=config)
    return ResearchMarketSpreadVolatilityWatchRow(
        public_cohort=row.public_cohort,
        observed_at=row.observed_at,
        age_seconds=age_seconds,
        sample_count=row.sample_count,
        aggregate_spread_instability_ratio=row.aggregate_spread_instability_ratio,
        depth_decay_ratio=row.depth_decay_ratio,
        quote_age_seconds=row.quote_age_seconds,
        cost_risk_pressure_score=row.cost_risk_pressure_score,
        spread_instability_pressure=spread_pressure,
        depth_decay_pressure=depth_pressure,
        quote_age_pressure=quote_pressure,
        cost_risk_pressure=cost_pressure,
        composite_pressure=composite_pressure,
        status=status,
        reason_codes=_row_reason_codes(
            row,
            status=status,
            composite_pressure=composite_pressure,
            config=config,
        ),
    )


def _row_status(
    row: ResearchMarketSpreadVolatilityWatchObservation,
    *,
    composite_pressure: Decimal,
    config: ResearchMarketSpreadVolatilityWatchConfig,
) -> str:
    if (
        row.aggregate_spread_instability_ratio >= config.block_spread_instability_ratio
        or row.depth_decay_ratio >= config.block_depth_decay_ratio
        or row.quote_age_seconds >= config.block_quote_age_seconds
        or row.cost_risk_pressure_score >= config.block_cost_risk_pressure_score
        or composite_pressure >= config.block_composite_pressure
    ):
        return STATUS_BLOCK
    if (
        row.reason_codes
        or row.aggregate_spread_instability_ratio >= config.watch_spread_instability_ratio
        or row.depth_decay_ratio >= config.watch_depth_decay_ratio
        or row.quote_age_seconds >= config.watch_quote_age_seconds
        or row.cost_risk_pressure_score >= config.watch_cost_risk_pressure_score
        or composite_pressure >= config.watch_composite_pressure
    ):
        return STATUS_WATCH
    return STATUS_PASS


def _row_reason_codes(
    row: ResearchMarketSpreadVolatilityWatchObservation,
    *,
    status: str,
    composite_pressure: Decimal,
    config: ResearchMarketSpreadVolatilityWatchConfig,
) -> tuple[str, ...]:
    reason_codes: list[str] = list(row.reason_codes)
    if row.aggregate_spread_instability_ratio >= config.block_spread_instability_ratio:
        reason_codes.append(SPREAD_INSTABILITY_BLOCK_REASON)
    elif row.aggregate_spread_instability_ratio >= config.watch_spread_instability_ratio:
        reason_codes.append(SPREAD_INSTABILITY_WATCH_REASON)
    if row.depth_decay_ratio >= config.block_depth_decay_ratio:
        reason_codes.append(DEPTH_DECAY_BLOCK_REASON)
    elif row.depth_decay_ratio >= config.watch_depth_decay_ratio:
        reason_codes.append(DEPTH_DECAY_WATCH_REASON)
    if row.quote_age_seconds >= config.block_quote_age_seconds:
        reason_codes.append(QUOTE_AGE_BLOCK_REASON)
    elif row.quote_age_seconds >= config.watch_quote_age_seconds:
        reason_codes.append(QUOTE_AGE_WATCH_REASON)
    if row.cost_risk_pressure_score >= config.block_cost_risk_pressure_score:
        reason_codes.append(COST_RISK_PRESSURE_BLOCK_REASON)
    elif row.cost_risk_pressure_score >= config.watch_cost_risk_pressure_score:
        reason_codes.append(COST_RISK_PRESSURE_WATCH_REASON)
    if composite_pressure >= config.block_composite_pressure:
        reason_codes.append(COMPOSITE_PRESSURE_BLOCK_REASON)
    elif composite_pressure >= config.watch_composite_pressure:
        reason_codes.append(COMPOSITE_PRESSURE_WATCH_REASON)
    if row.reason_codes and status == STATUS_WATCH:
        reason_codes.append(MANUAL_REVIEW_WATCH_REASON)
    if status == STATUS_PASS and not reason_codes:
        reason_codes.append(CLEAR_REASON)
    return _normalize_reason_codes(tuple(reason_codes), allow_empty=False)


def _report_reason_codes(
    rows: tuple[ResearchMarketSpreadVolatilityWatchRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return (NO_OBSERVATIONS_REASON,)
    reason_codes: list[str] = []
    if any(
        SPREAD_INSTABILITY_WATCH_REASON in row.reason_codes
        or SPREAD_INSTABILITY_BLOCK_REASON in row.reason_codes
        for row in rows
    ):
        reason_codes.append(REPORT_SPREAD_INSTABILITY_REASON)
    if any(
        DEPTH_DECAY_WATCH_REASON in row.reason_codes
        or DEPTH_DECAY_BLOCK_REASON in row.reason_codes
        for row in rows
    ):
        reason_codes.append(REPORT_DEPTH_DECAY_REASON)
    if any(
        QUOTE_AGE_WATCH_REASON in row.reason_codes
        or QUOTE_AGE_BLOCK_REASON in row.reason_codes
        for row in rows
    ):
        reason_codes.append(REPORT_QUOTE_AGE_REASON)
    if any(
        COST_RISK_PRESSURE_WATCH_REASON in row.reason_codes
        or COST_RISK_PRESSURE_BLOCK_REASON in row.reason_codes
        for row in rows
    ):
        reason_codes.append(REPORT_COST_RISK_REASON)
    if any(
        COMPOSITE_PRESSURE_WATCH_REASON in row.reason_codes
        or COMPOSITE_PRESSURE_BLOCK_REASON in row.reason_codes
        for row in rows
    ):
        reason_codes.append(REPORT_COMPOSITE_PRESSURE_REASON)
    if any(row.status != STATUS_PASS for row in rows):
        reason_codes.append(REPORT_MANUAL_REVIEW_REASON)
    if not reason_codes:
        reason_codes.append(REPORT_CLEAR_REASON)
    return _normalize_reason_codes(tuple(reason_codes), allow_empty=False)


def _reason_code_counts(
    rows: tuple[ResearchMarketSpreadVolatilityWatchRow, ...],
    report_reason_codes: tuple[str, ...],
) -> tuple[ResearchMarketSpreadVolatilityWatchReasonCodeCount, ...]:
    if not rows:
        return tuple(
            ResearchMarketSpreadVolatilityWatchReasonCodeCount(
                reason_code=reason_code,
                count=ONE,
                row_ratio=ZERO,
            )
            for reason_code in report_reason_codes
        )
    counter: Counter[str] = Counter()
    for row in rows:
        counter.update(row.reason_codes)
    row_count = _count(len(rows))
    return tuple(
        ResearchMarketSpreadVolatilityWatchReasonCodeCount(
            reason_code=reason_code,
            count=_count(count),
            row_ratio=_quantize(Decimal(count) / row_count),
        )
        for reason_code, count in sorted(counter.items())
    )


def _validate_row_consistency(row: ResearchMarketSpreadVolatilityWatchRow) -> None:
    if row.status == STATUS_PASS and row.reason_codes != (CLEAR_REASON,):
        raise ValueError("pass rows must contain only the clear reason")
    if COMPOSITE_PRESSURE_BLOCK_REASON in row.reason_codes and row.status != STATUS_BLOCK:
        raise ValueError("composite pressure block reason requires block status")
    if COMPOSITE_PRESSURE_WATCH_REASON in row.reason_codes and row.status == STATUS_PASS:
        raise ValueError("composite pressure watch reason requires review status")


def _validate_report_consistency(report: ResearchMarketSpreadVolatilityWatchReport) -> None:
    rows = report.rows
    for row in rows:
        _require_hard_flags("row", row)
    for reason_count in report.reason_code_counts:
        _require_hard_flags("reason code count", reason_count)
    if report.observation_count != _count(len(rows)):
        raise ValueError("observation_count must match rows")
    if report.row_count != _count(len(rows)):
        raise ValueError("row_count must match rows")
    if report.sample_count != sum((row.sample_count for row in rows), ZERO):
        raise ValueError("sample_count must match rows")
    if report.pass_count != _count(_status_count(rows, STATUS_PASS)):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _count(_status_count(rows, STATUS_WATCH)):
        raise ValueError("watch_count must match rows")
    if report.block_count != _count(_status_count(rows, STATUS_BLOCK)):
        raise ValueError("block_count must match rows")
    if report.spread_instability_watch_count != _count(
        _reason_count(rows, SPREAD_INSTABILITY_WATCH_REASON)
        + _reason_count(rows, SPREAD_INSTABILITY_BLOCK_REASON),
    ):
        raise ValueError("spread_instability_watch_count must match rows")
    if report.depth_decay_watch_count != _count(
        _reason_count(rows, DEPTH_DECAY_WATCH_REASON)
        + _reason_count(rows, DEPTH_DECAY_BLOCK_REASON),
    ):
        raise ValueError("depth_decay_watch_count must match rows")
    if report.quote_age_watch_count != _count(
        _reason_count(rows, QUOTE_AGE_WATCH_REASON)
        + _reason_count(rows, QUOTE_AGE_BLOCK_REASON),
    ):
        raise ValueError("quote_age_watch_count must match rows")
    if report.cost_risk_pressure_count != _count(
        _reason_count(rows, COST_RISK_PRESSURE_WATCH_REASON)
        + _reason_count(rows, COST_RISK_PRESSURE_BLOCK_REASON),
    ):
        raise ValueError("cost_risk_pressure_count must match rows")
    if report.mean_aggregate_spread_instability_ratio != _mean(
        tuple(row.aggregate_spread_instability_ratio for row in rows),
    ):
        raise ValueError("mean_aggregate_spread_instability_ratio must match rows")
    if report.mean_depth_decay_ratio != _mean(tuple(row.depth_decay_ratio for row in rows)):
        raise ValueError("mean_depth_decay_ratio must match rows")
    if report.mean_quote_age_seconds != _mean(tuple(row.quote_age_seconds for row in rows)):
        raise ValueError("mean_quote_age_seconds must match rows")
    if report.mean_cost_risk_pressure_score != _mean(
        tuple(row.cost_risk_pressure_score for row in rows),
    ):
        raise ValueError("mean_cost_risk_pressure_score must match rows")
    if report.mean_composite_pressure != _mean(tuple(row.composite_pressure for row in rows)):
        raise ValueError("mean_composite_pressure must match rows")
    if report.max_composite_pressure != max(
        (row.composite_pressure for row in rows),
        default=ZERO,
    ):
        raise ValueError("max_composite_pressure must match rows")
    if report.manual_review_required is not _manual_review_required(rows):
        raise ValueError("manual_review_required must match rows")
    if report.status != _report_status(rows):
        raise ValueError("status must match rows")
    if report.reason_codes != _report_reason_codes(rows):
        raise ValueError("reason_codes must match rows")


def _manual_review_required(rows: tuple[ResearchMarketSpreadVolatilityWatchRow, ...]) -> bool:
    if not rows:
        return True
    return any(row.status != STATUS_PASS for row in rows)


def _report_status(rows: tuple[ResearchMarketSpreadVolatilityWatchRow, ...]) -> str:
    if not rows:
        return STATUS_BLOCK
    if any(row.status == STATUS_BLOCK for row in rows):
        return STATUS_BLOCK
    if any(row.status == STATUS_WATCH for row in rows):
        return STATUS_WATCH
    return STATUS_PASS


def _status_count(
    rows: tuple[ResearchMarketSpreadVolatilityWatchRow, ...],
    status: str,
) -> int:
    return sum(1 for row in rows if row.status == status)


def _reason_count(
    rows: tuple[ResearchMarketSpreadVolatilityWatchRow, ...],
    reason_code: str,
) -> int:
    return sum(1 for row in rows if reason_code in row.reason_codes)


def _row_sort_key(row: ResearchMarketSpreadVolatilityWatchRow) -> tuple[int, str, datetime]:
    return (STATUS_SORT[row.status], row.public_cohort, row.observed_at)


def _composite_pressure(
    *,
    spread_instability_pressure: Decimal,
    depth_decay_pressure: Decimal,
    quote_age_pressure: Decimal,
    cost_risk_pressure: Decimal,
    config: ResearchMarketSpreadVolatilityWatchConfig,
) -> Decimal:
    return _clamp_ratio(
        spread_instability_pressure * config.spread_instability_weight
        + depth_decay_pressure * config.depth_decay_weight
        + quote_age_pressure * config.quote_age_weight
        + cost_risk_pressure * config.cost_risk_weight,
    )


def _threshold_pressure(
    value: Decimal,
    *,
    watch_value: Decimal,
    block_value: Decimal,
) -> Decimal:
    if value <= watch_value:
        return ZERO
    if value >= block_value:
        return ONE
    return _clamp_ratio((value - watch_value) / (block_value - watch_value))


def _age_seconds(observed_at: datetime, generated_at: datetime) -> Decimal:
    if observed_at > generated_at:
        raise ValueError("observed_at must be on or before generated_at")
    delta = generated_at - observed_at
    seconds = (
        Decimal(delta.days) * SECONDS_PER_DAY
        + Decimal(delta.seconds)
        + Decimal(delta.microseconds) / MICROSECONDS_PER_SECOND
    )
    return _quantize(seconds)


def _mean(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return ZERO
    return _quantize(sum(values, ZERO) / Decimal(len(values)))


def _count(value: int) -> Decimal:
    if type(value) is not int:
        raise ValueError("count must be an int")
    if value < 0:
        raise ValueError("count must be nonnegative")
    return _quantize(Decimal(value))


def _normalize_rows(
    rows: tuple[ResearchMarketSpreadVolatilityWatchRow, ...],
) -> tuple[ResearchMarketSpreadVolatilityWatchRow, ...]:
    if type(rows) is not tuple:
        raise ValueError("rows must be a tuple")
    for row in rows:
        if type(row) is not ResearchMarketSpreadVolatilityWatchRow:
            raise ValueError("rows must contain ResearchMarketSpreadVolatilityWatchRow")
        _require_hard_flags("row", row)
    if rows != tuple(sorted(rows, key=_row_sort_key)):
        raise ValueError("rows must be sorted by public cohort")
    return rows


def _normalize_reason_code_counts(
    values: tuple[ResearchMarketSpreadVolatilityWatchReasonCodeCount, ...],
) -> tuple[ResearchMarketSpreadVolatilityWatchReasonCodeCount, ...]:
    if type(values) is not tuple:
        raise ValueError("reason_code_counts must be a tuple")
    for value in values:
        if type(value) is not ResearchMarketSpreadVolatilityWatchReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "ResearchMarketSpreadVolatilityWatchReasonCodeCount",
            )
        _require_hard_flags("reason code count", value)
    if values != tuple(sorted(values, key=lambda value: value.reason_code)):
        raise ValueError("reason_code_counts must be sorted by reason_code")
    return values


def _require_exact_type(value: object, expected_type: type[object], label: str) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{label} must be exactly {expected_type.__name__}")


def _require_public_label(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if value.strip() != value or not value:
        raise ValueError(f"{field_name} must be non-empty public text")
    if not PUBLIC_LABEL_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a public label")
    _reject_unsafe_public_text(field_name, value)
    return value


def _require_reason_code(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if value.strip() != value or not value:
        raise ValueError(f"{field_name} must be non-empty")
    if not PUBLIC_REASON_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be public")
    _reject_unsafe_public_text(field_name, value)
    return value


def _normalize_input_reason_codes(
    reason_codes: tuple[str, ...],
    *,
    allow_empty: bool,
) -> tuple[str, ...]:
    normalized: list[str] = []
    for reason_code in _normalize_reason_codes(reason_codes, allow_empty=allow_empty):
        if reason_code.startswith("input_"):
            prefixed = reason_code
        else:
            prefixed = f"input_{reason_code}"
        if prefixed not in normalized:
            normalized.append(prefixed)
    return tuple(sorted(normalized))


def _normalize_reason_codes(
    reason_codes: tuple[str, ...],
    *,
    allow_empty: bool,
) -> tuple[str, ...]:
    if type(reason_codes) is not tuple:
        raise ValueError("reason_codes must be a tuple")
    if not reason_codes and not allow_empty:
        raise ValueError("reason_codes must not be empty")
    normalized: set[str] = set()
    for reason_code in reason_codes:
        normalized.add(_require_reason_code("reason_code", reason_code))
    return tuple(sorted(normalized))


def _reject_unsafe_public_text(field_name: str, value: str) -> None:
    lowered = value.lower()
    if any(fragment in lowered for fragment in PUBLIC_DENY_FRAGMENTS):
        raise ValueError(f"{field_name} has unsafe public value")


def _require_bool(field_name: str, value: object) -> bool:
    if type(value) is not bool:
        raise ValueError(f"{field_name} must be a bool")
    return value


def _require_status(field_name: str, value: object) -> str:
    if type(value) is not str or value not in STATUSES:
        raise ValueError(f"{field_name} must be one of pass, watch, block")
    return value


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


def _require_positive_whole_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_nonnegative_decimal(field_name, value)
    if normalized <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{field_name} must be a whole Decimal")
    return normalized


def _require_ratio_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < ZERO or normalized > ONE:
        raise ValueError(f"{field_name} must be between 0.000000 and 1.000000")
    return normalized


def _require_increasing_threshold(
    watch_field_name: str,
    watch_value: Decimal,
    block_field_name: str,
    block_value: Decimal,
) -> None:
    if block_value <= watch_value:
        raise ValueError(f"{block_field_name} must exceed {watch_field_name}")


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in HARD_FLAG_FIELDS:
        if getattr(value, field_name, None) is not True:
            raise ValueError(f"{label}.{field_name} must be True")


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _clamp_ratio(value: Decimal) -> Decimal:
    normalized = _quantize(value)
    if normalized < ZERO:
        return ZERO
    if normalized > ONE:
        return ONE
    return normalized


def _quantize(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(QUANT)


def _payload_value(value: Any) -> Any:
    if value is None:
        return None
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
    if is_dataclass(value) and not isinstance(value, type):
        return {
            field.name: _payload_value(getattr(value, field.name))
            for field in fields(value)
        }
    if type(value) is dict:
        return {str(key): _payload_value(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_payload_value(item) for item in value]
    raise ValueError("payload value is not JSON serializable")


def _derived_report_digest(report: ResearchMarketSpreadVolatilityWatchReport) -> str:
    payload = _payload_value(report)
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    digest_payload = dict(payload)
    digest_payload.pop("derived_validation_digest", None)
    encoded = json.dumps(
        digest_payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    )
    return sha256(encoded.encode("utf-8")).hexdigest()


def _reject_unsafe_payload(label: str, value: object) -> None:
    if type(value) is dict:
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("payload keys must be strings")
            _reject_unsafe_public_text(label, key)
            _reject_unsafe_payload(key, item)
        return
    if isinstance(value, list):
        for item in value:
            _reject_unsafe_payload(label, item)
        return
    if type(value) is str:
        _reject_unsafe_public_text(label, value)
        return
    if value is None or type(value) is bool:
        return
    raise ValueError(f"{label} contains an unsupported payload value")


def _require_hex_digest(field_name: str, value: object) -> None:
    if type(value) is not str or len(value) != 64:
        raise ValueError(f"{field_name} must be a 64-character hex string")
    allowed = set("0123456789abcdef")
    if any(character not in allowed for character in value):
        raise ValueError(f"{field_name} must be a 64-character hex string")
