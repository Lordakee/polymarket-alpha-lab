"""Pure paper/report/readonly resolution rule risk gate for research triage."""

from __future__ import annotations

from dataclasses import asdict, dataclass, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, InvalidOperation, localcontext
from hashlib import sha256
import json
from typing import Any


__all__ = (
    "DEFAULT_RESEARCH_RESOLUTION_RULE_RISK_GATE_CONFIG_VERSION",
    "ResearchResolutionRuleRiskGateConfig",
    "ResearchResolutionRuleRiskGateInput",
    "ResearchResolutionRuleRiskGateResult",
    "ResearchResolutionRuleRiskGateReport",
    "build_research_resolution_rule_risk_gate",
    "validate_research_resolution_rule_risk_gate_report",
    "validate_research_resolution_rule_risk_gate_public_payload",
    "research_resolution_rule_risk_gate_payload",
)


DEFAULT_RESEARCH_RESOLUTION_RULE_RISK_GATE_CONFIG_VERSION = (
    "research-resolution-rule-risk-gate-v1"
)

QUANTUM = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
DECIMAL_CONTEXT = Context(prec=64)

STATUSES = ("pass", "watch", "block")
HUMAN_RESEARCH_PRIORITIES = ("routine", "elevated", "urgent")
SAFETY_FLAG_NAMES = ("paper_only", "report_only", "readonly")

RESULT_REASON_CODES = (
    "resolution_rule_risk_pass",
    "resolution_rule_risk_watch",
    "resolution_rule_risk_block",
    "rule_completeness_watch",
    "rule_completeness_block",
    "resolution_path_ambiguity_watch",
    "resolution_path_ambiguity_block",
    "dispute_risk_watch",
    "dispute_risk_block",
    "resolution_timing_pressure_watch",
    "resolution_timing_pressure_block",
)
REPORT_REASON_CODES = (
    "no_research_items",
    "resolution_rule_risk_clear",
    "resolution_rule_risk_watch_present",
    "resolution_rule_risk_block_present",
    "rule_completeness_watch_present",
    "rule_completeness_block_present",
    "resolution_path_ambiguity_watch_present",
    "resolution_path_ambiguity_block_present",
    "dispute_risk_watch_present",
    "dispute_risk_block_present",
    "resolution_timing_pressure_watch_present",
    "resolution_timing_pressure_block_present",
)

UNSAFE_PUBLIC_KEY_FRAGMENTS = (
    "raw_candidate",
    "candidate_id",
    "market_id",
    "market_slug",
    "market_question",
    "question",
    "source_ref",
    "source_url",
    "source_text",
    "dsn",
    "table",
    "token",
    "wallet",
    "auth",
    "order",
    "trade",
    "position",
    "buy",
    "sell",
    "recommendation",
)
UNSAFE_PUBLIC_VALUE_TERMS = (
    "raw",
    "raw_candidate",
    "candidate_id",
    "market",
    "market_id",
    "market_slug",
    "question",
    "source",
    "source_ref",
    "source_url",
    "source_text",
    "http",
    "dsn",
    "postgres",
    "table",
    "token",
    "wallet",
    "auth",
    "order",
    "trade",
    "position",
    "buy",
    "sell",
    "recommendation",
)


@dataclass(frozen=True)
class ResearchResolutionRuleRiskGateConfig:
    config_version: str = DEFAULT_RESEARCH_RESOLUTION_RULE_RISK_GATE_CONFIG_VERSION
    max_pass_risk_score: Decimal = Decimal("0.250000")
    max_watch_risk_score: Decimal = Decimal("0.550000")
    min_pass_rule_completeness_score: Decimal = Decimal("0.900000")
    min_watch_rule_completeness_score: Decimal = Decimal("0.650000")
    max_pass_resolution_path_ambiguity_score: Decimal = Decimal("0.250000")
    max_watch_resolution_path_ambiguity_score: Decimal = Decimal("0.550000")
    max_pass_dispute_risk_score: Decimal = Decimal("0.250000")
    max_watch_dispute_risk_score: Decimal = Decimal("0.550000")
    max_pass_resolution_timing_pressure_score: Decimal = Decimal("0.250000")
    max_watch_resolution_timing_pressure_score: Decimal = Decimal("0.550000")
    rule_incompleteness_weight: Decimal = Decimal("0.350000")
    resolution_path_ambiguity_weight: Decimal = Decimal("0.250000")
    dispute_risk_weight: Decimal = Decimal("0.250000")
    resolution_timing_pressure_weight: Decimal = Decimal("0.150000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not ResearchResolutionRuleRiskGateConfig:
            raise ValueError("config must be a ResearchResolutionRuleRiskGateConfig")
        _require_canonical_string("config_version", self.config_version)
        for field_name in (
            "max_pass_risk_score",
            "max_watch_risk_score",
            "min_pass_rule_completeness_score",
            "min_watch_rule_completeness_score",
            "max_pass_resolution_path_ambiguity_score",
            "max_watch_resolution_path_ambiguity_score",
            "max_pass_dispute_risk_score",
            "max_watch_dispute_risk_score",
            "max_pass_resolution_timing_pressure_score",
            "max_watch_resolution_timing_pressure_score",
            "rule_incompleteness_weight",
            "resolution_path_ambiguity_weight",
            "dispute_risk_weight",
            "resolution_timing_pressure_weight",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability_decimal(field_name, getattr(self, field_name)),
            )
        if self.max_pass_risk_score > self.max_watch_risk_score:
            raise ValueError("max_pass_risk_score must not exceed max_watch_risk_score")
        if self.min_pass_rule_completeness_score < self.min_watch_rule_completeness_score:
            raise ValueError(
                "min_pass_rule_completeness_score must be at least watch threshold",
            )
        if (
            self.max_pass_resolution_path_ambiguity_score
            > self.max_watch_resolution_path_ambiguity_score
        ):
            raise ValueError(
                "max_pass_resolution_path_ambiguity_score must not exceed watch threshold",
            )
        if self.max_pass_dispute_risk_score > self.max_watch_dispute_risk_score:
            raise ValueError("max_pass_dispute_risk_score must not exceed watch threshold")
        if (
            self.max_pass_resolution_timing_pressure_score
            > self.max_watch_resolution_timing_pressure_score
        ):
            raise ValueError(
                "max_pass_resolution_timing_pressure_score must not exceed watch threshold",
            )
        if _weight_sum(self) != ONE:
            raise ValueError("weights must sum to 1.000000")
        _require_hard_flags("config", self)
        _reject_unsafe_public_payload("config", self)


@dataclass(frozen=True)
class ResearchResolutionRuleRiskGateInput:
    research_item_reference: str
    rule_completeness_score: Decimal
    resolution_path_ambiguity_score: Decimal
    dispute_risk_score: Decimal
    resolution_timing_pressure_score: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not ResearchResolutionRuleRiskGateInput:
            raise ValueError("input must be a ResearchResolutionRuleRiskGateInput")
        _require_safe_public_string("research_item_reference", self.research_item_reference)
        for field_name in (
            "rule_completeness_score",
            "resolution_path_ambiguity_score",
            "dispute_risk_score",
            "resolution_timing_pressure_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability_decimal(field_name, getattr(self, field_name)),
            )
        _require_hard_flags("input", self)
        _reject_unsafe_public_payload("input", self)


@dataclass(frozen=True)
class ResearchResolutionRuleRiskGateResult:
    research_item_reference: str
    rule_completeness_score: Decimal
    rule_incompleteness_pressure: Decimal
    resolution_path_ambiguity_score: Decimal
    dispute_risk_score: Decimal
    resolution_timing_pressure_score: Decimal
    resolution_rule_risk_score: Decimal
    status: str
    human_research_priority: str
    reason_codes: tuple[str, ...]
    result_sha256: str = ""
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not ResearchResolutionRuleRiskGateResult:
            raise ValueError("result must be a ResearchResolutionRuleRiskGateResult")
        _require_safe_public_string("research_item_reference", self.research_item_reference)
        for field_name in (
            "rule_completeness_score",
            "rule_incompleteness_pressure",
            "resolution_path_ambiguity_score",
            "dispute_risk_score",
            "resolution_timing_pressure_score",
            "resolution_rule_risk_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability_decimal(field_name, getattr(self, field_name)),
            )
        _require_member("status", self.status, STATUSES)
        _require_member(
            "human_research_priority",
            self.human_research_priority,
            HUMAN_RESEARCH_PRIORITIES,
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, RESULT_REASON_CODES),
        )
        _require_hard_flags("result", self)
        _reject_unsafe_public_payload("result", self)
        _set_or_validate_digest(self, "result_sha256")
        _set_or_validate_digest(self, "derived_validation_digest")
        _validate_result(self)


@dataclass(frozen=True)
class ResearchResolutionRuleRiskGateReport:
    generated_at: datetime
    config_version: str
    item_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    max_resolution_rule_risk_score: Decimal
    average_resolution_rule_risk_score: Decimal
    status: str
    human_research_priority: str
    reason_codes: tuple[str, ...]
    results: tuple[ResearchResolutionRuleRiskGateResult, ...]
    report_sha256: str = ""
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not ResearchResolutionRuleRiskGateReport:
            raise ValueError("report must be a ResearchResolutionRuleRiskGateReport")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        for field_name in ("item_count", "pass_count", "watch_count", "block_count"):
            object.__setattr__(
                self,
                field_name,
                _normalize_count_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "max_resolution_rule_risk_score",
            "average_resolution_rule_risk_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability_decimal(field_name, getattr(self, field_name)),
            )
        _require_member("status", self.status, STATUSES)
        _require_member(
            "human_research_priority",
            self.human_research_priority,
            HUMAN_RESEARCH_PRIORITIES,
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, REPORT_REASON_CODES),
        )
        object.__setattr__(self, "results", _normalize_results(self.results))
        _require_hard_flags("report", self)
        _reject_unsafe_public_payload("report", self)
        _set_or_validate_digest(self, "report_sha256")
        _set_or_validate_digest(self, "derived_validation_digest")
        _validate_report(self)


def build_research_resolution_rule_risk_gate(
    inputs: object,
    *,
    config: ResearchResolutionRuleRiskGateConfig,
    generated_at: datetime,
) -> ResearchResolutionRuleRiskGateReport:
    if type(config) is not ResearchResolutionRuleRiskGateConfig:
        raise ValueError("config must be a ResearchResolutionRuleRiskGateConfig")
    _require_hard_flags("config", config)
    checked_inputs = _normalize_inputs(inputs)
    generated_at_utc = _as_utc("generated_at", generated_at)
    results = tuple(_result_for_input(row, config) for row in checked_inputs)
    sorted_results = tuple(
        sorted(
            results,
            key=lambda row: (-row.resolution_rule_risk_score, row.research_item_reference),
        ),
    )
    return ResearchResolutionRuleRiskGateReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        item_count=_count_decimal(len(sorted_results)),
        pass_count=_count_decimal(sum(row.status == "pass" for row in sorted_results)),
        watch_count=_count_decimal(sum(row.status == "watch" for row in sorted_results)),
        block_count=_count_decimal(sum(row.status == "block" for row in sorted_results)),
        max_resolution_rule_risk_score=_max_risk_score(sorted_results),
        average_resolution_rule_risk_score=_average_risk_score(sorted_results),
        status=_report_status(sorted_results),
        human_research_priority=_priority_for_status(_report_status(sorted_results)),
        reason_codes=_report_reason_codes(sorted_results),
        results=sorted_results,
    )


def validate_research_resolution_rule_risk_gate_report(
    report: ResearchResolutionRuleRiskGateReport,
) -> bool:
    if type(report) is not ResearchResolutionRuleRiskGateReport:
        raise ValueError("report must be a ResearchResolutionRuleRiskGateReport")
    _require_hard_flags("report", report)
    _reject_unsafe_public_payload("report", report)
    _validate_report(report)
    _require_digest(report, "report_sha256")
    _require_digest(report, "derived_validation_digest")
    return True


def validate_research_resolution_rule_risk_gate_public_payload(
    payload: dict[str, Any],
) -> bool:
    if type(payload) is not dict:
        raise ValueError("payload must be a dict")
    _require_public_payload_flags(payload)
    _reject_unsafe_public_payload("payload", payload)
    return True


def research_resolution_rule_risk_gate_payload(
    report: ResearchResolutionRuleRiskGateReport,
) -> dict[str, Any]:
    validate_research_resolution_rule_risk_gate_report(report)
    payload = _json_ready(asdict(report))
    if type(payload) is not dict:
        raise ValueError("payload must be a dict")
    validate_research_resolution_rule_risk_gate_public_payload(payload)
    return payload


def _normalize_inputs(inputs: object) -> tuple[ResearchResolutionRuleRiskGateInput, ...]:
    if type(inputs) not in (list, tuple):
        raise ValueError("inputs must be a list or tuple")
    checked = tuple(inputs)
    seen: set[str] = set()
    for row in checked:
        if type(row) is not ResearchResolutionRuleRiskGateInput:
            raise ValueError("inputs items must be ResearchResolutionRuleRiskGateInput")
        _require_hard_flags("input", row)
        _reject_unsafe_public_payload("input", row)
        if row.research_item_reference in seen:
            raise ValueError("duplicate research_item_reference")
        seen.add(row.research_item_reference)
    return checked


def _result_for_input(
    row: ResearchResolutionRuleRiskGateInput,
    config: ResearchResolutionRuleRiskGateConfig,
) -> ResearchResolutionRuleRiskGateResult:
    rule_incompleteness_pressure = _q(ONE - row.rule_completeness_score)
    risk_score = _q(
        (rule_incompleteness_pressure * config.rule_incompleteness_weight)
        + (
            row.resolution_path_ambiguity_score
            * config.resolution_path_ambiguity_weight
        )
        + (row.dispute_risk_score * config.dispute_risk_weight)
        + (
            row.resolution_timing_pressure_score
            * config.resolution_timing_pressure_weight
        ),
    )
    status = _result_status(row=row, risk_score=risk_score, config=config)
    return ResearchResolutionRuleRiskGateResult(
        research_item_reference=row.research_item_reference,
        rule_completeness_score=row.rule_completeness_score,
        rule_incompleteness_pressure=rule_incompleteness_pressure,
        resolution_path_ambiguity_score=row.resolution_path_ambiguity_score,
        dispute_risk_score=row.dispute_risk_score,
        resolution_timing_pressure_score=row.resolution_timing_pressure_score,
        resolution_rule_risk_score=risk_score,
        status=status,
        human_research_priority=_priority_for_status(status),
        reason_codes=_result_reason_codes(row=row, risk_score=risk_score, status=status, config=config),
    )


def _result_status(
    *,
    row: ResearchResolutionRuleRiskGateInput,
    risk_score: Decimal,
    config: ResearchResolutionRuleRiskGateConfig,
) -> str:
    if (
        row.rule_completeness_score < config.min_watch_rule_completeness_score
        or row.resolution_path_ambiguity_score
        > config.max_watch_resolution_path_ambiguity_score
        or row.dispute_risk_score > config.max_watch_dispute_risk_score
        or row.resolution_timing_pressure_score
        > config.max_watch_resolution_timing_pressure_score
        or risk_score > config.max_watch_risk_score
    ):
        return "block"
    if (
        row.rule_completeness_score < config.min_pass_rule_completeness_score
        or row.resolution_path_ambiguity_score
        > config.max_pass_resolution_path_ambiguity_score
        or row.dispute_risk_score > config.max_pass_dispute_risk_score
        or row.resolution_timing_pressure_score
        > config.max_pass_resolution_timing_pressure_score
        or risk_score > config.max_pass_risk_score
    ):
        return "watch"
    return "pass"


def _result_reason_codes(
    *,
    row: ResearchResolutionRuleRiskGateInput,
    risk_score: Decimal,
    status: str,
    config: ResearchResolutionRuleRiskGateConfig,
) -> tuple[str, ...]:
    reason_codes: list[str] = [f"resolution_rule_risk_{status}"]
    if status == "pass":
        return tuple(reason_codes)
    rule_reason = _component_reason(
        below_value=row.rule_completeness_score,
        pass_threshold=config.min_pass_rule_completeness_score,
        watch_threshold=config.min_watch_rule_completeness_score,
        watch_code="rule_completeness_watch",
        block_code="rule_completeness_block",
    )
    if rule_reason is not None:
        reason_codes.append(rule_reason)
    for value, pass_threshold, watch_threshold, watch_code, block_code in (
        (
            row.resolution_path_ambiguity_score,
            config.max_pass_resolution_path_ambiguity_score,
            config.max_watch_resolution_path_ambiguity_score,
            "resolution_path_ambiguity_watch",
            "resolution_path_ambiguity_block",
        ),
        (
            row.dispute_risk_score,
            config.max_pass_dispute_risk_score,
            config.max_watch_dispute_risk_score,
            "dispute_risk_watch",
            "dispute_risk_block",
        ),
        (
            row.resolution_timing_pressure_score,
            config.max_pass_resolution_timing_pressure_score,
            config.max_watch_resolution_timing_pressure_score,
            "resolution_timing_pressure_watch",
            "resolution_timing_pressure_block",
        ),
    ):
        reason = _upper_component_reason(
            value=value,
            pass_threshold=pass_threshold,
            watch_threshold=watch_threshold,
            watch_code=watch_code,
            block_code=block_code,
        )
        if reason is not None:
            reason_codes.append(reason)
    if len(reason_codes) == 1 and risk_score > config.max_pass_risk_score:
        return tuple(reason_codes)
    return tuple(reason_codes)


def _component_reason(
    *,
    below_value: Decimal,
    pass_threshold: Decimal,
    watch_threshold: Decimal,
    watch_code: str,
    block_code: str,
) -> str | None:
    if below_value < watch_threshold:
        return block_code
    if below_value < pass_threshold:
        return watch_code
    return None


def _upper_component_reason(
    *,
    value: Decimal,
    pass_threshold: Decimal,
    watch_threshold: Decimal,
    watch_code: str,
    block_code: str,
) -> str | None:
    if value > watch_threshold:
        return block_code
    if value > pass_threshold:
        return watch_code
    return None


def _report_reason_codes(
    results: tuple[ResearchResolutionRuleRiskGateResult, ...],
) -> tuple[str, ...]:
    if not results:
        return ("no_research_items",)
    reason_codes: list[str] = []
    if any(row.status == "block" for row in results):
        reason_codes.append("resolution_rule_risk_block_present")
    if any(row.status == "watch" for row in results):
        reason_codes.append("resolution_rule_risk_watch_present")
    for block_code, watch_code in (
        ("rule_completeness_block", "rule_completeness_watch"),
        ("resolution_path_ambiguity_block", "resolution_path_ambiguity_watch"),
        ("dispute_risk_block", "dispute_risk_watch"),
        ("resolution_timing_pressure_block", "resolution_timing_pressure_watch"),
    ):
        if any(block_code in row.reason_codes for row in results):
            reason_codes.append(f"{block_code}_present")
        elif any(watch_code in row.reason_codes for row in results):
            reason_codes.append(f"{watch_code}_present")
    if not reason_codes:
        reason_codes.append("resolution_rule_risk_clear")
    return tuple(reason_codes)


def _report_status(results: tuple[ResearchResolutionRuleRiskGateResult, ...]) -> str:
    if any(row.status == "block" for row in results):
        return "block"
    if any(row.status == "watch" for row in results):
        return "watch"
    return "pass"


def _priority_for_status(status: str) -> str:
    if status == "block":
        return "urgent"
    if status == "watch":
        return "elevated"
    if status == "pass":
        return "routine"
    raise ValueError("status must be supported")


def _normalize_results(
    results: object,
) -> tuple[ResearchResolutionRuleRiskGateResult, ...]:
    if type(results) is not tuple:
        raise ValueError("results must be a tuple")
    checked = tuple(results)
    expected = tuple(
        sorted(
            checked,
            key=lambda row: (-row.resolution_rule_risk_score, row.research_item_reference),
        ),
    )
    if checked != expected:
        raise ValueError("results must be sorted by risk severity")
    seen: set[str] = set()
    for row in checked:
        if type(row) is not ResearchResolutionRuleRiskGateResult:
            raise ValueError("results must contain ResearchResolutionRuleRiskGateResult")
        _require_hard_flags("result", row)
        if row.research_item_reference in seen:
            raise ValueError("duplicate research_item_reference")
        seen.add(row.research_item_reference)
    return checked


def _validate_result(row: ResearchResolutionRuleRiskGateResult) -> None:
    if row.rule_incompleteness_pressure != _q(ONE - row.rule_completeness_score):
        raise ValueError("rule_incompleteness_pressure must match rule_completeness_score")
    if row.human_research_priority != _priority_for_status(row.status):
        raise ValueError("human_research_priority must match status")
    if row.reason_codes[0] != f"resolution_rule_risk_{row.status}":
        raise ValueError("reason_codes must include result status")
    _require_digest(row, "result_sha256")
    _require_digest(row, "derived_validation_digest")


def _validate_report(report: ResearchResolutionRuleRiskGateReport) -> None:
    results = report.results
    if report.item_count != _count_decimal(len(results)):
        raise ValueError("item_count must match results")
    if report.pass_count != _count_decimal(sum(row.status == "pass" for row in results)):
        raise ValueError("pass_count must match results")
    if report.watch_count != _count_decimal(sum(row.status == "watch" for row in results)):
        raise ValueError("watch_count must match results")
    if report.block_count != _count_decimal(sum(row.status == "block" for row in results)):
        raise ValueError("block_count must match results")
    if report.max_resolution_rule_risk_score != _max_risk_score(results):
        raise ValueError("max_resolution_rule_risk_score must match results")
    if report.average_resolution_rule_risk_score != _average_risk_score(results):
        raise ValueError("average_resolution_rule_risk_score must match results")
    if report.status != _report_status(results):
        raise ValueError("status must match results")
    if report.human_research_priority != _priority_for_status(report.status):
        raise ValueError("human_research_priority must match status")
    if report.reason_codes != _report_reason_codes(results):
        raise ValueError("reason_codes must match results")


def _max_risk_score(results: tuple[ResearchResolutionRuleRiskGateResult, ...]) -> Decimal:
    if not results:
        return ZERO
    return max(row.resolution_rule_risk_score for row in results)


def _average_risk_score(results: tuple[ResearchResolutionRuleRiskGateResult, ...]) -> Decimal:
    if not results:
        return ZERO
    total = sum((row.resolution_rule_risk_score for row in results), ZERO)
    with localcontext(DECIMAL_CONTEXT):
        return (total / _count_decimal(len(results))).quantize(QUANTUM)


def _weight_sum(config: ResearchResolutionRuleRiskGateConfig) -> Decimal:
    return _q(
        config.rule_incompleteness_weight
        + config.resolution_path_ambiguity_weight
        + config.dispute_risk_weight
        + config.resolution_timing_pressure_weight,
    )


def _normalize_reason_codes(
    field_name: str,
    value: object,
    allowed: tuple[str, ...],
) -> tuple[str, ...]:
    if type(value) not in (list, tuple):
        raise ValueError(f"{field_name} must be a list or tuple")
    reason_codes = tuple(value)
    if not reason_codes:
        raise ValueError(f"{field_name} must not be empty")
    if len(set(reason_codes)) != len(reason_codes):
        raise ValueError(f"{field_name} must be unique")
    for reason_code in reason_codes:
        _require_member(field_name, reason_code, allowed)
        _reject_unsafe_public_string(field_name, reason_code)
    return reason_codes


def _require_member(field_name: str, value: object, allowed: tuple[str, ...]) -> None:
    _require_canonical_string(field_name, value)
    if value not in allowed:
        raise ValueError(f"{field_name} must be one of {allowed!r}")


def _require_safe_public_string(field_name: str, value: object) -> None:
    _require_canonical_string(field_name, value)
    _reject_unsafe_public_string(field_name, value)
    if any(character.isspace() for character in value):
        raise ValueError(f"{field_name} must not contain whitespace")


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str or not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a non-empty canonical string")


def _normalize_probability_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized < ZERO or normalized > ONE:
        raise ValueError(f"{field_name} must be between 0.000000 and 1.000000")
    return normalized


def _normalize_count_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{field_name} must be whole")
    return _q(normalized)


def _normalize_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    with localcontext(DECIMAL_CONTEXT):
        try:
            return (+value).quantize(QUANTUM)
        except InvalidOperation as exc:
            raise ValueError(f"{field_name} must be usable") from exc


def _q(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(QUANTUM)


def _count_decimal(value: int) -> Decimal:
    return _q(Decimal(value))


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_hard_flags(label: str, value: object) -> None:
    if getattr(value, "paper_only", None) is not True:
        raise ValueError(f"{label} paper_only must be True")
    if getattr(value, "report_only", None) is not True:
        raise ValueError(f"{label} report_only must be True")
    if getattr(value, "readonly", None) is not True:
        raise ValueError(f"{label} readonly must be True")


def _require_public_payload_flags(payload: dict[str, Any]) -> None:
    for field_name in SAFETY_FLAG_NAMES:
        if payload.get(field_name) is not True:
            raise ValueError(f"{field_name} must be True")


def _set_or_validate_digest(value: object, field_name: str) -> None:
    supplied = getattr(value, field_name)
    if supplied == "":
        object.__setattr__(value, field_name, _digest_for(value, field_name))
        return
    _require_sha256(field_name, supplied)
    expected = _digest_for(value, field_name)
    if supplied != expected:
        raise ValueError(f"{field_name} mismatch")


def _require_digest(value: object, field_name: str) -> None:
    supplied = getattr(value, field_name)
    _require_sha256(field_name, supplied)
    if supplied != _digest_for(value, field_name):
        raise ValueError(f"{field_name} mismatch")


def _require_sha256(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if len(value) != 64 or value.lower() != value:
        raise ValueError(f"{field_name} must be a lowercase sha256 digest")
    try:
        int(value, 16)
    except ValueError as exc:
        raise ValueError(f"{field_name} must be a lowercase sha256 digest") from exc


def _digest_for(value: object, digest_field_name: str) -> str:
    if not is_dataclass(value) or isinstance(value, type):
        raise ValueError("digest requires a dataclass value")
    payload = asdict(value)
    payload.pop(digest_field_name, None)
    payload.pop("result_sha256", None)
    payload.pop("report_sha256", None)
    payload.pop("derived_validation_digest", None)
    ready = _json_ready(payload)
    encoded = json.dumps(ready, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return sha256(encoded).hexdigest()


def _json_ready(value: object) -> object:
    if isinstance(value, Decimal):
        if type(value) is not Decimal:
            raise ValueError("JSON Decimal value must be exactly Decimal")
        if not value.is_finite():
            raise ValueError("JSON Decimal value must be finite")
        return str(_q(value))
    if isinstance(value, datetime):
        if type(value) is not datetime:
            raise ValueError("JSON datetime value must be a datetime")
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("JSON datetime value must be timezone-aware")
        return value.astimezone(UTC).isoformat()
    if is_dataclass(value) and not isinstance(value, type):
        return _json_ready(asdict(value))
    if type(value) is bool:
        return value
    if type(value) is int:
        raise ValueError("JSON numeric value must use Decimal")
    if isinstance(value, float):
        raise ValueError("JSON value must not be a float")
    if type(value) is str:
        return value
    if value is None:
        return None
    if isinstance(value, tuple):
        return [_json_ready(item) for item in value]
    if isinstance(value, list):
        return [_json_ready(item) for item in value]
    if isinstance(value, dict):
        ready: dict[str, object] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            ready[key] = _json_ready(item)
        return ready
    raise ValueError("value is not JSON serializable")


def _reject_unsafe_public_payload(label: str, value: object, path: str = "") -> None:
    if is_dataclass(value) and not isinstance(value, type):
        _reject_unsafe_public_payload(label, asdict(value), path)
        return
    if type(value) is str:
        _reject_unsafe_public_string(path or label, value)
        return
    if isinstance(value, Decimal):
        if type(value) is not Decimal:
            raise ValueError(f"{path or label} must be exactly Decimal")
        if not value.is_finite():
            raise ValueError(f"{path or label} must be finite")
        return
    if isinstance(value, datetime):
        if type(value) is not datetime:
            raise ValueError(f"{path or label} must be a datetime")
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError(f"{path or label} must be timezone-aware")
        return
    if value is None or type(value) is bool:
        return
    if type(value) is int:
        raise ValueError(f"{path or label} must use Decimal-derived string values")
    if isinstance(value, float):
        raise ValueError("JSON value must not be a float")
    if isinstance(value, dict):
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            nested_path = key if not path else f"{path}.{key}"
            _reject_unsafe_public_key(key)
            if key in SAFETY_FLAG_NAMES and item is not True:
                raise ValueError(f"{nested_path} must be True")
            _reject_unsafe_public_payload(label, item, nested_path)
        return
    if isinstance(value, (list, tuple)):
        for item in value:
            _reject_unsafe_public_payload(label, item, path)
        return
    raise ValueError("value is not JSON serializable")


def _reject_unsafe_public_key(value: str) -> None:
    lowered = value.lower()
    for fragment in UNSAFE_PUBLIC_KEY_FRAGMENTS:
        if fragment in lowered:
            raise ValueError("unsafe public payload key")


def _reject_unsafe_public_string(label: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{label} must be a string")
    lowered = value.lower()
    for fragment in UNSAFE_PUBLIC_VALUE_TERMS:
        if fragment in lowered:
            raise ValueError(f"unsafe public payload value in {label}")
    tokens = _public_tokens(lowered)
    if any(term in tokens for term in UNSAFE_PUBLIC_VALUE_TERMS):
        raise ValueError(f"unsafe public payload value in {label}")


def _public_tokens(value: str) -> tuple[str, ...]:
    tokens: list[str] = []
    current: list[str] = []
    for character in value:
        if ("a" <= character <= "z") or ("0" <= character <= "9"):
            current.append(character)
            continue
        if current:
            tokens.append("".join(current))
            current = []
    if current:
        tokens.append("".join(current))
    return tuple(tokens)
