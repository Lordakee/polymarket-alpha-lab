"""Pure report-only source publication lag score for candidate decisions."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping
from dataclasses import asdict, dataclass, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal, ROUND_HALF_EVEN, localcontext
from typing import Any

from polymarket_alpha_lab.team_paper_guard import (
    json_ready_no_floats,
    require_paper_only_flags,
)


DEFAULT_CANDIDATE_DECISION_SOURCE_LAG_SCORE_CONFIG_VERSION = (
    "candidate-decision-source-lag-score-v0"
)
SOURCE_LAG_STATUSES = ("pass", "watch", "block")

QUANTUM = Decimal("0.000001")
COUNT_QUANTUM = Decimal("1")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
FIVE = Decimal("5.000000")
SECONDS_PER_DAY = Decimal("86400")
MICROSECONDS_PER_SECOND = Decimal("1000000")
SECONDS_PER_MINUTE = Decimal("60")
DECIMAL_CONTEXT_PRECISION = 64

_RAW_CANDIDATE_PUBLIC_TERMS = (
    "candidate_id",
    "candidateid",
    "raw_candidate_id",
    "raw_candidate_ref",
    "candidate_slug",
)
_RAW_MARKET_PUBLIC_TERMS = (
    "condition_id",
    "market_id",
    "market_slug",
    "market_question",
    "question",
)
_SOURCE_REFERENCE_PUBLIC_TERMS = (
    "source_ref",
    "source_refs",
    "source_url",
    "source_uri",
    "source_text",
    "source_excerpt",
    "source_title",
    "raw_text",
    "url",
    "http://",
    "https://",
    "www.",
    "://",
    "source-ref:",
    "source_ref:",
    "source-url:",
    "postgres://",
    "postgresql://",
    "mysql://",
    "sqlite://",
    "dsn=",
)
_UNSAFE_LIVE_PUBLIC_TERMS = (
    "api_key",
    "api-key",
    "auth",
    "bearer",
    "buy",
    "connection_string",
    "credential",
    "database",
    "jwt",
    "oauth",
    "order",
    "password",
    "position size",
    "position sizing",
    "position-size",
    "position-sizing",
    "position_size",
    "private_key",
    "private-key",
    "recommend",
    "secret",
    "sell",
    "session",
    "table",
    "table_name",
    "tablename",
    "token",
    "trade",
    "trading",
    "wallet",
)
_PUBLIC_STATUS_ALIASES = ("ready", "blocked", "matched", "supported")


@dataclass(frozen=True)
class CandidateDecisionSourceLagScoreConfig:
    config_version: str = DEFAULT_CANDIDATE_DECISION_SOURCE_LAG_SCORE_CONFIG_VERSION
    min_pass_source_lag_score: Decimal = Decimal("0.800000")
    min_watch_source_lag_score: Decimal = Decimal("0.500000")
    max_pass_publication_lag_minutes: Decimal = Decimal("30.000000")
    max_watch_publication_lag_minutes: Decimal = Decimal("240.000000")
    max_pass_source_after_signal_lag_minutes: Decimal = Decimal("15.000000")
    max_watch_source_after_signal_lag_minutes: Decimal = Decimal("180.000000")
    max_pass_research_signal_age_minutes: Decimal = Decimal("120.000000")
    max_watch_research_signal_age_minutes: Decimal = Decimal("720.000000")
    min_pass_critical_source_count: Decimal = Decimal("3")
    min_watch_critical_source_count: Decimal = Decimal("1")
    min_pass_independent_source_ratio: Decimal = Decimal("0.670000")
    min_watch_independent_source_ratio: Decimal = Decimal("0.340000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not CandidateDecisionSourceLagScoreConfig:
            raise TypeError(
                "CandidateDecisionSourceLagScoreConfig does not support subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type("config", self, CandidateDecisionSourceLagScoreConfig)
        object.__setattr__(
            self,
            "config_version",
            _require_canonical_string("config_version", self.config_version),
        )
        if self.config_version != DEFAULT_CANDIDATE_DECISION_SOURCE_LAG_SCORE_CONFIG_VERSION:
            raise ValueError("config_version must be the supported version")
        for field_name in (
            "min_pass_source_lag_score",
            "min_watch_source_lag_score",
            "min_pass_independent_source_ratio",
            "min_watch_independent_source_ratio",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_unit_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "max_pass_publication_lag_minutes",
            "max_watch_publication_lag_minutes",
            "max_pass_source_after_signal_lag_minutes",
            "max_watch_source_after_signal_lag_minutes",
            "max_pass_research_signal_age_minutes",
            "max_watch_research_signal_age_minutes",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in ("min_pass_critical_source_count", "min_watch_critical_source_count"):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_integral_decimal(
                    field_name,
                    getattr(self, field_name),
                ),
            )
        _validate_config(self)
        _require_phase_flags("config", self)
        reject_candidate_decision_source_lag_score_unsafe_payload(
            "source lag config",
            self,
        )


@dataclass(frozen=True)
class CandidateDecisionSourceLagScoreInput:
    generated_at: datetime
    information_event_at: datetime
    source_published_at: datetime
    research_signal_asof_at: datetime
    critical_source_count: Decimal
    independent_source_ratio: Decimal
    reason_codes: tuple[str, ...] = ()
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not CandidateDecisionSourceLagScoreInput:
            raise TypeError(
                "CandidateDecisionSourceLagScoreInput does not support subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type("input", self, CandidateDecisionSourceLagScoreInput)
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        object.__setattr__(
            self,
            "information_event_at",
            _as_utc("information_event_at", self.information_event_at),
        )
        object.__setattr__(
            self,
            "source_published_at",
            _as_utc("source_published_at", self.source_published_at),
        )
        object.__setattr__(
            self,
            "research_signal_asof_at",
            _as_utc("research_signal_asof_at", self.research_signal_asof_at),
        )
        if self.source_published_at < self.information_event_at:
            raise ValueError("source_published_at must not be before information_event_at")
        if self.source_published_at > self.generated_at:
            raise ValueError("source_published_at must not be after generated_at")
        if self.research_signal_asof_at > self.generated_at:
            raise ValueError("research_signal_asof_at must not be after generated_at")
        object.__setattr__(
            self,
            "critical_source_count",
            _normalize_nonnegative_integral_decimal(
                "critical_source_count",
                self.critical_source_count,
            ),
        )
        object.__setattr__(
            self,
            "independent_source_ratio",
            _normalize_unit_decimal(
                "independent_source_ratio",
                self.independent_source_ratio,
            ),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, allow_empty=True),
        )
        _require_phase_flags("input", self)
        reject_candidate_decision_source_lag_score_unsafe_payload(
            "source lag input",
            self,
        )


@dataclass(frozen=True)
class CandidateDecisionSourceLagScoreReport:
    generated_at: datetime
    config_version: str
    min_pass_source_lag_score: Decimal
    min_watch_source_lag_score: Decimal
    max_pass_publication_lag_minutes: Decimal
    max_watch_publication_lag_minutes: Decimal
    max_pass_source_after_signal_lag_minutes: Decimal
    max_watch_source_after_signal_lag_minutes: Decimal
    max_pass_research_signal_age_minutes: Decimal
    max_watch_research_signal_age_minutes: Decimal
    min_pass_critical_source_count: Decimal
    min_watch_critical_source_count: Decimal
    min_pass_independent_source_ratio: Decimal
    min_watch_independent_source_ratio: Decimal
    information_event_at: datetime
    source_published_at: datetime
    research_signal_asof_at: datetime
    publication_lag_minutes: Decimal
    source_after_signal_lag_minutes: Decimal
    research_signal_age_minutes: Decimal
    critical_source_count: Decimal
    independent_source_ratio: Decimal
    publication_lag_component: Decimal
    source_after_signal_lag_component: Decimal
    research_signal_freshness_component: Decimal
    source_count_coverage_component: Decimal
    independence_coverage_component: Decimal
    source_lag_score: Decimal
    lag_status: str
    hard_blocker_codes: tuple[str, ...]
    reason_codes: tuple[str, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not CandidateDecisionSourceLagScoreReport:
            raise TypeError(
                "CandidateDecisionSourceLagScoreReport does not support subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type("report", self, CandidateDecisionSourceLagScoreReport)
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        object.__setattr__(
            self,
            "information_event_at",
            _as_utc("information_event_at", self.information_event_at),
        )
        object.__setattr__(
            self,
            "source_published_at",
            _as_utc("source_published_at", self.source_published_at),
        )
        object.__setattr__(
            self,
            "research_signal_asof_at",
            _as_utc("research_signal_asof_at", self.research_signal_asof_at),
        )
        object.__setattr__(
            self,
            "config_version",
            _require_canonical_string("config_version", self.config_version),
        )
        if self.config_version != DEFAULT_CANDIDATE_DECISION_SOURCE_LAG_SCORE_CONFIG_VERSION:
            raise ValueError("config_version must be the supported version")
        for field_name in (
            "min_pass_source_lag_score",
            "min_watch_source_lag_score",
            "min_pass_independent_source_ratio",
            "min_watch_independent_source_ratio",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_unit_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "max_pass_publication_lag_minutes",
            "max_watch_publication_lag_minutes",
            "max_pass_source_after_signal_lag_minutes",
            "max_watch_source_after_signal_lag_minutes",
            "max_pass_research_signal_age_minutes",
            "max_watch_research_signal_age_minutes",
            "publication_lag_minutes",
            "source_after_signal_lag_minutes",
            "research_signal_age_minutes",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "min_pass_critical_source_count",
            "min_watch_critical_source_count",
            "critical_source_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_integral_decimal(
                    field_name,
                    getattr(self, field_name),
                ),
            )
        for field_name in (
            "independent_source_ratio",
            "publication_lag_component",
            "source_after_signal_lag_component",
            "research_signal_freshness_component",
            "source_count_coverage_component",
            "independence_coverage_component",
            "source_lag_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_unit_decimal(field_name, getattr(self, field_name)),
            )
        _require_choice("lag_status", self.lag_status, SOURCE_LAG_STATUSES)
        object.__setattr__(
            self,
            "hard_blocker_codes",
            _normalize_reason_codes(
                "hard_blocker_codes",
                self.hard_blocker_codes,
                allow_empty=True,
            ),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, allow_empty=False),
        )
        _validate_report(self)
        _require_phase_flags("report", self)
        reject_candidate_decision_source_lag_score_unsafe_payload(
            "source lag report",
            self,
        )
        expected_digest = _report_digest(self)
        if self.derived_validation_digest:
            _require_digest("derived_validation_digest", self.derived_validation_digest)
            if self.derived_validation_digest != expected_digest:
                raise ValueError("derived_validation_digest must match report fields")
        else:
            object.__setattr__(self, "derived_validation_digest", expected_digest)

    @property
    def payload(self) -> dict[str, Any]:
        return candidate_decision_source_lag_score_payload(self)


def build_candidate_decision_source_lag_score_report(
    score_input: CandidateDecisionSourceLagScoreInput,
    *,
    config: CandidateDecisionSourceLagScoreConfig | None = None,
) -> CandidateDecisionSourceLagScoreReport:
    if type(score_input) is not CandidateDecisionSourceLagScoreInput:
        raise ValueError("score_input must be a CandidateDecisionSourceLagScoreInput")
    report_config = config or CandidateDecisionSourceLagScoreConfig()
    if type(report_config) is not CandidateDecisionSourceLagScoreConfig:
        raise ValueError("config must be a CandidateDecisionSourceLagScoreConfig")
    _require_phase_flags("input", score_input)
    _require_phase_flags("config", report_config)
    reject_candidate_decision_source_lag_score_unsafe_payload(
        "source lag input",
        score_input,
    )
    reject_candidate_decision_source_lag_score_unsafe_payload(
        "source lag config",
        report_config,
    )
    return CandidateDecisionSourceLagScoreReport(
        **_report_values(score_input, report_config),
    )


def candidate_decision_source_lag_score_payload(
    report: CandidateDecisionSourceLagScoreReport,
) -> dict[str, Any]:
    if type(report) is not CandidateDecisionSourceLagScoreReport:
        raise ValueError("report must be a CandidateDecisionSourceLagScoreReport")
    _require_phase_flags("report", report)
    _validate_report(report)
    if report.derived_validation_digest != _report_digest(report):
        raise ValueError("derived_validation_digest must match report fields")
    reject_candidate_decision_source_lag_score_unsafe_payload(
        "source lag report",
        report,
    )
    payload = json_ready_no_floats(report)
    if type(payload) is not dict:
        raise ValueError("payload must be a dict")
    validate_candidate_decision_source_lag_score_public_payload(payload)
    return payload


def validate_candidate_decision_source_lag_score_public_payload(payload: object) -> None:
    if type(payload) is not dict:
        raise ValueError("public payload must be a JSON object")
    _reject_public_numbers(payload)
    _reject_public_status_aliases(payload)
    reject_candidate_decision_source_lag_score_unsafe_payload(
        "source lag public payload",
        payload,
    )


def reject_candidate_decision_source_lag_score_unsafe_payload(
    label: str,
    payload: object,
) -> None:
    for path, item in _iter_public_strings(payload):
        lowered = item.lower()
        if any(term in lowered for term in _RAW_CANDIDATE_PUBLIC_TERMS):
            raise ValueError(f"raw candidate public payload entry in {label}: {path}")
        if any(term in lowered for term in _RAW_MARKET_PUBLIC_TERMS):
            raise ValueError(f"market public payload entry in {label}: {path}")
        if any(term in lowered for term in _UNSAFE_LIVE_PUBLIC_TERMS):
            raise ValueError(f"unsafe live surface public payload entry in {label}: {path}")
        if any(term in lowered for term in _SOURCE_REFERENCE_PUBLIC_TERMS):
            raise ValueError(f"source public payload entry in {label}: {path}")


def _report_values(
    score_input: CandidateDecisionSourceLagScoreInput,
    config: CandidateDecisionSourceLagScoreConfig,
) -> dict[str, object]:
    publication_lag = _minutes_between(
        score_input.source_published_at,
        score_input.information_event_at,
    )
    source_after_signal_lag = _max_zero_minutes_between(
        score_input.source_published_at,
        score_input.research_signal_asof_at,
    )
    research_signal_age = _minutes_between(
        score_input.generated_at,
        score_input.research_signal_asof_at,
    )
    publication_component = _lower_is_better_component(
        publication_lag,
        config.max_pass_publication_lag_minutes,
        config.max_watch_publication_lag_minutes,
    )
    source_after_signal_component = _lower_is_better_component(
        source_after_signal_lag,
        config.max_pass_source_after_signal_lag_minutes,
        config.max_watch_source_after_signal_lag_minutes,
    )
    research_age_component = _lower_is_better_component(
        research_signal_age,
        config.max_pass_research_signal_age_minutes,
        config.max_watch_research_signal_age_minutes,
    )
    source_count_component = _coverage_component(
        score_input.critical_source_count,
        config.min_watch_critical_source_count,
        config.min_pass_critical_source_count,
    )
    independence_component = _coverage_component(
        score_input.independent_source_ratio,
        config.min_watch_independent_source_ratio,
        config.min_pass_independent_source_ratio,
    )
    source_lag_score = _source_lag_score(
        publication_component,
        source_after_signal_component,
        research_age_component,
        source_count_component,
        independence_component,
    )
    hard_blockers = _hard_blocker_codes(
        publication_lag,
        source_after_signal_lag,
        research_signal_age,
        score_input.critical_source_count,
        score_input.independent_source_ratio,
        source_lag_score,
        config,
    )
    lag_status = _lag_status(source_lag_score, hard_blockers, config)
    reason_codes = _reason_codes(
        score_input.reason_codes,
        publication_lag,
        source_after_signal_lag,
        research_signal_age,
        score_input.critical_source_count,
        score_input.independent_source_ratio,
        source_lag_score,
        lag_status,
        config,
    )
    return {
        "generated_at": score_input.generated_at,
        "config_version": config.config_version,
        "min_pass_source_lag_score": config.min_pass_source_lag_score,
        "min_watch_source_lag_score": config.min_watch_source_lag_score,
        "max_pass_publication_lag_minutes": config.max_pass_publication_lag_minutes,
        "max_watch_publication_lag_minutes": config.max_watch_publication_lag_minutes,
        "max_pass_source_after_signal_lag_minutes": (
            config.max_pass_source_after_signal_lag_minutes
        ),
        "max_watch_source_after_signal_lag_minutes": (
            config.max_watch_source_after_signal_lag_minutes
        ),
        "max_pass_research_signal_age_minutes": config.max_pass_research_signal_age_minutes,
        "max_watch_research_signal_age_minutes": (
            config.max_watch_research_signal_age_minutes
        ),
        "min_pass_critical_source_count": config.min_pass_critical_source_count,
        "min_watch_critical_source_count": config.min_watch_critical_source_count,
        "min_pass_independent_source_ratio": config.min_pass_independent_source_ratio,
        "min_watch_independent_source_ratio": config.min_watch_independent_source_ratio,
        "information_event_at": score_input.information_event_at,
        "source_published_at": score_input.source_published_at,
        "research_signal_asof_at": score_input.research_signal_asof_at,
        "publication_lag_minutes": publication_lag,
        "source_after_signal_lag_minutes": source_after_signal_lag,
        "research_signal_age_minutes": research_signal_age,
        "critical_source_count": score_input.critical_source_count,
        "independent_source_ratio": score_input.independent_source_ratio,
        "publication_lag_component": publication_component,
        "source_after_signal_lag_component": source_after_signal_component,
        "research_signal_freshness_component": research_age_component,
        "source_count_coverage_component": source_count_component,
        "independence_coverage_component": independence_component,
        "source_lag_score": source_lag_score,
        "lag_status": lag_status,
        "hard_blocker_codes": hard_blockers,
        "reason_codes": reason_codes,
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }


def _lower_is_better_component(
    value: Decimal,
    pass_threshold: Decimal,
    watch_threshold: Decimal,
) -> Decimal:
    if value <= pass_threshold:
        return ONE
    if value >= watch_threshold:
        return ZERO
    numerator = _subtract_nonnegative("lag_component_numerator", watch_threshold, value)
    denominator = _subtract_nonnegative(
        "lag_component_denominator",
        watch_threshold,
        pass_threshold,
    )
    return _safe_unit_ratio(numerator, denominator)


def _coverage_component(value: Decimal, watch_threshold: Decimal, pass_threshold: Decimal) -> Decimal:
    if value >= pass_threshold:
        return ONE
    if value < watch_threshold:
        return ZERO
    numerator = _subtract_nonnegative("coverage_component_numerator", value, watch_threshold)
    denominator = _subtract_nonnegative(
        "coverage_component_denominator",
        pass_threshold,
        watch_threshold,
    )
    return _safe_unit_ratio(numerator, denominator)


def _source_lag_score(
    publication_lag_component: Decimal,
    source_after_signal_lag_component: Decimal,
    research_signal_freshness_component: Decimal,
    source_count_coverage_component: Decimal,
    independence_coverage_component: Decimal,
) -> Decimal:
    with localcontext() as context:
        context.prec = DECIMAL_CONTEXT_PRECISION
        context.rounding = ROUND_HALF_EVEN
        return _normalize_unit_decimal(
            "source_lag_score",
            (
                publication_lag_component
                + source_after_signal_lag_component
                + research_signal_freshness_component
                + source_count_coverage_component
                + independence_coverage_component
            )
            / FIVE,
        )


def _hard_blocker_codes(
    publication_lag: Decimal,
    source_after_signal_lag: Decimal,
    research_signal_age: Decimal,
    critical_source_count: Decimal,
    independent_source_ratio: Decimal,
    source_lag_score: Decimal,
    config: CandidateDecisionSourceLagScoreConfig | CandidateDecisionSourceLagScoreReport,
) -> tuple[str, ...]:
    codes: list[str] = []
    if publication_lag > config.max_watch_publication_lag_minutes:
        codes.append("publication_lag_block")
    if source_after_signal_lag > config.max_watch_source_after_signal_lag_minutes:
        codes.append("source_after_signal_lag_block")
    if research_signal_age > config.max_watch_research_signal_age_minutes:
        codes.append("research_signal_age_block")
    if critical_source_count < config.min_watch_critical_source_count:
        codes.append("critical_source_count_block")
    if independent_source_ratio < config.min_watch_independent_source_ratio:
        codes.append("independent_source_ratio_block")
    if source_lag_score < config.min_watch_source_lag_score:
        codes.append("source_lag_score_block")
    return tuple(codes)


def _lag_status(
    source_lag_score: Decimal,
    hard_blocker_codes: tuple[str, ...],
    config: CandidateDecisionSourceLagScoreConfig | CandidateDecisionSourceLagScoreReport,
) -> str:
    if hard_blocker_codes:
        return "block"
    if source_lag_score < config.min_pass_source_lag_score:
        return "watch"
    return "pass"


def _reason_codes(
    existing_reason_codes: tuple[str, ...],
    publication_lag: Decimal,
    source_after_signal_lag: Decimal,
    research_signal_age: Decimal,
    critical_source_count: Decimal,
    independent_source_ratio: Decimal,
    source_lag_score: Decimal,
    lag_status: str,
    config: CandidateDecisionSourceLagScoreConfig | CandidateDecisionSourceLagScoreReport,
) -> tuple[str, ...]:
    codes = [
        *existing_reason_codes,
        f"source_lag_{lag_status}",
        _lower_is_better_reason(
            "publication_lag",
            publication_lag,
            config.max_pass_publication_lag_minutes,
            config.max_watch_publication_lag_minutes,
        ),
        _lower_is_better_reason(
            "source_after_signal_lag",
            source_after_signal_lag,
            config.max_pass_source_after_signal_lag_minutes,
            config.max_watch_source_after_signal_lag_minutes,
        ),
        _lower_is_better_reason(
            "research_signal_age",
            research_signal_age,
            config.max_pass_research_signal_age_minutes,
            config.max_watch_research_signal_age_minutes,
        ),
        _coverage_reason(
            "critical_source_count",
            critical_source_count,
            config.min_watch_critical_source_count,
            config.min_pass_critical_source_count,
        ),
        _coverage_reason(
            "independent_source_ratio",
            independent_source_ratio,
            config.min_watch_independent_source_ratio,
            config.min_pass_independent_source_ratio,
        ),
        _score_reason(source_lag_score, config),
    ]
    return _normalize_reason_codes("reason_codes", tuple(codes), allow_empty=False)


def _lower_is_better_reason(
    name: str,
    value: Decimal,
    pass_threshold: Decimal,
    watch_threshold: Decimal,
) -> str:
    if value <= pass_threshold:
        return f"{name}_pass"
    if value <= watch_threshold:
        return f"{name}_watch"
    return f"{name}_block"


def _coverage_reason(
    name: str,
    value: Decimal,
    watch_threshold: Decimal,
    pass_threshold: Decimal,
) -> str:
    if value >= pass_threshold:
        return f"{name}_pass"
    if value >= watch_threshold:
        return f"{name}_watch"
    return f"{name}_block"


def _score_reason(
    source_lag_score: Decimal,
    config: CandidateDecisionSourceLagScoreConfig | CandidateDecisionSourceLagScoreReport,
) -> str:
    if source_lag_score >= config.min_pass_source_lag_score:
        return "source_lag_score_pass"
    if source_lag_score >= config.min_watch_source_lag_score:
        return "source_lag_score_watch"
    return "source_lag_score_block"


def _validate_config(
    config: CandidateDecisionSourceLagScoreConfig | CandidateDecisionSourceLagScoreReport,
) -> None:
    if config.min_watch_source_lag_score > config.min_pass_source_lag_score:
        raise ValueError("min_watch_source_lag_score must not exceed pass threshold")
    for pass_field, watch_field in (
        ("max_pass_publication_lag_minutes", "max_watch_publication_lag_minutes"),
        (
            "max_pass_source_after_signal_lag_minutes",
            "max_watch_source_after_signal_lag_minutes",
        ),
        ("max_pass_research_signal_age_minutes", "max_watch_research_signal_age_minutes"),
    ):
        if getattr(config, pass_field) > getattr(config, watch_field):
            raise ValueError(f"{pass_field} must not exceed {watch_field}")
    if config.min_watch_critical_source_count > config.min_pass_critical_source_count:
        raise ValueError("min_watch_critical_source_count must not exceed pass threshold")
    if config.min_watch_independent_source_ratio > config.min_pass_independent_source_ratio:
        raise ValueError("min_watch_independent_source_ratio must not exceed pass threshold")


def _validate_report(report: CandidateDecisionSourceLagScoreReport) -> None:
    _validate_config(report)
    if report.source_published_at < report.information_event_at:
        raise ValueError("source_published_at must not be before information_event_at")
    if report.source_published_at > report.generated_at:
        raise ValueError("source_published_at must not be after generated_at")
    if report.research_signal_asof_at > report.generated_at:
        raise ValueError("research_signal_asof_at must not be after generated_at")
    expected_publication_lag = _minutes_between(
        report.source_published_at,
        report.information_event_at,
    )
    if report.publication_lag_minutes != expected_publication_lag:
        raise ValueError("publication_lag_minutes must match source timestamps")
    expected_source_after_signal_lag = _max_zero_minutes_between(
        report.source_published_at,
        report.research_signal_asof_at,
    )
    if report.source_after_signal_lag_minutes != expected_source_after_signal_lag:
        raise ValueError("source_after_signal_lag_minutes must match source timestamps")
    expected_research_signal_age = _minutes_between(
        report.generated_at,
        report.research_signal_asof_at,
    )
    if report.research_signal_age_minutes != expected_research_signal_age:
        raise ValueError("research_signal_age_minutes must match generated_at")
    expected_publication_component = _lower_is_better_component(
        report.publication_lag_minutes,
        report.max_pass_publication_lag_minutes,
        report.max_watch_publication_lag_minutes,
    )
    if report.publication_lag_component != expected_publication_component:
        raise ValueError("publication_lag_component must match thresholds")
    expected_source_after_signal_component = _lower_is_better_component(
        report.source_after_signal_lag_minutes,
        report.max_pass_source_after_signal_lag_minutes,
        report.max_watch_source_after_signal_lag_minutes,
    )
    if report.source_after_signal_lag_component != expected_source_after_signal_component:
        raise ValueError("source_after_signal_lag_component must match thresholds")
    expected_research_signal_component = _lower_is_better_component(
        report.research_signal_age_minutes,
        report.max_pass_research_signal_age_minutes,
        report.max_watch_research_signal_age_minutes,
    )
    if report.research_signal_freshness_component != expected_research_signal_component:
        raise ValueError("research_signal_freshness_component must match thresholds")
    expected_count_component = _coverage_component(
        report.critical_source_count,
        report.min_watch_critical_source_count,
        report.min_pass_critical_source_count,
    )
    if report.source_count_coverage_component != expected_count_component:
        raise ValueError("source_count_coverage_component must match critical_source_count")
    expected_independence_component = _coverage_component(
        report.independent_source_ratio,
        report.min_watch_independent_source_ratio,
        report.min_pass_independent_source_ratio,
    )
    if report.independence_coverage_component != expected_independence_component:
        raise ValueError("independence_coverage_component must match independent_source_ratio")
    expected_score = _source_lag_score(
        report.publication_lag_component,
        report.source_after_signal_lag_component,
        report.research_signal_freshness_component,
        report.source_count_coverage_component,
        report.independence_coverage_component,
    )
    if report.source_lag_score != expected_score:
        raise ValueError("source_lag_score must match component scores")
    expected_hard_blockers = _hard_blocker_codes(
        report.publication_lag_minutes,
        report.source_after_signal_lag_minutes,
        report.research_signal_age_minutes,
        report.critical_source_count,
        report.independent_source_ratio,
        report.source_lag_score,
        report,
    )
    if report.hard_blocker_codes != expected_hard_blockers:
        raise ValueError("hard_blocker_codes must match thresholds")
    expected_status = _lag_status(report.source_lag_score, expected_hard_blockers, report)
    if report.lag_status != expected_status:
        raise ValueError("lag_status must match thresholds")
    expected_generated_reason_codes = _reason_codes(
        (),
        report.publication_lag_minutes,
        report.source_after_signal_lag_minutes,
        report.research_signal_age_minutes,
        report.critical_source_count,
        report.independent_source_ratio,
        report.source_lag_score,
        report.lag_status,
        report,
    )
    if report.reason_codes[-len(expected_generated_reason_codes) :] != (
        expected_generated_reason_codes
    ):
        raise ValueError("reason_codes must end with generated lag reasons")


def _safe_unit_ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator <= ZERO:
        return ONE if numerator >= ZERO else ZERO
    with localcontext() as context:
        context.prec = DECIMAL_CONTEXT_PRECISION
        context.rounding = ROUND_HALF_EVEN
        return _normalize_unit_decimal("ratio", numerator / denominator)


def _subtract_nonnegative(field_name: str, minuend: Decimal, subtrahend: Decimal) -> Decimal:
    with localcontext() as context:
        context.prec = DECIMAL_CONTEXT_PRECISION
        context.rounding = ROUND_HALF_EVEN
        return _normalize_nonnegative_decimal(field_name, minuend - subtrahend)


def _max_zero_minutes_between(later: datetime, earlier: datetime) -> Decimal:
    if later <= earlier:
        return ZERO
    return _minutes_between(later, earlier)


def _minutes_between(later: datetime, earlier: datetime) -> Decimal:
    delta = later - earlier
    with localcontext() as context:
        context.prec = DECIMAL_CONTEXT_PRECISION
        context.rounding = ROUND_HALF_EVEN
        seconds = (
            Decimal(delta.days) * SECONDS_PER_DAY
            + Decimal(delta.seconds)
            + (Decimal(delta.microseconds) / MICROSECONDS_PER_SECOND)
        )
        return _normalize_nonnegative_decimal(
            "lag_minutes",
            seconds / SECONDS_PER_MINUTE,
        )


def _normalize_nonnegative_integral_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_nonnegative_decimal(field_name, value)
    with localcontext() as context:
        context.prec = DECIMAL_CONTEXT_PRECISION
        context.rounding = ROUND_HALF_EVEN
        integral = normalized.quantize(COUNT_QUANTUM, rounding=ROUND_HALF_EVEN)
    if normalized != integral:
        raise ValueError(f"{field_name} must be integral")
    return integral


def _normalize_unit_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_nonnegative_decimal(field_name, value)
    if normalized > ONE:
        raise ValueError(f"{field_name} must be no greater than 1")
    return normalized


def _normalize_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _normalize_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    with localcontext() as context:
        context.prec = DECIMAL_CONTEXT_PRECISION
        context.rounding = ROUND_HALF_EVEN
        return value.quantize(QUANTUM, rounding=ROUND_HALF_EVEN)


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _normalize_reason_codes(
    field_name: str,
    value: object,
    *,
    allow_empty: bool,
) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ValueError(f"{field_name} must be a tuple")
    if not value and not allow_empty:
        raise ValueError(f"{field_name} must not be empty")
    codes: list[str] = []
    for item in value:
        codes.append(_require_canonical_string(field_name, item))
    if len(set(codes)) != len(codes):
        raise ValueError(f"{field_name} must be unique")
    return tuple(codes)


def _require_canonical_string(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")
    return value


def _require_choice(field_name: str, value: object, choices: tuple[str, ...]) -> None:
    if type(value) is not str or value not in choices:
        raise ValueError(f"{field_name} must be pass, watch, or block")


def _require_exact_type(label: str, value: object, expected_type: type[object]) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{label} must be a {expected_type.__name__}")


def _require_phase_flags(label: str, value: object) -> None:
    require_paper_only_flags(f"source lag {label}", value)


def _require_digest(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if len(value) != 64 or any(char not in "0123456789abcdef" for char in value):
        raise ValueError(f"{field_name} must be a lowercase sha256 digest")


def _report_digest(report: CandidateDecisionSourceLagScoreReport) -> str:
    values = asdict(report)
    values.pop("derived_validation_digest", None)
    return _digest_from_values(values)


def _digest_from_values(values: Mapping[str, object]) -> str:
    payload = json_ready_no_floats(values)
    validate_candidate_decision_source_lag_score_public_payload(payload)
    canonical = json.dumps(
        payload,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _reject_public_numbers(value: object) -> None:
    if type(value) in (float, int, Decimal, datetime):
        raise ValueError("public payload numeric values must be decimal strings")
    if type(value) is dict:
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("public payload keys must be strings")
            _reject_public_numbers(item)
    elif type(value) is list:
        for item in value:
            _reject_public_numbers(item)


def _reject_public_status_aliases(payload: object) -> None:
    for path, item in _iter_public_strings(payload):
        lowered = item.lower()
        if path.rsplit(".", 1)[-1].lower() == lowered:
            continue
        if any(alias == lowered for alias in _PUBLIC_STATUS_ALIASES):
            raise ValueError(f"public status value must be pass, watch, or block: {path}")
        if path.lower().endswith("status") and lowered not in SOURCE_LAG_STATUSES:
            raise ValueError(f"public status value must be pass, watch, or block: {path}")


def _iter_public_strings(value: object, path: str = "$") -> tuple[tuple[str, str], ...]:
    if is_dataclass(value) and not isinstance(value, type):
        return _iter_public_strings(asdict(value), path)
    if type(value) is dict:
        entries: list[tuple[str, str]] = []
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("public payload keys must be strings")
            item_path = f"{path}.{key}"
            entries.append((item_path, key))
            entries.extend(_iter_public_strings(item, item_path))
        return tuple(entries)
    if type(value) in (list, tuple):
        entries = []
        for index, item in enumerate(value):
            entries.extend(_iter_public_strings(item, f"{path}[{index}]"))
        return tuple(entries)
    if type(value) is str:
        return ((path, value),)
    return ()


__all__ = (
    "DEFAULT_CANDIDATE_DECISION_SOURCE_LAG_SCORE_CONFIG_VERSION",
    "SOURCE_LAG_STATUSES",
    "CandidateDecisionSourceLagScoreConfig",
    "CandidateDecisionSourceLagScoreInput",
    "CandidateDecisionSourceLagScoreReport",
    "build_candidate_decision_source_lag_score_report",
    "candidate_decision_source_lag_score_payload",
    "validate_candidate_decision_source_lag_score_public_payload",
    "reject_candidate_decision_source_lag_score_unsafe_payload",
)
