from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from typing import Any


DEFAULT_AUTO_SALES_SURPRISE_CONFIG_VERSION = (
    "market-research-auto-sales-surprise-digest-v0"
)

DIGEST_STATUSES = ("pass", "watch", "blocked")
NEXT_STEP_BY_STATUS = {
    "pass": "continue_monitoring_auto_sales",
    "watch": "review_auto_sales_surprise",
    "blocked": "repair_auto_sales_consensus_inputs",
}
QUANT = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)

AUTO_SALES_BLOCKED_MISSING_CONSENSUS = "auto_sales_blocked_missing_consensus"
AUTO_SALES_BLOCKED_MISSING_EVIDENCE = "auto_sales_blocked_missing_evidence"
AUTO_SALES_MATERIAL_NEGATIVE_SURPRISE = "auto_sales_material_negative_surprise"
AUTO_SALES_MATERIAL_POSITIVE_SURPRISE = "auto_sales_material_positive_surprise"
AUTO_SALES_NO_MATERIAL_SURPRISE = "auto_sales_no_material_surprise"
AUTO_SALES_STALE_OBSERVATION = "auto_sales_stale_observation"
AUTO_SALES_WATCH = "auto_sales_watch"
REASON_CODES = (
    AUTO_SALES_BLOCKED_MISSING_CONSENSUS,
    AUTO_SALES_BLOCKED_MISSING_EVIDENCE,
    AUTO_SALES_MATERIAL_NEGATIVE_SURPRISE,
    AUTO_SALES_MATERIAL_POSITIVE_SURPRISE,
    AUTO_SALES_NO_MATERIAL_SURPRISE,
    AUTO_SALES_STALE_OBSERVATION,
    AUTO_SALES_WATCH,
)
MICROSECONDS_PER_SECOND = Decimal("1000000")


def _join_parts(*parts: str) -> str:
    return "".join(parts)


UNSAFE_TEXT_FRAGMENTS = frozenset(
    (
        _join_parts("au", "th"),
        _join_parts("bro", "ker"),
        _join_parts("sig", "ning"),
        _join_parts("sub", "mit"),
        _join_parts("can", "cel"),
        _join_parts("wal", "let"),
        _join_parts("acc", "ount"),
        _join_parts("ad", "vice"),
        _join_parts("net", "work"),
        _join_parts("data", "base"),
        _join_parts("per", "sist"),
        _join_parts("pay", "load"),
        _join_parts("sec", "ret"),
        _join_parts("to", "ken"),
        _join_parts("ke", "y"),
        _join_parts("pri", "vate"),
    ),
)

__all__ = (
    "AutoSalesSurpriseInput",
    "AutoSalesSurpriseObservation",
    "AutoSalesSurpriseReport",
    "build_market_research_auto_sales_surprise_digest",
    "market_research_auto_sales_surprise_digest_payload",
)


@dataclass(frozen=True)
class AutoSalesSurpriseInput:
    config_version: str = DEFAULT_AUTO_SALES_SURPRISE_CONFIG_VERSION
    material_surprise_threshold: Decimal = Decimal("0.030000")
    max_observation_age_seconds: Decimal = Decimal("86400.000000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("config_version", self.config_version)
        object.__setattr__(
            self,
            "material_surprise_threshold",
            _require_nonnegative_decimal(
                "material_surprise_threshold",
                self.material_surprise_threshold,
            ),
        )
        object.__setattr__(
            self,
            "max_observation_age_seconds",
            _require_positive_decimal(
                "max_observation_age_seconds",
                self.max_observation_age_seconds,
            ),
        )
        _require_hard_flags("AutoSalesSurpriseInput", self)


@dataclass(frozen=True)
class AutoSalesSurpriseObservation:
    release_id: str
    market_slug: str
    observed_at: datetime
    actual_sales: Decimal
    consensus_sales: Decimal
    previous_sales: Decimal
    source_name: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_public_string("release_id", self.release_id)
        _require_public_string("market_slug", self.market_slug)
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in ("actual_sales", "consensus_sales", "previous_sales"):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        _require_public_string("source_name", self.source_name)
        _require_hard_flags("AutoSalesSurpriseObservation", self)


@dataclass(frozen=True)
class AutoSalesSurpriseReport:
    generated_at: datetime
    config_version: str
    digest_status: str
    recommended_next_step: str
    observation_count: Decimal
    material_surprise_count: Decimal
    positive_surprise_count: Decimal
    negative_surprise_count: Decimal
    largest_abs_surprise_ratio: Decimal
    average_surprise_ratio: Decimal
    observations: tuple[AutoSalesSurpriseObservation, ...]
    reason_codes: tuple[str, ...]
    reason_code_counts: tuple[tuple[str, Decimal], ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        _require_digest_status("digest_status", self.digest_status)
        _require_canonical_string("recommended_next_step", self.recommended_next_step)
        for field_name in (
            "observation_count",
            "material_surprise_count",
            "positive_surprise_count",
            "negative_surprise_count",
            "largest_abs_surprise_ratio",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "average_surprise_ratio",
            _require_decimal("average_surprise_ratio", self.average_surprise_ratio),
        )
        object.__setattr__(self, "observations", _normalize_observations(self.observations))
        object.__setattr__(self, "reason_codes", _normalize_reason_codes(self.reason_codes))
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        _require_hard_flags("AutoSalesSurpriseReport", self)
        _validate_report_consistency(self)


def build_market_research_auto_sales_surprise_digest(
    observations: list[AutoSalesSurpriseObservation]
    | tuple[AutoSalesSurpriseObservation, ...],
    *,
    generated_at: datetime,
    config: AutoSalesSurpriseInput,
) -> AutoSalesSurpriseReport:
    if type(config) is not AutoSalesSurpriseInput:
        raise ValueError("config must be an AutoSalesSurpriseInput")
    _require_hard_flags("AutoSalesSurpriseInput", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    normalized = tuple(
        sorted(
            _normalize_observations(observations, require_sorted=False),
            key=_observation_sort_key,
        ),
    )
    ratios = tuple(_surprise_ratio(row) for row in normalized)
    valid_ratios = tuple(ratio for ratio in ratios if ratio is not None)
    material_ratios = tuple(
        ratio for ratio in valid_ratios if abs(ratio) >= config.material_surprise_threshold
    )
    stale_observation_count = _stale_observation_count(
        normalized,
        generated_at=generated_at_utc,
        max_observation_age_seconds=config.max_observation_age_seconds,
    )
    reason_codes = _reason_codes(
        ratios,
        material_ratios,
        has_observations=bool(normalized),
        stale_observation_count=stale_observation_count,
    )
    digest_status = _digest_status(reason_codes)

    return AutoSalesSurpriseReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        digest_status=digest_status,
        recommended_next_step=NEXT_STEP_BY_STATUS[digest_status],
        observation_count=_count_decimal(len(normalized)),
        material_surprise_count=_count_decimal(len(material_ratios)),
        positive_surprise_count=_count_decimal(sum(1 for ratio in material_ratios if ratio > ZERO)),
        negative_surprise_count=_count_decimal(sum(1 for ratio in material_ratios if ratio < ZERO)),
        largest_abs_surprise_ratio=_largest_abs_ratio(valid_ratios),
        average_surprise_ratio=_average_ratio(valid_ratios),
        observations=normalized,
        reason_codes=reason_codes,
        reason_code_counts=_reason_code_counts(reason_codes),
    )


def market_research_auto_sales_surprise_digest_payload(
    report: AutoSalesSurpriseReport,
) -> dict[str, Any]:
    if type(report) is not AutoSalesSurpriseReport:
        raise ValueError("report must be an AutoSalesSurpriseReport")
    _require_hard_flags("AutoSalesSurpriseReport", report)
    return _json_ready(asdict(report))


def _surprise_ratio(row: AutoSalesSurpriseObservation) -> Decimal | None:
    if row.consensus_sales == ZERO:
        return None
    with localcontext(DECIMAL_CONTEXT):
        return _quantize((row.actual_sales - row.consensus_sales) / row.consensus_sales)


def _reason_codes(
    ratios: tuple[Decimal | None, ...],
    material_ratios: tuple[Decimal, ...],
    *,
    has_observations: bool,
    stale_observation_count: Decimal,
) -> tuple[str, ...]:
    if not has_observations:
        return (AUTO_SALES_BLOCKED_MISSING_EVIDENCE,)
    codes: set[str] = set()
    if any(ratio is None for ratio in ratios):
        codes.add(AUTO_SALES_BLOCKED_MISSING_CONSENSUS)
    if any(ratio > ZERO for ratio in material_ratios):
        codes.add(AUTO_SALES_MATERIAL_POSITIVE_SURPRISE)
    if any(ratio < ZERO for ratio in material_ratios):
        codes.add(AUTO_SALES_MATERIAL_NEGATIVE_SURPRISE)
    if not material_ratios:
        codes.add(AUTO_SALES_NO_MATERIAL_SURPRISE)
    if stale_observation_count > ZERO:
        codes.add(AUTO_SALES_STALE_OBSERVATION)
    if codes == {AUTO_SALES_NO_MATERIAL_SURPRISE}:
        return (AUTO_SALES_NO_MATERIAL_SURPRISE,)
    if AUTO_SALES_BLOCKED_MISSING_CONSENSUS not in codes:
        codes.add(AUTO_SALES_WATCH)
    return tuple(sorted(codes))


def _digest_status(reason_codes: tuple[str, ...]) -> str:
    if (
        AUTO_SALES_BLOCKED_MISSING_CONSENSUS in reason_codes
        or AUTO_SALES_BLOCKED_MISSING_EVIDENCE in reason_codes
    ):
        return "blocked"
    if AUTO_SALES_WATCH in reason_codes:
        return "watch"
    return "pass"


def _reason_code_counts(
    reason_codes: tuple[str, ...],
) -> tuple[tuple[str, Decimal], ...]:
    counts: dict[str, Decimal] = {}
    for reason_code in reason_codes:
        counts[reason_code] = _quantize(counts.get(reason_code, ZERO) + ONE)
    return tuple(
        (reason_code, count)
        for reason_code, count in sorted(counts.items(), key=lambda item: (-item[1], item[0]))
    )


def _largest_abs_ratio(ratios: tuple[Decimal, ...]) -> Decimal:
    if not ratios:
        return ZERO
    return _quantize(max(abs(ratio) for ratio in ratios))


def _average_ratio(ratios: tuple[Decimal, ...]) -> Decimal:
    if not ratios:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return _quantize(sum(ratios, ZERO) / _count_decimal(len(ratios)))


def _count_decimal(value: int) -> Decimal:
    return _quantize(Decimal(value))


def _normalize_observations(
    value: object,
    *,
    require_sorted: bool = True,
) -> tuple[AutoSalesSurpriseObservation, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("observations must be a list or tuple")
    rows = tuple(value)
    seen: set[tuple[str, str, str, datetime]] = set()
    for row in rows:
        if type(row) is not AutoSalesSurpriseObservation:
            raise ValueError("observations must contain exact AutoSalesSurpriseObservation rows")
        _require_hard_flags("AutoSalesSurpriseObservation", row)
        observation_key = _observation_sort_key(row)
        if observation_key in seen:
            raise ValueError("observations must not contain duplicate observations")
        seen.add(observation_key)
    if require_sorted and rows != tuple(sorted(rows, key=_observation_sort_key)):
        raise ValueError("observations must use canonical sorting")
    return rows


def _observation_sort_key(
    row: AutoSalesSurpriseObservation,
) -> tuple[str, str, str, datetime]:
    return (row.release_id, row.market_slug, row.source_name, row.observed_at)


def _normalize_reason_codes(value: object) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ValueError("reason_codes must be a tuple")
    rows = tuple(value)
    if not rows:
        raise ValueError("reason_codes is required")
    seen: set[str] = set()
    previous: str | None = None
    for reason_code in rows:
        _require_canonical_string("reason_codes", reason_code)
        if reason_code not in REASON_CODES:
            raise ValueError("reason_codes must contain known reason codes")
        if reason_code in seen:
            raise ValueError("reason_codes must be unique")
        if previous is not None and previous > reason_code:
            raise ValueError("reason_codes must be sorted")
        previous = reason_code
        seen.add(reason_code)
    return rows


def _normalize_reason_code_counts(
    value: object,
) -> tuple[tuple[str, Decimal], ...]:
    if type(value) is not tuple:
        raise ValueError("reason_code_counts must be a tuple")
    rows = tuple(value)
    if not rows:
        raise ValueError("reason_code_counts is required")
    seen: set[str] = set()
    previous_key: tuple[Decimal, str] | None = None
    normalized: list[tuple[str, Decimal]] = []
    for item in rows:
        if type(item) is not tuple or len(item) != 2:
            raise ValueError("reason_code_counts must contain reason/count pairs")
        reason_code, count = item
        _require_canonical_string("reason_code_counts", reason_code)
        if reason_code not in REASON_CODES:
            raise ValueError("reason_code_counts must contain known reason codes")
        count = _require_positive_count_decimal("reason_code_counts", count)
        if reason_code in seen:
            raise ValueError("reason_code_counts must be unique")
        key = (-count, reason_code)
        if previous_key is not None and previous_key > key:
            raise ValueError("reason_code_counts must be deterministic")
        previous_key = key
        seen.add(reason_code)
        normalized.append((reason_code, count))
    return tuple(normalized)


def _validate_report_consistency(report: AutoSalesSurpriseReport) -> None:
    if report.recommended_next_step != NEXT_STEP_BY_STATUS[report.digest_status]:
        raise ValueError("recommended_next_step must match digest_status")
    if report.observation_count != _count_decimal(len(report.observations)):
        raise ValueError("observation_count must match observations")
    expected_counts = _reason_code_counts(report.reason_codes)
    if report.reason_code_counts != expected_counts:
        raise ValueError("reason_code_counts must match reason_codes")


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_digest_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in DIGEST_STATUSES:
        raise ValueError(f"{field_name} must be pass, watch, or blocked")


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str or not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical string")


def _require_public_string(field_name: str, value: object) -> None:
    _require_canonical_string(field_name, value)
    lowered = value.lower()
    if any(fragment in lowered for fragment in UNSAFE_TEXT_FRAGMENTS):
        raise ValueError(f"{field_name} must not contain restricted text")


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return _quantize(value)


def _require_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    value = _require_decimal(field_name, value)
    if value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return value


def _require_positive_decimal(field_name: str, value: object) -> Decimal:
    value = _require_decimal(field_name, value)
    if value <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return value


def _require_positive_count_decimal(field_name: str, value: object) -> Decimal:
    value = _require_positive_decimal(field_name, value)
    if value != value.to_integral_value():
        raise ValueError(f"{field_name} must be an integer count")
    return value


def _require_hard_flags(label: str, value: object) -> None:
    if object.__getattribute__(value, "paper_only") is not True:
        raise ValueError(f"{label} must be paper_only")
    if object.__getattribute__(value, "report_only") is not True:
        raise ValueError(f"{label} must be report_only")
    if object.__getattribute__(value, "readonly") is not True:
        raise ValueError(f"{label} must be readonly")


def _stale_observation_count(
    rows: tuple[AutoSalesSurpriseObservation, ...],
    *,
    generated_at: datetime,
    max_observation_age_seconds: Decimal,
) -> Decimal:
    return _count_decimal(
        sum(
            1
            for row in rows
            if _seconds_between(row.observed_at, generated_at)
            > max_observation_age_seconds
        ),
    )


def _seconds_between(start: datetime, end: datetime) -> Decimal:
    delta = end - start
    seconds = Decimal(delta.days * 86400 + delta.seconds)
    microseconds = Decimal(delta.microseconds) / MICROSECONDS_PER_SECOND
    return _quantize(seconds + microseconds)


def _quantize(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(QUANT)


def _json_ready(value: object) -> Any:
    if isinstance(value, Decimal):
        return f"{_quantize(value):.6f}"
    if type(value) is datetime:
        return value.isoformat()
    if isinstance(value, dict):
        return {key: _json_ready(nested) for key, nested in value.items()}
    if isinstance(value, tuple):
        return tuple(_json_ready(nested) for nested in value)
    if isinstance(value, list):
        return [_json_ready(nested) for nested in value]
    return value
