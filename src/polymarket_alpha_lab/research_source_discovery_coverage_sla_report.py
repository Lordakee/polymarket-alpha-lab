"""Pure report-only source discovery coverage SLA report."""

from __future__ import annotations

from dataclasses import asdict, dataclass, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal, ROUND_HALF_UP
from hashlib import sha256
import json
import re
from typing import Any, Mapping


DEFAULT_RESEARCH_SOURCE_DISCOVERY_COVERAGE_SLA_CONFIG_VERSION = (
    "research-source-discovery-coverage-sla-report-v0"
)

STATUSES = ("pass", "watch", "block")

NO_SOURCE_CLASSES_REASON = "research_source_discovery_coverage_sla_no_source_classes"
CLEAR_REASON = "research_source_discovery_coverage_sla_clear"
INCOMPLETE_CLASS_COVERAGE_REASON = (
    "research_source_discovery_coverage_sla_incomplete_class_coverage"
)
MISSING_SOURCE_CLASS_REASON = (
    "research_source_discovery_coverage_sla_missing_source_class"
)
STALE_DISCOVERY_FRESHNESS_REASON = (
    "research_source_discovery_coverage_sla_stale_discovery_freshness"
)
PARSE_QUALITY_NOT_READY_REASON = (
    "research_source_discovery_coverage_sla_parse_quality_not_ready"
)
RETRY_BACKLOG_PRESSURE_REASON = (
    "research_source_discovery_coverage_sla_retry_backlog_pressure"
)
MANUAL_REVIEW_URGENT_REASON = (
    "research_source_discovery_coverage_sla_manual_review_urgent"
)

REASON_CODES = (
    NO_SOURCE_CLASSES_REASON,
    INCOMPLETE_CLASS_COVERAGE_REASON,
    MISSING_SOURCE_CLASS_REASON,
    STALE_DISCOVERY_FRESHNESS_REASON,
    PARSE_QUALITY_NOT_READY_REASON,
    RETRY_BACKLOG_PRESSURE_REASON,
    MANUAL_REVIEW_URGENT_REASON,
    CLEAR_REASON,
)
STATUS_RANK = {
    "block": Decimal("0.000000"),
    "watch": Decimal("1.000000"),
    "pass": Decimal("2.000000"),
}

QUANT = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
PUBLIC_IDENTIFIER_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,127}$")
DIGEST_RE = re.compile(r"^[0-9a-f]{64}$")
PHASE_FLAG_FIELDS = frozenset(("paper_only", "report_only", "readonly"))


def _join_parts(*parts: str) -> str:
    return "".join(parts)


UNSAFE_PUBLIC_TERMS = (
    _join_parts("ra", "w"),
    _join_parts("u", "r", "l"),
    _join_parts("te", "xt"),
    _join_parts("mar", "ket"),
    _join_parts("candi", "date"),
    _join_parts("d", "s", "n"),
    _join_parts("ta", "ble"),
    _join_parts("to", "ken"),
    _join_parts("pri", "vate"),
    _join_parts("wa", "llet"),
    _join_parts("au", "th"),
    _join_parts("or", "der"),
    _join_parts("li", "ve"),
    _join_parts("tra", "de"),
    _join_parts("si", "zing"),
    _join_parts("recommen", "dation"),
    _join_parts("acc", "ount"),
    _join_parts("bro", "ker"),
    _join_parts("cre", "den", "tial"),
    "http",
    "www.",
)


@dataclass(frozen=True)
class ResearchSourceDiscoveryCoverageSlaConfig:
    config_version: str = DEFAULT_RESEARCH_SOURCE_DISCOVERY_COVERAGE_SLA_CONFIG_VERSION
    min_source_class_found_watch_ratio: Decimal = Decimal("1.000000")
    min_source_class_found_block_ratio: Decimal = Decimal("0.500000")
    max_missing_class_pressure_watch_ratio: Decimal = Decimal("0.000000")
    max_missing_class_pressure_block_ratio: Decimal = Decimal("0.500000")
    max_discovery_freshness_watch_seconds: Decimal = Decimal("3600.000000")
    max_discovery_freshness_block_seconds: Decimal = Decimal("7200.000000")
    min_parse_quality_ready_watch_ratio: Decimal = Decimal("0.800000")
    min_parse_quality_ready_block_ratio: Decimal = Decimal("0.600000")
    max_retry_backlog_watch_ratio: Decimal = Decimal("0.250000")
    max_retry_backlog_block_ratio: Decimal = Decimal("0.500000")
    max_manual_review_urgency_watch_ratio: Decimal = Decimal("0.500000")
    max_manual_review_urgency_block_ratio: Decimal = Decimal("0.850000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls) -> None:
        raise TypeError("ResearchSourceDiscoveryCoverageSlaConfig may not be subclassed")

    def __post_init__(self) -> None:
        if type(self) is not ResearchSourceDiscoveryCoverageSlaConfig:
            raise ValueError("config must be a ResearchSourceDiscoveryCoverageSlaConfig")
        _require_public_identifier("config_version", self.config_version)
        for field_name in (
            "min_source_class_found_watch_ratio",
            "min_source_class_found_block_ratio",
            "max_missing_class_pressure_watch_ratio",
            "max_missing_class_pressure_block_ratio",
            "min_parse_quality_ready_watch_ratio",
            "min_parse_quality_ready_block_ratio",
            "max_retry_backlog_watch_ratio",
            "max_retry_backlog_block_ratio",
            "max_manual_review_urgency_watch_ratio",
            "max_manual_review_urgency_block_ratio",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "max_discovery_freshness_watch_seconds",
            "max_discovery_freshness_block_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_positive_decimal(field_name, getattr(self, field_name)),
            )
        _validate_config(self)
        _require_hard_flags("config", self)
        _reject_public_payload(_json_ready(self))


@dataclass(frozen=True)
class ResearchSourceDiscoveryCoverageSlaInput:
    source_class: str
    required_source_count: Decimal
    discovered_source_count: Decimal
    discovery_freshness_age_seconds: Decimal
    parse_ready_source_count: Decimal
    retry_backlog_count: Decimal
    manual_review_item_count: Decimal
    manual_review_capacity_count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls) -> None:
        raise TypeError("ResearchSourceDiscoveryCoverageSlaInput may not be subclassed")

    def __post_init__(self) -> None:
        if type(self) is not ResearchSourceDiscoveryCoverageSlaInput:
            raise ValueError("input must be a ResearchSourceDiscoveryCoverageSlaInput")
        object.__setattr__(
            self,
            "source_class",
            _require_public_identifier("source_class", self.source_class),
        )
        object.__setattr__(
            self,
            "required_source_count",
            _require_positive_decimal("required_source_count", self.required_source_count),
        )
        for field_name in (
            "discovered_source_count",
            "discovery_freshness_age_seconds",
            "parse_ready_source_count",
            "retry_backlog_count",
            "manual_review_item_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "manual_review_capacity_count",
            _require_positive_decimal(
                "manual_review_capacity_count",
                self.manual_review_capacity_count,
            ),
        )
        _validate_input(self)
        _require_hard_flags("input", self)
        _reject_public_payload(_json_ready(self))


@dataclass(frozen=True)
class ResearchSourceDiscoveryCoverageSlaRow:
    source_class: str
    required_source_count: Decimal
    discovered_source_count: Decimal
    missing_source_count: Decimal
    source_class_found: bool
    source_class_covered: bool
    source_class_coverage_ratio: Decimal
    discovery_freshness_age_seconds: Decimal
    parse_ready_source_count: Decimal
    parse_quality_ready_ratio: Decimal
    retry_backlog_count: Decimal
    retry_backlog_ratio: Decimal
    manual_review_item_count: Decimal
    manual_review_capacity_count: Decimal
    manual_review_urgency_ratio: Decimal
    status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls) -> None:
        raise TypeError("ResearchSourceDiscoveryCoverageSlaRow may not be subclassed")

    def __post_init__(self) -> None:
        if type(self) is not ResearchSourceDiscoveryCoverageSlaRow:
            raise ValueError("row must be a ResearchSourceDiscoveryCoverageSlaRow")
        object.__setattr__(
            self,
            "source_class",
            _require_public_identifier("source_class", self.source_class),
        )
        object.__setattr__(
            self,
            "required_source_count",
            _require_positive_decimal("required_source_count", self.required_source_count),
        )
        for field_name in (
            "discovered_source_count",
            "missing_source_count",
            "discovery_freshness_age_seconds",
            "parse_ready_source_count",
            "retry_backlog_count",
            "manual_review_item_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in ("source_class_found", "source_class_covered"):
            if type(getattr(self, field_name)) is not bool:
                raise ValueError(f"{field_name} must be a bool")
        object.__setattr__(
            self,
            "manual_review_capacity_count",
            _require_positive_decimal(
                "manual_review_capacity_count",
                self.manual_review_capacity_count,
            ),
        )
        for field_name in (
            "source_class_coverage_ratio",
            "parse_quality_ready_ratio",
            "retry_backlog_ratio",
            "manual_review_urgency_ratio",
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
        _reject_public_payload(_json_ready(self))


@dataclass(frozen=True)
class ResearchSourceDiscoveryCoverageSlaReport:
    generated_at: datetime
    config_version: str
    required_source_class_count: Decimal
    found_source_class_count: Decimal
    covered_source_class_count: Decimal
    missing_source_class_count: Decimal
    required_source_count: Decimal
    discovered_source_count: Decimal
    missing_source_count: Decimal
    source_class_found_ratio: Decimal
    source_class_coverage_ratio: Decimal
    missing_class_pressure_ratio: Decimal
    discovery_freshness_age_seconds: Decimal
    parse_ready_source_count: Decimal
    parse_quality_ready_ratio: Decimal
    retry_backlog_count: Decimal
    retry_backlog_ratio: Decimal
    manual_review_item_count: Decimal
    manual_review_capacity_count: Decimal
    manual_review_urgency_ratio: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    status: str
    reason_codes: tuple[str, ...]
    coverage_rows: tuple[ResearchSourceDiscoveryCoverageSlaRow, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls) -> None:
        raise TypeError("ResearchSourceDiscoveryCoverageSlaReport may not be subclassed")

    def __post_init__(self) -> None:
        if type(self) is not ResearchSourceDiscoveryCoverageSlaReport:
            raise ValueError("report must be a ResearchSourceDiscoveryCoverageSlaReport")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_identifier("config_version", self.config_version)
        for field_name in (
            "required_source_class_count",
            "found_source_class_count",
            "covered_source_class_count",
            "missing_source_class_count",
            "required_source_count",
            "discovered_source_count",
            "missing_source_count",
            "discovery_freshness_age_seconds",
            "parse_ready_source_count",
            "retry_backlog_count",
            "manual_review_item_count",
            "manual_review_capacity_count",
            "pass_count",
            "watch_count",
            "block_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "source_class_found_ratio",
            "source_class_coverage_ratio",
            "missing_class_pressure_ratio",
            "parse_quality_ready_ratio",
            "retry_backlog_ratio",
            "manual_review_urgency_ratio",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio(field_name, getattr(self, field_name)),
            )
        _require_status("status", self.status)
        object.__setattr__(self, "reason_codes", _normalize_reason_codes(self.reason_codes))
        object.__setattr__(self, "coverage_rows", _normalize_rows(self.coverage_rows))
        _validate_report(self)
        _require_hard_flags("report", self)
        _require_or_set_digest(self)

    @property
    def payload(self) -> dict[str, Any]:
        return research_source_discovery_coverage_sla_report_payload(self)


def build_research_source_discovery_coverage_sla_report(
    inputs: list[ResearchSourceDiscoveryCoverageSlaInput]
    | tuple[ResearchSourceDiscoveryCoverageSlaInput, ...],
    *,
    config: ResearchSourceDiscoveryCoverageSlaConfig,
    generated_at: datetime,
) -> ResearchSourceDiscoveryCoverageSlaReport:
    if type(config) is not ResearchSourceDiscoveryCoverageSlaConfig:
        raise ValueError("config must be a ResearchSourceDiscoveryCoverageSlaConfig")
    _require_hard_flags("config", config)
    rows = _coverage_rows(_normalize_inputs(inputs), config=config)
    required_source_class_count = _count(len(rows))
    found_source_class_count = _count(sum(row.source_class_found for row in rows))
    covered_source_class_count = _count(sum(row.source_class_covered for row in rows))
    missing_source_class_count = _count(
        sum(not row.source_class_found for row in rows),
    )
    required_source_count = _sum_rows(rows, "required_source_count")
    discovered_source_count = _sum_rows(rows, "discovered_source_count")
    parse_ready_source_count = _sum_rows(rows, "parse_ready_source_count")
    retry_backlog_count = _sum_rows(rows, "retry_backlog_count")
    manual_review_item_count = _sum_rows(rows, "manual_review_item_count")
    manual_review_capacity_count = _sum_rows(rows, "manual_review_capacity_count")
    return ResearchSourceDiscoveryCoverageSlaReport(
        generated_at=_as_utc("generated_at", generated_at),
        config_version=config.config_version,
        required_source_class_count=required_source_class_count,
        found_source_class_count=found_source_class_count,
        covered_source_class_count=covered_source_class_count,
        missing_source_class_count=missing_source_class_count,
        required_source_count=required_source_count,
        discovered_source_count=discovered_source_count,
        missing_source_count=_sum_rows(rows, "missing_source_count"),
        source_class_found_ratio=_ratio(
            found_source_class_count,
            required_source_class_count,
        ),
        source_class_coverage_ratio=_ratio(
            covered_source_class_count,
            required_source_class_count,
        ),
        missing_class_pressure_ratio=_ratio(
            missing_source_class_count,
            required_source_class_count,
        ),
        discovery_freshness_age_seconds=_max_rows(
            rows,
            "discovery_freshness_age_seconds",
        ),
        parse_ready_source_count=parse_ready_source_count,
        parse_quality_ready_ratio=_ratio(
            parse_ready_source_count,
            discovered_source_count,
        ),
        retry_backlog_count=retry_backlog_count,
        retry_backlog_ratio=_ratio(retry_backlog_count, required_source_count),
        manual_review_item_count=manual_review_item_count,
        manual_review_capacity_count=manual_review_capacity_count,
        manual_review_urgency_ratio=_ratio(
            manual_review_item_count,
            manual_review_capacity_count,
        ),
        pass_count=_count(sum(row.status == "pass" for row in rows)),
        watch_count=_count(sum(row.status == "watch" for row in rows)),
        block_count=_count(sum(row.status == "block" for row in rows)),
        status=_report_status(rows),
        reason_codes=_report_reason_codes(rows),
        coverage_rows=rows,
    )


def research_source_discovery_coverage_sla_report_payload(
    report: ResearchSourceDiscoveryCoverageSlaReport,
) -> dict[str, Any]:
    if type(report) is not ResearchSourceDiscoveryCoverageSlaReport:
        raise ValueError("report must be a ResearchSourceDiscoveryCoverageSlaReport")
    _require_hard_flags("report", report)
    _require_or_set_digest(report)
    payload = _json_ready(report)
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    _reject_public_payload(payload)
    _verify_public_digest(payload)
    return payload


def validate_research_source_discovery_coverage_sla_report_payload(
    payload: Mapping[str, object],
) -> bool:
    if not isinstance(payload, Mapping):
        raise ValueError("payload must be a mapping")
    ready = _json_ready(dict(payload))
    if type(ready) is not dict:
        raise ValueError("payload must be a JSON object")
    _reject_public_payload(ready)
    _verify_public_digest(ready)
    return True


def _coverage_rows(
    inputs: tuple[ResearchSourceDiscoveryCoverageSlaInput, ...],
    *,
    config: ResearchSourceDiscoveryCoverageSlaConfig,
) -> tuple[ResearchSourceDiscoveryCoverageSlaRow, ...]:
    return tuple(sorted((_coverage_row(row, config=config) for row in inputs), key=_row_sort_key))


def _coverage_row(
    row: ResearchSourceDiscoveryCoverageSlaInput,
    *,
    config: ResearchSourceDiscoveryCoverageSlaConfig,
) -> ResearchSourceDiscoveryCoverageSlaRow:
    missing_source_count = _quantize(
        max(row.required_source_count - row.discovered_source_count, ZERO),
    )
    source_class_found = row.discovered_source_count > ZERO
    source_class_covered = row.discovered_source_count >= row.required_source_count
    source_class_coverage_ratio = _ratio(
        row.discovered_source_count,
        row.required_source_count,
    )
    parse_quality_ready_ratio = _ratio(
        row.parse_ready_source_count,
        row.discovered_source_count,
    )
    retry_backlog_ratio = _ratio(row.retry_backlog_count, row.required_source_count)
    manual_review_urgency_ratio = _ratio(
        row.manual_review_item_count,
        row.manual_review_capacity_count,
    )
    reason_codes = _row_reason_codes(
        row,
        source_class_found=source_class_found,
        source_class_coverage_ratio=source_class_coverage_ratio,
        parse_quality_ready_ratio=parse_quality_ready_ratio,
        retry_backlog_ratio=retry_backlog_ratio,
        manual_review_urgency_ratio=manual_review_urgency_ratio,
        config=config,
    )
    return ResearchSourceDiscoveryCoverageSlaRow(
        source_class=row.source_class,
        required_source_count=row.required_source_count,
        discovered_source_count=row.discovered_source_count,
        missing_source_count=missing_source_count,
        source_class_found=source_class_found,
        source_class_covered=source_class_covered,
        source_class_coverage_ratio=source_class_coverage_ratio,
        discovery_freshness_age_seconds=row.discovery_freshness_age_seconds,
        parse_ready_source_count=row.parse_ready_source_count,
        parse_quality_ready_ratio=parse_quality_ready_ratio,
        retry_backlog_count=row.retry_backlog_count,
        retry_backlog_ratio=retry_backlog_ratio,
        manual_review_item_count=row.manual_review_item_count,
        manual_review_capacity_count=row.manual_review_capacity_count,
        manual_review_urgency_ratio=manual_review_urgency_ratio,
        status=_row_status(
            row,
            source_class_found=source_class_found,
            source_class_coverage_ratio=source_class_coverage_ratio,
            parse_quality_ready_ratio=parse_quality_ready_ratio,
            retry_backlog_ratio=retry_backlog_ratio,
            manual_review_urgency_ratio=manual_review_urgency_ratio,
            reason_codes=reason_codes,
            config=config,
        ),
        reason_codes=reason_codes,
    )


def _row_reason_codes(
    row: ResearchSourceDiscoveryCoverageSlaInput,
    *,
    source_class_found: bool,
    source_class_coverage_ratio: Decimal,
    parse_quality_ready_ratio: Decimal,
    retry_backlog_ratio: Decimal,
    manual_review_urgency_ratio: Decimal,
    config: ResearchSourceDiscoveryCoverageSlaConfig,
) -> tuple[str, ...]:
    reasons: list[str] = []
    if source_class_coverage_ratio < config.min_source_class_found_watch_ratio:
        reasons.append(INCOMPLETE_CLASS_COVERAGE_REASON)
    if not source_class_found:
        reasons.append(MISSING_SOURCE_CLASS_REASON)
    if row.discovery_freshness_age_seconds >= config.max_discovery_freshness_watch_seconds:
        reasons.append(STALE_DISCOVERY_FRESHNESS_REASON)
    if parse_quality_ready_ratio <= config.min_parse_quality_ready_watch_ratio:
        reasons.append(PARSE_QUALITY_NOT_READY_REASON)
    if retry_backlog_ratio >= config.max_retry_backlog_watch_ratio:
        reasons.append(RETRY_BACKLOG_PRESSURE_REASON)
    if manual_review_urgency_ratio >= config.max_manual_review_urgency_watch_ratio:
        reasons.append(MANUAL_REVIEW_URGENT_REASON)
    if not reasons:
        reasons.append(CLEAR_REASON)
    return tuple(reasons)


def _row_status(
    row: ResearchSourceDiscoveryCoverageSlaInput,
    *,
    source_class_found: bool,
    source_class_coverage_ratio: Decimal,
    parse_quality_ready_ratio: Decimal,
    retry_backlog_ratio: Decimal,
    manual_review_urgency_ratio: Decimal,
    reason_codes: tuple[str, ...],
    config: ResearchSourceDiscoveryCoverageSlaConfig,
) -> str:
    if reason_codes == (CLEAR_REASON,):
        return "pass"
    if (
        not source_class_found
        or source_class_coverage_ratio <= config.min_source_class_found_block_ratio
        or row.discovery_freshness_age_seconds
        >= config.max_discovery_freshness_block_seconds
        or parse_quality_ready_ratio <= config.min_parse_quality_ready_block_ratio
        or retry_backlog_ratio >= config.max_retry_backlog_block_ratio
        or manual_review_urgency_ratio >= config.max_manual_review_urgency_block_ratio
    ):
        return "block"
    return "watch"


def _report_status(rows: tuple[ResearchSourceDiscoveryCoverageSlaRow, ...]) -> str:
    if not rows:
        return "block"
    if any(row.status == "block" for row in rows):
        return "block"
    if any(row.status == "watch" for row in rows):
        return "watch"
    return "pass"


def _report_reason_codes(
    rows: tuple[ResearchSourceDiscoveryCoverageSlaRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return (NO_SOURCE_CLASSES_REASON,)
    reasons: list[str] = []
    for row in rows:
        reasons.extend(reason for reason in row.reason_codes if reason != CLEAR_REASON)
    if not reasons:
        reasons.append(CLEAR_REASON)
    return _normalize_reason_codes(tuple(reasons))


def _normalize_inputs(
    value: object,
) -> tuple[ResearchSourceDiscoveryCoverageSlaInput, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("inputs must be a list or tuple")
    rows = tuple(value)
    seen: set[str] = set()
    for row in rows:
        if type(row) is not ResearchSourceDiscoveryCoverageSlaInput:
            raise ValueError("inputs must contain ResearchSourceDiscoveryCoverageSlaInput")
        _require_hard_flags("input", row)
        if row.source_class in seen:
            raise ValueError("inputs must be unique by source_class")
        seen.add(row.source_class)
    return tuple(sorted(rows, key=lambda row: row.source_class))


def _normalize_rows(
    value: object,
) -> tuple[ResearchSourceDiscoveryCoverageSlaRow, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("coverage_rows must be a list or tuple")
    rows = tuple(value)
    seen: set[str] = set()
    for row in rows:
        if type(row) is not ResearchSourceDiscoveryCoverageSlaRow:
            raise ValueError("coverage_rows must contain ResearchSourceDiscoveryCoverageSlaRow")
        _require_hard_flags("row", row)
        if row.source_class in seen:
            raise ValueError("coverage_rows must be unique by source_class")
        seen.add(row.source_class)
    return tuple(sorted(rows, key=_row_sort_key))


def _row_sort_key(row: ResearchSourceDiscoveryCoverageSlaRow) -> tuple[Decimal, str]:
    return (STATUS_RANK[row.status], row.source_class)


def _normalize_reason_codes(value: object) -> tuple[str, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("reason_codes must be a list or tuple")
    normalized: list[str] = []
    for reason_code in value:
        _require_public_identifier("reason_code", reason_code)
        if reason_code not in REASON_CODES:
            raise ValueError("reason_code must be supported")
        if reason_code not in normalized:
            normalized.append(reason_code)
    return tuple(reason_code for reason_code in REASON_CODES if reason_code in normalized)


def _validate_config(config: ResearchSourceDiscoveryCoverageSlaConfig) -> None:
    if (
        config.min_source_class_found_block_ratio
        > config.min_source_class_found_watch_ratio
    ):
        raise ValueError("source class found block threshold must not exceed watch threshold")
    if (
        config.max_missing_class_pressure_block_ratio
        < config.max_missing_class_pressure_watch_ratio
    ):
        raise ValueError(
            "missing class pressure block threshold must not be below watch threshold",
        )
    if (
        config.max_discovery_freshness_block_seconds
        < config.max_discovery_freshness_watch_seconds
    ):
        raise ValueError("freshness block threshold must not be below watch threshold")
    if (
        config.min_parse_quality_ready_block_ratio
        > config.min_parse_quality_ready_watch_ratio
    ):
        raise ValueError("parse readiness block threshold must not exceed watch threshold")
    if config.max_retry_backlog_block_ratio < config.max_retry_backlog_watch_ratio:
        raise ValueError("retry backlog block threshold must not be below watch threshold")
    if (
        config.max_manual_review_urgency_block_ratio
        < config.max_manual_review_urgency_watch_ratio
    ):
        raise ValueError("manual review urgency block threshold must not be below watch threshold")


def _validate_input(row: ResearchSourceDiscoveryCoverageSlaInput) -> None:
    if row.discovered_source_count > row.required_source_count:
        raise ValueError("discovered_source_count must not exceed required_source_count")
    if row.parse_ready_source_count > row.discovered_source_count:
        raise ValueError("parse_ready_source_count must not exceed discovered_source_count")
    if row.retry_backlog_count > row.required_source_count:
        raise ValueError("retry_backlog_count must not exceed required_source_count")
    if row.manual_review_item_count > row.manual_review_capacity_count:
        raise ValueError(
            "manual_review_item_count must not exceed manual_review_capacity_count",
        )


def _validate_row(row: ResearchSourceDiscoveryCoverageSlaRow) -> None:
    expected_missing = _quantize(row.required_source_count - row.discovered_source_count)
    if row.missing_source_count != expected_missing:
        raise ValueError("missing_source_count must match required less discovered")
    if row.source_class_found != (row.discovered_source_count > ZERO):
        raise ValueError("source_class_found must match discovered_source_count")
    if row.source_class_covered != (
        row.discovered_source_count >= row.required_source_count
    ):
        raise ValueError("source_class_covered must match discovered_source_count")
    if row.source_class_coverage_ratio != _ratio(
        row.discovered_source_count,
        row.required_source_count,
    ):
        raise ValueError("source_class_coverage_ratio must match source counts")
    if row.parse_quality_ready_ratio != _ratio(
        row.parse_ready_source_count,
        row.discovered_source_count,
    ):
        raise ValueError("parse_quality_ready_ratio must match source counts")
    if row.retry_backlog_ratio != _ratio(
        row.retry_backlog_count,
        row.required_source_count,
    ):
        raise ValueError("retry_backlog_ratio must match source counts")
    if row.manual_review_urgency_ratio != _ratio(
        row.manual_review_item_count,
        row.manual_review_capacity_count,
    ):
        raise ValueError("manual_review_urgency_ratio must match review counts")


def _validate_report(report: ResearchSourceDiscoveryCoverageSlaReport) -> None:
    rows = report.coverage_rows
    required_source_class_count = _count(len(rows))
    found_source_class_count = _count(sum(row.source_class_found for row in rows))
    covered_source_class_count = _count(sum(row.source_class_covered for row in rows))
    missing_source_class_count = _count(sum(not row.source_class_found for row in rows))
    required_source_count = _sum_rows(rows, "required_source_count")
    discovered_source_count = _sum_rows(rows, "discovered_source_count")
    parse_ready_source_count = _sum_rows(rows, "parse_ready_source_count")
    retry_backlog_count = _sum_rows(rows, "retry_backlog_count")
    manual_review_item_count = _sum_rows(rows, "manual_review_item_count")
    manual_review_capacity_count = _sum_rows(rows, "manual_review_capacity_count")
    expected_values = {
        "required_source_class_count": required_source_class_count,
        "found_source_class_count": found_source_class_count,
        "covered_source_class_count": covered_source_class_count,
        "missing_source_class_count": missing_source_class_count,
        "required_source_count": required_source_count,
        "discovered_source_count": discovered_source_count,
        "missing_source_count": _sum_rows(rows, "missing_source_count"),
        "source_class_found_ratio": _ratio(
            found_source_class_count,
            required_source_class_count,
        ),
        "source_class_coverage_ratio": _ratio(
            covered_source_class_count,
            required_source_class_count,
        ),
        "missing_class_pressure_ratio": _ratio(
            missing_source_class_count,
            required_source_class_count,
        ),
        "discovery_freshness_age_seconds": _max_rows(
            rows,
            "discovery_freshness_age_seconds",
        ),
        "parse_ready_source_count": parse_ready_source_count,
        "parse_quality_ready_ratio": _ratio(
            parse_ready_source_count,
            discovered_source_count,
        ),
        "retry_backlog_count": retry_backlog_count,
        "retry_backlog_ratio": _ratio(retry_backlog_count, required_source_count),
        "manual_review_item_count": manual_review_item_count,
        "manual_review_capacity_count": manual_review_capacity_count,
        "manual_review_urgency_ratio": _ratio(
            manual_review_item_count,
            manual_review_capacity_count,
        ),
        "pass_count": _count(sum(row.status == "pass" for row in rows)),
        "watch_count": _count(sum(row.status == "watch" for row in rows)),
        "block_count": _count(sum(row.status == "block" for row in rows)),
        "status": _report_status(rows),
        "reason_codes": _report_reason_codes(rows),
    }
    for field_name, expected in expected_values.items():
        if getattr(report, field_name) != expected:
            raise ValueError(f"{field_name} must match coverage_rows")


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in PHASE_FLAG_FIELDS:
        if getattr(value, field_name) is not True:
            raise ValueError(f"{field_name} must be True for {label}")


def _require_public_identifier(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not PUBLIC_IDENTIFIER_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a public identifier")
    _reject_public_string(field_name, value)
    return value


def _require_status(field_name: str, value: object) -> str:
    if type(value) is not str or value not in STATUSES:
        raise ValueError(f"{field_name} must be pass, watch, or block")
    return value


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return _quantize(value)


def _require_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _require_positive_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_nonnegative_decimal(field_name, value)
    if normalized <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _require_ratio(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < ZERO or normalized > ONE:
        raise ValueError(f"{field_name} must be between zero and one")
    return normalized


def _require_or_set_digest(report: ResearchSourceDiscoveryCoverageSlaReport) -> None:
    expected = _report_digest(report)
    if report.derived_validation_digest == "":
        object.__setattr__(report, "derived_validation_digest", expected)
        return
    if not DIGEST_RE.fullmatch(report.derived_validation_digest):
        raise ValueError("derived_validation_digest must be a sha256 digest")
    if report.derived_validation_digest != expected:
        raise ValueError("derived_validation_digest must match report payload")


def _verify_public_digest(payload: dict[str, Any]) -> None:
    digest = payload.get("derived_validation_digest")
    if type(digest) is not str or not DIGEST_RE.fullmatch(digest):
        raise ValueError("derived_validation_digest must be a sha256 digest")
    unsigned = dict(payload)
    unsigned.pop("derived_validation_digest", None)
    if digest != _digest_from_ready_payload(unsigned):
        raise ValueError("derived_validation_digest must match report payload")


def _report_digest(report: ResearchSourceDiscoveryCoverageSlaReport) -> str:
    values = asdict(report)
    values.pop("derived_validation_digest", None)
    return _digest_from_ready_payload(_json_ready(values))


def _digest_from_ready_payload(payload: Mapping[str, Any]) -> str:
    _reject_public_payload(payload)
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return sha256(canonical.encode()).hexdigest()


def _json_ready(value: Any) -> Any:
    if value is None:
        return None
    if is_dataclass(value) and not isinstance(value, type):
        return _json_ready(asdict(value))
    if type(value) is Decimal:
        if not value.is_finite():
            raise ValueError("Decimal payload value must be finite")
        return str(value)
    if type(value) is datetime:
        return _as_utc("datetime payload value", value).isoformat()
    if type(value) is bool or type(value) is str:
        return value
    if type(value) is int or isinstance(value, float):
        raise ValueError("public numeric values must be Decimal strings")
    if isinstance(value, Mapping):
        ready: dict[str, Any] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            ready[key] = _json_ready(item)
        return ready
    if type(value) in (list, tuple):
        return [_json_ready(item) for item in value]
    raise ValueError("payload value is not JSON serializable")


def _reject_public_payload(value: object) -> None:
    if isinstance(value, Mapping):
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            _reject_public_key(key)
            if key in PHASE_FLAG_FIELDS and item is not True:
                raise ValueError(f"{key} must be True")
            _reject_public_payload(item)
        return
    if type(value) in (list, tuple):
        for item in value:
            _reject_public_payload(item)
        return
    if type(value) is str:
        _reject_public_string("payload", value)
        return
    if value is None or type(value) is bool:
        return
    raise ValueError("payload value must be public JSON")


def _reject_public_key(key: str) -> None:
    lowered = key.lower()
    if any(term in lowered for term in UNSAFE_PUBLIC_TERMS):
        raise ValueError(f"{key} has unsafe public field")


def _reject_public_string(field_name: str, value: str) -> None:
    lowered = value.lower()
    if value.strip() != value:
        raise ValueError(f"{field_name} has unsafe public value")
    if "://" in lowered or "?" in lowered or "@" in lowered:
        raise ValueError(f"{field_name} has unsafe public value")
    if any(term in lowered for term in UNSAFE_PUBLIC_TERMS):
        raise ValueError(f"{field_name} has unsafe public value")


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _sum_rows(rows: tuple[ResearchSourceDiscoveryCoverageSlaRow, ...], field_name: str) -> Decimal:
    return _quantize(sum((getattr(row, field_name) for row in rows), ZERO))


def _max_rows(rows: tuple[ResearchSourceDiscoveryCoverageSlaRow, ...], field_name: str) -> Decimal:
    return max((getattr(row, field_name) for row in rows), default=ZERO)


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO:
        return ZERO
    return _clamp_ratio(numerator / denominator)


def _clamp_ratio(value: Decimal) -> Decimal:
    normalized = _quantize(value)
    if normalized < ZERO:
        return ZERO
    if normalized > ONE:
        return ONE
    return normalized


def _count(value: int) -> Decimal:
    if value < 0:
        raise ValueError("count must be nonnegative")
    return Decimal(value).quantize(QUANT)


def _quantize(value: Decimal) -> Decimal:
    return value.quantize(QUANT, rounding=ROUND_HALF_UP)


__all__ = (
    "DEFAULT_RESEARCH_SOURCE_DISCOVERY_COVERAGE_SLA_CONFIG_VERSION",
    "STATUSES",
    "ResearchSourceDiscoveryCoverageSlaConfig",
    "ResearchSourceDiscoveryCoverageSlaInput",
    "ResearchSourceDiscoveryCoverageSlaReport",
    "ResearchSourceDiscoveryCoverageSlaRow",
    "build_research_source_discovery_coverage_sla_report",
    "research_source_discovery_coverage_sla_report_payload",
    "validate_research_source_discovery_coverage_sla_report_payload",
)
