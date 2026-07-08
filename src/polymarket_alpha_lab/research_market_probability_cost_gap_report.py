"""Pure report-only model-vs-observed probability and cost drag reducer."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import asdict, dataclass, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, localcontext
import hashlib
import json
from typing import Any


__all__ = (
    "DEFAULT_RESEARCH_MARKET_PROBABILITY_COST_GAP_CONFIG_VERSION",
    "MarketProbabilityCostGapConfig",
    "MarketProbabilityCostGapObservation",
    "MarketProbabilityCostGapReasonCodeCount",
    "MarketProbabilityCostGapReport",
    "MarketProbabilityCostGapRow",
    "build_research_market_probability_cost_gap_report",
    "research_market_probability_cost_gap_report_payload",
    "validate_research_market_probability_cost_gap_report_payload",
)


DEFAULT_RESEARCH_MARKET_PROBABILITY_COST_GAP_CONFIG_VERSION = (
    "research-market-probability-cost-gap-report-v1"
)
QUANTUM = Decimal("0.000001")
ZERO = Decimal("0")
ONE = Decimal("1")
DECIMAL_CONTEXT = Context(prec=64)

PASS_STATUS = "pass"
WATCH_STATUS = "watch"
BLOCK_STATUS = "block"
STATUSES = (PASS_STATUS, WATCH_STATUS, BLOCK_STATUS)
STATUS_RANK = {
    BLOCK_STATUS: Decimal("0"),
    WATCH_STATUS: Decimal("1"),
    PASS_STATUS: Decimal("2"),
}

MISSING_INPUTS_REASON = "probability_cost_gap_missing_inputs"

_UNSAFE_PUBLIC_TERMS = (
    "://",
    "?",
    "@",
    "=",
    "api" "_" "key",
    "au" "th",
    "dsn",
    "market_id",
    "market_slug",
    "market_question",
    "private" "_" "key",
    "question",
    "raw_candidate_id",
    "raw_market_reference",
    "raw_source_reference",
    "secret",
    "source_text",
    "source_url",
    "table_name",
    "tok" "en",
    "or" "der",
    "tra" "de",
    "wal" "let",
)


@dataclass(frozen=True)
class MarketProbabilityCostGapConfig:
    config_version: str = DEFAULT_RESEARCH_MARKET_PROBABILITY_COST_GAP_CONFIG_VERSION
    watch_probability_gap: Decimal = Decimal("0.050000")
    block_probability_gap: Decimal = Decimal("0.150000")
    watch_total_cost_drag: Decimal = Decimal("0.030000")
    block_total_cost_drag: Decimal = Decimal("0.080000")
    watch_component_cost_drag: Decimal = Decimal("0.015000")
    block_component_cost_drag: Decimal = Decimal("0.040000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, MarketProbabilityCostGapConfig, "config")
        _require_public_identifier("config_version", self.config_version)
        for field_name in (
            "watch_probability_gap",
            "block_probability_gap",
            "watch_total_cost_drag",
            "block_total_cost_drag",
            "watch_component_cost_drag",
            "block_component_cost_drag",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        if self.block_probability_gap <= self.watch_probability_gap:
            raise ValueError("block_probability_gap must exceed watch_probability_gap")
        if self.block_total_cost_drag <= self.watch_total_cost_drag:
            raise ValueError("block_total_cost_drag must exceed watch_total_cost_drag")
        if self.block_component_cost_drag <= self.watch_component_cost_drag:
            raise ValueError(
                "block_component_cost_drag must exceed watch_component_cost_drag",
            )
        _require_hard_flags(self)
        _reject_unsafe_public_payload("config", self)


@dataclass(frozen=True)
class MarketProbabilityCostGapObservation:
    raw_candidate_id: str
    raw_market_reference: str
    raw_source_reference: str
    observed_at: datetime
    model_probability: Decimal
    observed_market_probability: Decimal
    fee_cost_drag: Decimal
    spread_cost_drag: Decimal
    depth_cost_drag: Decimal
    latency_cost_drag: Decimal
    upstream_reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, MarketProbabilityCostGapObservation, "observation")
        for field_name in (
            "raw_candidate_id",
            "raw_market_reference",
            "raw_source_reference",
        ):
            _require_raw_reference(field_name, getattr(self, field_name))
        object.__setattr__(
            self,
            "observed_at",
            _as_utc("observed_at", self.observed_at),
        )
        for field_name in (
            "model_probability",
            "observed_market_probability",
            "fee_cost_drag",
            "spread_cost_drag",
            "depth_cost_drag",
            "latency_cost_drag",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "upstream_reason_codes",
            _normalize_reason_codes(self.upstream_reason_codes),
        )
        _require_hard_flags(self)


@dataclass(frozen=True)
class MarketProbabilityCostGapRow:
    candidate_digest: str
    triage_rank: Decimal
    observed_at: datetime
    model_probability: Decimal
    observed_market_probability: Decimal
    probability_gap_abs: Decimal
    probability_gap_direction: str
    fee_cost_drag: Decimal
    spread_cost_drag: Decimal
    depth_cost_drag: Decimal
    latency_cost_drag: Decimal
    total_cost_drag: Decimal
    cost_adjusted_gap_abs: Decimal
    status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, MarketProbabilityCostGapRow, "row")
        _require_sha256_digest("candidate_digest", self.candidate_digest)
        object.__setattr__(
            self,
            "triage_rank",
            _normalize_positive_decimal("triage_rank", self.triage_rank),
        )
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in (
            "model_probability",
            "observed_market_probability",
            "probability_gap_abs",
            "fee_cost_drag",
            "spread_cost_drag",
            "depth_cost_drag",
            "latency_cost_drag",
            "total_cost_drag",
            "cost_adjusted_gap_abs",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        _require_probability_gap_direction(self.probability_gap_direction)
        _require_status("status", self.status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes),
        )
        _validate_row_consistency(self)
        _require_hard_flags(self)
        _reject_unsafe_public_payload("row", self)


@dataclass(frozen=True)
class MarketProbabilityCostGapReasonCodeCount:
    reason_code: str
    count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, MarketProbabilityCostGapReasonCodeCount, "reason_count")
        _require_public_identifier("reason_code", self.reason_code)
        if _contains_unsafe_public_term(self.reason_code):
            raise ValueError("reason_code has unsafe public payload")
        object.__setattr__(
            self,
            "count",
            _normalize_nonnegative_decimal("count", self.count),
        )
        _require_hard_flags(self)


@dataclass(frozen=True)
class MarketProbabilityCostGapReport:
    generated_at: datetime
    config_version: str
    status: str
    input_count: Decimal
    row_count: Decimal
    block_count: Decimal
    watch_count: Decimal
    pass_count: Decimal
    average_model_probability: Decimal
    average_observed_market_probability: Decimal
    average_probability_gap_abs: Decimal
    average_total_cost_drag: Decimal
    max_probability_gap_abs: Decimal
    max_total_cost_drag: Decimal
    max_cost_adjusted_gap_abs: Decimal
    reason_codes: tuple[str, ...]
    reason_code_counts: tuple[MarketProbabilityCostGapReasonCodeCount, ...]
    rows: tuple[MarketProbabilityCostGapRow, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, MarketProbabilityCostGapReport, "report")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_identifier("config_version", self.config_version)
        _require_status("status", self.status)
        for field_name in (
            "input_count",
            "row_count",
            "block_count",
            "watch_count",
            "pass_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "average_model_probability",
            "average_observed_market_probability",
            "average_probability_gap_abs",
            "average_total_cost_drag",
            "max_probability_gap_abs",
            "max_total_cost_drag",
            "max_cost_adjusted_gap_abs",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes),
        )
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        _validate_report_consistency(self)
        _require_hard_flags(self)
        _reject_unsafe_public_payload("report", self)
        if self.derived_validation_digest == "":
            object.__setattr__(
                self,
                "derived_validation_digest",
                _report_derived_validation_digest(self),
            )
        else:
            _require_sha256_digest(
                "derived_validation_digest",
                self.derived_validation_digest,
            )
            if self.derived_validation_digest != _report_derived_validation_digest(self):
                raise ValueError(
                    "derived_validation_digest does not match public payload",
                )


def build_research_market_probability_cost_gap_report(
    observations: Iterable[MarketProbabilityCostGapObservation],
    *,
    config: MarketProbabilityCostGapConfig,
    generated_at: datetime,
) -> MarketProbabilityCostGapReport:
    if type(config) is not MarketProbabilityCostGapConfig:
        raise ValueError("config must be a MarketProbabilityCostGapConfig")
    generated_at = _as_utc("generated_at", generated_at)
    _require_hard_flags(config)
    normalized = _normalize_observations(observations)
    unranked_rows = tuple(
        _row_from_observation(value, config=config, generated_at=generated_at)
        for value in normalized
    )
    rows = _rank_rows(unranked_rows)
    return MarketProbabilityCostGapReport(
        generated_at=generated_at,
        config_version=config.config_version,
        status=_report_status(rows),
        input_count=_count_decimal(len(normalized)),
        row_count=_count_decimal(len(rows)),
        block_count=_status_count(rows, BLOCK_STATUS),
        watch_count=_status_count(rows, WATCH_STATUS),
        pass_count=_status_count(rows, PASS_STATUS),
        average_model_probability=_average_row_decimal(rows, "model_probability"),
        average_observed_market_probability=_average_row_decimal(
            rows,
            "observed_market_probability",
        ),
        average_probability_gap_abs=_average_row_decimal(rows, "probability_gap_abs"),
        average_total_cost_drag=_average_row_decimal(rows, "total_cost_drag"),
        max_probability_gap_abs=_max_row_decimal(rows, "probability_gap_abs"),
        max_total_cost_drag=_max_row_decimal(rows, "total_cost_drag"),
        max_cost_adjusted_gap_abs=_max_row_decimal(rows, "cost_adjusted_gap_abs"),
        reason_codes=_report_reason_codes(rows),
        reason_code_counts=_reason_code_counts(rows),
        rows=rows,
    )


def research_market_probability_cost_gap_report_payload(
    report: MarketProbabilityCostGapReport,
) -> dict[str, Any]:
    if type(report) is not MarketProbabilityCostGapReport:
        raise ValueError("report must be a MarketProbabilityCostGapReport")
    _require_hard_flags(report)
    _reject_unsafe_public_payload("report", report)
    payload = _json_value(report)
    if type(payload) is not dict:
        raise ValueError("report must serialize to a JSON object")
    validate_research_market_probability_cost_gap_report_payload(payload)
    return payload


def validate_research_market_probability_cost_gap_report_payload(
    payload: dict[str, Any],
) -> dict[str, Any]:
    if type(payload) is not dict:
        raise ValueError("payload must be a dict")
    _require_payload_hard_flags(payload)
    _reject_unsafe_public_payload("payload", payload)
    provided_digest = payload.get("derived_validation_digest")
    _require_sha256_digest("derived_validation_digest", provided_digest)
    if provided_digest != _payload_derived_validation_digest(payload):
        raise ValueError("derived_validation_digest does not match public payload")
    return payload


def _row_from_observation(
    value: MarketProbabilityCostGapObservation,
    *,
    config: MarketProbabilityCostGapConfig,
    generated_at: datetime,
) -> MarketProbabilityCostGapRow:
    if value.observed_at > generated_at:
        raise ValueError("observed_at must not be after generated_at")
    probability_gap_abs = _abs_decimal(
        value.model_probability - value.observed_market_probability,
    )
    total_cost_drag = _total_cost_drag(
        value.fee_cost_drag,
        value.spread_cost_drag,
        value.depth_cost_drag,
        value.latency_cost_drag,
    )
    cost_adjusted_gap_abs = _cost_adjusted_gap_abs(
        probability_gap_abs,
        total_cost_drag,
    )
    direction = _probability_gap_direction(
        value.model_probability,
        value.observed_market_probability,
    )
    status = _row_status(
        probability_gap_abs=probability_gap_abs,
        total_cost_drag=total_cost_drag,
        component_cost_drags=(
            value.fee_cost_drag,
            value.spread_cost_drag,
            value.depth_cost_drag,
            value.latency_cost_drag,
        ),
        config=config,
    )
    return MarketProbabilityCostGapRow(
        candidate_digest=_candidate_digest(value.raw_candidate_id),
        triage_rank=ONE,
        observed_at=value.observed_at,
        model_probability=value.model_probability,
        observed_market_probability=value.observed_market_probability,
        probability_gap_abs=probability_gap_abs,
        probability_gap_direction=direction,
        fee_cost_drag=value.fee_cost_drag,
        spread_cost_drag=value.spread_cost_drag,
        depth_cost_drag=value.depth_cost_drag,
        latency_cost_drag=value.latency_cost_drag,
        total_cost_drag=total_cost_drag,
        cost_adjusted_gap_abs=cost_adjusted_gap_abs,
        status=status,
        reason_codes=_row_reason_codes(
            value.upstream_reason_codes,
            probability_gap_abs=probability_gap_abs,
            probability_gap_direction=direction,
            total_cost_drag=total_cost_drag,
            cost_adjusted_gap_abs=cost_adjusted_gap_abs,
            status=status,
            fee_cost_drag=value.fee_cost_drag,
            spread_cost_drag=value.spread_cost_drag,
            depth_cost_drag=value.depth_cost_drag,
            latency_cost_drag=value.latency_cost_drag,
            config=config,
        ),
    )


def _rank_rows(
    rows: tuple[MarketProbabilityCostGapRow, ...],
) -> tuple[MarketProbabilityCostGapRow, ...]:
    return tuple(
        MarketProbabilityCostGapRow(
            candidate_digest=row.candidate_digest,
            triage_rank=_count_decimal(index),
            observed_at=row.observed_at,
            model_probability=row.model_probability,
            observed_market_probability=row.observed_market_probability,
            probability_gap_abs=row.probability_gap_abs,
            probability_gap_direction=row.probability_gap_direction,
            fee_cost_drag=row.fee_cost_drag,
            spread_cost_drag=row.spread_cost_drag,
            depth_cost_drag=row.depth_cost_drag,
            latency_cost_drag=row.latency_cost_drag,
            total_cost_drag=row.total_cost_drag,
            cost_adjusted_gap_abs=row.cost_adjusted_gap_abs,
            status=row.status,
            reason_codes=row.reason_codes,
        )
        for index, row in enumerate(sorted(rows, key=_row_sort_key), start=1)
    )


def _row_status(
    *,
    probability_gap_abs: Decimal,
    total_cost_drag: Decimal,
    component_cost_drags: tuple[Decimal, ...],
    config: MarketProbabilityCostGapConfig,
) -> str:
    if (
        probability_gap_abs >= config.block_probability_gap
        or total_cost_drag >= config.block_total_cost_drag
        or any(value >= config.block_component_cost_drag for value in component_cost_drags)
    ):
        return BLOCK_STATUS
    if (
        probability_gap_abs >= config.watch_probability_gap
        or total_cost_drag >= config.watch_total_cost_drag
        or any(value >= config.watch_component_cost_drag for value in component_cost_drags)
    ):
        return WATCH_STATUS
    return PASS_STATUS


def _row_reason_codes(
    upstream_reason_codes: tuple[str, ...],
    *,
    probability_gap_abs: Decimal,
    probability_gap_direction: str,
    total_cost_drag: Decimal,
    cost_adjusted_gap_abs: Decimal,
    status: str,
    fee_cost_drag: Decimal,
    spread_cost_drag: Decimal,
    depth_cost_drag: Decimal,
    latency_cost_drag: Decimal,
    config: MarketProbabilityCostGapConfig,
) -> tuple[str, ...]:
    reason_codes = list(upstream_reason_codes)
    reason_codes.append(f"probability_cost_gap_status_{status}")
    reason_codes.append(f"probability_cost_gap_{probability_gap_direction}")
    if cost_adjusted_gap_abs > ZERO:
        reason_codes.append("probability_cost_gap_cost_adjusted_gap_positive")
    if probability_gap_abs >= config.block_probability_gap:
        reason_codes.append("probability_cost_gap_gap_block")
    elif probability_gap_abs >= config.watch_probability_gap:
        reason_codes.append("probability_cost_gap_gap_watch")
    if total_cost_drag >= config.block_total_cost_drag:
        reason_codes.append("probability_cost_gap_total_cost_drag_block")
    elif total_cost_drag >= config.watch_total_cost_drag:
        reason_codes.append("probability_cost_gap_total_cost_drag_watch")
    if fee_cost_drag >= config.watch_component_cost_drag:
        reason_codes.append("probability_cost_gap_fee_drag_elevated")
    if spread_cost_drag >= config.watch_component_cost_drag:
        reason_codes.append("probability_cost_gap_spread_drag_elevated")
    if depth_cost_drag >= config.watch_component_cost_drag:
        reason_codes.append("probability_cost_gap_depth_drag_elevated")
    if latency_cost_drag >= config.watch_component_cost_drag:
        reason_codes.append("probability_cost_gap_latency_drag_elevated")
    return _normalize_reason_codes(tuple(reason_codes))


def _normalize_observations(
    observations: Iterable[MarketProbabilityCostGapObservation],
) -> tuple[MarketProbabilityCostGapObservation, ...]:
    if isinstance(observations, (str, bytes)) or not isinstance(observations, Iterable):
        raise ValueError("observations must be an iterable")
    normalized = tuple(observations)
    for value in normalized:
        if type(value) is not MarketProbabilityCostGapObservation:
            raise ValueError(
                "observations must contain MarketProbabilityCostGapObservation",
            )
        _require_hard_flags(value)
    return normalized


def _normalize_rows(
    rows: Iterable[MarketProbabilityCostGapRow],
) -> tuple[MarketProbabilityCostGapRow, ...]:
    if isinstance(rows, (str, bytes)) or not isinstance(rows, Iterable):
        raise ValueError("rows must be an iterable")
    normalized = tuple(rows)
    for row in normalized:
        if type(row) is not MarketProbabilityCostGapRow:
            raise ValueError("rows must contain MarketProbabilityCostGapRow")
        _require_hard_flags(row)
    expected = tuple(sorted(normalized, key=_row_sort_key))
    if normalized != expected:
        raise ValueError("rows must use deterministic sequence")
    if tuple(row.triage_rank for row in normalized) != tuple(
        _count_decimal(index) for index in range(1, len(normalized) + 1)
    ):
        raise ValueError("rows must use sequential triage ranks")
    return normalized


def _normalize_reason_code_counts(
    counts: Iterable[MarketProbabilityCostGapReasonCodeCount],
) -> tuple[MarketProbabilityCostGapReasonCodeCount, ...]:
    if isinstance(counts, (str, bytes)) or not isinstance(counts, Iterable):
        raise ValueError("reason_code_counts must be an iterable")
    normalized = tuple(counts)
    seen: set[str] = set()
    for count in normalized:
        if type(count) is not MarketProbabilityCostGapReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain MarketProbabilityCostGapReasonCodeCount",
            )
        _require_hard_flags(count)
        if count.reason_code in seen:
            raise ValueError("reason_code_counts must not repeat")
        seen.add(count.reason_code)
    expected = tuple(sorted(normalized, key=lambda item: (-item.count, item.reason_code)))
    if normalized != expected:
        raise ValueError("reason_code_counts must use deterministic sequence")
    return normalized


def _validate_row_consistency(row: MarketProbabilityCostGapRow) -> None:
    status_reason = f"probability_cost_gap_status_{row.status}"
    if status_reason not in row.reason_codes:
        raise ValueError("status must match reason_codes")
    expected_gap = _abs_decimal(row.model_probability - row.observed_market_probability)
    if row.probability_gap_abs != expected_gap:
        raise ValueError("probability_gap_abs must match probabilities")
    expected_total = _total_cost_drag(
        row.fee_cost_drag,
        row.spread_cost_drag,
        row.depth_cost_drag,
        row.latency_cost_drag,
    )
    if row.total_cost_drag != expected_total:
        raise ValueError("total_cost_drag must match components")
    if row.cost_adjusted_gap_abs != _cost_adjusted_gap_abs(
        row.probability_gap_abs,
        row.total_cost_drag,
    ):
        raise ValueError("cost_adjusted_gap_abs must match gap and drag")
    if row.probability_gap_direction != _probability_gap_direction(
        row.model_probability,
        row.observed_market_probability,
    ):
        raise ValueError("probability_gap_direction must match probabilities")


def _validate_report_consistency(report: MarketProbabilityCostGapReport) -> None:
    if report.row_count != _count_decimal(len(report.rows)):
        raise ValueError("row_count must match rows")
    if report.block_count + report.watch_count + report.pass_count != report.row_count:
        raise ValueError("status counts must match row_count")
    if report.status != _report_status(report.rows):
        raise ValueError("status must match rows")
    if report.average_model_probability != _average_row_decimal(
        report.rows,
        "model_probability",
    ):
        raise ValueError("average_model_probability must match rows")
    if report.average_observed_market_probability != _average_row_decimal(
        report.rows,
        "observed_market_probability",
    ):
        raise ValueError("average_observed_market_probability must match rows")
    if report.average_probability_gap_abs != _average_row_decimal(
        report.rows,
        "probability_gap_abs",
    ):
        raise ValueError("average_probability_gap_abs must match rows")
    if report.average_total_cost_drag != _average_row_decimal(
        report.rows,
        "total_cost_drag",
    ):
        raise ValueError("average_total_cost_drag must match rows")
    if report.max_probability_gap_abs != _max_row_decimal(
        report.rows,
        "probability_gap_abs",
    ):
        raise ValueError("max_probability_gap_abs must match rows")
    if report.max_total_cost_drag != _max_row_decimal(report.rows, "total_cost_drag"):
        raise ValueError("max_total_cost_drag must match rows")
    if report.max_cost_adjusted_gap_abs != _max_row_decimal(
        report.rows,
        "cost_adjusted_gap_abs",
    ):
        raise ValueError("max_cost_adjusted_gap_abs must match rows")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")
    if report.reason_code_counts != _reason_code_counts(report.rows):
        raise ValueError("reason_code_counts must match rows")


def _report_status(rows: tuple[MarketProbabilityCostGapRow, ...]) -> str:
    if not rows:
        return BLOCK_STATUS
    if any(row.status == BLOCK_STATUS for row in rows):
        return BLOCK_STATUS
    if any(row.status == WATCH_STATUS for row in rows):
        return WATCH_STATUS
    return PASS_STATUS


def _report_reason_codes(
    rows: tuple[MarketProbabilityCostGapRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return (MISSING_INPUTS_REASON,)
    reason_codes: list[str] = []
    for row in rows:
        reason_codes.extend(row.reason_codes)
    return _normalize_reason_codes(tuple(reason_codes))


def _reason_code_counts(
    rows: tuple[MarketProbabilityCostGapRow, ...],
) -> tuple[MarketProbabilityCostGapReasonCodeCount, ...]:
    if not rows:
        return (
            MarketProbabilityCostGapReasonCodeCount(
                reason_code=MISSING_INPUTS_REASON,
                count=ONE,
            ),
        )
    counts: dict[str, Decimal] = {}
    for row in rows:
        for reason_code in row.reason_codes:
            counts[reason_code] = _quantize_decimal(counts.get(reason_code, ZERO) + ONE)
    return tuple(
        sorted(
            (
                MarketProbabilityCostGapReasonCodeCount(
                    reason_code=reason_code,
                    count=count,
                )
                for reason_code, count in counts.items()
            ),
            key=lambda item: (-item.count, item.reason_code),
        ),
    )


def _row_sort_key(
    row: MarketProbabilityCostGapRow,
) -> tuple[Decimal, Decimal, Decimal, Decimal, str]:
    return (
        STATUS_RANK[row.status],
        -row.cost_adjusted_gap_abs,
        -row.probability_gap_abs,
        -row.total_cost_drag,
        row.candidate_digest,
    )


def _status_count(
    rows: tuple[MarketProbabilityCostGapRow, ...],
    status: str,
) -> Decimal:
    return _count_decimal(sum(1 for row in rows if row.status == status))


def _max_row_decimal(rows: tuple[MarketProbabilityCostGapRow, ...], field_name: str) -> Decimal:
    if not rows:
        return _quantize_decimal(ZERO)
    return max(getattr(row, field_name) for row in rows)


def _average_row_decimal(
    rows: tuple[MarketProbabilityCostGapRow, ...],
    field_name: str,
) -> Decimal:
    if not rows:
        return _quantize_decimal(ZERO)
    total = ZERO
    for row in rows:
        total = _quantize_decimal(total + getattr(row, field_name))
    with localcontext(DECIMAL_CONTEXT):
        return _quantize_decimal(total / Decimal(len(rows)))


def _abs_decimal(value: Decimal) -> Decimal:
    return _quantize_decimal(abs(value))


def _total_cost_drag(*values: Decimal) -> Decimal:
    total = ZERO
    for value in values:
        total = _quantize_decimal(total + value)
    if total > ONE:
        raise ValueError("total_cost_drag must be between 0 and 1")
    return total


def _cost_adjusted_gap_abs(
    probability_gap_abs: Decimal,
    total_cost_drag: Decimal,
) -> Decimal:
    return _quantize_decimal(max(probability_gap_abs - total_cost_drag, ZERO))


def _probability_gap_direction(
    model_probability: Decimal,
    observed_market_probability: Decimal,
) -> str:
    if model_probability > observed_market_probability:
        return "model_above_market"
    if model_probability < observed_market_probability:
        return "model_below_market"
    return "model_matches_market"


def _candidate_digest(raw_candidate_id: str) -> str:
    return hashlib.sha256(raw_candidate_id.encode("utf-8")).hexdigest()


def _count_decimal(value: int) -> Decimal:
    return _quantize_decimal(Decimal(value))


def _normalize_probability(field_name: str, value: object) -> Decimal:
    normalized = _normalize_nonnegative_decimal(field_name, value)
    if normalized > ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return normalized


def _normalize_positive_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _normalize_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _normalize_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return _quantize_decimal(value)


def _quantize_decimal(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(QUANTUM)


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be UTC-aware")
    return value.astimezone(UTC)


def _require_raw_reference(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")


def _require_public_identifier(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")
    if len(value) > 128:
        raise ValueError(f"{field_name} must be at most 128 characters")
    allowed = set("ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789_.-")
    if any(character not in allowed for character in value):
        raise ValueError(f"{field_name} must be a public identifier")


def _require_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in STATUSES:
        raise ValueError(f"{field_name} must be pass, watch, or block")


def _require_probability_gap_direction(value: object) -> None:
    if type(value) is not str or value not in (
        "model_above_market",
        "model_below_market",
        "model_matches_market",
    ):
        raise ValueError("probability_gap_direction must be known")


def _normalize_reason_codes(reason_codes: Iterable[str]) -> tuple[str, ...]:
    if isinstance(reason_codes, (str, bytes)) or not isinstance(reason_codes, Iterable):
        raise ValueError("reason_codes must be an iterable")
    normalized: list[str] = []
    for reason_code in reason_codes:
        _require_public_identifier("reason_code", reason_code)
        if _contains_unsafe_public_term(reason_code):
            raise ValueError("reason_code has unsafe public payload")
        if reason_code not in normalized:
            normalized.append(reason_code)
    return tuple(sorted(normalized))


def _require_hard_flags(value: object) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if getattr(value, field_name, None) is not True:
            raise ValueError(f"{field_name} must be True")


def _require_payload_hard_flags(value: dict[str, Any]) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if value.get(field_name) is not True:
            raise ValueError(f"{field_name} must be True")


def _require_sha256_digest(field_name: str, value: object) -> None:
    if type(value) is not str or len(value) != 64:
        raise ValueError(f"{field_name} must be a SHA-256 digest")
    allowed = set("0123456789abcdef")
    if any(character not in allowed for character in value):
        raise ValueError(f"{field_name} must be a SHA-256 digest")


def _require_exact_type(value: object, expected_type: type[object], field_name: str) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{field_name} must be a {expected_type.__name__}")


def _json_value(value: object) -> Any:
    if is_dataclass(value) and not isinstance(value, type):
        return _json_value(asdict(value))
    if isinstance(value, dict):
        return {str(key): _json_value(item) for key, item in value.items()}
    if isinstance(value, tuple):
        return [_json_value(item) for item in value]
    if isinstance(value, list):
        return [_json_value(item) for item in value]
    if type(value) is Decimal:
        return f"{value:.6f}"
    if type(value) is datetime:
        return value.isoformat()
    if type(value) in (str, bool) or value is None:
        return value
    raise ValueError(f"unsupported public payload value: {type(value).__name__}")


def _report_derived_validation_digest(report: MarketProbabilityCostGapReport) -> str:
    value = asdict(report)
    value.pop("derived_validation_digest", None)
    return _canonical_payload_digest(_json_value(value))


def _payload_derived_validation_digest(payload: dict[str, Any]) -> str:
    value = dict(payload)
    value.pop("derived_validation_digest", None)
    return _canonical_payload_digest(value)


def _canonical_payload_digest(payload: dict[str, Any]) -> str:
    canonical = json.dumps(
        payload,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _reject_unsafe_public_payload(label: str, value: object) -> None:
    if is_dataclass(value) and not isinstance(value, type):
        value = asdict(value)
    if isinstance(value, dict):
        for key, item in value.items():
            if _contains_unsafe_public_term(str(key)):
                raise ValueError(f"{label} has unsafe public payload")
            _reject_unsafe_public_payload(label, item)
        return
    if isinstance(value, (tuple, list)):
        for item in value:
            _reject_unsafe_public_payload(label, item)
        return
    if isinstance(value, str) and _contains_unsafe_public_term(value):
        raise ValueError(f"{label} has unsafe public payload")


def _contains_unsafe_public_term(value: str) -> bool:
    lowered = value.lower()
    return any(term in lowered for term in _UNSAFE_PUBLIC_TERMS)
