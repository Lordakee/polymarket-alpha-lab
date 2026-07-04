"""Pure Phase 1 ADP employment surprise research reducer."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from typing import Any


DEFAULT_MARKET_RESEARCH_ADP_EMPLOYMENT_SURPRISE_DIGEST_CONFIG_VERSION = (
    "market-research-adp-employment-surprise-digest-v0"
)

STATUS_PASS = "pass"
STATUS_WATCH = "watch"
STATUS_BLOCKED = "blocked"
DIGEST_STATUSES = (STATUS_PASS, STATUS_WATCH, STATUS_BLOCKED)

REASON_PREFIX = "market_research_adp_employment_surprise_digest_"
NO_INPUTS_REASON = f"{REASON_PREFIX}no_inputs"
NO_MATERIAL_SURPRISE_REASON = f"{REASON_PREFIX}no_material_surprise"
MATERIAL_POSITIVE_SURPRISE_REASON = f"{REASON_PREFIX}material_positive_surprise"
MATERIAL_NEGATIVE_SURPRISE_REASON = f"{REASON_PREFIX}material_negative_surprise"
STALE_OBSERVATION_REASON = f"{REASON_PREFIX}stale_observation"
MISSING_CONSENSUS_REASON = f"{REASON_PREFIX}missing_consensus"
WATCH_REASON = f"{REASON_PREFIX}watch"

REASON_CODE_SEQUENCE = (
    MATERIAL_POSITIVE_SURPRISE_REASON,
    MATERIAL_NEGATIVE_SURPRISE_REASON,
    STALE_OBSERVATION_REASON,
    MISSING_CONSENSUS_REASON,
    WATCH_REASON,
    NO_MATERIAL_SURPRISE_REASON,
    NO_INPUTS_REASON,
)

NEXT_STEPS = {
    STATUS_PASS: "continue_monitoring_adp_employment_surprise",
    STATUS_WATCH: "review_adp_employment_surprise",
    STATUS_BLOCKED: "repair_adp_employment_consensus_inputs",
}

DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
QUANT = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
MICROSECONDS_PER_SECOND = Decimal("1000000")
UNSAFE_TEXT_FRAGMENTS = frozenset(
    (
        "auth",
        "broker",
        "cancel",
        "database",
        "network",
        "order",
        "private",
        "secret",
        "signing",
        "submit",
        "token",
        "trade",
        "wal" "let",
    ),
)


__all__ = (
    "DEFAULT_MARKET_RESEARCH_ADP_EMPLOYMENT_SURPRISE_DIGEST_CONFIG_VERSION",
    "MarketResearchAdpEmploymentSurpriseDigestConfig",
    "MarketResearchAdpEmploymentSurpriseDigestObservation",
    "MarketResearchAdpEmploymentSurpriseDigestReasonCodeCount",
    "MarketResearchAdpEmploymentSurpriseDigestReport",
    "build_market_research_adp_employment_surprise_digest",
    "market_research_adp_employment_surprise_digest_payload",
)


@dataclass(frozen=True)
class MarketResearchAdpEmploymentSurpriseDigestConfig:
    config_version: str = (
        DEFAULT_MARKET_RESEARCH_ADP_EMPLOYMENT_SURPRISE_DIGEST_CONFIG_VERSION
    )
    material_surprise_threshold: Decimal = Decimal("0.150000")
    max_observation_age_seconds: Decimal = Decimal("7200.000000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketResearchAdpEmploymentSurpriseDigestConfig:
            raise TypeError(
                "MarketResearchAdpEmploymentSurpriseDigestConfig does not support "
                "subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not MarketResearchAdpEmploymentSurpriseDigestConfig:
            raise ValueError(
                "config must be exactly "
                "MarketResearchAdpEmploymentSurpriseDigestConfig",
            )
        _require_canonical_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_MARKET_RESEARCH_ADP_EMPLOYMENT_SURPRISE_DIGEST_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        object.__setattr__(
            self,
            "material_surprise_threshold",
            _require_ratio_decimal(
                "material_surprise_threshold",
                self.material_surprise_threshold,
            ),
        )
        object.__setattr__(
            self,
            "max_observation_age_seconds",
            _require_positive_count_decimal(
                "max_observation_age_seconds",
                self.max_observation_age_seconds,
            ),
        )
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class MarketResearchAdpEmploymentSurpriseDigestObservation:
    release_id: str
    market_slug: str
    observed_at: datetime
    actual_jobs_change: Decimal
    consensus_jobs_change: Decimal
    previous_jobs_change: Decimal
    source_name: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketResearchAdpEmploymentSurpriseDigestObservation:
            raise TypeError(
                "MarketResearchAdpEmploymentSurpriseDigestObservation does not "
                "support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not MarketResearchAdpEmploymentSurpriseDigestObservation:
            raise ValueError(
                "observation must be exactly "
                "MarketResearchAdpEmploymentSurpriseDigestObservation",
            )
        for field_name in ("release_id", "market_slug", "source_name"):
            _require_public_string(field_name, getattr(self, field_name))
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in (
            "actual_jobs_change",
            "consensus_jobs_change",
            "previous_jobs_change",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_finite_decimal(field_name, getattr(self, field_name)),
            )
        _require_hard_flags("observation", self)


@dataclass(frozen=True)
class MarketResearchAdpEmploymentSurpriseDigestReasonCodeCount:
    reason_code: str
    count: Decimal
    observation_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketResearchAdpEmploymentSurpriseDigestReasonCodeCount:
            raise TypeError(
                "MarketResearchAdpEmploymentSurpriseDigestReasonCodeCount does "
                "not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not MarketResearchAdpEmploymentSurpriseDigestReasonCodeCount:
            raise ValueError(
                "reason code count must be exactly "
                "MarketResearchAdpEmploymentSurpriseDigestReasonCodeCount",
            )
        _require_reason_code("reason_code", self.reason_code)
        object.__setattr__(
            self,
            "count",
            _require_nonnegative_count_decimal("count", self.count),
        )
        object.__setattr__(
            self,
            "observation_ratio",
            _require_ratio_decimal("observation_ratio", self.observation_ratio),
        )
        _require_hard_flags("reason code count", self)


@dataclass(frozen=True)
class MarketResearchAdpEmploymentSurpriseDigestReport:
    generated_at: datetime
    config_version: str
    digest_status: str
    recommended_next_step: str
    observation_count: Decimal
    material_surprise_count: Decimal
    positive_surprise_count: Decimal
    negative_surprise_count: Decimal
    stale_observation_count: Decimal
    missing_consensus_count: Decimal
    largest_abs_surprise_ratio: Decimal
    average_surprise_ratio: Decimal
    observations: tuple[MarketResearchAdpEmploymentSurpriseDigestObservation, ...]
    reason_codes: tuple[str, ...]
    reason_code_counts: tuple[
        MarketResearchAdpEmploymentSurpriseDigestReasonCodeCount,
        ...,
    ]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketResearchAdpEmploymentSurpriseDigestReport:
            raise TypeError(
                "MarketResearchAdpEmploymentSurpriseDigestReport does not support "
                "subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not MarketResearchAdpEmploymentSurpriseDigestReport:
            raise ValueError(
                "report must be exactly MarketResearchAdpEmploymentSurpriseDigestReport",
            )
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        _require_status("digest_status", self.digest_status)
        _require_public_string("recommended_next_step", self.recommended_next_step)
        if self.recommended_next_step != NEXT_STEPS[self.digest_status]:
            raise ValueError("recommended_next_step must match digest_status")
        for field_name in (
            "observation_count",
            "material_surprise_count",
            "positive_surprise_count",
            "negative_surprise_count",
            "stale_observation_count",
            "missing_consensus_count",
            "largest_abs_surprise_ratio",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_count_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "average_surprise_ratio",
            _require_finite_decimal(
                "average_surprise_ratio",
                self.average_surprise_ratio,
            ),
        )
        object.__setattr__(self, "observations", _normalize_observations(self.observations))
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes),
        )
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        if self.observation_count != _decimal_count(self.observations):
            raise ValueError("observation_count must match observations")
        if (
            self.positive_surprise_count + self.negative_surprise_count
            > self.material_surprise_count
        ):
            raise ValueError("directional surprise counts cannot exceed material count")
        _require_hard_flags("report", self)


def build_market_research_adp_employment_surprise_digest(
    observations: Iterable[MarketResearchAdpEmploymentSurpriseDigestObservation],
    *,
    generated_at: datetime,
    config: MarketResearchAdpEmploymentSurpriseDigestConfig | None = None,
) -> MarketResearchAdpEmploymentSurpriseDigestReport:
    cfg = config or MarketResearchAdpEmploymentSurpriseDigestConfig()
    if type(cfg) is not MarketResearchAdpEmploymentSurpriseDigestConfig:
        raise ValueError(
            "config must be a MarketResearchAdpEmploymentSurpriseDigestConfig",
        )
    _require_hard_flags("config", cfg)
    generated_at_utc = _as_utc("generated_at", generated_at)
    normalized = tuple(sorted(_coerce_observations(observations), key=_observation_sort_key))

    ratios = tuple(_surprise_ratio(row) for row in normalized)
    valid_ratios = tuple(ratio for ratio in ratios if ratio is not None)
    material_ratios = tuple(
        ratio
        for ratio in valid_ratios
        if abs(ratio) >= cfg.material_surprise_threshold
    )
    stale_count = _decimal_count(
        row
        for row in normalized
        if _age_seconds(generated_at_utc, row.observed_at) > cfg.max_observation_age_seconds
    )
    missing_consensus_count = _decimal_count(ratio for ratio in ratios if ratio is None)
    reason_codes = _reason_codes(
        valid_ratios=valid_ratios,
        material_ratios=material_ratios,
        stale_count=stale_count,
        missing_consensus_count=missing_consensus_count,
        observation_count=_decimal_count(normalized),
    )
    digest_status = _digest_status(reason_codes)

    return MarketResearchAdpEmploymentSurpriseDigestReport(
        generated_at=generated_at_utc,
        config_version=cfg.config_version,
        digest_status=digest_status,
        recommended_next_step=NEXT_STEPS[digest_status],
        observation_count=_decimal_count(normalized),
        material_surprise_count=_decimal_count(material_ratios),
        positive_surprise_count=_decimal_count(ratio for ratio in material_ratios if ratio > ZERO),
        negative_surprise_count=_decimal_count(ratio for ratio in material_ratios if ratio < ZERO),
        stale_observation_count=stale_count,
        missing_consensus_count=missing_consensus_count,
        largest_abs_surprise_ratio=_largest_abs_ratio(valid_ratios),
        average_surprise_ratio=_average_ratio(valid_ratios),
        observations=normalized,
        reason_codes=reason_codes,
        reason_code_counts=_build_reason_code_counts(
            reason_codes,
            _decimal_count(normalized),
        ),
    )


def market_research_adp_employment_surprise_digest_payload(
    report: MarketResearchAdpEmploymentSurpriseDigestReport,
) -> dict[str, Any]:
    if type(report) is not MarketResearchAdpEmploymentSurpriseDigestReport:
        raise ValueError(
            "report must be a MarketResearchAdpEmploymentSurpriseDigestReport",
        )
    return _to_payload(asdict(report))


def _surprise_ratio(
    observation: MarketResearchAdpEmploymentSurpriseDigestObservation,
) -> Decimal | None:
    if observation.consensus_jobs_change == ZERO:
        return None
    return _quantize(
        (observation.actual_jobs_change - observation.consensus_jobs_change)
        / observation.consensus_jobs_change,
    )


def _reason_codes(
    *,
    valid_ratios: tuple[Decimal, ...],
    material_ratios: tuple[Decimal, ...],
    stale_count: Decimal,
    missing_consensus_count: Decimal,
    observation_count: Decimal,
) -> tuple[str, ...]:
    codes: list[str] = []
    if observation_count == ZERO:
        codes.append(NO_INPUTS_REASON)
    if any(ratio > ZERO for ratio in material_ratios):
        codes.append(MATERIAL_POSITIVE_SURPRISE_REASON)
    if any(ratio < ZERO for ratio in material_ratios):
        codes.append(MATERIAL_NEGATIVE_SURPRISE_REASON)
    if stale_count > ZERO:
        codes.append(STALE_OBSERVATION_REASON)
    if missing_consensus_count > ZERO:
        codes.append(MISSING_CONSENSUS_REASON)
    if not material_ratios and observation_count > ZERO:
        codes.append(NO_MATERIAL_SURPRISE_REASON)
    if (
        valid_ratios
        and (
            MATERIAL_POSITIVE_SURPRISE_REASON in codes
            or MATERIAL_NEGATIVE_SURPRISE_REASON in codes
            or STALE_OBSERVATION_REASON in codes
        )
        and MISSING_CONSENSUS_REASON not in codes
    ):
        codes.append(WATCH_REASON)
    return _ordered_reasons(codes)


def _digest_status(reason_codes: tuple[str, ...]) -> str:
    if MISSING_CONSENSUS_REASON in reason_codes:
        return STATUS_BLOCKED
    if WATCH_REASON in reason_codes or NO_INPUTS_REASON in reason_codes:
        return STATUS_WATCH
    return STATUS_PASS


def _build_reason_code_counts(
    reason_codes: tuple[str, ...],
    observation_count: Decimal,
) -> tuple[MarketResearchAdpEmploymentSurpriseDigestReasonCodeCount, ...]:
    divisor = observation_count
    return tuple(
        MarketResearchAdpEmploymentSurpriseDigestReasonCodeCount(
            reason_code=reason_code,
            count=ZERO if reason_code == NO_INPUTS_REASON else ONE,
            observation_ratio=(
                ZERO
                if divisor == ZERO
                else _quantize(
                    (ZERO if reason_code == NO_INPUTS_REASON else ONE) / divisor,
                )
            ),
        )
        for reason_code in reason_codes
    )


def _coerce_observations(
    observations: Iterable[MarketResearchAdpEmploymentSurpriseDigestObservation],
) -> tuple[MarketResearchAdpEmploymentSurpriseDigestObservation, ...]:
    if isinstance(observations, (str, bytes)) or not isinstance(observations, Iterable):
        raise ValueError("observations must be an iterable")
    rows = tuple(observations)
    for row in rows:
        if type(row) is not MarketResearchAdpEmploymentSurpriseDigestObservation:
            raise ValueError(
                "observations must contain "
                "MarketResearchAdpEmploymentSurpriseDigestObservation items",
            )
        _require_hard_flags("observation", row)
    return rows


def _normalize_observations(
    value: object,
) -> tuple[MarketResearchAdpEmploymentSurpriseDigestObservation, ...]:
    if isinstance(value, (str, bytes)) or not isinstance(value, Iterable):
        raise ValueError("observations must be an iterable")
    rows = tuple(value)
    for row in rows:
        if type(row) is not MarketResearchAdpEmploymentSurpriseDigestObservation:
            raise ValueError(
                "observations must contain "
                "MarketResearchAdpEmploymentSurpriseDigestObservation items",
            )
    return rows


def _normalize_reason_codes(value: object) -> tuple[str, ...]:
    if isinstance(value, (str, bytes)) or not isinstance(value, Iterable):
        raise ValueError("reason_codes must be an iterable")
    return _ordered_reasons(tuple(value))


def _normalize_reason_code_counts(
    value: object,
) -> tuple[MarketResearchAdpEmploymentSurpriseDigestReasonCodeCount, ...]:
    if isinstance(value, (str, bytes)) or not isinstance(value, Iterable):
        raise ValueError("reason_code_counts must be an iterable")
    rows = tuple(value)
    for row in rows:
        if type(row) is not MarketResearchAdpEmploymentSurpriseDigestReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "MarketResearchAdpEmploymentSurpriseDigestReasonCodeCount items",
            )
    return rows


def _ordered_reasons(reason_codes: Iterable[str]) -> tuple[str, ...]:
    unique = set(reason_codes)
    for reason_code in unique:
        _require_reason_code("reason_code", reason_code)
    return tuple(
        reason_code
        for reason_code in sorted(
            unique,
            key=lambda reason_code: (
                REASON_CODE_SEQUENCE.index(reason_code),
                reason_code,
            ),
        )
    )


def _observation_sort_key(
    row: MarketResearchAdpEmploymentSurpriseDigestObservation,
) -> tuple[str, str, str]:
    return (row.release_id, row.market_slug, row.source_name)


def _largest_abs_ratio(ratios: tuple[Decimal, ...]) -> Decimal:
    if not ratios:
        return ZERO
    return _quantize(max(abs(ratio) for ratio in ratios))


def _average_ratio(ratios: tuple[Decimal, ...]) -> Decimal:
    if not ratios:
        return ZERO
    return _quantize(sum(ratios, ZERO) / Decimal(len(ratios)))


def _decimal_count(value: Iterable[object]) -> Decimal:
    return _quantize(Decimal(sum(1 for _ in value)))


def _age_seconds(generated_at: datetime, observed_at: datetime) -> Decimal:
    delta = generated_at - observed_at
    micros = (
        Decimal(delta.days) * Decimal("86400000000")
        + Decimal(delta.seconds) * Decimal("1000000")
        + Decimal(delta.microseconds)
    )
    return max(ZERO, _quantize(micros / MICROSECONDS_PER_SECOND))


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _quantize(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(QUANT)


def _require_finite_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return _quantize(value)


def _require_nonnegative_count_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_finite_decimal(field_name, value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _require_positive_count_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_nonnegative_count_decimal(field_name, value)
    if normalized <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _require_ratio_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_finite_decimal(field_name, value)
    if normalized < ZERO or normalized > ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return normalized


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str or not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical string")


def _require_public_string(field_name: str, value: object) -> None:
    if type(value) is not str or not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a public string")
    lowered = value.lower()
    if any(fragment in lowered for fragment in UNSAFE_TEXT_FRAGMENTS):
        raise ValueError(f"{field_name} must be a public string")


def _require_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in DIGEST_STATUSES:
        raise ValueError(f"{field_name} must be a supported status")


def _require_reason_code(field_name: str, value: object) -> None:
    if type(value) is not str or value not in REASON_CODE_SEQUENCE:
        raise ValueError(f"{field_name} must be a supported reason code")


def _require_hard_flags(field_name: str, value: object) -> None:
    for flag in ("paper_only", "report_only", "readonly"):
        if type(getattr(value, flag, None)) is not bool:
            raise ValueError(f"{field_name} {flag} must be a bool")
        if getattr(value, flag) is not True:
            raise ValueError(f"{field_name} {flag} must be True")


def _to_payload(value: Any) -> Any:
    if isinstance(value, Decimal):
        return format(value, "f")
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, tuple):
        return [_to_payload(item) for item in value]
    if isinstance(value, list):
        return [_to_payload(item) for item in value]
    if isinstance(value, dict):
        return {key: _to_payload(item) for key, item in value.items()}
    return value
