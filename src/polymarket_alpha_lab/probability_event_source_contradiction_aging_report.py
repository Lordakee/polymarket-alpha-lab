"""Pure readonly aging report for unresolved probability-event source contradictions."""

from __future__ import annotations

from dataclasses import asdict, dataclass, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal, ROUND_HALF_UP
from hashlib import sha256
import json
from typing import Any


DEFAULT_PROBABILITY_EVENT_SOURCE_CONTRADICTION_AGING_CONFIG_VERSION = (
    "probability-event-source-contradiction-aging-report-v0"
)

_QUANT = Decimal("0.000001")
_ZERO = Decimal("0.000000")
_STATUSES = ("pass", "watch", "block")
_REASON_CODES = (
    "no_unresolved_contradictions",
    "unresolved_contradictions_present",
    "contradiction_age_block",
    "contradiction_age_watch",
    "official_anchor_stale",
    "manual_owner_missing",
    "market_close_urgent",
)
_PASS_STEP = "continue_probability_event_source_monitoring"
_OWNER_STEP = "assign_manual_owner_and_recheck_sources"
_REVIEW_STEP = "continue_owner_review_of_aging_contradictions"
_ESCALATE_STEP = "escalate_stale_contradiction_before_market_close"


@dataclass(frozen=True)
class ProbabilityEventSourceContradictionAgingConfig:
    config_version: str = DEFAULT_PROBABILITY_EVENT_SOURCE_CONTRADICTION_AGING_CONFIG_VERSION
    watch_contradiction_age_hours: Decimal = Decimal("24.000000")
    block_contradiction_age_hours: Decimal = Decimal("72.000000")
    official_anchor_stale_hours: Decimal = Decimal("48.000000")
    market_close_urgent_hours: Decimal = Decimal("12.000000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_public_text("config_version", self.config_version)
        for field_name in (
            "watch_contradiction_age_hours",
            "block_contradiction_age_hours",
            "official_anchor_stale_hours",
            "market_close_urgent_hours",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_positive_decimal(field_name, getattr(self, field_name)),
            )
        if self.block_contradiction_age_hours < self.watch_contradiction_age_hours:
            raise ValueError(
                "block_contradiction_age_hours must be at least watch_contradiction_age_hours",
            )
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class ProbabilityEventSourceContradictionAgingInput:
    unresolved_contradiction_count: Decimal
    oldest_contradiction_age_hours: Decimal
    official_anchor_age_hours: Decimal
    manual_owner_present: bool
    market_close_hours: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        for field_name in (
            "unresolved_contradiction_count",
            "oldest_contradiction_age_hours",
            "official_anchor_age_hours",
            "market_close_hours",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        _require_bool("manual_owner_present", self.manual_owner_present)
        _require_hard_flags("input", self)


@dataclass(frozen=True)
class ProbabilityEventSourceContradictionAgingReport:
    generated_at: datetime
    config_version: str
    unresolved_contradiction_count: Decimal
    oldest_contradiction_age_hours: Decimal
    official_anchor_age_hours: Decimal
    manual_owner_present: bool
    market_close_hours: Decimal
    contradiction_aging_status: str
    reason_codes: tuple[str, ...]
    manual_next_step: str
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_text("config_version", self.config_version)
        for field_name in (
            "unresolved_contradiction_count",
            "oldest_contradiction_age_hours",
            "official_anchor_age_hours",
            "market_close_hours",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        _require_bool("manual_owner_present", self.manual_owner_present)
        _require_status("contradiction_aging_status", self.contradiction_aging_status)
        object.__setattr__(self, "reason_codes", _normalize_reason_codes(self.reason_codes))
        _require_manual_next_step("manual_next_step", self.manual_next_step)
        _require_hard_flags("report", self)
        _require_or_set_digest(self)

    @property
    def payload(self) -> dict[str, Any]:
        return probability_event_source_contradiction_aging_report_payload(self)


def build_probability_event_source_contradiction_aging_report(
    source: ProbabilityEventSourceContradictionAgingInput,
    *,
    config: ProbabilityEventSourceContradictionAgingConfig,
    generated_at: datetime,
) -> ProbabilityEventSourceContradictionAgingReport:
    if type(source) is not ProbabilityEventSourceContradictionAgingInput:
        raise ValueError("source must be a ProbabilityEventSourceContradictionAgingInput")
    if type(config) is not ProbabilityEventSourceContradictionAgingConfig:
        raise ValueError("config must be a ProbabilityEventSourceContradictionAgingConfig")
    _require_hard_flags("source", source)
    _require_hard_flags("config", config)
    reason_codes = _reason_codes(source, config=config)
    return ProbabilityEventSourceContradictionAgingReport(
        generated_at=_as_utc("generated_at", generated_at),
        config_version=config.config_version,
        unresolved_contradiction_count=source.unresolved_contradiction_count,
        oldest_contradiction_age_hours=source.oldest_contradiction_age_hours,
        official_anchor_age_hours=source.official_anchor_age_hours,
        manual_owner_present=source.manual_owner_present,
        market_close_hours=source.market_close_hours,
        contradiction_aging_status=_status(reason_codes),
        reason_codes=reason_codes,
        manual_next_step=_manual_next_step(reason_codes),
    )


def probability_event_source_contradiction_aging_report_payload(
    report: ProbabilityEventSourceContradictionAgingReport | dict[str, Any],
) -> dict[str, Any]:
    if type(report) is ProbabilityEventSourceContradictionAgingReport:
        _require_hard_flags("report", report)
        payload = _json_ready(report)
    elif type(report) is dict:
        payload = _json_ready(report)
    else:
        raise ValueError("report must be a ProbabilityEventSourceContradictionAgingReport")
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    _reject_public_numerics(payload)
    _require_hard_flags("payload", _DictFlags(payload))
    _verify_digest(payload)
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


def _reason_codes(
    source: ProbabilityEventSourceContradictionAgingInput,
    *,
    config: ProbabilityEventSourceContradictionAgingConfig,
) -> tuple[str, ...]:
    if source.unresolved_contradiction_count == _ZERO:
        return ("no_unresolved_contradictions",)
    reasons = ["unresolved_contradictions_present"]
    if source.oldest_contradiction_age_hours >= config.block_contradiction_age_hours:
        reasons.append("contradiction_age_block")
    elif source.oldest_contradiction_age_hours >= config.watch_contradiction_age_hours:
        reasons.append("contradiction_age_watch")
    if source.official_anchor_age_hours >= config.official_anchor_stale_hours:
        reasons.append("official_anchor_stale")
    if not source.manual_owner_present:
        reasons.append("manual_owner_missing")
    if source.market_close_hours <= config.market_close_urgent_hours:
        reasons.append("market_close_urgent")
    return tuple(reason for reason in _REASON_CODES if reason in reasons)


def _status(reason_codes: tuple[str, ...]) -> str:
    if "contradiction_age_block" in reason_codes or (
        "official_anchor_stale" in reason_codes and "market_close_urgent" in reason_codes
    ):
        return "block"
    if reason_codes == ("no_unresolved_contradictions",):
        return "pass"
    return "watch"


def _manual_next_step(reason_codes: tuple[str, ...]) -> str:
    if reason_codes == ("no_unresolved_contradictions",):
        return _PASS_STEP
    if "contradiction_age_block" in reason_codes or (
        "official_anchor_stale" in reason_codes and "market_close_urgent" in reason_codes
    ):
        return _ESCALATE_STEP
    if "manual_owner_missing" in reason_codes:
        return _OWNER_STEP
    return _REVIEW_STEP


def _require_or_set_digest(report: ProbabilityEventSourceContradictionAgingReport) -> None:
    if type(report.derived_validation_digest) is not str:
        raise ValueError("derived_validation_digest must be a string")
    expected = _report_digest(report)
    if report.derived_validation_digest == "":
        object.__setattr__(report, "derived_validation_digest", expected)
        return
    if report.derived_validation_digest != expected:
        raise ValueError("derived_validation_digest does not match public payload")


def _report_digest(report: ProbabilityEventSourceContradictionAgingReport) -> str:
    payload = _json_ready(report)
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    payload.pop("derived_validation_digest", None)
    return _canonical_digest(payload)


def _verify_digest(payload: dict[str, Any]) -> None:
    digest = payload.get("derived_validation_digest")
    if type(digest) is not str:
        raise ValueError("derived_validation_digest must be a string")
    unsigned = dict(payload)
    unsigned.pop("derived_validation_digest", None)
    if digest != _canonical_digest(unsigned):
        raise ValueError("derived_validation_digest does not match public payload")


def _canonical_digest(payload: dict[str, Any]) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    return sha256(encoded).hexdigest()


def _json_ready(value: Any) -> Any:
    if value is None:
        return None
    if is_dataclass(value) and not isinstance(value, type):
        return _json_ready(asdict(value))
    if type(value) is Decimal:
        if not value.is_finite():
            raise ValueError("JSON Decimal value must be finite")
        return str(value)
    if isinstance(value, Decimal):
        raise ValueError("JSON Decimal value must be a Decimal")
    if type(value) is datetime:
        return _as_utc("JSON datetime value", value).isoformat()
    if isinstance(value, datetime):
        raise ValueError("JSON datetime value must be a datetime")
    if type(value) is bool:
        return value
    if type(value) in (float, int):
        raise ValueError("JSON numeric value must use Decimal")
    if type(value) is str:
        return value
    if isinstance(value, dict):
        ready: dict[str, Any] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            ready[key] = _json_ready(item)
        return ready
    if isinstance(value, (list, tuple)):
        return [_json_ready(item) for item in value]
    raise ValueError("value is not JSON serializable")


def _require_hard_flags(label: str, value: object) -> None:
    if getattr(value, "paper_only", None) is not True:
        raise ValueError(f"paper_only must be True for {label}")
    if getattr(value, "report_only", None) is not True:
        raise ValueError(f"report_only must be True for {label}")
    if getattr(value, "readonly", None) is not True:
        raise ValueError(f"readonly must be True for {label}")


def _require_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    if value < _ZERO:
        raise ValueError(f"{field_name} must be non-negative")
    return value.quantize(_QUANT, rounding=ROUND_HALF_UP)


def _require_positive_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_nonnegative_decimal(field_name, value)
    if normalized <= _ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _require_bool(field_name: str, value: object) -> None:
    if type(value) is not bool:
        raise ValueError(f"{field_name} must be a bool")


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_public_text(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")


def _require_status(field_name: str, value: object) -> None:
    _require_public_text(field_name, value)
    if value not in _STATUSES:
        raise ValueError(f"{field_name} must be pass, watch, or block")


def _require_manual_next_step(field_name: str, value: object) -> None:
    _require_public_text(field_name, value)
    if value not in (_PASS_STEP, _OWNER_STEP, _REVIEW_STEP, _ESCALATE_STEP):
        raise ValueError(f"{field_name} must be a known manual next step")


def _normalize_reason_codes(value: object) -> tuple[str, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("reason_codes must be a list or tuple")
    reason_codes = tuple(value)
    if not reason_codes:
        raise ValueError("reason_codes must not be empty")
    previous_index = -1
    seen: set[str] = set()
    for reason_code in reason_codes:
        _require_public_text("reason_code", reason_code)
        if reason_code not in _REASON_CODES:
            raise ValueError("reason_code must be known")
        index = _REASON_CODES.index(reason_code)
        if reason_code in seen:
            raise ValueError("reason_codes must be unique")
        if index <= previous_index:
            raise ValueError("reason_codes must follow deterministic sequence")
        previous_index = index
        seen.add(reason_code)
    return reason_codes


def _reject_public_numerics(value: object) -> None:
    if type(value) in (int, float, Decimal):
        raise ValueError("public payload numeric values must be strings")
    if isinstance(value, dict):
        for item in value.values():
            _reject_public_numerics(item)
    elif isinstance(value, list):
        for item in value:
            _reject_public_numerics(item)


__all__ = (
    "DEFAULT_PROBABILITY_EVENT_SOURCE_CONTRADICTION_AGING_CONFIG_VERSION",
    "ProbabilityEventSourceContradictionAgingConfig",
    "ProbabilityEventSourceContradictionAgingInput",
    "ProbabilityEventSourceContradictionAgingReport",
    "build_probability_event_source_contradiction_aging_report",
    "probability_event_source_contradiction_aging_report_payload",
)
