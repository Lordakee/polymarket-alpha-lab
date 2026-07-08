"""Pure in-memory public research evidence refresh priority report."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from typing import Any

from polymarket_alpha_lab.team_paper_guard import (
    json_ready_no_floats,
    reject_unsafe_surface_fields,
    require_paper_only_flags,
)


DEFAULT_RESEARCH_EVENT_EVIDENCE_REFRESH_PRIORITY_REPORT_CONFIG_VERSION = (
    "research-event-evidence-refresh-priority-report-v0"
)
RESEARCH_EVENT_EVIDENCE_REFRESH_PRIORITY_STATUSES = ("pass", "watch", "block")
EMPTY_REASON = "research_event_evidence_refresh_priority_empty"
CURRENT_REASON = "event_evidence_refresh_current"
AGE_WATCH_REASON = "event_evidence_age_watch"
AGE_BLOCK_REASON = "event_evidence_age_block"
RELIABILITY_WATCH_REASON = "source_reliability_watch"
RELIABILITY_BLOCK_REASON = "source_reliability_block"
CATALYST_WATCH_REASON = "catalyst_pressure_watch"
CATALYST_BLOCK_REASON = "catalyst_pressure_block"
CONTRADICTION_WATCH_REASON = "contradiction_pressure_watch"
CONTRADICTION_BLOCK_REASON = "contradiction_pressure_block"
DEADLINE_NEAR_REASON = "deadline_near"
DEADLINE_IMMINENT_REASON = "deadline_imminent"
ROW_REASON_CODES = (
    CURRENT_REASON,
    AGE_BLOCK_REASON,
    RELIABILITY_BLOCK_REASON,
    CATALYST_BLOCK_REASON,
    CONTRADICTION_BLOCK_REASON,
    DEADLINE_IMMINENT_REASON,
    AGE_WATCH_REASON,
    RELIABILITY_WATCH_REASON,
    CATALYST_WATCH_REASON,
    CONTRADICTION_WATCH_REASON,
    DEADLINE_NEAR_REASON,
)
REPORT_REASON_CODES = (EMPTY_REASON,) + ROW_REASON_CODES
REPORT_TRIGGER_REASON_CODES = tuple(
    reason for reason in REPORT_REASON_CODES if reason not in (EMPTY_REASON, CURRENT_REASON)
)

DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
QUANT = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
SECONDS_PER_DAY = Decimal("86400")
MICROSECONDS_PER_SECOND = Decimal("1000000")


@dataclass(frozen=True)
class ResearchEventEvidenceRefreshPriorityConfig:
    config_version: str = (
        DEFAULT_RESEARCH_EVENT_EVIDENCE_REFRESH_PRIORITY_REPORT_CONFIG_VERSION
    )
    fresh_age_seconds: Decimal = Decimal("3600.000000")
    stale_age_seconds: Decimal = Decimal("7200.000000")
    min_source_reliability_score: Decimal = Decimal("0.700000")
    critical_source_reliability_score: Decimal = Decimal("0.500000")
    catalyst_pressure_watch_threshold: Decimal = Decimal("0.500000")
    catalyst_pressure_block_threshold: Decimal = Decimal("0.800000")
    contradiction_watch_threshold: Decimal = Decimal("1.000000")
    contradiction_block_threshold: Decimal = Decimal("3.000000")
    deadline_near_seconds: Decimal = Decimal("86400.000000")
    deadline_imminent_seconds: Decimal = Decimal("7200.000000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("config_version", self.config_version)
        for field_name in (
            "fresh_age_seconds",
            "stale_age_seconds",
            "deadline_near_seconds",
            "deadline_imminent_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_positive_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "min_source_reliability_score",
            "critical_source_reliability_score",
            "catalyst_pressure_watch_threshold",
            "catalyst_pressure_block_threshold",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "contradiction_watch_threshold",
            "contradiction_block_threshold",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        _validate_config(self)
        require_paper_only_flags("config", self)


@dataclass(frozen=True)
class ResearchEventEvidenceRefreshPriorityInput:
    event_domain: str
    evidence_observed_at: datetime
    source_reliability_score: Decimal
    catalyst_pressure_score: Decimal
    contradiction_count: Decimal
    deadline_seconds: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "event_domain",
            _require_public_domain("event_domain", self.event_domain),
        )
        object.__setattr__(
            self,
            "evidence_observed_at",
            _as_utc("evidence_observed_at", self.evidence_observed_at),
        )
        object.__setattr__(
            self,
            "source_reliability_score",
            _require_ratio("source_reliability_score", self.source_reliability_score),
        )
        object.__setattr__(
            self,
            "catalyst_pressure_score",
            _require_ratio("catalyst_pressure_score", self.catalyst_pressure_score),
        )
        object.__setattr__(
            self,
            "contradiction_count",
            _require_nonnegative_decimal("contradiction_count", self.contradiction_count),
        )
        object.__setattr__(
            self,
            "deadline_seconds",
            _require_positive_decimal("deadline_seconds", self.deadline_seconds),
        )
        require_paper_only_flags("input", self)


@dataclass(frozen=True)
class ResearchEventEvidenceRefreshPriorityRow:
    event_domain: str
    evidence_count: Decimal
    average_evidence_age_seconds: Decimal
    max_evidence_age_seconds: Decimal
    average_source_reliability_score: Decimal
    catalyst_pressure_score: Decimal
    contradiction_count: Decimal
    nearest_deadline_seconds: Decimal
    refresh_priority_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "event_domain",
            _require_public_domain("event_domain", self.event_domain),
        )
        for field_name in (
            "evidence_count",
            "average_evidence_age_seconds",
            "max_evidence_age_seconds",
            "contradiction_count",
            "nearest_deadline_seconds",
            "refresh_priority_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "average_source_reliability_score",
            "catalyst_pressure_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio(field_name, getattr(self, field_name)),
            )
        _require_status("status", self.status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, ROW_REASON_CODES),
        )
        _validate_row(self)
        require_paper_only_flags("priority row", self)


@dataclass(frozen=True)
class ResearchEventEvidenceRefreshPriorityReport:
    generated_at: datetime
    config_version: str
    domain_count: Decimal
    evidence_count: Decimal
    pass_domain_count: Decimal
    watch_domain_count: Decimal
    block_domain_count: Decimal
    oldest_average_evidence_age_seconds: Decimal
    lowest_source_reliability_score: Decimal
    highest_catalyst_pressure_score: Decimal
    contradiction_count: Decimal
    nearest_deadline_seconds: Decimal
    status: str
    reason_codes: tuple[str, ...]
    rows: tuple[ResearchEventEvidenceRefreshPriorityRow, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        for field_name in (
            "domain_count",
            "evidence_count",
            "pass_domain_count",
            "watch_domain_count",
            "block_domain_count",
            "oldest_average_evidence_age_seconds",
            "contradiction_count",
            "nearest_deadline_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "lowest_source_reliability_score",
            _require_ratio("lowest_source_reliability_score", self.lowest_source_reliability_score),
        )
        object.__setattr__(
            self,
            "highest_catalyst_pressure_score",
            _require_ratio(
                "highest_catalyst_pressure_score",
                self.highest_catalyst_pressure_score,
            ),
        )
        _require_status("status", self.status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(
                "reason_codes",
                self.reason_codes,
                REPORT_REASON_CODES,
            ),
        )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        _validate_report(self)
        reject_unsafe_surface_fields("research evidence refresh priority report", self)
        require_paper_only_flags("priority report", self)


def build_research_event_evidence_refresh_priority_report(
    inputs: list[ResearchEventEvidenceRefreshPriorityInput]
    | tuple[ResearchEventEvidenceRefreshPriorityInput, ...],
    *,
    config: ResearchEventEvidenceRefreshPriorityConfig,
    generated_at: datetime,
) -> ResearchEventEvidenceRefreshPriorityReport:
    if type(config) is not ResearchEventEvidenceRefreshPriorityConfig:
        raise ValueError("config must be a ResearchEventEvidenceRefreshPriorityConfig")
    require_paper_only_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    rows = _priority_rows(
        _normalize_inputs(inputs, generated_at=generated_at_utc),
        config=config,
        generated_at=generated_at_utc,
    )
    return ResearchEventEvidenceRefreshPriorityReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        domain_count=_count(len(rows)),
        evidence_count=_sum_rows(rows, "evidence_count"),
        pass_domain_count=_status_count(rows, "pass"),
        watch_domain_count=_status_count(rows, "watch"),
        block_domain_count=_status_count(rows, "block"),
        oldest_average_evidence_age_seconds=max(
            (row.average_evidence_age_seconds for row in rows),
            default=ZERO,
        ).quantize(QUANT),
        lowest_source_reliability_score=min(
            (row.average_source_reliability_score for row in rows),
            default=ZERO,
        ).quantize(QUANT),
        highest_catalyst_pressure_score=max(
            (row.catalyst_pressure_score for row in rows),
            default=ZERO,
        ).quantize(QUANT),
        contradiction_count=_sum_rows(rows, "contradiction_count"),
        nearest_deadline_seconds=min(
            (row.nearest_deadline_seconds for row in rows),
            default=ZERO,
        ).quantize(QUANT),
        status=_report_status(rows),
        reason_codes=_report_reason_codes(rows),
        rows=rows,
    )


def research_event_evidence_refresh_priority_report_payload(
    report: ResearchEventEvidenceRefreshPriorityReport,
) -> dict[str, Any]:
    if type(report) is not ResearchEventEvidenceRefreshPriorityReport:
        raise ValueError("report must be a ResearchEventEvidenceRefreshPriorityReport")
    reject_unsafe_surface_fields("research evidence refresh priority report", report)
    require_paper_only_flags("report", report)
    payload = json_ready_no_floats(report)
    if type(payload) is not dict:
        raise ValueError("payload must be a dict")
    return payload


def research_event_evidence_refresh_priority_report_digest(
    report: ResearchEventEvidenceRefreshPriorityReport,
) -> str:
    payload = research_event_evidence_refresh_priority_report_payload(report)
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(encoded).hexdigest()


def _normalize_inputs(
    value: object,
    *,
    generated_at: datetime,
) -> tuple[ResearchEventEvidenceRefreshPriorityInput, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("inputs must be a list or tuple")
    rows = tuple(value)
    for row in rows:
        if type(row) is not ResearchEventEvidenceRefreshPriorityInput:
            raise ValueError(
                "inputs must contain ResearchEventEvidenceRefreshPriorityInput",
            )
        require_paper_only_flags("input", row)
        if row.evidence_observed_at > generated_at:
            raise ValueError("evidence_observed_at must not be in the future")
    return tuple(sorted(rows, key=lambda row: (row.event_domain, row.evidence_observed_at)))


def _priority_rows(
    inputs: tuple[ResearchEventEvidenceRefreshPriorityInput, ...],
    *,
    config: ResearchEventEvidenceRefreshPriorityConfig,
    generated_at: datetime,
) -> tuple[ResearchEventEvidenceRefreshPriorityRow, ...]:
    grouped: dict[str, list[ResearchEventEvidenceRefreshPriorityInput]] = {}
    for row in inputs:
        grouped.setdefault(row.event_domain, []).append(row)
    return tuple(
        sorted(
            (
                _priority_row(
                    domain_rows=tuple(domain_rows),
                    config=config,
                    generated_at=generated_at,
                )
                for domain_rows in grouped.values()
            ),
            key=_row_sort_key,
        ),
    )


def _priority_row(
    *,
    domain_rows: tuple[ResearchEventEvidenceRefreshPriorityInput, ...],
    config: ResearchEventEvidenceRefreshPriorityConfig,
    generated_at: datetime,
) -> ResearchEventEvidenceRefreshPriorityRow:
    ages = tuple(_age_seconds(generated_at, row.evidence_observed_at) for row in domain_rows)
    evidence_count = _count(len(domain_rows))
    average_age = _average(ages)
    average_reliability = _average(
        tuple(row.source_reliability_score for row in domain_rows),
    )
    catalyst_pressure = max(
        (row.catalyst_pressure_score for row in domain_rows),
        default=ZERO,
    ).quantize(QUANT)
    contradiction_count = sum(
        (row.contradiction_count for row in domain_rows),
        ZERO,
    ).quantize(QUANT)
    nearest_deadline = min(
        (row.deadline_seconds for row in domain_rows),
        default=ZERO,
    ).quantize(QUANT)
    reason_codes = _row_reason_codes(
        average_evidence_age_seconds=average_age,
        average_source_reliability_score=average_reliability,
        catalyst_pressure_score=catalyst_pressure,
        contradiction_count=contradiction_count,
        nearest_deadline_seconds=nearest_deadline,
        config=config,
    )
    return ResearchEventEvidenceRefreshPriorityRow(
        event_domain=domain_rows[0].event_domain,
        evidence_count=evidence_count,
        average_evidence_age_seconds=average_age,
        max_evidence_age_seconds=max(ages, default=ZERO).quantize(QUANT),
        average_source_reliability_score=average_reliability,
        catalyst_pressure_score=catalyst_pressure,
        contradiction_count=contradiction_count,
        nearest_deadline_seconds=nearest_deadline,
        refresh_priority_score=_priority_score(
            average_evidence_age_seconds=average_age,
            average_source_reliability_score=average_reliability,
            catalyst_pressure_score=catalyst_pressure,
            contradiction_count=contradiction_count,
            nearest_deadline_seconds=nearest_deadline,
            config=config,
        ),
        status=_row_status(reason_codes),
        reason_codes=reason_codes,
    )


def _row_reason_codes(
    *,
    average_evidence_age_seconds: Decimal,
    average_source_reliability_score: Decimal,
    catalyst_pressure_score: Decimal,
    contradiction_count: Decimal,
    nearest_deadline_seconds: Decimal,
    config: ResearchEventEvidenceRefreshPriorityConfig,
) -> tuple[str, ...]:
    reasons: list[str] = []
    if average_evidence_age_seconds >= config.stale_age_seconds:
        reasons.append(AGE_BLOCK_REASON)
    elif average_evidence_age_seconds > config.fresh_age_seconds:
        reasons.append(AGE_WATCH_REASON)
    if average_source_reliability_score <= config.critical_source_reliability_score:
        reasons.append(RELIABILITY_BLOCK_REASON)
    elif average_source_reliability_score < config.min_source_reliability_score:
        reasons.append(RELIABILITY_WATCH_REASON)
    if catalyst_pressure_score >= config.catalyst_pressure_block_threshold:
        reasons.append(CATALYST_BLOCK_REASON)
    elif catalyst_pressure_score >= config.catalyst_pressure_watch_threshold:
        reasons.append(CATALYST_WATCH_REASON)
    if contradiction_count >= config.contradiction_block_threshold:
        reasons.append(CONTRADICTION_BLOCK_REASON)
    elif contradiction_count >= config.contradiction_watch_threshold:
        reasons.append(CONTRADICTION_WATCH_REASON)
    if nearest_deadline_seconds <= config.deadline_imminent_seconds:
        reasons.append(DEADLINE_IMMINENT_REASON)
    elif nearest_deadline_seconds <= config.deadline_near_seconds:
        reasons.append(DEADLINE_NEAR_REASON)
    if not reasons:
        reasons.append(CURRENT_REASON)
    return tuple(reasons)


def _priority_score(
    *,
    average_evidence_age_seconds: Decimal,
    average_source_reliability_score: Decimal,
    catalyst_pressure_score: Decimal,
    contradiction_count: Decimal,
    nearest_deadline_seconds: Decimal,
    config: ResearchEventEvidenceRefreshPriorityConfig,
) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        age_component = min(average_evidence_age_seconds / config.stale_age_seconds, ONE)
        reliability_component = ONE - average_source_reliability_score
        catalyst_component = catalyst_pressure_score
        contradiction_component = min(
            contradiction_count / config.contradiction_block_threshold,
            ONE,
        )
        deadline_component = _deadline_priority_component(
            nearest_deadline_seconds,
            config=config,
        )
        return (
            age_component * Decimal("0.250000")
            + reliability_component * Decimal("0.200000")
            + catalyst_component * Decimal("0.250000")
            + contradiction_component * Decimal("0.200000")
            + deadline_component * Decimal("0.100000")
        ).quantize(QUANT)


def _row_status(reason_codes: tuple[str, ...]) -> str:
    if any(reason.endswith("_block") or reason == DEADLINE_IMMINENT_REASON for reason in reason_codes):
        return "block"
    if reason_codes == (CURRENT_REASON,):
        return "pass"
    return "watch"


def _report_status(rows: tuple[ResearchEventEvidenceRefreshPriorityRow, ...]) -> str:
    if any(row.status == "block" for row in rows):
        return "block"
    if any(row.status == "watch" for row in rows):
        return "watch"
    return "pass"


def _report_reason_codes(
    rows: tuple[ResearchEventEvidenceRefreshPriorityRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return (EMPTY_REASON,)
    reasons = tuple(
        reason
        for reason in REPORT_TRIGGER_REASON_CODES
        if any(reason in row.reason_codes for row in rows)
    )
    if reasons:
        return reasons
    return (CURRENT_REASON,)


def _deadline_priority_component(
    nearest_deadline_seconds: Decimal,
    *,
    config: ResearchEventEvidenceRefreshPriorityConfig,
) -> Decimal:
    if nearest_deadline_seconds > config.deadline_near_seconds:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return (
            (config.deadline_near_seconds - nearest_deadline_seconds)
            / config.deadline_near_seconds
        ).quantize(QUANT)


def _row_sort_key(row: ResearchEventEvidenceRefreshPriorityRow) -> tuple[Decimal, str]:
    return (-row.refresh_priority_score, row.event_domain)


def _status_count(
    rows: tuple[ResearchEventEvidenceRefreshPriorityRow, ...],
    status: str,
) -> Decimal:
    return _count(sum(1 for row in rows if row.status == status))


def _sum_rows(
    rows: tuple[ResearchEventEvidenceRefreshPriorityRow, ...],
    field_name: str,
) -> Decimal:
    return sum((getattr(row, field_name) for row in rows), ZERO).quantize(QUANT)


def _average(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return (sum(values, ZERO) / Decimal(len(values))).quantize(QUANT)


def _age_seconds(generated_at: datetime, observed_at: datetime) -> Decimal:
    generated_at_utc = _as_utc("generated_at", generated_at)
    observed_at_utc = _as_utc("evidence_observed_at", observed_at)
    delta = generated_at_utc - observed_at_utc
    seconds = (
        Decimal(delta.days) * SECONDS_PER_DAY
        + Decimal(delta.seconds)
        + (Decimal(delta.microseconds) / MICROSECONDS_PER_SECOND)
    )
    if seconds < ZERO:
        raise ValueError("evidence_observed_at must not be in the future")
    return seconds.quantize(QUANT)


def _validate_config(config: ResearchEventEvidenceRefreshPriorityConfig) -> None:
    if config.fresh_age_seconds >= config.stale_age_seconds:
        raise ValueError("fresh_age_seconds must be less than stale_age_seconds")
    if config.critical_source_reliability_score > config.min_source_reliability_score:
        raise ValueError(
            "critical_source_reliability_score must not exceed min_source_reliability_score",
        )
    if config.catalyst_pressure_watch_threshold > config.catalyst_pressure_block_threshold:
        raise ValueError(
            "catalyst_pressure_watch_threshold must not exceed catalyst_pressure_block_threshold",
        )
    if config.contradiction_watch_threshold > config.contradiction_block_threshold:
        raise ValueError(
            "contradiction_watch_threshold must not exceed contradiction_block_threshold",
        )
    if config.deadline_imminent_seconds > config.deadline_near_seconds:
        raise ValueError("deadline_imminent_seconds must not exceed deadline_near_seconds")


def _validate_row(row: ResearchEventEvidenceRefreshPriorityRow) -> None:
    if row.evidence_count <= ZERO:
        raise ValueError("evidence_count must be positive")
    if row.average_evidence_age_seconds > row.max_evidence_age_seconds:
        raise ValueError("average_evidence_age_seconds must not exceed max")
    if row.status != _row_status(row.reason_codes):
        raise ValueError("status must match reason_codes")
    if row.status == "pass" and row.reason_codes != (CURRENT_REASON,):
        raise ValueError("pass rows must be current")


def _validate_report(report: ResearchEventEvidenceRefreshPriorityReport) -> None:
    if report.domain_count != _count(len(report.rows)):
        raise ValueError("domain_count must match rows")
    if report.evidence_count != _sum_rows(report.rows, "evidence_count"):
        raise ValueError("evidence_count must match rows")
    for status, field_name in (
        ("pass", "pass_domain_count"),
        ("watch", "watch_domain_count"),
        ("block", "block_domain_count"),
    ):
        if getattr(report, field_name) != _status_count(report.rows, status):
            raise ValueError(f"{field_name} must match rows")
    if report.oldest_average_evidence_age_seconds != max(
        (row.average_evidence_age_seconds for row in report.rows),
        default=ZERO,
    ).quantize(QUANT):
        raise ValueError("oldest_average_evidence_age_seconds must match rows")
    if report.lowest_source_reliability_score != min(
        (row.average_source_reliability_score for row in report.rows),
        default=ZERO,
    ).quantize(QUANT):
        raise ValueError("lowest_source_reliability_score must match rows")
    if report.highest_catalyst_pressure_score != max(
        (row.catalyst_pressure_score for row in report.rows),
        default=ZERO,
    ).quantize(QUANT):
        raise ValueError("highest_catalyst_pressure_score must match rows")
    if report.contradiction_count != _sum_rows(report.rows, "contradiction_count"):
        raise ValueError("contradiction_count must match rows")
    if report.nearest_deadline_seconds != min(
        (row.nearest_deadline_seconds for row in report.rows),
        default=ZERO,
    ).quantize(QUANT):
        raise ValueError("nearest_deadline_seconds must match rows")
    if report.status != _report_status(report.rows):
        raise ValueError("status must match rows")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")
    if report.rows != tuple(sorted(report.rows, key=_row_sort_key)):
        raise ValueError("rows must use deterministic priority sort")


def _normalize_rows(value: object) -> tuple[ResearchEventEvidenceRefreshPriorityRow, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("rows must be a list or tuple")
    rows = tuple(value)
    seen: set[str] = set()
    for row in rows:
        if type(row) is not ResearchEventEvidenceRefreshPriorityRow:
            raise ValueError("rows must contain ResearchEventEvidenceRefreshPriorityRow")
        require_paper_only_flags("priority row", row)
        if row.event_domain in seen:
            raise ValueError("rows must be unique by event_domain")
        seen.add(row.event_domain)
    return tuple(sorted(rows, key=_row_sort_key))


def _count(value: int) -> Decimal:
    return Decimal(value).quantize(QUANT)


def _require_positive_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_nonnegative_decimal(field_name, value)
    if decimal_value <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return decimal_value


def _require_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    decimal_value = value.quantize(QUANT)
    if decimal_value != value:
        raise ValueError(f"{field_name} must use six decimal places")
    if decimal_value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return decimal_value


def _require_ratio(field_name: str, value: object) -> Decimal:
    decimal_value = _require_nonnegative_decimal(field_name, value)
    if decimal_value > ONE:
        raise ValueError(f"{field_name} must be between zero and one")
    return decimal_value


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _normalize_reason_codes(
    field_name: str,
    value: object,
    allowed: tuple[str, ...],
) -> tuple[str, ...]:
    if type(value) not in (list, tuple):
        raise ValueError(f"{field_name} must be a list or tuple")
    reason_codes = tuple(value)
    if not reason_codes:
        raise ValueError(f"{field_name} must not be empty")
    for reason in reason_codes:
        if type(reason) is not str or reason not in allowed:
            raise ValueError(f"{field_name} must contain known reason codes")
    if len(set(reason_codes)) != len(reason_codes):
        raise ValueError(f"{field_name} must be unique")
    if tuple(reason for reason in allowed if reason in reason_codes) != reason_codes:
        raise ValueError(f"{field_name} must be deterministic")
    return reason_codes


def _require_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in RESEARCH_EVENT_EVIDENCE_REFRESH_PRIORITY_STATUSES:
        raise ValueError(f"{field_name} must be pass, watch, or block")


def _require_public_domain(field_name: str, value: object) -> str:
    _require_canonical_string(field_name, value)
    lowered = value.lower()
    unsafe_fragments = (
        "secret",
        "token",
        "key",
        "identifier",
        "reference",
        "url",
        "slug",
    )
    if any(fragment in lowered for fragment in unsafe_fragments):
        raise ValueError(f"{field_name} contains unsafe text")
    return value


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value:
        raise ValueError(f"{field_name} must not be empty")
    if value.strip() != value:
        raise ValueError(f"{field_name} must be stripped")
    if "\n" in value or "\r" in value or "\t" in value:
        raise ValueError(f"{field_name} must be single line")


__all__ = (
    "DEFAULT_RESEARCH_EVENT_EVIDENCE_REFRESH_PRIORITY_REPORT_CONFIG_VERSION",
    "RESEARCH_EVENT_EVIDENCE_REFRESH_PRIORITY_STATUSES",
    "ResearchEventEvidenceRefreshPriorityConfig",
    "ResearchEventEvidenceRefreshPriorityInput",
    "ResearchEventEvidenceRefreshPriorityReport",
    "ResearchEventEvidenceRefreshPriorityRow",
    "build_research_event_evidence_refresh_priority_report",
    "research_event_evidence_refresh_priority_report_digest",
    "research_event_evidence_refresh_priority_report_payload",
)
