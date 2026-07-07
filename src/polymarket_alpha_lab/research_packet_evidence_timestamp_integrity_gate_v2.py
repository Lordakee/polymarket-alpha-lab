"""Read-only research packet evidence timestamp integrity gate for Phase 1."""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from typing import Any, Iterable

from polymarket_alpha_lab.team_paper_guard import (
    json_ready_no_floats,
    require_paper_only_flags,
)


DEFAULT_RESEARCH_PACKET_EVIDENCE_TIMESTAMP_INTEGRITY_GATE_V2_CONFIG_VERSION = (
    "research-packet-evidence-timestamp-integrity-gate-v2"
)
STATUSES = ("pass", "watch", "block")
REPORT_STATUSES = ("empty", "pass", "watch", "block")
REASON_CODES = (
    "timestamp_integrity_clear",
    "timestamp_integrity_empty",
    "future_timestamp_detected",
    "packet_update_stale",
    "observation_lag_long",
)
COUNT_QUANTUM = Decimal("1")
SECONDS_QUANTUM = Decimal("0.000001")
ZERO_COUNT = Decimal("0")
ZERO_SECONDS = Decimal("0")
ONE_COUNT = Decimal("1")
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
STATUS_WEIGHT = {"block": Decimal("0"), "watch": Decimal("1"), "pass": Decimal("2")}
UNSAFE_SURFACE_FIELD_FRAGMENTS = (
    "live",
    "auth",
    "private_key",
    "wallet",
    "order",
    "network",
    "database",
    "persist",
)


@dataclass(frozen=True)
class ResearchPacketEvidenceTimestampIntegrityGateV2Config:
    config_version: str = (
        DEFAULT_RESEARCH_PACKET_EVIDENCE_TIMESTAMP_INTEGRITY_GATE_V2_CONFIG_VERSION
    )
    max_observation_lag_seconds: Decimal = Decimal("900")
    max_packet_update_lag_seconds: Decimal = Decimal("300")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("config_version", self.config_version)
        for field_name in (
            "max_observation_lag_seconds",
            "max_packet_update_lag_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_seconds(field_name, getattr(self, field_name)),
            )
        require_paper_only_flags(
            "ResearchPacketEvidenceTimestampIntegrityGateV2Config",
            self,
        )


@dataclass(frozen=True)
class ResearchPacketEvidenceTimestampIntegrityInput:
    packet_id: str
    event_slug: str
    category: str
    evidence_created_at: datetime
    evidence_observed_at: datetime
    packet_updated_at: datetime
    source_published_at: datetime | None
    source_count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        for field_name in ("packet_id", "event_slug", "category"):
            _require_canonical_string(field_name, getattr(self, field_name))
        for field_name in (
            "evidence_created_at",
            "evidence_observed_at",
            "packet_updated_at",
        ):
            object.__setattr__(self, field_name, _as_utc(field_name, getattr(self, field_name)))
        object.__setattr__(
            self,
            "source_published_at",
            _as_optional_utc("source_published_at", self.source_published_at),
        )
        object.__setattr__(
            self,
            "source_count",
            _normalize_positive_count("source_count", self.source_count),
        )
        _validate_input(self)
        require_paper_only_flags("ResearchPacketEvidenceTimestampIntegrityInput", self)


@dataclass(frozen=True)
class ResearchPacketEvidenceTimestampIntegrityGateV2Row:
    packet_id: str
    event_slug: str
    category: str
    evidence_created_at: datetime
    evidence_observed_at: datetime
    packet_updated_at: datetime
    source_published_at: datetime | None
    source_count: Decimal
    observation_lag_seconds: Decimal
    packet_update_lag_seconds: Decimal
    future_timestamp_count: Decimal
    status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        for field_name in ("packet_id", "event_slug", "category"):
            _require_canonical_string(field_name, getattr(self, field_name))
        for field_name in (
            "evidence_created_at",
            "evidence_observed_at",
            "packet_updated_at",
        ):
            object.__setattr__(self, field_name, _as_utc(field_name, getattr(self, field_name)))
        object.__setattr__(
            self,
            "source_published_at",
            _as_optional_utc("source_published_at", self.source_published_at),
        )
        object.__setattr__(
            self,
            "source_count",
            _normalize_positive_count("source_count", self.source_count),
        )
        for field_name in (
            "observation_lag_seconds",
            "packet_update_lag_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_seconds(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "future_timestamp_count",
            _normalize_nonnegative_count(
                "future_timestamp_count",
                self.future_timestamp_count,
            ),
        )
        _require_member("status", self.status, STATUSES)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        _validate_row(self)
        require_paper_only_flags(
            "ResearchPacketEvidenceTimestampIntegrityGateV2Row",
            self,
        )


@dataclass(frozen=True)
class ResearchPacketEvidenceTimestampIntegrityGateV2ReasonCodeCount:
    reason_code: str
    count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_member("reason_code", self.reason_code, REASON_CODES)
        if self.reason_code in (
            "timestamp_integrity_clear",
            "timestamp_integrity_empty",
        ):
            raise ValueError("reason_code_counts only include actionable reason codes")
        object.__setattr__(
            self,
            "count",
            _normalize_nonnegative_count("count", self.count),
        )
        require_paper_only_flags(
            "ResearchPacketEvidenceTimestampIntegrityGateV2ReasonCodeCount",
            self,
        )


@dataclass(frozen=True)
class ResearchPacketEvidenceTimestampIntegrityGateV2Report:
    generated_at: datetime
    config_version: str
    packet_count: Decimal
    pass_packet_count: Decimal
    watch_packet_count: Decimal
    block_packet_count: Decimal
    future_timestamp_packet_count: Decimal
    stale_packet_update_count: Decimal
    long_observation_lag_count: Decimal
    max_observation_lag_seconds: Decimal
    report_status: str
    reason_codes: tuple[str, ...]
    reason_code_counts: tuple[ResearchPacketEvidenceTimestampIntegrityGateV2ReasonCodeCount, ...]
    derived_validation_digest: str
    rows: tuple[ResearchPacketEvidenceTimestampIntegrityGateV2Row, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        for field_name in (
            "packet_count",
            "pass_packet_count",
            "watch_packet_count",
            "block_packet_count",
            "future_timestamp_packet_count",
            "stale_packet_update_count",
            "long_observation_lag_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_count(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "max_observation_lag_seconds",
            _normalize_nonnegative_seconds(
                "max_observation_lag_seconds",
                self.max_observation_lag_seconds,
            ),
        )
        _require_member("report_status", self.report_status, REPORT_STATUSES)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        _require_sha256_digest(
            "derived_validation_digest",
            self.derived_validation_digest,
        )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        _validate_report(self)
        require_paper_only_flags(
            "ResearchPacketEvidenceTimestampIntegrityGateV2Report",
            self,
        )


def build_research_packet_evidence_timestamp_integrity_gate_v2_report(
    rows: Iterable[ResearchPacketEvidenceTimestampIntegrityInput],
    *,
    config: ResearchPacketEvidenceTimestampIntegrityGateV2Config,
    generated_at: datetime,
) -> ResearchPacketEvidenceTimestampIntegrityGateV2Report:
    if type(config) is not ResearchPacketEvidenceTimestampIntegrityGateV2Config:
        raise ValueError(
            "config must be a ResearchPacketEvidenceTimestampIntegrityGateV2Config",
        )
    require_paper_only_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    input_rows = _normalize_inputs(rows)
    packet_rows = tuple(
        _row_for_input(row, config=config, generated_at=generated_at_utc)
        for row in input_rows
    )
    ordered_rows = _order_rows(packet_rows)
    reason_codes = _report_reason_codes(ordered_rows)
    report_values: dict[str, object] = {
        "generated_at": generated_at_utc,
        "config_version": config.config_version,
        "packet_count": _decimal_count(len(ordered_rows)),
        "pass_packet_count": _status_count(ordered_rows, "pass"),
        "watch_packet_count": _status_count(ordered_rows, "watch"),
        "block_packet_count": _status_count(ordered_rows, "block"),
        "future_timestamp_packet_count": _reason_count(
            ordered_rows,
            "future_timestamp_detected",
        ),
        "stale_packet_update_count": _reason_count(
            ordered_rows,
            "packet_update_stale",
        ),
        "long_observation_lag_count": _reason_count(
            ordered_rows,
            "observation_lag_long",
        ),
        "max_observation_lag_seconds": _max_observation_lag_seconds(ordered_rows),
        "report_status": _report_status_from_rows(ordered_rows),
        "reason_codes": reason_codes,
        "reason_code_counts": _reason_code_counts(ordered_rows),
        "rows": ordered_rows,
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    report_values["derived_validation_digest"] = _derived_validation_digest(report_values)
    return ResearchPacketEvidenceTimestampIntegrityGateV2Report(  # type: ignore[arg-type]
        **report_values,
    )


def research_packet_evidence_timestamp_integrity_gate_v2_payload(
    report: ResearchPacketEvidenceTimestampIntegrityGateV2Report | dict[str, Any],
) -> dict[str, Any]:
    if type(report) is ResearchPacketEvidenceTimestampIntegrityGateV2Report:
        require_paper_only_flags("report", report)
        _reject_unsafe_surface_fields(
            "research packet evidence timestamp integrity gate v2 report",
            report,
        )
        payload = json_ready_no_floats(report)
    elif type(report) is dict:
        _reject_unsafe_surface_fields(
            "research packet evidence timestamp integrity gate v2 payload",
            report,
        )
        _reject_payload_numeric_values(report)
        _require_payload_hard_flags("payload", report, require_root=True)
        _validate_payload_digest(report)
        payload = json_ready_no_floats(report)
    else:
        raise ValueError(
            "report must be a ResearchPacketEvidenceTimestampIntegrityGateV2Report",
        )
    _reject_unsafe_surface_fields(
        "research packet evidence timestamp integrity gate v2 report",
        payload,
    )
    _reject_payload_numeric_values(payload)
    _require_payload_hard_flags("payload", payload, require_root=True)
    _validate_payload_digest(payload)
    return payload


def _row_for_input(
    row: ResearchPacketEvidenceTimestampIntegrityInput,
    *,
    config: ResearchPacketEvidenceTimestampIntegrityGateV2Config,
    generated_at: datetime,
) -> ResearchPacketEvidenceTimestampIntegrityGateV2Row:
    observation_lag_seconds = _seconds_between(
        row.evidence_observed_at,
        row.evidence_created_at,
        "observation_lag_seconds",
    )
    packet_update_lag_seconds = _seconds_between(
        row.packet_updated_at,
        row.evidence_observed_at,
        "packet_update_lag_seconds",
    )
    future_timestamp_count = _future_timestamp_count(row, generated_at)
    reason_codes = _row_reason_codes(
        future_timestamp_count=future_timestamp_count,
        packet_update_lag_seconds=packet_update_lag_seconds,
        max_packet_update_lag_seconds=config.max_packet_update_lag_seconds,
        observation_lag_seconds=observation_lag_seconds,
        max_observation_lag_seconds=config.max_observation_lag_seconds,
    )
    return ResearchPacketEvidenceTimestampIntegrityGateV2Row(
        packet_id=row.packet_id,
        event_slug=row.event_slug,
        category=row.category,
        evidence_created_at=row.evidence_created_at,
        evidence_observed_at=row.evidence_observed_at,
        packet_updated_at=row.packet_updated_at,
        source_published_at=row.source_published_at,
        source_count=row.source_count,
        observation_lag_seconds=observation_lag_seconds,
        packet_update_lag_seconds=packet_update_lag_seconds,
        future_timestamp_count=future_timestamp_count,
        status=_status_from_reason_codes(reason_codes),
        reason_codes=reason_codes,
    )


def _row_reason_codes(
    *,
    future_timestamp_count: Decimal,
    packet_update_lag_seconds: Decimal,
    max_packet_update_lag_seconds: Decimal,
    observation_lag_seconds: Decimal,
    max_observation_lag_seconds: Decimal,
) -> tuple[str, ...]:
    reasons: list[str] = []
    if future_timestamp_count > ZERO_COUNT:
        reasons.append("future_timestamp_detected")
    if packet_update_lag_seconds > max_packet_update_lag_seconds:
        reasons.append("packet_update_stale")
    if observation_lag_seconds > max_observation_lag_seconds:
        reasons.append("observation_lag_long")
    if not reasons:
        reasons.append("timestamp_integrity_clear")
    return tuple(reasons)


def _status_from_reason_codes(reason_codes: tuple[str, ...]) -> str:
    if reason_codes == ("timestamp_integrity_clear",):
        return "pass"
    if "future_timestamp_detected" in reason_codes:
        return "block"
    return "watch"


def _report_status_from_rows(
    rows: tuple[ResearchPacketEvidenceTimestampIntegrityGateV2Row, ...],
) -> str:
    if not rows:
        return "empty"
    if any(row.status == "block" for row in rows):
        return "block"
    if any(row.status == "watch" for row in rows):
        return "watch"
    return "pass"


def _report_reason_codes(
    rows: tuple[ResearchPacketEvidenceTimestampIntegrityGateV2Row, ...],
) -> tuple[str, ...]:
    if not rows:
        return ("timestamp_integrity_empty",)
    reasons: list[str] = []
    for reason_code in REASON_CODES:
        if reason_code in (
            "timestamp_integrity_clear",
            "timestamp_integrity_empty",
        ):
            continue
        if any(reason_code in row.reason_codes for row in rows):
            reasons.append(reason_code)
    if not reasons:
        reasons.append("timestamp_integrity_clear")
    return tuple(reasons)


def _reason_code_counts(
    rows: tuple[ResearchPacketEvidenceTimestampIntegrityGateV2Row, ...],
) -> tuple[ResearchPacketEvidenceTimestampIntegrityGateV2ReasonCodeCount, ...]:
    return tuple(
        ResearchPacketEvidenceTimestampIntegrityGateV2ReasonCodeCount(
            reason_code=reason_code,
            count=_reason_count(rows, reason_code),
        )
        for reason_code in REASON_CODES
        if reason_code
        not in (
            "timestamp_integrity_clear",
            "timestamp_integrity_empty",
        )
        and _reason_count(rows, reason_code) > ZERO_COUNT
    )


def _normalize_inputs(
    value: Iterable[ResearchPacketEvidenceTimestampIntegrityInput],
) -> tuple[ResearchPacketEvidenceTimestampIntegrityInput, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError("rows must be an iterable")
    try:
        rows = tuple(value)
    except TypeError as exc:
        raise ValueError("rows must be an iterable") from exc
    seen_packet_ids: set[str] = set()
    for row in rows:
        if type(row) is not ResearchPacketEvidenceTimestampIntegrityInput:
            raise ValueError(
                "rows must contain ResearchPacketEvidenceTimestampIntegrityInput",
            )
        require_paper_only_flags("input rows", row)
        if row.packet_id in seen_packet_ids:
            raise ValueError("packet_id values must be unique")
        seen_packet_ids.add(row.packet_id)
    return rows


def _normalize_rows(
    value: Iterable[ResearchPacketEvidenceTimestampIntegrityGateV2Row],
) -> tuple[ResearchPacketEvidenceTimestampIntegrityGateV2Row, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError("rows must be an iterable")
    try:
        rows = tuple(value)
    except TypeError as exc:
        raise ValueError("rows must be an iterable") from exc
    for row in rows:
        if type(row) is not ResearchPacketEvidenceTimestampIntegrityGateV2Row:
            raise ValueError(
                "rows must contain ResearchPacketEvidenceTimestampIntegrityGateV2Row",
            )
        require_paper_only_flags("rows", row)
    return rows


def _normalize_reason_code_counts(
    value: Iterable[ResearchPacketEvidenceTimestampIntegrityGateV2ReasonCodeCount],
) -> tuple[ResearchPacketEvidenceTimestampIntegrityGateV2ReasonCodeCount, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError("reason_code_counts must be an iterable")
    try:
        counts = tuple(value)
    except TypeError as exc:
        raise ValueError("reason_code_counts must be an iterable") from exc
    seen_reason_codes: set[str] = set()
    for count in counts:
        if type(count) is not ResearchPacketEvidenceTimestampIntegrityGateV2ReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "ResearchPacketEvidenceTimestampIntegrityGateV2ReasonCodeCount",
            )
        require_paper_only_flags("reason_code_counts", count)
        if count.reason_code in seen_reason_codes:
            raise ValueError("reason_code_counts must be unique by reason_code")
        seen_reason_codes.add(count.reason_code)
    return counts


def _order_rows(
    rows: tuple[ResearchPacketEvidenceTimestampIntegrityGateV2Row, ...],
) -> tuple[ResearchPacketEvidenceTimestampIntegrityGateV2Row, ...]:
    return tuple(
        sorted(
            rows,
            key=lambda row: (
                STATUS_WEIGHT[row.status],
                -row.future_timestamp_count,
                -row.observation_lag_seconds,
                -row.packet_update_lag_seconds,
                row.packet_id,
                row.event_slug,
                row.category,
            ),
        ),
    )


def _validate_input(row: ResearchPacketEvidenceTimestampIntegrityInput) -> None:
    if row.evidence_observed_at < row.evidence_created_at:
        raise ValueError("evidence_observed_at must not precede evidence_created_at")
    if row.packet_updated_at < row.evidence_observed_at:
        raise ValueError("packet_updated_at must not precede evidence_observed_at")
    if (
        row.source_published_at is not None
        and row.source_published_at > row.evidence_created_at
    ):
        raise ValueError("source_published_at must not be after evidence_created_at")


def _validate_row(row: ResearchPacketEvidenceTimestampIntegrityGateV2Row) -> None:
    _validate_input(
        ResearchPacketEvidenceTimestampIntegrityInput(
            packet_id=row.packet_id,
            event_slug=row.event_slug,
            category=row.category,
            evidence_created_at=row.evidence_created_at,
            evidence_observed_at=row.evidence_observed_at,
            packet_updated_at=row.packet_updated_at,
            source_published_at=row.source_published_at,
            source_count=row.source_count,
        ),
    )
    if row.observation_lag_seconds != _seconds_between(
        row.evidence_observed_at,
        row.evidence_created_at,
        "observation_lag_seconds",
    ):
        raise ValueError("observation_lag_seconds must match evidence timestamps")
    if row.packet_update_lag_seconds != _seconds_between(
        row.packet_updated_at,
        row.evidence_observed_at,
        "packet_update_lag_seconds",
    ):
        raise ValueError("packet_update_lag_seconds must match packet timestamps")
    if row.status != _status_from_reason_codes(row.reason_codes):
        raise ValueError("status must match reason_codes")
    if row.status == "pass":
        if row.reason_codes != ("timestamp_integrity_clear",):
            raise ValueError("pass rows require clear reason")
        if row.future_timestamp_count != ZERO_COUNT:
            raise ValueError("pass rows cannot have future timestamps")
    elif row.reason_codes == ("timestamp_integrity_clear",):
        raise ValueError("non-pass rows cannot use clear reason")


def _validate_report(report: ResearchPacketEvidenceTimestampIntegrityGateV2Report) -> None:
    if report.packet_count != _decimal_count(len(report.rows)):
        raise ValueError("packet_count must match rows")
    if report.pass_packet_count != _status_count(report.rows, "pass"):
        raise ValueError("pass_packet_count must match rows")
    if report.watch_packet_count != _status_count(report.rows, "watch"):
        raise ValueError("watch_packet_count must match rows")
    if report.block_packet_count != _status_count(report.rows, "block"):
        raise ValueError("block_packet_count must match rows")
    if report.future_timestamp_packet_count != _reason_count(
        report.rows,
        "future_timestamp_detected",
    ):
        raise ValueError("future_timestamp_packet_count must match rows")
    if report.stale_packet_update_count != _reason_count(
        report.rows,
        "packet_update_stale",
    ):
        raise ValueError("stale_packet_update_count must match rows")
    if report.long_observation_lag_count != _reason_count(
        report.rows,
        "observation_lag_long",
    ):
        raise ValueError("long_observation_lag_count must match rows")
    if report.max_observation_lag_seconds != _max_observation_lag_seconds(report.rows):
        raise ValueError("max_observation_lag_seconds must match rows")
    if report.report_status != _report_status_from_rows(report.rows):
        raise ValueError("report_status must match rows")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")
    if report.reason_code_counts != _reason_code_counts(report.rows):
        raise ValueError("reason_code_counts must match rows")
    if report.rows != _order_rows(report.rows):
        raise ValueError("rows must use deterministic ordering")
    if report.derived_validation_digest != _derived_validation_digest(asdict(report)):
        raise ValueError("derived_validation_digest must match report fields")


def _status_count(
    rows: tuple[ResearchPacketEvidenceTimestampIntegrityGateV2Row, ...],
    status: str,
) -> Decimal:
    return _decimal_count(sum(1 for row in rows if row.status == status))


def _reason_count(
    rows: tuple[ResearchPacketEvidenceTimestampIntegrityGateV2Row, ...],
    reason_code: str,
) -> Decimal:
    return _decimal_count(
        sum(1 for row in rows if reason_code in row.reason_codes),
    )


def _max_observation_lag_seconds(
    rows: tuple[ResearchPacketEvidenceTimestampIntegrityGateV2Row, ...],
) -> Decimal:
    if not rows:
        return ZERO_SECONDS
    return max(row.observation_lag_seconds for row in rows)


def _future_timestamp_count(
    row: ResearchPacketEvidenceTimestampIntegrityInput,
    generated_at: datetime,
) -> Decimal:
    values = (
        row.evidence_created_at,
        row.evidence_observed_at,
        row.packet_updated_at,
        row.source_published_at,
    )
    return _decimal_count(
        sum(1 for value in values if value is not None and value > generated_at),
    )


def _seconds_between(later: datetime, earlier: datetime, field_name: str) -> Decimal:
    delta = later - earlier
    seconds = Decimal(delta.days * 86400 + delta.seconds)
    if delta.microseconds:
        seconds += Decimal(delta.microseconds) / Decimal("1000000")
    return _normalize_nonnegative_seconds(field_name, seconds)


def _derived_validation_digest(values: object) -> str:
    canonical = _canonical_payload_for_digest(values)
    encoded = json.dumps(
        canonical,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _canonical_payload_for_digest(value: object) -> object:
    if value is None or type(value) is bool or type(value) is str:
        return value
    if is_dataclass(value) and not isinstance(value, type):
        return _canonical_payload_for_digest(asdict(value))
    if isinstance(value, Decimal):
        if not value.is_finite():
            raise ValueError("derived_validation_digest Decimal values must be finite")
        return str(value)
    if type(value) is datetime:
        if value.tzinfo is None:
            raise ValueError("derived_validation_digest datetimes must be timezone-aware")
        return value.astimezone(UTC).isoformat()
    if isinstance(value, dict):
        ready: dict[str, object] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            if key == "derived_validation_digest":
                continue
            ready[key] = _canonical_payload_for_digest(item)
        return ready
    if isinstance(value, (list, tuple)):
        return [_canonical_payload_for_digest(item) for item in value]
    raise ValueError("derived_validation_digest values must be JSON serializable")


def _validate_payload_digest(payload: dict[str, Any]) -> None:
    digest = payload.get("derived_validation_digest")
    _require_sha256_digest("derived_validation_digest", digest)
    if digest != _derived_validation_digest(payload):
        raise ValueError("derived_validation_digest must match payload fields")


def _reject_unsafe_surface_fields(label: str, value: object) -> None:
    if is_dataclass(value) and not isinstance(value, type):
        _reject_unsafe_surface_fields(label, asdict(value))
        return
    if isinstance(value, dict):
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            if _has_unsafe_surface_fragment(key):
                raise ValueError(f"unsafe live surface field in {label}: {key}")
            _reject_unsafe_surface_fields(label, item)
        return
    if isinstance(value, (list, tuple)):
        for item in value:
            _reject_unsafe_surface_fields(label, item)


def _has_unsafe_surface_fragment(value: str) -> bool:
    normalized = value.lower()
    return any(fragment in normalized for fragment in UNSAFE_SURFACE_FIELD_FRAGMENTS)


def _reject_payload_numeric_values(value: object) -> None:
    if type(value) is bool or value is None:
        return
    if isinstance(value, Decimal) or type(value) in (float, int):
        raise ValueError("payload numeric metrics must use Decimal-string values")
    if isinstance(value, dict):
        for item in value.values():
            _reject_payload_numeric_values(item)
        return
    if isinstance(value, (list, tuple)):
        for item in value:
            _reject_payload_numeric_values(item)


def _require_payload_hard_flags(
    label: str,
    value: object,
    *,
    require_root: bool = False,
) -> None:
    if isinstance(value, dict):
        flag_names = ("paper_only", "report_only", "readonly")
        requires_flags = require_root or any(flag_name in value for flag_name in flag_names)
        if requires_flags:
            for flag_name in flag_names:
                if value.get(flag_name) is not True:
                    raise ValueError(f"{flag_name} must be True for {label}")
        for item in value.values():
            _require_payload_hard_flags(label, item)
        return
    if isinstance(value, (list, tuple)):
        for item in value:
            _require_payload_hard_flags(label, item)


def _require_sha256_digest(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a SHA-256 hex digest")
    if len(value) != 64 or any(character not in "0123456789abcdef" for character in value):
        raise ValueError(f"{field_name} must be a SHA-256 hex digest")


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _as_optional_utc(field_name: str, value: object) -> datetime | None:
    if value is None:
        return None
    return _as_utc(field_name, value)


def _normalize_nonnegative_seconds(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value < ZERO_SECONDS:
        raise ValueError(f"{field_name} must be nonnegative")
    return _quantize_decimal(decimal_value, SECONDS_QUANTUM)


def _normalize_nonnegative_count(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value < ZERO_COUNT:
        raise ValueError(f"{field_name} must be nonnegative")
    normalized = decimal_value.quantize(COUNT_QUANTUM)
    if normalized != decimal_value:
        raise ValueError(f"{field_name} must be a whole Decimal count")
    return normalized


def _normalize_positive_count(field_name: str, value: object) -> Decimal:
    decimal_value = _normalize_nonnegative_count(field_name, value)
    if decimal_value <= ZERO_COUNT:
        raise ValueError(f"{field_name} must be positive")
    return decimal_value


def _decimal_count(value: int) -> Decimal:
    if type(value) is not int or value < 0:
        raise ValueError("count must be a nonnegative int")
    return Decimal(value).quantize(COUNT_QUANTUM)


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return value


def _quantize_decimal(value: Decimal, quantum: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        normalized = value.quantize(quantum)
    if normalized == normalized.to_integral_value():
        return normalized.quantize(COUNT_QUANTUM)
    return normalized


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value:
        raise ValueError(f"{field_name} is required")
    if value != value.strip():
        raise ValueError(f"{field_name} must not include surrounding whitespace")
    if any(character.isspace() for character in value):
        raise ValueError(f"{field_name} must not include whitespace")
    if _has_unsafe_surface_fragment(value):
        raise ValueError(f"{field_name} contains unsafe live surface text")


def _require_member(field_name: str, value: object, allowed: tuple[str, ...]) -> None:
    if type(value) is not str or value not in allowed:
        raise ValueError(f"{field_name} must be one of {allowed}")


def _normalize_reason_codes(field_name: str, value: object) -> tuple[str, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError(f"{field_name} must be an iterable of reason codes")
    try:
        codes = tuple(value)  # type: ignore[arg-type]
    except TypeError as exc:
        raise ValueError(f"{field_name} must be an iterable of reason codes") from exc
    if not codes:
        raise ValueError(f"{field_name} must not be empty")
    seen: set[str] = set()
    for code in codes:
        _require_member(field_name, code, REASON_CODES)
        if code in seen:
            raise ValueError(f"{field_name} must not contain duplicate reason codes")
        seen.add(code)
    clear_codes = {"timestamp_integrity_clear", "timestamp_integrity_empty"}
    if len(clear_codes.intersection(codes)) > 0 and len(codes) != 1:
        raise ValueError(f"{field_name} clear or empty reason must stand alone")
    return codes


__all__ = (
    "DEFAULT_RESEARCH_PACKET_EVIDENCE_TIMESTAMP_INTEGRITY_GATE_V2_CONFIG_VERSION",
    "ResearchPacketEvidenceTimestampIntegrityGateV2Config",
    "ResearchPacketEvidenceTimestampIntegrityInput",
    "ResearchPacketEvidenceTimestampIntegrityGateV2Row",
    "ResearchPacketEvidenceTimestampIntegrityGateV2ReasonCodeCount",
    "ResearchPacketEvidenceTimestampIntegrityGateV2Report",
    "build_research_packet_evidence_timestamp_integrity_gate_v2_report",
    "research_packet_evidence_timestamp_integrity_gate_v2_payload",
)
