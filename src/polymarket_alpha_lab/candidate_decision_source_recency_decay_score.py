"""Pure paper-only source recency decay score for candidate decisions."""

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


DEFAULT_CANDIDATE_DECISION_SOURCE_RECENCY_DECAY_SCORE_CONFIG_VERSION = (
    "candidate-decision-source-recency-decay-score-v0"
)
RECENCY_STATUSES = ("pass", "watch", "block")

QUANTUM = Decimal("0.000001")
COUNT_QUANTUM = Decimal("1")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
FIVE = Decimal("5.000000")
SECONDS_PER_DAY = Decimal("86400")
MICROSECONDS_PER_SECOND = Decimal("1000000")
SECONDS_PER_MINUTE = Decimal("60")
DECIMAL_CONTEXT_PRECISION = 64

_RAW_MARKET_PUBLIC_TERMS = (
    "candidate_id",
    "candidate_slug",
    "condition_id",
    "market_id",
    "market_slug",
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
)
_UNSAFE_LIVE_PUBLIC_TERMS = (
    "api_key",
    "auth",
    "bearer",
    "buy",
    "connection_string",
    "credential",
    "database",
    "dsn",
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
    "recommendation",
    "secret",
    "sell",
    "session",
    "table",
    "token",
    "trade",
    "trading",
    "wallet",
)
_PUBLIC_STATUS_ALIASES = ("ready", "blocked", "matched", "supported")


@dataclass(frozen=True)
class CandidateDecisionSourceRecencyDecayScoreConfig:
    config_version: str = (
        DEFAULT_CANDIDATE_DECISION_SOURCE_RECENCY_DECAY_SCORE_CONFIG_VERSION
    )
    min_pass_recency_decay_score: Decimal = Decimal("0.750000")
    min_watch_recency_decay_score: Decimal = Decimal("0.500000")
    max_pass_newest_source_age_minutes: Decimal = Decimal("60.000000")
    max_watch_newest_source_age_minutes: Decimal = Decimal("240.000000")
    max_pass_average_source_age_minutes: Decimal = Decimal("180.000000")
    max_watch_average_source_age_minutes: Decimal = Decimal("720.000000")
    max_pass_oldest_source_age_minutes: Decimal = Decimal("1440.000000")
    max_watch_oldest_source_age_minutes: Decimal = Decimal("2880.000000")
    min_pass_source_count: Decimal = Decimal("3")
    min_watch_source_count: Decimal = Decimal("1")
    min_pass_independent_source_ratio: Decimal = Decimal("0.670000")
    min_watch_independent_source_ratio: Decimal = Decimal("0.340000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not CandidateDecisionSourceRecencyDecayScoreConfig:
            raise TypeError(
                "CandidateDecisionSourceRecencyDecayScoreConfig does not support subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(
            "config",
            self,
            CandidateDecisionSourceRecencyDecayScoreConfig,
        )
        object.__setattr__(
            self,
            "config_version",
            _require_canonical_string("config_version", self.config_version),
        )
        if (
            self.config_version
            != DEFAULT_CANDIDATE_DECISION_SOURCE_RECENCY_DECAY_SCORE_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported version")
        for field_name in (
            "min_pass_recency_decay_score",
            "min_watch_recency_decay_score",
            "min_pass_independent_source_ratio",
            "min_watch_independent_source_ratio",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_unit_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "max_pass_newest_source_age_minutes",
            "max_watch_newest_source_age_minutes",
            "max_pass_average_source_age_minutes",
            "max_watch_average_source_age_minutes",
            "max_pass_oldest_source_age_minutes",
            "max_watch_oldest_source_age_minutes",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in ("min_pass_source_count", "min_watch_source_count"):
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
        reject_candidate_decision_source_recency_decay_score_unsafe_payload(
            "source recency decay config",
            self,
        )


@dataclass(frozen=True)
class CandidateDecisionSourceRecencyDecayScoreInput:
    generated_at: datetime
    newest_source_at: datetime
    oldest_source_at: datetime
    source_count: Decimal
    average_source_age_minutes: Decimal
    independent_source_ratio: Decimal
    reason_codes: tuple[str, ...] = ()
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not CandidateDecisionSourceRecencyDecayScoreInput:
            raise TypeError(
                "CandidateDecisionSourceRecencyDecayScoreInput does not support subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(
            "input",
            self,
            CandidateDecisionSourceRecencyDecayScoreInput,
        )
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        object.__setattr__(
            self,
            "newest_source_at",
            _as_utc("newest_source_at", self.newest_source_at),
        )
        object.__setattr__(
            self,
            "oldest_source_at",
            _as_utc("oldest_source_at", self.oldest_source_at),
        )
        if self.newest_source_at > self.generated_at:
            raise ValueError("newest_source_at must not be after generated_at")
        if self.oldest_source_at > self.newest_source_at:
            raise ValueError("oldest_source_at must not be after newest_source_at")
        object.__setattr__(
            self,
            "source_count",
            _normalize_nonnegative_integral_decimal("source_count", self.source_count),
        )
        object.__setattr__(
            self,
            "average_source_age_minutes",
            _normalize_nonnegative_decimal(
                "average_source_age_minutes",
                self.average_source_age_minutes,
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
        _validate_input(self)
        _require_phase_flags("input", self)
        reject_candidate_decision_source_recency_decay_score_unsafe_payload(
            "source recency decay input",
            self,
        )


@dataclass(frozen=True)
class CandidateDecisionSourceRecencyDecayScoreReport:
    generated_at: datetime
    config_version: str
    min_pass_recency_decay_score: Decimal
    min_watch_recency_decay_score: Decimal
    max_pass_newest_source_age_minutes: Decimal
    max_watch_newest_source_age_minutes: Decimal
    max_pass_average_source_age_minutes: Decimal
    max_watch_average_source_age_minutes: Decimal
    max_pass_oldest_source_age_minutes: Decimal
    max_watch_oldest_source_age_minutes: Decimal
    min_pass_source_count: Decimal
    min_watch_source_count: Decimal
    min_pass_independent_source_ratio: Decimal
    min_watch_independent_source_ratio: Decimal
    newest_source_at: datetime
    oldest_source_at: datetime
    source_count: Decimal
    newest_source_age_minutes: Decimal
    oldest_source_age_minutes: Decimal
    source_age_span_minutes: Decimal
    average_source_age_minutes: Decimal
    independent_source_ratio: Decimal
    newest_source_recency_component: Decimal
    average_source_recency_component: Decimal
    oldest_source_recency_component: Decimal
    source_count_coverage_component: Decimal
    independence_coverage_component: Decimal
    recency_decay_score: Decimal
    recency_status: str
    hard_blocker_codes: tuple[str, ...]
    reason_codes: tuple[str, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not CandidateDecisionSourceRecencyDecayScoreReport:
            raise TypeError(
                "CandidateDecisionSourceRecencyDecayScoreReport does not support subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(
            "report",
            self,
            CandidateDecisionSourceRecencyDecayScoreReport,
        )
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        object.__setattr__(
            self,
            "newest_source_at",
            _as_utc("newest_source_at", self.newest_source_at),
        )
        object.__setattr__(
            self,
            "oldest_source_at",
            _as_utc("oldest_source_at", self.oldest_source_at),
        )
        object.__setattr__(
            self,
            "config_version",
            _require_canonical_string("config_version", self.config_version),
        )
        if (
            self.config_version
            != DEFAULT_CANDIDATE_DECISION_SOURCE_RECENCY_DECAY_SCORE_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported version")
        for field_name in (
            "min_pass_recency_decay_score",
            "min_watch_recency_decay_score",
            "min_pass_independent_source_ratio",
            "min_watch_independent_source_ratio",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_unit_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "max_pass_newest_source_age_minutes",
            "max_watch_newest_source_age_minutes",
            "max_pass_average_source_age_minutes",
            "max_watch_average_source_age_minutes",
            "max_pass_oldest_source_age_minutes",
            "max_watch_oldest_source_age_minutes",
            "newest_source_age_minutes",
            "oldest_source_age_minutes",
            "source_age_span_minutes",
            "average_source_age_minutes",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in ("min_pass_source_count", "min_watch_source_count", "source_count"):
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
            "newest_source_recency_component",
            "average_source_recency_component",
            "oldest_source_recency_component",
            "source_count_coverage_component",
            "independence_coverage_component",
            "recency_decay_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_unit_decimal(field_name, getattr(self, field_name)),
            )
        _require_choice("recency_status", self.recency_status, RECENCY_STATUSES)
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
        reject_candidate_decision_source_recency_decay_score_unsafe_payload(
            "source recency decay report",
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
        return candidate_decision_source_recency_decay_score_payload(self)


def build_candidate_decision_source_recency_decay_score_report(
    score_input: CandidateDecisionSourceRecencyDecayScoreInput,
    *,
    config: CandidateDecisionSourceRecencyDecayScoreConfig | None = None,
) -> CandidateDecisionSourceRecencyDecayScoreReport:
    if type(score_input) is not CandidateDecisionSourceRecencyDecayScoreInput:
        raise ValueError(
            "score_input must be a CandidateDecisionSourceRecencyDecayScoreInput",
        )
    report_config = config or CandidateDecisionSourceRecencyDecayScoreConfig()
    if type(report_config) is not CandidateDecisionSourceRecencyDecayScoreConfig:
        raise ValueError(
            "config must be a CandidateDecisionSourceRecencyDecayScoreConfig",
        )
    _require_phase_flags("input", score_input)
    _require_phase_flags("config", report_config)
    reject_candidate_decision_source_recency_decay_score_unsafe_payload(
        "source recency decay input",
        score_input,
    )
    reject_candidate_decision_source_recency_decay_score_unsafe_payload(
        "source recency decay config",
        report_config,
    )
    values = _report_values(score_input, report_config)
    return CandidateDecisionSourceRecencyDecayScoreReport(**values)


def candidate_decision_source_recency_decay_score_payload(
    report: CandidateDecisionSourceRecencyDecayScoreReport,
) -> dict[str, Any]:
    if type(report) is not CandidateDecisionSourceRecencyDecayScoreReport:
        raise ValueError(
            "report must be a CandidateDecisionSourceRecencyDecayScoreReport",
        )
    _require_phase_flags("report", report)
    _validate_report(report)
    if report.derived_validation_digest != _report_digest(report):
        raise ValueError("derived_validation_digest must match report fields")
    reject_candidate_decision_source_recency_decay_score_unsafe_payload(
        "source recency decay report",
        report,
    )
    payload = json_ready_no_floats(report)
    if type(payload) is not dict:
        raise ValueError("payload must be a dict")
    validate_candidate_decision_source_recency_decay_score_public_payload(payload)
    return payload


def validate_candidate_decision_source_recency_decay_score_public_payload(
    payload: object,
) -> None:
    if type(payload) is not dict:
        raise ValueError("public payload must be a JSON object")
    _reject_public_numbers(payload)
    _reject_public_status_aliases(payload)
    reject_candidate_decision_source_recency_decay_score_unsafe_payload(
        "source recency decay public payload",
        payload,
    )


def reject_candidate_decision_source_recency_decay_score_unsafe_payload(
    label: str,
    payload: object,
) -> None:
    for path, item in _iter_public_strings(payload):
        lowered = item.lower()
        if any(term in lowered for term in _RAW_MARKET_PUBLIC_TERMS):
            raise ValueError(f"raw market public payload entry in {label}: {path}")
        if any(term in lowered for term in _SOURCE_REFERENCE_PUBLIC_TERMS):
            raise ValueError(f"source refs public payload entry in {label}: {path}")
        if any(term in lowered for term in _UNSAFE_LIVE_PUBLIC_TERMS):
            raise ValueError(f"unsafe live surface public payload entry in {label}: {path}")


def _report_values(
    score_input: CandidateDecisionSourceRecencyDecayScoreInput,
    config: CandidateDecisionSourceRecencyDecayScoreConfig,
) -> dict[str, object]:
    newest_age = _minutes_between(score_input.generated_at, score_input.newest_source_at)
    oldest_age = _minutes_between(score_input.generated_at, score_input.oldest_source_at)
    span = _subtract_nonnegative("source_age_span_minutes", oldest_age, newest_age)
    newest_component = _age_component(
        newest_age,
        config.max_pass_newest_source_age_minutes,
        config.max_watch_newest_source_age_minutes,
    )
    average_component = _age_component(
        score_input.average_source_age_minutes,
        config.max_pass_average_source_age_minutes,
        config.max_watch_average_source_age_minutes,
    )
    oldest_component = _age_component(
        oldest_age,
        config.max_pass_oldest_source_age_minutes,
        config.max_watch_oldest_source_age_minutes,
    )
    source_count_component = _coverage_component(
        score_input.source_count,
        config.min_watch_source_count,
        config.min_pass_source_count,
    )
    independence_component = _coverage_component(
        score_input.independent_source_ratio,
        config.min_watch_independent_source_ratio,
        config.min_pass_independent_source_ratio,
    )
    recency_decay_score = _recency_decay_score(
        newest_component,
        average_component,
        oldest_component,
        source_count_component,
        independence_component,
    )
    hard_blockers = _hard_blocker_codes(
        newest_age,
        score_input.average_source_age_minutes,
        oldest_age,
        score_input.source_count,
        score_input.independent_source_ratio,
        recency_decay_score,
        config,
    )
    recency_status = _recency_status(recency_decay_score, hard_blockers, config)
    reason_codes = _reason_codes(
        score_input.reason_codes,
        newest_age,
        score_input.average_source_age_minutes,
        oldest_age,
        score_input.source_count,
        score_input.independent_source_ratio,
        recency_decay_score,
        recency_status,
        config,
    )
    return {
        "generated_at": score_input.generated_at,
        "config_version": config.config_version,
        "min_pass_recency_decay_score": config.min_pass_recency_decay_score,
        "min_watch_recency_decay_score": config.min_watch_recency_decay_score,
        "max_pass_newest_source_age_minutes": config.max_pass_newest_source_age_minutes,
        "max_watch_newest_source_age_minutes": config.max_watch_newest_source_age_minutes,
        "max_pass_average_source_age_minutes": config.max_pass_average_source_age_minutes,
        "max_watch_average_source_age_minutes": config.max_watch_average_source_age_minutes,
        "max_pass_oldest_source_age_minutes": config.max_pass_oldest_source_age_minutes,
        "max_watch_oldest_source_age_minutes": config.max_watch_oldest_source_age_minutes,
        "min_pass_source_count": config.min_pass_source_count,
        "min_watch_source_count": config.min_watch_source_count,
        "min_pass_independent_source_ratio": config.min_pass_independent_source_ratio,
        "min_watch_independent_source_ratio": config.min_watch_independent_source_ratio,
        "newest_source_at": score_input.newest_source_at,
        "oldest_source_at": score_input.oldest_source_at,
        "source_count": score_input.source_count,
        "newest_source_age_minutes": newest_age,
        "oldest_source_age_minutes": oldest_age,
        "source_age_span_minutes": span,
        "average_source_age_minutes": score_input.average_source_age_minutes,
        "independent_source_ratio": score_input.independent_source_ratio,
        "newest_source_recency_component": newest_component,
        "average_source_recency_component": average_component,
        "oldest_source_recency_component": oldest_component,
        "source_count_coverage_component": source_count_component,
        "independence_coverage_component": independence_component,
        "recency_decay_score": recency_decay_score,
        "recency_status": recency_status,
        "hard_blocker_codes": hard_blockers,
        "reason_codes": reason_codes,
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }


def _age_component(
    age_minutes: Decimal,
    pass_age_minutes: Decimal,
    watch_age_minutes: Decimal,
) -> Decimal:
    if age_minutes <= pass_age_minutes:
        return ONE
    if age_minutes >= watch_age_minutes:
        return ZERO
    numerator = _subtract_nonnegative("age_component_numerator", watch_age_minutes, age_minutes)
    denominator = _subtract_nonnegative(
        "age_component_denominator",
        watch_age_minutes,
        pass_age_minutes,
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


def _recency_decay_score(
    newest_component: Decimal,
    average_component: Decimal,
    oldest_component: Decimal,
    source_count_component: Decimal,
    independence_component: Decimal,
) -> Decimal:
    with localcontext() as context:
        context.prec = DECIMAL_CONTEXT_PRECISION
        context.rounding = ROUND_HALF_EVEN
        return _normalize_unit_decimal(
            "recency_decay_score",
            (
                newest_component
                + average_component
                + oldest_component
                + source_count_component
                + independence_component
            )
            / FIVE,
        )


def _hard_blocker_codes(
    newest_age: Decimal,
    average_age: Decimal,
    oldest_age: Decimal,
    source_count: Decimal,
    independent_ratio: Decimal,
    recency_decay_score: Decimal,
    config: CandidateDecisionSourceRecencyDecayScoreConfig
    | CandidateDecisionSourceRecencyDecayScoreReport,
) -> tuple[str, ...]:
    codes: list[str] = []
    if newest_age > config.max_watch_newest_source_age_minutes:
        codes.append("newest_source_age_block")
    if average_age > config.max_watch_average_source_age_minutes:
        codes.append("average_source_age_block")
    if oldest_age > config.max_watch_oldest_source_age_minutes:
        codes.append("oldest_source_age_block")
    if source_count < config.min_watch_source_count:
        codes.append("source_count_block")
    if independent_ratio < config.min_watch_independent_source_ratio:
        codes.append("independent_source_ratio_block")
    if recency_decay_score < config.min_watch_recency_decay_score:
        codes.append("recency_decay_score_block")
    return tuple(codes)


def _recency_status(
    recency_decay_score: Decimal,
    hard_blocker_codes: tuple[str, ...],
    config: CandidateDecisionSourceRecencyDecayScoreConfig
    | CandidateDecisionSourceRecencyDecayScoreReport,
) -> str:
    if hard_blocker_codes:
        return "block"
    if recency_decay_score < config.min_pass_recency_decay_score:
        return "watch"
    return "pass"


def _reason_codes(
    existing_reason_codes: tuple[str, ...],
    newest_age: Decimal,
    average_age: Decimal,
    oldest_age: Decimal,
    source_count: Decimal,
    independent_ratio: Decimal,
    recency_decay_score: Decimal,
    recency_status: str,
    config: CandidateDecisionSourceRecencyDecayScoreConfig
    | CandidateDecisionSourceRecencyDecayScoreReport,
) -> tuple[str, ...]:
    codes = [
        *existing_reason_codes,
        f"source_recency_decay_{recency_status}",
        _age_reason(
            "newest_source_age",
            newest_age,
            config.max_pass_newest_source_age_minutes,
            config.max_watch_newest_source_age_minutes,
        ),
        _age_reason(
            "average_source_age",
            average_age,
            config.max_pass_average_source_age_minutes,
            config.max_watch_average_source_age_minutes,
        ),
        _age_reason(
            "oldest_source_age",
            oldest_age,
            config.max_pass_oldest_source_age_minutes,
            config.max_watch_oldest_source_age_minutes,
        ),
        _coverage_reason(
            "source_count",
            source_count,
            config.min_watch_source_count,
            config.min_pass_source_count,
        ),
        _coverage_reason(
            "independent_source_ratio",
            independent_ratio,
            config.min_watch_independent_source_ratio,
            config.min_pass_independent_source_ratio,
        ),
        _score_reason(recency_decay_score, config),
    ]
    return _normalize_reason_codes("reason_codes", tuple(codes), allow_empty=False)


def _age_reason(
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
    recency_decay_score: Decimal,
    config: CandidateDecisionSourceRecencyDecayScoreConfig
    | CandidateDecisionSourceRecencyDecayScoreReport,
) -> str:
    if recency_decay_score >= config.min_pass_recency_decay_score:
        return "recency_decay_score_pass"
    if recency_decay_score >= config.min_watch_recency_decay_score:
        return "recency_decay_score_watch"
    return "recency_decay_score_block"


def _validate_config(
    config: CandidateDecisionSourceRecencyDecayScoreConfig
    | CandidateDecisionSourceRecencyDecayScoreReport,
) -> None:
    if config.min_watch_recency_decay_score > config.min_pass_recency_decay_score:
        raise ValueError("min_watch_recency_decay_score must not exceed pass threshold")
    for pass_field, watch_field in (
        ("max_pass_newest_source_age_minutes", "max_watch_newest_source_age_minutes"),
        ("max_pass_average_source_age_minutes", "max_watch_average_source_age_minutes"),
        ("max_pass_oldest_source_age_minutes", "max_watch_oldest_source_age_minutes"),
    ):
        if getattr(config, pass_field) > getattr(config, watch_field):
            raise ValueError(f"{pass_field} must not exceed {watch_field}")
    if config.min_watch_source_count > config.min_pass_source_count:
        raise ValueError("min_watch_source_count must not exceed pass threshold")
    if config.min_watch_independent_source_ratio > config.min_pass_independent_source_ratio:
        raise ValueError("min_watch_independent_source_ratio must not exceed pass threshold")


def _validate_input(score_input: CandidateDecisionSourceRecencyDecayScoreInput) -> None:
    newest_age = _minutes_between(score_input.generated_at, score_input.newest_source_at)
    oldest_age = _minutes_between(score_input.generated_at, score_input.oldest_source_at)
    if oldest_age < newest_age:
        raise ValueError("oldest_source_age_minutes must not be less than newest age")
    if not newest_age <= score_input.average_source_age_minutes <= oldest_age:
        raise ValueError("average_source_age_minutes must be between newest and oldest ages")


def _validate_report(report: CandidateDecisionSourceRecencyDecayScoreReport) -> None:
    _validate_config(report)
    if report.newest_source_at > report.generated_at:
        raise ValueError("newest_source_at must not be after generated_at")
    if report.oldest_source_at > report.newest_source_at:
        raise ValueError("oldest_source_at must not be after newest_source_at")
    expected_newest_age = _minutes_between(report.generated_at, report.newest_source_at)
    expected_oldest_age = _minutes_between(report.generated_at, report.oldest_source_at)
    if report.newest_source_age_minutes != expected_newest_age:
        raise ValueError("newest_source_age_minutes must match generated_at")
    if report.oldest_source_age_minutes != expected_oldest_age:
        raise ValueError("oldest_source_age_minutes must match generated_at")
    expected_span = _subtract_nonnegative(
        "source_age_span_minutes",
        expected_oldest_age,
        expected_newest_age,
    )
    if report.source_age_span_minutes != expected_span:
        raise ValueError("source_age_span_minutes must match source timestamps")
    if not expected_newest_age <= report.average_source_age_minutes <= expected_oldest_age:
        raise ValueError("average_source_age_minutes must be between newest and oldest ages")
    expected_newest_component = _age_component(
        report.newest_source_age_minutes,
        report.max_pass_newest_source_age_minutes,
        report.max_watch_newest_source_age_minutes,
    )
    if report.newest_source_recency_component != expected_newest_component:
        raise ValueError("newest_source_recency_component must match age thresholds")
    expected_average_component = _age_component(
        report.average_source_age_minutes,
        report.max_pass_average_source_age_minutes,
        report.max_watch_average_source_age_minutes,
    )
    if report.average_source_recency_component != expected_average_component:
        raise ValueError("average_source_recency_component must match age thresholds")
    expected_oldest_component = _age_component(
        report.oldest_source_age_minutes,
        report.max_pass_oldest_source_age_minutes,
        report.max_watch_oldest_source_age_minutes,
    )
    if report.oldest_source_recency_component != expected_oldest_component:
        raise ValueError("oldest_source_recency_component must match age thresholds")
    expected_count_component = _coverage_component(
        report.source_count,
        report.min_watch_source_count,
        report.min_pass_source_count,
    )
    if report.source_count_coverage_component != expected_count_component:
        raise ValueError("source_count_coverage_component must match source_count")
    expected_independence_component = _coverage_component(
        report.independent_source_ratio,
        report.min_watch_independent_source_ratio,
        report.min_pass_independent_source_ratio,
    )
    if report.independence_coverage_component != expected_independence_component:
        raise ValueError("independence_coverage_component must match independent_source_ratio")
    expected_score = _recency_decay_score(
        report.newest_source_recency_component,
        report.average_source_recency_component,
        report.oldest_source_recency_component,
        report.source_count_coverage_component,
        report.independence_coverage_component,
    )
    if report.recency_decay_score != expected_score:
        raise ValueError("recency_decay_score must match component scores")
    expected_hard_blockers = _hard_blocker_codes(
        report.newest_source_age_minutes,
        report.average_source_age_minutes,
        report.oldest_source_age_minutes,
        report.source_count,
        report.independent_source_ratio,
        report.recency_decay_score,
        report,
    )
    if report.hard_blocker_codes != expected_hard_blockers:
        raise ValueError("hard_blocker_codes must match thresholds")
    expected_status = _recency_status(report.recency_decay_score, expected_hard_blockers, report)
    if report.recency_status != expected_status:
        raise ValueError("recency_status must match thresholds")
    expected_generated_reason_codes = _reason_codes(
        (),
        report.newest_source_age_minutes,
        report.average_source_age_minutes,
        report.oldest_source_age_minutes,
        report.source_count,
        report.independent_source_ratio,
        report.recency_decay_score,
        report.recency_status,
        report,
    )
    if report.reason_codes[-len(expected_generated_reason_codes) :] != expected_generated_reason_codes:
        raise ValueError("reason_codes must end with generated recency reasons")


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
            "source_age_minutes",
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
    require_paper_only_flags(f"source recency decay {label}", value)


def _require_digest(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if len(value) != 64 or any(char not in "0123456789abcdef" for char in value):
        raise ValueError(f"{field_name} must be a lowercase sha256 digest")


def _report_digest(report: CandidateDecisionSourceRecencyDecayScoreReport) -> str:
    values = asdict(report)
    values.pop("derived_validation_digest", None)
    return _digest_from_values(values)


def _digest_from_values(values: Mapping[str, object]) -> str:
    payload = json_ready_no_floats(values)
    validate_candidate_decision_source_recency_decay_score_public_payload(payload)
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
        if path.lower().endswith("status") and lowered not in RECENCY_STATUSES:
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
    "DEFAULT_CANDIDATE_DECISION_SOURCE_RECENCY_DECAY_SCORE_CONFIG_VERSION",
    "RECENCY_STATUSES",
    "CandidateDecisionSourceRecencyDecayScoreConfig",
    "CandidateDecisionSourceRecencyDecayScoreInput",
    "CandidateDecisionSourceRecencyDecayScoreReport",
    "build_candidate_decision_source_recency_decay_score_report",
    "candidate_decision_source_recency_decay_score_payload",
    "validate_candidate_decision_source_recency_decay_score_public_payload",
    "reject_candidate_decision_source_recency_decay_score_unsafe_payload",
)
