"""Pure Phase 1 official resolution readiness monitor."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, InvalidOperation, ROUND_HALF_EVEN, localcontext
import hashlib
import json
from typing import Any


DEFAULT_RESEARCH_PACKET_OFFICIAL_RESOLUTION_MONITOR_V2_CONFIG_VERSION = (
    "research-packet-official-resolution-monitor-v2"
)
MONITOR_STATUSES = ("ready", "watch", "blocked")
READY_REASON_CODE = "official_resolution_ready"
NO_PACKETS_REASON_CODE = "official_resolution_monitor_no_packets"
OFFICIAL_SOURCE_MISSING_REASON_CODE = "official_source_missing"
RULE_CRITERIA_GAP_REASON_CODE = "rule_criteria_coverage_gap"
OFFICIAL_UPDATE_STALE_REASON_CODE = "official_update_stale"
CONTRADICTION_REASON_CODE = "official_resolution_contradictions_present"
EVIDENCE_CHAIN_INCOMPLETE_REASON_CODE = "evidence_chain_incomplete"
SETTLEMENT_PROXIMITY_REASON_CODE = "settlement_proximity_not_met"
ROW_REASON_CODES = (
    READY_REASON_CODE,
    OFFICIAL_SOURCE_MISSING_REASON_CODE,
    RULE_CRITERIA_GAP_REASON_CODE,
    OFFICIAL_UPDATE_STALE_REASON_CODE,
    CONTRADICTION_REASON_CODE,
    EVIDENCE_CHAIN_INCOMPLETE_REASON_CODE,
    SETTLEMENT_PROXIMITY_REASON_CODE,
)
REPORT_REASON_CODES = (
    READY_REASON_CODE,
    NO_PACKETS_REASON_CODE,
    OFFICIAL_SOURCE_MISSING_REASON_CODE,
    RULE_CRITERIA_GAP_REASON_CODE,
    OFFICIAL_UPDATE_STALE_REASON_CODE,
    CONTRADICTION_REASON_CODE,
    EVIDENCE_CHAIN_INCOMPLETE_REASON_CODE,
    SETTLEMENT_PROXIMITY_REASON_CODE,
)
BLOCKING_REASON_CODES = frozenset(
    (
        OFFICIAL_SOURCE_MISSING_REASON_CODE,
        RULE_CRITERIA_GAP_REASON_CODE,
        OFFICIAL_UPDATE_STALE_REASON_CODE,
        CONTRADICTION_REASON_CODE,
        EVIDENCE_CHAIN_INCOMPLETE_REASON_CODE,
    ),
)
STATUS_SORT_RANK = {
    "blocked": Decimal("0.000000"),
    "watch": Decimal("1.000000"),
    "ready": Decimal("2.000000"),
}
QUANTUM = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)

ROW_PUBLIC_FIELDS_WITHOUT_DIGEST = (
    "packet_id",
    "market_id",
    "official_source_count",
    "required_official_source_count",
    "rule_criteria_covered_count",
    "required_rule_criteria_count",
    "last_official_update_age_seconds",
    "max_official_update_age_seconds",
    "contradiction_count",
    "max_contradiction_count",
    "evidence_chain_complete_count",
    "required_evidence_chain_link_count",
    "seconds_until_settlement",
    "max_seconds_until_settlement",
    "official_source_available",
    "rule_criteria_covered",
    "official_update_current",
    "contradiction_clear",
    "evidence_chain_complete",
    "settlement_proximate",
    "gap_count",
    "readiness_status",
    "reason_codes",
    "paper_only",
    "report_only",
    "readonly",
)
ROW_PUBLIC_FIELDS = (*ROW_PUBLIC_FIELDS_WITHOUT_DIGEST, "derived_validation_digest")
REPORT_PUBLIC_FIELDS_WITHOUT_DIGEST = (
    "generated_at",
    "config_version",
    "status",
    "packet_count",
    "ready_count",
    "watch_count",
    "blocked_count",
    "official_source_gap_count",
    "rule_criteria_gap_count",
    "stale_update_count",
    "contradiction_packet_count",
    "evidence_chain_gap_count",
    "settlement_proximity_gap_count",
    "reason_codes",
    "rows",
    "paper_only",
    "report_only",
    "readonly",
)
REPORT_PUBLIC_FIELDS = (
    *REPORT_PUBLIC_FIELDS_WITHOUT_DIGEST,
    "derived_validation_digest",
)

__all__ = (
    "DEFAULT_RESEARCH_PACKET_OFFICIAL_RESOLUTION_MONITOR_V2_CONFIG_VERSION",
    "MONITOR_STATUSES",
    "REPORT_REASON_CODES",
    "ROW_REASON_CODES",
    "ResearchPacketOfficialResolutionMonitorV2Config",
    "ResearchPacketOfficialResolutionMonitorV2Input",
    "ResearchPacketOfficialResolutionMonitorV2Report",
    "ResearchPacketOfficialResolutionMonitorV2Row",
    "build_research_packet_official_resolution_monitor_v2_report",
    "research_packet_official_resolution_monitor_v2_payload",
)


@dataclass(frozen=True)
class ResearchPacketOfficialResolutionMonitorV2Config:
    config_version: str = DEFAULT_RESEARCH_PACKET_OFFICIAL_RESOLUTION_MONITOR_V2_CONFIG_VERSION
    required_official_source_count: Decimal = Decimal("1.000000")
    required_rule_criteria_count: Decimal = Decimal("1.000000")
    max_official_update_age_seconds: Decimal = Decimal("3600.000000")
    max_contradiction_count: Decimal = Decimal("0.000000")
    required_evidence_chain_link_count: Decimal = Decimal("1.000000")
    max_seconds_until_settlement: Decimal = Decimal("86400.000000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchPacketOfficialResolutionMonitorV2Config does not support subclassing",
        )

    def __post_init__(self) -> None:
        if type(self) is not ResearchPacketOfficialResolutionMonitorV2Config:
            raise ValueError(
                "config must be exactly ResearchPacketOfficialResolutionMonitorV2Config",
            )
        _require_canonical_string("config_version", self.config_version)
        for field_name in (
            "required_official_source_count",
            "required_rule_criteria_count",
            "required_evidence_chain_link_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_positive_whole_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "max_contradiction_count",
            _normalize_nonnegative_whole_decimal(
                "max_contradiction_count",
                self.max_contradiction_count,
            ),
        )
        for field_name in (
            "max_official_update_age_seconds",
            "max_seconds_until_settlement",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_positive_decimal(field_name, getattr(self, field_name)),
            )
        _require_hard_flags(self)


@dataclass(frozen=True)
class ResearchPacketOfficialResolutionMonitorV2Input:
    packet_id: str
    market_id: str
    official_source_count: Decimal
    rule_criteria_covered_count: Decimal
    last_official_update_age_seconds: Decimal
    contradiction_count: Decimal
    evidence_chain_complete_count: Decimal
    seconds_until_settlement: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchPacketOfficialResolutionMonitorV2Input does not support subclassing",
        )

    def __post_init__(self) -> None:
        if type(self) is not ResearchPacketOfficialResolutionMonitorV2Input:
            raise ValueError(
                "input must be exactly ResearchPacketOfficialResolutionMonitorV2Input",
            )
        _require_canonical_string("packet_id", self.packet_id)
        _require_canonical_string("market_id", self.market_id)
        for field_name in (
            "official_source_count",
            "rule_criteria_covered_count",
            "contradiction_count",
            "evidence_chain_complete_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_whole_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "last_official_update_age_seconds",
            "seconds_until_settlement",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        _require_hard_flags(self)


@dataclass(frozen=True)
class ResearchPacketOfficialResolutionMonitorV2Row:
    packet_id: str
    market_id: str
    official_source_count: Decimal
    required_official_source_count: Decimal
    rule_criteria_covered_count: Decimal
    required_rule_criteria_count: Decimal
    last_official_update_age_seconds: Decimal
    max_official_update_age_seconds: Decimal
    contradiction_count: Decimal
    max_contradiction_count: Decimal
    evidence_chain_complete_count: Decimal
    required_evidence_chain_link_count: Decimal
    seconds_until_settlement: Decimal
    max_seconds_until_settlement: Decimal
    official_source_available: bool
    rule_criteria_covered: bool
    official_update_current: bool
    contradiction_clear: bool
    evidence_chain_complete: bool
    settlement_proximate: bool
    gap_count: Decimal
    readiness_status: str
    reason_codes: tuple[str, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchPacketOfficialResolutionMonitorV2Row does not support subclassing",
        )

    def __post_init__(self) -> None:
        if type(self) is not ResearchPacketOfficialResolutionMonitorV2Row:
            raise ValueError("row must be exactly ResearchPacketOfficialResolutionMonitorV2Row")
        _require_canonical_string("packet_id", self.packet_id)
        _require_canonical_string("market_id", self.market_id)
        for field_name in (
            "official_source_count",
            "required_official_source_count",
            "rule_criteria_covered_count",
            "required_rule_criteria_count",
            "contradiction_count",
            "max_contradiction_count",
            "evidence_chain_complete_count",
            "required_evidence_chain_link_count",
            "gap_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_whole_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "last_official_update_age_seconds",
            "max_official_update_age_seconds",
            "seconds_until_settlement",
            "max_seconds_until_settlement",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "official_source_available",
            "rule_criteria_covered",
            "official_update_current",
            "contradiction_clear",
            "evidence_chain_complete",
            "settlement_proximate",
        ):
            _require_bool(field_name, getattr(self, field_name))
        _require_member("readiness_status", self.readiness_status, MONITOR_STATUSES)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, ROW_REASON_CODES),
        )
        _require_hard_flags(self)
        _validate_row_consistency(self)
        if self.derived_validation_digest == "":
            object.__setattr__(
                self,
                "derived_validation_digest",
                _row_derived_validation_digest(self),
            )
        else:
            object.__setattr__(
                self,
                "derived_validation_digest",
                _normalize_sha256("derived_validation_digest", self.derived_validation_digest),
            )
        _validate_row_digest(self)


@dataclass(frozen=True)
class ResearchPacketOfficialResolutionMonitorV2Report:
    generated_at: datetime
    config_version: str
    status: str
    packet_count: Decimal
    ready_count: Decimal
    watch_count: Decimal
    blocked_count: Decimal
    official_source_gap_count: Decimal
    rule_criteria_gap_count: Decimal
    stale_update_count: Decimal
    contradiction_packet_count: Decimal
    evidence_chain_gap_count: Decimal
    settlement_proximity_gap_count: Decimal
    reason_codes: tuple[str, ...]
    rows: tuple[ResearchPacketOfficialResolutionMonitorV2Row, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchPacketOfficialResolutionMonitorV2Report does not support subclassing",
        )

    def __post_init__(self) -> None:
        if type(self) is not ResearchPacketOfficialResolutionMonitorV2Report:
            raise ValueError(
                "report must be exactly ResearchPacketOfficialResolutionMonitorV2Report",
            )
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        _require_member("status", self.status, MONITOR_STATUSES)
        for field_name in (
            "packet_count",
            "ready_count",
            "watch_count",
            "blocked_count",
            "official_source_gap_count",
            "rule_criteria_gap_count",
            "stale_update_count",
            "contradiction_packet_count",
            "evidence_chain_gap_count",
            "settlement_proximity_gap_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_whole_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, REPORT_REASON_CODES),
        )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        _require_hard_flags(self)
        _validate_report_consistency(self)
        if self.derived_validation_digest == "":
            object.__setattr__(
                self,
                "derived_validation_digest",
                _report_derived_validation_digest(self),
            )
        else:
            object.__setattr__(
                self,
                "derived_validation_digest",
                _normalize_sha256("derived_validation_digest", self.derived_validation_digest),
            )
        _validate_report_digest(self)


def build_research_packet_official_resolution_monitor_v2_report(
    packets: list[ResearchPacketOfficialResolutionMonitorV2Input]
    | tuple[ResearchPacketOfficialResolutionMonitorV2Input, ...],
    *,
    config: ResearchPacketOfficialResolutionMonitorV2Config,
    generated_at: datetime,
) -> ResearchPacketOfficialResolutionMonitorV2Report:
    if type(config) is not ResearchPacketOfficialResolutionMonitorV2Config:
        raise ValueError("config must be a ResearchPacketOfficialResolutionMonitorV2Config")
    _require_hard_flags(config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    normalized_packets = _normalize_inputs(packets)
    rows = tuple(
        sorted(
            (_row_for_packet(packet, config=config) for packet in normalized_packets),
            key=_row_sort_key,
        ),
    )
    return ResearchPacketOfficialResolutionMonitorV2Report(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        status=_report_status(rows),
        packet_count=_count_decimal(len(rows)),
        ready_count=_status_count(rows, "ready"),
        watch_count=_status_count(rows, "watch"),
        blocked_count=_status_count(rows, "blocked"),
        official_source_gap_count=_flag_gap_count(rows, "official_source_available"),
        rule_criteria_gap_count=_flag_gap_count(rows, "rule_criteria_covered"),
        stale_update_count=_flag_gap_count(rows, "official_update_current"),
        contradiction_packet_count=_flag_gap_count(rows, "contradiction_clear"),
        evidence_chain_gap_count=_flag_gap_count(rows, "evidence_chain_complete"),
        settlement_proximity_gap_count=_flag_gap_count(rows, "settlement_proximate"),
        reason_codes=_report_reason_codes(rows),
        rows=rows,
    )


def research_packet_official_resolution_monitor_v2_payload(value: object) -> dict[str, Any]:
    if type(value) is ResearchPacketOfficialResolutionMonitorV2Report:
        _validate_report_consistency(value)
        _validate_report_digest(value)
        payload = _report_public_payload_values(value)
        payload["derived_validation_digest"] = value.derived_validation_digest
        _validate_public_report_payload(payload)
        return payload
    if type(value) is dict:
        _validate_public_report_payload(value)
        return dict(value)
    raise ValueError(
        "value must be a ResearchPacketOfficialResolutionMonitorV2Report or dict",
    )


def _row_for_packet(
    packet: ResearchPacketOfficialResolutionMonitorV2Input,
    *,
    config: ResearchPacketOfficialResolutionMonitorV2Config,
) -> ResearchPacketOfficialResolutionMonitorV2Row:
    official_source_available = (
        packet.official_source_count >= config.required_official_source_count
    )
    rule_criteria_covered = (
        packet.rule_criteria_covered_count >= config.required_rule_criteria_count
    )
    official_update_current = (
        packet.last_official_update_age_seconds <= config.max_official_update_age_seconds
    )
    contradiction_clear = packet.contradiction_count <= config.max_contradiction_count
    evidence_chain_complete = (
        packet.evidence_chain_complete_count >= config.required_evidence_chain_link_count
    )
    settlement_proximate = packet.seconds_until_settlement <= config.max_seconds_until_settlement
    reason_codes = _row_reason_codes(
        official_source_available=official_source_available,
        rule_criteria_covered=rule_criteria_covered,
        official_update_current=official_update_current,
        contradiction_clear=contradiction_clear,
        evidence_chain_complete=evidence_chain_complete,
        settlement_proximate=settlement_proximate,
    )
    return ResearchPacketOfficialResolutionMonitorV2Row(
        packet_id=packet.packet_id,
        market_id=packet.market_id,
        official_source_count=packet.official_source_count,
        required_official_source_count=config.required_official_source_count,
        rule_criteria_covered_count=packet.rule_criteria_covered_count,
        required_rule_criteria_count=config.required_rule_criteria_count,
        last_official_update_age_seconds=packet.last_official_update_age_seconds,
        max_official_update_age_seconds=config.max_official_update_age_seconds,
        contradiction_count=packet.contradiction_count,
        max_contradiction_count=config.max_contradiction_count,
        evidence_chain_complete_count=packet.evidence_chain_complete_count,
        required_evidence_chain_link_count=config.required_evidence_chain_link_count,
        seconds_until_settlement=packet.seconds_until_settlement,
        max_seconds_until_settlement=config.max_seconds_until_settlement,
        official_source_available=official_source_available,
        rule_criteria_covered=rule_criteria_covered,
        official_update_current=official_update_current,
        contradiction_clear=contradiction_clear,
        evidence_chain_complete=evidence_chain_complete,
        settlement_proximate=settlement_proximate,
        gap_count=_gap_count(
            official_source_available=official_source_available,
            rule_criteria_covered=rule_criteria_covered,
            official_update_current=official_update_current,
            contradiction_clear=contradiction_clear,
            evidence_chain_complete=evidence_chain_complete,
            settlement_proximate=settlement_proximate,
        ),
        readiness_status=_row_status(reason_codes),
        reason_codes=reason_codes,
    )


def _normalize_inputs(
    value: object,
) -> tuple[ResearchPacketOfficialResolutionMonitorV2Input, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("packets must be a list or tuple")
    packets = tuple(value)
    seen: set[tuple[str, str]] = set()
    for packet in packets:
        if type(packet) is not ResearchPacketOfficialResolutionMonitorV2Input:
            raise ValueError(
                "packets must contain ResearchPacketOfficialResolutionMonitorV2Input values",
            )
        _require_hard_flags(packet)
        key = (packet.packet_id, packet.market_id)
        if key in seen:
            raise ValueError("packets must be unique by packet_id and market_id")
        seen.add(key)
    return packets


def _normalize_rows(value: object) -> tuple[ResearchPacketOfficialResolutionMonitorV2Row, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("rows must be a list or tuple")
    rows = tuple(value)
    seen: set[tuple[str, str]] = set()
    for row in rows:
        if type(row) is not ResearchPacketOfficialResolutionMonitorV2Row:
            raise ValueError(
                "rows must contain ResearchPacketOfficialResolutionMonitorV2Row values",
            )
        _require_hard_flags(row)
        _validate_row_consistency(row)
        _validate_row_digest(row)
        key = (row.packet_id, row.market_id)
        if key in seen:
            raise ValueError("rows must be unique by packet_id and market_id")
        seen.add(key)
    if rows != tuple(sorted(rows, key=_row_sort_key)):
        raise ValueError("rows must use deterministic sequence")
    return rows


def _validate_row_consistency(row: ResearchPacketOfficialResolutionMonitorV2Row) -> None:
    if row.required_official_source_count <= ZERO:
        raise ValueError("required_official_source_count must be positive")
    if row.required_rule_criteria_count <= ZERO:
        raise ValueError("required_rule_criteria_count must be positive")
    if row.max_official_update_age_seconds <= ZERO:
        raise ValueError("max_official_update_age_seconds must be positive")
    if row.required_evidence_chain_link_count <= ZERO:
        raise ValueError("required_evidence_chain_link_count must be positive")
    if row.max_seconds_until_settlement <= ZERO:
        raise ValueError("max_seconds_until_settlement must be positive")
    expected_reason_codes = _row_reason_codes(
        official_source_available=(
            row.official_source_count >= row.required_official_source_count
        ),
        rule_criteria_covered=(
            row.rule_criteria_covered_count >= row.required_rule_criteria_count
        ),
        official_update_current=(
            row.last_official_update_age_seconds <= row.max_official_update_age_seconds
        ),
        contradiction_clear=(row.contradiction_count <= row.max_contradiction_count),
        evidence_chain_complete=(
            row.evidence_chain_complete_count >= row.required_evidence_chain_link_count
        ),
        settlement_proximate=(
            row.seconds_until_settlement <= row.max_seconds_until_settlement
        ),
    )
    if row.reason_codes != expected_reason_codes:
        raise ValueError("reason_codes must match official resolution readiness fields")
    if row.official_source_available != (
        row.official_source_count >= row.required_official_source_count
    ):
        raise ValueError("official_source_available must match official source counts")
    if row.rule_criteria_covered != (
        row.rule_criteria_covered_count >= row.required_rule_criteria_count
    ):
        raise ValueError("rule_criteria_covered must match rule criteria counts")
    if row.official_update_current != (
        row.last_official_update_age_seconds <= row.max_official_update_age_seconds
    ):
        raise ValueError("official_update_current must match update age")
    if row.contradiction_clear != (row.contradiction_count <= row.max_contradiction_count):
        raise ValueError("contradiction_clear must match contradiction counts")
    if row.evidence_chain_complete != (
        row.evidence_chain_complete_count >= row.required_evidence_chain_link_count
    ):
        raise ValueError("evidence_chain_complete must match evidence chain counts")
    if row.settlement_proximate != (
        row.seconds_until_settlement <= row.max_seconds_until_settlement
    ):
        raise ValueError("settlement_proximate must match settlement proximity")
    if row.gap_count != _gap_count(
        official_source_available=row.official_source_available,
        rule_criteria_covered=row.rule_criteria_covered,
        official_update_current=row.official_update_current,
        contradiction_clear=row.contradiction_clear,
        evidence_chain_complete=row.evidence_chain_complete,
        settlement_proximate=row.settlement_proximate,
    ):
        raise ValueError("gap_count must match readiness flags")
    if row.readiness_status != _row_status(row.reason_codes):
        raise ValueError("readiness_status must match reason_codes")


def _validate_report_consistency(report: ResearchPacketOfficialResolutionMonitorV2Report) -> None:
    if report.packet_count != _count_decimal(len(report.rows)):
        raise ValueError("packet_count must match rows")
    if report.ready_count != _status_count(report.rows, "ready"):
        raise ValueError("ready_count must match rows")
    if report.watch_count != _status_count(report.rows, "watch"):
        raise ValueError("watch_count must match rows")
    if report.blocked_count != _status_count(report.rows, "blocked"):
        raise ValueError("blocked_count must match rows")
    if report.official_source_gap_count != _flag_gap_count(
        report.rows,
        "official_source_available",
    ):
        raise ValueError("official_source_gap_count must match rows")
    if report.rule_criteria_gap_count != _flag_gap_count(
        report.rows,
        "rule_criteria_covered",
    ):
        raise ValueError("rule_criteria_gap_count must match rows")
    if report.stale_update_count != _flag_gap_count(report.rows, "official_update_current"):
        raise ValueError("stale_update_count must match rows")
    if report.contradiction_packet_count != _flag_gap_count(
        report.rows,
        "contradiction_clear",
    ):
        raise ValueError("contradiction_packet_count must match rows")
    if report.evidence_chain_gap_count != _flag_gap_count(
        report.rows,
        "evidence_chain_complete",
    ):
        raise ValueError("evidence_chain_gap_count must match rows")
    if report.settlement_proximity_gap_count != _flag_gap_count(
        report.rows,
        "settlement_proximate",
    ):
        raise ValueError("settlement_proximity_gap_count must match rows")
    if report.status != _report_status(report.rows):
        raise ValueError("status must match rows")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")


def _row_reason_codes(
    *,
    official_source_available: bool,
    rule_criteria_covered: bool,
    official_update_current: bool,
    contradiction_clear: bool,
    evidence_chain_complete: bool,
    settlement_proximate: bool,
) -> tuple[str, ...]:
    codes: list[str] = []
    if not official_source_available:
        codes.append(OFFICIAL_SOURCE_MISSING_REASON_CODE)
    if not rule_criteria_covered:
        codes.append(RULE_CRITERIA_GAP_REASON_CODE)
    if not official_update_current:
        codes.append(OFFICIAL_UPDATE_STALE_REASON_CODE)
    if not contradiction_clear:
        codes.append(CONTRADICTION_REASON_CODE)
    if not evidence_chain_complete:
        codes.append(EVIDENCE_CHAIN_INCOMPLETE_REASON_CODE)
    if not settlement_proximate:
        codes.append(SETTLEMENT_PROXIMITY_REASON_CODE)
    if not codes:
        codes.append(READY_REASON_CODE)
    return tuple(codes)


def _row_status(reason_codes: tuple[str, ...]) -> str:
    if any(reason_code in BLOCKING_REASON_CODES for reason_code in reason_codes):
        return "blocked"
    if SETTLEMENT_PROXIMITY_REASON_CODE in reason_codes:
        return "watch"
    return "ready"


def _report_status(rows: tuple[ResearchPacketOfficialResolutionMonitorV2Row, ...]) -> str:
    if not rows:
        return "blocked"
    if any(row.readiness_status == "blocked" for row in rows):
        return "blocked"
    if any(row.readiness_status == "watch" for row in rows):
        return "watch"
    return "ready"


def _report_reason_codes(
    rows: tuple[ResearchPacketOfficialResolutionMonitorV2Row, ...],
) -> tuple[str, ...]:
    if not rows:
        return (NO_PACKETS_REASON_CODE,)
    present = frozenset(
        reason_code
        for row in rows
        for reason_code in row.reason_codes
        if reason_code != READY_REASON_CODE
    )
    if not present:
        return (READY_REASON_CODE,)
    return tuple(reason_code for reason_code in REPORT_REASON_CODES if reason_code in present)


def _gap_count(
    *,
    official_source_available: bool,
    rule_criteria_covered: bool,
    official_update_current: bool,
    contradiction_clear: bool,
    evidence_chain_complete: bool,
    settlement_proximate: bool,
) -> Decimal:
    count = ZERO
    for value in (
        official_source_available,
        rule_criteria_covered,
        official_update_current,
        contradiction_clear,
        evidence_chain_complete,
        settlement_proximate,
    ):
        if value is False:
            count += ONE
    return _normalize_nonnegative_whole_decimal("gap_count", count)


def _row_sort_key(
    row: ResearchPacketOfficialResolutionMonitorV2Row,
) -> tuple[Decimal, Decimal, Decimal, str, str]:
    return (
        STATUS_SORT_RANK[row.readiness_status],
        -row.gap_count,
        row.seconds_until_settlement,
        row.packet_id,
        row.market_id,
    )


def _status_count(
    rows: tuple[ResearchPacketOfficialResolutionMonitorV2Row, ...],
    status: str,
) -> Decimal:
    return _count_decimal(sum(1 for row in rows if row.readiness_status == status))


def _flag_gap_count(
    rows: tuple[ResearchPacketOfficialResolutionMonitorV2Row, ...],
    flag_name: str,
) -> Decimal:
    return _count_decimal(sum(1 for row in rows if getattr(row, flag_name) is False))


def _row_public_payload_values(
    row: ResearchPacketOfficialResolutionMonitorV2Row,
) -> dict[str, Any]:
    return {
        "packet_id": row.packet_id,
        "market_id": row.market_id,
        "official_source_count": _decimal_payload(row.official_source_count),
        "required_official_source_count": _decimal_payload(row.required_official_source_count),
        "rule_criteria_covered_count": _decimal_payload(row.rule_criteria_covered_count),
        "required_rule_criteria_count": _decimal_payload(row.required_rule_criteria_count),
        "last_official_update_age_seconds": _decimal_payload(
            row.last_official_update_age_seconds,
        ),
        "max_official_update_age_seconds": _decimal_payload(
            row.max_official_update_age_seconds,
        ),
        "contradiction_count": _decimal_payload(row.contradiction_count),
        "max_contradiction_count": _decimal_payload(row.max_contradiction_count),
        "evidence_chain_complete_count": _decimal_payload(row.evidence_chain_complete_count),
        "required_evidence_chain_link_count": _decimal_payload(
            row.required_evidence_chain_link_count,
        ),
        "seconds_until_settlement": _decimal_payload(row.seconds_until_settlement),
        "max_seconds_until_settlement": _decimal_payload(row.max_seconds_until_settlement),
        "official_source_available": row.official_source_available,
        "rule_criteria_covered": row.rule_criteria_covered,
        "official_update_current": row.official_update_current,
        "contradiction_clear": row.contradiction_clear,
        "evidence_chain_complete": row.evidence_chain_complete,
        "settlement_proximate": row.settlement_proximate,
        "gap_count": _decimal_payload(row.gap_count),
        "readiness_status": row.readiness_status,
        "reason_codes": list(row.reason_codes),
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }


def _row_public_payload_with_digest(
    row: ResearchPacketOfficialResolutionMonitorV2Row,
) -> dict[str, Any]:
    payload = _row_public_payload_values(row)
    payload["derived_validation_digest"] = row.derived_validation_digest
    return payload


def _report_public_payload_values(
    report: ResearchPacketOfficialResolutionMonitorV2Report,
) -> dict[str, Any]:
    return {
        "generated_at": report.generated_at.isoformat(),
        "config_version": report.config_version,
        "status": report.status,
        "packet_count": _decimal_payload(report.packet_count),
        "ready_count": _decimal_payload(report.ready_count),
        "watch_count": _decimal_payload(report.watch_count),
        "blocked_count": _decimal_payload(report.blocked_count),
        "official_source_gap_count": _decimal_payload(report.official_source_gap_count),
        "rule_criteria_gap_count": _decimal_payload(report.rule_criteria_gap_count),
        "stale_update_count": _decimal_payload(report.stale_update_count),
        "contradiction_packet_count": _decimal_payload(report.contradiction_packet_count),
        "evidence_chain_gap_count": _decimal_payload(report.evidence_chain_gap_count),
        "settlement_proximity_gap_count": _decimal_payload(
            report.settlement_proximity_gap_count,
        ),
        "reason_codes": list(report.reason_codes),
        "rows": [_row_public_payload_with_digest(row) for row in report.rows],
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }


def _row_derived_validation_digest(row: ResearchPacketOfficialResolutionMonitorV2Row) -> str:
    return _digest_payload(
        "research_packet_official_resolution_monitor_v2_row",
        _row_public_payload_values(row),
    )


def _report_derived_validation_digest(
    report: ResearchPacketOfficialResolutionMonitorV2Report,
) -> str:
    return _digest_payload(
        "research_packet_official_resolution_monitor_v2_report",
        _report_public_payload_values(report),
    )


def _public_row_digest(payload: dict[str, Any]) -> str:
    values = {field_name: payload[field_name] for field_name in ROW_PUBLIC_FIELDS_WITHOUT_DIGEST}
    return _digest_payload("research_packet_official_resolution_monitor_v2_row", values)


def _public_report_digest(payload: dict[str, Any]) -> str:
    values = {
        field_name: payload[field_name]
        for field_name in REPORT_PUBLIC_FIELDS_WITHOUT_DIGEST
    }
    return _digest_payload("research_packet_official_resolution_monitor_v2_report", values)


def _digest_payload(label: str, payload: dict[str, Any]) -> str:
    normalized = _json_ready(payload)
    return hashlib.sha256(
        json.dumps(
            {"label": label, "payload": normalized},
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8"),
    ).hexdigest()


def _validate_row_digest(row: ResearchPacketOfficialResolutionMonitorV2Row) -> None:
    if row.derived_validation_digest != _row_derived_validation_digest(row):
        raise ValueError("derived_validation_digest must match row fields")


def _validate_report_digest(report: ResearchPacketOfficialResolutionMonitorV2Report) -> None:
    if report.derived_validation_digest != _report_derived_validation_digest(report):
        raise ValueError("derived_validation_digest must match report fields")


def _validate_public_report_payload(payload: dict[str, Any]) -> None:
    if type(payload) is not dict:
        raise ValueError("payload must be a dict")
    _require_exact_payload_fields("payload", payload, REPORT_PUBLIC_FIELDS)
    _require_datetime_payload("generated_at", payload["generated_at"])
    _require_canonical_string("config_version", payload["config_version"])
    _require_member("status", payload["status"], MONITOR_STATUSES)
    for field_name in (
        "packet_count",
        "ready_count",
        "watch_count",
        "blocked_count",
        "official_source_gap_count",
        "rule_criteria_gap_count",
        "stale_update_count",
        "contradiction_packet_count",
        "evidence_chain_gap_count",
        "settlement_proximity_gap_count",
    ):
        _require_decimal_payload(field_name, payload[field_name], whole=True)
    _require_public_reason_codes("reason_codes", payload["reason_codes"], REPORT_REASON_CODES)
    rows = _validate_public_rows(payload["rows"])
    _require_payload_hard_flags("payload", payload)
    _reject_public_numbers(payload)
    provided_digest = _normalize_sha256(
        "derived_validation_digest",
        payload["derived_validation_digest"],
    )
    if provided_digest != _public_report_digest(payload):
        raise ValueError("derived_validation_digest must match public payload")
    _validate_public_report_counts(payload, rows)


def _validate_public_rows(value: object) -> tuple[dict[str, Any], ...]:
    if type(value) is not list:
        raise ValueError("rows must be a list")
    rows = tuple(value)
    seen: set[tuple[str, str]] = set()
    previous_key: tuple[Decimal, Decimal, Decimal, str, str] | None = None
    for row in rows:
        if type(row) is not dict:
            raise ValueError("rows must contain dict values")
        _validate_public_row_payload(row)
        key = (row["packet_id"], row["market_id"])
        if key in seen:
            raise ValueError("rows must be unique by packet_id and market_id")
        seen.add(key)
        sort_key = _public_row_sort_key(row)
        if previous_key is not None and previous_key > sort_key:
            raise ValueError("rows must use deterministic sequence")
        previous_key = sort_key
    return rows


def _validate_public_row_payload(payload: dict[str, Any]) -> None:
    _require_exact_payload_fields("row", payload, ROW_PUBLIC_FIELDS)
    _require_canonical_string("packet_id", payload["packet_id"])
    _require_canonical_string("market_id", payload["market_id"])
    count_fields = (
        "official_source_count",
        "required_official_source_count",
        "rule_criteria_covered_count",
        "required_rule_criteria_count",
        "contradiction_count",
        "max_contradiction_count",
        "evidence_chain_complete_count",
        "required_evidence_chain_link_count",
        "gap_count",
    )
    seconds_fields = (
        "last_official_update_age_seconds",
        "max_official_update_age_seconds",
        "seconds_until_settlement",
        "max_seconds_until_settlement",
    )
    for field_name in count_fields:
        _require_decimal_payload(field_name, payload[field_name], whole=True)
    for field_name in seconds_fields:
        _require_decimal_payload(field_name, payload[field_name], whole=False)
    for field_name in (
        "official_source_available",
        "rule_criteria_covered",
        "official_update_current",
        "contradiction_clear",
        "evidence_chain_complete",
        "settlement_proximate",
    ):
        _require_bool(field_name, payload[field_name])
    _require_member("readiness_status", payload["readiness_status"], MONITOR_STATUSES)
    _require_public_reason_codes("reason_codes", payload["reason_codes"], ROW_REASON_CODES)
    _require_payload_hard_flags("row", payload)
    if _normalize_sha256(
        "derived_validation_digest",
        payload["derived_validation_digest"],
    ) != _public_row_digest(payload):
        raise ValueError("derived_validation_digest must match row payload")
    _validate_public_row_consistency(payload)


def _validate_public_row_consistency(payload: dict[str, Any]) -> None:
    official_source_count = _require_decimal_payload(
        "official_source_count",
        payload["official_source_count"],
        whole=True,
    )
    required_official_source_count = _require_decimal_payload(
        "required_official_source_count",
        payload["required_official_source_count"],
        whole=True,
    )
    rule_criteria_covered_count = _require_decimal_payload(
        "rule_criteria_covered_count",
        payload["rule_criteria_covered_count"],
        whole=True,
    )
    required_rule_criteria_count = _require_decimal_payload(
        "required_rule_criteria_count",
        payload["required_rule_criteria_count"],
        whole=True,
    )
    last_official_update_age_seconds = _require_decimal_payload(
        "last_official_update_age_seconds",
        payload["last_official_update_age_seconds"],
        whole=False,
    )
    max_official_update_age_seconds = _require_decimal_payload(
        "max_official_update_age_seconds",
        payload["max_official_update_age_seconds"],
        whole=False,
    )
    contradiction_count = _require_decimal_payload(
        "contradiction_count",
        payload["contradiction_count"],
        whole=True,
    )
    max_contradiction_count = _require_decimal_payload(
        "max_contradiction_count",
        payload["max_contradiction_count"],
        whole=True,
    )
    evidence_chain_complete_count = _require_decimal_payload(
        "evidence_chain_complete_count",
        payload["evidence_chain_complete_count"],
        whole=True,
    )
    required_evidence_chain_link_count = _require_decimal_payload(
        "required_evidence_chain_link_count",
        payload["required_evidence_chain_link_count"],
        whole=True,
    )
    seconds_until_settlement = _require_decimal_payload(
        "seconds_until_settlement",
        payload["seconds_until_settlement"],
        whole=False,
    )
    max_seconds_until_settlement = _require_decimal_payload(
        "max_seconds_until_settlement",
        payload["max_seconds_until_settlement"],
        whole=False,
    )
    flags = {
        "official_source_available": (
            official_source_count >= required_official_source_count
        ),
        "rule_criteria_covered": (
            rule_criteria_covered_count >= required_rule_criteria_count
        ),
        "official_update_current": (
            last_official_update_age_seconds <= max_official_update_age_seconds
        ),
        "contradiction_clear": contradiction_count <= max_contradiction_count,
        "evidence_chain_complete": (
            evidence_chain_complete_count >= required_evidence_chain_link_count
        ),
        "settlement_proximate": seconds_until_settlement <= max_seconds_until_settlement,
    }
    for field_name, expected in flags.items():
        if payload[field_name] is not expected:
            raise ValueError(f"{field_name} must match public row values")
    expected_reasons = _row_reason_codes(**flags)
    if tuple(payload["reason_codes"]) != expected_reasons:
        raise ValueError("reason_codes must match public row values")
    if payload["readiness_status"] != _row_status(expected_reasons):
        raise ValueError("readiness_status must match public row values")
    if _require_decimal_payload("gap_count", payload["gap_count"], whole=True) != _gap_count(
        **flags,
    ):
        raise ValueError("gap_count must match public row values")


def _validate_public_report_counts(
    payload: dict[str, Any],
    rows: tuple[dict[str, Any], ...],
) -> None:
    if _require_decimal_payload(
        "packet_count",
        payload["packet_count"],
        whole=True,
    ) != _count_decimal(len(rows)):
        raise ValueError("packet_count must match rows")
    for field_name, status in (
        ("ready_count", "ready"),
        ("watch_count", "watch"),
        ("blocked_count", "blocked"),
    ):
        if _require_decimal_payload(field_name, payload[field_name], whole=True) != _count_decimal(
            sum(1 for row in rows if row["readiness_status"] == status),
        ):
            raise ValueError(f"{field_name} must match rows")
    for field_name, row_field in (
        ("official_source_gap_count", "official_source_available"),
        ("rule_criteria_gap_count", "rule_criteria_covered"),
        ("stale_update_count", "official_update_current"),
        ("contradiction_packet_count", "contradiction_clear"),
        ("evidence_chain_gap_count", "evidence_chain_complete"),
        ("settlement_proximity_gap_count", "settlement_proximate"),
    ):
        if _require_decimal_payload(field_name, payload[field_name], whole=True) != _count_decimal(
            sum(1 for row in rows if row[row_field] is False),
        ):
            raise ValueError(f"{field_name} must match rows")
    expected_status = _public_report_status(rows)
    if payload["status"] != expected_status:
        raise ValueError("status must match rows")
    expected_reasons = _public_report_reason_codes(rows)
    if tuple(payload["reason_codes"]) != expected_reasons:
        raise ValueError("reason_codes must match rows")


def _public_row_sort_key(payload: dict[str, Any]) -> tuple[Decimal, Decimal, Decimal, str, str]:
    return (
        STATUS_SORT_RANK[payload["readiness_status"]],
        -_require_decimal_payload("gap_count", payload["gap_count"], whole=True),
        _require_decimal_payload(
            "seconds_until_settlement",
            payload["seconds_until_settlement"],
            whole=False,
        ),
        payload["packet_id"],
        payload["market_id"],
    )


def _public_report_status(rows: tuple[dict[str, Any], ...]) -> str:
    if not rows:
        return "blocked"
    if any(row["readiness_status"] == "blocked" for row in rows):
        return "blocked"
    if any(row["readiness_status"] == "watch" for row in rows):
        return "watch"
    return "ready"


def _public_report_reason_codes(rows: tuple[dict[str, Any], ...]) -> tuple[str, ...]:
    if not rows:
        return (NO_PACKETS_REASON_CODE,)
    present = frozenset(
        reason_code
        for row in rows
        for reason_code in row["reason_codes"]
        if reason_code != READY_REASON_CODE
    )
    if not present:
        return (READY_REASON_CODE,)
    return tuple(reason_code for reason_code in REPORT_REASON_CODES if reason_code in present)


def _count_decimal(value: int) -> Decimal:
    if type(value) is not int or value < 0:
        raise ValueError("count must be a nonnegative int")
    return Decimal(value).quantize(QUANTUM)


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str or not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")


def _require_bool(field_name: str, value: object) -> None:
    if type(value) is not bool:
        raise ValueError(f"{field_name} must be a bool")


def _require_member(
    field_name: str,
    value: object,
    allowed_values: tuple[str, ...],
) -> None:
    if type(value) is not str or value not in allowed_values:
        expected = ", ".join(allowed_values)
        raise ValueError(f"{field_name} must be one of: {expected}")


def _require_hard_flags(value: object) -> None:
    if getattr(value, "paper_only") is not True:
        raise ValueError("paper_only must be True")
    if getattr(value, "report_only") is not True:
        raise ValueError("report_only must be True")
    if getattr(value, "readonly") is not True:
        raise ValueError("readonly must be True")


def _require_payload_hard_flags(label: str, payload: dict[str, Any]) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if payload.get(field_name) is not True:
            raise ValueError(f"{field_name} must be True for {label}")


def _normalize_nonnegative_whole_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_nonnegative_decimal(field_name, value)
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{field_name} must be a whole Decimal")
    return normalized


def _normalize_positive_whole_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_nonnegative_whole_decimal(field_name, value)
    if normalized <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _normalize_positive_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_nonnegative_decimal(field_name, value)
    if normalized <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _normalize_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    with localcontext(DECIMAL_CONTEXT):
        try:
            return value.quantize(QUANTUM)
        except InvalidOperation as exc:
            raise ValueError(f"{field_name} must be quantizable") from exc


def _decimal_payload(value: Decimal) -> str:
    if type(value) is not Decimal:
        raise ValueError("payload value must be a Decimal")
    if not value.is_finite():
        raise ValueError("payload Decimal must be finite")
    return str(value.quantize(QUANTUM))


def _require_decimal_payload(field_name: str, value: object, *, whole: bool) -> Decimal:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a Decimal string")
    try:
        parsed = Decimal(value)
    except InvalidOperation as exc:
        raise ValueError(f"{field_name} must be a Decimal string") from exc
    normalized = _normalize_nonnegative_decimal(field_name, parsed)
    if _decimal_payload(normalized) != value:
        raise ValueError(f"{field_name} must use normalized Decimal string format")
    if whole and normalized != normalized.to_integral_value():
        raise ValueError(f"{field_name} must be a whole Decimal string")
    return normalized


def _normalize_sha256(field_name: str, value: object) -> str:
    if type(value) is not str or len(value) != 64:
        raise ValueError(f"{field_name} must be a sha256 digest")
    if any(character not in "0123456789abcdef" for character in value):
        raise ValueError(f"{field_name} must be a sha256 digest")
    return value


def _require_datetime_payload(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be an ISO datetime string")
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError as exc:
        raise ValueError(f"{field_name} must be an ISO datetime string") from exc
    if parsed.tzinfo is None:
        raise ValueError(f"{field_name} must include timezone")
    if parsed.astimezone(UTC).isoformat() != value:
        raise ValueError(f"{field_name} must be normalized to UTC")


def _require_public_reason_codes(
    field_name: str,
    value: object,
    allowed_values: tuple[str, ...],
) -> tuple[str, ...]:
    if type(value) is not list:
        raise ValueError(f"{field_name} must be a list")
    normalized = tuple(value)
    _normalize_reason_codes(field_name, normalized, allowed_values)
    return normalized


def _normalize_reason_codes(
    field_name: str,
    value: object,
    allowed_values: tuple[str, ...],
) -> tuple[str, ...]:
    if type(value) not in (list, tuple):
        raise ValueError(f"{field_name} must be a list or tuple")
    reason_codes = tuple(value)
    if not reason_codes:
        raise ValueError(f"{field_name} must not be empty")
    seen: set[str] = set()
    for reason_code in reason_codes:
        _require_member(field_name, reason_code, allowed_values)
        if reason_code in seen:
            raise ValueError(f"{field_name} must be unique")
        seen.add(reason_code)
    expected = tuple(reason_code for reason_code in allowed_values if reason_code in seen)
    if reason_codes != expected:
        raise ValueError(f"{field_name} must use deterministic sequence")
    return reason_codes


def _require_exact_payload_fields(
    label: str,
    payload: dict[str, Any],
    field_names: tuple[str, ...],
) -> None:
    expected = set(field_names)
    actual = set(payload)
    if actual != expected:
        missing = sorted(expected - actual)
        if missing:
            raise ValueError(f"{missing[0]} is required in {label}")
        extra = sorted(actual - expected)
        raise ValueError(f"unexpected field in {label}: {extra[0]}")


def _reject_public_numbers(value: object) -> None:
    if type(value) is bool or value is None:
        return
    if type(value) in (int, float, Decimal):
        raise ValueError("public payload must use Decimal strings")
    if type(value) is dict:
        for item in value.values():
            _reject_public_numbers(item)
    if type(value) in (list, tuple):
        for item in value:
            _reject_public_numbers(item)


def _json_ready(value: Any) -> Any:
    if type(value) in (str, bool) or value is None:
        return value
    if type(value) is Decimal:
        return _decimal_payload(value)
    if isinstance(value, datetime):
        return value.astimezone(UTC).isoformat()
    if type(value) is dict:
        ready: dict[str, Any] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            ready[key] = _json_ready(item)
        return ready
    if type(value) in (list, tuple):
        return [_json_ready(item) for item in value]
    if type(value) in (int, float):
        raise ValueError("JSON value must not be numeric")
    raise ValueError("JSON value is unsupported")
