from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from decimal import Decimal
from typing import Any


AUDIT_TRAIL_STATUSES = ("pass", "watch", "blocked")
ZERO = Decimal("0")


@dataclass(frozen=True)
class OperatorStrategyRecommendationAuditTrailReport:
    recommendation_count: Decimal
    ranked_candidate_count: Decimal
    missing_digest_count: Decimal
    manual_review_count: Decimal
    approved_candidate_count: Decimal
    audit_trail_status: str
    reason_codes: tuple[str, ...]
    manual_next_step: str
    payload_digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_counts(self)
        _require_flags(self)
        if self.audit_trail_status not in AUDIT_TRAIL_STATUSES:
            raise ValueError("audit_trail_status must be pass, watch, or blocked")
        object.__setattr__(
            self,
            "reason_codes",
            _require_text_tuple("reason_codes", self.reason_codes),
        )
        _require_text("manual_next_step", self.manual_next_step)
        _require_payload_digest(self.payload_digest)
        _validate_report(self)

    @property
    def public_payload(self) -> "FrozenPublicPayload":
        return _freeze_public_payload(_payload_with_digest(self))


def build_operator_strategy_recommendation_audit_trail_report(
    *,
    recommendation_count: Decimal,
    ranked_candidate_count: Decimal,
    missing_digest_count: Decimal,
    manual_review_count: Decimal,
    approved_candidate_count: Decimal,
) -> OperatorStrategyRecommendationAuditTrailReport:
    counts = {
        "recommendation_count": _require_count(
            "recommendation_count",
            recommendation_count,
        ),
        "ranked_candidate_count": _require_count(
            "ranked_candidate_count",
            ranked_candidate_count,
        ),
        "missing_digest_count": _require_count(
            "missing_digest_count",
            missing_digest_count,
        ),
        "manual_review_count": _require_count(
            "manual_review_count",
            manual_review_count,
        ),
        "approved_candidate_count": _require_count(
            "approved_candidate_count",
            approved_candidate_count,
        ),
    }
    status = _audit_trail_status(**counts)
    reason_codes = _reason_codes(**counts)
    manual_next_step = _manual_next_step(status, reason_codes)
    payload_without_digest = {
        **{key: _decimal_text(value) for key, value in counts.items()},
        "audit_trail_status": status,
        "reason_codes": list(reason_codes),
        "manual_next_step": manual_next_step,
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    return OperatorStrategyRecommendationAuditTrailReport(
        **counts,
        audit_trail_status=status,
        reason_codes=reason_codes,
        manual_next_step=manual_next_step,
        payload_digest=_hexdigest(payload_without_digest),
    )


class FrozenPublicPayload(dict[str, Any]):
    def __setitem__(self, key: str, value: Any) -> None:
        raise TypeError("public_payload is immutable")

    def __delitem__(self, key: str) -> None:
        raise TypeError("public_payload is immutable")

    def clear(self) -> None:
        raise TypeError("public_payload is immutable")

    def pop(self, key: str, default: Any = None) -> Any:
        raise TypeError("public_payload is immutable")

    def popitem(self) -> tuple[str, Any]:
        raise TypeError("public_payload is immutable")

    def setdefault(self, key: str, default: Any = None) -> Any:
        raise TypeError("public_payload is immutable")

    def update(self, *args: Any, **kwargs: Any) -> None:
        raise TypeError("public_payload is immutable")

    def __ior__(self, other: object) -> "FrozenPublicPayload":
        raise TypeError("public_payload is immutable")


class FrozenPublicArray(tuple[Any, ...]):
    def __eq__(self, other: object) -> bool:
        if isinstance(other, (list, tuple)):
            return tuple(self) == tuple(other)
        return False

    def append(self, value: Any) -> None:
        raise TypeError("public_payload is immutable")

    def extend(self, values: Any) -> None:
        raise TypeError("public_payload is immutable")


def _audit_trail_status(
    *,
    recommendation_count: Decimal,
    ranked_candidate_count: Decimal,
    missing_digest_count: Decimal,
    manual_review_count: Decimal,
    approved_candidate_count: Decimal,
) -> str:
    if (
        missing_digest_count > ZERO
        or approved_candidate_count > recommendation_count
        or ranked_candidate_count > recommendation_count
        or manual_review_count > recommendation_count
    ):
        return "blocked"
    if (
        recommendation_count == ZERO
        or manual_review_count > ZERO
        or ranked_candidate_count != recommendation_count
        or approved_candidate_count != recommendation_count
    ):
        return "watch"
    return "pass"


def _reason_codes(
    *,
    recommendation_count: Decimal,
    ranked_candidate_count: Decimal,
    missing_digest_count: Decimal,
    manual_review_count: Decimal,
    approved_candidate_count: Decimal,
) -> tuple[str, ...]:
    codes: list[str] = []
    if recommendation_count == ZERO:
        codes.append("recommendation_audit_trail_empty")
    if missing_digest_count > ZERO:
        codes.append("candidate_digest_missing")
    if approved_candidate_count > recommendation_count:
        codes.append("approved_candidate_count_exceeds_recommendations")
    if ranked_candidate_count > recommendation_count:
        codes.append("ranked_candidate_count_exceeds_recommendations")
    if manual_review_count > recommendation_count:
        codes.append("manual_review_count_exceeds_recommendations")
    if manual_review_count > ZERO and manual_review_count <= recommendation_count:
        codes.append("manual_review_pending")
    if ranked_candidate_count < recommendation_count:
        codes.append("ranked_candidate_gap")
    if approved_candidate_count < recommendation_count and recommendation_count > ZERO:
        codes.append("approval_gap")
    if not codes:
        codes.append("recommendation_audit_trail_complete")
    return tuple(codes)


def _manual_next_step(status: str, reason_codes: tuple[str, ...]) -> str:
    if "candidate_digest_missing" in reason_codes:
        return "rebuild_missing_digest_chain_before_approval"
    if any(code.endswith("_exceeds_recommendations") for code in reason_codes):
        if "approved_candidate_count_exceeds_recommendations" in reason_codes:
            return "reconcile_approved_candidate_count"
        if "ranked_candidate_count_exceeds_recommendations" in reason_codes:
            return "reconcile_ranked_candidate_count"
        return "reconcile_manual_review_count"
    if "recommendation_audit_trail_empty" in reason_codes:
        return "wait_for_recommendation_chain"
    if "manual_review_pending" in reason_codes:
        return "complete_manual_review_before_operator_approval"
    if "ranked_candidate_gap" in reason_codes:
        return "rank_all_recommendation_candidates"
    if "approval_gap" in reason_codes:
        return "complete_readonly_operator_approval_review"
    if status == "pass":
        return "archive_readonly_audit_trail"
    return "review_recommendation_audit_trail"


def _validate_report(report: OperatorStrategyRecommendationAuditTrailReport) -> None:
    counts = {
        "recommendation_count": report.recommendation_count,
        "ranked_candidate_count": report.ranked_candidate_count,
        "missing_digest_count": report.missing_digest_count,
        "manual_review_count": report.manual_review_count,
        "approved_candidate_count": report.approved_candidate_count,
    }
    expected_reasons = _reason_codes(**counts)
    if report.reason_codes != expected_reasons:
        raise ValueError("reason_codes must match count state")
    expected_status = _audit_trail_status(**counts)
    if report.audit_trail_status != expected_status:
        raise ValueError("audit_trail_status must match count state")
    expected_step = _manual_next_step(expected_status, expected_reasons)
    if report.manual_next_step != expected_step:
        raise ValueError("manual_next_step must match count state")
    if report.payload_digest != _hexdigest(_payload_without_digest(report)):
        raise ValueError("payload_digest must match public payload")


def _require_counts(report: OperatorStrategyRecommendationAuditTrailReport) -> None:
    for field_name in (
        "recommendation_count",
        "ranked_candidate_count",
        "missing_digest_count",
        "manual_review_count",
        "approved_candidate_count",
    ):
        object.__setattr__(
            report,
            field_name,
            _require_count(field_name, getattr(report, field_name)),
        )


def _require_count(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be exactly Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    if value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    if value != value.to_integral_value():
        raise ValueError(f"{field_name} must be an integer Decimal")
    return value


def _require_flags(value: object) -> None:
    if getattr(value, "paper_only") is not True:
        raise ValueError("paper_only must be True")
    if getattr(value, "report_only") is not True:
        raise ValueError("report_only must be True")
    if getattr(value, "readonly") is not True:
        raise ValueError("readonly must be True")


def _require_text_tuple(field_name: str, value: object) -> tuple[str, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError(f"{field_name} must be a tuple of strings")
    try:
        items = tuple(value)  # type: ignore[arg-type]
    except TypeError as exc:
        raise ValueError(f"{field_name} must be a tuple of strings") from exc
    if not items:
        raise ValueError(f"{field_name} must not be empty")
    for item in items:
        _require_text(field_name, item)
    return items


def _require_text(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a nonblank string")
    if any(ord(character) < 32 for character in value):
        raise ValueError(f"{field_name} must not contain control characters")


def _require_payload_digest(value: object) -> None:
    if type(value) is not str:
        raise ValueError("payload_digest must be a string")
    if len(value) != 64:
        raise ValueError("payload_digest must be a sha256 hex string")
    try:
        int(value, 16)
    except ValueError as exc:
        raise ValueError("payload_digest must be a sha256 hex string") from exc


def _payload_without_digest(
    report: OperatorStrategyRecommendationAuditTrailReport,
) -> dict[str, Any]:
    return {
        "recommendation_count": _decimal_text(report.recommendation_count),
        "ranked_candidate_count": _decimal_text(report.ranked_candidate_count),
        "missing_digest_count": _decimal_text(report.missing_digest_count),
        "manual_review_count": _decimal_text(report.manual_review_count),
        "approved_candidate_count": _decimal_text(report.approved_candidate_count),
        "audit_trail_status": report.audit_trail_status,
        "reason_codes": list(report.reason_codes),
        "manual_next_step": report.manual_next_step,
        "paper_only": report.paper_only,
        "report_only": report.report_only,
        "readonly": report.readonly,
    }


def _payload_with_digest(
    report: OperatorStrategyRecommendationAuditTrailReport,
) -> dict[str, Any]:
    payload = _payload_without_digest(report)
    payload["payload_digest"] = report.payload_digest
    return payload


def _hexdigest(payload: dict[str, Any]) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _decimal_text(value: Decimal) -> str:
    return format(value, "f")


def _freeze_public_payload(value: dict[str, Any]) -> FrozenPublicPayload:
    return FrozenPublicPayload(
        {key: _freeze_public_value(item) for key, item in value.items()},
    )


def _freeze_public_value(value: Any) -> Any:
    if type(value) is dict:
        return _freeze_public_payload(value)
    if type(value) is list:
        return FrozenPublicArray(_freeze_public_value(item) for item in value)
    return value


__all__ = (
    "AUDIT_TRAIL_STATUSES",
    "FrozenPublicArray",
    "FrozenPublicPayload",
    "OperatorStrategyRecommendationAuditTrailReport",
    "build_operator_strategy_recommendation_audit_trail_report",
)
