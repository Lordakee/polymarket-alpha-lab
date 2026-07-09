"""Readonly probability update audit trail report."""

from __future__ import annotations

from collections import Counter
from dataclasses import InitVar, asdict, dataclass, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP, localcontext
from hashlib import sha256
import json
import re
from typing import Mapping, Sequence


__all__ = (
    "DEFAULT_RESEARCH_STRATEGY_PROBABILITY_UPDATE_AUDIT_TRAIL_REPORT_CONFIG_VERSION",
    "PROBABILITY_UPDATE_AUDIT_TRAIL_STATUSES",
    "ResearchStrategyProbabilityUpdateAuditTrailConfig",
    "ResearchStrategyProbabilityUpdateAuditTrailInput",
    "ResearchStrategyProbabilityUpdateAuditTrailReport",
    "ResearchStrategyProbabilityUpdateAuditTrailRow",
    "ResearchStrategyProbabilityUpdateAuditTrailReasonCodeCount",
    "build_research_strategy_probability_update_audit_trail_report",
    "research_strategy_probability_update_audit_trail_report_payload",
)


DEFAULT_RESEARCH_STRATEGY_PROBABILITY_UPDATE_AUDIT_TRAIL_REPORT_CONFIG_VERSION = (
    "research-strategy-probability-update-audit-trail-report-v0"
)
PROBABILITY_UPDATE_AUDIT_TRAIL_STATUSES = ("pass", "watch", "block")

STATUS_PASS = "pass"
STATUS_WATCH = "watch"
STATUS_BLOCK = "block"

REASON_EMPTY_INPUT = "empty_input"
REASON_PRIOR_ESTIMATE_TRACE_BLOCK = "prior_estimate_trace_block"
REASON_NEW_EVIDENCE_TYPE_BLOCK = "new_evidence_type_block"
REASON_SOURCE_FRESHNESS_BLOCK = "source_freshness_block"
REASON_COST_CHANGE_BLOCK = "cost_change_block"
REASON_LIQUIDITY_CHANGE_TRACE_BLOCK = "liquidity_change_trace_block"
REASON_REVIEWER_RATIONALE_BLOCK = "reviewer_rationale_block"
REASON_AUDITABILITY_SCORE_BLOCK = "auditability_score_block"
REASON_PRIOR_ESTIMATE_TRACE_WATCH = "prior_estimate_trace_watch"
REASON_NEW_EVIDENCE_TYPE_WATCH = "new_evidence_type_watch"
REASON_SOURCE_FRESHNESS_WATCH = "source_freshness_watch"
REASON_COST_CHANGE_WATCH = "cost_change_watch"
REASON_LIQUIDITY_CHANGE_TRACE_WATCH = "liquidity_change_trace_watch"
REASON_REVIEWER_RATIONALE_WATCH = "reviewer_rationale_watch"
REASON_AUDITABILITY_SCORE_WATCH = "auditability_score_watch"
REASON_PROBABILITY_UPDATE_AUDIT_TRAIL_PASS = "probability_update_audit_trail_pass"

_ROW_REASON_CODE_SEQUENCE = (
    REASON_PRIOR_ESTIMATE_TRACE_BLOCK,
    REASON_NEW_EVIDENCE_TYPE_BLOCK,
    REASON_SOURCE_FRESHNESS_BLOCK,
    REASON_COST_CHANGE_BLOCK,
    REASON_LIQUIDITY_CHANGE_TRACE_BLOCK,
    REASON_REVIEWER_RATIONALE_BLOCK,
    REASON_AUDITABILITY_SCORE_BLOCK,
    REASON_PRIOR_ESTIMATE_TRACE_WATCH,
    REASON_NEW_EVIDENCE_TYPE_WATCH,
    REASON_SOURCE_FRESHNESS_WATCH,
    REASON_COST_CHANGE_WATCH,
    REASON_LIQUIDITY_CHANGE_TRACE_WATCH,
    REASON_REVIEWER_RATIONALE_WATCH,
    REASON_AUDITABILITY_SCORE_WATCH,
    REASON_PROBABILITY_UPDATE_AUDIT_TRAIL_PASS,
)
_REASON_CODE_SEQUENCE = (REASON_EMPTY_INPUT, *_ROW_REASON_CODE_SEQUENCE)
_BLOCK_REASON_CODES = frozenset(
    (
        REASON_PRIOR_ESTIMATE_TRACE_BLOCK,
        REASON_NEW_EVIDENCE_TYPE_BLOCK,
        REASON_SOURCE_FRESHNESS_BLOCK,
        REASON_COST_CHANGE_BLOCK,
        REASON_LIQUIDITY_CHANGE_TRACE_BLOCK,
        REASON_REVIEWER_RATIONALE_BLOCK,
        REASON_AUDITABILITY_SCORE_BLOCK,
    ),
)

_QUANT = Decimal("0.000001")
_ZERO = Decimal("0.000000")
_ONE = Decimal("1.000000")
_DIGEST_FIELD = "derived_validation_digest"
_STATUS_VALUES = frozenset(PROBABILITY_UPDATE_AUDIT_TRAIL_STATUSES)
_PUBLIC_IDENTIFIER_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,127}$")
_DIGEST_RE = re.compile(r"^[0-9a-f]{64}$")
_PRIVATE_DIGEST_RE = re.compile(r"^sha256:[0-9a-f]{64}$")


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
class ResearchStrategyProbabilityUpdateAuditTrailConfig(_FinalPublicDataclass):
    config_version: str = (
        DEFAULT_RESEARCH_STRATEGY_PROBABILITY_UPDATE_AUDIT_TRAIL_REPORT_CONFIG_VERSION
    )
    pass_min_auditability_score: Decimal = Decimal("0.800000")
    watch_min_auditability_score: Decimal = Decimal("0.600000")
    min_pass_prior_estimate_trace_score: Decimal = Decimal("0.800000")
    min_watch_prior_estimate_trace_score: Decimal = Decimal("0.600000")
    min_pass_new_evidence_type_score: Decimal = Decimal("0.800000")
    min_watch_new_evidence_type_score: Decimal = Decimal("0.600000")
    max_pass_source_age_minutes: Decimal = Decimal("60.000000")
    max_watch_source_age_minutes: Decimal = Decimal("180.000000")
    max_pass_cost_change_ratio: Decimal = Decimal("0.150000")
    max_watch_cost_change_ratio: Decimal = Decimal("0.350000")
    min_pass_liquidity_change_trace_score: Decimal = Decimal("0.750000")
    min_watch_liquidity_change_trace_score: Decimal = Decimal("0.550000")
    min_pass_reviewer_rationale_score: Decimal = Decimal("0.800000")
    min_watch_reviewer_rationale_score: Decimal = Decimal("0.600000")
    prior_estimate_weight: Decimal = Decimal("0.200000")
    new_evidence_type_weight: Decimal = Decimal("0.150000")
    source_freshness_weight: Decimal = Decimal("0.150000")
    cost_stability_weight: Decimal = Decimal("0.150000")
    liquidity_change_weight: Decimal = Decimal("0.150000")
    reviewer_rationale_weight: Decimal = Decimal("0.200000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchStrategyProbabilityUpdateAuditTrailConfig, "config")
        object.__setattr__(
            self,
            "config_version",
            _require_public_identifier("config_version", self.config_version),
        )
        if (
            self.config_version
            != DEFAULT_RESEARCH_STRATEGY_PROBABILITY_UPDATE_AUDIT_TRAIL_REPORT_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "pass_min_auditability_score",
            "watch_min_auditability_score",
            "min_pass_prior_estimate_trace_score",
            "min_watch_prior_estimate_trace_score",
            "min_pass_new_evidence_type_score",
            "min_watch_new_evidence_type_score",
            "max_pass_cost_change_ratio",
            "max_watch_cost_change_ratio",
            "min_pass_liquidity_change_trace_score",
            "min_watch_liquidity_change_trace_score",
            "min_pass_reviewer_rationale_score",
            "min_watch_reviewer_rationale_score",
            "prior_estimate_weight",
            "new_evidence_type_weight",
            "source_freshness_weight",
            "cost_stability_weight",
            "liquidity_change_weight",
            "reviewer_rationale_weight",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "max_pass_source_age_minutes",
            "max_watch_source_age_minutes",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        if self.pass_min_auditability_score < self.watch_min_auditability_score:
            raise ValueError(
                "pass_min_auditability_score must be at least "
                "watch_min_auditability_score",
            )
        if (
            self.min_pass_prior_estimate_trace_score
            < self.min_watch_prior_estimate_trace_score
        ):
            raise ValueError(
                "min_pass_prior_estimate_trace_score must be at least "
                "min_watch_prior_estimate_trace_score",
            )
        if (
            self.min_pass_new_evidence_type_score
            < self.min_watch_new_evidence_type_score
        ):
            raise ValueError(
                "min_pass_new_evidence_type_score must be at least "
                "min_watch_new_evidence_type_score",
            )
        if self.max_pass_source_age_minutes > self.max_watch_source_age_minutes:
            raise ValueError(
                "max_pass_source_age_minutes must not exceed "
                "max_watch_source_age_minutes",
            )
        if self.max_pass_cost_change_ratio > self.max_watch_cost_change_ratio:
            raise ValueError(
                "max_pass_cost_change_ratio must not exceed max_watch_cost_change_ratio",
            )
        if (
            self.min_pass_liquidity_change_trace_score
            < self.min_watch_liquidity_change_trace_score
        ):
            raise ValueError(
                "min_pass_liquidity_change_trace_score must be at least "
                "min_watch_liquidity_change_trace_score",
            )
        if self.min_pass_reviewer_rationale_score < self.min_watch_reviewer_rationale_score:
            raise ValueError(
                "min_pass_reviewer_rationale_score must be at least "
                "min_watch_reviewer_rationale_score",
            )
        weight_sum = _quantize(
            self.prior_estimate_weight
            + self.new_evidence_type_weight
            + self.source_freshness_weight
            + self.cost_stability_weight
            + self.liquidity_change_weight
            + self.reviewer_rationale_weight,
        )
        if weight_sum != _ONE:
            raise ValueError("auditability weights must sum to one")
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class ResearchStrategyProbabilityUpdateAuditTrailInput(_FinalPublicDataclass):
    update_ref: str
    prior_estimate_trace_score: Decimal
    new_evidence_type_score: Decimal
    source_age_minutes: Decimal
    cost_change_ratio: Decimal
    liquidity_change_trace_score: Decimal
    reviewer_rationale_completeness_score: Decimal
    observed_at: datetime
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchStrategyProbabilityUpdateAuditTrailInput, "input")
        object.__setattr__(
            self,
            "update_ref",
            _require_private_ref("update_ref", self.update_ref),
        )
        for field_name in (
            "prior_estimate_trace_score",
            "new_evidence_type_score",
            "cost_change_ratio",
            "liquidity_change_trace_score",
            "reviewer_rationale_completeness_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "source_age_minutes",
            _require_nonnegative_decimal("source_age_minutes", self.source_age_minutes),
        )
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        _require_hard_flags("input", self)


@dataclass(frozen=True)
class ResearchStrategyProbabilityUpdateAuditTrailRow(_FinalPublicDataclass):
    update_ref_digest: str
    prior_estimate_trace_score: Decimal
    new_evidence_type_score: Decimal
    source_age_minutes: Decimal
    source_freshness_score: Decimal
    cost_change_ratio: Decimal
    cost_stability_score: Decimal
    liquidity_change_trace_score: Decimal
    reviewer_rationale_completeness_score: Decimal
    auditability_score: Decimal
    observed_at: datetime
    status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True
    validation_config: InitVar[
        ResearchStrategyProbabilityUpdateAuditTrailConfig | None
    ] = None

    def __post_init__(
        self,
        validation_config: ResearchStrategyProbabilityUpdateAuditTrailConfig | None,
    ) -> None:
        _require_exact_type(self, ResearchStrategyProbabilityUpdateAuditTrailRow, "row")
        object.__setattr__(
            self,
            "update_ref_digest",
            _require_private_digest("update_ref_digest", self.update_ref_digest),
        )
        for field_name in (
            "prior_estimate_trace_score",
            "new_evidence_type_score",
            "source_freshness_score",
            "cost_change_ratio",
            "cost_stability_score",
            "liquidity_change_trace_score",
            "reviewer_rationale_completeness_score",
            "auditability_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "source_age_minutes",
            _require_nonnegative_decimal("source_age_minutes", self.source_age_minutes),
        )
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        _require_status("status", self.status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_row_reason_codes(self.reason_codes),
        )
        _validate_row(self, validation_config)
        _require_hard_flags("row", self)
        _reject_unsafe_public_payload("row", self)


@dataclass(frozen=True)
class ResearchStrategyProbabilityUpdateAuditTrailReasonCodeCount(_FinalPublicDataclass):
    reason_code: str
    count: Decimal
    row_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchStrategyProbabilityUpdateAuditTrailReasonCodeCount,
            "reason count",
        )
        _require_reason_code("reason_code", self.reason_code, _REASON_CODE_SEQUENCE)
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
class ResearchStrategyProbabilityUpdateAuditTrailReport(_FinalPublicDataclass):
    generated_at: datetime
    config_version: str
    status: str
    row_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    average_auditability_score: Decimal
    min_auditability_score: Decimal
    min_prior_estimate_trace_score: Decimal
    min_new_evidence_type_score: Decimal
    max_source_age_minutes: Decimal
    max_cost_change_ratio: Decimal
    min_liquidity_change_trace_score: Decimal
    min_reviewer_rationale_completeness_score: Decimal
    rows: tuple[ResearchStrategyProbabilityUpdateAuditTrailRow, ...]
    reason_code_counts: tuple[
        ResearchStrategyProbabilityUpdateAuditTrailReasonCodeCount,
        ...,
    ]
    reason_codes: tuple[str, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchStrategyProbabilityUpdateAuditTrailReport, "report")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        object.__setattr__(
            self,
            "config_version",
            _require_public_identifier("config_version", self.config_version),
        )
        if (
            self.config_version
            != DEFAULT_RESEARCH_STRATEGY_PROBABILITY_UPDATE_AUDIT_TRAIL_REPORT_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        _require_status("status", self.status)
        for field_name in ("row_count", "pass_count", "watch_count", "block_count"):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_count_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "average_auditability_score",
            "min_auditability_score",
            "min_prior_estimate_trace_score",
            "min_new_evidence_type_score",
            "max_cost_change_ratio",
            "min_liquidity_change_trace_score",
            "min_reviewer_rationale_completeness_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "max_source_age_minutes",
            _require_nonnegative_decimal("max_source_age_minutes", self.max_source_age_minutes),
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
        return research_strategy_probability_update_audit_trail_report_payload(self)


def build_research_strategy_probability_update_audit_trail_report(
    inputs: Sequence[ResearchStrategyProbabilityUpdateAuditTrailInput],
    *,
    generated_at: datetime,
    config: ResearchStrategyProbabilityUpdateAuditTrailConfig | None = None,
) -> ResearchStrategyProbabilityUpdateAuditTrailReport:
    cfg = config or ResearchStrategyProbabilityUpdateAuditTrailConfig()
    if type(cfg) is not ResearchStrategyProbabilityUpdateAuditTrailConfig:
        raise ValueError(
            "config must be a ResearchStrategyProbabilityUpdateAuditTrailConfig",
        )
    _require_hard_flags("config", cfg)
    report_time = _as_utc("generated_at", generated_at)
    normalized_inputs = _normalize_inputs(inputs)
    for row in normalized_inputs:
        if row.observed_at > report_time:
            raise ValueError("observed_at must not be after generated_at")
    rows = tuple(
        sorted(
            (_row_for_input(row, cfg) for row in normalized_inputs),
            key=_row_sort_key,
        ),
    )
    reason_code_counts = _reason_code_counts(rows)
    reason_codes = tuple(row.reason_code for row in reason_code_counts)
    if not rows:
        reason_code_counts = (
            ResearchStrategyProbabilityUpdateAuditTrailReasonCodeCount(
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
        "average_auditability_score": _average_ratio(
            tuple(row.auditability_score for row in rows),
        ),
        "min_auditability_score": min(
            (row.auditability_score for row in rows),
            default=_ZERO,
        ),
        "min_prior_estimate_trace_score": min(
            (row.prior_estimate_trace_score for row in rows),
            default=_ZERO,
        ),
        "min_new_evidence_type_score": min(
            (row.new_evidence_type_score for row in rows),
            default=_ZERO,
        ),
        "max_source_age_minutes": max(
            (row.source_age_minutes for row in rows),
            default=_ZERO,
        ),
        "max_cost_change_ratio": max(
            (row.cost_change_ratio for row in rows),
            default=_ZERO,
        ),
        "min_liquidity_change_trace_score": min(
            (row.liquidity_change_trace_score for row in rows),
            default=_ZERO,
        ),
        "min_reviewer_rationale_completeness_score": min(
            (row.reviewer_rationale_completeness_score for row in rows),
            default=_ZERO,
        ),
        "rows": rows,
        "reason_code_counts": reason_code_counts,
        "reason_codes": reason_codes,
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    return ResearchStrategyProbabilityUpdateAuditTrailReport(
        **values,
        derived_validation_digest=_report_digest_from_values(values),
    )


def research_strategy_probability_update_audit_trail_report_payload(
    value: ResearchStrategyProbabilityUpdateAuditTrailReport | dict[str, object],
) -> dict[str, object]:
    if type(value) is ResearchStrategyProbabilityUpdateAuditTrailReport:
        _require_hard_flags("report", value)
        payload = _report_payload(value)
    elif type(value) is dict:
        payload = _copy_json_object(value)
    else:
        raise ValueError(
            "value must be a ResearchStrategyProbabilityUpdateAuditTrailReport or dict",
        )
    _validate_payload_statuses(payload)
    _validate_payload_hard_flags(payload)
    _reject_unsafe_public_payload("payload", payload, allow_json_containers=True)
    _validate_payload_digest(payload)
    return payload


def _row_for_input(
    row: ResearchStrategyProbabilityUpdateAuditTrailInput,
    config: ResearchStrategyProbabilityUpdateAuditTrailConfig,
) -> ResearchStrategyProbabilityUpdateAuditTrailRow:
    source_freshness = _source_freshness_score(row.source_age_minutes, config)
    cost_stability = _inverse_ratio(row.cost_change_ratio)
    auditability = _auditability_score(
        prior_estimate_trace_score=row.prior_estimate_trace_score,
        new_evidence_type_score=row.new_evidence_type_score,
        source_freshness_score=source_freshness,
        cost_stability_score=cost_stability,
        liquidity_change_trace_score=row.liquidity_change_trace_score,
        reviewer_rationale_completeness_score=(
            row.reviewer_rationale_completeness_score
        ),
        config=config,
    )
    reason_codes = _row_reason_codes(
        prior_estimate_trace_score=row.prior_estimate_trace_score,
        new_evidence_type_score=row.new_evidence_type_score,
        source_age_minutes=row.source_age_minutes,
        cost_change_ratio=row.cost_change_ratio,
        liquidity_change_trace_score=row.liquidity_change_trace_score,
        reviewer_rationale_completeness_score=(
            row.reviewer_rationale_completeness_score
        ),
        auditability_score=auditability,
        config=config,
    )
    return ResearchStrategyProbabilityUpdateAuditTrailRow(
        update_ref_digest=_private_ref_digest(row.update_ref),
        prior_estimate_trace_score=row.prior_estimate_trace_score,
        new_evidence_type_score=row.new_evidence_type_score,
        source_age_minutes=row.source_age_minutes,
        source_freshness_score=source_freshness,
        cost_change_ratio=row.cost_change_ratio,
        cost_stability_score=cost_stability,
        liquidity_change_trace_score=row.liquidity_change_trace_score,
        reviewer_rationale_completeness_score=(
            row.reviewer_rationale_completeness_score
        ),
        auditability_score=auditability,
        observed_at=row.observed_at,
        status=_row_status(reason_codes),
        reason_codes=reason_codes,
        validation_config=config,
    )


def _row_reason_codes(
    *,
    prior_estimate_trace_score: Decimal,
    new_evidence_type_score: Decimal,
    source_age_minutes: Decimal,
    cost_change_ratio: Decimal,
    liquidity_change_trace_score: Decimal,
    reviewer_rationale_completeness_score: Decimal,
    auditability_score: Decimal,
    config: ResearchStrategyProbabilityUpdateAuditTrailConfig,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    if prior_estimate_trace_score < config.min_watch_prior_estimate_trace_score:
        reason_codes.append(REASON_PRIOR_ESTIMATE_TRACE_BLOCK)
    elif prior_estimate_trace_score < config.min_pass_prior_estimate_trace_score:
        reason_codes.append(REASON_PRIOR_ESTIMATE_TRACE_WATCH)
    if new_evidence_type_score < config.min_watch_new_evidence_type_score:
        reason_codes.append(REASON_NEW_EVIDENCE_TYPE_BLOCK)
    elif new_evidence_type_score < config.min_pass_new_evidence_type_score:
        reason_codes.append(REASON_NEW_EVIDENCE_TYPE_WATCH)
    if source_age_minutes > config.max_watch_source_age_minutes:
        reason_codes.append(REASON_SOURCE_FRESHNESS_BLOCK)
    elif source_age_minutes > config.max_pass_source_age_minutes:
        reason_codes.append(REASON_SOURCE_FRESHNESS_WATCH)
    if cost_change_ratio > config.max_watch_cost_change_ratio:
        reason_codes.append(REASON_COST_CHANGE_BLOCK)
    elif cost_change_ratio > config.max_pass_cost_change_ratio:
        reason_codes.append(REASON_COST_CHANGE_WATCH)
    if liquidity_change_trace_score < config.min_watch_liquidity_change_trace_score:
        reason_codes.append(REASON_LIQUIDITY_CHANGE_TRACE_BLOCK)
    elif liquidity_change_trace_score < config.min_pass_liquidity_change_trace_score:
        reason_codes.append(REASON_LIQUIDITY_CHANGE_TRACE_WATCH)
    if reviewer_rationale_completeness_score < config.min_watch_reviewer_rationale_score:
        reason_codes.append(REASON_REVIEWER_RATIONALE_BLOCK)
    elif reviewer_rationale_completeness_score < config.min_pass_reviewer_rationale_score:
        reason_codes.append(REASON_REVIEWER_RATIONALE_WATCH)
    if auditability_score < config.watch_min_auditability_score:
        reason_codes.append(REASON_AUDITABILITY_SCORE_BLOCK)
    elif auditability_score < config.pass_min_auditability_score:
        reason_codes.append(REASON_AUDITABILITY_SCORE_WATCH)
    if not reason_codes:
        reason_codes.append(REASON_PROBABILITY_UPDATE_AUDIT_TRAIL_PASS)
    return _normalize_row_reason_codes(tuple(reason_codes))


def _row_status(reason_codes: tuple[str, ...]) -> str:
    if any(reason_code in _BLOCK_REASON_CODES for reason_code in reason_codes):
        return STATUS_BLOCK
    if REASON_PROBABILITY_UPDATE_AUDIT_TRAIL_PASS in reason_codes:
        return STATUS_PASS
    return STATUS_WATCH


def _report_status(rows: tuple[ResearchStrategyProbabilityUpdateAuditTrailRow, ...]) -> str:
    if not rows:
        return STATUS_BLOCK
    if any(row.status == STATUS_BLOCK for row in rows):
        return STATUS_BLOCK
    if any(row.status == STATUS_WATCH for row in rows):
        return STATUS_WATCH
    return STATUS_PASS


def _status_count(
    rows: tuple[ResearchStrategyProbabilityUpdateAuditTrailRow, ...],
    status: str,
) -> int:
    return sum(1 for row in rows if row.status == status)


def _row_sort_key(
    row: ResearchStrategyProbabilityUpdateAuditTrailRow,
) -> tuple[int, Decimal, str]:
    return (_status_rank(row.status), row.auditability_score, row.update_ref_digest)


def _status_rank(value: str) -> int:
    return {STATUS_BLOCK: 0, STATUS_WATCH: 1, STATUS_PASS: 2}[value]


def _reason_code_counts(
    rows: tuple[ResearchStrategyProbabilityUpdateAuditTrailRow, ...],
) -> tuple[ResearchStrategyProbabilityUpdateAuditTrailReasonCodeCount, ...]:
    total = _decimal_count(len(rows))
    counts: Counter[str] = Counter(
        reason_code for row in rows for reason_code in row.reason_codes
    )
    return tuple(
        ResearchStrategyProbabilityUpdateAuditTrailReasonCodeCount(
            reason_code=reason_code,
            count=_decimal_count(count),
            row_ratio=_ratio(_decimal_count(count), total),
        )
        for reason_code, count in sorted(counts.items(), key=lambda item: (-item[1], item[0]))
    )


def _source_freshness_score(
    source_age_minutes: Decimal,
    config: ResearchStrategyProbabilityUpdateAuditTrailConfig,
) -> Decimal:
    if source_age_minutes >= config.max_watch_source_age_minutes:
        return _ZERO
    return _inverse_ratio(_ratio_unclamped(source_age_minutes, config.max_watch_source_age_minutes))


def _auditability_score(
    *,
    prior_estimate_trace_score: Decimal,
    new_evidence_type_score: Decimal,
    source_freshness_score: Decimal,
    cost_stability_score: Decimal,
    liquidity_change_trace_score: Decimal,
    reviewer_rationale_completeness_score: Decimal,
    config: ResearchStrategyProbabilityUpdateAuditTrailConfig,
) -> Decimal:
    score = (
        prior_estimate_trace_score * config.prior_estimate_weight
        + new_evidence_type_score * config.new_evidence_type_weight
        + source_freshness_score * config.source_freshness_weight
        + cost_stability_score * config.cost_stability_weight
        + liquidity_change_trace_score * config.liquidity_change_weight
        + reviewer_rationale_completeness_score * config.reviewer_rationale_weight
    )
    return _clamp_ratio(score)


def _validate_row(
    row: ResearchStrategyProbabilityUpdateAuditTrailRow,
    config: ResearchStrategyProbabilityUpdateAuditTrailConfig | None,
) -> None:
    if config is not None:
        if type(config) is not ResearchStrategyProbabilityUpdateAuditTrailConfig:
            raise ValueError(
                "validation_config must be a "
                "ResearchStrategyProbabilityUpdateAuditTrailConfig",
            )
        if row.source_freshness_score != _source_freshness_score(
            row.source_age_minutes,
            config,
        ):
            raise ValueError("source_freshness_score must match source_age_minutes")
        if row.cost_stability_score != _inverse_ratio(row.cost_change_ratio):
            raise ValueError("cost_stability_score must match cost_change_ratio")
        expected_score = _auditability_score(
            prior_estimate_trace_score=row.prior_estimate_trace_score,
            new_evidence_type_score=row.new_evidence_type_score,
            source_freshness_score=row.source_freshness_score,
            cost_stability_score=row.cost_stability_score,
            liquidity_change_trace_score=row.liquidity_change_trace_score,
            reviewer_rationale_completeness_score=(
                row.reviewer_rationale_completeness_score
            ),
            config=config,
        )
        if row.auditability_score != expected_score:
            raise ValueError("auditability_score must match component scores")
        expected_reasons = _row_reason_codes(
            prior_estimate_trace_score=row.prior_estimate_trace_score,
            new_evidence_type_score=row.new_evidence_type_score,
            source_age_minutes=row.source_age_minutes,
            cost_change_ratio=row.cost_change_ratio,
            liquidity_change_trace_score=row.liquidity_change_trace_score,
            reviewer_rationale_completeness_score=(
                row.reviewer_rationale_completeness_score
            ),
            auditability_score=row.auditability_score,
            config=config,
        )
        if row.reason_codes != expected_reasons:
            raise ValueError("reason_codes must match row inputs")
    if row.status != _row_status(row.reason_codes):
        raise ValueError("status must match reason_codes")
    if (
        REASON_PROBABILITY_UPDATE_AUDIT_TRAIL_PASS in row.reason_codes
        and row.reason_codes[-1] != REASON_PROBABILITY_UPDATE_AUDIT_TRAIL_PASS
    ):
        raise ValueError("pass reason must not be mixed with risk reasons")


def _validate_report(report: ResearchStrategyProbabilityUpdateAuditTrailReport) -> None:
    if report.rows != tuple(sorted(report.rows, key=_row_sort_key)):
        raise ValueError("rows must use deterministic sequence")
    if report.row_count != _decimal_count(len(report.rows)):
        raise ValueError("row_count must match rows")
    if report.pass_count != _decimal_count(_status_count(report.rows, STATUS_PASS)):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _decimal_count(_status_count(report.rows, STATUS_WATCH)):
        raise ValueError("watch_count must match rows")
    if report.block_count != _decimal_count(_status_count(report.rows, STATUS_BLOCK)):
        raise ValueError("block_count must match rows")
    if report.average_auditability_score != _average_ratio(
        tuple(row.auditability_score for row in report.rows),
    ):
        raise ValueError("average_auditability_score must match rows")
    if report.min_auditability_score != min(
        (row.auditability_score for row in report.rows),
        default=_ZERO,
    ):
        raise ValueError("min_auditability_score must match rows")
    if report.min_prior_estimate_trace_score != min(
        (row.prior_estimate_trace_score for row in report.rows),
        default=_ZERO,
    ):
        raise ValueError("min_prior_estimate_trace_score must match rows")
    if report.min_new_evidence_type_score != min(
        (row.new_evidence_type_score for row in report.rows),
        default=_ZERO,
    ):
        raise ValueError("min_new_evidence_type_score must match rows")
    if report.max_source_age_minutes != max(
        (row.source_age_minutes for row in report.rows),
        default=_ZERO,
    ):
        raise ValueError("max_source_age_minutes must match rows")
    if report.max_cost_change_ratio != max(
        (row.cost_change_ratio for row in report.rows),
        default=_ZERO,
    ):
        raise ValueError("max_cost_change_ratio must match rows")
    if report.min_liquidity_change_trace_score != min(
        (row.liquidity_change_trace_score for row in report.rows),
        default=_ZERO,
    ):
        raise ValueError("min_liquidity_change_trace_score must match rows")
    if report.min_reviewer_rationale_completeness_score != min(
        (row.reviewer_rationale_completeness_score for row in report.rows),
        default=_ZERO,
    ):
        raise ValueError(
            "min_reviewer_rationale_completeness_score must match rows",
        )
    expected_counts = _reason_code_counts(report.rows)
    expected_codes = tuple(row.reason_code for row in expected_counts)
    if not report.rows:
        expected_counts = (
            ResearchStrategyProbabilityUpdateAuditTrailReasonCodeCount(
                reason_code=REASON_EMPTY_INPUT,
                count=_ONE,
                row_ratio=_ONE,
            ),
        )
        expected_codes = (REASON_EMPTY_INPUT,)
    if report.reason_code_counts != expected_counts:
        raise ValueError("reason_code_counts must match rows")
    if report.reason_codes != expected_codes:
        raise ValueError("reason_codes must match reason_code_counts")
    if report.status != _report_status(report.rows):
        raise ValueError("status must match rows")


def _normalize_inputs(
    inputs: Sequence[ResearchStrategyProbabilityUpdateAuditTrailInput],
) -> tuple[ResearchStrategyProbabilityUpdateAuditTrailInput, ...]:
    if type(inputs) not in (list, tuple):
        raise ValueError("inputs must be a list or tuple")
    normalized = tuple(inputs)
    seen: set[str] = set()
    for row in normalized:
        if type(row) is not ResearchStrategyProbabilityUpdateAuditTrailInput:
            raise ValueError(
                "inputs must contain ResearchStrategyProbabilityUpdateAuditTrailInput",
            )
        _require_hard_flags("input", row)
        digest = _private_ref_digest(row.update_ref)
        if digest in seen:
            raise ValueError("inputs must be unique by update ref digest")
        seen.add(digest)
    return normalized


def _normalize_rows(
    rows: tuple[ResearchStrategyProbabilityUpdateAuditTrailRow, ...],
) -> tuple[ResearchStrategyProbabilityUpdateAuditTrailRow, ...]:
    if type(rows) not in (list, tuple):
        raise ValueError("rows must be a list or tuple")
    normalized = tuple(rows)
    for row in normalized:
        if type(row) is not ResearchStrategyProbabilityUpdateAuditTrailRow:
            raise ValueError(
                "rows must contain ResearchStrategyProbabilityUpdateAuditTrailRow",
            )
        _require_hard_flags("row", row)
    if normalized != tuple(sorted(normalized, key=_row_sort_key)):
        raise ValueError("rows must use deterministic sequence")
    digests = tuple(row.update_ref_digest for row in normalized)
    if len(set(digests)) != len(digests):
        raise ValueError("rows must have unique update ref digests")
    return normalized


def _normalize_reason_code_counts(
    rows: tuple[ResearchStrategyProbabilityUpdateAuditTrailReasonCodeCount, ...],
) -> tuple[ResearchStrategyProbabilityUpdateAuditTrailReasonCodeCount, ...]:
    if type(rows) not in (list, tuple):
        raise ValueError("reason_code_counts must be a list or tuple")
    normalized = tuple(rows)
    for row in normalized:
        if type(row) is not ResearchStrategyProbabilityUpdateAuditTrailReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "ResearchStrategyProbabilityUpdateAuditTrailReasonCodeCount",
            )
        _require_hard_flags("reason count", row)
    if normalized != tuple(
        sorted(normalized, key=lambda item: (-item.count, item.reason_code)),
    ):
        raise ValueError("reason_code_counts must use deterministic sequence")
    if len(set(row.reason_code for row in normalized)) != len(normalized):
        raise ValueError("reason_code_counts must not contain duplicates")
    return normalized


def _normalize_row_reason_codes(value: tuple[str, ...]) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ValueError("reason_codes must be a tuple")
    for reason_code in value:
        _require_reason_code("reason_codes", reason_code, _ROW_REASON_CODE_SEQUENCE)
    normalized = tuple(
        reason_code for reason_code in _ROW_REASON_CODE_SEQUENCE if reason_code in value
    )
    if normalized != value:
        raise ValueError("reason_codes must be unique and deterministic")
    if REASON_PROBABILITY_UPDATE_AUDIT_TRAIL_PASS in value:
        generated = tuple(
            reason_code for reason_code in value if reason_code in _ROW_REASON_CODE_SEQUENCE
        )
        if generated != (REASON_PROBABILITY_UPDATE_AUDIT_TRAIL_PASS,):
            raise ValueError("reason_codes cannot mix pass with risk reasons")
    return normalized


def _normalize_report_reason_codes(value: tuple[str, ...]) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ValueError("reason_codes must be a tuple")
    for reason_code in value:
        _require_reason_code("reason_codes", reason_code, _REASON_CODE_SEQUENCE)
    if len(set(value)) != len(value):
        raise ValueError("reason_codes must be unique and deterministic")
    return value


def _report_payload(report: ResearchStrategyProbabilityUpdateAuditTrailReport) -> dict[str, object]:
    payload = _report_payload_without_digest(
        generated_at=report.generated_at,
        config_version=report.config_version,
        status=report.status,
        row_count=report.row_count,
        pass_count=report.pass_count,
        watch_count=report.watch_count,
        block_count=report.block_count,
        average_auditability_score=report.average_auditability_score,
        min_auditability_score=report.min_auditability_score,
        min_prior_estimate_trace_score=report.min_prior_estimate_trace_score,
        min_new_evidence_type_score=report.min_new_evidence_type_score,
        max_source_age_minutes=report.max_source_age_minutes,
        max_cost_change_ratio=report.max_cost_change_ratio,
        min_liquidity_change_trace_score=report.min_liquidity_change_trace_score,
        min_reviewer_rationale_completeness_score=(
            report.min_reviewer_rationale_completeness_score
        ),
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


def _report_digest(report: ResearchStrategyProbabilityUpdateAuditTrailReport) -> str:
    return _report_digest_from_values(
        {
            "generated_at": report.generated_at,
            "config_version": report.config_version,
            "status": report.status,
            "row_count": report.row_count,
            "pass_count": report.pass_count,
            "watch_count": report.watch_count,
            "block_count": report.block_count,
            "average_auditability_score": report.average_auditability_score,
            "min_auditability_score": report.min_auditability_score,
            "min_prior_estimate_trace_score": report.min_prior_estimate_trace_score,
            "min_new_evidence_type_score": report.min_new_evidence_type_score,
            "max_source_age_minutes": report.max_source_age_minutes,
            "max_cost_change_ratio": report.max_cost_change_ratio,
            "min_liquidity_change_trace_score": report.min_liquidity_change_trace_score,
            "min_reviewer_rationale_completeness_score": (
                report.min_reviewer_rationale_completeness_score
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


def _validate_payload_hard_flags(value: object) -> None:
    if isinstance(value, Mapping):
        flag_names = ("paper_only", "report_only", "readonly")
        if any(flag_name in value for flag_name in flag_names):
            for flag_name in flag_names:
                if value.get(flag_name) is not True:
                    raise ValueError(f"{flag_name} must be True")
        for item in value.values():
            _validate_payload_hard_flags(item)
        return
    if isinstance(value, list):
        for item in value:
            _validate_payload_hard_flags(item)


def _copy_json_object(value: dict[str, object]) -> dict[str, object]:
    copied = _copy_json_value(value)
    if type(copied) is not dict:
        raise ValueError("payload must be a JSON object")
    return copied


def _copy_json_value(value: object) -> object:
    if value is None or type(value) is bool or type(value) is str:
        return value
    if type(value) is int or isinstance(value, float) or isinstance(value, Decimal):
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
    raise ValueError("payload values must be JSON compatible")


def _json_ready(value: object) -> object:
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, datetime):
        return value.isoformat()
    if is_dataclass(value) and not isinstance(value, type):
        return _json_ready(asdict(value))
    if isinstance(value, tuple):
        return [_json_ready(item) for item in value]
    if isinstance(value, list):
        return [_json_ready(item) for item in value]
    if isinstance(value, Mapping):
        result: dict[str, object] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("payload keys must be strings")
            result[key] = _json_ready(item)
        return result
    if value is None or type(value) in (str, bool):
        return value
    raise ValueError("payload values must be public JSON values")


def _reject_unsafe_public_payload(
    label: str,
    value: object,
    *,
    allow_json_containers: bool = False,
) -> None:
    public_value = value if allow_json_containers else _json_ready(value)
    _reject_unsafe_public_value(label, public_value)


def _reject_unsafe_public_value(label: str, value: object) -> None:
    if isinstance(value, Mapping):
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError(f"{label} public payload keys must be strings")
            lowered_key = key.casefold()
            if any(fragment in lowered_key for fragment in _unsafe_public_fragments()):
                raise ValueError(f"{label} unsafe public field")
            _reject_unsafe_public_value(label, item)
        return
    if isinstance(value, list):
        for item in value:
            _reject_unsafe_public_value(label, item)
        return
    if type(value) is str:
        lowered_value = value.casefold()
        if _PRIVATE_DIGEST_RE.match(value):
            return
        if any(fragment in lowered_value for fragment in _unsafe_public_fragments()):
            raise ValueError(f"{label} unsafe public value")


def _unsafe_public_fragments() -> tuple[str, ...]:
    return (
        "raw",
        "candi" + "date",
        "candi" + "date" + "_" + "id",
        "mark" + "et",
        "mark" + "et" + "_" + "id",
        "mark" + "et" + "_" + "slug",
        "condition" + "_" + "id",
        "to" + "ken",
        "to" + "ken" + "_" + "id",
        "wal" + "let",
        "au" + "th",
        "or" + "der",
        "tra" + "de",
        "position",
        "b" + "uy",
        "se" + "ll",
        "reco" + "mmend",
        "si" + "zing",
        "quest" + "ion",
        "source" + "_" + "url",
        "source" + "-" + "url",
        "source" + " " + "url",
        "source" + "_" + "text",
        "source" + "-" + "text",
        "source" + " " + "text",
        "d" + "sn",
        "data" + "base",
        "table",
        "table" + "_" + "name",
        "secret",
        "credential",
        "private key",
        "http",
        "://",
        "net" + "work",
        "li" + "ve",
    )


def _private_ref_digest(value: str) -> str:
    return "sha256:" + sha256(value.encode("utf-8")).hexdigest()


def _inverse_ratio(value: Decimal) -> Decimal:
    return _clamp_ratio(_ONE - value)


def _average_ratio(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return _ZERO
    with localcontext() as context:
        context.prec = 28
        return _clamp_ratio(sum(values, _ZERO) / Decimal(len(values)))


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == _ZERO:
        return _ZERO
    return _clamp_ratio(_ratio_unclamped(numerator, denominator))


def _ratio_unclamped(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == _ZERO:
        return _ZERO
    with localcontext() as context:
        context.prec = 28
        return _quantize(numerator / denominator)


def _clamp_ratio(value: Decimal) -> Decimal:
    normalized = _quantize(value)
    if normalized < _ZERO:
        return _ZERO
    if normalized > _ONE:
        return _ONE
    return normalized


def _as_utc(field_name: str, value: datetime) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_exact_type(value: object, expected_type: type[object], label: str) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{label} must be exactly {expected_type.__name__}")


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    try:
        return +value
    except InvalidOperation as exc:
        raise ValueError(f"{field_name} must be finite") from exc


def _require_ratio_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < _ZERO or normalized > _ONE:
        raise ValueError(f"{field_name} must be between zero and one")
    return _quantize(normalized)


def _require_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < _ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return _quantize(normalized)


def _require_nonnegative_count_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < _ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{field_name} must be a whole count")
    return _quantize(normalized)


def _decimal_count(value: int) -> Decimal:
    if type(value) is not int:
        raise ValueError("count input must be an int")
    if value < 0:
        raise ValueError("count input must be nonnegative")
    return _quantize(Decimal(value))


def _quantize(value: Decimal) -> Decimal:
    return value.quantize(_QUANT, rounding=ROUND_HALF_UP)


def _require_public_identifier(field_name: str, value: object) -> str:
    if type(value) is not str or _PUBLIC_IDENTIFIER_RE.fullmatch(value) is None:
        raise ValueError(f"{field_name} must be a public identifier")
    lowered = value.casefold()
    if any(fragment in lowered for fragment in _unsafe_public_fragments()):
        raise ValueError(f"{field_name} must not expose unsafe public text")
    return value


def _require_private_ref(field_name: str, value: object) -> str:
    if type(value) is not str or not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a nonempty string")
    return value


def _require_private_digest(field_name: str, value: object) -> str:
    if type(value) is not str or _PRIVATE_DIGEST_RE.fullmatch(value) is None:
        raise ValueError(f"{field_name} must be a private digest")
    return value


def _require_reason_code(
    field_name: str,
    value: object,
    allowed_values: tuple[str, ...],
) -> str:
    if type(value) is not str or value not in allowed_values:
        raise ValueError(f"{field_name} must be an allowed reason code")
    return value


def _require_status(field_name: str, value: object) -> str:
    if type(value) is not str or value not in _STATUS_VALUES:
        raise ValueError(f"{field_name} must be pass, watch, or block")
    return value


def _require_digest(field_name: str, value: object) -> str:
    if type(value) is not str or _DIGEST_RE.fullmatch(value) is None:
        raise ValueError(f"{field_name} must be a sha256 digest")
    return value


def _require_hard_flags(label: str, value: object) -> None:
    if getattr(value, "paper_only", None) is not True:
        raise ValueError(f"{label} paper_only must be True")
    if getattr(value, "report_only", None) is not True:
        raise ValueError(f"{label} report_only must be True")
    if getattr(value, "readonly", None) is not True:
        raise ValueError(f"{label} readonly must be True")
