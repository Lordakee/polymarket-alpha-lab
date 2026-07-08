"""Pure aggregate cost freshness exception report."""

from __future__ import annotations

from dataclasses import asdict, dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
from json import dumps
from typing import Any, Iterable


DEFAULT_RESEARCH_STRATEGY_COST_FRESHNESS_EXCEPTION_REPORT_CONFIG_VERSION = (
    "research-strategy-cost-freshness-exception-report-v0"
)
RESEARCH_STRATEGY_COST_FRESHNESS_EXCEPTION_STATUSES = ("pass", "watch", "block")

QUANTUM = Decimal("0.000001")
ZERO = Decimal("0")
ONE = Decimal("1")
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
PHASE_FLAG_FIELDS = ("paper_only", "report_only", "readonly")
UNSAFE_PUBLIC_FRAGMENTS = (
    "aggregation_key",
    "candidate",
    "market",
    "slug",
    "que" + "stion",
    "source",
    "url",
    "d" + "sn",
    "table",
    "token",
    "secret",
    "credential",
)
ROW_REASON_CODES = (
    "cost_freshness_exception_pass",
    "cost_freshness_exception_watch",
    "cost_freshness_exception_block",
    "fee_observation_age_watch",
    "fee_observation_age_block",
    "spread_observation_age_watch",
    "spread_observation_age_block",
    "slippage_assumption_age_watch",
    "slippage_assumption_age_block",
    "settlement_friction_age_watch",
    "settlement_friction_age_block",
    "stale_cost_pressure_watch",
    "stale_cost_pressure_block",
    "manual_recheck_urgency_watch",
    "manual_recheck_urgency_block",
)
REPORT_REASON_CODES = (
    "cost_freshness_exception_report_empty",
    "cost_freshness_exception_report_pass",
    "cost_freshness_exception_report_watch",
    "cost_freshness_exception_report_block",
    "fee_observation_age_exception",
    "spread_observation_age_exception",
    "slippage_assumption_age_exception",
    "settlement_friction_age_exception",
    "stale_cost_pressure_exception",
    "manual_recheck_urgency_exception",
)


@dataclass(frozen=True)
class ResearchStrategyCostFreshnessExceptionConfig:
    config_version: str = (
        DEFAULT_RESEARCH_STRATEGY_COST_FRESHNESS_EXCEPTION_REPORT_CONFIG_VERSION
    )
    max_pass_fee_observation_age_seconds: Decimal = Decimal("3600.000000")
    max_watch_fee_observation_age_seconds: Decimal = Decimal("14400.000000")
    max_pass_spread_observation_age_seconds: Decimal = Decimal("300.000000")
    max_watch_spread_observation_age_seconds: Decimal = Decimal("1200.000000")
    max_pass_slippage_assumption_age_seconds: Decimal = Decimal("86400.000000")
    max_watch_slippage_assumption_age_seconds: Decimal = Decimal("259200.000000")
    max_pass_settlement_friction_age_seconds: Decimal = Decimal("604800.000000")
    max_watch_settlement_friction_age_seconds: Decimal = Decimal("1209600.000000")
    max_pass_stale_cost_pressure: Decimal = Decimal("0.300000")
    max_watch_stale_cost_pressure: Decimal = Decimal("0.700000")
    max_pass_manual_recheck_urgency: Decimal = Decimal("0.300000")
    max_watch_manual_recheck_urgency: Decimal = Decimal("0.700000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchStrategyCostFreshnessExceptionConfig, "config")
        _require_public_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_STRATEGY_COST_FRESHNESS_EXCEPTION_REPORT_CONFIG_VERSION
        ):
            raise ValueError("config_version must match the supported value")
        for field_name in (
            "max_pass_fee_observation_age_seconds",
            "max_watch_fee_observation_age_seconds",
            "max_pass_spread_observation_age_seconds",
            "max_watch_spread_observation_age_seconds",
            "max_pass_slippage_assumption_age_seconds",
            "max_watch_slippage_assumption_age_seconds",
            "max_pass_settlement_friction_age_seconds",
            "max_watch_settlement_friction_age_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_positive_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "max_pass_stale_cost_pressure",
            "max_watch_stale_cost_pressure",
            "max_pass_manual_recheck_urgency",
            "max_watch_manual_recheck_urgency",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        _require_ceiling_pair(
            "max_pass_fee_observation_age_seconds",
            self.max_pass_fee_observation_age_seconds,
            self.max_watch_fee_observation_age_seconds,
        )
        _require_ceiling_pair(
            "max_pass_spread_observation_age_seconds",
            self.max_pass_spread_observation_age_seconds,
            self.max_watch_spread_observation_age_seconds,
        )
        _require_ceiling_pair(
            "max_pass_slippage_assumption_age_seconds",
            self.max_pass_slippage_assumption_age_seconds,
            self.max_watch_slippage_assumption_age_seconds,
        )
        _require_ceiling_pair(
            "max_pass_settlement_friction_age_seconds",
            self.max_pass_settlement_friction_age_seconds,
            self.max_watch_settlement_friction_age_seconds,
        )
        _require_ceiling_pair(
            "max_pass_stale_cost_pressure",
            self.max_pass_stale_cost_pressure,
            self.max_watch_stale_cost_pressure,
        )
        _require_ceiling_pair(
            "max_pass_manual_recheck_urgency",
            self.max_pass_manual_recheck_urgency,
            self.max_watch_manual_recheck_urgency,
        )
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class ResearchStrategyCostFreshnessExceptionInput:
    aggregation_key: str
    fee_observation_age_seconds: Decimal
    spread_observation_age_seconds: Decimal
    slippage_assumption_age_seconds: Decimal
    settlement_friction_age_seconds: Decimal
    stale_cost_pressure: Decimal
    manual_recheck_urgency: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchStrategyCostFreshnessExceptionInput, "input")
        _require_input_key("aggregation_key", self.aggregation_key)
        for field_name in (
            "fee_observation_age_seconds",
            "spread_observation_age_seconds",
            "slippage_assumption_age_seconds",
            "settlement_friction_age_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in ("stale_cost_pressure", "manual_recheck_urgency"):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        _require_hard_flags("input", self)


@dataclass(frozen=True)
class ResearchStrategyCostFreshnessExceptionReasonCodeCount:
    reason_code: str
    count: Decimal
    input_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_reason_code("reason_code", self.reason_code)
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
class ResearchStrategyCostFreshnessExceptionRow:
    aggregate_row_number: Decimal
    aggregate_hash: str
    fee_observation_age_seconds: Decimal
    spread_observation_age_seconds: Decimal
    slippage_assumption_age_seconds: Decimal
    settlement_friction_age_seconds: Decimal
    stale_cost_pressure: Decimal
    manual_recheck_urgency: Decimal
    cost_freshness_exception_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchStrategyCostFreshnessExceptionRow, "row")
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
            "fee_observation_age_seconds",
            "spread_observation_age_seconds",
            "slippage_assumption_age_seconds",
            "settlement_friction_age_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "stale_cost_pressure",
            "manual_recheck_urgency",
            "cost_freshness_exception_score",
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
class ResearchStrategyCostFreshnessExceptionReport:
    generated_at: datetime
    config_version: str
    input_row_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    mean_fee_observation_age_seconds: Decimal
    mean_spread_observation_age_seconds: Decimal
    mean_slippage_assumption_age_seconds: Decimal
    mean_settlement_friction_age_seconds: Decimal
    max_stale_cost_pressure: Decimal
    max_manual_recheck_urgency: Decimal
    mean_cost_freshness_exception_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    reason_code_counts: tuple[ResearchStrategyCostFreshnessExceptionReasonCodeCount, ...]
    rows: tuple[ResearchStrategyCostFreshnessExceptionRow, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchStrategyCostFreshnessExceptionReport, "report")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_string("config_version", self.config_version)
        for field_name in ("input_row_count", "pass_count", "watch_count", "block_count"):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_whole_decimal(
                    field_name,
                    getattr(self, field_name),
                ),
            )
        for field_name in (
            "mean_fee_observation_age_seconds",
            "mean_spread_observation_age_seconds",
            "mean_slippage_assumption_age_seconds",
            "mean_settlement_friction_age_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "max_stale_cost_pressure",
            "max_manual_recheck_urgency",
            "mean_cost_freshness_exception_score",
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


def build_research_strategy_cost_freshness_exception_report(
    inputs: Iterable[ResearchStrategyCostFreshnessExceptionInput],
    *,
    config: ResearchStrategyCostFreshnessExceptionConfig,
    generated_at: datetime,
) -> ResearchStrategyCostFreshnessExceptionReport:
    if type(config) is not ResearchStrategyCostFreshnessExceptionConfig:
        raise ValueError(
            "config must be a ResearchStrategyCostFreshnessExceptionConfig",
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
    return ResearchStrategyCostFreshnessExceptionReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        input_row_count=_count(len(rows)),
        pass_count=_status_count(rows, "pass"),
        watch_count=_status_count(rows, "watch"),
        block_count=_status_count(rows, "block"),
        mean_fee_observation_age_seconds=_mean(
            tuple(row.fee_observation_age_seconds for row in rows),
        ),
        mean_spread_observation_age_seconds=_mean(
            tuple(row.spread_observation_age_seconds for row in rows),
        ),
        mean_slippage_assumption_age_seconds=_mean(
            tuple(row.slippage_assumption_age_seconds for row in rows),
        ),
        mean_settlement_friction_age_seconds=_mean(
            tuple(row.settlement_friction_age_seconds for row in rows),
        ),
        max_stale_cost_pressure=_maximum(
            tuple(row.stale_cost_pressure for row in rows),
        ),
        max_manual_recheck_urgency=_maximum(
            tuple(row.manual_recheck_urgency for row in rows),
        ),
        mean_cost_freshness_exception_score=_mean(
            tuple(row.cost_freshness_exception_score for row in rows),
        ),
        status=_report_status(rows),
        reason_codes=_report_reason_codes(rows),
        reason_code_counts=_reason_code_counts_from_rows(rows),
        rows=rows,
    )


def research_strategy_cost_freshness_exception_report_payload(
    report: ResearchStrategyCostFreshnessExceptionReport | dict[str, Any],
) -> dict[str, Any]:
    if type(report) is ResearchStrategyCostFreshnessExceptionReport:
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
            "report must be a ResearchStrategyCostFreshnessExceptionReport",
        )
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    _require_hard_flags("payload", _DictFlags(payload))
    _reject_unsafe_public_payload("payload", payload)
    return payload


def research_strategy_cost_freshness_exception_report_digest(
    report: ResearchStrategyCostFreshnessExceptionReport,
) -> str:
    payload = research_strategy_cost_freshness_exception_report_payload(report)
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
    fee_observation_age_seconds: Decimal
    spread_observation_age_seconds: Decimal
    slippage_assumption_age_seconds: Decimal
    settlement_friction_age_seconds: Decimal
    stale_cost_pressure: Decimal
    manual_recheck_urgency: Decimal
    cost_freshness_exception_score: Decimal
    status: str
    reason_codes: tuple[str, ...]


def _row_value_from_input(
    value: ResearchStrategyCostFreshnessExceptionInput,
    *,
    config: ResearchStrategyCostFreshnessExceptionConfig,
) -> _RowValue:
    component_statuses = {
        "fee_observation_age": _ceiling_status(
            value.fee_observation_age_seconds,
            pass_value=config.max_pass_fee_observation_age_seconds,
            watch_value=config.max_watch_fee_observation_age_seconds,
        ),
        "spread_observation_age": _ceiling_status(
            value.spread_observation_age_seconds,
            pass_value=config.max_pass_spread_observation_age_seconds,
            watch_value=config.max_watch_spread_observation_age_seconds,
        ),
        "slippage_assumption_age": _ceiling_status(
            value.slippage_assumption_age_seconds,
            pass_value=config.max_pass_slippage_assumption_age_seconds,
            watch_value=config.max_watch_slippage_assumption_age_seconds,
        ),
        "settlement_friction_age": _ceiling_status(
            value.settlement_friction_age_seconds,
            pass_value=config.max_pass_settlement_friction_age_seconds,
            watch_value=config.max_watch_settlement_friction_age_seconds,
        ),
        "stale_cost_pressure": _ceiling_status(
            value.stale_cost_pressure,
            pass_value=config.max_pass_stale_cost_pressure,
            watch_value=config.max_watch_stale_cost_pressure,
        ),
        "manual_recheck_urgency": _ceiling_status(
            value.manual_recheck_urgency,
            pass_value=config.max_pass_manual_recheck_urgency,
            watch_value=config.max_watch_manual_recheck_urgency,
        ),
    }
    status = _row_status(tuple(component_statuses.values()))
    return _RowValue(
        aggregate_hash=sha256(value.aggregation_key.encode("utf-8")).hexdigest(),
        fee_observation_age_seconds=value.fee_observation_age_seconds,
        spread_observation_age_seconds=value.spread_observation_age_seconds,
        slippage_assumption_age_seconds=value.slippage_assumption_age_seconds,
        settlement_friction_age_seconds=value.settlement_friction_age_seconds,
        stale_cost_pressure=value.stale_cost_pressure,
        manual_recheck_urgency=value.manual_recheck_urgency,
        cost_freshness_exception_score=_exception_score(
            value=value,
            status=status,
            config=config,
        ),
        status=status,
        reason_codes=_row_reason_codes(status=status, component_statuses=component_statuses),
    )


def _row_from_value(*, index: int, value: _RowValue) -> ResearchStrategyCostFreshnessExceptionRow:
    return ResearchStrategyCostFreshnessExceptionRow(
        aggregate_row_number=_count(index),
        aggregate_hash=value.aggregate_hash,
        fee_observation_age_seconds=value.fee_observation_age_seconds,
        spread_observation_age_seconds=value.spread_observation_age_seconds,
        slippage_assumption_age_seconds=value.slippage_assumption_age_seconds,
        settlement_friction_age_seconds=value.settlement_friction_age_seconds,
        stale_cost_pressure=value.stale_cost_pressure,
        manual_recheck_urgency=value.manual_recheck_urgency,
        cost_freshness_exception_score=value.cost_freshness_exception_score,
        status=value.status,
        reason_codes=value.reason_codes,
    )


def _exception_score(
    *,
    value: ResearchStrategyCostFreshnessExceptionInput,
    status: str,
    config: ResearchStrategyCostFreshnessExceptionConfig,
) -> Decimal:
    if status == "block":
        return ZERO.quantize(QUANTUM)
    return _mean(
        (
            _inverse_score(
                value.fee_observation_age_seconds,
                config.max_watch_fee_observation_age_seconds,
            ),
            _inverse_score(
                value.spread_observation_age_seconds,
                config.max_watch_spread_observation_age_seconds,
            ),
            _inverse_score(
                value.slippage_assumption_age_seconds,
                config.max_watch_slippage_assumption_age_seconds,
            ),
            _inverse_score(
                value.settlement_friction_age_seconds,
                config.max_watch_settlement_friction_age_seconds,
            ),
            _quantize(ONE - value.stale_cost_pressure),
            _quantize(ONE - value.manual_recheck_urgency),
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
        return ("cost_freshness_exception_pass",)
    codes = [f"cost_freshness_exception_{status}"]
    for component_name in (
        "fee_observation_age",
        "spread_observation_age",
        "slippage_assumption_age",
        "settlement_friction_age",
        "stale_cost_pressure",
        "manual_recheck_urgency",
    ):
        component_status = component_statuses[component_name]
        if component_status != "pass":
            codes.append(f"{component_name}_{component_status}")
    return _normalize_reason_codes("reason_codes", tuple(codes), ROW_REASON_CODES)


def _report_status(
    rows: tuple[ResearchStrategyCostFreshnessExceptionRow, ...],
) -> str:
    if not rows:
        return "block"
    if any(row.status == "block" for row in rows):
        return "block"
    if any(row.status == "watch" for row in rows):
        return "watch"
    return "pass"


def _report_reason_codes(
    rows: tuple[ResearchStrategyCostFreshnessExceptionRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return ("cost_freshness_exception_report_empty",)
    report_status = _report_status(rows)
    codes = [f"cost_freshness_exception_report_{report_status}"]
    row_codes = tuple(code for row in rows for code in row.reason_codes)
    for component_name, report_reason in (
        ("fee_observation_age_", "fee_observation_age_exception"),
        ("spread_observation_age_", "spread_observation_age_exception"),
        ("slippage_assumption_age_", "slippage_assumption_age_exception"),
        ("settlement_friction_age_", "settlement_friction_age_exception"),
        ("stale_cost_pressure_", "stale_cost_pressure_exception"),
        ("manual_recheck_urgency_", "manual_recheck_urgency_exception"),
    ):
        if any(code.startswith(component_name) for code in row_codes):
            codes.append(report_reason)
    return _normalize_reason_codes("reason_codes", tuple(codes), REPORT_REASON_CODES)


def _row_value_sort_key(value: _RowValue) -> tuple[int, Decimal, str]:
    return (
        {"block": 0, "watch": 1, "pass": 2}[value.status],
        value.cost_freshness_exception_score,
        value.aggregate_hash,
    )


def _row_sort_key(row: ResearchStrategyCostFreshnessExceptionRow) -> tuple[int, Decimal, str]:
    return (
        {"block": 0, "watch": 1, "pass": 2}[row.status],
        row.cost_freshness_exception_score,
        row.aggregate_hash,
    )


def _normalize_inputs(
    inputs: Iterable[ResearchStrategyCostFreshnessExceptionInput],
) -> tuple[ResearchStrategyCostFreshnessExceptionInput, ...]:
    if isinstance(inputs, (str, bytes)):
        raise ValueError("inputs must be an iterable")
    try:
        normalized = tuple(inputs)
    except TypeError as exc:
        raise ValueError("inputs must be an iterable") from exc
    seen_keys: set[str] = set()
    for value in normalized:
        if type(value) is not ResearchStrategyCostFreshnessExceptionInput:
            raise ValueError(
                "inputs must contain ResearchStrategyCostFreshnessExceptionInput values",
            )
        _require_hard_flags("input", value)
        if value.aggregation_key in seen_keys:
            raise ValueError("inputs must not contain duplicate aggregation_key values")
        seen_keys.add(value.aggregation_key)
    return normalized


def _normalize_rows(
    rows: Iterable[ResearchStrategyCostFreshnessExceptionRow],
) -> tuple[ResearchStrategyCostFreshnessExceptionRow, ...]:
    if isinstance(rows, (str, bytes)):
        raise ValueError("rows must be an iterable")
    try:
        normalized = tuple(rows)
    except TypeError as exc:
        raise ValueError("rows must be an iterable") from exc
    seen_hashes: set[str] = set()
    for row in normalized:
        if type(row) is not ResearchStrategyCostFreshnessExceptionRow:
            raise ValueError(
                "rows must contain ResearchStrategyCostFreshnessExceptionRow values",
            )
        _require_hard_flags("row", row)
        _verify_digest(row)
        if row.aggregate_hash in seen_hashes:
            raise ValueError("rows must not contain duplicate aggregate_hash values")
        seen_hashes.add(row.aggregate_hash)
    return normalized


def _normalize_reason_code_counts(
    value: Iterable[ResearchStrategyCostFreshnessExceptionReasonCodeCount],
) -> tuple[ResearchStrategyCostFreshnessExceptionReasonCodeCount, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError("reason_code_counts must be an iterable")
    try:
        rows = tuple(value)
    except TypeError as exc:
        raise ValueError("reason_code_counts must be an iterable") from exc
    for row in rows:
        if type(row) is not ResearchStrategyCostFreshnessExceptionReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "ResearchStrategyCostFreshnessExceptionReasonCodeCount values",
            )
        _require_hard_flags("reason_code_count", row)
    return rows


def _validate_row_consistency(row: ResearchStrategyCostFreshnessExceptionRow) -> None:
    if row.status == "pass" and row.reason_codes != ("cost_freshness_exception_pass",):
        raise ValueError("pass rows must only contain pass reason code")
    if row.status == "watch" and not any(code.endswith("_watch") for code in row.reason_codes):
        raise ValueError("watch rows must contain watch reason code")
    if row.status == "block" and not any(code.endswith("_block") for code in row.reason_codes):
        raise ValueError("block rows must contain block reason code")


def _validate_report_consistency(report: ResearchStrategyCostFreshnessExceptionReport) -> None:
    if report.input_row_count != _count(len(report.rows)):
        raise ValueError("input_row_count must match rows")
    if report.input_row_count != report.pass_count + report.watch_count + report.block_count:
        raise ValueError("status counts must match input_row_count")
    if report.pass_count != _status_count(report.rows, "pass"):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _status_count(report.rows, "watch"):
        raise ValueError("watch_count must match rows")
    if report.block_count != _status_count(report.rows, "block"):
        raise ValueError("block_count must match rows")
    if report.mean_fee_observation_age_seconds != _mean(
        tuple(row.fee_observation_age_seconds for row in report.rows),
    ):
        raise ValueError("mean_fee_observation_age_seconds must match rows")
    if report.mean_spread_observation_age_seconds != _mean(
        tuple(row.spread_observation_age_seconds for row in report.rows),
    ):
        raise ValueError("mean_spread_observation_age_seconds must match rows")
    if report.mean_slippage_assumption_age_seconds != _mean(
        tuple(row.slippage_assumption_age_seconds for row in report.rows),
    ):
        raise ValueError("mean_slippage_assumption_age_seconds must match rows")
    if report.mean_settlement_friction_age_seconds != _mean(
        tuple(row.settlement_friction_age_seconds for row in report.rows),
    ):
        raise ValueError("mean_settlement_friction_age_seconds must match rows")
    if report.max_stale_cost_pressure != _maximum(
        tuple(row.stale_cost_pressure for row in report.rows),
    ):
        raise ValueError("max_stale_cost_pressure must match rows")
    if report.max_manual_recheck_urgency != _maximum(
        tuple(row.manual_recheck_urgency for row in report.rows),
    ):
        raise ValueError("max_manual_recheck_urgency must match rows")
    if report.mean_cost_freshness_exception_score != _mean(
        tuple(row.cost_freshness_exception_score for row in report.rows),
    ):
        raise ValueError("mean_cost_freshness_exception_score must match rows")
    if report.status != _report_status(report.rows):
        raise ValueError("status must match rows")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")
    if report.reason_code_counts != _reason_code_counts_from_rows(report.rows):
        raise ValueError("reason_code_counts must match rows")
    if tuple(row.aggregate_row_number for row in report.rows) != tuple(
        _count(index) for index in range(1, len(report.rows) + 1)
    ):
        raise ValueError("aggregate_row_number must be deterministic")
    if tuple(sorted(report.rows, key=_row_sort_key)) != report.rows:
        raise ValueError("rows must use deterministic sequence")


def _verify_report_integrity(report: ResearchStrategyCostFreshnessExceptionReport) -> None:
    _verify_digest(report)
    _validate_report_consistency(report)
    for row in report.rows:
        _verify_digest(row)


def _verify_public_payload_integrity(payload: dict[str, Any]) -> None:
    _verify_public_payload_digest("payload", payload)
    rows = payload.get("rows")
    if rows is None:
        return
    if type(rows) is not list:
        raise ValueError("payload.rows must be a list")
    for index, row in enumerate(rows):
        if type(row) is not dict:
            raise ValueError("payload.rows must contain JSON objects")
        _verify_public_payload_digest(f"payload.rows[{index}]", row)


def _verify_public_payload_digest(label: str, payload: dict[str, Any]) -> None:
    provided = payload.get("derived_validation_digest")
    _require_digest(f"{label}.derived_validation_digest", provided)
    digest_input = dict(payload)
    digest_input.pop("derived_validation_digest", None)
    expected = _public_digest(digest_input)
    if provided != expected:
        raise ValueError("derived_validation_digest does not match public payload")


def _reason_code_counts_from_rows(
    rows: tuple[ResearchStrategyCostFreshnessExceptionRow, ...],
) -> tuple[ResearchStrategyCostFreshnessExceptionReasonCodeCount, ...]:
    if not rows:
        return ()
    counts: dict[str, int] = {}
    for row in rows:
        for reason_code in row.reason_codes:
            counts[reason_code] = counts.get(reason_code, 0) + 1
    denominator = _count(len(rows))
    return tuple(
        ResearchStrategyCostFreshnessExceptionReasonCodeCount(
            reason_code=reason_code,
            count=_count(count),
            input_ratio=_divide(_count(count), denominator),
        )
        for reason_code, count in sorted(
            counts.items(),
            key=lambda item: (-item[1], item[0]),
        )
    )


def _status_count(
    rows: tuple[ResearchStrategyCostFreshnessExceptionRow, ...],
    status: str,
) -> Decimal:
    return _count(sum(1 for row in rows if row.status == status))


def _mean(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return ZERO.quantize(QUANTUM)
    return _divide(_sum(values), _count(len(values)))


def _maximum(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return ZERO.quantize(QUANTUM)
    return max(values)


def _sum(values: tuple[Decimal, ...]) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return _quantize(sum(values, ZERO))


def _divide(left: Decimal, right: Decimal) -> Decimal:
    if right == ZERO:
        return ZERO.quantize(QUANTUM)
    with localcontext(DECIMAL_CONTEXT):
        return _quantize(left / right)


def _count(value: int) -> Decimal:
    return Decimal(value).quantize(QUANTUM)


def _normalize_probability(name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(name, value)
    if normalized < ZERO or normalized > ONE:
        raise ValueError(f"{name} must be between 0 and 1")
    return normalized


def _normalize_nonnegative_decimal(name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(name, value)
    if normalized < ZERO:
        raise ValueError(f"{name} must be nonnegative")
    return normalized


def _normalize_positive_decimal(name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(name, value)
    if normalized <= ZERO:
        raise ValueError(f"{name} must be positive")
    return normalized


def _normalize_nonnegative_whole_decimal(name: str, value: object) -> Decimal:
    normalized = _normalize_nonnegative_decimal(name, value)
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{name} must be a whole Decimal")
    return normalized


def _normalize_positive_whole_decimal(name: str, value: object) -> Decimal:
    normalized = _normalize_positive_decimal(name, value)
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{name} must be a whole Decimal")
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


def _require_ceiling_pair(name: str, pass_value: Decimal, watch_value: Decimal) -> None:
    if pass_value > watch_value:
        raise ValueError(f"{name} must not exceed watch threshold")


def _require_exact_type(value: object, expected_type: type[object], label: str) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{label} must be a {expected_type.__name__}")


def _require_status(name: str, value: object) -> None:
    if (
        type(value) is not str
        or value not in RESEARCH_STRATEGY_COST_FRESHNESS_EXCEPTION_STATUSES
    ):
        raise ValueError(f"{name} must be pass, watch, or block")


def _require_reason_code(name: str, value: object) -> None:
    if type(value) is not str or not value:
        raise ValueError(f"{name} must be a non-empty string")
    _require_public_string(name, value)
    if value not in ROW_REASON_CODES and value not in REPORT_REASON_CODES:
        raise ValueError(f"{name} is not supported")


def _normalize_reason_codes(
    name: str,
    value: tuple[str, ...],
    supported: tuple[str, ...],
) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ValueError(f"{name} must be a tuple")
    for reason_code in value:
        _require_reason_code(name, reason_code)
        if reason_code not in supported:
            raise ValueError(f"{name} contains an unsupported reason code")
    if len(set(value)) != len(value):
        raise ValueError(f"{name} must not contain duplicates")
    return value


def _require_public_string(name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{name} must be a string")
    if not value or value != value.strip():
        raise ValueError(f"{name} must be a canonical public string")


def _require_input_key(name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{name} must be a string")
    if not value or value != value.strip():
        raise ValueError(f"{name} must be canonical")


def _require_hard_flags(name: str, value: object) -> None:
    for field_name in PHASE_FLAG_FIELDS:
        if getattr(value, field_name, None) is not True:
            raise ValueError(f"{name} {field_name} must be True")


def _require_digest(name: str, value: object) -> None:
    if type(value) is not str or len(value) != 64:
        raise ValueError(f"{name} must be a SHA-256 digest")
    lowered = value.lower()
    if lowered != value or any(character not in "0123456789abcdef" for character in value):
        raise ValueError(f"{name} must be a SHA-256 digest")


def _apply_or_verify_digest(value: object) -> None:
    provided = getattr(value, "derived_validation_digest")
    if provided:
        _verify_digest(value)
    else:
        object.__setattr__(value, "derived_validation_digest", _digest_for_value(value))


def _verify_digest(value: object) -> None:
    provided = getattr(value, "derived_validation_digest", None)
    _require_digest("derived_validation_digest", provided)
    expected = _digest_for_value(value)
    if provided != expected:
        raise ValueError("derived_validation_digest does not match public payload")


def _digest_for_value(value: object) -> str:
    if is_dataclass(value) and not isinstance(value, type):
        digest_input = asdict(value)
    elif type(value) is dict:
        digest_input = dict(value)
    else:
        raise ValueError("value must be digestible")
    digest_input.pop("derived_validation_digest", None)
    return _public_digest(digest_input)


def _public_digest(value: object) -> str:
    encoded = dumps(
        _json_ready(value),
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    ).encode("utf-8")
    return sha256(encoded).hexdigest()


def _reject_unsafe_public_payload(label: str, value: object) -> None:
    if is_dataclass(value) and not isinstance(value, type):
        _reject_unsafe_public_payload(label, asdict(value))
        return
    if type(value) is dict:
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("public payload keys must be strings")
            if _has_unsafe_public_text(key):
                raise ValueError(f"unsafe public field in {label}")
            _reject_unsafe_public_payload(label, item)
        return
    if isinstance(value, (list, tuple)):
        for item in value:
            _reject_unsafe_public_payload(label, item)
        return
    if type(value) is str and _has_unsafe_public_text(value):
        raise ValueError(f"unsafe public value in {label}")


def _has_unsafe_public_text(value: str) -> bool:
    lowered = value.lower()
    return any(fragment in lowered for fragment in UNSAFE_PUBLIC_FRAGMENTS)


def _verify_public_payload_shape(value: object) -> None:
    if type(value) is int or type(value) is float:
        raise ValueError("public payload numerics must be Decimal strings")
    if type(value) is dict:
        for item in value.values():
            _verify_public_payload_shape(item)
    elif isinstance(value, list):
        for item in value:
            _verify_public_payload_shape(item)


def _json_ready(value: Any) -> Any:
    if value is None:
        return None
    if is_dataclass(value) and not isinstance(value, type):
        return _json_ready(asdict(value))
    if isinstance(value, Decimal):
        if not value.is_finite():
            raise ValueError("Decimal payload value must be finite")
        return str(value)
    if isinstance(value, datetime):
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("datetime payload value must be timezone-aware")
        return value.astimezone(UTC).isoformat()
    if isinstance(value, tuple):
        return [_json_ready(item) for item in value]
    if isinstance(value, list):
        return [_json_ready(item) for item in value]
    if type(value) is dict:
        ready: dict[str, Any] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("payload keys must be strings")
            ready[key] = _json_ready(item)
        return ready
    if type(value) is bool or type(value) is str:
        return value
    if type(value) is int or type(value) is float:
        raise ValueError("payload value must not be a numeric primitive")
    raise ValueError("payload value is not supported")


__all__ = (
    "DEFAULT_RESEARCH_STRATEGY_COST_FRESHNESS_EXCEPTION_REPORT_CONFIG_VERSION",
    "RESEARCH_STRATEGY_COST_FRESHNESS_EXCEPTION_STATUSES",
    "ResearchStrategyCostFreshnessExceptionConfig",
    "ResearchStrategyCostFreshnessExceptionInput",
    "ResearchStrategyCostFreshnessExceptionReasonCodeCount",
    "ResearchStrategyCostFreshnessExceptionRow",
    "ResearchStrategyCostFreshnessExceptionReport",
    "build_research_strategy_cost_freshness_exception_report",
    "research_strategy_cost_freshness_exception_report_payload",
    "research_strategy_cost_freshness_exception_report_digest",
)
