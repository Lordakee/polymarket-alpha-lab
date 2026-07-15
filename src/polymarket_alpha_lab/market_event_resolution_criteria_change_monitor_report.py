"""Phase 1 public report for resolution criteria change monitoring."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from decimal import Decimal
import hashlib
import json
from typing import Any, Mapping

from polymarket_alpha_lab.team_paper_guard import json_ready_no_floats


def _join_parts(*parts: str) -> str:
    return "".join(parts)


UNCHANGED_STATUS = "unchanged"
ATTENTION_STATUS = "attention"
CHANGED_STATUS = "changed"

CRITERIA_UNCHANGED_REASON = "market_event_resolution_criteria_unchanged"
SNAPSHOT_DIGEST_MISSING_REASON = (
    "market_event_resolution_criteria_snapshot_digest_missing"
)
DIGEST_CHANGED_REASON = "market_event_resolution_criteria_digest_changed"
OFFICIAL_UPDATES_PRESENT_REASON = (
    "market_event_resolution_criteria_official_updates_present"
)
AMBIGUOUS_UPDATES_PRESENT_REASON = (
    "market_event_resolution_criteria_ambiguous_updates_present"
)
CLOSE_WINDOW_ATTENTION_REASON = (
    "market_event_resolution_criteria_close_window_attention"
)

REASON_CODE_SEQUENCE = (
    DIGEST_CHANGED_REASON,
    OFFICIAL_UPDATES_PRESENT_REASON,
    SNAPSHOT_DIGEST_MISSING_REASON,
    AMBIGUOUS_UPDATES_PRESENT_REASON,
    CLOSE_WINDOW_ATTENTION_REASON,
    CRITERIA_UNCHANGED_REASON,
)
PAYLOAD_KEYS_WITHOUT_DIGEST = (
    "criteria_snapshot_digest_present",
    "latest_criteria_digest_matches",
    "official_update_count",
    "ambiguous_update_count",
    "market_close_hours",
    "criteria_change_status",
    "reason_codes",
    "manual_next_step",
    "paper_only",
    "report_only",
    "readonly",
)
PAYLOAD_KEYS = (*PAYLOAD_KEYS_WITHOUT_DIGEST, "payload_digest")
CLOSE_WINDOW_HOURS = Decimal("24.000000")
QUANT = Decimal("0.000001")
ZERO = Decimal("0")

NO_ACTION_NEXT_STEP = (
    "No manual criteria-change action required; keep monitoring in report-only mode."
)
CAPTURE_DIGEST_NEXT_STEP = (
    "Manually capture the current public resolution criteria digest before "
    "closing the monitoring review."
)
COMPARE_UPDATES_NEXT_STEP = (
    "Manually compare official resolution criteria updates before relying on "
    "the market event resolution packet."
)

UNSAFE_PUBLIC_KEY_FRAGMENTS = (
    "live",
    _join_parts("au", "th"),
    _join_parts("wal", "let"),
    _join_parts("or", "der"),
    "private",
    "secret",
    "token",
    "key",
    "sign",
)
UNSAFE_PUBLIC_TEXT_TOKENS = (
    "live",
    _join_parts("au", "th"),
    _join_parts("wal", "let"),
    _join_parts("or", "der"),
    "private",
    "secret",
    "token",
    "sign",
    _join_parts("exec", "ute"),
    "recommend",
)

__all__ = (
    "ATTENTION_STATUS",
    "CHANGED_STATUS",
    "UNCHANGED_STATUS",
    "MarketEventResolutionCriteriaChangeMonitorInput",
    "MarketEventResolutionCriteriaChangeMonitorReport",
    "build_market_event_resolution_criteria_change_monitor_report",
    "market_event_resolution_criteria_change_monitor_report_payload",
)


@dataclass(frozen=True)
class MarketEventResolutionCriteriaChangeMonitorInput:
    criteria_snapshot_digest_present: bool
    latest_criteria_digest_matches: bool
    official_update_count: Decimal
    ambiguous_update_count: Decimal
    market_close_hours: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketEventResolutionCriteriaChangeMonitorInput:
            raise TypeError(
                "MarketEventResolutionCriteriaChangeMonitorInput does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not MarketEventResolutionCriteriaChangeMonitorInput:
            raise ValueError(
                "input must be exactly MarketEventResolutionCriteriaChangeMonitorInput",
            )
        for field_name in (
            "criteria_snapshot_digest_present",
            "latest_criteria_digest_matches",
        ):
            _require_bool(field_name, getattr(self, field_name))
        for field_name in (
            "official_update_count",
            "ambiguous_update_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_whole_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "market_close_hours",
            _require_nonnegative_decimal("market_close_hours", self.market_close_hours),
        )
        _require_hard_flags("criteria change monitor input", self)


@dataclass(frozen=True)
class MarketEventResolutionCriteriaChangeMonitorReport:
    criteria_snapshot_digest_present: bool
    latest_criteria_digest_matches: bool
    official_update_count: Decimal
    ambiguous_update_count: Decimal
    market_close_hours: Decimal
    criteria_change_status: str
    reason_codes: tuple[str, ...]
    manual_next_step: str
    payload_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketEventResolutionCriteriaChangeMonitorReport:
            raise TypeError(
                "MarketEventResolutionCriteriaChangeMonitorReport does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not MarketEventResolutionCriteriaChangeMonitorReport:
            raise ValueError(
                "report must be exactly MarketEventResolutionCriteriaChangeMonitorReport",
            )
        for field_name in (
            "criteria_snapshot_digest_present",
            "latest_criteria_digest_matches",
        ):
            _require_bool(field_name, getattr(self, field_name))
        for field_name in (
            "official_update_count",
            "ambiguous_update_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_whole_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "market_close_hours",
            _require_nonnegative_decimal("market_close_hours", self.market_close_hours),
        )
        _require_status("criteria_change_status", self.criteria_change_status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        _require_public_text("manual_next_step", self.manual_next_step)
        _require_hard_flags("criteria change monitor report", self)
        _validate_report_consistency(self)
        expected_digest = _payload_digest(_payload_values_without_digest(self))
        if self.payload_digest:
            _require_digest("payload_digest", self.payload_digest)
            if self.payload_digest != expected_digest:
                raise ValueError("payload_digest must match report payload")
        else:
            object.__setattr__(self, "payload_digest", expected_digest)

    @property
    def public_payload(self) -> dict[str, Any]:
        return market_event_resolution_criteria_change_monitor_report_payload(self)


def build_market_event_resolution_criteria_change_monitor_report(
    monitor_input: MarketEventResolutionCriteriaChangeMonitorInput,
) -> MarketEventResolutionCriteriaChangeMonitorReport:
    if type(monitor_input) is not MarketEventResolutionCriteriaChangeMonitorInput:
        raise ValueError(
            "monitor_input must be a MarketEventResolutionCriteriaChangeMonitorInput",
        )
    reason_codes = _reason_codes_for_input(monitor_input)
    status = _status_for_reason_codes(reason_codes)
    return MarketEventResolutionCriteriaChangeMonitorReport(
        criteria_snapshot_digest_present=monitor_input.criteria_snapshot_digest_present,
        latest_criteria_digest_matches=monitor_input.latest_criteria_digest_matches,
        official_update_count=monitor_input.official_update_count,
        ambiguous_update_count=monitor_input.ambiguous_update_count,
        market_close_hours=monitor_input.market_close_hours,
        criteria_change_status=status,
        reason_codes=reason_codes,
        manual_next_step=_manual_next_step(
            status,
            monitor_input.criteria_snapshot_digest_present,
        ),
    )


def market_event_resolution_criteria_change_monitor_report_payload(
    report_or_payload: MarketEventResolutionCriteriaChangeMonitorReport
    | Mapping[str, object],
) -> dict[str, Any]:
    if type(report_or_payload) is MarketEventResolutionCriteriaChangeMonitorReport:
        payload = _payload_with_digest(report_or_payload)
    elif isinstance(report_or_payload, Mapping):
        payload = dict(report_or_payload)
    else:
        raise ValueError(
            "report_or_payload must be a MarketEventResolutionCriteriaChangeMonitorReport "
            "or mapping",
        )
    _validate_public_payload(payload)
    return payload


def _reason_codes_for_input(
    monitor_input: MarketEventResolutionCriteriaChangeMonitorInput,
) -> tuple[str, ...]:
    reasons: list[str] = []
    if monitor_input.latest_criteria_digest_matches is not True:
        reasons.append(DIGEST_CHANGED_REASON)
    if monitor_input.official_update_count > ZERO:
        reasons.append(OFFICIAL_UPDATES_PRESENT_REASON)
    if monitor_input.ambiguous_update_count > ZERO:
        reasons.append(AMBIGUOUS_UPDATES_PRESENT_REASON)
    if _has_close_window_attention(monitor_input):
        reasons.append(CLOSE_WINDOW_ATTENTION_REASON)
    if monitor_input.criteria_snapshot_digest_present is not True:
        reasons.append(SNAPSHOT_DIGEST_MISSING_REASON)
    selected_reasons = tuple(reason for reason in REASON_CODE_SEQUENCE if reason in reasons)
    if not selected_reasons:
        return (CRITERIA_UNCHANGED_REASON,)
    return selected_reasons


def _status_for_reason_codes(reason_codes: tuple[str, ...]) -> str:
    if DIGEST_CHANGED_REASON in reason_codes or OFFICIAL_UPDATES_PRESENT_REASON in reason_codes:
        return CHANGED_STATUS
    if reason_codes == (CRITERIA_UNCHANGED_REASON,):
        return UNCHANGED_STATUS
    return ATTENTION_STATUS


def _manual_next_step(status: str, snapshot_present: bool) -> str:
    if status == CHANGED_STATUS:
        return COMPARE_UPDATES_NEXT_STEP
    if snapshot_present is not True:
        return CAPTURE_DIGEST_NEXT_STEP
    if status == ATTENTION_STATUS:
        return (
            "Manually review ambiguous public criteria updates before closing "
            "the monitoring review."
        )
    return NO_ACTION_NEXT_STEP


def _has_close_window_attention(
    monitor_input: MarketEventResolutionCriteriaChangeMonitorInput,
) -> bool:
    if monitor_input.market_close_hours > CLOSE_WINDOW_HOURS:
        return False
    return (
        monitor_input.latest_criteria_digest_matches is not True
        or monitor_input.official_update_count > ZERO
        or monitor_input.ambiguous_update_count > ZERO
    )


def _payload_with_digest(
    report: MarketEventResolutionCriteriaChangeMonitorReport,
) -> dict[str, Any]:
    _validate_report_consistency(report)
    payload = _payload_values_without_digest(report)
    payload["payload_digest"] = report.payload_digest
    ready_payload = json_ready_no_floats(payload)
    if type(ready_payload) is not dict:
        raise ValueError("public payload must be a dict")
    return ready_payload


def _payload_values_without_digest(
    report: MarketEventResolutionCriteriaChangeMonitorReport,
) -> dict[str, object]:
    values = {
        key: asdict(report)[key]
        for key in PAYLOAD_KEYS_WITHOUT_DIGEST
    }
    values["paper_only"] = True
    values["report_only"] = True
    values["readonly"] = True
    return values


def _validate_public_payload(payload: Mapping[str, object]) -> None:
    if tuple(payload.keys()) != PAYLOAD_KEYS:
        raise ValueError("public payload schema must match criteria change monitor report")
    _reject_unsafe_public_values(payload)
    _require_bool("criteria_snapshot_digest_present", payload["criteria_snapshot_digest_present"])
    _require_bool("latest_criteria_digest_matches", payload["latest_criteria_digest_matches"])
    for field_name in (
        "official_update_count",
        "ambiguous_update_count",
        "market_close_hours",
    ):
        _require_decimal_string(field_name, payload[field_name])
    _require_status("criteria_change_status", payload["criteria_change_status"])
    reason_codes = _normalize_payload_reason_codes("reason_codes", payload["reason_codes"])
    _require_public_text("manual_next_step", payload["manual_next_step"])
    for field_name in ("paper_only", "report_only", "readonly"):
        _require_bool(field_name, payload[field_name])
        if payload[field_name] is not True:
            raise ValueError(f"{field_name} must be True")
    payload_digest = _require_digest("payload_digest", payload["payload_digest"])
    expected = _payload_digest({key: payload[key] for key in PAYLOAD_KEYS_WITHOUT_DIGEST})
    if payload_digest != expected:
        raise ValueError("payload_digest must match public payload")
    source = MarketEventResolutionCriteriaChangeMonitorInput(
        criteria_snapshot_digest_present=payload["criteria_snapshot_digest_present"],  # type: ignore[arg-type]
        latest_criteria_digest_matches=payload["latest_criteria_digest_matches"],  # type: ignore[arg-type]
        official_update_count=Decimal(payload["official_update_count"]),  # type: ignore[arg-type]
        ambiguous_update_count=Decimal(payload["ambiguous_update_count"]),  # type: ignore[arg-type]
        market_close_hours=Decimal(payload["market_close_hours"]),  # type: ignore[arg-type]
    )
    expected_reason_codes = _reason_codes_for_input(source)
    if reason_codes != expected_reason_codes:
        raise ValueError("reason_codes must match criteria fields")
    expected_status = _status_for_reason_codes(expected_reason_codes)
    if payload["criteria_change_status"] != expected_status:
        raise ValueError("criteria_change_status must match reason_codes")
    expected_step = _manual_next_step(
        expected_status,
        source.criteria_snapshot_digest_present,
    )
    if payload["manual_next_step"] != expected_step:
        raise ValueError("manual_next_step must match criteria_change_status")


def _validate_report_consistency(
    report: MarketEventResolutionCriteriaChangeMonitorReport,
) -> None:
    source = MarketEventResolutionCriteriaChangeMonitorInput(
        criteria_snapshot_digest_present=report.criteria_snapshot_digest_present,
        latest_criteria_digest_matches=report.latest_criteria_digest_matches,
        official_update_count=report.official_update_count,
        ambiguous_update_count=report.ambiguous_update_count,
        market_close_hours=report.market_close_hours,
    )
    expected_reason_codes = _reason_codes_for_input(source)
    if report.reason_codes != expected_reason_codes:
        raise ValueError("reason_codes must match criteria fields")
    expected_status = _status_for_reason_codes(expected_reason_codes)
    if report.criteria_change_status != expected_status:
        raise ValueError("criteria_change_status must match reason_codes")
    if report.manual_next_step != _manual_next_step(
        expected_status,
        report.criteria_snapshot_digest_present,
    ):
        raise ValueError("manual_next_step must match criteria_change_status")


def _payload_digest(payload_values: Mapping[str, object]) -> str:
    ready = json_ready_no_floats(dict(payload_values))
    _reject_unsafe_public_values(ready)
    canonical = json.dumps(
        ready,
        separators=(",", ":"),
        sort_keys=True,
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _normalize_reason_codes(
    field_name: str,
    value: object,
) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ValueError(f"{field_name} must be a tuple")
    _reject_duplicate_reason_codes(field_name, value)
    for reason_code in value:
        _require_reason_code(field_name, reason_code)
    return value


def _normalize_payload_reason_codes(
    field_name: str,
    value: object,
) -> tuple[str, ...]:
    if type(value) is list:
        reason_codes = tuple(value)
    elif type(value) is tuple:
        reason_codes = value
    else:
        raise ValueError(f"{field_name} must be a list")
    return _normalize_reason_codes(field_name, reason_codes)


def _reject_duplicate_reason_codes(field_name: str, value: tuple[object, ...]) -> None:
    if len(set(value)) != len(value):
        raise ValueError(f"{field_name} must not contain duplicates")


def _require_reason_code(field_name: str, value: object) -> None:
    if type(value) is not str or value not in REASON_CODE_SEQUENCE:
        raise ValueError(f"{field_name} contains an unsupported reason code")


def _require_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in (
        UNCHANGED_STATUS,
        ATTENTION_STATUS,
        CHANGED_STATUS,
    ):
        raise ValueError(f"{field_name} must be a supported criteria change status")


def _require_bool(field_name: str, value: object) -> None:
    if type(value) is not bool:
        raise ValueError(f"{field_name} must be a bool")


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if getattr(value, field_name) is not True:
            raise ValueError(f"{field_name} must be True for {label}")


def _require_nonnegative_whole_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_nonnegative_decimal(field_name, value)
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{field_name} must be a whole Decimal")
    return normalized.to_integral_value()


def _require_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite() or value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return value.quantize(QUANT)


def _require_decimal_string(field_name: str, value: object) -> Decimal:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a Decimal-derived string")
    try:
        return _require_nonnegative_decimal(field_name, Decimal(value))
    except ArithmeticError as exc:
        raise ValueError(f"{field_name} must be a Decimal-derived string") from exc


def _require_digest(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if len(value) != 64 or any(character not in "0123456789abcdef" for character in value):
        raise ValueError(f"{field_name} must be a sha256 hex digest")
    return value


def _require_public_text(field_name: str, value: object) -> None:
    if type(value) is not str or not value:
        raise ValueError(f"{field_name} must be public text")
    lowered = value.lower()
    if any(token in lowered for token in UNSAFE_PUBLIC_TEXT_TOKENS):
        raise ValueError(f"unsafe public text in {field_name}")


def _reject_unsafe_public_values(value: object) -> None:
    if isinstance(value, Mapping):
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("public payload keys must be strings")
            lowered_key = key.lower()
            if any(fragment in lowered_key for fragment in UNSAFE_PUBLIC_KEY_FRAGMENTS):
                raise ValueError(f"unsafe public payload key: {key}")
            _reject_unsafe_public_values(item)
        return
    if isinstance(value, (list, tuple)):
        for item in value:
            _reject_unsafe_public_values(item)
        return
    if type(value) is str:
        lowered = value.lower()
        if any(token in lowered for token in UNSAFE_PUBLIC_TEXT_TOKENS):
            raise ValueError("unsafe public payload text")
