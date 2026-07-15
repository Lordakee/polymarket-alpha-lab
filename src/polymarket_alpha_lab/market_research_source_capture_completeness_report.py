"""Pure read-only market research source capture completeness report."""

from __future__ import annotations

from dataclasses import asdict, dataclass, fields, is_dataclass
from decimal import Decimal
from hashlib import sha256
import json
from typing import Any


CAPTURE_STATUSES = ("complete", "attention", "blocked")
_COUNT_ZERO = Decimal("0")
_DIGEST_FIELD = "payload_digest"
_DECIMAL_FIELD_NAMES = (
    "source_count",
    "captured_snapshot_count",
    "missing_digest_count",
    "official_source_count",
    "minimum_required_sources",
)
_PUBLIC_PAYLOAD_KEYS = frozenset(
    (
        *_DECIMAL_FIELD_NAMES,
        "capture_status",
        "reason_codes",
        "manual_next_step",
        "paper_only",
        "report_only",
        "readonly",
        _DIGEST_FIELD,
    ),
)
_UNSAFE_PUBLIC_FIELD_FRAGMENTS = (
    "".join(("li", "ve")),
    "".join(("au", "th")),
    "".join(("wall", "et")),
    "".join(("or", "der")),
    "".join(("ke", "ys")),
    "".join(("sign", "ature")),
    "".join(("exec", "ute")),
    "".join(("execu", "tion")),
    "".join(("private",)),
    "".join(("secret",)),
    "".join(("token",)),
    "".join(("url",)),
    "".join(("path",)),
)


__all__ = (
    "CAPTURE_STATUSES",
    "MarketResearchSourceCaptureCompletenessReport",
    "build_market_research_source_capture_completeness_report",
    "market_research_source_capture_completeness_report_payload",
    "validate_market_research_source_capture_completeness_report_payload",
)


@dataclass(frozen=True)
class MarketResearchSourceCaptureCompletenessReport:
    source_count: Decimal
    captured_snapshot_count: Decimal
    missing_digest_count: Decimal
    official_source_count: Decimal
    minimum_required_sources: Decimal
    capture_status: str
    reason_codes: tuple[str, ...]
    manual_next_step: str
    payload_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "MarketResearchSourceCaptureCompletenessReport does not support subclassing",
        )

    def __post_init__(self) -> None:
        for field_name in _DECIMAL_FIELD_NAMES:
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        _validate_count_consistency(self)
        _require_capture_status("capture_status", self.capture_status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes),
        )
        _require_public_text("manual_next_step", self.manual_next_step)
        _require_hard_flags("report", self)
        _reject_unsafe_public_surface("report", self)
        if self.payload_digest == "":
            object.__setattr__(self, _DIGEST_FIELD, _payload_digest_for_report(self))
        else:
            _require_payload_digest(_DIGEST_FIELD, self.payload_digest)
            if self.payload_digest != _payload_digest_for_report(self):
                raise ValueError("payload_digest must match public payload")

    @property
    def public_payload(self) -> dict[str, Any]:
        return market_research_source_capture_completeness_report_payload(self)


def build_market_research_source_capture_completeness_report(
    *,
    source_count: Decimal,
    captured_snapshot_count: Decimal,
    missing_digest_count: Decimal,
    official_source_count: Decimal,
    minimum_required_sources: Decimal,
) -> MarketResearchSourceCaptureCompletenessReport:
    normalized_source_count = _require_nonnegative_decimal("source_count", source_count)
    normalized_captured_snapshot_count = _require_nonnegative_decimal(
        "captured_snapshot_count",
        captured_snapshot_count,
    )
    normalized_missing_digest_count = _require_nonnegative_decimal(
        "missing_digest_count",
        missing_digest_count,
    )
    normalized_official_source_count = _require_nonnegative_decimal(
        "official_source_count",
        official_source_count,
    )
    normalized_minimum_required_sources = _require_nonnegative_decimal(
        "minimum_required_sources",
        minimum_required_sources,
    )

    report_seed = _CaptureCompletenessSeed(
        source_count=normalized_source_count,
        captured_snapshot_count=normalized_captured_snapshot_count,
        missing_digest_count=normalized_missing_digest_count,
        official_source_count=normalized_official_source_count,
        minimum_required_sources=normalized_minimum_required_sources,
    )
    _validate_seed_consistency(report_seed)
    capture_status = _capture_status(report_seed)
    return MarketResearchSourceCaptureCompletenessReport(
        source_count=normalized_source_count,
        captured_snapshot_count=normalized_captured_snapshot_count,
        missing_digest_count=normalized_missing_digest_count,
        official_source_count=normalized_official_source_count,
        minimum_required_sources=normalized_minimum_required_sources,
        capture_status=capture_status,
        reason_codes=_reason_codes(report_seed, capture_status),
        manual_next_step=_manual_next_step(capture_status, report_seed),
    )


def market_research_source_capture_completeness_report_payload(
    report: MarketResearchSourceCaptureCompletenessReport,
) -> dict[str, Any]:
    if type(report) is not MarketResearchSourceCaptureCompletenessReport:
        raise ValueError(
            "report must be a MarketResearchSourceCaptureCompletenessReport",
        )
    _require_hard_flags("report", report)
    _reject_unsafe_public_surface("report", report)
    if report.payload_digest != _payload_digest_for_report(report):
        raise ValueError("payload_digest must match public payload")
    payload = _json_ready(report)
    if type(payload) is not dict:
        raise ValueError("public payload must be a JSON object")
    validate_market_research_source_capture_completeness_report_payload(payload)
    return payload


def validate_market_research_source_capture_completeness_report_payload(
    payload: object,
) -> bool:
    if type(payload) is not dict:
        raise ValueError("public payload must be a JSON object")
    _reject_unsafe_public_surface("public payload", payload)
    unknown_fields = set(payload) - _PUBLIC_PAYLOAD_KEYS
    if unknown_fields:
        unknown_field = sorted(unknown_fields)[0]
        raise ValueError(f"unknown public field: {unknown_field}")
    missing_fields = _PUBLIC_PAYLOAD_KEYS - set(payload)
    if missing_fields:
        missing_field = sorted(missing_fields)[0]
        raise ValueError(f"missing public field: {missing_field}")
    for field_name in _DECIMAL_FIELD_NAMES:
        _require_decimal_string(field_name, payload[field_name])
    _require_capture_status("capture_status", payload["capture_status"])
    _validate_public_reason_codes(payload["reason_codes"])
    _require_public_text("manual_next_step", payload["manual_next_step"])
    _require_hard_flags("payload", _PayloadFlags(payload))
    _require_payload_digest(_DIGEST_FIELD, payload[_DIGEST_FIELD])
    unsigned_payload = dict(payload)
    unsigned_payload.pop(_DIGEST_FIELD, None)
    if payload[_DIGEST_FIELD] != _digest_payload(unsigned_payload):
        raise ValueError("payload_digest must match public payload")
    return True


@dataclass(frozen=True)
class _CaptureCompletenessSeed:
    source_count: Decimal
    captured_snapshot_count: Decimal
    missing_digest_count: Decimal
    official_source_count: Decimal
    minimum_required_sources: Decimal


@dataclass(frozen=True)
class _PayloadFlags:
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


def _capture_status(seed: _CaptureCompletenessSeed) -> str:
    if (
        seed.source_count < seed.minimum_required_sources
        or seed.official_source_count == _COUNT_ZERO
    ):
        return "blocked"
    if (
        seed.captured_snapshot_count < seed.source_count
        or seed.missing_digest_count > _COUNT_ZERO
    ):
        return "attention"
    return "complete"


def _reason_codes(seed: _CaptureCompletenessSeed, capture_status: str) -> tuple[str, ...]:
    if capture_status == "complete":
        return (
            "source_capture_complete",
            "source_capture_minimum_sources_met",
            "source_capture_official_source_present",
        )

    reason_codes: list[str] = []
    if seed.source_count < seed.minimum_required_sources:
        reason_codes.append("source_capture_minimum_sources_unmet")
    if seed.official_source_count == _COUNT_ZERO:
        reason_codes.append("source_capture_no_official_source")
    if seed.missing_digest_count > _COUNT_ZERO:
        reason_codes.append("source_capture_missing_digests")
    if seed.captured_snapshot_count < seed.source_count:
        reason_codes.append("source_capture_snapshot_gap")
    return tuple(reason_codes)


def _manual_next_step(capture_status: str, seed: _CaptureCompletenessSeed) -> str:
    if capture_status == "complete":
        return "No manual follow-up required."
    if (
        seed.source_count < seed.minimum_required_sources
        or seed.official_source_count == _COUNT_ZERO
    ):
        return "Add official sources and meet the minimum source requirement before review."
    return "Re-capture missing source snapshots and regenerate absent digests before review."


def _require_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    if value < _COUNT_ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    if value != value.to_integral_value():
        raise ValueError(f"{field_name} must be a whole-number Decimal")
    return value


def _validate_seed_consistency(seed: _CaptureCompletenessSeed) -> None:
    if seed.captured_snapshot_count > seed.source_count:
        raise ValueError("captured_snapshot_count must not exceed source_count")
    if seed.missing_digest_count > seed.source_count:
        raise ValueError("missing_digest_count must not exceed source_count")
    if seed.official_source_count > seed.source_count:
        raise ValueError("official_source_count must not exceed source_count")


def _validate_count_consistency(
    report: MarketResearchSourceCaptureCompletenessReport,
) -> None:
    _validate_seed_consistency(
        _CaptureCompletenessSeed(
            source_count=report.source_count,
            captured_snapshot_count=report.captured_snapshot_count,
            missing_digest_count=report.missing_digest_count,
            official_source_count=report.official_source_count,
            minimum_required_sources=report.minimum_required_sources,
        ),
    )


def _require_capture_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in CAPTURE_STATUSES:
        raise ValueError(f"{field_name} must be complete, attention, or blocked")


def _normalize_reason_codes(value: object) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ValueError("reason_codes must be a tuple")
    if not value:
        raise ValueError("reason_codes must not be empty")
    normalized: list[str] = []
    seen: set[str] = set()
    for item in value:
        _require_public_text("reason_code", item)
        if item in seen:
            raise ValueError("reason_codes must be unique")
        seen.add(item)
        normalized.append(item)
    return tuple(normalized)


def _validate_public_reason_codes(value: object) -> None:
    if type(value) is not list:
        raise ValueError("reason_codes must be a list")
    if not value:
        raise ValueError("reason_codes must not be empty")
    seen: set[str] = set()
    for item in value:
        _require_public_text("reason_code", item)
        if item in seen:
            raise ValueError("reason_codes must be unique")
        seen.add(item)


def _require_public_text(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a non-empty canonical string")
    _reject_unsafe_public_text(field_name, value)


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if getattr(value, field_name, None) is not True:
            raise ValueError(f"{field_name} must be True for {label}")


def _require_payload_digest(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if len(value) != 64 or any(character not in "0123456789abcdef" for character in value):
        raise ValueError(f"{field_name} must be a lowercase sha256 hex digest")


def _require_decimal_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a Decimal string")
    try:
        parsed = Decimal(value)
    except Exception as exc:
        raise ValueError(f"{field_name} must be a Decimal string") from exc
    if not parsed.is_finite() or parsed < _COUNT_ZERO:
        raise ValueError(f"{field_name} must be a nonnegative Decimal string")
    if parsed != parsed.to_integral_value():
        raise ValueError(f"{field_name} must be a whole-number Decimal string")
    if str(parsed) != value:
        raise ValueError(f"{field_name} must be a canonical Decimal string")


def _payload_digest_for_report(
    report: MarketResearchSourceCaptureCompletenessReport,
) -> str:
    payload = _json_ready_without_digest(report)
    if type(payload) is not dict:
        raise ValueError("public payload must be a JSON object")
    return _digest_payload(payload)


def _digest_payload(payload: dict[str, Any]) -> str:
    canonical = json.dumps(
        payload,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    )
    return sha256(canonical.encode("utf-8")).hexdigest()


def _json_ready_without_digest(value: object) -> object:
    payload = _json_ready(value)
    if type(payload) is dict:
        payload.pop(_DIGEST_FIELD, None)
    return payload


def _json_ready(value: object) -> object:
    if is_dataclass(value) and not isinstance(value, type):
        return _json_ready(asdict(value))
    if type(value) is Decimal:
        if not value.is_finite():
            raise ValueError("JSON Decimal value must be finite")
        return str(value)
    if isinstance(value, Decimal):
        raise ValueError("JSON Decimal value must be an exact Decimal")
    if type(value) is dict:
        ready: dict[str, Any] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object field names must be strings")
            ready[key] = _json_ready(item)
        return ready
    if type(value) in (list, tuple):
        return [_json_ready(item) for item in value]
    if type(value) in (str, bool):
        return value
    if value is None:
        return None
    if isinstance(value, float) or type(value) is int:
        raise ValueError("JSON numeric values must use Decimal-derived strings")
    raise ValueError("value is not JSON serializable")


def _reject_unsafe_public_surface(label: str, value: object) -> None:
    if is_dataclass(value) and not isinstance(value, type):
        _reject_unsafe_public_surface(label, asdict(value))
        return
    if type(value) is dict:
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("public payload field names must be strings")
            normalized_key = key.lower()
            if any(fragment in normalized_key for fragment in _UNSAFE_PUBLIC_FIELD_FRAGMENTS):
                raise ValueError(f"unsafe public field in {label}: {key}")
            _reject_unsafe_public_surface(label, item)
        return
    if type(value) in (list, tuple):
        for item in value:
            _reject_unsafe_public_surface(label, item)
        return
    if type(value) is str:
        _reject_unsafe_public_text(label, value)


def _reject_unsafe_public_text(label: str, value: str) -> None:
    normalized = value.lower()
    if any(fragment in normalized for fragment in _UNSAFE_PUBLIC_FIELD_FRAGMENTS):
        raise ValueError(f"unsafe public value in {label}")


def _report_field_names() -> frozenset[str]:
    return frozenset(field.name for field in fields(MarketResearchSourceCaptureCompletenessReport))
