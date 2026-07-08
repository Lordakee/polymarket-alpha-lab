"""Pure report-only aggregate for source parse reliability exceptions."""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable, Mapping
from dataclasses import asdict, dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal, ROUND_HALF_UP
import hashlib
import json
import re
from typing import Any


__all__ = (
    "DEFAULT_RESEARCH_SOURCE_PARSE_RELIABILITY_EXCEPTION_REPORT_CONFIG_VERSION",
    "STATUSES",
    "ResearchSourceParseReliabilityExceptionConfig",
    "ResearchSourceParseReliabilityExceptionInput",
    "ResearchSourceParseReliabilityExceptionReasonCodeCount",
    "ResearchSourceParseReliabilityExceptionReport",
    "ResearchSourceParseReliabilityExceptionRow",
    "build_research_source_parse_reliability_exception_report",
    "research_source_parse_reliability_exception_report_payload",
    "validate_research_source_parse_reliability_exception_report_payload",
)


DEFAULT_RESEARCH_SOURCE_PARSE_RELIABILITY_EXCEPTION_REPORT_CONFIG_VERSION = (
    "research-source-parse-reliability-exception-report-v0"
)
STATUSES = ("pass", "watch", "block")
_ZERO = Decimal("0.000000")
_ONE = Decimal("1.000000")
_QUANT = Decimal("0.000001")
_DIGEST_FIELD = "derived_validation_digest"
_PUBLIC_NAME_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,127}$")
_REASON_CODE_RE = re.compile(r"^[a-z][a-z0-9_]{0,127}$")
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
_UNSAFE_NAME_TERMS = (
    "http",
    "url",
    "raw",
    "text",
    "market",
    "condition",
    "candidate",
    "dsn",
    "ta" + "ble",
    "to" + "ken",
    "pri" + "vate",
    "wal" + "let",
    "au" + "th",
    "or" + "der",
    "tra" + "de",
    "siz" + "ing",
    "recomm" + "endation",
    "credential",
    "secret",
)


class _Missing:
    pass


_MISSING = _Missing()


@dataclass(frozen=True)
class ResearchSourceParseReliabilityExceptionConfig:
    config_version: str = (
        DEFAULT_RESEARCH_SOURCE_PARSE_RELIABILITY_EXCEPTION_REPORT_CONFIG_VERSION
    )
    parse_success_ratio_watch_threshold: Decimal = Decimal("0.900000")
    parse_success_ratio_block_threshold: Decimal = Decimal("0.750000")
    missing_required_field_ratio_watch_threshold: Decimal = Decimal("0.100000")
    missing_required_field_ratio_block_threshold: Decimal = Decimal("0.300000")
    parser_output_age_watch_seconds: Decimal = Decimal("1800.000000")
    parser_output_age_block_seconds: Decimal = Decimal("7200.000000")
    corroboration_ready_ratio_watch_threshold: Decimal = Decimal("0.800000")
    corroboration_ready_ratio_block_threshold: Decimal = Decimal("0.500000")
    retry_backlog_watch_threshold: Decimal = Decimal("5.000000")
    retry_backlog_block_threshold: Decimal = Decimal("20.000000")
    manual_review_urgency_watch_threshold: Decimal = Decimal("0.400000")
    manual_review_urgency_block_threshold: Decimal = Decimal("0.750000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchSourceParseReliabilityExceptionConfig does not support subclassing",
        )

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchSourceParseReliabilityExceptionConfig,
            "config",
        )
        _require_public_name("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_SOURCE_PARSE_RELIABILITY_EXCEPTION_REPORT_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "parse_success_ratio_watch_threshold",
            "parse_success_ratio_block_threshold",
            "missing_required_field_ratio_watch_threshold",
            "missing_required_field_ratio_block_threshold",
            "corroboration_ready_ratio_watch_threshold",
            "corroboration_ready_ratio_block_threshold",
            "manual_review_urgency_watch_threshold",
            "manual_review_urgency_block_threshold",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_probability_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "parser_output_age_watch_seconds",
            "parser_output_age_block_seconds",
            "retry_backlog_watch_threshold",
            "retry_backlog_block_threshold",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        _require_threshold_ceiling_pair(
            "parse_success_ratio_watch_threshold",
            self.parse_success_ratio_watch_threshold,
            "parse_success_ratio_block_threshold",
            self.parse_success_ratio_block_threshold,
        )
        _require_threshold_floor_pair(
            "missing_required_field_ratio_watch_threshold",
            self.missing_required_field_ratio_watch_threshold,
            "missing_required_field_ratio_block_threshold",
            self.missing_required_field_ratio_block_threshold,
        )
        _require_threshold_floor_pair(
            "parser_output_age_watch_seconds",
            self.parser_output_age_watch_seconds,
            "parser_output_age_block_seconds",
            self.parser_output_age_block_seconds,
        )
        _require_threshold_ceiling_pair(
            "corroboration_ready_ratio_watch_threshold",
            self.corroboration_ready_ratio_watch_threshold,
            "corroboration_ready_ratio_block_threshold",
            self.corroboration_ready_ratio_block_threshold,
        )
        _require_threshold_floor_pair(
            "retry_backlog_watch_threshold",
            self.retry_backlog_watch_threshold,
            "retry_backlog_block_threshold",
            self.retry_backlog_block_threshold,
        )
        _require_threshold_floor_pair(
            "manual_review_urgency_watch_threshold",
            self.manual_review_urgency_watch_threshold,
            "manual_review_urgency_block_threshold",
            self.manual_review_urgency_block_threshold,
        )
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class ResearchSourceParseReliabilityExceptionInput:
    parser_family: str
    parsed_count: Decimal
    failed_count: Decimal
    required_field_count: Decimal
    missing_required_field_count: Decimal
    parser_output_generated_at: datetime
    corroborating_source_count: Decimal
    required_corroborating_source_count: Decimal
    retry_backlog_count: Decimal
    manual_review_urgency: Decimal
    reason_codes: tuple[str, ...] = ()
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchSourceParseReliabilityExceptionInput does not support subclassing",
        )

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchSourceParseReliabilityExceptionInput,
            "exception input",
        )
        object.__setattr__(
            self,
            "parser_family",
            _require_parser_family("parser_family", self.parser_family),
        )
        for field_name in (
            "parsed_count",
            "failed_count",
            "required_field_count",
            "missing_required_field_count",
            "corroborating_source_count",
            "required_corroborating_source_count",
            "retry_backlog_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_whole_decimal(field_name, getattr(self, field_name)),
            )
        if self.parsed_count + self.failed_count <= _ZERO:
            raise ValueError("parsed_count plus failed_count must be positive")
        if self.required_field_count <= _ZERO:
            raise ValueError("required_field_count must be positive")
        if self.missing_required_field_count > self.required_field_count:
            raise ValueError(
                "missing_required_field_count must not exceed required_field_count",
            )
        if self.required_corroborating_source_count <= _ZERO:
            raise ValueError("required_corroborating_source_count must be positive")
        if self.corroborating_source_count > self.required_corroborating_source_count:
            raise ValueError(
                "corroborating_source_count must not exceed "
                "required_corroborating_source_count",
            )
        object.__setattr__(
            self,
            "parser_output_generated_at",
            _as_utc("parser_output_generated_at", self.parser_output_generated_at),
        )
        object.__setattr__(
            self,
            "manual_review_urgency",
            _require_probability_decimal(
                "manual_review_urgency",
                self.manual_review_urgency,
            ),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, allow_empty=True),
        )
        _require_hard_flags("exception input", self)


@dataclass(frozen=True)
class ResearchSourceParseReliabilityExceptionRow:
    parser_family: str
    parsed_count: Decimal
    failed_count: Decimal
    required_field_count: Decimal
    missing_required_field_count: Decimal
    parser_output_generated_at: datetime
    parser_output_age_seconds: Decimal
    parse_success_ratio: Decimal
    missing_required_field_ratio: Decimal
    corroborating_source_count: Decimal
    required_corroborating_source_count: Decimal
    corroboration_ready_ratio: Decimal
    retry_backlog_count: Decimal
    manual_review_urgency: Decimal
    status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchSourceParseReliabilityExceptionRow does not support subclassing",
        )

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchSourceParseReliabilityExceptionRow, "row")
        object.__setattr__(
            self,
            "parser_family",
            _require_parser_family("parser_family", self.parser_family),
        )
        for field_name in (
            "parsed_count",
            "failed_count",
            "required_field_count",
            "missing_required_field_count",
            "corroborating_source_count",
            "required_corroborating_source_count",
            "retry_backlog_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_whole_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "parser_output_generated_at",
            _as_utc("parser_output_generated_at", self.parser_output_generated_at),
        )
        object.__setattr__(
            self,
            "parser_output_age_seconds",
            _require_nonnegative_decimal(
                "parser_output_age_seconds",
                self.parser_output_age_seconds,
            ),
        )
        for field_name in (
            "parse_success_ratio",
            "missing_required_field_ratio",
            "corroboration_ready_ratio",
            "manual_review_urgency",
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
        _validate_row_consistency(self)


@dataclass(frozen=True)
class ResearchSourceParseReliabilityExceptionReasonCodeCount:
    reason_code: str
    count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchSourceParseReliabilityExceptionReasonCodeCount does not support "
            "subclassing",
        )

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchSourceParseReliabilityExceptionReasonCodeCount,
            "reason_code_count",
        )
        _require_reason_code("reason_code", self.reason_code)
        object.__setattr__(
            self,
            "count",
            _require_positive_whole_decimal("count", self.count),
        )
        _require_hard_flags("reason_code_count", self)


@dataclass(frozen=True)
class ResearchSourceParseReliabilityExceptionReport:
    generated_at: datetime
    config_version: str
    parser_family_count: Decimal
    input_count: Decimal
    parse_success_ratio: Decimal
    missing_required_field_count: Decimal
    missing_required_field_ratio: Decimal
    stale_parser_output_count: Decimal
    max_parser_output_age_seconds: Decimal
    corroboration_ready_count: Decimal
    corroboration_ready_ratio: Decimal
    retry_backlog_count: Decimal
    manual_review_urgency_peak: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    status: str
    rows: tuple[ResearchSourceParseReliabilityExceptionRow, ...]
    reason_code_counts: tuple[ResearchSourceParseReliabilityExceptionReasonCodeCount, ...]
    reason_codes: tuple[str, ...]
    derived_validation_digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchSourceParseReliabilityExceptionReport does not support subclassing",
        )

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchSourceParseReliabilityExceptionReport, "report")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_name("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_SOURCE_PARSE_RELIABILITY_EXCEPTION_REPORT_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "parser_family_count",
            "input_count",
            "missing_required_field_count",
            "stale_parser_output_count",
            "corroboration_ready_count",
            "retry_backlog_count",
            "pass_count",
            "watch_count",
            "block_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_whole_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in ("max_parser_output_age_seconds",):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "parse_success_ratio",
            "missing_required_field_ratio",
            "corroboration_ready_ratio",
            "manual_review_urgency_peak",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_probability_decimal(field_name, getattr(self, field_name)),
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
        _require_digest(_DIGEST_FIELD, self.derived_validation_digest)
        _require_hard_flags("report", self)
        expected_digest = _report_digest_from_values(_report_values_without_digest(self))
        if self.derived_validation_digest != expected_digest:
            raise ValueError("derived_validation_digest does not match report payload")
        _validate_report_consistency(self)


def build_research_source_parse_reliability_exception_report(
    exception_items: Iterable[object],
    *,
    config: ResearchSourceParseReliabilityExceptionConfig,
    generated_at: datetime,
) -> ResearchSourceParseReliabilityExceptionReport:
    if type(config) is not ResearchSourceParseReliabilityExceptionConfig:
        raise ValueError(
            "config must be a ResearchSourceParseReliabilityExceptionConfig",
        )
    _require_hard_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    normalized_items = _normalize_exception_items(exception_items)
    for item in normalized_items:
        if item.parser_output_generated_at > generated_at_utc:
            raise ValueError(
                "parser_output_generated_at must not be after generated_at",
            )
    rows = tuple(
        _row_from_item(item, config=config, generated_at=generated_at_utc)
        for item in sorted(normalized_items, key=lambda value: value.parser_family)
    )
    reason_codes = _report_reason_codes(rows)
    values: dict[str, object] = {
        "generated_at": generated_at_utc,
        "config_version": config.config_version,
        "parser_family_count": _decimal_count(len(rows)),
        "input_count": _sum_decimal(row.parsed_count + row.failed_count for row in rows),
        "parse_success_ratio": _report_parse_success_ratio(rows),
        "missing_required_field_count": _sum_decimal(
            row.missing_required_field_count for row in rows
        ),
        "missing_required_field_ratio": _report_missing_required_field_ratio(rows),
        "stale_parser_output_count": _decimal_count(_stale_parser_output_count(rows)),
        "max_parser_output_age_seconds": max(
            (row.parser_output_age_seconds for row in rows),
            default=_ZERO,
        ),
        "corroboration_ready_count": _decimal_count(_corroboration_ready_count(rows)),
        "corroboration_ready_ratio": _report_corroboration_ready_ratio(rows),
        "retry_backlog_count": _sum_decimal(row.retry_backlog_count for row in rows),
        "manual_review_urgency_peak": max(
            (row.manual_review_urgency for row in rows),
            default=_ZERO,
        ),
        "pass_count": _decimal_count(_status_count(rows, "pass")),
        "watch_count": _decimal_count(_status_count(rows, "watch")),
        "block_count": _decimal_count(_status_count(rows, "block")),
        "status": _report_status(rows),
        "rows": rows,
        "reason_code_counts": _reason_code_counts(rows, reason_codes),
        "reason_codes": reason_codes,
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    return ResearchSourceParseReliabilityExceptionReport(
        **values,
        derived_validation_digest=_report_digest_from_values(values),
    )


def research_source_parse_reliability_exception_report_payload(
    report: ResearchSourceParseReliabilityExceptionReport,
) -> dict[str, Any]:
    if type(report) is not ResearchSourceParseReliabilityExceptionReport:
        raise ValueError(
            "report must be a ResearchSourceParseReliabilityExceptionReport",
        )
    _require_hard_flags("report", report)
    _validate_report_consistency(report)
    expected_digest = _report_digest_from_values(_report_values_without_digest(report))
    if report.derived_validation_digest != expected_digest:
        raise ValueError("derived_validation_digest does not match report payload")
    payload = _json_ready(asdict(report))
    _reject_public_payload("report payload", payload)
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    return payload


def validate_research_source_parse_reliability_exception_report_payload(
    payload: Mapping[str, object],
) -> bool:
    if not isinstance(payload, Mapping):
        raise ValueError("payload must be a mapping")
    _reject_public_payload("report payload", payload)
    _require_payload_keys(payload)
    digest = payload[_DIGEST_FIELD]
    if type(digest) is not str:
        raise ValueError("derived_validation_digest must be a string")
    _require_digest(_DIGEST_FIELD, digest)
    values_without_digest = {
        key: value for key, value in payload.items() if key != _DIGEST_FIELD
    }
    expected_digest = _report_digest_from_values(values_without_digest)
    if digest != expected_digest:
        raise ValueError("derived_validation_digest does not match report payload")
    return True


def _row_from_item(
    item: ResearchSourceParseReliabilityExceptionInput,
    *,
    config: ResearchSourceParseReliabilityExceptionConfig,
    generated_at: datetime,
) -> ResearchSourceParseReliabilityExceptionRow:
    parser_output_age_seconds = _age_seconds(generated_at, item.parser_output_generated_at)
    parse_success_ratio = _ratio(
        item.parsed_count,
        item.parsed_count + item.failed_count,
    )
    missing_required_field_ratio = _ratio(
        item.missing_required_field_count,
        item.required_field_count,
    )
    corroboration_ready_ratio = _ratio(
        item.corroborating_source_count,
        item.required_corroborating_source_count,
    )
    reason_codes = _row_reason_codes(
        parse_success_ratio=parse_success_ratio,
        missing_required_field_ratio=missing_required_field_ratio,
        parser_output_age_seconds=parser_output_age_seconds,
        corroboration_ready_ratio=corroboration_ready_ratio,
        retry_backlog_count=item.retry_backlog_count,
        manual_review_urgency=item.manual_review_urgency,
        input_reason_codes=item.reason_codes,
        config=config,
    )
    return ResearchSourceParseReliabilityExceptionRow(
        parser_family=item.parser_family,
        parsed_count=item.parsed_count,
        failed_count=item.failed_count,
        required_field_count=item.required_field_count,
        missing_required_field_count=item.missing_required_field_count,
        parser_output_generated_at=item.parser_output_generated_at,
        parser_output_age_seconds=parser_output_age_seconds,
        parse_success_ratio=parse_success_ratio,
        missing_required_field_ratio=missing_required_field_ratio,
        corroborating_source_count=item.corroborating_source_count,
        required_corroborating_source_count=item.required_corroborating_source_count,
        corroboration_ready_ratio=corroboration_ready_ratio,
        retry_backlog_count=item.retry_backlog_count,
        manual_review_urgency=item.manual_review_urgency,
        status=_status_from_reason_codes(reason_codes),
        reason_codes=reason_codes,
    )


def _row_reason_codes(
    *,
    parse_success_ratio: Decimal,
    missing_required_field_ratio: Decimal,
    parser_output_age_seconds: Decimal,
    corroboration_ready_ratio: Decimal,
    retry_backlog_count: Decimal,
    manual_review_urgency: Decimal,
    input_reason_codes: tuple[str, ...],
    config: ResearchSourceParseReliabilityExceptionConfig,
) -> tuple[str, ...]:
    codes: set[str] = set()
    if parse_success_ratio <= config.parse_success_ratio_block_threshold:
        codes.add("parse_success_ratio_block")
    elif parse_success_ratio < config.parse_success_ratio_watch_threshold:
        codes.add("parse_success_ratio_watch")
    if (
        missing_required_field_ratio
        >= config.missing_required_field_ratio_block_threshold
    ):
        codes.add("missing_required_fields_block")
    elif (
        missing_required_field_ratio
        >= config.missing_required_field_ratio_watch_threshold
    ):
        codes.add("missing_required_fields_watch")
    if parser_output_age_seconds >= config.parser_output_age_block_seconds:
        codes.add("stale_parser_output_block")
    elif parser_output_age_seconds >= config.parser_output_age_watch_seconds:
        codes.add("stale_parser_output_watch")
    if corroboration_ready_ratio <= config.corroboration_ready_ratio_block_threshold:
        codes.add("corroboration_not_ready_block")
    elif corroboration_ready_ratio < config.corroboration_ready_ratio_watch_threshold:
        codes.add("corroboration_not_ready_watch")
    if retry_backlog_count >= config.retry_backlog_block_threshold:
        codes.add("retry_backlog_block")
    elif retry_backlog_count >= config.retry_backlog_watch_threshold:
        codes.add("retry_backlog_watch")
    if manual_review_urgency >= config.manual_review_urgency_block_threshold:
        codes.add("manual_review_urgency_block")
    elif manual_review_urgency >= config.manual_review_urgency_watch_threshold:
        codes.add("manual_review_urgency_watch")
    for reason_code in input_reason_codes:
        codes.add(f"input_{reason_code}")
    if not codes:
        return ("source_parse_reliability_exception_pass",)
    status = _status_from_reason_codes(tuple(codes))
    codes.add(f"source_parse_reliability_exception_{status}")
    return tuple(sorted(codes))


def _normalize_exception_items(
    exception_items: Iterable[object],
) -> tuple[ResearchSourceParseReliabilityExceptionInput, ...]:
    if isinstance(exception_items, (str, bytes)):
        raise ValueError("exception_items must be an iterable")
    try:
        values = tuple(exception_items)
    except TypeError as exc:
        raise ValueError("exception_items must be an iterable") from exc
    return tuple(_coerce_exception_item(value) for value in values)


def _coerce_exception_item(
    value: object,
) -> ResearchSourceParseReliabilityExceptionInput:
    if type(value) is ResearchSourceParseReliabilityExceptionInput:
        _require_hard_flags("exception input", value)
        return value
    _require_hard_flags("exception input", value)
    return ResearchSourceParseReliabilityExceptionInput(
        parser_family=_field_value(value, "parser_family"),
        parsed_count=_field_value(value, "parsed_count"),
        failed_count=_field_value(value, "failed_count"),
        required_field_count=_field_value(value, "required_field_count"),
        missing_required_field_count=_field_value(
            value,
            "missing_required_field_count",
        ),
        parser_output_generated_at=_field_value(value, "parser_output_generated_at"),
        corroborating_source_count=_field_value(value, "corroborating_source_count"),
        required_corroborating_source_count=_field_value(
            value,
            "required_corroborating_source_count",
        ),
        retry_backlog_count=_field_value(value, "retry_backlog_count"),
        manual_review_urgency=_field_value(value, "manual_review_urgency"),
        reason_codes=_field_value(value, "reason_codes", default=()),
        paper_only=_field_value(value, "paper_only"),
        report_only=_field_value(value, "report_only"),
        readonly=_field_value(value, "readonly"),
    )


def _report_status(rows: tuple[ResearchSourceParseReliabilityExceptionRow, ...]) -> str:
    if any(row.status == "block" for row in rows):
        return "block"
    if any(row.status == "watch" for row in rows):
        return "watch"
    return "pass"


def _report_reason_codes(
    rows: tuple[ResearchSourceParseReliabilityExceptionRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return ("no_parse_reliability_exceptions",)
    if all(row.status == "pass" for row in rows):
        return ("source_parse_reliability_exception_pass",)
    return tuple(sorted({code for row in rows for code in row.reason_codes}))


def _reason_code_counts(
    rows: tuple[ResearchSourceParseReliabilityExceptionRow, ...],
    reason_codes: tuple[str, ...],
) -> tuple[ResearchSourceParseReliabilityExceptionReasonCodeCount, ...]:
    if not rows:
        return (
            ResearchSourceParseReliabilityExceptionReasonCodeCount(
                reason_code=reason_codes[0],
                count=_ONE,
            ),
        )
    counts: Counter[str] = Counter()
    for row in rows:
        counts.update(row.reason_codes)
    return tuple(
        ResearchSourceParseReliabilityExceptionReasonCodeCount(
            reason_code=reason_code,
            count=_decimal_count(count),
        )
        for reason_code, count in sorted(counts.items(), key=lambda item: item[0])
    )


def _report_parse_success_ratio(
    rows: tuple[ResearchSourceParseReliabilityExceptionRow, ...],
) -> Decimal:
    parsed_count = _sum_decimal(row.parsed_count for row in rows)
    input_count = _sum_decimal(row.parsed_count + row.failed_count for row in rows)
    if input_count == _ZERO:
        return _ONE
    return _ratio(parsed_count, input_count)


def _report_missing_required_field_ratio(
    rows: tuple[ResearchSourceParseReliabilityExceptionRow, ...],
) -> Decimal:
    required_field_count = _sum_decimal(row.required_field_count for row in rows)
    if required_field_count == _ZERO:
        return _ZERO
    return _ratio(
        _sum_decimal(row.missing_required_field_count for row in rows),
        required_field_count,
    )


def _report_corroboration_ready_ratio(
    rows: tuple[ResearchSourceParseReliabilityExceptionRow, ...],
) -> Decimal:
    if not rows:
        return _ONE
    return _ratio(_decimal_count(_corroboration_ready_count(rows)), _decimal_count(len(rows)))


def _corroboration_ready_count(
    rows: tuple[ResearchSourceParseReliabilityExceptionRow, ...],
) -> int:
    return sum(
        1
        for row in rows
        if not any(
            code
            in (
                "corroboration_not_ready_watch",
                "corroboration_not_ready_block",
            )
            for code in row.reason_codes
        )
    )


def _stale_parser_output_count(
    rows: tuple[ResearchSourceParseReliabilityExceptionRow, ...],
) -> int:
    return sum(
        1
        for row in rows
        if any(
            code
            in (
                "stale_parser_output_watch",
                "stale_parser_output_block",
            )
            for code in row.reason_codes
        )
    )


def _status_count(
    rows: tuple[ResearchSourceParseReliabilityExceptionRow, ...],
    status: str,
) -> int:
    return sum(1 for row in rows if row.status == status)


def _normalize_rows(
    rows: tuple[ResearchSourceParseReliabilityExceptionRow, ...],
) -> tuple[ResearchSourceParseReliabilityExceptionRow, ...]:
    if type(rows) is not tuple:
        raise ValueError("rows must be a tuple")
    for row in rows:
        if type(row) is not ResearchSourceParseReliabilityExceptionRow:
            raise ValueError(
                "rows must contain ResearchSourceParseReliabilityExceptionRow values",
            )
        _require_hard_flags("row", row)
    sorted_rows = tuple(sorted(rows, key=lambda row: row.parser_family))
    if rows != sorted_rows:
        raise ValueError("rows must be sorted by parser_family")
    return rows


def _normalize_reason_code_counts(
    counts: tuple[ResearchSourceParseReliabilityExceptionReasonCodeCount, ...],
) -> tuple[ResearchSourceParseReliabilityExceptionReasonCodeCount, ...]:
    if type(counts) is not tuple:
        raise ValueError("reason_code_counts must be a tuple")
    for count in counts:
        if type(count) is not ResearchSourceParseReliabilityExceptionReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "ResearchSourceParseReliabilityExceptionReasonCodeCount values",
            )
        _require_hard_flags("reason_code_count", count)
    sorted_counts = tuple(sorted(counts, key=lambda count: count.reason_code))
    if counts != sorted_counts:
        raise ValueError("reason_code_counts must be sorted by reason_code")
    return counts


def _validate_row_consistency(row: ResearchSourceParseReliabilityExceptionRow) -> None:
    if row.parsed_count + row.failed_count <= _ZERO:
        raise ValueError("parsed_count plus failed_count must be positive")
    if row.required_field_count <= _ZERO:
        raise ValueError("required_field_count must be positive")
    if row.missing_required_field_count > row.required_field_count:
        raise ValueError(
            "missing_required_field_count must not exceed required_field_count",
        )
    if row.required_corroborating_source_count <= _ZERO:
        raise ValueError("required_corroborating_source_count must be positive")
    if row.corroborating_source_count > row.required_corroborating_source_count:
        raise ValueError(
            "corroborating_source_count must not exceed "
            "required_corroborating_source_count",
        )
    if row.parse_success_ratio != _ratio(
        row.parsed_count,
        row.parsed_count + row.failed_count,
    ):
        raise ValueError("parse_success_ratio must match parse counts")
    if row.missing_required_field_ratio != _ratio(
        row.missing_required_field_count,
        row.required_field_count,
    ):
        raise ValueError("missing_required_field_ratio must match field counts")
    if row.corroboration_ready_ratio != _ratio(
        row.corroborating_source_count,
        row.required_corroborating_source_count,
    ):
        raise ValueError("corroboration_ready_ratio must match source counts")
    expected_status = _status_from_reason_codes(row.reason_codes)
    if row.status != expected_status:
        raise ValueError("status must match reason_codes")
    if f"source_parse_reliability_exception_{row.status}" not in row.reason_codes:
        raise ValueError("reason_codes must include row status")


def _validate_report_consistency(
    report: ResearchSourceParseReliabilityExceptionReport,
) -> None:
    if report.parser_family_count != _decimal_count(len(report.rows)):
        raise ValueError("parser_family_count must match rows")
    if report.input_count != _sum_decimal(
        row.parsed_count + row.failed_count for row in report.rows
    ):
        raise ValueError("input_count must match rows")
    if report.parse_success_ratio != _report_parse_success_ratio(report.rows):
        raise ValueError("parse_success_ratio must match rows")
    if report.missing_required_field_count != _sum_decimal(
        row.missing_required_field_count for row in report.rows
    ):
        raise ValueError("missing_required_field_count must match rows")
    if (
        report.missing_required_field_ratio
        != _report_missing_required_field_ratio(report.rows)
    ):
        raise ValueError("missing_required_field_ratio must match rows")
    if report.stale_parser_output_count != _decimal_count(
        _stale_parser_output_count(report.rows),
    ):
        raise ValueError("stale_parser_output_count must match rows")
    expected_max_age = max(
        (row.parser_output_age_seconds for row in report.rows),
        default=_ZERO,
    )
    if report.max_parser_output_age_seconds != expected_max_age:
        raise ValueError("max_parser_output_age_seconds must match rows")
    if report.corroboration_ready_count != _decimal_count(
        _corroboration_ready_count(report.rows),
    ):
        raise ValueError("corroboration_ready_count must match rows")
    if report.corroboration_ready_ratio != _report_corroboration_ready_ratio(report.rows):
        raise ValueError("corroboration_ready_ratio must match rows")
    if report.retry_backlog_count != _sum_decimal(
        row.retry_backlog_count for row in report.rows
    ):
        raise ValueError("retry_backlog_count must match rows")
    expected_urgency_peak = max(
        (row.manual_review_urgency for row in report.rows),
        default=_ZERO,
    )
    if report.manual_review_urgency_peak != expected_urgency_peak:
        raise ValueError("manual_review_urgency_peak must match rows")
    if report.pass_count != _decimal_count(_status_count(report.rows, "pass")):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _decimal_count(_status_count(report.rows, "watch")):
        raise ValueError("watch_count must match rows")
    if report.block_count != _decimal_count(_status_count(report.rows, "block")):
        raise ValueError("block_count must match rows")
    if report.status != _report_status(report.rows):
        raise ValueError("status must match rows")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")
    expected_counts = _reason_code_counts(report.rows, report.reason_codes)
    if report.reason_code_counts != expected_counts:
        raise ValueError("reason_code_counts must match rows")


def _status_from_reason_codes(reason_codes: tuple[str, ...]) -> str:
    if any(code.endswith("_block") for code in reason_codes):
        return "block"
    if any(code.endswith("_watch") for code in reason_codes):
        return "watch"
    if reason_codes == ("source_parse_reliability_exception_pass",):
        return "pass"
    return "watch"


def _field_value(value: object, field_name: str, default: object = _MISSING) -> object:
    if isinstance(value, Mapping) and field_name in value:
        return value[field_name]
    if hasattr(value, field_name):
        return getattr(value, field_name)
    if default is not _MISSING:
        return default
    raise ValueError(f"{field_name} is required")


def _require_exact_type(value: object, expected_type: type[object], label: str) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{label} must be exactly {expected_type.__name__}")


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if getattr(value, field_name, None) is not True:
            raise ValueError(f"{field_name} must be True for {label}")


def _require_status(field_name: str, value: object) -> str:
    if type(value) is not str or value not in STATUSES:
        raise ValueError(f"{field_name} must be one of {STATUSES}")
    return value


def _require_public_name(field_name: str, value: object) -> str:
    if type(value) is not str or not _PUBLIC_NAME_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a public name")
    _reject_public_string(field_name, value)
    return value


def _require_parser_family(field_name: str, value: object) -> str:
    return _require_public_name(field_name, value)


def _require_reason_code(field_name: str, value: object) -> str:
    if type(value) is not str or not _REASON_CODE_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a reason code")
    _reject_public_string(field_name, value)
    return value


def _normalize_reason_codes(
    field_name: str,
    reason_codes: tuple[str, ...],
    *,
    allow_empty: bool,
) -> tuple[str, ...]:
    if type(reason_codes) is not tuple:
        raise ValueError(f"{field_name} must be a tuple")
    if not allow_empty and not reason_codes:
        raise ValueError(f"{field_name} must not be empty")
    normalized: list[str] = []
    for reason_code in reason_codes:
        _require_reason_code(field_name, reason_code)
        if reason_code not in normalized:
            normalized.append(reason_code)
    return tuple(sorted(normalized))


def _require_digest(field_name: str, value: object) -> str:
    if type(value) is not str or not _SHA256_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a lowercase sha256 digest")
    return value


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    normalized = _quantize(value)
    if normalized != value:
        raise ValueError(f"{field_name} must use six decimal places")
    return normalized


def _require_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value < _ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return decimal_value


def _require_nonnegative_whole_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_nonnegative_decimal(field_name, value)
    if decimal_value != decimal_value.to_integral_value():
        raise ValueError(f"{field_name} must be a whole Decimal")
    return decimal_value


def _require_positive_whole_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_nonnegative_whole_decimal(field_name, value)
    if decimal_value <= _ZERO:
        raise ValueError(f"{field_name} must be positive")
    return decimal_value


def _require_probability_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_nonnegative_decimal(field_name, value)
    if decimal_value > _ONE:
        raise ValueError(f"{field_name} must be between 0.000000 and 1.000000")
    return decimal_value


def _require_threshold_floor_pair(
    watch_name: str,
    watch_value: Decimal,
    block_name: str,
    block_value: Decimal,
) -> None:
    if block_value < watch_value:
        raise ValueError(f"{block_name} must be >= {watch_name}")


def _require_threshold_ceiling_pair(
    watch_name: str,
    watch_value: Decimal,
    block_name: str,
    block_value: Decimal,
) -> None:
    if block_value > watch_value:
        raise ValueError(f"{block_name} must be <= {watch_name}")


def _decimal_count(value: int) -> Decimal:
    if value < 0:
        raise ValueError("count must be nonnegative")
    return Decimal(value).quantize(_QUANT)


def _sum_decimal(values: Iterable[Decimal]) -> Decimal:
    return _quantize(sum(values, _ZERO))


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator <= _ZERO:
        raise ValueError("ratio denominator must be positive")
    return _quantize(numerator / denominator)


def _age_seconds(generated_at: datetime, observed_at: datetime) -> Decimal:
    delta = generated_at - observed_at
    seconds = Decimal(delta.days * 86400 + delta.seconds)
    microseconds = Decimal(delta.microseconds) / Decimal("1000000")
    return _quantize(seconds + microseconds)


def _quantize(value: Decimal) -> Decimal:
    return value.quantize(_QUANT, rounding=ROUND_HALF_UP)


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is not UTC:
        raise ValueError(f"{field_name} must be timezone-aware UTC")
    return value


def _report_values_without_digest(
    report: ResearchSourceParseReliabilityExceptionReport,
) -> dict[str, object]:
    values = asdict(report)
    values.pop(_DIGEST_FIELD, None)
    return values


def _report_digest_from_values(values: Mapping[str, object]) -> str:
    payload = _json_ready(values)
    _reject_public_payload("derived_validation_digest payload", payload)
    canonical = json.dumps(
        payload,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


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


def _reject_public_payload(label: str, value: object) -> None:
    _reject_public_payload_at(label, value, label)


def _reject_public_payload_at(label: str, value: object, path: str) -> None:
    if is_dataclass(value) and not isinstance(value, type):
        for field in fields(value):
            _reject_public_key(path, field.name)
            _reject_public_payload_at(label, getattr(value, field.name), field.name)
        return
    if isinstance(value, Mapping):
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            _reject_public_key(path, key)
            _reject_public_payload_at(label, item, key)
        return
    if isinstance(value, (list, tuple)):
        for index, item in enumerate(value):
            _reject_public_payload_at(label, item, f"{path}[{index}]")
        return
    if type(value) is str:
        _reject_public_string(path, value)
        return
    if (
        value is None
        or type(value) is bool
        or type(value) is Decimal
        or type(value) is datetime
    ):
        return
    raise ValueError(f"{label} contains unsupported public payload value")


def _reject_public_key(path: str, key: str) -> None:
    lowered = key.lower()
    if any(term in lowered for term in _UNSAFE_NAME_TERMS):
        raise ValueError(f"{path}.{key} has unsafe public field")


def _reject_public_string(field_name: str, value: str) -> None:
    lowered = value.lower()
    if "://" in lowered or "?" in lowered or "@" in lowered:
        raise ValueError(f"{field_name} has unsafe public value")
    if any(term in lowered for term in _UNSAFE_NAME_TERMS):
        raise ValueError(f"{field_name} has unsafe public value")


def _require_payload_keys(payload: Mapping[str, object]) -> None:
    expected_keys = {field.name for field in fields(ResearchSourceParseReliabilityExceptionReport)}
    actual_keys = set(payload.keys())
    if actual_keys != expected_keys:
        raise ValueError("payload keys must match report fields")
