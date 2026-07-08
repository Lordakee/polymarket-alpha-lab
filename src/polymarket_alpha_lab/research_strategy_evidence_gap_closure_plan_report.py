"""Report-only evidence gap closure plan before analyst review.

The report turns source readiness, contradiction severity, update freshness,
domain coverage, and resolution-rule linkage into deterministic plan rows. It
does not expose recommendation, order, sizing, wallet, authentication, database,
network, scraping, or live execution surfaces.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import InitVar, dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal, ROUND_HALF_UP
from hashlib import sha256
import json
import re
from typing import Any, Mapping, Sequence


DEFAULT_RESEARCH_STRATEGY_EVIDENCE_GAP_CLOSURE_PLAN_REPORT_CONFIG_VERSION = (
    "research-strategy-evidence-gap-closure-plan-report-v0"
)

STATUS_PASS = "pass"
STATUS_WATCH = "watch"
STATUS_BLOCK = "block"

REASON_EMPTY_INPUT = "empty_input"
REASON_ANALYST_REVIEW_REQUESTED = "analyst_review_requested"
REASON_RESOLUTION_RULE_MISSING = "resolution_rule_missing"
REASON_SOURCE_READINESS_BLOCK = "source_readiness_block"
REASON_CONTRADICTION_SEVERITY_BLOCK = "contradiction_severity_block"
REASON_UPDATE_FRESHNESS_BLOCK = "update_freshness_block"
REASON_DOMAIN_COVERAGE_BLOCK = "domain_coverage_block"
REASON_RESOLUTION_RULE_LINKAGE_BLOCK = "resolution_rule_linkage_block"
REASON_CLOSURE_READINESS_SCORE_BLOCK = "closure_readiness_score_block"
REASON_SOURCE_READINESS_WATCH = "source_readiness_watch"
REASON_CONTRADICTION_SEVERITY_WATCH = "contradiction_severity_watch"
REASON_UPDATE_FRESHNESS_WATCH = "update_freshness_watch"
REASON_DOMAIN_COVERAGE_WATCH = "domain_coverage_watch"
REASON_RESOLUTION_RULE_LINKAGE_WATCH = "resolution_rule_linkage_watch"
REASON_CLOSURE_READINESS_SCORE_WATCH = "closure_readiness_score_watch"
REASON_EVIDENCE_GAP_CLOSURE_PLAN_PASS = "evidence_gap_closure_plan_pass"

PASS_CLOSURE_STEP = "retain_analyst_review_packet_readiness"
WATCH_CLOSURE_STEP = "refresh_public_evidence_before_analyst_review"
BLOCK_CLOSURE_STEP = "block_analyst_review_until_evidence_gap_closed"

_UPSTREAM_REASON_CODE_SEQUENCE = (
    REASON_ANALYST_REVIEW_REQUESTED,
    REASON_RESOLUTION_RULE_MISSING,
)
_GENERATED_ROW_REASON_CODE_SEQUENCE = (
    REASON_SOURCE_READINESS_BLOCK,
    REASON_CONTRADICTION_SEVERITY_BLOCK,
    REASON_UPDATE_FRESHNESS_BLOCK,
    REASON_DOMAIN_COVERAGE_BLOCK,
    REASON_RESOLUTION_RULE_LINKAGE_BLOCK,
    REASON_CLOSURE_READINESS_SCORE_BLOCK,
    REASON_SOURCE_READINESS_WATCH,
    REASON_CONTRADICTION_SEVERITY_WATCH,
    REASON_UPDATE_FRESHNESS_WATCH,
    REASON_DOMAIN_COVERAGE_WATCH,
    REASON_RESOLUTION_RULE_LINKAGE_WATCH,
    REASON_CLOSURE_READINESS_SCORE_WATCH,
    REASON_EVIDENCE_GAP_CLOSURE_PLAN_PASS,
)
_ROW_REASON_CODE_SEQUENCE = (
    *_UPSTREAM_REASON_CODE_SEQUENCE,
    *_GENERATED_ROW_REASON_CODE_SEQUENCE,
)
_REASON_CODE_SEQUENCE = (REASON_EMPTY_INPUT, *_ROW_REASON_CODE_SEQUENCE)
_BLOCK_REASON_CODES = frozenset(
    (
        REASON_SOURCE_READINESS_BLOCK,
        REASON_CONTRADICTION_SEVERITY_BLOCK,
        REASON_UPDATE_FRESHNESS_BLOCK,
        REASON_DOMAIN_COVERAGE_BLOCK,
        REASON_RESOLUTION_RULE_LINKAGE_BLOCK,
        REASON_CLOSURE_READINESS_SCORE_BLOCK,
    ),
)
_WATCH_REASON_CODES = frozenset(
    (
        REASON_SOURCE_READINESS_WATCH,
        REASON_CONTRADICTION_SEVERITY_WATCH,
        REASON_UPDATE_FRESHNESS_WATCH,
        REASON_DOMAIN_COVERAGE_WATCH,
        REASON_RESOLUTION_RULE_LINKAGE_WATCH,
        REASON_CLOSURE_READINESS_SCORE_WATCH,
    ),
)
_CLOSURE_STEPS = frozenset(
    (PASS_CLOSURE_STEP, WATCH_CLOSURE_STEP, BLOCK_CLOSURE_STEP),
)

_QUANT = Decimal("0.000001")
_ZERO = Decimal("0.000000")
_ONE = Decimal("1.000000")
_DIGEST_FIELD = "derived_validation_digest"
_STATUS_VALUES = frozenset((STATUS_PASS, STATUS_WATCH, STATUS_BLOCK))
_PHASE_FLAG_FIELDS = frozenset(("paper_only", "report_only", "readonly"))
_PUBLIC_IDENTIFIER_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,127}$")
_DIGEST_RE = re.compile(r"^[0-9a-f]{64}$")
_PRIVATE_DIGEST_RE = re.compile(r"^sha256:[0-9a-f]{64}$")
_UNSAFE_PUBLIC_FRAGMENTS = (
    "raw_candidate",
    "candidate_id",
    "candidate-",
    "market_id",
    "market_slug",
    "market-slug",
    "market_question",
    "question",
    "source_url",
    "source-url",
    "source url",
    "source_text",
    "source-text",
    "source text",
    "raw_source",
    "dsn",
    "database",
    "table",
    "token",
    "wallet",
    "auth",
    "order",
    "trade",
    "position",
    "sizing",
    "buy",
    "sell",
    "recommendation",
    "recommended",
    "recommend",
    "private key",
    "private_key",
    "secret",
    "credential",
    "http://",
    "https://",
    "://",
)


class _FinalPublicDataclass:
    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        for base in cls.__bases__:
            if base is not _FinalPublicDataclass and issubclass(
                base,
                _FinalPublicDataclass,
            ):
                raise TypeError(f"{base.__name__} may not be subclassed")


@dataclass(frozen=True)
class ResearchStrategyEvidenceGapClosurePlanConfig(_FinalPublicDataclass):
    config_version: str = (
        DEFAULT_RESEARCH_STRATEGY_EVIDENCE_GAP_CLOSURE_PLAN_REPORT_CONFIG_VERSION
    )
    pass_min_closure_readiness_score: Decimal = Decimal("0.800000")
    watch_min_closure_readiness_score: Decimal = Decimal("0.600000")
    min_pass_source_readiness_score: Decimal = Decimal("0.800000")
    min_watch_source_readiness_score: Decimal = Decimal("0.600000")
    max_pass_contradiction_severity_score: Decimal = Decimal("0.200000")
    max_watch_contradiction_severity_score: Decimal = Decimal("0.450000")
    min_pass_update_freshness_score: Decimal = Decimal("0.800000")
    min_watch_update_freshness_score: Decimal = Decimal("0.600000")
    min_pass_domain_coverage_score: Decimal = Decimal("0.800000")
    min_watch_domain_coverage_score: Decimal = Decimal("0.600000")
    min_pass_resolution_rule_linkage_score: Decimal = Decimal("0.800000")
    min_watch_resolution_rule_linkage_score: Decimal = Decimal("0.600000")
    source_readiness_weight: Decimal = Decimal("0.250000")
    contradiction_clarity_weight: Decimal = Decimal("0.200000")
    update_freshness_weight: Decimal = Decimal("0.200000")
    domain_coverage_weight: Decimal = Decimal("0.150000")
    resolution_rule_linkage_weight: Decimal = Decimal("0.200000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchStrategyEvidenceGapClosurePlanConfig,
            "config",
        )
        object.__setattr__(
            self,
            "config_version",
            _require_public_identifier("config_version", self.config_version),
        )
        if (
            self.config_version
            != DEFAULT_RESEARCH_STRATEGY_EVIDENCE_GAP_CLOSURE_PLAN_REPORT_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "pass_min_closure_readiness_score",
            "watch_min_closure_readiness_score",
            "min_pass_source_readiness_score",
            "min_watch_source_readiness_score",
            "max_pass_contradiction_severity_score",
            "max_watch_contradiction_severity_score",
            "min_pass_update_freshness_score",
            "min_watch_update_freshness_score",
            "min_pass_domain_coverage_score",
            "min_watch_domain_coverage_score",
            "min_pass_resolution_rule_linkage_score",
            "min_watch_resolution_rule_linkage_score",
            "source_readiness_weight",
            "contradiction_clarity_weight",
            "update_freshness_weight",
            "domain_coverage_weight",
            "resolution_rule_linkage_weight",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        if self.pass_min_closure_readiness_score < self.watch_min_closure_readiness_score:
            raise ValueError(
                "pass_min_closure_readiness_score must be at least "
                "watch_min_closure_readiness_score",
            )
        if self.min_pass_source_readiness_score < self.min_watch_source_readiness_score:
            raise ValueError(
                "min_pass_source_readiness_score must be at least "
                "min_watch_source_readiness_score",
            )
        if (
            self.max_pass_contradiction_severity_score
            > self.max_watch_contradiction_severity_score
        ):
            raise ValueError(
                "max_pass_contradiction_severity_score must not exceed "
                "max_watch_contradiction_severity_score",
            )
        if self.min_pass_update_freshness_score < self.min_watch_update_freshness_score:
            raise ValueError(
                "min_pass_update_freshness_score must be at least "
                "min_watch_update_freshness_score",
            )
        if self.min_pass_domain_coverage_score < self.min_watch_domain_coverage_score:
            raise ValueError(
                "min_pass_domain_coverage_score must be at least "
                "min_watch_domain_coverage_score",
            )
        if (
            self.min_pass_resolution_rule_linkage_score
            < self.min_watch_resolution_rule_linkage_score
        ):
            raise ValueError(
                "min_pass_resolution_rule_linkage_score must be at least "
                "min_watch_resolution_rule_linkage_score",
            )
        weight_sum = _quantize(
            self.source_readiness_weight
            + self.contradiction_clarity_weight
            + self.update_freshness_weight
            + self.domain_coverage_weight
            + self.resolution_rule_linkage_weight,
        )
        if weight_sum != _ONE:
            raise ValueError("config weights must sum to one")
        _require_hard_flags("config", self)
        _reject_unsafe_public_payload("config", self)


@dataclass(frozen=True)
class ResearchStrategyEvidenceGapClosurePlanInput(_FinalPublicDataclass):
    evidence_gap_ref: str
    source_readiness_score: Decimal
    contradiction_severity_score: Decimal
    update_freshness_score: Decimal
    domain_coverage_score: Decimal
    resolution_rule_linkage_score: Decimal
    observed_at: datetime
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchStrategyEvidenceGapClosurePlanInput, "input")
        object.__setattr__(
            self,
            "evidence_gap_ref",
            _require_private_ref("evidence_gap_ref", self.evidence_gap_ref),
        )
        for field_name in (
            "source_readiness_score",
            "contradiction_severity_score",
            "update_freshness_score",
            "domain_coverage_score",
            "resolution_rule_linkage_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_upstream_reason_codes(self.reason_codes),
        )
        _require_hard_flags("input", self)


@dataclass(frozen=True)
class ResearchStrategyEvidenceGapClosurePlanStep(_FinalPublicDataclass):
    evidence_gap_digest: str
    source_readiness_score: Decimal
    source_gap_score: Decimal
    contradiction_severity_score: Decimal
    contradiction_clarity_score: Decimal
    update_freshness_score: Decimal
    update_staleness_score: Decimal
    domain_coverage_score: Decimal
    domain_gap_score: Decimal
    resolution_rule_linkage_score: Decimal
    resolution_rule_gap_score: Decimal
    closure_readiness_score: Decimal
    observed_at: datetime
    status: str
    closure_step: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True
    validation_config: InitVar[ResearchStrategyEvidenceGapClosurePlanConfig | None] = None

    def __post_init__(
        self,
        validation_config: ResearchStrategyEvidenceGapClosurePlanConfig | None,
    ) -> None:
        _require_exact_type(self, ResearchStrategyEvidenceGapClosurePlanStep, "step")
        object.__setattr__(
            self,
            "evidence_gap_digest",
            _require_private_digest("evidence_gap_digest", self.evidence_gap_digest),
        )
        for field_name in (
            "source_readiness_score",
            "source_gap_score",
            "contradiction_severity_score",
            "contradiction_clarity_score",
            "update_freshness_score",
            "update_staleness_score",
            "domain_coverage_score",
            "domain_gap_score",
            "resolution_rule_linkage_score",
            "resolution_rule_gap_score",
            "closure_readiness_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        object.__setattr__(self, "status", _require_status("status", self.status))
        object.__setattr__(
            self,
            "closure_step",
            _require_closure_step("closure_step", self.closure_step),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_row_reason_codes(self.reason_codes),
        )
        _validate_step(self, validation_config)
        _require_hard_flags("step", self)
        _reject_unsafe_public_payload("step", self)


@dataclass(frozen=True)
class ResearchStrategyEvidenceGapClosurePlanReasonCodeCount(_FinalPublicDataclass):
    reason_code: str
    count: Decimal
    row_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchStrategyEvidenceGapClosurePlanReasonCodeCount,
            "reason count",
        )
        object.__setattr__(
            self,
            "reason_code",
            _require_reason_code("reason_code", self.reason_code, _REASON_CODE_SEQUENCE),
        )
        object.__setattr__(
            self,
            "count",
            _require_nonnegative_count_decimal("count", self.count),
        )
        object.__setattr__(
            self,
            "row_ratio",
            _require_ratio_decimal("row_ratio", self.row_ratio),
        )
        _require_hard_flags("reason count", self)
        _reject_unsafe_public_payload("reason count", self)


@dataclass(frozen=True)
class ResearchStrategyEvidenceGapClosurePlanReport(_FinalPublicDataclass):
    generated_at: datetime
    config_version: str
    status: str
    row_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    average_closure_readiness_score: Decimal
    min_source_readiness_score: Decimal
    max_contradiction_severity_score: Decimal
    min_update_freshness_score: Decimal
    min_domain_coverage_score: Decimal
    min_resolution_rule_linkage_score: Decimal
    rows: tuple[ResearchStrategyEvidenceGapClosurePlanStep, ...]
    reason_code_counts: tuple[
        ResearchStrategyEvidenceGapClosurePlanReasonCodeCount,
        ...,
    ]
    reason_codes: tuple[str, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchStrategyEvidenceGapClosurePlanReport, "report")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        object.__setattr__(
            self,
            "config_version",
            _require_public_identifier("config_version", self.config_version),
        )
        if (
            self.config_version
            != DEFAULT_RESEARCH_STRATEGY_EVIDENCE_GAP_CLOSURE_PLAN_REPORT_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        object.__setattr__(self, "status", _require_status("status", self.status))
        for field_name in ("row_count", "pass_count", "watch_count", "block_count"):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_count_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "average_closure_readiness_score",
            "min_source_readiness_score",
            "max_contradiction_severity_score",
            "min_update_freshness_score",
            "min_domain_coverage_score",
            "min_resolution_rule_linkage_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(self, "rows", _normalize_steps(self.rows))
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_report_reason_codes(self.reason_codes),
        )
        _validate_report(self)
        _require_hard_flags("report", self)
        _reject_unsafe_public_payload("report", self)
        expected_digest = _report_digest(self)
        if self.derived_validation_digest == "":
            object.__setattr__(self, _DIGEST_FIELD, expected_digest)
        elif self.derived_validation_digest != expected_digest:
            raise ValueError("derived_validation_digest mismatch")
        _require_digest(_DIGEST_FIELD, self.derived_validation_digest)

    @property
    def payload(self) -> dict[str, object]:
        return research_strategy_evidence_gap_closure_plan_report_payload(self)


def build_research_strategy_evidence_gap_closure_plan_report(
    inputs: Sequence[ResearchStrategyEvidenceGapClosurePlanInput],
    *,
    generated_at: datetime,
    config: ResearchStrategyEvidenceGapClosurePlanConfig | None = None,
) -> ResearchStrategyEvidenceGapClosurePlanReport:
    """Build a deterministic, readonly plan for closing evidence gaps."""

    cfg = config or ResearchStrategyEvidenceGapClosurePlanConfig()
    if type(cfg) is not ResearchStrategyEvidenceGapClosurePlanConfig:
        raise ValueError("config must be a ResearchStrategyEvidenceGapClosurePlanConfig")
    _require_hard_flags("config", cfg)
    report_time = _as_utc("generated_at", generated_at)
    normalized_inputs = _normalize_inputs(inputs)
    for item in normalized_inputs:
        if item.observed_at > report_time:
            raise ValueError("observed_at must not be after generated_at")
    rows = tuple(
        sorted(
            (_step_for_input(item, cfg) for item in normalized_inputs),
            key=_step_sort_key,
        ),
    )
    reason_code_counts = _reason_code_counts(rows)
    reason_codes = tuple(row.reason_code for row in reason_code_counts)
    if not rows:
        reason_code_counts = (
            ResearchStrategyEvidenceGapClosurePlanReasonCodeCount(
                reason_code=REASON_EMPTY_INPUT,
                count=_ONE,
                row_ratio=_ONE,
            ),
        )
        reason_codes = (REASON_EMPTY_INPUT,)
    values: dict[str, object] = {
        "generated_at": report_time,
        "config_version": cfg.config_version,
        "status": _report_status(rows),
        "row_count": _decimal_count(len(rows)),
        "pass_count": _decimal_count(_status_count(rows, STATUS_PASS)),
        "watch_count": _decimal_count(_status_count(rows, STATUS_WATCH)),
        "block_count": _decimal_count(_status_count(rows, STATUS_BLOCK)),
        "average_closure_readiness_score": _average_ratio(
            tuple(row.closure_readiness_score for row in rows),
        ),
        "min_source_readiness_score": min(
            (row.source_readiness_score for row in rows),
            default=_ZERO,
        ),
        "max_contradiction_severity_score": max(
            (row.contradiction_severity_score for row in rows),
            default=_ZERO,
        ),
        "min_update_freshness_score": min(
            (row.update_freshness_score for row in rows),
            default=_ZERO,
        ),
        "min_domain_coverage_score": min(
            (row.domain_coverage_score for row in rows),
            default=_ZERO,
        ),
        "min_resolution_rule_linkage_score": min(
            (row.resolution_rule_linkage_score for row in rows),
            default=_ZERO,
        ),
        "rows": rows,
        "reason_code_counts": reason_code_counts,
        "reason_codes": reason_codes,
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    return ResearchStrategyEvidenceGapClosurePlanReport(
        **values,
        derived_validation_digest=_report_digest_from_values(values),
    )


def research_strategy_evidence_gap_closure_plan_report_payload(
    report: ResearchStrategyEvidenceGapClosurePlanReport | Mapping[str, object],
) -> dict[str, object]:
    """Return a deterministic public payload and validate supplied payloads."""

    if type(report) is ResearchStrategyEvidenceGapClosurePlanReport:
        payload = _report_payload(report)
        _reject_unsafe_public_payload(
            "report payload",
            payload,
            allow_json_containers=True,
        )
        _validate_payload_statuses(payload)
        _validate_payload_digest(payload)
        return _copy_json_object(payload)
    if isinstance(report, Mapping):
        copied = _copy_json_value(report)
        if type(copied) is not dict:
            raise ValueError("payload must be a JSON object")
        _reject_unsafe_public_payload(
            "report payload",
            copied,
            allow_json_containers=True,
        )
        _validate_payload_statuses(copied)
        _validate_payload_digest(copied)
        return _copy_json_object(copied)
    raise ValueError("report must be a ResearchStrategyEvidenceGapClosurePlanReport")


def _step_for_input(
    item: ResearchStrategyEvidenceGapClosurePlanInput,
    config: ResearchStrategyEvidenceGapClosurePlanConfig,
) -> ResearchStrategyEvidenceGapClosurePlanStep:
    source_gap = _inverse_ratio(item.source_readiness_score)
    contradiction_clarity = _inverse_ratio(item.contradiction_severity_score)
    update_staleness = _inverse_ratio(item.update_freshness_score)
    domain_gap = _inverse_ratio(item.domain_coverage_score)
    resolution_rule_gap = _inverse_ratio(item.resolution_rule_linkage_score)
    closure_readiness = _closure_readiness_score(
        source_readiness_score=item.source_readiness_score,
        contradiction_clarity_score=contradiction_clarity,
        update_freshness_score=item.update_freshness_score,
        domain_coverage_score=item.domain_coverage_score,
        resolution_rule_linkage_score=item.resolution_rule_linkage_score,
        config=config,
    )
    reason_codes = _step_reason_codes(item, closure_readiness, config)
    status = _step_status(reason_codes)
    return ResearchStrategyEvidenceGapClosurePlanStep(
        evidence_gap_digest=_private_ref_digest(item.evidence_gap_ref),
        source_readiness_score=item.source_readiness_score,
        source_gap_score=source_gap,
        contradiction_severity_score=item.contradiction_severity_score,
        contradiction_clarity_score=contradiction_clarity,
        update_freshness_score=item.update_freshness_score,
        update_staleness_score=update_staleness,
        domain_coverage_score=item.domain_coverage_score,
        domain_gap_score=domain_gap,
        resolution_rule_linkage_score=item.resolution_rule_linkage_score,
        resolution_rule_gap_score=resolution_rule_gap,
        closure_readiness_score=closure_readiness,
        observed_at=item.observed_at,
        status=status,
        closure_step=_closure_step(status),
        reason_codes=reason_codes,
        validation_config=config,
    )


def _step_reason_codes(
    item: ResearchStrategyEvidenceGapClosurePlanInput,
    closure_readiness_score: Decimal,
    config: ResearchStrategyEvidenceGapClosurePlanConfig,
) -> tuple[str, ...]:
    reasons: list[str] = list(item.reason_codes)
    if item.source_readiness_score < config.min_watch_source_readiness_score:
        reasons.append(REASON_SOURCE_READINESS_BLOCK)
    elif item.source_readiness_score < config.min_pass_source_readiness_score:
        reasons.append(REASON_SOURCE_READINESS_WATCH)
    if item.contradiction_severity_score > config.max_watch_contradiction_severity_score:
        reasons.append(REASON_CONTRADICTION_SEVERITY_BLOCK)
    elif item.contradiction_severity_score > config.max_pass_contradiction_severity_score:
        reasons.append(REASON_CONTRADICTION_SEVERITY_WATCH)
    if item.update_freshness_score < config.min_watch_update_freshness_score:
        reasons.append(REASON_UPDATE_FRESHNESS_BLOCK)
    elif item.update_freshness_score < config.min_pass_update_freshness_score:
        reasons.append(REASON_UPDATE_FRESHNESS_WATCH)
    if item.domain_coverage_score < config.min_watch_domain_coverage_score:
        reasons.append(REASON_DOMAIN_COVERAGE_BLOCK)
    elif item.domain_coverage_score < config.min_pass_domain_coverage_score:
        reasons.append(REASON_DOMAIN_COVERAGE_WATCH)
    if (
        item.resolution_rule_linkage_score
        < config.min_watch_resolution_rule_linkage_score
    ):
        reasons.append(REASON_RESOLUTION_RULE_LINKAGE_BLOCK)
    elif (
        item.resolution_rule_linkage_score
        < config.min_pass_resolution_rule_linkage_score
    ):
        reasons.append(REASON_RESOLUTION_RULE_LINKAGE_WATCH)
    if closure_readiness_score < config.watch_min_closure_readiness_score:
        reasons.append(REASON_CLOSURE_READINESS_SCORE_BLOCK)
    elif closure_readiness_score < config.pass_min_closure_readiness_score:
        reasons.append(REASON_CLOSURE_READINESS_SCORE_WATCH)
    generated = tuple(
        reason for reason in reasons if reason in _GENERATED_ROW_REASON_CODE_SEQUENCE
    )
    if not generated:
        reasons.append(REASON_EVIDENCE_GAP_CLOSURE_PLAN_PASS)
    return _normalize_row_reason_codes(tuple(reasons))


def _step_status(reason_codes: tuple[str, ...]) -> str:
    if any(reason_code in _BLOCK_REASON_CODES for reason_code in reason_codes):
        return STATUS_BLOCK
    if any(reason_code in _WATCH_REASON_CODES for reason_code in reason_codes):
        return STATUS_WATCH
    return STATUS_PASS


def _report_status(rows: tuple[ResearchStrategyEvidenceGapClosurePlanStep, ...]) -> str:
    if not rows or any(row.status == STATUS_BLOCK for row in rows):
        return STATUS_BLOCK
    if any(row.status == STATUS_WATCH for row in rows):
        return STATUS_WATCH
    return STATUS_PASS


def _status_count(
    rows: tuple[ResearchStrategyEvidenceGapClosurePlanStep, ...],
    status: str,
) -> int:
    return sum(1 for row in rows if row.status == status)


def _closure_step(status: str) -> str:
    if status == STATUS_BLOCK:
        return BLOCK_CLOSURE_STEP
    if status == STATUS_WATCH:
        return WATCH_CLOSURE_STEP
    if status == STATUS_PASS:
        return PASS_CLOSURE_STEP
    raise ValueError("status must be pass, watch, or block")


def _step_sort_key(
    row: ResearchStrategyEvidenceGapClosurePlanStep,
) -> tuple[int, Decimal, str]:
    return (_status_rank(row.status), row.closure_readiness_score, row.evidence_gap_digest)


def _status_rank(status: str) -> int:
    if status == STATUS_BLOCK:
        return 0
    if status == STATUS_WATCH:
        return 1
    if status == STATUS_PASS:
        return 2
    raise ValueError("status must be pass, watch, or block")


def _reason_code_counts(
    rows: tuple[ResearchStrategyEvidenceGapClosurePlanStep, ...],
) -> tuple[ResearchStrategyEvidenceGapClosurePlanReasonCodeCount, ...]:
    if not rows:
        return ()
    counts: Counter[str] = Counter()
    for row in rows:
        counts.update(row.reason_codes)
    row_count = _decimal_count(len(rows))
    reason_order = {reason: index for index, reason in enumerate(_REASON_CODE_SEQUENCE)}
    return tuple(
        ResearchStrategyEvidenceGapClosurePlanReasonCodeCount(
            reason_code=reason_code,
            count=count_decimal,
            row_ratio=_ratio(count_decimal, row_count),
        )
        for reason_code, count_decimal in sorted(
            (
                (reason_code, _decimal_count(count))
                for reason_code, count in counts.items()
            ),
            key=lambda item: (-item[1], reason_order[item[0]]),
        )
    )


def _closure_readiness_score(
    *,
    source_readiness_score: Decimal,
    contradiction_clarity_score: Decimal,
    update_freshness_score: Decimal,
    domain_coverage_score: Decimal,
    resolution_rule_linkage_score: Decimal,
    config: ResearchStrategyEvidenceGapClosurePlanConfig,
) -> Decimal:
    return _clamp_ratio(
        source_readiness_score * config.source_readiness_weight
        + contradiction_clarity_score * config.contradiction_clarity_weight
        + update_freshness_score * config.update_freshness_weight
        + domain_coverage_score * config.domain_coverage_weight
        + resolution_rule_linkage_score * config.resolution_rule_linkage_weight,
    )


def _validate_step(
    step: ResearchStrategyEvidenceGapClosurePlanStep,
    config: ResearchStrategyEvidenceGapClosurePlanConfig | None,
) -> None:
    if step.source_gap_score != _inverse_ratio(step.source_readiness_score):
        raise ValueError("source_gap_score must equal inverse source readiness")
    if step.contradiction_clarity_score != _inverse_ratio(
        step.contradiction_severity_score,
    ):
        raise ValueError(
            "contradiction_clarity_score must equal inverse contradiction severity",
        )
    if step.update_staleness_score != _inverse_ratio(step.update_freshness_score):
        raise ValueError("update_staleness_score must equal inverse update freshness")
    if step.domain_gap_score != _inverse_ratio(step.domain_coverage_score):
        raise ValueError("domain_gap_score must equal inverse domain coverage")
    if step.resolution_rule_gap_score != _inverse_ratio(
        step.resolution_rule_linkage_score,
    ):
        raise ValueError(
            "resolution_rule_gap_score must equal inverse resolution-rule linkage",
        )
    if step.closure_step != _closure_step(step.status):
        raise ValueError("closure_step must match status")
    if step.status != _step_status(step.reason_codes):
        raise ValueError("status must match reason codes")
    if config is not None:
        expected = _closure_readiness_score(
            source_readiness_score=step.source_readiness_score,
            contradiction_clarity_score=step.contradiction_clarity_score,
            update_freshness_score=step.update_freshness_score,
            domain_coverage_score=step.domain_coverage_score,
            resolution_rule_linkage_score=step.resolution_rule_linkage_score,
            config=config,
        )
        if step.closure_readiness_score != expected:
            raise ValueError("closure_readiness_score mismatch")


def _validate_report(report: ResearchStrategyEvidenceGapClosurePlanReport) -> None:
    if report.rows != tuple(sorted(report.rows, key=_step_sort_key)):
        raise ValueError("rows must be sorted")
    seen_digests: set[str] = set()
    for row in report.rows:
        if row.evidence_gap_digest in seen_digests:
            raise ValueError("duplicate evidence gap digest")
        seen_digests.add(row.evidence_gap_digest)
    if report.row_count != _decimal_count(len(report.rows)):
        raise ValueError("row_count mismatch")
    if report.pass_count != _decimal_count(_status_count(report.rows, STATUS_PASS)):
        raise ValueError("pass_count mismatch")
    if report.watch_count != _decimal_count(_status_count(report.rows, STATUS_WATCH)):
        raise ValueError("watch_count mismatch")
    if report.block_count != _decimal_count(_status_count(report.rows, STATUS_BLOCK)):
        raise ValueError("block_count mismatch")
    if report.status != _report_status(report.rows):
        raise ValueError("status mismatch")
    if report.average_closure_readiness_score != _average_ratio(
        tuple(row.closure_readiness_score for row in report.rows),
    ):
        raise ValueError("average_closure_readiness_score mismatch")
    if report.min_source_readiness_score != min(
        (row.source_readiness_score for row in report.rows),
        default=_ZERO,
    ):
        raise ValueError("min_source_readiness_score mismatch")
    if report.max_contradiction_severity_score != max(
        (row.contradiction_severity_score for row in report.rows),
        default=_ZERO,
    ):
        raise ValueError("max_contradiction_severity_score mismatch")
    if report.min_update_freshness_score != min(
        (row.update_freshness_score for row in report.rows),
        default=_ZERO,
    ):
        raise ValueError("min_update_freshness_score mismatch")
    if report.min_domain_coverage_score != min(
        (row.domain_coverage_score for row in report.rows),
        default=_ZERO,
    ):
        raise ValueError("min_domain_coverage_score mismatch")
    if report.min_resolution_rule_linkage_score != min(
        (row.resolution_rule_linkage_score for row in report.rows),
        default=_ZERO,
    ):
        raise ValueError("min_resolution_rule_linkage_score mismatch")
    expected_counts = _reason_code_counts(report.rows)
    if not report.rows:
        expected_counts = (
            ResearchStrategyEvidenceGapClosurePlanReasonCodeCount(
                reason_code=REASON_EMPTY_INPUT,
                count=_ONE,
                row_ratio=_ONE,
            ),
        )
    if report.reason_code_counts != expected_counts:
        raise ValueError("reason_code_counts mismatch")
    if report.reason_codes != tuple(row.reason_code for row in expected_counts):
        raise ValueError("reason_codes mismatch")


def _normalize_inputs(
    inputs: Sequence[ResearchStrategyEvidenceGapClosurePlanInput],
) -> tuple[ResearchStrategyEvidenceGapClosurePlanInput, ...]:
    if isinstance(inputs, (str, bytes)) or not isinstance(inputs, Sequence):
        raise ValueError("inputs must be a sequence")
    normalized: list[ResearchStrategyEvidenceGapClosurePlanInput] = []
    for item in inputs:
        if type(item) is not ResearchStrategyEvidenceGapClosurePlanInput:
            raise ValueError("inputs must contain ResearchStrategyEvidenceGapClosurePlanInput")
        normalized.append(item)
    return tuple(normalized)


def _normalize_steps(
    rows: tuple[ResearchStrategyEvidenceGapClosurePlanStep, ...],
) -> tuple[ResearchStrategyEvidenceGapClosurePlanStep, ...]:
    if type(rows) is not tuple:
        raise ValueError("rows must be a tuple")
    for row in rows:
        if type(row) is not ResearchStrategyEvidenceGapClosurePlanStep:
            raise ValueError("rows must contain ResearchStrategyEvidenceGapClosurePlanStep")
    return rows


def _normalize_reason_code_counts(
    counts: tuple[ResearchStrategyEvidenceGapClosurePlanReasonCodeCount, ...],
) -> tuple[ResearchStrategyEvidenceGapClosurePlanReasonCodeCount, ...]:
    if type(counts) is not tuple:
        raise ValueError("reason_code_counts must be a tuple")
    for item in counts:
        if type(item) is not ResearchStrategyEvidenceGapClosurePlanReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "ResearchStrategyEvidenceGapClosurePlanReasonCodeCount",
            )
    return counts


def _normalize_upstream_reason_codes(value: tuple[str, ...]) -> tuple[str, ...]:
    return _normalize_reason_codes(
        value,
        _UPSTREAM_REASON_CODE_SEQUENCE,
        "reason_codes",
    )


def _normalize_row_reason_codes(value: tuple[str, ...]) -> tuple[str, ...]:
    return _normalize_reason_codes(value, _ROW_REASON_CODE_SEQUENCE, "reason_codes")


def _normalize_report_reason_codes(value: tuple[str, ...]) -> tuple[str, ...]:
    return _normalize_reason_codes(value, _REASON_CODE_SEQUENCE, "reason_codes")


def _normalize_reason_codes(
    value: tuple[str, ...],
    allowed_values: tuple[str, ...],
    field_name: str,
) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ValueError(f"{field_name} must be a tuple")
    seen: set[str] = set()
    for reason_code in value:
        _require_reason_code(field_name, reason_code, allowed_values)
        if reason_code in seen:
            raise ValueError(f"{field_name} must not contain duplicates")
        seen.add(reason_code)
    order = {reason_code: index for index, reason_code in enumerate(allowed_values)}
    return tuple(sorted(value, key=lambda reason_code: order[reason_code]))


def _report_payload(report: ResearchStrategyEvidenceGapClosurePlanReport) -> dict[str, object]:
    payload = _report_payload_without_digest(
        generated_at=report.generated_at,
        config_version=report.config_version,
        status=report.status,
        row_count=report.row_count,
        pass_count=report.pass_count,
        watch_count=report.watch_count,
        block_count=report.block_count,
        average_closure_readiness_score=report.average_closure_readiness_score,
        min_source_readiness_score=report.min_source_readiness_score,
        max_contradiction_severity_score=report.max_contradiction_severity_score,
        min_update_freshness_score=report.min_update_freshness_score,
        min_domain_coverage_score=report.min_domain_coverage_score,
        min_resolution_rule_linkage_score=report.min_resolution_rule_linkage_score,
        rows=report.rows,
        reason_code_counts=report.reason_code_counts,
        reason_codes=report.reason_codes,
        paper_only=report.paper_only,
        report_only=report.report_only,
        readonly=report.readonly,
    )
    payload[_DIGEST_FIELD] = report.derived_validation_digest
    return payload


def _report_payload_without_digest(**values: object) -> dict[str, object]:
    payload = _json_ready(values)
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    return payload


def _report_digest(report: ResearchStrategyEvidenceGapClosurePlanReport) -> str:
    return _report_digest_from_values(
        {
            "generated_at": report.generated_at,
            "config_version": report.config_version,
            "status": report.status,
            "row_count": report.row_count,
            "pass_count": report.pass_count,
            "watch_count": report.watch_count,
            "block_count": report.block_count,
            "average_closure_readiness_score": (
                report.average_closure_readiness_score
            ),
            "min_source_readiness_score": report.min_source_readiness_score,
            "max_contradiction_severity_score": (
                report.max_contradiction_severity_score
            ),
            "min_update_freshness_score": report.min_update_freshness_score,
            "min_domain_coverage_score": report.min_domain_coverage_score,
            "min_resolution_rule_linkage_score": (
                report.min_resolution_rule_linkage_score
            ),
            "rows": report.rows,
            "reason_code_counts": report.reason_code_counts,
            "reason_codes": report.reason_codes,
            "paper_only": report.paper_only,
            "report_only": report.report_only,
            "readonly": report.readonly,
        },
    )


def _report_digest_from_values(values: Mapping[str, object]) -> str:
    payload = _json_ready(values)
    _reject_unsafe_public_payload(
        "derived_validation_digest payload",
        payload,
        allow_json_containers=True,
    )
    canonical = json.dumps(
        payload,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    )
    return sha256(canonical.encode("utf-8")).hexdigest()


def _validate_payload_digest(payload: dict[str, object]) -> None:
    digest = payload.get(_DIGEST_FIELD)
    _require_digest(_DIGEST_FIELD, digest)
    payload_without_digest = dict(payload)
    payload_without_digest.pop(_DIGEST_FIELD, None)
    canonical = json.dumps(
        payload_without_digest,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    )
    expected = sha256(canonical.encode("utf-8")).hexdigest()
    if digest != expected:
        raise ValueError("derived_validation_digest mismatch")


def _validate_payload_statuses(value: object) -> None:
    if isinstance(value, Mapping):
        for key, item in value.items():
            if key == "status" and item not in _STATUS_VALUES:
                raise ValueError("status must be pass, watch, or block")
            _validate_payload_statuses(item)
        return
    if isinstance(value, list):
        for item in value:
            _validate_payload_statuses(item)


def _copy_json_object(value: dict[str, object]) -> dict[str, object]:
    copied = _copy_json_value(value)
    if type(copied) is not dict:
        raise ValueError("payload must be a JSON object")
    return copied


def _copy_json_value(value: object) -> object:
    if value is None or type(value) is bool or type(value) is str:
        return value
    if type(value) is int or isinstance(value, float):
        raise ValueError("payload numeric values must be Decimal strings")
    if isinstance(value, Mapping):
        copied: dict[str, object] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("payload keys must be strings")
            copied[key] = _copy_json_value(item)
        return copied
    if isinstance(value, list):
        return [_copy_json_value(item) for item in value]
    raise ValueError("payload contains unsupported JSON value")


def _json_ready(value: Any) -> Any:
    if value is None:
        return None
    if is_dataclass(value) and not isinstance(value, type):
        ready: dict[str, Any] = {}
        for field in fields(value):
            ready[field.name] = _json_ready(getattr(value, field.name))
        return ready
    if type(value) is Decimal:
        if not value.is_finite():
            raise ValueError("Decimal payload value must be finite")
        return str(value)
    if type(value) is datetime:
        return _as_utc("datetime payload value", value).isoformat()
    if type(value) is bool or type(value) is str:
        return value
    if type(value) is int or isinstance(value, float):
        raise ValueError("numeric payload values must be Decimal strings")
    if isinstance(value, Mapping):
        ready: dict[str, Any] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            ready[key] = _json_ready(item)
        return ready
    if isinstance(value, (list, tuple)):
        return [_json_ready(item) for item in value]
    raise ValueError("payload value is not JSON serializable")


def _reject_unsafe_public_payload(
    label: str,
    value: object,
    path: str = "",
    *,
    allow_json_containers: bool = False,
) -> None:
    current_path = path or label
    if is_dataclass(value) and not isinstance(value, type):
        for field in fields(value):
            _reject_unsafe_public_key(field.name, current_path)
            _reject_unsafe_public_payload(
                label,
                getattr(value, field.name),
                field.name if not path else f"{path}.{field.name}",
                allow_json_containers=allow_json_containers,
            )
        return
    if isinstance(value, Mapping):
        if not allow_json_containers:
            raise ValueError(f"{current_path} must remain constructor-normalized")
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            _reject_unsafe_public_key(key, current_path)
            _reject_unsafe_public_payload(
                label,
                item,
                key if not path else f"{path}.{key}",
                allow_json_containers=True,
            )
        return
    if isinstance(value, (list, tuple)):
        if type(value) is list and not allow_json_containers:
            raise ValueError(f"{current_path} must remain constructor-normalized")
        for index, item in enumerate(value):
            _reject_unsafe_public_payload(
                label,
                item,
                f"{current_path}[{index}]",
                allow_json_containers=allow_json_containers,
            )
        return
    if type(value) is str:
        _reject_unsafe_public_string(current_path, value)
        return
    if (
        value is None
        or type(value) is bool
        or type(value) is Decimal
        or type(value) is datetime
    ):
        return
    raise ValueError(f"{current_path} is not a supported public payload value")


def _reject_unsafe_public_key(key: str, path: str) -> None:
    lowered = key.lower()
    if any(fragment in lowered for fragment in _UNSAFE_PUBLIC_FRAGMENTS):
        raise ValueError(f"{path}.{key} has unsafe public field")


def _reject_unsafe_public_string(field_name: str, value: str) -> None:
    lowered = value.lower()
    if any(fragment in lowered for fragment in _UNSAFE_PUBLIC_FRAGMENTS):
        raise ValueError(f"{field_name} has unsafe public value")


def _require_exact_type(value: object, expected_type: type[object], label: str) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{label} must be exactly {expected_type.__name__}")


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in _PHASE_FLAG_FIELDS:
        if getattr(value, field_name) is not True:
            raise ValueError(f"{field_name} must be True for {label}")


def _require_private_ref(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if value.strip() != value or not value:
        raise ValueError(f"{field_name} must be non-empty private text")
    if len(value) > 2048:
        raise ValueError(f"{field_name} must not exceed 2048 characters")
    return value


def _private_ref_digest(value: str) -> str:
    return f"sha256:{sha256(value.encode('utf-8')).hexdigest()}"


def _require_private_digest(field_name: str, value: object) -> str:
    if type(value) is not str or not _PRIVATE_DIGEST_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a redacted sha256 digest")
    return value


def _require_public_identifier(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not _PUBLIC_IDENTIFIER_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a public identifier")
    _reject_unsafe_public_string(field_name, value)
    return value


def _require_closure_step(field_name: str, value: object) -> str:
    value = _require_public_identifier(field_name, value)
    if value not in _CLOSURE_STEPS:
        raise ValueError(f"{field_name} must be a supported closure step")
    return value


def _require_status(field_name: str, value: object) -> str:
    if type(value) is not str or value not in _STATUS_VALUES:
        raise ValueError(f"{field_name} must be pass, watch, or block")
    return value


def _require_reason_code(
    field_name: str,
    value: object,
    allowed_values: tuple[str, ...],
) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a reason code")
    _require_public_identifier(field_name, value)
    if value not in allowed_values:
        raise ValueError(f"{field_name} must be a supported reason code")
    return value


def _require_digest(field_name: str, value: object) -> str:
    if type(value) is not str or not _DIGEST_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a lowercase sha256 digest")
    return value


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return _quantize(value)


def _require_nonnegative_count_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < _ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _require_ratio_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < _ZERO or normalized > _ONE:
        raise ValueError(f"{field_name} must be between zero and one")
    return normalized


def _decimal_count(value: int) -> Decimal:
    if value < 0:
        raise ValueError("count must be nonnegative")
    return Decimal(value).quantize(_QUANT)


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == _ZERO:
        return _ZERO
    return _quantize(numerator / denominator)


def _average_ratio(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return _ZERO
    return _quantize(sum(values, _ZERO) / Decimal(len(values)))


def _inverse_ratio(value: Decimal) -> Decimal:
    return _clamp_ratio(_ONE - value)


def _clamp_ratio(value: Decimal) -> Decimal:
    normalized = _quantize(value)
    if normalized < _ZERO:
        return _ZERO
    if normalized > _ONE:
        return _ONE
    return normalized


def _quantize(value: Decimal) -> Decimal:
    return value.quantize(_QUANT, rounding=ROUND_HALF_UP)


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


__all__ = (
    "DEFAULT_RESEARCH_STRATEGY_EVIDENCE_GAP_CLOSURE_PLAN_REPORT_CONFIG_VERSION",
    "ResearchStrategyEvidenceGapClosurePlanConfig",
    "ResearchStrategyEvidenceGapClosurePlanInput",
    "ResearchStrategyEvidenceGapClosurePlanReasonCodeCount",
    "ResearchStrategyEvidenceGapClosurePlanReport",
    "ResearchStrategyEvidenceGapClosurePlanStep",
    "build_research_strategy_evidence_gap_closure_plan_report",
    "research_strategy_evidence_gap_closure_plan_report_payload",
)
