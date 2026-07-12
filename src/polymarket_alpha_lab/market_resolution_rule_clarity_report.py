"""Read-only resolution rule clarity report for probability event screening."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from decimal import Decimal, ROUND_HALF_UP
import hashlib
import json
import re
from typing import Any, Mapping


SIX_PLACES = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
STALE_RULE_CHECK_AGE_SECONDS = Decimal("86400.000000")
_DIGEST_RE = re.compile(r"^[0-9a-f]{64}$")

BLOCKED_REASON_CODES = (
    "rule_text_missing",
    "official_resolution_source_missing",
    "ambiguous_clauses_present",
    "conflicting_rule_signals_present",
    "manual_review_required",
    "source_payload_not_redacted",
)
ATTENTION_REASON_CODES = ("rule_check_stale",)
_ALL_REASON_CODES = frozenset((*BLOCKED_REASON_CODES, *ATTENTION_REASON_CODES))

_PUBLIC_PAYLOAD_FIELDS = (
    "rule_clarity_ready",
    "clarity_score",
    "blocked_reason_codes",
    "attention_reason_codes",
    "ready_ratio",
    "paper_only",
    "report_only",
    "readonly",
    "digest",
)
_UNSAFE_PUBLIC_FRAGMENTS = (
    "raw",
    "question",
    "source_url",
    "wallet",
    "auth",
    "order",
    "trade",
    "token",
    "private",
    "live",
)


@dataclass(frozen=True)
class MarketResolutionRuleClarityInput:
    rule_text_present: bool
    official_resolution_source_present: bool
    ambiguous_clause_count: Decimal
    conflicting_rule_signal_count: Decimal
    last_rule_check_age_seconds: Decimal
    manual_review_required: bool
    source_payload_redacted: bool
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketResolutionRuleClarityInput:
            raise TypeError("MarketResolutionRuleClarityInput does not support subclassing")

    def __post_init__(self) -> None:
        if type(self) is not MarketResolutionRuleClarityInput:
            raise ValueError("input must be exactly MarketResolutionRuleClarityInput")
        for field_name in (
            "rule_text_present",
            "official_resolution_source_present",
            "manual_review_required",
            "source_payload_redacted",
        ):
            _require_bool(field_name, getattr(self, field_name))
        for field_name in (
            "ambiguous_clause_count",
            "conflicting_rule_signal_count",
        ):
            value = _require_nonnegative_decimal(field_name, getattr(self, field_name))
            _require_integral_decimal(field_name, value)
            object.__setattr__(self, field_name, value)
        object.__setattr__(
            self,
            "last_rule_check_age_seconds",
            _require_nonnegative_decimal(
                "last_rule_check_age_seconds",
                self.last_rule_check_age_seconds,
            ),
        )
        _require_hard_flags("input", self)


@dataclass(frozen=True)
class MarketResolutionRuleClarityReport:
    rule_clarity_ready: bool
    clarity_score: Decimal
    blocked_reason_codes: tuple[str, ...]
    attention_reason_codes: tuple[str, ...]
    ready_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True
    digest: str = ""

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketResolutionRuleClarityReport:
            raise TypeError("MarketResolutionRuleClarityReport does not support subclassing")

    def __post_init__(self) -> None:
        if type(self) is not MarketResolutionRuleClarityReport:
            raise ValueError("report must be exactly MarketResolutionRuleClarityReport")
        _require_bool("rule_clarity_ready", self.rule_clarity_ready)
        object.__setattr__(
            self,
            "clarity_score",
            _require_ratio_decimal("clarity_score", self.clarity_score),
        )
        object.__setattr__(
            self,
            "ready_ratio",
            _require_ratio_decimal("ready_ratio", self.ready_ratio),
        )
        object.__setattr__(
            self,
            "blocked_reason_codes",
            _normalize_reason_codes(
                "blocked_reason_codes",
                self.blocked_reason_codes,
                BLOCKED_REASON_CODES,
            ),
        )
        object.__setattr__(
            self,
            "attention_reason_codes",
            _normalize_reason_codes(
                "attention_reason_codes",
                self.attention_reason_codes,
                ATTENTION_REASON_CODES,
            ),
        )
        _require_hard_flags("report", self)
        _validate_report(self)
        if self.digest:
            _require_digest("digest", self.digest)
            if self.digest != _digest_for_report(self):
                raise ValueError("digest must match report fields")
        else:
            object.__setattr__(self, "digest", _digest_for_report(self))

    @property
    def public_payload(self) -> dict[str, Any]:
        return market_resolution_rule_clarity_report_payload(self)


def build_market_resolution_rule_clarity_report(
    input_row: MarketResolutionRuleClarityInput,
) -> MarketResolutionRuleClarityReport:
    if type(input_row) is not MarketResolutionRuleClarityInput:
        raise ValueError("input_row must be a MarketResolutionRuleClarityInput")
    _require_hard_flags("input_row", input_row)

    blocked_reason_codes = _blocked_reason_codes(input_row)
    attention_reason_codes = _attention_reason_codes(input_row)
    ready_checks = Decimal("5.000000") - Decimal(str(len(blocked_reason_codes)))
    ready_ratio = _ratio(max(ready_checks, ZERO) / Decimal("5.000000"))
    clarity_score = ZERO if blocked_reason_codes else ready_ratio

    return MarketResolutionRuleClarityReport(
        rule_clarity_ready=not blocked_reason_codes,
        clarity_score=clarity_score,
        blocked_reason_codes=blocked_reason_codes,
        attention_reason_codes=attention_reason_codes,
        ready_ratio=ready_ratio,
    )


def market_resolution_rule_clarity_report_payload(
    report: MarketResolutionRuleClarityReport | Mapping[str, Any],
) -> dict[str, Any]:
    if type(report) is MarketResolutionRuleClarityReport:
        _require_hard_flags("report", report)
        _validate_report(report)
        if "source_payload_not_redacted" in report.blocked_reason_codes:
            raise ValueError("source payload must be redacted before publication")
        if report.digest != _digest_for_report(report):
            raise ValueError("digest must match report fields")
        payload = _payload_from_report(report)
    elif type(report) is dict:
        payload = dict(report)
    else:
        raise ValueError("report must be a MarketResolutionRuleClarityReport or payload")

    _validate_public_payload(payload)
    _reject_unsafe_public_payload(payload)
    unsigned = dict(payload)
    digest = unsigned.pop("digest")
    if digest != _digest_for_payload(unsigned):
        raise ValueError("digest must match public payload")
    if "source_payload_not_redacted" in payload["blocked_reason_codes"]:
        raise ValueError("source payload must be redacted before publication")
    return payload


def _blocked_reason_codes(
    input_row: MarketResolutionRuleClarityInput,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    if not input_row.rule_text_present:
        reason_codes.append("rule_text_missing")
    if not input_row.official_resolution_source_present:
        reason_codes.append("official_resolution_source_missing")
    if input_row.ambiguous_clause_count > ZERO:
        reason_codes.append("ambiguous_clauses_present")
    if input_row.conflicting_rule_signal_count > ZERO:
        reason_codes.append("conflicting_rule_signals_present")
    if input_row.manual_review_required:
        reason_codes.append("manual_review_required")
    if not input_row.source_payload_redacted:
        reason_codes.append("source_payload_not_redacted")
    return tuple(reason_codes)


def _attention_reason_codes(
    input_row: MarketResolutionRuleClarityInput,
) -> tuple[str, ...]:
    if input_row.last_rule_check_age_seconds > STALE_RULE_CHECK_AGE_SECONDS:
        return ("rule_check_stale",)
    return ()


def _payload_from_report(report: MarketResolutionRuleClarityReport) -> dict[str, Any]:
    return {
        "rule_clarity_ready": report.rule_clarity_ready,
        "clarity_score": _decimal_string(report.clarity_score),
        "blocked_reason_codes": list(report.blocked_reason_codes),
        "attention_reason_codes": list(report.attention_reason_codes),
        "ready_ratio": _decimal_string(report.ready_ratio),
        "paper_only": report.paper_only,
        "report_only": report.report_only,
        "readonly": report.readonly,
        "digest": report.digest,
    }


def _validate_report(report: MarketResolutionRuleClarityReport) -> None:
    if report.rule_clarity_ready != (not report.blocked_reason_codes):
        raise ValueError("rule_clarity_ready must match blocked reason codes")
    ready_checks = Decimal("5.000000") - Decimal(str(len(report.blocked_reason_codes)))
    expected_ready_ratio = _ratio(max(ready_checks, ZERO) / Decimal("5.000000"))
    if report.ready_ratio != expected_ready_ratio:
        raise ValueError("ready_ratio must match blocked reason codes")
    expected_clarity_score = ZERO if report.blocked_reason_codes else ONE
    if report.clarity_score != expected_clarity_score:
        raise ValueError("clarity_score must match blocked reason codes")
    if set(report.blocked_reason_codes) - _ALL_REASON_CODES:
        raise ValueError("blocked_reason_codes contain unsupported values")
    if set(report.attention_reason_codes) - _ALL_REASON_CODES:
        raise ValueError("attention_reason_codes contain unsupported values")


def _validate_public_payload(payload: dict[str, Any]) -> None:
    if tuple(payload.keys()) != _PUBLIC_PAYLOAD_FIELDS:
        raise ValueError("public payload fields must match canonical schema")
    _require_bool("rule_clarity_ready", payload["rule_clarity_ready"])
    _require_bool("paper_only", payload["paper_only"])
    _require_bool("report_only", payload["report_only"])
    _require_bool("readonly", payload["readonly"])
    if payload["paper_only"] is not True:
        raise ValueError("paper_only must be True")
    if payload["report_only"] is not True:
        raise ValueError("report_only must be True")
    if payload["readonly"] is not True:
        raise ValueError("readonly must be True")
    for field_name in ("clarity_score", "ready_ratio"):
        if type(payload[field_name]) is not str:
            raise ValueError(f"{field_name} must be a canonical Decimal string")
        _require_canonical_decimal_string(field_name, payload[field_name])
    for field_name, allowed in (
        ("blocked_reason_codes", BLOCKED_REASON_CODES),
        ("attention_reason_codes", ATTENTION_REASON_CODES),
    ):
        if type(payload[field_name]) is not list:
            raise ValueError(f"{field_name} must be a list")
        _normalize_reason_codes(field_name, tuple(payload[field_name]), allowed)
    _require_digest("digest", payload["digest"])


def _digest_for_report(report: MarketResolutionRuleClarityReport) -> str:
    payload = _json_ready(asdict(report))
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    payload.pop("digest", None)
    return _digest_for_payload(payload)


def _digest_for_payload(payload: Mapping[str, Any]) -> str:
    canonical_payload = json.dumps(
        _json_ready(dict(payload)),
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    )
    return hashlib.sha256(canonical_payload.encode("utf-8")).hexdigest()


def _json_ready(value: object) -> object:
    if type(value) is Decimal:
        return _decimal_string(value)
    if type(value) is tuple:
        return [_json_ready(item) for item in value]
    if type(value) is list:
        return [_json_ready(item) for item in value]
    if type(value) is dict:
        return {str(key): _json_ready(item) for key, item in value.items()}
    return value


def _reject_unsafe_public_payload(payload: Mapping[str, Any]) -> None:
    public_text = json.dumps(
        _json_ready(dict(payload)),
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    ).lower()
    for fragment in _UNSAFE_PUBLIC_FRAGMENTS:
        if fragment in public_text:
            raise ValueError("unsafe public payload")


def _normalize_reason_codes(
    field_name: str,
    reason_codes: tuple[str, ...],
    allowed_reason_codes: tuple[str, ...],
) -> tuple[str, ...]:
    if type(reason_codes) is not tuple:
        raise ValueError(f"{field_name} must be a tuple")
    seen: set[str] = set()
    normalized: list[str] = []
    for reason_code in reason_codes:
        if type(reason_code) is not str:
            raise ValueError(f"{field_name} must contain strings")
        if reason_code not in allowed_reason_codes:
            raise ValueError(f"{field_name} contains unsupported reason code")
        if reason_code in seen:
            raise ValueError(f"{field_name} must be unique")
        seen.add(reason_code)
        normalized.append(reason_code)
    return tuple(
        reason_code for reason_code in allowed_reason_codes if reason_code in normalized
    )


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if getattr(value, field_name, None) is not True:
            raise ValueError(f"{label} {field_name} must be True")


def _require_bool(field_name: str, value: object) -> None:
    if type(value) is not bool:
        raise ValueError(f"{field_name} must be bool")


def _require_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be Decimal")
    normalized = value.quantize(SIX_PLACES, rounding=ROUND_HALF_UP)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _require_ratio_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_nonnegative_decimal(field_name, value)
    if normalized > ONE:
        raise ValueError(f"{field_name} must be <= 1")
    return normalized


def _require_integral_decimal(field_name: str, value: Decimal) -> None:
    if value != value.to_integral_value():
        raise ValueError(f"{field_name} must be integral")


def _require_canonical_decimal_string(field_name: str, value: str) -> Decimal:
    parsed = Decimal(value)
    if _decimal_string(parsed) != value:
        raise ValueError(f"{field_name} must be a canonical Decimal string")
    return parsed


def _require_digest(field_name: str, value: object) -> str:
    if type(value) is not str or not _DIGEST_RE.match(value):
        raise ValueError(f"{field_name} must be a sha256 hex digest")
    return value


def _ratio(value: Decimal) -> Decimal:
    if value < ZERO:
        value = ZERO
    if value > ONE:
        value = ONE
    return value.quantize(SIX_PLACES, rounding=ROUND_HALF_UP)


def _decimal_string(value: Decimal) -> str:
    return f"{value.quantize(SIX_PLACES, rounding=ROUND_HALF_UP):f}"


__all__ = (
    "ATTENTION_REASON_CODES",
    "BLOCKED_REASON_CODES",
    "MarketResolutionRuleClarityInput",
    "MarketResolutionRuleClarityReport",
    "build_market_resolution_rule_clarity_report",
    "market_resolution_rule_clarity_report_payload",
)
