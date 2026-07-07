"""Pure Phase 1 scorer for research-packet evidence contradiction severity."""

from __future__ import annotations

from dataclasses import dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
import hashlib
from typing import Any


DEFAULT_RESEARCH_PACKET_EVIDENCE_CONTRADICTION_SEVERITY_V2_CONFIG_VERSION = (
    "research-packet-evidence-contradiction-severity-v2"
)
DERIVED_VALIDATION_DIGEST_FIELD = "derived_validation_digest"
PHASE_FLAG_FIELDS = ("paper_only", "report_only", "readonly")

STATUSES = ("clear", "watch", "blocked")
STATUS_RANK = {
    "clear": Decimal("0.000000"),
    "watch": Decimal("1.000000"),
    "blocked": Decimal("2.000000"),
}

QUANTUM = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
SECONDS_PER_HOUR = Decimal("3600.000000")
SECONDS_PER_DAY = Decimal("86400.000000")
MICROSECONDS_PER_SECOND = Decimal("1000000.000000")
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)

SOURCE_FAMILY_INDEPENDENCE_WEIGHT = Decimal("0.200000")
EVIDENCE_FRESHNESS_WEIGHT = Decimal("0.150000")
CLAIM_CONFLICT_WEIGHT = Decimal("0.200000")
OFFICIAL_SOURCE_CONFLICT_WEIGHT = Decimal("0.150000")
RESOLUTION_RULE_SENSITIVITY_WEIGHT = Decimal("0.150000")
MARKET_CLOSE_URGENCY_WEIGHT = Decimal("0.150000")

ROW_REASON_CODES = (
    "evidence_contradiction_severity_clear",
    "evidence_claim_conflict",
    "evidence_source_family_independent_conflict",
    "evidence_fresh_conflict",
    "evidence_official_source_conflict",
    "evidence_resolution_rule_sensitive",
    "evidence_market_close_urgent",
    "evidence_contradiction_severity_watch",
    "evidence_contradiction_severity_blocked",
)
REPORT_REASON_CODES = (
    "evidence_contradiction_severity_no_inputs",
    "evidence_contradiction_severity_clear",
    "evidence_claim_conflicts_present",
    "independent_source_family_conflicts_present",
    "fresh_contradictory_evidence_present",
    "official_source_conflict_present",
    "resolution_rule_sensitive_conflict_present",
    "market_close_urgency_present",
    "evidence_contradiction_severity_watch",
    "evidence_contradiction_severity_blocked",
)

PUBLIC_ROW_FIELDS = (
    "packet_id",
    "event_id",
    "evidence_id",
    "source_family",
    "source_id",
    "observed_at",
    "market_closes_at",
    "claimed_outcome",
    "reference_outcome",
    "official_source",
    "contradicts_reference",
    "evidence_age_hours",
    "hours_to_market_close",
    "source_family_independence_score",
    "evidence_freshness_score",
    "claim_conflict_count",
    "claim_conflict_score",
    "official_source_conflict_score",
    "resolution_rule_sensitivity_score",
    "market_close_urgency_score",
    "contradiction_severity_score",
    "watch_severity_threshold",
    "blocked_severity_threshold",
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
    "contradiction_count",
    "independent_source_family_conflict_count",
    "fresh_conflict_count",
    "official_source_conflict_count",
    "resolution_rule_sensitive_conflict_count",
    "market_close_urgent_conflict_count",
    "blocked_count",
    "watch_count",
    "clear_count",
    "max_contradiction_severity_score",
    "status",
    "reason_codes",
    "rows",
    "paper_only",
    "report_only",
    "readonly",
)
PUBLIC_REPORT_FIELDS = (
    *PUBLIC_REPORT_FIELDS_WITHOUT_DIGEST,
    DERIVED_VALIDATION_DIGEST_FIELD,
)

_BLOCKED_TEXT_FRAGMENTS = (
    "au" "th",
    "wal" "let",
    "acc" "ount",
    "bro" "ker",
    "ord" "er",
    "sub" "mit",
    "can" "cel",
    "sig" "ning",
    "net" "work",
    "data" "base",
    "live",
    "tra" "de",
    "tra" "ding",
    "mut" "ation",
    "per" "sist",
)

__all__ = (
    "DEFAULT_RESEARCH_PACKET_EVIDENCE_CONTRADICTION_SEVERITY_V2_CONFIG_VERSION",
    "ResearchPacketEvidenceContradictionInput",
    "ResearchPacketEvidenceContradictionSeverityConfig",
    "ResearchPacketEvidenceContradictionSeverityReport",
    "ResearchPacketEvidenceContradictionSeverityRow",
    "build_research_packet_evidence_contradiction_severity_v2_report",
    "research_packet_evidence_contradiction_severity_v2_payload",
)


@dataclass(frozen=True)
class ResearchPacketEvidenceContradictionSeverityConfig:
    config_version: str = (
        DEFAULT_RESEARCH_PACKET_EVIDENCE_CONTRADICTION_SEVERITY_V2_CONFIG_VERSION
    )
    freshness_window_hours: Decimal = Decimal("24.000000")
    market_close_urgency_window_hours: Decimal = Decimal("12.000000")
    independent_source_family_block_threshold: Decimal = Decimal("3.000000")
    claim_conflict_block_threshold: Decimal = Decimal("3.000000")
    watch_severity_threshold: Decimal = Decimal("0.350000")
    blocked_severity_threshold: Decimal = Decimal("0.750000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchPacketEvidenceContradictionSeverityConfig:
            raise TypeError(
                "ResearchPacketEvidenceContradictionSeverityConfig does not support subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(
            "config",
            self,
            ResearchPacketEvidenceContradictionSeverityConfig,
        )
        _require_canonical_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_PACKET_EVIDENCE_CONTRADICTION_SEVERITY_V2_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "freshness_window_hours",
            "market_close_urgency_window_hours",
            "independent_source_family_block_threshold",
            "claim_conflict_block_threshold",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_positive_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "watch_severity_threshold",
            "blocked_severity_threshold",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability_decimal(field_name, getattr(self, field_name)),
            )
        if self.blocked_severity_threshold < self.watch_severity_threshold:
            raise ValueError(
                "blocked_severity_threshold must be at least watch_severity_threshold",
            )
        _reject_unsafe_live_surface("config", self)
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class ResearchPacketEvidenceContradictionInput:
    packet_id: str
    event_id: str
    evidence_id: str
    source_family: str
    source_id: str
    observed_at: datetime
    market_closes_at: datetime
    claimed_outcome: str
    reference_outcome: str
    official_source: bool
    resolution_rule_sensitivity_score: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchPacketEvidenceContradictionInput:
            raise TypeError(
                "ResearchPacketEvidenceContradictionInput does not support subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type("evidence", self, ResearchPacketEvidenceContradictionInput)
        for field_name in (
            "packet_id",
            "event_id",
            "evidence_id",
            "source_family",
            "source_id",
            "claimed_outcome",
            "reference_outcome",
        ):
            _require_canonical_string(field_name, getattr(self, field_name))
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        object.__setattr__(
            self,
            "market_closes_at",
            _as_utc("market_closes_at", self.market_closes_at),
        )
        _require_bool("official_source", self.official_source)
        object.__setattr__(
            self,
            "resolution_rule_sensitivity_score",
            _normalize_probability_decimal(
                "resolution_rule_sensitivity_score",
                self.resolution_rule_sensitivity_score,
            ),
        )
        _reject_unsafe_live_surface("evidence", self)
        _require_hard_flags("evidence", self)


@dataclass(frozen=True)
class ResearchPacketEvidenceContradictionSeverityRow:
    packet_id: str
    event_id: str
    evidence_id: str
    source_family: str
    source_id: str
    observed_at: datetime
    market_closes_at: datetime
    claimed_outcome: str
    reference_outcome: str
    official_source: bool
    contradicts_reference: bool
    evidence_age_hours: Decimal
    hours_to_market_close: Decimal
    source_family_independence_score: Decimal
    evidence_freshness_score: Decimal
    claim_conflict_count: Decimal
    claim_conflict_score: Decimal
    official_source_conflict_score: Decimal
    resolution_rule_sensitivity_score: Decimal
    market_close_urgency_score: Decimal
    contradiction_severity_score: Decimal
    watch_severity_threshold: Decimal
    blocked_severity_threshold: Decimal
    status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchPacketEvidenceContradictionSeverityRow:
            raise TypeError(
                "ResearchPacketEvidenceContradictionSeverityRow does not support subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type("row", self, ResearchPacketEvidenceContradictionSeverityRow)
        for field_name in (
            "packet_id",
            "event_id",
            "evidence_id",
            "source_family",
            "source_id",
            "claimed_outcome",
            "reference_outcome",
        ):
            _require_canonical_string(field_name, getattr(self, field_name))
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        object.__setattr__(
            self,
            "market_closes_at",
            _as_utc("market_closes_at", self.market_closes_at),
        )
        _require_bool("official_source", self.official_source)
        _require_bool("contradicts_reference", self.contradicts_reference)
        for field_name in (
            "evidence_age_hours",
            "hours_to_market_close",
            "source_family_independence_score",
            "evidence_freshness_score",
            "claim_conflict_count",
            "claim_conflict_score",
            "official_source_conflict_score",
            "resolution_rule_sensitivity_score",
            "market_close_urgency_score",
            "contradiction_severity_score",
            "watch_severity_threshold",
            "blocked_severity_threshold",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "source_family_independence_score",
            "evidence_freshness_score",
            "claim_conflict_score",
            "official_source_conflict_score",
            "resolution_rule_sensitivity_score",
            "market_close_urgency_score",
            "contradiction_severity_score",
            "watch_severity_threshold",
            "blocked_severity_threshold",
        ):
            _require_probability(field_name, getattr(self, field_name))
        if self.blocked_severity_threshold < self.watch_severity_threshold:
            raise ValueError(
                "blocked_severity_threshold must be at least watch_severity_threshold",
            )
        _require_member("status", self.status, STATUSES)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, ROW_REASON_CODES),
        )
        _reject_unsafe_live_surface("row", self)
        _require_hard_flags("row", self)
        _validate_row(self)


@dataclass(frozen=True)
class ResearchPacketEvidenceContradictionSeverityReport:
    generated_at: datetime
    config_version: str
    packet_count: Decimal
    event_count: Decimal
    evidence_count: Decimal
    contradiction_count: Decimal
    independent_source_family_conflict_count: Decimal
    fresh_conflict_count: Decimal
    official_source_conflict_count: Decimal
    resolution_rule_sensitive_conflict_count: Decimal
    market_close_urgent_conflict_count: Decimal
    blocked_count: Decimal
    watch_count: Decimal
    clear_count: Decimal
    max_contradiction_severity_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    rows: tuple[ResearchPacketEvidenceContradictionSeverityRow, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchPacketEvidenceContradictionSeverityReport:
            raise TypeError(
                "ResearchPacketEvidenceContradictionSeverityReport does not support subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(
            "report",
            self,
            ResearchPacketEvidenceContradictionSeverityReport,
        )
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        for field_name in (
            "packet_count",
            "event_count",
            "evidence_count",
            "contradiction_count",
            "independent_source_family_conflict_count",
            "fresh_conflict_count",
            "official_source_conflict_count",
            "resolution_rule_sensitive_conflict_count",
            "market_close_urgent_conflict_count",
            "blocked_count",
            "watch_count",
            "clear_count",
            "max_contradiction_severity_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
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
                REPORT_REASON_CODES,
            ),
        )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        _reject_unsafe_live_surface("report", self)
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


def build_research_packet_evidence_contradiction_severity_v2_report(
    evidence: object,
    *,
    config: ResearchPacketEvidenceContradictionSeverityConfig,
    generated_at: datetime,
) -> ResearchPacketEvidenceContradictionSeverityReport:
    _require_exact_type(
        "config",
        config,
        ResearchPacketEvidenceContradictionSeverityConfig,
    )
    generated_at_utc = _as_utc("generated_at", generated_at)
    rows = _normalize_evidence_inputs(evidence, generated_at_utc)
    severity_rows = tuple(
        sorted(
            (
                _severity_row(row, packet_rows, config, generated_at_utc)
                for packet_rows in _packet_groups(rows)
                for row in packet_rows
            ),
            key=_row_sort_key,
        ),
    )
    status = _report_status(severity_rows)
    return ResearchPacketEvidenceContradictionSeverityReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        packet_count=_count(len({row.packet_id for row in severity_rows})),
        event_count=_count(len({row.event_id for row in severity_rows})),
        evidence_count=_count(len(severity_rows)),
        contradiction_count=_count(
            sum(1 for row in severity_rows if row.contradicts_reference),
        ),
        independent_source_family_conflict_count=_count(
            len(
                {
                    row.source_family
                    for row in severity_rows
                    if row.contradicts_reference
                },
            ),
        ),
        fresh_conflict_count=_count(
            sum(
                1
                for row in severity_rows
                if row.contradicts_reference and row.evidence_freshness_score > ZERO
            ),
        ),
        official_source_conflict_count=_count(
            sum(
                1
                for row in severity_rows
                if row.contradicts_reference and row.official_source
            ),
        ),
        resolution_rule_sensitive_conflict_count=_count(
            sum(
                1
                for row in severity_rows
                if row.contradicts_reference
                and row.resolution_rule_sensitivity_score > ZERO
            ),
        ),
        market_close_urgent_conflict_count=_count(
            sum(
                1
                for row in severity_rows
                if row.contradicts_reference and row.market_close_urgency_score > ZERO
            ),
        ),
        blocked_count=_status_count(severity_rows, "blocked"),
        watch_count=_status_count(severity_rows, "watch"),
        clear_count=_status_count(severity_rows, "clear"),
        max_contradiction_severity_score=_max_decimal(
            tuple(row.contradiction_severity_score for row in severity_rows),
        ),
        status=status,
        reason_codes=_report_reason_codes(severity_rows, status),
        rows=severity_rows,
    )


def research_packet_evidence_contradiction_severity_v2_payload(
    report: ResearchPacketEvidenceContradictionSeverityReport | dict[str, object],
) -> dict[str, object]:
    if type(report) is ResearchPacketEvidenceContradictionSeverityReport:
        _require_hard_flags("report", report)
        _reject_unsafe_live_surface("report", report)
        _validate_report_derived_validation_digest(report)
        payload = _report_public_payload_without_digest(report)
        payload[DERIVED_VALIDATION_DIGEST_FIELD] = report.derived_validation_digest
        return payload
    if type(report) is dict:
        _reject_unsafe_live_surface("payload", report)
        _validate_public_payload(report)
        return dict(report)
    raise ValueError("report must be a ResearchPacketEvidenceContradictionSeverityReport")


def _normalize_evidence_inputs(
    value: object,
    generated_at: datetime,
) -> tuple[ResearchPacketEvidenceContradictionInput, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("evidence must be a list or tuple")
    rows = tuple(value)
    seen: set[tuple[str, str]] = set()
    packet_events: dict[str, str] = {}
    packet_reference_outcomes: dict[str, str] = {}
    packet_close_times: dict[str, datetime] = {}
    for row in rows:
        if type(row) is not ResearchPacketEvidenceContradictionInput:
            raise ValueError(
                "evidence must contain ResearchPacketEvidenceContradictionInput values",
            )
        _require_hard_flags("evidence", row)
        if row.observed_at > generated_at:
            raise ValueError("observed_at must not be after generated_at")
        key = (row.packet_id, row.evidence_id)
        if key in seen:
            raise ValueError("evidence must be unique by packet_id and evidence_id")
        seen.add(key)
        if row.packet_id in packet_events and packet_events[row.packet_id] != row.event_id:
            raise ValueError("packet_id must map to exactly one event_id")
        packet_events[row.packet_id] = row.event_id
        if (
            row.packet_id in packet_reference_outcomes
            and packet_reference_outcomes[row.packet_id] != row.reference_outcome
        ):
            raise ValueError("packet_id must map to exactly one reference_outcome")
        packet_reference_outcomes[row.packet_id] = row.reference_outcome
        if (
            row.packet_id in packet_close_times
            and packet_close_times[row.packet_id] != row.market_closes_at
        ):
            raise ValueError("packet_id must map to exactly one market_closes_at")
        packet_close_times[row.packet_id] = row.market_closes_at
    return rows


def _packet_groups(
    rows: tuple[ResearchPacketEvidenceContradictionInput, ...],
) -> tuple[tuple[ResearchPacketEvidenceContradictionInput, ...], ...]:
    return tuple(
        tuple(row for row in rows if row.packet_id == packet_id)
        for packet_id in sorted({row.packet_id for row in rows})
    )


def _severity_row(
    row: ResearchPacketEvidenceContradictionInput,
    packet_rows: tuple[ResearchPacketEvidenceContradictionInput, ...],
    config: ResearchPacketEvidenceContradictionSeverityConfig,
    generated_at: datetime,
) -> ResearchPacketEvidenceContradictionSeverityRow:
    contradictory_rows = tuple(
        source
        for source in packet_rows
        if source.claimed_outcome != source.reference_outcome
    )
    contradicts_reference = row.claimed_outcome != row.reference_outcome
    independent_conflict_family_count = _count(
        len({source.source_family for source in contradictory_rows}),
    )
    claim_conflict_count = _count(len(contradictory_rows))
    evidence_age_hours = _hours_between(generated_at, row.observed_at)
    hours_to_market_close = _hours_until(row.market_closes_at, generated_at)
    source_family_independence_score = _bounded_ratio(
        independent_conflict_family_count,
        config.independent_source_family_block_threshold,
    )
    evidence_freshness_score = _freshness_score(
        evidence_age_hours,
        config.freshness_window_hours,
    )
    claim_conflict_score = _bounded_ratio(
        claim_conflict_count,
        config.claim_conflict_block_threshold,
    )
    official_source_conflict_score = ONE if contradicts_reference and row.official_source else ZERO
    market_close_urgency_score = _market_close_urgency_score(
        hours_to_market_close,
        config.market_close_urgency_window_hours,
    )
    severity_score = _contradiction_severity_score(
        contradicts_reference,
        source_family_independence_score,
        evidence_freshness_score,
        claim_conflict_score,
        official_source_conflict_score,
        row.resolution_rule_sensitivity_score,
        market_close_urgency_score,
    )
    status = _row_status(
        contradicts_reference,
        severity_score,
        config.watch_severity_threshold,
        config.blocked_severity_threshold,
    )
    return ResearchPacketEvidenceContradictionSeverityRow(
        packet_id=row.packet_id,
        event_id=row.event_id,
        evidence_id=row.evidence_id,
        source_family=row.source_family,
        source_id=row.source_id,
        observed_at=row.observed_at,
        market_closes_at=row.market_closes_at,
        claimed_outcome=row.claimed_outcome,
        reference_outcome=row.reference_outcome,
        official_source=row.official_source,
        contradicts_reference=contradicts_reference,
        evidence_age_hours=evidence_age_hours,
        hours_to_market_close=hours_to_market_close,
        source_family_independence_score=source_family_independence_score,
        evidence_freshness_score=evidence_freshness_score,
        claim_conflict_count=claim_conflict_count,
        claim_conflict_score=claim_conflict_score,
        official_source_conflict_score=official_source_conflict_score,
        resolution_rule_sensitivity_score=row.resolution_rule_sensitivity_score,
        market_close_urgency_score=market_close_urgency_score,
        contradiction_severity_score=severity_score,
        watch_severity_threshold=config.watch_severity_threshold,
        blocked_severity_threshold=config.blocked_severity_threshold,
        status=status,
        reason_codes=_row_reason_codes(
            contradicts_reference,
            source_family_independence_score,
            evidence_freshness_score,
            official_source_conflict_score,
            row.resolution_rule_sensitivity_score,
            market_close_urgency_score,
            status,
        ),
    )


def _freshness_score(age_hours: Decimal, freshness_window_hours: Decimal) -> Decimal:
    if age_hours >= freshness_window_hours:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return ((freshness_window_hours - age_hours) / freshness_window_hours).quantize(
            QUANTUM,
        )


def _market_close_urgency_score(
    hours_to_market_close: Decimal,
    market_close_urgency_window_hours: Decimal,
) -> Decimal:
    if hours_to_market_close >= market_close_urgency_window_hours:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return (
            (market_close_urgency_window_hours - hours_to_market_close)
            / market_close_urgency_window_hours
        ).quantize(QUANTUM)


def _bounded_ratio(part: Decimal, whole: Decimal) -> Decimal:
    if part <= ZERO:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        value = (part / whole).quantize(QUANTUM)
    if value > ONE:
        return ONE
    return value


def _contradiction_severity_score(
    contradicts_reference: bool,
    source_family_independence_score: Decimal,
    evidence_freshness_score: Decimal,
    claim_conflict_score: Decimal,
    official_source_conflict_score: Decimal,
    resolution_rule_sensitivity_score: Decimal,
    market_close_urgency_score: Decimal,
) -> Decimal:
    if not contradicts_reference:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return (
            source_family_independence_score * SOURCE_FAMILY_INDEPENDENCE_WEIGHT
            + evidence_freshness_score * EVIDENCE_FRESHNESS_WEIGHT
            + claim_conflict_score * CLAIM_CONFLICT_WEIGHT
            + official_source_conflict_score * OFFICIAL_SOURCE_CONFLICT_WEIGHT
            + resolution_rule_sensitivity_score * RESOLUTION_RULE_SENSITIVITY_WEIGHT
            + market_close_urgency_score * MARKET_CLOSE_URGENCY_WEIGHT
        ).quantize(QUANTUM)


def _row_status(
    contradicts_reference: bool,
    contradiction_severity_score: Decimal,
    watch_severity_threshold: Decimal,
    blocked_severity_threshold: Decimal,
) -> str:
    if not contradicts_reference:
        return "clear"
    if contradiction_severity_score >= blocked_severity_threshold:
        return "blocked"
    if contradiction_severity_score >= watch_severity_threshold:
        return "watch"
    return "clear"


def _report_status(
    rows: tuple[ResearchPacketEvidenceContradictionSeverityRow, ...],
) -> str:
    if not rows:
        return "blocked"
    if any(row.status == "blocked" for row in rows):
        return "blocked"
    if any(row.status == "watch" for row in rows):
        return "watch"
    return "clear"


def _row_reason_codes(
    contradicts_reference: bool,
    source_family_independence_score: Decimal,
    evidence_freshness_score: Decimal,
    official_source_conflict_score: Decimal,
    resolution_rule_sensitivity_score: Decimal,
    market_close_urgency_score: Decimal,
    status: str,
) -> tuple[str, ...]:
    if not contradicts_reference:
        return ("evidence_contradiction_severity_clear",)
    reason_codes = ["evidence_claim_conflict"]
    if source_family_independence_score > ZERO:
        reason_codes.append("evidence_source_family_independent_conflict")
    if evidence_freshness_score > ZERO:
        reason_codes.append("evidence_fresh_conflict")
    if official_source_conflict_score > ZERO:
        reason_codes.append("evidence_official_source_conflict")
    if resolution_rule_sensitivity_score > ZERO:
        reason_codes.append("evidence_resolution_rule_sensitive")
    if market_close_urgency_score > ZERO:
        reason_codes.append("evidence_market_close_urgent")
    reason_codes.append(f"evidence_contradiction_severity_{status}")
    return tuple(reason_codes)


def _report_reason_codes(
    rows: tuple[ResearchPacketEvidenceContradictionSeverityRow, ...],
    status: str,
) -> tuple[str, ...]:
    if not rows:
        return ("evidence_contradiction_severity_no_inputs",)
    if all(row.status == "clear" for row in rows) and not any(
        row.contradicts_reference for row in rows
    ):
        return ("evidence_contradiction_severity_clear",)
    reason_codes: list[str] = []
    if any(row.contradicts_reference for row in rows):
        reason_codes.append("evidence_claim_conflicts_present")
    if len({row.source_family for row in rows if row.contradicts_reference}) > 1:
        reason_codes.append("independent_source_family_conflicts_present")
    if any(
        row.contradicts_reference and row.evidence_freshness_score > ZERO
        for row in rows
    ):
        reason_codes.append("fresh_contradictory_evidence_present")
    if any(row.contradicts_reference and row.official_source for row in rows):
        reason_codes.append("official_source_conflict_present")
    if any(
        row.contradicts_reference and row.resolution_rule_sensitivity_score > ZERO
        for row in rows
    ):
        reason_codes.append("resolution_rule_sensitive_conflict_present")
    if any(
        row.contradicts_reference and row.market_close_urgency_score > ZERO
        for row in rows
    ):
        reason_codes.append("market_close_urgency_present")
    reason_codes.append(f"evidence_contradiction_severity_{status}")
    return tuple(reason_codes)


def _row_sort_key(
    row: ResearchPacketEvidenceContradictionSeverityRow,
) -> tuple[str, Decimal, Decimal, str]:
    return (
        row.packet_id,
        -STATUS_RANK[row.status],
        -row.contradiction_severity_score,
        row.evidence_id,
    )


def _status_count(
    rows: tuple[ResearchPacketEvidenceContradictionSeverityRow, ...],
    status: str,
) -> Decimal:
    return _count(sum(1 for row in rows if row.status == status))


def _report_public_payload_without_digest(
    report: ResearchPacketEvidenceContradictionSeverityReport,
) -> dict[str, object]:
    return {
        "generated_at": _datetime_payload(report.generated_at),
        "config_version": report.config_version,
        "packet_count": _decimal_payload(report.packet_count),
        "event_count": _decimal_payload(report.event_count),
        "evidence_count": _decimal_payload(report.evidence_count),
        "contradiction_count": _decimal_payload(report.contradiction_count),
        "independent_source_family_conflict_count": _decimal_payload(
            report.independent_source_family_conflict_count,
        ),
        "fresh_conflict_count": _decimal_payload(report.fresh_conflict_count),
        "official_source_conflict_count": _decimal_payload(
            report.official_source_conflict_count,
        ),
        "resolution_rule_sensitive_conflict_count": _decimal_payload(
            report.resolution_rule_sensitive_conflict_count,
        ),
        "market_close_urgent_conflict_count": _decimal_payload(
            report.market_close_urgent_conflict_count,
        ),
        "blocked_count": _decimal_payload(report.blocked_count),
        "watch_count": _decimal_payload(report.watch_count),
        "clear_count": _decimal_payload(report.clear_count),
        "max_contradiction_severity_score": _decimal_payload(
            report.max_contradiction_severity_score,
        ),
        "status": report.status,
        "reason_codes": list(report.reason_codes),
        "rows": [_row_payload(row) for row in report.rows],
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }


def _row_payload(row: ResearchPacketEvidenceContradictionSeverityRow) -> dict[str, object]:
    return {
        "packet_id": row.packet_id,
        "event_id": row.event_id,
        "evidence_id": row.evidence_id,
        "source_family": row.source_family,
        "source_id": row.source_id,
        "observed_at": _datetime_payload(row.observed_at),
        "market_closes_at": _datetime_payload(row.market_closes_at),
        "claimed_outcome": row.claimed_outcome,
        "reference_outcome": row.reference_outcome,
        "official_source": row.official_source,
        "contradicts_reference": row.contradicts_reference,
        "evidence_age_hours": _decimal_payload(row.evidence_age_hours),
        "hours_to_market_close": _decimal_payload(row.hours_to_market_close),
        "source_family_independence_score": _decimal_payload(
            row.source_family_independence_score,
        ),
        "evidence_freshness_score": _decimal_payload(row.evidence_freshness_score),
        "claim_conflict_count": _decimal_payload(row.claim_conflict_count),
        "claim_conflict_score": _decimal_payload(row.claim_conflict_score),
        "official_source_conflict_score": _decimal_payload(
            row.official_source_conflict_score,
        ),
        "resolution_rule_sensitivity_score": _decimal_payload(
            row.resolution_rule_sensitivity_score,
        ),
        "market_close_urgency_score": _decimal_payload(
            row.market_close_urgency_score,
        ),
        "contradiction_severity_score": _decimal_payload(
            row.contradiction_severity_score,
        ),
        "watch_severity_threshold": _decimal_payload(row.watch_severity_threshold),
        "blocked_severity_threshold": _decimal_payload(row.blocked_severity_threshold),
        "status": row.status,
        "reason_codes": list(row.reason_codes),
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }


def _report_derived_validation_digest(
    report: ResearchPacketEvidenceContradictionSeverityReport,
) -> str:
    return _derived_validation_digest(_report_public_payload_without_digest(report))


def _validate_report_derived_validation_digest(
    report: ResearchPacketEvidenceContradictionSeverityReport,
) -> None:
    if report.derived_validation_digest != _report_derived_validation_digest(report):
        raise ValueError("derived_validation_digest must match report fields")


def _derived_validation_digest(payload: dict[str, object]) -> str:
    values = tuple(
        f"{field_name}={_digest_payload_value(payload[field_name])}"
        for field_name in PUBLIC_REPORT_FIELDS_WITHOUT_DIGEST
    )
    return hashlib.sha256(
        (
            "research_packet_evidence_contradiction_severity_v2|"
            + "|".join(values)
        ).encode("utf-8"),
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


def _validate_public_payload(payload: dict[str, object]) -> None:
    _require_public_payload_fields(payload)
    _require_canonical_datetime_string("generated_at", payload["generated_at"])
    _require_canonical_string("config_version", payload["config_version"])
    for field_name in (
        "packet_count",
        "event_count",
        "evidence_count",
        "contradiction_count",
        "independent_source_family_conflict_count",
        "fresh_conflict_count",
        "official_source_conflict_count",
        "resolution_rule_sensitive_conflict_count",
        "market_close_urgent_conflict_count",
        "blocked_count",
        "watch_count",
        "clear_count",
        "max_contradiction_severity_score",
    ):
        _require_decimal_payload_string(field_name, payload[field_name])
    _require_member("status", payload["status"], STATUSES)
    _normalize_public_reason_codes(
        "reason_codes",
        payload["reason_codes"],
        REPORT_REASON_CODES,
    )
    _validate_public_rows(payload["rows"])
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


def _require_public_payload_fields(payload: dict[str, object]) -> None:
    for field_name in PUBLIC_REPORT_FIELDS:
        if field_name not in payload:
            raise ValueError(f"{field_name} is required")
    extra_fields = sorted(set(payload) - set(PUBLIC_REPORT_FIELDS))
    if extra_fields:
        raise ValueError(f"unexpected public payload field: {extra_fields[0]}")


def _validate_public_rows(rows_value: object) -> None:
    if type(rows_value) is not list:
        raise ValueError("rows must be a list")
    for row in rows_value:
        if type(row) is not dict:
            raise ValueError("rows must contain payload objects")
        if tuple(row) != PUBLIC_ROW_FIELDS:
            raise ValueError("rows fields must match expected payload")
        for key, value in row.items():
            if key in ("paper_only", "report_only", "readonly"):
                continue
            if key in ("observed_at", "market_closes_at"):
                _require_canonical_datetime_string(key, value)
                continue
            if key == "reason_codes":
                _normalize_public_reason_codes(key, value, ROW_REASON_CODES)
                continue
            if key in ("official_source", "contradicts_reference"):
                _require_bool(key, value)
                continue
            if key in (
                "evidence_age_hours",
                "hours_to_market_close",
                "source_family_independence_score",
                "evidence_freshness_score",
                "claim_conflict_count",
                "claim_conflict_score",
                "official_source_conflict_score",
                "resolution_rule_sensitivity_score",
                "market_close_urgency_score",
                "contradiction_severity_score",
                "watch_severity_threshold",
                "blocked_severity_threshold",
            ):
                _require_decimal_payload_string(key, value)
                continue
            if key == "status":
                _require_member(key, value, STATUSES)
                continue
            _require_canonical_string(key, value)
        _require_hard_flags("row payload", _DictFlags(row))


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


def _validate_row(row: ResearchPacketEvidenceContradictionSeverityRow) -> None:
    if row.contradicts_reference != (row.claimed_outcome != row.reference_outcome):
        raise ValueError("contradicts_reference must match claimed_outcome")
    expected_status = _row_status(
        row.contradicts_reference,
        row.contradiction_severity_score,
        row.watch_severity_threshold,
        row.blocked_severity_threshold,
    )
    if row.status != expected_status:
        raise ValueError("status must match contradiction state")
    if not row.contradicts_reference and row.contradiction_severity_score != ZERO:
        raise ValueError("contradiction_severity_score must be zero without conflict")
    expected_reasons = _row_reason_codes(
        row.contradicts_reference,
        row.source_family_independence_score,
        row.evidence_freshness_score,
        row.official_source_conflict_score,
        row.resolution_rule_sensitivity_score,
        row.market_close_urgency_score,
        row.status,
    )
    if row.reason_codes != expected_reasons:
        raise ValueError("reason_codes must match row fields")


def _validate_report(report: ResearchPacketEvidenceContradictionSeverityReport) -> None:
    if report.packet_count != _count(len({row.packet_id for row in report.rows})):
        raise ValueError("packet_count must match rows")
    if report.event_count != _count(len({row.event_id for row in report.rows})):
        raise ValueError("event_count must match rows")
    if report.evidence_count != _count(len(report.rows)):
        raise ValueError("evidence_count must match rows")
    if report.contradiction_count != _count(
        sum(1 for row in report.rows if row.contradicts_reference),
    ):
        raise ValueError("contradiction_count must match rows")
    if report.independent_source_family_conflict_count != _count(
        len({row.source_family for row in report.rows if row.contradicts_reference}),
    ):
        raise ValueError("independent_source_family_conflict_count must match rows")
    if report.fresh_conflict_count != _count(
        sum(
            1
            for row in report.rows
            if row.contradicts_reference and row.evidence_freshness_score > ZERO
        ),
    ):
        raise ValueError("fresh_conflict_count must match rows")
    if report.official_source_conflict_count != _count(
        sum(1 for row in report.rows if row.contradicts_reference and row.official_source),
    ):
        raise ValueError("official_source_conflict_count must match rows")
    if report.resolution_rule_sensitive_conflict_count != _count(
        sum(
            1
            for row in report.rows
            if row.contradicts_reference and row.resolution_rule_sensitivity_score > ZERO
        ),
    ):
        raise ValueError("resolution_rule_sensitive_conflict_count must match rows")
    if report.market_close_urgent_conflict_count != _count(
        sum(
            1
            for row in report.rows
            if row.contradicts_reference and row.market_close_urgency_score > ZERO
        ),
    ):
        raise ValueError("market_close_urgent_conflict_count must match rows")
    if report.blocked_count != _status_count(report.rows, "blocked"):
        raise ValueError("blocked_count must match rows")
    if report.watch_count != _status_count(report.rows, "watch"):
        raise ValueError("watch_count must match rows")
    if report.clear_count != _status_count(report.rows, "clear"):
        raise ValueError("clear_count must match rows")
    if report.max_contradiction_severity_score != _max_decimal(
        tuple(row.contradiction_severity_score for row in report.rows),
    ):
        raise ValueError("max_contradiction_severity_score must match rows")
    expected_status = _report_status(report.rows)
    if report.status != expected_status:
        raise ValueError("status must match rows")
    if report.reason_codes != _report_reason_codes(report.rows, expected_status):
        raise ValueError("reason_codes must match rows")
    if report.rows != tuple(sorted(report.rows, key=_row_sort_key)):
        raise ValueError("rows must use deterministic sort")


def _normalize_rows(
    value: object,
) -> tuple[ResearchPacketEvidenceContradictionSeverityRow, ...]:
    if type(value) is not tuple:
        raise ValueError("rows must be a tuple")
    for row in value:
        if type(row) is not ResearchPacketEvidenceContradictionSeverityRow:
            raise ValueError(
                "rows must contain ResearchPacketEvidenceContradictionSeverityRow values",
            )
        _require_hard_flags("row", row)
    return value


def _max_decimal(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return ZERO
    return _normalize_nonnegative_decimal("max_decimal", max(values))


def _count(value: int) -> Decimal:
    return Decimal(value).quantize(QUANTUM)


def _hours_between(later: datetime, earlier: datetime) -> Decimal:
    later_utc = _as_utc("later", later)
    earlier_utc = _as_utc("earlier", earlier)
    delta = later_utc - earlier_utc
    with localcontext(DECIMAL_CONTEXT):
        hours = (
            Decimal(delta.days) * SECONDS_PER_DAY
            + Decimal(delta.seconds)
            + (Decimal(delta.microseconds) / MICROSECONDS_PER_SECOND)
        ) / SECONDS_PER_HOUR
        normalized = hours.quantize(QUANTUM)
    if normalized < ZERO:
        raise ValueError("hours_between must be nonnegative")
    return normalized


def _hours_until(future: datetime, generated_at: datetime) -> Decimal:
    future_utc = _as_utc("market_closes_at", future)
    generated_utc = _as_utc("generated_at", generated_at)
    if future_utc <= generated_utc:
        return ZERO
    return _hours_between(future_utc, generated_utc)


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
    with localcontext(DECIMAL_CONTEXT):
        normalized = (+value).quantize(QUANTUM)
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


def _reject_unsafe_live_surface(label: str, value: object, path: str = "") -> None:
    if is_dataclass(value) and not isinstance(value, type):
        for field in fields(value):
            item_path = field.name if not path else f"{path}.{field.name}"
            if _is_unsafe_text(field.name):
                raise ValueError(f"unsafe live surface in {label}: {item_path}")
            _reject_unsafe_live_surface(label, getattr(value, field.name), item_path)
        return
    if type(value) is str:
        if _is_unsafe_text(value):
            raise ValueError(f"unsafe live surface in {label}: {path or label}")
        return
    if type(value) is dict:
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("payload keys must be strings")
            item_path = key if not path else f"{path}.{key}"
            if _is_unsafe_text(key):
                raise ValueError(f"unsafe live surface in {label}: {item_path}")
            _reject_unsafe_live_surface(label, item, item_path)
        return
    if type(value) in (list, tuple):
        for index, item in enumerate(value):
            item_path = f"{path}[{index}]" if path else f"{label}[{index}]"
            _reject_unsafe_live_surface(label, item, item_path)


def _is_unsafe_text(value: str) -> bool:
    lowered = value.lower()
    return any(fragment in lowered for fragment in _BLOCKED_TEXT_FRAGMENTS)
