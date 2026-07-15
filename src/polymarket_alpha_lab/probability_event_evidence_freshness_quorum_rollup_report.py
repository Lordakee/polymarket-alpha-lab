"""Pure report-only reducer for probability event evidence quorum freshness."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from hashlib import sha256
import json
import re
from typing import Any


__all__ = (
    "EVIDENCE_CONTRADICTION_STATUSES",
    "EVIDENCE_QUORUM_FRESHNESS_STATUSES",
    "ProbabilityEventEvidenceFreshnessQuorumRollupReport",
    "build_probability_event_evidence_freshness_quorum_rollup_report",
    "probability_event_evidence_freshness_quorum_rollup_report_payload",
)


EVIDENCE_QUORUM_FRESHNESS_STATUSES = ("pass", "watch", "block")
EVIDENCE_CONTRADICTION_STATUSES = ("none", "minor", "unresolved")

_QUANT = Decimal("0.000001")
_ZERO = Decimal("0.000000")
_WATCH_OFFICIAL_ANCHOR_AGE_HOURS = Decimal("6.000000")
_BLOCK_OFFICIAL_ANCHOR_AGE_HOURS = Decimal("24.000000")
_DIGEST_RE = re.compile(r"^[0-9a-f]{64}$")
_REASON_CODE_RE = re.compile(r"^[a-z][a-z0-9_]{0,95}$")

_REASON_PRIORITY = (
    "official_anchor_age_expired",
    "official_anchor_age_watch_stale",
    "independent_source_quorum_gap",
    "fresh_independent_source_quorum_gap",
    "minor_contradiction_present",
    "unresolved_contradiction_present",
    "evidence_freshness_quorum_pass",
)

_MANUAL_NEXT_STEPS = (
    "proceed_with_readonly_evidence_packet",
    "refresh_official_anchor_before_packet_use",
    "refresh_evidence_and_rebuild_packet_before_reuse",
    "add_independent_sources_before_packet_use",
    "add_fresh_independent_sources_before_packet_use",
    "manual_review_contradictions_before_packet_use",
    "resolve_contradictions_before_packet_use",
)


@dataclass(frozen=True)
class ProbabilityEventEvidenceFreshnessQuorumRollupReport:
    official_anchor_age_hours: Decimal
    independent_source_count: Decimal
    fresh_independent_source_count: Decimal
    required_quorum_count: Decimal
    contradiction_status: str
    quorum_freshness_status: str
    reason_codes: tuple[str, ...]
    manual_next_step: str
    digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    @property
    def public_payload(self) -> dict[str, Any]:
        return probability_event_evidence_freshness_quorum_rollup_report_payload(self)

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ProbabilityEventEvidenceFreshnessQuorumRollupReport:
            raise TypeError(
                "ProbabilityEventEvidenceFreshnessQuorumRollupReport cannot be subclassed",
            )

    def __post_init__(self) -> None:
        if type(self) is not ProbabilityEventEvidenceFreshnessQuorumRollupReport:
            raise ValueError(
                "report must be exactly ProbabilityEventEvidenceFreshnessQuorumRollupReport",
            )
        for field_name in (
            "official_anchor_age_hours",
            "independent_source_count",
            "fresh_independent_source_count",
            "required_quorum_count",
        ):
            value = getattr(self, field_name)
            if field_name.endswith("_count"):
                value = _require_whole_decimal(field_name, value)
            else:
                value = _require_decimal(field_name, value)
            object.__setattr__(self, field_name, value)
        if self.fresh_independent_source_count > self.independent_source_count:
            raise ValueError(
                "fresh_independent_source_count must not exceed independent_source_count",
            )
        object.__setattr__(
            self,
            "contradiction_status",
            _require_supported(
                "contradiction_status",
                self.contradiction_status,
                EVIDENCE_CONTRADICTION_STATUSES,
            ),
        )
        object.__setattr__(
            self,
            "quorum_freshness_status",
            _require_supported(
                "quorum_freshness_status",
                self.quorum_freshness_status,
                EVIDENCE_QUORUM_FRESHNESS_STATUSES,
            ),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes),
        )
        object.__setattr__(
            self,
            "manual_next_step",
            _require_supported(
                "manual_next_step",
                self.manual_next_step,
                _MANUAL_NEXT_STEPS,
            ),
        )
        _require_digest("digest", self.digest)
        _require_hard_flags(self)
        _validate_report_consistency(self)
        expected_digest = _digest_payload(_payload_core(self, include_digest=False))
        if self.digest != expected_digest:
            raise ValueError("digest must match report payload")


def build_probability_event_evidence_freshness_quorum_rollup_report(
    *,
    official_anchor_age_hours: Decimal,
    independent_source_count: Decimal,
    fresh_independent_source_count: Decimal,
    required_quorum_count: Decimal,
    contradiction_status: str,
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> ProbabilityEventEvidenceFreshnessQuorumRollupReport:
    values = {
        "official_anchor_age_hours": _require_decimal(
            "official_anchor_age_hours",
            official_anchor_age_hours,
        ),
        "independent_source_count": _require_whole_decimal(
            "independent_source_count",
            independent_source_count,
        ),
        "fresh_independent_source_count": _require_whole_decimal(
            "fresh_independent_source_count",
            fresh_independent_source_count,
        ),
        "required_quorum_count": _require_whole_decimal(
            "required_quorum_count",
            required_quorum_count,
        ),
        "contradiction_status": _require_supported(
            "contradiction_status",
            contradiction_status,
            EVIDENCE_CONTRADICTION_STATUSES,
        ),
        "paper_only": paper_only,
        "report_only": report_only,
        "readonly": readonly,
    }
    if values["fresh_independent_source_count"] > values["independent_source_count"]:
        raise ValueError(
            "fresh_independent_source_count must not exceed independent_source_count",
        )
    _require_hard_flags_from_values(values)
    reason_codes = _reason_codes(
        official_anchor_age_hours=values["official_anchor_age_hours"],
        independent_source_count=values["independent_source_count"],
        fresh_independent_source_count=values["fresh_independent_source_count"],
        required_quorum_count=values["required_quorum_count"],
        contradiction_status=values["contradiction_status"],
    )
    status = _status_from_reason_codes(reason_codes)
    values["quorum_freshness_status"] = status
    values["reason_codes"] = reason_codes
    values["manual_next_step"] = _manual_next_step(reason_codes)
    values["digest"] = _digest_payload(_payload_core_from_values(values))
    return ProbabilityEventEvidenceFreshnessQuorumRollupReport(**values)


def probability_event_evidence_freshness_quorum_rollup_report_payload(
    report: ProbabilityEventEvidenceFreshnessQuorumRollupReport,
) -> dict[str, Any]:
    if type(report) is not ProbabilityEventEvidenceFreshnessQuorumRollupReport:
        raise ValueError(
            "report must be a ProbabilityEventEvidenceFreshnessQuorumRollupReport",
        )
    _normalize_reason_codes(report.reason_codes)
    payload = _payload_core(report, include_digest=True)
    _reject_numeric_payload_values(payload)
    return payload


def _reason_codes(
    *,
    official_anchor_age_hours: Decimal,
    independent_source_count: Decimal,
    fresh_independent_source_count: Decimal,
    required_quorum_count: Decimal,
    contradiction_status: str,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    if official_anchor_age_hours >= _BLOCK_OFFICIAL_ANCHOR_AGE_HOURS:
        reason_codes.append("official_anchor_age_expired")
    elif official_anchor_age_hours >= _WATCH_OFFICIAL_ANCHOR_AGE_HOURS:
        reason_codes.append("official_anchor_age_watch_stale")
    if independent_source_count < required_quorum_count:
        reason_codes.append("independent_source_quorum_gap")
    if fresh_independent_source_count < required_quorum_count:
        reason_codes.append("fresh_independent_source_quorum_gap")
    if contradiction_status == "minor":
        reason_codes.append("minor_contradiction_present")
    elif contradiction_status == "unresolved":
        reason_codes.append("unresolved_contradiction_present")
    if not reason_codes:
        reason_codes.append("evidence_freshness_quorum_pass")
    return _normalize_reason_codes(tuple(reason_codes))


def _status_from_reason_codes(reason_codes: tuple[str, ...]) -> str:
    block_reasons = {
        "official_anchor_age_expired",
        "independent_source_quorum_gap",
        "fresh_independent_source_quorum_gap",
        "unresolved_contradiction_present",
    }
    if any(reason_code in block_reasons for reason_code in reason_codes):
        return "block"
    if reason_codes == ("evidence_freshness_quorum_pass",):
        return "pass"
    return "watch"


def _manual_next_step(reason_codes: tuple[str, ...]) -> str:
    if "unresolved_contradiction_present" in reason_codes:
        return "resolve_contradictions_before_packet_use"
    if "official_anchor_age_expired" in reason_codes:
        return "refresh_evidence_and_rebuild_packet_before_reuse"
    if "fresh_independent_source_quorum_gap" in reason_codes:
        return "add_fresh_independent_sources_before_packet_use"
    if "independent_source_quorum_gap" in reason_codes:
        return "add_independent_sources_before_packet_use"
    if "minor_contradiction_present" in reason_codes:
        return "manual_review_contradictions_before_packet_use"
    if "official_anchor_age_watch_stale" in reason_codes:
        return "refresh_official_anchor_before_packet_use"
    return "proceed_with_readonly_evidence_packet"


def _validate_report_consistency(
    report: ProbabilityEventEvidenceFreshnessQuorumRollupReport,
) -> None:
    expected_reason_codes = _reason_codes(
        official_anchor_age_hours=report.official_anchor_age_hours,
        independent_source_count=report.independent_source_count,
        fresh_independent_source_count=report.fresh_independent_source_count,
        required_quorum_count=report.required_quorum_count,
        contradiction_status=report.contradiction_status,
    )
    if report.reason_codes != expected_reason_codes:
        raise ValueError("reason_codes must match report inputs")
    if report.quorum_freshness_status != _status_from_reason_codes(report.reason_codes):
        raise ValueError("quorum_freshness_status must match reason_codes")
    if report.manual_next_step != _manual_next_step(report.reason_codes):
        raise ValueError("manual_next_step must match reason_codes")


def _payload_core(
    report: ProbabilityEventEvidenceFreshnessQuorumRollupReport,
    *,
    include_digest: bool,
) -> dict[str, Any]:
    payload = {
        "official_anchor_age_hours": _decimal_to_string(
            report.official_anchor_age_hours,
        ),
        "independent_source_count": _decimal_to_string(report.independent_source_count),
        "fresh_independent_source_count": _decimal_to_string(
            report.fresh_independent_source_count,
        ),
        "required_quorum_count": _decimal_to_string(report.required_quorum_count),
        "contradiction_status": report.contradiction_status,
        "quorum_freshness_status": report.quorum_freshness_status,
        "reason_codes": list(report.reason_codes),
        "manual_next_step": report.manual_next_step,
        "paper_only": report.paper_only,
        "report_only": report.report_only,
        "readonly": report.readonly,
    }
    if include_digest:
        payload["digest"] = report.digest
    return payload


def _payload_core_from_values(values: dict[str, object]) -> dict[str, Any]:
    return {
        "official_anchor_age_hours": _decimal_to_string(
            values["official_anchor_age_hours"],
        ),
        "independent_source_count": _decimal_to_string(
            values["independent_source_count"],
        ),
        "fresh_independent_source_count": _decimal_to_string(
            values["fresh_independent_source_count"],
        ),
        "required_quorum_count": _decimal_to_string(values["required_quorum_count"]),
        "contradiction_status": values["contradiction_status"],
        "quorum_freshness_status": values["quorum_freshness_status"],
        "reason_codes": list(values["reason_codes"]),
        "manual_next_step": values["manual_next_step"],
        "paper_only": values["paper_only"],
        "report_only": values["report_only"],
        "readonly": values["readonly"],
    }


def _digest_payload(payload: dict[str, Any]) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return sha256(encoded.encode("utf-8")).hexdigest()


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    if value < _ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return value.quantize(_QUANT)


def _require_whole_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value != decimal_value.to_integral_value():
        raise ValueError(f"{field_name} must be an integer Decimal")
    return decimal_value


def _decimal_to_string(value: object) -> str:
    if type(value) is not Decimal:
        raise ValueError("numeric payload values must be Decimal")
    return f"{value.quantize(_QUANT):f}"


def _require_supported(
    field_name: str,
    value: object,
    supported_values: tuple[str, ...],
) -> str:
    if type(value) is not str or value not in supported_values:
        raise ValueError(f"{field_name} must be supported")
    return value


def _normalize_reason_codes(value: object) -> tuple[str, ...]:
    if type(value) is not tuple or not value:
        raise ValueError("reason_codes must be a non-empty tuple")
    normalized: list[str] = []
    seen: set[str] = set()
    for reason_code in value:
        if type(reason_code) is not str or not _REASON_CODE_RE.fullmatch(reason_code):
            raise ValueError("reason_code must be lower snake case")
        if reason_code not in _REASON_PRIORITY:
            raise ValueError("reason_code must be supported")
        if reason_code not in seen:
            normalized.append(reason_code)
            seen.add(reason_code)
    return tuple(
        reason_code for reason_code in _REASON_PRIORITY if reason_code in seen
    )


def _require_digest(field_name: str, value: object) -> str:
    if type(value) is not str or _DIGEST_RE.fullmatch(value) is None:
        raise ValueError(f"{field_name} must be a sha256 hex digest")
    return value


def _require_hard_flags(
    report: ProbabilityEventEvidenceFreshnessQuorumRollupReport,
) -> None:
    _require_hard_flags_from_values(
        {
            "paper_only": report.paper_only,
            "report_only": report.report_only,
            "readonly": report.readonly,
        },
    )


def _require_hard_flags_from_values(values: dict[str, object]) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if values.get(field_name) is not True:
            raise ValueError(f"{field_name} must be True")


def _reject_numeric_payload_values(value: object) -> None:
    if type(value) is int or type(value) is float or type(value) is Decimal:
        raise ValueError("numeric payload values must be serialized strings")
    if isinstance(value, dict):
        for item in value.values():
            _reject_numeric_payload_values(item)
    elif isinstance(value, list):
        for item in value:
            _reject_numeric_payload_values(item)
