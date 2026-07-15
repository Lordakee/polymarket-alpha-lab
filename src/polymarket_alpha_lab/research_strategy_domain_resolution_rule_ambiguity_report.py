"""Deterministic report-only diagnostics for resolution-rule ambiguity.

The module accepts caller-supplied research observations, derives public-safe
manual-review diagnostics, and never performs network, persistence, wallet, or
execution activity.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import InitVar, asdict, dataclass, field, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, InvalidOperation, ROUND_HALF_EVEN, localcontext
import hashlib
import json
from typing import Any


DEFAULT_RESEARCH_STRATEGY_DOMAIN_RESOLUTION_RULE_AMBIGUITY_REPORT_CONFIG_VERSION = (
    "research-strategy-domain-resolution-rule-ambiguity-report-v0"
)
RESEARCH_STRATEGY_DOMAIN_RESOLUTION_RULE_AMBIGUITY_STATUSES = (
    "pass",
    "watch",
    "block",
)
MANUAL_REVIEW_PRIORITIES = ("routine", "priority", "urgent")

_DIGEST_FIELD = "derived_validation_digest"
_QUANTUM = Decimal("0.000001")
_ZERO = Decimal("0.000000")
_ONE = Decimal("1.000000")
_DECIMAL_CONTEXT = Context(prec=50, rounding=ROUND_HALF_EVEN)

_ROW_REASON_ORDER = (
    "no_verifiable_source_reference_block",
    "rule_text_completeness_block",
    "verifiable_source_coverage_block",
    "boundary_condition_coverage_block",
    "exception_clause_coverage_block",
    "contradiction_pressure_block",
    "unresolved_terms_block",
    "ambiguity_score_block",
    "rule_text_completeness_watch",
    "verifiable_source_coverage_watch",
    "boundary_condition_coverage_watch",
    "exception_clause_coverage_watch",
    "contradiction_pressure_watch",
    "unresolved_terms_watch",
    "ambiguity_score_watch",
    "resolution_rule_clear",
)
_UNSAFE_PUBLIC_VALUE_FRAGMENTS = (
    "://",
    "http:",
    "https:",
    "private",
    "secret",
    "credential",
    "token",
    "wallet",
    "postgres",
    "database",
    "table_name",
    "dsn",
    "api_key",
    "auth_key",
    "market_id",
    "market_slug",
    "raw_question",
)
_RAW_QUESTION_PREFIXES = (
    "will ",
    "when ",
    "what ",
    "which ",
    "who ",
    "does ",
    "did ",
    "is ",
    "are ",
)
_CONFIG_PROBABILITY_FIELDS = (
    "pass_rule_text_completeness",
    "watch_rule_text_completeness",
    "pass_verifiable_source_coverage",
    "watch_verifiable_source_coverage",
    "pass_boundary_condition_coverage",
    "watch_boundary_condition_coverage",
    "pass_exception_clause_coverage",
    "watch_exception_clause_coverage",
    "pass_contradiction_pressure_ceiling",
    "watch_contradiction_pressure_ceiling",
    "watch_ambiguity_score",
    "block_ambiguity_score",
    "rule_text_weight",
    "verifiable_source_weight",
    "boundary_condition_weight",
    "exception_clause_weight",
    "contradiction_weight",
    "unresolved_term_weight",
)
_CONFIG_WHOLE_COUNT_FIELDS = (
    "unresolved_term_watch_count",
    "unresolved_term_block_count",
)
_CONFIG_WEIGHT_FIELDS = (
    "rule_text_weight",
    "verifiable_source_weight",
    "boundary_condition_weight",
    "exception_clause_weight",
    "contradiction_weight",
    "unresolved_term_weight",
)
_INPUT_PROBABILITY_FIELDS = (
    "rule_text_completeness",
    "verifiable_source_coverage",
    "boundary_condition_coverage",
    "exception_clause_coverage",
    "contradiction_pressure",
)


@dataclass(frozen=True)
class ResearchStrategyDomainResolutionRuleAmbiguityConfig:
    config_version: str = (
        DEFAULT_RESEARCH_STRATEGY_DOMAIN_RESOLUTION_RULE_AMBIGUITY_REPORT_CONFIG_VERSION
    )
    pass_rule_text_completeness: Decimal = Decimal("0.850000")
    watch_rule_text_completeness: Decimal = Decimal("0.650000")
    pass_verifiable_source_coverage: Decimal = Decimal("0.800000")
    watch_verifiable_source_coverage: Decimal = Decimal("0.600000")
    pass_boundary_condition_coverage: Decimal = Decimal("0.800000")
    watch_boundary_condition_coverage: Decimal = Decimal("0.600000")
    pass_exception_clause_coverage: Decimal = Decimal("0.750000")
    watch_exception_clause_coverage: Decimal = Decimal("0.500000")
    pass_contradiction_pressure_ceiling: Decimal = Decimal("0.200000")
    watch_contradiction_pressure_ceiling: Decimal = Decimal("0.450000")
    unresolved_term_watch_count: Decimal = Decimal("1")
    unresolved_term_block_count: Decimal = Decimal("3")
    watch_ambiguity_score: Decimal = Decimal("0.250000")
    block_ambiguity_score: Decimal = Decimal("0.550000")
    rule_text_weight: Decimal = Decimal("0.250000")
    verifiable_source_weight: Decimal = Decimal("0.250000")
    boundary_condition_weight: Decimal = Decimal("0.200000")
    exception_clause_weight: Decimal = Decimal("0.100000")
    contradiction_weight: Decimal = Decimal("0.100000")
    unresolved_term_weight: Decimal = Decimal("0.100000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchStrategyDomainResolutionRuleAmbiguityConfig does not support "
            "subclassing",
        )

    def __post_init__(self) -> None:
        _require_exact_type(
            "config",
            self,
            ResearchStrategyDomainResolutionRuleAmbiguityConfig,
        )
        _require_public_identifier("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_STRATEGY_DOMAIN_RESOLUTION_RULE_AMBIGUITY_REPORT_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for name in _CONFIG_PROBABILITY_FIELDS:
            object.__setattr__(self, name, _probability(name, getattr(self, name)))
        for name in _CONFIG_WHOLE_COUNT_FIELDS:
            object.__setattr__(self, name, _whole_count(name, getattr(self, name)))
        _require_floor_order(
            "rule_text_completeness",
            self.pass_rule_text_completeness,
            self.watch_rule_text_completeness,
        )
        _require_floor_order(
            "verifiable_source_coverage",
            self.pass_verifiable_source_coverage,
            self.watch_verifiable_source_coverage,
        )
        _require_floor_order(
            "boundary_condition_coverage",
            self.pass_boundary_condition_coverage,
            self.watch_boundary_condition_coverage,
        )
        _require_floor_order(
            "exception_clause_coverage",
            self.pass_exception_clause_coverage,
            self.watch_exception_clause_coverage,
        )
        if (
            self.pass_contradiction_pressure_ceiling
            >= self.watch_contradiction_pressure_ceiling
        ):
            raise ValueError(
                "pass contradiction ceiling must be below watch contradiction ceiling",
            )
        if self.unresolved_term_watch_count <= _ZERO:
            raise ValueError("unresolved_term_watch_count must be positive")
        if self.unresolved_term_block_count <= self.unresolved_term_watch_count:
            raise ValueError(
                "unresolved_term_block_count must exceed unresolved_term_watch_count",
            )
        if self.block_ambiguity_score <= self.watch_ambiguity_score:
            raise ValueError("block_ambiguity_score must exceed watch_ambiguity_score")
        with localcontext(_DECIMAL_CONTEXT):
            weight_sum = _quantize(
                sum((getattr(self, name) for name in _CONFIG_WEIGHT_FIELDS), _ZERO),
            )
        if weight_sum != _ONE:
            raise ValueError("ambiguity score weights must sum to 1")
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class ResearchStrategyDomainResolutionRuleAmbiguityInput:
    domain_team: str
    public_rule_key: str
    private_source_references: tuple[str, ...] = field(repr=False)
    rule_text_completeness: Decimal = _ZERO
    verifiable_source_coverage: Decimal = _ZERO
    boundary_condition_coverage: Decimal = _ZERO
    exception_clause_coverage: Decimal = _ZERO
    contradiction_pressure: Decimal = _ZERO
    unresolved_term_count: Decimal = _ZERO
    reason_codes: tuple[str, ...] = ()
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchStrategyDomainResolutionRuleAmbiguityInput does not support "
            "subclassing",
        )

    def __post_init__(self) -> None:
        _require_exact_type(
            "input",
            self,
            ResearchStrategyDomainResolutionRuleAmbiguityInput,
        )
        _require_public_identifier("domain_team", self.domain_team)
        _require_public_identifier("public_rule_key", self.public_rule_key)
        object.__setattr__(
            self,
            "private_source_references",
            _private_references(self.private_source_references),
        )
        for name in _INPUT_PROBABILITY_FIELDS:
            object.__setattr__(self, name, _probability(name, getattr(self, name)))
        object.__setattr__(
            self,
            "unresolved_term_count",
            _whole_count("unresolved_term_count", self.unresolved_term_count),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _upstream_reason_codes(self.reason_codes),
        )
        if not self.private_source_references and self.verifiable_source_coverage != _ZERO:
            raise ValueError(
                "verifiable_source_coverage must be zero without source references",
            )
        _require_hard_flags("input", self)


@dataclass(frozen=True)
class ResearchStrategyDomainResolutionRuleAmbiguityRow:
    domain_team: str
    public_rule_key: str
    source_reference_count: Decimal
    rule_text_completeness: Decimal
    verifiable_source_coverage: Decimal
    boundary_condition_coverage: Decimal
    exception_clause_coverage: Decimal
    contradiction_pressure: Decimal
    unresolved_term_count: Decimal
    upstream_reason_codes: tuple[str, ...]
    rule_text_gap_score: Decimal
    verifiable_source_gap_score: Decimal
    boundary_condition_gap_score: Decimal
    exception_clause_gap_score: Decimal
    unresolved_term_pressure_score: Decimal
    ambiguity_score: Decimal
    manual_review_priority_score: Decimal
    status: str
    manual_review_priority: str
    reason_codes: tuple[str, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True
    validation_config: InitVar[
        ResearchStrategyDomainResolutionRuleAmbiguityConfig | None
    ] = None

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchStrategyDomainResolutionRuleAmbiguityRow does not support "
            "subclassing",
        )

    def __post_init__(
        self,
        validation_config: ResearchStrategyDomainResolutionRuleAmbiguityConfig | None,
    ) -> None:
        _require_exact_type(
            "row",
            self,
            ResearchStrategyDomainResolutionRuleAmbiguityRow,
        )
        config = validation_config or ResearchStrategyDomainResolutionRuleAmbiguityConfig()
        config = _require_config_contract("validation_config", config)
        _require_public_identifier("domain_team", self.domain_team)
        _require_public_identifier("public_rule_key", self.public_rule_key)
        for name in (
            "source_reference_count",
            "unresolved_term_count",
        ):
            object.__setattr__(self, name, _whole_count(name, getattr(self, name)))
        for name in (
            "rule_text_completeness",
            "verifiable_source_coverage",
            "boundary_condition_coverage",
            "exception_clause_coverage",
            "contradiction_pressure",
            "rule_text_gap_score",
            "verifiable_source_gap_score",
            "boundary_condition_gap_score",
            "exception_clause_gap_score",
            "unresolved_term_pressure_score",
            "ambiguity_score",
            "manual_review_priority_score",
        ):
            object.__setattr__(self, name, _probability(name, getattr(self, name)))
        object.__setattr__(
            self,
            "upstream_reason_codes",
            _upstream_reason_codes(self.upstream_reason_codes),
        )
        if (
            self.source_reference_count == _ZERO
            and self.verifiable_source_coverage != _ZERO
        ):
            raise ValueError(
                "verifiable_source_coverage must be zero without source references",
            )
        _member(
            "status",
            self.status,
            RESEARCH_STRATEGY_DOMAIN_RESOLUTION_RULE_AMBIGUITY_STATUSES,
        )
        _member(
            "manual_review_priority",
            self.manual_review_priority,
            MANUAL_REVIEW_PRIORITIES,
        )
        object.__setattr__(
            self,
            "reason_codes",
            _row_reason_codes(self.reason_codes),
        )
        _require_hard_flags("row", self)
        _validate_row_derived(self, config=config)
        expected_digest = _digest_value(self)
        if self.derived_validation_digest == "":
            object.__setattr__(self, "derived_validation_digest", expected_digest)
        else:
            _require_digest("derived_validation_digest", self.derived_validation_digest)
            if self.derived_validation_digest != expected_digest:
                raise ValueError(
                    "derived_validation_digest must match row fields",
                )


@dataclass(frozen=True)
class ResearchStrategyDomainResolutionRuleAmbiguityReasonCodeCount:
    reason_code: str
    count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchStrategyDomainResolutionRuleAmbiguityReasonCodeCount does not "
            "support subclassing",
        )

    def __post_init__(self) -> None:
        _require_exact_type(
            "reason code count",
            self,
            ResearchStrategyDomainResolutionRuleAmbiguityReasonCodeCount,
        )
        _require_public_identifier("reason_code", self.reason_code)
        object.__setattr__(self, "count", _positive_whole_count("count", self.count))
        _require_hard_flags("reason code count", self)


@dataclass(frozen=True)
class ResearchStrategyDomainResolutionRuleAmbiguityReport:
    generated_at: datetime
    config: ResearchStrategyDomainResolutionRuleAmbiguityConfig
    config_version: str
    rule_count: Decimal
    domain_team_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    routine_review_count: Decimal
    priority_review_count: Decimal
    urgent_review_count: Decimal
    average_ambiguity_score: Decimal
    max_ambiguity_score: Decimal
    max_manual_review_priority_score: Decimal
    status: str
    rows: tuple[ResearchStrategyDomainResolutionRuleAmbiguityRow, ...]
    reason_code_counts: tuple[
        ResearchStrategyDomainResolutionRuleAmbiguityReasonCodeCount,
        ...,
    ]
    reason_codes: tuple[str, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchStrategyDomainResolutionRuleAmbiguityReport does not support "
            "subclassing",
        )

    def __post_init__(self) -> None:
        _require_exact_type(
            "report",
            self,
            ResearchStrategyDomainResolutionRuleAmbiguityReport,
        )
        object.__setattr__(self, "generated_at", _utc("generated_at", self.generated_at))
        _require_config_contract("config", self.config)
        _require_public_identifier("config_version", self.config_version)
        if self.config_version != self.config.config_version:
            raise ValueError("config_version must match config")
        for name in (
            "rule_count",
            "domain_team_count",
            "pass_count",
            "watch_count",
            "block_count",
            "routine_review_count",
            "priority_review_count",
            "urgent_review_count",
        ):
            object.__setattr__(self, name, _whole_count(name, getattr(self, name)))
        for name in (
            "average_ambiguity_score",
            "max_ambiguity_score",
            "max_manual_review_priority_score",
        ):
            object.__setattr__(self, name, _probability(name, getattr(self, name)))
        _member(
            "status",
            self.status,
            RESEARCH_STRATEGY_DOMAIN_RESOLUTION_RULE_AMBIGUITY_STATUSES,
        )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _report_reason_codes_value(self.reason_codes),
        )
        _require_hard_flags("report", self)
        _validate_report_derived(self)
        expected_digest = _digest_value(self)
        if self.derived_validation_digest == "":
            object.__setattr__(self, "derived_validation_digest", expected_digest)
        else:
            _require_digest("derived_validation_digest", self.derived_validation_digest)
            if self.derived_validation_digest != expected_digest:
                raise ValueError(
                    "derived_validation_digest must match report fields",
                )


@dataclass(frozen=True)
class _PublicObservation:
    domain_team: str
    public_rule_key: str
    source_reference_count: Decimal
    rule_text_completeness: Decimal
    verifiable_source_coverage: Decimal
    boundary_condition_coverage: Decimal
    exception_clause_coverage: Decimal
    contradiction_pressure: Decimal
    unresolved_term_count: Decimal
    upstream_reason_codes: tuple[str, ...]


def build_research_strategy_domain_resolution_rule_ambiguity_report(
    inputs: tuple[ResearchStrategyDomainResolutionRuleAmbiguityInput, ...]
    | list[ResearchStrategyDomainResolutionRuleAmbiguityInput],
    *,
    generated_at: datetime,
    config: ResearchStrategyDomainResolutionRuleAmbiguityConfig | None = None,
) -> ResearchStrategyDomainResolutionRuleAmbiguityReport:
    if config is None:
        config = ResearchStrategyDomainResolutionRuleAmbiguityConfig()
    config = _require_config_contract("config", config)
    generated_at_utc = _utc("generated_at", generated_at)
    normalized_inputs = _normalize_inputs(inputs)
    observations = tuple(
        _PublicObservation(
            domain_team=value.domain_team,
            public_rule_key=value.public_rule_key,
            source_reference_count=Decimal(len(value.private_source_references)),
            rule_text_completeness=value.rule_text_completeness,
            verifiable_source_coverage=value.verifiable_source_coverage,
            boundary_condition_coverage=value.boundary_condition_coverage,
            exception_clause_coverage=value.exception_clause_coverage,
            contradiction_pressure=value.contradiction_pressure,
            unresolved_term_count=value.unresolved_term_count,
            upstream_reason_codes=value.reason_codes,
        )
        for value in normalized_inputs
    )
    return _assemble_report(
        observations,
        generated_at=generated_at_utc,
        config=config,
    )


def research_strategy_domain_resolution_rule_ambiguity_report_payload(
    report: ResearchStrategyDomainResolutionRuleAmbiguityReport | dict[str, Any],
) -> dict[str, Any]:
    if type(report) is ResearchStrategyDomainResolutionRuleAmbiguityReport:
        _validate_report_derived(report)
        _require_report_digest(report)
        payload = _payload_value(report)
        if type(payload) is not dict:
            raise ValueError("report payload must be a JSON object")
        _verify_payload_digests(payload)
        _reject_unsafe_public_payload(payload)
        return payload
    if type(report) is not dict:
        raise ValueError(
            "report must be a ResearchStrategyDomainResolutionRuleAmbiguityReport "
            "or payload dict",
        )
    _reject_raw_numeric_values(report)
    _require_exact_schema(
        "report payload",
        report,
        ResearchStrategyDomainResolutionRuleAmbiguityReport,
    )
    _require_payload_hard_flags(report)
    _verify_payload_digests(report)
    parsed = _report_from_payload(report)
    observations = tuple(_observation_from_row(row) for row in parsed.rows)
    rebuilt = _assemble_report(
        observations,
        generated_at=parsed.generated_at,
        config=parsed.config,
    )
    canonical = _payload_value(rebuilt)
    if type(canonical) is not dict:
        raise ValueError("canonical report payload must be a JSON object")
    if canonical != report:
        raise ValueError(
            "payload derived status/reason/score/count/aggregates must match "
            "canonical rederivation",
        )
    _reject_unsafe_public_payload(canonical)
    return canonical


def research_strategy_domain_resolution_rule_ambiguity_report_digest(
    report: ResearchStrategyDomainResolutionRuleAmbiguityReport,
) -> str:
    _require_exact_type(
        "report",
        report,
        ResearchStrategyDomainResolutionRuleAmbiguityReport,
    )
    _validate_report_derived(report)
    _require_report_digest(report)
    return report.derived_validation_digest


def _assemble_report(
    observations: tuple[_PublicObservation, ...],
    *,
    generated_at: datetime,
    config: ResearchStrategyDomainResolutionRuleAmbiguityConfig,
) -> ResearchStrategyDomainResolutionRuleAmbiguityReport:
    _reject_duplicate_observations(observations)
    preliminary = tuple(
        _row_from_observation(value, config=config)
        for value in observations
    )
    rows = tuple(sorted(preliminary, key=_row_sort_key))
    aggregates = _report_aggregates(rows)
    reason_codes = _report_reason_codes(rows)
    return ResearchStrategyDomainResolutionRuleAmbiguityReport(
        generated_at=generated_at,
        config=config,
        config_version=config.config_version,
        rule_count=aggregates["rule_count"],
        domain_team_count=aggregates["domain_team_count"],
        pass_count=aggregates["pass_count"],
        watch_count=aggregates["watch_count"],
        block_count=aggregates["block_count"],
        routine_review_count=aggregates["routine_review_count"],
        priority_review_count=aggregates["priority_review_count"],
        urgent_review_count=aggregates["urgent_review_count"],
        average_ambiguity_score=aggregates["average_ambiguity_score"],
        max_ambiguity_score=aggregates["max_ambiguity_score"],
        max_manual_review_priority_score=aggregates[
            "max_manual_review_priority_score"
        ],
        status=_report_status(rows),
        rows=rows,
        reason_code_counts=_reason_code_counts(rows),
        reason_codes=reason_codes,
    )


def _row_from_observation(
    value: _PublicObservation,
    *,
    config: ResearchStrategyDomainResolutionRuleAmbiguityConfig,
) -> ResearchStrategyDomainResolutionRuleAmbiguityRow:
    derived = _derive_row_values(value, config=config)
    return ResearchStrategyDomainResolutionRuleAmbiguityRow(
        domain_team=value.domain_team,
        public_rule_key=value.public_rule_key,
        source_reference_count=value.source_reference_count,
        rule_text_completeness=value.rule_text_completeness,
        verifiable_source_coverage=value.verifiable_source_coverage,
        boundary_condition_coverage=value.boundary_condition_coverage,
        exception_clause_coverage=value.exception_clause_coverage,
        contradiction_pressure=value.contradiction_pressure,
        unresolved_term_count=value.unresolved_term_count,
        upstream_reason_codes=value.upstream_reason_codes,
        rule_text_gap_score=derived["rule_text_gap_score"],
        verifiable_source_gap_score=derived["verifiable_source_gap_score"],
        boundary_condition_gap_score=derived["boundary_condition_gap_score"],
        exception_clause_gap_score=derived["exception_clause_gap_score"],
        unresolved_term_pressure_score=derived["unresolved_term_pressure_score"],
        ambiguity_score=derived["ambiguity_score"],
        manual_review_priority_score=derived["manual_review_priority_score"],
        status=derived["status"],
        manual_review_priority=derived["manual_review_priority"],
        reason_codes=derived["reason_codes"],
        validation_config=config,
    )


def _derive_row_values(
    value: _PublicObservation,
    *,
    config: ResearchStrategyDomainResolutionRuleAmbiguityConfig,
) -> dict[str, Any]:
    with localcontext(_DECIMAL_CONTEXT):
        rule_gap = _quantize(_ONE - value.rule_text_completeness)
        source_gap = _quantize(_ONE - value.verifiable_source_coverage)
        boundary_gap = _quantize(_ONE - value.boundary_condition_coverage)
        exception_gap = _quantize(_ONE - value.exception_clause_coverage)
        unresolved_pressure = _quantize(
            min(
                _ONE,
                value.unresolved_term_count / config.unresolved_term_block_count,
            ),
        )
        ambiguity_score = _quantize(
            rule_gap * config.rule_text_weight
            + source_gap * config.verifiable_source_weight
            + boundary_gap * config.boundary_condition_weight
            + exception_gap * config.exception_clause_weight
            + value.contradiction_pressure * config.contradiction_weight
            + unresolved_pressure * config.unresolved_term_weight,
        )
        priority_score = _quantize(
            max(
                ambiguity_score,
                rule_gap,
                source_gap,
                boundary_gap,
                exception_gap,
                value.contradiction_pressure,
                unresolved_pressure,
            ),
        )
    core_reasons = _core_reason_codes(
        value,
        ambiguity_score=ambiguity_score,
        config=config,
    )
    status = _status_from_core_reasons(core_reasons)
    reason_codes = _canonical_row_reasons(
        core_reasons,
        value.upstream_reason_codes,
    )
    return {
        "rule_text_gap_score": rule_gap,
        "verifiable_source_gap_score": source_gap,
        "boundary_condition_gap_score": boundary_gap,
        "exception_clause_gap_score": exception_gap,
        "unresolved_term_pressure_score": unresolved_pressure,
        "ambiguity_score": ambiguity_score,
        "manual_review_priority_score": priority_score,
        "status": status,
        "manual_review_priority": {
            "pass": "routine",
            "watch": "priority",
            "block": "urgent",
        }[status],
        "reason_codes": reason_codes,
    }


def _core_reason_codes(
    value: _PublicObservation,
    *,
    ambiguity_score: Decimal,
    config: ResearchStrategyDomainResolutionRuleAmbiguityConfig,
) -> tuple[str, ...]:
    reasons: list[str] = []
    if value.source_reference_count == _ZERO:
        reasons.append("no_verifiable_source_reference_block")
    _append_floor_reason(
        reasons,
        "rule_text_completeness",
        value.rule_text_completeness,
        config.pass_rule_text_completeness,
        config.watch_rule_text_completeness,
    )
    _append_floor_reason(
        reasons,
        "verifiable_source_coverage",
        value.verifiable_source_coverage,
        config.pass_verifiable_source_coverage,
        config.watch_verifiable_source_coverage,
    )
    _append_floor_reason(
        reasons,
        "boundary_condition_coverage",
        value.boundary_condition_coverage,
        config.pass_boundary_condition_coverage,
        config.watch_boundary_condition_coverage,
    )
    _append_floor_reason(
        reasons,
        "exception_clause_coverage",
        value.exception_clause_coverage,
        config.pass_exception_clause_coverage,
        config.watch_exception_clause_coverage,
    )
    _append_ceiling_reason(
        reasons,
        "contradiction_pressure",
        value.contradiction_pressure,
        config.pass_contradiction_pressure_ceiling,
        config.watch_contradiction_pressure_ceiling,
    )
    if value.unresolved_term_count >= config.unresolved_term_block_count:
        reasons.append("unresolved_terms_block")
    elif value.unresolved_term_count >= config.unresolved_term_watch_count:
        reasons.append("unresolved_terms_watch")
    if ambiguity_score >= config.block_ambiguity_score:
        reasons.append("ambiguity_score_block")
    elif ambiguity_score >= config.watch_ambiguity_score:
        reasons.append("ambiguity_score_watch")
    return tuple(reasons)


def _append_floor_reason(
    reasons: list[str],
    prefix: str,
    value: Decimal,
    pass_floor: Decimal,
    watch_floor: Decimal,
) -> None:
    if value < watch_floor:
        reasons.append(f"{prefix}_block")
    elif value < pass_floor:
        reasons.append(f"{prefix}_watch")


def _append_ceiling_reason(
    reasons: list[str],
    prefix: str,
    value: Decimal,
    pass_ceiling: Decimal,
    watch_ceiling: Decimal,
) -> None:
    if value > watch_ceiling:
        reasons.append(f"{prefix}_block")
    elif value > pass_ceiling:
        reasons.append(f"{prefix}_watch")


def _status_from_core_reasons(reasons: tuple[str, ...]) -> str:
    if any(reason.endswith("_block") for reason in reasons):
        return "block"
    if any(reason.endswith("_watch") for reason in reasons):
        return "watch"
    return "pass"


def _canonical_row_reasons(
    core_reasons: tuple[str, ...],
    upstream_reason_codes: tuple[str, ...],
) -> tuple[str, ...]:
    reasons = list(core_reasons)
    if not reasons:
        reasons.append("resolution_rule_clear")
    ordered = [
        reason
        for reason in _ROW_REASON_ORDER
        if reason in reasons
    ]
    ordered.extend(f"input_{reason}" for reason in upstream_reason_codes)
    return tuple(ordered)


def _observation_from_row(
    row: ResearchStrategyDomainResolutionRuleAmbiguityRow,
) -> _PublicObservation:
    return _PublicObservation(
        domain_team=row.domain_team,
        public_rule_key=row.public_rule_key,
        source_reference_count=row.source_reference_count,
        rule_text_completeness=row.rule_text_completeness,
        verifiable_source_coverage=row.verifiable_source_coverage,
        boundary_condition_coverage=row.boundary_condition_coverage,
        exception_clause_coverage=row.exception_clause_coverage,
        contradiction_pressure=row.contradiction_pressure,
        unresolved_term_count=row.unresolved_term_count,
        upstream_reason_codes=row.upstream_reason_codes,
    )


def _row_sort_key(
    row: ResearchStrategyDomainResolutionRuleAmbiguityRow,
) -> tuple[Decimal, Decimal, int, str, str]:
    return (
        -row.manual_review_priority_score,
        -row.ambiguity_score,
        {"block": 0, "watch": 1, "pass": 2}[row.status],
        row.domain_team,
        row.public_rule_key,
    )


def _report_aggregates(
    rows: tuple[ResearchStrategyDomainResolutionRuleAmbiguityRow, ...],
) -> dict[str, Decimal]:
    status_counts = Counter(row.status for row in rows)
    priority_counts = Counter(row.manual_review_priority for row in rows)
    average_ambiguity_score = _ZERO
    if rows:
        with localcontext(_DECIMAL_CONTEXT):
            average_ambiguity_score = _quantize(
                sum((row.ambiguity_score for row in rows), _ZERO)
                / Decimal(len(rows)),
            )
    return {
        "rule_count": Decimal(len(rows)),
        "domain_team_count": Decimal(len({row.domain_team for row in rows})),
        "pass_count": Decimal(status_counts["pass"]),
        "watch_count": Decimal(status_counts["watch"]),
        "block_count": Decimal(status_counts["block"]),
        "routine_review_count": Decimal(priority_counts["routine"]),
        "priority_review_count": Decimal(priority_counts["priority"]),
        "urgent_review_count": Decimal(priority_counts["urgent"]),
        "average_ambiguity_score": average_ambiguity_score,
        "max_ambiguity_score": max(
            (row.ambiguity_score for row in rows),
            default=_ZERO,
        ),
        "max_manual_review_priority_score": max(
            (row.manual_review_priority_score for row in rows),
            default=_ZERO,
        ),
    }


def _report_status(
    rows: tuple[ResearchStrategyDomainResolutionRuleAmbiguityRow, ...],
) -> str:
    if not rows or any(row.status == "block" for row in rows):
        return "block"
    if any(row.status == "watch" for row in rows):
        return "watch"
    return "pass"


def _report_reason_codes(
    rows: tuple[ResearchStrategyDomainResolutionRuleAmbiguityRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return ("resolution_rule_report_empty",)
    return tuple(sorted({reason for row in rows for reason in row.reason_codes}))


def _reason_code_counts(
    rows: tuple[ResearchStrategyDomainResolutionRuleAmbiguityRow, ...],
) -> tuple[ResearchStrategyDomainResolutionRuleAmbiguityReasonCodeCount, ...]:
    counts: Counter[str] = Counter()
    for row in rows:
        counts.update(row.reason_codes)
    return tuple(
        ResearchStrategyDomainResolutionRuleAmbiguityReasonCodeCount(
            reason_code=reason,
            count=Decimal(count),
        )
        for reason, count in sorted(counts.items())
    )


def _require_config_contract(
    field_name: str,
    config: object,
) -> ResearchStrategyDomainResolutionRuleAmbiguityConfig:
    _require_exact_type(
        field_name,
        config,
        ResearchStrategyDomainResolutionRuleAmbiguityConfig,
    )
    _require_public_identifier("config_version", config.config_version)
    if (
        config.config_version
        != DEFAULT_RESEARCH_STRATEGY_DOMAIN_RESOLUTION_RULE_AMBIGUITY_REPORT_CONFIG_VERSION
    ):
        raise ValueError("config_version must be the supported config version")
    for name in _CONFIG_PROBABILITY_FIELDS:
        if _probability(name, getattr(config, name)) != getattr(config, name):
            raise ValueError(f"{field_name} {name} must be canonical")
    for name in _CONFIG_WHOLE_COUNT_FIELDS:
        if _whole_count(name, getattr(config, name)) != getattr(config, name):
            raise ValueError(f"{field_name} {name} must be canonical")
    _require_floor_order(
        "rule_text_completeness",
        config.pass_rule_text_completeness,
        config.watch_rule_text_completeness,
    )
    _require_floor_order(
        "verifiable_source_coverage",
        config.pass_verifiable_source_coverage,
        config.watch_verifiable_source_coverage,
    )
    _require_floor_order(
        "boundary_condition_coverage",
        config.pass_boundary_condition_coverage,
        config.watch_boundary_condition_coverage,
    )
    _require_floor_order(
        "exception_clause_coverage",
        config.pass_exception_clause_coverage,
        config.watch_exception_clause_coverage,
    )
    if config.pass_contradiction_pressure_ceiling >= (
        config.watch_contradiction_pressure_ceiling
    ):
        raise ValueError(
            "pass contradiction ceiling must be below watch contradiction ceiling",
        )
    if config.unresolved_term_watch_count <= _ZERO:
        raise ValueError("unresolved_term_watch_count must be positive")
    if config.unresolved_term_block_count <= config.unresolved_term_watch_count:
        raise ValueError(
            "unresolved_term_block_count must exceed unresolved_term_watch_count",
        )
    if config.block_ambiguity_score <= config.watch_ambiguity_score:
        raise ValueError("block_ambiguity_score must exceed watch_ambiguity_score")
    with localcontext(_DECIMAL_CONTEXT):
        weight_sum = _quantize(
            sum((getattr(config, name) for name in _CONFIG_WEIGHT_FIELDS), _ZERO),
        )
    if weight_sum != _ONE:
        raise ValueError("ambiguity score weights must sum to 1")
    _require_hard_flags(field_name, config)
    return config


def _require_input_contract(
    field_name: str,
    value: object,
) -> ResearchStrategyDomainResolutionRuleAmbiguityInput:
    _require_exact_type(
        field_name,
        value,
        ResearchStrategyDomainResolutionRuleAmbiguityInput,
    )
    _require_public_identifier("domain_team", value.domain_team)
    _require_public_identifier("public_rule_key", value.public_rule_key)
    if _private_references(value.private_source_references) != (
        value.private_source_references
    ):
        raise ValueError("private_source_references must be canonical")
    for name in _INPUT_PROBABILITY_FIELDS:
        if _probability(name, getattr(value, name)) != getattr(value, name):
            raise ValueError(f"{field_name} {name} must be canonical")
    if _whole_count("unresolved_term_count", value.unresolved_term_count) != (
        value.unresolved_term_count
    ):
        raise ValueError(f"{field_name} unresolved_term_count must be canonical")
    if _upstream_reason_codes(value.reason_codes) != value.reason_codes:
        raise ValueError(f"{field_name} reason_codes must be canonical")
    if (
        not value.private_source_references
        and value.verifiable_source_coverage != _ZERO
    ):
        raise ValueError(
            "verifiable_source_coverage must be zero without source references",
        )
    _require_hard_flags(field_name, value)
    return value


def _validate_row_derived(
    row: ResearchStrategyDomainResolutionRuleAmbiguityRow,
    *,
    config: ResearchStrategyDomainResolutionRuleAmbiguityConfig,
) -> None:
    expected = _derive_row_values(_observation_from_row(row), config=config)
    for name in (
        "rule_text_gap_score",
        "verifiable_source_gap_score",
        "boundary_condition_gap_score",
        "exception_clause_gap_score",
        "unresolved_term_pressure_score",
        "ambiguity_score",
        "manual_review_priority_score",
        "status",
        "manual_review_priority",
        "reason_codes",
    ):
        if getattr(row, name) != expected[name]:
            raise ValueError(f"{name} must match canonical derived row values")


def _validate_report_derived(
    report: ResearchStrategyDomainResolutionRuleAmbiguityReport,
) -> None:
    _require_hard_flags("report", report)
    _require_config_contract("config", report.config)
    _reject_duplicate_rows(report.rows)
    expected_order = tuple(sorted(report.rows, key=_row_sort_key))
    if report.rows != expected_order:
        raise ValueError("rows must follow stable manual review ordering")
    for row in report.rows:
        _require_hard_flags("row", row)
        _validate_row_derived(row, config=report.config)
        _require_row_digest(row)
    for reason_code_count in report.reason_code_counts:
        _require_hard_flags("reason code count", reason_code_count)
    aggregates = _report_aggregates(report.rows)
    for name, expected in aggregates.items():
        if getattr(report, name) != expected:
            raise ValueError(f"{name} must match rows")
    if report.status != _report_status(report.rows):
        raise ValueError("status must match rows")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")
    if report.reason_code_counts != _reason_code_counts(report.rows):
        raise ValueError("reason_code_counts must match rows")


def _normalize_inputs(
    values: tuple[ResearchStrategyDomainResolutionRuleAmbiguityInput, ...]
    | list[ResearchStrategyDomainResolutionRuleAmbiguityInput],
) -> tuple[ResearchStrategyDomainResolutionRuleAmbiguityInput, ...]:
    if not isinstance(values, (list, tuple)):
        raise ValueError("inputs must be a list or tuple")
    normalized = tuple(values)
    for value in normalized:
        _require_input_contract("input", value)
    seen: set[tuple[str, str]] = set()
    for value in normalized:
        key = (value.domain_team, value.public_rule_key)
        if key in seen:
            raise ValueError("duplicate domain_team and public_rule_key pair")
        seen.add(key)
    return normalized


def _normalize_rows(
    rows: object,
) -> tuple[ResearchStrategyDomainResolutionRuleAmbiguityRow, ...]:
    if type(rows) is not tuple:
        raise ValueError("rows must be a tuple")
    normalized = tuple(rows)
    for row in normalized:
        _require_exact_type(
            "row",
            row,
            ResearchStrategyDomainResolutionRuleAmbiguityRow,
        )
        _require_hard_flags("row", row)
    return normalized


def _normalize_reason_code_counts(
    values: object,
) -> tuple[ResearchStrategyDomainResolutionRuleAmbiguityReasonCodeCount, ...]:
    if type(values) is not tuple:
        raise ValueError("reason_code_counts must be a tuple")
    normalized = tuple(values)
    for value in normalized:
        _require_exact_type(
            "reason code count",
            value,
            ResearchStrategyDomainResolutionRuleAmbiguityReasonCodeCount,
        )
        _require_hard_flags("reason code count", value)
    if normalized != tuple(sorted(normalized, key=lambda item: item.reason_code)):
        raise ValueError("reason_code_counts must be sorted")
    return normalized


def _reject_duplicate_observations(
    values: tuple[_PublicObservation, ...],
) -> None:
    seen: set[tuple[str, str]] = set()
    for value in values:
        key = (value.domain_team, value.public_rule_key)
        if key in seen:
            raise ValueError("duplicate domain_team and public_rule_key pair")
        seen.add(key)


def _reject_duplicate_rows(
    rows: tuple[ResearchStrategyDomainResolutionRuleAmbiguityRow, ...],
) -> None:
    seen: set[tuple[str, str]] = set()
    for row in rows:
        key = (row.domain_team, row.public_rule_key)
        if key in seen:
            raise ValueError("rows contain duplicate domain_team and public_rule_key")
        seen.add(key)


def _report_from_payload(
    payload: dict[str, Any],
) -> ResearchStrategyDomainResolutionRuleAmbiguityReport:
    config_value = payload["config"]
    if type(config_value) is not dict:
        raise ValueError("report payload config schema must be a JSON object")
    config = _config_from_payload(config_value)
    rows_value = payload["rows"]
    if type(rows_value) is not list:
        raise ValueError("report payload rows schema must be a list")
    rows = tuple(
        _row_from_payload(value, config=config, index=index)
        for index, value in enumerate(rows_value)
    )
    counts_value = payload["reason_code_counts"]
    if type(counts_value) is not list:
        raise ValueError("reason_code_counts schema must be a list")
    reason_code_counts = tuple(
        _reason_code_count_from_payload(value, index=index)
        for index, value in enumerate(counts_value)
    )
    report = ResearchStrategyDomainResolutionRuleAmbiguityReport(
        generated_at=_payload_datetime("generated_at", payload["generated_at"]),
        config=config,
        config_version=_payload_string("config_version", payload["config_version"]),
        rule_count=_payload_decimal("rule_count", payload["rule_count"]),
        domain_team_count=_payload_decimal(
            "domain_team_count",
            payload["domain_team_count"],
        ),
        pass_count=_payload_decimal("pass_count", payload["pass_count"]),
        watch_count=_payload_decimal("watch_count", payload["watch_count"]),
        block_count=_payload_decimal("block_count", payload["block_count"]),
        routine_review_count=_payload_decimal(
            "routine_review_count",
            payload["routine_review_count"],
        ),
        priority_review_count=_payload_decimal(
            "priority_review_count",
            payload["priority_review_count"],
        ),
        urgent_review_count=_payload_decimal(
            "urgent_review_count",
            payload["urgent_review_count"],
        ),
        average_ambiguity_score=_payload_decimal(
            "average_ambiguity_score",
            payload["average_ambiguity_score"],
        ),
        max_ambiguity_score=_payload_decimal(
            "max_ambiguity_score",
            payload["max_ambiguity_score"],
        ),
        max_manual_review_priority_score=_payload_decimal(
            "max_manual_review_priority_score",
            payload["max_manual_review_priority_score"],
        ),
        status=_payload_string("status", payload["status"]),
        rows=rows,
        reason_code_counts=reason_code_counts,
        reason_codes=_payload_string_tuple("reason_codes", payload["reason_codes"]),
        derived_validation_digest=_payload_digest(
            "derived_validation_digest",
            payload["derived_validation_digest"],
        ),
        paper_only=_payload_true("paper_only", payload["paper_only"]),
        report_only=_payload_true("report_only", payload["report_only"]),
        readonly=_payload_true("readonly", payload["readonly"]),
    )
    canonical = _payload_value(report)
    if canonical != payload:
        raise ValueError("report payload must use canonical schema values")
    return report


def _config_from_payload(
    payload: dict[str, Any],
) -> ResearchStrategyDomainResolutionRuleAmbiguityConfig:
    _require_exact_schema(
        "config payload",
        payload,
        ResearchStrategyDomainResolutionRuleAmbiguityConfig,
    )
    decimal_names = {
        item.name
        for item in fields(ResearchStrategyDomainResolutionRuleAmbiguityConfig)
        if item.name
        not in {"config_version", "paper_only", "report_only", "readonly"}
    }
    values: dict[str, Any] = {
        name: _payload_decimal(name, payload[name])
        for name in decimal_names
    }
    values.update(
        {
            "config_version": _payload_string(
                "config_version",
                payload["config_version"],
            ),
            "paper_only": _payload_true("paper_only", payload["paper_only"]),
            "report_only": _payload_true("report_only", payload["report_only"]),
            "readonly": _payload_true("readonly", payload["readonly"]),
        },
    )
    return ResearchStrategyDomainResolutionRuleAmbiguityConfig(**values)


def _row_from_payload(
    value: object,
    *,
    config: ResearchStrategyDomainResolutionRuleAmbiguityConfig,
    index: int,
) -> ResearchStrategyDomainResolutionRuleAmbiguityRow:
    label = f"report payload rows[{index}]"
    if type(value) is not dict:
        raise ValueError(f"{label} schema must be a JSON object")
    _require_exact_schema(
        label,
        value,
        ResearchStrategyDomainResolutionRuleAmbiguityRow,
    )
    decimal_names = {
        item.name
        for item in fields(ResearchStrategyDomainResolutionRuleAmbiguityRow)
        if item.name.endswith(("_count", "_score", "_rank"))
        or item.name
        in {
            "rule_text_completeness",
            "verifiable_source_coverage",
            "boundary_condition_coverage",
            "exception_clause_coverage",
            "contradiction_pressure",
        }
    }
    decimal_values = {
        name: _payload_decimal(name, value[name])
        for name in decimal_names
    }
    return ResearchStrategyDomainResolutionRuleAmbiguityRow(
        domain_team=_payload_string("domain_team", value["domain_team"]),
        public_rule_key=_payload_string(
            "public_rule_key",
            value["public_rule_key"],
        ),
        source_reference_count=decimal_values["source_reference_count"],
        rule_text_completeness=decimal_values["rule_text_completeness"],
        verifiable_source_coverage=decimal_values["verifiable_source_coverage"],
        boundary_condition_coverage=decimal_values["boundary_condition_coverage"],
        exception_clause_coverage=decimal_values["exception_clause_coverage"],
        contradiction_pressure=decimal_values["contradiction_pressure"],
        unresolved_term_count=decimal_values["unresolved_term_count"],
        upstream_reason_codes=_payload_string_tuple(
            "upstream_reason_codes",
            value["upstream_reason_codes"],
        ),
        rule_text_gap_score=decimal_values["rule_text_gap_score"],
        verifiable_source_gap_score=decimal_values["verifiable_source_gap_score"],
        boundary_condition_gap_score=decimal_values["boundary_condition_gap_score"],
        exception_clause_gap_score=decimal_values["exception_clause_gap_score"],
        unresolved_term_pressure_score=decimal_values[
            "unresolved_term_pressure_score"
        ],
        ambiguity_score=decimal_values["ambiguity_score"],
        manual_review_priority_score=decimal_values[
            "manual_review_priority_score"
        ],
        status=_payload_string("status", value["status"]),
        manual_review_priority=_payload_string(
            "manual_review_priority",
            value["manual_review_priority"],
        ),
        reason_codes=_payload_string_tuple("reason_codes", value["reason_codes"]),
        derived_validation_digest=_payload_digest(
            "derived_validation_digest",
            value["derived_validation_digest"],
        ),
        paper_only=_payload_true("paper_only", value["paper_only"]),
        report_only=_payload_true("report_only", value["report_only"]),
        readonly=_payload_true("readonly", value["readonly"]),
        validation_config=config,
    )


def _reason_code_count_from_payload(
    value: object,
    *,
    index: int,
) -> ResearchStrategyDomainResolutionRuleAmbiguityReasonCodeCount:
    label = f"report payload reason_code_counts[{index}]"
    if type(value) is not dict:
        raise ValueError(f"{label} schema must be a JSON object")
    _require_exact_schema(
        label,
        value,
        ResearchStrategyDomainResolutionRuleAmbiguityReasonCodeCount,
    )
    return ResearchStrategyDomainResolutionRuleAmbiguityReasonCodeCount(
        reason_code=_payload_string("reason_code", value["reason_code"]),
        count=_payload_decimal("count", value["count"]),
        paper_only=_payload_true("paper_only", value["paper_only"]),
        report_only=_payload_true("report_only", value["report_only"]),
        readonly=_payload_true("readonly", value["readonly"]),
    )


def _require_exact_schema(
    label: str,
    payload: dict[str, Any],
    expected_type: type[object],
) -> None:
    expected = tuple(item.name for item in fields(expected_type))
    if any(type(key) is not str for key in payload):
        raise ValueError(f"{label} schema keys must be canonical strings")
    if tuple(payload) != expected:
        raise ValueError(f"{label} schema fields and order must match exactly")


def _payload_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a canonical Decimal string")
    try:
        decimal_value = Decimal(value)
    except (InvalidOperation, ValueError) as exc:
        raise ValueError(
            f"{field_name} must be a canonical Decimal string",
        ) from exc
    if not decimal_value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    if decimal_value.is_zero() and decimal_value.is_signed():
        raise ValueError(f"{field_name} must not be signed zero")
    if format(decimal_value, "f") != value:
        raise ValueError(f"{field_name} must be a canonical Decimal string")
    return decimal_value


def _payload_datetime(field_name: str, value: object) -> datetime:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a canonical UTC datetime string")
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError as exc:
        raise ValueError(
            f"{field_name} must be a canonical UTC datetime string",
        ) from exc
    normalized = _utc(field_name, parsed)
    if normalized.isoformat() != value:
        raise ValueError(f"{field_name} must be a canonical UTC datetime string")
    return normalized


def _payload_string(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    return value


def _payload_string_tuple(field_name: str, value: object) -> tuple[str, ...]:
    if type(value) is not list:
        raise ValueError(f"{field_name} schema must be a list")
    return tuple(_payload_string(field_name, item) for item in value)


def _payload_true(field_name: str, value: object) -> bool:
    if value is not True:
        raise ValueError(f"{field_name} must be True")
    return True


def _payload_digest(field_name: str, value: object) -> str:
    _require_digest(field_name, value)
    return value


def _verify_payload_digests(payload: dict[str, Any]) -> None:
    supplied = payload.get(_DIGEST_FIELD)
    _require_digest(_DIGEST_FIELD, supplied)
    if supplied != _payload_digest_value(payload):
        raise ValueError("derived_validation_digest must match payload")
    rows = payload.get("rows")
    if type(rows) is not list:
        raise ValueError("report payload rows schema must be a list")
    for row in rows:
        if type(row) is not dict:
            raise ValueError("report payload row schema must be a JSON object")
        row_digest = row.get(_DIGEST_FIELD)
        _require_digest(_DIGEST_FIELD, row_digest)
        if row_digest != _payload_digest_value(row):
            raise ValueError("derived_validation_digest must match payload row")


def _require_report_digest(
    report: ResearchStrategyDomainResolutionRuleAmbiguityReport,
) -> None:
    if report.derived_validation_digest != _digest_value(report):
        raise ValueError("derived_validation_digest must match report fields")


def _require_row_digest(
    row: ResearchStrategyDomainResolutionRuleAmbiguityRow,
) -> None:
    if row.derived_validation_digest != _digest_value(row):
        raise ValueError("derived_validation_digest must match row fields")


def _digest_value(value: object) -> str:
    payload = _payload_value(value)
    if type(payload) is not dict:
        raise ValueError("digest payload must be a JSON object")
    return _payload_digest_value(payload)


def _payload_digest_value(payload: dict[str, Any]) -> str:
    unsigned = dict(payload)
    unsigned.pop(_DIGEST_FIELD, None)
    encoded = json.dumps(
        unsigned,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    )
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def _payload_value(value: object) -> Any:
    if type(value) is Decimal:
        if not value.is_finite():
            raise ValueError("payload Decimal values must be finite")
        if value.is_zero() and value.is_signed():
            raise ValueError("payload Decimal values must not be signed zero")
        return format(value, "f")
    if isinstance(value, Decimal):
        raise ValueError("payload Decimal values must be exactly Decimal")
    if type(value) is datetime:
        return _utc("payload datetime", value).isoformat()
    if isinstance(value, datetime):
        raise ValueError("payload datetime values must be exactly datetime")
    if is_dataclass(value) and not isinstance(value, type):
        return {
            item.name: _payload_value(getattr(value, item.name))
            for item in fields(value)
        }
    if type(value) is tuple:
        return [_payload_value(item) for item in value]
    if type(value) is list:
        return [_payload_value(item) for item in value]
    if type(value) is dict:
        ready: dict[str, Any] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("payload object keys must be strings")
            ready[key] = _payload_value(item)
        return ready
    if value is None or type(value) in (str, bool):
        return value
    if type(value) in (int, float):
        raise ValueError("payload numeric values must use Decimal strings")
    raise ValueError("payload contains unsupported value")


def _reject_raw_numeric_values(value: object) -> None:
    if type(value) in (int, float, Decimal):
        raise ValueError("public numeric values must be Decimal strings")
    if type(value) is dict:
        for item in value.values():
            _reject_raw_numeric_values(item)
    elif type(value) is list:
        for item in value:
            _reject_raw_numeric_values(item)


def _reject_unsafe_public_payload(value: object) -> None:
    if type(value) is dict:
        if "private_source_references" in value:
            raise ValueError("private source references must not enter public payloads")
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("public payload keys must be strings")
            _reject_unsafe_public_payload(item)
        return
    if type(value) is list:
        for item in value:
            _reject_unsafe_public_payload(item)
        return
    if type(value) is str:
        _reject_unsafe_public_text("public payload value", value)


def _reject_unsafe_public_text(field_name: str, value: str) -> None:
    lowered = value.lower()
    if lowered.startswith(_RAW_QUESTION_PREFIXES) or "?" in value:
        raise ValueError(f"{field_name} contains raw question text")
    if any(fragment in lowered for fragment in _UNSAFE_PUBLIC_VALUE_FRAGMENTS):
        raise ValueError(f"{field_name} contains unsafe private material")


def _private_references(value: object) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ValueError("private_source_references must be a tuple")
    normalized: list[str] = []
    for item in value:
        if type(item) is not str or not item or item.strip() != item:
            raise ValueError("private source references must be nonempty strings")
        normalized.append(item)
    if len(normalized) != len(set(normalized)):
        raise ValueError("private source references must be unique")
    return tuple(normalized)


def _upstream_reason_codes(value: object) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ValueError("reason_codes must be a tuple")
    normalized = tuple(
        _require_public_identifier("reason_code", item)
        for item in value
    )
    if len(normalized) != len(set(normalized)):
        raise ValueError("reason_codes must be unique")
    return tuple(sorted(normalized))


def _row_reason_codes(value: object) -> tuple[str, ...]:
    if type(value) is not tuple or not value:
        raise ValueError("reason_codes must be a nonempty tuple")
    normalized = tuple(
        _require_public_identifier("reason_code", item)
        for item in value
    )
    if len(normalized) != len(set(normalized)):
        raise ValueError("reason_codes must be unique")
    core = tuple(item for item in _ROW_REASON_ORDER if item in normalized)
    upstream = tuple(sorted(item for item in normalized if item.startswith("input_")))
    canonical = (*core, *upstream)
    if normalized != canonical:
        raise ValueError("reason_codes must use canonical ordering")
    return normalized


def _report_reason_codes_value(value: object) -> tuple[str, ...]:
    if type(value) is not tuple or not value:
        raise ValueError("reason_codes must be a nonempty tuple")
    normalized = tuple(
        _require_public_identifier("reason_code", item)
        for item in value
    )
    if len(normalized) != len(set(normalized)):
        raise ValueError("reason_codes must be unique")
    if normalized != tuple(sorted(normalized)):
        raise ValueError("reason_codes must be sorted")
    return normalized


def _probability(field_name: str, value: object) -> Decimal:
    decimal_value = _decimal(field_name, value)
    if decimal_value < _ZERO or decimal_value > _ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return _quantize(decimal_value)


def _whole_count(field_name: str, value: object) -> Decimal:
    decimal_value = _decimal(field_name, value)
    if decimal_value < _ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    if decimal_value != decimal_value.to_integral_value():
        raise ValueError(f"{field_name} must be a whole Decimal")
    return decimal_value


def _positive_whole_count(field_name: str, value: object) -> Decimal:
    decimal_value = _whole_count(field_name, value)
    if decimal_value <= _ZERO:
        raise ValueError(f"{field_name} must be positive")
    return decimal_value


def _decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    if value.is_zero() and value.is_signed():
        raise ValueError(f"{field_name} must not be signed zero")
    return value


def _quantize(value: Decimal) -> Decimal:
    with localcontext(_DECIMAL_CONTEXT):
        return value.quantize(_QUANTUM, rounding=ROUND_HALF_EVEN)


def _utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_public_identifier(field_name: str, value: object) -> str:
    if type(value) is not str or not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a nonempty canonical string")
    allowed = set("abcdefghijklmnopqrstuvwxyz0123456789-_")
    separators = {"-", "_"}
    if (
        any(character not in allowed for character in value)
        or value[0] in separators
        or value[-1] in separators
        or any(
            left in separators and right in separators
            for left, right in zip(value, value[1:], strict=False)
        )
    ):
        raise ValueError(f"{field_name} must be a lowercase public identifier")
    _reject_unsafe_public_text(field_name, value)
    return value


def _require_floor_order(
    field_name: str,
    pass_floor: Decimal,
    watch_floor: Decimal,
) -> None:
    if pass_floor <= watch_floor:
        raise ValueError(f"{field_name} pass floor must exceed watch floor")


def _member(field_name: str, value: object, allowed: tuple[str, ...]) -> None:
    if type(value) is not str or value not in allowed:
        raise ValueError(f"{field_name} must be a known value")


def _require_digest(field_name: str, value: object) -> None:
    if type(value) is not str or len(value) != 64:
        raise ValueError(f"{field_name} must be a sha256 digest")
    if any(character not in "0123456789abcdef" for character in value):
        raise ValueError(f"{field_name} must be a sha256 digest")


def _require_hard_flags(field_name: str, value: object) -> None:
    for name in ("paper_only", "report_only", "readonly"):
        if getattr(value, name, None) is not True:
            raise ValueError(f"{field_name} {name} must be True")


def _require_payload_hard_flags(payload: dict[str, object]) -> None:
    for name in ("paper_only", "report_only", "readonly"):
        if payload.get(name) is not True:
            raise ValueError(f"payload {name} must be True")


def _require_exact_type(
    field_name: str,
    value: object,
    expected: type[object],
) -> None:
    if type(value) is not expected:
        raise ValueError(f"{field_name} must be exactly {expected.__name__}")


ResearchStrategyDomainResolutionRuleAmbiguityReportConfig = (
    ResearchStrategyDomainResolutionRuleAmbiguityConfig
)


__all__ = (
    "DEFAULT_RESEARCH_STRATEGY_DOMAIN_RESOLUTION_RULE_AMBIGUITY_REPORT_CONFIG_VERSION",
    "MANUAL_REVIEW_PRIORITIES",
    "RESEARCH_STRATEGY_DOMAIN_RESOLUTION_RULE_AMBIGUITY_STATUSES",
    "ResearchStrategyDomainResolutionRuleAmbiguityConfig",
    "ResearchStrategyDomainResolutionRuleAmbiguityInput",
    "ResearchStrategyDomainResolutionRuleAmbiguityReasonCodeCount",
    "ResearchStrategyDomainResolutionRuleAmbiguityReport",
    "ResearchStrategyDomainResolutionRuleAmbiguityReportConfig",
    "ResearchStrategyDomainResolutionRuleAmbiguityRow",
    "build_research_strategy_domain_resolution_rule_ambiguity_report",
    "research_strategy_domain_resolution_rule_ambiguity_report_digest",
    "research_strategy_domain_resolution_rule_ambiguity_report_payload",
)
