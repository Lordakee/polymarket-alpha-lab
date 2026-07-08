"""Pure report reducer for strategy signal decay dashboards."""

from __future__ import annotations

from dataclasses import InitVar, asdict, dataclass, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
from typing import Any


DEFAULT_RESEARCH_STRATEGY_SIGNAL_DECAY_DASHBOARD_CONFIG_VERSION = (
    "research-strategy-signal-decay-dashboard-report-v0"
)

STATUS_PASS = "pass"
STATUS_WATCH = "watch"
STATUS_BLOCK = "block"

REASON_PREFIX = "research_strategy_signal_decay_dashboard_"
NO_INPUTS_REASON = f"{REASON_PREFIX}no_inputs"
PASS_REASON = f"{REASON_PREFIX}pass"
AGING_SIGNAL_REASON = f"{REASON_PREFIX}aging_signal"
STALE_SIGNAL_REASON = f"{REASON_PREFIX}stale_signal"
REFRESH_FAILURE_WATCH_REASON = f"{REASON_PREFIX}refresh_failure_watch"
REFRESH_FAILURE_BLOCK_REASON = f"{REASON_PREFIX}refresh_failure_block"
DOMAIN_DIFFERENCE_WATCH_REASON = f"{REASON_PREFIX}domain_difference_watch"
DOMAIN_DIFFERENCE_BLOCK_REASON = f"{REASON_PREFIX}domain_difference_block"
SETTLEMENT_WATCH_WINDOW_REASON = f"{REASON_PREFIX}settlement_watch_window"
SETTLEMENT_BLOCK_WINDOW_REASON = f"{REASON_PREFIX}settlement_block_window"
MODEL_DISAGREEMENT_WATCH_REASON = f"{REASON_PREFIX}model_disagreement_watch"
MODEL_DISAGREEMENT_BLOCK_REASON = f"{REASON_PREFIX}model_disagreement_block"
SCORE_WATCH_REASON = f"{REASON_PREFIX}score_watch"
SCORE_BLOCK_REASON = f"{REASON_PREFIX}score_block"

REASON_CODE_SEQUENCE = (
    NO_INPUTS_REASON,
    STALE_SIGNAL_REASON,
    AGING_SIGNAL_REASON,
    REFRESH_FAILURE_BLOCK_REASON,
    REFRESH_FAILURE_WATCH_REASON,
    DOMAIN_DIFFERENCE_BLOCK_REASON,
    DOMAIN_DIFFERENCE_WATCH_REASON,
    SETTLEMENT_BLOCK_WINDOW_REASON,
    SETTLEMENT_WATCH_WINDOW_REASON,
    MODEL_DISAGREEMENT_BLOCK_REASON,
    MODEL_DISAGREEMENT_WATCH_REASON,
    SCORE_BLOCK_REASON,
    SCORE_WATCH_REASON,
    PASS_REASON,
)
ROW_REASON_CODE_SEQUENCE = (
    STALE_SIGNAL_REASON,
    AGING_SIGNAL_REASON,
    REFRESH_FAILURE_BLOCK_REASON,
    REFRESH_FAILURE_WATCH_REASON,
    DOMAIN_DIFFERENCE_BLOCK_REASON,
    DOMAIN_DIFFERENCE_WATCH_REASON,
    SETTLEMENT_BLOCK_WINDOW_REASON,
    SETTLEMENT_WATCH_WINDOW_REASON,
    MODEL_DISAGREEMENT_BLOCK_REASON,
    MODEL_DISAGREEMENT_WATCH_REASON,
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
class ResearchStrategySignalDecayDashboardConfig:
    config_version: str = DEFAULT_RESEARCH_STRATEGY_SIGNAL_DECAY_DASHBOARD_CONFIG_VERSION
    fresh_signal_max_age_seconds: Decimal = Decimal("3600.000000")
    stale_signal_max_age_seconds: Decimal = Decimal("86400.000000")
    refresh_failure_watch_threshold: Decimal = Decimal("0.100000")
    refresh_failure_block_threshold: Decimal = Decimal("0.300000")
    domain_difference_watch_threshold: Decimal = Decimal("0.250000")
    domain_difference_block_threshold: Decimal = Decimal("0.500000")
    settlement_watch_window_seconds: Decimal = Decimal("172800.000000")
    settlement_block_window_seconds: Decimal = Decimal("21600.000000")
    model_disagreement_watch_threshold: Decimal = Decimal("0.150000")
    model_disagreement_block_threshold: Decimal = Decimal("0.350000")
    pass_dashboard_score: Decimal = Decimal("0.700000")
    watch_dashboard_score: Decimal = Decimal("0.400000")
    signal_age_weight: Decimal = Decimal("0.250000")
    refresh_failure_weight: Decimal = Decimal("0.200000")
    domain_difference_weight: Decimal = Decimal("0.200000")
    settlement_window_weight: Decimal = Decimal("0.150000")
    model_disagreement_weight: Decimal = Decimal("0.200000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchStrategySignalDecayDashboardConfig:
            raise TypeError(
                "ResearchStrategySignalDecayDashboardConfig does not allow subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchStrategySignalDecayDashboardConfig:
            raise ValueError(
                "config must be exactly ResearchStrategySignalDecayDashboardConfig",
            )
        _require_public_text("config_version", self.config_version)
        for field_name in (
            "fresh_signal_max_age_seconds",
            "stale_signal_max_age_seconds",
            "settlement_watch_window_seconds",
            "settlement_block_window_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        if self.stale_signal_max_age_seconds <= self.fresh_signal_max_age_seconds:
            raise ValueError(
                "stale_signal_max_age_seconds must exceed fresh_signal_max_age_seconds",
            )
        if self.settlement_block_window_seconds > self.settlement_watch_window_seconds:
            raise ValueError(
                "settlement_block_window_seconds must not exceed "
                "settlement_watch_window_seconds",
            )
        for field_name in (
            "refresh_failure_watch_threshold",
            "refresh_failure_block_threshold",
            "domain_difference_watch_threshold",
            "domain_difference_block_threshold",
            "model_disagreement_watch_threshold",
            "model_disagreement_block_threshold",
            "pass_dashboard_score",
            "watch_dashboard_score",
            "signal_age_weight",
            "refresh_failure_weight",
            "domain_difference_weight",
            "settlement_window_weight",
            "model_disagreement_weight",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        if self.refresh_failure_watch_threshold > self.refresh_failure_block_threshold:
            raise ValueError(
                "refresh_failure_watch_threshold must not exceed "
                "refresh_failure_block_threshold",
            )
        if self.domain_difference_watch_threshold > self.domain_difference_block_threshold:
            raise ValueError(
                "domain_difference_watch_threshold must not exceed "
                "domain_difference_block_threshold",
            )
        if (
            self.model_disagreement_watch_threshold
            > self.model_disagreement_block_threshold
        ):
            raise ValueError(
                "model_disagreement_watch_threshold must not exceed "
                "model_disagreement_block_threshold",
            )
        if self.pass_dashboard_score <= self.watch_dashboard_score:
            raise ValueError("pass_dashboard_score must exceed watch_dashboard_score")
        weight_sum = _quantize(
            self.signal_age_weight
            + self.refresh_failure_weight
            + self.domain_difference_weight
            + self.settlement_window_weight
            + self.model_disagreement_weight,
        )
        if weight_sum != ONE:
            raise ValueError(
                "signal_age_weight, refresh_failure_weight, domain_difference_weight, "
                "settlement_window_weight, and model_disagreement_weight must sum to 1",
            )
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class ResearchStrategySignalDecayInputRow:
    signal_ref: str
    signal_domain: str
    expected_domain: str
    signal_observed_at: datetime
    last_refresh_attempt_at: datetime
    refresh_failure_count: Decimal
    refresh_attempt_count: Decimal
    domain_difference_score: Decimal
    settlement_at: datetime
    model_probability_low: Decimal
    model_probability_high: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchStrategySignalDecayInputRow:
            raise TypeError(
                "ResearchStrategySignalDecayInputRow does not allow subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchStrategySignalDecayInputRow:
            raise ValueError("input row must be exactly ResearchStrategySignalDecayInputRow")
        _require_ref_text("signal_ref", self.signal_ref)
        object.__setattr__(
            self,
            "signal_domain",
            _require_public_text("signal_domain", self.signal_domain),
        )
        object.__setattr__(
            self,
            "expected_domain",
            _require_public_text("expected_domain", self.expected_domain),
        )
        object.__setattr__(
            self,
            "signal_observed_at",
            _as_utc("signal_observed_at", self.signal_observed_at),
        )
        object.__setattr__(
            self,
            "last_refresh_attempt_at",
            _as_utc("last_refresh_attempt_at", self.last_refresh_attempt_at),
        )
        for field_name in ("refresh_failure_count", "refresh_attempt_count"):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        if self.refresh_failure_count > self.refresh_attempt_count:
            raise ValueError("refresh_failure_count must not exceed refresh_attempt_count")
        object.__setattr__(
            self,
            "domain_difference_score",
            _require_ratio_decimal(
                "domain_difference_score",
                self.domain_difference_score,
            ),
        )
        object.__setattr__(self, "settlement_at", _as_utc("settlement_at", self.settlement_at))
        for field_name in ("model_probability_low", "model_probability_high"):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        if self.model_probability_high < self.model_probability_low:
            raise ValueError("model_probability_high must be at least model_probability_low")
        _require_hard_flags("input row", self)


@dataclass(frozen=True)
class ResearchStrategySignalDecayDashboardRow:
    redacted_signal_ref: str
    signal_domain: str
    expected_domain: str
    signal_observed_at: datetime
    last_refresh_attempt_at: datetime
    settlement_at: datetime
    signal_age_seconds: Decimal
    refresh_lag_seconds: Decimal
    refresh_failure_count: Decimal
    refresh_attempt_count: Decimal
    refresh_failure_rate: Decimal
    domain_difference_score: Decimal
    settlement_seconds_remaining: Decimal
    model_probability_low: Decimal
    model_probability_high: Decimal
    model_disagreement_score: Decimal
    signal_age_score: Decimal
    refresh_failure_score: Decimal
    domain_alignment_score: Decimal
    settlement_window_score: Decimal
    model_consensus_score: Decimal
    dashboard_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True
    validation_config: InitVar[ResearchStrategySignalDecayDashboardConfig | None] = None

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchStrategySignalDecayDashboardRow:
            raise TypeError(
                "ResearchStrategySignalDecayDashboardRow does not allow subclassing",
            )

    def __post_init__(
        self,
        validation_config: ResearchStrategySignalDecayDashboardConfig | None,
    ) -> None:
        if type(self) is not ResearchStrategySignalDecayDashboardRow:
            raise ValueError("row must be exactly ResearchStrategySignalDecayDashboardRow")
        object.__setattr__(
            self,
            "redacted_signal_ref",
            _require_redacted_ref("redacted_signal_ref", self.redacted_signal_ref),
        )
        object.__setattr__(
            self,
            "signal_domain",
            _require_public_text("signal_domain", self.signal_domain),
        )
        object.__setattr__(
            self,
            "expected_domain",
            _require_public_text("expected_domain", self.expected_domain),
        )
        for field_name in (
            "signal_observed_at",
            "last_refresh_attempt_at",
            "settlement_at",
        ):
            object.__setattr__(
                self,
                field_name,
                _as_utc(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "signal_age_seconds",
            "refresh_lag_seconds",
            "refresh_failure_count",
            "refresh_attempt_count",
            "settlement_seconds_remaining",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "refresh_failure_rate",
            "domain_difference_score",
            "model_probability_low",
            "model_probability_high",
            "model_disagreement_score",
            "signal_age_score",
            "refresh_failure_score",
            "domain_alignment_score",
            "settlement_window_score",
            "model_consensus_score",
            "dashboard_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        if self.refresh_failure_count > self.refresh_attempt_count:
            raise ValueError("refresh_failure_count must not exceed refresh_attempt_count")
        if self.model_probability_high < self.model_probability_low:
            raise ValueError("model_probability_high must be at least model_probability_low")
        _require_status("status", self.status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_row_reason_codes(self.reason_codes),
        )
        _validate_row(self, config=validation_config)
        _require_hard_flags("row", self)


@dataclass(frozen=True)
class ResearchStrategySignalDecayDashboardReasonCodeCount:
    reason_code: str
    count: Decimal
    row_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchStrategySignalDecayDashboardReasonCodeCount:
            raise TypeError(
                "ResearchStrategySignalDecayDashboardReasonCodeCount does not allow "
                "subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchStrategySignalDecayDashboardReasonCodeCount:
            raise ValueError(
                "reason code count must be exactly "
                "ResearchStrategySignalDecayDashboardReasonCodeCount",
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
class ResearchStrategySignalDecayDashboardReport:
    generated_at: datetime
    config_version: str
    dashboard_status: str
    row_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    average_dashboard_score: Decimal
    max_signal_age_seconds: Decimal
    max_refresh_failure_rate: Decimal
    max_domain_difference_score: Decimal
    min_settlement_seconds_remaining: Decimal
    max_model_disagreement_score: Decimal
    rows: tuple[ResearchStrategySignalDecayDashboardRow, ...]
    reason_code_counts: tuple[ResearchStrategySignalDecayDashboardReasonCodeCount, ...]
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchStrategySignalDecayDashboardReport:
            raise TypeError(
                "ResearchStrategySignalDecayDashboardReport does not allow subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchStrategySignalDecayDashboardReport:
            raise ValueError(
                "report must be exactly ResearchStrategySignalDecayDashboardReport",
            )
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_text("config_version", self.config_version)
        _require_status("dashboard_status", self.dashboard_status)
        for field_name in (
            "row_count",
            "pass_count",
            "watch_count",
            "block_count",
            "average_dashboard_score",
            "max_signal_age_seconds",
            "max_refresh_failure_rate",
            "max_domain_difference_score",
            "min_settlement_seconds_remaining",
            "max_model_disagreement_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "average_dashboard_score",
            "max_refresh_failure_rate",
            "max_domain_difference_score",
            "max_model_disagreement_score",
        ):
            _require_ratio_decimal(field_name, getattr(self, field_name))
        if type(self.rows) is not tuple:
            raise ValueError("rows must be a tuple")
        for row in self.rows:
            if type(row) is not ResearchStrategySignalDecayDashboardRow:
                raise ValueError("rows must contain ResearchStrategySignalDecayDashboardRow")
            _require_hard_flags("row", row)
        if type(self.reason_code_counts) is not tuple:
            raise ValueError("reason_code_counts must be a tuple")
        for count_row in self.reason_code_counts:
            if type(count_row) is not ResearchStrategySignalDecayDashboardReasonCodeCount:
                raise ValueError(
                    "reason_code_counts must contain "
                    "ResearchStrategySignalDecayDashboardReasonCodeCount",
                )
            _require_hard_flags("reason code count", count_row)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_report_reason_codes(self.reason_codes),
        )
        _validate_report(self)
        _require_hard_flags("report", self)

    @property
    def payload(self) -> dict[str, Any]:
        return research_strategy_signal_decay_dashboard_report_payload(self)


def build_research_strategy_signal_decay_dashboard_report(
    input_rows: list[ResearchStrategySignalDecayInputRow]
    | tuple[ResearchStrategySignalDecayInputRow, ...],
    *,
    config: ResearchStrategySignalDecayDashboardConfig | None = None,
    generated_at: datetime,
) -> ResearchStrategySignalDecayDashboardReport:
    cfg = config or ResearchStrategySignalDecayDashboardConfig()
    if type(cfg) is not ResearchStrategySignalDecayDashboardConfig:
        raise ValueError("config must be a ResearchStrategySignalDecayDashboardConfig")
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
            ResearchStrategySignalDecayDashboardReasonCodeCount(
                reason_code=NO_INPUTS_REASON,
                count=ONE,
                row_ratio=ONE,
            ),
        )
        reason_codes = (NO_INPUTS_REASON,)
    return ResearchStrategySignalDecayDashboardReport(
        generated_at=report_time,
        config_version=cfg.config_version,
        dashboard_status=_report_status(bool(ranked_rows), block_count, watch_count),
        row_count=row_count,
        pass_count=pass_count,
        watch_count=watch_count,
        block_count=block_count,
        average_dashboard_score=_ratio(
            _sum_decimal(row.dashboard_score for row in ranked_rows),
            row_count,
        ),
        max_signal_age_seconds=max(
            (row.signal_age_seconds for row in ranked_rows),
            default=ZERO,
        ),
        max_refresh_failure_rate=max(
            (row.refresh_failure_rate for row in ranked_rows),
            default=ZERO,
        ),
        max_domain_difference_score=max(
            (row.domain_difference_score for row in ranked_rows),
            default=ZERO,
        ),
        min_settlement_seconds_remaining=min(
            (row.settlement_seconds_remaining for row in ranked_rows),
            default=ZERO,
        ),
        max_model_disagreement_score=max(
            (row.model_disagreement_score for row in ranked_rows),
            default=ZERO,
        ),
        rows=ranked_rows,
        reason_code_counts=reason_code_counts,
        reason_codes=reason_codes,
    )


def research_strategy_signal_decay_dashboard_report_payload(
    report: ResearchStrategySignalDecayDashboardReport,
) -> dict[str, Any]:
    if type(report) is not ResearchStrategySignalDecayDashboardReport:
        raise ValueError("report must be a ResearchStrategySignalDecayDashboardReport")
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
    row: ResearchStrategySignalDecayInputRow,
    *,
    config: ResearchStrategySignalDecayDashboardConfig,
    generated_at: datetime,
) -> ResearchStrategySignalDecayDashboardRow:
    signal_age_seconds = _datetime_delta_seconds(generated_at, row.signal_observed_at)
    refresh_lag_seconds = _datetime_delta_seconds(generated_at, row.last_refresh_attempt_at)
    refresh_failure_rate = _ratio(row.refresh_failure_count, row.refresh_attempt_count)
    settlement_seconds_remaining = _future_delta_seconds(row.settlement_at, generated_at)
    model_disagreement_score = _quantize(
        row.model_probability_high - row.model_probability_low,
    )
    signal_age_score = _age_score(
        signal_age_seconds,
        fresh_seconds=config.fresh_signal_max_age_seconds,
        stale_seconds=config.stale_signal_max_age_seconds,
    )
    refresh_failure_score = _inverse_ratio(
        refresh_failure_rate,
        block_threshold=config.refresh_failure_block_threshold,
    )
    domain_alignment_score = _inverse_ratio(
        row.domain_difference_score,
        block_threshold=config.domain_difference_block_threshold,
    )
    settlement_window_score = _settlement_score(
        settlement_seconds_remaining,
        watch_window_seconds=config.settlement_watch_window_seconds,
        block_window_seconds=config.settlement_block_window_seconds,
    )
    model_consensus_score = _inverse_ratio(
        model_disagreement_score,
        block_threshold=config.model_disagreement_block_threshold,
    )
    dashboard_score = _dashboard_score(
        signal_age_score=signal_age_score,
        refresh_failure_score=refresh_failure_score,
        domain_alignment_score=domain_alignment_score,
        settlement_window_score=settlement_window_score,
        model_consensus_score=model_consensus_score,
        config=config,
    )
    reason_codes = _row_reason_codes(
        signal_age_seconds=signal_age_seconds,
        refresh_failure_rate=refresh_failure_rate,
        domain_difference_score=row.domain_difference_score,
        settlement_seconds_remaining=settlement_seconds_remaining,
        model_disagreement_score=model_disagreement_score,
        dashboard_score=dashboard_score,
        config=config,
    )
    return ResearchStrategySignalDecayDashboardRow(
        redacted_signal_ref=_redacted_ref(row.signal_ref),
        signal_domain=row.signal_domain,
        expected_domain=row.expected_domain,
        signal_observed_at=row.signal_observed_at,
        last_refresh_attempt_at=row.last_refresh_attempt_at,
        settlement_at=row.settlement_at,
        signal_age_seconds=signal_age_seconds,
        refresh_lag_seconds=refresh_lag_seconds,
        refresh_failure_count=row.refresh_failure_count,
        refresh_attempt_count=row.refresh_attempt_count,
        refresh_failure_rate=refresh_failure_rate,
        domain_difference_score=row.domain_difference_score,
        settlement_seconds_remaining=settlement_seconds_remaining,
        model_probability_low=row.model_probability_low,
        model_probability_high=row.model_probability_high,
        model_disagreement_score=model_disagreement_score,
        signal_age_score=signal_age_score,
        refresh_failure_score=refresh_failure_score,
        domain_alignment_score=domain_alignment_score,
        settlement_window_score=settlement_window_score,
        model_consensus_score=model_consensus_score,
        dashboard_score=dashboard_score,
        status=_row_status(reason_codes),
        reason_codes=reason_codes,
        validation_config=config,
    )


def _normalize_input_rows(
    rows: list[ResearchStrategySignalDecayInputRow]
    | tuple[ResearchStrategySignalDecayInputRow, ...],
    generated_at: datetime,
) -> tuple[ResearchStrategySignalDecayInputRow, ...]:
    if type(rows) not in (list, tuple):
        raise ValueError("input rows must be a list or tuple")
    normalized = tuple(rows)
    seen: set[str] = set()
    for row in normalized:
        if type(row) is not ResearchStrategySignalDecayInputRow:
            raise ValueError("input rows must contain ResearchStrategySignalDecayInputRow")
        _require_hard_flags("input row", row)
        if row.signal_observed_at > generated_at:
            raise ValueError("signal_observed_at must be on or before generated_at")
        if row.last_refresh_attempt_at > generated_at:
            raise ValueError("last_refresh_attempt_at must be on or before generated_at")
        ref_digest = _redacted_ref(row.signal_ref)
        if ref_digest in seen:
            raise ValueError("input rows must be unique")
        seen.add(ref_digest)
    return normalized


def _row_reason_codes(
    *,
    signal_age_seconds: Decimal,
    refresh_failure_rate: Decimal,
    domain_difference_score: Decimal,
    settlement_seconds_remaining: Decimal,
    model_disagreement_score: Decimal,
    dashboard_score: Decimal,
    config: ResearchStrategySignalDecayDashboardConfig,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    if signal_age_seconds >= config.stale_signal_max_age_seconds:
        reason_codes.append(STALE_SIGNAL_REASON)
    elif signal_age_seconds > config.fresh_signal_max_age_seconds:
        reason_codes.append(AGING_SIGNAL_REASON)
    if refresh_failure_rate >= config.refresh_failure_block_threshold:
        reason_codes.append(REFRESH_FAILURE_BLOCK_REASON)
    elif refresh_failure_rate >= config.refresh_failure_watch_threshold:
        reason_codes.append(REFRESH_FAILURE_WATCH_REASON)
    if domain_difference_score >= config.domain_difference_block_threshold:
        reason_codes.append(DOMAIN_DIFFERENCE_BLOCK_REASON)
    elif domain_difference_score >= config.domain_difference_watch_threshold:
        reason_codes.append(DOMAIN_DIFFERENCE_WATCH_REASON)
    if settlement_seconds_remaining <= config.settlement_block_window_seconds:
        reason_codes.append(SETTLEMENT_BLOCK_WINDOW_REASON)
    elif settlement_seconds_remaining <= config.settlement_watch_window_seconds:
        reason_codes.append(SETTLEMENT_WATCH_WINDOW_REASON)
    if model_disagreement_score >= config.model_disagreement_block_threshold:
        reason_codes.append(MODEL_DISAGREEMENT_BLOCK_REASON)
    elif model_disagreement_score >= config.model_disagreement_watch_threshold:
        reason_codes.append(MODEL_DISAGREEMENT_WATCH_REASON)
    if dashboard_score < config.watch_dashboard_score:
        reason_codes.append(SCORE_BLOCK_REASON)
    elif dashboard_score < config.pass_dashboard_score:
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
        STALE_SIGNAL_REASON in reason_codes
        or REFRESH_FAILURE_BLOCK_REASON in reason_codes
        or DOMAIN_DIFFERENCE_BLOCK_REASON in reason_codes
        or SETTLEMENT_BLOCK_WINDOW_REASON in reason_codes
        or MODEL_DISAGREEMENT_BLOCK_REASON in reason_codes
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
    rows: tuple[ResearchStrategySignalDecayDashboardRow, ...],
) -> tuple[ResearchStrategySignalDecayDashboardRow, ...]:
    return tuple(
        sorted(
            rows,
            key=lambda row: (
                _status_rank(row.status),
                row.dashboard_score,
                row.settlement_seconds_remaining,
                row.redacted_signal_ref,
            ),
        ),
    )


def _status_rank(value: str) -> int:
    return {STATUS_BLOCK: 0, STATUS_WATCH: 1, STATUS_PASS: 2}[value]


def _reason_code_counts(
    rows: tuple[ResearchStrategySignalDecayDashboardRow, ...],
) -> tuple[ResearchStrategySignalDecayDashboardReasonCodeCount, ...]:
    total = _count(len(rows))
    counts: dict[str, Decimal] = {}
    for row in rows:
        for reason_code in row.reason_codes:
            counts[reason_code] = counts.get(reason_code, ZERO) + ONE
    return tuple(
        ResearchStrategySignalDecayDashboardReasonCodeCount(
            reason_code=reason_code,
            count=_count(counts[reason_code]),
            row_ratio=_ratio(counts[reason_code], total),
        )
        for reason_code in REASON_CODE_SEQUENCE
        if reason_code in counts
    )


def _validate_row(
    row: ResearchStrategySignalDecayDashboardRow,
    *,
    config: ResearchStrategySignalDecayDashboardConfig | None,
) -> None:
    if config is None:
        config = ResearchStrategySignalDecayDashboardConfig()
    if type(config) is not ResearchStrategySignalDecayDashboardConfig:
        raise ValueError(
            "validation_config must be a ResearchStrategySignalDecayDashboardConfig",
        )
    if row.refresh_failure_count > row.refresh_attempt_count:
        raise ValueError("refresh_failure_count must not exceed refresh_attempt_count")
    if row.model_probability_high < row.model_probability_low:
        raise ValueError("model_probability_high must be at least model_probability_low")
    if row.refresh_failure_rate != _ratio(
        row.refresh_failure_count,
        row.refresh_attempt_count,
    ):
        raise ValueError("refresh_failure_rate must match refresh counts")
    if row.model_disagreement_score != _quantize(
        row.model_probability_high - row.model_probability_low,
    ):
        raise ValueError("model_disagreement_score must match model probabilities")
    expected_signal_age_score = _age_score(
        row.signal_age_seconds,
        fresh_seconds=config.fresh_signal_max_age_seconds,
        stale_seconds=config.stale_signal_max_age_seconds,
    )
    if row.signal_age_score != expected_signal_age_score:
        raise ValueError("signal_age_score must match signal age")
    expected_refresh_failure_score = _inverse_ratio(
        row.refresh_failure_rate,
        block_threshold=config.refresh_failure_block_threshold,
    )
    if row.refresh_failure_score != expected_refresh_failure_score:
        raise ValueError("refresh_failure_score must match refresh failure rate")
    expected_domain_alignment_score = _inverse_ratio(
        row.domain_difference_score,
        block_threshold=config.domain_difference_block_threshold,
    )
    if row.domain_alignment_score != expected_domain_alignment_score:
        raise ValueError("domain_alignment_score must match domain difference")
    expected_settlement_window_score = _settlement_score(
        row.settlement_seconds_remaining,
        watch_window_seconds=config.settlement_watch_window_seconds,
        block_window_seconds=config.settlement_block_window_seconds,
    )
    if row.settlement_window_score != expected_settlement_window_score:
        raise ValueError("settlement_window_score must match settlement window")
    expected_model_consensus_score = _inverse_ratio(
        row.model_disagreement_score,
        block_threshold=config.model_disagreement_block_threshold,
    )
    if row.model_consensus_score != expected_model_consensus_score:
        raise ValueError("model_consensus_score must match model disagreement")
    expected_dashboard_score = _dashboard_score(
        signal_age_score=row.signal_age_score,
        refresh_failure_score=row.refresh_failure_score,
        domain_alignment_score=row.domain_alignment_score,
        settlement_window_score=row.settlement_window_score,
        model_consensus_score=row.model_consensus_score,
        config=config,
    )
    if row.dashboard_score != expected_dashboard_score:
        raise ValueError("dashboard_score must match component scores")
    expected_reason_codes = _row_reason_codes(
        signal_age_seconds=row.signal_age_seconds,
        refresh_failure_rate=row.refresh_failure_rate,
        domain_difference_score=row.domain_difference_score,
        settlement_seconds_remaining=row.settlement_seconds_remaining,
        model_disagreement_score=row.model_disagreement_score,
        dashboard_score=row.dashboard_score,
        config=config,
    )
    if row.reason_codes != expected_reason_codes:
        raise ValueError("reason_codes must match row inputs")
    if row.status != _row_status(row.reason_codes):
        raise ValueError("status must match reason_codes")
    if row.status == STATUS_PASS and row.dashboard_score < config.pass_dashboard_score:
        raise ValueError("dashboard_score must back pass status")
    if row.status == STATUS_WATCH and row.dashboard_score < config.watch_dashboard_score:
        raise ValueError("dashboard_score must back watch status")
    if row.status == STATUS_BLOCK and row.dashboard_score >= config.watch_dashboard_score:
        has_hard_reason = any(
            reason_code in row.reason_codes
            for reason_code in (
                STALE_SIGNAL_REASON,
                REFRESH_FAILURE_BLOCK_REASON,
                DOMAIN_DIFFERENCE_BLOCK_REASON,
                SETTLEMENT_BLOCK_WINDOW_REASON,
                MODEL_DISAGREEMENT_BLOCK_REASON,
            )
        )
        if not has_hard_reason:
            raise ValueError("dashboard_score must back block status")
    if not _is_redacted_ref(row.redacted_signal_ref):
        raise ValueError("redacted_signal_ref must be redacted")


def _validate_report(report: ResearchStrategySignalDecayDashboardReport) -> None:
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
    if report.average_dashboard_score != _ratio(
        _sum_decimal(row.dashboard_score for row in report.rows),
        report.row_count,
    ):
        raise ValueError("average_dashboard_score must match rows")
    if report.max_signal_age_seconds != max(
        (row.signal_age_seconds for row in report.rows),
        default=ZERO,
    ):
        raise ValueError("max_signal_age_seconds must match rows")
    if report.max_refresh_failure_rate != max(
        (row.refresh_failure_rate for row in report.rows),
        default=ZERO,
    ):
        raise ValueError("max_refresh_failure_rate must match rows")
    if report.max_domain_difference_score != max(
        (row.domain_difference_score for row in report.rows),
        default=ZERO,
    ):
        raise ValueError("max_domain_difference_score must match rows")
    if report.min_settlement_seconds_remaining != min(
        (row.settlement_seconds_remaining for row in report.rows),
        default=ZERO,
    ):
        raise ValueError("min_settlement_seconds_remaining must match rows")
    if report.max_model_disagreement_score != max(
        (row.model_disagreement_score for row in report.rows),
        default=ZERO,
    ):
        raise ValueError("max_model_disagreement_score must match rows")
    expected_counts = _reason_code_counts(report.rows)
    expected_codes = tuple(row.reason_code for row in expected_counts)
    if not report.rows:
        expected_counts = (
            ResearchStrategySignalDecayDashboardReasonCodeCount(
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
    if report.dashboard_status != expected_status:
        raise ValueError("dashboard_status must match rows")


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


def _dashboard_score(
    *,
    signal_age_score: Decimal,
    refresh_failure_score: Decimal,
    domain_alignment_score: Decimal,
    settlement_window_score: Decimal,
    model_consensus_score: Decimal,
    config: ResearchStrategySignalDecayDashboardConfig,
) -> Decimal:
    return _quantize(
        signal_age_score * config.signal_age_weight
        + refresh_failure_score * config.refresh_failure_weight
        + domain_alignment_score * config.domain_difference_weight
        + settlement_window_score * config.settlement_window_weight
        + model_consensus_score * config.model_disagreement_weight,
    )


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
    if "://" in value or "?" in value:
        raise ValueError(f"{field_name} has unsafe public text")
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
        if "://" in value or "?" in value:
            raise ValueError(f"{path or label} has unsafe public text")
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
        _join_parts("wal", "let"),
        _join_parts("au", "th"),
        _join_parts("ord", "er"),
        _join_parts("ad", "vice"),
        _join_parts("tra", "de"),
        _join_parts("to", "ken"),
        _join_parts("sec", "ret"),
        _join_parts("priv", "ate"),
        _join_parts("api", "_key"),
        _join_parts("pass", "word"),
        _join_parts("d", "sn"),
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
    "DEFAULT_RESEARCH_STRATEGY_SIGNAL_DECAY_DASHBOARD_CONFIG_VERSION",
    "ResearchStrategySignalDecayDashboardConfig",
    "ResearchStrategySignalDecayDashboardReasonCodeCount",
    "ResearchStrategySignalDecayDashboardReport",
    "ResearchStrategySignalDecayDashboardRow",
    "ResearchStrategySignalDecayInputRow",
    "build_research_strategy_signal_decay_dashboard_report",
    "research_strategy_signal_decay_dashboard_report_payload",
)
