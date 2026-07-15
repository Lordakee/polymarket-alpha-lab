"""Pure in-memory source evidence to resolution authority gap report."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import asdict, dataclass, field, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, DecimalException, ROUND_HALF_EVEN, localcontext
import hashlib
import json
from typing import Any

from polymarket_alpha_lab.team_paper_guard import (
    json_ready_no_floats,
    require_paper_only_flags,
)


DEFAULT_RESEARCH_SOURCE_RESOLUTION_AUTHORITY_GAP_REPORT_CONFIG_VERSION = (
    "research-source-resolution-authority-gap-report-v0"
)
RESEARCH_SOURCE_RESOLUTION_AUTHORITY_GAP_REPORT_STATUSES = ("pass", "watch", "block")

EMPTY_REASON = "research_source_resolution_authority_gap_empty"
CLEAR_REASON = "resolution_authority_gap_clear"
LOW_AUTHORITY_COVERAGE_WATCH_REASON = "low_authority_coverage_watch"
LOW_AUTHORITY_COVERAGE_BLOCK_REASON = "low_authority_coverage_block"
STALE_EVIDENCE_WATCH_REASON = "stale_evidence_watch"
STALE_EVIDENCE_BLOCK_REASON = "stale_evidence_block"
LOW_INDEPENDENCE_WATCH_REASON = "low_independence_watch"
LOW_INDEPENDENCE_BLOCK_REASON = "low_independence_block"
CONTRADICTION_SEVERITY_WATCH_REASON = "contradiction_severity_watch"
CONTRADICTION_SEVERITY_BLOCK_REASON = "contradiction_severity_block"
WEAK_RULE_MAPPING_WATCH_REASON = "weak_rule_mapping_watch"
WEAK_RULE_MAPPING_BLOCK_REASON = "weak_rule_mapping_block"

ROW_REASON_CODES = (
    CLEAR_REASON,
    LOW_AUTHORITY_COVERAGE_BLOCK_REASON,
    STALE_EVIDENCE_BLOCK_REASON,
    LOW_INDEPENDENCE_BLOCK_REASON,
    CONTRADICTION_SEVERITY_BLOCK_REASON,
    WEAK_RULE_MAPPING_BLOCK_REASON,
    LOW_AUTHORITY_COVERAGE_WATCH_REASON,
    STALE_EVIDENCE_WATCH_REASON,
    LOW_INDEPENDENCE_WATCH_REASON,
    CONTRADICTION_SEVERITY_WATCH_REASON,
    WEAK_RULE_MAPPING_WATCH_REASON,
)
REPORT_REASON_CODES = (EMPTY_REASON,) + ROW_REASON_CODES
REPORT_TRIGGER_REASON_CODES = tuple(
    reason for reason in REPORT_REASON_CODES if reason not in (EMPTY_REASON, CLEAR_REASON)
)

DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
QUANT = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
SECONDS_PER_DAY = Decimal("86400")
MICROSECONDS_PER_SECOND = Decimal("1000000")
SHA256_HEX_LENGTH = 64

CONFIG_PUBLIC_PAYLOAD_FIELDS = (
    "config_version",
    "min_authority_coverage_ratio",
    "block_authority_coverage_ratio",
    "freshness_watch_age_seconds",
    "freshness_block_age_seconds",
    "min_independence_score",
    "block_independence_score",
    "contradiction_watch_severity",
    "contradiction_block_severity",
    "min_rule_mapping_score",
    "block_rule_mapping_score",
    "paper_only",
    "report_only",
    "readonly",
)
REPORT_PUBLIC_PAYLOAD_FIELDS = (
    "generated_at",
    "config_version",
    "criteria_group_count",
    "evidence_count",
    "pass_criteria_group_count",
    "watch_criteria_group_count",
    "block_criteria_group_count",
    "low_authority_coverage_count",
    "stale_evidence_count",
    "low_independence_count",
    "contradiction_severity_count",
    "weak_rule_mapping_count",
    "highest_authority_gap_score",
    "oldest_latest_evidence_age_seconds",
    "status",
    "reason_codes",
    "rows",
    "config",
    "derived_validation_digest",
    "paper_only",
    "report_only",
    "readonly",
)
ROW_PUBLIC_PAYLOAD_FIELDS = (
    "criteria_group",
    "evidence_count",
    "source_family_count",
    "latest_evidence_age_seconds",
    "average_evidence_age_seconds",
    "average_authority_coverage_ratio",
    "average_independence_score",
    "contradiction_severity",
    "average_rule_mapping_score",
    "authority_gap_score",
    "status",
    "reason_codes",
    "paper_only",
    "report_only",
    "readonly",
)
REPORT_COUNT_FIELDS = (
    "criteria_group_count",
    "evidence_count",
    "pass_criteria_group_count",
    "watch_criteria_group_count",
    "block_criteria_group_count",
    "low_authority_coverage_count",
    "stale_evidence_count",
    "low_independence_count",
    "contradiction_severity_count",
    "weak_rule_mapping_count",
)
ROW_COUNT_FIELDS = ("evidence_count", "source_family_count")
ROW_RATIO_FIELDS = (
    "average_authority_coverage_ratio",
    "average_independence_score",
    "contradiction_severity",
    "average_rule_mapping_score",
    "authority_gap_score",
)


@dataclass(frozen=True)
class ResearchSourceResolutionAuthorityGapConfig:
    config_version: str = (
        DEFAULT_RESEARCH_SOURCE_RESOLUTION_AUTHORITY_GAP_REPORT_CONFIG_VERSION
    )
    min_authority_coverage_ratio: Decimal = Decimal("0.800000")
    block_authority_coverage_ratio: Decimal = Decimal("0.500000")
    freshness_watch_age_seconds: Decimal = Decimal("3600.000000")
    freshness_block_age_seconds: Decimal = Decimal("7200.000000")
    min_independence_score: Decimal = Decimal("0.700000")
    block_independence_score: Decimal = Decimal("0.500000")
    contradiction_watch_severity: Decimal = Decimal("0.300000")
    contradiction_block_severity: Decimal = Decimal("0.600000")
    min_rule_mapping_score: Decimal = Decimal("0.800000")
    block_rule_mapping_score: Decimal = Decimal("0.500000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchSourceResolutionAuthorityGapConfig does not support subclassing",
        )

    def __post_init__(self) -> None:
        _require_exact_type("config", self, ResearchSourceResolutionAuthorityGapConfig)
        _require_canonical_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_SOURCE_RESOLUTION_AUTHORITY_GAP_REPORT_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "min_authority_coverage_ratio",
            "block_authority_coverage_ratio",
            "min_independence_score",
            "block_independence_score",
            "contradiction_watch_severity",
            "contradiction_block_severity",
            "min_rule_mapping_score",
            "block_rule_mapping_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "freshness_watch_age_seconds",
            "freshness_block_age_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_positive_decimal(field_name, getattr(self, field_name)),
            )
        _validate_config(self)
        require_paper_only_flags("config", self)
        _reject_unsafe_public_surface("config", self)


@dataclass(frozen=True)
class ResearchSourceResolutionAuthorityGapInput:
    criteria_group: str
    source_family: str
    evidence_observed_at: datetime
    authority_coverage_ratio: Decimal
    independence_score: Decimal
    contradiction_severity: Decimal
    rule_mapping_score: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchSourceResolutionAuthorityGapInput does not support subclassing",
        )

    def __post_init__(self) -> None:
        _require_exact_type("input", self, ResearchSourceResolutionAuthorityGapInput)
        object.__setattr__(
            self,
            "criteria_group",
            _require_public_label("criteria_group", self.criteria_group),
        )
        object.__setattr__(
            self,
            "source_family",
            _require_public_label("source_family", self.source_family),
        )
        object.__setattr__(
            self,
            "evidence_observed_at",
            _as_utc("evidence_observed_at", self.evidence_observed_at),
        )
        for field_name in (
            "authority_coverage_ratio",
            "independence_score",
            "contradiction_severity",
            "rule_mapping_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio(field_name, getattr(self, field_name)),
            )
        require_paper_only_flags("input", self)
        _reject_unsafe_public_surface("input", self)


@dataclass(frozen=True)
class ResearchSourceResolutionAuthorityGapRow:
    criteria_group: str
    evidence_count: Decimal
    source_family_count: Decimal
    latest_evidence_age_seconds: Decimal
    average_evidence_age_seconds: Decimal
    average_authority_coverage_ratio: Decimal
    average_independence_score: Decimal
    contradiction_severity: Decimal
    average_rule_mapping_score: Decimal
    authority_gap_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchSourceResolutionAuthorityGapRow does not support subclassing",
        )

    def __post_init__(self) -> None:
        _require_exact_type("row", self, ResearchSourceResolutionAuthorityGapRow)
        object.__setattr__(
            self,
            "criteria_group",
            _require_public_label("criteria_group", self.criteria_group),
        )
        for field_name in ROW_COUNT_FIELDS:
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_whole_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "latest_evidence_age_seconds",
            "average_evidence_age_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in ROW_RATIO_FIELDS:
            object.__setattr__(
                self,
                field_name,
                _require_ratio(field_name, getattr(self, field_name)),
            )
        _require_status("status", self.status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, ROW_REASON_CODES),
        )
        _validate_row(self)
        require_paper_only_flags("authority gap row", self)
        _reject_unsafe_public_surface("row", self)


@dataclass(frozen=True)
class ResearchSourceResolutionAuthorityGapReport:
    generated_at: datetime
    config_version: str
    criteria_group_count: Decimal
    evidence_count: Decimal
    pass_criteria_group_count: Decimal
    watch_criteria_group_count: Decimal
    block_criteria_group_count: Decimal
    low_authority_coverage_count: Decimal
    stale_evidence_count: Decimal
    low_independence_count: Decimal
    contradiction_severity_count: Decimal
    weak_rule_mapping_count: Decimal
    highest_authority_gap_score: Decimal
    oldest_latest_evidence_age_seconds: Decimal
    status: str
    reason_codes: tuple[str, ...]
    rows: tuple[ResearchSourceResolutionAuthorityGapRow, ...]
    config: ResearchSourceResolutionAuthorityGapConfig = field(
        default_factory=ResearchSourceResolutionAuthorityGapConfig,
    )
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchSourceResolutionAuthorityGapReport does not support subclassing",
        )

    def __post_init__(self) -> None:
        _require_exact_type("report", self, ResearchSourceResolutionAuthorityGapReport)
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_SOURCE_RESOLUTION_AUTHORITY_GAP_REPORT_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        _validate_public_config_snapshot(self.config)
        object.__setattr__(
            self,
            "config",
            ResearchSourceResolutionAuthorityGapConfig(**asdict(self.config)),
        )
        if self.config_version != self.config.config_version:
            raise ValueError("config_version must match config")
        for field_name in REPORT_COUNT_FIELDS:
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_whole_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "highest_authority_gap_score",
            _require_ratio(
                "highest_authority_gap_score",
                self.highest_authority_gap_score,
            ),
        )
        for field_name in ("oldest_latest_evidence_age_seconds",):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        _require_status("status", self.status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(
                "reason_codes",
                self.reason_codes,
                REPORT_REASON_CODES,
            ),
        )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        _validate_report(self, config=self.config)
        require_paper_only_flags("authority gap report", self)
        _reject_unsafe_public_surface("report", self)
        if self.derived_validation_digest == "":
            object.__setattr__(
                self,
                "derived_validation_digest",
                _report_digest_from_public_payload(self),
            )
        else:
            _require_sha256("derived_validation_digest", self.derived_validation_digest)
            if self.derived_validation_digest != _report_digest_from_public_payload(self):
                raise ValueError("derived_validation_digest must match report payload")


def build_research_source_resolution_authority_gap_report(
    inputs: list[ResearchSourceResolutionAuthorityGapInput]
    | tuple[ResearchSourceResolutionAuthorityGapInput, ...],
    *,
    config: ResearchSourceResolutionAuthorityGapConfig,
    generated_at: datetime,
) -> ResearchSourceResolutionAuthorityGapReport:
    """Build a deterministic report-only source-resolution authority gap snapshot."""

    if type(config) is not ResearchSourceResolutionAuthorityGapConfig:
        raise ValueError("config must be a ResearchSourceResolutionAuthorityGapConfig")
    require_paper_only_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    rows = _authority_gap_rows(
        _normalize_inputs(inputs, generated_at=generated_at_utc),
        config=config,
        generated_at=generated_at_utc,
    )
    return ResearchSourceResolutionAuthorityGapReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        criteria_group_count=_count(len(rows)),
        evidence_count=_sum_rows(rows, "evidence_count"),
        pass_criteria_group_count=_status_count(rows, "pass"),
        watch_criteria_group_count=_status_count(rows, "watch"),
        block_criteria_group_count=_status_count(rows, "block"),
        low_authority_coverage_count=_reason_count(
            rows,
            (
                LOW_AUTHORITY_COVERAGE_WATCH_REASON,
                LOW_AUTHORITY_COVERAGE_BLOCK_REASON,
            ),
        ),
        stale_evidence_count=_reason_count(
            rows,
            (STALE_EVIDENCE_WATCH_REASON, STALE_EVIDENCE_BLOCK_REASON),
        ),
        low_independence_count=_reason_count(
            rows,
            (LOW_INDEPENDENCE_WATCH_REASON, LOW_INDEPENDENCE_BLOCK_REASON),
        ),
        contradiction_severity_count=_reason_count(
            rows,
            (CONTRADICTION_SEVERITY_WATCH_REASON, CONTRADICTION_SEVERITY_BLOCK_REASON),
        ),
        weak_rule_mapping_count=_reason_count(
            rows,
            (WEAK_RULE_MAPPING_WATCH_REASON, WEAK_RULE_MAPPING_BLOCK_REASON),
        ),
        highest_authority_gap_score=max(
            (row.authority_gap_score for row in rows),
            default=ZERO,
        ),
        oldest_latest_evidence_age_seconds=max(
            (row.latest_evidence_age_seconds for row in rows),
            default=ZERO,
        ),
        status=_report_status(rows),
        reason_codes=_report_reason_codes(rows),
        rows=rows,
        config=config,
    )


def research_source_resolution_authority_gap_report_payload(
    report: object,
) -> dict[str, Any]:
    report = _report_from_report_or_public_payload(report)
    validate_research_source_resolution_authority_gap_report_digest(report)
    require_paper_only_flags("report", report)
    _reject_unsafe_public_surface("report", report)
    payload = json_ready_no_floats(report)
    if type(payload) is not dict:
        raise ValueError("payload must be a dict")
    _validate_public_payload_schema(payload)
    _reject_unsafe_public_surface("payload", payload)
    return payload


def research_source_resolution_authority_gap_report_digest(
    report: object,
) -> str:
    report = _report_from_report_or_public_payload(report)
    return _report_digest_from_public_payload(report)


def validate_research_source_resolution_authority_gap_report_digest(
    report: object,
) -> None:
    report = _report_from_report_or_public_payload(report)
    _require_sha256("derived_validation_digest", report.derived_validation_digest)
    if report.derived_validation_digest != _report_digest_from_public_payload(report):
        raise ValueError("derived_validation_digest must match report payload")


def _report_from_report_or_public_payload(
    value: object,
) -> ResearchSourceResolutionAuthorityGapReport:
    if type(value) is ResearchSourceResolutionAuthorityGapReport:
        return value
    if isinstance(value, Mapping):
        return _report_from_public_payload(value)
    raise ValueError(
        "report must be a ResearchSourceResolutionAuthorityGapReport or public mapping",
    )


def _report_from_public_payload(
    value: object,
) -> ResearchSourceResolutionAuthorityGapReport:
    report_payload = _require_exact_payload_fields(
        "report",
        value,
        REPORT_PUBLIC_PAYLOAD_FIELDS,
    )
    expected_digest = _payload_validation_digest(report_payload)
    supplied_digest = report_payload["derived_validation_digest"]
    if supplied_digest != "" and supplied_digest != expected_digest:
        raise ValueError("derived_validation_digest must match report payload")
    generated_at = _require_public_datetime_string(
        "generated_at",
        report_payload["generated_at"],
    )
    config = _validate_public_config_payload_schema(report_payload["config"])
    parsed_report_values: dict[str, object] = {
        field_name: _require_public_decimal_string(
            field_name,
            report_payload[field_name],
            _require_nonnegative_whole_decimal,
        )
        for field_name in REPORT_COUNT_FIELDS
    }
    parsed_report_values["highest_authority_gap_score"] = (
        _require_public_decimal_string(
            "highest_authority_gap_score",
            report_payload["highest_authority_gap_score"],
            _require_ratio,
        )
    )
    parsed_report_values["oldest_latest_evidence_age_seconds"] = (
        _require_public_decimal_string(
            "oldest_latest_evidence_age_seconds",
            report_payload["oldest_latest_evidence_age_seconds"],
            _require_nonnegative_decimal,
        )
    )
    rows_value = report_payload["rows"]
    if type(rows_value) is not list:
        raise ValueError("rows must be a list in the public payload schema")
    rows = tuple(
        _validate_public_row_payload_schema(index, row, config=config)
        for index, row in enumerate(rows_value)
    )
    reason_codes = _require_public_reason_code_list(
        "reason_codes",
        report_payload["reason_codes"],
        REPORT_REASON_CODES,
    )
    _require_public_payload_flags(report_payload)
    return ResearchSourceResolutionAuthorityGapReport(
        generated_at=generated_at,
        config_version=report_payload["config_version"],
        status=report_payload["status"],
        reason_codes=reason_codes,
        rows=rows,
        config=config,
        derived_validation_digest=report_payload["derived_validation_digest"],
        paper_only=report_payload["paper_only"],
        report_only=report_payload["report_only"],
        readonly=report_payload["readonly"],
        **parsed_report_values,
    )


def _validate_public_report_snapshot(
    report: ResearchSourceResolutionAuthorityGapReport,
) -> None:
    _require_exact_type("report", report, ResearchSourceResolutionAuthorityGapReport)
    _as_utc("generated_at", report.generated_at)
    _require_canonical_string("config_version", report.config_version)
    if (
        report.config_version
        != DEFAULT_RESEARCH_SOURCE_RESOLUTION_AUTHORITY_GAP_REPORT_CONFIG_VERSION
    ):
        raise ValueError("config_version must be the supported config version")
    _validate_public_config_snapshot(report.config)
    if report.config_version != report.config.config_version:
        raise ValueError("config_version must match config")
    for field_name in REPORT_COUNT_FIELDS:
        _require_nonnegative_whole_decimal(field_name, getattr(report, field_name))
    _require_ratio(
        "highest_authority_gap_score",
        report.highest_authority_gap_score,
    )
    for field_name in ("oldest_latest_evidence_age_seconds",):
        _require_nonnegative_decimal(field_name, getattr(report, field_name))
    _require_status("status", report.status)
    _normalize_reason_codes("reason_codes", report.reason_codes, REPORT_REASON_CODES)
    rows = _normalize_rows(report.rows)
    for row in rows:
        _validate_public_row_snapshot(row)
    _validate_report(report, config=report.config)
    require_paper_only_flags("authority gap report", report)


def _validate_public_row_snapshot(
    row: ResearchSourceResolutionAuthorityGapRow,
) -> None:
    _require_exact_type("row", row, ResearchSourceResolutionAuthorityGapRow)
    _require_public_label("criteria_group", row.criteria_group)
    for field_name in ROW_COUNT_FIELDS:
        _require_nonnegative_whole_decimal(field_name, getattr(row, field_name))
    for field_name in (
        "latest_evidence_age_seconds",
        "average_evidence_age_seconds",
    ):
        _require_nonnegative_decimal(field_name, getattr(row, field_name))
    for field_name in ROW_RATIO_FIELDS:
        _require_ratio(field_name, getattr(row, field_name))
    _require_status("status", row.status)
    _normalize_reason_codes("reason_codes", row.reason_codes, ROW_REASON_CODES)
    _validate_row(row)
    require_paper_only_flags("authority gap row", row)


def _normalize_inputs(
    value: object,
    *,
    generated_at: datetime,
) -> tuple[ResearchSourceResolutionAuthorityGapInput, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("inputs must be a list or tuple")
    rows = tuple(value)
    for row in rows:
        if type(row) is not ResearchSourceResolutionAuthorityGapInput:
            raise ValueError(
                "inputs must contain ResearchSourceResolutionAuthorityGapInput",
            )
        require_paper_only_flags("input", row)
        if row.evidence_observed_at > generated_at:
            raise ValueError("evidence_observed_at must not be in the future")
    return tuple(
        sorted(rows, key=_input_sort_key),
    )


def _authority_gap_rows(
    inputs: tuple[ResearchSourceResolutionAuthorityGapInput, ...],
    *,
    config: ResearchSourceResolutionAuthorityGapConfig,
    generated_at: datetime,
) -> tuple[ResearchSourceResolutionAuthorityGapRow, ...]:
    grouped: dict[str, list[ResearchSourceResolutionAuthorityGapInput]] = {}
    for row in inputs:
        grouped.setdefault(row.criteria_group, []).append(row)
    return tuple(
        sorted(
            (
                _authority_gap_row(
                    criteria_rows=tuple(criteria_rows),
                    config=config,
                    generated_at=generated_at,
                )
                for criteria_rows in grouped.values()
            ),
            key=_row_sort_key,
        ),
    )


def _authority_gap_row(
    *,
    criteria_rows: tuple[ResearchSourceResolutionAuthorityGapInput, ...],
    config: ResearchSourceResolutionAuthorityGapConfig,
    generated_at: datetime,
) -> ResearchSourceResolutionAuthorityGapRow:
    ages = tuple(_age_seconds(generated_at, row.evidence_observed_at) for row in criteria_rows)
    evidence_count = _count(len(criteria_rows))
    source_family_count = _count(len({row.source_family for row in criteria_rows}))
    latest_age = _quantize(min(ages, default=ZERO))
    average_age = _average(ages)
    average_authority_coverage = _average(
        tuple(row.authority_coverage_ratio for row in criteria_rows),
    )
    average_independence = _average(tuple(row.independence_score for row in criteria_rows))
    contradiction_severity = max(
        (row.contradiction_severity for row in criteria_rows),
        default=ZERO,
    )
    average_rule_mapping = _average(tuple(row.rule_mapping_score for row in criteria_rows))
    reason_codes = _row_reason_codes(
        latest_evidence_age_seconds=latest_age,
        average_authority_coverage_ratio=average_authority_coverage,
        average_independence_score=average_independence,
        contradiction_severity=contradiction_severity,
        average_rule_mapping_score=average_rule_mapping,
        config=config,
    )
    return ResearchSourceResolutionAuthorityGapRow(
        criteria_group=criteria_rows[0].criteria_group,
        evidence_count=evidence_count,
        source_family_count=source_family_count,
        latest_evidence_age_seconds=latest_age,
        average_evidence_age_seconds=average_age,
        average_authority_coverage_ratio=average_authority_coverage,
        average_independence_score=average_independence,
        contradiction_severity=contradiction_severity,
        average_rule_mapping_score=average_rule_mapping,
        authority_gap_score=_authority_gap_score(
            latest_evidence_age_seconds=latest_age,
            average_authority_coverage_ratio=average_authority_coverage,
            average_independence_score=average_independence,
            contradiction_severity=contradiction_severity,
            average_rule_mapping_score=average_rule_mapping,
            reason_codes=reason_codes,
            config=config,
        ),
        status=_row_status(reason_codes),
        reason_codes=reason_codes,
    )


def _row_reason_codes(
    *,
    latest_evidence_age_seconds: Decimal,
    average_authority_coverage_ratio: Decimal,
    average_independence_score: Decimal,
    contradiction_severity: Decimal,
    average_rule_mapping_score: Decimal,
    config: ResearchSourceResolutionAuthorityGapConfig,
) -> tuple[str, ...]:
    reasons: list[str] = []
    if average_authority_coverage_ratio <= config.block_authority_coverage_ratio:
        reasons.append(LOW_AUTHORITY_COVERAGE_BLOCK_REASON)
    elif average_authority_coverage_ratio < config.min_authority_coverage_ratio:
        reasons.append(LOW_AUTHORITY_COVERAGE_WATCH_REASON)
    if latest_evidence_age_seconds >= config.freshness_block_age_seconds:
        reasons.append(STALE_EVIDENCE_BLOCK_REASON)
    elif latest_evidence_age_seconds > config.freshness_watch_age_seconds:
        reasons.append(STALE_EVIDENCE_WATCH_REASON)
    if average_independence_score <= config.block_independence_score:
        reasons.append(LOW_INDEPENDENCE_BLOCK_REASON)
    elif average_independence_score < config.min_independence_score:
        reasons.append(LOW_INDEPENDENCE_WATCH_REASON)
    if contradiction_severity >= config.contradiction_block_severity:
        reasons.append(CONTRADICTION_SEVERITY_BLOCK_REASON)
    elif contradiction_severity >= config.contradiction_watch_severity:
        reasons.append(CONTRADICTION_SEVERITY_WATCH_REASON)
    if average_rule_mapping_score <= config.block_rule_mapping_score:
        reasons.append(WEAK_RULE_MAPPING_BLOCK_REASON)
    elif average_rule_mapping_score < config.min_rule_mapping_score:
        reasons.append(WEAK_RULE_MAPPING_WATCH_REASON)
    if not reasons:
        reasons.append(CLEAR_REASON)
    return tuple(reason for reason in ROW_REASON_CODES if reason in reasons)


def _authority_gap_score(
    *,
    latest_evidence_age_seconds: Decimal,
    average_authority_coverage_ratio: Decimal,
    average_independence_score: Decimal,
    contradiction_severity: Decimal,
    average_rule_mapping_score: Decimal,
    reason_codes: tuple[str, ...],
    config: ResearchSourceResolutionAuthorityGapConfig,
) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        authority_gap = ONE - average_authority_coverage_ratio
        freshness_pressure = min(latest_evidence_age_seconds / config.freshness_block_age_seconds, ONE)
        independence_gap = ONE - average_independence_score
        rule_gap = ONE - average_rule_mapping_score
        if reason_codes == (CLEAR_REASON,):
            score = (
                authority_gap * Decimal("0.200000")
                + freshness_pressure * Decimal("0.005000")
                + contradiction_severity * Decimal("0.050000")
                + rule_gap * Decimal("0.300000")
            )
            return score.quantize(QUANT)
        score = (
            authority_gap
            + freshness_pressure
            + independence_gap
            + contradiction_severity
            + rule_gap
        ) / Decimal("5.000000")
        return max(score - Decimal("0.025000"), ZERO).quantize(QUANT)


def _row_status(reason_codes: tuple[str, ...]) -> str:
    if any(reason.endswith("_block") for reason in reason_codes):
        return "block"
    if reason_codes == (CLEAR_REASON,):
        return "pass"
    return "watch"


def _report_status(rows: tuple[ResearchSourceResolutionAuthorityGapRow, ...]) -> str:
    if any(row.status == "block" for row in rows):
        return "block"
    if any(row.status == "watch" for row in rows):
        return "watch"
    return "pass"


def _report_reason_codes(
    rows: tuple[ResearchSourceResolutionAuthorityGapRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return (EMPTY_REASON,)
    reasons = tuple(
        reason
        for reason in REPORT_TRIGGER_REASON_CODES
        if any(reason in row.reason_codes for row in rows)
    )
    if reasons:
        return reasons
    return (CLEAR_REASON,)


def _input_sort_key(
    row: ResearchSourceResolutionAuthorityGapInput,
) -> tuple[str, str, datetime, Decimal, Decimal, Decimal, Decimal]:
    return (
        row.criteria_group,
        row.source_family,
        row.evidence_observed_at,
        row.authority_coverage_ratio,
        row.independence_score,
        row.contradiction_severity,
        row.rule_mapping_score,
    )


def _row_sort_key(row: ResearchSourceResolutionAuthorityGapRow) -> tuple[Decimal, str]:
    return (-row.authority_gap_score, row.criteria_group)


def _status_count(
    rows: tuple[ResearchSourceResolutionAuthorityGapRow, ...],
    status: str,
) -> Decimal:
    return _count(sum(1 for row in rows if row.status == status))


def _reason_count(
    rows: tuple[ResearchSourceResolutionAuthorityGapRow, ...],
    reasons: tuple[str, ...],
) -> Decimal:
    return _count(sum(1 for row in rows if any(reason in row.reason_codes for reason in reasons)))


def _sum_rows(
    rows: tuple[ResearchSourceResolutionAuthorityGapRow, ...],
    field_name: str,
) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return _quantize(sum((getattr(row, field_name) for row in rows), ZERO))


def _average(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return _quantize(sum(values, ZERO) / Decimal(len(values)))


def _age_seconds(generated_at: datetime, observed_at: datetime) -> Decimal:
    generated_at_utc = _as_utc("generated_at", generated_at)
    observed_at_utc = _as_utc("evidence_observed_at", observed_at)
    delta = generated_at_utc - observed_at_utc
    with localcontext(DECIMAL_CONTEXT):
        seconds = (
            Decimal(delta.days) * SECONDS_PER_DAY
            + Decimal(delta.seconds)
            + (Decimal(delta.microseconds) / MICROSECONDS_PER_SECOND)
        )
        if seconds < ZERO:
            raise ValueError("evidence_observed_at must not be in the future")
        return _quantize(seconds)


def _validate_config(config: ResearchSourceResolutionAuthorityGapConfig) -> None:
    if config.block_authority_coverage_ratio >= config.min_authority_coverage_ratio:
        raise ValueError(
            "block_authority_coverage_ratio must be below min_authority_coverage_ratio",
        )
    if config.freshness_watch_age_seconds >= config.freshness_block_age_seconds:
        raise ValueError(
            "freshness_watch_age_seconds must be below freshness_block_age_seconds",
        )
    if config.block_independence_score >= config.min_independence_score:
        raise ValueError("block_independence_score must be below min_independence_score")
    if config.contradiction_watch_severity >= config.contradiction_block_severity:
        raise ValueError(
            "contradiction_watch_severity must be below contradiction_block_severity",
        )
    if config.block_rule_mapping_score >= config.min_rule_mapping_score:
        raise ValueError("block_rule_mapping_score must be below min_rule_mapping_score")


def _validate_public_config_snapshot(
    config: ResearchSourceResolutionAuthorityGapConfig,
) -> None:
    _require_exact_type("config", config, ResearchSourceResolutionAuthorityGapConfig)
    _require_canonical_string("config_version", config.config_version)
    if (
        config.config_version
        != DEFAULT_RESEARCH_SOURCE_RESOLUTION_AUTHORITY_GAP_REPORT_CONFIG_VERSION
    ):
        raise ValueError("config_version must be the supported config version")
    for field_name in (
        "min_authority_coverage_ratio",
        "block_authority_coverage_ratio",
        "min_independence_score",
        "block_independence_score",
        "contradiction_watch_severity",
        "contradiction_block_severity",
        "min_rule_mapping_score",
        "block_rule_mapping_score",
    ):
        _require_ratio(field_name, getattr(config, field_name))
    for field_name in (
        "freshness_watch_age_seconds",
        "freshness_block_age_seconds",
    ):
        _require_positive_decimal(field_name, getattr(config, field_name))
    _validate_config(config)
    require_paper_only_flags("config", config)


def _validate_row(row: ResearchSourceResolutionAuthorityGapRow) -> None:
    if row.evidence_count <= ZERO:
        raise ValueError("evidence_count must be positive")
    if row.source_family_count <= ZERO:
        raise ValueError("source_family_count must be positive")
    if row.source_family_count > row.evidence_count:
        raise ValueError("source_family_count must not exceed evidence_count")
    if row.latest_evidence_age_seconds > row.average_evidence_age_seconds:
        raise ValueError("latest_evidence_age_seconds must not exceed average")
    if row.status != _row_status(row.reason_codes):
        raise ValueError("status must match reason_codes")
    if row.status == "pass" and row.reason_codes != (CLEAR_REASON,):
        raise ValueError("pass rows must be clear")


def _validate_derived_row(
    row: ResearchSourceResolutionAuthorityGapRow,
    *,
    config: ResearchSourceResolutionAuthorityGapConfig,
) -> None:
    expected_reason_codes = _row_reason_codes(
        latest_evidence_age_seconds=row.latest_evidence_age_seconds,
        average_authority_coverage_ratio=row.average_authority_coverage_ratio,
        average_independence_score=row.average_independence_score,
        contradiction_severity=row.contradiction_severity,
        average_rule_mapping_score=row.average_rule_mapping_score,
        config=config,
    )
    if row.reason_codes != expected_reason_codes:
        raise ValueError("reason_codes must match row metrics and config")
    expected_score = _authority_gap_score(
        latest_evidence_age_seconds=row.latest_evidence_age_seconds,
        average_authority_coverage_ratio=row.average_authority_coverage_ratio,
        average_independence_score=row.average_independence_score,
        contradiction_severity=row.contradiction_severity,
        average_rule_mapping_score=row.average_rule_mapping_score,
        reason_codes=expected_reason_codes,
        config=config,
    )
    if row.authority_gap_score != expected_score:
        raise ValueError("authority_gap_score must match row metrics and config")


def _derived_report_values(
    rows: tuple[ResearchSourceResolutionAuthorityGapRow, ...],
) -> dict[str, object]:
    return {
        "criteria_group_count": _count(len(rows)),
        "evidence_count": _sum_rows(rows, "evidence_count"),
        "pass_criteria_group_count": _status_count(rows, "pass"),
        "watch_criteria_group_count": _status_count(rows, "watch"),
        "block_criteria_group_count": _status_count(rows, "block"),
        "low_authority_coverage_count": _reason_count(
            rows,
            (
                LOW_AUTHORITY_COVERAGE_WATCH_REASON,
                LOW_AUTHORITY_COVERAGE_BLOCK_REASON,
            ),
        ),
        "stale_evidence_count": _reason_count(
            rows,
            (STALE_EVIDENCE_WATCH_REASON, STALE_EVIDENCE_BLOCK_REASON),
        ),
        "low_independence_count": _reason_count(
            rows,
            (LOW_INDEPENDENCE_WATCH_REASON, LOW_INDEPENDENCE_BLOCK_REASON),
        ),
        "contradiction_severity_count": _reason_count(
            rows,
            (
                CONTRADICTION_SEVERITY_WATCH_REASON,
                CONTRADICTION_SEVERITY_BLOCK_REASON,
            ),
        ),
        "weak_rule_mapping_count": _reason_count(
            rows,
            (WEAK_RULE_MAPPING_WATCH_REASON, WEAK_RULE_MAPPING_BLOCK_REASON),
        ),
        "highest_authority_gap_score": max(
            (row.authority_gap_score for row in rows),
            default=ZERO,
        ),
        "oldest_latest_evidence_age_seconds": max(
            (row.latest_evidence_age_seconds for row in rows),
            default=ZERO,
        ),
        "status": _report_status(rows),
        "reason_codes": _report_reason_codes(rows),
    }


def _validate_report(
    report: ResearchSourceResolutionAuthorityGapReport,
    *,
    config: ResearchSourceResolutionAuthorityGapConfig,
) -> None:
    for row in report.rows:
        _validate_derived_row(row, config=config)
    for field_name, expected_value in _derived_report_values(report.rows).items():
        if getattr(report, field_name) != expected_value:
            raise ValueError(f"{field_name} must match rows")
    if report.rows != tuple(sorted(report.rows, key=_row_sort_key)):
        raise ValueError("rows must use deterministic authority gap sort")


def _normalize_rows(
    value: object,
) -> tuple[ResearchSourceResolutionAuthorityGapRow, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("rows must be a list or tuple")
    rows = tuple(value)
    seen: set[str] = set()
    for row in rows:
        if type(row) is not ResearchSourceResolutionAuthorityGapRow:
            raise ValueError("rows must contain ResearchSourceResolutionAuthorityGapRow")
        require_paper_only_flags("authority gap row", row)
        if row.criteria_group in seen:
            raise ValueError("rows must be unique by criteria_group")
        seen.add(row.criteria_group)
    return tuple(sorted(rows, key=_row_sort_key))


def _count(value: int) -> Decimal:
    if value < 0:
        raise ValueError("count must be nonnegative")
    return _quantize(Decimal(value))


def _quantize(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(QUANT)


def _require_exact_type(label: str, value: object, expected_type: type[object]) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{label} must be exactly {expected_type.__name__}")


def _require_positive_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_nonnegative_decimal(field_name, value)
    if decimal_value <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return decimal_value


def _require_nonnegative_whole_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_nonnegative_decimal(field_name, value)
    with localcontext(DECIMAL_CONTEXT):
        if decimal_value != decimal_value.to_integral_value():
            raise ValueError(f"{field_name} must be a whole Decimal")
    return decimal_value


def _require_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    if value.is_zero() and value.is_signed():
        raise ValueError(f"{field_name} must not be signed zero")
    if value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    try:
        decimal_value = _quantize(value)
    except DecimalException as exc:
        raise ValueError(f"{field_name} must use six decimal places") from exc
    if decimal_value != value:
        raise ValueError(f"{field_name} must use six decimal places")
    if decimal_value == ZERO:
        return ZERO
    return decimal_value


def _require_ratio(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    if value > ONE:
        raise ValueError(f"{field_name} must be between zero and one")
    decimal_value = _require_nonnegative_decimal(field_name, value)
    return decimal_value


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _normalize_reason_codes(
    field_name: str,
    value: object,
    allowed: tuple[str, ...],
) -> tuple[str, ...]:
    if type(value) not in (list, tuple):
        raise ValueError(f"{field_name} must be a list or tuple")
    reason_codes = tuple(value)
    if not reason_codes:
        raise ValueError(f"{field_name} must not be empty")
    for reason in reason_codes:
        if type(reason) is not str or reason not in allowed:
            raise ValueError(f"{field_name} must contain known reason codes")
    if len(set(reason_codes)) != len(reason_codes):
        raise ValueError(f"{field_name} must be unique")
    if tuple(reason for reason in allowed if reason in reason_codes) != reason_codes:
        raise ValueError(f"{field_name} must be deterministic")
    return reason_codes


def _require_status(field_name: str, value: object) -> None:
    if (
        type(value) is not str
        or value not in RESEARCH_SOURCE_RESOLUTION_AUTHORITY_GAP_REPORT_STATUSES
    ):
        raise ValueError(f"{field_name} must be pass, watch, or block")


def _require_public_label(field_name: str, value: object) -> str:
    _require_canonical_string(field_name, value)
    lowered = value.lower()
    unsafe_fragments = (
        "http://",
        "https://",
        "postgres://",
        "mysql://",
        "jdbc:",
        "candidate",
        "credential",
        "dsn",
        "identifier",
        "market",
        "private",
        "question",
        "secret",
        "slug",
        "table",
        "token",
        "trade",
        "url",
        "wallet",
    )
    if any(fragment in lowered for fragment in unsafe_fragments):
        raise ValueError(f"{field_name} contains unsafe text")
    if (
        not value.isascii()
        or value != lowered
        or value.startswith(".")
        or value.endswith(".")
        or ".." in value
        or not all(char.isalnum() or char in (".", "_", "-") for char in value)
    ):
        raise ValueError(f"{field_name} must be a public identifier")
    return value


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value:
        raise ValueError(f"{field_name} must not be empty")
    if value.strip() != value:
        raise ValueError(f"{field_name} must be stripped")
    if "\n" in value or "\r" in value or "\t" in value:
        raise ValueError(f"{field_name} must be single line")


def _require_sha256(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if len(value) != SHA256_HEX_LENGTH:
        raise ValueError(f"{field_name} must be a SHA-256 digest")
    if any(char not in "0123456789abcdef" for char in value):
        raise ValueError(f"{field_name} must be lowercase hex")


def _report_digest_from_public_payload(
    report: ResearchSourceResolutionAuthorityGapReport,
) -> str:
    _validate_public_report_snapshot(report)
    payload = json_ready_no_floats(report)
    if type(payload) is not dict:
        raise ValueError("payload must be a dict")
    _reject_unsafe_public_surface("payload", payload)
    return _payload_validation_digest(payload)


def _payload_validation_digest(payload: Mapping[str, Any]) -> str:
    _validate_public_payload_schema(payload)
    canonical_payload = dict(payload)
    canonical_payload.pop("derived_validation_digest")
    encoded = json.dumps(
        canonical_payload,
        allow_nan=False,
        ensure_ascii=True,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _validate_public_payload_schema(payload: object) -> None:
    report_payload = _require_exact_payload_fields(
        "report",
        payload,
        REPORT_PUBLIC_PAYLOAD_FIELDS,
    )
    _require_public_datetime_string("generated_at", report_payload["generated_at"])
    _require_canonical_string("config_version", report_payload["config_version"])
    if (
        report_payload["config_version"]
        != DEFAULT_RESEARCH_SOURCE_RESOLUTION_AUTHORITY_GAP_REPORT_CONFIG_VERSION
    ):
        raise ValueError("config_version must be the supported config version")
    config = _validate_public_config_payload_schema(report_payload["config"])
    if report_payload["config_version"] != config.config_version:
        raise ValueError("config_version must match config")
    parsed_report_values: dict[str, object] = {}
    for field_name in REPORT_COUNT_FIELDS:
        parsed_report_values[field_name] = _require_public_decimal_string(
            field_name,
            report_payload[field_name],
            _require_nonnegative_whole_decimal,
        )
    parsed_report_values["highest_authority_gap_score"] = _require_public_decimal_string(
        "highest_authority_gap_score",
        report_payload["highest_authority_gap_score"],
        _require_ratio,
    )
    parsed_report_values["oldest_latest_evidence_age_seconds"] = (
        _require_public_decimal_string(
            "oldest_latest_evidence_age_seconds",
            report_payload["oldest_latest_evidence_age_seconds"],
            _require_nonnegative_decimal,
        )
    )
    _require_status("status", report_payload["status"])
    parsed_report_values["status"] = report_payload["status"]
    parsed_report_values["reason_codes"] = _require_public_reason_code_list(
        "reason_codes",
        report_payload["reason_codes"],
        REPORT_REASON_CODES,
    )
    row_payloads = report_payload["rows"]
    if type(row_payloads) is not list:
        raise ValueError("rows must be a list in the public payload schema")
    rows = tuple(
        _validate_public_row_payload_schema(index, row, config=config)
        for index, row in enumerate(row_payloads)
    )
    normalized_rows = _normalize_rows(rows)
    if rows != normalized_rows:
        raise ValueError("rows must use deterministic authority gap sort")
    for field_name, expected_value in _derived_report_values(rows).items():
        if parsed_report_values[field_name] != expected_value:
            raise ValueError(f"{field_name} must match rows")
    digest = report_payload["derived_validation_digest"]
    if digest != "":
        _require_sha256("derived_validation_digest", digest)
    _require_public_payload_flags(report_payload)


def _validate_public_config_payload_schema(
    payload: object,
) -> ResearchSourceResolutionAuthorityGapConfig:
    config_payload = _require_exact_payload_fields(
        "config",
        payload,
        CONFIG_PUBLIC_PAYLOAD_FIELDS,
    )
    _require_canonical_string("config_version", config_payload["config_version"])
    if (
        config_payload["config_version"]
        != DEFAULT_RESEARCH_SOURCE_RESOLUTION_AUTHORITY_GAP_REPORT_CONFIG_VERSION
    ):
        raise ValueError("config_version must be the supported config version")
    parsed_values = {
        field_name: _require_public_decimal_string(
            field_name,
            config_payload[field_name],
            _require_ratio,
        )
        for field_name in (
            "min_authority_coverage_ratio",
            "block_authority_coverage_ratio",
            "min_independence_score",
            "block_independence_score",
            "contradiction_watch_severity",
            "contradiction_block_severity",
            "min_rule_mapping_score",
            "block_rule_mapping_score",
        )
    }
    for field_name in (
        "freshness_watch_age_seconds",
        "freshness_block_age_seconds",
    ):
        parsed_values[field_name] = _require_public_decimal_string(
            field_name,
            config_payload[field_name],
            _require_positive_decimal,
        )
    _require_public_payload_flags(config_payload)
    return ResearchSourceResolutionAuthorityGapConfig(
        config_version=config_payload["config_version"],
        paper_only=config_payload["paper_only"],
        report_only=config_payload["report_only"],
        readonly=config_payload["readonly"],
        **parsed_values,
    )


def _validate_public_row_payload_schema(
    index: int,
    payload: object,
    *,
    config: ResearchSourceResolutionAuthorityGapConfig,
) -> ResearchSourceResolutionAuthorityGapRow:
    row_payload = _require_exact_payload_fields(
        f"rows[{index}]",
        payload,
        ROW_PUBLIC_PAYLOAD_FIELDS,
    )
    _require_public_label("criteria_group", row_payload["criteria_group"])
    parsed_counts = {
        field_name: _require_public_decimal_string(
            field_name,
            row_payload[field_name],
            _require_nonnegative_whole_decimal,
        )
        for field_name in ROW_COUNT_FIELDS
    }
    if parsed_counts["evidence_count"] <= ZERO:
        raise ValueError("evidence_count must be positive")
    if parsed_counts["source_family_count"] <= ZERO:
        raise ValueError("source_family_count must be positive")
    if parsed_counts["source_family_count"] > parsed_counts["evidence_count"]:
        raise ValueError("source_family_count must not exceed evidence_count")
    latest_age = _require_public_decimal_string(
        "latest_evidence_age_seconds",
        row_payload["latest_evidence_age_seconds"],
        _require_nonnegative_decimal,
    )
    average_age = _require_public_decimal_string(
        "average_evidence_age_seconds",
        row_payload["average_evidence_age_seconds"],
        _require_nonnegative_decimal,
    )
    if latest_age > average_age:
        raise ValueError("latest_evidence_age_seconds must not exceed average")
    parsed_ratios = {
        field_name: _require_public_decimal_string(
            field_name,
            row_payload[field_name],
            _require_ratio,
        )
        for field_name in ROW_RATIO_FIELDS
    }
    _require_status("status", row_payload["status"])
    reason_codes = _require_public_reason_code_list(
        "reason_codes",
        row_payload["reason_codes"],
        ROW_REASON_CODES,
    )
    if row_payload["status"] != _row_status(reason_codes):
        raise ValueError("status must match reason_codes")
    _require_public_payload_flags(row_payload)
    row = ResearchSourceResolutionAuthorityGapRow(
        criteria_group=row_payload["criteria_group"],
        evidence_count=parsed_counts["evidence_count"],
        source_family_count=parsed_counts["source_family_count"],
        latest_evidence_age_seconds=latest_age,
        average_evidence_age_seconds=average_age,
        average_authority_coverage_ratio=parsed_ratios[
            "average_authority_coverage_ratio"
        ],
        average_independence_score=parsed_ratios["average_independence_score"],
        contradiction_severity=parsed_ratios["contradiction_severity"],
        average_rule_mapping_score=parsed_ratios["average_rule_mapping_score"],
        authority_gap_score=parsed_ratios["authority_gap_score"],
        status=row_payload["status"],
        reason_codes=reason_codes,
        paper_only=row_payload["paper_only"],
        report_only=row_payload["report_only"],
        readonly=row_payload["readonly"],
    )
    _validate_derived_row(row, config=config)
    return row


def _require_exact_payload_fields(
    label: str,
    payload: object,
    expected_fields: tuple[str, ...],
) -> dict[str, Any]:
    if not isinstance(payload, Mapping):
        raise ValueError(f"{label} must be a dict in the public payload schema")
    if any(type(key) is not str for key in payload):
        raise ValueError(f"{label} does not match the public payload schema")
    payload_dict = dict(payload)
    if set(payload_dict) != set(expected_fields):
        raise ValueError(f"{label} does not match the public payload schema")
    if tuple(payload) != expected_fields:
        raise ValueError(f"{label} must use canonical field order")
    return payload_dict


def _require_public_datetime_string(field_name: str, value: object) -> datetime:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string in the public payload schema")
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError as exc:
        raise ValueError(f"{field_name} must be an ISO-8601 datetime") from exc
    normalized = _as_utc(field_name, parsed)
    if value != normalized.isoformat():
        raise ValueError(f"{field_name} must be a canonical UTC datetime")
    return normalized


def _require_public_decimal_string(
    field_name: str,
    value: object,
    validator: Any,
) -> Decimal:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a Decimal string")
    try:
        decimal_value = Decimal(value)
    except DecimalException as exc:
        raise ValueError(f"{field_name} must be a Decimal string") from exc
    validated = validator(field_name, decimal_value)
    if str(validated) != value:
        raise ValueError(f"{field_name} must be a canonical Decimal string")
    return validated


def _require_public_reason_code_list(
    field_name: str,
    value: object,
    allowed: tuple[str, ...],
) -> tuple[str, ...]:
    if type(value) is not list:
        raise ValueError(f"{field_name} must be a list in the public payload schema")
    return _normalize_reason_codes(field_name, value, allowed)


def _require_public_payload_flags(payload: dict[str, Any]) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if type(payload[field_name]) is not bool or payload[field_name] is not True:
            raise ValueError(f"{field_name} must be true in the public payload schema")


def _reject_unsafe_public_surface(label: str, value: object) -> None:
    if is_dataclass(value) and not isinstance(value, type):
        _reject_unsafe_public_surface(label, asdict(value))
        return
    if isinstance(value, dict):
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("public payload keys must be strings")
            _reject_unsafe_public_key(label, key)
            _reject_unsafe_public_surface(label, item)
        return
    if isinstance(value, (list, tuple)):
        for item in value:
            _reject_unsafe_public_surface(label, item)
        return
    if type(value) is str:
        _reject_unsafe_public_string(label, value)


def _reject_unsafe_public_key(label: str, key: str) -> None:
    lowered = key.lower()
    unsafe_fragments = (
        "raw_candidate",
        "candidate_id",
        "candidate_slug",
        "market_id",
        "market_slug",
        "market_question",
        "source_id",
        "source_url",
        "source_text",
        "dsn",
        "table_name",
        "token",
        "wallet",
        "order",
        "trade",
    )
    if any(fragment in lowered for fragment in unsafe_fragments):
        raise ValueError(f"{label} contains unsafe public field")


def _reject_unsafe_public_string(label: str, value: str) -> None:
    lowered = value.lower()
    unsafe_fragments = (
        "http://",
        "https://",
        "postgres://",
        "mysql://",
        "jdbc:",
        "candidate-",
        "market-",
        "question",
        "slug",
        "token",
        "wallet",
        "order",
        "trade",
    )
    if any(fragment in lowered for fragment in unsafe_fragments):
        raise ValueError(f"{label} contains unsafe public text")


__all__ = (
    "DEFAULT_RESEARCH_SOURCE_RESOLUTION_AUTHORITY_GAP_REPORT_CONFIG_VERSION",
    "RESEARCH_SOURCE_RESOLUTION_AUTHORITY_GAP_REPORT_STATUSES",
    "ResearchSourceResolutionAuthorityGapConfig",
    "ResearchSourceResolutionAuthorityGapInput",
    "ResearchSourceResolutionAuthorityGapReport",
    "ResearchSourceResolutionAuthorityGapRow",
    "build_research_source_resolution_authority_gap_report",
    "research_source_resolution_authority_gap_report_digest",
    "research_source_resolution_authority_gap_report_payload",
    "validate_research_source_resolution_authority_gap_report_digest",
)
