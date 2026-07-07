"""Pure in-memory resolution ambiguity alert report for Phase 1 packets."""

from __future__ import annotations

from dataclasses import asdict, dataclass, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
import hashlib
import json
import re
from typing import Any


DEFAULT_RESEARCH_PACKET_RESOLUTION_AMBIGUITY_ALERT_V2_CONFIG_VERSION = (
    "research-packet-resolution-ambiguity-alert-v2-phase1"
)
DEFAULT_MAX_RULE_TEXT_AGE_SECONDS = Decimal("604800.000000")

VAGUE_TRIGGER_TERMS = (
    "approximately",
    "around",
    "credible reports",
    "generally accepted",
    "major",
    "material",
    "may",
    "mostly",
    "officially recognized",
    "significant",
    "substantial",
)
SOURCE_FAMILY_ROLES = ("official", "primary", "proxy", "social", "model")
ALERT_STATUSES = ("clear", "watch", "blocked")
ROW_REASON_CODES = (
    "resolution_ambiguity_clear",
    "vague_trigger_terms",
    "missing_official_anchor",
    "contradictory_source_families",
    "stale_rule_text",
    "edge_case_gap",
    "dispute_prone_settlement_evidence",
)
REPORT_REASON_CODES = (
    "resolution_ambiguity_report_clear",
    "no_event_packets",
    "vague_trigger_terms_present",
    "missing_official_anchors_present",
    "contradictory_source_families_present",
    "stale_rule_text_present",
    "edge_case_gaps_present",
    "dispute_prone_settlement_evidence_present",
)
UNSAFE_PUBLIC_FRAGMENTS = (
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

COUNT_QUANTUM = Decimal("1")
AGE_QUANTUM = Decimal("0.000001")
RATIO_QUANTUM = Decimal("0.000001")
ZERO_COUNT = Decimal("0")
ZERO_RATIO = Decimal("0.000000")
ONE_RATIO = Decimal("1.000000")
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
UNSAFE_PUBLIC_RE = re.compile(
    r"(?<![a-z0-9])(" + "|".join(re.escape(term) for term in UNSAFE_PUBLIC_FRAGMENTS) + r")(?![a-z0-9])",
)
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")

STATUS_SORT_WEIGHT = {
    "blocked": 0,
    "watch": 1,
    "clear": 2,
}
ROW_REASON_SORT_WEIGHT = {
    "missing_official_anchor": 0,
    "contradictory_source_families": 1,
    "dispute_prone_settlement_evidence": 2,
    "edge_case_gap": 3,
    "stale_rule_text": 4,
    "vague_trigger_terms": 5,
    "resolution_ambiguity_clear": 6,
}
CLEAR_REASONS = frozenset(("resolution_ambiguity_clear", "resolution_ambiguity_report_clear"))


@dataclass(frozen=True)
class ResearchPacketResolutionAmbiguityAlertV2Config:
    config_version: str = DEFAULT_RESEARCH_PACKET_RESOLUTION_AMBIGUITY_ALERT_V2_CONFIG_VERSION
    max_rule_text_age_seconds: Decimal = DEFAULT_MAX_RULE_TEXT_AGE_SECONDS
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("config_version", self.config_version)
        object.__setattr__(
            self,
            "max_rule_text_age_seconds",
            _normalize_positive_age_seconds(
                "max_rule_text_age_seconds",
                self.max_rule_text_age_seconds,
            ),
        )
        _require_hard_flags("ResearchPacketResolutionAmbiguityAlertV2Config", self)


@dataclass(frozen=True)
class ResearchPacketResolutionAmbiguityEventPacket:
    packet_id: str
    market_slug: str
    event_title: str
    resolution_rule_text: str
    rule_text_observed_at: datetime
    official_anchor_refs: tuple[str, ...] = ()
    source_families: tuple[str, ...] = ()
    contradictory_source_families: tuple[str, ...] = ()
    edge_case_notes: tuple[str, ...] = ()
    settlement_evidence_risk_terms: tuple[str, ...] = ()
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        for field_name in (
            "packet_id",
            "market_slug",
            "event_title",
            "resolution_rule_text",
        ):
            _require_canonical_string(field_name, getattr(self, field_name))
        object.__setattr__(
            self,
            "rule_text_observed_at",
            _as_utc("rule_text_observed_at", self.rule_text_observed_at),
        )
        object.__setattr__(
            self,
            "official_anchor_refs",
            _normalize_string_tuple(
                "official_anchor_refs",
                self.official_anchor_refs,
                allow_empty=True,
            ),
        )
        object.__setattr__(
            self,
            "source_families",
            _normalize_source_families(self.source_families),
        )
        object.__setattr__(
            self,
            "contradictory_source_families",
            _normalize_string_tuple(
                "contradictory_source_families",
                self.contradictory_source_families,
                allow_empty=True,
            ),
        )
        object.__setattr__(
            self,
            "edge_case_notes",
            _normalize_string_tuple(
                "edge_case_notes",
                self.edge_case_notes,
                allow_empty=True,
            ),
        )
        object.__setattr__(
            self,
            "settlement_evidence_risk_terms",
            _normalize_string_tuple(
                "settlement_evidence_risk_terms",
                self.settlement_evidence_risk_terms,
                allow_empty=True,
            ),
        )
        _require_hard_flags("ResearchPacketResolutionAmbiguityEventPacket", self)
        _reject_unsafe_public_payload(
            "ResearchPacketResolutionAmbiguityEventPacket",
            self,
        )


@dataclass(frozen=True)
class ResearchPacketResolutionAmbiguityAlertV2Row:
    packet_id: str
    market_slug: str
    alert_status: str
    ambiguity_score: Decimal
    rule_text_age_seconds: Decimal
    vague_trigger_term_count: Decimal
    official_anchor_count: Decimal
    source_family_count: Decimal
    contradictory_source_family_count: Decimal
    edge_case_gap_count: Decimal
    dispute_prone_settlement_evidence_count: Decimal
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("packet_id", self.packet_id)
        _require_canonical_string("market_slug", self.market_slug)
        _require_member("alert_status", self.alert_status, ALERT_STATUSES)
        object.__setattr__(
            self,
            "ambiguity_score",
            _normalize_ratio("ambiguity_score", self.ambiguity_score),
        )
        object.__setattr__(
            self,
            "rule_text_age_seconds",
            _normalize_age_seconds("rule_text_age_seconds", self.rule_text_age_seconds),
        )
        for field_name in (
            "vague_trigger_term_count",
            "official_anchor_count",
            "source_family_count",
            "contradictory_source_family_count",
            "edge_case_gap_count",
            "dispute_prone_settlement_evidence_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_count(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, ROW_REASON_CODES),
        )
        _validate_alert_row(self)
        _require_hard_flags("ResearchPacketResolutionAmbiguityAlertV2Row", self)


@dataclass(frozen=True)
class ResearchPacketResolutionAmbiguityAlertV2Report:
    generated_at: datetime
    config_version: str
    max_rule_text_age_seconds: Decimal
    packet_count: Decimal
    alert_count: Decimal
    blocked_count: Decimal
    watch_count: Decimal
    clear_count: Decimal
    vague_trigger_packet_count: Decimal
    missing_official_anchor_packet_count: Decimal
    contradictory_source_family_packet_count: Decimal
    stale_rule_text_packet_count: Decimal
    edge_case_gap_packet_count: Decimal
    dispute_prone_settlement_evidence_packet_count: Decimal
    highest_ambiguity_score: Decimal
    average_ambiguity_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    rows: tuple[ResearchPacketResolutionAmbiguityAlertV2Row, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        object.__setattr__(
            self,
            "max_rule_text_age_seconds",
            _normalize_positive_age_seconds(
                "max_rule_text_age_seconds",
                self.max_rule_text_age_seconds,
            ),
        )
        for field_name in (
            "packet_count",
            "alert_count",
            "blocked_count",
            "watch_count",
            "clear_count",
            "vague_trigger_packet_count",
            "missing_official_anchor_packet_count",
            "contradictory_source_family_packet_count",
            "stale_rule_text_packet_count",
            "edge_case_gap_packet_count",
            "dispute_prone_settlement_evidence_packet_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_count(field_name, getattr(self, field_name)),
            )
        for field_name in ("highest_ambiguity_score", "average_ambiguity_score"):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        _require_member("status", self.status, ALERT_STATUSES)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, REPORT_REASON_CODES),
        )
        object.__setattr__(self, "rows", _normalize_alert_rows(self.rows))
        _reject_unsafe_public_payload("resolution ambiguity alert report", self)
        _require_hard_flags("ResearchPacketResolutionAmbiguityAlertV2Report", self)
        if self.derived_validation_digest:
            _require_sha256("derived_validation_digest", self.derived_validation_digest)
            expected_digest = _derived_validation_digest(self)
            if self.derived_validation_digest != expected_digest:
                raise ValueError("derived_validation_digest must match report payload")
        _validate_alert_report(self)
        if self.derived_validation_digest:
            return
        expected_digest = _derived_validation_digest(self)
        object.__setattr__(self, "derived_validation_digest", expected_digest)


def build_research_packet_resolution_ambiguity_alert_v2_report(
    event_packets: list[ResearchPacketResolutionAmbiguityEventPacket]
    | tuple[ResearchPacketResolutionAmbiguityEventPacket, ...],
    *,
    config: ResearchPacketResolutionAmbiguityAlertV2Config,
    generated_at: datetime,
) -> ResearchPacketResolutionAmbiguityAlertV2Report:
    if type(config) is not ResearchPacketResolutionAmbiguityAlertV2Config:
        raise ValueError(
            "config must be a ResearchPacketResolutionAmbiguityAlertV2Config",
        )
    _require_hard_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    packets = _normalize_event_packets(event_packets, generated_at=generated_at_utc)
    rows = tuple(
        sorted(
            (
                _alert_row(
                    packet,
                    generated_at=generated_at_utc,
                    max_rule_text_age_seconds=config.max_rule_text_age_seconds,
                )
                for packet in packets
            ),
            key=_alert_row_sort_key,
        ),
    )
    report = ResearchPacketResolutionAmbiguityAlertV2Report(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        max_rule_text_age_seconds=config.max_rule_text_age_seconds,
        packet_count=_count(len(packets)),
        alert_count=_status_count(rows, "blocked") + _status_count(rows, "watch"),
        blocked_count=_status_count(rows, "blocked"),
        watch_count=_status_count(rows, "watch"),
        clear_count=_status_count(rows, "clear"),
        vague_trigger_packet_count=_row_reason_count(rows, "vague_trigger_terms"),
        missing_official_anchor_packet_count=_row_reason_count(
            rows,
            "missing_official_anchor",
        ),
        contradictory_source_family_packet_count=_row_reason_count(
            rows,
            "contradictory_source_families",
        ),
        stale_rule_text_packet_count=_row_reason_count(rows, "stale_rule_text"),
        edge_case_gap_packet_count=_row_reason_count(rows, "edge_case_gap"),
        dispute_prone_settlement_evidence_packet_count=_row_reason_count(
            rows,
            "dispute_prone_settlement_evidence",
        ),
        highest_ambiguity_score=_highest_score(rows),
        average_ambiguity_score=_average_score(rows),
        status=_status_from_reason_codes(_report_reason_codes(rows)),
        reason_codes=_report_reason_codes(rows),
        rows=rows,
    )
    return report


def research_packet_resolution_ambiguity_alert_v2_payload(
    report: ResearchPacketResolutionAmbiguityAlertV2Report | dict[str, Any],
) -> dict[str, Any]:
    if type(report) is ResearchPacketResolutionAmbiguityAlertV2Report:
        _require_hard_flags("report", report)
        _reject_unsafe_public_payload("resolution ambiguity alert report", report)
        payload = _json_ready(report)
    elif type(report) is dict:
        _reject_unsafe_public_payload("resolution ambiguity alert payload", report)
        payload = _json_ready(report)
    else:
        raise ValueError(
            "report must be a ResearchPacketResolutionAmbiguityAlertV2Report",
        )
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    _require_hard_flags("payload", _DictFlags(payload))
    _validate_payload_digest(payload)
    _reject_unsafe_public_payload("resolution ambiguity alert payload", payload)
    return payload


@dataclass(frozen=True)
class _DictFlags:
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


def _alert_row(
    packet: ResearchPacketResolutionAmbiguityEventPacket,
    *,
    generated_at: datetime,
    max_rule_text_age_seconds: Decimal,
) -> ResearchPacketResolutionAmbiguityAlertV2Row:
    rule_text_age_seconds = _age_seconds(generated_at, packet.rule_text_observed_at)
    vague_terms = _vague_trigger_terms(packet)
    reason_codes = _row_reason_codes(
        vague_trigger_term_count=_count(len(vague_terms)),
        official_anchor_count=_count(len(packet.official_anchor_refs)),
        contradictory_source_family_count=_count(len(packet.contradictory_source_families)),
        rule_text_age_seconds=rule_text_age_seconds,
        max_rule_text_age_seconds=max_rule_text_age_seconds,
        edge_case_gap_count=_count(len(packet.edge_case_notes)),
        dispute_prone_settlement_evidence_count=_count(
            len(packet.settlement_evidence_risk_terms),
        ),
    )
    return ResearchPacketResolutionAmbiguityAlertV2Row(
        packet_id=packet.packet_id,
        market_slug=packet.market_slug,
        alert_status=_row_status_from_reason_codes(reason_codes),
        ambiguity_score=_ambiguity_score(reason_codes),
        rule_text_age_seconds=rule_text_age_seconds,
        vague_trigger_term_count=_count(len(vague_terms)),
        official_anchor_count=_count(len(packet.official_anchor_refs)),
        source_family_count=_count(len(packet.source_families)),
        contradictory_source_family_count=_count(len(packet.contradictory_source_families)),
        edge_case_gap_count=_count(len(packet.edge_case_notes)),
        dispute_prone_settlement_evidence_count=_count(
            len(packet.settlement_evidence_risk_terms),
        ),
        reason_codes=reason_codes,
    )


def _row_reason_codes(
    *,
    vague_trigger_term_count: Decimal,
    official_anchor_count: Decimal,
    contradictory_source_family_count: Decimal,
    rule_text_age_seconds: Decimal,
    max_rule_text_age_seconds: Decimal,
    edge_case_gap_count: Decimal,
    dispute_prone_settlement_evidence_count: Decimal,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    if vague_trigger_term_count > ZERO_COUNT:
        reason_codes.append("vague_trigger_terms")
    if official_anchor_count == ZERO_COUNT:
        reason_codes.append("missing_official_anchor")
    if contradictory_source_family_count > ZERO_COUNT:
        reason_codes.append("contradictory_source_families")
    if rule_text_age_seconds > max_rule_text_age_seconds:
        reason_codes.append("stale_rule_text")
    if edge_case_gap_count > ZERO_COUNT:
        reason_codes.append("edge_case_gap")
    if dispute_prone_settlement_evidence_count > ZERO_COUNT:
        reason_codes.append("dispute_prone_settlement_evidence")
    if not reason_codes:
        reason_codes.append("resolution_ambiguity_clear")
    return tuple(reason_codes)


def _report_reason_codes(
    rows: tuple[ResearchPacketResolutionAmbiguityAlertV2Row, ...],
) -> tuple[str, ...]:
    if not rows:
        return ("no_event_packets",)
    reason_codes: list[str] = []
    if _row_reason_count(rows, "vague_trigger_terms") > ZERO_COUNT:
        reason_codes.append("vague_trigger_terms_present")
    if _row_reason_count(rows, "missing_official_anchor") > ZERO_COUNT:
        reason_codes.append("missing_official_anchors_present")
    if _row_reason_count(rows, "contradictory_source_families") > ZERO_COUNT:
        reason_codes.append("contradictory_source_families_present")
    if _row_reason_count(rows, "stale_rule_text") > ZERO_COUNT:
        reason_codes.append("stale_rule_text_present")
    if _row_reason_count(rows, "edge_case_gap") > ZERO_COUNT:
        reason_codes.append("edge_case_gaps_present")
    if _row_reason_count(rows, "dispute_prone_settlement_evidence") > ZERO_COUNT:
        reason_codes.append("dispute_prone_settlement_evidence_present")
    if not reason_codes:
        reason_codes.append("resolution_ambiguity_report_clear")
    return tuple(reason_codes)


def _normalize_event_packets(
    event_packets: list[ResearchPacketResolutionAmbiguityEventPacket]
    | tuple[ResearchPacketResolutionAmbiguityEventPacket, ...],
    *,
    generated_at: datetime,
) -> tuple[ResearchPacketResolutionAmbiguityEventPacket, ...]:
    if type(event_packets) not in (list, tuple):
        raise ValueError("event_packets must be a list or tuple")
    rows = tuple(event_packets)
    seen_packet_ids: set[str] = set()
    for row in rows:
        if type(row) is not ResearchPacketResolutionAmbiguityEventPacket:
            raise ValueError(
                "event_packets must contain ResearchPacketResolutionAmbiguityEventPacket",
            )
        _require_hard_flags("event packet", row)
        _reject_unsafe_public_payload("event packet", row)
        if row.rule_text_observed_at > generated_at:
            raise ValueError("rule_text_observed_at must not be in the future")
        if row.packet_id in seen_packet_ids:
            raise ValueError("packet_id values must be unique")
        seen_packet_ids.add(row.packet_id)
    return rows


def _normalize_alert_rows(
    value: object,
) -> tuple[ResearchPacketResolutionAmbiguityAlertV2Row, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("rows must be a list or tuple")
    rows = tuple(value)
    seen_packet_ids: set[str] = set()
    for row in rows:
        if type(row) is not ResearchPacketResolutionAmbiguityAlertV2Row:
            raise ValueError("rows must contain ResearchPacketResolutionAmbiguityAlertV2Row")
        _require_hard_flags("row", row)
        if row.packet_id in seen_packet_ids:
            raise ValueError("rows packet_id values must be unique")
        seen_packet_ids.add(row.packet_id)
    if rows != tuple(sorted(rows, key=_alert_row_sort_key)):
        raise ValueError("rows must use deterministic sorting")
    return rows


def _validate_alert_row(row: ResearchPacketResolutionAmbiguityAlertV2Row) -> None:
    structural_reasons = _row_reason_codes(
        vague_trigger_term_count=row.vague_trigger_term_count,
        official_anchor_count=row.official_anchor_count,
        contradictory_source_family_count=row.contradictory_source_family_count,
        rule_text_age_seconds=row.rule_text_age_seconds,
        max_rule_text_age_seconds=Decimal("999999999999999999999999999999.000000"),
        edge_case_gap_count=row.edge_case_gap_count,
        dispute_prone_settlement_evidence_count=(
            row.dispute_prone_settlement_evidence_count
        ),
    )
    non_stale_reasons = tuple(
        reason for reason in row.reason_codes if reason != "stale_rule_text"
    )
    non_stale_structural_reasons = tuple(
        reason for reason in structural_reasons if reason != "stale_rule_text"
    )
    if non_stale_reasons != non_stale_structural_reasons and not (
        row.reason_codes == ("stale_rule_text",)
        and non_stale_structural_reasons == ("resolution_ambiguity_clear",)
    ):
        raise ValueError("reason_codes must match row ambiguity signals")
    if row.reason_codes == ("resolution_ambiguity_clear",) and row.ambiguity_score != ZERO_RATIO:
        raise ValueError("clear rows must have zero ambiguity_score")
    if row.reason_codes != ("resolution_ambiguity_clear",) and row.ambiguity_score == ZERO_RATIO:
        raise ValueError("alert rows must have positive ambiguity_score")
    if row.alert_status != _row_status_from_reason_codes(row.reason_codes):
        raise ValueError("alert_status must match reason_codes")


def _validate_alert_report(
    report: ResearchPacketResolutionAmbiguityAlertV2Report,
) -> None:
    if report.packet_count != _count(len(report.rows)):
        raise ValueError("packet_count must match rows")
    if report.blocked_count != _status_count(report.rows, "blocked"):
        raise ValueError("blocked_count must match rows")
    if report.watch_count != _status_count(report.rows, "watch"):
        raise ValueError("watch_count must match rows")
    if report.clear_count != _status_count(report.rows, "clear"):
        raise ValueError("clear_count must match rows")
    if report.alert_count != report.blocked_count + report.watch_count:
        raise ValueError("alert_count must match rows")
    if report.vague_trigger_packet_count != _row_reason_count(
        report.rows,
        "vague_trigger_terms",
    ):
        raise ValueError("vague_trigger_packet_count must match rows")
    if report.missing_official_anchor_packet_count != _row_reason_count(
        report.rows,
        "missing_official_anchor",
    ):
        raise ValueError("missing_official_anchor_packet_count must match rows")
    if report.contradictory_source_family_packet_count != _row_reason_count(
        report.rows,
        "contradictory_source_families",
    ):
        raise ValueError("contradictory_source_family_packet_count must match rows")
    if report.stale_rule_text_packet_count != _row_reason_count(
        report.rows,
        "stale_rule_text",
    ):
        raise ValueError("stale_rule_text_packet_count must match rows")
    for row in report.rows:
        has_stale_reason = "stale_rule_text" in row.reason_codes
        is_stale = row.rule_text_age_seconds > report.max_rule_text_age_seconds
        if has_stale_reason != is_stale:
            raise ValueError("stale_rule_text must match max_rule_text_age_seconds")
    if report.edge_case_gap_packet_count != _row_reason_count(report.rows, "edge_case_gap"):
        raise ValueError("edge_case_gap_packet_count must match rows")
    if report.dispute_prone_settlement_evidence_packet_count != _row_reason_count(
        report.rows,
        "dispute_prone_settlement_evidence",
    ):
        raise ValueError(
            "dispute_prone_settlement_evidence_packet_count must match rows",
        )
    if report.highest_ambiguity_score != _highest_score(report.rows):
        raise ValueError("highest_ambiguity_score must match rows")
    if report.average_ambiguity_score != _average_score(report.rows):
        raise ValueError("average_ambiguity_score must match rows")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")
    if report.status != _status_from_reason_codes(report.reason_codes):
        raise ValueError("status must match reason_codes")


def _alert_row_sort_key(
    row: ResearchPacketResolutionAmbiguityAlertV2Row,
) -> tuple[int, Decimal, int, str]:
    return (
        STATUS_SORT_WEIGHT[row.alert_status],
        -row.ambiguity_score,
        min(ROW_REASON_SORT_WEIGHT[reason_code] for reason_code in row.reason_codes),
        row.packet_id,
    )


def _row_status_from_reason_codes(reason_codes: tuple[str, ...]) -> str:
    if reason_codes == ("resolution_ambiguity_clear",):
        return "clear"
    if (
        "missing_official_anchor" in reason_codes
        and (
            "contradictory_source_families" in reason_codes
            or "dispute_prone_settlement_evidence" in reason_codes
            or "edge_case_gap" in reason_codes
        )
    ):
        return "blocked"
    if "contradictory_source_families" in reason_codes and (
        "dispute_prone_settlement_evidence" in reason_codes
    ):
        return "blocked"
    return "watch"


def _status_from_reason_codes(reason_codes: tuple[str, ...]) -> str:
    if reason_codes == ("resolution_ambiguity_report_clear",):
        return "clear"
    if "no_event_packets" in reason_codes:
        return "blocked"
    if (
        "missing_official_anchors_present" in reason_codes
        and (
            "contradictory_source_families_present" in reason_codes
            or "dispute_prone_settlement_evidence_present" in reason_codes
            or "edge_case_gaps_present" in reason_codes
        )
    ):
        return "blocked"
    if (
        "contradictory_source_families_present" in reason_codes
        and "dispute_prone_settlement_evidence_present" in reason_codes
    ):
        return "blocked"
    return "watch"


def _ambiguity_score(reason_codes: tuple[str, ...]) -> Decimal:
    if reason_codes == ("resolution_ambiguity_clear",):
        return ZERO_RATIO
    with localcontext(DECIMAL_CONTEXT):
        return (Decimal(len(reason_codes)) / Decimal("6")).quantize(RATIO_QUANTUM)


def _highest_score(rows: tuple[ResearchPacketResolutionAmbiguityAlertV2Row, ...]) -> Decimal:
    if not rows:
        return ZERO_RATIO
    return max(row.ambiguity_score for row in rows).quantize(RATIO_QUANTUM)


def _average_score(rows: tuple[ResearchPacketResolutionAmbiguityAlertV2Row, ...]) -> Decimal:
    if not rows:
        return ZERO_RATIO
    with localcontext(DECIMAL_CONTEXT):
        total = sum((row.ambiguity_score for row in rows), ZERO_RATIO)
        return (total / Decimal(len(rows))).quantize(RATIO_QUANTUM)


def _status_count(
    rows: tuple[ResearchPacketResolutionAmbiguityAlertV2Row, ...],
    status: str,
) -> Decimal:
    return _count(sum(1 for row in rows if row.alert_status == status))


def _row_reason_count(
    rows: tuple[ResearchPacketResolutionAmbiguityAlertV2Row, ...],
    reason_code: str,
) -> Decimal:
    return _count(sum(1 for row in rows if reason_code in row.reason_codes))


def _vague_trigger_terms(
    packet: ResearchPacketResolutionAmbiguityEventPacket,
) -> tuple[str, ...]:
    haystack = f"{packet.event_title} {packet.resolution_rule_text}".lower()
    terms = tuple(
        term
        for term in VAGUE_TRIGGER_TERMS
        if re.search(r"(?<![a-z0-9])" + re.escape(term) + r"(?![a-z0-9])", haystack)
    )
    return terms


def _count(value: int) -> Decimal:
    return Decimal(value).quantize(COUNT_QUANTUM)


def _age_seconds(generated_at: datetime, observed_at: datetime) -> Decimal:
    if observed_at > generated_at:
        raise ValueError("observed_at must not be in the future")
    delta = generated_at - observed_at
    seconds = Decimal(delta.days * 86400 + delta.seconds)
    microseconds = Decimal(delta.microseconds) / Decimal("1000000")
    return _normalize_age_seconds("age_seconds", seconds + microseconds)


def _normalize_nonnegative_count(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    quantized = value.quantize(COUNT_QUANTUM)
    if quantized != value:
        raise ValueError(f"{field_name} must be integral")
    if quantized < ZERO_COUNT:
        raise ValueError(f"{field_name} must be nonnegative")
    return quantized


def _normalize_ratio(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    if value < ZERO_RATIO or value > ONE_RATIO:
        raise ValueError(f"{field_name} must be between 0 and 1")
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(RATIO_QUANTUM)


def _normalize_positive_age_seconds(field_name: str, value: object) -> Decimal:
    normalized = _normalize_age_seconds(field_name, value)
    if normalized <= ZERO_COUNT:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _normalize_age_seconds(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    if value < ZERO_COUNT:
        raise ValueError(f"{field_name} must be nonnegative")
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(AGE_QUANTUM)


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _normalize_source_families(value: object) -> tuple[str, ...]:
    source_families = _normalize_string_tuple(
        "source_families",
        value,
        allow_empty=True,
    )
    for source_family in source_families:
        _require_member("source_families", source_family, SOURCE_FAMILY_ROLES)
    return source_families


def _normalize_string_tuple(
    field_name: str,
    value: object,
    *,
    allow_empty: bool,
) -> tuple[str, ...]:
    if type(value) not in (list, tuple):
        raise ValueError(f"{field_name} must be a list or tuple")
    items = tuple(value)
    if not allow_empty and not items:
        raise ValueError(f"{field_name} must not be empty")
    seen_items: set[str] = set()
    for item in items:
        _require_canonical_string(field_name, item)
        if item in seen_items:
            raise ValueError(f"{field_name} values must be unique")
        seen_items.add(item)
    return items


def _normalize_reason_codes(
    field_name: str,
    value: object,
    allowed: tuple[str, ...],
) -> tuple[str, ...]:
    if type(value) not in (list, tuple):
        raise ValueError(f"{field_name} must be a list or tuple")
    reason_codes = tuple(value)
    if not reason_codes:
        raise ValueError(f"{field_name} must not be empty")
    for reason_code in reason_codes:
        _require_member(field_name, reason_code, allowed)
    if len(set(reason_codes)) != len(reason_codes):
        raise ValueError(f"{field_name} must be unique")
    if tuple(code for code in allowed if code in reason_codes) != reason_codes:
        raise ValueError(f"{field_name} must be deterministic")
    if reason_codes[0] in CLEAR_REASONS and len(reason_codes) != 1:
        raise ValueError(f"{field_name} clear reason must be exclusive")
    return reason_codes


def _require_member(field_name: str, value: object, allowed: tuple[str, ...]) -> None:
    if type(value) is not str or value not in allowed:
        raise ValueError(f"{field_name} must be one of {allowed}")


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")


def _require_hard_flags(label: str, value: object) -> None:
    if getattr(value, "paper_only", None) is not True:
        raise ValueError(f"paper_only must be True for {label}")
    if getattr(value, "report_only", None) is not True:
        raise ValueError(f"report_only must be True for {label}")
    if getattr(value, "readonly", None) is not True:
        raise ValueError(f"readonly must be True for {label}")


def _require_sha256(field_name: str, value: object) -> None:
    if type(value) is not str or SHA256_RE.fullmatch(value) is None:
        raise ValueError(f"{field_name} must be a sha256 hex digest")


def _derived_validation_digest(
    report: ResearchPacketResolutionAmbiguityAlertV2Report,
) -> str:
    payload = _json_ready(asdict(report))
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    return _payload_validation_digest(payload)


def _payload_validation_digest(payload: dict[str, Any]) -> str:
    digest_payload = dict(payload)
    digest_payload.pop("derived_validation_digest", None)
    encoded = json.dumps(
        digest_payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _validate_payload_digest(payload: dict[str, Any]) -> None:
    digest = payload.get("derived_validation_digest")
    _require_sha256("derived_validation_digest", digest)
    expected = _payload_validation_digest(payload)
    if digest != expected:
        raise ValueError("derived_validation_digest must match report payload")


def _json_ready(value: Any) -> Any:
    if value is None:
        return None
    if is_dataclass(value) and not isinstance(value, type):
        return _json_ready(asdict(value))
    if isinstance(value, Decimal):
        if not value.is_finite():
            raise ValueError("JSON Decimal value must be finite")
        return str(value)
    if isinstance(value, datetime):
        if type(value) is not datetime:
            raise ValueError("JSON datetime value must be a datetime")
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("JSON datetime value must be timezone-aware")
        return value.astimezone(UTC).isoformat()
    if type(value) is bool:
        return value
    if type(value) is int:
        raise ValueError("JSON numeric value must use Decimal")
    if isinstance(value, float):
        raise ValueError("JSON value must not be a float")
    if type(value) is str:
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


def _reject_unsafe_public_payload(label: str, payload: object) -> None:
    _reject_unsafe_public_keys(label, payload)
    _reject_unsafe_public_values(label, payload)


def _reject_unsafe_public_keys(label: str, payload: object) -> None:
    if is_dataclass(payload) and not isinstance(payload, type):
        _reject_unsafe_public_keys(label, asdict(payload))
        return
    if isinstance(payload, dict):
        for key, item in payload.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            if _has_unsafe_public_fragment(key):
                raise ValueError(f"unsafe public field in {label}: {key}")
            _reject_unsafe_public_keys(label, item)
        return
    if isinstance(payload, (list, tuple)):
        for item in payload:
            _reject_unsafe_public_keys(label, item)


def _reject_unsafe_public_values(label: str, payload: object) -> None:
    if is_dataclass(payload) and not isinstance(payload, type):
        _reject_unsafe_public_values(label, asdict(payload))
        return
    if type(payload) is str:
        if _has_unsafe_public_fragment(payload):
            raise ValueError(f"unsafe public value in {label}")
        return
    if isinstance(payload, dict):
        for item in payload.values():
            _reject_unsafe_public_values(label, item)
        return
    if isinstance(payload, (list, tuple)):
        for item in payload:
            _reject_unsafe_public_values(label, item)


def _has_unsafe_public_fragment(value: str) -> bool:
    return UNSAFE_PUBLIC_RE.search(value.lower()) is not None


__all__ = (
    "ALERT_STATUSES",
    "DEFAULT_MAX_RULE_TEXT_AGE_SECONDS",
    "DEFAULT_RESEARCH_PACKET_RESOLUTION_AMBIGUITY_ALERT_V2_CONFIG_VERSION",
    "REPORT_REASON_CODES",
    "ROW_REASON_CODES",
    "SOURCE_FAMILY_ROLES",
    "UNSAFE_PUBLIC_FRAGMENTS",
    "VAGUE_TRIGGER_TERMS",
    "ResearchPacketResolutionAmbiguityAlertV2Config",
    "ResearchPacketResolutionAmbiguityAlertV2Report",
    "ResearchPacketResolutionAmbiguityAlertV2Row",
    "ResearchPacketResolutionAmbiguityEventPacket",
    "build_research_packet_resolution_ambiguity_alert_v2_report",
    "research_packet_resolution_ambiguity_alert_v2_payload",
)
