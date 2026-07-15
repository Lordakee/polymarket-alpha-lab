"""Pure report reducer for domain forecast error attribution diagnostics."""

from __future__ import annotations

from dataclasses import asdict, dataclass, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, DecimalException, ROUND_HALF_UP, localcontext
import hashlib
import json
import re
from typing import Any, Mapping, Sequence


DEFAULT_RESEARCH_STRATEGY_DOMAIN_FORECAST_ERROR_ATTRIBUTION_CONFIG_VERSION = (
    "research-strategy-domain-forecast-error-attribution-report"
)

_QUANT = Decimal("0.000001")
_ZERO = Decimal("0.000000")
_ONE = Decimal("1.000000")
_FACTOR_WEIGHT = Decimal("0.250000")
_MODERATE_ATTRIBUTION_THRESHOLD = Decimal("0.250000")
_HIGH_ATTRIBUTION_THRESHOLD = Decimal("0.500000")
_HIGH_FACTOR_PRESSURE_THRESHOLD = Decimal("0.750000")
_MEDIUM_REVIEW_PRIORITY_THRESHOLD = Decimal("0.250000")
_HIGH_REVIEW_PRIORITY_THRESHOLD = Decimal("0.500000")
_DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_UP)
_DIGEST_RE = re.compile(r"^[0-9a-f]{64}$")
_DIGEST_REFERENCE_RE = re.compile(r"^sha256:[0-9a-f]{64}$")
_PUBLIC_IDENTIFIER_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,127}$")
_PUBLIC_DECIMAL_RE = re.compile(r"^(?:0|[1-9][0-9]*)\.[0-9]{6}$")
_UNSAFE_TOKEN_RE = re.compile(r"[a-z0-9]+")
_UNSAFE_IDENTIFIER_TOKENS = frozenset(
    (
        "auth",
        "buy",
        "database",
        "dsn",
        "execution",
        "file",
        "live",
        "network",
        "order",
        "path",
        "persist",
        "position",
        "recommendation",
        "sell",
        "sizing",
        "token",
        "trade",
        "trading",
        "url",
        "wallet",
    ),
)
_STATUSES = ("empty", "low", "moderate", "high")
_REVIEW_PRIORITIES = ("low", "medium", "high")
_BUCKET_SEQUENCE = (
    "source_freshness",
    "authority_disagreement",
    "specialist_divergence",
    "resolution_ambiguity",
    "unattributed",
)
_REASON_CODE_SEQUENCE = (
    "empty_forecast_error_observations",
    "forecast_error_zero",
    "forecast_error_present",
    "source_freshness_pressure",
    "source_freshness_pressure_high",
    "authority_disagreement_pressure",
    "authority_disagreement_pressure_high",
    "specialist_divergence_pressure",
    "specialist_divergence_pressure_high",
    "resolution_ambiguity_pressure",
    "resolution_ambiguity_pressure_high",
    "source_freshness_attribution",
    "authority_disagreement_attribution",
    "specialist_divergence_attribution",
    "resolution_ambiguity_attribution",
    "forecast_error_unattributed",
    "forecast_error_attribution_low",
    "forecast_error_attribution_moderate",
    "forecast_error_attribution_high",
    "forecast_error_attribution_report_low",
    "forecast_error_attribution_report_moderate",
    "forecast_error_attribution_report_high",
    "long_term_learning_low",
    "long_term_learning_moderate",
    "long_term_learning_high",
    "human_review_priority_low",
    "human_review_priority_medium",
    "human_review_priority_high",
)
_PHASE_FLAG_FIELDS = ("paper_only", "report_only", "readonly")
_REPORT_PAYLOAD_KEYS = (
    "generated_at",
    "config_version",
    "status",
    "observation_count",
    "domain_count",
    "low_count",
    "moderate_count",
    "high_count",
    "high_review_priority_count",
    "medium_review_priority_count",
    "low_review_priority_count",
    "average_attribution_score",
    "max_attribution_score",
    "average_long_term_learning_score",
    "max_long_term_learning_score",
    "average_human_review_priority_score",
    "max_human_review_priority_score",
    "rows",
    "attribution_buckets",
    "reason_codes",
    "derived_validation_digest",
    "paper_only",
    "report_only",
    "readonly",
)
_ROW_PAYLOAD_KEYS = (
    "rank",
    "domain_key",
    "observation_count",
    "observation_digests",
    "team_count",
    "team_digests",
    "source_count",
    "source_digests",
    "average_absolute_forecast_error",
    "source_staleness_score",
    "authority_disagreement_score",
    "specialist_divergence_score",
    "resolution_ambiguity_score",
    "source_freshness_attribution_score",
    "authority_disagreement_attribution_score",
    "specialist_divergence_attribution_score",
    "resolution_ambiguity_attribution_score",
    "attribution_score",
    "long_term_learning_score",
    "human_review_priority_score",
    "human_review_priority",
    "dominant_attribution_bucket",
    "status",
    "reason_codes",
    "paper_only",
    "report_only",
    "readonly",
)
_BUCKET_PAYLOAD_KEYS = (
    "bucket_code",
    "domain_count",
    "observation_count",
    "average_attribution_score",
    "paper_only",
    "report_only",
    "readonly",
)


@dataclass(frozen=True)
class ResearchStrategyDomainForecastErrorAttributionConfig:
    config_version: str = (
        DEFAULT_RESEARCH_STRATEGY_DOMAIN_FORECAST_ERROR_ATTRIBUTION_CONFIG_VERSION
    )
    source_freshness_weight: Decimal = _FACTOR_WEIGHT
    authority_disagreement_weight: Decimal = _FACTOR_WEIGHT
    specialist_divergence_weight: Decimal = _FACTOR_WEIGHT
    resolution_ambiguity_weight: Decimal = _FACTOR_WEIGHT
    moderate_attribution_threshold: Decimal = _MODERATE_ATTRIBUTION_THRESHOLD
    high_attribution_threshold: Decimal = _HIGH_ATTRIBUTION_THRESHOLD
    high_factor_pressure_threshold: Decimal = _HIGH_FACTOR_PRESSURE_THRESHOLD
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchStrategyDomainForecastErrorAttributionConfig "
            "does not support subclassing",
        )

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchStrategyDomainForecastErrorAttributionConfig,
            "config",
        )
        _require_public_identifier("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_STRATEGY_DOMAIN_FORECAST_ERROR_ATTRIBUTION_CONFIG_VERSION
        ):
            raise ValueError("config_version must be supported")
        for field_name in (
            "source_freshness_weight",
            "authority_disagreement_weight",
            "specialist_divergence_weight",
            "resolution_ambiguity_weight",
            "moderate_attribution_threshold",
            "high_attribution_threshold",
            "high_factor_pressure_threshold",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio(field_name, getattr(self, field_name)),
            )
        if self.high_attribution_threshold <= self.moderate_attribution_threshold:
            raise ValueError(
                "high_attribution_threshold must exceed "
                "moderate_attribution_threshold",
            )
        weights = _sum_decimals(
            (
                self.source_freshness_weight,
                self.authority_disagreement_weight,
                self.specialist_divergence_weight,
                self.resolution_ambiguity_weight,
            ),
        )
        if weights != _ONE:
            raise ValueError("factor weights must sum to one")
        supported_values = {
            "source_freshness_weight": _FACTOR_WEIGHT,
            "authority_disagreement_weight": _FACTOR_WEIGHT,
            "specialist_divergence_weight": _FACTOR_WEIGHT,
            "resolution_ambiguity_weight": _FACTOR_WEIGHT,
            "moderate_attribution_threshold": _MODERATE_ATTRIBUTION_THRESHOLD,
            "high_attribution_threshold": _HIGH_ATTRIBUTION_THRESHOLD,
            "high_factor_pressure_threshold": _HIGH_FACTOR_PRESSURE_THRESHOLD,
        }
        for field_name, supported_value in supported_values.items():
            if getattr(self, field_name) != supported_value:
                raise ValueError(f"{field_name} must use the supported value")
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class ResearchStrategyDomainForecastErrorObservation:
    observation_digest: str
    domain_key: str
    observed_at: datetime
    absolute_forecast_error: Decimal
    source_freshness_score: Decimal
    authority_disagreement_score: Decimal
    specialist_divergence_score: Decimal
    resolution_ambiguity_score: Decimal
    team_identifier: str = "private-team-unspecified"
    source_identifiers: tuple[str, ...] = ("private-source-unspecified",)
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchStrategyDomainForecastErrorObservation "
            "does not support subclassing",
        )

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchStrategyDomainForecastErrorObservation,
            "observation",
        )
        _require_digest("observation_digest", self.observation_digest)
        _require_safe_identifier("domain_key", self.domain_key)
        _require_private_identifier("team_identifier", self.team_identifier)
        object.__setattr__(
            self,
            "source_identifiers",
            _normalize_private_identifiers(
                "source_identifiers",
                self.source_identifiers,
            ),
        )
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in (
            "absolute_forecast_error",
            "source_freshness_score",
            "authority_disagreement_score",
            "specialist_divergence_score",
            "resolution_ambiguity_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio(field_name, getattr(self, field_name)),
            )
        _require_hard_flags("observation", self)


@dataclass(frozen=True)
class ResearchStrategyDomainForecastErrorAttributionRow:
    rank: Decimal
    domain_key: str
    observation_count: Decimal
    observation_digests: tuple[str, ...]
    team_count: Decimal
    team_digests: tuple[str, ...]
    source_count: Decimal
    source_digests: tuple[str, ...]
    average_absolute_forecast_error: Decimal
    source_staleness_score: Decimal
    authority_disagreement_score: Decimal
    specialist_divergence_score: Decimal
    resolution_ambiguity_score: Decimal
    source_freshness_attribution_score: Decimal
    authority_disagreement_attribution_score: Decimal
    specialist_divergence_attribution_score: Decimal
    resolution_ambiguity_attribution_score: Decimal
    attribution_score: Decimal
    long_term_learning_score: Decimal
    human_review_priority_score: Decimal
    human_review_priority: str
    dominant_attribution_bucket: str
    status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchStrategyDomainForecastErrorAttributionRow "
            "does not support subclassing",
        )

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchStrategyDomainForecastErrorAttributionRow,
            "row",
        )
        object.__setattr__(self, "rank", _require_positive_count("rank", self.rank))
        _require_safe_identifier("domain_key", self.domain_key)
        object.__setattr__(
            self,
            "observation_count",
            _require_positive_count("observation_count", self.observation_count),
        )
        object.__setattr__(
            self,
            "observation_digests",
            _normalize_digests("observation_digests", self.observation_digests),
        )
        object.__setattr__(
            self,
            "team_count",
            _require_positive_count("team_count", self.team_count),
        )
        object.__setattr__(
            self,
            "team_digests",
            _normalize_digest_references("team_digests", self.team_digests),
        )
        object.__setattr__(
            self,
            "source_count",
            _require_positive_count("source_count", self.source_count),
        )
        object.__setattr__(
            self,
            "source_digests",
            _normalize_digest_references("source_digests", self.source_digests),
        )
        for field_name in (
            "average_absolute_forecast_error",
            "source_staleness_score",
            "authority_disagreement_score",
            "specialist_divergence_score",
            "resolution_ambiguity_score",
            "source_freshness_attribution_score",
            "authority_disagreement_attribution_score",
            "specialist_divergence_attribution_score",
            "resolution_ambiguity_attribution_score",
            "attribution_score",
            "long_term_learning_score",
            "human_review_priority_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio(field_name, getattr(self, field_name)),
            )
        _require_member(
            "human_review_priority",
            self.human_review_priority,
            _REVIEW_PRIORITIES,
        )
        _require_member(
            "dominant_attribution_bucket",
            self.dominant_attribution_bucket,
            _BUCKET_SEQUENCE,
        )
        _require_member("status", self.status, _STATUSES[1:])
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes),
        )
        _validate_row_consistency(self)
        _require_hard_flags("row", self)


@dataclass(frozen=True)
class ResearchStrategyDomainForecastErrorAttributionBucket:
    bucket_code: str
    domain_count: Decimal
    observation_count: Decimal
    average_attribution_score: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchStrategyDomainForecastErrorAttributionBucket "
            "does not support subclassing",
        )

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchStrategyDomainForecastErrorAttributionBucket,
            "bucket",
        )
        _require_member("bucket_code", self.bucket_code, _BUCKET_SEQUENCE)
        for field_name in ("domain_count", "observation_count"):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_count(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "average_attribution_score",
            _require_ratio(
                "average_attribution_score",
                self.average_attribution_score,
            ),
        )
        _require_hard_flags("bucket", self)


@dataclass(frozen=True)
class ResearchStrategyDomainForecastErrorAttributionReport:
    generated_at: datetime
    config_version: str
    status: str
    observation_count: Decimal
    domain_count: Decimal
    low_count: Decimal
    moderate_count: Decimal
    high_count: Decimal
    high_review_priority_count: Decimal
    medium_review_priority_count: Decimal
    low_review_priority_count: Decimal
    average_attribution_score: Decimal
    max_attribution_score: Decimal
    average_long_term_learning_score: Decimal
    max_long_term_learning_score: Decimal
    average_human_review_priority_score: Decimal
    max_human_review_priority_score: Decimal
    rows: tuple[ResearchStrategyDomainForecastErrorAttributionRow, ...]
    attribution_buckets: tuple[
        ResearchStrategyDomainForecastErrorAttributionBucket,
        ...,
    ]
    reason_codes: tuple[str, ...]
    derived_validation_digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchStrategyDomainForecastErrorAttributionReport "
            "does not support subclassing",
        )

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchStrategyDomainForecastErrorAttributionReport,
            "report",
        )
        object.__setattr__(
            self,
            "generated_at",
            _as_utc("generated_at", self.generated_at),
        )
        _require_public_identifier("config_version", self.config_version)
        _require_member("status", self.status, _STATUSES)
        for field_name in (
            "observation_count",
            "domain_count",
            "low_count",
            "moderate_count",
            "high_count",
            "high_review_priority_count",
            "medium_review_priority_count",
            "low_review_priority_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_count(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "average_attribution_score",
            "max_attribution_score",
            "average_long_term_learning_score",
            "max_long_term_learning_score",
            "average_human_review_priority_score",
            "max_human_review_priority_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio(field_name, getattr(self, field_name)),
            )
        if type(self.rows) is not tuple:
            raise ValueError("rows must be a tuple")
        for row in self.rows:
            if type(row) is not ResearchStrategyDomainForecastErrorAttributionRow:
                raise ValueError(
                    "rows must contain "
                    "ResearchStrategyDomainForecastErrorAttributionRow",
                )
        if type(self.attribution_buckets) is not tuple:
            raise ValueError("attribution_buckets must be a tuple")
        for bucket in self.attribution_buckets:
            if type(bucket) is not ResearchStrategyDomainForecastErrorAttributionBucket:
                raise ValueError(
                    "attribution_buckets must contain "
                    "ResearchStrategyDomainForecastErrorAttributionBucket",
                )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes),
        )
        _require_digest(
            "derived_validation_digest",
            self.derived_validation_digest,
        )
        _validate_report_consistency(self)
        _require_hard_flags("report", self)
        expected_digest = _report_digest_from_values(
            _report_values_without_digest(self),
        )
        if self.derived_validation_digest != expected_digest:
            raise ValueError(
                "derived_validation_digest does not match report payload",
            )

    @property
    def payload(self) -> dict[str, Any]:
        _validate_report_consistency(self)
        expected_digest = _report_digest_from_values(
            _report_values_without_digest(self),
        )
        if self.derived_validation_digest != expected_digest:
            raise ValueError(
                "derived_validation_digest does not match report payload",
            )
        payload = _json_ready(asdict(self))
        if type(payload) is not dict:
            raise ValueError("payload must be a dict")
        return payload


def build_research_strategy_domain_forecast_error_attribution_report(
    observations: Sequence[ResearchStrategyDomainForecastErrorObservation],
    *,
    generated_at: datetime,
    config: ResearchStrategyDomainForecastErrorAttributionConfig | None = None,
) -> ResearchStrategyDomainForecastErrorAttributionReport:
    """Reduce supplied observations into deterministic diagnostic attributions."""

    if config is None:
        config = ResearchStrategyDomainForecastErrorAttributionConfig()
    if type(config) is not ResearchStrategyDomainForecastErrorAttributionConfig:
        raise ValueError(
            "config must be a ResearchStrategyDomainForecastErrorAttributionConfig",
        )
    _require_config_integrity(config)
    generated_at = _as_utc("generated_at", generated_at)
    normalized = _normalize_observations(observations)
    for observation in normalized:
        if observation.observed_at > generated_at:
            raise ValueError("observed_at must not be after generated_at")

    grouped: dict[str, list[ResearchStrategyDomainForecastErrorObservation]] = {}
    for observation in normalized:
        grouped.setdefault(observation.domain_key, []).append(observation)

    row_values = [
        _domain_row_values(domain_key, tuple(items), config)
        for domain_key, items in sorted(grouped.items())
    ]
    row_values.sort(
        key=_row_values_sort_key,
    )
    rows = tuple(
        ResearchStrategyDomainForecastErrorAttributionRow(
            rank=_count(index),
            **values,
        )
        for index, values in enumerate(row_values, start=1)
    )
    status = _report_status(rows)
    reason_codes = _report_reason_codes(rows, status)
    values: dict[str, object] = {
        "generated_at": generated_at,
        "config_version": config.config_version,
        "status": status,
        "observation_count": _count(len(normalized)),
        "domain_count": _count(len(rows)),
        "low_count": _count(_status_count(rows, "low")),
        "moderate_count": _count(_status_count(rows, "moderate")),
        "high_count": _count(_status_count(rows, "high")),
        "high_review_priority_count": _count(
            _review_priority_count(rows, "high"),
        ),
        "medium_review_priority_count": _count(
            _review_priority_count(rows, "medium"),
        ),
        "low_review_priority_count": _count(
            _review_priority_count(rows, "low"),
        ),
        "average_attribution_score": _average(
            tuple(row.attribution_score for row in rows),
        ),
        "max_attribution_score": max(
            (row.attribution_score for row in rows),
            default=_ZERO,
        ),
        "average_long_term_learning_score": _average(
            tuple(row.long_term_learning_score for row in rows),
        ),
        "max_long_term_learning_score": max(
            (row.long_term_learning_score for row in rows),
            default=_ZERO,
        ),
        "average_human_review_priority_score": _average(
            tuple(row.human_review_priority_score for row in rows),
        ),
        "max_human_review_priority_score": max(
            (row.human_review_priority_score for row in rows),
            default=_ZERO,
        ),
        "rows": rows,
        "attribution_buckets": _build_buckets(rows),
        "reason_codes": reason_codes,
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    return ResearchStrategyDomainForecastErrorAttributionReport(
        **values,
        derived_validation_digest=_report_digest_from_values(values),
    )


def research_strategy_domain_forecast_error_attribution_report_payload(
    report: ResearchStrategyDomainForecastErrorAttributionReport,
) -> dict[str, Any]:
    """Return the validated canonical public payload for a report."""

    if type(report) is not ResearchStrategyDomainForecastErrorAttributionReport:
        raise ValueError(
            "report must be exactly "
            "ResearchStrategyDomainForecastErrorAttributionReport",
        )
    _require_hard_flags("report", report)
    payload = report.payload
    _report_from_public_payload(payload)
    return payload


def validate_research_strategy_domain_forecast_error_attribution_report_payload(
    payload: dict[str, Any],
) -> bool:
    """Validate an exact canonical public report payload."""

    _report_from_public_payload(payload)
    return True


def _domain_row_values(
    domain_key: str,
    observations: tuple[ResearchStrategyDomainForecastErrorObservation, ...],
    config: ResearchStrategyDomainForecastErrorAttributionConfig,
) -> dict[str, object]:
    average_error = _average(
        tuple(item.absolute_forecast_error for item in observations),
    )
    source_staleness = _difference(
        _ONE,
        _average(tuple(item.source_freshness_score for item in observations)),
    )
    authority_disagreement = _average(
        tuple(item.authority_disagreement_score for item in observations),
    )
    specialist_divergence = _average(
        tuple(item.specialist_divergence_score for item in observations),
    )
    resolution_ambiguity = _average(
        tuple(item.resolution_ambiguity_score for item in observations),
    )
    contributions = {
        "source_freshness": _product(
            average_error,
            source_staleness,
            config.source_freshness_weight,
        ),
        "authority_disagreement": _product(
            average_error,
            authority_disagreement,
            config.authority_disagreement_weight,
        ),
        "specialist_divergence": _product(
            average_error,
            specialist_divergence,
            config.specialist_divergence_weight,
        ),
        "resolution_ambiguity": _product(
            average_error,
            resolution_ambiguity,
            config.resolution_ambiguity_weight,
        ),
    }
    score = _sum_decimals(tuple(contributions.values()))
    long_term_learning_score = _average(
        (
            average_error,
            authority_disagreement,
            specialist_divergence,
            resolution_ambiguity,
        ),
    )
    human_review_priority_score = _average(
        (
            score,
            long_term_learning_score,
            source_staleness,
        ),
    )
    human_review_priority = _human_review_priority(
        human_review_priority_score,
    )
    bucket = _dominant_bucket(contributions, score)
    status = _attribution_status(score, config)
    observation_digests = tuple(
        sorted(item.observation_digest for item in observations),
    )
    team_digests = tuple(
        sorted(
            {
                _private_digest("team", item.team_identifier)
                for item in observations
            },
        ),
    )
    source_digests = tuple(
        sorted(
            {
                _private_digest("source", identifier)
                for item in observations
                for identifier in item.source_identifiers
            },
        ),
    )
    return {
        "domain_key": domain_key,
        "observation_count": _count(len(observation_digests)),
        "observation_digests": observation_digests,
        "team_count": _count(len(team_digests)),
        "team_digests": team_digests,
        "source_count": _count(len(source_digests)),
        "source_digests": source_digests,
        "average_absolute_forecast_error": average_error,
        "source_staleness_score": source_staleness,
        "authority_disagreement_score": authority_disagreement,
        "specialist_divergence_score": specialist_divergence,
        "resolution_ambiguity_score": resolution_ambiguity,
        "source_freshness_attribution_score": contributions["source_freshness"],
        "authority_disagreement_attribution_score": contributions[
            "authority_disagreement"
        ],
        "specialist_divergence_attribution_score": contributions[
            "specialist_divergence"
        ],
        "resolution_ambiguity_attribution_score": contributions[
            "resolution_ambiguity"
        ],
        "attribution_score": score,
        "long_term_learning_score": long_term_learning_score,
        "human_review_priority_score": human_review_priority_score,
        "human_review_priority": human_review_priority,
        "dominant_attribution_bucket": bucket,
        "status": status,
        "reason_codes": _row_reason_codes(
            average_error=average_error,
            source_staleness=source_staleness,
            authority_disagreement=authority_disagreement,
            specialist_divergence=specialist_divergence,
            resolution_ambiguity=resolution_ambiguity,
            bucket=bucket,
            status=status,
            long_term_learning_score=long_term_learning_score,
            human_review_priority=human_review_priority,
            config=config,
        ),
    }


def _dominant_bucket(
    contributions: dict[str, Decimal],
    score: Decimal,
) -> str:
    if score == _ZERO:
        return "unattributed"
    return max(
        _BUCKET_SEQUENCE[:-1],
        key=lambda bucket: (
            contributions[bucket],
            -_BUCKET_SEQUENCE.index(bucket),
        ),
    )


def _attribution_status(
    score: Decimal,
    config: ResearchStrategyDomainForecastErrorAttributionConfig,
) -> str:
    if score >= config.high_attribution_threshold:
        return "high"
    if score >= config.moderate_attribution_threshold:
        return "moderate"
    return "low"


def _long_term_learning_status(score: Decimal) -> str:
    if score >= _HIGH_ATTRIBUTION_THRESHOLD:
        return "high"
    if score >= _MODERATE_ATTRIBUTION_THRESHOLD:
        return "moderate"
    return "low"


def _human_review_priority(score: Decimal) -> str:
    if score >= _HIGH_REVIEW_PRIORITY_THRESHOLD:
        return "high"
    if score >= _MEDIUM_REVIEW_PRIORITY_THRESHOLD:
        return "medium"
    return "low"


def _row_reason_codes(
    *,
    average_error: Decimal,
    source_staleness: Decimal,
    authority_disagreement: Decimal,
    specialist_divergence: Decimal,
    resolution_ambiguity: Decimal,
    bucket: str,
    status: str,
    long_term_learning_score: Decimal,
    human_review_priority: str,
    config: ResearchStrategyDomainForecastErrorAttributionConfig,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    reason_codes.append(
        "forecast_error_zero" if average_error == _ZERO else "forecast_error_present",
    )
    pressures = (
        ("source_freshness", source_staleness),
        ("authority_disagreement", authority_disagreement),
        ("specialist_divergence", specialist_divergence),
        ("resolution_ambiguity", resolution_ambiguity),
    )
    for factor, pressure in pressures:
        if pressure > _ZERO:
            reason_codes.append(f"{factor}_pressure")
        if pressure >= config.high_factor_pressure_threshold:
            reason_codes.append(f"{factor}_pressure_high")
    if bucket == "unattributed":
        reason_codes.append("forecast_error_unattributed")
    else:
        reason_codes.append(f"{bucket}_attribution")
    reason_codes.append(f"forecast_error_attribution_{status}")
    reason_codes.append(
        f"long_term_learning_{_long_term_learning_status(long_term_learning_score)}",
    )
    reason_codes.append(f"human_review_priority_{human_review_priority}")
    return _normalize_reason_codes(tuple(reason_codes))


def _row_values_sort_key(
    values: Mapping[str, object],
) -> tuple[Decimal, Decimal, Decimal, str, tuple[str, ...], tuple[str, ...], tuple[str, ...]]:
    return (
        _descending_ratio_sort_key(
            "human_review_priority_score",
            values["human_review_priority_score"],
        ),
        _descending_ratio_sort_key(
            "attribution_score",
            values["attribution_score"],
        ),
        _descending_ratio_sort_key(
            "long_term_learning_score",
            values["long_term_learning_score"],
        ),
        _require_sort_string("domain_key", values["domain_key"]),
        _require_sort_tuple("team_digests", values["team_digests"]),
        _require_sort_tuple("source_digests", values["source_digests"]),
        _require_sort_tuple("observation_digests", values["observation_digests"]),
    )


def _row_sort_key(
    row: ResearchStrategyDomainForecastErrorAttributionRow,
) -> tuple[Decimal, Decimal, Decimal, str, tuple[str, ...], tuple[str, ...], tuple[str, ...]]:
    return (
        _descending_ratio_sort_key(
            "human_review_priority_score",
            row.human_review_priority_score,
        ),
        _descending_ratio_sort_key("attribution_score", row.attribution_score),
        _descending_ratio_sort_key(
            "long_term_learning_score",
            row.long_term_learning_score,
        ),
        row.domain_key,
        row.team_digests,
        row.source_digests,
        row.observation_digests,
    )


def _report_status(
    rows: tuple[ResearchStrategyDomainForecastErrorAttributionRow, ...],
) -> str:
    if not rows:
        return "empty"
    if any(row.status == "high" for row in rows):
        return "high"
    if any(row.status == "moderate" for row in rows):
        return "moderate"
    return "low"


def _report_reason_codes(
    rows: tuple[ResearchStrategyDomainForecastErrorAttributionRow, ...],
    status: str,
) -> tuple[str, ...]:
    if not rows:
        return ("empty_forecast_error_observations",)
    reason_codes: list[str] = []
    for row in rows:
        reason_codes.extend(row.reason_codes)
    reason_codes.append(f"forecast_error_attribution_report_{status}")
    return _canonical_reason_codes(reason_codes)


def _build_buckets(
    rows: tuple[ResearchStrategyDomainForecastErrorAttributionRow, ...],
) -> tuple[ResearchStrategyDomainForecastErrorAttributionBucket, ...]:
    buckets: list[ResearchStrategyDomainForecastErrorAttributionBucket] = []
    for bucket_code in _BUCKET_SEQUENCE:
        bucket_rows = tuple(
            row
            for row in rows
            if row.dominant_attribution_bucket == bucket_code
        )
        buckets.append(
            ResearchStrategyDomainForecastErrorAttributionBucket(
                bucket_code=bucket_code,
                domain_count=_count(len(bucket_rows)),
                observation_count=_sum_decimals(
                    tuple(row.observation_count for row in bucket_rows),
                ),
                average_attribution_score=_average(
                    tuple(row.attribution_score for row in bucket_rows),
                ),
            ),
        )
    return tuple(buckets)


def _validate_row_consistency(
    row: ResearchStrategyDomainForecastErrorAttributionRow,
) -> None:
    config = ResearchStrategyDomainForecastErrorAttributionConfig()
    if row.observation_count != _count(len(row.observation_digests)):
        raise ValueError("observation_count must match observation_digests")
    if row.team_count != _count(len(row.team_digests)):
        raise ValueError("team_count must match team_digests")
    if row.source_count != _count(len(row.source_digests)):
        raise ValueError("source_count must match source_digests")
    expected_contributions = {
        "source_freshness": _product(
            row.average_absolute_forecast_error,
            row.source_staleness_score,
            config.source_freshness_weight,
        ),
        "authority_disagreement": _product(
            row.average_absolute_forecast_error,
            row.authority_disagreement_score,
            config.authority_disagreement_weight,
        ),
        "specialist_divergence": _product(
            row.average_absolute_forecast_error,
            row.specialist_divergence_score,
            config.specialist_divergence_weight,
        ),
        "resolution_ambiguity": _product(
            row.average_absolute_forecast_error,
            row.resolution_ambiguity_score,
            config.resolution_ambiguity_weight,
        ),
    }
    actual_contributions = {
        "source_freshness": row.source_freshness_attribution_score,
        "authority_disagreement": row.authority_disagreement_attribution_score,
        "specialist_divergence": row.specialist_divergence_attribution_score,
        "resolution_ambiguity": row.resolution_ambiguity_attribution_score,
    }
    for bucket_code in _BUCKET_SEQUENCE[:-1]:
        if actual_contributions[bucket_code] != expected_contributions[bucket_code]:
            raise ValueError(
                f"{bucket_code}_attribution_score must match factor inputs",
            )
    expected_score = _sum_decimals(tuple(expected_contributions.values()))
    if row.attribution_score != expected_score:
        raise ValueError("attribution_score must match factor attribution scores")
    expected_learning_score = _average(
        (
            row.average_absolute_forecast_error,
            row.authority_disagreement_score,
            row.specialist_divergence_score,
            row.resolution_ambiguity_score,
        ),
    )
    if row.long_term_learning_score != expected_learning_score:
        raise ValueError("long_term_learning_score must match factor inputs")
    expected_review_score = _average(
        (
            expected_score,
            expected_learning_score,
            row.source_staleness_score,
        ),
    )
    if row.human_review_priority_score != expected_review_score:
        raise ValueError(
            "human_review_priority_score must match derived fields",
        )
    expected_review_priority = _human_review_priority(expected_review_score)
    if row.human_review_priority != expected_review_priority:
        raise ValueError(
            "human_review_priority must match human_review_priority_score",
        )
    expected_bucket = _dominant_bucket(expected_contributions, expected_score)
    if row.dominant_attribution_bucket != expected_bucket:
        raise ValueError(
            "dominant_attribution_bucket must match factor attribution scores",
        )
    expected_status = _attribution_status(expected_score, config)
    if row.status != expected_status:
        raise ValueError("status must match attribution_score")
    expected_reasons = _row_reason_codes(
        average_error=row.average_absolute_forecast_error,
        source_staleness=row.source_staleness_score,
        authority_disagreement=row.authority_disagreement_score,
        specialist_divergence=row.specialist_divergence_score,
        resolution_ambiguity=row.resolution_ambiguity_score,
        bucket=expected_bucket,
        status=expected_status,
        long_term_learning_score=expected_learning_score,
        human_review_priority=expected_review_priority,
        config=config,
    )
    if row.reason_codes != expected_reasons:
        raise ValueError("reason_codes must match row attribution factors")


def _validate_report_consistency(
    report: ResearchStrategyDomainForecastErrorAttributionReport,
) -> None:
    _require_report_runtime_schema(report)
    if len({row.domain_key for row in report.rows}) != len(report.rows):
        raise ValueError("rows must have unique domain_key values")
    seen_observation_digests: set[str] = set()
    for row in report.rows:
        _validate_row_consistency(row)
        if seen_observation_digests.intersection(row.observation_digests):
            raise ValueError(
                "observation_digests must be unique across rows",
            )
        seen_observation_digests.update(row.observation_digests)
    expected_sequence = tuple(sorted(report.rows, key=_row_sort_key))
    if report.rows != expected_sequence:
        raise ValueError("rows must use deterministic sequence")
    for index, row in enumerate(report.rows, start=1):
        if row.rank != _count(index):
            raise ValueError("row rank must match deterministic sequence")
    expected_observation_count = _sum_decimals(
        tuple(row.observation_count for row in report.rows),
    )
    if report.observation_count != expected_observation_count:
        raise ValueError("observation_count must match rows")
    if report.domain_count != _count(len(report.rows)):
        raise ValueError("domain_count must match rows")
    if report.low_count != _count(_status_count(report.rows, "low")):
        raise ValueError("low_count must match rows")
    if report.moderate_count != _count(_status_count(report.rows, "moderate")):
        raise ValueError("moderate_count must match rows")
    if report.high_count != _count(_status_count(report.rows, "high")):
        raise ValueError("high_count must match rows")
    for field_name, priority in (
        ("high_review_priority_count", "high"),
        ("medium_review_priority_count", "medium"),
        ("low_review_priority_count", "low"),
    ):
        if getattr(report, field_name) != _count(
            _review_priority_count(report.rows, priority),
        ):
            raise ValueError(f"{field_name} must match rows")
    expected_average = _average(
        tuple(row.attribution_score for row in report.rows),
    )
    if report.average_attribution_score != expected_average:
        raise ValueError("average_attribution_score must match rows")
    expected_maximum = max(
        (row.attribution_score for row in report.rows),
        default=_ZERO,
    )
    if report.max_attribution_score != expected_maximum:
        raise ValueError("max_attribution_score must match rows")
    expected_average_learning = _average(
        tuple(row.long_term_learning_score for row in report.rows),
    )
    if report.average_long_term_learning_score != expected_average_learning:
        raise ValueError("average_long_term_learning_score must match rows")
    expected_max_learning = max(
        (row.long_term_learning_score for row in report.rows),
        default=_ZERO,
    )
    if report.max_long_term_learning_score != expected_max_learning:
        raise ValueError("max_long_term_learning_score must match rows")
    expected_average_review = _average(
        tuple(row.human_review_priority_score for row in report.rows),
    )
    if report.average_human_review_priority_score != expected_average_review:
        raise ValueError(
            "average_human_review_priority_score must match rows",
        )
    expected_max_review = max(
        (row.human_review_priority_score for row in report.rows),
        default=_ZERO,
    )
    if report.max_human_review_priority_score != expected_max_review:
        raise ValueError("max_human_review_priority_score must match rows")
    expected_status = _report_status(report.rows)
    if report.status != expected_status:
        raise ValueError("status must match row statuses")
    expected_buckets = _build_buckets(report.rows)
    if report.attribution_buckets != expected_buckets:
        raise ValueError("attribution_buckets must match rows")
    expected_reasons = _report_reason_codes(report.rows, expected_status)
    if report.reason_codes != expected_reasons:
        raise ValueError("reason_codes must match rows")


def _report_from_public_payload(
    payload: object,
) -> ResearchStrategyDomainForecastErrorAttributionReport:
    if type(payload) is not dict:
        raise ValueError("public payload must be a dict")
    _require_public_payload_shape(payload)
    _require_payload_flags("payload", payload)
    report = ResearchStrategyDomainForecastErrorAttributionReport(
        generated_at=_public_datetime("generated_at", payload["generated_at"]),
        config_version=_public_string(
            "config_version",
            payload["config_version"],
        ),
        status=_public_member("status", payload["status"], _STATUSES),
        observation_count=_public_count(
            "observation_count",
            payload["observation_count"],
        ),
        domain_count=_public_count("domain_count", payload["domain_count"]),
        low_count=_public_count("low_count", payload["low_count"]),
        moderate_count=_public_count(
            "moderate_count",
            payload["moderate_count"],
        ),
        high_count=_public_count("high_count", payload["high_count"]),
        high_review_priority_count=_public_count(
            "high_review_priority_count",
            payload["high_review_priority_count"],
        ),
        medium_review_priority_count=_public_count(
            "medium_review_priority_count",
            payload["medium_review_priority_count"],
        ),
        low_review_priority_count=_public_count(
            "low_review_priority_count",
            payload["low_review_priority_count"],
        ),
        average_attribution_score=_public_ratio(
            "average_attribution_score",
            payload["average_attribution_score"],
        ),
        max_attribution_score=_public_ratio(
            "max_attribution_score",
            payload["max_attribution_score"],
        ),
        average_long_term_learning_score=_public_ratio(
            "average_long_term_learning_score",
            payload["average_long_term_learning_score"],
        ),
        max_long_term_learning_score=_public_ratio(
            "max_long_term_learning_score",
            payload["max_long_term_learning_score"],
        ),
        average_human_review_priority_score=_public_ratio(
            "average_human_review_priority_score",
            payload["average_human_review_priority_score"],
        ),
        max_human_review_priority_score=_public_ratio(
            "max_human_review_priority_score",
            payload["max_human_review_priority_score"],
        ),
        rows=tuple(
            _row_from_public_payload(row)
            for row in payload["rows"]
        ),
        attribution_buckets=tuple(
            _bucket_from_public_payload(bucket)
            for bucket in payload["attribution_buckets"]
        ),
        reason_codes=_public_reason_codes(
            "reason_codes",
            payload["reason_codes"],
        ),
        derived_validation_digest=_public_digest(
            "derived_validation_digest",
            payload["derived_validation_digest"],
        ),
        paper_only=payload["paper_only"],
        report_only=payload["report_only"],
        readonly=payload["readonly"],
    )
    if report.payload != payload:
        raise ValueError("public payload must use canonical ordering and values")
    return report


def _row_from_public_payload(
    payload: dict[str, Any],
) -> ResearchStrategyDomainForecastErrorAttributionRow:
    _require_payload_flags("payload row", payload)
    return ResearchStrategyDomainForecastErrorAttributionRow(
        rank=_public_positive_count("rank", payload["rank"]),
        domain_key=_public_string("domain_key", payload["domain_key"]),
        observation_count=_public_positive_count(
            "observation_count",
            payload["observation_count"],
        ),
        observation_digests=_public_digest_list(
            "observation_digests",
            payload["observation_digests"],
        ),
        team_count=_public_positive_count(
            "team_count",
            payload["team_count"],
        ),
        team_digests=_public_digest_reference_list(
            "team_digests",
            payload["team_digests"],
        ),
        source_count=_public_positive_count(
            "source_count",
            payload["source_count"],
        ),
        source_digests=_public_digest_reference_list(
            "source_digests",
            payload["source_digests"],
        ),
        average_absolute_forecast_error=_public_ratio(
            "average_absolute_forecast_error",
            payload["average_absolute_forecast_error"],
        ),
        source_staleness_score=_public_ratio(
            "source_staleness_score",
            payload["source_staleness_score"],
        ),
        authority_disagreement_score=_public_ratio(
            "authority_disagreement_score",
            payload["authority_disagreement_score"],
        ),
        specialist_divergence_score=_public_ratio(
            "specialist_divergence_score",
            payload["specialist_divergence_score"],
        ),
        resolution_ambiguity_score=_public_ratio(
            "resolution_ambiguity_score",
            payload["resolution_ambiguity_score"],
        ),
        source_freshness_attribution_score=_public_ratio(
            "source_freshness_attribution_score",
            payload["source_freshness_attribution_score"],
        ),
        authority_disagreement_attribution_score=_public_ratio(
            "authority_disagreement_attribution_score",
            payload["authority_disagreement_attribution_score"],
        ),
        specialist_divergence_attribution_score=_public_ratio(
            "specialist_divergence_attribution_score",
            payload["specialist_divergence_attribution_score"],
        ),
        resolution_ambiguity_attribution_score=_public_ratio(
            "resolution_ambiguity_attribution_score",
            payload["resolution_ambiguity_attribution_score"],
        ),
        attribution_score=_public_ratio(
            "attribution_score",
            payload["attribution_score"],
        ),
        long_term_learning_score=_public_ratio(
            "long_term_learning_score",
            payload["long_term_learning_score"],
        ),
        human_review_priority_score=_public_ratio(
            "human_review_priority_score",
            payload["human_review_priority_score"],
        ),
        human_review_priority=_public_member(
            "human_review_priority",
            payload["human_review_priority"],
            _REVIEW_PRIORITIES,
        ),
        dominant_attribution_bucket=_public_member(
            "dominant_attribution_bucket",
            payload["dominant_attribution_bucket"],
            _BUCKET_SEQUENCE,
        ),
        status=_public_member("status", payload["status"], _STATUSES[1:]),
        reason_codes=_public_reason_codes(
            "reason_codes",
            payload["reason_codes"],
        ),
        paper_only=payload["paper_only"],
        report_only=payload["report_only"],
        readonly=payload["readonly"],
    )


def _bucket_from_public_payload(
    payload: dict[str, Any],
) -> ResearchStrategyDomainForecastErrorAttributionBucket:
    _require_payload_flags("payload bucket", payload)
    return ResearchStrategyDomainForecastErrorAttributionBucket(
        bucket_code=_public_member(
            "bucket_code",
            payload["bucket_code"],
            _BUCKET_SEQUENCE,
        ),
        domain_count=_public_count("domain_count", payload["domain_count"]),
        observation_count=_public_count(
            "observation_count",
            payload["observation_count"],
        ),
        average_attribution_score=_public_ratio(
            "average_attribution_score",
            payload["average_attribution_score"],
        ),
        paper_only=payload["paper_only"],
        report_only=payload["report_only"],
        readonly=payload["readonly"],
    )


def _require_public_payload_shape(payload: dict[str, Any]) -> None:
    if tuple(payload) != _REPORT_PAYLOAD_KEYS:
        raise ValueError("payload keys must match the public report schema")
    rows = payload["rows"]
    if type(rows) is not list:
        raise ValueError("payload rows must be a list")
    for row in rows:
        if type(row) is not dict:
            raise ValueError("payload rows must contain JSON objects")
        if tuple(row) != _ROW_PAYLOAD_KEYS:
            raise ValueError("payload row keys must match the public row schema")
    buckets = payload["attribution_buckets"]
    if type(buckets) is not list:
        raise ValueError("attribution_buckets must be a list")
    for bucket in buckets:
        if type(bucket) is not dict:
            raise ValueError("attribution_buckets must contain JSON objects")
        if tuple(bucket) != _BUCKET_PAYLOAD_KEYS:
            raise ValueError(
                "payload bucket keys must match the public bucket schema",
            )


def _require_payload_flags(label: str, payload: Mapping[str, object]) -> None:
    for field_name in _PHASE_FLAG_FIELDS:
        if payload[field_name] is not True:
            raise ValueError(f"{field_name} must be True for {label}")


def _public_string(name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{name} must be a string")
    return value


def _public_member(
    name: str,
    value: object,
    allowed: Sequence[str],
) -> str:
    if type(value) is not str or value not in allowed:
        raise ValueError(f"{name} must be supported")
    return value


def _public_digest(name: str, value: object) -> str:
    _require_digest(name, value)
    return value


def _public_digest_list(name: str, value: object) -> tuple[str, ...]:
    if type(value) is not list:
        raise ValueError(f"{name} must be a list")
    return _normalize_digests(name, tuple(value))


def _public_digest_reference_list(
    name: str,
    value: object,
) -> tuple[str, ...]:
    if type(value) is not list:
        raise ValueError(f"{name} must be a list")
    return _normalize_digest_references(name, tuple(value))


def _public_datetime(name: str, value: object) -> datetime:
    if type(value) is not str:
        raise ValueError(f"{name} must be a canonical datetime string")
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError as exc:
        raise ValueError(f"{name} must be a canonical datetime string") from exc
    normalized = _as_utc(name, parsed)
    if normalized.isoformat() != value:
        raise ValueError(f"{name} must be a canonical UTC datetime string")
    return normalized


def _public_decimal(name: str, value: object) -> Decimal:
    if type(value) is not str or not _PUBLIC_DECIMAL_RE.fullmatch(value):
        raise ValueError(f"{name} must be a canonical Decimal string")
    return Decimal(value)


def _public_count(name: str, value: object) -> Decimal:
    return _require_nonnegative_count(name, _public_decimal(name, value))


def _public_positive_count(name: str, value: object) -> Decimal:
    return _require_positive_count(name, _public_decimal(name, value))


def _public_ratio(name: str, value: object) -> Decimal:
    return _require_ratio(name, _public_decimal(name, value))


def _public_reason_codes(name: str, value: object) -> tuple[str, ...]:
    if type(value) is not list:
        raise ValueError(f"{name} must be a list")
    return _normalize_reason_codes(value)


def _normalize_observations(
    observations: Sequence[ResearchStrategyDomainForecastErrorObservation],
) -> tuple[ResearchStrategyDomainForecastErrorObservation, ...]:
    if type(observations) not in (list, tuple):
        raise ValueError("observations must be a list or tuple")
    normalized: list[ResearchStrategyDomainForecastErrorObservation] = []
    digests: set[str] = set()
    for observation in observations:
        if type(observation) is not ResearchStrategyDomainForecastErrorObservation:
            raise ValueError(
                "observations must contain "
                "ResearchStrategyDomainForecastErrorObservation",
            )
        _require_observation_integrity(observation)
        if observation.observation_digest in digests:
            raise ValueError("observation_digest values must be unique")
        digests.add(observation.observation_digest)
        normalized.append(observation)
    return tuple(
        sorted(
            normalized,
            key=lambda item: (
                item.domain_key,
                item.observed_at,
                item.observation_digest,
            ),
        ),
    )


def _status_count(
    rows: tuple[ResearchStrategyDomainForecastErrorAttributionRow, ...],
    status: str,
) -> int:
    return sum(1 for row in rows if row.status == status)


def _review_priority_count(
    rows: tuple[ResearchStrategyDomainForecastErrorAttributionRow, ...],
    priority: str,
) -> int:
    return sum(1 for row in rows if row.human_review_priority == priority)


def _normalize_reason_codes(reason_codes: Sequence[str]) -> tuple[str, ...]:
    if type(reason_codes) not in (list, tuple):
        raise ValueError("reason_codes must be a list or tuple")
    normalized: list[str] = []
    for reason_code in reason_codes:
        _require_public_identifier("reason_code", reason_code)
        if reason_code not in _REASON_CODE_SEQUENCE:
            raise ValueError("reason_code must be supported")
        if reason_code in normalized:
            raise ValueError("reason_codes must be unique")
        normalized.append(reason_code)
    canonical = tuple(
        reason_code
        for reason_code in _REASON_CODE_SEQUENCE
        if reason_code in normalized
    )
    if tuple(normalized) != canonical:
        raise ValueError("reason_codes must use canonical ordering")
    return canonical


def _canonical_reason_codes(reason_codes: Sequence[str]) -> tuple[str, ...]:
    present: set[str] = set()
    for reason_code in reason_codes:
        _require_public_identifier("reason_code", reason_code)
        if reason_code not in _REASON_CODE_SEQUENCE:
            raise ValueError("reason_code must be supported")
        present.add(reason_code)
    return tuple(
        reason_code
        for reason_code in _REASON_CODE_SEQUENCE
        if reason_code in present
    )


def _require_digest(name: str, value: object) -> None:
    if type(value) is not str or not _DIGEST_RE.fullmatch(value):
        raise ValueError(f"{name} must be a lowercase sha256 digest")


def _require_digest_reference(name: str, value: object) -> None:
    if type(value) is not str or not _DIGEST_REFERENCE_RE.fullmatch(value):
        raise ValueError(f"{name} must be a sha256 digest reference")


def _normalize_digests(
    name: str,
    values: object,
) -> tuple[str, ...]:
    if type(values) is not tuple or not values:
        raise ValueError(f"{name} must be a non-empty tuple")
    normalized: list[str] = []
    for value in values:
        _require_digest(name, value)
        if value in normalized:
            raise ValueError(f"{name} must be unique")
        normalized.append(value)
    canonical = tuple(sorted(normalized))
    if tuple(normalized) != canonical:
        raise ValueError(f"{name} must use canonical ordering")
    return canonical


def _normalize_digest_references(
    name: str,
    values: object,
) -> tuple[str, ...]:
    if type(values) is not tuple or not values:
        raise ValueError(f"{name} must be a non-empty tuple")
    normalized: list[str] = []
    for value in values:
        _require_digest_reference(name, value)
        if value in normalized:
            raise ValueError(f"{name} must be unique")
        normalized.append(value)
    canonical = tuple(sorted(normalized))
    if tuple(normalized) != canonical:
        raise ValueError(f"{name} must use canonical ordering")
    return canonical


def _require_public_identifier(name: str, value: object) -> None:
    if type(value) is not str or not _PUBLIC_IDENTIFIER_RE.fullmatch(value):
        raise ValueError(f"{name} must be a public identifier")


def _require_safe_identifier(name: str, value: object) -> None:
    _require_public_identifier(name, value)
    tokens = frozenset(_UNSAFE_TOKEN_RE.findall(value.lower()))
    if tokens & _UNSAFE_IDENTIFIER_TOKENS:
        raise ValueError(f"{name} has unsafe public value")


def _require_private_identifier(name: str, value: object) -> str:
    if type(value) is not str or not value or value != value.strip():
        raise ValueError(f"{name} must be a private identifier")
    if len(value) > 2048 or any(ord(character) < 32 for character in value):
        raise ValueError(f"{name} must be a private identifier")
    return value


def _normalize_private_identifiers(
    name: str,
    values: object,
) -> tuple[str, ...]:
    if type(values) is not tuple or not values:
        raise ValueError(f"{name} must be a non-empty tuple")
    normalized: list[str] = []
    for value in values:
        private_value = _require_private_identifier(name, value)
        if private_value in normalized:
            raise ValueError(f"{name} must be unique")
        normalized.append(private_value)
    return tuple(sorted(normalized))


def _require_member(name: str, value: object, allowed: Sequence[str]) -> None:
    if type(value) is not str or value not in allowed:
        raise ValueError(f"{name} must be supported")


def _require_decimal(name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{name} must be finite")
    return _ZERO if value.is_zero() else value


def _require_ratio(name: str, value: object) -> Decimal:
    raw = _require_decimal(name, value)
    if raw < _ZERO or raw > _ONE:
        raise ValueError(f"{name} must be between zero and one")
    return _quantize(raw)


def _require_nonnegative_count(name: str, value: object) -> Decimal:
    raw = _require_decimal(name, value)
    with localcontext(_DECIMAL_CONTEXT):
        integral = raw.to_integral_value()
    if raw != integral:
        raise ValueError(f"{name} must be an integral Decimal")
    if raw < _ZERO:
        raise ValueError(f"{name} must be nonnegative")
    return _quantize(raw)


def _require_positive_count(name: str, value: object) -> Decimal:
    normalized = _require_nonnegative_count(name, value)
    if normalized <= _ZERO:
        raise ValueError(f"{name} must be positive")
    return normalized


def _require_hard_flags(name: str, value: object) -> None:
    for field_name in _PHASE_FLAG_FIELDS:
        if getattr(value, field_name) is not True:
            raise ValueError(f"{field_name} must be True for {name}")


def _require_exact_type(
    value: object,
    expected_type: type[object],
    label: str,
) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{label} must be exactly {expected_type.__name__}")


def _require_config_integrity(
    config: ResearchStrategyDomainForecastErrorAttributionConfig,
) -> None:
    _require_exact_type(
        config,
        ResearchStrategyDomainForecastErrorAttributionConfig,
        "config",
    )
    _require_public_identifier("config_version", config.config_version)
    if (
        config.config_version
        != DEFAULT_RESEARCH_STRATEGY_DOMAIN_FORECAST_ERROR_ATTRIBUTION_CONFIG_VERSION
    ):
        raise ValueError("config_version must be supported")
    supported_values = {
        "source_freshness_weight": _FACTOR_WEIGHT,
        "authority_disagreement_weight": _FACTOR_WEIGHT,
        "specialist_divergence_weight": _FACTOR_WEIGHT,
        "resolution_ambiguity_weight": _FACTOR_WEIGHT,
        "moderate_attribution_threshold": _MODERATE_ATTRIBUTION_THRESHOLD,
        "high_attribution_threshold": _HIGH_ATTRIBUTION_THRESHOLD,
        "high_factor_pressure_threshold": _HIGH_FACTOR_PRESSURE_THRESHOLD,
    }
    for field_name, supported_value in supported_values.items():
        value = getattr(config, field_name)
        if _require_ratio(field_name, value) != value:
            raise ValueError(f"{field_name} must be canonical")
        if value != supported_value:
            raise ValueError(f"{field_name} must use the supported value")
    if config.high_attribution_threshold <= config.moderate_attribution_threshold:
        raise ValueError(
            "high_attribution_threshold must exceed moderate_attribution_threshold",
        )
    if _sum_decimals(
        (
            config.source_freshness_weight,
            config.authority_disagreement_weight,
            config.specialist_divergence_weight,
            config.resolution_ambiguity_weight,
        ),
    ) != _ONE:
        raise ValueError("factor weights must sum to one")
    _require_hard_flags("config", config)


def _require_observation_integrity(
    observation: ResearchStrategyDomainForecastErrorObservation,
) -> None:
    _require_exact_type(
        observation,
        ResearchStrategyDomainForecastErrorObservation,
        "observation",
    )
    _require_digest("observation_digest", observation.observation_digest)
    _require_safe_identifier("domain_key", observation.domain_key)
    _require_private_identifier("team_identifier", observation.team_identifier)
    normalized_sources = _normalize_private_identifiers(
        "source_identifiers",
        observation.source_identifiers,
    )
    if observation.source_identifiers != normalized_sources:
        raise ValueError("source_identifiers must use canonical ordering")
    _require_canonical_utc_datetime("observed_at", observation.observed_at)
    for field_name in (
        "absolute_forecast_error",
        "source_freshness_score",
        "authority_disagreement_score",
        "specialist_divergence_score",
        "resolution_ambiguity_score",
    ):
        value = getattr(observation, field_name)
        if _require_ratio(field_name, value) != value:
            raise ValueError(f"{field_name} must be canonical")
    _require_hard_flags("observation", observation)


def _require_report_runtime_schema(
    report: ResearchStrategyDomainForecastErrorAttributionReport,
) -> None:
    _require_exact_type(
        report,
        ResearchStrategyDomainForecastErrorAttributionReport,
        "report",
    )
    _require_canonical_utc_datetime("generated_at", report.generated_at)
    _require_public_identifier("config_version", report.config_version)
    if (
        report.config_version
        != DEFAULT_RESEARCH_STRATEGY_DOMAIN_FORECAST_ERROR_ATTRIBUTION_CONFIG_VERSION
    ):
        raise ValueError("config_version must be supported")
    _require_member("status", report.status, _STATUSES)
    for field_name in (
        "observation_count",
        "domain_count",
        "low_count",
        "moderate_count",
        "high_count",
        "high_review_priority_count",
        "medium_review_priority_count",
        "low_review_priority_count",
    ):
        _require_runtime_nonnegative_count(field_name, getattr(report, field_name))
    for field_name in (
        "average_attribution_score",
        "max_attribution_score",
        "average_long_term_learning_score",
        "max_long_term_learning_score",
        "average_human_review_priority_score",
        "max_human_review_priority_score",
    ):
        _require_runtime_ratio(field_name, getattr(report, field_name))
    if type(report.rows) is not tuple:
        raise ValueError("rows must be a tuple")
    for row in report.rows:
        if type(row) is not ResearchStrategyDomainForecastErrorAttributionRow:
            raise ValueError(
                "rows must contain "
                "ResearchStrategyDomainForecastErrorAttributionRow",
            )
        _require_row_runtime_schema(row)
    if type(report.attribution_buckets) is not tuple:
        raise ValueError("attribution_buckets must be a tuple")
    for bucket in report.attribution_buckets:
        if type(bucket) is not ResearchStrategyDomainForecastErrorAttributionBucket:
            raise ValueError(
                "attribution_buckets must contain "
                "ResearchStrategyDomainForecastErrorAttributionBucket",
            )
        _require_bucket_runtime_schema(bucket)
    if type(report.reason_codes) is not tuple:
        raise ValueError("reason_codes must be a tuple")
    _normalize_reason_codes(report.reason_codes)
    _require_digest("derived_validation_digest", report.derived_validation_digest)
    _require_hard_flags("report", report)


def _require_row_runtime_schema(
    row: ResearchStrategyDomainForecastErrorAttributionRow,
) -> None:
    _require_exact_type(
        row,
        ResearchStrategyDomainForecastErrorAttributionRow,
        "row",
    )
    _require_runtime_positive_count("rank", row.rank)
    _require_safe_identifier("domain_key", row.domain_key)
    _require_runtime_positive_count("observation_count", row.observation_count)
    _normalize_digests("observation_digests", row.observation_digests)
    _require_runtime_positive_count("team_count", row.team_count)
    _normalize_digest_references("team_digests", row.team_digests)
    _require_runtime_positive_count("source_count", row.source_count)
    _normalize_digest_references("source_digests", row.source_digests)
    for field_name in (
        "average_absolute_forecast_error",
        "source_staleness_score",
        "authority_disagreement_score",
        "specialist_divergence_score",
        "resolution_ambiguity_score",
        "source_freshness_attribution_score",
        "authority_disagreement_attribution_score",
        "specialist_divergence_attribution_score",
        "resolution_ambiguity_attribution_score",
        "attribution_score",
        "long_term_learning_score",
        "human_review_priority_score",
    ):
        _require_runtime_ratio(field_name, getattr(row, field_name))
    _require_member(
        "human_review_priority",
        row.human_review_priority,
        _REVIEW_PRIORITIES,
    )
    _require_member(
        "dominant_attribution_bucket",
        row.dominant_attribution_bucket,
        _BUCKET_SEQUENCE,
    )
    _require_member("status", row.status, _STATUSES[1:])
    if type(row.reason_codes) is not tuple:
        raise ValueError("reason_codes must be a tuple")
    _normalize_reason_codes(row.reason_codes)
    _require_hard_flags("row", row)


def _require_bucket_runtime_schema(
    bucket: ResearchStrategyDomainForecastErrorAttributionBucket,
) -> None:
    _require_exact_type(
        bucket,
        ResearchStrategyDomainForecastErrorAttributionBucket,
        "bucket",
    )
    _require_member("bucket_code", bucket.bucket_code, _BUCKET_SEQUENCE)
    _require_runtime_nonnegative_count("domain_count", bucket.domain_count)
    _require_runtime_nonnegative_count(
        "observation_count",
        bucket.observation_count,
    )
    _require_runtime_ratio(
        "average_attribution_score",
        bucket.average_attribution_score,
    )
    _require_hard_flags("bucket", bucket)


def _require_runtime_ratio(name: str, value: object) -> Decimal:
    normalized = _require_ratio(name, value)
    if normalized != value:
        raise ValueError(f"{name} must be canonical")
    return normalized


def _require_runtime_nonnegative_count(name: str, value: object) -> Decimal:
    normalized = _require_nonnegative_count(name, value)
    if normalized != value:
        raise ValueError(f"{name} must be canonical")
    return normalized


def _require_runtime_positive_count(name: str, value: object) -> Decimal:
    normalized = _require_positive_count(name, value)
    if normalized != value:
        raise ValueError(f"{name} must be canonical")
    return normalized


def _require_canonical_utc_datetime(name: str, value: object) -> datetime:
    normalized = _as_utc(name, value)
    if value.tzinfo is not UTC or value != normalized:
        raise ValueError(f"{name} must use canonical UTC")
    return normalized


def _descending_ratio_sort_key(name: str, value: object) -> Decimal:
    return _require_ratio(name, value).copy_negate()


def _as_utc(name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_sort_string(name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{name} must be a string")
    return value


def _require_sort_tuple(name: str, value: object) -> tuple[str, ...]:
    if type(value) is not tuple or any(type(item) is not str for item in value):
        raise ValueError(f"{name} must be a tuple of strings")
    return value


def _private_digest(kind: str, value: str) -> str:
    private_value = _require_private_identifier("private identifier", value)
    digest = hashlib.sha256(
        (kind + "\0" + private_value).encode("utf-8"),
    ).hexdigest()
    return f"sha256:{digest}"


def _sum_decimals(values: tuple[Decimal, ...]) -> Decimal:
    with localcontext(_DECIMAL_CONTEXT):
        total = _ZERO
        for value in values:
            total += _require_decimal("sum value", value)
    return _quantize(total)


def _product(*values: Decimal) -> Decimal:
    with localcontext(_DECIMAL_CONTEXT):
        product = _ONE
        for value in values:
            product *= _require_decimal("product value", value)
    return _quantize(product)


def _difference(left: Decimal, right: Decimal) -> Decimal:
    with localcontext(_DECIMAL_CONTEXT):
        value = _require_decimal("left", left) - _require_decimal("right", right)
    return _require_ratio("difference", value)


def _average(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return _ZERO
    with localcontext(_DECIMAL_CONTEXT):
        total = _ZERO
        for value in values:
            total += _require_decimal("average value", value)
        average = total / Decimal(len(values))
    return _quantize(average)


def _count(value: int) -> Decimal:
    if value < 0:
        raise ValueError("count must be nonnegative")
    return _quantize(Decimal(value))


def _quantize(value: Decimal) -> Decimal:
    if type(value) is not Decimal or not value.is_finite():
        raise ValueError("Decimal value must be finite")
    try:
        with localcontext(_DECIMAL_CONTEXT):
            normalized = value.quantize(_QUANT)
    except DecimalException as exc:
        raise ValueError("Decimal value cannot be quantized") from exc
    return _ZERO if normalized.is_zero() else normalized


def _report_values_without_digest(
    report: ResearchStrategyDomainForecastErrorAttributionReport,
) -> dict[str, object]:
    values = asdict(report)
    values.pop("derived_validation_digest", None)
    return values


def _report_digest_from_values(values: Mapping[str, object]) -> str:
    canonical = json.dumps(
        _json_ready(values),
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _json_ready(value: Any) -> Any:
    if is_dataclass(value) and not isinstance(value, type):
        return _json_ready(asdict(value))
    if type(value) is dict:
        return {str(key): _json_ready(item) for key, item in value.items()}
    if type(value) in (list, tuple):
        return [_json_ready(item) for item in value]
    if type(value) is Decimal:
        return format(_require_decimal("public decimal", value), ".6f")
    if type(value) is datetime:
        return value.isoformat()
    if type(value) in (str, bool) or value is None:
        return value
    if type(value) in (int, float):
        raise ValueError("public numeric values must be Decimal")
    raise ValueError(f"unsupported public payload value: {type(value).__name__}")


__all__ = (
    "DEFAULT_RESEARCH_STRATEGY_DOMAIN_FORECAST_ERROR_ATTRIBUTION_CONFIG_VERSION",
    "ResearchStrategyDomainForecastErrorAttributionBucket",
    "ResearchStrategyDomainForecastErrorAttributionConfig",
    "ResearchStrategyDomainForecastErrorAttributionReport",
    "ResearchStrategyDomainForecastErrorAttributionRow",
    "ResearchStrategyDomainForecastErrorObservation",
    "build_research_strategy_domain_forecast_error_attribution_report",
    "research_strategy_domain_forecast_error_attribution_report_payload",
    "validate_research_strategy_domain_forecast_error_attribution_report_payload",
)
