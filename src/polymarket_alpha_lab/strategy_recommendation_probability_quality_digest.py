from __future__ import annotations

import hashlib
import json
from collections import Counter
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, localcontext
from typing import Any

from polymarket_alpha_lab.team_paper_guard import (
    UNSAFE_SURFACE_FIELD_FRAGMENTS as _UNSAFE_SURFACE_FIELD_FRAGMENTS,
)


__all__ = (
    "DEFAULT_STRATEGY_RECOMMENDATION_PROBABILITY_QUALITY_DIGEST_CONFIG_VERSION",
    "StrategyRecommendationProbabilityQualityDigestCandidate",
    "StrategyRecommendationProbabilityQualityDigestConfig",
    "StrategyRecommendationProbabilityQualityDigestReport",
    "StrategyRecommendationProbabilityQualityDigestRollup",
    "build_strategy_recommendation_probability_quality_digest_report",
    "strategy_recommendation_probability_quality_digest_payload",
)


DEFAULT_STRATEGY_RECOMMENDATION_PROBABILITY_QUALITY_DIGEST_CONFIG_VERSION = (
    "strategy-recommendation-probability-quality-digest-v0"
)
DECIMAL_CONTEXT = Context(prec=64)
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
STATUSES = ("pass", "watch", "blocked")
READY_REASON_CODE = "probability_quality_ready"
SOURCE_READY_REASON_CODE = "source_ready"
MODULE_REASON_CODES = frozenset(
    (
        "ensemble_dispersion_blocked",
        "ensemble_dispersion_watch",
        "low_forecast_confidence",
        "market_probability_gap_below_threshold",
        "missing_rationale",
        "stale_probability_context",
        "unresolved_rationale_gap",
    ),
)
SENSITIVE_STRING_FRAGMENTS = (
    "api key",
    "api_key",
    "api-key",
    "apikey",
    "bearer",
    "credential",
    "password",
    "private key",
    "private_key",
    "private-key",
    "secret",
    "sk_",
    "token",
    "aut" "h",
    "can" "cel",
    "li" "ve",
    "ord" "er",
    "rep" "lace",
    "tra" "de",
    "wal" "let",
    "net" "work",
    "data" "base",
    "per" "sist",
)
EXTRA_UNSAFE_SURFACE_FIELD_FRAGMENTS = frozenset(
    (
        "li" "ve",
        "net" "work",
        "data" "base",
        "per" "sist",
    ),
)
UNSAFE_SURFACE_FIELD_FRAGMENTS = (
    _UNSAFE_SURFACE_FIELD_FRAGMENTS | EXTRA_UNSAFE_SURFACE_FIELD_FRAGMENTS
)


@dataclass(frozen=True)
class StrategyRecommendationProbabilityQualityDigestConfig:
    config_version: str = (
        DEFAULT_STRATEGY_RECOMMENDATION_PROBABILITY_QUALITY_DIGEST_CONFIG_VERSION
    )
    min_forecast_confidence: Decimal = Decimal("0.700000")
    min_probability_gap: Decimal = Decimal("0.020000")
    max_watch_ensemble_dispersion: Decimal = Decimal("0.150000")
    max_blocking_ensemble_dispersion: Decimal = Decimal("0.350000")
    max_probability_context_age_seconds: Decimal = Decimal("14400")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "StrategyRecommendationProbabilityQualityDigestConfig "
            "does not support subclassing",
        )

    def __post_init__(self) -> None:
        if type(self) is not StrategyRecommendationProbabilityQualityDigestConfig:
            raise ValueError(
                "config must be exactly "
                "StrategyRecommendationProbabilityQualityDigestConfig",
            )
        _require_canonical_string("config_version", self.config_version)
        object.__setattr__(
            self,
            "min_forecast_confidence",
            _require_probability("min_forecast_confidence", self.min_forecast_confidence),
        )
        object.__setattr__(
            self,
            "min_probability_gap",
            _require_probability("min_probability_gap", self.min_probability_gap),
        )
        object.__setattr__(
            self,
            "max_watch_ensemble_dispersion",
            _require_probability(
                "max_watch_ensemble_dispersion",
                self.max_watch_ensemble_dispersion,
            ),
        )
        object.__setattr__(
            self,
            "max_blocking_ensemble_dispersion",
            _require_probability(
                "max_blocking_ensemble_dispersion",
                self.max_blocking_ensemble_dispersion,
            ),
        )
        object.__setattr__(
            self,
            "max_probability_context_age_seconds",
            _require_nonnegative_decimal(
                "max_probability_context_age_seconds",
                self.max_probability_context_age_seconds,
            ),
        )
        if self.max_watch_ensemble_dispersion > self.max_blocking_ensemble_dispersion:
            raise ValueError(
                "max_watch_ensemble_dispersion must be less than or equal to "
                "max_blocking_ensemble_dispersion",
            )
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class StrategyRecommendationProbabilityQualityDigestCandidate:
    candidate_id: str
    market_slug: str
    condition_id: str
    recommendation_rank: Decimal
    forecast_probability: Decimal
    market_probability: Decimal
    probability_gap: Decimal
    forecast_confidence: Decimal
    ensemble_min_probability: Decimal
    ensemble_max_probability: Decimal
    ensemble_dispersion: Decimal
    probability_generated_at: datetime
    probability_context_age_seconds: Decimal
    quality_status: str
    rationale: str
    rationale_gap_codes: tuple[str, ...]
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "StrategyRecommendationProbabilityQualityDigestCandidate "
            "does not support subclassing",
        )

    def __post_init__(self) -> None:
        if type(self) is not StrategyRecommendationProbabilityQualityDigestCandidate:
            raise ValueError(
                "candidate must be exactly "
                "StrategyRecommendationProbabilityQualityDigestCandidate",
            )
        _require_canonical_string("candidate_id", self.candidate_id)
        _require_canonical_string("market_slug", self.market_slug)
        _require_canonical_string("condition_id", self.condition_id)
        object.__setattr__(
            self,
            "recommendation_rank",
            _require_nonnegative_decimal("recommendation_rank", self.recommendation_rank),
        )
        for field_name in (
            "forecast_probability",
            "market_probability",
            "forecast_confidence",
            "ensemble_min_probability",
            "ensemble_max_probability",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_probability(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "probability_gap",
            _require_probability("probability_gap", self.probability_gap),
        )
        object.__setattr__(
            self,
            "ensemble_dispersion",
            _require_probability("ensemble_dispersion", self.ensemble_dispersion),
        )
        object.__setattr__(
            self,
            "probability_generated_at",
            _as_utc("probability_generated_at", self.probability_generated_at),
        )
        object.__setattr__(
            self,
            "probability_context_age_seconds",
            _require_nonnegative_decimal(
                "probability_context_age_seconds",
                self.probability_context_age_seconds,
            ),
        )
        _require_status("quality_status", self.quality_status)
        _require_string("rationale", self.rationale)
        object.__setattr__(
            self,
            "rationale_gap_codes",
            _normalize_reason_codes("rationale_gap_codes", self.rationale_gap_codes),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        if self.ensemble_min_probability > self.ensemble_max_probability:
            raise ValueError(
                "ensemble_min_probability must be less than or equal to "
                "ensemble_max_probability",
            )
        if self.probability_gap != _abs_decimal(
            self.forecast_probability - self.market_probability,
        ):
            raise ValueError("probability_gap must match forecast and market probability")
        if self.ensemble_dispersion != (
            self.ensemble_max_probability - self.ensemble_min_probability
        ):
            raise ValueError("ensemble_dispersion must match ensemble bounds")
        _require_hard_flags("candidate", self)


@dataclass(frozen=True)
class StrategyRecommendationProbabilityQualityDigestRollup:
    candidate_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    blocked_count: Decimal
    average_forecast_confidence: Decimal
    average_probability_gap: Decimal
    average_ensemble_dispersion: Decimal
    stale_context_count: Decimal
    unresolved_rationale_gap_count: Decimal
    reason_code_counts: tuple[tuple[str, Decimal], ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "StrategyRecommendationProbabilityQualityDigestRollup "
            "does not support subclassing",
        )

    def __post_init__(self) -> None:
        if type(self) is not StrategyRecommendationProbabilityQualityDigestRollup:
            raise ValueError(
                "rollup must be exactly "
                "StrategyRecommendationProbabilityQualityDigestRollup",
            )
        for field_name in (
            "candidate_count",
            "pass_count",
            "watch_count",
            "blocked_count",
            "average_forecast_confidence",
            "average_probability_gap",
            "average_ensemble_dispersion",
            "stale_context_count",
            "unresolved_rationale_gap_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        _require_hard_flags("rollup", self)


@dataclass(frozen=True)
class StrategyRecommendationProbabilityQualityDigestReport:
    generated_at: datetime
    config_version: str
    digest_status: str
    recommended_next_step: str
    rows: tuple[StrategyRecommendationProbabilityQualityDigestCandidate, ...]
    rollup: StrategyRecommendationProbabilityQualityDigestRollup
    reason_codes: tuple[str, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "StrategyRecommendationProbabilityQualityDigestReport "
            "does not support subclassing",
        )

    def __post_init__(self) -> None:
        if type(self) is not StrategyRecommendationProbabilityQualityDigestReport:
            raise ValueError(
                "report must be exactly "
                "StrategyRecommendationProbabilityQualityDigestReport",
            )
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        _require_status("digest_status", self.digest_status)
        _require_canonical_string("recommended_next_step", self.recommended_next_step)
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        if type(self.rollup) is not StrategyRecommendationProbabilityQualityDigestRollup:
            raise ValueError("rollup must be exact rollup")
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        object.__setattr__(
            self,
            "derived_validation_digest",
            (
                _report_derived_validation_digest(self)
                if self.derived_validation_digest == ""
                else _require_sha256_digest(
                    "derived_validation_digest",
                    self.derived_validation_digest,
                )
            ),
        )
        _validate_report(self)
        _require_hard_flags("report", self)


def build_strategy_recommendation_probability_quality_digest_report(
    candidates: object,
    *,
    generated_at: datetime,
    config: StrategyRecommendationProbabilityQualityDigestConfig,
) -> StrategyRecommendationProbabilityQualityDigestReport:
    if type(config) is not StrategyRecommendationProbabilityQualityDigestConfig:
        raise ValueError(
            "config must be exactly "
            "StrategyRecommendationProbabilityQualityDigestConfig",
        )
    _require_hard_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    source_rows = _source_rows(candidates)
    rows = tuple(
        sorted(
            (_candidate_from_source(row, generated_at_utc, config) for row in source_rows),
            key=_candidate_sort_key,
        ),
    )
    reason_codes = _digest_reason_codes(rows)
    digest_status = _digest_status(rows)
    return StrategyRecommendationProbabilityQualityDigestReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        digest_status=digest_status,
        recommended_next_step=_recommended_next_step(digest_status, reason_codes),
        rows=rows,
        rollup=_rollup(rows, reason_codes),
        reason_codes=reason_codes,
    )


def strategy_recommendation_probability_quality_digest_payload(
    report: object,
) -> dict[str, Any]:
    if type(report) is StrategyRecommendationProbabilityQualityDigestReport:
        _require_hard_flags("report", report)
        _reject_unsafe_surface_fields("report", report)
        _validate_report(report)
        payload = _payload_value(report)
        if not isinstance(payload, dict):
            raise ValueError("payload must be a public object")
        return payload
    if isinstance(report, dict):
        return _validate_public_payload(report)
    raise ValueError(
        "report must be exactly "
        "StrategyRecommendationProbabilityQualityDigestReport or public payload dict",
    )


def _candidate_from_source(
    source: object,
    generated_at: datetime,
    config: StrategyRecommendationProbabilityQualityDigestConfig,
) -> StrategyRecommendationProbabilityQualityDigestCandidate:
    _reject_unsafe_surface_fields("candidate", source)
    _require_hard_flags("candidate", source)
    _reject_float_tree("candidate", source)
    forecast_probability = _require_probability(
        "forecast_probability",
        _required_attr(source, "forecast_probability"),
    )
    market_probability = _require_probability(
        "market_probability",
        _required_attr(source, "market_probability"),
    )
    forecast_confidence = _require_probability(
        "forecast_confidence",
        _required_attr(source, "forecast_confidence"),
    )
    ensemble_min_probability = _require_probability(
        "ensemble_min_probability",
        _required_attr(source, "ensemble_min_probability"),
    )
    ensemble_max_probability = _require_probability(
        "ensemble_max_probability",
        _required_attr(source, "ensemble_max_probability"),
    )
    if ensemble_min_probability > ensemble_max_probability:
        raise ValueError(
            "ensemble_min_probability must be less than or equal to "
            "ensemble_max_probability",
        )
    probability_generated_at = _as_utc(
        "probability_generated_at",
        _required_attr(source, "probability_generated_at"),
    )
    context_age = _seconds_between(generated_at, probability_generated_at)
    rationale = _optional_string(source, "rationale")
    rationale_gap_codes = _normalize_reason_codes(
        "rationale_gap_codes",
        _optional_attr(source, "rationale_gap_codes", ()),
    )
    probability_gap = _abs_decimal(forecast_probability - market_probability)
    ensemble_dispersion = ensemble_max_probability - ensemble_min_probability
    reason_codes = _candidate_reason_codes(
        forecast_confidence=forecast_confidence,
        probability_gap=probability_gap,
        ensemble_dispersion=ensemble_dispersion,
        context_age=context_age,
        rationale=rationale,
        rationale_gap_codes=rationale_gap_codes,
        source_reason_codes=_normalize_source_reason_codes(source),
        config=config,
    )
    return StrategyRecommendationProbabilityQualityDigestCandidate(
        candidate_id=_required_canonical_attr(source, "candidate_id"),
        market_slug=_required_canonical_attr(source, "market_slug"),
        condition_id=_required_canonical_attr(source, "condition_id"),
        recommendation_rank=_require_nonnegative_decimal(
            "recommendation_rank",
            _optional_attr(source, "recommendation_rank", ZERO),
        ),
        forecast_probability=forecast_probability,
        market_probability=market_probability,
        probability_gap=probability_gap,
        forecast_confidence=forecast_confidence,
        ensemble_min_probability=ensemble_min_probability,
        ensemble_max_probability=ensemble_max_probability,
        ensemble_dispersion=ensemble_dispersion,
        probability_generated_at=probability_generated_at,
        probability_context_age_seconds=context_age,
        quality_status=_candidate_status(reason_codes),
        rationale=rationale,
        rationale_gap_codes=rationale_gap_codes,
        reason_codes=reason_codes,
    )


def _candidate_reason_codes(
    *,
    forecast_confidence: Decimal,
    probability_gap: Decimal,
    ensemble_dispersion: Decimal,
    context_age: Decimal,
    rationale: str,
    rationale_gap_codes: tuple[str, ...],
    source_reason_codes: tuple[str, ...],
    config: StrategyRecommendationProbabilityQualityDigestConfig,
) -> tuple[str, ...]:
    codes: list[str] = []
    if forecast_confidence < config.min_forecast_confidence:
        codes.append("low_forecast_confidence")
    if probability_gap < config.min_probability_gap:
        codes.append("market_probability_gap_below_threshold")
    if ensemble_dispersion >= config.max_blocking_ensemble_dispersion:
        codes.append("ensemble_dispersion_blocked")
    elif ensemble_dispersion >= config.max_watch_ensemble_dispersion:
        codes.append("ensemble_dispersion_watch")
    if context_age > config.max_probability_context_age_seconds:
        codes.append("stale_probability_context")
    if not rationale:
        codes.append("missing_rationale")
    if rationale_gap_codes:
        codes.append("unresolved_rationale_gap")
        codes.extend(rationale_gap_codes)
    codes.extend(code for code in source_reason_codes if code != SOURCE_READY_REASON_CODE)
    if not codes:
        codes.append(READY_REASON_CODE)
    return tuple(sorted(dict.fromkeys(codes)))


def _candidate_status(reason_codes: tuple[str, ...]) -> str:
    blocked_codes = (
        "ensemble_dispersion_blocked",
        "low_forecast_confidence",
        "market_probability_gap_below_threshold",
        "missing_rationale",
        "stale_probability_context",
        "unresolved_rationale_gap",
    )
    if any(code in reason_codes for code in blocked_codes):
        return "blocked"
    if any(code.endswith("_watch") for code in reason_codes):
        return "watch"
    return "pass"


def _digest_status(
    rows: tuple[StrategyRecommendationProbabilityQualityDigestCandidate, ...],
) -> str:
    if not rows:
        return "blocked"
    if any(row.quality_status == "blocked" for row in rows):
        return "blocked"
    if any(row.quality_status == "watch" for row in rows):
        return "watch"
    return "pass"


def _digest_reason_codes(
    rows: tuple[StrategyRecommendationProbabilityQualityDigestCandidate, ...],
) -> tuple[str, ...]:
    if not rows:
        return ("missing_candidates",)
    codes = sorted(
        {
            code
            for row in rows
            for code in row.reason_codes
            if code != READY_REASON_CODE
            and (code in MODULE_REASON_CODES or code in row.rationale_gap_codes)
        },
    )
    if not codes:
        return (READY_REASON_CODE,)
    return tuple(codes)


def _recommended_next_step(status: str, reason_codes: tuple[str, ...]) -> str:
    if "missing_candidates" in reason_codes:
        return "provide_recommendation_candidates"
    if "stale_probability_context" in reason_codes:
        return "refresh_probability_context"
    if status == "blocked":
        return "resolve_probability_quality_blocks"
    if status == "watch":
        return "review_probability_quality_watchlist"
    return "continue_recommendation_review"


def _rollup(
    rows: tuple[StrategyRecommendationProbabilityQualityDigestCandidate, ...],
    reason_codes: tuple[str, ...],
) -> StrategyRecommendationProbabilityQualityDigestRollup:
    if not rows:
        return StrategyRecommendationProbabilityQualityDigestRollup(
            candidate_count=Decimal("0"),
            pass_count=Decimal("0"),
            watch_count=Decimal("0"),
            blocked_count=Decimal("0"),
            average_forecast_confidence=ZERO,
            average_probability_gap=ZERO,
            average_ensemble_dispersion=ZERO,
            stale_context_count=Decimal("0"),
            unresolved_rationale_gap_count=Decimal("0"),
            reason_code_counts=(("missing_candidates", Decimal("1")),),
        )
    return StrategyRecommendationProbabilityQualityDigestRollup(
        candidate_count=Decimal(len(rows)),
        pass_count=_status_count(rows, "pass"),
        watch_count=_status_count(rows, "watch"),
        blocked_count=_status_count(rows, "blocked"),
        average_forecast_confidence=_average(
            row.forecast_confidence for row in rows
        ),
        average_probability_gap=_average(row.probability_gap for row in rows),
        average_ensemble_dispersion=_average(row.ensemble_dispersion for row in rows),
        stale_context_count=Decimal(
            sum("stale_probability_context" in row.reason_codes for row in rows),
        ),
        unresolved_rationale_gap_count=Decimal(
            sum(
                bool(row.rationale_gap_codes) or "missing_rationale" in row.reason_codes
                for row in rows
            ),
        ),
        reason_code_counts=_reason_code_counts(rows, reason_codes),
    )


def _reason_code_counts(
    rows: tuple[StrategyRecommendationProbabilityQualityDigestCandidate, ...],
    reason_codes: tuple[str, ...],
) -> tuple[tuple[str, Decimal], ...]:
    if reason_codes == ("missing_candidates",):
        return (("missing_candidates", Decimal("1")),)
    counter: Counter[str] = Counter()
    for row in rows:
        counter.update(row.reason_codes)
    return tuple(
        (reason_code, Decimal(counter[reason_code]))
        for reason_code in sorted(counter)
    )


def _status_count(
    rows: tuple[StrategyRecommendationProbabilityQualityDigestCandidate, ...],
    status: str,
) -> Decimal:
    return Decimal(sum(row.quality_status == status for row in rows))


def _average(values: object) -> Decimal:
    values_tuple = tuple(values)
    if not values_tuple:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return _six_places(sum(values_tuple, ZERO) / Decimal(len(values_tuple)))


def _source_rows(candidates: object) -> tuple[object, ...]:
    if candidates is None:
        raise ValueError("candidates must be a tuple")
    _reject_float_tree("candidates", candidates)
    if not isinstance(candidates, tuple):
        raise ValueError("candidates must be a tuple")
    return tuple(candidates)


def _normalize_rows(
    rows: object,
) -> tuple[StrategyRecommendationProbabilityQualityDigestCandidate, ...]:
    if type(rows) is not tuple:
        raise ValueError("rows must be a tuple")
    normalized = tuple(rows)
    previous_key: tuple[Decimal, str, str, str] | None = None
    for row in normalized:
        if type(row) is not StrategyRecommendationProbabilityQualityDigestCandidate:
            raise ValueError("rows must contain exact candidate rows")
        key = _candidate_sort_key(row)
        if previous_key is not None and previous_key > key:
            raise ValueError("rows must use deterministic sequence")
        previous_key = key
    return normalized


def _candidate_sort_key(
    row: StrategyRecommendationProbabilityQualityDigestCandidate,
) -> tuple[Decimal, str, str, str]:
    return (
        row.recommendation_rank,
        row.market_slug,
        row.condition_id,
        row.candidate_id,
    )


def _normalize_reason_code_counts(
    value: object,
) -> tuple[tuple[str, Decimal], ...]:
    if type(value) is not tuple:
        raise ValueError("reason_code_counts must be a tuple")
    rows: list[tuple[str, Decimal]] = []
    seen: set[str] = set()
    previous: str | None = None
    for item in value:
        if type(item) is not tuple or len(item) != 2:
            raise ValueError("reason_code_counts must contain pairs")
        reason_code, count = item
        _require_canonical_string("reason_code", reason_code)
        if reason_code in seen:
            raise ValueError("reason_code_counts must be unique")
        if previous is not None and previous > reason_code:
            raise ValueError("reason_code_counts must be sorted")
        rows.append(
            (
                reason_code,
                _require_positive_decimal("reason_code_count", count),
            ),
        )
        previous = reason_code
        seen.add(reason_code)
    if not rows:
        raise ValueError("reason_code_counts is required")
    return tuple(rows)


def _normalize_reason_codes(field_name: str, value: object) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ValueError(f"{field_name} must be a tuple")
    values = tuple(value)
    if not values:
        return ()
    normalized: list[str] = []
    seen: set[str] = set()
    for reason_code in values:
        _require_canonical_string(field_name, reason_code)
        if reason_code not in seen:
            normalized.append(reason_code)
            seen.add(reason_code)
    return tuple(sorted(normalized))


def _normalize_source_reason_codes(source: object) -> tuple[str, ...]:
    return _normalize_reason_codes(
        "reason_codes",
        _optional_attr(source, "reason_codes", ()),
    )


def _validate_report(report: StrategyRecommendationProbabilityQualityDigestReport) -> None:
    if report.derived_validation_digest != _report_derived_validation_digest(report):
        raise ValueError("derived_validation_digest must match report fields")
    if report.reason_codes != _digest_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")
    if report.digest_status != _digest_status(report.rows):
        raise ValueError("digest_status must match rows")
    if report.recommended_next_step != _recommended_next_step(
        report.digest_status,
        report.reason_codes,
    ):
        raise ValueError("recommended_next_step must match report status")
    if report.rollup != _rollup(report.rows, report.reason_codes):
        raise ValueError("rollup must match rows")


def _report_derived_validation_digest(
    report: StrategyRecommendationProbabilityQualityDigestReport,
) -> str:
    values = _payload_value(asdict(report))
    if not isinstance(values, dict):
        raise ValueError("derived_validation_digest source must be an object")
    return _derived_validation_digest(values)


def _derived_validation_digest(values: dict[str, Any]) -> str:
    payload = dict(values)
    payload.pop("derived_validation_digest", None)
    return hashlib.sha256(
        json.dumps(
            payload,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
            allow_nan=False,
        ).encode("utf-8"),
    ).hexdigest()


def _require_sha256_digest(field_name: str, value: object) -> str:
    if type(value) is not str or len(value) != 64:
        raise ValueError(f"{field_name} must be a sha256 hex string")
    if any(character not in "0123456789abcdef" for character in value):
        raise ValueError(f"{field_name} must be a sha256 hex string")
    return value


def _validate_public_payload(payload: dict[str, Any]) -> dict[str, Any]:
    normalized = _payload_value(payload)
    if not isinstance(normalized, dict):
        raise ValueError("payload must be a public object")
    _require_payload_hard_flags("payload", normalized)
    provided_digest = _require_sha256_digest(
        "derived_validation_digest",
        normalized.get("derived_validation_digest"),
    )
    if provided_digest != _derived_validation_digest(normalized):
        raise ValueError("derived_validation_digest must match public payload")
    return normalized


def _require_payload_hard_flags(label: str, value: object) -> None:
    if isinstance(value, dict):
        if any(field_name in value for field_name in ("paper_only", "report_only", "readonly")):
            if value.get("paper_only") is not True:
                raise ValueError(f"{label} must be paper_only")
            if value.get("report_only") is not True:
                raise ValueError(f"{label} must be report_only")
            if value.get("readonly") is not True:
                raise ValueError(f"{label} must be readonly")
        for item in value.values():
            _require_payload_hard_flags(label, item)
    elif isinstance(value, list):
        for item in value:
            _require_payload_hard_flags(label, item)


def _payload_value(value: object) -> Any:
    if isinstance(value, Decimal):
        return str(value)
    if type(value) is datetime:
        return value.astimezone(UTC).isoformat()
    if type(value) is float:
        raise ValueError("payload value must not be a float")
    if type(value) is int:
        raise ValueError("payload value must use Decimal values")
    if hasattr(value, "__dataclass_fields__"):
        _require_hard_flags("payload", value)
        _reject_unsafe_surface_fields("payload", value)
        return _payload_value(asdict(value))
    if isinstance(value, dict):
        _reject_unsafe_surface_fields("payload", value)
        return {str(key): _payload_value(item) for key, item in value.items()}
    if isinstance(value, tuple):
        return [_payload_value(item) for item in value]
    if isinstance(value, list):
        return [_payload_value(item) for item in value]
    if type(value) is str:
        _reject_unsafe_public_value("payload", value)
        return value
    return value


def _required_attr(source: object, name: str) -> object:
    try:
        value = object.__getattribute__(source, name)
    except AttributeError as exc:
        raise ValueError(f"candidate must expose {name}") from exc
    if value is None:
        raise ValueError(f"candidate must expose {name}")
    return value


def _optional_attr(source: object, name: str, default: object = None) -> object:
    try:
        value = object.__getattribute__(source, name)
    except AttributeError:
        return default
    if value is None:
        return default
    return value


def _required_canonical_attr(source: object, name: str) -> str:
    value = _required_attr(source, name)
    _require_canonical_string(name, value)
    return value


def _optional_string(source: object, name: str) -> str:
    value = _optional_attr(source, name, "")
    _require_string(name, value)
    return value.strip()


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _seconds_between(later: datetime, earlier: datetime) -> Decimal:
    seconds = Decimal(str((later - earlier).total_seconds()))
    if seconds < 0:
        raise ValueError("probability context timestamp must not be after generated_at")
    return _six_places(seconds)


def _reject_float_tree(label: str, value: object) -> None:
    if isinstance(value, float):
        raise ValueError(f"{label} must not contain float values")
    if isinstance(value, dict):
        for key, item in value.items():
            _reject_float_tree(f"{label}.{key}", item)
    elif isinstance(value, (tuple, list)):
        for index, item in enumerate(value):
            _reject_float_tree(f"{label}.{index}", item)
    elif hasattr(value, "__dict__"):
        for key, item in vars(value).items():
            _reject_float_tree(f"{label}.{key}", item)


def _reject_unsafe_surface_fields(label: str, value: object) -> None:
    for field_name in _iter_field_names(value):
        normalized = field_name.lower()
        if any(fragment in normalized for fragment in UNSAFE_SURFACE_FIELD_FRAGMENTS):
            raise ValueError(f"unsafe surface field in {label}: {field_name}")


def _iter_field_names(value: object) -> tuple[str, ...]:
    if hasattr(value, "__dataclass_fields__") and not isinstance(value, type):
        keys: list[str] = []
        dataclass_field_names = tuple(value.__dataclass_fields__)
        for field_name in dataclass_field_names:
            keys.append(field_name)
            keys.extend(_iter_field_names(getattr(value, field_name)))
        for key, item in vars(value).items():
            if key not in dataclass_field_names:
                keys.append(key)
                keys.extend(_iter_field_names(item))
        return tuple(keys)
    if isinstance(value, dict):
        keys = []
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("candidate field names must be strings")
            keys.append(key)
            keys.extend(_iter_field_names(item))
        return tuple(keys)
    if isinstance(value, (tuple, list)):
        keys = []
        for item in value:
            keys.extend(_iter_field_names(item))
        return tuple(keys)
    if hasattr(value, "__dict__"):
        keys = []
        for key, item in vars(value).items():
            keys.append(key)
            keys.extend(_iter_field_names(item))
        return tuple(keys)
    return ()


def _require_probability(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value < ZERO or decimal_value > ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return decimal_value


def _require_positive_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value <= 0:
        raise ValueError(f"{field_name} must be positive")
    return decimal_value


def _require_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value < 0:
        raise ValueError(f"{field_name} must be nonnegative")
    return decimal_value


def _require_decimal(field_name: str, value: object) -> Decimal:
    if isinstance(value, float):
        raise ValueError(f"{field_name} must not be a float")
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return _six_places(value)


def _six_places(value: Decimal) -> Decimal:
    return value.quantize(Decimal("0.000001"))


def _abs_decimal(value: Decimal) -> Decimal:
    if value < 0:
        return -value
    return value


def _require_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in STATUSES:
        raise ValueError(f"{field_name} must be pass, watch, or blocked")


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str or not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical string")
    _reject_sensitive_value(field_name, value)


def _require_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    _reject_sensitive_value(field_name, value)


def _require_hard_flags(label: str, value: object) -> None:
    if _optional_attr(value, "paper_only") is not True:
        raise ValueError(f"{label} must be paper_only")
    if _optional_attr(value, "report_only") is not True:
        raise ValueError(f"{label} must be report_only")
    if _optional_attr(value, "readonly") is not True:
        raise ValueError(f"{label} must be readonly")


def _reject_sensitive_value(field_name: str, value: str) -> None:
    lowered = value.lower()
    if any(fragment in lowered for fragment in SENSITIVE_STRING_FRAGMENTS):
        raise ValueError(f"{field_name} contains sensitive material")


def _reject_unsafe_public_value(field_name: str, value: str) -> None:
    lowered = value.lower()
    if any(fragment in lowered for fragment in SENSITIVE_STRING_FRAGMENTS):
        raise ValueError(f"unsafe public value in {field_name}")
