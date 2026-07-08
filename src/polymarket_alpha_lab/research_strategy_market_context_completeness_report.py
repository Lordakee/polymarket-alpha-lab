"""Pure market-context completeness report for manual review."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
import json
from typing import Any


DEFAULT_RESEARCH_STRATEGY_MARKET_CONTEXT_COMPLETENESS_REPORT_CONFIG_VERSION = (
    "research-strategy-market-context-completeness-report-v0"
)

_DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
_QUANTUM = Decimal("0.000001")
_ZERO = Decimal("0.000000")
_ONE = Decimal("1.000000")
_SEVEN = Decimal("7.000000")

_STATUS_PASS = "pass"
_STATUS_WATCH = "watch"
_STATUS_BLOCK = "block"
_STATUSES = (_STATUS_PASS, _STATUS_WATCH, _STATUS_BLOCK)
_STATUS_WEIGHT = {
    _STATUS_BLOCK: Decimal("0.000000"),
    _STATUS_WATCH: Decimal("1.000000"),
    _STATUS_PASS: Decimal("2.000000"),
}

_NO_CONTEXTS_REASON = "market_context_completeness_no_contexts"
_PASS_REASON = "market_context_completeness_pass"
_WATCH_REASON = "market_context_completeness_watch"
_BLOCK_REASON = "market_context_completeness_block"

_REASON_PRIORITY = (
    "sanitized_evidence_count_block",
    "independent_family_count_block",
    "evidence_section_block",
    "cost_section_block",
    "settlement_rule_section_block",
    "domain_memory_section_block",
    "forecast_rationale_section_block",
    "aggregate_context_block",
    "open_context_gap_block",
    _BLOCK_REASON,
    "sanitized_evidence_count_watch",
    "independent_family_count_watch",
    "evidence_section_watch",
    "cost_section_watch",
    "settlement_rule_section_watch",
    "domain_memory_section_watch",
    "forecast_rationale_section_watch",
    "aggregate_context_watch",
    "open_context_gap_watch",
    _WATCH_REASON,
    _PASS_REASON,
    _NO_CONTEXTS_REASON,
)
_ROW_REASON_CODES = tuple(
    reason
    for reason in _REASON_PRIORITY
    if reason not in {_WATCH_REASON, _BLOCK_REASON, _NO_CONTEXTS_REASON}
)
_REPORT_REASON_CODES = _REASON_PRIORITY
_UNSAFE_PUBLIC_TEXT_FRAGMENTS = (
    "candidate" "_" "id",
    "candidate-id",
    "market" "_" "id",
    "market-id",
    "market" "_" "slug",
    "slug",
    "question",
    "source" "_" "text",
    "source-url",
    "source" "_" "url",
    "http" "://",
    "https" "://",
    "://",
    "dsn",
    "table" "_" "name",
    "token",
    "wal" "let",
    "au" "th",
    "or" "der",
    "tr" "ade",
    "private" "_" "key",
    "b" "uy",
    "se" "ll",
    "reco" "mmend",
    "position" "_" "size",
    "siz" "ing",
)

__all__ = (
    "DEFAULT_RESEARCH_STRATEGY_MARKET_CONTEXT_COMPLETENESS_REPORT_CONFIG_VERSION",
    "ResearchStrategyMarketContextCompletenessConfig",
    "ResearchStrategyMarketContextCompletenessInput",
    "ResearchStrategyMarketContextCompletenessRow",
    "ResearchStrategyMarketContextCompletenessReport",
    "build_research_strategy_market_context_completeness_report",
    "research_strategy_market_context_completeness_report_payload",
    "validate_research_strategy_market_context_completeness_report_payload",
)


class _FinalPublicDataclass:
    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls.__bases__ != (_FinalPublicDataclass,):
            raise TypeError("public dataclasses do not support subclassing")
        if not cls.__name__.startswith("ResearchStrategyMarketContextCompleteness"):
            raise TypeError("public dataclasses do not support subclassing")


@dataclass(frozen=True)
class ResearchStrategyMarketContextCompletenessConfig(_FinalPublicDataclass):
    config_version: str = (
        DEFAULT_RESEARCH_STRATEGY_MARKET_CONTEXT_COMPLETENESS_REPORT_CONFIG_VERSION
    )
    min_sanitized_evidence_count: Decimal = Decimal("4.000000")
    sanitized_evidence_count_pass_floor: Decimal = Decimal("6.000000")
    min_independent_family_count: Decimal = Decimal("2.000000")
    independent_family_count_pass_floor: Decimal = Decimal("3.000000")
    section_watch_floor: Decimal = Decimal("0.700000")
    section_block_floor: Decimal = Decimal("0.400000")
    aggregate_watch_floor: Decimal = Decimal("0.750000")
    aggregate_block_floor: Decimal = Decimal("0.500000")
    open_context_gap_watch_ceiling: Decimal = Decimal("0.000000")
    open_context_gap_block_ceiling: Decimal = Decimal("2.000000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchStrategyMarketContextCompletenessConfig,
            "config",
        )
        object.__setattr__(
            self,
            "config_version",
            _require_public_string("config_version", self.config_version),
        )
        for field_name in (
            "min_sanitized_evidence_count",
            "sanitized_evidence_count_pass_floor",
            "min_independent_family_count",
            "independent_family_count_pass_floor",
            "open_context_gap_watch_ceiling",
            "open_context_gap_block_ceiling",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_count(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "section_watch_floor",
            "section_block_floor",
            "aggregate_watch_floor",
            "aggregate_block_floor",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio(field_name, getattr(self, field_name)),
            )
        _require_at_least(
            "sanitized_evidence_count_pass_floor",
            self.sanitized_evidence_count_pass_floor,
            self.min_sanitized_evidence_count,
        )
        _require_at_least(
            "independent_family_count_pass_floor",
            self.independent_family_count_pass_floor,
            self.min_independent_family_count,
        )
        _require_at_least(
            "section_watch_floor",
            self.section_watch_floor,
            self.section_block_floor,
        )
        _require_at_least(
            "aggregate_watch_floor",
            self.aggregate_watch_floor,
            self.aggregate_block_floor,
        )
        _require_at_most(
            "open_context_gap_watch_ceiling",
            self.open_context_gap_watch_ceiling,
            self.open_context_gap_block_ceiling,
        )
        _require_hard_flags("config", self)
        _reject_unsafe_public_payload("config", _payload_value(self))


@dataclass(frozen=True)
class ResearchStrategyMarketContextCompletenessInput(_FinalPublicDataclass):
    review_label: str
    sanitized_evidence_count: Decimal
    independent_family_count: Decimal
    evidence_section_completeness: Decimal
    cost_section_completeness: Decimal
    settlement_rule_section_completeness: Decimal
    domain_memory_section_completeness: Decimal
    forecast_rationale_section_completeness: Decimal
    open_context_gap_count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchStrategyMarketContextCompletenessInput, "input")
        object.__setattr__(
            self,
            "review_label",
            _require_public_string("review_label", self.review_label),
        )
        for field_name in (
            "sanitized_evidence_count",
            "independent_family_count",
            "open_context_gap_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_count(field_name, getattr(self, field_name)),
            )
        if self.independent_family_count > self.sanitized_evidence_count:
            raise ValueError(
                "independent_family_count must not exceed sanitized_evidence_count",
            )
        for field_name in (
            "evidence_section_completeness",
            "cost_section_completeness",
            "settlement_rule_section_completeness",
            "domain_memory_section_completeness",
            "forecast_rationale_section_completeness",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio(field_name, getattr(self, field_name)),
            )
        _require_hard_flags("input", self)
        _reject_unsafe_public_payload("input", _payload_value(self))


@dataclass(frozen=True)
class ResearchStrategyMarketContextCompletenessRow(_FinalPublicDataclass):
    review_rank: Decimal
    review_label: str
    sanitized_evidence_count: Decimal
    independent_family_count: Decimal
    evidence_count_ratio: Decimal
    independent_family_ratio: Decimal
    evidence_section_completeness: Decimal
    cost_section_completeness: Decimal
    settlement_rule_section_completeness: Decimal
    domain_memory_section_completeness: Decimal
    forecast_rationale_section_completeness: Decimal
    open_context_gap_count: Decimal
    context_completeness_score: Decimal
    status: str
    manual_review_state: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchStrategyMarketContextCompletenessRow, "row")
        object.__setattr__(self, "review_rank", _require_positive_count("review_rank", self.review_rank))
        object.__setattr__(
            self,
            "review_label",
            _require_public_string("review_label", self.review_label),
        )
        for field_name in (
            "sanitized_evidence_count",
            "independent_family_count",
            "open_context_gap_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_count(field_name, getattr(self, field_name)),
            )
        if self.independent_family_count > self.sanitized_evidence_count:
            raise ValueError(
                "independent_family_count must not exceed sanitized_evidence_count",
            )
        for field_name in (
            "evidence_count_ratio",
            "independent_family_ratio",
            "evidence_section_completeness",
            "cost_section_completeness",
            "settlement_rule_section_completeness",
            "domain_memory_section_completeness",
            "forecast_rationale_section_completeness",
            "context_completeness_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio(field_name, getattr(self, field_name)),
            )
        _require_status("status", self.status)
        _require_manual_review_state("manual_review_state", self.manual_review_state)
        object.__setattr__(
            self,
            "reason_codes",
            _require_reason_codes("reason_codes", self.reason_codes, _ROW_REASON_CODES),
        )
        _require_hard_flags("row", self)
        _reject_unsafe_public_payload("row", _payload_value(self))
        _validate_row(self)


@dataclass(frozen=True)
class ResearchStrategyMarketContextCompletenessReport(_FinalPublicDataclass):
    generated_at: datetime
    config_version: str
    context_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    min_context_completeness_score: Decimal | None
    average_context_completeness_score: Decimal
    status: str
    manual_review_state: str
    reason_codes: tuple[str, ...]
    rows: tuple[ResearchStrategyMarketContextCompletenessRow, ...]
    derived_validation_digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchStrategyMarketContextCompletenessReport, "report")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        object.__setattr__(
            self,
            "config_version",
            _require_public_string("config_version", self.config_version),
        )
        for field_name in ("context_count", "pass_count", "watch_count", "block_count"):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_count(field_name, getattr(self, field_name)),
            )
        if self.min_context_completeness_score is not None:
            object.__setattr__(
                self,
                "min_context_completeness_score",
                _require_ratio(
                    "min_context_completeness_score",
                    self.min_context_completeness_score,
                ),
            )
        object.__setattr__(
            self,
            "average_context_completeness_score",
            _require_ratio(
                "average_context_completeness_score",
                self.average_context_completeness_score,
            ),
        )
        _require_status("status", self.status)
        _require_manual_review_state("manual_review_state", self.manual_review_state)
        object.__setattr__(self, "rows", _require_rows(self.rows))
        object.__setattr__(
            self,
            "reason_codes",
            _require_reason_codes("reason_codes", self.reason_codes, _REPORT_REASON_CODES),
        )
        _require_digest("derived_validation_digest", self.derived_validation_digest)
        _require_hard_flags("report", self)
        _reject_unsafe_public_payload("report", _payload_value(self))
        _validate_report(self)
        _require_matching_digest(_payload_value(self))


def build_research_strategy_market_context_completeness_report(
    inputs: Iterable[ResearchStrategyMarketContextCompletenessInput],
    *,
    config: ResearchStrategyMarketContextCompletenessConfig | None = None,
    generated_at: datetime,
) -> ResearchStrategyMarketContextCompletenessReport:
    cfg = config or ResearchStrategyMarketContextCompletenessConfig()
    if type(cfg) is not ResearchStrategyMarketContextCompletenessConfig:
        raise ValueError(
            "config must be exactly ResearchStrategyMarketContextCompletenessConfig",
        )
    _require_hard_flags("config", cfg)
    generated_at_utc = _as_utc("generated_at", generated_at)
    normalized = _normalize_inputs(inputs)
    row_values = tuple(_row_values(value, config=cfg) for value in normalized)
    sorted_values = tuple(sorted(row_values, key=_row_values_sort_key))
    rows = tuple(
        ResearchStrategyMarketContextCompletenessRow(
            review_rank=_count_decimal(index),
            **values,
        )
        for index, values in enumerate(sorted_values, start=1)
    )
    status = _report_status(rows)
    values: dict[str, Any] = {
        "generated_at": generated_at_utc,
        "config_version": cfg.config_version,
        "context_count": _count_decimal(len(rows)),
        "pass_count": _status_count(rows, _STATUS_PASS),
        "watch_count": _status_count(rows, _STATUS_WATCH),
        "block_count": _status_count(rows, _STATUS_BLOCK),
        "min_context_completeness_score": (
            None if not rows else min(row.context_completeness_score for row in rows)
        ),
        "average_context_completeness_score": _average(
            row.context_completeness_score for row in rows
        ),
        "status": status,
        "manual_review_state": _manual_review_state(status),
        "reason_codes": _report_reason_codes(rows),
        "rows": rows,
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    payload = _payload_value(values)
    if type(payload) is not dict:
        raise ValueError("payload must be a dict")
    values["derived_validation_digest"] = _derived_validation_digest(payload)
    return ResearchStrategyMarketContextCompletenessReport(**values)


def research_strategy_market_context_completeness_report_payload(
    report: ResearchStrategyMarketContextCompletenessReport | dict[str, Any],
) -> dict[str, Any]:
    if type(report) is ResearchStrategyMarketContextCompletenessReport:
        _require_hard_flags("report", report)
        payload = _payload_value(report)
    elif type(report) is dict:
        payload = _payload_value(report)
    else:
        raise ValueError(
            "report must be exactly ResearchStrategyMarketContextCompletenessReport",
        )
    if type(payload) is not dict:
        raise ValueError("payload must be a dict")
    _reject_unsafe_public_payload("payload", payload)
    _require_payload_hard_flags(payload)
    _require_matching_digest(payload)
    return payload


def validate_research_strategy_market_context_completeness_report_payload(
    payload: dict[str, Any],
) -> bool:
    if type(payload) is not dict:
        raise ValueError("public payload must be a dict")
    ready = _payload_value(payload)
    if type(ready) is not dict:
        raise ValueError("public payload must be a dict")
    _reject_unsafe_public_payload("payload", ready)
    _require_payload_hard_flags(ready)
    _require_matching_digest(ready)
    return True


def _row_values(
    value: ResearchStrategyMarketContextCompletenessInput,
    *,
    config: ResearchStrategyMarketContextCompletenessConfig,
) -> dict[str, Any]:
    evidence_count_ratio = _capped_ratio(
        value.sanitized_evidence_count,
        config.sanitized_evidence_count_pass_floor,
    )
    independent_family_ratio = _capped_ratio(
        value.independent_family_count,
        config.independent_family_count_pass_floor,
    )
    context_completeness_score = _context_completeness_score(
        (
            evidence_count_ratio,
            independent_family_ratio,
            value.evidence_section_completeness,
            value.cost_section_completeness,
            value.settlement_rule_section_completeness,
            value.domain_memory_section_completeness,
            value.forecast_rationale_section_completeness,
        ),
    )
    reason_codes = _row_reason_codes(
        value,
        context_completeness_score=context_completeness_score,
        config=config,
    )
    status = _row_status(reason_codes)
    return {
        "review_label": value.review_label,
        "sanitized_evidence_count": value.sanitized_evidence_count,
        "independent_family_count": value.independent_family_count,
        "evidence_count_ratio": evidence_count_ratio,
        "independent_family_ratio": independent_family_ratio,
        "evidence_section_completeness": value.evidence_section_completeness,
        "cost_section_completeness": value.cost_section_completeness,
        "settlement_rule_section_completeness": (
            value.settlement_rule_section_completeness
        ),
        "domain_memory_section_completeness": value.domain_memory_section_completeness,
        "forecast_rationale_section_completeness": (
            value.forecast_rationale_section_completeness
        ),
        "open_context_gap_count": value.open_context_gap_count,
        "context_completeness_score": context_completeness_score,
        "status": status,
        "manual_review_state": _manual_review_state(status),
        "reason_codes": reason_codes,
    }


def _row_reason_codes(
    value: ResearchStrategyMarketContextCompletenessInput,
    *,
    context_completeness_score: Decimal,
    config: ResearchStrategyMarketContextCompletenessConfig,
) -> tuple[str, ...]:
    block_reasons: list[str] = []
    watch_reasons: list[str] = []
    if value.sanitized_evidence_count < config.min_sanitized_evidence_count:
        block_reasons.append("sanitized_evidence_count_block")
    elif value.sanitized_evidence_count < config.sanitized_evidence_count_pass_floor:
        watch_reasons.append("sanitized_evidence_count_watch")
    if value.independent_family_count < config.min_independent_family_count:
        block_reasons.append("independent_family_count_block")
    elif value.independent_family_count < config.independent_family_count_pass_floor:
        watch_reasons.append("independent_family_count_watch")
    _append_section_reason(
        "evidence_section",
        value.evidence_section_completeness,
        block_reasons=block_reasons,
        watch_reasons=watch_reasons,
        config=config,
    )
    _append_section_reason(
        "cost_section",
        value.cost_section_completeness,
        block_reasons=block_reasons,
        watch_reasons=watch_reasons,
        config=config,
    )
    _append_section_reason(
        "settlement_rule_section",
        value.settlement_rule_section_completeness,
        block_reasons=block_reasons,
        watch_reasons=watch_reasons,
        config=config,
    )
    _append_section_reason(
        "domain_memory_section",
        value.domain_memory_section_completeness,
        block_reasons=block_reasons,
        watch_reasons=watch_reasons,
        config=config,
    )
    _append_section_reason(
        "forecast_rationale_section",
        value.forecast_rationale_section_completeness,
        block_reasons=block_reasons,
        watch_reasons=watch_reasons,
        config=config,
    )
    if context_completeness_score < config.aggregate_block_floor:
        block_reasons.append("aggregate_context_block")
    elif context_completeness_score < config.aggregate_watch_floor:
        watch_reasons.append("aggregate_context_watch")
    if value.open_context_gap_count >= config.open_context_gap_block_ceiling:
        block_reasons.append("open_context_gap_block")
    elif value.open_context_gap_count > config.open_context_gap_watch_ceiling:
        watch_reasons.append("open_context_gap_watch")
    reason_codes = tuple(block_reasons + watch_reasons)
    if not reason_codes:
        reason_codes = (_PASS_REASON,)
    return _require_reason_codes("reason_codes", reason_codes, _ROW_REASON_CODES)


def _append_section_reason(
    section_name: str,
    value: Decimal,
    *,
    block_reasons: list[str],
    watch_reasons: list[str],
    config: ResearchStrategyMarketContextCompletenessConfig,
) -> None:
    if value < config.section_block_floor:
        block_reasons.append(f"{section_name}_block")
    elif value < config.section_watch_floor:
        watch_reasons.append(f"{section_name}_watch")


def _row_status(reason_codes: tuple[str, ...]) -> str:
    if any(reason_code.endswith("_block") for reason_code in reason_codes):
        return _STATUS_BLOCK
    if any(reason_code.endswith("_watch") for reason_code in reason_codes):
        return _STATUS_WATCH
    return _STATUS_PASS


def _report_status(
    rows: tuple[ResearchStrategyMarketContextCompletenessRow, ...],
) -> str:
    if not rows:
        return _STATUS_BLOCK
    if any(row.status == _STATUS_BLOCK for row in rows):
        return _STATUS_BLOCK
    if any(row.status == _STATUS_WATCH for row in rows):
        return _STATUS_WATCH
    return _STATUS_PASS


def _manual_review_state(status: str) -> str:
    if status == _STATUS_BLOCK:
        return "manual_review_block"
    if status == _STATUS_WATCH:
        return "manual_review_watch"
    return "manual_review_ready"


def _report_reason_codes(
    rows: tuple[ResearchStrategyMarketContextCompletenessRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return (_NO_CONTEXTS_REASON,)
    status = _report_status(rows)
    reason_codes = tuple(
        reason_code
        for row in rows
        for reason_code in row.reason_codes
        if reason_code != _PASS_REASON
    )
    if status == _STATUS_BLOCK:
        reason_codes = (*reason_codes, _BLOCK_REASON)
    elif status == _STATUS_WATCH:
        reason_codes = (*reason_codes, _WATCH_REASON)
    else:
        reason_codes = (_PASS_REASON,)
    return _require_reason_codes("reason_codes", reason_codes, _REPORT_REASON_CODES)


def _context_completeness_score(values: tuple[Decimal, ...]) -> Decimal:
    if len(values) != 7:
        raise ValueError("context score requires seven components")
    return _ratio(_sum_decimals(values), _SEVEN)


def _row_values_sort_key(values: dict[str, Any]) -> tuple[Decimal, Decimal, str]:
    status = values["status"]
    score = values["context_completeness_score"]
    label = values["review_label"]
    if type(status) is not str or type(score) is not Decimal or type(label) is not str:
        raise ValueError("row values are not sortable")
    return (_STATUS_WEIGHT[status], score, label)


def _row_sort_key(
    row: ResearchStrategyMarketContextCompletenessRow,
) -> tuple[Decimal, Decimal, str]:
    return (_STATUS_WEIGHT[row.status], row.context_completeness_score, row.review_label)


def _normalize_inputs(
    inputs: Iterable[ResearchStrategyMarketContextCompletenessInput],
) -> tuple[ResearchStrategyMarketContextCompletenessInput, ...]:
    if isinstance(inputs, (str, bytes)) or not isinstance(inputs, Iterable):
        raise ValueError("inputs must be an iterable")
    normalized = tuple(inputs)
    seen: set[str] = set()
    for value in normalized:
        if type(value) is not ResearchStrategyMarketContextCompletenessInput:
            raise ValueError(
                "inputs must contain ResearchStrategyMarketContextCompletenessInput",
            )
        _require_hard_flags("input", value)
        if value.review_label in seen:
            raise ValueError("review_label values must be unique")
        seen.add(value.review_label)
    return normalized


def _require_rows(
    rows: Iterable[ResearchStrategyMarketContextCompletenessRow],
) -> tuple[ResearchStrategyMarketContextCompletenessRow, ...]:
    if isinstance(rows, (str, bytes)) or not isinstance(rows, Iterable):
        raise ValueError("rows must be an iterable")
    normalized = tuple(rows)
    seen: set[str] = set()
    for row in normalized:
        if type(row) is not ResearchStrategyMarketContextCompletenessRow:
            raise ValueError(
                "rows must contain ResearchStrategyMarketContextCompletenessRow",
            )
        _require_hard_flags("row", row)
        if row.review_label in seen:
            raise ValueError("row review_label values must be unique")
        seen.add(row.review_label)
    if normalized != tuple(sorted(normalized, key=_row_sort_key)):
        raise ValueError("rows must be sorted deterministically")
    return normalized


def _validate_row(row: ResearchStrategyMarketContextCompletenessRow) -> None:
    expected_score = _context_completeness_score(
        (
            row.evidence_count_ratio,
            row.independent_family_ratio,
            row.evidence_section_completeness,
            row.cost_section_completeness,
            row.settlement_rule_section_completeness,
            row.domain_memory_section_completeness,
            row.forecast_rationale_section_completeness,
        ),
    )
    if row.context_completeness_score != expected_score:
        raise ValueError("context_completeness_score must match component scores")
    if row.status != _row_status(row.reason_codes):
        raise ValueError("status must match reason_codes")
    if row.manual_review_state != _manual_review_state(row.status):
        raise ValueError("manual_review_state must match status")


def _validate_report(report: ResearchStrategyMarketContextCompletenessReport) -> None:
    if report.context_count != _count_decimal(len(report.rows)):
        raise ValueError("context_count must match rows")
    if report.pass_count != _status_count(report.rows, _STATUS_PASS):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _status_count(report.rows, _STATUS_WATCH):
        raise ValueError("watch_count must match rows")
    if report.block_count != _status_count(report.rows, _STATUS_BLOCK):
        raise ValueError("block_count must match rows")
    expected_min = (
        None if not report.rows else min(row.context_completeness_score for row in report.rows)
    )
    if report.min_context_completeness_score != expected_min:
        raise ValueError("min_context_completeness_score must match rows")
    if report.average_context_completeness_score != _average(
        row.context_completeness_score for row in report.rows
    ):
        raise ValueError("average_context_completeness_score must match rows")
    if report.status != _report_status(report.rows):
        raise ValueError("status must match rows")
    if report.manual_review_state != _manual_review_state(report.status):
        raise ValueError("manual_review_state must match status")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")


def _status_count(
    rows: tuple[ResearchStrategyMarketContextCompletenessRow, ...],
    status: str,
) -> Decimal:
    return _count_decimal(sum(1 for row in rows if row.status == status))


def _average(values: Iterable[Decimal]) -> Decimal:
    normalized = tuple(values)
    if not normalized:
        return _ZERO
    return _ratio(_sum_decimals(normalized), _count_decimal(len(normalized)))


def _sum_decimals(values: Iterable[Decimal]) -> Decimal:
    total = _ZERO
    with localcontext(_DECIMAL_CONTEXT):
        for value in values:
            total += _require_decimal("sum value", value)
    return _six(total)


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    numerator = _require_decimal("numerator", numerator)
    denominator = _require_decimal("denominator", denominator)
    if denominator <= _ZERO:
        raise ValueError("denominator must be positive")
    with localcontext(_DECIMAL_CONTEXT):
        return _six(numerator / denominator)


def _capped_ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    value = _ratio(numerator, denominator)
    if value > _ONE:
        return _ONE
    return value


def _count_decimal(value: int) -> Decimal:
    if type(value) is not int or value < 0:
        raise ValueError("count must be a nonnegative int")
    return _six(Decimal(value))


def _require_nonnegative_count(name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(name, value)
    if decimal_value < _ZERO:
        raise ValueError(f"{name} must be nonnegative")
    if decimal_value != decimal_value.to_integral_value():
        raise ValueError(f"{name} must be an integer Decimal")
    return decimal_value


def _require_positive_count(name: str, value: object) -> Decimal:
    decimal_value = _require_nonnegative_count(name, value)
    if decimal_value <= _ZERO:
        raise ValueError(f"{name} must be positive")
    return decimal_value


def _require_ratio(name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(name, value)
    if decimal_value < _ZERO or decimal_value > _ONE:
        raise ValueError(f"{name} must be between 0 and 1")
    return decimal_value


def _require_decimal(name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{name} must be finite")
    return _six(value)


def _six(value: Decimal) -> Decimal:
    with localcontext(_DECIMAL_CONTEXT):
        return value.quantize(_QUANTUM)


def _as_utc(name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_exact_type(value: object, expected_type: type[object], name: str) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{name} must be exactly {expected_type.__name__}")


def _require_at_least(name: str, value: Decimal, floor: Decimal) -> None:
    if value < floor:
        raise ValueError(f"{name} must be at least its paired floor")


def _require_at_most(name: str, value: Decimal, ceiling: Decimal) -> None:
    if value > ceiling:
        raise ValueError(f"{name} must be at most its paired ceiling")


def _require_status(name: str, value: object) -> None:
    if type(value) is not str or value not in _STATUSES:
        raise ValueError(f"{name} must be pass, watch, or block")


def _require_manual_review_state(name: str, value: object) -> None:
    if type(value) is not str or value not in {
        "manual_review_ready",
        "manual_review_watch",
        "manual_review_block",
    }:
        raise ValueError(f"{name} must be a manual review state")


def _require_public_string(name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{name} must be a string")
    if not value:
        raise ValueError(f"{name} must be non-empty")
    if value.strip() != value:
        raise ValueError(f"{name} must be canonical")
    if "\n" in value or "\r" in value or "\t" in value:
        raise ValueError(f"{name} must be canonical")
    _require_safe_public_text(name, value)
    return value


def _require_safe_public_text(name: str, value: str) -> None:
    normalized = value.lower()
    if any(fragment in normalized for fragment in _UNSAFE_PUBLIC_TEXT_FRAGMENTS):
        raise ValueError(f"{name} contains unsafe public surface")


def _require_reason_codes(
    name: str,
    values: Iterable[str],
    allowed: tuple[str, ...],
) -> tuple[str, ...]:
    if isinstance(values, (str, bytes)) or not isinstance(values, Iterable):
        raise ValueError(f"{name} must be an iterable")
    normalized = tuple(values)
    if not normalized:
        raise ValueError(f"{name} must not be empty")
    for value in normalized:
        if type(value) is not str or value not in allowed:
            raise ValueError(f"{name} must contain known reason codes")
    return tuple(sorted(dict.fromkeys(normalized), key=_reason_sort_key))


def _reason_sort_key(reason_code: str) -> tuple[int, str]:
    if reason_code in _REASON_PRIORITY:
        return (_REASON_PRIORITY.index(reason_code), reason_code)
    return (len(_REASON_PRIORITY), reason_code)


def _require_digest(name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{name} must be a string")
    if len(value) != 64 or any(character not in "0123456789abcdef" for character in value):
        raise ValueError(f"{name} must be a sha256 hex digest")


def _require_hard_flags(label: str, value: object) -> None:
    if getattr(value, "paper_only", None) is not True:
        raise ValueError(f"{label} paper_only must be True")
    if getattr(value, "report_only", None) is not True:
        raise ValueError(f"{label} report_only must be True")
    if getattr(value, "readonly", None) is not True:
        raise ValueError(f"{label} readonly must be True")


def _require_payload_hard_flags(payload: dict[str, Any]) -> None:
    for key in ("paper_only", "report_only", "readonly"):
        if payload.get(key) is not True:
            raise ValueError(f"payload {key} must be True")


def _payload_value(value: Any) -> Any:
    if type(value) is Decimal:
        if not value.is_finite():
            raise ValueError("Decimal value must be finite")
        return str(_six(value))
    if isinstance(value, Decimal):
        raise ValueError("Decimal value must be exactly Decimal")
    if type(value) is datetime:
        return _as_utc("datetime", value).isoformat()
    if isinstance(value, datetime):
        raise ValueError("datetime value must be exactly datetime")
    if is_dataclass(value) and not isinstance(value, type):
        return {field.name: _payload_value(getattr(value, field.name)) for field in fields(value)}
    if isinstance(value, (tuple, list)):
        return [_payload_value(item) for item in value]
    if isinstance(value, Mapping):
        ready: dict[str, Any] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("public payload keys must be strings")
            ready[key] = _payload_value(item)
        return ready
    if type(value) in (int, float):
        raise ValueError("public payload must use Decimal strings")
    if type(value) is str:
        _require_safe_public_text("public payload value", value)
        return value
    if value is None or type(value) is bool:
        return value
    raise ValueError("public payload contains unsupported value")


def _reject_unsafe_public_payload(label: str, value: object, path: str = "") -> None:
    if isinstance(value, Mapping):
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("public payload keys must be strings")
            nested_path = key if not path else f"{path}.{key}"
            _require_safe_public_text(f"{label} key", key)
            if key in {"paper_only", "report_only", "readonly"} and item is not True:
                raise ValueError(f"payload {key} must be True")
            _reject_unsafe_public_payload(label, item, nested_path)
        return
    if isinstance(value, (list, tuple)):
        for index, item in enumerate(value):
            nested_path = f"{path}[{index}]" if path else f"{label}[{index}]"
            _reject_unsafe_public_payload(label, item, nested_path)
        return
    if type(value) is str:
        _require_safe_public_text(path or label, value)
        return
    if type(value) in (int, float):
        raise ValueError("public payload must use Decimal strings")
    if value is None or type(value) is bool:
        return
    raise ValueError("public payload contains unsupported value")


def _derived_validation_digest(payload: dict[str, Any]) -> str:
    material = {
        key: value
        for key, value in payload.items()
        if key != "derived_validation_digest"
    }
    encoded = json.dumps(material, sort_keys=True, separators=(",", ":"))
    return sha256(encoded.encode("utf-8")).hexdigest()


def _require_matching_digest(payload: dict[str, Any]) -> None:
    if "derived_validation_digest" not in payload:
        raise ValueError("derived_validation_digest is required")
    _require_digest("derived_validation_digest", payload["derived_validation_digest"])
    if payload["derived_validation_digest"] != _derived_validation_digest(payload):
        raise ValueError("derived_validation_digest does not match report payload")
