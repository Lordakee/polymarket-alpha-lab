from __future__ import annotations

import hashlib
import json
from collections.abc import Iterable
from dataclasses import asdict, dataclass, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal, ROUND_HALF_EVEN, localcontext
from typing import Any


DEFAULT_RESEARCH_PACKET_DISCONFIRMING_EVIDENCE_GATE_V2_CONFIG_VERSION = (
    "research-packet-disconfirming-evidence-gate-v2"
)

Q = Decimal("0.000001")
COUNT_Q = Decimal("1")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
COUNT_ZERO = Decimal("0")
COUNT_ONE = Decimal("1")

GATE_STATUSES = frozenset(("pass", "review", "fail"))
REASON_PRIORITY = {
    "disconfirming_coverage_complete": 0,
    "disconfirming_coverage_partial": 1,
    "disconfirming_coverage_missing": 2,
    "opposition_source_present": 3,
    "missing_opposition_source": 4,
    "contradiction_penalty_high": 5,
    "contradiction_penalty_watch": 6,
    "contradiction_penalty_low": 7,
    "gate_pass": 8,
    "gate_review": 9,
    "gate_fail": 10,
}
REPORT_PAYLOAD_FIELDS = frozenset(
    (
        "generated_at",
        "config_version",
        "packet_count",
        "pass_count",
        "review_count",
        "fail_count",
        "average_gate_score",
        "min_gate_score",
        "max_contradiction_penalty_ratio",
        "rows",
        "derived_validation_digest",
        "paper_only",
        "report_only",
        "readonly",
    ),
)
ROW_PAYLOAD_FIELDS = frozenset(
    (
        "rank",
        "packet_id",
        "market_question",
        "thesis_summary",
        "disconfirming_source_count",
        "opposition_source_count",
        "supporting_source_count",
        "disconfirming_coverage_ratio",
        "opposition_coverage_ratio",
        "contradiction_penalty_ratio",
        "gate_score",
        "gate_status",
        "reason_codes",
        "paper_only",
        "report_only",
        "readonly",
    ),
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
class ResearchPacketDisconfirmingEvidenceGateV2Config:
    config_version: str
    minimum_disconfirming_sources: Decimal
    minimum_opposition_sources: Decimal
    coverage_weight: Decimal
    opposition_source_weight: Decimal
    contradiction_penalty_weight: Decimal
    pass_threshold: Decimal
    review_threshold: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _config_version(self.config_version)
        for name in ("minimum_disconfirming_sources", "minimum_opposition_sources"):
            object.__setattr__(self, name, _count_positive(name, getattr(self, name)))
        for name in (
            "coverage_weight",
            "opposition_source_weight",
            "contradiction_penalty_weight",
            "pass_threshold",
            "review_threshold",
        ):
            object.__setattr__(self, name, _ratio(name, getattr(self, name)))
        if _weight_total(self) != ONE:
            raise ValueError("gate weights must total 1")
        if self.review_threshold > self.pass_threshold:
            raise ValueError("review_threshold must not exceed pass_threshold")
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class ResearchPacketDisconfirmingEvidenceGateV2Packet:
    packet_id: str
    market_question: str
    thesis_summary: str
    disconfirming_source_count: Decimal
    opposition_source_count: Decimal
    supporting_source_count: Decimal
    contradiction_severity: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _safe_text("packet_id", self.packet_id)
        _safe_text("market_question", self.market_question)
        _safe_text("thesis_summary", self.thesis_summary)
        for name in (
            "disconfirming_source_count",
            "opposition_source_count",
            "supporting_source_count",
        ):
            object.__setattr__(self, name, _count(name, getattr(self, name)))
        object.__setattr__(
            self,
            "contradiction_severity",
            _ratio("contradiction_severity", self.contradiction_severity),
        )
        _require_hard_flags("packet", self)


@dataclass(frozen=True)
class ResearchPacketDisconfirmingEvidenceGateV2Row:
    rank: Decimal
    packet_id: str
    market_question: str
    thesis_summary: str
    disconfirming_source_count: Decimal
    opposition_source_count: Decimal
    supporting_source_count: Decimal
    disconfirming_coverage_ratio: Decimal
    opposition_coverage_ratio: Decimal
    contradiction_penalty_ratio: Decimal
    gate_score: Decimal
    gate_status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "rank", _count_positive("rank", self.rank))
        _safe_text("packet_id", self.packet_id)
        _safe_text("market_question", self.market_question)
        _safe_text("thesis_summary", self.thesis_summary)
        for name in (
            "disconfirming_source_count",
            "opposition_source_count",
            "supporting_source_count",
        ):
            object.__setattr__(self, name, _count(name, getattr(self, name)))
        for name in (
            "disconfirming_coverage_ratio",
            "opposition_coverage_ratio",
            "contradiction_penalty_ratio",
            "gate_score",
        ):
            object.__setattr__(self, name, _ratio(name, getattr(self, name)))
        _member("gate_status", self.gate_status, GATE_STATUSES)
        object.__setattr__(self, "reason_codes", _reason_codes(self.reason_codes))
        _require_hard_flags("row", self)


@dataclass(frozen=True)
class ResearchPacketDisconfirmingEvidenceGateV2Report:
    generated_at: datetime
    config_version: str
    packet_count: Decimal
    pass_count: Decimal
    review_count: Decimal
    fail_count: Decimal
    average_gate_score: Decimal
    min_gate_score: Decimal
    max_contradiction_penalty_ratio: Decimal
    rows: tuple[ResearchPacketDisconfirmingEvidenceGateV2Row, ...]
    derived_validation_digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _config_version(self.config_version)
        for name in ("packet_count", "pass_count", "review_count", "fail_count"):
            object.__setattr__(self, name, _count(name, getattr(self, name)))
        for name in (
            "average_gate_score",
            "min_gate_score",
            "max_contradiction_penalty_ratio",
        ):
            object.__setattr__(self, name, _ratio(name, getattr(self, name)))
        if (
            type(self.rows) is not tuple
            or not all(
                type(row) is ResearchPacketDisconfirmingEvidenceGateV2Row
                for row in self.rows
            )
        ):
            raise ValueError("rows must contain disconfirming evidence gate rows")
        _hex_digest("derived_validation_digest", self.derived_validation_digest)
        _validate_digest(self)
        _report_matches(self)
        _require_hard_flags("report", self)

    @property
    def payload(self) -> dict[str, Any]:
        return research_packet_disconfirming_evidence_gate_v2_payload(self)


def build_research_packet_disconfirming_evidence_gate_v2(
    packets: Iterable[ResearchPacketDisconfirmingEvidenceGateV2Packet],
    *,
    config: ResearchPacketDisconfirmingEvidenceGateV2Config,
    generated_at: datetime,
) -> ResearchPacketDisconfirmingEvidenceGateV2Report:
    if type(config) is not ResearchPacketDisconfirmingEvidenceGateV2Config:
        raise ValueError("config must be a disconfirming evidence gate config")
    _require_hard_flags("config", config)
    stamp = _as_utc("generated_at", generated_at)
    source_packets = tuple(packets)
    if not all(
        type(packet) is ResearchPacketDisconfirmingEvidenceGateV2Packet
        for packet in source_packets
    ):
        raise ValueError("packets must contain disconfirming evidence packet values")
    built_rows = _ranked_rows(tuple(_row(packet, config) for packet in source_packets))
    report_values = {
        "generated_at": stamp,
        "config_version": config.config_version,
        "packet_count": Decimal(len(built_rows)),
        "pass_count": Decimal(
            sum(COUNT_ONE for row in built_rows if row.gate_status == "pass"),
        ),
        "review_count": Decimal(
            sum(COUNT_ONE for row in built_rows if row.gate_status == "review"),
        ),
        "fail_count": Decimal(
            sum(COUNT_ONE for row in built_rows if row.gate_status == "fail"),
        ),
        "average_gate_score": _average(tuple(row.gate_score for row in built_rows)),
        "min_gate_score": min((row.gate_score for row in built_rows), default=ZERO),
        "max_contradiction_penalty_ratio": max(
            (row.contradiction_penalty_ratio for row in built_rows),
            default=ZERO,
        ),
        "rows": built_rows,
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    digest = _derive_digest_from_public_payload(_payload(report_values))
    return ResearchPacketDisconfirmingEvidenceGateV2Report(
        **report_values,
        derived_validation_digest=digest,
    )


def research_packet_disconfirming_evidence_gate_v2_payload(
    report: ResearchPacketDisconfirmingEvidenceGateV2Report | dict[str, Any],
) -> dict[str, Any]:
    if type(report) is ResearchPacketDisconfirmingEvidenceGateV2Report:
        _require_hard_flags("report", report)
        payload = _payload(report)
    elif type(report) is dict:
        payload = _json_ready(report)
    else:
        raise ValueError("report must be a disconfirming evidence gate report")
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    _reject_unsafe_public_payload(payload)
    _require_supported_payload(payload)
    _require_hard_flags("payload", _DictFlags(payload))
    _require_payload_digest(payload)
    return payload


def derive_research_packet_disconfirming_evidence_gate_v2_digest(
    report: ResearchPacketDisconfirmingEvidenceGateV2Report | dict[str, Any],
) -> str:
    if type(report) is ResearchPacketDisconfirmingEvidenceGateV2Report:
        payload = _payload(report)
    elif type(report) is dict:
        payload = _json_ready(report)
    else:
        raise ValueError("report must be a disconfirming evidence gate report")
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
    packet: ResearchPacketDisconfirmingEvidenceGateV2Packet,
    config: ResearchPacketDisconfirmingEvidenceGateV2Config,
) -> ResearchPacketDisconfirmingEvidenceGateV2Row:
    disconfirming_coverage_ratio = _clamp_unit(
        _q(packet.disconfirming_source_count / config.minimum_disconfirming_sources),
    )
    opposition_coverage_ratio = _clamp_unit(
        _q(packet.opposition_source_count / config.minimum_opposition_sources),
    )
    contradiction_penalty_ratio = packet.contradiction_severity
    gate_score = _gate_score(
        config,
        disconfirming_coverage_ratio=disconfirming_coverage_ratio,
        opposition_coverage_ratio=opposition_coverage_ratio,
        contradiction_penalty_ratio=contradiction_penalty_ratio,
    )
    gate_status = _gate_status(gate_score, config)
    return ResearchPacketDisconfirmingEvidenceGateV2Row(
        rank=COUNT_ONE,
        packet_id=packet.packet_id,
        market_question=packet.market_question,
        thesis_summary=packet.thesis_summary,
        disconfirming_source_count=packet.disconfirming_source_count,
        opposition_source_count=packet.opposition_source_count,
        supporting_source_count=packet.supporting_source_count,
        disconfirming_coverage_ratio=disconfirming_coverage_ratio,
        opposition_coverage_ratio=opposition_coverage_ratio,
        contradiction_penalty_ratio=contradiction_penalty_ratio,
        gate_score=gate_score,
        gate_status=gate_status,
        reason_codes=_dedupe(
            (
                _disconfirming_reason(disconfirming_coverage_ratio),
                _opposition_reason(opposition_coverage_ratio),
                _contradiction_reason(contradiction_penalty_ratio),
                f"gate_{gate_status}",
            ),
        ),
    )


def _ranked_rows(
    rows: tuple[ResearchPacketDisconfirmingEvidenceGateV2Row, ...],
) -> tuple[ResearchPacketDisconfirmingEvidenceGateV2Row, ...]:
    ranked = []
    for index, row in enumerate(sorted(rows, key=_row_key), start=1):
        ranked.append(
            ResearchPacketDisconfirmingEvidenceGateV2Row(
                rank=Decimal(index),
                packet_id=row.packet_id,
                market_question=row.market_question,
                thesis_summary=row.thesis_summary,
                disconfirming_source_count=row.disconfirming_source_count,
                opposition_source_count=row.opposition_source_count,
                supporting_source_count=row.supporting_source_count,
                disconfirming_coverage_ratio=row.disconfirming_coverage_ratio,
                opposition_coverage_ratio=row.opposition_coverage_ratio,
                contradiction_penalty_ratio=row.contradiction_penalty_ratio,
                gate_score=row.gate_score,
                gate_status=row.gate_status,
                reason_codes=row.reason_codes,
            ),
        )
    return tuple(ranked)


def _row_key(row: ResearchPacketDisconfirmingEvidenceGateV2Row) -> tuple[Decimal, str]:
    return (row.gate_score, row.packet_id)


def _gate_score(
    config: ResearchPacketDisconfirmingEvidenceGateV2Config,
    *,
    disconfirming_coverage_ratio: Decimal,
    opposition_coverage_ratio: Decimal,
    contradiction_penalty_ratio: Decimal,
) -> Decimal:
    return _q(
        disconfirming_coverage_ratio * config.coverage_weight
        + opposition_coverage_ratio * config.opposition_source_weight
        + (ONE - contradiction_penalty_ratio) * config.contradiction_penalty_weight,
    )


def _gate_status(
    gate_score: Decimal,
    config: ResearchPacketDisconfirmingEvidenceGateV2Config,
) -> str:
    if gate_score >= config.pass_threshold:
        return "pass"
    if gate_score >= config.review_threshold:
        return "review"
    return "fail"


def _disconfirming_reason(disconfirming_coverage_ratio: Decimal) -> str:
    if disconfirming_coverage_ratio >= ONE:
        return "disconfirming_coverage_complete"
    if disconfirming_coverage_ratio > ZERO:
        return "disconfirming_coverage_partial"
    return "disconfirming_coverage_missing"


def _opposition_reason(opposition_coverage_ratio: Decimal) -> str:
    if opposition_coverage_ratio >= ONE:
        return "opposition_source_present"
    return "missing_opposition_source"


def _contradiction_reason(contradiction_penalty_ratio: Decimal) -> str:
    if contradiction_penalty_ratio >= Decimal("0.750000"):
        return "contradiction_penalty_high"
    if contradiction_penalty_ratio >= Decimal("0.250000"):
        return "contradiction_penalty_watch"
    return "contradiction_penalty_low"


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
    if type(value) is float:
        raise ValueError("JSON value must not be a float")
    if type(value) is int:
        raise ValueError("JSON numeric value must use Decimal")
    if type(value) in (str, bool):
        return value
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
    public_payload = {key: value for key, value in payload.items() if key != "derived_validation_digest"}
    encoded = json.dumps(
        public_payload,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _validate_digest(report: ResearchPacketDisconfirmingEvidenceGateV2Report) -> None:
    if report.derived_validation_digest != _derive_digest_from_public_payload(_payload(report)):
        raise ValueError("derived_validation_digest must match report fields")


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


def _require_payload_report_values(
    payload: dict[str, Any],
    *,
    digest_required: bool,
) -> None:
    _payload_datetime(payload.get("generated_at"))
    if payload.get("config_version") != DEFAULT_RESEARCH_PACKET_DISCONFIRMING_EVIDENCE_GATE_V2_CONFIG_VERSION:
        raise ValueError("config_version is not supported")
    for name in ("packet_count", "pass_count", "review_count", "fail_count"):
        _payload_count_string(name, payload.get(name))
    for name in (
        "average_gate_score",
        "min_gate_score",
        "max_contradiction_penalty_ratio",
    ):
        _payload_ratio_string(name, payload.get(name))
    if digest_required:
        _hex_digest("derived_validation_digest", payload.get("derived_validation_digest"))


def _require_payload_row_values(row: dict[str, Any]) -> None:
    _payload_count_string("rank", row.get("rank"))
    _safe_text("packet_id", row.get("packet_id"))
    _safe_text("market_question", row.get("market_question"))
    _safe_text("thesis_summary", row.get("thesis_summary"))
    for name in (
        "disconfirming_source_count",
        "opposition_source_count",
        "supporting_source_count",
    ):
        _payload_count_string(name, row.get(name))
    for name in (
        "disconfirming_coverage_ratio",
        "opposition_coverage_ratio",
        "contradiction_penalty_ratio",
        "gate_score",
    ):
        _payload_ratio_string(name, row.get(name))
    _member("gate_status", row.get("gate_status"), GATE_STATUSES)
    reason_codes = row.get("reason_codes")
    if type(reason_codes) is not list:
        raise ValueError("reason_codes must be a list")
    _reason_codes(tuple(reason_codes))


def _report_matches(report: ResearchPacketDisconfirmingEvidenceGateV2Report) -> None:
    if report.packet_count != Decimal(len(report.rows)):
        raise ValueError("packet_count must match rows")
    if report.pass_count != Decimal(sum(COUNT_ONE for row in report.rows if row.gate_status == "pass")):
        raise ValueError("pass_count must match rows")
    if report.review_count != Decimal(sum(COUNT_ONE for row in report.rows if row.gate_status == "review")):
        raise ValueError("review_count must match rows")
    if report.fail_count != Decimal(sum(COUNT_ONE for row in report.rows if row.gate_status == "fail")):
        raise ValueError("fail_count must match rows")
    if report.average_gate_score != _average(tuple(row.gate_score for row in report.rows)):
        raise ValueError("average_gate_score must match rows")
    if report.min_gate_score != min((row.gate_score for row in report.rows), default=ZERO):
        raise ValueError("min_gate_score must match rows")
    if report.max_contradiction_penalty_ratio != max(
        (row.contradiction_penalty_ratio for row in report.rows),
        default=ZERO,
    ):
        raise ValueError("max_contradiction_penalty_ratio must match rows")


def _unsafe_text(value: str) -> bool:
    lowered = value.lower()
    return any(fragment in lowered for fragment in UNSAFE_PUBLIC_FRAGMENTS)


def _reason_codes(values: tuple[str, ...]) -> tuple[str, ...]:
    if type(values) is not tuple:
        raise ValueError("reason_codes must be a tuple")
    normalized = tuple(_checked_reason(value) for value in values)
    if len(set(normalized)) != len(normalized):
        raise ValueError("reason_codes must be unique")
    return normalized


def _checked_reason(value: str) -> str:
    if type(value) is not str or value not in REASON_PRIORITY:
        raise ValueError("reason_codes must be supported")
    if _unsafe_text(value):
        raise ValueError("unsafe public payload value")
    return value


def _dedupe(values: Iterable[str]) -> tuple[str, ...]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        _checked_reason(value)
        if value not in seen:
            seen.add(value)
            result.append(value)
    return tuple(sorted(result, key=lambda item: REASON_PRIORITY[item]))


def _average(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return ZERO
    return _q(sum(values, ZERO) / Decimal(len(values)))


def _weight_total(config: ResearchPacketDisconfirmingEvidenceGateV2Config) -> Decimal:
    return _q(
        config.coverage_weight
        + config.opposition_source_weight
        + config.contradiction_penalty_weight,
    )


def _as_utc(name: str, value: datetime) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{name} must be a datetime")
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


def _safe_text(name: str, value: object) -> None:
    if type(value) is not str or not value:
        raise ValueError(f"{name} must be a non-empty string")
    if value.strip() != value:
        raise ValueError(f"{name} must not have outer whitespace")
    if _unsafe_text(value):
        raise ValueError("unsafe public payload value")


def _payload_datetime(value: object) -> None:
    if type(value) is not str or not value.endswith("Z"):
        raise ValueError("generated_at must be a UTC timestamp string")


def _payload_count_string(name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{name} must be a Decimal string")
    _count(name, Decimal(value))


def _payload_ratio_string(name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{name} must be a Decimal string")
    result = _ratio(name, Decimal(value))
    if str(result) != value:
        raise ValueError(f"{name} must be a canonical Decimal string")


def _config_version(value: str) -> None:
    if type(value) is not str:
        raise ValueError("config_version must be a string")
    if value != DEFAULT_RESEARCH_PACKET_DISCONFIRMING_EVIDENCE_GATE_V2_CONFIG_VERSION:
        raise ValueError("config_version is not supported")


def _hex_digest(name: str, value: object) -> None:
    if type(value) is not str or len(value) != 64:
        raise ValueError(f"{name} must be a sha256 hex digest")
    if any(character not in "0123456789abcdef" for character in value):
        raise ValueError(f"{name} must be a sha256 hex digest")


def _member(name: str, value: object, allowed: frozenset[str]) -> None:
    if type(value) is not str or value not in allowed:
        raise ValueError(f"{name} is not supported")


def _dec(name: str, value: Decimal) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{name} must be finite")
    return _q(value)


def _count(name: str, value: Decimal) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{name} must be finite")
    if value < COUNT_ZERO or value != value.to_integral_value():
        raise ValueError(f"{name} must be a nonnegative whole Decimal")
    return value.quantize(COUNT_Q)


def _count_positive(name: str, value: Decimal) -> Decimal:
    result = _count(name, value)
    if result <= COUNT_ZERO:
        raise ValueError(f"{name} must be positive")
    return result


def _ratio(name: str, value: Decimal) -> Decimal:
    result = _dec(name, value)
    if result < ZERO or result > ONE:
        raise ValueError(f"{name} must be between 0 and 1")
    return result


def _require_hard_flags(name: str, value: object) -> None:
    if getattr(value, "paper_only", None) is not True:
        raise ValueError(f"{name} must be paper_only")
    if getattr(value, "report_only", None) is not True:
        raise ValueError(f"{name} must be report_only")
    if getattr(value, "readonly", None) is not True:
        raise ValueError(f"{name} must be readonly")


def _q(value: Decimal) -> Decimal:
    with localcontext() as ctx:
        ctx.prec = 64
        ctx.rounding = ROUND_HALF_EVEN
        return value.quantize(Q)


def _clamp_unit(value: Decimal) -> Decimal:
    if value < ZERO:
        return ZERO
    if value > ONE:
        return ONE
    return value


__all__ = (
    "DEFAULT_RESEARCH_PACKET_DISCONFIRMING_EVIDENCE_GATE_V2_CONFIG_VERSION",
    "ResearchPacketDisconfirmingEvidenceGateV2Config",
    "ResearchPacketDisconfirmingEvidenceGateV2Packet",
    "ResearchPacketDisconfirmingEvidenceGateV2Report",
    "ResearchPacketDisconfirmingEvidenceGateV2Row",
    "build_research_packet_disconfirming_evidence_gate_v2",
    "derive_research_packet_disconfirming_evidence_gate_v2_digest",
    "research_packet_disconfirming_evidence_gate_v2_payload",
)
