"""Pure Phase 1 gold real-yield shock pressure reducer."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
from typing import Any


DEFAULT_MARKET_RESEARCH_GOLD_REAL_YIELD_SHOCK_DIGEST_CONFIG_VERSION = (
    "market-research-gold-real-yield-shock-digest-v0"
)

STATUS_READY = "ready"
STATUS_WATCH = "watch"
STATUS_BLOCKED = "blocked"
DIGEST_STATUSES = (STATUS_READY, STATUS_WATCH, STATUS_BLOCKED)

REASON_PREFIX = "market_research_gold_real_yield_shock_digest_"
NO_INPUTS_REASON = f"{REASON_PREFIX}no_inputs"
READY_REASON = f"{REASON_PREFIX}ready"
STALE_SIGNAL_REASON = f"{REASON_PREFIX}stale_signal"
LOW_REAL_YIELD_MOVE_REASON = f"{REASON_PREFIX}low_real_yield_move"
LOW_GOLD_INVERSE_MOVE_REASON = f"{REASON_PREFIX}low_gold_inverse_move"
LOW_ETF_FLOW_PRESSURE_REASON = f"{REASON_PREFIX}low_etf_flow_pressure"
SOURCE_FAMILY_GAP_REASON = f"{REASON_PREFIX}source_family_gap"
STALE_SOURCE_RATIO_REASON = f"{REASON_PREFIX}stale_source_ratio"
CONFIRMATION_GAP_REASON = f"{REASON_PREFIX}confirmation_gap"

REASON_CODE_SEQUENCE = (
    CONFIRMATION_GAP_REASON,
    STALE_SIGNAL_REASON,
    LOW_REAL_YIELD_MOVE_REASON,
    LOW_GOLD_INVERSE_MOVE_REASON,
    LOW_ETF_FLOW_PRESSURE_REASON,
    SOURCE_FAMILY_GAP_REASON,
    STALE_SOURCE_RATIO_REASON,
    READY_REASON,
    NO_INPUTS_REASON,
)
ROW_REASON_CODE_SEQUENCE = (
    STALE_SIGNAL_REASON,
    LOW_REAL_YIELD_MOVE_REASON,
    LOW_GOLD_INVERSE_MOVE_REASON,
    LOW_ETF_FLOW_PRESSURE_REASON,
    SOURCE_FAMILY_GAP_REASON,
    STALE_SOURCE_RATIO_REASON,
    CONFIRMATION_GAP_REASON,
    READY_REASON,
)

NEXT_STEPS = {
    STATUS_READY: "allow_report_only_market_research_gold_real_yield_shock_digest",
    STATUS_WATCH: "watch_report_only_market_research_gold_real_yield_shock_digest",
    STATUS_BLOCKED: "block_report_only_market_research_gold_real_yield_shock_digest",
}

DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
QUANT = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
MICROSECONDS_PER_SECOND = Decimal("1000000")


def _join_parts(*parts: str) -> str:
    return "".join(parts)


UNSAFE_TEXT_FRAGMENTS = frozenset(
    (
        _join_parts("au", "th"),
        _join_parts("bro", "ker"),
        _join_parts("sig", "ning"),
        _join_parts("sub", "mit"),
        _join_parts("can", "cel"),
        _join_parts("or", "der"),
        _join_parts("re", "place"),
        _join_parts("ex", "change"),
        _join_parts("wal", "let"),
        _join_parts("acc", "ount"),
        _join_parts("ad", "vice"),
        _join_parts("net", "work"),
        _join_parts("data", "base"),
        _join_parts("per", "sist"),
        _join_parts("sec", "ret"),
        _join_parts("to", "ken"),
        _join_parts("pri", "vate"),
        _join_parts("api", "_", "key"),
        _join_parts("api", "-", "key"),
        _join_parts("api", "key"),
        _join_parts("pri", "vate", "_", "key"),
        _join_parts("pri", "vate", "-", "key"),
        _join_parts("ht", "tp://"),
        _join_parts("ht", "tps://"),
    ),
)

__all__ = (
    "DEFAULT_MARKET_RESEARCH_GOLD_REAL_YIELD_SHOCK_DIGEST_CONFIG_VERSION",
    "MarketResearchGoldRealYieldShockDigestConfig",
    "MarketResearchGoldRealYieldShockDigestReasonCodeCount",
    "MarketResearchGoldRealYieldShockDigestReport",
    "MarketResearchGoldRealYieldShockDigestRow",
    "MarketResearchGoldRealYieldShockDigestSignal",
    "build_market_research_gold_real_yield_shock_digest",
    "market_research_gold_real_yield_shock_digest_payload",
)


@dataclass(frozen=True)
class MarketResearchGoldRealYieldShockDigestConfig:
    config_version: str = (
        DEFAULT_MARKET_RESEARCH_GOLD_REAL_YIELD_SHOCK_DIGEST_CONFIG_VERSION
    )
    max_signal_age_seconds: Decimal = Decimal("7200.000000")
    min_real_yield_move_bp_abs: Decimal = Decimal("12.000000")
    min_gold_inverse_move_pct_abs: Decimal = Decimal("0.750000")
    min_etf_flow_pressure_ratio_abs: Decimal = Decimal("0.200000")
    min_source_family_count: Decimal = Decimal("3.000000")
    max_stale_source_ratio: Decimal = Decimal("0.250000")
    min_confirmation_ratio: Decimal = Decimal("0.650000")
    confidence_decay_per_gap: Decimal = Decimal("0.100000")
    watch_confidence_threshold: Decimal = Decimal("0.650000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketResearchGoldRealYieldShockDigestConfig:
            raise TypeError(
                "MarketResearchGoldRealYieldShockDigestConfig does not support "
                "subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not MarketResearchGoldRealYieldShockDigestConfig:
            raise ValueError(
                "config must be exactly "
                "MarketResearchGoldRealYieldShockDigestConfig",
            )
        _require_canonical_string("config_version", self.config_version)
        for field_name in (
            "max_signal_age_seconds",
            "min_source_family_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_positive_count_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "min_real_yield_move_bp_abs",
            "min_gold_inverse_move_pct_abs",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_positive_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "min_etf_flow_pressure_ratio_abs",
            "max_stale_source_ratio",
            "min_confirmation_ratio",
            "confidence_decay_per_gap",
            "watch_confidence_threshold",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class MarketResearchGoldRealYieldShockDigestSignal:
    condition_id: str
    shock_key: str
    public_signal_reference: str
    observed_at: datetime
    real_yield_move_bp: Decimal
    gold_inverse_move_pct: Decimal
    etf_flow_pressure_ratio: Decimal
    source_family_count: Decimal
    stale_source_ratio: Decimal
    confirmation_ratio: Decimal
    base_confidence: Decimal
    signal_config_version: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketResearchGoldRealYieldShockDigestSignal:
            raise TypeError(
                "MarketResearchGoldRealYieldShockDigestSignal does not support "
                "subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not MarketResearchGoldRealYieldShockDigestSignal:
            raise ValueError(
                "signal must be exactly "
                "MarketResearchGoldRealYieldShockDigestSignal",
            )
        for field_name in (
            "condition_id",
            "shock_key",
            "signal_config_version",
        ):
            _require_public_string(field_name, getattr(self, field_name))
        _require_canonical_string(
            "public_signal_reference",
            self.public_signal_reference,
        )
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in (
            "real_yield_move_bp",
            "gold_inverse_move_pct",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "etf_flow_pressure_ratio",
            _require_bounded_decimal(
                "etf_flow_pressure_ratio",
                self.etf_flow_pressure_ratio,
            ),
        )
        object.__setattr__(
            self,
            "source_family_count",
            _require_nonnegative_count_decimal(
                "source_family_count",
                self.source_family_count,
            ),
        )
        for field_name in (
            "stale_source_ratio",
            "confirmation_ratio",
            "base_confidence",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        _require_hard_flags("signal", self)


@dataclass(frozen=True)
class MarketResearchGoldRealYieldShockDigestRow:
    condition_id: str
    shock_key: str
    digest_status: str
    observed_at: datetime
    signal_age_seconds: Decimal
    real_yield_move_bp: Decimal
    real_yield_move_bp_abs: Decimal
    gold_inverse_move_pct: Decimal
    gold_inverse_move_pct_abs: Decimal
    etf_flow_pressure_ratio: Decimal
    etf_flow_pressure_ratio_abs: Decimal
    source_family_count: Decimal
    stale_source_ratio: Decimal
    confirmation_ratio: Decimal
    base_confidence: Decimal
    confidence_decay_factor: Decimal
    final_confidence: Decimal
    redacted_public_signal_reference: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketResearchGoldRealYieldShockDigestRow:
            raise TypeError(
                "MarketResearchGoldRealYieldShockDigestRow does not support "
                "subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not MarketResearchGoldRealYieldShockDigestRow:
            raise ValueError(
                "row must be exactly MarketResearchGoldRealYieldShockDigestRow",
            )
        for field_name in ("condition_id", "shock_key"):
            _require_public_string(field_name, getattr(self, field_name))
        _require_status("digest_status", self.digest_status)
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in (
            "real_yield_move_bp",
            "gold_inverse_move_pct",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "etf_flow_pressure_ratio",
            _require_bounded_decimal(
                "etf_flow_pressure_ratio",
                self.etf_flow_pressure_ratio,
            ),
        )
        for field_name in (
            "signal_age_seconds",
            "real_yield_move_bp_abs",
            "gold_inverse_move_pct_abs",
            "etf_flow_pressure_ratio_abs",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "source_family_count",
            _require_nonnegative_count_decimal(
                "source_family_count",
                self.source_family_count,
            ),
        )
        for field_name in (
            "stale_source_ratio",
            "confirmation_ratio",
            "base_confidence",
            "confidence_decay_factor",
            "final_confidence",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        _require_redacted_reference(
            "redacted_public_signal_reference",
            self.redacted_public_signal_reference,
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(
                self.reason_codes,
                sequence=ROW_REASON_CODE_SEQUENCE,
            ),
        )
        _validate_row(self)
        _require_hard_flags("row", self)


@dataclass(frozen=True)
class MarketResearchGoldRealYieldShockDigestReasonCodeCount:
    reason_code: str
    count: Decimal
    signal_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketResearchGoldRealYieldShockDigestReasonCodeCount:
            raise TypeError(
                "MarketResearchGoldRealYieldShockDigestReasonCodeCount does not "
                "support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not MarketResearchGoldRealYieldShockDigestReasonCodeCount:
            raise ValueError(
                "reason code count must be exactly "
                "MarketResearchGoldRealYieldShockDigestReasonCodeCount",
            )
        _require_reason_code("reason_code", self.reason_code)
        object.__setattr__(
            self,
            "count",
            _require_positive_count_decimal("count", self.count),
        )
        object.__setattr__(
            self,
            "signal_ratio",
            _require_ratio_decimal("signal_ratio", self.signal_ratio),
        )
        _require_hard_flags("reason code count", self)


@dataclass(frozen=True)
class MarketResearchGoldRealYieldShockDigestReport:
    generated_at: datetime
    config_version: str
    digest_status: str
    recommended_next_step: str
    signal_count: Decimal
    ready_signal_count: Decimal
    watch_signal_count: Decimal
    blocked_signal_count: Decimal
    stale_signal_count: Decimal
    low_real_yield_move_signal_count: Decimal
    low_gold_inverse_move_signal_count: Decimal
    low_etf_flow_pressure_signal_count: Decimal
    source_family_gap_signal_count: Decimal
    stale_source_signal_count: Decimal
    confirmation_gap_signal_count: Decimal
    total_confidence_decay: Decimal
    average_final_confidence: Decimal
    average_real_yield_move_bp_abs: Decimal
    average_gold_inverse_move_pct_abs: Decimal
    average_etf_flow_pressure_ratio_abs: Decimal
    average_confirmation_ratio: Decimal
    max_signal_age_seconds: Decimal
    min_real_yield_move_bp_abs: Decimal
    min_gold_inverse_move_pct_abs: Decimal
    min_etf_flow_pressure_ratio_abs: Decimal
    min_source_family_count: Decimal
    max_stale_source_ratio: Decimal
    min_confirmation_ratio: Decimal
    max_observed_signal_age_seconds: Decimal
    rows: tuple[MarketResearchGoldRealYieldShockDigestRow, ...]
    signal_config_versions: tuple[tuple[str, str], ...]
    reason_code_counts: tuple[
        MarketResearchGoldRealYieldShockDigestReasonCodeCount,
        ...
    ]
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketResearchGoldRealYieldShockDigestReport:
            raise TypeError(
                "MarketResearchGoldRealYieldShockDigestReport does not support "
                "subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not MarketResearchGoldRealYieldShockDigestReport:
            raise ValueError(
                "report must be exactly MarketResearchGoldRealYieldShockDigestReport",
            )
        object.__setattr__(
            self,
            "generated_at",
            _as_utc("generated_at", self.generated_at),
        )
        _require_canonical_string("config_version", self.config_version)
        _require_status("digest_status", self.digest_status)
        _require_canonical_string("recommended_next_step", self.recommended_next_step)
        for field_name in (
            "signal_count",
            "ready_signal_count",
            "watch_signal_count",
            "blocked_signal_count",
            "stale_signal_count",
            "low_real_yield_move_signal_count",
            "low_gold_inverse_move_signal_count",
            "low_etf_flow_pressure_signal_count",
            "source_family_gap_signal_count",
            "stale_source_signal_count",
            "confirmation_gap_signal_count",
            "max_signal_age_seconds",
            "min_source_family_count",
            "max_observed_signal_age_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_count_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "total_confidence_decay",
            "average_real_yield_move_bp_abs",
            "average_gold_inverse_move_pct_abs",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "average_final_confidence",
            "average_etf_flow_pressure_ratio_abs",
            "average_confirmation_ratio",
            "min_etf_flow_pressure_ratio_abs",
            "max_stale_source_ratio",
            "min_confirmation_ratio",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "min_real_yield_move_bp_abs",
            "min_gold_inverse_move_pct_abs",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        object.__setattr__(
            self,
            "signal_config_versions",
            _normalize_signal_config_versions(self.signal_config_versions),
        )
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(
                self.reason_codes,
                sequence=REASON_CODE_SEQUENCE,
            ),
        )
        _validate_report(self)
        _require_hard_flags("report", self)


_PUBLIC_DATACLASS_TYPES = (
    MarketResearchGoldRealYieldShockDigestConfig,
    MarketResearchGoldRealYieldShockDigestSignal,
    MarketResearchGoldRealYieldShockDigestRow,
    MarketResearchGoldRealYieldShockDigestReasonCodeCount,
    MarketResearchGoldRealYieldShockDigestReport,
)


def build_market_research_gold_real_yield_shock_digest(
    signals: Iterable[MarketResearchGoldRealYieldShockDigestSignal],
    *,
    config: MarketResearchGoldRealYieldShockDigestConfig | None = None,
    generated_at: datetime,
) -> MarketResearchGoldRealYieldShockDigestReport:
    cfg = (
        MarketResearchGoldRealYieldShockDigestConfig()
        if config is None
        else config
    )
    if type(cfg) is not MarketResearchGoldRealYieldShockDigestConfig:
        raise ValueError(
            "config must be exactly MarketResearchGoldRealYieldShockDigestConfig",
        )
    generated_at_utc = _as_utc("generated_at", generated_at)
    normalized_signals = _normalize_signals(signals)
    rows = tuple(
        _row_for_signal(signal, config=cfg, generated_at=generated_at_utc)
        for signal in normalized_signals
    )
    sorted_rows = _sorted_rows(rows)
    report_status = _report_status(sorted_rows)
    return MarketResearchGoldRealYieldShockDigestReport(
        generated_at=generated_at_utc,
        config_version=cfg.config_version,
        digest_status=report_status,
        recommended_next_step=_recommended_next_step(report_status),
        signal_count=_decimal_count(len(sorted_rows)),
        ready_signal_count=_decimal_count(
            sum(1 for row in sorted_rows if row.digest_status == STATUS_READY),
        ),
        watch_signal_count=_decimal_count(
            sum(1 for row in sorted_rows if row.digest_status == STATUS_WATCH),
        ),
        blocked_signal_count=_decimal_count(
            sum(1 for row in sorted_rows if row.digest_status == STATUS_BLOCKED),
        ),
        stale_signal_count=_reason_signal_count(sorted_rows, STALE_SIGNAL_REASON),
        low_real_yield_move_signal_count=_reason_signal_count(
            sorted_rows,
            LOW_REAL_YIELD_MOVE_REASON,
        ),
        low_gold_inverse_move_signal_count=_reason_signal_count(
            sorted_rows,
            LOW_GOLD_INVERSE_MOVE_REASON,
        ),
        low_etf_flow_pressure_signal_count=_reason_signal_count(
            sorted_rows,
            LOW_ETF_FLOW_PRESSURE_REASON,
        ),
        source_family_gap_signal_count=_reason_signal_count(
            sorted_rows,
            SOURCE_FAMILY_GAP_REASON,
        ),
        stale_source_signal_count=_reason_signal_count(
            sorted_rows,
            STALE_SOURCE_RATIO_REASON,
        ),
        confirmation_gap_signal_count=_reason_signal_count(
            sorted_rows,
            CONFIRMATION_GAP_REASON,
        ),
        total_confidence_decay=_sum_decimal(
            row.confidence_decay_factor for row in sorted_rows
        ),
        average_final_confidence=_average_decimal(
            row.final_confidence for row in sorted_rows
        ),
        average_real_yield_move_bp_abs=_average_decimal(
            row.real_yield_move_bp_abs for row in sorted_rows
        ),
        average_gold_inverse_move_pct_abs=_average_decimal(
            row.gold_inverse_move_pct_abs for row in sorted_rows
        ),
        average_etf_flow_pressure_ratio_abs=_average_decimal(
            row.etf_flow_pressure_ratio_abs for row in sorted_rows
        ),
        average_confirmation_ratio=_average_decimal(
            row.confirmation_ratio for row in sorted_rows
        ),
        max_signal_age_seconds=cfg.max_signal_age_seconds,
        min_real_yield_move_bp_abs=cfg.min_real_yield_move_bp_abs,
        min_gold_inverse_move_pct_abs=cfg.min_gold_inverse_move_pct_abs,
        min_etf_flow_pressure_ratio_abs=cfg.min_etf_flow_pressure_ratio_abs,
        min_source_family_count=cfg.min_source_family_count,
        max_stale_source_ratio=cfg.max_stale_source_ratio,
        min_confirmation_ratio=cfg.min_confirmation_ratio,
        max_observed_signal_age_seconds=_max_decimal(
            row.signal_age_seconds for row in sorted_rows
        ),
        rows=sorted_rows,
        signal_config_versions=_signal_config_versions(sorted_rows, normalized_signals),
        reason_code_counts=_reason_code_counts(sorted_rows),
        reason_codes=_report_reason_codes(sorted_rows),
    )


def market_research_gold_real_yield_shock_digest_payload(
    report: MarketResearchGoldRealYieldShockDigestReport,
) -> dict[str, Any]:
    if type(report) is not MarketResearchGoldRealYieldShockDigestReport:
        raise ValueError(
            "report must be exactly MarketResearchGoldRealYieldShockDigestReport",
        )
    _require_payload_safe_value("report", report)
    _validate_report(report)
    _require_hard_flags("report", report)
    serialized = _json_ready(report)
    if not isinstance(serialized, dict):
        raise ValueError("serialized report must be a dict")
    return serialized


def _normalize_signals(
    signals: Iterable[MarketResearchGoldRealYieldShockDigestSignal],
) -> tuple[MarketResearchGoldRealYieldShockDigestSignal, ...]:
    if isinstance(signals, (str, bytes)):
        raise ValueError(
            "signals must contain MarketResearchGoldRealYieldShockDigestSignal values",
        )
    try:
        items = tuple(signals)
    except TypeError as exc:
        raise ValueError(
            "signals must contain MarketResearchGoldRealYieldShockDigestSignal values",
        ) from exc
    seen: set[str] = set()
    for item in items:
        if type(item) is not MarketResearchGoldRealYieldShockDigestSignal:
            raise ValueError(
                "signals must contain MarketResearchGoldRealYieldShockDigestSignal",
            )
        _require_hard_flags("signal", item)
        if item.shock_key in seen:
            raise ValueError("shock_key values must be unique")
        seen.add(item.shock_key)
    return items


def _row_for_signal(
    signal: MarketResearchGoldRealYieldShockDigestSignal,
    *,
    config: MarketResearchGoldRealYieldShockDigestConfig,
    generated_at: datetime,
) -> MarketResearchGoldRealYieldShockDigestRow:
    if signal.observed_at > generated_at:
        raise ValueError("observed_at must not be in the future")
    signal_age_seconds = _age_seconds(generated_at, signal.observed_at)
    real_yield_move_bp_abs = _abs_decimal(signal.real_yield_move_bp)
    gold_inverse_move_pct_abs = _abs_decimal(signal.gold_inverse_move_pct)
    etf_flow_pressure_ratio_abs = _abs_decimal(signal.etf_flow_pressure_ratio)
    reason_codes = _row_reason_codes(
        signal_age_seconds=signal_age_seconds,
        real_yield_move_bp_abs=real_yield_move_bp_abs,
        gold_inverse_move_pct_abs=gold_inverse_move_pct_abs,
        etf_flow_pressure_ratio_abs=etf_flow_pressure_ratio_abs,
        source_family_count=signal.source_family_count,
        stale_source_ratio=signal.stale_source_ratio,
        confirmation_ratio=signal.confirmation_ratio,
        config=config,
    )
    confidence_decay_factor = _confidence_decay_factor(reason_codes, config=config)
    final_confidence = _clamp_ratio(signal.base_confidence - confidence_decay_factor)
    return MarketResearchGoldRealYieldShockDigestRow(
        condition_id=signal.condition_id,
        shock_key=signal.shock_key,
        digest_status=_row_status(reason_codes, final_confidence, config),
        observed_at=signal.observed_at,
        signal_age_seconds=signal_age_seconds,
        real_yield_move_bp=signal.real_yield_move_bp,
        real_yield_move_bp_abs=real_yield_move_bp_abs,
        gold_inverse_move_pct=signal.gold_inverse_move_pct,
        gold_inverse_move_pct_abs=gold_inverse_move_pct_abs,
        etf_flow_pressure_ratio=signal.etf_flow_pressure_ratio,
        etf_flow_pressure_ratio_abs=etf_flow_pressure_ratio_abs,
        source_family_count=signal.source_family_count,
        stale_source_ratio=signal.stale_source_ratio,
        confirmation_ratio=signal.confirmation_ratio,
        base_confidence=signal.base_confidence,
        confidence_decay_factor=confidence_decay_factor,
        final_confidence=final_confidence,
        redacted_public_signal_reference=_redacted_reference(
            signal.public_signal_reference,
        ),
        reason_codes=reason_codes,
    )


def _row_reason_codes(
    *,
    signal_age_seconds: Decimal,
    real_yield_move_bp_abs: Decimal,
    gold_inverse_move_pct_abs: Decimal,
    etf_flow_pressure_ratio_abs: Decimal,
    source_family_count: Decimal,
    stale_source_ratio: Decimal,
    confirmation_ratio: Decimal,
    config: MarketResearchGoldRealYieldShockDigestConfig,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    if signal_age_seconds > config.max_signal_age_seconds:
        reason_codes.append(STALE_SIGNAL_REASON)
    if real_yield_move_bp_abs < config.min_real_yield_move_bp_abs:
        reason_codes.append(LOW_REAL_YIELD_MOVE_REASON)
    if gold_inverse_move_pct_abs < config.min_gold_inverse_move_pct_abs:
        reason_codes.append(LOW_GOLD_INVERSE_MOVE_REASON)
    if etf_flow_pressure_ratio_abs < config.min_etf_flow_pressure_ratio_abs:
        reason_codes.append(LOW_ETF_FLOW_PRESSURE_REASON)
    if source_family_count < config.min_source_family_count:
        reason_codes.append(SOURCE_FAMILY_GAP_REASON)
    if stale_source_ratio > config.max_stale_source_ratio:
        reason_codes.append(STALE_SOURCE_RATIO_REASON)
    if confirmation_ratio < config.min_confirmation_ratio:
        reason_codes.append(CONFIRMATION_GAP_REASON)
    if not reason_codes:
        reason_codes.append(READY_REASON)
    return _normalize_reason_codes(
        tuple(reason_codes),
        sequence=ROW_REASON_CODE_SEQUENCE,
    )


def _confidence_decay_factor(
    reason_codes: tuple[str, ...],
    *,
    config: MarketResearchGoldRealYieldShockDigestConfig,
) -> Decimal:
    no_decay_reasons = (READY_REASON, STALE_SOURCE_RATIO_REASON)
    gap_count = sum(1 for reason_code in reason_codes if reason_code not in no_decay_reasons)
    return _clamp_ratio(config.confidence_decay_per_gap * _decimal_count(gap_count))


def _row_status(
    reason_codes: tuple[str, ...],
    final_confidence: Decimal,
    config: MarketResearchGoldRealYieldShockDigestConfig,
) -> str:
    if reason_codes == (READY_REASON,):
        return STATUS_READY
    if final_confidence < config.watch_confidence_threshold:
        return STATUS_BLOCKED
    return STATUS_WATCH


def _report_status(
    rows: tuple[MarketResearchGoldRealYieldShockDigestRow, ...],
) -> str:
    if not rows:
        return STATUS_BLOCKED
    if any(row.digest_status == STATUS_BLOCKED for row in rows):
        return STATUS_BLOCKED
    if any(row.digest_status == STATUS_WATCH for row in rows):
        return STATUS_WATCH
    return STATUS_READY


def _recommended_next_step(status: str) -> str:
    _require_status("digest_status", status)
    return NEXT_STEPS[status]


def _reason_signal_count(
    rows: tuple[MarketResearchGoldRealYieldShockDigestRow, ...],
    reason_code: str,
) -> Decimal:
    _require_reason_code("reason_code", reason_code)
    return _decimal_count(sum(1 for row in rows if reason_code in row.reason_codes))


def _reason_code_counts(
    rows: tuple[MarketResearchGoldRealYieldShockDigestRow, ...],
) -> tuple[MarketResearchGoldRealYieldShockDigestReasonCodeCount, ...]:
    if not rows:
        return (
            MarketResearchGoldRealYieldShockDigestReasonCodeCount(
                reason_code=NO_INPUTS_REASON,
                count=ONE,
                signal_ratio=ZERO,
            ),
        )
    counts: dict[str, int] = {}
    for row in rows:
        for reason_code in row.reason_codes:
            counts[reason_code] = counts.setdefault(reason_code, 0) + 1
    signal_count = _decimal_count(len(rows))
    return tuple(
        MarketResearchGoldRealYieldShockDigestReasonCodeCount(
            reason_code=reason_code,
            count=_decimal_count(counts[reason_code]),
            signal_ratio=_divide_decimal(_decimal_count(counts[reason_code]), signal_count),
        )
        for reason_code in REASON_CODE_SEQUENCE
        if reason_code in counts
    )


def _report_reason_codes(
    rows: tuple[MarketResearchGoldRealYieldShockDigestRow, ...],
) -> tuple[str, ...]:
    return tuple(item.reason_code for item in _reason_code_counts(rows))


def _signal_config_versions(
    rows: tuple[MarketResearchGoldRealYieldShockDigestRow, ...],
    signals: tuple[MarketResearchGoldRealYieldShockDigestSignal, ...],
) -> tuple[tuple[str, str], ...]:
    versions = {signal.shock_key: signal.signal_config_version for signal in signals}
    return tuple((row.shock_key, versions[row.shock_key]) for row in rows)


def _normalize_rows(
    rows: object,
) -> tuple[MarketResearchGoldRealYieldShockDigestRow, ...]:
    if type(rows) is not tuple:
        raise ValueError("rows must be a tuple")
    for row in rows:
        if type(row) is not MarketResearchGoldRealYieldShockDigestRow:
            raise ValueError(
                "rows must contain only MarketResearchGoldRealYieldShockDigestRow",
            )
        _require_hard_flags("row", row)
    normalized = rows
    if normalized != _sorted_rows(normalized):
        raise ValueError("rows must be sorted deterministically")
    if len({row.shock_key for row in normalized}) != len(normalized):
        raise ValueError("shock_key values must be unique")
    return normalized


def _normalize_signal_config_versions(
    value: object,
) -> tuple[tuple[str, str], ...]:
    if type(value) is not tuple:
        raise ValueError("signal_config_versions must be a tuple")
    normalized: list[tuple[str, str]] = []
    seen: set[str] = set()
    for item in value:
        if type(item) is not tuple or len(item) != 2:
            raise ValueError("signal_config_versions must contain key/version pairs")
        shock_key, config_version = item
        _require_public_string("signal_config_versions key", shock_key)
        _require_public_string("signal_config_versions version", config_version)
        if shock_key in seen:
            raise ValueError("signal_config_versions keys must be unique")
        seen.add(shock_key)
        normalized.append((shock_key, config_version))
    return tuple(normalized)


def _normalize_reason_code_counts(
    value: object,
) -> tuple[MarketResearchGoldRealYieldShockDigestReasonCodeCount, ...]:
    if type(value) is not tuple:
        raise ValueError("reason_code_counts must be a tuple")
    for item in value:
        if type(item) is not MarketResearchGoldRealYieldShockDigestReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain only "
                "MarketResearchGoldRealYieldShockDigestReasonCodeCount",
            )
        _require_hard_flags("reason code count", item)
    normalized = tuple(
        sorted(
            value,
            key=lambda item: _reason_code_position(item.reason_code, REASON_CODE_SEQUENCE),
        ),
    )
    if value != normalized:
        raise ValueError("reason_code_counts must be sorted deterministically")
    return normalized


def _normalize_reason_codes(
    value: object,
    *,
    sequence: tuple[str, ...],
) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ValueError("reason_codes must be a tuple")
    unique: set[str] = set()
    for reason_code in value:
        _require_reason_code("reason_code", reason_code)
        unique.add(reason_code)
    if len(unique) != len(value):
        raise ValueError("reason_codes must be unique")
    normalized = tuple(reason_code for reason_code in sequence if reason_code in unique)
    if value != normalized:
        raise ValueError("reason_codes must be sorted deterministically")
    return normalized


def _validate_row(row: MarketResearchGoldRealYieldShockDigestRow) -> None:
    if not row.reason_codes:
        raise ValueError("reason_codes must be non-empty")
    if row.real_yield_move_bp_abs != _abs_decimal(row.real_yield_move_bp):
        raise ValueError("real_yield_move_bp_abs must match real_yield_move_bp")
    if row.gold_inverse_move_pct_abs != _abs_decimal(row.gold_inverse_move_pct):
        raise ValueError("gold_inverse_move_pct_abs must match gold_inverse_move_pct")
    if row.etf_flow_pressure_ratio_abs != _abs_decimal(row.etf_flow_pressure_ratio):
        raise ValueError(
            "etf_flow_pressure_ratio_abs must match etf_flow_pressure_ratio",
        )
    if row.final_confidence != _clamp_ratio(
        row.base_confidence - row.confidence_decay_factor,
    ):
        raise ValueError("final_confidence must match base_confidence and decay")
    if row.digest_status == STATUS_READY and row.reason_codes != (READY_REASON,):
        raise ValueError("digest_status must match reason_codes")
    if row.digest_status != STATUS_READY and row.reason_codes == (READY_REASON,):
        raise ValueError("digest_status must match reason_codes")


def _validate_report(report: MarketResearchGoldRealYieldShockDigestReport) -> None:
    rows = report.rows
    for row in rows:
        _require_hard_flags("row", row)
    for reason_code_count in report.reason_code_counts:
        _require_hard_flags("reason code count", reason_code_count)
    if rows != _sorted_rows(rows):
        raise ValueError("rows must be sorted deterministically")
    if report.recommended_next_step != _recommended_next_step(report.digest_status):
        raise ValueError("recommended_next_step must match digest_status")
    if report.signal_count != _decimal_count(len(rows)):
        raise ValueError("signal_count must match rows")
    if tuple(key for key, _ in report.signal_config_versions) != tuple(
        row.shock_key for row in rows
    ):
        raise ValueError("signal_config_versions must match rows")
    expected_counts = {
        "ready_signal_count": sum(1 for row in rows if row.digest_status == STATUS_READY),
        "watch_signal_count": sum(1 for row in rows if row.digest_status == STATUS_WATCH),
        "blocked_signal_count": sum(
            1 for row in rows if row.digest_status == STATUS_BLOCKED
        ),
        "stale_signal_count": sum(
            1 for row in rows if STALE_SIGNAL_REASON in row.reason_codes
        ),
        "low_real_yield_move_signal_count": sum(
            1 for row in rows if LOW_REAL_YIELD_MOVE_REASON in row.reason_codes
        ),
        "low_gold_inverse_move_signal_count": sum(
            1 for row in rows if LOW_GOLD_INVERSE_MOVE_REASON in row.reason_codes
        ),
        "low_etf_flow_pressure_signal_count": sum(
            1 for row in rows if LOW_ETF_FLOW_PRESSURE_REASON in row.reason_codes
        ),
        "source_family_gap_signal_count": sum(
            1 for row in rows if SOURCE_FAMILY_GAP_REASON in row.reason_codes
        ),
        "stale_source_signal_count": sum(
            1 for row in rows if STALE_SOURCE_RATIO_REASON in row.reason_codes
        ),
        "confirmation_gap_signal_count": sum(
            1 for row in rows if CONFIRMATION_GAP_REASON in row.reason_codes
        ),
    }
    for field_name, expected_count in expected_counts.items():
        if getattr(report, field_name) != _decimal_count(expected_count):
            raise ValueError(f"{field_name} must match rows")
    if report.digest_status != _report_status(rows):
        raise ValueError("digest_status must match rows")
    if report.total_confidence_decay != _sum_decimal(
        row.confidence_decay_factor for row in rows
    ):
        raise ValueError("total_confidence_decay must match rows")
    average_checks = {
        "average_final_confidence": (row.final_confidence for row in rows),
        "average_real_yield_move_bp_abs": (
            row.real_yield_move_bp_abs for row in rows
        ),
        "average_gold_inverse_move_pct_abs": (
            row.gold_inverse_move_pct_abs for row in rows
        ),
        "average_etf_flow_pressure_ratio_abs": (
            row.etf_flow_pressure_ratio_abs for row in rows
        ),
        "average_confirmation_ratio": (row.confirmation_ratio for row in rows),
    }
    for field_name, values in average_checks.items():
        if getattr(report, field_name) != _average_decimal(values):
            raise ValueError(f"{field_name} must match rows")
    if report.max_observed_signal_age_seconds != _max_decimal(
        row.signal_age_seconds for row in rows
    ):
        raise ValueError("max_observed_signal_age_seconds must match rows")
    if report.reason_code_counts != _reason_code_counts(rows):
        raise ValueError("reason_code_counts must match rows")
    if report.reason_codes != tuple(item.reason_code for item in report.reason_code_counts):
        raise ValueError("reason_codes must match reason_code_counts")


def _sorted_rows(
    rows: tuple[MarketResearchGoldRealYieldShockDigestRow, ...],
) -> tuple[MarketResearchGoldRealYieldShockDigestRow, ...]:
    return tuple(
        sorted(
            rows,
            key=lambda row: (_row_sort_value(row), row.shock_key, row.condition_id),
        ),
    )


def _row_sort_value(row: MarketResearchGoldRealYieldShockDigestRow) -> int:
    return {
        STATUS_BLOCKED: 0,
        STATUS_WATCH: 1,
        STATUS_READY: 2,
    }[row.digest_status]


def _age_seconds(later: datetime, earlier: datetime) -> Decimal:
    delta = later - earlier
    with localcontext(DECIMAL_CONTEXT):
        seconds = Decimal(delta.days * 86400 + delta.seconds)
        micros = Decimal(delta.microseconds) / MICROSECONDS_PER_SECOND
        return _quantize(seconds + micros)


def _sum_decimal(values: Iterable[Decimal]) -> Decimal:
    total = ZERO
    for value in values:
        if type(value) is not Decimal:
            raise ValueError("values must be Decimals")
        if not value.is_finite():
            raise ValueError("values must be finite")
        total += value
    return _quantize(total)


def _average_decimal(values: Iterable[Decimal]) -> Decimal:
    items = tuple(values)
    if not items:
        return ZERO
    return _divide_decimal(_sum_decimal(items), _decimal_count(len(items)))


def _max_decimal(values: Iterable[Decimal]) -> Decimal:
    items = tuple(values)
    if not items:
        return ZERO
    for value in items:
        if type(value) is not Decimal:
            raise ValueError("values must be Decimals")
        if not value.is_finite():
            raise ValueError("values must be finite")
    return _quantize(max(items))


def _divide_decimal(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return _quantize(numerator / denominator)


def _abs_decimal(value: Decimal) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError("value must be a Decimal")
    if not value.is_finite():
        raise ValueError("value must be finite")
    return _quantize(abs(value))


def _decimal_count(value: int) -> Decimal:
    return _quantize(Decimal(value))


def _reason_code_position(
    reason_code: str,
    sequence: tuple[str, ...],
) -> int:
    _require_reason_code("reason_code", reason_code)
    return sequence.index(reason_code)


def _redacted_reference(value: str) -> str:
    lowered = value.lower()
    if any(fragment in lowered for fragment in UNSAFE_TEXT_FRAGMENTS):
        return "sha256:" + sha256(value.encode("utf-8")).hexdigest()[:12]
    return value


def _json_ready(value: object) -> object:
    if is_dataclass(value) and not isinstance(value, type):
        if type(value) not in _PUBLIC_DATACLASS_TYPES:
            raise ValueError("JSON dataclass must be a supported public dataclass")
        ready: dict[str, Any] = {}
        for field in fields(value):
            item = getattr(value, field.name)
            if field.name in {"paper_only", "report_only", "readonly"}:
                if item is not True:
                    raise ValueError(f"{field.name} must be True")
            ready[field.name] = _json_ready(item)
        return ready
    if type(value) is Decimal:
        if _require_decimal("JSON Decimal value", value) != value:
            raise ValueError("JSON Decimal value must be quantized to six decimals")
        if not value.same_quantum(QUANT):
            raise ValueError("JSON Decimal value must be quantized to six decimals")
        return format(value, "f")
    if isinstance(value, Decimal):
        raise ValueError("output numerics must be exact Decimals")
    if type(value) is datetime:
        _as_utc("JSON datetime value", value)
        if value.tzinfo is not UTC:
            raise ValueError("JSON datetime value must be normalized to UTC")
        return value.isoformat()
    if isinstance(value, datetime):
        raise ValueError("JSON datetime value must be exactly datetime")
    if type(value) is tuple:
        return [_json_ready(item) for item in value]
    if type(value) in (list, dict, set):
        raise ValueError("JSON value must remain constructor-normalized")
    if type(value) in (str, bool) or value is None:
        return value
    return value


def _require_payload_safe_value(field_name: str, value: object) -> None:
    if type(value) is Decimal:
        decimal_value = _require_decimal(field_name, value)
        if decimal_value != value or not value.same_quantum(QUANT):
            raise ValueError(f"{field_name} must be quantized to six decimals")
        return
    if type(value) is datetime:
        _as_utc(field_name, value)
        if value.tzinfo is not UTC:
            raise ValueError(f"{field_name} must be normalized to UTC")
        return
    if is_dataclass(value) and not isinstance(value, type):
        if type(value) not in _PUBLIC_DATACLASS_TYPES:
            raise ValueError(f"{field_name} must be a supported public dataclass")
        _require_hard_flags(field_name, value)
        for field in fields(value):
            _require_payload_safe_value(
                f"{field_name}.{field.name}",
                getattr(value, field.name),
            )
        _rebuild_public_dataclass(field_name, value)
        return
    if type(value) is tuple:
        for index, item in enumerate(value):
            _require_payload_safe_value(f"{field_name}[{index}]", item)
        return
    if type(value) is int:
        raise ValueError(f"{field_name} must use Decimal values")
    if isinstance(value, float):
        raise ValueError(f"{field_name} must not be a float")
    if type(value) in (str, bool) or value is None:
        return
    if type(value) in (list, dict, set):
        raise ValueError(f"{field_name} must remain constructor-normalized")
    raise ValueError(f"{field_name} must be safe for payload serialization")


def _rebuild_public_dataclass(field_name: str, value: object) -> None:
    type_ = type(value)
    try:
        type_(**{field.name: getattr(value, field.name) for field in fields(value)})
    except (ArithmeticError, TypeError, ValueError) as exc:
        raise ValueError(f"{field_name} must remain constructor-valid") from exc


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in DIGEST_STATUSES:
        raise ValueError(f"{field_name} must be ready, watch, or blocked")


def _require_reason_code(field_name: str, value: object) -> None:
    _require_canonical_string(field_name, value)
    if value not in REASON_CODE_SEQUENCE:
        raise ValueError(f"{field_name} contains unknown reason code")


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str or not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a non-empty string")


def _require_public_string(field_name: str, value: object) -> None:
    _require_canonical_string(field_name, value)
    lowered = value.lower()
    if any(fragment in lowered for fragment in UNSAFE_TEXT_FRAGMENTS):
        raise ValueError(f"{field_name} contains disallowed text")


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be exactly Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return _quantize(value)


def _require_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    decimal = _require_decimal(field_name, value)
    if decimal < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return decimal


def _require_positive_decimal(field_name: str, value: object) -> Decimal:
    decimal = _require_nonnegative_decimal(field_name, value)
    if decimal <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return decimal


def _require_bounded_decimal(field_name: str, value: object) -> Decimal:
    decimal = _require_decimal(field_name, value)
    if decimal < -ONE or decimal > ONE:
        raise ValueError(f"{field_name} must be between -1 and 1")
    return decimal


def _require_nonnegative_count_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be exactly Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    if value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    if value != value.to_integral_value():
        raise ValueError(f"{field_name} must be an integral Decimal")
    return _quantize(value)


def _require_positive_count_decimal(field_name: str, value: object) -> Decimal:
    decimal = _require_nonnegative_count_decimal(field_name, value)
    if decimal <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return decimal


def _require_ratio_decimal(field_name: str, value: object) -> Decimal:
    decimal = _require_decimal(field_name, value)
    if decimal < ZERO or decimal > ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return decimal


def _require_redacted_reference(field_name: str, value: object) -> None:
    _require_canonical_string(field_name, value)
    lowered = value.lower()
    if any(fragment in lowered for fragment in UNSAFE_TEXT_FRAGMENTS):
        raise ValueError(f"{field_name} must be redacted")


def _require_hard_flags(field_name: str, value: object) -> None:
    if getattr(value, "paper_only", None) is not True:
        raise ValueError(f"{field_name} paper_only must be True")
    if getattr(value, "report_only", None) is not True:
        raise ValueError(f"{field_name} report_only must be True")
    if getattr(value, "readonly", None) is not True:
        raise ValueError(f"{field_name} readonly must be True")


def _clamp_ratio(value: Decimal) -> Decimal:
    decimal = _require_decimal("value", value)
    if decimal < ZERO:
        return ZERO
    if decimal > ONE:
        return ONE
    return decimal


def _quantize(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(QUANT)
