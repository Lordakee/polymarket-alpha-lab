"""Pure event-resolution rule classification for caller-supplied research rows.

The module is deterministic and side-effect free. Callers provide typed rule
features; the classifier returns report-only pass/watch/block classifications.
"""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable
from dataclasses import dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation
from typing import Any


__all__ = (
    "ResearchEventResolutionRuleClassificationReport",
    "ResearchEventResolutionRuleClassificationRow",
    "ResearchEventResolutionRuleClassifierConfig",
    "ResearchEventResolutionRuleInput",
    "ResearchEventResolutionRuleReasonCodeCount",
    "build_research_event_resolution_rule_classification_report",
    "research_event_resolution_rule_classification_report_payload",
)


DEFAULT_CONFIG_VERSION = "research-event-resolution-rule-classifier-v0"
STATUSES = ("pass", "watch", "block")
RULE_CLASSES = ("clear", "manual_review", "ambiguity_block")
ZERO = Decimal("0")
ONE = Decimal("1")
FIVE = Decimal("5")
RATIO_QUANTUM = Decimal("0.000001")
UNSAFE_PUBLIC_FRAGMENTS = (
    "market",
    "question",
    "source",
    "url",
    "dsn",
    "table",
    "token",
    "buy",
    "sell",
    "position",
    "recommend",
)


class _Missing:
    pass


_MISSING = _Missing()


@dataclass(frozen=True)
class ResearchEventResolutionRuleClassifierConfig:
    config_version: str = DEFAULT_CONFIG_VERSION
    min_resolver_authority_count: Decimal = Decimal("1")
    min_measurable_condition_count: Decimal = Decimal("2")
    pass_clarity_score: Decimal = Decimal("0.800000")
    watch_clarity_score: Decimal = Decimal("0.500000")
    block_ambiguity_score: Decimal = Decimal("0.500000")
    subjective_judgment_weight: Decimal = Decimal("0.250000")
    discretionary_clause_weight: Decimal = Decimal("0.300000")
    conflicting_clause_weight: Decimal = Decimal("0.500000")
    missing_condition_weight: Decimal = Decimal("0.250000")
    unresolved_dependency_weight: Decimal = Decimal("0.200000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchEventResolutionRuleClassifierConfig:
            raise TypeError(
                "ResearchEventResolutionRuleClassifierConfig does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchEventResolutionRuleClassifierConfig:
            raise ValueError(
                "config must be exactly ResearchEventResolutionRuleClassifierConfig",
            )
        object.__setattr__(
            self,
            "config_version",
            _require_public_identifier("config_version", self.config_version),
        )
        for field_name in (
            "min_resolver_authority_count",
            "min_measurable_condition_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_positive_whole_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "pass_clarity_score",
            "watch_clarity_score",
            "block_ambiguity_score",
            "subjective_judgment_weight",
            "discretionary_clause_weight",
            "conflicting_clause_weight",
            "missing_condition_weight",
            "unresolved_dependency_weight",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_probability_decimal(field_name, getattr(self, field_name)),
            )
        if self.pass_clarity_score <= self.watch_clarity_score:
            raise ValueError("pass_clarity_score must be greater than watch_clarity_score")
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class ResearchEventResolutionRuleInput:
    event_key: str
    rule_id: str
    resolver_authority_count: Decimal
    measurable_condition_count: Decimal
    objective_deadline_present: bool
    numeric_threshold_present: bool
    official_resolver_present: bool
    subjective_judgment_flag: bool = False
    discretionary_clause_flag: bool = False
    conflicting_clause_flag: bool = False
    missing_condition_flag: bool = False
    unresolved_dependency_flag: bool = False
    reason_codes: tuple[str, ...] = ()
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchEventResolutionRuleInput:
            raise TypeError("ResearchEventResolutionRuleInput does not support subclassing")

    def __post_init__(self) -> None:
        if type(self) is not ResearchEventResolutionRuleInput:
            raise ValueError("input must be exactly ResearchEventResolutionRuleInput")
        for field_name in ("event_key", "rule_id"):
            object.__setattr__(
                self,
                field_name,
                _require_public_identifier(field_name, getattr(self, field_name)),
            )
        for field_name in ("resolver_authority_count", "measurable_condition_count"):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_whole_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "objective_deadline_present",
            "numeric_threshold_present",
            "official_resolver_present",
            "subjective_judgment_flag",
            "discretionary_clause_flag",
            "conflicting_clause_flag",
            "missing_condition_flag",
            "unresolved_dependency_flag",
        ):
            _require_bool(field_name, getattr(self, field_name))
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, allow_empty=True),
        )
        _require_hard_flags("input", self)


@dataclass(frozen=True)
class ResearchEventResolutionRuleClassificationRow:
    event_key: str
    rule_id: str
    resolver_authority_count: Decimal
    measurable_condition_count: Decimal
    objective_deadline_present: bool
    numeric_threshold_present: bool
    official_resolver_present: bool
    subjective_judgment_flag: bool
    discretionary_clause_flag: bool
    conflicting_clause_flag: bool
    missing_condition_flag: bool
    unresolved_dependency_flag: bool
    clarity_score: Decimal
    ambiguity_score: Decimal
    review_pressure_score: Decimal
    status: str
    resolution_rule_class: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchEventResolutionRuleClassificationRow:
            raise TypeError(
                "ResearchEventResolutionRuleClassificationRow does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchEventResolutionRuleClassificationRow:
            raise ValueError(
                "row must be exactly ResearchEventResolutionRuleClassificationRow",
            )
        for field_name in ("event_key", "rule_id"):
            object.__setattr__(
                self,
                field_name,
                _require_public_identifier(field_name, getattr(self, field_name)),
            )
        for field_name in ("resolver_authority_count", "measurable_condition_count"):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_whole_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "objective_deadline_present",
            "numeric_threshold_present",
            "official_resolver_present",
            "subjective_judgment_flag",
            "discretionary_clause_flag",
            "conflicting_clause_flag",
            "missing_condition_flag",
            "unresolved_dependency_flag",
        ):
            _require_bool(field_name, getattr(self, field_name))
        for field_name in ("clarity_score", "ambiguity_score", "review_pressure_score"):
            object.__setattr__(
                self,
                field_name,
                _require_probability_decimal(field_name, getattr(self, field_name)),
            )
        _require_member("status", self.status, STATUSES)
        _require_member("resolution_rule_class", self.resolution_rule_class, RULE_CLASSES)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, allow_empty=False),
        )
        _require_hard_flags("row", self)
        _validate_row(self)


@dataclass(frozen=True)
class ResearchEventResolutionRuleReasonCodeCount:
    reason_code: str
    count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchEventResolutionRuleReasonCodeCount:
            raise TypeError(
                "ResearchEventResolutionRuleReasonCodeCount does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchEventResolutionRuleReasonCodeCount:
            raise ValueError(
                "reason code count must be exactly "
                "ResearchEventResolutionRuleReasonCodeCount",
            )
        object.__setattr__(
            self,
            "reason_code",
            _require_public_identifier("reason_code", self.reason_code),
        )
        object.__setattr__(
            self,
            "count",
            _require_positive_whole_decimal("count", self.count),
        )
        _require_hard_flags("reason_code_count", self)


@dataclass(frozen=True)
class ResearchEventResolutionRuleClassificationReport:
    generated_at: datetime
    config_version: str
    rule_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    average_clarity_score: Decimal | None
    average_ambiguity_score: Decimal | None
    status: str
    rows: tuple[ResearchEventResolutionRuleClassificationRow, ...]
    reason_code_counts: tuple[ResearchEventResolutionRuleReasonCodeCount, ...]
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchEventResolutionRuleClassificationReport:
            raise TypeError(
                "ResearchEventResolutionRuleClassificationReport does not support "
                "subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchEventResolutionRuleClassificationReport:
            raise ValueError(
                "report must be exactly ResearchEventResolutionRuleClassificationReport",
            )
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        object.__setattr__(
            self,
            "config_version",
            _require_public_identifier("config_version", self.config_version),
        )
        for field_name in ("rule_count", "pass_count", "watch_count", "block_count"):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_whole_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in ("average_clarity_score", "average_ambiguity_score"):
            object.__setattr__(
                self,
                field_name,
                _require_optional_probability_decimal(field_name, getattr(self, field_name)),
            )
        _require_member("status", self.status, STATUSES)
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
        _validate_report(self)


def build_research_event_resolution_rule_classification_report(
    resolution_rules: Iterable[object],
    *,
    config: ResearchEventResolutionRuleClassifierConfig,
    generated_at: datetime,
) -> ResearchEventResolutionRuleClassificationReport:
    if type(config) is not ResearchEventResolutionRuleClassifierConfig:
        raise ValueError("config must be a ResearchEventResolutionRuleClassifierConfig")
    _require_hard_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    input_rows = _normalize_input_rows(resolution_rules)
    rows = tuple(
        sorted(
            (_classify_rule(row, config=config) for row in input_rows),
            key=lambda row: (row.event_key, row.rule_id),
        ),
    )
    reason_codes = _summary_reason_codes(rows)
    return ResearchEventResolutionRuleClassificationReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        rule_count=_decimal_count(len(rows)),
        pass_count=_decimal_count(_status_count(rows, "pass")),
        watch_count=_decimal_count(_status_count(rows, "watch")),
        block_count=_decimal_count(_status_count(rows, "block")),
        average_clarity_score=_average_score(tuple(row.clarity_score for row in rows)),
        average_ambiguity_score=_average_score(tuple(row.ambiguity_score for row in rows)),
        status=_summary_status(rows),
        rows=rows,
        reason_code_counts=_reason_code_counts(rows, reason_codes),
        reason_codes=reason_codes,
    )


def research_event_resolution_rule_classification_report_payload(
    report: ResearchEventResolutionRuleClassificationReport,
) -> dict[str, Any]:
    if type(report) is not ResearchEventResolutionRuleClassificationReport:
        raise ValueError(
            "report must be a ResearchEventResolutionRuleClassificationReport",
        )
    _require_hard_flags("report", report)
    payload = _payload_value(report)
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    _reject_unsafe_public_payload("report payload", payload)
    return payload


def _classify_rule(
    row: ResearchEventResolutionRuleInput,
    *,
    config: ResearchEventResolutionRuleClassifierConfig,
) -> ResearchEventResolutionRuleClassificationRow:
    clarity_score = _clarity_score(row, config=config)
    ambiguity_score = _ambiguity_score(row, config=config)
    review_pressure_score = _review_pressure_score(
        clarity_score=clarity_score,
        ambiguity_score=ambiguity_score,
    )
    status = _row_status(
        clarity_score=clarity_score,
        ambiguity_score=ambiguity_score,
        config=config,
    )
    rule_class = _rule_class(status)
    return ResearchEventResolutionRuleClassificationRow(
        event_key=row.event_key,
        rule_id=row.rule_id,
        resolver_authority_count=row.resolver_authority_count,
        measurable_condition_count=row.measurable_condition_count,
        objective_deadline_present=row.objective_deadline_present,
        numeric_threshold_present=row.numeric_threshold_present,
        official_resolver_present=row.official_resolver_present,
        subjective_judgment_flag=row.subjective_judgment_flag,
        discretionary_clause_flag=row.discretionary_clause_flag,
        conflicting_clause_flag=row.conflicting_clause_flag,
        missing_condition_flag=row.missing_condition_flag,
        unresolved_dependency_flag=row.unresolved_dependency_flag,
        clarity_score=clarity_score,
        ambiguity_score=ambiguity_score,
        review_pressure_score=review_pressure_score,
        status=status,
        resolution_rule_class=rule_class,
        reason_codes=_row_reason_codes(row, status=status, rule_class=rule_class, config=config),
    )


def _clarity_score(
    row: ResearchEventResolutionRuleInput,
    *,
    config: ResearchEventResolutionRuleClassifierConfig,
) -> Decimal:
    resolver_score = min(ONE, row.resolver_authority_count / config.min_resolver_authority_count)
    condition_score = min(ONE, row.measurable_condition_count / config.min_measurable_condition_count)
    deadline_score = ONE if row.objective_deadline_present else ZERO
    threshold_score = ONE if row.numeric_threshold_present else ZERO
    official_score = ONE if row.official_resolver_present else ZERO
    return _quantize(
        (resolver_score + condition_score + deadline_score + threshold_score + official_score)
        / FIVE,
    )


def _ambiguity_score(
    row: ResearchEventResolutionRuleInput,
    *,
    config: ResearchEventResolutionRuleClassifierConfig,
) -> Decimal:
    score = ZERO
    if row.subjective_judgment_flag:
        score += config.subjective_judgment_weight
    if row.discretionary_clause_flag:
        score += config.discretionary_clause_weight
    if row.conflicting_clause_flag:
        score += config.conflicting_clause_weight
    if row.missing_condition_flag:
        score += config.missing_condition_weight
    if row.unresolved_dependency_flag:
        score += config.unresolved_dependency_weight
    return _quantize(min(ONE, score))


def _review_pressure_score(*, clarity_score: Decimal, ambiguity_score: Decimal) -> Decimal:
    return _quantize(min(ONE, (ONE - clarity_score) + ambiguity_score))


def _row_status(
    *,
    clarity_score: Decimal,
    ambiguity_score: Decimal,
    config: ResearchEventResolutionRuleClassifierConfig,
) -> str:
    if ambiguity_score >= config.block_ambiguity_score:
        return "block"
    if clarity_score < config.watch_clarity_score:
        return "block"
    if clarity_score < config.pass_clarity_score:
        return "watch"
    if ambiguity_score > ZERO:
        return "watch"
    return "pass"


def _rule_class(status: str) -> str:
    if status == "pass":
        return "clear"
    if status == "watch":
        return "manual_review"
    return "ambiguity_block"


def _row_reason_codes(
    row: ResearchEventResolutionRuleInput,
    *,
    status: str,
    rule_class: str,
    config: ResearchEventResolutionRuleClassifierConfig,
) -> tuple[str, ...]:
    reason_codes: set[str] = set()
    if status == "pass":
        reason_codes.add("resolution_rule_clear")
    elif status == "watch":
        reason_codes.add("manual_review_needed")
    else:
        reason_codes.add("ambiguity_block")

    reason_codes.add(
        "resolver_authority_present"
        if row.resolver_authority_count >= config.min_resolver_authority_count
        else "missing_resolver_authority",
    )
    reason_codes.add(
        "sufficient_measurable_conditions"
        if row.measurable_condition_count >= config.min_measurable_condition_count
        else "thin_measurable_conditions",
    )
    reason_codes.add(
        "objective_deadline_present"
        if row.objective_deadline_present
        else "missing_deadline",
    )
    reason_codes.add(
        "numeric_threshold_present"
        if row.numeric_threshold_present
        else "missing_numeric_threshold",
    )
    reason_codes.add(
        "official_resolver_present"
        if row.official_resolver_present
        else "missing_official_resolver",
    )
    if row.subjective_judgment_flag:
        reason_codes.add("subjective_judgment_present")
    if row.discretionary_clause_flag:
        reason_codes.add("discretionary_clause_present")
    if row.conflicting_clause_flag:
        reason_codes.add("conflicting_clauses_present")
    if row.missing_condition_flag:
        reason_codes.add("missing_conditions_present")
    if row.unresolved_dependency_flag:
        reason_codes.add("unresolved_dependency_present")
    for reason_code in row.reason_codes:
        reason_codes.add(f"input_{reason_code}")
    if rule_class not in RULE_CLASSES:
        raise ValueError("resolution_rule_class must be valid")
    return tuple(sorted(reason_codes))


def _normalize_input_rows(
    rows: Iterable[object],
) -> tuple[ResearchEventResolutionRuleInput, ...]:
    if isinstance(rows, (str, bytes)):
        raise ValueError("resolution_rules must be an iterable")
    try:
        values = tuple(rows)
    except TypeError as exc:
        raise ValueError("resolution_rules must be an iterable") from exc
    return tuple(_coerce_input_row(value) for value in values)


def _coerce_input_row(value: object) -> ResearchEventResolutionRuleInput:
    if type(value) is ResearchEventResolutionRuleInput:
        _require_hard_flags("input", value)
        return value
    _require_hard_flags("input", value)
    return ResearchEventResolutionRuleInput(
        event_key=_field_value(value, "event_key"),
        rule_id=_field_value(value, "rule_id"),
        resolver_authority_count=_field_value(value, "resolver_authority_count"),
        measurable_condition_count=_field_value(value, "measurable_condition_count"),
        objective_deadline_present=_field_value(value, "objective_deadline_present"),
        numeric_threshold_present=_field_value(value, "numeric_threshold_present"),
        official_resolver_present=_field_value(value, "official_resolver_present"),
        subjective_judgment_flag=_field_value(
            value,
            "subjective_judgment_flag",
            default=False,
        ),
        discretionary_clause_flag=_field_value(
            value,
            "discretionary_clause_flag",
            default=False,
        ),
        conflicting_clause_flag=_field_value(
            value,
            "conflicting_clause_flag",
            default=False,
        ),
        missing_condition_flag=_field_value(value, "missing_condition_flag", default=False),
        unresolved_dependency_flag=_field_value(
            value,
            "unresolved_dependency_flag",
            default=False,
        ),
        reason_codes=_field_value(value, "reason_codes", default=()),
        paper_only=_field_value(value, "paper_only"),
        report_only=_field_value(value, "report_only"),
        readonly=_field_value(value, "readonly"),
    )


def _reason_code_counts(
    rows: tuple[ResearchEventResolutionRuleClassificationRow, ...],
    reason_codes: tuple[str, ...],
) -> tuple[ResearchEventResolutionRuleReasonCodeCount, ...]:
    if not rows:
        return (
            ResearchEventResolutionRuleReasonCodeCount(
                reason_code=reason_codes[0],
                count=ONE,
            ),
        )
    counts: Counter[str] = Counter()
    for row in rows:
        counts.update(row.reason_codes)
    return tuple(
        ResearchEventResolutionRuleReasonCodeCount(
            reason_code=reason_code,
            count=_decimal_count(count),
        )
        for reason_code, count in sorted(counts.items(), key=lambda item: item[0])
    )


def _summary_reason_codes(
    rows: tuple[ResearchEventResolutionRuleClassificationRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return ("no_resolution_rules",)
    return tuple(sorted({reason_code for row in rows for reason_code in row.reason_codes}))


def _summary_status(rows: tuple[ResearchEventResolutionRuleClassificationRow, ...]) -> str:
    if not rows:
        return "block"
    if any(row.status == "block" for row in rows):
        return "block"
    if any(row.status == "watch" for row in rows):
        return "watch"
    return "pass"


def _status_count(
    rows: tuple[ResearchEventResolutionRuleClassificationRow, ...],
    status: str,
) -> int:
    return sum(1 for row in rows if row.status == status)


def _average_score(values: tuple[Decimal, ...]) -> Decimal | None:
    if not values:
        return None
    return _quantize(sum(values, ZERO) / Decimal(len(values)))


def _normalize_rows(
    rows: tuple[ResearchEventResolutionRuleClassificationRow, ...],
) -> tuple[ResearchEventResolutionRuleClassificationRow, ...]:
    if type(rows) is not tuple:
        raise ValueError("rows must be a tuple")
    for row in rows:
        if type(row) is not ResearchEventResolutionRuleClassificationRow:
            raise ValueError(
                "rows must contain ResearchEventResolutionRuleClassificationRow values",
            )
        _require_hard_flags("row", row)
    sorted_rows = tuple(sorted(rows, key=lambda row: (row.event_key, row.rule_id)))
    if rows != sorted_rows:
        raise ValueError("rows must be sorted by event_key and rule_id")
    return rows


def _normalize_reason_code_counts(
    counts: tuple[ResearchEventResolutionRuleReasonCodeCount, ...],
) -> tuple[ResearchEventResolutionRuleReasonCodeCount, ...]:
    if type(counts) is not tuple:
        raise ValueError("reason_code_counts must be a tuple")
    for count in counts:
        if type(count) is not ResearchEventResolutionRuleReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "ResearchEventResolutionRuleReasonCodeCount values",
            )
        _require_hard_flags("reason_code_count", count)
    sorted_counts = tuple(sorted(counts, key=lambda count: count.reason_code))
    if counts != sorted_counts:
        raise ValueError("reason_code_counts must be sorted by reason_code")
    return counts


def _validate_row(row: ResearchEventResolutionRuleClassificationRow) -> None:
    if row.status == "pass" and row.clarity_score < Decimal("0.800000"):
        raise ValueError("clarity_score must support pass status")
    if row.status == "pass" and row.ambiguity_score != ZERO:
        raise ValueError("ambiguity_score must support pass status")
    if row.status == "watch" and (
        row.clarity_score < Decimal("0.500000") or row.clarity_score >= Decimal("0.800000")
    ):
        if row.ambiguity_score == ZERO:
            raise ValueError("clarity_score must support watch status")
    if row.status == "block" and (
        row.clarity_score >= Decimal("0.500000") and row.ambiguity_score < Decimal("0.500000")
    ):
        raise ValueError("clarity_score must support block status")
    expected_class = _rule_class(row.status)
    if row.resolution_rule_class != expected_class:
        raise ValueError("resolution_rule_class must match status")
    required_reason = {
        "pass": "resolution_rule_clear",
        "watch": "manual_review_needed",
        "block": "ambiguity_block",
    }[row.status]
    if required_reason not in row.reason_codes:
        raise ValueError("reason_codes must match status")


def _validate_report(report: ResearchEventResolutionRuleClassificationReport) -> None:
    if report.rule_count != _decimal_count(len(report.rows)):
        raise ValueError("rule_count must match rows")
    if report.pass_count != _decimal_count(_status_count(report.rows, "pass")):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _decimal_count(_status_count(report.rows, "watch")):
        raise ValueError("watch_count must match rows")
    if report.block_count != _decimal_count(_status_count(report.rows, "block")):
        raise ValueError("block_count must match rows")
    if report.average_clarity_score != _average_score(
        tuple(row.clarity_score for row in report.rows),
    ):
        raise ValueError("average_clarity_score must match rows")
    if report.average_ambiguity_score != _average_score(
        tuple(row.ambiguity_score for row in report.rows),
    ):
        raise ValueError("average_ambiguity_score must match rows")
    if report.reason_codes != _summary_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")
    if report.status != _summary_status(report.rows):
        raise ValueError("status must match rows")


def _field_value(value: object, field_name: str, *, default: object = _MISSING) -> object:
    if is_dataclass(value):
        for field in fields(value):
            if field.name == field_name:
                return getattr(value, field_name)
    if hasattr(value, field_name):
        return getattr(value, field_name)
    if default is not _MISSING:
        return default
    raise ValueError(f"{field_name} is required")


def _payload_value(value: object) -> object:
    if isinstance(value, Decimal):
        return _decimal_payload(value)
    if isinstance(value, datetime):
        return value.isoformat()
    if is_dataclass(value) and not isinstance(value, type):
        return {field.name: _payload_value(getattr(value, field.name)) for field in fields(value)}
    if isinstance(value, tuple):
        return [_payload_value(item) for item in value]
    if isinstance(value, list):
        return [_payload_value(item) for item in value]
    if isinstance(value, dict):
        return {str(key): _payload_value(item) for key, item in value.items()}
    if isinstance(value, float):
        raise ValueError("payload must not contain floats")
    return value


def _reject_unsafe_public_payload(label: str, value: object) -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError(f"{label} keys must be strings")
            _reject_unsafe_public_text(f"{label}.{key}", key)
            _reject_unsafe_public_payload(f"{label}.{key}", item)
    elif isinstance(value, list):
        for item in value:
            _reject_unsafe_public_payload(label, item)
    elif isinstance(value, str):
        _reject_unsafe_public_text(label, value)
    elif isinstance(value, float):
        raise ValueError(f"{label} must not contain floats")


def _reject_unsafe_public_text(field_name: str, value: str) -> None:
    lowered = value.lower()
    if any(fragment in lowered for fragment in UNSAFE_PUBLIC_FRAGMENTS):
        raise ValueError(f"{field_name} contains unsafe public text")


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
        raise ValueError("count value must be an int")
    if value < 0:
        raise ValueError("count value must be nonnegative")
    return Decimal(value)


def _decimal_payload(value: Decimal) -> str:
    if type(value) is not Decimal or not value.is_finite():
        raise ValueError("payload Decimal must be finite")
    return str(value)


def _quantize(value: Decimal) -> Decimal:
    return value.quantize(RATIO_QUANTUM)


def _require_public_identifier(field_name: str, value: object) -> str:
    if type(value) is not str or not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a nonempty canonical string")
    allowed = set("abcdefghijklmnopqrstuvwxyz0123456789-_")
    if any(character not in allowed for character in value):
        raise ValueError(f"{field_name} must be a lowercase public identifier")
    _reject_unsafe_public_text(field_name, value)
    return value


def _require_member(field_name: str, value: object, allowed: tuple[str, ...]) -> None:
    if type(value) is not str or value not in allowed:
        raise ValueError(f"{field_name} must be one of {allowed}")


def _require_bool(field_name: str, value: object) -> None:
    if type(value) is not bool:
        raise ValueError(f"{field_name} must be a bool")


def _normalize_reason_codes(
    field_name: str,
    values: object,
    *,
    allow_empty: bool,
) -> tuple[str, ...]:
    if type(values) is not tuple:
        raise ValueError(f"{field_name} must be a tuple")
    normalized = tuple(
        _require_public_identifier(field_name, value)
        for value in values
    )
    if not allow_empty and not normalized:
        raise ValueError(f"{field_name} must be nonempty")
    return tuple(sorted(set(normalized)))


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if getattr(value, field_name, None) is not True:
            raise ValueError(f"{field_name} must be True for {label}")
