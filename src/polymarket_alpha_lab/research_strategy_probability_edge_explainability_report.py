"""Report-only probability edge explainability review."""

from __future__ import annotations

from collections import Counter
from dataclasses import InitVar, asdict, dataclass, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal, ROUND_HALF_UP
from hashlib import sha256
import json
import re
from typing import Any, Sequence


DEFAULT_RESEARCH_STRATEGY_PROBABILITY_EDGE_EXPLAINABILITY_REPORT_CONFIG_VERSION = (
    "research-strategy-probability-edge-explainability-report-v0"
)
RESEARCH_STRATEGY_PROBABILITY_EDGE_EXPLAINABILITY_STATUSES = (
    "pass",
    "watch",
    "block",
)

STATUS_PASS = "pass"
STATUS_WATCH = "watch"
STATUS_BLOCK = "block"

REASON_EMPTY_INPUT = "empty_input"
REASON_EVIDENCE_QUALITY_BLOCK = "evidence_quality_block"
REASON_MODEL_CONFIDENCE_BLOCK = "model_confidence_block"
REASON_MARKET_DIVERGENCE_BLOCK = "market_divergence_block"
REASON_COST_DRAG_BLOCK = "cost_drag_block"
REASON_LIQUIDITY_QUALITY_BLOCK = "liquidity_quality_block"
REASON_RESOLUTION_CLARITY_BLOCK = "resolution_clarity_block"
REASON_EXPLAINABILITY_SCORE_BLOCK = "explainability_score_block"
REASON_EVIDENCE_QUALITY_WATCH = "evidence_quality_watch"
REASON_MODEL_CONFIDENCE_WATCH = "model_confidence_watch"
REASON_MARKET_DIVERGENCE_WATCH = "market_divergence_watch"
REASON_COST_DRAG_WATCH = "cost_drag_watch"
REASON_LIQUIDITY_QUALITY_WATCH = "liquidity_quality_watch"
REASON_RESOLUTION_CLARITY_WATCH = "resolution_clarity_watch"
REASON_EXPLAINABILITY_SCORE_WATCH = "explainability_score_watch"
REASON_EXPLAINABILITY_PASS = "probability_edge_explainability_pass"

_ROW_REASON_CODE_SEQUENCE = (
    REASON_EVIDENCE_QUALITY_BLOCK,
    REASON_MODEL_CONFIDENCE_BLOCK,
    REASON_MARKET_DIVERGENCE_BLOCK,
    REASON_COST_DRAG_BLOCK,
    REASON_LIQUIDITY_QUALITY_BLOCK,
    REASON_RESOLUTION_CLARITY_BLOCK,
    REASON_EXPLAINABILITY_SCORE_BLOCK,
    REASON_EVIDENCE_QUALITY_WATCH,
    REASON_MODEL_CONFIDENCE_WATCH,
    REASON_MARKET_DIVERGENCE_WATCH,
    REASON_COST_DRAG_WATCH,
    REASON_LIQUIDITY_QUALITY_WATCH,
    REASON_RESOLUTION_CLARITY_WATCH,
    REASON_EXPLAINABILITY_SCORE_WATCH,
    REASON_EXPLAINABILITY_PASS,
)
_REASON_CODE_SEQUENCE = (REASON_EMPTY_INPUT, *_ROW_REASON_CODE_SEQUENCE)
_BLOCK_REASON_CODES = frozenset(
    (
        REASON_EVIDENCE_QUALITY_BLOCK,
        REASON_MODEL_CONFIDENCE_BLOCK,
        REASON_MARKET_DIVERGENCE_BLOCK,
        REASON_COST_DRAG_BLOCK,
        REASON_LIQUIDITY_QUALITY_BLOCK,
        REASON_RESOLUTION_CLARITY_BLOCK,
        REASON_EXPLAINABILITY_SCORE_BLOCK,
    ),
)

_QUANT = Decimal("0.000001")
_ZERO = Decimal("0.000000")
_ONE = Decimal("1.000000")
_DIGEST_FIELD = "derived_validation_digest"
_STATUS_VALUES = frozenset(RESEARCH_STRATEGY_PROBABILITY_EDGE_EXPLAINABILITY_STATUSES)
_PHASE_FLAG_FIELDS = frozenset(("paper_only", "report_only", "readonly"))
_PUBLIC_IDENTIFIER_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,127}$")
_DIGEST_RE = re.compile(r"^[0-9a-f]{64}$")
_PRIVATE_DIGEST_RE = re.compile(r"^sha256:[0-9a-f]{64}$")
_UNSAFE_PUBLIC_FRAGMENTS = (
    "candidate",
    "condition_id",
    "market_id",
    "market_slug",
    "slug",
    "question",
    "source_url",
    "source-url",
    "source url",
    "source_text",
    "source-text",
    "source text",
    "url",
    "dsn",
    "database",
    "table",
    "token",
    "wallet",
    "auth",
    "order",
    "trade",
    "live",
    "position",
    "sizing",
    "buy",
    "sell",
    "recommend",
    "private key",
    "http://",
    "https://",
    "://",
)


class _FinalPublicDataclass:
    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        for base in cls.__bases__:
            if base is not _FinalPublicDataclass and issubclass(
                base,
                _FinalPublicDataclass,
            ):
                raise TypeError(f"{base.__name__} may not be subclassed")


@dataclass(frozen=True)
class ResearchStrategyProbabilityEdgeExplainabilityConfig(_FinalPublicDataclass):
    config_version: str = (
        DEFAULT_RESEARCH_STRATEGY_PROBABILITY_EDGE_EXPLAINABILITY_REPORT_CONFIG_VERSION
    )
    pass_min_explainability_score: Decimal = Decimal("0.800000")
    watch_min_explainability_score: Decimal = Decimal("0.600000")
    min_pass_evidence_quality_score: Decimal = Decimal("0.750000")
    min_watch_evidence_quality_score: Decimal = Decimal("0.500000")
    min_pass_model_confidence_score: Decimal = Decimal("0.750000")
    min_watch_model_confidence_score: Decimal = Decimal("0.500000")
    min_pass_market_divergence_score: Decimal = Decimal("0.700000")
    min_watch_market_divergence_score: Decimal = Decimal("0.450000")
    max_pass_cost_drag_score: Decimal = Decimal("0.150000")
    max_watch_cost_drag_score: Decimal = Decimal("0.350000")
    min_pass_liquidity_quality_score: Decimal = Decimal("0.750000")
    min_watch_liquidity_quality_score: Decimal = Decimal("0.500000")
    min_pass_resolution_clarity_score: Decimal = Decimal("0.750000")
    min_watch_resolution_clarity_score: Decimal = Decimal("0.500000")
    evidence_quality_weight: Decimal = Decimal("0.250000")
    model_confidence_weight: Decimal = Decimal("0.200000")
    market_divergence_weight: Decimal = Decimal("0.200000")
    cost_drag_quality_weight: Decimal = Decimal("0.150000")
    liquidity_quality_weight: Decimal = Decimal("0.100000")
    resolution_clarity_weight: Decimal = Decimal("0.100000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchStrategyProbabilityEdgeExplainabilityConfig,
            "config",
        )
        object.__setattr__(
            self,
            "config_version",
            _require_public_identifier("config_version", self.config_version),
        )
        if (
            self.config_version
            != DEFAULT_RESEARCH_STRATEGY_PROBABILITY_EDGE_EXPLAINABILITY_REPORT_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "pass_min_explainability_score",
            "watch_min_explainability_score",
            "min_pass_evidence_quality_score",
            "min_watch_evidence_quality_score",
            "min_pass_model_confidence_score",
            "min_watch_model_confidence_score",
            "min_pass_market_divergence_score",
            "min_watch_market_divergence_score",
            "max_pass_cost_drag_score",
            "max_watch_cost_drag_score",
            "min_pass_liquidity_quality_score",
            "min_watch_liquidity_quality_score",
            "min_pass_resolution_clarity_score",
            "min_watch_resolution_clarity_score",
            "evidence_quality_weight",
            "model_confidence_weight",
            "market_divergence_weight",
            "cost_drag_quality_weight",
            "liquidity_quality_weight",
            "resolution_clarity_weight",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        if self.pass_min_explainability_score < self.watch_min_explainability_score:
            raise ValueError(
                "pass_min_explainability_score must be at least "
                "watch_min_explainability_score",
            )
        _require_floor_pair(
            "min_pass_evidence_quality_score",
            self.min_pass_evidence_quality_score,
            "min_watch_evidence_quality_score",
            self.min_watch_evidence_quality_score,
        )
        _require_floor_pair(
            "min_pass_model_confidence_score",
            self.min_pass_model_confidence_score,
            "min_watch_model_confidence_score",
            self.min_watch_model_confidence_score,
        )
        _require_floor_pair(
            "min_pass_market_divergence_score",
            self.min_pass_market_divergence_score,
            "min_watch_market_divergence_score",
            self.min_watch_market_divergence_score,
        )
        _require_floor_pair(
            "min_pass_liquidity_quality_score",
            self.min_pass_liquidity_quality_score,
            "min_watch_liquidity_quality_score",
            self.min_watch_liquidity_quality_score,
        )
        _require_floor_pair(
            "min_pass_resolution_clarity_score",
            self.min_pass_resolution_clarity_score,
            "min_watch_resolution_clarity_score",
            self.min_watch_resolution_clarity_score,
        )
        if self.max_pass_cost_drag_score > self.max_watch_cost_drag_score:
            raise ValueError(
                "max_pass_cost_drag_score must not exceed max_watch_cost_drag_score",
            )
        weight_sum = _quantize(
            self.evidence_quality_weight
            + self.model_confidence_weight
            + self.market_divergence_weight
            + self.cost_drag_quality_weight
            + self.liquidity_quality_weight
            + self.resolution_clarity_weight,
        )
        if weight_sum != _ONE:
            raise ValueError("explainability weights must sum to one")
        _require_hard_flags("config", self)
        _reject_unsafe_public_payload("config", self)


@dataclass(frozen=True)
class ResearchStrategyProbabilityEdgeExplainabilityInput(_FinalPublicDataclass):
    edge_ref: str
    evidence_quality_score: Decimal
    model_confidence_score: Decimal
    market_divergence_score: Decimal
    cost_drag_score: Decimal
    liquidity_quality_score: Decimal
    resolution_clarity_score: Decimal
    observed_at: datetime
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchStrategyProbabilityEdgeExplainabilityInput, "input")
        object.__setattr__(
            self,
            "edge_ref",
            _require_private_ref("edge_ref", self.edge_ref),
        )
        for field_name in (
            "evidence_quality_score",
            "model_confidence_score",
            "market_divergence_score",
            "cost_drag_score",
            "liquidity_quality_score",
            "resolution_clarity_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        _require_hard_flags("input", self)


@dataclass(frozen=True)
class ResearchStrategyProbabilityEdgeExplainabilityRow(_FinalPublicDataclass):
    edge_digest: str
    evidence_quality_score: Decimal
    model_confidence_score: Decimal
    market_divergence_score: Decimal
    cost_drag_score: Decimal
    cost_drag_quality_score: Decimal
    liquidity_quality_score: Decimal
    resolution_clarity_score: Decimal
    explainability_score: Decimal
    observed_at: datetime
    status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True
    validation_config: InitVar[
        ResearchStrategyProbabilityEdgeExplainabilityConfig | None
    ] = None

    def __post_init__(
        self,
        validation_config: (
            ResearchStrategyProbabilityEdgeExplainabilityConfig | None
        ),
    ) -> None:
        _require_exact_type(self, ResearchStrategyProbabilityEdgeExplainabilityRow, "row")
        object.__setattr__(
            self,
            "edge_digest",
            _require_private_digest("edge_digest", self.edge_digest),
        )
        for field_name in (
            "evidence_quality_score",
            "model_confidence_score",
            "market_divergence_score",
            "cost_drag_score",
            "cost_drag_quality_score",
            "liquidity_quality_score",
            "resolution_clarity_score",
            "explainability_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        _require_status("status", self.status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_row_reason_codes(self.reason_codes),
        )
        _validate_row(self, validation_config)
        _require_hard_flags("row", self)
        _reject_unsafe_public_payload("row", self)


@dataclass(frozen=True)
class ResearchStrategyProbabilityEdgeExplainabilityReasonCodeCount(
    _FinalPublicDataclass,
):
    reason_code: str
    count: Decimal
    row_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchStrategyProbabilityEdgeExplainabilityReasonCodeCount,
            "reason count",
        )
        _require_reason_code("reason_code", self.reason_code, _REASON_CODE_SEQUENCE)
        object.__setattr__(
            self,
            "count",
            _require_nonnegative_count_decimal("count", self.count),
        )
        object.__setattr__(
            self,
            "row_ratio",
            _require_ratio_decimal("row_ratio", self.row_ratio),
        )
        _require_hard_flags("reason count", self)
        _reject_unsafe_public_payload("reason count", self)


@dataclass(frozen=True)
class ResearchStrategyProbabilityEdgeExplainabilityReport(_FinalPublicDataclass):
    generated_at: datetime
    config_version: str
    status: str
    row_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    average_explainability_score: Decimal
    min_explainability_score: Decimal
    min_evidence_quality_score: Decimal
    min_model_confidence_score: Decimal
    min_market_divergence_score: Decimal
    max_cost_drag_score: Decimal
    min_liquidity_quality_score: Decimal
    min_resolution_clarity_score: Decimal
    rows: tuple[ResearchStrategyProbabilityEdgeExplainabilityRow, ...]
    reason_code_counts: tuple[
        ResearchStrategyProbabilityEdgeExplainabilityReasonCodeCount,
        ...,
    ]
    reason_codes: tuple[str, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchStrategyProbabilityEdgeExplainabilityReport, "report")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        object.__setattr__(
            self,
            "config_version",
            _require_public_identifier("config_version", self.config_version),
        )
        if (
            self.config_version
            != DEFAULT_RESEARCH_STRATEGY_PROBABILITY_EDGE_EXPLAINABILITY_REPORT_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        _require_status("status", self.status)
        for field_name in ("row_count", "pass_count", "watch_count", "block_count"):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_count_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "average_explainability_score",
            "min_explainability_score",
            "min_evidence_quality_score",
            "min_model_confidence_score",
            "min_market_divergence_score",
            "max_cost_drag_score",
            "min_liquidity_quality_score",
            "min_resolution_clarity_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
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
            _normalize_report_reason_codes(self.reason_codes),
        )
        _validate_report(self)
        _require_hard_flags("report", self)
        _reject_unsafe_public_payload("report", self)
        expected_digest = _report_digest(self)
        if self.derived_validation_digest == "":
            object.__setattr__(self, _DIGEST_FIELD, expected_digest)
        elif self.derived_validation_digest != expected_digest:
            raise ValueError("derived_validation_digest mismatch")
        _require_digest(_DIGEST_FIELD, self.derived_validation_digest)

    @property
    def payload(self) -> dict[str, object]:
        return research_strategy_probability_edge_explainability_report_payload(self)


def build_research_strategy_probability_edge_explainability_report(
    inputs: Sequence[ResearchStrategyProbabilityEdgeExplainabilityInput],
    *,
    generated_at: datetime,
    config: ResearchStrategyProbabilityEdgeExplainabilityConfig | None = None,
) -> ResearchStrategyProbabilityEdgeExplainabilityReport:
    """Build a deterministic, readonly probability edge explainability report."""

    cfg = config or ResearchStrategyProbabilityEdgeExplainabilityConfig()
    if type(cfg) is not ResearchStrategyProbabilityEdgeExplainabilityConfig:
        raise ValueError(
            "config must be a ResearchStrategyProbabilityEdgeExplainabilityConfig",
        )
    _require_hard_flags("config", cfg)
    report_time = _as_utc("generated_at", generated_at)
    normalized_inputs = _normalize_inputs(inputs)
    for row in normalized_inputs:
        if row.observed_at > report_time:
            raise ValueError("observed_at must not be after generated_at")
    rows = tuple(
        sorted(
            (_row_for_input(row, cfg) for row in normalized_inputs),
            key=_row_sort_key,
        ),
    )
    reason_code_counts = _reason_code_counts(rows)
    reason_codes = tuple(row.reason_code for row in reason_code_counts)
    if not rows:
        reason_code_counts = (
            ResearchStrategyProbabilityEdgeExplainabilityReasonCodeCount(
                reason_code=REASON_EMPTY_INPUT,
                count=_ONE,
                row_ratio=_ONE,
            ),
        )
        reason_codes = (REASON_EMPTY_INPUT,)
    values: dict[str, object] = {
        "generated_at": report_time,
        "config_version": cfg.config_version,
        "status": _report_status(rows),
        "row_count": _decimal_count(len(rows)),
        "pass_count": _decimal_count(_status_count(rows, STATUS_PASS)),
        "watch_count": _decimal_count(_status_count(rows, STATUS_WATCH)),
        "block_count": _decimal_count(_status_count(rows, STATUS_BLOCK)),
        "average_explainability_score": _average_ratio(
            tuple(row.explainability_score for row in rows),
        ),
        "min_explainability_score": min(
            (row.explainability_score for row in rows),
            default=_ZERO,
        ),
        "min_evidence_quality_score": min(
            (row.evidence_quality_score for row in rows),
            default=_ZERO,
        ),
        "min_model_confidence_score": min(
            (row.model_confidence_score for row in rows),
            default=_ZERO,
        ),
        "min_market_divergence_score": min(
            (row.market_divergence_score for row in rows),
            default=_ZERO,
        ),
        "max_cost_drag_score": max(
            (row.cost_drag_score for row in rows),
            default=_ZERO,
        ),
        "min_liquidity_quality_score": min(
            (row.liquidity_quality_score for row in rows),
            default=_ZERO,
        ),
        "min_resolution_clarity_score": min(
            (row.resolution_clarity_score for row in rows),
            default=_ZERO,
        ),
        "rows": rows,
        "reason_code_counts": reason_code_counts,
        "reason_codes": reason_codes,
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    return ResearchStrategyProbabilityEdgeExplainabilityReport(
        **values,
        derived_validation_digest=_report_digest_from_values(values),
    )


def research_strategy_probability_edge_explainability_report_payload(
    value: ResearchStrategyProbabilityEdgeExplainabilityReport | dict[str, object],
) -> dict[str, object]:
    if type(value) is ResearchStrategyProbabilityEdgeExplainabilityReport:
        _require_hard_flags("report", value)
        payload = _report_payload(value)
    elif type(value) is dict:
        payload = _copy_json_object(value)
    else:
        raise ValueError(
            "value must be a ResearchStrategyProbabilityEdgeExplainabilityReport or dict",
        )
    _validate_payload_statuses(payload)
    _reject_unsafe_public_payload("payload", payload, allow_json_containers=True)
    _validate_payload_digest(payload)
    return payload


def _row_for_input(
    row: ResearchStrategyProbabilityEdgeExplainabilityInput,
    config: ResearchStrategyProbabilityEdgeExplainabilityConfig,
) -> ResearchStrategyProbabilityEdgeExplainabilityRow:
    cost_drag_quality = _inverse_ratio(row.cost_drag_score)
    explainability_score = _explainability_score(
        evidence_quality_score=row.evidence_quality_score,
        model_confidence_score=row.model_confidence_score,
        market_divergence_score=row.market_divergence_score,
        cost_drag_quality_score=cost_drag_quality,
        liquidity_quality_score=row.liquidity_quality_score,
        resolution_clarity_score=row.resolution_clarity_score,
        config=config,
    )
    reason_codes = _row_reason_codes(
        evidence_quality_score=row.evidence_quality_score,
        model_confidence_score=row.model_confidence_score,
        market_divergence_score=row.market_divergence_score,
        cost_drag_score=row.cost_drag_score,
        liquidity_quality_score=row.liquidity_quality_score,
        resolution_clarity_score=row.resolution_clarity_score,
        explainability_score=explainability_score,
        config=config,
    )
    return ResearchStrategyProbabilityEdgeExplainabilityRow(
        edge_digest=_private_ref_digest(row.edge_ref),
        evidence_quality_score=row.evidence_quality_score,
        model_confidence_score=row.model_confidence_score,
        market_divergence_score=row.market_divergence_score,
        cost_drag_score=row.cost_drag_score,
        cost_drag_quality_score=cost_drag_quality,
        liquidity_quality_score=row.liquidity_quality_score,
        resolution_clarity_score=row.resolution_clarity_score,
        explainability_score=explainability_score,
        observed_at=row.observed_at,
        status=_row_status(reason_codes),
        reason_codes=reason_codes,
        validation_config=config,
    )


def _row_reason_codes(
    *,
    evidence_quality_score: Decimal,
    model_confidence_score: Decimal,
    market_divergence_score: Decimal,
    cost_drag_score: Decimal,
    liquidity_quality_score: Decimal,
    resolution_clarity_score: Decimal,
    explainability_score: Decimal,
    config: ResearchStrategyProbabilityEdgeExplainabilityConfig,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    if evidence_quality_score < config.min_watch_evidence_quality_score:
        reason_codes.append(REASON_EVIDENCE_QUALITY_BLOCK)
    elif evidence_quality_score < config.min_pass_evidence_quality_score:
        reason_codes.append(REASON_EVIDENCE_QUALITY_WATCH)
    if model_confidence_score < config.min_watch_model_confidence_score:
        reason_codes.append(REASON_MODEL_CONFIDENCE_BLOCK)
    elif model_confidence_score < config.min_pass_model_confidence_score:
        reason_codes.append(REASON_MODEL_CONFIDENCE_WATCH)
    if market_divergence_score < config.min_watch_market_divergence_score:
        reason_codes.append(REASON_MARKET_DIVERGENCE_BLOCK)
    elif market_divergence_score < config.min_pass_market_divergence_score:
        reason_codes.append(REASON_MARKET_DIVERGENCE_WATCH)
    if cost_drag_score > config.max_watch_cost_drag_score:
        reason_codes.append(REASON_COST_DRAG_BLOCK)
    elif cost_drag_score > config.max_pass_cost_drag_score:
        reason_codes.append(REASON_COST_DRAG_WATCH)
    if liquidity_quality_score < config.min_watch_liquidity_quality_score:
        reason_codes.append(REASON_LIQUIDITY_QUALITY_BLOCK)
    elif liquidity_quality_score < config.min_pass_liquidity_quality_score:
        reason_codes.append(REASON_LIQUIDITY_QUALITY_WATCH)
    if resolution_clarity_score < config.min_watch_resolution_clarity_score:
        reason_codes.append(REASON_RESOLUTION_CLARITY_BLOCK)
    elif resolution_clarity_score < config.min_pass_resolution_clarity_score:
        reason_codes.append(REASON_RESOLUTION_CLARITY_WATCH)
    if explainability_score < config.watch_min_explainability_score:
        reason_codes.append(REASON_EXPLAINABILITY_SCORE_BLOCK)
    elif explainability_score < config.pass_min_explainability_score:
        reason_codes.append(REASON_EXPLAINABILITY_SCORE_WATCH)
    if not reason_codes:
        reason_codes.append(REASON_EXPLAINABILITY_PASS)
    return _normalize_row_reason_codes(tuple(reason_codes))


def _row_status(reason_codes: tuple[str, ...]) -> str:
    if any(reason_code in _BLOCK_REASON_CODES for reason_code in reason_codes):
        return STATUS_BLOCK
    if reason_codes == (REASON_EXPLAINABILITY_PASS,):
        return STATUS_PASS
    return STATUS_WATCH


def _report_status(
    rows: tuple[ResearchStrategyProbabilityEdgeExplainabilityRow, ...],
) -> str:
    if not rows:
        return STATUS_BLOCK
    if any(row.status == STATUS_BLOCK for row in rows):
        return STATUS_BLOCK
    if any(row.status == STATUS_WATCH for row in rows):
        return STATUS_WATCH
    return STATUS_PASS


def _status_count(
    rows: tuple[ResearchStrategyProbabilityEdgeExplainabilityRow, ...],
    status: str,
) -> int:
    return sum(1 for row in rows if row.status == status)


def _row_sort_key(
    row: ResearchStrategyProbabilityEdgeExplainabilityRow,
) -> tuple[int, Decimal, str]:
    return (_status_rank(row.status), row.explainability_score, row.edge_digest)


def _status_rank(value: str) -> int:
    return {STATUS_BLOCK: 0, STATUS_WATCH: 1, STATUS_PASS: 2}[value]


def _reason_code_counts(
    rows: tuple[ResearchStrategyProbabilityEdgeExplainabilityRow, ...],
) -> tuple[ResearchStrategyProbabilityEdgeExplainabilityReasonCodeCount, ...]:
    total = _decimal_count(len(rows))
    counts: Counter[str] = Counter(
        reason_code for row in rows for reason_code in row.reason_codes
    )
    return tuple(
        ResearchStrategyProbabilityEdgeExplainabilityReasonCodeCount(
            reason_code=reason_code,
            count=_decimal_count(count),
            row_ratio=_ratio(_decimal_count(count), total),
        )
        for reason_code, count in sorted(counts.items(), key=lambda item: (-item[1], item[0]))
    )


def _explainability_score(
    *,
    evidence_quality_score: Decimal,
    model_confidence_score: Decimal,
    market_divergence_score: Decimal,
    cost_drag_quality_score: Decimal,
    liquidity_quality_score: Decimal,
    resolution_clarity_score: Decimal,
    config: ResearchStrategyProbabilityEdgeExplainabilityConfig,
) -> Decimal:
    score = (
        evidence_quality_score * config.evidence_quality_weight
        + model_confidence_score * config.model_confidence_weight
        + market_divergence_score * config.market_divergence_weight
        + cost_drag_quality_score * config.cost_drag_quality_weight
        + liquidity_quality_score * config.liquidity_quality_weight
        + resolution_clarity_score * config.resolution_clarity_weight
    )
    return _clamp_ratio(score)


def _validate_row(
    row: ResearchStrategyProbabilityEdgeExplainabilityRow,
    config: ResearchStrategyProbabilityEdgeExplainabilityConfig | None,
) -> None:
    if row.cost_drag_quality_score != _inverse_ratio(row.cost_drag_score):
        raise ValueError("cost_drag_quality_score must match cost_drag_score")
    if row.status != _row_status(row.reason_codes):
        raise ValueError("status must match reason_codes")
    if row.status == STATUS_PASS and row.reason_codes != (REASON_EXPLAINABILITY_PASS,):
        raise ValueError("reason_codes must match status")
    if REASON_EXPLAINABILITY_PASS in row.reason_codes and row.reason_codes != (
        REASON_EXPLAINABILITY_PASS,
    ):
        raise ValueError("reason_codes must not mix pass and review codes")
    if config is None:
        return
    if type(config) is not ResearchStrategyProbabilityEdgeExplainabilityConfig:
        raise ValueError(
            "validation_config must be a "
            "ResearchStrategyProbabilityEdgeExplainabilityConfig",
        )
    expected_score = _explainability_score(
        evidence_quality_score=row.evidence_quality_score,
        model_confidence_score=row.model_confidence_score,
        market_divergence_score=row.market_divergence_score,
        cost_drag_quality_score=row.cost_drag_quality_score,
        liquidity_quality_score=row.liquidity_quality_score,
        resolution_clarity_score=row.resolution_clarity_score,
        config=config,
    )
    if row.explainability_score != expected_score:
        raise ValueError("explainability_score must match component scores")
    if row.reason_codes != _row_reason_codes(
        evidence_quality_score=row.evidence_quality_score,
        model_confidence_score=row.model_confidence_score,
        market_divergence_score=row.market_divergence_score,
        cost_drag_score=row.cost_drag_score,
        liquidity_quality_score=row.liquidity_quality_score,
        resolution_clarity_score=row.resolution_clarity_score,
        explainability_score=row.explainability_score,
        config=config,
    ):
        raise ValueError("reason_codes must match component scores")


def _validate_report(report: ResearchStrategyProbabilityEdgeExplainabilityReport) -> None:
    if report.row_count != _decimal_count(len(report.rows)):
        raise ValueError("row_count must match rows")
    if report.pass_count != _decimal_count(_status_count(report.rows, STATUS_PASS)):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _decimal_count(_status_count(report.rows, STATUS_WATCH)):
        raise ValueError("watch_count must match rows")
    if report.block_count != _decimal_count(_status_count(report.rows, STATUS_BLOCK)):
        raise ValueError("block_count must match rows")
    if report.row_count != report.pass_count + report.watch_count + report.block_count:
        raise ValueError("status counts must match row_count")
    if report.average_explainability_score != _average_ratio(
        tuple(row.explainability_score for row in report.rows),
    ):
        raise ValueError("average_explainability_score must match rows")
    if report.min_explainability_score != min(
        (row.explainability_score for row in report.rows),
        default=_ZERO,
    ):
        raise ValueError("min_explainability_score must match rows")
    if report.min_evidence_quality_score != min(
        (row.evidence_quality_score for row in report.rows),
        default=_ZERO,
    ):
        raise ValueError("min_evidence_quality_score must match rows")
    if report.min_model_confidence_score != min(
        (row.model_confidence_score for row in report.rows),
        default=_ZERO,
    ):
        raise ValueError("min_model_confidence_score must match rows")
    if report.min_market_divergence_score != min(
        (row.market_divergence_score for row in report.rows),
        default=_ZERO,
    ):
        raise ValueError("min_market_divergence_score must match rows")
    if report.max_cost_drag_score != max(
        (row.cost_drag_score for row in report.rows),
        default=_ZERO,
    ):
        raise ValueError("max_cost_drag_score must match rows")
    if report.min_liquidity_quality_score != min(
        (row.liquidity_quality_score for row in report.rows),
        default=_ZERO,
    ):
        raise ValueError("min_liquidity_quality_score must match rows")
    if report.min_resolution_clarity_score != min(
        (row.resolution_clarity_score for row in report.rows),
        default=_ZERO,
    ):
        raise ValueError("min_resolution_clarity_score must match rows")
    if report.status != _report_status(report.rows):
        raise ValueError("status must match rows")
    if report.reason_code_counts != _expected_reason_code_counts(report.rows):
        raise ValueError("reason_code_counts must match rows")
    if report.reason_codes != tuple(row.reason_code for row in report.reason_code_counts):
        raise ValueError("reason_codes must match reason_code_counts")
    if tuple(sorted(report.rows, key=_row_sort_key)) != report.rows:
        raise ValueError("rows must use deterministic sequence")


def _expected_reason_code_counts(
    rows: tuple[ResearchStrategyProbabilityEdgeExplainabilityRow, ...],
) -> tuple[ResearchStrategyProbabilityEdgeExplainabilityReasonCodeCount, ...]:
    if not rows:
        return (
            ResearchStrategyProbabilityEdgeExplainabilityReasonCodeCount(
                reason_code=REASON_EMPTY_INPUT,
                count=_ONE,
                row_ratio=_ONE,
            ),
        )
    return _reason_code_counts(rows)


def _normalize_inputs(
    inputs: Sequence[ResearchStrategyProbabilityEdgeExplainabilityInput],
) -> tuple[ResearchStrategyProbabilityEdgeExplainabilityInput, ...]:
    if isinstance(inputs, (str, bytes)):
        raise ValueError("inputs must be a sequence")
    try:
        normalized = tuple(inputs)
    except TypeError as exc:
        raise ValueError("inputs must be a sequence") from exc
    seen_refs: set[str] = set()
    for row in normalized:
        if type(row) is not ResearchStrategyProbabilityEdgeExplainabilityInput:
            raise ValueError(
                "inputs must contain ResearchStrategyProbabilityEdgeExplainabilityInput values",
            )
        _require_hard_flags("input", row)
        if row.edge_ref in seen_refs:
            raise ValueError("inputs must not contain duplicate edge_ref values")
        seen_refs.add(row.edge_ref)
    return normalized


def _normalize_rows(
    rows: Sequence[ResearchStrategyProbabilityEdgeExplainabilityRow],
) -> tuple[ResearchStrategyProbabilityEdgeExplainabilityRow, ...]:
    if isinstance(rows, (str, bytes)):
        raise ValueError("rows must be a sequence")
    try:
        normalized = tuple(rows)
    except TypeError as exc:
        raise ValueError("rows must be a sequence") from exc
    seen_digests: set[str] = set()
    for row in normalized:
        if type(row) is not ResearchStrategyProbabilityEdgeExplainabilityRow:
            raise ValueError(
                "rows must contain ResearchStrategyProbabilityEdgeExplainabilityRow values",
            )
        _require_hard_flags("row", row)
        if row.edge_digest in seen_digests:
            raise ValueError("rows must not contain duplicate edge_digest values")
        seen_digests.add(row.edge_digest)
    return normalized


def _normalize_reason_code_counts(
    rows: Sequence[ResearchStrategyProbabilityEdgeExplainabilityReasonCodeCount],
) -> tuple[ResearchStrategyProbabilityEdgeExplainabilityReasonCodeCount, ...]:
    if isinstance(rows, (str, bytes)):
        raise ValueError("reason_code_counts must be a sequence")
    try:
        normalized = tuple(rows)
    except TypeError as exc:
        raise ValueError("reason_code_counts must be a sequence") from exc
    for row in normalized:
        if type(row) is not ResearchStrategyProbabilityEdgeExplainabilityReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "ResearchStrategyProbabilityEdgeExplainabilityReasonCodeCount values",
            )
        _require_hard_flags("reason count", row)
    return normalized


def _normalize_row_reason_codes(value: tuple[str, ...]) -> tuple[str, ...]:
    return _normalize_reason_codes("reason_codes", value, _ROW_REASON_CODE_SEQUENCE)


def _normalize_report_reason_codes(value: tuple[str, ...]) -> tuple[str, ...]:
    return _normalize_reason_codes("reason_codes", value, _REASON_CODE_SEQUENCE)


def _normalize_reason_codes(
    name: str,
    value: tuple[str, ...],
    supported: tuple[str, ...],
) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ValueError(f"{name} must be a tuple")
    for reason_code in value:
        _require_reason_code(name, reason_code, supported)
    if len(set(value)) != len(value):
        raise ValueError(f"{name} must not contain duplicates")
    return value


def _require_reason_code(name: str, value: object, supported: tuple[str, ...]) -> str:
    value = _require_public_identifier(name, value)
    if value not in supported:
        raise ValueError(f"{name} is not supported")
    return value


def _report_payload(
    value: ResearchStrategyProbabilityEdgeExplainabilityReport,
) -> dict[str, object]:
    _validate_report(value)
    if value.derived_validation_digest != _report_digest(value):
        raise ValueError("derived_validation_digest mismatch")
    payload = _json_ready(asdict(value))
    if type(payload) is not dict:
        raise ValueError("payload must be a JSON object")
    return payload


def _report_digest(
    value: ResearchStrategyProbabilityEdgeExplainabilityReport,
) -> str:
    payload = asdict(value)
    payload.pop(_DIGEST_FIELD, None)
    return _payload_digest(payload)


def _report_digest_from_values(values: dict[str, object]) -> str:
    payload = dict(values)
    payload.pop(_DIGEST_FIELD, None)
    return _payload_digest(payload)


def _payload_digest(value: dict[str, object]) -> str:
    encoded = json.dumps(
        _json_ready(value),
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    ).encode("utf-8")
    return sha256(encoded).hexdigest()


def _validate_payload_digest(payload: dict[str, object]) -> None:
    provided = payload.get(_DIGEST_FIELD)
    _require_digest(_DIGEST_FIELD, provided)
    digest_input = dict(payload)
    digest_input.pop(_DIGEST_FIELD, None)
    expected = _payload_digest(digest_input)
    if provided != expected:
        raise ValueError("derived_validation_digest mismatch")


def _validate_payload_statuses(value: object) -> None:
    if type(value) is dict:
        for key, item in value.items():
            if key == "status" and item not in _STATUS_VALUES:
                raise ValueError("status must be pass, watch, or block")
            _validate_payload_statuses(item)
    elif type(value) is list:
        for item in value:
            _validate_payload_statuses(item)


def _json_ready(value: Any) -> Any:
    if value is None:
        return None
    if is_dataclass(value) and not isinstance(value, type):
        return _json_ready(asdict(value))
    if type(value) is Decimal:
        if not value.is_finite():
            raise ValueError("Decimal value must be finite")
        return str(_quantize(value))
    if type(value) is datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("datetime value must be timezone-aware")
        return value.astimezone(UTC).isoformat()
    if type(value) is str:
        return value
    if type(value) is bool:
        return value
    if type(value) in (int, float):
        raise ValueError("numeric payload values must be Decimal-derived strings")
    if type(value) is dict:
        ready: dict[str, Any] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            ready[key] = _json_ready(item)
        return ready
    if type(value) in (list, tuple):
        return [_json_ready(item) for item in value]
    raise ValueError("value is not JSON serializable")


def _copy_json_object(value: dict[str, object]) -> dict[str, object]:
    copied = _copy_json_value(value)
    if type(copied) is not dict:
        raise ValueError("payload must be a JSON object")
    return copied


def _copy_json_value(value: object) -> object:
    if value is None or type(value) in (str, bool):
        return value
    if type(value) in (int, float, Decimal):
        raise ValueError("numeric payload values must be Decimal-derived strings")
    if type(value) is dict:
        copied: dict[str, object] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            copied[key] = _copy_json_value(item)
        return copied
    if type(value) is list:
        return [_copy_json_value(item) for item in value]
    raise ValueError("payload is not JSON serializable")


def _reject_unsafe_public_payload(
    label: str,
    value: object,
    *,
    allow_json_containers: bool = False,
) -> None:
    if is_dataclass(value) and not isinstance(value, type):
        _reject_unsafe_public_payload(label, asdict(value))
        return
    if type(value) is dict:
        if not allow_json_containers and type(value) is not dict:
            raise ValueError("payload must use plain JSON containers")
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            if any(fragment in key.casefold() for fragment in _UNSAFE_PUBLIC_FRAGMENTS):
                raise ValueError(f"unsafe public field in {label}")
            _reject_unsafe_public_payload(
                label,
                item,
                allow_json_containers=allow_json_containers,
            )
        return
    if type(value) in (list, tuple):
        for item in value:
            _reject_unsafe_public_payload(
                label,
                item,
                allow_json_containers=allow_json_containers,
            )
        return
    if type(value) is str and any(
        fragment in value.casefold() for fragment in _UNSAFE_PUBLIC_FRAGMENTS
    ):
        raise ValueError(f"unsafe public value in {label}")


def _require_exact_type(value: object, expected_type: type[object], name: str) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{name} must be exactly {expected_type.__name__}")


def _require_public_identifier(name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{name} must be a string")
    if _PUBLIC_IDENTIFIER_RE.fullmatch(value) is None:
        raise ValueError(f"{name} must be a canonical public identifier")
    if any(fragment in value.casefold() for fragment in _UNSAFE_PUBLIC_FRAGMENTS):
        raise ValueError(f"{name} has unsafe public text")
    return value


def _require_private_ref(name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{name} must be a string")
    if not value or value != value.strip():
        raise ValueError(f"{name} must be a canonical string")
    return value


def _private_ref_digest(value: str) -> str:
    return f"sha256:{sha256(value.encode('utf-8')).hexdigest()}"


def _require_private_digest(name: str, value: object) -> str:
    if type(value) is not str or _PRIVATE_DIGEST_RE.fullmatch(value) is None:
        raise ValueError(f"{name} must be a private sha256 digest")
    return value


def _require_digest(name: str, value: object) -> str:
    if type(value) is not str or _DIGEST_RE.fullmatch(value) is None:
        raise ValueError(f"{name} must be a sha256 hex digest")
    return value


def _require_status(name: str, value: object) -> str:
    if type(value) is not str or value not in _STATUS_VALUES:
        raise ValueError(f"{name} must be pass, watch, or block")
    return value


def _require_hard_flags(name: str, value: object) -> None:
    for field_name in _PHASE_FLAG_FIELDS:
        if getattr(value, field_name, None) is not True:
            raise ValueError(f"{name} {field_name} must be True")


def _require_ratio_decimal(name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(name, value)
    if decimal_value < _ZERO or decimal_value > _ONE:
        raise ValueError(f"{name} must be between zero and one")
    return decimal_value


def _require_nonnegative_count_decimal(name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(name, value)
    if decimal_value < _ZERO:
        raise ValueError(f"{name} must be nonnegative")
    return decimal_value


def _require_decimal(name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{name} must be finite")
    return _quantize(value)


def _as_utc(name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_floor_pair(
    pass_name: str,
    pass_floor: Decimal,
    watch_name: str,
    watch_floor: Decimal,
) -> None:
    if pass_floor < watch_floor:
        raise ValueError(f"{pass_name} must be at least {watch_name}")


def _quantize(value: Decimal) -> Decimal:
    return value.quantize(_QUANT, rounding=ROUND_HALF_UP)


def _clamp_ratio(value: Decimal) -> Decimal:
    quantized = _quantize(value)
    if quantized < _ZERO:
        return _ZERO
    if quantized > _ONE:
        return _ONE
    return quantized


def _inverse_ratio(value: Decimal) -> Decimal:
    return _clamp_ratio(_ONE - value)


def _decimal_count(value: int) -> Decimal:
    return Decimal(value).quantize(_QUANT)


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == _ZERO:
        return _ZERO
    return _quantize(numerator / denominator)


def _average_ratio(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return _ZERO
    return _ratio(sum(values, _ZERO), _decimal_count(len(values)))


__all__ = (
    "DEFAULT_RESEARCH_STRATEGY_PROBABILITY_EDGE_EXPLAINABILITY_REPORT_CONFIG_VERSION",
    "RESEARCH_STRATEGY_PROBABILITY_EDGE_EXPLAINABILITY_STATUSES",
    "ResearchStrategyProbabilityEdgeExplainabilityConfig",
    "ResearchStrategyProbabilityEdgeExplainabilityInput",
    "ResearchStrategyProbabilityEdgeExplainabilityReasonCodeCount",
    "ResearchStrategyProbabilityEdgeExplainabilityReport",
    "ResearchStrategyProbabilityEdgeExplainabilityRow",
    "build_research_strategy_probability_edge_explainability_report",
    "research_strategy_probability_edge_explainability_report_payload",
)
