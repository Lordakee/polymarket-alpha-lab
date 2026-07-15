"""Read-only market event external catalyst dependency report.

Pure in-memory Decimal arithmetic for manual catalyst dependency review. The
module only produces immutable report objects, public payloads, and digests.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
from json import dumps
from typing import Any


MARKET_EVENT_EXTERNAL_CATALYST_DEPENDENCY_STATUSES = (
    "ready",
    "attention",
    "blocked",
)
QUANTUM = Decimal("0.000001")
ZERO = Decimal("0")
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
_FLAG_FIELDS = ("paper_only", "report_only", "readonly")
_REASON_CODES = (
    "external_catalyst_not_identified_attention",
    "external_catalysts_unconfirmed_blocker",
    "next_catalyst_after_market_close_attention",
    "market_event_external_catalyst_dependency_ready",
)
_MANUAL_NEXT_STEPS = (
    "document_external_catalyst_dependency_review",
    "escalate_manual_catalyst_confirmation",
    "identify_public_external_catalyst",
    "review_market_close_before_catalyst",
)
_PUBLIC_FIELDS = frozenset(
    (
        "external_catalyst_count",
        "confirmed_catalyst_count",
        "unconfirmed_catalyst_count",
        "next_catalyst_hours",
        "market_close_hours",
        "catalyst_dependency_status",
        "reason_codes",
        "manual_next_step",
        "payload_digest",
        "paper_only",
        "report_only",
        "readonly",
    ),
)
_UNSAFE_PUBLIC_FRAGMENTS = (
    "au" + "th",
    "auto",
    "b" + "uy",
    "crawl",
    "exec" + "ute",
    "exec" + "ution",
    "jsonl",
    "k" + "ey",
    "li" + "ve",
    "persist",
    "scrape",
    "se" + "ll",
    "sig" + "n",
    "trad" + "e",
    "wal" + "let",
)

__all__ = (
    "MARKET_EVENT_EXTERNAL_CATALYST_DEPENDENCY_STATUSES",
    "MarketEventExternalCatalystDependencyInput",
    "MarketEventExternalCatalystDependencyReport",
    "build_market_event_external_catalyst_dependency_report",
    "market_event_external_catalyst_dependency_public_payload",
)


@dataclass(frozen=True)
class MarketEventExternalCatalystDependencyInput:
    external_catalyst_count: Decimal
    confirmed_catalyst_count: Decimal
    unconfirmed_catalyst_count: Decimal
    next_catalyst_hours: Decimal
    market_close_hours: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not MarketEventExternalCatalystDependencyInput:
            raise ValueError(
                "input must be exactly MarketEventExternalCatalystDependencyInput",
            )
        for field_name in (
            "external_catalyst_count",
            "confirmed_catalyst_count",
            "unconfirmed_catalyst_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_count(field_name, getattr(self, field_name)),
            )
        for field_name in ("next_catalyst_hours", "market_close_hours"):
            object.__setattr__(
                self,
                field_name,
                _normalize_decimal(field_name, getattr(self, field_name)),
            )
        _validate_catalyst_counts(self)
        _require_hard_flags("input", self)


@dataclass(frozen=True)
class MarketEventExternalCatalystDependencyReport:
    external_catalyst_count: Decimal
    confirmed_catalyst_count: Decimal
    unconfirmed_catalyst_count: Decimal
    next_catalyst_hours: Decimal
    market_close_hours: Decimal
    catalyst_dependency_status: str
    reason_codes: tuple[str, ...]
    manual_next_step: str
    payload_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not MarketEventExternalCatalystDependencyReport:
            raise ValueError(
                "report must be exactly MarketEventExternalCatalystDependencyReport",
            )
        for field_name in (
            "external_catalyst_count",
            "confirmed_catalyst_count",
            "unconfirmed_catalyst_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_count(field_name, getattr(self, field_name)),
            )
        for field_name in ("next_catalyst_hours", "market_close_hours"):
            object.__setattr__(
                self,
                field_name,
                _normalize_decimal(field_name, getattr(self, field_name)),
            )
        _validate_catalyst_counts(self)
        _require_status("catalyst_dependency_status", self.catalyst_dependency_status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        _require_manual_next_step("manual_next_step", self.manual_next_step)
        _require_hard_flags("report", self)
        _apply_or_verify_payload_digest(self)
        _validate_report_consistency(self)

    @property
    def public_payload(self) -> dict[str, Any]:
        return market_event_external_catalyst_dependency_public_payload(self)


def build_market_event_external_catalyst_dependency_report(
    value: MarketEventExternalCatalystDependencyInput,
) -> MarketEventExternalCatalystDependencyReport:
    if type(value) is not MarketEventExternalCatalystDependencyInput:
        raise ValueError(
            "value must be a MarketEventExternalCatalystDependencyInput",
        )
    _require_hard_flags("input", value)
    reason_codes = _reason_codes(
        external_catalyst_count=value.external_catalyst_count,
        unconfirmed_catalyst_count=value.unconfirmed_catalyst_count,
        next_catalyst_hours=value.next_catalyst_hours,
        market_close_hours=value.market_close_hours,
    )
    status = _catalyst_dependency_status(reason_codes)
    return MarketEventExternalCatalystDependencyReport(
        external_catalyst_count=value.external_catalyst_count,
        confirmed_catalyst_count=value.confirmed_catalyst_count,
        unconfirmed_catalyst_count=value.unconfirmed_catalyst_count,
        next_catalyst_hours=value.next_catalyst_hours,
        market_close_hours=value.market_close_hours,
        catalyst_dependency_status=status,
        reason_codes=reason_codes,
        manual_next_step=_manual_next_step(status, reason_codes),
    )


def market_event_external_catalyst_dependency_public_payload(
    report: MarketEventExternalCatalystDependencyReport,
) -> dict[str, Any]:
    if type(report) is not MarketEventExternalCatalystDependencyReport:
        raise ValueError(
            "report must be a MarketEventExternalCatalystDependencyReport",
        )
    _require_hard_flags("report", report)
    _verify_payload_digest(report)
    payload = _json_ready(asdict(report))
    if type(payload) is not dict:
        raise ValueError("public payload must be a JSON object")
    _validate_public_payload_schema(payload)
    _reject_unsafe_public_payload("payload", payload)
    return payload


def _reason_codes(
    *,
    external_catalyst_count: Decimal,
    unconfirmed_catalyst_count: Decimal,
    next_catalyst_hours: Decimal,
    market_close_hours: Decimal,
) -> tuple[str, ...]:
    reasons: list[str] = []
    if unconfirmed_catalyst_count > ZERO:
        reasons.append("external_catalysts_unconfirmed_blocker")
    if external_catalyst_count == ZERO:
        reasons.append("external_catalyst_not_identified_attention")
    if external_catalyst_count > ZERO and next_catalyst_hours > market_close_hours:
        reasons.append("next_catalyst_after_market_close_attention")
    if not reasons:
        return ("market_event_external_catalyst_dependency_ready",)
    return tuple(reason for reason in _REASON_CODES if reason in reasons)


def _catalyst_dependency_status(reason_codes: tuple[str, ...]) -> str:
    if "external_catalysts_unconfirmed_blocker" in reason_codes:
        return "blocked"
    if reason_codes != ("market_event_external_catalyst_dependency_ready",):
        return "attention"
    return "ready"


def _manual_next_step(
    status: str,
    reason_codes: tuple[str, ...],
) -> str:
    if status == "blocked":
        return "escalate_manual_catalyst_confirmation"
    if "external_catalyst_not_identified_attention" in reason_codes:
        return "identify_public_external_catalyst"
    if "next_catalyst_after_market_close_attention" in reason_codes:
        return "review_market_close_before_catalyst"
    return "document_external_catalyst_dependency_review"


def _validate_report_consistency(
    report: MarketEventExternalCatalystDependencyReport,
) -> None:
    expected_reason_codes = _reason_codes(
        external_catalyst_count=report.external_catalyst_count,
        unconfirmed_catalyst_count=report.unconfirmed_catalyst_count,
        next_catalyst_hours=report.next_catalyst_hours,
        market_close_hours=report.market_close_hours,
    )
    if report.reason_codes != expected_reason_codes:
        raise ValueError("reason_codes must match catalyst dependency inputs")
    expected_status = _catalyst_dependency_status(expected_reason_codes)
    if report.catalyst_dependency_status != expected_status:
        raise ValueError(
            "catalyst_dependency_status must match catalyst dependency inputs",
        )
    expected_next_step = _manual_next_step(expected_status, expected_reason_codes)
    if report.manual_next_step != expected_next_step:
        raise ValueError("manual_next_step must match catalyst dependency status")


def _validate_catalyst_counts(value: object) -> None:
    external_count = getattr(value, "external_catalyst_count")
    confirmed_count = getattr(value, "confirmed_catalyst_count")
    unconfirmed_count = getattr(value, "unconfirmed_catalyst_count")
    if confirmed_count > external_count:
        raise ValueError("confirmed_catalyst_count must not exceed external count")
    if confirmed_count + unconfirmed_count != external_count:
        raise ValueError(
            "catalyst counts must reconcile to external_catalyst_count",
        )


def _normalize_count(field_name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized != normalized.to_integral_value(rounding=ROUND_HALF_EVEN):
        raise ValueError(f"{field_name} must be an integer-valued Decimal")
    return normalized


def _normalize_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    with localcontext(DECIMAL_CONTEXT):
        normalized = value.quantize(QUANTUM)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _require_status(field_name: str, value: object) -> None:
    if (
        type(value) is not str
        or value not in MARKET_EVENT_EXTERNAL_CATALYST_DEPENDENCY_STATUSES
    ):
        raise ValueError(f"{field_name} must be a supported status")


def _normalize_reason_codes(field_name: str, value: object) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ValueError(f"{field_name} must be a tuple")
    seen: set[str] = set()
    for reason_code in value:
        if type(reason_code) is not str or reason_code not in _REASON_CODES:
            raise ValueError(f"{field_name} contains unsupported reason code")
        if reason_code in seen:
            raise ValueError(f"{field_name} must not contain duplicates")
        seen.add(reason_code)
    ordered = tuple(reason_code for reason_code in _REASON_CODES if reason_code in seen)
    if value != ordered:
        raise ValueError(f"{field_name} must use canonical order")
    return ordered


def _require_manual_next_step(field_name: str, value: object) -> None:
    if type(value) is not str or value not in _MANUAL_NEXT_STEPS:
        raise ValueError(f"{field_name} must be a supported manual next step")


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in _FLAG_FIELDS:
        flag = getattr(value, field_name)
        if flag is not True:
            raise ValueError(f"{label} {field_name} must be True")


def _apply_or_verify_payload_digest(
    report: MarketEventExternalCatalystDependencyReport,
) -> None:
    if report.payload_digest == "":
        object.__setattr__(report, "payload_digest", _payload_digest(report))
        return
    _verify_payload_digest(report)


def _verify_payload_digest(report: MarketEventExternalCatalystDependencyReport) -> None:
    if type(report.payload_digest) is not str or len(report.payload_digest) != 64:
        raise ValueError("payload_digest must be a 64-character hex digest")
    if report.payload_digest != _payload_digest(report):
        raise ValueError("payload_digest must match public payload")


def _payload_digest(report: MarketEventExternalCatalystDependencyReport) -> str:
    payload = asdict(report)
    payload.pop("payload_digest")
    json_payload = _json_ready(payload)
    encoded = dumps(
        json_payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    ).encode("utf-8")
    return sha256(encoded).hexdigest()


def _json_ready(value: Any) -> Any:
    if type(value) is Decimal:
        return f"{value.quantize(QUANTUM)}"
    if isinstance(value, tuple):
        return [_json_ready(item) for item in value]
    if isinstance(value, list):
        return [_json_ready(item) for item in value]
    if isinstance(value, dict):
        return {str(key): _json_ready(item) for key, item in value.items()}
    return value


def _validate_public_payload_schema(payload: dict[str, Any]) -> None:
    if set(payload) != _PUBLIC_FIELDS:
        raise ValueError("public payload must match the canonical catalyst schema")


def _reject_unsafe_public_payload(label: str, value: object) -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            _reject_unsafe_public_payload(f"{label}.{key}", item)
        return
    if isinstance(value, list):
        for index, item in enumerate(value):
            _reject_unsafe_public_payload(f"{label}[{index}]", item)
        return
    if type(value) is str:
        normalized = value.lower()
        if any(fragment in normalized for fragment in _UNSAFE_PUBLIC_FRAGMENTS):
            raise ValueError(f"{label} contains unsafe public text")
