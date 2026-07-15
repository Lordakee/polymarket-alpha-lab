"""Paper-only contradictory evidence map for research packets."""

from __future__ import annotations

from dataclasses import dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
import hashlib
from typing import Any


__all__ = (
    "ResearchPacketSourceContradictionEvidence",
    "ResearchPacketSourceContradictionEvidenceMapConfig",
    "ResearchPacketSourceContradictionEvidenceMapReport",
    "ResearchPacketSourceContradictionEvidenceRow",
    "ResearchPacketSourceContradictionSourceFamilyRow",
    "build_research_packet_source_contradiction_evidence_map_v2_report",
    "research_packet_source_contradiction_evidence_map_v2_payload",
)


DEFAULT_CONFIG_VERSION = "research-packet-source-contradiction-evidence-map-v2"
DERIVED_VALIDATION_DIGEST_FIELD = "derived_validation_digest"
PHASE_FLAG_FIELDS = ("paper_only", "report_only", "readonly")
SOURCE_ROLES = ("official", "supporting", "proxy")
STATUSES = ("clear", "watch", "blocked")
ROLE_RANK = {
    "official": Decimal("3.000000"),
    "supporting": Decimal("2.000000"),
    "proxy": Decimal("1.000000"),
}
STATUS_RANK = {
    "clear": Decimal("0.000000"),
    "watch": Decimal("1.000000"),
    "blocked": Decimal("2.000000"),
}
QUANTUM = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
SECONDS_PER_HOUR = Decimal("3600.000000")
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)

EVIDENCE_ROW_REASON_CODES = (
    "source_evidence_clear",
    "source_evidence_contradicts_reference",
    "source_evidence_official_reference",
    "source_evidence_stale",
    "source_evidence_current",
    "source_evidence_rule_relevant",
    "source_evidence_severe_contradiction",
    "source_evidence_watch",
    "source_evidence_blocked",
)
SOURCE_FAMILY_REASON_CODES = (
    "source_family_evidence_clear",
    "source_family_contradiction_present",
    "source_family_official_ranked_reference",
    "source_family_stale_evidence_present",
    "source_family_rule_relevant_evidence",
    "source_family_severe_contradiction_present",
    "source_family_watch",
    "source_family_blocked",
)
REPORT_REASON_CODES = (
    "source_contradiction_evidence_map_clear",
    "source_contradiction_present",
    "official_source_ranked_contradiction_present",
    "stale_evidence_present",
    "severe_contradiction_present",
    "source_contradiction_watch",
    "source_contradiction_blocked",
)

UNSAFE_PUBLIC_TOKENS = frozenset(
    (
        "auth",
        "buy",
        "database",
        "live",
        "mutation",
        "network",
        "order",
        "persist",
        "sell",
        "signing",
        "trade",
        "wallet",
    ),
)

PUBLIC_EVIDENCE_ROW_FIELDS = (
    "packet_id",
    "event_id",
    "evidence_id",
    "source_family",
    "source_id",
    "source_role",
    "observed_at",
    "independence_group",
    "claimed_outcome",
    "reference_outcome",
    "reference_source_family",
    "reference_source_id",
    "reference_observed_at",
    "reference_official_source_rank_score",
    "evidence_age_hours",
    "recency_weight",
    "independent_source_family_count",
    "independent_evidence_count",
    "official_source_rank_score",
    "resolution_rule_relevance_score",
    "contradicts_reference",
    "contradiction_severity_score",
    "status",
    "reason_codes",
    "paper_only",
    "report_only",
    "readonly",
)
PUBLIC_SOURCE_FAMILY_ROW_FIELDS = (
    "packet_id",
    "event_id",
    "source_family",
    "evidence_count",
    "contradicted_evidence_count",
    "official_source_count",
    "current_evidence_count",
    "independent_evidence_count",
    "independent_group_count",
    "max_official_source_rank_score",
    "max_reference_official_source_rank_score",
    "max_resolution_rule_relevance_score",
    "max_recency_weight",
    "max_contradiction_severity_score",
    "status",
    "reason_codes",
    "paper_only",
    "report_only",
    "readonly",
)
PUBLIC_REPORT_FIELDS_WITHOUT_DIGEST = (
    "generated_at",
    "config_version",
    "packet_count",
    "event_count",
    "evidence_count",
    "source_family_count",
    "contradiction_count",
    "official_source_contradiction_count",
    "severe_contradiction_count",
    "current_evidence_count",
    "independent_source_family_count",
    "independent_evidence_count",
    "max_contradiction_severity_score",
    "status",
    "reason_codes",
    "evidence_rows",
    "source_family_rows",
    "paper_only",
    "report_only",
    "readonly",
)
PUBLIC_REPORT_FIELDS = (
    *PUBLIC_REPORT_FIELDS_WITHOUT_DIGEST,
    DERIVED_VALIDATION_DIGEST_FIELD,
)


@dataclass(frozen=True)
class ResearchPacketSourceContradictionEvidenceMapConfig:
    config_version: str = DEFAULT_CONFIG_VERSION
    recency_window_hours: Decimal = Decimal("24.000000")
    severe_contradiction_threshold: Decimal = Decimal("0.600000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchPacketSourceContradictionEvidenceMapConfig:
            raise TypeError(
                "ResearchPacketSourceContradictionEvidenceMapConfig does not support subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(
            "config",
            self,
            ResearchPacketSourceContradictionEvidenceMapConfig,
        )
        _require_canonical_string("config_version", self.config_version)
        object.__setattr__(
            self,
            "recency_window_hours",
            _normalize_positive_decimal("recency_window_hours", self.recency_window_hours),
        )
        object.__setattr__(
            self,
            "severe_contradiction_threshold",
            _normalize_probability_decimal(
                "severe_contradiction_threshold",
                self.severe_contradiction_threshold,
            ),
        )
        _reject_unsafe_public_payload("config", self)
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class ResearchPacketSourceContradictionEvidence:
    packet_id: str
    event_id: str
    evidence_id: str
    source_family: str
    source_id: str
    source_role: str
    observed_at: datetime
    independence_group: str
    claimed_outcome: str
    official_source_rank_score: Decimal
    resolution_rule_relevance_score: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchPacketSourceContradictionEvidence:
            raise TypeError(
                "ResearchPacketSourceContradictionEvidence does not support subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type("evidence", self, ResearchPacketSourceContradictionEvidence)
        for field_name in (
            "packet_id",
            "event_id",
            "evidence_id",
            "source_family",
            "source_id",
            "independence_group",
            "claimed_outcome",
        ):
            _require_canonical_string(field_name, getattr(self, field_name))
        _require_member("source_role", self.source_role, SOURCE_ROLES)
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        object.__setattr__(
            self,
            "official_source_rank_score",
            _normalize_probability_decimal(
                "official_source_rank_score",
                self.official_source_rank_score,
            ),
        )
        object.__setattr__(
            self,
            "resolution_rule_relevance_score",
            _normalize_probability_decimal(
                "resolution_rule_relevance_score",
                self.resolution_rule_relevance_score,
            ),
        )
        _reject_unsafe_public_payload("evidence", self)
        _require_hard_flags("evidence", self)


@dataclass(frozen=True)
class ResearchPacketSourceContradictionEvidenceRow:
    packet_id: str
    event_id: str
    evidence_id: str
    source_family: str
    source_id: str
    source_role: str
    observed_at: datetime
    independence_group: str
    claimed_outcome: str
    reference_outcome: str
    reference_source_family: str
    reference_source_id: str
    reference_observed_at: datetime
    reference_official_source_rank_score: Decimal
    evidence_age_hours: Decimal
    recency_weight: Decimal
    independent_source_family_count: Decimal
    independent_evidence_count: Decimal
    official_source_rank_score: Decimal
    resolution_rule_relevance_score: Decimal
    contradicts_reference: bool
    contradiction_severity_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchPacketSourceContradictionEvidenceRow:
            raise TypeError(
                "ResearchPacketSourceContradictionEvidenceRow does not support subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type("evidence row", self, ResearchPacketSourceContradictionEvidenceRow)
        for field_name in (
            "packet_id",
            "event_id",
            "evidence_id",
            "source_family",
            "source_id",
            "independence_group",
            "claimed_outcome",
            "reference_outcome",
            "reference_source_family",
            "reference_source_id",
        ):
            _require_canonical_string(field_name, getattr(self, field_name))
        _require_member("source_role", self.source_role, SOURCE_ROLES)
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        object.__setattr__(
            self,
            "reference_observed_at",
            _as_utc("reference_observed_at", self.reference_observed_at),
        )
        for field_name in (
            "reference_official_source_rank_score",
            "evidence_age_hours",
            "recency_weight",
            "independent_source_family_count",
            "independent_evidence_count",
            "official_source_rank_score",
            "resolution_rule_relevance_score",
            "contradiction_severity_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        _require_probability("reference_official_source_rank_score", self.reference_official_source_rank_score)
        _require_probability("recency_weight", self.recency_weight)
        _require_probability("official_source_rank_score", self.official_source_rank_score)
        _require_probability(
            "resolution_rule_relevance_score",
            self.resolution_rule_relevance_score,
        )
        _require_probability("contradiction_severity_score", self.contradiction_severity_score)
        _require_bool("contradicts_reference", self.contradicts_reference)
        _require_member("status", self.status, STATUSES)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(
                "reason_codes",
                self.reason_codes,
                EVIDENCE_ROW_REASON_CODES,
            ),
        )
        _validate_evidence_row(self)
        _reject_unsafe_public_payload("evidence row", self)
        _require_hard_flags("evidence row", self)


@dataclass(frozen=True)
class ResearchPacketSourceContradictionSourceFamilyRow:
    packet_id: str
    event_id: str
    source_family: str
    evidence_count: Decimal
    contradicted_evidence_count: Decimal
    official_source_count: Decimal
    current_evidence_count: Decimal
    independent_evidence_count: Decimal
    independent_group_count: Decimal
    max_official_source_rank_score: Decimal
    max_reference_official_source_rank_score: Decimal
    max_resolution_rule_relevance_score: Decimal
    max_recency_weight: Decimal
    max_contradiction_severity_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchPacketSourceContradictionSourceFamilyRow:
            raise TypeError(
                "ResearchPacketSourceContradictionSourceFamilyRow does not support subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(
            "source family row",
            self,
            ResearchPacketSourceContradictionSourceFamilyRow,
        )
        for field_name in ("packet_id", "event_id", "source_family"):
            _require_canonical_string(field_name, getattr(self, field_name))
        for field_name in (
            "evidence_count",
            "contradicted_evidence_count",
            "official_source_count",
            "current_evidence_count",
            "independent_evidence_count",
            "independent_group_count",
            "max_official_source_rank_score",
            "max_reference_official_source_rank_score",
            "max_resolution_rule_relevance_score",
            "max_recency_weight",
            "max_contradiction_severity_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        _require_probability("max_official_source_rank_score", self.max_official_source_rank_score)
        _require_probability(
            "max_reference_official_source_rank_score",
            self.max_reference_official_source_rank_score,
        )
        _require_probability(
            "max_resolution_rule_relevance_score",
            self.max_resolution_rule_relevance_score,
        )
        _require_probability("max_recency_weight", self.max_recency_weight)
        _require_probability(
            "max_contradiction_severity_score",
            self.max_contradiction_severity_score,
        )
        _require_member("status", self.status, STATUSES)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(
                "reason_codes",
                self.reason_codes,
                SOURCE_FAMILY_REASON_CODES,
            ),
        )
        _validate_source_family_row(self)
        _reject_unsafe_public_payload("source family row", self)
        _require_hard_flags("source family row", self)


@dataclass(frozen=True)
class ResearchPacketSourceContradictionEvidenceMapReport:
    generated_at: datetime
    config_version: str
    packet_count: Decimal
    event_count: Decimal
    evidence_count: Decimal
    source_family_count: Decimal
    contradiction_count: Decimal
    official_source_contradiction_count: Decimal
    severe_contradiction_count: Decimal
    current_evidence_count: Decimal
    independent_source_family_count: Decimal
    independent_evidence_count: Decimal
    max_contradiction_severity_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    evidence_rows: tuple[ResearchPacketSourceContradictionEvidenceRow, ...]
    source_family_rows: tuple[ResearchPacketSourceContradictionSourceFamilyRow, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchPacketSourceContradictionEvidenceMapReport:
            raise TypeError(
                "ResearchPacketSourceContradictionEvidenceMapReport does not support subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type("report", self, ResearchPacketSourceContradictionEvidenceMapReport)
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        for field_name in (
            "packet_count",
            "event_count",
            "evidence_count",
            "source_family_count",
            "contradiction_count",
            "official_source_contradiction_count",
            "severe_contradiction_count",
            "current_evidence_count",
            "independent_source_family_count",
            "independent_evidence_count",
            "max_contradiction_severity_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        _require_probability("max_contradiction_severity_score", self.max_contradiction_severity_score)
        _require_member("status", self.status, STATUSES)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, REPORT_REASON_CODES),
        )
        object.__setattr__(self, "evidence_rows", _normalize_evidence_rows(self.evidence_rows))
        object.__setattr__(
            self,
            "source_family_rows",
            _normalize_source_family_rows(self.source_family_rows),
        )
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
        _validate_report(self)


def build_research_packet_source_contradiction_evidence_map_v2_report(
    evidence: list[ResearchPacketSourceContradictionEvidence]
    | tuple[ResearchPacketSourceContradictionEvidence, ...],
    *,
    config: ResearchPacketSourceContradictionEvidenceMapConfig,
    generated_at: datetime,
) -> ResearchPacketSourceContradictionEvidenceMapReport:
    _require_exact_type("config", config, ResearchPacketSourceContradictionEvidenceMapConfig)
    generated_at_utc = _as_utc("generated_at", generated_at)
    rows = _normalize_evidence_inputs(evidence, generated_at_utc)
    evidence_rows = tuple(
        sorted(
            (
                _evidence_row(row, packet_rows, config, generated_at_utc)
                for packet_rows in _packet_groups(rows)
                for row in packet_rows
            ),
            key=_evidence_row_sort_key,
        ),
    )
    source_family_rows = tuple(
        sorted(
            (
                _source_family_row(
                    packet_id,
                    event_id,
                    source_family,
                    tuple(
                        row
                        for row in evidence_rows
                        if row.packet_id == packet_id
                        and row.event_id == event_id
                        and row.source_family == source_family
                    ),
                )
                for packet_id, event_id, source_family in sorted(
                    {
                        (row.packet_id, row.event_id, row.source_family)
                        for row in evidence_rows
                    },
                )
            ),
            key=_source_family_row_sort_key,
        ),
    )
    status = _status_rollup(tuple(row.status for row in evidence_rows))
    return ResearchPacketSourceContradictionEvidenceMapReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        packet_count=_count(len({row.packet_id for row in evidence_rows})),
        event_count=_count(len({row.event_id for row in evidence_rows})),
        evidence_count=_count(len(evidence_rows)),
        source_family_count=_count(len(source_family_rows)),
        contradiction_count=_count(
            sum(1 for row in evidence_rows if row.contradicts_reference),
        ),
        official_source_contradiction_count=_count(
            sum(
                1
                for row in evidence_rows
                if row.contradicts_reference
                and row.reference_official_source_rank_score > ZERO
            ),
        ),
        severe_contradiction_count=_count(
            sum(
                1
                for row in evidence_rows
                if row.contradiction_severity_score
                >= config.severe_contradiction_threshold
                and row.contradicts_reference
            ),
        ),
        current_evidence_count=_count(sum(1 for row in evidence_rows if row.recency_weight > ZERO)),
        independent_source_family_count=_count(
            len({row.source_family for row in evidence_rows}),
        ),
        independent_evidence_count=_count(
            len({row.independence_group for row in evidence_rows}),
        ),
        max_contradiction_severity_score=_max_decimal(
            tuple(row.contradiction_severity_score for row in evidence_rows),
        ),
        status=status,
        reason_codes=_report_reason_codes(evidence_rows, status),
        evidence_rows=evidence_rows,
        source_family_rows=source_family_rows,
    )


def research_packet_source_contradiction_evidence_map_v2_payload(
    report: ResearchPacketSourceContradictionEvidenceMapReport | dict[str, object],
) -> dict[str, object]:
    if type(report) is ResearchPacketSourceContradictionEvidenceMapReport:
        _require_hard_flags("report", report)
        _reject_unsafe_public_payload("report", report)
        _validate_report_derived_validation_digest(report)
        payload = _report_public_payload_without_digest(report)
        payload[DERIVED_VALIDATION_DIGEST_FIELD] = report.derived_validation_digest
        return payload
    if type(report) is dict:
        _reject_unsafe_public_payload("payload", report)
        _require_public_payload_fields(report)
        _validate_public_payload(report)
        return dict(report)
    raise ValueError("report must be a ResearchPacketSourceContradictionEvidenceMapReport")


def _normalize_evidence_inputs(
    value: object,
    generated_at: datetime,
) -> tuple[ResearchPacketSourceContradictionEvidence, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("evidence must be a list or tuple")
    rows = tuple(value)
    seen: set[tuple[str, str]] = set()
    packet_events: dict[str, str] = {}
    for row in rows:
        if type(row) is not ResearchPacketSourceContradictionEvidence:
            raise ValueError("evidence must contain ResearchPacketSourceContradictionEvidence values")
        _require_hard_flags("evidence", row)
        if row.observed_at > generated_at:
            raise ValueError("observed_at must not be after generated_at")
        key = (row.packet_id, row.evidence_id)
        if key in seen:
            raise ValueError("evidence must not contain duplicate packet_id/evidence_id values")
        seen.add(key)
        if row.packet_id in packet_events and packet_events[row.packet_id] != row.event_id:
            raise ValueError("packet_id must map to exactly one event_id")
        packet_events[row.packet_id] = row.event_id
    return rows


def _packet_groups(
    rows: tuple[ResearchPacketSourceContradictionEvidence, ...],
) -> tuple[tuple[ResearchPacketSourceContradictionEvidence, ...], ...]:
    return tuple(
        tuple(row for row in rows if row.packet_id == packet_id)
        for packet_id in sorted({row.packet_id for row in rows})
    )


def _reference_evidence(
    rows: tuple[ResearchPacketSourceContradictionEvidence, ...],
) -> ResearchPacketSourceContradictionEvidence:
    datetime_origin = datetime.min.replace(tzinfo=UTC)
    return sorted(
        rows,
        key=lambda row: (
            -ROLE_RANK[row.source_role],
            -row.official_source_rank_score,
            -_exact_seconds_between(row.observed_at, datetime_origin),
            row.evidence_id,
        ),
    )[0]


def _evidence_row(
    row: ResearchPacketSourceContradictionEvidence,
    packet_rows: tuple[ResearchPacketSourceContradictionEvidence, ...],
    config: ResearchPacketSourceContradictionEvidenceMapConfig,
    generated_at: datetime,
) -> ResearchPacketSourceContradictionEvidenceRow:
    reference = _reference_evidence(packet_rows)
    source_family_count = _count(len({source.source_family for source in packet_rows}))
    independent_count = _count(len({source.independence_group for source in packet_rows}))
    age_hours = _age_hours(generated_at, row.observed_at)
    recency_weight = _recency_weight(age_hours, config.recency_window_hours)
    contradicts_reference = row.claimed_outcome != reference.claimed_outcome
    severity = _contradiction_severity_score(
        contradicts_reference,
        reference.official_source_rank_score,
        recency_weight,
        row.resolution_rule_relevance_score,
    )
    status = _row_status(contradicts_reference, severity, config.severe_contradiction_threshold)
    return ResearchPacketSourceContradictionEvidenceRow(
        packet_id=row.packet_id,
        event_id=row.event_id,
        evidence_id=row.evidence_id,
        source_family=row.source_family,
        source_id=row.source_id,
        source_role=row.source_role,
        observed_at=row.observed_at,
        independence_group=row.independence_group,
        claimed_outcome=row.claimed_outcome,
        reference_outcome=reference.claimed_outcome,
        reference_source_family=reference.source_family,
        reference_source_id=reference.source_id,
        reference_observed_at=reference.observed_at,
        reference_official_source_rank_score=reference.official_source_rank_score,
        evidence_age_hours=age_hours,
        recency_weight=recency_weight,
        independent_source_family_count=source_family_count,
        independent_evidence_count=independent_count,
        official_source_rank_score=row.official_source_rank_score,
        resolution_rule_relevance_score=row.resolution_rule_relevance_score,
        contradicts_reference=contradicts_reference,
        contradiction_severity_score=severity,
        status=status,
        reason_codes=_evidence_row_reason_codes(row, reference, contradicts_reference, recency_weight, severity, status),
    )


def _source_family_row(
    packet_id: str,
    event_id: str,
    source_family: str,
    rows: tuple[ResearchPacketSourceContradictionEvidenceRow, ...],
) -> ResearchPacketSourceContradictionSourceFamilyRow:
    status = _status_rollup(tuple(row.status for row in rows))
    return ResearchPacketSourceContradictionSourceFamilyRow(
        packet_id=packet_id,
        event_id=event_id,
        source_family=source_family,
        evidence_count=_count(len(rows)),
        contradicted_evidence_count=_count(
            sum(1 for row in rows if row.contradicts_reference),
        ),
        official_source_count=_count(sum(1 for row in rows if row.source_role == "official")),
        current_evidence_count=_count(sum(1 for row in rows if row.recency_weight > ZERO)),
        independent_evidence_count=_count(len({row.evidence_id for row in rows})),
        independent_group_count=_count(len({row.independence_group for row in rows})),
        max_official_source_rank_score=_max_decimal(
            tuple(row.official_source_rank_score for row in rows),
        ),
        max_reference_official_source_rank_score=_max_decimal(
            tuple(row.reference_official_source_rank_score for row in rows),
        ),
        max_resolution_rule_relevance_score=_max_decimal(
            tuple(row.resolution_rule_relevance_score for row in rows),
        ),
        max_recency_weight=_max_decimal(tuple(row.recency_weight for row in rows)),
        max_contradiction_severity_score=_max_decimal(
            tuple(row.contradiction_severity_score for row in rows),
        ),
        status=status,
        reason_codes=_source_family_reason_codes(rows, status),
    )


def _age_hours(generated_at: datetime, observed_at: datetime) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        age_seconds = _exact_seconds_between(generated_at, observed_at)
        return (age_seconds / SECONDS_PER_HOUR).quantize(QUANTUM)


def _exact_seconds_between(later: datetime, earlier: datetime) -> Decimal:
    delta = later - earlier
    with localcontext(DECIMAL_CONTEXT):
        return (
            Decimal(delta.days) * Decimal("86400")
            + Decimal(delta.seconds)
            + Decimal(delta.microseconds) / Decimal("1000000")
        )


def _recency_weight(age_hours: Decimal, recency_window_hours: Decimal) -> Decimal:
    if age_hours >= recency_window_hours:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return ((recency_window_hours - age_hours) / recency_window_hours).quantize(
            QUANTUM,
        )


def _contradiction_severity_score(
    contradicts_reference: bool,
    reference_rank: Decimal,
    recency_weight: Decimal,
    rule_relevance: Decimal,
) -> Decimal:
    if not contradicts_reference:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return (reference_rank * recency_weight * rule_relevance).quantize(QUANTUM)


def _row_status(
    contradicts_reference: bool,
    severity: Decimal,
    severe_threshold: Decimal,
) -> str:
    if not contradicts_reference:
        return "clear"
    if severity >= severe_threshold:
        return "blocked"
    return "watch"


def _status_rollup(statuses: tuple[str, ...]) -> str:
    if any(status == "blocked" for status in statuses):
        return "blocked"
    if any(status == "watch" for status in statuses):
        return "watch"
    return "clear"


def _evidence_row_reason_codes(
    row: ResearchPacketSourceContradictionEvidence,
    reference: ResearchPacketSourceContradictionEvidence,
    contradicts_reference: bool,
    recency_weight: Decimal,
    severity: Decimal,
    status: str,
) -> tuple[str, ...]:
    codes: list[str] = []
    if not contradicts_reference:
        codes.append("source_evidence_clear")
    if contradicts_reference:
        codes.append("source_evidence_contradicts_reference")
    if reference.source_role == "official":
        codes.append("source_evidence_official_reference")
    if recency_weight == ZERO:
        codes.append("source_evidence_stale")
    else:
        codes.append("source_evidence_current")
    if row.resolution_rule_relevance_score > ZERO:
        codes.append("source_evidence_rule_relevant")
    if severity > ZERO and status == "blocked":
        codes.append("source_evidence_severe_contradiction")
    if status == "watch":
        codes.append("source_evidence_watch")
    if status == "blocked":
        codes.append("source_evidence_blocked")
    return tuple(codes)


def _source_family_reason_codes(
    rows: tuple[ResearchPacketSourceContradictionEvidenceRow, ...],
    status: str,
) -> tuple[str, ...]:
    codes: list[str] = []
    if not rows or all(row.status == "clear" for row in rows):
        codes.append("source_family_evidence_clear")
    if any(row.contradicts_reference for row in rows):
        codes.append("source_family_contradiction_present")
    if any(row.reference_official_source_rank_score > ZERO for row in rows):
        codes.append("source_family_official_ranked_reference")
    if any(row.recency_weight == ZERO for row in rows):
        codes.append("source_family_stale_evidence_present")
    if any(row.resolution_rule_relevance_score > ZERO for row in rows):
        codes.append("source_family_rule_relevant_evidence")
    if any(row.status == "blocked" for row in rows):
        codes.append("source_family_severe_contradiction_present")
    if status == "watch":
        codes.append("source_family_watch")
    if status == "blocked":
        codes.append("source_family_blocked")
    return tuple(codes)


def _report_reason_codes(
    rows: tuple[ResearchPacketSourceContradictionEvidenceRow, ...],
    status: str,
) -> tuple[str, ...]:
    if not rows or all(row.status == "clear" for row in rows):
        return ("source_contradiction_evidence_map_clear",)
    codes: list[str] = []
    if any(row.contradicts_reference for row in rows):
        codes.append("source_contradiction_present")
    if any(
        row.contradicts_reference and row.reference_official_source_rank_score > ZERO
        for row in rows
    ):
        codes.append("official_source_ranked_contradiction_present")
    if any(row.recency_weight == ZERO for row in rows):
        codes.append("stale_evidence_present")
    if any(row.status == "blocked" for row in rows):
        codes.append("severe_contradiction_present")
    if status == "watch":
        codes.append("source_contradiction_watch")
    if status == "blocked":
        codes.append("source_contradiction_blocked")
    return tuple(codes)


def _evidence_row_sort_key(
    row: ResearchPacketSourceContradictionEvidenceRow,
) -> tuple[str, Decimal, Decimal, str]:
    return (
        row.packet_id,
        -STATUS_RANK[row.status],
        -row.contradiction_severity_score,
        row.evidence_id,
    )


def _source_family_row_sort_key(
    row: ResearchPacketSourceContradictionSourceFamilyRow,
) -> tuple[str, Decimal, Decimal, str]:
    return (
        row.packet_id,
        -STATUS_RANK[row.status],
        -row.max_contradiction_severity_score,
        row.source_family,
    )


def _report_public_payload_without_digest(
    report: ResearchPacketSourceContradictionEvidenceMapReport,
) -> dict[str, object]:
    return {
        "generated_at": _datetime_payload(report.generated_at),
        "config_version": report.config_version,
        "packet_count": _decimal_payload(report.packet_count),
        "event_count": _decimal_payload(report.event_count),
        "evidence_count": _decimal_payload(report.evidence_count),
        "source_family_count": _decimal_payload(report.source_family_count),
        "contradiction_count": _decimal_payload(report.contradiction_count),
        "official_source_contradiction_count": _decimal_payload(
            report.official_source_contradiction_count,
        ),
        "severe_contradiction_count": _decimal_payload(report.severe_contradiction_count),
        "current_evidence_count": _decimal_payload(report.current_evidence_count),
        "independent_source_family_count": _decimal_payload(
            report.independent_source_family_count,
        ),
        "independent_evidence_count": _decimal_payload(report.independent_evidence_count),
        "max_contradiction_severity_score": _decimal_payload(
            report.max_contradiction_severity_score,
        ),
        "status": report.status,
        "reason_codes": list(report.reason_codes),
        "evidence_rows": [_evidence_row_payload(row) for row in report.evidence_rows],
        "source_family_rows": [
            _source_family_row_payload(row) for row in report.source_family_rows
        ],
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }


def _evidence_row_payload(row: ResearchPacketSourceContradictionEvidenceRow) -> dict[str, object]:
    return {
        "packet_id": row.packet_id,
        "event_id": row.event_id,
        "evidence_id": row.evidence_id,
        "source_family": row.source_family,
        "source_id": row.source_id,
        "source_role": row.source_role,
        "observed_at": _datetime_payload(row.observed_at),
        "independence_group": row.independence_group,
        "claimed_outcome": row.claimed_outcome,
        "reference_outcome": row.reference_outcome,
        "reference_source_family": row.reference_source_family,
        "reference_source_id": row.reference_source_id,
        "reference_observed_at": _datetime_payload(row.reference_observed_at),
        "reference_official_source_rank_score": _decimal_payload(
            row.reference_official_source_rank_score,
        ),
        "evidence_age_hours": _decimal_payload(row.evidence_age_hours),
        "recency_weight": _decimal_payload(row.recency_weight),
        "independent_source_family_count": _decimal_payload(
            row.independent_source_family_count,
        ),
        "independent_evidence_count": _decimal_payload(row.independent_evidence_count),
        "official_source_rank_score": _decimal_payload(row.official_source_rank_score),
        "resolution_rule_relevance_score": _decimal_payload(
            row.resolution_rule_relevance_score,
        ),
        "contradicts_reference": row.contradicts_reference,
        "contradiction_severity_score": _decimal_payload(
            row.contradiction_severity_score,
        ),
        "status": row.status,
        "reason_codes": list(row.reason_codes),
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }


def _source_family_row_payload(
    row: ResearchPacketSourceContradictionSourceFamilyRow,
) -> dict[str, object]:
    return {
        "packet_id": row.packet_id,
        "event_id": row.event_id,
        "source_family": row.source_family,
        "evidence_count": _decimal_payload(row.evidence_count),
        "contradicted_evidence_count": _decimal_payload(row.contradicted_evidence_count),
        "official_source_count": _decimal_payload(row.official_source_count),
        "current_evidence_count": _decimal_payload(row.current_evidence_count),
        "independent_evidence_count": _decimal_payload(row.independent_evidence_count),
        "independent_group_count": _decimal_payload(row.independent_group_count),
        "max_official_source_rank_score": _decimal_payload(
            row.max_official_source_rank_score,
        ),
        "max_reference_official_source_rank_score": _decimal_payload(
            row.max_reference_official_source_rank_score,
        ),
        "max_resolution_rule_relevance_score": _decimal_payload(
            row.max_resolution_rule_relevance_score,
        ),
        "max_recency_weight": _decimal_payload(row.max_recency_weight),
        "max_contradiction_severity_score": _decimal_payload(
            row.max_contradiction_severity_score,
        ),
        "status": row.status,
        "reason_codes": list(row.reason_codes),
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }


def _report_derived_validation_digest(
    report: ResearchPacketSourceContradictionEvidenceMapReport,
) -> str:
    return _derived_validation_digest(_report_public_payload_without_digest(report))


def _validate_report_derived_validation_digest(
    report: ResearchPacketSourceContradictionEvidenceMapReport,
) -> None:
    if report.derived_validation_digest != _report_derived_validation_digest(report):
        raise ValueError("derived_validation_digest must match report fields")


def _derived_validation_digest(payload: dict[str, object]) -> str:
    values = tuple(
        f"{field_name}={_digest_payload_value(payload[field_name])}"
        for field_name in PUBLIC_REPORT_FIELDS_WITHOUT_DIGEST
    )
    return hashlib.sha256(
        ("research_packet_source_contradiction_evidence_map_v2|" + "|".join(values)).encode(
            "utf-8",
        ),
    ).hexdigest()


def _digest_payload_value(value: object) -> str:
    if type(value) is dict:
        return "{" + "|".join(
            f"{key}:{_digest_payload_value(item)}" for key, item in value.items()
        ) + "}"
    if type(value) is list:
        return "[" + ",".join(_digest_payload_value(item) for item in value) + "]"
    if type(value) is bool:
        return "true" if value else "false"
    return str(value)


def _require_public_payload_fields(payload: dict[str, object]) -> None:
    for field_name in PUBLIC_REPORT_FIELDS:
        if field_name not in payload:
            raise ValueError(f"{field_name} is required")
    extra_fields = sorted(set(payload) - set(PUBLIC_REPORT_FIELDS))
    if extra_fields:
        raise ValueError(f"unexpected public payload field: {extra_fields[0]}")


def _validate_public_payload(payload: dict[str, object]) -> None:
    _require_public_payload_fields(payload)
    _require_canonical_datetime_string("generated_at", payload["generated_at"])
    _require_canonical_string("config_version", payload["config_version"])
    for field_name in (
        "packet_count",
        "event_count",
        "evidence_count",
        "source_family_count",
        "contradiction_count",
        "official_source_contradiction_count",
        "severe_contradiction_count",
        "current_evidence_count",
        "independent_source_family_count",
        "independent_evidence_count",
        "max_contradiction_severity_score",
    ):
        _require_decimal_payload_string(field_name, payload[field_name])
    _require_member("status", payload["status"], STATUSES)
    _normalize_public_reason_codes("reason_codes", payload["reason_codes"], REPORT_REASON_CODES)
    _validate_public_rows(
        "evidence_rows",
        payload["evidence_rows"],
        PUBLIC_EVIDENCE_ROW_FIELDS,
        EVIDENCE_ROW_REASON_CODES,
    )
    _validate_public_rows(
        "source_family_rows",
        payload["source_family_rows"],
        PUBLIC_SOURCE_FAMILY_ROW_FIELDS,
        SOURCE_FAMILY_REASON_CODES,
    )
    _require_hard_flags("payload", _DictFlags(payload))
    provided_digest = _normalize_sha256(
        DERIVED_VALIDATION_DIGEST_FIELD,
        payload[DERIVED_VALIDATION_DIGEST_FIELD],
    )
    without_digest = dict(payload)
    without_digest.pop(DERIVED_VALIDATION_DIGEST_FIELD)
    if provided_digest != _derived_validation_digest(without_digest):
        raise ValueError("derived_validation_digest must match payload fields")
    _canonical_payload_value(payload)


def _validate_public_rows(
    field_name: str,
    rows_value: object,
    expected_fields: tuple[str, ...],
    allowed_reason_codes: tuple[str, ...],
) -> None:
    if type(rows_value) is not list:
        raise ValueError(f"{field_name} must be a list")
    for row in rows_value:
        if type(row) is not dict:
            raise ValueError(f"{field_name} must contain payload objects")
        if tuple(row) != expected_fields:
            raise ValueError(f"{field_name} fields must match expected payload")
        for key, value in row.items():
            if key in ("paper_only", "report_only", "readonly"):
                continue
            if key in ("observed_at", "reference_observed_at"):
                _require_canonical_datetime_string(key, value)
                continue
            if key == "reason_codes":
                _normalize_public_reason_codes(key, value, allowed_reason_codes)
                continue
            if key in ("contradicts_reference",):
                _require_bool(key, value)
                continue
            if key in (
                "reference_official_source_rank_score",
                "evidence_age_hours",
                "recency_weight",
                "independent_source_family_count",
                "independent_evidence_count",
                "official_source_rank_score",
                "resolution_rule_relevance_score",
                "contradiction_severity_score",
                "evidence_count",
                "contradicted_evidence_count",
                "official_source_count",
                "current_evidence_count",
                "independent_group_count",
                "max_official_source_rank_score",
                "max_reference_official_source_rank_score",
                "max_resolution_rule_relevance_score",
                "max_recency_weight",
                "max_contradiction_severity_score",
            ):
                _require_decimal_payload_string(key, value)
                continue
            if key == "source_role":
                _require_member(key, value, SOURCE_ROLES)
                continue
            if key == "status":
                _require_member(key, value, STATUSES)
                continue
            _require_canonical_string(key, value)
        _require_hard_flags(field_name, _DictFlags(row))


def _normalize_public_reason_codes(
    field_name: str,
    value: object,
    allowed_values: tuple[str, ...],
) -> tuple[str, ...]:
    if type(value) is not list:
        raise ValueError(f"{field_name} must be a list")
    if not value:
        raise ValueError(f"{field_name} must not be empty")
    rows: list[str] = []
    for reason_code in value:
        _require_member(field_name, reason_code, allowed_values)
        rows.append(reason_code)
    if len(set(rows)) != len(rows):
        raise ValueError(f"{field_name} must be unique")
    return tuple(rows)


def _canonical_payload_value(value: Any) -> Any:
    if type(value) is dict:
        ready: dict[str, Any] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("payload field must be a string")
            _require_canonical_string("payload field", key)
            ready[key] = _canonical_payload_value(item)
        return ready
    if type(value) is list:
        return [_canonical_payload_value(item) for item in value]
    if type(value) in (str, bool):
        return value
    if type(value) in (int, float, Decimal):
        raise ValueError("payload value must be a Decimal-derived string")
    raise ValueError("payload value is not JSON serializable")


def _validate_evidence_row(row: ResearchPacketSourceContradictionEvidenceRow) -> None:
    if row.evidence_age_hours < ZERO:
        raise ValueError("evidence_age_hours must be nonnegative")
    if row.contradicts_reference != (row.claimed_outcome != row.reference_outcome):
        raise ValueError("contradicts_reference must match claimed_outcome")
    expected_status = "clear"
    if row.contradicts_reference:
        expected_status = "blocked" if row.status == "blocked" else "watch"
    if row.status != expected_status:
        raise ValueError("status must match contradiction state")
    if not row.contradicts_reference and row.contradiction_severity_score != ZERO:
        raise ValueError("contradiction_severity_score must be zero without contradiction")


def _validate_source_family_row(
    row: ResearchPacketSourceContradictionSourceFamilyRow,
) -> None:
    if row.contradicted_evidence_count > row.evidence_count:
        raise ValueError("contradicted_evidence_count must not exceed evidence_count")
    if row.current_evidence_count > row.evidence_count:
        raise ValueError("current_evidence_count must not exceed evidence_count")
    if row.official_source_count > row.evidence_count:
        raise ValueError("official_source_count must not exceed evidence_count")
    if row.independent_evidence_count > row.evidence_count:
        raise ValueError("independent_evidence_count must not exceed evidence_count")


def _validate_report(report: ResearchPacketSourceContradictionEvidenceMapReport) -> None:
    if report.packet_count != _count(len({row.packet_id for row in report.evidence_rows})):
        raise ValueError("packet_count must match evidence_rows")
    if report.event_count != _count(len({row.event_id for row in report.evidence_rows})):
        raise ValueError("event_count must match evidence_rows")
    if report.evidence_count != _count(len(report.evidence_rows)):
        raise ValueError("evidence_count must match evidence_rows")
    if report.source_family_count != _count(len(report.source_family_rows)):
        raise ValueError("source_family_count must match source_family_rows")
    if report.contradiction_count != _count(
        sum(1 for row in report.evidence_rows if row.contradicts_reference),
    ):
        raise ValueError("contradiction_count must match evidence_rows")
    if report.current_evidence_count != _count(
        sum(1 for row in report.evidence_rows if row.recency_weight > ZERO),
    ):
        raise ValueError("current_evidence_count must match evidence_rows")
    if report.max_contradiction_severity_score != _max_decimal(
        tuple(row.contradiction_severity_score for row in report.evidence_rows),
    ):
        raise ValueError("max_contradiction_severity_score must match evidence_rows")
    if report.status != _status_rollup(tuple(row.status for row in report.evidence_rows)):
        raise ValueError("status must match evidence_rows")
    if report.evidence_rows != tuple(sorted(report.evidence_rows, key=_evidence_row_sort_key)):
        raise ValueError("evidence_rows must use deterministic ordering")
    if report.source_family_rows != tuple(
        sorted(report.source_family_rows, key=_source_family_row_sort_key),
    ):
        raise ValueError("source_family_rows must use deterministic ordering")


def _normalize_evidence_rows(value: object) -> tuple[ResearchPacketSourceContradictionEvidenceRow, ...]:
    if type(value) is not tuple:
        raise ValueError("evidence_rows must be a tuple")
    for row in value:
        if type(row) is not ResearchPacketSourceContradictionEvidenceRow:
            raise ValueError("evidence_rows must contain ResearchPacketSourceContradictionEvidenceRow values")
        _require_hard_flags("evidence row", row)
    return value


def _normalize_source_family_rows(
    value: object,
) -> tuple[ResearchPacketSourceContradictionSourceFamilyRow, ...]:
    if type(value) is not tuple:
        raise ValueError("source_family_rows must be a tuple")
    for row in value:
        if type(row) is not ResearchPacketSourceContradictionSourceFamilyRow:
            raise ValueError(
                "source_family_rows must contain ResearchPacketSourceContradictionSourceFamilyRow values",
            )
        _require_hard_flags("source family row", row)
    return value


def _max_decimal(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return ZERO
    return _normalize_nonnegative_decimal("max_decimal", max(values))


def _count(value: int) -> Decimal:
    return Decimal(value).quantize(QUANTUM)


def _normalize_reason_codes(
    field_name: str,
    value: object,
    allowed_values: tuple[str, ...],
) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ValueError(f"{field_name} must be a tuple")
    if not value:
        raise ValueError(f"{field_name} must not be empty")
    for reason_code in value:
        _require_member(field_name, reason_code, allowed_values)
    if len(set(value)) != len(value):
        raise ValueError(f"{field_name} must be unique")
    return value


def _require_exact_type(field_name: str, value: object, expected_type: type[object]) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{field_name} must be a {expected_type.__name__}")
    _require_hard_flags(field_name, value)


def _require_hard_flags(field_name: str, value: object) -> None:
    for flag_name in PHASE_FLAG_FIELDS:
        if getattr(value, flag_name, None) is not True:
            raise ValueError(f"{flag_name} must be True for {field_name}")


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


def _normalize_positive_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_nonnegative_decimal(field_name, value)
    if normalized <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _normalize_probability_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_nonnegative_decimal(field_name, value)
    _require_probability(field_name, normalized)
    return normalized


def _normalize_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    normalized = value.quantize(QUANTUM)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _require_probability(field_name: str, value: Decimal) -> None:
    if value < ZERO or value > ONE:
        raise ValueError(f"{field_name} must be a probability")


def _decimal_payload(value: Decimal) -> str:
    return format(value, "f")


def _require_decimal_payload_string(field_name: str, value: object) -> Decimal:
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
    return normalized


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _datetime_payload(value: datetime) -> str:
    return _as_utc("datetime payload", value).isoformat()


def _require_canonical_datetime_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be an ISO datetime string")
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError as exc:
        raise ValueError(f"{field_name} must be an ISO datetime string") from exc
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    if parsed.astimezone(UTC).isoformat() != value:
        raise ValueError(f"{field_name} must be canonical UTC")


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


def _reject_unsafe_public_payload(label: str, value: object, path: str = "") -> None:
    if is_dataclass(value) and not isinstance(value, type):
        for field in fields(value):
            item_path = field.name if not path else f"{path}.{field.name}"
            if _is_unsafe_public_text(field.name):
                raise ValueError(f"unsafe public payload in {label}: {item_path}")
            _reject_unsafe_public_payload(label, getattr(value, field.name), item_path)
        return
    if type(value) is str:
        if _is_unsafe_public_text(value):
            raise ValueError(f"unsafe public payload in {label}: {path or label}")
        return
    if type(value) is dict:
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("payload keys must be strings")
            item_path = key if not path else f"{path}.{key}"
            if _is_unsafe_public_text(key):
                raise ValueError(f"unsafe public payload in {label}: {item_path}")
            _reject_unsafe_public_payload(label, item, item_path)
        return
    if type(value) in (list, tuple):
        for index, item in enumerate(value):
            item_path = f"{path}[{index}]" if path else f"{label}[{index}]"
            _reject_unsafe_public_payload(label, item, item_path)


def _is_unsafe_public_text(value: str) -> bool:
    tokens = _surface_text_tokens(value.lower())
    return any(token in UNSAFE_PUBLIC_TOKENS for token in tokens)


def _surface_text_tokens(value: str) -> tuple[str, ...]:
    tokens: list[str] = []
    current: list[str] = []
    for character in value:
        if "a" <= character <= "z" or "0" <= character <= "9":
            current.append(character)
            continue
        if current:
            tokens.append("".join(current))
            current = []
    if current:
        tokens.append("".join(current))
    return tuple(tokens)
