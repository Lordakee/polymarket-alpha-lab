"""Pure report-only reducer for cross-team disagreement arbitration readiness."""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable
from dataclasses import dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
import json
from typing import Any


__all__ = (
    "DEFAULT_RESEARCH_STRATEGY_CROSS_TEAM_DISAGREEMENT_ARBITRATION_REPORT_CONFIG_VERSION",
    "ARBITRATION_READINESS_STATUSES",
    "ResearchStrategyCrossTeamDisagreementArbitrationConfig",
    "ResearchStrategyCrossTeamDisagreementArbitrationInput",
    "ResearchStrategyCrossTeamDisagreementArbitrationReasonCodeCount",
    "ResearchStrategyCrossTeamDisagreementArbitrationReport",
    "ResearchStrategyCrossTeamDisagreementArbitrationRow",
    "build_research_strategy_cross_team_disagreement_arbitration_report",
    "research_strategy_cross_team_disagreement_arbitration_report_digest",
    "research_strategy_cross_team_disagreement_arbitration_report_payload",
)


DEFAULT_RESEARCH_STRATEGY_CROSS_TEAM_DISAGREEMENT_ARBITRATION_REPORT_CONFIG_VERSION = (
    "research-strategy-cross-team-disagreement-arbitration-report-v0"
)
ARBITRATION_READINESS_STATUSES = ("pass", "watch", "block")
QUANTUM = Decimal("0.000001")
COUNT_QUANTUM = Decimal("1.000000")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
SECONDS_PER_DAY = Decimal("86400.000000")
MICROSECONDS_PER_SECOND = Decimal("1000000.000000")
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
STATUS_WEIGHT = {
    "block": Decimal("2.000000"),
    "watch": Decimal("1.000000"),
    "pass": Decimal("0.000000"),
}
NO_INPUTS_REASON = "cross_team_disagreement_arbitration_no_inputs"
CLEAR_REASON = "cross_team_disagreement_arbitration_clear"
REPORT_STATUS_REASONS = (
    "cross_team_disagreement_arbitration_pass",
    "cross_team_disagreement_arbitration_watch",
    "cross_team_disagreement_arbitration_block",
)
ROW_REASON_PRIORITY = (
    "disagreement_severity_block",
    "disagreement_severity_watch",
    "evidence_maturity_block",
    "evidence_maturity_watch",
    "manual_escalation_urgency_block",
    "manual_escalation_urgency_watch",
    "queue_age_block",
    "queue_age_watch",
    "source_conflict_pressure_block",
    "source_conflict_pressure_watch",
    "specialist_lane_coverage_block",
    "specialist_lane_coverage_watch",
    CLEAR_REASON,
)
REPORT_REASON_PRIORITY = (
    *REPORT_STATUS_REASONS,
    NO_INPUTS_REASON,
    *ROW_REASON_PRIORITY,
)
REASON_CODES = tuple(dict.fromkeys(REPORT_REASON_PRIORITY))


def _join_parts(*parts: str) -> str:
    return "".join(parts)


UNSAFE_TEXT_PARTS = (
    _join_parts("raw", "_candidate", "_id"),
    _join_parts("candidate", "_id"),
    _join_parts("market", "_id"),
    _join_parts("market", "_sl", "ug"),
    _join_parts("ques", "tion"),
    _join_parts("source", "_u", "rl"),
    _join_parts("source", "_te", "xt"),
    _join_parts("d", "sn"),
    _join_parts("table", "_name"),
    _join_parts("private", "_token"),
    _join_parts("wal", "let"),
    _join_parts("au", "th"),
    _join_parts("or", "der"),
    _join_parts("li", "ve"),
    _join_parts("tra", "ding"),
    _join_parts("position", "_size"),
    _join_parts("b", "uy"),
    _join_parts("se", "ll"),
    _join_parts("reco", "mmend"),
    _join_parts("req", "uests"),
    _join_parts("ht", "tp"),
    _join_parts("so", "cket"),
    _join_parts("sub", "process"),
    _join_parts("net", "work"),
    _join_parts("api", "_key"),
    _join_parts("sec", "ret"),
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
class ResearchStrategyCrossTeamDisagreementArbitrationConfig(_FinalPublicDataclass):
    config_version: str = (
        DEFAULT_RESEARCH_STRATEGY_CROSS_TEAM_DISAGREEMENT_ARBITRATION_REPORT_CONFIG_VERSION
    )
    disagreement_severity_watch_threshold: Decimal = Decimal("0.250000")
    disagreement_severity_block_threshold: Decimal = Decimal("0.750000")
    evidence_maturity_watch_threshold: Decimal = Decimal("0.800000")
    evidence_maturity_block_threshold: Decimal = Decimal("0.500000")
    source_conflict_pressure_watch_threshold: Decimal = Decimal("0.350000")
    source_conflict_pressure_block_threshold: Decimal = Decimal("0.700000")
    specialist_lane_coverage_watch_threshold: Decimal = Decimal("1.000000")
    specialist_lane_coverage_block_threshold: Decimal = Decimal("0.500000")
    queue_age_watch_seconds: Decimal = Decimal("86400.000000")
    queue_age_block_seconds: Decimal = Decimal("259200.000000")
    manual_escalation_urgency_watch_threshold: Decimal = Decimal("0.500000")
    manual_escalation_urgency_block_threshold: Decimal = Decimal("0.850000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchStrategyCrossTeamDisagreementArbitrationConfig,
            "config",
        )
        _require_canonical_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_STRATEGY_CROSS_TEAM_DISAGREEMENT_ARBITRATION_REPORT_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "disagreement_severity_watch_threshold",
            "disagreement_severity_block_threshold",
            "evidence_maturity_watch_threshold",
            "evidence_maturity_block_threshold",
            "source_conflict_pressure_watch_threshold",
            "source_conflict_pressure_block_threshold",
            "specialist_lane_coverage_watch_threshold",
            "specialist_lane_coverage_block_threshold",
            "manual_escalation_urgency_watch_threshold",
            "manual_escalation_urgency_block_threshold",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in ("queue_age_watch_seconds", "queue_age_block_seconds"):
            object.__setattr__(
                self,
                field_name,
                _normalize_positive_decimal(field_name, getattr(self, field_name)),
            )
        _require_less_than(
            "disagreement_severity_watch_threshold",
            self.disagreement_severity_watch_threshold,
            self.disagreement_severity_block_threshold,
        )
        _require_less_than(
            "evidence_maturity_block_threshold",
            self.evidence_maturity_block_threshold,
            self.evidence_maturity_watch_threshold,
        )
        _require_less_than(
            "source_conflict_pressure_watch_threshold",
            self.source_conflict_pressure_watch_threshold,
            self.source_conflict_pressure_block_threshold,
        )
        _require_less_than(
            "specialist_lane_coverage_block_threshold",
            self.specialist_lane_coverage_block_threshold,
            self.specialist_lane_coverage_watch_threshold,
        )
        _require_less_than(
            "queue_age_watch_seconds",
            self.queue_age_watch_seconds,
            self.queue_age_block_seconds,
        )
        _require_less_than(
            "manual_escalation_urgency_watch_threshold",
            self.manual_escalation_urgency_watch_threshold,
            self.manual_escalation_urgency_block_threshold,
        )
        _require_hard_flags("config", self)
        _reject_unsafe_public_payload("config", self)


@dataclass(frozen=True)
class ResearchStrategyCrossTeamDisagreementArbitrationInput(_FinalPublicDataclass):
    disagreement_key: str
    disagreement_severity_score: Decimal
    evidence_maturity_score: Decimal
    source_conflict_pressure_score: Decimal
    specialist_lane_count: Decimal
    required_specialist_lane_count: Decimal
    queued_at: datetime
    manual_escalation_urgency_score: Decimal
    reason_codes: tuple[str, ...] = ()
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchStrategyCrossTeamDisagreementArbitrationInput,
            "input",
        )
        _require_public_key("disagreement_key", self.disagreement_key)
        for field_name in (
            "disagreement_severity_score",
            "evidence_maturity_score",
            "source_conflict_pressure_score",
            "manual_escalation_urgency_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "specialist_lane_count",
            _normalize_nonnegative_count(
                "specialist_lane_count",
                self.specialist_lane_count,
            ),
        )
        object.__setattr__(
            self,
            "required_specialist_lane_count",
            _normalize_positive_count(
                "required_specialist_lane_count",
                self.required_specialist_lane_count,
            ),
        )
        if self.specialist_lane_count > self.required_specialist_lane_count:
            raise ValueError(
                "specialist_lane_count must be at most required_specialist_lane_count",
            )
        object.__setattr__(self, "queued_at", _as_utc("queued_at", self.queued_at))
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, allow_empty=True),
        )
        _require_hard_flags("input", self)
        _reject_unsafe_public_payload("input", self)


@dataclass(frozen=True)
class ResearchStrategyCrossTeamDisagreementArbitrationRow(_FinalPublicDataclass):
    aggregate_row_number: Decimal
    aggregate_row_hash: str
    status: str
    disagreement_severity_score: Decimal
    evidence_maturity_score: Decimal
    source_conflict_pressure_score: Decimal
    specialist_lane_count: Decimal
    required_specialist_lane_count: Decimal
    specialist_lane_coverage_score: Decimal
    queued_at: datetime
    queue_age_seconds: Decimal
    manual_escalation_urgency_score: Decimal
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchStrategyCrossTeamDisagreementArbitrationRow,
            "row",
        )
        object.__setattr__(
            self,
            "aggregate_row_number",
            _normalize_positive_count(
                "aggregate_row_number",
                self.aggregate_row_number,
            ),
        )
        _require_public_digest("aggregate_row_hash", self.aggregate_row_hash)
        _require_status("status", self.status)
        for field_name in (
            "disagreement_severity_score",
            "evidence_maturity_score",
            "source_conflict_pressure_score",
            "specialist_lane_coverage_score",
            "manual_escalation_urgency_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "specialist_lane_count",
            _normalize_nonnegative_count(
                "specialist_lane_count",
                self.specialist_lane_count,
            ),
        )
        object.__setattr__(
            self,
            "required_specialist_lane_count",
            _normalize_positive_count(
                "required_specialist_lane_count",
                self.required_specialist_lane_count,
            ),
        )
        object.__setattr__(self, "queued_at", _as_utc("queued_at", self.queued_at))
        object.__setattr__(
            self,
            "queue_age_seconds",
            _normalize_nonnegative_decimal("queue_age_seconds", self.queue_age_seconds),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        _validate_row(self)
        _require_hard_flags("row", self)
        _reject_unsafe_public_payload("row", self)


@dataclass(frozen=True)
class ResearchStrategyCrossTeamDisagreementArbitrationReasonCodeCount(
    _FinalPublicDataclass,
):
    reason_code: str
    count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchStrategyCrossTeamDisagreementArbitrationReasonCodeCount,
            "reason_code_count",
        )
        _require_reason_code("reason_code", self.reason_code)
        object.__setattr__(
            self,
            "count",
            _normalize_positive_count("count", self.count),
        )
        _require_hard_flags("reason_code_count", self)
        _reject_unsafe_public_payload("reason_code_count", self)


@dataclass(frozen=True)
class ResearchStrategyCrossTeamDisagreementArbitrationReport(_FinalPublicDataclass):
    generated_at: datetime
    config_version: str
    arbitration_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    disagreement_severity_watch_count: Decimal
    low_evidence_maturity_count: Decimal
    source_conflict_pressure_count: Decimal
    specialist_lane_gap_count: Decimal
    queue_age_watch_count: Decimal
    manual_escalation_urgent_count: Decimal
    mean_disagreement_severity_score: Decimal
    max_disagreement_severity_score: Decimal
    mean_evidence_maturity_score: Decimal
    min_evidence_maturity_score: Decimal
    mean_source_conflict_pressure_score: Decimal
    max_source_conflict_pressure_score: Decimal
    mean_specialist_lane_coverage_score: Decimal
    min_specialist_lane_coverage_score: Decimal
    mean_queue_age_seconds: Decimal
    max_queue_age_seconds: Decimal
    mean_manual_escalation_urgency_score: Decimal
    max_manual_escalation_urgency_score: Decimal
    status: str
    public_digest: str
    reason_codes: tuple[str, ...]
    reason_code_counts: tuple[
        ResearchStrategyCrossTeamDisagreementArbitrationReasonCodeCount,
        ...,
    ]
    rows: tuple[ResearchStrategyCrossTeamDisagreementArbitrationRow, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchStrategyCrossTeamDisagreementArbitrationReport,
            "report",
        )
        object.__setattr__(
            self,
            "generated_at",
            _as_utc("generated_at", self.generated_at),
        )
        _require_canonical_string("config_version", self.config_version)
        for field_name in (
            "arbitration_count",
            "pass_count",
            "watch_count",
            "block_count",
            "disagreement_severity_watch_count",
            "low_evidence_maturity_count",
            "source_conflict_pressure_count",
            "specialist_lane_gap_count",
            "queue_age_watch_count",
            "manual_escalation_urgent_count",
            "mean_queue_age_seconds",
            "max_queue_age_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "mean_disagreement_severity_score",
            "max_disagreement_severity_score",
            "mean_evidence_maturity_score",
            "min_evidence_maturity_score",
            "mean_source_conflict_pressure_score",
            "max_source_conflict_pressure_score",
            "mean_specialist_lane_coverage_score",
            "min_specialist_lane_coverage_score",
            "mean_manual_escalation_urgency_score",
            "max_manual_escalation_urgency_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability_decimal(field_name, getattr(self, field_name)),
            )
        _require_status("status", self.status)
        _require_public_digest("public_digest", self.public_digest)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        _validate_report(self)
        _require_hard_flags("report", self)
        _reject_unsafe_public_payload("report", self)
        if self.public_digest != _computed_report_digest(self):
            raise ValueError("public_digest must match report values")


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


@dataclass(frozen=True)
class _RowValues:
    aggregate_row_hash: str
    status: str
    disagreement_severity_score: Decimal
    evidence_maturity_score: Decimal
    source_conflict_pressure_score: Decimal
    specialist_lane_count: Decimal
    required_specialist_lane_count: Decimal
    specialist_lane_coverage_score: Decimal
    queued_at: datetime
    queue_age_seconds: Decimal
    manual_escalation_urgency_score: Decimal
    reason_codes: tuple[str, ...]


def build_research_strategy_cross_team_disagreement_arbitration_report(
    disagreements: Iterable[ResearchStrategyCrossTeamDisagreementArbitrationInput],
    *,
    config: ResearchStrategyCrossTeamDisagreementArbitrationConfig,
    generated_at: datetime,
) -> ResearchStrategyCrossTeamDisagreementArbitrationReport:
    if type(config) is not ResearchStrategyCrossTeamDisagreementArbitrationConfig:
        raise ValueError(
            "config must be a ResearchStrategyCrossTeamDisagreementArbitrationConfig",
        )
    _require_hard_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    inputs = _normalize_inputs(disagreements)
    row_values = sorted(
        (
            _row_values_for_input(
                value,
                config=config,
                generated_at=generated_at_utc,
            )
            for value in inputs
        ),
        key=_row_values_sort_key,
    )
    rows = tuple(
        _row_from_values(_count(index), values)
        for index, values in enumerate(row_values, start=1)
    )
    values = _report_values(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        rows=rows,
    )
    return ResearchStrategyCrossTeamDisagreementArbitrationReport(
        **values,
        public_digest=_digest_from_mapping(values),
    )


def research_strategy_cross_team_disagreement_arbitration_report_digest(
    report: ResearchStrategyCrossTeamDisagreementArbitrationReport,
) -> str:
    if type(report) is not ResearchStrategyCrossTeamDisagreementArbitrationReport:
        raise ValueError(
            "report must be a ResearchStrategyCrossTeamDisagreementArbitrationReport",
        )
    _reject_unsafe_public_payload("report", report)
    _revalidate_report_for_payload(report)
    return _computed_report_digest(report)


def research_strategy_cross_team_disagreement_arbitration_report_payload(
    report: ResearchStrategyCrossTeamDisagreementArbitrationReport,
) -> dict[str, Any]:
    if type(report) is not ResearchStrategyCrossTeamDisagreementArbitrationReport:
        raise ValueError(
            "report must be a ResearchStrategyCrossTeamDisagreementArbitrationReport",
        )
    _reject_unsafe_public_payload("report", report)
    _revalidate_report_for_payload(report)
    payload = _json_ready(report)
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    _require_hard_flags("payload", _DictFlags(payload))
    _reject_unsafe_public_payload("payload", payload)
    return payload


def _row_values_for_input(
    value: ResearchStrategyCrossTeamDisagreementArbitrationInput,
    *,
    config: ResearchStrategyCrossTeamDisagreementArbitrationConfig,
    generated_at: datetime,
) -> _RowValues:
    queue_age_seconds = _queue_age_seconds(value.queued_at, generated_at)
    lane_coverage_score = _bounded_ratio(
        value.specialist_lane_count,
        value.required_specialist_lane_count,
    )
    reason_codes = _row_reason_codes(
        value,
        config=config,
        lane_coverage_score=lane_coverage_score,
        queue_age_seconds=queue_age_seconds,
    )
    return _RowValues(
        aggregate_row_hash=_public_hash(value.disagreement_key),
        status=_status_from_reason_codes(reason_codes),
        disagreement_severity_score=value.disagreement_severity_score,
        evidence_maturity_score=value.evidence_maturity_score,
        source_conflict_pressure_score=value.source_conflict_pressure_score,
        specialist_lane_count=value.specialist_lane_count,
        required_specialist_lane_count=value.required_specialist_lane_count,
        specialist_lane_coverage_score=lane_coverage_score,
        queued_at=value.queued_at,
        queue_age_seconds=queue_age_seconds,
        manual_escalation_urgency_score=value.manual_escalation_urgency_score,
        reason_codes=reason_codes,
    )


def _row_from_values(
    aggregate_row_number: Decimal,
    values: _RowValues,
) -> ResearchStrategyCrossTeamDisagreementArbitrationRow:
    return ResearchStrategyCrossTeamDisagreementArbitrationRow(
        aggregate_row_number=aggregate_row_number,
        aggregate_row_hash=values.aggregate_row_hash,
        status=values.status,
        disagreement_severity_score=values.disagreement_severity_score,
        evidence_maturity_score=values.evidence_maturity_score,
        source_conflict_pressure_score=values.source_conflict_pressure_score,
        specialist_lane_count=values.specialist_lane_count,
        required_specialist_lane_count=values.required_specialist_lane_count,
        specialist_lane_coverage_score=values.specialist_lane_coverage_score,
        queued_at=values.queued_at,
        queue_age_seconds=values.queue_age_seconds,
        manual_escalation_urgency_score=values.manual_escalation_urgency_score,
        reason_codes=values.reason_codes,
    )


def _row_reason_codes(
    value: ResearchStrategyCrossTeamDisagreementArbitrationInput,
    *,
    config: ResearchStrategyCrossTeamDisagreementArbitrationConfig,
    lane_coverage_score: Decimal,
    queue_age_seconds: Decimal,
) -> tuple[str, ...]:
    reasons = [*value.reason_codes]
    if value.disagreement_severity_score >= config.disagreement_severity_block_threshold:
        reasons.append("disagreement_severity_block")
    elif value.disagreement_severity_score >= config.disagreement_severity_watch_threshold:
        reasons.append("disagreement_severity_watch")
    if value.evidence_maturity_score <= config.evidence_maturity_block_threshold:
        reasons.append("evidence_maturity_block")
    elif value.evidence_maturity_score < config.evidence_maturity_watch_threshold:
        reasons.append("evidence_maturity_watch")
    if value.source_conflict_pressure_score >= config.source_conflict_pressure_block_threshold:
        reasons.append("source_conflict_pressure_block")
    elif value.source_conflict_pressure_score >= config.source_conflict_pressure_watch_threshold:
        reasons.append("source_conflict_pressure_watch")
    if lane_coverage_score <= config.specialist_lane_coverage_block_threshold:
        reasons.append("specialist_lane_coverage_block")
    elif lane_coverage_score < config.specialist_lane_coverage_watch_threshold:
        reasons.append("specialist_lane_coverage_watch")
    if queue_age_seconds >= config.queue_age_block_seconds:
        reasons.append("queue_age_block")
    elif queue_age_seconds >= config.queue_age_watch_seconds:
        reasons.append("queue_age_watch")
    if (
        value.manual_escalation_urgency_score
        >= config.manual_escalation_urgency_block_threshold
    ):
        reasons.append("manual_escalation_urgency_block")
    elif (
        value.manual_escalation_urgency_score
        >= config.manual_escalation_urgency_watch_threshold
    ):
        reasons.append("manual_escalation_urgency_watch")
    if not reasons:
        reasons.append(CLEAR_REASON)
    return _normalize_reason_codes("reason_codes", tuple(reasons))


def _status_from_reason_codes(reason_codes: tuple[str, ...]) -> str:
    if any(reason_code.endswith("_block") for reason_code in reason_codes):
        return "block"
    if any(reason_code.endswith("_watch") for reason_code in reason_codes):
        return "watch"
    return "pass"


def _rollup_status(
    rows: tuple[ResearchStrategyCrossTeamDisagreementArbitrationRow, ...],
) -> str:
    if not rows:
        return "block"
    if any(row.status == "block" for row in rows):
        return "block"
    if any(row.status == "watch" for row in rows):
        return "watch"
    return "pass"


def _report_reason_codes(
    rows: tuple[ResearchStrategyCrossTeamDisagreementArbitrationRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return (NO_INPUTS_REASON,)
    status = _rollup_status(rows)
    reasons = [f"cross_team_disagreement_arbitration_{status}"]
    present = frozenset(
        reason_code
        for row in rows
        for reason_code in row.reason_codes
        if reason_code != CLEAR_REASON
    )
    for reason_code in ROW_REASON_PRIORITY:
        if reason_code in present:
            reasons.append(reason_code)
    return tuple(reasons)


def _reason_code_counts(
    rows: tuple[ResearchStrategyCrossTeamDisagreementArbitrationRow, ...],
) -> tuple[ResearchStrategyCrossTeamDisagreementArbitrationReasonCodeCount, ...]:
    if not rows:
        return (
            ResearchStrategyCrossTeamDisagreementArbitrationReasonCodeCount(
                reason_code=NO_INPUTS_REASON,
                count=COUNT_QUANTUM,
            ),
        )
    counter: Counter[str] = Counter()
    for row in rows:
        counter.update(row.reason_codes)
    return tuple(
        ResearchStrategyCrossTeamDisagreementArbitrationReasonCodeCount(
            reason_code=reason_code,
            count=_count(count),
        )
        for reason_code, count in sorted(counter.items(), key=lambda item: (-item[1], item[0]))
    )


def _report_values(
    *,
    generated_at: datetime,
    config_version: str,
    rows: tuple[ResearchStrategyCrossTeamDisagreementArbitrationRow, ...],
) -> dict[str, Any]:
    return {
        "generated_at": generated_at,
        "config_version": config_version,
        "arbitration_count": _count(len(rows)),
        "pass_count": _status_count(rows, "pass"),
        "watch_count": _status_count(rows, "watch"),
        "block_count": _status_count(rows, "block"),
        "disagreement_severity_watch_count": _kind_count(
            rows,
            "disagreement_severity_",
        ),
        "low_evidence_maturity_count": _kind_count(rows, "evidence_maturity_"),
        "source_conflict_pressure_count": _kind_count(
            rows,
            "source_conflict_pressure_",
        ),
        "specialist_lane_gap_count": _kind_count(
            rows,
            "specialist_lane_coverage_",
        ),
        "queue_age_watch_count": _kind_count(rows, "queue_age_"),
        "manual_escalation_urgent_count": _kind_count(
            rows,
            "manual_escalation_urgency_",
        ),
        "mean_disagreement_severity_score": _mean(
            tuple(row.disagreement_severity_score for row in rows),
        ),
        "max_disagreement_severity_score": _max_decimal(
            tuple(row.disagreement_severity_score for row in rows),
        ),
        "mean_evidence_maturity_score": _mean(
            tuple(row.evidence_maturity_score for row in rows),
        ),
        "min_evidence_maturity_score": _min_decimal(
            tuple(row.evidence_maturity_score for row in rows),
        ),
        "mean_source_conflict_pressure_score": _mean(
            tuple(row.source_conflict_pressure_score for row in rows),
        ),
        "max_source_conflict_pressure_score": _max_decimal(
            tuple(row.source_conflict_pressure_score for row in rows),
        ),
        "mean_specialist_lane_coverage_score": _mean(
            tuple(row.specialist_lane_coverage_score for row in rows),
        ),
        "min_specialist_lane_coverage_score": _min_decimal(
            tuple(row.specialist_lane_coverage_score for row in rows),
        ),
        "mean_queue_age_seconds": _mean(tuple(row.queue_age_seconds for row in rows)),
        "max_queue_age_seconds": _max_decimal(
            tuple(row.queue_age_seconds for row in rows),
        ),
        "mean_manual_escalation_urgency_score": _mean(
            tuple(row.manual_escalation_urgency_score for row in rows),
        ),
        "max_manual_escalation_urgency_score": _max_decimal(
            tuple(row.manual_escalation_urgency_score for row in rows),
        ),
        "status": _rollup_status(rows),
        "reason_codes": _report_reason_codes(rows),
        "reason_code_counts": _reason_code_counts(rows),
        "rows": rows,
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }


def _normalize_inputs(
    values: Iterable[ResearchStrategyCrossTeamDisagreementArbitrationInput],
) -> tuple[ResearchStrategyCrossTeamDisagreementArbitrationInput, ...]:
    if isinstance(values, (str, bytes)):
        raise ValueError("disagreements must be an iterable")
    try:
        normalized = tuple(values)
    except TypeError as exc:
        raise ValueError("disagreements must be an iterable") from exc
    seen: set[str] = set()
    for value in normalized:
        if type(value) is not ResearchStrategyCrossTeamDisagreementArbitrationInput:
            raise ValueError(
                "disagreements must contain "
                "ResearchStrategyCrossTeamDisagreementArbitrationInput values",
            )
        _require_hard_flags("input", value)
        _reject_unsafe_public_payload("input", value)
        if value.disagreement_key in seen:
            raise ValueError("disagreements must not contain duplicate disagreement_key values")
        seen.add(value.disagreement_key)
    return normalized


def _normalize_rows(
    values: Iterable[ResearchStrategyCrossTeamDisagreementArbitrationRow],
) -> tuple[ResearchStrategyCrossTeamDisagreementArbitrationRow, ...]:
    if isinstance(values, (str, bytes)):
        raise ValueError("rows must be an iterable")
    try:
        rows = tuple(values)
    except TypeError as exc:
        raise ValueError("rows must be an iterable") from exc
    seen_hashes: set[str] = set()
    for row in rows:
        if type(row) is not ResearchStrategyCrossTeamDisagreementArbitrationRow:
            raise ValueError(
                "rows must contain "
                "ResearchStrategyCrossTeamDisagreementArbitrationRow values",
            )
        _require_hard_flags("row", row)
        _reject_unsafe_public_payload("row", row)
        if row.aggregate_row_hash in seen_hashes:
            raise ValueError("rows must not contain duplicate aggregate_row_hash values")
        seen_hashes.add(row.aggregate_row_hash)
    if rows != tuple(sorted(rows, key=_row_sort_key)):
        raise ValueError("rows must use canonical sequence")
    return rows


def _normalize_reason_code_counts(
    values: Iterable[ResearchStrategyCrossTeamDisagreementArbitrationReasonCodeCount],
) -> tuple[ResearchStrategyCrossTeamDisagreementArbitrationReasonCodeCount, ...]:
    if isinstance(values, (str, bytes)):
        raise ValueError("reason_code_counts must be an iterable")
    try:
        rows = tuple(values)
    except TypeError as exc:
        raise ValueError("reason_code_counts must be an iterable") from exc
    seen: set[str] = set()
    for row in rows:
        if type(row) is not ResearchStrategyCrossTeamDisagreementArbitrationReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "ResearchStrategyCrossTeamDisagreementArbitrationReasonCodeCount values",
            )
        _require_hard_flags("reason_code_count", row)
        _reject_unsafe_public_payload("reason_code_count", row)
        if row.reason_code in seen:
            raise ValueError("reason_code_counts must not contain duplicate reason_code values")
        seen.add(row.reason_code)
    return tuple(sorted(rows, key=lambda item: (-item.count, item.reason_code)))


def _row_sort_key(
    row: ResearchStrategyCrossTeamDisagreementArbitrationRow,
) -> tuple[Decimal, Decimal, Decimal, Decimal, str]:
    return (
        -STATUS_WEIGHT[row.status],
        -row.manual_escalation_urgency_score,
        -row.disagreement_severity_score,
        -row.queue_age_seconds,
        row.aggregate_row_hash,
    )


def _row_values_sort_key(values: _RowValues) -> tuple[Decimal, Decimal, Decimal, Decimal, str]:
    return (
        -STATUS_WEIGHT[values.status],
        -values.manual_escalation_urgency_score,
        -values.disagreement_severity_score,
        -values.queue_age_seconds,
        values.aggregate_row_hash,
    )


def _status_count(
    rows: tuple[ResearchStrategyCrossTeamDisagreementArbitrationRow, ...],
    status: str,
) -> Decimal:
    return _count(sum(1 for row in rows if row.status == status))


def _kind_count(
    rows: tuple[ResearchStrategyCrossTeamDisagreementArbitrationRow, ...],
    kind: str,
) -> Decimal:
    return _count(
        sum(
            1
            for row in rows
            if any(reason_code.startswith(kind) for reason_code in row.reason_codes)
        ),
    )


def _validate_row(row: ResearchStrategyCrossTeamDisagreementArbitrationRow) -> None:
    if row.specialist_lane_count > row.required_specialist_lane_count:
        raise ValueError(
            "specialist_lane_count must be at most required_specialist_lane_count",
        )
    if row.specialist_lane_coverage_score != _bounded_ratio(
        row.specialist_lane_count,
        row.required_specialist_lane_count,
    ):
        raise ValueError("specialist_lane_coverage_score must match counts")
    if row.status != _status_from_reason_codes(row.reason_codes):
        raise ValueError("status must match reason_codes")


def _validate_report(
    report: ResearchStrategyCrossTeamDisagreementArbitrationReport,
) -> None:
    rows = report.rows
    if report.arbitration_count != _count(len(rows)):
        raise ValueError("arbitration_count must match rows")
    if report.pass_count != _status_count(rows, "pass"):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _status_count(rows, "watch"):
        raise ValueError("watch_count must match rows")
    if report.block_count != _status_count(rows, "block"):
        raise ValueError("block_count must match rows")
    for field_name, kind in (
        ("disagreement_severity_watch_count", "disagreement_severity_"),
        ("low_evidence_maturity_count", "evidence_maturity_"),
        ("source_conflict_pressure_count", "source_conflict_pressure_"),
        ("specialist_lane_gap_count", "specialist_lane_coverage_"),
        ("queue_age_watch_count", "queue_age_"),
        ("manual_escalation_urgent_count", "manual_escalation_urgency_"),
    ):
        if getattr(report, field_name) != _kind_count(rows, kind):
            raise ValueError(f"{field_name} must match rows")
    expected_metrics = {
        "mean_disagreement_severity_score": _mean(
            tuple(row.disagreement_severity_score for row in rows),
        ),
        "max_disagreement_severity_score": _max_decimal(
            tuple(row.disagreement_severity_score for row in rows),
        ),
        "mean_evidence_maturity_score": _mean(
            tuple(row.evidence_maturity_score for row in rows),
        ),
        "min_evidence_maturity_score": _min_decimal(
            tuple(row.evidence_maturity_score for row in rows),
        ),
        "mean_source_conflict_pressure_score": _mean(
            tuple(row.source_conflict_pressure_score for row in rows),
        ),
        "max_source_conflict_pressure_score": _max_decimal(
            tuple(row.source_conflict_pressure_score for row in rows),
        ),
        "mean_specialist_lane_coverage_score": _mean(
            tuple(row.specialist_lane_coverage_score for row in rows),
        ),
        "min_specialist_lane_coverage_score": _min_decimal(
            tuple(row.specialist_lane_coverage_score for row in rows),
        ),
        "mean_queue_age_seconds": _mean(tuple(row.queue_age_seconds for row in rows)),
        "max_queue_age_seconds": _max_decimal(
            tuple(row.queue_age_seconds for row in rows),
        ),
        "mean_manual_escalation_urgency_score": _mean(
            tuple(row.manual_escalation_urgency_score for row in rows),
        ),
        "max_manual_escalation_urgency_score": _max_decimal(
            tuple(row.manual_escalation_urgency_score for row in rows),
        ),
    }
    for field_name, expected in expected_metrics.items():
        if getattr(report, field_name) != expected:
            raise ValueError(f"{field_name} must match rows")
    if report.status != _rollup_status(rows):
        raise ValueError("status must match rows")
    if report.reason_codes != _report_reason_codes(rows):
        raise ValueError("reason_codes must match rows")
    if report.reason_code_counts != _reason_code_counts(rows):
        raise ValueError("reason_code_counts must match rows")
    for index, row in enumerate(rows, start=1):
        if row.aggregate_row_number != _count(index):
            raise ValueError("aggregate_row_number must match rows")


def _revalidate_report_for_payload(
    report: ResearchStrategyCrossTeamDisagreementArbitrationReport,
) -> None:
    _require_exact_type(
        report,
        ResearchStrategyCrossTeamDisagreementArbitrationReport,
        "report",
    )
    _require_hard_flags("report", report)
    for row in report.rows:
        _require_exact_type(
            row,
            ResearchStrategyCrossTeamDisagreementArbitrationRow,
            "row",
        )
        _require_hard_flags("row", row)
    for row in report.reason_code_counts:
        _require_exact_type(
            row,
            ResearchStrategyCrossTeamDisagreementArbitrationReasonCodeCount,
            "reason_code_count",
        )
        _require_hard_flags("reason_code_count", row)
    _validate_report(report)
    if report.public_digest != _computed_report_digest(report):
        raise ValueError("public_digest must match report values")


def _queue_age_seconds(queued_at: datetime, generated_at: datetime) -> Decimal:
    value = _seconds_between(queued_at, generated_at)
    if value < ZERO:
        raise ValueError("generated_at must be at or after queued_at")
    return value


def _seconds_between(start: datetime, end: datetime) -> Decimal:
    delta = end - start
    whole_seconds = Decimal(delta.days) * SECONDS_PER_DAY + Decimal(delta.seconds)
    microseconds = Decimal(delta.microseconds) / MICROSECONDS_PER_SECOND
    with localcontext(DECIMAL_CONTEXT):
        return _quantize(whole_seconds + microseconds)


def _bounded_ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator <= ZERO:
        raise ValueError("denominator must be positive")
    with localcontext(DECIMAL_CONTEXT):
        value = _quantize(numerator / denominator)
    if value > ONE:
        return ONE
    if value < ZERO:
        return ZERO
    return value


def _mean(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return _quantize(sum(values, ZERO) / Decimal(len(values)))


def _max_decimal(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return ZERO
    return max(values)


def _min_decimal(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return ZERO
    return min(values)


def _count(value: int) -> Decimal:
    return Decimal(value).quantize(COUNT_QUANTUM)


def _public_hash(value: str) -> str:
    return sha256(value.encode("utf-8")).hexdigest()


def _computed_report_digest(
    report: ResearchStrategyCrossTeamDisagreementArbitrationReport,
) -> str:
    return _digest_from_mapping(
        {
            field.name: getattr(report, field.name)
            for field in fields(report)
            if field.name != "public_digest"
        },
    )


def _digest_from_mapping(value: dict[str, Any]) -> str:
    payload = json.dumps(
        _json_ready(value),
        allow_nan=False,
        separators=(",", ":"),
        sort_keys=True,
    )
    return sha256(payload.encode("utf-8")).hexdigest()


def _json_ready(value: Any) -> Any:
    if is_dataclass(value) and not isinstance(value, type):
        return {field.name: _json_ready(getattr(value, field.name)) for field in fields(value)}
    if isinstance(value, dict):
        return {str(key): _json_ready(item) for key, item in value.items()}
    if isinstance(value, tuple):
        return [_json_ready(item) for item in value]
    if isinstance(value, list):
        return [_json_ready(item) for item in value]
    if type(value) is Decimal:
        return format(value, "f")
    if type(value) is datetime:
        return value.isoformat()
    return value


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    offset = value.utcoffset()
    if value.tzinfo is None or offset is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _normalize_reason_codes(
    field_name: str,
    value: Iterable[str],
    *,
    allow_empty: bool = False,
) -> tuple[str, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError(f"{field_name} must be a tuple")
    try:
        values = tuple(value)
    except TypeError as exc:
        raise ValueError(f"{field_name} must be a tuple") from exc
    if not values and allow_empty:
        return ()
    if not values:
        raise ValueError(f"{field_name} must contain at least one value")
    if len(set(values)) != len(values):
        raise ValueError(f"{field_name} must not contain duplicates")
    for item in values:
        _require_reason_code(field_name, item)
    return tuple(reason_code for reason_code in REASON_CODES if reason_code in values)


def _require_reason_code(field_name: str, value: object) -> None:
    _require_canonical_string(field_name, value)
    if value not in REASON_CODES:
        raise ValueError(f"{field_name} contains an unsupported value")


def _require_public_key(field_name: str, value: object) -> None:
    _require_canonical_string(field_name, value)
    if _contains_unsafe_text(value):
        raise ValueError(f"{field_name} contains unsafe public text")


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")


def _require_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in ARBITRATION_READINESS_STATUSES:
        raise ValueError(f"{field_name} must be pass, watch, or block")


def _require_public_digest(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a digest string")
    if len(value) != 64 or any(character not in "0123456789abcdef" for character in value):
        raise ValueError(f"{field_name} must be a SHA-256 hex digest")


def _normalize_probability_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_nonnegative_decimal(field_name, value)
    if normalized > ONE:
        raise ValueError(f"{field_name} must be at most 1.000000")
    return normalized


def _normalize_positive_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_nonnegative_decimal(field_name, value)
    if normalized <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _normalize_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    normalized = _quantize(value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _normalize_nonnegative_count(field_name: str, value: object) -> Decimal:
    normalized = _normalize_nonnegative_decimal(field_name, value)
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{field_name} must be a whole Decimal")
    return normalized


def _normalize_positive_count(field_name: str, value: object) -> Decimal:
    normalized = _normalize_nonnegative_count(field_name, value)
    if normalized <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _quantize(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(QUANTUM)


def _require_less_than(field_name: str, left: Decimal, right: Decimal) -> None:
    if left >= right:
        raise ValueError(f"{field_name} must be less than its paired threshold")


def _require_exact_type(value: object, expected_type: type[object], label: str) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{label} must be a {expected_type.__name__}")


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if getattr(value, field_name, None) is not True:
            raise ValueError(f"{label}.{field_name} must be True")


def _reject_unsafe_public_payload(label: str, value: object) -> None:
    if type(value) is str:
        if _contains_unsafe_text(value):
            raise ValueError(f"{label} contains unsafe public value")
        return
    if is_dataclass(value) and not isinstance(value, type):
        for field in fields(value):
            _reject_unsafe_public_payload(f"{label}.{field.name}", getattr(value, field.name))
        return
    if isinstance(value, dict):
        for key, item in value.items():
            _reject_unsafe_public_payload(f"{label}.key", str(key))
            _reject_unsafe_public_payload(f"{label}.{key}", item)
        return
    if isinstance(value, (tuple, list)):
        for item in value:
            _reject_unsafe_public_payload(label, item)


def _contains_unsafe_text(value: str) -> bool:
    lowered = value.lower()
    return any(fragment in lowered for fragment in UNSAFE_TEXT_PARTS)
