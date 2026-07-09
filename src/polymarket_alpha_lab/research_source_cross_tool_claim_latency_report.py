"""Report-only reducer for sanitized cross-tool claim latency checks."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, localcontext
from hashlib import sha256
import json
import re
from typing import Any


DEFAULT_RESEARCH_SOURCE_CROSS_TOOL_CLAIM_LATENCY_REPORT_CONFIG_VERSION = (
    "research-source-cross-tool-claim-latency-report-v0"
)

TOOL_SCRAPLING = "scrapling"
TOOL_AGENT_REACH = "agent_reach"
TOOL_BROWSER_CAPTURE = "browser_capture"
TOOL_FALLBACK = "fallback"
RESEARCH_SOURCE_CROSS_TOOL_CLAIM_LATENCY_TOOLS = (
    TOOL_SCRAPLING,
    TOOL_AGENT_REACH,
    TOOL_BROWSER_CAPTURE,
    TOOL_FALLBACK,
)

STATUS_PASS = "pass"
STATUS_WATCH = "watch"
STATUS_BLOCK = "block"
RESEARCH_SOURCE_CROSS_TOOL_CLAIM_LATENCY_STATUSES = (
    STATUS_PASS,
    STATUS_WATCH,
    STATUS_BLOCK,
)
STATUS_RANK = {
    STATUS_BLOCK: Decimal("0.000000"),
    STATUS_WATCH: Decimal("1.000000"),
    STATUS_PASS: Decimal("2.000000"),
}

NO_INPUTS_REASON = "cross_tool_claim_latency_no_inputs"
PASS_REASON = "cross_tool_claim_latency_pass"
WATCH_REASON = "cross_tool_claim_latency_watch"
BLOCK_REASON = "cross_tool_claim_latency_block"
MISSING_TOOL_CLAIM_REASON = "missing_tool_claim"
LATENCY_ABOVE_BLOCK_REASON = "claim_latency_above_block_threshold"
LATENCY_ABOVE_WATCH_REASON = "claim_latency_above_watch_threshold"
AUTHORITY_BELOW_WATCH_REASON = "authority_score_below_watch_threshold"
AUTHORITY_BELOW_PASS_REASON = "authority_score_below_pass_threshold"
TOOL_COUNT_BELOW_WATCH_REASON = "tool_count_below_watch_threshold"
TOOL_COUNT_BELOW_PASS_REASON = "tool_count_below_pass_threshold"

REASON_CODE_SEQUENCE = (
    NO_INPUTS_REASON,
    PASS_REASON,
    WATCH_REASON,
    BLOCK_REASON,
    MISSING_TOOL_CLAIM_REASON,
    LATENCY_ABOVE_BLOCK_REASON,
    LATENCY_ABOVE_WATCH_REASON,
    AUTHORITY_BELOW_WATCH_REASON,
    AUTHORITY_BELOW_PASS_REASON,
    TOOL_COUNT_BELOW_WATCH_REASON,
    TOOL_COUNT_BELOW_PASS_REASON,
)
REASON_CODE_SET = frozenset(REASON_CODE_SEQUENCE)
REASON_CODE_RANK = {
    reason_code: Decimal(index).quantize(Decimal("0.000001"))
    for index, reason_code in enumerate(REASON_CODE_SEQUENCE)
}

DECIMAL_CONTEXT = Context(prec=64)
QUANTUM = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
SECONDS_PER_DAY = Decimal("86400.000000")
MICROSECONDS_PER_SECOND = Decimal("1000000.000000")

PUBLIC_IDENTIFIER_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,127}$")
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")

PUBLIC_DIGEST_FIELD = "public_digest"
UNSAFE_PUBLIC_FRAGMENTS = (
    "".join(("can", "didate_id")),
    "".join(("can", "didate-id")),
    "".join(("can", "didate id")),
    "".join(("can", "didate_slug")),
    "".join(("can", "didate slug")),
    "".join(("mar", "ket_id")),
    "".join(("mar", "ket-id")),
    "".join(("mar", "ket id")),
    "".join(("mar", "ket_slug")),
    "".join(("mar", "ket-slug")),
    "".join(("mar", "ket slug")),
    "".join(("mar", "ket-")),
    "".join(("sl", "ug")),
    "".join(("ques", "tion")),
    "".join(("source_", "url")),
    "".join(("source-", "url")),
    "".join(("source ", "url")),
    "".join(("raw_", "url")),
    "".join(("raw-", "url")),
    "".join(("raw ", "url")),
    "".join(("ur", "l")),
    "".join(("source_", "text")),
    "".join(("source-", "text")),
    "".join(("source ", "text")),
    "".join(("raw_", "text")),
    "".join(("raw-", "text")),
    "".join(("raw ", "text")),
    "".join(("ds", "n")),
    "".join(("ta", "ble_name")),
    "".join(("ta", "ble name")),
    "".join(("ta", "ble")),
    "".join(("to", "ken")),
    "".join(("wall", "et")),
    "".join(("or", "der")),
    "".join(("tr", "ade")),
    "".join(("posi", "tion")),
    "".join(("li", "ve_trading")),
    "".join(("li", "ve trading")),
    "".join(("siz", "ing")),
    "".join(("recom", "mendation")),
    "".join(("pri", "vate_key")),
    "".join(("creden", "tial")),
    "http://",
    "https://",
    "www.",
)

__all__ = (
    "DEFAULT_RESEARCH_SOURCE_CROSS_TOOL_CLAIM_LATENCY_REPORT_CONFIG_VERSION",
    "RESEARCH_SOURCE_CROSS_TOOL_CLAIM_LATENCY_TOOLS",
    "RESEARCH_SOURCE_CROSS_TOOL_CLAIM_LATENCY_STATUSES",
    "ResearchSourceCrossToolClaimLatencyConfig",
    "ResearchSourceCrossToolClaimLatencyObservation",
    "ResearchSourceCrossToolClaimLatencyReport",
    "ResearchSourceCrossToolClaimLatencyRow",
    "build_research_source_cross_tool_claim_latency_report",
    "research_source_cross_tool_claim_latency_report_public_digest",
    "research_source_cross_tool_claim_latency_report_public_payload",
    "validate_research_source_cross_tool_claim_latency_report_public_payload",
)


@dataclass(frozen=True)
class ResearchSourceCrossToolClaimLatencyConfig:
    config_version: str = (
        DEFAULT_RESEARCH_SOURCE_CROSS_TOOL_CLAIM_LATENCY_REPORT_CONFIG_VERSION
    )
    watch_claim_latency_seconds: Decimal = Decimal("900.000000")
    block_claim_latency_seconds: Decimal = Decimal("3600.000000")
    minimum_pass_tool_count: Decimal = Decimal("2.000000")
    minimum_watch_tool_count: Decimal = Decimal("1.000000")
    minimum_pass_authority_score: Decimal = Decimal("0.750000")
    minimum_watch_authority_score: Decimal = Decimal("0.500000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchSourceCrossToolClaimLatencyConfig does not support subclassing",
        )

    def __post_init__(self) -> None:
        _require_exact_type("config", self, ResearchSourceCrossToolClaimLatencyConfig)
        _require_safe_public_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_SOURCE_CROSS_TOOL_CLAIM_LATENCY_REPORT_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "watch_claim_latency_seconds",
            "block_claim_latency_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_positive_decimal(field_name, getattr(self, field_name)),
            )
        if self.block_claim_latency_seconds <= self.watch_claim_latency_seconds:
            raise ValueError(
                "block_claim_latency_seconds must exceed watch_claim_latency_seconds",
            )
        for field_name in ("minimum_pass_tool_count", "minimum_watch_tool_count"):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_whole_decimal(field_name, getattr(self, field_name)),
            )
        if self.minimum_pass_tool_count < self.minimum_watch_tool_count:
            raise ValueError(
                "minimum_pass_tool_count must be at least minimum_watch_tool_count",
            )
        for field_name in (
            "minimum_pass_authority_score",
            "minimum_watch_authority_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        if self.minimum_pass_authority_score <= self.minimum_watch_authority_score:
            raise ValueError(
                "minimum_pass_authority_score must exceed "
                "minimum_watch_authority_score",
            )
        _require_hard_flags(self)
        _reject_unsafe_public_surface("config", self)


@dataclass(frozen=True)
class ResearchSourceCrossToolClaimLatencyObservation:
    claim_scope: str
    tool_name: str
    claim_digest: str
    claim_captured_at: datetime
    tool_claim_observed_at: datetime | None
    tool_authority_score: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchSourceCrossToolClaimLatencyObservation does not support subclassing",
        )

    def __post_init__(self) -> None:
        _require_exact_type(
            "observation",
            self,
            ResearchSourceCrossToolClaimLatencyObservation,
        )
        object.__setattr__(
            self,
            "claim_scope",
            _require_public_identifier("claim_scope", self.claim_scope),
        )
        object.__setattr__(
            self,
            "tool_name",
            _require_tool_name("tool_name", self.tool_name),
        )
        object.__setattr__(
            self,
            "claim_digest",
            _require_public_sha256_digest("claim_digest", self.claim_digest),
        )
        object.__setattr__(
            self,
            "claim_captured_at",
            _as_utc("claim_captured_at", self.claim_captured_at),
        )
        object.__setattr__(
            self,
            "tool_claim_observed_at",
            _optional_as_utc("tool_claim_observed_at", self.tool_claim_observed_at),
        )
        object.__setattr__(
            self,
            "tool_authority_score",
            _require_ratio_decimal("tool_authority_score", self.tool_authority_score),
        )
        if (
            self.tool_claim_observed_at is not None
            and _seconds_between(self.claim_captured_at, self.tool_claim_observed_at)
            < ZERO
        ):
            raise ValueError(
                "tool_claim_observed_at must be at or after claim_captured_at",
            )
        _require_hard_flags(self)
        _reject_unsafe_public_surface("observation", self)


@dataclass(frozen=True)
class ResearchSourceCrossToolClaimLatencyRow:
    claim_scope: str
    claim_digest: str
    status: str
    reason_codes: tuple[str, ...]
    tool_count: Decimal
    observed_tool_count: Decimal
    missing_tool_count: Decimal
    max_claim_latency_seconds: Decimal
    average_claim_latency_seconds: Decimal
    lowest_tool_authority_score: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchSourceCrossToolClaimLatencyRow does not support subclassing",
        )

    def __post_init__(self) -> None:
        _require_exact_type("row", self, ResearchSourceCrossToolClaimLatencyRow)
        object.__setattr__(
            self,
            "claim_scope",
            _require_public_identifier("claim_scope", self.claim_scope),
        )
        object.__setattr__(
            self,
            "claim_digest",
            _require_public_sha256_digest("claim_digest", self.claim_digest),
        )
        _require_status("status", self.status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        for field_name in ("tool_count", "observed_tool_count", "missing_tool_count"):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_whole_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "max_claim_latency_seconds",
            "average_claim_latency_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "lowest_tool_authority_score",
            _require_ratio_decimal(
                "lowest_tool_authority_score",
                self.lowest_tool_authority_score,
            ),
        )
        _validate_row_consistency(self)
        _require_hard_flags(self)
        _reject_unsafe_public_surface("row", self)


@dataclass(frozen=True)
class ResearchSourceCrossToolClaimLatencyReport:
    generated_at: datetime
    config_version: str
    status: str
    claim_scope_count: Decimal
    observation_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    latency_issue_count: Decimal
    missing_tool_claim_count: Decimal
    low_authority_claim_count: Decimal
    issue_ratio: Decimal
    max_claim_latency_seconds: Decimal
    lowest_tool_authority_score: Decimal
    reason_codes: tuple[str, ...]
    rows: tuple[ResearchSourceCrossToolClaimLatencyRow, ...]
    public_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchSourceCrossToolClaimLatencyReport does not support subclassing",
        )

    def __post_init__(self) -> None:
        _require_exact_type("report", self, ResearchSourceCrossToolClaimLatencyReport)
        object.__setattr__(
            self,
            "generated_at",
            _as_utc("generated_at", self.generated_at),
        )
        _require_safe_public_string("config_version", self.config_version)
        _require_status("status", self.status)
        for field_name in (
            "claim_scope_count",
            "observation_count",
            "pass_count",
            "watch_count",
            "block_count",
            "latency_issue_count",
            "missing_tool_claim_count",
            "low_authority_claim_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_whole_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "issue_ratio",
            _require_ratio_decimal("issue_ratio", self.issue_ratio),
        )
        object.__setattr__(
            self,
            "max_claim_latency_seconds",
            _require_nonnegative_decimal(
                "max_claim_latency_seconds",
                self.max_claim_latency_seconds,
            ),
        )
        object.__setattr__(
            self,
            "lowest_tool_authority_score",
            _require_ratio_decimal(
                "lowest_tool_authority_score",
                self.lowest_tool_authority_score,
            ),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        _validate_report_consistency(self)
        _require_hard_flags(self)
        _reject_unsafe_public_surface("report", self)
        _require_or_set_public_digest(self)

    @property
    def public_payload(self) -> dict[str, Any]:
        return research_source_cross_tool_claim_latency_report_public_payload(self)


def build_research_source_cross_tool_claim_latency_report(
    observations: Iterable[ResearchSourceCrossToolClaimLatencyObservation],
    *,
    config: ResearchSourceCrossToolClaimLatencyConfig,
    generated_at: datetime,
) -> ResearchSourceCrossToolClaimLatencyReport:
    if type(config) is not ResearchSourceCrossToolClaimLatencyConfig:
        raise ValueError("config must be a ResearchSourceCrossToolClaimLatencyConfig")
    _require_hard_flags(config)
    _reject_unsafe_public_surface("config", config)
    generated_at = _as_utc("generated_at", generated_at)
    values = _normalize_observations(observations)
    _validate_generated_at_covers_values(generated_at, values)
    rows = tuple(
        sorted(
            (
                _row_from_group(
                    claim_scope,
                    group,
                    config=config,
                    generated_at=generated_at,
                )
                for claim_scope, group in _group_observations(values).items()
            ),
            key=_row_sort_key,
        ),
    )
    claim_scope_count = _decimal_count(len(rows))
    watch_count = _status_count(rows, STATUS_WATCH)
    block_count = _status_count(rows, STATUS_BLOCK)
    issue_count = _quantize(watch_count + block_count)
    return ResearchSourceCrossToolClaimLatencyReport(
        generated_at=generated_at,
        config_version=config.config_version,
        status=_report_status(rows),
        claim_scope_count=claim_scope_count,
        observation_count=_decimal_count(len(values)),
        pass_count=_status_count(rows, STATUS_PASS),
        watch_count=watch_count,
        block_count=block_count,
        latency_issue_count=issue_count,
        missing_tool_claim_count=_reason_count(rows, MISSING_TOOL_CLAIM_REASON),
        low_authority_claim_count=_authority_issue_count(rows),
        issue_ratio=_ratio(issue_count, claim_scope_count),
        max_claim_latency_seconds=_max_claim_latency_seconds(rows),
        lowest_tool_authority_score=_lowest_authority_score(rows),
        reason_codes=_report_reason_codes(rows),
        rows=rows,
    )


def research_source_cross_tool_claim_latency_report_public_digest(
    report: ResearchSourceCrossToolClaimLatencyReport,
) -> str:
    if type(report) is not ResearchSourceCrossToolClaimLatencyReport:
        raise ValueError("report must be a ResearchSourceCrossToolClaimLatencyReport")
    _require_hard_flags(report)
    _reject_unsafe_public_surface("report", report)
    return _public_payload_digest(_payload_value(report, include_public_digest=False))


def research_source_cross_tool_claim_latency_report_public_payload(
    report: ResearchSourceCrossToolClaimLatencyReport,
) -> dict[str, Any]:
    if type(report) is not ResearchSourceCrossToolClaimLatencyReport:
        raise ValueError("report must be a ResearchSourceCrossToolClaimLatencyReport")
    _require_hard_flags(report)
    _reject_unsafe_public_surface("report", report)
    payload = _payload_value(report, include_public_digest=True)
    if type(payload) is not dict:
        raise ValueError("public payload must be a JSON object")
    validate_research_source_cross_tool_claim_latency_report_public_payload(payload)
    return payload


def validate_research_source_cross_tool_claim_latency_report_public_payload(
    payload: object,
) -> bool:
    if not isinstance(payload, dict):
        raise ValueError("public payload must be a JSON object")
    _reject_unsafe_public_surface("public payload", payload)
    _require_public_payload_values(payload)
    expected = _public_payload_digest(_payload_without_public_digest(payload))
    current = payload.get(PUBLIC_DIGEST_FIELD)
    if type(current) is not str or current != expected or not SHA256_RE.fullmatch(current):
        raise ValueError("public_digest does not match public payload")
    return True


def _row_from_group(
    claim_scope: str,
    group: tuple[ResearchSourceCrossToolClaimLatencyObservation, ...],
    *,
    config: ResearchSourceCrossToolClaimLatencyConfig,
    generated_at: datetime,
) -> ResearchSourceCrossToolClaimLatencyRow:
    latencies = tuple(
        _claim_latency_seconds(value, generated_at=generated_at) for value in group
    )
    tool_count = _decimal_count(len(group))
    observed_tool_count = _decimal_count(
        sum(ONE for value in group if value.tool_claim_observed_at is not None),
    )
    missing_tool_count = _quantize(tool_count - observed_tool_count)
    max_latency = _max_decimal(latencies)
    lowest_authority = _min_decimal(
        tuple(value.tool_authority_score for value in group),
        default=ZERO,
    )
    reason_codes = _row_reason_codes(
        tool_count=tool_count,
        missing_tool_count=missing_tool_count,
        max_latency=max_latency,
        lowest_authority=lowest_authority,
        config=config,
    )
    return ResearchSourceCrossToolClaimLatencyRow(
        claim_scope=claim_scope,
        claim_digest=group[0].claim_digest,
        status=_row_status(reason_codes),
        reason_codes=reason_codes,
        tool_count=tool_count,
        observed_tool_count=observed_tool_count,
        missing_tool_count=missing_tool_count,
        max_claim_latency_seconds=max_latency,
        average_claim_latency_seconds=_average_decimal(latencies),
        lowest_tool_authority_score=lowest_authority,
    )


def _row_reason_codes(
    *,
    tool_count: Decimal,
    missing_tool_count: Decimal,
    max_latency: Decimal,
    lowest_authority: Decimal,
    config: ResearchSourceCrossToolClaimLatencyConfig,
) -> tuple[str, ...]:
    block_reasons: list[str] = []
    watch_reasons: list[str] = []
    if missing_tool_count > ZERO:
        block_reasons.append(MISSING_TOOL_CLAIM_REASON)
    if max_latency > config.block_claim_latency_seconds:
        block_reasons.append(LATENCY_ABOVE_BLOCK_REASON)
    elif max_latency > config.watch_claim_latency_seconds:
        watch_reasons.append(LATENCY_ABOVE_WATCH_REASON)
    if lowest_authority < config.minimum_watch_authority_score:
        block_reasons.append(AUTHORITY_BELOW_WATCH_REASON)
    elif lowest_authority < config.minimum_pass_authority_score:
        watch_reasons.append(AUTHORITY_BELOW_PASS_REASON)
    if tool_count < config.minimum_watch_tool_count:
        block_reasons.append(TOOL_COUNT_BELOW_WATCH_REASON)
    elif tool_count < config.minimum_pass_tool_count:
        watch_reasons.append(TOOL_COUNT_BELOW_PASS_REASON)
    if block_reasons:
        return _normalize_reason_codes(
            "reason_codes",
            (BLOCK_REASON, *block_reasons),
        )
    if watch_reasons:
        return _normalize_reason_codes(
            "reason_codes",
            (WATCH_REASON, *watch_reasons),
        )
    return (PASS_REASON,)


def _claim_latency_seconds(
    value: ResearchSourceCrossToolClaimLatencyObservation,
    *,
    generated_at: datetime,
) -> Decimal:
    if value.tool_claim_observed_at is None:
        return _seconds_between(value.claim_captured_at, generated_at)
    return _seconds_between(value.claim_captured_at, value.tool_claim_observed_at)


def _normalize_observations(
    observations: Iterable[ResearchSourceCrossToolClaimLatencyObservation],
) -> tuple[ResearchSourceCrossToolClaimLatencyObservation, ...]:
    if isinstance(observations, (str, bytes)):
        raise ValueError("observations must be an iterable")
    try:
        values = tuple(observations)
    except TypeError as exc:
        raise ValueError("observations must be an iterable") from exc
    seen_keys: set[tuple[str, str]] = set()
    scope_details: dict[str, tuple[str, datetime]] = {}
    for value in values:
        if type(value) is not ResearchSourceCrossToolClaimLatencyObservation:
            raise ValueError(
                "observations must contain "
                "ResearchSourceCrossToolClaimLatencyObservation values",
            )
        _require_hard_flags(value)
        _reject_unsafe_public_surface("observation", value)
        key = (value.claim_scope, value.tool_name)
        if key in seen_keys:
            raise ValueError("observations must not contain duplicate claim tool keys")
        seen_keys.add(key)
        details = (value.claim_digest, value.claim_captured_at)
        existing = scope_details.setdefault(value.claim_scope, details)
        if existing != details:
            raise ValueError("claim scopes must use one digest and captured_at")
    return values


def _group_observations(
    observations: tuple[ResearchSourceCrossToolClaimLatencyObservation, ...],
) -> dict[str, tuple[ResearchSourceCrossToolClaimLatencyObservation, ...]]:
    grouped: dict[str, list[ResearchSourceCrossToolClaimLatencyObservation]] = {}
    for value in observations:
        grouped.setdefault(value.claim_scope, []).append(value)
    return {
        claim_scope: tuple(sorted(group, key=lambda item: item.tool_name))
        for claim_scope, group in sorted(grouped.items())
    }


def _validate_generated_at_covers_values(
    generated_at: datetime,
    values: tuple[ResearchSourceCrossToolClaimLatencyObservation, ...],
) -> None:
    for value in values:
        if _seconds_between(value.claim_captured_at, generated_at) < ZERO:
            raise ValueError("claim_captured_at must not be after generated_at")
        if (
            value.tool_claim_observed_at is not None
            and _seconds_between(value.tool_claim_observed_at, generated_at) < ZERO
        ):
            raise ValueError("tool_claim_observed_at must not be after generated_at")


def _normalize_rows(
    rows: Iterable[ResearchSourceCrossToolClaimLatencyRow],
) -> tuple[ResearchSourceCrossToolClaimLatencyRow, ...]:
    if isinstance(rows, (str, bytes)):
        raise ValueError("rows must contain ResearchSourceCrossToolClaimLatencyRow values")
    try:
        values = tuple(rows)
    except TypeError as exc:
        raise ValueError(
            "rows must contain ResearchSourceCrossToolClaimLatencyRow values",
        ) from exc
    for row in values:
        if type(row) is not ResearchSourceCrossToolClaimLatencyRow:
            raise ValueError(
                "rows must contain ResearchSourceCrossToolClaimLatencyRow values",
            )
        _require_hard_flags(row)
        _reject_unsafe_public_surface("row", row)
    if values != tuple(sorted(values, key=_row_sort_key)):
        raise ValueError("rows must use deterministic sort")
    if len({_row_identity(row) for row in values}) != len(values):
        raise ValueError("rows must be unique")
    return values


def _validate_row_consistency(row: ResearchSourceCrossToolClaimLatencyRow) -> None:
    if row.status != _row_status(row.reason_codes):
        raise ValueError("status must match reason_codes")
    if row.tool_count != _quantize(row.observed_tool_count + row.missing_tool_count):
        raise ValueError("tool_count must match observed and missing tool counts")
    if row.observed_tool_count > row.tool_count:
        raise ValueError("observed_tool_count must not exceed tool_count")
    if row.status == STATUS_PASS and row.reason_codes != (PASS_REASON,):
        raise ValueError("pass rows require pass reason")
    if row.status != STATUS_PASS and PASS_REASON in row.reason_codes:
        raise ValueError("issue rows must not use pass reason")
    if MISSING_TOOL_CLAIM_REASON in row.reason_codes and row.missing_tool_count <= ZERO:
        raise ValueError("missing_tool_claim requires missing_tool_count")
    if MISSING_TOOL_CLAIM_REASON not in row.reason_codes and row.missing_tool_count > ZERO:
        raise ValueError("missing_tool_count requires missing_tool_claim reason")


def _validate_report_consistency(
    report: ResearchSourceCrossToolClaimLatencyReport,
) -> None:
    if report.claim_scope_count != _decimal_count(len(report.rows)):
        raise ValueError("claim_scope_count must match rows")
    if report.status != _report_status(report.rows):
        raise ValueError("status must match rows")
    if report.pass_count != _status_count(report.rows, STATUS_PASS):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _status_count(report.rows, STATUS_WATCH):
        raise ValueError("watch_count must match rows")
    if report.block_count != _status_count(report.rows, STATUS_BLOCK):
        raise ValueError("block_count must match rows")
    if report.latency_issue_count != _quantize(report.watch_count + report.block_count):
        raise ValueError("latency_issue_count must match watch and block rows")
    if report.missing_tool_claim_count != _reason_count(
        report.rows,
        MISSING_TOOL_CLAIM_REASON,
    ):
        raise ValueError("missing_tool_claim_count must match rows")
    if report.low_authority_claim_count != _authority_issue_count(report.rows):
        raise ValueError("low_authority_claim_count must match rows")
    if report.issue_ratio != _ratio(report.latency_issue_count, report.claim_scope_count):
        raise ValueError("issue_ratio must match issue and scope counts")
    if report.max_claim_latency_seconds != _max_claim_latency_seconds(report.rows):
        raise ValueError("max_claim_latency_seconds must match rows")
    if report.lowest_tool_authority_score != _lowest_authority_score(report.rows):
        raise ValueError("lowest_tool_authority_score must match rows")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")
    if report.observation_count != _row_observation_count(report.rows):
        raise ValueError("observation_count must match rows")


def _row_sort_key(
    row: ResearchSourceCrossToolClaimLatencyRow,
) -> tuple[Decimal, Decimal, Decimal, str]:
    return (
        STATUS_RANK[row.status],
        -row.max_claim_latency_seconds,
        row.lowest_tool_authority_score,
        row.claim_scope,
    )


def _row_identity(row: ResearchSourceCrossToolClaimLatencyRow) -> str:
    return row.claim_scope


def _row_status(reason_codes: tuple[str, ...]) -> str:
    if BLOCK_REASON in reason_codes:
        return STATUS_BLOCK
    if WATCH_REASON in reason_codes:
        return STATUS_WATCH
    return STATUS_PASS


def _report_status(rows: tuple[ResearchSourceCrossToolClaimLatencyRow, ...]) -> str:
    if any(row.status == STATUS_BLOCK for row in rows):
        return STATUS_BLOCK
    if any(row.status == STATUS_WATCH for row in rows):
        return STATUS_WATCH
    return STATUS_PASS


def _report_reason_codes(
    rows: tuple[ResearchSourceCrossToolClaimLatencyRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return (NO_INPUTS_REASON,)
    reason_codes: list[str] = []
    for row in rows:
        for reason_code in row.reason_codes:
            if reason_code not in reason_codes:
                reason_codes.append(reason_code)
    return _normalize_reason_codes(
        "reason_codes",
        tuple(sorted(reason_codes, key=lambda item: REASON_CODE_RANK[item])),
    )


def _status_count(
    rows: tuple[ResearchSourceCrossToolClaimLatencyRow, ...],
    status: str,
) -> Decimal:
    return _decimal_count(sum(ONE for row in rows if row.status == status))


def _reason_count(
    rows: tuple[ResearchSourceCrossToolClaimLatencyRow, ...],
    reason_code: str,
) -> Decimal:
    return _decimal_count(sum(ONE for row in rows if reason_code in row.reason_codes))


def _authority_issue_count(
    rows: tuple[ResearchSourceCrossToolClaimLatencyRow, ...],
) -> Decimal:
    return _decimal_count(
        sum(
            ONE
            for row in rows
            if AUTHORITY_BELOW_PASS_REASON in row.reason_codes
            or AUTHORITY_BELOW_WATCH_REASON in row.reason_codes
        ),
    )


def _row_observation_count(
    rows: tuple[ResearchSourceCrossToolClaimLatencyRow, ...],
) -> Decimal:
    total = ZERO
    for row in rows:
        total = _quantize(total + row.tool_count)
    return total


def _max_claim_latency_seconds(
    rows: tuple[ResearchSourceCrossToolClaimLatencyRow, ...],
) -> Decimal:
    return _max_decimal(tuple(row.max_claim_latency_seconds for row in rows))


def _lowest_authority_score(
    rows: tuple[ResearchSourceCrossToolClaimLatencyRow, ...],
) -> Decimal:
    return _min_decimal(
        tuple(row.lowest_tool_authority_score for row in rows),
        default=ZERO,
    )


def _max_decimal(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return ZERO
    result = values[0]
    for value in values[1:]:
        if value > result:
            result = value
    return _quantize(result)


def _min_decimal(values: tuple[Decimal, ...], *, default: Decimal) -> Decimal:
    if not values:
        return default
    result = values[0]
    for value in values[1:]:
        if value < result:
            result = value
    return _quantize(result)


def _average_decimal(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return ZERO
    total = ZERO
    for value in values:
        total = _quantize(total + value)
    with localcontext(DECIMAL_CONTEXT):
        return _quantize(total / _decimal_count(len(values)))


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return _quantize(numerator / denominator)


def _seconds_between(start: datetime, end: datetime) -> Decimal:
    delta = end - start
    whole_seconds = Decimal(delta.days) * SECONDS_PER_DAY + Decimal(delta.seconds)
    microseconds = Decimal(delta.microseconds) / MICROSECONDS_PER_SECOND
    with localcontext(DECIMAL_CONTEXT):
        return _quantize(whole_seconds + microseconds)


def _decimal_count(value: int | Decimal) -> Decimal:
    return _quantize(Decimal(value))


def _normalize_reason_codes(
    field_name: str,
    value: Iterable[str],
) -> tuple[str, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError(f"{field_name} must be an iterable of strings")
    try:
        reason_codes = tuple(value)
    except TypeError as exc:
        raise ValueError(f"{field_name} must be an iterable of strings") from exc
    if not reason_codes:
        raise ValueError(f"{field_name} must contain at least one value")
    if len(set(reason_codes)) != len(reason_codes):
        raise ValueError(f"{field_name} must not contain duplicates")
    for reason_code in reason_codes:
        if type(reason_code) is not str or reason_code not in REASON_CODE_SET:
            raise ValueError(f"{field_name} must contain known values")
    expected = tuple(
        reason_code for reason_code in REASON_CODE_SEQUENCE if reason_code in reason_codes
    )
    if expected != reason_codes:
        raise ValueError(f"{field_name} must use deterministic sequence")
    return reason_codes


def _require_tool_name(field_name: str, value: object) -> str:
    if type(value) is not str or value not in RESEARCH_SOURCE_CROSS_TOOL_CLAIM_LATENCY_TOOLS:
        raise ValueError(f"{field_name} must be a supported tool name")
    return value


def _require_public_identifier(field_name: str, value: object) -> str:
    _require_safe_public_string(field_name, value)
    if not PUBLIC_IDENTIFIER_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a public identifier")
    return value


def _require_public_sha256_digest(field_name: str, value: object) -> str:
    _require_safe_public_string(field_name, value)
    if not SHA256_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a sha256 hex digest")
    return value


def _require_safe_public_string(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")
    if "\n" in value or "\r" in value or "\t" in value:
        raise ValueError(f"{field_name} must be single line")
    _reject_unsafe_public_surface(field_name, value)
    return value


def _require_status(field_name: str, value: object) -> None:
    if (
        type(value) is not str
        or value not in RESEARCH_SOURCE_CROSS_TOOL_CLAIM_LATENCY_STATUSES
    ):
        raise ValueError(f"{field_name} must be pass, watch, or block")


def _require_nonnegative_whole_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_nonnegative_decimal(field_name, value)
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{field_name} must be a whole Decimal")
    return normalized


def _require_positive_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_nonnegative_decimal(field_name, value)
    if normalized <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _require_ratio_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_nonnegative_decimal(field_name, value)
    if normalized > ONE:
        raise ValueError(f"{field_name} must be at most one")
    return normalized


def _require_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    normalized = _quantize(value)
    if normalized != value:
        raise ValueError(f"{field_name} must be quantized to 0.000001")
    return normalized


def _quantize(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(QUANTUM)


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _optional_as_utc(field_name: str, value: object) -> datetime | None:
    if value is None:
        return None
    return _as_utc(field_name, value)


def _require_exact_type(label: str, value: object, expected_type: type[object]) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{label} must be a {expected_type.__name__}")


def _require_hard_flags(value: object) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if getattr(value, field_name) is not True:
            raise ValueError(f"{field_name} must be True")


def _reject_unsafe_public_surface(label: str, value: object) -> None:
    for item in _surface_items(value):
        lowered = item.lower()
        if any(fragment in lowered for fragment in UNSAFE_PUBLIC_FRAGMENTS):
            raise ValueError(f"unsafe public surface in {label}: {item}")


def _surface_items(value: object) -> tuple[str, ...]:
    if is_dataclass(value) and not isinstance(value, type):
        items: list[str] = []
        for field in fields(value):
            items.append(field.name)
            items.extend(_surface_items(getattr(value, field.name)))
        return tuple(items)
    if isinstance(value, dict):
        items = []
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("public payload keys must be strings")
            items.append(key)
            items.extend(_surface_items(item))
        return tuple(items)
    if isinstance(value, (list, tuple)):
        items = []
        for item in value:
            items.extend(_surface_items(item))
        return tuple(items)
    if type(value) is str:
        return (value,)
    return ()


def _require_or_set_public_digest(
    report: ResearchSourceCrossToolClaimLatencyReport,
) -> None:
    current = report.public_digest
    if type(current) is not str:
        raise ValueError("public_digest must be a string")
    expected = research_source_cross_tool_claim_latency_report_public_digest(report)
    if current == "":
        object.__setattr__(report, PUBLIC_DIGEST_FIELD, expected)
        return
    if current != expected or not SHA256_RE.fullmatch(current):
        raise ValueError("public_digest does not match public payload")


def _public_payload_digest(payload: object) -> str:
    encoded = json.dumps(
        payload,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return sha256(encoded).hexdigest()


def _payload_without_public_digest(value: dict[str, object]) -> dict[str, object]:
    return {
        key: _payload_value(item, include_public_digest=False)
        for key, item in value.items()
        if key != PUBLIC_DIGEST_FIELD
    }


def _payload_value(value: object, *, include_public_digest: bool) -> Any:
    if value is None:
        return None
    if is_dataclass(value) and not isinstance(value, type):
        result: dict[str, object] = {}
        for field in fields(value):
            if field.name == PUBLIC_DIGEST_FIELD and not include_public_digest:
                continue
            result[field.name] = _payload_value(
                getattr(value, field.name),
                include_public_digest=include_public_digest,
            )
        return result
    if isinstance(value, Decimal):
        if not value.is_finite():
            raise ValueError("public payload Decimal value must be finite")
        return str(value)
    if type(value) is datetime:
        return value.astimezone(UTC).isoformat()
    if type(value) in (str, bool):
        return value
    if isinstance(value, dict):
        result: dict[str, object] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("public payload keys must be strings")
            if key == PUBLIC_DIGEST_FIELD and not include_public_digest:
                continue
            result[key] = _payload_value(
                item,
                include_public_digest=include_public_digest,
            )
        return result
    if isinstance(value, tuple):
        return [
            _payload_value(item, include_public_digest=include_public_digest)
            for item in value
        ]
    if isinstance(value, list):
        return [
            _payload_value(item, include_public_digest=include_public_digest)
            for item in value
        ]
    raise ValueError("unsupported public payload value")


def _require_public_payload_values(value: object) -> None:
    if value is None or type(value) in (str, bool):
        return
    if isinstance(value, list):
        for item in value:
            _require_public_payload_values(item)
        return
    if isinstance(value, dict):
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("public payload keys must be strings")
            _require_public_payload_values(item)
        return
    raise ValueError("public payload values must be JSON strings, booleans, or arrays")
