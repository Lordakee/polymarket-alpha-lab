"""Pure evidence, cost, and consensus readiness gate report."""

from __future__ import annotations

from dataclasses import asdict, dataclass, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
from json import dumps
from typing import Any, Iterable


DEFAULT_RESEARCH_STRATEGY_EVIDENCE_COST_CONSENSUS_GATE_REPORT_CONFIG_VERSION = (
    "research-strategy-evidence-cost-consensus-gate-report-v0"
)
RESEARCH_STRATEGY_EVIDENCE_COST_CONSENSUS_GATE_STATUSES = (
    "pass",
    "watch",
    "block",
)

QUANTUM = Decimal("0.000001")
COUNT_QUANTUM = Decimal("1.000000")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)

ROW_REASON_CODES = (
    "evidence_cost_consensus_gate_pass",
    "evidence_cost_consensus_gate_watch",
    "evidence_cost_consensus_gate_block",
    "evidence_maturity_watch",
    "evidence_maturity_block",
    "fee_freshness_watch",
    "fee_freshness_block",
    "spread_freshness_watch",
    "spread_freshness_block",
    "slippage_freshness_watch",
    "slippage_freshness_block",
    "specialist_consensus_watch",
    "specialist_consensus_block",
    "source_conflict_pressure_watch",
    "source_conflict_pressure_block",
    "manual_queue_urgency_watch",
    "manual_queue_urgency_block",
)
REPORT_REASON_CODES = (
    "evidence_cost_consensus_gate_report_empty",
    "evidence_cost_consensus_gate_report_pass",
    "evidence_cost_consensus_gate_report_watch",
    "evidence_cost_consensus_gate_report_block",
    "evidence_maturity_exception",
    "cost_freshness_exception",
    "specialist_consensus_exception",
    "source_conflict_pressure_exception",
    "manual_queue_urgency_exception",
)


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
)


@dataclass(frozen=True)
class ResearchStrategyEvidenceCostConsensusGateConfig:
    config_version: str = (
        DEFAULT_RESEARCH_STRATEGY_EVIDENCE_COST_CONSENSUS_GATE_REPORT_CONFIG_VERSION
    )
    min_pass_evidence_maturity_score: Decimal = Decimal("0.800000")
    min_watch_evidence_maturity_score: Decimal = Decimal("0.600000")
    max_pass_fee_freshness_age_seconds: Decimal = Decimal("3600.000000")
    max_watch_fee_freshness_age_seconds: Decimal = Decimal("14400.000000")
    max_pass_spread_freshness_age_seconds: Decimal = Decimal("300.000000")
    max_watch_spread_freshness_age_seconds: Decimal = Decimal("1200.000000")
    max_pass_slippage_freshness_age_seconds: Decimal = Decimal("86400.000000")
    max_watch_slippage_freshness_age_seconds: Decimal = Decimal("259200.000000")
    min_pass_specialist_consensus_score: Decimal = Decimal("0.800000")
    min_watch_specialist_consensus_score: Decimal = Decimal("0.600000")
    max_pass_source_conflict_pressure: Decimal = Decimal("0.200000")
    max_watch_source_conflict_pressure: Decimal = Decimal("0.500000")
    max_pass_manual_queue_urgency: Decimal = Decimal("0.300000")
    max_watch_manual_queue_urgency: Decimal = Decimal("0.700000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchStrategyEvidenceCostConsensusGateConfig, "config")
        _require_public_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_STRATEGY_EVIDENCE_COST_CONSENSUS_GATE_REPORT_CONFIG_VERSION
        ):
            raise ValueError("config_version must match the supported value")
        for field_name in (
            "min_pass_evidence_maturity_score",
            "min_watch_evidence_maturity_score",
            "min_pass_specialist_consensus_score",
            "min_watch_specialist_consensus_score",
            "max_pass_source_conflict_pressure",
            "max_watch_source_conflict_pressure",
            "max_pass_manual_queue_urgency",
            "max_watch_manual_queue_urgency",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "max_pass_fee_freshness_age_seconds",
            "max_watch_fee_freshness_age_seconds",
            "max_pass_spread_freshness_age_seconds",
            "max_watch_spread_freshness_age_seconds",
            "max_pass_slippage_freshness_age_seconds",
            "max_watch_slippage_freshness_age_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_positive_decimal(field_name, getattr(self, field_name)),
            )
        _require_floor_pair(
            "min_pass_evidence_maturity_score",
            self.min_pass_evidence_maturity_score,
            "min_watch_evidence_maturity_score",
            self.min_watch_evidence_maturity_score,
        )
        _require_floor_pair(
            "min_pass_specialist_consensus_score",
            self.min_pass_specialist_consensus_score,
            "min_watch_specialist_consensus_score",
            self.min_watch_specialist_consensus_score,
        )
        _require_ceiling_pair(
            "max_pass_fee_freshness_age_seconds",
            self.max_pass_fee_freshness_age_seconds,
            self.max_watch_fee_freshness_age_seconds,
        )
        _require_ceiling_pair(
            "max_pass_spread_freshness_age_seconds",
            self.max_pass_spread_freshness_age_seconds,
            self.max_watch_spread_freshness_age_seconds,
        )
        _require_ceiling_pair(
            "max_pass_slippage_freshness_age_seconds",
            self.max_pass_slippage_freshness_age_seconds,
            self.max_watch_slippage_freshness_age_seconds,
        )
        _require_ceiling_pair(
            "max_pass_source_conflict_pressure",
            self.max_pass_source_conflict_pressure,
            self.max_watch_source_conflict_pressure,
        )
        _require_ceiling_pair(
            "max_pass_manual_queue_urgency",
            self.max_pass_manual_queue_urgency,
            self.max_watch_manual_queue_urgency,
        )
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class ResearchStrategyEvidenceCostConsensusGateInput:
    aggregation_key: str
    evidence_maturity_score: Decimal
    fee_freshness_age_seconds: Decimal
    spread_freshness_age_seconds: Decimal
    slippage_freshness_age_seconds: Decimal
    specialist_consensus_score: Decimal
    source_conflict_pressure: Decimal
    manual_queue_urgency: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchStrategyEvidenceCostConsensusGateInput, "input")
        _require_private_key("aggregation_key", self.aggregation_key)
        for field_name in (
            "evidence_maturity_score",
            "specialist_consensus_score",
            "source_conflict_pressure",
            "manual_queue_urgency",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "fee_freshness_age_seconds",
            "spread_freshness_age_seconds",
            "slippage_freshness_age_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        _require_hard_flags("input", self)


@dataclass(frozen=True)
class ResearchStrategyEvidenceCostConsensusGateReasonCodeCount:
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
            _normalize_nonnegative_decimal("count", self.count),
        )
        object.__setattr__(
            self,
            "input_ratio",
            _normalize_probability("input_ratio", self.input_ratio),
        )
        _require_hard_flags("reason_code_count", self)


@dataclass(frozen=True)
class ResearchStrategyEvidenceCostConsensusGateRow:
    aggregate_row_number: Decimal
    aggregate_hash: str
    evidence_maturity_score: Decimal
    fee_freshness_age_seconds: Decimal
    spread_freshness_age_seconds: Decimal
    slippage_freshness_age_seconds: Decimal
    cost_freshness_score: Decimal
    specialist_consensus_score: Decimal
    source_conflict_pressure: Decimal
    manual_queue_urgency: Decimal
    readiness_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchStrategyEvidenceCostConsensusGateRow, "row")
        object.__setattr__(
            self,
            "aggregate_row_number",
            _normalize_positive_whole_decimal(
                "aggregate_row_number",
                self.aggregate_row_number,
            ),
        )
        _require_digest("aggregate_hash", self.aggregate_hash)
        for field_name in (
            "evidence_maturity_score",
            "cost_freshness_score",
            "specialist_consensus_score",
            "source_conflict_pressure",
            "manual_queue_urgency",
            "readiness_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "fee_freshness_age_seconds",
            "spread_freshness_age_seconds",
            "slippage_freshness_age_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
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
class ResearchStrategyEvidenceCostConsensusGateReport:
    generated_at: datetime
    config_version: str
    input_row_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    mean_evidence_maturity_score: Decimal
    mean_cost_freshness_score: Decimal
    mean_specialist_consensus_score: Decimal
    max_source_conflict_pressure: Decimal
    max_manual_queue_urgency: Decimal
    mean_readiness_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    reason_code_counts: tuple[ResearchStrategyEvidenceCostConsensusGateReasonCodeCount, ...]
    rows: tuple[ResearchStrategyEvidenceCostConsensusGateRow, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchStrategyEvidenceCostConsensusGateReport, "report")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_string("config_version", self.config_version)
        for field_name in ("input_row_count", "pass_count", "watch_count", "block_count"):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_whole_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "mean_evidence_maturity_score",
            "mean_cost_freshness_score",
            "mean_specialist_consensus_score",
            "max_source_conflict_pressure",
            "max_manual_queue_urgency",
            "mean_readiness_score",
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


def build_research_strategy_evidence_cost_consensus_gate_report(
    inputs: Iterable[ResearchStrategyEvidenceCostConsensusGateInput],
    *,
    config: ResearchStrategyEvidenceCostConsensusGateConfig,
    generated_at: datetime,
) -> ResearchStrategyEvidenceCostConsensusGateReport:
    if type(config) is not ResearchStrategyEvidenceCostConsensusGateConfig:
        raise ValueError(
            "config must be a ResearchStrategyEvidenceCostConsensusGateConfig",
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
    return ResearchStrategyEvidenceCostConsensusGateReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        input_row_count=_count(len(rows)),
        pass_count=_status_count(rows, "pass"),
        watch_count=_status_count(rows, "watch"),
        block_count=_status_count(rows, "block"),
        mean_evidence_maturity_score=_mean(
            tuple(row.evidence_maturity_score for row in rows),
        ),
        mean_cost_freshness_score=_mean(
            tuple(row.cost_freshness_score for row in rows),
        ),
        mean_specialist_consensus_score=_mean(
            tuple(row.specialist_consensus_score for row in rows),
        ),
        max_source_conflict_pressure=_maximum(
            tuple(row.source_conflict_pressure for row in rows),
        ),
        max_manual_queue_urgency=_maximum(
            tuple(row.manual_queue_urgency for row in rows),
        ),
        mean_readiness_score=_mean(tuple(row.readiness_score for row in rows)),
        status=_report_status(rows),
        reason_codes=_report_reason_codes(rows),
        reason_code_counts=_reason_code_counts_from_rows(rows),
        rows=rows,
    )


def research_strategy_evidence_cost_consensus_gate_report_payload(
    report: ResearchStrategyEvidenceCostConsensusGateReport | dict[str, Any],
) -> dict[str, Any]:
    if type(report) is ResearchStrategyEvidenceCostConsensusGateReport:
        _verify_report_integrity(report)
        _reject_unsafe_public_payload("report", report)
        payload = _json_ready(asdict(report))
    elif type(report) is dict:
        _require_hard_flags("payload", _DictFlags(report))
        _reject_unsafe_public_payload("payload", report)
        _verify_public_payload_integrity(report)
        payload = _json_ready(report)
    else:
        raise ValueError(
            "report must be a ResearchStrategyEvidenceCostConsensusGateReport",
        )
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    _require_hard_flags("payload", _DictFlags(payload))
    _reject_unsafe_public_payload("payload", payload)
    return payload


def research_strategy_evidence_cost_consensus_gate_report_digest(
    report: ResearchStrategyEvidenceCostConsensusGateReport,
) -> str:
    payload = research_strategy_evidence_cost_consensus_gate_report_payload(report)
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
    aggregate_hash: str
    evidence_maturity_score: Decimal
    fee_freshness_age_seconds: Decimal
    spread_freshness_age_seconds: Decimal
    slippage_freshness_age_seconds: Decimal
    cost_freshness_score: Decimal
    specialist_consensus_score: Decimal
    source_conflict_pressure: Decimal
    manual_queue_urgency: Decimal
    readiness_score: Decimal
    status: str
    reason_codes: tuple[str, ...]


def _row_value_from_input(
    value: ResearchStrategyEvidenceCostConsensusGateInput,
    *,
    config: ResearchStrategyEvidenceCostConsensusGateConfig,
) -> _RowValue:
    component_statuses = {
        "evidence_maturity": _floor_status(
            value.evidence_maturity_score,
            pass_value=config.min_pass_evidence_maturity_score,
            watch_value=config.min_watch_evidence_maturity_score,
        ),
        "fee_freshness": _ceiling_status(
            value.fee_freshness_age_seconds,
            pass_value=config.max_pass_fee_freshness_age_seconds,
            watch_value=config.max_watch_fee_freshness_age_seconds,
        ),
        "spread_freshness": _ceiling_status(
            value.spread_freshness_age_seconds,
            pass_value=config.max_pass_spread_freshness_age_seconds,
            watch_value=config.max_watch_spread_freshness_age_seconds,
        ),
        "slippage_freshness": _ceiling_status(
            value.slippage_freshness_age_seconds,
            pass_value=config.max_pass_slippage_freshness_age_seconds,
            watch_value=config.max_watch_slippage_freshness_age_seconds,
        ),
        "specialist_consensus": _floor_status(
            value.specialist_consensus_score,
            pass_value=config.min_pass_specialist_consensus_score,
            watch_value=config.min_watch_specialist_consensus_score,
        ),
        "source_conflict_pressure": _ceiling_status(
            value.source_conflict_pressure,
            pass_value=config.max_pass_source_conflict_pressure,
            watch_value=config.max_watch_source_conflict_pressure,
        ),
        "manual_queue_urgency": _ceiling_status(
            value.manual_queue_urgency,
            pass_value=config.max_pass_manual_queue_urgency,
            watch_value=config.max_watch_manual_queue_urgency,
        ),
    }
    status = _row_status(tuple(component_statuses.values()))
    cost_freshness_score = _cost_freshness_score(
        value=value,
        status=status,
        config=config,
    )
    return _RowValue(
        aggregate_hash=sha256(value.aggregation_key.encode("utf-8")).hexdigest(),
        evidence_maturity_score=value.evidence_maturity_score,
        fee_freshness_age_seconds=value.fee_freshness_age_seconds,
        spread_freshness_age_seconds=value.spread_freshness_age_seconds,
        slippage_freshness_age_seconds=value.slippage_freshness_age_seconds,
        cost_freshness_score=cost_freshness_score,
        specialist_consensus_score=value.specialist_consensus_score,
        source_conflict_pressure=value.source_conflict_pressure,
        manual_queue_urgency=value.manual_queue_urgency,
        readiness_score=_readiness_score(
            value=value,
            cost_freshness_score=cost_freshness_score,
            status=status,
        ),
        status=status,
        reason_codes=_row_reason_codes(status=status, component_statuses=component_statuses),
    )


def _row_from_value(
    *,
    index: int,
    value: _RowValue,
) -> ResearchStrategyEvidenceCostConsensusGateRow:
    return ResearchStrategyEvidenceCostConsensusGateRow(
        aggregate_row_number=_count(index),
        aggregate_hash=value.aggregate_hash,
        evidence_maturity_score=value.evidence_maturity_score,
        fee_freshness_age_seconds=value.fee_freshness_age_seconds,
        spread_freshness_age_seconds=value.spread_freshness_age_seconds,
        slippage_freshness_age_seconds=value.slippage_freshness_age_seconds,
        cost_freshness_score=value.cost_freshness_score,
        specialist_consensus_score=value.specialist_consensus_score,
        source_conflict_pressure=value.source_conflict_pressure,
        manual_queue_urgency=value.manual_queue_urgency,
        readiness_score=value.readiness_score,
        status=value.status,
        reason_codes=value.reason_codes,
    )


def _cost_freshness_score(
    *,
    value: ResearchStrategyEvidenceCostConsensusGateInput,
    status: str,
    config: ResearchStrategyEvidenceCostConsensusGateConfig,
) -> Decimal:
    if status == "block" and (
        value.fee_freshness_age_seconds > config.max_watch_fee_freshness_age_seconds
        or value.spread_freshness_age_seconds > config.max_watch_spread_freshness_age_seconds
        or value.slippage_freshness_age_seconds
        > config.max_watch_slippage_freshness_age_seconds
    ):
        return ZERO.quantize(QUANTUM)
    return _mean(
        (
            _inverse_score(
                value.fee_freshness_age_seconds,
                config.max_watch_fee_freshness_age_seconds,
            ),
            _inverse_score(
                value.spread_freshness_age_seconds,
                config.max_watch_spread_freshness_age_seconds,
            ),
            _inverse_score(
                value.slippage_freshness_age_seconds,
                config.max_watch_slippage_freshness_age_seconds,
            ),
        ),
    )


def _readiness_score(
    *,
    value: ResearchStrategyEvidenceCostConsensusGateInput,
    cost_freshness_score: Decimal,
    status: str,
) -> Decimal:
    if status == "block":
        return ZERO.quantize(QUANTUM)
    return _mean(
        (
            value.evidence_maturity_score,
            cost_freshness_score,
            value.specialist_consensus_score,
            _quantize(ONE - value.source_conflict_pressure),
            _quantize(ONE - value.manual_queue_urgency),
        ),
    )


def _inverse_score(value: Decimal, watch_value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        score = ONE - (value / watch_value)
    if score < ZERO:
        return ZERO.quantize(QUANTUM)
    if score > ONE:
        return ONE.quantize(QUANTUM)
    return _quantize(score)


def _floor_status(value: Decimal, *, pass_value: Decimal, watch_value: Decimal) -> str:
    if value < watch_value:
        return "block"
    if value < pass_value:
        return "watch"
    return "pass"


def _ceiling_status(value: Decimal, *, pass_value: Decimal, watch_value: Decimal) -> str:
    if value > watch_value:
        return "block"
    if value > pass_value:
        return "watch"
    return "pass"


def _row_status(component_statuses: tuple[str, ...]) -> str:
    if "block" in component_statuses:
        return "block"
    if "watch" in component_statuses:
        return "watch"
    return "pass"


def _row_reason_codes(
    *,
    status: str,
    component_statuses: dict[str, str],
) -> tuple[str, ...]:
    if status == "pass":
        return ("evidence_cost_consensus_gate_pass",)
    codes = [f"evidence_cost_consensus_gate_{status}"]
    for component_name in (
        "evidence_maturity",
        "fee_freshness",
        "spread_freshness",
        "slippage_freshness",
        "specialist_consensus",
        "source_conflict_pressure",
        "manual_queue_urgency",
    ):
        component_status = component_statuses[component_name]
        if component_status != "pass":
            codes.append(f"{component_name}_{component_status}")
    return tuple(codes)


def _report_status(
    rows: tuple[ResearchStrategyEvidenceCostConsensusGateRow, ...],
) -> str:
    if not rows:
        return "block"
    return _row_status(tuple(row.status for row in rows))


def _report_reason_codes(
    rows: tuple[ResearchStrategyEvidenceCostConsensusGateRow, ...],
) -> tuple[str, ...]:
    status = _report_status(rows)
    if not rows:
        return ("evidence_cost_consensus_gate_report_empty",)
    if status == "pass":
        return ("evidence_cost_consensus_gate_report_pass",)
    codes = [f"evidence_cost_consensus_gate_report_{status}"]
    row_codes = set()
    for row in rows:
        row_codes.update(row.reason_codes)
    if "evidence_maturity_block" in row_codes or "evidence_maturity_watch" in row_codes:
        codes.append("evidence_maturity_exception")
    if any(
        code in row_codes
        for code in (
            "fee_freshness_block",
            "fee_freshness_watch",
            "spread_freshness_block",
            "spread_freshness_watch",
            "slippage_freshness_block",
            "slippage_freshness_watch",
        )
    ):
        codes.append("cost_freshness_exception")
    if (
        "specialist_consensus_block" in row_codes
        or "specialist_consensus_watch" in row_codes
    ):
        codes.append("specialist_consensus_exception")
    if (
        "source_conflict_pressure_block" in row_codes
        or "source_conflict_pressure_watch" in row_codes
    ):
        codes.append("source_conflict_pressure_exception")
    if "manual_queue_urgency_block" in row_codes or "manual_queue_urgency_watch" in row_codes:
        codes.append("manual_queue_urgency_exception")
    return tuple(codes)


def _reason_code_counts_from_rows(
    rows: tuple[ResearchStrategyEvidenceCostConsensusGateRow, ...],
) -> tuple[ResearchStrategyEvidenceCostConsensusGateReasonCodeCount, ...]:
    if not rows:
        return ()
    counts: dict[str, Decimal] = {}
    for row in rows:
        for code in row.reason_codes:
            counts[code] = counts.get(code, ZERO) + COUNT_QUANTUM
    total = _count(len(rows))
    return tuple(
        ResearchStrategyEvidenceCostConsensusGateReasonCodeCount(
            reason_code=code,
            count=counts[code],
            input_ratio=_ratio(counts[code], total),
        )
        for code in ROW_REASON_CODES
        if code in counts
    )


def _normalize_inputs(
    inputs: Iterable[ResearchStrategyEvidenceCostConsensusGateInput],
) -> tuple[ResearchStrategyEvidenceCostConsensusGateInput, ...]:
    try:
        values = tuple(inputs)
    except TypeError as exc:
        raise ValueError("inputs must be iterable") from exc
    seen: set[str] = set()
    for value in values:
        if type(value) is not ResearchStrategyEvidenceCostConsensusGateInput:
            raise ValueError(
                "inputs must contain ResearchStrategyEvidenceCostConsensusGateInput",
            )
        _require_hard_flags("input", value)
        if value.aggregation_key in seen:
            raise ValueError("duplicate aggregation_key")
        seen.add(value.aggregation_key)
    return values


def _row_value_sort_key(value: _RowValue) -> tuple[int, str]:
    severity = {"block": 0, "watch": 1, "pass": 2}
    return (severity[value.status], value.aggregate_hash)


def _normalize_rows(
    rows: tuple[ResearchStrategyEvidenceCostConsensusGateRow, ...],
) -> tuple[ResearchStrategyEvidenceCostConsensusGateRow, ...]:
    if type(rows) is not tuple:
        raise ValueError("rows must be a tuple")
    last_number = ZERO
    seen_hashes: set[str] = set()
    for row in rows:
        if type(row) is not ResearchStrategyEvidenceCostConsensusGateRow:
            raise ValueError("rows must contain ResearchStrategyEvidenceCostConsensusGateRow")
        _require_hard_flags("row", row)
        if row.aggregate_row_number <= last_number:
            raise ValueError("aggregate_row_number must increase")
        if row.aggregate_hash in seen_hashes:
            raise ValueError("duplicate aggregate_hash")
        last_number = row.aggregate_row_number
        seen_hashes.add(row.aggregate_hash)
    return rows


def _normalize_reason_code_counts(
    values: tuple[ResearchStrategyEvidenceCostConsensusGateReasonCodeCount, ...],
) -> tuple[ResearchStrategyEvidenceCostConsensusGateReasonCodeCount, ...]:
    if type(values) is not tuple:
        raise ValueError("reason_code_counts must be a tuple")
    seen: set[str] = set()
    for value in values:
        if type(value) is not ResearchStrategyEvidenceCostConsensusGateReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "ResearchStrategyEvidenceCostConsensusGateReasonCodeCount",
            )
        if value.reason_code in seen:
            raise ValueError("duplicate reason_code")
        seen.add(value.reason_code)
        _require_hard_flags("reason_code_count", value)
    return values


def _validate_row_consistency(row: ResearchStrategyEvidenceCostConsensusGateRow) -> None:
    if row.status == "pass" and row.reason_codes != ("evidence_cost_consensus_gate_pass",):
        raise ValueError("pass row reason_codes must contain only pass")
    if row.status != "pass" and row.reason_codes[0] != f"evidence_cost_consensus_gate_{row.status}":
        raise ValueError("row reason_codes do not match status")
    if row.status == "block" and row.readiness_score != ZERO:
        raise ValueError("block row readiness_score must be zero")


def _validate_report_consistency(report: ResearchStrategyEvidenceCostConsensusGateReport) -> None:
    row_count = _count(len(report.rows))
    if report.input_row_count != row_count:
        raise ValueError("input_row_count must match rows")
    if report.pass_count + report.watch_count + report.block_count != report.input_row_count:
        raise ValueError("status counts must match input_row_count")
    if report.status != _report_status(report.rows):
        raise ValueError("report status must match rows")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("report reason_codes must match rows")
    if report.reason_code_counts != _reason_code_counts_from_rows(report.rows):
        raise ValueError("reason_code_counts must match rows")


def _status_count(
    rows: tuple[ResearchStrategyEvidenceCostConsensusGateRow, ...],
    status: str,
) -> Decimal:
    return _count(sum(1 for row in rows if row.status == status))


def _mean(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return ZERO.quantize(QUANTUM)
    with localcontext(DECIMAL_CONTEXT):
        return _quantize(sum(values, ZERO) / Decimal(len(values)))


def _maximum(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return ZERO.quantize(QUANTUM)
    return max(values).quantize(QUANTUM)


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO:
        return ZERO.quantize(QUANTUM)
    with localcontext(DECIMAL_CONTEXT):
        return _quantize(numerator / denominator)


def _count(value: int) -> Decimal:
    return Decimal(value).quantize(COUNT_QUANTUM)


def _normalize_positive_decimal(name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(name, value)
    if normalized <= ZERO:
        raise ValueError(f"{name} must be positive")
    return normalized


def _normalize_nonnegative_decimal(name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(name, value)
    if normalized < ZERO:
        raise ValueError(f"{name} must be nonnegative")
    return normalized


def _normalize_positive_whole_decimal(name: str, value: object) -> Decimal:
    normalized = _normalize_positive_decimal(name, value)
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{name} must be a whole Decimal")
    return normalized.quantize(COUNT_QUANTUM)


def _normalize_nonnegative_whole_decimal(name: str, value: object) -> Decimal:
    normalized = _normalize_nonnegative_decimal(name, value)
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{name} must be a whole Decimal")
    return normalized.quantize(COUNT_QUANTUM)


def _normalize_probability(name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(name, value)
    if normalized < ZERO or normalized > ONE:
        raise ValueError(f"{name} must be between 0 and 1")
    return normalized


def _normalize_decimal(name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{name} must be finite")
    return _quantize(value)


def _quantize(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(QUANTUM)


def _as_utc(name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_floor_pair(
    pass_name: str,
    pass_value: Decimal,
    watch_name: str,
    watch_value: Decimal,
) -> None:
    if pass_value <= watch_value:
        raise ValueError(f"{pass_name} must exceed {watch_name}")


def _require_ceiling_pair(pass_name: str, pass_value: Decimal, watch_value: Decimal) -> None:
    if pass_value >= watch_value:
        raise ValueError(f"{pass_name} must be below watch threshold")


def _require_exact_type(value: object, expected: type[object], name: str) -> None:
    if type(value) is not expected:
        raise ValueError(f"{name} must be a {expected.__name__}")


def _require_private_key(name: str, value: object) -> None:
    if type(value) is not str or not value.strip():
        raise ValueError(f"{name} must be a non-empty string")


def _require_public_string(name: str, value: object) -> None:
    if type(value) is not str or not value:
        raise ValueError(f"{name} must be a non-empty string")
    if _has_unsafe_text(value):
        raise ValueError(f"{name} has unsafe value")


def _require_digest(name: str, value: object) -> None:
    if type(value) is not str or len(value) != 64:
        raise ValueError(f"{name} must be a SHA-256 digest")
    if any(character not in "0123456789abcdef" for character in value):
        raise ValueError(f"{name} must be a SHA-256 digest")


def _require_status(name: str, value: object) -> None:
    if value not in RESEARCH_STRATEGY_EVIDENCE_COST_CONSENSUS_GATE_STATUSES:
        raise ValueError(f"{name} must be pass, watch, or block")


def _require_reason_code(name: str, value: object, allowed: tuple[str, ...]) -> None:
    if type(value) is not str or value not in allowed:
        raise ValueError(f"{name} is invalid")


def _normalize_reason_codes(
    name: str,
    values: tuple[str, ...],
    allowed: tuple[str, ...],
) -> tuple[str, ...]:
    if type(values) is not tuple or not values:
        raise ValueError(f"{name} must be a non-empty tuple")
    for value in values:
        _require_reason_code(name, value, allowed)
    if len(set(values)) != len(values):
        raise ValueError(f"{name} must not contain duplicates")
    return values


def _require_hard_flags(name: str, value: object) -> None:
    if getattr(value, "paper_only", None) is not True:
        raise ValueError(f"{name} paper_only must be True")
    if getattr(value, "report_only", None) is not True:
        raise ValueError(f"{name} report_only must be True")
    if getattr(value, "readonly", None) is not True:
        raise ValueError(f"{name} readonly must be True")


def _apply_or_verify_digest(value: object) -> None:
    digest = _derived_digest(value)
    current = getattr(value, "derived_validation_digest")
    if current == "":
        object.__setattr__(value, "derived_validation_digest", digest)
        return
    _require_digest("derived_validation_digest", current)
    if current != digest:
        raise ValueError("derived_validation_digest does not match public payload")


def _derived_digest(value: object) -> str:
    payload = _public_digest_payload(value)
    encoded = dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    ).encode("utf-8")
    return sha256(encoded).hexdigest()


def _public_digest_payload(value: object) -> dict[str, Any]:
    if is_dataclass(value) and not isinstance(value, type):
        payload = asdict(value)
    elif type(value) is dict:
        payload = dict(value)
    else:
        raise ValueError("value must be a dataclass or payload dict")
    payload.pop("derived_validation_digest", None)
    return _json_ready(payload)


def _verify_report_integrity(report: ResearchStrategyEvidenceCostConsensusGateReport) -> None:
    for row in report.rows:
        if row.derived_validation_digest != _derived_digest(row):
            raise ValueError("derived_validation_digest does not match row")
    if report.derived_validation_digest != _derived_digest(report):
        raise ValueError("derived_validation_digest does not match report")


def _verify_public_payload_integrity(payload: dict[str, Any]) -> None:
    rows = payload.get("rows", ())
    if type(rows) is list:
        for row in rows:
            if type(row) is not dict:
                raise ValueError("rows must contain payload objects")
            expected = row.get("derived_validation_digest")
            _require_digest("derived_validation_digest", expected)
            if expected != _derived_digest(row):
                raise ValueError("derived_validation_digest does not match row")
    expected = payload.get("derived_validation_digest")
    _require_digest("derived_validation_digest", expected)
    if expected != _derived_digest(payload):
        raise ValueError("derived_validation_digest does not match report")


def _reject_unsafe_public_payload(label: str, value: object) -> None:
    if is_dataclass(value) and not isinstance(value, type):
        _reject_unsafe_public_payload(label, asdict(value))
        return
    if type(value) is dict:
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("payload keys must be strings")
            if _has_unsafe_text(key):
                raise ValueError(f"unsafe field in {label}")
            _reject_unsafe_public_payload(label, item)
        return
    if isinstance(value, (list, tuple)):
        for item in value:
            _reject_unsafe_public_payload(label, item)
        return
    if type(value) is str and _has_unsafe_text(value):
        raise ValueError(f"unsafe value in {label}")


def _has_unsafe_text(value: str) -> bool:
    normalized = value.lower()
    return any(fragment in normalized for fragment in UNSAFE_PUBLIC_FRAGMENTS)


def _json_ready(value: Any) -> Any:
    if value is None:
        return None
    if is_dataclass(value) and not isinstance(value, type):
        return _json_ready(asdict(value))
    if isinstance(value, Decimal):
        if not value.is_finite():
            raise ValueError("Decimal value must be finite")
        return str(value)
    if isinstance(value, datetime):
        if type(value) is not datetime:
            raise ValueError("datetime value must be exact")
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("datetime value must be timezone-aware")
        return value.astimezone(UTC).isoformat()
    if type(value) is bool:
        return value
    if type(value) is int:
        raise ValueError("payload numeric value must be Decimal-derived")
    if type(value) is float:
        raise ValueError("payload numeric value must be Decimal-derived")
    if type(value) is str:
        return value
    if type(value) is dict:
        ready: dict[str, Any] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("payload keys must be strings")
            ready[key] = _json_ready(item)
        return ready
    if isinstance(value, (list, tuple)):
        return [_json_ready(item) for item in value]
    raise ValueError("value is not JSON serializable")


__all__ = (
    "DEFAULT_RESEARCH_STRATEGY_EVIDENCE_COST_CONSENSUS_GATE_REPORT_CONFIG_VERSION",
    "RESEARCH_STRATEGY_EVIDENCE_COST_CONSENSUS_GATE_STATUSES",
    "ResearchStrategyEvidenceCostConsensusGateConfig",
    "ResearchStrategyEvidenceCostConsensusGateInput",
    "ResearchStrategyEvidenceCostConsensusGateReasonCodeCount",
    "ResearchStrategyEvidenceCostConsensusGateRow",
    "ResearchStrategyEvidenceCostConsensusGateReport",
    "build_research_strategy_evidence_cost_consensus_gate_report",
    "research_strategy_evidence_cost_consensus_gate_report_payload",
    "research_strategy_evidence_cost_consensus_gate_report_digest",
)
