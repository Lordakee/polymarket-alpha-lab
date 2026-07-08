"""Pure aggregate contradiction-memory report for caller-supplied research labels."""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable
from dataclasses import dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation
import hashlib
import json
from typing import Any


__all__ = (
    "ResearchEventSourceContradictionMemoryConfig",
    "ResearchEventSourceContradictionMemoryRecord",
    "ResearchEventSourceContradictionMemoryReasonCodeCount",
    "ResearchEventSourceContradictionMemoryReport",
    "ResearchEventSourceContradictionMemoryRow",
    "build_research_event_source_contradiction_memory_report",
    "research_event_source_contradiction_memory_report_payload",
    "validate_research_event_source_contradiction_memory_public_payload",
)


DEFAULT_CONFIG_VERSION = "research-event-source-contradiction-memory-report-v0"
STATUSES = ("pass", "watch", "block")
POSITION_LABELS = ("affirming", "negating", "unknown", "unresolved")
DIRECTIONAL_POSITION_LABELS = frozenset(("affirming", "negating"))
PUBLIC_LABEL_CHARACTERS = frozenset("abcdefghijklmnopqrstuvwxyz0123456789-_")
UNSAFE_PUBLIC_FRAGMENTS = (
    "://",
    "http",
    "www.",
    "/",
    "\\",
    "@",
    "?",
    "#",
    "private",
    "secret",
    "token",
    "key=",
    "candidate",
    "market",
    "question",
    "url",
    "text",
    "dsn",
    "data" + "base",
    "schema",
    "table",
    "wall" + "et",
    "order",
    "trade",
    "live" + "_trading",
    "live-trading",
    "sizing",
    "recommendation",
)
ZERO = Decimal("0")
ONE = Decimal("1")
RATIO_QUANTUM = Decimal("0.000001")
ZERO_SCORE = Decimal("0.000000")
DEFAULT_WATCH_RECHECK_URGENCY_SCORE = Decimal("0.350000")
DEFAULT_BLOCK_RECHECK_URGENCY_SCORE = Decimal("0.750000")


@dataclass(frozen=True)
class ResearchEventSourceContradictionMemoryConfig:
    config_version: str = DEFAULT_CONFIG_VERSION
    stale_evidence_seconds: Decimal = Decimal("86400")
    watch_recheck_urgency_score: Decimal = DEFAULT_WATCH_RECHECK_URGENCY_SCORE
    block_recheck_urgency_score: Decimal = DEFAULT_BLOCK_RECHECK_URGENCY_SCORE
    unresolved_disagreement_weight: Decimal = Decimal("0.450000")
    stale_evidence_weight: Decimal = Decimal("0.300000")
    domain_escalation_fit_weight: Decimal = Decimal("0.250000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_public_label("config_version", self.config_version)
        object.__setattr__(
            self,
            "stale_evidence_seconds",
            _require_positive_decimal(
                "stale_evidence_seconds",
                self.stale_evidence_seconds,
            ),
        )
        for field_name in (
            "watch_recheck_urgency_score",
            "block_recheck_urgency_score",
            "unresolved_disagreement_weight",
            "stale_evidence_weight",
            "domain_escalation_fit_weight",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_probability_decimal(field_name, getattr(self, field_name)),
            )
        if self.block_recheck_urgency_score <= self.watch_recheck_urgency_score:
            raise ValueError(
                "block_recheck_urgency_score must be greater than "
                "watch_recheck_urgency_score",
            )
        weight_sum = _quantize(
            self.unresolved_disagreement_weight
            + self.stale_evidence_weight
            + self.domain_escalation_fit_weight,
        )
        if weight_sum != ONE:
            raise ValueError(
                "unresolved_disagreement_weight, stale_evidence_weight, "
                "and domain_escalation_fit_weight must sum to 1",
            )
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class ResearchEventSourceContradictionMemoryRecord:
    memory_id: str
    event_slug: str
    domain_label: str
    source_label: str
    position_label: str
    observed_at: datetime
    resolved: bool = False
    domain_escalation_fit: bool = False
    reason_codes: tuple[str, ...] = ()
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_public_label("memory_id", self.memory_id)
        _require_public_label("event_slug", self.event_slug)
        _require_public_label("domain_label", self.domain_label)
        _require_public_label("source_label", self.source_label, aggregate_required=True)
        _require_enum("position_label", self.position_label, POSITION_LABELS)
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        _require_bool("resolved", self.resolved)
        _require_bool("domain_escalation_fit", self.domain_escalation_fit)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, allow_empty=True),
        )
        _require_hard_flags("memory record", self)


@dataclass(frozen=True)
class ResearchEventSourceContradictionMemoryRow:
    event_slug: str
    domain_label: str
    memory_record_count: Decimal
    source_label_count: Decimal
    position_label_count: Decimal
    contradiction_evidence_count: Decimal
    latest_observed_at: datetime
    latest_evidence_age_seconds: Decimal
    oldest_contradiction_evidence_age_seconds: Decimal | None
    unresolved_source_disagreement: bool
    stale_contradiction_evidence: bool
    domain_escalation_fit: bool
    recheck_urgency_score: Decimal
    status: str
    source_labels: tuple[str, ...]
    position_labels: tuple[str, ...]
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_public_label("event_slug", self.event_slug)
        _require_public_label("domain_label", self.domain_label)
        for field_name in (
            "memory_record_count",
            "source_label_count",
            "position_label_count",
            "contradiction_evidence_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_whole_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "latest_observed_at",
            _as_utc("latest_observed_at", self.latest_observed_at),
        )
        object.__setattr__(
            self,
            "latest_evidence_age_seconds",
            _require_nonnegative_decimal(
                "latest_evidence_age_seconds",
                self.latest_evidence_age_seconds,
            ),
        )
        object.__setattr__(
            self,
            "oldest_contradiction_evidence_age_seconds",
            _require_optional_nonnegative_decimal(
                "oldest_contradiction_evidence_age_seconds",
                self.oldest_contradiction_evidence_age_seconds,
            ),
        )
        _require_bool("unresolved_source_disagreement", self.unresolved_source_disagreement)
        _require_bool("stale_contradiction_evidence", self.stale_contradiction_evidence)
        _require_bool("domain_escalation_fit", self.domain_escalation_fit)
        object.__setattr__(
            self,
            "recheck_urgency_score",
            _require_probability_decimal(
                "recheck_urgency_score",
                self.recheck_urgency_score,
            ),
        )
        _require_enum("status", self.status, STATUSES)
        object.__setattr__(
            self,
            "source_labels",
            _normalize_public_label_tuple(
                "source_labels",
                self.source_labels,
                aggregate_required=True,
            ),
        )
        object.__setattr__(
            self,
            "position_labels",
            _normalize_position_label_tuple("position_labels", self.position_labels),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, allow_empty=False),
        )
        _require_hard_flags("row", self)
        _validate_row_consistency(self)


@dataclass(frozen=True)
class ResearchEventSourceContradictionMemoryReasonCodeCount:
    reason_code: str
    count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_reason_code("reason_code", self.reason_code)
        object.__setattr__(
            self,
            "count",
            _require_positive_whole_decimal("count", self.count),
        )
        _require_hard_flags("reason code count", self)


@dataclass(frozen=True)
class ResearchEventSourceContradictionMemoryReport:
    generated_at: datetime
    config_version: str
    event_count: Decimal
    memory_record_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    unresolved_source_disagreement_count: Decimal
    stale_contradiction_evidence_count: Decimal
    domain_escalation_fit_count: Decimal
    max_recheck_urgency_score: Decimal
    status: str
    rows: tuple[ResearchEventSourceContradictionMemoryRow, ...]
    reason_code_counts: tuple[ResearchEventSourceContradictionMemoryReasonCodeCount, ...]
    reason_codes: tuple[str, ...]
    derived_validation_digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_label("config_version", self.config_version)
        for field_name in (
            "event_count",
            "memory_record_count",
            "pass_count",
            "watch_count",
            "block_count",
            "unresolved_source_disagreement_count",
            "stale_contradiction_evidence_count",
            "domain_escalation_fit_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_whole_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "max_recheck_urgency_score",
            _require_probability_decimal(
                "max_recheck_urgency_score",
                self.max_recheck_urgency_score,
            ),
        )
        _require_enum("status", self.status, STATUSES)
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
        _require_digest("derived_validation_digest", self.derived_validation_digest)
        _require_hard_flags("report", self)
        _validate_report_consistency(self)


def build_research_event_source_contradiction_memory_report(
    memory_records: Iterable[ResearchEventSourceContradictionMemoryRecord],
    *,
    config: ResearchEventSourceContradictionMemoryConfig,
    generated_at: datetime,
) -> ResearchEventSourceContradictionMemoryReport:
    if type(config) is not ResearchEventSourceContradictionMemoryConfig:
        raise ValueError(
            "config must be a ResearchEventSourceContradictionMemoryConfig",
        )
    _require_hard_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    records = _normalize_memory_records(memory_records)
    for record in records:
        if record.observed_at > generated_at_utc:
            raise ValueError("observed_at must not be after generated_at")

    grouped: dict[tuple[str, str], list[ResearchEventSourceContradictionMemoryRecord]] = {}
    for record in records:
        grouped.setdefault((record.event_slug, record.domain_label), []).append(record)

    rows = tuple(
        _row_from_memory_records(
            event_slug=event_slug,
            domain_label=domain_label,
            records=tuple(grouped[(event_slug, domain_label)]),
            config=config,
            generated_at=generated_at_utc,
        )
        for event_slug, domain_label in sorted(grouped)
    )
    reason_codes = _report_reason_codes(rows)
    reason_code_counts = _reason_code_counts(rows, reason_codes)
    unsigned_values = _report_values(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        rows=rows,
        reason_code_counts=reason_code_counts,
        reason_codes=reason_codes,
    )
    digest = _digest_payload(_json_ready(unsigned_values))
    return ResearchEventSourceContradictionMemoryReport(
        **unsigned_values,
        derived_validation_digest=digest,
    )


def research_event_source_contradiction_memory_report_payload(
    report: ResearchEventSourceContradictionMemoryReport,
) -> dict[str, Any]:
    if type(report) is not ResearchEventSourceContradictionMemoryReport:
        raise ValueError(
            "report must be a ResearchEventSourceContradictionMemoryReport",
        )
    _require_hard_flags("report", report)
    _reject_unsafe_public_surface("report", report)
    payload = _json_ready(report)
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    validate_research_event_source_contradiction_memory_public_payload(payload)
    return payload


def validate_research_event_source_contradiction_memory_public_payload(
    payload: dict[str, Any],
) -> None:
    if type(payload) is not dict:
        raise ValueError("public payload must be a JSON object")
    _reject_unsafe_public_surface("public payload", payload)
    _reject_public_numerics(payload)
    _require_hard_flags("public payload", _PayloadFlags(payload))
    digest = payload.get("derived_validation_digest")
    _require_digest("derived_validation_digest", digest)
    unsigned_payload = dict(payload)
    unsigned_payload.pop("derived_validation_digest", None)
    expected_digest = _digest_payload(unsigned_payload)
    if digest != expected_digest:
        raise ValueError("derived_validation_digest does not match public payload")


def _row_from_memory_records(
    *,
    event_slug: str,
    domain_label: str,
    records: tuple[ResearchEventSourceContradictionMemoryRecord, ...],
    config: ResearchEventSourceContradictionMemoryConfig,
    generated_at: datetime,
) -> ResearchEventSourceContradictionMemoryRow:
    sorted_records = tuple(
        sorted(
            records,
            key=lambda record: (
                record.observed_at,
                record.memory_id,
                record.source_label,
                record.position_label,
            ),
        ),
    )
    latest_record = max(sorted_records, key=lambda record: record.observed_at)
    active_records = tuple(record for record in sorted_records if not record.resolved)
    active_directional_positions = {
        record.position_label
        for record in active_records
        if record.position_label in DIRECTIONAL_POSITION_LABELS
    }
    active_source_labels = {record.source_label for record in active_records}
    unresolved_disagreement = (
        len(active_directional_positions) > 1 and len(active_source_labels) > 1
    )
    contradiction_records = active_records if unresolved_disagreement else ()
    contradiction_ages = tuple(
        _duration_seconds(record.observed_at, generated_at) for record in contradiction_records
    )
    stale_contradiction = any(
        age_seconds >= config.stale_evidence_seconds for age_seconds in contradiction_ages
    )
    domain_escalation_fit = any(record.domain_escalation_fit for record in active_records)
    urgency_score = _recheck_urgency_score(
        unresolved_source_disagreement=unresolved_disagreement,
        stale_contradiction_evidence=stale_contradiction,
        domain_escalation_fit=domain_escalation_fit,
        config=config,
    )
    status = _status_from_score(urgency_score, config)
    reason_codes = _row_reason_codes(
        status=status,
        unresolved_source_disagreement=unresolved_disagreement,
        stale_contradiction_evidence=stale_contradiction,
        domain_escalation_fit=domain_escalation_fit,
        contradiction_evidence_count=_decimal_count(len(contradiction_records)),
        input_reason_codes=tuple(
            reason_code for record in sorted_records for reason_code in record.reason_codes
        ),
    )
    return ResearchEventSourceContradictionMemoryRow(
        event_slug=event_slug,
        domain_label=domain_label,
        memory_record_count=_decimal_count(len(sorted_records)),
        source_label_count=_decimal_count(
            len({record.source_label for record in sorted_records}),
        ),
        position_label_count=_decimal_count(
            len({record.position_label for record in sorted_records}),
        ),
        contradiction_evidence_count=_decimal_count(len(contradiction_records)),
        latest_observed_at=latest_record.observed_at,
        latest_evidence_age_seconds=_duration_seconds(
            latest_record.observed_at,
            generated_at,
        ),
        oldest_contradiction_evidence_age_seconds=(
            None if not contradiction_ages else max(contradiction_ages)
        ),
        unresolved_source_disagreement=unresolved_disagreement,
        stale_contradiction_evidence=stale_contradiction,
        domain_escalation_fit=domain_escalation_fit,
        recheck_urgency_score=urgency_score,
        status=status,
        source_labels=tuple(sorted({record.source_label for record in sorted_records})),
        position_labels=tuple(sorted({record.position_label for record in sorted_records})),
        reason_codes=reason_codes,
    )


def _report_values(
    *,
    generated_at: datetime,
    config_version: str,
    rows: tuple[ResearchEventSourceContradictionMemoryRow, ...],
    reason_code_counts: tuple[ResearchEventSourceContradictionMemoryReasonCodeCount, ...],
    reason_codes: tuple[str, ...],
) -> dict[str, Any]:
    return {
        "generated_at": generated_at,
        "config_version": config_version,
        "event_count": _decimal_count(len(rows)),
        "memory_record_count": sum(
            (row.memory_record_count for row in rows),
            ZERO,
        ),
        "pass_count": _decimal_count(_status_count(rows, "pass")),
        "watch_count": _decimal_count(_status_count(rows, "watch")),
        "block_count": _decimal_count(_status_count(rows, "block")),
        "unresolved_source_disagreement_count": _decimal_count(
            sum(1 for row in rows if row.unresolved_source_disagreement),
        ),
        "stale_contradiction_evidence_count": _decimal_count(
            sum(1 for row in rows if row.stale_contradiction_evidence),
        ),
        "domain_escalation_fit_count": _decimal_count(
            sum(1 for row in rows if row.domain_escalation_fit),
        ),
        "max_recheck_urgency_score": _max_recheck_urgency_score(rows),
        "status": _report_status(rows),
        "rows": rows,
        "reason_code_counts": reason_code_counts,
        "reason_codes": reason_codes,
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }


def _normalize_memory_records(
    memory_records: Iterable[ResearchEventSourceContradictionMemoryRecord],
) -> tuple[ResearchEventSourceContradictionMemoryRecord, ...]:
    if isinstance(memory_records, (str, bytes)):
        raise ValueError("memory_records must be an iterable")
    try:
        normalized = tuple(memory_records)
    except TypeError as exc:
        raise ValueError("memory_records must be an iterable") from exc
    seen: set[str] = set()
    for record in normalized:
        if type(record) is not ResearchEventSourceContradictionMemoryRecord:
            raise ValueError(
                "memory_records must contain "
                "ResearchEventSourceContradictionMemoryRecord values",
            )
        _require_hard_flags("memory record", record)
        if record.memory_id in seen:
            raise ValueError("memory_id values must be unique")
        seen.add(record.memory_id)
    return tuple(
        sorted(
            normalized,
            key=lambda record: (
                record.event_slug,
                record.domain_label,
                record.observed_at,
                record.memory_id,
            ),
        ),
    )


def _recheck_urgency_score(
    *,
    unresolved_source_disagreement: bool,
    stale_contradiction_evidence: bool,
    domain_escalation_fit: bool,
    config: ResearchEventSourceContradictionMemoryConfig,
) -> Decimal:
    score = ZERO
    if unresolved_source_disagreement:
        score += config.unresolved_disagreement_weight
    if stale_contradiction_evidence:
        score += config.stale_evidence_weight
    if domain_escalation_fit:
        score += config.domain_escalation_fit_weight
    return _quantize(min(ONE, score))


def _status_from_score(
    score: Decimal,
    config: ResearchEventSourceContradictionMemoryConfig,
) -> str:
    if score >= config.block_recheck_urgency_score:
        return "block"
    if score >= config.watch_recheck_urgency_score:
        return "watch"
    return "pass"


def _row_reason_codes(
    *,
    status: str,
    unresolved_source_disagreement: bool,
    stale_contradiction_evidence: bool,
    domain_escalation_fit: bool,
    contradiction_evidence_count: Decimal,
    input_reason_codes: tuple[str, ...],
) -> tuple[str, ...]:
    reason_codes: set[str] = {
        f"contradiction_memory_{status}",
        f"recheck_urgency_{status}",
    }
    reason_codes.add(
        "unresolved_source_disagreement"
        if unresolved_source_disagreement
        else "no_unresolved_source_disagreement",
    )
    if contradiction_evidence_count > ZERO:
        reason_codes.add(
            "stale_contradiction_evidence"
            if stale_contradiction_evidence
            else "fresh_contradiction_evidence",
        )
    else:
        reason_codes.add("no_contradiction_evidence")
    reason_codes.add(
        "domain_escalation_fit"
        if domain_escalation_fit
        else "domain_escalation_not_fit",
    )
    for reason_code in input_reason_codes:
        reason_codes.add(f"input_{reason_code}")
    return tuple(sorted(reason_codes))


def _report_reason_codes(
    rows: tuple[ResearchEventSourceContradictionMemoryRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return ("contradiction_memory_no_records",)
    if all(row.status == "pass" for row in rows):
        return ("contradiction_memory_pass",)
    return tuple(sorted({reason_code for row in rows for reason_code in row.reason_codes}))


def _report_status(rows: tuple[ResearchEventSourceContradictionMemoryRow, ...]) -> str:
    if any(row.status == "block" for row in rows):
        return "block"
    if any(row.status == "watch" for row in rows):
        return "watch"
    return "pass"


def _reason_code_counts(
    rows: tuple[ResearchEventSourceContradictionMemoryRow, ...],
    reason_codes: tuple[str, ...],
) -> tuple[ResearchEventSourceContradictionMemoryReasonCodeCount, ...]:
    if not rows:
        return (
            ResearchEventSourceContradictionMemoryReasonCodeCount(
                reason_code=reason_codes[0],
                count=ONE,
            ),
        )
    counts: Counter[str] = Counter()
    for row in rows:
        counts.update(row.reason_codes)
    return tuple(
        ResearchEventSourceContradictionMemoryReasonCodeCount(
            reason_code=reason_code,
            count=_decimal_count(count),
        )
        for reason_code, count in sorted(counts.items(), key=lambda item: item[0])
    )


def _max_recheck_urgency_score(
    rows: tuple[ResearchEventSourceContradictionMemoryRow, ...],
) -> Decimal:
    if not rows:
        return ZERO_SCORE
    return max(row.recheck_urgency_score for row in rows)


def _status_count(
    rows: tuple[ResearchEventSourceContradictionMemoryRow, ...],
    status: str,
) -> int:
    return sum(1 for row in rows if row.status == status)


def _normalize_rows(
    rows: object,
) -> tuple[ResearchEventSourceContradictionMemoryRow, ...]:
    if type(rows) is not tuple:
        raise ValueError("rows must be a tuple")
    for row in rows:
        if type(row) is not ResearchEventSourceContradictionMemoryRow:
            raise ValueError(
                "rows must contain ResearchEventSourceContradictionMemoryRow values",
            )
        _require_hard_flags("row", row)
    expected = tuple(sorted(rows, key=lambda row: (row.event_slug, row.domain_label)))
    if rows != expected:
        raise ValueError("rows must use deterministic sorting")
    return rows


def _normalize_reason_code_counts(
    counts: object,
) -> tuple[ResearchEventSourceContradictionMemoryReasonCodeCount, ...]:
    if type(counts) is not tuple:
        raise ValueError("reason_code_counts must be a tuple")
    for count in counts:
        if type(count) is not ResearchEventSourceContradictionMemoryReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "ResearchEventSourceContradictionMemoryReasonCodeCount values",
            )
        _require_hard_flags("reason code count", count)
    expected = tuple(sorted(counts, key=lambda count: count.reason_code))
    if counts != expected:
        raise ValueError("reason_code_counts must use deterministic sorting")
    return counts


def _validate_row_consistency(
    row: ResearchEventSourceContradictionMemoryRow,
) -> None:
    if row.memory_record_count <= ZERO:
        raise ValueError("memory_record_count must be positive")
    if row.source_label_count != _decimal_count(len(row.source_labels)):
        raise ValueError("source_label_count must match source_labels")
    if row.position_label_count != _decimal_count(len(row.position_labels)):
        raise ValueError("position_label_count must match position_labels")
    if row.contradiction_evidence_count > row.memory_record_count:
        raise ValueError("contradiction_evidence_count must not exceed memory_record_count")
    if row.contradiction_evidence_count == ZERO:
        if row.oldest_contradiction_evidence_age_seconds is not None:
            raise ValueError("oldest contradiction age must be absent without contradiction")
        if row.stale_contradiction_evidence:
            raise ValueError("stale contradiction requires contradiction evidence")
    elif row.oldest_contradiction_evidence_age_seconds is None:
        raise ValueError("oldest contradiction age is required with contradiction evidence")
    if (
        row.unresolved_source_disagreement
        and "unresolved_source_disagreement" not in row.reason_codes
    ):
        raise ValueError("unresolved rows require unresolved_source_disagreement reason")
    if (
        row.stale_contradiction_evidence
        and "stale_contradiction_evidence" not in row.reason_codes
    ):
        raise ValueError("stale rows require stale_contradiction_evidence reason")
    if row.domain_escalation_fit and "domain_escalation_fit" not in row.reason_codes:
        raise ValueError("domain escalation rows require domain_escalation_fit reason")
    if f"contradiction_memory_{row.status}" not in row.reason_codes:
        raise ValueError("status must match contradiction memory reason")
    if f"recheck_urgency_{row.status}" not in row.reason_codes:
        raise ValueError("status must match recheck urgency reason")


def _validate_report_consistency(
    report: ResearchEventSourceContradictionMemoryReport,
) -> None:
    expected_values = _report_values(
        generated_at=report.generated_at,
        config_version=report.config_version,
        rows=report.rows,
        reason_code_counts=report.reason_code_counts,
        reason_codes=report.reason_codes,
    )
    for field_name, expected_value in expected_values.items():
        if getattr(report, field_name) != expected_value:
            raise ValueError(f"{field_name} must match rows")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")
    if report.reason_code_counts != _reason_code_counts(report.rows, report.reason_codes):
        raise ValueError("reason_code_counts must match rows")
    unsigned_payload = _json_ready(_unsigned_report_payload(report))
    expected_digest = _digest_payload(unsigned_payload)
    if report.derived_validation_digest != expected_digest:
        raise ValueError("derived_validation_digest must match report payload")


def _unsigned_report_payload(
    report: ResearchEventSourceContradictionMemoryReport,
) -> dict[str, Any]:
    payload = _json_ready(report)
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    payload.pop("derived_validation_digest", None)
    return payload


def _duration_seconds(start: datetime, end: datetime) -> Decimal:
    delta = end - start
    return (
        Decimal(delta.days * 86_400)
        + Decimal(delta.seconds)
        + (Decimal(delta.microseconds) / Decimal("1000000"))
    )


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    try:
        return +value
    except InvalidOperation as exc:
        raise ValueError(f"{field_name} must be finite") from exc


def _require_positive_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _require_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _require_optional_nonnegative_decimal(
    field_name: str,
    value: object,
) -> Decimal | None:
    if value is None:
        return None
    return _require_nonnegative_decimal(field_name, value)


def _require_probability_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < ZERO or normalized > ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return _quantize(normalized)


def _require_positive_whole_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_positive_decimal(field_name, value)
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{field_name} must be a whole count")
    return normalized


def _require_nonnegative_whole_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_nonnegative_decimal(field_name, value)
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{field_name} must be a whole count")
    return normalized


def _decimal_count(value: int) -> Decimal:
    if type(value) is not int:
        raise ValueError("count source must be an int")
    if value < 0:
        raise ValueError("count source must be nonnegative")
    return Decimal(value)


def _quantize(value: Decimal) -> Decimal:
    return value.quantize(RATIO_QUANTUM)


def _require_bool(field_name: str, value: object) -> None:
    if type(value) is not bool:
        raise ValueError(f"{field_name} must be a bool")


def _require_public_label(
    field_name: str,
    value: object,
    *,
    aggregate_required: bool = False,
) -> str:
    if type(value) is not str or not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a nonempty public label")
    if value.lower() != value:
        raise ValueError(f"{field_name} must be lowercase")
    if any(fragment in value for fragment in UNSAFE_PUBLIC_FRAGMENTS):
        raise ValueError(f"{field_name} must be public-safe")
    if any(character not in PUBLIC_LABEL_CHARACTERS for character in value):
        raise ValueError(f"{field_name} must use public label characters")
    if value.startswith(("-", "_")) or value.endswith(("-", "_")):
        raise ValueError(f"{field_name} must not start or end with punctuation")
    if field_name == "event_slug":
        event_suffix = value.removeprefix("event-")
        if event_suffix == value or "-" in event_suffix or "_" in event_suffix:
            raise ValueError("event_slug must be a synthetic event label")
    if aggregate_required and not value.endswith("-aggregate"):
        raise ValueError(f"{field_name} must be an aggregate label")
    return value


def _require_reason_code(field_name: str, value: object) -> str:
    if type(value) is not str or not value or value.strip() != value:
        raise ValueError(f"{field_name} must contain public reason codes")
    if value.lower() != value:
        raise ValueError(f"{field_name} must contain lowercase reason codes")
    if any(fragment in value for fragment in UNSAFE_PUBLIC_FRAGMENTS):
        raise ValueError(f"{field_name} must contain public-safe reason codes")
    if any(character not in PUBLIC_LABEL_CHARACTERS for character in value):
        raise ValueError(f"{field_name} must contain canonical reason codes")
    return value


def _require_enum(field_name: str, value: object, allowed: tuple[str, ...]) -> None:
    if type(value) is not str or value not in allowed:
        raise ValueError(f"{field_name} must be one of {allowed}")


def _normalize_public_label_tuple(
    field_name: str,
    values: object,
    *,
    aggregate_required: bool,
) -> tuple[str, ...]:
    if type(values) is not tuple:
        raise ValueError(f"{field_name} must be a tuple")
    normalized = tuple(
        _require_public_label(
            field_name,
            value,
            aggregate_required=aggregate_required,
        )
        for value in values
    )
    if not normalized:
        raise ValueError(f"{field_name} must be nonempty")
    expected = tuple(sorted(set(normalized)))
    if normalized != expected:
        raise ValueError(f"{field_name} must be unique and sorted")
    return normalized


def _normalize_position_label_tuple(
    field_name: str,
    values: object,
) -> tuple[str, ...]:
    if type(values) is not tuple:
        raise ValueError(f"{field_name} must be a tuple")
    normalized: list[str] = []
    for value in values:
        _require_enum(field_name, value, POSITION_LABELS)
        normalized.append(value)
    if not normalized:
        raise ValueError(f"{field_name} must be nonempty")
    expected = tuple(sorted(set(normalized)))
    if tuple(normalized) != expected:
        raise ValueError(f"{field_name} must be unique and sorted")
    return tuple(normalized)


def _normalize_reason_codes(
    field_name: str,
    values: object,
    *,
    allow_empty: bool,
) -> tuple[str, ...]:
    if type(values) is not tuple:
        raise ValueError(f"{field_name} must be a tuple")
    normalized = tuple(_require_reason_code(field_name, value) for value in values)
    if not allow_empty and not normalized:
        raise ValueError(f"{field_name} must be nonempty")
    return tuple(sorted(set(normalized)))


def _require_digest(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if len(value) != 64 or any(character not in "0123456789abcdef" for character in value):
        raise ValueError(f"{field_name} must be a lowercase sha256 hex digest")
    return value


@dataclass(frozen=True)
class _PayloadFlags:
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


def _require_hard_flags(label: str, value: object) -> None:
    if getattr(value, "paper_only", None) is not True:
        raise ValueError(f"paper_only must be True for {label}")
    if getattr(value, "report_only", None) is not True:
        raise ValueError(f"report_only must be True for {label}")
    if getattr(value, "readonly", None) is not True:
        raise ValueError(f"readonly must be True for {label}")


def _json_ready(value: Any) -> Any:
    if value is None:
        return None
    if is_dataclass(value) and not isinstance(value, type):
        return {field.name: _json_ready(getattr(value, field.name)) for field in fields(value)}
    if isinstance(value, Decimal):
        if type(value) is not Decimal:
            raise ValueError("JSON Decimal value must be a Decimal")
        if not value.is_finite():
            raise ValueError("JSON Decimal value must be finite")
        return str(value)
    if isinstance(value, datetime):
        if type(value) is not datetime:
            raise ValueError("JSON datetime value must be a datetime")
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("JSON datetime value must be timezone-aware")
        return value.astimezone(UTC).isoformat()
    if isinstance(value, float):
        raise ValueError("JSON value must not be a float")
    if type(value) is int:
        raise ValueError("JSON numeric value must use Decimal")
    if isinstance(value, (str, bool)):
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


def _digest_payload(payload: dict[str, Any]) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(encoded).hexdigest()


def _reject_unsafe_public_surface(label: str, value: object) -> None:
    if is_dataclass(value) and not isinstance(value, type):
        _reject_unsafe_public_surface(label, _json_ready(value))
        return
    if type(value) is str:
        if any(fragment in value.lower() for fragment in UNSAFE_PUBLIC_FRAGMENTS):
            raise ValueError(f"unsafe public value in {label}")
        return
    if isinstance(value, dict):
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            if any(fragment in key.lower() for fragment in UNSAFE_PUBLIC_FRAGMENTS):
                raise ValueError(f"unsafe public field in {label}")
            _reject_unsafe_public_surface(label, item)
            if key == "event_slug":
                _require_public_label("event_slug", item)
        return
    if isinstance(value, (list, tuple)):
        for item in value:
            _reject_unsafe_public_surface(label, item)


def _reject_public_numerics(value: object) -> None:
    if isinstance(value, float) or type(value) is int:
        raise ValueError("public payload numerics must be Decimal-derived strings")
    if isinstance(value, dict):
        for item in value.values():
            _reject_public_numerics(item)
        return
    if isinstance(value, list):
        for item in value:
            _reject_public_numerics(item)
