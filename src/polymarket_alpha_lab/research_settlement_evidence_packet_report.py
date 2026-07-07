"""Report-only settlement evidence packet for near-resolution events."""

from __future__ import annotations

from dataclasses import asdict, dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal, ROUND_HALF_UP
import hashlib
import json
import re
from typing import Any, Mapping, Sequence


DEFAULT_RESEARCH_SETTLEMENT_EVIDENCE_PACKET_CONFIG_VERSION = (
    "research-settlement-evidence-packet-report-v1"
)

_QUANT = Decimal("0.000001")
_ZERO = Decimal("0.000000")
_ONE = Decimal("1.000000")
_PUBLIC_IDENTIFIER_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,127}$")
_DIGEST_RE = re.compile(r"^[0-9a-f]{64}$")
_PACKET_STATUSES = frozenset(("pass", "watch", "block"))
_EVIDENCE_TYPES = frozenset(
    (
        "official_result",
        "resolution_rule",
        "settlement_time",
        "source_confirmation",
        "other_public",
    ),
)
_MAPPING_STATUSES = frozenset(("mapped", "partial", "unmapped"))
_REVIEW_STATUSES = frozenset(("approved", "needs_review", "not_reviewed"))
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
    "advice",
    "recommendation",
)
_REASON_CODE_SEQUENCE = (
    "empty_packets",
    "evidence_incomplete",
    "evidence_conflict_watch",
    "source_independence_watch",
    "source_independence_pass",
    "rule_mapping_missing",
    "rule_mapping_partial",
    "unresolved_ambiguity_watch",
    "unresolved_ambiguity_block",
    "review_pending",
    "review_approved",
    "settlement_window_watch",
    "settlement_window_block",
    "settlement_evidence_packet_pass",
)


@dataclass(frozen=True)
class ResearchSettlementEvidencePacketConfig:
    config_version: str = DEFAULT_RESEARCH_SETTLEMENT_EVIDENCE_PACKET_CONFIG_VERSION
    required_evidence_types: tuple[str, ...] = (
        "official_result",
        "resolution_rule",
        "settlement_time",
    )
    min_source_family_count: Decimal = Decimal("2.000000")
    min_rule_mapping_score: Decimal = Decimal("1.000000")
    high_ambiguity_severity: Decimal = Decimal("0.800000")
    settlement_watch_hours: Decimal = Decimal("1.000000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchSettlementEvidencePacketConfig:
            raise TypeError(
                "ResearchSettlementEvidencePacketConfig does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchSettlementEvidencePacketConfig:
            raise ValueError(
                "config must be exactly ResearchSettlementEvidencePacketConfig",
            )
        _require_public_identifier("config_version", self.config_version)
        if self.config_version != DEFAULT_RESEARCH_SETTLEMENT_EVIDENCE_PACKET_CONFIG_VERSION:
            raise ValueError("config_version must be the supported config version")
        object.__setattr__(
            self,
            "required_evidence_types",
            _normalize_evidence_types(self.required_evidence_types),
        )
        object.__setattr__(
            self,
            "min_source_family_count",
            _require_positive_count_decimal(
                "min_source_family_count",
                self.min_source_family_count,
            ),
        )
        for field_name in ("min_rule_mapping_score", "high_ambiguity_severity"):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "settlement_watch_hours",
            _require_nonnegative_decimal(
                "settlement_watch_hours",
                self.settlement_watch_hours,
            ),
        )
        _require_hard_flags("config", self)
        _reject_unsafe_public_payload("config", self)


@dataclass(frozen=True)
class ResearchSettlementEvidenceItem:
    packet_id: str
    event_id: str
    evidence_id: str
    evidence_type: str
    source_id: str
    source_family: str
    observed_at: datetime
    relevance_score: Decimal
    supports_resolution: bool = True
    public_note: str | None = None
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchSettlementEvidenceItem:
            raise TypeError("ResearchSettlementEvidenceItem does not support subclassing")

    def __post_init__(self) -> None:
        if type(self) is not ResearchSettlementEvidenceItem:
            raise ValueError("evidence must be exactly ResearchSettlementEvidenceItem")
        for field_name in (
            "packet_id",
            "event_id",
            "evidence_id",
            "source_id",
            "source_family",
        ):
            _require_public_identifier(field_name, getattr(self, field_name))
        _require_member("evidence_type", self.evidence_type, _EVIDENCE_TYPES)
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        object.__setattr__(
            self,
            "relevance_score",
            _require_ratio_decimal("relevance_score", self.relevance_score),
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
class ResearchSettlementRuleMapping:
    packet_id: str
    event_id: str
    rule_id: str
    evidence_id: str
    mapping_status: str
    public_note: str | None = None
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchSettlementRuleMapping:
            raise TypeError("ResearchSettlementRuleMapping does not support subclassing")

    def __post_init__(self) -> None:
        if type(self) is not ResearchSettlementRuleMapping:
            raise ValueError("rule mapping must be exactly ResearchSettlementRuleMapping")
        for field_name in ("packet_id", "event_id", "rule_id", "evidence_id"):
            _require_public_identifier(field_name, getattr(self, field_name))
        _require_member("mapping_status", self.mapping_status, _MAPPING_STATUSES)
        object.__setattr__(
            self,
            "public_note",
            _normalize_optional_public_text("public_note", self.public_note),
        )
        _require_hard_flags("rule mapping", self)
        _reject_unsafe_public_payload("rule mapping", self)


@dataclass(frozen=True)
class ResearchSettlementAmbiguityPoint:
    packet_id: str
    event_id: str
    ambiguity_id: str
    severity_score: Decimal
    resolved: bool
    public_note: str | None = None
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchSettlementAmbiguityPoint:
            raise TypeError("ResearchSettlementAmbiguityPoint does not support subclassing")

    def __post_init__(self) -> None:
        if type(self) is not ResearchSettlementAmbiguityPoint:
            raise ValueError(
                "ambiguity point must be exactly ResearchSettlementAmbiguityPoint",
            )
        for field_name in ("packet_id", "event_id", "ambiguity_id"):
            _require_public_identifier(field_name, getattr(self, field_name))
        object.__setattr__(
            self,
            "severity_score",
            _require_ratio_decimal("severity_score", self.severity_score),
        )
        _require_bool("resolved", self.resolved)
        object.__setattr__(
            self,
            "public_note",
            _normalize_optional_public_text("public_note", self.public_note),
        )
        _require_hard_flags("ambiguity point", self)
        _reject_unsafe_public_payload("ambiguity point", self)


@dataclass(frozen=True)
class ResearchSettlementReviewState:
    packet_id: str
    event_id: str
    review_status: str
    reviewer_count: Decimal
    reviewed_at: datetime | None = None
    public_note: str | None = None
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchSettlementReviewState:
            raise TypeError("ResearchSettlementReviewState does not support subclassing")

    def __post_init__(self) -> None:
        if type(self) is not ResearchSettlementReviewState:
            raise ValueError("review state must be exactly ResearchSettlementReviewState")
        for field_name in ("packet_id", "event_id"):
            _require_public_identifier(field_name, getattr(self, field_name))
        _require_member("review_status", self.review_status, _REVIEW_STATUSES)
        object.__setattr__(
            self,
            "reviewer_count",
            _require_nonnegative_count_decimal("reviewer_count", self.reviewer_count),
        )
        if self.reviewed_at is not None:
            object.__setattr__(
                self,
                "reviewed_at",
                _as_utc("reviewed_at", self.reviewed_at),
            )
        if self.review_status == "approved" and self.reviewer_count <= _ZERO:
            raise ValueError("approved review requires at least one reviewer")
        object.__setattr__(
            self,
            "public_note",
            _normalize_optional_public_text("public_note", self.public_note),
        )
        _require_hard_flags("review state", self)
        _reject_unsafe_public_payload("review state", self)


@dataclass(frozen=True)
class ResearchSettlementEvidencePacketPublicPayloadItem:
    key: str
    value: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchSettlementEvidencePacketPublicPayloadItem:
            raise TypeError(
                "ResearchSettlementEvidencePacketPublicPayloadItem does not support "
                "subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchSettlementEvidencePacketPublicPayloadItem:
            raise ValueError(
                "public payload item must be exactly "
                "ResearchSettlementEvidencePacketPublicPayloadItem",
            )
        _require_public_identifier("key", self.key)
        object.__setattr__(self, "value", _require_public_text("value", self.value))
        _require_hard_flags("public payload item", self)
        _reject_unsafe_public_payload("public payload item", self)


@dataclass(frozen=True)
class ResearchSettlementEvidencePacketRow:
    packet_id: str
    event_id: str
    evidence_count: Decimal
    supporting_evidence_count: Decimal
    required_evidence_type_count: Decimal
    covered_evidence_type_count: Decimal
    missing_evidence_type_count: Decimal
    source_family_count: Decimal
    rule_count: Decimal
    mapped_rule_count: Decimal
    partial_rule_count: Decimal
    open_ambiguity_count: Decimal
    max_open_ambiguity_severity: Decimal
    reviewer_count: Decimal
    evidence_completeness_score: Decimal
    source_independence_score: Decimal
    rule_mapping_score: Decimal
    settlement_hours_remaining: Decimal
    review_status: str
    packet_status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchSettlementEvidencePacketRow:
            raise TypeError(
                "ResearchSettlementEvidencePacketRow does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchSettlementEvidencePacketRow:
            raise ValueError("row must be exactly ResearchSettlementEvidencePacketRow")
        for field_name in ("packet_id", "event_id"):
            _require_public_identifier(field_name, getattr(self, field_name))
        for field_name in (
            "evidence_count",
            "supporting_evidence_count",
            "required_evidence_type_count",
            "covered_evidence_type_count",
            "missing_evidence_type_count",
            "source_family_count",
            "rule_count",
            "mapped_rule_count",
            "partial_rule_count",
            "open_ambiguity_count",
            "reviewer_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_count_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "max_open_ambiguity_severity",
            _require_ratio_decimal(
                "max_open_ambiguity_severity",
                self.max_open_ambiguity_severity,
            ),
        )
        for field_name in (
            "evidence_completeness_score",
            "source_independence_score",
            "rule_mapping_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "settlement_hours_remaining",
            _require_decimal("settlement_hours_remaining", self.settlement_hours_remaining),
        )
        _require_member("review_status", self.review_status, _REVIEW_STATUSES)
        _require_member("packet_status", self.packet_status, _PACKET_STATUSES)
        object.__setattr__(self, "reason_codes", _normalize_reason_codes(self.reason_codes))
        _validate_row_consistency(self)
        _require_hard_flags("row", self)
        _reject_unsafe_public_payload("row", self)


@dataclass(frozen=True)
class ResearchSettlementEvidencePacketReport:
    generated_at: datetime
    settlement_due_at: datetime
    config_version: str
    packet_status: str
    packet_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    settlement_hours_remaining_min: Decimal
    average_evidence_completeness_score: Decimal
    average_source_independence_score: Decimal
    average_rule_mapping_score: Decimal
    open_ambiguity_count: Decimal
    rows: tuple[ResearchSettlementEvidencePacketRow, ...]
    reason_codes: tuple[str, ...]
    public_payload: tuple[ResearchSettlementEvidencePacketPublicPayloadItem, ...]
    derived_validation_digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchSettlementEvidencePacketReport:
            raise TypeError(
                "ResearchSettlementEvidencePacketReport does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchSettlementEvidencePacketReport:
            raise ValueError("report must be exactly ResearchSettlementEvidencePacketReport")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        object.__setattr__(
            self,
            "settlement_due_at",
            _as_utc("settlement_due_at", self.settlement_due_at),
        )
        _require_public_identifier("config_version", self.config_version)
        if self.config_version != DEFAULT_RESEARCH_SETTLEMENT_EVIDENCE_PACKET_CONFIG_VERSION:
            raise ValueError("config_version must be the supported config version")
        _require_member("packet_status", self.packet_status, _PACKET_STATUSES)
        for field_name in (
            "packet_count",
            "pass_count",
            "watch_count",
            "block_count",
            "open_ambiguity_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_count_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "settlement_hours_remaining_min",
            _require_decimal(
                "settlement_hours_remaining_min",
                self.settlement_hours_remaining_min,
            ),
        )
        for field_name in (
            "average_evidence_completeness_score",
            "average_source_independence_score",
            "average_rule_mapping_score",
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
            "ResearchSettlementEvidencePacketReport.payload",
            payload,
            allow_json_containers=True,
        )
        if type(payload) is not dict:
            raise ValueError("payload must be a dict")
        return payload


def build_research_settlement_evidence_packet_report(
    evidence: Sequence[ResearchSettlementEvidenceItem],
    *,
    rule_mappings: Sequence[ResearchSettlementRuleMapping],
    ambiguity_points: Sequence[ResearchSettlementAmbiguityPoint] = (),
    review_states: Sequence[ResearchSettlementReviewState] = (),
    generated_at: datetime,
    settlement_due_at: datetime,
    config: ResearchSettlementEvidencePacketConfig | None = None,
    public_payload: Sequence[ResearchSettlementEvidencePacketPublicPayloadItem] = (),
) -> ResearchSettlementEvidencePacketReport:
    """Build a local report-only settlement evidence packet snapshot."""

    if config is None:
        config = ResearchSettlementEvidencePacketConfig()
    if type(config) is not ResearchSettlementEvidencePacketConfig:
        raise ValueError("config must be a ResearchSettlementEvidencePacketConfig")
    generated_at = _as_utc("generated_at", generated_at)
    settlement_due_at = _as_utc("settlement_due_at", settlement_due_at)
    normalized_evidence = _normalize_evidence(evidence)
    normalized_mappings = _normalize_rule_mappings(rule_mappings)
    normalized_ambiguities = _normalize_ambiguity_points(ambiguity_points)
    normalized_reviews = _normalize_review_states(review_states)
    for item in normalized_evidence:
        if item.observed_at > generated_at:
            raise ValueError("evidence observed_at must not be after generated_at")
    for item in normalized_reviews:
        if item.reviewed_at is not None and item.reviewed_at > generated_at:
            raise ValueError("reviewed_at must not be after generated_at")
    payload_items = _normalize_public_payload(public_payload)
    rows = _build_rows(
        normalized_evidence,
        normalized_mappings,
        normalized_ambiguities,
        normalized_reviews,
        generated_at=generated_at,
        settlement_due_at=settlement_due_at,
        config=config,
    )
    reason_codes = _report_reason_codes(rows)
    values: dict[str, object] = {
        "generated_at": generated_at,
        "settlement_due_at": settlement_due_at,
        "config_version": config.config_version,
        "packet_status": _report_status(rows),
        "packet_count": _decimal_count(len(rows)),
        "pass_count": _decimal_count(_status_count(rows, "pass")),
        "watch_count": _decimal_count(_status_count(rows, "watch")),
        "block_count": _decimal_count(_status_count(rows, "block")),
        "settlement_hours_remaining_min": min(
            (row.settlement_hours_remaining for row in rows),
            default=_hours_between(generated_at, settlement_due_at),
        ),
        "average_evidence_completeness_score": _average(
            tuple(row.evidence_completeness_score for row in rows),
        ),
        "average_source_independence_score": _average(
            tuple(row.source_independence_score for row in rows),
        ),
        "average_rule_mapping_score": _average(
            tuple(row.rule_mapping_score for row in rows),
        ),
        "open_ambiguity_count": _sum_decimal(
            tuple(row.open_ambiguity_count for row in rows),
        ),
        "rows": rows,
        "reason_codes": reason_codes,
        "public_payload": payload_items,
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    return ResearchSettlementEvidencePacketReport(
        **values,
        derived_validation_digest=_report_digest_from_values(values),
    )


def _build_rows(
    evidence: tuple[ResearchSettlementEvidenceItem, ...],
    rule_mappings: tuple[ResearchSettlementRuleMapping, ...],
    ambiguity_points: tuple[ResearchSettlementAmbiguityPoint, ...],
    review_states: tuple[ResearchSettlementReviewState, ...],
    *,
    generated_at: datetime,
    settlement_due_at: datetime,
    config: ResearchSettlementEvidencePacketConfig,
) -> tuple[ResearchSettlementEvidencePacketRow, ...]:
    keys = {
        (item.packet_id, item.event_id)
        for item in (*evidence, *rule_mappings, *ambiguity_points, *review_states)
    }
    rows = [
        _row_for_key(
            packet_id,
            event_id,
            tuple(item for item in evidence if (item.packet_id, item.event_id) == key),
            tuple(item for item in rule_mappings if (item.packet_id, item.event_id) == key),
            tuple(item for item in ambiguity_points if (item.packet_id, item.event_id) == key),
            tuple(item for item in review_states if (item.packet_id, item.event_id) == key),
            generated_at=generated_at,
            settlement_due_at=settlement_due_at,
            config=config,
        )
        for key in sorted(keys)
        for packet_id, event_id in (key,)
    ]
    return tuple(rows)


def _row_for_key(
    packet_id: str,
    event_id: str,
    evidence: tuple[ResearchSettlementEvidenceItem, ...],
    rule_mappings: tuple[ResearchSettlementRuleMapping, ...],
    ambiguity_points: tuple[ResearchSettlementAmbiguityPoint, ...],
    review_states: tuple[ResearchSettlementReviewState, ...],
    *,
    generated_at: datetime,
    settlement_due_at: datetime,
    config: ResearchSettlementEvidencePacketConfig,
) -> ResearchSettlementEvidencePacketRow:
    _reject_duplicate_identifiers(
        "evidence_id",
        tuple(item.evidence_id for item in evidence),
    )
    _reject_duplicate_identifiers("rule_id", tuple(item.rule_id for item in rule_mappings))
    _reject_duplicate_identifiers(
        "ambiguity_id",
        tuple(item.ambiguity_id for item in ambiguity_points),
    )
    supporting = tuple(item for item in evidence if item.supports_resolution)
    evidence_ids = frozenset(item.evidence_id for item in evidence)
    covered_types = frozenset(
        item.evidence_type
        for item in supporting
        if item.evidence_type in config.required_evidence_types
    )
    missing_type_count = _decimal_count(
        len(config.required_evidence_types) - len(covered_types),
    )
    source_family_count = _decimal_count(len({item.source_family for item in supporting}))
    rule_count = _decimal_count(len(rule_mappings))
    mapped_rule_count = _decimal_count(
        sum(
            1
            for item in rule_mappings
            if item.mapping_status == "mapped" and item.evidence_id in evidence_ids
        ),
    )
    partial_rule_count = _decimal_count(
        sum(1 for item in rule_mappings if item.mapping_status == "partial"),
    )
    open_ambiguities = tuple(item for item in ambiguity_points if not item.resolved)
    max_open_ambiguity_severity = max(
        (item.severity_score for item in open_ambiguities),
        default=_ZERO,
    )
    latest_review = _latest_review_state(review_states)
    review_status = latest_review.review_status if latest_review is not None else "not_reviewed"
    reviewer_count = latest_review.reviewer_count if latest_review is not None else _ZERO
    evidence_completeness_score = _ratio(
        _decimal_count(len(covered_types)),
        _decimal_count(len(config.required_evidence_types)),
    )
    source_independence_score = _clamp_ratio(
        source_family_count / config.min_source_family_count,
    )
    rule_mapping_score = _ratio(mapped_rule_count, rule_count)
    settlement_hours_remaining = _hours_between(generated_at, settlement_due_at)
    reason_codes = _row_reason_codes(
        evidence_count=_decimal_count(len(evidence)),
        evidence_completeness_score=evidence_completeness_score,
        source_independence_score=source_independence_score,
        rule_count=rule_count,
        rule_mapping_score=rule_mapping_score,
        open_ambiguity_count=_decimal_count(len(open_ambiguities)),
        max_open_ambiguity_severity=max_open_ambiguity_severity,
        review_status=review_status,
        settlement_hours_remaining=settlement_hours_remaining,
        config=config,
    )
    return ResearchSettlementEvidencePacketRow(
        packet_id=packet_id,
        event_id=event_id,
        evidence_count=_decimal_count(len(evidence)),
        supporting_evidence_count=_decimal_count(len(supporting)),
        required_evidence_type_count=_decimal_count(len(config.required_evidence_types)),
        covered_evidence_type_count=_decimal_count(len(covered_types)),
        missing_evidence_type_count=missing_type_count,
        source_family_count=source_family_count,
        rule_count=rule_count,
        mapped_rule_count=mapped_rule_count,
        partial_rule_count=partial_rule_count,
        open_ambiguity_count=_decimal_count(len(open_ambiguities)),
        max_open_ambiguity_severity=max_open_ambiguity_severity,
        reviewer_count=reviewer_count,
        evidence_completeness_score=evidence_completeness_score,
        source_independence_score=source_independence_score,
        rule_mapping_score=rule_mapping_score,
        settlement_hours_remaining=settlement_hours_remaining,
        review_status=review_status,
        packet_status=_row_status(reason_codes),
        reason_codes=reason_codes,
    )


def _row_reason_codes(
    *,
    evidence_count: Decimal,
    evidence_completeness_score: Decimal,
    source_independence_score: Decimal,
    rule_count: Decimal,
    rule_mapping_score: Decimal,
    open_ambiguity_count: Decimal,
    max_open_ambiguity_severity: Decimal,
    review_status: str,
    settlement_hours_remaining: Decimal,
    config: ResearchSettlementEvidencePacketConfig,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    if evidence_count == _ZERO or evidence_completeness_score < _ONE:
        reason_codes.append("evidence_incomplete")
    if source_independence_score < _ONE:
        reason_codes.append("source_independence_watch")
    else:
        reason_codes.append("source_independence_pass")
    if rule_count == _ZERO:
        reason_codes.append("rule_mapping_missing")
    elif rule_mapping_score < config.min_rule_mapping_score:
        reason_codes.append("rule_mapping_partial")
    if open_ambiguity_count > _ZERO:
        if max_open_ambiguity_severity >= config.high_ambiguity_severity:
            reason_codes.append("unresolved_ambiguity_block")
        else:
            reason_codes.append("unresolved_ambiguity_watch")
    if review_status != "approved":
        reason_codes.append("review_pending")
    else:
        reason_codes.append("review_approved")
    if settlement_hours_remaining <= _ZERO:
        reason_codes.append("settlement_window_block")
    elif settlement_hours_remaining <= config.settlement_watch_hours:
        reason_codes.append("settlement_window_watch")
    if not reason_codes or reason_codes == [
        "source_independence_pass",
        "review_approved",
    ]:
        reason_codes.append("settlement_evidence_packet_pass")
    return _normalize_reason_codes(tuple(reason_codes))


def _row_status(reason_codes: tuple[str, ...]) -> str:
    if "settlement_window_block" in reason_codes:
        return "block"
    if "unresolved_ambiguity_block" in reason_codes:
        return "block"
    if "evidence_incomplete" in reason_codes and "source_independence_pass" not in reason_codes:
        return "watch"
    if "rule_mapping_missing" in reason_codes and "evidence_incomplete" in reason_codes:
        return "block"
    if any(
        reason_code
        in {
            "evidence_incomplete",
            "source_independence_watch",
            "rule_mapping_missing",
            "rule_mapping_partial",
            "unresolved_ambiguity_watch",
            "review_pending",
            "settlement_window_watch",
        }
        for reason_code in reason_codes
    ):
        return "watch"
    return "pass"


def _report_status(rows: tuple[ResearchSettlementEvidencePacketRow, ...]) -> str:
    if not rows:
        return "block"
    if any(row.packet_status == "block" for row in rows):
        return "block"
    if any(row.packet_status == "watch" for row in rows):
        return "watch"
    return "pass"


def _report_reason_codes(
    rows: tuple[ResearchSettlementEvidencePacketRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return ("empty_packets",)
    reason_codes: list[str] = []
    for row in rows:
        reason_codes.extend(row.reason_codes)
    return _normalize_reason_codes(tuple(reason_codes))


def _status_count(rows: tuple[ResearchSettlementEvidencePacketRow, ...], status: str) -> int:
    return sum(1 for row in rows if row.packet_status == status)


def _validate_row_consistency(row: ResearchSettlementEvidencePacketRow) -> None:
    if row.supporting_evidence_count > row.evidence_count:
        raise ValueError("supporting_evidence_count must not exceed evidence_count")
    if row.covered_evidence_type_count > row.required_evidence_type_count:
        raise ValueError("covered_evidence_type_count must not exceed required count")
    expected_missing = _quantize(
        row.required_evidence_type_count - row.covered_evidence_type_count,
    )
    if row.missing_evidence_type_count != expected_missing:
        raise ValueError("missing_evidence_type_count must match required coverage")
    if row.mapped_rule_count > row.rule_count:
        raise ValueError("mapped_rule_count must not exceed rule_count")
    if row.partial_rule_count > row.rule_count:
        raise ValueError("partial_rule_count must not exceed rule_count")
    if row.open_ambiguity_count == _ZERO and row.max_open_ambiguity_severity != _ZERO:
        raise ValueError("max_open_ambiguity_severity requires open ambiguity")
    expected_status = _row_status(row.reason_codes)
    if row.packet_status != expected_status:
        raise ValueError("packet_status must match reason codes")


def _validate_report_consistency(report: ResearchSettlementEvidencePacketReport) -> None:
    if report.packet_count != _decimal_count(len(report.rows)):
        raise ValueError("packet_count must match rows")
    if report.pass_count != _decimal_count(_status_count(report.rows, "pass")):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _decimal_count(_status_count(report.rows, "watch")):
        raise ValueError("watch_count must match rows")
    if report.block_count != _decimal_count(_status_count(report.rows, "block")):
        raise ValueError("block_count must match rows")
    if report.settlement_hours_remaining_min != min(
        (row.settlement_hours_remaining for row in report.rows),
        default=_hours_between(report.generated_at, report.settlement_due_at),
    ):
        raise ValueError("settlement_hours_remaining_min must match rows")
    if report.average_evidence_completeness_score != _average(
        tuple(row.evidence_completeness_score for row in report.rows),
    ):
        raise ValueError("average_evidence_completeness_score must match rows")
    if report.average_source_independence_score != _average(
        tuple(row.source_independence_score for row in report.rows),
    ):
        raise ValueError("average_source_independence_score must match rows")
    if report.average_rule_mapping_score != _average(
        tuple(row.rule_mapping_score for row in report.rows),
    ):
        raise ValueError("average_rule_mapping_score must match rows")
    if report.open_ambiguity_count != _sum_decimal(
        tuple(row.open_ambiguity_count for row in report.rows),
    ):
        raise ValueError("open_ambiguity_count must match rows")
    if report.packet_status != _report_status(report.rows):
        raise ValueError("packet_status must match row statuses")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")


def _normalize_evidence(
    evidence: Sequence[ResearchSettlementEvidenceItem],
) -> tuple[ResearchSettlementEvidenceItem, ...]:
    if isinstance(evidence, (str, bytes)) or not isinstance(evidence, Sequence):
        raise ValueError("evidence must be a sequence")
    normalized: list[ResearchSettlementEvidenceItem] = []
    for item in evidence:
        if type(item) is not ResearchSettlementEvidenceItem:
            raise ValueError("evidence items must be ResearchSettlementEvidenceItem")
        normalized.append(item)
    return tuple(
        sorted(
            normalized,
            key=lambda item: (
                item.packet_id,
                item.event_id,
                item.observed_at,
                item.evidence_id,
            ),
        ),
    )


def _normalize_rule_mappings(
    rule_mappings: Sequence[ResearchSettlementRuleMapping],
) -> tuple[ResearchSettlementRuleMapping, ...]:
    if isinstance(rule_mappings, (str, bytes)) or not isinstance(rule_mappings, Sequence):
        raise ValueError("rule_mappings must be a sequence")
    normalized: list[ResearchSettlementRuleMapping] = []
    for item in rule_mappings:
        if type(item) is not ResearchSettlementRuleMapping:
            raise ValueError("rule_mappings items must be ResearchSettlementRuleMapping")
        normalized.append(item)
    return tuple(sorted(normalized, key=lambda item: (item.packet_id, item.event_id, item.rule_id)))


def _normalize_ambiguity_points(
    ambiguity_points: Sequence[ResearchSettlementAmbiguityPoint],
) -> tuple[ResearchSettlementAmbiguityPoint, ...]:
    if isinstance(ambiguity_points, (str, bytes)) or not isinstance(
        ambiguity_points,
        Sequence,
    ):
        raise ValueError("ambiguity_points must be a sequence")
    normalized: list[ResearchSettlementAmbiguityPoint] = []
    for item in ambiguity_points:
        if type(item) is not ResearchSettlementAmbiguityPoint:
            raise ValueError(
                "ambiguity_points items must be ResearchSettlementAmbiguityPoint",
            )
        normalized.append(item)
    return tuple(
        sorted(
            normalized,
            key=lambda item: (item.packet_id, item.event_id, item.ambiguity_id),
        ),
    )


def _normalize_review_states(
    review_states: Sequence[ResearchSettlementReviewState],
) -> tuple[ResearchSettlementReviewState, ...]:
    if isinstance(review_states, (str, bytes)) or not isinstance(review_states, Sequence):
        raise ValueError("review_states must be a sequence")
    normalized: list[ResearchSettlementReviewState] = []
    for item in review_states:
        if type(item) is not ResearchSettlementReviewState:
            raise ValueError("review_states items must be ResearchSettlementReviewState")
        normalized.append(item)
    return tuple(
        sorted(
            normalized,
            key=lambda item: (
                item.packet_id,
                item.event_id,
                item.reviewed_at or datetime.min.replace(tzinfo=UTC),
                item.review_status,
            ),
        ),
    )


def _normalize_rows(
    rows: Sequence[ResearchSettlementEvidencePacketRow],
) -> tuple[ResearchSettlementEvidencePacketRow, ...]:
    if isinstance(rows, (str, bytes)) or not isinstance(rows, Sequence):
        raise ValueError("rows must be a sequence")
    normalized: list[ResearchSettlementEvidencePacketRow] = []
    for row in rows:
        if type(row) is not ResearchSettlementEvidencePacketRow:
            raise ValueError("rows must contain ResearchSettlementEvidencePacketRow")
        normalized.append(row)
    return tuple(sorted(normalized, key=lambda row: (row.packet_id, row.event_id)))


def _normalize_public_payload(
    public_payload: Sequence[ResearchSettlementEvidencePacketPublicPayloadItem],
) -> tuple[ResearchSettlementEvidencePacketPublicPayloadItem, ...]:
    if isinstance(public_payload, (str, bytes)) or not isinstance(public_payload, Sequence):
        raise ValueError("public_payload must be a sequence")
    normalized: list[ResearchSettlementEvidencePacketPublicPayloadItem] = []
    for item in public_payload:
        if type(item) is not ResearchSettlementEvidencePacketPublicPayloadItem:
            raise ValueError(
                "public_payload items must be "
                "ResearchSettlementEvidencePacketPublicPayloadItem",
            )
        normalized.append(item)
    return tuple(sorted(normalized, key=lambda item: item.key))


def _normalize_evidence_types(evidence_types: Sequence[str]) -> tuple[str, ...]:
    if isinstance(evidence_types, (str, bytes)) or not isinstance(evidence_types, Sequence):
        raise ValueError("required_evidence_types must be a sequence")
    normalized: list[str] = []
    for evidence_type in evidence_types:
        _require_member("required_evidence_type", evidence_type, _EVIDENCE_TYPES)
        if evidence_type not in normalized:
            normalized.append(evidence_type)
    if not normalized:
        raise ValueError("required_evidence_types must not be empty")
    return tuple(normalized)


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
    return tuple(reason_code for reason_code in _REASON_CODE_SEQUENCE if reason_code in normalized)


def _latest_review_state(
    review_states: tuple[ResearchSettlementReviewState, ...],
) -> ResearchSettlementReviewState | None:
    if not review_states:
        return None
    return sorted(
        review_states,
        key=lambda item: (
            item.reviewed_at or datetime.min.replace(tzinfo=UTC),
            item.review_status,
        ),
    )[-1]


def _reject_duplicate_identifiers(field_name: str, values: tuple[str, ...]) -> None:
    if len(values) != len(frozenset(values)):
        raise ValueError(f"duplicate {field_name} values are not allowed per packet")


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in _PHASE_FLAG_FIELDS:
        if getattr(value, field_name) is not True:
            raise ValueError(f"{field_name} must be True for {label}")


def _require_bool(field_name: str, value: object) -> bool:
    if type(value) is not bool:
        raise ValueError(f"{field_name} must be a bool")
    return value


def _require_member(field_name: str, value: object, allowed_values: frozenset[str]) -> str:
    if type(value) is not str or value not in allowed_values:
        raise ValueError(f"{field_name} must be supported")
    _reject_unsafe_public_string(field_name, value)
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


def _require_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < _ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _require_nonnegative_count_decimal(field_name: str, value: object) -> Decimal:
    return _require_nonnegative_decimal(field_name, value)


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
    if type(value) is not int:
        raise ValueError("count must be an int")
    if value < 0:
        raise ValueError("count must be nonnegative")
    return _quantize(Decimal(value))


def _sum_decimal(values: tuple[Decimal, ...]) -> Decimal:
    return _quantize(sum(values, _ZERO))


def _average(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return _ZERO
    return _quantize(sum(values, _ZERO) / Decimal(len(values)))


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == _ZERO:
        return _ZERO
    return _clamp_ratio(numerator / denominator)


def _clamp_ratio(value: Decimal) -> Decimal:
    normalized = _quantize(value)
    if normalized < _ZERO:
        return _ZERO
    if normalized > _ONE:
        return _ONE
    return normalized


def _hours_between(start: datetime, end: datetime) -> Decimal:
    delta = end - start
    seconds = Decimal(delta.days * 86400 + delta.seconds)
    microseconds = Decimal(delta.microseconds) / Decimal("1000000")
    return _quantize((seconds + microseconds) / Decimal("3600"))


def _quantize(value: Decimal) -> Decimal:
    return value.quantize(_QUANT, rounding=ROUND_HALF_UP)


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _report_values_without_digest(
    report: ResearchSettlementEvidencePacketReport,
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
    "DEFAULT_RESEARCH_SETTLEMENT_EVIDENCE_PACKET_CONFIG_VERSION",
    "ResearchSettlementAmbiguityPoint",
    "ResearchSettlementEvidenceItem",
    "ResearchSettlementEvidencePacketConfig",
    "ResearchSettlementEvidencePacketPublicPayloadItem",
    "ResearchSettlementEvidencePacketReport",
    "ResearchSettlementEvidencePacketRow",
    "ResearchSettlementReviewState",
    "ResearchSettlementRuleMapping",
    "build_research_settlement_evidence_packet_report",
)
