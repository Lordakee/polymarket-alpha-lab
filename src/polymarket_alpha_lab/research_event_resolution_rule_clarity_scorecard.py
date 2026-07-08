"""Pure report-only resolution-rule clarity scorecard."""

from __future__ import annotations

from collections import Counter
from dataclasses import asdict, dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal, ROUND_HALF_UP
import hashlib
import json
import re
from typing import Any, Mapping, Sequence


DEFAULT_RESEARCH_EVENT_RESOLUTION_RULE_CLARITY_SCORECARD_CONFIG_VERSION = (
    "research-event-resolution-rule-clarity-scorecard-v1"
)

_QUANT = Decimal("0.000001")
_ZERO = Decimal("0.000000")
_ONE = Decimal("1.000000")
_PUBLIC_IDENTIFIER_RE = re.compile(r"^[A-Za-z][A-Za-z0-9_.-]{0,127}$")
_DIGEST_RE = re.compile(r"^[0-9a-f]{64}$")
_WORKFLOW_STATUSES = frozenset(("pass", "watch", "block"))
_PHASE_FLAG_FIELDS = frozenset(("paper_only", "report_only", "readonly"))
_UNSAFE_PUBLIC_FRAGMENTS = (
    "raw",
    "market",
    "question",
    "source",
    "url",
    "dsn",
    "table",
    "wallet",
    "auth",
    "order",
    "trade",
    "private-key",
    "private_key",
    "privatekey",
    "token",
    "live",
    "execution",
    "buy",
    "sell",
    "position",
    "recommend",
)
_REASON_CODE_SEQUENCE = (
    "no_event_categories",
    "rule_specificity_ready",
    "rule_specificity_gap",
    "oracle_consistency_ready",
    "oracle_consistency_gap",
    "deadline_clear",
    "deadline_gap",
    "ambiguity_clear",
    "ambiguity_flag_present",
    "ambiguity_block",
    "clarity_pass",
    "clarity_watch",
    "clarity_block",
)


@dataclass(frozen=True)
class ResearchEventResolutionRuleClarityScorecardConfig:
    config_version: str = (
        DEFAULT_RESEARCH_EVENT_RESOLUTION_RULE_CLARITY_SCORECARD_CONFIG_VERSION
    )
    min_rule_specificity_score: Decimal = Decimal("0.700000")
    min_oracle_consistency_score: Decimal = Decimal("0.700000")
    min_deadline_clarity_score: Decimal = Decimal("0.600000")
    pass_clarity_score: Decimal = Decimal("0.750000")
    block_clarity_score: Decimal = Decimal("0.450000")
    rule_specificity_weight: Decimal = Decimal("0.350000")
    oracle_consistency_weight: Decimal = Decimal("0.350000")
    deadline_clarity_weight: Decimal = Decimal("0.300000")
    ambiguity_flag_penalty: Decimal = Decimal("0.100000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchEventResolutionRuleClarityScorecardConfig:
            raise TypeError(
                "ResearchEventResolutionRuleClarityScorecardConfig does not support "
                "subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchEventResolutionRuleClarityScorecardConfig:
            raise ValueError(
                "config must be exactly "
                "ResearchEventResolutionRuleClarityScorecardConfig",
            )
        object.__setattr__(
            self,
            "config_version",
            _require_public_identifier("config_version", self.config_version),
        )
        if (
            self.config_version
            != DEFAULT_RESEARCH_EVENT_RESOLUTION_RULE_CLARITY_SCORECARD_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "min_rule_specificity_score",
            "min_oracle_consistency_score",
            "min_deadline_clarity_score",
            "pass_clarity_score",
            "block_clarity_score",
            "rule_specificity_weight",
            "oracle_consistency_weight",
            "deadline_clarity_weight",
            "ambiguity_flag_penalty",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        if self.pass_clarity_score <= self.block_clarity_score:
            raise ValueError("pass_clarity_score must exceed block_clarity_score")
        if (
            self.rule_specificity_weight
            + self.oracle_consistency_weight
            + self.deadline_clarity_weight
        ) != _ONE:
            raise ValueError("clarity weights must sum to one")
        _require_hard_flags("config", self)
        _reject_unsafe_public_payload("config", self)


@dataclass(frozen=True)
class ResearchEventResolutionRuleCategoryInput:
    event_category: str
    rule_specificity_score: Decimal
    oracle_consistency_score: Decimal
    deadline_clarity_score: Decimal
    subjective_wording_flag: bool = False
    discretionary_resolution_flag: bool = False
    conflicting_resolution_flag: bool = False
    missing_deadline_flag: bool = False
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchEventResolutionRuleCategoryInput:
            raise TypeError(
                "ResearchEventResolutionRuleCategoryInput does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchEventResolutionRuleCategoryInput:
            raise ValueError(
                "input must be exactly ResearchEventResolutionRuleCategoryInput",
            )
        object.__setattr__(
            self,
            "event_category",
            _require_public_identifier("event_category", self.event_category),
        )
        for field_name in (
            "rule_specificity_score",
            "oracle_consistency_score",
            "deadline_clarity_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "subjective_wording_flag",
            "discretionary_resolution_flag",
            "conflicting_resolution_flag",
            "missing_deadline_flag",
        ):
            _require_bool(field_name, getattr(self, field_name))
        _require_hard_flags("input", self)
        _reject_unsafe_public_payload("input", self)


@dataclass(frozen=True)
class ResearchEventResolutionRuleClarityScorecardRow:
    event_category: str
    rule_specificity_score: Decimal
    oracle_consistency_score: Decimal
    deadline_clarity_score: Decimal
    subjective_wording_flag: bool
    discretionary_resolution_flag: bool
    conflicting_resolution_flag: bool
    missing_deadline_flag: bool
    clarity_score: Decimal
    ambiguity_flag_count: Decimal
    workflow_status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchEventResolutionRuleClarityScorecardRow:
            raise TypeError(
                "ResearchEventResolutionRuleClarityScorecardRow does not support "
                "subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchEventResolutionRuleClarityScorecardRow:
            raise ValueError(
                "row must be exactly ResearchEventResolutionRuleClarityScorecardRow",
            )
        object.__setattr__(
            self,
            "event_category",
            _require_public_identifier("event_category", self.event_category),
        )
        for field_name in (
            "rule_specificity_score",
            "oracle_consistency_score",
            "deadline_clarity_score",
            "clarity_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "subjective_wording_flag",
            "discretionary_resolution_flag",
            "conflicting_resolution_flag",
            "missing_deadline_flag",
        ):
            _require_bool(field_name, getattr(self, field_name))
        object.__setattr__(
            self,
            "ambiguity_flag_count",
            _require_nonnegative_count_decimal(
                "ambiguity_flag_count",
                self.ambiguity_flag_count,
            ),
        )
        _require_workflow_status("workflow_status", self.workflow_status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        _validate_row(self)
        _require_hard_flags("row", self)
        _reject_unsafe_public_payload("row", self)


@dataclass(frozen=True)
class ResearchEventResolutionRuleClarityReasonCodeCount:
    reason_code: str
    count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchEventResolutionRuleClarityReasonCodeCount:
            raise TypeError(
                "ResearchEventResolutionRuleClarityReasonCodeCount does not support "
                "subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchEventResolutionRuleClarityReasonCodeCount:
            raise ValueError(
                "reason code count must be exactly "
                "ResearchEventResolutionRuleClarityReasonCodeCount",
            )
        object.__setattr__(
            self,
            "reason_code",
            _require_reason_code("reason_code", self.reason_code),
        )
        object.__setattr__(
            self,
            "count",
            _require_positive_count_decimal("count", self.count),
        )
        _require_hard_flags("reason code count", self)
        _reject_unsafe_public_payload("reason code count", self)


@dataclass(frozen=True)
class ResearchEventResolutionRuleClarityScorecardReport:
    generated_at: datetime
    config_version: str
    workflow_status: str
    category_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    average_clarity_score: Decimal
    max_ambiguity_flag_count: Decimal
    rows: tuple[ResearchEventResolutionRuleClarityScorecardRow, ...]
    reason_code_counts: tuple[ResearchEventResolutionRuleClarityReasonCodeCount, ...]
    reason_codes: tuple[str, ...]
    derived_validation_digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchEventResolutionRuleClarityScorecardReport:
            raise TypeError(
                "ResearchEventResolutionRuleClarityScorecardReport does not support "
                "subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchEventResolutionRuleClarityScorecardReport:
            raise ValueError(
                "report must be exactly "
                "ResearchEventResolutionRuleClarityScorecardReport",
            )
        object.__setattr__(
            self,
            "generated_at",
            _as_utc("generated_at", self.generated_at),
        )
        object.__setattr__(
            self,
            "config_version",
            _require_public_identifier("config_version", self.config_version),
        )
        if (
            self.config_version
            != DEFAULT_RESEARCH_EVENT_RESOLUTION_RULE_CLARITY_SCORECARD_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        _require_workflow_status("workflow_status", self.workflow_status)
        for field_name in (
            "category_count",
            "pass_count",
            "watch_count",
            "block_count",
            "max_ambiguity_flag_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_count_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "average_clarity_score",
            _require_ratio_decimal(
                "average_clarity_score",
                self.average_clarity_score,
            ),
        )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        _require_sha256_digest("derived_validation_digest", self.derived_validation_digest)
        _validate_report(self)
        _require_hard_flags("report", self)
        _reject_unsafe_public_payload("report", self)
        expected_digest = _report_digest_from_values(_report_values_without_digest(self))
        if self.derived_validation_digest != expected_digest:
            raise ValueError("derived_validation_digest does not match report payload")


def build_research_event_resolution_rule_clarity_scorecard(
    event_categories: Sequence[ResearchEventResolutionRuleCategoryInput],
    *,
    generated_at: datetime,
    config: ResearchEventResolutionRuleClarityScorecardConfig | None = None,
) -> ResearchEventResolutionRuleClarityScorecardReport:
    if config is None:
        config = ResearchEventResolutionRuleClarityScorecardConfig()
    if type(config) is not ResearchEventResolutionRuleClarityScorecardConfig:
        raise ValueError(
            "config must be a ResearchEventResolutionRuleClarityScorecardConfig",
        )
    _require_hard_flags("config", config)
    generated_at = _as_utc("generated_at", generated_at)
    inputs = _normalize_inputs(event_categories)
    rows = tuple(_row_for_input(item, config=config) for item in inputs)
    reason_codes = _summary_reason_codes(rows)
    values: dict[str, object] = {
        "generated_at": generated_at,
        "config_version": config.config_version,
        "workflow_status": _summary_status(rows),
        "category_count": _decimal_count(len(rows)),
        "pass_count": _decimal_count(_status_count(rows, "pass")),
        "watch_count": _decimal_count(_status_count(rows, "watch")),
        "block_count": _decimal_count(_status_count(rows, "block")),
        "average_clarity_score": _average(
            tuple(row.clarity_score for row in rows),
        ),
        "max_ambiguity_flag_count": max(
            (row.ambiguity_flag_count for row in rows),
            default=_ZERO,
        ),
        "rows": rows,
        "reason_code_counts": _reason_code_counts(rows, reason_codes),
        "reason_codes": reason_codes,
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    return ResearchEventResolutionRuleClarityScorecardReport(
        **values,
        derived_validation_digest=_report_digest_from_values(values),
    )


def research_event_resolution_rule_clarity_scorecard_payload(
    report: ResearchEventResolutionRuleClarityScorecardReport,
) -> dict[str, Any]:
    if type(report) is not ResearchEventResolutionRuleClarityScorecardReport:
        raise ValueError(
            "report must be a ResearchEventResolutionRuleClarityScorecardReport",
        )
    _require_hard_flags("report", report)
    payload = _json_ready(report)
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    _reject_unsafe_public_payload("report payload", payload, allow_json_containers=True)
    return payload


def _row_for_input(
    item: ResearchEventResolutionRuleCategoryInput,
    *,
    config: ResearchEventResolutionRuleClarityScorecardConfig,
) -> ResearchEventResolutionRuleClarityScorecardRow:
    ambiguity_flag_count = _ambiguity_flag_count(item)
    clarity_score = _clarity_score(
        item,
        ambiguity_flag_count=ambiguity_flag_count,
        config=config,
    )
    workflow_status = _row_status(
        item,
        clarity_score=clarity_score,
        config=config,
    )
    return ResearchEventResolutionRuleClarityScorecardRow(
        event_category=item.event_category,
        rule_specificity_score=item.rule_specificity_score,
        oracle_consistency_score=item.oracle_consistency_score,
        deadline_clarity_score=item.deadline_clarity_score,
        subjective_wording_flag=item.subjective_wording_flag,
        discretionary_resolution_flag=item.discretionary_resolution_flag,
        conflicting_resolution_flag=item.conflicting_resolution_flag,
        missing_deadline_flag=item.missing_deadline_flag,
        clarity_score=clarity_score,
        ambiguity_flag_count=ambiguity_flag_count,
        workflow_status=workflow_status,
        reason_codes=_row_reason_codes(
            item,
            workflow_status=workflow_status,
            config=config,
        ),
    )


def _clarity_score(
    item: ResearchEventResolutionRuleCategoryInput,
    *,
    ambiguity_flag_count: Decimal,
    config: ResearchEventResolutionRuleClarityScorecardConfig,
) -> Decimal:
    return _clamp_ratio(
        (item.rule_specificity_score * config.rule_specificity_weight)
        + (item.oracle_consistency_score * config.oracle_consistency_weight)
        + (item.deadline_clarity_score * config.deadline_clarity_weight)
        - (ambiguity_flag_count * config.ambiguity_flag_penalty),
    )


def _ambiguity_flag_count(item: ResearchEventResolutionRuleCategoryInput) -> Decimal:
    return _decimal_count(
        sum(
            (
                item.subjective_wording_flag,
                item.discretionary_resolution_flag,
                item.conflicting_resolution_flag,
                item.missing_deadline_flag,
            ),
        ),
    )


def _row_status(
    item: ResearchEventResolutionRuleCategoryInput,
    *,
    clarity_score: Decimal,
    config: ResearchEventResolutionRuleClarityScorecardConfig,
) -> str:
    if item.conflicting_resolution_flag:
        return "block"
    if clarity_score < config.block_clarity_score:
        return "block"
    if item.missing_deadline_flag:
        return "block"
    if clarity_score < config.pass_clarity_score:
        return "watch"
    if _ambiguity_flag_count(item) > _ZERO:
        return "watch"
    if item.rule_specificity_score < config.min_rule_specificity_score:
        return "watch"
    if item.oracle_consistency_score < config.min_oracle_consistency_score:
        return "watch"
    if item.deadline_clarity_score < config.min_deadline_clarity_score:
        return "watch"
    return "pass"


def _row_reason_codes(
    item: ResearchEventResolutionRuleCategoryInput,
    *,
    workflow_status: str,
    config: ResearchEventResolutionRuleClarityScorecardConfig,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    reason_codes.append(
        "rule_specificity_ready"
        if item.rule_specificity_score >= config.min_rule_specificity_score
        else "rule_specificity_gap",
    )
    reason_codes.append(
        "oracle_consistency_ready"
        if item.oracle_consistency_score >= config.min_oracle_consistency_score
        else "oracle_consistency_gap",
    )
    deadline_gap = (
        item.deadline_clarity_score < config.min_deadline_clarity_score
        or item.missing_deadline_flag
    )
    reason_codes.append("deadline_gap" if deadline_gap else "deadline_clear")
    if item.conflicting_resolution_flag or item.missing_deadline_flag:
        reason_codes.append("ambiguity_block")
    elif _ambiguity_flag_count(item) > _ZERO:
        reason_codes.append("ambiguity_flag_present")
    else:
        reason_codes.append("ambiguity_clear")
    if workflow_status == "pass":
        reason_codes.append("clarity_pass")
    elif workflow_status == "watch":
        reason_codes.append("clarity_watch")
    else:
        reason_codes.append("clarity_block")
    return _normalize_reason_codes("reason_codes", tuple(reason_codes))


def _summary_status(
    rows: tuple[ResearchEventResolutionRuleClarityScorecardRow, ...],
) -> str:
    if not rows:
        return "block"
    if any(row.workflow_status == "block" for row in rows):
        return "block"
    if any(row.workflow_status == "watch" for row in rows):
        return "watch"
    return "pass"


def _summary_reason_codes(
    rows: tuple[ResearchEventResolutionRuleClarityScorecardRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return ("no_event_categories",)
    reason_codes: list[str] = []
    for row in rows:
        reason_codes.extend(row.reason_codes)
    return _normalize_reason_codes("reason_codes", tuple(reason_codes))


def _reason_code_counts(
    rows: tuple[ResearchEventResolutionRuleClarityScorecardRow, ...],
    reason_codes: tuple[str, ...],
) -> tuple[ResearchEventResolutionRuleClarityReasonCodeCount, ...]:
    if not rows:
        return (
            ResearchEventResolutionRuleClarityReasonCodeCount(
                reason_code="no_event_categories",
                count=_ONE,
            ),
        )
    counts = Counter(reason_code for row in rows for reason_code in row.reason_codes)
    return tuple(
        ResearchEventResolutionRuleClarityReasonCodeCount(
            reason_code=reason_code,
            count=_decimal_count(counts[reason_code]),
        )
        for reason_code in reason_codes
        if counts[reason_code] > 0
    )


def _status_count(
    rows: tuple[ResearchEventResolutionRuleClarityScorecardRow, ...],
    status: str,
) -> int:
    return sum(1 for row in rows if row.workflow_status == status)


def _validate_row(row: ResearchEventResolutionRuleClarityScorecardRow) -> None:
    if row.workflow_status == "pass" and "clarity_pass" not in row.reason_codes:
        raise ValueError("pass rows must include clarity_pass")
    if row.workflow_status == "watch" and "clarity_watch" not in row.reason_codes:
        raise ValueError("watch rows must include clarity_watch")
    if row.workflow_status == "block" and "clarity_block" not in row.reason_codes:
        raise ValueError("block rows must include clarity_block")
    if row.workflow_status != "pass" and "clarity_pass" in row.reason_codes:
        raise ValueError("non-pass rows must not include clarity_pass")


def _validate_report(report: ResearchEventResolutionRuleClarityScorecardReport) -> None:
    if report.category_count != _decimal_count(len(report.rows)):
        raise ValueError("category_count must match rows")
    if report.pass_count != _decimal_count(_status_count(report.rows, "pass")):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _decimal_count(_status_count(report.rows, "watch")):
        raise ValueError("watch_count must match rows")
    if report.block_count != _decimal_count(_status_count(report.rows, "block")):
        raise ValueError("block_count must match rows")
    if report.average_clarity_score != _average(
        tuple(row.clarity_score for row in report.rows),
    ):
        raise ValueError("average_clarity_score must match rows")
    expected_max_flags = max(
        (row.ambiguity_flag_count for row in report.rows),
        default=_ZERO,
    )
    if report.max_ambiguity_flag_count != expected_max_flags:
        raise ValueError("max_ambiguity_flag_count must match rows")
    if report.workflow_status != _summary_status(report.rows):
        raise ValueError("workflow_status must match rows")
    if report.reason_codes != _summary_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")
    if report.reason_code_counts != _reason_code_counts(
        report.rows,
        report.reason_codes,
    ):
        raise ValueError("reason_code_counts must match rows")


def _normalize_inputs(
    values: Sequence[ResearchEventResolutionRuleCategoryInput],
) -> tuple[ResearchEventResolutionRuleCategoryInput, ...]:
    if isinstance(values, (str, bytes)) or not isinstance(values, Sequence):
        raise ValueError("event_categories must be a sequence")
    normalized: list[ResearchEventResolutionRuleCategoryInput] = []
    for item in values:
        if type(item) is not ResearchEventResolutionRuleCategoryInput:
            raise ValueError(
                "event_categories must contain "
                "ResearchEventResolutionRuleCategoryInput",
            )
        _require_hard_flags("input", item)
        normalized.append(item)
    return tuple(sorted(normalized, key=lambda item: item.event_category))


def _normalize_rows(
    values: Sequence[ResearchEventResolutionRuleClarityScorecardRow],
) -> tuple[ResearchEventResolutionRuleClarityScorecardRow, ...]:
    if isinstance(values, (str, bytes)) or not isinstance(values, Sequence):
        raise ValueError("rows must be a sequence")
    normalized: list[ResearchEventResolutionRuleClarityScorecardRow] = []
    for item in values:
        if type(item) is not ResearchEventResolutionRuleClarityScorecardRow:
            raise ValueError(
                "rows must contain ResearchEventResolutionRuleClarityScorecardRow",
            )
        _require_hard_flags("row", item)
        normalized.append(item)
    return tuple(sorted(normalized, key=lambda item: item.event_category))


def _normalize_reason_code_counts(
    values: Sequence[ResearchEventResolutionRuleClarityReasonCodeCount],
) -> tuple[ResearchEventResolutionRuleClarityReasonCodeCount, ...]:
    if isinstance(values, (str, bytes)) or not isinstance(values, Sequence):
        raise ValueError("reason_code_counts must be a sequence")
    normalized: list[ResearchEventResolutionRuleClarityReasonCodeCount] = []
    for item in values:
        if type(item) is not ResearchEventResolutionRuleClarityReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "ResearchEventResolutionRuleClarityReasonCodeCount",
            )
        _require_hard_flags("reason code count", item)
        normalized.append(item)
    return tuple(
        sorted(
            normalized,
            key=lambda item: _REASON_CODE_SEQUENCE.index(item.reason_code),
        ),
    )


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in _PHASE_FLAG_FIELDS:
        if getattr(value, field_name) is not True:
            raise ValueError(f"{field_name} must be True for {label}")


def _require_public_identifier(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not _PUBLIC_IDENTIFIER_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a public identifier")
    _reject_unsafe_public_string(field_name, value)
    return value


def _require_reason_code(field_name: str, value: object) -> str:
    value = _require_public_identifier(field_name, value)
    if value not in _REASON_CODE_SEQUENCE:
        raise ValueError(f"{field_name} must be supported")
    return value


def _require_bool(field_name: str, value: object) -> None:
    if type(value) is not bool:
        raise ValueError(f"{field_name} must be a bool")


def _require_workflow_status(field_name: str, value: object) -> str:
    if type(value) is not str or value not in _WORKFLOW_STATUSES:
        raise ValueError(f"{field_name} must be one of pass, watch, block")
    return value


def _require_sha256_digest(field_name: str, value: object) -> str:
    if type(value) is not str or not _DIGEST_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a lowercase sha256 digest")
    return value


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return _quantize(value)


def _require_ratio_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < _ZERO or normalized > _ONE:
        raise ValueError(f"{field_name} must be between zero and one")
    return normalized


def _require_nonnegative_count_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < _ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _require_positive_count_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_nonnegative_count_decimal(field_name, value)
    if normalized <= _ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _decimal_count(value: int) -> Decimal:
    if value < 0:
        raise ValueError("count must be nonnegative")
    return Decimal(value).quantize(_QUANT)


def _average(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return _ZERO
    return _quantize(sum(values, _ZERO) / Decimal(len(values)))


def _clamp_ratio(value: Decimal) -> Decimal:
    normalized = _quantize(value)
    if normalized < _ZERO:
        return _ZERO
    if normalized > _ONE:
        return _ONE
    return normalized


def _quantize(value: Decimal) -> Decimal:
    return value.quantize(_QUANT, rounding=ROUND_HALF_UP)


def _normalize_reason_codes(
    field_name: str,
    reason_codes: Sequence[str],
) -> tuple[str, ...]:
    if isinstance(reason_codes, (str, bytes)) or not isinstance(reason_codes, Sequence):
        raise ValueError(f"{field_name} must be a sequence")
    normalized: list[str] = []
    for reason_code in reason_codes:
        reason_code = _require_reason_code("reason_code", reason_code)
        if reason_code not in normalized:
            normalized.append(reason_code)
    if not normalized:
        raise ValueError(f"{field_name} must not be empty")
    return tuple(
        reason_code
        for reason_code in _REASON_CODE_SEQUENCE
        if reason_code in normalized
    )


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _report_values_without_digest(
    report: ResearchEventResolutionRuleClarityScorecardReport,
) -> dict[str, object]:
    values = asdict(report)
    values.pop("derived_validation_digest", None)
    return values


def _report_digest_from_values(values: Mapping[str, object]) -> str:
    payload = _json_ready(values)
    _reject_unsafe_public_payload(
        "derived_validation_digest payload",
        payload,
        allow_json_containers=True,
    )
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


def _reject_unsafe_public_payload(
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
            _reject_unsafe_public_payload(
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
            _reject_unsafe_public_payload(
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
            _reject_unsafe_public_payload(
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
    if "://" in lowered or "?" in lowered or "@" in lowered:
        raise ValueError(f"{field_name} has unsafe public value")
    if any(fragment in lowered for fragment in _UNSAFE_PUBLIC_FRAGMENTS):
        raise ValueError(f"{field_name} has unsafe public value")


__all__ = (
    "DEFAULT_RESEARCH_EVENT_RESOLUTION_RULE_CLARITY_SCORECARD_CONFIG_VERSION",
    "ResearchEventResolutionRuleCategoryInput",
    "ResearchEventResolutionRuleClarityReasonCodeCount",
    "ResearchEventResolutionRuleClarityScorecardConfig",
    "ResearchEventResolutionRuleClarityScorecardReport",
    "ResearchEventResolutionRuleClarityScorecardRow",
    "build_research_event_resolution_rule_clarity_scorecard",
    "research_event_resolution_rule_clarity_scorecard_payload",
)
