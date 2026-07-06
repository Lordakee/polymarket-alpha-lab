"""Pure Phase 1 readonly research packet source-gap triage report."""

from __future__ import annotations

from dataclasses import asdict, dataclass, replace
from decimal import Decimal, InvalidOperation
import hashlib
from typing import Any


DEFAULT_RESEARCH_PACKET_SOURCE_GAP_TRIAGE_V2_CONFIG_VERSION = (
    "research-packet-source-gap-triage-v2-v0"
)

SCORE_QUANT = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")

OFFICIAL_ANCHOR_WEIGHT = Decimal("0.15666665")
SOURCE_FAMILY_WEIGHT = Decimal("0.05000000")
STALE_EVIDENCE_WEIGHT = Decimal("0.20000000")
CONTRADICTION_WEIGHT = Decimal("0.05000000")
UNATTRIBUTED_MOVE_WEIGHT = Decimal("0.05000000")
RESOLUTION_HORIZON_WEIGHT = Decimal("0.33500000")
SPECIALIST_UNCERTAINTY_WEIGHT = Decimal("0.20000000")

STATUSES = ("pass", "watch", "blocked")
REASON_CODES = (
    "source_gap_triage_no_inputs",
    "source_gap_triage_status_pass",
    "source_gap_triage_status_watch",
    "source_gap_triage_status_blocked",
    "missing_official_anchor",
    "weak_source_family_independence",
    "stale_evidence",
    "contradiction_severity",
    "unattributed_probability_move",
    "near_resolution_horizon",
    "specialist_uncertainty",
)
TRIAGE_REASON_ORDER = REASON_CODES[4:]
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
REPORT_NEXT_STEPS = {
    "pass": "use_source_gap_triage_for_paper_report",
    "watch": "review_source_gap_evidence_for_paper_report",
    "blocked": "collect_source_gap_evidence_for_paper_report",
}
ROW_ACTIONS = {
    "pass": "source_gap_research_clear",
    "watch": "source_gap_research_watch",
    "blocked": "source_gap_research_first",
}

__all__ = (
    "DEFAULT_RESEARCH_PACKET_SOURCE_GAP_TRIAGE_V2_CONFIG_VERSION",
    "REASON_CODES",
    "ResearchPacketSourceGapTriageV2Config",
    "ResearchPacketSourceGapTriageV2Input",
    "ResearchPacketSourceGapTriageV2Report",
    "ResearchPacketSourceGapTriageV2Row",
    "STATUSES",
    "build_research_packet_source_gap_triage_v2_report",
    "research_packet_source_gap_triage_v2_payload",
)


@dataclass(frozen=True)
class ResearchPacketSourceGapTriageV2Config:
    config_version: str = DEFAULT_RESEARCH_PACKET_SOURCE_GAP_TRIAGE_V2_CONFIG_VERSION
    min_official_anchor_count: Decimal = Decimal("1.000000")
    min_source_family_count: Decimal = Decimal("3.000000")
    fresh_evidence_age_hours: Decimal = Decimal("24.000000")
    stale_evidence_span_hours: Decimal = Decimal("48.000000")
    near_resolution_hours: Decimal = Decimal("24.000000")
    safe_resolution_hours: Decimal = Decimal("168.000000")
    blocked_priority_score: Decimal = Decimal("0.750000")
    watch_priority_score: Decimal = Decimal("0.050000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not ResearchPacketSourceGapTriageV2Config:
            raise ValueError("config must be a ResearchPacketSourceGapTriageV2Config")
        _require_canonical_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_PACKET_SOURCE_GAP_TRIAGE_V2_CONFIG_VERSION
        ):
            raise ValueError("config_version must be supported")
        for field_name in (
            "min_official_anchor_count",
            "min_source_family_count",
            "fresh_evidence_age_hours",
            "stale_evidence_span_hours",
            "near_resolution_hours",
            "safe_resolution_hours",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_positive_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in ("blocked_priority_score", "watch_priority_score"):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        if self.near_resolution_hours >= self.safe_resolution_hours:
            raise ValueError("near_resolution_hours must be below safe_resolution_hours")
        if self.watch_priority_score >= self.blocked_priority_score:
            raise ValueError("watch_priority_score must be below blocked_priority_score")
        _require_hard_flags(self)
        _reject_unsafe_public_payload("config", asdict(self))


@dataclass(frozen=True)
class ResearchPacketSourceGapTriageV2Input:
    packet_ref: str
    question_ref: str
    specialist_ref: str
    official_anchor_count: Decimal
    source_family_count: Decimal
    freshest_evidence_age_hours: Decimal
    contradiction_severity_score: Decimal
    unattributed_probability_move: Decimal
    hours_to_resolution: Decimal
    specialist_uncertainty_score: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not ResearchPacketSourceGapTriageV2Input:
            raise ValueError("subject must be a ResearchPacketSourceGapTriageV2Input")
        for field_name in ("packet_ref", "question_ref", "specialist_ref"):
            _require_identifier(field_name, getattr(self, field_name))
        for field_name in (
            "official_anchor_count",
            "source_family_count",
            "freshest_evidence_age_hours",
            "hours_to_resolution",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "contradiction_severity_score",
            "unattributed_probability_move",
            "specialist_uncertainty_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        _require_hard_flags(self)
        _reject_unsafe_public_payload("source gap triage input", asdict(self))


@dataclass(frozen=True)
class ResearchPacketSourceGapTriageV2Row:
    packet_ref: str
    question_ref: str
    specialist_ref: str
    priority_rank: Decimal
    priority_score: Decimal
    official_anchor_gap_score: Decimal
    source_family_independence_gap_score: Decimal
    stale_evidence_score: Decimal
    contradiction_severity_score: Decimal
    unattributed_probability_move: Decimal
    resolution_horizon_score: Decimal
    specialist_uncertainty_score: Decimal
    official_anchor_count: Decimal
    source_family_count: Decimal
    freshest_evidence_age_hours: Decimal
    hours_to_resolution: Decimal
    triage_status: str
    recommended_research_action: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not ResearchPacketSourceGapTriageV2Row:
            raise ValueError("row must be a ResearchPacketSourceGapTriageV2Row")
        for field_name in ("packet_ref", "question_ref", "specialist_ref"):
            _require_identifier(field_name, getattr(self, field_name))
        object.__setattr__(
            self,
            "priority_rank",
            _normalize_positive_decimal("priority_rank", self.priority_rank),
        )
        for field_name in (
            "priority_score",
            "official_anchor_gap_score",
            "source_family_independence_gap_score",
            "stale_evidence_score",
            "contradiction_severity_score",
            "unattributed_probability_move",
            "resolution_horizon_score",
            "specialist_uncertainty_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "official_anchor_count",
            "source_family_count",
            "freshest_evidence_age_hours",
            "hours_to_resolution",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        _require_choice("triage_status", self.triage_status, STATUSES)
        _require_choice(
            "recommended_research_action",
            self.recommended_research_action,
            tuple(ROW_ACTIONS.values()),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes, allow_empty=False),
        )
        _require_hard_flags(self)
        _reject_unsafe_public_payload("source gap triage row", asdict(self))
        _validate_row(self)


@dataclass(frozen=True)
class ResearchPacketSourceGapTriageV2Report:
    config_version: str
    status: str
    recommended_next_step: str
    input_count: Decimal
    blocked_count: Decimal
    watch_count: Decimal
    pass_count: Decimal
    missing_official_anchor_count: Decimal
    weak_source_family_independence_count: Decimal
    stale_evidence_count: Decimal
    contradiction_severity_count: Decimal
    unattributed_probability_move_count: Decimal
    near_resolution_horizon_count: Decimal
    specialist_uncertainty_count: Decimal
    highest_priority_score: Decimal
    rows: tuple[ResearchPacketSourceGapTriageV2Row, ...]
    reason_codes: tuple[str, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not ResearchPacketSourceGapTriageV2Report:
            raise ValueError("report must be a ResearchPacketSourceGapTriageV2Report")
        _require_canonical_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_PACKET_SOURCE_GAP_TRIAGE_V2_CONFIG_VERSION
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
            "missing_official_anchor_count",
            "weak_source_family_independence_count",
            "stale_evidence_count",
            "contradiction_severity_count",
            "unattributed_probability_move_count",
            "near_resolution_horizon_count",
            "specialist_uncertainty_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "highest_priority_score",
            _normalize_probability("highest_priority_score", self.highest_priority_score),
        )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes, allow_empty=False),
        )
        _require_hard_flags(self)
        _reject_unsafe_public_payload("source gap triage report", asdict(self))
        if self.derived_validation_digest == "":
            object.__setattr__(
                self,
                "derived_validation_digest",
                _derived_validation_digest(self),
            )
        else:
            object.__setattr__(
                self,
                "derived_validation_digest",
                _normalize_derived_validation_digest(self.derived_validation_digest),
            )
        _validate_report(self)

    @property
    def payload(self) -> dict[str, object]:
        payload = _payload_value(asdict(self))
        _reject_unsafe_public_payload("source gap triage payload", payload)
        if type(payload) is not dict:
            raise ValueError("source gap triage payload must be an object")
        return payload

    @classmethod
    def from_payload(cls, payload: object) -> ResearchPacketSourceGapTriageV2Report:
        _reject_unsafe_public_payload("source gap triage payload", payload)
        payload_dict = _payload_dict("source gap triage payload", payload)
        _require_payload_fields(payload_dict, _REPORT_PAYLOAD_FIELDS)
        rows_value = payload_dict["rows"]
        if not isinstance(rows_value, list):
            raise ValueError("rows must be a list")
        rows = tuple(_row_from_payload(item) for item in rows_value)
        return cls(
            config_version=_payload_string("config_version", payload_dict["config_version"]),
            status=_payload_string("status", payload_dict["status"]),
            recommended_next_step=_payload_string(
                "recommended_next_step",
                payload_dict["recommended_next_step"],
            ),
            input_count=_decimal_from_payload("input_count", payload_dict["input_count"]),
            blocked_count=_decimal_from_payload(
                "blocked_count",
                payload_dict["blocked_count"],
            ),
            watch_count=_decimal_from_payload("watch_count", payload_dict["watch_count"]),
            pass_count=_decimal_from_payload("pass_count", payload_dict["pass_count"]),
            missing_official_anchor_count=_decimal_from_payload(
                "missing_official_anchor_count",
                payload_dict["missing_official_anchor_count"],
            ),
            weak_source_family_independence_count=_decimal_from_payload(
                "weak_source_family_independence_count",
                payload_dict["weak_source_family_independence_count"],
            ),
            stale_evidence_count=_decimal_from_payload(
                "stale_evidence_count",
                payload_dict["stale_evidence_count"],
            ),
            contradiction_severity_count=_decimal_from_payload(
                "contradiction_severity_count",
                payload_dict["contradiction_severity_count"],
            ),
            unattributed_probability_move_count=_decimal_from_payload(
                "unattributed_probability_move_count",
                payload_dict["unattributed_probability_move_count"],
            ),
            near_resolution_horizon_count=_decimal_from_payload(
                "near_resolution_horizon_count",
                payload_dict["near_resolution_horizon_count"],
            ),
            specialist_uncertainty_count=_decimal_from_payload(
                "specialist_uncertainty_count",
                payload_dict["specialist_uncertainty_count"],
            ),
            highest_priority_score=_decimal_from_payload(
                "highest_priority_score",
                payload_dict["highest_priority_score"],
            ),
            rows=rows,
            reason_codes=_string_tuple_from_payload(
                "reason_codes",
                payload_dict["reason_codes"],
            ),
            derived_validation_digest=_payload_string(
                "derived_validation_digest",
                payload_dict["derived_validation_digest"],
            ),
            paper_only=_payload_bool("paper_only", payload_dict["paper_only"]),
            report_only=_payload_bool("report_only", payload_dict["report_only"]),
            readonly=_payload_bool("readonly", payload_dict["readonly"]),
        )


_REPORT_PAYLOAD_FIELDS = (
    "config_version",
    "status",
    "recommended_next_step",
    "input_count",
    "blocked_count",
    "watch_count",
    "pass_count",
    "missing_official_anchor_count",
    "weak_source_family_independence_count",
    "stale_evidence_count",
    "contradiction_severity_count",
    "unattributed_probability_move_count",
    "near_resolution_horizon_count",
    "specialist_uncertainty_count",
    "highest_priority_score",
    "rows",
    "reason_codes",
    "derived_validation_digest",
    "paper_only",
    "report_only",
    "readonly",
)
_ROW_PAYLOAD_FIELDS = (
    "packet_ref",
    "question_ref",
    "specialist_ref",
    "priority_rank",
    "priority_score",
    "official_anchor_gap_score",
    "source_family_independence_gap_score",
    "stale_evidence_score",
    "contradiction_severity_score",
    "unattributed_probability_move",
    "resolution_horizon_score",
    "specialist_uncertainty_score",
    "official_anchor_count",
    "source_family_count",
    "freshest_evidence_age_hours",
    "hours_to_resolution",
    "triage_status",
    "recommended_research_action",
    "reason_codes",
    "paper_only",
    "report_only",
    "readonly",
)


def build_research_packet_source_gap_triage_v2_report(
    rows: object,
    *,
    config: ResearchPacketSourceGapTriageV2Config | None = None,
) -> ResearchPacketSourceGapTriageV2Report:
    if config is None:
        config = ResearchPacketSourceGapTriageV2Config()
    if type(config) is not ResearchPacketSourceGapTriageV2Config:
        raise ValueError("config must be a ResearchPacketSourceGapTriageV2Config")
    _require_hard_flags(config)
    source_rows = _normalize_input_rows(rows)
    ranked_rows = tuple(
        _ranked_row(row, rank=index + 1)
        for index, row in enumerate(
            sorted(
                (_unranked_row(item, config=config) for item in source_rows),
                key=_row_sort_key,
            ),
        )
    )
    reason_codes = _report_reason_codes(ranked_rows)
    status = _report_status(ranked_rows)
    return ResearchPacketSourceGapTriageV2Report(
        config_version=config.config_version,
        status=status,
        recommended_next_step=REPORT_NEXT_STEPS[status],
        input_count=_count(len(source_rows)),
        blocked_count=_status_count(ranked_rows, "blocked"),
        watch_count=_status_count(ranked_rows, "watch"),
        pass_count=_status_count(ranked_rows, "pass"),
        missing_official_anchor_count=_reason_count(
            ranked_rows,
            "missing_official_anchor",
        ),
        weak_source_family_independence_count=_reason_count(
            ranked_rows,
            "weak_source_family_independence",
        ),
        stale_evidence_count=_reason_count(ranked_rows, "stale_evidence"),
        contradiction_severity_count=_reason_count(
            ranked_rows,
            "contradiction_severity",
        ),
        unattributed_probability_move_count=_reason_count(
            ranked_rows,
            "unattributed_probability_move",
        ),
        near_resolution_horizon_count=_reason_count(
            ranked_rows,
            "near_resolution_horizon",
        ),
        specialist_uncertainty_count=_reason_count(
            ranked_rows,
            "specialist_uncertainty",
        ),
        highest_priority_score=_max_priority_score(ranked_rows),
        rows=ranked_rows,
        reason_codes=reason_codes,
    )


def research_packet_source_gap_triage_v2_payload(
    report: ResearchPacketSourceGapTriageV2Report,
) -> dict[str, object]:
    if type(report) is not ResearchPacketSourceGapTriageV2Report:
        raise ValueError("report must be a ResearchPacketSourceGapTriageV2Report")
    _require_hard_flags(report)
    _validate_report(report)
    return report.payload


def _unranked_row(
    subject: ResearchPacketSourceGapTriageV2Input,
    *,
    config: ResearchPacketSourceGapTriageV2Config,
) -> ResearchPacketSourceGapTriageV2Row:
    official_anchor_gap_score = _official_anchor_gap_score(subject, config)
    source_family_independence_gap_score = _source_family_independence_gap_score(
        subject,
        config,
    )
    stale_evidence_score = _stale_evidence_score(subject, config)
    resolution_horizon_score = _resolution_horizon_score(subject, config)
    priority_score = _priority_score(
        official_anchor_gap_score=official_anchor_gap_score,
        source_family_independence_gap_score=source_family_independence_gap_score,
        stale_evidence_score=stale_evidence_score,
        contradiction_severity_score=subject.contradiction_severity_score,
        unattributed_probability_move=subject.unattributed_probability_move,
        resolution_horizon_score=resolution_horizon_score,
        specialist_uncertainty_score=subject.specialist_uncertainty_score,
    )
    triage_status = _triage_status(priority_score, config)
    return ResearchPacketSourceGapTriageV2Row(
        packet_ref=subject.packet_ref,
        question_ref=subject.question_ref,
        specialist_ref=subject.specialist_ref,
        priority_rank=ONE,
        priority_score=priority_score,
        official_anchor_gap_score=official_anchor_gap_score,
        source_family_independence_gap_score=source_family_independence_gap_score,
        stale_evidence_score=stale_evidence_score,
        contradiction_severity_score=subject.contradiction_severity_score,
        unattributed_probability_move=subject.unattributed_probability_move,
        resolution_horizon_score=resolution_horizon_score,
        specialist_uncertainty_score=subject.specialist_uncertainty_score,
        official_anchor_count=subject.official_anchor_count,
        source_family_count=subject.source_family_count,
        freshest_evidence_age_hours=subject.freshest_evidence_age_hours,
        hours_to_resolution=subject.hours_to_resolution,
        triage_status=triage_status,
        recommended_research_action=ROW_ACTIONS[triage_status],
        reason_codes=_row_reason_codes(
            triage_status=triage_status,
            official_anchor_gap_score=official_anchor_gap_score,
            source_family_independence_gap_score=source_family_independence_gap_score,
            stale_evidence_score=stale_evidence_score,
            contradiction_severity_score=subject.contradiction_severity_score,
            unattributed_probability_move=subject.unattributed_probability_move,
            resolution_horizon_score=resolution_horizon_score,
            specialist_uncertainty_score=subject.specialist_uncertainty_score,
        ),
    )


def _ranked_row(
    row: ResearchPacketSourceGapTriageV2Row,
    *,
    rank: int,
) -> ResearchPacketSourceGapTriageV2Row:
    return replace(row, priority_rank=_count(rank))


def _row_sort_key(row: ResearchPacketSourceGapTriageV2Row) -> tuple[Decimal, str, str]:
    return (-row.priority_score, row.packet_ref, row.question_ref)


def _official_anchor_gap_score(
    subject: ResearchPacketSourceGapTriageV2Input,
    config: ResearchPacketSourceGapTriageV2Config,
) -> Decimal:
    if subject.official_anchor_count >= config.min_official_anchor_count:
        return ZERO
    gap = config.min_official_anchor_count - subject.official_anchor_count
    return _clamp_probability(gap / config.min_official_anchor_count)


def _source_family_independence_gap_score(
    subject: ResearchPacketSourceGapTriageV2Input,
    config: ResearchPacketSourceGapTriageV2Config,
) -> Decimal:
    if subject.source_family_count >= config.min_source_family_count:
        return ZERO
    gap = config.min_source_family_count - subject.source_family_count
    return _clamp_probability(gap / config.min_source_family_count)


def _stale_evidence_score(
    subject: ResearchPacketSourceGapTriageV2Input,
    config: ResearchPacketSourceGapTriageV2Config,
) -> Decimal:
    if subject.freshest_evidence_age_hours <= config.fresh_evidence_age_hours:
        return ZERO
    elapsed = subject.freshest_evidence_age_hours - config.fresh_evidence_age_hours
    return _clamp_probability(elapsed / config.stale_evidence_span_hours)


def _resolution_horizon_score(
    subject: ResearchPacketSourceGapTriageV2Input,
    config: ResearchPacketSourceGapTriageV2Config,
) -> Decimal:
    if subject.hours_to_resolution <= config.near_resolution_hours:
        return ONE
    if subject.hours_to_resolution >= config.safe_resolution_hours:
        return ZERO
    span = config.safe_resolution_hours - config.near_resolution_hours
    remaining = config.safe_resolution_hours - subject.hours_to_resolution
    return _clamp_probability(remaining / span)


def _priority_score(
    *,
    official_anchor_gap_score: Decimal,
    source_family_independence_gap_score: Decimal,
    stale_evidence_score: Decimal,
    contradiction_severity_score: Decimal,
    unattributed_probability_move: Decimal,
    resolution_horizon_score: Decimal,
    specialist_uncertainty_score: Decimal,
) -> Decimal:
    return _clamp_probability(
        (official_anchor_gap_score * OFFICIAL_ANCHOR_WEIGHT)
        + (source_family_independence_gap_score * SOURCE_FAMILY_WEIGHT)
        + (stale_evidence_score * STALE_EVIDENCE_WEIGHT)
        + (contradiction_severity_score * CONTRADICTION_WEIGHT)
        + (unattributed_probability_move * UNATTRIBUTED_MOVE_WEIGHT)
        + (resolution_horizon_score * RESOLUTION_HORIZON_WEIGHT)
        + (specialist_uncertainty_score * SPECIALIST_UNCERTAINTY_WEIGHT),
    )


def _triage_status(
    priority_score: Decimal,
    config: ResearchPacketSourceGapTriageV2Config,
) -> str:
    if priority_score >= config.blocked_priority_score:
        return "blocked"
    if priority_score >= config.watch_priority_score:
        return "watch"
    return "pass"


def _row_reason_codes(
    *,
    triage_status: str,
    official_anchor_gap_score: Decimal,
    source_family_independence_gap_score: Decimal,
    stale_evidence_score: Decimal,
    contradiction_severity_score: Decimal,
    unattributed_probability_move: Decimal,
    resolution_horizon_score: Decimal,
    specialist_uncertainty_score: Decimal,
) -> tuple[str, ...]:
    codes = [f"source_gap_triage_status_{triage_status}"]
    if official_anchor_gap_score > ZERO:
        codes.append("missing_official_anchor")
    if source_family_independence_gap_score > ZERO:
        codes.append("weak_source_family_independence")
    if stale_evidence_score > ZERO:
        codes.append("stale_evidence")
    if contradiction_severity_score > ZERO:
        codes.append("contradiction_severity")
    if unattributed_probability_move > ZERO:
        codes.append("unattributed_probability_move")
    if resolution_horizon_score > ZERO:
        codes.append("near_resolution_horizon")
    if specialist_uncertainty_score > ZERO:
        codes.append("specialist_uncertainty")
    return tuple(codes)


def _report_reason_codes(rows: tuple[ResearchPacketSourceGapTriageV2Row, ...]) -> tuple[str, ...]:
    if not rows:
        return ("source_gap_triage_no_inputs",)
    status = _report_status(rows)
    codes = [f"source_gap_triage_status_{status}"]
    row_codes = {code for row in rows for code in row.reason_codes}
    for code in TRIAGE_REASON_ORDER:
        if code in row_codes:
            codes.append(code)
    return tuple(codes)


def _report_status(rows: tuple[ResearchPacketSourceGapTriageV2Row, ...]) -> str:
    if not rows:
        return "blocked"
    if any(row.triage_status == "blocked" for row in rows):
        return "blocked"
    if any(row.triage_status == "watch" for row in rows):
        return "watch"
    return "pass"


def _status_count(rows: tuple[ResearchPacketSourceGapTriageV2Row, ...], status: str) -> Decimal:
    return _count(sum(1 for row in rows if row.triage_status == status))


def _reason_count(
    rows: tuple[ResearchPacketSourceGapTriageV2Row, ...],
    reason_code: str,
) -> Decimal:
    return _count(sum(1 for row in rows if reason_code in row.reason_codes))


def _max_priority_score(rows: tuple[ResearchPacketSourceGapTriageV2Row, ...]) -> Decimal:
    if not rows:
        return ZERO
    return max(row.priority_score for row in rows)


def _validate_row(row: ResearchPacketSourceGapTriageV2Row) -> None:
    expected_priority_score = _priority_score(
        official_anchor_gap_score=row.official_anchor_gap_score,
        source_family_independence_gap_score=row.source_family_independence_gap_score,
        stale_evidence_score=row.stale_evidence_score,
        contradiction_severity_score=row.contradiction_severity_score,
        unattributed_probability_move=row.unattributed_probability_move,
        resolution_horizon_score=row.resolution_horizon_score,
        specialist_uncertainty_score=row.specialist_uncertainty_score,
    )
    if row.priority_score != expected_priority_score:
        raise ValueError("priority_score must match source gap drivers")
    if row.triage_status == "blocked":
        expected_status = "blocked"
    elif row.triage_status == "watch":
        expected_status = "watch"
    else:
        expected_status = "pass"
    if row.triage_status != expected_status:
        raise ValueError("triage_status must match priority_score")
    if row.recommended_research_action != ROW_ACTIONS[row.triage_status]:
        raise ValueError("recommended_research_action must match triage_status")
    if row.reason_codes != _row_reason_codes(
        triage_status=row.triage_status,
        official_anchor_gap_score=row.official_anchor_gap_score,
        source_family_independence_gap_score=row.source_family_independence_gap_score,
        stale_evidence_score=row.stale_evidence_score,
        contradiction_severity_score=row.contradiction_severity_score,
        unattributed_probability_move=row.unattributed_probability_move,
        resolution_horizon_score=row.resolution_horizon_score,
        specialist_uncertainty_score=row.specialist_uncertainty_score,
    ):
        raise ValueError("reason_codes must match source gap drivers")


def _validate_report(report: ResearchPacketSourceGapTriageV2Report) -> None:
    for row in report.rows:
        _validate_row(row)
    if report.derived_validation_digest != _derived_validation_digest(report):
        raise ValueError("derived_validation_digest must match report fields")
    expected_status = _report_status(report.rows)
    if report.status != expected_status:
        raise ValueError("status must match rows")
    if report.recommended_next_step != REPORT_NEXT_STEPS[report.status]:
        raise ValueError("recommended_next_step must match status")
    if report.input_count != _count(len(report.rows)):
        raise ValueError("input_count must match rows")
    if report.blocked_count != _status_count(report.rows, "blocked"):
        raise ValueError("blocked_count must match rows")
    if report.watch_count != _status_count(report.rows, "watch"):
        raise ValueError("watch_count must match rows")
    if report.pass_count != _status_count(report.rows, "pass"):
        raise ValueError("pass_count must match rows")
    if report.missing_official_anchor_count != _reason_count(
        report.rows,
        "missing_official_anchor",
    ):
        raise ValueError("missing_official_anchor_count must match rows")
    if report.weak_source_family_independence_count != _reason_count(
        report.rows,
        "weak_source_family_independence",
    ):
        raise ValueError("weak_source_family_independence_count must match rows")
    if report.stale_evidence_count != _reason_count(report.rows, "stale_evidence"):
        raise ValueError("stale_evidence_count must match rows")
    if report.contradiction_severity_count != _reason_count(
        report.rows,
        "contradiction_severity",
    ):
        raise ValueError("contradiction_severity_count must match rows")
    if report.unattributed_probability_move_count != _reason_count(
        report.rows,
        "unattributed_probability_move",
    ):
        raise ValueError("unattributed_probability_move_count must match rows")
    if report.near_resolution_horizon_count != _reason_count(
        report.rows,
        "near_resolution_horizon",
    ):
        raise ValueError("near_resolution_horizon_count must match rows")
    if report.specialist_uncertainty_count != _reason_count(
        report.rows,
        "specialist_uncertainty",
    ):
        raise ValueError("specialist_uncertainty_count must match rows")
    if report.highest_priority_score != _max_priority_score(report.rows):
        raise ValueError("highest_priority_score must match rows")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")


def _normalize_input_rows(rows: object) -> tuple[ResearchPacketSourceGapTriageV2Input, ...]:
    if isinstance(rows, (str, bytes)) or not hasattr(rows, "__iter__"):
        raise ValueError("rows must be an iterable of ResearchPacketSourceGapTriageV2Input")
    normalized = tuple(rows)
    for row in normalized:
        if type(row) is not ResearchPacketSourceGapTriageV2Input:
            raise ValueError("rows must be ResearchPacketSourceGapTriageV2Input values")
        _require_hard_flags(row)
    return normalized


def _normalize_rows(rows: object) -> tuple[ResearchPacketSourceGapTriageV2Row, ...]:
    if isinstance(rows, (str, bytes)) or not hasattr(rows, "__iter__"):
        raise ValueError("rows must be an iterable of ResearchPacketSourceGapTriageV2Row")
    normalized = tuple(rows)
    for row in normalized:
        if type(row) is not ResearchPacketSourceGapTriageV2Row:
            raise ValueError("rows must be ResearchPacketSourceGapTriageV2Row values")
        _require_hard_flags(row)
    expected_ranks = tuple(_count(index + 1) for index in range(len(normalized)))
    actual_ranks = tuple(row.priority_rank for row in normalized)
    if actual_ranks != expected_ranks:
        raise ValueError("priority_rank must match row order")
    return normalized


def _normalize_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    if value.as_tuple().exponent < SCORE_QUANT.as_tuple().exponent:
        raise ValueError(f"{field_name} must not exceed six decimal places")
    return _q(value)


def _normalize_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _normalize_positive_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _normalize_probability(field_name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized < ZERO or normalized > ONE:
        raise ValueError(f"{field_name} must be between 0.000000 and 1.000000")
    return normalized


def _normalize_derived_validation_digest(value: object) -> str:
    if type(value) is not str:
        raise ValueError("derived_validation_digest must be a string")
    if len(value) != 64 or value.lower() != value:
        raise ValueError("derived_validation_digest must be a lowercase sha256 digest")
    try:
        int(value, 16)
    except ValueError as exc:
        raise ValueError("derived_validation_digest must be a lowercase sha256 digest") from exc
    return value


def _normalize_reason_codes(values: object, *, allow_empty: bool) -> tuple[str, ...]:
    if isinstance(values, (str, bytes)) or not hasattr(values, "__iter__"):
        raise ValueError("reason_codes must contain supported reason codes")
    reason_codes = tuple(values)
    if not allow_empty and not reason_codes:
        raise ValueError("reason_codes must not be empty")
    if len(set(reason_codes)) != len(reason_codes):
        raise ValueError("reason_codes must not contain duplicates")
    for code in reason_codes:
        _require_choice("reason_codes", code, REASON_CODES)
    return reason_codes


def _count(value: int) -> Decimal:
    return _q(Decimal(value))


def _q(value: Decimal) -> Decimal:
    return value.quantize(SCORE_QUANT)


def _clamp_probability(value: Decimal) -> Decimal:
    if value <= ZERO:
        return ZERO
    if value >= ONE:
        return ONE
    return _q(value)


def _require_choice(
    field_name: str,
    value: object,
    allowed_values: tuple[str, ...],
) -> None:
    _require_canonical_string(field_name, value)
    if value not in allowed_values:
        raise ValueError(f"{field_name} must be one of {allowed_values!r}")


def _require_identifier(field_name: str, value: object) -> None:
    _require_canonical_string(field_name, value)
    if any(character.isspace() for character in value):
        raise ValueError(f"{field_name} must not contain whitespace")


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a non-empty canonical string")
    if _mentions_unsafe_public_term(value):
        raise ValueError(f"unsafe public payload value in {field_name}: {value}")


def _require_hard_flags(value: object) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if getattr(value, field_name, None) is not True:
            raise ValueError(f"{field_name} must be True")


def _reject_unsafe_public_payload(label: str, payload: object) -> None:
    if hasattr(payload, "__dataclass_fields__") and not isinstance(payload, type):
        _reject_unsafe_public_payload(label, asdict(payload))
        return
    if isinstance(payload, dict):
        for key, value in payload.items():
            if type(key) is not str:
                raise ValueError("public payload keys must be strings")
            if _mentions_unsafe_public_term(key):
                raise ValueError(f"unsafe public payload key in {label}: {key}")
            _reject_unsafe_public_payload(label, value)
        return
    if isinstance(payload, (list, tuple)):
        for item in payload:
            _reject_unsafe_public_payload(label, item)
        return
    if type(payload) is str and _mentions_unsafe_public_term(payload):
        raise ValueError(f"unsafe public payload value in {label}: {payload}")
    if type(payload) in (int, float):
        raise ValueError("public payload numeric values must be Decimal strings")


def _mentions_unsafe_public_term(value: str) -> bool:
    tokens = _public_tokens(value.lower())
    return any(term in tokens for term in UNSAFE_PUBLIC_TERMS)


def _public_tokens(value: str) -> tuple[str, ...]:
    tokens: list[str] = []
    current: list[str] = []
    for character in value:
        if ("a" <= character <= "z") or ("0" <= character <= "9"):
            current.append(character)
            continue
        if current:
            tokens.append("".join(current))
            current = []
    if current:
        tokens.append("".join(current))
    return tuple(tokens)


def _payload_value(value: Any) -> Any:
    if type(value) in (int, float):
        raise ValueError("public payload numeric values must be Decimal strings")
    if type(value) is Decimal:
        return str(_q(value))
    if isinstance(value, tuple):
        return [_payload_value(item) for item in value]
    if isinstance(value, list):
        return [_payload_value(item) for item in value]
    if isinstance(value, dict):
        _reject_unsafe_public_payload("source gap triage payload", value)
        return {str(key): _payload_value(item) for key, item in value.items()}
    return value


def _payload_dict(label: str, value: object) -> dict[str, object]:
    if type(value) is not dict:
        raise ValueError(f"{label} must be an object")
    for key in value:
        if type(key) is not str:
            raise ValueError(f"{label} keys must be strings")
    return value


def _require_payload_fields(payload: dict[str, object], fields: tuple[str, ...]) -> None:
    if tuple(payload.keys()) != fields:
        raise ValueError("payload fields must match public contract")


def _row_from_payload(value: object) -> ResearchPacketSourceGapTriageV2Row:
    payload = _payload_dict("row", value)
    _require_payload_fields(payload, _ROW_PAYLOAD_FIELDS)
    return ResearchPacketSourceGapTriageV2Row(
        packet_ref=_payload_string("packet_ref", payload["packet_ref"]),
        question_ref=_payload_string("question_ref", payload["question_ref"]),
        specialist_ref=_payload_string("specialist_ref", payload["specialist_ref"]),
        priority_rank=_decimal_from_payload("priority_rank", payload["priority_rank"]),
        priority_score=_decimal_from_payload("priority_score", payload["priority_score"]),
        official_anchor_gap_score=_decimal_from_payload(
            "official_anchor_gap_score",
            payload["official_anchor_gap_score"],
        ),
        source_family_independence_gap_score=_decimal_from_payload(
            "source_family_independence_gap_score",
            payload["source_family_independence_gap_score"],
        ),
        stale_evidence_score=_decimal_from_payload(
            "stale_evidence_score",
            payload["stale_evidence_score"],
        ),
        contradiction_severity_score=_decimal_from_payload(
            "contradiction_severity_score",
            payload["contradiction_severity_score"],
        ),
        unattributed_probability_move=_decimal_from_payload(
            "unattributed_probability_move",
            payload["unattributed_probability_move"],
        ),
        resolution_horizon_score=_decimal_from_payload(
            "resolution_horizon_score",
            payload["resolution_horizon_score"],
        ),
        specialist_uncertainty_score=_decimal_from_payload(
            "specialist_uncertainty_score",
            payload["specialist_uncertainty_score"],
        ),
        official_anchor_count=_decimal_from_payload(
            "official_anchor_count",
            payload["official_anchor_count"],
        ),
        source_family_count=_decimal_from_payload(
            "source_family_count",
            payload["source_family_count"],
        ),
        freshest_evidence_age_hours=_decimal_from_payload(
            "freshest_evidence_age_hours",
            payload["freshest_evidence_age_hours"],
        ),
        hours_to_resolution=_decimal_from_payload(
            "hours_to_resolution",
            payload["hours_to_resolution"],
        ),
        triage_status=_payload_string("triage_status", payload["triage_status"]),
        recommended_research_action=_payload_string(
            "recommended_research_action",
            payload["recommended_research_action"],
        ),
        reason_codes=_string_tuple_from_payload("reason_codes", payload["reason_codes"]),
        paper_only=_payload_bool("paper_only", payload["paper_only"]),
        report_only=_payload_bool("report_only", payload["report_only"]),
        readonly=_payload_bool("readonly", payload["readonly"]),
    )


def _payload_string(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    return value


def _payload_bool(field_name: str, value: object) -> bool:
    if value is not True:
        raise ValueError(f"{field_name} must be True")
    return True


def _string_tuple_from_payload(field_name: str, value: object) -> tuple[str, ...]:
    if not isinstance(value, list):
        raise ValueError(f"{field_name} must be a list")
    return tuple(_payload_string(field_name, item) for item in value)


def _decimal_from_payload(field_name: str, value: object) -> Decimal:
    if type(value) is not str:
        raise ValueError(f"{field_name} must use Decimal strings")
    try:
        decimal_value = Decimal(value)
    except InvalidOperation as exc:
        raise ValueError(f"{field_name} must use Decimal strings") from exc
    return _normalize_decimal(field_name, decimal_value)


def _derived_validation_digest(report: ResearchPacketSourceGapTriageV2Report) -> str:
    values = asdict(report)
    values.pop("derived_validation_digest", None)
    return hashlib.sha256(_canonical_payload(values).encode("utf-8")).hexdigest()


def _canonical_payload(value: object) -> str:
    if type(value) is Decimal:
        return f"decimal:{_q(value)}"
    if type(value) is str:
        return f"string:{len(value)}:{value}"
    if type(value) is bool:
        return f"bool:{value}"
    if value is None:
        return "none"
    if isinstance(value, tuple):
        return "[" + ",".join(_canonical_payload(item) for item in value) + "]"
    if isinstance(value, list):
        return "[" + ",".join(_canonical_payload(item) for item in value) + "]"
    if isinstance(value, dict):
        parts = []
        for key in sorted(value):
            if type(key) is not str:
                raise ValueError("canonical payload keys must be strings")
            parts.append(f"{_canonical_payload(key)}:{_canonical_payload(value[key])}")
        return "{" + ",".join(parts) + "}"
    raise ValueError("canonical payload value is not supported")
