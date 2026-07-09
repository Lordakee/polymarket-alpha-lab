"""Report-only signal confidence and evidence decay bridge."""

from __future__ import annotations

from dataclasses import asdict, dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, InvalidOperation, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
from json import dumps
from typing import Any, Iterable


DEFAULT_RESEARCH_STRATEGY_SIGNAL_CONFIDENCE_DECAY_BRIDGE_REPORT_CONFIG_VERSION = (
    "research-strategy-signal-confidence-decay-bridge-report-v0"
)
RESEARCH_STRATEGY_SIGNAL_CONFIDENCE_DECAY_BRIDGE_STATUSES = ("pass", "watch", "block")

STATUS_PASS = "pass"
STATUS_WATCH = "watch"
STATUS_BLOCK = "block"

ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
RATIO_QUANTUM = Decimal("0.000001")
SECONDS_PER_DAY = Decimal("86400.000000")
MICROSECONDS_PER_SECOND = Decimal("1000000.000000")
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)

ROW_PASS_REASON = "signal_confidence_decay_bridge_pass"
SOURCE_AGE_BLOCK_REASON = "source_age_block"
SOURCE_AGE_WATCH_REASON = "source_age_watch"
AUTHORITY_BLOCK_REASON = "authority_block"
AUTHORITY_WATCH_REASON = "authority_watch"
CORROBORATION_BLOCK_REASON = "corroboration_block"
CORROBORATION_WATCH_REASON = "corroboration_watch"
CONTRADICTION_BLOCK_REASON = "contradiction_pressure_block"
CONTRADICTION_WATCH_REASON = "contradiction_pressure_watch"
MOVEMENT_BLOCK_REASON = "market_movement_block"
MOVEMENT_WATCH_REASON = "market_movement_watch"
COST_BLOCK_REASON = "cost_drag_block"
COST_WATCH_REASON = "cost_drag_watch"
LIQUIDITY_BLOCK_REASON = "liquidity_reliability_block"
LIQUIDITY_WATCH_REASON = "liquidity_reliability_watch"
AMBIGUITY_BLOCK_REASON = "resolution_ambiguity_block"
AMBIGUITY_WATCH_REASON = "resolution_ambiguity_watch"
BRIDGE_BLOCK_REASON = "bridge_confidence_block"
BRIDGE_WATCH_REASON = "bridge_confidence_watch"

REPORT_PASS_REASON = "signal_confidence_decay_bridge_pass"
REPORT_WATCH_REASON = "signal_confidence_decay_bridge_watch"
REPORT_BLOCK_REASON = "signal_confidence_decay_bridge_block"
REPORT_NO_INPUTS_REASON = "signal_confidence_decay_bridge_no_inputs"
SOURCE_AGE_REVIEW_REASON = "source_age_review"
AUTHORITY_REVIEW_REASON = "authority_review"
CORROBORATION_REVIEW_REASON = "corroboration_review"
CONTRADICTION_REVIEW_REASON = "contradiction_pressure_review"
MOVEMENT_REVIEW_REASON = "market_movement_review"
COST_REVIEW_REASON = "cost_drag_review"
LIQUIDITY_REVIEW_REASON = "liquidity_reliability_review"
AMBIGUITY_REVIEW_REASON = "resolution_ambiguity_review"
BRIDGE_REVIEW_REASON = "bridge_confidence_review"

ROW_REASON_CODES = (
    ROW_PASS_REASON,
    SOURCE_AGE_BLOCK_REASON,
    SOURCE_AGE_WATCH_REASON,
    AUTHORITY_BLOCK_REASON,
    AUTHORITY_WATCH_REASON,
    CORROBORATION_BLOCK_REASON,
    CORROBORATION_WATCH_REASON,
    CONTRADICTION_BLOCK_REASON,
    CONTRADICTION_WATCH_REASON,
    MOVEMENT_BLOCK_REASON,
    MOVEMENT_WATCH_REASON,
    COST_BLOCK_REASON,
    COST_WATCH_REASON,
    LIQUIDITY_BLOCK_REASON,
    LIQUIDITY_WATCH_REASON,
    AMBIGUITY_BLOCK_REASON,
    AMBIGUITY_WATCH_REASON,
    BRIDGE_BLOCK_REASON,
    BRIDGE_WATCH_REASON,
)
REPORT_REASON_CODES = (
    REPORT_PASS_REASON,
    REPORT_WATCH_REASON,
    REPORT_BLOCK_REASON,
    REPORT_NO_INPUTS_REASON,
    SOURCE_AGE_REVIEW_REASON,
    AUTHORITY_REVIEW_REASON,
    CORROBORATION_REVIEW_REASON,
    CONTRADICTION_REVIEW_REASON,
    MOVEMENT_REVIEW_REASON,
    COST_REVIEW_REASON,
    LIQUIDITY_REVIEW_REASON,
    AMBIGUITY_REVIEW_REASON,
    BRIDGE_REVIEW_REASON,
)
ALL_REASON_CODES = frozenset((*ROW_REASON_CODES, *REPORT_REASON_CODES))
PUBLIC_REPORT_PAYLOAD_KEYS = frozenset(
    (
        "generated_at",
        "config_version",
        "source_row_count",
        "pass_count",
        "watch_count",
        "block_count",
        "mean_source_age_pressure",
        "mean_evidence_decay_score",
        "mean_confidence_decay_bridge_score",
        "lowest_confidence_decay_bridge_score",
        "highest_evidence_decay_score",
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
PUBLIC_ROW_PAYLOAD_KEYS = frozenset(
    (
        "aggregate_row_number",
        "aggregate_signal_hash",
        "source_age_seconds",
        "source_age_pressure",
        "freshness_score",
        "base_signal_confidence_score",
        "source_authority_score",
        "corroboration_score",
        "contradiction_pressure",
        "market_movement_pressure",
        "cost_drag_score",
        "liquidity_reliability_score",
        "resolution_ambiguity_score",
        "evidence_decay_score",
        "confidence_decay_bridge_score",
        "status",
        "reason_codes",
        "derived_validation_digest",
        "paper_only",
        "report_only",
        "readonly",
    ),
)

UNSAFE_KEY_FRAGMENTS = (
    "raw",
    "cand" + "idate" + "_" + "id",
    "cand" + "idate" + "-" + "id",
    "market" + "_" + "id",
    "market" + "-" + "id",
    "market" + "_" + "slug",
    "market" + "-" + "slug",
    "q" + "uestion",
    "source" + "_" + "url",
    "source" + "-" + "url",
    "source" + "_" + "text",
    "source" + "-" + "text",
    "d" + "sn",
    "ta" + "ble",
    "to" + "ken",
    "wal" + "let",
    "or" + "der",
    "tr" + "ade",
    "li" + "ve",
    "pos" + "ition",
    "siz" + "ing",
    "reco" + "mmend",
    "secret",
    "credential",
    "api" + "_" + "key",
)
UNSAFE_VALUE_FRAGMENTS = (
    "http://",
    "https://",
    "://",
    "postgres://",
    "mysql://",
    "jdbc:",
    "cand" + "idate",
    "market-alpha",
    "market" + "_" + "id",
    "market" + "_" + "slug",
    "q" + "uestion",
    "source" + "_" + "url",
    "source" + "_" + "text",
    "d" + "sn",
    "ta" + "ble=",
    "db.",
    "to" + "ken",
    "wal" + "let",
    "or" + "der",
    "tr" + "ade",
    "li" + "ve",
    "pos" + "ition",
    "siz" + "ing",
    "reco" + "mmend",
    "secret",
    "credential",
    "api" + "_" + "key",
)


@dataclass(frozen=True)
class ResearchStrategySignalConfidenceDecayBridgeConfig:
    config_version: str
    fresh_age_seconds: Decimal
    stale_age_seconds: Decimal
    min_pass_freshness_score: Decimal
    min_watch_freshness_score: Decimal
    min_pass_authority_score: Decimal
    min_watch_authority_score: Decimal
    min_pass_corroboration_score: Decimal
    min_watch_corroboration_score: Decimal
    max_pass_contradiction_pressure: Decimal
    max_watch_contradiction_pressure: Decimal
    max_pass_market_movement_pressure: Decimal
    max_watch_market_movement_pressure: Decimal
    max_pass_cost_drag_score: Decimal
    max_watch_cost_drag_score: Decimal
    min_pass_liquidity_reliability_score: Decimal
    min_watch_liquidity_reliability_score: Decimal
    max_pass_resolution_ambiguity_score: Decimal
    max_watch_resolution_ambiguity_score: Decimal
    min_pass_bridge_confidence_score: Decimal
    min_watch_bridge_confidence_score: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchStrategySignalConfidenceDecayBridgeConfig,
            "config",
        )
        _require_canonical_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_STRATEGY_SIGNAL_CONFIDENCE_DECAY_BRIDGE_REPORT_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in ("fresh_age_seconds", "stale_age_seconds"):
            object.__setattr__(
                self,
                field_name,
                _normalize_positive_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "min_pass_freshness_score",
            "min_watch_freshness_score",
            "min_pass_authority_score",
            "min_watch_authority_score",
            "min_pass_corroboration_score",
            "min_watch_corroboration_score",
            "max_pass_contradiction_pressure",
            "max_watch_contradiction_pressure",
            "max_pass_market_movement_pressure",
            "max_watch_market_movement_pressure",
            "max_pass_cost_drag_score",
            "max_watch_cost_drag_score",
            "min_pass_liquidity_reliability_score",
            "min_watch_liquidity_reliability_score",
            "max_pass_resolution_ambiguity_score",
            "max_watch_resolution_ambiguity_score",
            "min_pass_bridge_confidence_score",
            "min_watch_bridge_confidence_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        _require_age_threshold_pair(
            "source_age threshold",
            self.fresh_age_seconds,
            self.stale_age_seconds,
        )
        _require_min_threshold_pair(
            "freshness threshold",
            self.min_watch_freshness_score,
            self.min_pass_freshness_score,
        )
        _require_min_threshold_pair(
            "authority threshold",
            self.min_watch_authority_score,
            self.min_pass_authority_score,
        )
        _require_min_threshold_pair(
            "corroboration threshold",
            self.min_watch_corroboration_score,
            self.min_pass_corroboration_score,
        )
        _require_max_threshold_pair(
            "contradiction threshold",
            self.max_pass_contradiction_pressure,
            self.max_watch_contradiction_pressure,
        )
        _require_max_threshold_pair(
            "movement threshold",
            self.max_pass_market_movement_pressure,
            self.max_watch_market_movement_pressure,
        )
        _require_max_threshold_pair(
            "cost threshold",
            self.max_pass_cost_drag_score,
            self.max_watch_cost_drag_score,
        )
        _require_min_threshold_pair(
            "liquidity threshold",
            self.min_watch_liquidity_reliability_score,
            self.min_pass_liquidity_reliability_score,
        )
        _require_max_threshold_pair(
            "ambiguity threshold",
            self.max_pass_resolution_ambiguity_score,
            self.max_watch_resolution_ambiguity_score,
        )
        _require_min_threshold_pair(
            "bridge threshold",
            self.min_watch_bridge_confidence_score,
            self.min_pass_bridge_confidence_score,
        )
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class ResearchStrategySignalConfidenceDecayBridgeInput:
    signal_ref: str
    observed_at: datetime
    base_signal_confidence_score: Decimal
    source_authority_score: Decimal
    corroboration_score: Decimal
    contradiction_pressure: Decimal
    market_movement_pressure: Decimal
    cost_drag_score: Decimal
    liquidity_reliability_score: Decimal
    resolution_ambiguity_score: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchStrategySignalConfidenceDecayBridgeInput,
            "input",
        )
        _require_canonical_string("signal_ref", self.signal_ref)
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in (
            "base_signal_confidence_score",
            "source_authority_score",
            "corroboration_score",
            "contradiction_pressure",
            "market_movement_pressure",
            "cost_drag_score",
            "liquidity_reliability_score",
            "resolution_ambiguity_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        _require_hard_flags("input", self)


@dataclass(frozen=True)
class ResearchStrategySignalConfidenceDecayBridgeRow:
    aggregate_row_number: Decimal
    aggregate_signal_hash: str
    source_age_seconds: Decimal
    source_age_pressure: Decimal
    freshness_score: Decimal
    base_signal_confidence_score: Decimal
    source_authority_score: Decimal
    corroboration_score: Decimal
    contradiction_pressure: Decimal
    market_movement_pressure: Decimal
    cost_drag_score: Decimal
    liquidity_reliability_score: Decimal
    resolution_ambiguity_score: Decimal
    evidence_decay_score: Decimal
    confidence_decay_bridge_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchStrategySignalConfidenceDecayBridgeRow,
            "row",
        )
        object.__setattr__(
            self,
            "aggregate_row_number",
            _normalize_positive_count(
                "aggregate_row_number",
                self.aggregate_row_number,
            ),
        )
        _require_sha256_digest("aggregate_signal_hash", self.aggregate_signal_hash)
        object.__setattr__(
            self,
            "source_age_seconds",
            _normalize_nonnegative_decimal("source_age_seconds", self.source_age_seconds),
        )
        for field_name in (
            "source_age_pressure",
            "freshness_score",
            "base_signal_confidence_score",
            "source_authority_score",
            "corroboration_score",
            "contradiction_pressure",
            "market_movement_pressure",
            "cost_drag_score",
            "liquidity_reliability_score",
            "resolution_ambiguity_score",
            "evidence_decay_score",
            "confidence_decay_bridge_score",
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
            _normalize_reason_codes("reason_codes", self.reason_codes, ROW_REASON_CODES),
        )
        _require_hard_flags("row", self)
        _apply_or_verify_digest(self)
        _validate_row_consistency(self)


@dataclass(frozen=True)
class ResearchStrategySignalConfidenceDecayBridgeReport:
    generated_at: datetime
    config_version: str
    source_row_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    mean_source_age_pressure: Decimal
    mean_evidence_decay_score: Decimal
    mean_confidence_decay_bridge_score: Decimal
    lowest_confidence_decay_bridge_score: Decimal
    highest_evidence_decay_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    reason_code_counts: tuple[tuple[str, Decimal], ...]
    rows: tuple[ResearchStrategySignalConfidenceDecayBridgeRow, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchStrategySignalConfidenceDecayBridgeReport,
            "report",
        )
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_STRATEGY_SIGNAL_CONFIDENCE_DECAY_BRIDGE_REPORT_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in ("source_row_count", "pass_count", "watch_count", "block_count"):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_count(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "mean_source_age_pressure",
            "mean_evidence_decay_score",
            "mean_confidence_decay_bridge_score",
            "lowest_confidence_decay_bridge_score",
            "highest_evidence_decay_score",
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


def build_research_strategy_signal_confidence_decay_bridge_report(
    inputs: Iterable[ResearchStrategySignalConfidenceDecayBridgeInput],
    *,
    config: ResearchStrategySignalConfidenceDecayBridgeConfig,
    generated_at: datetime,
) -> ResearchStrategySignalConfidenceDecayBridgeReport:
    if type(config) is not ResearchStrategySignalConfidenceDecayBridgeConfig:
        raise ValueError(
            "config must be a ResearchStrategySignalConfidenceDecayBridgeConfig",
        )
    _require_hard_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    normalized_inputs = _normalize_inputs(inputs)
    prepared_rows = tuple(
        sorted(
            (
                _prepare_row(value, config=config, generated_at=generated_at_utc)
                for value in normalized_inputs
            ),
            key=_prepared_row_sort_key,
        ),
    )
    rows = tuple(
        _row_from_prepared(value, aggregate_row_number=_count(index))
        for index, value in enumerate(prepared_rows, start=1)
    )
    return ResearchStrategySignalConfidenceDecayBridgeReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        source_row_count=_count(len(rows)),
        pass_count=_status_count(rows, STATUS_PASS),
        watch_count=_status_count(rows, STATUS_WATCH),
        block_count=_status_count(rows, STATUS_BLOCK),
        mean_source_age_pressure=_mean(tuple(row.source_age_pressure for row in rows)),
        mean_evidence_decay_score=_mean(tuple(row.evidence_decay_score for row in rows)),
        mean_confidence_decay_bridge_score=_mean(
            tuple(row.confidence_decay_bridge_score for row in rows),
        ),
        lowest_confidence_decay_bridge_score=min(
            (row.confidence_decay_bridge_score for row in rows),
            default=ZERO,
        ),
        highest_evidence_decay_score=max(
            (row.evidence_decay_score for row in rows),
            default=ZERO,
        ),
        status=_report_status(rows),
        reason_codes=_report_reason_codes(rows),
        reason_code_counts=_reason_code_counts_from_rows(rows),
        rows=rows,
    )


def research_strategy_signal_confidence_decay_bridge_report_payload(
    report: ResearchStrategySignalConfidenceDecayBridgeReport | dict[str, Any],
) -> dict[str, Any]:
    if type(report) is ResearchStrategySignalConfidenceDecayBridgeReport:
        _require_hard_flags("report", report)
        _verify_report_integrity(report)
        _reject_unsafe_public_payload("report", report)
        payload = _json_ready(asdict(report))
    elif type(report) is dict:
        _require_hard_flags("payload", _DictFlags(report))
        _reject_unsafe_public_payload("payload", report)
        _validate_public_payload_values("payload", report)
        _verify_public_payload_integrity(report)
        validated_report = _report_from_public_payload(report)
        payload = _json_ready(validated_report)
        if payload != report:
            raise ValueError("payload must use canonical public encoding")
    else:
        raise ValueError(
            "report must be a ResearchStrategySignalConfidenceDecayBridgeReport",
        )
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    _require_hard_flags("payload", _DictFlags(payload))
    _reject_unsafe_public_payload("payload", payload)
    return payload


__all__ = (
    "DEFAULT_RESEARCH_STRATEGY_SIGNAL_CONFIDENCE_DECAY_BRIDGE_REPORT_CONFIG_VERSION",
    "RESEARCH_STRATEGY_SIGNAL_CONFIDENCE_DECAY_BRIDGE_STATUSES",
    "ResearchStrategySignalConfidenceDecayBridgeConfig",
    "ResearchStrategySignalConfidenceDecayBridgeInput",
    "ResearchStrategySignalConfidenceDecayBridgeRow",
    "ResearchStrategySignalConfidenceDecayBridgeReport",
    "build_research_strategy_signal_confidence_decay_bridge_report",
    "research_strategy_signal_confidence_decay_bridge_report_payload",
)


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


@dataclass(frozen=True)
class _PreparedRow:
    aggregate_signal_hash: str
    source_age_seconds: Decimal
    source_age_pressure: Decimal
    freshness_score: Decimal
    base_signal_confidence_score: Decimal
    source_authority_score: Decimal
    corroboration_score: Decimal
    contradiction_pressure: Decimal
    market_movement_pressure: Decimal
    cost_drag_score: Decimal
    liquidity_reliability_score: Decimal
    resolution_ambiguity_score: Decimal
    evidence_decay_score: Decimal
    confidence_decay_bridge_score: Decimal
    status: str
    reason_codes: tuple[str, ...]


def _prepare_row(
    value: ResearchStrategySignalConfidenceDecayBridgeInput,
    *,
    config: ResearchStrategySignalConfidenceDecayBridgeConfig,
    generated_at: datetime,
) -> _PreparedRow:
    if value.observed_at > generated_at:
        raise ValueError("observed_at must not be after generated_at")
    source_age = _age_seconds(generated_at, value.observed_at)
    source_age_pressure = _age_pressure(
        source_age,
        fresh_age=config.fresh_age_seconds,
        stale_age=config.stale_age_seconds,
    )
    freshness_score = _quantize(ONE - source_age_pressure)
    evidence_decay_score = _evidence_decay_score(
        source_age_pressure=source_age_pressure,
        source_authority_score=value.source_authority_score,
        corroboration_score=value.corroboration_score,
        contradiction_pressure=value.contradiction_pressure,
        market_movement_pressure=value.market_movement_pressure,
        cost_drag_score=value.cost_drag_score,
        liquidity_reliability_score=value.liquidity_reliability_score,
        resolution_ambiguity_score=value.resolution_ambiguity_score,
    )
    bridge_score = _quantize(
        value.base_signal_confidence_score * (ONE - evidence_decay_score),
    )
    reason_codes = _row_reason_codes(
        freshness_score=freshness_score,
        source_authority_score=value.source_authority_score,
        corroboration_score=value.corroboration_score,
        contradiction_pressure=value.contradiction_pressure,
        market_movement_pressure=value.market_movement_pressure,
        cost_drag_score=value.cost_drag_score,
        liquidity_reliability_score=value.liquidity_reliability_score,
        resolution_ambiguity_score=value.resolution_ambiguity_score,
        confidence_decay_bridge_score=bridge_score,
        config=config,
    )
    status = _row_status(reason_codes)
    return _PreparedRow(
        aggregate_signal_hash=_aggregate_signal_hash(value.signal_ref),
        source_age_seconds=source_age,
        source_age_pressure=source_age_pressure,
        freshness_score=freshness_score,
        base_signal_confidence_score=value.base_signal_confidence_score,
        source_authority_score=value.source_authority_score,
        corroboration_score=value.corroboration_score,
        contradiction_pressure=value.contradiction_pressure,
        market_movement_pressure=value.market_movement_pressure,
        cost_drag_score=value.cost_drag_score,
        liquidity_reliability_score=value.liquidity_reliability_score,
        resolution_ambiguity_score=value.resolution_ambiguity_score,
        evidence_decay_score=evidence_decay_score,
        confidence_decay_bridge_score=bridge_score,
        status=status,
        reason_codes=reason_codes,
    )


def _row_from_prepared(
    value: _PreparedRow,
    *,
    aggregate_row_number: Decimal,
) -> ResearchStrategySignalConfidenceDecayBridgeRow:
    return ResearchStrategySignalConfidenceDecayBridgeRow(
        aggregate_row_number=aggregate_row_number,
        aggregate_signal_hash=value.aggregate_signal_hash,
        source_age_seconds=value.source_age_seconds,
        source_age_pressure=value.source_age_pressure,
        freshness_score=value.freshness_score,
        base_signal_confidence_score=value.base_signal_confidence_score,
        source_authority_score=value.source_authority_score,
        corroboration_score=value.corroboration_score,
        contradiction_pressure=value.contradiction_pressure,
        market_movement_pressure=value.market_movement_pressure,
        cost_drag_score=value.cost_drag_score,
        liquidity_reliability_score=value.liquidity_reliability_score,
        resolution_ambiguity_score=value.resolution_ambiguity_score,
        evidence_decay_score=value.evidence_decay_score,
        confidence_decay_bridge_score=value.confidence_decay_bridge_score,
        status=value.status,
        reason_codes=value.reason_codes,
    )


def _row_reason_codes(
    *,
    freshness_score: Decimal,
    source_authority_score: Decimal,
    corroboration_score: Decimal,
    contradiction_pressure: Decimal,
    market_movement_pressure: Decimal,
    cost_drag_score: Decimal,
    liquidity_reliability_score: Decimal,
    resolution_ambiguity_score: Decimal,
    confidence_decay_bridge_score: Decimal,
    config: ResearchStrategySignalConfidenceDecayBridgeConfig,
) -> tuple[str, ...]:
    codes: list[str] = []
    if freshness_score < config.min_watch_freshness_score:
        codes.append(SOURCE_AGE_BLOCK_REASON)
    elif freshness_score < config.min_pass_freshness_score:
        codes.append(SOURCE_AGE_WATCH_REASON)
    if source_authority_score < config.min_watch_authority_score:
        codes.append(AUTHORITY_BLOCK_REASON)
    elif source_authority_score < config.min_pass_authority_score:
        codes.append(AUTHORITY_WATCH_REASON)
    if corroboration_score < config.min_watch_corroboration_score:
        codes.append(CORROBORATION_BLOCK_REASON)
    elif corroboration_score < config.min_pass_corroboration_score:
        codes.append(CORROBORATION_WATCH_REASON)
    if contradiction_pressure > config.max_watch_contradiction_pressure:
        codes.append(CONTRADICTION_BLOCK_REASON)
    elif contradiction_pressure > config.max_pass_contradiction_pressure:
        codes.append(CONTRADICTION_WATCH_REASON)
    if market_movement_pressure > config.max_watch_market_movement_pressure:
        codes.append(MOVEMENT_BLOCK_REASON)
    elif market_movement_pressure > config.max_pass_market_movement_pressure:
        codes.append(MOVEMENT_WATCH_REASON)
    if cost_drag_score > config.max_watch_cost_drag_score:
        codes.append(COST_BLOCK_REASON)
    elif cost_drag_score > config.max_pass_cost_drag_score:
        codes.append(COST_WATCH_REASON)
    if liquidity_reliability_score < config.min_watch_liquidity_reliability_score:
        codes.append(LIQUIDITY_BLOCK_REASON)
    elif liquidity_reliability_score < config.min_pass_liquidity_reliability_score:
        codes.append(LIQUIDITY_WATCH_REASON)
    if resolution_ambiguity_score > config.max_watch_resolution_ambiguity_score:
        codes.append(AMBIGUITY_BLOCK_REASON)
    elif resolution_ambiguity_score > config.max_pass_resolution_ambiguity_score:
        codes.append(AMBIGUITY_WATCH_REASON)
    if confidence_decay_bridge_score < config.min_watch_bridge_confidence_score:
        codes.append(BRIDGE_BLOCK_REASON)
    elif confidence_decay_bridge_score < config.min_pass_bridge_confidence_score:
        codes.append(BRIDGE_WATCH_REASON)
    if not codes:
        return (ROW_PASS_REASON,)
    return _normalize_reason_codes("reason_codes", tuple(sorted(codes)), ROW_REASON_CODES)


def _row_status(reason_codes: tuple[str, ...]) -> str:
    if any(reason_code.endswith("_block") for reason_code in reason_codes):
        return STATUS_BLOCK
    if reason_codes != (ROW_PASS_REASON,):
        return STATUS_WATCH
    return STATUS_PASS


def _report_status(
    rows: tuple[ResearchStrategySignalConfidenceDecayBridgeRow, ...],
) -> str:
    if not rows:
        return STATUS_BLOCK
    if any(row.status == STATUS_BLOCK for row in rows):
        return STATUS_BLOCK
    if any(row.status == STATUS_WATCH for row in rows):
        return STATUS_WATCH
    return STATUS_PASS


def _report_reason_codes(
    rows: tuple[ResearchStrategySignalConfidenceDecayBridgeRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return (REPORT_BLOCK_REASON, REPORT_NO_INPUTS_REASON)
    status = _report_status(rows)
    codes: list[str] = [
        {
            STATUS_PASS: REPORT_PASS_REASON,
            STATUS_WATCH: REPORT_WATCH_REASON,
            STATUS_BLOCK: REPORT_BLOCK_REASON,
        }[status],
    ]
    review_pairs = (
        ((SOURCE_AGE_BLOCK_REASON, SOURCE_AGE_WATCH_REASON), SOURCE_AGE_REVIEW_REASON),
        ((AUTHORITY_BLOCK_REASON, AUTHORITY_WATCH_REASON), AUTHORITY_REVIEW_REASON),
        (
            (CORROBORATION_BLOCK_REASON, CORROBORATION_WATCH_REASON),
            CORROBORATION_REVIEW_REASON,
        ),
        (
            (CONTRADICTION_BLOCK_REASON, CONTRADICTION_WATCH_REASON),
            CONTRADICTION_REVIEW_REASON,
        ),
        ((MOVEMENT_BLOCK_REASON, MOVEMENT_WATCH_REASON), MOVEMENT_REVIEW_REASON),
        ((COST_BLOCK_REASON, COST_WATCH_REASON), COST_REVIEW_REASON),
        ((LIQUIDITY_BLOCK_REASON, LIQUIDITY_WATCH_REASON), LIQUIDITY_REVIEW_REASON),
        ((AMBIGUITY_BLOCK_REASON, AMBIGUITY_WATCH_REASON), AMBIGUITY_REVIEW_REASON),
        ((BRIDGE_BLOCK_REASON, BRIDGE_WATCH_REASON), BRIDGE_REVIEW_REASON),
    )
    for row_reasons, report_reason in review_pairs:
        if any(any(reason in row.reason_codes for reason in row_reasons) for row in rows):
            codes.append(report_reason)
    return _normalize_reason_codes("reason_codes", tuple(codes), REPORT_REASON_CODES)


def _prepared_row_sort_key(value: _PreparedRow) -> tuple[int, Decimal, str]:
    return (
        {STATUS_BLOCK: 0, STATUS_WATCH: 1, STATUS_PASS: 2}[value.status],
        -value.evidence_decay_score,
        value.aggregate_signal_hash,
    )


def _normalize_inputs(
    value: Iterable[ResearchStrategySignalConfidenceDecayBridgeInput],
) -> tuple[ResearchStrategySignalConfidenceDecayBridgeInput, ...]:
    if isinstance(value, (str, bytes, dict)):
        raise ValueError("inputs must be an iterable of input rows")
    rows = tuple(value)
    seen: set[str] = set()
    for row in rows:
        if type(row) is not ResearchStrategySignalConfidenceDecayBridgeInput:
            raise ValueError(
                "inputs must contain ResearchStrategySignalConfidenceDecayBridgeInput",
            )
        _require_hard_flags("input", row)
        if row.signal_ref in seen:
            raise ValueError("duplicate signal_ref values are not allowed")
        seen.add(row.signal_ref)
    return rows


def _normalize_rows(
    value: object,
) -> tuple[ResearchStrategySignalConfidenceDecayBridgeRow, ...]:
    if type(value) not in (tuple, list):
        raise ValueError("rows must be a tuple or list")
    rows = tuple(value)
    seen_numbers: set[Decimal] = set()
    seen_hashes: set[str] = set()
    for row in rows:
        if type(row) is not ResearchStrategySignalConfidenceDecayBridgeRow:
            raise ValueError(
                "rows must contain ResearchStrategySignalConfidenceDecayBridgeRow",
            )
        _require_hard_flags("row", row)
        if row.aggregate_row_number in seen_numbers:
            raise ValueError("aggregate_row_number values must be unique")
        if row.aggregate_signal_hash in seen_hashes:
            raise ValueError("aggregate_signal_hash values must be unique")
        seen_numbers.add(row.aggregate_row_number)
        seen_hashes.add(row.aggregate_signal_hash)
    return rows


def _normalize_reason_code_counts(
    value: object,
) -> tuple[tuple[str, Decimal], ...]:
    if type(value) not in (tuple, list):
        raise ValueError("reason_code_counts must be a tuple or list")
    rows = tuple(value)
    normalized: list[tuple[str, Decimal]] = []
    seen: set[str] = set()
    for item in rows:
        if type(item) not in (tuple, list) or len(item) != 2:
            raise ValueError("reason_code_counts must contain reason/count pairs")
        reason_code = item[0]
        count = _normalize_nonnegative_count("reason_code_count", item[1])
        _require_reason_code("reason_code", reason_code)
        if reason_code in seen:
            raise ValueError("reason_code_counts reason_code values must be unique")
        seen.add(reason_code)
        normalized.append((reason_code, count))
    result = tuple(sorted(normalized, key=lambda item: item[0]))
    if tuple(normalized) != result:
        raise ValueError("reason_code_counts must use deterministic sorting")
    return result


def _reason_code_counts_from_rows(
    rows: tuple[ResearchStrategySignalConfidenceDecayBridgeRow, ...],
) -> tuple[tuple[str, Decimal], ...]:
    counts: dict[str, Decimal] = {}
    for row in rows:
        for reason_code in row.reason_codes:
            counts[reason_code] = counts.get(reason_code, ZERO) + ONE
    if not rows:
        counts[REPORT_NO_INPUTS_REASON] = ONE
    return tuple((reason, count) for reason, count in sorted(counts.items()))


def _status_count(
    rows: tuple[ResearchStrategySignalConfidenceDecayBridgeRow, ...],
    status: str,
) -> Decimal:
    return _count(sum(1 for row in rows if row.status == status))


def _validate_row_consistency(
    row: ResearchStrategySignalConfidenceDecayBridgeRow,
) -> None:
    if row.freshness_score != _quantize(ONE - row.source_age_pressure):
        raise ValueError("freshness_score must match source_age_pressure")
    expected_decay = _evidence_decay_score(
        source_age_pressure=row.source_age_pressure,
        source_authority_score=row.source_authority_score,
        corroboration_score=row.corroboration_score,
        contradiction_pressure=row.contradiction_pressure,
        market_movement_pressure=row.market_movement_pressure,
        cost_drag_score=row.cost_drag_score,
        liquidity_reliability_score=row.liquidity_reliability_score,
        resolution_ambiguity_score=row.resolution_ambiguity_score,
    )
    if row.evidence_decay_score != expected_decay:
        raise ValueError("evidence_decay_score must match row components")
    expected_bridge = _quantize(
        row.base_signal_confidence_score * (ONE - row.evidence_decay_score),
    )
    if row.confidence_decay_bridge_score != expected_bridge:
        raise ValueError("confidence_decay_bridge_score must match row components")
    if row.status != _row_status(row.reason_codes):
        raise ValueError("status must match reason_codes")


def _validate_report_consistency(
    report: ResearchStrategySignalConfidenceDecayBridgeReport,
) -> None:
    expected_values = {
        "source_row_count": _count(len(report.rows)),
        "pass_count": _status_count(report.rows, STATUS_PASS),
        "watch_count": _status_count(report.rows, STATUS_WATCH),
        "block_count": _status_count(report.rows, STATUS_BLOCK),
        "mean_source_age_pressure": _mean(
            tuple(row.source_age_pressure for row in report.rows),
        ),
        "mean_evidence_decay_score": _mean(
            tuple(row.evidence_decay_score for row in report.rows),
        ),
        "mean_confidence_decay_bridge_score": _mean(
            tuple(row.confidence_decay_bridge_score for row in report.rows),
        ),
        "lowest_confidence_decay_bridge_score": min(
            (row.confidence_decay_bridge_score for row in report.rows),
            default=ZERO,
        ),
        "highest_evidence_decay_score": max(
            (row.evidence_decay_score for row in report.rows),
            default=ZERO,
        ),
    }
    for field_name, expected_value in expected_values.items():
        if getattr(report, field_name) != expected_value:
            raise ValueError(f"{field_name} must match rows")
    if report.status != _report_status(report.rows):
        raise ValueError("status must match rows")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")
    if report.reason_code_counts != _reason_code_counts_from_rows(report.rows):
        raise ValueError("reason_code_counts must match rows")


def _evidence_decay_score(
    *,
    source_age_pressure: Decimal,
    source_authority_score: Decimal,
    corroboration_score: Decimal,
    contradiction_pressure: Decimal,
    market_movement_pressure: Decimal,
    cost_drag_score: Decimal,
    liquidity_reliability_score: Decimal,
    resolution_ambiguity_score: Decimal,
) -> Decimal:
    return _mean(
        (
            source_age_pressure,
            ONE - source_authority_score,
            ONE - corroboration_score,
            contradiction_pressure,
            market_movement_pressure,
            cost_drag_score,
            ONE - liquidity_reliability_score,
            resolution_ambiguity_score,
        ),
    )


def _age_pressure(
    age_seconds: Decimal,
    *,
    fresh_age: Decimal,
    stale_age: Decimal,
) -> Decimal:
    if age_seconds <= fresh_age:
        return ZERO
    if age_seconds >= stale_age:
        return ONE
    return _quantize((age_seconds - fresh_age) / (stale_age - fresh_age))


def _age_seconds(generated_at: datetime, observed_at: datetime) -> Decimal:
    generated = _as_utc("generated_at", generated_at)
    observed = _as_utc("observed_at", observed_at)
    if observed > generated:
        raise ValueError("observed_at must not be after generated_at")
    delta = generated - observed
    return _quantize(
        Decimal(delta.days) * SECONDS_PER_DAY
        + Decimal(delta.seconds)
        + (Decimal(delta.microseconds) / MICROSECONDS_PER_SECOND),
    )


def _aggregate_signal_hash(value: str) -> str:
    return sha256(value.encode("utf-8")).hexdigest()


def _count(value: int) -> Decimal:
    return _quantize(Decimal(value))


def _mean(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return ZERO
    return _quantize(sum(values, ZERO) / _count(len(values)))


def _normalize_reason_codes(
    name: str,
    value: object,
    allowed: tuple[str, ...],
) -> tuple[str, ...]:
    if type(value) not in (tuple, list):
        raise ValueError(f"{name} must be a tuple or list")
    codes = tuple(value)
    if not codes:
        raise ValueError(f"{name} must not be empty")
    seen: set[str] = set()
    for code in codes:
        _require_reason_code("reason_code", code)
        if code not in allowed:
            raise ValueError(f"{name} contains an unsupported reason code")
        if code in seen:
            raise ValueError(f"{name} must be unique")
        seen.add(code)
    return codes


def _apply_or_verify_digest(value: object) -> None:
    current_digest = getattr(value, "derived_validation_digest")
    if current_digest == "":
        object.__setattr__(value, "derived_validation_digest", _digest_for_value(value))
        return
    _require_sha256_digest("derived_validation_digest", current_digest)
    if current_digest != _digest_for_value(value):
        raise ValueError("derived_validation_digest does not match payload")


def _digest_for_value(value: object) -> str:
    ready = _json_ready_without_digest(value)
    _reject_unsafe_public_payload("digest payload", ready)
    canonical_payload = dumps(
        ready,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    )
    return sha256(canonical_payload.encode("utf-8")).hexdigest()


def _json_ready_without_digest(value: object) -> dict[str, Any]:
    if not is_dataclass(value) or isinstance(value, type):
        raise ValueError("digest value must be a dataclass instance")
    ready = _json_ready(asdict(value))
    if type(ready) is not dict:
        raise ValueError("digest payload must be a JSON object")
    ready.pop("derived_validation_digest", None)
    return ready


def _verify_report_integrity(
    report: ResearchStrategySignalConfidenceDecayBridgeReport,
) -> None:
    _require_sha256_digest("derived_validation_digest", report.derived_validation_digest)
    if report.derived_validation_digest != _digest_for_value(report):
        raise ValueError("derived_validation_digest does not match payload")
    for row in report.rows:
        _require_sha256_digest("derived_validation_digest", row.derived_validation_digest)
        if row.derived_validation_digest != _digest_for_value(row):
            raise ValueError("derived_validation_digest does not match row payload")


def _verify_public_payload_integrity(payload: dict[str, Any]) -> None:
    expected_digest = payload.get("derived_validation_digest")
    if type(expected_digest) is not str:
        raise ValueError("derived_validation_digest must be a string")
    _require_sha256_digest("derived_validation_digest", expected_digest)
    comparable = dict(payload)
    comparable.pop("derived_validation_digest", None)
    canonical_payload = dumps(
        comparable,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    )
    actual_digest = sha256(canonical_payload.encode("utf-8")).hexdigest()
    if expected_digest != actual_digest:
        raise ValueError("derived_validation_digest does not match payload")


def _report_from_public_payload(
    payload: dict[str, Any],
) -> ResearchStrategySignalConfidenceDecayBridgeReport:
    _require_public_payload_keys("payload", payload, PUBLIC_REPORT_PAYLOAD_KEYS)
    rows_value = payload["rows"]
    if type(rows_value) is not list:
        raise ValueError("rows must be a JSON list")
    reason_counts_value = payload["reason_code_counts"]
    if type(reason_counts_value) is not list:
        raise ValueError("reason_code_counts must be a JSON list")
    return ResearchStrategySignalConfidenceDecayBridgeReport(
        generated_at=_public_datetime("generated_at", payload["generated_at"]),
        config_version=_public_string("config_version", payload["config_version"]),
        source_row_count=_public_decimal("source_row_count", payload["source_row_count"]),
        pass_count=_public_decimal("pass_count", payload["pass_count"]),
        watch_count=_public_decimal("watch_count", payload["watch_count"]),
        block_count=_public_decimal("block_count", payload["block_count"]),
        mean_source_age_pressure=_public_decimal(
            "mean_source_age_pressure",
            payload["mean_source_age_pressure"],
        ),
        mean_evidence_decay_score=_public_decimal(
            "mean_evidence_decay_score",
            payload["mean_evidence_decay_score"],
        ),
        mean_confidence_decay_bridge_score=_public_decimal(
            "mean_confidence_decay_bridge_score",
            payload["mean_confidence_decay_bridge_score"],
        ),
        lowest_confidence_decay_bridge_score=_public_decimal(
            "lowest_confidence_decay_bridge_score",
            payload["lowest_confidence_decay_bridge_score"],
        ),
        highest_evidence_decay_score=_public_decimal(
            "highest_evidence_decay_score",
            payload["highest_evidence_decay_score"],
        ),
        status=_public_string("status", payload["status"]),
        reason_codes=_public_string_tuple("reason_codes", payload["reason_codes"]),
        reason_code_counts=tuple(
            _public_reason_code_count(item) for item in reason_counts_value
        ),
        rows=tuple(_row_from_public_payload(item) for item in rows_value),
        derived_validation_digest=_public_string(
            "derived_validation_digest",
            payload["derived_validation_digest"],
        ),
        paper_only=_public_bool("paper_only", payload["paper_only"]),
        report_only=_public_bool("report_only", payload["report_only"]),
        readonly=_public_bool("readonly", payload["readonly"]),
    )


def _row_from_public_payload(
    payload: object,
) -> ResearchStrategySignalConfidenceDecayBridgeRow:
    if type(payload) is not dict:
        raise ValueError("rows must contain JSON objects")
    _require_public_payload_keys("row", payload, PUBLIC_ROW_PAYLOAD_KEYS)
    return ResearchStrategySignalConfidenceDecayBridgeRow(
        aggregate_row_number=_public_decimal(
            "aggregate_row_number",
            payload["aggregate_row_number"],
        ),
        aggregate_signal_hash=_public_string(
            "aggregate_signal_hash",
            payload["aggregate_signal_hash"],
        ),
        source_age_seconds=_public_decimal(
            "source_age_seconds",
            payload["source_age_seconds"],
        ),
        source_age_pressure=_public_decimal(
            "source_age_pressure",
            payload["source_age_pressure"],
        ),
        freshness_score=_public_decimal("freshness_score", payload["freshness_score"]),
        base_signal_confidence_score=_public_decimal(
            "base_signal_confidence_score",
            payload["base_signal_confidence_score"],
        ),
        source_authority_score=_public_decimal(
            "source_authority_score",
            payload["source_authority_score"],
        ),
        corroboration_score=_public_decimal(
            "corroboration_score",
            payload["corroboration_score"],
        ),
        contradiction_pressure=_public_decimal(
            "contradiction_pressure",
            payload["contradiction_pressure"],
        ),
        market_movement_pressure=_public_decimal(
            "market_movement_pressure",
            payload["market_movement_pressure"],
        ),
        cost_drag_score=_public_decimal("cost_drag_score", payload["cost_drag_score"]),
        liquidity_reliability_score=_public_decimal(
            "liquidity_reliability_score",
            payload["liquidity_reliability_score"],
        ),
        resolution_ambiguity_score=_public_decimal(
            "resolution_ambiguity_score",
            payload["resolution_ambiguity_score"],
        ),
        evidence_decay_score=_public_decimal(
            "evidence_decay_score",
            payload["evidence_decay_score"],
        ),
        confidence_decay_bridge_score=_public_decimal(
            "confidence_decay_bridge_score",
            payload["confidence_decay_bridge_score"],
        ),
        status=_public_string("status", payload["status"]),
        reason_codes=_public_string_tuple("reason_codes", payload["reason_codes"]),
        derived_validation_digest=_public_string(
            "derived_validation_digest",
            payload["derived_validation_digest"],
        ),
        paper_only=_public_bool("paper_only", payload["paper_only"]),
        report_only=_public_bool("report_only", payload["report_only"]),
        readonly=_public_bool("readonly", payload["readonly"]),
    )


def _public_reason_code_count(payload: object) -> tuple[str, Decimal]:
    if type(payload) is not list or len(payload) != 2:
        raise ValueError("reason_code_counts must contain reason/count pairs")
    return (
        _public_string("reason_code", payload[0]),
        _public_decimal("reason_code_count", payload[1]),
    )


def _public_string_tuple(name: str, value: object) -> tuple[str, ...]:
    if type(value) is not list:
        raise ValueError(f"{name} must be a JSON list")
    return tuple(_public_string(f"{name} item", item) for item in value)


def _public_datetime(name: str, value: object) -> datetime:
    if type(value) is not str:
        raise ValueError(f"{name} must be a JSON string")
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError as exc:
        raise ValueError(f"{name} must be an ISO datetime string") from exc
    normalized = _as_utc(name, parsed)
    if normalized.isoformat() != value:
        raise ValueError(f"{name} must be a canonical UTC datetime string")
    return normalized


def _public_decimal(name: str, value: object) -> Decimal:
    if type(value) is not str:
        raise ValueError(f"{name} must be JSON string encoded")
    try:
        parsed = Decimal(value)
    except InvalidOperation as exc:
        raise ValueError(f"{name} must be a Decimal string") from exc
    normalized = _decimal(name, parsed)
    if format(normalized, "f") != value:
        raise ValueError(f"{name} must be a canonical Decimal string")
    return normalized


def _public_string(name: str, value: object) -> str:
    return _require_canonical_string(name, value)


def _public_bool(name: str, value: object) -> bool:
    if type(value) is not bool:
        raise ValueError(f"{name} must be a boolean")
    return value


def _require_public_payload_keys(
    label: str,
    payload: dict[str, Any],
    expected_keys: frozenset[str],
) -> None:
    actual_keys = frozenset(payload)
    if actual_keys == expected_keys:
        return
    missing_keys = tuple(sorted(expected_keys - actual_keys))
    extra_keys = tuple(sorted(actual_keys - expected_keys))
    if missing_keys:
        raise ValueError(
            f"{label} is missing public payload keys: {', '.join(missing_keys)}",
        )
    raise ValueError(
        f"{label} contains unsupported public payload keys: {', '.join(extra_keys)}",
    )


def _json_ready(value: Any) -> Any:
    if is_dataclass(value) and not isinstance(value, type):
        return _json_ready(asdict(value))
    if isinstance(value, Decimal):
        return format(_quantize(value), "f")
    if isinstance(value, datetime):
        return _as_utc("datetime", value).isoformat()
    if isinstance(value, dict):
        return {str(key): _json_ready(item) for key, item in value.items()}
    if isinstance(value, (tuple, list)):
        return [_json_ready(item) for item in value]
    if type(value) in (str, bool) or value is None:
        return value
    raise ValueError("payload contains unsupported value type")


def _validate_public_payload_values(label: str, value: object) -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError(f"{label} keys must be strings")
            _validate_public_payload_values(key, item)
    elif isinstance(value, list):
        for item in value:
            _validate_public_payload_values(label, item)
    elif type(value) in (Decimal, int, float):
        raise ValueError(f"{label} must be JSON string encoded")
    elif type(value) not in (str, bool) and value is not None:
        raise ValueError(f"{label} contains unsupported value type")


def _reject_unsafe_public_payload(label: str, value: object) -> None:
    if is_dataclass(value) and not isinstance(value, type):
        for field in fields(value):
            _reject_unsafe_key(label, field.name)
            _reject_unsafe_public_payload(field.name, getattr(value, field.name))
        return
    if isinstance(value, dict):
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError(f"{label} keys must be strings")
            _reject_unsafe_key(label, key)
            _reject_unsafe_public_payload(key, item)
        return
    if isinstance(value, (tuple, list)):
        for item in value:
            _reject_unsafe_public_payload(label, item)
        return
    if type(value) is str:
        lowered = value.lower()
        if any(fragment in lowered for fragment in UNSAFE_VALUE_FRAGMENTS):
            raise ValueError(f"{label} contains unsafe public value")


def _reject_unsafe_key(label: str, key: str) -> None:
    lowered = key.lower()
    if any(fragment in lowered for fragment in UNSAFE_KEY_FRAGMENTS):
        raise ValueError(f"{label} contains unsafe public key")


def _normalize_positive_decimal(name: str, value: object) -> Decimal:
    normalized = _decimal(name, value)
    if normalized <= ZERO:
        raise ValueError(f"{name} must be positive")
    return normalized


def _normalize_nonnegative_decimal(name: str, value: object) -> Decimal:
    normalized = _decimal(name, value)
    if normalized < ZERO:
        raise ValueError(f"{name} must be nonnegative")
    return normalized


def _normalize_nonnegative_count(name: str, value: object) -> Decimal:
    normalized = _normalize_nonnegative_decimal(name, value)
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{name} must be integral")
    return normalized


def _normalize_positive_count(name: str, value: object) -> Decimal:
    normalized = _normalize_positive_decimal(name, value)
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{name} must be integral")
    return normalized


def _normalize_probability(name: str, value: object) -> Decimal:
    normalized = _decimal(name, value)
    if normalized < ZERO or normalized > ONE:
        raise ValueError(f"{name} must be between zero and one")
    return normalized


def _decimal(name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{name} must be finite")
    try:
        return _quantize(value)
    except InvalidOperation as exc:
        raise ValueError(f"{name} must be quantizable") from exc


def _quantize(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(RATIO_QUANTUM)


def _as_utc(name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_exact_type(value: object, expected_type: type[object], label: str) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{label} must be exactly {expected_type.__name__}")


def _require_canonical_string(name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{name} must be a canonical nonblank string")
    return value


def _require_status(name: str, value: object) -> None:
    if value not in RESEARCH_STRATEGY_SIGNAL_CONFIDENCE_DECAY_BRIDGE_STATUSES:
        raise ValueError(f"{name} must be one of pass, watch, block")


def _require_reason_code(name: str, value: object) -> None:
    _require_canonical_string(name, value)
    if value not in ALL_REASON_CODES:
        raise ValueError(f"{name} must be a known reason code")


def _require_sha256_digest(name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{name} must be a string")
    if len(value) != 64:
        raise ValueError(f"{name} must be a 64-character hex string")
    if any(character not in "0123456789abcdef" for character in value):
        raise ValueError(f"{name} must be lowercase hex")


def _require_hard_flags(label: str, value: object) -> None:
    for flag_name in ("paper_only", "report_only", "readonly"):
        if getattr(value, flag_name) is not True:
            raise ValueError(f"{label} {flag_name} must be True")


def _require_age_threshold_pair(name: str, watch_value: Decimal, block_value: Decimal) -> None:
    if watch_value >= block_value:
        raise ValueError(f"{name} must use ascending threshold values")


def _require_min_threshold_pair(name: str, watch_value: Decimal, pass_value: Decimal) -> None:
    if pass_value < watch_value:
        raise ValueError(f"{name} must keep pass threshold at least watch threshold")


def _require_max_threshold_pair(name: str, pass_value: Decimal, watch_value: Decimal) -> None:
    if pass_value > watch_value:
        raise ValueError(f"{name} must keep pass threshold no greater than watch threshold")
