"""Pure report for research strategy edge decay monitoring."""

from __future__ import annotations

from collections import Counter
from dataclasses import InitVar, asdict, dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, InvalidOperation, localcontext
import hashlib
import json
from typing import Any


DEFAULT_RESEARCH_STRATEGY_EDGE_DECAY_MONITOR_REPORT_CONFIG_VERSION = (
    "research-strategy-edge-decay-monitor-report-v0"
)

STATUS_PASS = "pass"
STATUS_WATCH = "watch"
STATUS_BLOCK = "block"
STATUSES = (STATUS_PASS, STATUS_WATCH, STATUS_BLOCK)

REASON_PREFIX = "research_strategy_edge_decay_monitor_"
NO_INPUTS_REASON = f"{REASON_PREFIX}no_inputs"
PASS_REASON = f"{REASON_PREFIX}pass"
AGING_EVIDENCE_REASON = f"{REASON_PREFIX}aging_evidence"
STALE_EVIDENCE_REASON = f"{REASON_PREFIX}stale_evidence"
MARKET_REPRICING_WATCH_REASON = f"{REASON_PREFIX}market_repricing_watch"
MARKET_REPRICING_BLOCK_REASON = f"{REASON_PREFIX}market_repricing_block"
COST_PRESSURE_WATCH_REASON = f"{REASON_PREFIX}cost_pressure_watch"
COST_PRESSURE_BLOCK_REASON = f"{REASON_PREFIX}cost_pressure_block"
TEAM_REVIEW_LAG_WATCH_REASON = f"{REASON_PREFIX}team_review_lag_watch"
TEAM_REVIEW_LAG_BLOCK_REASON = f"{REASON_PREFIX}team_review_lag_block"
SCORE_WATCH_REASON = f"{REASON_PREFIX}score_watch"
SCORE_BLOCK_REASON = f"{REASON_PREFIX}score_block"

REASON_CODE_SEQUENCE = (
    NO_INPUTS_REASON,
    STALE_EVIDENCE_REASON,
    AGING_EVIDENCE_REASON,
    MARKET_REPRICING_BLOCK_REASON,
    MARKET_REPRICING_WATCH_REASON,
    COST_PRESSURE_BLOCK_REASON,
    COST_PRESSURE_WATCH_REASON,
    TEAM_REVIEW_LAG_BLOCK_REASON,
    TEAM_REVIEW_LAG_WATCH_REASON,
    SCORE_BLOCK_REASON,
    SCORE_WATCH_REASON,
    PASS_REASON,
)
ROW_REASON_CODE_SEQUENCE = (
    STALE_EVIDENCE_REASON,
    AGING_EVIDENCE_REASON,
    MARKET_REPRICING_BLOCK_REASON,
    MARKET_REPRICING_WATCH_REASON,
    COST_PRESSURE_BLOCK_REASON,
    COST_PRESSURE_WATCH_REASON,
    TEAM_REVIEW_LAG_BLOCK_REASON,
    TEAM_REVIEW_LAG_WATCH_REASON,
    SCORE_BLOCK_REASON,
    SCORE_WATCH_REASON,
    PASS_REASON,
)
STATUS_RANK = {STATUS_BLOCK: 0, STATUS_WATCH: 1, STATUS_PASS: 2}

DECIMAL_CONTEXT = Context(prec=64)
QUANT = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
SECONDS_PER_DAY = Decimal("86400")
MICROSECONDS_PER_SECOND = Decimal("1000000")
HASH_PREFIX = "sha256:"
SENSITIVE_TEXT_FRAGMENTS = (
    "private",
    "secret",
    "hidden",
    "password",
    "bearer",
    "token",
    "api_key",
    "key=",
)


@dataclass(frozen=True)
class ResearchStrategyEdgeDecayMonitorConfig:
    config_version: str = (
        DEFAULT_RESEARCH_STRATEGY_EDGE_DECAY_MONITOR_REPORT_CONFIG_VERSION
    )
    fresh_evidence_max_age_seconds: Decimal = Decimal("3600.000000")
    stale_evidence_max_age_seconds: Decimal = Decimal("86400.000000")
    repricing_watch_delta: Decimal = Decimal("0.050000")
    repricing_block_delta: Decimal = Decimal("0.120000")
    cost_pressure_watch_delta: Decimal = Decimal("0.020000")
    cost_pressure_block_delta: Decimal = Decimal("0.060000")
    review_watch_lag_seconds: Decimal = Decimal("21600.000000")
    review_block_lag_seconds: Decimal = Decimal("86400.000000")
    pass_edge_health_score: Decimal = Decimal("0.750000")
    watch_edge_health_score: Decimal = Decimal("0.500000")
    evidence_age_weight: Decimal = Decimal("0.250000")
    market_repricing_weight: Decimal = Decimal("0.250000")
    cost_pressure_weight: Decimal = Decimal("0.250000")
    team_review_lag_weight: Decimal = Decimal("0.250000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchStrategyEdgeDecayMonitorConfig:
            raise TypeError("ResearchStrategyEdgeDecayMonitorConfig cannot be subclassed")

    def __post_init__(self) -> None:
        if type(self) is not ResearchStrategyEdgeDecayMonitorConfig:
            raise ValueError("config must be exactly ResearchStrategyEdgeDecayMonitorConfig")
        _require_public_text("config_version", self.config_version)
        for field_name in (
            "fresh_evidence_max_age_seconds",
            "stale_evidence_max_age_seconds",
            "review_watch_lag_seconds",
            "review_block_lag_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        if self.stale_evidence_max_age_seconds <= self.fresh_evidence_max_age_seconds:
            raise ValueError(
                "stale_evidence_max_age_seconds must exceed "
                "fresh_evidence_max_age_seconds",
            )
        if self.review_block_lag_seconds <= self.review_watch_lag_seconds:
            raise ValueError(
                "review_block_lag_seconds must exceed review_watch_lag_seconds",
            )
        for field_name in (
            "repricing_watch_delta",
            "repricing_block_delta",
            "cost_pressure_watch_delta",
            "cost_pressure_block_delta",
            "pass_edge_health_score",
            "watch_edge_health_score",
            "evidence_age_weight",
            "market_repricing_weight",
            "cost_pressure_weight",
            "team_review_lag_weight",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_probability_decimal(field_name, getattr(self, field_name)),
            )
        if self.repricing_watch_delta > self.repricing_block_delta:
            raise ValueError("repricing_watch_delta must not exceed repricing_block_delta")
        if self.cost_pressure_watch_delta > self.cost_pressure_block_delta:
            raise ValueError(
                "cost_pressure_watch_delta must not exceed cost_pressure_block_delta",
            )
        if self.pass_edge_health_score <= self.watch_edge_health_score:
            raise ValueError("pass_edge_health_score must exceed watch_edge_health_score")
        if _config_weight_sum(self) != ONE:
            raise ValueError(
                "evidence_age_weight, market_repricing_weight, cost_pressure_weight, "
                "and team_review_lag_weight must sum to 1",
            )
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class ResearchStrategyEdgeDecayMonitorInput:
    research_case_ref: str
    evidence_observed_at: datetime
    last_market_priced_at: datetime
    last_team_reviewed_at: datetime
    apparent_edge: Decimal
    current_edge: Decimal
    evidence_market_probability: Decimal
    current_market_probability: Decimal
    baseline_cost_rate: Decimal
    current_cost_rate: Decimal
    reason_codes: tuple[str, ...] = ()
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchStrategyEdgeDecayMonitorInput:
            raise TypeError("ResearchStrategyEdgeDecayMonitorInput cannot be subclassed")

    def __post_init__(self) -> None:
        if type(self) is not ResearchStrategyEdgeDecayMonitorInput:
            raise ValueError("input must be exactly ResearchStrategyEdgeDecayMonitorInput")
        _require_ref_text("research_case_ref", self.research_case_ref)
        for field_name in (
            "evidence_observed_at",
            "last_market_priced_at",
            "last_team_reviewed_at",
        ):
            object.__setattr__(
                self,
                field_name,
                _as_utc(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "apparent_edge",
            _require_positive_decimal("apparent_edge", self.apparent_edge),
        )
        object.__setattr__(
            self,
            "current_edge",
            _require_decimal("current_edge", self.current_edge),
        )
        for field_name in (
            "evidence_market_probability",
            "current_market_probability",
            "baseline_cost_rate",
            "current_cost_rate",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_probability_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "reason_codes",
            tuple(
                sorted(
                    _normalize_reason_codes(
                        "reason_codes",
                        self.reason_codes,
                        allow_empty=True,
                    ),
                ),
            ),
        )
        _require_hard_flags("input", self)


@dataclass(frozen=True)
class ResearchStrategyEdgeDecayMonitorRow:
    redacted_research_case_ref: str
    evidence_observed_at: datetime
    last_market_priced_at: datetime
    last_team_reviewed_at: datetime
    apparent_edge: Decimal
    current_edge: Decimal
    evidence_market_probability: Decimal
    current_market_probability: Decimal
    baseline_cost_rate: Decimal
    current_cost_rate: Decimal
    evidence_age_seconds: Decimal
    market_repricing_delta: Decimal
    cost_pressure: Decimal
    team_review_lag_seconds: Decimal
    edge_decay_ratio: Decimal
    edge_retention_ratio: Decimal
    evidence_age_score: Decimal
    market_repricing_score: Decimal
    cost_pressure_score: Decimal
    team_review_lag_score: Decimal
    edge_health_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True
    validation_config: InitVar[ResearchStrategyEdgeDecayMonitorConfig | None] = None

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchStrategyEdgeDecayMonitorRow:
            raise TypeError("ResearchStrategyEdgeDecayMonitorRow cannot be subclassed")

    def __post_init__(
        self,
        validation_config: ResearchStrategyEdgeDecayMonitorConfig | None,
    ) -> None:
        if type(self) is not ResearchStrategyEdgeDecayMonitorRow:
            raise ValueError("row must be exactly ResearchStrategyEdgeDecayMonitorRow")
        _require_redacted_ref("redacted_research_case_ref", self.redacted_research_case_ref)
        for field_name in (
            "evidence_observed_at",
            "last_market_priced_at",
            "last_team_reviewed_at",
        ):
            object.__setattr__(
                self,
                field_name,
                _as_utc(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "apparent_edge",
            _require_positive_decimal("apparent_edge", self.apparent_edge),
        )
        object.__setattr__(
            self,
            "current_edge",
            _require_decimal("current_edge", self.current_edge),
        )
        for field_name in (
            "evidence_market_probability",
            "current_market_probability",
            "baseline_cost_rate",
            "current_cost_rate",
            "edge_decay_ratio",
            "edge_retention_ratio",
            "evidence_age_score",
            "market_repricing_score",
            "cost_pressure_score",
            "team_review_lag_score",
            "edge_health_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_probability_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "evidence_age_seconds",
            "market_repricing_delta",
            "cost_pressure",
            "team_review_lag_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        _require_status("status", self.status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, allow_empty=False),
        )
        _require_hard_flags("row", self)
        _validate_row(self, config=validation_config)


@dataclass(frozen=True)
class ResearchStrategyEdgeDecayMonitorReasonCodeCount:
    reason_code: str
    count: Decimal
    row_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchStrategyEdgeDecayMonitorReasonCodeCount:
            raise TypeError(
                "ResearchStrategyEdgeDecayMonitorReasonCodeCount cannot be subclassed",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchStrategyEdgeDecayMonitorReasonCodeCount:
            raise ValueError(
                "reason count must be exactly "
                "ResearchStrategyEdgeDecayMonitorReasonCodeCount",
            )
        _require_reason_code("reason_code", self.reason_code)
        object.__setattr__(
            self,
            "count",
            _require_positive_whole_decimal("count", self.count),
        )
        object.__setattr__(
            self,
            "row_ratio",
            _require_probability_decimal("row_ratio", self.row_ratio),
        )
        _require_hard_flags("reason count", self)


@dataclass(frozen=True)
class ResearchStrategyEdgeDecayMonitorReport:
    generated_at: datetime
    config_version: str
    input_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    average_edge_health_score: Decimal
    max_edge_decay_ratio: Decimal
    max_evidence_age_seconds: Decimal
    max_market_repricing_delta: Decimal
    max_cost_pressure: Decimal
    max_team_review_lag_seconds: Decimal
    status: str
    reason_codes: tuple[str, ...]
    reason_code_counts: tuple[ResearchStrategyEdgeDecayMonitorReasonCodeCount, ...]
    rows: tuple[ResearchStrategyEdgeDecayMonitorRow, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchStrategyEdgeDecayMonitorReport:
            raise TypeError("ResearchStrategyEdgeDecayMonitorReport cannot be subclassed")

    def __post_init__(self) -> None:
        if type(self) is not ResearchStrategyEdgeDecayMonitorReport:
            raise ValueError("report must be exactly ResearchStrategyEdgeDecayMonitorReport")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_text("config_version", self.config_version)
        for field_name in (
            "input_count",
            "pass_count",
            "watch_count",
            "block_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_whole_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "average_edge_health_score",
            "max_edge_decay_ratio",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_probability_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "max_evidence_age_seconds",
            "max_market_repricing_delta",
            "max_cost_pressure",
            "max_team_review_lag_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        _require_status("status", self.status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, allow_empty=False),
        )
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        _require_hard_flags("report", self)
        _validate_report(self)


def build_research_strategy_edge_decay_monitor_report(
    inputs: list[object] | tuple[object, ...],
    *,
    config: ResearchStrategyEdgeDecayMonitorConfig,
    generated_at: datetime,
) -> ResearchStrategyEdgeDecayMonitorReport:
    if type(config) is not ResearchStrategyEdgeDecayMonitorConfig:
        raise ValueError("config must be a ResearchStrategyEdgeDecayMonitorConfig")
    _require_hard_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    input_rows = _normalize_inputs(inputs, generated_at_utc)
    rows = _ranked_rows(
        tuple(
            _row_from_input(item, config=config, generated_at=generated_at_utc)
            for item in input_rows
        ),
    )
    return ResearchStrategyEdgeDecayMonitorReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        input_count=_count(len(rows)),
        pass_count=_count(_status_count(rows, STATUS_PASS)),
        watch_count=_count(_status_count(rows, STATUS_WATCH)),
        block_count=_count(_status_count(rows, STATUS_BLOCK)),
        average_edge_health_score=_average(
            tuple(row.edge_health_score for row in rows),
        ),
        max_edge_decay_ratio=_max_decimal(row.edge_decay_ratio for row in rows),
        max_evidence_age_seconds=_max_decimal(row.evidence_age_seconds for row in rows),
        max_market_repricing_delta=_max_decimal(
            (row.market_repricing_delta for row in rows),
        ),
        max_cost_pressure=_max_decimal(row.cost_pressure for row in rows),
        max_team_review_lag_seconds=_max_decimal(
            (row.team_review_lag_seconds for row in rows),
        ),
        status=_report_status(rows),
        reason_codes=_report_reason_codes(rows),
        reason_code_counts=_reason_code_counts(rows),
        rows=rows,
    )


def research_strategy_edge_decay_monitor_report_payload(
    report: ResearchStrategyEdgeDecayMonitorReport,
) -> dict[str, Any]:
    if type(report) is not ResearchStrategyEdgeDecayMonitorReport:
        raise ValueError("report must be a ResearchStrategyEdgeDecayMonitorReport")
    _require_hard_flags("report", report)
    payload = _payload_value(report)
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    return payload


def research_strategy_edge_decay_monitor_report_digest(
    report: ResearchStrategyEdgeDecayMonitorReport,
) -> str:
    payload = research_strategy_edge_decay_monitor_report_payload(report)
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def _row_from_input(
    item: ResearchStrategyEdgeDecayMonitorInput,
    *,
    config: ResearchStrategyEdgeDecayMonitorConfig,
    generated_at: datetime,
) -> ResearchStrategyEdgeDecayMonitorRow:
    evidence_age_seconds = _time_delta_seconds(generated_at, item.evidence_observed_at)
    market_repricing_delta = _absolute_decimal(
        item.current_market_probability - item.evidence_market_probability,
    )
    cost_pressure = max(ZERO, _quantize(item.current_cost_rate - item.baseline_cost_rate))
    team_review_lag_seconds = _time_delta_seconds(generated_at, item.last_team_reviewed_at)
    edge_decay_ratio = _edge_decay_ratio(item.current_edge, item.apparent_edge)
    edge_retention_ratio = _quantize(ONE - edge_decay_ratio)
    evidence_age_score = _threshold_score(
        evidence_age_seconds,
        watch_threshold=config.fresh_evidence_max_age_seconds,
        block_threshold=config.stale_evidence_max_age_seconds,
    )
    market_repricing_score = _threshold_score(
        market_repricing_delta,
        watch_threshold=config.repricing_watch_delta,
        block_threshold=config.repricing_block_delta,
    )
    cost_pressure_score = _threshold_score(
        cost_pressure,
        watch_threshold=config.cost_pressure_watch_delta,
        block_threshold=config.cost_pressure_block_delta,
    )
    team_review_lag_score = _threshold_score(
        team_review_lag_seconds,
        watch_threshold=config.review_watch_lag_seconds,
        block_threshold=config.review_block_lag_seconds,
    )
    component_score = _component_score(
        evidence_age_score=evidence_age_score,
        market_repricing_score=market_repricing_score,
        cost_pressure_score=cost_pressure_score,
        team_review_lag_score=team_review_lag_score,
        config=config,
    )
    edge_health_score = _quantize(edge_retention_ratio * component_score)
    reason_codes = _row_reason_codes(
        source_reason_codes=item.reason_codes,
        evidence_age_seconds=evidence_age_seconds,
        market_repricing_delta=market_repricing_delta,
        cost_pressure=cost_pressure,
        team_review_lag_seconds=team_review_lag_seconds,
        edge_health_score=edge_health_score,
        config=config,
    )
    return ResearchStrategyEdgeDecayMonitorRow(
        redacted_research_case_ref=_redacted_ref(item.research_case_ref),
        evidence_observed_at=item.evidence_observed_at,
        last_market_priced_at=item.last_market_priced_at,
        last_team_reviewed_at=item.last_team_reviewed_at,
        apparent_edge=item.apparent_edge,
        current_edge=item.current_edge,
        evidence_market_probability=item.evidence_market_probability,
        current_market_probability=item.current_market_probability,
        baseline_cost_rate=item.baseline_cost_rate,
        current_cost_rate=item.current_cost_rate,
        evidence_age_seconds=evidence_age_seconds,
        market_repricing_delta=market_repricing_delta,
        cost_pressure=cost_pressure,
        team_review_lag_seconds=team_review_lag_seconds,
        edge_decay_ratio=edge_decay_ratio,
        edge_retention_ratio=edge_retention_ratio,
        evidence_age_score=evidence_age_score,
        market_repricing_score=market_repricing_score,
        cost_pressure_score=cost_pressure_score,
        team_review_lag_score=team_review_lag_score,
        edge_health_score=edge_health_score,
        status=_row_status(reason_codes),
        reason_codes=reason_codes,
        validation_config=config,
    )


def _normalize_inputs(
    inputs: list[object] | tuple[object, ...],
    generated_at: datetime,
) -> tuple[ResearchStrategyEdgeDecayMonitorInput, ...]:
    if type(inputs) not in (list, tuple):
        raise ValueError("inputs must be a list or tuple")
    normalized = tuple(inputs)
    seen: set[str] = set()
    for item in normalized:
        if type(item) is not ResearchStrategyEdgeDecayMonitorInput:
            raise ValueError("inputs must contain ResearchStrategyEdgeDecayMonitorInput")
        _require_hard_flags("input", item)
        if item.evidence_observed_at > generated_at:
            raise ValueError("evidence_observed_at must be on or before generated_at")
        if item.last_market_priced_at > generated_at:
            raise ValueError("last_market_priced_at must be on or before generated_at")
        if item.last_team_reviewed_at > generated_at:
            raise ValueError("last_team_reviewed_at must be on or before generated_at")
        redacted_ref = _redacted_ref(item.research_case_ref)
        if redacted_ref in seen:
            raise ValueError("inputs must be unique")
        seen.add(redacted_ref)
    return normalized


def _ranked_rows(
    rows: tuple[ResearchStrategyEdgeDecayMonitorRow, ...],
) -> tuple[ResearchStrategyEdgeDecayMonitorRow, ...]:
    return tuple(
        sorted(
            rows,
            key=lambda row: (
                STATUS_RANK[row.status],
                row.edge_health_score,
                -row.edge_decay_ratio,
                row.redacted_research_case_ref,
            ),
        ),
    )


def _row_reason_codes(
    *,
    source_reason_codes: tuple[str, ...],
    evidence_age_seconds: Decimal,
    market_repricing_delta: Decimal,
    cost_pressure: Decimal,
    team_review_lag_seconds: Decimal,
    edge_health_score: Decimal,
    config: ResearchStrategyEdgeDecayMonitorConfig,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    if evidence_age_seconds >= config.stale_evidence_max_age_seconds:
        reason_codes.append(STALE_EVIDENCE_REASON)
    elif evidence_age_seconds > config.fresh_evidence_max_age_seconds:
        reason_codes.append(AGING_EVIDENCE_REASON)
    if market_repricing_delta >= config.repricing_block_delta:
        reason_codes.append(MARKET_REPRICING_BLOCK_REASON)
    elif market_repricing_delta >= config.repricing_watch_delta:
        reason_codes.append(MARKET_REPRICING_WATCH_REASON)
    if cost_pressure >= config.cost_pressure_block_delta:
        reason_codes.append(COST_PRESSURE_BLOCK_REASON)
    elif cost_pressure >= config.cost_pressure_watch_delta:
        reason_codes.append(COST_PRESSURE_WATCH_REASON)
    if team_review_lag_seconds >= config.review_block_lag_seconds:
        reason_codes.append(TEAM_REVIEW_LAG_BLOCK_REASON)
    elif team_review_lag_seconds >= config.review_watch_lag_seconds:
        reason_codes.append(TEAM_REVIEW_LAG_WATCH_REASON)
    if edge_health_score < config.watch_edge_health_score:
        reason_codes.append(SCORE_BLOCK_REASON)
    elif edge_health_score < config.pass_edge_health_score:
        reason_codes.append(SCORE_WATCH_REASON)
    if not reason_codes:
        reason_codes.append(PASS_REASON)
    ranked = [
        reason_code
        for reason_code in ROW_REASON_CODE_SEQUENCE
        if reason_code in reason_codes
    ]
    ranked.extend(f"input_{reason_code}" for reason_code in source_reason_codes)
    return tuple(ranked)


def _row_status(reason_codes: tuple[str, ...]) -> str:
    if (
        STALE_EVIDENCE_REASON in reason_codes
        or MARKET_REPRICING_BLOCK_REASON in reason_codes
        or COST_PRESSURE_BLOCK_REASON in reason_codes
        or TEAM_REVIEW_LAG_BLOCK_REASON in reason_codes
        or SCORE_BLOCK_REASON in reason_codes
    ):
        return STATUS_BLOCK
    if reason_codes == (PASS_REASON,):
        return STATUS_PASS
    return STATUS_WATCH


def _report_status(rows: tuple[ResearchStrategyEdgeDecayMonitorRow, ...]) -> str:
    if not rows:
        return STATUS_BLOCK
    if any(row.status == STATUS_BLOCK for row in rows):
        return STATUS_BLOCK
    if any(row.status == STATUS_WATCH for row in rows):
        return STATUS_WATCH
    return STATUS_PASS


def _report_reason_codes(
    rows: tuple[ResearchStrategyEdgeDecayMonitorRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return (NO_INPUTS_REASON,)
    found = {reason_code for row in rows for reason_code in row.reason_codes}
    return tuple(reason_code for reason_code in REASON_CODE_SEQUENCE if reason_code in found)


def _reason_code_counts(
    rows: tuple[ResearchStrategyEdgeDecayMonitorRow, ...],
) -> tuple[ResearchStrategyEdgeDecayMonitorReasonCodeCount, ...]:
    if not rows:
        return (
            ResearchStrategyEdgeDecayMonitorReasonCodeCount(
                reason_code=NO_INPUTS_REASON,
                count=ONE,
                row_ratio=ONE,
            ),
        )
    total = _count(len(rows))
    counter: Counter[str] = Counter()
    for row in rows:
        counter.update(row.reason_codes)
    reason_codes = tuple(
        reason_code
        for reason_code in REASON_CODE_SEQUENCE
        if reason_code in counter
    )
    input_reason_codes = tuple(
        sorted(
            reason_code
            for reason_code in counter
            if reason_code.startswith("input_")
        ),
    )
    return tuple(
        ResearchStrategyEdgeDecayMonitorReasonCodeCount(
            reason_code=reason_code,
            count=_count(counter[reason_code]),
            row_ratio=_ratio(_count(counter[reason_code]), total),
        )
        for reason_code in (*reason_codes, *input_reason_codes)
    )


def _status_count(
    rows: tuple[ResearchStrategyEdgeDecayMonitorRow, ...],
    status: str,
) -> int:
    return sum(1 for row in rows if row.status == status)


def _average(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return ZERO
    return _ratio(sum(values, ZERO), _count(len(values)))


def _max_decimal(values: Any) -> Decimal:
    normalized = tuple(values)
    if not normalized:
        return ZERO
    return max(normalized)


def _validate_row(
    row: ResearchStrategyEdgeDecayMonitorRow,
    *,
    config: ResearchStrategyEdgeDecayMonitorConfig | None,
) -> None:
    if config is None:
        config = ResearchStrategyEdgeDecayMonitorConfig()
    if type(config) is not ResearchStrategyEdgeDecayMonitorConfig:
        raise ValueError("validation_config must be a ResearchStrategyEdgeDecayMonitorConfig")
    if row.edge_decay_ratio != _edge_decay_ratio(row.current_edge, row.apparent_edge):
        raise ValueError("edge_decay_ratio must match edge inputs")
    if row.edge_retention_ratio != _quantize(ONE - row.edge_decay_ratio):
        raise ValueError("edge_retention_ratio must match edge_decay_ratio")
    if row.market_repricing_delta != _absolute_decimal(
        row.current_market_probability - row.evidence_market_probability,
    ):
        raise ValueError("market_repricing_delta must match probabilities")
    if row.cost_pressure != max(
        ZERO,
        _quantize(row.current_cost_rate - row.baseline_cost_rate),
    ):
        raise ValueError("cost_pressure must match cost rates")
    component_score = _component_score(
        evidence_age_score=row.evidence_age_score,
        market_repricing_score=row.market_repricing_score,
        cost_pressure_score=row.cost_pressure_score,
        team_review_lag_score=row.team_review_lag_score,
        config=config,
    )
    if row.edge_health_score != _quantize(row.edge_retention_ratio * component_score):
        raise ValueError("edge_health_score must match component scores")
    expected_reason_codes = _row_reason_codes(
        source_reason_codes=_input_reason_codes(row.reason_codes),
        evidence_age_seconds=row.evidence_age_seconds,
        market_repricing_delta=row.market_repricing_delta,
        cost_pressure=row.cost_pressure,
        team_review_lag_seconds=row.team_review_lag_seconds,
        edge_health_score=row.edge_health_score,
        config=config,
    )
    if row.reason_codes != expected_reason_codes:
        raise ValueError("reason_codes must match row inputs")
    if row.status != _row_status(row.reason_codes):
        raise ValueError("status must match reason_codes")


def _validate_report(report: ResearchStrategyEdgeDecayMonitorReport) -> None:
    if report.input_count != _count(len(report.rows)):
        raise ValueError("input_count must match rows")
    if report.pass_count != _count(_status_count(report.rows, STATUS_PASS)):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _count(_status_count(report.rows, STATUS_WATCH)):
        raise ValueError("watch_count must match rows")
    if report.block_count != _count(_status_count(report.rows, STATUS_BLOCK)):
        raise ValueError("block_count must match rows")
    if report.average_edge_health_score != _average(
        tuple(row.edge_health_score for row in report.rows),
    ):
        raise ValueError("average_edge_health_score must match rows")
    if report.max_edge_decay_ratio != _max_decimal(
        row.edge_decay_ratio for row in report.rows
    ):
        raise ValueError("max_edge_decay_ratio must match rows")
    if report.max_evidence_age_seconds != _max_decimal(
        row.evidence_age_seconds for row in report.rows
    ):
        raise ValueError("max_evidence_age_seconds must match rows")
    if report.max_market_repricing_delta != _max_decimal(
        row.market_repricing_delta for row in report.rows
    ):
        raise ValueError("max_market_repricing_delta must match rows")
    if report.max_cost_pressure != _max_decimal(row.cost_pressure for row in report.rows):
        raise ValueError("max_cost_pressure must match rows")
    if report.max_team_review_lag_seconds != _max_decimal(
        row.team_review_lag_seconds for row in report.rows
    ):
        raise ValueError("max_team_review_lag_seconds must match rows")
    if report.status != _report_status(report.rows):
        raise ValueError("status must match rows")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")
    if report.reason_code_counts != _reason_code_counts(report.rows):
        raise ValueError("reason_code_counts must match rows")


def _normalize_rows(
    rows: tuple[ResearchStrategyEdgeDecayMonitorRow, ...],
) -> tuple[ResearchStrategyEdgeDecayMonitorRow, ...]:
    if type(rows) is not tuple:
        raise ValueError("rows must be a tuple")
    for row in rows:
        if type(row) is not ResearchStrategyEdgeDecayMonitorRow:
            raise ValueError("rows must contain ResearchStrategyEdgeDecayMonitorRow")
        _require_hard_flags("row", row)
    ranked = _ranked_rows(rows)
    if rows != ranked:
        raise ValueError("rows must be ranked deterministically")
    return rows


def _normalize_reason_code_counts(
    counts: tuple[ResearchStrategyEdgeDecayMonitorReasonCodeCount, ...],
) -> tuple[ResearchStrategyEdgeDecayMonitorReasonCodeCount, ...]:
    if type(counts) is not tuple:
        raise ValueError("reason_code_counts must be a tuple")
    for count in counts:
        if type(count) is not ResearchStrategyEdgeDecayMonitorReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "ResearchStrategyEdgeDecayMonitorReasonCodeCount",
            )
        _require_hard_flags("reason count", count)
    sorted_counts = tuple(
        sorted(counts, key=lambda count: _reason_count_sort_key(count.reason_code)),
    )
    if counts != sorted_counts:
        raise ValueError("reason_code_counts must be sorted")
    return counts


def _reason_count_sort_key(reason_code: str) -> tuple[int, str]:
    if reason_code in REASON_CODE_SEQUENCE:
        return (REASON_CODE_SEQUENCE.index(reason_code), reason_code)
    return (len(REASON_CODE_SEQUENCE), reason_code)


def _input_reason_codes(reason_codes: tuple[str, ...]) -> tuple[str, ...]:
    return tuple(
        reason_code.removeprefix("input_")
        for reason_code in reason_codes
        if reason_code.startswith("input_")
    )


def _payload_value(value: object) -> object:
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, datetime):
        return value.isoformat()
    if is_dataclass(value) and not isinstance(value, type):
        return _payload_value(asdict(value))
    if isinstance(value, tuple):
        return [_payload_value(item) for item in value]
    if isinstance(value, list):
        return [_payload_value(item) for item in value]
    if isinstance(value, dict):
        payload: dict[str, object] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            payload[key] = _payload_value(item)
        return payload
    if isinstance(value, (str, bool)) or value is None:
        return value
    raise ValueError("value is not JSON serializable")


def _edge_decay_ratio(current_edge: Decimal, apparent_edge: Decimal) -> Decimal:
    if current_edge <= ZERO:
        return ONE
    decay = _ratio(apparent_edge - current_edge, apparent_edge)
    if decay < ZERO:
        return ZERO
    if decay > ONE:
        return ONE
    return decay


def _component_score(
    *,
    evidence_age_score: Decimal,
    market_repricing_score: Decimal,
    cost_pressure_score: Decimal,
    team_review_lag_score: Decimal,
    config: ResearchStrategyEdgeDecayMonitorConfig,
) -> Decimal:
    return _quantize(
        (evidence_age_score * config.evidence_age_weight)
        + (market_repricing_score * config.market_repricing_weight)
        + (cost_pressure_score * config.cost_pressure_weight)
        + (team_review_lag_score * config.team_review_lag_weight),
    )


def _threshold_score(
    value: Decimal,
    *,
    watch_threshold: Decimal,
    block_threshold: Decimal,
) -> Decimal:
    if value <= watch_threshold:
        return ONE
    if value >= block_threshold:
        return ZERO
    return _ratio(block_threshold - value, block_threshold - watch_threshold)


def _time_delta_seconds(later: datetime, earlier: datetime) -> Decimal:
    delta = later - earlier
    seconds = (
        (Decimal(delta.days) * SECONDS_PER_DAY)
        + Decimal(delta.seconds)
        + (Decimal(delta.microseconds) / MICROSECONDS_PER_SECOND)
    )
    if seconds < ZERO:
        raise ValueError("time delta must be nonnegative")
    return _quantize(seconds)


def _absolute_decimal(value: Decimal) -> Decimal:
    if value < ZERO:
        return _quantize(-value)
    return _quantize(value)


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    try:
        return _quantize(+value)
    except InvalidOperation as exc:
        raise ValueError(f"{field_name} must be finite") from exc


def _require_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _require_positive_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _require_probability_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < ZERO or normalized > ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return normalized


def _require_nonnegative_whole_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_nonnegative_decimal(field_name, value)
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{field_name} must be whole")
    return _quantize(normalized)


def _require_positive_whole_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_nonnegative_whole_decimal(field_name, value)
    if normalized <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return _quantize(numerator / denominator)


def _quantize(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(QUANT)


def _count(value: int | Decimal) -> Decimal:
    if type(value) is int:
        return _quantize(Decimal(value))
    return _require_nonnegative_whole_decimal("count", value)


def _config_weight_sum(config: ResearchStrategyEdgeDecayMonitorConfig) -> Decimal:
    return _quantize(
        config.evidence_age_weight
        + config.market_repricing_weight
        + config.cost_pressure_weight
        + config.team_review_lag_weight,
    )


def _require_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in STATUSES:
        raise ValueError(f"{field_name} must be pass, watch, or block")


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if getattr(value, field_name, None) is not True:
            raise ValueError(f"{field_name} must be True for {label}")


def _require_public_text(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical string")
    if not all(char.islower() or char.isdigit() or char in "-_" for char in value):
        raise ValueError(f"{field_name} must be public lowercase text")


def _require_ref_text(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical string")


def _require_reason_code(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not _is_reason_code(value):
        raise ValueError(f"{field_name} must be lowercase snake case")


def _normalize_reason_codes(
    field_name: str,
    value: object,
    *,
    allow_empty: bool,
) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ValueError(f"{field_name} must be a tuple")
    reason_codes: list[str] = []
    for item in value:
        _require_reason_code(field_name, item)
        if item not in reason_codes:
            reason_codes.append(item)
    normalized = tuple(reason_codes)
    if not allow_empty and not normalized:
        raise ValueError(f"{field_name} must not be empty")
    return normalized


def _is_reason_code(value: str) -> bool:
    if not value or value.strip() != value:
        return False
    return all(char.islower() or char.isdigit() or char == "_" for char in value)


def _redacted_ref(value: str) -> str:
    if _is_safe_ref(value):
        return value
    digest = hashlib.sha256(value.encode("utf-8")).hexdigest()
    return f"{HASH_PREFIX}{digest}"


def _require_redacted_ref(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if value.startswith(HASH_PREFIX):
        digest = value.removeprefix(HASH_PREFIX)
        if len(digest) != 64 or any(char not in "0123456789abcdef" for char in digest):
            raise ValueError(f"{field_name} must be a sha256 digest")
        return
    if not _is_safe_ref(value):
        raise ValueError(f"{field_name} must be redacted")


def _is_safe_ref(value: str) -> bool:
    lowered = value.lower()
    if any(fragment in lowered for fragment in SENSITIVE_TEXT_FRAGMENTS):
        return False
    return all(char.islower() or char.isdigit() or char in "-_" for char in value)


__all__ = (
    "DEFAULT_RESEARCH_STRATEGY_EDGE_DECAY_MONITOR_REPORT_CONFIG_VERSION",
    "ResearchStrategyEdgeDecayMonitorConfig",
    "ResearchStrategyEdgeDecayMonitorInput",
    "ResearchStrategyEdgeDecayMonitorReasonCodeCount",
    "ResearchStrategyEdgeDecayMonitorReport",
    "ResearchStrategyEdgeDecayMonitorRow",
    "build_research_strategy_edge_decay_monitor_report",
    "research_strategy_edge_decay_monitor_report_digest",
    "research_strategy_edge_decay_monitor_report_payload",
)
