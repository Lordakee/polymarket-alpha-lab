"""Pure readonly forecast evidence conflict penalty v10."""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, localcontext
from typing import Any


DEFAULT_CONFIG_VERSION = "strategy-forecast-evidence-conflict-penalty-v10"
DECIMAL_CONTEXT = Context(prec=64)
QUANTUM = Decimal("0.000001")
COUNT_QUANTUM = Decimal("1")
ZERO = Decimal("0")
ONE = Decimal("1")
SECONDS_PER_HOUR = Decimal("3600")
SECONDS_PER_DAY = Decimal("86400")
MICROSECONDS_PER_SECOND = Decimal("1000000")

CLEAR_STATUS = "clear"
WATCH_STATUS = "watch"
BLOCKED_STATUS = "blocked"
STATUSES = (CLEAR_STATUS, WATCH_STATUS, BLOCKED_STATUS)

CLEAR_REASON = "evidence_conflict_penalty_clear"
REPORT_EMPTY_REASON = "strategy_forecast_evidence_conflict_penalty_empty"
PENALTY_APPLIED_REASON = "penalty_applied"
CONTRADICTION_REASON = "contradiction_rate_present"
RELIABILITY_REASON = "reliability_spread_high"
SOURCE_FAMILY_REASON = "source_family_concentration_high"
RECENCY_REASON = "recency_mismatch_high"
URGENCY_REASON = "resolution_urgency_high"

HEX_DIGITS = frozenset("0123456789abcdef")
FLAG_FIELDS = ("paper_only", "report_only", "readonly")
TEXT_RISK_PARTS = (
    ("au", "th"),
    ("wal", "let"),
    ("acc", "ount"),
    ("ord", "er"),
    ("tr", "ade"),
    ("bro", "ker"),
    ("sig", "ning"),
    ("sub", "mit"),
    ("can", "cel"),
    ("net", "work"),
    ("data", "base"),
    ("op", "en("),
    ("req", "uests"),
    ("sock", "et"),
    ("psy", "copg"),
    ("s", "ql"),
)


@dataclass(frozen=True)
class StrategyForecastEvidenceConflictPenaltyConfig:
    config_version: str = DEFAULT_CONFIG_VERSION
    contradiction_probability_gap: Decimal = Decimal("0.150000")
    recency_mismatch_full_gap_hours: Decimal = Decimal("48.000000")
    urgency_window_hours: Decimal = Decimal("24.000000")
    watch_penalty_score: Decimal = Decimal("0.350000")
    blocked_penalty_score: Decimal = Decimal("0.700000")
    contradiction_rate_weight: Decimal = Decimal("0.350000")
    reliability_spread_weight: Decimal = Decimal("0.200000")
    source_family_concentration_weight: Decimal = Decimal("0.150000")
    recency_mismatch_weight: Decimal = Decimal("0.150000")
    resolution_urgency_weight: Decimal = Decimal("0.150000")
    high_reliability_spread: Decimal = Decimal("0.500000")
    high_source_family_concentration: Decimal = Decimal("0.600000")
    high_recency_mismatch: Decimal = Decimal("0.750000")
    high_resolution_urgency: Decimal = Decimal("0.500000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError("StrategyForecastEvidenceConflictPenaltyConfig is final")

    def __post_init__(self) -> None:
        _require_exact_instance(
            "config",
            self,
            StrategyForecastEvidenceConflictPenaltyConfig,
        )
        _require_canonical_string("config_version", self.config_version)
        if self.config_version != DEFAULT_CONFIG_VERSION:
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "contradiction_probability_gap",
            "recency_mismatch_full_gap_hours",
            "urgency_window_hours",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_positive_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "watch_penalty_score",
            "blocked_penalty_score",
            "contradiction_rate_weight",
            "reliability_spread_weight",
            "source_family_concentration_weight",
            "recency_mismatch_weight",
            "resolution_urgency_weight",
            "high_reliability_spread",
            "high_source_family_concentration",
            "high_recency_mismatch",
            "high_resolution_urgency",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_probability(field_name, getattr(self, field_name)),
            )
        if self.watch_penalty_score > self.blocked_penalty_score:
            raise ValueError("watch_penalty_score must not exceed blocked_penalty_score")
        _validate_weight_total(self)
        _require_hard_flags("config", self)
        _reject_unsafe_public_payload("config", self)


@dataclass(frozen=True)
class StrategyForecastEvidenceConflictEvidence:
    forecast_id: str
    source_id: str
    source_family: str
    probability: Decimal
    reliability: Decimal
    observed_at: datetime
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError("StrategyForecastEvidenceConflictEvidence is final")

    def __post_init__(self) -> None:
        _require_exact_instance(
            "evidence",
            self,
            StrategyForecastEvidenceConflictEvidence,
        )
        for field_name in ("forecast_id", "source_id", "source_family"):
            _require_canonical_string(field_name, getattr(self, field_name))
        object.__setattr__(
            self,
            "probability",
            _require_probability("probability", self.probability),
        )
        object.__setattr__(
            self,
            "reliability",
            _require_probability("reliability", self.reliability),
        )
        object.__setattr__(
            self,
            "observed_at",
            _as_utc("observed_at", self.observed_at),
        )
        _require_hard_flags("evidence", self)
        _reject_unsafe_public_payload("evidence", self)


@dataclass(frozen=True)
class StrategyForecastEvidenceConflictForecast:
    forecast_id: str
    base_probability: Decimal
    resolution_at: datetime
    evidence: tuple[StrategyForecastEvidenceConflictEvidence, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError("StrategyForecastEvidenceConflictForecast is final")

    def __post_init__(self) -> None:
        _require_exact_instance(
            "forecast",
            self,
            StrategyForecastEvidenceConflictForecast,
        )
        _require_canonical_string("forecast_id", self.forecast_id)
        object.__setattr__(
            self,
            "base_probability",
            _require_probability("base_probability", self.base_probability),
        )
        object.__setattr__(
            self,
            "resolution_at",
            _as_utc("resolution_at", self.resolution_at),
        )
        object.__setattr__(self, "evidence", _normalize_evidence_rows(self))
        _require_hard_flags("forecast", self)
        _reject_unsafe_public_payload("forecast", self)


@dataclass(frozen=True)
class StrategyForecastEvidenceConflictPenaltyResult:
    generated_at: datetime
    config_version: str
    forecast: StrategyForecastEvidenceConflictForecast
    evidence_count: Decimal
    conflicting_evidence_count: Decimal
    contradiction_rate: Decimal
    reliability_spread: Decimal
    source_family_concentration: Decimal
    recency_mismatch: Decimal
    resolution_urgency: Decimal
    penalty_score: Decimal
    penalty_amount: Decimal
    adjusted_probability: Decimal
    status: str
    reason_codes: tuple[str, ...]
    validation_digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError("StrategyForecastEvidenceConflictPenaltyResult is final")

    def __post_init__(self) -> None:
        _require_exact_instance(
            "result",
            self,
            StrategyForecastEvidenceConflictPenaltyResult,
        )
        object.__setattr__(
            self,
            "generated_at",
            _as_utc("generated_at", self.generated_at),
        )
        _require_canonical_string("config_version", self.config_version)
        if self.config_version != DEFAULT_CONFIG_VERSION:
            raise ValueError("config_version must be the supported config version")
        _require_exact_instance(
            "forecast",
            self.forecast,
            StrategyForecastEvidenceConflictForecast,
        )
        for field_name in ("evidence_count", "conflicting_evidence_count"):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_whole_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "contradiction_rate",
            "reliability_spread",
            "source_family_concentration",
            "recency_mismatch",
            "resolution_urgency",
            "penalty_score",
            "penalty_amount",
            "adjusted_probability",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_probability(field_name, getattr(self, field_name)),
            )
        _require_member("status", self.status, STATUSES)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        object.__setattr__(
            self,
            "validation_digest",
            _require_validation_digest("validation_digest", self.validation_digest),
        )
        _validate_result(self, StrategyForecastEvidenceConflictPenaltyConfig())
        _require_hard_flags("result", self)
        _reject_unsafe_public_payload("result", self)


@dataclass(frozen=True)
class StrategyForecastEvidenceConflictPenaltyReport:
    generated_at: datetime
    config_version: str
    result_count: Decimal
    clear_result_count: Decimal
    watch_result_count: Decimal
    blocked_result_count: Decimal
    max_penalty_score: Decimal | None
    mean_penalty_score: Decimal | None
    status: str
    reason_codes: tuple[str, ...]
    results: tuple[StrategyForecastEvidenceConflictPenaltyResult, ...]
    validation_digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError("StrategyForecastEvidenceConflictPenaltyReport is final")

    def __post_init__(self) -> None:
        _require_exact_instance(
            "report",
            self,
            StrategyForecastEvidenceConflictPenaltyReport,
        )
        object.__setattr__(
            self,
            "generated_at",
            _as_utc("generated_at", self.generated_at),
        )
        _require_canonical_string("config_version", self.config_version)
        if self.config_version != DEFAULT_CONFIG_VERSION:
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "result_count",
            "clear_result_count",
            "watch_result_count",
            "blocked_result_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_whole_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in ("max_penalty_score", "mean_penalty_score"):
            value = getattr(self, field_name)
            if value is not None:
                object.__setattr__(self, field_name, _require_probability(field_name, value))
        _require_member("status", self.status, STATUSES)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        object.__setattr__(self, "results", _normalize_results(self.results))
        object.__setattr__(
            self,
            "validation_digest",
            _require_validation_digest("validation_digest", self.validation_digest),
        )
        _validate_report(self)
        _require_hard_flags("report", self)
        _reject_unsafe_public_payload("report", self)


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


def build_strategy_forecast_evidence_conflict_penalty_v10(
    forecasts: object,
    *,
    config: StrategyForecastEvidenceConflictPenaltyConfig | None = None,
    generated_at: datetime,
) -> StrategyForecastEvidenceConflictPenaltyReport:
    cfg = config or StrategyForecastEvidenceConflictPenaltyConfig()
    _require_exact_instance("config", cfg, StrategyForecastEvidenceConflictPenaltyConfig)
    generated_at_utc = _as_utc("generated_at", generated_at)
    forecast_rows = _normalize_forecasts(forecasts)
    results = tuple(
        _result_for_forecast(forecast, config=cfg, generated_at=generated_at_utc)
        for forecast in forecast_rows
    )
    return _report_for_results(results, config=cfg, generated_at=generated_at_utc)


def strategy_forecast_evidence_conflict_penalty_report_data(
    report: StrategyForecastEvidenceConflictPenaltyReport | dict[str, Any],
) -> dict[str, Any]:
    if type(report) is StrategyForecastEvidenceConflictPenaltyReport:
        _require_hard_flags("report", report)
        _reject_unsafe_public_payload("report", report)
        payload = _json_ready(report)
    elif type(report) is dict:
        _reject_unsafe_public_payload("payload", report)
        payload = _json_ready(report)
    else:
        raise ValueError(
            "report must be a StrategyForecastEvidenceConflictPenaltyReport",
        )
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    _require_hard_flags("payload", _DictFlags(payload))
    _reject_unsafe_public_payload("payload", payload)
    return payload


def _result_for_forecast(
    forecast: StrategyForecastEvidenceConflictForecast,
    *,
    config: StrategyForecastEvidenceConflictPenaltyConfig,
    generated_at: datetime,
) -> StrategyForecastEvidenceConflictPenaltyResult:
    if forecast.resolution_at < generated_at:
        raise ValueError("resolution_at must not be before generated_at")
    for item in forecast.evidence:
        if item.observed_at > generated_at:
            raise ValueError("observed_at must not be after generated_at")

    evidence_count = _count_decimal(len(forecast.evidence))
    conflicting_evidence_count = _count_decimal(
        sum(
            1
            for item in forecast.evidence
            if _abs_decimal(item.probability - forecast.base_probability)
            >= config.contradiction_probability_gap
        ),
    )
    contradiction_rate = _ratio(conflicting_evidence_count, evidence_count)
    reliability_spread = _reliability_spread(forecast.evidence)
    source_family_concentration = _source_family_concentration(forecast.evidence)
    recency_mismatch = _recency_mismatch(
        forecast.evidence,
        config=config,
        generated_at=generated_at,
    )
    resolution_urgency = _resolution_urgency(
        forecast.resolution_at,
        config=config,
        generated_at=generated_at,
    )
    penalty_score = _penalty_score(
        contradiction_rate=contradiction_rate,
        reliability_spread=reliability_spread,
        source_family_concentration=source_family_concentration,
        recency_mismatch=recency_mismatch,
        resolution_urgency=resolution_urgency,
        config=config,
    )
    penalty_amount = _penalty_amount(forecast.base_probability, penalty_score)
    adjusted_probability = _clamp_probability(forecast.base_probability - penalty_amount)
    status = _result_status(penalty_score, config)
    reason_codes = _result_reason_codes(
        contradiction_rate=contradiction_rate,
        reliability_spread=reliability_spread,
        source_family_concentration=source_family_concentration,
        recency_mismatch=recency_mismatch,
        resolution_urgency=resolution_urgency,
        config=config,
    )
    digest = _result_validation_digest(
        generated_at=generated_at,
        config_version=config.config_version,
        forecast=forecast,
        evidence_count=evidence_count,
        conflicting_evidence_count=conflicting_evidence_count,
        contradiction_rate=contradiction_rate,
        reliability_spread=reliability_spread,
        source_family_concentration=source_family_concentration,
        recency_mismatch=recency_mismatch,
        resolution_urgency=resolution_urgency,
        penalty_score=penalty_score,
        penalty_amount=penalty_amount,
        adjusted_probability=adjusted_probability,
        status=status,
        reason_codes=reason_codes,
    )
    return StrategyForecastEvidenceConflictPenaltyResult(
        generated_at=generated_at,
        config_version=config.config_version,
        forecast=forecast,
        evidence_count=evidence_count,
        conflicting_evidence_count=conflicting_evidence_count,
        contradiction_rate=contradiction_rate,
        reliability_spread=reliability_spread,
        source_family_concentration=source_family_concentration,
        recency_mismatch=recency_mismatch,
        resolution_urgency=resolution_urgency,
        penalty_score=penalty_score,
        penalty_amount=penalty_amount,
        adjusted_probability=adjusted_probability,
        status=status,
        reason_codes=reason_codes,
        validation_digest=digest,
    )


def _report_for_results(
    results: tuple[StrategyForecastEvidenceConflictPenaltyResult, ...],
    *,
    config: StrategyForecastEvidenceConflictPenaltyConfig,
    generated_at: datetime,
) -> StrategyForecastEvidenceConflictPenaltyReport:
    result_count = _count_decimal(len(results))
    clear_result_count = _count_decimal(
        sum(1 for result in results if result.status == CLEAR_STATUS),
    )
    watch_result_count = _count_decimal(
        sum(1 for result in results if result.status == WATCH_STATUS),
    )
    blocked_result_count = _count_decimal(
        sum(1 for result in results if result.status == BLOCKED_STATUS),
    )
    max_penalty_score = max((result.penalty_score for result in results), default=None)
    mean_penalty_score = _mean(result.penalty_score for result in results)
    status = _report_status(results)
    reason_codes = _report_reason_codes(results, status)
    digest = _report_validation_digest(
        generated_at=generated_at,
        config_version=config.config_version,
        result_count=result_count,
        clear_result_count=clear_result_count,
        watch_result_count=watch_result_count,
        blocked_result_count=blocked_result_count,
        max_penalty_score=max_penalty_score,
        mean_penalty_score=mean_penalty_score,
        status=status,
        reason_codes=reason_codes,
        results=results,
    )
    return StrategyForecastEvidenceConflictPenaltyReport(
        generated_at=generated_at,
        config_version=config.config_version,
        result_count=result_count,
        clear_result_count=clear_result_count,
        watch_result_count=watch_result_count,
        blocked_result_count=blocked_result_count,
        max_penalty_score=max_penalty_score,
        mean_penalty_score=mean_penalty_score,
        status=status,
        reason_codes=reason_codes,
        results=results,
        validation_digest=digest,
    )


def _validate_result(
    result: StrategyForecastEvidenceConflictPenaltyResult,
    config: StrategyForecastEvidenceConflictPenaltyConfig,
) -> None:
    if result.forecast.resolution_at < result.generated_at:
        raise ValueError("resolution_at must not be before generated_at")
    for item in result.forecast.evidence:
        if item.observed_at > result.generated_at:
            raise ValueError("observed_at must not be after generated_at")

    expected_evidence_count = _count_decimal(len(result.forecast.evidence))
    expected_conflicting_evidence_count = _count_decimal(
        sum(
            1
            for item in result.forecast.evidence
            if _abs_decimal(item.probability - result.forecast.base_probability)
            >= config.contradiction_probability_gap
        ),
    )
    expected_contradiction_rate = _ratio(
        expected_conflicting_evidence_count,
        expected_evidence_count,
    )
    expected_reliability_spread = _reliability_spread(result.forecast.evidence)
    expected_source_family_concentration = _source_family_concentration(
        result.forecast.evidence,
    )
    expected_recency_mismatch = _recency_mismatch(
        result.forecast.evidence,
        config=config,
        generated_at=result.generated_at,
    )
    expected_resolution_urgency = _resolution_urgency(
        result.forecast.resolution_at,
        config=config,
        generated_at=result.generated_at,
    )
    expected_penalty_score = _penalty_score(
        contradiction_rate=expected_contradiction_rate,
        reliability_spread=expected_reliability_spread,
        source_family_concentration=expected_source_family_concentration,
        recency_mismatch=expected_recency_mismatch,
        resolution_urgency=expected_resolution_urgency,
        config=config,
    )
    expected_penalty_amount = _penalty_amount(
        result.forecast.base_probability,
        expected_penalty_score,
    )
    expected_adjusted_probability = _clamp_probability(
        result.forecast.base_probability - expected_penalty_amount,
    )
    expected_status = _result_status(expected_penalty_score, config)
    expected_reason_codes = _result_reason_codes(
        contradiction_rate=expected_contradiction_rate,
        reliability_spread=expected_reliability_spread,
        source_family_concentration=expected_source_family_concentration,
        recency_mismatch=expected_recency_mismatch,
        resolution_urgency=expected_resolution_urgency,
        config=config,
    )
    expected_validation_digest = _result_validation_digest(
        generated_at=result.generated_at,
        config_version=result.config_version,
        forecast=result.forecast,
        evidence_count=expected_evidence_count,
        conflicting_evidence_count=expected_conflicting_evidence_count,
        contradiction_rate=expected_contradiction_rate,
        reliability_spread=expected_reliability_spread,
        source_family_concentration=expected_source_family_concentration,
        recency_mismatch=expected_recency_mismatch,
        resolution_urgency=expected_resolution_urgency,
        penalty_score=expected_penalty_score,
        penalty_amount=expected_penalty_amount,
        adjusted_probability=expected_adjusted_probability,
        status=expected_status,
        reason_codes=expected_reason_codes,
    )

    if result.evidence_count != expected_evidence_count:
        raise ValueError("evidence_count must match forecast evidence")
    if result.conflicting_evidence_count != expected_conflicting_evidence_count:
        raise ValueError("conflicting_evidence_count must match forecast evidence")
    if result.contradiction_rate != expected_contradiction_rate:
        raise ValueError("contradiction_rate must match derived validation")
    if result.reliability_spread != expected_reliability_spread:
        raise ValueError("reliability_spread must match derived validation")
    if result.source_family_concentration != expected_source_family_concentration:
        raise ValueError("source_family_concentration must match derived validation")
    if result.recency_mismatch != expected_recency_mismatch:
        raise ValueError("recency_mismatch must match derived validation")
    if result.resolution_urgency != expected_resolution_urgency:
        raise ValueError("resolution_urgency must match derived validation")
    if result.penalty_score != expected_penalty_score:
        raise ValueError("penalty_score must match derived validation")
    if result.penalty_amount != expected_penalty_amount:
        raise ValueError("penalty_amount must match derived validation")
    if result.adjusted_probability != expected_adjusted_probability:
        raise ValueError("adjusted_probability must match derived validation")
    if result.status != expected_status:
        raise ValueError("status must match derived validation")
    if result.reason_codes != expected_reason_codes:
        raise ValueError("reason_codes must match derived validation")
    if result.validation_digest != expected_validation_digest:
        raise ValueError("validation_digest must match")


def _validate_report(report: StrategyForecastEvidenceConflictPenaltyReport) -> None:
    expected_result_count = _count_decimal(len(report.results))
    expected_clear_result_count = _count_decimal(
        sum(1 for result in report.results if result.status == CLEAR_STATUS),
    )
    expected_watch_result_count = _count_decimal(
        sum(1 for result in report.results if result.status == WATCH_STATUS),
    )
    expected_blocked_result_count = _count_decimal(
        sum(1 for result in report.results if result.status == BLOCKED_STATUS),
    )
    expected_max_penalty_score = max(
        (result.penalty_score for result in report.results),
        default=None,
    )
    expected_mean_penalty_score = _mean(
        (result.penalty_score for result in report.results),
    )
    expected_status = _report_status(report.results)
    expected_reason_codes = _report_reason_codes(report.results, expected_status)
    expected_validation_digest = _report_validation_digest(
        generated_at=report.generated_at,
        config_version=report.config_version,
        result_count=expected_result_count,
        clear_result_count=expected_clear_result_count,
        watch_result_count=expected_watch_result_count,
        blocked_result_count=expected_blocked_result_count,
        max_penalty_score=expected_max_penalty_score,
        mean_penalty_score=expected_mean_penalty_score,
        status=expected_status,
        reason_codes=expected_reason_codes,
        results=report.results,
    )
    if report.result_count != expected_result_count:
        raise ValueError("result_count must match results")
    if report.clear_result_count != expected_clear_result_count:
        raise ValueError("clear_result_count must match results")
    if report.watch_result_count != expected_watch_result_count:
        raise ValueError("watch_result_count must match results")
    if report.blocked_result_count != expected_blocked_result_count:
        raise ValueError("blocked_result_count must match results")
    if report.max_penalty_score != expected_max_penalty_score:
        raise ValueError("max_penalty_score must match results")
    if report.mean_penalty_score != expected_mean_penalty_score:
        raise ValueError("mean_penalty_score must match results")
    if report.status != expected_status:
        raise ValueError("status must match results")
    if report.reason_codes != expected_reason_codes:
        raise ValueError("reason_codes must match results")
    if report.validation_digest != expected_validation_digest:
        raise ValueError("validation_digest must match")


def _normalize_forecasts(
    forecasts: object,
) -> tuple[StrategyForecastEvidenceConflictForecast, ...]:
    _reject_float_tree("forecasts", forecasts)
    if not isinstance(forecasts, (list, tuple)):
        raise ValueError("forecasts must be a list or tuple")
    normalized = tuple(forecasts)
    seen: set[str] = set()
    for forecast in normalized:
        _require_exact_instance(
            "forecast",
            forecast,
            StrategyForecastEvidenceConflictForecast,
        )
        if forecast.forecast_id in seen:
            raise ValueError("duplicate forecast_id")
        seen.add(forecast.forecast_id)
    return tuple(sorted(normalized, key=lambda item: item.forecast_id))


def _normalize_evidence_rows(
    forecast: StrategyForecastEvidenceConflictForecast,
) -> tuple[StrategyForecastEvidenceConflictEvidence, ...]:
    _reject_float_tree("evidence", forecast.evidence)
    if not isinstance(forecast.evidence, (list, tuple)):
        raise ValueError("evidence must be a list or tuple")
    normalized = tuple(forecast.evidence)
    seen: set[str] = set()
    for item in normalized:
        _require_exact_instance("evidence", item, StrategyForecastEvidenceConflictEvidence)
        if item.forecast_id != forecast.forecast_id:
            raise ValueError("evidence forecast_id must match forecast_id")
        if item.source_id in seen:
            raise ValueError("duplicate source_id")
        seen.add(item.source_id)
    return tuple(sorted(normalized, key=lambda item: item.source_id))


def _reliability_spread(
    rows: tuple[StrategyForecastEvidenceConflictEvidence, ...],
) -> Decimal:
    if not rows:
        return ZERO.quantize(QUANTUM)
    values = tuple(row.reliability for row in rows)
    return _quantize(max(values) - min(values))


def _source_family_concentration(
    rows: tuple[StrategyForecastEvidenceConflictEvidence, ...],
) -> Decimal:
    if not rows:
        return ZERO.quantize(QUANTUM)
    counts: dict[str, Decimal] = {}
    for row in rows:
        counts[row.source_family] = counts.get(row.source_family, ZERO) + ONE
    return _ratio(max(counts.values()), _count_decimal(len(rows)))


def _recency_mismatch(
    rows: tuple[StrategyForecastEvidenceConflictEvidence, ...],
    *,
    config: StrategyForecastEvidenceConflictPenaltyConfig,
    generated_at: datetime,
) -> Decimal:
    if len(rows) < 2:
        return ZERO.quantize(QUANTUM)
    ages = tuple(_hours_between(generated_at, row.observed_at) for row in rows)
    return _ratio(max(ages) - min(ages), config.recency_mismatch_full_gap_hours)


def _resolution_urgency(
    resolution_at: datetime,
    *,
    config: StrategyForecastEvidenceConflictPenaltyConfig,
    generated_at: datetime,
) -> Decimal:
    remaining_hours = _hours_between(resolution_at, generated_at)
    if remaining_hours >= config.urgency_window_hours:
        return ZERO.quantize(QUANTUM)
    with localcontext(DECIMAL_CONTEXT):
        return _clamp_probability(
            (config.urgency_window_hours - remaining_hours) / config.urgency_window_hours,
        )


def _penalty_score(
    *,
    contradiction_rate: Decimal,
    reliability_spread: Decimal,
    source_family_concentration: Decimal,
    recency_mismatch: Decimal,
    resolution_urgency: Decimal,
    config: StrategyForecastEvidenceConflictPenaltyConfig,
) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return _clamp_probability(
            (contradiction_rate * config.contradiction_rate_weight)
            + (reliability_spread * config.reliability_spread_weight)
            + (
                source_family_concentration
                * config.source_family_concentration_weight
            )
            + (recency_mismatch * config.recency_mismatch_weight)
            + (resolution_urgency * config.resolution_urgency_weight),
        )


def _penalty_amount(base_probability: Decimal, penalty_score: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        exposure_above_even = base_probability - Decimal("0.500000")
        if exposure_above_even <= ZERO:
            return ZERO.quantize(QUANTUM)
        return _quantize(exposure_above_even * penalty_score)


def _result_status(
    penalty_score: Decimal,
    config: StrategyForecastEvidenceConflictPenaltyConfig,
) -> str:
    if penalty_score >= config.blocked_penalty_score:
        return BLOCKED_STATUS
    if penalty_score >= config.watch_penalty_score:
        return WATCH_STATUS
    return CLEAR_STATUS


def _result_reason_codes(
    *,
    contradiction_rate: Decimal,
    reliability_spread: Decimal,
    source_family_concentration: Decimal,
    recency_mismatch: Decimal,
    resolution_urgency: Decimal,
    config: StrategyForecastEvidenceConflictPenaltyConfig,
) -> tuple[str, ...]:
    codes: list[str] = []
    if contradiction_rate > ZERO:
        codes.append(CONTRADICTION_REASON)
    if reliability_spread >= config.high_reliability_spread:
        codes.append(RELIABILITY_REASON)
    if source_family_concentration >= config.high_source_family_concentration:
        codes.append(SOURCE_FAMILY_REASON)
    if recency_mismatch >= config.high_recency_mismatch:
        codes.append(RECENCY_REASON)
    if resolution_urgency >= config.high_resolution_urgency:
        codes.append(URGENCY_REASON)
    if not codes:
        codes.append(CLEAR_REASON)
    return tuple(codes)


def _report_status(
    results: tuple[StrategyForecastEvidenceConflictPenaltyResult, ...],
) -> str:
    if any(result.status == BLOCKED_STATUS for result in results):
        return BLOCKED_STATUS
    if any(result.status == WATCH_STATUS for result in results):
        return WATCH_STATUS
    return CLEAR_STATUS


def _report_reason_codes(
    results: tuple[StrategyForecastEvidenceConflictPenaltyResult, ...],
    status: str,
) -> tuple[str, ...]:
    if not results:
        return (REPORT_EMPTY_REASON,)
    codes = [f"strategy_forecast_evidence_conflict_penalty_{status}"]
    for result in results:
        for reason_code in result.reason_codes:
            if reason_code != CLEAR_REASON and reason_code not in codes:
                codes.append(reason_code)
    codes.append(PENALTY_APPLIED_REASON)
    return tuple(codes)


def _count_decimal(value: int) -> Decimal:
    return Decimal(str(value))


def _mean(values: object) -> Decimal | None:
    rows = tuple(values)
    if not rows:
        return None
    with localcontext(DECIMAL_CONTEXT):
        return _quantize(sum(rows, ZERO) / _count_decimal(len(rows)))


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO:
        return ZERO.quantize(QUANTUM)
    with localcontext(DECIMAL_CONTEXT):
        return _clamp_probability(numerator / denominator)


def _hours_between(later: datetime, earlier: datetime) -> Decimal:
    delta = later - earlier
    total_microseconds = (
        (
            (Decimal(str(delta.days)) * SECONDS_PER_DAY)
            + Decimal(str(delta.seconds))
        )
        * MICROSECONDS_PER_SECOND
    ) + Decimal(str(delta.microseconds))
    with localcontext(DECIMAL_CONTEXT):
        return total_microseconds / MICROSECONDS_PER_SECOND / SECONDS_PER_HOUR


def _validate_weight_total(
    config: StrategyForecastEvidenceConflictPenaltyConfig,
) -> None:
    total = (
        config.contradiction_rate_weight
        + config.reliability_spread_weight
        + config.source_family_concentration_weight
        + config.recency_mismatch_weight
        + config.resolution_urgency_weight
    )
    if total != ONE.quantize(QUANTUM):
        raise ValueError("penalty weights must sum to 1")


def _result_validation_digest(
    *,
    generated_at: datetime,
    config_version: str,
    forecast: StrategyForecastEvidenceConflictForecast,
    evidence_count: Decimal,
    conflicting_evidence_count: Decimal,
    contradiction_rate: Decimal,
    reliability_spread: Decimal,
    source_family_concentration: Decimal,
    recency_mismatch: Decimal,
    resolution_urgency: Decimal,
    penalty_score: Decimal,
    penalty_amount: Decimal,
    adjusted_probability: Decimal,
    status: str,
    reason_codes: tuple[str, ...],
) -> str:
    return _hash_payload(
        {
            "generated_at": generated_at,
            "config_version": config_version,
            "forecast": forecast,
            "evidence_count": evidence_count,
            "conflicting_evidence_count": conflicting_evidence_count,
            "contradiction_rate": contradiction_rate,
            "reliability_spread": reliability_spread,
            "source_family_concentration": source_family_concentration,
            "recency_mismatch": recency_mismatch,
            "resolution_urgency": resolution_urgency,
            "penalty_score": penalty_score,
            "penalty_amount": penalty_amount,
            "adjusted_probability": adjusted_probability,
            "status": status,
            "reason_codes": reason_codes,
            "paper_only": True,
            "report_only": True,
            "readonly": True,
        },
    )


def _report_validation_digest(
    *,
    generated_at: datetime,
    config_version: str,
    result_count: Decimal,
    clear_result_count: Decimal,
    watch_result_count: Decimal,
    blocked_result_count: Decimal,
    max_penalty_score: Decimal | None,
    mean_penalty_score: Decimal | None,
    status: str,
    reason_codes: tuple[str, ...],
    results: tuple[StrategyForecastEvidenceConflictPenaltyResult, ...],
) -> str:
    return _hash_payload(
        {
            "generated_at": generated_at,
            "config_version": config_version,
            "result_count": result_count,
            "clear_result_count": clear_result_count,
            "watch_result_count": watch_result_count,
            "blocked_result_count": blocked_result_count,
            "max_penalty_score": max_penalty_score,
            "mean_penalty_score": mean_penalty_score,
            "status": status,
            "reason_codes": reason_codes,
            "result_digests": tuple(result.validation_digest for result in results),
            "paper_only": True,
            "report_only": True,
            "readonly": True,
        },
    )


def _hash_payload(payload: dict[str, Any]) -> str:
    ready = _json_ready(payload)
    text = json.dumps(ready, separators=(",", ":"), sort_keys=True)
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _normalize_results(
    values: object,
) -> tuple[StrategyForecastEvidenceConflictPenaltyResult, ...]:
    if type(values) is not tuple:
        raise ValueError("results must be a tuple")
    previous_id: str | None = None
    normalized = tuple(values)
    for result in normalized:
        _require_exact_instance(
            "result",
            result,
            StrategyForecastEvidenceConflictPenaltyResult,
        )
        forecast_id = result.forecast.forecast_id
        if previous_id is not None and previous_id > forecast_id:
            raise ValueError("results must be sorted")
        previous_id = forecast_id
    return normalized


def _normalize_reason_codes(field_name: str, value: object) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ValueError(f"{field_name} must be a tuple")
    if not value:
        raise ValueError(f"{field_name} must not be empty")
    seen: set[str] = set()
    normalized: list[str] = []
    for reason_code in value:
        _require_canonical_string(field_name, reason_code)
        if reason_code not in seen:
            normalized.append(reason_code)
            seen.add(reason_code)
    return tuple(normalized)


def _require_exact_instance(field_name: str, value: object, expected_type: type) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{field_name} must be a {expected_type.__name__}")


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in FLAG_FIELDS:
        if getattr(value, field_name, None) is not True:
            raise ValueError(f"{field_name} must be True")


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a non-empty canonical string")
    if _has_text_risk(value):
        raise ValueError(f"{field_name} has unsafe value")


def _require_member(
    field_name: str,
    value: object,
    allowed_values: tuple[str, ...],
) -> None:
    _require_canonical_string(field_name, value)
    if value not in allowed_values:
        raise ValueError(f"{field_name} must be a known value")


def _require_probability(field_name: str, value: object) -> Decimal:
    decimal_value = _require_nonnegative_decimal(field_name, value)
    if decimal_value > ONE:
        raise ValueError(f"{field_name} must be at most 1")
    return decimal_value


def _require_positive_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_nonnegative_decimal(field_name, value)
    if decimal_value <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return decimal_value


def _require_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    decimal_value = value.quantize(QUANTUM)
    if decimal_value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return decimal_value


def _require_nonnegative_whole_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    decimal_value = value.quantize(COUNT_QUANTUM)
    if value != decimal_value:
        raise ValueError(f"{field_name} must be a whole number")
    if decimal_value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return decimal_value


def _require_validation_digest(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a validation digest")
    if len(value) != 64 or any(character not in HEX_DIGITS for character in value):
        raise ValueError(f"{field_name} must be a lowercase sha256 hex digest")
    return value


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _reject_float_tree(label: str, value: object) -> None:
    if isinstance(value, float):
        raise ValueError(f"{label} must not contain float values")
    if is_dataclass(value) and not isinstance(value, type):
        for field_name in value.__dataclass_fields__:
            _reject_float_tree(f"{label}.{field_name}", getattr(value, field_name))
        return
    if isinstance(value, dict):
        for key, item in value.items():
            _reject_float_tree(f"{label}.{key}", item)
        return
    if isinstance(value, (list, tuple)):
        for index, item in enumerate(value):
            _reject_float_tree(f"{label}.{index}", item)


def _reject_unsafe_public_payload(label: str, value: object, path: str = "") -> None:
    if is_dataclass(value) and not isinstance(value, type):
        _reject_unsafe_public_payload(label, asdict(value), path)
        return
    if type(value) is str:
        if _has_text_risk(value):
            raise ValueError(f"{path or label} has unsafe value")
        return
    if type(value) is Decimal:
        if not value.is_finite():
            raise ValueError(f"{path or label} must be finite")
        return
    if isinstance(value, Decimal):
        raise ValueError(f"{path or label} must be exactly Decimal")
    if isinstance(value, datetime):
        if type(value) is not datetime:
            raise ValueError(f"{path or label} must be a datetime")
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError(f"{path or label} must be timezone-aware")
        return
    if value is None or type(value) is bool:
        return
    if isinstance(value, float):
        raise ValueError("JSON value must not be a float")
    if type(value) is int:
        raise ValueError(f"{path or label} must use Decimal-derived string values")
    if isinstance(value, dict):
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            nested_path = key if not path else f"{path}.{key}"
            if _has_text_risk(key):
                raise ValueError(f"unsafe surface field in {label}: {key}")
            if key in FLAG_FIELDS and item is not True:
                raise ValueError(f"{nested_path} must be True")
            _reject_unsafe_public_payload(label, item, nested_path)
        return
    if isinstance(value, (list, tuple)):
        for index, item in enumerate(value):
            nested_path = f"{path}[{index}]" if path else f"{label}[{index}]"
            _reject_unsafe_public_payload(label, item, nested_path)
        return
    raise ValueError("value is not JSON serializable")


def _json_ready(value: Any) -> Any:
    if value is None:
        return None
    if type(value) is Decimal:
        if not value.is_finite():
            raise ValueError("JSON Decimal value must be finite")
        return str(value)
    if isinstance(value, Decimal):
        raise ValueError("JSON Decimal value must be exactly Decimal")
    if isinstance(value, datetime):
        if type(value) is not datetime:
            raise ValueError("JSON datetime value must be a datetime")
        return _as_utc("JSON datetime value", value).isoformat()
    if is_dataclass(value) and not isinstance(value, type):
        return _json_ready(asdict(value))
    if type(value) is bool:
        return value
    if isinstance(value, float):
        raise ValueError("JSON value must not be a float")
    if type(value) is int:
        raise ValueError("JSON numeric value must use Decimal-derived string values")
    if type(value) is str:
        return value
    if isinstance(value, tuple):
        return [_json_ready(item) for item in value]
    if isinstance(value, list):
        return [_json_ready(item) for item in value]
    if isinstance(value, dict):
        ready: dict[str, Any] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            ready[key] = _json_ready(item)
        return ready
    raise ValueError("value is not JSON serializable")


def _has_text_risk(value: str) -> bool:
    lowered = value.lower()
    return any("".join(parts) in lowered for parts in TEXT_RISK_PARTS)


def _quantize(value: Decimal) -> Decimal:
    return value.quantize(QUANTUM)


def _clamp_probability(value: Decimal) -> Decimal:
    if value <= ZERO:
        return ZERO.quantize(QUANTUM)
    if value >= ONE:
        return ONE.quantize(QUANTUM)
    return _quantize(value)


def _abs_decimal(value: Decimal) -> Decimal:
    if value < ZERO:
        return -value
    return value


__all__ = [
    "DEFAULT_CONFIG_VERSION",
    "StrategyForecastEvidenceConflictEvidence",
    "StrategyForecastEvidenceConflictForecast",
    "StrategyForecastEvidenceConflictPenaltyConfig",
    "StrategyForecastEvidenceConflictPenaltyReport",
    "StrategyForecastEvidenceConflictPenaltyResult",
    "build_strategy_forecast_evidence_conflict_penalty_v10",
    "strategy_forecast_evidence_conflict_penalty_report_data",
]
