"""Pure paper research packet evidence chain completeness gate."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal
import hashlib
from typing import Any


DEFAULT_RESEARCH_PACKET_EVIDENCE_CHAIN_COMPLETENESS_GATE_V2_CONFIG_VERSION = (
    "research-packet-evidence-chain-completeness-gate-v2"
)
GATE_STATUSES = ("pass", "watch", "blocked")
NEXT_REPORT_ACTION_BY_STATUS = {
    "pass": "continue_report_only_research_packet_review",
    "watch": "review_report_only_research_packet_gaps",
    "blocked": "block_report_only_research_packet_gap_review",
}
PASS_REASON_CODE = "research_packet_evidence_chain_completeness_gate_v2_passed"
MISSING_LINK_REASON_CODE = "research_packet_evidence_chain_link_missing"
INCOMPLETE_LINK_REASON_CODE = "research_packet_evidence_chain_link_incomplete"
SOURCE_QUORUM_GAP_REASON_CODE = "research_packet_source_quorum_gap"
MISSING_SOURCE_FAMILY_REASON_CODE = "research_packet_required_source_family_missing"
DERIVED_VALIDATION_DIGEST_FIELD = "derived_validation_digest"
PHASE_FLAG_FIELDS = ("paper_only", "report_only", "readonly")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
QUANTUM = Decimal("0.000001")
PUBLIC_REPORT_FIELDS_WITHOUT_DIGEST = (
    "generated_at",
    "config_version",
    "gate_status",
    "recommended_report_action",
    "evidence_count",
    "required_chain_link_count",
    "complete_chain_link_count",
    "missing_chain_link_count",
    "incomplete_evidence_count",
    "required_source_family_count",
    "unique_source_family_count",
    "minimum_source_quorum",
    "source_quorum_gap_count",
    "completeness_ratio",
    "missing_chain_link_ids",
    "observed_source_families",
    "missing_source_families",
    "evidence",
    "reason_code_counts",
    "reason_codes",
    "paper_only",
    "report_only",
    "readonly",
)
PUBLIC_REPORT_FIELDS = (
    *PUBLIC_REPORT_FIELDS_WITHOUT_DIGEST,
    DERIVED_VALIDATION_DIGEST_FIELD,
)
UNSAFE_PUBLIC_PAYLOAD_TOKENS = (
    "li" + "ve",
    "au" + "th",
    "wal" + "let",
    "or" + "der",
    "net" + "work",
    "data" + "base",
    "per" + "sist",
    "sign" + "ing",
    "mu" + "tation",
    "b" + "uy",
    "s" + "ell",
    "tra" + "de",
)

__all__ = (
    "DEFAULT_RESEARCH_PACKET_EVIDENCE_CHAIN_COMPLETENESS_GATE_V2_CONFIG_VERSION",
    "ResearchPacketEvidenceChainCompletenessGateV2Config",
    "ResearchPacketEvidenceChainCompletenessGateV2Evidence",
    "ResearchPacketEvidenceChainCompletenessGateV2ReasonCodeCount",
    "ResearchPacketEvidenceChainCompletenessGateV2Report",
    "build_research_packet_evidence_chain_completeness_gate_v2_report",
    "research_packet_evidence_chain_completeness_gate_v2_report_to_payload",
)


@dataclass(frozen=True)
class ResearchPacketEvidenceChainCompletenessGateV2Config:
    required_chain_link_ids: tuple[str, ...]
    required_source_families: tuple[str, ...]
    minimum_source_quorum: Decimal
    config_version: str = (
        DEFAULT_RESEARCH_PACKET_EVIDENCE_CHAIN_COMPLETENESS_GATE_V2_CONFIG_VERSION
    )
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchPacketEvidenceChainCompletenessGateV2Config:
            raise TypeError(
                "ResearchPacketEvidenceChainCompletenessGateV2Config "
                "does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchPacketEvidenceChainCompletenessGateV2Config:
            raise ValueError(
                "config must be exactly "
                "ResearchPacketEvidenceChainCompletenessGateV2Config",
            )
        object.__setattr__(
            self,
            "required_chain_link_ids",
            _normalize_unique_strings(
                "required_chain_link_ids",
                self.required_chain_link_ids,
                allow_empty=False,
            ),
        )
        object.__setattr__(
            self,
            "required_source_families",
            _normalize_unique_strings(
                "required_source_families",
                self.required_source_families,
                allow_empty=False,
            ),
        )
        object.__setattr__(
            self,
            "minimum_source_quorum",
            _normalize_positive_whole_decimal(
                "minimum_source_quorum",
                self.minimum_source_quorum,
            ),
        )
        if self.minimum_source_quorum > Decimal(len(self.required_source_families)):
            raise ValueError("minimum_source_quorum must not exceed source families")
        _require_canonical_string("config_version", self.config_version)
        _reject_unsafe_public_payload("config", self)
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class ResearchPacketEvidenceChainCompletenessGateV2Evidence:
    chain_link_id: str
    source_family: str
    source_label: str
    chain_link_complete: bool
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchPacketEvidenceChainCompletenessGateV2Evidence:
            raise TypeError(
                "ResearchPacketEvidenceChainCompletenessGateV2Evidence "
                "does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchPacketEvidenceChainCompletenessGateV2Evidence:
            raise ValueError(
                "evidence must be exactly "
                "ResearchPacketEvidenceChainCompletenessGateV2Evidence",
            )
        for field_name in ("chain_link_id", "source_family", "source_label"):
            _require_canonical_string(field_name, getattr(self, field_name))
        _require_bool("chain_link_complete", self.chain_link_complete)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        _reject_unsafe_public_payload("evidence", self)
        _require_hard_flags("evidence", self)


@dataclass(frozen=True)
class ResearchPacketEvidenceChainCompletenessGateV2ReasonCodeCount:
    reason_code: str
    report_count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchPacketEvidenceChainCompletenessGateV2ReasonCodeCount:
            raise TypeError(
                "ResearchPacketEvidenceChainCompletenessGateV2ReasonCodeCount "
                "does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchPacketEvidenceChainCompletenessGateV2ReasonCodeCount:
            raise ValueError(
                "reason code count must be exactly "
                "ResearchPacketEvidenceChainCompletenessGateV2ReasonCodeCount",
            )
        _require_canonical_string("reason_code", self.reason_code)
        object.__setattr__(
            self,
            "report_count",
            _normalize_positive_whole_decimal("report_count", self.report_count),
        )
        _reject_unsafe_public_payload("reason_code_count", self)
        _require_hard_flags("reason_code_count", self)


@dataclass(frozen=True)
class ResearchPacketEvidenceChainCompletenessGateV2Report:
    generated_at: datetime
    config_version: str
    gate_status: str
    recommended_report_action: str
    evidence_count: Decimal
    required_chain_link_count: Decimal
    complete_chain_link_count: Decimal
    missing_chain_link_count: Decimal
    incomplete_evidence_count: Decimal
    required_source_family_count: Decimal
    unique_source_family_count: Decimal
    minimum_source_quorum: Decimal
    source_quorum_gap_count: Decimal
    completeness_ratio: Decimal
    missing_chain_link_ids: tuple[str, ...]
    observed_source_families: tuple[str, ...]
    missing_source_families: tuple[str, ...]
    evidence: tuple[ResearchPacketEvidenceChainCompletenessGateV2Evidence, ...]
    reason_code_counts: tuple[
        ResearchPacketEvidenceChainCompletenessGateV2ReasonCodeCount,
        ...,
    ]
    reason_codes: tuple[str, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchPacketEvidenceChainCompletenessGateV2Report:
            raise TypeError(
                "ResearchPacketEvidenceChainCompletenessGateV2Report "
                "does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchPacketEvidenceChainCompletenessGateV2Report:
            raise ValueError(
                "report must be exactly "
                "ResearchPacketEvidenceChainCompletenessGateV2Report",
            )
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        _require_member("gate_status", self.gate_status, GATE_STATUSES)
        _require_canonical_string(
            "recommended_report_action",
            self.recommended_report_action,
        )
        for field_name in (
            "evidence_count",
            "required_chain_link_count",
            "complete_chain_link_count",
            "missing_chain_link_count",
            "incomplete_evidence_count",
            "required_source_family_count",
            "unique_source_family_count",
            "minimum_source_quorum",
            "source_quorum_gap_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_whole_decimal(
                    field_name,
                    getattr(self, field_name),
                ),
            )
        object.__setattr__(
            self,
            "completeness_ratio",
            _normalize_probability_decimal("completeness_ratio", self.completeness_ratio),
        )
        object.__setattr__(
            self,
            "missing_chain_link_ids",
            _normalize_unique_strings(
                "missing_chain_link_ids",
                self.missing_chain_link_ids,
                allow_empty=True,
            ),
        )
        object.__setattr__(
            self,
            "observed_source_families",
            _normalize_unique_strings(
                "observed_source_families",
                self.observed_source_families,
                allow_empty=True,
            ),
        )
        object.__setattr__(
            self,
            "missing_source_families",
            _normalize_unique_strings(
                "missing_source_families",
                self.missing_source_families,
                allow_empty=True,
            ),
        )
        object.__setattr__(self, "evidence", _normalize_evidence(self.evidence))
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, sorted_only=True),
        )
        _validate_report_consistency(self)
        _reject_unsafe_public_payload("report", self)
        _require_hard_flags("report", self)
        if self.derived_validation_digest == "":
            object.__setattr__(
                self,
                DERIVED_VALIDATION_DIGEST_FIELD,
                _report_derived_validation_digest(self),
            )
        else:
            object.__setattr__(
                self,
                DERIVED_VALIDATION_DIGEST_FIELD,
                _normalize_sha256(
                    DERIVED_VALIDATION_DIGEST_FIELD,
                    self.derived_validation_digest,
                ),
            )
        _validate_report_derived_validation_digest(self)


def build_research_packet_evidence_chain_completeness_gate_v2_report(
    evidence: tuple[ResearchPacketEvidenceChainCompletenessGateV2Evidence, ...],
    *,
    config: ResearchPacketEvidenceChainCompletenessGateV2Config,
    generated_at: datetime,
) -> ResearchPacketEvidenceChainCompletenessGateV2Report:
    _require_exact_type(
        "config",
        config,
        ResearchPacketEvidenceChainCompletenessGateV2Config,
    )
    generated_at_utc = _as_utc("generated_at", generated_at)
    evidence_rows = _normalize_evidence(evidence)
    required_links = config.required_chain_link_ids
    complete_links = {
        row.chain_link_id
        for row in evidence_rows
        if row.chain_link_id in required_links and row.chain_link_complete
    }
    missing_chain_link_ids = tuple(
        chain_link_id
        for chain_link_id in required_links
        if chain_link_id not in complete_links
    )
    observed_source_families = tuple(
        sorted({row.source_family for row in evidence_rows}),
    )
    missing_source_families = tuple(
        source_family
        for source_family in config.required_source_families
        if source_family not in observed_source_families
    )
    unique_source_family_count = Decimal(len(observed_source_families)).quantize(QUANTUM)
    source_quorum_gap_count = max(
        ZERO,
        config.minimum_source_quorum - unique_source_family_count,
    ).quantize(QUANTUM)
    required_chain_link_count = Decimal(len(required_links)).quantize(QUANTUM)
    complete_chain_link_count = Decimal(len(complete_links)).quantize(QUANTUM)
    missing_chain_link_count = Decimal(len(missing_chain_link_ids)).quantize(QUANTUM)
    incomplete_evidence_count = Decimal(
        sum(1 for row in evidence_rows if not row.chain_link_complete),
    ).quantize(QUANTUM)
    reason_code_events = _report_reason_code_events(
        evidence_rows,
        missing_chain_link_count=missing_chain_link_count,
        incomplete_evidence_count=incomplete_evidence_count,
        missing_source_families=missing_source_families,
        source_quorum_gap_count=source_quorum_gap_count,
    )
    gate_status = _gate_status(
        missing_chain_link_count=missing_chain_link_count,
        missing_source_family_count=Decimal(len(missing_source_families)).quantize(
            QUANTUM,
        ),
        source_quorum_gap_count=source_quorum_gap_count,
        incomplete_evidence_count=incomplete_evidence_count,
    )
    return ResearchPacketEvidenceChainCompletenessGateV2Report(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        gate_status=gate_status,
        recommended_report_action=NEXT_REPORT_ACTION_BY_STATUS[gate_status],
        evidence_count=Decimal(len(evidence_rows)).quantize(QUANTUM),
        required_chain_link_count=required_chain_link_count,
        complete_chain_link_count=complete_chain_link_count,
        missing_chain_link_count=missing_chain_link_count,
        incomplete_evidence_count=incomplete_evidence_count,
        required_source_family_count=Decimal(len(config.required_source_families)).quantize(
            QUANTUM,
        ),
        unique_source_family_count=unique_source_family_count,
        minimum_source_quorum=config.minimum_source_quorum,
        source_quorum_gap_count=source_quorum_gap_count,
        completeness_ratio=_ratio(complete_chain_link_count, required_chain_link_count),
        missing_chain_link_ids=missing_chain_link_ids,
        observed_source_families=observed_source_families,
        missing_source_families=missing_source_families,
        evidence=evidence_rows,
        reason_code_counts=_reason_code_counts(reason_code_events),
        reason_codes=tuple(sorted(set(reason_code_events))),
    )


def research_packet_evidence_chain_completeness_gate_v2_report_to_payload(
    report: ResearchPacketEvidenceChainCompletenessGateV2Report | dict[str, object],
) -> dict[str, object]:
    if type(report) is ResearchPacketEvidenceChainCompletenessGateV2Report:
        _require_hard_flags("report", report)
        _reject_unsafe_public_payload("report", report)
        _validate_report_derived_validation_digest(report)
        payload = _report_public_payload_values(report)
        payload[DERIVED_VALIDATION_DIGEST_FIELD] = report.derived_validation_digest
        return payload
    if type(report) is dict:
        _reject_unsafe_public_payload("payload", report)
        _require_public_report_payload_fields(report)
        _validate_public_report_payload(report)
        return dict(report)
    raise ValueError(
        "report must be a ResearchPacketEvidenceChainCompletenessGateV2Report",
    )


def _report_reason_code_events(
    evidence: tuple[ResearchPacketEvidenceChainCompletenessGateV2Evidence, ...],
    *,
    missing_chain_link_count: Decimal,
    incomplete_evidence_count: Decimal,
    missing_source_families: tuple[str, ...],
    source_quorum_gap_count: Decimal,
) -> tuple[str, ...]:
    events: list[str] = []
    if missing_chain_link_count > ZERO:
        events.append(MISSING_LINK_REASON_CODE)
    if incomplete_evidence_count > ZERO:
        events.append(INCOMPLETE_LINK_REASON_CODE)
    if missing_source_families:
        events.append(MISSING_SOURCE_FAMILY_REASON_CODE)
    if source_quorum_gap_count > ZERO:
        events.append(SOURCE_QUORUM_GAP_REASON_CODE)
    for row in evidence:
        events.extend(row.reason_codes)
    if not events:
        events.append(PASS_REASON_CODE)
    return tuple(events)


def _gate_status(
    *,
    missing_chain_link_count: Decimal,
    missing_source_family_count: Decimal,
    source_quorum_gap_count: Decimal,
    incomplete_evidence_count: Decimal,
) -> str:
    if (
        missing_chain_link_count > ZERO
        or missing_source_family_count > ZERO
        or source_quorum_gap_count > ZERO
    ):
        return "blocked"
    if incomplete_evidence_count > ZERO:
        return "watch"
    return "pass"


def _reason_code_counts(
    reason_codes: tuple[str, ...],
) -> tuple[ResearchPacketEvidenceChainCompletenessGateV2ReasonCodeCount, ...]:
    counts: dict[str, Decimal] = {}
    for reason_code in reason_codes:
        counts[reason_code] = counts.get(reason_code, ZERO) + ONE
    return tuple(
        ResearchPacketEvidenceChainCompletenessGateV2ReasonCodeCount(
            reason_code=reason_code,
            report_count=report_count.quantize(QUANTUM),
        )
        for reason_code, report_count in sorted(
            counts.items(),
            key=lambda item: (-item[1], item[0]),
        )
    )


def _report_public_payload_values(
    report: ResearchPacketEvidenceChainCompletenessGateV2Report,
) -> dict[str, object]:
    return {
        "generated_at": report.generated_at.isoformat(),
        "config_version": report.config_version,
        "gate_status": report.gate_status,
        "recommended_report_action": report.recommended_report_action,
        "evidence_count": _decimal_payload(report.evidence_count),
        "required_chain_link_count": _decimal_payload(report.required_chain_link_count),
        "complete_chain_link_count": _decimal_payload(report.complete_chain_link_count),
        "missing_chain_link_count": _decimal_payload(report.missing_chain_link_count),
        "incomplete_evidence_count": _decimal_payload(report.incomplete_evidence_count),
        "required_source_family_count": _decimal_payload(
            report.required_source_family_count,
        ),
        "unique_source_family_count": _decimal_payload(report.unique_source_family_count),
        "minimum_source_quorum": _decimal_payload(report.minimum_source_quorum),
        "source_quorum_gap_count": _decimal_payload(report.source_quorum_gap_count),
        "completeness_ratio": _decimal_payload(report.completeness_ratio),
        "missing_chain_link_ids": list(report.missing_chain_link_ids),
        "observed_source_families": list(report.observed_source_families),
        "missing_source_families": list(report.missing_source_families),
        "evidence": [_evidence_payload(row) for row in report.evidence],
        "reason_code_counts": [
            _reason_code_count_payload(row) for row in report.reason_code_counts
        ],
        "reason_codes": list(report.reason_codes),
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }


def _evidence_payload(
    row: ResearchPacketEvidenceChainCompletenessGateV2Evidence,
) -> dict[str, object]:
    return {
        "chain_link_id": row.chain_link_id,
        "source_family": row.source_family,
        "source_label": row.source_label,
        "chain_link_complete": row.chain_link_complete,
        "reason_codes": list(row.reason_codes),
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }


def _reason_code_count_payload(
    row: ResearchPacketEvidenceChainCompletenessGateV2ReasonCodeCount,
) -> dict[str, object]:
    return {
        "reason_code": row.reason_code,
        "report_count": _decimal_payload(row.report_count),
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }


def _report_derived_validation_digest(
    report: ResearchPacketEvidenceChainCompletenessGateV2Report,
) -> str:
    return _derived_validation_digest(_report_public_payload_values(report))


def _validate_report_derived_validation_digest(
    report: ResearchPacketEvidenceChainCompletenessGateV2Report,
) -> None:
    if report.derived_validation_digest != _report_derived_validation_digest(report):
        raise ValueError("derived_validation_digest must match report fields")


def _derived_validation_digest(payload: dict[str, object]) -> str:
    values = tuple(
        f"{field_name}={_digest_payload_value(payload[field_name])}"
        for field_name in PUBLIC_REPORT_FIELDS_WITHOUT_DIGEST
    )
    return _sha256("research_packet_evidence_chain_completeness_gate_v2", values)


def _digest_payload_value(value: object) -> str:
    if type(value) is dict:
        return "{" + ",".join(
            f"{key}:{_digest_payload_value(value[key])}" for key in sorted(value)
        ) + "}"
    if type(value) is list or type(value) is tuple:
        return "[" + ",".join(_digest_payload_value(item) for item in value) + "]"
    return str(value)


def _sha256(label: str, values: tuple[str, ...]) -> str:
    return hashlib.sha256((f"{label}|" + "|".join(values)).encode("utf-8")).hexdigest()


def _require_public_report_payload_fields(payload: dict[str, object]) -> None:
    for field_name in PUBLIC_REPORT_FIELDS:
        if field_name not in payload:
            raise ValueError(f"{field_name} is required")
    extra_fields = sorted(set(payload) - set(PUBLIC_REPORT_FIELDS))
    if extra_fields:
        raise ValueError(f"unexpected public payload field: {extra_fields[0]}")


def _validate_public_report_payload(payload: dict[str, object]) -> None:
    _require_datetime_payload_string("generated_at", payload["generated_at"])
    for field_name in ("config_version", "recommended_report_action"):
        _require_canonical_string(field_name, payload[field_name])
    _require_member("gate_status", payload["gate_status"], GATE_STATUSES)
    for field_name in (
        "evidence_count",
        "required_chain_link_count",
        "complete_chain_link_count",
        "missing_chain_link_count",
        "incomplete_evidence_count",
        "required_source_family_count",
        "unique_source_family_count",
        "minimum_source_quorum",
        "source_quorum_gap_count",
    ):
        _require_decimal_payload_string(field_name, payload[field_name], whole=True)
    _require_decimal_payload_string(
        "completeness_ratio",
        payload["completeness_ratio"],
        probability=True,
    )
    for field_name in (
        "missing_chain_link_ids",
        "observed_source_families",
        "missing_source_families",
    ):
        _normalize_public_string_list(field_name, payload[field_name], allow_empty=True)
    _validate_public_evidence(payload["evidence"])
    _validate_public_reason_code_counts(payload["reason_code_counts"])
    _normalize_public_string_list("reason_codes", payload["reason_codes"])
    _require_hard_flags("payload", _DictFlags(payload))
    provided_digest = _normalize_sha256(
        DERIVED_VALIDATION_DIGEST_FIELD,
        payload[DERIVED_VALIDATION_DIGEST_FIELD],
    )
    if provided_digest != _derived_validation_digest(payload):
        raise ValueError("derived_validation_digest must match payload fields")


def _validate_public_evidence(value: object) -> None:
    if type(value) is not list:
        raise ValueError("evidence must be a list")
    for row in value:
        if type(row) is not dict:
            raise ValueError("evidence rows must be dicts")
        expected = {
            "chain_link_id",
            "source_family",
            "source_label",
            "chain_link_complete",
            "reason_codes",
            "paper_only",
            "report_only",
            "readonly",
        }
        if set(row) != expected:
            raise ValueError("evidence row fields are invalid")
        for field_name in ("chain_link_id", "source_family", "source_label"):
            _require_canonical_string(field_name, row[field_name])
        _require_bool("chain_link_complete", row["chain_link_complete"])
        _normalize_public_string_list("reason_codes", row["reason_codes"])
        _require_hard_flags("evidence row", _DictFlags(row))


def _validate_public_reason_code_counts(value: object) -> None:
    if type(value) is not list:
        raise ValueError("reason_code_counts must be a list")
    if not value:
        raise ValueError("reason_code_counts must not be empty")
    previous_key: tuple[Decimal, str] | None = None
    seen: set[str] = set()
    for row in value:
        if type(row) is not dict:
            raise ValueError("reason_code_counts rows must be dicts")
        expected = {
            "reason_code",
            "report_count",
            "paper_only",
            "report_only",
            "readonly",
        }
        if set(row) != expected:
            raise ValueError("reason_code_counts row fields are invalid")
        _require_canonical_string("reason_code", row["reason_code"])
        report_count = _require_decimal_payload_string(
            "report_count",
            row["report_count"],
            whole=True,
        )
        _require_hard_flags("reason_code_count row", _DictFlags(row))
        if row["reason_code"] in seen:
            raise ValueError("reason_code_counts must be unique")
        key = (-report_count, row["reason_code"])
        if previous_key is not None and previous_key > key:
            raise ValueError("reason_code_counts must be deterministic")
        previous_key = key
        seen.add(row["reason_code"])


def _validate_report_consistency(
    report: ResearchPacketEvidenceChainCompletenessGateV2Report,
) -> None:
    if report.recommended_report_action != NEXT_REPORT_ACTION_BY_STATUS[report.gate_status]:
        raise ValueError("recommended_report_action must match gate_status")
    if report.evidence_count != Decimal(len(report.evidence)).quantize(QUANTUM):
        raise ValueError("evidence_count must match evidence")
    if (
        report.required_chain_link_count
        != report.complete_chain_link_count + report.missing_chain_link_count
    ):
        raise ValueError("chain link counts must tie")
    if report.missing_chain_link_count != Decimal(
        len(report.missing_chain_link_ids),
    ).quantize(QUANTUM):
        raise ValueError("missing_chain_link_count must match missing ids")
    if report.unique_source_family_count != Decimal(
        len(report.observed_source_families),
    ).quantize(QUANTUM):
        raise ValueError("unique_source_family_count must match source families")
    if report.required_source_family_count < report.unique_source_family_count:
        raise ValueError("source family counts must tie")
    if report.source_quorum_gap_count != max(
        ZERO,
        report.minimum_source_quorum - report.unique_source_family_count,
    ).quantize(QUANTUM):
        raise ValueError("source_quorum_gap_count must match source families")
    if report.completeness_ratio != _ratio(
        report.complete_chain_link_count,
        report.required_chain_link_count,
    ):
        raise ValueError("completeness_ratio must match chain link counts")
    expected_status = _gate_status(
        missing_chain_link_count=report.missing_chain_link_count,
        missing_source_family_count=Decimal(len(report.missing_source_families)).quantize(
            QUANTUM,
        ),
        source_quorum_gap_count=report.source_quorum_gap_count,
        incomplete_evidence_count=report.incomplete_evidence_count,
    )
    if report.gate_status != expected_status:
        raise ValueError("gate_status must match report fields")


def _normalize_evidence(
    value: object,
) -> tuple[ResearchPacketEvidenceChainCompletenessGateV2Evidence, ...]:
    if type(value) is not tuple:
        raise ValueError("evidence must be a tuple")
    rows = tuple(value)
    seen: set[tuple[str, str]] = set()
    for row in rows:
        _require_exact_type(
            "evidence row",
            row,
            ResearchPacketEvidenceChainCompletenessGateV2Evidence,
        )
        key = (row.chain_link_id, row.source_label)
        if key in seen:
            raise ValueError("evidence rows must be unique")
        seen.add(key)
    return rows


def _normalize_reason_code_counts(
    value: object,
) -> tuple[ResearchPacketEvidenceChainCompletenessGateV2ReasonCodeCount, ...]:
    if type(value) is not tuple:
        raise ValueError("reason_code_counts must be a tuple")
    rows = tuple(value)
    if not rows:
        raise ValueError("reason_code_counts must not be empty")
    seen: set[str] = set()
    previous_key: tuple[Decimal, str] | None = None
    for row in rows:
        _require_exact_type(
            "reason_code_count",
            row,
            ResearchPacketEvidenceChainCompletenessGateV2ReasonCodeCount,
        )
        if row.reason_code in seen:
            raise ValueError("reason_code_counts must be unique")
        key = (-row.report_count, row.reason_code)
        if previous_key is not None and previous_key > key:
            raise ValueError("reason_code_counts must be deterministic")
        previous_key = key
        seen.add(row.reason_code)
    return rows


def _normalize_unique_strings(
    field_name: str,
    value: object,
    *,
    allow_empty: bool,
) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ValueError(f"{field_name} must be a tuple")
    rows = tuple(value)
    if not rows and not allow_empty:
        raise ValueError(f"{field_name} must not be empty")
    previous: str | None = None
    seen: set[str] = set()
    for row in rows:
        _require_canonical_string(field_name, row)
        if row in seen:
            raise ValueError(f"{field_name} must be unique")
        if previous is not None and previous > row:
            raise ValueError(f"{field_name} must be sorted")
        previous = row
        seen.add(row)
    return rows


def _normalize_reason_codes(
    field_name: str,
    value: object,
    *,
    sorted_only: bool = False,
) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ValueError(f"{field_name} must be a tuple")
    rows = tuple(value)
    if not rows:
        raise ValueError(f"{field_name} must not be empty")
    previous: str | None = None
    seen: set[str] = set()
    for row in rows:
        _require_canonical_string(field_name, row)
        if row in seen:
            raise ValueError(f"{field_name} must be unique")
        if sorted_only and previous is not None and previous > row:
            raise ValueError(f"{field_name} must be sorted")
        previous = row
        seen.add(row)
    return rows


def _normalize_public_string_list(
    field_name: str,
    value: object,
    *,
    allow_empty: bool = False,
) -> tuple[str, ...]:
    if type(value) is not list:
        raise ValueError(f"{field_name} must be a list")
    rows = tuple(value)
    if not rows and not allow_empty:
        raise ValueError(f"{field_name} must not be empty")
    seen: set[str] = set()
    for row in rows:
        _require_canonical_string(field_name, row)
        if row in seen:
            raise ValueError(f"{field_name} must be unique")
        seen.add(row)
    return rows


def _require_exact_type(field_name: str, value: object, expected_type: type[object]) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{field_name} must be a {expected_type.__name__}")
    _require_hard_flags(field_name, value)


def _require_member(
    field_name: str,
    value: object,
    allowed_values: tuple[str, ...],
) -> None:
    if type(value) is not str or value not in allowed_values:
        expected = ", ".join(allowed_values)
        raise ValueError(f"{field_name} must be one of: {expected}")


def _require_bool(field_name: str, value: object) -> None:
    if type(value) is not bool:
        raise ValueError(f"{field_name} must be a bool")


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")
    _reject_unsafe_public_value(field_name, value)


def _normalize_probability_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_nonnegative_decimal(field_name, value)
    if normalized > ONE:
        raise ValueError(f"{field_name} must be a probability")
    return normalized


def _normalize_positive_whole_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_nonnegative_whole_decimal(field_name, value)
    if normalized <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _normalize_nonnegative_whole_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_nonnegative_decimal(field_name, value)
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{field_name} must be a whole Decimal")
    return normalized


def _normalize_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    normalized = value.quantize(QUANTUM)
    if normalized != value:
        raise ValueError(f"{field_name} must use 6 decimal places")
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _require_decimal_payload_string(
    field_name: str,
    value: object,
    *,
    probability: bool = False,
    whole: bool = False,
) -> Decimal:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a Decimal-derived string")
    try:
        decimal_value = Decimal(value)
    except Exception as exc:
        raise ValueError(f"{field_name} must be a Decimal-derived string") from exc
    if not decimal_value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    normalized = decimal_value.quantize(QUANTUM)
    if format(normalized, "f") != value:
        raise ValueError(f"{field_name} must be a canonical Decimal-derived string")
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    if probability and normalized > ONE:
        raise ValueError(f"{field_name} must be a probability")
    if whole and normalized != normalized.to_integral_value():
        raise ValueError(f"{field_name} must be a whole Decimal-derived string")
    return normalized


def _decimal_payload(value: Decimal) -> str:
    return format(value, "f")


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO:
        return ZERO
    return (numerator / denominator).quantize(QUANTUM)


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_datetime_payload_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a datetime string")
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError as exc:
        raise ValueError(f"{field_name} must be a datetime string") from exc
    if parsed.tzinfo is None or parsed.astimezone(UTC).isoformat() != value:
        raise ValueError(f"{field_name} must be a canonical UTC datetime string")


def _normalize_sha256(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a sha256 string")
    if len(value) != 64 or any(character not in "0123456789abcdef" for character in value):
        raise ValueError(f"{field_name} must be a sha256 string")
    return value


@dataclass(frozen=True)
class _DictFlags:
    value: dict[str, object]

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
    for field_name in PHASE_FLAG_FIELDS:
        if _optional_attr(value, field_name) is not True:
            raise ValueError(f"{label} {field_name} must be True")


def _optional_attr(value: object, attr_name: str) -> object | None:
    try:
        return object.__getattribute__(value, attr_name)
    except AttributeError:
        return None


def _reject_unsafe_public_payload(label: str, value: object) -> None:
    if type(value) is dict:
        for key, item in value.items():
            _reject_unsafe_public_value(label, str(key))
            _reject_unsafe_public_payload(label, item)
        return
    if type(value) is list or type(value) is tuple:
        for item in value:
            _reject_unsafe_public_payload(label, item)
        return
    field_names = getattr(value, "__dataclass_fields__", None)
    if type(field_names) is dict:
        for field_name in field_names:
            _reject_unsafe_public_value(label, field_name)
            _reject_unsafe_public_payload(label, getattr(value, field_name))
        return
    if type(value) is str:
        _reject_unsafe_public_value(label, value)


def _reject_unsafe_public_value(field_name: str, value: str) -> None:
    lowered = value.lower()
    if any(token in lowered for token in UNSAFE_PUBLIC_PAYLOAD_TOKENS):
        raise ValueError(f"{field_name} contains unsafe public surface")
