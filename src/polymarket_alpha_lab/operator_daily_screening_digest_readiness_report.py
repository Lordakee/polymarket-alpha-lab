"""Pure read-only operator daily screening digest readiness report."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from typing import Any


__all__ = (
    "OperatorDailyScreeningDigestReadinessInput",
    "OperatorDailyScreeningDigestReadinessReport",
    "build_operator_daily_screening_digest_readiness_report",
    "operator_daily_screening_digest_readiness_payload",
)


QUANTUM = Decimal("0.000001")
ZERO = Decimal("0.000000")
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)

READY_STATUS = "ready"
PENDING_STATUS = "pending"
BLOCKED_STATUS = "blocked"

READY_REASON = "operator_daily_screening_digest_ready"
NO_SCREENED_MARKETS_REASON = "operator_daily_screening_digest_no_screened_markets"
NO_CANDIDATES_REASON = "operator_daily_screening_digest_no_candidates"
ALL_CANDIDATES_BLOCKED_REASON = (
    "operator_daily_screening_digest_all_candidates_blocked"
)
READY_PACKET_MISSING_REASON = (
    "operator_daily_screening_digest_ready_packet_missing"
)
DIGEST_NOT_GENERATED_REASON = "operator_daily_screening_digest_not_generated"
WATCH_ITEMS_PRESENT_REASON = (
    "operator_daily_screening_digest_watch_items_present"
)

REASON_PRIORITY = (
    READY_REASON,
    NO_SCREENED_MARKETS_REASON,
    NO_CANDIDATES_REASON,
    ALL_CANDIDATES_BLOCKED_REASON,
    READY_PACKET_MISSING_REASON,
    DIGEST_NOT_GENERATED_REASON,
    WATCH_ITEMS_PRESENT_REASON,
)
STATUSES = (READY_STATUS, PENDING_STATUS, BLOCKED_STATUS)


class _FinalDataclass:
    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        for base in cls.__bases__:
            if base is not _FinalDataclass and issubclass(base, _FinalDataclass):
                raise TypeError(f"{base.__name__} may not be subclassed")


@dataclass(frozen=True)
class OperatorDailyScreeningDigestReadinessInput(_FinalDataclass):
    screened_market_count: Decimal
    candidate_count: Decimal
    blocked_count: Decimal
    watch_count: Decimal
    ready_packet_count: Decimal
    digest_generated: bool
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            OperatorDailyScreeningDigestReadinessInput,
            "screening digest input",
        )
        for field_name in (
            "screened_market_count",
            "candidate_count",
            "blocked_count",
            "watch_count",
            "ready_packet_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_count(field_name, getattr(self, field_name)),
            )
        _require_bool("digest_generated", self.digest_generated)
        _validate_input_counts(self)
        _require_hard_flags("screening digest input", self)


@dataclass(frozen=True)
class OperatorDailyScreeningDigestReadinessReport(_FinalDataclass):
    digest_status: str
    reason_codes: tuple[str, ...]
    manual_next_step: str
    screened_market_count: Decimal
    candidate_count: Decimal
    blocked_count: Decimal
    watch_count: Decimal
    ready_packet_count: Decimal
    digest_generated: bool
    payload_digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            OperatorDailyScreeningDigestReadinessReport,
            "screening digest report",
        )
        _require_status(self.digest_status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes),
        )
        _require_public_string("manual_next_step", self.manual_next_step)
        for field_name in (
            "screened_market_count",
            "candidate_count",
            "blocked_count",
            "watch_count",
            "ready_packet_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_count(field_name, getattr(self, field_name)),
            )
        _require_bool("digest_generated", self.digest_generated)
        _require_digest(self.payload_digest)
        _validate_report(self)
        _require_hard_flags("screening digest report", self)

    @property
    def public_payload(self) -> dict[str, object]:
        return operator_daily_screening_digest_readiness_payload(self)


def build_operator_daily_screening_digest_readiness_report(
    readiness_input: OperatorDailyScreeningDigestReadinessInput,
) -> OperatorDailyScreeningDigestReadinessReport:
    if type(readiness_input) is not OperatorDailyScreeningDigestReadinessInput:
        raise ValueError(
            "readiness_input must be an OperatorDailyScreeningDigestReadinessInput",
        )
    _require_hard_flags("screening digest input", readiness_input)
    _validate_input_counts(readiness_input)

    digest_status = _digest_status(readiness_input)
    reason_codes = _reason_codes(readiness_input, digest_status)
    manual_next_step = _manual_next_step(digest_status, reason_codes)
    pending_report = OperatorDailyScreeningDigestReadinessReport(
        digest_status=digest_status,
        reason_codes=reason_codes,
        manual_next_step=manual_next_step,
        screened_market_count=readiness_input.screened_market_count,
        candidate_count=readiness_input.candidate_count,
        blocked_count=readiness_input.blocked_count,
        watch_count=readiness_input.watch_count,
        ready_packet_count=readiness_input.ready_packet_count,
        digest_generated=readiness_input.digest_generated,
        payload_digest="pending",
        paper_only=readiness_input.paper_only,
        report_only=readiness_input.report_only,
        readonly=readiness_input.readonly,
    )
    return OperatorDailyScreeningDigestReadinessReport(
        digest_status=pending_report.digest_status,
        reason_codes=pending_report.reason_codes,
        manual_next_step=pending_report.manual_next_step,
        screened_market_count=pending_report.screened_market_count,
        candidate_count=pending_report.candidate_count,
        blocked_count=pending_report.blocked_count,
        watch_count=pending_report.watch_count,
        ready_packet_count=pending_report.ready_packet_count,
        digest_generated=pending_report.digest_generated,
        payload_digest=_payload_digest(pending_report),
        paper_only=pending_report.paper_only,
        report_only=pending_report.report_only,
        readonly=pending_report.readonly,
    )


def operator_daily_screening_digest_readiness_payload(
    report: OperatorDailyScreeningDigestReadinessReport,
) -> dict[str, object]:
    if type(report) is not OperatorDailyScreeningDigestReadinessReport:
        raise ValueError(
            "report must be an OperatorDailyScreeningDigestReadinessReport",
        )
    _require_hard_flags("screening digest report", report)
    _validate_report(report)
    expected_digest = _payload_digest(report)
    if report.payload_digest != expected_digest:
        raise ValueError("payload_digest does not match report payload")
    payload = _payload_for_digest(report)
    payload["payload_digest"] = expected_digest
    return payload


def _digest_status(
    readiness_input: OperatorDailyScreeningDigestReadinessInput,
) -> str:
    if (
        readiness_input.screened_market_count == ZERO
        or _all_candidates_blocked(readiness_input)
    ):
        return BLOCKED_STATUS
    if (
        readiness_input.ready_packet_count == ZERO
        or not readiness_input.digest_generated
        or readiness_input.watch_count > ZERO
    ):
        return PENDING_STATUS
    return READY_STATUS


def _reason_codes(
    readiness_input: OperatorDailyScreeningDigestReadinessInput,
    digest_status: str,
) -> tuple[str, ...]:
    if digest_status == READY_STATUS:
        return (READY_REASON,)

    reason_codes: list[str] = []
    if readiness_input.screened_market_count == ZERO:
        reason_codes.append(NO_SCREENED_MARKETS_REASON)
    if readiness_input.candidate_count == ZERO:
        reason_codes.append(NO_CANDIDATES_REASON)
    if _all_candidates_blocked(readiness_input):
        reason_codes.append(ALL_CANDIDATES_BLOCKED_REASON)
    if readiness_input.ready_packet_count == ZERO:
        reason_codes.append(READY_PACKET_MISSING_REASON)
    if not readiness_input.digest_generated:
        reason_codes.append(DIGEST_NOT_GENERATED_REASON)
    if readiness_input.watch_count > ZERO:
        reason_codes.append(WATCH_ITEMS_PRESENT_REASON)
    return _normalize_reason_codes(tuple(reason_codes))


def _manual_next_step(digest_status: str, reason_codes: tuple[str, ...]) -> str:
    if digest_status == READY_STATUS:
        return "review_daily_screening_digest"
    if NO_SCREENED_MARKETS_REASON in reason_codes or ALL_CANDIDATES_BLOCKED_REASON in reason_codes:
        return "complete_daily_screening_before_digest_review"
    if READY_PACKET_MISSING_REASON in reason_codes or DIGEST_NOT_GENERATED_REASON in reason_codes:
        return "prepare_ready_packet_then_generate_digest"
    return "review_watch_items_before_digest_review"


def _payload_for_digest(
    report: OperatorDailyScreeningDigestReadinessReport,
) -> dict[str, object]:
    return {
        "digest_status": report.digest_status,
        "reason_codes": list(report.reason_codes),
        "manual_next_step": report.manual_next_step,
        "screened_market_count": _decimal_text(report.screened_market_count),
        "candidate_count": _decimal_text(report.candidate_count),
        "blocked_count": _decimal_text(report.blocked_count),
        "watch_count": _decimal_text(report.watch_count),
        "ready_packet_count": _decimal_text(report.ready_packet_count),
        "digest_generated": report.digest_generated,
        "paper_only": report.paper_only,
        "report_only": report.report_only,
        "readonly": report.readonly,
    }


def _payload_digest(report: OperatorDailyScreeningDigestReadinessReport) -> str:
    encoded = json.dumps(
        _payload_for_digest(report),
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _validate_input_counts(
    readiness_input: OperatorDailyScreeningDigestReadinessInput,
) -> None:
    if readiness_input.candidate_count > readiness_input.screened_market_count:
        raise ValueError("candidate_count cannot exceed screened_market_count")
    if readiness_input.blocked_count + readiness_input.watch_count > readiness_input.candidate_count:
        raise ValueError(
            "blocked_count plus watch_count cannot exceed candidate_count",
        )
    if readiness_input.ready_packet_count > readiness_input.candidate_count:
        raise ValueError("ready_packet_count cannot exceed candidate_count")


def _validate_report(report: OperatorDailyScreeningDigestReadinessReport) -> None:
    _validate_input_counts(report)
    expected_status = _digest_status(report)
    if report.digest_status != expected_status:
        raise ValueError("digest_status must match screening counts")
    if report.reason_codes != _reason_codes(report, expected_status):
        raise ValueError("reason_codes must match screening counts")
    if report.manual_next_step != _manual_next_step(report.digest_status, report.reason_codes):
        raise ValueError("manual_next_step must match digest_status")


def _all_candidates_blocked(value: Any) -> bool:
    return value.candidate_count > ZERO and value.blocked_count == value.candidate_count


def _require_exact_type(value: object, expected_type: type[object], label: str) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{label} must be exactly {expected_type.__name__}")


def _require_bool(field_name: str, value: object) -> None:
    if type(value) is not bool:
        raise ValueError(f"{field_name} must be a bool")


def _require_status(value: object) -> None:
    if type(value) is not str or value not in STATUSES:
        raise ValueError("digest_status must be ready, pending, or blocked")


def _require_public_string(field_name: str, value: object) -> None:
    if type(value) is not str or not value.strip():
        raise ValueError(f"{field_name} must be a non-empty string")
    if value != value.strip():
        raise ValueError(f"{field_name} must be stripped")


def _normalize_count(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    with localcontext(DECIMAL_CONTEXT):
        normalized = value.quantize(QUANTUM)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{field_name} must be an integer")
    return normalized


def _normalize_reason_codes(value: object) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ValueError("reason_codes must be a tuple")
    if not value:
        raise ValueError("reason_codes must not be empty")
    normalized: list[str] = []
    allowed = set(REASON_PRIORITY)
    for reason_code in value:
        _require_public_string("reason_codes", reason_code)
        if reason_code not in allowed:
            raise ValueError("reason_codes contains an unknown reason")
        if reason_code not in normalized:
            normalized.append(reason_code)
    return tuple(
        reason_code for reason_code in REASON_PRIORITY if reason_code in normalized
    )


def _require_digest(value: object) -> None:
    if value == "pending":
        return
    if type(value) is not str or len(value) != 64:
        raise ValueError("payload_digest must be a sha256 hex digest")
    try:
        int(value, 16)
    except ValueError as exc:
        raise ValueError("payload_digest must be a sha256 hex digest") from exc


def _require_hard_flags(label: str, value: Any) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if getattr(value, field_name) is not True:
            raise ValueError(f"{label} must keep {field_name}=True")


def _decimal_text(value: Decimal) -> str:
    return format(value.quantize(QUANTUM), "f")
