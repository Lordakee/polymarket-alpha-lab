"""Pure source-confidence, edge, and cost-pressure alignment report."""

from __future__ import annotations

from dataclasses import asdict, dataclass, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
from json import dumps
from typing import Any, Iterable


DEFAULT_RESEARCH_STRATEGY_SOURCE_CONFIDENCE_COST_ALIGNMENT_REPORT_CONFIG_VERSION = (
    "research-strategy-source-confidence-cost-alignment-report-v0"
)
RESEARCH_STRATEGY_SOURCE_CONFIDENCE_COST_ALIGNMENT_REPORT_STATUSES = (
    "pass",
    "watch",
    "block",
)

QUANTUM = Decimal("0.000001")
ZERO = Decimal("0")
ONE = Decimal("1")
THREE = Decimal("3")
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)

ROW_REASON_CODES = (
    "source_confidence_cost_alignment_pass",
    "source_confidence_cost_alignment_watch",
    "source_confidence_cost_alignment_block",
    "source_confidence_pass",
    "source_confidence_watch",
    "source_confidence_block",
    "probability_edge_pass",
    "probability_edge_watch",
    "probability_edge_block",
    "cost_pressure_pass",
    "cost_pressure_watch",
    "cost_pressure_block",
)
REPORT_REASON_CODES = (
    "source_confidence_cost_alignment_report_pass",
    "source_confidence_cost_alignment_report_watch",
    "source_confidence_cost_alignment_report_block",
    "source_confidence_cost_alignment_report_empty",
    "source_confidence_review",
    "probability_edge_review",
    "cost_pressure_review",
)
REASON_CODES = ROW_REASON_CODES + REPORT_REASON_CODES
_HEX_CHARS = frozenset("0123456789abcdef")
_PRIVATE_PUBLIC_KEY_FRAGMENTS = (
    "candidate" + "_id",
    "market" + "_id",
    "market" + "_slug",
    "market" + "_ques" + "tion",
    "ques" + "tion",
    "source" + "_id",
    "source" + "_url",
    "source" + "_text",
    "url",
    "dsn",
    "credential",
    "secret",
    "token",
    "au" + "th",
    "wal" + "let",
    "or" + "der",
    "trad" + "e",
    "trad" + "ing",
    "signing",
    "mutation",
    "persist",
    "table",
)
_PRIVATE_PUBLIC_VALUE_FRAGMENTS = (
    "http://",
    "https://",
    "candidate_",
    "market_",
    "raw_id",
    "private",
    "dsn=",
    "token=",
    "wal" + "let",
    "or" + "der",
    "trad" + "e",
    "b" + "uy",
    "se" + "ll",
    "reco" + "mmendation",
    "siz" + "ing",
)
_REPORT_PUBLIC_PAYLOAD_KEYS = frozenset(
    (
        "generated_at",
        "config_version",
        "input_count",
        "pass_count",
        "watch_count",
        "block_count",
        "mean_sanitized_source_confidence_score",
        "mean_absolute_probability_edge",
        "mean_total_cost_pressure_score",
        "mean_alignment_score",
        "status",
        "reason_codes",
        "reason_code_counts",
        "rows",
        "derived_validation_digest",
        "paper_only",
        "report_only",
        "readonly",
    ),
)
_ROW_PUBLIC_PAYLOAD_KEYS = frozenset(
    (
        "observed_at",
        "sanitized_source_confidence_score",
        "forecast_probability",
        "market_probability",
        "raw_probability_edge",
        "absolute_probability_edge",
        "probability_edge_strength_score",
        "fee_cost_pressure_score",
        "spread_cost_pressure_score",
        "liquidity_cost_pressure_score",
        "total_cost_pressure_score",
        "cost_pressure_safety_score",
        "alignment_score",
        "status",
        "reason_codes",
        "row_number",
        "derived_validation_digest",
        "paper_only",
        "report_only",
        "readonly",
    ),
)
_REASON_CODE_COUNT_PUBLIC_PAYLOAD_KEYS = frozenset(
    (
        "reason_code",
        "count",
        "input_ratio",
        "paper_only",
        "report_only",
        "readonly",
    ),
)


@dataclass(frozen=True)
class ResearchStrategySourceConfidenceCostAlignmentConfig:
    config_version: str
    source_confidence_pass_floor: Decimal
    source_confidence_watch_floor: Decimal
    probability_edge_pass_floor: Decimal
    probability_edge_watch_floor: Decimal
    fee_cost_pressure_pass_ceiling: Decimal
    fee_cost_pressure_watch_ceiling: Decimal
    spread_cost_pressure_pass_ceiling: Decimal
    spread_cost_pressure_watch_ceiling: Decimal
    liquidity_cost_pressure_pass_ceiling: Decimal
    liquidity_cost_pressure_watch_ceiling: Decimal
    total_cost_pressure_pass_ceiling: Decimal
    total_cost_pressure_watch_ceiling: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("config_version", self.config_version)
        for field_name in (
            "source_confidence_pass_floor",
            "source_confidence_watch_floor",
            "probability_edge_pass_floor",
            "probability_edge_watch_floor",
            "fee_cost_pressure_pass_ceiling",
            "fee_cost_pressure_watch_ceiling",
            "spread_cost_pressure_pass_ceiling",
            "spread_cost_pressure_watch_ceiling",
            "liquidity_cost_pressure_pass_ceiling",
            "liquidity_cost_pressure_watch_ceiling",
            "total_cost_pressure_pass_ceiling",
            "total_cost_pressure_watch_ceiling",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        _require_floor_pair(
            "source_confidence",
            self.source_confidence_pass_floor,
            self.source_confidence_watch_floor,
        )
        _require_floor_pair(
            "probability_edge",
            self.probability_edge_pass_floor,
            self.probability_edge_watch_floor,
        )
        _require_ceiling_pair(
            "fee_cost_pressure",
            self.fee_cost_pressure_pass_ceiling,
            self.fee_cost_pressure_watch_ceiling,
        )
        _require_ceiling_pair(
            "spread_cost_pressure",
            self.spread_cost_pressure_pass_ceiling,
            self.spread_cost_pressure_watch_ceiling,
        )
        _require_ceiling_pair(
            "liquidity_cost_pressure",
            self.liquidity_cost_pressure_pass_ceiling,
            self.liquidity_cost_pressure_watch_ceiling,
        )
        _require_ceiling_pair(
            "total_cost_pressure",
            self.total_cost_pressure_pass_ceiling,
            self.total_cost_pressure_watch_ceiling,
        )
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class ResearchStrategySourceConfidenceCostAlignmentInput:
    candidate_id: str
    market_id: str
    market_slug: str
    market_question: str
    observed_at: datetime
    sanitized_source_confidence_score: Decimal
    forecast_probability: Decimal
    market_probability: Decimal
    fee_cost_pressure_score: Decimal
    spread_cost_pressure_score: Decimal
    liquidity_cost_pressure_score: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        for field_name in (
            "candidate_id",
            "market_id",
            "market_slug",
            "market_question",
        ):
            _require_private_string(field_name, getattr(self, field_name))
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in (
            "sanitized_source_confidence_score",
            "forecast_probability",
            "market_probability",
            "fee_cost_pressure_score",
            "spread_cost_pressure_score",
            "liquidity_cost_pressure_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        _require_hard_flags("input", self)


@dataclass(frozen=True)
class ResearchStrategySourceConfidenceCostAlignmentReasonCodeCount:
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
            _normalize_nonnegative_count("count", self.count),
        )
        object.__setattr__(
            self,
            "input_ratio",
            _normalize_probability("input_ratio", self.input_ratio),
        )
        _require_hard_flags("reason_code_count", self)


@dataclass(frozen=True)
class ResearchStrategySourceConfidenceCostAlignmentRow:
    candidate_id: str
    market_id: str
    market_slug: str
    market_question: str
    observed_at: datetime
    sanitized_source_confidence_score: Decimal
    forecast_probability: Decimal
    market_probability: Decimal
    raw_probability_edge: Decimal
    absolute_probability_edge: Decimal
    probability_edge_strength_score: Decimal
    fee_cost_pressure_score: Decimal
    spread_cost_pressure_score: Decimal
    liquidity_cost_pressure_score: Decimal
    total_cost_pressure_score: Decimal
    cost_pressure_safety_score: Decimal
    alignment_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        for field_name in (
            "candidate_id",
            "market_id",
            "market_slug",
            "market_question",
        ):
            _require_private_string(field_name, getattr(self, field_name))
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in (
            "sanitized_source_confidence_score",
            "forecast_probability",
            "market_probability",
            "absolute_probability_edge",
            "probability_edge_strength_score",
            "fee_cost_pressure_score",
            "spread_cost_pressure_score",
            "liquidity_cost_pressure_score",
            "total_cost_pressure_score",
            "cost_pressure_safety_score",
            "alignment_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "raw_probability_edge",
            _normalize_decimal("raw_probability_edge", self.raw_probability_edge),
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
class ResearchStrategySourceConfidenceCostAlignmentReport:
    generated_at: datetime
    config_version: str
    input_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    mean_sanitized_source_confidence_score: Decimal
    mean_absolute_probability_edge: Decimal
    mean_total_cost_pressure_score: Decimal
    mean_alignment_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    reason_code_counts: tuple[ResearchStrategySourceConfidenceCostAlignmentReasonCodeCount, ...]
    rows: tuple[ResearchStrategySourceConfidenceCostAlignmentRow, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        for field_name in ("input_count", "pass_count", "watch_count", "block_count"):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_count(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "mean_sanitized_source_confidence_score",
            "mean_absolute_probability_edge",
            "mean_total_cost_pressure_score",
            "mean_alignment_score",
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
            _normalize_reason_codes("reason_codes", self.reason_codes, REPORT_REASON_CODES),
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


def build_research_strategy_source_confidence_cost_alignment_report(
    inputs: Iterable[ResearchStrategySourceConfidenceCostAlignmentInput],
    *,
    config: ResearchStrategySourceConfidenceCostAlignmentConfig,
    generated_at: datetime,
) -> ResearchStrategySourceConfidenceCostAlignmentReport:
    if type(config) is not ResearchStrategySourceConfidenceCostAlignmentConfig:
        raise ValueError(
            "config must be a ResearchStrategySourceConfidenceCostAlignmentConfig",
        )
    _require_hard_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    normalized_inputs = _normalize_inputs(inputs)
    rows = tuple(
        sorted(
            (
                _row_from_input(value, config=config, generated_at=generated_at_utc)
                for value in normalized_inputs
            ),
            key=_row_sort_key,
        ),
    )
    return ResearchStrategySourceConfidenceCostAlignmentReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        input_count=_count(len(rows)),
        pass_count=_status_count(rows, "pass"),
        watch_count=_status_count(rows, "watch"),
        block_count=_status_count(rows, "block"),
        mean_sanitized_source_confidence_score=_mean(
            tuple(row.sanitized_source_confidence_score for row in rows),
        ),
        mean_absolute_probability_edge=_mean(
            tuple(row.absolute_probability_edge for row in rows),
        ),
        mean_total_cost_pressure_score=_mean(
            tuple(row.total_cost_pressure_score for row in rows),
        ),
        mean_alignment_score=_mean(tuple(row.alignment_score for row in rows)),
        status=_report_status(rows),
        reason_codes=_report_reason_codes(rows),
        reason_code_counts=_reason_code_counts_from_rows(rows),
        rows=rows,
    )


def research_strategy_source_confidence_cost_alignment_report_payload(
    report: ResearchStrategySourceConfidenceCostAlignmentReport | dict[str, Any],
) -> dict[str, Any]:
    if type(report) is ResearchStrategySourceConfidenceCostAlignmentReport:
        _require_hard_flags("report", report)
        _verify_report_integrity(report)
        payload = _public_report_payload(report)
    elif type(report) is dict:
        _require_hard_flags("payload", _DictFlags(report))
        _reject_unsafe_public_payload("payload", report)
        _verify_public_payload_integrity(report)
        payload = _json_ready(report)
    else:
        raise ValueError(
            "report must be a ResearchStrategySourceConfidenceCostAlignmentReport",
        )
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    _require_hard_flags("payload", _DictFlags(payload))
    _reject_unsafe_public_payload("payload", payload)
    return payload


def _row_from_input(
    value: ResearchStrategySourceConfidenceCostAlignmentInput,
    *,
    config: ResearchStrategySourceConfidenceCostAlignmentConfig,
    generated_at: datetime,
) -> ResearchStrategySourceConfidenceCostAlignmentRow:
    observed_at = _as_utc("observed_at", value.observed_at)
    if observed_at > generated_at:
        raise ValueError("observed_at must not be after generated_at")
    raw_edge = _subtract_decimal(value.forecast_probability, value.market_probability)
    absolute_edge = _absolute_decimal(raw_edge)
    edge_strength = _floor_strength_score(
        absolute_edge,
        pass_floor=config.probability_edge_pass_floor,
        watch_floor=config.probability_edge_watch_floor,
    )
    total_cost = _sum_probabilities(
        (
            value.fee_cost_pressure_score,
            value.spread_cost_pressure_score,
            value.liquidity_cost_pressure_score,
        ),
    )
    cost_safety = _cost_pressure_safety_score(total_cost, config)
    alignment = _alignment_score(
        sanitized_source_confidence_score=value.sanitized_source_confidence_score,
        probability_edge_strength_score=edge_strength,
        cost_pressure_safety_score=cost_safety,
    )
    status = _row_status(
        sanitized_source_confidence_score=value.sanitized_source_confidence_score,
        absolute_probability_edge=absolute_edge,
        fee_cost_pressure_score=value.fee_cost_pressure_score,
        spread_cost_pressure_score=value.spread_cost_pressure_score,
        liquidity_cost_pressure_score=value.liquidity_cost_pressure_score,
        total_cost_pressure_score=total_cost,
        config=config,
    )
    return ResearchStrategySourceConfidenceCostAlignmentRow(
        candidate_id=value.candidate_id,
        market_id=value.market_id,
        market_slug=value.market_slug,
        market_question=value.market_question,
        observed_at=observed_at,
        sanitized_source_confidence_score=value.sanitized_source_confidence_score,
        forecast_probability=value.forecast_probability,
        market_probability=value.market_probability,
        raw_probability_edge=raw_edge,
        absolute_probability_edge=absolute_edge,
        probability_edge_strength_score=edge_strength,
        fee_cost_pressure_score=value.fee_cost_pressure_score,
        spread_cost_pressure_score=value.spread_cost_pressure_score,
        liquidity_cost_pressure_score=value.liquidity_cost_pressure_score,
        total_cost_pressure_score=total_cost,
        cost_pressure_safety_score=cost_safety,
        alignment_score=alignment,
        status=status,
        reason_codes=_row_reason_codes(
            sanitized_source_confidence_score=value.sanitized_source_confidence_score,
            absolute_probability_edge=absolute_edge,
            fee_cost_pressure_score=value.fee_cost_pressure_score,
            spread_cost_pressure_score=value.spread_cost_pressure_score,
            liquidity_cost_pressure_score=value.liquidity_cost_pressure_score,
            total_cost_pressure_score=total_cost,
            status=status,
            config=config,
        ),
    )


def _row_status(
    *,
    sanitized_source_confidence_score: Decimal,
    absolute_probability_edge: Decimal,
    fee_cost_pressure_score: Decimal,
    spread_cost_pressure_score: Decimal,
    liquidity_cost_pressure_score: Decimal,
    total_cost_pressure_score: Decimal,
    config: ResearchStrategySourceConfidenceCostAlignmentConfig,
) -> str:
    component_statuses = (
        _floor_status(
            sanitized_source_confidence_score,
            pass_floor=config.source_confidence_pass_floor,
            watch_floor=config.source_confidence_watch_floor,
        ),
        _floor_status(
            absolute_probability_edge,
            pass_floor=config.probability_edge_pass_floor,
            watch_floor=config.probability_edge_watch_floor,
        ),
        _cost_pressure_status(
            fee_cost_pressure_score=fee_cost_pressure_score,
            spread_cost_pressure_score=spread_cost_pressure_score,
            liquidity_cost_pressure_score=liquidity_cost_pressure_score,
            total_cost_pressure_score=total_cost_pressure_score,
            config=config,
        ),
    )
    if "block" in component_statuses:
        return "block"
    if "watch" in component_statuses:
        return "watch"
    return "pass"


def _row_reason_codes(
    *,
    sanitized_source_confidence_score: Decimal,
    absolute_probability_edge: Decimal,
    fee_cost_pressure_score: Decimal,
    spread_cost_pressure_score: Decimal,
    liquidity_cost_pressure_score: Decimal,
    total_cost_pressure_score: Decimal,
    status: str,
    config: ResearchStrategySourceConfidenceCostAlignmentConfig,
) -> tuple[str, ...]:
    return _normalize_reason_codes(
        "reason_codes",
        (
            f"source_confidence_cost_alignment_{status}",
            "source_confidence_"
            + _floor_status(
                sanitized_source_confidence_score,
                pass_floor=config.source_confidence_pass_floor,
                watch_floor=config.source_confidence_watch_floor,
            ),
            "probability_edge_"
            + _floor_status(
                absolute_probability_edge,
                pass_floor=config.probability_edge_pass_floor,
                watch_floor=config.probability_edge_watch_floor,
            ),
            "cost_pressure_"
            + _cost_pressure_status(
                fee_cost_pressure_score=fee_cost_pressure_score,
                spread_cost_pressure_score=spread_cost_pressure_score,
                liquidity_cost_pressure_score=liquidity_cost_pressure_score,
                total_cost_pressure_score=total_cost_pressure_score,
                config=config,
            ),
        ),
        ROW_REASON_CODES,
    )


def _floor_status(value: Decimal, *, pass_floor: Decimal, watch_floor: Decimal) -> str:
    if value < watch_floor:
        return "block"
    if value < pass_floor:
        return "watch"
    return "pass"


def _cost_pressure_status(
    *,
    fee_cost_pressure_score: Decimal,
    spread_cost_pressure_score: Decimal,
    liquidity_cost_pressure_score: Decimal,
    total_cost_pressure_score: Decimal,
    config: ResearchStrategySourceConfidenceCostAlignmentConfig,
) -> str:
    if (
        fee_cost_pressure_score <= config.fee_cost_pressure_pass_ceiling
        and spread_cost_pressure_score <= config.spread_cost_pressure_pass_ceiling
        and liquidity_cost_pressure_score <= config.liquidity_cost_pressure_pass_ceiling
        and total_cost_pressure_score <= config.total_cost_pressure_pass_ceiling
    ):
        return "pass"
    if (
        fee_cost_pressure_score <= config.fee_cost_pressure_watch_ceiling
        and spread_cost_pressure_score <= config.spread_cost_pressure_watch_ceiling
        and liquidity_cost_pressure_score <= config.liquidity_cost_pressure_watch_ceiling
        and total_cost_pressure_score <= config.total_cost_pressure_watch_ceiling
    ):
        return "watch"
    return "block"


def _floor_strength_score(
    value: Decimal,
    *,
    pass_floor: Decimal,
    watch_floor: Decimal,
) -> Decimal:
    if value <= watch_floor:
        return ZERO.quantize(QUANTUM)
    if value >= pass_floor:
        return ONE.quantize(QUANTUM)
    with localcontext(DECIMAL_CONTEXT):
        score = (value - watch_floor) / (pass_floor - watch_floor)
    return _normalize_probability("probability_edge_strength_score", score)


def _cost_pressure_safety_score(
    total_cost_pressure_score: Decimal,
    config: ResearchStrategySourceConfidenceCostAlignmentConfig,
) -> Decimal:
    if total_cost_pressure_score <= config.total_cost_pressure_pass_ceiling:
        return ONE.quantize(QUANTUM)
    if total_cost_pressure_score >= config.total_cost_pressure_watch_ceiling:
        return ZERO.quantize(QUANTUM)
    with localcontext(DECIMAL_CONTEXT):
        score = (
            config.total_cost_pressure_watch_ceiling - total_cost_pressure_score
        ) / (
            config.total_cost_pressure_watch_ceiling
            - config.total_cost_pressure_pass_ceiling
        )
    return _normalize_probability("cost_pressure_safety_score", score)


def _alignment_score(
    *,
    sanitized_source_confidence_score: Decimal,
    probability_edge_strength_score: Decimal,
    cost_pressure_safety_score: Decimal,
) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        score = (
            sanitized_source_confidence_score
            + probability_edge_strength_score
            + cost_pressure_safety_score
        ) / THREE
    return _normalize_probability("alignment_score", score)


def _report_status(rows: tuple[ResearchStrategySourceConfidenceCostAlignmentRow, ...]) -> str:
    if not rows:
        return "block"
    if any(row.status == "block" for row in rows):
        return "block"
    if any(row.status == "watch" for row in rows):
        return "watch"
    return "pass"


def _report_reason_codes(
    rows: tuple[ResearchStrategySourceConfidenceCostAlignmentRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return ("source_confidence_cost_alignment_report_empty",)
    report_status = _report_status(rows)
    row_codes = tuple(code for row in rows for code in row.reason_codes)
    codes = [f"source_confidence_cost_alignment_report_{report_status}"]
    if any(code.startswith("source_confidence_") and not code.endswith("_pass") for code in row_codes):
        codes.append("source_confidence_review")
    if any(code.startswith("probability_edge_") and not code.endswith("_pass") for code in row_codes):
        codes.append("probability_edge_review")
    if any(code.startswith("cost_pressure_") and not code.endswith("_pass") for code in row_codes):
        codes.append("cost_pressure_review")
    return _normalize_reason_codes("reason_codes", tuple(codes), REPORT_REASON_CODES)


def _reason_code_counts_from_rows(
    rows: tuple[ResearchStrategySourceConfidenceCostAlignmentRow, ...],
) -> tuple[ResearchStrategySourceConfidenceCostAlignmentReasonCodeCount, ...]:
    if not rows:
        return (
            ResearchStrategySourceConfidenceCostAlignmentReasonCodeCount(
                reason_code="source_confidence_cost_alignment_report_empty",
                count=_count(1),
                input_ratio=ONE.quantize(QUANTUM),
            ),
        )
    reason_codes = sorted({code for row in rows for code in row.reason_codes})
    return tuple(
        ResearchStrategySourceConfidenceCostAlignmentReasonCodeCount(
            reason_code=reason_code,
            count=_count(sum(1 for row in rows if reason_code in row.reason_codes)),
            input_ratio=_ratio(
                sum(1 for row in rows if reason_code in row.reason_codes),
                len(rows),
            ),
        )
        for reason_code in reason_codes
    )


def _public_report_payload(
    report: ResearchStrategySourceConfidenceCostAlignmentReport,
) -> dict[str, Any]:
    payload = asdict(report)
    payload["rows"] = [
        _public_row_payload(index, row) for index, row in enumerate(report.rows, start=1)
    ]
    payload.pop("derived_validation_digest", None)
    public_payload = _json_ready(payload)
    if type(public_payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    public_payload["derived_validation_digest"] = _public_payload_digest(public_payload)
    _verify_public_payload_integrity(public_payload)
    return public_payload


def _public_row_payload(
    row_number: int,
    row: ResearchStrategySourceConfidenceCostAlignmentRow,
) -> dict[str, Any]:
    payload = asdict(row)
    for field_name in (
        "candidate_id",
        "market_id",
        "market_slug",
        "market_question",
    ):
        payload.pop(field_name, None)
    payload.pop("derived_validation_digest", None)
    payload["row_number"] = _count(row_number)
    public_payload = _json_ready(payload)
    if type(public_payload) is not dict:
        raise ValueError("row payload must be a JSON object")
    public_payload["derived_validation_digest"] = _public_payload_digest(public_payload)
    return public_payload


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


def _normalize_inputs(
    inputs: Iterable[ResearchStrategySourceConfidenceCostAlignmentInput],
) -> tuple[ResearchStrategySourceConfidenceCostAlignmentInput, ...]:
    if isinstance(inputs, (str, bytes)):
        raise ValueError("inputs must be an iterable")
    try:
        normalized = tuple(inputs)
    except TypeError as exc:
        raise ValueError("inputs must be an iterable") from exc
    seen_refs: set[str] = set()
    for value in normalized:
        if type(value) is not ResearchStrategySourceConfidenceCostAlignmentInput:
            raise ValueError(
                "inputs must contain ResearchStrategySourceConfidenceCostAlignmentInput values",
            )
        _require_hard_flags("input", value)
        if value.candidate_id in seen_refs:
            raise ValueError("inputs must not contain duplicate candidate_id values")
        seen_refs.add(value.candidate_id)
    return normalized


def _normalize_rows(
    rows: Iterable[ResearchStrategySourceConfidenceCostAlignmentRow],
) -> tuple[ResearchStrategySourceConfidenceCostAlignmentRow, ...]:
    if isinstance(rows, (str, bytes)):
        raise ValueError("rows must be an iterable")
    try:
        normalized = tuple(rows)
    except TypeError as exc:
        raise ValueError("rows must be an iterable") from exc
    seen_refs: set[str] = set()
    for row in normalized:
        if type(row) is not ResearchStrategySourceConfidenceCostAlignmentRow:
            raise ValueError(
                "rows must contain ResearchStrategySourceConfidenceCostAlignmentRow values",
            )
        _require_hard_flags("row", row)
        _verify_digest(row)
        if row.candidate_id in seen_refs:
            raise ValueError("rows must not contain duplicate candidate_id values")
        seen_refs.add(row.candidate_id)
    return tuple(sorted(normalized, key=_row_sort_key))


def _normalize_reason_code_counts(
    counts: Iterable[ResearchStrategySourceConfidenceCostAlignmentReasonCodeCount],
) -> tuple[ResearchStrategySourceConfidenceCostAlignmentReasonCodeCount, ...]:
    if isinstance(counts, (str, bytes)):
        raise ValueError("reason_code_counts must be an iterable")
    try:
        normalized = tuple(counts)
    except TypeError as exc:
        raise ValueError("reason_code_counts must be an iterable") from exc
    for count in normalized:
        if type(count) is not ResearchStrategySourceConfidenceCostAlignmentReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "ResearchStrategySourceConfidenceCostAlignmentReasonCodeCount values",
            )
        _require_hard_flags("reason_code_count", count)
    return tuple(sorted(normalized, key=lambda item: item.reason_code))


def _validate_row_consistency(row: ResearchStrategySourceConfidenceCostAlignmentRow) -> None:
    expected_raw_edge = _subtract_decimal(row.forecast_probability, row.market_probability)
    if row.raw_probability_edge != expected_raw_edge:
        raise ValueError("raw_probability_edge does not match probabilities")
    if row.absolute_probability_edge != _absolute_decimal(expected_raw_edge):
        raise ValueError("absolute_probability_edge does not match raw edge")
    expected_total_cost = _sum_probabilities(
        (
            row.fee_cost_pressure_score,
            row.spread_cost_pressure_score,
            row.liquidity_cost_pressure_score,
        ),
    )
    if row.total_cost_pressure_score != expected_total_cost:
        raise ValueError("total_cost_pressure_score does not match cost inputs")
    expected_alignment = _alignment_score(
        sanitized_source_confidence_score=row.sanitized_source_confidence_score,
        probability_edge_strength_score=row.probability_edge_strength_score,
        cost_pressure_safety_score=row.cost_pressure_safety_score,
    )
    if row.alignment_score != expected_alignment:
        raise ValueError("alignment_score does not match row inputs")
    if row.reason_codes[0] != f"source_confidence_cost_alignment_{row.status}":
        raise ValueError("reason_codes must match status")
    if row.status == "pass" and not all(code.endswith("_pass") for code in row.reason_codes):
        raise ValueError("pass rows must only contain pass reason codes")
    if row.status == "watch" and not any(code.endswith("_watch") for code in row.reason_codes):
        raise ValueError("watch rows must contain watch reason code")
    if row.status == "block" and not any(code.endswith("_block") for code in row.reason_codes):
        raise ValueError("block rows must contain block reason code")


def _validate_report_consistency(
    report: ResearchStrategySourceConfidenceCostAlignmentReport,
) -> None:
    if report.input_count != _count(len(report.rows)):
        raise ValueError("input_count must match rows")
    if report.pass_count != _status_count(report.rows, "pass"):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _status_count(report.rows, "watch"):
        raise ValueError("watch_count must match rows")
    if report.block_count != _status_count(report.rows, "block"):
        raise ValueError("block_count must match rows")
    if report.mean_sanitized_source_confidence_score != _mean(
        tuple(row.sanitized_source_confidence_score for row in report.rows),
    ):
        raise ValueError("mean_sanitized_source_confidence_score must match rows")
    if report.mean_absolute_probability_edge != _mean(
        tuple(row.absolute_probability_edge for row in report.rows),
    ):
        raise ValueError("mean_absolute_probability_edge must match rows")
    if report.mean_total_cost_pressure_score != _mean(
        tuple(row.total_cost_pressure_score for row in report.rows),
    ):
        raise ValueError("mean_total_cost_pressure_score must match rows")
    if report.mean_alignment_score != _mean(tuple(row.alignment_score for row in report.rows)):
        raise ValueError("mean_alignment_score must match rows")
    if report.status != _report_status(report.rows):
        raise ValueError("status must match rows")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")
    if report.reason_code_counts != _reason_code_counts_from_rows(report.rows):
        raise ValueError("reason_code_counts must match rows")


def _row_sort_key(
    row: ResearchStrategySourceConfidenceCostAlignmentRow,
) -> tuple[int, Decimal, Decimal, Decimal, str]:
    return (
        {"block": 0, "watch": 1, "pass": 2}[row.status],
        row.alignment_score,
        -row.total_cost_pressure_score,
        row.sanitized_source_confidence_score,
        row.candidate_id,
    )


def _status_count(
    rows: tuple[ResearchStrategySourceConfidenceCostAlignmentRow, ...],
    status: str,
) -> Decimal:
    return _count(sum(1 for row in rows if row.status == status))


def _mean(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return ZERO.quantize(QUANTUM)
    with localcontext(DECIMAL_CONTEXT):
        return _normalize_decimal("mean", sum(values, ZERO) / Decimal(len(values)))


def _ratio(count: int, total: int) -> Decimal:
    if total <= 0:
        return ZERO.quantize(QUANTUM)
    with localcontext(DECIMAL_CONTEXT):
        return _normalize_probability("input_ratio", Decimal(count) / Decimal(total))


def _sum_probabilities(values: tuple[Decimal, ...]) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return _normalize_probability("sum", sum(values, ZERO))


def _subtract_decimal(left: Decimal, right: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return _normalize_decimal("difference", left - right)


def _absolute_decimal(value: Decimal) -> Decimal:
    return _normalize_probability("absolute_value", abs(value))


def _count(value: int) -> Decimal:
    if type(value) is not int:
        raise ValueError("count source must be an int")
    if value < 0:
        raise ValueError("count source must be nonnegative")
    return Decimal(value).quantize(QUANTUM)


def _json_ready(value: object) -> object:
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, datetime):
        return value.isoformat()
    if is_dataclass(value) and not isinstance(value, type):
        return _json_ready(asdict(value))
    if isinstance(value, tuple):
        return [_json_ready(item) for item in value]
    if isinstance(value, list):
        return [_json_ready(item) for item in value]
    if isinstance(value, dict):
        return {str(key): _json_ready(item) for key, item in value.items()}
    return value


def _apply_or_verify_digest(value: object) -> None:
    expected = _derived_digest(value)
    provided = getattr(value, "derived_validation_digest", None)
    if provided == "":
        object.__setattr__(value, "derived_validation_digest", expected)
        return
    _require_digest("derived_validation_digest", provided)
    if provided != expected:
        raise ValueError("derived_validation_digest does not match derived fields")


def _verify_digest(value: object) -> None:
    _require_digest("derived_validation_digest", getattr(value, "derived_validation_digest", None))
    if getattr(value, "derived_validation_digest") != _derived_digest(value):
        raise ValueError("derived_validation_digest does not match derived fields")


def _derived_digest(value: object) -> str:
    digest_input = asdict(value)
    digest_input.pop("derived_validation_digest", None)
    encoded = dumps(
        _json_ready(digest_input),
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    ).encode("utf-8")
    return sha256(encoded).hexdigest()


def _public_payload_digest(payload: dict[str, Any]) -> str:
    digest_input = dict(payload)
    digest_input.pop("derived_validation_digest", None)
    encoded = dumps(
        _json_ready(digest_input),
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    ).encode("utf-8")
    return sha256(encoded).hexdigest()


def _verify_report_integrity(report: ResearchStrategySourceConfidenceCostAlignmentReport) -> None:
    _verify_digest(report)
    for row in report.rows:
        _verify_digest(row)


def _verify_public_payload_integrity(payload: dict[str, Any]) -> None:
    _validate_public_report_payload(payload)
    _verify_public_payload_digest("payload", payload)
    rows = payload.get("rows", [])
    if not isinstance(rows, list):
        raise ValueError("payload rows must be a list")
    for index, row in enumerate(rows):
        if not isinstance(row, dict):
            raise ValueError("payload rows must contain objects")
        _verify_public_payload_digest(f"payload.rows[{index}]", row)


def _validate_public_report_payload(payload: dict[str, Any]) -> None:
    _require_exact_public_keys("payload", payload, _REPORT_PUBLIC_PAYLOAD_KEYS)
    _require_canonical_string("generated_at", payload["generated_at"])
    _require_canonical_string("config_version", payload["config_version"])
    for field_name in ("input_count", "pass_count", "watch_count", "block_count"):
        _require_public_decimal_string(field_name, payload[field_name], nonnegative=True)
    for field_name in (
        "mean_sanitized_source_confidence_score",
        "mean_absolute_probability_edge",
        "mean_total_cost_pressure_score",
        "mean_alignment_score",
    ):
        _require_public_decimal_string(field_name, payload[field_name], probability=True)
    _require_status("status", payload["status"])
    _require_public_reason_codes("reason_codes", payload["reason_codes"], REPORT_REASON_CODES)
    reason_code_counts = payload["reason_code_counts"]
    if type(reason_code_counts) is not list:
        raise ValueError("reason_code_counts must be a list")
    for index, value in enumerate(reason_code_counts):
        _validate_public_reason_code_count_payload(index, value)
    rows = payload["rows"]
    if type(rows) is not list:
        raise ValueError("rows must be a list")
    for index, value in enumerate(rows):
        _validate_public_row_payload(index, value)


def _validate_public_reason_code_count_payload(index: int, value: object) -> None:
    if type(value) is not dict:
        raise ValueError("reason_code_counts must contain public objects")
    label = f"reason_code_counts[{index}]"
    _require_exact_public_keys(label, value, _REASON_CODE_COUNT_PUBLIC_PAYLOAD_KEYS)
    _require_reason_code("reason_code", value["reason_code"])
    _require_public_decimal_string(f"{label}.count", value["count"], nonnegative=True)
    _require_public_decimal_string(f"{label}.input_ratio", value["input_ratio"], probability=True)
    _require_hard_flags(label, _DictFlags(value))


def _validate_public_row_payload(index: int, value: object) -> None:
    if type(value) is not dict:
        raise ValueError("rows must contain public objects")
    label = f"rows[{index}]"
    _require_exact_public_keys(label, value, _ROW_PUBLIC_PAYLOAD_KEYS)
    _require_canonical_string(f"{label}.observed_at", value["observed_at"])
    for field_name in (
        "sanitized_source_confidence_score",
        "forecast_probability",
        "market_probability",
        "absolute_probability_edge",
        "probability_edge_strength_score",
        "fee_cost_pressure_score",
        "spread_cost_pressure_score",
        "liquidity_cost_pressure_score",
        "total_cost_pressure_score",
        "cost_pressure_safety_score",
        "alignment_score",
    ):
        _require_public_decimal_string(f"{label}.{field_name}", value[field_name], probability=True)
    _require_public_decimal_string(f"{label}.raw_probability_edge", value["raw_probability_edge"])
    _require_public_decimal_string(f"{label}.row_number", value["row_number"], nonnegative=True)
    _require_status(f"{label}.status", value["status"])
    _require_public_reason_codes(f"{label}.reason_codes", value["reason_codes"], ROW_REASON_CODES)
    _require_hard_flags(label, _DictFlags(value))


def _require_exact_public_keys(
    label: str,
    payload: dict[str, Any],
    allowed_keys: frozenset[str],
) -> None:
    actual_keys = set(payload)
    unexpected_keys = sorted(actual_keys - allowed_keys)
    if unexpected_keys:
        raise ValueError(f"{label} contains unexpected public field: {unexpected_keys[0]}")
    missing_keys = sorted(allowed_keys - actual_keys)
    if missing_keys:
        raise ValueError(f"{label} is missing public field: {missing_keys[0]}")


def _require_public_reason_codes(
    field_name: str,
    values: object,
    allowed: tuple[str, ...],
) -> None:
    if type(values) is not list:
        raise ValueError(f"{field_name} must be a list")
    _normalize_reason_codes(field_name, tuple(values), allowed)


def _require_public_decimal_string(
    field_name: str,
    value: object,
    *,
    probability: bool = False,
    nonnegative: bool = False,
) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a Decimal string")
    try:
        decimal = Decimal(value)
    except Exception as exc:
        raise ValueError(f"{field_name} must be a Decimal string") from exc
    if probability:
        normalized = _normalize_probability(field_name, decimal)
    elif nonnegative:
        normalized = _normalize_nonnegative_count(field_name, decimal)
    else:
        normalized = _normalize_decimal(field_name, decimal)
    if str(normalized) != value:
        raise ValueError(f"{field_name} must be a canonical Decimal string")


def _verify_public_payload_digest(label: str, payload: dict[str, Any]) -> None:
    provided = payload.get("derived_validation_digest")
    _require_digest(f"{label}.derived_validation_digest", provided)
    expected = _public_payload_digest(payload)
    if provided != expected:
        raise ValueError("derived_validation_digest does not match public payload")


def _reject_unsafe_public_payload(label: str, value: object, path: str = "$") -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            _reject_unsafe_public_key(label, key, path)
            if key in {"paper_only", "report_only", "readonly"} and item is not True:
                raise ValueError(f"{label} unsafe phase flag at {path}.{key}")
            _reject_unsafe_public_payload(label, item, f"{path}.{key}")
        return
    if isinstance(value, list):
        for index, item in enumerate(value):
            _reject_unsafe_public_payload(label, item, f"{path}[{index}]")
        return
    if isinstance(value, tuple):
        for index, item in enumerate(value):
            _reject_unsafe_public_payload(label, item, f"{path}[{index}]")
        return
    if isinstance(value, str):
        _reject_unsafe_public_value(label, value, path)


def _reject_unsafe_public_key(label: str, key: object, path: str) -> None:
    if type(key) is not str:
        raise ValueError(f"{label} unsafe non-string key at {path}")
    lowered = key.lower()
    if any(fragment in lowered for fragment in _PRIVATE_PUBLIC_KEY_FRAGMENTS):
        raise ValueError(f"{label} unsafe public key at {path}.{key}")


def _reject_unsafe_public_value(label: str, value: str, path: str) -> None:
    lowered = value.lower()
    if any(fragment in lowered for fragment in _PRIVATE_PUBLIC_VALUE_FRAGMENTS):
        raise ValueError(f"{label} unsafe public value at {path}")


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _normalize_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    try:
        return value.quantize(QUANTUM, rounding=ROUND_HALF_EVEN)
    except Exception as exc:
        raise ValueError(f"{field_name} must be finite") from exc


def _normalize_probability(field_name: str, value: object) -> Decimal:
    decimal = _normalize_decimal(field_name, value)
    if decimal < ZERO or decimal > ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return decimal


def _normalize_nonnegative_count(field_name: str, value: object) -> Decimal:
    decimal = _normalize_decimal(field_name, value)
    if decimal < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return decimal


def _normalize_reason_codes(
    field_name: str,
    values: object,
    allowed: tuple[str, ...],
) -> tuple[str, ...]:
    if type(values) is not tuple:
        raise ValueError(f"{field_name} must be a tuple")
    for value in values:
        _require_reason_code(field_name, value)
        if value not in allowed:
            raise ValueError(f"{field_name} contains unsupported reason code")
    if not values:
        raise ValueError(f"{field_name} must be nonempty")
    if len(set(values)) != len(values):
        raise ValueError(f"{field_name} must not contain duplicates")
    return values


def _require_reason_code(field_name: str, value: object) -> None:
    if type(value) is not str or not value:
        raise ValueError(f"{field_name} must contain canonical reason codes")
    if value.strip() != value or value.lower() != value or " " in value:
        raise ValueError(f"{field_name} must contain canonical reason codes")
    if value not in REASON_CODES:
        raise ValueError(f"{field_name} contains unsupported reason code")


def _require_status(field_name: str, value: object) -> None:
    if value not in RESEARCH_STRATEGY_SOURCE_CONFIDENCE_COST_ALIGNMENT_REPORT_STATUSES:
        raise ValueError(f"{field_name} must be pass, watch, or block")


def _require_hard_flags(field_name: str, value: object) -> None:
    if getattr(value, "paper_only", None) is not True:
        raise ValueError(f"{field_name} must be paper_only")
    if getattr(value, "report_only", None) is not True:
        raise ValueError(f"{field_name} must be report_only")
    if getattr(value, "readonly", None) is not True:
        raise ValueError(f"{field_name} must be readonly")


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str or not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a nonempty canonical string")


def _require_private_string(field_name: str, value: object) -> None:
    if type(value) is not str or not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a nonempty private string")


def _require_floor_pair(field_name: str, pass_floor: Decimal, watch_floor: Decimal) -> None:
    if pass_floor <= watch_floor:
        raise ValueError(f"{field_name}_pass_floor must exceed {field_name}_watch_floor")


def _require_ceiling_pair(
    field_name: str,
    pass_ceiling: Decimal,
    watch_ceiling: Decimal,
) -> None:
    if pass_ceiling >= watch_ceiling:
        raise ValueError(f"{field_name}_pass_ceiling must be below {field_name}_watch_ceiling")


def _require_digest(field_name: str, value: object) -> None:
    if type(value) is not str or len(value) != 64:
        raise ValueError(f"{field_name} must be a sha256 hex digest")
    if any(character not in _HEX_CHARS for character in value):
        raise ValueError(f"{field_name} must be a sha256 hex digest")


__all__ = (
    "DEFAULT_RESEARCH_STRATEGY_SOURCE_CONFIDENCE_COST_ALIGNMENT_REPORT_CONFIG_VERSION",
    "RESEARCH_STRATEGY_SOURCE_CONFIDENCE_COST_ALIGNMENT_REPORT_STATUSES",
    "ResearchStrategySourceConfidenceCostAlignmentConfig",
    "ResearchStrategySourceConfidenceCostAlignmentInput",
    "ResearchStrategySourceConfidenceCostAlignmentReasonCodeCount",
    "ResearchStrategySourceConfidenceCostAlignmentRow",
    "ResearchStrategySourceConfidenceCostAlignmentReport",
    "build_research_strategy_source_confidence_cost_alignment_report",
    "research_strategy_source_confidence_cost_alignment_report_payload",
)
