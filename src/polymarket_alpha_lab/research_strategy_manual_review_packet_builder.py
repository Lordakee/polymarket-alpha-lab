"""Deterministic paper-only manual review packets for research strategy signals."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
import hashlib
import json
from typing import Any


DEFAULT_RESEARCH_STRATEGY_MANUAL_REVIEW_PACKET_CONFIG_VERSION = (
    "research-strategy-manual-review-packet-builder-v1"
)

DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
QUANTUM = Decimal("0.000001")
COUNT_QUANTUM = Decimal("1")
ZERO = Decimal("0.000000")
ZERO_COUNT = Decimal("0")
ONE = Decimal("1.000000")

MANUAL_REVIEW_PACKET_PUBLIC_STATUSES = ("pass", "watch", "block")

MANUAL_REVIEW_PACKET_PASS_REASON = "manual_review_packet_pass"
EMPTY_MANUAL_REVIEW_PACKET_REASON = "empty_manual_review_packet"

RESEARCH_STRATEGY_MANUAL_REVIEW_PACKET_REASON_CODES = (
    MANUAL_REVIEW_PACKET_PASS_REASON,
    EMPTY_MANUAL_REVIEW_PACKET_REASON,
    "signal_strength_below_floor",
    "signal_confidence_below_floor",
    "evidence_gap_watch",
    "evidence_gap_block",
    "cost_surface_watch",
    "cost_surface_block",
    "calibration_drift_watch",
    "calibration_drift_block",
    "team_capacity_watch",
    "team_capacity_block",
    "team_disagreement_watch",
    "team_disagreement_block",
    "hard_review_flag",
)

BLOCK_REASON_CODES = frozenset(
    (
        EMPTY_MANUAL_REVIEW_PACKET_REASON,
        "evidence_gap_block",
        "cost_surface_block",
        "calibration_drift_block",
        "team_capacity_block",
        "team_disagreement_block",
        "hard_review_flag",
    ),
)

UNSAFE_PUBLIC_FRAGMENTS = (
    "raw_candidate_id",
    "raw-candidate-id",
    "raw_candidate",
    "raw-candidate",
    "candidate_id",
    "candidate-id",
    "market_id",
    "market-id",
    "market_slug",
    "market-slug",
    "question",
    "source_ref",
    "source-ref",
    "source_url",
    "source-url",
    "source_text",
    "source-text",
    "dsn",
    "table",
    "token",
    "wallet",
    "order",
    "trade",
    "position",
    "buy",
    "sell",
    "recommend",
    "auth",
    "live",
)


@dataclass(frozen=True)
class ResearchStrategyManualReviewPacketConfig:
    config_version: str = DEFAULT_RESEARCH_STRATEGY_MANUAL_REVIEW_PACKET_CONFIG_VERSION
    signal_strength_floor: Decimal = Decimal("0.500000")
    signal_confidence_floor: Decimal = Decimal("0.600000")
    evidence_gap_watch_threshold: Decimal = Decimal("0.250000")
    evidence_gap_block_threshold: Decimal = Decimal("0.700000")
    cost_surface_watch_threshold: Decimal = Decimal("0.250000")
    cost_surface_block_threshold: Decimal = Decimal("0.700000")
    calibration_drift_watch_threshold: Decimal = Decimal("0.200000")
    calibration_drift_block_threshold: Decimal = Decimal("0.700000")
    team_capacity_watch_floor: Decimal = Decimal("0.500000")
    team_capacity_block_floor: Decimal = Decimal("0.300000")
    team_disagreement_watch_threshold: Decimal = Decimal("0.250000")
    team_disagreement_block_threshold: Decimal = Decimal("0.700000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type("config", self, ResearchStrategyManualReviewPacketConfig)
        _require_public_string("config_version", self.config_version)
        for field_name in (
            "signal_strength_floor",
            "signal_confidence_floor",
            "evidence_gap_watch_threshold",
            "evidence_gap_block_threshold",
            "cost_surface_watch_threshold",
            "cost_surface_block_threshold",
            "calibration_drift_watch_threshold",
            "calibration_drift_block_threshold",
            "team_capacity_watch_floor",
            "team_capacity_block_floor",
            "team_disagreement_watch_threshold",
            "team_disagreement_block_threshold",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        _require_watch_below_block(
            "evidence_gap_watch_threshold",
            self.evidence_gap_watch_threshold,
            "evidence_gap_block_threshold",
            self.evidence_gap_block_threshold,
        )
        _require_watch_below_block(
            "cost_surface_watch_threshold",
            self.cost_surface_watch_threshold,
            "cost_surface_block_threshold",
            self.cost_surface_block_threshold,
        )
        _require_watch_below_block(
            "calibration_drift_watch_threshold",
            self.calibration_drift_watch_threshold,
            "calibration_drift_block_threshold",
            self.calibration_drift_block_threshold,
        )
        _require_watch_below_block(
            "team_disagreement_watch_threshold",
            self.team_disagreement_watch_threshold,
            "team_disagreement_block_threshold",
            self.team_disagreement_block_threshold,
        )
        if self.team_capacity_block_floor >= self.team_capacity_watch_floor:
            raise ValueError("team_capacity_block_floor must be below team_capacity_watch_floor")
        _require_hard_flags("config", self)
        _reject_unsafe_public_payload("config", _payload_value(self))


@dataclass(frozen=True)
class ResearchStrategyManualReviewPacketInput:
    packet_key: str
    signal_strength: Decimal
    signal_confidence: Decimal
    evidence_gap_score: Decimal
    cost_surface_score: Decimal
    calibration_drift_score: Decimal
    team_capacity_score: Decimal
    team_disagreement_score: Decimal
    hard_flag_count: Decimal
    assigned_team: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type("packet", self, ResearchStrategyManualReviewPacketInput)
        _require_public_string("packet_key", self.packet_key)
        _require_public_string("assigned_team", self.assigned_team)
        for field_name in (
            "signal_strength",
            "signal_confidence",
            "evidence_gap_score",
            "cost_surface_score",
            "calibration_drift_score",
            "team_capacity_score",
            "team_disagreement_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "hard_flag_count",
            _normalize_whole_decimal("hard_flag_count", self.hard_flag_count),
        )
        _require_hard_flags("packet", self)
        _reject_unsafe_public_payload("packet", _payload_value(self))


@dataclass(frozen=True)
class ResearchStrategyManualReviewPacketRow:
    packet_key: str
    signal_strength: Decimal
    signal_confidence: Decimal
    evidence_gap_score: Decimal
    cost_surface_score: Decimal
    calibration_drift_score: Decimal
    team_capacity_score: Decimal
    team_disagreement_score: Decimal
    hard_flag_count: Decimal
    assigned_team: str
    public_status: str
    review_focus: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type("row", self, ResearchStrategyManualReviewPacketRow)
        _require_public_string("packet_key", self.packet_key)
        _require_public_string("assigned_team", self.assigned_team)
        for field_name in (
            "signal_strength",
            "signal_confidence",
            "evidence_gap_score",
            "cost_surface_score",
            "calibration_drift_score",
            "team_capacity_score",
            "team_disagreement_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "hard_flag_count",
            _normalize_whole_decimal("hard_flag_count", self.hard_flag_count),
        )
        _require_public_status("public_status", self.public_status)
        _require_public_string("review_focus", self.review_focus)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        if self.public_status != _status_from_reason_codes(self.reason_codes):
            raise ValueError("public_status must match reason_codes")
        if self.review_focus != _review_focus(self.public_status):
            raise ValueError("review_focus must match public_status")
        _require_hard_flags("row", self)
        _reject_unsafe_public_payload("row", _payload_value(self))


@dataclass(frozen=True)
class ResearchStrategyManualReviewPacketReport:
    generated_at: datetime
    config_version: str
    packet_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    highest_signal_strength: Decimal
    highest_evidence_gap_score: Decimal
    highest_cost_surface_score: Decimal
    highest_calibration_drift_score: Decimal
    lowest_team_capacity_score: Decimal
    highest_team_disagreement_score: Decimal
    hard_flag_count: Decimal
    public_status: str
    review_focus: str
    reason_codes: tuple[str, ...]
    review_rows: tuple[ResearchStrategyManualReviewPacketRow, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type("report", self, ResearchStrategyManualReviewPacketReport)
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_string("config_version", self.config_version)
        for field_name in (
            "packet_count",
            "pass_count",
            "watch_count",
            "block_count",
            "hard_flag_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_whole_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "highest_signal_strength",
            "highest_evidence_gap_score",
            "highest_cost_surface_score",
            "highest_calibration_drift_score",
            "lowest_team_capacity_score",
            "highest_team_disagreement_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        _require_public_status("public_status", self.public_status)
        _require_public_string("review_focus", self.review_focus)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        object.__setattr__(self, "review_rows", _normalize_rows(self.review_rows))
        _require_hard_flags("report", self)
        _validate_report(self)
        _reject_unsafe_public_payload("report", _payload_value(self))
        _set_or_validate_derived_validation_digest(self)

    @property
    def payload(self) -> dict[str, Any]:
        return research_strategy_manual_review_packet_public_payload(self)


def build_research_strategy_manual_review_packet(
    packets: Iterable[ResearchStrategyManualReviewPacketInput],
    *,
    generated_at: datetime,
    config: ResearchStrategyManualReviewPacketConfig | None = None,
) -> ResearchStrategyManualReviewPacketReport:
    active_config = config or ResearchStrategyManualReviewPacketConfig()
    if type(active_config) is not ResearchStrategyManualReviewPacketConfig:
        raise ValueError("config must be a ResearchStrategyManualReviewPacketConfig")
    _require_hard_flags("config", active_config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    normalized_packets = _normalize_packets(packets)
    rows = tuple(
        sorted(
            (_row_for_packet(packet, active_config) for packet in normalized_packets),
            key=_row_sort_key,
        ),
    )
    reason_codes = _report_reason_codes(rows)
    public_status = _status_from_reason_codes(reason_codes)
    return ResearchStrategyManualReviewPacketReport(
        generated_at=generated_at_utc,
        config_version=active_config.config_version,
        packet_count=_count(len(rows)),
        pass_count=_count(sum(1 for row in rows if row.public_status == "pass")),
        watch_count=_count(sum(1 for row in rows if row.public_status == "watch")),
        block_count=_count(sum(1 for row in rows if row.public_status == "block")),
        highest_signal_strength=_max_ratio(row.signal_strength for row in rows),
        highest_evidence_gap_score=_max_ratio(row.evidence_gap_score for row in rows),
        highest_cost_surface_score=_max_ratio(row.cost_surface_score for row in rows),
        highest_calibration_drift_score=_max_ratio(
            row.calibration_drift_score for row in rows
        ),
        lowest_team_capacity_score=_min_ratio(row.team_capacity_score for row in rows),
        highest_team_disagreement_score=_max_ratio(
            row.team_disagreement_score for row in rows
        ),
        hard_flag_count=_sum_counts(row.hard_flag_count for row in rows),
        public_status=public_status,
        review_focus=_review_focus(public_status),
        reason_codes=reason_codes,
        review_rows=rows,
    )


def research_strategy_manual_review_packet_public_payload(
    value: ResearchStrategyManualReviewPacketReport | dict[str, Any],
) -> dict[str, Any]:
    if type(value) is ResearchStrategyManualReviewPacketReport:
        _validate_report(value)
        _validate_derived_validation_digest(value)
        payload = _payload_value(value)
    elif type(value) is dict:
        payload = value
    else:
        raise ValueError(
            "value must be a ResearchStrategyManualReviewPacketReport or dict",
        )
    if type(payload) is not dict:
        raise ValueError("public payload must be a dict")
    validate_research_strategy_manual_review_packet_public_payload(payload)
    return dict(payload)


def validate_research_strategy_manual_review_packet_public_payload(
    payload: dict[str, Any],
) -> bool:
    if type(payload) is not dict:
        raise ValueError("payload must be a dict")
    _reject_unsafe_public_payload("public payload", payload)
    _require_public_payload_flags(payload)
    _require_payload_status(payload, "public_status")
    _require_payload_rows(payload)
    digest_value = _payload_required_string(payload, "derived_validation_digest")
    _require_sha256_digest("derived_validation_digest", digest_value)
    if digest_value != _derived_validation_digest(payload):
        raise ValueError("derived_validation_digest must match public payload")
    return True


def research_strategy_manual_review_packet_digest(
    value: ResearchStrategyManualReviewPacketReport | dict[str, Any],
) -> str:
    if type(value) is ResearchStrategyManualReviewPacketReport:
        _validate_derived_validation_digest(value)
        return value.derived_validation_digest
    if type(value) is dict:
        validate_research_strategy_manual_review_packet_public_payload(value)
        return _payload_required_string(value, "derived_validation_digest")
    raise ValueError("value must be a ResearchStrategyManualReviewPacketReport or dict")


def _row_for_packet(
    packet: ResearchStrategyManualReviewPacketInput,
    config: ResearchStrategyManualReviewPacketConfig,
) -> ResearchStrategyManualReviewPacketRow:
    reason_codes = _row_reason_codes(packet, config)
    public_status = _status_from_reason_codes(reason_codes)
    return ResearchStrategyManualReviewPacketRow(
        packet_key=packet.packet_key,
        signal_strength=packet.signal_strength,
        signal_confidence=packet.signal_confidence,
        evidence_gap_score=packet.evidence_gap_score,
        cost_surface_score=packet.cost_surface_score,
        calibration_drift_score=packet.calibration_drift_score,
        team_capacity_score=packet.team_capacity_score,
        team_disagreement_score=packet.team_disagreement_score,
        hard_flag_count=packet.hard_flag_count,
        assigned_team=packet.assigned_team,
        public_status=public_status,
        review_focus=_review_focus(public_status),
        reason_codes=reason_codes,
    )


def _row_reason_codes(
    packet: ResearchStrategyManualReviewPacketInput,
    config: ResearchStrategyManualReviewPacketConfig,
) -> tuple[str, ...]:
    codes: list[str] = []
    if packet.signal_strength < config.signal_strength_floor:
        codes.append("signal_strength_below_floor")
    if packet.signal_confidence < config.signal_confidence_floor:
        codes.append("signal_confidence_below_floor")
    _append_threshold_reason(
        codes,
        "evidence_gap",
        packet.evidence_gap_score,
        config.evidence_gap_watch_threshold,
        config.evidence_gap_block_threshold,
    )
    _append_threshold_reason(
        codes,
        "cost_surface",
        packet.cost_surface_score,
        config.cost_surface_watch_threshold,
        config.cost_surface_block_threshold,
    )
    _append_threshold_reason(
        codes,
        "calibration_drift",
        packet.calibration_drift_score,
        config.calibration_drift_watch_threshold,
        config.calibration_drift_block_threshold,
    )
    _append_floor_reason(
        codes,
        packet.team_capacity_score,
        config.team_capacity_watch_floor,
        config.team_capacity_block_floor,
    )
    _append_threshold_reason(
        codes,
        "team_disagreement",
        packet.team_disagreement_score,
        config.team_disagreement_watch_threshold,
        config.team_disagreement_block_threshold,
    )
    if packet.hard_flag_count > ZERO_COUNT:
        codes.append("hard_review_flag")
    if not codes:
        return (MANUAL_REVIEW_PACKET_PASS_REASON,)
    return _normalize_reason_codes("reason_codes", tuple(codes))


def _append_threshold_reason(
    codes: list[str],
    prefix: str,
    value: Decimal,
    watch_threshold: Decimal,
    block_threshold: Decimal,
) -> None:
    if value >= block_threshold:
        codes.append(f"{prefix}_block")
    elif value >= watch_threshold:
        codes.append(f"{prefix}_watch")


def _append_floor_reason(
    codes: list[str],
    value: Decimal,
    watch_floor: Decimal,
    block_floor: Decimal,
) -> None:
    if value <= block_floor:
        codes.append("team_capacity_block")
    elif value < watch_floor:
        codes.append("team_capacity_watch")


def _report_reason_codes(
    rows: tuple[ResearchStrategyManualReviewPacketRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return (EMPTY_MANUAL_REVIEW_PACKET_REASON,)
    active_codes = tuple(
        code
        for row in rows
        for code in row.reason_codes
        if code != MANUAL_REVIEW_PACKET_PASS_REASON
    )
    if not active_codes:
        return (MANUAL_REVIEW_PACKET_PASS_REASON,)
    return _normalize_reason_codes("reason_codes", active_codes)


def _normalize_packets(
    value: Iterable[ResearchStrategyManualReviewPacketInput],
) -> tuple[ResearchStrategyManualReviewPacketInput, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError("packets must be an iterable")
    try:
        packets = tuple(value)
    except TypeError as exc:
        raise ValueError("packets must be an iterable") from exc
    seen_keys: set[str] = set()
    for packet in packets:
        if type(packet) is not ResearchStrategyManualReviewPacketInput:
            raise ValueError(
                "packets must contain ResearchStrategyManualReviewPacketInput values",
            )
        _require_hard_flags("packet", packet)
        if packet.packet_key in seen_keys:
            raise ValueError("packet_key values must be unique")
        seen_keys.add(packet.packet_key)
    return tuple(sorted(packets, key=_packet_sort_key))


def _normalize_rows(
    value: object,
) -> tuple[ResearchStrategyManualReviewPacketRow, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("review_rows must be a list or tuple")
    rows = tuple(value)
    seen_keys: set[str] = set()
    for row in rows:
        if type(row) is not ResearchStrategyManualReviewPacketRow:
            raise ValueError(
                "review_rows must contain ResearchStrategyManualReviewPacketRow values",
            )
        _require_hard_flags("row", row)
        if row.packet_key in seen_keys:
            raise ValueError("review_rows packet_key values must be unique")
        seen_keys.add(row.packet_key)
    if tuple(sorted(rows, key=_row_sort_key)) != rows:
        raise ValueError("review_rows must be sorted deterministically")
    return rows


def _validate_report(report: ResearchStrategyManualReviewPacketReport) -> None:
    rows = report.review_rows
    if report.packet_count != _count(len(rows)):
        raise ValueError("packet_count must match review_rows")
    if report.pass_count != _count(sum(1 for row in rows if row.public_status == "pass")):
        raise ValueError("pass_count must match review_rows")
    if report.watch_count != _count(sum(1 for row in rows if row.public_status == "watch")):
        raise ValueError("watch_count must match review_rows")
    if report.block_count != _count(sum(1 for row in rows if row.public_status == "block")):
        raise ValueError("block_count must match review_rows")
    if report.highest_signal_strength != _max_ratio(row.signal_strength for row in rows):
        raise ValueError("highest_signal_strength must match review_rows")
    if report.highest_evidence_gap_score != _max_ratio(
        row.evidence_gap_score for row in rows
    ):
        raise ValueError("highest_evidence_gap_score must match review_rows")
    if report.highest_cost_surface_score != _max_ratio(
        row.cost_surface_score for row in rows
    ):
        raise ValueError("highest_cost_surface_score must match review_rows")
    if report.highest_calibration_drift_score != _max_ratio(
        row.calibration_drift_score for row in rows
    ):
        raise ValueError("highest_calibration_drift_score must match review_rows")
    if report.lowest_team_capacity_score != _min_ratio(
        row.team_capacity_score for row in rows
    ):
        raise ValueError("lowest_team_capacity_score must match review_rows")
    if report.highest_team_disagreement_score != _max_ratio(
        row.team_disagreement_score for row in rows
    ):
        raise ValueError("highest_team_disagreement_score must match review_rows")
    if report.hard_flag_count != _sum_counts(row.hard_flag_count for row in rows):
        raise ValueError("hard_flag_count must match review_rows")
    expected_reason_codes = _report_reason_codes(rows)
    if report.reason_codes != expected_reason_codes:
        raise ValueError("reason_codes must match review_rows")
    if report.public_status != _status_from_reason_codes(report.reason_codes):
        raise ValueError("public_status must match reason_codes")
    if report.review_focus != _review_focus(report.public_status):
        raise ValueError("review_focus must match public_status")


def _set_or_validate_derived_validation_digest(
    report: ResearchStrategyManualReviewPacketReport,
) -> None:
    current = report.derived_validation_digest
    expected = _derived_validation_digest(report)
    if current == "":
        object.__setattr__(report, "derived_validation_digest", expected)
        return
    _require_sha256_digest("derived_validation_digest", current)
    if current != expected:
        raise ValueError("derived_validation_digest must match report fields")


def _validate_derived_validation_digest(
    report: ResearchStrategyManualReviewPacketReport,
) -> None:
    current = _require_sha256_digest(
        "derived_validation_digest",
        report.derived_validation_digest,
    )
    if current != _derived_validation_digest(report):
        raise ValueError("derived_validation_digest must match report fields")


def _derived_validation_digest(value: object) -> str:
    payload = _without_derived_validation_digest(_payload_value(value))
    encoded = json.dumps(
        payload,
        allow_nan=False,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _without_derived_validation_digest(value: object) -> object:
    if type(value) is dict:
        return {
            key: _without_derived_validation_digest(item)
            for key, item in value.items()
            if key != "derived_validation_digest"
        }
    if type(value) is list:
        return [_without_derived_validation_digest(item) for item in value]
    return value


def _payload_value(value: object) -> Any:
    if type(value) is Decimal:
        if not value.is_finite():
            raise ValueError("Decimal payload values must be finite")
        return format(value, "f")
    if type(value) is datetime:
        return _as_utc("datetime", value).isoformat()
    if is_dataclass(value) and not isinstance(value, type):
        return {
            field.name: _payload_value(getattr(value, field.name))
            for field in fields(value)
        }
    if type(value) is tuple or type(value) is list:
        return [_payload_value(item) for item in value]
    if type(value) is dict:
        return {key: _payload_value(item) for key, item in value.items()}
    return value


def _reject_unsafe_public_payload(label: str, value: object, path: str = "") -> None:
    if value is None or type(value) is bool:
        return
    if type(value) is str:
        if _has_unsafe_public_fragment(value):
            raise ValueError(f"unsafe public payload value in {path or label}")
        return
    if isinstance(value, (Decimal, int, float)):
        raise ValueError(f"{path or label} must use Decimal strings, not numeric values")
    if type(value) is dict:
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("public payload keys must be strings")
            if _has_unsafe_public_fragment(key):
                raise ValueError(f"unsafe public payload key in {label}: {key}")
            item_path = key if not path else f"{path}.{key}"
            if key in ("paper_only", "report_only", "readonly") and item is not True:
                raise ValueError(f"{item_path} must be True")
            _reject_unsafe_public_payload(label, item, item_path)
        return
    if type(value) is list:
        for index, item in enumerate(value):
            item_path = f"{path}[{index}]" if path else f"{label}[{index}]"
            _reject_unsafe_public_payload(label, item, item_path)
        return
    raise ValueError(f"{path or label} is not public JSON serializable")


def _require_public_payload_flags(payload: dict[str, Any]) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if payload.get(field_name) is not True:
            raise ValueError(f"{field_name} must be True")


def _require_payload_status(payload: dict[str, Any], field_name: str) -> None:
    value = payload.get(field_name)
    _require_public_status(field_name, value)


def _require_payload_rows(payload: dict[str, Any]) -> None:
    rows = payload.get("review_rows")
    if type(rows) is not list:
        raise ValueError("review_rows must be a list")
    for row in rows:
        if type(row) is not dict:
            raise ValueError("review_rows must contain JSON objects")
        _require_payload_status(row, "public_status")
        _require_public_payload_flags(row)


def _payload_required_string(payload: dict[str, Any], field_name: str) -> str:
    value = payload.get(field_name)
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    return value


def _require_sha256_digest(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if len(value) != 64 or any(character not in "0123456789abcdef" for character in value):
        raise ValueError(f"{field_name} must be a lowercase sha256 digest")
    return value


def _normalize_ratio(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    quantized = _quantize(normalized)
    if quantized < ZERO or quantized > ONE:
        raise ValueError(f"{field_name} must be between 0.000000 and 1.000000")
    return quantized


def _normalize_whole_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    quantized = decimal_value.quantize(COUNT_QUANTUM)
    if decimal_value != quantized:
        raise ValueError(f"{field_name} must be a whole Decimal")
    if quantized < ZERO_COUNT:
        raise ValueError(f"{field_name} must be nonnegative")
    return quantized


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return value


def _quantize(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(QUANTUM)


def _normalize_reason_codes(field_name: str, value: Iterable[str]) -> tuple[str, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError(f"{field_name} must be an iterable of reason codes")
    try:
        codes = tuple(value)
    except TypeError as exc:
        raise ValueError(f"{field_name} must be an iterable of reason codes") from exc
    if not codes:
        raise ValueError(f"{field_name} must not be empty")
    for code in codes:
        if type(code) is not str or code not in RESEARCH_STRATEGY_MANUAL_REVIEW_PACKET_REASON_CODES:
            raise ValueError(f"{field_name} contains an unknown reason code")
    active_codes = [code for code in codes if code != MANUAL_REVIEW_PACKET_PASS_REASON]
    if MANUAL_REVIEW_PACKET_PASS_REASON in codes and active_codes:
        raise ValueError(f"{field_name} pass reason must stand alone")
    if EMPTY_MANUAL_REVIEW_PACKET_REASON in codes and len(codes) != 1:
        raise ValueError(f"{field_name} empty reason must stand alone")
    return tuple(
        code
        for code in RESEARCH_STRATEGY_MANUAL_REVIEW_PACKET_REASON_CODES
        if code in set(codes)
    )


def _status_from_reason_codes(reason_codes: tuple[str, ...]) -> str:
    if reason_codes == (MANUAL_REVIEW_PACKET_PASS_REASON,):
        return "pass"
    if any(code in BLOCK_REASON_CODES for code in reason_codes):
        return "block"
    return "watch"


def _review_focus(public_status: str) -> str:
    if public_status == "pass":
        return "ready_for_human_review"
    if public_status == "watch":
        return "refresh_manual_review_inputs"
    return "repair_before_manual_review"


def _count(value: int) -> Decimal:
    return Decimal(value).quantize(COUNT_QUANTUM)


def _sum_counts(values: Iterable[Decimal]) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        total = sum(values, ZERO_COUNT)
    return total.quantize(COUNT_QUANTUM)


def _max_ratio(values: Iterable[Decimal]) -> Decimal:
    return max(tuple(values), default=ZERO).quantize(QUANTUM)


def _min_ratio(values: Iterable[Decimal]) -> Decimal:
    return min(tuple(values), default=ZERO).quantize(QUANTUM)


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


def _require_public_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in MANUAL_REVIEW_PACKET_PUBLIC_STATUSES:
        raise ValueError(
            f"{field_name} must be one of {MANUAL_REVIEW_PACKET_PUBLIC_STATUSES}",
        )


def _require_public_string(field_name: str, value: object) -> None:
    if type(value) is not str or not value:
        raise ValueError(f"{field_name} must be a non-empty string")
    if value != value.strip() or "\n" in value or "\r" in value or "\t" in value:
        raise ValueError(f"{field_name} must be a canonical string")
    if _has_unsafe_public_fragment(value):
        raise ValueError(f"{field_name} has unsafe public content")


def _has_unsafe_public_fragment(value: str) -> bool:
    normalized = value.lower()
    return any(fragment in normalized for fragment in UNSAFE_PUBLIC_FRAGMENTS)


def _require_exact_type(field_name: str, value: object, expected_type: type[object]) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{field_name} must be exactly {expected_type.__name__}")


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if getattr(value, field_name, None) is not True:
            raise ValueError(f"{label} {field_name} must be True")


def _require_watch_below_block(
    watch_name: str,
    watch_value: Decimal,
    block_name: str,
    block_value: Decimal,
) -> None:
    if watch_value >= block_value:
        raise ValueError(f"{watch_name} must be below {block_name}")


def _packet_sort_key(
    packet: ResearchStrategyManualReviewPacketInput,
) -> tuple[str, str]:
    return (packet.packet_key, packet.assigned_team)


def _row_sort_key(
    row: ResearchStrategyManualReviewPacketRow,
) -> tuple[str, str]:
    return (row.packet_key, row.assigned_team)


__all__ = (
    "DEFAULT_RESEARCH_STRATEGY_MANUAL_REVIEW_PACKET_CONFIG_VERSION",
    "MANUAL_REVIEW_PACKET_PUBLIC_STATUSES",
    "RESEARCH_STRATEGY_MANUAL_REVIEW_PACKET_REASON_CODES",
    "ResearchStrategyManualReviewPacketConfig",
    "ResearchStrategyManualReviewPacketInput",
    "ResearchStrategyManualReviewPacketReport",
    "ResearchStrategyManualReviewPacketRow",
    "build_research_strategy_manual_review_packet",
    "research_strategy_manual_review_packet_digest",
    "research_strategy_manual_review_packet_public_payload",
    "validate_research_strategy_manual_review_packet_public_payload",
)
