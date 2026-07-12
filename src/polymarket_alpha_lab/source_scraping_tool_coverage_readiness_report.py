"""Read-only Phase 1 source scraping tool coverage readiness report."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
import hashlib
import json
from typing import Any


__all__ = (
    "SourceScrapingToolCoverageReadinessInput",
    "SourceScrapingToolCoverageReadinessReport",
    "build_source_scraping_tool_coverage_readiness_report",
)


ZERO = Decimal("0")
ONE = Decimal("1")

STATUSES = ("ready", "watch", "blocked")
SHA256_LENGTH = 64


class _NoPublicSubclass:
    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if _NoPublicSubclass not in cls.__bases__:
            raise TypeError(f"{cls.__name__} does not support subclassing")


@dataclass(frozen=True)
class SourceScrapingToolCoverageReadinessInput(_NoPublicSubclass):
    agent_reach_available: bool
    scrapling_available: bool
    official_api_available: bool
    browser_capture_available: bool
    source_snapshot_digest_present: bool
    fallback_path_count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, SourceScrapingToolCoverageReadinessInput, "input")
        for field_name in (
            "agent_reach_available",
            "scrapling_available",
            "official_api_available",
            "browser_capture_available",
            "source_snapshot_digest_present",
        ):
            _require_bool(field_name, getattr(self, field_name))
        object.__setattr__(
            self,
            "fallback_path_count",
            _require_nonnegative_whole_decimal(
                "fallback_path_count",
                self.fallback_path_count,
            ),
        )
        _require_hard_flags("input", self)


@dataclass(frozen=True)
class SourceScrapingToolCoverageReadinessReport(_NoPublicSubclass):
    agent_reach_available: bool
    scrapling_available: bool
    official_api_available: bool
    browser_capture_available: bool
    source_snapshot_digest_present: bool
    fallback_path_count: Decimal
    tool_path_count: Decimal
    coverage_status: str
    reason_codes: tuple[str, ...]
    manual_next_step: str
    payload_digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, SourceScrapingToolCoverageReadinessReport, "report")
        for field_name in (
            "agent_reach_available",
            "scrapling_available",
            "official_api_available",
            "browser_capture_available",
            "source_snapshot_digest_present",
        ):
            _require_bool(field_name, getattr(self, field_name))
        for field_name in ("fallback_path_count", "tool_path_count"):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_whole_decimal(field_name, getattr(self, field_name)),
            )
        _require_status("coverage_status", self.coverage_status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes),
        )
        _require_manual_next_step(self.manual_next_step)
        _require_digest_or_empty("payload_digest", self.payload_digest)
        _require_hard_flags("report", self)
        _validate_report(self)

    @property
    def public_payload(self) -> dict[str, object]:
        payload = _payload_without_digest(self)
        payload["payload_digest"] = self.payload_digest
        _validate_public_payload(payload)
        return payload


def build_source_scraping_tool_coverage_readiness_report(
    readiness_input: SourceScrapingToolCoverageReadinessInput,
) -> SourceScrapingToolCoverageReadinessReport:
    if type(readiness_input) is not SourceScrapingToolCoverageReadinessInput:
        raise ValueError(
            "readiness_input must be a SourceScrapingToolCoverageReadinessInput",
        )
    _require_hard_flags("input", readiness_input)
    tool_path_count = _tool_path_count(readiness_input)
    reason_codes = _reason_codes(readiness_input, tool_path_count)
    coverage_status = _coverage_status(reason_codes)
    report_without_digest = SourceScrapingToolCoverageReadinessReport(
        agent_reach_available=readiness_input.agent_reach_available,
        scrapling_available=readiness_input.scrapling_available,
        official_api_available=readiness_input.official_api_available,
        browser_capture_available=readiness_input.browser_capture_available,
        source_snapshot_digest_present=readiness_input.source_snapshot_digest_present,
        fallback_path_count=readiness_input.fallback_path_count,
        tool_path_count=tool_path_count,
        coverage_status=coverage_status,
        reason_codes=reason_codes,
        manual_next_step=_manual_next_step(reason_codes),
        payload_digest="",
    )
    return SourceScrapingToolCoverageReadinessReport(
        agent_reach_available=report_without_digest.agent_reach_available,
        scrapling_available=report_without_digest.scrapling_available,
        official_api_available=report_without_digest.official_api_available,
        browser_capture_available=report_without_digest.browser_capture_available,
        source_snapshot_digest_present=(
            report_without_digest.source_snapshot_digest_present
        ),
        fallback_path_count=report_without_digest.fallback_path_count,
        tool_path_count=report_without_digest.tool_path_count,
        coverage_status=report_without_digest.coverage_status,
        reason_codes=report_without_digest.reason_codes,
        manual_next_step=report_without_digest.manual_next_step,
        payload_digest=_payload_digest(_payload_without_digest(report_without_digest)),
    )


def _tool_path_count(
    readiness_input: SourceScrapingToolCoverageReadinessInput,
) -> Decimal:
    count = ZERO
    for available in (
        readiness_input.agent_reach_available,
        readiness_input.scrapling_available,
        readiness_input.official_api_available,
        readiness_input.browser_capture_available,
    ):
        if available:
            count += ONE
    return count


def _reason_codes(
    readiness_input: SourceScrapingToolCoverageReadinessInput,
    tool_path_count: Decimal,
) -> tuple[str, ...]:
    codes: set[str] = set()
    if tool_path_count == ZERO:
        codes.add("collection_tool_missing")
    if not readiness_input.agent_reach_available:
        codes.add("agent_reach_missing")
    if not readiness_input.scrapling_available:
        codes.add("scrapling_missing")
    if not readiness_input.official_api_available:
        codes.add("official_api_missing")
    if not readiness_input.browser_capture_available:
        codes.add("browser_capture_missing")
    if not readiness_input.source_snapshot_digest_present:
        codes.add("source_snapshot_digest_missing")
    if readiness_input.fallback_path_count == ZERO:
        codes.add("fallback_path_missing")
    if tool_path_count == ONE:
        codes.add("single_collection_tool_path")

    if _has_blocking_reason(codes):
        codes.add("coverage_blocked")
    elif codes:
        codes.add("coverage_watch")
    else:
        codes.add("coverage_ready")
    return tuple(sorted(codes))


def _coverage_status(reason_codes: tuple[str, ...]) -> str:
    if "coverage_blocked" in reason_codes:
        return "blocked"
    if "coverage_watch" in reason_codes:
        return "watch"
    return "ready"


def _manual_next_step(reason_codes: tuple[str, ...]) -> str:
    if "collection_tool_missing" in reason_codes:
        return "Add at least one readonly paper collection tool before source review."
    if "source_snapshot_digest_missing" in reason_codes:
        return "Add a public source snapshot digest before readiness review."
    if "fallback_path_missing" in reason_codes:
        return "Record at least one manual fallback path before relying on tool coverage."
    if "coverage_watch" in reason_codes:
        return "Add missing readonly collection paths or record the manual review rationale."
    return "Continue paper-only source coverage review with the current tool map."


def _has_blocking_reason(reason_codes: set[str]) -> bool:
    return bool(
        {
            "collection_tool_missing",
            "source_snapshot_digest_missing",
            "fallback_path_missing",
        }
        & reason_codes,
    )


def _payload_without_digest(
    report: SourceScrapingToolCoverageReadinessReport,
) -> dict[str, object]:
    return {
        "agent_reach_available": report.agent_reach_available,
        "scrapling_available": report.scrapling_available,
        "official_api_available": report.official_api_available,
        "browser_capture_available": report.browser_capture_available,
        "source_snapshot_digest_present": report.source_snapshot_digest_present,
        "fallback_path_count": str(report.fallback_path_count),
        "tool_path_count": str(report.tool_path_count),
        "coverage_status": report.coverage_status,
        "reason_codes": list(report.reason_codes),
        "manual_next_step": report.manual_next_step,
        "paper_only": report.paper_only,
        "report_only": report.report_only,
        "readonly": report.readonly,
    }


def _payload_digest(payload: dict[str, object]) -> str:
    encoded = json.dumps(payload, separators=(",", ":"), sort_keys=True).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _validate_report(report: SourceScrapingToolCoverageReadinessReport) -> None:
    expected_tool_count = _tool_path_count(
        SourceScrapingToolCoverageReadinessInput(
            agent_reach_available=report.agent_reach_available,
            scrapling_available=report.scrapling_available,
            official_api_available=report.official_api_available,
            browser_capture_available=report.browser_capture_available,
            source_snapshot_digest_present=report.source_snapshot_digest_present,
            fallback_path_count=report.fallback_path_count,
        ),
    )
    if report.tool_path_count != expected_tool_count:
        raise ValueError("tool_path_count must match available tool flags")
    expected_reasons = _reason_codes(
        SourceScrapingToolCoverageReadinessInput(
            agent_reach_available=report.agent_reach_available,
            scrapling_available=report.scrapling_available,
            official_api_available=report.official_api_available,
            browser_capture_available=report.browser_capture_available,
            source_snapshot_digest_present=report.source_snapshot_digest_present,
            fallback_path_count=report.fallback_path_count,
        ),
        report.tool_path_count,
    )
    if report.reason_codes != expected_reasons:
        raise ValueError("reason_codes must match coverage inputs")
    if report.coverage_status != _coverage_status(report.reason_codes):
        raise ValueError("coverage_status must match reason_codes")
    if report.manual_next_step != _manual_next_step(report.reason_codes):
        raise ValueError("manual_next_step must match reason_codes")
    if report.payload_digest:
        expected_digest = _payload_digest(_payload_without_digest(report))
        if report.payload_digest != expected_digest:
            raise ValueError("payload_digest must match public payload")


def _validate_public_payload(payload: dict[str, object]) -> None:
    _require_digest_or_empty("payload_digest", payload.get("payload_digest"))
    for value in _walk_payload_values(payload):
        if type(value) in (int, float):
            raise ValueError("public_payload must not expose numeric primitives")


def _walk_payload_values(value: object) -> tuple[object, ...]:
    values: list[object] = []
    if isinstance(value, dict):
        for field_name, item in value.items():
            values.extend(_walk_payload_values(field_name))
            values.extend(_walk_payload_values(item))
    elif isinstance(value, list):
        for item in value:
            values.extend(_walk_payload_values(item))
    else:
        values.append(value)
    return tuple(values)


def _require_exact_type(value: object, expected_type: type[object], label: str) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{label} must be a {expected_type.__name__}")


def _require_bool(field_name: str, value: object) -> None:
    if type(value) is not bool:
        raise ValueError(f"{field_name} must be a bool")


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    try:
        normalized = Decimal(value)
    except InvalidOperation as exc:
        raise ValueError(f"{field_name} must be finite") from exc
    if not normalized.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return normalized


def _require_nonnegative_whole_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{field_name} must be a whole count")
    return normalized


def _require_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in STATUSES:
        raise ValueError(f"{field_name} must be one of {STATUSES}")


def _normalize_reason_codes(values: object) -> tuple[str, ...]:
    if type(values) is not tuple or not values:
        raise ValueError("reason_codes must be a nonempty tuple")
    normalized = []
    for value in values:
        _require_reason_code("reason_codes", value)
        normalized.append(value)
    return tuple(sorted(set(normalized)))


def _require_reason_code(field_name: str, value: object) -> None:
    if type(value) is not str or not value or value.strip() != value:
        raise ValueError(f"{field_name} must be nonempty deterministic code text")
    allowed = "abcdefghijklmnopqrstuvwxyz0123456789_"
    if any(character not in allowed for character in value):
        raise ValueError(f"{field_name} must contain deterministic code text")


def _require_manual_next_step(value: object) -> None:
    if type(value) is not str or not value or value.strip() != value:
        raise ValueError("manual_next_step must be a nonempty public string")


def _require_digest_or_empty(field_name: str, value: object) -> None:
    if value == "":
        return
    if type(value) is not str or len(value) != SHA256_LENGTH:
        raise ValueError(f"{field_name} must be a sha256 hex digest")
    if any(character not in "0123456789abcdef" for character in value):
        raise ValueError(f"{field_name} must be a sha256 hex digest")


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if getattr(value, field_name, None) is not True:
            raise ValueError(f"{label} {field_name} must be True")
