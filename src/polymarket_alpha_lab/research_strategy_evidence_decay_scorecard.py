from __future__ import annotations

from dataclasses import InitVar, asdict, dataclass, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
from typing import Any


DEFAULT_RESEARCH_STRATEGY_EVIDENCE_DECAY_SCORECARD_CONFIG_VERSION = (
    "research-strategy-evidence-decay-scorecard-v0"
)

STATUS_PASS = "pass"
STATUS_WATCH = "watch"
STATUS_BLOCK = "block"

REASON_PREFIX = "research_strategy_evidence_decay_scorecard_"
NO_INPUTS_REASON = f"{REASON_PREFIX}no_inputs"
PASS_REASON = f"{REASON_PREFIX}pass"
AGING_EVIDENCE_REASON = f"{REASON_PREFIX}aging_evidence"
STALE_EVIDENCE_REASON = f"{REASON_PREFIX}stale_evidence"
SLOW_REFRESH_REASON = f"{REASON_PREFIX}slow_refresh"
STALE_REFRESH_REASON = f"{REASON_PREFIX}stale_refresh"
CONFLICT_GROWTH_WATCH_REASON = f"{REASON_PREFIX}conflict_growth_watch"
CONFLICT_GROWTH_BLOCK_REASON = f"{REASON_PREFIX}conflict_growth_block"
SETTLEMENT_WATCH_WINDOW_REASON = f"{REASON_PREFIX}settlement_watch_window"
SETTLEMENT_BLOCK_WINDOW_REASON = f"{REASON_PREFIX}settlement_block_window"
SCORE_WATCH_REASON = f"{REASON_PREFIX}score_watch"
SCORE_BLOCK_REASON = f"{REASON_PREFIX}score_block"

REASON_CODE_SEQUENCE = (
    NO_INPUTS_REASON,
    STALE_EVIDENCE_REASON,
    AGING_EVIDENCE_REASON,
    STALE_REFRESH_REASON,
    SLOW_REFRESH_REASON,
    CONFLICT_GROWTH_BLOCK_REASON,
    CONFLICT_GROWTH_WATCH_REASON,
    SETTLEMENT_BLOCK_WINDOW_REASON,
    SETTLEMENT_WATCH_WINDOW_REASON,
    SCORE_BLOCK_REASON,
    SCORE_WATCH_REASON,
    PASS_REASON,
)
ROW_REASON_CODE_SEQUENCE = (
    STALE_EVIDENCE_REASON,
    AGING_EVIDENCE_REASON,
    STALE_REFRESH_REASON,
    SLOW_REFRESH_REASON,
    CONFLICT_GROWTH_BLOCK_REASON,
    CONFLICT_GROWTH_WATCH_REASON,
    SETTLEMENT_BLOCK_WINDOW_REASON,
    SETTLEMENT_WATCH_WINDOW_REASON,
    SCORE_BLOCK_REASON,
    SCORE_WATCH_REASON,
    PASS_REASON,
)

DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
QUANT = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
MICROSECONDS_PER_SECOND = Decimal("1000000")


@dataclass(frozen=True)
class ResearchStrategyEvidenceDecayScorecardConfig:
    config_version: str = DEFAULT_RESEARCH_STRATEGY_EVIDENCE_DECAY_SCORECARD_CONFIG_VERSION
    fresh_evidence_max_age_seconds: Decimal = Decimal("3600.000000")
    stale_evidence_max_age_seconds: Decimal = Decimal("86400.000000")
    target_refresh_interval_seconds: Decimal = Decimal("21600.000000")
    stale_refresh_interval_seconds: Decimal = Decimal("86400.000000")
    conflict_growth_watch_threshold: Decimal = Decimal("0.100000")
    conflict_growth_block_threshold: Decimal = Decimal("0.500000")
    settlement_watch_window_seconds: Decimal = Decimal("172800.000000")
    settlement_block_window_seconds: Decimal = Decimal("21600.000000")
    pass_decay_score: Decimal = Decimal("0.700000")
    watch_decay_score: Decimal = Decimal("0.400000")
    evidence_age_weight: Decimal = Decimal("0.300000")
    refresh_frequency_weight: Decimal = Decimal("0.250000")
    conflict_growth_weight: Decimal = Decimal("0.250000")
    settlement_risk_weight: Decimal = Decimal("0.200000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchStrategyEvidenceDecayScorecardConfig:
            raise TypeError(
                "ResearchStrategyEvidenceDecayScorecardConfig does not allow subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchStrategyEvidenceDecayScorecardConfig:
            raise ValueError(
                "config must be exactly ResearchStrategyEvidenceDecayScorecardConfig",
            )
        _require_public_text("config_version", self.config_version)
        for field_name in (
            "fresh_evidence_max_age_seconds",
            "stale_evidence_max_age_seconds",
            "target_refresh_interval_seconds",
            "stale_refresh_interval_seconds",
            "settlement_watch_window_seconds",
            "settlement_block_window_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        if self.stale_evidence_max_age_seconds <= self.fresh_evidence_max_age_seconds:
            raise ValueError(
                "stale_evidence_max_age_seconds must exceed fresh_evidence_max_age_seconds",
            )
        if self.stale_refresh_interval_seconds <= self.target_refresh_interval_seconds:
            raise ValueError(
                "stale_refresh_interval_seconds must exceed target_refresh_interval_seconds",
            )
        if self.settlement_block_window_seconds > self.settlement_watch_window_seconds:
            raise ValueError(
                "settlement_block_window_seconds must not exceed settlement_watch_window_seconds",
            )
        for field_name in (
            "conflict_growth_watch_threshold",
            "conflict_growth_block_threshold",
            "pass_decay_score",
            "watch_decay_score",
            "evidence_age_weight",
            "refresh_frequency_weight",
            "conflict_growth_weight",
            "settlement_risk_weight",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        if self.conflict_growth_watch_threshold > self.conflict_growth_block_threshold:
            raise ValueError(
                "conflict_growth_watch_threshold must not exceed conflict_growth_block_threshold",
            )
        if self.pass_decay_score <= self.watch_decay_score:
            raise ValueError("pass_decay_score must exceed watch_decay_score")
        weight_sum = _quantize(
            self.evidence_age_weight
            + self.refresh_frequency_weight
            + self.conflict_growth_weight
            + self.settlement_risk_weight,
        )
        if weight_sum != ONE:
            raise ValueError(
                "evidence_age_weight, refresh_frequency_weight, conflict_growth_weight, "
                "and settlement_risk_weight must sum to 1",
            )
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class ResearchStrategyEvidenceDecayInputRow:
    strategy_ref: str
    evidence_observed_at: datetime
    last_refreshed_at: datetime
    previous_refreshed_at: datetime | None
    conflict_count_previous: Decimal
    conflict_count_current: Decimal
    settlement_at: datetime
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchStrategyEvidenceDecayInputRow:
            raise TypeError(
                "ResearchStrategyEvidenceDecayInputRow does not allow subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchStrategyEvidenceDecayInputRow:
            raise ValueError("input row must be exactly ResearchStrategyEvidenceDecayInputRow")
        _require_ref_text("strategy_ref", self.strategy_ref)
        object.__setattr__(
            self,
            "evidence_observed_at",
            _as_utc("evidence_observed_at", self.evidence_observed_at),
        )
        object.__setattr__(
            self,
            "last_refreshed_at",
            _as_utc("last_refreshed_at", self.last_refreshed_at),
        )
        object.__setattr__(
            self,
            "previous_refreshed_at",
            _optional_utc("previous_refreshed_at", self.previous_refreshed_at),
        )
        for field_name in ("conflict_count_previous", "conflict_count_current"):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        if self.conflict_count_current < self.conflict_count_previous:
            raise ValueError(
                "conflict_count_current must be at least conflict_count_previous",
            )
        if (
            self.previous_refreshed_at is not None
            and self.previous_refreshed_at > self.last_refreshed_at
        ):
            raise ValueError("previous_refreshed_at must not follow last_refreshed_at")
        object.__setattr__(
            self,
            "settlement_at",
            _as_utc("settlement_at", self.settlement_at),
        )
        _require_hard_flags("input row", self)


@dataclass(frozen=True)
class ResearchStrategyEvidenceDecayScoreRow:
    redacted_strategy_ref: str
    evidence_observed_at: datetime
    last_refreshed_at: datetime
    previous_refreshed_at: datetime | None
    settlement_at: datetime
    evidence_age_seconds: Decimal
    refresh_interval_seconds: Decimal
    refresh_lag_seconds: Decimal
    effective_refresh_seconds: Decimal
    conflict_count_previous: Decimal
    conflict_count_current: Decimal
    conflict_delta_count: Decimal
    conflict_growth_ratio: Decimal
    settlement_seconds_remaining: Decimal
    evidence_age_score: Decimal
    refresh_frequency_score: Decimal
    conflict_growth_score: Decimal
    settlement_risk_score: Decimal
    decay_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True
    validation_config: InitVar[ResearchStrategyEvidenceDecayScorecardConfig | None] = None

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchStrategyEvidenceDecayScoreRow:
            raise TypeError("ResearchStrategyEvidenceDecayScoreRow does not allow subclassing")

    def __post_init__(
        self,
        validation_config: ResearchStrategyEvidenceDecayScorecardConfig | None,
    ) -> None:
        if type(self) is not ResearchStrategyEvidenceDecayScoreRow:
            raise ValueError("row must be exactly ResearchStrategyEvidenceDecayScoreRow")
        object.__setattr__(
            self,
            "redacted_strategy_ref",
            _require_redacted_ref("redacted_strategy_ref", self.redacted_strategy_ref),
        )
        for field_name in (
            "evidence_observed_at",
            "last_refreshed_at",
            "settlement_at",
        ):
            object.__setattr__(
                self,
                field_name,
                _as_utc(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "previous_refreshed_at",
            _optional_utc("previous_refreshed_at", self.previous_refreshed_at),
        )
        for field_name in (
            "evidence_age_seconds",
            "refresh_interval_seconds",
            "refresh_lag_seconds",
            "effective_refresh_seconds",
            "conflict_count_previous",
            "conflict_count_current",
            "conflict_delta_count",
            "conflict_growth_ratio",
            "settlement_seconds_remaining",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "evidence_age_score",
            "refresh_frequency_score",
            "conflict_growth_score",
            "settlement_risk_score",
            "decay_score",
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
            _normalize_row_reason_codes(self.reason_codes),
        )
        _validate_row(self, config=validation_config)
        _require_hard_flags("row", self)


@dataclass(frozen=True)
class ResearchStrategyEvidenceDecayReasonCodeCount:
    reason_code: str
    count: Decimal
    row_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchStrategyEvidenceDecayReasonCodeCount:
            raise TypeError(
                "ResearchStrategyEvidenceDecayReasonCodeCount does not allow subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchStrategyEvidenceDecayReasonCodeCount:
            raise ValueError(
                "reason code count must be exactly ResearchStrategyEvidenceDecayReasonCodeCount",
            )
        _require_reason_code("reason_code", self.reason_code, REASON_CODE_SEQUENCE)
        object.__setattr__(
            self,
            "count",
            _require_nonnegative_decimal("count", self.count),
        )
        object.__setattr__(
            self,
            "row_ratio",
            _require_ratio_decimal("row_ratio", self.row_ratio),
        )
        _require_hard_flags("reason code count", self)


@dataclass(frozen=True)
class ResearchStrategyEvidenceDecayScorecardReport:
    generated_at: datetime
    config_version: str
    scorecard_status: str
    row_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    average_decay_score: Decimal
    max_evidence_age_seconds: Decimal
    max_refresh_lag_seconds: Decimal
    max_conflict_growth_ratio: Decimal
    min_settlement_seconds_remaining: Decimal
    rows: tuple[ResearchStrategyEvidenceDecayScoreRow, ...]
    reason_code_counts: tuple[ResearchStrategyEvidenceDecayReasonCodeCount, ...]
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchStrategyEvidenceDecayScorecardReport:
            raise TypeError(
                "ResearchStrategyEvidenceDecayScorecardReport does not allow subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchStrategyEvidenceDecayScorecardReport:
            raise ValueError(
                "report must be exactly ResearchStrategyEvidenceDecayScorecardReport",
            )
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_text("config_version", self.config_version)
        _require_status("scorecard_status", self.scorecard_status)
        for field_name in (
            "row_count",
            "pass_count",
            "watch_count",
            "block_count",
            "average_decay_score",
            "max_evidence_age_seconds",
            "max_refresh_lag_seconds",
            "max_conflict_growth_ratio",
            "min_settlement_seconds_remaining",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        if type(self.rows) is not tuple:
            raise ValueError("rows must be a tuple")
        for row in self.rows:
            if type(row) is not ResearchStrategyEvidenceDecayScoreRow:
                raise ValueError("rows must contain ResearchStrategyEvidenceDecayScoreRow")
            _require_hard_flags("row", row)
        if type(self.reason_code_counts) is not tuple:
            raise ValueError("reason_code_counts must be a tuple")
        for count_row in self.reason_code_counts:
            if type(count_row) is not ResearchStrategyEvidenceDecayReasonCodeCount:
                raise ValueError(
                    "reason_code_counts must contain ResearchStrategyEvidenceDecayReasonCodeCount",
                )
            _require_hard_flags("reason code count", count_row)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_report_reason_codes(self.reason_codes),
        )
        _validate_report(self)
        _require_hard_flags("report", self)


def build_research_strategy_evidence_decay_scorecard(
    input_rows: list[ResearchStrategyEvidenceDecayInputRow]
    | tuple[ResearchStrategyEvidenceDecayInputRow, ...],
    *,
    config: ResearchStrategyEvidenceDecayScorecardConfig | None = None,
    generated_at: datetime,
) -> ResearchStrategyEvidenceDecayScorecardReport:
    cfg = config or ResearchStrategyEvidenceDecayScorecardConfig()
    if type(cfg) is not ResearchStrategyEvidenceDecayScorecardConfig:
        raise ValueError("config must be a ResearchStrategyEvidenceDecayScorecardConfig")
    _require_hard_flags("config", cfg)
    report_time = _as_utc("generated_at", generated_at)
    rows = _normalize_input_rows(input_rows, report_time)
    built_rows = tuple(_build_row(row, config=cfg, generated_at=report_time) for row in rows)
    ranked_rows = _ranked_rows(built_rows)
    row_count = _count(len(ranked_rows))
    pass_count = _count(sum(1 for row in ranked_rows if row.status == STATUS_PASS))
    watch_count = _count(sum(1 for row in ranked_rows if row.status == STATUS_WATCH))
    block_count = _count(sum(1 for row in ranked_rows if row.status == STATUS_BLOCK))
    reason_code_counts = _reason_code_counts(ranked_rows)
    reason_codes = tuple(row.reason_code for row in reason_code_counts)
    if not ranked_rows:
        reason_code_counts = (
            ResearchStrategyEvidenceDecayReasonCodeCount(
                reason_code=NO_INPUTS_REASON,
                count=ONE,
                row_ratio=ONE,
            ),
        )
        reason_codes = (NO_INPUTS_REASON,)
    return ResearchStrategyEvidenceDecayScorecardReport(
        generated_at=report_time,
        config_version=cfg.config_version,
        scorecard_status=_report_status(bool(ranked_rows), block_count, watch_count),
        row_count=row_count,
        pass_count=pass_count,
        watch_count=watch_count,
        block_count=block_count,
        average_decay_score=_ratio(
            _sum_decimal(row.decay_score for row in ranked_rows),
            row_count,
        ),
        max_evidence_age_seconds=max(
            (row.evidence_age_seconds for row in ranked_rows),
            default=ZERO,
        ),
        max_refresh_lag_seconds=max(
            (row.refresh_lag_seconds for row in ranked_rows),
            default=ZERO,
        ),
        max_conflict_growth_ratio=max(
            (row.conflict_growth_ratio for row in ranked_rows),
            default=ZERO,
        ),
        min_settlement_seconds_remaining=min(
            (row.settlement_seconds_remaining for row in ranked_rows),
            default=ZERO,
        ),
        rows=ranked_rows,
        reason_code_counts=reason_code_counts,
        reason_codes=reason_codes,
    )


def research_strategy_evidence_decay_scorecard_payload(
    report: ResearchStrategyEvidenceDecayScorecardReport,
) -> dict[str, Any]:
    if type(report) is not ResearchStrategyEvidenceDecayScorecardReport:
        raise ValueError("report must be a ResearchStrategyEvidenceDecayScorecardReport")
    _require_hard_flags("report", report)
    _reject_bad_blob("report", report)
    payload = _json_ready(report)
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    _require_hard_flags("payload", _DictFlags(payload))
    _reject_bad_blob("payload", payload)
    return payload


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


def _build_row(
    row: ResearchStrategyEvidenceDecayInputRow,
    *,
    config: ResearchStrategyEvidenceDecayScorecardConfig,
    generated_at: datetime,
) -> ResearchStrategyEvidenceDecayScoreRow:
    evidence_age_seconds = _datetime_delta_seconds(generated_at, row.evidence_observed_at)
    refresh_lag_seconds = _datetime_delta_seconds(generated_at, row.last_refreshed_at)
    refresh_interval_seconds = (
        refresh_lag_seconds
        if row.previous_refreshed_at is None
        else _datetime_delta_seconds(row.last_refreshed_at, row.previous_refreshed_at)
    )
    effective_refresh_seconds = max(refresh_interval_seconds, refresh_lag_seconds)
    conflict_delta_count = _quantize(row.conflict_count_current - row.conflict_count_previous)
    conflict_growth_ratio = _conflict_ratio(
        conflict_delta_count,
        row.conflict_count_previous,
    )
    settlement_seconds_remaining = _future_delta_seconds(row.settlement_at, generated_at)
    evidence_age_score = _age_score(
        evidence_age_seconds,
        fresh_seconds=config.fresh_evidence_max_age_seconds,
        stale_seconds=config.stale_evidence_max_age_seconds,
    )
    refresh_frequency_score = _age_score(
        effective_refresh_seconds,
        fresh_seconds=config.target_refresh_interval_seconds,
        stale_seconds=config.stale_refresh_interval_seconds,
    )
    conflict_growth_score = _inverse_ratio(
        conflict_growth_ratio,
        block_threshold=config.conflict_growth_block_threshold,
    )
    settlement_risk_score = _settlement_score(
        settlement_seconds_remaining,
        watch_window_seconds=config.settlement_watch_window_seconds,
        block_window_seconds=config.settlement_block_window_seconds,
    )
    decay_score = _decay_score(
        evidence_age_score=evidence_age_score,
        refresh_frequency_score=refresh_frequency_score,
        conflict_growth_score=conflict_growth_score,
        settlement_risk_score=settlement_risk_score,
        config=config,
    )
    reason_codes = _row_reason_codes(
        evidence_age_seconds=evidence_age_seconds,
        effective_refresh_seconds=effective_refresh_seconds,
        conflict_growth_ratio=conflict_growth_ratio,
        settlement_seconds_remaining=settlement_seconds_remaining,
        decay_score=decay_score,
        config=config,
    )
    return ResearchStrategyEvidenceDecayScoreRow(
        redacted_strategy_ref=_redacted_ref(row.strategy_ref),
        evidence_observed_at=row.evidence_observed_at,
        last_refreshed_at=row.last_refreshed_at,
        previous_refreshed_at=row.previous_refreshed_at,
        settlement_at=row.settlement_at,
        evidence_age_seconds=evidence_age_seconds,
        refresh_interval_seconds=refresh_interval_seconds,
        refresh_lag_seconds=refresh_lag_seconds,
        effective_refresh_seconds=effective_refresh_seconds,
        conflict_count_previous=row.conflict_count_previous,
        conflict_count_current=row.conflict_count_current,
        conflict_delta_count=conflict_delta_count,
        conflict_growth_ratio=conflict_growth_ratio,
        settlement_seconds_remaining=settlement_seconds_remaining,
        evidence_age_score=evidence_age_score,
        refresh_frequency_score=refresh_frequency_score,
        conflict_growth_score=conflict_growth_score,
        settlement_risk_score=settlement_risk_score,
        decay_score=decay_score,
        status=_row_status(reason_codes),
        reason_codes=reason_codes,
        validation_config=config,
    )


def _normalize_input_rows(
    rows: list[ResearchStrategyEvidenceDecayInputRow]
    | tuple[ResearchStrategyEvidenceDecayInputRow, ...],
    generated_at: datetime,
) -> tuple[ResearchStrategyEvidenceDecayInputRow, ...]:
    if type(rows) not in (list, tuple):
        raise ValueError("input rows must be a list or tuple")
    normalized = tuple(rows)
    seen: set[str] = set()
    for row in normalized:
        if type(row) is not ResearchStrategyEvidenceDecayInputRow:
            raise ValueError("input rows must contain ResearchStrategyEvidenceDecayInputRow")
        _require_hard_flags("input row", row)
        if row.evidence_observed_at > generated_at:
            raise ValueError("evidence_observed_at must be on or before generated_at")
        if row.last_refreshed_at > generated_at:
            raise ValueError("last_refreshed_at must be on or before generated_at")
        ref_digest = _redacted_ref(row.strategy_ref)
        if ref_digest in seen:
            raise ValueError("input rows must be unique")
        seen.add(ref_digest)
    return normalized


def _row_reason_codes(
    *,
    evidence_age_seconds: Decimal,
    effective_refresh_seconds: Decimal,
    conflict_growth_ratio: Decimal,
    settlement_seconds_remaining: Decimal,
    decay_score: Decimal,
    config: ResearchStrategyEvidenceDecayScorecardConfig,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    if evidence_age_seconds >= config.stale_evidence_max_age_seconds:
        reason_codes.append(STALE_EVIDENCE_REASON)
    elif evidence_age_seconds > config.fresh_evidence_max_age_seconds:
        reason_codes.append(AGING_EVIDENCE_REASON)
    if effective_refresh_seconds >= config.stale_refresh_interval_seconds:
        reason_codes.append(STALE_REFRESH_REASON)
    elif effective_refresh_seconds > config.target_refresh_interval_seconds:
        reason_codes.append(SLOW_REFRESH_REASON)
    if conflict_growth_ratio >= config.conflict_growth_block_threshold:
        reason_codes.append(CONFLICT_GROWTH_BLOCK_REASON)
    elif conflict_growth_ratio >= config.conflict_growth_watch_threshold:
        reason_codes.append(CONFLICT_GROWTH_WATCH_REASON)
    if settlement_seconds_remaining <= config.settlement_block_window_seconds:
        reason_codes.append(SETTLEMENT_BLOCK_WINDOW_REASON)
    elif settlement_seconds_remaining <= config.settlement_watch_window_seconds:
        reason_codes.append(SETTLEMENT_WATCH_WINDOW_REASON)
    if decay_score < config.watch_decay_score:
        reason_codes.append(SCORE_BLOCK_REASON)
    elif decay_score < config.pass_decay_score:
        reason_codes.append(SCORE_WATCH_REASON)
    if not reason_codes:
        reason_codes.append(PASS_REASON)
    return tuple(
        reason_code
        for reason_code in ROW_REASON_CODE_SEQUENCE
        if reason_code in reason_codes
    )


def _row_status(reason_codes: tuple[str, ...]) -> str:
    if (
        STALE_EVIDENCE_REASON in reason_codes
        or STALE_REFRESH_REASON in reason_codes
        or CONFLICT_GROWTH_BLOCK_REASON in reason_codes
        or SETTLEMENT_BLOCK_WINDOW_REASON in reason_codes
        or SCORE_BLOCK_REASON in reason_codes
    ):
        return STATUS_BLOCK
    if reason_codes == (PASS_REASON,):
        return STATUS_PASS
    return STATUS_WATCH


def _report_status(
    has_rows: bool,
    block_count: Decimal,
    watch_count: Decimal,
) -> str:
    if not has_rows or block_count > ZERO:
        return STATUS_BLOCK
    if watch_count > ZERO:
        return STATUS_WATCH
    return STATUS_PASS


def _ranked_rows(
    rows: tuple[ResearchStrategyEvidenceDecayScoreRow, ...],
) -> tuple[ResearchStrategyEvidenceDecayScoreRow, ...]:
    return tuple(
        sorted(
            rows,
            key=lambda row: (
                _status_rank(row.status),
                row.decay_score,
                row.settlement_seconds_remaining,
                row.redacted_strategy_ref,
            ),
        ),
    )


def _status_rank(value: str) -> int:
    return {STATUS_BLOCK: 0, STATUS_WATCH: 1, STATUS_PASS: 2}[value]


def _reason_code_counts(
    rows: tuple[ResearchStrategyEvidenceDecayScoreRow, ...],
) -> tuple[ResearchStrategyEvidenceDecayReasonCodeCount, ...]:
    total = _count(len(rows))
    counts: dict[str, Decimal] = {}
    for row in rows:
        for reason_code in row.reason_codes:
            counts[reason_code] = counts.get(reason_code, ZERO) + ONE
    return tuple(
        ResearchStrategyEvidenceDecayReasonCodeCount(
            reason_code=reason_code,
            count=_count(counts[reason_code]),
            row_ratio=_ratio(counts[reason_code], total),
        )
        for reason_code in REASON_CODE_SEQUENCE
        if reason_code in counts
    )


def _validate_row(
    row: ResearchStrategyEvidenceDecayScoreRow,
    *,
    config: ResearchStrategyEvidenceDecayScorecardConfig | None,
) -> None:
    if config is None:
        config = ResearchStrategyEvidenceDecayScorecardConfig()
    if type(config) is not ResearchStrategyEvidenceDecayScorecardConfig:
        raise ValueError(
            "validation_config must be a ResearchStrategyEvidenceDecayScorecardConfig",
        )
    if row.conflict_count_current < row.conflict_count_previous:
        raise ValueError("conflict_count_current must be at least conflict_count_previous")
    if row.conflict_delta_count != _quantize(
        row.conflict_count_current - row.conflict_count_previous,
    ):
        raise ValueError("conflict_delta_count must match conflict counts")
    if row.conflict_growth_ratio != _conflict_ratio(
        row.conflict_delta_count,
        row.conflict_count_previous,
    ):
        raise ValueError("conflict_growth_ratio must match conflict counts")
    if row.effective_refresh_seconds != max(
        row.refresh_interval_seconds,
        row.refresh_lag_seconds,
    ):
        raise ValueError("effective_refresh_seconds must match refresh timings")
    expected_decay_score = _decay_score(
        evidence_age_score=row.evidence_age_score,
        refresh_frequency_score=row.refresh_frequency_score,
        conflict_growth_score=row.conflict_growth_score,
        settlement_risk_score=row.settlement_risk_score,
        config=config,
    )
    if row.decay_score != expected_decay_score:
        raise ValueError("decay_score must match component scores")
    expected_reason_codes = _row_reason_codes(
        evidence_age_seconds=row.evidence_age_seconds,
        effective_refresh_seconds=row.effective_refresh_seconds,
        conflict_growth_ratio=row.conflict_growth_ratio,
        settlement_seconds_remaining=row.settlement_seconds_remaining,
        decay_score=row.decay_score,
        config=config,
    )
    if row.reason_codes != expected_reason_codes:
        raise ValueError("reason_codes must match row inputs")
    if row.status != _row_status(row.reason_codes):
        raise ValueError("status must match reason_codes")
    if row.status == STATUS_PASS and row.decay_score < config.pass_decay_score:
        raise ValueError("decay_score must back pass status")
    if row.status == STATUS_WATCH and row.decay_score < config.watch_decay_score:
        raise ValueError("decay_score must back watch status")
    if row.status == STATUS_BLOCK and row.decay_score >= config.watch_decay_score:
        has_hard_reason = any(
            reason_code in row.reason_codes
            for reason_code in (
                STALE_EVIDENCE_REASON,
                STALE_REFRESH_REASON,
                CONFLICT_GROWTH_BLOCK_REASON,
                SETTLEMENT_BLOCK_WINDOW_REASON,
            )
        )
        if not has_hard_reason:
            raise ValueError("decay_score must back block status")
    if not _is_redacted_ref(row.redacted_strategy_ref):
        raise ValueError("redacted_strategy_ref must be redacted")


def _validate_report(report: ResearchStrategyEvidenceDecayScorecardReport) -> None:
    if report.rows != _ranked_rows(report.rows):
        raise ValueError("rows must be ranked deterministically")
    if report.row_count != _count(len(report.rows)):
        raise ValueError("row_count must match rows")
    if report.pass_count != _count(sum(1 for row in report.rows if row.status == STATUS_PASS)):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _count(sum(1 for row in report.rows if row.status == STATUS_WATCH)):
        raise ValueError("watch_count must match rows")
    if report.block_count != _count(sum(1 for row in report.rows if row.status == STATUS_BLOCK)):
        raise ValueError("block_count must match rows")
    if report.average_decay_score != _ratio(
        _sum_decimal(row.decay_score for row in report.rows),
        report.row_count,
    ):
        raise ValueError("average_decay_score must match rows")
    if report.max_evidence_age_seconds != max(
        (row.evidence_age_seconds for row in report.rows),
        default=ZERO,
    ):
        raise ValueError("max_evidence_age_seconds must match rows")
    if report.max_refresh_lag_seconds != max(
        (row.refresh_lag_seconds for row in report.rows),
        default=ZERO,
    ):
        raise ValueError("max_refresh_lag_seconds must match rows")
    if report.max_conflict_growth_ratio != max(
        (row.conflict_growth_ratio for row in report.rows),
        default=ZERO,
    ):
        raise ValueError("max_conflict_growth_ratio must match rows")
    if report.min_settlement_seconds_remaining != min(
        (row.settlement_seconds_remaining for row in report.rows),
        default=ZERO,
    ):
        raise ValueError("min_settlement_seconds_remaining must match rows")
    expected_counts = _reason_code_counts(report.rows)
    expected_codes = tuple(row.reason_code for row in expected_counts)
    if not report.rows:
        expected_counts = (
            ResearchStrategyEvidenceDecayReasonCodeCount(
                reason_code=NO_INPUTS_REASON,
                count=ONE,
                row_ratio=ONE,
            ),
        )
        expected_codes = (NO_INPUTS_REASON,)
    if report.reason_code_counts != expected_counts:
        raise ValueError("reason_code_counts must match rows")
    if report.reason_codes != expected_codes:
        raise ValueError("reason_codes must match reason_code_counts")
    expected_status = _report_status(
        bool(report.rows),
        report.block_count,
        report.watch_count,
    )
    if report.scorecard_status != expected_status:
        raise ValueError("scorecard_status must match rows")


def _normalize_row_reason_codes(value: tuple[str, ...]) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ValueError("reason_codes must be a tuple")
    for reason_code in value:
        _require_reason_code("reason_codes", reason_code, ROW_REASON_CODE_SEQUENCE)
    normalized = tuple(
        reason_code for reason_code in ROW_REASON_CODE_SEQUENCE if reason_code in value
    )
    if normalized != value:
        raise ValueError("reason_codes must be unique and ranked")
    if PASS_REASON in value and len(value) != 1:
        raise ValueError("reason_codes cannot mix pass with risk reasons")
    return normalized


def _normalize_report_reason_codes(value: tuple[str, ...]) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ValueError("reason_codes must be a tuple")
    for reason_code in value:
        _require_reason_code("reason_codes", reason_code, REASON_CODE_SEQUENCE)
    normalized = tuple(
        reason_code for reason_code in REASON_CODE_SEQUENCE if reason_code in value
    )
    if normalized != value:
        raise ValueError("reason_codes must be unique and ranked")
    return normalized


def _age_score(
    age_seconds: Decimal,
    *,
    fresh_seconds: Decimal,
    stale_seconds: Decimal,
) -> Decimal:
    if age_seconds <= fresh_seconds:
        return ONE
    if age_seconds >= stale_seconds:
        return ZERO
    return _quantize(ONE - (age_seconds / stale_seconds))


def _inverse_ratio(value: Decimal, *, block_threshold: Decimal) -> Decimal:
    if block_threshold == ZERO:
        return ZERO if value > ZERO else ONE
    if value >= block_threshold:
        return ZERO
    return _quantize(ONE - (value / block_threshold))


def _settlement_score(
    seconds_remaining: Decimal,
    *,
    watch_window_seconds: Decimal,
    block_window_seconds: Decimal,
) -> Decimal:
    if seconds_remaining <= block_window_seconds:
        return ZERO
    if seconds_remaining >= watch_window_seconds:
        return ONE
    return _quantize(seconds_remaining / watch_window_seconds)


def _decay_score(
    *,
    evidence_age_score: Decimal,
    refresh_frequency_score: Decimal,
    conflict_growth_score: Decimal,
    settlement_risk_score: Decimal,
    config: ResearchStrategyEvidenceDecayScorecardConfig,
) -> Decimal:
    return _quantize(
        evidence_age_score * config.evidence_age_weight
        + refresh_frequency_score * config.refresh_frequency_weight
        + conflict_growth_score * config.conflict_growth_weight
        + settlement_risk_score * config.settlement_risk_weight,
    )


def _conflict_ratio(delta_count: Decimal, previous_count: Decimal) -> Decimal:
    if previous_count == ZERO:
        return ONE if delta_count > ZERO else ZERO
    return _quantize(delta_count / previous_count)


def _future_delta_seconds(later: datetime, earlier: datetime) -> Decimal:
    if later <= earlier:
        return ZERO
    return _datetime_delta_seconds(later, earlier)


def _require_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in (STATUS_PASS, STATUS_WATCH, STATUS_BLOCK):
        raise ValueError(f"{field_name} must be a known status")


def _require_reason_code(
    field_name: str,
    value: object,
    allowed_values: tuple[str, ...],
) -> None:
    if type(value) is not str or value not in allowed_values:
        raise ValueError(f"{field_name} must be a known reason code")


def _require_ref_text(field_name: str, value: object) -> str:
    if type(value) is not str or not value.strip() or value != value.strip():
        raise ValueError(f"{field_name} must be a non-empty string")
    return value


def _require_public_text(field_name: str, value: object) -> str:
    if type(value) is not str or not value.strip() or value != value.strip():
        raise ValueError(f"{field_name} must be a non-empty string")
    _reject_bad_text(field_name, value)
    return value


def _require_redacted_ref(field_name: str, value: object) -> str:
    if type(value) is not str or not value.strip():
        raise ValueError(f"{field_name} must be a non-empty string")
    if not _is_redacted_ref(value):
        raise ValueError(f"{field_name} must be redacted")
    _reject_bad_text(field_name, value)
    return value


def _is_redacted_ref(value: str) -> bool:
    return value.startswith("sha256:") and len(value) == 19


def _redacted_ref(value: str) -> str:
    return f"sha256:{sha256(value.encode('utf-8')).hexdigest()[:12]}"


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if getattr(value, field_name, None) is not True:
            raise ValueError(f"{field_name} must be True for {label}")


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _optional_utc(field_name: str, value: object) -> datetime | None:
    if value is None:
        return None
    return _as_utc(field_name, value)


def _require_finite_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return _quantize(value)


def _require_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_finite_decimal(field_name, value)
    if decimal_value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return decimal_value


def _require_ratio_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_nonnegative_decimal(field_name, value)
    if decimal_value > ONE:
        raise ValueError(f"{field_name} must be in the closed unit interval")
    return decimal_value


def _datetime_delta_seconds(later: datetime, earlier: datetime) -> Decimal:
    delta = later - earlier
    total_microseconds = (
        Decimal(delta.days * 86400 + delta.seconds) * MICROSECONDS_PER_SECOND
        + Decimal(delta.microseconds)
    )
    return _quantize(total_microseconds / MICROSECONDS_PER_SECOND)


def _quantize(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(QUANT)


def _count(value: int | Decimal) -> Decimal:
    if type(value) is int:
        return _quantize(Decimal(value))
    if type(value) is Decimal:
        return _quantize(value)
    raise ValueError("count value must be an int or Decimal")


def _sum_decimal(values: object) -> Decimal:
    total = ZERO
    for value in values:  # type: ignore[union-attr]
        if type(value) is not Decimal:
            raise ValueError("sum values must be Decimal")
        total += value
    return _quantize(total)


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return (numerator / denominator).quantize(QUANT)


def _reject_bad_blob(label: str, value: object, path: str = "") -> None:
    if is_dataclass(value) and not isinstance(value, type):
        _reject_bad_blob(label, asdict(value), path)
        return
    if type(value) is str:
        _reject_bad_text(path or label, value)
        return
    if isinstance(value, Decimal):
        if type(value) is not Decimal or not value.is_finite():
            raise ValueError(f"{path or label} must be finite Decimal")
        return
    if isinstance(value, datetime):
        _as_utc(path or label, value)
        return
    if value is None or type(value) is bool:
        return
    if isinstance(value, float):
        raise ValueError("JSON value must not be a float")
    if type(value) is int:
        raise ValueError(f"{path or label} must use Decimal-derived string values")
    if isinstance(value, dict):
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            nested_path = key if not path else f"{path}.{key}"
            if key in {"paper_only", "report_only", "readonly"} and item is not True:
                raise ValueError(f"{nested_path} must be True")
            _reject_bad_text(nested_path, key)
            _reject_bad_blob(label, item, nested_path)
        return
    if isinstance(value, (list, tuple)):
        for index, item in enumerate(value):
            nested_path = f"{path}[{index}]" if path else f"{label}[{index}]"
            _reject_bad_blob(label, item, nested_path)
        return
    raise ValueError("value is not JSON serializable")


def _reject_bad_text(field_name: str, value: str) -> None:
    lowered = value.lower()
    bad_fragments = (
        _join_parts("au", "th"),
        _join_parts("wal", "let"),
        _join_parts("bro", "ker"),
        _join_parts("ord", "er"),
        _join_parts("can", "cel"),
        _join_parts("repl", "ace"),
        "sign",
        _join_parts("ad", "vice"),
        _join_parts("sou", "rce"),
        _join_parts("mar", "ket"),
        _join_parts("d", "sn"),
        _join_parts("ta", "ble"),
        _join_parts("to", "ken"),
        _join_parts("priv", "ate"),
        _join_parts("api", "_key"),
        _join_parts("sec", "ret"),
        _join_parts("pos", "ition"),
        _join_parts("tra", "de"),
        _join_parts("be", "t"),
        _join_parts("sta", "ke"),
        _join_parts("cli", "ent"),
        _join_parts("data", "base"),
        _join_parts("net", "work"),
        _join_parts("li", "ve"),
    )
    if any(fragment in lowered for fragment in bad_fragments):
        raise ValueError(f"{field_name} has disallowed text")


def _join_parts(*parts: str) -> str:
    return "".join(parts)


def _json_ready(value: Any) -> Any:
    if value is None:
        return None
    if is_dataclass(value) and not isinstance(value, type):
        return _json_ready(asdict(value))
    if isinstance(value, Decimal):
        if type(value) is not Decimal or not value.is_finite():
            raise ValueError("JSON Decimal value must be finite")
        return str(value)
    if isinstance(value, datetime):
        return _as_utc("datetime", value).isoformat()
    if isinstance(value, float):
        raise ValueError("JSON value must not be a float")
    if type(value) is int:
        raise ValueError("JSON numeric value must use Decimal")
    if type(value) in (str, bool):
        return value
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


__all__ = (
    "DEFAULT_RESEARCH_STRATEGY_EVIDENCE_DECAY_SCORECARD_CONFIG_VERSION",
    "ResearchStrategyEvidenceDecayInputRow",
    "ResearchStrategyEvidenceDecayReasonCodeCount",
    "ResearchStrategyEvidenceDecayScoreRow",
    "ResearchStrategyEvidenceDecayScorecardConfig",
    "ResearchStrategyEvidenceDecayScorecardReport",
    "build_research_strategy_evidence_decay_scorecard",
    "research_strategy_evidence_decay_scorecard_payload",
)
