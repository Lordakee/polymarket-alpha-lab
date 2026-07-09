"""Report-only cost drag versus confidence frontier snapshot.

The reducer accepts caller-supplied private candidate surfaces, computes a
public aggregate frontier from cost drag and confidence dimensions, and returns
only redacted report rows. It is paper-only, report-only, readonly, and never
recommends trades, positions, order placement, or sizing.
"""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable
from dataclasses import asdict, dataclass, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation
from hashlib import sha256
import json
from typing import Any


__all__ = (
    "ResearchStrategyCostConfidenceFrontierConfig",
    "ResearchStrategyCostConfidenceFrontierInput",
    "ResearchStrategyCostConfidenceFrontierReasonCodeCount",
    "ResearchStrategyCostConfidenceFrontierReport",
    "ResearchStrategyCostConfidenceFrontierRow",
    "build_research_strategy_cost_confidence_frontier_report",
    "research_strategy_cost_confidence_frontier_report_payload",
)


DEFAULT_CONFIG_VERSION = "research-strategy-cost-confidence-frontier-report-v0"
STATUSES = ("pass", "watch", "block")
ZERO = Decimal("0")
ONE = Decimal("1")
RATIO_QUANTUM = Decimal("0.000001")
THREE = Decimal("3")

UNSAFE_PUBLIC_SURFACE_FRAGMENTS = frozenset(
    (
        "api_key",
        "auth",
        "candidate",
        "candidate_id",
        "candidate_ref",
        "database",
        "dsn",
        "execute",
        "http://",
        "https://",
        "live",
        "market_id",
        "market_ref",
        "market_slug",
        "market_url",
        "position",
        "private_key",
        "question",
        "recommend",
        "order",
        "route",
        "secret",
        "sizing",
        "slug",
        "source_text",
        "source_url",
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
class ResearchStrategyCostConfidenceFrontierConfig:
    config_version: str = DEFAULT_CONFIG_VERSION
    pass_min_confidence: Decimal = Decimal("0.750000")
    watch_min_confidence: Decimal = Decimal("0.550000")
    pass_max_cost_drag: Decimal = Decimal("0.030000")
    block_max_cost_drag: Decimal = Decimal("0.080000")
    liquidity_penalty_weight: Decimal = Decimal("0.050000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchStrategyCostConfidenceFrontierConfig:
            raise TypeError(
                "ResearchStrategyCostConfidenceFrontierConfig does not support "
                "subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchStrategyCostConfidenceFrontierConfig:
            raise ValueError(
                "config must be exactly ResearchStrategyCostConfidenceFrontierConfig",
            )
        _require_canonical_string("config_version", self.config_version)
        if self.config_version != DEFAULT_CONFIG_VERSION:
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "pass_min_confidence",
            "watch_min_confidence",
            "pass_max_cost_drag",
            "block_max_cost_drag",
            "liquidity_penalty_weight",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_probability_decimal(field_name, getattr(self, field_name)),
            )
        if self.watch_min_confidence <= ZERO:
            raise ValueError("watch_min_confidence must be positive")
        if self.pass_min_confidence < self.watch_min_confidence:
            raise ValueError("pass_min_confidence must be at least watch_min_confidence")
        if self.pass_max_cost_drag <= ZERO:
            raise ValueError("pass_max_cost_drag must be positive")
        if self.block_max_cost_drag <= self.pass_max_cost_drag:
            raise ValueError("block_max_cost_drag must exceed pass_max_cost_drag")
        if self.liquidity_penalty_weight <= ZERO:
            raise ValueError("liquidity_penalty_weight must be positive")
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class ResearchStrategyCostConfidenceFrontierInput:
    candidate_id: str
    market_id: str
    market_slug: str
    market_question: str
    market_url: str
    fee_cost: Decimal
    spread_cost: Decimal
    slippage_cost: Decimal
    liquidity_reliability: Decimal
    evidence_strength: Decimal
    resolution_clarity: Decimal
    reason_codes: tuple[str, ...] = ()
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchStrategyCostConfidenceFrontierInput:
            raise TypeError(
                "ResearchStrategyCostConfidenceFrontierInput does not support "
                "subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchStrategyCostConfidenceFrontierInput:
            raise ValueError(
                "input must be exactly ResearchStrategyCostConfidenceFrontierInput",
            )
        for field_name in (
            "candidate_id",
            "market_id",
            "market_slug",
            "market_question",
            "market_url",
        ):
            _require_canonical_string(field_name, getattr(self, field_name))
        for field_name in (
            "fee_cost",
            "spread_cost",
            "slippage_cost",
            "liquidity_reliability",
            "evidence_strength",
            "resolution_clarity",
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
        _require_hard_flags("input", self)


@dataclass(frozen=True)
class ResearchStrategyCostConfidenceFrontierRow:
    rank: Decimal
    fee_cost: Decimal
    spread_cost: Decimal
    slippage_cost: Decimal
    liquidity_reliability: Decimal
    liquidity_reliability_drag: Decimal
    total_cost_drag: Decimal
    evidence_strength: Decimal
    resolution_clarity: Decimal
    confidence_score: Decimal
    frontier_score: Decimal
    frontier_status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchStrategyCostConfidenceFrontierRow:
            raise TypeError(
                "ResearchStrategyCostConfidenceFrontierRow does not support "
                "subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchStrategyCostConfidenceFrontierRow:
            raise ValueError(
                "row must be exactly ResearchStrategyCostConfidenceFrontierRow",
            )
        object.__setattr__(
            self,
            "rank",
            _require_positive_count_decimal("rank", self.rank),
        )
        for field_name in (
            "fee_cost",
            "spread_cost",
            "slippage_cost",
            "liquidity_reliability",
            "liquidity_reliability_drag",
            "total_cost_drag",
            "evidence_strength",
            "resolution_clarity",
            "confidence_score",
            "frontier_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_decimal(field_name, getattr(self, field_name)).quantize(
                    RATIO_QUANTUM,
                ),
            )
        for field_name in (
            "fee_cost",
            "spread_cost",
            "slippage_cost",
            "liquidity_reliability",
            "liquidity_reliability_drag",
            "total_cost_drag",
            "evidence_strength",
            "resolution_clarity",
            "confidence_score",
        ):
            _require_probability_decimal(field_name, getattr(self, field_name))
        _require_status("frontier_status", self.frontier_status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, allow_empty=False),
        )
        _require_hard_flags("row", self)
        _validate_row_consistency(self)


@dataclass(frozen=True)
class ResearchStrategyCostConfidenceFrontierReasonCodeCount:
    reason_code: str
    count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchStrategyCostConfidenceFrontierReasonCodeCount:
            raise TypeError(
                "ResearchStrategyCostConfidenceFrontierReasonCodeCount does not "
                "support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchStrategyCostConfidenceFrontierReasonCodeCount:
            raise ValueError(
                "reason_code_count must be exactly "
                "ResearchStrategyCostConfidenceFrontierReasonCodeCount",
            )
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
class ResearchStrategyCostConfidenceFrontierReport:
    generated_at: datetime
    config_version: str
    frontier_status: str
    sample_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    average_cost_drag: Decimal | None
    average_confidence_score: Decimal | None
    best_frontier_score: Decimal | None
    rows: tuple[ResearchStrategyCostConfidenceFrontierRow, ...]
    reason_code_counts: tuple[
        ResearchStrategyCostConfidenceFrontierReasonCodeCount,
        ...,
    ]
    reason_codes: tuple[str, ...]
    derived_validation_digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchStrategyCostConfidenceFrontierReport:
            raise TypeError(
                "ResearchStrategyCostConfidenceFrontierReport does not support "
                "subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchStrategyCostConfidenceFrontierReport:
            raise ValueError(
                "report must be exactly ResearchStrategyCostConfidenceFrontierReport",
            )
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        if self.config_version != DEFAULT_CONFIG_VERSION:
            raise ValueError("config_version must be the supported config version")
        _require_status("frontier_status", self.frontier_status)
        for field_name in ("sample_count", "pass_count", "watch_count", "block_count"):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_count_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "average_cost_drag",
            "average_confidence_score",
            "best_frontier_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_optional_decimal(field_name, getattr(self, field_name)),
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
            _normalize_reason_codes("reason_codes", self.reason_codes, allow_empty=False),
        )
        _require_sha256_hex("derived_validation_digest", self.derived_validation_digest)
        _require_hard_flags("report", self)
        _validate_report_consistency(self)
        _reject_unsafe_public_payload("report", _payload_value(self))
        expected_digest = _derived_validation_digest_for(_report_values_without_digest(self))
        if self.derived_validation_digest != expected_digest:
            raise ValueError("derived_validation_digest does not match report payload")


def build_research_strategy_cost_confidence_frontier_report(
    samples: Iterable[object],
    *,
    generated_at: datetime,
    config: ResearchStrategyCostConfidenceFrontierConfig | None = None,
) -> ResearchStrategyCostConfidenceFrontierReport:
    if config is None:
        config = ResearchStrategyCostConfidenceFrontierConfig()
    if type(config) is not ResearchStrategyCostConfidenceFrontierConfig:
        raise ValueError(
            "config must be a ResearchStrategyCostConfidenceFrontierConfig",
        )
    _require_hard_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    input_items = _normalize_inputs(samples)
    rows = _ranked_rows(input_items, config)
    reason_codes = _summary_reason_codes(rows)
    report_values = {
        "generated_at": generated_at_utc,
        "config_version": config.config_version,
        "frontier_status": _summary_status(rows),
        "sample_count": _decimal_count(len(rows)),
        "pass_count": _decimal_count(_status_count(rows, "pass")),
        "watch_count": _decimal_count(_status_count(rows, "watch")),
        "block_count": _decimal_count(_status_count(rows, "block")),
        "average_cost_drag": _average_cost_drag(rows),
        "average_confidence_score": _average_confidence_score(rows),
        "best_frontier_score": rows[0].frontier_score if rows else None,
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
    return ResearchStrategyCostConfidenceFrontierReport(**report_values)


def research_strategy_cost_confidence_frontier_report_payload(
    report: ResearchStrategyCostConfidenceFrontierReport | dict[str, Any],
) -> dict[str, Any]:
    label = "cost confidence frontier report payload"
    if type(report) is not ResearchStrategyCostConfidenceFrontierReport:
        if type(report) is not dict:
            raise ValueError(
                "report must be a ResearchStrategyCostConfidenceFrontierReport "
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


def _normalize_inputs(
    samples: Iterable[object],
) -> tuple[ResearchStrategyCostConfidenceFrontierInput, ...]:
    if isinstance(samples, (str, bytes)):
        raise ValueError("samples must be an iterable")
    try:
        values = tuple(samples)
    except TypeError as exc:
        raise ValueError("samples must be an iterable") from exc
    return tuple(_coerce_input(value) for value in values)


def _coerce_input(value: object) -> ResearchStrategyCostConfidenceFrontierInput:
    if type(value) is ResearchStrategyCostConfidenceFrontierInput:
        _require_hard_flags("input", value)
        return value
    _require_hard_flags("input", value)
    return ResearchStrategyCostConfidenceFrontierInput(
        candidate_id=_field_value(value, "candidate_id"),
        market_id=_field_value(value, "market_id"),
        market_slug=_field_value(value, "market_slug"),
        market_question=_field_value(value, "market_question"),
        market_url=_field_value(value, "market_url"),
        fee_cost=_field_value(value, "fee_cost"),
        spread_cost=_field_value(value, "spread_cost"),
        slippage_cost=_field_value(value, "slippage_cost"),
        liquidity_reliability=_field_value(value, "liquidity_reliability"),
        evidence_strength=_field_value(value, "evidence_strength"),
        resolution_clarity=_field_value(value, "resolution_clarity"),
        reason_codes=_field_value(value, "reason_codes", default=()),
        paper_only=_field_value(value, "paper_only"),
        report_only=_field_value(value, "report_only"),
        readonly=_field_value(value, "readonly"),
    )


def _ranked_rows(
    samples: tuple[ResearchStrategyCostConfidenceFrontierInput, ...],
    config: ResearchStrategyCostConfidenceFrontierConfig,
) -> tuple[ResearchStrategyCostConfidenceFrontierRow, ...]:
    scored = tuple((sample, _sample_metrics(sample, config)) for sample in samples)
    sorted_scored = tuple(
        sorted(
            scored,
            key=lambda item: (
                -_metric_decimal(item[1], "frontier_score"),
                _metric_decimal(item[1], "total_cost_drag"),
            ),
        ),
    )
    return tuple(
        _row_from_metrics(rank=index + 1, metrics=metrics)
        for index, (_sample, metrics) in enumerate(sorted_scored)
    )


def _sample_metrics(
    sample: ResearchStrategyCostConfidenceFrontierInput,
    config: ResearchStrategyCostConfidenceFrontierConfig,
) -> dict[str, Decimal | str | tuple[str, ...]]:
    liquidity_reliability_drag = _quantize(
        (ONE - sample.liquidity_reliability) * config.liquidity_penalty_weight,
    )
    total_cost_drag = _quantize(
        sample.fee_cost
        + sample.spread_cost
        + sample.slippage_cost
        + liquidity_reliability_drag,
    )
    confidence_score = _quantize(
        (
            sample.liquidity_reliability
            + sample.evidence_strength
            + sample.resolution_clarity
        )
        / THREE,
    )
    frontier_score = _quantize(confidence_score - total_cost_drag)
    frontier_status = _row_status(
        confidence_score=confidence_score,
        total_cost_drag=total_cost_drag,
        config=config,
    )
    return {
        "fee_cost": sample.fee_cost,
        "spread_cost": sample.spread_cost,
        "slippage_cost": sample.slippage_cost,
        "liquidity_reliability": sample.liquidity_reliability,
        "liquidity_reliability_drag": liquidity_reliability_drag,
        "total_cost_drag": total_cost_drag,
        "evidence_strength": sample.evidence_strength,
        "resolution_clarity": sample.resolution_clarity,
        "confidence_score": confidence_score,
        "frontier_score": frontier_score,
        "frontier_status": frontier_status,
        "reason_codes": _row_reason_codes(
            confidence_score=confidence_score,
            total_cost_drag=total_cost_drag,
            liquidity_reliability_drag=liquidity_reliability_drag,
            frontier_status=frontier_status,
            input_reason_codes=sample.reason_codes,
            config=config,
        ),
    }


def _row_from_metrics(
    *,
    rank: int,
    metrics: dict[str, Decimal | str | tuple[str, ...]],
) -> ResearchStrategyCostConfidenceFrontierRow:
    return ResearchStrategyCostConfidenceFrontierRow(
        rank=_decimal_count(rank),
        fee_cost=_metric_decimal(metrics, "fee_cost"),
        spread_cost=_metric_decimal(metrics, "spread_cost"),
        slippage_cost=_metric_decimal(metrics, "slippage_cost"),
        liquidity_reliability=_metric_decimal(metrics, "liquidity_reliability"),
        liquidity_reliability_drag=_metric_decimal(
            metrics,
            "liquidity_reliability_drag",
        ),
        total_cost_drag=_metric_decimal(metrics, "total_cost_drag"),
        evidence_strength=_metric_decimal(metrics, "evidence_strength"),
        resolution_clarity=_metric_decimal(metrics, "resolution_clarity"),
        confidence_score=_metric_decimal(metrics, "confidence_score"),
        frontier_score=_metric_decimal(metrics, "frontier_score"),
        frontier_status=_metric_status(metrics, "frontier_status"),
        reason_codes=_metric_reason_codes(metrics, "reason_codes"),
    )


def _row_status(
    *,
    confidence_score: Decimal,
    total_cost_drag: Decimal,
    config: ResearchStrategyCostConfidenceFrontierConfig,
) -> str:
    if (
        confidence_score >= config.pass_min_confidence
        and total_cost_drag <= config.pass_max_cost_drag
    ):
        return "pass"
    if confidence_score >= config.watch_min_confidence:
        return "watch"
    return "block"


def _row_reason_codes(
    *,
    confidence_score: Decimal,
    total_cost_drag: Decimal,
    liquidity_reliability_drag: Decimal,
    frontier_status: str,
    input_reason_codes: tuple[str, ...],
    config: ResearchStrategyCostConfidenceFrontierConfig,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    if confidence_score >= config.pass_min_confidence:
        reason_codes.append("high_confidence_score")
    elif confidence_score >= config.watch_min_confidence:
        reason_codes.append("confidence_score_watch_band")
    else:
        reason_codes.append("confidence_score_below_watch_band")

    if frontier_status == "pass":
        reason_codes.append("cost_confidence_frontier_pass")
        reason_codes.append("cost_drag_within_pass_band")
    elif frontier_status == "watch":
        reason_codes.append("cost_confidence_frontier_watch")
        reason_codes.append("cost_drag_watch_band")
    else:
        reason_codes.append("cost_confidence_frontier_block")
        reason_codes.append(
            "cost_drag_above_block_band"
            if total_cost_drag >= config.block_max_cost_drag
            else "cost_drag_watch_band",
        )

    if liquidity_reliability_drag > ZERO:
        reason_codes.append("liquidity_reliability_drag_applied")
    for reason_code in input_reason_codes:
        reason_codes.append(f"input_{reason_code}")
    return tuple(sorted(set(reason_codes)))


def _summary_reason_codes(
    rows: tuple[ResearchStrategyCostConfidenceFrontierRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return ("empty_frontier_samples",)
    if all(row.frontier_status == "pass" for row in rows):
        return ("cost_confidence_frontier_pass",)
    if all(row.frontier_status == "block" for row in rows):
        return tuple(sorted({reason_code for row in rows for reason_code in row.reason_codes}))
    return tuple(sorted({reason_code for row in rows for reason_code in row.reason_codes}))


def _summary_status(rows: tuple[ResearchStrategyCostConfidenceFrontierRow, ...]) -> str:
    if not rows:
        return "block"
    if all(row.frontier_status == "pass" for row in rows):
        return "pass"
    if all(row.frontier_status == "block" for row in rows):
        return "block"
    return "watch"


def _reason_code_counts(
    rows: tuple[ResearchStrategyCostConfidenceFrontierRow, ...],
    reason_codes: tuple[str, ...],
) -> tuple[ResearchStrategyCostConfidenceFrontierReasonCodeCount, ...]:
    if not rows:
        return (
            ResearchStrategyCostConfidenceFrontierReasonCodeCount(
                reason_code=reason_codes[0],
                count=ONE,
            ),
        )
    counts: Counter[str] = Counter()
    for row in rows:
        counts.update(row.reason_codes)
    return tuple(
        ResearchStrategyCostConfidenceFrontierReasonCodeCount(
            reason_code=reason_code,
            count=_decimal_count(count),
        )
        for reason_code, count in sorted(counts.items(), key=lambda item: item[0])
    )


def _status_count(
    rows: tuple[ResearchStrategyCostConfidenceFrontierRow, ...],
    status: str,
) -> int:
    return sum(1 for row in rows if row.frontier_status == status)


def _average_cost_drag(
    rows: tuple[ResearchStrategyCostConfidenceFrontierRow, ...],
) -> Decimal | None:
    if not rows:
        return None
    return _quantize(sum((row.total_cost_drag for row in rows), ZERO) / Decimal(len(rows)))


def _average_confidence_score(
    rows: tuple[ResearchStrategyCostConfidenceFrontierRow, ...],
) -> Decimal | None:
    if not rows:
        return None
    return _quantize(
        sum((row.confidence_score for row in rows), ZERO) / Decimal(len(rows)),
    )


def _normalize_rows(
    rows: tuple[ResearchStrategyCostConfidenceFrontierRow, ...],
) -> tuple[ResearchStrategyCostConfidenceFrontierRow, ...]:
    if type(rows) is not tuple:
        raise ValueError("rows must be a tuple")
    for row in rows:
        if type(row) is not ResearchStrategyCostConfidenceFrontierRow:
            raise ValueError(
                "rows must contain ResearchStrategyCostConfidenceFrontierRow values",
            )
        _require_hard_flags("row", row)
    expected_ranks = tuple(_decimal_count(index + 1) for index in range(len(rows)))
    if tuple(row.rank for row in rows) != expected_ranks:
        raise ValueError("rows must be ranked sequentially")
    sorted_rows = tuple(
        sorted(rows, key=lambda row: (-row.frontier_score, row.total_cost_drag, row.rank)),
    )
    if rows != sorted_rows:
        raise ValueError("rows must be sorted by frontier score")
    return rows


def _normalize_reason_code_counts(
    rows: tuple[ResearchStrategyCostConfidenceFrontierReasonCodeCount, ...],
) -> tuple[ResearchStrategyCostConfidenceFrontierReasonCodeCount, ...]:
    if type(rows) is not tuple:
        raise ValueError("reason_code_counts must be a tuple")
    for row in rows:
        if type(row) is not ResearchStrategyCostConfidenceFrontierReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "ResearchStrategyCostConfidenceFrontierReasonCodeCount values",
            )
        _require_hard_flags("reason_code_count", row)
    sorted_rows = tuple(sorted(rows, key=lambda row: row.reason_code))
    if rows != sorted_rows:
        raise ValueError("reason_code_counts must be sorted by reason_code")
    return rows


def _validate_row_consistency(row: ResearchStrategyCostConfidenceFrontierRow) -> None:
    expected_total_cost_drag = _quantize(
        row.fee_cost
        + row.spread_cost
        + row.slippage_cost
        + row.liquidity_reliability_drag,
    )
    if row.total_cost_drag != expected_total_cost_drag:
        raise ValueError("total_cost_drag must match cost components")
    expected_confidence_score = _quantize(
        (row.liquidity_reliability + row.evidence_strength + row.resolution_clarity)
        / THREE,
    )
    if row.confidence_score != expected_confidence_score:
        raise ValueError("confidence_score must match reliability and evidence dimensions")
    expected_frontier_score = _quantize(row.confidence_score - row.total_cost_drag)
    if row.frontier_score != expected_frontier_score:
        raise ValueError("frontier_score must match confidence score and cost drag")
    required_reason_code = f"cost_confidence_frontier_{row.frontier_status}"
    if required_reason_code not in row.reason_codes:
        raise ValueError("row reason_codes must include frontier status reason code")


def _validate_report_consistency(report: ResearchStrategyCostConfidenceFrontierReport) -> None:
    if report.sample_count != _decimal_count(len(report.rows)):
        raise ValueError("sample_count must match rows")
    if report.pass_count != _decimal_count(_status_count(report.rows, "pass")):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _decimal_count(_status_count(report.rows, "watch")):
        raise ValueError("watch_count must match rows")
    if report.block_count != _decimal_count(_status_count(report.rows, "block")):
        raise ValueError("block_count must match rows")
    if report.frontier_status != _summary_status(report.rows):
        raise ValueError("frontier_status must match row statuses")
    if report.average_cost_drag != _average_cost_drag(report.rows):
        raise ValueError("average_cost_drag must match rows")
    if report.average_confidence_score != _average_confidence_score(report.rows):
        raise ValueError("average_confidence_score must match rows")
    expected_best = report.rows[0].frontier_score if report.rows else None
    if report.best_frontier_score != expected_best:
        raise ValueError("best_frontier_score must match rows")
    if report.reason_codes != _summary_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")
    if report.reason_code_counts != _reason_code_counts(report.rows, report.reason_codes):
        raise ValueError("reason_code_counts must match rows")


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


def _field_value(value: object, field_name: str, *, default: object = _MISSING) -> Any:
    if isinstance(value, dict):
        if field_name in value:
            return value[field_name]
        if default is not _MISSING:
            return default
        raise ValueError(f"{field_name} is required")
    if hasattr(value, field_name):
        return getattr(value, field_name)
    if default is not _MISSING:
        return default
    raise ValueError(f"{field_name} is required")


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return value.quantize(RATIO_QUANTUM)


def _require_probability_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value < ZERO or decimal_value > ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return decimal_value


def _require_optional_decimal(field_name: str, value: object) -> Decimal | None:
    if value is None:
        return None
    return _require_decimal(field_name, value)


def _require_positive_count_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_count_decimal(field_name, value)
    if decimal_value <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return decimal_value


def _require_nonnegative_count_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_count_decimal(field_name, value)
    if decimal_value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return decimal_value


def _require_count_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    if value != value.to_integral_value():
        raise ValueError(f"{field_name} must be an integer Decimal")
    return value


def _decimal_count(value: int) -> Decimal:
    return Decimal(value)


def _quantize(value: Decimal) -> Decimal:
    try:
        return value.quantize(RATIO_QUANTUM)
    except InvalidOperation as exc:
        raise ValueError("Decimal value cannot be quantized") from exc


def _require_status(field_name: str, value: object) -> str:
    if type(value) is not str or value not in STATUSES:
        raise ValueError(f"{field_name} must be one of pass, watch, block")
    return value


def _normalize_reason_codes(
    field_name: str,
    values: object,
    *,
    allow_empty: bool,
) -> tuple[str, ...]:
    if type(values) is not tuple:
        raise ValueError(f"{field_name} must be a tuple")
    normalized = tuple(_normalize_reason_code(field_name, value) for value in values)
    if not allow_empty and not normalized:
        raise ValueError(f"{field_name} must not be empty")
    return tuple(sorted(set(normalized)))


def _normalize_reason_code(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must contain strings")
    if not value or value.strip() != value or value.lower() != value:
        raise ValueError(f"{field_name} must contain canonical lowercase strings")
    if any(fragment in value for fragment in UNSAFE_PUBLIC_SURFACE_FRAGMENTS):
        raise ValueError(f"{field_name} contains unsafe public surface")
    allowed = set("abcdefghijklmnopqrstuvwxyz0123456789_")
    if any(character not in allowed for character in value):
        raise ValueError(f"{field_name} must contain canonical reason code strings")
    return value


def _require_canonical_string(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a canonical nonblank string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")
    return value


def _require_sha256_hex(field_name: str, value: object) -> str:
    if type(value) is not str or len(value) != 64:
        raise ValueError(f"{field_name} must be a lowercase sha256 digest")
    if value.lower() != value or any(character not in "0123456789abcdef" for character in value):
        raise ValueError(f"{field_name} must be a lowercase sha256 digest")
    return value


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if getattr(value, field_name, None) is not True:
            raise ValueError(f"{label}.{field_name} must be True")


def _payload_value(value: Any) -> Any:
    if is_dataclass(value) and not isinstance(value, type):
        return _payload_value(asdict(value))
    if value is None:
        return None
    if type(value) is Decimal:
        if not value.is_finite():
            raise ValueError("public payload values must be JSON-safe")
        return str(value)
    if type(value) is datetime:
        return _as_utc("datetime payload value", value).isoformat()
    if type(value) in (str, bool):
        return value
    if type(value) in (int, float):
        raise ValueError("public numeric values must be Decimal strings")
    if type(value) is dict:
        payload: dict[str, Any] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("public payload keys must be strings")
            payload[key] = _payload_value(item)
        return payload
    if type(value) in (tuple, list):
        return [_payload_value(item) for item in value]
    raise ValueError("public payload values must be JSON-safe")


def _validate_public_payload(label: str, payload: object) -> None:
    if not isinstance(payload, dict):
        raise ValueError("report payload must be a JSON object")
    _require_hard_flags(label, _PayloadFlags(payload))
    _reject_unsafe_public_payload(label, payload)
    _validate_public_status_values(payload)
    _reject_public_numeric_primitives(payload)
    _ensure_json_safe(payload)
    digest = payload.get("derived_validation_digest")
    if digest is not None:
        _require_sha256_hex("derived_validation_digest", digest)
        expected = _derived_validation_digest_for(
            {key: value for key, value in payload.items() if key != "derived_validation_digest"},
        )
        if digest != expected:
            raise ValueError("derived_validation_digest does not match report payload")


def _reject_public_numeric_primitives(value: object) -> None:
    if type(value) is dict:
        for item in value.values():
            _reject_public_numeric_primitives(item)
        return
    if type(value) is list:
        for item in value:
            _reject_public_numeric_primitives(item)
        return
    if type(value) in (int, float):
        raise ValueError("public numeric values must be Decimal strings")
    if type(value) is Decimal:
        raise ValueError("public payload values must be JSON-safe")


def _ensure_json_safe(value: object) -> None:
    try:
        json.dumps(value, sort_keys=True, separators=(",", ":"))
    except (TypeError, ValueError) as exc:
        raise ValueError("public payload values must be JSON-safe") from exc


def _reject_unsafe_public_payload(label: str, value: object) -> None:
    if type(value) is dict:
        for key, item in value.items():
            if _contains_unsafe_public_surface(key):
                raise ValueError(f"unsafe public surface in {label}: {key}")
            _reject_unsafe_public_payload(label, item)
        return
    if type(value) in (tuple, list):
        for item in value:
            _reject_unsafe_public_payload(label, item)
        return
    if type(value) is str:
        if _contains_unsafe_public_surface(value):
            raise ValueError(f"unsafe public surface in {label}")


def _contains_unsafe_public_surface(value: str) -> bool:
    normalized = value.lower()
    compact = "".join(character for character in normalized if character.isalnum())
    for fragment in UNSAFE_PUBLIC_SURFACE_FRAGMENTS:
        compact_fragment = "".join(
            character for character in fragment if character.isalnum()
        )
        if fragment in normalized or (
            compact_fragment and compact_fragment in compact
        ):
            return True
    return False


def _validate_public_status_values(value: object) -> None:
    if type(value) is dict:
        for key, item in value.items():
            if _is_public_status_key(key):
                _require_status(key, item)
            _validate_public_status_values(item)
        return
    if type(value) is list:
        for item in value:
            _validate_public_status_values(item)


def _is_public_status_key(key: str) -> bool:
    normalized = key.lower()
    return normalized == "status" or normalized.endswith("_status")


def _report_values_without_digest(
    report: ResearchStrategyCostConfidenceFrontierReport,
) -> dict[str, Any]:
    payload = _payload_value(report)
    if not isinstance(payload, dict):
        raise ValueError("report payload must be a JSON object")
    payload.pop("derived_validation_digest", None)
    return payload


def _derived_validation_digest_for(values: dict[str, Any]) -> str:
    payload = _payload_value(values)
    if not isinstance(payload, dict):
        raise ValueError("digest payload must be a JSON object")
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return sha256(encoded).hexdigest()


class _PayloadFlags:
    def __init__(self, payload: dict[str, object]) -> None:
        self.paper_only = payload.get("paper_only")
        self.report_only = payload.get("report_only")
        self.readonly = payload.get("readonly")
