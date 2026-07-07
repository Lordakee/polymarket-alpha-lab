"""Pure source scraping-readiness report for caller-supplied source metadata.

The module is deterministic and side-effect free. Callers provide typed source
metadata; the policy returns report-only readiness scores, statuses, and reason
codes before any external collection tool is used.
"""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable
from dataclasses import dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation
from typing import Any


__all__ = (
    "ResearchSourceScrapingReadinessConfig",
    "ResearchSourceScrapingReadinessReasonCodeCount",
    "ResearchSourceScrapingReadinessReport",
    "ResearchSourceScrapingReadinessRow",
    "ResearchSourceScrapingReadinessSource",
    "build_research_source_scraping_readiness_report",
    "research_source_scraping_readiness_report_payload",
)


DEFAULT_CONFIG_VERSION = "research-source-scraping-readiness-report-v0"
STATUSES = ("pass", "watch", "blocked")
ACCESS_POLICIES = ("allowed", "conditional", "disallowed")
STRUCTURE_STABILITIES = ("stable", "mostly_stable", "dynamic", "unstable")
VALIDATION_PATHS = (
    "independent_primary",
    "independent_secondary",
    "manual_review",
    "none",
)
FALLBACK_PATHS = (
    "independent_alternate",
    "cached_snapshot",
    "manual_review",
    "none",
)
ZERO = Decimal("0")
ONE = Decimal("1")
TWO = Decimal("2")
RATIO_QUANTUM = Decimal("0.000001")
DEFAULT_PASS_READINESS_SCORE = Decimal("0.800000")
DEFAULT_WATCH_READINESS_SCORE = Decimal("0.500000")
STRUCTURE_SCORES = {
    "stable": Decimal("1.000000"),
    "mostly_stable": Decimal("0.750000"),
    "dynamic": Decimal("0.500000"),
    "unstable": Decimal("0.100000"),
}
VALIDATION_SCORES = {
    "independent_primary": Decimal("1.000000"),
    "independent_secondary": Decimal("0.800000"),
    "manual_review": Decimal("0.500000"),
    "none": Decimal("0.000000"),
}
FALLBACK_SCORES = {
    "independent_alternate": Decimal("1.000000"),
    "cached_snapshot": Decimal("0.700000"),
    "manual_review": Decimal("0.500000"),
    "none": Decimal("0.000000"),
}
UNTESTED_FALLBACK_SCORE = Decimal("0.300000")
UNSAFE_PUBLIC_SUBSTRINGS = (
    "url",
    "text",
    "ref",
    "dsn",
    "table",
    "token",
    "http",
    "://",
    "www.",
)


@dataclass(frozen=True)
class ResearchSourceScrapingReadinessConfig:
    config_version: str = DEFAULT_CONFIG_VERSION
    pass_readiness_score: Decimal = DEFAULT_PASS_READINESS_SCORE
    watch_readiness_score: Decimal = DEFAULT_WATCH_READINESS_SCORE
    allowability_weight: Decimal = Decimal("0.250000")
    structure_weight: Decimal = Decimal("0.250000")
    cadence_weight: Decimal = Decimal("0.200000")
    validation_weight: Decimal = Decimal("0.200000")
    fallback_weight: Decimal = Decimal("0.100000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("config_version", self.config_version)
        for field_name in (
            "pass_readiness_score",
            "watch_readiness_score",
            "allowability_weight",
            "structure_weight",
            "cadence_weight",
            "validation_weight",
            "fallback_weight",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_probability_decimal(field_name, getattr(self, field_name)),
            )
        if self.pass_readiness_score <= self.watch_readiness_score:
            raise ValueError("pass_readiness_score must be greater than watch_readiness_score")
        weight_sum = _quantize(
            self.allowability_weight
            + self.structure_weight
            + self.cadence_weight
            + self.validation_weight
            + self.fallback_weight,
        )
        if weight_sum != ONE:
            raise ValueError(
                "allowability_weight, structure_weight, cadence_weight, "
                "validation_weight, and fallback_weight must sum to 1",
            )
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class ResearchSourceScrapingReadinessSource:
    private_source_id: str
    access_policy: str
    automated_collection_allowed: bool
    credential_required: bool
    credential_access_approved: bool
    structure_stability: str
    cadence_seconds: Decimal
    max_staleness_seconds: Decimal
    validation_path: str
    fallback_path: str
    fallback_tested: bool
    reason_codes: tuple[str, ...] = ()
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_private_string("private_source_id", self.private_source_id)
        _require_enum("access_policy", self.access_policy, ACCESS_POLICIES)
        for field_name in (
            "automated_collection_allowed",
            "credential_required",
            "credential_access_approved",
            "fallback_tested",
        ):
            if type(getattr(self, field_name)) is not bool:
                raise ValueError(f"{field_name} must be a bool")
        _require_enum(
            "structure_stability",
            self.structure_stability,
            STRUCTURE_STABILITIES,
        )
        object.__setattr__(
            self,
            "cadence_seconds",
            _require_positive_decimal("cadence_seconds", self.cadence_seconds),
        )
        object.__setattr__(
            self,
            "max_staleness_seconds",
            _require_positive_decimal(
                "max_staleness_seconds",
                self.max_staleness_seconds,
            ),
        )
        _require_enum("validation_path", self.validation_path, VALIDATION_PATHS)
        _require_enum("fallback_path", self.fallback_path, FALLBACK_PATHS)
        if self.fallback_path == "none" and self.fallback_tested:
            raise ValueError("fallback_tested requires a fallback_path")
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, allow_empty=True),
        )
        _require_hard_flags("source", self)


@dataclass(frozen=True)
class ResearchSourceScrapingReadinessRow:
    source_index: Decimal
    allowability_score: Decimal
    structure_score: Decimal
    cadence_score: Decimal
    validation_score: Decimal
    fallback_score: Decimal
    readiness_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "source_index",
            _require_positive_whole_decimal("source_index", self.source_index),
        )
        for field_name in (
            "allowability_score",
            "structure_score",
            "cadence_score",
            "validation_score",
            "fallback_score",
            "readiness_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_probability_decimal(field_name, getattr(self, field_name)),
            )
        _require_status("status", self.status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, allow_empty=False),
        )
        _require_hard_flags("row", self)


@dataclass(frozen=True)
class ResearchSourceScrapingReadinessReasonCodeCount:
    reason_code: str
    count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_reason_code("reason_code", self.reason_code)
        object.__setattr__(
            self,
            "count",
            _require_positive_whole_decimal("count", self.count),
        )
        _require_hard_flags("reason_code_count", self)


@dataclass(frozen=True)
class ResearchSourceScrapingReadinessReport:
    generated_at: datetime
    config_version: str
    source_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    blocked_count: Decimal
    average_readiness_score: Decimal | None
    status: str
    rows: tuple[ResearchSourceScrapingReadinessRow, ...]
    reason_code_counts: tuple[ResearchSourceScrapingReadinessReasonCodeCount, ...]
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        for field_name in ("source_count", "pass_count", "watch_count", "blocked_count"):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_whole_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "average_readiness_score",
            _require_optional_probability_decimal(
                "average_readiness_score",
                self.average_readiness_score,
            ),
        )
        _require_status("status", self.status)
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, allow_empty=False),
        )
        _require_hard_flags("report", self)
        _validate_report_consistency(self)


def build_research_source_scraping_readiness_report(
    sources: Iterable[object],
    *,
    config: ResearchSourceScrapingReadinessConfig,
    generated_at: datetime,
) -> ResearchSourceScrapingReadinessReport:
    if type(config) is not ResearchSourceScrapingReadinessConfig:
        raise ValueError("config must be a ResearchSourceScrapingReadinessConfig")
    _require_hard_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    source_items = _normalize_sources(sources)
    _reject_duplicate_private_source_ids(source_items)

    rows = tuple(
        _score_row_from_source(
            source_index=_decimal_count(index),
            source=source,
            config=config,
        )
        for index, source in enumerate(
            sorted(source_items, key=lambda item: item.private_source_id),
            start=1,
        )
    )
    reason_codes = _summary_reason_codes(rows)

    return ResearchSourceScrapingReadinessReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        source_count=_decimal_count(len(rows)),
        pass_count=_decimal_count(_status_count(rows, "pass")),
        watch_count=_decimal_count(_status_count(rows, "watch")),
        blocked_count=_decimal_count(_status_count(rows, "blocked")),
        average_readiness_score=_average_readiness_score(rows),
        status=_summary_status(reason_codes),
        rows=rows,
        reason_code_counts=_reason_code_counts(rows, reason_codes),
        reason_codes=reason_codes,
    )


def research_source_scraping_readiness_report_payload(
    report: ResearchSourceScrapingReadinessReport,
) -> dict[str, Any]:
    if type(report) is not ResearchSourceScrapingReadinessReport:
        raise ValueError("report must be a ResearchSourceScrapingReadinessReport")
    _require_hard_flags("report", report)
    payload = _payload_value(report)
    if not isinstance(payload, dict):
        raise ValueError("report payload must be a JSON object")
    _reject_unsafe_public_payload(payload)
    return payload


def _normalize_sources(
    sources: Iterable[object],
) -> tuple[ResearchSourceScrapingReadinessSource, ...]:
    if isinstance(sources, (str, bytes)):
        raise ValueError("sources must be an iterable")
    try:
        values = tuple(sources)
    except TypeError as exc:
        raise ValueError("sources must be an iterable") from exc
    for value in values:
        if type(value) is not ResearchSourceScrapingReadinessSource:
            raise ValueError(
                "sources must contain ResearchSourceScrapingReadinessSource values",
            )
        _require_hard_flags("source", value)
    return values


def _reject_duplicate_private_source_ids(
    sources: tuple[ResearchSourceScrapingReadinessSource, ...],
) -> None:
    counts = Counter(source.private_source_id for source in sources)
    if any(count > 1 for count in counts.values()):
        raise ValueError("private_source_id values must be unique")


def _score_row_from_source(
    *,
    source_index: Decimal,
    source: ResearchSourceScrapingReadinessSource,
    config: ResearchSourceScrapingReadinessConfig,
) -> ResearchSourceScrapingReadinessRow:
    allowability_score = _allowability_score(source)
    structure_score = STRUCTURE_SCORES[source.structure_stability]
    cadence_score = _cadence_score(source.cadence_seconds, source.max_staleness_seconds)
    validation_score = VALIDATION_SCORES[source.validation_path]
    fallback_score = _fallback_score(source)
    readiness_score = _quantize(
        (allowability_score * config.allowability_weight)
        + (structure_score * config.structure_weight)
        + (cadence_score * config.cadence_weight)
        + (validation_score * config.validation_weight)
        + (fallback_score * config.fallback_weight),
    )
    status = _row_status(
        source=source,
        allowability_score=allowability_score,
        validation_score=validation_score,
        fallback_score=fallback_score,
        readiness_score=readiness_score,
        config=config,
    )
    return ResearchSourceScrapingReadinessRow(
        source_index=source_index,
        allowability_score=allowability_score,
        structure_score=structure_score,
        cadence_score=cadence_score,
        validation_score=validation_score,
        fallback_score=fallback_score,
        readiness_score=readiness_score,
        status=status,
        reason_codes=_row_reason_codes(
            source=source,
            status=status,
            allowability_score=allowability_score,
            cadence_score=cadence_score,
            validation_score=validation_score,
            fallback_score=fallback_score,
        ),
    )


def _allowability_score(source: ResearchSourceScrapingReadinessSource) -> Decimal:
    if source.access_policy == "disallowed":
        return ZERO
    if not source.automated_collection_allowed:
        return ZERO
    if source.credential_required and not source.credential_access_approved:
        return ZERO
    if source.access_policy == "conditional":
        return Decimal("0.700000")
    if source.credential_required:
        return Decimal("0.800000")
    return ONE


def _cadence_score(cadence_seconds: Decimal, max_staleness_seconds: Decimal) -> Decimal:
    if cadence_seconds <= max_staleness_seconds:
        return ONE
    if cadence_seconds <= max_staleness_seconds * TWO:
        return Decimal("0.500000")
    return ZERO


def _fallback_score(source: ResearchSourceScrapingReadinessSource) -> Decimal:
    if source.fallback_path == "none":
        return ZERO
    if not source.fallback_tested:
        return UNTESTED_FALLBACK_SCORE
    return FALLBACK_SCORES[source.fallback_path]


def _row_status(
    *,
    source: ResearchSourceScrapingReadinessSource,
    allowability_score: Decimal,
    validation_score: Decimal,
    fallback_score: Decimal,
    readiness_score: Decimal,
    config: ResearchSourceScrapingReadinessConfig,
) -> str:
    if allowability_score == ZERO:
        return "blocked"
    if validation_score == ZERO and fallback_score == ZERO:
        return "blocked"
    if readiness_score < config.watch_readiness_score:
        return "blocked"
    if readiness_score < config.pass_readiness_score:
        return "watch"
    if source.access_policy != "allowed":
        return "watch"
    if source.credential_required:
        return "watch"
    if source.structure_stability != "stable":
        return "watch"
    if source.fallback_path == "none" or not source.fallback_tested:
        return "watch"
    return "pass"


def _row_reason_codes(
    *,
    source: ResearchSourceScrapingReadinessSource,
    status: str,
    allowability_score: Decimal,
    cadence_score: Decimal,
    validation_score: Decimal,
    fallback_score: Decimal,
) -> tuple[str, ...]:
    reason_codes = {f"scraping_readiness_{status}"}
    if allowability_score == ZERO:
        reason_codes.add("source_access_blocked")
    elif source.access_policy == "conditional":
        reason_codes.add("source_access_conditional")
    else:
        reason_codes.add("source_access_allowed")
    reason_codes.add(
        "automation_allowed"
        if source.automated_collection_allowed
        else "automation_not_allowed",
    )
    if source.credential_required and source.credential_access_approved:
        reason_codes.add("credential_gate_ready")
    if source.credential_required and not source.credential_access_approved:
        reason_codes.add("credential_gate_blocked")
    if source.structure_stability in ("stable", "mostly_stable"):
        reason_codes.add("source_shape_fixed")
    elif source.structure_stability == "dynamic":
        reason_codes.add("source_shape_watch")
    else:
        reason_codes.add("source_shape_unfixed")
    if cadence_score == ONE:
        reason_codes.add("cadence_within_sla")
    elif cadence_score > ZERO:
        reason_codes.add("cadence_watch")
    else:
        reason_codes.add("cadence_blocked")
    if validation_score >= Decimal("0.800000"):
        reason_codes.add("validation_path_ready")
    elif validation_score > ZERO:
        reason_codes.add("validation_path_watch")
    else:
        reason_codes.add("validation_path_missing")
    if fallback_score >= Decimal("0.700000"):
        reason_codes.add("fallback_ready")
    elif fallback_score > ZERO:
        reason_codes.add("fallback_watch")
    else:
        reason_codes.add("fallback_missing")
    if source.fallback_path != "none" and not source.fallback_tested:
        reason_codes.add("fallback_untested")
    for reason_code in source.reason_codes:
        reason_codes.add(f"input_{reason_code}")
    return tuple(sorted(reason_codes))


def _summary_reason_codes(
    rows: tuple[ResearchSourceScrapingReadinessRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return ("no_sources_to_assess",)
    if any(row.status == "blocked" for row in rows):
        return tuple(sorted({code for row in rows for code in row.reason_codes}))
    if all(row.status == "pass" for row in rows):
        return ("scraping_readiness_pass",)
    return tuple(sorted({code for row in rows for code in row.reason_codes}))


def _summary_status(reason_codes: tuple[str, ...]) -> str:
    if reason_codes == ("no_sources_to_assess",):
        return "blocked"
    if "scraping_readiness_blocked" in reason_codes:
        return "blocked"
    if "scraping_readiness_watch" in reason_codes:
        return "watch"
    return "pass"


def _reason_code_counts(
    rows: tuple[ResearchSourceScrapingReadinessRow, ...],
    reason_codes: tuple[str, ...],
) -> tuple[ResearchSourceScrapingReadinessReasonCodeCount, ...]:
    if not rows:
        return (
            ResearchSourceScrapingReadinessReasonCodeCount(
                reason_code=reason_codes[0],
                count=ONE,
            ),
        )
    counts: Counter[str] = Counter()
    for row in rows:
        counts.update(row.reason_codes)
    return tuple(
        ResearchSourceScrapingReadinessReasonCodeCount(
            reason_code=reason_code,
            count=_decimal_count(count),
        )
        for reason_code, count in sorted(counts.items(), key=lambda item: item[0])
    )


def _average_readiness_score(
    rows: tuple[ResearchSourceScrapingReadinessRow, ...],
) -> Decimal | None:
    if not rows:
        return None
    return _quantize(
        sum((row.readiness_score for row in rows), ZERO) / Decimal(len(rows)),
    )


def _status_count(
    rows: tuple[ResearchSourceScrapingReadinessRow, ...],
    status: str,
) -> int:
    return sum(1 for row in rows if row.status == status)


def _normalize_rows(
    rows: tuple[ResearchSourceScrapingReadinessRow, ...],
) -> tuple[ResearchSourceScrapingReadinessRow, ...]:
    if type(rows) is not tuple:
        raise ValueError("rows must be a tuple")
    for row in rows:
        if type(row) is not ResearchSourceScrapingReadinessRow:
            raise ValueError("rows must contain ResearchSourceScrapingReadinessRow values")
        _require_hard_flags("row", row)
    sorted_rows = tuple(sorted(rows, key=lambda row: row.source_index))
    if rows != sorted_rows:
        raise ValueError("rows must be sorted by source_index")
    expected_index = ONE
    for row in rows:
        if row.source_index != expected_index:
            raise ValueError("rows source_index values must be contiguous")
        expected_index += ONE
    return rows


def _normalize_reason_code_counts(
    counts: tuple[ResearchSourceScrapingReadinessReasonCodeCount, ...],
) -> tuple[ResearchSourceScrapingReadinessReasonCodeCount, ...]:
    if type(counts) is not tuple:
        raise ValueError("reason_code_counts must be a tuple")
    for count in counts:
        if type(count) is not ResearchSourceScrapingReadinessReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "ResearchSourceScrapingReadinessReasonCodeCount values",
            )
        _require_hard_flags("reason_code_count", count)
    sorted_counts = tuple(sorted(counts, key=lambda count: count.reason_code))
    if counts != sorted_counts:
        raise ValueError("reason_code_counts must be sorted by reason_code")
    return counts


def _validate_report_consistency(report: ResearchSourceScrapingReadinessReport) -> None:
    if report.source_count != _decimal_count(len(report.rows)):
        raise ValueError("source_count must match rows")
    if report.pass_count != _decimal_count(_status_count(report.rows, "pass")):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _decimal_count(_status_count(report.rows, "watch")):
        raise ValueError("watch_count must match rows")
    if report.blocked_count != _decimal_count(_status_count(report.rows, "blocked")):
        raise ValueError("blocked_count must match rows")
    if report.average_readiness_score != _average_readiness_score(report.rows):
        raise ValueError("average_readiness_score must match rows")
    if report.reason_codes != _summary_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")
    if report.status != _summary_status(report.reason_codes):
        raise ValueError("status must match reason_codes")
    if report.reason_code_counts != _reason_code_counts(report.rows, report.reason_codes):
        raise ValueError("reason_code_counts must match rows")


def _payload_value(value: object) -> object:
    if type(value) is Decimal:
        return format(value, "f")
    if type(value) is datetime:
        return value.astimezone(UTC).isoformat()
    if type(value) is tuple:
        return [_payload_value(item) for item in value]
    if is_dataclass(value) and not isinstance(value, type):
        return {
            field.name: _payload_value(getattr(value, field.name))
            for field in fields(value)
        }
    if value is None or type(value) in (str, bool):
        return value
    raise ValueError("payload contains an unsupported value")


def _reject_unsafe_public_payload(value: object) -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            _reject_unsafe_public_string(str(key))
            _reject_unsafe_public_payload(item)
        return
    if isinstance(value, list):
        for item in value:
            _reject_unsafe_public_payload(item)
        return
    if type(value) is str:
        _reject_unsafe_public_string(value)


def _reject_unsafe_public_string(value: str) -> None:
    lowered = value.lower()
    if any(fragment in lowered for fragment in UNSAFE_PUBLIC_SUBSTRINGS):
        raise ValueError("public payload contains unsafe source material")


def _as_utc(field_name: str, value: datetime) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    try:
        return +value
    except InvalidOperation as exc:
        raise ValueError(f"{field_name} must be finite") from exc


def _require_positive_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _require_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _require_probability_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < ZERO or normalized > ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return _quantize(normalized)


def _require_optional_probability_decimal(
    field_name: str,
    value: object,
) -> Decimal | None:
    if value is None:
        return None
    return _require_probability_decimal(field_name, value)


def _require_positive_whole_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_positive_decimal(field_name, value)
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{field_name} must be a whole count")
    return normalized


def _require_nonnegative_whole_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_nonnegative_decimal(field_name, value)
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{field_name} must be a whole count")
    return normalized


def _decimal_count(value: int) -> Decimal:
    if type(value) is not int:
        raise ValueError("count source must be an int")
    if value < 0:
        raise ValueError("count source must be nonnegative")
    return Decimal(value)


def _quantize(value: Decimal) -> Decimal:
    return value.quantize(RATIO_QUANTUM)


def _require_private_string(field_name: str, value: object) -> None:
    if type(value) is not str or not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a nonempty private string")


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str or not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a nonempty canonical string")


def _require_enum(field_name: str, value: object, allowed: tuple[str, ...]) -> None:
    if type(value) is not str or value not in allowed:
        raise ValueError(f"{field_name} must be one of {allowed}")


def _normalize_reason_codes(
    field_name: str,
    values: object,
    *,
    allow_empty: bool,
) -> tuple[str, ...]:
    if type(values) is not tuple:
        raise ValueError(f"{field_name} must be a tuple")
    normalized: list[str] = []
    for value in values:
        _require_reason_code(field_name, value)
        normalized.append(value)
    if not allow_empty and not normalized:
        raise ValueError(f"{field_name} must be nonempty")
    return tuple(sorted(set(normalized)))


def _require_reason_code(field_name: str, value: object) -> None:
    _require_canonical_string(field_name, value)
    allowed = "abcdefghijklmnopqrstuvwxyz0123456789_"
    if any(character not in allowed for character in value):
        raise ValueError(f"{field_name} must contain deterministic code text")
    lowered = value.lower()
    if any(fragment in lowered for fragment in UNSAFE_PUBLIC_SUBSTRINGS):
        raise ValueError(f"{field_name} must not expose source material")


def _require_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in STATUSES:
        raise ValueError(f"{field_name} must be a known status")


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if getattr(value, field_name, None) is not True:
            raise ValueError(f"{label} {field_name} must be True")
