"""Pure report snapshot for routing evidence packets into manual review."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import asdict, dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal, ROUND_HALF_UP
import hashlib
import json
import re
from typing import Any


DEFAULT_RESEARCH_MANUAL_REVIEW_EVIDENCE_PACKET_ROUTER_CONFIG_VERSION = (
    "research-manual-review-evidence-packet-router-report"
)

MANUAL_REVIEW_EVIDENCE_PACKET_ROUTER_DIMENSIONS = (
    "evidence_completeness",
    "specialist_fit",
    "cost_sanity",
    "resolution_rule_readiness",
    "recheck_urgency",
)

_QUANT = Decimal("0.000001")
_ZERO = Decimal("0.000000")
_ONE = Decimal("1.000000")
_PUBLIC_IDENTIFIER_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,127}$")
_DIGEST_RE = re.compile(r"^[0-9a-f]{64}$")
_ROUTE_STATUSES = ("pass", "watch", "block")
_POSITIVE_DIMENSION_FIELDS = (
    (
        "evidence_completeness_score",
        "manual_review_router_evidence_incomplete",
        "manual_review_router_evidence_missing",
    ),
    (
        "specialist_fit_score",
        "manual_review_router_specialist_fit_incomplete",
        "manual_review_router_specialist_fit_missing",
    ),
    (
        "cost_sanity_score",
        "manual_review_router_cost_sanity_incomplete",
        "manual_review_router_cost_sanity_missing",
    ),
    (
        "resolution_rule_readiness_score",
        "manual_review_router_resolution_rule_incomplete",
        "manual_review_router_resolution_rule_missing",
    ),
)
_ALL_SCORE_FIELDS = tuple(
    field_name for field_name, _, _ in _POSITIVE_DIMENSION_FIELDS
) + ("recheck_urgency_score",)
_ROW_REASON_CODES = (
    "manual_review_router_row_passed",
    "manual_review_router_evidence_incomplete",
    "manual_review_router_evidence_missing",
    "manual_review_router_specialist_fit_incomplete",
    "manual_review_router_specialist_fit_missing",
    "manual_review_router_cost_sanity_incomplete",
    "manual_review_router_cost_sanity_missing",
    "manual_review_router_resolution_rule_incomplete",
    "manual_review_router_resolution_rule_missing",
    "manual_review_router_recheck_urgency_watch",
    "manual_review_router_recheck_urgency_block",
    "manual_review_router_score_below_watch",
    "manual_review_router_score_below_pass",
)
_REPORT_REASON_CODES = (
    "manual_review_router_report_passed",
    "manual_review_router_report_empty",
    "manual_review_router_report_block_rows",
    "manual_review_router_report_watch_rows",
    "manual_review_router_report_average_below_watch",
    "manual_review_router_report_average_below_pass",
    "manual_review_router_report_recheck_urgent_rows",
)
_UNSAFE_PUBLIC_TERMS = (
    "li" "ve",
    "au" "th",
    "wal" "let",
    "ord" "er",
    "net" "work",
    "data" "base",
    "persist",
    "signing",
    "mutation",
    "buy",
    "sell",
    "tra" "de",
    "recommendation",
    "sizing",
    "candidate",
    "market",
    "slug",
    "question",
    "source",
    "url",
    "text",
    "dsn",
    "table",
    "token",
)

__all__ = (
    "DEFAULT_RESEARCH_MANUAL_REVIEW_EVIDENCE_PACKET_ROUTER_CONFIG_VERSION",
    "MANUAL_REVIEW_EVIDENCE_PACKET_ROUTER_DIMENSIONS",
    "ResearchManualReviewEvidencePacket",
    "ResearchManualReviewEvidencePacketRouterConfig",
    "ResearchManualReviewEvidencePacketRouterReport",
    "ResearchManualReviewEvidencePacketRouterRow",
    "build_research_manual_review_evidence_packet_router_report",
    "research_manual_review_evidence_packet_router_report_payload",
)


@dataclass(frozen=True)
class ResearchManualReviewEvidencePacketRouterConfig:
    config_version: str = (
        DEFAULT_RESEARCH_MANUAL_REVIEW_EVIDENCE_PACKET_ROUTER_CONFIG_VERSION
    )
    min_pass_routing_score: Decimal = Decimal("0.850000")
    min_watch_routing_score: Decimal = Decimal("0.650000")
    min_pass_dimension_score: Decimal = Decimal("0.750000")
    min_watch_dimension_score: Decimal = Decimal("0.500000")
    recheck_urgency_watch_threshold: Decimal = Decimal("0.500000")
    recheck_urgency_block_threshold: Decimal = Decimal("0.800000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not ResearchManualReviewEvidencePacketRouterConfig:
            raise ValueError("config must be exactly ResearchManualReviewEvidencePacketRouterConfig")
        object.__setattr__(
            self,
            "config_version",
            _require_public_identifier("config_version", self.config_version),
        )
        if (
            self.config_version
            != DEFAULT_RESEARCH_MANUAL_REVIEW_EVIDENCE_PACKET_ROUTER_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "min_pass_routing_score",
            "min_watch_routing_score",
            "min_pass_dimension_score",
            "min_watch_dimension_score",
            "recheck_urgency_watch_threshold",
            "recheck_urgency_block_threshold",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        _validate_config(self)
        _require_hard_flags("config", self)
        _reject_unsafe_public_payload("config", self)


@dataclass(frozen=True)
class ResearchManualReviewEvidencePacket:
    packet_id: str
    evidence_completeness_score: Decimal
    specialist_fit_score: Decimal
    cost_sanity_score: Decimal
    resolution_rule_readiness_score: Decimal
    recheck_urgency_score: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not ResearchManualReviewEvidencePacket:
            raise ValueError("packet must be exactly ResearchManualReviewEvidencePacket")
        object.__setattr__(
            self,
            "packet_id",
            _require_public_identifier("packet_id", self.packet_id),
        )
        for field_name in _ALL_SCORE_FIELDS:
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        _require_hard_flags("packet", self)
        _reject_unsafe_public_payload("packet", self)


@dataclass(frozen=True)
class ResearchManualReviewEvidencePacketRouterRow:
    rank: Decimal
    packet_id: str
    evidence_completeness_score: Decimal
    specialist_fit_score: Decimal
    cost_sanity_score: Decimal
    resolution_rule_readiness_score: Decimal
    recheck_urgency_score: Decimal
    routing_score: Decimal
    route_status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not ResearchManualReviewEvidencePacketRouterRow:
            raise ValueError("row must be exactly ResearchManualReviewEvidencePacketRouterRow")
        object.__setattr__(
            self,
            "rank",
            _require_positive_count_decimal("rank", self.rank),
        )
        object.__setattr__(
            self,
            "packet_id",
            _require_public_identifier("packet_id", self.packet_id),
        )
        for field_name in _ALL_SCORE_FIELDS:
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "routing_score",
            _require_ratio_decimal("routing_score", self.routing_score),
        )
        _require_route_status("route_status", self.route_status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, _ROW_REASON_CODES),
        )
        _validate_row_score(self)
        _require_hard_flags("row", self)
        _reject_unsafe_public_payload("row", self)


@dataclass(frozen=True)
class ResearchManualReviewEvidencePacketRouterReport:
    generated_at: datetime
    config_version: str
    route_status: str
    packet_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    pass_ratio: Decimal
    watch_ratio: Decimal
    block_ratio: Decimal
    average_routing_score: Decimal
    max_recheck_urgency_score: Decimal
    min_pass_routing_score: Decimal
    min_watch_routing_score: Decimal
    min_pass_dimension_score: Decimal
    min_watch_dimension_score: Decimal
    recheck_urgency_watch_threshold: Decimal
    recheck_urgency_block_threshold: Decimal
    rows: tuple[ResearchManualReviewEvidencePacketRouterRow, ...]
    reason_codes: tuple[str, ...]
    derived_validation_digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not ResearchManualReviewEvidencePacketRouterReport:
            raise ValueError("report must be exactly ResearchManualReviewEvidencePacketRouterReport")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        object.__setattr__(
            self,
            "config_version",
            _require_public_identifier("config_version", self.config_version),
        )
        if (
            self.config_version
            != DEFAULT_RESEARCH_MANUAL_REVIEW_EVIDENCE_PACKET_ROUTER_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        _require_route_status("route_status", self.route_status)
        for field_name in ("packet_count", "pass_count", "watch_count", "block_count"):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_count_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "pass_ratio",
            "watch_ratio",
            "block_ratio",
            "average_routing_score",
            "max_recheck_urgency_score",
            "min_pass_routing_score",
            "min_watch_routing_score",
            "min_pass_dimension_score",
            "min_watch_dimension_score",
            "recheck_urgency_watch_threshold",
            "recheck_urgency_block_threshold",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(
                "reason_codes",
                self.reason_codes,
                _REPORT_REASON_CODES,
            ),
        )
        _require_sha256_digest("derived_validation_digest", self.derived_validation_digest)
        _validate_report_consistency(self)
        _require_hard_flags("report", self)
        _reject_unsafe_public_payload("report", self)
        if self.derived_validation_digest != _digest_from_values(asdict(self)):
            raise ValueError("derived_validation_digest must match report fields")

    @property
    def payload(self) -> dict[str, object]:
        payload = _json_ready(asdict(self))
        _reject_unsafe_public_payload(
            "ResearchManualReviewEvidencePacketRouterReport.payload",
            payload,
            allow_json_containers=True,
        )
        if type(payload) is not dict:
            raise ValueError("payload must be a dict")
        return payload


def build_research_manual_review_evidence_packet_router_report(
    evidence_packets: Sequence[ResearchManualReviewEvidencePacket],
    *,
    generated_at: datetime,
    config: ResearchManualReviewEvidencePacketRouterConfig | None = None,
) -> ResearchManualReviewEvidencePacketRouterReport:
    """Build a deterministic local report for manual review evidence routing."""

    if config is None:
        config = ResearchManualReviewEvidencePacketRouterConfig()
    if type(config) is not ResearchManualReviewEvidencePacketRouterConfig:
        raise ValueError("config must be a ResearchManualReviewEvidencePacketRouterConfig")
    _require_hard_flags("config", config)
    generated_at = _as_utc("generated_at", generated_at)
    packets = _normalize_packets(evidence_packets)
    rows = _build_rows(packets, config)
    packet_count = _decimal_count(len(rows))
    pass_count = _decimal_count(_status_count(rows, "pass"))
    watch_count = _decimal_count(_status_count(rows, "watch"))
    block_count = _decimal_count(_status_count(rows, "block"))
    average_routing_score = _average(tuple(row.routing_score for row in rows))
    max_recheck_urgency_score = max(
        (row.recheck_urgency_score for row in rows),
        default=_ZERO,
    )
    values: dict[str, object] = {
        "generated_at": generated_at,
        "config_version": config.config_version,
        "route_status": _report_status(
            rows=rows,
            packet_count=packet_count,
            average_routing_score=average_routing_score,
            config=config,
        ),
        "packet_count": packet_count,
        "pass_count": pass_count,
        "watch_count": watch_count,
        "block_count": block_count,
        "pass_ratio": _ratio_or_zero(pass_count, packet_count),
        "watch_ratio": _ratio_or_zero(watch_count, packet_count),
        "block_ratio": _ratio_or_zero(block_count, packet_count),
        "average_routing_score": average_routing_score,
        "max_recheck_urgency_score": max_recheck_urgency_score,
        "min_pass_routing_score": config.min_pass_routing_score,
        "min_watch_routing_score": config.min_watch_routing_score,
        "min_pass_dimension_score": config.min_pass_dimension_score,
        "min_watch_dimension_score": config.min_watch_dimension_score,
        "recheck_urgency_watch_threshold": config.recheck_urgency_watch_threshold,
        "recheck_urgency_block_threshold": config.recheck_urgency_block_threshold,
        "rows": rows,
        "reason_codes": _report_reason_codes(
            packet_count=packet_count,
            block_count=block_count,
            watch_count=watch_count,
            average_routing_score=average_routing_score,
            max_recheck_urgency_score=max_recheck_urgency_score,
            config=config,
        ),
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    values["derived_validation_digest"] = _digest_from_values(values)
    return ResearchManualReviewEvidencePacketRouterReport(**values)


def research_manual_review_evidence_packet_router_report_payload(
    value: object,
) -> dict[str, object]:
    if type(value) is ResearchManualReviewEvidencePacketRouterReport:
        return value.payload
    payload = _json_ready(value)
    if type(payload) is not dict:
        raise ValueError("payload must be a dict")
    _require_payload_hard_flags(payload)
    _reject_unsafe_public_payload(
        "research_manual_review_evidence_packet_router_report_payload",
        payload,
        allow_json_containers=True,
    )
    _require_sha256_digest("derived_validation_digest", payload.get("derived_validation_digest"))
    if payload["derived_validation_digest"] != _digest_from_values(payload):
        raise ValueError("derived_validation_digest must match payload fields")
    return payload


def _build_rows(
    packets: tuple[ResearchManualReviewEvidencePacket, ...],
    config: ResearchManualReviewEvidencePacketRouterConfig,
) -> tuple[ResearchManualReviewEvidencePacketRouterRow, ...]:
    sorted_packets = tuple(sorted(packets, key=lambda item: item.packet_id))
    return tuple(
        _row_for_packet(index, packet, config)
        for index, packet in enumerate(sorted_packets, start=1)
    )


def _row_for_packet(
    rank: int,
    packet: ResearchManualReviewEvidencePacket,
    config: ResearchManualReviewEvidencePacketRouterConfig,
) -> ResearchManualReviewEvidencePacketRouterRow:
    routing_score = _routing_score(packet)
    return ResearchManualReviewEvidencePacketRouterRow(
        rank=_decimal_count(rank),
        packet_id=packet.packet_id,
        evidence_completeness_score=packet.evidence_completeness_score,
        specialist_fit_score=packet.specialist_fit_score,
        cost_sanity_score=packet.cost_sanity_score,
        resolution_rule_readiness_score=packet.resolution_rule_readiness_score,
        recheck_urgency_score=packet.recheck_urgency_score,
        routing_score=routing_score,
        route_status=_row_status(packet, routing_score, config),
        reason_codes=_row_reason_codes(packet, routing_score, config),
    )


def _routing_score(
    value: ResearchManualReviewEvidencePacket | ResearchManualReviewEvidencePacketRouterRow,
) -> Decimal:
    values = tuple(getattr(value, field_name) for field_name, _, _ in _POSITIVE_DIMENSION_FIELDS)
    values = values + (_ONE - value.recheck_urgency_score,)
    return _clamp_ratio(sum(values, _ZERO) / Decimal(len(values)))


def _row_status(
    value: ResearchManualReviewEvidencePacket | ResearchManualReviewEvidencePacketRouterRow,
    routing_score: Decimal,
    config: ResearchManualReviewEvidencePacketRouterConfig
    | ResearchManualReviewEvidencePacketRouterReport,
) -> str:
    dimension_scores = tuple(
        getattr(value, field_name) for field_name, _, _ in _POSITIVE_DIMENSION_FIELDS
    )
    if (
        routing_score < config.min_watch_routing_score
        or any(score < config.min_watch_dimension_score for score in dimension_scores)
        or value.recheck_urgency_score >= config.recheck_urgency_block_threshold
    ):
        return "block"
    if (
        routing_score < config.min_pass_routing_score
        or any(score < config.min_pass_dimension_score for score in dimension_scores)
        or value.recheck_urgency_score >= config.recheck_urgency_watch_threshold
    ):
        return "watch"
    return "pass"


def _row_reason_codes(
    value: ResearchManualReviewEvidencePacket | ResearchManualReviewEvidencePacketRouterRow,
    routing_score: Decimal,
    config: ResearchManualReviewEvidencePacketRouterConfig
    | ResearchManualReviewEvidencePacketRouterReport,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    for field_name, incomplete_reason, missing_reason in _POSITIVE_DIMENSION_FIELDS:
        score = getattr(value, field_name)
        if score < config.min_watch_dimension_score:
            reason_codes.append(missing_reason)
        elif score < config.min_pass_dimension_score:
            reason_codes.append(incomplete_reason)
    if value.recheck_urgency_score >= config.recheck_urgency_block_threshold:
        reason_codes.append("manual_review_router_recheck_urgency_block")
    elif value.recheck_urgency_score >= config.recheck_urgency_watch_threshold:
        reason_codes.append("manual_review_router_recheck_urgency_watch")
    if routing_score < config.min_watch_routing_score:
        reason_codes.append("manual_review_router_score_below_watch")
    elif routing_score < config.min_pass_routing_score:
        reason_codes.append("manual_review_router_score_below_pass")
    return _normalize_reason_codes(
        "reason_codes",
        tuple(reason_codes or ("manual_review_router_row_passed",)),
        _ROW_REASON_CODES,
    )


def _report_status(
    *,
    rows: tuple[ResearchManualReviewEvidencePacketRouterRow, ...],
    packet_count: Decimal,
    average_routing_score: Decimal,
    config: ResearchManualReviewEvidencePacketRouterConfig
    | ResearchManualReviewEvidencePacketRouterReport,
) -> str:
    if (
        packet_count == _ZERO
        or any(row.route_status == "block" for row in rows)
        or average_routing_score < config.min_watch_routing_score
    ):
        return "block"
    if (
        any(row.route_status == "watch" for row in rows)
        or average_routing_score < config.min_pass_routing_score
    ):
        return "watch"
    return "pass"


def _report_reason_codes(
    *,
    packet_count: Decimal,
    block_count: Decimal,
    watch_count: Decimal,
    average_routing_score: Decimal,
    max_recheck_urgency_score: Decimal,
    config: ResearchManualReviewEvidencePacketRouterConfig
    | ResearchManualReviewEvidencePacketRouterReport,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    if packet_count == _ZERO:
        reason_codes.append("manual_review_router_report_empty")
    if block_count > _ZERO:
        reason_codes.append("manual_review_router_report_block_rows")
    if watch_count > _ZERO:
        reason_codes.append("manual_review_router_report_watch_rows")
    if average_routing_score < config.min_watch_routing_score:
        reason_codes.append("manual_review_router_report_average_below_watch")
    elif average_routing_score < config.min_pass_routing_score:
        reason_codes.append("manual_review_router_report_average_below_pass")
    if packet_count > _ZERO and (
        max_recheck_urgency_score >= config.recheck_urgency_watch_threshold
    ):
        reason_codes.append("manual_review_router_report_recheck_urgent_rows")
    return _normalize_reason_codes(
        "reason_codes",
        tuple(reason_codes or ("manual_review_router_report_passed",)),
        _REPORT_REASON_CODES,
    )


def _status_count(
    rows: tuple[ResearchManualReviewEvidencePacketRouterRow, ...],
    status: str,
) -> int:
    return sum(1 for row in rows if row.route_status == status)


def _average(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return _ZERO
    return _quantize(sum(values, _ZERO) / Decimal(len(values)))


def _ratio_or_zero(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == _ZERO:
        return _ZERO
    return _clamp_ratio(numerator / denominator)


def _validate_config(config: ResearchManualReviewEvidencePacketRouterConfig) -> None:
    if config.min_watch_routing_score > config.min_pass_routing_score:
        raise ValueError("min_watch_routing_score must not exceed min_pass_routing_score")
    if config.min_watch_dimension_score > config.min_pass_dimension_score:
        raise ValueError("min_watch_dimension_score must not exceed min_pass_dimension_score")
    if config.recheck_urgency_watch_threshold > config.recheck_urgency_block_threshold:
        raise ValueError(
            "recheck_urgency_watch_threshold must not exceed "
            "recheck_urgency_block_threshold",
        )


def _validate_row_score(row: ResearchManualReviewEvidencePacketRouterRow) -> None:
    if row.routing_score != _routing_score(row):
        raise ValueError("routing_score must match row dimensions")


def _validate_report_consistency(
    report: ResearchManualReviewEvidencePacketRouterReport,
) -> None:
    rows = report.rows
    if report.packet_count != _decimal_count(len(rows)):
        raise ValueError("packet_count must match rows")
    if report.pass_count != _decimal_count(_status_count(rows, "pass")):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _decimal_count(_status_count(rows, "watch")):
        raise ValueError("watch_count must match rows")
    if report.block_count != _decimal_count(_status_count(rows, "block")):
        raise ValueError("block_count must match rows")
    if report.pass_ratio != _ratio_or_zero(report.pass_count, report.packet_count):
        raise ValueError("pass_ratio must match counts")
    if report.watch_ratio != _ratio_or_zero(report.watch_count, report.packet_count):
        raise ValueError("watch_ratio must match counts")
    if report.block_ratio != _ratio_or_zero(report.block_count, report.packet_count):
        raise ValueError("block_ratio must match counts")
    if report.average_routing_score != _average(tuple(row.routing_score for row in rows)):
        raise ValueError("average_routing_score must match rows")
    expected_max = max((row.recheck_urgency_score for row in rows), default=_ZERO)
    if report.max_recheck_urgency_score != expected_max:
        raise ValueError("max_recheck_urgency_score must match rows")
    _validate_rows_sorted(rows)
    _validate_rows_against_report(rows, report)
    expected_status = _report_status(
        rows=rows,
        packet_count=report.packet_count,
        average_routing_score=report.average_routing_score,
        config=report,
    )
    if report.route_status != expected_status:
        raise ValueError("route_status must match report fields")
    expected_reasons = _report_reason_codes(
        packet_count=report.packet_count,
        block_count=report.block_count,
        watch_count=report.watch_count,
        average_routing_score=report.average_routing_score,
        max_recheck_urgency_score=report.max_recheck_urgency_score,
        config=report,
    )
    if report.reason_codes != expected_reasons:
        raise ValueError("reason_codes must match report fields")


def _validate_rows_sorted(
    rows: tuple[ResearchManualReviewEvidencePacketRouterRow, ...],
) -> None:
    expected_rows = tuple(sorted(rows, key=lambda row: row.packet_id))
    expected_ranks = tuple(_decimal_count(index) for index in range(1, len(rows) + 1))
    if rows != expected_rows or tuple(row.rank for row in rows) != expected_ranks:
        raise ValueError("rows must use deterministic sorting and rank")


def _validate_rows_against_report(
    rows: tuple[ResearchManualReviewEvidencePacketRouterRow, ...],
    report: ResearchManualReviewEvidencePacketRouterReport,
) -> None:
    for row in rows:
        routing_score = _routing_score(row)
        if row.routing_score != routing_score:
            raise ValueError("row routing_score must match dimensions")
        if row.route_status != _row_status(row, routing_score, report):
            raise ValueError("row route_status must match report thresholds")
        if row.reason_codes != _row_reason_codes(row, routing_score, report):
            raise ValueError("row reason_codes must match report thresholds")


def _normalize_packets(
    value: Sequence[ResearchManualReviewEvidencePacket],
) -> tuple[ResearchManualReviewEvidencePacket, ...]:
    if isinstance(value, (str, bytes)) or not isinstance(value, Sequence):
        raise ValueError("evidence_packets must be a sequence")
    packets = tuple(value)
    seen: set[str] = set()
    for item in packets:
        if type(item) is not ResearchManualReviewEvidencePacket:
            raise ValueError("evidence_packets must contain ResearchManualReviewEvidencePacket")
        _require_hard_flags("packet", item)
        if item.packet_id in seen:
            raise ValueError("evidence_packets must not contain duplicate packet_id values")
        seen.add(item.packet_id)
    return packets


def _normalize_rows(
    value: object,
) -> tuple[ResearchManualReviewEvidencePacketRouterRow, ...]:
    if type(value) is not tuple:
        raise ValueError("rows must be a tuple")
    for row in value:
        if type(row) is not ResearchManualReviewEvidencePacketRouterRow:
            raise ValueError("rows must contain ResearchManualReviewEvidencePacketRouterRow")
    return value


def _normalize_reason_codes(
    field_name: str,
    value: object,
    allowed: tuple[str, ...],
) -> tuple[str, ...]:
    if type(value) is not tuple or not value:
        raise ValueError(f"{field_name} must be a non-empty tuple")
    normalized: list[str] = []
    for item in value:
        _require_public_identifier(field_name, item)
        if item not in allowed:
            raise ValueError(f"{field_name} must contain supported reason codes")
        if item not in normalized:
            normalized.append(item)
    return tuple(reason_code for reason_code in allowed if reason_code in normalized)


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_hard_flags(label: str, value: object) -> None:
    if getattr(value, "paper_only", None) is not True:
        raise ValueError(f"paper_only must be True for {label}")
    if getattr(value, "report_only", None) is not True:
        raise ValueError(f"report_only must be True for {label}")
    if getattr(value, "readonly", None) is not True:
        raise ValueError(f"readonly must be True for {label}")


def _require_payload_hard_flags(payload: dict[str, object]) -> None:
    if payload.get("paper_only") is not True:
        raise ValueError("paper_only must be True for payload")
    if payload.get("report_only") is not True:
        raise ValueError("report_only must be True for payload")
    if payload.get("readonly") is not True:
        raise ValueError("readonly must be True for payload")


def _require_route_status(field_name: str, value: object) -> str:
    if type(value) is not str or value not in _ROUTE_STATUSES:
        raise ValueError(f"{field_name} must be pass, watch, or block")
    return value


def _require_public_identifier(field_name: str, value: object) -> str:
    if type(value) is not str or not _PUBLIC_IDENTIFIER_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a public identifier")
    _reject_unsafe_public_string(field_name, value)
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


def _require_ratio_decimal(field_name: str, value: object) -> Decimal:
    value = _require_decimal(field_name, value)
    if value < _ZERO or value > _ONE:
        raise ValueError(f"{field_name} must be between zero and one")
    return value


def _require_nonnegative_count_decimal(field_name: str, value: object) -> Decimal:
    value = _require_decimal(field_name, value)
    if value < _ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    if value != value.to_integral_value().quantize(_QUANT):
        raise ValueError(f"{field_name} must be integral")
    return value


def _require_positive_count_decimal(field_name: str, value: object) -> Decimal:
    value = _require_nonnegative_count_decimal(field_name, value)
    if value <= _ZERO:
        raise ValueError(f"{field_name} must be positive")
    return value


def _decimal_count(value: int) -> Decimal:
    if value < 0:
        raise ValueError("count must be nonnegative")
    return Decimal(value).quantize(_QUANT)


def _clamp_ratio(value: Decimal) -> Decimal:
    value = _quantize(value)
    if value < _ZERO:
        return _ZERO
    if value > _ONE:
        return _ONE
    return value


def _quantize(value: Decimal) -> Decimal:
    return value.quantize(_QUANT, rounding=ROUND_HALF_UP)


def _digest_from_values(values: Mapping[str, object]) -> str:
    payload = {
        key: _json_ready(item)
        for key, item in values.items()
        if key != "derived_validation_digest"
    }
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
            _reject_unsafe_public_string(current_path, field.name)
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
            _reject_unsafe_public_string(current_path, key)
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
    if type(value) in (int, float) and type(value) is not bool:
        raise ValueError(f"unsafe public payload in {current_path}")
    if type(value) is str:
        _reject_unsafe_public_string(current_path, value)


def _reject_unsafe_public_string(field_name: str, value: str) -> None:
    lowered = value.lower()
    if "://" in lowered or "?" in lowered or "@" in lowered:
        raise ValueError(f"{field_name} has unsafe public value")
    if any(term in lowered for term in _UNSAFE_PUBLIC_TERMS):
        raise ValueError(f"{field_name} has unsafe public value")
