"""Report-only specialist team evidence provenance integrity report."""

from __future__ import annotations

from dataclasses import asdict, dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal, ROUND_HALF_UP
import hashlib
import json
import re
from typing import Any, Mapping, Sequence


DEFAULT_SPECIALIST_TEAM_EVIDENCE_PROVENANCE_INTEGRITY_REPORT_VERSION = (
    "specialist-team-evidence-provenance-integrity-report-v1"
)

_QUANT = Decimal("0.000001")
_ZERO = Decimal("0.000000")
_PUBLIC_IDENTIFIER_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,127}$")
_DIGEST_RE = re.compile(r"^[0-9a-f]{64}$")
_STATUSES = frozenset(("pass", "watch", "block"))
_MISSING_LABELS = frozenset(("", "missing", "none", "unknown"))
_REASON_CODE_SEQUENCE = (
    "missing_evidence_source_id",
    "missing_source_family_id",
    "missing_captured_at",
    "missing_content_hash",
    "missing_analyst_note",
    "missing_team_id",
    "missing_official_anchor",
    "provenance_integrity_pass",
)
_BLOCK_REASON_CODES = frozenset(
    (
        "missing_evidence_source_id",
        "missing_source_family_id",
        "missing_captured_at",
        "missing_team_id",
        "missing_official_anchor",
    ),
)
_WATCH_REASON_CODES = frozenset(("missing_content_hash", "missing_analyst_note"))
_UNSAFE_PUBLIC_TERMS = (
    "live",
    "auth",
    "wallet",
    "order",
    "network",
    "database",
    "persist",
    "signing",
    "trade",
    "trading",
    "buy",
    "sell",
    "recommend",
    "recommendation",
)


@dataclass(frozen=True)
class SpecialistTeamEvidenceProvenanceIntegrityEvidence:
    evidence_source_id: str | None
    source_family_id: str | None
    official_anchor_flag: bool
    captured_at: datetime | None
    content_hash_present: bool
    analyst_note_present: bool
    team_id: str | None
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not SpecialistTeamEvidenceProvenanceIntegrityEvidence:
            raise TypeError(
                "SpecialistTeamEvidenceProvenanceIntegrityEvidence does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not SpecialistTeamEvidenceProvenanceIntegrityEvidence:
            raise ValueError(
                "evidence must be exactly SpecialistTeamEvidenceProvenanceIntegrityEvidence",
            )
        object.__setattr__(
            self,
            "evidence_source_id",
            _normalize_optional_public_identifier(
                "evidence_source_id",
                self.evidence_source_id,
                missing_sentinel=False,
            ),
        )
        object.__setattr__(
            self,
            "source_family_id",
            _normalize_optional_public_identifier(
                "source_family_id",
                self.source_family_id,
                missing_sentinel=True,
            ),
        )
        object.__setattr__(
            self,
            "team_id",
            _normalize_optional_public_identifier(
                "team_id",
                self.team_id,
                missing_sentinel=True,
            ),
        )
        _require_bool("official_anchor_flag", self.official_anchor_flag)
        _require_bool("content_hash_present", self.content_hash_present)
        _require_bool("analyst_note_present", self.analyst_note_present)
        if self.captured_at is not None:
            object.__setattr__(self, "captured_at", _as_utc("captured_at", self.captured_at))
        _require_hard_flags("evidence", self)
        _reject_unsafe_public_payload("evidence", self)


@dataclass(frozen=True)
class SpecialistTeamEvidenceProvenanceIntegrityPublicPayloadItem:
    key: str
    value: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not SpecialistTeamEvidenceProvenanceIntegrityPublicPayloadItem:
            raise TypeError(
                "SpecialistTeamEvidenceProvenanceIntegrityPublicPayloadItem "
                "does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not SpecialistTeamEvidenceProvenanceIntegrityPublicPayloadItem:
            raise ValueError(
                "public payload item must be exactly "
                "SpecialistTeamEvidenceProvenanceIntegrityPublicPayloadItem",
            )
        _require_public_identifier("key", self.key)
        object.__setattr__(self, "value", _require_public_text("value", self.value))
        _require_hard_flags("public payload item", self)
        _reject_unsafe_public_payload("public payload item", self)


@dataclass(frozen=True)
class SpecialistTeamEvidenceProvenanceIntegrityRow:
    evidence_source_id: str | None
    source_family_id: str | None
    official_anchor_flag: bool
    captured_at: datetime | None
    content_hash_present: bool
    analyst_note_present: bool
    team_id: str | None
    provenance_status: str
    reason_codes: tuple[str, ...]
    manual_next_step: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not SpecialistTeamEvidenceProvenanceIntegrityRow:
            raise TypeError(
                "SpecialistTeamEvidenceProvenanceIntegrityRow does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not SpecialistTeamEvidenceProvenanceIntegrityRow:
            raise ValueError("row must be exactly SpecialistTeamEvidenceProvenanceIntegrityRow")
        object.__setattr__(
            self,
            "evidence_source_id",
            _normalize_optional_public_identifier(
                "evidence_source_id",
                self.evidence_source_id,
                missing_sentinel=False,
            ),
        )
        object.__setattr__(
            self,
            "source_family_id",
            _normalize_optional_public_identifier(
                "source_family_id",
                self.source_family_id,
                missing_sentinel=True,
            ),
        )
        object.__setattr__(
            self,
            "team_id",
            _normalize_optional_public_identifier(
                "team_id",
                self.team_id,
                missing_sentinel=True,
            ),
        )
        _require_bool("official_anchor_flag", self.official_anchor_flag)
        _require_bool("content_hash_present", self.content_hash_present)
        _require_bool("analyst_note_present", self.analyst_note_present)
        if self.captured_at is not None:
            object.__setattr__(self, "captured_at", _as_utc("captured_at", self.captured_at))
        _require_status("provenance_status", self.provenance_status)
        object.__setattr__(self, "reason_codes", _normalize_reason_codes(self.reason_codes))
        object.__setattr__(
            self,
            "manual_next_step",
            _require_manual_next_step("manual_next_step", self.manual_next_step),
        )
        _validate_row(self)
        _require_hard_flags("row", self)
        _reject_unsafe_public_payload("row", self)


@dataclass(frozen=True)
class SpecialistTeamEvidenceProvenanceIntegrityReport:
    generated_at: datetime
    config_version: str
    provenance_status: str
    evidence_source_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    team_count: Decimal
    rows: tuple[SpecialistTeamEvidenceProvenanceIntegrityRow, ...]
    reason_codes: tuple[str, ...]
    manual_next_step: str
    public_payload: tuple[SpecialistTeamEvidenceProvenanceIntegrityPublicPayloadItem, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not SpecialistTeamEvidenceProvenanceIntegrityReport:
            raise TypeError(
                "SpecialistTeamEvidenceProvenanceIntegrityReport does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not SpecialistTeamEvidenceProvenanceIntegrityReport:
            raise ValueError("report must be exactly SpecialistTeamEvidenceProvenanceIntegrityReport")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_identifier("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_SPECIALIST_TEAM_EVIDENCE_PROVENANCE_INTEGRITY_REPORT_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        _require_status("provenance_status", self.provenance_status)
        for field_name in (
            "evidence_source_count",
            "pass_count",
            "watch_count",
            "block_count",
            "team_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_count_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        object.__setattr__(self, "reason_codes", _normalize_reason_codes(self.reason_codes))
        object.__setattr__(
            self,
            "manual_next_step",
            _require_manual_next_step("manual_next_step", self.manual_next_step),
        )
        object.__setattr__(
            self,
            "public_payload",
            _normalize_public_payload(self.public_payload),
        )
        _validate_report(self)
        _require_hard_flags("report", self)
        _reject_unsafe_public_payload("report", self)
        if self.derived_validation_digest:
            _require_sha256_digest("derived_validation_digest", self.derived_validation_digest)
            if self.derived_validation_digest != _report_digest_from_values(
                _report_values_without_digest(self),
            ):
                raise ValueError("derived_validation_digest does not match report payload")
        else:
            object.__setattr__(
                self,
                "derived_validation_digest",
                _report_digest_from_values(_report_values_without_digest(self)),
            )

    @property
    def payload(self) -> dict[str, object]:
        payload = _json_ready(asdict(self))
        _reject_unsafe_public_payload(
            "SpecialistTeamEvidenceProvenanceIntegrityReport.payload",
            payload,
            allow_json_containers=True,
        )
        if type(payload) is not dict:
            raise ValueError("payload must be a dict")
        return payload


def build_specialist_team_evidence_provenance_integrity_report(
    evidence: Sequence[SpecialistTeamEvidenceProvenanceIntegrityEvidence],
    *,
    generated_at: datetime,
    public_payload: Sequence[SpecialistTeamEvidenceProvenanceIntegrityPublicPayloadItem] = (),
) -> SpecialistTeamEvidenceProvenanceIntegrityReport:
    """Build a deterministic local report-only provenance integrity snapshot."""

    generated_at = _as_utc("generated_at", generated_at)
    normalized_evidence = _normalize_evidence(evidence)
    for item in normalized_evidence:
        if item.captured_at is not None and item.captured_at > generated_at:
            raise ValueError("evidence captured_at must not be after generated_at")
    rows = _build_rows(normalized_evidence)
    reason_codes = _report_reason_codes(rows)
    values: dict[str, object] = {
        "generated_at": generated_at,
        "config_version": DEFAULT_SPECIALIST_TEAM_EVIDENCE_PROVENANCE_INTEGRITY_REPORT_VERSION,
        "provenance_status": _report_status(rows),
        "evidence_source_count": _decimal_count(len(rows)),
        "pass_count": _decimal_count(_status_count(rows, "pass")),
        "watch_count": _decimal_count(_status_count(rows, "watch")),
        "block_count": _decimal_count(_status_count(rows, "block")),
        "team_count": _decimal_count(
            len({row.team_id for row in rows if not _is_missing_public_identifier(row.team_id)}),
        ),
        "rows": rows,
        "reason_codes": reason_codes,
        "manual_next_step": _report_manual_next_step(rows),
        "public_payload": _normalize_public_payload(public_payload),
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    return SpecialistTeamEvidenceProvenanceIntegrityReport(
        **values,
        derived_validation_digest=_report_digest_from_values(values),
    )


def _build_rows(
    evidence: tuple[SpecialistTeamEvidenceProvenanceIntegrityEvidence, ...],
) -> tuple[SpecialistTeamEvidenceProvenanceIntegrityRow, ...]:
    has_valid_official_anchor = any(_is_valid_official_anchor(item) for item in evidence)
    return tuple(
        _row_for_evidence(item, has_valid_official_anchor=has_valid_official_anchor)
        for item in evidence
    )


def _row_for_evidence(
    item: SpecialistTeamEvidenceProvenanceIntegrityEvidence,
    *,
    has_valid_official_anchor: bool,
) -> SpecialistTeamEvidenceProvenanceIntegrityRow:
    reason_codes = _row_reason_codes(
        item,
        has_valid_official_anchor=has_valid_official_anchor,
    )
    return SpecialistTeamEvidenceProvenanceIntegrityRow(
        evidence_source_id=item.evidence_source_id,
        source_family_id=item.source_family_id,
        official_anchor_flag=item.official_anchor_flag,
        captured_at=item.captured_at,
        content_hash_present=item.content_hash_present,
        analyst_note_present=item.analyst_note_present,
        team_id=item.team_id,
        provenance_status=_status_from_reason_codes(reason_codes),
        reason_codes=reason_codes,
        manual_next_step=_row_manual_next_step(reason_codes),
    )


def _row_reason_codes(
    item: SpecialistTeamEvidenceProvenanceIntegrityEvidence,
    *,
    has_valid_official_anchor: bool,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    if _is_missing_public_identifier(item.evidence_source_id):
        reason_codes.append("missing_evidence_source_id")
    if _is_missing_public_identifier(item.source_family_id):
        reason_codes.append("missing_source_family_id")
    if item.captured_at is None:
        reason_codes.append("missing_captured_at")
    if not item.content_hash_present:
        reason_codes.append("missing_content_hash")
    if not item.analyst_note_present:
        reason_codes.append("missing_analyst_note")
    if _is_missing_public_identifier(item.team_id):
        reason_codes.append("missing_team_id")
    if _needs_official_anchor_reason(
        item,
        has_valid_official_anchor=has_valid_official_anchor,
    ):
        reason_codes.append("missing_official_anchor")
    if not reason_codes:
        reason_codes.append("provenance_integrity_pass")
    return _normalize_reason_codes(tuple(reason_codes))


def _needs_official_anchor_reason(
    item: SpecialistTeamEvidenceProvenanceIntegrityEvidence,
    *,
    has_valid_official_anchor: bool,
) -> bool:
    if has_valid_official_anchor:
        return False
    if _is_missing_public_identifier(item.source_family_id):
        return True
    return item.source_family_id == "official" and not item.official_anchor_flag


def _is_valid_official_anchor(item: SpecialistTeamEvidenceProvenanceIntegrityEvidence) -> bool:
    return (
        item.source_family_id == "official"
        and item.official_anchor_flag is True
        and item.captured_at is not None
        and not _is_missing_public_identifier(item.evidence_source_id)
        and not _is_missing_public_identifier(item.team_id)
    )


def _status_from_reason_codes(reason_codes: tuple[str, ...]) -> str:
    if any(reason_code in _BLOCK_REASON_CODES for reason_code in reason_codes):
        return "block"
    if any(reason_code in _WATCH_REASON_CODES for reason_code in reason_codes):
        return "watch"
    return "pass"


def _row_manual_next_step(reason_codes: tuple[str, ...]) -> str:
    status = _status_from_reason_codes(reason_codes)
    if status == "block":
        return "manual_source_provenance_review"
    if "missing_content_hash" in reason_codes and "missing_analyst_note" in reason_codes:
        return "complete_evidence_hash_and_note_review"
    if "missing_content_hash" in reason_codes:
        return "attach_content_hash"
    if "missing_analyst_note" in reason_codes:
        return "add_analyst_note"
    return "archive_evidence_provenance_snapshot"


def _report_status(rows: tuple[SpecialistTeamEvidenceProvenanceIntegrityRow, ...]) -> str:
    if any(row.provenance_status == "block" for row in rows):
        return "block"
    if any(row.provenance_status == "watch" for row in rows):
        return "watch"
    return "pass"


def _report_manual_next_step(
    rows: tuple[SpecialistTeamEvidenceProvenanceIntegrityRow, ...],
) -> str:
    status = _report_status(rows)
    if status == "block":
        return "manual_source_provenance_review"
    if status == "watch":
        return "complete_evidence_hash_and_note_review"
    return "archive_evidence_provenance_snapshot"


def _report_reason_codes(
    rows: tuple[SpecialistTeamEvidenceProvenanceIntegrityRow, ...],
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    for row in rows:
        reason_codes.extend(row.reason_codes)
    return _normalize_reason_codes(tuple(reason_codes or ("provenance_integrity_pass",)))


def _status_count(
    rows: tuple[SpecialistTeamEvidenceProvenanceIntegrityRow, ...],
    status: str,
) -> int:
    return sum(1 for row in rows if row.provenance_status == status)


def _normalize_evidence(
    evidence: Sequence[SpecialistTeamEvidenceProvenanceIntegrityEvidence],
) -> tuple[SpecialistTeamEvidenceProvenanceIntegrityEvidence, ...]:
    if isinstance(evidence, (str, bytes)) or not isinstance(evidence, Sequence):
        raise ValueError("evidence must be a sequence")
    normalized: list[SpecialistTeamEvidenceProvenanceIntegrityEvidence] = []
    seen: set[str] = set()
    for item in evidence:
        if type(item) is not SpecialistTeamEvidenceProvenanceIntegrityEvidence:
            raise ValueError(
                "evidence must contain SpecialistTeamEvidenceProvenanceIntegrityEvidence",
            )
        if item.evidence_source_id is not None:
            if item.evidence_source_id in seen:
                raise ValueError("evidence must not contain duplicate evidence_source_id")
            seen.add(item.evidence_source_id)
        normalized.append(item)
    return tuple(normalized)


def _normalize_rows(
    rows: Sequence[SpecialistTeamEvidenceProvenanceIntegrityRow],
) -> tuple[SpecialistTeamEvidenceProvenanceIntegrityRow, ...]:
    if isinstance(rows, (str, bytes)) or not isinstance(rows, Sequence):
        raise ValueError("rows must be a sequence")
    normalized: list[SpecialistTeamEvidenceProvenanceIntegrityRow] = []
    seen: set[str] = set()
    for row in rows:
        if type(row) is not SpecialistTeamEvidenceProvenanceIntegrityRow:
            raise ValueError("rows must contain SpecialistTeamEvidenceProvenanceIntegrityRow")
        if row.evidence_source_id is not None:
            if row.evidence_source_id in seen:
                raise ValueError("rows must not contain duplicate evidence_source_id")
            seen.add(row.evidence_source_id)
        normalized.append(row)
    return tuple(normalized)


def _normalize_public_payload(
    items: Sequence[SpecialistTeamEvidenceProvenanceIntegrityPublicPayloadItem],
) -> tuple[SpecialistTeamEvidenceProvenanceIntegrityPublicPayloadItem, ...]:
    if isinstance(items, (str, bytes)) or not isinstance(items, Sequence):
        raise ValueError("public_payload must be a sequence")
    normalized: list[SpecialistTeamEvidenceProvenanceIntegrityPublicPayloadItem] = []
    seen: set[str] = set()
    for item in items:
        if type(item) is not SpecialistTeamEvidenceProvenanceIntegrityPublicPayloadItem:
            raise ValueError(
                "public_payload must contain "
                "SpecialistTeamEvidenceProvenanceIntegrityPublicPayloadItem",
            )
        if item.key in seen:
            raise ValueError("public_payload keys must be unique")
        seen.add(item.key)
        normalized.append(item)
    return tuple(sorted(normalized, key=lambda item: item.key))


def _validate_row(row: SpecialistTeamEvidenceProvenanceIntegrityRow) -> None:
    if row.provenance_status != _status_from_reason_codes(row.reason_codes):
        raise ValueError("provenance_status must match reason_codes")
    if row.manual_next_step != _row_manual_next_step(row.reason_codes):
        raise ValueError("manual_next_step must match reason_codes")
    if row.reason_codes == ("provenance_integrity_pass",) and row.provenance_status != "pass":
        raise ValueError("pass reason must match pass status")
    if "provenance_integrity_pass" in row.reason_codes and len(row.reason_codes) > 1:
        raise ValueError("pass reason must stand alone")


def _validate_report(report: SpecialistTeamEvidenceProvenanceIntegrityReport) -> None:
    if report.evidence_source_count != _decimal_count(len(report.rows)):
        raise ValueError("evidence_source_count must equal row count")
    if report.pass_count != _decimal_count(_status_count(report.rows, "pass")):
        raise ValueError("pass_count must equal passing rows")
    if report.watch_count != _decimal_count(_status_count(report.rows, "watch")):
        raise ValueError("watch_count must equal watched rows")
    if report.block_count != _decimal_count(_status_count(report.rows, "block")):
        raise ValueError("block_count must equal blocked rows")
    expected_team_count = _decimal_count(
        len({row.team_id for row in report.rows if not _is_missing_public_identifier(row.team_id)}),
    )
    if report.team_count != expected_team_count:
        raise ValueError("team_count must equal distinct present teams")
    if report.provenance_status != _report_status(report.rows):
        raise ValueError("provenance_status must match row statuses")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match row reason codes")
    if report.manual_next_step != _report_manual_next_step(report.rows):
        raise ValueError("manual_next_step must match row statuses")


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if getattr(value, field_name) is not True:
            raise ValueError(f"{label} {field_name} must be True")


def _normalize_optional_public_identifier(
    field_name: str,
    value: object,
    *,
    missing_sentinel: bool,
) -> str | None:
    if value is None:
        return None
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a public identifier")
    stripped = value.strip()
    if not stripped:
        return None
    if missing_sentinel and stripped.lower() in _MISSING_LABELS:
        return "missing"
    return _require_public_identifier(field_name, stripped)


def _is_missing_public_identifier(value: object) -> bool:
    return value is None or (type(value) is str and value.lower() in _MISSING_LABELS)


def _require_public_identifier(field_name: str, value: object) -> str:
    if type(value) is not str or not _PUBLIC_IDENTIFIER_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a public identifier")
    _reject_unsafe_public_string(field_name, value)
    return value


def _require_public_text(field_name: str, value: object) -> str:
    if type(value) is not str or not value.strip():
        raise ValueError(f"{field_name} must be public text")
    if len(value) > 256:
        raise ValueError(f"{field_name} must be short public text")
    _reject_unsafe_public_string(field_name, value)
    return value


def _require_bool(field_name: str, value: object) -> bool:
    if type(value) is not bool:
        raise ValueError(f"{field_name} must be a bool")
    return value


def _require_status(field_name: str, value: object) -> str:
    if type(value) is not str or value not in _STATUSES:
        raise ValueError(f"{field_name} must be pass, watch, or block")
    return value


def _require_manual_next_step(field_name: str, value: object) -> str:
    if type(value) is not str or value not in (
        "archive_evidence_provenance_snapshot",
        "attach_content_hash",
        "add_analyst_note",
        "complete_evidence_hash_and_note_review",
        "manual_source_provenance_review",
    ):
        raise ValueError(f"{field_name} must be a supported manual step")
    _reject_unsafe_public_string(field_name, value)
    return value


def _require_sha256_digest(field_name: str, value: object) -> str:
    if type(value) is not str or not _DIGEST_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a SHA-256 digest")
    return value


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return _quantize(value)


def _require_nonnegative_count_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < _ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _decimal_count(value: int) -> Decimal:
    if value < 0:
        raise ValueError("count must be nonnegative")
    return Decimal(value).quantize(_QUANT)


def _quantize(value: Decimal) -> Decimal:
    return value.quantize(_QUANT, rounding=ROUND_HALF_UP)


def _normalize_reason_codes(reason_codes: Sequence[str]) -> tuple[str, ...]:
    if isinstance(reason_codes, (str, bytes)) or not isinstance(reason_codes, Sequence):
        raise ValueError("reason_codes must be a sequence")
    normalized: list[str] = []
    for reason_code in reason_codes:
        _require_public_identifier("reason_code", reason_code)
        if reason_code not in _REASON_CODE_SEQUENCE:
            raise ValueError("reason_code must be supported")
        if reason_code not in normalized:
            normalized.append(reason_code)
    return tuple(
        reason_code
        for reason_code in _REASON_CODE_SEQUENCE
        if reason_code in normalized
    )


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _report_values_without_digest(
    report: SpecialistTeamEvidenceProvenanceIntegrityReport,
) -> dict[str, object]:
    values = asdict(report)
    values.pop("derived_validation_digest", None)
    return values


def _report_digest_from_values(values: Mapping[str, object]) -> str:
    payload = _json_ready(values)
    _reject_unsafe_public_payload(
        "derived_validation_digest payload",
        payload,
        allow_json_containers=True,
    )
    canonical = json.dumps(
        payload,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _json_ready(value: Any) -> Any:
    if value is None:
        return None
    if is_dataclass(value) and not isinstance(value, type):
        return _json_ready(asdict(value))
    if type(value) is Decimal:
        if not value.is_finite():
            raise ValueError("Decimal payload value must be finite")
        return str(value)
    if type(value) is datetime:
        return _as_utc("datetime payload value", value).isoformat()
    if type(value) is bool or type(value) is str:
        return value
    if type(value) is int or isinstance(value, float):
        raise ValueError("numeric payload values must be Decimal strings")
    if isinstance(value, Mapping):
        ready: dict[str, Any] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            ready[key] = _json_ready(item)
        return ready
    if isinstance(value, (list, tuple)):
        return [_json_ready(item) for item in value]
    raise ValueError("payload value is not JSON serializable")


def _reject_unsafe_public_payload(
    label: str,
    value: object,
    path: str = "",
    *,
    allow_json_containers: bool = False,
) -> None:
    current_path = path or label
    if is_dataclass(value) and not isinstance(value, type):
        for field in fields(value):
            _reject_unsafe_public_payload(
                label,
                getattr(value, field.name),
                field.name if not path else f"{path}.{field.name}",
                allow_json_containers=allow_json_containers,
            )
        return
    if isinstance(value, Mapping):
        if not allow_json_containers:
            raise ValueError(f"{label} must not expose mapping payloads")
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("public payload keys must be strings")
            _reject_unsafe_public_string(current_path, key)
            _reject_unsafe_public_payload(
                label,
                item,
                key if not path else f"{path}.{key}",
                allow_json_containers=allow_json_containers,
            )
        return
    if isinstance(value, (list, tuple)):
        if not allow_json_containers and not all(
            type(item) in (str, bool, Decimal, datetime)
            or item is None
            or (is_dataclass(item) and not isinstance(item, type))
            for item in value
        ):
            raise ValueError(f"{label} must not expose nested payloads")
        for index, item in enumerate(value):
            _reject_unsafe_public_payload(
                label,
                item,
                f"{current_path}[{index}]",
                allow_json_containers=allow_json_containers,
            )
        return
    if type(value) is str:
        _reject_unsafe_public_string(current_path, value)


def _reject_unsafe_public_string(field_name: str, value: str) -> None:
    lowered = value.lower()
    if any(term in lowered for term in _UNSAFE_PUBLIC_TERMS):
        raise ValueError(f"unsafe public value for {field_name}")


__all__ = (
    "DEFAULT_SPECIALIST_TEAM_EVIDENCE_PROVENANCE_INTEGRITY_REPORT_VERSION",
    "SpecialistTeamEvidenceProvenanceIntegrityEvidence",
    "SpecialistTeamEvidenceProvenanceIntegrityPublicPayloadItem",
    "SpecialistTeamEvidenceProvenanceIntegrityRow",
    "SpecialistTeamEvidenceProvenanceIntegrityReport",
    "build_specialist_team_evidence_provenance_integrity_report",
)
