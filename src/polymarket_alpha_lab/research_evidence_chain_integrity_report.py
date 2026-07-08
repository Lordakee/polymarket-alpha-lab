"""Report-only research evidence chain integrity snapshot."""

from __future__ import annotations

from dataclasses import asdict, dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal, ROUND_HALF_UP
import hashlib
import json
import re
from typing import Any, Mapping, Sequence


DEFAULT_RESEARCH_EVIDENCE_CHAIN_INTEGRITY_CONFIG_VERSION = (
    "research-evidence-chain-integrity-report-v1"
)

_QUANT = Decimal("0.000001")
_ZERO = Decimal("0.000000")
_ONE = Decimal("1.000000")
_PUBLIC_IDENTIFIER_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,127}$")
_DIGEST_RE = re.compile(r"^[0-9a-f]{64}$")
_CHAIN_STATUSES = frozenset(("pass", "watch", "block"))
_EVIDENCE_STANCES = frozenset(("supporting", "counterevidence"))
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
    "recommend",
    "advice",
)
_REASON_CODE_SEQUENCE = (
    "empty_evidence",
    "missing_supporting_evidence",
    "insufficient_source_independence",
    "missing_counterevidence",
    "chronology_issue",
    "citation_summary_gap",
    "complete_evidence_chain",
)


@dataclass(frozen=True)
class ResearchEvidenceChainIntegrityConfig:
    config_version: str = DEFAULT_RESEARCH_EVIDENCE_CHAIN_INTEGRITY_CONFIG_VERSION
    min_independent_support_family_count: Decimal = Decimal("2.000000")
    min_counterevidence_count: Decimal = Decimal("1.000000")
    min_citation_summary_characters: Decimal = Decimal("16.000000")
    gap_penalty: Decimal = Decimal("0.250000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchEvidenceChainIntegrityConfig:
            raise TypeError(
                "ResearchEvidenceChainIntegrityConfig does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchEvidenceChainIntegrityConfig:
            raise ValueError(
                "config must be exactly ResearchEvidenceChainIntegrityConfig",
            )
        _require_public_identifier("config_version", self.config_version)
        if self.config_version != DEFAULT_RESEARCH_EVIDENCE_CHAIN_INTEGRITY_CONFIG_VERSION:
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "min_independent_support_family_count",
            "min_counterevidence_count",
            "min_citation_summary_characters",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_positive_count_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "gap_penalty",
            _require_ratio_decimal("gap_penalty", self.gap_penalty),
        )
        _require_hard_flags("config", self)
        _reject_unsafe_public_payload("config", self)


@dataclass(frozen=True)
class ResearchEvidenceChainEvidence:
    packet_id: str
    claim_id: str
    evidence_id: str
    source_id: str
    source_family: str
    stance: str
    source_event_at: datetime
    captured_at: datetime
    confidence_score: Decimal
    citation_summary: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchEvidenceChainEvidence:
            raise TypeError("ResearchEvidenceChainEvidence does not support subclassing")

    def __post_init__(self) -> None:
        if type(self) is not ResearchEvidenceChainEvidence:
            raise ValueError("evidence must be exactly ResearchEvidenceChainEvidence")
        for field_name in (
            "packet_id",
            "claim_id",
            "evidence_id",
            "source_id",
            "source_family",
        ):
            _require_public_identifier(field_name, getattr(self, field_name))
        _require_stance("stance", self.stance)
        object.__setattr__(
            self,
            "source_event_at",
            _as_utc("source_event_at", self.source_event_at),
        )
        object.__setattr__(self, "captured_at", _as_utc("captured_at", self.captured_at))
        object.__setattr__(
            self,
            "confidence_score",
            _require_ratio_decimal("confidence_score", self.confidence_score),
        )
        object.__setattr__(
            self,
            "citation_summary",
            _require_public_text("citation_summary", self.citation_summary),
        )
        _require_hard_flags("evidence", self)
        _reject_unsafe_public_payload("evidence", self)


@dataclass(frozen=True)
class ResearchEvidenceChainPublicPayloadItem:
    key: str
    value: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchEvidenceChainPublicPayloadItem:
            raise TypeError(
                "ResearchEvidenceChainPublicPayloadItem does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchEvidenceChainPublicPayloadItem:
            raise ValueError(
                "public payload item must be exactly "
                "ResearchEvidenceChainPublicPayloadItem",
            )
        _require_public_identifier("key", self.key)
        object.__setattr__(self, "value", _require_public_text("value", self.value))
        _require_hard_flags("public payload item", self)
        _reject_unsafe_public_payload("public payload item", self)


@dataclass(frozen=True)
class ResearchEvidenceChainIntegrityRow:
    packet_id: str
    claim_id: str
    source_count: Decimal
    supporting_source_count: Decimal
    independent_support_family_count: Decimal
    counterevidence_count: Decimal
    chronology_issue_count: Decimal
    citation_summary_gap_count: Decimal
    gap_count: Decimal
    integrity_score: Decimal
    chain_status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchEvidenceChainIntegrityRow:
            raise TypeError(
                "ResearchEvidenceChainIntegrityRow does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchEvidenceChainIntegrityRow:
            raise ValueError("row must be exactly ResearchEvidenceChainIntegrityRow")
        _require_public_identifier("packet_id", self.packet_id)
        _require_public_identifier("claim_id", self.claim_id)
        for field_name in (
            "source_count",
            "supporting_source_count",
            "independent_support_family_count",
            "counterevidence_count",
            "chronology_issue_count",
            "citation_summary_gap_count",
            "gap_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_count_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "integrity_score",
            _require_ratio_decimal("integrity_score", self.integrity_score),
        )
        _require_chain_status("chain_status", self.chain_status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes),
        )
        _validate_row_consistency(self)
        _require_hard_flags("row", self)
        _reject_unsafe_public_payload("row", self)


@dataclass(frozen=True)
class ResearchEvidenceChainIntegrityReport:
    generated_at: datetime
    config_version: str
    chain_status: str
    claim_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    average_integrity_score: Decimal
    total_gap_count: Decimal
    rows: tuple[ResearchEvidenceChainIntegrityRow, ...]
    reason_codes: tuple[str, ...]
    public_payload: tuple[ResearchEvidenceChainPublicPayloadItem, ...]
    derived_validation_digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchEvidenceChainIntegrityReport:
            raise TypeError(
                "ResearchEvidenceChainIntegrityReport does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchEvidenceChainIntegrityReport:
            raise ValueError("report must be exactly ResearchEvidenceChainIntegrityReport")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_identifier("config_version", self.config_version)
        if self.config_version != DEFAULT_RESEARCH_EVIDENCE_CHAIN_INTEGRITY_CONFIG_VERSION:
            raise ValueError("config_version must be the supported config version")
        _require_chain_status("chain_status", self.chain_status)
        for field_name in ("claim_count", "pass_count", "watch_count", "block_count"):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_count_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "average_integrity_score",
            _require_ratio_decimal(
                "average_integrity_score",
                self.average_integrity_score,
            ),
        )
        object.__setattr__(
            self,
            "total_gap_count",
            _require_nonnegative_count_decimal("total_gap_count", self.total_gap_count),
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
            "ResearchEvidenceChainIntegrityReport.payload",
            payload,
            allow_json_containers=True,
        )
        if type(payload) is not dict:
            raise ValueError("payload must be a dict")
        return payload


def build_research_evidence_chain_integrity_report(
    evidence: Sequence[ResearchEvidenceChainEvidence],
    *,
    generated_at: datetime,
    config: ResearchEvidenceChainIntegrityConfig | None = None,
    public_payload: Sequence[ResearchEvidenceChainPublicPayloadItem] = (),
) -> ResearchEvidenceChainIntegrityReport:
    """Build a local report-only research evidence chain integrity snapshot."""

    if config is None:
        config = ResearchEvidenceChainIntegrityConfig()
    if type(config) is not ResearchEvidenceChainIntegrityConfig:
        raise ValueError("config must be a ResearchEvidenceChainIntegrityConfig")
    generated_at = _as_utc("generated_at", generated_at)
    normalized_evidence = _normalize_evidence(evidence)
    for item in normalized_evidence:
        if item.captured_at > generated_at:
            raise ValueError("evidence captured_at must not be after generated_at")
        if item.source_event_at > generated_at:
            raise ValueError("evidence source_event_at must not be after generated_at")
    payload_items = _normalize_public_payload(public_payload)
    rows = _build_rows(normalized_evidence, config)
    reason_codes = _report_reason_codes(rows)
    values: dict[str, object] = {
        "generated_at": generated_at,
        "config_version": config.config_version,
        "chain_status": _report_status(rows),
        "claim_count": _decimal_count(len(rows)),
        "pass_count": _decimal_count(_status_count(rows, "pass")),
        "watch_count": _decimal_count(_status_count(rows, "watch")),
        "block_count": _decimal_count(_status_count(rows, "block")),
        "average_integrity_score": _average(
            tuple(row.integrity_score for row in rows),
        ),
        "total_gap_count": _quantize(sum((row.gap_count for row in rows), _ZERO)),
        "rows": rows,
        "reason_codes": reason_codes,
        "public_payload": payload_items,
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    return ResearchEvidenceChainIntegrityReport(
        **values,
        derived_validation_digest=_report_digest_from_values(values),
    )


def _build_rows(
    evidence: tuple[ResearchEvidenceChainEvidence, ...],
    config: ResearchEvidenceChainIntegrityConfig,
) -> tuple[ResearchEvidenceChainIntegrityRow, ...]:
    grouped: dict[tuple[str, str], list[ResearchEvidenceChainEvidence]] = {}
    for item in evidence:
        grouped.setdefault((item.packet_id, item.claim_id), []).append(item)
    return tuple(
        _row_for_group(packet_id, claim_id, tuple(items), config)
        for (packet_id, claim_id), items in sorted(grouped.items())
    )


def _row_for_group(
    packet_id: str,
    claim_id: str,
    evidence: tuple[ResearchEvidenceChainEvidence, ...],
    config: ResearchEvidenceChainIntegrityConfig,
) -> ResearchEvidenceChainIntegrityRow:
    supporting = tuple(item for item in evidence if item.stance == "supporting")
    counterevidence = tuple(item for item in evidence if item.stance == "counterevidence")
    support_family_count = _decimal_count(
        len({item.source_family for item in supporting}),
    )
    chronology_issue_count = _decimal_count(
        sum(1 for item in evidence if item.source_event_at > item.captured_at),
    )
    citation_summary_gap_count = _decimal_count(
        sum(
            1
            for item in evidence
            if _decimal_count(len(item.citation_summary))
            < config.min_citation_summary_characters
        ),
    )
    supporting_source_count = _decimal_count(len(supporting))
    counterevidence_count = _decimal_count(len(counterevidence))
    source_independence_gap_count = _source_independence_gap_count(
        supporting_source_count=supporting_source_count,
        support_family_count=support_family_count,
        config=config,
    )
    counterevidence_gap_count = _counterevidence_gap_count(
        counterevidence_count=counterevidence_count,
        config=config,
    )
    gap_count = _quantize(
        source_independence_gap_count
        + counterevidence_gap_count
        + chronology_issue_count
        + citation_summary_gap_count,
    )
    integrity_score = _clamp_ratio(_ONE - (gap_count * config.gap_penalty))
    reason_codes = _row_reason_codes(
        supporting_source_count=supporting_source_count,
        support_family_count=support_family_count,
        counterevidence_count=counterevidence_count,
        chronology_issue_count=chronology_issue_count,
        citation_summary_gap_count=citation_summary_gap_count,
        config=config,
    )
    return ResearchEvidenceChainIntegrityRow(
        packet_id=packet_id,
        claim_id=claim_id,
        source_count=_decimal_count(len(evidence)),
        supporting_source_count=supporting_source_count,
        independent_support_family_count=support_family_count,
        counterevidence_count=counterevidence_count,
        chronology_issue_count=chronology_issue_count,
        citation_summary_gap_count=citation_summary_gap_count,
        gap_count=gap_count,
        integrity_score=integrity_score,
        chain_status=_row_status(
            supporting_source_count=supporting_source_count,
            support_family_count=support_family_count,
            counterevidence_count=counterevidence_count,
            chronology_issue_count=chronology_issue_count,
            citation_summary_gap_count=citation_summary_gap_count,
            config=config,
        ),
        reason_codes=reason_codes,
    )


def _source_independence_gap_count(
    *,
    supporting_source_count: Decimal,
    support_family_count: Decimal,
    config: ResearchEvidenceChainIntegrityConfig,
) -> Decimal:
    if supporting_source_count == _ZERO:
        return _ONE
    if support_family_count < config.min_independent_support_family_count:
        return _ONE
    return _ZERO


def _counterevidence_gap_count(
    *,
    counterevidence_count: Decimal,
    config: ResearchEvidenceChainIntegrityConfig,
) -> Decimal:
    if counterevidence_count < config.min_counterevidence_count:
        return _ONE
    return _ZERO


def _row_reason_codes(
    *,
    supporting_source_count: Decimal,
    support_family_count: Decimal,
    counterevidence_count: Decimal,
    chronology_issue_count: Decimal,
    citation_summary_gap_count: Decimal,
    config: ResearchEvidenceChainIntegrityConfig,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    if supporting_source_count == _ZERO:
        reason_codes.append("missing_supporting_evidence")
    elif support_family_count < config.min_independent_support_family_count:
        reason_codes.append("insufficient_source_independence")
    if counterevidence_count < config.min_counterevidence_count:
        reason_codes.append("missing_counterevidence")
    if chronology_issue_count > _ZERO:
        reason_codes.append("chronology_issue")
    if citation_summary_gap_count > _ZERO:
        reason_codes.append("citation_summary_gap")
    if not reason_codes:
        reason_codes.append("complete_evidence_chain")
    return _normalize_reason_codes(tuple(reason_codes))


def _row_status(
    *,
    supporting_source_count: Decimal,
    support_family_count: Decimal,
    counterevidence_count: Decimal,
    chronology_issue_count: Decimal,
    citation_summary_gap_count: Decimal,
    config: ResearchEvidenceChainIntegrityConfig,
) -> str:
    if supporting_source_count == _ZERO or chronology_issue_count > _ZERO:
        return "block"
    if (
        support_family_count < config.min_independent_support_family_count
        or counterevidence_count < config.min_counterevidence_count
        or citation_summary_gap_count > _ZERO
    ):
        return "watch"
    return "pass"


def _report_status(rows: tuple[ResearchEvidenceChainIntegrityRow, ...]) -> str:
    if not rows:
        return "block"
    if any(row.chain_status == "block" for row in rows):
        return "block"
    if any(row.chain_status == "watch" for row in rows):
        return "watch"
    return "pass"


def _report_reason_codes(
    rows: tuple[ResearchEvidenceChainIntegrityRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return ("empty_evidence",)
    reason_codes: list[str] = []
    for row in rows:
        reason_codes.extend(row.reason_codes)
    return _normalize_reason_codes(tuple(reason_codes))


def _status_count(rows: tuple[ResearchEvidenceChainIntegrityRow, ...], status: str) -> int:
    return sum(1 for row in rows if row.chain_status == status)


def _validate_row_consistency(row: ResearchEvidenceChainIntegrityRow) -> None:
    if row.supporting_source_count > row.source_count:
        raise ValueError("supporting_source_count must not exceed source_count")
    if row.independent_support_family_count > row.supporting_source_count:
        raise ValueError(
            "independent_support_family_count must not exceed supporting_source_count",
        )
    if row.counterevidence_count > row.source_count:
        raise ValueError("counterevidence_count must not exceed source_count")
    if row.chain_status == "pass" and row.reason_codes != ("complete_evidence_chain",):
        raise ValueError("pass rows must contain only complete_evidence_chain")
    if row.chain_status == "block" and not (
        row.supporting_source_count == _ZERO or row.chronology_issue_count > _ZERO
    ):
        raise ValueError("block rows must have missing support or chronology issues")


def _validate_report_consistency(report: ResearchEvidenceChainIntegrityReport) -> None:
    if report.claim_count != _decimal_count(len(report.rows)):
        raise ValueError("claim_count must match rows")
    if report.pass_count != _decimal_count(_status_count(report.rows, "pass")):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _decimal_count(_status_count(report.rows, "watch")):
        raise ValueError("watch_count must match rows")
    if report.block_count != _decimal_count(_status_count(report.rows, "block")):
        raise ValueError("block_count must match rows")
    if report.average_integrity_score != _average(
        tuple(row.integrity_score for row in report.rows),
    ):
        raise ValueError("average_integrity_score must match rows")
    if report.total_gap_count != _quantize(
        sum((row.gap_count for row in report.rows), _ZERO),
    ):
        raise ValueError("total_gap_count must match rows")
    if report.chain_status != _report_status(report.rows):
        raise ValueError("chain_status must match row statuses")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")


def _normalize_evidence(
    evidence: Sequence[ResearchEvidenceChainEvidence],
) -> tuple[ResearchEvidenceChainEvidence, ...]:
    if isinstance(evidence, (str, bytes)) or not isinstance(evidence, Sequence):
        raise ValueError("evidence must be a sequence")
    normalized: list[ResearchEvidenceChainEvidence] = []
    for item in evidence:
        if type(item) is not ResearchEvidenceChainEvidence:
            raise ValueError("evidence items must be ResearchEvidenceChainEvidence")
        normalized.append(item)
    return tuple(
        sorted(
            normalized,
            key=lambda item: (
                item.packet_id,
                item.claim_id,
                item.source_event_at,
                item.captured_at,
                item.evidence_id,
            ),
        ),
    )


def _normalize_rows(
    rows: Sequence[ResearchEvidenceChainIntegrityRow],
) -> tuple[ResearchEvidenceChainIntegrityRow, ...]:
    if isinstance(rows, (str, bytes)) or not isinstance(rows, Sequence):
        raise ValueError("rows must be a sequence")
    normalized: list[ResearchEvidenceChainIntegrityRow] = []
    for row in rows:
        if type(row) is not ResearchEvidenceChainIntegrityRow:
            raise ValueError("rows must contain ResearchEvidenceChainIntegrityRow")
        normalized.append(row)
    return tuple(sorted(normalized, key=lambda row: (row.packet_id, row.claim_id)))


def _normalize_public_payload(
    public_payload: Sequence[ResearchEvidenceChainPublicPayloadItem],
) -> tuple[ResearchEvidenceChainPublicPayloadItem, ...]:
    if isinstance(public_payload, (str, bytes)) or not isinstance(public_payload, Sequence):
        raise ValueError("public_payload must be a sequence")
    normalized: list[ResearchEvidenceChainPublicPayloadItem] = []
    for item in public_payload:
        if type(item) is not ResearchEvidenceChainPublicPayloadItem:
            raise ValueError(
                "public_payload items must be ResearchEvidenceChainPublicPayloadItem",
            )
        normalized.append(item)
    return tuple(sorted(normalized, key=lambda item: item.key))


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in _PHASE_FLAG_FIELDS:
        if getattr(value, field_name) is not True:
            raise ValueError(f"{field_name} must be True for {label}")


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


def _reject_unsafe_public_string(field_name: str, value: str) -> None:
    lowered = value.lower()
    if "://" in lowered or "?" in lowered or "@" in lowered:
        raise ValueError(f"{field_name} has unsafe public value")
    if any(term in lowered for term in _UNSAFE_PUBLIC_TERMS):
        raise ValueError(f"{field_name} has unsafe public value")


def _require_stance(field_name: str, value: object) -> str:
    if type(value) is not str or value not in _EVIDENCE_STANCES:
        raise ValueError(f"{field_name} must be a known stance")
    return value


def _require_chain_status(field_name: str, value: object) -> str:
    if type(value) is not str or value not in _CHAIN_STATUSES:
        raise ValueError(f"{field_name} must be a known chain status")
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


def _require_positive_count_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_nonnegative_count_decimal(field_name, value)
    if normalized <= _ZERO:
        raise ValueError(f"{field_name} must be positive")
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
    report: ResearchEvidenceChainIntegrityReport,
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
    "DEFAULT_RESEARCH_EVIDENCE_CHAIN_INTEGRITY_CONFIG_VERSION",
    "ResearchEvidenceChainEvidence",
    "ResearchEvidenceChainIntegrityConfig",
    "ResearchEvidenceChainIntegrityReport",
    "ResearchEvidenceChainIntegrityRow",
    "ResearchEvidenceChainPublicPayloadItem",
    "build_research_evidence_chain_integrity_report",
)
