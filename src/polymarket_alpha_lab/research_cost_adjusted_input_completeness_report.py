"""Pure cost-adjusted input completeness report for manual research review.

Callers provide abstract Decimal inputs for cost friction, liquidity quality,
evidence freshness, and rule clarity. The module returns a deterministic,
readonly report and never computes exposure sizing, direction, or action advice.
"""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable
from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, InvalidOperation, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
import json
from typing import Any


__all__ = (
    "DEFAULT_RESEARCH_COST_ADJUSTED_INPUT_COMPLETENESS_CONFIG_VERSION",
    "CostAdjustedInputCompletenessConfig",
    "CostAdjustedInputCompletenessInput",
    "CostAdjustedInputCompletenessReasonCodeCount",
    "CostAdjustedInputCompletenessReport",
    "CostAdjustedInputCompletenessRow",
    "build_research_cost_adjusted_input_completeness_report",
    "research_cost_adjusted_input_completeness_report_payload",
)


DEFAULT_RESEARCH_COST_ADJUSTED_INPUT_COMPLETENESS_CONFIG_VERSION = (
    "research-cost-adjusted-input-completeness-report-v0"
)

QUANTUM = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
PASS_COST_COMPLETENESS_SCORE = Decimal("0.900000")
WATCH_COST_COMPLETENESS_SCORE = Decimal("0.650000")
BLOCK_COST_COMPLETENESS_SCORE = Decimal("0.350000")
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
STATUSES = ("pass", "watch", "block")
STATUS_SORT_WEIGHT = {"block": 0, "watch": 1, "pass": 2}
PHASE_FLAG_FIELDS = ("paper_only", "report_only", "readonly")
UNSAFE_TEXT_FRAGMENTS = (
    "auth",
    "buy",
    "identifier",
    "key",
    "live",
    "market",
    "order",
    "position",
    "private",
    "recommend",
    "sell",
    "source",
    "trade",
    "wallet",
)
HEX_CHARS = frozenset("0123456789abcdef")
REPORT_REASON_PRIORITY = (
    "cost_adjusted_total_cost_block",
    "cost_adjusted_spread_block",
    "cost_adjusted_liquidity_block",
    "cost_adjusted_evidence_freshness_block",
    "cost_adjusted_rule_clarity_block",
    "cost_adjusted_completeness_block",
    "cost_adjusted_total_cost_watch",
    "cost_adjusted_spread_watch",
    "cost_adjusted_liquidity_watch",
    "cost_adjusted_evidence_freshness_watch",
    "cost_adjusted_rule_clarity_watch",
    "cost_adjusted_completeness_watch",
)
SUMMARY_EXPLANATION_BY_STATUS = {
    "pass": "pass: cost-adjusted inputs are complete enough for manual or paper review",
    "watch": "watch: cost-adjusted inputs need manual review before paper review",
    "block": "block: cost-adjusted inputs are incomplete for manual or paper review",
}


class _FinalPublicDataclass:
    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        for base in cls.__bases__:
            if base is not _FinalPublicDataclass and issubclass(
                base,
                _FinalPublicDataclass,
            ):
                raise ValueError(f"{base.__name__} subclass is not allowed")


@dataclass(frozen=True)
class CostAdjustedInputCompletenessConfig(_FinalPublicDataclass):
    config_version: str = (
        DEFAULT_RESEARCH_COST_ADJUSTED_INPUT_COMPLETENESS_CONFIG_VERSION
    )
    pass_min_completeness_score: Decimal = Decimal("0.850000")
    watch_min_completeness_score: Decimal = Decimal("0.650000")
    max_pass_total_cost_rate: Decimal = Decimal("0.030000")
    max_watch_total_cost_rate: Decimal = Decimal("0.060000")
    max_pass_spread_rate: Decimal = Decimal("0.020000")
    max_watch_spread_rate: Decimal = Decimal("0.040000")
    min_pass_liquidity_quality: Decimal = Decimal("0.700000")
    min_watch_liquidity_quality: Decimal = Decimal("0.400000")
    min_pass_evidence_freshness: Decimal = Decimal("0.750000")
    min_watch_evidence_freshness: Decimal = Decimal("0.500000")
    min_pass_rule_clarity: Decimal = Decimal("0.800000")
    min_watch_rule_clarity: Decimal = Decimal("0.550000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, CostAdjustedInputCompletenessConfig, "config")
        if (
            self.config_version
            != DEFAULT_RESEARCH_COST_ADJUSTED_INPUT_COMPLETENESS_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "pass_min_completeness_score",
            "watch_min_completeness_score",
            "max_pass_total_cost_rate",
            "max_watch_total_cost_rate",
            "max_pass_spread_rate",
            "max_watch_spread_rate",
            "min_pass_liquidity_quality",
            "min_watch_liquidity_quality",
            "min_pass_evidence_freshness",
            "min_watch_evidence_freshness",
            "min_pass_rule_clarity",
            "min_watch_rule_clarity",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        if self.pass_min_completeness_score < self.watch_min_completeness_score:
            raise ValueError(
                "pass_min_completeness_score must be at least "
                "watch_min_completeness_score",
            )
        if self.max_watch_total_cost_rate < self.max_pass_total_cost_rate:
            raise ValueError(
                "max_watch_total_cost_rate must be at least max_pass_total_cost_rate",
            )
        if self.max_watch_spread_rate < self.max_pass_spread_rate:
            raise ValueError(
                "max_watch_spread_rate must be at least max_pass_spread_rate",
            )
        if self.min_pass_liquidity_quality < self.min_watch_liquidity_quality:
            raise ValueError(
                "min_pass_liquidity_quality must be at least "
                "min_watch_liquidity_quality",
            )
        if self.min_pass_evidence_freshness < self.min_watch_evidence_freshness:
            raise ValueError(
                "min_pass_evidence_freshness must be at least "
                "min_watch_evidence_freshness",
            )
        if self.min_pass_rule_clarity < self.min_watch_rule_clarity:
            raise ValueError(
                "min_pass_rule_clarity must be at least min_watch_rule_clarity",
            )
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class CostAdjustedInputCompletenessInput(_FinalPublicDataclass):
    spread_rate: Decimal
    taker_fee_rate: Decimal
    deposit_friction_rate: Decimal
    settlement_friction_rate: Decimal
    gas_friction_rate: Decimal
    liquidity_quality: Decimal
    evidence_freshness: Decimal
    rule_clarity: Decimal
    observed_at: datetime
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, CostAdjustedInputCompletenessInput, "input")
        for field_name in (
            "spread_rate",
            "taker_fee_rate",
            "deposit_friction_rate",
            "settlement_friction_rate",
            "gas_friction_rate",
            "liquidity_quality",
            "evidence_freshness",
            "rule_clarity",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_sorted_reason_codes("reason_codes", self.reason_codes),
        )
        _require_hard_flags("input", self)


@dataclass(frozen=True)
class CostAdjustedInputCompletenessRow(_FinalPublicDataclass):
    row_index: Decimal
    spread_rate: Decimal
    taker_fee_rate: Decimal
    deposit_friction_rate: Decimal
    settlement_friction_rate: Decimal
    gas_friction_rate: Decimal
    total_cost_rate: Decimal
    liquidity_quality: Decimal
    evidence_freshness: Decimal
    rule_clarity: Decimal
    completeness_score: Decimal
    observed_at: datetime
    status: str
    status_explanation: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, CostAdjustedInputCompletenessRow, "row")
        object.__setattr__(
            self,
            "row_index",
            _require_positive_decimal("row_index", self.row_index),
        )
        for field_name in (
            "spread_rate",
            "taker_fee_rate",
            "deposit_friction_rate",
            "settlement_friction_rate",
            "gas_friction_rate",
            "total_cost_rate",
            "liquidity_quality",
            "evidence_freshness",
            "rule_clarity",
            "completeness_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        _require_status("status", self.status)
        _require_safe_public_text("status_explanation", self.status_explanation)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        _validate_row_consistency(self)
        _require_hard_flags("row", self)


@dataclass(frozen=True)
class CostAdjustedInputCompletenessReasonCodeCount(_FinalPublicDataclass):
    reason_code: str
    count: Decimal
    input_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, CostAdjustedInputCompletenessReasonCodeCount, "count")
        _require_reason_code("reason_code", self.reason_code)
        object.__setattr__(
            self,
            "count",
            _require_nonnegative_decimal("count", self.count),
        )
        object.__setattr__(
            self,
            "input_ratio",
            _require_ratio_decimal("input_ratio", self.input_ratio),
        )
        _require_hard_flags("reason_code_count", self)


@dataclass(frozen=True)
class CostAdjustedInputCompletenessReport(_FinalPublicDataclass):
    generated_at: datetime
    config_version: str
    input_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    max_total_cost_rate: Decimal
    min_completeness_score: Decimal
    status: str
    summary_explanation: str
    reason_codes: tuple[str, ...]
    reason_code_counts: tuple[CostAdjustedInputCompletenessReasonCodeCount, ...]
    rows: tuple[CostAdjustedInputCompletenessRow, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, CostAdjustedInputCompletenessReport, "report")
        object.__setattr__(
            self,
            "generated_at",
            _as_utc("generated_at", self.generated_at),
        )
        if (
            self.config_version
            != DEFAULT_RESEARCH_COST_ADJUSTED_INPUT_COMPLETENESS_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "input_count",
            "pass_count",
            "watch_count",
            "block_count",
            "max_total_cost_rate",
            "min_completeness_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        _require_status("status", self.status)
        _require_safe_public_text("summary_explanation", self.summary_explanation)
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
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        _validate_report_consistency(self)
        _require_hard_flags("report", self)
        if self.derived_validation_digest:
            _require_digest(self.derived_validation_digest)
        else:
            object.__setattr__(
                self,
                "derived_validation_digest",
                _digest_payload(_report_payload_core(self, include_digest=False)),
            )


def build_research_cost_adjusted_input_completeness_report(
    inputs: Iterable[CostAdjustedInputCompletenessInput],
    *,
    config: CostAdjustedInputCompletenessConfig,
    generated_at: datetime,
) -> CostAdjustedInputCompletenessReport:
    if type(config) is not CostAdjustedInputCompletenessConfig:
        raise ValueError("config must be a CostAdjustedInputCompletenessConfig")
    _require_hard_flags("config", config)
    generated_at = _as_utc("generated_at", generated_at)
    normalized_inputs = _normalize_inputs(inputs)
    rows = tuple(
        sorted(
            (
                _row_from_input(value, row_index=index, config=config)
                for index, value in enumerate(normalized_inputs, start=1)
            ),
            key=_row_sort_key,
        ),
    )
    status = _report_status(rows)
    return CostAdjustedInputCompletenessReport(
        generated_at=generated_at,
        config_version=config.config_version,
        input_count=_count_decimal(len(normalized_inputs)),
        pass_count=_status_count(rows, "pass"),
        watch_count=_status_count(rows, "watch"),
        block_count=_status_count(rows, "block"),
        max_total_cost_rate=_max_row_decimal(rows, "total_cost_rate"),
        min_completeness_score=_min_row_decimal(rows, "completeness_score"),
        status=status,
        summary_explanation=_summary_explanation(status, has_rows=bool(rows)),
        reason_codes=_report_reason_codes(rows, status=status),
        reason_code_counts=_reason_code_counts(rows),
        rows=rows,
    )


def research_cost_adjusted_input_completeness_report_payload(
    report: CostAdjustedInputCompletenessReport,
) -> dict[str, Any]:
    if type(report) is not CostAdjustedInputCompletenessReport:
        raise ValueError("report must be a CostAdjustedInputCompletenessReport")
    _require_hard_flags("report", report)
    payload = _report_payload_core(report, include_digest=True)
    _reject_unsafe_payload(payload)
    return payload


def _row_from_input(
    value: CostAdjustedInputCompletenessInput,
    *,
    row_index: int,
    config: CostAdjustedInputCompletenessConfig,
) -> CostAdjustedInputCompletenessRow:
    total_cost_rate = _sum_decimals(
        (
            value.spread_rate,
            value.taker_fee_rate,
            value.deposit_friction_rate,
            value.settlement_friction_rate,
            value.gas_friction_rate,
        ),
    )
    cost_score = _cost_completeness_score(total_cost_rate, config)
    completeness_score = _average_decimals(
        (
            cost_score,
            value.liquidity_quality,
            value.evidence_freshness,
            value.rule_clarity,
        ),
    )
    status = _row_status(
        total_cost_rate=total_cost_rate,
        spread_rate=value.spread_rate,
        liquidity_quality=value.liquidity_quality,
        evidence_freshness=value.evidence_freshness,
        rule_clarity=value.rule_clarity,
        completeness_score=completeness_score,
        config=config,
    )
    return CostAdjustedInputCompletenessRow(
        row_index=_count_decimal(row_index),
        spread_rate=value.spread_rate,
        taker_fee_rate=value.taker_fee_rate,
        deposit_friction_rate=value.deposit_friction_rate,
        settlement_friction_rate=value.settlement_friction_rate,
        gas_friction_rate=value.gas_friction_rate,
        total_cost_rate=total_cost_rate,
        liquidity_quality=value.liquidity_quality,
        evidence_freshness=value.evidence_freshness,
        rule_clarity=value.rule_clarity,
        completeness_score=completeness_score,
        observed_at=value.observed_at,
        status=status,
        status_explanation=SUMMARY_EXPLANATION_BY_STATUS[status],
        reason_codes=_row_reason_codes(
            value.reason_codes,
            total_cost_rate=total_cost_rate,
            spread_rate=value.spread_rate,
            liquidity_quality=value.liquidity_quality,
            evidence_freshness=value.evidence_freshness,
            rule_clarity=value.rule_clarity,
            completeness_score=completeness_score,
            status=status,
            config=config,
        ),
    )


def _row_status(
    *,
    total_cost_rate: Decimal,
    spread_rate: Decimal,
    liquidity_quality: Decimal,
    evidence_freshness: Decimal,
    rule_clarity: Decimal,
    completeness_score: Decimal,
    config: CostAdjustedInputCompletenessConfig,
) -> str:
    if (
        total_cost_rate > config.max_watch_total_cost_rate
        or spread_rate > config.max_watch_spread_rate
        or liquidity_quality < config.min_watch_liquidity_quality
        or evidence_freshness < config.min_watch_evidence_freshness
        or rule_clarity < config.min_watch_rule_clarity
    ):
        return "block"
    if (
        total_cost_rate > config.max_pass_total_cost_rate
        or spread_rate > config.max_pass_spread_rate
        or liquidity_quality < config.min_pass_liquidity_quality
        or evidence_freshness < config.min_pass_evidence_freshness
        or rule_clarity < config.min_pass_rule_clarity
        or completeness_score < config.pass_min_completeness_score
    ):
        return "watch"
    return "pass"


def _row_reason_codes(
    upstream_reason_codes: tuple[str, ...],
    *,
    total_cost_rate: Decimal,
    spread_rate: Decimal,
    liquidity_quality: Decimal,
    evidence_freshness: Decimal,
    rule_clarity: Decimal,
    completeness_score: Decimal,
    status: str,
    config: CostAdjustedInputCompletenessConfig,
) -> tuple[str, ...]:
    reason_codes = list(upstream_reason_codes)
    if total_cost_rate > config.max_watch_total_cost_rate:
        reason_codes.append("cost_adjusted_total_cost_block")
    elif total_cost_rate > config.max_pass_total_cost_rate:
        reason_codes.append("cost_adjusted_total_cost_watch")
    if spread_rate > config.max_watch_spread_rate:
        reason_codes.append("cost_adjusted_spread_block")
    elif spread_rate > config.max_pass_spread_rate:
        reason_codes.append("cost_adjusted_spread_watch")
    if liquidity_quality < config.min_watch_liquidity_quality:
        reason_codes.append("cost_adjusted_liquidity_block")
    elif liquidity_quality < config.min_pass_liquidity_quality:
        reason_codes.append("cost_adjusted_liquidity_watch")
    if evidence_freshness < config.min_watch_evidence_freshness:
        reason_codes.append("cost_adjusted_evidence_freshness_block")
    elif evidence_freshness < config.min_pass_evidence_freshness:
        reason_codes.append("cost_adjusted_evidence_freshness_watch")
    if rule_clarity < config.min_watch_rule_clarity:
        reason_codes.append("cost_adjusted_rule_clarity_block")
    elif rule_clarity < config.min_pass_rule_clarity:
        reason_codes.append("cost_adjusted_rule_clarity_watch")
    if status == "block":
        reason_codes.append("cost_adjusted_completeness_block")
    elif status == "watch":
        reason_codes.append("cost_adjusted_completeness_watch")
    else:
        reason_codes.append("cost_adjusted_inputs_complete")
    return _normalize_reason_codes("reason_codes", tuple(reason_codes))


def _cost_completeness_score(
    total_cost_rate: Decimal,
    config: CostAdjustedInputCompletenessConfig,
) -> Decimal:
    if total_cost_rate > config.max_watch_total_cost_rate:
        return BLOCK_COST_COMPLETENESS_SCORE
    if total_cost_rate > config.max_pass_total_cost_rate:
        return WATCH_COST_COMPLETENESS_SCORE
    return PASS_COST_COMPLETENESS_SCORE


def _report_status(rows: tuple[CostAdjustedInputCompletenessRow, ...]) -> str:
    if not rows:
        return "block"
    if any(row.status == "block" for row in rows):
        return "block"
    if any(row.status == "watch" for row in rows):
        return "watch"
    return "pass"


def _summary_explanation(status: str, *, has_rows: bool) -> str:
    if not has_rows:
        return "block: no cost-adjusted inputs supplied for manual or paper review"
    return SUMMARY_EXPLANATION_BY_STATUS[status]


def _report_reason_codes(
    rows: tuple[CostAdjustedInputCompletenessRow, ...],
    *,
    status: str,
) -> tuple[str, ...]:
    if not rows:
        return ("cost_adjusted_inputs_report_empty",)
    generated_reasons = {
        reason_code
        for row in rows
        for reason_code in row.reason_codes
        if reason_code.startswith("cost_adjusted_")
    }
    report_reason = f"cost_adjusted_inputs_report_{status}"
    return (report_reason,) + tuple(
        reason_code
        for reason_code in REPORT_REASON_PRIORITY
        if reason_code in generated_reasons
    )


def _reason_code_counts(
    rows: tuple[CostAdjustedInputCompletenessRow, ...],
) -> tuple[CostAdjustedInputCompletenessReasonCodeCount, ...]:
    if not rows:
        return ()
    counts: Counter[str] = Counter(
        reason_code for row in rows for reason_code in row.reason_codes
    )
    denominator = _count_decimal(len(rows))
    return tuple(
        CostAdjustedInputCompletenessReasonCodeCount(
            reason_code=reason_code,
            count=_count_decimal(count),
            input_ratio=_divide_decimal(_count_decimal(count), denominator),
        )
        for reason_code, count in sorted(
            counts.items(),
            key=lambda item: (-item[1], item[0]),
        )
    )


def _report_payload_core(
    report: CostAdjustedInputCompletenessReport,
    *,
    include_digest: bool,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "generated_at": report.generated_at.isoformat(),
        "config_version": report.config_version,
        "input_count": _decimal_to_string(report.input_count),
        "pass_count": _decimal_to_string(report.pass_count),
        "watch_count": _decimal_to_string(report.watch_count),
        "block_count": _decimal_to_string(report.block_count),
        "max_total_cost_rate": _decimal_to_string(report.max_total_cost_rate),
        "min_completeness_score": _decimal_to_string(report.min_completeness_score),
        "status": report.status,
        "summary_explanation": report.summary_explanation,
        "reason_codes": list(report.reason_codes),
        "reason_code_counts": [
            _reason_code_count_payload(reason_count)
            for reason_count in report.reason_code_counts
        ],
        "rows": [_row_payload(row) for row in report.rows],
        "paper_only": report.paper_only,
        "report_only": report.report_only,
        "readonly": report.readonly,
    }
    if include_digest:
        payload["derived_validation_digest"] = report.derived_validation_digest
    return payload


def _row_payload(row: CostAdjustedInputCompletenessRow) -> dict[str, Any]:
    return {
        "row_index": _decimal_to_string(row.row_index),
        "spread_rate": _decimal_to_string(row.spread_rate),
        "taker_fee_rate": _decimal_to_string(row.taker_fee_rate),
        "deposit_friction_rate": _decimal_to_string(row.deposit_friction_rate),
        "settlement_friction_rate": _decimal_to_string(row.settlement_friction_rate),
        "gas_friction_rate": _decimal_to_string(row.gas_friction_rate),
        "total_cost_rate": _decimal_to_string(row.total_cost_rate),
        "liquidity_quality": _decimal_to_string(row.liquidity_quality),
        "evidence_freshness": _decimal_to_string(row.evidence_freshness),
        "rule_clarity": _decimal_to_string(row.rule_clarity),
        "completeness_score": _decimal_to_string(row.completeness_score),
        "observed_at": row.observed_at.isoformat(),
        "status": row.status,
        "status_explanation": row.status_explanation,
        "reason_codes": list(row.reason_codes),
        "paper_only": row.paper_only,
        "report_only": row.report_only,
        "readonly": row.readonly,
    }


def _reason_code_count_payload(
    reason_count: CostAdjustedInputCompletenessReasonCodeCount,
) -> dict[str, Any]:
    return {
        "reason_code": reason_count.reason_code,
        "count": _decimal_to_string(reason_count.count),
        "input_ratio": _decimal_to_string(reason_count.input_ratio),
        "paper_only": reason_count.paper_only,
        "report_only": reason_count.report_only,
        "readonly": reason_count.readonly,
    }


def _json_value(value: Any) -> Any:
    if isinstance(value, Decimal):
        return _decimal_to_string(value)
    if isinstance(value, datetime):
        return _as_utc("datetime", value).isoformat()
    if isinstance(value, tuple):
        return [_json_value(item) for item in value]
    if isinstance(value, list):
        return [_json_value(item) for item in value]
    if isinstance(value, dict):
        return {str(key): _json_value(item) for key, item in value.items()}
    return value


def _digest_payload(payload: dict[str, Any]) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return sha256(encoded.encode("utf-8")).hexdigest()


def _normalize_inputs(
    inputs: Iterable[CostAdjustedInputCompletenessInput],
) -> tuple[CostAdjustedInputCompletenessInput, ...]:
    if isinstance(inputs, (str, bytes)):
        raise ValueError("inputs must be an iterable of CostAdjustedInputCompletenessInput")
    try:
        values = tuple(inputs)
    except TypeError as exc:
        raise ValueError(
            "inputs must be an iterable of CostAdjustedInputCompletenessInput",
        ) from exc
    for value in values:
        if type(value) is not CostAdjustedInputCompletenessInput:
            raise ValueError("inputs must contain CostAdjustedInputCompletenessInput")
        _require_hard_flags("inputs", value)
    return values


def _normalize_rows(
    rows: tuple[CostAdjustedInputCompletenessRow, ...],
) -> tuple[CostAdjustedInputCompletenessRow, ...]:
    if type(rows) is not tuple:
        raise ValueError("rows must be a tuple")
    for row in rows:
        if type(row) is not CostAdjustedInputCompletenessRow:
            raise ValueError("rows must contain CostAdjustedInputCompletenessRow")
        _require_hard_flags("rows", row)
    return tuple(sorted(rows, key=_row_sort_key))


def _normalize_reason_code_counts(
    reason_code_counts: tuple[CostAdjustedInputCompletenessReasonCodeCount, ...],
) -> tuple[CostAdjustedInputCompletenessReasonCodeCount, ...]:
    if type(reason_code_counts) is not tuple:
        raise ValueError("reason_code_counts must be a tuple")
    for reason_count in reason_code_counts:
        if type(reason_count) is not CostAdjustedInputCompletenessReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "CostAdjustedInputCompletenessReasonCodeCount",
            )
        _require_hard_flags("reason_code_counts", reason_count)
    return tuple(sorted(reason_code_counts, key=lambda item: (-item.count, item.reason_code)))


def _normalize_reason_codes(
    field_name: str,
    value: tuple[str, ...],
) -> tuple[str, ...]:
    if type(value) is not tuple or not value:
        raise ValueError(f"{field_name} must be a non-empty tuple")
    normalized_items: list[str] = []
    seen: set[str] = set()
    for item in value:
        reason_code = _require_reason_code(field_name, item)
        if reason_code not in seen:
            normalized_items.append(reason_code)
            seen.add(reason_code)
    normalized = tuple(normalized_items)
    if not normalized:
        raise ValueError(f"{field_name} must not be empty")
    return normalized


def _normalize_sorted_reason_codes(
    field_name: str,
    value: tuple[str, ...],
) -> tuple[str, ...]:
    return tuple(sorted(_normalize_reason_codes(field_name, value)))


def _require_reason_code(field_name: str, value: str) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must contain strings")
    if value != value.strip() or value != value.lower() or not value:
        raise ValueError(f"{field_name} must contain canonical reason codes")
    if not all(char.isalnum() or char == "_" for char in value):
        raise ValueError(f"{field_name} must contain canonical reason codes")
    for fragment in UNSAFE_TEXT_FRAGMENTS:
        if fragment in value:
            raise ValueError(f"{field_name} contains unsafe public text")
    return value


def _require_safe_public_text(field_name: str, value: str) -> None:
    if type(value) is not str or not value or value != value.strip():
        raise ValueError(f"{field_name} must be non-empty text")
    lowered = value.lower()
    for fragment in UNSAFE_TEXT_FRAGMENTS:
        if fragment in lowered:
            raise ValueError(f"{field_name} contains unsafe public text")


def _require_status(field_name: str, value: str) -> None:
    if value not in STATUSES:
        raise ValueError(f"{field_name} must be one of {STATUSES}")


def _require_ratio_decimal(field_name: str, value: Decimal) -> Decimal:
    normalized = _require_nonnegative_decimal(field_name, value)
    if normalized > ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return normalized


def _require_positive_decimal(field_name: str, value: Decimal) -> Decimal:
    normalized = _require_nonnegative_decimal(field_name, value)
    if normalized <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _require_nonnegative_decimal(field_name: str, value: Decimal) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    if value < ZERO:
        raise ValueError(f"{field_name} must be non-negative")
    return _quantize_decimal(field_name, value)


def _quantize_decimal(field_name: str, value: Decimal) -> Decimal:
    try:
        with localcontext(DECIMAL_CONTEXT):
            return value.quantize(QUANTUM)
    except InvalidOperation as exc:
        raise ValueError(f"{field_name} must be quantizable") from exc


def _sum_decimals(values: tuple[Decimal, ...]) -> Decimal:
    total = ZERO
    with localcontext(DECIMAL_CONTEXT):
        for value in values:
            total += value
    return _quantize_decimal("total_cost_rate", total)


def _average_decimals(values: tuple[Decimal, ...]) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        total = sum(values, ZERO)
        return _quantize_decimal("completeness_score", total / Decimal(len(values)))


def _divide_decimal(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return _quantize_decimal("input_ratio", numerator / denominator)


def _count_decimal(value: int) -> Decimal:
    return _quantize_decimal("count", Decimal(value))


def _decimal_to_string(value: Decimal) -> str:
    if type(value) is not Decimal:
        raise ValueError("payload decimal value must be a Decimal")
    return format(value, "f")


def _as_utc(field_name: str, value: datetime) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _status_count(
    rows: tuple[CostAdjustedInputCompletenessRow, ...],
    status: str,
) -> Decimal:
    return _count_decimal(sum(1 for row in rows if row.status == status))


def _max_row_decimal(
    rows: tuple[CostAdjustedInputCompletenessRow, ...],
    field_name: str,
) -> Decimal:
    if not rows:
        return ZERO
    return max(getattr(row, field_name) for row in rows)


def _min_row_decimal(
    rows: tuple[CostAdjustedInputCompletenessRow, ...],
    field_name: str,
) -> Decimal:
    if not rows:
        return ZERO
    return min(getattr(row, field_name) for row in rows)


def _row_sort_key(row: CostAdjustedInputCompletenessRow) -> tuple[int, Decimal]:
    return (STATUS_SORT_WEIGHT[row.status], row.row_index)


def _validate_row_consistency(row: CostAdjustedInputCompletenessRow) -> None:
    expected_total = _sum_decimals(
        (
            row.spread_rate,
            row.taker_fee_rate,
            row.deposit_friction_rate,
            row.settlement_friction_rate,
            row.gas_friction_rate,
        ),
    )
    if row.total_cost_rate != expected_total:
        raise ValueError("row total_cost_rate is inconsistent")


def _validate_report_consistency(report: CostAdjustedInputCompletenessReport) -> None:
    rows = report.rows
    if report.input_count != _count_decimal(len(rows)):
        raise ValueError("input_count does not match rows")
    if report.pass_count != _status_count(rows, "pass"):
        raise ValueError("pass_count does not match rows")
    if report.watch_count != _status_count(rows, "watch"):
        raise ValueError("watch_count does not match rows")
    if report.block_count != _status_count(rows, "block"):
        raise ValueError("block_count does not match rows")
    if report.max_total_cost_rate != _max_row_decimal(rows, "total_cost_rate"):
        raise ValueError("max_total_cost_rate does not match rows")
    if report.min_completeness_score != _min_row_decimal(rows, "completeness_score"):
        raise ValueError("min_completeness_score does not match rows")
    if report.status != _report_status(rows):
        raise ValueError("status does not match rows")
    expected_summary = _summary_explanation(report.status, has_rows=bool(rows))
    if report.summary_explanation != expected_summary:
        raise ValueError("summary_explanation does not match status")


def _require_digest(value: str) -> None:
    if type(value) is not str or len(value) != 64:
        raise ValueError("derived_validation_digest must be a 64-character hex digest")
    if any(char not in HEX_CHARS for char in value):
        raise ValueError("derived_validation_digest must be a lowercase hex digest")


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in PHASE_FLAG_FIELDS:
        flag = getattr(value, field_name, None)
        if type(flag) is not bool or flag is not True:
            raise ValueError(f"{label}.{field_name} must be True")


def _require_exact_type(value: object, type_: type[object], label: str) -> None:
    if type(value) is not type_:
        raise ValueError(f"{label} must be exactly {type_.__name__}")


def _reject_unsafe_payload(value: object) -> None:
    json_ready = _json_value(value)
    encoded = json.dumps(json_ready, sort_keys=True, separators=(",", ":")).lower()
    for fragment in ("market", "source", "identifier"):
        if fragment in encoded:
            raise ValueError("payload contains unsafe public identity text")
    if "blocked" in encoded:
        raise ValueError("payload must use block status wording")
