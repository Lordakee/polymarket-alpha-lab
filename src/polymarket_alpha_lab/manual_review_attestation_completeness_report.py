"""Pure public-safe report-only manual review attestation completeness summary."""

from __future__ import annotations

from dataclasses import asdict, dataclass, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal
from hashlib import sha256
import json
from typing import Any


DEFAULT_MANUAL_REVIEW_ATTESTATION_COMPLETENESS_CONFIG_VERSION = (
    "manual-review-attestation-completeness-report-v0"
)

ATTESTATION_STATUSES = ("complete", "incomplete")
MANUAL_REVIEW_ATTESTATION_REQUIRED_SECTIONS = (
    "operator_id",
    "reviewed_screen",
    "reviewed_sources",
    "reviewed_costs",
    "reviewed_memory_policy",
    "reviewed_resolution_rules",
    "attestation_text_present",
)

ZERO = Decimal("0")

COMPLETE_REASON = "manual_review_attestation_complete"
SECTION_REASON_CODES = {
    "operator_id": "manual_review_operator_id_missing",
    "reviewed_screen": "manual_review_screen_not_reviewed",
    "reviewed_sources": "manual_review_sources_not_reviewed",
    "reviewed_costs": "manual_review_costs_not_reviewed",
    "reviewed_memory_policy": "manual_review_memory_policy_not_reviewed",
    "reviewed_resolution_rules": "manual_review_resolution_rules_not_reviewed",
    "attestation_text_present": "manual_review_attestation_text_missing",
}
REASON_CODES = (COMPLETE_REASON, *SECTION_REASON_CODES.values())
COMPLETE_NEXT_STEP = "manual_review_attestation_complete_report_only"
INCOMPLETE_NEXT_STEP = "complete_missing_manual_review_sections_before_any_use"
MANUAL_NEXT_STEPS = (COMPLETE_NEXT_STEP, INCOMPLETE_NEXT_STEP)

UNSAFE_PUBLIC_TEXT_FRAGMENTS = (
    "candidate" "_id",
    "event" "_id",
    "market" "_id",
    "market" "_slug",
    "source" "_id",
    "wal" "let",
    "au" "th",
    "ord" "er",
    "tra" "de",
    "li" "ve",
    "b" "uy",
    "se" "ll",
    "reco" "mmend",
    "position" "_size",
    "position" " sizing",
)


@dataclass(frozen=True)
class ManualReviewAttestationCompletenessConfig:
    config_version: str = DEFAULT_MANUAL_REVIEW_ATTESTATION_COMPLETENESS_CONFIG_VERSION
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_public_string("config_version", self.config_version)
        if self.config_version != DEFAULT_MANUAL_REVIEW_ATTESTATION_COMPLETENESS_CONFIG_VERSION:
            raise ValueError("config_version must be the supported config version")
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class ManualReviewAttestationCompletenessInput:
    operator_id: str | None
    reviewed_screen: bool
    reviewed_sources: bool
    reviewed_costs: bool
    reviewed_memory_policy: bool
    reviewed_resolution_rules: bool
    attestation_text_present: bool
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "operator_id",
            _normalize_operator_id("operator_id", self.operator_id),
        )
        for section in MANUAL_REVIEW_ATTESTATION_REQUIRED_SECTIONS[1:]:
            _require_bool(section, getattr(self, section))
        _require_hard_flags("attestation input", self)


@dataclass(frozen=True)
class ManualReviewAttestationCompletenessSectionRow:
    section: str
    is_complete: bool
    reason_code: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_section("section", self.section)
        _require_bool("is_complete", self.is_complete)
        _require_reason_code("reason_code", self.reason_code)
        _require_hard_flags("section row", self)
        _validate_row(self)


@dataclass(frozen=True)
class ManualReviewAttestationCompletenessReport:
    generated_at: datetime
    config_version: str
    operator_id: str | None
    required_section_count: Decimal
    completed_section_count: Decimal
    missing_section_count: Decimal
    attestation_status: str
    missing_sections: tuple[str, ...]
    reason_codes: tuple[str, ...]
    manual_next_step: str
    report_digest: str
    rows: tuple[ManualReviewAttestationCompletenessSectionRow, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_string("config_version", self.config_version)
        object.__setattr__(
            self,
            "operator_id",
            _normalize_operator_id("operator_id", self.operator_id),
        )
        for field_name in (
            "required_section_count",
            "completed_section_count",
            "missing_section_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_count(field_name, getattr(self, field_name)),
            )
        _require_status("attestation_status", self.attestation_status)
        object.__setattr__(
            self,
            "missing_sections",
            _normalize_missing_sections(self.missing_sections),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes),
        )
        _require_manual_next_step("manual_next_step", self.manual_next_step)
        _require_digest("report_digest", self.report_digest)
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        _require_hard_flags("report", self)
        _validate_report(self)


def build_manual_review_attestation_completeness_report(
    attestation: ManualReviewAttestationCompletenessInput,
    *,
    config: ManualReviewAttestationCompletenessConfig,
    generated_at: datetime,
) -> ManualReviewAttestationCompletenessReport:
    if type(attestation) is not ManualReviewAttestationCompletenessInput:
        raise ValueError(
            "attestation must be a ManualReviewAttestationCompletenessInput",
        )
    if type(config) is not ManualReviewAttestationCompletenessConfig:
        raise ValueError("config must be a ManualReviewAttestationCompletenessConfig")
    _require_hard_flags("attestation input", attestation)
    _require_hard_flags("config", config)
    rows = _build_rows(attestation)
    missing_sections = tuple(row.section for row in rows if not row.is_complete)
    reason_codes = _reason_codes_from_rows(rows)
    status = "complete" if not missing_sections else "incomplete"
    values = {
        "generated_at": _as_utc("generated_at", generated_at),
        "config_version": config.config_version,
        "operator_id": attestation.operator_id,
        "required_section_count": Decimal(len(rows)),
        "completed_section_count": Decimal(sum(1 for row in rows if row.is_complete)),
        "missing_section_count": Decimal(len(missing_sections)),
        "attestation_status": status,
        "missing_sections": missing_sections,
        "reason_codes": reason_codes,
        "manual_next_step": COMPLETE_NEXT_STEP if status == "complete" else INCOMPLETE_NEXT_STEP,
        "rows": rows,
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    return ManualReviewAttestationCompletenessReport(
        report_digest=_report_digest_for_values(values),
        **values,
    )


def manual_review_attestation_completeness_report_payload(
    report: ManualReviewAttestationCompletenessReport | dict[str, Any],
) -> dict[str, Any]:
    if type(report) is ManualReviewAttestationCompletenessReport:
        _require_hard_flags("report", report)
        return _json_ready(asdict(report))
    if type(report) is not dict:
        raise ValueError("report must be a ManualReviewAttestationCompletenessReport")
    payload = _json_ready(report)
    if type(payload) is not dict:
        raise ValueError("payload must be a dict")
    _require_payload_hard_flags(payload)
    _require_digest("report_digest", payload.get("report_digest"))
    if payload["report_digest"] != _report_digest_for_values(payload):
        raise ValueError("report_digest must match payload fields")
    return payload


def _build_rows(
    attestation: ManualReviewAttestationCompletenessInput,
) -> tuple[ManualReviewAttestationCompletenessSectionRow, ...]:
    return tuple(
        ManualReviewAttestationCompletenessSectionRow(
            section=section,
            is_complete=_section_is_complete(attestation, section),
            reason_code=_section_reason_code(attestation, section),
        )
        for section in MANUAL_REVIEW_ATTESTATION_REQUIRED_SECTIONS
    )


def _section_is_complete(
    attestation: ManualReviewAttestationCompletenessInput,
    section: str,
) -> bool:
    if section == "operator_id":
        return attestation.operator_id is not None
    return getattr(attestation, section) is True


def _section_reason_code(
    attestation: ManualReviewAttestationCompletenessInput,
    section: str,
) -> str:
    if _section_is_complete(attestation, section):
        return COMPLETE_REASON
    return SECTION_REASON_CODES[section]


def _reason_codes_from_rows(
    rows: tuple[ManualReviewAttestationCompletenessSectionRow, ...],
) -> tuple[str, ...]:
    missing = tuple(row.reason_code for row in rows if not row.is_complete)
    return missing if missing else (COMPLETE_REASON,)


def _validate_row(row: ManualReviewAttestationCompletenessSectionRow) -> None:
    if row.is_complete and row.reason_code != COMPLETE_REASON:
        raise ValueError("reason_codes must match row completeness")
    if not row.is_complete and row.reason_code != SECTION_REASON_CODES[row.section]:
        raise ValueError("reason_codes must match row completeness")


def _validate_report(report: ManualReviewAttestationCompletenessReport) -> None:
    rows = report.rows
    missing_sections = tuple(row.section for row in rows if not row.is_complete)
    reason_codes = _reason_codes_from_rows(rows)
    if tuple(row.section for row in rows) != MANUAL_REVIEW_ATTESTATION_REQUIRED_SECTIONS:
        raise ValueError("rows must match required section sequence")
    if report.required_section_count != Decimal(len(rows)):
        raise ValueError("required_section_count must match rows")
    if report.completed_section_count != Decimal(sum(1 for row in rows if row.is_complete)):
        raise ValueError("completed_section_count must match rows")
    if report.missing_section_count != Decimal(len(missing_sections)):
        raise ValueError("missing_section_count must match rows")
    if report.missing_sections != missing_sections:
        raise ValueError("missing_sections must match rows")
    if report.reason_codes != reason_codes:
        raise ValueError("reason_codes must match rows")
    if report.attestation_status != ("complete" if not missing_sections else "incomplete"):
        raise ValueError("attestation_status must match rows")
    if report.manual_next_step != (
        COMPLETE_NEXT_STEP if report.attestation_status == "complete" else INCOMPLETE_NEXT_STEP
    ):
        raise ValueError("manual_next_step must match attestation_status")
    if report.report_digest != _report_digest(report):
        raise ValueError("report_digest must match report fields")


def _normalize_rows(
    rows: object,
) -> tuple[ManualReviewAttestationCompletenessSectionRow, ...]:
    if type(rows) is not tuple:
        raise ValueError("rows must be a tuple")
    for row in rows:
        if type(row) is not ManualReviewAttestationCompletenessSectionRow:
            raise ValueError(
                "rows must contain ManualReviewAttestationCompletenessSectionRow",
            )
        _require_hard_flags("section row", row)
    return rows


def _normalize_missing_sections(value: object) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ValueError("missing_sections must be a tuple")
    for section in value:
        _require_section("missing_sections", section)
    if len(set(value)) != len(value):
        raise ValueError("missing_sections must not contain duplicates")
    return value


def _normalize_reason_codes(value: object) -> tuple[str, ...]:
    if type(value) is not tuple or not value:
        raise ValueError("reason_codes must be a nonempty tuple")
    for reason_code in value:
        _require_reason_code("reason_codes", reason_code)
    if len(set(value)) != len(value):
        raise ValueError("reason_codes must not contain duplicates")
    return value


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _normalize_operator_id(field_name: str, value: object) -> str | None:
    if value is None:
        return None
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a public operator identifier")
    if value == "":
        return None
    if value.strip() != value:
        raise ValueError(f"{field_name} must be a public operator identifier")
    _require_public_string(field_name, value)
    return value


def _normalize_count(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    if value != value.to_integral_value():
        raise ValueError(f"{field_name} must be integral")
    if value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return value


def _require_public_string(field_name: str, value: object) -> None:
    if type(value) is not str or not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")
    if any(fragment in value.lower() for fragment in UNSAFE_PUBLIC_TEXT_FRAGMENTS):
        raise ValueError(f"{field_name} must not contain raw public identifiers")


def _require_bool(field_name: str, value: object) -> None:
    if type(value) is not bool:
        raise ValueError(f"{field_name} must be a bool")


def _require_section(field_name: str, value: object) -> None:
    if type(value) is not str or value not in MANUAL_REVIEW_ATTESTATION_REQUIRED_SECTIONS:
        raise ValueError(f"{field_name} must be a known required section")


def _require_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in ATTESTATION_STATUSES:
        raise ValueError(f"{field_name} must be complete or incomplete")


def _require_reason_code(field_name: str, value: object) -> None:
    if type(value) is not str or value not in REASON_CODES:
        raise ValueError(f"{field_name} must contain known reason codes")


def _require_manual_next_step(field_name: str, value: object) -> None:
    if type(value) is not str or value not in MANUAL_NEXT_STEPS:
        raise ValueError(f"{field_name} must contain a known manual next step")


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if getattr(value, field_name, None) is not True:
            raise ValueError(f"{field_name} must be True for {label}")


def _require_payload_hard_flags(payload: dict[str, Any]) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if payload.get(field_name) is not True:
            raise ValueError(f"{field_name} must be True for payload")


def _require_digest(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if len(value) != 64 or any(character not in "0123456789abcdef" for character in value):
        raise ValueError(f"{field_name} must be a sha256 hex digest")


def _json_ready(value: Any) -> Any:
    if value is None:
        return None
    if is_dataclass(value) and not isinstance(value, type):
        return _json_ready(asdict(value))
    if type(value) is Decimal:
        if not value.is_finite():
            raise ValueError("Decimal payload values must be finite")
        return str(value)
    if type(value) is datetime:
        return _as_utc("payload datetime", value).isoformat()
    if type(value) is bool:
        return value
    if type(value) in (int, float):
        raise ValueError("payload must not contain binary numeric values")
    if type(value) is str:
        _require_public_string("payload string", value)
        return value
    if type(value) is dict:
        ready: dict[str, Any] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("payload keys must be strings")
            _require_public_string("payload key", key)
            ready[key] = _json_ready(item)
        return ready
    if type(value) in (list, tuple):
        return [_json_ready(item) for item in value]
    raise ValueError("payload value is not JSON serializable")


def _report_digest(report: ManualReviewAttestationCompletenessReport) -> str:
    return _report_digest_for_values(asdict(report))


def _report_digest_for_values(values: dict[str, Any]) -> str:
    payload = {key: value for key, value in values.items() if key != "report_digest"}
    encoded = json.dumps(
        _json_ready(payload),
        allow_nan=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return sha256(encoded).hexdigest()


__all__ = (
    "ATTESTATION_STATUSES",
    "DEFAULT_MANUAL_REVIEW_ATTESTATION_COMPLETENESS_CONFIG_VERSION",
    "MANUAL_REVIEW_ATTESTATION_REQUIRED_SECTIONS",
    "ManualReviewAttestationCompletenessConfig",
    "ManualReviewAttestationCompletenessInput",
    "ManualReviewAttestationCompletenessReport",
    "ManualReviewAttestationCompletenessSectionRow",
    "build_manual_review_attestation_completeness_report",
    "manual_review_attestation_completeness_report_payload",
)
