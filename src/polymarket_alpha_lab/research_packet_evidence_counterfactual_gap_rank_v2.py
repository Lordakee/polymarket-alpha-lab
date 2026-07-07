"""Phase 1 counterfactual evidence gap rank report for research packets."""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, is_dataclass
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from typing import Any

from polymarket_alpha_lab.team_paper_guard import (
    json_ready_no_floats,
    reject_unsafe_surface_fields,
    require_paper_only_flags,
)


DEFAULT_RESEARCH_PACKET_EVIDENCE_COUNTERFACTUAL_GAP_RANK_V2_CONFIG_VERSION = (
    "research-packet-evidence-counterfactual-gap-rank-v2-v0"
)

COUNT_QUANTUM = Decimal("1")
SCORE_QUANTUM = Decimal("0.000001")
ZERO_COUNT = Decimal("0")
ZERO_SCORE = Decimal("0.000000")
ONE_SCORE = Decimal("1.000000")
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)

PASS_STATUS = "pass"
WATCH_STATUS = "watch"
BLOCKED_STATUS = "blocked"
STATUSES = (PASS_STATUS, WATCH_STATUS, BLOCKED_STATUS)

BLOCKED_REASON = "counterfactual_gap_rank_status_blocked"
WATCH_REASON = "counterfactual_gap_rank_status_watch"
PASS_REASON = "counterfactual_gap_rank_status_pass"
MISSING_COUNTERFACTUAL_EVIDENCE_REASON = "missing_counterfactual_evidence"
HIGH_EVENT_CATEGORY_PRIORITY_REASON = "high_event_category_priority"
HIGH_CATALYST_URGENCY_REASON = "high_catalyst_urgency"
THIN_SOURCE_COVERAGE_REASON = "thin_source_coverage"
CONTRADICTION_SEVERITY_REASON = "contradiction_severity"
RESOLUTION_RULE_SENSITIVE_REASON = "resolution_rule_sensitive"

STATUS_REASON_CODES = (BLOCKED_REASON, WATCH_REASON, PASS_REASON)
DRIVER_REASON_CODES = (
    MISSING_COUNTERFACTUAL_EVIDENCE_REASON,
    HIGH_EVENT_CATEGORY_PRIORITY_REASON,
    HIGH_CATALYST_URGENCY_REASON,
    THIN_SOURCE_COVERAGE_REASON,
    CONTRADICTION_SEVERITY_REASON,
    RESOLUTION_RULE_SENSITIVE_REASON,
)
REASON_CODES = (*STATUS_REASON_CODES, *DRIVER_REASON_CODES)

RECOMMENDED_NEXT_STEPS = {
    BLOCKED_STATUS: "collect_counterfactual_evidence_before_using_packet",
    WATCH_STATUS: "review_counterfactual_evidence_before_using_packet",
    PASS_STATUS: "continue_using_counterfactual_evidence_rank",
}
RECOMMENDED_RESEARCH_ACTIONS = {
    BLOCKED_STATUS: "collect_counterfactual_evidence_first",
    WATCH_STATUS: "review_counterfactual_evidence_coverage",
    PASS_STATUS: "continue_packet_research",
}
STATUS_REASON_BY_STATUS = {
    BLOCKED_STATUS: BLOCKED_REASON,
    WATCH_STATUS: WATCH_REASON,
    PASS_STATUS: PASS_REASON,
}

EVENT_CATEGORY_PRIORITY_SCORES = {
    "politics": Decimal("1.000000"),
    "macro": Decimal("0.900000"),
    "crypto": Decimal("0.850000"),
    "sports": Decimal("0.650000"),
    "other": Decimal("0.250000"),
}


__all__ = (
    "DEFAULT_RESEARCH_PACKET_EVIDENCE_COUNTERFACTUAL_GAP_RANK_V2_CONFIG_VERSION",
    "ResearchPacketCounterfactualEvidenceGapRankV2Config",
    "ResearchPacketCounterfactualEvidenceGapInput",
    "ResearchPacketCounterfactualEvidenceGapRankV2Row",
    "ResearchPacketCounterfactualEvidenceGapRankV2Report",
    "build_research_packet_evidence_counterfactual_gap_rank_v2_report",
    "research_packet_evidence_counterfactual_gap_rank_v2_payload",
)


@dataclass(frozen=True)
class ResearchPacketCounterfactualEvidenceGapRankV2Config:
    config_version: str = (
        DEFAULT_RESEARCH_PACKET_EVIDENCE_COUNTERFACTUAL_GAP_RANK_V2_CONFIG_VERSION
    )
    target_counterfactual_evidence_count: Decimal = Decimal("2.000000")
    counterfactual_gap_weight: Decimal = Decimal("0.300000")
    event_category_priority_weight: Decimal = Decimal("0.150000")
    catalyst_urgency_weight: Decimal = Decimal("0.200000")
    source_coverage_gap_weight: Decimal = Decimal("0.150000")
    contradiction_severity_weight: Decimal = Decimal("0.100000")
    resolution_rule_sensitivity_weight: Decimal = Decimal("0.100000")
    high_event_category_priority_threshold: Decimal = Decimal("0.900000")
    high_catalyst_urgency_threshold: Decimal = Decimal("0.750000")
    thin_source_coverage_threshold: Decimal = Decimal("0.500000")
    contradiction_severity_threshold: Decimal = Decimal("0.200000")
    resolution_rule_sensitivity_threshold: Decimal = Decimal("0.500000")
    watch_priority_score_threshold: Decimal = Decimal("0.250000")
    blocked_priority_score_threshold: Decimal = Decimal("0.800000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("config_version", self.config_version)
        object.__setattr__(
            self,
            "target_counterfactual_evidence_count",
            _normalize_positive_driver_decimal(
                "target_counterfactual_evidence_count",
                self.target_counterfactual_evidence_count,
            ),
        )
        for field_name in (
            "counterfactual_gap_weight",
            "event_category_priority_weight",
            "catalyst_urgency_weight",
            "source_coverage_gap_weight",
            "contradiction_severity_weight",
            "resolution_rule_sensitivity_weight",
            "high_event_category_priority_threshold",
            "high_catalyst_urgency_threshold",
            "thin_source_coverage_threshold",
            "contradiction_severity_threshold",
            "resolution_rule_sensitivity_threshold",
            "watch_priority_score_threshold",
            "blocked_priority_score_threshold",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_score(field_name, getattr(self, field_name)),
            )
        _require_score_total(
            self.counterfactual_gap_weight,
            self.event_category_priority_weight,
            self.catalyst_urgency_weight,
            self.source_coverage_gap_weight,
            self.contradiction_severity_weight,
            self.resolution_rule_sensitivity_weight,
        )
        if self.watch_priority_score_threshold > self.blocked_priority_score_threshold:
            raise ValueError(
                "watch_priority_score_threshold must not exceed "
                "blocked_priority_score_threshold",
            )
        require_paper_only_flags("ResearchPacketCounterfactualEvidenceGapRankV2Config", self)


@dataclass(frozen=True)
class ResearchPacketCounterfactualEvidenceGapInput:
    packet_ref: str
    question_ref: str
    event_category: str
    counterfactual_evidence_count: Decimal
    catalyst_urgency_score: Decimal
    source_coverage_score: Decimal
    contradiction_severity_score: Decimal
    resolution_rule_sensitivity_score: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("packet_ref", self.packet_ref)
        _require_canonical_string("question_ref", self.question_ref)
        _require_member(
            "event_category",
            self.event_category,
            tuple(EVENT_CATEGORY_PRIORITY_SCORES),
        )
        object.__setattr__(
            self,
            "counterfactual_evidence_count",
            _normalize_counterfactual_evidence_count(
                "counterfactual_evidence_count",
                self.counterfactual_evidence_count,
            ),
        )
        for field_name in (
            "catalyst_urgency_score",
            "source_coverage_score",
            "contradiction_severity_score",
            "resolution_rule_sensitivity_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_score(field_name, getattr(self, field_name)),
            )
        require_paper_only_flags("ResearchPacketCounterfactualEvidenceGapInput", self)


@dataclass(frozen=True)
class ResearchPacketCounterfactualEvidenceGapRankV2Row:
    priority_rank: Decimal
    packet_ref: str
    question_ref: str
    event_category: str
    counterfactual_evidence_count: Decimal
    catalyst_urgency_score: Decimal
    source_coverage_score: Decimal
    contradiction_severity_score: Decimal
    resolution_rule_sensitivity_score: Decimal
    counterfactual_gap_score: Decimal
    event_category_priority_score: Decimal
    source_coverage_gap_score: Decimal
    priority_score: Decimal
    gap_status: str
    recommended_research_action: str
    reason_codes: tuple[str, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "priority_rank",
            _normalize_positive_count("priority_rank", self.priority_rank),
        )
        _require_canonical_string("packet_ref", self.packet_ref)
        _require_canonical_string("question_ref", self.question_ref)
        _require_member(
            "event_category",
            self.event_category,
            tuple(EVENT_CATEGORY_PRIORITY_SCORES),
        )
        object.__setattr__(
            self,
            "counterfactual_evidence_count",
            _normalize_counterfactual_evidence_count(
                "counterfactual_evidence_count",
                self.counterfactual_evidence_count,
            ),
        )
        for field_name in (
            "catalyst_urgency_score",
            "source_coverage_score",
            "contradiction_severity_score",
            "resolution_rule_sensitivity_score",
            "counterfactual_gap_score",
            "event_category_priority_score",
            "source_coverage_gap_score",
            "priority_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_score(field_name, getattr(self, field_name)),
            )
        _require_member("gap_status", self.gap_status, STATUSES)
        _require_member(
            "recommended_research_action",
            self.recommended_research_action,
            tuple(RECOMMENDED_RESEARCH_ACTIONS.values()),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        require_paper_only_flags("ResearchPacketCounterfactualEvidenceGapRankV2Row", self)
        reject_unsafe_surface_fields(
            "research packet counterfactual evidence gap rank row",
            self,
        )
        expected_digest = _row_derived_validation_digest(self)
        if self.derived_validation_digest == "":
            object.__setattr__(self, "derived_validation_digest", expected_digest)
        else:
            _require_sha256_digest("derived_validation_digest", self.derived_validation_digest)
            if self.derived_validation_digest != expected_digest:
                raise ValueError("derived_validation_digest must match row fields")
        _validate_row(self)


@dataclass(frozen=True)
class ResearchPacketCounterfactualEvidenceGapRankV2Report:
    config_version: str
    input_count: Decimal
    blocked_count: Decimal
    watch_count: Decimal
    pass_count: Decimal
    missing_counterfactual_evidence_count: Decimal
    high_event_category_priority_count: Decimal
    high_catalyst_urgency_count: Decimal
    thin_source_coverage_count: Decimal
    contradiction_severity_count: Decimal
    resolution_rule_sensitive_count: Decimal
    highest_priority_score: Decimal
    status: str
    recommended_next_step: str
    reason_codes: tuple[str, ...]
    rows: tuple[ResearchPacketCounterfactualEvidenceGapRankV2Row, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("config_version", self.config_version)
        for field_name in (
            "input_count",
            "blocked_count",
            "watch_count",
            "pass_count",
            "missing_counterfactual_evidence_count",
            "high_event_category_priority_count",
            "high_catalyst_urgency_count",
            "thin_source_coverage_count",
            "contradiction_severity_count",
            "resolution_rule_sensitive_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_count(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "highest_priority_score",
            _normalize_score("highest_priority_score", self.highest_priority_score),
        )
        _require_member("status", self.status, STATUSES)
        _require_member(
            "recommended_next_step",
            self.recommended_next_step,
            tuple(RECOMMENDED_NEXT_STEPS.values()),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        require_paper_only_flags("ResearchPacketCounterfactualEvidenceGapRankV2Report", self)
        reject_unsafe_surface_fields(
            "research packet counterfactual evidence gap rank report",
            self,
        )
        expected_digest = _report_derived_validation_digest(self)
        if self.derived_validation_digest == "":
            object.__setattr__(self, "derived_validation_digest", expected_digest)
        else:
            _require_sha256_digest("derived_validation_digest", self.derived_validation_digest)
            if self.derived_validation_digest != expected_digest:
                raise ValueError("derived_validation_digest must match report fields")
        _validate_report(self)


def build_research_packet_evidence_counterfactual_gap_rank_v2_report(
    inputs: list[ResearchPacketCounterfactualEvidenceGapInput]
    | tuple[ResearchPacketCounterfactualEvidenceGapInput, ...],
    *,
    config: ResearchPacketCounterfactualEvidenceGapRankV2Config,
) -> ResearchPacketCounterfactualEvidenceGapRankV2Report:
    if type(config) is not ResearchPacketCounterfactualEvidenceGapRankV2Config:
        raise ValueError(
            "config must be a ResearchPacketCounterfactualEvidenceGapRankV2Config",
        )
    require_paper_only_flags("config", config)
    normalized_inputs = _normalize_inputs(inputs)
    ranked_rows = tuple(
        sorted(
            (_row_for_input(item, config=config) for item in normalized_inputs),
            key=_row_sort_key,
        ),
    )
    rows = tuple(
        _row_with_priority_rank(row, _count(index + 1))
        for index, row in enumerate(ranked_rows)
    )
    status = _report_status(rows)
    return ResearchPacketCounterfactualEvidenceGapRankV2Report(
        config_version=config.config_version,
        input_count=_count(len(normalized_inputs)),
        blocked_count=_status_count(rows, BLOCKED_STATUS),
        watch_count=_status_count(rows, WATCH_STATUS),
        pass_count=_status_count(rows, PASS_STATUS),
        missing_counterfactual_evidence_count=_reason_count(
            rows,
            MISSING_COUNTERFACTUAL_EVIDENCE_REASON,
        ),
        high_event_category_priority_count=_reason_count(
            rows,
            HIGH_EVENT_CATEGORY_PRIORITY_REASON,
        ),
        high_catalyst_urgency_count=_reason_count(rows, HIGH_CATALYST_URGENCY_REASON),
        thin_source_coverage_count=_reason_count(rows, THIN_SOURCE_COVERAGE_REASON),
        contradiction_severity_count=_reason_count(rows, CONTRADICTION_SEVERITY_REASON),
        resolution_rule_sensitive_count=_reason_count(
            rows,
            RESOLUTION_RULE_SENSITIVE_REASON,
        ),
        highest_priority_score=max((row.priority_score for row in rows), default=ZERO_SCORE),
        status=status,
        recommended_next_step=RECOMMENDED_NEXT_STEPS[status],
        reason_codes=_report_reason_codes(rows),
        rows=rows,
    )


def research_packet_evidence_counterfactual_gap_rank_v2_payload(
    report: ResearchPacketCounterfactualEvidenceGapRankV2Report,
) -> dict[str, Any]:
    if type(report) is not ResearchPacketCounterfactualEvidenceGapRankV2Report:
        raise ValueError(
            "report must be a ResearchPacketCounterfactualEvidenceGapRankV2Report",
        )
    require_paper_only_flags("report", report)
    reject_unsafe_surface_fields(
        "research packet counterfactual evidence gap rank report",
        report,
    )
    if report.derived_validation_digest != _report_derived_validation_digest(report):
        raise ValueError("derived_validation_digest must match report fields")
    payload = json_ready_no_floats(report)
    if type(payload) is not dict:
        raise ValueError("payload must be a dict")
    return payload


def _row_for_input(
    item: ResearchPacketCounterfactualEvidenceGapInput,
    *,
    config: ResearchPacketCounterfactualEvidenceGapRankV2Config,
) -> ResearchPacketCounterfactualEvidenceGapRankV2Row:
    counterfactual_gap_score = _counterfactual_gap_score(
        item.counterfactual_evidence_count,
        config.target_counterfactual_evidence_count,
    )
    event_category_priority_score = EVENT_CATEGORY_PRIORITY_SCORES[item.event_category]
    source_coverage_gap_score = _clamp_score(ONE_SCORE - item.source_coverage_score)
    priority_score = _priority_score(
        counterfactual_gap_score=counterfactual_gap_score,
        event_category_priority_score=event_category_priority_score,
        catalyst_urgency_score=item.catalyst_urgency_score,
        source_coverage_gap_score=source_coverage_gap_score,
        contradiction_severity_score=item.contradiction_severity_score,
        resolution_rule_sensitivity_score=item.resolution_rule_sensitivity_score,
        config=config,
    )
    gap_status = _gap_status(priority_score, config=config)
    reason_codes = _row_reason_codes(
        gap_status=gap_status,
        counterfactual_evidence_count=item.counterfactual_evidence_count,
        event_category_priority_score=event_category_priority_score,
        catalyst_urgency_score=item.catalyst_urgency_score,
        source_coverage_score=item.source_coverage_score,
        contradiction_severity_score=item.contradiction_severity_score,
        resolution_rule_sensitivity_score=item.resolution_rule_sensitivity_score,
        config=config,
    )
    return ResearchPacketCounterfactualEvidenceGapRankV2Row(
        priority_rank=_count(1),
        packet_ref=item.packet_ref,
        question_ref=item.question_ref,
        event_category=item.event_category,
        counterfactual_evidence_count=item.counterfactual_evidence_count,
        catalyst_urgency_score=item.catalyst_urgency_score,
        source_coverage_score=item.source_coverage_score,
        contradiction_severity_score=item.contradiction_severity_score,
        resolution_rule_sensitivity_score=item.resolution_rule_sensitivity_score,
        counterfactual_gap_score=counterfactual_gap_score,
        event_category_priority_score=event_category_priority_score,
        source_coverage_gap_score=source_coverage_gap_score,
        priority_score=priority_score,
        gap_status=gap_status,
        recommended_research_action=RECOMMENDED_RESEARCH_ACTIONS[gap_status],
        reason_codes=reason_codes,
    )


def _row_with_priority_rank(
    row: ResearchPacketCounterfactualEvidenceGapRankV2Row,
    priority_rank: Decimal,
) -> ResearchPacketCounterfactualEvidenceGapRankV2Row:
    return ResearchPacketCounterfactualEvidenceGapRankV2Row(
        priority_rank=priority_rank,
        packet_ref=row.packet_ref,
        question_ref=row.question_ref,
        event_category=row.event_category,
        counterfactual_evidence_count=row.counterfactual_evidence_count,
        catalyst_urgency_score=row.catalyst_urgency_score,
        source_coverage_score=row.source_coverage_score,
        contradiction_severity_score=row.contradiction_severity_score,
        resolution_rule_sensitivity_score=row.resolution_rule_sensitivity_score,
        counterfactual_gap_score=row.counterfactual_gap_score,
        event_category_priority_score=row.event_category_priority_score,
        source_coverage_gap_score=row.source_coverage_gap_score,
        priority_score=row.priority_score,
        gap_status=row.gap_status,
        recommended_research_action=row.recommended_research_action,
        reason_codes=row.reason_codes,
    )


def _counterfactual_gap_score(
    counterfactual_evidence_count: Decimal,
    target_counterfactual_evidence_count: Decimal,
) -> Decimal:
    if counterfactual_evidence_count >= target_counterfactual_evidence_count:
        return ZERO_SCORE
    with localcontext(DECIMAL_CONTEXT):
        return _clamp_score(
            (target_counterfactual_evidence_count - counterfactual_evidence_count)
            / target_counterfactual_evidence_count,
        )


def _priority_score(
    *,
    counterfactual_gap_score: Decimal,
    event_category_priority_score: Decimal,
    catalyst_urgency_score: Decimal,
    source_coverage_gap_score: Decimal,
    contradiction_severity_score: Decimal,
    resolution_rule_sensitivity_score: Decimal,
    config: ResearchPacketCounterfactualEvidenceGapRankV2Config,
) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return _clamp_score(
            counterfactual_gap_score * config.counterfactual_gap_weight
            + event_category_priority_score * config.event_category_priority_weight
            + catalyst_urgency_score * config.catalyst_urgency_weight
            + source_coverage_gap_score * config.source_coverage_gap_weight
            + contradiction_severity_score * config.contradiction_severity_weight
            + resolution_rule_sensitivity_score * config.resolution_rule_sensitivity_weight,
        )


def _gap_status(
    priority_score: Decimal,
    *,
    config: ResearchPacketCounterfactualEvidenceGapRankV2Config,
) -> str:
    if priority_score >= config.blocked_priority_score_threshold:
        return BLOCKED_STATUS
    if priority_score >= config.watch_priority_score_threshold:
        return WATCH_STATUS
    return PASS_STATUS


def _row_reason_codes(
    *,
    gap_status: str,
    counterfactual_evidence_count: Decimal,
    event_category_priority_score: Decimal,
    catalyst_urgency_score: Decimal,
    source_coverage_score: Decimal,
    contradiction_severity_score: Decimal,
    resolution_rule_sensitivity_score: Decimal,
    config: ResearchPacketCounterfactualEvidenceGapRankV2Config,
) -> tuple[str, ...]:
    present = {STATUS_REASON_BY_STATUS[gap_status]}
    if counterfactual_evidence_count < config.target_counterfactual_evidence_count:
        present.add(MISSING_COUNTERFACTUAL_EVIDENCE_REASON)
    if event_category_priority_score >= config.high_event_category_priority_threshold:
        present.add(HIGH_EVENT_CATEGORY_PRIORITY_REASON)
    if catalyst_urgency_score >= config.high_catalyst_urgency_threshold:
        present.add(HIGH_CATALYST_URGENCY_REASON)
    if source_coverage_score <= config.thin_source_coverage_threshold:
        present.add(THIN_SOURCE_COVERAGE_REASON)
    if contradiction_severity_score >= config.contradiction_severity_threshold:
        present.add(CONTRADICTION_SEVERITY_REASON)
    if resolution_rule_sensitivity_score >= config.resolution_rule_sensitivity_threshold:
        present.add(RESOLUTION_RULE_SENSITIVE_REASON)
    return tuple(reason_code for reason_code in REASON_CODES if reason_code in present)


def _report_reason_codes(
    rows: tuple[ResearchPacketCounterfactualEvidenceGapRankV2Row, ...],
) -> tuple[str, ...]:
    status = _report_status(rows)
    present = {STATUS_REASON_BY_STATUS[status]}
    for row in rows:
        for reason_code in row.reason_codes:
            if reason_code not in STATUS_REASON_CODES:
                present.add(reason_code)
    return tuple(reason_code for reason_code in REASON_CODES if reason_code in present)


def _report_status(
    rows: tuple[ResearchPacketCounterfactualEvidenceGapRankV2Row, ...],
) -> str:
    if any(row.gap_status == BLOCKED_STATUS for row in rows):
        return BLOCKED_STATUS
    if any(row.gap_status == WATCH_STATUS for row in rows):
        return WATCH_STATUS
    return PASS_STATUS


def _normalize_inputs(
    inputs: list[ResearchPacketCounterfactualEvidenceGapInput]
    | tuple[ResearchPacketCounterfactualEvidenceGapInput, ...],
) -> tuple[ResearchPacketCounterfactualEvidenceGapInput, ...]:
    if type(inputs) not in (list, tuple):
        raise ValueError("inputs must be a list or tuple")
    normalized = tuple(inputs)
    seen_keys: set[tuple[str, str]] = set()
    for item in normalized:
        if type(item) is not ResearchPacketCounterfactualEvidenceGapInput:
            raise ValueError(
                "inputs must contain ResearchPacketCounterfactualEvidenceGapInput values",
            )
        require_paper_only_flags("input", item)
        key = (item.packet_ref, item.question_ref)
        if key in seen_keys:
            raise ValueError("inputs must not contain duplicate packet/question pairs")
        seen_keys.add(key)
    return normalized


def _normalize_rows(
    rows: object,
) -> tuple[ResearchPacketCounterfactualEvidenceGapRankV2Row, ...]:
    if type(rows) not in (list, tuple):
        raise ValueError("rows must be a list or tuple")
    normalized = tuple(rows)
    seen_keys: set[tuple[str, str]] = set()
    expected_ranks = tuple(_count(index + 1) for index in range(len(normalized)))
    if tuple(row.priority_rank for row in normalized) != expected_ranks:
        raise ValueError("rows must use contiguous priority_rank values")
    for row in normalized:
        if type(row) is not ResearchPacketCounterfactualEvidenceGapRankV2Row:
            raise ValueError(
                "rows must contain ResearchPacketCounterfactualEvidenceGapRankV2Row values",
            )
        require_paper_only_flags("row", row)
        key = (row.packet_ref, row.question_ref)
        if key in seen_keys:
            raise ValueError("rows must not contain duplicate packet/question pairs")
        seen_keys.add(key)
    if normalized != tuple(sorted(normalized, key=_row_sort_key)):
        raise ValueError("rows must use deterministic priority ordering")
    return normalized


def _row_sort_key(
    row: ResearchPacketCounterfactualEvidenceGapRankV2Row,
) -> tuple[Decimal, str, str]:
    return (-row.priority_score, row.packet_ref, row.question_ref)


def _status_count(
    rows: tuple[ResearchPacketCounterfactualEvidenceGapRankV2Row, ...],
    status: str,
) -> Decimal:
    return _count(sum(1 for row in rows if row.gap_status == status))


def _reason_count(
    rows: tuple[ResearchPacketCounterfactualEvidenceGapRankV2Row, ...],
    reason_code: str,
) -> Decimal:
    return _count(sum(1 for row in rows if reason_code in row.reason_codes))


def _validate_row(row: ResearchPacketCounterfactualEvidenceGapRankV2Row) -> None:
    if row.event_category_priority_score != EVENT_CATEGORY_PRIORITY_SCORES[row.event_category]:
        raise ValueError("event_category_priority_score must match event_category")
    if row.source_coverage_gap_score != _clamp_score(ONE_SCORE - row.source_coverage_score):
        raise ValueError("source_coverage_gap_score must match source_coverage_score")
    if row.recommended_research_action != RECOMMENDED_RESEARCH_ACTIONS[row.gap_status]:
        raise ValueError("recommended_research_action must match gap_status")
    if STATUS_REASON_BY_STATUS[row.gap_status] not in row.reason_codes:
        raise ValueError("reason_codes must include gap_status reason")
    if row.derived_validation_digest != _row_derived_validation_digest(row):
        raise ValueError("derived_validation_digest must match row fields")


def _validate_report(report: ResearchPacketCounterfactualEvidenceGapRankV2Report) -> None:
    if report.input_count != _count(len(report.rows)):
        raise ValueError("input_count must match rows")
    if report.blocked_count != _status_count(report.rows, BLOCKED_STATUS):
        raise ValueError("blocked_count must match rows")
    if report.watch_count != _status_count(report.rows, WATCH_STATUS):
        raise ValueError("watch_count must match rows")
    if report.pass_count != _status_count(report.rows, PASS_STATUS):
        raise ValueError("pass_count must match rows")
    if (
        report.missing_counterfactual_evidence_count
        != _reason_count(report.rows, MISSING_COUNTERFACTUAL_EVIDENCE_REASON)
    ):
        raise ValueError("missing_counterfactual_evidence_count must match rows")
    if (
        report.high_event_category_priority_count
        != _reason_count(report.rows, HIGH_EVENT_CATEGORY_PRIORITY_REASON)
    ):
        raise ValueError("high_event_category_priority_count must match rows")
    if report.high_catalyst_urgency_count != _reason_count(
        report.rows,
        HIGH_CATALYST_URGENCY_REASON,
    ):
        raise ValueError("high_catalyst_urgency_count must match rows")
    if report.thin_source_coverage_count != _reason_count(
        report.rows,
        THIN_SOURCE_COVERAGE_REASON,
    ):
        raise ValueError("thin_source_coverage_count must match rows")
    if report.contradiction_severity_count != _reason_count(
        report.rows,
        CONTRADICTION_SEVERITY_REASON,
    ):
        raise ValueError("contradiction_severity_count must match rows")
    if report.resolution_rule_sensitive_count != _reason_count(
        report.rows,
        RESOLUTION_RULE_SENSITIVE_REASON,
    ):
        raise ValueError("resolution_rule_sensitive_count must match rows")
    if report.highest_priority_score != max(
        (row.priority_score for row in report.rows),
        default=ZERO_SCORE,
    ):
        raise ValueError("highest_priority_score must match rows")
    if report.status != _report_status(report.rows):
        raise ValueError("status must match rows")
    if report.recommended_next_step != RECOMMENDED_NEXT_STEPS[report.status]:
        raise ValueError("recommended_next_step must match status")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")
    if report.derived_validation_digest != _report_derived_validation_digest(report):
        raise ValueError("derived_validation_digest must match report fields")


def _row_derived_validation_digest(
    row: ResearchPacketCounterfactualEvidenceGapRankV2Row,
) -> str:
    return _derived_validation_digest(_digest_payload_without_digest(row))


def _report_derived_validation_digest(
    report: ResearchPacketCounterfactualEvidenceGapRankV2Report,
) -> str:
    return _derived_validation_digest(_digest_payload_without_digest(report))


def _digest_payload_without_digest(value: object) -> object:
    payload = _canonical_payload_for_digest(value)
    if type(payload) is not dict:
        raise ValueError("derived_validation_digest payload must be a dict")
    payload.pop("derived_validation_digest", None)
    return payload


def _derived_validation_digest(value: object) -> str:
    encoded = json.dumps(
        value,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _canonical_payload_for_digest(value: object) -> object:
    if value is None or type(value) is bool or type(value) is str:
        return value
    if is_dataclass(value) and not isinstance(value, type):
        return _canonical_payload_for_digest(asdict(value))
    if isinstance(value, Decimal):
        if not value.is_finite():
            raise ValueError("derived_validation_digest Decimal values must be finite")
        return str(value)
    if isinstance(value, dict):
        ready: dict[str, object] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            if key == "derived_validation_digest":
                continue
            ready[key] = _canonical_payload_for_digest(item)
        return ready
    if isinstance(value, (list, tuple)):
        return [_canonical_payload_for_digest(item) for item in value]
    raise ValueError("derived_validation_digest values must be JSON serializable")


def _normalize_reason_codes(
    field_name: str,
    value: object,
) -> tuple[str, ...]:
    if type(value) not in (list, tuple):
        raise ValueError(f"{field_name} must be a list or tuple")
    reason_codes = tuple(value)
    if not reason_codes:
        raise ValueError(f"{field_name} must not be empty")
    seen: set[str] = set()
    for reason_code in reason_codes:
        _require_member(field_name, reason_code, REASON_CODES)
        if reason_code in seen:
            raise ValueError(f"{field_name} must not contain duplicates")
        seen.add(reason_code)
    expected = tuple(reason_code for reason_code in REASON_CODES if reason_code in seen)
    if reason_codes != expected:
        raise ValueError(f"{field_name} must use deterministic sequence")
    return reason_codes


def _require_member(
    field_name: str,
    value: object,
    allowed_values: tuple[str, ...],
) -> None:
    if type(value) is not str or value not in allowed_values:
        raise ValueError(f"{field_name} must be one of {', '.join(allowed_values)}")


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if value == "" or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")


def _require_sha256_digest(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if len(value) != 64:
        raise ValueError(f"{field_name} must be a SHA-256 hex digest")
    if any(character not in "0123456789abcdef" for character in value):
        raise ValueError(f"{field_name} must be a SHA-256 hex digest")


def _normalize_counterfactual_evidence_count(
    field_name: str,
    value: object,
) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value < ZERO_COUNT:
        raise ValueError(f"{field_name} must be nonnegative")
    if decimal_value != decimal_value.to_integral_value():
        raise ValueError(f"{field_name} must be an integer Decimal")
    return _quantize_score(decimal_value)


def _normalize_positive_count(field_name: str, value: object) -> Decimal:
    decimal_value = _normalize_nonnegative_count(field_name, value)
    if decimal_value <= ZERO_COUNT:
        raise ValueError(f"{field_name} must be positive")
    return decimal_value


def _normalize_nonnegative_count(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value < ZERO_COUNT:
        raise ValueError(f"{field_name} must be nonnegative")
    with localcontext(DECIMAL_CONTEXT):
        quantized = decimal_value.quantize(COUNT_QUANTUM)
    if quantized != decimal_value:
        raise ValueError(f"{field_name} must be an integer Decimal")
    return quantized


def _normalize_positive_driver_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value <= ZERO_SCORE:
        raise ValueError(f"{field_name} must be positive")
    return _quantize_score(decimal_value)


def _normalize_score(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value < ZERO_SCORE or decimal_value > ONE_SCORE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return _quantize_score(decimal_value)


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return value


def _require_score_total(*values: Decimal) -> None:
    with localcontext(DECIMAL_CONTEXT):
        if sum(values, ZERO_SCORE).quantize(SCORE_QUANTUM) != ONE_SCORE:
            raise ValueError("priority weights must sum to 1")


def _clamp_score(value: Decimal) -> Decimal:
    if value < ZERO_SCORE:
        return ZERO_SCORE
    if value > ONE_SCORE:
        return ONE_SCORE
    return _quantize_score(value)


def _quantize_score(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(SCORE_QUANTUM)


def _count(value: int) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return Decimal(value).quantize(COUNT_QUANTUM)
