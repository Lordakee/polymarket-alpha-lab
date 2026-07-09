"""Report-only cost-weighted signal router snapshot.

The reducer accepts caller-supplied private signal surfaces, computes public
aggregate router rows from signal quality and cost drag dimensions, and returns
only redacted report payloads. It is paper-only, report-only, readonly, and has
no database, network, wallet, order, sizing, or live execution surface.
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
    "ResearchStrategyCostWeightedSignalRouterConfig",
    "ResearchStrategyCostWeightedSignalRouterInput",
    "ResearchStrategyCostWeightedSignalRouterReasonCodeCount",
    "ResearchStrategyCostWeightedSignalRouterReport",
    "ResearchStrategyCostWeightedSignalRouterRow",
    "build_research_strategy_cost_weighted_signal_router_report",
    "research_strategy_cost_weighted_signal_router_report_payload",
)


DEFAULT_CONFIG_VERSION = "research-strategy-cost-weighted-signal-router-report-v0"
STATUSES = ("pass", "watch", "block")
ZERO = Decimal("0")
ONE = Decimal("1")
RATIO_QUANTUM = Decimal("0.000001")

UNSAFE_PUBLIC_SURFACE_FRAGMENTS = frozenset(
    (
        "api_key",
        "auth",
        "candidate",
        "candidate_id",
        "database",
        "dsn",
        "execute",
        "http://",
        "https://",
        "live",
        "market_id",
        "market_slug",
        "order",
        "position",
        "private_key",
        "question",
        "recommend",
        "secret",
        "signal_id",
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
class ResearchStrategyCostWeightedSignalRouterConfig:
    config_version: str = DEFAULT_CONFIG_VERSION
    pass_min_router_score: Decimal = Decimal("0.700000")
    watch_min_router_score: Decimal = Decimal("0.450000")
    block_min_cost_drag: Decimal = Decimal("0.120000")
    cost_drag_weight: Decimal = Decimal("0.500000")
    staleness_weight: Decimal = Decimal("0.200000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchStrategyCostWeightedSignalRouterConfig:
            raise TypeError(
                "ResearchStrategyCostWeightedSignalRouterConfig does not support "
                "subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchStrategyCostWeightedSignalRouterConfig:
            raise ValueError(
                "config must be exactly ResearchStrategyCostWeightedSignalRouterConfig",
            )
        _require_canonical_string("config_version", self.config_version)
        if self.config_version != DEFAULT_CONFIG_VERSION:
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "pass_min_router_score",
            "watch_min_router_score",
            "block_min_cost_drag",
            "cost_drag_weight",
            "staleness_weight",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_probability_decimal(field_name, getattr(self, field_name)),
            )
        if self.watch_min_router_score <= ZERO:
            raise ValueError("watch_min_router_score must be positive")
        if self.pass_min_router_score < self.watch_min_router_score:
            raise ValueError(
                "pass_min_router_score must be at least watch_min_router_score",
            )
        if self.block_min_cost_drag <= ZERO:
            raise ValueError("block_min_cost_drag must be positive")
        if self.cost_drag_weight <= ZERO:
            raise ValueError("cost_drag_weight must be positive")
        if self.staleness_weight <= ZERO:
            raise ValueError("staleness_weight must be positive")
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class ResearchStrategyCostWeightedSignalRouterInput:
    signal_id: str
    candidate_id: str
    market_id: str
    market_slug: str
    market_question: str
    source_url: str
    source_text: str
    signal_strength: Decimal
    signal_confidence: Decimal
    source_quorum_score: Decimal
    fee_cost: Decimal
    spread_cost: Decimal
    slippage_cost: Decimal
    source_staleness: Decimal
    reason_codes: tuple[str, ...] = ()
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchStrategyCostWeightedSignalRouterInput:
            raise TypeError(
                "ResearchStrategyCostWeightedSignalRouterInput does not support "
                "subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchStrategyCostWeightedSignalRouterInput:
            raise ValueError(
                "input must be exactly ResearchStrategyCostWeightedSignalRouterInput",
            )
        for field_name in (
            "signal_id",
            "candidate_id",
            "market_id",
            "market_slug",
            "market_question",
            "source_url",
            "source_text",
        ):
            _require_canonical_string(field_name, getattr(self, field_name))
        for field_name in (
            "signal_strength",
            "signal_confidence",
            "source_quorum_score",
            "fee_cost",
            "spread_cost",
            "slippage_cost",
            "source_staleness",
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
class ResearchStrategyCostWeightedSignalRouterRow:
    rank: Decimal
    signal_strength: Decimal
    signal_confidence: Decimal
    source_quorum_score: Decimal
    raw_signal_score: Decimal
    cost_drag: Decimal
    cost_drag_penalty: Decimal
    source_staleness: Decimal
    staleness_penalty: Decimal
    router_score: Decimal
    router_status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchStrategyCostWeightedSignalRouterRow:
            raise TypeError(
                "ResearchStrategyCostWeightedSignalRouterRow does not support "
                "subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchStrategyCostWeightedSignalRouterRow:
            raise ValueError(
                "row must be exactly ResearchStrategyCostWeightedSignalRouterRow",
            )
        object.__setattr__(
            self,
            "rank",
            _require_positive_count_decimal("rank", self.rank),
        )
        for field_name in (
            "signal_strength",
            "signal_confidence",
            "source_quorum_score",
            "raw_signal_score",
            "cost_drag",
            "cost_drag_penalty",
            "source_staleness",
            "staleness_penalty",
            "router_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_decimal(field_name, getattr(self, field_name)).quantize(
                    RATIO_QUANTUM,
                ),
            )
        for field_name in (
            "signal_strength",
            "signal_confidence",
            "source_quorum_score",
            "raw_signal_score",
            "cost_drag",
            "cost_drag_penalty",
            "source_staleness",
            "staleness_penalty",
        ):
            _require_probability_decimal(field_name, getattr(self, field_name))
        _require_status("router_status", self.router_status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, allow_empty=False),
        )
        _require_hard_flags("row", self)
        _validate_row_consistency(self)


@dataclass(frozen=True)
class ResearchStrategyCostWeightedSignalRouterReasonCodeCount:
    reason_code: str
    count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchStrategyCostWeightedSignalRouterReasonCodeCount:
            raise TypeError(
                "ResearchStrategyCostWeightedSignalRouterReasonCodeCount does not "
                "support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchStrategyCostWeightedSignalRouterReasonCodeCount:
            raise ValueError(
                "reason_code_count must be exactly "
                "ResearchStrategyCostWeightedSignalRouterReasonCodeCount",
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
class ResearchStrategyCostWeightedSignalRouterReport:
    generated_at: datetime
    config_version: str
    router_status: str
    sample_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    average_router_score: Decimal | None
    average_cost_drag: Decimal | None
    top_router_score: Decimal | None
    rows: tuple[ResearchStrategyCostWeightedSignalRouterRow, ...]
    reason_code_counts: tuple[
        ResearchStrategyCostWeightedSignalRouterReasonCodeCount,
        ...,
    ]
    reason_codes: tuple[str, ...]
    derived_validation_digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchStrategyCostWeightedSignalRouterReport:
            raise TypeError(
                "ResearchStrategyCostWeightedSignalRouterReport does not support "
                "subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchStrategyCostWeightedSignalRouterReport:
            raise ValueError(
                "report must be exactly ResearchStrategyCostWeightedSignalRouterReport",
            )
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        if self.config_version != DEFAULT_CONFIG_VERSION:
            raise ValueError("config_version must be the supported config version")
        _require_status("router_status", self.router_status)
        for field_name in ("sample_count", "pass_count", "watch_count", "block_count"):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_count_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "average_router_score",
            "average_cost_drag",
            "top_router_score",
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


def build_research_strategy_cost_weighted_signal_router_report(
    samples: Iterable[object],
    *,
    generated_at: datetime,
    config: ResearchStrategyCostWeightedSignalRouterConfig | None = None,
) -> ResearchStrategyCostWeightedSignalRouterReport:
    if config is None:
        config = ResearchStrategyCostWeightedSignalRouterConfig()
    if type(config) is not ResearchStrategyCostWeightedSignalRouterConfig:
        raise ValueError(
            "config must be a ResearchStrategyCostWeightedSignalRouterConfig",
        )
    _require_hard_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    input_items = _normalize_inputs(samples)
    rows = _ranked_rows(input_items, config)
    reason_codes = _summary_reason_codes(rows)
    report_values = {
        "generated_at": generated_at_utc,
        "config_version": config.config_version,
        "router_status": _summary_status(rows),
        "sample_count": _decimal_count(len(rows)),
        "pass_count": _decimal_count(_status_count(rows, "pass")),
        "watch_count": _decimal_count(_status_count(rows, "watch")),
        "block_count": _decimal_count(_status_count(rows, "block")),
        "average_router_score": _average_router_score(rows),
        "average_cost_drag": _average_cost_drag(rows),
        "top_router_score": rows[0].router_score if rows else None,
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
    return ResearchStrategyCostWeightedSignalRouterReport(**report_values)


def research_strategy_cost_weighted_signal_router_report_payload(
    report: ResearchStrategyCostWeightedSignalRouterReport | dict[str, Any],
) -> dict[str, Any]:
    label = "cost weighted signal router report payload"
    if type(report) is not ResearchStrategyCostWeightedSignalRouterReport:
        if type(report) is not dict:
            raise ValueError(
                "report must be a ResearchStrategyCostWeightedSignalRouterReport "
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
) -> tuple[ResearchStrategyCostWeightedSignalRouterInput, ...]:
    if isinstance(samples, (str, bytes)):
        raise ValueError("samples must be an iterable")
    try:
        values = tuple(samples)
    except TypeError as exc:
        raise ValueError("samples must be an iterable") from exc
    return tuple(_coerce_input(value) for value in values)


def _coerce_input(value: object) -> ResearchStrategyCostWeightedSignalRouterInput:
    if type(value) is ResearchStrategyCostWeightedSignalRouterInput:
        _require_hard_flags("input", value)
        return value
    _require_hard_flags("input", value)
    return ResearchStrategyCostWeightedSignalRouterInput(
        signal_id=_field_value(value, "signal_id"),
        candidate_id=_field_value(value, "candidate_id"),
        market_id=_field_value(value, "market_id"),
        market_slug=_field_value(value, "market_slug"),
        market_question=_field_value(value, "market_question"),
        source_url=_field_value(value, "source_url"),
        source_text=_field_value(value, "source_text"),
        signal_strength=_field_value(value, "signal_strength"),
        signal_confidence=_field_value(value, "signal_confidence"),
        source_quorum_score=_field_value(value, "source_quorum_score"),
        fee_cost=_field_value(value, "fee_cost"),
        spread_cost=_field_value(value, "spread_cost"),
        slippage_cost=_field_value(value, "slippage_cost"),
        source_staleness=_field_value(value, "source_staleness"),
        reason_codes=_field_value(value, "reason_codes", default=()),
        paper_only=_field_value(value, "paper_only"),
        report_only=_field_value(value, "report_only"),
        readonly=_field_value(value, "readonly"),
    )


def _ranked_rows(
    samples: tuple[ResearchStrategyCostWeightedSignalRouterInput, ...],
    config: ResearchStrategyCostWeightedSignalRouterConfig,
) -> tuple[ResearchStrategyCostWeightedSignalRouterRow, ...]:
    scored = tuple((sample, _sample_metrics(sample, config)) for sample in samples)
    sorted_scored = tuple(
        sorted(
            scored,
            key=lambda item: (
                -_metric_decimal(item[1], "router_score"),
                _metric_decimal(item[1], "cost_drag"),
                item[0].signal_id,
                item[0].candidate_id,
                item[0].market_id,
            ),
        ),
    )
    return tuple(
        _row_from_metrics(rank=index + 1, metrics=metrics)
        for index, (_sample, metrics) in enumerate(sorted_scored)
    )


def _sample_metrics(
    sample: ResearchStrategyCostWeightedSignalRouterInput,
    config: ResearchStrategyCostWeightedSignalRouterConfig,
) -> dict[str, Decimal | str | tuple[str, ...]]:
    raw_signal_score = sample.signal_strength
    cost_drag = _quantize(sample.fee_cost + sample.spread_cost + sample.slippage_cost)
    cost_drag_penalty = _quantize(cost_drag * config.cost_drag_weight)
    staleness_penalty = _quantize(sample.source_staleness * config.staleness_weight)
    router_score = _quantize(raw_signal_score - cost_drag_penalty - staleness_penalty)
    router_status = _row_status(
        router_score=router_score,
        cost_drag=cost_drag,
        config=config,
    )
    return {
        "signal_strength": sample.signal_strength,
        "signal_confidence": sample.signal_confidence,
        "source_quorum_score": sample.source_quorum_score,
        "raw_signal_score": raw_signal_score,
        "cost_drag": cost_drag,
        "cost_drag_penalty": cost_drag_penalty,
        "source_staleness": sample.source_staleness,
        "staleness_penalty": staleness_penalty,
        "router_score": router_score,
        "router_status": router_status,
        "reason_codes": _row_reason_codes(
            router_score=router_score,
            cost_drag=cost_drag,
            staleness_penalty=staleness_penalty,
            router_status=router_status,
            input_reason_codes=sample.reason_codes,
            config=config,
        ),
    }


def _row_from_metrics(
    *,
    rank: int,
    metrics: dict[str, Decimal | str | tuple[str, ...]],
) -> ResearchStrategyCostWeightedSignalRouterRow:
    return ResearchStrategyCostWeightedSignalRouterRow(
        rank=_decimal_count(rank),
        signal_strength=_metric_decimal(metrics, "signal_strength"),
        signal_confidence=_metric_decimal(metrics, "signal_confidence"),
        source_quorum_score=_metric_decimal(metrics, "source_quorum_score"),
        raw_signal_score=_metric_decimal(metrics, "raw_signal_score"),
        cost_drag=_metric_decimal(metrics, "cost_drag"),
        cost_drag_penalty=_metric_decimal(metrics, "cost_drag_penalty"),
        source_staleness=_metric_decimal(metrics, "source_staleness"),
        staleness_penalty=_metric_decimal(metrics, "staleness_penalty"),
        router_score=_metric_decimal(metrics, "router_score"),
        router_status=_metric_status(metrics, "router_status"),
        reason_codes=_metric_reason_codes(metrics, "reason_codes"),
    )


def _row_status(
    *,
    router_score: Decimal,
    cost_drag: Decimal,
    config: ResearchStrategyCostWeightedSignalRouterConfig,
) -> str:
    if (
        router_score >= config.pass_min_router_score
        and cost_drag < config.block_min_cost_drag
    ):
        return "pass"
    if router_score >= config.watch_min_router_score and cost_drag < config.block_min_cost_drag:
        return "watch"
    return "block"


def _row_reason_codes(
    *,
    router_score: Decimal,
    cost_drag: Decimal,
    staleness_penalty: Decimal,
    router_status: str,
    input_reason_codes: tuple[str, ...],
    config: ResearchStrategyCostWeightedSignalRouterConfig,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    if router_score >= config.pass_min_router_score:
        reason_codes.append("strong_weighted_signal")
    elif router_score >= config.watch_min_router_score:
        reason_codes.append("weighted_signal_watch_band")
    else:
        reason_codes.append("weighted_signal_below_watch_band")

    if router_status == "pass":
        reason_codes.append("cost_weighted_signal_router_pass")
        reason_codes.append("cost_drag_within_router_band")
    elif router_status == "watch":
        reason_codes.append("cost_weighted_signal_router_watch")
        reason_codes.append("cost_drag_watch_band")
    else:
        reason_codes.append("cost_weighted_signal_router_block")
        reason_codes.append(
            "cost_drag_above_block_band"
            if cost_drag >= config.block_min_cost_drag
            else "cost_drag_watch_band",
        )

    if staleness_penalty > ZERO:
        reason_codes.append("source_freshness_penalty_applied")
    for reason_code in input_reason_codes:
        reason_codes.append(f"input_{reason_code}")
    return tuple(sorted(set(reason_codes)))


def _summary_reason_codes(
    rows: tuple[ResearchStrategyCostWeightedSignalRouterRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return ("empty_signal_router_samples",)
    if all(row.router_status == "pass" for row in rows):
        return ("cost_weighted_signal_router_pass",)
    return tuple(sorted({reason_code for row in rows for reason_code in row.reason_codes}))


def _summary_status(rows: tuple[ResearchStrategyCostWeightedSignalRouterRow, ...]) -> str:
    if not rows:
        return "block"
    if all(row.router_status == "pass" for row in rows):
        return "pass"
    if all(row.router_status == "block" for row in rows):
        return "block"
    return "watch"


def _reason_code_counts(
    rows: tuple[ResearchStrategyCostWeightedSignalRouterRow, ...],
    reason_codes: tuple[str, ...],
) -> tuple[ResearchStrategyCostWeightedSignalRouterReasonCodeCount, ...]:
    if not rows:
        return (
            ResearchStrategyCostWeightedSignalRouterReasonCodeCount(
                reason_code=reason_codes[0],
                count=ONE,
            ),
        )
    counts: Counter[str] = Counter()
    for row in rows:
        counts.update(row.reason_codes)
    return tuple(
        ResearchStrategyCostWeightedSignalRouterReasonCodeCount(
            reason_code=reason_code,
            count=_decimal_count(count),
        )
        for reason_code, count in sorted(counts.items(), key=lambda item: item[0])
    )


def _status_count(
    rows: tuple[ResearchStrategyCostWeightedSignalRouterRow, ...],
    status: str,
) -> int:
    return sum(1 for row in rows if row.router_status == status)


def _average_router_score(
    rows: tuple[ResearchStrategyCostWeightedSignalRouterRow, ...],
) -> Decimal | None:
    if not rows:
        return None
    return _quantize(sum((row.router_score for row in rows), ZERO) / Decimal(len(rows)))


def _average_cost_drag(
    rows: tuple[ResearchStrategyCostWeightedSignalRouterRow, ...],
) -> Decimal | None:
    if not rows:
        return None
    return _quantize(sum((row.cost_drag for row in rows), ZERO) / Decimal(len(rows)))


def _normalize_rows(
    rows: tuple[ResearchStrategyCostWeightedSignalRouterRow, ...],
) -> tuple[ResearchStrategyCostWeightedSignalRouterRow, ...]:
    if type(rows) is not tuple:
        raise ValueError("rows must be a tuple")
    for row in rows:
        if type(row) is not ResearchStrategyCostWeightedSignalRouterRow:
            raise ValueError(
                "rows must contain ResearchStrategyCostWeightedSignalRouterRow values",
            )
        _require_hard_flags("row", row)
    expected_ranks = tuple(_decimal_count(index + 1) for index in range(len(rows)))
    if tuple(row.rank for row in rows) != expected_ranks:
        raise ValueError("rows must be ranked sequentially")
    sorted_rows = tuple(
        sorted(rows, key=lambda row: (-row.router_score, row.cost_drag, row.rank)),
    )
    if rows != sorted_rows:
        raise ValueError("rows must be sorted by router score")
    return rows


def _normalize_reason_code_counts(
    rows: tuple[ResearchStrategyCostWeightedSignalRouterReasonCodeCount, ...],
) -> tuple[ResearchStrategyCostWeightedSignalRouterReasonCodeCount, ...]:
    if type(rows) is not tuple:
        raise ValueError("reason_code_counts must be a tuple")
    for row in rows:
        if type(row) is not ResearchStrategyCostWeightedSignalRouterReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "ResearchStrategyCostWeightedSignalRouterReasonCodeCount values",
            )
        _require_hard_flags("reason_code_count", row)
    sorted_rows = tuple(sorted(rows, key=lambda row: row.reason_code))
    if rows != sorted_rows:
        raise ValueError("reason_code_counts must be sorted by reason_code")
    return rows


def _validate_row_consistency(row: ResearchStrategyCostWeightedSignalRouterRow) -> None:
    if row.raw_signal_score != row.signal_strength:
        raise ValueError("raw_signal_score must match signal_strength")
    expected_router_score = _quantize(
        row.raw_signal_score - row.cost_drag_penalty - row.staleness_penalty,
    )
    if row.router_score != expected_router_score:
        raise ValueError("router_score must match signal score and penalties")
    required_reason_code = f"cost_weighted_signal_router_{row.router_status}"
    if required_reason_code not in row.reason_codes:
        raise ValueError("row reason_codes must include router status reason code")


def _validate_report_consistency(
    report: ResearchStrategyCostWeightedSignalRouterReport,
) -> None:
    if report.sample_count != _decimal_count(len(report.rows)):
        raise ValueError("sample_count must match rows")
    if report.pass_count != _decimal_count(_status_count(report.rows, "pass")):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _decimal_count(_status_count(report.rows, "watch")):
        raise ValueError("watch_count must match rows")
    if report.block_count != _decimal_count(_status_count(report.rows, "block")):
        raise ValueError("block_count must match rows")
    if report.router_status != _summary_status(report.rows):
        raise ValueError("router_status must match row statuses")
    if report.average_router_score != _average_router_score(report.rows):
        raise ValueError("average_router_score must match rows")
    if report.average_cost_drag != _average_cost_drag(report.rows):
        raise ValueError("average_cost_drag must match rows")
    expected_top = report.rows[0].router_score if report.rows else None
    if report.top_router_score != expected_top:
        raise ValueError("top_router_score must match rows")
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
    _validate_public_status_fields(payload)
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


def _validate_public_status_fields(value: object) -> None:
    if type(value) is dict:
        for key, item in value.items():
            if key == "router_status":
                _require_status("router_status", item)
            _validate_public_status_fields(item)
        return
    if type(value) in (tuple, list):
        for item in value:
            _validate_public_status_fields(item)


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
            normalized_key = key.lower()
            if any(fragment in normalized_key for fragment in UNSAFE_PUBLIC_SURFACE_FRAGMENTS):
                raise ValueError(f"unsafe public surface in {label}: {key}")
            _reject_unsafe_public_payload(label, item)
        return
    if type(value) in (tuple, list):
        for item in value:
            _reject_unsafe_public_payload(label, item)
        return
    if type(value) is str:
        normalized_value = value.lower()
        if any(fragment in normalized_value for fragment in UNSAFE_PUBLIC_SURFACE_FRAGMENTS):
            raise ValueError(f"unsafe public surface in {label}")


def _report_values_without_digest(
    report: ResearchStrategyCostWeightedSignalRouterReport,
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
