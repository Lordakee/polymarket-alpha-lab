"""Pure public aggregate SLA report for unresolved evidence contradictions."""

from __future__ import annotations

from dataclasses import asdict, dataclass, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, InvalidOperation, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
import json
from typing import Any

from polymarket_alpha_lab.team_paper_guard import require_paper_only_flags


DEFAULT_RESEARCH_SOURCE_EVIDENCE_CONTRADICTION_SLA_CONFIG_VERSION = (
    "research-source-evidence-contradiction-sla-v0"
)

STATUSES = ("pass", "watch", "block")
NO_UNRESOLVED_REASON = (
    "research_source_evidence_contradiction_sla_no_unresolved_contradictions"
)
CLEAR_REASON = "research_source_evidence_contradiction_sla_clear"
UNRESOLVED_AGE_REASON = (
    "research_source_evidence_contradiction_sla_unresolved_age_breach"
)
SOURCE_CLASS_QUORUM_REASON = (
    "research_source_evidence_contradiction_sla_source_class_quorum_gap"
)
CORROBORATION_STALE_REASON = (
    "research_source_evidence_contradiction_sla_corroboration_stale"
)
PARSE_RELIABILITY_LOW_REASON = (
    "research_source_evidence_contradiction_sla_parse_reliability_low"
)
RETRY_BACKLOG_HIGH_REASON = (
    "research_source_evidence_contradiction_sla_retry_backlog_high"
)
MANUAL_ESCALATION_URGENT_REASON = (
    "research_source_evidence_contradiction_sla_manual_escalation_urgent"
)
REASON_CODES = (
    NO_UNRESOLVED_REASON,
    UNRESOLVED_AGE_REASON,
    SOURCE_CLASS_QUORUM_REASON,
    CORROBORATION_STALE_REASON,
    PARSE_RELIABILITY_LOW_REASON,
    RETRY_BACKLOG_HIGH_REASON,
    MANUAL_ESCALATION_URGENT_REASON,
    CLEAR_REASON,
)
STATUS_RANK = {
    "block": Decimal("0.000000"),
    "watch": Decimal("1.000000"),
    "pass": Decimal("2.000000"),
}

DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
QUANT = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
UNRESOLVED_AGE_WEIGHT = Decimal("0.250000")
SOURCE_CLASS_QUORUM_WEIGHT = Decimal("0.200000")
CORROBORATION_FRESHNESS_WEIGHT = Decimal("0.150000")
PARSE_RELIABILITY_WEIGHT = Decimal("0.150000")
RETRY_BACKLOG_WEIGHT = Decimal("0.100000")
MANUAL_ESCALATION_WEIGHT = Decimal("0.150000")


def _join_parts(*parts: str) -> str:
    return "".join(parts)


UNSAFE_PUBLIC_KEY_FRAGMENTS = (
    _join_parts("u", "r", "l"),
    _join_parts("te", "xt"),
    _join_parts("ra", "w"),
    _join_parts("market", "_", "id"),
    _join_parts("candidate", "_", "id"),
    _join_parts("d", "sn"),
    _join_parts("table", "_", "name"),
    _join_parts("private", "_", "token"),
    _join_parts("source", "_", "id"),
    _join_parts("token"),
)
UNSAFE_PUBLIC_VALUE_FRAGMENTS = (
    _join_parts("http", "://"),
    _join_parts("https", "://"),
    _join_parts("postgres", "://"),
    _join_parts("postgresql", "://"),
    _join_parts("token", "="),
)


@dataclass(frozen=True)
class ResearchSourceEvidenceContradictionSlaConfig:
    config_version: str = DEFAULT_RESEARCH_SOURCE_EVIDENCE_CONTRADICTION_SLA_CONFIG_VERSION
    unresolved_age_watch_seconds: Decimal = Decimal("3600.000000")
    unresolved_age_block_seconds: Decimal = Decimal("7200.000000")
    source_class_quorum_watch_floor: Decimal = Decimal("0.750000")
    source_class_quorum_block_floor: Decimal = Decimal("0.500000")
    corroboration_age_watch_seconds: Decimal = Decimal("1800.000000")
    corroboration_age_block_seconds: Decimal = Decimal("4800.000000")
    parse_reliability_watch_floor: Decimal = Decimal("0.800000")
    parse_reliability_block_floor: Decimal = Decimal("0.600000")
    retry_backlog_watch_count: Decimal = Decimal("2.000000")
    retry_backlog_block_count: Decimal = Decimal("6.000000")
    manual_escalation_urgency_watch_score: Decimal = Decimal("0.500000")
    manual_escalation_urgency_block_score: Decimal = Decimal("0.850000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_public_string("config_version", self.config_version)
        for field_name in (
            "unresolved_age_watch_seconds",
            "unresolved_age_block_seconds",
            "corroboration_age_watch_seconds",
            "corroboration_age_block_seconds",
            "retry_backlog_watch_count",
            "retry_backlog_block_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_positive_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "source_class_quorum_watch_floor",
            "source_class_quorum_block_floor",
            "parse_reliability_watch_floor",
            "parse_reliability_block_floor",
            "manual_escalation_urgency_watch_score",
            "manual_escalation_urgency_block_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio(field_name, getattr(self, field_name)),
            )
        if self.unresolved_age_block_seconds < self.unresolved_age_watch_seconds:
            raise ValueError("unresolved_age_block_seconds must not be below watch seconds")
        if self.source_class_quorum_block_floor > self.source_class_quorum_watch_floor:
            raise ValueError("source_class_quorum_block_floor must not exceed watch floor")
        if self.corroboration_age_block_seconds < self.corroboration_age_watch_seconds:
            raise ValueError("corroboration_age_block_seconds must not be below watch seconds")
        if self.parse_reliability_block_floor > self.parse_reliability_watch_floor:
            raise ValueError("parse_reliability_block_floor must not exceed watch floor")
        if self.retry_backlog_block_count < self.retry_backlog_watch_count:
            raise ValueError("retry_backlog_block_count must not be below watch count")
        if (
            self.manual_escalation_urgency_block_score
            < self.manual_escalation_urgency_watch_score
        ):
            raise ValueError(
                "manual_escalation_urgency_block_score must not be below watch score",
            )
        require_paper_only_flags("config", self)


@dataclass(frozen=True)
class ResearchSourceEvidenceContradictionSlaInput:
    contradiction_key: str
    source_class: str
    unresolved_contradiction_age_seconds: Decimal
    required_source_class_count: Decimal
    observed_source_class_count: Decimal
    last_corroborated_age_seconds: Decimal
    parse_reliability_score: Decimal
    retry_backlog_count: Decimal
    manual_escalation_urgency_score: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_public_string("contradiction_key", self.contradiction_key)
        _require_public_string("source_class", self.source_class)
        for field_name in (
            "unresolved_contradiction_age_seconds",
            "observed_source_class_count",
            "last_corroborated_age_seconds",
            "retry_backlog_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "required_source_class_count",
            _require_positive_decimal(
                "required_source_class_count",
                self.required_source_class_count,
            ),
        )
        for field_name in (
            "parse_reliability_score",
            "manual_escalation_urgency_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio(field_name, getattr(self, field_name)),
            )
        require_paper_only_flags("input", self)


@dataclass(frozen=True)
class ResearchSourceEvidenceContradictionSlaRow:
    contradiction_key: str
    source_class: str
    unresolved_contradiction_age_seconds: Decimal
    required_source_class_count: Decimal
    observed_source_class_count: Decimal
    source_class_quorum_ratio: Decimal
    last_corroborated_age_seconds: Decimal
    parse_reliability_score: Decimal
    retry_backlog_count: Decimal
    manual_escalation_urgency_score: Decimal
    sla_pressure_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_public_string("contradiction_key", self.contradiction_key)
        _require_public_string("source_class", self.source_class)
        for field_name in (
            "unresolved_contradiction_age_seconds",
            "required_source_class_count",
            "observed_source_class_count",
            "last_corroborated_age_seconds",
            "retry_backlog_count",
            "sla_pressure_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "source_class_quorum_ratio",
            "parse_reliability_score",
            "manual_escalation_urgency_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio(field_name, getattr(self, field_name)),
            )
        _require_status("status", self.status)
        object.__setattr__(self, "reason_codes", _normalize_reason_codes(self.reason_codes))
        _validate_row(self)
        require_paper_only_flags("sla row", self)


@dataclass(frozen=True)
class ResearchSourceEvidenceContradictionSlaReport:
    generated_at: datetime
    config_version: str
    contradiction_count: Decimal
    block_contradiction_count: Decimal
    watch_contradiction_count: Decimal
    max_unresolved_contradiction_age_seconds: Decimal
    min_source_class_quorum_ratio: Decimal
    max_corroboration_age_seconds: Decimal
    min_parse_reliability_score: Decimal
    max_retry_backlog_count: Decimal
    max_manual_escalation_urgency_score: Decimal
    average_sla_pressure_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    sla_rows: tuple[ResearchSourceEvidenceContradictionSlaRow, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_string("config_version", self.config_version)
        for field_name in (
            "contradiction_count",
            "block_contradiction_count",
            "watch_contradiction_count",
            "max_unresolved_contradiction_age_seconds",
            "max_corroboration_age_seconds",
            "max_retry_backlog_count",
            "average_sla_pressure_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "min_source_class_quorum_ratio",
            "min_parse_reliability_score",
            "max_manual_escalation_urgency_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio(field_name, getattr(self, field_name)),
            )
        _require_status("status", self.status)
        object.__setattr__(self, "reason_codes", _normalize_reason_codes(self.reason_codes))
        object.__setattr__(self, "sla_rows", _normalize_sla_rows(self.sla_rows))
        require_paper_only_flags("report", self)
        _require_or_set_digest(self)
        _validate_report(self)


def build_research_source_evidence_contradiction_sla_report(
    inputs: list[ResearchSourceEvidenceContradictionSlaInput]
    | tuple[ResearchSourceEvidenceContradictionSlaInput, ...],
    *,
    config: ResearchSourceEvidenceContradictionSlaConfig,
    generated_at: datetime,
) -> ResearchSourceEvidenceContradictionSlaReport:
    if type(config) is not ResearchSourceEvidenceContradictionSlaConfig:
        raise ValueError("config must be a ResearchSourceEvidenceContradictionSlaConfig")
    require_paper_only_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    rows = _sla_rows(_normalize_inputs(inputs), config=config)
    return ResearchSourceEvidenceContradictionSlaReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        contradiction_count=_count(len(rows)),
        block_contradiction_count=_count(sum(row.status == "block" for row in rows)),
        watch_contradiction_count=_count(sum(row.status == "watch" for row in rows)),
        max_unresolved_contradiction_age_seconds=_max_rows(
            rows,
            "unresolved_contradiction_age_seconds",
        ),
        min_source_class_quorum_ratio=_min_rows(rows, "source_class_quorum_ratio"),
        max_corroboration_age_seconds=_max_rows(rows, "last_corroborated_age_seconds"),
        min_parse_reliability_score=_min_rows(rows, "parse_reliability_score"),
        max_retry_backlog_count=_max_rows(rows, "retry_backlog_count"),
        max_manual_escalation_urgency_score=_max_rows(
            rows,
            "manual_escalation_urgency_score",
        ),
        average_sla_pressure_score=_ratio(_sum_rows(rows, "sla_pressure_score"), _count(len(rows))),
        status=_report_status(rows),
        reason_codes=_report_reason_codes(rows),
        sla_rows=rows,
    )


def research_source_evidence_contradiction_sla_report_payload(
    report: ResearchSourceEvidenceContradictionSlaReport,
) -> dict[str, Any]:
    if type(report) is not ResearchSourceEvidenceContradictionSlaReport:
        raise ValueError("report must be a ResearchSourceEvidenceContradictionSlaReport")
    require_paper_only_flags("report", report)
    _require_or_set_digest(report)
    payload = _json_ready(report)
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    _reject_public_payload(payload)
    _verify_public_digest(payload)
    return payload


def _normalize_inputs(
    value: object,
) -> tuple[ResearchSourceEvidenceContradictionSlaInput, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("inputs must be a list or tuple")
    rows = tuple(value)
    seen: set[str] = set()
    for row in rows:
        if type(row) is not ResearchSourceEvidenceContradictionSlaInput:
            raise ValueError(
                "inputs must contain ResearchSourceEvidenceContradictionSlaInput",
            )
        require_paper_only_flags("input", row)
        if row.contradiction_key in seen:
            raise ValueError("inputs must be unique by contradiction_key")
        seen.add(row.contradiction_key)
    return tuple(sorted(rows, key=lambda row: row.contradiction_key))


def _sla_rows(
    rows: tuple[ResearchSourceEvidenceContradictionSlaInput, ...],
    *,
    config: ResearchSourceEvidenceContradictionSlaConfig,
) -> tuple[ResearchSourceEvidenceContradictionSlaRow, ...]:
    return tuple(sorted((_sla_row(row, config=config) for row in rows), key=_row_sort_key))


def _sla_row(
    row: ResearchSourceEvidenceContradictionSlaInput,
    *,
    config: ResearchSourceEvidenceContradictionSlaConfig,
) -> ResearchSourceEvidenceContradictionSlaRow:
    quorum_ratio = _quorum_ratio(row)
    reason_codes = _row_reason_codes(row, quorum_ratio=quorum_ratio, config=config)
    return ResearchSourceEvidenceContradictionSlaRow(
        contradiction_key=row.contradiction_key,
        source_class=row.source_class,
        unresolved_contradiction_age_seconds=row.unresolved_contradiction_age_seconds,
        required_source_class_count=row.required_source_class_count,
        observed_source_class_count=row.observed_source_class_count,
        source_class_quorum_ratio=quorum_ratio,
        last_corroborated_age_seconds=row.last_corroborated_age_seconds,
        parse_reliability_score=row.parse_reliability_score,
        retry_backlog_count=row.retry_backlog_count,
        manual_escalation_urgency_score=row.manual_escalation_urgency_score,
        sla_pressure_score=_sla_pressure_score(row, quorum_ratio=quorum_ratio, config=config),
        status=_row_status(row, quorum_ratio=quorum_ratio, reason_codes=reason_codes, config=config),
        reason_codes=reason_codes,
    )


def _quorum_ratio(row: ResearchSourceEvidenceContradictionSlaInput) -> Decimal:
    return min(
        _ratio(row.observed_source_class_count, row.required_source_class_count),
        ONE,
    )


def _sla_pressure_score(
    row: ResearchSourceEvidenceContradictionSlaInput,
    *,
    quorum_ratio: Decimal,
    config: ResearchSourceEvidenceContradictionSlaConfig,
) -> Decimal:
    unresolved_age_pressure = min(
        _ratio(row.unresolved_contradiction_age_seconds, config.unresolved_age_block_seconds),
        ONE,
    )
    quorum_gap = (ONE - quorum_ratio).quantize(QUANT)
    corroboration_age_pressure = min(
        _ratio(row.last_corroborated_age_seconds, config.corroboration_age_block_seconds),
        ONE,
    )
    parse_reliability_gap = (ONE - row.parse_reliability_score).quantize(QUANT)
    retry_backlog_pressure = min(
        _ratio(row.retry_backlog_count, config.retry_backlog_block_count),
        ONE,
    )
    with localcontext(DECIMAL_CONTEXT):
        return (
            unresolved_age_pressure * UNRESOLVED_AGE_WEIGHT
            + quorum_gap * SOURCE_CLASS_QUORUM_WEIGHT
            + corroboration_age_pressure * CORROBORATION_FRESHNESS_WEIGHT
            + parse_reliability_gap * PARSE_RELIABILITY_WEIGHT
            + retry_backlog_pressure * RETRY_BACKLOG_WEIGHT
            + row.manual_escalation_urgency_score * MANUAL_ESCALATION_WEIGHT
        ).quantize(QUANT)


def _row_reason_codes(
    row: ResearchSourceEvidenceContradictionSlaInput,
    *,
    quorum_ratio: Decimal,
    config: ResearchSourceEvidenceContradictionSlaConfig,
) -> tuple[str, ...]:
    reasons: list[str] = []
    if row.unresolved_contradiction_age_seconds >= config.unresolved_age_watch_seconds:
        reasons.append(UNRESOLVED_AGE_REASON)
    if quorum_ratio <= config.source_class_quorum_watch_floor:
        reasons.append(SOURCE_CLASS_QUORUM_REASON)
    if row.last_corroborated_age_seconds >= config.corroboration_age_watch_seconds:
        reasons.append(CORROBORATION_STALE_REASON)
    if row.parse_reliability_score <= config.parse_reliability_watch_floor:
        reasons.append(PARSE_RELIABILITY_LOW_REASON)
    if row.retry_backlog_count >= config.retry_backlog_watch_count:
        reasons.append(RETRY_BACKLOG_HIGH_REASON)
    if row.manual_escalation_urgency_score >= config.manual_escalation_urgency_watch_score:
        reasons.append(MANUAL_ESCALATION_URGENT_REASON)
    if not reasons:
        reasons.append(CLEAR_REASON)
    return tuple(reasons)


def _row_status(
    row: ResearchSourceEvidenceContradictionSlaInput,
    *,
    quorum_ratio: Decimal,
    reason_codes: tuple[str, ...],
    config: ResearchSourceEvidenceContradictionSlaConfig,
) -> str:
    if reason_codes == (CLEAR_REASON,):
        return "pass"
    if (
        row.unresolved_contradiction_age_seconds >= config.unresolved_age_block_seconds
        or quorum_ratio <= config.source_class_quorum_block_floor
        or row.last_corroborated_age_seconds >= config.corroboration_age_block_seconds
        or row.parse_reliability_score <= config.parse_reliability_block_floor
        or row.retry_backlog_count >= config.retry_backlog_block_count
        or row.manual_escalation_urgency_score
        >= config.manual_escalation_urgency_block_score
    ):
        return "block"
    return "watch"


def _row_status_is_consistent(row: ResearchSourceEvidenceContradictionSlaRow) -> bool:
    if row.reason_codes == (CLEAR_REASON,):
        return row.status == "pass"
    return row.status in ("watch", "block")


def _row_sort_key(
    row: ResearchSourceEvidenceContradictionSlaRow,
) -> tuple[Decimal, Decimal, str]:
    return (
        STATUS_RANK[row.status],
        -row.sla_pressure_score,
        row.contradiction_key,
    )


def _report_status(rows: tuple[ResearchSourceEvidenceContradictionSlaRow, ...]) -> str:
    if any(row.status == "block" for row in rows):
        return "block"
    if any(row.status == "watch" for row in rows):
        return "watch"
    return "pass"


def _report_reason_codes(
    rows: tuple[ResearchSourceEvidenceContradictionSlaRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return (NO_UNRESOLVED_REASON,)
    reasons = tuple(
        reason_code
        for reason_code in REASON_CODES
        if reason_code not in (NO_UNRESOLVED_REASON, CLEAR_REASON)
        and any(reason_code in row.reason_codes for row in rows)
    )
    if reasons:
        return reasons
    return (CLEAR_REASON,)


def _normalize_sla_rows(
    value: object,
) -> tuple[ResearchSourceEvidenceContradictionSlaRow, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("sla_rows must be a list or tuple")
    rows = tuple(value)
    previous_key: tuple[Decimal, Decimal, str] | None = None
    seen: set[str] = set()
    for row in rows:
        if type(row) is not ResearchSourceEvidenceContradictionSlaRow:
            raise ValueError("sla_rows must contain ResearchSourceEvidenceContradictionSlaRow")
        require_paper_only_flags("sla row", row)
        if row.contradiction_key in seen:
            raise ValueError("sla_rows must contain unique contradiction_key values")
        seen.add(row.contradiction_key)
        sort_key = _row_sort_key(row)
        if previous_key is not None and sort_key <= previous_key:
            raise ValueError("sla_rows must follow deterministic sequence")
        previous_key = sort_key
    return rows


def _validate_row(row: ResearchSourceEvidenceContradictionSlaRow) -> None:
    if row.required_source_class_count <= ZERO:
        raise ValueError("required_source_class_count must be positive")
    if row.source_class_quorum_ratio != min(
        _ratio(row.observed_source_class_count, row.required_source_class_count),
        ONE,
    ):
        raise ValueError("source_class_quorum_ratio must match source class counts")
    if not _row_status_is_consistent(row):
        raise ValueError("status must match reason_codes")


def _validate_report(report: ResearchSourceEvidenceContradictionSlaReport) -> None:
    if report.contradiction_count != _count(len(report.sla_rows)):
        raise ValueError("contradiction_count must match sla_rows")
    if report.block_contradiction_count != _count(
        sum(row.status == "block" for row in report.sla_rows),
    ):
        raise ValueError("block_contradiction_count must match sla_rows")
    if report.watch_contradiction_count != _count(
        sum(row.status == "watch" for row in report.sla_rows),
    ):
        raise ValueError("watch_contradiction_count must match sla_rows")
    if report.max_unresolved_contradiction_age_seconds != _max_rows(
        report.sla_rows,
        "unresolved_contradiction_age_seconds",
    ):
        raise ValueError("max_unresolved_contradiction_age_seconds must match sla_rows")
    if report.min_source_class_quorum_ratio != _min_rows(
        report.sla_rows,
        "source_class_quorum_ratio",
    ):
        raise ValueError("min_source_class_quorum_ratio must match sla_rows")
    if report.max_corroboration_age_seconds != _max_rows(
        report.sla_rows,
        "last_corroborated_age_seconds",
    ):
        raise ValueError("max_corroboration_age_seconds must match sla_rows")
    if report.min_parse_reliability_score != _min_rows(
        report.sla_rows,
        "parse_reliability_score",
    ):
        raise ValueError("min_parse_reliability_score must match sla_rows")
    if report.max_retry_backlog_count != _max_rows(report.sla_rows, "retry_backlog_count"):
        raise ValueError("max_retry_backlog_count must match sla_rows")
    if report.max_manual_escalation_urgency_score != _max_rows(
        report.sla_rows,
        "manual_escalation_urgency_score",
    ):
        raise ValueError("max_manual_escalation_urgency_score must match sla_rows")
    if report.average_sla_pressure_score != _ratio(
        _sum_rows(report.sla_rows, "sla_pressure_score"),
        _count(len(report.sla_rows)),
    ):
        raise ValueError("average_sla_pressure_score must match sla_rows")
    if report.reason_codes != _report_reason_codes(report.sla_rows):
        raise ValueError("reason_codes must match sla_rows")
    if report.status != _report_status(report.sla_rows):
        raise ValueError("status must match sla_rows")


def _count(value: int) -> Decimal:
    if type(value) is not int:
        raise ValueError("count value must be an int")
    if value < 0:
        raise ValueError("count value must be nonnegative")
    return Decimal(value).quantize(QUANT)


def _sum_rows(rows: tuple[object, ...], field_name: str) -> Decimal:
    return _require_nonnegative_decimal(
        field_name,
        sum((getattr(row, field_name) for row in rows), ZERO),
    )


def _max_rows(rows: tuple[object, ...], field_name: str) -> Decimal:
    if not rows:
        return ZERO
    return max(
        _require_nonnegative_decimal(field_name, getattr(row, field_name))
        for row in rows
    ).quantize(QUANT)


def _min_rows(rows: tuple[object, ...], field_name: str) -> Decimal:
    if not rows:
        return ZERO
    return min(
        _require_nonnegative_decimal(field_name, getattr(row, field_name))
        for row in rows
    ).quantize(QUANT)


def _require_status(field_name: str, value: object) -> None:
    _require_public_string(field_name, value)
    if value not in STATUSES:
        raise ValueError(f"{field_name} must be pass, watch, or block")


def _normalize_reason_codes(value: object) -> tuple[str, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("reason_codes must be a list or tuple")
    reason_codes = tuple(value)
    if not reason_codes:
        raise ValueError("reason_codes must not be empty")
    previous_index = -1
    seen: set[str] = set()
    for reason_code in reason_codes:
        _require_public_string("reason_code", reason_code)
        if reason_code not in REASON_CODES:
            raise ValueError("reason_code must be known")
        index = REASON_CODES.index(reason_code)
        if reason_code in seen:
            raise ValueError("reason_codes must be unique")
        if index <= previous_index:
            raise ValueError("reason_codes must follow deterministic sequence")
        previous_index = index
        seen.add(reason_code)
    return reason_codes


def _require_public_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")
    lowered = value.lower()
    if any(fragment in lowered for fragment in UNSAFE_PUBLIC_VALUE_FRAGMENTS):
        raise ValueError(f"{field_name} must be public safe")


def _require_ratio(field_name: str, value: object) -> Decimal:
    ratio = _require_nonnegative_decimal(field_name, value)
    if ratio > ONE:
        raise ValueError(f"{field_name} must not exceed one")
    return ratio


def _require_positive_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_nonnegative_decimal(field_name, value)
    if normalized <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _require_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    if value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    try:
        with localcontext(DECIMAL_CONTEXT):
            return value.quantize(QUANT)
    except InvalidOperation as exc:
        raise ValueError(f"{field_name} must fit the decimal context") from exc


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    numerator_value = _require_nonnegative_decimal("ratio numerator", numerator)
    denominator_value = _require_nonnegative_decimal("ratio denominator", denominator)
    if denominator_value == ZERO:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return (numerator_value / denominator_value).quantize(QUANT)


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_or_set_digest(report: ResearchSourceEvidenceContradictionSlaReport) -> None:
    if type(report.derived_validation_digest) is not str:
        raise ValueError("derived_validation_digest must be a string")
    expected = _report_digest(report)
    if report.derived_validation_digest == "":
        object.__setattr__(report, "derived_validation_digest", expected)
        return
    if report.derived_validation_digest != expected:
        raise ValueError("derived_validation_digest does not match public payload")


def _report_digest(report: ResearchSourceEvidenceContradictionSlaReport) -> str:
    payload = _json_ready(report)
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    payload.pop("derived_validation_digest", None)
    return _canonical_digest(payload)


def _verify_public_digest(payload: dict[str, Any]) -> None:
    digest = payload.get("derived_validation_digest")
    if type(digest) is not str:
        raise ValueError("derived_validation_digest must be a string")
    unsigned = dict(payload)
    unsigned.pop("derived_validation_digest", None)
    if digest != _canonical_digest(unsigned):
        raise ValueError("derived_validation_digest does not match public payload")


def _canonical_digest(payload: dict[str, Any]) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    return sha256(encoded).hexdigest()


def _json_ready(value: Any) -> Any:
    if value is None:
        return None
    if is_dataclass(value) and not isinstance(value, type):
        return _json_ready(asdict(value))
    if isinstance(value, Decimal):
        if type(value) is not Decimal:
            raise ValueError("JSON Decimal value must be a Decimal")
        if not value.is_finite():
            raise ValueError("JSON Decimal value must be finite")
        return str(value)
    if isinstance(value, datetime):
        return _as_utc("JSON datetime value", value).isoformat()
    if isinstance(value, bool):
        return value
    if isinstance(value, (float, int)):
        raise ValueError("JSON numeric value must use Decimal")
    if isinstance(value, str):
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


def _reject_public_payload(value: object) -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            lowered = key.lower()
            if any(fragment in lowered for fragment in UNSAFE_PUBLIC_KEY_FRAGMENTS):
                raise ValueError("public payload contains unsafe key")
            _reject_public_payload(item)
        return
    if isinstance(value, list):
        for item in value:
            _reject_public_payload(item)
        return
    if type(value) in (int, float):
        raise ValueError("public payload numerics must be Decimal-derived strings")
    if isinstance(value, str):
        lowered = value.lower()
        if any(fragment in lowered for fragment in UNSAFE_PUBLIC_VALUE_FRAGMENTS):
            raise ValueError("public payload contains unsafe value")


__all__ = (
    "DEFAULT_RESEARCH_SOURCE_EVIDENCE_CONTRADICTION_SLA_CONFIG_VERSION",
    "STATUSES",
    "ResearchSourceEvidenceContradictionSlaConfig",
    "ResearchSourceEvidenceContradictionSlaInput",
    "ResearchSourceEvidenceContradictionSlaReport",
    "ResearchSourceEvidenceContradictionSlaRow",
    "build_research_source_evidence_contradiction_sla_report",
    "research_source_evidence_contradiction_sla_report_payload",
)
