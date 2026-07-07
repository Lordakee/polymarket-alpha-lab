"""Pure report reducer for human research decision packet completeness."""

from __future__ import annotations

from dataclasses import InitVar, asdict, dataclass, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
from typing import Any


DEFAULT_RESEARCH_DECISION_PACKET_COMPLETENESS_CONFIG_VERSION = (
    "research-decision-packet-completeness-report-v0"
)

STATUS_PASS = "pass"
STATUS_WATCH = "watch"
STATUS_BLOCK = "block"

REASON_PREFIX = "research_decision_packet_completeness_"
NO_INPUTS_REASON = f"{REASON_PREFIX}no_inputs"
PASS_REASON = f"{REASON_PREFIX}pass"
STALE_PACKET_REASON = f"{REASON_PREFIX}stale_packet"
SLOW_TEAM_REVIEW_REASON = f"{REASON_PREFIX}slow_team_review"
MISSING_PROBABILITY_ASSUMPTIONS_REASON = f"{REASON_PREFIX}missing_probability_assumptions"
MISSING_EVIDENCE_REASON = f"{REASON_PREFIX}missing_evidence"
MISSING_COUNTER_EVIDENCE_REASON = f"{REASON_PREFIX}missing_counter_evidence"
MISSING_COST_REVIEW_REASON = f"{REASON_PREFIX}missing_cost_review"
MISSING_SETTLEMENT_RULES_REASON = f"{REASON_PREFIX}missing_settlement_rules"
MISSING_TEAM_REVIEW_REASON = f"{REASON_PREFIX}missing_team_review"
MISSING_RETROSPECTIVE_PLAN_REASON = f"{REASON_PREFIX}missing_retrospective_plan"
WEAK_PROBABILITY_ASSUMPTIONS_REASON = f"{REASON_PREFIX}weak_probability_assumptions"
WEAK_EVIDENCE_REASON = f"{REASON_PREFIX}weak_evidence"
WEAK_COUNTER_EVIDENCE_REASON = f"{REASON_PREFIX}weak_counter_evidence"
WEAK_COST_REVIEW_REASON = f"{REASON_PREFIX}weak_cost_review"
WEAK_SETTLEMENT_RULES_REASON = f"{REASON_PREFIX}weak_settlement_rules"
WEAK_TEAM_REVIEW_REASON = f"{REASON_PREFIX}weak_team_review"
WEAK_RETROSPECTIVE_PLAN_REASON = f"{REASON_PREFIX}weak_retrospective_plan"

REASON_CODE_SEQUENCE = (
    NO_INPUTS_REASON,
    MISSING_PROBABILITY_ASSUMPTIONS_REASON,
    MISSING_EVIDENCE_REASON,
    MISSING_COUNTER_EVIDENCE_REASON,
    MISSING_COST_REVIEW_REASON,
    MISSING_SETTLEMENT_RULES_REASON,
    MISSING_TEAM_REVIEW_REASON,
    MISSING_RETROSPECTIVE_PLAN_REASON,
    SLOW_TEAM_REVIEW_REASON,
    STALE_PACKET_REASON,
    WEAK_PROBABILITY_ASSUMPTIONS_REASON,
    WEAK_EVIDENCE_REASON,
    WEAK_COUNTER_EVIDENCE_REASON,
    WEAK_COST_REVIEW_REASON,
    WEAK_SETTLEMENT_RULES_REASON,
    WEAK_TEAM_REVIEW_REASON,
    WEAK_RETROSPECTIVE_PLAN_REASON,
    PASS_REASON,
)
ROW_REASON_CODE_SEQUENCE = (
    MISSING_PROBABILITY_ASSUMPTIONS_REASON,
    MISSING_EVIDENCE_REASON,
    MISSING_COUNTER_EVIDENCE_REASON,
    MISSING_COST_REVIEW_REASON,
    MISSING_SETTLEMENT_RULES_REASON,
    MISSING_TEAM_REVIEW_REASON,
    MISSING_RETROSPECTIVE_PLAN_REASON,
    SLOW_TEAM_REVIEW_REASON,
    STALE_PACKET_REASON,
    WEAK_PROBABILITY_ASSUMPTIONS_REASON,
    WEAK_EVIDENCE_REASON,
    WEAK_COUNTER_EVIDENCE_REASON,
    WEAK_COST_REVIEW_REASON,
    WEAK_SETTLEMENT_RULES_REASON,
    WEAK_TEAM_REVIEW_REASON,
    WEAK_RETROSPECTIVE_PLAN_REASON,
    PASS_REASON,
)

NEXT_STEPS = {
    STATUS_PASS: "pass_report_only_decision_packet_completeness",
    STATUS_WATCH: "watch_report_only_decision_packet_completeness",
    STATUS_BLOCK: "block_report_only_decision_packet_completeness",
}

DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
QUANT = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
MICROSECONDS_PER_SECOND = Decimal("1000000")

_PUBLIC_REFERENCE_FRAGMENTS = ("public", "memo", "bulletin", "notice", "release")


@dataclass(frozen=True)
class ResearchDecisionPacketCompletenessConfig:
    config_version: str = DEFAULT_RESEARCH_DECISION_PACKET_COMPLETENESS_CONFIG_VERSION
    max_packet_age_seconds: Decimal = Decimal("86400.000000")
    max_team_review_lag_seconds: Decimal = Decimal("7200.000000")
    min_probability_assumption_count: Decimal = Decimal("1")
    min_evidence_source_count: Decimal = Decimal("2")
    min_counter_evidence_count: Decimal = Decimal("1")
    min_cost_review_count: Decimal = Decimal("1")
    min_settlement_rule_count: Decimal = Decimal("1")
    min_team_reviewer_count: Decimal = Decimal("1")
    min_retrospective_plan_count: Decimal = Decimal("1")
    min_section_quality: Decimal = Decimal("0.700000")
    watch_section_quality: Decimal = Decimal("0.500000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchDecisionPacketCompletenessConfig:
            raise TypeError(
                "ResearchDecisionPacketCompletenessConfig does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchDecisionPacketCompletenessConfig:
            raise ValueError(
                "config must be exactly ResearchDecisionPacketCompletenessConfig",
            )
        _require_public_string("config_version", self.config_version)
        for field_name in (
            "max_packet_age_seconds",
            "max_team_review_lag_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "min_probability_assumption_count",
            "min_evidence_source_count",
            "min_counter_evidence_count",
            "min_cost_review_count",
            "min_settlement_rule_count",
            "min_team_reviewer_count",
            "min_retrospective_plan_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_count_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "min_section_quality",
            _require_ratio_decimal("min_section_quality", self.min_section_quality),
        )
        object.__setattr__(
            self,
            "watch_section_quality",
            _require_ratio_decimal("watch_section_quality", self.watch_section_quality),
        )
        if self.watch_section_quality > self.min_section_quality:
            raise ValueError("watch_section_quality must not exceed min_section_quality")
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class ResearchDecisionPacketCompletenessInputRow:
    packet_key: str
    condition_id: str
    packet_label: str
    public_packet_reference: str
    prepared_at: datetime
    reviewed_at: datetime | None
    probability_assumption_count: Decimal
    probability_assumption_quality: Decimal
    evidence_source_count: Decimal
    evidence_quality: Decimal
    counter_evidence_count: Decimal
    counter_evidence_quality: Decimal
    cost_review_count: Decimal
    cost_review_quality: Decimal
    settlement_rule_count: Decimal
    settlement_rule_quality: Decimal
    team_reviewer_count: Decimal
    team_review_quality: Decimal
    retrospective_plan_count: Decimal
    retrospective_plan_quality: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchDecisionPacketCompletenessInputRow:
            raise TypeError(
                "ResearchDecisionPacketCompletenessInputRow does not support "
                "subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchDecisionPacketCompletenessInputRow:
            raise ValueError(
                "input row must be exactly ResearchDecisionPacketCompletenessInputRow",
            )
        for field_name in ("packet_key", "condition_id", "packet_label"):
            _require_public_string(field_name, getattr(self, field_name))
        _require_reference("public_packet_reference", self.public_packet_reference)
        object.__setattr__(
            self,
            "prepared_at",
            _as_utc("prepared_at", self.prepared_at),
        )
        object.__setattr__(
            self,
            "reviewed_at",
            _optional_utc("reviewed_at", self.reviewed_at),
        )
        for field_name in (
            "probability_assumption_count",
            "evidence_source_count",
            "counter_evidence_count",
            "cost_review_count",
            "settlement_rule_count",
            "team_reviewer_count",
            "retrospective_plan_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_count_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "probability_assumption_quality",
            "evidence_quality",
            "counter_evidence_quality",
            "cost_review_quality",
            "settlement_rule_quality",
            "team_review_quality",
            "retrospective_plan_quality",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        if self.reviewed_at is not None and self.reviewed_at < self.prepared_at:
            raise ValueError("reviewed_at must be on or after prepared_at")
        _require_hard_flags("input row", self)


@dataclass(frozen=True)
class ResearchDecisionPacketCompletenessRow:
    packet_key: str
    condition_id: str
    packet_label: str
    prepared_at: datetime
    reviewed_at: datetime | None
    packet_age_seconds: Decimal
    team_review_lag_seconds: Decimal | None
    probability_assumption_count: Decimal
    probability_assumption_quality: Decimal
    evidence_source_count: Decimal
    evidence_quality: Decimal
    counter_evidence_count: Decimal
    counter_evidence_quality: Decimal
    cost_review_count: Decimal
    cost_review_quality: Decimal
    settlement_rule_count: Decimal
    settlement_rule_quality: Decimal
    team_reviewer_count: Decimal
    team_review_quality: Decimal
    retrospective_plan_count: Decimal
    retrospective_plan_quality: Decimal
    completeness_score: Decimal
    packet_status: str
    redacted_packet_reference: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True
    validation_config: InitVar[ResearchDecisionPacketCompletenessConfig | None] = None

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchDecisionPacketCompletenessRow:
            raise TypeError(
                "ResearchDecisionPacketCompletenessRow does not support subclassing",
            )

    def __post_init__(
        self,
        validation_config: ResearchDecisionPacketCompletenessConfig | None,
    ) -> None:
        if type(self) is not ResearchDecisionPacketCompletenessRow:
            raise ValueError("row must be exactly ResearchDecisionPacketCompletenessRow")
        for field_name in ("packet_key", "condition_id", "packet_label"):
            _require_public_string(field_name, getattr(self, field_name))
        object.__setattr__(
            self,
            "prepared_at",
            _as_utc("prepared_at", self.prepared_at),
        )
        object.__setattr__(
            self,
            "reviewed_at",
            _optional_utc("reviewed_at", self.reviewed_at),
        )
        object.__setattr__(
            self,
            "packet_age_seconds",
            _require_nonnegative_decimal("packet_age_seconds", self.packet_age_seconds),
        )
        object.__setattr__(
            self,
            "team_review_lag_seconds",
            _require_optional_nonnegative_decimal(
                "team_review_lag_seconds",
                self.team_review_lag_seconds,
            ),
        )
        for field_name in (
            "probability_assumption_count",
            "evidence_source_count",
            "counter_evidence_count",
            "cost_review_count",
            "settlement_rule_count",
            "team_reviewer_count",
            "retrospective_plan_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_count_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "probability_assumption_quality",
            "evidence_quality",
            "counter_evidence_quality",
            "cost_review_quality",
            "settlement_rule_quality",
            "team_review_quality",
            "retrospective_plan_quality",
            "completeness_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        _require_status("packet_status", self.packet_status)
        object.__setattr__(
            self,
            "redacted_packet_reference",
            _require_redacted_reference(
                "redacted_packet_reference",
                self.redacted_packet_reference,
            ),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_row_reason_codes(self.reason_codes),
        )
        _validate_row(self, config=validation_config)
        _require_hard_flags("row", self)


@dataclass(frozen=True)
class ResearchDecisionPacketCompletenessReasonCodeCount:
    reason_code: str
    count: Decimal
    packet_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchDecisionPacketCompletenessReasonCodeCount:
            raise TypeError(
                "ResearchDecisionPacketCompletenessReasonCodeCount does not support "
                "subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchDecisionPacketCompletenessReasonCodeCount:
            raise ValueError(
                "reason code count must be exactly "
                "ResearchDecisionPacketCompletenessReasonCodeCount",
            )
        _require_reason_code("reason_code", self.reason_code, REASON_CODE_SEQUENCE)
        object.__setattr__(
            self,
            "count",
            _require_nonnegative_decimal("count", self.count),
        )
        object.__setattr__(
            self,
            "packet_ratio",
            _require_ratio_decimal("packet_ratio", self.packet_ratio),
        )
        _require_hard_flags("reason code count", self)


@dataclass(frozen=True)
class ResearchDecisionPacketCompletenessReport:
    generated_at: datetime
    config_version: str
    report_status: str
    next_step: str
    packet_count: Decimal
    pass_packet_count: Decimal
    watch_packet_count: Decimal
    blocked_packet_count: Decimal
    stale_packet_count: Decimal
    slow_team_review_count: Decimal
    missing_probability_assumption_count: Decimal
    missing_evidence_count: Decimal
    missing_counter_evidence_count: Decimal
    missing_cost_review_count: Decimal
    missing_settlement_rule_count: Decimal
    missing_team_review_count: Decimal
    missing_retrospective_plan_count: Decimal
    average_completeness_score: Decimal
    minimum_completeness_score: Decimal
    rows: tuple[ResearchDecisionPacketCompletenessRow, ...]
    reason_code_counts: tuple[ResearchDecisionPacketCompletenessReasonCodeCount, ...]
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchDecisionPacketCompletenessReport:
            raise TypeError(
                "ResearchDecisionPacketCompletenessReport does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchDecisionPacketCompletenessReport:
            raise ValueError(
                "report must be exactly ResearchDecisionPacketCompletenessReport",
            )
        object.__setattr__(
            self,
            "generated_at",
            _as_utc("generated_at", self.generated_at),
        )
        _require_public_string("config_version", self.config_version)
        _require_status("report_status", self.report_status)
        _require_public_string("next_step", self.next_step)
        for field_name in (
            "packet_count",
            "pass_packet_count",
            "watch_packet_count",
            "blocked_packet_count",
            "stale_packet_count",
            "slow_team_review_count",
            "missing_probability_assumption_count",
            "missing_evidence_count",
            "missing_counter_evidence_count",
            "missing_cost_review_count",
            "missing_settlement_rule_count",
            "missing_team_review_count",
            "missing_retrospective_plan_count",
            "average_completeness_score",
            "minimum_completeness_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        if type(self.rows) is not tuple:
            raise ValueError("rows must be a tuple")
        for row in self.rows:
            if type(row) is not ResearchDecisionPacketCompletenessRow:
                raise ValueError(
                    "rows must contain ResearchDecisionPacketCompletenessRow",
                )
            _require_hard_flags("row", row)
        if type(self.reason_code_counts) is not tuple:
            raise ValueError("reason_code_counts must be a tuple")
        for row in self.reason_code_counts:
            if type(row) is not ResearchDecisionPacketCompletenessReasonCodeCount:
                raise ValueError(
                    "reason_code_counts must contain "
                    "ResearchDecisionPacketCompletenessReasonCodeCount",
                )
            _require_hard_flags("reason code count", row)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_report_reason_codes(self.reason_codes),
        )
        _validate_report(self)
        _require_hard_flags("report", self)


def build_research_decision_packet_completeness_report(
    input_rows: list[ResearchDecisionPacketCompletenessInputRow]
    | tuple[ResearchDecisionPacketCompletenessInputRow, ...],
    *,
    config: ResearchDecisionPacketCompletenessConfig | None = None,
    generated_at: datetime,
) -> ResearchDecisionPacketCompletenessReport:
    cfg = config or ResearchDecisionPacketCompletenessConfig()
    if type(cfg) is not ResearchDecisionPacketCompletenessConfig:
        raise ValueError("config must be a ResearchDecisionPacketCompletenessConfig")
    _require_hard_flags("config", cfg)
    report_time = _as_utc("generated_at", generated_at)
    rows = _normalize_input_rows(input_rows, report_time)
    built_rows = tuple(_build_row(row, config=cfg, generated_at=report_time) for row in rows)
    ranked_rows = _ranked_rows(built_rows)
    packet_count = _count(len(ranked_rows))
    pass_packet_count = _count(
        sum(1 for row in ranked_rows if row.packet_status == STATUS_PASS),
    )
    watch_packet_count = _count(
        sum(1 for row in ranked_rows if row.packet_status == STATUS_WATCH),
    )
    blocked_packet_count = _count(
        sum(1 for row in ranked_rows if row.packet_status == STATUS_BLOCK),
    )
    reason_code_counts = _reason_code_counts(ranked_rows)
    reason_codes = tuple(row.reason_code for row in reason_code_counts)
    if not ranked_rows:
        reason_code_counts = (
            ResearchDecisionPacketCompletenessReasonCodeCount(
                reason_code=NO_INPUTS_REASON,
                count=ONE,
                packet_ratio=ONE,
            ),
        )
        reason_codes = (NO_INPUTS_REASON,)
    report_status = _report_status(
        has_inputs=bool(ranked_rows),
        blocked_packet_count=blocked_packet_count,
        watch_packet_count=watch_packet_count,
    )
    return ResearchDecisionPacketCompletenessReport(
        generated_at=report_time,
        config_version=cfg.config_version,
        report_status=report_status,
        next_step=NEXT_STEPS[report_status],
        packet_count=packet_count,
        pass_packet_count=pass_packet_count,
        watch_packet_count=watch_packet_count,
        blocked_packet_count=blocked_packet_count,
        stale_packet_count=_count(
            sum(1 for row in ranked_rows if STALE_PACKET_REASON in row.reason_codes),
        ),
        slow_team_review_count=_count(
            sum(1 for row in ranked_rows if SLOW_TEAM_REVIEW_REASON in row.reason_codes),
        ),
        missing_probability_assumption_count=_count(
            sum(
                1
                for row in ranked_rows
                if MISSING_PROBABILITY_ASSUMPTIONS_REASON in row.reason_codes
            ),
        ),
        missing_evidence_count=_count(
            sum(1 for row in ranked_rows if MISSING_EVIDENCE_REASON in row.reason_codes),
        ),
        missing_counter_evidence_count=_count(
            sum(
                1
                for row in ranked_rows
                if MISSING_COUNTER_EVIDENCE_REASON in row.reason_codes
            ),
        ),
        missing_cost_review_count=_count(
            sum(
                1
                for row in ranked_rows
                if MISSING_COST_REVIEW_REASON in row.reason_codes
            ),
        ),
        missing_settlement_rule_count=_count(
            sum(
                1
                for row in ranked_rows
                if MISSING_SETTLEMENT_RULES_REASON in row.reason_codes
            ),
        ),
        missing_team_review_count=_count(
            sum(
                1
                for row in ranked_rows
                if MISSING_TEAM_REVIEW_REASON in row.reason_codes
            ),
        ),
        missing_retrospective_plan_count=_count(
            sum(
                1
                for row in ranked_rows
                if MISSING_RETROSPECTIVE_PLAN_REASON in row.reason_codes
            ),
        ),
        average_completeness_score=_ratio(
            _sum_decimal(row.completeness_score for row in ranked_rows),
            packet_count,
        ),
        minimum_completeness_score=min(
            (row.completeness_score for row in ranked_rows),
            default=ZERO,
        ),
        rows=ranked_rows,
        reason_code_counts=reason_code_counts,
        reason_codes=reason_codes,
    )


def research_decision_packet_completeness_report_payload(
    report: ResearchDecisionPacketCompletenessReport,
) -> dict[str, Any]:
    if type(report) is not ResearchDecisionPacketCompletenessReport:
        raise ValueError(
            "report must be a ResearchDecisionPacketCompletenessReport",
        )
    _require_hard_flags("report", report)
    _reject_unsafe_payload("report", report)
    payload = _json_ready(report)
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    _require_hard_flags("payload", _DictFlags(payload))
    _reject_unsafe_payload("payload", payload)
    return payload


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


def _build_row(
    row: ResearchDecisionPacketCompletenessInputRow,
    *,
    config: ResearchDecisionPacketCompletenessConfig,
    generated_at: datetime,
) -> ResearchDecisionPacketCompletenessRow:
    packet_age_seconds = _datetime_delta_seconds(generated_at, row.prepared_at)
    team_review_lag_seconds = (
        None
        if row.reviewed_at is None
        else _datetime_delta_seconds(row.reviewed_at, row.prepared_at)
    )
    completeness_score = _completeness_score(row, config=config)
    reason_codes = _row_reason_codes(
        packet_age_seconds=packet_age_seconds,
        team_review_lag_seconds=team_review_lag_seconds,
        probability_assumption_count=row.probability_assumption_count,
        probability_assumption_quality=row.probability_assumption_quality,
        evidence_source_count=row.evidence_source_count,
        evidence_quality=row.evidence_quality,
        counter_evidence_count=row.counter_evidence_count,
        counter_evidence_quality=row.counter_evidence_quality,
        cost_review_count=row.cost_review_count,
        cost_review_quality=row.cost_review_quality,
        settlement_rule_count=row.settlement_rule_count,
        settlement_rule_quality=row.settlement_rule_quality,
        team_reviewer_count=row.team_reviewer_count,
        team_review_quality=row.team_review_quality,
        retrospective_plan_count=row.retrospective_plan_count,
        retrospective_plan_quality=row.retrospective_plan_quality,
        config=config,
    )
    packet_status = _row_status(reason_codes)
    return ResearchDecisionPacketCompletenessRow(
        packet_key=row.packet_key,
        condition_id=row.condition_id,
        packet_label=row.packet_label,
        prepared_at=row.prepared_at,
        reviewed_at=row.reviewed_at,
        packet_age_seconds=packet_age_seconds,
        team_review_lag_seconds=team_review_lag_seconds,
        probability_assumption_count=row.probability_assumption_count,
        probability_assumption_quality=row.probability_assumption_quality,
        evidence_source_count=row.evidence_source_count,
        evidence_quality=row.evidence_quality,
        counter_evidence_count=row.counter_evidence_count,
        counter_evidence_quality=row.counter_evidence_quality,
        cost_review_count=row.cost_review_count,
        cost_review_quality=row.cost_review_quality,
        settlement_rule_count=row.settlement_rule_count,
        settlement_rule_quality=row.settlement_rule_quality,
        team_reviewer_count=row.team_reviewer_count,
        team_review_quality=row.team_review_quality,
        retrospective_plan_count=row.retrospective_plan_count,
        retrospective_plan_quality=row.retrospective_plan_quality,
        completeness_score=completeness_score,
        packet_status=packet_status,
        redacted_packet_reference=_redacted_reference(row.public_packet_reference),
        reason_codes=reason_codes,
        validation_config=config,
    )


def _normalize_input_rows(
    rows: list[ResearchDecisionPacketCompletenessInputRow]
    | tuple[ResearchDecisionPacketCompletenessInputRow, ...],
    generated_at: datetime,
) -> tuple[ResearchDecisionPacketCompletenessInputRow, ...]:
    if type(rows) not in (list, tuple):
        raise ValueError("input rows must be a list or tuple")
    normalized = tuple(rows)
    seen: set[tuple[str, str]] = set()
    for row in normalized:
        if type(row) is not ResearchDecisionPacketCompletenessInputRow:
            raise ValueError(
                "input rows must contain ResearchDecisionPacketCompletenessInputRow",
            )
        _require_hard_flags("input row", row)
        if row.prepared_at > generated_at:
            raise ValueError("prepared_at must be on or before generated_at")
        key = (row.packet_key, row.condition_id)
        if key in seen:
            raise ValueError("input rows must not contain duplicate packet keys")
        seen.add(key)
    return normalized


def _row_reason_codes(
    *,
    packet_age_seconds: Decimal,
    team_review_lag_seconds: Decimal | None,
    probability_assumption_count: Decimal,
    probability_assumption_quality: Decimal,
    evidence_source_count: Decimal,
    evidence_quality: Decimal,
    counter_evidence_count: Decimal,
    counter_evidence_quality: Decimal,
    cost_review_count: Decimal,
    cost_review_quality: Decimal,
    settlement_rule_count: Decimal,
    settlement_rule_quality: Decimal,
    team_reviewer_count: Decimal,
    team_review_quality: Decimal,
    retrospective_plan_count: Decimal,
    retrospective_plan_quality: Decimal,
    config: ResearchDecisionPacketCompletenessConfig,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    if probability_assumption_count < config.min_probability_assumption_count:
        reason_codes.append(MISSING_PROBABILITY_ASSUMPTIONS_REASON)
    if evidence_source_count < config.min_evidence_source_count:
        reason_codes.append(MISSING_EVIDENCE_REASON)
    if counter_evidence_count < config.min_counter_evidence_count:
        reason_codes.append(MISSING_COUNTER_EVIDENCE_REASON)
    if cost_review_count < config.min_cost_review_count:
        reason_codes.append(MISSING_COST_REVIEW_REASON)
    if settlement_rule_count < config.min_settlement_rule_count:
        reason_codes.append(MISSING_SETTLEMENT_RULES_REASON)
    if (
        team_reviewer_count < config.min_team_reviewer_count
        or team_review_lag_seconds is None
    ):
        reason_codes.append(MISSING_TEAM_REVIEW_REASON)
    if retrospective_plan_count < config.min_retrospective_plan_count:
        reason_codes.append(MISSING_RETROSPECTIVE_PLAN_REASON)
    if (
        team_review_lag_seconds is not None
        and team_review_lag_seconds > config.max_team_review_lag_seconds
    ):
        reason_codes.append(SLOW_TEAM_REVIEW_REASON)
    if packet_age_seconds > config.max_packet_age_seconds:
        reason_codes.append(STALE_PACKET_REASON)
    weak_checks = (
        (probability_assumption_quality, WEAK_PROBABILITY_ASSUMPTIONS_REASON),
        (evidence_quality, WEAK_EVIDENCE_REASON),
        (counter_evidence_quality, WEAK_COUNTER_EVIDENCE_REASON),
        (cost_review_quality, WEAK_COST_REVIEW_REASON),
        (settlement_rule_quality, WEAK_SETTLEMENT_RULES_REASON),
        (team_review_quality, WEAK_TEAM_REVIEW_REASON),
        (retrospective_plan_quality, WEAK_RETROSPECTIVE_PLAN_REASON),
    )
    for quality, reason_code in weak_checks:
        if quality < config.min_section_quality:
            reason_codes.append(reason_code)
    if not reason_codes:
        reason_codes.append(PASS_REASON)
    return tuple(
        reason_code
        for reason_code in ROW_REASON_CODE_SEQUENCE
        if reason_code in reason_codes
    )


def _row_status(reason_codes: tuple[str, ...]) -> str:
    block_reasons = (
        MISSING_PROBABILITY_ASSUMPTIONS_REASON,
        MISSING_EVIDENCE_REASON,
        MISSING_COUNTER_EVIDENCE_REASON,
        MISSING_COST_REVIEW_REASON,
        MISSING_SETTLEMENT_RULES_REASON,
        MISSING_TEAM_REVIEW_REASON,
        MISSING_RETROSPECTIVE_PLAN_REASON,
    )
    if any(reason_code in reason_codes for reason_code in block_reasons):
        return STATUS_BLOCK
    if reason_codes == (PASS_REASON,):
        return STATUS_PASS
    return STATUS_WATCH


def _report_status(
    *,
    has_inputs: bool,
    blocked_packet_count: Decimal,
    watch_packet_count: Decimal,
) -> str:
    if not has_inputs or blocked_packet_count > ZERO:
        return STATUS_BLOCK
    if watch_packet_count > ZERO:
        return STATUS_WATCH
    return STATUS_PASS


def _completeness_score(
    row: ResearchDecisionPacketCompletenessInputRow,
    *,
    config: ResearchDecisionPacketCompletenessConfig,
) -> Decimal:
    section_scores = (
        _section_score(
            row.probability_assumption_count,
            config.min_probability_assumption_count,
            row.probability_assumption_quality,
        ),
        _section_score(
            row.evidence_source_count,
            config.min_evidence_source_count,
            row.evidence_quality,
        ),
        _section_score(
            row.counter_evidence_count,
            config.min_counter_evidence_count,
            row.counter_evidence_quality,
        ),
        _section_score(
            row.cost_review_count,
            config.min_cost_review_count,
            row.cost_review_quality,
        ),
        _section_score(
            row.settlement_rule_count,
            config.min_settlement_rule_count,
            row.settlement_rule_quality,
        ),
        _section_score(
            row.team_reviewer_count,
            config.min_team_reviewer_count,
            row.team_review_quality,
        ),
        _section_score(
            row.retrospective_plan_count,
            config.min_retrospective_plan_count,
            row.retrospective_plan_quality,
        ),
    )
    return _ratio(_sum_decimal(section_scores), _count(len(section_scores)))


def _section_score(value_count: Decimal, minimum_count: Decimal, quality: Decimal) -> Decimal:
    if value_count < minimum_count:
        return ZERO
    return quality


def _ranked_rows(
    rows: tuple[ResearchDecisionPacketCompletenessRow, ...],
) -> tuple[ResearchDecisionPacketCompletenessRow, ...]:
    return tuple(
        sorted(
            rows,
            key=lambda row: (
                _status_rank(row.packet_status),
                row.completeness_score,
                row.packet_label,
                row.packet_key,
            ),
        ),
    )


def _status_rank(value: str) -> int:
    return {STATUS_BLOCK: 0, STATUS_WATCH: 1, STATUS_PASS: 2}[value]


def _reason_code_counts(
    rows: tuple[ResearchDecisionPacketCompletenessRow, ...],
) -> tuple[ResearchDecisionPacketCompletenessReasonCodeCount, ...]:
    total = _count(len(rows))
    counts: dict[str, Decimal] = {}
    for row in rows:
        for reason_code in row.reason_codes:
            counts[reason_code] = counts.get(reason_code, ZERO) + ONE
    return tuple(
        ResearchDecisionPacketCompletenessReasonCodeCount(
            reason_code=reason_code,
            count=_count(counts[reason_code]),
            packet_ratio=_ratio(counts[reason_code], total),
        )
        for reason_code in REASON_CODE_SEQUENCE
        if reason_code in counts
    )


def _validate_row(
    row: ResearchDecisionPacketCompletenessRow,
    *,
    config: ResearchDecisionPacketCompletenessConfig | None,
) -> None:
    if config is None:
        config = ResearchDecisionPacketCompletenessConfig()
    if type(config) is not ResearchDecisionPacketCompletenessConfig:
        raise ValueError(
            "validation_config must be a ResearchDecisionPacketCompletenessConfig",
        )
    expected_reason_codes = _row_reason_codes(
        packet_age_seconds=row.packet_age_seconds,
        team_review_lag_seconds=row.team_review_lag_seconds,
        probability_assumption_count=row.probability_assumption_count,
        probability_assumption_quality=row.probability_assumption_quality,
        evidence_source_count=row.evidence_source_count,
        evidence_quality=row.evidence_quality,
        counter_evidence_count=row.counter_evidence_count,
        counter_evidence_quality=row.counter_evidence_quality,
        cost_review_count=row.cost_review_count,
        cost_review_quality=row.cost_review_quality,
        settlement_rule_count=row.settlement_rule_count,
        settlement_rule_quality=row.settlement_rule_quality,
        team_reviewer_count=row.team_reviewer_count,
        team_review_quality=row.team_review_quality,
        retrospective_plan_count=row.retrospective_plan_count,
        retrospective_plan_quality=row.retrospective_plan_quality,
        config=config,
    )
    if row.reason_codes != expected_reason_codes:
        raise ValueError("reason_codes must match row inputs")
    expected_score = _ratio(
        _sum_decimal(
            (
                _section_score(
                    row.probability_assumption_count,
                    config.min_probability_assumption_count,
                    row.probability_assumption_quality,
                ),
                _section_score(
                    row.evidence_source_count,
                    config.min_evidence_source_count,
                    row.evidence_quality,
                ),
                _section_score(
                    row.counter_evidence_count,
                    config.min_counter_evidence_count,
                    row.counter_evidence_quality,
                ),
                _section_score(
                    row.cost_review_count,
                    config.min_cost_review_count,
                    row.cost_review_quality,
                ),
                _section_score(
                    row.settlement_rule_count,
                    config.min_settlement_rule_count,
                    row.settlement_rule_quality,
                ),
                _section_score(
                    row.team_reviewer_count,
                    config.min_team_reviewer_count,
                    row.team_review_quality,
                ),
                _section_score(
                    row.retrospective_plan_count,
                    config.min_retrospective_plan_count,
                    row.retrospective_plan_quality,
                ),
            ),
        ),
        _count(7),
    )
    if row.completeness_score != expected_score:
        raise ValueError("completeness_score must match row inputs")
    if row.reviewed_at is None:
        expected_lag = None
    else:
        expected_lag = _datetime_delta_seconds(row.reviewed_at, row.prepared_at)
    if row.team_review_lag_seconds != expected_lag:
        raise ValueError(
            "team_review_lag_seconds must match reviewed_at and prepared_at",
        )
    if row.packet_status != _row_status(row.reason_codes):
        raise ValueError("packet_status must match reason_codes")
    if not _is_redacted_reference(row.redacted_packet_reference):
        raise ValueError("redacted_packet_reference must be redacted or public")


def _validate_report(report: ResearchDecisionPacketCompletenessReport) -> None:
    if report.next_step != NEXT_STEPS[report.report_status]:
        raise ValueError("next_step must match report_status")
    if report.rows != _ranked_rows(report.rows):
        raise ValueError("rows must be sorted deterministically")
    if report.packet_count != _count(len(report.rows)):
        raise ValueError("packet_count must match rows")
    expected_pass = _count(
        sum(1 for row in report.rows if row.packet_status == STATUS_PASS),
    )
    if report.pass_packet_count != expected_pass:
        raise ValueError("pass_packet_count must match rows")
    expected_watch = _count(
        sum(1 for row in report.rows if row.packet_status == STATUS_WATCH),
    )
    if report.watch_packet_count != expected_watch:
        raise ValueError("watch_packet_count must match rows")
    expected_blocked = _count(
        sum(1 for row in report.rows if row.packet_status == STATUS_BLOCK),
    )
    if report.blocked_packet_count != expected_blocked:
        raise ValueError("blocked_packet_count must match rows")
    if report.stale_packet_count != _count(
        sum(1 for row in report.rows if STALE_PACKET_REASON in row.reason_codes),
    ):
        raise ValueError("stale_packet_count must match rows")
    if report.slow_team_review_count != _count(
        sum(1 for row in report.rows if SLOW_TEAM_REVIEW_REASON in row.reason_codes),
    ):
        raise ValueError("slow_team_review_count must match rows")
    if report.missing_probability_assumption_count != _count(
        sum(
            1
            for row in report.rows
            if MISSING_PROBABILITY_ASSUMPTIONS_REASON in row.reason_codes
        ),
    ):
        raise ValueError("missing_probability_assumption_count must match rows")
    if report.missing_evidence_count != _count(
        sum(1 for row in report.rows if MISSING_EVIDENCE_REASON in row.reason_codes),
    ):
        raise ValueError("missing_evidence_count must match rows")
    if report.missing_counter_evidence_count != _count(
        sum(
            1
            for row in report.rows
            if MISSING_COUNTER_EVIDENCE_REASON in row.reason_codes
        ),
    ):
        raise ValueError("missing_counter_evidence_count must match rows")
    if report.missing_cost_review_count != _count(
        sum(1 for row in report.rows if MISSING_COST_REVIEW_REASON in row.reason_codes),
    ):
        raise ValueError("missing_cost_review_count must match rows")
    if report.missing_settlement_rule_count != _count(
        sum(
            1
            for row in report.rows
            if MISSING_SETTLEMENT_RULES_REASON in row.reason_codes
        ),
    ):
        raise ValueError("missing_settlement_rule_count must match rows")
    if report.missing_team_review_count != _count(
        sum(1 for row in report.rows if MISSING_TEAM_REVIEW_REASON in row.reason_codes),
    ):
        raise ValueError("missing_team_review_count must match rows")
    if report.missing_retrospective_plan_count != _count(
        sum(
            1
            for row in report.rows
            if MISSING_RETROSPECTIVE_PLAN_REASON in row.reason_codes
        ),
    ):
        raise ValueError("missing_retrospective_plan_count must match rows")
    if report.average_completeness_score != _ratio(
        _sum_decimal(row.completeness_score for row in report.rows),
        report.packet_count,
    ):
        raise ValueError("average_completeness_score must match rows")
    expected_minimum_score = min(
        (row.completeness_score for row in report.rows),
        default=ZERO,
    )
    if report.minimum_completeness_score != expected_minimum_score:
        raise ValueError("minimum_completeness_score must match rows")
    expected_counts = _reason_code_counts(report.rows)
    expected_codes = tuple(row.reason_code for row in expected_counts)
    if not report.rows:
        expected_counts = (
            ResearchDecisionPacketCompletenessReasonCodeCount(
                reason_code=NO_INPUTS_REASON,
                count=ONE,
                packet_ratio=ONE,
            ),
        )
        expected_codes = (NO_INPUTS_REASON,)
    if report.reason_code_counts != expected_counts:
        raise ValueError("reason_code_counts must match rows")
    if report.reason_codes != expected_codes:
        raise ValueError("reason_codes must match reason_code_counts")
    expected_status = _report_status(
        has_inputs=bool(report.rows),
        blocked_packet_count=report.blocked_packet_count,
        watch_packet_count=report.watch_packet_count,
    )
    if report.report_status != expected_status:
        raise ValueError("report_status must match rows")


def _normalize_row_reason_codes(value: tuple[str, ...]) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ValueError("reason_codes must be a tuple")
    for reason_code in value:
        _require_reason_code("reason_codes", reason_code, ROW_REASON_CODE_SEQUENCE)
    normalized = tuple(
        reason_code for reason_code in ROW_REASON_CODE_SEQUENCE if reason_code in value
    )
    if normalized != value:
        raise ValueError("reason_codes must be unique and sorted")
    if PASS_REASON in value and len(value) != 1:
        raise ValueError("reason_codes cannot mix pass with completeness concerns")
    return normalized


def _normalize_report_reason_codes(value: tuple[str, ...]) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ValueError("reason_codes must be a tuple")
    for reason_code in value:
        _require_reason_code("reason_codes", reason_code, REASON_CODE_SEQUENCE)
    normalized = tuple(
        reason_code for reason_code in REASON_CODE_SEQUENCE if reason_code in value
    )
    if normalized != value:
        raise ValueError("reason_codes must be unique and sorted")
    return normalized


def _require_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in (STATUS_PASS, STATUS_WATCH, STATUS_BLOCK):
        raise ValueError(f"{field_name} must be a supported status")


def _require_reason_code(
    field_name: str,
    value: object,
    allowed_values: tuple[str, ...],
) -> None:
    if type(value) is not str or value not in allowed_values:
        raise ValueError(f"{field_name} must be a supported reason code")


def _require_public_string(field_name: str, value: object) -> str:
    if type(value) is not str or not value.strip() or value != value.strip():
        raise ValueError(f"{field_name} must be a non-empty string")
    _reject_unsafe_text(field_name, value)
    return value


def _require_reference(field_name: str, value: object) -> str:
    if type(value) is not str or not value.strip():
        raise ValueError(f"{field_name} must be a non-empty string")
    return value


def _require_redacted_reference(field_name: str, value: object) -> str:
    if type(value) is not str or not value.strip():
        raise ValueError(f"{field_name} must be a non-empty string")
    if not _is_redacted_reference(value):
        raise ValueError(f"{field_name} must be redacted or public")
    return value


def _is_redacted_reference(value: str) -> bool:
    if value.startswith("sha256:") and len(value) == 19:
        return True
    lowered = value.lower()
    return all(fragment in lowered for fragment in ("public",)) and any(
        fragment in lowered for fragment in _PUBLIC_REFERENCE_FRAGMENTS
    )


def _redacted_reference(value: str) -> str:
    if _is_redacted_reference(value):
        return value
    return f"sha256:{sha256(value.encode('utf-8')).hexdigest()[:12]}"


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if getattr(value, field_name, None) is not True:
            raise ValueError(f"{field_name} must be True for {label}")


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _optional_utc(field_name: str, value: object) -> datetime | None:
    if value is None:
        return None
    return _as_utc(field_name, value)


def _require_finite_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return _quantize(value)


def _require_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_finite_decimal(field_name, value)
    if decimal_value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return decimal_value


def _require_optional_nonnegative_decimal(
    field_name: str,
    value: object,
) -> Decimal | None:
    if value is None:
        return None
    return _require_nonnegative_decimal(field_name, value)


def _require_nonnegative_count_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_nonnegative_decimal(field_name, value)
    if decimal_value != decimal_value.to_integral_value():
        raise ValueError(f"{field_name} must be a whole-number Decimal")
    return _quantize(decimal_value)


def _require_ratio_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_nonnegative_decimal(field_name, value)
    if decimal_value > ONE:
        raise ValueError(f"{field_name} must be in the closed unit interval")
    return decimal_value


def _datetime_delta_seconds(later: datetime, earlier: datetime) -> Decimal:
    delta = later - earlier
    total_microseconds = (
        Decimal(delta.days * 86400 + delta.seconds) * MICROSECONDS_PER_SECOND
        + Decimal(delta.microseconds)
    )
    return _quantize(total_microseconds / MICROSECONDS_PER_SECOND)


def _quantize(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(QUANT)


def _count(value: int | Decimal) -> Decimal:
    if type(value) is int:
        return _quantize(Decimal(value))
    if type(value) is Decimal:
        return _quantize(value)
    raise ValueError("count value must be an int or Decimal")


def _sum_decimal(values: object) -> Decimal:
    total = ZERO
    for value in values:  # type: ignore[union-attr]
        if type(value) is not Decimal:
            raise ValueError("sum values must be Decimal")
        total += value
    return _quantize(total)


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return (numerator / denominator).quantize(QUANT)


def _reject_unsafe_payload(label: str, value: object, path: str = "") -> None:
    if is_dataclass(value) and not isinstance(value, type):
        _reject_unsafe_payload(label, asdict(value), path)
        return
    if type(value) is str:
        _reject_unsafe_text(path or label, value)
        return
    if isinstance(value, Decimal):
        if type(value) is not Decimal or not value.is_finite():
            raise ValueError(f"{path or label} must be finite Decimal")
        return
    if isinstance(value, datetime):
        _as_utc(path or label, value)
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
            if key in {"paper_only", "report_only", "readonly"} and item is not True:
                raise ValueError(f"{nested_path} must be True")
            _reject_unsafe_text(nested_path, key)
            _reject_unsafe_payload(label, item, nested_path)
        return
    if isinstance(value, (list, tuple)):
        for index, item in enumerate(value):
            nested_path = f"{path}[{index}]" if path else f"{label}[{index}]"
            _reject_unsafe_payload(label, item, nested_path)
        return
    raise ValueError("value is not JSON serializable")


def _reject_unsafe_text(field_name: str, value: str) -> None:
    lowered = value.lower()
    unsafe_fragments = (
        _join_parts("au", "th"),
        _join_parts("cred", "ential"),
        _join_parts("hid", "den"),
        _join_parts("wal", "let"),
        _join_parts("acc", "ount"),
        _join_parts("bro", "ker"),
        _join_parts("ord", "er"),
        _join_parts("can", "cel"),
        _join_parts("repl", "ace"),
        "sign",
        _join_parts("priv", "ate"),
        _join_parts("api", "_key"),
        _join_parts("sec", "ret"),
        _join_parts("tok", "en"),
        _join_parts("cli", "ent"),
        _join_parts("data", "base"),
        _join_parts("net", "work"),
        _join_parts("li", "ve"),
        _join_parts("b", "uy"),
        _join_parts("se", "ll"),
        _join_parts("recomm", "end"),
        _join_parts("tra", "de"),
        _join_parts("pos", "ition"),
        _join_parts("st", "ake"),
        _join_parts("b", "et"),
    )
    if any(fragment in lowered for fragment in unsafe_fragments):
        raise ValueError(f"{field_name} has unsafe value")


def _join_parts(*parts: str) -> str:
    return "".join(parts)


def _json_ready(value: Any) -> Any:
    if value is None:
        return None
    if is_dataclass(value) and not isinstance(value, type):
        return _json_ready(asdict(value))
    if isinstance(value, Decimal):
        if type(value) is not Decimal or not value.is_finite():
            raise ValueError("JSON Decimal value must be finite")
        return str(value)
    if isinstance(value, datetime):
        return _as_utc("datetime", value).isoformat()
    if isinstance(value, float):
        raise ValueError("JSON value must not be a float")
    if type(value) is int:
        raise ValueError("JSON numeric value must use Decimal")
    if type(value) in (str, bool):
        return value
    if isinstance(value, dict):
        ready: dict[str, Any] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            ready[key] = _json_ready(item)
        return ready
    if isinstance(value, (list, tuple)):
        return [_json_ready(item) for item in value]
    raise ValueError("value is not JSON serializable")


__all__ = (
    "DEFAULT_RESEARCH_DECISION_PACKET_COMPLETENESS_CONFIG_VERSION",
    "ResearchDecisionPacketCompletenessConfig",
    "ResearchDecisionPacketCompletenessInputRow",
    "ResearchDecisionPacketCompletenessReasonCodeCount",
    "ResearchDecisionPacketCompletenessReport",
    "ResearchDecisionPacketCompletenessRow",
    "build_research_decision_packet_completeness_report",
    "research_decision_packet_completeness_report_payload",
)
