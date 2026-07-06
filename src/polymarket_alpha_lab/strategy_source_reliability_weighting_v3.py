"""Pure typed source reliability weighting v3 reducer."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from typing import Any


__all__ = (
    "StrategySourceReliabilityWeightingV3Config",
    "StrategySourceReliabilityWeightingV3Report",
    "StrategySourceReliabilityWeightingV3Row",
    "StrategySourceReliabilityWeightingV3Source",
    "build_strategy_source_reliability_weighting_v3",
    "strategy_source_reliability_weighting_v3_payload",
)


DEFAULT_CONFIG_VERSION = "strategy-source-reliability-weighting-v3"
COUNT_QUANTUM = Decimal("1")
RATIO_QUANTUM = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)

SOURCE_TIERS = ("official", "primary", "secondary", "tertiary")
RELIABILITY_STATUSES = ("pass", "watch", "block")
REPORT_STATUSES = ("pass", "watch", "blocked")
EMPTY_REASON_CODE = "strategy_source_reliability_weighting_v3_empty"
PASS_REASON_CODE = "source_weight_pass"
WATCH_REASON_CODE = "source_weight_watch"
BLOCK_REASON_CODE = "source_weight_block"
OFFICIAL_OVERRIDE_REASON_CODE = "source_official_override"

STATUS_PRIORITY = {"pass": 0, "watch": 1, "block": 2}
REPORT_REASON_PRIORITY = (
    PASS_REASON_CODE,
    WATCH_REASON_CODE,
    BLOCK_REASON_CODE,
    OFFICIAL_OVERRIDE_REASON_CODE,
    "historical_accuracy_low",
    "source_stale",
    "directness_low",
    "source_conflict_rate_high",
)
TIER_WEIGHTS = {
    "official": Decimal("1.000000"),
    "primary": Decimal("0.850000"),
    "secondary": Decimal("0.650000"),
    "tertiary": Decimal("0.450000"),
}
TIER_PART = Decimal("0.250000")
ACCURACY_PART = Decimal("0.300000")
RECENCY_PART = Decimal("0.150000")
DIRECTNESS_PART = Decimal("0.200000")
CONFLICT_PART = Decimal("0.100000")
SENSITIVE_MARKERS = (
    "secret",
    "password",
    "passwd",
    "api_key",
    "apikey",
    "private_key",
    "access_key",
    "access_token",
    "bearer ",
    "://",
    "@",
)


@dataclass(frozen=True)
class StrategySourceReliabilityWeightingV3Config:
    config_version: str = DEFAULT_CONFIG_VERSION
    min_pass_source_weight: Decimal = Decimal("0.700000")
    min_watch_source_weight: Decimal = Decimal("0.450000")
    min_historical_accuracy: Decimal = Decimal("0.600000")
    min_directness: Decimal = Decimal("0.500000")
    max_source_age_seconds: Decimal = Decimal("86400.000000")
    max_conflict_rate: Decimal = Decimal("0.250000")
    official_override_floor: Decimal = Decimal("0.850000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("config_version", self.config_version)
        object.__setattr__(
            self,
            "min_pass_source_weight",
            _normalize_probability(
                "min_pass_source_weight",
                self.min_pass_source_weight,
            ),
        )
        object.__setattr__(
            self,
            "min_watch_source_weight",
            _normalize_probability(
                "min_watch_source_weight",
                self.min_watch_source_weight,
            ),
        )
        object.__setattr__(
            self,
            "min_historical_accuracy",
            _normalize_probability(
                "min_historical_accuracy",
                self.min_historical_accuracy,
            ),
        )
        object.__setattr__(
            self,
            "min_directness",
            _normalize_probability("min_directness", self.min_directness),
        )
        object.__setattr__(
            self,
            "max_source_age_seconds",
            _normalize_positive_decimal(
                "max_source_age_seconds",
                self.max_source_age_seconds,
            ),
        )
        object.__setattr__(
            self,
            "max_conflict_rate",
            _normalize_probability("max_conflict_rate", self.max_conflict_rate),
        )
        object.__setattr__(
            self,
            "official_override_floor",
            _normalize_probability(
                "official_override_floor",
                self.official_override_floor,
            ),
        )
        if self.min_pass_source_weight < self.min_watch_source_weight:
            raise ValueError("min_pass_source_weight must not be below watch")
        _require_safety_flags("config", self)


@dataclass(frozen=True)
class StrategySourceReliabilityWeightingV3Source:
    source_id: str
    source_tier: str
    observed_at: datetime
    historical_accuracy: Decimal
    source_age_seconds: Decimal
    directness: Decimal
    conflict_rate: Decimal
    official_override: bool = False
    reason_codes: tuple[str, ...] = ()
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("source_id", self.source_id)
        _require_member("source_tier", self.source_tier, SOURCE_TIERS)
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in (
            "historical_accuracy",
            "directness",
            "conflict_rate",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "source_age_seconds",
            _normalize_nonnegative_decimal(
                "source_age_seconds",
                self.source_age_seconds,
            ),
        )
        _require_bool("official_override", self.official_override)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes),
        )
        _require_safety_flags("source", self)


@dataclass(frozen=True)
class StrategySourceReliabilityWeightingV3Row:
    source_id: str
    source_tier: str
    observed_at: datetime
    historical_accuracy: Decimal
    source_age_seconds: Decimal
    directness: Decimal
    conflict_rate: Decimal
    official_override: bool
    tier_weight: Decimal
    recency_weight: Decimal
    source_weight: Decimal
    reliability_status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("source_id", self.source_id)
        _require_member("source_tier", self.source_tier, SOURCE_TIERS)
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in (
            "historical_accuracy",
            "directness",
            "conflict_rate",
            "tier_weight",
            "recency_weight",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "source_age_seconds",
            _normalize_nonnegative_decimal(
                "source_age_seconds",
                self.source_age_seconds,
            ),
        )
        _require_bool("official_override", self.official_override)
        object.__setattr__(
            self,
            "source_weight",
            _normalize_probability("source_weight", self.source_weight),
        )
        _require_member("reliability_status", self.reliability_status, RELIABILITY_STATUSES)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes, require_nonempty=True),
        )
        _require_safety_flags("row", self)


@dataclass(frozen=True)
class StrategySourceReliabilityWeightingV3Report:
    generated_at: datetime
    config_version: str
    source_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    average_source_weight: Decimal
    reliability_status: str
    reason_codes: tuple[str, ...]
    rows: tuple[StrategySourceReliabilityWeightingV3Row, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        for field_name in ("source_count", "pass_count", "watch_count", "block_count"):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_count(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "average_source_weight",
            _normalize_probability("average_source_weight", self.average_source_weight),
        )
        _require_member("reliability_status", self.reliability_status, REPORT_STATUSES)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes, require_nonempty=True),
        )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        _validate_report(self)
        _require_safety_flags("report", self)


def build_strategy_source_reliability_weighting_v3(
    sources: Iterable[object],
    *,
    config: StrategySourceReliabilityWeightingV3Config,
    generated_at: datetime,
) -> StrategySourceReliabilityWeightingV3Report:
    if type(config) is not StrategySourceReliabilityWeightingV3Config:
        raise ValueError("config must be a StrategySourceReliabilityWeightingV3Config")
    _require_safety_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    source_rows = _normalize_sources(sources)
    _reject_duplicate_sources(source_rows)
    rows = tuple(
        sorted(
            (_row_from_source(source, config=config) for source in source_rows),
            key=_row_sort_key,
        ),
    )
    return StrategySourceReliabilityWeightingV3Report(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        source_count=_count(len(rows)),
        pass_count=_status_count(rows, "pass"),
        watch_count=_status_count(rows, "watch"),
        block_count=_status_count(rows, "block"),
        average_source_weight=_average(tuple(row.source_weight for row in rows)),
        reliability_status=_report_status(rows),
        reason_codes=_report_reason_codes(rows),
        rows=rows,
    )


def strategy_source_reliability_weighting_v3_payload(
    report: StrategySourceReliabilityWeightingV3Report,
) -> dict[str, Any]:
    if type(report) is not StrategySourceReliabilityWeightingV3Report:
        raise ValueError("report must be a StrategySourceReliabilityWeightingV3Report")
    _require_safety_flags("report", report)
    return {
        "generated_at": report.generated_at.isoformat(),
        "config_version": report.config_version,
        "source_count": _count_payload(report.source_count),
        "pass_count": _count_payload(report.pass_count),
        "watch_count": _count_payload(report.watch_count),
        "block_count": _count_payload(report.block_count),
        "average_source_weight": _decimal_payload(report.average_source_weight),
        "reliability_status": report.reliability_status,
        "reason_codes": list(report.reason_codes),
        "rows": [_row_payload(row) for row in report.rows],
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }


def _row_payload(row: StrategySourceReliabilityWeightingV3Row) -> dict[str, Any]:
    _require_safety_flags("row", row)
    return {
        "source_id": row.source_id,
        "source_tier": row.source_tier,
        "observed_at": row.observed_at.isoformat(),
        "historical_accuracy": _decimal_payload(row.historical_accuracy),
        "source_age_seconds": _decimal_payload(row.source_age_seconds),
        "directness": _decimal_payload(row.directness),
        "conflict_rate": _decimal_payload(row.conflict_rate),
        "official_override": row.official_override,
        "tier_weight": _decimal_payload(row.tier_weight),
        "recency_weight": _decimal_payload(row.recency_weight),
        "source_weight": _decimal_payload(row.source_weight),
        "reliability_status": row.reliability_status,
        "reason_codes": list(row.reason_codes),
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }


def _row_from_source(
    source: StrategySourceReliabilityWeightingV3Source,
    *,
    config: StrategySourceReliabilityWeightingV3Config,
) -> StrategySourceReliabilityWeightingV3Row:
    tier_weight = TIER_WEIGHTS[source.source_tier]
    recency_weight = _recency_weight(source.source_age_seconds, config)
    source_weight = _source_weight(
        source=source,
        tier_weight=tier_weight,
        recency_weight=recency_weight,
        config=config,
    )
    reliability_status = _source_status(source_weight, config)
    return StrategySourceReliabilityWeightingV3Row(
        source_id=source.source_id,
        source_tier=source.source_tier,
        observed_at=source.observed_at,
        historical_accuracy=source.historical_accuracy,
        source_age_seconds=source.source_age_seconds,
        directness=source.directness,
        conflict_rate=source.conflict_rate,
        official_override=source.official_override,
        tier_weight=tier_weight,
        recency_weight=recency_weight,
        source_weight=source_weight,
        reliability_status=reliability_status,
        reason_codes=_row_reason_codes(
            source=source,
            recency_weight=recency_weight,
            reliability_status=reliability_status,
            config=config,
        ),
    )


def _source_weight(
    *,
    source: StrategySourceReliabilityWeightingV3Source,
    tier_weight: Decimal,
    recency_weight: Decimal,
    config: StrategySourceReliabilityWeightingV3Config,
) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        conflict_weight = ONE - source.conflict_rate
        raw_weight = (
            tier_weight * TIER_PART
            + source.historical_accuracy * ACCURACY_PART
            + recency_weight * RECENCY_PART
            + source.directness * DIRECTNESS_PART
            + conflict_weight * CONFLICT_PART
        )
        if source.official_override and raw_weight < config.official_override_floor:
            raw_weight = config.official_override_floor
        return _quantize_probability("source_weight", raw_weight)


def _recency_weight(
    source_age_seconds: Decimal,
    config: StrategySourceReliabilityWeightingV3Config,
) -> Decimal:
    if source_age_seconds >= config.max_source_age_seconds:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return _quantize_probability(
            "recency_weight",
            ONE - (source_age_seconds / config.max_source_age_seconds),
        )


def _source_status(
    source_weight: Decimal,
    config: StrategySourceReliabilityWeightingV3Config,
) -> str:
    if source_weight >= config.min_pass_source_weight:
        return "pass"
    if source_weight >= config.min_watch_source_weight:
        return "watch"
    return "block"


def _row_reason_codes(
    *,
    source: StrategySourceReliabilityWeightingV3Source,
    recency_weight: Decimal,
    reliability_status: str,
    config: StrategySourceReliabilityWeightingV3Config,
) -> tuple[str, ...]:
    reason_codes = list(source.reason_codes)
    reason_codes.append(_status_reason_code(reliability_status))
    if source.official_override:
        reason_codes.append(OFFICIAL_OVERRIDE_REASON_CODE)
    reason_codes.append(f"source_tier_{source.source_tier}")
    if source.historical_accuracy >= Decimal("0.800000"):
        reason_codes.append("historical_accuracy_strong")
    elif source.historical_accuracy < config.min_historical_accuracy:
        reason_codes.append("historical_accuracy_low")
    if recency_weight == ZERO:
        reason_codes.append("source_stale")
    elif recency_weight >= Decimal("0.750000"):
        reason_codes.append("source_recent")
    else:
        reason_codes.append("source_recency_decay")
    if source.directness > config.min_directness:
        reason_codes.append("direct_source")
    elif source.directness < config.min_directness:
        reason_codes.append("directness_low")
    if source.conflict_rate > config.max_conflict_rate:
        reason_codes.append("source_conflict_rate_high")
    else:
        reason_codes.append("source_conflict_rate_contained")
    return _normalize_reason_codes(tuple(reason_codes), require_nonempty=True)


def _status_reason_code(reliability_status: str) -> str:
    if reliability_status == "pass":
        return PASS_REASON_CODE
    if reliability_status == "watch":
        return WATCH_REASON_CODE
    return BLOCK_REASON_CODE


def _report_status(rows: tuple[StrategySourceReliabilityWeightingV3Row, ...]) -> str:
    if not rows:
        return "watch"
    if any(row.reliability_status == "block" for row in rows):
        return "blocked"
    if any(row.reliability_status == "watch" for row in rows):
        return "watch"
    return "pass"


def _report_reason_codes(
    rows: tuple[StrategySourceReliabilityWeightingV3Row, ...],
) -> tuple[str, ...]:
    if not rows:
        return (EMPTY_REASON_CODE,)
    present = {reason_code for row in rows for reason_code in row.reason_codes}
    return tuple(
        reason_code
        for reason_code in REPORT_REASON_PRIORITY
        if reason_code in present
    )


def _normalize_sources(
    value: Iterable[object],
) -> tuple[StrategySourceReliabilityWeightingV3Source, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError("sources must be an iterable")
    try:
        rows = tuple(value)
    except TypeError as exc:
        raise ValueError("sources must be an iterable") from exc
    for row in rows:
        if type(row) is not StrategySourceReliabilityWeightingV3Source:
            raise ValueError(
                "sources must contain StrategySourceReliabilityWeightingV3Source values",
            )
        _require_safety_flags("source", row)
    return rows


def _normalize_rows(
    value: object,
) -> tuple[StrategySourceReliabilityWeightingV3Row, ...]:
    if type(value) is not tuple:
        raise ValueError("rows must be a tuple")
    for row in value:
        if type(row) is not StrategySourceReliabilityWeightingV3Row:
            raise ValueError(
                "rows must contain StrategySourceReliabilityWeightingV3Row values",
            )
        _require_safety_flags("row", row)
    return value


def _reject_duplicate_sources(
    sources: tuple[StrategySourceReliabilityWeightingV3Source, ...],
) -> None:
    seen: set[str] = set()
    for source in sources:
        if source.source_id in seen:
            raise ValueError("duplicate source_id")
        seen.add(source.source_id)


def _validate_report(report: StrategySourceReliabilityWeightingV3Report) -> None:
    if report.source_count != _count(len(report.rows)):
        raise ValueError("source_count must match rows")
    if report.pass_count != _status_count(report.rows, "pass"):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _status_count(report.rows, "watch"):
        raise ValueError("watch_count must match rows")
    if report.block_count != _status_count(report.rows, "block"):
        raise ValueError("block_count must match rows")
    if report.average_source_weight != _average(
        tuple(row.source_weight for row in report.rows),
    ):
        raise ValueError("average_source_weight must match rows")
    if report.reliability_status != _report_status(report.rows):
        raise ValueError("reliability_status must match rows")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")


def _row_sort_key(row: StrategySourceReliabilityWeightingV3Row) -> tuple[int, Decimal, str]:
    return (STATUS_PRIORITY[row.reliability_status], -row.source_weight, row.source_id)


def _status_count(
    rows: tuple[StrategySourceReliabilityWeightingV3Row, ...],
    reliability_status: str,
) -> Decimal:
    return _count(sum(1 for row in rows if row.reliability_status == reliability_status))


def _average(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return _quantize_probability("average", sum(values, ZERO) / _count(len(values)))


def _count(value: int) -> Decimal:
    return Decimal(value).quantize(COUNT_QUANTUM)


def _normalize_probability(field_name: str, value: object) -> Decimal:
    decimal_value = _normalize_decimal(field_name, value, RATIO_QUANTUM)
    if decimal_value < ZERO or decimal_value > ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return decimal_value


def _quantize_probability(field_name: str, value: object) -> Decimal:
    decimal_value = _quantize_decimal(field_name, value, RATIO_QUANTUM)
    if decimal_value < ZERO or decimal_value > ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return decimal_value


def _normalize_positive_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _normalize_decimal(field_name, value, RATIO_QUANTUM)
    if decimal_value <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return decimal_value


def _normalize_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _normalize_decimal(field_name, value, RATIO_QUANTUM)
    if decimal_value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return decimal_value


def _normalize_nonnegative_count(field_name: str, value: object) -> Decimal:
    decimal_value = _normalize_decimal(field_name, value, COUNT_QUANTUM)
    if decimal_value < Decimal("0"):
        raise ValueError(f"{field_name} must be nonnegative")
    return decimal_value


def _normalize_decimal(field_name: str, value: object, quantum: Decimal) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    decimal_value = value.quantize(quantum)
    if decimal_value != value:
        raise ValueError(f"{field_name} must use the required decimal precision")
    return decimal_value


def _quantize_decimal(field_name: str, value: object, quantum: Decimal) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return value.quantize(quantum)


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be exactly datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_member(
    field_name: str,
    value: object,
    allowed_values: tuple[str, ...],
) -> None:
    if type(value) is not str or value not in allowed_values:
        raise ValueError(f"{field_name} must be a known value")


def _require_bool(field_name: str, value: object) -> None:
    if type(value) is not bool:
        raise ValueError(f"{field_name} must be a bool")


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a canonical nonblank string")
    if not value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")
    if value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")
    if "\n" in value or "\r" in value or "\t" in value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")
    _reject_unsafe_text(value)


def _normalize_reason_codes(
    value: object,
    *,
    require_nonempty: bool = False,
) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ValueError("reason_codes must be a tuple")
    if require_nonempty and not value:
        raise ValueError("reason_codes must not be empty")
    seen: set[str] = set()
    normalized: list[str] = []
    for reason_code in value:
        _require_canonical_string("reason_codes", reason_code)
        if reason_code in seen:
            raise ValueError("reason_codes must be unique")
        seen.add(reason_code)
        normalized.append(reason_code)
    return tuple(normalized)


def _require_safety_flags(label: str, value: object) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if not hasattr(value, field_name):
            raise ValueError(f"{label} must expose {field_name}")
        if getattr(value, field_name) is not True:
            raise ValueError(f"{field_name} must be True")


def _reject_unsafe_text(value: str) -> None:
    lowered = value.lower()
    if any(marker in lowered for marker in SENSITIVE_MARKERS):
        raise ValueError("must not contain sensitive material")


def _decimal_payload(value: Decimal) -> str:
    if type(value) is not Decimal:
        raise ValueError("payload decimal must be a Decimal")
    return format(value, "f")


def _count_payload(value: Decimal) -> str:
    decimal_value = _normalize_nonnegative_count("payload count", value)
    return format(decimal_value, "f")
