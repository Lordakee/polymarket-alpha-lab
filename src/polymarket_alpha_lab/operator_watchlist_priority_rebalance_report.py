"""Pure in-memory operator watchlist priority rebalance report."""

from __future__ import annotations

from dataclasses import asdict, dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal
from hashlib import sha256
import json
from typing import Any


__all__ = (
    "DEFAULT_OPERATOR_WATCHLIST_PRIORITY_REBALANCE_REPORT_CONFIG_VERSION",
    "OperatorWatchlistPriorityRebalanceInput",
    "OperatorWatchlistPriorityRebalanceReport",
    "build_operator_watchlist_priority_rebalance_report",
    "operator_watchlist_priority_rebalance_report_digest",
    "operator_watchlist_priority_rebalance_report_payload",
)


DEFAULT_OPERATOR_WATCHLIST_PRIORITY_REBALANCE_REPORT_CONFIG_VERSION = (
    "operator-watchlist-priority-rebalance-report-v0"
)
COUNT_QUANTUM = Decimal("1.000000")
ZERO = Decimal("0.000000")
MIN_MANUAL_WINDOW_MINUTES = Decimal("30.000000")
REBALANCE_STATUSES = ("pass", "watch", "blocked")
PRIORITY_QUEUE_ACTIONS = (
    "maintain_current_priority_queue",
    "defer_rebalance_until_manual_window",
    "refresh_stale_candidates_before_rebalance",
    "rebalance_high_edge_candidates_first",
    "clear_blockers_before_rebalance",
)
MANUAL_NEXT_STEPS = (
    "continue_operator_watchlist_monitoring",
    "schedule_additional_manual_review_time",
    "refresh_stale_candidates_then_rebalance",
    "review_high_edge_candidates_within_capacity",
    "resolve_blocked_watchlist_items_before_review",
)
REASON_CODES = (
    "operator_watchlist_priority_queue_current",
    "operator_watchlist_time_budget_constrained",
    "operator_watchlist_stale_items_present",
    "operator_watchlist_high_edge_backlog",
    "operator_watchlist_manual_capacity_constrained",
    "operator_watchlist_blocked_items_present",
)
PHASE_FLAG_FIELDS = ("paper_only", "report_only", "readonly")
UNSAFE_PUBLIC_FRAGMENTS = (
    "au" + "th",
    "credential",
    "private",
    "secret",
    "tok" + "en",
    "wal" + "let",
    "ord" + "er",
    "broker",
    "buy",
    "sell",
    "trade",
    "network",
    "li" + "ve",
    "js" + "onl",
    "per" + "sist",
    "si" + "gn",
    "exec" + "ute",
)


class _FinalPublicDataclass:
    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        for base in cls.__bases__:
            if base is not _FinalPublicDataclass and issubclass(
                base,
                _FinalPublicDataclass,
            ):
                raise TypeError(f"{base.__name__} may not be subclassed")


@dataclass(frozen=True)
class OperatorWatchlistPriorityRebalanceInput(_FinalPublicDataclass):
    candidate_count: Decimal
    high_edge_count: Decimal
    stale_count: Decimal
    blocked_count: Decimal
    manual_capacity_slots: Decimal
    time_budget_minutes: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, OperatorWatchlistPriorityRebalanceInput, "input")
        for field_name in (
            "candidate_count",
            "high_edge_count",
            "stale_count",
            "blocked_count",
            "manual_capacity_slots",
            "time_budget_minutes",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        _require_at_most("high_edge_count", self.high_edge_count, self.candidate_count)
        _require_at_most("stale_count", self.stale_count, self.candidate_count)
        _require_at_most("blocked_count", self.blocked_count, self.candidate_count)
        _require_hard_flags("input", self)
        _reject_unsafe_public_payload("input", self)


@dataclass(frozen=True)
class OperatorWatchlistPriorityRebalanceReport(_FinalPublicDataclass):
    generated_at: datetime
    config_version: str
    candidate_count: Decimal
    high_edge_count: Decimal
    stale_count: Decimal
    blocked_count: Decimal
    manual_capacity_slots: Decimal
    time_budget_minutes: Decimal
    rebalance_status: str
    priority_queue_action: str
    reason_codes: tuple[str, ...]
    manual_next_step: str
    payload_digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, OperatorWatchlistPriorityRebalanceReport, "report")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_string("config_version", self.config_version)
        for field_name in (
            "candidate_count",
            "high_edge_count",
            "stale_count",
            "blocked_count",
            "manual_capacity_slots",
            "time_budget_minutes",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        _require_at_most("high_edge_count", self.high_edge_count, self.candidate_count)
        _require_at_most("stale_count", self.stale_count, self.candidate_count)
        _require_at_most("blocked_count", self.blocked_count, self.candidate_count)
        _require_member("rebalance_status", self.rebalance_status, REBALANCE_STATUSES)
        _require_member(
            "priority_queue_action",
            self.priority_queue_action,
            PRIORITY_QUEUE_ACTIONS,
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        _require_member("manual_next_step", self.manual_next_step, MANUAL_NEXT_STEPS)
        _require_digest("payload_digest", self.payload_digest)
        _require_hard_flags("report", self)
        _reject_unsafe_public_payload("report", self)
        if self.payload_digest != _report_digest_from_values(self):
            raise ValueError("payload_digest must match report fields")

    @property
    def public_payload(self) -> dict[str, Any]:
        return operator_watchlist_priority_rebalance_report_payload(self)


def build_operator_watchlist_priority_rebalance_report(
    inputs: OperatorWatchlistPriorityRebalanceInput,
    *,
    generated_at: datetime,
) -> OperatorWatchlistPriorityRebalanceReport:
    if type(inputs) is not OperatorWatchlistPriorityRebalanceInput:
        raise ValueError("inputs must be an OperatorWatchlistPriorityRebalanceInput")
    generated_at = _as_utc("generated_at", generated_at)
    reason_codes = _reason_codes_for_inputs(inputs)
    rebalance_status = _rebalance_status(reason_codes)
    priority_queue_action = _priority_queue_action(reason_codes)
    manual_next_step = _manual_next_step(priority_queue_action)
    values: dict[str, object] = {
        "generated_at": generated_at,
        "config_version": DEFAULT_OPERATOR_WATCHLIST_PRIORITY_REBALANCE_REPORT_CONFIG_VERSION,
        "candidate_count": inputs.candidate_count,
        "high_edge_count": inputs.high_edge_count,
        "stale_count": inputs.stale_count,
        "blocked_count": inputs.blocked_count,
        "manual_capacity_slots": inputs.manual_capacity_slots,
        "time_budget_minutes": inputs.time_budget_minutes,
        "rebalance_status": rebalance_status,
        "priority_queue_action": priority_queue_action,
        "reason_codes": reason_codes,
        "manual_next_step": manual_next_step,
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    values["payload_digest"] = _payload_digest(values)
    return OperatorWatchlistPriorityRebalanceReport(**values)  # type: ignore[arg-type]


def operator_watchlist_priority_rebalance_report_payload(
    report: OperatorWatchlistPriorityRebalanceReport | dict[str, Any],
) -> dict[str, Any]:
    if type(report) is OperatorWatchlistPriorityRebalanceReport:
        _require_hard_flags("report", report)
        _reject_unsafe_public_payload("report", report)
        payload = _json_ready(report)
    elif type(report) is dict:
        _reject_unsafe_public_payload("payload", report)
        _reject_public_numeric_values(report)
        payload = _json_ready(report)
    else:
        raise ValueError(
            "report must be an OperatorWatchlistPriorityRebalanceReport or payload",
        )
    if type(payload) is not dict:
        raise ValueError("payload must be a JSON object")
    _validate_public_payload(payload)
    _reject_unsafe_public_payload("payload", payload)
    return payload


def operator_watchlist_priority_rebalance_report_digest(
    report: OperatorWatchlistPriorityRebalanceReport | dict[str, Any],
) -> str:
    if type(report) is OperatorWatchlistPriorityRebalanceReport:
        return _report_digest_from_values(report)
    if type(report) is dict:
        payload = _json_ready(report)
        if type(payload) is not dict:
            raise ValueError("payload must be a JSON object")
        return _payload_digest(payload)
    raise ValueError(
        "report must be an OperatorWatchlistPriorityRebalanceReport or payload",
    )


def _reason_codes_for_inputs(
    inputs: OperatorWatchlistPriorityRebalanceInput,
) -> tuple[str, ...]:
    reasons: list[str] = []
    if inputs.blocked_count > ZERO:
        reasons.append("operator_watchlist_blocked_items_present")
    if inputs.high_edge_count > inputs.manual_capacity_slots:
        reasons.append("operator_watchlist_high_edge_backlog")
    if inputs.stale_count > ZERO:
        reasons.append("operator_watchlist_stale_items_present")
    if inputs.manual_capacity_slots < inputs.candidate_count:
        reasons.append("operator_watchlist_manual_capacity_constrained")
    if inputs.time_budget_minutes < MIN_MANUAL_WINDOW_MINUTES:
        reasons.append("operator_watchlist_time_budget_constrained")
    if not reasons:
        reasons.append("operator_watchlist_priority_queue_current")
    return tuple(reasons)


def _rebalance_status(reason_codes: tuple[str, ...]) -> str:
    if "operator_watchlist_blocked_items_present" in reason_codes:
        return "blocked"
    if reason_codes == ("operator_watchlist_priority_queue_current",):
        return "pass"
    return "watch"


def _priority_queue_action(reason_codes: tuple[str, ...]) -> str:
    if "operator_watchlist_blocked_items_present" in reason_codes:
        return "clear_blockers_before_rebalance"
    if "operator_watchlist_time_budget_constrained" in reason_codes:
        return "defer_rebalance_until_manual_window"
    if "operator_watchlist_stale_items_present" in reason_codes:
        return "refresh_stale_candidates_before_rebalance"
    if "operator_watchlist_high_edge_backlog" in reason_codes:
        return "rebalance_high_edge_candidates_first"
    return "maintain_current_priority_queue"


def _manual_next_step(priority_queue_action: str) -> str:
    if priority_queue_action == "clear_blockers_before_rebalance":
        return "resolve_blocked_watchlist_items_before_review"
    if priority_queue_action == "defer_rebalance_until_manual_window":
        return "schedule_additional_manual_review_time"
    if priority_queue_action == "refresh_stale_candidates_before_rebalance":
        return "refresh_stale_candidates_then_rebalance"
    if priority_queue_action == "rebalance_high_edge_candidates_first":
        return "review_high_edge_candidates_within_capacity"
    return "continue_operator_watchlist_monitoring"


def _report_digest_from_values(
    report: OperatorWatchlistPriorityRebalanceReport,
) -> str:
    return _payload_digest(_json_ready(_report_values_without_digest(report)))


def _report_values_without_digest(
    report: OperatorWatchlistPriorityRebalanceReport,
) -> dict[str, object]:
    values = asdict(report)
    values.pop("payload_digest", None)
    return values


def _payload_digest(payload: dict[str, object]) -> str:
    hash_payload = dict(payload)
    hash_payload.pop("payload_digest", None)
    canonical = json.dumps(
        _json_ready(hash_payload),
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    )
    return sha256(canonical.encode("utf-8")).hexdigest()


def _validate_public_payload(payload: dict[str, Any]) -> None:
    expected_names = {field.name for field in fields(OperatorWatchlistPriorityRebalanceReport)}
    if set(payload) != expected_names:
        raise ValueError("payload must contain exactly report fields")
    _require_hard_flags("payload", _DictFlags(payload))
    _as_utc("generated_at", payload["generated_at"])
    _require_public_string("config_version", payload["config_version"])
    for field_name in (
        "candidate_count",
        "high_edge_count",
        "stale_count",
        "blocked_count",
        "manual_capacity_slots",
        "time_budget_minutes",
    ):
        _require_decimal_string(field_name, payload[field_name])
    _require_at_most(
        "high_edge_count",
        Decimal(payload["high_edge_count"]),
        Decimal(payload["candidate_count"]),
    )
    _require_at_most(
        "stale_count",
        Decimal(payload["stale_count"]),
        Decimal(payload["candidate_count"]),
    )
    _require_at_most(
        "blocked_count",
        Decimal(payload["blocked_count"]),
        Decimal(payload["candidate_count"]),
    )
    _require_member("rebalance_status", payload["rebalance_status"], REBALANCE_STATUSES)
    _require_member(
        "priority_queue_action",
        payload["priority_queue_action"],
        PRIORITY_QUEUE_ACTIONS,
    )
    _normalize_reason_codes("reason_codes", payload["reason_codes"])
    _require_member("manual_next_step", payload["manual_next_step"], MANUAL_NEXT_STEPS)
    _require_digest("payload_digest", payload["payload_digest"])
    if payload["payload_digest"] != _payload_digest(payload):
        raise ValueError("payload_digest must match payload values")


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


def _require_exact_type(value: object, expected_type: type[object], label: str) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{label} must use the exact public dataclass type")


def _normalize_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        if isinstance(value, Decimal):
            raise ValueError(f"{field_name} must use plain Decimal")
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    if value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return value.quantize(COUNT_QUANTUM)


def _require_at_most(field_name: str, value: Decimal, maximum: Decimal) -> None:
    if value > maximum:
        raise ValueError(f"{field_name} cannot exceed candidate_count")


def _normalize_reason_codes(field_name: str, value: object) -> tuple[str, ...]:
    if type(value) not in (list, tuple):
        raise ValueError(f"{field_name} must be a sequence")
    normalized: list[str] = []
    for item in value:
        _require_member(field_name, item, REASON_CODES)
        if item not in normalized:
            normalized.append(item)
    if not normalized:
        raise ValueError(f"{field_name} must not be empty")
    return tuple(normalized)


def _require_member(field_name: str, value: object, allowed_values: tuple[str, ...]) -> None:
    if type(value) is not str or value not in allowed_values:
        raise ValueError(f"{field_name} must be one of the supported values")


def _require_public_string(field_name: str, value: object) -> str:
    if type(value) is not str or not value:
        raise ValueError(f"{field_name} must be a non-empty string")
    _reject_unsafe_public_text(field_name, value)
    return value


def _require_decimal_string(field_name: str, value: object) -> Decimal:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a Decimal string")
    try:
        parsed = Decimal(value)
    except Exception as exc:
        raise ValueError(f"{field_name} must be a Decimal string") from exc
    if parsed < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    if str(parsed.quantize(COUNT_QUANTUM)) != value:
        raise ValueError(f"{field_name} must be canonical")
    return parsed


def _require_digest(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if len(value) != 64 or any(character not in "0123456789abcdef" for character in value):
        raise ValueError(f"{field_name} must be a lowercase sha256 hex digest")
    return value


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in PHASE_FLAG_FIELDS:
        if getattr(value, field_name, None) is not True:
            raise ValueError(f"{field_name} must be True for {label}")


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is str:
        try:
            value = datetime.fromisoformat(value)
        except ValueError as exc:
            raise ValueError(f"{field_name} must be a valid datetime") from exc
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _json_ready(value: Any) -> Any:
    if value is None:
        return None
    if is_dataclass(value) and not isinstance(value, type):
        return _json_ready(asdict(value))
    if type(value) is Decimal:
        if not value.is_finite():
            raise ValueError("JSON Decimal value must be finite")
        return str(value.quantize(COUNT_QUANTUM))
    if isinstance(value, Decimal):
        raise ValueError("JSON Decimal value must use plain Decimal")
    if type(value) is datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("JSON datetime value must be timezone-aware")
        return value.astimezone(UTC).isoformat()
    if isinstance(value, float) or type(value) is int:
        raise ValueError("JSON numeric value must use Decimal")
    if type(value) in (str, bool):
        return value
    if type(value) is dict:
        ready: dict[str, Any] = {}
        for name, item in value.items():
            if type(name) is not str:
                raise ValueError("JSON object names must be strings")
            ready[name] = _json_ready(item)
        return ready
    if type(value) in (list, tuple):
        return [_json_ready(item) for item in value]
    raise ValueError("value is not JSON serializable")


def _reject_public_numeric_values(value: object) -> None:
    if isinstance(value, float) or type(value) is int:
        raise ValueError("public payload numerics must be Decimal-derived strings")
    if type(value) is dict:
        for item in value.values():
            _reject_public_numeric_values(item)
        return
    if type(value) is list:
        for item in value:
            _reject_public_numeric_values(item)


def _reject_unsafe_public_payload(label: str, value: object) -> None:
    if is_dataclass(value) and not isinstance(value, type):
        _reject_unsafe_public_payload(label, asdict(value))
        return
    if type(value) is str:
        _reject_unsafe_public_text(label, value)
        return
    if type(value) in (Decimal, datetime, bool) or value is None:
        return
    if isinstance(value, float) or type(value) is int:
        raise ValueError("unsafe public payload numeric value")
    if type(value) is dict:
        for name, item in value.items():
            if type(name) is not str:
                raise ValueError("payload names must be strings")
            _reject_unsafe_public_text(label, name)
            _reject_unsafe_public_payload(label, item)
        return
    if type(value) in (list, tuple):
        for item in value:
            _reject_unsafe_public_payload(label, item)
        return
    raise ValueError("unsafe public payload value")


def _reject_unsafe_public_text(label: str, value: str) -> None:
    lowered = value.lower()
    if any(fragment in lowered for fragment in UNSAFE_PUBLIC_FRAGMENTS):
        raise ValueError(f"unsafe public value in {label}")
