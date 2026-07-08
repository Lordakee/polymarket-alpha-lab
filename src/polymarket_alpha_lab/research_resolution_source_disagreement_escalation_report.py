"""Pure public report for resolution-source disagreement escalation."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation, localcontext
from hashlib import sha256
import json
from typing import Any


DEFAULT_CONFIG_VERSION = (
    "research-resolution-source-disagreement-escalation-report-v0"
)
PUBLIC_STATUSES = ("pass", "watch", "block")
COUNT_QUANT = Decimal("1")
SCORE_QUANT = Decimal("0.000001")
ZERO = Decimal("0")
ONE = Decimal("1")
DECIMAL_WEIGHT_CONFLICT = Decimal("0.250000")
DECIMAL_WEIGHT_RELIABILITY_SPREAD = Decimal("0.200000")
DECIMAL_WEIGHT_ORACLE_GAP = Decimal("0.200000")
DECIMAL_WEIGHT_DEADLINE = Decimal("0.154000")
DECIMAL_WEIGHT_SOURCE_CLASS_SHARE = Decimal("0.100000")
HIGH_CONFLICT_CONVEX_WEIGHT = Decimal("0.300000")
LOW_RISK_REVIEW_FLOOR = Decimal("0.100000")
RELIABILITY_GAP_FLOOR = Decimal("0.250000")
STATUS_RANK = {"block": 0, "watch": 1, "pass": 2}
UNSAFE_TEXT_FRAGMENTS = (
    "market" + "_slug",
    "market" + "_id",
    "market" + "_identifier",
    "source" + "_id",
    "source" + "_name",
    "source" + "_url",
    "raw" + "_text",
    "url",
    "private" + "_key",
    "wal" + "let",
    "au" + "th",
    "or" + "der",
    "credential",
    "secret",
    "token",
)


@dataclass(frozen=True)
class ResearchResolutionSourceDisagreementEscalationConfig:
    config_version: str = DEFAULT_CONFIG_VERSION
    watch_escalation_score: Decimal = Decimal("0.350000")
    block_escalation_score: Decimal = Decimal("0.650000")
    low_oracle_clarity_floor: Decimal = Decimal("0.500000")
    deadline_pressure_watch_hours: Decimal = Decimal("72.000000")
    deadline_pressure_block_hours: Decimal = Decimal("24.000000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not ResearchResolutionSourceDisagreementEscalationConfig:
            raise ValueError(
                "config must be a ResearchResolutionSourceDisagreementEscalationConfig",
            )
        _require_public_label("config_version", self.config_version)
        for field_name in (
            "watch_escalation_score",
            "block_escalation_score",
            "low_oracle_clarity_floor",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_probability_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "deadline_pressure_watch_hours",
            "deadline_pressure_block_hours",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_positive_score_decimal(field_name, getattr(self, field_name)),
            )
        if self.block_escalation_score <= self.watch_escalation_score:
            raise ValueError("block_escalation_score must exceed watch_escalation_score")
        if self.deadline_pressure_block_hours > self.deadline_pressure_watch_hours:
            raise ValueError(
                "deadline_pressure_block_hours must not exceed "
                "deadline_pressure_watch_hours",
            )
        _require_hard_flags("config", self)
        _reject_unsafe_public_payload("config", self)


@dataclass(frozen=True)
class ResearchResolutionSourceDisagreementEscalationInput:
    bucket_id: str
    evidence_conflict_score: Decimal
    weakest_source_class_reliability: Decimal
    strongest_source_class_reliability: Decimal
    oracle_clarity_score: Decimal
    hours_to_deadline: Decimal
    aggregate_evidence_count: Decimal
    disagreeing_source_class_count: Decimal
    source_class_count: Decimal
    observed_at: datetime
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not ResearchResolutionSourceDisagreementEscalationInput:
            raise ValueError(
                "input must be a ResearchResolutionSourceDisagreementEscalationInput",
            )
        _require_public_label("bucket_id", self.bucket_id)
        for field_name in (
            "evidence_conflict_score",
            "weakest_source_class_reliability",
            "strongest_source_class_reliability",
            "oracle_clarity_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_probability_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in ("hours_to_deadline",):
            object.__setattr__(
                self,
                field_name,
                _require_score_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "aggregate_evidence_count",
            "disagreeing_source_class_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_count_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "source_class_count",
            _require_positive_count_decimal("source_class_count", self.source_class_count),
        )
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        if self.weakest_source_class_reliability > self.strongest_source_class_reliability:
            raise ValueError(
                "weakest_source_class_reliability must not exceed "
                "strongest_source_class_reliability",
            )
        if self.disagreeing_source_class_count > self.source_class_count:
            raise ValueError(
                "disagreeing_source_class_count must not exceed source_class_count",
            )
        _require_hard_flags("input", self)
        _reject_unsafe_public_payload("input", self)


@dataclass(frozen=True)
class ResearchResolutionSourceDisagreementEscalationRow:
    bucket_id: str
    status: str
    evidence_conflict_score: Decimal
    weakest_source_class_reliability: Decimal
    strongest_source_class_reliability: Decimal
    source_class_reliability_spread: Decimal
    oracle_clarity_score: Decimal
    deadline_pressure_score: Decimal
    hours_to_deadline: Decimal
    aggregate_evidence_count: Decimal
    disagreeing_source_class_count: Decimal
    source_class_count: Decimal
    source_class_disagreement_share: Decimal
    escalation_score: Decimal
    observed_at: datetime
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not ResearchResolutionSourceDisagreementEscalationRow:
            raise ValueError(
                "row must be a ResearchResolutionSourceDisagreementEscalationRow",
            )
        _require_public_label("bucket_id", self.bucket_id)
        _require_status("status", self.status)
        for field_name in (
            "evidence_conflict_score",
            "weakest_source_class_reliability",
            "strongest_source_class_reliability",
            "source_class_reliability_spread",
            "oracle_clarity_score",
            "deadline_pressure_score",
            "source_class_disagreement_share",
            "escalation_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_probability_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "hours_to_deadline",
            _require_score_decimal("hours_to_deadline", self.hours_to_deadline),
        )
        for field_name in (
            "aggregate_evidence_count",
            "disagreeing_source_class_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_count_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "source_class_count",
            _require_positive_count_decimal("source_class_count", self.source_class_count),
        )
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, allow_empty=False),
        )
        _require_hard_flags("row", self)
        _reject_unsafe_public_payload("row", self)
        _validate_row(self)


@dataclass(frozen=True)
class ResearchResolutionSourceDisagreementEscalationReasonCodeCount:
    reason_code: str
    count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_public_label("reason_code", self.reason_code)
        object.__setattr__(self, "count", _require_positive_count_decimal("count", self.count))
        _require_hard_flags("reason_code_count", self)
        _reject_unsafe_public_payload("reason_code_count", self)


@dataclass(frozen=True)
class ResearchResolutionSourceDisagreementEscalationReport:
    generated_at: datetime
    config_version: str
    status: str
    input_count: Decimal
    row_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    aggregate_evidence_count: Decimal
    disagreeing_source_class_count: Decimal
    source_class_count: Decimal
    max_deadline_pressure_score: Decimal
    average_oracle_clarity_score: Decimal | None
    average_source_class_reliability_spread: Decimal | None
    max_escalation_score: Decimal
    average_escalation_score: Decimal | None
    rows: tuple[ResearchResolutionSourceDisagreementEscalationRow, ...]
    reason_code_counts: tuple[ResearchResolutionSourceDisagreementEscalationReasonCodeCount, ...]
    reason_codes: tuple[str, ...]
    report_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not ResearchResolutionSourceDisagreementEscalationReport:
            raise ValueError(
                "report must be a ResearchResolutionSourceDisagreementEscalationReport",
            )
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_label("config_version", self.config_version)
        _require_status("status", self.status)
        for field_name in (
            "input_count",
            "row_count",
            "pass_count",
            "watch_count",
            "block_count",
            "aggregate_evidence_count",
            "disagreeing_source_class_count",
            "source_class_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_count_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in ("max_deadline_pressure_score", "max_escalation_score"):
            object.__setattr__(
                self,
                field_name,
                _require_probability_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "average_oracle_clarity_score",
            "average_source_class_reliability_spread",
            "average_escalation_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_optional_probability_decimal(field_name, getattr(self, field_name)),
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
            _normalize_reason_codes("reason_codes", self.reason_codes, allow_empty=False),
        )
        _require_hard_flags("report", self)
        _reject_unsafe_public_payload("report", self)
        _validate_report(self)
        expected_digest = _report_digest(self)
        if self.report_digest:
            digest = _require_sha256_digest("report_digest", self.report_digest)
            object.__setattr__(self, "report_digest", digest)
            if digest != expected_digest:
                raise ValueError("report_digest must match report payload")
        else:
            object.__setattr__(self, "report_digest", expected_digest)


def build_research_resolution_source_disagreement_escalation_report(
    inputs: object,
    *,
    config: ResearchResolutionSourceDisagreementEscalationConfig,
    generated_at: datetime,
) -> ResearchResolutionSourceDisagreementEscalationReport:
    if type(config) is not ResearchResolutionSourceDisagreementEscalationConfig:
        raise ValueError(
            "config must be a ResearchResolutionSourceDisagreementEscalationConfig",
        )
    _require_hard_flags("config", config)
    _reject_unsafe_public_payload("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    normalized_inputs = _normalize_inputs(inputs)
    _validate_unique_bucket_ids(normalized_inputs)
    for item in normalized_inputs:
        if item.observed_at > generated_at_utc:
            raise ValueError("observed_at must not be after generated_at")

    rows = _normalize_rows(
        tuple(
            _row_from_input(item, config=config)
            for item in normalized_inputs
        ),
    )
    reason_codes = _report_reason_codes(rows)
    return ResearchResolutionSourceDisagreementEscalationReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        status=_report_status(rows),
        input_count=_decimal_count(len(normalized_inputs)),
        row_count=_decimal_count(len(rows)),
        pass_count=_decimal_count(_status_count(rows, "pass")),
        watch_count=_decimal_count(_status_count(rows, "watch")),
        block_count=_decimal_count(_status_count(rows, "block")),
        aggregate_evidence_count=_sum_decimal(row.aggregate_evidence_count for row in rows),
        disagreeing_source_class_count=_sum_decimal(
            row.disagreeing_source_class_count for row in rows
        ),
        source_class_count=_sum_decimal(row.source_class_count for row in rows),
        max_deadline_pressure_score=max(
            (row.deadline_pressure_score for row in rows),
            default=ZERO.quantize(SCORE_QUANT),
        ),
        average_oracle_clarity_score=_average_optional(
            tuple(row.oracle_clarity_score for row in rows),
        ),
        average_source_class_reliability_spread=_average_optional(
            tuple(row.source_class_reliability_spread for row in rows),
        ),
        max_escalation_score=max(
            (row.escalation_score for row in rows),
            default=ZERO.quantize(SCORE_QUANT),
        ),
        average_escalation_score=_average_optional(
            tuple(row.escalation_score for row in rows),
        ),
        rows=rows,
        reason_code_counts=_reason_code_counts(rows, reason_codes),
        reason_codes=reason_codes,
    )


def research_resolution_source_disagreement_escalation_report_payload(
    report: ResearchResolutionSourceDisagreementEscalationReport,
) -> dict[str, Any]:
    if type(report) is not ResearchResolutionSourceDisagreementEscalationReport:
        raise ValueError(
            "report must be a ResearchResolutionSourceDisagreementEscalationReport",
        )
    _require_hard_flags("report", report)
    _reject_unsafe_public_payload("report", report)
    _validate_report(report)
    if report.report_digest != _report_digest(report):
        raise ValueError("report_digest must match report payload")
    payload = _json_ready(report)
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    _reject_unsafe_public_payload("report payload", payload)
    return payload


def _row_from_input(
    value: ResearchResolutionSourceDisagreementEscalationInput,
    *,
    config: ResearchResolutionSourceDisagreementEscalationConfig,
) -> ResearchResolutionSourceDisagreementEscalationRow:
    reliability_spread = _quantize(
        value.strongest_source_class_reliability
        - value.weakest_source_class_reliability,
    )
    disagreement_share = _ratio(
        value.disagreeing_source_class_count,
        value.source_class_count,
    )
    deadline_pressure = _deadline_pressure_score(value.hours_to_deadline, config=config)
    escalation_score = _escalation_score(
        evidence_conflict_score=value.evidence_conflict_score,
        reliability_spread=reliability_spread,
        oracle_clarity_score=value.oracle_clarity_score,
        deadline_pressure_score=deadline_pressure,
        source_class_disagreement_share=disagreement_share,
        config=config,
    )
    status = _status_for_score(escalation_score, config=config)
    return ResearchResolutionSourceDisagreementEscalationRow(
        bucket_id=value.bucket_id,
        status=status,
        evidence_conflict_score=value.evidence_conflict_score,
        weakest_source_class_reliability=value.weakest_source_class_reliability,
        strongest_source_class_reliability=value.strongest_source_class_reliability,
        source_class_reliability_spread=reliability_spread,
        oracle_clarity_score=value.oracle_clarity_score,
        deadline_pressure_score=deadline_pressure,
        hours_to_deadline=value.hours_to_deadline,
        aggregate_evidence_count=value.aggregate_evidence_count,
        disagreeing_source_class_count=value.disagreeing_source_class_count,
        source_class_count=value.source_class_count,
        source_class_disagreement_share=disagreement_share,
        escalation_score=escalation_score,
        observed_at=value.observed_at,
        reason_codes=_row_reason_codes(
            status=status,
            evidence_conflict_score=value.evidence_conflict_score,
            reliability_spread=reliability_spread,
            oracle_clarity_score=value.oracle_clarity_score,
            deadline_pressure_score=deadline_pressure,
            config=config,
        ),
    )


def _escalation_score(
    *,
    evidence_conflict_score: Decimal,
    reliability_spread: Decimal,
    oracle_clarity_score: Decimal,
    deadline_pressure_score: Decimal,
    source_class_disagreement_share: Decimal,
    config: ResearchResolutionSourceDisagreementEscalationConfig,
) -> Decimal:
    oracle_gap = ONE - oracle_clarity_score
    score = (
        evidence_conflict_score * DECIMAL_WEIGHT_CONFLICT
        + reliability_spread * DECIMAL_WEIGHT_RELIABILITY_SPREAD
        + oracle_gap * DECIMAL_WEIGHT_ORACLE_GAP
        + deadline_pressure_score * DECIMAL_WEIGHT_DEADLINE
        + source_class_disagreement_share * DECIMAL_WEIGHT_SOURCE_CLASS_SHARE
    )
    if evidence_conflict_score > config.block_escalation_score:
        score += (
            evidence_conflict_score - config.block_escalation_score
        ) * HIGH_CONFLICT_CONVEX_WEIGHT
    if (
        evidence_conflict_score < config.watch_escalation_score
        and reliability_spread < RELIABILITY_GAP_FLOOR
        and oracle_clarity_score >= config.low_oracle_clarity_floor
        and deadline_pressure_score == ZERO.quantize(SCORE_QUANT)
    ):
        score += LOW_RISK_REVIEW_FLOOR
    return _bounded_probability(score)


def _deadline_pressure_score(
    hours_to_deadline: Decimal,
    *,
    config: ResearchResolutionSourceDisagreementEscalationConfig,
) -> Decimal:
    if hours_to_deadline <= config.deadline_pressure_block_hours:
        return ONE.quantize(SCORE_QUANT)
    if hours_to_deadline >= config.deadline_pressure_watch_hours:
        return ZERO.quantize(SCORE_QUANT)
    with localcontext() as ctx:
        ctx.prec = 28
        pressure = (
            config.deadline_pressure_watch_hours - hours_to_deadline
        ) / config.deadline_pressure_block_hours
    return _bounded_probability(pressure)


def _row_reason_codes(
    *,
    status: str,
    evidence_conflict_score: Decimal,
    reliability_spread: Decimal,
    oracle_clarity_score: Decimal,
    deadline_pressure_score: Decimal,
    config: ResearchResolutionSourceDisagreementEscalationConfig,
) -> tuple[str, ...]:
    codes = {f"resolution_source_disagreement_{status}"}
    if evidence_conflict_score >= config.block_escalation_score:
        codes.add("high_aggregate_evidence_conflict")
    elif evidence_conflict_score >= config.watch_escalation_score:
        codes.add("moderate_aggregate_evidence_conflict")
    if reliability_spread >= RELIABILITY_GAP_FLOOR:
        codes.add("source_class_reliability_gap")
    if oracle_clarity_score < config.low_oracle_clarity_floor:
        codes.add("low_oracle_clarity")
    if deadline_pressure_score >= ONE:
        codes.add("deadline_pressure_block")
    elif deadline_pressure_score > ZERO:
        codes.add("deadline_pressure_watch")
    return tuple(sorted(codes))


def _status_for_score(
    escalation_score: Decimal,
    *,
    config: ResearchResolutionSourceDisagreementEscalationConfig,
) -> str:
    if escalation_score >= config.block_escalation_score:
        return "block"
    if escalation_score >= config.watch_escalation_score:
        return "watch"
    return "pass"


def _normalize_inputs(
    inputs: object,
) -> tuple[ResearchResolutionSourceDisagreementEscalationInput, ...]:
    if isinstance(inputs, (str, bytes)):
        raise ValueError("inputs must be an iterable")
    try:
        values = tuple(inputs)  # type: ignore[arg-type]
    except TypeError as exc:
        raise ValueError("inputs must be an iterable") from exc
    normalized: list[ResearchResolutionSourceDisagreementEscalationInput] = []
    for value in values:
        if type(value) is not ResearchResolutionSourceDisagreementEscalationInput:
            raise ValueError(
                "inputs must contain ResearchResolutionSourceDisagreementEscalationInput",
            )
        _require_hard_flags("input", value)
        _reject_unsafe_public_payload("input", value)
        normalized.append(value)
    return tuple(normalized)


def _validate_unique_bucket_ids(
    inputs: tuple[ResearchResolutionSourceDisagreementEscalationInput, ...],
) -> None:
    seen: set[str] = set()
    for value in inputs:
        if value.bucket_id in seen:
            raise ValueError("bucket_id values must be unique")
        seen.add(value.bucket_id)


def _normalize_rows(
    rows: tuple[ResearchResolutionSourceDisagreementEscalationRow, ...],
) -> tuple[ResearchResolutionSourceDisagreementEscalationRow, ...]:
    for row in rows:
        if type(row) is not ResearchResolutionSourceDisagreementEscalationRow:
            raise ValueError(
                "rows must contain ResearchResolutionSourceDisagreementEscalationRow",
            )
        _require_hard_flags("row", row)
    return tuple(
        sorted(
            rows,
            key=lambda row: (STATUS_RANK[row.status], row.bucket_id),
        ),
    )


def _normalize_reason_code_counts(
    counts: tuple[ResearchResolutionSourceDisagreementEscalationReasonCodeCount, ...],
) -> tuple[ResearchResolutionSourceDisagreementEscalationReasonCodeCount, ...]:
    for count in counts:
        if type(count) is not ResearchResolutionSourceDisagreementEscalationReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "ResearchResolutionSourceDisagreementEscalationReasonCodeCount",
            )
        _require_hard_flags("reason_code_count", count)
    return tuple(sorted(counts, key=lambda item: item.reason_code))


def _report_status(
    rows: tuple[ResearchResolutionSourceDisagreementEscalationRow, ...],
) -> str:
    if not rows:
        return "block"
    if any(row.status == "block" for row in rows):
        return "block"
    if any(row.status == "watch" for row in rows):
        return "watch"
    return "pass"


def _report_reason_codes(
    rows: tuple[ResearchResolutionSourceDisagreementEscalationRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return ("resolution_source_disagreement_escalation_empty",)
    return tuple(sorted({code for row in rows for code in row.reason_codes}))


def _reason_code_counts(
    rows: tuple[ResearchResolutionSourceDisagreementEscalationRow, ...],
    reason_codes: tuple[str, ...],
) -> tuple[ResearchResolutionSourceDisagreementEscalationReasonCodeCount, ...]:
    if not rows:
        return (
            ResearchResolutionSourceDisagreementEscalationReasonCodeCount(
                reason_code=reason_codes[0],
                count=ONE.quantize(COUNT_QUANT),
            ),
        )
    counts: Counter[str] = Counter()
    for row in rows:
        counts.update(row.reason_codes)
    return tuple(
        ResearchResolutionSourceDisagreementEscalationReasonCodeCount(
            reason_code=reason_code,
            count=_decimal_count(counts[reason_code]),
        )
        for reason_code in reason_codes
    )


def _status_count(
    rows: tuple[ResearchResolutionSourceDisagreementEscalationRow, ...],
    status: str,
) -> int:
    return sum(1 for row in rows if row.status == status)


def _validate_row(row: ResearchResolutionSourceDisagreementEscalationRow) -> None:
    expected_spread = _quantize(
        row.strongest_source_class_reliability - row.weakest_source_class_reliability,
    )
    if row.source_class_reliability_spread != expected_spread:
        raise ValueError("source_class_reliability_spread must match reliability inputs")
    expected_share = _ratio(row.disagreeing_source_class_count, row.source_class_count)
    if row.source_class_disagreement_share != expected_share:
        raise ValueError("source_class_disagreement_share must match source class counts")
    if row.disagreeing_source_class_count > row.source_class_count:
        raise ValueError("disagreeing_source_class_count must not exceed source_class_count")


def _validate_report(report: ResearchResolutionSourceDisagreementEscalationReport) -> None:
    if report.row_count != _decimal_count(len(report.rows)):
        raise ValueError("row_count must match rows")
    if report.input_count != report.row_count:
        raise ValueError("input_count must match row_count")
    if report.pass_count != _decimal_count(_status_count(report.rows, "pass")):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _decimal_count(_status_count(report.rows, "watch")):
        raise ValueError("watch_count must match rows")
    if report.block_count != _decimal_count(_status_count(report.rows, "block")):
        raise ValueError("block_count must match rows")
    if report.status != _report_status(report.rows):
        raise ValueError("status must match rows")
    expected_reason_codes = _report_reason_codes(report.rows)
    if report.reason_codes != expected_reason_codes:
        raise ValueError("reason_codes must match rows")
    if tuple(item.reason_code for item in report.reason_code_counts) != report.reason_codes:
        raise ValueError("reason_code_counts must match reason_codes")
    if report.aggregate_evidence_count != _sum_decimal(
        row.aggregate_evidence_count for row in report.rows
    ):
        raise ValueError("aggregate_evidence_count must match rows")
    if report.disagreeing_source_class_count != _sum_decimal(
        row.disagreeing_source_class_count for row in report.rows
    ):
        raise ValueError("disagreeing_source_class_count must match rows")
    if report.source_class_count != _sum_decimal(row.source_class_count for row in report.rows):
        raise ValueError("source_class_count must match rows")
    if report.max_deadline_pressure_score != max(
        (row.deadline_pressure_score for row in report.rows),
        default=ZERO.quantize(SCORE_QUANT),
    ):
        raise ValueError("max_deadline_pressure_score must match rows")
    if report.max_escalation_score != max(
        (row.escalation_score for row in report.rows),
        default=ZERO.quantize(SCORE_QUANT),
    ):
        raise ValueError("max_escalation_score must match rows")
    if report.average_oracle_clarity_score != _average_optional(
        tuple(row.oracle_clarity_score for row in report.rows),
    ):
        raise ValueError("average_oracle_clarity_score must match rows")
    if report.average_source_class_reliability_spread != _average_optional(
        tuple(row.source_class_reliability_spread for row in report.rows),
    ):
        raise ValueError("average_source_class_reliability_spread must match rows")
    if report.average_escalation_score != _average_optional(
        tuple(row.escalation_score for row in report.rows),
    ):
        raise ValueError("average_escalation_score must match rows")


def _report_digest(report: ResearchResolutionSourceDisagreementEscalationReport) -> str:
    payload = _json_ready(report, skip_report_digest=True)
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return sha256(encoded.encode("utf-8")).hexdigest()


def _json_ready(value: Any, *, skip_report_digest: bool = False) -> Any:
    if value is None:
        return None
    if is_dataclass(value) and not isinstance(value, type):
        result: dict[str, Any] = {}
        for field in fields(value):
            if skip_report_digest and field.name == "report_digest":
                continue
            result[field.name] = _json_ready(
                getattr(value, field.name),
                skip_report_digest=skip_report_digest,
            )
        return result
    if isinstance(value, Decimal):
        if not value.is_finite():
            raise ValueError("Decimal payload values must be finite")
        return format(value, "f")
    if type(value) is datetime:
        return value.astimezone(UTC).isoformat()
    if isinstance(value, float):
        raise ValueError("payload values must not be floats")
    if isinstance(value, tuple):
        return [_json_ready(item, skip_report_digest=skip_report_digest) for item in value]
    if isinstance(value, list):
        return [_json_ready(item, skip_report_digest=skip_report_digest) for item in value]
    if isinstance(value, dict):
        return {
            _require_payload_key(key): _json_ready(
                item,
                skip_report_digest=skip_report_digest,
            )
            for key, item in value.items()
        }
    if isinstance(value, (str, bool, int)):
        return value
    raise ValueError("payload values must be JSON serializable")


def _field_keys(value: object) -> tuple[str, ...]:
    if is_dataclass(value) and not isinstance(value, type):
        return tuple(field.name for field in fields(value))
    if isinstance(value, dict):
        return tuple(str(key) for key in value)
    return ()


def _iter_public_strings(value: object) -> tuple[str, ...]:
    if isinstance(value, str):
        return (value,)
    if is_dataclass(value) and not isinstance(value, type):
        strings: list[str] = []
        for field in fields(value):
            strings.extend(_iter_public_strings(getattr(value, field.name)))
        return tuple(strings)
    if isinstance(value, dict):
        strings = []
        for key, item in value.items():
            strings.append(str(key))
            strings.extend(_iter_public_strings(item))
        return tuple(strings)
    if isinstance(value, (list, tuple)):
        strings = []
        for item in value:
            strings.extend(_iter_public_strings(item))
        return tuple(strings)
    return ()


def _reject_unsafe_public_payload(label: str, value: object) -> None:
    for key in _field_keys(value):
        lowered_key = key.lower()
        if any(fragment in lowered_key for fragment in UNSAFE_TEXT_FRAGMENTS):
            raise ValueError(f"{label} contains unsafe field: {key}")
    for item in _iter_public_strings(value):
        lowered = item.lower()
        if any(fragment in lowered for fragment in UNSAFE_TEXT_FRAGMENTS):
            raise ValueError(f"{label} contains unsafe text")


def _require_hard_flags(label: str, value: object) -> None:
    if getattr(value, "paper_only", None) is not True:
        raise ValueError(f"paper_only must be True for {label}")
    if getattr(value, "report_only", None) is not True:
        raise ValueError(f"report_only must be True for {label}")
    if getattr(value, "readonly", None) is not True:
        raise ValueError(f"readonly must be True for {label}")


def _require_public_label(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")
    if "\n" in value or "\r" in value or "\t" in value:
        raise ValueError(f"{field_name} must be single line")
    lowered = value.lower()
    if any(fragment in lowered for fragment in UNSAFE_TEXT_FRAGMENTS):
        raise ValueError(f"{field_name} contains unsafe text")


def _require_status(field_name: str, value: object) -> None:
    _require_public_label(field_name, value)
    if value not in PUBLIC_STATUSES:
        raise ValueError(f"{field_name} must be pass, watch, or block")


def _normalize_reason_codes(
    field_name: str,
    value: object,
    *,
    allow_empty: bool,
) -> tuple[str, ...]:
    if type(value) not in (tuple, list):
        raise ValueError(f"{field_name} must be a tuple or list")
    reason_codes = tuple(value)
    if not allow_empty and not reason_codes:
        raise ValueError(f"{field_name} must not be empty")
    for reason_code in reason_codes:
        _require_public_label(field_name, reason_code)
    if len(set(reason_codes)) != len(reason_codes):
        raise ValueError(f"{field_name} values must be unique")
    return tuple(sorted(reason_codes))


def _require_probability_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_score_decimal(field_name, value)
    if decimal_value > ONE:
        raise ValueError(f"{field_name} must be at most one")
    return decimal_value


def _require_optional_probability_decimal(field_name: str, value: object) -> Decimal | None:
    if value is None:
        return None
    return _require_probability_decimal(field_name, value)


def _require_positive_score_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_score_decimal(field_name, value)
    if decimal_value <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return decimal_value


def _require_score_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    if value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return _quantize(value)


def _require_count_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    if value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    try:
        decimal_value = value.quantize(COUNT_QUANT)
    except InvalidOperation as exc:
        raise ValueError(f"{field_name} must be quantizable") from exc
    if decimal_value != value:
        raise ValueError(f"{field_name} must be a whole Decimal")
    return decimal_value


def _require_positive_count_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_count_decimal(field_name, value)
    if decimal_value <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return decimal_value


def _require_sha256_digest(field_name: str, value: object) -> str:
    if type(value) is not str or len(value) != 64:
        raise ValueError(f"{field_name} must be a sha256 digest")
    allowed = set("0123456789abcdef")
    if any(char not in allowed for char in value):
        raise ValueError(f"{field_name} must be lowercase hex")
    return value


def _require_payload_key(value: object) -> str:
    if type(value) is not str:
        raise ValueError("payload keys must be strings")
    return value


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be exactly datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _decimal_count(value: int) -> Decimal:
    return Decimal(value).quantize(COUNT_QUANT)


def _sum_decimal(values: object) -> Decimal:
    total = ZERO.quantize(COUNT_QUANT)
    for value in values:  # type: ignore[assignment]
        if type(value) is not Decimal:
            raise ValueError("sum values must be Decimal")
        total += value
    return total.quantize(COUNT_QUANT)


def _average_optional(values: tuple[Decimal, ...]) -> Decimal | None:
    if not values:
        return None
    return _average(values)


def _average(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        raise ValueError("values must not be empty")
    with localcontext() as ctx:
        ctx.prec = 28
        return _quantize(sum(values, ZERO) / Decimal(len(values)))


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator <= ZERO:
        raise ValueError("denominator must be positive")
    with localcontext() as ctx:
        ctx.prec = 28
        return _bounded_probability(numerator / denominator)


def _bounded_probability(value: Decimal) -> Decimal:
    if value < ZERO:
        return ZERO.quantize(SCORE_QUANT)
    if value > ONE:
        return ONE.quantize(SCORE_QUANT)
    return _quantize(value)


def _quantize(value: Decimal) -> Decimal:
    try:
        return value.quantize(SCORE_QUANT)
    except InvalidOperation as exc:
        raise ValueError("Decimal value must be quantizable") from exc


__all__ = (
    "DEFAULT_CONFIG_VERSION",
    "PUBLIC_STATUSES",
    "ResearchResolutionSourceDisagreementEscalationConfig",
    "ResearchResolutionSourceDisagreementEscalationInput",
    "ResearchResolutionSourceDisagreementEscalationReasonCodeCount",
    "ResearchResolutionSourceDisagreementEscalationReport",
    "ResearchResolutionSourceDisagreementEscalationRow",
    "build_research_resolution_source_disagreement_escalation_report",
    "research_resolution_source_disagreement_escalation_report_payload",
)
