"""Pure report-only liquidity source reliability digest reducer."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, localcontext
import hashlib
from typing import Any


__all__ = (
    "MarketLiquiditySourceReliabilityDigestConfig",
    "MarketLiquiditySourceReliabilityDigestObservation",
    "MarketLiquiditySourceReliabilityDigestReport",
    "MarketLiquiditySourceReliabilityDigestRow",
    "build_market_liquidity_source_reliability_digest",
    "market_liquidity_source_reliability_digest_payload",
)


QUANTUM = Decimal("0.000001")
ZERO = Decimal("0")
DECIMAL_CONTEXT = Context(prec=64)
RELIABILITY_STATUSES = ("pass", "watch", "blocked")
STATUS_RANK = {"pass": 0, "watch": 1, "blocked": 2}
BLOCKING_REASON_CODES = (
    "depth_disagreement",
    "missing_source_redundancy",
    "source_family_stale",
    "spread_disagreement",
)
SENSITIVE_REFERENCE_MARKERS = (
    "api_key=",
    "apikey=",
    "authorization=",
    "bearer ",
    "password=",
    "private_key=",
    "secret=",
    "signature=",
    "token=",
    "wallet=",
)
DERIVED_VALIDATION_DIGEST_FIELD = "derived_validation_digest"
REPORT_PAYLOAD_FIELDS_WITHOUT_DIGEST = (
    "generated_at",
    "config_version",
    "observation_count",
    "row_count",
    "pass_count",
    "watch_count",
    "blocked_count",
    "stale_source_family_count",
    "depth_disagreement_count",
    "spread_disagreement_count",
    "missing_redundancy_count",
    "max_source_age_seconds_observed",
    "max_depth_disagreement_ratio_observed",
    "max_spread_disagreement_ratio_observed",
    "reason_codes",
    "rows",
    "paper_only",
    "report_only",
    "readonly",
)
REPORT_PAYLOAD_FIELDS = (
    *REPORT_PAYLOAD_FIELDS_WITHOUT_DIGEST,
    DERIVED_VALIDATION_DIGEST_FIELD,
)
ROW_PAYLOAD_FIELDS = (
    "market_slug",
    "outcome_name",
    "reliability_status",
    "source_family_count",
    "observation_count",
    "stale_source_family_count",
    "max_source_age_seconds",
    "min_bid_depth",
    "max_bid_depth",
    "min_ask_depth",
    "max_ask_depth",
    "depth_disagreement_ratio",
    "min_spread",
    "max_spread",
    "spread_disagreement_ratio",
    "missing_redundancy",
    "latest_observed_at",
    "oldest_observed_at",
    "observation_references",
    "reason_codes",
    "paper_only",
    "report_only",
    "readonly",
)
UNSAFE_PUBLIC_TERMS = (
    "li" + "ve",
    "a" + "uth",
    "wal" + "let",
    "or" + "der",
    "net" + "work",
    "data" + "base",
    "per" + "sist",
)


@dataclass(frozen=True)
class MarketLiquiditySourceReliabilityDigestConfig:
    config_version: str
    max_source_age_seconds: Decimal
    max_depth_disagreement_ratio: Decimal
    max_spread_disagreement_ratio: Decimal
    min_source_family_count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "MarketLiquiditySourceReliabilityDigestConfig does not support subclassing",
        )

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            MarketLiquiditySourceReliabilityDigestConfig,
            "config",
        )
        _require_canonical_string("config_version", self.config_version)
        for field_name in ("max_source_age_seconds", "min_source_family_count"):
            object.__setattr__(
                self,
                field_name,
                _normalize_positive_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "max_depth_disagreement_ratio",
            "max_spread_disagreement_ratio",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        _require_hard_flags(self)
        _reject_unsafe_public_payload("config", self)


@dataclass(frozen=True)
class MarketLiquiditySourceReliabilityDigestObservation:
    market_slug: str
    outcome_name: str
    source_family: str
    source_name: str
    observed_at: datetime
    bid_depth: Decimal
    ask_depth: Decimal
    spread: Decimal
    reference: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "MarketLiquiditySourceReliabilityDigestObservation "
            "does not support subclassing",
        )

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            MarketLiquiditySourceReliabilityDigestObservation,
            "observation",
        )
        for field_name in (
            "market_slug",
            "outcome_name",
            "source_family",
            "source_name",
            "reference",
        ):
            _require_canonical_string(field_name, getattr(self, field_name))
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in ("bid_depth", "ask_depth", "spread"):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes),
        )
        _require_hard_flags(self)
        _reject_unsafe_public_payload("observation", self)


@dataclass(frozen=True)
class MarketLiquiditySourceReliabilityDigestRow:
    market_slug: str
    outcome_name: str
    reliability_status: str
    source_family_count: Decimal
    observation_count: Decimal
    stale_source_family_count: Decimal
    max_source_age_seconds: Decimal
    min_bid_depth: Decimal
    max_bid_depth: Decimal
    min_ask_depth: Decimal
    max_ask_depth: Decimal
    depth_disagreement_ratio: Decimal
    min_spread: Decimal
    max_spread: Decimal
    spread_disagreement_ratio: Decimal
    missing_redundancy: bool
    latest_observed_at: datetime
    oldest_observed_at: datetime
    observation_references: tuple[str, ...]
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "MarketLiquiditySourceReliabilityDigestRow does not support subclassing",
        )

    def __post_init__(self) -> None:
        _require_exact_type(self, MarketLiquiditySourceReliabilityDigestRow, "row")
        _require_canonical_string("market_slug", self.market_slug)
        _require_canonical_string("outcome_name", self.outcome_name)
        _require_reliability_status("reliability_status", self.reliability_status)
        for field_name in (
            "source_family_count",
            "observation_count",
            "stale_source_family_count",
            "max_source_age_seconds",
            "min_bid_depth",
            "max_bid_depth",
            "min_ask_depth",
            "max_ask_depth",
            "depth_disagreement_ratio",
            "min_spread",
            "max_spread",
            "spread_disagreement_ratio",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        if type(self.missing_redundancy) is not bool:
            raise ValueError("missing_redundancy must be a bool")
        object.__setattr__(
            self,
            "latest_observed_at",
            _as_utc("latest_observed_at", self.latest_observed_at),
        )
        object.__setattr__(
            self,
            "oldest_observed_at",
            _as_utc("oldest_observed_at", self.oldest_observed_at),
        )
        object.__setattr__(
            self,
            "observation_references",
            _normalize_string_tuple("observation_references", self.observation_references),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes),
        )
        _validate_row_consistency(self)
        _require_hard_flags(self)
        _reject_unsafe_references(self.observation_references)
        _reject_unsafe_public_payload("row", self)


@dataclass(frozen=True)
class MarketLiquiditySourceReliabilityDigestReport:
    generated_at: datetime
    config_version: str
    observation_count: Decimal
    row_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    blocked_count: Decimal
    stale_source_family_count: Decimal
    depth_disagreement_count: Decimal
    spread_disagreement_count: Decimal
    missing_redundancy_count: Decimal
    max_source_age_seconds_observed: Decimal
    max_depth_disagreement_ratio_observed: Decimal
    max_spread_disagreement_ratio_observed: Decimal
    reason_codes: tuple[str, ...]
    rows: tuple[MarketLiquiditySourceReliabilityDigestRow, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True
    derived_validation_digest: str = ""

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "MarketLiquiditySourceReliabilityDigestReport does not support subclassing",
        )

    def __post_init__(self) -> None:
        _require_exact_type(self, MarketLiquiditySourceReliabilityDigestReport, "report")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        for field_name in (
            "observation_count",
            "row_count",
            "pass_count",
            "watch_count",
            "blocked_count",
            "stale_source_family_count",
            "depth_disagreement_count",
            "spread_disagreement_count",
            "missing_redundancy_count",
            "max_source_age_seconds_observed",
            "max_depth_disagreement_ratio_observed",
            "max_spread_disagreement_ratio_observed",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes),
        )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        _validate_report_consistency(self)
        _require_hard_flags(self)
        _reject_unsafe_public_payload("report", self)
        if self.derived_validation_digest == "":
            object.__setattr__(
                self,
                DERIVED_VALIDATION_DIGEST_FIELD,
                _report_derived_validation_digest(self),
            )
        else:
            object.__setattr__(
                self,
                DERIVED_VALIDATION_DIGEST_FIELD,
                _normalize_sha256(
                    DERIVED_VALIDATION_DIGEST_FIELD,
                    self.derived_validation_digest,
                ),
            )
        _validate_report_derived_validation_digest(self)


def build_market_liquidity_source_reliability_digest(
    observations: Iterable[MarketLiquiditySourceReliabilityDigestObservation],
    *,
    config: MarketLiquiditySourceReliabilityDigestConfig,
    generated_at: datetime,
) -> MarketLiquiditySourceReliabilityDigestReport:
    if type(config) is not MarketLiquiditySourceReliabilityDigestConfig:
        raise ValueError(
            "config must be a MarketLiquiditySourceReliabilityDigestConfig",
        )
    generated_at = _as_utc("generated_at", generated_at)
    _require_hard_flags(config)
    normalized_observations = _normalize_observations(observations)
    grouped = _group_observations(normalized_observations)
    rows = tuple(
        sorted(
            (
                _row_from_observations(
                    market_slug=market_slug,
                    outcome_name=outcome_name,
                    observations=group_rows,
                    config=config,
                    generated_at=generated_at,
                )
                for (market_slug, outcome_name), group_rows in grouped.items()
            ),
            key=_row_sort_key,
        ),
    )
    return MarketLiquiditySourceReliabilityDigestReport(
        generated_at=generated_at,
        config_version=config.config_version,
        observation_count=_count_decimal(len(normalized_observations)),
        row_count=_count_decimal(len(rows)),
        pass_count=_status_count(rows, "pass"),
        watch_count=_status_count(rows, "watch"),
        blocked_count=_status_count(rows, "blocked"),
        stale_source_family_count=_count_decimal(
            sum(1 for row in rows if row.stale_source_family_count > ZERO),
        ),
        depth_disagreement_count=_count_decimal(
            sum(1 for row in rows if "depth_disagreement" in row.reason_codes),
        ),
        spread_disagreement_count=_count_decimal(
            sum(1 for row in rows if "spread_disagreement" in row.reason_codes),
        ),
        missing_redundancy_count=_count_decimal(
            sum(1 for row in rows if row.missing_redundancy),
        ),
        max_source_age_seconds_observed=_max_row_decimal(
            rows,
            "max_source_age_seconds",
        ),
        max_depth_disagreement_ratio_observed=_max_row_decimal(
            rows,
            "depth_disagreement_ratio",
        ),
        max_spread_disagreement_ratio_observed=_max_row_decimal(
            rows,
            "spread_disagreement_ratio",
        ),
        reason_codes=_report_reason_codes(rows),
        rows=rows,
    )


def market_liquidity_source_reliability_digest_payload(
    report: MarketLiquiditySourceReliabilityDigestReport | dict[str, Any],
) -> dict[str, Any]:
    if type(report) in (float, int):
        raise ValueError("payload must not contain public float or int values")
    if type(report) is MarketLiquiditySourceReliabilityDigestReport:
        _reject_unsafe_public_payload("report", report)
        _validate_report_derived_validation_digest(report)
        _validate_report_consistency(report)
        _require_hard_flags(report)
        payload = _report_public_payload_values(report)
        payload[DERIVED_VALIDATION_DIGEST_FIELD] = report.derived_validation_digest
        _reject_unsafe_public_payload("payload", payload)
        return payload
    if type(report) is dict:
        _reject_unsafe_public_payload("payload", report)
        _validate_public_payload(report)
        return dict(report)
    raise ValueError("report must be a MarketLiquiditySourceReliabilityDigestReport")


def _row_from_observations(
    *,
    market_slug: str,
    outcome_name: str,
    observations: tuple[MarketLiquiditySourceReliabilityDigestObservation, ...],
    config: MarketLiquiditySourceReliabilityDigestConfig,
    generated_at: datetime,
) -> MarketLiquiditySourceReliabilityDigestRow:
    sorted_observations = tuple(sorted(observations, key=_observation_sort_key))
    source_families = tuple(
        dict.fromkeys(observation.source_family for observation in sorted_observations),
    )
    source_family_count = _count_decimal(len(source_families))
    observation_count = _count_decimal(len(sorted_observations))
    source_family_ages = tuple(
        _source_family_age_seconds(source_family, sorted_observations, generated_at)
        for source_family in source_families
    )
    stale_source_family_count = _count_decimal(
        sum(1 for age in source_family_ages if age > config.max_source_age_seconds),
    )
    bid_depths = tuple(observation.bid_depth for observation in sorted_observations)
    ask_depths = tuple(observation.ask_depth for observation in sorted_observations)
    spreads = tuple(observation.spread for observation in sorted_observations)
    min_bid_depth = min(bid_depths)
    max_bid_depth = max(bid_depths)
    min_ask_depth = min(ask_depths)
    max_ask_depth = max(ask_depths)
    min_spread = min(spreads)
    max_spread = max(spreads)
    depth_disagreement_ratio = max(
        _range_ratio(min_bid_depth, max_bid_depth),
        _range_ratio(min_ask_depth, max_ask_depth),
    )
    spread_disagreement_ratio = _range_ratio(min_spread, max_spread)
    missing_redundancy = source_family_count < config.min_source_family_count

    reason_codes = _row_reason_codes(
        sorted_observations,
        stale_source_family_count=stale_source_family_count,
        depth_disagreement_ratio=depth_disagreement_ratio,
        spread_disagreement_ratio=spread_disagreement_ratio,
        missing_redundancy=missing_redundancy,
        config=config,
    )
    status = _row_status(reason_codes)
    observed_times = tuple(observation.observed_at for observation in sorted_observations)
    return MarketLiquiditySourceReliabilityDigestRow(
        market_slug=market_slug,
        outcome_name=outcome_name,
        reliability_status=status,
        source_family_count=source_family_count,
        observation_count=observation_count,
        stale_source_family_count=stale_source_family_count,
        max_source_age_seconds=max(source_family_ages),
        min_bid_depth=min_bid_depth,
        max_bid_depth=max_bid_depth,
        min_ask_depth=min_ask_depth,
        max_ask_depth=max_ask_depth,
        depth_disagreement_ratio=depth_disagreement_ratio,
        min_spread=min_spread,
        max_spread=max_spread,
        spread_disagreement_ratio=spread_disagreement_ratio,
        missing_redundancy=missing_redundancy,
        latest_observed_at=max(observed_times),
        oldest_observed_at=min(observed_times),
        observation_references=tuple(
            f"{observation.source_name}:{_redact_reference(observation.reference)}"
            for observation in sorted_observations
        ),
        reason_codes=reason_codes,
    )


def _row_reason_codes(
    observations: tuple[MarketLiquiditySourceReliabilityDigestObservation, ...],
    *,
    stale_source_family_count: Decimal,
    depth_disagreement_ratio: Decimal,
    spread_disagreement_ratio: Decimal,
    missing_redundancy: bool,
    config: MarketLiquiditySourceReliabilityDigestConfig,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    for observation in observations:
        reason_codes.extend(observation.reason_codes)

    if stale_source_family_count > ZERO:
        reason_codes.append("source_family_stale")
    else:
        reason_codes.append("source_timeliness_pass")

    if depth_disagreement_ratio > config.max_depth_disagreement_ratio:
        reason_codes.append("depth_disagreement")
    else:
        reason_codes.append("depth_agreement_pass")

    if spread_disagreement_ratio > config.max_spread_disagreement_ratio:
        reason_codes.append("spread_disagreement")
    else:
        reason_codes.append("spread_agreement_pass")

    if missing_redundancy:
        reason_codes.append("missing_source_redundancy")
    else:
        reason_codes.append("source_redundancy_pass")

    return _normalize_reason_codes(tuple(reason_codes))


def _row_status(reason_codes: tuple[str, ...]) -> str:
    if any(reason_code in reason_codes for reason_code in BLOCKING_REASON_CODES):
        return "blocked"
    if any(
        not (reason_code.endswith("_pass") or reason_code.endswith("_ok"))
        for reason_code in reason_codes
    ):
        return "watch"
    return "pass"


def _source_family_age_seconds(
    source_family: str,
    observations: tuple[MarketLiquiditySourceReliabilityDigestObservation, ...],
    generated_at: datetime,
) -> Decimal:
    oldest = min(
        observation.observed_at
        for observation in observations
        if observation.source_family == source_family
    )
    return _seconds_between(generated_at, oldest)


def _seconds_between(later: datetime, earlier: datetime) -> Decimal:
    delta = later - earlier
    if delta.total_seconds() < 0:
        raise ValueError("observed_at must not be after generated_at")
    return _quantize_decimal(Decimal(delta.days * 86400 + delta.seconds))


def _group_observations(
    observations: tuple[MarketLiquiditySourceReliabilityDigestObservation, ...],
) -> dict[
    tuple[str, str],
    tuple[MarketLiquiditySourceReliabilityDigestObservation, ...],
]:
    groups: dict[tuple[str, str], list[MarketLiquiditySourceReliabilityDigestObservation]] = {}
    for observation in observations:
        groups.setdefault((observation.market_slug, observation.outcome_name), []).append(
            observation,
        )
    return {key: tuple(value) for key, value in groups.items()}


def _normalize_observations(
    observations: Iterable[MarketLiquiditySourceReliabilityDigestObservation],
) -> tuple[MarketLiquiditySourceReliabilityDigestObservation, ...]:
    if isinstance(observations, (str, bytes)) or not isinstance(observations, Iterable):
        raise ValueError("observations must be an iterable")
    normalized = tuple(observations)
    for observation in normalized:
        if type(observation) is not MarketLiquiditySourceReliabilityDigestObservation:
            raise ValueError(
                "observations must contain MarketLiquiditySourceReliabilityDigestObservation",
            )
        _require_hard_flags(observation)
    return normalized


def _normalize_rows(
    rows: Iterable[MarketLiquiditySourceReliabilityDigestRow],
) -> tuple[MarketLiquiditySourceReliabilityDigestRow, ...]:
    if isinstance(rows, (str, bytes)) or not isinstance(rows, Iterable):
        raise ValueError("rows must be an iterable")
    normalized = tuple(rows)
    for row in normalized:
        if type(row) is not MarketLiquiditySourceReliabilityDigestRow:
            raise ValueError("rows must contain MarketLiquiditySourceReliabilityDigestRow")
        _require_hard_flags(row)
    return tuple(sorted(normalized, key=_row_sort_key))


def _validate_row_consistency(row: MarketLiquiditySourceReliabilityDigestRow) -> None:
    if row.source_family_count == ZERO:
        raise ValueError("source_family_count must be positive")
    if row.observation_count == ZERO:
        raise ValueError("observation_count must be positive")
    if row.source_family_count > row.observation_count:
        raise ValueError("source_family_count cannot exceed observation_count")
    if row.stale_source_family_count > row.source_family_count:
        raise ValueError("stale_source_family_count cannot exceed source_family_count")
    if row.max_bid_depth < row.min_bid_depth:
        raise ValueError("max_bid_depth must be at least min_bid_depth")
    if row.max_ask_depth < row.min_ask_depth:
        raise ValueError("max_ask_depth must be at least min_ask_depth")
    if row.max_spread < row.min_spread:
        raise ValueError("max_spread must be at least min_spread")
    if row.latest_observed_at < row.oldest_observed_at:
        raise ValueError("latest_observed_at must be at least oldest_observed_at")
    expected_missing_redundancy = (
        "missing_source_redundancy" in row.reason_codes
    )
    if row.missing_redundancy is not expected_missing_redundancy:
        raise ValueError("missing_redundancy must match reason_codes")
    expected_status = _row_status(row.reason_codes)
    if row.reliability_status != expected_status:
        raise ValueError("reliability_status must match reason_codes")


def _validate_report_consistency(report: MarketLiquiditySourceReliabilityDigestReport) -> None:
    if report.row_count != _count_decimal(len(report.rows)):
        raise ValueError("row_count must match rows")
    if report.pass_count + report.watch_count + report.blocked_count != report.row_count:
        raise ValueError("status counts must match row_count")
    if report.observation_count != sum(
        (row.observation_count for row in report.rows),
        ZERO,
    ):
        raise ValueError("observation_count must match rows")
    if report.stale_source_family_count != _count_decimal(
        sum(1 for row in report.rows if row.stale_source_family_count > ZERO),
    ):
        raise ValueError("stale_source_family_count must match rows")
    if report.depth_disagreement_count != _count_decimal(
        sum(1 for row in report.rows if "depth_disagreement" in row.reason_codes),
    ):
        raise ValueError("depth_disagreement_count must match rows")
    if report.spread_disagreement_count != _count_decimal(
        sum(1 for row in report.rows if "spread_disagreement" in row.reason_codes),
    ):
        raise ValueError("spread_disagreement_count must match rows")
    if report.missing_redundancy_count != _count_decimal(
        sum(1 for row in report.rows if row.missing_redundancy),
    ):
        raise ValueError("missing_redundancy_count must match rows")
    if report.max_source_age_seconds_observed != _max_row_decimal(
        report.rows,
        "max_source_age_seconds",
    ):
        raise ValueError("max_source_age_seconds_observed must match rows")
    if report.max_depth_disagreement_ratio_observed != _max_row_decimal(
        report.rows,
        "depth_disagreement_ratio",
    ):
        raise ValueError("max_depth_disagreement_ratio_observed must match rows")
    if report.max_spread_disagreement_ratio_observed != _max_row_decimal(
        report.rows,
        "spread_disagreement_ratio",
    ):
        raise ValueError("max_spread_disagreement_ratio_observed must match rows")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")


def _report_reason_codes(
    rows: tuple[MarketLiquiditySourceReliabilityDigestRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return ("no_liquidity_observations",)
    reason_codes: list[str] = []
    for row in rows:
        reason_codes.extend(row.reason_codes)
    return _normalize_reason_codes(tuple(reason_codes))


def _status_count(
    rows: tuple[MarketLiquiditySourceReliabilityDigestRow, ...],
    status: str,
) -> Decimal:
    return _count_decimal(sum(1 for row in rows if row.reliability_status == status))


def _max_row_decimal(
    rows: tuple[MarketLiquiditySourceReliabilityDigestRow, ...],
    field_name: str,
) -> Decimal:
    if not rows:
        return _quantize_decimal(ZERO)
    return max(getattr(row, field_name) for row in rows)


def _range_ratio(low: Decimal, high: Decimal) -> Decimal:
    if high == ZERO:
        return _quantize_decimal(ZERO)
    return _quantize_decimal((high - low) / ((high + low) / Decimal("2")))


def _count_decimal(value: int) -> Decimal:
    return _quantize_decimal(Decimal(value))


def _normalize_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _normalize_positive_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _normalize_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return _quantize_decimal(value)


def _quantize_decimal(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(QUANTUM)


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be UTC-aware")
    return value.astimezone(UTC)


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")


def _require_reliability_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in RELIABILITY_STATUSES:
        raise ValueError(f"{field_name} must be pass, watch, or blocked")


def _normalize_reason_codes(reason_codes: Iterable[str]) -> tuple[str, ...]:
    if isinstance(reason_codes, (str, bytes)) or not isinstance(reason_codes, Iterable):
        raise ValueError("reason_codes must be an iterable")
    normalized: list[str] = []
    for reason_code in reason_codes:
        _require_canonical_string("reason_code", reason_code)
        if reason_code not in normalized:
            normalized.append(reason_code)
    return tuple(sorted(normalized))


def _normalize_string_tuple(field_name: str, values: Iterable[str]) -> tuple[str, ...]:
    if isinstance(values, (str, bytes)) or not isinstance(values, Iterable):
        raise ValueError(f"{field_name} must be an iterable")
    normalized = tuple(values)
    for value in normalized:
        _require_canonical_string(field_name, value)
    return tuple(sorted(dict.fromkeys(normalized)))


def _require_hard_flags(value: object) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if getattr(value, field_name, None) is not True:
            raise ValueError(f"{field_name} must be True")


def _require_exact_type(value: object, type_: type[object], label: str) -> None:
    if type(value) is not type_:
        raise ValueError(f"{label} must be exactly {type_.__name__}")


def _observation_sort_key(
    observation: MarketLiquiditySourceReliabilityDigestObservation,
) -> tuple[str, str, str, str, datetime]:
    return (
        observation.market_slug,
        observation.outcome_name,
        observation.source_family,
        observation.source_name,
        observation.observed_at,
    )


def _row_sort_key(
    row: MarketLiquiditySourceReliabilityDigestRow,
) -> tuple[int, str, str]:
    return (
        STATUS_RANK[row.reliability_status],
        row.market_slug,
        row.outcome_name,
    )


def _redact_reference(reference: str) -> str:
    lower = reference.lower()
    if "?" in reference and any(marker in lower for marker in SENSITIVE_REFERENCE_MARKERS):
        return reference.split("?", 1)[0] + "?<redacted>"
    if any(marker in lower for marker in SENSITIVE_REFERENCE_MARKERS):
        return "<redacted>"
    return reference


def _reject_unsafe_references(references: tuple[str, ...]) -> None:
    for reference in references:
        if any(marker in reference.lower() for marker in SENSITIVE_REFERENCE_MARKERS):
            raise ValueError("observation_references must not contain secrets")


def _report_public_payload_values(
    report: MarketLiquiditySourceReliabilityDigestReport,
) -> dict[str, Any]:
    return {
        field_name: _payload_value(getattr(report, field_name))
        for field_name in REPORT_PAYLOAD_FIELDS_WITHOUT_DIGEST
    }


def _validate_public_payload(payload: dict[str, Any]) -> None:
    _require_public_payload_fields(payload)
    report = _report_from_public_payload(payload)
    _validate_report_consistency(report)
    _validate_report_derived_validation_digest(report)


def _require_public_payload_fields(payload: dict[str, Any]) -> None:
    actual_fields = tuple(payload)
    missing_fields = tuple(
        field_name for field_name in REPORT_PAYLOAD_FIELDS if field_name not in payload
    )
    if missing_fields:
        raise ValueError("derived_validation_digest missing from public payload")
    if actual_fields != REPORT_PAYLOAD_FIELDS:
        raise ValueError("public payload fields must match report schema")


def _report_from_public_payload(
    payload: dict[str, Any],
) -> MarketLiquiditySourceReliabilityDigestReport:
    rows_value = payload["rows"]
    if type(rows_value) is not list:
        raise ValueError("rows must be a public payload list")
    return MarketLiquiditySourceReliabilityDigestReport(
        generated_at=_datetime_from_public_payload("generated_at", payload["generated_at"]),
        config_version=_string_from_public_payload(
            "config_version",
            payload["config_version"],
        ),
        observation_count=_decimal_from_public_payload(
            "observation_count",
            payload["observation_count"],
        ),
        row_count=_decimal_from_public_payload("row_count", payload["row_count"]),
        pass_count=_decimal_from_public_payload("pass_count", payload["pass_count"]),
        watch_count=_decimal_from_public_payload("watch_count", payload["watch_count"]),
        blocked_count=_decimal_from_public_payload(
            "blocked_count",
            payload["blocked_count"],
        ),
        stale_source_family_count=_decimal_from_public_payload(
            "stale_source_family_count",
            payload["stale_source_family_count"],
        ),
        depth_disagreement_count=_decimal_from_public_payload(
            "depth_disagreement_count",
            payload["depth_disagreement_count"],
        ),
        spread_disagreement_count=_decimal_from_public_payload(
            "spread_disagreement_count",
            payload["spread_disagreement_count"],
        ),
        missing_redundancy_count=_decimal_from_public_payload(
            "missing_redundancy_count",
            payload["missing_redundancy_count"],
        ),
        max_source_age_seconds_observed=_decimal_from_public_payload(
            "max_source_age_seconds_observed",
            payload["max_source_age_seconds_observed"],
        ),
        max_depth_disagreement_ratio_observed=_decimal_from_public_payload(
            "max_depth_disagreement_ratio_observed",
            payload["max_depth_disagreement_ratio_observed"],
        ),
        max_spread_disagreement_ratio_observed=_decimal_from_public_payload(
            "max_spread_disagreement_ratio_observed",
            payload["max_spread_disagreement_ratio_observed"],
        ),
        reason_codes=_string_tuple_from_public_payload(
            "reason_codes",
            payload["reason_codes"],
        ),
        rows=tuple(_row_from_public_payload(row) for row in rows_value),
        paper_only=_bool_from_public_payload("paper_only", payload["paper_only"]),
        report_only=_bool_from_public_payload("report_only", payload["report_only"]),
        readonly=_bool_from_public_payload("readonly", payload["readonly"]),
        derived_validation_digest=_string_from_public_payload(
            DERIVED_VALIDATION_DIGEST_FIELD,
            payload[DERIVED_VALIDATION_DIGEST_FIELD],
        ),
    )


def _row_from_public_payload(payload: object) -> MarketLiquiditySourceReliabilityDigestRow:
    if type(payload) is not dict:
        raise ValueError("rows must contain public payload objects")
    _require_row_payload_fields(payload)
    return MarketLiquiditySourceReliabilityDigestRow(
        market_slug=_string_from_public_payload("market_slug", payload["market_slug"]),
        outcome_name=_string_from_public_payload("outcome_name", payload["outcome_name"]),
        reliability_status=_string_from_public_payload(
            "reliability_status",
            payload["reliability_status"],
        ),
        source_family_count=_decimal_from_public_payload(
            "source_family_count",
            payload["source_family_count"],
        ),
        observation_count=_decimal_from_public_payload(
            "observation_count",
            payload["observation_count"],
        ),
        stale_source_family_count=_decimal_from_public_payload(
            "stale_source_family_count",
            payload["stale_source_family_count"],
        ),
        max_source_age_seconds=_decimal_from_public_payload(
            "max_source_age_seconds",
            payload["max_source_age_seconds"],
        ),
        min_bid_depth=_decimal_from_public_payload(
            "min_bid_depth",
            payload["min_bid_depth"],
        ),
        max_bid_depth=_decimal_from_public_payload(
            "max_bid_depth",
            payload["max_bid_depth"],
        ),
        min_ask_depth=_decimal_from_public_payload(
            "min_ask_depth",
            payload["min_ask_depth"],
        ),
        max_ask_depth=_decimal_from_public_payload(
            "max_ask_depth",
            payload["max_ask_depth"],
        ),
        depth_disagreement_ratio=_decimal_from_public_payload(
            "depth_disagreement_ratio",
            payload["depth_disagreement_ratio"],
        ),
        min_spread=_decimal_from_public_payload("min_spread", payload["min_spread"]),
        max_spread=_decimal_from_public_payload("max_spread", payload["max_spread"]),
        spread_disagreement_ratio=_decimal_from_public_payload(
            "spread_disagreement_ratio",
            payload["spread_disagreement_ratio"],
        ),
        missing_redundancy=_bool_from_public_payload(
            "missing_redundancy",
            payload["missing_redundancy"],
        ),
        latest_observed_at=_datetime_from_public_payload(
            "latest_observed_at",
            payload["latest_observed_at"],
        ),
        oldest_observed_at=_datetime_from_public_payload(
            "oldest_observed_at",
            payload["oldest_observed_at"],
        ),
        observation_references=_string_tuple_from_public_payload(
            "observation_references",
            payload["observation_references"],
        ),
        reason_codes=_string_tuple_from_public_payload(
            "reason_codes",
            payload["reason_codes"],
        ),
        paper_only=_bool_from_public_payload("paper_only", payload["paper_only"]),
        report_only=_bool_from_public_payload("report_only", payload["report_only"]),
        readonly=_bool_from_public_payload("readonly", payload["readonly"]),
    )


def _require_row_payload_fields(payload: dict[str, Any]) -> None:
    if tuple(payload) != ROW_PAYLOAD_FIELDS:
        raise ValueError("row public payload fields must match row schema")


def _decimal_from_public_payload(field_name: str, value: object) -> Decimal:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a Decimal string")
    decimal_value = _normalize_decimal(field_name, Decimal(value))
    if value != f"{decimal_value:.6f}":
        raise ValueError(f"{field_name} must be a canonical Decimal string")
    return decimal_value


def _datetime_from_public_payload(field_name: str, value: object) -> datetime:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a datetime string")
    return _as_utc(field_name, datetime.fromisoformat(value))


def _string_from_public_payload(field_name: str, value: object) -> str:
    _require_canonical_string(field_name, value)
    return value


def _string_tuple_from_public_payload(field_name: str, value: object) -> tuple[str, ...]:
    if type(value) is not list:
        raise ValueError(f"{field_name} must be a public payload list")
    return _normalize_string_tuple(field_name, value)


def _bool_from_public_payload(field_name: str, value: object) -> bool:
    if type(value) is not bool:
        raise ValueError(f"{field_name} must be a bool")
    return value


def _report_derived_validation_digest(
    report: MarketLiquiditySourceReliabilityDigestReport,
) -> str:
    canonical_payload = _canonical_digest_value(_report_public_payload_values(report))
    return hashlib.sha256(canonical_payload.encode("utf-8")).hexdigest()


def _validate_report_derived_validation_digest(
    report: MarketLiquiditySourceReliabilityDigestReport,
) -> None:
    if report.derived_validation_digest != _report_derived_validation_digest(report):
        raise ValueError("derived_validation_digest must match report payload")


def _normalize_sha256(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if len(value) != 64 or any(character not in "0123456789abcdef" for character in value):
        raise ValueError(f"{field_name} must be a lowercase sha256 hex digest")
    return value


def _canonical_digest_value(value: object) -> str:
    if type(value) is dict:
        return "".join(
            (
                "dict(",
                "".join(
                    f"{len(key)}:{key}={_canonical_digest_value(value[key])};"
                    for key in sorted(value)
                ),
                ")",
            ),
        )
    if type(value) is list:
        return "".join(
            (
                "list(",
                "".join(_canonical_digest_value(item) + ";" for item in value),
                ")",
            ),
        )
    if type(value) is str:
        return f"str:{len(value)}:{value}"
    if type(value) is bool:
        return f"bool:{value}"
    raise ValueError("public payload contains unsupported digest value")


def _reject_unsafe_public_payload(
    label: str,
    value: object,
    path: str = "",
) -> None:
    if is_dataclass(value) and not isinstance(value, type):
        field_names = {field.name for field in fields(value)}
        for key, item in vars(value).items():
            if key in field_names:
                continue
            item_path = f"{path}.{key}" if path else str(key)
            _reject_unsafe_text(label, str(key), item_path)
            _reject_unsafe_public_payload(label, item, item_path)
        _reject_unsafe_public_payload(label, _payload_value(value), path)
        return
    if type(value) is dict:
        for key, item in value.items():
            _reject_unsafe_text(label, str(key), f"{path}.{key}" if path else str(key))
            _reject_unsafe_public_payload(
                label,
                item,
                f"{path}.{key}" if path else str(key),
            )
        return
    if isinstance(value, (tuple, list)):
        for index, item in enumerate(value):
            _reject_unsafe_public_payload(label, item, f"{path}[{index}]")
        return
    if type(value) is str:
        _reject_unsafe_text(label, value, path)


def _reject_unsafe_text(label: str, value: str, path: str) -> None:
    lowered = value.lower()
    if any(term in lowered for term in UNSAFE_PUBLIC_TERMS):
        location = path or label
        raise ValueError(f"{label} contains unsafe public surface at {location}")


def _payload_value(value: object) -> Any:
    if type(value) is Decimal:
        return f"{value:.6f}"
    if type(value) is datetime:
        return value.isoformat()
    if is_dataclass(value) and not isinstance(value, type):
        return {
            field.name: _payload_value(getattr(value, field.name))
            for field in fields(value)
        }
    if isinstance(value, tuple):
        return [_payload_value(item) for item in value]
    if type(value) in (float, int):
        raise ValueError("payload must not contain public float or int values")
    return value
