"""Phase 1 report-only official resolution evidence gap queue."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import asdict, dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal, ROUND_HALF_UP
import hashlib
import json
import re
from typing import Any


DEFAULT_RESEARCH_PACKET_OFFICIAL_RESOLUTION_EVIDENCE_GAP_QUEUE_V2_CONFIG_VERSION = (
    "research-packet-official-resolution-evidence-gap-queue-v2"
)

_QUANT = Decimal("0.000001")
_ZERO = Decimal("0.000000")
_ONE = Decimal("1.000000")
_PUBLIC_IDENTIFIER_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,127}$")
_DIGEST_RE = re.compile(r"^[0-9a-f]{64}$")
_EVIDENCE_ROLES = frozenset(("official", "corroborating", "context"))
_QUEUE_STATUSES = frozenset(("pass", "watch", "blocked"))
_PHASE_FLAG_FIELDS = frozenset(("paper_only", "report_only", "readonly"))
_UNSAFE_PUBLIC_TERMS = (
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
_REASON_CODE_SEQUENCE = (
    "empty_evidence",
    "missing_official_resolution_evidence",
    "official_resolution_evidence_observed",
    "missing_corroborated_evidence",
    "corroborated_evidence_boost",
    "evidence_score_watch",
    "official_resolution_evidence_complete",
)


@dataclass(frozen=True)
class ResearchPacketOfficialResolutionEvidenceGapQueueConfig:
    config_version: str = (
        DEFAULT_RESEARCH_PACKET_OFFICIAL_RESOLUTION_EVIDENCE_GAP_QUEUE_V2_CONFIG_VERSION
    )
    min_complete_score: Decimal = Decimal("0.650000")
    missing_official_evidence_penalty: Decimal = Decimal("0.400000")
    corroborated_evidence_boost_per_family: Decimal = Decimal("0.100000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchPacketOfficialResolutionEvidenceGapQueueConfig:
            raise TypeError(
                "ResearchPacketOfficialResolutionEvidenceGapQueueConfig does not "
                "support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchPacketOfficialResolutionEvidenceGapQueueConfig:
            raise ValueError(
                "config must be exactly "
                "ResearchPacketOfficialResolutionEvidenceGapQueueConfig",
            )
        _require_public_identifier("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_PACKET_OFFICIAL_RESOLUTION_EVIDENCE_GAP_QUEUE_V2_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "min_complete_score",
            "missing_official_evidence_penalty",
            "corroborated_evidence_boost_per_family",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        _require_hard_flags("config", self)
        _reject_unsafe_public_payload("config", self)


@dataclass(frozen=True)
class ResearchPacketOfficialResolutionEvidence:
    packet_id: str
    criterion_id: str
    source_id: str
    source_family: str
    source_role: str
    observed_at: datetime
    confidence_score: Decimal
    supports_resolution: bool = True
    public_note: str | None = None
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchPacketOfficialResolutionEvidence:
            raise TypeError(
                "ResearchPacketOfficialResolutionEvidence does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchPacketOfficialResolutionEvidence:
            raise ValueError(
                "evidence must be exactly ResearchPacketOfficialResolutionEvidence",
            )
        for field_name in ("packet_id", "criterion_id", "source_id", "source_family"):
            _require_public_identifier(field_name, getattr(self, field_name))
        _require_evidence_role("source_role", self.source_role)
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        object.__setattr__(
            self,
            "confidence_score",
            _require_ratio_decimal("confidence_score", self.confidence_score),
        )
        _require_bool("supports_resolution", self.supports_resolution)
        object.__setattr__(
            self,
            "public_note",
            _normalize_optional_public_text("public_note", self.public_note),
        )
        _require_hard_flags("evidence", self)
        _reject_unsafe_public_payload("evidence", self)


@dataclass(frozen=True)
class ResearchPacketOfficialResolutionEvidencePublicPayloadItem:
    key: str
    value: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchPacketOfficialResolutionEvidencePublicPayloadItem:
            raise TypeError(
                "ResearchPacketOfficialResolutionEvidencePublicPayloadItem does not "
                "support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchPacketOfficialResolutionEvidencePublicPayloadItem:
            raise ValueError(
                "public payload item must be exactly "
                "ResearchPacketOfficialResolutionEvidencePublicPayloadItem",
            )
        _require_public_identifier("key", self.key)
        object.__setattr__(self, "value", _require_public_text("value", self.value))
        _require_hard_flags("public payload item", self)
        _reject_unsafe_public_payload("public payload item", self)


@dataclass(frozen=True)
class ResearchPacketOfficialResolutionEvidenceGapQueueRow:
    packet_id: str
    criterion_id: str
    evidence_count: Decimal
    official_evidence_count: Decimal
    supporting_evidence_count: Decimal
    corroborating_family_count: Decimal
    missing_official_evidence_penalty: Decimal
    corroborated_evidence_boost: Decimal
    average_support_confidence_score: Decimal
    official_resolution_evidence_score: Decimal
    queue_status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchPacketOfficialResolutionEvidenceGapQueueRow:
            raise TypeError(
                "ResearchPacketOfficialResolutionEvidenceGapQueueRow does not "
                "support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchPacketOfficialResolutionEvidenceGapQueueRow:
            raise ValueError(
                "row must be exactly ResearchPacketOfficialResolutionEvidenceGapQueueRow",
            )
        _require_public_identifier("packet_id", self.packet_id)
        _require_public_identifier("criterion_id", self.criterion_id)
        for field_name in (
            "evidence_count",
            "official_evidence_count",
            "supporting_evidence_count",
            "corroborating_family_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_count_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "missing_official_evidence_penalty",
            "corroborated_evidence_boost",
            "average_support_confidence_score",
            "official_resolution_evidence_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        _require_queue_status("queue_status", self.queue_status)
        object.__setattr__(self, "reason_codes", _normalize_reason_codes(self.reason_codes))
        _validate_row_consistency(self)
        _require_hard_flags("row", self)
        _reject_unsafe_public_payload("row", self)


@dataclass(frozen=True)
class ResearchPacketOfficialResolutionEvidenceGapQueueReport:
    generated_at: datetime
    config_version: str
    queue_status: str
    packet_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    blocked_count: Decimal
    average_official_resolution_evidence_score: Decimal
    max_missing_official_evidence_penalty: Decimal
    rows: tuple[ResearchPacketOfficialResolutionEvidenceGapQueueRow, ...]
    reason_codes: tuple[str, ...]
    public_payload: tuple[ResearchPacketOfficialResolutionEvidencePublicPayloadItem, ...]
    derived_validation_digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchPacketOfficialResolutionEvidenceGapQueueReport:
            raise TypeError(
                "ResearchPacketOfficialResolutionEvidenceGapQueueReport does not "
                "support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchPacketOfficialResolutionEvidenceGapQueueReport:
            raise ValueError(
                "report must be exactly "
                "ResearchPacketOfficialResolutionEvidenceGapQueueReport",
            )
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_identifier("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_PACKET_OFFICIAL_RESOLUTION_EVIDENCE_GAP_QUEUE_V2_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        _require_queue_status("queue_status", self.queue_status)
        for field_name in ("packet_count", "pass_count", "watch_count", "blocked_count"):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_count_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "average_official_resolution_evidence_score",
            "max_missing_official_evidence_penalty",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        object.__setattr__(self, "reason_codes", _normalize_reason_codes(self.reason_codes))
        object.__setattr__(
            self,
            "public_payload",
            _normalize_public_payload(self.public_payload),
        )
        _require_sha256_digest("derived_validation_digest", self.derived_validation_digest)
        _validate_report_consistency(self)
        _require_hard_flags("report", self)
        _reject_unsafe_public_payload("report", self)
        expected_digest = _report_digest_from_values(_report_values_without_digest(self))
        if self.derived_validation_digest != expected_digest:
            raise ValueError("derived_validation_digest does not match report payload")

    @property
    def payload(self) -> dict[str, object]:
        payload = _json_ready(asdict(self))
        _reject_unsafe_public_payload(
            "ResearchPacketOfficialResolutionEvidenceGapQueueReport.payload",
            payload,
            allow_json_containers=True,
        )
        if type(payload) is not dict:
            raise ValueError("payload must be a dict")
        return payload


def build_research_packet_official_resolution_evidence_gap_queue_v2_report(
    evidence: Sequence[ResearchPacketOfficialResolutionEvidence],
    *,
    generated_at: datetime,
    config: ResearchPacketOfficialResolutionEvidenceGapQueueConfig | None = None,
    public_payload: Sequence[ResearchPacketOfficialResolutionEvidencePublicPayloadItem] = (),
) -> ResearchPacketOfficialResolutionEvidenceGapQueueReport:
    """Build a local report-only official resolution evidence gap queue snapshot."""

    if config is None:
        config = ResearchPacketOfficialResolutionEvidenceGapQueueConfig()
    if type(config) is not ResearchPacketOfficialResolutionEvidenceGapQueueConfig:
        raise ValueError(
            "config must be a ResearchPacketOfficialResolutionEvidenceGapQueueConfig",
        )
    generated_at = _as_utc("generated_at", generated_at)
    normalized_evidence = _normalize_evidence(evidence)
    for item in normalized_evidence:
        if item.observed_at > generated_at:
            raise ValueError("evidence observed_at must not be after generated_at")
    payload_items = _normalize_public_payload(public_payload)
    rows = _build_rows(normalized_evidence, config)
    reason_codes = _report_reason_codes(rows)
    values: dict[str, object] = {
        "generated_at": generated_at,
        "config_version": config.config_version,
        "queue_status": _report_status(rows),
        "packet_count": _decimal_count(len(rows)),
        "pass_count": _decimal_count(_status_count(rows, "pass")),
        "watch_count": _decimal_count(_status_count(rows, "watch")),
        "blocked_count": _decimal_count(_status_count(rows, "blocked")),
        "average_official_resolution_evidence_score": _average(
            tuple(row.official_resolution_evidence_score for row in rows),
        ),
        "max_missing_official_evidence_penalty": max(
            (row.missing_official_evidence_penalty for row in rows),
            default=_ZERO,
        ),
        "rows": rows,
        "reason_codes": reason_codes,
        "public_payload": payload_items,
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    return ResearchPacketOfficialResolutionEvidenceGapQueueReport(
        **values,
        derived_validation_digest=_report_digest_from_values(values),
    )


def research_packet_official_resolution_evidence_gap_queue_v2_payload(
    report: ResearchPacketOfficialResolutionEvidenceGapQueueReport,
) -> dict[str, object]:
    if type(report) is not ResearchPacketOfficialResolutionEvidenceGapQueueReport:
        raise ValueError(
            "report must be a ResearchPacketOfficialResolutionEvidenceGapQueueReport",
        )
    return report.payload


def _build_rows(
    evidence: tuple[ResearchPacketOfficialResolutionEvidence, ...],
    config: ResearchPacketOfficialResolutionEvidenceGapQueueConfig,
) -> tuple[ResearchPacketOfficialResolutionEvidenceGapQueueRow, ...]:
    grouped: dict[tuple[str, str], list[ResearchPacketOfficialResolutionEvidence]] = {}
    for item in evidence:
        grouped.setdefault((item.packet_id, item.criterion_id), []).append(item)
    rows = [
        _row_for_group(packet_id, criterion_id, tuple(items), config)
        for (packet_id, criterion_id), items in sorted(grouped.items())
    ]
    return tuple(rows)


def _row_for_group(
    packet_id: str,
    criterion_id: str,
    evidence: tuple[ResearchPacketOfficialResolutionEvidence, ...],
    config: ResearchPacketOfficialResolutionEvidenceGapQueueConfig,
) -> ResearchPacketOfficialResolutionEvidenceGapQueueRow:
    supporting = tuple(item for item in evidence if item.supports_resolution)
    official = tuple(item for item in supporting if item.source_role == "official")
    corroborating_families = {
        item.source_family
        for item in supporting
        if item.source_role == "corroborating"
    }
    official_count = _decimal_count(len(official))
    supporting_count = _decimal_count(len(supporting))
    corroborating_family_count = _decimal_count(len(corroborating_families))
    missing_penalty = (
        config.missing_official_evidence_penalty
        if official_count == _ZERO
        else _ZERO
    )
    corroborated_boost = _clamp_ratio(
        corroborating_family_count * config.corroborated_evidence_boost_per_family,
    )
    average_support_confidence = _average(
        tuple(item.confidence_score for item in supporting),
    )
    evidence_score = _clamp_ratio(
        average_support_confidence + corroborated_boost - missing_penalty,
    )
    queue_status = _row_status(
        official_evidence_count=official_count,
        evidence_score=evidence_score,
        config=config,
    )
    return ResearchPacketOfficialResolutionEvidenceGapQueueRow(
        packet_id=packet_id,
        criterion_id=criterion_id,
        evidence_count=_decimal_count(len(evidence)),
        official_evidence_count=official_count,
        supporting_evidence_count=supporting_count,
        corroborating_family_count=corroborating_family_count,
        missing_official_evidence_penalty=missing_penalty,
        corroborated_evidence_boost=corroborated_boost,
        average_support_confidence_score=average_support_confidence,
        official_resolution_evidence_score=evidence_score,
        queue_status=queue_status,
        reason_codes=_row_reason_codes(
            official_evidence_count=official_count,
            corroborating_family_count=corroborating_family_count,
            evidence_score=evidence_score,
            queue_status=queue_status,
            config=config,
        ),
    )


def _row_status(
    *,
    official_evidence_count: Decimal,
    evidence_score: Decimal,
    config: ResearchPacketOfficialResolutionEvidenceGapQueueConfig,
) -> str:
    if official_evidence_count == _ZERO:
        return "blocked"
    if evidence_score >= config.min_complete_score:
        return "pass"
    return "watch"


def _row_reason_codes(
    *,
    official_evidence_count: Decimal,
    corroborating_family_count: Decimal,
    evidence_score: Decimal,
    queue_status: str,
    config: ResearchPacketOfficialResolutionEvidenceGapQueueConfig,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    if official_evidence_count == _ZERO:
        reason_codes.append("missing_official_resolution_evidence")
    else:
        reason_codes.append("official_resolution_evidence_observed")
    if corroborating_family_count == _ZERO:
        reason_codes.append("missing_corroborated_evidence")
    else:
        reason_codes.append("corroborated_evidence_boost")
    if (
        official_evidence_count > _ZERO
        and evidence_score < config.min_complete_score
    ):
        reason_codes.append("evidence_score_watch")
    if queue_status == "pass":
        reason_codes.append("official_resolution_evidence_complete")
    return _normalize_reason_codes(tuple(reason_codes))


def _report_status(
    rows: tuple[ResearchPacketOfficialResolutionEvidenceGapQueueRow, ...],
) -> str:
    if not rows:
        return "blocked"
    if any(row.queue_status == "blocked" for row in rows):
        return "blocked"
    if any(row.queue_status == "watch" for row in rows):
        return "watch"
    return "pass"


def _report_reason_codes(
    rows: tuple[ResearchPacketOfficialResolutionEvidenceGapQueueRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return ("empty_evidence",)
    reason_codes: list[str] = []
    for row in rows:
        reason_codes.extend(row.reason_codes)
    return _normalize_reason_codes(tuple(reason_codes))


def _status_count(
    rows: tuple[ResearchPacketOfficialResolutionEvidenceGapQueueRow, ...],
    status: str,
) -> int:
    return sum(1 for row in rows if row.queue_status == status)


def _validate_row_consistency(
    row: ResearchPacketOfficialResolutionEvidenceGapQueueRow,
) -> None:
    if row.official_evidence_count > row.supporting_evidence_count:
        raise ValueError("official_evidence_count must not exceed supporting_evidence_count")
    if row.supporting_evidence_count > row.evidence_count:
        raise ValueError("supporting_evidence_count must not exceed evidence_count")
    if row.corroborating_family_count > row.supporting_evidence_count:
        raise ValueError("corroborating_family_count must not exceed supporting_evidence_count")
    if row.official_evidence_count == _ZERO:
        if row.missing_official_evidence_penalty == _ZERO:
            raise ValueError("missing_official_evidence_penalty must be positive")
        if row.queue_status != "blocked":
            raise ValueError("rows missing official evidence must be blocked")
        if "missing_official_resolution_evidence" not in row.reason_codes:
            raise ValueError("missing official evidence rows must include reason code")
    if row.official_evidence_count > _ZERO:
        if row.missing_official_evidence_penalty != _ZERO:
            raise ValueError("missing_official_evidence_penalty must be zero")
        if "official_resolution_evidence_observed" not in row.reason_codes:
            raise ValueError("official evidence rows must include reason code")
    if row.corroborating_family_count == _ZERO:
        if row.corroborated_evidence_boost != _ZERO:
            raise ValueError("corroborated_evidence_boost must be zero")
        if "missing_corroborated_evidence" not in row.reason_codes:
            raise ValueError("missing corroborated evidence rows must include reason code")
    if row.corroborating_family_count > _ZERO:
        if "corroborated_evidence_boost" not in row.reason_codes:
            raise ValueError("corroborated evidence rows must include boost reason code")
    if row.queue_status == "pass" and (
        "official_resolution_evidence_complete" not in row.reason_codes
    ):
        raise ValueError("pass rows must include official resolution evidence completion")


def _validate_report_consistency(
    report: ResearchPacketOfficialResolutionEvidenceGapQueueReport,
) -> None:
    if report.packet_count != _decimal_count(len(report.rows)):
        raise ValueError("packet_count must match rows")
    if report.pass_count != _decimal_count(_status_count(report.rows, "pass")):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _decimal_count(_status_count(report.rows, "watch")):
        raise ValueError("watch_count must match rows")
    if report.blocked_count != _decimal_count(_status_count(report.rows, "blocked")):
        raise ValueError("blocked_count must match rows")
    if report.average_official_resolution_evidence_score != _average(
        tuple(row.official_resolution_evidence_score for row in report.rows),
    ):
        raise ValueError("average_official_resolution_evidence_score must match rows")
    expected_max_penalty = max(
        (row.missing_official_evidence_penalty for row in report.rows),
        default=_ZERO,
    )
    if report.max_missing_official_evidence_penalty != expected_max_penalty:
        raise ValueError("max_missing_official_evidence_penalty must match rows")
    if report.queue_status != _report_status(report.rows):
        raise ValueError("queue_status must match row statuses")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")


def _normalize_evidence(
    evidence: Sequence[ResearchPacketOfficialResolutionEvidence],
) -> tuple[ResearchPacketOfficialResolutionEvidence, ...]:
    if isinstance(evidence, (str, bytes)) or not isinstance(evidence, Sequence):
        raise ValueError("evidence must be a sequence")
    normalized: list[ResearchPacketOfficialResolutionEvidence] = []
    seen: set[tuple[str, str, str]] = set()
    for item in evidence:
        if type(item) is not ResearchPacketOfficialResolutionEvidence:
            raise ValueError(
                "evidence items must be ResearchPacketOfficialResolutionEvidence",
            )
        key = (item.packet_id, item.criterion_id, item.source_id)
        if key in seen:
            raise ValueError("evidence source_id values must be unique per criterion")
        seen.add(key)
        normalized.append(item)
    return tuple(
        sorted(
            normalized,
            key=lambda item: (
                item.packet_id,
                item.criterion_id,
                item.observed_at,
                item.source_id,
            ),
        ),
    )


def _normalize_rows(
    rows: Sequence[ResearchPacketOfficialResolutionEvidenceGapQueueRow],
) -> tuple[ResearchPacketOfficialResolutionEvidenceGapQueueRow, ...]:
    if isinstance(rows, (str, bytes)) or not isinstance(rows, Sequence):
        raise ValueError("rows must be a sequence")
    normalized: list[ResearchPacketOfficialResolutionEvidenceGapQueueRow] = []
    for row in rows:
        if type(row) is not ResearchPacketOfficialResolutionEvidenceGapQueueRow:
            raise ValueError(
                "rows must contain ResearchPacketOfficialResolutionEvidenceGapQueueRow",
            )
        normalized.append(row)
    return tuple(sorted(normalized, key=lambda row: (row.packet_id, row.criterion_id)))


def _normalize_public_payload(
    public_payload: Sequence[ResearchPacketOfficialResolutionEvidencePublicPayloadItem],
) -> tuple[ResearchPacketOfficialResolutionEvidencePublicPayloadItem, ...]:
    if isinstance(public_payload, (str, bytes)) or not isinstance(public_payload, Sequence):
        raise ValueError("public_payload must be a sequence")
    normalized: list[ResearchPacketOfficialResolutionEvidencePublicPayloadItem] = []
    seen: set[str] = set()
    for item in public_payload:
        if type(item) is not ResearchPacketOfficialResolutionEvidencePublicPayloadItem:
            raise ValueError(
                "public_payload items must be "
                "ResearchPacketOfficialResolutionEvidencePublicPayloadItem",
            )
        if item.key in seen:
            raise ValueError("public_payload keys must be unique")
        seen.add(item.key)
        normalized.append(item)
    return tuple(sorted(normalized, key=lambda item: item.key))


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in _PHASE_FLAG_FIELDS:
        if getattr(value, field_name) is not True:
            raise ValueError(f"{field_name} must be True for {label}")


def _require_bool(field_name: str, value: object) -> bool:
    if type(value) is not bool:
        raise ValueError(f"{field_name} must be a bool")
    return value


def _require_public_identifier(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not _PUBLIC_IDENTIFIER_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a public identifier")
    _reject_unsafe_public_string(field_name, value)
    return value


def _require_public_text(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if value.strip() != value or not value:
        raise ValueError(f"{field_name} must be non-empty public text")
    if len(value) > 512:
        raise ValueError(f"{field_name} must not exceed 512 characters")
    _reject_unsafe_public_string(field_name, value)
    return value


def _normalize_optional_public_text(field_name: str, value: object) -> str | None:
    if value is None:
        return None
    return _require_public_text(field_name, value)


def _reject_unsafe_public_string(field_name: str, value: str) -> None:
    lowered = value.lower()
    if "://" in lowered or "?" in lowered or "@" in lowered:
        raise ValueError(f"{field_name} has unsafe public value")
    if any(term in lowered for term in _UNSAFE_PUBLIC_TERMS):
        raise ValueError(f"{field_name} has unsafe public value")


def _require_evidence_role(field_name: str, value: object) -> str:
    if type(value) is not str or value not in _EVIDENCE_ROLES:
        raise ValueError(f"{field_name} must be a known evidence role")
    return value


def _require_queue_status(field_name: str, value: object) -> str:
    if type(value) is not str or value not in _QUEUE_STATUSES:
        raise ValueError(f"{field_name} must be a known queue status")
    return value


def _require_sha256_digest(field_name: str, value: object) -> str:
    if type(value) is not str or not _DIGEST_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a lowercase sha256 digest")
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


def _require_ratio_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < _ZERO or normalized > _ONE:
        raise ValueError(f"{field_name} must be between zero and one")
    return normalized


def _decimal_count(value: int) -> Decimal:
    if value < 0:
        raise ValueError("count must be nonnegative")
    return Decimal(value).quantize(_QUANT)


def _average(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return _ZERO
    return _quantize(sum(values, _ZERO) / Decimal(len(values)))


def _clamp_ratio(value: Decimal) -> Decimal:
    normalized = _quantize(value)
    if normalized < _ZERO:
        return _ZERO
    if normalized > _ONE:
        return _ONE
    return normalized


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
    report: ResearchPacketOfficialResolutionEvidenceGapQueueReport,
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
            _reject_unsafe_public_key(field.name, current_path)
            _reject_unsafe_public_payload(
                label,
                getattr(value, field.name),
                field.name if not path else f"{path}.{field.name}",
                allow_json_containers=allow_json_containers,
            )
        return
    if isinstance(value, Mapping):
        if not allow_json_containers:
            raise ValueError(f"{current_path} must remain constructor-normalized")
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            _reject_unsafe_public_key(key, current_path)
            _reject_unsafe_public_payload(
                label,
                item,
                key if not path else f"{path}.{key}",
                allow_json_containers=True,
            )
        return
    if isinstance(value, (list, tuple)):
        if type(value) is list and not allow_json_containers:
            raise ValueError(f"{current_path} must remain constructor-normalized")
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
        return
    if (
        value is None
        or type(value) is bool
        or type(value) is Decimal
        or type(value) is datetime
    ):
        return
    raise ValueError(f"{current_path} is not a supported public payload value")


def _reject_unsafe_public_key(key: str, path: str) -> None:
    lowered = key.lower()
    if any(term in lowered for term in _UNSAFE_PUBLIC_TERMS):
        raise ValueError(f"{path}.{key} has unsafe public field")


__all__ = (
    "DEFAULT_RESEARCH_PACKET_OFFICIAL_RESOLUTION_EVIDENCE_GAP_QUEUE_V2_CONFIG_VERSION",
    "ResearchPacketOfficialResolutionEvidence",
    "ResearchPacketOfficialResolutionEvidenceGapQueueConfig",
    "ResearchPacketOfficialResolutionEvidenceGapQueueReport",
    "ResearchPacketOfficialResolutionEvidenceGapQueueRow",
    "ResearchPacketOfficialResolutionEvidencePublicPayloadItem",
    "build_research_packet_official_resolution_evidence_gap_queue_v2_report",
    "research_packet_official_resolution_evidence_gap_queue_v2_payload",
)
