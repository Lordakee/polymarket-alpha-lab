"""Pure report-only book observation quality reducer for manual research."""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable
from dataclasses import dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation
import json
from hashlib import sha256
from typing import Any


__all__ = (
    "ResearchMarketBookObservation",
    "ResearchMarketBookObservationQualityConfig",
    "ResearchMarketBookObservationQualityReasonCodeCount",
    "ResearchMarketBookObservationQualityReport",
    "ResearchMarketBookObservationQualityRow",
    "build_research_market_book_observation_quality_report",
    "research_market_book_observation_quality_report_payload",
)


DEFAULT_CONFIG_VERSION = "research-market-book-observation-quality-report-v0"
STATUSES = ("pass", "watch", "block")
ZERO = Decimal("0")
ONE = Decimal("1")
RATIO_QUANTUM = Decimal("0.000001")


@dataclass(frozen=True)
class ResearchMarketBookObservationQualityConfig:
    config_version: str = DEFAULT_CONFIG_VERSION
    max_fresh_age_seconds: Decimal = Decimal("600")
    expected_observation_count: Decimal = Decimal("3")
    pass_max_average_spread: Decimal = Decimal("0.040000")
    block_max_average_spread: Decimal = Decimal("0.060000")
    spread_score_zero_at: Decimal = Decimal("0.050000")
    pass_max_average_fee_rate: Decimal = Decimal("0.020000")
    block_max_average_fee_rate: Decimal = Decimal("0.050000")
    fee_score_zero_at: Decimal = Decimal("0.050000")
    watch_missing_observation_pressure: Decimal = Decimal("0.250000")
    block_missing_observation_pressure: Decimal = Decimal("0.500000")
    pass_quality_score: Decimal = Decimal("0.700000")
    watch_quality_score: Decimal = Decimal("0.400000")
    freshness_weight: Decimal = Decimal("0.300000")
    spread_stability_weight: Decimal = Decimal("0.300000")
    fee_friction_weight: Decimal = Decimal("0.200000")
    observation_completeness_weight: Decimal = Decimal("0.200000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchMarketBookObservationQualityConfig, "config")
        _require_canonical_string("config_version", self.config_version)
        object.__setattr__(
            self,
            "max_fresh_age_seconds",
            _require_positive_decimal("max_fresh_age_seconds", self.max_fresh_age_seconds),
        )
        object.__setattr__(
            self,
            "expected_observation_count",
            _require_positive_whole_decimal(
                "expected_observation_count",
                self.expected_observation_count,
            ),
        )
        for field_name in (
            "pass_max_average_spread",
            "block_max_average_spread",
            "spread_score_zero_at",
            "pass_max_average_fee_rate",
            "block_max_average_fee_rate",
            "fee_score_zero_at",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_positive_decimal(field_name, getattr(self, field_name)),
            )
        if self.block_max_average_spread <= self.pass_max_average_spread:
            raise ValueError("block_max_average_spread must exceed pass_max_average_spread")
        if self.block_max_average_fee_rate <= self.pass_max_average_fee_rate:
            raise ValueError(
                "block_max_average_fee_rate must exceed pass_max_average_fee_rate",
            )
        for field_name in (
            "watch_missing_observation_pressure",
            "block_missing_observation_pressure",
            "pass_quality_score",
            "watch_quality_score",
            "freshness_weight",
            "spread_stability_weight",
            "fee_friction_weight",
            "observation_completeness_weight",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_probability_decimal(field_name, getattr(self, field_name)),
            )
        if self.block_missing_observation_pressure <= self.watch_missing_observation_pressure:
            raise ValueError(
                "block_missing_observation_pressure must exceed "
                "watch_missing_observation_pressure",
            )
        if self.pass_quality_score <= self.watch_quality_score:
            raise ValueError("pass_quality_score must exceed watch_quality_score")
        weight_sum = _quantize(
            self.freshness_weight
            + self.spread_stability_weight
            + self.fee_friction_weight
            + self.observation_completeness_weight,
        )
        if weight_sum != ONE:
            raise ValueError("quality score weights must sum to 1")
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class ResearchMarketBookObservation:
    observation_id: str
    market_slug: str
    observed_at: datetime
    best_bid_price: Decimal
    best_ask_price: Decimal
    bid_depth: Decimal
    ask_depth: Decimal
    fee_rate: Decimal
    reason_codes: tuple[str, ...] = ()
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchMarketBookObservation, "observation")
        _require_canonical_string("observation_id", self.observation_id)
        _require_canonical_string("market_slug", self.market_slug)
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in ("best_bid_price", "best_ask_price", "fee_rate"):
            object.__setattr__(
                self,
                field_name,
                _require_probability_decimal(field_name, getattr(self, field_name)),
            )
        if self.best_ask_price <= self.best_bid_price:
            raise ValueError("best_ask_price must exceed best_bid_price")
        for field_name in ("bid_depth", "ask_depth"):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, allow_empty=True),
        )
        _require_hard_flags("observation", self)


@dataclass(frozen=True)
class ResearchMarketBookObservationQualityRow:
    market_group_ref: str
    observation_count: Decimal
    fresh_observation_count: Decimal
    stale_observation_count: Decimal
    latest_observed_at: datetime
    latest_observation_age_seconds: Decimal
    average_spread: Decimal
    max_spread: Decimal
    spread_range: Decimal
    average_fee_rate: Decimal
    max_fee_rate: Decimal
    min_bid_depth: Decimal
    min_ask_depth: Decimal
    freshness_score: Decimal
    spread_stability_score: Decimal
    fee_friction_score: Decimal
    observation_completeness_score: Decimal
    missing_observation_pressure: Decimal
    quality_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchMarketBookObservationQualityRow, "row")
        _require_canonical_string("market_group_ref", self.market_group_ref)
        for field_name in (
            "observation_count",
            "fresh_observation_count",
            "stale_observation_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_whole_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "latest_observed_at",
            _as_utc("latest_observed_at", self.latest_observed_at),
        )
        for field_name in (
            "latest_observation_age_seconds",
            "average_spread",
            "max_spread",
            "spread_range",
            "average_fee_rate",
            "max_fee_rate",
            "min_bid_depth",
            "min_ask_depth",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "freshness_score",
            "spread_stability_score",
            "fee_friction_score",
            "observation_completeness_score",
            "missing_observation_pressure",
            "quality_score",
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
            _normalize_reason_codes("reason_codes", self.reason_codes, allow_empty=False),
        )
        _require_hard_flags("row", self)
        _validate_row_consistency(self)


@dataclass(frozen=True)
class ResearchMarketBookObservationQualityReasonCodeCount:
    reason_code: str
    count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchMarketBookObservationQualityReasonCodeCount,
            "reason_code_count",
        )
        _require_canonical_string("reason_code", self.reason_code)
        object.__setattr__(
            self,
            "count",
            _require_positive_whole_decimal("count", self.count),
        )
        _require_hard_flags("reason_code_count", self)


@dataclass(frozen=True)
class ResearchMarketBookObservationQualityReport:
    generated_at: datetime
    config_version: str
    market_count: Decimal
    observation_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    fresh_observation_count: Decimal
    stale_observation_count: Decimal
    max_missing_observation_pressure: Decimal
    average_quality_score: Decimal | None
    status: str
    rows: tuple[ResearchMarketBookObservationQualityRow, ...]
    reason_code_counts: tuple[ResearchMarketBookObservationQualityReasonCodeCount, ...]
    reason_codes: tuple[str, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchMarketBookObservationQualityReport, "report")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        for field_name in (
            "market_count",
            "observation_count",
            "pass_count",
            "watch_count",
            "block_count",
            "fresh_observation_count",
            "stale_observation_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_whole_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "max_missing_observation_pressure",
            _require_probability_decimal(
                "max_missing_observation_pressure",
                self.max_missing_observation_pressure,
            ),
        )
        object.__setattr__(
            self,
            "average_quality_score",
            _require_optional_probability_decimal(
                "average_quality_score",
                self.average_quality_score,
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
            _normalize_reason_codes("reason_codes", self.reason_codes, allow_empty=False),
        )
        _require_hard_flags("report", self)
        _validate_report_consistency(self)
        expected_digest = _derived_report_digest(self)
        if self.derived_validation_digest:
            _require_hex_digest("derived_validation_digest", self.derived_validation_digest)
            if self.derived_validation_digest != expected_digest:
                raise ValueError("derived_validation_digest must match report fields")
        else:
            object.__setattr__(self, "derived_validation_digest", expected_digest)


def build_research_market_book_observation_quality_report(
    observations: Iterable[ResearchMarketBookObservation],
    *,
    config: ResearchMarketBookObservationQualityConfig,
    generated_at: datetime,
) -> ResearchMarketBookObservationQualityReport:
    if type(config) is not ResearchMarketBookObservationQualityConfig:
        raise ValueError("config must be a ResearchMarketBookObservationQualityConfig")
    _require_hard_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    normalized = _normalize_observations(observations)
    for item in normalized:
        if item.observed_at > generated_at_utc:
            raise ValueError("observed_at must not be after generated_at")

    grouped: dict[str, list[ResearchMarketBookObservation]] = {}
    for item in normalized:
        grouped.setdefault(item.market_slug, []).append(item)
    rows = tuple(
        _quality_row_from_observations(
            market_group_ref=f"book_observation_group_{index:03d}",
            observations=tuple(grouped[market_slug]),
            config=config,
            generated_at=generated_at_utc,
        )
        for index, market_slug in enumerate(sorted(grouped), start=1)
    )
    reason_codes = _summary_reason_codes(rows)
    return ResearchMarketBookObservationQualityReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        market_count=_decimal_count(len(rows)),
        observation_count=sum((row.observation_count for row in rows), ZERO),
        pass_count=_decimal_count(_status_count(rows, "pass")),
        watch_count=_decimal_count(_status_count(rows, "watch")),
        block_count=_decimal_count(_status_count(rows, "block")),
        fresh_observation_count=sum((row.fresh_observation_count for row in rows), ZERO),
        stale_observation_count=sum((row.stale_observation_count for row in rows), ZERO),
        max_missing_observation_pressure=_max_or_zero(
            tuple(row.missing_observation_pressure for row in rows),
        ),
        average_quality_score=_average_quality_score(rows),
        status=_summary_status(rows),
        rows=rows,
        reason_code_counts=_reason_code_counts(rows, reason_codes),
        reason_codes=reason_codes,
    )


def research_market_book_observation_quality_report_payload(
    report: ResearchMarketBookObservationQualityReport,
) -> dict[str, Any]:
    if type(report) is not ResearchMarketBookObservationQualityReport:
        raise ValueError("report must be a ResearchMarketBookObservationQualityReport")
    _require_hard_flags("report", report)
    payload = _payload_value(report)
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    return payload


def _quality_row_from_observations(
    *,
    market_group_ref: str,
    observations: tuple[ResearchMarketBookObservation, ...],
    config: ResearchMarketBookObservationQualityConfig,
    generated_at: datetime,
) -> ResearchMarketBookObservationQualityRow:
    sorted_observations = tuple(sorted(observations, key=_observation_sort_key))
    ages = tuple(_age_seconds(generated_at, item.observed_at) for item in sorted_observations)
    latest = max(sorted_observations, key=lambda item: item.observed_at)
    latest_age = _age_seconds(generated_at, latest.observed_at)
    fresh_count = sum(1 for age in ages if age <= config.max_fresh_age_seconds)
    stale_count = len(sorted_observations) - fresh_count
    spreads = tuple(item.best_ask_price - item.best_bid_price for item in sorted_observations)
    fee_rates = tuple(item.fee_rate for item in sorted_observations)
    freshness_score = _ratio_score(_decimal_count(fresh_count), _decimal_count(len(ages)))
    observation_completeness_score = _quantize(
        min(ONE, _decimal_count(len(sorted_observations)) / config.expected_observation_count),
    )
    missing_pressure = _quantize(ONE - observation_completeness_score)
    average_spread = _average_decimal(spreads)
    max_spread = max(spreads)
    average_fee_rate = _average_decimal(fee_rates)
    max_fee_rate = max(fee_rates)
    spread_stability_score = _inverse_ratio_score(average_spread, config.spread_score_zero_at)
    fee_friction_score = _inverse_ratio_score(average_fee_rate, config.fee_score_zero_at)
    quality_score = _quality_score(
        freshness_score=freshness_score,
        spread_stability_score=spread_stability_score,
        fee_friction_score=fee_friction_score,
        observation_completeness_score=observation_completeness_score,
        config=config,
    )
    status = _row_status(
        quality_score=quality_score,
        average_spread=average_spread,
        average_fee_rate=average_fee_rate,
        missing_observation_pressure=missing_pressure,
        config=config,
    )
    return ResearchMarketBookObservationQualityRow(
        market_group_ref=market_group_ref,
        observation_count=_decimal_count(len(sorted_observations)),
        fresh_observation_count=_decimal_count(fresh_count),
        stale_observation_count=_decimal_count(stale_count),
        latest_observed_at=latest.observed_at,
        latest_observation_age_seconds=latest_age,
        average_spread=average_spread,
        max_spread=max_spread,
        spread_range=_quantize(max_spread - min(spreads)),
        average_fee_rate=average_fee_rate,
        max_fee_rate=max_fee_rate,
        min_bid_depth=min(item.bid_depth for item in sorted_observations),
        min_ask_depth=min(item.ask_depth for item in sorted_observations),
        freshness_score=freshness_score,
        spread_stability_score=spread_stability_score,
        fee_friction_score=fee_friction_score,
        observation_completeness_score=observation_completeness_score,
        missing_observation_pressure=missing_pressure,
        quality_score=quality_score,
        status=status,
        reason_codes=_row_reason_codes(
            observations=sorted_observations,
            stale_count=stale_count,
            average_spread=average_spread,
            average_fee_rate=average_fee_rate,
            missing_observation_pressure=missing_pressure,
            status=status,
            config=config,
        ),
    )


def _quality_score(
    *,
    freshness_score: Decimal,
    spread_stability_score: Decimal,
    fee_friction_score: Decimal,
    observation_completeness_score: Decimal,
    config: ResearchMarketBookObservationQualityConfig,
) -> Decimal:
    return _quantize(
        freshness_score * config.freshness_weight
        + spread_stability_score * config.spread_stability_weight
        + fee_friction_score * config.fee_friction_weight
        + observation_completeness_score * config.observation_completeness_weight,
    )


def _row_status(
    *,
    quality_score: Decimal,
    average_spread: Decimal,
    average_fee_rate: Decimal,
    missing_observation_pressure: Decimal,
    config: ResearchMarketBookObservationQualityConfig,
) -> str:
    if (
        quality_score < config.watch_quality_score
        or average_spread >= config.block_max_average_spread
        or average_fee_rate >= config.block_max_average_fee_rate
        or missing_observation_pressure >= config.block_missing_observation_pressure
    ):
        return "block"
    if (
        quality_score < config.pass_quality_score
        or average_spread >= config.pass_max_average_spread
        or average_fee_rate >= config.pass_max_average_fee_rate
        or missing_observation_pressure >= config.watch_missing_observation_pressure
    ):
        return "watch"
    return "pass"


def _row_reason_codes(
    *,
    observations: tuple[ResearchMarketBookObservation, ...],
    stale_count: int,
    average_spread: Decimal,
    average_fee_rate: Decimal,
    missing_observation_pressure: Decimal,
    status: str,
    config: ResearchMarketBookObservationQualityConfig,
) -> tuple[str, ...]:
    reason_codes: set[str] = {f"market_book_observation_quality_{status}"}
    reason_codes.add("book_depth_stale" if stale_count else "book_depth_fresh")
    reason_codes.add(
        _high_value_component_reason(
            prefix="spread_stability",
            value=average_spread,
            pass_threshold=config.pass_max_average_spread,
            block_threshold=config.block_max_average_spread,
        ),
    )
    reason_codes.add(
        _high_value_component_reason(
            prefix="fee_friction",
            value=average_fee_rate,
            pass_threshold=config.pass_max_average_fee_rate,
            block_threshold=config.block_max_average_fee_rate,
        ),
    )
    reason_codes.add(
        _high_value_component_reason(
            prefix="missing_observation_pressure",
            value=missing_observation_pressure,
            pass_threshold=config.watch_missing_observation_pressure,
            block_threshold=config.block_missing_observation_pressure,
        ),
    )
    for reason_code in tuple(code for item in observations for code in item.reason_codes):
        reason_codes.add(f"input_{reason_code}")
    return tuple(sorted(reason_codes))


def _high_value_component_reason(
    *,
    prefix: str,
    value: Decimal,
    pass_threshold: Decimal,
    block_threshold: Decimal,
) -> str:
    if value >= block_threshold:
        return f"{prefix}_block"
    if value >= pass_threshold:
        return f"{prefix}_watch"
    return f"{prefix}_pass"


def _normalize_observations(
    observations: Iterable[ResearchMarketBookObservation],
) -> tuple[ResearchMarketBookObservation, ...]:
    if isinstance(observations, (str, bytes)):
        raise ValueError("observations must be an iterable")
    try:
        values = tuple(observations)
    except TypeError as exc:
        raise ValueError("observations must be an iterable") from exc
    for value in values:
        if type(value) is not ResearchMarketBookObservation:
            raise ValueError("observations must contain ResearchMarketBookObservation values")
        _require_hard_flags("observation", value)
    return values


def _normalize_rows(
    rows: tuple[ResearchMarketBookObservationQualityRow, ...],
) -> tuple[ResearchMarketBookObservationQualityRow, ...]:
    if type(rows) is not tuple:
        raise ValueError("rows must be a tuple")
    for row in rows:
        if type(row) is not ResearchMarketBookObservationQualityRow:
            raise ValueError("rows must contain ResearchMarketBookObservationQualityRow values")
        _require_hard_flags("row", row)
    sorted_rows = tuple(sorted(rows, key=lambda item: item.market_group_ref))
    if rows != sorted_rows:
        raise ValueError("rows must be sorted by market_group_ref")
    return rows


def _normalize_reason_code_counts(
    counts: tuple[ResearchMarketBookObservationQualityReasonCodeCount, ...],
) -> tuple[ResearchMarketBookObservationQualityReasonCodeCount, ...]:
    if type(counts) is not tuple:
        raise ValueError("reason_code_counts must be a tuple")
    for count in counts:
        if type(count) is not ResearchMarketBookObservationQualityReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "ResearchMarketBookObservationQualityReasonCodeCount values",
            )
        _require_hard_flags("reason_code_count", count)
    sorted_counts = tuple(sorted(counts, key=lambda item: item.reason_code))
    if counts != sorted_counts:
        raise ValueError("reason_code_counts must be sorted by reason_code")
    return counts


def _validate_row_consistency(row: ResearchMarketBookObservationQualityRow) -> None:
    if row.observation_count <= ZERO:
        raise ValueError("observation_count must be positive")
    if row.fresh_observation_count + row.stale_observation_count != row.observation_count:
        raise ValueError("fresh and stale counts must match observation_count")
    if row.max_spread < row.average_spread:
        raise ValueError("max_spread must cover average_spread")
    if row.max_fee_rate < row.average_fee_rate:
        raise ValueError("max_fee_rate must cover average_fee_rate")
    if row.observation_completeness_score + row.missing_observation_pressure != ONE:
        raise ValueError("missing_observation_pressure must match completeness")
    if f"market_book_observation_quality_{row.status}" not in row.reason_codes:
        raise ValueError("status must match reason_codes")


def _validate_report_consistency(report: ResearchMarketBookObservationQualityReport) -> None:
    if report.market_count != _decimal_count(len(report.rows)):
        raise ValueError("market_count must match rows")
    if report.observation_count != sum((row.observation_count for row in report.rows), ZERO):
        raise ValueError("observation_count must match rows")
    if report.pass_count != _decimal_count(_status_count(report.rows, "pass")):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _decimal_count(_status_count(report.rows, "watch")):
        raise ValueError("watch_count must match rows")
    if report.block_count != _decimal_count(_status_count(report.rows, "block")):
        raise ValueError("block_count must match rows")
    if report.fresh_observation_count != sum(
        (row.fresh_observation_count for row in report.rows),
        ZERO,
    ):
        raise ValueError("fresh_observation_count must match rows")
    if report.stale_observation_count != sum(
        (row.stale_observation_count for row in report.rows),
        ZERO,
    ):
        raise ValueError("stale_observation_count must match rows")
    if report.max_missing_observation_pressure != _max_or_zero(
        tuple(row.missing_observation_pressure for row in report.rows),
    ):
        raise ValueError("max_missing_observation_pressure must match rows")
    if report.average_quality_score != _average_quality_score(report.rows):
        raise ValueError("average_quality_score must match rows")
    if report.status != _summary_status(report.rows):
        raise ValueError("status must match rows")
    if report.reason_codes != _summary_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")


def _summary_status(rows: tuple[ResearchMarketBookObservationQualityRow, ...]) -> str:
    if not rows or any(row.status == "block" for row in rows):
        return "block"
    if any(row.status == "watch" for row in rows):
        return "watch"
    return "pass"


def _summary_reason_codes(
    rows: tuple[ResearchMarketBookObservationQualityRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return ("no_book_observations",)
    if all(row.status == "pass" for row in rows):
        return ("market_book_observation_quality_pass",)
    return tuple(sorted({code for row in rows for code in row.reason_codes}))


def _reason_code_counts(
    rows: tuple[ResearchMarketBookObservationQualityRow, ...],
    reason_codes: tuple[str, ...],
) -> tuple[ResearchMarketBookObservationQualityReasonCodeCount, ...]:
    if not rows:
        return (
            ResearchMarketBookObservationQualityReasonCodeCount(
                reason_code=reason_codes[0],
                count=ONE,
            ),
        )
    counts: Counter[str] = Counter()
    for row in rows:
        counts.update(row.reason_codes)
    return tuple(
        ResearchMarketBookObservationQualityReasonCodeCount(
            reason_code=reason_code,
            count=_decimal_count(count),
        )
        for reason_code, count in sorted(counts.items(), key=lambda item: item[0])
    )


def _average_quality_score(
    rows: tuple[ResearchMarketBookObservationQualityRow, ...],
) -> Decimal | None:
    if not rows:
        return None
    return _average_decimal(tuple(row.quality_score for row in rows))


def _average_decimal(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        raise ValueError("values must be nonempty")
    return _quantize(sum(values, ZERO) / Decimal(len(values)))


def _ratio_score(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator <= ZERO:
        raise ValueError("denominator must be positive")
    return _quantize(min(ONE, numerator / denominator))


def _inverse_ratio_score(value: Decimal, zero_at: Decimal) -> Decimal:
    if zero_at <= ZERO:
        raise ValueError("zero_at must be positive")
    return _quantize(max(ZERO, ONE - (value / zero_at)))


def _max_or_zero(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return ZERO
    return max(values)


def _age_seconds(generated_at: datetime, observed_at: datetime) -> Decimal:
    delta = generated_at - observed_at
    return (
        Decimal(delta.days * 86_400)
        + Decimal(delta.seconds)
        + (Decimal(delta.microseconds) / Decimal("1000000"))
    )


def _status_count(rows: tuple[ResearchMarketBookObservationQualityRow, ...], status: str) -> int:
    return sum(1 for row in rows if row.status == status)


def _observation_sort_key(
    value: ResearchMarketBookObservation,
) -> tuple[str, str, datetime]:
    return value.market_slug, value.observation_id, value.observed_at


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


def _derived_report_digest(report: ResearchMarketBookObservationQualityReport) -> str:
    payload = _payload_value(report)
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    payload = dict(payload)
    payload.pop("derived_validation_digest", None)
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return sha256(encoded.encode("utf-8")).hexdigest()


def _as_utc(field_name: str, value: datetime) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_exact_type(value: object, expected_type: type[object], field_name: str) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{field_name} must be {expected_type.__name__}")


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


def _decimal_count(value: int) -> Decimal:
    if type(value) is not int:
        raise ValueError("count source must be an int")
    if value < 0:
        raise ValueError("count source must be nonnegative")
    return Decimal(value)


def _quantize(value: Decimal) -> Decimal:
    return value.quantize(RATIO_QUANTUM)


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str or not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a nonempty canonical string")


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
    _require_canonical_string(field_name, value)
    allowed = set("abcdefghijklmnopqrstuvwxyz0123456789_")
    if any(character not in allowed for character in value):
        raise ValueError(f"{field_name} must contain lowercase snake-case values")


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        flag = getattr(value, field_name, None)
        if type(flag) is not bool or flag is not True:
            raise ValueError(f"{label}.{field_name} must be True")


def _require_hex_digest(field_name: str, value: object) -> None:
    if type(value) is not str or len(value) != 64:
        raise ValueError(f"{field_name} must be a 64-character hex string")
    allowed = set("0123456789abcdef")
    if any(character not in allowed for character in value):
        raise ValueError(f"{field_name} must be a 64-character hex string")
