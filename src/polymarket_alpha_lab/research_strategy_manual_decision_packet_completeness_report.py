"""Pure manual decision packet completeness report."""

from __future__ import annotations

import json
from collections.abc import Iterable, Mapping
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
from typing import Any


__all__ = (
    "DEFAULT_RESEARCH_STRATEGY_MANUAL_DECISION_PACKET_COMPLETENESS_REPORT_CONFIG_VERSION",
    "RESEARCH_STRATEGY_MANUAL_DECISION_PACKET_COMPLETENESS_STATUSES",
    "ResearchStrategyManualDecisionPacketCompletenessConfig",
    "ResearchStrategyManualDecisionPacketCompletenessReport",
    "ResearchStrategyManualDecisionPacketCompletenessRow",
    "ResearchStrategyManualDecisionPacketInput",
    "build_research_strategy_manual_decision_packet_completeness_report",
    "research_strategy_manual_decision_packet_completeness_report_digest",
    "research_strategy_manual_decision_packet_completeness_report_payload",
)


DEFAULT_RESEARCH_STRATEGY_MANUAL_DECISION_PACKET_COMPLETENESS_REPORT_CONFIG_VERSION = (
    "research-strategy-manual-decision-packet-completeness-report-v0"
)

QUANTUM = Decimal("0.000001")
COUNT_QUANTUM = Decimal("1.000000")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
EIGHT = Decimal("8.000000")
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
PHASE_FLAG_FIELDS = ("paper_only", "report_only", "readonly")
RESEARCH_STRATEGY_MANUAL_DECISION_PACKET_COMPLETENESS_STATUSES = (
    "pass",
    "watch",
    "block",
)
PUBLIC_STATUSES = RESEARCH_STRATEGY_MANUAL_DECISION_PACKET_COMPLETENESS_STATUSES
STATUS_WEIGHT = {
    "block": Decimal("0.000000"),
    "watch": Decimal("1.000000"),
    "pass": Decimal("2.000000"),
}
NO_PACKETS_REASON = "manual_decision_packet_completeness_no_packets"
SUMMARY_KEYS = (
    "generated_at",
    "config_version",
    "packet_count",
    "pass_count",
    "watch_count",
    "block_count",
    "average_completeness_score",
    "min_completeness_score",
    "status",
    "manual_decision_review_state",
    "reason_codes",
    "validation_digest",
    "paper_only",
    "report_only",
    "readonly",
)
REPORT_PAYLOAD_KEYS = (
    "generated_at",
    "config_version",
    "packet_count",
    "pass_count",
    "watch_count",
    "block_count",
    "average_completeness_score",
    "min_completeness_score",
    "status",
    "manual_decision_review_state",
    "reason_codes",
    "rows",
    "validation_digest",
    "paper_only",
    "report_only",
    "readonly",
)
ROW_PAYLOAD_KEYS = (
    "row_number",
    "public_packet_hash",
    "evidence_item_count",
    "independent_source_count",
    "evidence_coverage_ratio",
    "independent_source_ratio",
    "evidence_summary_score",
    "cost_summary_score",
    "risk_summary_score",
    "resolution_summary_score",
    "team_memory_summary_score",
    "update_trigger_summary_score",
    "unresolved_summary_gap_count",
    "completeness_score",
    "status",
    "manual_decision_review_state",
    "reason_codes",
    "validation_digest",
    "paper_only",
    "report_only",
    "readonly",
)
SUMMARY_SCORE_FIELDS = (
    "evidence_summary_score",
    "cost_summary_score",
    "risk_summary_score",
    "resolution_summary_score",
    "team_memory_summary_score",
    "update_trigger_summary_score",
)
SUMMARY_REASON_PREFIXES = (
    "evidence_summary",
    "cost_summary",
    "risk_summary",
    "resolution_summary",
    "team_memory_summary",
    "update_trigger_summary",
)
REASON_PRIORITY = (
    "evidence_item_count_block",
    "independent_source_count_block",
    "evidence_summary_block",
    "cost_summary_block",
    "risk_summary_block",
    "resolution_summary_block",
    "team_memory_summary_block",
    "update_trigger_summary_block",
    "unresolved_summary_gap_block",
    "manual_decision_packet_completeness_block",
    "evidence_item_count_watch",
    "independent_source_count_watch",
    "evidence_summary_watch",
    "cost_summary_watch",
    "risk_summary_watch",
    "resolution_summary_watch",
    "team_memory_summary_watch",
    "update_trigger_summary_watch",
    "unresolved_summary_gap_watch",
    "manual_decision_packet_completeness_watch",
    "manual_decision_packet_completeness_pass",
    NO_PACKETS_REASON,
)
UNSAFE_TEXT_FRAGMENTS = (
    "li" "ve",
    "au" "th",
    "wal" "let",
    "bro" "ker",
    "or" "der",
    "can" "cel",
    "re" "place",
    "ex" "change",
    "private" "_" "key",
    "api" "_" "key",
    "sec" "ret",
    "mar" "ket" "_" "id",
    "can" "didate" "_" "id",
    "mar" "ket" "_" "s" "lug",
    "s" "lug",
    "ques" "tion",
    "source" "_" "u" "rl",
    "source" "_" "text",
    "d" "sn",
    "ta" "ble",
    "to" "ken",
    "po" "sition",
    "b" "uy",
    "se" "ll",
    "reco" "mmend",
    "siz" "ing",
    "data" "base",
    "net" "work",
    "req" "uests",
    "ht" "tp",
    "sock" "et",
    "sub" "process",
    "tr" "ade",
    "://",
)


class _FinalDataclass:
    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        for base in cls.__bases__:
            if base is not _FinalDataclass and issubclass(base, _FinalDataclass):
                raise TypeError(f"{base.__name__} may not be subclassed")


@dataclass(frozen=True)
class ResearchStrategyManualDecisionPacketCompletenessConfig(_FinalDataclass):
    config_version: str = (
        DEFAULT_RESEARCH_STRATEGY_MANUAL_DECISION_PACKET_COMPLETENESS_REPORT_CONFIG_VERSION
    )
    min_evidence_item_count: Decimal = Decimal("4.000000")
    evidence_item_count_pass_floor: Decimal = Decimal("6.000000")
    min_independent_source_count: Decimal = Decimal("2.000000")
    independent_source_count_pass_floor: Decimal = Decimal("3.000000")
    summary_watch_floor: Decimal = Decimal("0.700000")
    summary_block_floor: Decimal = Decimal("0.500000")
    unresolved_summary_gap_watch_ceiling: Decimal = Decimal("0.000000")
    unresolved_summary_gap_block_ceiling: Decimal = Decimal("2.000000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchStrategyManualDecisionPacketCompletenessConfig,
            "config",
        )
        _require_public_text("config_version", self.config_version)
        for field_name in (
            "min_evidence_item_count",
            "evidence_item_count_pass_floor",
            "min_independent_source_count",
            "independent_source_count_pass_floor",
            "unresolved_summary_gap_watch_ceiling",
            "unresolved_summary_gap_block_ceiling",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_count(field_name, getattr(self, field_name)),
            )
        for field_name in ("summary_watch_floor", "summary_block_floor"):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        _require_at_least(
            "evidence_item_count_pass_floor",
            self.evidence_item_count_pass_floor,
            self.min_evidence_item_count,
        )
        _require_at_least(
            "independent_source_count_pass_floor",
            self.independent_source_count_pass_floor,
            self.min_independent_source_count,
        )
        _require_at_least(
            "summary_watch_floor",
            self.summary_watch_floor,
            self.summary_block_floor,
        )
        _require_at_most(
            "unresolved_summary_gap_watch_ceiling",
            self.unresolved_summary_gap_watch_ceiling,
            self.unresolved_summary_gap_block_ceiling,
        )
        _require_hard_phase_flags("config", self)


@dataclass(frozen=True)
class ResearchStrategyManualDecisionPacketInput(_FinalDataclass):
    internal_packet_key: str
    evidence_item_count: Decimal
    independent_source_count: Decimal
    evidence_summary_score: Decimal
    cost_summary_score: Decimal
    risk_summary_score: Decimal
    resolution_summary_score: Decimal
    team_memory_summary_score: Decimal
    update_trigger_summary_score: Decimal
    unresolved_summary_gap_count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchStrategyManualDecisionPacketInput, "packet")
        _require_text("internal_packet_key", self.internal_packet_key)
        for field_name in ("evidence_item_count", "independent_source_count"):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_count(field_name, getattr(self, field_name)),
            )
        if self.independent_source_count > self.evidence_item_count:
            raise ValueError("independent_source_count must not exceed evidence_item_count")
        for field_name in SUMMARY_SCORE_FIELDS:
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "unresolved_summary_gap_count",
            _normalize_nonnegative_count(
                "unresolved_summary_gap_count",
                self.unresolved_summary_gap_count,
            ),
        )
        _require_hard_phase_flags("packet", self)


@dataclass(frozen=True)
class ResearchStrategyManualDecisionPacketCompletenessRow(_FinalDataclass):
    row_number: Decimal
    public_packet_hash: str
    evidence_item_count: Decimal
    independent_source_count: Decimal
    evidence_coverage_ratio: Decimal
    independent_source_ratio: Decimal
    evidence_summary_score: Decimal
    cost_summary_score: Decimal
    risk_summary_score: Decimal
    resolution_summary_score: Decimal
    team_memory_summary_score: Decimal
    update_trigger_summary_score: Decimal
    unresolved_summary_gap_count: Decimal
    completeness_score: Decimal
    status: str
    manual_decision_review_state: str
    reason_codes: tuple[str, ...]
    validation_digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchStrategyManualDecisionPacketCompletenessRow,
            "row",
        )
        object.__setattr__(
            self,
            "row_number",
            _normalize_positive_count("row_number", self.row_number),
        )
        _require_public_hash("public_packet_hash", self.public_packet_hash)
        for field_name in ("evidence_item_count", "independent_source_count"):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_count(field_name, getattr(self, field_name)),
            )
        if self.independent_source_count > self.evidence_item_count:
            raise ValueError("independent_source_count must not exceed evidence_item_count")
        for field_name in (
            "evidence_coverage_ratio",
            "independent_source_ratio",
            *SUMMARY_SCORE_FIELDS,
            "completeness_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "unresolved_summary_gap_count",
            _normalize_nonnegative_count(
                "unresolved_summary_gap_count",
                self.unresolved_summary_gap_count,
            ),
        )
        _require_status("status", self.status)
        _require_manual_state("manual_decision_review_state", self.manual_decision_review_state)
        object.__setattr__(self, "reason_codes", _normalize_reason_codes(self.reason_codes))
        _require_digest("validation_digest", self.validation_digest)
        _require_hard_phase_flags("row", self)
        _validate_row(self)


@dataclass(frozen=True)
class ResearchStrategyManualDecisionPacketCompletenessReport(_FinalDataclass):
    generated_at: datetime
    config_version: str
    packet_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    average_completeness_score: Decimal | None
    min_completeness_score: Decimal | None
    status: str
    manual_decision_review_state: str
    reason_codes: tuple[str, ...]
    rows: tuple[ResearchStrategyManualDecisionPacketCompletenessRow, ...]
    validation_digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchStrategyManualDecisionPacketCompletenessReport,
            "report",
        )
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_text("config_version", self.config_version)
        for field_name in ("packet_count", "pass_count", "watch_count", "block_count"):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_count(field_name, getattr(self, field_name)),
            )
        for field_name in ("average_completeness_score", "min_completeness_score"):
            value = getattr(self, field_name)
            if value is not None:
                object.__setattr__(self, field_name, _normalize_ratio(field_name, value))
        _require_status("status", self.status)
        _require_manual_state("manual_decision_review_state", self.manual_decision_review_state)
        object.__setattr__(self, "reason_codes", _normalize_reason_codes(self.reason_codes))
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        _require_digest("validation_digest", self.validation_digest)
        _require_hard_phase_flags("report", self)
        _validate_report(self)


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


def build_research_strategy_manual_decision_packet_completeness_report(
    packets: Iterable[ResearchStrategyManualDecisionPacketInput],
    *,
    config: ResearchStrategyManualDecisionPacketCompletenessConfig,
    generated_at: datetime,
) -> ResearchStrategyManualDecisionPacketCompletenessReport:
    if type(config) is not ResearchStrategyManualDecisionPacketCompletenessConfig:
        raise ValueError(
            "config must be a ResearchStrategyManualDecisionPacketCompletenessConfig",
        )
    _require_hard_phase_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    normalized_packets = _normalize_packets(packets)
    row_values = tuple(
        sorted(
            (
                _row_values_from_packet(packet_value, config=config)
                for packet_value in normalized_packets
            ),
            key=_row_value_sort_key,
        ),
    )
    rows = tuple(
        _row_from_values(_count(index), values)
        for index, values in enumerate(row_values, start=1)
    )
    report_status = _report_status(rows)
    report_values = {
        "generated_at": generated_at_utc,
        "config_version": config.config_version,
        "packet_count": _count(len(rows)),
        "pass_count": _status_count(rows, "pass"),
        "watch_count": _status_count(rows, "watch"),
        "block_count": _status_count(rows, "block"),
        "average_completeness_score": _average_completeness_score(rows),
        "min_completeness_score": (
            None if not rows else min(row.completeness_score for row in rows)
        ),
        "status": report_status,
        "manual_decision_review_state": _manual_state(report_status),
        "reason_codes": _report_reason_codes(rows),
        "rows": rows,
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    return ResearchStrategyManualDecisionPacketCompletenessReport(
        **report_values,
        validation_digest=_validation_digest(report_values),
    )


def research_strategy_manual_decision_packet_completeness_report_payload(
    report: ResearchStrategyManualDecisionPacketCompletenessReport | dict[str, Any],
) -> dict[str, Any]:
    if type(report) is ResearchStrategyManualDecisionPacketCompletenessReport:
        _require_hard_phase_flags("report", report)
        payload = _json_ready(report)
    elif type(report) is dict:
        payload = _json_ready(report)
    else:
        raise ValueError(
            "report must be a ResearchStrategyManualDecisionPacketCompletenessReport",
        )
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    _reject_unsafe_payload(payload)
    _require_hard_phase_flags("payload", _DictFlags(payload))
    _validate_payload_digests(payload)
    return payload


def research_strategy_manual_decision_packet_completeness_report_digest(
    report: ResearchStrategyManualDecisionPacketCompletenessReport,
) -> dict[str, Any]:
    payload = research_strategy_manual_decision_packet_completeness_report_payload(report)
    return {key: payload[key] for key in SUMMARY_KEYS}


def _row_values_from_packet(
    packet: ResearchStrategyManualDecisionPacketInput,
    *,
    config: ResearchStrategyManualDecisionPacketCompletenessConfig,
) -> dict[str, Any]:
    evidence_coverage_ratio = _capped_ratio(
        packet.evidence_item_count,
        config.evidence_item_count_pass_floor,
    )
    independent_source_ratio = _capped_ratio(
        packet.independent_source_count,
        config.independent_source_count_pass_floor,
    )
    reason_codes = _row_reason_codes(packet, config=config)
    status = _row_status(reason_codes)
    completeness_score = _completeness_score(
        (
            evidence_coverage_ratio,
            independent_source_ratio,
            packet.evidence_summary_score,
            packet.cost_summary_score,
            packet.risk_summary_score,
            packet.resolution_summary_score,
            packet.team_memory_summary_score,
            packet.update_trigger_summary_score,
        ),
    )
    return {
        "public_packet_hash": _public_packet_hash(packet.internal_packet_key),
        "evidence_item_count": packet.evidence_item_count,
        "independent_source_count": packet.independent_source_count,
        "evidence_coverage_ratio": evidence_coverage_ratio,
        "independent_source_ratio": independent_source_ratio,
        "evidence_summary_score": packet.evidence_summary_score,
        "cost_summary_score": packet.cost_summary_score,
        "risk_summary_score": packet.risk_summary_score,
        "resolution_summary_score": packet.resolution_summary_score,
        "team_memory_summary_score": packet.team_memory_summary_score,
        "update_trigger_summary_score": packet.update_trigger_summary_score,
        "unresolved_summary_gap_count": packet.unresolved_summary_gap_count,
        "completeness_score": completeness_score,
        "status": status,
        "manual_decision_review_state": _manual_state(status),
        "reason_codes": reason_codes,
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }


def _row_from_values(
    row_number: Decimal,
    values: dict[str, Any],
) -> ResearchStrategyManualDecisionPacketCompletenessRow:
    row_values = {"row_number": row_number, **values}
    return ResearchStrategyManualDecisionPacketCompletenessRow(
        **row_values,
        validation_digest=_validation_digest(row_values),
    )


def _row_reason_codes(
    packet: ResearchStrategyManualDecisionPacketInput,
    *,
    config: ResearchStrategyManualDecisionPacketCompletenessConfig,
) -> tuple[str, ...]:
    block_reasons: list[str] = []
    watch_reasons: list[str] = []
    if packet.evidence_item_count < config.min_evidence_item_count:
        block_reasons.append("evidence_item_count_block")
    elif packet.evidence_item_count < config.evidence_item_count_pass_floor:
        watch_reasons.append("evidence_item_count_watch")
    if packet.independent_source_count < config.min_independent_source_count:
        block_reasons.append("independent_source_count_block")
    elif packet.independent_source_count < config.independent_source_count_pass_floor:
        watch_reasons.append("independent_source_count_watch")
    for field_name, reason_prefix in zip(
        SUMMARY_SCORE_FIELDS,
        SUMMARY_REASON_PREFIXES,
        strict=True,
    ):
        score = getattr(packet, field_name)
        if score < config.summary_block_floor:
            block_reasons.append(f"{reason_prefix}_block")
        elif score < config.summary_watch_floor:
            watch_reasons.append(f"{reason_prefix}_watch")
    if packet.unresolved_summary_gap_count >= config.unresolved_summary_gap_block_ceiling:
        block_reasons.append("unresolved_summary_gap_block")
    elif packet.unresolved_summary_gap_count > config.unresolved_summary_gap_watch_ceiling:
        watch_reasons.append("unresolved_summary_gap_watch")
    reasons = tuple(block_reasons + watch_reasons)
    if not reasons:
        reasons = ("manual_decision_packet_completeness_pass",)
    return _normalize_reason_codes(reasons)


def _row_status(reason_codes: tuple[str, ...]) -> str:
    if any(reason_code.endswith("_block") for reason_code in reason_codes):
        return "block"
    if any(reason_code.endswith("_watch") for reason_code in reason_codes):
        return "watch"
    return "pass"


def _report_status(
    rows: tuple[ResearchStrategyManualDecisionPacketCompletenessRow, ...],
) -> str:
    if not rows:
        return "block"
    if any(row.status == "block" for row in rows):
        return "block"
    if any(row.status == "watch" for row in rows):
        return "watch"
    return "pass"


def _manual_state(status: str) -> str:
    if status == "block":
        return "manual_decision_review_block"
    if status == "watch":
        return "manual_decision_review_watch"
    return "manual_decision_review_ready"


def _report_reason_codes(
    rows: tuple[ResearchStrategyManualDecisionPacketCompletenessRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return (NO_PACKETS_REASON,)
    status = _report_status(rows)
    values = tuple(
        reason
        for row in rows
        for reason in row.reason_codes
        if reason != "manual_decision_packet_completeness_pass"
    )
    return _normalize_reason_codes((*values, f"manual_decision_packet_completeness_{status}"))


def _completeness_score(values: tuple[Decimal, ...]) -> Decimal:
    return _ratio(_sum_decimal(values), EIGHT)


def _average_completeness_score(
    rows: tuple[ResearchStrategyManualDecisionPacketCompletenessRow, ...],
) -> Decimal | None:
    if not rows:
        return None
    return _ratio(_sum_decimal(tuple(row.completeness_score for row in rows)), _count(len(rows)))


def _normalize_packets(
    packets: Iterable[ResearchStrategyManualDecisionPacketInput],
) -> tuple[ResearchStrategyManualDecisionPacketInput, ...]:
    if isinstance(packets, (str, bytes)):
        raise ValueError("packets must be an iterable")
    try:
        values = tuple(packets)
    except TypeError as exc:
        raise ValueError("packets must be an iterable") from exc
    seen: set[str] = set()
    for packet in values:
        if type(packet) is not ResearchStrategyManualDecisionPacketInput:
            raise ValueError(
                "packets must contain ResearchStrategyManualDecisionPacketInput",
            )
        _require_hard_phase_flags("packet", packet)
        if packet.internal_packet_key in seen:
            raise ValueError("internal_packet_key values must be unique")
        seen.add(packet.internal_packet_key)
    return values


def _normalize_rows(
    rows: Iterable[ResearchStrategyManualDecisionPacketCompletenessRow],
) -> tuple[ResearchStrategyManualDecisionPacketCompletenessRow, ...]:
    if isinstance(rows, (str, bytes)):
        raise ValueError("rows must be an iterable")
    try:
        values = tuple(rows)
    except TypeError as exc:
        raise ValueError("rows must be an iterable") from exc
    seen: set[str] = set()
    for index, row in enumerate(values, start=1):
        if type(row) is not ResearchStrategyManualDecisionPacketCompletenessRow:
            raise ValueError(
                "rows must contain ResearchStrategyManualDecisionPacketCompletenessRow",
            )
        _require_hard_phase_flags("row", row)
        if row.public_packet_hash in seen:
            raise ValueError("public_packet_hash values must be unique")
        seen.add(row.public_packet_hash)
        if row.row_number != _count(index):
            raise ValueError("row_number values must be sequential")
    if values != tuple(sorted(values, key=_row_sort_key)):
        raise ValueError("rows must be sorted deterministically")
    return values


def _validate_row(row: ResearchStrategyManualDecisionPacketCompletenessRow) -> None:
    if row.validation_digest != _validation_digest(_row_digest_values(row)):
        raise ValueError("validation_digest must match row payload")
    expected_completeness = _completeness_score(
        (
            row.evidence_coverage_ratio,
            row.independent_source_ratio,
            row.evidence_summary_score,
            row.cost_summary_score,
            row.risk_summary_score,
            row.resolution_summary_score,
            row.team_memory_summary_score,
            row.update_trigger_summary_score,
        ),
    )
    if row.completeness_score != expected_completeness:
        raise ValueError("completeness_score must match component scores")
    if row.status != _row_status(row.reason_codes):
        raise ValueError("status must match reason_codes")
    if row.manual_decision_review_state != _manual_state(row.status):
        raise ValueError("manual_decision_review_state must match status")


def _validate_report(report: ResearchStrategyManualDecisionPacketCompletenessReport) -> None:
    if report.validation_digest != _validation_digest(_report_digest_values(report)):
        raise ValueError("validation_digest must match report payload")
    if report.packet_count != _count(len(report.rows)):
        raise ValueError("packet_count must match rows")
    if report.pass_count != _status_count(report.rows, "pass"):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _status_count(report.rows, "watch"):
        raise ValueError("watch_count must match rows")
    if report.block_count != _status_count(report.rows, "block"):
        raise ValueError("block_count must match rows")
    if report.average_completeness_score != _average_completeness_score(report.rows):
        raise ValueError("average_completeness_score must match rows")
    expected_min = None if not report.rows else min(row.completeness_score for row in report.rows)
    if report.min_completeness_score != expected_min:
        raise ValueError("min_completeness_score must match rows")
    if report.status != _report_status(report.rows):
        raise ValueError("status must match rows")
    if report.manual_decision_review_state != _manual_state(report.status):
        raise ValueError("manual_decision_review_state must match status")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")


def _row_digest_values(
    row: ResearchStrategyManualDecisionPacketCompletenessRow,
) -> dict[str, Any]:
    return {
        "row_number": row.row_number,
        "public_packet_hash": row.public_packet_hash,
        "evidence_item_count": row.evidence_item_count,
        "independent_source_count": row.independent_source_count,
        "evidence_coverage_ratio": row.evidence_coverage_ratio,
        "independent_source_ratio": row.independent_source_ratio,
        "evidence_summary_score": row.evidence_summary_score,
        "cost_summary_score": row.cost_summary_score,
        "risk_summary_score": row.risk_summary_score,
        "resolution_summary_score": row.resolution_summary_score,
        "team_memory_summary_score": row.team_memory_summary_score,
        "update_trigger_summary_score": row.update_trigger_summary_score,
        "unresolved_summary_gap_count": row.unresolved_summary_gap_count,
        "completeness_score": row.completeness_score,
        "status": row.status,
        "manual_decision_review_state": row.manual_decision_review_state,
        "reason_codes": row.reason_codes,
        "paper_only": row.paper_only,
        "report_only": row.report_only,
        "readonly": row.readonly,
    }


def _report_digest_values(
    report: ResearchStrategyManualDecisionPacketCompletenessReport,
) -> dict[str, Any]:
    return {
        "generated_at": report.generated_at,
        "config_version": report.config_version,
        "packet_count": report.packet_count,
        "pass_count": report.pass_count,
        "watch_count": report.watch_count,
        "block_count": report.block_count,
        "average_completeness_score": report.average_completeness_score,
        "min_completeness_score": report.min_completeness_score,
        "status": report.status,
        "manual_decision_review_state": report.manual_decision_review_state,
        "reason_codes": report.reason_codes,
        "rows": report.rows,
        "paper_only": report.paper_only,
        "report_only": report.report_only,
        "readonly": report.readonly,
    }


def _validate_payload_digests(payload: dict[str, Any]) -> None:
    _require_payload_keys("report payload", payload, REPORT_PAYLOAD_KEYS)
    rows = payload["rows"]
    if type(rows) is not list:
        raise ValueError("rows must be a JSON list")
    for row_payload in rows:
        if type(row_payload) is not dict:
            raise ValueError("rows must contain JSON objects")
        _require_payload_keys("row payload", row_payload, ROW_PAYLOAD_KEYS)
        _validate_payload_digest("row", row_payload, ROW_PAYLOAD_KEYS)
    _validate_payload_digest("report", payload, REPORT_PAYLOAD_KEYS)


def _require_payload_keys(
    name: str,
    payload: dict[str, Any],
    expected_keys: tuple[str, ...],
) -> None:
    if set(payload) != set(expected_keys):
        raise ValueError(f"{name} keys must match the public payload schema")


def _validate_payload_digest(
    name: str,
    payload: dict[str, Any],
    payload_keys: tuple[str, ...],
) -> None:
    digest = payload["validation_digest"]
    _require_digest("validation_digest", digest)
    digest_values = {
        key: payload[key]
        for key in payload_keys
        if key != "validation_digest"
    }
    if digest != _validation_digest(digest_values):
        raise ValueError(f"validation_digest must match {name} payload")


def _row_value_sort_key(values: dict[str, Any]) -> tuple[Decimal, Decimal, str]:
    return (
        STATUS_WEIGHT[str(values["status"])],
        _normalize_ratio("completeness_score", values["completeness_score"]),
        str(values["public_packet_hash"]),
    )


def _row_sort_key(
    row: ResearchStrategyManualDecisionPacketCompletenessRow,
) -> tuple[Decimal, Decimal, str]:
    return (STATUS_WEIGHT[row.status], row.completeness_score, row.public_packet_hash)


def _status_count(
    rows: tuple[ResearchStrategyManualDecisionPacketCompletenessRow, ...],
    status: str,
) -> Decimal:
    return _count(sum(1 for row in rows if row.status == status))


def _normalize_reason_codes(values: object) -> tuple[str, ...]:
    if isinstance(values, (str, bytes)):
        raise ValueError("reason_codes must be an iterable")
    try:
        reason_codes = tuple(values)
    except TypeError as exc:
        raise ValueError("reason_codes must be an iterable") from exc
    if not reason_codes:
        raise ValueError("reason_codes must not be empty")
    for reason_code in reason_codes:
        _require_public_text("reason_codes", reason_code)
        compact = "".join(part for part in reason_code if part != "_")
        if not compact.isalnum() or reason_code.lower() != reason_code:
            raise ValueError("reason_codes must be lowercase snake case")
    normalized = tuple(sorted(dict.fromkeys(reason_codes), key=_reason_sort_key))
    if "manual_decision_packet_completeness_pass" in normalized and len(normalized) != 1:
        raise ValueError("manual_decision_packet_completeness_pass must stand alone")
    if NO_PACKETS_REASON in normalized and len(normalized) != 1:
        raise ValueError("no packets reason must stand alone")
    return normalized


def _reason_sort_key(reason_code: str) -> tuple[int, str]:
    if reason_code in REASON_PRIORITY:
        return (REASON_PRIORITY.index(reason_code), reason_code)
    return (len(REASON_PRIORITY), reason_code)


def _public_packet_hash(internal_packet_key: str) -> str:
    _require_text("internal_packet_key", internal_packet_key)
    digest = sha256(f"manual-decision-packet:{internal_packet_key}".encode()).hexdigest()
    return f"sha256:{digest}"


def _count(value: int) -> Decimal:
    if type(value) is not int or value < 0:
        raise ValueError("count must be a nonnegative int")
    return Decimal(value).quantize(COUNT_QUANTUM)


def _sum_decimal(values: Iterable[Decimal]) -> Decimal:
    total = ZERO
    for value in values:
        total += _normalize_decimal("sum value", value)
    return _quantize(total)


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    denominator = _normalize_decimal("denominator", denominator)
    if denominator <= ZERO:
        raise ValueError("denominator must be positive")
    numerator = _normalize_decimal("numerator", numerator)
    with localcontext(DECIMAL_CONTEXT):
        return _quantize(numerator / denominator)


def _capped_ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    value = _ratio(numerator, denominator)
    if value > ONE:
        return ONE
    return value


def _normalize_positive_count(name: str, value: object) -> Decimal:
    normalized = _normalize_nonnegative_count(name, value)
    if normalized <= ZERO:
        raise ValueError(f"{name} must be positive")
    return normalized


def _normalize_nonnegative_count(name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(name, value)
    if normalized < ZERO:
        raise ValueError(f"{name} must be nonnegative")
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{name} must be an integer")
    return normalized.quantize(COUNT_QUANTUM)


def _normalize_ratio(name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(name, value)
    if normalized < ZERO or normalized > ONE:
        raise ValueError(f"{name} must be between 0 and 1")
    return _quantize(normalized)


def _normalize_decimal(name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{name} must be finite")
    return value


def _quantize(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(QUANTUM)


def _as_utc(name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_exact_type(value: object, expected_type: type[object], name: str) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{name} must be exactly {expected_type.__name__}")


def _require_at_least(name: str, value: Decimal, floor: Decimal) -> None:
    if value < floor:
        raise ValueError(f"{name} must be at least its paired floor")


def _require_at_most(name: str, value: Decimal, ceiling: Decimal) -> None:
    if value > ceiling:
        raise ValueError(f"{name} must be at most its paired ceiling")


def _require_status(name: str, value: object) -> None:
    _require_public_text(name, value)
    if value not in PUBLIC_STATUSES:
        raise ValueError(f"{name} must be pass, watch, or block")


def _require_manual_state(name: str, value: object) -> None:
    _require_public_text(name, value)
    if value not in {
        "manual_decision_review_ready",
        "manual_decision_review_watch",
        "manual_decision_review_block",
    }:
        raise ValueError(f"{name} must be a manual decision review state")


def _require_text(name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{name} must be a non-empty canonical string")


def _require_public_text(name: str, value: object) -> None:
    _require_text(name, value)
    normalized = value.lower()
    if any(fragment in normalized for fragment in UNSAFE_TEXT_FRAGMENTS):
        raise ValueError(f"{name} contains unsafe public text")


def _require_public_hash(name: str, value: object) -> None:
    _require_text(name, value)
    prefix = "sha256:"
    if not value.startswith(prefix):
        raise ValueError(f"{name} must be a sha256 public hash")
    digest = value[len(prefix) :]
    if len(digest) != 64 or any(char not in "0123456789abcdef" for char in digest):
        raise ValueError(f"{name} must be a sha256 public hash")


def _require_digest(name: str, value: object) -> None:
    _require_text(name, value)
    if len(value) != 64 or any(char not in "0123456789abcdef" for char in value):
        raise ValueError(f"{name} must be a sha256 hex digest")


def _require_hard_phase_flags(name: str, value: object) -> None:
    for field_name in PHASE_FLAG_FIELDS:
        if getattr(value, field_name, None) is not True:
            raise ValueError(f"{name} {field_name} must be True")


def _validation_digest(values: dict[str, Any]) -> str:
    ready = _json_ready(values)
    encoded = json.dumps(ready, sort_keys=True, separators=(",", ":"))
    return sha256(encoded.encode("utf-8")).hexdigest()


def _json_ready(value: Any) -> Any:
    if value is None:
        return None
    if hasattr(value, "__dataclass_fields__") and not isinstance(value, type):
        return _json_ready(asdict(value))
    if type(value) is bool:
        return value
    if type(value) is Decimal:
        if not value.is_finite():
            raise ValueError("JSON Decimal value must be finite")
        return format(value, "f")
    if type(value) is datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("JSON datetime value must be timezone-aware")
        return value.astimezone(UTC).isoformat()
    if type(value) is str:
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


def _reject_unsafe_payload(value: object) -> None:
    if isinstance(value, Mapping):
        for key, item in value.items():
            _require_public_text("payload key", key)
            _reject_unsafe_payload(item)
        return
    if isinstance(value, list):
        for item in value:
            _reject_unsafe_payload(item)
        return
    if type(value) is str:
        _require_public_text("payload value", value)
        return
    if value is None or type(value) is bool:
        return
    raise ValueError("payload contains unsupported value")
