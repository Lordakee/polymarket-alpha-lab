"""Report-only evidence chain decision readiness delta rows.

The module scores sanitized changes in decision readiness as evidence chains
improve or deteriorate. It is intentionally readonly and public-payload only:
no database, network, wallet, order, recommendation, sizing, or live-trading
surface is exposed.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import InitVar, asdict, dataclass, field, fields, is_dataclass
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from hashlib import sha256
import json
import re
from typing import Any, Mapping, Sequence


DEFAULT_RESEARCH_STRATEGY_EVIDENCE_CHAIN_DECISION_DELTA_REPORT_VERSION = (
    "research-strategy-evidence-chain-decision-delta-report-v0"
)

STATUS_PASS = "pass"
STATUS_WATCH = "watch"
STATUS_BLOCK = "block"

REASON_EMPTY_INPUT = "empty_input"
REASON_EVIDENCE_COMPLETENESS_DETERIORATED_BLOCK = (
    "evidence_completeness_deteriorated_block"
)
REASON_EVIDENCE_COMPLETENESS_DETERIORATED_WATCH = (
    "evidence_completeness_deteriorated_watch"
)
REASON_CONFIDENCE_DETERIORATED_BLOCK = "confidence_deteriorated_block"
REASON_CONFIDENCE_DETERIORATED_WATCH = "confidence_deteriorated_watch"
REASON_CONTRADICTION_PRESSURE_INCREASED_BLOCK = (
    "contradiction_pressure_increased_block"
)
REASON_CONTRADICTION_PRESSURE_INCREASED_WATCH = (
    "contradiction_pressure_increased_watch"
)
REASON_LIQUIDITY_COST_PRESSURE_BLOCK = "liquidity_cost_pressure_block"
REASON_LIQUIDITY_COST_PRESSURE_WATCH = "liquidity_cost_pressure_watch"
REASON_REVIEW_URGENCY_BLOCK = "review_urgency_block"
REASON_REVIEW_URGENCY_WATCH = "review_urgency_watch"
REASON_DECISION_DELTA_SCORE_BLOCK = "decision_delta_score_block"
REASON_DECISION_DELTA_SCORE_WATCH = "decision_delta_score_watch"
REASON_DECISION_READINESS_DELTA_PASS = "decision_readiness_delta_pass"

_ROW_REASON_CODE_SEQUENCE = (
    REASON_EVIDENCE_COMPLETENESS_DETERIORATED_BLOCK,
    REASON_EVIDENCE_COMPLETENESS_DETERIORATED_WATCH,
    REASON_CONFIDENCE_DETERIORATED_BLOCK,
    REASON_CONFIDENCE_DETERIORATED_WATCH,
    REASON_CONTRADICTION_PRESSURE_INCREASED_BLOCK,
    REASON_CONTRADICTION_PRESSURE_INCREASED_WATCH,
    REASON_LIQUIDITY_COST_PRESSURE_BLOCK,
    REASON_LIQUIDITY_COST_PRESSURE_WATCH,
    REASON_REVIEW_URGENCY_BLOCK,
    REASON_REVIEW_URGENCY_WATCH,
    REASON_DECISION_DELTA_SCORE_BLOCK,
    REASON_DECISION_DELTA_SCORE_WATCH,
    REASON_DECISION_READINESS_DELTA_PASS,
)
_REPORT_REASON_CODE_SEQUENCE = (REASON_EMPTY_INPUT, *_ROW_REASON_CODE_SEQUENCE)
_BLOCK_REASON_CODES = frozenset(
    (
        REASON_EVIDENCE_COMPLETENESS_DETERIORATED_BLOCK,
        REASON_CONFIDENCE_DETERIORATED_BLOCK,
        REASON_CONTRADICTION_PRESSURE_INCREASED_BLOCK,
        REASON_LIQUIDITY_COST_PRESSURE_BLOCK,
        REASON_REVIEW_URGENCY_BLOCK,
        REASON_DECISION_DELTA_SCORE_BLOCK,
    ),
)
_WATCH_REASON_CODES = frozenset(
    reason_code
    for reason_code in _ROW_REASON_CODE_SEQUENCE
    if reason_code.endswith("_watch")
)

_QUANT = Decimal("0.000001")
_ZERO = Decimal("0.000000")
_ONE = Decimal("1.000000")
_NEG_ONE = Decimal("-1.000000")
_DIGEST_FIELD = "derived_validation_digest"
_STATUSES = frozenset((STATUS_PASS, STATUS_WATCH, STATUS_BLOCK))
_PUBLIC_IDENTIFIER_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,127}$")
_PRIVATE_DIGEST_RE = re.compile(r"^sha256:[0-9a-f]{64}$")
_DIGEST_RE = re.compile(r"^[0-9a-f]{64}$")
_UNSAFE_PUBLIC_FRAGMENTS = (
    "candidate",
    "condition",
    "market",
    "slug",
    "question",
    "source_url",
    "source-url",
    "source url",
    "source_text",
    "source-text",
    "source text",
    "sourceurl",
    "sourcetext",
    "dsn",
    "database",
    "db_",
    "db-",
    "db ",
    "execute",
    "execution",
    "live",
    "live_",
    "live-",
    "live ",
    "network",
    "api_key",
    "api-key",
    "private_key",
    "private-key",
    "secret",
    "postgres",
    "table",
    "token",
    "wallet",
    "auth",
    "order",
    "trade",
    "trading",
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
class ResearchStrategyEvidenceChainDecisionDeltaConfig(_FinalPublicDataclass):
    config_version: str = (
        DEFAULT_RESEARCH_STRATEGY_EVIDENCE_CHAIN_DECISION_DELTA_REPORT_VERSION
    )
    pass_min_delta_score: Decimal = Decimal("0.100000")
    block_below_delta_score: Decimal = Decimal("-0.100000")
    min_pass_evidence_completeness_delta: Decimal = Decimal("0.100000")
    min_watch_evidence_completeness_delta: Decimal = Decimal("-0.200000")
    min_pass_confidence_delta: Decimal = Decimal("0.100000")
    min_watch_confidence_delta: Decimal = Decimal("-0.200000")
    max_pass_contradiction_pressure_delta: Decimal = Decimal("0.000000")
    max_watch_contradiction_pressure_delta: Decimal = Decimal("0.300000")
    max_pass_liquidity_cost_pressure: Decimal = Decimal("0.200000")
    max_watch_liquidity_cost_pressure: Decimal = Decimal("0.500000")
    max_pass_review_urgency: Decimal = Decimal("0.200000")
    max_watch_review_urgency: Decimal = Decimal("0.600000")
    evidence_completeness_delta_weight: Decimal = Decimal("0.300000")
    confidence_delta_weight: Decimal = Decimal("0.250000")
    contradiction_pressure_delta_weight: Decimal = Decimal("0.200000")
    liquidity_cost_pressure_weight: Decimal = Decimal("0.150000")
    review_urgency_weight: Decimal = Decimal("0.100000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchStrategyEvidenceChainDecisionDeltaConfig, "config")
        object.__setattr__(
            self,
            "config_version",
            _require_public_identifier("config_version", self.config_version),
        )
        if (
            self.config_version
            != DEFAULT_RESEARCH_STRATEGY_EVIDENCE_CHAIN_DECISION_DELTA_REPORT_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "pass_min_delta_score",
            "block_below_delta_score",
            "min_pass_evidence_completeness_delta",
            "min_watch_evidence_completeness_delta",
            "min_pass_confidence_delta",
            "min_watch_confidence_delta",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_delta_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "max_pass_contradiction_pressure_delta",
            "max_watch_contradiction_pressure_delta",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_delta_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "max_pass_liquidity_cost_pressure",
            "max_watch_liquidity_cost_pressure",
            "max_pass_review_urgency",
            "max_watch_review_urgency",
            "evidence_completeness_delta_weight",
            "confidence_delta_weight",
            "contradiction_pressure_delta_weight",
            "liquidity_cost_pressure_weight",
            "review_urgency_weight",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        if self.pass_min_delta_score < self.block_below_delta_score:
            raise ValueError(
                "pass_min_delta_score must be at least block_below_delta_score",
            )
        if (
            self.min_pass_evidence_completeness_delta
            < self.min_watch_evidence_completeness_delta
        ):
            raise ValueError(
                "min_pass_evidence_completeness_delta must be at least "
                "min_watch_evidence_completeness_delta",
            )
        if self.min_pass_confidence_delta < self.min_watch_confidence_delta:
            raise ValueError(
                "min_pass_confidence_delta must be at least min_watch_confidence_delta",
            )
        if (
            self.max_pass_contradiction_pressure_delta
            > self.max_watch_contradiction_pressure_delta
        ):
            raise ValueError(
                "max_pass_contradiction_pressure_delta must not exceed "
                "max_watch_contradiction_pressure_delta",
            )
        if self.max_pass_liquidity_cost_pressure > self.max_watch_liquidity_cost_pressure:
            raise ValueError(
                "max_pass_liquidity_cost_pressure must not exceed "
                "max_watch_liquidity_cost_pressure",
            )
        if self.max_pass_review_urgency > self.max_watch_review_urgency:
            raise ValueError(
                "max_pass_review_urgency must not exceed max_watch_review_urgency",
            )
        weight_sum = _quantize(
            self.evidence_completeness_delta_weight
            + self.confidence_delta_weight
            + self.contradiction_pressure_delta_weight
            + self.liquidity_cost_pressure_weight
            + self.review_urgency_weight,
        )
        if weight_sum != _ONE:
            raise ValueError("decision delta weights must sum to one")
        _require_hard_flags("config", self)
        _reject_unsafe_public_payload("config", self)


@dataclass(frozen=True)
class ResearchStrategyEvidenceChainDecisionDeltaInput(_FinalPublicDataclass):
    chain_ref: str = field(repr=False)
    evidence_completeness_delta: Decimal
    source_confidence_delta: Decimal
    contradiction_pressure_delta: Decimal
    liquidity_cost_pressure: Decimal
    review_urgency: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchStrategyEvidenceChainDecisionDeltaInput, "input")
        object.__setattr__(
            self,
            "chain_ref",
            _require_private_ref("chain_ref", self.chain_ref),
        )
        for field_name in (
            "evidence_completeness_delta",
            "source_confidence_delta",
            "contradiction_pressure_delta",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_delta_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in ("liquidity_cost_pressure", "review_urgency"):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        _require_hard_flags("input", self)


@dataclass(frozen=True)
class ResearchStrategyEvidenceChainDecisionDeltaRow(_FinalPublicDataclass):
    chain_digest: str
    evidence_completeness_delta: Decimal
    source_confidence_delta: Decimal
    contradiction_pressure_delta: Decimal
    liquidity_cost_pressure: Decimal
    review_urgency: Decimal
    delta_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True
    validation_config: InitVar[
        ResearchStrategyEvidenceChainDecisionDeltaConfig | None
    ] = None

    def __post_init__(
        self,
        validation_config: ResearchStrategyEvidenceChainDecisionDeltaConfig | None,
    ) -> None:
        _require_exact_type(self, ResearchStrategyEvidenceChainDecisionDeltaRow, "row")
        object.__setattr__(
            self,
            "chain_digest",
            _require_private_digest("chain_digest", self.chain_digest),
        )
        for field_name in (
            "evidence_completeness_delta",
            "source_confidence_delta",
            "contradiction_pressure_delta",
            "delta_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_delta_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in ("liquidity_cost_pressure", "review_urgency"):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
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
class ResearchStrategyEvidenceChainDecisionDeltaReasonCodeCount(_FinalPublicDataclass):
    reason_code: str
    count: Decimal
    row_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchStrategyEvidenceChainDecisionDeltaReasonCodeCount,
            "reason count",
        )
        _require_reason_code("reason_code", self.reason_code, _REPORT_REASON_CODE_SEQUENCE)
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
class ResearchStrategyEvidenceChainDecisionDeltaReport(_FinalPublicDataclass):
    config_version: str
    status: str
    row_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    average_delta_score: Decimal
    min_delta_score: Decimal
    max_delta_score: Decimal
    max_liquidity_cost_pressure: Decimal
    max_review_urgency: Decimal
    rows: tuple[ResearchStrategyEvidenceChainDecisionDeltaRow, ...]
    reason_code_counts: tuple[
        ResearchStrategyEvidenceChainDecisionDeltaReasonCodeCount,
        ...,
    ]
    reason_codes: tuple[str, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchStrategyEvidenceChainDecisionDeltaReport, "report")
        object.__setattr__(
            self,
            "config_version",
            _require_public_identifier("config_version", self.config_version),
        )
        if (
            self.config_version
            != DEFAULT_RESEARCH_STRATEGY_EVIDENCE_CHAIN_DECISION_DELTA_REPORT_VERSION
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
            "average_delta_score",
            "min_delta_score",
            "max_delta_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_delta_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in ("max_liquidity_cost_pressure", "max_review_urgency"):
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
    def public_payload(self) -> dict[str, object]:
        return research_strategy_evidence_chain_decision_delta_public_payload(self)


def build_research_strategy_evidence_chain_decision_delta_report(
    inputs: Sequence[ResearchStrategyEvidenceChainDecisionDeltaInput],
    *,
    config: ResearchStrategyEvidenceChainDecisionDeltaConfig | None = None,
) -> ResearchStrategyEvidenceChainDecisionDeltaReport:
    """Build a deterministic analyst-only report of decision readiness deltas."""

    cfg = (
        ResearchStrategyEvidenceChainDecisionDeltaConfig()
        if config is None
        else config
    )
    if type(cfg) is not ResearchStrategyEvidenceChainDecisionDeltaConfig:
        raise ValueError(
            "config must be a ResearchStrategyEvidenceChainDecisionDeltaConfig",
        )
    _require_hard_flags("config", cfg)
    normalized_inputs = _normalize_inputs(inputs)
    rows = tuple(
        sorted(
            (_row_for_input(row, cfg) for row in normalized_inputs),
            key=_row_sort_key,
        ),
    )
    reason_code_counts = _reason_code_counts(rows)
    reason_codes = tuple(item.reason_code for item in reason_code_counts)
    if not rows:
        reason_code_counts = (
            ResearchStrategyEvidenceChainDecisionDeltaReasonCodeCount(
                reason_code=REASON_EMPTY_INPUT,
                count=_ONE,
                row_ratio=_ONE,
            ),
        )
        reason_codes = (REASON_EMPTY_INPUT,)
    values: dict[str, object] = {
        "config_version": cfg.config_version,
        "status": _report_status(rows),
        "row_count": _decimal_count(len(rows)),
        "pass_count": _decimal_count(_status_count(rows, STATUS_PASS)),
        "watch_count": _decimal_count(_status_count(rows, STATUS_WATCH)),
        "block_count": _decimal_count(_status_count(rows, STATUS_BLOCK)),
        "average_delta_score": _average_delta(tuple(row.delta_score for row in rows)),
        "min_delta_score": min((row.delta_score for row in rows), default=_ZERO),
        "max_delta_score": max((row.delta_score for row in rows), default=_ZERO),
        "max_liquidity_cost_pressure": max(
            (row.liquidity_cost_pressure for row in rows),
            default=_ZERO,
        ),
        "max_review_urgency": max((row.review_urgency for row in rows), default=_ZERO),
        "rows": rows,
        "reason_code_counts": reason_code_counts,
        "reason_codes": reason_codes,
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    return ResearchStrategyEvidenceChainDecisionDeltaReport(
        **values,
        derived_validation_digest=_report_digest_from_values(values),
    )


def research_strategy_evidence_chain_decision_delta_public_payload(
    value: ResearchStrategyEvidenceChainDecisionDeltaReport | dict[str, object],
) -> dict[str, object]:
    if type(value) is ResearchStrategyEvidenceChainDecisionDeltaReport:
        _require_hard_flags("report", value)
        payload = _report_payload(value)
    elif type(value) is dict:
        payload = _copy_json_object(value)
    else:
        raise ValueError(
            "value must be a ResearchStrategyEvidenceChainDecisionDeltaReport or dict",
        )
    _validate_payload_statuses(payload)
    _reject_unsafe_public_payload("public payload", payload, allow_json_containers=True)
    _require_hard_flags("public payload", _PayloadFlags(payload))
    _validate_payload_digest(payload)
    _validate_public_payload_schema(payload)
    return payload


def research_strategy_evidence_chain_decision_delta_digest(
    value: ResearchStrategyEvidenceChainDecisionDeltaReport | dict[str, object],
) -> str:
    payload = research_strategy_evidence_chain_decision_delta_public_payload(value)
    digest = payload[_DIGEST_FIELD]
    if type(digest) is not str:
        raise ValueError("derived_validation_digest must be a string")
    return digest


def _row_for_input(
    item: ResearchStrategyEvidenceChainDecisionDeltaInput,
    config: ResearchStrategyEvidenceChainDecisionDeltaConfig,
) -> ResearchStrategyEvidenceChainDecisionDeltaRow:
    delta_score = _decision_delta_score(
        evidence_completeness_delta=item.evidence_completeness_delta,
        source_confidence_delta=item.source_confidence_delta,
        contradiction_pressure_delta=item.contradiction_pressure_delta,
        liquidity_cost_pressure=item.liquidity_cost_pressure,
        review_urgency=item.review_urgency,
        config=config,
    )
    reason_codes = _row_reason_codes(
        evidence_completeness_delta=item.evidence_completeness_delta,
        source_confidence_delta=item.source_confidence_delta,
        contradiction_pressure_delta=item.contradiction_pressure_delta,
        liquidity_cost_pressure=item.liquidity_cost_pressure,
        review_urgency=item.review_urgency,
        delta_score=delta_score,
        config=config,
    )
    return ResearchStrategyEvidenceChainDecisionDeltaRow(
        chain_digest=_private_ref_digest(item.chain_ref),
        evidence_completeness_delta=item.evidence_completeness_delta,
        source_confidence_delta=item.source_confidence_delta,
        contradiction_pressure_delta=item.contradiction_pressure_delta,
        liquidity_cost_pressure=item.liquidity_cost_pressure,
        review_urgency=item.review_urgency,
        delta_score=delta_score,
        status=_row_status(reason_codes),
        reason_codes=reason_codes,
        validation_config=config,
    )


def _decision_delta_score(
    *,
    evidence_completeness_delta: Decimal,
    source_confidence_delta: Decimal,
    contradiction_pressure_delta: Decimal,
    liquidity_cost_pressure: Decimal,
    review_urgency: Decimal,
    config: ResearchStrategyEvidenceChainDecisionDeltaConfig,
) -> Decimal:
    score = (
        evidence_completeness_delta * config.evidence_completeness_delta_weight
        + source_confidence_delta * config.confidence_delta_weight
        - contradiction_pressure_delta * config.contradiction_pressure_delta_weight
        - liquidity_cost_pressure * config.liquidity_cost_pressure_weight
        - review_urgency * config.review_urgency_weight
    )
    return _clamp_delta(score)


def _row_reason_codes(
    *,
    evidence_completeness_delta: Decimal,
    source_confidence_delta: Decimal,
    contradiction_pressure_delta: Decimal,
    liquidity_cost_pressure: Decimal,
    review_urgency: Decimal,
    delta_score: Decimal,
    config: ResearchStrategyEvidenceChainDecisionDeltaConfig,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    if evidence_completeness_delta < config.min_watch_evidence_completeness_delta:
        reason_codes.append(REASON_EVIDENCE_COMPLETENESS_DETERIORATED_BLOCK)
    elif evidence_completeness_delta < config.min_pass_evidence_completeness_delta:
        reason_codes.append(REASON_EVIDENCE_COMPLETENESS_DETERIORATED_WATCH)
    if source_confidence_delta < config.min_watch_confidence_delta:
        reason_codes.append(REASON_CONFIDENCE_DETERIORATED_BLOCK)
    elif source_confidence_delta < config.min_pass_confidence_delta:
        reason_codes.append(REASON_CONFIDENCE_DETERIORATED_WATCH)
    if contradiction_pressure_delta > config.max_watch_contradiction_pressure_delta:
        reason_codes.append(REASON_CONTRADICTION_PRESSURE_INCREASED_BLOCK)
    elif contradiction_pressure_delta > config.max_pass_contradiction_pressure_delta:
        reason_codes.append(REASON_CONTRADICTION_PRESSURE_INCREASED_WATCH)
    if liquidity_cost_pressure > config.max_watch_liquidity_cost_pressure:
        reason_codes.append(REASON_LIQUIDITY_COST_PRESSURE_BLOCK)
    elif liquidity_cost_pressure > config.max_pass_liquidity_cost_pressure:
        reason_codes.append(REASON_LIQUIDITY_COST_PRESSURE_WATCH)
    if review_urgency > config.max_watch_review_urgency:
        reason_codes.append(REASON_REVIEW_URGENCY_BLOCK)
    elif review_urgency > config.max_pass_review_urgency:
        reason_codes.append(REASON_REVIEW_URGENCY_WATCH)
    if delta_score < config.block_below_delta_score:
        reason_codes.append(REASON_DECISION_DELTA_SCORE_BLOCK)
    elif delta_score < config.pass_min_delta_score:
        reason_codes.append(REASON_DECISION_DELTA_SCORE_WATCH)
    if not reason_codes:
        reason_codes.append(REASON_DECISION_READINESS_DELTA_PASS)
    return _normalize_row_reason_codes(tuple(reason_codes))


def _row_status(reason_codes: tuple[str, ...]) -> str:
    if any(reason_code in _BLOCK_REASON_CODES for reason_code in reason_codes):
        return STATUS_BLOCK
    if reason_codes == (REASON_DECISION_READINESS_DELTA_PASS,):
        return STATUS_PASS
    return STATUS_WATCH


def _report_status(rows: tuple[ResearchStrategyEvidenceChainDecisionDeltaRow, ...]) -> str:
    if not rows:
        return STATUS_BLOCK
    if any(row.status == STATUS_BLOCK for row in rows):
        return STATUS_BLOCK
    if any(row.status == STATUS_WATCH for row in rows):
        return STATUS_WATCH
    return STATUS_PASS


def _status_count(
    rows: tuple[ResearchStrategyEvidenceChainDecisionDeltaRow, ...],
    status: str,
) -> int:
    return sum(1 for row in rows if row.status == status)


def _row_sort_key(row: ResearchStrategyEvidenceChainDecisionDeltaRow) -> tuple[int, Decimal, str]:
    return (_status_rank(row.status), row.delta_score, row.chain_digest)


def _status_rank(value: str) -> int:
    return {STATUS_BLOCK: 0, STATUS_WATCH: 1, STATUS_PASS: 2}[value]


def _reason_code_counts(
    rows: tuple[ResearchStrategyEvidenceChainDecisionDeltaRow, ...],
) -> tuple[ResearchStrategyEvidenceChainDecisionDeltaReasonCodeCount, ...]:
    total = _decimal_count(len(rows))
    counts: Counter[str] = Counter(
        reason_code for row in rows for reason_code in row.reason_codes
    )
    return tuple(
        ResearchStrategyEvidenceChainDecisionDeltaReasonCodeCount(
            reason_code=reason_code,
            count=_decimal_count(count),
            row_ratio=_ratio(_decimal_count(count), total),
        )
        for reason_code, count in sorted(counts.items(), key=lambda item: (-item[1], item[0]))
    )


def _validate_row(
    row: ResearchStrategyEvidenceChainDecisionDeltaRow,
    config: ResearchStrategyEvidenceChainDecisionDeltaConfig | None,
) -> None:
    if config is not None:
        if type(config) is not ResearchStrategyEvidenceChainDecisionDeltaConfig:
            raise ValueError(
                "validation_config must be a "
                "ResearchStrategyEvidenceChainDecisionDeltaConfig",
            )
        expected_score = _decision_delta_score(
            evidence_completeness_delta=row.evidence_completeness_delta,
            source_confidence_delta=row.source_confidence_delta,
            contradiction_pressure_delta=row.contradiction_pressure_delta,
            liquidity_cost_pressure=row.liquidity_cost_pressure,
            review_urgency=row.review_urgency,
            config=config,
        )
        if row.delta_score != expected_score:
            raise ValueError("delta_score must match inputs")
        expected_reasons = _row_reason_codes(
            evidence_completeness_delta=row.evidence_completeness_delta,
            source_confidence_delta=row.source_confidence_delta,
            contradiction_pressure_delta=row.contradiction_pressure_delta,
            liquidity_cost_pressure=row.liquidity_cost_pressure,
            review_urgency=row.review_urgency,
            delta_score=row.delta_score,
            config=config,
        )
        if row.reason_codes != expected_reasons:
            raise ValueError("reason_codes must match row inputs")
    if row.status != _row_status(row.reason_codes):
        raise ValueError("status must match reason_codes")
    if (
        REASON_DECISION_READINESS_DELTA_PASS in row.reason_codes
        and row.reason_codes != (REASON_DECISION_READINESS_DELTA_PASS,)
    ):
        raise ValueError("pass reason cannot be mixed with risk reasons")


def _validate_report(report: ResearchStrategyEvidenceChainDecisionDeltaReport) -> None:
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
    if report.average_delta_score != _average_delta(
        tuple(row.delta_score for row in report.rows),
    ):
        raise ValueError("average_delta_score must match rows")
    if report.min_delta_score != min((row.delta_score for row in report.rows), default=_ZERO):
        raise ValueError("min_delta_score must match rows")
    if report.max_delta_score != max((row.delta_score for row in report.rows), default=_ZERO):
        raise ValueError("max_delta_score must match rows")
    if report.max_liquidity_cost_pressure != max(
        (row.liquidity_cost_pressure for row in report.rows),
        default=_ZERO,
    ):
        raise ValueError("max_liquidity_cost_pressure must match rows")
    if report.max_review_urgency != max(
        (row.review_urgency for row in report.rows),
        default=_ZERO,
    ):
        raise ValueError("max_review_urgency must match rows")
    expected_counts = _reason_code_counts(report.rows)
    expected_codes = tuple(row.reason_code for row in expected_counts)
    if not report.rows:
        expected_counts = (
            ResearchStrategyEvidenceChainDecisionDeltaReasonCodeCount(
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
    inputs: Sequence[ResearchStrategyEvidenceChainDecisionDeltaInput],
) -> tuple[ResearchStrategyEvidenceChainDecisionDeltaInput, ...]:
    if type(inputs) not in (list, tuple):
        raise ValueError("inputs must be a list or tuple")
    normalized = tuple(inputs)
    seen: set[str] = set()
    for row in normalized:
        if type(row) is not ResearchStrategyEvidenceChainDecisionDeltaInput:
            raise ValueError(
                "inputs must contain ResearchStrategyEvidenceChainDecisionDeltaInput",
            )
        _require_hard_flags("input", row)
        digest = _private_ref_digest(row.chain_ref)
        if digest in seen:
            raise ValueError("inputs must be unique by chain digest")
        seen.add(digest)
    return normalized


def _normalize_rows(
    rows: tuple[ResearchStrategyEvidenceChainDecisionDeltaRow, ...],
) -> tuple[ResearchStrategyEvidenceChainDecisionDeltaRow, ...]:
    if type(rows) not in (list, tuple):
        raise ValueError("rows must be a list or tuple")
    normalized = tuple(rows)
    for row in normalized:
        if type(row) is not ResearchStrategyEvidenceChainDecisionDeltaRow:
            raise ValueError("rows must contain ResearchStrategyEvidenceChainDecisionDeltaRow")
        _require_hard_flags("row", row)
    if normalized != tuple(sorted(normalized, key=_row_sort_key)):
        raise ValueError("rows must use deterministic ordering")
    digests = tuple(row.chain_digest for row in normalized)
    if len(set(digests)) != len(digests):
        raise ValueError("rows must have unique chain digests")
    return normalized


def _normalize_reason_code_counts(
    counts: tuple[ResearchStrategyEvidenceChainDecisionDeltaReasonCodeCount, ...],
) -> tuple[ResearchStrategyEvidenceChainDecisionDeltaReasonCodeCount, ...]:
    if type(counts) not in (list, tuple):
        raise ValueError("reason_code_counts must be a list or tuple")
    normalized = tuple(counts)
    for row in normalized:
        if type(row) is not ResearchStrategyEvidenceChainDecisionDeltaReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "ResearchStrategyEvidenceChainDecisionDeltaReasonCodeCount",
            )
        _require_hard_flags("reason count", row)
    if normalized != tuple(
        sorted(normalized, key=lambda item: (-item.count, item.reason_code)),
    ):
        raise ValueError("reason_code_counts must use deterministic ordering")
    if len(set(row.reason_code for row in normalized)) != len(normalized):
        raise ValueError("reason_code_counts must not contain duplicates")
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
    if REASON_DECISION_READINESS_DELTA_PASS in value and value != (
        REASON_DECISION_READINESS_DELTA_PASS,
    ):
        raise ValueError("reason_codes cannot mix pass with risk reasons")
    return normalized


def _normalize_report_reason_codes(value: tuple[str, ...]) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ValueError("reason_codes must be a tuple")
    for reason_code in value:
        _require_reason_code("reason_codes", reason_code, _REPORT_REASON_CODE_SEQUENCE)
    if len(set(value)) != len(value):
        raise ValueError("reason_codes must be unique")
    return value


def _report_payload(report: ResearchStrategyEvidenceChainDecisionDeltaReport) -> dict[str, object]:
    payload = _report_payload_without_digest(
        config_version=report.config_version,
        status=report.status,
        row_count=report.row_count,
        pass_count=report.pass_count,
        watch_count=report.watch_count,
        block_count=report.block_count,
        average_delta_score=report.average_delta_score,
        min_delta_score=report.min_delta_score,
        max_delta_score=report.max_delta_score,
        max_liquidity_cost_pressure=report.max_liquidity_cost_pressure,
        max_review_urgency=report.max_review_urgency,
        rows=report.rows,
        reason_code_counts=report.reason_code_counts,
        reason_codes=report.reason_codes,
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


def _report_digest(report: ResearchStrategyEvidenceChainDecisionDeltaReport) -> str:
    return _report_digest_from_values(
        {
            "config_version": report.config_version,
            "status": report.status,
            "row_count": report.row_count,
            "pass_count": report.pass_count,
            "watch_count": report.watch_count,
            "block_count": report.block_count,
            "average_delta_score": report.average_delta_score,
            "min_delta_score": report.min_delta_score,
            "max_delta_score": report.max_delta_score,
            "max_liquidity_cost_pressure": report.max_liquidity_cost_pressure,
            "max_review_urgency": report.max_review_urgency,
            "rows": report.rows,
            "reason_code_counts": report.reason_code_counts,
            "reason_codes": report.reason_codes,
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
    unsigned = dict(payload)
    unsigned.pop(_DIGEST_FIELD, None)
    canonical = json.dumps(
        unsigned,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    )
    expected = sha256(canonical.encode("utf-8")).hexdigest()
    if digest != expected:
        raise ValueError("derived_validation_digest mismatch")


def _validate_public_payload_schema(payload: dict[str, object]) -> None:
    _require_exact_payload_keys(
        "report",
        payload,
        frozenset(
            field_info.name
            for field_info in fields(ResearchStrategyEvidenceChainDecisionDeltaReport)
        ),
    )
    rows = tuple(
        _row_from_public_payload(item, index)
        for index, item in enumerate(_require_payload_list("rows", payload["rows"]))
    )
    reason_code_counts = tuple(
        _reason_code_count_from_public_payload(item, index)
        for index, item in enumerate(
            _require_payload_list(
                "reason_code_counts",
                payload["reason_code_counts"],
            ),
        )
    )
    reconstructed = ResearchStrategyEvidenceChainDecisionDeltaReport(
        config_version=payload["config_version"],
        status=payload["status"],
        row_count=_decimal_from_public_payload("row_count", payload["row_count"]),
        pass_count=_decimal_from_public_payload("pass_count", payload["pass_count"]),
        watch_count=_decimal_from_public_payload("watch_count", payload["watch_count"]),
        block_count=_decimal_from_public_payload("block_count", payload["block_count"]),
        average_delta_score=_decimal_from_public_payload(
            "average_delta_score",
            payload["average_delta_score"],
        ),
        min_delta_score=_decimal_from_public_payload(
            "min_delta_score",
            payload["min_delta_score"],
        ),
        max_delta_score=_decimal_from_public_payload(
            "max_delta_score",
            payload["max_delta_score"],
        ),
        max_liquidity_cost_pressure=_decimal_from_public_payload(
            "max_liquidity_cost_pressure",
            payload["max_liquidity_cost_pressure"],
        ),
        max_review_urgency=_decimal_from_public_payload(
            "max_review_urgency",
            payload["max_review_urgency"],
        ),
        rows=rows,
        reason_code_counts=reason_code_counts,
        reason_codes=_reason_codes_from_public_payload(
            "reason_codes",
            payload["reason_codes"],
        ),
        derived_validation_digest=payload[_DIGEST_FIELD],
        paper_only=payload["paper_only"],
        report_only=payload["report_only"],
        readonly=payload["readonly"],
    )
    if _report_payload(reconstructed) != payload:
        raise ValueError("public payload must use canonical report values")


def _row_from_public_payload(
    value: object,
    index: int,
) -> ResearchStrategyEvidenceChainDecisionDeltaRow:
    label = f"rows[{index}]"
    if type(value) is not dict:
        raise ValueError(f"{label} must be an object")
    _require_exact_payload_keys(
        label,
        value,
        frozenset(
            field_info.name
            for field_info in fields(ResearchStrategyEvidenceChainDecisionDeltaRow)
        ),
    )
    return ResearchStrategyEvidenceChainDecisionDeltaRow(
        chain_digest=value["chain_digest"],
        evidence_completeness_delta=_decimal_from_public_payload(
            f"{label}.evidence_completeness_delta",
            value["evidence_completeness_delta"],
        ),
        source_confidence_delta=_decimal_from_public_payload(
            f"{label}.source_confidence_delta",
            value["source_confidence_delta"],
        ),
        contradiction_pressure_delta=_decimal_from_public_payload(
            f"{label}.contradiction_pressure_delta",
            value["contradiction_pressure_delta"],
        ),
        liquidity_cost_pressure=_decimal_from_public_payload(
            f"{label}.liquidity_cost_pressure",
            value["liquidity_cost_pressure"],
        ),
        review_urgency=_decimal_from_public_payload(
            f"{label}.review_urgency",
            value["review_urgency"],
        ),
        delta_score=_decimal_from_public_payload(
            f"{label}.delta_score",
            value["delta_score"],
        ),
        status=value["status"],
        reason_codes=_reason_codes_from_public_payload(
            f"{label}.reason_codes",
            value["reason_codes"],
        ),
        paper_only=value["paper_only"],
        report_only=value["report_only"],
        readonly=value["readonly"],
    )


def _reason_code_count_from_public_payload(
    value: object,
    index: int,
) -> ResearchStrategyEvidenceChainDecisionDeltaReasonCodeCount:
    label = f"reason_code_counts[{index}]"
    if type(value) is not dict:
        raise ValueError(f"{label} must be an object")
    _require_exact_payload_keys(
        label,
        value,
        frozenset(
            field_info.name
            for field_info in fields(
                ResearchStrategyEvidenceChainDecisionDeltaReasonCodeCount,
            )
        ),
    )
    return ResearchStrategyEvidenceChainDecisionDeltaReasonCodeCount(
        reason_code=value["reason_code"],
        count=_decimal_from_public_payload(f"{label}.count", value["count"]),
        row_ratio=_decimal_from_public_payload(
            f"{label}.row_ratio",
            value["row_ratio"],
        ),
        paper_only=value["paper_only"],
        report_only=value["report_only"],
        readonly=value["readonly"],
    )


def _require_exact_payload_keys(
    label: str,
    payload: dict[str, object],
    expected_keys: frozenset[str],
) -> None:
    actual_keys = frozenset(payload)
    if actual_keys - expected_keys:
        raise ValueError(f"unexpected public payload field in {label}")
    if expected_keys - actual_keys:
        raise ValueError(f"missing public payload field in {label}")


def _require_payload_list(label: str, value: object) -> list[object]:
    if type(value) is not list:
        raise ValueError(f"{label} must be a list")
    return value


def _reason_codes_from_public_payload(
    label: str,
    value: object,
) -> tuple[str, ...]:
    return tuple(_require_payload_list(label, value))


def _decimal_from_public_payload(field_name: str, value: object) -> Decimal:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a canonical Decimal string")
    try:
        parsed = Decimal(value)
        normalized = _quantize(parsed)
    except InvalidOperation as exc:
        raise ValueError(
            f"{field_name} must be a canonical Decimal string",
        ) from exc
    if not parsed.is_finite() or str(normalized) != value:
        raise ValueError(f"{field_name} must be a canonical Decimal string")
    return parsed


def _validate_payload_statuses(value: object) -> None:
    if isinstance(value, Mapping):
        for key, item in value.items():
            if key == "status":
                _require_status("status", item)
            _validate_payload_statuses(item)
        return
    if isinstance(value, list):
        for item in value:
            _validate_payload_statuses(item)


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
    raise ValueError("payload must contain only JSON values")


def _json_ready(value: object) -> object:
    if is_dataclass(value) and not isinstance(value, type):
        return _json_ready(asdict(value))
    if isinstance(value, Decimal):
        return str(_quantize(value))
    if type(value) is bool or value is None or type(value) is str:
        return value
    if isinstance(value, Mapping):
        return {str(key): _json_ready(item) for key, item in value.items()}
    if isinstance(value, (tuple, list)):
        return [_json_ready(item) for item in value]
    raise ValueError(f"unsupported public payload value type: {type(value).__name__}")


@dataclass(frozen=True)
class _PayloadFlags:
    value: Mapping[str, object]

    @property
    def paper_only(self) -> object:
        return self.value.get("paper_only")

    @property
    def report_only(self) -> object:
        return self.value.get("report_only")

    @property
    def readonly(self) -> object:
        return self.value.get("readonly")


def _require_exact_type(value: object, expected_type: type[object], label: str) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{label} must be exactly {expected_type.__name__}")


def _require_public_identifier(field_name: str, value: object) -> str:
    if type(value) is not str or not value:
        raise ValueError(f"{field_name} must be a non-empty string")
    if not _PUBLIC_IDENTIFIER_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a public identifier")
    lowered = value.casefold()
    if any(fragment in lowered for fragment in _UNSAFE_PUBLIC_FRAGMENTS):
        raise ValueError(f"{field_name} contains unsafe public text")
    return value


def _require_private_ref(field_name: str, value: object) -> str:
    if type(value) is not str or not value.strip():
        raise ValueError(f"{field_name} must be a non-empty string")
    return value


def _require_private_digest(field_name: str, value: object) -> str:
    if type(value) is not str or _PRIVATE_DIGEST_RE.fullmatch(value) is None:
        raise ValueError(f"{field_name} must be a private sha256 digest")
    return value


def _require_digest(field_name: str, value: object) -> str:
    if type(value) is not str or _DIGEST_RE.fullmatch(value) is None:
        raise ValueError(f"{field_name} must be a sha256 digest")
    return value


def _require_delta_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    normalized = _quantize(value)
    if normalized < _NEG_ONE or normalized > _ONE:
        raise ValueError(f"{field_name} must be between -1.000000 and 1.000000")
    return normalized


def _require_ratio_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    normalized = _quantize(value)
    if normalized < _ZERO or normalized > _ONE:
        raise ValueError(f"{field_name} must be between 0.000000 and 1.000000")
    return normalized


def _require_nonnegative_count_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    normalized = _quantize(value)
    if normalized < _ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{field_name} must be a whole Decimal")
    return normalized


def _require_status(field_name: str, value: object) -> str:
    if type(value) is not str or value not in _STATUSES:
        raise ValueError(f"{field_name} must be pass, watch, or block")
    return value


def _require_reason_code(
    field_name: str,
    value: object,
    allowed: tuple[str, ...],
) -> str:
    if type(value) is not str or value not in allowed:
        raise ValueError(f"{field_name} must be a supported reason code")
    return value


def _require_hard_flags(label: str, value: object) -> None:
    if getattr(value, "paper_only", None) is not True:
        raise ValueError(f"{label} paper_only must be True")
    if getattr(value, "report_only", None) is not True:
        raise ValueError(f"{label} report_only must be True")
    if getattr(value, "readonly", None) is not True:
        raise ValueError(f"{label} readonly must be True")


def _reject_unsafe_public_payload(
    label: str,
    value: object,
    *,
    allow_json_containers: bool = False,
) -> None:
    if is_dataclass(value) and not isinstance(value, type):
        for field in fields(value):
            _reject_unsafe_public_payload(
                f"{label}.{field.name}",
                getattr(value, field.name),
                allow_json_containers=True,
            )
        return
    if isinstance(value, Mapping):
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError(f"{label} public field names must be strings")
            lowered_key = key.casefold()
            if any(fragment in lowered_key for fragment in _UNSAFE_PUBLIC_FRAGMENTS):
                raise ValueError(f"{label} unsafe public field")
            _reject_unsafe_public_payload(
                f"{label}.{key}",
                item,
                allow_json_containers=True,
            )
        return
    if isinstance(value, (tuple, list)):
        if not allow_json_containers:
            raise ValueError(f"{label} unexpected public container")
        for item in value:
            _reject_unsafe_public_payload(label, item, allow_json_containers=True)
        return
    if type(value) is str:
        lowered_value = value.casefold()
        if any(fragment in lowered_value for fragment in _UNSAFE_PUBLIC_FRAGMENTS):
            raise ValueError(f"{label} unsafe public value")
        return
    if isinstance(value, Decimal) or type(value) is bool or value is None:
        return
    raise ValueError(f"{label} unsupported public payload value")


def _private_ref_digest(value: str) -> str:
    return "sha256:" + sha256(value.encode("utf-8")).hexdigest()


def _decimal_count(value: int) -> Decimal:
    return _quantize(Decimal(value))


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == _ZERO:
        return _ZERO
    return _quantize(numerator / denominator)


def _average_delta(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return _ZERO
    return _quantize(sum(values, _ZERO) / _decimal_count(len(values)))


def _clamp_delta(value: Decimal) -> Decimal:
    return _quantize(min(_ONE, max(_NEG_ONE, value)))


def _quantize(value: Decimal) -> Decimal:
    normalized = value.quantize(_QUANT, rounding=ROUND_HALF_UP)
    if normalized == _ZERO:
        return _ZERO
    return normalized


__all__ = (
    "DEFAULT_RESEARCH_STRATEGY_EVIDENCE_CHAIN_DECISION_DELTA_REPORT_VERSION",
    "ResearchStrategyEvidenceChainDecisionDeltaConfig",
    "ResearchStrategyEvidenceChainDecisionDeltaInput",
    "ResearchStrategyEvidenceChainDecisionDeltaReasonCodeCount",
    "ResearchStrategyEvidenceChainDecisionDeltaReport",
    "ResearchStrategyEvidenceChainDecisionDeltaRow",
    "build_research_strategy_evidence_chain_decision_delta_report",
    "research_strategy_evidence_chain_decision_delta_digest",
    "research_strategy_evidence_chain_decision_delta_public_payload",
)
