"""Pure public resolution-liquidity mismatch report.

Callers provide aggregate, already-public observations. The module returns
deterministic report-only rows, summary status, reason counts, and a validation
digest without external side effects.
"""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable
from dataclasses import dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation
from hashlib import sha256
import json
from typing import Any


__all__ = (
    "STATUSES",
    "ResearchMarketResolutionLiquidityMismatchConfig",
    "ResearchMarketResolutionLiquidityMismatchObservation",
    "ResearchMarketResolutionLiquidityMismatchReasonCodeCount",
    "ResearchMarketResolutionLiquidityMismatchReport",
    "ResearchMarketResolutionLiquidityMismatchRow",
    "build_research_market_resolution_liquidity_mismatch_report",
    "research_market_resolution_liquidity_mismatch_report_payload",
)


DEFAULT_CONFIG_VERSION = "research-market-resolution-liquidity-mismatch-report-v0"
STATUSES = ("pass", "watch", "block")
ZERO = Decimal("0")
ONE = Decimal("1")
TWO = Decimal("2")
THREE = Decimal("3")
RATIO_QUANTUM = Decimal("0.000001")
DEFAULT_WATCH_MISMATCH_SCORE = Decimal("0.250000")
DEFAULT_BLOCK_MISMATCH_SCORE = Decimal("0.650000")
DEFAULT_WATCH_RULE_AMBIGUITY_SCORE = Decimal("0.350000")
DEFAULT_BLOCK_RULE_AMBIGUITY_SCORE = Decimal("0.750000")
DEFAULT_WATCH_DEADLINE_PRESSURE_SCORE = Decimal("0.300000")
DEFAULT_BLOCK_DEADLINE_PRESSURE_SCORE = Decimal("0.700000")
DEFAULT_WATCH_DEPTH_FADE_RATE = Decimal("0.200000")
DEFAULT_BLOCK_DEPTH_FADE_RATE = Decimal("0.600000")
DEFAULT_WATCH_SPREAD_WIDENING_RATE = Decimal("0.150000")
DEFAULT_BLOCK_SPREAD_WIDENING_RATE = Decimal("0.500000")
DEFAULT_WATCH_QUOTE_STALENESS_SECONDS = Decimal("300.000000")
DEFAULT_BLOCK_QUOTE_STALENESS_SECONDS = Decimal("900.000000")
_DERIVED_VALIDATION_DIGEST_FIELD = "derived_validation_digest"
_PUBLIC_LABEL_DENY_FRAGMENTS = (
    "market",
    "slug",
    "source",
    "raw",
)


@dataclass(frozen=True)
class ResearchMarketResolutionLiquidityMismatchConfig:
    config_version: str = DEFAULT_CONFIG_VERSION
    watch_mismatch_score: Decimal = DEFAULT_WATCH_MISMATCH_SCORE
    block_mismatch_score: Decimal = DEFAULT_BLOCK_MISMATCH_SCORE
    watch_rule_ambiguity_score: Decimal = DEFAULT_WATCH_RULE_AMBIGUITY_SCORE
    block_rule_ambiguity_score: Decimal = DEFAULT_BLOCK_RULE_AMBIGUITY_SCORE
    watch_deadline_pressure_score: Decimal = DEFAULT_WATCH_DEADLINE_PRESSURE_SCORE
    block_deadline_pressure_score: Decimal = DEFAULT_BLOCK_DEADLINE_PRESSURE_SCORE
    watch_depth_fade_rate: Decimal = DEFAULT_WATCH_DEPTH_FADE_RATE
    block_depth_fade_rate: Decimal = DEFAULT_BLOCK_DEPTH_FADE_RATE
    watch_spread_widening_rate: Decimal = DEFAULT_WATCH_SPREAD_WIDENING_RATE
    block_spread_widening_rate: Decimal = DEFAULT_BLOCK_SPREAD_WIDENING_RATE
    watch_quote_staleness_seconds: Decimal = DEFAULT_WATCH_QUOTE_STALENESS_SECONDS
    block_quote_staleness_seconds: Decimal = DEFAULT_BLOCK_QUOTE_STALENESS_SECONDS
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_text("config_version", self.config_version)
        for field_name in (
            "watch_mismatch_score",
            "block_mismatch_score",
            "watch_rule_ambiguity_score",
            "block_rule_ambiguity_score",
            "watch_deadline_pressure_score",
            "block_deadline_pressure_score",
            "watch_depth_fade_rate",
            "block_depth_fade_rate",
            "watch_spread_widening_rate",
            "block_spread_widening_rate",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_probability_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "watch_quote_staleness_seconds",
            "block_quote_staleness_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_positive_decimal(field_name, getattr(self, field_name)),
            )
        _require_increasing_threshold(
            "watch_mismatch_score",
            self.watch_mismatch_score,
            "block_mismatch_score",
            self.block_mismatch_score,
        )
        _require_increasing_threshold(
            "watch_rule_ambiguity_score",
            self.watch_rule_ambiguity_score,
            "block_rule_ambiguity_score",
            self.block_rule_ambiguity_score,
        )
        _require_increasing_threshold(
            "watch_deadline_pressure_score",
            self.watch_deadline_pressure_score,
            "block_deadline_pressure_score",
            self.block_deadline_pressure_score,
        )
        _require_increasing_threshold(
            "watch_depth_fade_rate",
            self.watch_depth_fade_rate,
            "block_depth_fade_rate",
            self.block_depth_fade_rate,
        )
        _require_increasing_threshold(
            "watch_spread_widening_rate",
            self.watch_spread_widening_rate,
            "block_spread_widening_rate",
            self.block_spread_widening_rate,
        )
        _require_increasing_threshold(
            "watch_quote_staleness_seconds",
            self.watch_quote_staleness_seconds,
            "block_quote_staleness_seconds",
            self.block_quote_staleness_seconds,
        )
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class ResearchMarketResolutionLiquidityMismatchObservation:
    public_cluster: str
    resolution_bucket: str
    sample_count: Decimal
    aggregate_rule_ambiguity_score: Decimal
    deadline_pressure_score: Decimal
    depth_fade_rate: Decimal
    spread_widening_rate: Decimal
    quote_staleness_seconds: Decimal
    observed_at: datetime
    reason_codes: tuple[str, ...] = ()
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_public_label("public_cluster", self.public_cluster)
        _require_public_label("resolution_bucket", self.resolution_bucket)
        object.__setattr__(
            self,
            "sample_count",
            _require_positive_whole_decimal("sample_count", self.sample_count),
        )
        for field_name in (
            "aggregate_rule_ambiguity_score",
            "deadline_pressure_score",
            "depth_fade_rate",
            "spread_widening_rate",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_probability_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "quote_staleness_seconds",
            _require_nonnegative_decimal(
                "quote_staleness_seconds",
                self.quote_staleness_seconds,
            ),
        )
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, allow_empty=True),
        )
        _require_hard_flags("observation", self)


@dataclass(frozen=True)
class ResearchMarketResolutionLiquidityMismatchRow:
    public_cluster: str
    resolution_bucket: str
    sample_count: Decimal
    aggregate_rule_ambiguity_score: Decimal
    deadline_pressure_score: Decimal
    resolution_risk_score: Decimal
    depth_fade_rate: Decimal
    spread_widening_rate: Decimal
    quote_staleness_seconds: Decimal
    quote_staleness_score: Decimal
    liquidity_stress_score: Decimal
    mismatch_score: Decimal
    observed_at: datetime
    age_seconds: Decimal
    status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_public_label("public_cluster", self.public_cluster)
        _require_public_label("resolution_bucket", self.resolution_bucket)
        object.__setattr__(
            self,
            "sample_count",
            _require_positive_whole_decimal("sample_count", self.sample_count),
        )
        for field_name in (
            "aggregate_rule_ambiguity_score",
            "deadline_pressure_score",
            "resolution_risk_score",
            "depth_fade_rate",
            "spread_widening_rate",
            "quote_staleness_score",
            "liquidity_stress_score",
            "mismatch_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_probability_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in ("quote_staleness_seconds", "age_seconds"):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        _require_status("status", self.status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, allow_empty=False),
        )
        _validate_row_consistency(self)
        _require_hard_flags("row", self)


@dataclass(frozen=True)
class ResearchMarketResolutionLiquidityMismatchReasonCodeCount:
    reason_code: str
    count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_reason_code("reason_code", self.reason_code)
        object.__setattr__(
            self,
            "count",
            _require_positive_whole_decimal("count", self.count),
        )
        _require_hard_flags("reason_code_count", self)


@dataclass(frozen=True)
class ResearchMarketResolutionLiquidityMismatchReport:
    generated_at: datetime
    config_version: str
    status: str
    observation_count: Decimal
    sample_count: Decimal
    row_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    rule_ambiguity_watch_count: Decimal
    deadline_pressure_watch_count: Decimal
    depth_fade_watch_count: Decimal
    spread_widening_watch_count: Decimal
    quote_stale_count: Decimal
    max_mismatch_score: Decimal | None
    average_mismatch_score: Decimal | None
    rows: tuple[ResearchMarketResolutionLiquidityMismatchRow, ...]
    reason_code_counts: tuple[ResearchMarketResolutionLiquidityMismatchReasonCodeCount, ...]
    reason_codes: tuple[str, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_text("config_version", self.config_version)
        _require_status("status", self.status)
        for field_name in (
            "observation_count",
            "sample_count",
            "row_count",
            "pass_count",
            "watch_count",
            "block_count",
            "rule_ambiguity_watch_count",
            "deadline_pressure_watch_count",
            "depth_fade_watch_count",
            "spread_widening_watch_count",
            "quote_stale_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_whole_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in ("max_mismatch_score", "average_mismatch_score"):
            object.__setattr__(
                self,
                field_name,
                _require_optional_probability_decimal(field_name, getattr(self, field_name)),
            )
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
        if self.derived_validation_digest == "":
            object.__setattr__(
                self,
                "derived_validation_digest",
                _report_derived_validation_digest(self),
            )
        else:
            object.__setattr__(
                self,
                "derived_validation_digest",
                _require_sha256_digest(
                    "derived_validation_digest",
                    self.derived_validation_digest,
                ),
            )
        _validate_report_consistency(self)


def build_research_market_resolution_liquidity_mismatch_report(
    observations: Iterable[object],
    *,
    config: ResearchMarketResolutionLiquidityMismatchConfig,
    generated_at: datetime,
) -> ResearchMarketResolutionLiquidityMismatchReport:
    if type(config) is not ResearchMarketResolutionLiquidityMismatchConfig:
        raise ValueError("config must be a ResearchMarketResolutionLiquidityMismatchConfig")
    _require_hard_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    normalized = _normalize_observations(observations)
    for observation in normalized:
        _reject_future_observed_at(observation, generated_at_utc)
    rows = tuple(
        sorted(
            (
                _row_from_observation(
                    observation,
                    config=config,
                    generated_at=generated_at_utc,
                )
                for observation in normalized
            ),
            key=_row_key,
        ),
    )
    reason_codes = _report_reason_codes(rows)
    return ResearchMarketResolutionLiquidityMismatchReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        status=_report_status(rows),
        observation_count=_decimal_count(len(normalized)),
        sample_count=sum((row.sample_count for row in rows), ZERO),
        row_count=_decimal_count(len(rows)),
        pass_count=_status_count(rows, "pass"),
        watch_count=_status_count(rows, "watch"),
        block_count=_status_count(rows, "block"),
        rule_ambiguity_watch_count=_threshold_count(
            rows,
            "aggregate_rule_ambiguity_score",
            config.watch_rule_ambiguity_score,
        ),
        deadline_pressure_watch_count=_threshold_count(
            rows,
            "deadline_pressure_score",
            config.watch_deadline_pressure_score,
        ),
        depth_fade_watch_count=_threshold_count(
            rows,
            "depth_fade_rate",
            config.watch_depth_fade_rate,
        ),
        spread_widening_watch_count=_threshold_count(
            rows,
            "spread_widening_rate",
            config.watch_spread_widening_rate,
        ),
        quote_stale_count=_threshold_count(
            rows,
            "quote_staleness_seconds",
            config.watch_quote_staleness_seconds,
        ),
        max_mismatch_score=_max_mismatch_score(rows),
        average_mismatch_score=_average_mismatch_score(rows),
        rows=rows,
        reason_code_counts=_reason_code_counts(rows, reason_codes),
        reason_codes=reason_codes,
    )


def research_market_resolution_liquidity_mismatch_report_payload(
    report: ResearchMarketResolutionLiquidityMismatchReport,
) -> dict[str, Any]:
    if type(report) is not ResearchMarketResolutionLiquidityMismatchReport:
        raise ValueError("report must be a ResearchMarketResolutionLiquidityMismatchReport")
    _require_hard_flags("report", report)
    payload = _payload_value(report)
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    _validate_payload_digest(payload)
    return payload


def _row_from_observation(
    observation: ResearchMarketResolutionLiquidityMismatchObservation,
    *,
    config: ResearchMarketResolutionLiquidityMismatchConfig,
    generated_at: datetime,
) -> ResearchMarketResolutionLiquidityMismatchRow:
    quote_score = _quote_staleness_score(
        observation.quote_staleness_seconds,
        config.block_quote_staleness_seconds,
    )
    resolution_risk_score = _average_decimal(
        (
            observation.aggregate_rule_ambiguity_score,
            observation.deadline_pressure_score,
        ),
    )
    liquidity_stress_score = _average_decimal(
        (
            observation.depth_fade_rate,
            observation.spread_widening_rate,
            quote_score,
        ),
    )
    mismatch_score = _average_decimal((resolution_risk_score, liquidity_stress_score))
    status = _row_status(
        observation,
        quote_score=quote_score,
        mismatch_score=mismatch_score,
        config=config,
    )
    return ResearchMarketResolutionLiquidityMismatchRow(
        public_cluster=observation.public_cluster,
        resolution_bucket=observation.resolution_bucket,
        sample_count=observation.sample_count,
        aggregate_rule_ambiguity_score=observation.aggregate_rule_ambiguity_score,
        deadline_pressure_score=observation.deadline_pressure_score,
        resolution_risk_score=resolution_risk_score,
        depth_fade_rate=observation.depth_fade_rate,
        spread_widening_rate=observation.spread_widening_rate,
        quote_staleness_seconds=observation.quote_staleness_seconds,
        quote_staleness_score=quote_score,
        liquidity_stress_score=liquidity_stress_score,
        mismatch_score=mismatch_score,
        observed_at=observation.observed_at,
        age_seconds=_age_seconds(generated_at, observation.observed_at),
        status=status,
        reason_codes=_row_reason_codes(
            observation.reason_codes,
            observation=observation,
            status=status,
            config=config,
        ),
    )


def _row_status(
    observation: ResearchMarketResolutionLiquidityMismatchObservation,
    *,
    quote_score: Decimal,
    mismatch_score: Decimal,
    config: ResearchMarketResolutionLiquidityMismatchConfig,
) -> str:
    if (
        mismatch_score >= config.block_mismatch_score
        or observation.aggregate_rule_ambiguity_score >= config.block_rule_ambiguity_score
        or observation.deadline_pressure_score >= config.block_deadline_pressure_score
        or observation.depth_fade_rate >= config.block_depth_fade_rate
        or observation.spread_widening_rate >= config.block_spread_widening_rate
        or observation.quote_staleness_seconds >= config.block_quote_staleness_seconds
        or quote_score >= ONE
    ):
        return "block"
    if (
        mismatch_score >= config.watch_mismatch_score
        or observation.aggregate_rule_ambiguity_score >= config.watch_rule_ambiguity_score
        or observation.deadline_pressure_score >= config.watch_deadline_pressure_score
        or observation.depth_fade_rate >= config.watch_depth_fade_rate
        or observation.spread_widening_rate >= config.watch_spread_widening_rate
        or observation.quote_staleness_seconds >= config.watch_quote_staleness_seconds
    ):
        return "watch"
    return "pass"


def _row_reason_codes(
    input_reason_codes: tuple[str, ...],
    *,
    observation: ResearchMarketResolutionLiquidityMismatchObservation,
    status: str,
    config: ResearchMarketResolutionLiquidityMismatchConfig,
) -> tuple[str, ...]:
    reason_codes = {f"resolution_liquidity_mismatch_{status}"}
    reason_codes.add(
        _component_reason_code(
            "rule_ambiguity",
            observation.aggregate_rule_ambiguity_score,
            config.watch_rule_ambiguity_score,
            config.block_rule_ambiguity_score,
        ),
    )
    reason_codes.add(
        _component_reason_code(
            "deadline_pressure",
            observation.deadline_pressure_score,
            config.watch_deadline_pressure_score,
            config.block_deadline_pressure_score,
        ),
    )
    reason_codes.add(
        _component_reason_code(
            "depth_fade",
            observation.depth_fade_rate,
            config.watch_depth_fade_rate,
            config.block_depth_fade_rate,
        ),
    )
    reason_codes.add(
        _component_reason_code(
            "spread_widening",
            observation.spread_widening_rate,
            config.watch_spread_widening_rate,
            config.block_spread_widening_rate,
        ),
    )
    reason_codes.add(
        _quote_reason_code(
            observation.quote_staleness_seconds,
            config.watch_quote_staleness_seconds,
            config.block_quote_staleness_seconds,
        ),
    )
    for reason_code in input_reason_codes:
        reason_codes.add(f"input_{reason_code}")
    return _normalize_reason_codes("reason_codes", tuple(reason_codes), allow_empty=False)


def _component_reason_code(
    label: str,
    value: Decimal,
    watch_threshold: Decimal,
    block_threshold: Decimal,
) -> str:
    if value >= block_threshold:
        suffix = "block"
    elif value >= watch_threshold:
        suffix = "watch"
    else:
        suffix = "pass"
    return f"resolution_liquidity_{label}_{suffix}"


def _quote_reason_code(
    value: Decimal,
    watch_threshold: Decimal,
    block_threshold: Decimal,
) -> str:
    if value >= block_threshold:
        suffix = "block"
    elif value >= watch_threshold:
        suffix = "watch"
    else:
        suffix = "fresh"
    return f"resolution_liquidity_quote_staleness_{suffix}"


def _quote_staleness_score(value: Decimal, block_threshold: Decimal) -> Decimal:
    return _quantize(min(ONE, value / block_threshold))


def _normalize_observations(
    observations: Iterable[object],
) -> tuple[ResearchMarketResolutionLiquidityMismatchObservation, ...]:
    if isinstance(observations, (str, bytes)):
        raise ValueError("observations must be an iterable")
    try:
        values = tuple(observations)
    except TypeError as exc:
        raise ValueError("observations must be an iterable") from exc
    for value in values:
        if type(value) is not ResearchMarketResolutionLiquidityMismatchObservation:
            raise ValueError(
                "observations must contain "
                "ResearchMarketResolutionLiquidityMismatchObservation values",
            )
        _require_hard_flags("observation", value)
    return values


def _normalize_rows(
    rows: tuple[ResearchMarketResolutionLiquidityMismatchRow, ...],
) -> tuple[ResearchMarketResolutionLiquidityMismatchRow, ...]:
    if type(rows) is not tuple:
        raise ValueError("rows must be a tuple")
    for row in rows:
        if type(row) is not ResearchMarketResolutionLiquidityMismatchRow:
            raise ValueError(
                "rows must contain ResearchMarketResolutionLiquidityMismatchRow values",
            )
        _require_hard_flags("row", row)
    if rows != tuple(sorted(rows, key=_row_key)):
        raise ValueError("rows must use canonical sequence")
    return rows


def _normalize_reason_code_counts(
    counts: tuple[ResearchMarketResolutionLiquidityMismatchReasonCodeCount, ...],
) -> tuple[ResearchMarketResolutionLiquidityMismatchReasonCodeCount, ...]:
    if type(counts) is not tuple:
        raise ValueError("reason_code_counts must be a tuple")
    for count in counts:
        if type(count) is not ResearchMarketResolutionLiquidityMismatchReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "ResearchMarketResolutionLiquidityMismatchReasonCodeCount values",
            )
        _require_hard_flags("reason_code_count", count)
    if counts != tuple(sorted(counts, key=lambda count: count.reason_code)):
        raise ValueError("reason_code_counts must use canonical sequence")
    return counts


def _validate_row_consistency(
    row: ResearchMarketResolutionLiquidityMismatchRow,
) -> None:
    if row.resolution_risk_score != _average_decimal(
        (row.aggregate_rule_ambiguity_score, row.deadline_pressure_score),
    ):
        raise ValueError("resolution_risk_score must match row values")
    if row.liquidity_stress_score != _average_decimal(
        (row.depth_fade_rate, row.spread_widening_rate, row.quote_staleness_score),
    ):
        raise ValueError("liquidity_stress_score must match row values")
    if row.mismatch_score != _average_decimal(
        (row.resolution_risk_score, row.liquidity_stress_score),
    ):
        raise ValueError("mismatch_score must match row values")
    if f"resolution_liquidity_mismatch_{row.status}" not in row.reason_codes:
        raise ValueError("status must match reason_codes")


def _validate_report_consistency(
    report: ResearchMarketResolutionLiquidityMismatchReport,
) -> None:
    if report.observation_count != _decimal_count(len(report.rows)):
        raise ValueError("observation_count must match rows")
    if report.row_count != _decimal_count(len(report.rows)):
        raise ValueError("row_count must match rows")
    if report.sample_count != sum((row.sample_count for row in report.rows), ZERO):
        raise ValueError("sample_count must match rows")
    if report.pass_count != _status_count(report.rows, "pass"):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _status_count(report.rows, "watch"):
        raise ValueError("watch_count must match rows")
    if report.block_count != _status_count(report.rows, "block"):
        raise ValueError("block_count must match rows")
    if report.status != _report_status(report.rows):
        raise ValueError("status must match rows")
    if report.max_mismatch_score != _max_mismatch_score(report.rows):
        raise ValueError("max_mismatch_score must match rows")
    if report.average_mismatch_score != _average_mismatch_score(report.rows):
        raise ValueError("average_mismatch_score must match rows")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")
    if report.reason_code_counts != _reason_code_counts(report.rows, report.reason_codes):
        raise ValueError("reason_code_counts must match rows")
    if report.derived_validation_digest != _report_derived_validation_digest(report):
        raise ValueError("derived_validation_digest must match report values")


def _report_reason_codes(
    rows: tuple[ResearchMarketResolutionLiquidityMismatchRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return ("resolution_liquidity_mismatch_no_observations",)
    return _normalize_reason_codes(
        "reason_codes",
        tuple(reason_code for row in rows for reason_code in row.reason_codes),
        allow_empty=False,
    )


def _reason_code_counts(
    rows: tuple[ResearchMarketResolutionLiquidityMismatchRow, ...],
    reason_codes: tuple[str, ...],
) -> tuple[ResearchMarketResolutionLiquidityMismatchReasonCodeCount, ...]:
    if not rows:
        return (
            ResearchMarketResolutionLiquidityMismatchReasonCodeCount(
                reason_code=reason_codes[0],
                count=ONE,
            ),
        )
    counter: Counter[str] = Counter()
    for row in rows:
        counter.update(row.reason_codes)
    return tuple(
        ResearchMarketResolutionLiquidityMismatchReasonCodeCount(
            reason_code=reason_code,
            count=_decimal_count(count),
        )
        for reason_code, count in sorted(counter.items(), key=lambda item: item[0])
    )


def _report_status(rows: tuple[ResearchMarketResolutionLiquidityMismatchRow, ...]) -> str:
    if not rows or any(row.status == "block" for row in rows):
        return "block"
    if any(row.status == "watch" for row in rows):
        return "watch"
    return "pass"


def _status_count(
    rows: tuple[ResearchMarketResolutionLiquidityMismatchRow, ...],
    status: str,
) -> Decimal:
    return _decimal_count(sum(1 for row in rows if row.status == status))


def _threshold_count(
    rows: tuple[ResearchMarketResolutionLiquidityMismatchRow, ...],
    field_name: str,
    threshold: Decimal,
) -> Decimal:
    return _decimal_count(sum(1 for row in rows if getattr(row, field_name) >= threshold))


def _max_mismatch_score(
    rows: tuple[ResearchMarketResolutionLiquidityMismatchRow, ...],
) -> Decimal | None:
    if not rows:
        return None
    return max(row.mismatch_score for row in rows)


def _average_mismatch_score(
    rows: tuple[ResearchMarketResolutionLiquidityMismatchRow, ...],
) -> Decimal | None:
    if not rows:
        return None
    return _average_decimal(tuple(row.mismatch_score for row in rows))


def _average_decimal(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        raise ValueError("values must be nonempty")
    return _quantize(sum(values, ZERO) / Decimal(len(values)))


def _age_seconds(generated_at: datetime, observed_at: datetime) -> Decimal:
    delta = generated_at - observed_at
    return (
        Decimal(delta.days * 86_400)
        + Decimal(delta.seconds)
        + (Decimal(delta.microseconds) / Decimal("1000000"))
    )


def _reject_future_observed_at(
    observation: ResearchMarketResolutionLiquidityMismatchObservation,
    generated_at: datetime,
) -> None:
    if observation.observed_at > generated_at:
        raise ValueError("observed_at must not be after generated_at")


def _row_key(row: ResearchMarketResolutionLiquidityMismatchRow) -> tuple[str, str]:
    return (row.public_cluster, row.resolution_bucket)


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


def _payload_without_digest(
    payload: dict[str, Any],
) -> dict[str, Any]:
    return {
        key: value
        for key, value in payload.items()
        if key != _DERIVED_VALIDATION_DIGEST_FIELD
    }


def _report_derived_validation_digest(
    report: ResearchMarketResolutionLiquidityMismatchReport,
) -> str:
    payload = _payload_value(report)
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    return _digest_payload(_payload_without_digest(payload))


def _digest_payload(payload: dict[str, Any]) -> str:
    encoded = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return sha256(encoded).hexdigest()


def _validate_payload_digest(payload: dict[str, Any]) -> None:
    digest_value = payload.get(_DERIVED_VALIDATION_DIGEST_FIELD)
    _require_sha256_digest(_DERIVED_VALIDATION_DIGEST_FIELD, digest_value)
    if digest_value != _digest_payload(_payload_without_digest(payload)):
        raise ValueError("derived_validation_digest must match payload values")


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
    return normalized


def _require_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _require_probability_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < ZERO or normalized > ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return _quantize(normalized)


def _require_optional_probability_decimal(
    field_name: str,
    value: object,
) -> Decimal | None:
    if value is None:
        return None
    return _require_probability_decimal(field_name, value)


def _require_positive_whole_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_positive_decimal(field_name, value)
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{field_name} must be a whole count")
    return normalized


def _require_nonnegative_whole_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_nonnegative_decimal(field_name, value)
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{field_name} must be a whole count")
    return normalized


def _require_increasing_threshold(
    watch_field_name: str,
    watch_value: Decimal,
    block_field_name: str,
    block_value: Decimal,
) -> None:
    if block_value <= watch_value:
        raise ValueError(f"{block_field_name} must exceed {watch_field_name}")


def _decimal_count(value: int) -> Decimal:
    if type(value) is not int:
        raise ValueError("count value must be an int")
    if value < 0:
        raise ValueError("count value must be nonnegative")
    return Decimal(value)


def _quantize(value: Decimal) -> Decimal:
    return value.quantize(RATIO_QUANTUM)


def _require_public_label(field_name: str, value: object) -> None:
    _require_canonical_text(field_name, value)
    if any(fragment in value for fragment in _PUBLIC_LABEL_DENY_FRAGMENTS):
        raise ValueError(f"{field_name} must not expose raw identifiers")


def _require_canonical_text(field_name: str, value: object) -> None:
    if type(value) is not str or not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a nonempty canonical public label")
    allowed = "abcdefghijklmnopqrstuvwxyz0123456789-"
    if any(character not in allowed for character in value):
        raise ValueError(f"{field_name} must use canonical public text")


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
        raise ValueError(f"{field_name} must be a nonempty canonical code")
    allowed = "abcdefghijklmnopqrstuvwxyz0123456789_"
    if any(character not in allowed for character in value):
        raise ValueError(f"{field_name} must contain deterministic code text")


def _require_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in STATUSES:
        raise ValueError(f"{field_name} must be one of {STATUSES}")


def _require_sha256_digest(field_name: str, value: object) -> str:
    if (
        type(value) is not str
        or len(value) != 64
        or any(character not in "0123456789abcdef" for character in value)
    ):
        raise ValueError(f"{field_name} must be a lowercase sha256 digest")
    return value


def _field_value(value: object, field_name: str) -> object:
    if is_dataclass(value):
        for field in fields(value):
            if field.name == field_name:
                return getattr(value, field_name)
    if hasattr(value, field_name):
        return getattr(value, field_name)
    raise ValueError(f"{field_name} is required")


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if _field_value(value, field_name) is not True:
            raise ValueError(f"{label} {field_name} must be True")
