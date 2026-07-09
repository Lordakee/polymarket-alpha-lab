"""Pure in-memory expected value cost threshold report.

This reducer ranks caller-supplied research candidates by model-market expected
value edge after fees, spread, slippage, settlement uncertainty, and confidence
haircut. It is paper-only, report-only, readonly, and does not size positions,
submit orders, save state, or reach outside the supplied inputs.
"""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable
from dataclasses import dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation
from hashlib import sha256
import json
from typing import Any


__all__ = (
    "ResearchStrategyExpectedValueCostThresholdCandidate",
    "ResearchStrategyExpectedValueCostThresholdConfig",
    "ResearchStrategyExpectedValueCostThresholdReasonCodeCount",
    "ResearchStrategyExpectedValueCostThresholdReport",
    "ResearchStrategyExpectedValueCostThresholdRow",
    "build_research_strategy_expected_value_cost_threshold_report",
    "research_strategy_expected_value_cost_threshold_report_payload",
)


DEFAULT_CONFIG_VERSION = "research-strategy-expected-value-cost-threshold-report-v0"
STATUSES = ("pass", "watch", "block")
ZERO = Decimal("0")
ONE = Decimal("1")
RATIO_QUANTUM = Decimal("0.000001")


UNSAFE_PUBLIC_SURFACE_FRAGMENTS = frozenset(
    (
        "api_key",
        "auth",
        "candidate_id",
        "client",
        "database",
        "dsn",
        "http://",
        "https://",
        "live",
        "market_id",
        "market_question",
        "market_slug",
        "market_url",
        "network",
        "order",
        "persist",
        "private_key",
        "raw-",
        "raw_",
        "secret",
        "sizing",
        "submit",
        "table",
        "text",
        "token",
        "trade",
        "url",
        "wallet",
        "://",
    ),
)


class _Missing:
    pass


_MISSING = _Missing()


@dataclass(frozen=True)
class ResearchStrategyExpectedValueCostThresholdConfig:
    config_version: str = DEFAULT_CONFIG_VERSION
    pass_adjusted_edge_threshold: Decimal = Decimal("0.050000")
    watch_adjusted_edge_threshold: Decimal = Decimal("0.010000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchStrategyExpectedValueCostThresholdConfig:
            raise TypeError(
                "ResearchStrategyExpectedValueCostThresholdConfig does not support "
                "subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchStrategyExpectedValueCostThresholdConfig:
            raise ValueError(
                "config must be exactly ResearchStrategyExpectedValueCostThresholdConfig",
            )
        _require_canonical_string("config_version", self.config_version)
        if self.config_version != DEFAULT_CONFIG_VERSION:
            raise ValueError("config_version must be the supported config version")
        object.__setattr__(
            self,
            "pass_adjusted_edge_threshold",
            _require_positive_decimal(
                "pass_adjusted_edge_threshold",
                self.pass_adjusted_edge_threshold,
            ),
        )
        object.__setattr__(
            self,
            "watch_adjusted_edge_threshold",
            _require_positive_decimal(
                "watch_adjusted_edge_threshold",
                self.watch_adjusted_edge_threshold,
            ),
        )
        if self.pass_adjusted_edge_threshold < self.watch_adjusted_edge_threshold:
            raise ValueError(
                "pass_adjusted_edge_threshold must be at least watch threshold",
            )
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class ResearchStrategyExpectedValueCostThresholdCandidate:
    candidate_id: str
    market_id: str
    market_slug: str
    market_question: str
    market_url: str
    model_probability: Decimal
    market_probability: Decimal
    fee_cost: Decimal
    spread_cost: Decimal
    slippage_cost: Decimal
    settlement_uncertainty: Decimal
    confidence_haircut: Decimal
    reason_codes: tuple[str, ...] = ()
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        for field_name in (
            "candidate_id",
            "market_id",
            "market_slug",
            "market_question",
            "market_url",
        ):
            _require_canonical_string(field_name, getattr(self, field_name))
        for field_name in ("model_probability", "market_probability"):
            object.__setattr__(
                self,
                field_name,
                _require_probability_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "fee_cost",
            "spread_cost",
            "slippage_cost",
            "settlement_uncertainty",
            "confidence_haircut",
        ):
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
        _require_hard_flags("candidate", self)


@dataclass(frozen=True)
class ResearchStrategyExpectedValueCostThresholdRow:
    rank: Decimal
    model_probability: Decimal
    market_probability: Decimal
    gross_expected_value_edge: Decimal
    fee_cost: Decimal
    spread_cost: Decimal
    slippage_cost: Decimal
    settlement_uncertainty: Decimal
    confidence_haircut: Decimal
    total_cost_drag: Decimal
    adjusted_expected_value_edge: Decimal
    status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "rank",
            _require_positive_count_decimal("rank", self.rank),
        )
        for field_name in ("model_probability", "market_probability"):
            object.__setattr__(
                self,
                field_name,
                _require_probability_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "fee_cost",
            "spread_cost",
            "slippage_cost",
            "settlement_uncertainty",
            "confidence_haircut",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_probability_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "gross_expected_value_edge",
            "total_cost_drag",
            "adjusted_expected_value_edge",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_decimal(field_name, getattr(self, field_name)).quantize(
                    RATIO_QUANTUM,
                ),
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
class ResearchStrategyExpectedValueCostThresholdReasonCodeCount:
    reason_code: str
    count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "reason_code",
            _normalize_reason_code("reason_code", self.reason_code),
        )
        object.__setattr__(
            self,
            "count",
            _require_positive_count_decimal("count", self.count),
        )
        _require_hard_flags("reason_code_count", self)


@dataclass(frozen=True)
class ResearchStrategyExpectedValueCostThresholdReport:
    generated_at: datetime
    config_version: str
    candidate_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    blocked_count: Decimal
    average_adjusted_expected_value_edge: Decimal | None
    top_adjusted_expected_value_edge: Decimal | None
    status: str
    rows: tuple[ResearchStrategyExpectedValueCostThresholdRow, ...]
    reason_code_counts: tuple[
        ResearchStrategyExpectedValueCostThresholdReasonCodeCount,
        ...,
    ]
    reason_codes: tuple[str, ...]
    derived_validation_digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        if self.config_version != DEFAULT_CONFIG_VERSION:
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "candidate_count",
            "pass_count",
            "watch_count",
            "blocked_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_count_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "average_adjusted_expected_value_edge",
            "top_adjusted_expected_value_edge",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_optional_decimal(field_name, getattr(self, field_name)),
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
        _require_sha256_hex("derived_validation_digest", self.derived_validation_digest)
        _require_hard_flags("report", self)
        _validate_report_consistency(self)


def build_research_strategy_expected_value_cost_threshold_report(
    candidates: Iterable[object],
    *,
    config: ResearchStrategyExpectedValueCostThresholdConfig,
    generated_at: datetime,
) -> ResearchStrategyExpectedValueCostThresholdReport:
    if type(config) is not ResearchStrategyExpectedValueCostThresholdConfig:
        raise ValueError(
            "config must be a ResearchStrategyExpectedValueCostThresholdConfig",
        )
    _require_hard_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    candidate_items = _normalize_candidates(candidates)
    rows = _ranked_rows(candidate_items, config)
    reason_codes = _summary_reason_codes(rows)
    report_values = {
        "generated_at": generated_at_utc,
        "config_version": config.config_version,
        "candidate_count": _decimal_count(len(rows)),
        "pass_count": _decimal_count(_status_count(rows, "pass")),
        "watch_count": _decimal_count(_status_count(rows, "watch")),
        "blocked_count": _decimal_count(_status_count(rows, "block")),
        "average_adjusted_expected_value_edge": _average_adjusted_edge(rows),
        "top_adjusted_expected_value_edge": (
            rows[0].adjusted_expected_value_edge if rows else None
        ),
        "status": _summary_status(rows),
        "rows": rows,
        "reason_code_counts": _reason_code_counts(rows, reason_codes),
        "reason_codes": reason_codes,
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    report_values["derived_validation_digest"] = _derived_validation_digest_for(
        report_values,
    )
    return ResearchStrategyExpectedValueCostThresholdReport(**report_values)


def research_strategy_expected_value_cost_threshold_report_payload(
    report: ResearchStrategyExpectedValueCostThresholdReport | dict[str, Any],
) -> dict[str, Any]:
    label = "expected value cost threshold report payload"
    if type(report) is not ResearchStrategyExpectedValueCostThresholdReport:
        if type(report) is not dict:
            raise ValueError(
                "report must be a ResearchStrategyExpectedValueCostThresholdReport "
                "or payload dict",
            )
        _validate_public_payload(label, report)
        payload = _payload_value(report)
        _validate_public_payload(label, payload)
        if not isinstance(payload, dict):
            raise ValueError("report payload must be a JSON object")
        return payload
    _require_hard_flags("report", report)
    payload = _payload_value(report)
    if not isinstance(payload, dict):
        raise ValueError("report payload must be a JSON object")
    _validate_public_payload(label, payload)
    return payload


def _normalize_candidates(
    candidates: Iterable[object],
) -> tuple[ResearchStrategyExpectedValueCostThresholdCandidate, ...]:
    if isinstance(candidates, (str, bytes)):
        raise ValueError("candidates must be an iterable")
    try:
        values = tuple(candidates)
    except TypeError as exc:
        raise ValueError("candidates must be an iterable") from exc
    return tuple(_coerce_candidate(value) for value in values)


def _coerce_candidate(
    value: object,
) -> ResearchStrategyExpectedValueCostThresholdCandidate:
    if type(value) is ResearchStrategyExpectedValueCostThresholdCandidate:
        _require_hard_flags("candidate", value)
        return value
    _require_hard_flags("candidate", value)
    return ResearchStrategyExpectedValueCostThresholdCandidate(
        candidate_id=_field_value(value, "candidate_id"),
        market_id=_field_value(value, "market_id"),
        market_slug=_field_value(value, "market_slug"),
        market_question=_field_value(value, "market_question"),
        market_url=_field_value(value, "market_url"),
        model_probability=_field_value(value, "model_probability"),
        market_probability=_field_value(value, "market_probability"),
        fee_cost=_field_value(value, "fee_cost"),
        spread_cost=_field_value(value, "spread_cost"),
        slippage_cost=_field_value(value, "slippage_cost"),
        settlement_uncertainty=_field_value(value, "settlement_uncertainty"),
        confidence_haircut=_field_value(value, "confidence_haircut"),
        reason_codes=_field_value(value, "reason_codes", default=()),
        paper_only=_field_value(value, "paper_only"),
        report_only=_field_value(value, "report_only"),
        readonly=_field_value(value, "readonly"),
    )


def _ranked_rows(
    candidates: tuple[ResearchStrategyExpectedValueCostThresholdCandidate, ...],
    config: ResearchStrategyExpectedValueCostThresholdConfig,
) -> tuple[ResearchStrategyExpectedValueCostThresholdRow, ...]:
    scored = tuple(
        (
            candidate,
            _candidate_metrics(candidate, config),
        )
        for candidate in candidates
    )
    sorted_scored = tuple(
        sorted(
            scored,
            key=lambda item: (
                -item[1]["adjusted_expected_value_edge"],
                item[0].candidate_id,
                item[0].market_id,
            ),
        ),
    )
    return tuple(
        _row_from_metrics(rank=index + 1, metrics=metrics)
        for index, (_candidate, metrics) in enumerate(sorted_scored)
    )


def _candidate_metrics(
    candidate: ResearchStrategyExpectedValueCostThresholdCandidate,
    config: ResearchStrategyExpectedValueCostThresholdConfig,
) -> dict[str, Decimal | str | tuple[str, ...]]:
    gross_edge = _quantize(candidate.model_probability - candidate.market_probability)
    total_cost_drag = _quantize(
        candidate.fee_cost
        + candidate.spread_cost
        + candidate.slippage_cost
        + candidate.settlement_uncertainty
        + candidate.confidence_haircut,
    )
    adjusted_edge = _quantize(gross_edge - total_cost_drag)
    status = _row_status(
        gross_expected_value_edge=gross_edge,
        total_cost_drag=total_cost_drag,
        adjusted_expected_value_edge=adjusted_edge,
        config=config,
    )
    return {
        "model_probability": candidate.model_probability,
        "market_probability": candidate.market_probability,
        "gross_expected_value_edge": gross_edge,
        "fee_cost": candidate.fee_cost,
        "spread_cost": candidate.spread_cost,
        "slippage_cost": candidate.slippage_cost,
        "settlement_uncertainty": candidate.settlement_uncertainty,
        "confidence_haircut": candidate.confidence_haircut,
        "total_cost_drag": total_cost_drag,
        "adjusted_expected_value_edge": adjusted_edge,
        "status": status,
        "reason_codes": _row_reason_codes(
            gross_expected_value_edge=gross_edge,
            total_cost_drag=total_cost_drag,
            adjusted_expected_value_edge=adjusted_edge,
            confidence_haircut=candidate.confidence_haircut,
            status=status,
            input_reason_codes=candidate.reason_codes,
            config=config,
        ),
    }


def _row_from_metrics(
    *,
    rank: int,
    metrics: dict[str, Decimal | str | tuple[str, ...]],
) -> ResearchStrategyExpectedValueCostThresholdRow:
    return ResearchStrategyExpectedValueCostThresholdRow(
        rank=_decimal_count(rank),
        model_probability=_metric_decimal(metrics, "model_probability"),
        market_probability=_metric_decimal(metrics, "market_probability"),
        gross_expected_value_edge=_metric_decimal(
            metrics,
            "gross_expected_value_edge",
        ),
        fee_cost=_metric_decimal(metrics, "fee_cost"),
        spread_cost=_metric_decimal(metrics, "spread_cost"),
        slippage_cost=_metric_decimal(metrics, "slippage_cost"),
        settlement_uncertainty=_metric_decimal(metrics, "settlement_uncertainty"),
        confidence_haircut=_metric_decimal(metrics, "confidence_haircut"),
        total_cost_drag=_metric_decimal(metrics, "total_cost_drag"),
        adjusted_expected_value_edge=_metric_decimal(
            metrics,
            "adjusted_expected_value_edge",
        ),
        status=_metric_status(metrics, "status"),
        reason_codes=_metric_reason_codes(metrics, "reason_codes"),
    )


def _metric_decimal(
    metrics: dict[str, Decimal | str | tuple[str, ...]],
    name: str,
) -> Decimal:
    value = metrics[name]
    if type(value) is not Decimal:
        raise ValueError(f"{name} must be a Decimal")
    return value


def _metric_status(
    metrics: dict[str, Decimal | str | tuple[str, ...]],
    name: str,
) -> str:
    value = metrics[name]
    if type(value) is not str:
        raise ValueError(f"{name} must be a string")
    return value


def _metric_reason_codes(
    metrics: dict[str, Decimal | str | tuple[str, ...]],
    name: str,
) -> tuple[str, ...]:
    value = metrics[name]
    if type(value) is not tuple:
        raise ValueError(f"{name} must be a tuple")
    return value


def _row_status(
    *,
    gross_expected_value_edge: Decimal,
    total_cost_drag: Decimal,
    adjusted_expected_value_edge: Decimal,
    config: ResearchStrategyExpectedValueCostThresholdConfig,
) -> str:
    if gross_expected_value_edge <= ZERO or total_cost_drag >= gross_expected_value_edge:
        return "block"
    if adjusted_expected_value_edge >= config.pass_adjusted_edge_threshold:
        return "pass"
    if adjusted_expected_value_edge >= config.watch_adjusted_edge_threshold:
        return "watch"
    return "block"


def _row_reason_codes(
    *,
    gross_expected_value_edge: Decimal,
    total_cost_drag: Decimal,
    adjusted_expected_value_edge: Decimal,
    confidence_haircut: Decimal,
    status: str,
    input_reason_codes: tuple[str, ...],
    config: ResearchStrategyExpectedValueCostThresholdConfig,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    reason_codes.append(
        "positive_model_market_edge"
        if gross_expected_value_edge > ZERO
        else "model_edge_not_positive",
    )
    reason_codes.append(
        "cost_drag_within_edge"
        if total_cost_drag < gross_expected_value_edge
        else "cost_drag_exceeds_edge",
    )
    if confidence_haircut > ZERO:
        reason_codes.append("confidence_haircut_applied")
    if status == "pass":
        reason_codes.append("expected_value_cost_threshold_pass")
    elif status == "watch":
        reason_codes.append("expected_value_cost_threshold_watch")
    else:
        reason_codes.append("expected_value_edge_below_watch_threshold")
    for reason_code in input_reason_codes:
        reason_codes.append(f"input_{reason_code}")
    return tuple(sorted(set(reason_codes)))


def _summary_reason_codes(
    rows: tuple[ResearchStrategyExpectedValueCostThresholdRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return ("no_expected_value_candidates",)
    if all(row.status == "pass" for row in rows):
        return ("expected_value_cost_threshold_pass",)
    if all(row.status == "block" for row in rows):
        return tuple(
            sorted(
                {
                    reason_code
                    for row in rows
                    for reason_code in row.reason_codes
                    if reason_code.startswith("input_")
                    or reason_code
                    in (
                        "cost_drag_exceeds_edge",
                        "expected_value_edge_below_watch_threshold",
                        "model_edge_not_positive",
                    )
                },
            ),
        )
    return tuple(
        sorted({reason_code for row in rows for reason_code in row.reason_codes}),
    )


def _summary_status(
    rows: tuple[ResearchStrategyExpectedValueCostThresholdRow, ...],
) -> str:
    if not rows:
        return "block"
    if all(row.status == "pass" for row in rows):
        return "pass"
    if all(row.status == "block" for row in rows):
        return "block"
    return "watch"


def _reason_code_counts(
    rows: tuple[ResearchStrategyExpectedValueCostThresholdRow, ...],
    reason_codes: tuple[str, ...],
) -> tuple[ResearchStrategyExpectedValueCostThresholdReasonCodeCount, ...]:
    if not rows:
        return (
            ResearchStrategyExpectedValueCostThresholdReasonCodeCount(
                reason_code=reason_codes[0],
                count=ONE,
            ),
        )
    counts: Counter[str] = Counter()
    for row in rows:
        counts.update(row.reason_codes)
    return tuple(
        ResearchStrategyExpectedValueCostThresholdReasonCodeCount(
            reason_code=reason_code,
            count=_decimal_count(count),
        )
        for reason_code, count in sorted(counts.items(), key=lambda item: item[0])
    )


def _status_count(
    rows: tuple[ResearchStrategyExpectedValueCostThresholdRow, ...],
    status: str,
) -> int:
    return sum(1 for row in rows if row.status == status)


def _average_adjusted_edge(
    rows: tuple[ResearchStrategyExpectedValueCostThresholdRow, ...],
) -> Decimal | None:
    if not rows:
        return None
    return _quantize(
        sum((row.adjusted_expected_value_edge for row in rows), ZERO)
        / Decimal(len(rows)),
    )


def _normalize_rows(
    rows: tuple[ResearchStrategyExpectedValueCostThresholdRow, ...],
) -> tuple[ResearchStrategyExpectedValueCostThresholdRow, ...]:
    if type(rows) is not tuple:
        raise ValueError("rows must be a tuple")
    for row in rows:
        if type(row) is not ResearchStrategyExpectedValueCostThresholdRow:
            raise ValueError(
                "rows must contain ResearchStrategyExpectedValueCostThresholdRow values",
            )
        _require_hard_flags("row", row)
    expected_ranks = tuple(_decimal_count(index + 1) for index in range(len(rows)))
    if tuple(row.rank for row in rows) != expected_ranks:
        raise ValueError("rows must be ranked sequentially")
    sorted_rows = tuple(
        sorted(rows, key=lambda row: (-row.adjusted_expected_value_edge, row.rank)),
    )
    if rows != sorted_rows:
        raise ValueError("rows must be sorted by adjusted expected value edge")
    return rows


def _normalize_reason_code_counts(
    rows: tuple[ResearchStrategyExpectedValueCostThresholdReasonCodeCount, ...],
) -> tuple[ResearchStrategyExpectedValueCostThresholdReasonCodeCount, ...]:
    if type(rows) is not tuple:
        raise ValueError("reason_code_counts must be a tuple")
    for row in rows:
        if type(row) is not ResearchStrategyExpectedValueCostThresholdReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "ResearchStrategyExpectedValueCostThresholdReasonCodeCount values",
            )
        _require_hard_flags("reason_code_count", row)
    sorted_rows = tuple(sorted(rows, key=lambda row: row.reason_code))
    if rows != sorted_rows:
        raise ValueError("reason_code_counts must be sorted by reason_code")
    return rows


def _validate_row_consistency(row: ResearchStrategyExpectedValueCostThresholdRow) -> None:
    expected_total_cost_drag = _quantize(
        row.fee_cost
        + row.spread_cost
        + row.slippage_cost
        + row.settlement_uncertainty
        + row.confidence_haircut,
    )
    if row.total_cost_drag != expected_total_cost_drag:
        raise ValueError("total_cost_drag must match cost components")
    expected_gross_edge = _quantize(row.model_probability - row.market_probability)
    if row.gross_expected_value_edge != expected_gross_edge:
        raise ValueError(
            "gross_expected_value_edge must match model and market probabilities",
        )
    expected_adjusted_edge = _quantize(row.gross_expected_value_edge - row.total_cost_drag)
    if row.adjusted_expected_value_edge != expected_adjusted_edge:
        raise ValueError(
            "adjusted_expected_value_edge must match gross edge and total cost drag",
        )
    if row.status == "pass":
        if "expected_value_cost_threshold_pass" not in row.reason_codes:
            raise ValueError("pass rows must include pass reason code")
    if row.status == "watch" and "expected_value_cost_threshold_watch" not in row.reason_codes:
        raise ValueError("watch rows must include watch reason code")
    if row.status == "block" and "expected_value_edge_below_watch_threshold" not in row.reason_codes:
        raise ValueError("block rows must include block reason code")


def _validate_report_consistency(
    report: ResearchStrategyExpectedValueCostThresholdReport,
) -> None:
    if report.candidate_count != _decimal_count(len(report.rows)):
        raise ValueError("candidate_count must match rows")
    if report.pass_count != _decimal_count(_status_count(report.rows, "pass")):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _decimal_count(_status_count(report.rows, "watch")):
        raise ValueError("watch_count must match rows")
    if report.blocked_count != _decimal_count(_status_count(report.rows, "block")):
        raise ValueError("blocked_count must match rows")
    if report.average_adjusted_expected_value_edge != _average_adjusted_edge(report.rows):
        raise ValueError("average_adjusted_expected_value_edge must match rows")
    expected_top_edge = (
        report.rows[0].adjusted_expected_value_edge if report.rows else None
    )
    if report.top_adjusted_expected_value_edge != expected_top_edge:
        raise ValueError("top_adjusted_expected_value_edge must match rows")
    if report.status != _summary_status(report.rows):
        raise ValueError("status must match rows")
    if report.reason_codes != _summary_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")
    if report.reason_code_counts != _reason_code_counts(report.rows, report.reason_codes):
        raise ValueError("reason_code_counts must match rows")
    if report.derived_validation_digest != _expected_derived_validation_digest(report):
        raise ValueError("derived_validation_digest must match report values")


def _payload_value(value: object) -> object:
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, datetime):
        return value.isoformat()
    if is_dataclass(value) and not isinstance(value, type):
        return {
            field.name: _payload_value(getattr(value, field.name))
            for field in fields(value)
        }
    if isinstance(value, tuple):
        return [_payload_value(item) for item in value]
    if isinstance(value, list):
        return [_payload_value(item) for item in value]
    if isinstance(value, dict):
        return {str(key): _payload_value(item) for key, item in value.items()}
    return value


def _expected_derived_validation_digest(
    report: ResearchStrategyExpectedValueCostThresholdReport,
) -> str:
    return _derived_validation_digest_for(
        {
            field.name: getattr(report, field.name)
            for field in fields(report)
            if field.name != "derived_validation_digest"
        },
    )


def _derived_validation_digest_for(values: dict[str, object]) -> str:
    encoded = json.dumps(
        _payload_value(values),
        sort_keys=True,
        separators=(",", ":"),
    )
    return sha256(encoded.encode("utf-8")).hexdigest()


def _validate_public_payload(label: str, payload: object) -> None:
    if type(payload) is not dict:
        raise ValueError(f"{label} must be a JSON object")
    _require_payload_flags(label, payload)
    _reject_unsafe_public_surfaces(label, payload)
    _reject_public_numeric_primitives(label, payload)
    _reject_public_datetime_values(label, payload)
    _reject_public_non_json_values(label, payload)
    _validate_payload_digest_if_present(label, payload)


def _require_payload_flags(label: str, payload: dict[str, Any]) -> None:
    for flag_name in ("paper_only", "report_only", "readonly"):
        if payload.get(flag_name) is not True:
            raise ValueError(f"{label}.{flag_name} must be True")


def _reject_unsafe_public_surfaces(label: str, payload: object) -> None:
    for path, value in _iter_public_payload_values(payload):
        if _has_unsafe_public_surface(path) or (
            type(value) is str and _has_unsafe_public_surface(value)
        ):
            raise ValueError(f"unsafe surface in {label}: {path}")


def _reject_public_numeric_primitives(label: str, payload: object) -> None:
    for path, value in _iter_public_payload_values(payload):
        if type(value) in (int, float):
            raise ValueError(
                f"public numeric values must be Decimal strings in {label}: {path}",
            )


def _reject_public_datetime_values(label: str, payload: object) -> None:
    for path, value in _iter_public_payload_values(payload):
        if isinstance(value, datetime):
            if type(value) is not datetime:
                raise ValueError(f"{path} must be a datetime")
            if value.tzinfo is None or value.utcoffset() is None:
                raise ValueError(f"{path} must be timezone-aware")


def _reject_public_non_json_values(label: str, payload: object) -> None:
    for path, value in _iter_public_payload_values(payload):
        if value is not None and type(value) not in (dict, list, str, bool, int, float):
            raise ValueError(f"public payload values must be JSON-safe in {label}: {path}")


def _validate_payload_digest_if_present(
    label: str,
    payload: dict[str, Any],
) -> None:
    digest = payload.get("derived_validation_digest")
    if digest is None:
        return
    _require_sha256_hex("derived_validation_digest", digest)
    values = dict(payload)
    del values["derived_validation_digest"]
    if digest != _derived_validation_digest_for(values):
        raise ValueError(f"{label}.derived_validation_digest must match payload values")


def _iter_public_payload_values(
    value: object,
    path: str = "payload",
) -> tuple[tuple[str, object], ...]:
    values: list[tuple[str, object]] = []
    if isinstance(value, dict):
        for key, item in value.items():
            key_text = str(key)
            item_path = f"{path}.{key_text}"
            values.append((item_path, item))
            values.extend(_iter_public_payload_values(item, item_path))
    elif isinstance(value, (list, tuple)):
        for index, item in enumerate(value):
            item_path = f"{path}[{index}]"
            values.append((item_path, item))
            values.extend(_iter_public_payload_values(item, item_path))
    return tuple(values)


def _has_unsafe_public_surface(value: str) -> bool:
    lowered = value.lower()
    return any(fragment in lowered for fragment in UNSAFE_PUBLIC_SURFACE_FRAGMENTS)


def _as_utc(field_name: str, value: datetime) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _field_value(value: object, field_name: str, *, default: object = _MISSING) -> object:
    if is_dataclass(value):
        for field in fields(value):
            if field.name == field_name:
                return getattr(value, field_name)
    if type(value) is dict and field_name in value:
        return value[field_name]
    if hasattr(value, field_name):
        return getattr(value, field_name)
    if default is not _MISSING:
        return default
    raise ValueError(f"{field_name} is required")


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    try:
        return +value
    except InvalidOperation as exc:
        raise ValueError(f"{field_name} must be finite") from exc


def _require_optional_decimal(field_name: str, value: object) -> Decimal | None:
    if value is None:
        return None
    return _require_decimal(field_name, value).quantize(RATIO_QUANTUM)


def _require_positive_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value).quantize(RATIO_QUANTUM)
    if normalized <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _require_probability_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < ZERO or normalized > ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return _quantize(normalized)


def _require_positive_count_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_positive_decimal(field_name, value)
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{field_name} must be an integer count")
    return normalized


def _require_nonnegative_count_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{field_name} must be an integer count")
    return normalized


def _decimal_count(value: int) -> Decimal:
    if type(value) is not int:
        raise ValueError("count source must be an int")
    if value < 0:
        raise ValueError("count source must be nonnegative")
    return Decimal(value)


def _quantize(value: Decimal) -> Decimal:
    return value.quantize(RATIO_QUANTUM)


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str or not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a nonempty canonical string")


def _normalize_reason_codes(
    field_name: str,
    values: object,
    *,
    allow_empty: bool,
) -> tuple[str, ...]:
    if type(values) is not tuple:
        raise ValueError(f"{field_name} must be a tuple")
    normalized: list[str] = []
    for value in values:
        normalized.append(_normalize_reason_code(field_name, value))
    if not allow_empty and not normalized:
        raise ValueError(f"{field_name} must be nonempty")
    return tuple(normalized)


def _normalize_reason_code(field_name: str, value: object) -> str:
    _require_canonical_string(field_name, value)
    if _has_unsafe_public_surface(value):
        raise ValueError(f"{field_name} contains unsafe surface")
    return value


def _require_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in STATUSES:
        raise ValueError(f"{field_name} must be a known status")


def _require_hard_flags(label: str, value: object) -> None:
    for flag in ("paper_only", "report_only", "readonly"):
        flag_value = _field_value(value, flag)
        if type(flag_value) is not bool or flag_value is not True:
            raise ValueError(f"{label}.{flag} must be True")


def _require_sha256_hex(field_name: str, value: object) -> None:
    if (
        type(value) is not str
        or len(value) != 64
        or any(character not in "0123456789abcdef" for character in value)
    ):
        raise ValueError(f"{field_name} must be a sha256 hex digest")
