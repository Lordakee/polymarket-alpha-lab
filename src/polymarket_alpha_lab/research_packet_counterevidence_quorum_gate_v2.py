"""Phase 1 read-only counterevidence quorum gate."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Iterable
from dataclasses import asdict, dataclass, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal, ROUND_HALF_EVEN, localcontext
from typing import Any


DEFAULT_RESEARCH_PACKET_COUNTEREVIDENCE_QUORUM_GATE_V2_CONFIG_VERSION = (
    "research-packet-counterevidence-quorum-gate-v2"
)

QUANTUM = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
STATUSES = frozenset(("pass", "watch", "block"))
REPORT_STATUSES = frozenset(("pass", "watch", "block", "empty"))
REPORT_PAYLOAD_FIELDS = frozenset(
    (
        "generated_at",
        "config_version",
        "report_status",
        "packet_count",
        "pass_count",
        "watch_count",
        "block_count",
        "missing_counterevidence_count",
        "severe_contradiction_count",
        "insufficient_reviewer_count",
        "min_quorum_ratio",
        "rows",
        "reason_code_counts",
        "derived_validation_digest",
        "paper_only",
        "report_only",
        "readonly",
    ),
)
ROW_PAYLOAD_FIELDS = frozenset(
    (
        "packet_id",
        "event_slug",
        "category",
        "supporting_source_count",
        "counterevidence_source_count",
        "independent_counterevidence_family_count",
        "contradiction_severity_score",
        "reviewer_count",
        "counterevidence_quorum_ratio",
        "status",
        "reason_codes",
        "paper_only",
        "report_only",
        "readonly",
    ),
)
REASON_CODE_COUNT_PAYLOAD_FIELDS = frozenset(
    (
        "reason_code",
        "count",
        "paper_only",
        "report_only",
        "readonly",
    ),
)
REASON_CODE_SEQUENCE = (
    "counterevidence_quorum_met",
    "counterevidence_quorum_below_minimum",
    "insufficient_independent_counterevidence_families",
    "insufficient_reviewers",
    "missing_counterevidence",
    "severe_contradiction",
)
UNSAFE_PUBLIC_FRAGMENTS = frozenset(
    (
        "li" + "ve",
        "au" + "th",
        "wal" + "let",
        "or" + "der",
        "net" + "work",
        "data" + "base",
        "per" + "sist",
        "sign" + "ing",
        "muta" + "tion",
        "b" + "uy",
        "se" + "ll",
        "tra" + "de",
    ),
)


@dataclass(frozen=True)
class ResearchPacketCounterevidenceQuorumGateV2Config:
    config_version: str = (
        DEFAULT_RESEARCH_PACKET_COUNTEREVIDENCE_QUORUM_GATE_V2_CONFIG_VERSION
    )
    min_counterevidence_quorum_ratio: Decimal = Decimal("0.500000")
    min_independent_counterevidence_family_count: Decimal = Decimal("2")
    min_reviewer_count: Decimal = Decimal("2")
    severe_contradiction_threshold: Decimal = Decimal("0.750000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if (
            self.config_version
            != DEFAULT_RESEARCH_PACKET_COUNTEREVIDENCE_QUORUM_GATE_V2_CONFIG_VERSION
        ):
            raise ValueError("config_version is not supported")
        object.__setattr__(
            self,
            "min_counterevidence_quorum_ratio",
            _ratio(
                "min_counterevidence_quorum_ratio",
                self.min_counterevidence_quorum_ratio,
            ),
        )
        object.__setattr__(
            self,
            "min_independent_counterevidence_family_count",
            _count(
                "min_independent_counterevidence_family_count",
                self.min_independent_counterevidence_family_count,
            ),
        )
        object.__setattr__(
            self,
            "min_reviewer_count",
            _count("min_reviewer_count", self.min_reviewer_count),
        )
        object.__setattr__(
            self,
            "severe_contradiction_threshold",
            _ratio(
                "severe_contradiction_threshold",
                self.severe_contradiction_threshold,
            ),
        )
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class ResearchPacketCounterevidenceQuorumGateV2Input:
    packet_id: str
    event_slug: str
    category: str
    supporting_source_count: Decimal
    counterevidence_source_count: Decimal
    independent_counterevidence_family_count: Decimal
    contradiction_severity_score: Decimal
    reviewer_count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _public_text("packet_id", self.packet_id)
        _public_text("event_slug", self.event_slug)
        _public_text("category", self.category)
        for name in (
            "supporting_source_count",
            "counterevidence_source_count",
            "independent_counterevidence_family_count",
            "reviewer_count",
        ):
            object.__setattr__(self, name, _count(name, getattr(self, name)))
        object.__setattr__(
            self,
            "contradiction_severity_score",
            _ratio("contradiction_severity_score", self.contradiction_severity_score),
        )
        _require_hard_flags("input", self)


@dataclass(frozen=True)
class ResearchPacketCounterevidenceQuorumGateV2Row:
    packet_id: str
    event_slug: str
    category: str
    supporting_source_count: Decimal
    counterevidence_source_count: Decimal
    independent_counterevidence_family_count: Decimal
    contradiction_severity_score: Decimal
    reviewer_count: Decimal
    counterevidence_quorum_ratio: Decimal
    status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _public_text("packet_id", self.packet_id)
        _public_text("event_slug", self.event_slug)
        _public_text("category", self.category)
        for name in (
            "supporting_source_count",
            "counterevidence_source_count",
            "independent_counterevidence_family_count",
            "reviewer_count",
        ):
            object.__setattr__(self, name, _count(name, getattr(self, name)))
        for name in ("contradiction_severity_score", "counterevidence_quorum_ratio"):
            object.__setattr__(self, name, _ratio(name, getattr(self, name)))
        _status("status", self.status)
        object.__setattr__(self, "reason_codes", _reason_codes(self.reason_codes))
        _require_hard_flags("row", self)


@dataclass(frozen=True)
class ResearchPacketCounterevidenceQuorumGateV2ReasonCodeCount:
    reason_code: str
    count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "reason_code", _reason_code(self.reason_code))
        object.__setattr__(self, "count", _count("count", self.count))
        _require_hard_flags("reason code count", self)


@dataclass(frozen=True)
class ResearchPacketCounterevidenceQuorumGateV2Report:
    generated_at: datetime
    config_version: str
    report_status: str
    packet_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    missing_counterevidence_count: Decimal
    severe_contradiction_count: Decimal
    insufficient_reviewer_count: Decimal
    min_quorum_ratio: Decimal
    rows: tuple[ResearchPacketCounterevidenceQuorumGateV2Row, ...]
    reason_code_counts: tuple[
        ResearchPacketCounterevidenceQuorumGateV2ReasonCodeCount,
        ...,
    ]
    derived_validation_digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        if (
            self.config_version
            != DEFAULT_RESEARCH_PACKET_COUNTEREVIDENCE_QUORUM_GATE_V2_CONFIG_VERSION
        ):
            raise ValueError("config_version is not supported")
        _report_status("report_status", self.report_status)
        for name in (
            "packet_count",
            "pass_count",
            "watch_count",
            "block_count",
            "missing_counterevidence_count",
            "severe_contradiction_count",
            "insufficient_reviewer_count",
        ):
            object.__setattr__(self, name, _count(name, getattr(self, name)))
        object.__setattr__(
            self,
            "min_quorum_ratio",
            _ratio("min_quorum_ratio", self.min_quorum_ratio),
        )
        if (
            type(self.rows) is not tuple
            or not all(
                type(row) is ResearchPacketCounterevidenceQuorumGateV2Row
                for row in self.rows
            )
        ):
            raise ValueError("rows must contain counterevidence quorum rows")
        if (
            type(self.reason_code_counts) is not tuple
            or not all(
                type(count)
                is ResearchPacketCounterevidenceQuorumGateV2ReasonCodeCount
                for count in self.reason_code_counts
            )
        ):
            raise ValueError("reason_code_counts must contain reason code counts")
        _require_hard_flags("report", self)
        _hex_digest("derived_validation_digest", self.derived_validation_digest)
        if self.derived_validation_digest != _derive_digest_from_public_payload(
            _payload(self),
        ):
            raise ValueError("derived_validation_digest must match report fields")
        _report_matches(self)

    @property
    def payload(self) -> dict[str, Any]:
        return research_packet_counterevidence_quorum_gate_v2_payload(self)


def build_research_packet_counterevidence_quorum_gate_v2(
    packets: Iterable[ResearchPacketCounterevidenceQuorumGateV2Input],
    *,
    generated_at: datetime,
    config: ResearchPacketCounterevidenceQuorumGateV2Config | None = None,
) -> ResearchPacketCounterevidenceQuorumGateV2Report:
    if config is None:
        config = ResearchPacketCounterevidenceQuorumGateV2Config()
    if type(config) is not ResearchPacketCounterevidenceQuorumGateV2Config:
        raise ValueError("config must be a counterevidence quorum config")
    normalized_packets = tuple(packets)
    if not all(
        type(packet) is ResearchPacketCounterevidenceQuorumGateV2Input
        for packet in normalized_packets
    ):
        raise ValueError("packets must contain counterevidence quorum input rows")
    rows = tuple(sorted((_row(packet, config) for packet in normalized_packets), key=_row_key))
    values = {
        "generated_at": _as_utc("generated_at", generated_at),
        "config_version": config.config_version,
        "report_status": _overall_status(rows),
        "packet_count": _decimal_len(rows),
        "pass_count": _status_count(rows, "pass"),
        "watch_count": _status_count(rows, "watch"),
        "block_count": _status_count(rows, "block"),
        "missing_counterevidence_count": _reason_count(rows, "missing_counterevidence"),
        "severe_contradiction_count": _reason_count(rows, "severe_contradiction"),
        "insufficient_reviewer_count": _reason_count(rows, "insufficient_reviewers"),
        "min_quorum_ratio": min(
            (row.counterevidence_quorum_ratio for row in rows),
            default=ZERO,
        ),
        "rows": rows,
        "reason_code_counts": _reason_code_counts(rows),
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    return ResearchPacketCounterevidenceQuorumGateV2Report(
        **values,
        derived_validation_digest=_derive_digest_from_public_payload(_payload(values)),
    )


def research_packet_counterevidence_quorum_gate_v2_payload(
    report: ResearchPacketCounterevidenceQuorumGateV2Report | dict[str, Any],
) -> dict[str, Any]:
    if type(report) is ResearchPacketCounterevidenceQuorumGateV2Report:
        _require_hard_flags("report", report)
        payload = _payload(report)
    elif type(report) is dict:
        payload = _json_ready(report)
    else:
        raise ValueError("report must be a counterevidence quorum gate report")
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    _reject_unsafe_public_payload(payload)
    _require_supported_payload(payload)
    _require_hard_flags("payload", _DictFlags(payload))
    _require_payload_digest(payload)
    return payload


def derive_research_packet_counterevidence_quorum_gate_v2_digest(
    report: ResearchPacketCounterevidenceQuorumGateV2Report | dict[str, Any],
) -> str:
    if type(report) is ResearchPacketCounterevidenceQuorumGateV2Report:
        payload = _payload(report)
    elif type(report) is dict:
        payload = _json_ready(report)
    else:
        raise ValueError("report must be a counterevidence quorum gate report")
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    _reject_unsafe_public_payload(payload)
    _require_supported_payload(payload, digest_required=False)
    _require_hard_flags("payload", _DictFlags(payload))
    return _derive_digest_from_public_payload(payload)


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


def _row(
    packet: ResearchPacketCounterevidenceQuorumGateV2Input,
    config: ResearchPacketCounterevidenceQuorumGateV2Config,
) -> ResearchPacketCounterevidenceQuorumGateV2Row:
    quorum_ratio = _counterevidence_quorum_ratio(packet)
    reasons = _row_reason_codes(packet, quorum_ratio, config)
    return ResearchPacketCounterevidenceQuorumGateV2Row(
        packet_id=packet.packet_id,
        event_slug=packet.event_slug,
        category=packet.category,
        supporting_source_count=packet.supporting_source_count,
        counterevidence_source_count=packet.counterevidence_source_count,
        independent_counterevidence_family_count=(
            packet.independent_counterevidence_family_count
        ),
        contradiction_severity_score=packet.contradiction_severity_score,
        reviewer_count=packet.reviewer_count,
        counterevidence_quorum_ratio=quorum_ratio,
        status=_row_status(reasons),
        reason_codes=reasons,
    )


def _counterevidence_quorum_ratio(
    packet: ResearchPacketCounterevidenceQuorumGateV2Input,
) -> Decimal:
    if packet.supporting_source_count == ZERO:
        if packet.counterevidence_source_count == ZERO:
            return ZERO
        return ONE
    return _clamp_ratio(
        _q(packet.counterevidence_source_count / packet.supporting_source_count),
    )


def _row_reason_codes(
    packet: ResearchPacketCounterevidenceQuorumGateV2Input,
    quorum_ratio: Decimal,
    config: ResearchPacketCounterevidenceQuorumGateV2Config,
) -> tuple[str, ...]:
    reasons: list[str] = []
    if packet.counterevidence_source_count == ZERO:
        reasons.append("missing_counterevidence")
    elif quorum_ratio < config.min_counterevidence_quorum_ratio:
        reasons.append("counterevidence_quorum_below_minimum")
    if packet.counterevidence_source_count > ZERO:
        if (
            packet.independent_counterevidence_family_count
            < config.min_independent_counterevidence_family_count
        ):
            reasons.append("insufficient_independent_counterevidence_families")
        if packet.reviewer_count < config.min_reviewer_count:
            reasons.append("insufficient_reviewers")
    if packet.contradiction_severity_score >= config.severe_contradiction_threshold:
        reasons.append("severe_contradiction")
    if not reasons:
        reasons.append("counterevidence_quorum_met")
    return _reason_codes(tuple(reasons))


def _row_status(reason_codes: tuple[str, ...]) -> str:
    if "missing_counterevidence" in reason_codes or "severe_contradiction" in reason_codes:
        return "block"
    if reason_codes == ("counterevidence_quorum_met",):
        return "pass"
    return "watch"


def _overall_status(
    rows: tuple[ResearchPacketCounterevidenceQuorumGateV2Row, ...],
) -> str:
    if not rows:
        return "empty"
    if any(row.status == "block" for row in rows):
        return "block"
    if any(row.status == "watch" for row in rows):
        return "watch"
    return "pass"


def _reason_code_counts(
    rows: tuple[ResearchPacketCounterevidenceQuorumGateV2Row, ...],
) -> tuple[ResearchPacketCounterevidenceQuorumGateV2ReasonCodeCount, ...]:
    return tuple(
        ResearchPacketCounterevidenceQuorumGateV2ReasonCodeCount(
            reason_code=reason_code,
            count=_reason_count(rows, reason_code),
        )
        for reason_code in REASON_CODE_SEQUENCE
        if _reason_count(rows, reason_code) > ZERO
    )


def _reason_count(
    rows: tuple[ResearchPacketCounterevidenceQuorumGateV2Row, ...],
    reason_code: str,
) -> Decimal:
    return Decimal(
        sum(1 for row in rows if reason_code in row.reason_codes),
    ).quantize(QUANTUM)


def _status_count(
    rows: tuple[ResearchPacketCounterevidenceQuorumGateV2Row, ...],
    status: str,
) -> Decimal:
    return Decimal(sum(1 for row in rows if row.status == status)).quantize(QUANTUM)


def _decimal_len(rows: tuple[object, ...]) -> Decimal:
    return Decimal(len(rows)).quantize(QUANTUM)


def _row_key(row: ResearchPacketCounterevidenceQuorumGateV2Row) -> tuple[str, str, str]:
    return (row.packet_id, row.event_slug, row.category)


def _report_matches(report: ResearchPacketCounterevidenceQuorumGateV2Report) -> None:
    if report.rows != tuple(sorted(report.rows, key=_row_key)):
        raise ValueError("rows must use deterministic order")
    if report.packet_count != _decimal_len(report.rows):
        raise ValueError("packet_count must match rows")
    if report.pass_count != _status_count(report.rows, "pass"):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _status_count(report.rows, "watch"):
        raise ValueError("watch_count must match rows")
    if report.block_count != _status_count(report.rows, "block"):
        raise ValueError("block_count must match rows")
    if report.missing_counterevidence_count != _reason_count(
        report.rows,
        "missing_counterevidence",
    ):
        raise ValueError("missing_counterevidence_count must match rows")
    if report.severe_contradiction_count != _reason_count(
        report.rows,
        "severe_contradiction",
    ):
        raise ValueError("severe_contradiction_count must match rows")
    if report.insufficient_reviewer_count != _reason_count(
        report.rows,
        "insufficient_reviewers",
    ):
        raise ValueError("insufficient_reviewer_count must match rows")
    if report.min_quorum_ratio != min(
        (row.counterevidence_quorum_ratio for row in report.rows),
        default=ZERO,
    ):
        raise ValueError("min_quorum_ratio must match rows")
    if report.report_status != _overall_status(report.rows):
        raise ValueError("report_status must match rows")
    if report.reason_code_counts != _reason_code_counts(report.rows):
        raise ValueError("reason_code_counts must match rows")


def _payload(value: object) -> Any:
    return _json_ready(value)


def _json_ready(value: object) -> Any:
    if value is None:
        return None
    if is_dataclass(value) and not isinstance(value, type):
        return _json_ready(asdict(value))
    if type(value) is Decimal:
        if not value.is_finite():
            raise ValueError("JSON Decimal value must be finite")
        return str(value)
    if type(value) is datetime:
        return _as_utc("datetime", value).isoformat().replace("+00:00", "Z")
    if type(value) is bool:
        return value
    if type(value) is str:
        return value
    if type(value) is int:
        raise ValueError("JSON numeric value must use Decimal")
    if type(value) is float:
        raise ValueError("JSON value must not be a float")
    if type(value) is dict:
        ready: dict[str, Any] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            ready[key] = _json_ready(item)
        return ready
    if type(value) in (list, tuple):
        return [_json_ready(item) for item in value]
    raise ValueError("value is not JSON serializable")


def _derive_digest_from_public_payload(payload: dict[str, Any]) -> str:
    public_payload = {
        key: value for key, value in payload.items() if key != "derived_validation_digest"
    }
    encoded = json.dumps(
        public_payload,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _require_payload_digest(payload: dict[str, Any]) -> None:
    digest = payload.get("derived_validation_digest")
    _hex_digest("derived_validation_digest", digest)
    if digest != _derive_digest_from_public_payload(payload):
        raise ValueError("derived_validation_digest must match payload fields")


def _reject_unsafe_public_payload(value: object) -> None:
    if type(value) is dict:
        for key, item in value.items():
            if _unsafe_text(key):
                raise ValueError("unsafe public payload key")
            _reject_unsafe_public_payload(item)
        return
    if type(value) is list:
        for item in value:
            _reject_unsafe_public_payload(item)
        return
    if type(value) is str and _unsafe_text(value):
        raise ValueError("unsafe public payload value")


def _require_supported_payload(
    payload: dict[str, Any],
    *,
    digest_required: bool = True,
) -> None:
    expected_report_fields = set(REPORT_PAYLOAD_FIELDS)
    if not digest_required:
        expected_report_fields.remove("derived_validation_digest")
        allowed_report_fields = set(REPORT_PAYLOAD_FIELDS)
    else:
        allowed_report_fields = expected_report_fields
    for key in payload:
        if key not in allowed_report_fields:
            raise ValueError("payload field is not supported")
    missing = expected_report_fields - set(payload)
    if missing:
        raise ValueError("payload field is missing")
    _require_payload_report_values(payload, digest_required=digest_required)
    rows = payload.get("rows")
    if type(rows) is not list:
        raise ValueError("rows must be a list")
    for row in rows:
        if type(row) is not dict:
            raise ValueError("rows must contain payload objects")
        for key in row:
            if key not in ROW_PAYLOAD_FIELDS:
                raise ValueError("payload field is not supported")
        if set(row) != set(ROW_PAYLOAD_FIELDS):
            raise ValueError("payload field is missing")
        _require_payload_row_values(row)
        _require_hard_flags("row payload", _DictFlags(row))
    reason_code_counts = payload.get("reason_code_counts")
    if type(reason_code_counts) is not list:
        raise ValueError("reason_code_counts must be a list")
    for count in reason_code_counts:
        if type(count) is not dict:
            raise ValueError("reason_code_counts must contain payload objects")
        for key in count:
            if key not in REASON_CODE_COUNT_PAYLOAD_FIELDS:
                raise ValueError("payload field is not supported")
        if set(count) != set(REASON_CODE_COUNT_PAYLOAD_FIELDS):
            raise ValueError("payload field is missing")
        _reason_code(count.get("reason_code"))
        _payload_count_string("count", count.get("count"))
        _require_hard_flags("reason code count payload", _DictFlags(count))


def _require_payload_report_values(
    payload: dict[str, Any],
    *,
    digest_required: bool,
) -> None:
    _payload_datetime(payload.get("generated_at"))
    if (
        payload.get("config_version")
        != DEFAULT_RESEARCH_PACKET_COUNTEREVIDENCE_QUORUM_GATE_V2_CONFIG_VERSION
    ):
        raise ValueError("config_version is not supported")
    _report_status("report_status", payload.get("report_status"))
    for name in (
        "packet_count",
        "pass_count",
        "watch_count",
        "block_count",
        "missing_counterevidence_count",
        "severe_contradiction_count",
        "insufficient_reviewer_count",
    ):
        _payload_count_string(name, payload.get(name))
    _payload_ratio_string("min_quorum_ratio", payload.get("min_quorum_ratio"))
    if digest_required:
        _hex_digest("derived_validation_digest", payload.get("derived_validation_digest"))
    _require_hard_flags("payload", _DictFlags(payload))


def _require_payload_row_values(row: dict[str, Any]) -> None:
    _public_text("packet_id", row.get("packet_id"))
    _public_text("event_slug", row.get("event_slug"))
    _public_text("category", row.get("category"))
    for name in (
        "supporting_source_count",
        "counterevidence_source_count",
        "independent_counterevidence_family_count",
        "reviewer_count",
    ):
        _payload_count_string(name, row.get(name))
    for name in ("contradiction_severity_score", "counterevidence_quorum_ratio"):
        _payload_ratio_string(name, row.get(name))
    _status("status", row.get("status"))
    reason_codes = row.get("reason_codes")
    if type(reason_codes) is not list:
        raise ValueError("reason_codes must be a list")
    _reason_codes(tuple(reason_codes))


def _payload_datetime(value: object) -> None:
    if type(value) is not str or not value.endswith("Z"):
        raise ValueError("generated_at must be a UTC timestamp string")


def _payload_count_string(name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{name} must be a Decimal string")
    result = _count(name, Decimal(value))
    if str(result) != value:
        raise ValueError(f"{name} must be a canonical Decimal string")


def _payload_ratio_string(name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{name} must be a Decimal string")
    result = _ratio(name, Decimal(value))
    if str(result) != value:
        raise ValueError(f"{name} must be a canonical Decimal string")


def _as_utc(name: str, value: datetime) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{name} must be timezone-aware")
    return value.astimezone(UTC)


def _public_text(name: str, value: object) -> str:
    if type(value) is not str or not value:
        raise ValueError(f"{name} must be a non-empty string")
    if value.strip() != value:
        raise ValueError(f"{name} must not have outer whitespace")
    if _unsafe_text(value):
        raise ValueError(f"{name} has unsafe public value")
    return value


def _require_hard_flags(name: str, value: object) -> None:
    if getattr(value, "paper_only", None) is not True:
        raise ValueError(f"{name} must be paper_only")
    if getattr(value, "report_only", None) is not True:
        raise ValueError(f"{name} must be report_only")
    if getattr(value, "readonly", None) is not True:
        raise ValueError(f"{name} must be readonly")


def _reason_codes(values: tuple[str, ...]) -> tuple[str, ...]:
    if type(values) is not tuple:
        raise ValueError("reason_codes must be a tuple")
    normalized = tuple(_reason_code(value) for value in values)
    if len(set(normalized)) != len(normalized):
        raise ValueError("reason_codes must be unique")
    return tuple(reason for reason in REASON_CODE_SEQUENCE if reason in normalized)


def _reason_code(value: str) -> str:
    if type(value) is not str or value not in REASON_CODE_SEQUENCE:
        raise ValueError("reason_code must be supported")
    return value


def _hex_digest(name: str, value: object) -> None:
    if type(value) is not str or len(value) != 64:
        raise ValueError(f"{name} must be a sha256 hex digest")
    if any(character not in "0123456789abcdef" for character in value):
        raise ValueError(f"{name} must be a sha256 hex digest")


def _unsafe_text(value: str) -> bool:
    lowered = value.lower()
    return any(fragment in lowered for fragment in UNSAFE_PUBLIC_FRAGMENTS)


def _status(name: str, value: str) -> None:
    if type(value) is not str or value not in STATUSES:
        raise ValueError(f"{name} is not supported")


def _report_status(name: str, value: str) -> None:
    if type(value) is not str or value not in REPORT_STATUSES:
        raise ValueError(f"{name} is not supported")


def _count(name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{name} must be finite")
    if value < ZERO:
        raise ValueError(f"{name} must be nonnegative")
    if value != value.to_integral_value():
        raise ValueError(f"{name} must be a whole Decimal")
    return value.quantize(QUANTUM)


def _ratio(name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{name} must be finite")
    result = _q(value)
    if result < ZERO or result > ONE:
        raise ValueError(f"{name} must be between zero and one")
    return result


def _q(value: Decimal) -> Decimal:
    with localcontext() as context:
        context.prec = 64
        context.rounding = ROUND_HALF_EVEN
        return value.quantize(QUANTUM)


def _clamp_ratio(value: Decimal) -> Decimal:
    if value < ZERO:
        return ZERO
    if value > ONE:
        return ONE
    return value


__all__ = (
    "DEFAULT_RESEARCH_PACKET_COUNTEREVIDENCE_QUORUM_GATE_V2_CONFIG_VERSION",
    "ResearchPacketCounterevidenceQuorumGateV2Config",
    "ResearchPacketCounterevidenceQuorumGateV2Input",
    "ResearchPacketCounterevidenceQuorumGateV2ReasonCodeCount",
    "ResearchPacketCounterevidenceQuorumGateV2Report",
    "ResearchPacketCounterevidenceQuorumGateV2Row",
    "build_research_packet_counterevidence_quorum_gate_v2",
    "derive_research_packet_counterevidence_quorum_gate_v2_digest",
    "research_packet_counterevidence_quorum_gate_v2_payload",
)
