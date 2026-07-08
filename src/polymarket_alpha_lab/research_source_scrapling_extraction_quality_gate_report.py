"""Report-only quality gate for sanitized Scrapling extraction outputs."""

from __future__ import annotations

from dataclasses import asdict, dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal, ROUND_HALF_UP
from hashlib import sha256
import json
import re
from typing import Any, Mapping, Sequence


DEFAULT_RESEARCH_SOURCE_SCRAPLING_EXTRACTION_QUALITY_GATE_CONFIG_VERSION = (
    "research-source-scrapling-extraction-quality-gate-report-v0"
)

_QUANT = Decimal("0.000001")
_ZERO = Decimal("0.000000")
_ONE = Decimal("1.000000")
_DIGEST_RE = re.compile(r"^[0-9a-f]{64}$")
_PUBLIC_IDENTIFIER_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,127}$")

_STATUS_PASS = "pass"
_STATUS_WATCH = "watch"
_STATUS_BLOCK = "block"
_STATUSES = frozenset((_STATUS_PASS, _STATUS_WATCH, _STATUS_BLOCK))
_STATUS_RANK = {_STATUS_BLOCK: 0, _STATUS_WATCH: 1, _STATUS_PASS: 2}
_STATUS_REASON = {
    _STATUS_PASS: "scrapling_extraction_quality_gate_pass",
    _STATUS_WATCH: "scrapling_extraction_quality_gate_watch",
    _STATUS_BLOCK: "scrapling_extraction_quality_gate_block",
}
_REPORT_EMPTY_REASON = "empty_scrapling_extraction_output_set"
_ROW_DETAIL_REASON_SEQUENCE = (
    "extraction_completeness_below_block_threshold",
    "extraction_completeness_below_pass_threshold",
    "source_freshness_below_block_threshold",
    "source_freshness_below_pass_threshold",
    "selector_stability_below_block_threshold",
    "selector_stability_below_pass_threshold",
    "conflict_risk_above_block_threshold",
    "conflict_risk_above_pass_threshold",
    "fallback_coverage_below_block_threshold",
    "fallback_coverage_below_pass_threshold",
)
_REASON_CODE_SEQUENCE = (
    _REPORT_EMPTY_REASON,
    _STATUS_REASON[_STATUS_PASS],
    _STATUS_REASON[_STATUS_WATCH],
    _STATUS_REASON[_STATUS_BLOCK],
    *_ROW_DETAIL_REASON_SEQUENCE,
)
_BLOCK_DETAIL_REASONS = frozenset(
    reason_code
    for reason_code in _ROW_DETAIL_REASON_SEQUENCE
    if reason_code.endswith("_block_threshold")
)
_UNSAFE_PUBLIC_FRAGMENTS = (
    "candidate_id",
    "candidate-id",
    "market_id",
    "market-id",
    "market_slug",
    "market-slug",
    "slug",
    "question",
    "source_url",
    "source-url",
    "raw_url",
    "raw-url",
    "url",
    "source_text",
    "source-text",
    "raw_text",
    "raw-text",
    "dsn",
    "table",
    "token",
    "wallet",
    "order",
    "trade",
    "live",
    "auth",
    "network",
    "database",
    "http://",
    "https://",
    "www.",
)


@dataclass(frozen=True)
class ResearchSourceScraplingExtractionQualityGateConfig:
    config_version: str = (
        DEFAULT_RESEARCH_SOURCE_SCRAPLING_EXTRACTION_QUALITY_GATE_CONFIG_VERSION
    )
    min_extraction_completeness_pass_ratio: Decimal = Decimal("0.900000")
    min_extraction_completeness_block_ratio: Decimal = Decimal("0.500000")
    max_freshness_age_pass_seconds: Decimal = Decimal("3600.000000")
    max_freshness_age_block_seconds: Decimal = Decimal("21600.000000")
    min_source_freshness_pass_score: Decimal = Decimal("0.800000")
    min_source_freshness_block_score: Decimal = Decimal("0.200000")
    min_selector_stability_pass_ratio: Decimal = Decimal("0.900000")
    min_selector_stability_block_ratio: Decimal = Decimal("0.500000")
    max_conflict_risk_pass_ratio: Decimal = Decimal("0.250000")
    max_conflict_risk_block_ratio: Decimal = Decimal("0.500000")
    min_fallback_coverage_pass_ratio: Decimal = Decimal("0.800000")
    min_fallback_coverage_block_ratio: Decimal = Decimal("0.500000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchSourceScraplingExtractionQualityGateConfig does not support "
            "subclassing",
        )

    def __post_init__(self) -> None:
        _require_exact_type(
            "config",
            self,
            ResearchSourceScraplingExtractionQualityGateConfig,
        )
        _require_safe_public_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_SOURCE_SCRAPLING_EXTRACTION_QUALITY_GATE_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "max_freshness_age_pass_seconds",
            "max_freshness_age_block_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_positive_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "min_extraction_completeness_pass_ratio",
            "min_extraction_completeness_block_ratio",
            "min_source_freshness_pass_score",
            "min_source_freshness_block_score",
            "min_selector_stability_pass_ratio",
            "min_selector_stability_block_ratio",
            "max_conflict_risk_pass_ratio",
            "max_conflict_risk_block_ratio",
            "min_fallback_coverage_pass_ratio",
            "min_fallback_coverage_block_ratio",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        _require_floor_pair(
            "min_extraction_completeness_pass_ratio",
            self.min_extraction_completeness_pass_ratio,
            "min_extraction_completeness_block_ratio",
            self.min_extraction_completeness_block_ratio,
        )
        _require_floor_pair(
            "min_source_freshness_pass_score",
            self.min_source_freshness_pass_score,
            "min_source_freshness_block_score",
            self.min_source_freshness_block_score,
        )
        _require_floor_pair(
            "min_selector_stability_pass_ratio",
            self.min_selector_stability_pass_ratio,
            "min_selector_stability_block_ratio",
            self.min_selector_stability_block_ratio,
        )
        _require_floor_pair(
            "min_fallback_coverage_pass_ratio",
            self.min_fallback_coverage_pass_ratio,
            "min_fallback_coverage_block_ratio",
            self.min_fallback_coverage_block_ratio,
        )
        if self.max_conflict_risk_pass_ratio > self.max_conflict_risk_block_ratio:
            raise ValueError(
                "max_conflict_risk_pass_ratio must not exceed block threshold",
            )
        if self.max_freshness_age_pass_seconds >= self.max_freshness_age_block_seconds:
            raise ValueError(
                "max_freshness_age_pass_seconds must be less than block threshold",
            )
        _require_hard_flags("config", self)
        _reject_unsafe_public_surface("config", self)


@dataclass(frozen=True)
class ResearchSourceScraplingExtractionOutput:
    extraction_scope: str
    extracted_at: datetime
    required_field_count: Decimal
    extracted_field_count: Decimal
    selector_expected_count: Decimal
    selector_match_count: Decimal
    conflict_count: Decimal
    fallback_attempt_count: Decimal
    fallback_success_count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchSourceScraplingExtractionOutput does not support subclassing",
        )

    def __post_init__(self) -> None:
        _require_exact_type("output", self, ResearchSourceScraplingExtractionOutput)
        object.__setattr__(
            self,
            "extraction_scope",
            _require_safe_public_identifier("extraction_scope", self.extraction_scope),
        )
        object.__setattr__(self, "extracted_at", _as_utc("extracted_at", self.extracted_at))
        object.__setattr__(
            self,
            "required_field_count",
            _normalize_positive_count("required_field_count", self.required_field_count),
        )
        for field_name in (
            "extracted_field_count",
            "selector_expected_count",
            "selector_match_count",
            "conflict_count",
            "fallback_attempt_count",
            "fallback_success_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_count(field_name, getattr(self, field_name)),
            )
        _validate_output_consistency(self)
        _require_hard_flags("output", self)
        _reject_unsafe_public_surface("output", self)


@dataclass(frozen=True)
class ResearchSourceScraplingExtractionQualityGateRow:
    extraction_scope: str
    extracted_at: datetime
    freshness_age_seconds: Decimal
    extraction_completeness_ratio: Decimal
    source_freshness_score: Decimal
    selector_stability_ratio: Decimal
    conflict_risk_ratio: Decimal
    fallback_coverage_ratio: Decimal
    extraction_quality_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchSourceScraplingExtractionQualityGateRow does not support "
            "subclassing",
        )

    def __post_init__(self) -> None:
        _require_exact_type("row", self, ResearchSourceScraplingExtractionQualityGateRow)
        object.__setattr__(
            self,
            "extraction_scope",
            _require_safe_public_identifier("extraction_scope", self.extraction_scope),
        )
        object.__setattr__(self, "extracted_at", _as_utc("extracted_at", self.extracted_at))
        object.__setattr__(
            self,
            "freshness_age_seconds",
            _normalize_nonnegative_decimal(
                "freshness_age_seconds",
                self.freshness_age_seconds,
            ),
        )
        for field_name in (
            "extraction_completeness_ratio",
            "source_freshness_score",
            "selector_stability_ratio",
            "conflict_risk_ratio",
            "fallback_coverage_ratio",
            "extraction_quality_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        _require_status("status", self.status)
        object.__setattr__(self, "reason_codes", _normalize_reason_codes(self.reason_codes))
        _validate_row_consistency(self)
        _require_hard_flags("row", self)
        _reject_unsafe_public_surface("row", self)


@dataclass(frozen=True)
class ResearchSourceScraplingExtractionQualityGateReport:
    generated_at: datetime
    config_version: str
    extraction_scope_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    average_extraction_quality_score: Decimal
    lowest_extraction_quality_score: Decimal
    highest_conflict_risk_ratio: Decimal
    max_freshness_age_seconds: Decimal
    status: str
    reason_codes: tuple[str, ...]
    rows: tuple[ResearchSourceScraplingExtractionQualityGateRow, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchSourceScraplingExtractionQualityGateReport does not support "
            "subclassing",
        )

    def __post_init__(self) -> None:
        _require_exact_type(
            "report",
            self,
            ResearchSourceScraplingExtractionQualityGateReport,
        )
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_safe_public_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_SOURCE_SCRAPLING_EXTRACTION_QUALITY_GATE_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "extraction_scope_count",
            "pass_count",
            "watch_count",
            "block_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_count(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "average_extraction_quality_score",
            "lowest_extraction_quality_score",
            "highest_conflict_risk_ratio",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "max_freshness_age_seconds",
            _normalize_nonnegative_decimal(
                "max_freshness_age_seconds",
                self.max_freshness_age_seconds,
            ),
        )
        _require_status("status", self.status)
        object.__setattr__(self, "reason_codes", _normalize_reason_codes(self.reason_codes))
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        _validate_report_consistency(self)
        _require_hard_flags("report", self)
        _reject_unsafe_public_surface("report", self)
        expected_digest = _report_digest_from_values(_report_values_without_digest(self))
        if self.derived_validation_digest == "":
            object.__setattr__(self, "derived_validation_digest", expected_digest)
        elif self.derived_validation_digest != expected_digest:
            raise ValueError("derived_validation_digest must match report fields")
        _require_digest("derived_validation_digest", self.derived_validation_digest)

    @property
    def payload(self) -> dict[str, Any]:
        return research_source_scrapling_extraction_quality_gate_report_payload(self)


def build_research_source_scrapling_extraction_quality_gate_report(
    outputs: Sequence[ResearchSourceScraplingExtractionOutput],
    *,
    config: ResearchSourceScraplingExtractionQualityGateConfig | None = None,
    generated_at: datetime,
) -> ResearchSourceScraplingExtractionQualityGateReport:
    normalized_config = (
        ResearchSourceScraplingExtractionQualityGateConfig()
        if config is None
        else _require_config(config)
    )
    generated_at_utc = _as_utc("generated_at", generated_at)
    normalized_outputs = _normalize_outputs(outputs)
    rows = tuple(
        sorted(
            (
                _row_from_output(
                    output,
                    config=normalized_config,
                    generated_at=generated_at_utc,
                )
                for output in normalized_outputs
            ),
            key=lambda row: row.extraction_scope,
        ),
    )
    return ResearchSourceScraplingExtractionQualityGateReport(
        generated_at=generated_at_utc,
        config_version=normalized_config.config_version,
        extraction_scope_count=_decimal_from_int(len(rows)),
        pass_count=_status_count(rows, _STATUS_PASS),
        watch_count=_status_count(rows, _STATUS_WATCH),
        block_count=_status_count(rows, _STATUS_BLOCK),
        average_extraction_quality_score=_average_ratio(
            tuple(row.extraction_quality_score for row in rows),
        ),
        lowest_extraction_quality_score=min(
            (row.extraction_quality_score for row in rows),
            default=_ZERO,
        ),
        highest_conflict_risk_ratio=max(
            (row.conflict_risk_ratio for row in rows),
            default=_ZERO,
        ),
        max_freshness_age_seconds=max(
            (row.freshness_age_seconds for row in rows),
            default=_ZERO,
        ),
        status=_report_status(rows),
        reason_codes=_report_reason_codes(rows),
        rows=rows,
    )


def research_source_scrapling_extraction_quality_gate_report_payload(
    value: ResearchSourceScraplingExtractionQualityGateReport | Mapping[str, object],
) -> dict[str, Any]:
    if type(value) is ResearchSourceScraplingExtractionQualityGateReport:
        _require_hard_flags("report", value)
        _validate_report_digest(value)
        payload = _json_ready(asdict(value))
    elif isinstance(value, Mapping):
        payload = _copy_json_object(value)
    else:
        raise ValueError(
            "value must be a ResearchSourceScraplingExtractionQualityGateReport or dict",
        )
    if type(payload) is not dict:
        raise ValueError("payload must be a JSON object")
    _reject_unsafe_public_surface("payload", payload, allow_json_containers=True)
    _validate_public_payload_digest(payload)
    return payload


def research_source_scrapling_extraction_quality_gate_report_digest(
    report: ResearchSourceScraplingExtractionQualityGateReport,
) -> str:
    _require_exact_type("report", report, ResearchSourceScraplingExtractionQualityGateReport)
    _require_hard_flags("report", report)
    return _report_digest_from_values(_report_values_without_digest(report))


def validate_research_source_scrapling_extraction_quality_gate_report_digest(
    report: ResearchSourceScraplingExtractionQualityGateReport,
) -> bool:
    _validate_report_digest(report)
    return True


def _require_config(
    config: ResearchSourceScraplingExtractionQualityGateConfig,
) -> ResearchSourceScraplingExtractionQualityGateConfig:
    _require_exact_type("config", config, ResearchSourceScraplingExtractionQualityGateConfig)
    _require_hard_flags("config", config)
    _reject_unsafe_public_surface("config", config)
    return config


def _normalize_outputs(
    outputs: Sequence[ResearchSourceScraplingExtractionOutput],
) -> tuple[ResearchSourceScraplingExtractionOutput, ...]:
    if isinstance(outputs, (str, bytes, dict)):
        raise ValueError("outputs must be a sequence of Scrapling extraction outputs")
    normalized = tuple(outputs)
    seen_scopes: set[str] = set()
    for output in normalized:
        _require_exact_type("output", output, ResearchSourceScraplingExtractionOutput)
        _require_hard_flags("output", output)
        _reject_unsafe_public_surface("output", output)
        if output.extraction_scope in seen_scopes:
            raise ValueError("extraction_scope values must be unique")
        seen_scopes.add(output.extraction_scope)
    return normalized


def _row_from_output(
    output: ResearchSourceScraplingExtractionOutput,
    *,
    config: ResearchSourceScraplingExtractionQualityGateConfig,
    generated_at: datetime,
) -> ResearchSourceScraplingExtractionQualityGateRow:
    if output.extracted_at > generated_at:
        raise ValueError("extracted_at must not be after generated_at")
    freshness_age_seconds = _duration_seconds(output.extracted_at, generated_at)
    extraction_completeness_ratio = _ratio(
        output.extracted_field_count,
        output.required_field_count,
    )
    source_freshness_score = _source_freshness_score(
        freshness_age_seconds,
        config=config,
    )
    selector_stability_ratio = _optional_ratio_default_one(
        output.selector_match_count,
        output.selector_expected_count,
    )
    conflict_risk_ratio = _optional_ratio_default_zero(
        output.conflict_count,
        output.selector_expected_count,
    )
    fallback_coverage_ratio = _optional_ratio_default_one(
        output.fallback_success_count,
        output.fallback_attempt_count,
    )
    detail_reasons = _row_detail_reasons(
        extraction_completeness_ratio=extraction_completeness_ratio,
        source_freshness_score=source_freshness_score,
        selector_stability_ratio=selector_stability_ratio,
        conflict_risk_ratio=conflict_risk_ratio,
        fallback_coverage_ratio=fallback_coverage_ratio,
        config=config,
    )
    status = _row_status(detail_reasons)
    return ResearchSourceScraplingExtractionQualityGateRow(
        extraction_scope=output.extraction_scope,
        extracted_at=output.extracted_at,
        freshness_age_seconds=freshness_age_seconds,
        extraction_completeness_ratio=extraction_completeness_ratio,
        source_freshness_score=source_freshness_score,
        selector_stability_ratio=selector_stability_ratio,
        conflict_risk_ratio=conflict_risk_ratio,
        fallback_coverage_ratio=fallback_coverage_ratio,
        extraction_quality_score=_average_ratio(
            (
                extraction_completeness_ratio,
                source_freshness_score,
                selector_stability_ratio,
                _normalize_ratio("conflict_resilience_score", _ONE - conflict_risk_ratio),
                fallback_coverage_ratio,
            ),
        ),
        status=status,
        reason_codes=(_STATUS_REASON[status], *detail_reasons),
    )


def _source_freshness_score(
    freshness_age_seconds: Decimal,
    *,
    config: ResearchSourceScraplingExtractionQualityGateConfig,
) -> Decimal:
    if freshness_age_seconds <= config.max_freshness_age_pass_seconds:
        return _ONE
    if freshness_age_seconds >= config.max_freshness_age_block_seconds:
        return _ZERO
    freshness_window = (
        config.max_freshness_age_block_seconds - config.max_freshness_age_pass_seconds
    )
    age_over_pass = freshness_age_seconds - config.max_freshness_age_pass_seconds
    return _normalize_ratio("source_freshness_score", _ONE - (age_over_pass / freshness_window))


def _row_detail_reasons(
    *,
    extraction_completeness_ratio: Decimal,
    source_freshness_score: Decimal,
    selector_stability_ratio: Decimal,
    conflict_risk_ratio: Decimal,
    fallback_coverage_ratio: Decimal,
    config: ResearchSourceScraplingExtractionQualityGateConfig,
) -> tuple[str, ...]:
    hard_block_reasons: list[str] = []
    if extraction_completeness_ratio < config.min_extraction_completeness_block_ratio:
        hard_block_reasons.append("extraction_completeness_below_block_threshold")
    if source_freshness_score < config.min_source_freshness_block_score:
        hard_block_reasons.append("source_freshness_below_block_threshold")
    if selector_stability_ratio < config.min_selector_stability_block_ratio:
        hard_block_reasons.append("selector_stability_below_block_threshold")
    if fallback_coverage_ratio < config.min_fallback_coverage_block_ratio:
        hard_block_reasons.append("fallback_coverage_below_block_threshold")
    block_reasons = list(hard_block_reasons)
    if conflict_risk_ratio > config.max_conflict_risk_block_ratio or (
        conflict_risk_ratio >= config.max_conflict_risk_block_ratio
        and hard_block_reasons
    ):
        block_reasons.append("conflict_risk_above_block_threshold")
    if block_reasons:
        return _normalize_detail_reason_codes(tuple(block_reasons))

    watch_reasons: list[str] = []
    if extraction_completeness_ratio < config.min_extraction_completeness_pass_ratio:
        watch_reasons.append("extraction_completeness_below_pass_threshold")
    if source_freshness_score < config.min_source_freshness_pass_score:
        watch_reasons.append("source_freshness_below_pass_threshold")
    if selector_stability_ratio < config.min_selector_stability_pass_ratio:
        watch_reasons.append("selector_stability_below_pass_threshold")
    if conflict_risk_ratio > config.max_conflict_risk_pass_ratio:
        watch_reasons.append("conflict_risk_above_pass_threshold")
    if fallback_coverage_ratio < config.min_fallback_coverage_pass_ratio:
        watch_reasons.append("fallback_coverage_below_pass_threshold")
    return _normalize_detail_reason_codes(tuple(watch_reasons))


def _row_status(reason_codes: tuple[str, ...]) -> str:
    if any(reason_code in _BLOCK_DETAIL_REASONS for reason_code in reason_codes):
        return _STATUS_BLOCK
    if reason_codes:
        return _STATUS_WATCH
    return _STATUS_PASS


def _report_status(
    rows: tuple[ResearchSourceScraplingExtractionQualityGateRow, ...],
) -> str:
    if not rows:
        return _STATUS_BLOCK
    return min((row.status for row in rows), key=lambda status: _STATUS_RANK[status])


def _report_reason_codes(
    rows: tuple[ResearchSourceScraplingExtractionQualityGateRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return (_REPORT_EMPTY_REASON,)
    reason_codes: list[str] = [_STATUS_REASON[_report_status(rows)]]
    for row in rows:
        reason_codes.extend(
            reason_code
            for reason_code in row.reason_codes
            if reason_code != _STATUS_REASON[row.status]
        )
    return _normalize_reason_codes(tuple(reason_codes))


def _validate_output_consistency(
    output: ResearchSourceScraplingExtractionOutput,
) -> None:
    if output.extracted_field_count > output.required_field_count:
        raise ValueError("extracted_field_count must not exceed required_field_count")
    if output.selector_match_count > output.selector_expected_count:
        raise ValueError("selector_match_count must not exceed selector_expected_count")
    if output.conflict_count > output.selector_expected_count:
        raise ValueError("conflict_count must not exceed selector_expected_count")
    if output.fallback_success_count > output.fallback_attempt_count:
        raise ValueError("fallback_success_count must not exceed fallback_attempt_count")


def _validate_row_consistency(
    row: ResearchSourceScraplingExtractionQualityGateRow,
) -> None:
    if row.status != _row_status(_detail_reasons_from_row(row)):
        raise ValueError("row status must match reason_codes")
    if not row.reason_codes or row.reason_codes[0] != _STATUS_REASON[row.status]:
        raise ValueError("row reason_codes must start with status reason")
    expected_quality_score = _average_ratio(
        (
            row.extraction_completeness_ratio,
            row.source_freshness_score,
            row.selector_stability_ratio,
            _normalize_ratio("conflict_resilience_score", _ONE - row.conflict_risk_ratio),
            row.fallback_coverage_ratio,
        ),
    )
    if row.extraction_quality_score != expected_quality_score:
        raise ValueError("extraction_quality_score must match quality factors")


def _validate_report_consistency(
    report: ResearchSourceScraplingExtractionQualityGateReport,
) -> None:
    if report.extraction_scope_count != _decimal_from_int(len(report.rows)):
        raise ValueError("extraction_scope_count must match rows")
    if report.pass_count != _status_count(report.rows, _STATUS_PASS):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _status_count(report.rows, _STATUS_WATCH):
        raise ValueError("watch_count must match rows")
    if report.block_count != _status_count(report.rows, _STATUS_BLOCK):
        raise ValueError("block_count must match rows")
    if report.average_extraction_quality_score != _average_ratio(
        tuple(row.extraction_quality_score for row in report.rows),
    ):
        raise ValueError("average_extraction_quality_score must match rows")
    if report.lowest_extraction_quality_score != min(
        (row.extraction_quality_score for row in report.rows),
        default=_ZERO,
    ):
        raise ValueError("lowest_extraction_quality_score must match rows")
    if report.highest_conflict_risk_ratio != max(
        (row.conflict_risk_ratio for row in report.rows),
        default=_ZERO,
    ):
        raise ValueError("highest_conflict_risk_ratio must match rows")
    if report.max_freshness_age_seconds != max(
        (row.freshness_age_seconds for row in report.rows),
        default=_ZERO,
    ):
        raise ValueError("max_freshness_age_seconds must match rows")
    if report.status != _report_status(report.rows):
        raise ValueError("status must match rows")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")
    if tuple(row.extraction_scope for row in report.rows) != tuple(
        sorted(row.extraction_scope for row in report.rows),
    ):
        raise ValueError("rows must be sorted by extraction_scope")
    if len({row.extraction_scope for row in report.rows}) != len(report.rows):
        raise ValueError("rows must have unique extraction_scope values")


def _normalize_rows(
    rows: object,
) -> tuple[ResearchSourceScraplingExtractionQualityGateRow, ...]:
    if isinstance(rows, (str, bytes, dict)):
        raise ValueError("rows must be a tuple of quality gate rows")
    normalized = tuple(rows)  # type: ignore[arg-type]
    for row in normalized:
        _require_exact_type("row", row, ResearchSourceScraplingExtractionQualityGateRow)
        _require_hard_flags("row", row)
        _reject_unsafe_public_surface("row", row)
    return normalized


def _detail_reasons_from_row(
    row: ResearchSourceScraplingExtractionQualityGateRow,
) -> tuple[str, ...]:
    return tuple(
        reason_code
        for reason_code in row.reason_codes
        if reason_code != _STATUS_REASON[row.status]
    )


def _normalize_detail_reason_codes(reason_codes: tuple[str, ...]) -> tuple[str, ...]:
    normalized = _normalize_reason_codes(reason_codes)
    for reason_code in normalized:
        if reason_code not in _ROW_DETAIL_REASON_SEQUENCE:
            raise ValueError("detail reason_code must be supported")
    return tuple(
        reason_code
        for reason_code in _ROW_DETAIL_REASON_SEQUENCE
        if reason_code in normalized
    )


def _normalize_reason_codes(reason_codes: object) -> tuple[str, ...]:
    if isinstance(reason_codes, (str, bytes)):
        raise ValueError("reason_codes must be an iterable")
    try:
        normalized = tuple(reason_codes)  # type: ignore[arg-type]
    except TypeError as exc:
        raise ValueError("reason_codes must be an iterable") from exc
    for reason_code in normalized:
        _require_safe_public_string("reason_code", reason_code)
        if reason_code not in _REASON_CODE_SEQUENCE:
            raise ValueError("reason_code must be supported")
    if len(set(normalized)) != len(normalized):
        raise ValueError("reason_codes must not contain duplicates")
    return tuple(
        reason_code for reason_code in _REASON_CODE_SEQUENCE if reason_code in normalized
    )


def _status_count(
    rows: tuple[ResearchSourceScraplingExtractionQualityGateRow, ...],
    status: str,
) -> Decimal:
    return _decimal_from_int(sum(1 for row in rows if row.status == status))


def _average_ratio(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return _ZERO
    return _normalize_ratio("average_ratio", sum(values, _ZERO) / _decimal_from_int(len(values)))


def _duration_seconds(start: datetime, end: datetime) -> Decimal:
    delta = end - start
    return _normalize_nonnegative_decimal(
        "duration_seconds",
        Decimal(str(delta.total_seconds())),
    )


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == _ZERO:
        raise ValueError("ratio denominator must be positive")
    return _normalize_ratio("ratio", numerator / denominator)


def _optional_ratio_default_one(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == _ZERO:
        return _ONE
    return _ratio(numerator, denominator)


def _optional_ratio_default_zero(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == _ZERO:
        if numerator != _ZERO:
            raise ValueError("ratio numerator must be zero when denominator is zero")
        return _ZERO
    return _ratio(numerator, denominator)


def _require_floor_pair(
    pass_name: str,
    pass_value: Decimal,
    block_name: str,
    block_value: Decimal,
) -> None:
    if block_value > pass_value:
        raise ValueError(f"{block_name} must not exceed pass threshold")


def _require_status(field_name: str, value: object) -> None:
    _require_safe_public_string(field_name, value)
    if value not in _STATUSES:
        raise ValueError(f"{field_name} must be pass, watch, or block")


def _require_exact_type(field_name: str, value: object, expected_type: type[object]) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{field_name} must be exactly {expected_type.__name__}")


def _require_safe_public_identifier(field_name: str, value: object) -> str:
    _require_safe_public_string(field_name, value)
    if not _PUBLIC_IDENTIFIER_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a safe public identifier")
    return value


def _require_safe_public_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if value == "" or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")
    _reject_unsafe_public_string(field_name, value)


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _normalize_positive_count(field_name: str, value: object) -> Decimal:
    normalized = _normalize_count(field_name, value)
    if normalized <= _ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _normalize_count(field_name: str, value: object) -> Decimal:
    normalized = _normalize_nonnegative_decimal(field_name, value)
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{field_name} must be a whole Decimal")
    return normalized


def _normalize_positive_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized <= _ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _normalize_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized < _ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _normalize_ratio(field_name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized < _ZERO or normalized > _ONE:
        raise ValueError(f"{field_name} must be between zero and one")
    return normalized


def _normalize_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return value.quantize(_QUANT, rounding=ROUND_HALF_UP)


def _decimal_from_int(value: int) -> Decimal:
    return Decimal(value).quantize(_QUANT, rounding=ROUND_HALF_UP)


def _require_hard_flags(field_name: str, value: object) -> None:
    if getattr(value, "paper_only", None) is not True:
        raise ValueError(f"{field_name} paper_only must be True")
    if getattr(value, "report_only", None) is not True:
        raise ValueError(f"{field_name} report_only must be True")
    if getattr(value, "readonly", None) is not True:
        raise ValueError(f"{field_name} readonly must be True")


def _require_digest(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if _DIGEST_RE.fullmatch(value) is None:
        raise ValueError(f"{field_name} must be a sha256 hex digest")


def _validate_report_digest(
    report: ResearchSourceScraplingExtractionQualityGateReport,
) -> None:
    _require_exact_type("report", report, ResearchSourceScraplingExtractionQualityGateReport)
    _require_hard_flags("report", report)
    expected_digest = research_source_scrapling_extraction_quality_gate_report_digest(report)
    if report.derived_validation_digest != expected_digest:
        raise ValueError("derived_validation_digest must match report fields")


def _validate_public_payload_digest(payload: Mapping[str, object]) -> None:
    digest = payload.get("derived_validation_digest")
    _require_digest("derived_validation_digest", digest)
    values = dict(payload)
    values.pop("derived_validation_digest", None)
    expected_digest = _report_digest_from_values(values)
    if digest != expected_digest:
        raise ValueError("derived_validation_digest must match payload")


def _report_values_without_digest(
    report: ResearchSourceScraplingExtractionQualityGateReport,
) -> dict[str, object]:
    values = asdict(report)
    values.pop("derived_validation_digest", None)
    return values


def _report_digest_from_values(values: Mapping[str, object]) -> str:
    payload = _json_ready(values)
    _reject_unsafe_public_surface(
        "derived_validation_digest_payload",
        payload,
        allow_json_containers=True,
    )
    canonical_payload = json.dumps(
        payload,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    )
    return sha256(canonical_payload.encode("utf-8")).hexdigest()


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
        raise ValueError("numeric payload values must be Decimal strings")
    if isinstance(value, Mapping):
        ready: dict[str, Any] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            ready[key] = _json_ready(item)
        return ready
    if isinstance(value, (list, tuple)):
        return [_json_ready(item) for item in value]
    raise ValueError("payload value is not JSON serializable")


def _copy_json_object(value: Mapping[str, object]) -> dict[str, Any]:
    copied = _json_ready(value)
    if type(copied) is not dict:
        raise ValueError("payload must be a JSON object")
    return copied


def _reject_unsafe_public_surface(
    label: str,
    value: object,
    path: str = "",
    *,
    allow_json_containers: bool = False,
) -> None:
    current_path = path or label
    if is_dataclass(value) and not isinstance(value, type):
        for field in fields(value):
            _reject_unsafe_public_key(field.name, current_path)
            _reject_unsafe_public_surface(
                label,
                getattr(value, field.name),
                field.name if not path else f"{path}.{field.name}",
                allow_json_containers=allow_json_containers,
            )
        return
    if isinstance(value, Mapping):
        if not allow_json_containers:
            raise ValueError(f"{current_path} must remain constructor-normalized")
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            _reject_unsafe_public_key(key, current_path)
            _reject_unsafe_public_surface(
                label,
                item,
                key if not path else f"{path}.{key}",
                allow_json_containers=True,
            )
        return
    if isinstance(value, (list, tuple)):
        if type(value) is list and not allow_json_containers:
            raise ValueError(f"{current_path} must remain constructor-normalized")
        for index, item in enumerate(value):
            _reject_unsafe_public_surface(
                label,
                item,
                f"{current_path}[{index}]",
                allow_json_containers=allow_json_containers,
            )
        return
    if type(value) is str:
        _reject_unsafe_public_string(current_path, value)
        return
    if (
        value is None
        or type(value) is bool
        or type(value) is Decimal
        or type(value) is datetime
    ):
        return
    raise ValueError(f"{current_path} is not a supported public payload value")


def _reject_unsafe_public_key(key: str, path: str) -> None:
    lowered = key.lower()
    if any(fragment in lowered for fragment in _UNSAFE_PUBLIC_FRAGMENTS):
        raise ValueError(f"{path}.{key} has unsafe public field")


def _reject_unsafe_public_string(field_name: str, value: str) -> None:
    lowered = value.lower()
    if any(fragment in lowered for fragment in _UNSAFE_PUBLIC_FRAGMENTS):
        raise ValueError(f"{field_name} contains unsafe public value")


__all__ = (
    "DEFAULT_RESEARCH_SOURCE_SCRAPLING_EXTRACTION_QUALITY_GATE_CONFIG_VERSION",
    "ResearchSourceScraplingExtractionQualityGateConfig",
    "ResearchSourceScraplingExtractionOutput",
    "ResearchSourceScraplingExtractionQualityGateRow",
    "ResearchSourceScraplingExtractionQualityGateReport",
    "build_research_source_scrapling_extraction_quality_gate_report",
    "research_source_scrapling_extraction_quality_gate_report_digest",
    "research_source_scrapling_extraction_quality_gate_report_payload",
    "validate_research_source_scrapling_extraction_quality_gate_report_digest",
)
