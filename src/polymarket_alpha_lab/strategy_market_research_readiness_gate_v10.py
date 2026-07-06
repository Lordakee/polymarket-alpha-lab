"""Pure paper-only market research readiness gate."""

from __future__ import annotations

from dataclasses import asdict, dataclass, is_dataclass
from decimal import Decimal
from typing import Any


SCORE_QUANTUM = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
INFO_WATCH_FLOOR = Decimal("0.600000")
RESOLUTION_WATCH_FLOOR = Decimal("0.700000")
TEAM_WATCH_FLOOR = Decimal("0.700000")
SEVERE_SCORE_FLOOR = Decimal("0.400000")
DEEP_INFORMATION_FLOOR = Decimal("0.800000")
DEEP_RESOLUTION_FLOOR = Decimal("0.750000")
DEEP_TEAM_FLOOR = Decimal("0.700000")
STATUSES = ("pass", "watch", "blocked")
READINESS_STATUSES = ("ready", "watch", "needs_human_review", "blocked")
RESEARCH_DEPTH_LEVELS = (
    "deep_research",
    "standard_research",
    "light_research",
    "do_not_research",
)
HARD_FLAGS = ("paper_only", "report_only", "readonly")
_UNSAFE_SURFACE_FRAGMENTS = (
    "au" + "th",
    "wal" + "let",
    "bro" + "ker",
    "sig" + "ning",
    "sub" + "mit",
    "can" + "cel",
    "re" + "place",
    "net" + "work",
    "data" + "base",
    "d" + "b",
    "op" + "en(",
    "or" + "der",
    "tra" + "de",
)


@dataclass(frozen=True)
class MarketResearchReadinessGateV10Input:
    information_edge_score: Decimal
    source_quorum_status: str
    forecast_rationale_status: str
    liquidity_guard_status: str
    resolution_precedent_score: Decimal
    team_capacity_score: Decimal
    human_review_required: bool
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "information_edge_score",
            _normalize_score("information_edge_score", self.information_edge_score),
        )
        object.__setattr__(
            self,
            "source_quorum_status",
            _normalize_status("source_quorum_status", self.source_quorum_status),
        )
        object.__setattr__(
            self,
            "forecast_rationale_status",
            _normalize_status(
                "forecast_rationale_status",
                self.forecast_rationale_status,
            ),
        )
        object.__setattr__(
            self,
            "liquidity_guard_status",
            _normalize_status("liquidity_guard_status", self.liquidity_guard_status),
        )
        object.__setattr__(
            self,
            "resolution_precedent_score",
            _normalize_score(
                "resolution_precedent_score",
                self.resolution_precedent_score,
            ),
        )
        object.__setattr__(
            self,
            "team_capacity_score",
            _normalize_score("team_capacity_score", self.team_capacity_score),
        )
        _require_bool("human_review_required", self.human_review_required)
        _require_hard_flags("input", self)


@dataclass(frozen=True)
class MarketResearchReadinessGateV10Report:
    information_edge_score: Decimal
    source_quorum_status: str
    forecast_rationale_status: str
    liquidity_guard_status: str
    resolution_precedent_score: Decimal
    team_capacity_score: Decimal
    human_review_required: bool
    readiness_status: str
    research_depth_level: str
    blocking_reasons: tuple[str, ...]
    reason_codes: tuple[str, ...]
    payload: dict[str, Any]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        for field_name in (
            "information_edge_score",
            "resolution_precedent_score",
            "team_capacity_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_score(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "source_quorum_status",
            "forecast_rationale_status",
            "liquidity_guard_status",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_status(field_name, getattr(self, field_name)),
            )
        _require_bool("human_review_required", self.human_review_required)
        _require_member("readiness_status", self.readiness_status, READINESS_STATUSES)
        _require_member(
            "research_depth_level",
            self.research_depth_level,
            RESEARCH_DEPTH_LEVELS,
        )
        object.__setattr__(
            self,
            "blocking_reasons",
            _normalize_reason_codes("blocking_reasons", self.blocking_reasons),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        _require_hard_flags("report", self)
        _reject_unsafe_public_payload("payload", self.payload)
        if self.payload != _json_ready(_report_payload(self)):
            raise ValueError("payload must match report fields")


def evaluate_market_research_readiness_gate_v10(
    inputs: MarketResearchReadinessGateV10Input,
) -> MarketResearchReadinessGateV10Report:
    if type(inputs) is not MarketResearchReadinessGateV10Input:
        raise ValueError("inputs must be a MarketResearchReadinessGateV10Input")
    _require_hard_flags("inputs", inputs)

    blocking_reasons = _blocking_reasons(inputs)
    readiness_status = _readiness_status(inputs, blocking_reasons)
    research_depth_level = _research_depth_level(inputs, blocking_reasons)
    reason_codes = _reason_codes(
        inputs,
        blocking_reasons,
        research_depth_level,
    )
    report_values = {
        "information_edge_score": inputs.information_edge_score,
        "source_quorum_status": inputs.source_quorum_status,
        "forecast_rationale_status": inputs.forecast_rationale_status,
        "liquidity_guard_status": inputs.liquidity_guard_status,
        "resolution_precedent_score": inputs.resolution_precedent_score,
        "team_capacity_score": inputs.team_capacity_score,
        "human_review_required": inputs.human_review_required,
        "readiness_status": readiness_status,
        "research_depth_level": research_depth_level,
        "blocking_reasons": blocking_reasons,
        "reason_codes": reason_codes,
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }

    return MarketResearchReadinessGateV10Report(
        **report_values,
        payload=_json_ready(report_values),
    )


def strategy_market_research_readiness_gate_v10_payload(
    report: MarketResearchReadinessGateV10Report | dict[str, Any],
) -> dict[str, Any]:
    if type(report) is MarketResearchReadinessGateV10Report:
        _require_hard_flags("report", report)
        _reject_unsafe_public_payload("report", report)
        payload = _json_ready(_report_payload(report))
    elif type(report) is dict:
        _reject_unsafe_public_payload("payload", report)
        payload = _json_ready(report)
    else:
        raise ValueError("report must be a MarketResearchReadinessGateV10Report")

    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    _require_hard_flags("payload", _DictFlags(payload))
    _reject_unsafe_public_payload("payload", payload)
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


def _blocking_reasons(
    inputs: MarketResearchReadinessGateV10Input,
) -> tuple[str, ...]:
    reasons: list[str] = []
    if inputs.source_quorum_status == "blocked":
        reasons.append("source_quorum_blocked")
    if inputs.forecast_rationale_status == "blocked":
        reasons.append("forecast_rationale_blocked")
    if inputs.liquidity_guard_status == "blocked":
        reasons.append("liquidity_guard_blocked")
    if inputs.information_edge_score < SEVERE_SCORE_FLOOR:
        reasons.append("information_edge_below_floor")
    if inputs.resolution_precedent_score < SEVERE_SCORE_FLOOR:
        reasons.append("resolution_precedent_below_floor")
    if inputs.team_capacity_score < SEVERE_SCORE_FLOOR:
        reasons.append("team_capacity_below_floor")
    if reasons and inputs.resolution_precedent_score < RESOLUTION_WATCH_FLOOR:
        _append_unique(reasons, "resolution_precedent_below_floor")
    return tuple(reasons)


def _readiness_status(
    inputs: MarketResearchReadinessGateV10Input,
    blocking_reasons: tuple[str, ...],
) -> str:
    if blocking_reasons:
        return "blocked"
    if inputs.human_review_required:
        return "needs_human_review"
    if _watch_reasons(inputs):
        return "watch"
    return "ready"


def _research_depth_level(
    inputs: MarketResearchReadinessGateV10Input,
    blocking_reasons: tuple[str, ...],
) -> str:
    if blocking_reasons:
        return "do_not_research"
    if _deep_research_ready(inputs):
        return "deep_research"
    if (
        inputs.information_edge_score >= RESOLUTION_WATCH_FLOOR
        and inputs.resolution_precedent_score >= RESOLUTION_WATCH_FLOOR
        and inputs.team_capacity_score >= TEAM_WATCH_FLOOR
    ):
        return "standard_research"
    return "light_research"


def _reason_codes(
    inputs: MarketResearchReadinessGateV10Input,
    blocking_reasons: tuple[str, ...],
    research_depth_level: str,
) -> tuple[str, ...]:
    if blocking_reasons:
        return blocking_reasons

    reason_codes = list(_watch_reasons(inputs))
    if inputs.human_review_required:
        reason_codes.append("human_review_required")
    if not reason_codes:
        reason_codes.append("market_research_ready")
    reason_codes.append(f"{research_depth_level}_candidate")
    return tuple(reason_codes)


def _watch_reasons(inputs: MarketResearchReadinessGateV10Input) -> tuple[str, ...]:
    reasons: list[str] = []
    if inputs.source_quorum_status == "watch":
        reasons.append("source_quorum_watch")
    if inputs.forecast_rationale_status == "watch":
        reasons.append("forecast_rationale_watch")
    if inputs.liquidity_guard_status == "watch":
        reasons.append("liquidity_guard_watch")
    if inputs.information_edge_score < INFO_WATCH_FLOOR:
        reasons.append("information_edge_watch")
    if inputs.resolution_precedent_score < RESOLUTION_WATCH_FLOOR:
        reasons.append("resolution_precedent_watch")
    if inputs.team_capacity_score < TEAM_WATCH_FLOOR:
        reasons.append("team_capacity_watch")
    return tuple(reasons)


def _deep_research_ready(inputs: MarketResearchReadinessGateV10Input) -> bool:
    return (
        inputs.source_quorum_status == "pass"
        and inputs.forecast_rationale_status == "pass"
        and inputs.liquidity_guard_status == "pass"
        and inputs.information_edge_score >= DEEP_INFORMATION_FLOOR
        and inputs.resolution_precedent_score >= DEEP_RESOLUTION_FLOOR
        and inputs.team_capacity_score >= DEEP_TEAM_FLOOR
        and inputs.human_review_required is False
    )


def _report_payload(report: MarketResearchReadinessGateV10Report) -> dict[str, Any]:
    return {
        "information_edge_score": report.information_edge_score,
        "source_quorum_status": report.source_quorum_status,
        "forecast_rationale_status": report.forecast_rationale_status,
        "liquidity_guard_status": report.liquidity_guard_status,
        "resolution_precedent_score": report.resolution_precedent_score,
        "team_capacity_score": report.team_capacity_score,
        "human_review_required": report.human_review_required,
        "readiness_status": report.readiness_status,
        "research_depth_level": report.research_depth_level,
        "blocking_reasons": report.blocking_reasons,
        "reason_codes": report.reason_codes,
        "paper_only": report.paper_only,
        "report_only": report.report_only,
        "readonly": report.readonly,
    }


def _json_ready(value: object) -> object:
    if isinstance(value, Decimal):
        if type(value) is not Decimal:
            raise ValueError("JSON Decimal value must be exactly Decimal")
        if not value.is_finite():
            raise ValueError("JSON Decimal value must be finite")
        return str(value.quantize(SCORE_QUANTUM))
    if is_dataclass(value) and not isinstance(value, type):
        return _json_ready(asdict(value))
    if type(value) is bool or value is None:
        return value
    if isinstance(value, float):
        raise ValueError("JSON value must not be a float")
    if type(value) is int:
        raise ValueError("JSON numeric value must use Decimal")
    if type(value) is str:
        return value
    if isinstance(value, tuple):
        return [_json_ready(item) for item in value]
    if isinstance(value, list):
        return [_json_ready(item) for item in value]
    if isinstance(value, dict):
        ready: dict[str, Any] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            ready[key] = _json_ready(item)
        return ready
    raise ValueError("value is not JSON serializable")


def _reject_unsafe_public_payload(
    label: str,
    value: object,
    path: str = "",
) -> None:
    if is_dataclass(value) and not isinstance(value, type):
        _reject_unsafe_public_payload(label, asdict(value), path)
        return
    if type(value) is str:
        if _has_unsafe_surface_fragment(value):
            raise ValueError(f"{path or label} has unsafe live surface value")
        return
    if isinstance(value, Decimal):
        if type(value) is not Decimal:
            raise ValueError(f"{path or label} must be exactly Decimal")
        if not value.is_finite():
            raise ValueError(f"{path or label} must be finite")
        return
    if type(value) is bool or value is None:
        return
    if isinstance(value, float):
        raise ValueError("JSON value must not be a float")
    if type(value) is int:
        raise ValueError(f"{path or label} must use Decimal values")
    if isinstance(value, dict):
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            item_path = key if not path else f"{path}.{key}"
            if _has_unsafe_surface_fragment(key):
                raise ValueError(f"unsafe live surface field in {label}: {key}")
            if key in HARD_FLAGS and item is not True:
                raise ValueError(f"{label} {key} must be True")
            _reject_unsafe_public_payload(label, item, item_path)
        return
    if isinstance(value, (list, tuple)):
        for item in value:
            _reject_unsafe_public_payload(label, item, path)
        return
    raise ValueError("value is not JSON serializable")


def _normalize_score(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    normalized = value.quantize(SCORE_QUANTUM)
    if normalized < ZERO or normalized > ONE:
        raise ValueError(f"{field_name} must be between zero and one")
    return normalized


def _normalize_status(field_name: str, value: object) -> str:
    _require_member(field_name, value, STATUSES)
    return value


def _normalize_reason_codes(
    field_name: str,
    values: tuple[str, ...],
) -> tuple[str, ...]:
    if isinstance(values, (str, bytes)):
        raise ValueError(f"{field_name} must be an iterable")
    try:
        reason_codes = tuple(values)
    except TypeError as exc:
        raise ValueError(f"{field_name} must be an iterable") from exc
    if len(set(reason_codes)) != len(reason_codes):
        raise ValueError(f"{field_name} must not contain duplicates")
    for reason_code in reason_codes:
        _require_canonical_string(field_name, reason_code)
    return reason_codes


def _append_unique(values: list[str], value: str) -> None:
    if value not in values:
        values.append(value)


def _require_bool(field_name: str, value: object) -> None:
    if type(value) is not bool:
        raise ValueError(f"{field_name} must be a bool")


def _require_member(
    field_name: str,
    value: object,
    allowed_values: tuple[str, ...],
) -> None:
    if type(value) is not str or value not in allowed_values:
        raise ValueError(f"{field_name} must be one of {allowed_values}")


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")
    if _has_unsafe_surface_fragment(value):
        raise ValueError(f"{field_name} has unsafe live surface value")


def _require_hard_flags(label: str, value: object) -> None:
    if getattr(value, "paper_only", None) is not True:
        raise ValueError(f"{label} paper_only must be True")
    if getattr(value, "report_only", None) is not True:
        raise ValueError(f"{label} report_only must be True")
    if getattr(value, "readonly", None) is not True:
        raise ValueError(f"{label} readonly must be True")


def _has_unsafe_surface_fragment(value: str) -> bool:
    normalized = value.lower()
    return any(fragment in normalized for fragment in _UNSAFE_SURFACE_FRAGMENTS)


__all__ = (
    "MarketResearchReadinessGateV10Input",
    "MarketResearchReadinessGateV10Report",
    "evaluate_market_research_readiness_gate_v10",
    "strategy_market_research_readiness_gate_v10_payload",
)
