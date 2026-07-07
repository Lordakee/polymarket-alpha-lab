"""Pure reducer for evidence traceability SLA summaries."""

from __future__ import annotations

from dataclasses import dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, localcontext
import hashlib
import json

from polymarket_alpha_lab.team_paper_guard import require_paper_only_flags


def _join_parts(*parts: str) -> str:
    return "".join(parts)


DEFAULT_EVIDENCE_TRACEABILITY_SLA_CONFIG_VERSION = (
    "evidence-traceability-sla-monitor-v0"
)

_DERIVED_VALIDATION_DIGEST_FIELD = "derived_validation_digest"
_PHASE_FLAG_FIELDS = ("paper_only", "report_only", "readonly")
_REPORT_PUBLIC_PAYLOAD_FIELDS_WITHOUT_DIGEST = (
    "generated_at",
    "config_version",
    "traceability_status",
    "total_source_count",
    "total_evidence_count",
    "total_traced_evidence_count",
    "total_missing_trace_count",
    "previous_missing_trace_count",
    "missing_trace_delta",
    "total_linked_reference_count",
    "total_orphan_evidence_count",
    "total_stale_link_count",
    "stale_link_sla_breach_count",
    "total_duplicate_reference_count",
    "total_redacted_payload_count",
    "missing_trace_share",
    "orphan_evidence_share",
    "duplicate_reference_share",
    "rows",
    "reason_codes",
    "paper_only",
    "report_only",
    "readonly",
)
_REPORT_PUBLIC_PAYLOAD_FIELDS = (
    *_REPORT_PUBLIC_PAYLOAD_FIELDS_WITHOUT_DIGEST,
    _DERIVED_VALIDATION_DIGEST_FIELD,
)
_ROW_PUBLIC_PAYLOAD_FIELDS = (
    "source_id",
    "evidence_count",
    "traced_evidence_count",
    "missing_trace_count",
    "previous_missing_trace_count",
    "missing_trace_delta",
    "linked_reference_count",
    "orphan_evidence_count",
    "stale_link_count",
    "stale_link_sla_breach_count",
    "duplicate_reference_count",
    "redacted_payload_count",
    "oldest_link_age_minutes",
    "missing_trace_share",
    "orphan_evidence_share",
    "duplicate_reference_share",
    "traceability_status",
    "reason_codes",
    "raw_payload_reference",
    "paper_only",
    "report_only",
    "readonly",
)
_DECIMAL_CONTEXT = Context(prec=64)
_QUANTUM = Decimal("0.000001")
_ZERO = Decimal("0.000000")
_ONE = Decimal("1.000000")
_DEFAULT_STALE_LINK_WATCH_MINUTES = Decimal("120.000000")
_DEFAULT_STALE_LINK_BREACH_MINUTES = Decimal("360.000000")
_DEFAULT_MAX_MISSING_TRACE_SHARE = Decimal("0.000000")
_DEFAULT_MAX_DUPLICATE_REFERENCE_SHARE = Decimal("0.100000")
_REDACTED_EVIDENCE_PAYLOAD = "<redacted-evidence-payload>"
_TRACEABILITY_STATUSES = ("pass", "watch", "blocked")
_STATUS_SEVERITY = {"blocked": 0, "watch": 1, "pass": 2}
_UNSAFE_PUBLIC_TEXT_FRAGMENTS = frozenset(
    (
        _join_parts("acc", "ount"),
        _join_parts("au", "th"),
        "balance",
        "cancel",
        "credential",
        _join_parts("or", "der"),
        "private",
        _join_parts("si", "gn"),
        "secret",
        "token",
        _join_parts("wal", "let"),
        _join_parts("mu", "tation"),
        _join_parts("b", "u", "y"),
        _join_parts("s", "e", "l", "l"),
    ),
)


@dataclass(frozen=True)
class EvidenceTraceabilitySlaConfig:
    config_version: str = DEFAULT_EVIDENCE_TRACEABILITY_SLA_CONFIG_VERSION
    stale_link_watch_minutes: Decimal = _DEFAULT_STALE_LINK_WATCH_MINUTES
    stale_link_breach_minutes: Decimal = _DEFAULT_STALE_LINK_BREACH_MINUTES
    max_missing_trace_share: Decimal = _DEFAULT_MAX_MISSING_TRACE_SHARE
    max_duplicate_reference_share: Decimal = _DEFAULT_MAX_DUPLICATE_REFERENCE_SHARE
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("config_version", self.config_version)
        object.__setattr__(
            self,
            "stale_link_watch_minutes",
            _normalize_nonnegative_decimal(
                "stale_link_watch_minutes",
                self.stale_link_watch_minutes,
            ),
        )
        object.__setattr__(
            self,
            "stale_link_breach_minutes",
            _normalize_nonnegative_decimal(
                "stale_link_breach_minutes",
                self.stale_link_breach_minutes,
            ),
        )
        if self.stale_link_breach_minutes < self.stale_link_watch_minutes:
            raise ValueError(
                "stale_link_breach_minutes must be >= stale_link_watch_minutes",
            )
        object.__setattr__(
            self,
            "max_missing_trace_share",
            _normalize_probability(
                "max_missing_trace_share",
                self.max_missing_trace_share,
            ),
        )
        object.__setattr__(
            self,
            "max_duplicate_reference_share",
            _normalize_probability(
                "max_duplicate_reference_share",
                self.max_duplicate_reference_share,
            ),
        )
        require_paper_only_flags("EvidenceTraceabilitySlaConfig", self)


@dataclass(frozen=True)
class EvidenceTraceabilityAuditSnapshot:
    source_id: str
    evidence_count: Decimal
    traced_evidence_count: Decimal
    linked_reference_count: Decimal
    stale_link_count: Decimal = _ZERO
    duplicate_reference_count: Decimal = _ZERO
    redacted_payload_count: Decimal = _ZERO
    oldest_link_age_minutes: Decimal = _ZERO
    previous_missing_trace_count: Decimal | None = None
    raw_payload_reference: str = _REDACTED_EVIDENCE_PAYLOAD
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("source_id", self.source_id)
        for field_name in (
            "evidence_count",
            "traced_evidence_count",
            "linked_reference_count",
            "stale_link_count",
            "duplicate_reference_count",
            "redacted_payload_count",
            "oldest_link_age_minutes",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        if self.previous_missing_trace_count is not None:
            object.__setattr__(
                self,
                "previous_missing_trace_count",
                _normalize_nonnegative_decimal(
                    "previous_missing_trace_count",
                    self.previous_missing_trace_count,
                ),
            )
        _validate_snapshot_counts(self)
        _require_canonical_string("raw_payload_reference", self.raw_payload_reference)
        object.__setattr__(self, "raw_payload_reference", _REDACTED_EVIDENCE_PAYLOAD)
        require_paper_only_flags("EvidenceTraceabilityAuditSnapshot", self)


@dataclass(frozen=True)
class EvidenceTraceabilitySlaRow:
    source_id: str
    evidence_count: Decimal
    traced_evidence_count: Decimal
    missing_trace_count: Decimal
    previous_missing_trace_count: Decimal | None
    missing_trace_delta: Decimal
    linked_reference_count: Decimal
    orphan_evidence_count: Decimal
    stale_link_count: Decimal
    stale_link_sla_breach_count: Decimal
    duplicate_reference_count: Decimal
    redacted_payload_count: Decimal
    oldest_link_age_minutes: Decimal
    missing_trace_share: Decimal
    orphan_evidence_share: Decimal
    duplicate_reference_share: Decimal
    traceability_status: str
    reason_codes: tuple[str, ...]
    raw_payload_reference: str = _REDACTED_EVIDENCE_PAYLOAD
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("source_id", self.source_id)
        for field_name in (
            "evidence_count",
            "traced_evidence_count",
            "missing_trace_count",
            "missing_trace_delta",
            "linked_reference_count",
            "orphan_evidence_count",
            "stale_link_count",
            "stale_link_sla_breach_count",
            "duplicate_reference_count",
            "redacted_payload_count",
            "oldest_link_age_minutes",
            "missing_trace_share",
            "orphan_evidence_share",
            "duplicate_reference_share",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        if self.previous_missing_trace_count is not None:
            object.__setattr__(
                self,
                "previous_missing_trace_count",
                _normalize_nonnegative_decimal(
                    "previous_missing_trace_count",
                    self.previous_missing_trace_count,
                ),
            )
        if self.raw_payload_reference != _REDACTED_EVIDENCE_PAYLOAD:
            raise ValueError("raw_payload_reference must be redacted")
        _require_status("traceability_status", self.traceability_status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes, allow_empty=False),
        )
        _validate_row_consistency(self)
        require_paper_only_flags("EvidenceTraceabilitySlaRow", self)


@dataclass(frozen=True)
class EvidenceTraceabilitySlaReport:
    generated_at: datetime
    config_version: str
    traceability_status: str
    total_source_count: Decimal
    total_evidence_count: Decimal
    total_traced_evidence_count: Decimal
    total_missing_trace_count: Decimal
    previous_missing_trace_count: Decimal
    missing_trace_delta: Decimal
    total_linked_reference_count: Decimal
    total_orphan_evidence_count: Decimal
    total_stale_link_count: Decimal
    stale_link_sla_breach_count: Decimal
    total_duplicate_reference_count: Decimal
    total_redacted_payload_count: Decimal
    missing_trace_share: Decimal
    orphan_evidence_share: Decimal
    duplicate_reference_share: Decimal
    rows: tuple[EvidenceTraceabilitySlaRow, ...]
    reason_codes: tuple[str, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        _require_status("traceability_status", self.traceability_status)
        for field_name in (
            "total_source_count",
            "total_evidence_count",
            "total_traced_evidence_count",
            "total_missing_trace_count",
            "previous_missing_trace_count",
            "missing_trace_delta",
            "total_linked_reference_count",
            "total_orphan_evidence_count",
            "total_stale_link_count",
            "stale_link_sla_breach_count",
            "total_duplicate_reference_count",
            "total_redacted_payload_count",
            "missing_trace_share",
            "orphan_evidence_share",
            "duplicate_reference_share",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes, allow_empty=False),
        )
        _validate_report_consistency(self)
        expected_digest = _report_derived_validation_digest(self)
        if not self.derived_validation_digest:
            object.__setattr__(
                self,
                "derived_validation_digest",
                expected_digest,
            )
        else:
            normalized_digest = _normalize_sha256(
                _DERIVED_VALIDATION_DIGEST_FIELD,
                self.derived_validation_digest,
            )
            object.__setattr__(
                self,
                "derived_validation_digest",
                normalized_digest,
            )
            if normalized_digest != expected_digest:
                raise ValueError("derived_validation_digest must match report payload")
        require_paper_only_flags("EvidenceTraceabilitySlaReport", self)


def build_evidence_traceability_sla_report(
    snapshots: tuple[EvidenceTraceabilityAuditSnapshot, ...]
    | list[EvidenceTraceabilityAuditSnapshot],
    *,
    config: EvidenceTraceabilitySlaConfig,
    generated_at: datetime,
) -> EvidenceTraceabilitySlaReport:
    if type(config) is not EvidenceTraceabilitySlaConfig:
        raise ValueError("config must be an EvidenceTraceabilitySlaConfig")
    require_paper_only_flags("EvidenceTraceabilitySlaConfig", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    normalized_snapshots = _normalize_snapshots(snapshots)
    rows = tuple(
        sorted(
            (
                _row_from_snapshot(snapshot, config=config)
                for snapshot in normalized_snapshots
            ),
            key=lambda row: (_STATUS_SEVERITY[row.traceability_status], row.source_id),
        ),
    )
    traceability_status = _report_status(rows)

    return EvidenceTraceabilitySlaReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        traceability_status=traceability_status,
        total_source_count=Decimal(len(rows)).quantize(_QUANTUM),
        total_evidence_count=_sum_decimal(row.evidence_count for row in rows),
        total_traced_evidence_count=_sum_decimal(
            row.traced_evidence_count for row in rows
        ),
        total_missing_trace_count=_sum_decimal(
            row.missing_trace_count for row in rows
        ),
        previous_missing_trace_count=_sum_decimal(
            row.previous_missing_trace_count
            for row in rows
            if row.previous_missing_trace_count is not None
        ),
        missing_trace_delta=_sum_decimal(row.missing_trace_delta for row in rows),
        total_linked_reference_count=_sum_decimal(
            row.linked_reference_count for row in rows
        ),
        total_orphan_evidence_count=_sum_decimal(
            row.orphan_evidence_count for row in rows
        ),
        total_stale_link_count=_sum_decimal(row.stale_link_count for row in rows),
        stale_link_sla_breach_count=_sum_decimal(
            row.stale_link_sla_breach_count for row in rows
        ),
        total_duplicate_reference_count=_sum_decimal(
            row.duplicate_reference_count for row in rows
        ),
        total_redacted_payload_count=_sum_decimal(
            row.redacted_payload_count for row in rows
        ),
        missing_trace_share=_ratio(
            _sum_decimal(row.missing_trace_count for row in rows),
            _sum_decimal(row.evidence_count for row in rows),
        ),
        orphan_evidence_share=_ratio(
            _sum_decimal(row.orphan_evidence_count for row in rows),
            _sum_decimal(row.evidence_count for row in rows),
        ),
        duplicate_reference_share=_ratio(
            _sum_decimal(row.duplicate_reference_count for row in rows),
            _sum_decimal(row.evidence_count for row in rows),
        ),
        rows=rows,
        reason_codes=_report_reason_codes(rows, traceability_status),
    )


def evidence_traceability_sla_report_payload(
    report: EvidenceTraceabilitySlaReport | dict[str, object],
) -> dict[str, object]:
    if type(report) is EvidenceTraceabilitySlaReport:
        require_paper_only_flags("EvidenceTraceabilitySlaReport", report)
        _validate_report_consistency(report)
        _validate_report_derived_validation_digest(report)
        _reject_unsafe_public_payload("EvidenceTraceabilitySlaReport", report)
        payload = _report_public_payload_values(report)
        payload[_DERIVED_VALIDATION_DIGEST_FIELD] = report.derived_validation_digest
        _reject_unsafe_public_payload(
            "EvidenceTraceabilitySlaReport.payload",
            payload,
            allow_json_containers=True,
        )
        return payload
    if type(report) is dict:
        _reject_unsafe_public_payload(
            "EvidenceTraceabilitySlaReport.payload",
            report,
            allow_json_containers=True,
        )
        _require_public_payload_fields(report)
        _validate_public_payload_derived_validation_digest(report)
        _report_from_public_payload(report)
        return dict(report)
    raise ValueError("report must be an EvidenceTraceabilitySlaReport")


def _row_from_snapshot(
    snapshot: EvidenceTraceabilityAuditSnapshot,
    *,
    config: EvidenceTraceabilitySlaConfig,
) -> EvidenceTraceabilitySlaRow:
    missing_trace_count = snapshot.evidence_count - snapshot.traced_evidence_count
    orphan_evidence_count = _positive_difference(
        snapshot.evidence_count,
        snapshot.linked_reference_count,
    )
    previous_missing_trace_count = snapshot.previous_missing_trace_count
    missing_trace_delta = (
        _ZERO
        if previous_missing_trace_count is None
        else _positive_difference(missing_trace_count, previous_missing_trace_count)
    )
    stale_link_sla_breach_count = (
        snapshot.stale_link_count
        if snapshot.stale_link_count > _ZERO
        and snapshot.oldest_link_age_minutes >= config.stale_link_breach_minutes
        else _ZERO
    )
    missing_trace_share = _ratio(missing_trace_count, snapshot.evidence_count)
    orphan_evidence_share = _ratio(orphan_evidence_count, snapshot.evidence_count)
    duplicate_reference_share = _ratio(
        snapshot.duplicate_reference_count,
        snapshot.linked_reference_count,
    )
    traceability_status, reason_codes = _row_status_and_reasons(
        snapshot,
        missing_trace_count=missing_trace_count,
        missing_trace_delta=missing_trace_delta,
        orphan_evidence_count=orphan_evidence_count,
        stale_link_sla_breach_count=stale_link_sla_breach_count,
        missing_trace_share=missing_trace_share,
        duplicate_reference_share=duplicate_reference_share,
        config=config,
    )

    return EvidenceTraceabilitySlaRow(
        source_id=snapshot.source_id,
        evidence_count=snapshot.evidence_count,
        traced_evidence_count=snapshot.traced_evidence_count,
        missing_trace_count=missing_trace_count,
        previous_missing_trace_count=previous_missing_trace_count,
        missing_trace_delta=missing_trace_delta,
        linked_reference_count=snapshot.linked_reference_count,
        orphan_evidence_count=orphan_evidence_count,
        stale_link_count=snapshot.stale_link_count,
        stale_link_sla_breach_count=stale_link_sla_breach_count,
        duplicate_reference_count=snapshot.duplicate_reference_count,
        redacted_payload_count=snapshot.redacted_payload_count,
        oldest_link_age_minutes=snapshot.oldest_link_age_minutes,
        missing_trace_share=missing_trace_share,
        orphan_evidence_share=orphan_evidence_share,
        duplicate_reference_share=duplicate_reference_share,
        traceability_status=traceability_status,
        reason_codes=reason_codes,
    )


def _row_status_and_reasons(
    snapshot: EvidenceTraceabilityAuditSnapshot,
    *,
    missing_trace_count: Decimal,
    missing_trace_delta: Decimal,
    orphan_evidence_count: Decimal,
    stale_link_sla_breach_count: Decimal,
    missing_trace_share: Decimal,
    duplicate_reference_share: Decimal,
    config: EvidenceTraceabilitySlaConfig,
) -> tuple[str, tuple[str, ...]]:
    blocked_reasons: list[str] = []
    if stale_link_sla_breach_count > _ZERO:
        blocked_reasons.append("stale_link_sla_breach_threshold_exceeded")
    if blocked_reasons:
        return "blocked", tuple(blocked_reasons)

    watch_reasons: list[str] = []
    if missing_trace_share > config.max_missing_trace_share and missing_trace_delta == _ZERO:
        watch_reasons.append("missing_trace_share_above_threshold")
    if missing_trace_delta > _ZERO:
        watch_reasons.append("missing_trace_trend_worsening")
    if orphan_evidence_count > _ZERO:
        watch_reasons.append("orphan_evidence_pressure_present")
    if (
        snapshot.stale_link_count > _ZERO
        and snapshot.oldest_link_age_minutes >= config.stale_link_watch_minutes
    ):
        watch_reasons.append("stale_link_watch_threshold_breached")
    if duplicate_reference_share > config.max_duplicate_reference_share:
        watch_reasons.append("duplicate_reference_pressure_present")
    elif snapshot.duplicate_reference_count > _ZERO:
        watch_reasons.append("duplicate_reference_pressure_present")
    if snapshot.redacted_payload_count > _ZERO:
        watch_reasons.append("redacted_payload_rows_present")
    if watch_reasons:
        return "watch", tuple(watch_reasons)
    return "pass", ("evidence_traceability_source_pass",)


def _report_status(rows: tuple[EvidenceTraceabilitySlaRow, ...]) -> str:
    if not rows or any(row.traceability_status == "blocked" for row in rows):
        return "blocked"
    if any(row.traceability_status == "watch" for row in rows):
        return "watch"
    return "pass"


def _report_reason_codes(
    rows: tuple[EvidenceTraceabilitySlaRow, ...],
    traceability_status: str,
) -> tuple[str, ...]:
    if not rows:
        return ("no_evidence_traceability_snapshots",)
    reason_codes: list[str] = []
    for row in rows:
        reason_codes.extend(row.reason_codes)
    if traceability_status == "blocked":
        reason_codes.append("evidence_traceability_sla_blocked")
    elif traceability_status == "watch":
        reason_codes.append("evidence_traceability_sla_watch")
    else:
        reason_codes.append("evidence_traceability_sla_pass")
    return _normalize_reason_codes(
        tuple(
            reason_code
            for reason_code in reason_codes
            if reason_code != "evidence_traceability_source_pass"
        ),
        allow_empty=False,
    )


def _normalize_snapshots(
    value: tuple[EvidenceTraceabilityAuditSnapshot, ...]
    | list[EvidenceTraceabilityAuditSnapshot],
) -> tuple[EvidenceTraceabilityAuditSnapshot, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError("snapshots must contain EvidenceTraceabilityAuditSnapshot values")
    try:
        snapshots = tuple(value)
    except TypeError as exc:
        raise ValueError(
            "snapshots must contain EvidenceTraceabilityAuditSnapshot values",
        ) from exc
    seen_source_ids: set[str] = set()
    for snapshot in snapshots:
        if type(snapshot) is not EvidenceTraceabilityAuditSnapshot:
            raise ValueError(
                "snapshots must contain EvidenceTraceabilityAuditSnapshot values",
            )
        require_paper_only_flags("EvidenceTraceabilityAuditSnapshot", snapshot)
        if snapshot.source_id in seen_source_ids:
            raise ValueError("snapshots must not contain duplicate source_id values")
        seen_source_ids.add(snapshot.source_id)
    return snapshots


def _normalize_rows(value: object) -> tuple[EvidenceTraceabilitySlaRow, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError("rows must contain EvidenceTraceabilitySlaRow values")
    try:
        rows = tuple(value)  # type: ignore[arg-type]
    except TypeError as exc:
        raise ValueError("rows must contain EvidenceTraceabilitySlaRow values") from exc
    for row in rows:
        if type(row) is not EvidenceTraceabilitySlaRow:
            raise ValueError("rows must contain EvidenceTraceabilitySlaRow values")
        require_paper_only_flags("EvidenceTraceabilitySlaRow", row)
    if rows != tuple(
        sorted(
            rows,
            key=lambda row: (_STATUS_SEVERITY[row.traceability_status], row.source_id),
        ),
    ):
        raise ValueError("rows must follow deterministic traceability sequence")
    return rows


def _validate_snapshot_counts(snapshot: EvidenceTraceabilityAuditSnapshot) -> None:
    if snapshot.traced_evidence_count > snapshot.evidence_count:
        raise ValueError("traced_evidence_count must not exceed evidence_count")
    if snapshot.stale_link_count > snapshot.linked_reference_count:
        raise ValueError("stale_link_count must not exceed linked_reference_count")
    if snapshot.duplicate_reference_count > snapshot.linked_reference_count:
        raise ValueError("duplicate_reference_count must not exceed linked_reference_count")
    if snapshot.redacted_payload_count > snapshot.evidence_count:
        raise ValueError("redacted_payload_count must not exceed evidence_count")


def _validate_row_consistency(row: EvidenceTraceabilitySlaRow) -> None:
    if row.traced_evidence_count > row.evidence_count:
        raise ValueError("traced_evidence_count must not exceed evidence_count")
    if row.stale_link_count > row.linked_reference_count:
        raise ValueError("stale_link_count must not exceed linked_reference_count")
    if row.stale_link_sla_breach_count > row.stale_link_count:
        raise ValueError("stale_link_sla_breach_count must not exceed stale_link_count")
    if row.duplicate_reference_count > row.linked_reference_count:
        raise ValueError("duplicate_reference_count must not exceed linked_reference_count")
    if row.redacted_payload_count > row.evidence_count:
        raise ValueError("redacted_payload_count must not exceed evidence_count")
    if row.missing_trace_count != row.evidence_count - row.traced_evidence_count:
        raise ValueError("missing_trace_count must match evidence gap")
    if row.previous_missing_trace_count is None:
        if row.missing_trace_delta != _ZERO:
            raise ValueError("missing_trace_delta must be zero without previous trace count")
    elif row.missing_trace_delta != _positive_difference(
        row.missing_trace_count,
        row.previous_missing_trace_count,
    ):
        raise ValueError("missing_trace_delta must match previous trace count")
    if row.orphan_evidence_count != _positive_difference(
        row.evidence_count,
        row.linked_reference_count,
    ):
        raise ValueError("orphan_evidence_count must match link gap")
    if row.missing_trace_share != _ratio(row.missing_trace_count, row.evidence_count):
        raise ValueError("missing_trace_share must match missing trace count")
    if row.orphan_evidence_share != _ratio(row.orphan_evidence_count, row.evidence_count):
        raise ValueError("orphan_evidence_share must match orphan evidence count")
    if row.duplicate_reference_share != _ratio(
        row.duplicate_reference_count,
        row.linked_reference_count,
    ):
        raise ValueError("duplicate_reference_share must match duplicate references")
    if row.traceability_status == "pass" and row.reason_codes != (
        "evidence_traceability_source_pass",
    ):
        raise ValueError("pass rows must use pass reason code")


def _validate_report_consistency(report: EvidenceTraceabilitySlaReport) -> None:
    if report.total_source_count != Decimal(len(report.rows)).quantize(_QUANTUM):
        raise ValueError("total_source_count must match rows")
    if report.total_evidence_count != _sum_decimal(row.evidence_count for row in report.rows):
        raise ValueError("total_evidence_count must match rows")
    if report.total_traced_evidence_count != _sum_decimal(
        row.traced_evidence_count for row in report.rows
    ):
        raise ValueError("total_traced_evidence_count must match rows")
    if report.total_missing_trace_count != _sum_decimal(
        row.missing_trace_count for row in report.rows
    ):
        raise ValueError("total_missing_trace_count must match rows")
    if report.previous_missing_trace_count != _sum_decimal(
        row.previous_missing_trace_count
        for row in report.rows
        if row.previous_missing_trace_count is not None
    ):
        raise ValueError("previous_missing_trace_count must match rows")
    if report.missing_trace_delta != _sum_decimal(
        row.missing_trace_delta for row in report.rows
    ):
        raise ValueError("missing_trace_delta must match rows")
    if report.total_linked_reference_count != _sum_decimal(
        row.linked_reference_count for row in report.rows
    ):
        raise ValueError("total_linked_reference_count must match rows")
    if report.total_orphan_evidence_count != _sum_decimal(
        row.orphan_evidence_count for row in report.rows
    ):
        raise ValueError("total_orphan_evidence_count must match rows")
    if report.total_stale_link_count != _sum_decimal(
        row.stale_link_count for row in report.rows
    ):
        raise ValueError("total_stale_link_count must match rows")
    if report.stale_link_sla_breach_count != _sum_decimal(
        row.stale_link_sla_breach_count for row in report.rows
    ):
        raise ValueError("stale_link_sla_breach_count must match rows")
    if report.total_duplicate_reference_count != _sum_decimal(
        row.duplicate_reference_count for row in report.rows
    ):
        raise ValueError("total_duplicate_reference_count must match rows")
    if report.total_redacted_payload_count != _sum_decimal(
        row.redacted_payload_count for row in report.rows
    ):
        raise ValueError("total_redacted_payload_count must match rows")
    if report.missing_trace_share != _ratio(
        report.total_missing_trace_count,
        report.total_evidence_count,
    ):
        raise ValueError("missing_trace_share must match totals")
    if report.orphan_evidence_share != _ratio(
        report.total_orphan_evidence_count,
        report.total_evidence_count,
    ):
        raise ValueError("orphan_evidence_share must match totals")
    if report.duplicate_reference_share != _ratio(
        report.total_duplicate_reference_count,
        report.total_evidence_count,
    ):
        raise ValueError("duplicate_reference_share must match totals")
    if report.traceability_status != _report_status(report.rows):
        raise ValueError("traceability_status must match rows")
    if report.reason_codes != _report_reason_codes(
        report.rows,
        report.traceability_status,
    ):
        raise ValueError("reason_codes must match rows")


def _report_public_payload_values(
    report: EvidenceTraceabilitySlaReport,
) -> dict[str, object]:
    payload = _json_ready(report)
    if type(payload) is not dict:
        raise ValueError("report must convert to a JSON object")
    payload.pop(_DERIVED_VALIDATION_DIGEST_FIELD, None)
    return payload


def _report_derived_validation_digest(report: EvidenceTraceabilitySlaReport) -> str:
    return _derived_validation_digest(_report_public_payload_values(report))


def _validate_report_derived_validation_digest(
    report: EvidenceTraceabilitySlaReport,
) -> None:
    if report.derived_validation_digest != _report_derived_validation_digest(report):
        raise ValueError("derived_validation_digest must match report payload")


def _validate_public_payload_derived_validation_digest(
    payload: dict[str, object],
) -> None:
    digest = _normalize_sha256(
        _DERIVED_VALIDATION_DIGEST_FIELD,
        payload[_DERIVED_VALIDATION_DIGEST_FIELD],
    )
    if digest != _derived_validation_digest(dict(payload)):
        raise ValueError("derived_validation_digest must match public payload")


def _derived_validation_digest(payload: dict[str, object]) -> str:
    payload_without_digest = dict(payload)
    payload_without_digest.pop(_DERIVED_VALIDATION_DIGEST_FIELD, None)
    digest_payload = json.dumps(
        payload_without_digest,
        allow_nan=False,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    )
    return hashlib.sha256(
        ("evidence_traceability_sla_monitor|" + digest_payload).encode("utf-8"),
    ).hexdigest()


def _json_ready(value: object) -> object:
    if is_dataclass(value) and not isinstance(value, type):
        return {field.name: _json_ready(getattr(value, field.name)) for field in fields(value)}
    if isinstance(value, Decimal):
        if type(value) is not Decimal:
            raise ValueError("JSON Decimal value must be exactly Decimal")
        if not value.is_finite():
            raise ValueError("JSON Decimal value must be finite")
        return str(value)
    if isinstance(value, datetime):
        if type(value) is not datetime:
            raise ValueError("JSON datetime value must be exactly datetime")
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("JSON datetime value must be timezone-aware")
        return value.astimezone(UTC).isoformat()
    if type(value) is tuple:
        return [_json_ready(item) for item in value]
    if type(value) is list:
        return [_json_ready(item) for item in value]
    if type(value) is dict:
        ready: dict[str, object] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            ready[key] = _json_ready(item)
        return ready
    if value is None or type(value) in (str, bool):
        return value
    if isinstance(value, float):
        raise ValueError("JSON value must not be a float")
    if type(value) is int:
        raise ValueError("JSON numeric value must use Decimal strings")
    raise ValueError("value is not JSON-ready")


def _require_public_payload_fields(payload: dict[str, object]) -> None:
    for field_name in _REPORT_PUBLIC_PAYLOAD_FIELDS:
        if field_name not in payload:
            raise ValueError(f"{field_name} is required")
    extra_fields = sorted(set(payload) - set(_REPORT_PUBLIC_PAYLOAD_FIELDS))
    if extra_fields:
        raise ValueError(f"unexpected public payload field: {extra_fields[0]}")


def _report_from_public_payload(
    payload: dict[str, object],
) -> EvidenceTraceabilitySlaReport:
    _require_public_payload_fields(payload)
    return EvidenceTraceabilitySlaReport(
        generated_at=_datetime_from_public_payload("generated_at", payload["generated_at"]),
        config_version=_public_string_from_payload("config_version", payload["config_version"]),
        traceability_status=_public_status_from_payload(
            "traceability_status",
            payload["traceability_status"],
        ),
        total_source_count=_decimal_from_public_payload(
            "total_source_count",
            payload["total_source_count"],
        ),
        total_evidence_count=_decimal_from_public_payload(
            "total_evidence_count",
            payload["total_evidence_count"],
        ),
        total_traced_evidence_count=_decimal_from_public_payload(
            "total_traced_evidence_count",
            payload["total_traced_evidence_count"],
        ),
        total_missing_trace_count=_decimal_from_public_payload(
            "total_missing_trace_count",
            payload["total_missing_trace_count"],
        ),
        previous_missing_trace_count=_decimal_from_public_payload(
            "previous_missing_trace_count",
            payload["previous_missing_trace_count"],
        ),
        missing_trace_delta=_decimal_from_public_payload(
            "missing_trace_delta",
            payload["missing_trace_delta"],
        ),
        total_linked_reference_count=_decimal_from_public_payload(
            "total_linked_reference_count",
            payload["total_linked_reference_count"],
        ),
        total_orphan_evidence_count=_decimal_from_public_payload(
            "total_orphan_evidence_count",
            payload["total_orphan_evidence_count"],
        ),
        total_stale_link_count=_decimal_from_public_payload(
            "total_stale_link_count",
            payload["total_stale_link_count"],
        ),
        stale_link_sla_breach_count=_decimal_from_public_payload(
            "stale_link_sla_breach_count",
            payload["stale_link_sla_breach_count"],
        ),
        total_duplicate_reference_count=_decimal_from_public_payload(
            "total_duplicate_reference_count",
            payload["total_duplicate_reference_count"],
        ),
        total_redacted_payload_count=_decimal_from_public_payload(
            "total_redacted_payload_count",
            payload["total_redacted_payload_count"],
        ),
        missing_trace_share=_decimal_from_public_payload(
            "missing_trace_share",
            payload["missing_trace_share"],
        ),
        orphan_evidence_share=_decimal_from_public_payload(
            "orphan_evidence_share",
            payload["orphan_evidence_share"],
        ),
        duplicate_reference_share=_decimal_from_public_payload(
            "duplicate_reference_share",
            payload["duplicate_reference_share"],
        ),
        rows=_rows_from_public_payload(payload["rows"]),
        reason_codes=_reason_codes_from_public_payload("reason_codes", payload["reason_codes"]),
        derived_validation_digest=_normalize_sha256(
            _DERIVED_VALIDATION_DIGEST_FIELD,
            payload[_DERIVED_VALIDATION_DIGEST_FIELD],
        ),
        paper_only=_bool_from_public_payload("paper_only", payload["paper_only"]),
        report_only=_bool_from_public_payload("report_only", payload["report_only"]),
        readonly=_bool_from_public_payload("readonly", payload["readonly"]),
    )


def _rows_from_public_payload(value: object) -> tuple[EvidenceTraceabilitySlaRow, ...]:
    row_payloads = _payload_dicts("rows", value)
    return tuple(_row_from_public_payload(row_payload) for row_payload in row_payloads)


def _row_from_public_payload(payload: dict[str, object]) -> EvidenceTraceabilitySlaRow:
    _require_nested_public_payload_fields("rows", payload, _ROW_PUBLIC_PAYLOAD_FIELDS)
    return EvidenceTraceabilitySlaRow(
        source_id=_public_string_from_payload("source_id", payload["source_id"]),
        evidence_count=_decimal_from_public_payload("evidence_count", payload["evidence_count"]),
        traced_evidence_count=_decimal_from_public_payload(
            "traced_evidence_count",
            payload["traced_evidence_count"],
        ),
        missing_trace_count=_decimal_from_public_payload(
            "missing_trace_count",
            payload["missing_trace_count"],
        ),
        previous_missing_trace_count=_optional_decimal_from_public_payload(
            "previous_missing_trace_count",
            payload["previous_missing_trace_count"],
        ),
        missing_trace_delta=_decimal_from_public_payload(
            "missing_trace_delta",
            payload["missing_trace_delta"],
        ),
        linked_reference_count=_decimal_from_public_payload(
            "linked_reference_count",
            payload["linked_reference_count"],
        ),
        orphan_evidence_count=_decimal_from_public_payload(
            "orphan_evidence_count",
            payload["orphan_evidence_count"],
        ),
        stale_link_count=_decimal_from_public_payload("stale_link_count", payload["stale_link_count"]),
        stale_link_sla_breach_count=_decimal_from_public_payload(
            "stale_link_sla_breach_count",
            payload["stale_link_sla_breach_count"],
        ),
        duplicate_reference_count=_decimal_from_public_payload(
            "duplicate_reference_count",
            payload["duplicate_reference_count"],
        ),
        redacted_payload_count=_decimal_from_public_payload(
            "redacted_payload_count",
            payload["redacted_payload_count"],
        ),
        oldest_link_age_minutes=_decimal_from_public_payload(
            "oldest_link_age_minutes",
            payload["oldest_link_age_minutes"],
        ),
        missing_trace_share=_decimal_from_public_payload(
            "missing_trace_share",
            payload["missing_trace_share"],
        ),
        orphan_evidence_share=_decimal_from_public_payload(
            "orphan_evidence_share",
            payload["orphan_evidence_share"],
        ),
        duplicate_reference_share=_decimal_from_public_payload(
            "duplicate_reference_share",
            payload["duplicate_reference_share"],
        ),
        traceability_status=_public_status_from_payload(
            "traceability_status",
            payload["traceability_status"],
        ),
        reason_codes=_reason_codes_from_public_payload("reason_codes", payload["reason_codes"]),
        raw_payload_reference=_public_string_from_payload(
            "raw_payload_reference",
            payload["raw_payload_reference"],
        ),
        paper_only=_bool_from_public_payload("paper_only", payload["paper_only"]),
        report_only=_bool_from_public_payload("report_only", payload["report_only"]),
        readonly=_bool_from_public_payload("readonly", payload["readonly"]),
    )


def _payload_dicts(field_name: str, value: object) -> tuple[dict[str, object], ...]:
    if type(value) is not list:
        raise ValueError(f"{field_name} must be a list")
    rows: list[dict[str, object]] = []
    for item in value:
        if type(item) is not dict:
            raise ValueError(f"{field_name} must contain JSON objects")
        rows.append(item)
    return tuple(rows)


def _require_nested_public_payload_fields(
    field_name: str,
    payload: dict[str, object],
    allowed_fields: tuple[str, ...],
) -> None:
    for key in allowed_fields:
        if key not in payload:
            raise ValueError(f"{field_name}.{key} is required")
    extra_fields = sorted(set(payload) - set(allowed_fields))
    if extra_fields:
        raise ValueError(f"unexpected public payload field: {field_name}.{extra_fields[0]}")


def _datetime_from_public_payload(field_name: str, value: object) -> datetime:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a datetime string")
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError as exc:
        raise ValueError(f"{field_name} must be a datetime string") from exc
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    parsed_utc = parsed.astimezone(UTC)
    if parsed_utc.isoformat() != value:
        raise ValueError(f"{field_name} must be a canonical UTC datetime string")
    return parsed_utc


def _decimal_from_public_payload(field_name: str, value: object) -> Decimal:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a Decimal-derived string")
    try:
        decimal_value = Decimal(value)
    except Exception as exc:
        raise ValueError(f"{field_name} must be a Decimal-derived string") from exc
    if not decimal_value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    normalized = _normalize_nonnegative_decimal(field_name, decimal_value)
    if format(normalized, "f") != value:
        raise ValueError(f"{field_name} must be a canonical Decimal-derived string")
    return normalized


def _optional_decimal_from_public_payload(
    field_name: str,
    value: object,
) -> Decimal | None:
    if value is None:
        return None
    return _decimal_from_public_payload(field_name, value)


def _reason_codes_from_public_payload(
    field_name: str,
    value: object,
) -> tuple[str, ...]:
    if type(value) is not list:
        raise ValueError(f"{field_name} must be a list")
    return _normalize_reason_codes(tuple(value), allow_empty=False)


def _public_status_from_payload(field_name: str, value: object) -> str:
    _require_status(field_name, value)
    return value


def _public_string_from_payload(field_name: str, value: object) -> str:
    _require_canonical_string(field_name, value)
    if _contains_unsafe_public_text(value):
        raise ValueError(f"{field_name} has unsafe value")
    return value


def _bool_from_public_payload(field_name: str, value: object) -> bool:
    if type(value) is not bool:
        raise ValueError(f"{field_name} must be a bool")
    return value


def _reject_unsafe_public_payload(
    label: str,
    value: object,
    path: str = "",
    *,
    allow_json_containers: bool = False,
) -> None:
    current_path = path or label
    if is_dataclass(value) and not isinstance(value, type):
        if type(value) not in (
            EvidenceTraceabilitySlaConfig,
            EvidenceTraceabilityAuditSnapshot,
            EvidenceTraceabilitySlaRow,
            EvidenceTraceabilitySlaReport,
        ):
            raise ValueError(f"{current_path} must be a supported public dataclass")
        for field in fields(value):
            item_path = field.name if not path else f"{path}.{field.name}"
            _reject_unsafe_public_payload(
                label,
                getattr(value, field.name),
                item_path,
                allow_json_containers=allow_json_containers,
            )
        return
    if isinstance(value, Decimal):
        if type(value) is not Decimal:
            raise ValueError(f"{current_path} must be a Decimal")
        if not value.is_finite():
            raise ValueError(f"{current_path} must be finite")
        if not value.same_quantum(_QUANTUM):
            raise ValueError(f"{current_path} must be quantized to six decimals")
        return
    if isinstance(value, datetime):
        if type(value) is not datetime:
            raise ValueError(f"{current_path} must be exactly datetime")
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError(f"{current_path} must be timezone-aware")
        return
    if value is None or type(value) is bool:
        return
    if type(value) is int:
        raise ValueError(f"{current_path} must use Decimal-derived string values")
    if isinstance(value, float):
        raise ValueError(f"{current_path} must not be a float")
    if type(value) is str:
        if value.strip() != value:
            raise ValueError(f"{current_path} has unsafe value")
        if "://" in value or "?" in value or _contains_unsafe_public_text(value):
            raise ValueError(f"{current_path} has unsafe value")
        return
    if type(value) is dict:
        if not allow_json_containers:
            raise ValueError(f"{current_path} must remain constructor-normalized")
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            item_path = key if not path else f"{path}.{key}"
            if _contains_unsafe_public_text(key):
                raise ValueError(f"{item_path} has unsafe field")
            if key in _PHASE_FLAG_FIELDS and item is not True:
                raise ValueError(f"{item_path} must be True for {label}")
            _reject_unsafe_public_payload(
                label,
                item,
                item_path,
                allow_json_containers=True,
            )
        return
    if type(value) is list:
        if not allow_json_containers:
            raise ValueError(f"{current_path} must remain constructor-normalized")
        for index, item in enumerate(value):
            item_path = f"{path}[{index}]" if path else f"{label}[{index}]"
            _reject_unsafe_public_payload(
                label,
                item,
                item_path,
                allow_json_containers=True,
            )
        return
    if type(value) is tuple:
        for index, item in enumerate(value):
            item_path = f"{path}[{index}]" if path else f"{label}[{index}]"
            _reject_unsafe_public_payload(
                label,
                item,
                item_path,
                allow_json_containers=allow_json_containers,
            )
        return
    raise ValueError(f"{current_path} is not JSON serializable")


def _contains_unsafe_public_text(value: str) -> bool:
    lowered = value.lower()
    return any(fragment in lowered for fragment in _UNSAFE_PUBLIC_TEXT_FRAGMENTS)


def _sum_decimal(values: object) -> Decimal:
    total = _ZERO
    for value in values:  # type: ignore[operator]
        total += value
    return total.quantize(_QUANTUM)


def _positive_difference(left: Decimal, right: Decimal) -> Decimal:
    difference = left - right
    if difference <= _ZERO:
        return _ZERO
    return difference.quantize(_QUANTUM)


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == _ZERO:
        return _ZERO
    with localcontext(_DECIMAL_CONTEXT):
        return (numerator / denominator).quantize(_QUANTUM)


def _normalize_probability(field_name: str, value: object) -> Decimal:
    normalized = _normalize_nonnegative_decimal(field_name, value)
    if normalized > _ONE:
        raise ValueError(f"{field_name} must be <= 1.000000")
    return normalized


def _normalize_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    with localcontext(_DECIMAL_CONTEXT):
        normalized = value.quantize(_QUANTUM)
    if normalized < _ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _normalize_reason_codes(
    value: object,
    *,
    allow_empty: bool,
) -> tuple[str, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError("reason_codes must contain canonical strings")
    try:
        items = tuple(value)  # type: ignore[arg-type]
    except TypeError as exc:
        raise ValueError("reason_codes must contain canonical strings") from exc
    if not items and not allow_empty:
        raise ValueError("reason_codes must not be empty")
    for item in items:
        _require_canonical_string("reason_codes", item)
    return tuple(dict.fromkeys(items))


def _require_status(field_name: str, value: object) -> None:
    if value not in _TRACEABILITY_STATUSES:
        raise ValueError(f"{field_name} must be one of {_TRACEABILITY_STATUSES}")


def _normalize_sha256(field_name: str, value: object) -> str:
    _require_canonical_string(field_name, value)
    if len(value) != 64 or any(character not in "0123456789abcdef" for character in value):
        raise ValueError(f"{field_name} must be a sha256 hex digest")
    return value


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str or not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


__all__ = (
    "DEFAULT_EVIDENCE_TRACEABILITY_SLA_CONFIG_VERSION",
    "EvidenceTraceabilityAuditSnapshot",
    "EvidenceTraceabilitySlaConfig",
    "EvidenceTraceabilitySlaReport",
    "EvidenceTraceabilitySlaRow",
    "build_evidence_traceability_sla_report",
    "evidence_traceability_sla_report_payload",
)
