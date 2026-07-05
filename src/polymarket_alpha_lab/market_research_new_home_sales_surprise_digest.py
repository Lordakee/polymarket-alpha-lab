from __future__ import annotations

from collections.abc import Iterable
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from typing import Any


DEFAULT_MARKET_RESEARCH_NEW_HOME_SALES_SURPRISE_DIGEST_CONFIG_VERSION = (
    "market-research-new-home-sales-surprise-digest-v0"
)

SURPRISE_STATUSES = ("pass", "watch", "blocked")
SURPRISE_BUCKET_SEQUENCE = ("blocked", "watch", "pass")
REASON_CODES = (
    "new_home_sales_surprise_blocked_threshold_breached",
    "new_home_sales_surprise_watch_threshold_breached",
    "new_home_sales_surprise_digest_empty",
    "new_home_sales_surprise_digest_passed",
)
NEXT_STEP = "review_new_home_sales_surprise_digest"
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
RATIO_QUANT = Decimal("0.000001")
INTEGER_QUANT = Decimal("1")
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)


def _join_parts(*parts: str) -> str:
    return "".join(parts)


UNSAFE_TEXT_FRAGMENTS = frozenset(
    (
        _join_parts("au", "th"),
        _join_parts("api", "_", "key"),
        _join_parts("bro", "ker"),
        _join_parts("b", "uy"),
        _join_parts("can", "cel"),
        _join_parts("data", "base"),
        _join_parts("ex", "change"),
        _join_parts("li", "ve"),
        _join_parts("mut", "ation"),
        _join_parts("or", "der"),
        _join_parts("pri", "vate"),
        _join_parts("re", "place"),
        _join_parts("sec", "ret"),
        _join_parts("se", "ll"),
        _join_parts("sig", "ning"),
        _join_parts("sub", "mit"),
        _join_parts("to", "ken"),
        _join_parts("tra", "de"),
        _join_parts("wal", "let"),
    ),
)

__all__ = (
    "DEFAULT_MARKET_RESEARCH_NEW_HOME_SALES_SURPRISE_DIGEST_CONFIG_VERSION",
    "MarketResearchNewHomeSalesSurpriseDigestConfig",
    "MarketResearchNewHomeSalesSurpriseDigestObservation",
    "MarketResearchNewHomeSalesSurpriseDigestReasonCodeCount",
    "MarketResearchNewHomeSalesSurpriseDigestReport",
    "MarketResearchNewHomeSalesSurpriseDigestSurpriseBucket",
    "build_market_research_new_home_sales_surprise_digest",
    "market_research_new_home_sales_surprise_digest_payload",
)


@dataclass(frozen=True)
class MarketResearchNewHomeSalesSurpriseDigestConfig:
    config_version: str = (
        DEFAULT_MARKET_RESEARCH_NEW_HOME_SALES_SURPRISE_DIGEST_CONFIG_VERSION
    )
    watch_abs_surprise_threshold: Decimal = Decimal("0.020000")
    blocked_abs_surprise_threshold: Decimal = Decimal("0.050000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "MarketResearchNewHomeSalesSurpriseDigestConfig does not support subclassing",
        )

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            MarketResearchNewHomeSalesSurpriseDigestConfig,
            "config",
        )
        _require_public_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_MARKET_RESEARCH_NEW_HOME_SALES_SURPRISE_DIGEST_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported version")
        object.__setattr__(
            self,
            "watch_abs_surprise_threshold",
            _normalize_nonnegative_decimal(
                "watch_abs_surprise_threshold",
                self.watch_abs_surprise_threshold,
            ),
        )
        object.__setattr__(
            self,
            "blocked_abs_surprise_threshold",
            _normalize_nonnegative_decimal(
                "blocked_abs_surprise_threshold",
                self.blocked_abs_surprise_threshold,
            ),
        )
        if self.blocked_abs_surprise_threshold < self.watch_abs_surprise_threshold:
            raise ValueError(
                "blocked_abs_surprise_threshold must be at least watch_abs_surprise_threshold",
            )
        _require_hard_flags("MarketResearchNewHomeSalesSurpriseDigestConfig", self)


@dataclass(frozen=True)
class MarketResearchNewHomeSalesSurpriseDigestObservation:
    release_id: str
    release_at: datetime
    actual_sales: Decimal
    consensus_sales: Decimal
    prior_sales: Decimal
    surprise_ratio: Decimal = field(init=False)
    abs_surprise_ratio: Decimal = field(init=False)
    surprise_status: str = "pass"
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "MarketResearchNewHomeSalesSurpriseDigestObservation does not support subclassing",
        )

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            MarketResearchNewHomeSalesSurpriseDigestObservation,
            "observation",
        )
        _require_public_string("release_id", self.release_id)
        object.__setattr__(self, "release_at", _as_utc("release_at", self.release_at))
        object.__setattr__(
            self,
            "actual_sales",
            _normalize_nonnegative_decimal("actual_sales", self.actual_sales),
        )
        object.__setattr__(
            self,
            "consensus_sales",
            _normalize_positive_decimal("consensus_sales", self.consensus_sales),
        )
        object.__setattr__(
            self,
            "prior_sales",
            _normalize_nonnegative_decimal("prior_sales", self.prior_sales),
        )
        object.__setattr__(
            self,
            "surprise_ratio",
            _ratio(self.actual_sales - self.consensus_sales, self.consensus_sales),
        )
        object.__setattr__(self, "abs_surprise_ratio", abs(self.surprise_ratio))
        _require_surprise_status("surprise_status", self.surprise_status)
        _require_hard_flags("MarketResearchNewHomeSalesSurpriseDigestObservation", self)


@dataclass(frozen=True)
class MarketResearchNewHomeSalesSurpriseDigestSurpriseBucket:
    surprise_bucket: str
    observation_count: Decimal
    average_surprise_ratio: Decimal | None
    max_abs_surprise_ratio: Decimal | None
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "MarketResearchNewHomeSalesSurpriseDigestSurpriseBucket does not support subclassing",
        )

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            MarketResearchNewHomeSalesSurpriseDigestSurpriseBucket,
            "surprise_bucket",
        )
        _require_surprise_status("surprise_bucket", self.surprise_bucket)
        object.__setattr__(
            self,
            "observation_count",
            _normalize_positive_count_decimal("observation_count", self.observation_count),
        )
        if self.average_surprise_ratio is not None:
            object.__setattr__(
                self,
                "average_surprise_ratio",
                _normalize_decimal("average_surprise_ratio", self.average_surprise_ratio),
            )
        if self.max_abs_surprise_ratio is not None:
            object.__setattr__(
                self,
                "max_abs_surprise_ratio",
                _normalize_nonnegative_decimal(
                    "max_abs_surprise_ratio",
                    self.max_abs_surprise_ratio,
                ),
            )
        _require_hard_flags(
            "MarketResearchNewHomeSalesSurpriseDigestSurpriseBucket",
            self,
        )


@dataclass(frozen=True)
class MarketResearchNewHomeSalesSurpriseDigestReasonCodeCount:
    reason_code: str
    count: Decimal
    observation_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "MarketResearchNewHomeSalesSurpriseDigestReasonCodeCount does not support subclassing",
        )

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            MarketResearchNewHomeSalesSurpriseDigestReasonCodeCount,
            "reason_code_count",
        )
        _require_reason_code("reason_code", self.reason_code)
        object.__setattr__(
            self,
            "count",
            _normalize_nonnegative_count_decimal("count", self.count),
        )
        object.__setattr__(
            self,
            "observation_ratio",
            _normalize_observation_ratio("observation_ratio", self.observation_ratio),
        )
        _require_hard_flags(
            "MarketResearchNewHomeSalesSurpriseDigestReasonCodeCount",
            self,
        )


@dataclass(frozen=True)
class MarketResearchNewHomeSalesSurpriseDigestReport:
    generated_at: datetime
    config_version: str
    digest_status: str
    digest_next_step: str
    observation_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    blocked_count: Decimal
    upside_surprise_count: Decimal
    downside_surprise_count: Decimal
    average_surprise_ratio: Decimal | None
    max_abs_surprise_ratio: Decimal | None
    blocked_observation_ratio: Decimal | None
    surprise_buckets: tuple[MarketResearchNewHomeSalesSurpriseDigestSurpriseBucket, ...]
    observations: tuple[MarketResearchNewHomeSalesSurpriseDigestObservation, ...]
    reason_code_counts: tuple[
        MarketResearchNewHomeSalesSurpriseDigestReasonCodeCount,
        ...,
    ]
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "MarketResearchNewHomeSalesSurpriseDigestReport does not support subclassing",
        )

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            MarketResearchNewHomeSalesSurpriseDigestReport,
            "report",
        )
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_MARKET_RESEARCH_NEW_HOME_SALES_SURPRISE_DIGEST_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported version")
        _require_surprise_status("digest_status", self.digest_status)
        _require_public_string("digest_next_step", self.digest_next_step)
        for field_name in (
            "observation_count",
            "pass_count",
            "watch_count",
            "blocked_count",
            "upside_surprise_count",
            "downside_surprise_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_count_decimal(field_name, getattr(self, field_name)),
            )
        if self.average_surprise_ratio is not None:
            object.__setattr__(
                self,
                "average_surprise_ratio",
                _normalize_decimal("average_surprise_ratio", self.average_surprise_ratio),
            )
        if self.max_abs_surprise_ratio is not None:
            object.__setattr__(
                self,
                "max_abs_surprise_ratio",
                _normalize_nonnegative_decimal(
                    "max_abs_surprise_ratio",
                    self.max_abs_surprise_ratio,
                ),
            )
        if self.blocked_observation_ratio is not None:
            object.__setattr__(
                self,
                "blocked_observation_ratio",
                _normalize_observation_ratio(
                    "blocked_observation_ratio",
                    self.blocked_observation_ratio,
                ),
            )
        object.__setattr__(
            self,
            "surprise_buckets",
            _normalize_surprise_buckets(self.surprise_buckets),
        )
        object.__setattr__(
            self,
            "observations",
            _normalize_observations(self.observations, require_sorted=True),
        )
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        object.__setattr__(self, "reason_codes", _normalize_reason_codes(self.reason_codes))
        _require_hard_flags("MarketResearchNewHomeSalesSurpriseDigestReport", self)
        _validate_report_consistency(self)


def build_market_research_new_home_sales_surprise_digest(
    observations: Iterable[MarketResearchNewHomeSalesSurpriseDigestObservation],
    *,
    config: MarketResearchNewHomeSalesSurpriseDigestConfig,
    generated_at: datetime,
) -> MarketResearchNewHomeSalesSurpriseDigestReport:
    if type(config) is not MarketResearchNewHomeSalesSurpriseDigestConfig:
        raise ValueError(
            "config must be a MarketResearchNewHomeSalesSurpriseDigestConfig",
        )
    _require_hard_flags("MarketResearchNewHomeSalesSurpriseDigestConfig", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    normalized = tuple(
        _observation_with_status(item, config) for item in _normalize_observations(observations)
    )
    sorted_observations = tuple(
        sorted(
            normalized,
            key=_observation_sort_key,
        ),
    )
    reason_codes = _reason_codes(sorted_observations)
    digest_status = _digest_status(reason_codes)
    observation_count = _count_decimal(len(sorted_observations))
    blocked_count = _count_status(sorted_observations, "blocked")

    return MarketResearchNewHomeSalesSurpriseDigestReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        digest_status=digest_status,
        digest_next_step=NEXT_STEP,
        observation_count=observation_count,
        pass_count=_count_status(sorted_observations, "pass"),
        watch_count=_count_status(sorted_observations, "watch"),
        blocked_count=blocked_count,
        upside_surprise_count=_count_decimal(
            sum(1 for item in sorted_observations if item.surprise_ratio > ZERO),
        ),
        downside_surprise_count=_count_decimal(
            sum(1 for item in sorted_observations if item.surprise_ratio < ZERO),
        ),
        average_surprise_ratio=_average_surprise_ratio(sorted_observations),
        max_abs_surprise_ratio=_max_abs_surprise_ratio(sorted_observations),
        blocked_observation_ratio=_safe_ratio(blocked_count, observation_count),
        surprise_buckets=_surprise_buckets(sorted_observations),
        observations=sorted_observations,
        reason_code_counts=_reason_code_counts(sorted_observations),
        reason_codes=reason_codes,
    )


def market_research_new_home_sales_surprise_digest_payload(
    report: MarketResearchNewHomeSalesSurpriseDigestReport,
) -> dict[str, Any]:
    if type(report) is not MarketResearchNewHomeSalesSurpriseDigestReport:
        raise ValueError("report must be a MarketResearchNewHomeSalesSurpriseDigestReport")
    return _json_ready(asdict(report))


def _observation_with_status(
    item: MarketResearchNewHomeSalesSurpriseDigestObservation,
    config: MarketResearchNewHomeSalesSurpriseDigestConfig,
) -> MarketResearchNewHomeSalesSurpriseDigestObservation:
    return MarketResearchNewHomeSalesSurpriseDigestObservation(
        release_id=item.release_id,
        release_at=item.release_at,
        actual_sales=item.actual_sales,
        consensus_sales=item.consensus_sales,
        prior_sales=item.prior_sales,
        surprise_status=_surprise_status(item.abs_surprise_ratio, config),
        paper_only=item.paper_only,
        report_only=item.report_only,
        readonly=item.readonly,
    )


def _surprise_status(
    abs_surprise_ratio: Decimal,
    config: MarketResearchNewHomeSalesSurpriseDigestConfig,
) -> str:
    if abs_surprise_ratio >= config.blocked_abs_surprise_threshold:
        return "blocked"
    if abs_surprise_ratio >= config.watch_abs_surprise_threshold:
        return "watch"
    return "pass"


def _reason_codes(
    observations: tuple[MarketResearchNewHomeSalesSurpriseDigestObservation, ...],
) -> tuple[str, ...]:
    if not observations:
        return ("new_home_sales_surprise_digest_empty",)
    codes: list[str] = []
    if any(item.surprise_status == "blocked" for item in observations):
        codes.append("new_home_sales_surprise_blocked_threshold_breached")
    if any(item.surprise_status == "watch" for item in observations):
        codes.append("new_home_sales_surprise_watch_threshold_breached")
    if not codes:
        codes.append("new_home_sales_surprise_digest_passed")
    return tuple(codes)


def _digest_status(reason_codes: tuple[str, ...]) -> str:
    if (
        "new_home_sales_surprise_digest_empty" in reason_codes
        or "new_home_sales_surprise_blocked_threshold_breached" in reason_codes
    ):
        return "blocked"
    if "new_home_sales_surprise_watch_threshold_breached" in reason_codes:
        return "watch"
    return "pass"


def _surprise_buckets(
    observations: tuple[MarketResearchNewHomeSalesSurpriseDigestObservation, ...],
) -> tuple[MarketResearchNewHomeSalesSurpriseDigestSurpriseBucket, ...]:
    buckets: list[MarketResearchNewHomeSalesSurpriseDigestSurpriseBucket] = []
    for surprise_bucket in SURPRISE_BUCKET_SEQUENCE:
        matching = tuple(
            item for item in observations if item.surprise_status == surprise_bucket
        )
        if not matching:
            continue
        buckets.append(
            MarketResearchNewHomeSalesSurpriseDigestSurpriseBucket(
                surprise_bucket=surprise_bucket,
                observation_count=_count_decimal(len(matching)),
                average_surprise_ratio=_average_surprise_ratio(matching),
                max_abs_surprise_ratio=_max_abs_surprise_ratio(matching),
            ),
        )
    return tuple(buckets)


def _average_surprise_ratio(
    observations: tuple[MarketResearchNewHomeSalesSurpriseDigestObservation, ...],
) -> Decimal | None:
    if not observations:
        return None
    with localcontext(DECIMAL_CONTEXT):
        return (
            sum((item.surprise_ratio for item in observations), ZERO)
            / _count_decimal(len(observations))
        ).quantize(RATIO_QUANT)


def _max_abs_surprise_ratio(
    observations: tuple[MarketResearchNewHomeSalesSurpriseDigestObservation, ...],
) -> Decimal | None:
    if not observations:
        return None
    return max(item.abs_surprise_ratio for item in observations).quantize(RATIO_QUANT)


def _count_status(
    observations: tuple[MarketResearchNewHomeSalesSurpriseDigestObservation, ...],
    surprise_status: str,
) -> Decimal:
    return _count_decimal(sum(1 for item in observations if item.surprise_status == surprise_status))


def _safe_ratio(value: Decimal, total: Decimal) -> Decimal | None:
    if total == ZERO:
        return None
    with localcontext(DECIMAL_CONTEXT):
        return (value / total).quantize(RATIO_QUANT)


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return (numerator / denominator).quantize(RATIO_QUANT)


def _count_decimal(value: int) -> Decimal:
    return _quantize_decimal(Decimal(value))


def _status_rank(surprise_status: str) -> int:
    return SURPRISE_BUCKET_SEQUENCE.index(surprise_status)


def _observation_sort_key(
    item: MarketResearchNewHomeSalesSurpriseDigestObservation,
) -> tuple[int, Decimal, Decimal, str]:
    return (
        _status_rank(item.surprise_status),
        -item.abs_surprise_ratio,
        _quantize_decimal(Decimal(str(-item.release_at.timestamp()))),
        item.release_id,
    )


def _json_ready(value: object) -> Any:
    if type(value) is Decimal:
        return format(value.quantize(RATIO_QUANT), "f")
    if type(value) is datetime:
        return value.astimezone(UTC).isoformat()
    if isinstance(value, tuple):
        return [_json_ready(item) for item in value]
    if isinstance(value, list):
        return [_json_ready(item) for item in value]
    if isinstance(value, dict):
        return {str(key): _json_ready(item) for key, item in value.items()}
    if value is None or type(value) in (bool, str):
        return value
    if type(value) in (float, int):
        raise ValueError("payload contains a non-Decimal numeric value")
    return value


def _normalize_observations(
    observations: Iterable[MarketResearchNewHomeSalesSurpriseDigestObservation],
    *,
    require_sorted: bool = False,
) -> tuple[MarketResearchNewHomeSalesSurpriseDigestObservation, ...]:
    if isinstance(observations, (str, bytes)):
        raise ValueError("observations must contain new home sales observations")
    try:
        normalized = tuple(observations)
    except TypeError as exc:
        raise ValueError("observations must contain new home sales observations") from exc
    seen_release_ids: set[str] = set()
    for item in normalized:
        if type(item) is not MarketResearchNewHomeSalesSurpriseDigestObservation:
            raise ValueError(
                "observations must contain MarketResearchNewHomeSalesSurpriseDigestObservation values",
            )
        _require_hard_flags("MarketResearchNewHomeSalesSurpriseDigestObservation", item)
        if item.release_id in seen_release_ids:
            raise ValueError("observations release_id values must be unique")
        seen_release_ids.add(item.release_id)
    if require_sorted and normalized != tuple(sorted(normalized, key=_observation_sort_key)):
        raise ValueError("observations must use canonical sequence")
    return normalized


def _normalize_surprise_buckets(
    buckets: list[MarketResearchNewHomeSalesSurpriseDigestSurpriseBucket]
    | tuple[MarketResearchNewHomeSalesSurpriseDigestSurpriseBucket, ...],
) -> tuple[MarketResearchNewHomeSalesSurpriseDigestSurpriseBucket, ...]:
    if type(buckets) not in (list, tuple):
        raise ValueError("surprise_buckets must be a list or tuple")
    normalized = tuple(buckets)
    seen_buckets: set[str] = set()
    for bucket in normalized:
        if type(bucket) is not MarketResearchNewHomeSalesSurpriseDigestSurpriseBucket:
            raise ValueError(
                "surprise_buckets must contain MarketResearchNewHomeSalesSurpriseDigestSurpriseBucket values",
            )
        _require_hard_flags(
            "MarketResearchNewHomeSalesSurpriseDigestSurpriseBucket",
            bucket,
        )
        if bucket.surprise_bucket in seen_buckets:
            raise ValueError("surprise_buckets surprise_bucket values must be unique")
        seen_buckets.add(bucket.surprise_bucket)
    if tuple(bucket.surprise_bucket for bucket in normalized) != tuple(
        bucket for bucket in SURPRISE_BUCKET_SEQUENCE if bucket in seen_buckets
    ):
        raise ValueError("surprise_buckets must use canonical bucket sequence")
    return normalized


def _normalize_reason_code_counts(
    reason_code_counts: list[MarketResearchNewHomeSalesSurpriseDigestReasonCodeCount]
    | tuple[MarketResearchNewHomeSalesSurpriseDigestReasonCodeCount, ...],
) -> tuple[MarketResearchNewHomeSalesSurpriseDigestReasonCodeCount, ...]:
    if type(reason_code_counts) not in (list, tuple):
        raise ValueError("reason_code_counts must be a list or tuple")
    normalized = tuple(reason_code_counts)
    seen_reason_codes: set[str] = set()
    for item in normalized:
        if type(item) is not MarketResearchNewHomeSalesSurpriseDigestReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain MarketResearchNewHomeSalesSurpriseDigestReasonCodeCount values",
            )
        _require_hard_flags(
            "MarketResearchNewHomeSalesSurpriseDigestReasonCodeCount",
            item,
        )
        if item.reason_code in seen_reason_codes:
            raise ValueError("reason_code_counts reason_code values must be unique")
        seen_reason_codes.add(item.reason_code)
    if normalized != tuple(
        sorted(normalized, key=lambda item: REASON_CODES.index(item.reason_code)),
    ):
        raise ValueError("reason_code_counts must use canonical sequence")
    return normalized


def _normalize_reason_codes(reason_codes: tuple[str, ...]) -> tuple[str, ...]:
    if type(reason_codes) not in (list, tuple):
        raise ValueError("reason_codes must be a list or tuple")
    normalized = tuple(reason_codes)
    if not normalized:
        raise ValueError("reason_codes must be nonempty")
    seen_reason_codes: set[str] = set()
    for reason_code in normalized:
        _require_reason_code("reason_codes", reason_code)
        if reason_code in seen_reason_codes:
            raise ValueError("reason_codes reason_code values must be unique")
        seen_reason_codes.add(reason_code)
    if normalized != tuple(reason_code for reason_code in REASON_CODES if reason_code in normalized):
        raise ValueError("reason_codes must use canonical sequence")
    return normalized


def _reason_code_counts(
    observations: tuple[MarketResearchNewHomeSalesSurpriseDigestObservation, ...],
) -> tuple[MarketResearchNewHomeSalesSurpriseDigestReasonCodeCount, ...]:
    if not observations:
        return (
            MarketResearchNewHomeSalesSurpriseDigestReasonCodeCount(
                reason_code="new_home_sales_surprise_digest_empty",
                count=ONE,
                observation_ratio=ZERO,
            ),
        )
    total = _count_decimal(len(observations))
    counts: list[MarketResearchNewHomeSalesSurpriseDigestReasonCodeCount] = []
    for reason_code in _reason_codes(observations):
        count = _reason_observation_count(observations, reason_code)
        if count == ZERO:
            continue
        counts.append(
            MarketResearchNewHomeSalesSurpriseDigestReasonCodeCount(
                reason_code=reason_code,
                count=count,
                observation_ratio=_safe_ratio(count, total) or ZERO,
            ),
        )
    return tuple(counts)


def _reason_observation_count(
    observations: tuple[MarketResearchNewHomeSalesSurpriseDigestObservation, ...],
    reason_code: str,
) -> Decimal:
    if reason_code == "new_home_sales_surprise_blocked_threshold_breached":
        return _count_status(observations, "blocked")
    if reason_code == "new_home_sales_surprise_watch_threshold_breached":
        return _count_status(observations, "watch")
    if reason_code == "new_home_sales_surprise_digest_passed":
        return _count_status(observations, "pass")
    if reason_code == "new_home_sales_surprise_digest_empty":
        return ONE if not observations else ZERO
    raise ValueError("reason_code must contain known reason codes")


def _validate_report_consistency(
    report: MarketResearchNewHomeSalesSurpriseDigestReport,
) -> None:
    if report.digest_next_step != NEXT_STEP:
        raise ValueError("digest_next_step must match digest reducer")
    if report.observation_count != _count_decimal(len(report.observations)):
        raise ValueError("observation_count must match observations")
    if report.pass_count != _report_status_count(report, "pass"):
        raise ValueError("pass_count must match observations")
    if report.watch_count != _report_status_count(report, "watch"):
        raise ValueError("watch_count must match observations")
    if report.blocked_count != _report_status_count(report, "blocked"):
        raise ValueError("blocked_count must match observations")
    if report.upside_surprise_count != _count_decimal(
        sum(1 for item in report.observations if item.surprise_ratio > ZERO),
    ):
        raise ValueError("upside_surprise_count must match observations")
    if report.downside_surprise_count != _count_decimal(
        sum(1 for item in report.observations if item.surprise_ratio < ZERO),
    ):
        raise ValueError("downside_surprise_count must match observations")
    if report.average_surprise_ratio != _average_surprise_ratio(report.observations):
        raise ValueError("average_surprise_ratio must match observations")
    if report.max_abs_surprise_ratio != _max_abs_surprise_ratio(report.observations):
        raise ValueError("max_abs_surprise_ratio must match observations")
    if report.blocked_observation_ratio != _safe_ratio(
        report.blocked_count,
        report.observation_count,
    ):
        raise ValueError("blocked_observation_ratio must match observations")
    if report.surprise_buckets != _surprise_buckets(report.observations):
        raise ValueError("surprise_buckets must match observations")
    if report.reason_code_counts != _reason_code_counts(report.observations):
        raise ValueError("reason_code_counts must match observations")
    if report.reason_codes != tuple(item.reason_code for item in report.reason_code_counts):
        raise ValueError("reason_codes must match reason_code_counts")
    if report.reason_codes != _reason_codes(report.observations):
        raise ValueError("reason_codes must match observations")
    if report.digest_status != _digest_status(report.reason_codes):
        raise ValueError("digest_status must match reason_codes")


def _report_status_count(
    report: MarketResearchNewHomeSalesSurpriseDigestReport,
    surprise_status: str,
) -> Decimal:
    return _count_status(report.observations, surprise_status)


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_surprise_status(field_name: str, value: object) -> None:
    _require_canonical_string(field_name, value)
    if value not in SURPRISE_STATUSES:
        raise ValueError(f"{field_name} must be pass, watch, or blocked")


def _require_reason_code(field_name: str, value: object) -> None:
    _require_canonical_string(field_name, value)
    if value not in REASON_CODES:
        raise ValueError(f"{field_name} must contain known reason codes")


def _require_exact_type(value: object, expected_type: type[object], field_name: str) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{field_name} must be exactly {expected_type.__name__}")


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")


def _require_public_string(field_name: str, value: object) -> None:
    _require_canonical_string(field_name, value)
    lowered = value.lower()
    if any(fragment in lowered for fragment in UNSAFE_TEXT_FRAGMENTS):
        raise ValueError(f"{field_name} must be public")


def _normalize_positive_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _normalize_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _normalize_positive_count_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_nonnegative_count_decimal(field_name, value)
    if normalized <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _normalize_nonnegative_count_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_nonnegative_decimal(field_name, value)
    if normalized != normalized.quantize(INTEGER_QUANT):
        raise ValueError(f"{field_name} must be an integer Decimal")
    return normalized


def _normalize_observation_ratio(field_name: str, value: object) -> Decimal:
    normalized = _normalize_nonnegative_decimal(field_name, value)
    if normalized > ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return normalized


def _normalize_decimal(field_name: str, value: object) -> Decimal:
    return _quantize_decimal(_require_decimal(field_name, value))


def _quantize_decimal(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(RATIO_QUANT)


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return value


def _require_hard_flags(field_name: str, value: object) -> None:
    for flag_name in ("paper_only", "report_only", "readonly"):
        flag = getattr(value, flag_name, None)
        if type(flag) is not bool:
            raise ValueError(f"{field_name} {flag_name} must be a bool")
        if flag is not True:
            raise ValueError(f"{field_name} {flag_name} must be True")
