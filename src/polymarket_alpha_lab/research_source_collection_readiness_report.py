"""Pure aggregate readiness report for pre-probability research collection."""

from __future__ import annotations

from dataclasses import asdict, dataclass, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, InvalidOperation, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
import json
from typing import Any


DEFAULT_RESEARCH_SOURCE_COLLECTION_READINESS_CONFIG_VERSION = (
    "research-source-collection-readiness-v0"
)

STATUSES = ("pass", "watch", "block")
SOURCE_TYPES = ("official", "news", "data", "analysis", "expert")

NO_EVIDENCE_REASON = "research_source_collection_readiness_no_evidence"
PASS_REASON = "research_source_collection_readiness_pass"
WATCH_REASON = "research_source_collection_readiness_watch"
BLOCK_REASON = "research_source_collection_readiness_block"
READY_REASON = "research_source_collection_readiness_ready"
INSUFFICIENT_EVIDENCE_REASON = (
    "research_source_collection_readiness_insufficient_evidence_count"
)
INSUFFICIENT_INDEPENDENCE_REASON = (
    "research_source_collection_readiness_insufficient_independent_sources"
)
INSUFFICIENT_SOURCE_TYPE_REASON = (
    "research_source_collection_readiness_insufficient_source_type_diversity"
)
STALE_EVIDENCE_REASON = "research_source_collection_readiness_stale_evidence"
REASON_CODES = (
    NO_EVIDENCE_REASON,
    BLOCK_REASON,
    WATCH_REASON,
    PASS_REASON,
    READY_REASON,
    INSUFFICIENT_EVIDENCE_REASON,
    INSUFFICIENT_INDEPENDENCE_REASON,
    INSUFFICIENT_SOURCE_TYPE_REASON,
    STALE_EVIDENCE_REASON,
)

DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
QUANT = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
STATUS_RANK = {
    "block": Decimal("0.000000"),
    "watch": Decimal("1.000000"),
    "pass": Decimal("2.000000"),
}


def _join_parts(*parts: str) -> str:
    return "".join(parts)


UNSAFE_PUBLIC_KEY_FRAGMENTS = (
    _join_parts("candidate", "_", "id"),
    _join_parts("market", "_", "id"),
    _join_parts("market", "_", "slug"),
    _join_parts("market", "_", "question"),
    _join_parts("ques", "tion"),
    _join_parts("source", "_", "id"),
    _join_parts("source", "_", "url"),
    _join_parts("source", "_", "text"),
    _join_parts("source", "_", "ref"),
    _join_parts("source", "_", "reference"),
    _join_parts("d", "s", "n"),
    _join_parts("table", "_", "name"),
    _join_parts("to", "ken"),
    _join_parts("wal", "let"),
    _join_parts("or", "der"),
    _join_parts("tr", "ade"),
)


class _NoPublicSubclass:
    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if _NoPublicSubclass not in cls.__bases__:
            raise TypeError(f"{cls.__name__} does not support subclassing")


@dataclass(frozen=True)
class ResearchSourceCollectionReadinessConfig(_NoPublicSubclass):
    config_version: str = DEFAULT_RESEARCH_SOURCE_COLLECTION_READINESS_CONFIG_VERSION
    timely_evidence_age_seconds: Decimal = Decimal("7200.000000")
    min_evidence_count: Decimal = Decimal("3.000000")
    min_independent_source_count: Decimal = Decimal("2.000000")
    min_source_type_count: Decimal = Decimal("2.000000")
    pass_readiness_score: Decimal = Decimal("0.750000")
    watch_readiness_score: Decimal = Decimal("0.500000")
    timeliness_weight: Decimal = Decimal("0.350000")
    independence_weight: Decimal = Decimal("0.350000")
    source_type_diversity_weight: Decimal = Decimal("0.300000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchSourceCollectionReadinessConfig, "config")
        _require_canonical_string("config_version", self.config_version)
        object.__setattr__(
            self,
            "timely_evidence_age_seconds",
            _require_positive_decimal(
                "timely_evidence_age_seconds",
                self.timely_evidence_age_seconds,
            ),
        )
        for field_name in (
            "min_evidence_count",
            "min_independent_source_count",
            "min_source_type_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_positive_whole_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "pass_readiness_score",
            "watch_readiness_score",
            "timeliness_weight",
            "independence_weight",
            "source_type_diversity_weight",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio(field_name, getattr(self, field_name)),
            )
        if self.pass_readiness_score <= self.watch_readiness_score:
            raise ValueError("pass_readiness_score must exceed watch_readiness_score")
        if _quantize(
            self.timeliness_weight
            + self.independence_weight
            + self.source_type_diversity_weight,
        ) != ONE:
            raise ValueError("readiness weights must sum to one")
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class ResearchSourceCollectionReadinessEvidence(_NoPublicSubclass):
    event_category: str
    source_family: str
    source_type: str
    observed_at: datetime
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchSourceCollectionReadinessEvidence, "evidence")
        _require_canonical_string("event_category", self.event_category)
        _require_canonical_string("source_family", self.source_family)
        _require_enum("source_type", self.source_type, SOURCE_TYPES)
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        _require_hard_flags("evidence", self)


@dataclass(frozen=True)
class ResearchSourceCollectionReadinessRow(_NoPublicSubclass):
    event_category: str
    evidence_count: Decimal
    timely_evidence_count: Decimal
    independent_source_count: Decimal
    source_type_count: Decimal
    latest_observed_at: datetime
    latest_source_age_seconds: Decimal
    timely_evidence_ratio: Decimal
    independence_ratio: Decimal
    source_type_diversity_ratio: Decimal
    readiness_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchSourceCollectionReadinessRow, "row")
        _require_canonical_string("event_category", self.event_category)
        for field_name in (
            "evidence_count",
            "timely_evidence_count",
            "independent_source_count",
            "source_type_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_whole_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "latest_observed_at",
            _as_utc("latest_observed_at", self.latest_observed_at),
        )
        object.__setattr__(
            self,
            "latest_source_age_seconds",
            _require_nonnegative_decimal(
                "latest_source_age_seconds",
                self.latest_source_age_seconds,
            ),
        )
        for field_name in (
            "timely_evidence_ratio",
            "independence_ratio",
            "source_type_diversity_ratio",
            "readiness_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio(field_name, getattr(self, field_name)),
            )
        _require_status("status", self.status)
        object.__setattr__(self, "reason_codes", _normalize_reason_codes(self.reason_codes))
        _validate_row(self)
        _require_hard_flags("row", self)


@dataclass(frozen=True)
class ResearchSourceCollectionReadinessReport(_NoPublicSubclass):
    generated_at: datetime
    config_version: str
    event_category_count: Decimal
    evidence_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    min_readiness_score: Decimal
    average_readiness_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    rows: tuple[ResearchSourceCollectionReadinessRow, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchSourceCollectionReadinessReport, "report")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        for field_name in (
            "event_category_count",
            "evidence_count",
            "pass_count",
            "watch_count",
            "block_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_whole_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in ("min_readiness_score", "average_readiness_score"):
            object.__setattr__(
                self,
                field_name,
                _require_ratio(field_name, getattr(self, field_name)),
            )
        _require_status("status", self.status)
        object.__setattr__(self, "reason_codes", _normalize_reason_codes(self.reason_codes))
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        _validate_report(self)
        _require_or_set_digest(self)
        _require_hard_flags("report", self)


def build_research_source_collection_readiness_report(
    evidence_rows: list[ResearchSourceCollectionReadinessEvidence]
    | tuple[ResearchSourceCollectionReadinessEvidence, ...],
    *,
    config: ResearchSourceCollectionReadinessConfig,
    generated_at: datetime,
) -> ResearchSourceCollectionReadinessReport:
    if type(config) is not ResearchSourceCollectionReadinessConfig:
        raise ValueError("config must be a ResearchSourceCollectionReadinessConfig")
    _require_hard_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    evidence_items = _normalize_evidence_rows(evidence_rows)
    for item in evidence_items:
        if item.observed_at > generated_at_utc:
            raise ValueError("observed_at must not be after generated_at")
    grouped: dict[str, list[ResearchSourceCollectionReadinessEvidence]] = {}
    for item in evidence_items:
        grouped.setdefault(item.event_category, []).append(item)
    rows = tuple(
        sorted(
            (
                _row_from_group(
                    event_category=event_category,
                    evidence_rows=tuple(grouped[event_category]),
                    config=config,
                    generated_at=generated_at_utc,
                )
                for event_category in sorted(grouped)
            ),
            key=_row_sort_key,
        ),
    )
    return ResearchSourceCollectionReadinessReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        event_category_count=_count(len(rows)),
        evidence_count=_sum_rows(rows, "evidence_count"),
        pass_count=_count(sum(row.status == "pass" for row in rows)),
        watch_count=_count(sum(row.status == "watch" for row in rows)),
        block_count=_count(sum(row.status == "block" for row in rows)),
        min_readiness_score=_min_rows(rows, "readiness_score"),
        average_readiness_score=_ratio(_sum_rows(rows, "readiness_score"), _count(len(rows))),
        status=_report_status(rows),
        reason_codes=_report_reason_codes(rows),
        rows=rows,
    )


def research_source_collection_readiness_report_payload(
    report: ResearchSourceCollectionReadinessReport,
) -> dict[str, Any]:
    if type(report) is not ResearchSourceCollectionReadinessReport:
        raise ValueError("report must be a ResearchSourceCollectionReadinessReport")
    _require_hard_flags("report", report)
    _require_or_set_digest(report)
    payload = _json_ready(report)
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    validate_research_source_collection_readiness_public_payload(payload)
    return payload


def validate_research_source_collection_readiness_public_payload(
    payload: dict[str, Any],
) -> bool:
    if type(payload) is not dict:
        raise ValueError("payload must be a JSON object")
    _reject_unsafe_public_payload(payload)
    _require_payload_hard_flags(payload)
    _verify_public_digest(payload)
    return True


def _row_from_group(
    *,
    event_category: str,
    evidence_rows: tuple[ResearchSourceCollectionReadinessEvidence, ...],
    config: ResearchSourceCollectionReadinessConfig,
    generated_at: datetime,
) -> ResearchSourceCollectionReadinessRow:
    latest = max(evidence_rows, key=lambda row: row.observed_at)
    source_ages = tuple(_age_seconds(generated_at, row.observed_at) for row in evidence_rows)
    timely_evidence_count = sum(
        age <= config.timely_evidence_age_seconds for age in source_ages
    )
    independent_source_count = len({row.source_family for row in evidence_rows})
    source_type_count = len({row.source_type for row in evidence_rows})
    evidence_count = len(evidence_rows)
    timely_evidence_ratio = _ratio(_count(timely_evidence_count), _count(evidence_count))
    independence_ratio = min(
        _ratio(_count(independent_source_count), config.min_independent_source_count),
        ONE,
    )
    source_type_diversity_ratio = min(
        _ratio(_count(source_type_count), config.min_source_type_count),
        ONE,
    )
    readiness_score = _readiness_score(
        timely_evidence_ratio=timely_evidence_ratio,
        independence_ratio=independence_ratio,
        source_type_diversity_ratio=source_type_diversity_ratio,
        config=config,
    )
    status = _row_status(
        evidence_count=evidence_count,
        timely_evidence_count=timely_evidence_count,
        independent_source_count=independent_source_count,
        source_type_count=source_type_count,
        readiness_score=readiness_score,
        config=config,
    )
    return ResearchSourceCollectionReadinessRow(
        event_category=event_category,
        evidence_count=_count(evidence_count),
        timely_evidence_count=_count(timely_evidence_count),
        independent_source_count=_count(independent_source_count),
        source_type_count=_count(source_type_count),
        latest_observed_at=latest.observed_at,
        latest_source_age_seconds=_age_seconds(generated_at, latest.observed_at),
        timely_evidence_ratio=timely_evidence_ratio,
        independence_ratio=independence_ratio,
        source_type_diversity_ratio=source_type_diversity_ratio,
        readiness_score=readiness_score,
        status=status,
        reason_codes=_row_reason_codes(
            status=status,
            evidence_count=evidence_count,
            timely_evidence_count=timely_evidence_count,
            independent_source_count=independent_source_count,
            source_type_count=source_type_count,
            config=config,
        ),
    )


def _readiness_score(
    *,
    timely_evidence_ratio: Decimal,
    independence_ratio: Decimal,
    source_type_diversity_ratio: Decimal,
    config: ResearchSourceCollectionReadinessConfig,
) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return (
            timely_evidence_ratio * config.timeliness_weight
            + independence_ratio * config.independence_weight
            + source_type_diversity_ratio * config.source_type_diversity_weight
        ).quantize(QUANT)


def _row_status(
    *,
    evidence_count: int,
    timely_evidence_count: int,
    independent_source_count: int,
    source_type_count: int,
    readiness_score: Decimal,
    config: ResearchSourceCollectionReadinessConfig,
) -> str:
    if timely_evidence_count == 0 or readiness_score < config.watch_readiness_score:
        return "block"
    if (
        readiness_score < config.pass_readiness_score
        or _count(evidence_count) < config.min_evidence_count
        or _count(independent_source_count) < config.min_independent_source_count
        or _count(source_type_count) < config.min_source_type_count
    ):
        return "watch"
    return "pass"


def _row_reason_codes(
    *,
    status: str,
    evidence_count: int,
    timely_evidence_count: int,
    independent_source_count: int,
    source_type_count: int,
    config: ResearchSourceCollectionReadinessConfig,
) -> tuple[str, ...]:
    reasons: list[str] = []
    if status == "block":
        reasons.append(BLOCK_REASON)
    if _count(evidence_count) < config.min_evidence_count:
        reasons.append(INSUFFICIENT_EVIDENCE_REASON)
    if _count(independent_source_count) < config.min_independent_source_count:
        reasons.append(INSUFFICIENT_INDEPENDENCE_REASON)
    if _count(source_type_count) < config.min_source_type_count:
        reasons.append(INSUFFICIENT_SOURCE_TYPE_REASON)
    if timely_evidence_count == 0:
        reasons.append(STALE_EVIDENCE_REASON)
    if status == "watch":
        reasons.append(WATCH_REASON)
    if status == "pass":
        reasons.extend((PASS_REASON, READY_REASON))
    return tuple(reasons)


def _normalize_evidence_rows(
    value: object,
) -> tuple[ResearchSourceCollectionReadinessEvidence, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("evidence_rows must be a list or tuple")
    rows = tuple(value)
    for row in rows:
        if type(row) is not ResearchSourceCollectionReadinessEvidence:
            raise ValueError(
                "evidence_rows must contain ResearchSourceCollectionReadinessEvidence",
            )
        _require_hard_flags("evidence", row)
    return tuple(
        sorted(
            rows,
            key=lambda row: (
                row.event_category,
                row.observed_at,
                row.source_type,
                row.source_family,
            ),
        ),
    )


def _normalize_rows(
    value: object,
) -> tuple[ResearchSourceCollectionReadinessRow, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("rows must be a list or tuple")
    rows = tuple(value)
    previous_key: tuple[Decimal, Decimal, str] | None = None
    seen: set[str] = set()
    for row in rows:
        if type(row) is not ResearchSourceCollectionReadinessRow:
            raise ValueError("rows must contain ResearchSourceCollectionReadinessRow")
        _require_hard_flags("row", row)
        if row.event_category in seen:
            raise ValueError("rows must contain unique event categories")
        seen.add(row.event_category)
        sort_key = _row_sort_key(row)
        if previous_key is not None and sort_key <= previous_key:
            raise ValueError("rows must follow deterministic sequence")
        previous_key = sort_key
    return rows


def _row_sort_key(
    row: ResearchSourceCollectionReadinessRow,
) -> tuple[Decimal, Decimal, str]:
    return (STATUS_RANK[row.status], row.readiness_score, row.event_category)


def _report_status(rows: tuple[ResearchSourceCollectionReadinessRow, ...]) -> str:
    if not rows:
        return "block"
    if any(row.status == "block" for row in rows):
        return "block"
    if any(row.status == "watch" for row in rows):
        return "watch"
    return "pass"


def _report_reason_codes(
    rows: tuple[ResearchSourceCollectionReadinessRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return (NO_EVIDENCE_REASON,)
    values: list[str] = []
    for reason_code in REASON_CODES:
        if reason_code == NO_EVIDENCE_REASON:
            continue
        if any(reason_code in row.reason_codes for row in rows):
            values.append(reason_code)
    return tuple(values)


def _validate_row(row: ResearchSourceCollectionReadinessRow) -> None:
    if row.timely_evidence_count > row.evidence_count:
        raise ValueError("timely_evidence_count must not exceed evidence_count")
    if row.independent_source_count > row.evidence_count:
        raise ValueError("independent_source_count must not exceed evidence_count")
    if row.source_type_count > row.evidence_count:
        raise ValueError("source_type_count must not exceed evidence_count")
    if row.evidence_count <= ZERO:
        raise ValueError("evidence_count must be positive")
    expected_timely_ratio = _ratio(row.timely_evidence_count, row.evidence_count)
    if row.timely_evidence_ratio != expected_timely_ratio:
        raise ValueError("timely_evidence_ratio must match counts")
    if row.status == "block" and BLOCK_REASON not in row.reason_codes:
        raise ValueError("status must match reason_codes")
    if row.status == "watch" and WATCH_REASON not in row.reason_codes:
        raise ValueError("status must match reason_codes")
    if row.status == "pass" and PASS_REASON not in row.reason_codes:
        raise ValueError("status must match reason_codes")


def _validate_report(report: ResearchSourceCollectionReadinessReport) -> None:
    if report.event_category_count != _count(len(report.rows)):
        raise ValueError("event_category_count must match rows")
    if report.evidence_count != _sum_rows(report.rows, "evidence_count"):
        raise ValueError("evidence_count must match rows")
    if report.pass_count != _count(sum(row.status == "pass" for row in report.rows)):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _count(sum(row.status == "watch" for row in report.rows)):
        raise ValueError("watch_count must match rows")
    if report.block_count != _count(sum(row.status == "block" for row in report.rows)):
        raise ValueError("block_count must match rows")
    if report.min_readiness_score != _min_rows(report.rows, "readiness_score"):
        raise ValueError("min_readiness_score must match rows")
    if report.average_readiness_score != _ratio(
        _sum_rows(report.rows, "readiness_score"),
        _count(len(report.rows)),
    ):
        raise ValueError("average_readiness_score must match rows")
    if report.status != _report_status(report.rows):
        raise ValueError("status must match rows")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")


def _count(value: int) -> Decimal:
    if type(value) is not int:
        raise ValueError("count value must be an int")
    if value < 0:
        raise ValueError("count value must be nonnegative")
    return Decimal(value).quantize(QUANT)


def _sum_rows(rows: tuple[object, ...], field_name: str) -> Decimal:
    return _require_nonnegative_decimal(
        field_name,
        sum((getattr(row, field_name) for row in rows), ZERO),
    )


def _min_rows(rows: tuple[object, ...], field_name: str) -> Decimal:
    if not rows:
        return ZERO
    return min(
        _require_nonnegative_decimal(field_name, getattr(row, field_name))
        for row in rows
    ).quantize(QUANT)


def _age_seconds(generated_at: datetime, observed_at: datetime) -> Decimal:
    delta = generated_at - observed_at
    value = (
        Decimal(delta.days * 86400)
        + Decimal(delta.seconds)
        + (Decimal(delta.microseconds) / Decimal("1000000"))
    )
    return _require_nonnegative_decimal("source_age_seconds", value)


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    numerator_value = _require_nonnegative_decimal("ratio numerator", numerator)
    denominator_value = _require_nonnegative_decimal("ratio denominator", denominator)
    if denominator_value == ZERO:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return (numerator_value / denominator_value).quantize(QUANT)


def _require_status(field_name: str, value: object) -> None:
    _require_canonical_string(field_name, value)
    if value not in STATUSES:
        raise ValueError(f"{field_name} must be pass, watch, or block")


def _require_enum(field_name: str, value: object, allowed: tuple[str, ...]) -> None:
    _require_canonical_string(field_name, value)
    if value not in allowed:
        raise ValueError(f"{field_name} must be one of {allowed}")


def _normalize_reason_codes(value: object) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ValueError("reason_codes must be a tuple")
    if not value:
        raise ValueError("reason_codes must not be empty")
    seen: set[str] = set()
    normalized: list[str] = []
    for reason_code in value:
        _require_canonical_string("reason_code", reason_code)
        if reason_code not in REASON_CODES:
            raise ValueError("reason_code must be known")
        if reason_code in seen:
            raise ValueError("reason_codes must be unique")
        seen.add(reason_code)
        normalized.append(reason_code)
    return tuple(normalized)


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")


def _require_ratio(field_name: str, value: object) -> Decimal:
    ratio = _require_nonnegative_decimal(field_name, value)
    if ratio > ONE:
        raise ValueError(f"{field_name} must not exceed one")
    return ratio


def _require_positive_whole_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_positive_decimal(field_name, value)
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{field_name} must be a whole Decimal")
    return normalized


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


def _require_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    if value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    try:
        with localcontext(DECIMAL_CONTEXT):
            return value.quantize(QUANT)
    except InvalidOperation as exc:
        raise ValueError(f"{field_name} must fit the decimal context") from exc


def _quantize(value: Decimal) -> Decimal:
    return _require_nonnegative_decimal("quantized value", value)


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_exact_type(value: object, expected_type: type[object], label: str) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{label} must be an exact {expected_type.__name__}")


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if getattr(value, field_name, None) is not True:
            raise ValueError(f"{label} must have {field_name}=True")


def _require_or_set_digest(report: ResearchSourceCollectionReadinessReport) -> None:
    if type(report.derived_validation_digest) is not str:
        raise ValueError("derived_validation_digest must be a string")
    expected = _report_digest(report)
    if report.derived_validation_digest == "":
        object.__setattr__(report, "derived_validation_digest", expected)
        return
    if report.derived_validation_digest != expected:
        raise ValueError("derived_validation_digest does not match public payload")


def _report_digest(report: ResearchSourceCollectionReadinessReport) -> str:
    payload = _json_ready(report)
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    payload.pop("derived_validation_digest", None)
    return _canonical_digest(payload)


def _verify_public_digest(payload: dict[str, Any]) -> None:
    digest = payload.get("derived_validation_digest")
    if type(digest) is not str:
        raise ValueError("derived_validation_digest must be a string")
    unsigned = dict(payload)
    unsigned.pop("derived_validation_digest", None)
    if digest != _canonical_digest(unsigned):
        raise ValueError("derived_validation_digest does not match public payload")


def _canonical_digest(payload: dict[str, Any]) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    return sha256(encoded).hexdigest()


def _json_ready(value: Any) -> Any:
    if value is None:
        return None
    if is_dataclass(value) and not isinstance(value, type):
        return _json_ready(asdict(value))
    if isinstance(value, Decimal):
        if type(value) is not Decimal:
            raise ValueError("JSON Decimal value must be a Decimal")
        if not value.is_finite():
            raise ValueError("JSON Decimal value must be finite")
        return str(value)
    if isinstance(value, datetime):
        return _as_utc("JSON datetime value", value).isoformat()
    if isinstance(value, bool):
        return value
    if isinstance(value, (float, int)):
        raise ValueError("JSON numeric value must use Decimal")
    if isinstance(value, str):
        return value
    if isinstance(value, dict):
        ready: dict[str, Any] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            ready[key] = _json_ready(item)
        return ready
    if isinstance(value, (list, tuple)):
        return [_json_ready(item) for item in value]
    raise ValueError("value is not JSON serializable")


def _require_payload_hard_flags(value: object) -> None:
    if isinstance(value, dict):
        flag_keys = ("paper_only", "report_only", "readonly")
        if any(key in value for key in flag_keys):
            if any(value.get(key) is not True for key in flag_keys):
                raise ValueError("public payload hard flags must be true")
        for item in value.values():
            _require_payload_hard_flags(item)
        return
    if isinstance(value, list):
        for item in value:
            _require_payload_hard_flags(item)


def _reject_unsafe_public_payload(value: object) -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            lowered = key.lower()
            if any(fragment in lowered for fragment in UNSAFE_PUBLIC_KEY_FRAGMENTS):
                raise ValueError("unsafe public payload key")
            _reject_unsafe_public_payload(item)
        return
    if isinstance(value, list):
        for item in value:
            _reject_unsafe_public_payload(item)
        return
    if type(value) in (int, float):
        raise ValueError("unsafe public payload numeric")
    if isinstance(value, str):
        lowered = value.lower()
        if lowered.startswith(("http://", "https://")):
            raise ValueError("unsafe public payload value")
        if any(fragment in lowered for fragment in UNSAFE_PUBLIC_KEY_FRAGMENTS):
            raise ValueError("unsafe public payload value")


__all__ = (
    "DEFAULT_RESEARCH_SOURCE_COLLECTION_READINESS_CONFIG_VERSION",
    "STATUSES",
    "SOURCE_TYPES",
    "ResearchSourceCollectionReadinessConfig",
    "ResearchSourceCollectionReadinessEvidence",
    "ResearchSourceCollectionReadinessReport",
    "ResearchSourceCollectionReadinessRow",
    "build_research_source_collection_readiness_report",
    "research_source_collection_readiness_report_payload",
    "validate_research_source_collection_readiness_public_payload",
)
