"""Pure report-only information-risk register for research candidates."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
import hashlib
import json
import re
from typing import Any


DEFAULT_RESEARCH_STRATEGY_INFORMATION_RISK_REGISTER_CONFIG_VERSION = (
    "research-strategy-information-risk-register-report-v0"
)

STATUS_PASS = "pass"
STATUS_WATCH = "watch"
STATUS_BLOCK = "block"
INFORMATION_RISK_STATUSES = (STATUS_PASS, STATUS_WATCH, STATUS_BLOCK)

EVIDENCE_FRESHNESS_BLOCK_REASON = "information_risk_evidence_freshness_block"
EVIDENCE_FRESHNESS_WATCH_REASON = "information_risk_evidence_freshness_watch"
SOURCE_RELIABILITY_BLOCK_REASON = "information_risk_source_reliability_block"
SOURCE_RELIABILITY_WATCH_REASON = "information_risk_source_reliability_watch"
CONTRADICTION_PRESSURE_BLOCK_REASON = (
    "information_risk_contradiction_pressure_block"
)
CONTRADICTION_PRESSURE_WATCH_REASON = (
    "information_risk_contradiction_pressure_watch"
)
AMBIGUITY_BLOCK_REASON = "information_risk_ambiguity_block"
AMBIGUITY_WATCH_REASON = "information_risk_ambiguity_watch"
TEAM_DISAGREEMENT_BLOCK_REASON = "information_risk_team_disagreement_block"
TEAM_DISAGREEMENT_WATCH_REASON = "information_risk_team_disagreement_watch"
COST_INPUT_QUALITY_BLOCK_REASON = "information_risk_cost_input_quality_block"
COST_INPUT_QUALITY_WATCH_REASON = "information_risk_cost_input_quality_watch"
THIN_AGGREGATE_EVIDENCE_REASON = "information_risk_thin_aggregate_evidence"
THIN_AGGREGATE_SOURCES_REASON = "information_risk_thin_aggregate_sources"
PASS_REASON = "information_risk_register_pass"
WATCH_PRESENT_REASON = "information_risk_register_watch_present"
CLEAR_REASON = "information_risk_register_clear"
EMPTY_REASON = "information_risk_register_empty"

ROW_REASON_CODE_SEQUENCE = (
    EVIDENCE_FRESHNESS_BLOCK_REASON,
    EVIDENCE_FRESHNESS_WATCH_REASON,
    SOURCE_RELIABILITY_BLOCK_REASON,
    SOURCE_RELIABILITY_WATCH_REASON,
    CONTRADICTION_PRESSURE_BLOCK_REASON,
    CONTRADICTION_PRESSURE_WATCH_REASON,
    AMBIGUITY_BLOCK_REASON,
    AMBIGUITY_WATCH_REASON,
    TEAM_DISAGREEMENT_BLOCK_REASON,
    TEAM_DISAGREEMENT_WATCH_REASON,
    COST_INPUT_QUALITY_BLOCK_REASON,
    COST_INPUT_QUALITY_WATCH_REASON,
    THIN_AGGREGATE_EVIDENCE_REASON,
    THIN_AGGREGATE_SOURCES_REASON,
    PASS_REASON,
)
REPORT_REASON_CODE_SEQUENCE = (
    EVIDENCE_FRESHNESS_BLOCK_REASON,
    EVIDENCE_FRESHNESS_WATCH_REASON,
    SOURCE_RELIABILITY_BLOCK_REASON,
    SOURCE_RELIABILITY_WATCH_REASON,
    CONTRADICTION_PRESSURE_BLOCK_REASON,
    CONTRADICTION_PRESSURE_WATCH_REASON,
    AMBIGUITY_BLOCK_REASON,
    AMBIGUITY_WATCH_REASON,
    TEAM_DISAGREEMENT_BLOCK_REASON,
    TEAM_DISAGREEMENT_WATCH_REASON,
    COST_INPUT_QUALITY_BLOCK_REASON,
    COST_INPUT_QUALITY_WATCH_REASON,
    THIN_AGGREGATE_EVIDENCE_REASON,
    THIN_AGGREGATE_SOURCES_REASON,
    WATCH_PRESENT_REASON,
    CLEAR_REASON,
    EMPTY_REASON,
)
BLOCK_REASON_CODES = (
    EVIDENCE_FRESHNESS_BLOCK_REASON,
    SOURCE_RELIABILITY_BLOCK_REASON,
    CONTRADICTION_PRESSURE_BLOCK_REASON,
    AMBIGUITY_BLOCK_REASON,
    TEAM_DISAGREEMENT_BLOCK_REASON,
    COST_INPUT_QUALITY_BLOCK_REASON,
    THIN_AGGREGATE_EVIDENCE_REASON,
    THIN_AGGREGATE_SOURCES_REASON,
)

NEXT_STEPS = {
    STATUS_PASS: "allow_report_only_research_strategy_information_risk_register",
    STATUS_WATCH: "watch_report_only_research_strategy_information_risk_register",
    STATUS_BLOCK: "block_report_only_research_strategy_information_risk_register",
}

DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
QUANT = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
WATCH_RISK_SCORE = Decimal("0.500000")
_CANONICAL_RE = re.compile(r"^[a-z0-9][a-z0-9_.-]*$")

__all__ = (
    "DEFAULT_RESEARCH_STRATEGY_INFORMATION_RISK_REGISTER_CONFIG_VERSION",
    "ResearchStrategyInformationRiskRegisterConfig",
    "ResearchStrategyInformationRiskRegisterInput",
    "ResearchStrategyInformationRiskRegisterRow",
    "ResearchStrategyInformationRiskRegisterReasonCodeCount",
    "ResearchStrategyInformationRiskRegisterReport",
    "build_research_strategy_information_risk_register_report",
    "research_strategy_information_risk_register_report_payload",
    "research_strategy_information_risk_register_report_digest",
)


@dataclass(frozen=True)
class ResearchStrategyInformationRiskRegisterConfig:
    config_version: str = (
        DEFAULT_RESEARCH_STRATEGY_INFORMATION_RISK_REGISTER_CONFIG_VERSION
    )
    watch_evidence_age_hours: Decimal = Decimal("24.000000")
    block_evidence_age_hours: Decimal = Decimal("72.000000")
    min_aggregate_evidence_count: Decimal = Decimal("2.000000")
    min_aggregate_source_count: Decimal = Decimal("2.000000")
    watch_min_source_reliability_score: Decimal = Decimal("0.700000")
    block_min_source_reliability_score: Decimal = Decimal("0.400000")
    watch_contradiction_pressure: Decimal = Decimal("0.250000")
    block_contradiction_pressure: Decimal = Decimal("0.600000")
    watch_ambiguity_score: Decimal = Decimal("0.350000")
    block_ambiguity_score: Decimal = Decimal("0.650000")
    watch_team_disagreement_ratio: Decimal = Decimal("0.250000")
    block_team_disagreement_ratio: Decimal = Decimal("0.500000")
    watch_min_cost_input_quality_score: Decimal = Decimal("0.700000")
    block_min_cost_input_quality_score: Decimal = Decimal("0.400000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchStrategyInformationRiskRegisterConfig:
            raise TypeError(
                "ResearchStrategyInformationRiskRegisterConfig does not support "
                "subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchStrategyInformationRiskRegisterConfig,
            "config",
        )
        _require_canonical_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_STRATEGY_INFORMATION_RISK_REGISTER_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "watch_evidence_age_hours",
            "block_evidence_age_hours",
            "min_aggregate_evidence_count",
            "min_aggregate_source_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_positive_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "watch_min_source_reliability_score",
            "block_min_source_reliability_score",
            "watch_contradiction_pressure",
            "block_contradiction_pressure",
            "watch_ambiguity_score",
            "block_ambiguity_score",
            "watch_team_disagreement_ratio",
            "block_team_disagreement_ratio",
            "watch_min_cost_input_quality_score",
            "block_min_cost_input_quality_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        _require_watch_not_above_blocked(
            "watch_evidence_age_hours",
            self.watch_evidence_age_hours,
            "block_evidence_age_hours",
            self.block_evidence_age_hours,
        )
        _require_watch_not_above_blocked(
            "watch_contradiction_pressure",
            self.watch_contradiction_pressure,
            "block_contradiction_pressure",
            self.block_contradiction_pressure,
        )
        _require_watch_not_above_blocked(
            "watch_ambiguity_score",
            self.watch_ambiguity_score,
            "block_ambiguity_score",
            self.block_ambiguity_score,
        )
        _require_watch_not_above_blocked(
            "watch_team_disagreement_ratio",
            self.watch_team_disagreement_ratio,
            "block_team_disagreement_ratio",
            self.block_team_disagreement_ratio,
        )
        _require_block_not_above_watch_minimum(
            "block_min_source_reliability_score",
            self.block_min_source_reliability_score,
            "watch_min_source_reliability_score",
            self.watch_min_source_reliability_score,
        )
        _require_block_not_above_watch_minimum(
            "block_min_cost_input_quality_score",
            self.block_min_cost_input_quality_score,
            "watch_min_cost_input_quality_score",
            self.watch_min_cost_input_quality_score,
        )
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class ResearchStrategyInformationRiskRegisterInput:
    candidate_label: str
    research_area: str
    evidence_as_of: datetime
    evidence_age_hours: Decimal
    aggregate_evidence_count: Decimal
    aggregate_source_count: Decimal
    source_reliability_score: Decimal
    contradiction_pressure: Decimal
    ambiguity_score: Decimal
    team_disagreement_ratio: Decimal
    cost_input_quality_score: Decimal
    upstream_reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchStrategyInformationRiskRegisterInput:
            raise TypeError(
                "ResearchStrategyInformationRiskRegisterInput does not support "
                "subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchStrategyInformationRiskRegisterInput, "input")
        for field_name in ("candidate_label", "research_area"):
            _require_canonical_string(field_name, getattr(self, field_name))
        object.__setattr__(
            self,
            "evidence_as_of",
            _as_utc("evidence_as_of", self.evidence_as_of),
        )
        for field_name in (
            "evidence_age_hours",
            "aggregate_evidence_count",
            "aggregate_source_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "source_reliability_score",
            "contradiction_pressure",
            "ambiguity_score",
            "team_disagreement_ratio",
            "cost_input_quality_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "upstream_reason_codes",
            _normalize_open_reason_codes(
                "upstream_reason_codes",
                self.upstream_reason_codes,
            ),
        )
        _require_hard_flags("input", self)


@dataclass(frozen=True)
class ResearchStrategyInformationRiskRegisterRow:
    candidate_label: str
    research_area: str
    evidence_as_of: datetime
    evidence_age_hours: Decimal
    aggregate_evidence_count: Decimal
    aggregate_source_count: Decimal
    source_reliability_score: Decimal
    contradiction_pressure: Decimal
    ambiguity_score: Decimal
    team_disagreement_ratio: Decimal
    cost_input_quality_score: Decimal
    information_risk_status: str
    risk_score: Decimal
    upstream_reason_codes: tuple[str, ...]
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchStrategyInformationRiskRegisterRow:
            raise TypeError(
                "ResearchStrategyInformationRiskRegisterRow does not support "
                "subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchStrategyInformationRiskRegisterRow, "row")
        for field_name in ("candidate_label", "research_area"):
            _require_canonical_string(field_name, getattr(self, field_name))
        object.__setattr__(
            self,
            "evidence_as_of",
            _as_utc("evidence_as_of", self.evidence_as_of),
        )
        for field_name in (
            "evidence_age_hours",
            "aggregate_evidence_count",
            "aggregate_source_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "source_reliability_score",
            "contradiction_pressure",
            "ambiguity_score",
            "team_disagreement_ratio",
            "cost_input_quality_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        _require_member(
            "information_risk_status",
            self.information_risk_status,
            INFORMATION_RISK_STATUSES,
        )
        object.__setattr__(
            self,
            "risk_score",
            _require_ratio_decimal("risk_score", self.risk_score),
        )
        object.__setattr__(
            self,
            "upstream_reason_codes",
            _normalize_open_reason_codes(
                "upstream_reason_codes",
                self.upstream_reason_codes,
            ),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(
                "reason_codes",
                self.reason_codes,
                ROW_REASON_CODE_SEQUENCE,
            ),
        )
        _validate_row_consistency(self)
        _require_hard_flags("row", self)


@dataclass(frozen=True)
class ResearchStrategyInformationRiskRegisterReasonCodeCount:
    reason_code: str
    count: Decimal
    row_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchStrategyInformationRiskRegisterReasonCodeCount:
            raise TypeError(
                "ResearchStrategyInformationRiskRegisterReasonCodeCount does not "
                "support subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchStrategyInformationRiskRegisterReasonCodeCount,
            "reason code count",
        )
        _require_member("reason_code", self.reason_code, REPORT_REASON_CODE_SEQUENCE)
        object.__setattr__(
            self,
            "count",
            _require_nonnegative_decimal("count", self.count),
        )
        object.__setattr__(
            self,
            "row_ratio",
            _require_ratio_decimal("row_ratio", self.row_ratio),
        )
        _require_hard_flags("reason code count", self)


@dataclass(frozen=True)
class ResearchStrategyInformationRiskRegisterReport:
    generated_at: datetime
    config_version: str
    register_status: str
    next_step: str
    input_count: Decimal
    row_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    evidence_freshness_risk_count: Decimal
    low_source_reliability_count: Decimal
    contradiction_pressure_count: Decimal
    ambiguity_count: Decimal
    team_disagreement_count: Decimal
    low_cost_input_quality_count: Decimal
    thin_evidence_count: Decimal
    thin_source_count: Decimal
    max_evidence_age_hours: Decimal
    min_source_reliability_score: Decimal
    max_contradiction_pressure: Decimal
    max_ambiguity_score: Decimal
    max_team_disagreement_ratio: Decimal
    min_cost_input_quality_score: Decimal
    information_risk_score: Decimal
    rows: tuple[ResearchStrategyInformationRiskRegisterRow, ...]
    reason_codes: tuple[str, ...]
    reason_code_counts: tuple[
        ResearchStrategyInformationRiskRegisterReasonCodeCount,
        ...,
    ]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchStrategyInformationRiskRegisterReport:
            raise TypeError(
                "ResearchStrategyInformationRiskRegisterReport does not support "
                "subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchStrategyInformationRiskRegisterReport, "report")
        object.__setattr__(
            self,
            "generated_at",
            _as_utc("generated_at", self.generated_at),
        )
        _require_canonical_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_STRATEGY_INFORMATION_RISK_REGISTER_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        _require_member("register_status", self.register_status, INFORMATION_RISK_STATUSES)
        _require_canonical_string("next_step", self.next_step)
        if self.next_step != NEXT_STEPS[self.register_status]:
            raise ValueError("next_step must match register_status")
        for field_name in (
            "input_count",
            "row_count",
            "pass_count",
            "watch_count",
            "block_count",
            "evidence_freshness_risk_count",
            "low_source_reliability_count",
            "contradiction_pressure_count",
            "ambiguity_count",
            "team_disagreement_count",
            "low_cost_input_quality_count",
            "thin_evidence_count",
            "thin_source_count",
            "max_evidence_age_hours",
            "min_source_reliability_score",
            "max_contradiction_pressure",
            "max_ambiguity_score",
            "max_team_disagreement_ratio",
            "min_cost_input_quality_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "information_risk_score",
            _require_ratio_decimal(
                "information_risk_score",
                self.information_risk_score,
            ),
        )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(
                "reason_codes",
                self.reason_codes,
                REPORT_REASON_CODE_SEQUENCE,
            ),
        )
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        _validate_report_consistency(self)
        _require_hard_flags("report", self)


def build_research_strategy_information_risk_register_report(
    inputs: tuple[object, ...],
    *,
    config: ResearchStrategyInformationRiskRegisterConfig | None = None,
    generated_at: datetime,
) -> ResearchStrategyInformationRiskRegisterReport:
    cfg = config or ResearchStrategyInformationRiskRegisterConfig()
    if type(cfg) is not ResearchStrategyInformationRiskRegisterConfig:
        raise ValueError(
            "config must be exactly ResearchStrategyInformationRiskRegisterConfig",
        )
    _require_hard_flags("config", cfg)
    generated_at_utc = _as_utc("generated_at", generated_at)
    normalized_inputs = _normalize_inputs(inputs)
    for row in normalized_inputs:
        if row.evidence_as_of > generated_at_utc:
            raise ValueError("evidence_as_of cannot be after generated_at")
    rows = tuple(
        sorted(
            (_build_row(row, config=cfg) for row in normalized_inputs),
            key=_row_sort_key,
        ),
    )
    reason_codes = _report_reason_codes(rows)
    register_status = _report_status(rows)
    return ResearchStrategyInformationRiskRegisterReport(
        generated_at=generated_at_utc,
        config_version=cfg.config_version,
        register_status=register_status,
        next_step=NEXT_STEPS[register_status],
        input_count=_decimal_count(len(normalized_inputs)),
        row_count=_decimal_count(len(rows)),
        pass_count=_status_count(rows, STATUS_PASS),
        watch_count=_status_count(rows, STATUS_WATCH),
        block_count=_status_count(rows, STATUS_BLOCK),
        evidence_freshness_risk_count=(
            _reason_count(EVIDENCE_FRESHNESS_BLOCK_REASON, rows)
            + _reason_count(EVIDENCE_FRESHNESS_WATCH_REASON, rows)
        ),
        low_source_reliability_count=(
            _reason_count(SOURCE_RELIABILITY_BLOCK_REASON, rows)
            + _reason_count(SOURCE_RELIABILITY_WATCH_REASON, rows)
        ),
        contradiction_pressure_count=(
            _reason_count(CONTRADICTION_PRESSURE_BLOCK_REASON, rows)
            + _reason_count(CONTRADICTION_PRESSURE_WATCH_REASON, rows)
        ),
        ambiguity_count=(
            _reason_count(AMBIGUITY_BLOCK_REASON, rows)
            + _reason_count(AMBIGUITY_WATCH_REASON, rows)
        ),
        team_disagreement_count=(
            _reason_count(TEAM_DISAGREEMENT_BLOCK_REASON, rows)
            + _reason_count(TEAM_DISAGREEMENT_WATCH_REASON, rows)
        ),
        low_cost_input_quality_count=(
            _reason_count(COST_INPUT_QUALITY_BLOCK_REASON, rows)
            + _reason_count(COST_INPUT_QUALITY_WATCH_REASON, rows)
        ),
        thin_evidence_count=_reason_count(THIN_AGGREGATE_EVIDENCE_REASON, rows),
        thin_source_count=_reason_count(THIN_AGGREGATE_SOURCES_REASON, rows),
        max_evidence_age_hours=_max_decimal(
            (row.evidence_age_hours for row in rows),
            default=ZERO,
        ),
        min_source_reliability_score=_min_decimal(
            (row.source_reliability_score for row in rows),
            default=ZERO,
        ),
        max_contradiction_pressure=_max_decimal(
            (row.contradiction_pressure for row in rows),
            default=ZERO,
        ),
        max_ambiguity_score=_max_decimal(
            (row.ambiguity_score for row in rows),
            default=ZERO,
        ),
        max_team_disagreement_ratio=_max_decimal(
            (row.team_disagreement_ratio for row in rows),
            default=ZERO,
        ),
        min_cost_input_quality_score=_min_decimal(
            (row.cost_input_quality_score for row in rows),
            default=ZERO,
        ),
        information_risk_score=_report_risk_score(rows),
        rows=rows,
        reason_codes=reason_codes,
        reason_code_counts=_reason_code_counts(reason_codes, rows),
    )


def research_strategy_information_risk_register_report_payload(
    report: ResearchStrategyInformationRiskRegisterReport,
) -> dict[str, Any]:
    if type(report) is not ResearchStrategyInformationRiskRegisterReport:
        raise ValueError(
            "report must be exactly ResearchStrategyInformationRiskRegisterReport",
        )
    _validate_report_consistency(report)
    return _payload_value(report)


def research_strategy_information_risk_register_report_digest(
    report: ResearchStrategyInformationRiskRegisterReport,
) -> str:
    payload = research_strategy_information_risk_register_report_payload(report)
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _build_row(
    row: ResearchStrategyInformationRiskRegisterInput,
    *,
    config: ResearchStrategyInformationRiskRegisterConfig,
) -> ResearchStrategyInformationRiskRegisterRow:
    reason_codes = _row_reason_codes(row, config=config)
    information_risk_status = _row_status(reason_codes)
    return ResearchStrategyInformationRiskRegisterRow(
        candidate_label=row.candidate_label,
        research_area=row.research_area,
        evidence_as_of=row.evidence_as_of,
        evidence_age_hours=row.evidence_age_hours,
        aggregate_evidence_count=row.aggregate_evidence_count,
        aggregate_source_count=row.aggregate_source_count,
        source_reliability_score=row.source_reliability_score,
        contradiction_pressure=row.contradiction_pressure,
        ambiguity_score=row.ambiguity_score,
        team_disagreement_ratio=row.team_disagreement_ratio,
        cost_input_quality_score=row.cost_input_quality_score,
        information_risk_status=information_risk_status,
        risk_score=_status_risk_score(information_risk_status),
        upstream_reason_codes=row.upstream_reason_codes,
        reason_codes=reason_codes,
    )


def _row_reason_codes(
    row: ResearchStrategyInformationRiskRegisterInput,
    *,
    config: ResearchStrategyInformationRiskRegisterConfig,
) -> tuple[str, ...]:
    reasons: list[str] = []
    if row.evidence_age_hours >= config.block_evidence_age_hours:
        reasons.append(EVIDENCE_FRESHNESS_BLOCK_REASON)
    elif row.evidence_age_hours >= config.watch_evidence_age_hours:
        reasons.append(EVIDENCE_FRESHNESS_WATCH_REASON)
    if row.source_reliability_score <= config.block_min_source_reliability_score:
        reasons.append(SOURCE_RELIABILITY_BLOCK_REASON)
    elif row.source_reliability_score <= config.watch_min_source_reliability_score:
        reasons.append(SOURCE_RELIABILITY_WATCH_REASON)
    if row.contradiction_pressure >= config.block_contradiction_pressure:
        reasons.append(CONTRADICTION_PRESSURE_BLOCK_REASON)
    elif row.contradiction_pressure >= config.watch_contradiction_pressure:
        reasons.append(CONTRADICTION_PRESSURE_WATCH_REASON)
    if row.ambiguity_score >= config.block_ambiguity_score:
        reasons.append(AMBIGUITY_BLOCK_REASON)
    elif row.ambiguity_score >= config.watch_ambiguity_score:
        reasons.append(AMBIGUITY_WATCH_REASON)
    if row.team_disagreement_ratio >= config.block_team_disagreement_ratio:
        reasons.append(TEAM_DISAGREEMENT_BLOCK_REASON)
    elif row.team_disagreement_ratio >= config.watch_team_disagreement_ratio:
        reasons.append(TEAM_DISAGREEMENT_WATCH_REASON)
    if row.cost_input_quality_score <= config.block_min_cost_input_quality_score:
        reasons.append(COST_INPUT_QUALITY_BLOCK_REASON)
    elif row.cost_input_quality_score <= config.watch_min_cost_input_quality_score:
        reasons.append(COST_INPUT_QUALITY_WATCH_REASON)
    if row.aggregate_evidence_count < config.min_aggregate_evidence_count:
        reasons.append(THIN_AGGREGATE_EVIDENCE_REASON)
    if row.aggregate_source_count < config.min_aggregate_source_count:
        reasons.append(THIN_AGGREGATE_SOURCES_REASON)
    if not reasons:
        reasons.append(PASS_REASON)
    return _normalize_reason_codes(
        "reason_codes",
        tuple(reasons),
        ROW_REASON_CODE_SEQUENCE,
    )


def _row_status(reason_codes: tuple[str, ...]) -> str:
    if any(reason in BLOCK_REASON_CODES for reason in reason_codes):
        return STATUS_BLOCK
    if reason_codes == (PASS_REASON,):
        return STATUS_PASS
    return STATUS_WATCH


def _status_risk_score(status: str) -> Decimal:
    if status == STATUS_BLOCK:
        return ONE
    if status == STATUS_WATCH:
        return WATCH_RISK_SCORE
    return ZERO


def _report_reason_codes(
    rows: tuple[ResearchStrategyInformationRiskRegisterRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return (EMPTY_REASON,)
    present = {reason for row in rows for reason in row.reason_codes if reason != PASS_REASON}
    reasons = [reason for reason in REPORT_REASON_CODE_SEQUENCE if reason in present]
    if any(row.information_risk_status == STATUS_WATCH for row in rows):
        reasons.append(WATCH_PRESENT_REASON)
    if not reasons:
        reasons.append(CLEAR_REASON)
    return _normalize_reason_codes(
        "reason_codes",
        tuple(reasons),
        REPORT_REASON_CODE_SEQUENCE,
    )


def _report_status(rows: tuple[ResearchStrategyInformationRiskRegisterRow, ...]) -> str:
    if not rows:
        return STATUS_BLOCK
    if any(row.information_risk_status == STATUS_BLOCK for row in rows):
        return STATUS_BLOCK
    if any(row.information_risk_status == STATUS_WATCH for row in rows):
        return STATUS_WATCH
    return STATUS_PASS


def _reason_code_counts(
    reason_codes: tuple[str, ...],
    rows: tuple[ResearchStrategyInformationRiskRegisterRow, ...],
) -> tuple[ResearchStrategyInformationRiskRegisterReasonCodeCount, ...]:
    row_count = _decimal_count(len(rows))
    if reason_codes == (EMPTY_REASON,):
        return (
            ResearchStrategyInformationRiskRegisterReasonCodeCount(
                reason_code=EMPTY_REASON,
                count=ONE,
                row_ratio=ZERO,
            ),
        )
    return tuple(
        ResearchStrategyInformationRiskRegisterReasonCodeCount(
            reason_code=reason_code,
            count=_report_reason_count(reason_code, rows),
            row_ratio=_ratio(_report_reason_count(reason_code, rows), row_count),
        )
        for reason_code in reason_codes
    )


def _report_reason_count(
    reason_code: str,
    rows: tuple[ResearchStrategyInformationRiskRegisterRow, ...],
) -> Decimal:
    if reason_code == WATCH_PRESENT_REASON:
        return _status_count(rows, STATUS_WATCH)
    if reason_code == CLEAR_REASON:
        return _status_count(rows, STATUS_PASS)
    return _reason_count(reason_code, rows)


def _reason_count(
    reason_code: str,
    rows: tuple[ResearchStrategyInformationRiskRegisterRow, ...],
) -> Decimal:
    return _decimal_count(sum(1 for row in rows if reason_code in row.reason_codes))


def _status_count(
    rows: tuple[ResearchStrategyInformationRiskRegisterRow, ...],
    status: str,
) -> Decimal:
    return _decimal_count(
        sum(1 for row in rows if row.information_risk_status == status),
    )


def _report_risk_score(
    rows: tuple[ResearchStrategyInformationRiskRegisterRow, ...],
) -> Decimal:
    if not rows:
        return ZERO
    weighted = _status_count(rows, STATUS_BLOCK) + (
        _status_count(rows, STATUS_WATCH) * WATCH_RISK_SCORE
    )
    return _ratio(weighted, _decimal_count(len(rows)))


def _validate_row_consistency(
    row: ResearchStrategyInformationRiskRegisterRow,
) -> None:
    if row.information_risk_status != _row_status(row.reason_codes):
        raise ValueError("reason_codes must match information_risk_status")
    if row.risk_score != _status_risk_score(row.information_risk_status):
        raise ValueError("risk_score must match information_risk_status")
    if row.information_risk_status == STATUS_PASS and row.reason_codes != (PASS_REASON,):
        raise ValueError("reason_codes must match information_risk_status")
    if row.information_risk_status != STATUS_PASS and PASS_REASON in row.reason_codes:
        raise ValueError("reason_codes must match information_risk_status")


def _validate_report_consistency(
    report: ResearchStrategyInformationRiskRegisterReport,
) -> None:
    if report.input_count != _decimal_count(len(report.rows)):
        raise ValueError("input_count must match rows")
    if report.row_count != _decimal_count(len(report.rows)):
        raise ValueError("row_count must match rows")
    if report.pass_count != _status_count(report.rows, STATUS_PASS):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _status_count(report.rows, STATUS_WATCH):
        raise ValueError("watch_count must match rows")
    if report.block_count != _status_count(report.rows, STATUS_BLOCK):
        raise ValueError("block_count must match rows")
    if report.pass_count + report.watch_count + report.block_count != report.row_count:
        raise ValueError("status counts must match rows")
    if report.evidence_freshness_risk_count != (
        _reason_count(EVIDENCE_FRESHNESS_BLOCK_REASON, report.rows)
        + _reason_count(EVIDENCE_FRESHNESS_WATCH_REASON, report.rows)
    ):
        raise ValueError("evidence_freshness_risk_count must match rows")
    if report.low_source_reliability_count != (
        _reason_count(SOURCE_RELIABILITY_BLOCK_REASON, report.rows)
        + _reason_count(SOURCE_RELIABILITY_WATCH_REASON, report.rows)
    ):
        raise ValueError("low_source_reliability_count must match rows")
    if report.contradiction_pressure_count != (
        _reason_count(CONTRADICTION_PRESSURE_BLOCK_REASON, report.rows)
        + _reason_count(CONTRADICTION_PRESSURE_WATCH_REASON, report.rows)
    ):
        raise ValueError("contradiction_pressure_count must match rows")
    if report.ambiguity_count != (
        _reason_count(AMBIGUITY_BLOCK_REASON, report.rows)
        + _reason_count(AMBIGUITY_WATCH_REASON, report.rows)
    ):
        raise ValueError("ambiguity_count must match rows")
    if report.team_disagreement_count != (
        _reason_count(TEAM_DISAGREEMENT_BLOCK_REASON, report.rows)
        + _reason_count(TEAM_DISAGREEMENT_WATCH_REASON, report.rows)
    ):
        raise ValueError("team_disagreement_count must match rows")
    if report.low_cost_input_quality_count != (
        _reason_count(COST_INPUT_QUALITY_BLOCK_REASON, report.rows)
        + _reason_count(COST_INPUT_QUALITY_WATCH_REASON, report.rows)
    ):
        raise ValueError("low_cost_input_quality_count must match rows")
    if report.thin_evidence_count != _reason_count(
        THIN_AGGREGATE_EVIDENCE_REASON,
        report.rows,
    ):
        raise ValueError("thin_evidence_count must match rows")
    if report.thin_source_count != _reason_count(
        THIN_AGGREGATE_SOURCES_REASON,
        report.rows,
    ):
        raise ValueError("thin_source_count must match rows")
    if report.max_evidence_age_hours != _max_decimal(
        (row.evidence_age_hours for row in report.rows),
        default=ZERO,
    ):
        raise ValueError("max_evidence_age_hours must match rows")
    if report.min_source_reliability_score != _min_decimal(
        (row.source_reliability_score for row in report.rows),
        default=ZERO,
    ):
        raise ValueError("min_source_reliability_score must match rows")
    if report.max_contradiction_pressure != _max_decimal(
        (row.contradiction_pressure for row in report.rows),
        default=ZERO,
    ):
        raise ValueError("max_contradiction_pressure must match rows")
    if report.max_ambiguity_score != _max_decimal(
        (row.ambiguity_score for row in report.rows),
        default=ZERO,
    ):
        raise ValueError("max_ambiguity_score must match rows")
    if report.max_team_disagreement_ratio != _max_decimal(
        (row.team_disagreement_ratio for row in report.rows),
        default=ZERO,
    ):
        raise ValueError("max_team_disagreement_ratio must match rows")
    if report.min_cost_input_quality_score != _min_decimal(
        (row.cost_input_quality_score for row in report.rows),
        default=ZERO,
    ):
        raise ValueError("min_cost_input_quality_score must match rows")
    if report.information_risk_score != _report_risk_score(report.rows):
        raise ValueError("information_risk_score must match rows")
    if report.register_status != _report_status(report.rows):
        raise ValueError("register_status must match rows")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")
    if report.reason_code_counts != _reason_code_counts(report.reason_codes, report.rows):
        raise ValueError("reason_code_counts must match reason_codes")


def _normalize_inputs(
    inputs: tuple[object, ...],
) -> tuple[ResearchStrategyInformationRiskRegisterInput, ...]:
    if type(inputs) is not tuple:
        raise ValueError("inputs must be a tuple")
    seen_candidate_labels: set[str] = set()
    normalized: list[ResearchStrategyInformationRiskRegisterInput] = []
    for row in inputs:
        if type(row) is not ResearchStrategyInformationRiskRegisterInput:
            raise ValueError(
                "inputs must contain ResearchStrategyInformationRiskRegisterInput",
            )
        _require_hard_flags("input", row)
        if row.candidate_label in seen_candidate_labels:
            raise ValueError("inputs must not contain duplicate candidate_label values")
        seen_candidate_labels.add(row.candidate_label)
        normalized.append(row)
    return tuple(normalized)


def _normalize_rows(
    rows: tuple[ResearchStrategyInformationRiskRegisterRow, ...],
) -> tuple[ResearchStrategyInformationRiskRegisterRow, ...]:
    if type(rows) is not tuple:
        raise ValueError("rows must be a tuple")
    seen_candidate_labels: set[str] = set()
    for row in rows:
        if type(row) is not ResearchStrategyInformationRiskRegisterRow:
            raise ValueError(
                "rows must contain ResearchStrategyInformationRiskRegisterRow",
            )
        _require_hard_flags("row", row)
        if row.candidate_label in seen_candidate_labels:
            raise ValueError("rows must not contain duplicate candidate_label values")
        seen_candidate_labels.add(row.candidate_label)
    return tuple(sorted(rows, key=_row_sort_key))


def _normalize_reason_code_counts(
    rows: tuple[ResearchStrategyInformationRiskRegisterReasonCodeCount, ...],
) -> tuple[ResearchStrategyInformationRiskRegisterReasonCodeCount, ...]:
    if type(rows) is not tuple:
        raise ValueError("reason_code_counts must be a tuple")
    for row in rows:
        if type(row) is not ResearchStrategyInformationRiskRegisterReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "ResearchStrategyInformationRiskRegisterReasonCodeCount",
            )
        _require_hard_flags("reason code count", row)
    return tuple(
        sorted(rows, key=lambda row: REPORT_REASON_CODE_SEQUENCE.index(row.reason_code)),
    )


def _normalize_open_reason_codes(
    field_name: str,
    reason_codes: tuple[str, ...],
) -> tuple[str, ...]:
    if type(reason_codes) is not tuple:
        raise ValueError(f"{field_name} must be a tuple")
    seen: set[str] = set()
    normalized: list[str] = []
    for reason_code in reason_codes:
        _require_canonical_string("reason_code", reason_code)
        if reason_code not in seen:
            normalized.append(reason_code)
            seen.add(reason_code)
    return tuple(sorted(normalized))


def _normalize_reason_codes(
    field_name: str,
    reason_codes: Iterable[str],
    sequence: tuple[str, ...],
) -> tuple[str, ...]:
    if isinstance(reason_codes, (str, bytes)) or not isinstance(reason_codes, Iterable):
        raise ValueError(f"{field_name} must contain reason code strings")
    normalized = tuple(reason_codes)
    seen: set[str] = set()
    for reason_code in normalized:
        _require_member("reason_code", reason_code, sequence)
        if reason_code in seen:
            raise ValueError(f"{field_name} must be unique")
        seen.add(reason_code)
    return tuple(reason_code for reason_code in sequence if reason_code in seen)


def _row_sort_key(
    row: ResearchStrategyInformationRiskRegisterRow,
) -> tuple[int, Decimal, str, str]:
    status_rank = {
        STATUS_BLOCK: 0,
        STATUS_WATCH: 1,
        STATUS_PASS: 2,
    }
    return (
        status_rank[row.information_risk_status],
        -row.risk_score,
        row.candidate_label,
        row.research_area,
    )


def _max_decimal(values: Iterable[Decimal], *, default: Decimal) -> Decimal:
    normalized = tuple(values)
    if not normalized:
        return default
    for value in normalized:
        if type(value) is not Decimal:
            raise ValueError("values must be Decimals")
    return _quantize(max(normalized))


def _min_decimal(values: Iterable[Decimal], *, default: Decimal) -> Decimal:
    normalized = tuple(values)
    if not normalized:
        return default
    for value in normalized:
        if type(value) is not Decimal:
            raise ValueError("values must be Decimals")
    return _quantize(min(normalized))


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return _quantize(numerator / denominator)


def _decimal_count(value: int) -> Decimal:
    return _quantize(Decimal(value))


def _require_watch_not_above_blocked(
    watch_field_name: str,
    watch_value: Decimal,
    blocked_field_name: str,
    blocked_value: Decimal,
) -> None:
    if watch_value > blocked_value:
        raise ValueError(f"{watch_field_name} must not exceed {blocked_field_name}")


def _require_block_not_above_watch_minimum(
    block_field_name: str,
    block_value: Decimal,
    watch_field_name: str,
    watch_value: Decimal,
) -> None:
    if block_value > watch_value:
        raise ValueError(f"{block_field_name} must not exceed {watch_field_name}")


def _require_ratio_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_nonnegative_decimal(field_name, value)
    if decimal_value > ONE:
        raise ValueError(f"{field_name} must be between zero and one")
    return decimal_value


def _require_positive_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return decimal_value


def _require_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return decimal_value


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return _quantize(value)


def _quantize(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(QUANT)


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be exactly datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_member(field_name: str, value: object, allowed: tuple[str, ...]) -> None:
    _require_canonical_string(field_name, value)
    if value not in allowed:
        raise ValueError(f"{field_name} must be supported")


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a plain str")
    if not value or value.strip() != value or _CANONICAL_RE.fullmatch(value) is None:
        raise ValueError(f"{field_name} must be a canonical nonblank string")


def _require_hard_flags(field_name: str, value: object) -> None:
    if getattr(value, "paper_only", None) is not True:
        raise ValueError(f"{field_name} paper_only must be True")
    if getattr(value, "report_only", None) is not True:
        raise ValueError(f"{field_name} report_only must be True")
    if getattr(value, "readonly", None) is not True:
        raise ValueError(f"{field_name} readonly must be True")


def _require_exact_type(value: object, expected_type: type[object], field_name: str) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{field_name} must be exactly {expected_type.__name__}")


def _payload_value(value: object) -> Any:
    if isinstance(value, Decimal):
        return format(value, "f")
    if type(value) is datetime:
        return value.isoformat()
    if is_dataclass(value) and not isinstance(value, type):
        return {
            field.name: _payload_value(getattr(value, field.name))
            for field in fields(value)
        }
    if isinstance(value, tuple):
        return [_payload_value(item) for item in value]
    return value
