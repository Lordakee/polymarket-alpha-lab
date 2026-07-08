"""Pure report-only aggregate for resolution rule-change exceptions."""

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
    "DEFAULT_RESEARCH_RESOLUTION_RULE_CHANGE_EXCEPTION_REPORT_CONFIG_VERSION",
    "STATUSES",
    "ResearchResolutionRuleChangeExceptionConfig",
    "ResearchResolutionRuleChangeExceptionInput",
    "ResearchResolutionRuleChangeExceptionReasonCodeCount",
    "ResearchResolutionRuleChangeExceptionReport",
    "ResearchResolutionRuleChangeExceptionRow",
    "build_research_resolution_rule_change_exception_report",
    "research_resolution_rule_change_exception_report_payload",
    "validate_research_resolution_rule_change_exception_report_payload",
)


DEFAULT_RESEARCH_RESOLUTION_RULE_CHANGE_EXCEPTION_REPORT_CONFIG_VERSION = (
    "research-resolution-rule-change-exception-report-v0"
)
STATUSES = ("pass", "watch", "block")
_STATUSES = frozenset(STATUSES)
_ZERO = Decimal("0.000000")
_ONE = Decimal("1.000000")
_QUANT = Decimal("0.000001")
_DIGEST_FIELD = "derived_validation_digest"
_PUBLIC_NAME_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,127}$")
_REASON_CODE_RE = re.compile(r"^[a-z][a-z0-9_]{0,127}$")
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
_UNSAFE_GROUP_TERMS = (
    "http",
    "url",
    "market",
    "condition",
    "slug",
    "question",
    "source",
    "ref",
    "raw",
    "text",
)
_UNSAFE_PUBLIC_TEXT = (
    "http://",
    "https://",
    "source_url",
    "source_text",
    "source_ref",
    "source_reference",
    "source_identifier",
    "raw_source",
    "raw_text",
    "raw_url",
    "market_slug",
    "market_id",
    "condition_id",
    "question",
)
_UNSAFE_ACTION_TEXT = (
    "wal" + "let",
    "au" + "th",
    "or" + "der",
    "tra" + "de",
    "li" + "ve",
    "recomm" + "endation",
    "siz" + "ing",
    "pri" + "vate",
    "credential",
    "secret",
    "token",
)


class _Missing:
    pass


_MISSING = _Missing()


@dataclass(frozen=True)
class ResearchResolutionRuleChangeExceptionConfig:
    config_version: str = (
        DEFAULT_RESEARCH_RESOLUTION_RULE_CHANGE_EXCEPTION_REPORT_CONFIG_VERSION
    )
    rule_version_drift_watch_threshold: Decimal = Decimal("1.000000")
    rule_version_drift_block_threshold: Decimal = Decimal("3.000000")
    official_source_freshness_watch_threshold: Decimal = Decimal("0.800000")
    official_source_freshness_block_threshold: Decimal = Decimal("0.500000")
    unresolved_ambiguity_watch_threshold: Decimal = Decimal("1.000000")
    unresolved_ambiguity_block_threshold: Decimal = Decimal("3.000000")
    manual_review_urgency_watch_threshold: Decimal = Decimal("0.400000")
    manual_review_urgency_block_threshold: Decimal = Decimal("0.750000")
    impacted_packet_watch_threshold: Decimal = Decimal("5.000000")
    impacted_packet_block_threshold: Decimal = Decimal("20.000000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchResolutionRuleChangeExceptionConfig does not support subclassing",
        )

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchResolutionRuleChangeExceptionConfig,
            "config",
        )
        _require_public_name("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_RESOLUTION_RULE_CHANGE_EXCEPTION_REPORT_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "rule_version_drift_watch_threshold",
            "rule_version_drift_block_threshold",
            "unresolved_ambiguity_watch_threshold",
            "unresolved_ambiguity_block_threshold",
            "impacted_packet_watch_threshold",
            "impacted_packet_block_threshold",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "official_source_freshness_watch_threshold",
            "official_source_freshness_block_threshold",
            "manual_review_urgency_watch_threshold",
            "manual_review_urgency_block_threshold",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_probability_decimal(field_name, getattr(self, field_name)),
            )
        _require_threshold_floor_pair(
            "rule_version_drift_watch_threshold",
            self.rule_version_drift_watch_threshold,
            "rule_version_drift_block_threshold",
            self.rule_version_drift_block_threshold,
        )
        _require_threshold_floor_pair(
            "unresolved_ambiguity_watch_threshold",
            self.unresolved_ambiguity_watch_threshold,
            "unresolved_ambiguity_block_threshold",
            self.unresolved_ambiguity_block_threshold,
        )
        _require_threshold_floor_pair(
            "manual_review_urgency_watch_threshold",
            self.manual_review_urgency_watch_threshold,
            "manual_review_urgency_block_threshold",
            self.manual_review_urgency_block_threshold,
        )
        _require_threshold_floor_pair(
            "impacted_packet_watch_threshold",
            self.impacted_packet_watch_threshold,
            "impacted_packet_block_threshold",
            self.impacted_packet_block_threshold,
        )
        if (
            self.official_source_freshness_block_threshold
            > self.official_source_freshness_watch_threshold
        ):
            raise ValueError(
                "official_source_freshness_block_threshold must be <= "
                "official_source_freshness_watch_threshold",
            )
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class ResearchResolutionRuleChangeExceptionInput:
    exception_group: str
    baseline_rule_version: Decimal
    observed_rule_version: Decimal
    official_source_freshness: Decimal
    unresolved_ambiguity_count: Decimal
    impacted_packet_count: Decimal
    manual_review_urgency: Decimal
    reason_codes: tuple[str, ...] = ()
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchResolutionRuleChangeExceptionInput does not support subclassing",
        )

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchResolutionRuleChangeExceptionInput,
            "exception input",
        )
        object.__setattr__(
            self,
            "exception_group",
            _require_exception_group("exception_group", self.exception_group),
        )
        for field_name in (
            "baseline_rule_version",
            "observed_rule_version",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "unresolved_ambiguity_count",
            "impacted_packet_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_whole_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in ("official_source_freshness", "manual_review_urgency"):
            object.__setattr__(
                self,
                field_name,
                _require_probability_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, allow_empty=True),
        )
        _require_hard_flags("exception input", self)


@dataclass(frozen=True)
class ResearchResolutionRuleChangeExceptionRow:
    exception_group: str
    rule_version_drift: Decimal
    official_source_freshness: Decimal
    unresolved_ambiguity_count: Decimal
    impacted_packet_count: Decimal
    manual_review_urgency: Decimal
    status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchResolutionRuleChangeExceptionRow does not support subclassing",
        )

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchResolutionRuleChangeExceptionRow, "row")
        object.__setattr__(
            self,
            "exception_group",
            _require_exception_group("exception_group", self.exception_group),
        )
        object.__setattr__(
            self,
            "rule_version_drift",
            _require_nonnegative_decimal(
                "rule_version_drift",
                self.rule_version_drift,
            ),
        )
        for field_name in (
            "unresolved_ambiguity_count",
            "impacted_packet_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_whole_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in ("official_source_freshness", "manual_review_urgency"):
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
class ResearchResolutionRuleChangeExceptionReasonCodeCount:
    reason_code: str
    count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchResolutionRuleChangeExceptionReasonCodeCount does not support "
            "subclassing",
        )

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchResolutionRuleChangeExceptionReasonCodeCount,
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
class ResearchResolutionRuleChangeExceptionReport:
    generated_at: datetime
    config_version: str
    exception_group_count: Decimal
    impacted_packet_count: Decimal
    rule_version_drift_exception_count: Decimal
    stale_official_source_count: Decimal
    unresolved_ambiguity_count: Decimal
    manual_review_urgency_peak: Decimal
    average_official_source_freshness: Decimal | None
    max_rule_version_drift: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    status: str
    rows: tuple[ResearchResolutionRuleChangeExceptionRow, ...]
    reason_code_counts: tuple[ResearchResolutionRuleChangeExceptionReasonCodeCount, ...]
    reason_codes: tuple[str, ...]
    derived_validation_digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchResolutionRuleChangeExceptionReport does not support subclassing",
        )

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchResolutionRuleChangeExceptionReport, "report")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_name("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_RESOLUTION_RULE_CHANGE_EXCEPTION_REPORT_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "exception_group_count",
            "impacted_packet_count",
            "rule_version_drift_exception_count",
            "stale_official_source_count",
            "unresolved_ambiguity_count",
            "pass_count",
            "watch_count",
            "block_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_whole_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in ("manual_review_urgency_peak", "max_rule_version_drift"):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "average_official_source_freshness",
            _require_optional_probability_decimal(
                "average_official_source_freshness",
                self.average_official_source_freshness,
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
        _require_digest(_DIGEST_FIELD, self.derived_validation_digest)
        _require_hard_flags("report", self)
        expected_digest = _report_digest_from_values(_report_values_without_digest(self))
        if self.derived_validation_digest != expected_digest:
            raise ValueError("derived_validation_digest does not match report payload")
        _validate_report_consistency(self)


def build_research_resolution_rule_change_exception_report(
    exception_items: Iterable[object],
    *,
    config: ResearchResolutionRuleChangeExceptionConfig,
    generated_at: datetime,
) -> ResearchResolutionRuleChangeExceptionReport:
    if type(config) is not ResearchResolutionRuleChangeExceptionConfig:
        raise ValueError(
            "config must be a ResearchResolutionRuleChangeExceptionConfig",
        )
    _require_hard_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    normalized_items = _normalize_exception_items(exception_items)
    rows = tuple(
        _row_from_item(item, config=config)
        for item in sorted(normalized_items, key=lambda value: value.exception_group)
    )
    reason_codes = _report_reason_codes(rows)
    values: dict[str, object] = {
        "generated_at": generated_at_utc,
        "config_version": config.config_version,
        "exception_group_count": _decimal_count(len(rows)),
        "impacted_packet_count": _sum_decimal(row.impacted_packet_count for row in rows),
        "rule_version_drift_exception_count": _decimal_count(
            sum(1 for row in rows if row.rule_version_drift > _ZERO),
        ),
        "stale_official_source_count": _decimal_count(
            sum(
                1
                for row in rows
                if row.official_source_freshness
                < config.official_source_freshness_watch_threshold
            ),
        ),
        "unresolved_ambiguity_count": _sum_decimal(
            row.unresolved_ambiguity_count for row in rows
        ),
        "manual_review_urgency_peak": max(
            (row.manual_review_urgency for row in rows),
            default=_ZERO,
        ),
        "average_official_source_freshness": _average_official_source_freshness(rows),
        "max_rule_version_drift": max(
            (row.rule_version_drift for row in rows),
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
    return ResearchResolutionRuleChangeExceptionReport(
        **values,
        derived_validation_digest=_report_digest_from_values(values),
    )


def research_resolution_rule_change_exception_report_payload(
    report: ResearchResolutionRuleChangeExceptionReport,
) -> dict[str, Any]:
    if type(report) is not ResearchResolutionRuleChangeExceptionReport:
        raise ValueError(
            "report must be a ResearchResolutionRuleChangeExceptionReport",
        )
    _require_hard_flags("report", report)
    _validate_report_consistency(report)
    payload = _json_ready(asdict(report))
    _reject_public_payload("report payload", payload)
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    return payload


def validate_research_resolution_rule_change_exception_report_payload(
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
    item: ResearchResolutionRuleChangeExceptionInput,
    *,
    config: ResearchResolutionRuleChangeExceptionConfig,
) -> ResearchResolutionRuleChangeExceptionRow:
    rule_version_drift = _quantize(
        abs(item.observed_rule_version - item.baseline_rule_version),
    )
    reason_codes = _row_reason_codes(
        rule_version_drift=rule_version_drift,
        official_source_freshness=item.official_source_freshness,
        unresolved_ambiguity_count=item.unresolved_ambiguity_count,
        impacted_packet_count=item.impacted_packet_count,
        manual_review_urgency=item.manual_review_urgency,
        input_reason_codes=item.reason_codes,
        config=config,
    )
    return ResearchResolutionRuleChangeExceptionRow(
        exception_group=item.exception_group,
        rule_version_drift=rule_version_drift,
        official_source_freshness=item.official_source_freshness,
        unresolved_ambiguity_count=item.unresolved_ambiguity_count,
        impacted_packet_count=item.impacted_packet_count,
        manual_review_urgency=item.manual_review_urgency,
        status=_status_from_reason_codes(reason_codes),
        reason_codes=reason_codes,
    )


def _row_reason_codes(
    *,
    rule_version_drift: Decimal,
    official_source_freshness: Decimal,
    unresolved_ambiguity_count: Decimal,
    impacted_packet_count: Decimal,
    manual_review_urgency: Decimal,
    input_reason_codes: tuple[str, ...],
    config: ResearchResolutionRuleChangeExceptionConfig,
) -> tuple[str, ...]:
    codes: set[str] = set()
    if rule_version_drift >= config.rule_version_drift_block_threshold:
        codes.add("rule_version_drift_block")
    elif rule_version_drift >= config.rule_version_drift_watch_threshold:
        codes.add("rule_version_drift_watch")
    if official_source_freshness <= config.official_source_freshness_block_threshold:
        codes.add("official_source_freshness_block")
    elif official_source_freshness < config.official_source_freshness_watch_threshold:
        codes.add("official_source_freshness_watch")
    if unresolved_ambiguity_count >= config.unresolved_ambiguity_block_threshold:
        codes.add("unresolved_ambiguity_block")
    elif unresolved_ambiguity_count >= config.unresolved_ambiguity_watch_threshold:
        codes.add("unresolved_ambiguity_watch")
    if impacted_packet_count >= config.impacted_packet_block_threshold:
        codes.add("impacted_packet_count_block")
    elif impacted_packet_count >= config.impacted_packet_watch_threshold:
        codes.add("impacted_packet_count_watch")
    if manual_review_urgency >= config.manual_review_urgency_block_threshold:
        codes.add("manual_review_urgency_block")
    elif manual_review_urgency >= config.manual_review_urgency_watch_threshold:
        codes.add("manual_review_urgency_watch")
    for reason_code in input_reason_codes:
        codes.add(f"input_{reason_code}")
    if not codes:
        return ("resolution_rule_change_exception_pass",)
    status = _status_from_reason_codes(tuple(codes))
    codes.add(f"resolution_rule_change_exception_{status}")
    return tuple(sorted(codes))


def _normalize_exception_items(
    exception_items: Iterable[object],
) -> tuple[ResearchResolutionRuleChangeExceptionInput, ...]:
    if isinstance(exception_items, (str, bytes)):
        raise ValueError("exception_items must be an iterable")
    try:
        values = tuple(exception_items)
    except TypeError as exc:
        raise ValueError("exception_items must be an iterable") from exc
    return tuple(_coerce_exception_item(value) for value in values)


def _coerce_exception_item(
    value: object,
) -> ResearchResolutionRuleChangeExceptionInput:
    if type(value) is ResearchResolutionRuleChangeExceptionInput:
        _require_hard_flags("exception input", value)
        return value
    _require_hard_flags("exception input", value)
    return ResearchResolutionRuleChangeExceptionInput(
        exception_group=_field_value(value, "exception_group"),
        baseline_rule_version=_field_value(value, "baseline_rule_version"),
        observed_rule_version=_field_value(value, "observed_rule_version"),
        official_source_freshness=_field_value(value, "official_source_freshness"),
        unresolved_ambiguity_count=_field_value(value, "unresolved_ambiguity_count"),
        impacted_packet_count=_field_value(value, "impacted_packet_count"),
        manual_review_urgency=_field_value(value, "manual_review_urgency"),
        reason_codes=_field_value(value, "reason_codes", default=()),
        paper_only=_field_value(value, "paper_only"),
        report_only=_field_value(value, "report_only"),
        readonly=_field_value(value, "readonly"),
    )


def _report_status(
    rows: tuple[ResearchResolutionRuleChangeExceptionRow, ...],
) -> str:
    if any(row.status == "block" for row in rows):
        return "block"
    if any(row.status == "watch" for row in rows):
        return "watch"
    return "pass"


def _report_reason_codes(
    rows: tuple[ResearchResolutionRuleChangeExceptionRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return ("no_rule_change_exceptions",)
    if all(row.status == "pass" for row in rows):
        return ("resolution_rule_change_exception_pass",)
    return tuple(sorted({code for row in rows for code in row.reason_codes}))


def _reason_code_counts(
    rows: tuple[ResearchResolutionRuleChangeExceptionRow, ...],
    reason_codes: tuple[str, ...],
) -> tuple[ResearchResolutionRuleChangeExceptionReasonCodeCount, ...]:
    if not rows:
        return (
            ResearchResolutionRuleChangeExceptionReasonCodeCount(
                reason_code=reason_codes[0],
                count=_ONE,
            ),
        )
    counts: Counter[str] = Counter()
    for row in rows:
        counts.update(row.reason_codes)
    return tuple(
        ResearchResolutionRuleChangeExceptionReasonCodeCount(
            reason_code=reason_code,
            count=_decimal_count(count),
        )
        for reason_code, count in sorted(counts.items(), key=lambda item: item[0])
    )


def _average_official_source_freshness(
    rows: tuple[ResearchResolutionRuleChangeExceptionRow, ...],
) -> Decimal | None:
    if not rows:
        return None
    return _quantize(
        sum((row.official_source_freshness for row in rows), _ZERO) / Decimal(len(rows)),
    )


def _status_count(
    rows: tuple[ResearchResolutionRuleChangeExceptionRow, ...],
    status: str,
) -> int:
    return sum(1 for row in rows if row.status == status)


def _normalize_rows(
    rows: tuple[ResearchResolutionRuleChangeExceptionRow, ...],
) -> tuple[ResearchResolutionRuleChangeExceptionRow, ...]:
    if type(rows) is not tuple:
        raise ValueError("rows must be a tuple")
    for row in rows:
        if type(row) is not ResearchResolutionRuleChangeExceptionRow:
            raise ValueError(
                "rows must contain ResearchResolutionRuleChangeExceptionRow values",
            )
        _require_hard_flags("row", row)
    sorted_rows = tuple(sorted(rows, key=lambda row: row.exception_group))
    if rows != sorted_rows:
        raise ValueError("rows must be sorted by exception_group")
    return rows


def _normalize_reason_code_counts(
    counts: tuple[ResearchResolutionRuleChangeExceptionReasonCodeCount, ...],
) -> tuple[ResearchResolutionRuleChangeExceptionReasonCodeCount, ...]:
    if type(counts) is not tuple:
        raise ValueError("reason_code_counts must be a tuple")
    for count in counts:
        if type(count) is not ResearchResolutionRuleChangeExceptionReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "ResearchResolutionRuleChangeExceptionReasonCodeCount values",
            )
        _require_hard_flags("reason_code_count", count)
    sorted_counts = tuple(sorted(counts, key=lambda count: count.reason_code))
    if counts != sorted_counts:
        raise ValueError("reason_code_counts must be sorted by reason_code")
    return counts


def _validate_row_consistency(row: ResearchResolutionRuleChangeExceptionRow) -> None:
    if not row.reason_codes:
        raise ValueError("reason_codes must be nonempty")
    expected_status = _status_from_reason_codes(row.reason_codes)
    if row.status != expected_status:
        raise ValueError("status must match reason_codes")
    if f"resolution_rule_change_exception_{row.status}" not in row.reason_codes:
        raise ValueError("reason_codes must include row status")


def _validate_report_consistency(
    report: ResearchResolutionRuleChangeExceptionReport,
) -> None:
    if report.exception_group_count != _decimal_count(len(report.rows)):
        raise ValueError("exception_group_count must match rows")
    if report.impacted_packet_count != _sum_decimal(
        row.impacted_packet_count for row in report.rows
    ):
        raise ValueError("impacted_packet_count must match rows")
    drift_count = sum(1 for row in report.rows if row.rule_version_drift > _ZERO)
    if report.rule_version_drift_exception_count != _decimal_count(drift_count):
        raise ValueError("rule_version_drift_exception_count must match rows")
    stale_count = sum(
        any(
            code
            in (
                "official_source_freshness_watch",
                "official_source_freshness_block",
            )
            for code in row.reason_codes
        )
        for row in report.rows
    )
    if report.stale_official_source_count != _decimal_count(stale_count):
        raise ValueError("stale_official_source_count must match rows")
    if report.unresolved_ambiguity_count != _sum_decimal(
        row.unresolved_ambiguity_count for row in report.rows
    ):
        raise ValueError("unresolved_ambiguity_count must match rows")
    expected_urgency_peak = max(
        (row.manual_review_urgency for row in report.rows),
        default=_ZERO,
    )
    if report.manual_review_urgency_peak != expected_urgency_peak:
        raise ValueError("manual_review_urgency_peak must match rows")
    if report.average_official_source_freshness != _average_official_source_freshness(
        report.rows,
    ):
        raise ValueError("average_official_source_freshness must match rows")
    expected_max_drift = max((row.rule_version_drift for row in report.rows), default=_ZERO)
    if report.max_rule_version_drift != expected_max_drift:
        raise ValueError("max_rule_version_drift must match rows")
    if report.pass_count != _decimal_count(_status_count(report.rows, "pass")):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _decimal_count(_status_count(report.rows, "watch")):
        raise ValueError("watch_count must match rows")
    if report.block_count != _decimal_count(_status_count(report.rows, "block")):
        raise ValueError("block_count must match rows")
    if report.status != _report_status(report.rows):
        raise ValueError("status must match rows")
    expected_reason_codes = _report_reason_codes(report.rows)
    if report.reason_codes != expected_reason_codes:
        raise ValueError("reason_codes must match rows")
    if report.reason_code_counts != _reason_code_counts(report.rows, report.reason_codes):
        raise ValueError("reason_code_counts must match rows")


def _status_from_reason_codes(reason_codes: tuple[str, ...]) -> str:
    if any(code.endswith("_block") for code in reason_codes):
        return "block"
    if any(code.endswith("_watch") for code in reason_codes):
        return "watch"
    return "pass"


def _report_values_without_digest(
    report: ResearchResolutionRuleChangeExceptionReport,
) -> dict[str, object]:
    return {
        field.name: getattr(report, field.name)
        for field in fields(report)
        if field.name != _DIGEST_FIELD
    }


def _report_digest_from_values(values: Mapping[str, object]) -> str:
    ready = _json_ready(dict(values))
    _reject_public_payload("report digest payload", ready)
    encoded = json.dumps(ready, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def _json_ready(value: Any) -> Any:
    if value is None:
        return None
    if is_dataclass(value) and not isinstance(value, type):
        return _json_ready(asdict(value))
    if type(value) is Decimal:
        if not value.is_finite():
            raise ValueError("JSON Decimal value must be finite")
        return str(value)
    if isinstance(value, Decimal):
        raise ValueError("JSON value must use exact Decimal values")
    if type(value) is datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("JSON datetime value must be timezone-aware")
        return value.astimezone(UTC).isoformat()
    if isinstance(value, datetime):
        raise ValueError("JSON datetime value must be an exact datetime")
    if type(value) is bool:
        return value
    if type(value) is int:
        raise ValueError("JSON numeric value must be Decimal-derived")
    if type(value) is float:
        raise ValueError("JSON value must not be a float")
    if type(value) is str:
        _reject_text_value("JSON string value", value)
        return value
    if isinstance(value, Mapping):
        ready: dict[str, Any] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            _reject_text_value("JSON object key", key)
            ready[key] = _json_ready(item)
        return ready
    if isinstance(value, (list, tuple)):
        return [_json_ready(item) for item in value]
    raise ValueError("value is not JSON serializable")


def _field_value(value: object, name: str, default: object = _MISSING) -> object:
    if is_dataclass(value) and not isinstance(value, type):
        if any(field.name == name for field in fields(value)):
            return getattr(value, name)
    elif isinstance(value, Mapping):
        if name in value:
            return value[name]
    elif hasattr(value, name):
        return getattr(value, name)
    if default is not _MISSING:
        return default
    raise ValueError(f"{name} is required")


def _as_utc(name: str, value: datetime) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_exact_type(value: object, expected_type: type[object], name: str) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{name} must be exactly {expected_type.__name__}")


def _require_threshold_floor_pair(
    watch_name: str,
    watch_value: Decimal,
    block_name: str,
    block_value: Decimal,
) -> None:
    if block_value < watch_value:
        raise ValueError(f"{block_name} must be >= {watch_name}")


def _require_public_name(name: str, value: str) -> str:
    if type(value) is not str:
        raise ValueError(f"{name} must be a string")
    if not _PUBLIC_NAME_RE.fullmatch(value):
        raise ValueError(f"{name} must be public-safe")
    _reject_text_value(name, value)
    return value


def _require_exception_group(name: str, value: str) -> str:
    _require_public_name(name, value)
    normalized = value.lower()
    if any(term in normalized for term in _UNSAFE_GROUP_TERMS):
        raise ValueError(f"{name} must not expose restricted public surface details")
    return value


def _require_reason_code(name: str, value: str) -> str:
    if type(value) is not str:
        raise ValueError(f"{name} must be a string")
    if not _REASON_CODE_RE.fullmatch(value):
        raise ValueError(f"{name} must be a lowercase reason code")
    _reject_text_value(name, value)
    return value


def _normalize_reason_codes(
    name: str,
    value: tuple[str, ...],
    *,
    allow_empty: bool,
) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ValueError(f"{name} must be a tuple")
    if not allow_empty and not value:
        raise ValueError(f"{name} must be nonempty")
    normalized = tuple(_require_reason_code(name, item) for item in value)
    if len(set(normalized)) != len(normalized):
        raise ValueError(f"{name} must not contain duplicates")
    return tuple(sorted(normalized))


def _require_status(name: str, value: str) -> str:
    if type(value) is not str:
        raise ValueError(f"{name} must be a string")
    if value not in _STATUSES:
        raise ValueError(f"{name} must be pass, watch, or block")
    return value


def _require_nonnegative_decimal(name: str, value: Decimal) -> Decimal:
    result = _require_decimal(name, value)
    if result < _ZERO:
        raise ValueError(f"{name} must be nonnegative")
    return _quantize(result)


def _require_positive_whole_decimal(name: str, value: Decimal) -> Decimal:
    result = _require_nonnegative_whole_decimal(name, value)
    if result <= _ZERO:
        raise ValueError(f"{name} must be positive")
    return result


def _require_nonnegative_whole_decimal(name: str, value: Decimal) -> Decimal:
    result = _require_nonnegative_decimal(name, value)
    if result != result.to_integral_value():
        raise ValueError(f"{name} must be a whole Decimal")
    return result


def _require_probability_decimal(name: str, value: Decimal) -> Decimal:
    result = _require_decimal(name, value)
    if result < _ZERO or result > _ONE:
        raise ValueError(f"{name} must be between 0 and 1")
    return _quantize(result)


def _require_optional_probability_decimal(
    name: str,
    value: Decimal | None,
) -> Decimal | None:
    if value is None:
        return None
    return _require_probability_decimal(name, value)


def _require_decimal(name: str, value: Decimal) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{name} must be finite")
    return value


def _decimal_count(value: int) -> Decimal:
    return _quantize(Decimal(value))


def _sum_decimal(values: Iterable[Decimal]) -> Decimal:
    return _quantize(sum(values, _ZERO))


def _quantize(value: Decimal) -> Decimal:
    return value.quantize(_QUANT, rounding=ROUND_HALF_UP)


def _require_digest(name: str, value: str) -> str:
    if type(value) is not str:
        raise ValueError(f"{name} must be a string")
    if not _SHA256_RE.fullmatch(value):
        raise ValueError(f"{name} must be a sha256 digest")
    return value


def _flag_value(value: object, name: str) -> object:
    if isinstance(value, Mapping):
        return value.get(name)
    return getattr(value, name, None)


def _require_hard_flags(name: str, value: object) -> None:
    if _flag_value(value, "paper_only") is not True:
        raise ValueError(f"{name} paper_only must be True")
    if _flag_value(value, "report_only") is not True:
        raise ValueError(f"{name} report_only must be True")
    if _flag_value(value, "readonly") is not True:
        raise ValueError(f"{name} readonly must be True")


def _require_payload_keys(payload: Mapping[str, object]) -> None:
    expected_keys = {field.name for field in fields(ResearchResolutionRuleChangeExceptionReport)}
    actual_keys = set(payload.keys())
    if actual_keys != expected_keys:
        raise ValueError("payload fields must match report fields")


def _reject_public_payload(label: str, value: object) -> None:
    if isinstance(value, Mapping):
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("payload keys must be strings")
            _reject_text_value(label, key)
            _reject_public_payload(label, item)
        return
    if isinstance(value, (list, tuple)):
        for item in value:
            _reject_public_payload(label, item)
        return
    if type(value) is str:
        _reject_text_value(label, value)


def _reject_text_value(label: str, value: str) -> None:
    normalized = value.lower()
    if any(fragment in normalized for fragment in _UNSAFE_PUBLIC_TEXT):
        raise ValueError(f"{label} contains unsafe public surface text")
    if any(term in normalized for term in _UNSAFE_ACTION_TEXT):
        raise ValueError(f"{label} contains unsafe action text")
