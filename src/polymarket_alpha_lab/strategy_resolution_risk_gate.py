"""Pure report-only gate for strategy resolution risk."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from decimal import Context, Decimal, localcontext
from typing import Any


DEFAULT_STRATEGY_RESOLUTION_RISK_GATE_CONFIG_VERSION = (
    "strategy-resolution-risk-gate-v0"
)
QUANTUM = Decimal("0.000001")
COUNT_QUANTUM = Decimal("1")
ZERO = Decimal("0")
ONE = Decimal("1")
DECIMAL_CONTEXT = Context(prec=64)

PASS_REASON_CODE = "strategy_resolution_risk_gate_passed"
BLOCKING_REASON_CODES = (
    "ambiguous_resolution_rules",
    "missing_official_sources",
    "severe_dispute_history",
    "imminent_resolution_window",
    "excessive_resolution_dependencies",
)
WATCH_REASON_CODES = (
    "weak_rule_clarity",
    "limited_official_sources",
    "elevated_dispute_history",
    "near_resolution_time_pressure",
    "resolution_dependency_load",
)
REASON_CODES = BLOCKING_REASON_CODES + WATCH_REASON_CODES + (PASS_REASON_CODE,)
NEXT_STEP_BY_STATUS = {
    "pass": "allow_strategy_resolution_risk_gate",
    "watch": "refresh_strategy_resolution_risk_evidence",
    "blocked": "block_strategy_resolution_risk_gate",
}


@dataclass(frozen=True)
class StrategyResolutionRiskGateConfig:
    config_version: str = DEFAULT_STRATEGY_RESOLUTION_RISK_GATE_CONFIG_VERSION
    pass_rule_clarity_score: Decimal = Decimal("0.800000")
    block_rule_clarity_score: Decimal = Decimal("0.500000")
    pass_official_source_count: Decimal = Decimal("2")
    block_official_source_count: Decimal = Decimal("1")
    pass_dispute_history_score: Decimal = Decimal("0.300000")
    block_dispute_history_score: Decimal = Decimal("0.600000")
    pass_time_to_resolution_hours: Decimal = Decimal("24.000000")
    block_time_to_resolution_hours: Decimal = Decimal("6.000000")
    pass_resolution_dependency_count: Decimal = Decimal("1")
    block_resolution_dependency_count: Decimal = Decimal("3")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not StrategyResolutionRiskGateConfig:
            raise ValueError("config must be a StrategyResolutionRiskGateConfig")
        _require_canonical_string("config_version", self.config_version)
        object.__setattr__(
            self,
            "pass_rule_clarity_score",
            _normalize_ratio("pass_rule_clarity_score", self.pass_rule_clarity_score),
        )
        object.__setattr__(
            self,
            "block_rule_clarity_score",
            _normalize_ratio("block_rule_clarity_score", self.block_rule_clarity_score),
        )
        object.__setattr__(
            self,
            "pass_official_source_count",
            _normalize_positive_whole_decimal(
                "pass_official_source_count",
                self.pass_official_source_count,
            ),
        )
        object.__setattr__(
            self,
            "block_official_source_count",
            _normalize_positive_whole_decimal(
                "block_official_source_count",
                self.block_official_source_count,
            ),
        )
        object.__setattr__(
            self,
            "pass_dispute_history_score",
            _normalize_ratio(
                "pass_dispute_history_score",
                self.pass_dispute_history_score,
            ),
        )
        object.__setattr__(
            self,
            "block_dispute_history_score",
            _normalize_ratio(
                "block_dispute_history_score",
                self.block_dispute_history_score,
            ),
        )
        object.__setattr__(
            self,
            "pass_time_to_resolution_hours",
            _normalize_positive_decimal(
                "pass_time_to_resolution_hours",
                self.pass_time_to_resolution_hours,
            ),
        )
        object.__setattr__(
            self,
            "block_time_to_resolution_hours",
            _normalize_nonnegative_decimal(
                "block_time_to_resolution_hours",
                self.block_time_to_resolution_hours,
            ),
        )
        object.__setattr__(
            self,
            "pass_resolution_dependency_count",
            _normalize_nonnegative_whole_decimal(
                "pass_resolution_dependency_count",
                self.pass_resolution_dependency_count,
            ),
        )
        object.__setattr__(
            self,
            "block_resolution_dependency_count",
            _normalize_positive_whole_decimal(
                "block_resolution_dependency_count",
                self.block_resolution_dependency_count,
            ),
        )
        if self.block_rule_clarity_score >= self.pass_rule_clarity_score:
            raise ValueError(
                "block_rule_clarity_score must be below pass_rule_clarity_score",
            )
        if self.block_official_source_count >= self.pass_official_source_count:
            raise ValueError(
                "block_official_source_count must be below pass_official_source_count",
            )
        if self.pass_dispute_history_score >= self.block_dispute_history_score:
            raise ValueError(
                "pass_dispute_history_score must be below block_dispute_history_score",
            )
        if self.block_time_to_resolution_hours >= self.pass_time_to_resolution_hours:
            raise ValueError(
                "block_time_to_resolution_hours must be below "
                "pass_time_to_resolution_hours",
            )
        if self.pass_resolution_dependency_count >= self.block_resolution_dependency_count:
            raise ValueError(
                "pass_resolution_dependency_count must be below "
                "block_resolution_dependency_count",
            )
        _require_hard_flags(self)


@dataclass(frozen=True)
class StrategyResolutionRiskGateMetrics:
    rule_clarity_score: Decimal
    official_source_count: Decimal
    dispute_history_score: Decimal
    time_to_resolution_hours: Decimal
    resolution_dependency_count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not StrategyResolutionRiskGateMetrics:
            raise ValueError("metrics must be a StrategyResolutionRiskGateMetrics")
        object.__setattr__(
            self,
            "rule_clarity_score",
            _normalize_ratio("rule_clarity_score", self.rule_clarity_score),
        )
        object.__setattr__(
            self,
            "official_source_count",
            _normalize_nonnegative_whole_decimal(
                "official_source_count",
                self.official_source_count,
            ),
        )
        object.__setattr__(
            self,
            "dispute_history_score",
            _normalize_ratio("dispute_history_score", self.dispute_history_score),
        )
        object.__setattr__(
            self,
            "time_to_resolution_hours",
            _normalize_nonnegative_decimal(
                "time_to_resolution_hours",
                self.time_to_resolution_hours,
            ),
        )
        object.__setattr__(
            self,
            "resolution_dependency_count",
            _normalize_nonnegative_whole_decimal(
                "resolution_dependency_count",
                self.resolution_dependency_count,
            ),
        )
        _require_hard_flags(self)


@dataclass(frozen=True)
class StrategyResolutionRiskGateReasonCodeCount:
    reason_code: str
    count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not StrategyResolutionRiskGateReasonCodeCount:
            raise ValueError("reason row must be a StrategyResolutionRiskGateReasonCodeCount")
        _require_reason_code("reason_code", self.reason_code)
        object.__setattr__(
            self,
            "count",
            _normalize_positive_whole_decimal("count", self.count),
        )
        _require_hard_flags(self)


@dataclass(frozen=True)
class StrategyResolutionRiskGateReport:
    config_version: str
    gate_status: str
    recommended_next_step: str
    rule_clarity_score: Decimal
    official_source_count: Decimal
    dispute_history_score: Decimal
    time_to_resolution_hours: Decimal
    resolution_dependency_count: Decimal
    reason_codes: tuple[str, ...]
    reason_code_counts: tuple[StrategyResolutionRiskGateReasonCodeCount, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not StrategyResolutionRiskGateReport:
            raise ValueError("report must be a StrategyResolutionRiskGateReport")
        _require_canonical_string("config_version", self.config_version)
        _require_gate_status("gate_status", self.gate_status)
        _require_canonical_string("recommended_next_step", self.recommended_next_step)
        if self.recommended_next_step != NEXT_STEP_BY_STATUS[self.gate_status]:
            raise ValueError("recommended_next_step must match gate_status")
        object.__setattr__(
            self,
            "rule_clarity_score",
            _normalize_ratio("rule_clarity_score", self.rule_clarity_score),
        )
        object.__setattr__(
            self,
            "official_source_count",
            _normalize_nonnegative_whole_decimal(
                "official_source_count",
                self.official_source_count,
            ),
        )
        object.__setattr__(
            self,
            "dispute_history_score",
            _normalize_ratio("dispute_history_score", self.dispute_history_score),
        )
        object.__setattr__(
            self,
            "time_to_resolution_hours",
            _normalize_nonnegative_decimal(
                "time_to_resolution_hours",
                self.time_to_resolution_hours,
            ),
        )
        object.__setattr__(
            self,
            "resolution_dependency_count",
            _normalize_nonnegative_whole_decimal(
                "resolution_dependency_count",
                self.resolution_dependency_count,
            ),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        if self.gate_status != _status_from_reason_codes(self.reason_codes):
            raise ValueError("gate_status must match reason_codes")
        if self.gate_status == "pass" and self.reason_codes != (PASS_REASON_CODE,):
            raise ValueError("pass gate must have the pass reason_code")
        if self.gate_status != "pass" and PASS_REASON_CODE in self.reason_codes:
            raise ValueError("non-pass gate must not have the pass reason_code")
        if tuple(row.reason_code for row in self.reason_code_counts) != self.reason_codes:
            raise ValueError("reason_code_counts must match reason_codes")
        _require_hard_flags(self)


def build_strategy_resolution_risk_gate_report(
    metrics: StrategyResolutionRiskGateMetrics,
    *,
    config: StrategyResolutionRiskGateConfig,
) -> StrategyResolutionRiskGateReport:
    """Aggregate resolution metrics into a pure pass/watch/blocked report."""

    if type(metrics) is not StrategyResolutionRiskGateMetrics:
        raise ValueError("metrics must be a StrategyResolutionRiskGateMetrics")
    if type(config) is not StrategyResolutionRiskGateConfig:
        raise ValueError("config must be a StrategyResolutionRiskGateConfig")
    _require_hard_flags(metrics)
    _require_hard_flags(config)
    reason_codes = _reason_codes_for_metrics(metrics, config)
    gate_status = _status_from_reason_codes(reason_codes)

    return StrategyResolutionRiskGateReport(
        config_version=config.config_version,
        gate_status=gate_status,
        recommended_next_step=NEXT_STEP_BY_STATUS[gate_status],
        rule_clarity_score=metrics.rule_clarity_score,
        official_source_count=metrics.official_source_count,
        dispute_history_score=metrics.dispute_history_score,
        time_to_resolution_hours=metrics.time_to_resolution_hours,
        resolution_dependency_count=metrics.resolution_dependency_count,
        reason_codes=reason_codes,
        reason_code_counts=tuple(
            StrategyResolutionRiskGateReasonCodeCount(reason_code, Decimal("1"))
            for reason_code in reason_codes
        ),
    )


def strategy_resolution_risk_gate_payload(
    report: StrategyResolutionRiskGateReport,
) -> dict[str, Any]:
    if type(report) is not StrategyResolutionRiskGateReport:
        raise ValueError("report must be a StrategyResolutionRiskGateReport")
    return _payload_value(asdict(report))


def _reason_codes_for_metrics(
    metrics: StrategyResolutionRiskGateMetrics,
    config: StrategyResolutionRiskGateConfig,
) -> tuple[str, ...]:
    reason_codes: list[str] = []

    if metrics.rule_clarity_score <= config.block_rule_clarity_score:
        reason_codes.append("ambiguous_resolution_rules")
    elif metrics.rule_clarity_score < config.pass_rule_clarity_score:
        reason_codes.append("weak_rule_clarity")

    if metrics.official_source_count < config.block_official_source_count:
        reason_codes.append("missing_official_sources")
    elif metrics.official_source_count < config.pass_official_source_count:
        reason_codes.append("limited_official_sources")

    if metrics.dispute_history_score >= config.block_dispute_history_score:
        reason_codes.append("severe_dispute_history")
    elif metrics.dispute_history_score > config.pass_dispute_history_score:
        reason_codes.append("elevated_dispute_history")

    if metrics.time_to_resolution_hours <= config.block_time_to_resolution_hours:
        reason_codes.append("imminent_resolution_window")
    elif metrics.time_to_resolution_hours < config.pass_time_to_resolution_hours:
        reason_codes.append("near_resolution_time_pressure")

    if metrics.resolution_dependency_count >= config.block_resolution_dependency_count:
        reason_codes.append("excessive_resolution_dependencies")
    elif metrics.resolution_dependency_count > config.pass_resolution_dependency_count:
        reason_codes.append("resolution_dependency_load")

    if reason_codes:
        return tuple(reason_codes)
    return (PASS_REASON_CODE,)


def _status_from_reason_codes(reason_codes: tuple[str, ...]) -> str:
    if any(reason_code in BLOCKING_REASON_CODES for reason_code in reason_codes):
        return "blocked"
    if any(reason_code in WATCH_REASON_CODES for reason_code in reason_codes):
        return "watch"
    return "pass"


def _normalize_reason_code_counts(
    values: tuple[StrategyResolutionRiskGateReasonCodeCount, ...],
) -> tuple[StrategyResolutionRiskGateReasonCodeCount, ...]:
    if type(values) is not tuple:
        raise ValueError("reason_code_counts must be a tuple")
    for value in values:
        if type(value) is not StrategyResolutionRiskGateReasonCodeCount:
            raise ValueError("reason_code_counts must contain reason rows")
        _require_hard_flags(value)
    if len({value.reason_code for value in values}) != len(values):
        raise ValueError("reason_code_counts must not contain duplicate reason codes")
    return values


def _normalize_reason_codes(field_name: str, values: tuple[str, ...]) -> tuple[str, ...]:
    if type(values) is not tuple:
        raise ValueError(f"{field_name} must be a tuple")
    if not values:
        raise ValueError(f"{field_name} must contain at least one reason code")
    if len(set(values)) != len(values):
        raise ValueError(f"{field_name} must not contain duplicates")
    for value in values:
        _require_reason_code(field_name, value)
    return values


def _normalize_ratio(field_name: str, value: Decimal) -> Decimal:
    value = _normalize_nonnegative_decimal(field_name, value)
    if value > ONE:
        raise ValueError(f"{field_name} must be at most 1")
    return value


def _normalize_nonnegative_decimal(field_name: str, value: Decimal) -> Decimal:
    value = _normalize_decimal(field_name, value)
    if value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return value


def _normalize_positive_decimal(field_name: str, value: Decimal) -> Decimal:
    value = _normalize_nonnegative_decimal(field_name, value)
    if value <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return value


def _normalize_nonnegative_whole_decimal(field_name: str, value: Decimal) -> Decimal:
    value = _normalize_nonnegative_decimal(field_name, value)
    if value != value.to_integral_value():
        raise ValueError(f"{field_name} must be a whole Decimal")
    return value.quantize(COUNT_QUANTUM)


def _normalize_positive_whole_decimal(field_name: str, value: Decimal) -> Decimal:
    value = _normalize_nonnegative_whole_decimal(field_name, value)
    if value <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return value


def _normalize_decimal(field_name: str, value: Decimal) -> Decimal:
    _require_decimal(field_name, value)
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(QUANTUM)


def _require_decimal(field_name: str, value: Decimal) -> None:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")


def _require_canonical_string(field_name: str, value: str) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")


def _require_gate_status(field_name: str, value: str) -> None:
    _require_canonical_string(field_name, value)
    if value not in NEXT_STEP_BY_STATUS:
        raise ValueError(f"{field_name} must be a known status")


def _require_reason_code(field_name: str, value: str) -> None:
    _require_canonical_string(field_name, value)
    if value not in REASON_CODES:
        raise ValueError(f"{field_name} must contain known reason codes")


def _require_hard_flags(value: object) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if getattr(value, field_name) is not True:
            raise ValueError(f"{field_name} must be True")


def _payload_value(value: Any, *, field_name: str | None = None) -> Any:
    if isinstance(value, Decimal):
        if field_name is not None and field_name.endswith("count"):
            return str(value.quantize(COUNT_QUANTUM))
        return str(value)
    if isinstance(value, tuple):
        return [_payload_value(item) for item in value]
    if isinstance(value, list):
        return [_payload_value(item) for item in value]
    if isinstance(value, dict):
        return {
            str(key): _payload_value(item, field_name=str(key))
            for key, item in value.items()
        }
    return value


__all__ = (
    "DEFAULT_STRATEGY_RESOLUTION_RISK_GATE_CONFIG_VERSION",
    "StrategyResolutionRiskGateConfig",
    "StrategyResolutionRiskGateMetrics",
    "StrategyResolutionRiskGateReasonCodeCount",
    "StrategyResolutionRiskGateReport",
    "build_strategy_resolution_risk_gate_report",
    "strategy_resolution_risk_gate_payload",
)
