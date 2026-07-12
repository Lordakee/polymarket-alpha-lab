"""Read-only operator candidate portfolio conflict check report."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from hashlib import sha256
import json
from typing import Mapping


__all__ = (
    "OPERATOR_CANDIDATE_PORTFOLIO_CONFLICT_STATUSES",
    "OperatorCandidatePortfolioConflictCheckReport",
    "build_operator_candidate_portfolio_conflict_check_report",
    "operator_candidate_portfolio_conflict_check_report_payload",
    "operator_candidate_portfolio_conflict_check_report_payload_digest",
    "validate_operator_candidate_portfolio_conflict_check_public_payload",
)


ZERO = Decimal("0")
COUNT_QUANTUM = Decimal("1")

OPERATOR_CANDIDATE_PORTFOLIO_CONFLICT_STATUSES = (
    "clear",
    "manual_review",
    "blocked",
)

CLEAR_REASON_CODE = "candidate_portfolio_conflict_clear"
REASON_CODE_SEQUENCE = (
    "candidate_portfolio_same_event_family_conflict",
    "candidate_portfolio_opposing_outcome_conflict",
    "candidate_portfolio_correlated_risk_conflict",
    "candidate_portfolio_manual_conflict_limit_exceeded",
    CLEAR_REASON_CODE,
)
MANUAL_NEXT_STEPS = (
    "manual_monitor_candidate_portfolio",
    "manual_review_candidate_portfolio_conflicts",
    "manual_block_candidate_portfolio_until_resolved",
)
PAYLOAD_KEYS = (
    "candidate_market_count",
    "same_event_family_count",
    "opposing_outcome_count",
    "correlated_risk_count",
    "manual_conflict_limit_count",
    "conflict_status",
    "reason_codes",
    "manual_next_step",
    "paper_only",
    "report_only",
    "readonly",
)
COUNT_FIELDS = (
    "candidate_market_count",
    "same_event_family_count",
    "opposing_outcome_count",
    "correlated_risk_count",
    "manual_conflict_limit_count",
)


class _OperatorCandidatePortfolioConflictCheckPublicDataclass:
    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        for base in cls.__bases__:
            if (
                base is not _OperatorCandidatePortfolioConflictCheckPublicDataclass
                and issubclass(
                    base,
                    _OperatorCandidatePortfolioConflictCheckPublicDataclass,
                )
            ):
                raise TypeError(f"{base.__name__} does not support subclassing")


@dataclass(frozen=True)
class OperatorCandidatePortfolioConflictCheckReport(
    _OperatorCandidatePortfolioConflictCheckPublicDataclass,
):
    candidate_market_count: Decimal
    same_event_family_count: Decimal
    opposing_outcome_count: Decimal
    correlated_risk_count: Decimal
    manual_conflict_limit_count: Decimal
    conflict_status: str
    reason_codes: tuple[str, ...]
    manual_next_step: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            OperatorCandidatePortfolioConflictCheckReport,
            "report",
        )
        for field_name in COUNT_FIELDS:
            object.__setattr__(
                self,
                field_name,
                _normalize_count(field_name, getattr(self, field_name)),
            )
        for field_name in ("paper_only", "report_only", "readonly"):
            _require_true(field_name, getattr(self, field_name))
        object.__setattr__(
            self,
            "conflict_status",
            _normalize_status("conflict_status", self.conflict_status),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        object.__setattr__(
            self,
            "manual_next_step",
            _normalize_next_step("manual_next_step", self.manual_next_step),
        )
        _validate_report(self)

    @property
    def public_payload(self) -> dict[str, object]:
        return operator_candidate_portfolio_conflict_check_report_payload(self)

    @property
    def payload_digest(self) -> str:
        return operator_candidate_portfolio_conflict_check_report_payload_digest(self)


def build_operator_candidate_portfolio_conflict_check_report(
    *,
    candidate_market_count: Decimal,
    same_event_family_count: Decimal,
    opposing_outcome_count: Decimal,
    correlated_risk_count: Decimal,
    manual_conflict_limit_count: Decimal,
) -> OperatorCandidatePortfolioConflictCheckReport:
    counts = {
        "candidate_market_count": _normalize_count(
            "candidate_market_count",
            candidate_market_count,
        ),
        "same_event_family_count": _normalize_count(
            "same_event_family_count",
            same_event_family_count,
        ),
        "opposing_outcome_count": _normalize_count(
            "opposing_outcome_count",
            opposing_outcome_count,
        ),
        "correlated_risk_count": _normalize_count(
            "correlated_risk_count",
            correlated_risk_count,
        ),
        "manual_conflict_limit_count": _normalize_count(
            "manual_conflict_limit_count",
            manual_conflict_limit_count,
        ),
    }
    conflict_status, reason_codes, manual_next_step = _findings(
        candidate_market_count=counts["candidate_market_count"],
        same_event_family_count=counts["same_event_family_count"],
        opposing_outcome_count=counts["opposing_outcome_count"],
        correlated_risk_count=counts["correlated_risk_count"],
        manual_conflict_limit_count=counts["manual_conflict_limit_count"],
    )
    return OperatorCandidatePortfolioConflictCheckReport(
        candidate_market_count=counts["candidate_market_count"],
        same_event_family_count=counts["same_event_family_count"],
        opposing_outcome_count=counts["opposing_outcome_count"],
        correlated_risk_count=counts["correlated_risk_count"],
        manual_conflict_limit_count=counts["manual_conflict_limit_count"],
        conflict_status=conflict_status,
        reason_codes=reason_codes,
        manual_next_step=manual_next_step,
    )


def operator_candidate_portfolio_conflict_check_report_payload(
    report: OperatorCandidatePortfolioConflictCheckReport,
) -> dict[str, object]:
    if type(report) is not OperatorCandidatePortfolioConflictCheckReport:
        raise ValueError(
            "report must be exactly OperatorCandidatePortfolioConflictCheckReport",
        )
    _validate_report(report)
    payload: dict[str, object] = {
        "candidate_market_count": _serialize_count(report.candidate_market_count),
        "same_event_family_count": _serialize_count(report.same_event_family_count),
        "opposing_outcome_count": _serialize_count(report.opposing_outcome_count),
        "correlated_risk_count": _serialize_count(report.correlated_risk_count),
        "manual_conflict_limit_count": _serialize_count(
            report.manual_conflict_limit_count,
        ),
        "conflict_status": report.conflict_status,
        "reason_codes": list(report.reason_codes),
        "manual_next_step": report.manual_next_step,
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    validate_operator_candidate_portfolio_conflict_check_public_payload(payload)
    return payload


def operator_candidate_portfolio_conflict_check_report_payload_digest(
    report: OperatorCandidatePortfolioConflictCheckReport,
) -> str:
    payload = operator_candidate_portfolio_conflict_check_report_payload(report)
    return _digest_payload(payload)


def validate_operator_candidate_portfolio_conflict_check_public_payload(
    payload: Mapping[str, object],
) -> Mapping[str, object]:
    if not isinstance(payload, Mapping):
        raise ValueError("payload must be a mapping")
    if tuple(payload.keys()) != PAYLOAD_KEYS:
        raise ValueError("payload must match the canonical conflict check schema")
    for field_name in COUNT_FIELDS:
        value = payload[field_name]
        if type(value) is not str:
            raise ValueError(f"{field_name} must be serialized as a string")
        _normalize_count(field_name, Decimal(value))
    conflict_status = _normalize_status(
        "conflict_status",
        payload["conflict_status"],
    )
    reason_codes = _normalize_payload_reason_codes(
        "reason_codes",
        payload["reason_codes"],
    )
    manual_next_step = _normalize_next_step(
        "manual_next_step",
        payload["manual_next_step"],
    )
    for field_name in ("paper_only", "report_only", "readonly"):
        _require_true(field_name, payload[field_name])
    expected_status, expected_reason_codes, expected_next_step = _payload_findings(
        payload,
    )
    if conflict_status == "clear":
        candidate_market_count = Decimal(payload["candidate_market_count"])  # type: ignore[arg-type]
        manual_conflict_limit_count = Decimal(  # type: ignore[arg-type]
            payload["manual_conflict_limit_count"],
        )
        if candidate_market_count > manual_conflict_limit_count:
            raise ValueError("candidate_market_count must match conflict_status")
        for field_name in (
            "same_event_family_count",
            "opposing_outcome_count",
            "correlated_risk_count",
        ):
            if Decimal(payload[field_name]) != ZERO:  # type: ignore[arg-type]
                raise ValueError(f"{field_name} must match conflict_status")
    if conflict_status != expected_status:
        raise ValueError("conflict_status must match conflict counts")
    if reason_codes != expected_reason_codes:
        raise ValueError("reason_codes must match conflict counts")
    if manual_next_step != expected_next_step:
        raise ValueError("manual_next_step must match conflict_status")
    return payload


def _validate_report(report: OperatorCandidatePortfolioConflictCheckReport) -> None:
    conflict_status, reason_codes, manual_next_step = _findings(
        candidate_market_count=report.candidate_market_count,
        same_event_family_count=report.same_event_family_count,
        opposing_outcome_count=report.opposing_outcome_count,
        correlated_risk_count=report.correlated_risk_count,
        manual_conflict_limit_count=report.manual_conflict_limit_count,
    )
    if report.conflict_status != conflict_status:
        raise ValueError("report must be exactly derived from conflict counts")
    if report.reason_codes != reason_codes:
        raise ValueError("reason_codes must match conflict counts")
    if report.manual_next_step != manual_next_step:
        raise ValueError("manual_next_step must match conflict_status")


def _payload_findings(
    payload: Mapping[str, object],
) -> tuple[str, tuple[str, ...], str]:
    return _findings(
        candidate_market_count=Decimal(payload["candidate_market_count"]),  # type: ignore[arg-type]
        same_event_family_count=Decimal(payload["same_event_family_count"]),  # type: ignore[arg-type]
        opposing_outcome_count=Decimal(payload["opposing_outcome_count"]),  # type: ignore[arg-type]
        correlated_risk_count=Decimal(payload["correlated_risk_count"]),  # type: ignore[arg-type]
        manual_conflict_limit_count=Decimal(  # type: ignore[arg-type]
            payload["manual_conflict_limit_count"],
        ),
    )


def _findings(
    *,
    candidate_market_count: Decimal,
    same_event_family_count: Decimal,
    opposing_outcome_count: Decimal,
    correlated_risk_count: Decimal,
    manual_conflict_limit_count: Decimal,
) -> tuple[str, tuple[str, ...], str]:
    reason_codes: list[str] = []
    if same_event_family_count > ZERO:
        reason_codes.append("candidate_portfolio_same_event_family_conflict")
    if opposing_outcome_count > ZERO:
        reason_codes.append("candidate_portfolio_opposing_outcome_conflict")
    if correlated_risk_count > ZERO:
        reason_codes.append("candidate_portfolio_correlated_risk_conflict")
    if candidate_market_count > manual_conflict_limit_count:
        reason_codes.append("candidate_portfolio_manual_conflict_limit_exceeded")

    ordered_reason_codes = tuple(
        reason_code for reason_code in REASON_CODE_SEQUENCE if reason_code in reason_codes
    )
    if "candidate_portfolio_opposing_outcome_conflict" in ordered_reason_codes:
        return (
            "blocked",
            ordered_reason_codes,
            "manual_block_candidate_portfolio_until_resolved",
        )
    if "candidate_portfolio_manual_conflict_limit_exceeded" in ordered_reason_codes:
        return (
            "blocked",
            ordered_reason_codes,
            "manual_block_candidate_portfolio_until_resolved",
        )
    if ordered_reason_codes:
        return (
            "manual_review",
            ordered_reason_codes,
            "manual_review_candidate_portfolio_conflicts",
        )
    return (
        "clear",
        (CLEAR_REASON_CODE,),
        "manual_monitor_candidate_portfolio",
    )


def _normalize_count(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    if value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    if value != value.to_integral_value():
        raise ValueError(f"{field_name} must be an integer Decimal")
    return value.quantize(COUNT_QUANTUM)


def _serialize_count(value: Decimal) -> str:
    return format(value, "f")


def _normalize_status(field_name: str, value: object) -> str:
    if type(value) is not str or value not in OPERATOR_CANDIDATE_PORTFOLIO_CONFLICT_STATUSES:
        raise ValueError(f"{field_name} must be a supported conflict status")
    return value


def _normalize_next_step(field_name: str, value: object) -> str:
    if type(value) is not str or value not in MANUAL_NEXT_STEPS:
        raise ValueError(f"{field_name} must be a supported manual next step")
    return value


def _normalize_reason_codes(field_name: str, value: object) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ValueError(f"{field_name} must be a tuple")
    return _normalize_reason_code_items(field_name, value)


def _normalize_payload_reason_codes(
    field_name: str,
    value: object,
) -> tuple[str, ...]:
    if type(value) is not list:
        raise ValueError(f"{field_name} must be a list")
    return _normalize_reason_code_items(field_name, tuple(value))


def _normalize_reason_code_items(
    field_name: str,
    reason_codes: tuple[str, ...],
) -> tuple[str, ...]:
    seen: set[str] = set()
    for reason_code in reason_codes:
        if type(reason_code) is not str or reason_code not in REASON_CODE_SEQUENCE:
            raise ValueError(f"{field_name} contains unsupported reason code")
        if reason_code in seen:
            raise ValueError(f"{field_name} must not contain duplicates")
        seen.add(reason_code)
    ordered = tuple(
        reason_code for reason_code in REASON_CODE_SEQUENCE if reason_code in seen
    )
    if reason_codes != ordered:
        raise ValueError(f"{field_name} must use canonical ordering")
    return ordered


def _require_exact_type(value: object, expected_type: type[object], label: str) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{label} must be exactly {expected_type.__name__}")


def _require_true(field_name: str, value: object) -> None:
    if type(value) is not bool:
        raise ValueError(f"{field_name} must be a bool")
    if value is not True:
        raise ValueError(f"{field_name} must be True")


def _digest_payload(payload: dict[str, object]) -> str:
    return sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8"),
    ).hexdigest()
