"""Report-only outcome-learning edge decay scorecard.

This module evaluates whether settled-outcome feedback is improving or
protecting probability edge quality without exposing raw research identifiers
or any execution surface.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import InitVar, asdict, dataclass, field, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, InvalidOperation, ROUND_HALF_UP, localcontext
from hashlib import sha256
import json
import re
from typing import Any, Sequence


DEFAULT_RESEARCH_STRATEGY_OUTCOME_LEARNING_EDGE_DECAY_REPORT_CONFIG_VERSION = (
    "research-strategy-outcome-learning-edge-decay-report-v0"
)

STATUS_PASS = "pass"
STATUS_WATCH = "watch"
STATUS_BLOCK = "block"
RESEARCH_STRATEGY_OUTCOME_LEARNING_EDGE_DECAY_STATUSES = (
    STATUS_PASS,
    STATUS_WATCH,
    STATUS_BLOCK,
)

REASON_EMPTY_INPUT = "empty_input"
REASON_SETTLED_OUTCOME_FEEDBACK_READY = "settled_outcome_feedback_ready"
REASON_CALIBRATION_UPDATE_READY = "calibration_update_ready"
REASON_EVIDENCE_REUSE_READY = "evidence_reuse_ready"
REASON_EDGE_DECAY_BLOCK = "edge_decay_block"
REASON_SETTLED_FEEDBACK_BLOCK = "settled_feedback_block"
REASON_CALIBRATION_UPDATE_BLOCK = "calibration_update_block"
REASON_EVIDENCE_REUSE_BLOCK = "evidence_reuse_block"
REASON_COST_PRESSURE_BLOCK = "cost_pressure_block"
REASON_STALE_THESIS_PRESSURE_BLOCK = "stale_thesis_pressure_block"
REASON_OUTCOME_LEARNING_SCORE_BLOCK = "outcome_learning_score_block"
REASON_EDGE_DECAY_WATCH = "edge_decay_watch"
REASON_SETTLED_FEEDBACK_WATCH = "settled_feedback_watch"
REASON_CALIBRATION_UPDATE_WATCH = "calibration_update_watch"
REASON_EVIDENCE_REUSE_WATCH = "evidence_reuse_watch"
REASON_COST_PRESSURE_WATCH = "cost_pressure_watch"
REASON_STALE_THESIS_PRESSURE_WATCH = "stale_thesis_pressure_watch"
REASON_OUTCOME_LEARNING_SCORE_WATCH = "outcome_learning_score_watch"
REASON_OUTCOME_LEARNING_PASS = "outcome_learning_pass"

_UPSTREAM_REASON_CODE_SEQUENCE = (
    REASON_SETTLED_OUTCOME_FEEDBACK_READY,
    REASON_CALIBRATION_UPDATE_READY,
    REASON_EVIDENCE_REUSE_READY,
)
_GENERATED_ROW_REASON_CODE_SEQUENCE = (
    REASON_EDGE_DECAY_BLOCK,
    REASON_SETTLED_FEEDBACK_BLOCK,
    REASON_CALIBRATION_UPDATE_BLOCK,
    REASON_EVIDENCE_REUSE_BLOCK,
    REASON_COST_PRESSURE_BLOCK,
    REASON_STALE_THESIS_PRESSURE_BLOCK,
    REASON_OUTCOME_LEARNING_SCORE_BLOCK,
    REASON_EDGE_DECAY_WATCH,
    REASON_SETTLED_FEEDBACK_WATCH,
    REASON_CALIBRATION_UPDATE_WATCH,
    REASON_EVIDENCE_REUSE_WATCH,
    REASON_COST_PRESSURE_WATCH,
    REASON_STALE_THESIS_PRESSURE_WATCH,
    REASON_OUTCOME_LEARNING_SCORE_WATCH,
    REASON_OUTCOME_LEARNING_PASS,
)
_ROW_REASON_CODE_SEQUENCE = (
    *_UPSTREAM_REASON_CODE_SEQUENCE,
    *_GENERATED_ROW_REASON_CODE_SEQUENCE,
)
_REASON_CODE_SEQUENCE = (REASON_EMPTY_INPUT, *_ROW_REASON_CODE_SEQUENCE)
_BLOCK_REASON_CODES = frozenset(
    (
        REASON_EDGE_DECAY_BLOCK,
        REASON_SETTLED_FEEDBACK_BLOCK,
        REASON_CALIBRATION_UPDATE_BLOCK,
        REASON_EVIDENCE_REUSE_BLOCK,
        REASON_COST_PRESSURE_BLOCK,
        REASON_STALE_THESIS_PRESSURE_BLOCK,
        REASON_OUTCOME_LEARNING_SCORE_BLOCK,
    ),
)

_QUANT = Decimal("0.000001")
_ZERO = Decimal("0.000000")
_ONE = Decimal("1.000000")
_DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_UP)
_DIGEST_FIELD = "derived_validation_digest"
_STATUS_VALUES = frozenset(RESEARCH_STRATEGY_OUTCOME_LEARNING_EDGE_DECAY_STATUSES)
_PUBLIC_IDENTIFIER_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,127}$")
_DIGEST_RE = re.compile(r"^[0-9a-f]{64}$")
_PRIVATE_DIGEST_RE = re.compile(r"^sha256:[0-9a-f]{64}$")
_PUBLIC_DECIMAL_RE = re.compile(r"^(?:0|[1-9][0-9]*)\.[0-9]{6}$")
_PUBLIC_REPORT_FIELDS = (
    "generated_at",
    "config_version",
    "config",
    "status",
    "input_count",
    "pass_count",
    "watch_count",
    "block_count",
    "average_outcome_learning_score",
    "min_outcome_learning_score",
    "max_probability_edge_decay_ratio",
    "min_settled_outcome_feedback_score",
    "min_calibration_update_quality_score",
    "min_evidence_reuse_score",
    "max_cost_pressure_score",
    "max_stale_thesis_pressure_score",
    "rows",
    "reason_code_counts",
    "reason_codes",
    _DIGEST_FIELD,
    "paper_only",
    "report_only",
    "readonly",
)
_PUBLIC_CONFIG_FIELDS = (
    "config_version",
    "pass_min_outcome_learning_score",
    "watch_min_outcome_learning_score",
    "max_pass_probability_edge_decay_ratio",
    "max_watch_probability_edge_decay_ratio",
    "min_pass_settled_outcome_feedback_score",
    "min_watch_settled_outcome_feedback_score",
    "min_pass_calibration_update_quality_score",
    "min_watch_calibration_update_quality_score",
    "min_pass_evidence_reuse_score",
    "min_watch_evidence_reuse_score",
    "max_pass_cost_pressure_score",
    "max_watch_cost_pressure_score",
    "max_pass_stale_thesis_pressure_score",
    "max_watch_stale_thesis_pressure_score",
    "settled_feedback_weight",
    "calibration_update_weight",
    "evidence_reuse_weight",
    "cost_pressure_weight",
    "stale_thesis_weight",
    "edge_retention_weight",
    "paper_only",
    "report_only",
    "readonly",
)
_PUBLIC_ROW_FIELDS = (
    "learning_ref_digest",
    "observed_at",
    "pre_feedback_probability_edge",
    "post_feedback_probability_edge",
    "probability_edge_decay_ratio",
    "edge_retention_score",
    "settled_outcome_feedback_score",
    "calibration_update_quality_score",
    "evidence_reuse_score",
    "cost_pressure_score",
    "cost_relief_score",
    "stale_thesis_pressure_score",
    "thesis_freshness_score",
    "outcome_learning_score",
    "status",
    "reason_codes",
    "paper_only",
    "report_only",
    "readonly",
)
_PUBLIC_REASON_CODE_COUNT_FIELDS = (
    "reason_code",
    "count",
    "input_ratio",
    "paper_only",
    "report_only",
    "readonly",
)
_INPUT_FIELDS = (
    "candidate_ref",
    "surface_ref",
    "observed_at",
    "pre_feedback_probability_edge",
    "post_feedback_probability_edge",
    "settled_outcome_feedback_score",
    "calibration_update_quality_score",
    "evidence_reuse_score",
    "cost_pressure_score",
    "stale_thesis_pressure_score",
    "reason_codes",
    "paper_only",
    "report_only",
    "readonly",
)
_UNSAFE_PUBLIC_FRAGMENTS = (
    "candidate",
    "market",
    "slug",
    "question",
    "source",
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
    "live",
    "execute",
    "execution",
    "position",
    "sizing",
    "recommend",
    "private_key",
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
class ResearchStrategyOutcomeLearningEdgeDecayConfig(_FinalPublicDataclass):
    config_version: str = (
        DEFAULT_RESEARCH_STRATEGY_OUTCOME_LEARNING_EDGE_DECAY_REPORT_CONFIG_VERSION
    )
    pass_min_outcome_learning_score: Decimal = Decimal("0.750000")
    watch_min_outcome_learning_score: Decimal = Decimal("0.550000")
    max_pass_probability_edge_decay_ratio: Decimal = Decimal("0.200000")
    max_watch_probability_edge_decay_ratio: Decimal = Decimal("0.450000")
    min_pass_settled_outcome_feedback_score: Decimal = Decimal("0.750000")
    min_watch_settled_outcome_feedback_score: Decimal = Decimal("0.500000")
    min_pass_calibration_update_quality_score: Decimal = Decimal("0.750000")
    min_watch_calibration_update_quality_score: Decimal = Decimal("0.500000")
    min_pass_evidence_reuse_score: Decimal = Decimal("0.700000")
    min_watch_evidence_reuse_score: Decimal = Decimal("0.450000")
    max_pass_cost_pressure_score: Decimal = Decimal("0.250000")
    max_watch_cost_pressure_score: Decimal = Decimal("0.500000")
    max_pass_stale_thesis_pressure_score: Decimal = Decimal("0.200000")
    max_watch_stale_thesis_pressure_score: Decimal = Decimal("0.450000")
    settled_feedback_weight: Decimal = Decimal("0.250000")
    calibration_update_weight: Decimal = Decimal("0.250000")
    evidence_reuse_weight: Decimal = Decimal("0.150000")
    cost_pressure_weight: Decimal = Decimal("0.150000")
    stale_thesis_weight: Decimal = Decimal("0.100000")
    edge_retention_weight: Decimal = Decimal("0.100000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchStrategyOutcomeLearningEdgeDecayConfig, "config")
        object.__setattr__(
            self,
            "config_version",
            _require_public_identifier("config_version", self.config_version),
        )
        if (
            self.config_version
            != DEFAULT_RESEARCH_STRATEGY_OUTCOME_LEARNING_EDGE_DECAY_REPORT_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "pass_min_outcome_learning_score",
            "watch_min_outcome_learning_score",
            "max_pass_probability_edge_decay_ratio",
            "max_watch_probability_edge_decay_ratio",
            "min_pass_settled_outcome_feedback_score",
            "min_watch_settled_outcome_feedback_score",
            "min_pass_calibration_update_quality_score",
            "min_watch_calibration_update_quality_score",
            "min_pass_evidence_reuse_score",
            "min_watch_evidence_reuse_score",
            "max_pass_cost_pressure_score",
            "max_watch_cost_pressure_score",
            "max_pass_stale_thesis_pressure_score",
            "max_watch_stale_thesis_pressure_score",
            "settled_feedback_weight",
            "calibration_update_weight",
            "evidence_reuse_weight",
            "cost_pressure_weight",
            "stale_thesis_weight",
            "edge_retention_weight",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        _require_floor_pair(
            "pass_min_outcome_learning_score",
            self.pass_min_outcome_learning_score,
            "watch_min_outcome_learning_score",
            self.watch_min_outcome_learning_score,
        )
        _require_ceiling_pair(
            "max_pass_probability_edge_decay_ratio",
            self.max_pass_probability_edge_decay_ratio,
            "max_watch_probability_edge_decay_ratio",
            self.max_watch_probability_edge_decay_ratio,
        )
        _require_floor_pair(
            "min_pass_settled_outcome_feedback_score",
            self.min_pass_settled_outcome_feedback_score,
            "min_watch_settled_outcome_feedback_score",
            self.min_watch_settled_outcome_feedback_score,
        )
        _require_floor_pair(
            "min_pass_calibration_update_quality_score",
            self.min_pass_calibration_update_quality_score,
            "min_watch_calibration_update_quality_score",
            self.min_watch_calibration_update_quality_score,
        )
        _require_floor_pair(
            "min_pass_evidence_reuse_score",
            self.min_pass_evidence_reuse_score,
            "min_watch_evidence_reuse_score",
            self.min_watch_evidence_reuse_score,
        )
        _require_ceiling_pair(
            "max_pass_cost_pressure_score",
            self.max_pass_cost_pressure_score,
            "max_watch_cost_pressure_score",
            self.max_watch_cost_pressure_score,
        )
        _require_ceiling_pair(
            "max_pass_stale_thesis_pressure_score",
            self.max_pass_stale_thesis_pressure_score,
            "max_watch_stale_thesis_pressure_score",
            self.max_watch_stale_thesis_pressure_score,
        )
        with localcontext(_DECIMAL_CONTEXT):
            weight_sum = _quantize(
                sum(
                    (
                        self.settled_feedback_weight,
                        self.calibration_update_weight,
                        self.evidence_reuse_weight,
                        self.cost_pressure_weight,
                        self.stale_thesis_weight,
                        self.edge_retention_weight,
                    ),
                    _ZERO,
                ),
                field_name="outcome_learning weights",
            )
        if weight_sum != _ONE:
            raise ValueError("outcome_learning weights must sum to one")
        _require_hard_flags("config", self)
        _reject_unsafe_public_payload("config", self)


@dataclass(frozen=True)
class ResearchStrategyOutcomeLearningEdgeDecayInput(_FinalPublicDataclass):
    candidate_ref: str
    surface_ref: str
    observed_at: datetime
    pre_feedback_probability_edge: Decimal
    post_feedback_probability_edge: Decimal
    settled_outcome_feedback_score: Decimal
    calibration_update_quality_score: Decimal
    evidence_reuse_score: Decimal
    cost_pressure_score: Decimal
    stale_thesis_pressure_score: Decimal
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchStrategyOutcomeLearningEdgeDecayInput, "input")
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
            "pre_feedback_probability_edge",
            "post_feedback_probability_edge",
            "settled_outcome_feedback_score",
            "calibration_update_quality_score",
            "evidence_reuse_score",
            "cost_pressure_score",
            "stale_thesis_pressure_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
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
class ResearchStrategyOutcomeLearningEdgeDecayReasonCodeCount(_FinalPublicDataclass):
    reason_code: str
    count: Decimal
    input_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchStrategyOutcomeLearningEdgeDecayReasonCodeCount,
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
class ResearchStrategyOutcomeLearningEdgeDecayRow(_FinalPublicDataclass):
    learning_ref_digest: str
    observed_at: datetime
    pre_feedback_probability_edge: Decimal
    post_feedback_probability_edge: Decimal
    probability_edge_decay_ratio: Decimal
    edge_retention_score: Decimal
    settled_outcome_feedback_score: Decimal
    calibration_update_quality_score: Decimal
    evidence_reuse_score: Decimal
    cost_pressure_score: Decimal
    cost_relief_score: Decimal
    stale_thesis_pressure_score: Decimal
    thesis_freshness_score: Decimal
    outcome_learning_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True
    validation_config: InitVar[
        ResearchStrategyOutcomeLearningEdgeDecayConfig | None
    ] = None

    def __post_init__(
        self,
        validation_config: ResearchStrategyOutcomeLearningEdgeDecayConfig | None,
    ) -> None:
        _require_exact_type(self, ResearchStrategyOutcomeLearningEdgeDecayRow, "row")
        object.__setattr__(
            self,
            "learning_ref_digest",
            _require_private_digest("learning_ref_digest", self.learning_ref_digest),
        )
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in (
            "pre_feedback_probability_edge",
            "post_feedback_probability_edge",
            "probability_edge_decay_ratio",
            "edge_retention_score",
            "settled_outcome_feedback_score",
            "calibration_update_quality_score",
            "evidence_reuse_score",
            "cost_pressure_score",
            "cost_relief_score",
            "stale_thesis_pressure_score",
            "thesis_freshness_score",
            "outcome_learning_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
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
class ResearchStrategyOutcomeLearningEdgeDecayReport(_FinalPublicDataclass):
    generated_at: datetime
    config_version: str
    config: ResearchStrategyOutcomeLearningEdgeDecayConfig = field(
        default_factory=ResearchStrategyOutcomeLearningEdgeDecayConfig,
        kw_only=True,
    )
    status: str
    input_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    average_outcome_learning_score: Decimal
    min_outcome_learning_score: Decimal
    max_probability_edge_decay_ratio: Decimal
    min_settled_outcome_feedback_score: Decimal
    min_calibration_update_quality_score: Decimal
    min_evidence_reuse_score: Decimal
    max_cost_pressure_score: Decimal
    max_stale_thesis_pressure_score: Decimal
    rows: tuple[ResearchStrategyOutcomeLearningEdgeDecayRow, ...]
    reason_code_counts: tuple[
        ResearchStrategyOutcomeLearningEdgeDecayReasonCodeCount,
        ...,
    ]
    reason_codes: tuple[str, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchStrategyOutcomeLearningEdgeDecayReport, "report")
        _require_expected_dataclass_state("report", self, _PUBLIC_REPORT_FIELDS)
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        object.__setattr__(
            self,
            "config_version",
            _require_public_identifier("config_version", self.config_version),
        )
        if (
            self.config_version
            != DEFAULT_RESEARCH_STRATEGY_OUTCOME_LEARNING_EDGE_DECAY_REPORT_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        object.__setattr__(self, "config", _revalidated_config(self.config))
        if self.config_version != self.config.config_version:
            raise ValueError("config_version must match config")
        _require_status("status", self.status)
        for field_name in ("input_count", "pass_count", "watch_count", "block_count"):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_count_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "average_outcome_learning_score",
            "min_outcome_learning_score",
            "max_probability_edge_decay_ratio",
            "min_settled_outcome_feedback_score",
            "min_calibration_update_quality_score",
            "min_evidence_reuse_score",
            "max_cost_pressure_score",
            "max_stale_thesis_pressure_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(self, "rows", _normalize_rows(self.rows, self.config))
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
        return research_strategy_outcome_learning_edge_decay_report_payload(self)


def build_research_strategy_outcome_learning_edge_decay_report(
    inputs: Sequence[ResearchStrategyOutcomeLearningEdgeDecayInput],
    *,
    generated_at: datetime,
    config: ResearchStrategyOutcomeLearningEdgeDecayConfig | None = None,
) -> ResearchStrategyOutcomeLearningEdgeDecayReport:
    """Build a deterministic readonly outcome-learning edge decay report."""

    cfg = _revalidated_config(config or ResearchStrategyOutcomeLearningEdgeDecayConfig())
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
            ResearchStrategyOutcomeLearningEdgeDecayReasonCodeCount(
                reason_code=REASON_EMPTY_INPUT,
                count=_ONE,
                input_ratio=_ONE,
            ),
        )
        reason_codes = (REASON_EMPTY_INPUT,)
    values: dict[str, object] = {
        "generated_at": report_time,
        "config_version": cfg.config_version,
        "config": cfg,
        "status": _report_status(rows),
        "input_count": _decimal_count(len(rows)),
        "pass_count": _decimal_count(_status_count(rows, STATUS_PASS)),
        "watch_count": _decimal_count(_status_count(rows, STATUS_WATCH)),
        "block_count": _decimal_count(_status_count(rows, STATUS_BLOCK)),
        "average_outcome_learning_score": _average_ratio(
            tuple(row.outcome_learning_score for row in rows),
        ),
        "min_outcome_learning_score": min(
            (row.outcome_learning_score for row in rows),
            default=_ZERO,
        ),
        "max_probability_edge_decay_ratio": max(
            (row.probability_edge_decay_ratio for row in rows),
            default=_ZERO,
        ),
        "min_settled_outcome_feedback_score": min(
            (row.settled_outcome_feedback_score for row in rows),
            default=_ZERO,
        ),
        "min_calibration_update_quality_score": min(
            (row.calibration_update_quality_score for row in rows),
            default=_ZERO,
        ),
        "min_evidence_reuse_score": min(
            (row.evidence_reuse_score for row in rows),
            default=_ZERO,
        ),
        "max_cost_pressure_score": max(
            (row.cost_pressure_score for row in rows),
            default=_ZERO,
        ),
        "max_stale_thesis_pressure_score": max(
            (row.stale_thesis_pressure_score for row in rows),
            default=_ZERO,
        ),
        "rows": rows,
        "reason_code_counts": reason_code_counts,
        "reason_codes": reason_codes,
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    report = ResearchStrategyOutcomeLearningEdgeDecayReport(
        **values,
        derived_validation_digest=_report_digest_from_values(values),
    )
    return report


def research_strategy_outcome_learning_edge_decay_report_payload(
    value: ResearchStrategyOutcomeLearningEdgeDecayReport | dict[str, object],
) -> dict[str, object]:
    if type(value) is ResearchStrategyOutcomeLearningEdgeDecayReport:
        _require_hard_flags("report", value)
        payload = _report_payload(value)
    elif type(value) is dict:
        payload = _copy_json_object(value)
    else:
        raise ValueError(
            "value must be a ResearchStrategyOutcomeLearningEdgeDecayReport or dict",
        )
    _reject_unsafe_public_payload("payload", payload, allow_json_containers=True)
    _validate_payload_statuses(payload)
    _validate_payload_flags(payload)
    _validate_payload_private_digests(payload)
    _validate_payload_digest(payload)
    _validate_public_payload_schema(payload)
    return payload


def _row_for_input(
    item: ResearchStrategyOutcomeLearningEdgeDecayInput,
    config: ResearchStrategyOutcomeLearningEdgeDecayConfig,
) -> ResearchStrategyOutcomeLearningEdgeDecayRow:
    edge_decay_ratio = _edge_decay_ratio(
        item.pre_feedback_probability_edge,
        item.post_feedback_probability_edge,
    )
    edge_retention_score = _inverse_ratio(edge_decay_ratio)
    cost_relief_score = _inverse_ratio(item.cost_pressure_score)
    thesis_freshness_score = _inverse_ratio(item.stale_thesis_pressure_score)
    outcome_learning_score = _outcome_learning_score(
        settled_outcome_feedback_score=item.settled_outcome_feedback_score,
        calibration_update_quality_score=item.calibration_update_quality_score,
        evidence_reuse_score=item.evidence_reuse_score,
        cost_relief_score=cost_relief_score,
        thesis_freshness_score=thesis_freshness_score,
        edge_retention_score=edge_retention_score,
        config=config,
    )
    reason_codes = _row_reason_codes(
        upstream_reason_codes=item.reason_codes,
        probability_edge_decay_ratio=edge_decay_ratio,
        settled_outcome_feedback_score=item.settled_outcome_feedback_score,
        calibration_update_quality_score=item.calibration_update_quality_score,
        evidence_reuse_score=item.evidence_reuse_score,
        cost_pressure_score=item.cost_pressure_score,
        stale_thesis_pressure_score=item.stale_thesis_pressure_score,
        outcome_learning_score=outcome_learning_score,
        config=config,
    )
    return ResearchStrategyOutcomeLearningEdgeDecayRow(
        learning_ref_digest=_learning_ref_digest(item.candidate_ref, item.surface_ref),
        observed_at=item.observed_at,
        pre_feedback_probability_edge=item.pre_feedback_probability_edge,
        post_feedback_probability_edge=item.post_feedback_probability_edge,
        probability_edge_decay_ratio=edge_decay_ratio,
        edge_retention_score=edge_retention_score,
        settled_outcome_feedback_score=item.settled_outcome_feedback_score,
        calibration_update_quality_score=item.calibration_update_quality_score,
        evidence_reuse_score=item.evidence_reuse_score,
        cost_pressure_score=item.cost_pressure_score,
        cost_relief_score=cost_relief_score,
        stale_thesis_pressure_score=item.stale_thesis_pressure_score,
        thesis_freshness_score=thesis_freshness_score,
        outcome_learning_score=outcome_learning_score,
        status=_row_status(reason_codes),
        reason_codes=reason_codes,
        validation_config=config,
    )


def _row_reason_codes(
    *,
    upstream_reason_codes: tuple[str, ...],
    probability_edge_decay_ratio: Decimal,
    settled_outcome_feedback_score: Decimal,
    calibration_update_quality_score: Decimal,
    evidence_reuse_score: Decimal,
    cost_pressure_score: Decimal,
    stale_thesis_pressure_score: Decimal,
    outcome_learning_score: Decimal,
    config: ResearchStrategyOutcomeLearningEdgeDecayConfig,
) -> tuple[str, ...]:
    reason_codes = list(upstream_reason_codes)
    if probability_edge_decay_ratio > config.max_watch_probability_edge_decay_ratio:
        reason_codes.append(REASON_EDGE_DECAY_BLOCK)
    elif probability_edge_decay_ratio > config.max_pass_probability_edge_decay_ratio:
        reason_codes.append(REASON_EDGE_DECAY_WATCH)
    if settled_outcome_feedback_score < config.min_watch_settled_outcome_feedback_score:
        reason_codes.append(REASON_SETTLED_FEEDBACK_BLOCK)
    elif settled_outcome_feedback_score < config.min_pass_settled_outcome_feedback_score:
        reason_codes.append(REASON_SETTLED_FEEDBACK_WATCH)
    if (
        calibration_update_quality_score
        < config.min_watch_calibration_update_quality_score
    ):
        reason_codes.append(REASON_CALIBRATION_UPDATE_BLOCK)
    elif (
        calibration_update_quality_score
        < config.min_pass_calibration_update_quality_score
    ):
        reason_codes.append(REASON_CALIBRATION_UPDATE_WATCH)
    if evidence_reuse_score < config.min_watch_evidence_reuse_score:
        reason_codes.append(REASON_EVIDENCE_REUSE_BLOCK)
    elif evidence_reuse_score < config.min_pass_evidence_reuse_score:
        reason_codes.append(REASON_EVIDENCE_REUSE_WATCH)
    if cost_pressure_score > config.max_watch_cost_pressure_score:
        reason_codes.append(REASON_COST_PRESSURE_BLOCK)
    elif cost_pressure_score > config.max_pass_cost_pressure_score:
        reason_codes.append(REASON_COST_PRESSURE_WATCH)
    if stale_thesis_pressure_score > config.max_watch_stale_thesis_pressure_score:
        reason_codes.append(REASON_STALE_THESIS_PRESSURE_BLOCK)
    elif stale_thesis_pressure_score > config.max_pass_stale_thesis_pressure_score:
        reason_codes.append(REASON_STALE_THESIS_PRESSURE_WATCH)
    if outcome_learning_score < config.watch_min_outcome_learning_score:
        reason_codes.append(REASON_OUTCOME_LEARNING_SCORE_BLOCK)
    elif outcome_learning_score < config.pass_min_outcome_learning_score:
        reason_codes.append(REASON_OUTCOME_LEARNING_SCORE_WATCH)
    generated = tuple(
        reason_code
        for reason_code in reason_codes
        if reason_code in _GENERATED_ROW_REASON_CODE_SEQUENCE
    )
    if not generated:
        reason_codes.append(REASON_OUTCOME_LEARNING_PASS)
    return _normalize_reason_codes(
        "reason_codes",
        tuple(reason_codes),
        _ROW_REASON_CODE_SEQUENCE,
    )


def _row_status(reason_codes: tuple[str, ...]) -> str:
    if any(reason_code in _BLOCK_REASON_CODES for reason_code in reason_codes):
        return STATUS_BLOCK
    if REASON_OUTCOME_LEARNING_PASS in reason_codes:
        return STATUS_PASS
    return STATUS_WATCH


def _report_status(
    rows: tuple[ResearchStrategyOutcomeLearningEdgeDecayRow, ...],
) -> str:
    if not rows:
        return STATUS_BLOCK
    if any(row.status == STATUS_BLOCK for row in rows):
        return STATUS_BLOCK
    if any(row.status == STATUS_WATCH for row in rows):
        return STATUS_WATCH
    return STATUS_PASS


def _status_count(
    rows: tuple[ResearchStrategyOutcomeLearningEdgeDecayRow, ...],
    status: str,
) -> int:
    return sum(1 for row in rows if row.status == status)


def _row_sort_key(
    row: ResearchStrategyOutcomeLearningEdgeDecayRow,
) -> tuple[
    int,
    Decimal,
    Decimal,
    Decimal,
    Decimal,
    Decimal,
    Decimal,
    Decimal,
    Decimal,
    Decimal,
    Decimal,
    Decimal,
    Decimal,
    datetime,
    tuple[str, ...],
    str,
]:
    return (
        _status_rank(row.status),
        row.outcome_learning_score,
        row.probability_edge_decay_ratio,
        row.pre_feedback_probability_edge,
        row.post_feedback_probability_edge,
        row.edge_retention_score,
        row.settled_outcome_feedback_score,
        row.calibration_update_quality_score,
        row.evidence_reuse_score,
        row.cost_pressure_score,
        row.cost_relief_score,
        row.stale_thesis_pressure_score,
        row.thesis_freshness_score,
        row.observed_at,
        row.reason_codes,
        row.learning_ref_digest,
    )


def _status_rank(value: str) -> int:
    return {STATUS_BLOCK: 0, STATUS_WATCH: 1, STATUS_PASS: 2}[value]


def _reason_code_counts(
    rows: tuple[ResearchStrategyOutcomeLearningEdgeDecayRow, ...],
) -> tuple[ResearchStrategyOutcomeLearningEdgeDecayReasonCodeCount, ...]:
    total = _decimal_count(len(rows))
    counts: Counter[str] = Counter(
        reason_code for row in rows for reason_code in row.reason_codes
    )
    return tuple(
        ResearchStrategyOutcomeLearningEdgeDecayReasonCodeCount(
            reason_code=reason_code,
            count=_decimal_count(count),
            input_ratio=_ratio(_decimal_count(count), total),
        )
        for reason_code in _REASON_CODE_SEQUENCE
        if (count := counts.get(reason_code, 0)) > 0
    )


def _outcome_learning_score(
    *,
    settled_outcome_feedback_score: Decimal,
    calibration_update_quality_score: Decimal,
    evidence_reuse_score: Decimal,
    cost_relief_score: Decimal,
    thesis_freshness_score: Decimal,
    edge_retention_score: Decimal,
    config: ResearchStrategyOutcomeLearningEdgeDecayConfig,
) -> Decimal:
    with localcontext(_DECIMAL_CONTEXT):
        score = (
            settled_outcome_feedback_score * config.settled_feedback_weight
            + calibration_update_quality_score * config.calibration_update_weight
            + evidence_reuse_score * config.evidence_reuse_weight
            + cost_relief_score * config.cost_pressure_weight
            + thesis_freshness_score * config.stale_thesis_weight
            + edge_retention_score * config.edge_retention_weight
        )
    return _clamp_ratio(score)


def _validate_row(
    row: ResearchStrategyOutcomeLearningEdgeDecayRow,
    config: ResearchStrategyOutcomeLearningEdgeDecayConfig | None,
) -> None:
    if row.probability_edge_decay_ratio != _edge_decay_ratio(
        row.pre_feedback_probability_edge,
        row.post_feedback_probability_edge,
    ):
        raise ValueError("probability_edge_decay_ratio must match feedback edges")
    if row.edge_retention_score != _inverse_ratio(row.probability_edge_decay_ratio):
        raise ValueError("edge_retention_score must match probability_edge_decay_ratio")
    if row.cost_relief_score != _inverse_ratio(row.cost_pressure_score):
        raise ValueError("cost_relief_score must match cost_pressure_score")
    if row.thesis_freshness_score != _inverse_ratio(row.stale_thesis_pressure_score):
        raise ValueError("thesis_freshness_score must match stale_thesis_pressure_score")
    if row.status != _row_status(row.reason_codes):
        raise ValueError("status must match reason_codes")
    if config is None:
        config = ResearchStrategyOutcomeLearningEdgeDecayConfig()
    else:
        config = _revalidated_config(config)
    expected_score = _outcome_learning_score(
        settled_outcome_feedback_score=row.settled_outcome_feedback_score,
        calibration_update_quality_score=row.calibration_update_quality_score,
        evidence_reuse_score=row.evidence_reuse_score,
        cost_relief_score=row.cost_relief_score,
        thesis_freshness_score=row.thesis_freshness_score,
        edge_retention_score=row.edge_retention_score,
        config=config,
    )
    if row.outcome_learning_score != expected_score:
        raise ValueError("outcome_learning_score must match component scores")
    expected_reasons = _row_reason_codes(
        upstream_reason_codes=tuple(
            reason_code
            for reason_code in row.reason_codes
            if reason_code in _UPSTREAM_REASON_CODE_SEQUENCE
        ),
        probability_edge_decay_ratio=row.probability_edge_decay_ratio,
        settled_outcome_feedback_score=row.settled_outcome_feedback_score,
        calibration_update_quality_score=row.calibration_update_quality_score,
        evidence_reuse_score=row.evidence_reuse_score,
        cost_pressure_score=row.cost_pressure_score,
        stale_thesis_pressure_score=row.stale_thesis_pressure_score,
        outcome_learning_score=row.outcome_learning_score,
        config=config,
    )
    if row.reason_codes != expected_reasons:
        raise ValueError("reason_codes must match outcome_learning thresholds")


def _validate_report(report: ResearchStrategyOutcomeLearningEdgeDecayReport) -> None:
    rows = report.rows
    for row in rows:
        _validate_row(row, report.config)
    if any(row.observed_at > report.generated_at for row in rows):
        raise ValueError("observed_at must not be after generated_at")
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
    if report.average_outcome_learning_score != _average_ratio(
        tuple(row.outcome_learning_score for row in rows),
    ):
        raise ValueError("average_outcome_learning_score must match rows")
    if report.min_outcome_learning_score != min(
        (row.outcome_learning_score for row in rows),
        default=_ZERO,
    ):
        raise ValueError("min_outcome_learning_score must match rows")
    if report.max_probability_edge_decay_ratio != max(
        (row.probability_edge_decay_ratio for row in rows),
        default=_ZERO,
    ):
        raise ValueError("max_probability_edge_decay_ratio must match rows")
    if report.min_settled_outcome_feedback_score != min(
        (row.settled_outcome_feedback_score for row in rows),
        default=_ZERO,
    ):
        raise ValueError("min_settled_outcome_feedback_score must match rows")
    if report.min_calibration_update_quality_score != min(
        (row.calibration_update_quality_score for row in rows),
        default=_ZERO,
    ):
        raise ValueError("min_calibration_update_quality_score must match rows")
    if report.min_evidence_reuse_score != min(
        (row.evidence_reuse_score for row in rows),
        default=_ZERO,
    ):
        raise ValueError("min_evidence_reuse_score must match rows")
    if report.max_cost_pressure_score != max(
        (row.cost_pressure_score for row in rows),
        default=_ZERO,
    ):
        raise ValueError("max_cost_pressure_score must match rows")
    if report.max_stale_thesis_pressure_score != max(
        (row.stale_thesis_pressure_score for row in rows),
        default=_ZERO,
    ):
        raise ValueError("max_stale_thesis_pressure_score must match rows")
    expected_counts = (
        _reason_code_counts(rows)
        if rows
        else (
            ResearchStrategyOutcomeLearningEdgeDecayReasonCodeCount(
                reason_code=REASON_EMPTY_INPUT,
                count=_ONE,
                input_ratio=_ONE,
            ),
        )
    )
    if report.reason_code_counts != expected_counts:
        raise ValueError("reason_code_counts must match rows")
    expected_reasons = tuple(item.reason_code for item in expected_counts)
    if report.reason_codes != expected_reasons:
        raise ValueError("reason_codes must match reason_code_counts")


def _normalize_inputs(
    value: object,
) -> tuple[ResearchStrategyOutcomeLearningEdgeDecayInput, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("inputs must be a list or tuple")
    inputs = tuple(value)
    return tuple(_revalidated_input(item) for item in inputs)


def _normalize_rows(
    value: object,
    validation_config: ResearchStrategyOutcomeLearningEdgeDecayConfig,
) -> tuple[ResearchStrategyOutcomeLearningEdgeDecayRow, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("rows must be a list or tuple")
    rows = tuple(_revalidated_row(row, validation_config) for row in value)
    seen: set[str] = set()
    for row in rows:
        if row.learning_ref_digest in seen:
            raise ValueError("rows must not repeat learning_ref_digest values")
        seen.add(row.learning_ref_digest)
    return rows


def _normalize_reason_code_counts(
    value: object,
) -> tuple[ResearchStrategyOutcomeLearningEdgeDecayReasonCodeCount, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("reason_code_counts must be a list or tuple")
    rows = tuple(_revalidated_reason_code_count(row) for row in value)
    seen: set[str] = set()
    for row in rows:
        if row.reason_code in seen:
            raise ValueError("reason_code_counts must not repeat reason_code values")
        seen.add(row.reason_code)
    return rows


def _revalidated_config(
    value: object,
) -> ResearchStrategyOutcomeLearningEdgeDecayConfig:
    if type(value) is not ResearchStrategyOutcomeLearningEdgeDecayConfig:
        raise ValueError(
            "config must be a ResearchStrategyOutcomeLearningEdgeDecayConfig",
        )
    return ResearchStrategyOutcomeLearningEdgeDecayConfig(
        **_dataclass_field_values("config", value, _PUBLIC_CONFIG_FIELDS),
    )


def _revalidated_input(
    value: object,
) -> ResearchStrategyOutcomeLearningEdgeDecayInput:
    if type(value) is not ResearchStrategyOutcomeLearningEdgeDecayInput:
        raise ValueError(
            "inputs must contain ResearchStrategyOutcomeLearningEdgeDecayInput values",
        )
    return ResearchStrategyOutcomeLearningEdgeDecayInput(
        **_dataclass_field_values("input", value, _INPUT_FIELDS),
    )


def _revalidated_row(
    value: object,
    validation_config: ResearchStrategyOutcomeLearningEdgeDecayConfig,
) -> ResearchStrategyOutcomeLearningEdgeDecayRow:
    if type(value) is not ResearchStrategyOutcomeLearningEdgeDecayRow:
        raise ValueError(
            "rows must contain ResearchStrategyOutcomeLearningEdgeDecayRow values",
        )
    return ResearchStrategyOutcomeLearningEdgeDecayRow(
        **_dataclass_field_values("row", value, _PUBLIC_ROW_FIELDS),
        validation_config=validation_config,
    )


def _revalidated_reason_code_count(
    value: object,
) -> ResearchStrategyOutcomeLearningEdgeDecayReasonCodeCount:
    if type(value) is not ResearchStrategyOutcomeLearningEdgeDecayReasonCodeCount:
        raise ValueError(
            "reason_code_counts must contain "
            "ResearchStrategyOutcomeLearningEdgeDecayReasonCodeCount values",
        )
    return ResearchStrategyOutcomeLearningEdgeDecayReasonCodeCount(
        **_dataclass_field_values(
            "reason count",
            value,
            _PUBLIC_REASON_CODE_COUNT_FIELDS,
        ),
    )


def _dataclass_field_values(
    label: str,
    value: object,
    expected_fields: tuple[str, ...],
) -> dict[str, object]:
    _require_expected_dataclass_state(label, value, expected_fields)
    values: dict[str, object] = {}
    for field_name in expected_fields:
        try:
            values[field_name] = getattr(value, field_name)
        except AttributeError as exc:
            raise ValueError(f"{label}.{field_name} is required") from exc
    return values


def _require_expected_dataclass_state(
    label: str,
    value: object,
    expected_fields: tuple[str, ...],
) -> None:
    actual_state = getattr(value, "__dict__", None)
    if type(actual_state) is not dict:
        return
    unexpected = sorted(set(actual_state) - set(expected_fields))
    if unexpected:
        raise ValueError(f"{label} has unexpected fields: {', '.join(unexpected)}")


def _edge_decay_ratio(pre_feedback_edge: Decimal, post_feedback_edge: Decimal) -> Decimal:
    if pre_feedback_edge == _ZERO:
        return _ZERO
    if post_feedback_edge >= pre_feedback_edge:
        return _ZERO
    with localcontext(_DECIMAL_CONTEXT):
        return _clamp_ratio(
            (pre_feedback_edge - post_feedback_edge) / pre_feedback_edge,
        )


def _learning_ref_digest(candidate_ref: str, surface_ref: str) -> str:
    payload = {"candidate_ref": candidate_ref, "surface_ref": surface_ref}
    return "sha256:" + _canonical_digest(payload)


def _report_payload(report: ResearchStrategyOutcomeLearningEdgeDecayReport) -> dict[str, object]:
    payload = _json_ready(asdict(report))
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    return payload


def _report_digest(report: ResearchStrategyOutcomeLearningEdgeDecayReport) -> str:
    payload = asdict(report)
    payload.pop(_DIGEST_FIELD, None)
    ready = _json_ready(payload)
    if type(ready) is not dict:
        raise ValueError("report payload must be a JSON object")
    return _canonical_digest(ready)


def _report_digest_from_values(values: dict[str, object]) -> str:
    ready = _json_ready(values)
    if type(ready) is not dict:
        raise ValueError("report values must build a JSON object")
    return _canonical_digest(ready)


def _validate_payload_digest(payload: dict[str, object]) -> None:
    digest = payload.get(_DIGEST_FIELD)
    _require_digest(_DIGEST_FIELD, digest)
    unsigned_payload = dict(payload)
    unsigned_payload.pop(_DIGEST_FIELD, None)
    expected_digest = _canonical_digest(unsigned_payload)
    if digest != expected_digest:
        raise ValueError("derived_validation_digest mismatch")


def _validate_public_payload_schema(
    payload: dict[str, object],
) -> None:
    _require_exact_public_fields("payload", payload, _PUBLIC_REPORT_FIELDS)
    validation_config = _config_from_public_payload(payload["config"])
    rows = tuple(
        _row_from_public_payload(
            item,
            index=index,
            validation_config=validation_config,
        )
        for index, item in enumerate(_require_public_list("rows", payload["rows"]))
    )
    reason_code_counts = tuple(
        _reason_code_count_from_public_payload(item, index=index)
        for index, item in enumerate(
            _require_public_list(
                "reason_code_counts",
                payload["reason_code_counts"],
            ),
        )
    )
    validated_report = ResearchStrategyOutcomeLearningEdgeDecayReport(
        generated_at=_require_public_datetime("generated_at", payload["generated_at"]),
        config_version=_require_public_string(
            "config_version",
            payload["config_version"],
        ),
        config=validation_config,
        status=_require_public_string("status", payload["status"]),
        input_count=_require_public_decimal("input_count", payload["input_count"]),
        pass_count=_require_public_decimal("pass_count", payload["pass_count"]),
        watch_count=_require_public_decimal("watch_count", payload["watch_count"]),
        block_count=_require_public_decimal("block_count", payload["block_count"]),
        average_outcome_learning_score=_require_public_decimal(
            "average_outcome_learning_score",
            payload["average_outcome_learning_score"],
        ),
        min_outcome_learning_score=_require_public_decimal(
            "min_outcome_learning_score",
            payload["min_outcome_learning_score"],
        ),
        max_probability_edge_decay_ratio=_require_public_decimal(
            "max_probability_edge_decay_ratio",
            payload["max_probability_edge_decay_ratio"],
        ),
        min_settled_outcome_feedback_score=_require_public_decimal(
            "min_settled_outcome_feedback_score",
            payload["min_settled_outcome_feedback_score"],
        ),
        min_calibration_update_quality_score=_require_public_decimal(
            "min_calibration_update_quality_score",
            payload["min_calibration_update_quality_score"],
        ),
        min_evidence_reuse_score=_require_public_decimal(
            "min_evidence_reuse_score",
            payload["min_evidence_reuse_score"],
        ),
        max_cost_pressure_score=_require_public_decimal(
            "max_cost_pressure_score",
            payload["max_cost_pressure_score"],
        ),
        max_stale_thesis_pressure_score=_require_public_decimal(
            "max_stale_thesis_pressure_score",
            payload["max_stale_thesis_pressure_score"],
        ),
        rows=rows,
        reason_code_counts=reason_code_counts,
        reason_codes=_require_public_string_tuple(
            "reason_codes",
            payload["reason_codes"],
        ),
        derived_validation_digest=_require_digest(
            _DIGEST_FIELD,
            payload[_DIGEST_FIELD],
        ),
        paper_only=_require_public_true("paper_only", payload["paper_only"]),
        report_only=_require_public_true("report_only", payload["report_only"]),
        readonly=_require_public_true("readonly", payload["readonly"]),
    )
    if payload != _report_payload(validated_report):
        raise ValueError("public payload must use canonical schema values")


def _config_from_public_payload(
    value: object,
) -> ResearchStrategyOutcomeLearningEdgeDecayConfig:
    label = "config"
    if type(value) is not dict:
        raise ValueError(f"{label} must be a JSON object")
    _require_exact_public_fields(label, value, _PUBLIC_CONFIG_FIELDS)
    return ResearchStrategyOutcomeLearningEdgeDecayConfig(
        config_version=_require_public_string(
            f"{label}.config_version",
            value["config_version"],
        ),
        pass_min_outcome_learning_score=_require_public_decimal(
            f"{label}.pass_min_outcome_learning_score",
            value["pass_min_outcome_learning_score"],
        ),
        watch_min_outcome_learning_score=_require_public_decimal(
            f"{label}.watch_min_outcome_learning_score",
            value["watch_min_outcome_learning_score"],
        ),
        max_pass_probability_edge_decay_ratio=_require_public_decimal(
            f"{label}.max_pass_probability_edge_decay_ratio",
            value["max_pass_probability_edge_decay_ratio"],
        ),
        max_watch_probability_edge_decay_ratio=_require_public_decimal(
            f"{label}.max_watch_probability_edge_decay_ratio",
            value["max_watch_probability_edge_decay_ratio"],
        ),
        min_pass_settled_outcome_feedback_score=_require_public_decimal(
            f"{label}.min_pass_settled_outcome_feedback_score",
            value["min_pass_settled_outcome_feedback_score"],
        ),
        min_watch_settled_outcome_feedback_score=_require_public_decimal(
            f"{label}.min_watch_settled_outcome_feedback_score",
            value["min_watch_settled_outcome_feedback_score"],
        ),
        min_pass_calibration_update_quality_score=_require_public_decimal(
            f"{label}.min_pass_calibration_update_quality_score",
            value["min_pass_calibration_update_quality_score"],
        ),
        min_watch_calibration_update_quality_score=_require_public_decimal(
            f"{label}.min_watch_calibration_update_quality_score",
            value["min_watch_calibration_update_quality_score"],
        ),
        min_pass_evidence_reuse_score=_require_public_decimal(
            f"{label}.min_pass_evidence_reuse_score",
            value["min_pass_evidence_reuse_score"],
        ),
        min_watch_evidence_reuse_score=_require_public_decimal(
            f"{label}.min_watch_evidence_reuse_score",
            value["min_watch_evidence_reuse_score"],
        ),
        max_pass_cost_pressure_score=_require_public_decimal(
            f"{label}.max_pass_cost_pressure_score",
            value["max_pass_cost_pressure_score"],
        ),
        max_watch_cost_pressure_score=_require_public_decimal(
            f"{label}.max_watch_cost_pressure_score",
            value["max_watch_cost_pressure_score"],
        ),
        max_pass_stale_thesis_pressure_score=_require_public_decimal(
            f"{label}.max_pass_stale_thesis_pressure_score",
            value["max_pass_stale_thesis_pressure_score"],
        ),
        max_watch_stale_thesis_pressure_score=_require_public_decimal(
            f"{label}.max_watch_stale_thesis_pressure_score",
            value["max_watch_stale_thesis_pressure_score"],
        ),
        settled_feedback_weight=_require_public_decimal(
            f"{label}.settled_feedback_weight",
            value["settled_feedback_weight"],
        ),
        calibration_update_weight=_require_public_decimal(
            f"{label}.calibration_update_weight",
            value["calibration_update_weight"],
        ),
        evidence_reuse_weight=_require_public_decimal(
            f"{label}.evidence_reuse_weight",
            value["evidence_reuse_weight"],
        ),
        cost_pressure_weight=_require_public_decimal(
            f"{label}.cost_pressure_weight",
            value["cost_pressure_weight"],
        ),
        stale_thesis_weight=_require_public_decimal(
            f"{label}.stale_thesis_weight",
            value["stale_thesis_weight"],
        ),
        edge_retention_weight=_require_public_decimal(
            f"{label}.edge_retention_weight",
            value["edge_retention_weight"],
        ),
        paper_only=_require_public_true(
            f"{label}.paper_only",
            value["paper_only"],
        ),
        report_only=_require_public_true(
            f"{label}.report_only",
            value["report_only"],
        ),
        readonly=_require_public_true(f"{label}.readonly", value["readonly"]),
    )


def _row_from_public_payload(
    value: object,
    *,
    index: int,
    validation_config: ResearchStrategyOutcomeLearningEdgeDecayConfig | None,
) -> ResearchStrategyOutcomeLearningEdgeDecayRow:
    label = f"rows[{index}]"
    if type(value) is not dict:
        raise ValueError(f"{label} must be a JSON object")
    _require_exact_public_fields(label, value, _PUBLIC_ROW_FIELDS)
    return ResearchStrategyOutcomeLearningEdgeDecayRow(
        learning_ref_digest=_require_private_digest(
            f"{label}.learning_ref_digest",
            value["learning_ref_digest"],
        ),
        observed_at=_require_public_datetime(
            f"{label}.observed_at",
            value["observed_at"],
        ),
        pre_feedback_probability_edge=_require_public_decimal(
            f"{label}.pre_feedback_probability_edge",
            value["pre_feedback_probability_edge"],
        ),
        post_feedback_probability_edge=_require_public_decimal(
            f"{label}.post_feedback_probability_edge",
            value["post_feedback_probability_edge"],
        ),
        probability_edge_decay_ratio=_require_public_decimal(
            f"{label}.probability_edge_decay_ratio",
            value["probability_edge_decay_ratio"],
        ),
        edge_retention_score=_require_public_decimal(
            f"{label}.edge_retention_score",
            value["edge_retention_score"],
        ),
        settled_outcome_feedback_score=_require_public_decimal(
            f"{label}.settled_outcome_feedback_score",
            value["settled_outcome_feedback_score"],
        ),
        calibration_update_quality_score=_require_public_decimal(
            f"{label}.calibration_update_quality_score",
            value["calibration_update_quality_score"],
        ),
        evidence_reuse_score=_require_public_decimal(
            f"{label}.evidence_reuse_score",
            value["evidence_reuse_score"],
        ),
        cost_pressure_score=_require_public_decimal(
            f"{label}.cost_pressure_score",
            value["cost_pressure_score"],
        ),
        cost_relief_score=_require_public_decimal(
            f"{label}.cost_relief_score",
            value["cost_relief_score"],
        ),
        stale_thesis_pressure_score=_require_public_decimal(
            f"{label}.stale_thesis_pressure_score",
            value["stale_thesis_pressure_score"],
        ),
        thesis_freshness_score=_require_public_decimal(
            f"{label}.thesis_freshness_score",
            value["thesis_freshness_score"],
        ),
        outcome_learning_score=_require_public_decimal(
            f"{label}.outcome_learning_score",
            value["outcome_learning_score"],
        ),
        status=_require_public_string(f"{label}.status", value["status"]),
        reason_codes=_require_public_string_tuple(
            f"{label}.reason_codes",
            value["reason_codes"],
        ),
        paper_only=_require_public_true(
            f"{label}.paper_only",
            value["paper_only"],
        ),
        report_only=_require_public_true(
            f"{label}.report_only",
            value["report_only"],
        ),
        readonly=_require_public_true(f"{label}.readonly", value["readonly"]),
        validation_config=validation_config,
    )


def _reason_code_count_from_public_payload(
    value: object,
    *,
    index: int,
) -> ResearchStrategyOutcomeLearningEdgeDecayReasonCodeCount:
    label = f"reason_code_counts[{index}]"
    if type(value) is not dict:
        raise ValueError(f"{label} must be a JSON object")
    _require_exact_public_fields(label, value, _PUBLIC_REASON_CODE_COUNT_FIELDS)
    return ResearchStrategyOutcomeLearningEdgeDecayReasonCodeCount(
        reason_code=_require_public_string(
            f"{label}.reason_code",
            value["reason_code"],
        ),
        count=_require_public_decimal(f"{label}.count", value["count"]),
        input_ratio=_require_public_decimal(
            f"{label}.input_ratio",
            value["input_ratio"],
        ),
        paper_only=_require_public_true(
            f"{label}.paper_only",
            value["paper_only"],
        ),
        report_only=_require_public_true(
            f"{label}.report_only",
            value["report_only"],
        ),
        readonly=_require_public_true(f"{label}.readonly", value["readonly"]),
    )


def _require_exact_public_fields(
    label: str,
    value: dict[str, object],
    expected_fields: tuple[str, ...],
) -> None:
    actual_fields = tuple(value)
    actual = set(actual_fields)
    expected = set(expected_fields)
    missing = sorted(expected - actual)
    if missing:
        raise ValueError(f"{label} has missing fields: {', '.join(missing)}")
    unexpected = sorted(actual - expected)
    if unexpected:
        raise ValueError(f"{label} has unexpected fields: {', '.join(unexpected)}")
    if actual_fields != expected_fields:
        raise ValueError(f"{label} fields must use canonical field order")


def _require_public_list(field_name: str, value: object) -> list[object]:
    if type(value) is not list:
        raise ValueError(f"{field_name} must be a list")
    return value


def _require_public_string(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    return value


def _require_public_string_tuple(field_name: str, value: object) -> tuple[str, ...]:
    items = _require_public_list(field_name, value)
    normalized: list[str] = []
    for index, item in enumerate(items):
        normalized.append(_require_public_string(f"{field_name}[{index}]", item))
    return tuple(normalized)


def _require_public_decimal(field_name: str, value: object) -> Decimal:
    text = _require_public_string(field_name, value)
    if _PUBLIC_DECIMAL_RE.fullmatch(text) is None:
        raise ValueError(f"{field_name} must be a canonical Decimal string")
    return Decimal(text)


def _require_public_datetime(field_name: str, value: object) -> datetime:
    text = _require_public_string(field_name, value)
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError as exc:
        raise ValueError(f"{field_name} must be an ISO datetime") from exc
    normalized = _as_utc(field_name, parsed)
    if normalized.isoformat() != text:
        raise ValueError(f"{field_name} must be a canonical UTC datetime")
    return normalized


def _require_public_true(field_name: str, value: object) -> bool:
    if value is not True:
        raise ValueError(f"{field_name} must be True")
    return True


def _validate_payload_flags(
    value: object,
    *,
    path: str = "payload",
    require_current: bool = True,
) -> None:
    if isinstance(value, dict):
        if require_current:
            for key in ("paper_only", "report_only", "readonly"):
                if value.get(key) is not True:
                    raise ValueError(f"{path}.{key} must be True")
        for key, item in value.items():
            if key in {"paper_only", "report_only", "readonly"} and item is not True:
                raise ValueError(f"{key} must be True")
            nested_path = key if path == "" else f"{path}.{key}"
            _validate_payload_flags(
                item,
                path=nested_path,
                require_current=isinstance(item, dict),
            )
        return
    if isinstance(value, list):
        for index, item in enumerate(value):
            _validate_payload_flags(
                item,
                path=f"{path}[{index}]",
                require_current=isinstance(item, dict),
            )


def _validate_payload_private_digests(
    value: object,
    *,
    path: str = "payload",
) -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            nested_path = key if path == "" else f"{path}.{key}"
            if key == "learning_ref_digest":
                _require_private_digest(nested_path, item)
            _validate_payload_private_digests(item, path=nested_path)
        return
    if isinstance(value, list):
        for index, item in enumerate(value):
            _validate_payload_private_digests(item, path=f"{path}[{index}]")


def _validate_payload_statuses(payload: dict[str, object]) -> None:
    status = payload.get("status")
    if type(status) is str:
        _require_status("status", status)
    rows = payload.get("rows")
    if isinstance(rows, list):
        for row in rows:
            if isinstance(row, dict) and type(row.get("status")) is str:
                _require_status("status", row["status"])


def _canonical_digest(payload: object) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    return sha256(encoded).hexdigest()


def _json_ready(value: Any) -> Any:
    if is_dataclass(value) and not isinstance(value, type):
        return _json_ready(asdict(value))
    if isinstance(value, Decimal):
        if type(value) is not Decimal:
            raise ValueError("JSON Decimal value must be exactly Decimal")
        if not value.is_finite():
            raise ValueError("JSON Decimal value must be finite")
        return str(value)
    if isinstance(value, datetime):
        if type(value) is not datetime:
            raise ValueError("JSON datetime value must be a datetime")
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("JSON datetime value must be timezone-aware")
        return value.astimezone(UTC).isoformat()
    if value is None:
        return None
    if type(value) is bool:
        return value
    if isinstance(value, float):
        raise ValueError("JSON value must not be a float")
    if type(value) is int:
        raise ValueError("JSON numeric value must use Decimal strings")
    if type(value) is str:
        return value
    if isinstance(value, tuple):
        return [_json_ready(item) for item in value]
    if isinstance(value, list):
        return [_json_ready(item) for item in value]
    if isinstance(value, dict):
        ready: dict[str, Any] = {}
        for key, nested_value in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            ready[key] = _json_ready(nested_value)
        return ready
    raise ValueError("value is not JSON serializable")


def _copy_json_object(value: dict[str, object]) -> dict[str, object]:
    copied = _copy_json_value(value)
    if type(copied) is not dict:
        raise ValueError("payload must be a JSON object")
    return copied


def _copy_json_value(value: object) -> object:
    if type(value) is dict:
        copied: dict[str, object] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            copied[key] = _copy_json_value(item)
        return copied
    if type(value) is list:
        return [_copy_json_value(item) for item in value]
    if value is None or type(value) in (str, bool):
        return value
    if isinstance(value, float):
        raise ValueError("JSON value must not be a float")
    if type(value) is int or isinstance(value, Decimal):
        raise ValueError("public payload numerics must be Decimal-derived strings")
    raise ValueError("value is not JSON serializable")


def _reject_unsafe_public_payload(
    label: str,
    value: object,
    *,
    allow_json_containers: bool = False,
    path: str = "",
) -> None:
    if is_dataclass(value) and not isinstance(value, type):
        _reject_unsafe_public_payload(label, asdict(value), path=path)
        return
    if type(value) is str:
        if _has_unsafe_public_fragment(value):
            raise ValueError(f"{path or label} has unsafe public value")
        return
    if isinstance(value, Decimal):
        if type(value) is not Decimal:
            raise ValueError(f"{path or label} must be exactly Decimal")
        if not value.is_finite():
            raise ValueError(f"{path or label} must be finite")
        return
    if isinstance(value, datetime):
        if type(value) is not datetime:
            raise ValueError(f"{path or label} must be a datetime")
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError(f"{path or label} must be timezone-aware")
        return
    if value is None or type(value) is bool:
        return
    if allow_json_containers and type(value) is int:
        raise ValueError("public payload numerics must be Decimal-derived strings")
    if isinstance(value, float):
        raise ValueError("JSON value must not be a float")
    if isinstance(value, dict):
        for key, nested_value in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            nested_path = key if not path else f"{path}.{key}"
            if _has_unsafe_public_fragment(key):
                raise ValueError(f"unsafe public surface field in {label}: {key}")
            if key in {"paper_only", "report_only", "readonly"} and nested_value is not True:
                raise ValueError(f"{nested_path} must be True")
            _reject_unsafe_public_payload(
                label,
                nested_value,
                allow_json_containers=allow_json_containers,
                path=nested_path,
            )
        return
    if isinstance(value, (list, tuple)):
        for index, nested_value in enumerate(value):
            nested_path = f"{path}[{index}]" if path else f"{label}[{index}]"
            _reject_unsafe_public_payload(
                label,
                nested_value,
                allow_json_containers=allow_json_containers,
                path=nested_path,
            )
        return
    raise ValueError("value is not JSON serializable")


def _has_unsafe_public_fragment(value: str) -> bool:
    normalized = value.casefold()
    return any(fragment in normalized for fragment in _UNSAFE_PUBLIC_FRAGMENTS)


def _average_ratio(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return _ZERO
    with localcontext(_DECIMAL_CONTEXT):
        return _quantize(
            sum(values, _ZERO) / Decimal(len(values)),
            field_name="average ratio",
        )


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == _ZERO:
        return _ZERO
    with localcontext(_DECIMAL_CONTEXT):
        return _clamp_ratio(numerator / denominator)


def _inverse_ratio(value: Decimal) -> Decimal:
    with localcontext(_DECIMAL_CONTEXT):
        return _clamp_ratio(_ONE - value)


def _clamp_ratio(value: Decimal) -> Decimal:
    decimal_value = _require_decimal("ratio", value)
    if decimal_value < _ZERO:
        return _ZERO
    if decimal_value > _ONE:
        return _ONE
    return _quantize(decimal_value, field_name="ratio")


def _decimal_count(value: int) -> Decimal:
    return _quantize(Decimal(value), field_name="count")


def _quantize(value: Decimal, *, field_name: str = "value") -> Decimal:
    try:
        with localcontext(_DECIMAL_CONTEXT):
            normalized = value.quantize(_QUANT)
    except InvalidOperation as exc:
        raise ValueError(f"{field_name} must fit the decimal context") from exc
    if normalized.is_zero() and normalized.is_signed():
        raise ValueError(f"{field_name} must not quantize to signed zero")
    return normalized


def _require_exact_type(value: object, expected_type: type[object], label: str) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{label} must be exactly {expected_type.__name__}")


def _require_private_ref(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")
    return value


def _require_public_identifier(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if _has_unsafe_public_fragment(value):
        raise ValueError(f"{field_name} has unsafe public value")
    if _PUBLIC_IDENTIFIER_RE.fullmatch(value) is None:
        raise ValueError(f"{field_name} must be a public identifier")
    return value


def _require_private_digest(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if _PRIVATE_DIGEST_RE.fullmatch(value) is None:
        raise ValueError(f"{field_name} must be a sha256 digest reference")
    return value


def _require_digest(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if _DIGEST_RE.fullmatch(value) is None:
        raise ValueError(f"{field_name} must be a lowercase sha256 hex digest")
    return value


def _require_ratio_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value < _ZERO or decimal_value > _ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return _quantize(decimal_value, field_name=field_name)


def _require_nonnegative_count_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value < _ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    with localcontext(_DECIMAL_CONTEXT):
        if decimal_value != decimal_value.to_integral_value():
            raise ValueError(f"{field_name} must be an integer Decimal")
    return _quantize(decimal_value, field_name=field_name)


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    if value.is_zero() and value.is_signed():
        raise ValueError(f"{field_name} must not use negative zero")
    return value


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_member(field_name: str, value: object, allowed: tuple[str, ...]) -> None:
    if type(value) is not str or value not in allowed:
        raise ValueError(f"{field_name} must be one of {', '.join(allowed)}")


def _require_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in _STATUS_VALUES:
        raise ValueError(f"{field_name} must be pass, watch, or block")


def _require_reason_code(
    field_name: str,
    value: object,
    allowed_values: tuple[str, ...],
) -> None:
    _require_member(field_name, value, allowed_values)


def _normalize_reason_codes(
    field_name: str,
    value: object,
    allowed_values: tuple[str, ...],
) -> tuple[str, ...]:
    if type(value) not in (list, tuple):
        raise ValueError(f"{field_name} must be a list or tuple")
    seen: set[str] = set()
    for item in value:
        _require_reason_code(field_name, item, allowed_values)
        if item in seen:
            raise ValueError(f"{field_name} must not contain duplicates")
        seen.add(item)
    return tuple(reason_code for reason_code in allowed_values if reason_code in seen)


def _require_floor_pair(
    pass_field_name: str,
    pass_value: Decimal,
    watch_field_name: str,
    watch_value: Decimal,
) -> None:
    if pass_value < watch_value:
        raise ValueError(f"{pass_field_name} must not be below {watch_field_name}")


def _require_ceiling_pair(
    pass_field_name: str,
    pass_value: Decimal,
    watch_field_name: str,
    watch_value: Decimal,
) -> None:
    if pass_value > watch_value:
        raise ValueError(f"{pass_field_name} must not exceed {watch_field_name}")


def _require_hard_flags(label: str, value: object) -> None:
    if getattr(value, "paper_only", None) is not True:
        raise ValueError(f"paper_only must be True for {label}")
    if getattr(value, "report_only", None) is not True:
        raise ValueError(f"report_only must be True for {label}")
    if getattr(value, "readonly", None) is not True:
        raise ValueError(f"readonly must be True for {label}")


__all__ = (
    "DEFAULT_RESEARCH_STRATEGY_OUTCOME_LEARNING_EDGE_DECAY_REPORT_CONFIG_VERSION",
    "RESEARCH_STRATEGY_OUTCOME_LEARNING_EDGE_DECAY_STATUSES",
    "ResearchStrategyOutcomeLearningEdgeDecayConfig",
    "ResearchStrategyOutcomeLearningEdgeDecayInput",
    "ResearchStrategyOutcomeLearningEdgeDecayReasonCodeCount",
    "ResearchStrategyOutcomeLearningEdgeDecayReport",
    "ResearchStrategyOutcomeLearningEdgeDecayRow",
    "build_research_strategy_outcome_learning_edge_decay_report",
    "research_strategy_outcome_learning_edge_decay_report_payload",
)
