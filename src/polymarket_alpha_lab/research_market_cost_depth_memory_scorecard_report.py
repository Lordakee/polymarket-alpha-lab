"""Pure cost/depth/memory scorecard report for paper research review."""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable
from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
import json
from typing import Any


__all__ = (
    "DEFAULT_RESEARCH_MARKET_COST_DEPTH_MEMORY_SCORECARD_CONFIG_VERSION",
    "MarketCostDepthMemoryScorecardConfig",
    "MarketCostDepthMemoryScorecardInput",
    "MarketCostDepthMemoryScorecardReasonCodeCount",
    "MarketCostDepthMemoryScorecardReport",
    "MarketCostDepthMemoryScorecardRow",
    "build_research_market_cost_depth_memory_scorecard_report",
    "research_market_cost_depth_memory_scorecard_report_payload",
)


DEFAULT_RESEARCH_MARKET_COST_DEPTH_MEMORY_SCORECARD_CONFIG_VERSION = (
    "research-market-cost-depth-memory-scorecard-report-v0"
)

QUANTUM = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
PASS_COMPONENT_SCORE = Decimal("0.900000")
WATCH_COMPONENT_SCORE = Decimal("0.650000")
BLOCK_COMPONENT_SCORE = Decimal("0.350000")
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
STATUSES = ("pass", "watch", "block")
STATUS_SORT_WEIGHT = {"block": 0, "watch": 1, "pass": 2}
HEX_CHARS = frozenset("0123456789abcdef")


def _unsafe_term(*parts: str) -> str:
    return "".join(parts)


UNSAFE_PUBLIC_TEXT_FRAGMENTS = (
    _unsafe_term("a", "u", "t", "h"),
    "candidate",
    "candidate_id",
    "dsn",
    "http",
    "identifier",
    "key",
    _unsafe_term("l", "i", "v", "e"),
    "market_id",
    "market_slug",
    "market_url",
    _unsafe_term("o", "r", "d", "e", "r"),
    "position",
    "private",
    "question",
    "raw_text",
    _unsafe_term("r", "e", "c", "o", "m", "m", "e", "n", "d"),
    "sell",
    _unsafe_term("s", "i", "z", "i", "n", "g"),
    "slug",
    "source",
    "table",
    "token",
    _unsafe_term("t", "r", "a", "d", "e"),
    "url",
    _unsafe_term("w", "a", "l", "l", "e", "t"),
)
REPORT_REASON_PRIORITY = (
    "market_cost_depth_memory_scorecard_cost_block",
    "market_cost_depth_memory_scorecard_depth_block",
    "market_cost_depth_memory_scorecard_confidence_block",
    "market_cost_depth_memory_scorecard_recency_block",
    "market_cost_depth_memory_scorecard_readiness_block",
    "market_cost_depth_memory_scorecard_cost_watch",
    "market_cost_depth_memory_scorecard_depth_watch",
    "market_cost_depth_memory_scorecard_confidence_watch",
    "market_cost_depth_memory_scorecard_recency_watch",
    "market_cost_depth_memory_scorecard_readiness_watch",
)
SUMMARY_EXPLANATION_BY_STATUS = {
    "pass": "pass: cost/depth/memory scorecard inputs are sufficient for paper review",
    "watch": (
        "watch: cost/depth/memory scorecard inputs need manual review "
        "before paper review"
    ),
    "block": (
        "block: cost/depth/memory scorecard inputs are not sufficient "
        "for paper review"
    ),
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
class MarketCostDepthMemoryScorecardConfig(_FinalPublicDataclass):
    config_version: str = (
        DEFAULT_RESEARCH_MARKET_COST_DEPTH_MEMORY_SCORECARD_CONFIG_VERSION
    )
    max_pass_cost_rate: Decimal = Decimal("0.025000")
    max_watch_cost_rate: Decimal = Decimal("0.060000")
    min_pass_depth_score: Decimal = Decimal("0.700000")
    min_watch_depth_score: Decimal = Decimal("0.450000")
    min_pass_memory_confidence_score: Decimal = Decimal("0.750000")
    min_watch_memory_confidence_score: Decimal = Decimal("0.500000")
    min_pass_memory_recency_score: Decimal = Decimal("0.700000")
    min_watch_memory_recency_score: Decimal = Decimal("0.450000")
    pass_min_scorecard_score: Decimal = Decimal("0.850000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, MarketCostDepthMemoryScorecardConfig, "config")
        if (
            self.config_version
            != DEFAULT_RESEARCH_MARKET_COST_DEPTH_MEMORY_SCORECARD_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "max_pass_cost_rate",
            "max_watch_cost_rate",
            "min_pass_depth_score",
            "min_watch_depth_score",
            "min_pass_memory_confidence_score",
            "min_watch_memory_confidence_score",
            "min_pass_memory_recency_score",
            "min_watch_memory_recency_score",
            "pass_min_scorecard_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        if self.max_watch_cost_rate < self.max_pass_cost_rate:
            raise ValueError("max_watch_cost_rate must be at least max_pass_cost_rate")
        if self.min_pass_depth_score < self.min_watch_depth_score:
            raise ValueError(
                "min_pass_depth_score must be at least min_watch_depth_score",
            )
        if (
            self.min_pass_memory_confidence_score
            < self.min_watch_memory_confidence_score
        ):
            raise ValueError(
                "min_pass_memory_confidence_score must be at least "
                "min_watch_memory_confidence_score",
            )
        if self.min_pass_memory_recency_score < self.min_watch_memory_recency_score:
            raise ValueError(
                "min_pass_memory_recency_score must be at least "
                "min_watch_memory_recency_score",
            )
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class MarketCostDepthMemoryScorecardInput(_FinalPublicDataclass):
    cost_rate: Decimal
    depth_score: Decimal
    memory_confidence_score: Decimal
    memory_recency_score: Decimal
    observed_at: datetime
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, MarketCostDepthMemoryScorecardInput, "input")
        for field_name in (
            "cost_rate",
            "depth_score",
            "memory_confidence_score",
            "memory_recency_score",
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
class MarketCostDepthMemoryScorecardRow(_FinalPublicDataclass):
    row_index: Decimal
    cost_rate: Decimal
    depth_score: Decimal
    memory_confidence_score: Decimal
    memory_recency_score: Decimal
    scorecard_score: Decimal
    observed_at: datetime
    status: str
    status_explanation: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, MarketCostDepthMemoryScorecardRow, "row")
        object.__setattr__(
            self,
            "row_index",
            _require_positive_decimal("row_index", self.row_index),
        )
        for field_name in (
            "cost_rate",
            "depth_score",
            "memory_confidence_score",
            "memory_recency_score",
            "scorecard_score",
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
class MarketCostDepthMemoryScorecardReasonCodeCount(_FinalPublicDataclass):
    reason_code: str
    count: Decimal
    input_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, MarketCostDepthMemoryScorecardReasonCodeCount, "count")
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
class MarketCostDepthMemoryScorecardReport(_FinalPublicDataclass):
    generated_at: datetime
    config_version: str
    input_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    max_cost_rate: Decimal
    min_depth_score: Decimal
    min_memory_confidence_score: Decimal
    min_memory_recency_score: Decimal
    min_scorecard_score: Decimal
    status: str
    summary_explanation: str
    reason_codes: tuple[str, ...]
    reason_code_counts: tuple[MarketCostDepthMemoryScorecardReasonCodeCount, ...]
    rows: tuple[MarketCostDepthMemoryScorecardRow, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, MarketCostDepthMemoryScorecardReport, "report")
        object.__setattr__(
            self,
            "generated_at",
            _as_utc("generated_at", self.generated_at),
        )
        if (
            self.config_version
            != DEFAULT_RESEARCH_MARKET_COST_DEPTH_MEMORY_SCORECARD_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in ("input_count", "pass_count", "watch_count", "block_count"):
            object.__setattr__(
                self,
                field_name,
                _require_count_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "max_cost_rate",
            "min_depth_score",
            "min_memory_confidence_score",
            "min_memory_recency_score",
            "min_scorecard_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
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
            _require_matching_digest(
                "derived_validation_digest",
                self.derived_validation_digest,
                _report_payload_core(self, include_digest=False),
            )
        else:
            object.__setattr__(
                self,
                "derived_validation_digest",
                _digest_payload(_report_payload_core(self, include_digest=False)),
            )


def build_research_market_cost_depth_memory_scorecard_report(
    inputs: Iterable[MarketCostDepthMemoryScorecardInput],
    *,
    config: MarketCostDepthMemoryScorecardConfig,
    generated_at: datetime,
) -> MarketCostDepthMemoryScorecardReport:
    if type(config) is not MarketCostDepthMemoryScorecardConfig:
        raise ValueError("config must be a MarketCostDepthMemoryScorecardConfig")
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
    return MarketCostDepthMemoryScorecardReport(
        generated_at=generated_at,
        config_version=config.config_version,
        input_count=_count_decimal(len(normalized_inputs)),
        pass_count=_status_count(rows, "pass"),
        watch_count=_status_count(rows, "watch"),
        block_count=_status_count(rows, "block"),
        max_cost_rate=_max_row_decimal(rows, "cost_rate"),
        min_depth_score=_min_row_decimal(rows, "depth_score"),
        min_memory_confidence_score=_min_row_decimal(
            rows,
            "memory_confidence_score",
        ),
        min_memory_recency_score=_min_row_decimal(rows, "memory_recency_score"),
        min_scorecard_score=_min_row_decimal(rows, "scorecard_score"),
        status=status,
        summary_explanation=_summary_explanation(status, has_rows=bool(rows)),
        reason_codes=_report_reason_codes(rows, status=status),
        reason_code_counts=_reason_code_counts(rows),
        rows=rows,
    )


def research_market_cost_depth_memory_scorecard_report_payload(
    report: MarketCostDepthMemoryScorecardReport,
) -> dict[str, Any]:
    if type(report) is not MarketCostDepthMemoryScorecardReport:
        raise ValueError("report must be a MarketCostDepthMemoryScorecardReport")
    _require_hard_flags("report", report)
    payload = _report_payload_core(report, include_digest=True)
    _reject_unsafe_payload(payload)
    return payload


def _row_from_input(
    value: MarketCostDepthMemoryScorecardInput,
    *,
    row_index: int,
    config: MarketCostDepthMemoryScorecardConfig,
) -> MarketCostDepthMemoryScorecardRow:
    scorecard_score = _average_decimals(
        (
            _cost_component_score(value.cost_rate, config),
            _minimum_component_score(
                value.depth_score,
                pass_minimum=config.min_pass_depth_score,
                watch_minimum=config.min_watch_depth_score,
            ),
            _minimum_component_score(
                value.memory_confidence_score,
                pass_minimum=config.min_pass_memory_confidence_score,
                watch_minimum=config.min_watch_memory_confidence_score,
            ),
            _minimum_component_score(
                value.memory_recency_score,
                pass_minimum=config.min_pass_memory_recency_score,
                watch_minimum=config.min_watch_memory_recency_score,
            ),
        ),
    )
    status = _row_status(value, scorecard_score=scorecard_score, config=config)
    return MarketCostDepthMemoryScorecardRow(
        row_index=_count_decimal(row_index),
        cost_rate=value.cost_rate,
        depth_score=value.depth_score,
        memory_confidence_score=value.memory_confidence_score,
        memory_recency_score=value.memory_recency_score,
        scorecard_score=scorecard_score,
        observed_at=value.observed_at,
        status=status,
        status_explanation=SUMMARY_EXPLANATION_BY_STATUS[status],
        reason_codes=_row_reason_codes(
            value.reason_codes,
            value,
            scorecard_score=scorecard_score,
            status=status,
            config=config,
        ),
    )


def _row_status(
    value: MarketCostDepthMemoryScorecardInput,
    *,
    scorecard_score: Decimal,
    config: MarketCostDepthMemoryScorecardConfig,
) -> str:
    if (
        value.cost_rate > config.max_watch_cost_rate
        or value.depth_score < config.min_watch_depth_score
        or value.memory_confidence_score < config.min_watch_memory_confidence_score
        or value.memory_recency_score < config.min_watch_memory_recency_score
    ):
        return "block"
    if (
        value.cost_rate > config.max_pass_cost_rate
        or value.depth_score < config.min_pass_depth_score
        or value.memory_confidence_score < config.min_pass_memory_confidence_score
        or value.memory_recency_score < config.min_pass_memory_recency_score
        or scorecard_score < config.pass_min_scorecard_score
    ):
        return "watch"
    return "pass"


def _row_reason_codes(
    upstream_reason_codes: tuple[str, ...],
    value: MarketCostDepthMemoryScorecardInput,
    *,
    scorecard_score: Decimal,
    status: str,
    config: MarketCostDepthMemoryScorecardConfig,
) -> tuple[str, ...]:
    reason_codes = list(upstream_reason_codes)
    if value.cost_rate > config.max_watch_cost_rate:
        reason_codes.append("market_cost_depth_memory_scorecard_cost_block")
    elif value.cost_rate > config.max_pass_cost_rate:
        reason_codes.append("market_cost_depth_memory_scorecard_cost_watch")
    if value.depth_score < config.min_watch_depth_score:
        reason_codes.append("market_cost_depth_memory_scorecard_depth_block")
    elif value.depth_score < config.min_pass_depth_score:
        reason_codes.append("market_cost_depth_memory_scorecard_depth_watch")
    if value.memory_confidence_score < config.min_watch_memory_confidence_score:
        reason_codes.append("market_cost_depth_memory_scorecard_confidence_block")
    elif value.memory_confidence_score < config.min_pass_memory_confidence_score:
        reason_codes.append("market_cost_depth_memory_scorecard_confidence_watch")
    if value.memory_recency_score < config.min_watch_memory_recency_score:
        reason_codes.append("market_cost_depth_memory_scorecard_recency_block")
    elif value.memory_recency_score < config.min_pass_memory_recency_score:
        reason_codes.append("market_cost_depth_memory_scorecard_recency_watch")
    if status == "block":
        reason_codes.append("market_cost_depth_memory_scorecard_readiness_block")
    elif status == "watch":
        reason_codes.append("market_cost_depth_memory_scorecard_readiness_watch")
    elif scorecard_score >= config.pass_min_scorecard_score:
        reason_codes.append("market_cost_depth_memory_scorecard_ready")
    return _normalize_reason_codes("reason_codes", tuple(reason_codes))


def _cost_component_score(
    cost_rate: Decimal,
    config: MarketCostDepthMemoryScorecardConfig,
) -> Decimal:
    return _maximum_component_score(
        cost_rate,
        pass_maximum=config.max_pass_cost_rate,
        watch_maximum=config.max_watch_cost_rate,
    )


def _minimum_component_score(
    value: Decimal,
    *,
    pass_minimum: Decimal,
    watch_minimum: Decimal,
) -> Decimal:
    if value < watch_minimum:
        return BLOCK_COMPONENT_SCORE
    if value < pass_minimum:
        return WATCH_COMPONENT_SCORE
    return PASS_COMPONENT_SCORE


def _maximum_component_score(
    value: Decimal,
    *,
    pass_maximum: Decimal,
    watch_maximum: Decimal,
) -> Decimal:
    if value > watch_maximum:
        return BLOCK_COMPONENT_SCORE
    if value > pass_maximum:
        return WATCH_COMPONENT_SCORE
    return PASS_COMPONENT_SCORE


def _report_status(rows: tuple[MarketCostDepthMemoryScorecardRow, ...]) -> str:
    if not rows:
        return "block"
    if any(row.status == "block" for row in rows):
        return "block"
    if any(row.status == "watch" for row in rows):
        return "watch"
    return "pass"


def _summary_explanation(status: str, *, has_rows: bool) -> str:
    if not has_rows:
        return "block: no cost/depth/memory scorecard inputs supplied for paper review"
    return SUMMARY_EXPLANATION_BY_STATUS[status]


def _report_reason_codes(
    rows: tuple[MarketCostDepthMemoryScorecardRow, ...],
    *,
    status: str,
) -> tuple[str, ...]:
    if not rows:
        return ("market_cost_depth_memory_scorecard_report_empty",)
    generated_reasons = {
        reason_code
        for row in rows
        for reason_code in row.reason_codes
        if reason_code.startswith("market_cost_depth_memory_scorecard_")
    }
    report_reason = f"market_cost_depth_memory_scorecard_report_{status}"
    return (report_reason,) + tuple(
        reason_code
        for reason_code in REPORT_REASON_PRIORITY
        if reason_code in generated_reasons
    )


def _reason_code_counts(
    rows: tuple[MarketCostDepthMemoryScorecardRow, ...],
) -> tuple[MarketCostDepthMemoryScorecardReasonCodeCount, ...]:
    if not rows:
        return ()
    counts: Counter[str] = Counter(
        reason_code for row in rows for reason_code in row.reason_codes
    )
    denominator = _count_decimal(len(rows))
    return tuple(
        MarketCostDepthMemoryScorecardReasonCodeCount(
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
    report: MarketCostDepthMemoryScorecardReport,
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
        "max_cost_rate": _decimal_to_string(report.max_cost_rate),
        "min_depth_score": _decimal_to_string(report.min_depth_score),
        "min_memory_confidence_score": _decimal_to_string(
            report.min_memory_confidence_score,
        ),
        "min_memory_recency_score": _decimal_to_string(
            report.min_memory_recency_score,
        ),
        "min_scorecard_score": _decimal_to_string(report.min_scorecard_score),
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


def _row_payload(row: MarketCostDepthMemoryScorecardRow) -> dict[str, Any]:
    return {
        "row_index": _decimal_to_string(row.row_index),
        "cost_rate": _decimal_to_string(row.cost_rate),
        "depth_score": _decimal_to_string(row.depth_score),
        "memory_confidence_score": _decimal_to_string(row.memory_confidence_score),
        "memory_recency_score": _decimal_to_string(row.memory_recency_score),
        "scorecard_score": _decimal_to_string(row.scorecard_score),
        "observed_at": row.observed_at.isoformat(),
        "status": row.status,
        "status_explanation": row.status_explanation,
        "reason_codes": list(row.reason_codes),
        "paper_only": row.paper_only,
        "report_only": row.report_only,
        "readonly": row.readonly,
    }


def _reason_code_count_payload(
    reason_count: MarketCostDepthMemoryScorecardReasonCodeCount,
) -> dict[str, Any]:
    return {
        "reason_code": reason_count.reason_code,
        "count": _decimal_to_string(reason_count.count),
        "input_ratio": _decimal_to_string(reason_count.input_ratio),
        "paper_only": reason_count.paper_only,
        "report_only": reason_count.report_only,
        "readonly": reason_count.readonly,
    }


def _digest_payload(payload: dict[str, Any]) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return sha256(encoded.encode("utf-8")).hexdigest()


def _normalize_inputs(
    inputs: Iterable[MarketCostDepthMemoryScorecardInput],
) -> tuple[MarketCostDepthMemoryScorecardInput, ...]:
    if isinstance(inputs, (str, bytes)) or type(inputs) is dict:
        raise ValueError("inputs must be an iterable of MarketCostDepthMemoryScorecardInput")
    try:
        values = tuple(inputs)
    except TypeError as exc:
        raise ValueError(
            "inputs must be an iterable of MarketCostDepthMemoryScorecardInput",
        ) from exc
    for value in values:
        if type(value) is not MarketCostDepthMemoryScorecardInput:
            raise ValueError("inputs must contain MarketCostDepthMemoryScorecardInput")
        _require_hard_flags("inputs", value)
    return values


def _normalize_rows(
    rows: tuple[MarketCostDepthMemoryScorecardRow, ...],
) -> tuple[MarketCostDepthMemoryScorecardRow, ...]:
    if type(rows) is not tuple:
        raise ValueError("rows must be a tuple")
    for row in rows:
        if type(row) is not MarketCostDepthMemoryScorecardRow:
            raise ValueError("rows must contain MarketCostDepthMemoryScorecardRow")
        _require_hard_flags("rows", row)
    return tuple(sorted(rows, key=_row_sort_key))


def _normalize_reason_code_counts(
    reason_code_counts: tuple[MarketCostDepthMemoryScorecardReasonCodeCount, ...],
) -> tuple[MarketCostDepthMemoryScorecardReasonCodeCount, ...]:
    if type(reason_code_counts) is not tuple:
        raise ValueError("reason_code_counts must be a tuple")
    for reason_count in reason_code_counts:
        if type(reason_count) is not MarketCostDepthMemoryScorecardReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "MarketCostDepthMemoryScorecardReasonCodeCount",
            )
        _require_hard_flags("reason_code_counts", reason_count)
    return tuple(
        sorted(reason_code_counts, key=lambda item: (-item.count, item.reason_code)),
    )


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
    return tuple(normalized_items)


def _normalize_sorted_reason_codes(
    field_name: str,
    value: tuple[str, ...],
) -> tuple[str, ...]:
    return tuple(sorted(_normalize_reason_codes(field_name, value)))


def _validate_row_consistency(row: MarketCostDepthMemoryScorecardRow) -> None:
    expected_reason = {
        "pass": "market_cost_depth_memory_scorecard_ready",
        "watch": "market_cost_depth_memory_scorecard_readiness_watch",
        "block": "market_cost_depth_memory_scorecard_readiness_block",
    }[row.status]
    if expected_reason not in row.reason_codes:
        raise ValueError("status must match reason_codes")
    if row.status_explanation != SUMMARY_EXPLANATION_BY_STATUS[row.status]:
        raise ValueError("status_explanation must match status")


def _validate_report_consistency(
    report: MarketCostDepthMemoryScorecardReport,
) -> None:
    rows = report.rows
    input_count = _count_decimal(len(rows))
    if report.input_count != input_count:
        raise ValueError("input_count must match rows")
    for field_name, status in (
        ("pass_count", "pass"),
        ("watch_count", "watch"),
        ("block_count", "block"),
    ):
        if getattr(report, field_name) != _status_count(rows, status):
            raise ValueError(f"{field_name} must match rows")
    if report.pass_count + report.watch_count + report.block_count != input_count:
        raise ValueError("status counts must match input_count")
    if report.max_cost_rate != _max_row_decimal(rows, "cost_rate"):
        raise ValueError("max_cost_rate must match rows")
    if report.min_depth_score != _min_row_decimal(rows, "depth_score"):
        raise ValueError("min_depth_score must match rows")
    if report.min_memory_confidence_score != _min_row_decimal(
        rows,
        "memory_confidence_score",
    ):
        raise ValueError("min_memory_confidence_score must match rows")
    if report.min_memory_recency_score != _min_row_decimal(
        rows,
        "memory_recency_score",
    ):
        raise ValueError("min_memory_recency_score must match rows")
    if report.min_scorecard_score != _min_row_decimal(rows, "scorecard_score"):
        raise ValueError("min_scorecard_score must match rows")
    if report.status != _report_status(rows):
        raise ValueError("status must match rows")
    if report.summary_explanation != _summary_explanation(
        report.status,
        has_rows=bool(rows),
    ):
        raise ValueError("summary_explanation must match status")
    if report.reason_codes != _report_reason_codes(rows, status=report.status):
        raise ValueError("reason_codes must match rows")
    if report.reason_code_counts != _reason_code_counts(rows):
        raise ValueError("reason_code_counts must match rows")


def _row_sort_key(row: MarketCostDepthMemoryScorecardRow) -> tuple[Decimal, Decimal]:
    return (Decimal(STATUS_SORT_WEIGHT[row.status]), row.row_index)


def _status_count(
    rows: tuple[MarketCostDepthMemoryScorecardRow, ...],
    status: str,
) -> Decimal:
    return _count_decimal(sum(1 for row in rows if row.status == status))


def _max_row_decimal(
    rows: tuple[MarketCostDepthMemoryScorecardRow, ...],
    field_name: str,
) -> Decimal:
    return max((getattr(row, field_name) for row in rows), default=ZERO)


def _min_row_decimal(
    rows: tuple[MarketCostDepthMemoryScorecardRow, ...],
    field_name: str,
) -> Decimal:
    return min((getattr(row, field_name) for row in rows), default=ZERO)


def _average_decimals(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return ZERO
    return _divide_decimal(_sum_decimals(values), _count_decimal(len(values)))


def _sum_decimals(values: tuple[Decimal, ...]) -> Decimal:
    return _quantize(sum(values, ZERO))


def _divide_decimal(left: Decimal, right: Decimal) -> Decimal:
    if right == ZERO:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return _quantize(left / right)


def _count_decimal(value: int) -> Decimal:
    return _quantize(Decimal(value))


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_reason_code(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must contain strings")
    if value == "" or value != value.strip():
        raise ValueError(f"{field_name} must be canonical")
    if not all(
        character.islower() or character.isdigit() or character == "_"
        for character in value
    ):
        raise ValueError(f"{field_name} must be lower snake case")
    _require_safe_public_text(field_name, value)
    return value


def _require_safe_public_text(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if value == "":
        raise ValueError(f"{field_name} must not be empty")
    if value != value.strip():
        raise ValueError(f"{field_name} must be canonical")
    if any(ord(character) < 32 for character in value):
        raise ValueError(f"{field_name} must not contain control characters")
    normalized = value.lower()
    if any(fragment in normalized for fragment in UNSAFE_PUBLIC_TEXT_FRAGMENTS):
        raise ValueError(f"{field_name} contains unsafe public surface")
    return value


def _require_status(field_name: str, value: object) -> str:
    if type(value) is not str or value not in STATUSES:
        raise ValueError(f"{field_name} must be pass, watch, or block")
    return value


def _require_exact_type(value: object, expected_type: type[object], label: str) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{label} must be exactly {expected_type.__name__}")


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if getattr(value, field_name, None) is not True:
            raise ValueError(f"{label} {field_name} must be True")


def _require_ratio_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _normalize_decimal(field_name, value)
    if decimal_value < ZERO or decimal_value > ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return decimal_value


def _require_positive_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_nonnegative_decimal(field_name, value)
    if decimal_value <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return decimal_value


def _require_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _normalize_decimal(field_name, value)
    if decimal_value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return decimal_value


def _require_count_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_nonnegative_decimal(field_name, value)
    if decimal_value != decimal_value.to_integral_value():
        raise ValueError(f"{field_name} must be a whole Decimal")
    return decimal_value


def _normalize_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return _quantize(value)


def _quantize(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(QUANTUM)


def _decimal_to_string(value: Decimal) -> str:
    return format(_quantize(value), "f")


def _require_matching_digest(
    field_name: str,
    value: object,
    payload: dict[str, Any],
) -> str:
    digest = _require_digest(field_name, value)
    if digest != _digest_payload(payload):
        raise ValueError(f"{field_name} must match report payload")
    return digest


def _require_digest(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if len(value) != 64 or any(character not in HEX_CHARS for character in value):
        raise ValueError(f"{field_name} must be a sha256 digest")
    return value


def _reject_unsafe_payload(value: object) -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            _require_safe_public_text("payload key", key)
            _reject_unsafe_payload(item)
    elif isinstance(value, list):
        for item in value:
            _reject_unsafe_payload(item)
    elif type(value) is str:
        _require_safe_public_text("payload value", value)
    elif isinstance(value, bool):
        return
    elif value is None:
        return
    elif isinstance(value, (Decimal, int, float)):
        raise ValueError("payload must expose Decimal strings, not numeric values")
