"""Report-only analyst queue readiness scorecard.

The scorecard combines evidence completeness, cost-adjusted edge quality,
market microstructure signal quality, and resolution ambiguity into a
deterministic public report. It exposes no live execution, recommendation,
wallet, order, database, network, or persistence surface.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import InitVar, dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal, ROUND_HALF_UP
from hashlib import sha256
import json
import re
from typing import Any, Mapping, Sequence


DEFAULT_RESEARCH_STRATEGY_EVIDENCE_COST_RESOLUTION_SCORECARD_CONFIG_VERSION = (
    "research-strategy-evidence-cost-resolution-scorecard-report-v0"
)

STATUS_PASS = "pass"
STATUS_WATCH = "watch"
STATUS_BLOCK = "block"

REASON_EMPTY_INPUT = "empty_input"
REASON_ANALYST_INPUTS_READY = "analyst_inputs_ready"
REASON_MANUAL_REVIEW_REQUESTED = "manual_review_requested"
REASON_MISSING_RESOLUTION_DETAIL = "missing_resolution_detail"
REASON_EVIDENCE_COMPLETENESS_BLOCK = "evidence_completeness_block"
REASON_COST_ADJUSTED_EDGE_BLOCK = "cost_adjusted_edge_block"
REASON_MICROSTRUCTURE_SIGNAL_BLOCK = "microstructure_signal_block"
REASON_RESOLUTION_AMBIGUITY_BLOCK = "resolution_ambiguity_block"
REASON_READINESS_SCORE_BLOCK = "readiness_score_block"
REASON_EVIDENCE_COMPLETENESS_WATCH = "evidence_completeness_watch"
REASON_COST_ADJUSTED_EDGE_WATCH = "cost_adjusted_edge_watch"
REASON_MICROSTRUCTURE_SIGNAL_WATCH = "microstructure_signal_watch"
REASON_RESOLUTION_AMBIGUITY_WATCH = "resolution_ambiguity_watch"
REASON_READINESS_SCORE_WATCH = "readiness_score_watch"
REASON_ANALYST_QUEUE_READY_PASS = "analyst_queue_ready_pass"

_UPSTREAM_REASON_CODE_SEQUENCE = (
    REASON_ANALYST_INPUTS_READY,
    REASON_MANUAL_REVIEW_REQUESTED,
    REASON_MISSING_RESOLUTION_DETAIL,
)
_GENERATED_ROW_REASON_CODE_SEQUENCE = (
    REASON_EVIDENCE_COMPLETENESS_BLOCK,
    REASON_COST_ADJUSTED_EDGE_BLOCK,
    REASON_MICROSTRUCTURE_SIGNAL_BLOCK,
    REASON_RESOLUTION_AMBIGUITY_BLOCK,
    REASON_READINESS_SCORE_BLOCK,
    REASON_EVIDENCE_COMPLETENESS_WATCH,
    REASON_COST_ADJUSTED_EDGE_WATCH,
    REASON_MICROSTRUCTURE_SIGNAL_WATCH,
    REASON_RESOLUTION_AMBIGUITY_WATCH,
    REASON_READINESS_SCORE_WATCH,
    REASON_ANALYST_QUEUE_READY_PASS,
)
_ROW_REASON_CODE_SEQUENCE = (
    *_UPSTREAM_REASON_CODE_SEQUENCE,
    *_GENERATED_ROW_REASON_CODE_SEQUENCE,
)
_REASON_CODE_SEQUENCE = (REASON_EMPTY_INPUT, *_ROW_REASON_CODE_SEQUENCE)
_BLOCK_REASON_CODES = frozenset(
    (
        REASON_EVIDENCE_COMPLETENESS_BLOCK,
        REASON_COST_ADJUSTED_EDGE_BLOCK,
        REASON_MICROSTRUCTURE_SIGNAL_BLOCK,
        REASON_RESOLUTION_AMBIGUITY_BLOCK,
        REASON_READINESS_SCORE_BLOCK,
    ),
)

_QUANT = Decimal("0.000001")
_ZERO = Decimal("0.000000")
_ONE = Decimal("1.000000")
_DIGEST_FIELD = "derived_validation_digest"
_STATUS_VALUES = frozenset((STATUS_PASS, STATUS_WATCH, STATUS_BLOCK))
_PHASE_FLAG_FIELDS = frozenset(("paper_only", "report_only", "readonly"))
_PUBLIC_IDENTIFIER_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,127}$")
_DIGEST_RE = re.compile(r"^[0-9a-f]{64}$")
_PRIVATE_DIGEST_RE = re.compile(r"^sha256:[0-9a-f]{64}$")
_DECIMAL_PAYLOAD_RE = re.compile(r"^(?:0|[1-9][0-9]*)\.[0-9]{6}$")
_REPORT_PAYLOAD_FIELDS = frozenset(
    (
        "generated_at",
        "config_version",
        "status",
        "row_count",
        "pass_count",
        "watch_count",
        "block_count",
        "average_readiness_score",
        "min_readiness_score",
        "min_evidence_completeness_score",
        "min_cost_adjusted_edge_score",
        "min_microstructure_signal_score",
        "max_resolution_ambiguity_score",
        "rows",
        "reason_code_counts",
        "reason_codes",
        "public_notes",
        "derived_validation_digest",
        "paper_only",
        "report_only",
        "readonly",
    ),
)
_ROW_PAYLOAD_FIELDS = frozenset(
    (
        "queue_item_digest",
        "evidence_completeness_score",
        "evidence_gap_score",
        "cost_adjusted_edge_score",
        "cost_adjusted_edge_gap_score",
        "microstructure_signal_score",
        "microstructure_gap_score",
        "resolution_ambiguity_score",
        "resolution_certainty_score",
        "readiness_score",
        "observed_at",
        "status",
        "reason_codes",
        "paper_only",
        "report_only",
        "readonly",
    ),
)
_REASON_COUNT_PAYLOAD_FIELDS = frozenset(
    (
        "reason_code",
        "count",
        "row_ratio",
        "paper_only",
        "report_only",
        "readonly",
    ),
)
_PUBLIC_NOTE_PAYLOAD_FIELDS = frozenset(
    (
        "key",
        "value",
        "paper_only",
        "report_only",
        "readonly",
    ),
)
_UNSAFE_PUBLIC_FRAGMENTS = (
    "candidate",
    "market",
    "slug",
    "question",
    "source",
    "source_url",
    "source-url",
    "source url",
    "source_text",
    "source-text",
    "source text",
    "dsn",
    "database",
    "table",
    "token",
    "wallet",
    "auth",
    "order",
    "trade",
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
class ResearchStrategyEvidenceCostResolutionScorecardConfig(_FinalPublicDataclass):
    config_version: str = (
        DEFAULT_RESEARCH_STRATEGY_EVIDENCE_COST_RESOLUTION_SCORECARD_CONFIG_VERSION
    )
    pass_min_readiness_score: Decimal = Decimal("0.800000")
    watch_min_readiness_score: Decimal = Decimal("0.600000")
    min_pass_evidence_completeness_score: Decimal = Decimal("0.800000")
    min_watch_evidence_completeness_score: Decimal = Decimal("0.600000")
    min_pass_cost_adjusted_edge_score: Decimal = Decimal("0.750000")
    min_watch_cost_adjusted_edge_score: Decimal = Decimal("0.550000")
    min_pass_microstructure_signal_score: Decimal = Decimal("0.750000")
    min_watch_microstructure_signal_score: Decimal = Decimal("0.550000")
    max_pass_resolution_ambiguity_score: Decimal = Decimal("0.200000")
    max_watch_resolution_ambiguity_score: Decimal = Decimal("0.450000")
    evidence_weight: Decimal = Decimal("0.300000")
    cost_adjusted_edge_weight: Decimal = Decimal("0.300000")
    microstructure_signal_weight: Decimal = Decimal("0.200000")
    resolution_certainty_weight: Decimal = Decimal("0.200000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchStrategyEvidenceCostResolutionScorecardConfig,
            "config",
        )
        object.__setattr__(
            self,
            "config_version",
            _require_public_identifier("config_version", self.config_version),
        )
        if (
            self.config_version
            != DEFAULT_RESEARCH_STRATEGY_EVIDENCE_COST_RESOLUTION_SCORECARD_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "pass_min_readiness_score",
            "watch_min_readiness_score",
            "min_pass_evidence_completeness_score",
            "min_watch_evidence_completeness_score",
            "min_pass_cost_adjusted_edge_score",
            "min_watch_cost_adjusted_edge_score",
            "min_pass_microstructure_signal_score",
            "min_watch_microstructure_signal_score",
            "max_pass_resolution_ambiguity_score",
            "max_watch_resolution_ambiguity_score",
            "evidence_weight",
            "cost_adjusted_edge_weight",
            "microstructure_signal_weight",
            "resolution_certainty_weight",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        if self.pass_min_readiness_score < self.watch_min_readiness_score:
            raise ValueError(
                "pass_min_readiness_score must be at least watch_min_readiness_score",
            )
        if (
            self.min_pass_evidence_completeness_score
            < self.min_watch_evidence_completeness_score
        ):
            raise ValueError(
                "min_pass_evidence_completeness_score must be at least "
                "min_watch_evidence_completeness_score",
            )
        if (
            self.min_pass_cost_adjusted_edge_score
            < self.min_watch_cost_adjusted_edge_score
        ):
            raise ValueError(
                "min_pass_cost_adjusted_edge_score must be at least "
                "min_watch_cost_adjusted_edge_score",
            )
        if (
            self.min_pass_microstructure_signal_score
            < self.min_watch_microstructure_signal_score
        ):
            raise ValueError(
                "min_pass_microstructure_signal_score must be at least "
                "min_watch_microstructure_signal_score",
            )
        if (
            self.max_pass_resolution_ambiguity_score
            > self.max_watch_resolution_ambiguity_score
        ):
            raise ValueError(
                "max_pass_resolution_ambiguity_score must not exceed "
                "max_watch_resolution_ambiguity_score",
            )
        weight_sum = _quantize(
            self.evidence_weight
            + self.cost_adjusted_edge_weight
            + self.microstructure_signal_weight
            + self.resolution_certainty_weight,
        )
        if weight_sum != _ONE:
            raise ValueError("scorecard weights must sum to one")
        _require_hard_flags("config", self)
        _reject_unsafe_public_payload("config", self)


@dataclass(frozen=True)
class ResearchStrategyEvidenceCostResolutionInput(_FinalPublicDataclass):
    queue_item_ref: str
    evidence_completeness_score: Decimal
    cost_adjusted_edge_score: Decimal
    microstructure_signal_score: Decimal
    resolution_ambiguity_score: Decimal
    observed_at: datetime
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchStrategyEvidenceCostResolutionInput, "input")
        object.__setattr__(
            self,
            "queue_item_ref",
            _require_private_ref("queue_item_ref", self.queue_item_ref),
        )
        for field_name in (
            "evidence_completeness_score",
            "cost_adjusted_edge_score",
            "microstructure_signal_score",
            "resolution_ambiguity_score",
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
            _normalize_upstream_reason_codes(self.reason_codes),
        )
        _require_hard_flags("input", self)


@dataclass(frozen=True)
class ResearchStrategyEvidenceCostResolutionPublicNote(_FinalPublicDataclass):
    key: str
    value: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchStrategyEvidenceCostResolutionPublicNote, "note")
        object.__setattr__(self, "key", _require_public_identifier("key", self.key))
        object.__setattr__(self, "value", _require_public_text("value", self.value))
        _require_hard_flags("public note", self)
        _reject_unsafe_public_payload("public note", self)


@dataclass(frozen=True)
class ResearchStrategyEvidenceCostResolutionScorecardRow(_FinalPublicDataclass):
    queue_item_digest: str
    evidence_completeness_score: Decimal
    evidence_gap_score: Decimal
    cost_adjusted_edge_score: Decimal
    cost_adjusted_edge_gap_score: Decimal
    microstructure_signal_score: Decimal
    microstructure_gap_score: Decimal
    resolution_ambiguity_score: Decimal
    resolution_certainty_score: Decimal
    readiness_score: Decimal
    observed_at: datetime
    status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True
    validation_config: InitVar[
        ResearchStrategyEvidenceCostResolutionScorecardConfig | None
    ] = None

    def __post_init__(
        self,
        validation_config: (
            ResearchStrategyEvidenceCostResolutionScorecardConfig | None
        ),
    ) -> None:
        _require_exact_type(
            self,
            ResearchStrategyEvidenceCostResolutionScorecardRow,
            "row",
        )
        object.__setattr__(
            self,
            "queue_item_digest",
            _require_private_digest("queue_item_digest", self.queue_item_digest),
        )
        for field_name in (
            "evidence_completeness_score",
            "evidence_gap_score",
            "cost_adjusted_edge_score",
            "cost_adjusted_edge_gap_score",
            "microstructure_signal_score",
            "microstructure_gap_score",
            "resolution_ambiguity_score",
            "resolution_certainty_score",
            "readiness_score",
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
class ResearchStrategyEvidenceCostResolutionReasonCodeCount(_FinalPublicDataclass):
    reason_code: str
    count: Decimal
    row_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchStrategyEvidenceCostResolutionReasonCodeCount,
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
class ResearchStrategyEvidenceCostResolutionScorecardReport(_FinalPublicDataclass):
    generated_at: datetime
    config_version: str
    status: str
    row_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    average_readiness_score: Decimal
    min_readiness_score: Decimal
    min_evidence_completeness_score: Decimal
    min_cost_adjusted_edge_score: Decimal
    min_microstructure_signal_score: Decimal
    max_resolution_ambiguity_score: Decimal
    rows: tuple[ResearchStrategyEvidenceCostResolutionScorecardRow, ...]
    reason_code_counts: tuple[
        ResearchStrategyEvidenceCostResolutionReasonCodeCount,
        ...,
    ]
    reason_codes: tuple[str, ...]
    public_notes: tuple[ResearchStrategyEvidenceCostResolutionPublicNote, ...] = ()
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchStrategyEvidenceCostResolutionScorecardReport,
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
            != DEFAULT_RESEARCH_STRATEGY_EVIDENCE_COST_RESOLUTION_SCORECARD_CONFIG_VERSION
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
            "average_readiness_score",
            "min_readiness_score",
            "min_evidence_completeness_score",
            "min_cost_adjusted_edge_score",
            "min_microstructure_signal_score",
            "max_resolution_ambiguity_score",
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
        object.__setattr__(self, "public_notes", _normalize_public_notes(self.public_notes))
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
        return research_strategy_evidence_cost_resolution_scorecard_report_payload(self)


def build_research_strategy_evidence_cost_resolution_scorecard_report(
    inputs: Sequence[ResearchStrategyEvidenceCostResolutionInput],
    *,
    generated_at: datetime,
    config: ResearchStrategyEvidenceCostResolutionScorecardConfig | None = None,
    public_notes: Sequence[ResearchStrategyEvidenceCostResolutionPublicNote] = (),
) -> ResearchStrategyEvidenceCostResolutionScorecardReport:
    """Build a deterministic, readonly analyst queue readiness scorecard."""

    cfg = config or ResearchStrategyEvidenceCostResolutionScorecardConfig()
    if type(cfg) is not ResearchStrategyEvidenceCostResolutionScorecardConfig:
        raise ValueError(
            "config must be a ResearchStrategyEvidenceCostResolutionScorecardConfig",
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
            ResearchStrategyEvidenceCostResolutionReasonCodeCount(
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
        "average_readiness_score": _average_ratio(
            tuple(row.readiness_score for row in rows),
        ),
        "min_readiness_score": min(
            (row.readiness_score for row in rows),
            default=_ZERO,
        ),
        "min_evidence_completeness_score": min(
            (row.evidence_completeness_score for row in rows),
            default=_ZERO,
        ),
        "min_cost_adjusted_edge_score": min(
            (row.cost_adjusted_edge_score for row in rows),
            default=_ZERO,
        ),
        "min_microstructure_signal_score": min(
            (row.microstructure_signal_score for row in rows),
            default=_ZERO,
        ),
        "max_resolution_ambiguity_score": max(
            (row.resolution_ambiguity_score for row in rows),
            default=_ZERO,
        ),
        "rows": rows,
        "reason_code_counts": reason_code_counts,
        "reason_codes": reason_codes,
        "public_notes": _normalize_public_notes(public_notes),
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    return ResearchStrategyEvidenceCostResolutionScorecardReport(
        **values,
        derived_validation_digest=_report_digest_from_values(values),
    )


def research_strategy_evidence_cost_resolution_scorecard_report_payload(
    value: ResearchStrategyEvidenceCostResolutionScorecardReport | dict[str, object],
) -> dict[str, object]:
    if type(value) is ResearchStrategyEvidenceCostResolutionScorecardReport:
        _require_hard_flags("report", value)
        payload = _report_payload(value)
    elif type(value) is dict:
        payload = _copy_json_object(value)
    else:
        raise ValueError(
            "value must be a "
            "ResearchStrategyEvidenceCostResolutionScorecardReport or dict",
        )
    _validate_payload_statuses(payload)
    _reject_unsafe_public_payload("payload", payload, allow_json_containers=True)
    _validate_payload_digest(payload)
    _validate_payload_schema(payload)
    return payload


def _row_for_input(
    row: ResearchStrategyEvidenceCostResolutionInput,
    config: ResearchStrategyEvidenceCostResolutionScorecardConfig,
) -> ResearchStrategyEvidenceCostResolutionScorecardRow:
    evidence_gap = _inverse_ratio(row.evidence_completeness_score)
    cost_gap = _inverse_ratio(row.cost_adjusted_edge_score)
    microstructure_gap = _inverse_ratio(row.microstructure_signal_score)
    resolution_certainty = _inverse_ratio(row.resolution_ambiguity_score)
    readiness_score = _readiness_score(
        evidence_completeness_score=row.evidence_completeness_score,
        cost_adjusted_edge_score=row.cost_adjusted_edge_score,
        microstructure_signal_score=row.microstructure_signal_score,
        resolution_certainty_score=resolution_certainty,
        config=config,
    )
    reason_codes = _row_reason_codes(
        upstream_reason_codes=row.reason_codes,
        evidence_completeness_score=row.evidence_completeness_score,
        cost_adjusted_edge_score=row.cost_adjusted_edge_score,
        microstructure_signal_score=row.microstructure_signal_score,
        resolution_ambiguity_score=row.resolution_ambiguity_score,
        readiness_score=readiness_score,
        config=config,
    )
    return ResearchStrategyEvidenceCostResolutionScorecardRow(
        queue_item_digest=_private_ref_digest(row.queue_item_ref),
        evidence_completeness_score=row.evidence_completeness_score,
        evidence_gap_score=evidence_gap,
        cost_adjusted_edge_score=row.cost_adjusted_edge_score,
        cost_adjusted_edge_gap_score=cost_gap,
        microstructure_signal_score=row.microstructure_signal_score,
        microstructure_gap_score=microstructure_gap,
        resolution_ambiguity_score=row.resolution_ambiguity_score,
        resolution_certainty_score=resolution_certainty,
        readiness_score=readiness_score,
        observed_at=row.observed_at,
        status=_row_status(reason_codes),
        reason_codes=reason_codes,
        validation_config=config,
    )


def _row_reason_codes(
    *,
    upstream_reason_codes: tuple[str, ...],
    evidence_completeness_score: Decimal,
    cost_adjusted_edge_score: Decimal,
    microstructure_signal_score: Decimal,
    resolution_ambiguity_score: Decimal,
    readiness_score: Decimal,
    config: ResearchStrategyEvidenceCostResolutionScorecardConfig,
) -> tuple[str, ...]:
    reason_codes = list(upstream_reason_codes)
    if evidence_completeness_score < config.min_watch_evidence_completeness_score:
        reason_codes.append(REASON_EVIDENCE_COMPLETENESS_BLOCK)
    elif evidence_completeness_score < config.min_pass_evidence_completeness_score:
        reason_codes.append(REASON_EVIDENCE_COMPLETENESS_WATCH)
    if cost_adjusted_edge_score < config.min_watch_cost_adjusted_edge_score:
        reason_codes.append(REASON_COST_ADJUSTED_EDGE_BLOCK)
    elif cost_adjusted_edge_score < config.min_pass_cost_adjusted_edge_score:
        reason_codes.append(REASON_COST_ADJUSTED_EDGE_WATCH)
    if microstructure_signal_score < config.min_watch_microstructure_signal_score:
        reason_codes.append(REASON_MICROSTRUCTURE_SIGNAL_BLOCK)
    elif microstructure_signal_score < config.min_pass_microstructure_signal_score:
        reason_codes.append(REASON_MICROSTRUCTURE_SIGNAL_WATCH)
    if resolution_ambiguity_score > config.max_watch_resolution_ambiguity_score:
        reason_codes.append(REASON_RESOLUTION_AMBIGUITY_BLOCK)
    elif resolution_ambiguity_score > config.max_pass_resolution_ambiguity_score:
        reason_codes.append(REASON_RESOLUTION_AMBIGUITY_WATCH)
    if readiness_score < config.watch_min_readiness_score:
        reason_codes.append(REASON_READINESS_SCORE_BLOCK)
    elif readiness_score < config.pass_min_readiness_score:
        reason_codes.append(REASON_READINESS_SCORE_WATCH)
    generated = tuple(
        reason_code
        for reason_code in reason_codes
        if reason_code in _GENERATED_ROW_REASON_CODE_SEQUENCE
    )
    if not generated:
        reason_codes.append(REASON_ANALYST_QUEUE_READY_PASS)
    return _normalize_row_reason_codes(tuple(reason_codes))


def _row_status(reason_codes: tuple[str, ...]) -> str:
    if any(reason_code in _BLOCK_REASON_CODES for reason_code in reason_codes):
        return STATUS_BLOCK
    if REASON_ANALYST_QUEUE_READY_PASS in reason_codes:
        return STATUS_PASS
    return STATUS_WATCH


def _report_status(
    rows: tuple[ResearchStrategyEvidenceCostResolutionScorecardRow, ...],
) -> str:
    if not rows:
        return STATUS_BLOCK
    if any(row.status == STATUS_BLOCK for row in rows):
        return STATUS_BLOCK
    if any(row.status == STATUS_WATCH for row in rows):
        return STATUS_WATCH
    return STATUS_PASS


def _status_count(
    rows: tuple[ResearchStrategyEvidenceCostResolutionScorecardRow, ...],
    status: str,
) -> int:
    return sum(1 for row in rows if row.status == status)


def _row_sort_key(
    row: ResearchStrategyEvidenceCostResolutionScorecardRow,
) -> tuple[int, Decimal, str]:
    return (_status_rank(row.status), row.readiness_score, row.queue_item_digest)


def _status_rank(value: str) -> int:
    return {STATUS_BLOCK: 0, STATUS_WATCH: 1, STATUS_PASS: 2}[value]


def _reason_code_counts(
    rows: tuple[ResearchStrategyEvidenceCostResolutionScorecardRow, ...],
) -> tuple[ResearchStrategyEvidenceCostResolutionReasonCodeCount, ...]:
    total = _decimal_count(len(rows))
    counts: Counter[str] = Counter(
        reason_code for row in rows for reason_code in row.reason_codes
    )
    return tuple(
        ResearchStrategyEvidenceCostResolutionReasonCodeCount(
            reason_code=reason_code,
            count=_decimal_count(count),
            row_ratio=_ratio(_decimal_count(count), total),
        )
        for reason_code, count in sorted(counts.items(), key=lambda item: (-item[1], item[0]))
    )


def _readiness_score(
    *,
    evidence_completeness_score: Decimal,
    cost_adjusted_edge_score: Decimal,
    microstructure_signal_score: Decimal,
    resolution_certainty_score: Decimal,
    config: ResearchStrategyEvidenceCostResolutionScorecardConfig,
) -> Decimal:
    score = (
        evidence_completeness_score * config.evidence_weight
        + cost_adjusted_edge_score * config.cost_adjusted_edge_weight
        + microstructure_signal_score * config.microstructure_signal_weight
        + resolution_certainty_score * config.resolution_certainty_weight
    )
    return _clamp_ratio(score)


def _validate_row(
    row: ResearchStrategyEvidenceCostResolutionScorecardRow,
    config: ResearchStrategyEvidenceCostResolutionScorecardConfig | None,
) -> None:
    if row.evidence_gap_score != _inverse_ratio(row.evidence_completeness_score):
        raise ValueError(
            "evidence_gap_score must match evidence_completeness_score",
        )
    if row.cost_adjusted_edge_gap_score != _inverse_ratio(
        row.cost_adjusted_edge_score,
    ):
        raise ValueError(
            "cost_adjusted_edge_gap_score must match cost_adjusted_edge_score",
        )
    if row.microstructure_gap_score != _inverse_ratio(
        row.microstructure_signal_score,
    ):
        raise ValueError(
            "microstructure_gap_score must match microstructure_signal_score",
        )
    if row.resolution_certainty_score != _inverse_ratio(
        row.resolution_ambiguity_score,
    ):
        raise ValueError(
            "resolution_certainty_score must match resolution_ambiguity_score",
        )
    if config is not None:
        if type(config) is not ResearchStrategyEvidenceCostResolutionScorecardConfig:
            raise ValueError(
                "validation_config must be a "
                "ResearchStrategyEvidenceCostResolutionScorecardConfig",
            )
        expected_readiness = _readiness_score(
            evidence_completeness_score=row.evidence_completeness_score,
            cost_adjusted_edge_score=row.cost_adjusted_edge_score,
            microstructure_signal_score=row.microstructure_signal_score,
            resolution_certainty_score=row.resolution_certainty_score,
            config=config,
        )
        if row.readiness_score != expected_readiness:
            raise ValueError("readiness_score must match component scores")
        upstream_reason_codes = tuple(
            reason_code
            for reason_code in row.reason_codes
            if reason_code in _UPSTREAM_REASON_CODE_SEQUENCE
        )
        expected_reasons = _row_reason_codes(
            upstream_reason_codes=upstream_reason_codes,
            evidence_completeness_score=row.evidence_completeness_score,
            cost_adjusted_edge_score=row.cost_adjusted_edge_score,
            microstructure_signal_score=row.microstructure_signal_score,
            resolution_ambiguity_score=row.resolution_ambiguity_score,
            readiness_score=row.readiness_score,
            config=config,
        )
        if row.reason_codes != expected_reasons:
            raise ValueError("reason_codes must match row inputs")
    if row.status != _row_status(row.reason_codes):
        raise ValueError("status must match reason_codes")
    if (
        REASON_ANALYST_QUEUE_READY_PASS in row.reason_codes
        and row.reason_codes[-1] != REASON_ANALYST_QUEUE_READY_PASS
    ):
        raise ValueError("pass reason must not be mixed with risk reasons")


def _validate_report(
    report: ResearchStrategyEvidenceCostResolutionScorecardReport,
) -> None:
    if report.rows != tuple(sorted(report.rows, key=_row_sort_key)):
        raise ValueError("rows must use deterministic ordering")
    if report.row_count != _decimal_count(len(report.rows)):
        raise ValueError("row_count must match rows")
    if report.pass_count != _decimal_count(_status_count(report.rows, STATUS_PASS)):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _decimal_count(_status_count(report.rows, STATUS_WATCH)):
        raise ValueError("watch_count must match rows")
    if report.block_count != _decimal_count(_status_count(report.rows, STATUS_BLOCK)):
        raise ValueError("block_count must match rows")
    if report.average_readiness_score != _average_ratio(
        tuple(row.readiness_score for row in report.rows),
    ):
        raise ValueError("average_readiness_score must match rows")
    if report.min_readiness_score != min(
        (row.readiness_score for row in report.rows),
        default=_ZERO,
    ):
        raise ValueError("min_readiness_score must match rows")
    if report.min_evidence_completeness_score != min(
        (row.evidence_completeness_score for row in report.rows),
        default=_ZERO,
    ):
        raise ValueError("min_evidence_completeness_score must match rows")
    if report.min_cost_adjusted_edge_score != min(
        (row.cost_adjusted_edge_score for row in report.rows),
        default=_ZERO,
    ):
        raise ValueError("min_cost_adjusted_edge_score must match rows")
    if report.min_microstructure_signal_score != min(
        (row.microstructure_signal_score for row in report.rows),
        default=_ZERO,
    ):
        raise ValueError("min_microstructure_signal_score must match rows")
    if report.max_resolution_ambiguity_score != max(
        (row.resolution_ambiguity_score for row in report.rows),
        default=_ZERO,
    ):
        raise ValueError("max_resolution_ambiguity_score must match rows")
    expected_counts = _reason_code_counts(report.rows)
    expected_codes = tuple(row.reason_code for row in expected_counts)
    if not report.rows:
        expected_counts = (
            ResearchStrategyEvidenceCostResolutionReasonCodeCount(
                reason_code=REASON_EMPTY_INPUT,
                count=_ONE,
                row_ratio=_ONE,
            ),
        )
        expected_codes = (REASON_EMPTY_INPUT,)
    if report.reason_code_counts != expected_counts:
        raise ValueError("reason_code_counts must match rows")
    if report.reason_codes != expected_codes:
        raise ValueError("reason_codes must match reason_code_counts")
    if report.status != _report_status(report.rows):
        raise ValueError("status must match rows")


def _normalize_inputs(
    inputs: Sequence[ResearchStrategyEvidenceCostResolutionInput],
) -> tuple[ResearchStrategyEvidenceCostResolutionInput, ...]:
    if type(inputs) not in (list, tuple):
        raise ValueError("inputs must be a list or tuple")
    normalized = tuple(inputs)
    seen: set[str] = set()
    for row in normalized:
        if type(row) is not ResearchStrategyEvidenceCostResolutionInput:
            raise ValueError(
                "inputs must contain ResearchStrategyEvidenceCostResolutionInput",
            )
        _require_hard_flags("input", row)
        digest = _private_ref_digest(row.queue_item_ref)
        if digest in seen:
            raise ValueError("inputs must be unique by queue item digest")
        seen.add(digest)
    return normalized


def _normalize_rows(
    rows: tuple[ResearchStrategyEvidenceCostResolutionScorecardRow, ...],
) -> tuple[ResearchStrategyEvidenceCostResolutionScorecardRow, ...]:
    if type(rows) not in (list, tuple):
        raise ValueError("rows must be a list or tuple")
    normalized = tuple(rows)
    for row in normalized:
        if type(row) is not ResearchStrategyEvidenceCostResolutionScorecardRow:
            raise ValueError(
                "rows must contain ResearchStrategyEvidenceCostResolutionScorecardRow",
            )
        _require_hard_flags("row", row)
    if normalized != tuple(sorted(normalized, key=_row_sort_key)):
        raise ValueError("rows must use deterministic ordering")
    digests = tuple(row.queue_item_digest for row in normalized)
    if len(set(digests)) != len(digests):
        raise ValueError("rows must have unique queue item digests")
    return normalized


def _normalize_reason_code_counts(
    rows: tuple[ResearchStrategyEvidenceCostResolutionReasonCodeCount, ...],
) -> tuple[ResearchStrategyEvidenceCostResolutionReasonCodeCount, ...]:
    if type(rows) not in (list, tuple):
        raise ValueError("reason_code_counts must be a list or tuple")
    normalized = tuple(rows)
    for row in normalized:
        if type(row) is not ResearchStrategyEvidenceCostResolutionReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "ResearchStrategyEvidenceCostResolutionReasonCodeCount",
            )
        _require_hard_flags("reason count", row)
    if normalized != tuple(
        sorted(normalized, key=lambda item: (-item.count, item.reason_code)),
    ):
        raise ValueError("reason_code_counts must use deterministic ordering")
    if len(set(row.reason_code for row in normalized)) != len(normalized):
        raise ValueError("reason_code_counts must not contain duplicates")
    return normalized


def _normalize_public_notes(
    public_notes: Sequence[ResearchStrategyEvidenceCostResolutionPublicNote],
) -> tuple[ResearchStrategyEvidenceCostResolutionPublicNote, ...]:
    if type(public_notes) not in (list, tuple):
        raise ValueError("public_notes must be a list or tuple")
    normalized = tuple(public_notes)
    for note in normalized:
        if type(note) is not ResearchStrategyEvidenceCostResolutionPublicNote:
            raise ValueError(
                "public_notes must contain "
                "ResearchStrategyEvidenceCostResolutionPublicNote",
            )
        _require_hard_flags("public note", note)
    keys = tuple(note.key for note in normalized)
    if keys != tuple(sorted(keys)):
        raise ValueError("public_notes must be sorted by key")
    if len(set(keys)) != len(keys):
        raise ValueError("public_notes must have unique keys")
    return normalized


def _normalize_upstream_reason_codes(value: tuple[str, ...]) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ValueError("reason_codes must be a tuple")
    for reason_code in value:
        _require_reason_code(
            "reason_codes",
            reason_code,
            _UPSTREAM_REASON_CODE_SEQUENCE,
        )
    normalized = tuple(
        reason_code
        for reason_code in _UPSTREAM_REASON_CODE_SEQUENCE
        if reason_code in value
    )
    if normalized != value:
        raise ValueError("reason_codes must be unique and deterministic")
    return normalized


def _normalize_row_reason_codes(value: tuple[str, ...]) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ValueError("reason_codes must be a tuple")
    for reason_code in value:
        _require_reason_code("reason_codes", reason_code, _ROW_REASON_CODE_SEQUENCE)
    normalized = tuple(
        reason_code for reason_code in _ROW_REASON_CODE_SEQUENCE if reason_code in value
    )
    if normalized != value:
        raise ValueError("reason_codes must be unique and deterministic")
    if REASON_ANALYST_QUEUE_READY_PASS in value:
        generated = tuple(
            reason_code
            for reason_code in value
            if reason_code in _GENERATED_ROW_REASON_CODE_SEQUENCE
        )
        if generated != (REASON_ANALYST_QUEUE_READY_PASS,):
            raise ValueError("reason_codes cannot mix pass with risk reasons")
    return normalized


def _normalize_report_reason_codes(value: tuple[str, ...]) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ValueError("reason_codes must be a tuple")
    for reason_code in value:
        _require_reason_code("reason_codes", reason_code, _REASON_CODE_SEQUENCE)
    if len(set(value)) != len(value):
        raise ValueError("reason_codes must be unique and deterministic")
    return value


def _report_payload(
    report: ResearchStrategyEvidenceCostResolutionScorecardReport,
) -> dict[str, object]:
    payload = _report_payload_without_digest(
        generated_at=report.generated_at,
        config_version=report.config_version,
        status=report.status,
        row_count=report.row_count,
        pass_count=report.pass_count,
        watch_count=report.watch_count,
        block_count=report.block_count,
        average_readiness_score=report.average_readiness_score,
        min_readiness_score=report.min_readiness_score,
        min_evidence_completeness_score=report.min_evidence_completeness_score,
        min_cost_adjusted_edge_score=report.min_cost_adjusted_edge_score,
        min_microstructure_signal_score=report.min_microstructure_signal_score,
        max_resolution_ambiguity_score=report.max_resolution_ambiguity_score,
        rows=report.rows,
        reason_code_counts=report.reason_code_counts,
        reason_codes=report.reason_codes,
        public_notes=report.public_notes,
        paper_only=report.paper_only,
        report_only=report.report_only,
        readonly=report.readonly,
    )
    payload[_DIGEST_FIELD] = report.derived_validation_digest
    return payload


def _report_payload_without_digest(**values: object) -> dict[str, object]:
    payload = _json_ready(values)
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    return payload


def _report_digest(
    report: ResearchStrategyEvidenceCostResolutionScorecardReport,
) -> str:
    return _report_digest_from_values(
        {
            "generated_at": report.generated_at,
            "config_version": report.config_version,
            "status": report.status,
            "row_count": report.row_count,
            "pass_count": report.pass_count,
            "watch_count": report.watch_count,
            "block_count": report.block_count,
            "average_readiness_score": report.average_readiness_score,
            "min_readiness_score": report.min_readiness_score,
            "min_evidence_completeness_score": report.min_evidence_completeness_score,
            "min_cost_adjusted_edge_score": report.min_cost_adjusted_edge_score,
            "min_microstructure_signal_score": report.min_microstructure_signal_score,
            "max_resolution_ambiguity_score": report.max_resolution_ambiguity_score,
            "rows": report.rows,
            "reason_code_counts": report.reason_code_counts,
            "reason_codes": report.reason_codes,
            "public_notes": report.public_notes,
            "paper_only": report.paper_only,
            "report_only": report.report_only,
            "readonly": report.readonly,
        },
    )


def _report_digest_from_values(values: Mapping[str, object]) -> str:
    payload = _json_ready(values)
    _reject_unsafe_public_payload(
        "derived_validation_digest payload",
        payload,
        allow_json_containers=True,
    )
    canonical = json.dumps(
        payload,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    )
    return sha256(canonical.encode("utf-8")).hexdigest()


def _validate_payload_digest(payload: dict[str, object]) -> None:
    digest = payload.get(_DIGEST_FIELD)
    _require_digest(_DIGEST_FIELD, digest)
    payload_without_digest = dict(payload)
    payload_without_digest.pop(_DIGEST_FIELD, None)
    canonical = json.dumps(
        payload_without_digest,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    )
    expected = sha256(canonical.encode("utf-8")).hexdigest()
    if digest != expected:
        raise ValueError("derived_validation_digest mismatch")


def _validate_payload_statuses(value: object) -> None:
    if isinstance(value, Mapping):
        for key, item in value.items():
            if key == "status" and item not in _STATUS_VALUES:
                raise ValueError("status must be pass, watch, or block")
            _validate_payload_statuses(item)
        return
    if isinstance(value, list):
        for item in value:
            _validate_payload_statuses(item)


def _validate_payload_schema(payload: dict[str, object]) -> None:
    try:
        reconstructed = _report_from_payload(payload)
    except ValueError as exc:
        raise ValueError(f"payload schema invalid: {exc}") from exc
    if _report_payload(reconstructed) != payload:
        raise ValueError("payload schema must use canonical values")


def _report_from_payload(
    payload: dict[str, object],
) -> ResearchStrategyEvidenceCostResolutionScorecardReport:
    _require_payload_fields("payload", payload, _REPORT_PAYLOAD_FIELDS)
    rows = tuple(
        _row_from_payload(item, index=index)
        for index, item in enumerate(_require_payload_list("rows", payload["rows"]))
    )
    reason_code_counts = tuple(
        _reason_count_from_payload(item, index=index)
        for index, item in enumerate(
            _require_payload_list(
                "reason_code_counts",
                payload["reason_code_counts"],
            ),
        )
    )
    public_notes = tuple(
        _public_note_from_payload(item, index=index)
        for index, item in enumerate(
            _require_payload_list("public_notes", payload["public_notes"]),
        )
    )
    return ResearchStrategyEvidenceCostResolutionScorecardReport(
        generated_at=_require_payload_datetime(
            "generated_at",
            payload["generated_at"],
        ),
        config_version=_require_payload_string(
            "config_version",
            payload["config_version"],
        ),
        status=_require_payload_string("status", payload["status"]),
        row_count=_require_payload_count_decimal("row_count", payload["row_count"]),
        pass_count=_require_payload_count_decimal(
            "pass_count",
            payload["pass_count"],
        ),
        watch_count=_require_payload_count_decimal(
            "watch_count",
            payload["watch_count"],
        ),
        block_count=_require_payload_count_decimal(
            "block_count",
            payload["block_count"],
        ),
        average_readiness_score=_require_payload_ratio_decimal(
            "average_readiness_score",
            payload["average_readiness_score"],
        ),
        min_readiness_score=_require_payload_ratio_decimal(
            "min_readiness_score",
            payload["min_readiness_score"],
        ),
        min_evidence_completeness_score=_require_payload_ratio_decimal(
            "min_evidence_completeness_score",
            payload["min_evidence_completeness_score"],
        ),
        min_cost_adjusted_edge_score=_require_payload_ratio_decimal(
            "min_cost_adjusted_edge_score",
            payload["min_cost_adjusted_edge_score"],
        ),
        min_microstructure_signal_score=_require_payload_ratio_decimal(
            "min_microstructure_signal_score",
            payload["min_microstructure_signal_score"],
        ),
        max_resolution_ambiguity_score=_require_payload_ratio_decimal(
            "max_resolution_ambiguity_score",
            payload["max_resolution_ambiguity_score"],
        ),
        rows=rows,
        reason_code_counts=reason_code_counts,
        reason_codes=_require_payload_string_tuple(
            "reason_codes",
            payload["reason_codes"],
        ),
        public_notes=public_notes,
        derived_validation_digest=_require_payload_string(
            _DIGEST_FIELD,
            payload[_DIGEST_FIELD],
        ),
        paper_only=_require_payload_true("paper_only", payload["paper_only"]),
        report_only=_require_payload_true("report_only", payload["report_only"]),
        readonly=_require_payload_true("readonly", payload["readonly"]),
    )


def _row_from_payload(
    value: object,
    *,
    index: int,
) -> ResearchStrategyEvidenceCostResolutionScorecardRow:
    path = f"rows[{index}]"
    row = _require_payload_object(path, value)
    _require_payload_fields(path, row, _ROW_PAYLOAD_FIELDS)
    return ResearchStrategyEvidenceCostResolutionScorecardRow(
        queue_item_digest=_require_payload_string(
            f"{path}.queue_item_digest",
            row["queue_item_digest"],
        ),
        evidence_completeness_score=_require_payload_ratio_decimal(
            f"{path}.evidence_completeness_score",
            row["evidence_completeness_score"],
        ),
        evidence_gap_score=_require_payload_ratio_decimal(
            f"{path}.evidence_gap_score",
            row["evidence_gap_score"],
        ),
        cost_adjusted_edge_score=_require_payload_ratio_decimal(
            f"{path}.cost_adjusted_edge_score",
            row["cost_adjusted_edge_score"],
        ),
        cost_adjusted_edge_gap_score=_require_payload_ratio_decimal(
            f"{path}.cost_adjusted_edge_gap_score",
            row["cost_adjusted_edge_gap_score"],
        ),
        microstructure_signal_score=_require_payload_ratio_decimal(
            f"{path}.microstructure_signal_score",
            row["microstructure_signal_score"],
        ),
        microstructure_gap_score=_require_payload_ratio_decimal(
            f"{path}.microstructure_gap_score",
            row["microstructure_gap_score"],
        ),
        resolution_ambiguity_score=_require_payload_ratio_decimal(
            f"{path}.resolution_ambiguity_score",
            row["resolution_ambiguity_score"],
        ),
        resolution_certainty_score=_require_payload_ratio_decimal(
            f"{path}.resolution_certainty_score",
            row["resolution_certainty_score"],
        ),
        readiness_score=_require_payload_ratio_decimal(
            f"{path}.readiness_score",
            row["readiness_score"],
        ),
        observed_at=_require_payload_datetime(
            f"{path}.observed_at",
            row["observed_at"],
        ),
        status=_require_payload_string(f"{path}.status", row["status"]),
        reason_codes=_require_payload_string_tuple(
            f"{path}.reason_codes",
            row["reason_codes"],
        ),
        paper_only=_require_payload_true(
            f"{path}.paper_only",
            row["paper_only"],
        ),
        report_only=_require_payload_true(
            f"{path}.report_only",
            row["report_only"],
        ),
        readonly=_require_payload_true(f"{path}.readonly", row["readonly"]),
    )


def _reason_count_from_payload(
    value: object,
    *,
    index: int,
) -> ResearchStrategyEvidenceCostResolutionReasonCodeCount:
    path = f"reason_code_counts[{index}]"
    count = _require_payload_object(path, value)
    _require_payload_fields(path, count, _REASON_COUNT_PAYLOAD_FIELDS)
    return ResearchStrategyEvidenceCostResolutionReasonCodeCount(
        reason_code=_require_payload_string(
            f"{path}.reason_code",
            count["reason_code"],
        ),
        count=_require_payload_count_decimal(f"{path}.count", count["count"]),
        row_ratio=_require_payload_ratio_decimal(
            f"{path}.row_ratio",
            count["row_ratio"],
        ),
        paper_only=_require_payload_true(
            f"{path}.paper_only",
            count["paper_only"],
        ),
        report_only=_require_payload_true(
            f"{path}.report_only",
            count["report_only"],
        ),
        readonly=_require_payload_true(f"{path}.readonly", count["readonly"]),
    )


def _public_note_from_payload(
    value: object,
    *,
    index: int,
) -> ResearchStrategyEvidenceCostResolutionPublicNote:
    path = f"public_notes[{index}]"
    note = _require_payload_object(path, value)
    _require_payload_fields(path, note, _PUBLIC_NOTE_PAYLOAD_FIELDS)
    return ResearchStrategyEvidenceCostResolutionPublicNote(
        key=_require_payload_string(f"{path}.key", note["key"]),
        value=_require_payload_string(f"{path}.value", note["value"]),
        paper_only=_require_payload_true(
            f"{path}.paper_only",
            note["paper_only"],
        ),
        report_only=_require_payload_true(
            f"{path}.report_only",
            note["report_only"],
        ),
        readonly=_require_payload_true(f"{path}.readonly", note["readonly"]),
    )


def _require_payload_fields(
    path: str,
    value: dict[str, object],
    expected_fields: frozenset[str],
) -> None:
    if frozenset(value) != expected_fields:
        raise ValueError(f"{path} fields must match the payload schema")


def _require_payload_object(path: str, value: object) -> dict[str, object]:
    if type(value) is not dict:
        raise ValueError(f"{path} must be a JSON object")
    return value


def _require_payload_list(path: str, value: object) -> list[object]:
    if type(value) is not list:
        raise ValueError(f"{path} must be a JSON list")
    return value


def _require_payload_string(path: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{path} must be a string")
    return value


def _require_payload_string_tuple(path: str, value: object) -> tuple[str, ...]:
    return tuple(
        _require_payload_string(f"{path}[{index}]", item)
        for index, item in enumerate(_require_payload_list(path, value))
    )


def _require_payload_true(path: str, value: object) -> bool:
    if value is not True:
        raise ValueError(f"{path} must be True")
    return True


def _require_payload_decimal(path: str, value: object) -> Decimal:
    if type(value) is not str or _DECIMAL_PAYLOAD_RE.fullmatch(value) is None:
        raise ValueError(f"{path} must be a canonical Decimal string")
    return Decimal(value)


def _require_payload_count_decimal(path: str, value: object) -> Decimal:
    return _require_nonnegative_count_decimal(
        path,
        _require_payload_decimal(path, value),
    )


def _require_payload_ratio_decimal(path: str, value: object) -> Decimal:
    return _require_ratio_decimal(path, _require_payload_decimal(path, value))


def _require_payload_datetime(path: str, value: object) -> datetime:
    text = _require_payload_string(path, value)
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError as exc:
        raise ValueError(f"{path} must be an ISO datetime") from exc
    normalized = _as_utc(path, parsed)
    if normalized.isoformat() != text:
        raise ValueError(f"{path} must be a canonical UTC datetime")
    return normalized


def _copy_json_object(value: dict[str, object]) -> dict[str, object]:
    copied = _copy_json_value(value)
    if type(copied) is not dict:
        raise ValueError("payload must be a JSON object")
    return copied


def _copy_json_value(value: object) -> object:
    if value is None or type(value) is bool or type(value) is str:
        return value
    if type(value) is int or isinstance(value, float):
        raise ValueError("payload numeric values must be Decimal strings")
    if isinstance(value, Mapping):
        copied: dict[str, object] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("payload keys must be strings")
            copied[key] = _copy_json_value(item)
        return copied
    if isinstance(value, list):
        return [_copy_json_value(item) for item in value]
    raise ValueError("payload contains unsupported JSON value")


def _json_ready(value: Any) -> Any:
    if value is None:
        return None
    if is_dataclass(value) and not isinstance(value, type):
        ready: dict[str, Any] = {}
        for field in fields(value):
            ready[field.name] = _json_ready(getattr(value, field.name))
        return ready
    if type(value) is Decimal:
        if not value.is_finite():
            raise ValueError("Decimal payload value must be finite")
        return str(value)
    if type(value) is datetime:
        return _as_utc("datetime payload value", value).isoformat()
    if type(value) is bool or type(value) is str:
        return value
    if type(value) is int or isinstance(value, float):
        raise ValueError("numeric payload values must be Decimal strings")
    if isinstance(value, Mapping):
        ready: dict[str, Any] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            ready[key] = _json_ready(item)
        return ready
    if isinstance(value, (list, tuple)):
        return [_json_ready(item) for item in value]
    raise ValueError("payload value is not JSON serializable")


def _reject_unsafe_public_payload(
    label: str,
    value: object,
    path: str = "",
    *,
    allow_json_containers: bool = False,
) -> None:
    current_path = path or label
    if is_dataclass(value) and not isinstance(value, type):
        for field in fields(value):
            _reject_unsafe_public_key(field.name, current_path)
            _reject_unsafe_public_payload(
                label,
                getattr(value, field.name),
                field.name if not path else f"{path}.{field.name}",
                allow_json_containers=allow_json_containers,
            )
        return
    if isinstance(value, Mapping):
        if not allow_json_containers:
            raise ValueError(f"{current_path} must remain constructor-normalized")
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            _reject_unsafe_public_key(key, current_path)
            _reject_unsafe_public_payload(
                label,
                item,
                key if not path else f"{path}.{key}",
                allow_json_containers=True,
            )
        return
    if isinstance(value, (list, tuple)):
        if type(value) is list and not allow_json_containers:
            raise ValueError(f"{current_path} must remain constructor-normalized")
        for index, item in enumerate(value):
            _reject_unsafe_public_payload(
                label,
                item,
                f"{current_path}[{index}]",
                allow_json_containers=allow_json_containers,
            )
        return
    if type(value) is str:
        _reject_unsafe_public_string(current_path, value)
        return
    if (
        value is None
        or type(value) is bool
        or type(value) is Decimal
        or type(value) is datetime
    ):
        return
    raise ValueError(f"{current_path} is not a supported public payload value")


def _reject_unsafe_public_key(key: str, path: str) -> None:
    lowered = key.lower()
    if any(fragment in lowered for fragment in _UNSAFE_PUBLIC_FRAGMENTS):
        raise ValueError(f"{path}.{key} has unsafe public field")


def _reject_unsafe_public_string(field_name: str, value: str) -> None:
    lowered = value.lower()
    if any(fragment in lowered for fragment in _UNSAFE_PUBLIC_FRAGMENTS):
        raise ValueError(f"{field_name} has unsafe public value")


def _require_exact_type(value: object, expected_type: type[object], label: str) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{label} must be exactly {expected_type.__name__}")


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in _PHASE_FLAG_FIELDS:
        if getattr(value, field_name) is not True:
            raise ValueError(f"{field_name} must be True for {label}")


def _require_private_ref(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if value.strip() != value or not value:
        raise ValueError(f"{field_name} must be non-empty private text")
    if len(value) > 2048:
        raise ValueError(f"{field_name} must not exceed 2048 characters")
    return value


def _private_ref_digest(value: str) -> str:
    return f"sha256:{sha256(value.encode('utf-8')).hexdigest()}"


def _require_private_digest(field_name: str, value: object) -> str:
    if type(value) is not str or not _PRIVATE_DIGEST_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a redacted sha256 digest")
    return value


def _require_public_identifier(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not _PUBLIC_IDENTIFIER_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a public identifier")
    _reject_unsafe_public_string(field_name, value)
    return value


def _require_public_text(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if value.strip() != value or not value:
        raise ValueError(f"{field_name} must be non-empty public text")
    if len(value) > 512:
        raise ValueError(f"{field_name} must not exceed 512 characters")
    _reject_unsafe_public_string(field_name, value)
    return value


def _require_status(field_name: str, value: object) -> str:
    if type(value) is not str or value not in _STATUS_VALUES:
        raise ValueError(f"{field_name} must be pass, watch, or block")
    return value


def _require_reason_code(
    field_name: str,
    value: object,
    allowed_values: tuple[str, ...],
) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a reason code")
    _require_public_identifier(field_name, value)
    if value not in allowed_values:
        raise ValueError(f"{field_name} must be a supported reason code")
    return value


def _require_digest(field_name: str, value: object) -> str:
    if type(value) is not str or not _DIGEST_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a lowercase sha256 digest")
    return value


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return _quantize(value)


def _require_nonnegative_count_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < _ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _require_ratio_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < _ZERO or normalized > _ONE:
        raise ValueError(f"{field_name} must be between zero and one")
    return normalized


def _decimal_count(value: int) -> Decimal:
    if value < 0:
        raise ValueError("count must be nonnegative")
    return Decimal(value).quantize(_QUANT)


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == _ZERO:
        return _ZERO
    return _quantize(numerator / denominator)


def _average_ratio(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return _ZERO
    return _quantize(sum(values, _ZERO) / Decimal(len(values)))


def _inverse_ratio(value: Decimal) -> Decimal:
    return _clamp_ratio(_ONE - value)


def _clamp_ratio(value: Decimal) -> Decimal:
    normalized = _quantize(value)
    if normalized < _ZERO:
        return _ZERO
    if normalized > _ONE:
        return _ONE
    return normalized


def _quantize(value: Decimal) -> Decimal:
    return value.quantize(_QUANT, rounding=ROUND_HALF_UP)


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


__all__ = (
    "DEFAULT_RESEARCH_STRATEGY_EVIDENCE_COST_RESOLUTION_SCORECARD_CONFIG_VERSION",
    "ResearchStrategyEvidenceCostResolutionInput",
    "ResearchStrategyEvidenceCostResolutionPublicNote",
    "ResearchStrategyEvidenceCostResolutionReasonCodeCount",
    "ResearchStrategyEvidenceCostResolutionScorecardConfig",
    "ResearchStrategyEvidenceCostResolutionScorecardReport",
    "ResearchStrategyEvidenceCostResolutionScorecardRow",
    "build_research_strategy_evidence_cost_resolution_scorecard_report",
    "research_strategy_evidence_cost_resolution_scorecard_report_payload",
)
