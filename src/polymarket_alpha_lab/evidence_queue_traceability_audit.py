"""Pure report-only reducer for evidence queue traceability diagnostics."""

from __future__ import annotations

from dataclasses import dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal
import hashlib
import json

from polymarket_alpha_lab.team_paper_guard import require_paper_only_flags
from polymarket_alpha_lab.team_taxonomy import require_team_id


DEFAULT_EVIDENCE_QUEUE_TRACEABILITY_AUDIT_CONFIG_VERSION = (
    "evidence-queue-traceability-audit-v0"
)

PASS_REASON = "evidence_queue_traceability_audit_passed"
NO_QUEUE_ROWS_REASON = "evidence_queue_traceability_no_queue_rows"
MISSING_TRACE_REASON = "evidence_queue_traceability_missing_trace_links"
ORPHAN_EVIDENCE_REASON = "evidence_queue_traceability_orphan_evidence"
DUPLICATE_QUEUE_REFERENCE_REASON = (
    "evidence_queue_traceability_duplicate_queue_references"
)
STALE_EVIDENCE_LINK_REASON = "evidence_queue_traceability_stale_evidence_links"
REDACTED_DIAGNOSTIC_REASON = "evidence_queue_traceability_redacted_diagnostics"

REASON_CODES = (
    PASS_REASON,
    NO_QUEUE_ROWS_REASON,
    MISSING_TRACE_REASON,
    ORPHAN_EVIDENCE_REASON,
    DUPLICATE_QUEUE_REFERENCE_REASON,
    STALE_EVIDENCE_LINK_REASON,
    REDACTED_DIAGNOSTIC_REASON,
)
TRACE_STATUSES = ("pass", "watch", "blocked")
REPORT_ACTIONS = {
    "pass": "continue_report_only_queue_review",
    "watch": "review_traceability_watch_items",
    "blocked": "block_queue_rows_until_trace_links_are_repaired",
}
ZERO = Decimal("0")
MICROSECONDS_PER_SECOND = Decimal("1000000")
UNSAFE_PUBLIC_REF_FRAGMENTS = frozenset(
    (
        "acc" + "ount",
        "au" + "th",
        "bal" + "ance",
        "b" + "uy",
        "can" + "cel",
        "credential",
        "exchange_mutation",
        "market_" + "slug",
        "ord" + "er",
        "pay" + "load",
        "private" + "-key",
        "private" + "_key",
        "private" + "key",
        "ques" + "tion",
        "raw",
        "selected-side",
        "selected" + "_side",
        "se" + "ll",
        "scoring-side",
        "scoring" + "_side",
        "submit",
        "token",
        "wal" + "let",
    )
)

__all__ = (
    "DEFAULT_EVIDENCE_QUEUE_TRACEABILITY_AUDIT_CONFIG_VERSION",
    "EvidencePacketReference",
    "EvidenceQueueTraceabilityAuditConfig",
    "EvidenceQueueTraceabilityAuditReport",
    "EvidenceQueueTraceabilityOrphanEvidenceRow",
    "EvidenceQueueTraceabilityQueueRow",
    "EvidenceQueueTraceabilityQueueTraceRow",
    "build_evidence_queue_traceability_audit_report",
    "evidence_queue_traceability_audit_payload",
)


@dataclass(frozen=True)
class EvidenceQueueTraceabilityAuditConfig:
    config_version: str = DEFAULT_EVIDENCE_QUEUE_TRACEABILITY_AUDIT_CONFIG_VERSION
    stale_trace_link_seconds: Decimal = Decimal("86400")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("config_version", self.config_version)
        object.__setattr__(
            self,
            "stale_trace_link_seconds",
            _normalize_positive_decimal(
                "stale_trace_link_seconds",
                self.stale_trace_link_seconds,
            ),
        )
        require_paper_only_flags("EvidenceQueueTraceabilityAuditConfig", self)


@dataclass(frozen=True)
class EvidencePacketReference:
    redacted_evidence_ref: str
    redacted_packet_ref: str
    team_id: str
    last_seen_at: datetime
    source_config_version: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_public_ref("redacted_evidence_ref", self.redacted_evidence_ref)
        _require_public_ref("redacted_packet_ref", self.redacted_packet_ref)
        object.__setattr__(self, "team_id", require_team_id("team_id", self.team_id))
        object.__setattr__(self, "last_seen_at", _as_utc("last_seen_at", self.last_seen_at))
        _require_canonical_string("source_config_version", self.source_config_version)
        require_paper_only_flags("EvidencePacketReference", self)


@dataclass(frozen=True)
class EvidenceQueueTraceabilityQueueRow:
    redacted_queue_ref: str
    team_id: str
    redacted_packet_ref: str | None
    redacted_evidence_refs: tuple[str, ...]
    created_at: datetime
    queue_status: str
    source_config_version: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_public_ref("redacted_queue_ref", self.redacted_queue_ref)
        object.__setattr__(self, "team_id", require_team_id("team_id", self.team_id))
        if self.redacted_packet_ref is not None:
            _require_public_ref("redacted_packet_ref", self.redacted_packet_ref)
        object.__setattr__(
            self,
            "redacted_evidence_refs",
            _normalize_public_refs("evidence_refs", self.redacted_evidence_refs),
        )
        object.__setattr__(self, "created_at", _as_utc("created_at", self.created_at))
        _require_queue_status("queue_status", self.queue_status)
        _require_canonical_string("source_config_version", self.source_config_version)
        require_paper_only_flags("EvidenceQueueTraceabilityQueueRow", self)


@dataclass(frozen=True)
class EvidenceQueueTraceabilityQueueTraceRow:
    redacted_queue_ref: str
    team_id: str
    redacted_packet_ref: str | None
    queue_status: str
    missing_trace_link_count: Decimal
    stale_evidence_link_count: Decimal
    duplicate_queue_reference_count: Decimal
    redacted_traceability_diagnostic_count: Decimal
    trace_status: str
    reason_codes: tuple[str, ...]
    created_at: datetime | None = None
    newest_evidence_link_age_seconds: Decimal | None = None
    oldest_evidence_link_age_seconds: Decimal | None = None
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_public_ref("redacted_queue_ref", self.redacted_queue_ref)
        object.__setattr__(self, "team_id", require_team_id("team_id", self.team_id))
        if self.redacted_packet_ref is not None:
            _require_public_ref("redacted_packet_ref", self.redacted_packet_ref)
        _require_queue_status("queue_status", self.queue_status)
        for field_name in (
            "missing_trace_link_count",
            "stale_evidence_link_count",
            "duplicate_queue_reference_count",
            "redacted_traceability_diagnostic_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        _require_trace_status("trace_status", self.trace_status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        if self.created_at is not None:
            object.__setattr__(self, "created_at", _as_utc("created_at", self.created_at))
        for field_name in (
            "newest_evidence_link_age_seconds",
            "oldest_evidence_link_age_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_optional_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        _validate_queue_trace_row(self)
        require_paper_only_flags("EvidenceQueueTraceabilityQueueTraceRow", self)


@dataclass(frozen=True)
class EvidenceQueueTraceabilityOrphanEvidenceRow:
    redacted_evidence_ref: str
    redacted_packet_ref: str
    team_id: str
    evidence_link_age_seconds: Decimal
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_public_ref("redacted_evidence_ref", self.redacted_evidence_ref)
        _require_public_ref("redacted_packet_ref", self.redacted_packet_ref)
        object.__setattr__(self, "team_id", require_team_id("team_id", self.team_id))
        object.__setattr__(
            self,
            "evidence_link_age_seconds",
            _normalize_nonnegative_decimal(
                "evidence_link_age_seconds",
                self.evidence_link_age_seconds,
            ),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        if self.reason_codes != (ORPHAN_EVIDENCE_REASON,):
            raise ValueError("reason_codes must match orphan evidence")
        require_paper_only_flags("EvidenceQueueTraceabilityOrphanEvidenceRow", self)


@dataclass(frozen=True)
class EvidenceQueueTraceabilityAuditReport:
    generated_at: datetime
    config_version: str
    traceability_status: str
    recommended_report_action: str
    evidence_reference_count: Decimal
    queue_row_count: Decimal
    missing_trace_link_count: Decimal
    orphan_evidence_count: Decimal
    duplicate_queue_reference_count: Decimal
    stale_evidence_link_count: Decimal
    redacted_traceability_diagnostic_count: Decimal
    stale_trace_link_seconds: Decimal
    queue_trace_rows: tuple[EvidenceQueueTraceabilityQueueTraceRow, ...]
    orphan_evidence_rows: tuple[EvidenceQueueTraceabilityOrphanEvidenceRow, ...]
    reason_codes: tuple[str, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        _require_trace_status("traceability_status", self.traceability_status)
        _require_canonical_string("recommended_report_action", self.recommended_report_action)
        for field_name in (
            "evidence_reference_count",
            "queue_row_count",
            "missing_trace_link_count",
            "orphan_evidence_count",
            "duplicate_queue_reference_count",
            "stale_evidence_link_count",
            "redacted_traceability_diagnostic_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "stale_trace_link_seconds",
            _normalize_positive_decimal(
                "stale_trace_link_seconds",
                self.stale_trace_link_seconds,
            ),
        )
        object.__setattr__(
            self,
            "queue_trace_rows",
            _normalize_queue_trace_rows(self.queue_trace_rows),
        )
        object.__setattr__(
            self,
            "orphan_evidence_rows",
            _normalize_orphan_evidence_rows(self.orphan_evidence_rows),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        _validate_report(self)
        require_paper_only_flags("EvidenceQueueTraceabilityAuditReport", self)
        _set_or_validate_derived_validation_digest(self)

    @property
    def payload(self) -> dict[str, object]:
        return evidence_queue_traceability_audit_payload(self)


def build_evidence_queue_traceability_audit_report(
    evidence_rows: object,
    queue_rows: object,
    *,
    config: EvidenceQueueTraceabilityAuditConfig,
    generated_at: datetime,
) -> EvidenceQueueTraceabilityAuditReport:
    if type(config) is not EvidenceQueueTraceabilityAuditConfig:
        raise ValueError("config must be an EvidenceQueueTraceabilityAuditConfig")
    if type(generated_at) is not datetime:
        raise ValueError("generated_at must be a datetime")
    require_paper_only_flags("config", config)

    generated_at_utc = _as_utc("generated_at", generated_at)
    evidence = _normalize_evidence_rows(evidence_rows, generated_at=generated_at_utc)
    queue = _normalize_queue_rows(queue_rows, generated_at=generated_at_utc)
    evidence_by_ref = {row.redacted_evidence_ref: row for row in evidence}
    queue_ref_counts = _queue_reference_counts(queue)
    referenced_evidence_refs = frozenset(
        evidence_ref
        for row in queue
        for evidence_ref in row.redacted_evidence_refs
    )
    queue_trace_rows = tuple(
        _queue_trace_row(
            row,
            evidence_by_ref=evidence_by_ref,
            queue_ref_counts=queue_ref_counts,
            config=config,
            generated_at=generated_at_utc,
        )
        for row in queue
    )
    orphan_evidence_rows = tuple(
        _orphan_evidence_row(row, generated_at=generated_at_utc)
        for row in evidence
        if row.redacted_evidence_ref not in referenced_evidence_refs
    )
    reason_codes = _report_reason_codes(
        queue_row_count=len(queue),
        missing_trace_link_count=sum(
            int(row.missing_trace_link_count) for row in queue_trace_rows
        ),
        orphan_evidence_count=len(orphan_evidence_rows),
        duplicate_queue_reference_count=sum(
            int(row.duplicate_queue_reference_count) for row in queue_trace_rows
        ),
        stale_evidence_link_count=sum(
            int(row.stale_evidence_link_count) for row in queue_trace_rows
        ),
        redacted_traceability_diagnostic_count=sum(
            int(row.redacted_traceability_diagnostic_count)
            for row in queue_trace_rows
        ),
    )
    traceability_status = _traceability_status(reason_codes)

    return EvidenceQueueTraceabilityAuditReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        traceability_status=traceability_status,
        recommended_report_action=REPORT_ACTIONS[traceability_status],
        evidence_reference_count=_decimal_count(len(evidence)),
        queue_row_count=_decimal_count(len(queue)),
        missing_trace_link_count=_decimal_count(
            sum(int(row.missing_trace_link_count) for row in queue_trace_rows),
        ),
        orphan_evidence_count=_decimal_count(len(orphan_evidence_rows)),
        duplicate_queue_reference_count=_decimal_count(
            sum(int(row.duplicate_queue_reference_count) for row in queue_trace_rows),
        ),
        stale_evidence_link_count=_decimal_count(
            sum(int(row.stale_evidence_link_count) for row in queue_trace_rows),
        ),
        redacted_traceability_diagnostic_count=_decimal_count(
            sum(
                int(row.redacted_traceability_diagnostic_count)
                for row in queue_trace_rows
            ),
        ),
        stale_trace_link_seconds=config.stale_trace_link_seconds,
        queue_trace_rows=queue_trace_rows,
        orphan_evidence_rows=orphan_evidence_rows,
        reason_codes=reason_codes,
    )


def evidence_queue_traceability_audit_payload(
    value: EvidenceQueueTraceabilityAuditReport | dict[str, object],
) -> dict[str, object]:
    if type(value) is EvidenceQueueTraceabilityAuditReport:
        _validate_report(value)
        _validate_derived_validation_digest(value)
        payload = _payload_value(value)
    elif type(value) is dict:
        payload = value
    else:
        raise ValueError("value must be an EvidenceQueueTraceabilityAuditReport or dict")
    if type(payload) is not dict:
        raise ValueError("public payload must be a dict")
    _validate_public_payload(payload)
    return dict(payload)


def _queue_trace_row(
    row: EvidenceQueueTraceabilityQueueRow,
    *,
    evidence_by_ref: dict[str, EvidencePacketReference],
    queue_ref_counts: dict[tuple[str, str | None], int],
    config: EvidenceQueueTraceabilityAuditConfig,
    generated_at: datetime,
) -> EvidenceQueueTraceabilityQueueTraceRow:
    evidence_refs = row.redacted_evidence_refs
    linked_evidence = tuple(
        evidence_by_ref[evidence_ref]
        for evidence_ref in evidence_refs
        if evidence_ref in evidence_by_ref
    )
    missing_count = sum(
        1 for evidence_ref in evidence_refs if evidence_ref not in evidence_by_ref
    )
    if row.redacted_packet_ref is None or not evidence_refs:
        missing_count += 1
    link_ages = tuple(
        _age_seconds(generated_at, evidence.last_seen_at)
        for evidence in linked_evidence
    )
    stale_count = sum(1 for age in link_ages if age > config.stale_trace_link_seconds)
    duplicate_count = (
        1 if queue_ref_counts[(row.team_id, row.redacted_packet_ref)] > 1 else 0
    )
    redacted_count = Decimal("1") if missing_count or duplicate_count else ZERO
    reason_codes = _queue_reason_codes(
        missing_trace_link_count=missing_count,
        stale_evidence_link_count=stale_count,
        duplicate_queue_reference_count=duplicate_count,
        redacted_traceability_diagnostic_count=int(redacted_count),
    )
    return EvidenceQueueTraceabilityQueueTraceRow(
        redacted_queue_ref=row.redacted_queue_ref,
        team_id=row.team_id,
        redacted_packet_ref=row.redacted_packet_ref,
        queue_status=row.queue_status,
        missing_trace_link_count=_decimal_count(missing_count),
        stale_evidence_link_count=_decimal_count(stale_count),
        duplicate_queue_reference_count=_decimal_count(duplicate_count),
        redacted_traceability_diagnostic_count=redacted_count,
        trace_status=_traceability_status(reason_codes),
        reason_codes=reason_codes,
        created_at=row.created_at,
        newest_evidence_link_age_seconds=min(link_ages) if link_ages else None,
        oldest_evidence_link_age_seconds=max(link_ages) if link_ages else None,
    )


def _orphan_evidence_row(
    row: EvidencePacketReference,
    *,
    generated_at: datetime,
) -> EvidenceQueueTraceabilityOrphanEvidenceRow:
    return EvidenceQueueTraceabilityOrphanEvidenceRow(
        redacted_evidence_ref=row.redacted_evidence_ref,
        redacted_packet_ref=row.redacted_packet_ref,
        team_id=row.team_id,
        evidence_link_age_seconds=_age_seconds(generated_at, row.last_seen_at),
        reason_codes=(ORPHAN_EVIDENCE_REASON,),
    )


def _queue_reason_codes(
    *,
    missing_trace_link_count: int,
    stale_evidence_link_count: int,
    duplicate_queue_reference_count: int,
    redacted_traceability_diagnostic_count: int,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    if missing_trace_link_count:
        reason_codes.append(MISSING_TRACE_REASON)
    if duplicate_queue_reference_count:
        reason_codes.append(DUPLICATE_QUEUE_REFERENCE_REASON)
    if stale_evidence_link_count:
        reason_codes.append(STALE_EVIDENCE_LINK_REASON)
    if redacted_traceability_diagnostic_count:
        reason_codes.append(REDACTED_DIAGNOSTIC_REASON)
    if not reason_codes:
        reason_codes.append(PASS_REASON)
    return tuple(reason_codes)


def _report_reason_codes(
    *,
    queue_row_count: int,
    missing_trace_link_count: int,
    orphan_evidence_count: int,
    duplicate_queue_reference_count: int,
    stale_evidence_link_count: int,
    redacted_traceability_diagnostic_count: int,
) -> tuple[str, ...]:
    if queue_row_count == 0:
        return (NO_QUEUE_ROWS_REASON,)
    reason_codes: list[str] = []
    if missing_trace_link_count:
        reason_codes.append(MISSING_TRACE_REASON)
    if orphan_evidence_count:
        reason_codes.append(ORPHAN_EVIDENCE_REASON)
    if duplicate_queue_reference_count:
        reason_codes.append(DUPLICATE_QUEUE_REFERENCE_REASON)
    if stale_evidence_link_count:
        reason_codes.append(STALE_EVIDENCE_LINK_REASON)
    if redacted_traceability_diagnostic_count:
        reason_codes.append(REDACTED_DIAGNOSTIC_REASON)
    if not reason_codes:
        reason_codes.append(PASS_REASON)
    return tuple(reason_codes)


def _traceability_status(reason_codes: tuple[str, ...]) -> str:
    if reason_codes == (PASS_REASON,):
        return "pass"
    if any(
        reason_code in reason_codes
        for reason_code in (NO_QUEUE_ROWS_REASON, MISSING_TRACE_REASON)
    ):
        return "blocked"
    if any(
        reason_code in reason_codes
        for reason_code in (
            ORPHAN_EVIDENCE_REASON,
            DUPLICATE_QUEUE_REFERENCE_REASON,
            STALE_EVIDENCE_LINK_REASON,
            REDACTED_DIAGNOSTIC_REASON,
        )
    ):
        return "watch"
    raise ValueError("reason_codes must contain known traceability reasons")


def _normalize_evidence_rows(
    rows: object,
    *,
    generated_at: datetime,
) -> tuple[EvidencePacketReference, ...]:
    if type(rows) not in (list, tuple):
        raise ValueError("evidence_rows must be a list or tuple")
    normalized = tuple(rows)
    seen_refs: set[str] = set()
    for row in normalized:
        if type(row) is not EvidencePacketReference:
            raise ValueError("evidence_rows must contain EvidencePacketReference values")
        require_paper_only_flags("evidence row", row)
        if row.redacted_evidence_ref in seen_refs:
            raise ValueError("redacted_evidence_ref values must be unique")
        if row.last_seen_at > generated_at:
            raise ValueError("last_seen_at must not be in the future")
        seen_refs.add(row.redacted_evidence_ref)
    return tuple(
        sorted(
            normalized,
            key=lambda row: (row.team_id, row.redacted_packet_ref, row.redacted_evidence_ref),
        ),
    )


def _normalize_queue_rows(
    rows: object,
    *,
    generated_at: datetime,
) -> tuple[EvidenceQueueTraceabilityQueueRow, ...]:
    if type(rows) not in (list, tuple):
        raise ValueError("queue_rows must be a list or tuple")
    normalized = tuple(rows)
    seen_refs: set[str] = set()
    for row in normalized:
        if type(row) is not EvidenceQueueTraceabilityQueueRow:
            raise ValueError(
                "queue_rows must contain EvidenceQueueTraceabilityQueueRow values",
            )
        require_paper_only_flags("queue row", row)
        if row.redacted_queue_ref in seen_refs:
            raise ValueError("redacted_queue_ref values must be unique")
        if row.created_at > generated_at:
            raise ValueError("created_at must not be in the future")
        seen_refs.add(row.redacted_queue_ref)
    return tuple(sorted(normalized, key=lambda row: row.redacted_queue_ref))


def _queue_reference_counts(
    rows: tuple[EvidenceQueueTraceabilityQueueRow, ...],
) -> dict[tuple[str, str | None], int]:
    counts: dict[tuple[str, str | None], int] = {}
    for row in rows:
        key = (row.team_id, row.redacted_packet_ref)
        counts[key] = counts.get(key, 0) + 1
    return counts


def _normalize_queue_trace_rows(
    rows: tuple[EvidenceQueueTraceabilityQueueTraceRow, ...],
) -> tuple[EvidenceQueueTraceabilityQueueTraceRow, ...]:
    if type(rows) not in (list, tuple):
        raise ValueError("queue_trace_rows must be a list or tuple")
    normalized = tuple(rows)
    seen_refs: set[str] = set()
    for row in normalized:
        if type(row) is not EvidenceQueueTraceabilityQueueTraceRow:
            raise ValueError("queue_trace_rows must contain queue trace rows")
        require_paper_only_flags("queue trace row", row)
        if row.redacted_queue_ref in seen_refs:
            raise ValueError("queue_trace_rows redacted_queue_ref values must be unique")
        seen_refs.add(row.redacted_queue_ref)
    if normalized != tuple(
        sorted(
            normalized,
            key=lambda row: row.redacted_queue_ref,
        ),
    ):
        raise ValueError("queue_trace_rows must be sorted")
    return normalized


def _normalize_orphan_evidence_rows(
    rows: tuple[EvidenceQueueTraceabilityOrphanEvidenceRow, ...],
) -> tuple[EvidenceQueueTraceabilityOrphanEvidenceRow, ...]:
    if type(rows) not in (list, tuple):
        raise ValueError("orphan_evidence_rows must be a list or tuple")
    normalized = tuple(rows)
    seen_refs: set[str] = set()
    for row in normalized:
        if type(row) is not EvidenceQueueTraceabilityOrphanEvidenceRow:
            raise ValueError("orphan_evidence_rows must contain orphan evidence rows")
        require_paper_only_flags("orphan evidence row", row)
        if row.redacted_evidence_ref in seen_refs:
            raise ValueError(
                "orphan_evidence_rows redacted_evidence_ref values must be unique",
            )
        seen_refs.add(row.redacted_evidence_ref)
    if normalized != tuple(
        sorted(
            normalized,
            key=lambda row: (row.team_id, row.redacted_packet_ref, row.redacted_evidence_ref),
        ),
    ):
        raise ValueError("orphan_evidence_rows must be sorted")
    return normalized


def _validate_queue_trace_row(row: EvidenceQueueTraceabilityQueueTraceRow) -> None:
    expected_reason_codes = _queue_reason_codes(
        missing_trace_link_count=int(row.missing_trace_link_count),
        stale_evidence_link_count=int(row.stale_evidence_link_count),
        duplicate_queue_reference_count=int(row.duplicate_queue_reference_count),
        redacted_traceability_diagnostic_count=int(
            row.redacted_traceability_diagnostic_count,
        ),
    )
    if row.reason_codes != expected_reason_codes:
        raise ValueError("reason_codes must match trace counts")
    if row.trace_status != _traceability_status(row.reason_codes):
        raise ValueError("trace_status must match reason_codes")
    if (
        row.newest_evidence_link_age_seconds is not None
        and row.oldest_evidence_link_age_seconds is not None
        and row.newest_evidence_link_age_seconds > row.oldest_evidence_link_age_seconds
    ):
        raise ValueError("newest evidence link age must not exceed oldest evidence link age")


def _validate_report(report: EvidenceQueueTraceabilityAuditReport) -> None:
    if report.recommended_report_action != REPORT_ACTIONS[report.traceability_status]:
        raise ValueError("recommended_report_action must match traceability_status")
    if report.queue_row_count != _decimal_count(len(report.queue_trace_rows)):
        raise ValueError("queue_row_count must match queue_trace_rows")
    if report.orphan_evidence_count != _decimal_count(len(report.orphan_evidence_rows)):
        raise ValueError("orphan_evidence_count must match orphan_evidence_rows")
    if report.missing_trace_link_count != sum(
        (row.missing_trace_link_count for row in report.queue_trace_rows),
        ZERO,
    ):
        raise ValueError("missing_trace_link_count must match queue_trace_rows")
    if report.duplicate_queue_reference_count != sum(
        (row.duplicate_queue_reference_count for row in report.queue_trace_rows),
        ZERO,
    ):
        raise ValueError("duplicate_queue_reference_count must match queue_trace_rows")
    if report.stale_evidence_link_count != sum(
        (row.stale_evidence_link_count for row in report.queue_trace_rows),
        ZERO,
    ):
        raise ValueError("stale_evidence_link_count must match queue_trace_rows")
    if report.redacted_traceability_diagnostic_count != sum(
        (
            row.redacted_traceability_diagnostic_count
            for row in report.queue_trace_rows
        ),
        ZERO,
    ):
        raise ValueError("redacted_traceability_diagnostic_count must match queue_trace_rows")
    expected_reason_codes = _report_reason_codes(
        queue_row_count=int(report.queue_row_count),
        missing_trace_link_count=int(report.missing_trace_link_count),
        orphan_evidence_count=int(report.orphan_evidence_count),
        duplicate_queue_reference_count=int(report.duplicate_queue_reference_count),
        stale_evidence_link_count=int(report.stale_evidence_link_count),
        redacted_traceability_diagnostic_count=int(
            report.redacted_traceability_diagnostic_count,
        ),
    )
    if report.reason_codes != expected_reason_codes:
        raise ValueError("reason_codes must match report counts")
    if report.traceability_status != _traceability_status(report.reason_codes):
        raise ValueError("traceability_status must match reason_codes")


def _set_or_validate_derived_validation_digest(
    report: EvidenceQueueTraceabilityAuditReport,
) -> None:
    current = report.derived_validation_digest
    expected = _derived_validation_digest(report)
    if current == "":
        object.__setattr__(report, "derived_validation_digest", expected)
        return
    _require_sha256_digest("derived_validation_digest", current)
    if current != expected:
        raise ValueError("derived_validation_digest must match report fields")


def _validate_derived_validation_digest(
    report: EvidenceQueueTraceabilityAuditReport,
) -> None:
    current = _require_sha256_digest(
        "derived_validation_digest",
        report.derived_validation_digest,
    )
    if current != _derived_validation_digest(report):
        raise ValueError("derived_validation_digest must match report fields")


def _validate_public_payload(payload: dict[str, object]) -> None:
    _reject_unsafe_public_payload("public payload", payload)
    for field_name in ("paper_only", "report_only", "readonly"):
        if payload.get(field_name) is not True:
            raise ValueError(f"{field_name} must be True")
    digest_value = payload.get("derived_validation_digest")
    _require_sha256_digest("derived_validation_digest", digest_value)
    if digest_value != _derived_validation_digest(payload):
        raise ValueError("derived_validation_digest must match public payload")


def _derived_validation_digest(value: object) -> str:
    payload = _without_derived_validation_digest(_payload_value(value))
    encoded = json.dumps(
        payload,
        allow_nan=False,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _without_derived_validation_digest(value: object) -> object:
    if type(value) is dict:
        return {
            key: _without_derived_validation_digest(item)
            for key, item in value.items()
            if key != "derived_validation_digest"
        }
    if type(value) is list:
        return [_without_derived_validation_digest(item) for item in value]
    return value


def _payload_value(value: object) -> object:
    if type(value) is Decimal:
        if not value.is_finite():
            raise ValueError("Decimal payload values must be finite")
        return format(value, "f")
    if type(value) is datetime:
        return _as_utc("datetime", value).isoformat()
    if is_dataclass(value) and not isinstance(value, type):
        return {
            field.name: _payload_value(getattr(value, field.name))
            for field in fields(value)
        }
    if type(value) in (list, tuple):
        return [_payload_value(item) for item in value]
    if type(value) is dict:
        return {key: _payload_value(item) for key, item in value.items()}
    return value


def _reject_unsafe_public_payload(
    label: str,
    value: object,
    path: str = "",
) -> None:
    if value is None or type(value) is bool:
        return
    if type(value) is str:
        if _has_unsafe_public_fragment(value):
            raise ValueError(f"unsafe public payload value in {path or label}")
        return
    if isinstance(value, (Decimal, int, float)):
        raise ValueError(f"{path or label} must use Decimal strings, not numeric values")
    if type(value) is dict:
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("public payload keys must be strings")
            if _has_unsafe_public_fragment(key):
                raise ValueError(f"unsafe public payload key in {label}: {key}")
            item_path = key if not path else f"{path}.{key}"
            if key in ("paper_only", "report_only", "readonly") and item is not True:
                raise ValueError(f"{item_path} must be True")
            _reject_unsafe_public_payload(label, item, item_path)
        return
    if type(value) is list:
        for index, item in enumerate(value):
            item_path = f"{path}[{index}]" if path else f"{label}[{index}]"
            _reject_unsafe_public_payload(label, item, item_path)
        return
    raise ValueError(f"{path or label} is not public JSON serializable")


def _require_sha256_digest(name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{name} must be a string")
    if len(value) != 64 or any(character not in "0123456789abcdef" for character in value):
        raise ValueError(f"{name} must be a lowercase sha256 digest")
    return value


def _has_unsafe_public_fragment(value: str) -> bool:
    lowered = value.lower()
    return any(fragment in lowered for fragment in UNSAFE_PUBLIC_REF_FRAGMENTS)


def _normalize_public_refs(name: str, value: object) -> tuple[str, ...]:
    if type(value) not in (list, tuple):
        raise ValueError(f"{name} must contain public references")
    refs = tuple(value)
    for item in refs:
        try:
            _require_public_ref(name, item)
        except ValueError as exc:
            raise ValueError(f"{name} must contain public references") from exc
    if len(set(refs)) != len(refs):
        raise ValueError(f"{name} must be unique")
    return refs


def _normalize_reason_codes(name: str, value: object) -> tuple[str, ...]:
    if type(value) not in (list, tuple):
        raise ValueError(f"{name} must be a list or tuple")
    reason_codes = tuple(value)
    if not reason_codes:
        raise ValueError(f"{name} must contain at least one value")
    for reason_code in reason_codes:
        _require_canonical_string(name, reason_code)
        if reason_code not in REASON_CODES:
            raise ValueError(f"{name} must contain known reason codes")
    if len(set(reason_codes)) != len(reason_codes):
        raise ValueError(f"{name} must be unique")
    return reason_codes


def _normalize_positive_decimal(name: str, value: object) -> Decimal:
    decimal_value = _normalize_decimal(name, value)
    if decimal_value <= ZERO:
        raise ValueError(f"{name} must be positive")
    return decimal_value


def _normalize_nonnegative_decimal(name: str, value: object) -> Decimal:
    decimal_value = _normalize_decimal(name, value)
    if decimal_value < ZERO:
        raise ValueError(f"{name} must be nonnegative")
    return decimal_value


def _normalize_optional_nonnegative_decimal(name: str, value: object) -> Decimal | None:
    if value is None:
        return None
    return _normalize_nonnegative_decimal(name, value)


def _normalize_decimal(name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{name} must be finite")
    return value


def _decimal_count(value: int) -> Decimal:
    return Decimal(value)


def _as_utc(name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{name} must be a datetime")
    if value.tzinfo is None:
        raise ValueError(f"{name} must be timezone-aware")
    return value.astimezone(UTC)


def _age_seconds(later: datetime, earlier: datetime) -> Decimal:
    delta = later - earlier
    return Decimal(delta.days * 86400 + delta.seconds) + (
        Decimal(delta.microseconds) / MICROSECONDS_PER_SECOND
    )


def _require_public_ref(name: str, value: object) -> None:
    _require_canonical_string(name, value)
    lowered = value.lower()
    if any(fragment in lowered for fragment in UNSAFE_PUBLIC_REF_FRAGMENTS):
        raise ValueError(f"{name} contains unsafe public reference")


def _require_canonical_string(name: str, value: object) -> None:
    if type(value) is not str or not value or value.strip() != value:
        raise ValueError(f"{name} must be a canonical nonblank string")


def _require_queue_status(name: str, value: object) -> None:
    _require_canonical_string(name, value)
    if "report" not in value:
        raise ValueError(f"{name} must be report-only")


def _require_trace_status(name: str, value: object) -> None:
    if type(value) is not str or value not in TRACE_STATUSES:
        raise ValueError(f"{name} must be pass, watch, or blocked")
