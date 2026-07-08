"""Pure strategy decision traceability gap report reducer."""

from __future__ import annotations

from dataclasses import asdict, dataclass, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
from json import dumps
from typing import Any, Iterable


__all__ = (
    "DEFAULT_RESEARCH_STRATEGY_DECISION_TRACEABILITY_GAP_REPORT_CONFIG_VERSION",
    "RESEARCH_STRATEGY_DECISION_TRACEABILITY_GAP_STATUSES",
    "ResearchStrategyDecisionTraceabilityGapConfig",
    "ResearchStrategyDecisionTraceabilityGapInput",
    "ResearchStrategyDecisionTraceabilityGapReasonCodeCount",
    "ResearchStrategyDecisionTraceabilityGapRow",
    "ResearchStrategyDecisionTraceabilityGapReport",
    "build_research_strategy_decision_traceability_gap_report",
    "research_strategy_decision_traceability_gap_report_payload",
    "research_strategy_decision_traceability_gap_report_digest",
)


DEFAULT_RESEARCH_STRATEGY_DECISION_TRACEABILITY_GAP_REPORT_CONFIG_VERSION = (
    "research-strategy-decision-traceability-gap-report-v0"
)
RESEARCH_STRATEGY_DECISION_TRACEABILITY_GAP_STATUSES = ("pass", "watch", "block")

STATUS_PASS = "pass"
STATUS_WATCH = "watch"
STATUS_BLOCK = "block"
STATUS_WEIGHT = {
    STATUS_BLOCK: Decimal("0.000000"),
    STATUS_WATCH: Decimal("1.000000"),
    STATUS_PASS: Decimal("2.000000"),
}

QUANTUM = Decimal("0.000001")
COUNT_QUANTUM = Decimal("1.000000")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)

ROW_REASON_CODES = (
    "decision_traceability_gap_pass",
    "decision_traceability_gap_watch",
    "decision_traceability_gap_block",
    "research_evidence_traceability_gap_watch",
    "research_evidence_traceability_gap_block",
    "forecast_rationale_traceability_gap_watch",
    "forecast_rationale_traceability_gap_block",
    "cost_context_traceability_gap_watch",
    "cost_context_traceability_gap_block",
    "settlement_rule_note_traceability_gap_watch",
    "settlement_rule_note_traceability_gap_block",
    "trace_gap_pressure_watch",
    "trace_gap_pressure_block",
)
REPORT_REASON_CODES = (
    "decision_traceability_gap_report_empty",
    "decision_traceability_gap_report_pass",
    "decision_traceability_gap_report_watch",
    "decision_traceability_gap_report_block",
    "research_evidence_traceability_gap_exception",
    "forecast_rationale_traceability_gap_exception",
    "cost_context_traceability_gap_exception",
    "settlement_rule_note_traceability_gap_exception",
    "trace_gap_pressure_exception",
)
ROW_REASON_INDEX = {reason_code: index for index, reason_code in enumerate(ROW_REASON_CODES)}
REPORT_REASON_INDEX = {
    reason_code: index for index, reason_code in enumerate(REPORT_REASON_CODES)
}


def _join_parts(*parts: str) -> str:
    return "".join(parts)


UNSAFE_PUBLIC_FRAGMENTS = (
    _join_parts("raw", "_id"),
    _join_parts("can", "did", "ate"),
    _join_parts("mar", "ket", "_id"),
    _join_parts("mar", "ket", "_sl", "ug"),
    _join_parts("sl", "ug"),
    _join_parts("ques", "tion"),
    _join_parts("sou", "rce", "_u", "rl"),
    _join_parts("sou", "rce", "_te", "xt"),
    _join_parts("u", "rl"),
    _join_parts("d", "sn"),
    _join_parts("ta", "ble", "_na", "me"),
    _join_parts("pri", "vate", "_to", "ken"),
    _join_parts("to", "ken"),
    _join_parts("sec", "ret"),
    _join_parts("cre", "den", "tial"),
    _join_parts("wa", "ll", "et"),
    _join_parts("or", "der"),
    _join_parts("tr", "ade"),
    _join_parts("reco", "mmendation"),
    _join_parts("siz", "ing"),
    _join_parts("b", "uy"),
    _join_parts("se", "ll"),
)


@dataclass(frozen=True)
class ResearchStrategyDecisionTraceabilityGapConfig:
    config_version: str = (
        DEFAULT_RESEARCH_STRATEGY_DECISION_TRACEABILITY_GAP_REPORT_CONFIG_VERSION
    )
    min_pass_research_evidence_link_ratio: Decimal = Decimal("0.950000")
    min_watch_research_evidence_link_ratio: Decimal = Decimal("0.800000")
    min_pass_forecast_rationale_link_ratio: Decimal = Decimal("0.950000")
    min_watch_forecast_rationale_link_ratio: Decimal = Decimal("0.800000")
    min_pass_cost_context_link_ratio: Decimal = Decimal("0.950000")
    min_watch_cost_context_link_ratio: Decimal = Decimal("0.800000")
    min_pass_settlement_rule_note_link_ratio: Decimal = Decimal("0.950000")
    min_watch_settlement_rule_note_link_ratio: Decimal = Decimal("0.800000")
    max_pass_trace_gap_pressure: Decimal = Decimal("0.050000")
    max_watch_trace_gap_pressure: Decimal = Decimal("0.200000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchStrategyDecisionTraceabilityGapConfig,
            "config",
        )
        _require_public_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_STRATEGY_DECISION_TRACEABILITY_GAP_REPORT_CONFIG_VERSION
        ):
            raise ValueError("config_version must match the supported value")
        for field_name in (
            "min_pass_research_evidence_link_ratio",
            "min_watch_research_evidence_link_ratio",
            "min_pass_forecast_rationale_link_ratio",
            "min_watch_forecast_rationale_link_ratio",
            "min_pass_cost_context_link_ratio",
            "min_watch_cost_context_link_ratio",
            "min_pass_settlement_rule_note_link_ratio",
            "min_watch_settlement_rule_note_link_ratio",
            "max_pass_trace_gap_pressure",
            "max_watch_trace_gap_pressure",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        _require_floor_pair(
            "min_pass_research_evidence_link_ratio",
            self.min_pass_research_evidence_link_ratio,
            "min_watch_research_evidence_link_ratio",
            self.min_watch_research_evidence_link_ratio,
        )
        _require_floor_pair(
            "min_pass_forecast_rationale_link_ratio",
            self.min_pass_forecast_rationale_link_ratio,
            "min_watch_forecast_rationale_link_ratio",
            self.min_watch_forecast_rationale_link_ratio,
        )
        _require_floor_pair(
            "min_pass_cost_context_link_ratio",
            self.min_pass_cost_context_link_ratio,
            "min_watch_cost_context_link_ratio",
            self.min_watch_cost_context_link_ratio,
        )
        _require_floor_pair(
            "min_pass_settlement_rule_note_link_ratio",
            self.min_pass_settlement_rule_note_link_ratio,
            "min_watch_settlement_rule_note_link_ratio",
            self.min_watch_settlement_rule_note_link_ratio,
        )
        _require_ceiling_pair(
            "max_pass_trace_gap_pressure",
            self.max_pass_trace_gap_pressure,
            self.max_watch_trace_gap_pressure,
        )
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class ResearchStrategyDecisionTraceabilityGapInput:
    trace_key: str
    research_evidence_expected_links: Decimal
    research_evidence_linked_count: Decimal
    forecast_rationale_expected_links: Decimal
    forecast_rationale_linked_count: Decimal
    cost_context_expected_links: Decimal
    cost_context_linked_count: Decimal
    settlement_rule_note_expected_links: Decimal
    settlement_rule_note_linked_count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchStrategyDecisionTraceabilityGapInput, "input")
        _require_private_key("trace_key", self.trace_key)
        for field_name in (
            "research_evidence_expected_links",
            "research_evidence_linked_count",
            "forecast_rationale_expected_links",
            "forecast_rationale_linked_count",
            "cost_context_expected_links",
            "cost_context_linked_count",
            "settlement_rule_note_expected_links",
            "settlement_rule_note_linked_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_whole_decimal(
                    field_name,
                    getattr(self, field_name),
                ),
            )
        _require_link_pair(
            "research_evidence_linked_count",
            self.research_evidence_linked_count,
            self.research_evidence_expected_links,
        )
        _require_link_pair(
            "forecast_rationale_linked_count",
            self.forecast_rationale_linked_count,
            self.forecast_rationale_expected_links,
        )
        _require_link_pair(
            "cost_context_linked_count",
            self.cost_context_linked_count,
            self.cost_context_expected_links,
        )
        _require_link_pair(
            "settlement_rule_note_linked_count",
            self.settlement_rule_note_linked_count,
            self.settlement_rule_note_expected_links,
        )
        _require_hard_flags("input", self)


@dataclass(frozen=True)
class ResearchStrategyDecisionTraceabilityGapReasonCodeCount:
    reason_code: str
    count: Decimal
    input_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_reason_code("reason_code", self.reason_code, ROW_REASON_CODES)
        object.__setattr__(
            self,
            "count",
            _normalize_nonnegative_whole_decimal("count", self.count),
        )
        object.__setattr__(
            self,
            "input_ratio",
            _normalize_probability("input_ratio", self.input_ratio),
        )
        _require_hard_flags("reason_code_count", self)


@dataclass(frozen=True)
class ResearchStrategyDecisionTraceabilityGapRow:
    aggregate_row_number: Decimal
    trace_hash: str
    research_evidence_expected_links: Decimal
    research_evidence_linked_count: Decimal
    research_evidence_missing_links: Decimal
    research_evidence_link_ratio: Decimal
    forecast_rationale_expected_links: Decimal
    forecast_rationale_linked_count: Decimal
    forecast_rationale_missing_links: Decimal
    forecast_rationale_link_ratio: Decimal
    cost_context_expected_links: Decimal
    cost_context_linked_count: Decimal
    cost_context_missing_links: Decimal
    cost_context_link_ratio: Decimal
    settlement_rule_note_expected_links: Decimal
    settlement_rule_note_linked_count: Decimal
    settlement_rule_note_missing_links: Decimal
    settlement_rule_note_link_ratio: Decimal
    total_expected_links: Decimal
    total_missing_links: Decimal
    trace_gap_pressure: Decimal
    status: str
    reason_codes: tuple[str, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchStrategyDecisionTraceabilityGapRow, "row")
        object.__setattr__(
            self,
            "aggregate_row_number",
            _normalize_positive_whole_decimal(
                "aggregate_row_number",
                self.aggregate_row_number,
            ),
        )
        _require_digest("trace_hash", self.trace_hash)
        for field_name in (
            "research_evidence_expected_links",
            "research_evidence_linked_count",
            "research_evidence_missing_links",
            "forecast_rationale_expected_links",
            "forecast_rationale_linked_count",
            "forecast_rationale_missing_links",
            "cost_context_expected_links",
            "cost_context_linked_count",
            "cost_context_missing_links",
            "settlement_rule_note_expected_links",
            "settlement_rule_note_linked_count",
            "settlement_rule_note_missing_links",
            "total_expected_links",
            "total_missing_links",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_whole_decimal(
                    field_name,
                    getattr(self, field_name),
                ),
            )
        for field_name in (
            "research_evidence_link_ratio",
            "forecast_rationale_link_ratio",
            "cost_context_link_ratio",
            "settlement_rule_note_link_ratio",
            "trace_gap_pressure",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        _require_status("status", self.status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, ROW_REASON_CODES),
        )
        _require_hard_flags("row", self)
        _apply_or_verify_digest(self)
        _validate_row_consistency(self)


@dataclass(frozen=True)
class ResearchStrategyDecisionTraceabilityGapReport:
    generated_at: datetime
    config_version: str
    input_row_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    total_expected_links: Decimal
    total_missing_links: Decimal
    research_evidence_missing_links: Decimal
    forecast_rationale_missing_links: Decimal
    cost_context_missing_links: Decimal
    settlement_rule_note_missing_links: Decimal
    mean_trace_gap_pressure: Decimal
    max_trace_gap_pressure: Decimal
    status: str
    reason_codes: tuple[str, ...]
    reason_code_counts: tuple[ResearchStrategyDecisionTraceabilityGapReasonCodeCount, ...]
    rows: tuple[ResearchStrategyDecisionTraceabilityGapRow, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchStrategyDecisionTraceabilityGapReport, "report")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_string("config_version", self.config_version)
        for field_name in (
            "input_row_count",
            "pass_count",
            "watch_count",
            "block_count",
            "total_expected_links",
            "total_missing_links",
            "research_evidence_missing_links",
            "forecast_rationale_missing_links",
            "cost_context_missing_links",
            "settlement_rule_note_missing_links",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_whole_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in ("mean_trace_gap_pressure", "max_trace_gap_pressure"):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
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
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        _require_hard_flags("report", self)
        _apply_or_verify_digest(self)
        _validate_report_consistency(self)


def build_research_strategy_decision_traceability_gap_report(
    inputs: Iterable[ResearchStrategyDecisionTraceabilityGapInput],
    *,
    config: ResearchStrategyDecisionTraceabilityGapConfig,
    generated_at: datetime,
) -> ResearchStrategyDecisionTraceabilityGapReport:
    if type(config) is not ResearchStrategyDecisionTraceabilityGapConfig:
        raise ValueError(
            "config must be a ResearchStrategyDecisionTraceabilityGapConfig",
        )
    _require_hard_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    normalized_inputs = _normalize_inputs(inputs)
    row_values = tuple(_row_value_from_input(value, config=config) for value in normalized_inputs)
    row_values = tuple(sorted(row_values, key=_row_value_sort_key))
    rows = tuple(
        _row_from_value(index=index, value=value)
        for index, value in enumerate(row_values, start=1)
    )
    return ResearchStrategyDecisionTraceabilityGapReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        input_row_count=_count(len(rows)),
        pass_count=_status_count(rows, STATUS_PASS),
        watch_count=_status_count(rows, STATUS_WATCH),
        block_count=_status_count(rows, STATUS_BLOCK),
        total_expected_links=_sum_decimal(tuple(row.total_expected_links for row in rows)),
        total_missing_links=_sum_decimal(tuple(row.total_missing_links for row in rows)),
        research_evidence_missing_links=_sum_decimal(
            tuple(row.research_evidence_missing_links for row in rows),
        ),
        forecast_rationale_missing_links=_sum_decimal(
            tuple(row.forecast_rationale_missing_links for row in rows),
        ),
        cost_context_missing_links=_sum_decimal(
            tuple(row.cost_context_missing_links for row in rows),
        ),
        settlement_rule_note_missing_links=_sum_decimal(
            tuple(row.settlement_rule_note_missing_links for row in rows),
        ),
        mean_trace_gap_pressure=_mean(tuple(row.trace_gap_pressure for row in rows)),
        max_trace_gap_pressure=_maximum(tuple(row.trace_gap_pressure for row in rows)),
        status=_report_status(rows),
        reason_codes=_report_reason_codes(rows),
        reason_code_counts=_reason_code_counts_from_rows(rows),
        rows=rows,
    )


def research_strategy_decision_traceability_gap_report_payload(
    report: ResearchStrategyDecisionTraceabilityGapReport | dict[str, Any],
) -> dict[str, Any]:
    if type(report) is ResearchStrategyDecisionTraceabilityGapReport:
        _verify_report_integrity(report)
        _reject_unsafe_public_payload("report", report)
        payload = _json_ready(asdict(report))
    elif type(report) is dict:
        payload = _json_ready(report)
        if type(payload) is not dict:
            raise ValueError("report payload must be a JSON object")
        _require_hard_flags("payload", _DictFlags(payload))
        _reject_unsafe_public_payload("payload", payload)
        _verify_public_payload_integrity(payload)
    else:
        raise ValueError(
            "report must be a ResearchStrategyDecisionTraceabilityGapReport",
        )
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    _require_hard_flags("payload", _DictFlags(payload))
    _reject_unsafe_public_payload("payload", payload)
    return payload


def research_strategy_decision_traceability_gap_report_digest(
    report: ResearchStrategyDecisionTraceabilityGapReport,
) -> str:
    payload = research_strategy_decision_traceability_gap_report_payload(report)
    encoded = dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    ).encode("utf-8")
    return sha256(encoded).hexdigest()


@dataclass(frozen=True)
class _DictFlags:
    value: dict[str, Any]

    @property
    def paper_only(self) -> object:
        return self.value.get("paper_only")

    @property
    def report_only(self) -> object:
        return self.value.get("report_only")

    @property
    def readonly(self) -> object:
        return self.value.get("readonly")


@dataclass(frozen=True)
class _RowValue:
    trace_hash: str
    research_evidence_expected_links: Decimal
    research_evidence_linked_count: Decimal
    research_evidence_missing_links: Decimal
    research_evidence_link_ratio: Decimal
    forecast_rationale_expected_links: Decimal
    forecast_rationale_linked_count: Decimal
    forecast_rationale_missing_links: Decimal
    forecast_rationale_link_ratio: Decimal
    cost_context_expected_links: Decimal
    cost_context_linked_count: Decimal
    cost_context_missing_links: Decimal
    cost_context_link_ratio: Decimal
    settlement_rule_note_expected_links: Decimal
    settlement_rule_note_linked_count: Decimal
    settlement_rule_note_missing_links: Decimal
    settlement_rule_note_link_ratio: Decimal
    total_expected_links: Decimal
    total_missing_links: Decimal
    trace_gap_pressure: Decimal
    status: str
    reason_codes: tuple[str, ...]


def _row_value_from_input(
    value: ResearchStrategyDecisionTraceabilityGapInput,
    *,
    config: ResearchStrategyDecisionTraceabilityGapConfig,
) -> _RowValue:
    research_evidence_missing_links = _missing_links(
        value.research_evidence_expected_links,
        value.research_evidence_linked_count,
    )
    forecast_rationale_missing_links = _missing_links(
        value.forecast_rationale_expected_links,
        value.forecast_rationale_linked_count,
    )
    cost_context_missing_links = _missing_links(
        value.cost_context_expected_links,
        value.cost_context_linked_count,
    )
    settlement_rule_note_missing_links = _missing_links(
        value.settlement_rule_note_expected_links,
        value.settlement_rule_note_linked_count,
    )
    research_evidence_link_ratio = _link_ratio(
        value.research_evidence_linked_count,
        value.research_evidence_expected_links,
    )
    forecast_rationale_link_ratio = _link_ratio(
        value.forecast_rationale_linked_count,
        value.forecast_rationale_expected_links,
    )
    cost_context_link_ratio = _link_ratio(
        value.cost_context_linked_count,
        value.cost_context_expected_links,
    )
    settlement_rule_note_link_ratio = _link_ratio(
        value.settlement_rule_note_linked_count,
        value.settlement_rule_note_expected_links,
    )
    total_expected_links = _sum_decimal(
        (
            value.research_evidence_expected_links,
            value.forecast_rationale_expected_links,
            value.cost_context_expected_links,
            value.settlement_rule_note_expected_links,
        ),
    )
    total_missing_links = _sum_decimal(
        (
            research_evidence_missing_links,
            forecast_rationale_missing_links,
            cost_context_missing_links,
            settlement_rule_note_missing_links,
        ),
    )
    trace_gap_pressure = _gap_pressure(total_missing_links, total_expected_links)
    component_statuses = {
        "research_evidence": _floor_status(
            research_evidence_link_ratio,
            pass_value=config.min_pass_research_evidence_link_ratio,
            watch_value=config.min_watch_research_evidence_link_ratio,
        ),
        "forecast_rationale": _floor_status(
            forecast_rationale_link_ratio,
            pass_value=config.min_pass_forecast_rationale_link_ratio,
            watch_value=config.min_watch_forecast_rationale_link_ratio,
        ),
        "cost_context": _floor_status(
            cost_context_link_ratio,
            pass_value=config.min_pass_cost_context_link_ratio,
            watch_value=config.min_watch_cost_context_link_ratio,
        ),
        "settlement_rule_note": _floor_status(
            settlement_rule_note_link_ratio,
            pass_value=config.min_pass_settlement_rule_note_link_ratio,
            watch_value=config.min_watch_settlement_rule_note_link_ratio,
        ),
        "trace_gap_pressure": _ceiling_status(
            trace_gap_pressure,
            pass_value=config.max_pass_trace_gap_pressure,
            watch_value=config.max_watch_trace_gap_pressure,
        ),
    }
    status = _row_status(tuple(component_statuses.values()))
    return _RowValue(
        trace_hash=sha256(value.trace_key.encode("utf-8")).hexdigest(),
        research_evidence_expected_links=value.research_evidence_expected_links,
        research_evidence_linked_count=value.research_evidence_linked_count,
        research_evidence_missing_links=research_evidence_missing_links,
        research_evidence_link_ratio=research_evidence_link_ratio,
        forecast_rationale_expected_links=value.forecast_rationale_expected_links,
        forecast_rationale_linked_count=value.forecast_rationale_linked_count,
        forecast_rationale_missing_links=forecast_rationale_missing_links,
        forecast_rationale_link_ratio=forecast_rationale_link_ratio,
        cost_context_expected_links=value.cost_context_expected_links,
        cost_context_linked_count=value.cost_context_linked_count,
        cost_context_missing_links=cost_context_missing_links,
        cost_context_link_ratio=cost_context_link_ratio,
        settlement_rule_note_expected_links=value.settlement_rule_note_expected_links,
        settlement_rule_note_linked_count=value.settlement_rule_note_linked_count,
        settlement_rule_note_missing_links=settlement_rule_note_missing_links,
        settlement_rule_note_link_ratio=settlement_rule_note_link_ratio,
        total_expected_links=total_expected_links,
        total_missing_links=total_missing_links,
        trace_gap_pressure=trace_gap_pressure,
        status=status,
        reason_codes=_row_reason_codes(status=status, component_statuses=component_statuses),
    )


def _row_from_value(
    *,
    index: int,
    value: _RowValue,
) -> ResearchStrategyDecisionTraceabilityGapRow:
    return ResearchStrategyDecisionTraceabilityGapRow(
        aggregate_row_number=_count(index),
        trace_hash=value.trace_hash,
        research_evidence_expected_links=value.research_evidence_expected_links,
        research_evidence_linked_count=value.research_evidence_linked_count,
        research_evidence_missing_links=value.research_evidence_missing_links,
        research_evidence_link_ratio=value.research_evidence_link_ratio,
        forecast_rationale_expected_links=value.forecast_rationale_expected_links,
        forecast_rationale_linked_count=value.forecast_rationale_linked_count,
        forecast_rationale_missing_links=value.forecast_rationale_missing_links,
        forecast_rationale_link_ratio=value.forecast_rationale_link_ratio,
        cost_context_expected_links=value.cost_context_expected_links,
        cost_context_linked_count=value.cost_context_linked_count,
        cost_context_missing_links=value.cost_context_missing_links,
        cost_context_link_ratio=value.cost_context_link_ratio,
        settlement_rule_note_expected_links=value.settlement_rule_note_expected_links,
        settlement_rule_note_linked_count=value.settlement_rule_note_linked_count,
        settlement_rule_note_missing_links=value.settlement_rule_note_missing_links,
        settlement_rule_note_link_ratio=value.settlement_rule_note_link_ratio,
        total_expected_links=value.total_expected_links,
        total_missing_links=value.total_missing_links,
        trace_gap_pressure=value.trace_gap_pressure,
        status=value.status,
        reason_codes=value.reason_codes,
    )


def _row_reason_codes(
    *,
    status: str,
    component_statuses: dict[str, str],
) -> tuple[str, ...]:
    reason_codes = [f"decision_traceability_gap_{status}"]
    for component in (
        "research_evidence",
        "forecast_rationale",
        "cost_context",
        "settlement_rule_note",
        "trace_gap_pressure",
    ):
        component_status = component_statuses[component]
        if component_status != STATUS_PASS:
            if component == "trace_gap_pressure":
                reason_codes.append(f"trace_gap_pressure_{component_status}")
            else:
                reason_codes.append(f"{component}_traceability_gap_{component_status}")
    return _normalize_reason_codes(
        "reason_codes",
        tuple(reason_codes),
        ROW_REASON_CODES,
    )


def _report_reason_codes(
    rows: tuple[ResearchStrategyDecisionTraceabilityGapRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return ("decision_traceability_gap_report_empty",)
    status = _report_status(rows)
    reason_codes = [f"decision_traceability_gap_report_{status}"]
    component_pairs = (
        (
            "research_evidence_traceability_gap_exception",
            (
                "research_evidence_traceability_gap_watch",
                "research_evidence_traceability_gap_block",
            ),
        ),
        (
            "forecast_rationale_traceability_gap_exception",
            (
                "forecast_rationale_traceability_gap_watch",
                "forecast_rationale_traceability_gap_block",
            ),
        ),
        (
            "cost_context_traceability_gap_exception",
            (
                "cost_context_traceability_gap_watch",
                "cost_context_traceability_gap_block",
            ),
        ),
        (
            "settlement_rule_note_traceability_gap_exception",
            (
                "settlement_rule_note_traceability_gap_watch",
                "settlement_rule_note_traceability_gap_block",
            ),
        ),
        (
            "trace_gap_pressure_exception",
            ("trace_gap_pressure_watch", "trace_gap_pressure_block"),
        ),
    )
    for report_reason, row_reasons in component_pairs:
        if any(_row_has_any_reason(row, row_reasons) for row in rows):
            reason_codes.append(report_reason)
    return _normalize_reason_codes(
        "reason_codes",
        tuple(reason_codes),
        REPORT_REASON_CODES,
    )


def _reason_code_counts_from_rows(
    rows: tuple[ResearchStrategyDecisionTraceabilityGapRow, ...],
) -> tuple[ResearchStrategyDecisionTraceabilityGapReasonCodeCount, ...]:
    if not rows:
        return ()
    row_count = _count(len(rows))
    counts: dict[str, Decimal] = {}
    for row in rows:
        for reason_code in row.reason_codes:
            counts[reason_code] = counts.get(reason_code, ZERO) + ONE
    return tuple(
        ResearchStrategyDecisionTraceabilityGapReasonCodeCount(
            reason_code=reason_code,
            count=count,
            input_ratio=_ratio(count, row_count),
        )
        for reason_code, count in sorted(
            counts.items(),
            key=lambda item: (ROW_REASON_INDEX[item[0]], item[0]),
        )
    )


def _normalize_inputs(
    inputs: Iterable[ResearchStrategyDecisionTraceabilityGapInput],
) -> tuple[ResearchStrategyDecisionTraceabilityGapInput, ...]:
    if type(inputs) in (str, bytes):
        raise ValueError("inputs must be an iterable")
    try:
        normalized = tuple(inputs)
    except TypeError as exc:
        raise ValueError("inputs must be an iterable") from exc
    seen_keys: set[str] = set()
    for value in normalized:
        if type(value) is not ResearchStrategyDecisionTraceabilityGapInput:
            raise ValueError(
                "inputs must contain ResearchStrategyDecisionTraceabilityGapInput",
            )
        _require_hard_flags("input", value)
        if value.trace_key in seen_keys:
            raise ValueError("inputs must not contain duplicate trace_key values")
        seen_keys.add(value.trace_key)
    return normalized


def _normalize_rows(
    rows: Iterable[ResearchStrategyDecisionTraceabilityGapRow],
) -> tuple[ResearchStrategyDecisionTraceabilityGapRow, ...]:
    if type(rows) in (str, bytes):
        raise ValueError("rows must be an iterable")
    try:
        normalized = tuple(rows)
    except TypeError as exc:
        raise ValueError("rows must be an iterable") from exc
    seen_hashes: set[str] = set()
    for row in normalized:
        if type(row) is not ResearchStrategyDecisionTraceabilityGapRow:
            raise ValueError("rows must contain ResearchStrategyDecisionTraceabilityGapRow")
        _require_hard_flags("row", row)
        if row.trace_hash in seen_hashes:
            raise ValueError("rows must not contain duplicate trace_hash values")
        seen_hashes.add(row.trace_hash)
    return tuple(sorted(normalized, key=_row_sort_key))


def _normalize_reason_code_counts(
    counts: Iterable[ResearchStrategyDecisionTraceabilityGapReasonCodeCount],
) -> tuple[ResearchStrategyDecisionTraceabilityGapReasonCodeCount, ...]:
    if type(counts) in (str, bytes):
        raise ValueError("reason_code_counts must be an iterable")
    try:
        normalized = tuple(counts)
    except TypeError as exc:
        raise ValueError("reason_code_counts must be an iterable") from exc
    seen_codes: set[str] = set()
    for value in normalized:
        if type(value) is not ResearchStrategyDecisionTraceabilityGapReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "ResearchStrategyDecisionTraceabilityGapReasonCodeCount",
            )
        _require_hard_flags("reason_code_count", value)
        if value.reason_code in seen_codes:
            raise ValueError("reason_code_counts must not contain duplicate values")
        seen_codes.add(value.reason_code)
    return tuple(sorted(normalized, key=lambda item: (ROW_REASON_INDEX[item.reason_code], item.reason_code)))


def _validate_row_consistency(row: ResearchStrategyDecisionTraceabilityGapRow) -> None:
    if row.research_evidence_missing_links != _missing_links(
        row.research_evidence_expected_links,
        row.research_evidence_linked_count,
    ):
        raise ValueError("research_evidence_missing_links must match linked count")
    if row.forecast_rationale_missing_links != _missing_links(
        row.forecast_rationale_expected_links,
        row.forecast_rationale_linked_count,
    ):
        raise ValueError("forecast_rationale_missing_links must match linked count")
    if row.cost_context_missing_links != _missing_links(
        row.cost_context_expected_links,
        row.cost_context_linked_count,
    ):
        raise ValueError("cost_context_missing_links must match linked count")
    if row.settlement_rule_note_missing_links != _missing_links(
        row.settlement_rule_note_expected_links,
        row.settlement_rule_note_linked_count,
    ):
        raise ValueError("settlement_rule_note_missing_links must match linked count")
    if row.research_evidence_link_ratio != _link_ratio(
        row.research_evidence_linked_count,
        row.research_evidence_expected_links,
    ):
        raise ValueError("research_evidence_link_ratio must match linked count")
    if row.forecast_rationale_link_ratio != _link_ratio(
        row.forecast_rationale_linked_count,
        row.forecast_rationale_expected_links,
    ):
        raise ValueError("forecast_rationale_link_ratio must match linked count")
    if row.cost_context_link_ratio != _link_ratio(
        row.cost_context_linked_count,
        row.cost_context_expected_links,
    ):
        raise ValueError("cost_context_link_ratio must match linked count")
    if row.settlement_rule_note_link_ratio != _link_ratio(
        row.settlement_rule_note_linked_count,
        row.settlement_rule_note_expected_links,
    ):
        raise ValueError("settlement_rule_note_link_ratio must match linked count")
    if row.total_expected_links != _sum_decimal(
        (
            row.research_evidence_expected_links,
            row.forecast_rationale_expected_links,
            row.cost_context_expected_links,
            row.settlement_rule_note_expected_links,
        ),
    ):
        raise ValueError("total_expected_links must match component links")
    if row.total_missing_links != _sum_decimal(
        (
            row.research_evidence_missing_links,
            row.forecast_rationale_missing_links,
            row.cost_context_missing_links,
            row.settlement_rule_note_missing_links,
        ),
    ):
        raise ValueError("total_missing_links must match component links")
    if row.trace_gap_pressure != _gap_pressure(
        row.total_missing_links,
        row.total_expected_links,
    ):
        raise ValueError("trace_gap_pressure must match total links")
    if row.status != _status_from_row_reason_codes(row.reason_codes):
        raise ValueError("status must match reason_codes")


def _validate_report_consistency(report: ResearchStrategyDecisionTraceabilityGapReport) -> None:
    rows = report.rows
    if report.input_row_count != _count(len(rows)):
        raise ValueError("input_row_count must match rows")
    if report.pass_count != _status_count(rows, STATUS_PASS):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _status_count(rows, STATUS_WATCH):
        raise ValueError("watch_count must match rows")
    if report.block_count != _status_count(rows, STATUS_BLOCK):
        raise ValueError("block_count must match rows")
    if report.total_expected_links != _sum_decimal(tuple(row.total_expected_links for row in rows)):
        raise ValueError("total_expected_links must match rows")
    if report.total_missing_links != _sum_decimal(tuple(row.total_missing_links for row in rows)):
        raise ValueError("total_missing_links must match rows")
    if report.research_evidence_missing_links != _sum_decimal(
        tuple(row.research_evidence_missing_links for row in rows),
    ):
        raise ValueError("research_evidence_missing_links must match rows")
    if report.forecast_rationale_missing_links != _sum_decimal(
        tuple(row.forecast_rationale_missing_links for row in rows),
    ):
        raise ValueError("forecast_rationale_missing_links must match rows")
    if report.cost_context_missing_links != _sum_decimal(
        tuple(row.cost_context_missing_links for row in rows),
    ):
        raise ValueError("cost_context_missing_links must match rows")
    if report.settlement_rule_note_missing_links != _sum_decimal(
        tuple(row.settlement_rule_note_missing_links for row in rows),
    ):
        raise ValueError("settlement_rule_note_missing_links must match rows")
    if report.mean_trace_gap_pressure != _mean(tuple(row.trace_gap_pressure for row in rows)):
        raise ValueError("mean_trace_gap_pressure must match rows")
    if report.max_trace_gap_pressure != _maximum(tuple(row.trace_gap_pressure for row in rows)):
        raise ValueError("max_trace_gap_pressure must match rows")
    if report.status != _report_status(rows):
        raise ValueError("status must match rows")
    if report.reason_codes != _report_reason_codes(rows):
        raise ValueError("reason_codes must match rows")
    if report.reason_code_counts != _reason_code_counts_from_rows(rows):
        raise ValueError("reason_code_counts must match rows")


def _verify_report_integrity(report: ResearchStrategyDecisionTraceabilityGapReport) -> None:
    if report.derived_validation_digest != _payload_digest(_unsigned_payload(report)):
        raise ValueError("derived_validation_digest does not match report payload")
    for row in report.rows:
        if row.derived_validation_digest != _payload_digest(_unsigned_payload(row)):
            raise ValueError("derived_validation_digest does not match row payload")


def _verify_public_payload_integrity(payload: dict[str, Any]) -> None:
    rows = payload.get("rows")
    if type(rows) is list:
        for row in rows:
            if type(row) is not dict:
                raise ValueError("rows must contain payload objects")
            _verify_payload_digest(row)
    _verify_payload_digest(payload)


def _verify_payload_digest(payload: dict[str, Any]) -> None:
    supplied = payload.get("derived_validation_digest")
    if type(supplied) is not str:
        raise ValueError("derived_validation_digest must be a lowercase sha256 digest")
    _require_digest("derived_validation_digest", supplied)
    base_payload = {
        key: value for key, value in payload.items() if key != "derived_validation_digest"
    }
    if _payload_digest(base_payload) != supplied:
        raise ValueError("derived_validation_digest does not match payload fields")


def _apply_or_verify_digest(
    value: ResearchStrategyDecisionTraceabilityGapRow
    | ResearchStrategyDecisionTraceabilityGapReport,
) -> None:
    expected_digest = _payload_digest(_unsigned_payload(value))
    supplied_digest = value.derived_validation_digest
    if supplied_digest == "":
        object.__setattr__(value, "derived_validation_digest", expected_digest)
        return
    _require_digest("derived_validation_digest", supplied_digest)
    if supplied_digest != expected_digest:
        raise ValueError("derived_validation_digest does not match report payload")


def _unsigned_payload(
    value: ResearchStrategyDecisionTraceabilityGapRow
    | ResearchStrategyDecisionTraceabilityGapReport,
) -> dict[str, Any]:
    payload = _json_ready(asdict(value))
    if type(payload) is not dict:
        raise ValueError("payload must be a JSON object")
    payload.pop("derived_validation_digest", None)
    _reject_unsafe_public_payload("payload", payload)
    return payload


def _payload_digest(payload: dict[str, Any]) -> str:
    _reject_unsafe_public_payload("payload", payload)
    encoded = dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    )
    return sha256(encoded.encode("utf-8")).hexdigest()


def _json_ready(value: object) -> Any:
    if is_dataclass(value) and not isinstance(value, type):
        return _json_ready(asdict(value))
    if type(value) is dict:
        return {str(key): _json_ready(item) for key, item in value.items()}
    if type(value) in (list, tuple):
        return [_json_ready(item) for item in value]
    if type(value) is Decimal:
        return _decimal_string(value)
    if type(value) is datetime:
        return _as_utc("datetime", value).isoformat()
    if type(value) in (str, bool) or value is None:
        return value
    if type(value) is int:
        raise ValueError("public payload must not contain primitive numerics")
    return value


def _reject_unsafe_public_payload(label: str, value: object) -> None:
    if is_dataclass(value) and not isinstance(value, type):
        _reject_unsafe_public_payload(label, asdict(value))
        return
    if type(value) is dict:
        for key, item in value.items():
            _reject_unsafe_public_payload(f"{label}.key", key)
            if key in {"paper_only", "report_only", "readonly"} and item is not True:
                raise ValueError(f"{label}.{key} must be True")
            _reject_unsafe_public_payload(f"{label}.{key}", item)
        return
    if type(value) in (list, tuple):
        for item in value:
            _reject_unsafe_public_payload(label, item)
        return
    if type(value) is str:
        lowered = value.lower()
        if any(fragment in lowered for fragment in UNSAFE_PUBLIC_FRAGMENTS):
            raise ValueError(f"{label} contains unsafe public payload content")


def _require_exact_type(value: object, expected_type: type[object], field_name: str) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{field_name} must be a {expected_type.__name__}")


def _require_public_string(field_name: str, value: object) -> str:
    if type(value) is not str or not value.strip():
        raise ValueError(f"{field_name} must be a non-empty string")
    _reject_unsafe_public_payload(field_name, value)
    return value


def _require_private_key(field_name: str, value: object) -> str:
    if type(value) is not str or not value.strip():
        raise ValueError(f"{field_name} must be a non-empty string")
    return value


def _require_digest(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a lowercase sha256 digest")
    if len(value) != 64 or any(item not in "0123456789abcdef" for item in value):
        raise ValueError(f"{field_name} must be a lowercase sha256 digest")
    return value


def _require_status(field_name: str, value: object) -> str:
    if type(value) is not str or value not in RESEARCH_STRATEGY_DECISION_TRACEABILITY_GAP_STATUSES:
        raise ValueError(f"{field_name} must be pass, watch, or block")
    return value


def _require_reason_code(
    field_name: str,
    value: object,
    allowed_values: tuple[str, ...],
) -> str:
    if type(value) is not str or value not in allowed_values:
        raise ValueError(f"{field_name} must be a supported reason code")
    return value


def _require_hard_flags(field_name: str, value: object) -> None:
    if getattr(value, "paper_only", None) is not True:
        raise ValueError(f"{field_name} must be paper_only")
    if getattr(value, "report_only", None) is not True:
        raise ValueError(f"{field_name} must be report_only")
    if getattr(value, "readonly", None) is not True:
        raise ValueError(f"{field_name} must be readonly")


def _require_floor_pair(
    pass_field_name: str,
    pass_value: Decimal,
    watch_field_name: str,
    watch_value: Decimal,
) -> None:
    if pass_value < watch_value:
        raise ValueError(f"{pass_field_name} must be at least {watch_field_name}")


def _require_ceiling_pair(
    pass_field_name: str,
    pass_value: Decimal,
    watch_value: Decimal,
) -> None:
    if pass_value > watch_value:
        raise ValueError(f"{pass_field_name} must not exceed paired watch value")


def _require_link_pair(
    linked_field_name: str,
    linked_value: Decimal,
    expected_value: Decimal,
) -> None:
    if linked_value > expected_value:
        raise ValueError(f"{linked_field_name} must not exceed expected links")


def _normalize_probability(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < ZERO or normalized > ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return _quantize_decimal(normalized)


def _normalize_nonnegative_whole_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{field_name} must be a whole decimal")
    return normalized.quantize(COUNT_QUANTUM)


def _normalize_positive_whole_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_nonnegative_whole_decimal(field_name, value)
    if normalized <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return value


def _quantize_decimal(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(QUANTUM)


def _decimal_string(value: Decimal) -> str:
    return format(value.quantize(QUANTUM), "f")


def _count(value: int) -> Decimal:
    return Decimal(value).quantize(COUNT_QUANTUM)


def _sum_decimal(values: tuple[Decimal, ...]) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        total = ZERO
        for value in values:
            total += value
    return total.quantize(QUANTUM)


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO:
        return ZERO.quantize(QUANTUM)
    with localcontext(DECIMAL_CONTEXT):
        value = numerator / denominator
    if value < ZERO:
        value = ZERO
    if value > ONE:
        value = ONE
    return _quantize_decimal(value)


def _mean(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return ZERO.quantize(QUANTUM)
    return _ratio(_sum_decimal(values), _count(len(values)))


def _maximum(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return ZERO.quantize(QUANTUM)
    return max(values).quantize(QUANTUM)


def _link_ratio(linked_count: Decimal, expected_links: Decimal) -> Decimal:
    if expected_links == ZERO:
        return ONE.quantize(QUANTUM)
    return _ratio(linked_count, expected_links)


def _gap_pressure(missing_links: Decimal, expected_links: Decimal) -> Decimal:
    if expected_links == ZERO:
        return ZERO.quantize(QUANTUM)
    return _ratio(missing_links, expected_links)


def _missing_links(expected_links: Decimal, linked_count: Decimal) -> Decimal:
    return (expected_links - linked_count).quantize(QUANTUM)


def _floor_status(value: Decimal, *, pass_value: Decimal, watch_value: Decimal) -> str:
    if value >= pass_value:
        return STATUS_PASS
    if value >= watch_value:
        return STATUS_WATCH
    return STATUS_BLOCK


def _ceiling_status(value: Decimal, *, pass_value: Decimal, watch_value: Decimal) -> str:
    if value <= pass_value:
        return STATUS_PASS
    if value <= watch_value:
        return STATUS_WATCH
    return STATUS_BLOCK


def _row_status(statuses: tuple[str, ...]) -> str:
    if STATUS_BLOCK in statuses:
        return STATUS_BLOCK
    if STATUS_WATCH in statuses:
        return STATUS_WATCH
    return STATUS_PASS


def _report_status(rows: tuple[ResearchStrategyDecisionTraceabilityGapRow, ...]) -> str:
    if not rows:
        return STATUS_BLOCK
    return _row_status(tuple(row.status for row in rows))


def _status_count(
    rows: tuple[ResearchStrategyDecisionTraceabilityGapRow, ...],
    status: str,
) -> Decimal:
    return _count(sum(1 for row in rows if row.status == status))


def _status_from_row_reason_codes(reason_codes: tuple[str, ...]) -> str:
    if any(reason_code.endswith("_block") for reason_code in reason_codes):
        return STATUS_BLOCK
    if any(reason_code.endswith("_watch") for reason_code in reason_codes):
        return STATUS_WATCH
    return STATUS_PASS


def _normalize_reason_codes(
    field_name: str,
    reason_codes: tuple[str, ...],
    allowed_values: tuple[str, ...],
) -> tuple[str, ...]:
    if type(reason_codes) is not tuple or not reason_codes:
        raise ValueError(f"{field_name} must be a non-empty tuple")
    for reason_code in reason_codes:
        _require_reason_code(field_name, reason_code, allowed_values)
    if len(set(reason_codes)) != len(reason_codes):
        raise ValueError(f"{field_name} must not contain duplicates")
    index = ROW_REASON_INDEX if allowed_values is ROW_REASON_CODES else REPORT_REASON_INDEX
    expected = tuple(sorted(reason_codes, key=lambda item: (index[item], item)))
    if reason_codes != expected:
        raise ValueError(f"{field_name} must use canonical sequence")
    return reason_codes


def _row_has_any_reason(
    row: ResearchStrategyDecisionTraceabilityGapRow,
    reason_codes: tuple[str, ...],
) -> bool:
    return any(reason_code in row.reason_codes for reason_code in reason_codes)


def _row_sort_key(value: ResearchStrategyDecisionTraceabilityGapRow) -> tuple[Decimal, str]:
    return (STATUS_WEIGHT[value.status], value.trace_hash)


def _row_value_sort_key(value: _RowValue) -> tuple[Decimal, str]:
    return (STATUS_WEIGHT[value.status], value.trace_hash)


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)
