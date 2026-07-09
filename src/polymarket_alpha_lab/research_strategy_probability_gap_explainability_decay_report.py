"""Report-only probability gap explainability decay scorecard.

The report evaluates whether a model-vs-public probability gap remains
explainable as evidence ages, cost pressure changes, liquidity weakens,
source confidence decays, and resolution ambiguity changes. It exposes only
deterministic public report payloads and no execution, persistence, or live
market surface.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import InitVar, asdict, dataclass, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal, ROUND_HALF_UP
from hashlib import sha256
import json
import re
from typing import Any, Sequence


DEFAULT_RESEARCH_STRATEGY_PROBABILITY_GAP_EXPLAINABILITY_DECAY_REPORT_CONFIG_VERSION = (
    "research-strategy-probability-gap-explainability-decay-report-v0"
)

STATUS_PASS = "pass"
STATUS_WATCH = "watch"
STATUS_BLOCK = "block"
RESEARCH_STRATEGY_PROBABILITY_GAP_EXPLAINABILITY_DECAY_STATUSES = (
    STATUS_PASS,
    STATUS_WATCH,
    STATUS_BLOCK,
)

REASON_EMPTY_INPUT = "empty_input"
REASON_EVIDENCE_PACKET_READY = "evidence_packet_ready"
REASON_COST_UPDATE_OBSERVED = "cost_update_observed"
REASON_LIQUIDITY_UPDATE_OBSERVED = "liquidity_update_observed"
REASON_RESOLUTION_SCOPE_REVIEW_REQUESTED = "resolution_scope_review_requested"
REASON_EVIDENCE_AGE_BLOCK = "evidence_age_block"
REASON_COST_DRAG_BLOCK = "cost_drag_block"
REASON_LIQUIDITY_CHANGE_BLOCK = "liquidity_change_block"
REASON_SOURCE_CONFIDENCE_DECAY_BLOCK = "source_confidence_decay_block"
REASON_RESOLUTION_AMBIGUITY_BLOCK = "resolution_ambiguity_block"
REASON_EXPLAINABILITY_SCORE_BLOCK = "explainability_score_block"
REASON_EVIDENCE_AGE_WATCH = "evidence_age_watch"
REASON_COST_DRAG_WATCH = "cost_drag_watch"
REASON_LIQUIDITY_CHANGE_WATCH = "liquidity_change_watch"
REASON_SOURCE_CONFIDENCE_DECAY_WATCH = "source_confidence_decay_watch"
REASON_RESOLUTION_AMBIGUITY_WATCH = "resolution_ambiguity_watch"
REASON_EXPLAINABILITY_SCORE_WATCH = "explainability_score_watch"
REASON_GAP_EXPLAINABILITY_PASS = "gap_explainability_pass"

_UPSTREAM_REASON_CODE_SEQUENCE = (
    REASON_EVIDENCE_PACKET_READY,
    REASON_COST_UPDATE_OBSERVED,
    REASON_LIQUIDITY_UPDATE_OBSERVED,
    REASON_RESOLUTION_SCOPE_REVIEW_REQUESTED,
)
_GENERATED_ROW_REASON_CODE_SEQUENCE = (
    REASON_EVIDENCE_AGE_BLOCK,
    REASON_COST_DRAG_BLOCK,
    REASON_LIQUIDITY_CHANGE_BLOCK,
    REASON_SOURCE_CONFIDENCE_DECAY_BLOCK,
    REASON_RESOLUTION_AMBIGUITY_BLOCK,
    REASON_EXPLAINABILITY_SCORE_BLOCK,
    REASON_EVIDENCE_AGE_WATCH,
    REASON_COST_DRAG_WATCH,
    REASON_LIQUIDITY_CHANGE_WATCH,
    REASON_SOURCE_CONFIDENCE_DECAY_WATCH,
    REASON_RESOLUTION_AMBIGUITY_WATCH,
    REASON_EXPLAINABILITY_SCORE_WATCH,
    REASON_GAP_EXPLAINABILITY_PASS,
)
_ROW_REASON_CODE_SEQUENCE = (
    *_UPSTREAM_REASON_CODE_SEQUENCE,
    *_GENERATED_ROW_REASON_CODE_SEQUENCE,
)
_REASON_CODE_SEQUENCE = (REASON_EMPTY_INPUT, *_ROW_REASON_CODE_SEQUENCE)
_BLOCK_REASON_CODES = frozenset(
    (
        REASON_EVIDENCE_AGE_BLOCK,
        REASON_COST_DRAG_BLOCK,
        REASON_LIQUIDITY_CHANGE_BLOCK,
        REASON_SOURCE_CONFIDENCE_DECAY_BLOCK,
        REASON_RESOLUTION_AMBIGUITY_BLOCK,
        REASON_EXPLAINABILITY_SCORE_BLOCK,
    ),
)

GAP_DIRECTION_MODEL_ABOVE_PUBLIC = "model_above_public"
GAP_DIRECTION_MODEL_BELOW_PUBLIC = "model_below_public"
GAP_DIRECTION_ALIGNED = "aligned"
_GAP_DIRECTIONS = frozenset(
    (
        GAP_DIRECTION_MODEL_ABOVE_PUBLIC,
        GAP_DIRECTION_MODEL_BELOW_PUBLIC,
        GAP_DIRECTION_ALIGNED,
    ),
)

_QUANT = Decimal("0.000001")
_ZERO = Decimal("0.000000")
_ONE = Decimal("1.000000")
_DIGEST_FIELD = "derived_validation_digest"
_STATUS_VALUES = frozenset(RESEARCH_STRATEGY_PROBABILITY_GAP_EXPLAINABILITY_DECAY_STATUSES)
_PUBLIC_IDENTIFIER_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,127}$")
_DIGEST_RE = re.compile(r"^[0-9a-f]{64}$")
_PRIVATE_DIGEST_RE = re.compile(r"^sha256:[0-9a-f]{64}$")
_UNSAFE_PUBLIC_FRAGMENTS = (
    "candidate",
    "market",
    "slug",
    "question",
    "url",
    "text",
    "dsn",
    "database",
    "table",
    "token",
    "wallet",
    "auth",
    "order",
    "trade",
    "trading",
    "live",
    "execution",
    "execute",
    "position",
    "sizing",
    "buy",
    "sell",
    "recommend",
    "private",
    "private key",
    "secret",
    "credential",
    "api_key",
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
class ResearchStrategyProbabilityGapExplainabilityDecayConfig(_FinalPublicDataclass):
    config_version: str = (
        DEFAULT_RESEARCH_STRATEGY_PROBABILITY_GAP_EXPLAINABILITY_DECAY_REPORT_CONFIG_VERSION
    )
    pass_min_explainability_score: Decimal = Decimal("0.750000")
    watch_min_explainability_score: Decimal = Decimal("0.550000")
    max_pass_evidence_age_seconds: Decimal = Decimal("21600.000000")
    max_watch_evidence_age_seconds: Decimal = Decimal("86400.000000")
    max_pass_cost_probability_drag: Decimal = Decimal("0.030000")
    max_watch_cost_probability_drag: Decimal = Decimal("0.080000")
    min_pass_liquidity_quality_score: Decimal = Decimal("0.750000")
    min_watch_liquidity_quality_score: Decimal = Decimal("0.500000")
    min_pass_adjusted_source_confidence_score: Decimal = Decimal("0.700000")
    min_watch_adjusted_source_confidence_score: Decimal = Decimal("0.500000")
    max_pass_resolution_ambiguity_score: Decimal = Decimal("0.200000")
    max_watch_resolution_ambiguity_score: Decimal = Decimal("0.450000")
    evidence_freshness_weight: Decimal = Decimal("0.250000")
    cost_stability_weight: Decimal = Decimal("0.200000")
    liquidity_quality_weight: Decimal = Decimal("0.200000")
    source_confidence_weight: Decimal = Decimal("0.200000")
    resolution_clarity_weight: Decimal = Decimal("0.150000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchStrategyProbabilityGapExplainabilityDecayConfig,
            "config",
        )
        object.__setattr__(
            self,
            "config_version",
            _require_public_identifier("config_version", self.config_version),
        )
        if (
            self.config_version
            != DEFAULT_RESEARCH_STRATEGY_PROBABILITY_GAP_EXPLAINABILITY_DECAY_REPORT_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "pass_min_explainability_score",
            "watch_min_explainability_score",
            "max_pass_cost_probability_drag",
            "max_watch_cost_probability_drag",
            "min_pass_liquidity_quality_score",
            "min_watch_liquidity_quality_score",
            "min_pass_adjusted_source_confidence_score",
            "min_watch_adjusted_source_confidence_score",
            "max_pass_resolution_ambiguity_score",
            "max_watch_resolution_ambiguity_score",
            "evidence_freshness_weight",
            "cost_stability_weight",
            "liquidity_quality_weight",
            "source_confidence_weight",
            "resolution_clarity_weight",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "max_pass_evidence_age_seconds",
            "max_watch_evidence_age_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_positive_decimal(field_name, getattr(self, field_name)),
            )
        _require_floor_pair(
            "explainability_score",
            self.pass_min_explainability_score,
            self.watch_min_explainability_score,
        )
        _require_ceiling_pair(
            "evidence_age_seconds",
            self.max_pass_evidence_age_seconds,
            self.max_watch_evidence_age_seconds,
        )
        _require_ceiling_pair(
            "cost_probability_drag",
            self.max_pass_cost_probability_drag,
            self.max_watch_cost_probability_drag,
        )
        _require_floor_pair(
            "liquidity_quality_score",
            self.min_pass_liquidity_quality_score,
            self.min_watch_liquidity_quality_score,
        )
        _require_floor_pair(
            "adjusted_source_confidence_score",
            self.min_pass_adjusted_source_confidence_score,
            self.min_watch_adjusted_source_confidence_score,
        )
        _require_ceiling_pair(
            "resolution_ambiguity_score",
            self.max_pass_resolution_ambiguity_score,
            self.max_watch_resolution_ambiguity_score,
        )
        weight_sum = _quantize(
            self.evidence_freshness_weight
            + self.cost_stability_weight
            + self.liquidity_quality_weight
            + self.source_confidence_weight
            + self.resolution_clarity_weight,
        )
        if weight_sum != _ONE:
            raise ValueError("probability_gap weights must sum to one")
        _require_hard_flags("config", self)
        _reject_unsafe_public_payload("config", self)


@dataclass(frozen=True)
class ResearchStrategyProbabilityGapExplainabilityDecayInput(_FinalPublicDataclass):
    candidate_ref: str
    surface_ref: str
    observed_at: datetime
    model_probability: Decimal
    public_probability: Decimal
    evidence_age_seconds: Decimal
    cost_probability_drag: Decimal
    liquidity_quality_score: Decimal
    source_confidence_score: Decimal
    source_confidence_decay_score: Decimal
    resolution_ambiguity_score: Decimal
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchStrategyProbabilityGapExplainabilityDecayInput,
            "input",
        )
        object.__setattr__(
            self,
            "candidate_ref",
            _require_private_ref("candidate_ref", self.candidate_ref),
        )
        object.__setattr__(
            self,
            "surface_ref",
            _require_private_ref("surface_ref", self.surface_ref),
        )
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in (
            "model_probability",
            "public_probability",
            "cost_probability_drag",
            "liquidity_quality_score",
            "source_confidence_score",
            "source_confidence_decay_score",
            "resolution_ambiguity_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "evidence_age_seconds",
            _require_nonnegative_decimal(
                "evidence_age_seconds",
                self.evidence_age_seconds,
            ),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(
                "reason_codes",
                self.reason_codes,
                _UPSTREAM_REASON_CODE_SEQUENCE,
            ),
        )
        _require_hard_flags("input", self)


@dataclass(frozen=True)
class ResearchStrategyProbabilityGapExplainabilityDecayReasonCodeCount(
    _FinalPublicDataclass,
):
    reason_code: str
    count: Decimal
    input_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchStrategyProbabilityGapExplainabilityDecayReasonCodeCount,
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
            "input_ratio",
            _require_ratio_decimal("input_ratio", self.input_ratio),
        )
        _require_hard_flags("reason count", self)
        _reject_unsafe_public_payload("reason count", self)


@dataclass(frozen=True)
class ResearchStrategyProbabilityGapExplainabilityDecayRow(_FinalPublicDataclass):
    gap_ref_digest: str
    observed_at: datetime
    model_probability: Decimal
    public_probability: Decimal
    probability_gap: Decimal
    gap_direction: str
    evidence_age_seconds: Decimal
    evidence_freshness_score: Decimal
    cost_probability_drag: Decimal
    cost_stability_score: Decimal
    liquidity_quality_score: Decimal
    source_confidence_score: Decimal
    source_confidence_decay_score: Decimal
    adjusted_source_confidence_score: Decimal
    resolution_ambiguity_score: Decimal
    resolution_clarity_score: Decimal
    explainability_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True
    validation_config: InitVar[
        ResearchStrategyProbabilityGapExplainabilityDecayConfig | None
    ] = None

    def __post_init__(
        self,
        validation_config: (
            ResearchStrategyProbabilityGapExplainabilityDecayConfig | None
        ),
    ) -> None:
        _require_exact_type(
            self,
            ResearchStrategyProbabilityGapExplainabilityDecayRow,
            "row",
        )
        object.__setattr__(
            self,
            "gap_ref_digest",
            _require_private_digest("gap_ref_digest", self.gap_ref_digest),
        )
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in (
            "model_probability",
            "public_probability",
            "probability_gap",
            "evidence_freshness_score",
            "cost_probability_drag",
            "cost_stability_score",
            "liquidity_quality_score",
            "source_confidence_score",
            "source_confidence_decay_score",
            "adjusted_source_confidence_score",
            "resolution_ambiguity_score",
            "resolution_clarity_score",
            "explainability_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "evidence_age_seconds",
            _require_nonnegative_decimal(
                "evidence_age_seconds",
                self.evidence_age_seconds,
            ),
        )
        _require_member("gap_direction", self.gap_direction, _GAP_DIRECTIONS)
        _require_status("status", self.status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(
                "reason_codes",
                self.reason_codes,
                _ROW_REASON_CODE_SEQUENCE,
            ),
        )
        _validate_row(self, validation_config)
        _require_hard_flags("row", self)
        _reject_unsafe_public_payload("row", self)


@dataclass(frozen=True)
class ResearchStrategyProbabilityGapExplainabilityDecayReport(_FinalPublicDataclass):
    generated_at: datetime
    config_version: str
    status: str
    input_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    average_explainability_score: Decimal
    min_explainability_score: Decimal
    max_evidence_age_seconds: Decimal
    max_cost_probability_drag: Decimal
    min_liquidity_quality_score: Decimal
    min_adjusted_source_confidence_score: Decimal
    max_resolution_ambiguity_score: Decimal
    rows: tuple[ResearchStrategyProbabilityGapExplainabilityDecayRow, ...]
    reason_code_counts: tuple[
        ResearchStrategyProbabilityGapExplainabilityDecayReasonCodeCount,
        ...,
    ]
    reason_codes: tuple[str, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchStrategyProbabilityGapExplainabilityDecayReport,
            "report",
        )
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        object.__setattr__(
            self,
            "config_version",
            _require_public_identifier("config_version", self.config_version),
        )
        if (
            self.config_version
            != DEFAULT_RESEARCH_STRATEGY_PROBABILITY_GAP_EXPLAINABILITY_DECAY_REPORT_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        _require_status("status", self.status)
        for field_name in ("input_count", "pass_count", "watch_count", "block_count"):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_count_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "average_explainability_score",
            "min_explainability_score",
            "max_cost_probability_drag",
            "min_liquidity_quality_score",
            "min_adjusted_source_confidence_score",
            "max_resolution_ambiguity_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "max_evidence_age_seconds",
            _require_nonnegative_decimal(
                "max_evidence_age_seconds",
                self.max_evidence_age_seconds,
            ),
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
            _normalize_reason_codes(
                "reason_codes",
                self.reason_codes,
                _REASON_CODE_SEQUENCE,
            ),
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
        return research_strategy_probability_gap_explainability_decay_report_payload(self)


def build_research_strategy_probability_gap_explainability_decay_report(
    inputs: Sequence[ResearchStrategyProbabilityGapExplainabilityDecayInput],
    *,
    generated_at: datetime,
    config: ResearchStrategyProbabilityGapExplainabilityDecayConfig | None = None,
) -> ResearchStrategyProbabilityGapExplainabilityDecayReport:
    """Build a deterministic readonly probability gap explainability report."""

    cfg = config or ResearchStrategyProbabilityGapExplainabilityDecayConfig()
    if type(cfg) is not ResearchStrategyProbabilityGapExplainabilityDecayConfig:
        raise ValueError(
            "config must be a ResearchStrategyProbabilityGapExplainabilityDecayConfig",
        )
    _require_hard_flags("config", cfg)
    report_time = _as_utc("generated_at", generated_at)
    normalized_inputs = _normalize_inputs(inputs)
    for item in normalized_inputs:
        if item.observed_at > report_time:
            raise ValueError("observed_at must not be after generated_at")
    rows = tuple(
        sorted(
            (_row_for_input(item, cfg) for item in normalized_inputs),
            key=_row_sort_key,
        ),
    )
    reason_code_counts = _reason_code_counts(rows)
    reason_codes = _normalize_reason_codes(
        "reason_codes",
        tuple(item.reason_code for item in reason_code_counts),
        _REASON_CODE_SEQUENCE,
    )
    if not rows:
        reason_code_counts = (
            ResearchStrategyProbabilityGapExplainabilityDecayReasonCodeCount(
                reason_code=REASON_EMPTY_INPUT,
                count=_ONE,
                input_ratio=_ONE,
            ),
        )
        reason_codes = (REASON_EMPTY_INPUT,)
    values: dict[str, object] = {
        "generated_at": report_time,
        "config_version": cfg.config_version,
        "status": _report_status(rows),
        "input_count": _decimal_count(len(rows)),
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
        "max_evidence_age_seconds": max(
            (row.evidence_age_seconds for row in rows),
            default=_ZERO,
        ),
        "max_cost_probability_drag": max(
            (row.cost_probability_drag for row in rows),
            default=_ZERO,
        ),
        "min_liquidity_quality_score": min(
            (row.liquidity_quality_score for row in rows),
            default=_ZERO,
        ),
        "min_adjusted_source_confidence_score": min(
            (row.adjusted_source_confidence_score for row in rows),
            default=_ZERO,
        ),
        "max_resolution_ambiguity_score": max(
            (row.resolution_ambiguity_score for row in rows),
            default=_ZERO,
        ),
        "rows": rows,
        "reason_code_counts": reason_code_counts,
        "reason_codes": reason_codes,
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    return ResearchStrategyProbabilityGapExplainabilityDecayReport(
        **values,
        derived_validation_digest=_report_digest_from_values(values),
    )


def research_strategy_probability_gap_explainability_decay_report_payload(
    value: ResearchStrategyProbabilityGapExplainabilityDecayReport | dict[str, object],
) -> dict[str, object]:
    if type(value) is ResearchStrategyProbabilityGapExplainabilityDecayReport:
        _require_hard_flags("report", value)
        payload = _report_payload(value)
    elif type(value) is dict:
        payload = _copy_json_object(value)
    else:
        raise ValueError(
            "value must be a ResearchStrategyProbabilityGapExplainabilityDecayReport "
            "or dict",
        )
    _reject_unsafe_public_payload("payload", payload, allow_json_containers=True)
    _validate_payload_statuses(payload)
    _validate_payload_flags(payload, require_top_level=True)
    _validate_payload_digest(payload)
    return payload


def _row_for_input(
    item: ResearchStrategyProbabilityGapExplainabilityDecayInput,
    config: ResearchStrategyProbabilityGapExplainabilityDecayConfig,
) -> ResearchStrategyProbabilityGapExplainabilityDecayRow:
    probability_gap = _absolute_probability_gap(
        item.model_probability,
        item.public_probability,
    )
    evidence_freshness_score = _stability_score(
        item.evidence_age_seconds,
        config.max_watch_evidence_age_seconds,
    )
    cost_stability_score = _stability_score(
        item.cost_probability_drag,
        config.max_watch_cost_probability_drag,
    )
    adjusted_source_confidence_score = _clamp_ratio(
        item.source_confidence_score * _inverse_ratio(item.source_confidence_decay_score),
    )
    resolution_clarity_score = _inverse_ratio(item.resolution_ambiguity_score)
    explainability_score = _explainability_score(
        evidence_freshness_score=evidence_freshness_score,
        cost_stability_score=cost_stability_score,
        liquidity_quality_score=item.liquidity_quality_score,
        adjusted_source_confidence_score=adjusted_source_confidence_score,
        resolution_clarity_score=resolution_clarity_score,
        config=config,
    )
    reason_codes = _row_reason_codes(
        upstream_reason_codes=item.reason_codes,
        evidence_age_seconds=item.evidence_age_seconds,
        cost_probability_drag=item.cost_probability_drag,
        liquidity_quality_score=item.liquidity_quality_score,
        adjusted_source_confidence_score=adjusted_source_confidence_score,
        resolution_ambiguity_score=item.resolution_ambiguity_score,
        explainability_score=explainability_score,
        config=config,
    )
    return ResearchStrategyProbabilityGapExplainabilityDecayRow(
        gap_ref_digest=_gap_ref_digest(item.candidate_ref, item.surface_ref),
        observed_at=item.observed_at,
        model_probability=item.model_probability,
        public_probability=item.public_probability,
        probability_gap=probability_gap,
        gap_direction=_gap_direction(item.model_probability, item.public_probability),
        evidence_age_seconds=item.evidence_age_seconds,
        evidence_freshness_score=evidence_freshness_score,
        cost_probability_drag=item.cost_probability_drag,
        cost_stability_score=cost_stability_score,
        liquidity_quality_score=item.liquidity_quality_score,
        source_confidence_score=item.source_confidence_score,
        source_confidence_decay_score=item.source_confidence_decay_score,
        adjusted_source_confidence_score=adjusted_source_confidence_score,
        resolution_ambiguity_score=item.resolution_ambiguity_score,
        resolution_clarity_score=resolution_clarity_score,
        explainability_score=explainability_score,
        status=_row_status(reason_codes),
        reason_codes=reason_codes,
        validation_config=config,
    )


def _row_reason_codes(
    *,
    upstream_reason_codes: tuple[str, ...],
    evidence_age_seconds: Decimal,
    cost_probability_drag: Decimal,
    liquidity_quality_score: Decimal,
    adjusted_source_confidence_score: Decimal,
    resolution_ambiguity_score: Decimal,
    explainability_score: Decimal,
    config: ResearchStrategyProbabilityGapExplainabilityDecayConfig,
) -> tuple[str, ...]:
    reason_codes = list(upstream_reason_codes)
    if evidence_age_seconds > config.max_watch_evidence_age_seconds:
        reason_codes.append(REASON_EVIDENCE_AGE_BLOCK)
    elif evidence_age_seconds > config.max_pass_evidence_age_seconds:
        reason_codes.append(REASON_EVIDENCE_AGE_WATCH)
    if cost_probability_drag > config.max_watch_cost_probability_drag:
        reason_codes.append(REASON_COST_DRAG_BLOCK)
    elif cost_probability_drag > config.max_pass_cost_probability_drag:
        reason_codes.append(REASON_COST_DRAG_WATCH)
    if liquidity_quality_score < config.min_watch_liquidity_quality_score:
        reason_codes.append(REASON_LIQUIDITY_CHANGE_BLOCK)
    elif liquidity_quality_score < config.min_pass_liquidity_quality_score:
        reason_codes.append(REASON_LIQUIDITY_CHANGE_WATCH)
    if (
        adjusted_source_confidence_score
        < config.min_watch_adjusted_source_confidence_score
    ):
        reason_codes.append(REASON_SOURCE_CONFIDENCE_DECAY_BLOCK)
    elif (
        adjusted_source_confidence_score
        < config.min_pass_adjusted_source_confidence_score
    ):
        reason_codes.append(REASON_SOURCE_CONFIDENCE_DECAY_WATCH)
    if resolution_ambiguity_score > config.max_watch_resolution_ambiguity_score:
        reason_codes.append(REASON_RESOLUTION_AMBIGUITY_BLOCK)
    elif resolution_ambiguity_score > config.max_pass_resolution_ambiguity_score:
        reason_codes.append(REASON_RESOLUTION_AMBIGUITY_WATCH)
    if explainability_score < config.watch_min_explainability_score:
        reason_codes.append(REASON_EXPLAINABILITY_SCORE_BLOCK)
    elif explainability_score < config.pass_min_explainability_score:
        reason_codes.append(REASON_EXPLAINABILITY_SCORE_WATCH)
    generated = tuple(
        reason_code
        for reason_code in reason_codes
        if reason_code in _GENERATED_ROW_REASON_CODE_SEQUENCE
    )
    if not generated:
        reason_codes.append(REASON_GAP_EXPLAINABILITY_PASS)
    return _normalize_reason_codes(
        "reason_codes",
        tuple(reason_codes),
        _ROW_REASON_CODE_SEQUENCE,
    )


def _row_status(reason_codes: tuple[str, ...]) -> str:
    if any(reason_code in _BLOCK_REASON_CODES for reason_code in reason_codes):
        return STATUS_BLOCK
    if REASON_GAP_EXPLAINABILITY_PASS in reason_codes:
        return STATUS_PASS
    return STATUS_WATCH


def _report_status(
    rows: tuple[ResearchStrategyProbabilityGapExplainabilityDecayRow, ...],
) -> str:
    if not rows:
        return STATUS_BLOCK
    if any(row.status == STATUS_BLOCK for row in rows):
        return STATUS_BLOCK
    if any(row.status == STATUS_WATCH for row in rows):
        return STATUS_WATCH
    return STATUS_PASS


def _status_count(
    rows: tuple[ResearchStrategyProbabilityGapExplainabilityDecayRow, ...],
    status: str,
) -> int:
    return sum(1 for row in rows if row.status == status)


def _row_sort_key(
    row: ResearchStrategyProbabilityGapExplainabilityDecayRow,
) -> tuple[int, Decimal, str]:
    return (_status_rank(row.status), row.explainability_score, row.gap_ref_digest)


def _status_rank(value: str) -> int:
    return {STATUS_BLOCK: 0, STATUS_WATCH: 1, STATUS_PASS: 2}[value]


def _reason_code_counts(
    rows: tuple[ResearchStrategyProbabilityGapExplainabilityDecayRow, ...],
) -> tuple[ResearchStrategyProbabilityGapExplainabilityDecayReasonCodeCount, ...]:
    total = _decimal_count(len(rows))
    counts: Counter[str] = Counter(
        reason_code for row in rows for reason_code in row.reason_codes
    )
    return tuple(
        ResearchStrategyProbabilityGapExplainabilityDecayReasonCodeCount(
            reason_code=reason_code,
            count=_decimal_count(count),
            input_ratio=_ratio(_decimal_count(count), total),
        )
        for reason_code, count in sorted(counts.items(), key=lambda item: (-item[1], item[0]))
    )


def _explainability_score(
    *,
    evidence_freshness_score: Decimal,
    cost_stability_score: Decimal,
    liquidity_quality_score: Decimal,
    adjusted_source_confidence_score: Decimal,
    resolution_clarity_score: Decimal,
    config: ResearchStrategyProbabilityGapExplainabilityDecayConfig,
) -> Decimal:
    score = (
        evidence_freshness_score * config.evidence_freshness_weight
        + cost_stability_score * config.cost_stability_weight
        + liquidity_quality_score * config.liquidity_quality_weight
        + adjusted_source_confidence_score * config.source_confidence_weight
        + resolution_clarity_score * config.resolution_clarity_weight
    )
    return _clamp_ratio(score)


def _validate_row(
    row: ResearchStrategyProbabilityGapExplainabilityDecayRow,
    config: ResearchStrategyProbabilityGapExplainabilityDecayConfig | None,
) -> None:
    if row.probability_gap != _absolute_probability_gap(
        row.model_probability,
        row.public_probability,
    ):
        raise ValueError("probability_gap must match model and public probabilities")
    if row.gap_direction != _gap_direction(row.model_probability, row.public_probability):
        raise ValueError("gap_direction must match model and public probabilities")
    if row.adjusted_source_confidence_score != _clamp_ratio(
        row.source_confidence_score * _inverse_ratio(row.source_confidence_decay_score),
    ):
        raise ValueError(
            "adjusted_source_confidence_score must match confidence and decay",
        )
    if row.resolution_clarity_score != _inverse_ratio(row.resolution_ambiguity_score):
        raise ValueError(
            "resolution_clarity_score must match resolution_ambiguity_score",
        )
    if row.status != _row_status(row.reason_codes):
        raise ValueError("status must match reason_codes")
    if config is not None:
        if type(config) is not ResearchStrategyProbabilityGapExplainabilityDecayConfig:
            raise ValueError(
                "validation_config must be a "
                "ResearchStrategyProbabilityGapExplainabilityDecayConfig",
            )
        if row.evidence_freshness_score != _stability_score(
            row.evidence_age_seconds,
            config.max_watch_evidence_age_seconds,
        ):
            raise ValueError(
                "evidence_freshness_score must match evidence_age_seconds",
            )
        if row.cost_stability_score != _stability_score(
            row.cost_probability_drag,
            config.max_watch_cost_probability_drag,
        ):
            raise ValueError(
                "cost_stability_score must match cost_probability_drag",
            )
        expected_score = _explainability_score(
            evidence_freshness_score=row.evidence_freshness_score,
            cost_stability_score=row.cost_stability_score,
            liquidity_quality_score=row.liquidity_quality_score,
            adjusted_source_confidence_score=row.adjusted_source_confidence_score,
            resolution_clarity_score=row.resolution_clarity_score,
            config=config,
        )
        if row.explainability_score != expected_score:
            raise ValueError("explainability_score must match component scores")
        expected_reasons = _row_reason_codes(
            upstream_reason_codes=tuple(
                reason_code
                for reason_code in row.reason_codes
                if reason_code in _UPSTREAM_REASON_CODE_SEQUENCE
            ),
            evidence_age_seconds=row.evidence_age_seconds,
            cost_probability_drag=row.cost_probability_drag,
            liquidity_quality_score=row.liquidity_quality_score,
            adjusted_source_confidence_score=row.adjusted_source_confidence_score,
            resolution_ambiguity_score=row.resolution_ambiguity_score,
            explainability_score=row.explainability_score,
            config=config,
        )
        if row.reason_codes != expected_reasons:
            raise ValueError("reason_codes must match explainability thresholds")


def _validate_report(
    report: ResearchStrategyProbabilityGapExplainabilityDecayReport,
) -> None:
    rows = report.rows
    if report.status != _report_status(rows):
        raise ValueError("status must match rows")
    if report.input_count != _decimal_count(len(rows)):
        raise ValueError("input_count must match rows")
    if report.pass_count != _decimal_count(_status_count(rows, STATUS_PASS)):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _decimal_count(_status_count(rows, STATUS_WATCH)):
        raise ValueError("watch_count must match rows")
    if report.block_count != _decimal_count(_status_count(rows, STATUS_BLOCK)):
        raise ValueError("block_count must match rows")
    if rows != tuple(sorted(rows, key=_row_sort_key)):
        raise ValueError("rows must be sorted by status, score, and digest")
    if report.average_explainability_score != _average_ratio(
        tuple(row.explainability_score for row in rows),
    ):
        raise ValueError("average_explainability_score must match rows")
    if report.min_explainability_score != min(
        (row.explainability_score for row in rows),
        default=_ZERO,
    ):
        raise ValueError("min_explainability_score must match rows")
    if report.max_evidence_age_seconds != max(
        (row.evidence_age_seconds for row in rows),
        default=_ZERO,
    ):
        raise ValueError("max_evidence_age_seconds must match rows")
    if report.max_cost_probability_drag != max(
        (row.cost_probability_drag for row in rows),
        default=_ZERO,
    ):
        raise ValueError("max_cost_probability_drag must match rows")
    if report.min_liquidity_quality_score != min(
        (row.liquidity_quality_score for row in rows),
        default=_ZERO,
    ):
        raise ValueError("min_liquidity_quality_score must match rows")
    if report.min_adjusted_source_confidence_score != min(
        (row.adjusted_source_confidence_score for row in rows),
        default=_ZERO,
    ):
        raise ValueError("min_adjusted_source_confidence_score must match rows")
    if report.max_resolution_ambiguity_score != max(
        (row.resolution_ambiguity_score for row in rows),
        default=_ZERO,
    ):
        raise ValueError("max_resolution_ambiguity_score must match rows")
    expected_counts = (
        _reason_code_counts(rows)
        if rows
        else (
            ResearchStrategyProbabilityGapExplainabilityDecayReasonCodeCount(
                reason_code=REASON_EMPTY_INPUT,
                count=_ONE,
                input_ratio=_ONE,
            ),
        )
    )
    if report.reason_code_counts != expected_counts:
        raise ValueError("reason_code_counts must match rows")
    expected_reason_codes = _normalize_reason_codes(
        "reason_codes",
        tuple(item.reason_code for item in expected_counts),
        _REASON_CODE_SEQUENCE,
    )
    if report.reason_codes != expected_reason_codes:
        raise ValueError("reason_codes must match reason_code_counts")


def _report_payload(
    report: ResearchStrategyProbabilityGapExplainabilityDecayReport,
) -> dict[str, object]:
    payload = _json_ready(asdict(report))
    if type(payload) is not dict:
        raise ValueError("payload must be a JSON object")
    return payload


def _report_payload_without_digest(
    value: ResearchStrategyProbabilityGapExplainabilityDecayReport | dict[str, object],
) -> dict[str, object]:
    if type(value) is ResearchStrategyProbabilityGapExplainabilityDecayReport:
        payload = _report_payload(value)
    else:
        payload = _json_ready(value)
        if type(payload) is not dict:
            raise ValueError("payload must be a JSON object")
    payload.pop(_DIGEST_FIELD, None)
    return payload


def _report_digest(
    report: ResearchStrategyProbabilityGapExplainabilityDecayReport,
) -> str:
    return _digest_payload(_report_payload_without_digest(report))


def _report_digest_from_values(values: dict[str, object]) -> str:
    return _digest_payload(_report_payload_without_digest(values))


def _digest_payload(payload_without_digest: dict[str, object]) -> str:
    encoded = json.dumps(
        payload_without_digest,
        sort_keys=True,
        separators=(",", ":"),
    )
    return sha256(encoded.encode("utf-8")).hexdigest()


def _validate_payload_digest(payload: dict[str, object]) -> None:
    digest = payload.get(_DIGEST_FIELD)
    if type(digest) is not str or _DIGEST_RE.fullmatch(digest) is None:
        raise ValueError("derived_validation_digest must be a sha256 digest")
    expected = _digest_payload(_payload_without_digest_copy(payload))
    if digest != expected:
        raise ValueError("derived_validation_digest mismatch")


def _payload_without_digest_copy(payload: dict[str, object]) -> dict[str, object]:
    copied = _copy_json_object(payload)
    copied.pop(_DIGEST_FIELD, None)
    return copied


def _validate_payload_statuses(value: object) -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            if key == "status" and item not in _STATUS_VALUES:
                raise ValueError("status must be pass, watch, or block")
            _validate_payload_statuses(item)
    elif isinstance(value, list):
        for item in value:
            _validate_payload_statuses(item)


def _validate_payload_flags(value: object, *, require_top_level: bool = False) -> None:
    if isinstance(value, dict):
        for field_name in ("paper_only", "report_only", "readonly"):
            if field_name not in value:
                raise ValueError(f"{field_name} must be True in payload")
            if field_name in value and value[field_name] is not True:
                raise ValueError(f"{field_name} must be True in payload")
        for item in value.values():
            _validate_payload_flags(item)
    elif isinstance(value, list):
        for item in value:
            _validate_payload_flags(item)


def _json_ready(value: Any) -> Any:
    if value is None:
        return None
    if is_dataclass(value) and not isinstance(value, type):
        return _json_ready(asdict(value))
    if type(value) is Decimal:
        if not value.is_finite():
            raise ValueError("JSON Decimal value must be finite")
        return str(value)
    if type(value) is datetime:
        return value.astimezone(UTC).isoformat()
    if type(value) is float:
        raise ValueError("JSON value must not be a float")
    if type(value) in (str, bool):
        return value
    if type(value) is int:
        raise ValueError("JSON numeric value must use Decimal")
    if isinstance(value, dict):
        ready: dict[str, Any] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            ready[key] = _json_ready(item)
        return ready
    if isinstance(value, (list, tuple)):
        return [_json_ready(item) for item in value]
    raise ValueError("value is not JSON serializable")


def _copy_json_object(value: dict[str, object]) -> dict[str, object]:
    return {
        _require_json_key(key): _copy_json_value(item)
        for key, item in value.items()
    }


def _copy_json_value(value: object) -> object:
    if isinstance(value, dict):
        return _copy_json_object(value)
    if isinstance(value, list):
        return [_copy_json_value(item) for item in value]
    if type(value) in (str, bool) or value is None:
        return value
    if type(value) is int:
        raise ValueError("payload numerics must be Decimal-derived strings")
    if type(value) in (float, Decimal):
        raise ValueError("payload values must be JSON-ready strings")
    raise ValueError("payload is not JSON serializable")


def _require_json_key(value: object) -> str:
    if type(value) is not str:
        raise ValueError("JSON object keys must be strings")
    return value


def _reject_unsafe_public_payload(
    label: str,
    value: object,
    *,
    allow_json_containers: bool = False,
) -> None:
    if is_dataclass(value) and not isinstance(value, type):
        _reject_unsafe_public_payload(
            label,
            asdict(value),
            allow_json_containers=True,
        )
        return
    if isinstance(value, dict):
        if not allow_json_containers:
            raise ValueError(f"{label} must be a public dataclass")
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("public payload keys must be strings")
            _reject_unsafe_public_key(key, label)
            _reject_unsafe_public_payload(
                f"{label}.{key}",
                item,
                allow_json_containers=True,
            )
        return
    if isinstance(value, (list, tuple)):
        if not allow_json_containers:
            raise ValueError(f"{label} must be a public dataclass")
        for index, item in enumerate(value):
            _reject_unsafe_public_payload(
                f"{label}[{index}]",
                item,
                allow_json_containers=True,
            )
        return
    if type(value) is str:
        _reject_unsafe_public_string(label, value)


def _reject_unsafe_public_key(key: str, path: str) -> None:
    normalized = key.casefold()
    if any(fragment in normalized for fragment in _UNSAFE_PUBLIC_FRAGMENTS):
        raise ValueError(f"unsafe public field in {path}: {key}")


def _reject_unsafe_public_string(field_name: str, value: str) -> None:
    normalized = value.casefold()
    if any(fragment in normalized for fragment in _UNSAFE_PUBLIC_FRAGMENTS):
        raise ValueError(f"unsafe public value in {field_name}")


def _normalize_inputs(
    inputs: Sequence[ResearchStrategyProbabilityGapExplainabilityDecayInput],
) -> tuple[ResearchStrategyProbabilityGapExplainabilityDecayInput, ...]:
    if isinstance(inputs, (str, bytes)) or not isinstance(inputs, Sequence):
        raise ValueError("inputs must be a sequence")
    rows = tuple(inputs)
    for item in rows:
        if type(item) is not ResearchStrategyProbabilityGapExplainabilityDecayInput:
            raise ValueError(
                "inputs must contain ResearchStrategyProbabilityGapExplainabilityDecayInput",
            )
        _require_hard_flags("input", item)
    digests = tuple(_gap_ref_digest(item.candidate_ref, item.surface_ref) for item in rows)
    if len(set(digests)) != len(digests):
        raise ValueError("inputs must not contain duplicate private refs")
    return rows


def _normalize_rows(
    rows: Sequence[ResearchStrategyProbabilityGapExplainabilityDecayRow],
) -> tuple[ResearchStrategyProbabilityGapExplainabilityDecayRow, ...]:
    if isinstance(rows, (str, bytes)) or not isinstance(rows, Sequence):
        raise ValueError("rows must be a sequence")
    normalized = tuple(rows)
    for row in normalized:
        if type(row) is not ResearchStrategyProbabilityGapExplainabilityDecayRow:
            raise ValueError(
                "rows must contain ResearchStrategyProbabilityGapExplainabilityDecayRow",
            )
        _require_hard_flags("row", row)
    return normalized


def _normalize_reason_code_counts(
    counts: Sequence[ResearchStrategyProbabilityGapExplainabilityDecayReasonCodeCount],
) -> tuple[ResearchStrategyProbabilityGapExplainabilityDecayReasonCodeCount, ...]:
    if isinstance(counts, (str, bytes)) or not isinstance(counts, Sequence):
        raise ValueError("reason_code_counts must be a sequence")
    normalized = tuple(counts)
    for item in normalized:
        if type(item) is not ResearchStrategyProbabilityGapExplainabilityDecayReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "ResearchStrategyProbabilityGapExplainabilityDecayReasonCodeCount",
            )
        _require_hard_flags("reason count", item)
    return normalized


def _normalize_reason_codes(
    field_name: str,
    values: Sequence[str],
    allowed: tuple[str, ...],
) -> tuple[str, ...]:
    if isinstance(values, (str, bytes)) or not isinstance(values, Sequence):
        raise ValueError(f"{field_name} must be a sequence")
    seen: set[str] = set()
    normalized: list[str] = []
    for value in values:
        if type(value) is not str:
            raise ValueError(f"{field_name} entries must be strings")
        _require_reason_code(field_name, value, allowed)
        if value not in seen:
            seen.add(value)
            normalized.append(value)
    order = {reason_code: index for index, reason_code in enumerate(allowed)}
    return tuple(sorted(normalized, key=lambda reason_code: order[reason_code]))


def _require_reason_code(field_name: str, value: str, allowed: tuple[str, ...]) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if value not in allowed:
        raise ValueError(f"{field_name} contains unsupported reason code: {value}")
    return value


def _require_exact_type(value: object, expected: type[object], label: str) -> None:
    if type(value) is not expected:
        raise ValueError(f"{label} must be exactly {expected.__name__}")


def _require_public_identifier(field_name: str, value: str) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if _PUBLIC_IDENTIFIER_RE.fullmatch(value) is None:
        raise ValueError(f"{field_name} must be a public identifier")
    _reject_unsafe_public_string(field_name, value)
    return value


def _require_private_ref(field_name: str, value: str) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if value.strip() == "":
        raise ValueError(f"{field_name} must not be blank")
    return value


def _require_private_digest(field_name: str, value: str) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if _PRIVATE_DIGEST_RE.fullmatch(value) is None:
        raise ValueError(f"{field_name} must be a private sha256 digest")
    return value


def _require_digest(field_name: str, value: str) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if _DIGEST_RE.fullmatch(value) is None:
        raise ValueError(f"{field_name} must be a sha256 digest")
    return value


def _require_status(field_name: str, value: str) -> str:
    return _require_member(field_name, value, _STATUS_VALUES)


def _require_member(field_name: str, value: str, allowed: frozenset[str]) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if value not in allowed:
        raise ValueError(f"{field_name} must be pass, watch, or block")
    return value


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if getattr(value, field_name) is not True:
            raise ValueError(f"{field_name} must be True for {label}")


def _require_ratio_decimal(field_name: str, value: Decimal) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value < _ZERO or decimal_value > _ONE:
        raise ValueError(f"{field_name} must be between zero and one")
    return decimal_value


def _require_nonnegative_decimal(field_name: str, value: Decimal) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value < _ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return decimal_value


def _require_nonnegative_count_decimal(field_name: str, value: Decimal) -> Decimal:
    return _require_nonnegative_decimal(field_name, value)


def _require_positive_decimal(field_name: str, value: Decimal) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value <= _ZERO:
        raise ValueError(f"{field_name} must be positive")
    return decimal_value


def _require_decimal(field_name: str, value: Decimal) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return _quantize(value)


def _require_floor_pair(field_name: str, pass_floor: Decimal, watch_floor: Decimal) -> None:
    if pass_floor < watch_floor:
        raise ValueError(f"pass_min_{field_name} must be at least watch_min_{field_name}")


def _require_ceiling_pair(
    field_name: str,
    pass_ceiling: Decimal,
    watch_ceiling: Decimal,
) -> None:
    if pass_ceiling > watch_ceiling:
        raise ValueError(f"max_pass_{field_name} must not exceed max_watch_{field_name}")


def _as_utc(field_name: str, value: datetime) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _absolute_probability_gap(model_probability: Decimal, public_probability: Decimal) -> Decimal:
    return _quantize(abs(model_probability - public_probability))


def _gap_direction(model_probability: Decimal, public_probability: Decimal) -> str:
    if model_probability > public_probability:
        return GAP_DIRECTION_MODEL_ABOVE_PUBLIC
    if model_probability < public_probability:
        return GAP_DIRECTION_MODEL_BELOW_PUBLIC
    return GAP_DIRECTION_ALIGNED


def _stability_score(value: Decimal, watch_ceiling: Decimal) -> Decimal:
    if value >= watch_ceiling:
        return _ZERO
    return _clamp_ratio(_ONE - (value / watch_ceiling))


def _inverse_ratio(value: Decimal) -> Decimal:
    return _clamp_ratio(_ONE - value)


def _clamp_ratio(value: Decimal) -> Decimal:
    quantized = _quantize(value)
    if quantized < _ZERO:
        return _ZERO
    if quantized > _ONE:
        return _ONE
    return quantized


def _average_ratio(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return _ZERO
    return _ratio(sum(values, _ZERO), _decimal_count(len(values)))


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == _ZERO:
        return _ZERO
    return _clamp_ratio(numerator / denominator)


def _decimal_count(value: int) -> Decimal:
    return _quantize(Decimal(value))


def _quantize(value: Decimal) -> Decimal:
    return value.quantize(_QUANT, rounding=ROUND_HALF_UP)


def _gap_ref_digest(candidate_ref: str, surface_ref: str) -> str:
    digest = sha256(f"{candidate_ref}\n{surface_ref}".encode("utf-8")).hexdigest()
    return f"sha256:{digest}"


__all__ = (
    "DEFAULT_RESEARCH_STRATEGY_PROBABILITY_GAP_EXPLAINABILITY_DECAY_REPORT_CONFIG_VERSION",
    "RESEARCH_STRATEGY_PROBABILITY_GAP_EXPLAINABILITY_DECAY_STATUSES",
    "ResearchStrategyProbabilityGapExplainabilityDecayConfig",
    "ResearchStrategyProbabilityGapExplainabilityDecayInput",
    "ResearchStrategyProbabilityGapExplainabilityDecayReasonCodeCount",
    "ResearchStrategyProbabilityGapExplainabilityDecayReport",
    "ResearchStrategyProbabilityGapExplainabilityDecayRow",
    "build_research_strategy_probability_gap_explainability_decay_report",
    "research_strategy_probability_gap_explainability_decay_report_payload",
)
