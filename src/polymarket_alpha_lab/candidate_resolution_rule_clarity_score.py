"""Pure candidate resolution rule clarity scoring from aggregate facts."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
import hashlib
import json
from typing import Any

from polymarket_alpha_lab.team_paper_guard import (
    json_ready_no_floats,
    reject_unsafe_surface_fields,
    require_paper_only_flags,
)


DEFAULT_CANDIDATE_RESOLUTION_RULE_CLARITY_SCORE_CONFIG_VERSION = (
    "candidate-resolution-rule-clarity-score-v0"
)
BOUNDARY_STATEMENT = (
    "Paper-only report-only readonly candidate resolution rule clarity score; "
    "research decision-support only."
)

QUANTUM = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
BOOLEAN_COMPONENT_COUNT = Decimal("5.000000")
SCORE_COMPONENT_COUNT = Decimal("3.000000")
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)

CLARITY_STATUSES = ("pass", "watch", "block")

OFFICIAL_CRITERIA_MISSING_BLOCK_REASON = "official_criteria_missing_block"
MEASURABLE_OUTCOME_MISSING_BLOCK_REASON = "measurable_outcome_missing_block"
ORACLE_SOURCE_UNCLEAR_BLOCK_REASON = "oracle_source_unclear_block"
AMBIGUITY_FLAGS_BLOCK_REASON = "ambiguity_flags_block"
KNOWN_DISPUTE_RISK_BLOCK_REASON = "known_dispute_risk_block"
DATE_TIMEZONE_UNCLEAR_WATCH_REASON = "date_timezone_unclear_watch"
FALLBACK_RESOLUTION_PATH_MISSING_WATCH_REASON = (
    "fallback_resolution_path_missing_watch"
)
AMBIGUITY_FLAGS_WATCH_REASON = "ambiguity_flags_watch"
KNOWN_DISPUTE_RISK_WATCH_REASON = "known_dispute_risk_watch"
CLARITY_SCORE_WATCH_REASON = "resolution_rule_clarity_score_watch"
CLARITY_PASS_REASON = "resolution_rule_clarity_pass"

REASON_CODES = (
    OFFICIAL_CRITERIA_MISSING_BLOCK_REASON,
    MEASURABLE_OUTCOME_MISSING_BLOCK_REASON,
    ORACLE_SOURCE_UNCLEAR_BLOCK_REASON,
    AMBIGUITY_FLAGS_BLOCK_REASON,
    KNOWN_DISPUTE_RISK_BLOCK_REASON,
    DATE_TIMEZONE_UNCLEAR_WATCH_REASON,
    FALLBACK_RESOLUTION_PATH_MISSING_WATCH_REASON,
    AMBIGUITY_FLAGS_WATCH_REASON,
    KNOWN_DISPUTE_RISK_WATCH_REASON,
    CLARITY_SCORE_WATCH_REASON,
    CLARITY_PASS_REASON,
)

UNSAFE_PUBLIC_KEY_TERMS = (
    "candidate_id",
    "market_id",
    "market_slug",
    "marketquestion",
    "marketslug",
    "condition_id",
    "question",
    "slug",
    "source_ref",
    "source_refs",
    "source_url",
    "source_uri",
    "source_text",
    "sourceref",
    "sourcerefs",
    "sourceurl",
    "sourceuri",
    "sourcetext",
    "url",
    "dsn",
    "table",
    "tablename",
    "schema",
    "private" + "_key",
    "privatekey",
    "auth",
    "token",
    "wal" + "let",
    "wal" + "letaddress",
    "account",
    "balance",
    "order",
    "trade",
    "position" + "_size",
    "position" + "sizing",
)
UNSAFE_PUBLIC_VALUE_TERMS = (
    "http://",
    "https://",
    "www.",
    "://",
    "postgres://",
    "postgresql://",
    "mysql://",
    "dsn=",
    "table:",
    "schema:",
    "select ",
    " from ",
    "private" + "_key",
    "auth",
    "secret",
    "token",
    "wal" + "let",
    "order",
    "buy",
    "sell",
    "trade",
    "position" + "_size",
    "position" + " sizing",
    "position" + "sizing",
    "reco" + "mmendation",
    "reco" + "mmend ",
    "reco" + "mmended",
)


@dataclass(frozen=True)
class CandidateResolutionRuleClarityScoreConfig:
    config_version: str = DEFAULT_CANDIDATE_RESOLUTION_RULE_CLARITY_SCORE_CONFIG_VERSION
    min_pass_clarity_score: Decimal = Decimal("0.800000")
    min_watch_clarity_score: Decimal = Decimal("0.500000")
    max_pass_ambiguity_flag_count: Decimal = Decimal("0.000000")
    max_watch_ambiguity_flag_count: Decimal = Decimal("2.000000")
    max_pass_known_dispute_risk: Decimal = Decimal("0.200000")
    max_watch_known_dispute_risk: Decimal = Decimal("0.500000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not CandidateResolutionRuleClarityScoreConfig:
            raise ValueError(
                "config must be a CandidateResolutionRuleClarityScoreConfig",
            )
        object.__setattr__(
            self,
            "config_version",
            _require_canonical_string("config_version", self.config_version),
        )
        if (
            self.config_version
            != DEFAULT_CANDIDATE_RESOLUTION_RULE_CLARITY_SCORE_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported version")
        for field_name in ("min_pass_clarity_score", "min_watch_clarity_score"):
            object.__setattr__(
                self,
                field_name,
                _normalize_unit_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "max_pass_ambiguity_flag_count",
            "max_watch_ambiguity_flag_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_whole_decimal(
                    field_name,
                    getattr(self, field_name),
                ),
            )
        for field_name in (
            "max_pass_known_dispute_risk",
            "max_watch_known_dispute_risk",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_unit_decimal(field_name, getattr(self, field_name)),
            )
        _validate_config(self)
        reject_unsafe_surface_fields("resolution rule clarity score config", self)
        _reject_unsafe_public_payload("resolution rule clarity score config", self)
        require_paper_only_flags("CandidateResolutionRuleClarityScoreConfig", self)


@dataclass(frozen=True)
class CandidateResolutionRuleClarityFacts:
    official_criteria_present: bool
    measurable_outcome_definition_present: bool
    date_timezone_clear: bool
    oracle_source_clear: bool
    fallback_resolution_path_present: bool
    ambiguity_flag_count: Decimal
    known_dispute_risk: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not CandidateResolutionRuleClarityFacts:
            raise ValueError("facts must be a CandidateResolutionRuleClarityFacts")
        for field_name in (
            "official_criteria_present",
            "measurable_outcome_definition_present",
            "date_timezone_clear",
            "oracle_source_clear",
            "fallback_resolution_path_present",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_bool(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "ambiguity_flag_count",
            _normalize_nonnegative_whole_decimal(
                "ambiguity_flag_count",
                self.ambiguity_flag_count,
            ),
        )
        object.__setattr__(
            self,
            "known_dispute_risk",
            _normalize_unit_decimal("known_dispute_risk", self.known_dispute_risk),
        )
        reject_unsafe_surface_fields("resolution rule clarity facts", self)
        _reject_unsafe_public_payload("resolution rule clarity facts", self)
        require_paper_only_flags("CandidateResolutionRuleClarityFacts", self)


@dataclass(frozen=True)
class CandidateResolutionRuleClarityScoreReport:
    generated_at: datetime
    config_version: str
    min_pass_clarity_score: Decimal
    min_watch_clarity_score: Decimal
    max_pass_ambiguity_flag_count: Decimal
    max_watch_ambiguity_flag_count: Decimal
    max_pass_known_dispute_risk: Decimal
    max_watch_known_dispute_risk: Decimal
    official_criteria_present: bool
    measurable_outcome_definition_present: bool
    date_timezone_clear: bool
    oracle_source_clear: bool
    fallback_resolution_path_present: bool
    ambiguity_flag_count: Decimal
    known_dispute_risk: Decimal
    component_clarity_score: Decimal
    ambiguity_penalty_score: Decimal
    known_dispute_risk_score: Decimal
    clarity_score: Decimal
    clarity_status: str
    hard_blocker_codes: tuple[str, ...]
    reason_codes: tuple[str, ...]
    derived_validation_digest: str
    boundary_statement: str = BOUNDARY_STATEMENT
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not CandidateResolutionRuleClarityScoreReport:
            raise ValueError("report must be a CandidateResolutionRuleClarityScoreReport")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        object.__setattr__(
            self,
            "config_version",
            _require_canonical_string("config_version", self.config_version),
        )
        if (
            self.config_version
            != DEFAULT_CANDIDATE_RESOLUTION_RULE_CLARITY_SCORE_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported version")
        for field_name in ("min_pass_clarity_score", "min_watch_clarity_score"):
            object.__setattr__(
                self,
                field_name,
                _normalize_unit_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "max_pass_ambiguity_flag_count",
            "max_watch_ambiguity_flag_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_whole_decimal(
                    field_name,
                    getattr(self, field_name),
                ),
            )
        for field_name in (
            "max_pass_known_dispute_risk",
            "max_watch_known_dispute_risk",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_unit_decimal(field_name, getattr(self, field_name)),
            )
        _validate_config(_config_from_report(self))
        for field_name in (
            "official_criteria_present",
            "measurable_outcome_definition_present",
            "date_timezone_clear",
            "oracle_source_clear",
            "fallback_resolution_path_present",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_bool(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "ambiguity_flag_count",
            _normalize_nonnegative_whole_decimal(
                "ambiguity_flag_count",
                self.ambiguity_flag_count,
            ),
        )
        object.__setattr__(
            self,
            "known_dispute_risk",
            _normalize_unit_decimal("known_dispute_risk", self.known_dispute_risk),
        )
        for field_name in (
            "component_clarity_score",
            "ambiguity_penalty_score",
            "known_dispute_risk_score",
            "clarity_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_unit_decimal(field_name, getattr(self, field_name)),
            )
        _require_member("clarity_status", self.clarity_status, CLARITY_STATUSES)
        object.__setattr__(
            self,
            "hard_blocker_codes",
            _normalize_reason_codes(self.hard_blocker_codes, allow_empty=True),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes, allow_empty=False),
        )
        _require_validation_digest(self.derived_validation_digest)
        if self.boundary_statement != BOUNDARY_STATEMENT:
            raise ValueError("boundary_statement must match paper-only scope")
        reject_unsafe_surface_fields("resolution rule clarity score report", self)
        _reject_unsafe_public_payload("resolution rule clarity score report", self)
        require_paper_only_flags("CandidateResolutionRuleClarityScoreReport", self)
        _validate_report_derived_fields(self)
        if self.derived_validation_digest != _report_digest_from_values(
            _report_values_without_digest(self),
        ):
            raise ValueError("derived_validation_digest must match report payload")
        _validate_report_against_facts(self)


def build_candidate_resolution_rule_clarity_score_report(
    facts: CandidateResolutionRuleClarityFacts,
    *,
    config: CandidateResolutionRuleClarityScoreConfig,
    generated_at: datetime,
) -> CandidateResolutionRuleClarityScoreReport:
    if type(facts) is not CandidateResolutionRuleClarityFacts:
        raise ValueError("facts must be a CandidateResolutionRuleClarityFacts")
    if type(config) is not CandidateResolutionRuleClarityScoreConfig:
        raise ValueError("config must be a CandidateResolutionRuleClarityScoreConfig")
    require_paper_only_flags("CandidateResolutionRuleClarityFacts", facts)
    require_paper_only_flags("CandidateResolutionRuleClarityScoreConfig", config)
    reject_unsafe_surface_fields("resolution rule clarity facts", facts)
    reject_unsafe_surface_fields("resolution rule clarity config", config)
    _reject_unsafe_public_payload("resolution rule clarity facts", facts)
    _reject_unsafe_public_payload("resolution rule clarity config", config)

    generated_at_utc = _as_utc("generated_at", generated_at)
    component_clarity_score = _component_clarity_score(facts)
    ambiguity_penalty_score = _ambiguity_penalty_score(facts, config)
    known_dispute_risk_score = _known_dispute_risk_score(facts.known_dispute_risk)
    hard_blockers = _hard_blocker_codes(facts, config)
    clarity_score = _clarity_score(
        component_clarity_score=component_clarity_score,
        ambiguity_penalty_score=ambiguity_penalty_score,
        known_dispute_risk_score=known_dispute_risk_score,
        hard_blocker_codes=hard_blockers,
    )
    clarity_status = _clarity_status(
        clarity_score=clarity_score,
        hard_blocker_codes=hard_blockers,
        config=config,
    )
    report_values: dict[str, object] = {
        "generated_at": generated_at_utc,
        "config_version": config.config_version,
        "min_pass_clarity_score": config.min_pass_clarity_score,
        "min_watch_clarity_score": config.min_watch_clarity_score,
        "max_pass_ambiguity_flag_count": config.max_pass_ambiguity_flag_count,
        "max_watch_ambiguity_flag_count": config.max_watch_ambiguity_flag_count,
        "max_pass_known_dispute_risk": config.max_pass_known_dispute_risk,
        "max_watch_known_dispute_risk": config.max_watch_known_dispute_risk,
        "official_criteria_present": facts.official_criteria_present,
        "measurable_outcome_definition_present": (
            facts.measurable_outcome_definition_present
        ),
        "date_timezone_clear": facts.date_timezone_clear,
        "oracle_source_clear": facts.oracle_source_clear,
        "fallback_resolution_path_present": facts.fallback_resolution_path_present,
        "ambiguity_flag_count": facts.ambiguity_flag_count,
        "known_dispute_risk": facts.known_dispute_risk,
        "component_clarity_score": component_clarity_score,
        "ambiguity_penalty_score": ambiguity_penalty_score,
        "known_dispute_risk_score": known_dispute_risk_score,
        "clarity_score": clarity_score,
        "clarity_status": clarity_status,
        "hard_blocker_codes": hard_blockers,
        "reason_codes": _reason_codes(
            facts=facts,
            clarity_score=clarity_score,
            hard_blocker_codes=hard_blockers,
            config=config,
        ),
        "boundary_statement": BOUNDARY_STATEMENT,
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    return CandidateResolutionRuleClarityScoreReport(
        **report_values,
        derived_validation_digest=_report_digest_from_values(report_values),
    )


def candidate_resolution_rule_clarity_score_payload(
    report: CandidateResolutionRuleClarityScoreReport,
) -> dict[str, Any]:
    if type(report) is not CandidateResolutionRuleClarityScoreReport:
        raise ValueError("report must be a CandidateResolutionRuleClarityScoreReport")
    require_paper_only_flags("CandidateResolutionRuleClarityScoreReport", report)
    _reject_unsafe_public_payload("resolution rule clarity score report", report)
    payload = json_ready_no_floats(report)
    if not isinstance(payload, dict):
        raise ValueError("report payload must be a JSON object")
    validate_candidate_resolution_rule_clarity_score_public_payload(payload)
    return payload


def validate_candidate_resolution_rule_clarity_score_public_payload(
    payload: object,
) -> None:
    _reject_unsafe_public_payload("resolution rule clarity score public payload", payload)


def _component_clarity_score(facts: CandidateResolutionRuleClarityFacts) -> Decimal:
    present_count = ZERO
    for value in (
        facts.official_criteria_present,
        facts.measurable_outcome_definition_present,
        facts.date_timezone_clear,
        facts.oracle_source_clear,
        facts.fallback_resolution_path_present,
    ):
        if value:
            present_count += ONE
    return _q(present_count / BOOLEAN_COMPONENT_COUNT)


def _ambiguity_penalty_score(
    facts: CandidateResolutionRuleClarityFacts,
    config: CandidateResolutionRuleClarityScoreConfig,
) -> Decimal:
    if facts.ambiguity_flag_count <= config.max_pass_ambiguity_flag_count:
        return ZERO
    denominator = config.max_watch_ambiguity_flag_count
    if denominator <= ZERO:
        return ONE
    return _ratio_capped(facts.ambiguity_flag_count, denominator)


def _known_dispute_risk_score(known_dispute_risk: Decimal) -> Decimal:
    return _q(ONE - known_dispute_risk)


def _hard_blocker_codes(
    facts: CandidateResolutionRuleClarityFacts,
    config: CandidateResolutionRuleClarityScoreConfig,
) -> tuple[str, ...]:
    values: list[str] = []
    if not facts.official_criteria_present:
        values.append(OFFICIAL_CRITERIA_MISSING_BLOCK_REASON)
    if not facts.measurable_outcome_definition_present:
        values.append(MEASURABLE_OUTCOME_MISSING_BLOCK_REASON)
    if not facts.oracle_source_clear:
        values.append(ORACLE_SOURCE_UNCLEAR_BLOCK_REASON)
    if facts.ambiguity_flag_count > config.max_watch_ambiguity_flag_count:
        values.append(AMBIGUITY_FLAGS_BLOCK_REASON)
    if facts.known_dispute_risk > config.max_watch_known_dispute_risk:
        values.append(KNOWN_DISPUTE_RISK_BLOCK_REASON)
    return tuple(values)


def _clarity_score(
    *,
    component_clarity_score: Decimal,
    ambiguity_penalty_score: Decimal,
    known_dispute_risk_score: Decimal,
    hard_blocker_codes: tuple[str, ...],
) -> Decimal:
    if hard_blocker_codes:
        return ZERO
    return _q(
        (
            component_clarity_score
            + (ONE - ambiguity_penalty_score)
            + known_dispute_risk_score
        )
        / SCORE_COMPONENT_COUNT,
    )


def _clarity_status(
    *,
    clarity_score: Decimal,
    hard_blocker_codes: tuple[str, ...],
    config: CandidateResolutionRuleClarityScoreConfig,
) -> str:
    if hard_blocker_codes or clarity_score < config.min_watch_clarity_score:
        return "block"
    if clarity_score < config.min_pass_clarity_score:
        return "watch"
    return "pass"


def _reason_codes(
    *,
    facts: CandidateResolutionRuleClarityFacts,
    clarity_score: Decimal,
    hard_blocker_codes: tuple[str, ...],
    config: CandidateResolutionRuleClarityScoreConfig,
) -> tuple[str, ...]:
    if hard_blocker_codes:
        return hard_blocker_codes
    values: list[str] = []
    if not facts.date_timezone_clear:
        values.append(DATE_TIMEZONE_UNCLEAR_WATCH_REASON)
    if not facts.fallback_resolution_path_present:
        values.append(FALLBACK_RESOLUTION_PATH_MISSING_WATCH_REASON)
    if (
        facts.ambiguity_flag_count > config.max_pass_ambiguity_flag_count
        and facts.ambiguity_flag_count <= config.max_watch_ambiguity_flag_count
    ):
        values.append(AMBIGUITY_FLAGS_WATCH_REASON)
    if (
        facts.known_dispute_risk > config.max_pass_known_dispute_risk
        and facts.known_dispute_risk <= config.max_watch_known_dispute_risk
    ):
        values.append(KNOWN_DISPUTE_RISK_WATCH_REASON)
    if clarity_score < config.min_pass_clarity_score:
        values.append(CLARITY_SCORE_WATCH_REASON)
    if values:
        return tuple(values)
    return (CLARITY_PASS_REASON,)


def _validate_report_derived_fields(
    report: CandidateResolutionRuleClarityScoreReport,
) -> None:
    expected_clarity_score = _clarity_score(
        component_clarity_score=report.component_clarity_score,
        ambiguity_penalty_score=report.ambiguity_penalty_score,
        known_dispute_risk_score=report.known_dispute_risk_score,
        hard_blocker_codes=report.hard_blocker_codes,
    )
    if report.clarity_score != expected_clarity_score:
        raise ValueError("clarity_score must match score components")
    config = _config_from_report(report)
    expected_status = _clarity_status(
        clarity_score=report.clarity_score,
        hard_blocker_codes=report.hard_blocker_codes,
        config=config,
    )
    if report.clarity_status != expected_status:
        raise ValueError("clarity_status must match clarity_score")
    facts = _facts_from_report(report)
    expected_reason_codes = _reason_codes(
        facts=facts,
        clarity_score=report.clarity_score,
        hard_blocker_codes=report.hard_blocker_codes,
        config=config,
    )
    if report.reason_codes != expected_reason_codes:
        raise ValueError("reason_codes must match report fields")


def _validate_report_against_facts(
    report: CandidateResolutionRuleClarityScoreReport,
) -> None:
    facts = _facts_from_report(report)
    config = _config_from_report(report)
    expected_hard_blockers = _hard_blocker_codes(facts, config)
    if report.hard_blocker_codes != expected_hard_blockers:
        raise ValueError("hard_blocker_codes must match report fields")
    expected_component_score = _component_clarity_score(facts)
    if report.component_clarity_score != expected_component_score:
        raise ValueError("component_clarity_score must match report fields")
    expected_ambiguity_penalty_score = _ambiguity_penalty_score(facts, config)
    if report.ambiguity_penalty_score != expected_ambiguity_penalty_score:
        raise ValueError("ambiguity_penalty_score must match report fields")
    expected_known_dispute_risk_score = _known_dispute_risk_score(
        report.known_dispute_risk,
    )
    if report.known_dispute_risk_score != expected_known_dispute_risk_score:
        raise ValueError("known_dispute_risk_score must match report fields")


def _facts_from_report(
    report: CandidateResolutionRuleClarityScoreReport,
) -> CandidateResolutionRuleClarityFacts:
    return CandidateResolutionRuleClarityFacts(
        official_criteria_present=report.official_criteria_present,
        measurable_outcome_definition_present=(
            report.measurable_outcome_definition_present
        ),
        date_timezone_clear=report.date_timezone_clear,
        oracle_source_clear=report.oracle_source_clear,
        fallback_resolution_path_present=report.fallback_resolution_path_present,
        ambiguity_flag_count=report.ambiguity_flag_count,
        known_dispute_risk=report.known_dispute_risk,
    )


def _config_from_report(
    report: CandidateResolutionRuleClarityScoreReport,
) -> CandidateResolutionRuleClarityScoreConfig:
    return CandidateResolutionRuleClarityScoreConfig(
        config_version=report.config_version,
        min_pass_clarity_score=report.min_pass_clarity_score,
        min_watch_clarity_score=report.min_watch_clarity_score,
        max_pass_ambiguity_flag_count=report.max_pass_ambiguity_flag_count,
        max_watch_ambiguity_flag_count=report.max_watch_ambiguity_flag_count,
        max_pass_known_dispute_risk=report.max_pass_known_dispute_risk,
        max_watch_known_dispute_risk=report.max_watch_known_dispute_risk,
    )


def _validate_config(config: CandidateResolutionRuleClarityScoreConfig) -> None:
    if config.min_watch_clarity_score > config.min_pass_clarity_score:
        raise ValueError("min_watch_clarity_score must not exceed min_pass_clarity_score")
    if (
        config.max_pass_ambiguity_flag_count
        > config.max_watch_ambiguity_flag_count
    ):
        raise ValueError(
            "max_pass_ambiguity_flag_count must not exceed "
            "max_watch_ambiguity_flag_count",
        )
    if config.max_pass_known_dispute_risk > config.max_watch_known_dispute_risk:
        raise ValueError(
            "max_pass_known_dispute_risk must not exceed "
            "max_watch_known_dispute_risk",
        )


def _normalize_bool(field_name: str, value: object) -> bool:
    if type(value) is not bool:
        raise ValueError(f"{field_name} must be a bool")
    return value


def _normalize_nonnegative_whole_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_nonnegative_decimal(field_name, value)
    if normalized % ONE != ZERO:
        raise ValueError(f"{field_name} must be whole")
    return normalized


def _normalize_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _normalize_unit_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized < ZERO or normalized > ONE:
        raise ValueError(f"{field_name} must be between 0.000000 and 1.000000")
    return normalized


def _normalize_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return _q(value)


def _require_canonical_string(field_name: str, value: object) -> str:
    if type(value) is not str or value == "" or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical string")
    return value


def _require_member(
    field_name: str,
    value: object,
    allowed_values: tuple[str, ...],
) -> str:
    if type(value) is not str or value not in allowed_values:
        raise ValueError(f"{field_name} must be one of {allowed_values}")
    return value


def _normalize_reason_codes(
    values: object,
    *,
    allow_empty: bool,
) -> tuple[str, ...]:
    if isinstance(values, (str, bytes)):
        raise ValueError("reason_codes must be a tuple")
    if not isinstance(values, tuple):
        raise ValueError("reason_codes must be a tuple")
    if not values and not allow_empty:
        raise ValueError("reason_codes must not be empty")
    normalized: list[str] = []
    for value in values:
        if type(value) is not str or value not in REASON_CODES:
            raise ValueError("reason_codes contains unsupported reason code")
        if value in normalized:
            raise ValueError("reason_codes must not contain duplicates")
        normalized.append(value)
    return tuple(normalized)


def _require_validation_digest(value: object) -> str:
    if type(value) is not str:
        raise ValueError("derived_validation_digest must be a string")
    if len(value) != 64 or value.lower() != value:
        raise ValueError("derived_validation_digest must be a lowercase sha256 digest")
    try:
        int(value, 16)
    except ValueError as exc:
        raise ValueError(
            "derived_validation_digest must be a lowercase sha256 digest",
        ) from exc
    return value


def _report_values_without_digest(
    report: CandidateResolutionRuleClarityScoreReport,
) -> dict[str, object]:
    values = asdict(report)
    values.pop("derived_validation_digest")
    return values


def _report_digest_from_values(values: dict[str, object]) -> str:
    payload = json_ready_no_floats(values)
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8"),
    ).hexdigest()


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


def _ratio_capped(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator <= ZERO:
        raise ValueError("denominator must be positive")
    ratio = numerator / denominator
    if ratio >= ONE:
        return ONE
    if ratio <= ZERO:
        return ZERO
    return _q(ratio)


def _q(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(QUANTUM)


def _reject_unsafe_public_payload(label: str, value: object) -> None:
    for key in _iter_payload_keys(value):
        if _has_unsafe_public_term(key, UNSAFE_PUBLIC_KEY_TERMS):
            raise ValueError(f"unsafe public payload in {label}")
    for item in _iter_payload_values(value):
        if isinstance(item, str):
            if _has_unsafe_public_term(item, UNSAFE_PUBLIC_VALUE_TERMS):
                raise ValueError(f"unsafe public payload in {label}")


def _has_unsafe_public_term(value: str, terms: tuple[str, ...]) -> bool:
    lowered_value = value.lower()
    normalized_value = _normalize_public_payload_text(value)
    for term in terms:
        lowered_term = term.lower()
        normalized_term = _normalize_public_payload_text(term)
        if lowered_term in lowered_value:
            return True
        if normalized_term and normalized_term in normalized_value:
            return True
    return False


def _normalize_public_payload_text(value: str) -> str:
    return "".join(character for character in value.lower() if character.isalnum())


def _iter_payload_keys(value: object) -> tuple[str, ...]:
    if isinstance(value, dict):
        keys: list[str] = []
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("unsafe public payload key type")
            keys.append(key)
            keys.extend(_iter_payload_keys(item))
        return tuple(keys)
    if isinstance(value, (list, tuple)):
        keys = []
        for item in value:
            keys.extend(_iter_payload_keys(item))
        return tuple(keys)
    if hasattr(value, "__dataclass_fields__") and not isinstance(value, type):
        return _iter_payload_keys(asdict(value))
    return ()


def _iter_payload_values(value: object) -> tuple[object, ...]:
    if isinstance(value, dict):
        values: list[object] = []
        for item in value.values():
            values.extend(_iter_payload_values(item))
        return tuple(values)
    if isinstance(value, (list, tuple)):
        values = []
        for item in value:
            values.extend(_iter_payload_values(item))
        return tuple(values)
    if hasattr(value, "__dataclass_fields__") and not isinstance(value, type):
        return _iter_payload_values(asdict(value))
    return (value,)


__all__ = (
    "DEFAULT_CANDIDATE_RESOLUTION_RULE_CLARITY_SCORE_CONFIG_VERSION",
    "BOUNDARY_STATEMENT",
    "CLARITY_STATUSES",
    "REASON_CODES",
    "CandidateResolutionRuleClarityScoreConfig",
    "CandidateResolutionRuleClarityFacts",
    "CandidateResolutionRuleClarityScoreReport",
    "build_candidate_resolution_rule_clarity_score_report",
    "candidate_resolution_rule_clarity_score_payload",
    "validate_candidate_resolution_rule_clarity_score_public_payload",
)
