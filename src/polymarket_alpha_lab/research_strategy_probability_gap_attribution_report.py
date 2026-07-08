"""Pure report-only probability gap attribution reducer."""

from __future__ import annotations

from collections import Counter
from collections.abc import Sequence
from dataclasses import asdict, dataclass, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
import hashlib
import json
import re
from typing import Any


DEFAULT_RESEARCH_STRATEGY_PROBABILITY_GAP_ATTRIBUTION_REPORT_CONFIG_VERSION = (
    "research-strategy-probability-gap-attribution-report-v0"
)

__all__ = (
    "DEFAULT_RESEARCH_STRATEGY_PROBABILITY_GAP_ATTRIBUTION_REPORT_CONFIG_VERSION",
    "ResearchStrategyProbabilityGapAttributionConfig",
    "ResearchStrategyProbabilityGapAttributionInput",
    "ResearchStrategyProbabilityGapAttributionReasonCodeCount",
    "ResearchStrategyProbabilityGapAttributionReport",
    "ResearchStrategyProbabilityGapAttributionRow",
    "build_research_strategy_probability_gap_attribution_report",
    "research_strategy_probability_gap_attribution_digest",
    "research_strategy_probability_gap_attribution_digest_payload",
    "research_strategy_probability_gap_attribution_report_payload",
)


PASS_STATUS = "pass"
WATCH_STATUS = "watch"
BLOCK_STATUS = "block"
STATUSES = (PASS_STATUS, WATCH_STATUS, BLOCK_STATUS)
STATUS_SEVERITY = {
    BLOCK_STATUS: Decimal("0.000000"),
    WATCH_STATUS: Decimal("1.000000"),
    PASS_STATUS: Decimal("2.000000"),
}
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
QUANTUM = Decimal("0.000001")
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
DIGEST_RE = re.compile("^[0-9a-f]{64}$")

MISSING_INPUTS_REASON = "probability_gap_attribution_missing_inputs"
REASON_CODE_SEQUENCE = (
    MISSING_INPUTS_REASON,
    "probability_gap_attribution_block",
    "probability_gap_attribution_watch",
    "probability_gap_attribution_pass",
    "gap_magnitude_block",
    "gap_magnitude_watch",
    "evidence_driver_block",
    "evidence_driver_watch",
    "cost_driver_block",
    "cost_driver_watch",
    "settlement_driver_block",
    "settlement_driver_watch",
    "domain_memory_driver_block",
    "domain_memory_driver_watch",
)
DRIVER_NAMES = (
    "evidence",
    "cost",
    "settlement",
    "domain_memory",
)
GAP_DIRECTIONS = (
    "forecast_above_benchmark",
    "forecast_below_benchmark",
    "forecast_matches_benchmark",
)


@dataclass(frozen=True)
class ResearchStrategyProbabilityGapAttributionConfig:
    config_version: str = (
        DEFAULT_RESEARCH_STRATEGY_PROBABILITY_GAP_ATTRIBUTION_REPORT_CONFIG_VERSION
    )
    watch_probability_gap: Decimal = Decimal("0.100000")
    block_probability_gap: Decimal = Decimal("0.250000")
    watch_driver_score: Decimal = Decimal("0.400000")
    block_driver_score: Decimal = Decimal("0.650000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchStrategyProbabilityGapAttributionConfig:
            raise TypeError(
                "ResearchStrategyProbabilityGapAttributionConfig does not support "
                "subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchStrategyProbabilityGapAttributionConfig,
            "config",
        )
        _require_supported_config_version(self.config_version)
        for field_name in (
            "watch_probability_gap",
            "block_probability_gap",
            "watch_driver_score",
            "block_driver_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_probability_decimal(field_name, getattr(self, field_name)),
            )
        _require_less_than(
            "watch_probability_gap",
            self.watch_probability_gap,
            "block_probability_gap",
            self.block_probability_gap,
        )
        _require_less_than(
            "watch_driver_score",
            self.watch_driver_score,
            "block_driver_score",
            self.block_driver_score,
        )
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class ResearchStrategyProbabilityGapAttributionInput:
    forecast_probability: Decimal
    benchmark_probability: Decimal
    observed_at: datetime
    evidence_driver_score: Decimal
    cost_driver_score: Decimal
    settlement_driver_score: Decimal
    domain_memory_driver_score: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchStrategyProbabilityGapAttributionInput:
            raise TypeError(
                "ResearchStrategyProbabilityGapAttributionInput does not support "
                "subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchStrategyProbabilityGapAttributionInput,
            "input",
        )
        for field_name in (
            "forecast_probability",
            "benchmark_probability",
            "evidence_driver_score",
            "cost_driver_score",
            "settlement_driver_score",
            "domain_memory_driver_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_probability_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        _require_hard_flags("input", self)


@dataclass(frozen=True)
class ResearchStrategyProbabilityGapAttributionRow:
    rank: Decimal
    observed_at: datetime
    forecast_probability: Decimal
    benchmark_probability: Decimal
    probability_gap_abs: Decimal
    probability_gap_direction: str
    evidence_driver_score: Decimal
    cost_driver_score: Decimal
    settlement_driver_score: Decimal
    domain_memory_driver_score: Decimal
    dominant_driver: str
    dominant_driver_score: Decimal
    attribution_pressure: Decimal
    status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchStrategyProbabilityGapAttributionRow:
            raise TypeError(
                "ResearchStrategyProbabilityGapAttributionRow does not support "
                "subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchStrategyProbabilityGapAttributionRow, "row")
        object.__setattr__(self, "rank", _require_nonnegative_decimal("rank", self.rank))
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in (
            "forecast_probability",
            "benchmark_probability",
            "probability_gap_abs",
            "evidence_driver_score",
            "cost_driver_score",
            "settlement_driver_score",
            "domain_memory_driver_score",
            "dominant_driver_score",
            "attribution_pressure",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_probability_decimal(field_name, getattr(self, field_name)),
            )
        _require_direction(self.probability_gap_direction)
        _require_driver_name(self.dominant_driver)
        _require_status(self.status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(
                "reason_codes",
                self.reason_codes,
                allow_empty=False,
            ),
        )
        _require_hard_flags("row", self)
        _validate_row_consistency(self)


@dataclass(frozen=True)
class ResearchStrategyProbabilityGapAttributionReasonCodeCount:
    reason_code: str
    count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchStrategyProbabilityGapAttributionReasonCodeCount:
            raise TypeError(
                "ResearchStrategyProbabilityGapAttributionReasonCodeCount does not "
                "support subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchStrategyProbabilityGapAttributionReasonCodeCount,
            "reason_count",
        )
        object.__setattr__(self, "reason_code", _require_reason_code(self.reason_code))
        object.__setattr__(
            self,
            "count",
            _require_nonnegative_decimal("count", self.count),
        )
        _require_hard_flags("reason_count", self)


@dataclass(frozen=True)
class ResearchStrategyProbabilityGapAttributionReport:
    generated_at: datetime
    config_version: str
    status: str
    attribution_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    average_forecast_probability: Decimal
    average_benchmark_probability: Decimal
    average_probability_gap_abs: Decimal
    average_evidence_driver_score: Decimal
    average_cost_driver_score: Decimal
    average_settlement_driver_score: Decimal
    average_domain_memory_driver_score: Decimal
    dominant_driver: str
    dominant_driver_score: Decimal
    max_attribution_pressure: Decimal
    rows: tuple[ResearchStrategyProbabilityGapAttributionRow, ...]
    reason_code_counts: tuple[
        ResearchStrategyProbabilityGapAttributionReasonCodeCount,
        ...,
    ]
    reason_codes: tuple[str, ...]
    public_payload_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchStrategyProbabilityGapAttributionReport:
            raise TypeError(
                "ResearchStrategyProbabilityGapAttributionReport does not support "
                "subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchStrategyProbabilityGapAttributionReport,
            "report",
        )
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_supported_config_version(self.config_version)
        _require_status(self.status)
        for field_name in (
            "attribution_count",
            "pass_count",
            "watch_count",
            "block_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "average_forecast_probability",
            "average_benchmark_probability",
            "average_probability_gap_abs",
            "average_evidence_driver_score",
            "average_cost_driver_score",
            "average_settlement_driver_score",
            "average_domain_memory_driver_score",
            "dominant_driver_score",
            "max_attribution_pressure",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_probability_decimal(field_name, getattr(self, field_name)),
            )
        _require_driver_name(self.dominant_driver)
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(
                "reason_codes",
                self.reason_codes,
                allow_empty=False,
            ),
        )
        _require_digest_or_empty(self.public_payload_digest)
        _require_hard_flags("report", self)
        expected_digest = _public_digest_from_values(_report_values_without_digest(self))
        if self.public_payload_digest:
            if self.public_payload_digest != expected_digest:
                raise ValueError("public_payload_digest must match report payload")
        else:
            object.__setattr__(self, "public_payload_digest", expected_digest)
        _validate_report_consistency(self)


def build_research_strategy_probability_gap_attribution_report(
    inputs: Sequence[ResearchStrategyProbabilityGapAttributionInput],
    *,
    generated_at: datetime,
    config: ResearchStrategyProbabilityGapAttributionConfig | None = None,
) -> ResearchStrategyProbabilityGapAttributionReport:
    if config is None:
        config = ResearchStrategyProbabilityGapAttributionConfig()
    if type(config) is not ResearchStrategyProbabilityGapAttributionConfig:
        raise ValueError(
            "config must be ResearchStrategyProbabilityGapAttributionConfig",
        )
    _require_hard_flags("config", config)
    generated_at = _as_utc("generated_at", generated_at)
    items = _normalize_inputs(inputs)
    for item in items:
        if item.observed_at > generated_at:
            raise ValueError("observed_at must not be after generated_at")
    rows = _rank_rows(tuple(_row_from_input(item, config) for item in items))
    averages = _driver_averages(rows)
    dominant_driver, dominant_driver_score = _dominant_from_named_values(averages)
    reason_codes = _report_reason_codes(rows)
    values: dict[str, object] = {
        "generated_at": generated_at,
        "config_version": config.config_version,
        "status": _report_status(rows),
        "attribution_count": _decimal_count(len(rows)),
        "pass_count": _status_count(rows, PASS_STATUS),
        "watch_count": _status_count(rows, WATCH_STATUS),
        "block_count": _status_count(rows, BLOCK_STATUS),
        "average_forecast_probability": _average(
            tuple(row.forecast_probability for row in rows),
        ),
        "average_benchmark_probability": _average(
            tuple(row.benchmark_probability for row in rows),
        ),
        "average_probability_gap_abs": _average(
            tuple(row.probability_gap_abs for row in rows),
        ),
        "average_evidence_driver_score": averages[0][1],
        "average_cost_driver_score": averages[1][1],
        "average_settlement_driver_score": averages[2][1],
        "average_domain_memory_driver_score": averages[3][1],
        "dominant_driver": dominant_driver,
        "dominant_driver_score": dominant_driver_score,
        "max_attribution_pressure": max(
            (row.attribution_pressure for row in rows),
            default=ZERO,
        ),
        "rows": rows,
        "reason_code_counts": _reason_code_counts(rows),
        "reason_codes": reason_codes,
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    return ResearchStrategyProbabilityGapAttributionReport(
        **values,
        public_payload_digest=_public_digest_from_values(values),
    )


def research_strategy_probability_gap_attribution_report_payload(
    report: ResearchStrategyProbabilityGapAttributionReport,
) -> dict[str, Any]:
    if type(report) is not ResearchStrategyProbabilityGapAttributionReport:
        raise ValueError(
            "report must be ResearchStrategyProbabilityGapAttributionReport",
        )
    _require_hard_flags("report", report)
    if report.public_payload_digest != research_strategy_probability_gap_attribution_digest(
        report,
    ):
        raise ValueError("public_payload_digest must match report payload")
    payload = _json_ready(asdict(report))
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    return payload


def research_strategy_probability_gap_attribution_digest_payload(
    report: ResearchStrategyProbabilityGapAttributionReport,
) -> dict[str, Any]:
    if type(report) is not ResearchStrategyProbabilityGapAttributionReport:
        raise ValueError(
            "report must be ResearchStrategyProbabilityGapAttributionReport",
        )
    payload = _json_ready(_report_values_without_digest(report))
    if type(payload) is not dict:
        raise ValueError("digest payload must be a JSON object")
    return payload


def research_strategy_probability_gap_attribution_digest(
    report: ResearchStrategyProbabilityGapAttributionReport,
) -> str:
    if type(report) is not ResearchStrategyProbabilityGapAttributionReport:
        raise ValueError(
            "report must be ResearchStrategyProbabilityGapAttributionReport",
        )
    return _public_digest_from_values(_report_values_without_digest(report))


def _row_from_input(
    item: ResearchStrategyProbabilityGapAttributionInput,
    config: ResearchStrategyProbabilityGapAttributionConfig,
) -> ResearchStrategyProbabilityGapAttributionRow:
    probability_gap_abs = _abs_decimal(
        item.forecast_probability - item.benchmark_probability,
    )
    dominant_driver, dominant_driver_score = _dominant_driver_for_item(item)
    reason_codes = _row_reason_codes(
        probability_gap_abs=probability_gap_abs,
        item=item,
        config=config,
    )
    return ResearchStrategyProbabilityGapAttributionRow(
        rank=ONE,
        observed_at=item.observed_at,
        forecast_probability=item.forecast_probability,
        benchmark_probability=item.benchmark_probability,
        probability_gap_abs=probability_gap_abs,
        probability_gap_direction=_gap_direction(
            item.forecast_probability,
            item.benchmark_probability,
        ),
        evidence_driver_score=item.evidence_driver_score,
        cost_driver_score=item.cost_driver_score,
        settlement_driver_score=item.settlement_driver_score,
        domain_memory_driver_score=item.domain_memory_driver_score,
        dominant_driver=dominant_driver,
        dominant_driver_score=dominant_driver_score,
        attribution_pressure=max(probability_gap_abs, dominant_driver_score),
        status=_status_from_reason_codes(reason_codes),
        reason_codes=reason_codes,
    )


def _row_reason_codes(
    *,
    probability_gap_abs: Decimal,
    item: ResearchStrategyProbabilityGapAttributionInput,
    config: ResearchStrategyProbabilityGapAttributionConfig,
) -> tuple[str, ...]:
    detail_codes: list[str] = []
    if probability_gap_abs >= config.block_probability_gap:
        detail_codes.append("gap_magnitude_block")
    elif probability_gap_abs >= config.watch_probability_gap:
        detail_codes.append("gap_magnitude_watch")
    _append_driver_reason(
        detail_codes,
        score=item.evidence_driver_score,
        config=config,
        block_reason="evidence_driver_block",
        watch_reason="evidence_driver_watch",
    )
    _append_driver_reason(
        detail_codes,
        score=item.cost_driver_score,
        config=config,
        block_reason="cost_driver_block",
        watch_reason="cost_driver_watch",
    )
    _append_driver_reason(
        detail_codes,
        score=item.settlement_driver_score,
        config=config,
        block_reason="settlement_driver_block",
        watch_reason="settlement_driver_watch",
    )
    _append_driver_reason(
        detail_codes,
        score=item.domain_memory_driver_score,
        config=config,
        block_reason="domain_memory_driver_block",
        watch_reason="domain_memory_driver_watch",
    )
    status = _status_from_reason_codes(tuple(detail_codes))
    return _normalize_reason_codes(
        "reason_codes",
        (f"probability_gap_attribution_{status}", *detail_codes),
        allow_empty=False,
    )


def _append_driver_reason(
    reason_codes: list[str],
    *,
    score: Decimal,
    config: ResearchStrategyProbabilityGapAttributionConfig,
    block_reason: str,
    watch_reason: str,
) -> None:
    if score >= config.block_driver_score:
        reason_codes.append(block_reason)
    elif score >= config.watch_driver_score:
        reason_codes.append(watch_reason)


def _rank_rows(
    rows: tuple[ResearchStrategyProbabilityGapAttributionRow, ...],
) -> tuple[ResearchStrategyProbabilityGapAttributionRow, ...]:
    return tuple(
        ResearchStrategyProbabilityGapAttributionRow(
            rank=_decimal_count(index),
            observed_at=row.observed_at,
            forecast_probability=row.forecast_probability,
            benchmark_probability=row.benchmark_probability,
            probability_gap_abs=row.probability_gap_abs,
            probability_gap_direction=row.probability_gap_direction,
            evidence_driver_score=row.evidence_driver_score,
            cost_driver_score=row.cost_driver_score,
            settlement_driver_score=row.settlement_driver_score,
            domain_memory_driver_score=row.domain_memory_driver_score,
            dominant_driver=row.dominant_driver,
            dominant_driver_score=row.dominant_driver_score,
            attribution_pressure=row.attribution_pressure,
            status=row.status,
            reason_codes=row.reason_codes,
        )
        for index, row in enumerate(sorted(rows, key=_row_sort_key), start=1)
    )


def _row_sort_key(
    row: ResearchStrategyProbabilityGapAttributionRow,
) -> tuple[Decimal, Decimal, Decimal, Decimal, Decimal, Decimal, Decimal, datetime]:
    return (
        STATUS_SEVERITY[row.status],
        -row.attribution_pressure,
        -row.probability_gap_abs,
        -row.dominant_driver_score,
        -row.evidence_driver_score,
        -row.cost_driver_score,
        -row.settlement_driver_score,
        row.observed_at,
    )


def _normalize_inputs(
    value: Sequence[ResearchStrategyProbabilityGapAttributionInput],
) -> tuple[ResearchStrategyProbabilityGapAttributionInput, ...]:
    if isinstance(value, (str, bytes)) or not isinstance(value, Sequence):
        raise ValueError("inputs must be a sequence")
    rows = tuple(value)
    for row in rows:
        if type(row) is not ResearchStrategyProbabilityGapAttributionInput:
            raise ValueError("inputs must contain gap attribution input values")
        _require_hard_flags("input", row)
    return rows


def _normalize_rows(
    value: Sequence[ResearchStrategyProbabilityGapAttributionRow],
) -> tuple[ResearchStrategyProbabilityGapAttributionRow, ...]:
    if isinstance(value, (str, bytes)) or not isinstance(value, Sequence):
        raise ValueError("rows must be a sequence")
    rows = tuple(value)
    for row in rows:
        if type(row) is not ResearchStrategyProbabilityGapAttributionRow:
            raise ValueError("rows must contain gap attribution row values")
        _require_hard_flags("row", row)
    if rows != tuple(sorted(rows, key=_row_sort_key)):
        raise ValueError("rows must use deterministic sequence")
    if tuple(row.rank for row in rows) != tuple(
        _decimal_count(index) for index in range(1, len(rows) + 1)
    ):
        raise ValueError("rows must use sequential ranks")
    return rows


def _normalize_reason_code_counts(
    value: Sequence[ResearchStrategyProbabilityGapAttributionReasonCodeCount],
) -> tuple[ResearchStrategyProbabilityGapAttributionReasonCodeCount, ...]:
    if isinstance(value, (str, bytes)) or not isinstance(value, Sequence):
        raise ValueError("reason_code_counts must be a sequence")
    rows = tuple(value)
    seen: set[str] = set()
    expected = tuple(sorted(rows, key=lambda row: _reason_code_rank(row.reason_code)))
    if rows != expected:
        raise ValueError("reason_code_counts must use deterministic sequence")
    for row in rows:
        if type(row) is not ResearchStrategyProbabilityGapAttributionReasonCodeCount:
            raise ValueError("reason_code_counts must contain reason count values")
        _require_hard_flags("reason_count", row)
        if row.reason_code in seen:
            raise ValueError("reason_code_counts must not repeat")
        seen.add(row.reason_code)
    return rows


def _reason_code_counts(
    rows: tuple[ResearchStrategyProbabilityGapAttributionRow, ...],
) -> tuple[ResearchStrategyProbabilityGapAttributionReasonCodeCount, ...]:
    if not rows:
        return (
            ResearchStrategyProbabilityGapAttributionReasonCodeCount(
                reason_code=MISSING_INPUTS_REASON,
                count=ONE,
            ),
        )
    counter: Counter[str] = Counter()
    for row in rows:
        counter.update(row.reason_codes)
    return tuple(
        ResearchStrategyProbabilityGapAttributionReasonCodeCount(
            reason_code=reason_code,
            count=_decimal_count(counter[reason_code]),
        )
        for reason_code in REASON_CODE_SEQUENCE
        if reason_code in counter
    )


def _normalize_reason_codes(
    field_name: str,
    value: Sequence[str],
    *,
    allow_empty: bool,
) -> tuple[str, ...]:
    if isinstance(value, (str, bytes)) or not isinstance(value, Sequence):
        raise ValueError(f"{field_name} must be a sequence")
    normalized: list[str] = []
    seen: set[str] = set()
    for reason_code in value:
        reason_code = _require_reason_code(reason_code)
        if reason_code in seen:
            raise ValueError(f"{field_name} must not repeat")
        seen.add(reason_code)
        normalized.append(reason_code)
    if not allow_empty and not normalized:
        raise ValueError(f"{field_name} must not be empty")
    expected = tuple(
        reason_code for reason_code in REASON_CODE_SEQUENCE if reason_code in seen
    )
    if tuple(normalized) != expected:
        raise ValueError(f"{field_name} must use deterministic sequence")
    return tuple(normalized)


def _report_reason_codes(
    rows: tuple[ResearchStrategyProbabilityGapAttributionRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return (MISSING_INPUTS_REASON,)
    seen: set[str] = set()
    for row in rows:
        seen.update(row.reason_codes)
    return _normalize_reason_codes(
        "reason_codes",
        tuple(reason_code for reason_code in REASON_CODE_SEQUENCE if reason_code in seen),
        allow_empty=False,
    )


def _report_status(
    rows: tuple[ResearchStrategyProbabilityGapAttributionRow, ...],
) -> str:
    if not rows:
        return BLOCK_STATUS
    if any(row.status == BLOCK_STATUS for row in rows):
        return BLOCK_STATUS
    if any(row.status == WATCH_STATUS for row in rows):
        return WATCH_STATUS
    return PASS_STATUS


def _status_count(
    rows: tuple[ResearchStrategyProbabilityGapAttributionRow, ...],
    status: str,
) -> Decimal:
    return _decimal_count(sum(1 for row in rows if row.status == status))


def _average(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return _clamp_probability(sum(values, ZERO) / Decimal(len(values)))


def _driver_averages(
    rows: tuple[ResearchStrategyProbabilityGapAttributionRow, ...],
) -> tuple[tuple[str, Decimal], ...]:
    return (
        ("evidence", _average(tuple(row.evidence_driver_score for row in rows))),
        ("cost", _average(tuple(row.cost_driver_score for row in rows))),
        ("settlement", _average(tuple(row.settlement_driver_score for row in rows))),
        (
            "domain_memory",
            _average(tuple(row.domain_memory_driver_score for row in rows)),
        ),
    )


def _dominant_driver_for_item(
    item: ResearchStrategyProbabilityGapAttributionInput,
) -> tuple[str, Decimal]:
    return _dominant_from_named_values(
        (
            ("evidence", item.evidence_driver_score),
            ("cost", item.cost_driver_score),
            ("settlement", item.settlement_driver_score),
            ("domain_memory", item.domain_memory_driver_score),
        ),
    )


def _dominant_from_named_values(values: tuple[tuple[str, Decimal], ...]) -> tuple[str, Decimal]:
    best_name = values[0][0]
    best_score = values[0][1]
    for name, score in values[1:]:
        if score > best_score:
            best_name = name
            best_score = score
    return best_name, best_score


def _gap_direction(forecast_probability: Decimal, benchmark_probability: Decimal) -> str:
    if forecast_probability > benchmark_probability:
        return "forecast_above_benchmark"
    if forecast_probability < benchmark_probability:
        return "forecast_below_benchmark"
    return "forecast_matches_benchmark"


def _validate_row_consistency(
    row: ResearchStrategyProbabilityGapAttributionRow,
) -> None:
    expected_gap = _abs_decimal(row.forecast_probability - row.benchmark_probability)
    if row.probability_gap_abs != expected_gap:
        raise ValueError("probability_gap_abs must match probability fields")
    if row.probability_gap_direction != _gap_direction(
        row.forecast_probability,
        row.benchmark_probability,
    ):
        raise ValueError("probability_gap_direction must match probability fields")
    expected_driver, expected_score = _dominant_from_named_values(
        (
            ("evidence", row.evidence_driver_score),
            ("cost", row.cost_driver_score),
            ("settlement", row.settlement_driver_score),
            ("domain_memory", row.domain_memory_driver_score),
        ),
    )
    if row.dominant_driver != expected_driver:
        raise ValueError("dominant_driver must match driver scores")
    if row.dominant_driver_score != expected_score:
        raise ValueError("dominant_driver_score must match driver scores")
    if row.attribution_pressure != max(row.probability_gap_abs, row.dominant_driver_score):
        raise ValueError("attribution_pressure must match row fields")
    if row.status != _status_from_reason_codes(row.reason_codes):
        raise ValueError("status must match reason_codes")
    if row.status == PASS_STATUS and row.reason_codes != (
        "probability_gap_attribution_pass",
    ):
        raise ValueError("pass rows must expose only pass reason code")


def _validate_report_consistency(
    report: ResearchStrategyProbabilityGapAttributionReport,
) -> None:
    rows = report.rows
    if report.attribution_count != _decimal_count(len(rows)):
        raise ValueError("attribution_count must match rows")
    if report.pass_count != _status_count(rows, PASS_STATUS):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _status_count(rows, WATCH_STATUS):
        raise ValueError("watch_count must match rows")
    if report.block_count != _status_count(rows, BLOCK_STATUS):
        raise ValueError("block_count must match rows")
    if report.average_forecast_probability != _average(
        tuple(row.forecast_probability for row in rows),
    ):
        raise ValueError("average_forecast_probability must match rows")
    if report.average_benchmark_probability != _average(
        tuple(row.benchmark_probability for row in rows),
    ):
        raise ValueError("average_benchmark_probability must match rows")
    if report.average_probability_gap_abs != _average(
        tuple(row.probability_gap_abs for row in rows),
    ):
        raise ValueError("average_probability_gap_abs must match rows")
    averages = _driver_averages(rows)
    if report.average_evidence_driver_score != averages[0][1]:
        raise ValueError("average_evidence_driver_score must match rows")
    if report.average_cost_driver_score != averages[1][1]:
        raise ValueError("average_cost_driver_score must match rows")
    if report.average_settlement_driver_score != averages[2][1]:
        raise ValueError("average_settlement_driver_score must match rows")
    if report.average_domain_memory_driver_score != averages[3][1]:
        raise ValueError("average_domain_memory_driver_score must match rows")
    dominant_driver, dominant_driver_score = _dominant_from_named_values(averages)
    if report.dominant_driver != dominant_driver:
        raise ValueError("dominant_driver must match driver averages")
    if report.dominant_driver_score != dominant_driver_score:
        raise ValueError("dominant_driver_score must match driver averages")
    if report.max_attribution_pressure != max(
        (row.attribution_pressure for row in rows),
        default=ZERO,
    ):
        raise ValueError("max_attribution_pressure must match rows")
    if report.status != _report_status(rows):
        raise ValueError("status must match rows")
    if report.reason_codes != _report_reason_codes(rows):
        raise ValueError("reason_codes must match rows")
    if report.reason_code_counts != _reason_code_counts(rows):
        raise ValueError("reason_code_counts must match rows")


def _status_from_reason_codes(reason_codes: tuple[str, ...]) -> str:
    if any(reason_code.endswith("_block") for reason_code in reason_codes):
        return BLOCK_STATUS
    if any(reason_code.endswith("_watch") for reason_code in reason_codes):
        return WATCH_STATUS
    return PASS_STATUS


def _require_supported_config_version(value: object) -> str:
    if type(value) is not str:
        raise ValueError("config_version must be a string")
    if value != DEFAULT_RESEARCH_STRATEGY_PROBABILITY_GAP_ATTRIBUTION_REPORT_CONFIG_VERSION:
        raise ValueError("config_version must be the supported value")
    return value


def _require_reason_code(value: object) -> str:
    if type(value) is not str:
        raise ValueError("reason_code must be a string")
    if value not in REASON_CODE_SEQUENCE:
        raise ValueError("reason_code is not supported")
    return value


def _reason_code_rank(reason_code: str) -> int:
    return REASON_CODE_SEQUENCE.index(reason_code)


def _require_driver_name(value: object) -> str:
    if type(value) is not str or value not in DRIVER_NAMES:
        raise ValueError("dominant_driver must be evidence, cost, settlement, or domain_memory")
    return value


def _require_direction(value: object) -> str:
    if type(value) is not str or value not in GAP_DIRECTIONS:
        raise ValueError("probability_gap_direction must be supported")
    return value


def _require_status(value: object) -> str:
    if type(value) is not str:
        raise ValueError("status must be a string")
    if value not in STATUSES:
        raise ValueError("status must be pass, watch, or block")
    return value


def _require_hard_flags(label: str, value: object) -> None:
    if getattr(value, "paper_only", None) is not True:
        raise ValueError(f"{label} paper_only must be True")
    if getattr(value, "report_only", None) is not True:
        raise ValueError(f"{label} report_only must be True")
    if getattr(value, "readonly", None) is not True:
        raise ValueError(f"{label} readonly must be True")


def _require_exact_type(value: object, expected_type: type[object], label: str) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{label} must be exactly {expected_type.__name__}")


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be exactly datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_probability_decimal(field_name: str, value: object) -> Decimal:
    value = _require_decimal(field_name, value)
    if value < ZERO or value > ONE:
        raise ValueError(f"{field_name} must be between zero and one")
    return _quantize(value)


def _require_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    value = _require_decimal(field_name, value)
    if value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return _quantize(value)


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return value


def _decimal_count(value: int) -> Decimal:
    return _quantize(Decimal(value))


def _quantize(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(QUANTUM)


def _clamp_probability(value: Decimal) -> Decimal:
    value = _quantize(value)
    if value < ZERO:
        return ZERO
    if value > ONE:
        return ONE
    return value


def _abs_decimal(value: Decimal) -> Decimal:
    return -value if value < ZERO else value


def _require_less_than(
    left_name: str,
    left: Decimal,
    right_name: str,
    right: Decimal,
) -> None:
    if left >= right:
        raise ValueError(f"{left_name} must be less than {right_name}")


def _require_digest_or_empty(value: object) -> str:
    if type(value) is not str:
        raise ValueError("public_payload_digest must be a string")
    if value and not DIGEST_RE.fullmatch(value):
        raise ValueError("public_payload_digest must be a SHA-256 hex digest")
    return value


def _public_digest_from_values(values: dict[str, object]) -> str:
    payload = _json_ready(values)
    encoded = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _report_values_without_digest(
    report: ResearchStrategyProbabilityGapAttributionReport,
) -> dict[str, object]:
    values = asdict(report)
    values.pop("public_payload_digest", None)
    return values


def _json_ready(value: object) -> object:
    if is_dataclass(value) and not isinstance(value, type):
        return _json_ready(asdict(value))
    if isinstance(value, dict):
        return {str(key): _json_ready(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_ready(item) for item in value]
    if type(value) is Decimal:
        return format(value, "f")
    if type(value) is datetime:
        return value.isoformat()
    if type(value) in (str, bool) or value is None:
        return value
    raise ValueError(f"unsupported public payload value type: {type(value).__name__}")
