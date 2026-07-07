"""Pure in-memory resolution source preflight for Phase 1 packets."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from typing import Any


DEFAULT_RESEARCH_PACKET_RESOLUTION_SOURCE_PREFLIGHT_V2_CONFIG_VERSION = (
    "research-packet-resolution-source-preflight-v2-v0"
)

COUNT_QUANTUM = Decimal("1")
AGE_QUANTUM = Decimal("0.000001")
ZERO_COUNT = Decimal("0")
ONE_COUNT = Decimal("1")
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)

STATUSES = ("pass", "blocked")
PREFLIGHT_REASON_CODES = (
    "resolution_source_preflight_clear",
    "insufficient_official_anchor_count",
    "insufficient_source_family_independence",
    "stale_official_resolution_source_anchor",
    "missing_contradiction_review",
    "missing_rule_text_traceability",
    "missing_settlement_evidence",
)
CLEAR_REASONS = frozenset(("resolution_source_preflight_clear",))
PHASE_FLAG_FIELDS = frozenset(("paper_only", "report_only", "readonly"))
UNSAFE_PUBLIC_FRAGMENTS = (
    "li" "ve",
    "au" "th",
    "wa" "llet",
    "or" "der",
    "net" "work",
    "data" "base",
    "per" "sist",
    "sign" "ing",
    "muta" "tion",
    "bu" "y",
    "se" "ll",
    "tra" "de",
)


@dataclass(frozen=True)
class ResearchPacketResolutionSourcePreflightConfig:
    config_version: str = DEFAULT_RESEARCH_PACKET_RESOLUTION_SOURCE_PREFLIGHT_V2_CONFIG_VERSION
    min_official_anchor_count: Decimal = Decimal("2")
    min_independent_source_family_count: Decimal = Decimal("2")
    max_official_anchor_age_seconds: Decimal = Decimal("3600.000000")
    min_rule_text_trace_count: Decimal = Decimal("1")
    min_settlement_evidence_count: Decimal = Decimal("1")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_public_string("config_version", self.config_version)
        for field_name in (
            "min_official_anchor_count",
            "min_independent_source_family_count",
            "min_rule_text_trace_count",
            "min_settlement_evidence_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_count(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "max_official_anchor_age_seconds",
            _normalize_positive_age_seconds(
                "max_official_anchor_age_seconds",
                self.max_official_anchor_age_seconds,
            ),
        )
        _require_hard_flags("ResearchPacketResolutionSourcePreflightConfig", self)
        _reject_unsafe_public_payload("config", self)


@dataclass(frozen=True)
class ResearchPacketResolutionSourceAnchor:
    source_id: str
    source_family: str
    observed_at: datetime
    is_official_resolution_source: bool
    has_rule_text_trace: bool
    has_settlement_evidence: bool
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_public_string("source_id", self.source_id)
        _require_public_string("source_family", self.source_family)
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in (
            "is_official_resolution_source",
            "has_rule_text_trace",
            "has_settlement_evidence",
        ):
            _require_bool(field_name, getattr(self, field_name))
        _require_hard_flags("ResearchPacketResolutionSourceAnchor", self)
        _reject_unsafe_public_payload("source anchor", self)


@dataclass(frozen=True)
class ResearchPacketResolutionSourceEventPacket:
    packet_id: str
    event_slug: str
    rule_text_reference: str
    contradiction_reviewed: bool
    contradiction_reviewed_at: datetime | None
    anchors: tuple[ResearchPacketResolutionSourceAnchor, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_public_string("packet_id", self.packet_id)
        _require_public_string("event_slug", self.event_slug)
        _require_public_string("rule_text_reference", self.rule_text_reference)
        _require_bool("contradiction_reviewed", self.contradiction_reviewed)
        if self.contradiction_reviewed:
            if self.contradiction_reviewed_at is None:
                raise ValueError("contradiction_reviewed_at is required")
            object.__setattr__(
                self,
                "contradiction_reviewed_at",
                _as_utc("contradiction_reviewed_at", self.contradiction_reviewed_at),
            )
        elif self.contradiction_reviewed_at is not None:
            raise ValueError("contradiction_reviewed_at must be empty when not reviewed")
        object.__setattr__(self, "anchors", _normalize_anchors(self.anchors))
        _require_hard_flags("ResearchPacketResolutionSourceEventPacket", self)
        _reject_unsafe_public_payload("event packet", self)


@dataclass(frozen=True)
class ResearchPacketResolutionSourcePreflightAnchorRow:
    source_id: str
    source_family: str
    observed_at: datetime
    anchor_age_seconds: Decimal
    is_official_resolution_source: bool
    has_rule_text_trace: bool
    has_settlement_evidence: bool
    is_fresh: bool
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_public_string("source_id", self.source_id)
        _require_public_string("source_family", self.source_family)
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        object.__setattr__(
            self,
            "anchor_age_seconds",
            _normalize_age_seconds("anchor_age_seconds", self.anchor_age_seconds),
        )
        for field_name in (
            "is_official_resolution_source",
            "has_rule_text_trace",
            "has_settlement_evidence",
            "is_fresh",
        ):
            _require_bool(field_name, getattr(self, field_name))
        _require_hard_flags("ResearchPacketResolutionSourcePreflightAnchorRow", self)
        _reject_unsafe_public_payload("anchor row", self)


@dataclass(frozen=True)
class ResearchPacketResolutionSourcePreflightReport:
    generated_at: datetime
    config_version: str
    packet_id: str
    event_slug: str
    rule_text_reference: str
    min_official_anchor_count: Decimal
    min_independent_source_family_count: Decimal
    max_official_anchor_age_seconds: Decimal
    min_rule_text_trace_count: Decimal
    min_settlement_evidence_count: Decimal
    anchor_count: Decimal
    official_anchor_count: Decimal
    independent_source_family_count: Decimal
    stale_official_anchor_count: Decimal
    rule_text_trace_count: Decimal
    settlement_evidence_count: Decimal
    contradiction_review_count: Decimal
    newest_official_anchor_age_seconds: Decimal | None
    oldest_official_anchor_age_seconds: Decimal | None
    status: str
    reason_codes: tuple[str, ...]
    anchor_rows: tuple[ResearchPacketResolutionSourcePreflightAnchorRow, ...]
    derived_validation_digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_string("config_version", self.config_version)
        _require_public_string("packet_id", self.packet_id)
        _require_public_string("event_slug", self.event_slug)
        _require_public_string("rule_text_reference", self.rule_text_reference)
        for field_name in (
            "min_official_anchor_count",
            "min_independent_source_family_count",
            "min_rule_text_trace_count",
            "min_settlement_evidence_count",
            "anchor_count",
            "official_anchor_count",
            "independent_source_family_count",
            "stale_official_anchor_count",
            "rule_text_trace_count",
            "settlement_evidence_count",
            "contradiction_review_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_count(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "max_official_anchor_age_seconds",
            _normalize_positive_age_seconds(
                "max_official_anchor_age_seconds",
                self.max_official_anchor_age_seconds,
            ),
        )
        for field_name in (
            "newest_official_anchor_age_seconds",
            "oldest_official_anchor_age_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_optional_age_seconds(field_name, getattr(self, field_name)),
            )
        _require_member("status", self.status, STATUSES)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        object.__setattr__(self, "anchor_rows", _normalize_anchor_rows(self.anchor_rows))
        _require_hard_flags("ResearchPacketResolutionSourcePreflightReport", self)
        _reject_unsafe_public_payload("preflight report", self)
        _require_sha256_digest("derived_validation_digest", self.derived_validation_digest)
        _validate_report(self)
        if self.derived_validation_digest != _digest_for_report(self):
            raise ValueError("derived_validation_digest must match report payload")


def build_research_packet_resolution_source_preflight_v2_report(
    event_packet: ResearchPacketResolutionSourceEventPacket,
    *,
    config: ResearchPacketResolutionSourcePreflightConfig,
    generated_at: datetime,
) -> ResearchPacketResolutionSourcePreflightReport:
    if type(config) is not ResearchPacketResolutionSourcePreflightConfig:
        raise ValueError("config must be a ResearchPacketResolutionSourcePreflightConfig")
    if type(event_packet) is not ResearchPacketResolutionSourceEventPacket:
        raise ValueError(
            "event_packet must be a ResearchPacketResolutionSourceEventPacket",
        )
    _require_hard_flags("config", config)
    _require_hard_flags("event_packet", event_packet)
    generated_at_utc = _as_utc("generated_at", generated_at)
    if (
        event_packet.contradiction_reviewed_at is not None
        and event_packet.contradiction_reviewed_at > generated_at_utc
    ):
        raise ValueError("contradiction_reviewed_at must not be in the future")
    for source_anchor in event_packet.anchors:
        if source_anchor.observed_at > generated_at_utc:
            raise ValueError("observed_at must not be in the future")
    rows = tuple(
        sorted(
            (
                _row_for_anchor(
                    source_anchor,
                    generated_at=generated_at_utc,
                    max_age_seconds=config.max_official_anchor_age_seconds,
                )
                for source_anchor in event_packet.anchors
            ),
            key=_anchor_row_sort_key,
        ),
    )
    official_rows = _official_rows(rows)
    reason_codes = _report_reason_codes(
        official_anchor_count=_count(len(official_rows)),
        independent_source_family_count=_independent_source_family_count(official_rows),
        stale_official_anchor_count=_stale_official_anchor_count(official_rows),
        rule_text_trace_count=_rule_text_trace_count(official_rows),
        settlement_evidence_count=_settlement_evidence_count(official_rows),
        contradiction_review_count=_count(1 if event_packet.contradiction_reviewed else 0),
        config=config,
    )
    values: dict[str, object] = {
        "generated_at": generated_at_utc,
        "config_version": config.config_version,
        "packet_id": event_packet.packet_id,
        "event_slug": event_packet.event_slug,
        "rule_text_reference": event_packet.rule_text_reference,
        "min_official_anchor_count": config.min_official_anchor_count,
        "min_independent_source_family_count": (
            config.min_independent_source_family_count
        ),
        "max_official_anchor_age_seconds": config.max_official_anchor_age_seconds,
        "min_rule_text_trace_count": config.min_rule_text_trace_count,
        "min_settlement_evidence_count": config.min_settlement_evidence_count,
        "anchor_count": _count(len(rows)),
        "official_anchor_count": _count(len(official_rows)),
        "independent_source_family_count": _independent_source_family_count(official_rows),
        "stale_official_anchor_count": _stale_official_anchor_count(official_rows),
        "rule_text_trace_count": _rule_text_trace_count(official_rows),
        "settlement_evidence_count": _settlement_evidence_count(official_rows),
        "contradiction_review_count": _count(
            1 if event_packet.contradiction_reviewed else 0,
        ),
        "newest_official_anchor_age_seconds": _newest_official_anchor_age(official_rows),
        "oldest_official_anchor_age_seconds": _oldest_official_anchor_age(official_rows),
        "status": _status_from_reason_codes(reason_codes),
        "reason_codes": reason_codes,
        "anchor_rows": rows,
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    values["derived_validation_digest"] = _digest_for_public_payload(_public_value(values))
    return ResearchPacketResolutionSourcePreflightReport(**values)


def research_packet_resolution_source_preflight_v2_payload(
    report: ResearchPacketResolutionSourcePreflightReport,
) -> dict[str, Any]:
    if type(report) is not ResearchPacketResolutionSourcePreflightReport:
        raise ValueError("report must be a ResearchPacketResolutionSourcePreflightReport")
    _require_hard_flags("report", report)
    _reject_unsafe_public_payload("preflight report", report)
    payload = _public_value(report)
    if type(payload) is not dict:
        raise ValueError("report payload must be an object")
    return validate_research_packet_resolution_source_preflight_v2_payload(payload)


def validate_research_packet_resolution_source_preflight_v2_payload(
    payload: dict[str, Any],
) -> dict[str, Any]:
    if type(payload) is not dict:
        raise ValueError("payload must be an object")
    _reject_unsafe_public_payload("preflight payload", payload)
    digest = payload.get("derived_validation_digest")
    if digest is None:
        raise ValueError("derived_validation_digest is required")
    _require_sha256_digest("derived_validation_digest", digest)
    if digest != _digest_for_public_payload(payload):
        raise ValueError("derived_validation_digest must match report payload")
    return payload


def _row_for_anchor(
    source_anchor: ResearchPacketResolutionSourceAnchor,
    *,
    generated_at: datetime,
    max_age_seconds: Decimal,
) -> ResearchPacketResolutionSourcePreflightAnchorRow:
    anchor_age_seconds = _age_seconds(generated_at, source_anchor.observed_at)
    return ResearchPacketResolutionSourcePreflightAnchorRow(
        source_id=source_anchor.source_id,
        source_family=source_anchor.source_family,
        observed_at=source_anchor.observed_at,
        anchor_age_seconds=anchor_age_seconds,
        is_official_resolution_source=source_anchor.is_official_resolution_source,
        has_rule_text_trace=source_anchor.has_rule_text_trace,
        has_settlement_evidence=source_anchor.has_settlement_evidence,
        is_fresh=anchor_age_seconds <= max_age_seconds,
    )


def _report_reason_codes(
    *,
    official_anchor_count: Decimal,
    independent_source_family_count: Decimal,
    stale_official_anchor_count: Decimal,
    rule_text_trace_count: Decimal,
    settlement_evidence_count: Decimal,
    contradiction_review_count: Decimal,
    config: ResearchPacketResolutionSourcePreflightConfig,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    if official_anchor_count < config.min_official_anchor_count:
        reason_codes.append("insufficient_official_anchor_count")
    if independent_source_family_count < config.min_independent_source_family_count:
        reason_codes.append("insufficient_source_family_independence")
    if stale_official_anchor_count > ZERO_COUNT:
        reason_codes.append("stale_official_resolution_source_anchor")
    if contradiction_review_count < ONE_COUNT:
        reason_codes.append("missing_contradiction_review")
    if rule_text_trace_count < config.min_rule_text_trace_count:
        reason_codes.append("missing_rule_text_traceability")
    if settlement_evidence_count < config.min_settlement_evidence_count:
        reason_codes.append("missing_settlement_evidence")
    if not reason_codes:
        reason_codes.append("resolution_source_preflight_clear")
    return tuple(reason_codes)


def _normalize_anchors(
    value: object,
) -> tuple[ResearchPacketResolutionSourceAnchor, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("anchors must be a list or tuple")
    rows = tuple(value)
    seen_source_ids: set[str] = set()
    for row in rows:
        if type(row) is not ResearchPacketResolutionSourceAnchor:
            raise ValueError("anchors must contain ResearchPacketResolutionSourceAnchor")
        _require_hard_flags("source anchor", row)
        if row.source_id in seen_source_ids:
            raise ValueError("source_id values must be unique")
        seen_source_ids.add(row.source_id)
    return rows


def _normalize_anchor_rows(
    value: object,
) -> tuple[ResearchPacketResolutionSourcePreflightAnchorRow, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("anchor_rows must be a list or tuple")
    rows = tuple(value)
    seen_source_ids: set[str] = set()
    for row in rows:
        if type(row) is not ResearchPacketResolutionSourcePreflightAnchorRow:
            raise ValueError(
                "anchor_rows must contain ResearchPacketResolutionSourcePreflightAnchorRow",
            )
        _require_hard_flags("anchor row", row)
        if row.source_id in seen_source_ids:
            raise ValueError("anchor_rows source_id values must be unique")
        seen_source_ids.add(row.source_id)
    if rows != tuple(sorted(rows, key=_anchor_row_sort_key)):
        raise ValueError("anchor_rows must use deterministic sorting")
    return rows


def _validate_report(report: ResearchPacketResolutionSourcePreflightReport) -> None:
    official_rows = _official_rows(report.anchor_rows)
    if report.anchor_count != _count(len(report.anchor_rows)):
        raise ValueError("anchor_count must match anchor_rows")
    if report.official_anchor_count != _count(len(official_rows)):
        raise ValueError("official_anchor_count must match anchor_rows")
    if report.independent_source_family_count != _independent_source_family_count(
        official_rows,
    ):
        raise ValueError("independent_source_family_count must match anchor_rows")
    if report.stale_official_anchor_count != _stale_official_anchor_count(official_rows):
        raise ValueError("stale_official_anchor_count must match anchor_rows")
    if report.rule_text_trace_count != _rule_text_trace_count(official_rows):
        raise ValueError("rule_text_trace_count must match anchor_rows")
    if report.settlement_evidence_count != _settlement_evidence_count(official_rows):
        raise ValueError("settlement_evidence_count must match anchor_rows")
    expected_reasons = _report_reason_codes(
        official_anchor_count=report.official_anchor_count,
        independent_source_family_count=report.independent_source_family_count,
        stale_official_anchor_count=report.stale_official_anchor_count,
        rule_text_trace_count=report.rule_text_trace_count,
        settlement_evidence_count=report.settlement_evidence_count,
        contradiction_review_count=report.contradiction_review_count,
        config=ResearchPacketResolutionSourcePreflightConfig(
            config_version=report.config_version,
            min_official_anchor_count=report.min_official_anchor_count,
            min_independent_source_family_count=(
                report.min_independent_source_family_count
            ),
            max_official_anchor_age_seconds=report.max_official_anchor_age_seconds,
            min_rule_text_trace_count=report.min_rule_text_trace_count,
            min_settlement_evidence_count=report.min_settlement_evidence_count,
        ),
    )
    if report.reason_codes != expected_reasons:
        raise ValueError("reason_codes must match report counts")
    if report.status != _status_from_reason_codes(report.reason_codes):
        raise ValueError("status must match reason_codes")
    if report.newest_official_anchor_age_seconds != _newest_official_anchor_age(
        official_rows,
    ):
        raise ValueError("newest_official_anchor_age_seconds must match anchor_rows")
    if report.oldest_official_anchor_age_seconds != _oldest_official_anchor_age(
        official_rows,
    ):
        raise ValueError("oldest_official_anchor_age_seconds must match anchor_rows")


def _official_rows(
    rows: tuple[ResearchPacketResolutionSourcePreflightAnchorRow, ...],
) -> tuple[ResearchPacketResolutionSourcePreflightAnchorRow, ...]:
    return tuple(row for row in rows if row.is_official_resolution_source)


def _independent_source_family_count(
    rows: tuple[ResearchPacketResolutionSourcePreflightAnchorRow, ...],
) -> Decimal:
    return _count(len({row.source_family for row in rows}))


def _stale_official_anchor_count(
    rows: tuple[ResearchPacketResolutionSourcePreflightAnchorRow, ...],
) -> Decimal:
    return _count(sum(1 for row in rows if not row.is_fresh))


def _rule_text_trace_count(
    rows: tuple[ResearchPacketResolutionSourcePreflightAnchorRow, ...],
) -> Decimal:
    return _count(sum(1 for row in rows if row.has_rule_text_trace))


def _settlement_evidence_count(
    rows: tuple[ResearchPacketResolutionSourcePreflightAnchorRow, ...],
) -> Decimal:
    return _count(sum(1 for row in rows if row.has_settlement_evidence))


def _newest_official_anchor_age(
    rows: tuple[ResearchPacketResolutionSourcePreflightAnchorRow, ...],
) -> Decimal | None:
    ages = tuple(row.anchor_age_seconds for row in rows)
    return min(ages) if ages else None


def _oldest_official_anchor_age(
    rows: tuple[ResearchPacketResolutionSourcePreflightAnchorRow, ...],
) -> Decimal | None:
    ages = tuple(row.anchor_age_seconds for row in rows)
    return max(ages) if ages else None


def _anchor_row_sort_key(
    row: ResearchPacketResolutionSourcePreflightAnchorRow,
) -> tuple[str, str]:
    return (row.source_id, row.source_family)


def _status_from_reason_codes(reason_codes: tuple[str, ...]) -> str:
    if reason_codes == ("resolution_source_preflight_clear",):
        return "pass"
    return "blocked"


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


def _normalize_positive_age_seconds(field_name: str, value: object) -> Decimal:
    normalized = _normalize_age_seconds(field_name, value)
    if normalized <= ZERO_COUNT:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _normalize_optional_age_seconds(
    field_name: str,
    value: object,
) -> Decimal | None:
    if value is None:
        return None
    return _normalize_age_seconds(field_name, value)


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
        raise ValueError(f"{field_name} must be exactly datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _normalize_reason_codes(
    field_name: str,
    value: object,
) -> tuple[str, ...]:
    if type(value) not in (list, tuple):
        raise ValueError(f"{field_name} must be a list or tuple")
    reason_codes = tuple(value)
    if not reason_codes:
        raise ValueError(f"{field_name} must not be empty")
    for reason_code in reason_codes:
        _require_member(field_name, reason_code, PREFLIGHT_REASON_CODES)
    if len(set(reason_codes)) != len(reason_codes):
        raise ValueError(f"{field_name} must be unique")
    if tuple(code for code in PREFLIGHT_REASON_CODES if code in reason_codes) != reason_codes:
        raise ValueError(f"{field_name} must be deterministic")
    if reason_codes[0] in CLEAR_REASONS and len(reason_codes) != 1:
        raise ValueError(f"{field_name} clear reason must be exclusive")
    return reason_codes


def _require_member(field_name: str, value: object, allowed: tuple[str, ...]) -> None:
    if type(value) is not str or value not in allowed:
        raise ValueError(f"{field_name} must be one of {allowed}")


def _require_public_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")
    if "://" in value or "?" in value:
        raise ValueError(f"{field_name} has unsafe public value")
    _reject_unsafe_public_text(field_name, value, is_key=False)


def _require_bool(field_name: str, value: object) -> None:
    if type(value) is not bool:
        raise ValueError(f"{field_name} must be a bool")


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in PHASE_FLAG_FIELDS:
        if getattr(value, field_name) is not True:
            raise ValueError(f"{field_name} must be True for {label}")


def _reject_unsafe_public_payload(label: str, value: object, path: str = "") -> None:
    current_path = path or label
    if is_dataclass(value) and not isinstance(value, type):
        for field in fields(value):
            item_path = field.name if not path else f"{path}.{field.name}"
            _reject_unsafe_public_text(item_path, field.name, is_key=True)
            _reject_unsafe_public_payload(
                label,
                getattr(value, field.name),
                item_path,
            )
        return
    if type(value) is dict:
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("payload keys must be strings")
            item_path = key if not path else f"{path}.{key}"
            _reject_unsafe_public_text(item_path, key, is_key=True)
            if key in PHASE_FLAG_FIELDS and item is not True:
                raise ValueError(f"{item_path} must be True for {label}")
            _reject_unsafe_public_payload(label, item, item_path)
        return
    if type(value) in (list, tuple):
        for index, item in enumerate(value):
            _reject_unsafe_public_payload(label, item, f"{current_path}[{index}]")
        return
    if type(value) is str:
        _reject_unsafe_public_text(current_path, value, is_key=False)
        return
    if type(value) is Decimal:
        if not value.is_finite():
            raise ValueError(f"{current_path} must be finite")
        return
    if type(value) is datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError(f"{current_path} must be timezone-aware")
        return
    if value is None or type(value) is bool:
        return
    if type(value) is int:
        raise ValueError(f"{current_path} must use Decimal-derived string values")
    if type(value) is float:
        raise ValueError(f"{current_path} must not be a float")
    raise ValueError(f"{current_path} is not JSON serializable")


def _reject_unsafe_public_text(path: str, value: str, *, is_key: bool) -> None:
    lowered = value.lower()
    if value.strip() != value:
        raise ValueError(f"{path} has unsafe public value")
    for fragment in UNSAFE_PUBLIC_FRAGMENTS:
        if fragment in lowered:
            if is_key:
                raise ValueError(f"{path} has unsafe public field")
            raise ValueError(f"{path} has unsafe public value")


def _public_value(value: Any) -> Any:
    _reject_unsafe_public_payload("public payload", value)
    if value is None:
        return None
    if is_dataclass(value) and not isinstance(value, type):
        return {field.name: _public_value(getattr(value, field.name)) for field in fields(value)}
    if type(value) is Decimal:
        if not value.is_finite():
            raise ValueError("Decimal values must be finite")
        return str(value)
    if type(value) is datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("datetime values must be timezone-aware")
        return value.astimezone(UTC).isoformat()
    if type(value) is dict:
        ready: dict[str, Any] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("payload keys must be strings")
            ready[key] = _public_value(item)
        return ready
    if type(value) in (list, tuple):
        return [_public_value(item) for item in value]
    if type(value) in (str, bool):
        return value
    if type(value) is int:
        raise ValueError("integer values must use Decimal-derived strings")
    if type(value) is float:
        raise ValueError("float values are not allowed")
    raise ValueError("value is not JSON serializable")


def _digest_for_report(report: ResearchPacketResolutionSourcePreflightReport) -> str:
    return _digest_for_public_payload(_public_value(report))


def _digest_for_public_payload(payload: Any) -> str:
    if type(payload) is not dict:
        raise ValueError("payload must be an object")
    payload_without_digest = {
        key: value for key, value in payload.items() if key != "derived_validation_digest"
    }
    canonical = json.dumps(
        payload_without_digest,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _require_sha256_digest(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if len(value) != 64:
        raise ValueError(f"{field_name} must be a sha256 hex digest")
    for character in value:
        if character not in "0123456789abcdef":
            raise ValueError(f"{field_name} must be a sha256 hex digest")


__all__ = (
    "DEFAULT_RESEARCH_PACKET_RESOLUTION_SOURCE_PREFLIGHT_V2_CONFIG_VERSION",
    "PREFLIGHT_REASON_CODES",
    "STATUSES",
    "ResearchPacketResolutionSourceAnchor",
    "ResearchPacketResolutionSourceEventPacket",
    "ResearchPacketResolutionSourcePreflightAnchorRow",
    "ResearchPacketResolutionSourcePreflightConfig",
    "ResearchPacketResolutionSourcePreflightReport",
    "build_research_packet_resolution_source_preflight_v2_report",
    "research_packet_resolution_source_preflight_v2_payload",
    "validate_research_packet_resolution_source_preflight_v2_payload",
)
