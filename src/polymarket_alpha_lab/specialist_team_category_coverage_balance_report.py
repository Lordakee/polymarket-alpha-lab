"""Pure Phase 1 report for specialist team category coverage balance."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
import hashlib
import json
from typing import Any


CONFIG_VERSION = "specialist-team-category-coverage-balance-report-v1"
ZERO = Decimal("0")
COUNT_QUANTUM = Decimal("1")
DIGEST_LENGTH = 64

COVERAGE_BALANCE_STATUSES = ("balanced", "watch", "blocked")
REASON_CODES = (
    "category_universe_missing",
    "all_categories_covered",
    "category_coverage_incomplete",
    "no_overloaded_specialist_teams",
    "overloaded_specialist_teams_present",
    "no_undercovered_categories",
    "undercovered_categories_present",
    "all_category_memory_ready",
    "category_memory_incomplete",
    "coverage_balance_balanced",
    "coverage_balance_watch",
    "coverage_balance_blocked",
)

NEXT_STEP_BY_STATUS = {
    "balanced": "Manual review only; keep specialist team category coverage on file.",
    "watch": "Manually rebalance specialist coverage and memory readiness before reuse.",
    "blocked": "Manually assign specialist team coverage before paper research.",
}

PAYLOAD_FIELDS = (
    "config_version",
    "category_count",
    "covered_category_count",
    "overloaded_team_count",
    "undercovered_category_count",
    "memory_ready_category_count",
    "coverage_balance_status",
    "reason_codes",
    "manual_next_step",
    "paper_only",
    "report_only",
    "readonly",
    "payload_digest",
)


class _FinalDataclass:
    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        for base in cls.__bases__:
            if base is not _FinalDataclass and issubclass(base, _FinalDataclass):
                raise TypeError(f"{base.__name__} may not be subclassed")


@dataclass(frozen=True)
class SpecialistTeamCategoryCoverageBalanceReport(_FinalDataclass):
    config_version: str
    category_count: Decimal
    covered_category_count: Decimal
    overloaded_team_count: Decimal
    undercovered_category_count: Decimal
    memory_ready_category_count: Decimal
    coverage_balance_status: str
    reason_codes: tuple[str, ...]
    manual_next_step: str
    payload_digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, SpecialistTeamCategoryCoverageBalanceReport, "report")
        if self.config_version != CONFIG_VERSION:
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "category_count",
            "covered_category_count",
            "overloaded_team_count",
            "undercovered_category_count",
            "memory_ready_category_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_count(field_name, getattr(self, field_name)),
            )
        _validate_count_relationships(
            category_count=self.category_count,
            covered_category_count=self.covered_category_count,
            undercovered_category_count=self.undercovered_category_count,
            memory_ready_category_count=self.memory_ready_category_count,
        )
        _require_coverage_balance_status(
            "coverage_balance_status",
            self.coverage_balance_status,
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes),
        )
        if type(self.manual_next_step) is not str or not self.manual_next_step:
            raise ValueError("manual_next_step must be a non-empty string")
        _require_digest_or_pending("payload_digest", self.payload_digest)
        _require_hard_flags("report", self)
        _validate_report(self)

    @property
    def public_payload(self) -> dict[str, Any]:
        return specialist_team_category_coverage_balance_report_payload(self)


def build_specialist_team_category_coverage_balance_report(
    *,
    category_count: Decimal,
    covered_category_count: Decimal,
    overloaded_team_count: Decimal,
    undercovered_category_count: Decimal,
    memory_ready_category_count: Decimal,
) -> SpecialistTeamCategoryCoverageBalanceReport:
    normalized_category_count = _normalize_count("category_count", category_count)
    normalized_covered_category_count = _normalize_count(
        "covered_category_count",
        covered_category_count,
    )
    normalized_overloaded_team_count = _normalize_count(
        "overloaded_team_count",
        overloaded_team_count,
    )
    normalized_undercovered_category_count = _normalize_count(
        "undercovered_category_count",
        undercovered_category_count,
    )
    normalized_memory_ready_category_count = _normalize_count(
        "memory_ready_category_count",
        memory_ready_category_count,
    )
    _validate_count_relationships(
        category_count=normalized_category_count,
        covered_category_count=normalized_covered_category_count,
        undercovered_category_count=normalized_undercovered_category_count,
        memory_ready_category_count=normalized_memory_ready_category_count,
    )
    values = {
        "config_version": CONFIG_VERSION,
        "category_count": normalized_category_count,
        "covered_category_count": normalized_covered_category_count,
        "overloaded_team_count": normalized_overloaded_team_count,
        "undercovered_category_count": normalized_undercovered_category_count,
        "memory_ready_category_count": normalized_memory_ready_category_count,
    }
    reason_codes = _reason_codes(
        category_count=normalized_category_count,
        covered_category_count=normalized_covered_category_count,
        overloaded_team_count=normalized_overloaded_team_count,
        undercovered_category_count=normalized_undercovered_category_count,
        memory_ready_category_count=normalized_memory_ready_category_count,
    )
    status = _coverage_balance_status(reason_codes)
    values["coverage_balance_status"] = status
    values["reason_codes"] = reason_codes
    values["manual_next_step"] = NEXT_STEP_BY_STATUS[status]
    report = SpecialistTeamCategoryCoverageBalanceReport(
        **values,
        payload_digest="pending",
    )
    return SpecialistTeamCategoryCoverageBalanceReport(
        config_version=report.config_version,
        category_count=report.category_count,
        covered_category_count=report.covered_category_count,
        overloaded_team_count=report.overloaded_team_count,
        undercovered_category_count=report.undercovered_category_count,
        memory_ready_category_count=report.memory_ready_category_count,
        coverage_balance_status=report.coverage_balance_status,
        reason_codes=report.reason_codes,
        manual_next_step=report.manual_next_step,
        payload_digest=_payload_digest_without_digest(report),
    )


def specialist_team_category_coverage_balance_report_payload(
    report: SpecialistTeamCategoryCoverageBalanceReport | dict[str, Any],
) -> dict[str, Any]:
    if type(report) is SpecialistTeamCategoryCoverageBalanceReport:
        _require_hard_flags("report", report)
        _validate_report(report)
        expected_digest = _payload_digest_without_digest(report)
        if report.payload_digest != expected_digest:
            raise ValueError("payload_digest must match coverage balance payload")
        payload = _public_payload_without_digest(report)
        payload["payload_digest"] = expected_digest
        _validate_payload_schema(payload)
        return payload
    if type(report) is dict:
        _validate_payload_schema(report)
        _reject_public_numeric_values(report)
        _require_hard_flags("payload", report)
        expected_digest = _payload_digest_from_payload(report)
        if report["payload_digest"] != expected_digest:
            raise ValueError("payload_digest mismatch for coverage balance payload")
        return dict(report)
    raise ValueError(
        "report must be a SpecialistTeamCategoryCoverageBalanceReport or payload dict",
    )


def _reason_codes(
    *,
    category_count: Decimal,
    covered_category_count: Decimal,
    overloaded_team_count: Decimal,
    undercovered_category_count: Decimal,
    memory_ready_category_count: Decimal,
) -> tuple[str, ...]:
    codes: list[str] = []
    if category_count == ZERO:
        codes.append("category_universe_missing")
    elif covered_category_count == category_count:
        codes.append("all_categories_covered")
    else:
        codes.append("category_coverage_incomplete")
    if overloaded_team_count == ZERO:
        codes.append("no_overloaded_specialist_teams")
    else:
        codes.append("overloaded_specialist_teams_present")
    if undercovered_category_count == ZERO:
        codes.append("no_undercovered_categories")
    else:
        codes.append("undercovered_categories_present")
    if memory_ready_category_count == category_count:
        codes.append("all_category_memory_ready")
    else:
        codes.append("category_memory_incomplete")
    status = _coverage_balance_status(tuple(codes))
    codes.append(f"coverage_balance_{status}")
    return _normalize_reason_codes(tuple(codes))


def _coverage_balance_status(reason_codes: tuple[str, ...]) -> str:
    if (
        "category_universe_missing" in reason_codes
        or "category_coverage_incomplete" in reason_codes
        or "undercovered_categories_present" in reason_codes
    ):
        return "blocked"
    if (
        "overloaded_specialist_teams_present" in reason_codes
        or "category_memory_incomplete" in reason_codes
    ):
        return "watch"
    return "balanced"


def _public_payload_without_digest(
    report: SpecialistTeamCategoryCoverageBalanceReport,
) -> dict[str, Any]:
    return {
        "config_version": report.config_version,
        "category_count": _decimal_to_string(report.category_count),
        "covered_category_count": _decimal_to_string(report.covered_category_count),
        "overloaded_team_count": _decimal_to_string(report.overloaded_team_count),
        "undercovered_category_count": _decimal_to_string(
            report.undercovered_category_count,
        ),
        "memory_ready_category_count": _decimal_to_string(
            report.memory_ready_category_count,
        ),
        "coverage_balance_status": report.coverage_balance_status,
        "reason_codes": list(report.reason_codes),
        "manual_next_step": report.manual_next_step,
        "paper_only": report.paper_only,
        "report_only": report.report_only,
        "readonly": report.readonly,
    }


def _payload_digest_without_digest(
    report: SpecialistTeamCategoryCoverageBalanceReport,
) -> str:
    return _digest_mapping(_public_payload_without_digest(report))


def _payload_digest_from_payload(payload: dict[str, Any]) -> str:
    payload_without_digest = dict(payload)
    payload_without_digest.pop("payload_digest")
    return _digest_mapping(payload_without_digest)


def _digest_mapping(payload: dict[str, Any]) -> str:
    encoded = json.dumps(payload, separators=(",", ":"), sort_keys=True).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _validate_report(report: SpecialistTeamCategoryCoverageBalanceReport) -> None:
    expected_reasons = _reason_codes(
        category_count=report.category_count,
        covered_category_count=report.covered_category_count,
        overloaded_team_count=report.overloaded_team_count,
        undercovered_category_count=report.undercovered_category_count,
        memory_ready_category_count=report.memory_ready_category_count,
    )
    if report.reason_codes != expected_reasons:
        raise ValueError("reason_codes must match coverage balance inputs")
    expected_status = _coverage_balance_status(report.reason_codes)
    if report.coverage_balance_status != expected_status:
        raise ValueError("coverage_balance_status must match reason_codes")
    expected_step = NEXT_STEP_BY_STATUS[report.coverage_balance_status]
    if report.manual_next_step != expected_step:
        raise ValueError("manual_next_step must match coverage_balance_status")


def _validate_payload_schema(payload: dict[str, Any]) -> None:
    if tuple(payload) != PAYLOAD_FIELDS:
        raise ValueError("payload fields must be deterministic")
    for field_name in (
        "category_count",
        "covered_category_count",
        "overloaded_team_count",
        "undercovered_category_count",
        "memory_ready_category_count",
    ):
        _parse_payload_decimal(field_name, payload[field_name])
    _validate_count_relationships(
        category_count=_parse_payload_decimal("category_count", payload["category_count"]),
        covered_category_count=_parse_payload_decimal(
            "covered_category_count",
            payload["covered_category_count"],
        ),
        undercovered_category_count=_parse_payload_decimal(
            "undercovered_category_count",
            payload["undercovered_category_count"],
        ),
        memory_ready_category_count=_parse_payload_decimal(
            "memory_ready_category_count",
            payload["memory_ready_category_count"],
        ),
    )
    _require_coverage_balance_status(
        "coverage_balance_status",
        payload["coverage_balance_status"],
    )
    _normalize_reason_codes(tuple(payload["reason_codes"]))
    _require_digest_or_pending("payload_digest", payload["payload_digest"])


def _validate_count_relationships(
    *,
    category_count: Decimal,
    covered_category_count: Decimal,
    undercovered_category_count: Decimal,
    memory_ready_category_count: Decimal,
) -> None:
    if undercovered_category_count > category_count:
        raise ValueError("undercovered_category_count cannot exceed category_count")
    if memory_ready_category_count > category_count:
        raise ValueError("memory_ready_category_count cannot exceed category_count")
    if covered_category_count > category_count:
        raise ValueError("covered_category_count cannot exceed category_count")


def _require_exact_type(value: object, expected_type: type[object], label: str) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{label} must be exactly {expected_type.__name__}")


def _normalize_count(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    if value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    if value != value.quantize(COUNT_QUANTUM):
        raise ValueError(f"{field_name} must be an integral Decimal")
    return value.quantize(COUNT_QUANTUM)


def _parse_payload_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a Decimal string")
    try:
        parsed = Decimal(value)
    except Exception as exc:
        raise ValueError(f"{field_name} must be a Decimal string") from exc
    return _normalize_count(field_name, parsed)


def _require_coverage_balance_status(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if value not in COVERAGE_BALANCE_STATUSES:
        raise ValueError(f"{field_name} must be balanced, watch, or blocked")


def _normalize_reason_codes(value: object) -> tuple[str, ...]:
    if isinstance(value, (str, bytes)) or type(value) not in (list, tuple):
        raise ValueError("reason_codes must be a list or tuple")
    normalized = tuple(value)
    if not normalized:
        raise ValueError("reason_codes must not be empty")
    for reason_code in normalized:
        if type(reason_code) is not str or reason_code not in REASON_CODES:
            raise ValueError("reason_codes must contain known reason codes")
    if len(set(normalized)) != len(normalized):
        raise ValueError("reason_codes must be unique")
    if tuple(reason for reason in REASON_CODES if reason in normalized) != normalized:
        raise ValueError("reason_codes must be deterministic")
    return normalized


def _require_digest_or_pending(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if value == "pending":
        return
    if len(value) != DIGEST_LENGTH or any(char not in "0123456789abcdef" for char in value):
        raise ValueError(f"{field_name} must be a sha256 hex digest")


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if isinstance(value, dict):
            flag_value = value.get(field_name)
        else:
            flag_value = getattr(value, field_name, None)
        if flag_value is not True:
            raise ValueError(f"{field_name} must be True for {label}")


def _reject_public_numeric_values(value: object) -> None:
    if type(value) in (int, float):
        raise ValueError("public payload must use Decimal strings, not numeric values")
    if isinstance(value, dict):
        for child in value.values():
            _reject_public_numeric_values(child)
    if isinstance(value, list):
        for child in value:
            _reject_public_numeric_values(child)


def _decimal_to_string(value: Decimal) -> str:
    return format(value, "f")


__all__ = (
    "CONFIG_VERSION",
    "SpecialistTeamCategoryCoverageBalanceReport",
    "build_specialist_team_category_coverage_balance_report",
    "specialist_team_category_coverage_balance_report_payload",
)
