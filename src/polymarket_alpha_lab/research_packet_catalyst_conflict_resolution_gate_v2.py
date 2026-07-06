"""Pure Phase 1 readonly catalyst conflict resolution gate report."""

from __future__ import annotations

from dataclasses import asdict, dataclass, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation, localcontext
import hashlib
import json
from typing import Any


DEFAULT_RESEARCH_PACKET_CATALYST_CONFLICT_RESOLUTION_GATE_V2_CONFIG_VERSION = (
    "research-packet-catalyst-conflict-resolution-gate-v2-v0"
)

DECIMAL_QUANT = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
WATCH_RISK_SCORE = Decimal("0.400000")
BLOCKED_RISK_SCORE = Decimal("0.800000")
INDEPENDENT_SOURCE_BOOST = Decimal("0.200000")
AVERAGE_BOOST_DISCOUNT_RATIO = Decimal("0.250000")

STATUSES = ("pass", "watch", "blocked")
REASON_CODES = (
    "catalyst_conflict_resolution_gate_no_inputs",
    "catalyst_conflict_resolution_gate_status_pass",
    "catalyst_conflict_resolution_gate_status_watch",
    "catalyst_conflict_resolution_gate_status_blocked",
    "unresolved_contradiction_watch",
    "unresolved_contradiction_blocked",
    "contradicting_source_pressure_watch",
    "contradicting_source_pressure_blocked",
    "weak_independent_source_quorum",
    "independent_source_boost_applied",
)
REASON_CODE_PRIORITY = REASON_CODES
BLOCK_REASONS = frozenset(
    (
        "unresolved_contradiction_blocked",
        "contradicting_source_pressure_blocked",
    ),
)
WATCH_REASONS = frozenset(
    (
        "unresolved_contradiction_watch",
        "contradicting_source_pressure_watch",
        "weak_independent_source_quorum",
    ),
)
STATUS_REASON = {
    "pass": "catalyst_conflict_resolution_gate_status_pass",
    "watch": "catalyst_conflict_resolution_gate_status_watch",
    "blocked": "catalyst_conflict_resolution_gate_status_blocked",
}
REPORT_NEXT_STEPS = {
    "pass": "use_catalyst_conflicts_for_paper_report",
    "watch": "review_catalyst_conflicts_before_paper_report",
    "blocked": "resolve_catalyst_conflicts_before_paper_report",
}
ROW_ACTIONS = {
    "pass": "use_catalyst_conflict_for_paper_report",
    "watch": "review_catalyst_conflict_before_paper_report",
    "blocked": "resolve_catalyst_conflict_before_paper_report",
}
UNSAFE_PUBLIC_TERMS = (
    "live",
    "auth",
    "wallet",
    "order",
    "network",
    "database",
    "persist",
    "signing",
    "mutation",
    "buy",
    "sell",
    "trade",
)
PHASE_FLAG_FIELDS = ("paper_only", "report_only", "readonly")
DERIVED_VALIDATION_DIGEST_FIELD = "derived_validation_digest"

_CONFIG_PAYLOAD_FIELDS = (
    "config_version",
    "max_pass_unresolved_contradiction_count",
    "max_watch_unresolved_contradiction_count",
    "max_pass_contradiction_ratio",
    "max_watch_contradiction_ratio",
    "min_pass_independent_source_ratio",
    "min_independent_source_boost_ratio",
    "min_independent_source_boost_count",
    "paper_only",
    "report_only",
    "readonly",
)
_INPUT_PAYLOAD_FIELDS = (
    "packet_ref",
    "question_ref",
    "catalyst_ref",
    "supporting_source_count",
    "contradicting_source_count",
    "independent_source_count",
    "resolved_contradiction_count",
    "unresolved_contradiction_count",
    "reason_codes",
    "paper_only",
    "report_only",
    "readonly",
)
_ROW_PAYLOAD_FIELDS = (
    "packet_ref",
    "question_ref",
    "catalyst_ref",
    "supporting_source_count",
    "contradicting_source_count",
    "independent_source_count",
    "resolved_contradiction_count",
    "unresolved_contradiction_count",
    "total_source_count",
    "contradiction_ratio",
    "unresolved_contradiction_ratio",
    "independent_source_ratio",
    "independent_source_boost",
    "conflict_risk_score",
    "conflict_status",
    "recommended_research_action",
    "reason_codes",
    "paper_only",
    "report_only",
    "readonly",
)
_REPORT_PAYLOAD_FIELDS = (
    "generated_at",
    "config_version",
    "status",
    "recommended_next_step",
    "input_count",
    "blocked_count",
    "watch_count",
    "pass_count",
    "unresolved_contradiction_count",
    "independent_source_boost_count",
    "highest_conflict_risk_score",
    "average_conflict_risk_score",
    "max_unresolved_contradiction_count",
    "rows",
    "reason_codes",
    "derived_validation_digest",
    "paper_only",
    "report_only",
    "readonly",
)

__all__ = (
    "DEFAULT_RESEARCH_PACKET_CATALYST_CONFLICT_RESOLUTION_GATE_V2_CONFIG_VERSION",
    "REASON_CODES",
    "ResearchPacketCatalystConflictResolutionGateV2Config",
    "ResearchPacketCatalystConflictResolutionGateV2Input",
    "ResearchPacketCatalystConflictResolutionGateV2Report",
    "ResearchPacketCatalystConflictResolutionGateV2Row",
    "STATUSES",
    "build_research_packet_catalyst_conflict_resolution_gate_v2_report",
    "research_packet_catalyst_conflict_resolution_gate_v2_payload",
)


@dataclass(frozen=True)
class ResearchPacketCatalystConflictResolutionGateV2Config:
    config_version: str = (
        DEFAULT_RESEARCH_PACKET_CATALYST_CONFLICT_RESOLUTION_GATE_V2_CONFIG_VERSION
    )
    max_pass_unresolved_contradiction_count: Decimal = Decimal("0.000000")
    max_watch_unresolved_contradiction_count: Decimal = Decimal("1.000000")
    max_pass_contradiction_ratio: Decimal = Decimal("0.250000")
    max_watch_contradiction_ratio: Decimal = Decimal("0.500000")
    min_pass_independent_source_ratio: Decimal = Decimal("0.666667")
    min_independent_source_boost_ratio: Decimal = Decimal("0.666667")
    min_independent_source_boost_count: Decimal = Decimal("2.000000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not ResearchPacketCatalystConflictResolutionGateV2Config:
            raise ValueError(
                "config must be a ResearchPacketCatalystConflictResolutionGateV2Config",
            )
        _require_canonical_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_PACKET_CATALYST_CONFLICT_RESOLUTION_GATE_V2_CONFIG_VERSION
        ):
            raise ValueError("config_version must be supported")
        for field_name in (
            "max_pass_unresolved_contradiction_count",
            "max_watch_unresolved_contradiction_count",
            "min_independent_source_boost_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_count(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "max_pass_contradiction_ratio",
            "max_watch_contradiction_ratio",
            "min_pass_independent_source_ratio",
            "min_independent_source_boost_ratio",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        _validate_config(self)
        _require_hard_flags("config", self)
        _reject_unsafe_public_payload("config", asdict(self))

    @property
    def payload(self) -> dict[str, object]:
        payload = _payload_value(asdict(self))
        _reject_unsafe_public_payload("config payload", payload)
        if type(payload) is not dict:
            raise ValueError("config payload must be an object")
        return payload


@dataclass(frozen=True)
class ResearchPacketCatalystConflictResolutionGateV2Input:
    packet_ref: str
    question_ref: str
    catalyst_ref: str
    supporting_source_count: Decimal
    contradicting_source_count: Decimal
    independent_source_count: Decimal
    resolved_contradiction_count: Decimal
    unresolved_contradiction_count: Decimal
    reason_codes: tuple[str, ...] = ()
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not ResearchPacketCatalystConflictResolutionGateV2Input:
            raise ValueError(
                "subject must be a ResearchPacketCatalystConflictResolutionGateV2Input",
            )
        for field_name in ("packet_ref", "question_ref", "catalyst_ref"):
            _require_identifier(field_name, getattr(self, field_name))
        for field_name in (
            "supporting_source_count",
            "contradicting_source_count",
            "independent_source_count",
            "resolved_contradiction_count",
            "unresolved_contradiction_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_count(field_name, getattr(self, field_name)),
            )
        if self.independent_source_count > _total_source_count(self):
            raise ValueError("independent_source_count must be at most total_source_count")
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_source_reason_codes("reason_codes", self.reason_codes),
        )
        _require_hard_flags("subject", self)
        _reject_unsafe_public_payload("catalyst conflict resolution input", asdict(self))

    @property
    def payload(self) -> dict[str, object]:
        payload = _payload_value(asdict(self))
        _reject_unsafe_public_payload("catalyst conflict resolution input payload", payload)
        if type(payload) is not dict:
            raise ValueError("input payload must be an object")
        return payload


@dataclass(frozen=True)
class ResearchPacketCatalystConflictResolutionGateV2Row:
    packet_ref: str
    question_ref: str
    catalyst_ref: str
    supporting_source_count: Decimal
    contradicting_source_count: Decimal
    independent_source_count: Decimal
    resolved_contradiction_count: Decimal
    unresolved_contradiction_count: Decimal
    total_source_count: Decimal
    contradiction_ratio: Decimal
    unresolved_contradiction_ratio: Decimal
    independent_source_ratio: Decimal
    independent_source_boost: Decimal
    conflict_risk_score: Decimal
    conflict_status: str
    recommended_research_action: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not ResearchPacketCatalystConflictResolutionGateV2Row:
            raise ValueError("row must be a ResearchPacketCatalystConflictResolutionGateV2Row")
        for field_name in ("packet_ref", "question_ref", "catalyst_ref"):
            _require_identifier(field_name, getattr(self, field_name))
        for field_name in (
            "supporting_source_count",
            "contradicting_source_count",
            "independent_source_count",
            "resolved_contradiction_count",
            "unresolved_contradiction_count",
            "total_source_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_count(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "contradiction_ratio",
            "unresolved_contradiction_ratio",
            "independent_source_ratio",
            "independent_source_boost",
            "conflict_risk_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        _require_choice("conflict_status", self.conflict_status, STATUSES)
        _require_choice(
            "recommended_research_action",
            self.recommended_research_action,
            tuple(ROW_ACTIONS.values()),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_row_reason_codes("reason_codes", self.reason_codes),
        )
        _require_hard_flags("row", self)
        _reject_unsafe_public_payload("catalyst conflict resolution row", asdict(self))
        _validate_row(self)


@dataclass(frozen=True)
class ResearchPacketCatalystConflictResolutionGateV2Report:
    generated_at: datetime
    config_version: str
    status: str
    recommended_next_step: str
    input_count: Decimal
    blocked_count: Decimal
    watch_count: Decimal
    pass_count: Decimal
    unresolved_contradiction_count: Decimal
    independent_source_boost_count: Decimal
    highest_conflict_risk_score: Decimal
    average_conflict_risk_score: Decimal
    max_unresolved_contradiction_count: Decimal
    rows: tuple[ResearchPacketCatalystConflictResolutionGateV2Row, ...]
    reason_codes: tuple[str, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not ResearchPacketCatalystConflictResolutionGateV2Report:
            raise ValueError(
                "report must be a ResearchPacketCatalystConflictResolutionGateV2Report",
            )
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_PACKET_CATALYST_CONFLICT_RESOLUTION_GATE_V2_CONFIG_VERSION
        ):
            raise ValueError("config_version must be supported")
        _require_choice("status", self.status, STATUSES)
        _require_choice(
            "recommended_next_step",
            self.recommended_next_step,
            tuple(REPORT_NEXT_STEPS.values()),
        )
        for field_name in (
            "input_count",
            "blocked_count",
            "watch_count",
            "pass_count",
            "unresolved_contradiction_count",
            "independent_source_boost_count",
            "max_unresolved_contradiction_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_count(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "highest_conflict_risk_score",
            "average_conflict_risk_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_report_reason_codes("reason_codes", self.reason_codes),
        )
        _require_hard_flags("report", self)
        _reject_unsafe_public_payload("catalyst conflict resolution report", asdict(self))
        if self.derived_validation_digest == "":
            object.__setattr__(
                self,
                DERIVED_VALIDATION_DIGEST_FIELD,
                _derived_validation_digest(self),
            )
        else:
            object.__setattr__(
                self,
                DERIVED_VALIDATION_DIGEST_FIELD,
                _normalize_sha256(
                    DERIVED_VALIDATION_DIGEST_FIELD,
                    self.derived_validation_digest,
                ),
            )
        _validate_report(self)
        _validate_report_derived_validation_digest(self)

    @property
    def payload(self) -> dict[str, object]:
        payload = _payload_value(asdict(self))
        _reject_unsafe_public_payload("catalyst conflict resolution payload", payload)
        if type(payload) is not dict:
            raise ValueError("catalyst conflict resolution payload must be an object")
        _validate_report(self)
        _validate_report_derived_validation_digest(self)
        return payload

    @classmethod
    def from_payload(
        cls,
        payload: object,
    ) -> ResearchPacketCatalystConflictResolutionGateV2Report:
        _reject_unsafe_public_payload("catalyst conflict resolution payload", payload)
        payload_dict = _payload_dict("catalyst conflict resolution payload", payload)
        _require_payload_fields(payload_dict, _REPORT_PAYLOAD_FIELDS)
        rows_value = payload_dict["rows"]
        if type(rows_value) is not list:
            raise ValueError("rows must be a list")
        return cls(
            generated_at=_payload_datetime("generated_at", payload_dict["generated_at"]),
            config_version=_payload_str("config_version", payload_dict["config_version"]),
            status=_payload_str("status", payload_dict["status"]),
            recommended_next_step=_payload_str(
                "recommended_next_step",
                payload_dict["recommended_next_step"],
            ),
            input_count=_payload_decimal("input_count", payload_dict["input_count"]),
            blocked_count=_payload_decimal("blocked_count", payload_dict["blocked_count"]),
            watch_count=_payload_decimal("watch_count", payload_dict["watch_count"]),
            pass_count=_payload_decimal("pass_count", payload_dict["pass_count"]),
            unresolved_contradiction_count=_payload_decimal(
                "unresolved_contradiction_count",
                payload_dict["unresolved_contradiction_count"],
            ),
            independent_source_boost_count=_payload_decimal(
                "independent_source_boost_count",
                payload_dict["independent_source_boost_count"],
            ),
            highest_conflict_risk_score=_payload_decimal(
                "highest_conflict_risk_score",
                payload_dict["highest_conflict_risk_score"],
            ),
            average_conflict_risk_score=_payload_decimal(
                "average_conflict_risk_score",
                payload_dict["average_conflict_risk_score"],
            ),
            max_unresolved_contradiction_count=_payload_decimal(
                "max_unresolved_contradiction_count",
                payload_dict["max_unresolved_contradiction_count"],
            ),
            rows=tuple(_row_from_payload(row) for row in rows_value),
            reason_codes=_payload_str_tuple("reason_codes", payload_dict["reason_codes"]),
            derived_validation_digest=_payload_str(
                DERIVED_VALIDATION_DIGEST_FIELD,
                payload_dict[DERIVED_VALIDATION_DIGEST_FIELD],
            ),
            paper_only=_payload_bool("paper_only", payload_dict["paper_only"]),
            report_only=_payload_bool("report_only", payload_dict["report_only"]),
            readonly=_payload_bool("readonly", payload_dict["readonly"]),
        )


def build_research_packet_catalyst_conflict_resolution_gate_v2_report(
    subjects: object,
    *,
    config: ResearchPacketCatalystConflictResolutionGateV2Config | None = None,
    generated_at: datetime,
) -> ResearchPacketCatalystConflictResolutionGateV2Report:
    if config is None:
        config = ResearchPacketCatalystConflictResolutionGateV2Config()
    if type(config) is not ResearchPacketCatalystConflictResolutionGateV2Config:
        raise ValueError(
            "config must be a ResearchPacketCatalystConflictResolutionGateV2Config",
        )
    object.__setattr__(config, "paper_only", config.paper_only)
    generated_at = _as_utc("generated_at", generated_at)
    normalized_subjects = _normalize_subjects(subjects)
    rows = tuple(
        sorted(
            (_row_for_subject(subject, config) for subject in normalized_subjects),
            key=_row_sort_key,
        ),
    )
    status = _report_status(rows)
    return ResearchPacketCatalystConflictResolutionGateV2Report(
        generated_at=generated_at,
        config_version=config.config_version,
        status=status,
        recommended_next_step=REPORT_NEXT_STEPS[status],
        input_count=_count(len(rows)),
        blocked_count=_count(sum(1 for row in rows if row.conflict_status == "blocked")),
        watch_count=_count(sum(1 for row in rows if row.conflict_status == "watch")),
        pass_count=_count(sum(1 for row in rows if row.conflict_status == "pass")),
        unresolved_contradiction_count=_sum_decimal(
            row.unresolved_contradiction_count for row in rows
        ),
        independent_source_boost_count=_count(
            sum(1 for row in rows if row.independent_source_boost > ZERO),
        ),
        highest_conflict_risk_score=_max_decimal(row.conflict_risk_score for row in rows),
        average_conflict_risk_score=_average_conflict_risk_score(rows),
        max_unresolved_contradiction_count=_max_decimal(
            row.unresolved_contradiction_count for row in rows
        ),
        rows=rows,
        reason_codes=_report_reason_codes(rows, status),
    )


def research_packet_catalyst_conflict_resolution_gate_v2_payload(
    report: object,
) -> dict[str, object]:
    if type(report) is not ResearchPacketCatalystConflictResolutionGateV2Report:
        raise ValueError(
            "report must be a ResearchPacketCatalystConflictResolutionGateV2Report",
        )
    return report.payload


def _row_for_subject(
    subject: ResearchPacketCatalystConflictResolutionGateV2Input,
    config: ResearchPacketCatalystConflictResolutionGateV2Config,
) -> ResearchPacketCatalystConflictResolutionGateV2Row:
    total_source_count = _total_source_count(subject)
    contradiction_ratio = _ratio(
        numerator=subject.contradicting_source_count,
        denominator=total_source_count,
    )
    unresolved_total = (
        subject.resolved_contradiction_count + subject.unresolved_contradiction_count
    )
    unresolved_contradiction_ratio = _ratio(
        numerator=subject.unresolved_contradiction_count,
        denominator=unresolved_total,
    )
    independent_source_ratio = _ratio(
        numerator=subject.independent_source_count,
        denominator=total_source_count,
    )
    independent_source_boost = _independent_source_boost(
        subject=subject,
        independent_source_ratio=independent_source_ratio,
        config=config,
    )
    reason_codes = _row_reason_codes(
        subject=subject,
        contradiction_ratio=contradiction_ratio,
        independent_source_ratio=independent_source_ratio,
        config=config,
    )
    conflict_status = _row_status(reason_codes)
    return ResearchPacketCatalystConflictResolutionGateV2Row(
        packet_ref=subject.packet_ref,
        question_ref=subject.question_ref,
        catalyst_ref=subject.catalyst_ref,
        supporting_source_count=subject.supporting_source_count,
        contradicting_source_count=subject.contradicting_source_count,
        independent_source_count=subject.independent_source_count,
        resolved_contradiction_count=subject.resolved_contradiction_count,
        unresolved_contradiction_count=subject.unresolved_contradiction_count,
        total_source_count=total_source_count,
        contradiction_ratio=contradiction_ratio,
        unresolved_contradiction_ratio=unresolved_contradiction_ratio,
        independent_source_ratio=independent_source_ratio,
        independent_source_boost=independent_source_boost,
        conflict_risk_score=_risk_score_for_status(conflict_status),
        conflict_status=conflict_status,
        recommended_research_action=ROW_ACTIONS[conflict_status],
        reason_codes=reason_codes,
    )


def _row_from_payload(payload: object) -> ResearchPacketCatalystConflictResolutionGateV2Row:
    payload_dict = _payload_dict("row", payload)
    _require_payload_fields(payload_dict, _ROW_PAYLOAD_FIELDS)
    return ResearchPacketCatalystConflictResolutionGateV2Row(
        packet_ref=_payload_str("packet_ref", payload_dict["packet_ref"]),
        question_ref=_payload_str("question_ref", payload_dict["question_ref"]),
        catalyst_ref=_payload_str("catalyst_ref", payload_dict["catalyst_ref"]),
        supporting_source_count=_payload_decimal(
            "supporting_source_count",
            payload_dict["supporting_source_count"],
        ),
        contradicting_source_count=_payload_decimal(
            "contradicting_source_count",
            payload_dict["contradicting_source_count"],
        ),
        independent_source_count=_payload_decimal(
            "independent_source_count",
            payload_dict["independent_source_count"],
        ),
        resolved_contradiction_count=_payload_decimal(
            "resolved_contradiction_count",
            payload_dict["resolved_contradiction_count"],
        ),
        unresolved_contradiction_count=_payload_decimal(
            "unresolved_contradiction_count",
            payload_dict["unresolved_contradiction_count"],
        ),
        total_source_count=_payload_decimal(
            "total_source_count",
            payload_dict["total_source_count"],
        ),
        contradiction_ratio=_payload_decimal(
            "contradiction_ratio",
            payload_dict["contradiction_ratio"],
        ),
        unresolved_contradiction_ratio=_payload_decimal(
            "unresolved_contradiction_ratio",
            payload_dict["unresolved_contradiction_ratio"],
        ),
        independent_source_ratio=_payload_decimal(
            "independent_source_ratio",
            payload_dict["independent_source_ratio"],
        ),
        independent_source_boost=_payload_decimal(
            "independent_source_boost",
            payload_dict["independent_source_boost"],
        ),
        conflict_risk_score=_payload_decimal(
            "conflict_risk_score",
            payload_dict["conflict_risk_score"],
        ),
        conflict_status=_payload_str("conflict_status", payload_dict["conflict_status"]),
        recommended_research_action=_payload_str(
            "recommended_research_action",
            payload_dict["recommended_research_action"],
        ),
        reason_codes=_payload_str_tuple("reason_codes", payload_dict["reason_codes"]),
        paper_only=_payload_bool("paper_only", payload_dict["paper_only"]),
        report_only=_payload_bool("report_only", payload_dict["report_only"]),
        readonly=_payload_bool("readonly", payload_dict["readonly"]),
    )


def _row_reason_codes(
    *,
    subject: ResearchPacketCatalystConflictResolutionGateV2Input,
    contradiction_ratio: Decimal,
    independent_source_ratio: Decimal,
    config: ResearchPacketCatalystConflictResolutionGateV2Config,
) -> tuple[str, ...]:
    reasons: list[str] = list(subject.reason_codes)
    if subject.unresolved_contradiction_count > config.max_watch_unresolved_contradiction_count:
        reasons.append("unresolved_contradiction_blocked")
    elif subject.unresolved_contradiction_count > config.max_pass_unresolved_contradiction_count:
        reasons.append("unresolved_contradiction_watch")
    if contradiction_ratio > config.max_watch_contradiction_ratio:
        reasons.append("contradicting_source_pressure_blocked")
    elif contradiction_ratio > config.max_pass_contradiction_ratio:
        reasons.append("contradicting_source_pressure_watch")
    if independent_source_ratio < config.min_pass_independent_source_ratio:
        reasons.append("weak_independent_source_quorum")
    if _independent_source_boost(
        subject=subject,
        independent_source_ratio=independent_source_ratio,
        config=config,
    ) > ZERO:
        reasons.append("independent_source_boost_applied")
    status = _row_status(tuple(reasons))
    return _dedupe_reason_codes(
        (*subject.reason_codes, STATUS_REASON[status], *tuple(reasons)),
    )


def _independent_source_boost(
    *,
    subject: ResearchPacketCatalystConflictResolutionGateV2Input,
    independent_source_ratio: Decimal,
    config: ResearchPacketCatalystConflictResolutionGateV2Config,
) -> Decimal:
    if (
        subject.independent_source_count >= config.min_independent_source_boost_count
        and independent_source_ratio >= config.min_independent_source_boost_ratio
    ):
        return INDEPENDENT_SOURCE_BOOST
    return ZERO


def _validate_config(
    config: ResearchPacketCatalystConflictResolutionGateV2Config,
) -> None:
    if (
        config.max_pass_unresolved_contradiction_count
        > config.max_watch_unresolved_contradiction_count
    ):
        raise ValueError(
            "max_pass_unresolved_contradiction_count must be at most "
            "max_watch_unresolved_contradiction_count",
        )
    if config.max_pass_contradiction_ratio > config.max_watch_contradiction_ratio:
        raise ValueError(
            "max_pass_contradiction_ratio must be at most max_watch_contradiction_ratio",
        )
    if config.min_independent_source_boost_ratio < config.min_pass_independent_source_ratio:
        raise ValueError(
            "min_independent_source_boost_ratio must be at least "
            "min_pass_independent_source_ratio",
        )


def _validate_row(row: ResearchPacketCatalystConflictResolutionGateV2Row) -> None:
    if row.independent_source_count > row.total_source_count:
        raise ValueError("independent_source_count must be at most total_source_count")
    if row.total_source_count != row.supporting_source_count + row.contradicting_source_count:
        raise ValueError("total_source_count must match supporting and contradicting sources")
    if row.contradiction_ratio != _ratio(
        numerator=row.contradicting_source_count,
        denominator=row.total_source_count,
    ):
        raise ValueError("contradiction_ratio must match source counts")
    unresolved_total = row.resolved_contradiction_count + row.unresolved_contradiction_count
    if row.unresolved_contradiction_ratio != _ratio(
        numerator=row.unresolved_contradiction_count,
        denominator=unresolved_total,
    ):
        raise ValueError("unresolved_contradiction_ratio must match contradiction counts")
    if row.independent_source_ratio != _ratio(
        numerator=row.independent_source_count,
        denominator=row.total_source_count,
    ):
        raise ValueError("independent_source_ratio must match source counts")
    if row.independent_source_boost not in (ZERO, INDEPENDENT_SOURCE_BOOST):
        raise ValueError("independent_source_boost must match boost policy")
    if row.conflict_status != _row_status(row.reason_codes):
        raise ValueError("conflict_status must match reason_codes")
    if row.conflict_risk_score != _risk_score_for_status(row.conflict_status):
        raise ValueError("conflict_risk_score must match conflict_status")
    if row.recommended_research_action != ROW_ACTIONS[row.conflict_status]:
        raise ValueError("recommended_research_action must match conflict_status")
    if STATUS_REASON[row.conflict_status] not in row.reason_codes:
        raise ValueError("reason_codes must include conflict_status reason")


def _validate_report(
    report: ResearchPacketCatalystConflictResolutionGateV2Report,
) -> None:
    rows = report.rows
    if report.input_count != _count(len(rows)):
        raise ValueError("input_count must match rows")
    if report.blocked_count != _count(
        sum(1 for row in rows if row.conflict_status == "blocked"),
    ):
        raise ValueError("blocked_count must match rows")
    if report.watch_count != _count(sum(1 for row in rows if row.conflict_status == "watch")):
        raise ValueError("watch_count must match rows")
    if report.pass_count != _count(sum(1 for row in rows if row.conflict_status == "pass")):
        raise ValueError("pass_count must match rows")
    if report.unresolved_contradiction_count != _sum_decimal(
        row.unresolved_contradiction_count for row in rows
    ):
        raise ValueError("unresolved_contradiction_count must match rows")
    if report.independent_source_boost_count != _count(
        sum(1 for row in rows if row.independent_source_boost > ZERO),
    ):
        raise ValueError("independent_source_boost_count must match rows")
    if report.highest_conflict_risk_score != _max_decimal(
        row.conflict_risk_score for row in rows
    ):
        raise ValueError("highest_conflict_risk_score must match rows")
    if report.average_conflict_risk_score != _average_conflict_risk_score(rows):
        raise ValueError("average_conflict_risk_score must match rows")
    if report.max_unresolved_contradiction_count != _max_decimal(
        row.unresolved_contradiction_count for row in rows
    ):
        raise ValueError("max_unresolved_contradiction_count must match rows")
    if report.status != _report_status(rows):
        raise ValueError("status must match rows")
    if report.recommended_next_step != REPORT_NEXT_STEPS[report.status]:
        raise ValueError("recommended_next_step must match status")
    if report.reason_codes != _report_reason_codes(rows, report.status):
        raise ValueError("reason_codes must match rows")


def _validate_report_derived_validation_digest(
    report: ResearchPacketCatalystConflictResolutionGateV2Report,
) -> None:
    if report.derived_validation_digest != _derived_validation_digest(report):
        raise ValueError("derived_validation_digest must match report payload")


def _report_status(
    rows: tuple[ResearchPacketCatalystConflictResolutionGateV2Row, ...],
) -> str:
    if any(row.conflict_status == "blocked" for row in rows):
        return "blocked"
    if any(row.conflict_status == "watch" for row in rows):
        return "watch"
    return "pass"


def _row_status(reason_codes: tuple[str, ...]) -> str:
    if any(reason in BLOCK_REASONS for reason in reason_codes):
        return "blocked"
    if any(reason in WATCH_REASONS for reason in reason_codes):
        return "watch"
    return "pass"


def _risk_score_for_status(status: str) -> Decimal:
    if status == "blocked":
        return BLOCKED_RISK_SCORE
    if status == "watch":
        return WATCH_RISK_SCORE
    return ZERO


def _row_sort_key(
    row: ResearchPacketCatalystConflictResolutionGateV2Row,
) -> tuple[int, Decimal, str, str, str]:
    status_rank = {"blocked": 0, "watch": 1, "pass": 2}[row.conflict_status]
    return (
        status_rank,
        -row.conflict_risk_score,
        row.packet_ref,
        row.question_ref,
        row.catalyst_ref,
    )


def _report_reason_codes(
    rows: tuple[ResearchPacketCatalystConflictResolutionGateV2Row, ...],
    status: str,
) -> tuple[str, ...]:
    if not rows:
        return ("catalyst_conflict_resolution_gate_no_inputs", STATUS_REASON[status])
    reasons: list[str] = [STATUS_REASON[status]]
    status_reasons = frozenset(STATUS_REASON.values())
    for reason in REASON_CODE_PRIORITY:
        if reason in status_reasons or reason == "catalyst_conflict_resolution_gate_no_inputs":
            continue
        if any(reason in row.reason_codes for row in rows):
            reasons.append(reason)
    return tuple(reasons)


def _average_conflict_risk_score(
    rows: tuple[ResearchPacketCatalystConflictResolutionGateV2Row, ...],
) -> Decimal:
    if not rows:
        return ZERO
    gross_score = _sum_decimal(row.conflict_risk_score for row in rows)
    boost_discount = _sum_decimal(row.independent_source_boost for row in rows) * (
        AVERAGE_BOOST_DISCOUNT_RATIO
    )
    adjusted_score = gross_score - boost_discount
    if adjusted_score < ZERO:
        adjusted_score = ZERO
    return _quantize(adjusted_score / _count(len(rows)))


def _total_source_count(
    subject: ResearchPacketCatalystConflictResolutionGateV2Input,
) -> Decimal:
    return _quantize(subject.supporting_source_count + subject.contradicting_source_count)


def _ratio(*, numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO:
        return ZERO
    return _normalize_probability("ratio", numerator / denominator)


def _normalize_subjects(
    subjects: object,
) -> tuple[ResearchPacketCatalystConflictResolutionGateV2Input, ...]:
    if isinstance(subjects, (str, bytes)) or not isinstance(subjects, tuple | list):
        raise ValueError("subjects must be a tuple or list")
    normalized: list[ResearchPacketCatalystConflictResolutionGateV2Input] = []
    for subject in subjects:
        if type(subject) is not ResearchPacketCatalystConflictResolutionGateV2Input:
            raise ValueError(
                "subjects must contain ResearchPacketCatalystConflictResolutionGateV2Input",
            )
        normalized.append(subject)
    return tuple(normalized)


def _normalize_rows(
    rows: object,
) -> tuple[ResearchPacketCatalystConflictResolutionGateV2Row, ...]:
    if isinstance(rows, (str, bytes)) or not isinstance(rows, tuple | list):
        raise ValueError("rows must be a tuple or list")
    normalized: list[ResearchPacketCatalystConflictResolutionGateV2Row] = []
    for row in rows:
        if type(row) is not ResearchPacketCatalystConflictResolutionGateV2Row:
            raise ValueError(
                "rows must contain ResearchPacketCatalystConflictResolutionGateV2Row",
            )
        normalized.append(row)
    return tuple(sorted(normalized, key=_row_sort_key))


def _normalize_source_reason_codes(field_name: str, value: object) -> tuple[str, ...]:
    if isinstance(value, (str, bytes)) or not isinstance(value, tuple | list):
        raise ValueError(f"{field_name} must be a tuple or list")
    reasons: list[str] = []
    for item in value:
        _require_canonical_string(field_name, item)
        assert type(item) is str
        if _has_unsafe_public_token(item):
            raise ValueError(f"{field_name} has unsafe public payload value")
        if item not in reasons:
            reasons.append(item)
    return tuple(reasons)


def _normalize_row_reason_codes(field_name: str, value: object) -> tuple[str, ...]:
    return _normalize_source_reason_codes(field_name, value)


def _normalize_report_reason_codes(field_name: str, value: object) -> tuple[str, ...]:
    reasons = _normalize_source_reason_codes(field_name, value)
    for reason in reasons:
        if reason not in REASON_CODES:
            raise ValueError(f"{field_name} contains an unsupported reason code")
    return reasons


def _dedupe_reason_codes(value: tuple[str, ...]) -> tuple[str, ...]:
    reasons: list[str] = []
    for item in value:
        if item not in reasons:
            reasons.append(item)
    return tuple(reasons)


def _sum_decimal(values: object) -> Decimal:
    total = ZERO
    for value in values:
        total += value
    return _quantize(total)


def _max_decimal(values: object) -> Decimal:
    current = ZERO
    for value in values:
        if value > current:
            current = value
    return _quantize(current)


def _count(value: int) -> Decimal:
    return _quantize(Decimal(value))


def _normalize_nonnegative_count(field_name: str, value: object) -> Decimal:
    normalized = _normalize_nonnegative_decimal(field_name, value)
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{field_name} must be integral")
    return normalized


def _normalize_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _normalize_probability(field_name: str, value: object) -> Decimal:
    normalized = _normalize_nonnegative_decimal(field_name, value)
    if normalized > ONE:
        raise ValueError(f"{field_name} must be at most 1.000000")
    return normalized


def _normalize_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return _quantize(value)


def _quantize(value: Decimal) -> Decimal:
    with localcontext() as ctx:
        ctx.prec = 48
        return value.quantize(DECIMAL_QUANT)


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_identifier(field_name: str, value: object) -> None:
    _require_canonical_string(field_name, value)
    assert type(value) is str
    if _has_unsafe_public_token(value):
        raise ValueError(f"{field_name} has unsafe public payload value")


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str or not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a non-empty canonical string")


def _require_choice(field_name: str, value: object, choices: tuple[str, ...]) -> None:
    if type(value) is not str or value not in choices:
        raise ValueError(f"{field_name} must be one of {', '.join(choices)}")


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in PHASE_FLAG_FIELDS:
        if getattr(value, field_name) is not True:
            raise ValueError(f"{field_name} must be True for {label}")


def _normalize_sha256(field_name: str, value: object) -> str:
    if type(value) is not str or len(value) != 64:
        raise ValueError(f"{field_name} must be a sha256 hex digest")
    lowered = value.lower()
    if value != lowered:
        raise ValueError(f"{field_name} must be lowercase")
    if any(character not in "0123456789abcdef" for character in lowered):
        raise ValueError(f"{field_name} must be a sha256 hex digest")
    return lowered


def _payload_value(value: object) -> object:
    if type(value) is Decimal:
        return format(value, "f")
    if type(value) is datetime:
        return value.isoformat()
    if is_dataclass(value) and not isinstance(value, type):
        return _payload_value(asdict(value))
    if type(value) is tuple:
        return [_payload_value(item) for item in value]
    if type(value) is list:
        return [_payload_value(item) for item in value]
    if type(value) is dict:
        return {key: _payload_value(item) for key, item in value.items()}
    if value is None or type(value) in (str, bool):
        return value
    raise ValueError("payload contains an unsupported value")


def _report_payload_without_digest(
    report: ResearchPacketCatalystConflictResolutionGateV2Report,
) -> dict[str, object]:
    payload = _payload_value(asdict(report))
    if type(payload) is not dict:
        raise ValueError("report payload must be an object")
    payload.pop(DERIVED_VALIDATION_DIGEST_FIELD, None)
    return payload


def _derived_validation_digest(
    report: ResearchPacketCatalystConflictResolutionGateV2Report,
) -> str:
    canonical_json = json.dumps(
        _report_payload_without_digest(report),
        allow_nan=False,
        separators=(",", ":"),
        sort_keys=True,
    )
    return hashlib.sha256(canonical_json.encode("utf-8")).hexdigest()


def _payload_dict(field_name: str, value: object) -> dict[str, object]:
    if type(value) is not dict:
        raise ValueError(f"{field_name} must be an object")
    if any(type(key) is not str for key in value):
        raise ValueError(f"{field_name} keys must be strings")
    _reject_unsafe_public_payload(field_name, value)
    return value


def _require_payload_fields(
    payload: dict[str, object],
    expected_fields: tuple[str, ...],
) -> None:
    actual_fields = tuple(payload.keys())
    if actual_fields != expected_fields:
        raise ValueError("payload fields must match schema")


def _payload_str(field_name: str, value: object) -> str:
    _require_canonical_string(field_name, value)
    assert type(value) is str
    if _has_unsafe_public_token(value):
        raise ValueError(f"{field_name} has unsafe public payload value")
    return value


def _payload_bool(field_name: str, value: object) -> bool:
    if type(value) is not bool:
        raise ValueError(f"{field_name} must be a boolean")
    return value


def _payload_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a decimal string")
    try:
        parsed = Decimal(value)
    except InvalidOperation as exc:
        raise ValueError(f"{field_name} must be a decimal string") from exc
    return _normalize_decimal(field_name, parsed)


def _payload_datetime(field_name: str, value: object) -> datetime:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a datetime string")
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError as exc:
        raise ValueError(f"{field_name} must be a datetime string") from exc
    return _as_utc(field_name, parsed)


def _payload_str_tuple(field_name: str, value: object) -> tuple[str, ...]:
    if type(value) is not list:
        raise ValueError(f"{field_name} must be a list")
    return tuple(_payload_str(field_name, item) for item in value)


def _reject_unsafe_public_payload(label: str, value: object) -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError(f"{label} contains non-string key")
            if _has_unsafe_public_token(key):
                raise ValueError(f"{label} contains unsafe public payload key")
            _reject_unsafe_public_payload(label, item)
        return
    if isinstance(value, (list, tuple)):
        for item in value:
            _reject_unsafe_public_payload(label, item)
        return
    if type(value) is str and _has_unsafe_public_token(value):
        raise ValueError(f"{label} contains unsafe public payload value")
    if (
        value is None
        or type(value) in (bool, int, Decimal, datetime)
        or is_dataclass(value)
        and not isinstance(value, type)
    ):
        return
    if type(value) is float:
        raise ValueError(f"{label} contains unsupported numeric payload value")


def _has_unsafe_public_token(value: str) -> bool:
    lowered = value.lower()
    return any(term in lowered for term in UNSAFE_PUBLIC_TERMS)
