"""Pure in-memory source resolution claim trace gap report."""

from __future__ import annotations

from dataclasses import asdict, dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
import hashlib
import json
from typing import Any

from polymarket_alpha_lab.team_paper_guard import (
    json_ready_no_floats,
    require_paper_only_flags,
)


DEFAULT_RESEARCH_SOURCE_RESOLUTION_CLAIM_TRACE_GAP_REPORT_CONFIG_VERSION = (
    "research-source-resolution-claim-trace-gap-report-v0"
)
RESEARCH_SOURCE_RESOLUTION_CLAIM_TRACE_GAP_REPORT_STATUSES = (
    "pass",
    "watch",
    "block",
)

EMPTY_REASON = "research_source_resolution_claim_trace_gap_empty"
CLEAR_REASON = "resolution_claim_trace_gap_clear"
CLAIM_TRACE_COVERAGE_WATCH_REASON = "claim_trace_coverage_watch"
CLAIM_TRACE_COVERAGE_BLOCK_REASON = "claim_trace_coverage_block"
RESOLUTION_CLAUSE_COVERAGE_WATCH_REASON = "resolution_clause_coverage_watch"
RESOLUTION_CLAUSE_COVERAGE_BLOCK_REASON = "resolution_clause_coverage_block"
STALE_CLAIM_TRACE_WATCH_REASON = "stale_claim_trace_watch"
STALE_CLAIM_TRACE_BLOCK_REASON = "stale_claim_trace_block"
LOW_SOURCE_AUTHORITY_WATCH_REASON = "low_source_authority_watch"
LOW_SOURCE_AUTHORITY_BLOCK_REASON = "low_source_authority_block"
CONTRADICTION_PRESSURE_WATCH_REASON = "contradiction_pressure_watch"
CONTRADICTION_PRESSURE_BLOCK_REASON = "contradiction_pressure_block"
LOW_INDEPENDENT_SOURCE_WATCH_REASON = "low_independent_source_watch"
LOW_INDEPENDENT_SOURCE_BLOCK_REASON = "low_independent_source_block"
MISSING_TRACE_LINK_WATCH_REASON = "missing_trace_link_watch"
MISSING_TRACE_LINK_BLOCK_REASON = "missing_trace_link_block"
DEADLINE_PROXIMITY_WATCH_REASON = "deadline_proximity_watch"
DEADLINE_PROXIMITY_BLOCK_REASON = "deadline_proximity_block"

ROW_REASON_CODES = (
    CLEAR_REASON,
    CLAIM_TRACE_COVERAGE_BLOCK_REASON,
    RESOLUTION_CLAUSE_COVERAGE_BLOCK_REASON,
    STALE_CLAIM_TRACE_BLOCK_REASON,
    LOW_SOURCE_AUTHORITY_BLOCK_REASON,
    CONTRADICTION_PRESSURE_BLOCK_REASON,
    LOW_INDEPENDENT_SOURCE_BLOCK_REASON,
    MISSING_TRACE_LINK_BLOCK_REASON,
    DEADLINE_PROXIMITY_BLOCK_REASON,
    CLAIM_TRACE_COVERAGE_WATCH_REASON,
    RESOLUTION_CLAUSE_COVERAGE_WATCH_REASON,
    STALE_CLAIM_TRACE_WATCH_REASON,
    LOW_SOURCE_AUTHORITY_WATCH_REASON,
    CONTRADICTION_PRESSURE_WATCH_REASON,
    LOW_INDEPENDENT_SOURCE_WATCH_REASON,
    MISSING_TRACE_LINK_WATCH_REASON,
    DEADLINE_PROXIMITY_WATCH_REASON,
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

ROW_PUBLIC_FIELDS = (
    "claim_trace_key",
    "resolution_scope",
    "evidence_count",
    "evidence_family_count",
    "latest_trace_age_seconds",
    "average_trace_age_seconds",
    "average_claim_trace_coverage",
    "average_resolution_clause_coverage",
    "average_source_authority_score",
    "contradiction_pressure",
    "independent_source_count",
    "missing_trace_link_count",
    "deadline_proximity_seconds",
    "claim_trace_gap_score",
    "status",
    "reason_codes",
    "paper_only",
    "report_only",
    "readonly",
)
REPORT_PUBLIC_FIELDS = (
    "generated_at",
    "config_version",
    "claim_trace_count",
    "evidence_count",
    "pass_claim_trace_count",
    "watch_claim_trace_count",
    "block_claim_trace_count",
    "low_claim_trace_coverage_count",
    "low_resolution_clause_coverage_count",
    "stale_trace_count",
    "low_source_authority_count",
    "contradiction_pressure_count",
    "low_independent_source_count",
    "missing_trace_link_count",
    "deadline_pressure_count",
    "highest_claim_trace_gap_score",
    "nearest_deadline_seconds",
    "status",
    "reason_codes",
    "rows",
    "derived_validation_digest",
    "paper_only",
    "report_only",
    "readonly",
)


@dataclass(frozen=True)
class ResearchSourceResolutionClaimTraceGapConfig:
    config_version: str = (
        DEFAULT_RESEARCH_SOURCE_RESOLUTION_CLAIM_TRACE_GAP_REPORT_CONFIG_VERSION
    )
    min_claim_trace_coverage: Decimal = Decimal("0.800000")
    block_claim_trace_coverage: Decimal = Decimal("0.500000")
    min_resolution_clause_coverage: Decimal = Decimal("0.800000")
    block_resolution_clause_coverage: Decimal = Decimal("0.500000")
    trace_watch_age_seconds: Decimal = Decimal("3600.000000")
    trace_block_age_seconds: Decimal = Decimal("7200.000000")
    min_source_authority_score: Decimal = Decimal("0.800000")
    block_source_authority_score: Decimal = Decimal("0.500000")
    contradiction_watch_pressure: Decimal = Decimal("0.300000")
    contradiction_block_pressure: Decimal = Decimal("0.600000")
    min_independent_source_count: Decimal = Decimal("2.000000")
    block_independent_source_count: Decimal = Decimal("1.000000")
    missing_trace_link_watch_count: Decimal = Decimal("1.000000")
    missing_trace_link_block_count: Decimal = Decimal("2.000000")
    deadline_watch_proximity_seconds: Decimal = Decimal("43200.000000")
    deadline_block_proximity_seconds: Decimal = Decimal("7200.000000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchSourceResolutionClaimTraceGapConfig does not support subclassing",
        )

    def __post_init__(self) -> None:
        _require_exact_type("config", self, ResearchSourceResolutionClaimTraceGapConfig)
        _require_canonical_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_SOURCE_RESOLUTION_CLAIM_TRACE_GAP_REPORT_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "min_claim_trace_coverage",
            "block_claim_trace_coverage",
            "min_resolution_clause_coverage",
            "block_resolution_clause_coverage",
            "min_source_authority_score",
            "block_source_authority_score",
            "contradiction_watch_pressure",
            "contradiction_block_pressure",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "trace_watch_age_seconds",
            "trace_block_age_seconds",
            "min_independent_source_count",
            "block_independent_source_count",
            "deadline_watch_proximity_seconds",
            "deadline_block_proximity_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_positive_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "missing_trace_link_watch_count",
            "missing_trace_link_block_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        _validate_config(self)
        require_paper_only_flags("config", self)
        _reject_unsafe_public_surface("config", self)


@dataclass(frozen=True)
class ResearchSourceResolutionClaimTraceGapInput:
    claim_trace_key: str
    resolution_scope: str
    evidence_family: str
    observed_at: datetime
    resolution_deadline_at: datetime
    claim_trace_coverage: Decimal
    resolution_clause_coverage: Decimal
    source_authority_score: Decimal
    contradiction_pressure: Decimal
    independent_source_count: Decimal
    missing_trace_link_count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchSourceResolutionClaimTraceGapInput does not support subclassing",
        )

    def __post_init__(self) -> None:
        _require_exact_type("input", self, ResearchSourceResolutionClaimTraceGapInput)
        for field_name in ("claim_trace_key", "resolution_scope", "evidence_family"):
            object.__setattr__(
                self,
                field_name,
                _require_public_label(field_name, getattr(self, field_name)),
            )
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        object.__setattr__(
            self,
            "resolution_deadline_at",
            _as_utc("resolution_deadline_at", self.resolution_deadline_at),
        )
        for field_name in (
            "claim_trace_coverage",
            "resolution_clause_coverage",
            "source_authority_score",
            "contradiction_pressure",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "independent_source_count",
            "missing_trace_link_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        require_paper_only_flags("input", self)
        _reject_unsafe_public_surface("input", self)


@dataclass(frozen=True)
class ResearchSourceResolutionClaimTraceGapRow:
    claim_trace_key: str
    resolution_scope: str
    evidence_count: Decimal
    evidence_family_count: Decimal
    latest_trace_age_seconds: Decimal
    average_trace_age_seconds: Decimal
    average_claim_trace_coverage: Decimal
    average_resolution_clause_coverage: Decimal
    average_source_authority_score: Decimal
    contradiction_pressure: Decimal
    independent_source_count: Decimal
    missing_trace_link_count: Decimal
    deadline_proximity_seconds: Decimal
    claim_trace_gap_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchSourceResolutionClaimTraceGapRow does not support subclassing",
        )

    def __post_init__(self) -> None:
        _require_exact_type("row", self, ResearchSourceResolutionClaimTraceGapRow)
        for field_name in ("claim_trace_key", "resolution_scope"):
            object.__setattr__(
                self,
                field_name,
                _require_public_label(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "evidence_count",
            "evidence_family_count",
            "latest_trace_age_seconds",
            "average_trace_age_seconds",
            "independent_source_count",
            "missing_trace_link_count",
            "deadline_proximity_seconds",
            "claim_trace_gap_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "average_claim_trace_coverage",
            "average_resolution_clause_coverage",
            "average_source_authority_score",
            "contradiction_pressure",
        ):
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
        require_paper_only_flags("claim trace gap row", self)
        _reject_unsafe_public_surface("row", self)


@dataclass(frozen=True)
class ResearchSourceResolutionClaimTraceGapReport:
    generated_at: datetime
    config_version: str
    claim_trace_count: Decimal
    evidence_count: Decimal
    pass_claim_trace_count: Decimal
    watch_claim_trace_count: Decimal
    block_claim_trace_count: Decimal
    low_claim_trace_coverage_count: Decimal
    low_resolution_clause_coverage_count: Decimal
    stale_trace_count: Decimal
    low_source_authority_count: Decimal
    contradiction_pressure_count: Decimal
    low_independent_source_count: Decimal
    missing_trace_link_count: Decimal
    deadline_pressure_count: Decimal
    highest_claim_trace_gap_score: Decimal
    nearest_deadline_seconds: Decimal
    status: str
    reason_codes: tuple[str, ...]
    rows: tuple[ResearchSourceResolutionClaimTraceGapRow, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchSourceResolutionClaimTraceGapReport does not support subclassing",
        )

    def __post_init__(self) -> None:
        _require_exact_type("report", self, ResearchSourceResolutionClaimTraceGapReport)
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_SOURCE_RESOLUTION_CLAIM_TRACE_GAP_REPORT_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "claim_trace_count",
            "evidence_count",
            "pass_claim_trace_count",
            "watch_claim_trace_count",
            "block_claim_trace_count",
            "low_claim_trace_coverage_count",
            "low_resolution_clause_coverage_count",
            "stale_trace_count",
            "low_source_authority_count",
            "contradiction_pressure_count",
            "low_independent_source_count",
            "missing_trace_link_count",
            "deadline_pressure_count",
            "highest_claim_trace_gap_score",
            "nearest_deadline_seconds",
        ):
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
        _validate_report(self)
        require_paper_only_flags("claim trace gap report", self)
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


def build_research_source_resolution_claim_trace_gap_report(
    inputs: list[ResearchSourceResolutionClaimTraceGapInput]
    | tuple[ResearchSourceResolutionClaimTraceGapInput, ...],
    *,
    config: ResearchSourceResolutionClaimTraceGapConfig,
    generated_at: datetime,
) -> ResearchSourceResolutionClaimTraceGapReport:
    """Build a deterministic report-only source-resolution claim trace gap snapshot."""

    if type(config) is not ResearchSourceResolutionClaimTraceGapConfig:
        raise ValueError("config must be a ResearchSourceResolutionClaimTraceGapConfig")
    config = _revalidate_config(config)
    require_paper_only_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    rows = _claim_trace_gap_rows(
        _normalize_inputs(inputs, generated_at=generated_at_utc),
        config=config,
        generated_at=generated_at_utc,
    )
    return ResearchSourceResolutionClaimTraceGapReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        claim_trace_count=_count(len(rows)),
        evidence_count=_sum_rows(rows, "evidence_count"),
        pass_claim_trace_count=_status_count(rows, "pass"),
        watch_claim_trace_count=_status_count(rows, "watch"),
        block_claim_trace_count=_status_count(rows, "block"),
        low_claim_trace_coverage_count=_reason_count(
            rows,
            (CLAIM_TRACE_COVERAGE_WATCH_REASON, CLAIM_TRACE_COVERAGE_BLOCK_REASON),
        ),
        low_resolution_clause_coverage_count=_reason_count(
            rows,
            (
                RESOLUTION_CLAUSE_COVERAGE_WATCH_REASON,
                RESOLUTION_CLAUSE_COVERAGE_BLOCK_REASON,
            ),
        ),
        stale_trace_count=_reason_count(
            rows,
            (STALE_CLAIM_TRACE_WATCH_REASON, STALE_CLAIM_TRACE_BLOCK_REASON),
        ),
        low_source_authority_count=_reason_count(
            rows,
            (LOW_SOURCE_AUTHORITY_WATCH_REASON, LOW_SOURCE_AUTHORITY_BLOCK_REASON),
        ),
        contradiction_pressure_count=_reason_count(
            rows,
            (CONTRADICTION_PRESSURE_WATCH_REASON, CONTRADICTION_PRESSURE_BLOCK_REASON),
        ),
        low_independent_source_count=_reason_count(
            rows,
            (
                LOW_INDEPENDENT_SOURCE_WATCH_REASON,
                LOW_INDEPENDENT_SOURCE_BLOCK_REASON,
            ),
        ),
        missing_trace_link_count=_reason_count(
            rows,
            (MISSING_TRACE_LINK_WATCH_REASON, MISSING_TRACE_LINK_BLOCK_REASON),
        ),
        deadline_pressure_count=_reason_count(
            rows,
            (DEADLINE_PROXIMITY_WATCH_REASON, DEADLINE_PROXIMITY_BLOCK_REASON),
        ),
        highest_claim_trace_gap_score=_quantize(
            max(
                (row.claim_trace_gap_score for row in rows),
                default=ZERO,
            ),
        ),
        nearest_deadline_seconds=_quantize(
            min(
                (row.deadline_proximity_seconds for row in rows),
                default=ZERO,
            ),
        ),
        status=_report_status(rows),
        reason_codes=_report_reason_codes(rows),
        rows=rows,
    )


def research_source_resolution_claim_trace_gap_report_payload(
    report: ResearchSourceResolutionClaimTraceGapReport | dict[str, Any],
) -> dict[str, Any]:
    if type(report) is ResearchSourceResolutionClaimTraceGapReport:
        validate_research_source_resolution_claim_trace_gap_report_digest(report)
        require_paper_only_flags("report", report)
        _reject_unsafe_public_surface("report", report)
        payload = json_ready_no_floats(report)
    elif type(report) is dict:
        payload = report
        validate_research_source_resolution_claim_trace_gap_report_digest(payload)
    else:
        raise ValueError(
            "report must be a ResearchSourceResolutionClaimTraceGapReport or plain dict",
        )
    if type(payload) is not dict:
        raise ValueError("payload must be a dict")
    _reject_unsafe_public_surface("payload", payload)
    return payload


def research_source_resolution_claim_trace_gap_report_digest(
    report: ResearchSourceResolutionClaimTraceGapReport | dict[str, Any],
) -> str:
    if type(report) is ResearchSourceResolutionClaimTraceGapReport:
        return _report_digest_from_public_payload(report)
    if type(report) is dict:
        validate_research_source_resolution_claim_trace_gap_report_digest(report)
        digest = report["derived_validation_digest"]
        if type(digest) is not str:
            raise ValueError("derived_validation_digest must be a string")
        return digest
    raise ValueError(
        "report must be a ResearchSourceResolutionClaimTraceGapReport or plain dict",
    )


def validate_research_source_resolution_claim_trace_gap_report_digest(
    report: ResearchSourceResolutionClaimTraceGapReport | dict[str, Any],
) -> None:
    if type(report) is ResearchSourceResolutionClaimTraceGapReport:
        _require_sha256("derived_validation_digest", report.derived_validation_digest)
        if report.derived_validation_digest != _report_digest_from_public_payload(report):
            raise ValueError("derived_validation_digest must match report payload")
        return
    if type(report) is dict:
        _validate_public_payload(report)
        return
    raise ValueError(
        "report must be a ResearchSourceResolutionClaimTraceGapReport or plain dict",
    )


def _revalidate_config(
    config: ResearchSourceResolutionClaimTraceGapConfig,
) -> ResearchSourceResolutionClaimTraceGapConfig:
    return ResearchSourceResolutionClaimTraceGapConfig(
        **{field.name: getattr(config, field.name) for field in fields(config)},
    )


def _revalidate_input(
    row: ResearchSourceResolutionClaimTraceGapInput,
) -> ResearchSourceResolutionClaimTraceGapInput:
    return ResearchSourceResolutionClaimTraceGapInput(
        **{field.name: getattr(row, field.name) for field in fields(row)},
    )


def _revalidate_row(
    row: ResearchSourceResolutionClaimTraceGapRow,
) -> ResearchSourceResolutionClaimTraceGapRow:
    return ResearchSourceResolutionClaimTraceGapRow(
        **{field.name: getattr(row, field.name) for field in fields(row)},
    )


def _validate_public_payload(payload: dict[str, Any]) -> None:
    if type(payload) is not dict:
        raise ValueError("public payload must be a JSON object")
    _require_public_fields("public payload", payload, REPORT_PUBLIC_FIELDS)
    _require_payload_flags("public payload", payload)
    _require_canonical_public_json(payload)
    _reject_unsafe_public_surface("public payload", payload)
    digest = payload["derived_validation_digest"]
    _require_sha256("derived_validation_digest", digest)
    if digest != _payload_validation_digest(payload):
        raise ValueError("derived_validation_digest must match report payload")
    _report_from_public_payload(payload)


def _report_from_public_payload(
    payload: dict[str, Any],
) -> ResearchSourceResolutionClaimTraceGapReport:
    rows_value = payload["rows"]
    if type(rows_value) is not list:
        raise ValueError("rows must be a public list")
    rows = tuple(_row_from_public_payload(row) for row in rows_value)
    if rows != tuple(sorted(rows, key=_row_sort_key)):
        raise ValueError("rows must use deterministic claim trace gap sort")
    return ResearchSourceResolutionClaimTraceGapReport(
        generated_at=_require_public_datetime("generated_at", payload["generated_at"]),
        config_version=_require_public_string("config_version", payload["config_version"]),
        claim_trace_count=_require_public_decimal(
            "claim_trace_count",
            payload["claim_trace_count"],
        ),
        evidence_count=_require_public_decimal("evidence_count", payload["evidence_count"]),
        pass_claim_trace_count=_require_public_decimal(
            "pass_claim_trace_count",
            payload["pass_claim_trace_count"],
        ),
        watch_claim_trace_count=_require_public_decimal(
            "watch_claim_trace_count",
            payload["watch_claim_trace_count"],
        ),
        block_claim_trace_count=_require_public_decimal(
            "block_claim_trace_count",
            payload["block_claim_trace_count"],
        ),
        low_claim_trace_coverage_count=_require_public_decimal(
            "low_claim_trace_coverage_count",
            payload["low_claim_trace_coverage_count"],
        ),
        low_resolution_clause_coverage_count=_require_public_decimal(
            "low_resolution_clause_coverage_count",
            payload["low_resolution_clause_coverage_count"],
        ),
        stale_trace_count=_require_public_decimal(
            "stale_trace_count",
            payload["stale_trace_count"],
        ),
        low_source_authority_count=_require_public_decimal(
            "low_source_authority_count",
            payload["low_source_authority_count"],
        ),
        contradiction_pressure_count=_require_public_decimal(
            "contradiction_pressure_count",
            payload["contradiction_pressure_count"],
        ),
        low_independent_source_count=_require_public_decimal(
            "low_independent_source_count",
            payload["low_independent_source_count"],
        ),
        missing_trace_link_count=_require_public_decimal(
            "missing_trace_link_count",
            payload["missing_trace_link_count"],
        ),
        deadline_pressure_count=_require_public_decimal(
            "deadline_pressure_count",
            payload["deadline_pressure_count"],
        ),
        highest_claim_trace_gap_score=_require_public_decimal(
            "highest_claim_trace_gap_score",
            payload["highest_claim_trace_gap_score"],
        ),
        nearest_deadline_seconds=_require_public_decimal(
            "nearest_deadline_seconds",
            payload["nearest_deadline_seconds"],
        ),
        status=_require_public_status("status", payload["status"]),
        reason_codes=_require_public_reason_codes(
            "reason_codes",
            payload["reason_codes"],
            REPORT_REASON_CODES,
        ),
        rows=rows,
        derived_validation_digest=_require_sha256(
            "derived_validation_digest",
            payload["derived_validation_digest"],
        ),
        paper_only=_require_true_flag("paper_only", payload["paper_only"]),
        report_only=_require_true_flag("report_only", payload["report_only"]),
        readonly=_require_true_flag("readonly", payload["readonly"]),
    )


def _row_from_public_payload(value: object) -> ResearchSourceResolutionClaimTraceGapRow:
    if type(value) is not dict:
        raise ValueError("rows must contain public JSON objects")
    _require_public_fields("row", value, ROW_PUBLIC_FIELDS)
    _require_payload_flags("row", value)
    row = ResearchSourceResolutionClaimTraceGapRow(
        claim_trace_key=_require_public_label("claim_trace_key", value["claim_trace_key"]),
        resolution_scope=_require_public_label(
            "resolution_scope",
            value["resolution_scope"],
        ),
        evidence_count=_require_public_decimal("evidence_count", value["evidence_count"]),
        evidence_family_count=_require_public_decimal(
            "evidence_family_count",
            value["evidence_family_count"],
        ),
        latest_trace_age_seconds=_require_public_decimal(
            "latest_trace_age_seconds",
            value["latest_trace_age_seconds"],
        ),
        average_trace_age_seconds=_require_public_decimal(
            "average_trace_age_seconds",
            value["average_trace_age_seconds"],
        ),
        average_claim_trace_coverage=_require_public_ratio(
            "average_claim_trace_coverage",
            value["average_claim_trace_coverage"],
        ),
        average_resolution_clause_coverage=_require_public_ratio(
            "average_resolution_clause_coverage",
            value["average_resolution_clause_coverage"],
        ),
        average_source_authority_score=_require_public_ratio(
            "average_source_authority_score",
            value["average_source_authority_score"],
        ),
        contradiction_pressure=_require_public_ratio(
            "contradiction_pressure",
            value["contradiction_pressure"],
        ),
        independent_source_count=_require_public_decimal(
            "independent_source_count",
            value["independent_source_count"],
        ),
        missing_trace_link_count=_require_public_decimal(
            "missing_trace_link_count",
            value["missing_trace_link_count"],
        ),
        deadline_proximity_seconds=_require_public_decimal(
            "deadline_proximity_seconds",
            value["deadline_proximity_seconds"],
        ),
        claim_trace_gap_score=_require_public_decimal(
            "claim_trace_gap_score",
            value["claim_trace_gap_score"],
        ),
        status=_require_public_status("status", value["status"]),
        reason_codes=_require_public_reason_codes(
            "reason_codes",
            value["reason_codes"],
            ROW_REASON_CODES,
        ),
        paper_only=_require_true_flag("paper_only", value["paper_only"]),
        report_only=_require_true_flag("report_only", value["report_only"]),
        readonly=_require_true_flag("readonly", value["readonly"]),
    )
    _validate_public_row_derivations(row)
    return row


def _validate_public_row_derivations(
    row: ResearchSourceResolutionClaimTraceGapRow,
) -> None:
    config = ResearchSourceResolutionClaimTraceGapConfig()
    expected_reasons = _row_reason_codes(
        average_claim_trace_coverage=row.average_claim_trace_coverage,
        average_resolution_clause_coverage=row.average_resolution_clause_coverage,
        latest_trace_age_seconds=row.latest_trace_age_seconds,
        average_source_authority_score=row.average_source_authority_score,
        contradiction_pressure=row.contradiction_pressure,
        independent_source_count=row.independent_source_count,
        missing_trace_link_count=row.missing_trace_link_count,
        deadline_proximity_seconds=row.deadline_proximity_seconds,
        config=config,
    )
    if row.reason_codes != expected_reasons:
        raise ValueError("reason_codes must match trace gap metrics")
    expected_status = _row_status(expected_reasons)
    if row.status != expected_status:
        raise ValueError("status must match trace gap metrics")
    expected_score = _claim_trace_gap_score(
        average_claim_trace_coverage=row.average_claim_trace_coverage,
        average_resolution_clause_coverage=row.average_resolution_clause_coverage,
        latest_trace_age_seconds=row.latest_trace_age_seconds,
        average_source_authority_score=row.average_source_authority_score,
        contradiction_pressure=row.contradiction_pressure,
        independent_source_count=row.independent_source_count,
        missing_trace_link_count=row.missing_trace_link_count,
        deadline_proximity_seconds=row.deadline_proximity_seconds,
        config=config,
    )
    if row.claim_trace_gap_score != expected_score:
        raise ValueError("claim_trace_gap_score must match trace gap metrics")


def _normalize_inputs(
    value: object,
    *,
    generated_at: datetime,
) -> tuple[ResearchSourceResolutionClaimTraceGapInput, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("inputs must be a list or tuple")
    normalized_rows: list[ResearchSourceResolutionClaimTraceGapInput] = []
    for row in tuple(value):
        if type(row) is not ResearchSourceResolutionClaimTraceGapInput:
            raise ValueError("inputs must contain ResearchSourceResolutionClaimTraceGapInput")
        row = _revalidate_input(row)
        require_paper_only_flags("input", row)
        if row.observed_at > generated_at:
            raise ValueError("observed_at must not be in the future")
        normalized_rows.append(row)
    return tuple(
        sorted(
            normalized_rows,
            key=lambda row: (
                row.claim_trace_key,
                row.resolution_scope,
                row.evidence_family,
                row.observed_at,
                row.resolution_deadline_at,
            ),
        ),
    )


def _claim_trace_gap_rows(
    inputs: tuple[ResearchSourceResolutionClaimTraceGapInput, ...],
    *,
    config: ResearchSourceResolutionClaimTraceGapConfig,
    generated_at: datetime,
) -> tuple[ResearchSourceResolutionClaimTraceGapRow, ...]:
    grouped: dict[str, list[ResearchSourceResolutionClaimTraceGapInput]] = {}
    for row in inputs:
        grouped.setdefault(row.claim_trace_key, []).append(row)
    return tuple(
        sorted(
            (
                _claim_trace_gap_row(
                    trace_rows=tuple(trace_rows),
                    config=config,
                    generated_at=generated_at,
                )
                for trace_rows in grouped.values()
            ),
            key=_row_sort_key,
        ),
    )


def _claim_trace_gap_row(
    *,
    trace_rows: tuple[ResearchSourceResolutionClaimTraceGapInput, ...],
    config: ResearchSourceResolutionClaimTraceGapConfig,
    generated_at: datetime,
) -> ResearchSourceResolutionClaimTraceGapRow:
    resolution_scopes = {row.resolution_scope for row in trace_rows}
    if len(resolution_scopes) != 1:
        raise ValueError("claim_trace_key must map to one resolution_scope")
    ages = tuple(_age_seconds(generated_at, row.observed_at) for row in trace_rows)
    deadline_proximities = tuple(
        _deadline_seconds(generated_at, row.resolution_deadline_at) for row in trace_rows
    )
    evidence_count = _count(len(trace_rows))
    evidence_family_count = _count(len({row.evidence_family for row in trace_rows}))
    latest_age = _quantize(min(ages, default=ZERO))
    average_age = _average(ages)
    average_claim_trace_coverage = _average(
        tuple(row.claim_trace_coverage for row in trace_rows),
    )
    average_resolution_clause_coverage = _average(
        tuple(row.resolution_clause_coverage for row in trace_rows),
    )
    average_source_authority = _average(
        tuple(row.source_authority_score for row in trace_rows),
    )
    contradiction_pressure = _quantize(
        max(
            (row.contradiction_pressure for row in trace_rows),
            default=ZERO,
        ),
    )
    independent_source_count = min(
        (row.independent_source_count for row in trace_rows),
        default=ZERO,
    )
    independent_source_count = _quantize(independent_source_count)
    missing_trace_link_count = max(
        (row.missing_trace_link_count for row in trace_rows),
        default=ZERO,
    )
    missing_trace_link_count = _quantize(missing_trace_link_count)
    deadline_proximity_seconds = _quantize(min(deadline_proximities, default=ZERO))
    reason_codes = _row_reason_codes(
        average_claim_trace_coverage=average_claim_trace_coverage,
        average_resolution_clause_coverage=average_resolution_clause_coverage,
        latest_trace_age_seconds=latest_age,
        average_source_authority_score=average_source_authority,
        contradiction_pressure=contradiction_pressure,
        independent_source_count=independent_source_count,
        missing_trace_link_count=missing_trace_link_count,
        deadline_proximity_seconds=deadline_proximity_seconds,
        config=config,
    )
    return ResearchSourceResolutionClaimTraceGapRow(
        claim_trace_key=trace_rows[0].claim_trace_key,
        resolution_scope=trace_rows[0].resolution_scope,
        evidence_count=evidence_count,
        evidence_family_count=evidence_family_count,
        latest_trace_age_seconds=latest_age,
        average_trace_age_seconds=average_age,
        average_claim_trace_coverage=average_claim_trace_coverage,
        average_resolution_clause_coverage=average_resolution_clause_coverage,
        average_source_authority_score=average_source_authority,
        contradiction_pressure=contradiction_pressure,
        independent_source_count=independent_source_count,
        missing_trace_link_count=missing_trace_link_count,
        deadline_proximity_seconds=deadline_proximity_seconds,
        claim_trace_gap_score=_claim_trace_gap_score(
            average_claim_trace_coverage=average_claim_trace_coverage,
            average_resolution_clause_coverage=average_resolution_clause_coverage,
            latest_trace_age_seconds=latest_age,
            average_source_authority_score=average_source_authority,
            contradiction_pressure=contradiction_pressure,
            independent_source_count=independent_source_count,
            missing_trace_link_count=missing_trace_link_count,
            deadline_proximity_seconds=deadline_proximity_seconds,
            config=config,
        ),
        status=_row_status(reason_codes),
        reason_codes=reason_codes,
    )


def _row_reason_codes(
    *,
    average_claim_trace_coverage: Decimal,
    average_resolution_clause_coverage: Decimal,
    latest_trace_age_seconds: Decimal,
    average_source_authority_score: Decimal,
    contradiction_pressure: Decimal,
    independent_source_count: Decimal,
    missing_trace_link_count: Decimal,
    deadline_proximity_seconds: Decimal,
    config: ResearchSourceResolutionClaimTraceGapConfig,
) -> tuple[str, ...]:
    reasons: list[str] = []
    if average_claim_trace_coverage <= config.block_claim_trace_coverage:
        reasons.append(CLAIM_TRACE_COVERAGE_BLOCK_REASON)
    elif average_claim_trace_coverage < config.min_claim_trace_coverage:
        reasons.append(CLAIM_TRACE_COVERAGE_WATCH_REASON)
    if average_resolution_clause_coverage <= config.block_resolution_clause_coverage:
        reasons.append(RESOLUTION_CLAUSE_COVERAGE_BLOCK_REASON)
    elif average_resolution_clause_coverage < config.min_resolution_clause_coverage:
        reasons.append(RESOLUTION_CLAUSE_COVERAGE_WATCH_REASON)
    if latest_trace_age_seconds >= config.trace_block_age_seconds:
        reasons.append(STALE_CLAIM_TRACE_BLOCK_REASON)
    elif latest_trace_age_seconds > config.trace_watch_age_seconds:
        reasons.append(STALE_CLAIM_TRACE_WATCH_REASON)
    if average_source_authority_score <= config.block_source_authority_score:
        reasons.append(LOW_SOURCE_AUTHORITY_BLOCK_REASON)
    elif average_source_authority_score < config.min_source_authority_score:
        reasons.append(LOW_SOURCE_AUTHORITY_WATCH_REASON)
    if contradiction_pressure >= config.contradiction_block_pressure:
        reasons.append(CONTRADICTION_PRESSURE_BLOCK_REASON)
    elif contradiction_pressure >= config.contradiction_watch_pressure:
        reasons.append(CONTRADICTION_PRESSURE_WATCH_REASON)
    if independent_source_count <= config.block_independent_source_count:
        reasons.append(LOW_INDEPENDENT_SOURCE_BLOCK_REASON)
    elif independent_source_count < config.min_independent_source_count:
        reasons.append(LOW_INDEPENDENT_SOURCE_WATCH_REASON)
    if missing_trace_link_count >= config.missing_trace_link_block_count:
        reasons.append(MISSING_TRACE_LINK_BLOCK_REASON)
    elif missing_trace_link_count >= config.missing_trace_link_watch_count:
        reasons.append(MISSING_TRACE_LINK_WATCH_REASON)
    if deadline_proximity_seconds <= config.deadline_block_proximity_seconds:
        reasons.append(DEADLINE_PROXIMITY_BLOCK_REASON)
    elif deadline_proximity_seconds <= config.deadline_watch_proximity_seconds:
        reasons.append(DEADLINE_PROXIMITY_WATCH_REASON)
    if not reasons:
        reasons.append(CLEAR_REASON)
    return tuple(reason for reason in ROW_REASON_CODES if reason in reasons)


def _claim_trace_gap_score(
    *,
    average_claim_trace_coverage: Decimal,
    average_resolution_clause_coverage: Decimal,
    latest_trace_age_seconds: Decimal,
    average_source_authority_score: Decimal,
    contradiction_pressure: Decimal,
    independent_source_count: Decimal,
    missing_trace_link_count: Decimal,
    deadline_proximity_seconds: Decimal,
    config: ResearchSourceResolutionClaimTraceGapConfig,
) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        claim_trace_gap = ONE - average_claim_trace_coverage
        resolution_clause_gap = ONE - average_resolution_clause_coverage
        trace_staleness_pressure = min(
            latest_trace_age_seconds / config.trace_block_age_seconds,
            ONE,
        )
        source_authority_gap = ONE - average_source_authority_score
        independent_source_gap = max(
            (config.min_independent_source_count - independent_source_count)
            / config.min_independent_source_count,
            ZERO,
        )
        if config.missing_trace_link_block_count == ZERO:
            missing_trace_pressure = ONE if missing_trace_link_count > ZERO else ZERO
        else:
            missing_trace_pressure = min(
                missing_trace_link_count / config.missing_trace_link_block_count,
                ONE,
            )
        deadline_pressure = max(
            ONE - (deadline_proximity_seconds / config.deadline_watch_proximity_seconds),
            ZERO,
        )
        score = (
            claim_trace_gap
            + resolution_clause_gap
            + trace_staleness_pressure
            + source_authority_gap
            + contradiction_pressure
            + independent_source_gap
            + missing_trace_pressure
            + deadline_pressure
        ) / Decimal("8.000000")
        return _quantize(score)


def _row_status(reason_codes: tuple[str, ...]) -> str:
    if any(reason.endswith("_block") for reason in reason_codes):
        return "block"
    if reason_codes == (CLEAR_REASON,):
        return "pass"
    return "watch"


def _report_status(rows: tuple[ResearchSourceResolutionClaimTraceGapRow, ...]) -> str:
    if any(row.status == "block" for row in rows):
        return "block"
    if any(row.status == "watch" for row in rows):
        return "watch"
    return "pass"


def _report_reason_codes(
    rows: tuple[ResearchSourceResolutionClaimTraceGapRow, ...],
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


def _row_sort_key(row: ResearchSourceResolutionClaimTraceGapRow) -> tuple[Decimal, str]:
    return (-row.claim_trace_gap_score, row.claim_trace_key)


def _status_count(
    rows: tuple[ResearchSourceResolutionClaimTraceGapRow, ...],
    status: str,
) -> Decimal:
    return _count(sum(1 for row in rows if row.status == status))


def _reason_count(
    rows: tuple[ResearchSourceResolutionClaimTraceGapRow, ...],
    reasons: tuple[str, ...],
) -> Decimal:
    return _count(sum(1 for row in rows if any(reason in row.reason_codes for reason in reasons)))


def _sum_rows(
    rows: tuple[ResearchSourceResolutionClaimTraceGapRow, ...],
    field_name: str,
) -> Decimal:
    return _quantize(sum((getattr(row, field_name) for row in rows), ZERO))


def _average(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return _quantize(sum(values, ZERO) / Decimal(len(values)))


def _age_seconds(generated_at: datetime, observed_at: datetime) -> Decimal:
    generated_at_utc = _as_utc("generated_at", generated_at)
    observed_at_utc = _as_utc("observed_at", observed_at)
    delta = generated_at_utc - observed_at_utc
    with localcontext(DECIMAL_CONTEXT):
        seconds = (
            Decimal(delta.days) * SECONDS_PER_DAY
            + Decimal(delta.seconds)
            + (Decimal(delta.microseconds) / MICROSECONDS_PER_SECOND)
        )
    if seconds < ZERO:
        raise ValueError("observed_at must not be in the future")
    return _quantize(seconds)


def _deadline_seconds(generated_at: datetime, deadline_at: datetime) -> Decimal:
    generated_at_utc = _as_utc("generated_at", generated_at)
    deadline_at_utc = _as_utc("resolution_deadline_at", deadline_at)
    delta = deadline_at_utc - generated_at_utc
    with localcontext(DECIMAL_CONTEXT):
        seconds = (
            Decimal(delta.days) * SECONDS_PER_DAY
            + Decimal(delta.seconds)
            + (Decimal(delta.microseconds) / MICROSECONDS_PER_SECOND)
        )
    return _quantize(max(seconds, ZERO))


def _validate_config(config: ResearchSourceResolutionClaimTraceGapConfig) -> None:
    if config.block_claim_trace_coverage >= config.min_claim_trace_coverage:
        raise ValueError(
            "block_claim_trace_coverage must be below min_claim_trace_coverage",
        )
    if config.block_resolution_clause_coverage >= config.min_resolution_clause_coverage:
        raise ValueError(
            "block_resolution_clause_coverage must be below "
            "min_resolution_clause_coverage",
        )
    if config.trace_watch_age_seconds >= config.trace_block_age_seconds:
        raise ValueError("trace_watch_age_seconds must be below trace_block_age_seconds")
    if config.block_source_authority_score >= config.min_source_authority_score:
        raise ValueError(
            "block_source_authority_score must be below min_source_authority_score",
        )
    if config.contradiction_watch_pressure > config.contradiction_block_pressure:
        raise ValueError(
            "contradiction_watch_pressure must not exceed contradiction_block_pressure",
        )
    if config.block_independent_source_count > config.min_independent_source_count:
        raise ValueError(
            "block_independent_source_count must not exceed min_independent_source_count",
        )
    if config.missing_trace_link_watch_count > config.missing_trace_link_block_count:
        raise ValueError(
            "missing_trace_link_watch_count must not exceed "
            "missing_trace_link_block_count",
        )
    if config.deadline_block_proximity_seconds > config.deadline_watch_proximity_seconds:
        raise ValueError(
            "deadline_block_proximity_seconds must not exceed "
            "deadline_watch_proximity_seconds",
        )


def _validate_row(row: ResearchSourceResolutionClaimTraceGapRow) -> None:
    if row.evidence_count <= ZERO:
        raise ValueError("evidence_count must be positive")
    if row.evidence_family_count <= ZERO:
        raise ValueError("evidence_family_count must be positive")
    if row.latest_trace_age_seconds > row.average_trace_age_seconds:
        raise ValueError("latest_trace_age_seconds must not exceed average")
    if row.status != _row_status(row.reason_codes):
        raise ValueError("status must match reason_codes")
    if row.status == "pass" and row.reason_codes != (CLEAR_REASON,):
        raise ValueError("pass rows must be clear")


def _validate_report(report: ResearchSourceResolutionClaimTraceGapReport) -> None:
    if report.claim_trace_count != _count(len(report.rows)):
        raise ValueError("claim_trace_count must match rows")
    if report.evidence_count != _sum_rows(report.rows, "evidence_count"):
        raise ValueError("evidence_count must match rows")
    for status, field_name in (
        ("pass", "pass_claim_trace_count"),
        ("watch", "watch_claim_trace_count"),
        ("block", "block_claim_trace_count"),
    ):
        if getattr(report, field_name) != _status_count(report.rows, status):
            raise ValueError(f"{field_name} must match rows")
    reason_count_fields = (
        (
            "low_claim_trace_coverage_count",
            (CLAIM_TRACE_COVERAGE_WATCH_REASON, CLAIM_TRACE_COVERAGE_BLOCK_REASON),
        ),
        (
            "low_resolution_clause_coverage_count",
            (
                RESOLUTION_CLAUSE_COVERAGE_WATCH_REASON,
                RESOLUTION_CLAUSE_COVERAGE_BLOCK_REASON,
            ),
        ),
        (
            "stale_trace_count",
            (STALE_CLAIM_TRACE_WATCH_REASON, STALE_CLAIM_TRACE_BLOCK_REASON),
        ),
        (
            "low_source_authority_count",
            (LOW_SOURCE_AUTHORITY_WATCH_REASON, LOW_SOURCE_AUTHORITY_BLOCK_REASON),
        ),
        (
            "contradiction_pressure_count",
            (CONTRADICTION_PRESSURE_WATCH_REASON, CONTRADICTION_PRESSURE_BLOCK_REASON),
        ),
        (
            "low_independent_source_count",
            (
                LOW_INDEPENDENT_SOURCE_WATCH_REASON,
                LOW_INDEPENDENT_SOURCE_BLOCK_REASON,
            ),
        ),
        (
            "missing_trace_link_count",
            (MISSING_TRACE_LINK_WATCH_REASON, MISSING_TRACE_LINK_BLOCK_REASON),
        ),
        (
            "deadline_pressure_count",
            (DEADLINE_PROXIMITY_WATCH_REASON, DEADLINE_PROXIMITY_BLOCK_REASON),
        ),
    )
    for field_name, reasons in reason_count_fields:
        if getattr(report, field_name) != _reason_count(report.rows, reasons):
            raise ValueError(f"{field_name} must match rows")
    if report.highest_claim_trace_gap_score != _quantize(
        max(
            (row.claim_trace_gap_score for row in report.rows),
            default=ZERO,
        ),
    ):
        raise ValueError("highest_claim_trace_gap_score must match rows")
    if report.nearest_deadline_seconds != _quantize(
        min(
            (row.deadline_proximity_seconds for row in report.rows),
            default=ZERO,
        ),
    ):
        raise ValueError("nearest_deadline_seconds must match rows")
    if report.status != _report_status(report.rows):
        raise ValueError("status must match rows")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")
    if report.rows != tuple(sorted(report.rows, key=_row_sort_key)):
        raise ValueError("rows must use deterministic claim trace gap sort")


def _normalize_rows(
    value: object,
) -> tuple[ResearchSourceResolutionClaimTraceGapRow, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("rows must be a list or tuple")
    rows: list[ResearchSourceResolutionClaimTraceGapRow] = []
    seen: set[str] = set()
    for row in tuple(value):
        if type(row) is not ResearchSourceResolutionClaimTraceGapRow:
            raise ValueError("rows must contain ResearchSourceResolutionClaimTraceGapRow")
        row = _revalidate_row(row)
        require_paper_only_flags("claim trace gap row", row)
        if row.claim_trace_key in seen:
            raise ValueError("rows must be unique by claim_trace_key")
        seen.add(row.claim_trace_key)
        rows.append(row)
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


def _require_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    raw_value = _require_raw_decimal(field_name, value)
    if raw_value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return _require_exact_decimal(field_name, raw_value)


def _require_raw_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    if value.is_zero() and value.is_signed():
        raise ValueError(f"{field_name} must not be signed zero")
    return value


def _require_exact_decimal(field_name: str, value: Decimal) -> Decimal:
    if value.as_tuple().exponent != QUANT.as_tuple().exponent:
        raise ValueError(f"{field_name} must use six decimal places")
    decimal_value = _quantize(value)
    if decimal_value != value:
        raise ValueError(f"{field_name} must use six decimal places")
    return decimal_value


def _require_ratio(field_name: str, value: object) -> Decimal:
    raw_value = _require_raw_decimal(field_name, value)
    if raw_value < ZERO or raw_value > ONE:
        raise ValueError(f"{field_name} must be between zero and one")
    return _require_exact_decimal(field_name, raw_value)


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_public_fields(
    label: str,
    value: dict[str, Any],
    expected_fields: tuple[str, ...],
) -> None:
    if any(type(key) is not str for key in value):
        raise ValueError(f"{label} keys must be strings")
    actual_fields = tuple(value)
    if frozenset(actual_fields) != frozenset(expected_fields):
        raise ValueError(f"{label} must contain exact public fields")
    if actual_fields != expected_fields:
        raise ValueError(f"{label} must use canonical field order")


def _require_payload_flags(label: str, value: dict[str, Any]) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        _require_true_flag(f"{label} {field_name}", value.get(field_name))


def _require_true_flag(field_name: str, value: object) -> bool:
    if value is not True:
        raise ValueError(f"{field_name} must be True")
    return True


def _require_canonical_public_json(
    value: object,
    path: str = "public payload",
) -> None:
    if value is None or type(value) in (str, bool):
        return
    if type(value) in (int, float, Decimal):
        raise ValueError(f"{path} must use Decimal-derived strings")
    if type(value) is dict:
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError(f"{path} must use canonical plain JSON values")
            _require_canonical_public_json(item, f"{path}.{key}")
        return
    if type(value) is list:
        for index, item in enumerate(value):
            _require_canonical_public_json(item, f"{path}.{index}")
        return
    raise ValueError(f"{path} must use canonical plain JSON values")


def _require_public_string(field_name: str, value: object) -> str:
    _require_canonical_string(field_name, value)
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    return value


def _require_public_status(field_name: str, value: object) -> str:
    _require_status(field_name, value)
    if type(value) is not str:
        raise ValueError(f"{field_name} must be pass, watch, or block")
    return value


def _require_public_reason_codes(
    field_name: str,
    value: object,
    allowed: tuple[str, ...],
) -> tuple[str, ...]:
    if type(value) is not list:
        raise ValueError(f"{field_name} must be a public list")
    return _normalize_reason_codes(field_name, value, allowed)


def _require_public_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a canonical Decimal-derived string")
    try:
        decimal_value = Decimal(value)
    except Exception as exc:
        raise ValueError(
            f"{field_name} must be a canonical Decimal-derived string",
        ) from exc
    normalized = _require_nonnegative_decimal(field_name, decimal_value)
    if value != format(normalized, "f"):
        raise ValueError(f"{field_name} must be a canonical Decimal-derived string")
    return normalized


def _require_public_ratio(field_name: str, value: object) -> Decimal:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a canonical Decimal-derived string")
    try:
        decimal_value = Decimal(value)
    except Exception as exc:
        raise ValueError(
            f"{field_name} must be a canonical Decimal-derived string",
        ) from exc
    normalized = _require_ratio(field_name, decimal_value)
    if value != format(normalized, "f"):
        raise ValueError(f"{field_name} must be a canonical Decimal-derived string")
    return normalized


def _require_public_datetime(field_name: str, value: object) -> datetime:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a canonical UTC datetime")
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError as exc:
        raise ValueError(f"{field_name} must be a canonical UTC datetime") from exc
    normalized = _as_utc(field_name, parsed)
    if value != normalized.isoformat():
        raise ValueError(f"{field_name} must be a canonical UTC datetime")
    return normalized


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
        or value not in RESEARCH_SOURCE_RESOLUTION_CLAIM_TRACE_GAP_REPORT_STATUSES
    ):
        raise ValueError(f"{field_name} must be pass, watch, or block")


def _require_public_label(field_name: str, value: object) -> str:
    _require_canonical_string(field_name, value)
    lowered = value.lower()
    unsafe_fragments = (
        "api-key",
        "api_key",
        "auth_token",
        "authentication",
        "authorization",
        "bearer",
        "bet-size",
        "bet_size",
        "http://",
        "https://",
        "postgres://",
        "mysql://",
        "jdbc:",
        "candidate",
        "credential",
        "dsn",
        "execution",
        "identifier",
        "live",
        "market",
        "notional",
        "password",
        "position-size",
        "position_size",
        "private",
        "question",
        "recommendation",
        "recommended",
        "secret",
        "sizing",
        "slug",
        "stake",
        "table",
        "token",
        "trade",
        "url",
        "wallet",
    )
    if any(fragment in lowered for fragment in unsafe_fragments):
        raise ValueError(f"{field_name} contains unsafe text")
    if not all(char.isalnum() or char in (".", "_", "-") for char in value):
        raise ValueError(f"{field_name} must be a public label")
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


def _require_sha256(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if len(value) != SHA256_HEX_LENGTH:
        raise ValueError(f"{field_name} must be a SHA-256 digest")
    if any(char not in "0123456789abcdef" for char in value):
        raise ValueError(f"{field_name} must be lowercase hex")
    return value


def _report_digest_from_public_payload(
    report: ResearchSourceResolutionClaimTraceGapReport,
) -> str:
    payload = json_ready_no_floats(report)
    if type(payload) is not dict:
        raise ValueError("payload must be a dict")
    _reject_unsafe_public_surface("payload", payload)
    return _payload_validation_digest(payload)


def _payload_validation_digest(payload: dict[str, Any]) -> str:
    canonical_payload = dict(payload)
    canonical_payload.pop("derived_validation_digest", None)
    encoded = json.dumps(
        canonical_payload,
        sort_keys=True,
        separators=(",", ":"),
    ).encode()
    return hashlib.sha256(encoded).hexdigest()


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
        "api_key",
        "auth_token",
        "authentication",
        "authorization",
        "bearer",
        "bet_size",
        "raw_candidate",
        "candidate_id",
        "candidate_slug",
        "execution",
        "market_id",
        "market_slug",
        "market_question",
        "notional",
        "password",
        "position_size",
        "recommendation",
        "recommended",
        "sizing",
        "source_id",
        "source_url",
        "source_text",
        "dsn",
        "stake",
        "table_name",
        "token",
        "wallet",
        "order",
        "trade",
        "live",
    )
    if any(fragment in lowered for fragment in unsafe_fragments):
        raise ValueError(f"{label} contains unsafe public field")


def _reject_unsafe_public_string(label: str, value: str) -> None:
    lowered = value.lower()
    unsafe_fragments = (
        "api-key",
        "api_key",
        "auth-token",
        "auth_token",
        "authentication",
        "authorization",
        "bearer",
        "bet-size",
        "bet_size",
        "http://",
        "https://",
        "postgres://",
        "mysql://",
        "jdbc:",
        "candidate-",
        "candidate_",
        "credential",
        "dsn",
        "execution",
        "live",
        "market-",
        "market_",
        "notional",
        "password",
        "position-size",
        "position_size",
        "private",
        "question",
        "recommendation",
        "recommended",
        "secret",
        "sizing",
        "slug",
        "stake",
        "table",
        "token",
        "trade",
        "url",
        "wallet",
    )
    if any(fragment in lowered for fragment in unsafe_fragments):
        raise ValueError(f"{label} contains unsafe public surface")


__all__ = (
    "DEFAULT_RESEARCH_SOURCE_RESOLUTION_CLAIM_TRACE_GAP_REPORT_CONFIG_VERSION",
    "RESEARCH_SOURCE_RESOLUTION_CLAIM_TRACE_GAP_REPORT_STATUSES",
    "ResearchSourceResolutionClaimTraceGapConfig",
    "ResearchSourceResolutionClaimTraceGapInput",
    "ResearchSourceResolutionClaimTraceGapRow",
    "ResearchSourceResolutionClaimTraceGapReport",
    "build_research_source_resolution_claim_trace_gap_report",
    "research_source_resolution_claim_trace_gap_report_payload",
    "research_source_resolution_claim_trace_gap_report_digest",
    "validate_research_source_resolution_claim_trace_gap_report_digest",
)
