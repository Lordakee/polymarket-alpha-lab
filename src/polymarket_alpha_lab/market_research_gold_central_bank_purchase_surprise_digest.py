"""Pure Phase 1 gold central-bank purchase surprise research reducer."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
from typing import Any


DEFAULT_MARKET_RESEARCH_GOLD_CENTRAL_BANK_PURCHASE_SURPRISE_DIGEST_CONFIG_VERSION = (
    "market-research-gold-central-bank-purchase-surprise-digest-v0"
)

STATUS_READY = "ready"
STATUS_WATCH = "watch"
STATUS_BLOCKED = "blocked"
DIGEST_STATUSES = (STATUS_READY, STATUS_WATCH, STATUS_BLOCKED)

SURPRISE_DIRECTION_ABOVE = "above_consensus"
SURPRISE_DIRECTION_BELOW = "below_consensus"
SURPRISE_DIRECTION_INLINE = "in_line"
SURPRISE_DIRECTIONS = (
    SURPRISE_DIRECTION_ABOVE,
    SURPRISE_DIRECTION_BELOW,
    SURPRISE_DIRECTION_INLINE,
)

REASON_PREFIX = "market_research_gold_central_bank_purchase_surprise_digest_"
NO_INPUTS_REASON = f"{REASON_PREFIX}no_inputs"
READY_REASON = f"{REASON_PREFIX}ready"
STALE_REPORT_SIGNAL_REASON = f"{REASON_PREFIX}stale_report_signal"
REPORTING_LAG_REASON = f"{REASON_PREFIX}reporting_lag"
CONFIRMATION_SOURCE_GAP_REASON = f"{REASON_PREFIX}confirmation_source_gap"
PURCHASE_SURPRISE_GAP_REASON = f"{REASON_PREFIX}purchase_surprise_gap"
RESERVE_REVISION_GAP_REASON = f"{REASON_PREFIX}reserve_revision_gap"
FX_RESERVE_SHARE_PRESSURE_GAP_REASON = (
    f"{REASON_PREFIX}fx_reserve_share_pressure_gap"
)
COMMODITY_ALIGNMENT_GAP_REASON = f"{REASON_PREFIX}commodity_alignment_gap"

REASON_CODE_SEQUENCE = (
    FX_RESERVE_SHARE_PRESSURE_GAP_REASON,
    COMMODITY_ALIGNMENT_GAP_REASON,
    STALE_REPORT_SIGNAL_REASON,
    REPORTING_LAG_REASON,
    CONFIRMATION_SOURCE_GAP_REASON,
    PURCHASE_SURPRISE_GAP_REASON,
    RESERVE_REVISION_GAP_REASON,
    READY_REASON,
    NO_INPUTS_REASON,
)
ROW_REASON_CODE_SEQUENCE = (
    STALE_REPORT_SIGNAL_REASON,
    REPORTING_LAG_REASON,
    CONFIRMATION_SOURCE_GAP_REASON,
    PURCHASE_SURPRISE_GAP_REASON,
    RESERVE_REVISION_GAP_REASON,
    FX_RESERVE_SHARE_PRESSURE_GAP_REASON,
    COMMODITY_ALIGNMENT_GAP_REASON,
    READY_REASON,
)

NEXT_STEPS = {
    STATUS_READY: (
        "allow_report_only_market_research_gold_central_bank_purchase_surprise_digest"
    ),
    STATUS_WATCH: (
        "monitor_report_only_market_research_gold_central_bank_purchase_surprise_digest"
    ),
    STATUS_BLOCKED: (
        "block_report_only_market_research_gold_central_bank_purchase_surprise_digest"
    ),
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
        _join_parts("or", "der"),
        _join_parts("can", "cel"),
        _join_parts("rep", "lace"),
        _join_parts("ex", "change"),
        _join_parts("wal", "let"),
        _join_parts("sig", "ning"),
        _join_parts("pri", "vate"),
        _join_parts("sec", "ret"),
        _join_parts("to", "ken"),
        _join_parts("ht", "tp"),
        _join_parts("tra", "de"),
        _join_parts("liv", "e_trading"),
        "://",
    ),
)

__all__ = (
    "DEFAULT_MARKET_RESEARCH_GOLD_CENTRAL_BANK_PURCHASE_SURPRISE_DIGEST_CONFIG_VERSION",
    "MarketResearchGoldCentralBankPurchaseSurpriseDigestConfig",
    "MarketResearchGoldCentralBankPurchaseSurpriseDigestReasonCodeCount",
    "MarketResearchGoldCentralBankPurchaseSurpriseDigestReport",
    "MarketResearchGoldCentralBankPurchaseSurpriseDigestRow",
    "MarketResearchGoldCentralBankPurchaseSurpriseDigestSignal",
    "build_market_research_gold_central_bank_purchase_surprise_digest",
    "market_research_gold_central_bank_purchase_surprise_digest_payload",
)


@dataclass(frozen=True)
class MarketResearchGoldCentralBankPurchaseSurpriseDigestConfig:
    config_version: str = (
        DEFAULT_MARKET_RESEARCH_GOLD_CENTRAL_BANK_PURCHASE_SURPRISE_DIGEST_CONFIG_VERSION
    )
    max_report_age_seconds: Decimal = Decimal("7200.000000")
    max_reporting_lag_seconds: Decimal = Decimal("86400.000000")
    min_purchase_surprise_tonnage_abs: Decimal = Decimal("5.000000")
    min_reserve_revision_tonnage_abs: Decimal = Decimal("1.000000")
    min_confirmation_source_count: Decimal = Decimal("2.000000")
    min_fx_reserve_share_pressure: Decimal = Decimal("0.050000")
    min_commodity_event_alignment_score: Decimal = Decimal("0.550000")
    watch_confidence_threshold: Decimal = Decimal("0.650000")
    confidence_decay_per_gap: Decimal = Decimal("0.100000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketResearchGoldCentralBankPurchaseSurpriseDigestConfig:
            raise TypeError(
                "MarketResearchGoldCentralBankPurchaseSurpriseDigestConfig does not "
                "support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not MarketResearchGoldCentralBankPurchaseSurpriseDigestConfig:
            raise ValueError(
                "config must be exactly "
                "MarketResearchGoldCentralBankPurchaseSurpriseDigestConfig",
            )
        _require_canonical_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_MARKET_RESEARCH_GOLD_CENTRAL_BANK_PURCHASE_SURPRISE_DIGEST_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "max_report_age_seconds",
            "max_reporting_lag_seconds",
            "min_purchase_surprise_tonnage_abs",
            "min_reserve_revision_tonnage_abs",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_positive_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "min_confirmation_source_count",
            _require_positive_count_decimal(
                "min_confirmation_source_count",
                self.min_confirmation_source_count,
            ),
        )
        for field_name in (
            "min_fx_reserve_share_pressure",
            "min_commodity_event_alignment_score",
            "watch_confidence_threshold",
            "confidence_decay_per_gap",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class MarketResearchGoldCentralBankPurchaseSurpriseDigestSignal:
    surprise_key: str
    condition_id: str
    central_bank: str
    public_report_reference: str
    observed_at: datetime
    reporting_lag_seconds: Decimal
    reported_purchase_tonnage: Decimal
    expected_purchase_tonnage: Decimal
    reserve_revision_tonnage_abs: Decimal
    confirmation_source_count: Decimal
    fx_reserve_share_pressure: Decimal
    commodity_event_alignment_score: Decimal
    base_confidence: Decimal
    signal_config_version: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketResearchGoldCentralBankPurchaseSurpriseDigestSignal:
            raise TypeError(
                "MarketResearchGoldCentralBankPurchaseSurpriseDigestSignal does not "
                "support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not MarketResearchGoldCentralBankPurchaseSurpriseDigestSignal:
            raise ValueError(
                "signal must be exactly "
                "MarketResearchGoldCentralBankPurchaseSurpriseDigestSignal",
            )
        for field_name in (
            "surprise_key",
            "condition_id",
            "central_bank",
            "signal_config_version",
        ):
            _require_public_string(field_name, getattr(self, field_name))
        _require_canonical_string("public_report_reference", self.public_report_reference)
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in (
            "reporting_lag_seconds",
            "reported_purchase_tonnage",
            "expected_purchase_tonnage",
            "reserve_revision_tonnage_abs",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "confirmation_source_count",
            _require_nonnegative_count_decimal(
                "confirmation_source_count",
                self.confirmation_source_count,
            ),
        )
        for field_name in (
            "fx_reserve_share_pressure",
            "commodity_event_alignment_score",
            "base_confidence",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        _require_hard_flags("signal", self)


@dataclass(frozen=True)
class MarketResearchGoldCentralBankPurchaseSurpriseDigestRow:
    surprise_key: str
    condition_id: str
    central_bank: str
    digest_status: str
    observed_at: datetime
    signal_age_seconds: Decimal
    reporting_lag_seconds: Decimal
    reported_purchase_tonnage: Decimal
    expected_purchase_tonnage: Decimal
    purchase_surprise_direction: str
    purchase_surprise_tonnage_abs: Decimal
    reserve_revision_tonnage_abs: Decimal
    confirmation_source_count: Decimal
    fx_reserve_share_pressure: Decimal
    commodity_event_alignment_score: Decimal
    base_confidence: Decimal
    confidence_decay_factor: Decimal
    final_confidence: Decimal
    redacted_public_report_reference: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketResearchGoldCentralBankPurchaseSurpriseDigestRow:
            raise TypeError(
                "MarketResearchGoldCentralBankPurchaseSurpriseDigestRow does not "
                "support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not MarketResearchGoldCentralBankPurchaseSurpriseDigestRow:
            raise ValueError(
                "row must be exactly "
                "MarketResearchGoldCentralBankPurchaseSurpriseDigestRow",
            )
        for field_name in ("surprise_key", "condition_id", "central_bank"):
            _require_public_string(field_name, getattr(self, field_name))
        _require_status("digest_status", self.digest_status)
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in (
            "signal_age_seconds",
            "reporting_lag_seconds",
            "reported_purchase_tonnage",
            "expected_purchase_tonnage",
            "purchase_surprise_tonnage_abs",
            "reserve_revision_tonnage_abs",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "confirmation_source_count",
            _require_nonnegative_count_decimal(
                "confirmation_source_count",
                self.confirmation_source_count,
            ),
        )
        _require_surprise_direction(
            "purchase_surprise_direction",
            self.purchase_surprise_direction,
        )
        for field_name in (
            "fx_reserve_share_pressure",
            "commodity_event_alignment_score",
            "base_confidence",
            "confidence_decay_factor",
            "final_confidence",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "redacted_public_report_reference",
            _require_redacted_reference(
                "redacted_public_report_reference",
                self.redacted_public_report_reference,
            ),
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
class MarketResearchGoldCentralBankPurchaseSurpriseDigestReasonCodeCount:
    reason_code: str
    count: Decimal
    signal_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketResearchGoldCentralBankPurchaseSurpriseDigestReasonCodeCount:
            raise TypeError(
                "MarketResearchGoldCentralBankPurchaseSurpriseDigestReasonCodeCount "
                "does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not MarketResearchGoldCentralBankPurchaseSurpriseDigestReasonCodeCount:
            raise ValueError(
                "reason code count must be exactly "
                "MarketResearchGoldCentralBankPurchaseSurpriseDigestReasonCodeCount",
            )
        _require_reason_code("reason_code", self.reason_code)
        object.__setattr__(
            self,
            "count",
            _require_nonnegative_count_decimal("count", self.count),
        )
        object.__setattr__(
            self,
            "signal_ratio",
            _require_ratio_decimal("signal_ratio", self.signal_ratio),
        )
        _require_hard_flags("reason code count", self)


@dataclass(frozen=True)
class MarketResearchGoldCentralBankPurchaseSurpriseDigestReport:
    generated_at: datetime
    config_version: str
    digest_status: str
    recommended_next_step: str
    signal_count: Decimal
    ready_signal_count: Decimal
    watch_signal_count: Decimal
    blocked_signal_count: Decimal
    stale_report_signal_count: Decimal
    reporting_lag_signal_count: Decimal
    confirmation_source_gap_signal_count: Decimal
    purchase_surprise_gap_signal_count: Decimal
    reserve_revision_gap_signal_count: Decimal
    fx_reserve_share_pressure_gap_signal_count: Decimal
    commodity_alignment_gap_signal_count: Decimal
    total_confidence_decay: Decimal
    average_final_confidence: Decimal
    average_purchase_surprise_tonnage_abs: Decimal
    average_reserve_revision_tonnage_abs: Decimal
    average_fx_reserve_share_pressure: Decimal
    average_commodity_event_alignment_score: Decimal
    max_report_age_seconds: Decimal
    max_reporting_lag_seconds: Decimal
    min_purchase_surprise_tonnage_abs: Decimal
    min_reserve_revision_tonnage_abs: Decimal
    min_confirmation_source_count: Decimal
    min_fx_reserve_share_pressure: Decimal
    min_commodity_event_alignment_score: Decimal
    max_observed_signal_age_seconds: Decimal
    rows: tuple[MarketResearchGoldCentralBankPurchaseSurpriseDigestRow, ...]
    signal_config_versions: tuple[tuple[str, str], ...]
    reason_code_counts: tuple[
        MarketResearchGoldCentralBankPurchaseSurpriseDigestReasonCodeCount,
        ...,
    ]
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketResearchGoldCentralBankPurchaseSurpriseDigestReport:
            raise TypeError(
                "MarketResearchGoldCentralBankPurchaseSurpriseDigestReport does not "
                "support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not MarketResearchGoldCentralBankPurchaseSurpriseDigestReport:
            raise ValueError(
                "report must be exactly "
                "MarketResearchGoldCentralBankPurchaseSurpriseDigestReport",
            )
        object.__setattr__(
            self,
            "generated_at",
            _as_utc("generated_at", self.generated_at),
        )
        _require_canonical_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_MARKET_RESEARCH_GOLD_CENTRAL_BANK_PURCHASE_SURPRISE_DIGEST_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        _require_status("digest_status", self.digest_status)
        _require_canonical_string("recommended_next_step", self.recommended_next_step)
        for field_name in (
            "signal_count",
            "ready_signal_count",
            "watch_signal_count",
            "blocked_signal_count",
            "stale_report_signal_count",
            "reporting_lag_signal_count",
            "confirmation_source_gap_signal_count",
            "purchase_surprise_gap_signal_count",
            "reserve_revision_gap_signal_count",
            "fx_reserve_share_pressure_gap_signal_count",
            "commodity_alignment_gap_signal_count",
            "min_confirmation_source_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_count_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "total_confidence_decay",
            "average_purchase_surprise_tonnage_abs",
            "average_reserve_revision_tonnage_abs",
            "max_report_age_seconds",
            "max_reporting_lag_seconds",
            "min_purchase_surprise_tonnage_abs",
            "min_reserve_revision_tonnage_abs",
            "max_observed_signal_age_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "average_final_confidence",
            "average_fx_reserve_share_pressure",
            "average_commodity_event_alignment_score",
            "min_fx_reserve_share_pressure",
            "min_commodity_event_alignment_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
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
            _normalize_reason_codes(self.reason_codes, sequence=REASON_CODE_SEQUENCE),
        )
        _validate_report(self)
        _require_hard_flags("report", self)


def build_market_research_gold_central_bank_purchase_surprise_digest(
    signals: Iterable[MarketResearchGoldCentralBankPurchaseSurpriseDigestSignal],
    *,
    config: MarketResearchGoldCentralBankPurchaseSurpriseDigestConfig | None = None,
    generated_at: datetime,
) -> MarketResearchGoldCentralBankPurchaseSurpriseDigestReport:
    cfg = config or MarketResearchGoldCentralBankPurchaseSurpriseDigestConfig()
    if type(cfg) is not MarketResearchGoldCentralBankPurchaseSurpriseDigestConfig:
        raise ValueError(
            "config must be exactly "
            "MarketResearchGoldCentralBankPurchaseSurpriseDigestConfig",
        )
    _require_hard_flags("config", cfg)
    generated_at_utc = _as_utc("generated_at", generated_at)
    normalized_signals = _normalize_signals(signals)
    rows = tuple(
        sorted(
            (
                _row_for_signal(signal, config=cfg, generated_at=generated_at_utc)
                for signal in normalized_signals
            ),
            key=lambda row: (_row_sort_value(row), row.surprise_key, row.condition_id),
        ),
    )
    report_status = _report_status(rows)
    signal_count = _decimal_count(len(rows))
    reason_code_counts = _reason_code_counts(rows)
    return MarketResearchGoldCentralBankPurchaseSurpriseDigestReport(
        generated_at=generated_at_utc,
        config_version=cfg.config_version,
        digest_status=report_status,
        recommended_next_step=NEXT_STEPS[report_status],
        signal_count=signal_count,
        ready_signal_count=_status_count(rows, STATUS_READY),
        watch_signal_count=_status_count(rows, STATUS_WATCH),
        blocked_signal_count=_status_count(rows, STATUS_BLOCKED),
        stale_report_signal_count=_reason_signal_count(
            rows,
            STALE_REPORT_SIGNAL_REASON,
        ),
        reporting_lag_signal_count=_reason_signal_count(rows, REPORTING_LAG_REASON),
        confirmation_source_gap_signal_count=_reason_signal_count(
            rows,
            CONFIRMATION_SOURCE_GAP_REASON,
        ),
        purchase_surprise_gap_signal_count=_reason_signal_count(
            rows,
            PURCHASE_SURPRISE_GAP_REASON,
        ),
        reserve_revision_gap_signal_count=_reason_signal_count(
            rows,
            RESERVE_REVISION_GAP_REASON,
        ),
        fx_reserve_share_pressure_gap_signal_count=_reason_signal_count(
            rows,
            FX_RESERVE_SHARE_PRESSURE_GAP_REASON,
        ),
        commodity_alignment_gap_signal_count=_reason_signal_count(
            rows,
            COMMODITY_ALIGNMENT_GAP_REASON,
        ),
        total_confidence_decay=_decimal_sum(
            row.confidence_decay_factor for row in rows
        ),
        average_final_confidence=_ratio(
            _decimal_sum(row.final_confidence for row in rows),
            signal_count,
        ),
        average_purchase_surprise_tonnage_abs=_ratio(
            _decimal_sum(row.purchase_surprise_tonnage_abs for row in rows),
            signal_count,
        ),
        average_reserve_revision_tonnage_abs=_ratio(
            _decimal_sum(row.reserve_revision_tonnage_abs for row in rows),
            signal_count,
        ),
        average_fx_reserve_share_pressure=_ratio(
            _decimal_sum(row.fx_reserve_share_pressure for row in rows),
            signal_count,
        ),
        average_commodity_event_alignment_score=_ratio(
            _decimal_sum(row.commodity_event_alignment_score for row in rows),
            signal_count,
        ),
        max_report_age_seconds=cfg.max_report_age_seconds,
        max_reporting_lag_seconds=cfg.max_reporting_lag_seconds,
        min_purchase_surprise_tonnage_abs=cfg.min_purchase_surprise_tonnage_abs,
        min_reserve_revision_tonnage_abs=cfg.min_reserve_revision_tonnage_abs,
        min_confirmation_source_count=cfg.min_confirmation_source_count,
        min_fx_reserve_share_pressure=cfg.min_fx_reserve_share_pressure,
        min_commodity_event_alignment_score=cfg.min_commodity_event_alignment_score,
        max_observed_signal_age_seconds=max(
            (row.signal_age_seconds for row in rows),
            default=ZERO,
        ),
        rows=rows,
        signal_config_versions=tuple(
            sorted(
                (
                    signal.surprise_key,
                    signal.signal_config_version,
                )
                for signal in normalized_signals
            ),
        ),
        reason_code_counts=reason_code_counts,
        reason_codes=tuple(item.reason_code for item in reason_code_counts),
    )


def market_research_gold_central_bank_purchase_surprise_digest_payload(
    report: MarketResearchGoldCentralBankPurchaseSurpriseDigestReport,
) -> dict[str, Any]:
    if type(report) is not MarketResearchGoldCentralBankPurchaseSurpriseDigestReport:
        raise ValueError(
            "report must be exactly "
            "MarketResearchGoldCentralBankPurchaseSurpriseDigestReport",
        )
    _require_hard_flags("report", report)
    value = _json_ready(asdict(report))
    if type(value) is not dict:
        raise ValueError("value must be a dict")
    return value


def _row_for_signal(
    signal: MarketResearchGoldCentralBankPurchaseSurpriseDigestSignal,
    *,
    config: MarketResearchGoldCentralBankPurchaseSurpriseDigestConfig,
    generated_at: datetime,
) -> MarketResearchGoldCentralBankPurchaseSurpriseDigestRow:
    if signal.observed_at > generated_at:
        raise ValueError("observed_at must not be in the future")
    signal_age_seconds = _age_seconds(generated_at, signal.observed_at)
    surprise_tonnage_abs = _purchase_surprise_tonnage_abs(signal)
    reason_codes = _row_reason_codes(
        signal=signal,
        config=config,
        signal_age_seconds=signal_age_seconds,
        purchase_surprise_tonnage_abs=surprise_tonnage_abs,
    )
    confidence_decay_factor = _confidence_decay_factor(reason_codes, config=config)
    final_confidence = _final_confidence(signal.base_confidence, confidence_decay_factor)
    return MarketResearchGoldCentralBankPurchaseSurpriseDigestRow(
        surprise_key=signal.surprise_key,
        condition_id=signal.condition_id,
        central_bank=signal.central_bank,
        digest_status=_row_status(
            reason_codes,
            final_confidence=final_confidence,
            watch_confidence_threshold=config.watch_confidence_threshold,
        ),
        observed_at=signal.observed_at,
        signal_age_seconds=signal_age_seconds,
        reporting_lag_seconds=signal.reporting_lag_seconds,
        reported_purchase_tonnage=signal.reported_purchase_tonnage,
        expected_purchase_tonnage=signal.expected_purchase_tonnage,
        purchase_surprise_direction=_purchase_surprise_direction(signal),
        purchase_surprise_tonnage_abs=surprise_tonnage_abs,
        reserve_revision_tonnage_abs=signal.reserve_revision_tonnage_abs,
        confirmation_source_count=signal.confirmation_source_count,
        fx_reserve_share_pressure=signal.fx_reserve_share_pressure,
        commodity_event_alignment_score=signal.commodity_event_alignment_score,
        base_confidence=signal.base_confidence,
        confidence_decay_factor=confidence_decay_factor,
        final_confidence=final_confidence,
        redacted_public_report_reference=_redacted_reference(
            signal.public_report_reference,
        ),
        reason_codes=reason_codes,
    )


def _row_reason_codes(
    *,
    signal: MarketResearchGoldCentralBankPurchaseSurpriseDigestSignal,
    config: MarketResearchGoldCentralBankPurchaseSurpriseDigestConfig,
    signal_age_seconds: Decimal,
    purchase_surprise_tonnage_abs: Decimal,
) -> tuple[str, ...]:
    reasons: list[str] = []
    if signal_age_seconds > config.max_report_age_seconds:
        reasons.append(STALE_REPORT_SIGNAL_REASON)
    if signal.reporting_lag_seconds > config.max_reporting_lag_seconds:
        reasons.append(REPORTING_LAG_REASON)
    if signal.confirmation_source_count < config.min_confirmation_source_count:
        reasons.append(CONFIRMATION_SOURCE_GAP_REASON)
    if purchase_surprise_tonnage_abs < config.min_purchase_surprise_tonnage_abs:
        reasons.append(PURCHASE_SURPRISE_GAP_REASON)
    if signal.reserve_revision_tonnage_abs < config.min_reserve_revision_tonnage_abs:
        reasons.append(RESERVE_REVISION_GAP_REASON)
    if signal.fx_reserve_share_pressure < config.min_fx_reserve_share_pressure:
        reasons.append(FX_RESERVE_SHARE_PRESSURE_GAP_REASON)
    if (
        signal.commodity_event_alignment_score
        < config.min_commodity_event_alignment_score
    ):
        reasons.append(COMMODITY_ALIGNMENT_GAP_REASON)
    if not reasons:
        return (READY_REASON,)
    return tuple(reason for reason in ROW_REASON_CODE_SEQUENCE if reason in reasons)


def _purchase_surprise_tonnage_abs(
    signal: MarketResearchGoldCentralBankPurchaseSurpriseDigestSignal,
) -> Decimal:
    return _quantize(abs(signal.reported_purchase_tonnage - signal.expected_purchase_tonnage))


def _purchase_surprise_direction(
    signal: MarketResearchGoldCentralBankPurchaseSurpriseDigestSignal,
) -> str:
    if signal.reported_purchase_tonnage > signal.expected_purchase_tonnage:
        return SURPRISE_DIRECTION_ABOVE
    if signal.reported_purchase_tonnage < signal.expected_purchase_tonnage:
        return SURPRISE_DIRECTION_BELOW
    return SURPRISE_DIRECTION_INLINE


def _confidence_decay_factor(
    reason_codes: tuple[str, ...],
    *,
    config: MarketResearchGoldCentralBankPurchaseSurpriseDigestConfig,
) -> Decimal:
    gap_count = sum(1 for reason_code in reason_codes if reason_code != READY_REASON)
    value = _quantize(config.confidence_decay_per_gap * _decimal_count(gap_count))
    if value > ONE:
        return ONE
    return value


def _final_confidence(base_confidence: Decimal, confidence_decay_factor: Decimal) -> Decimal:
    value = base_confidence - confidence_decay_factor
    if value < ZERO:
        return ZERO
    return _require_ratio_decimal("final_confidence", value)


def _row_status(
    reason_codes: tuple[str, ...],
    *,
    final_confidence: Decimal,
    watch_confidence_threshold: Decimal,
) -> str:
    if reason_codes == (READY_REASON,):
        return STATUS_READY
    if final_confidence < watch_confidence_threshold:
        return STATUS_BLOCKED
    return STATUS_WATCH


def _report_status(
    rows: tuple[MarketResearchGoldCentralBankPurchaseSurpriseDigestRow, ...],
) -> str:
    if not rows:
        return STATUS_BLOCKED
    if any(row.digest_status == STATUS_BLOCKED for row in rows):
        return STATUS_BLOCKED
    if any(row.digest_status == STATUS_WATCH for row in rows):
        return STATUS_WATCH
    return STATUS_READY


def _row_sort_value(
    row: MarketResearchGoldCentralBankPurchaseSurpriseDigestRow,
) -> Decimal:
    if row.digest_status == STATUS_BLOCKED:
        return ZERO
    if row.digest_status == STATUS_WATCH:
        return ONE
    return Decimal("2.000000")


def _status_count(
    rows: tuple[MarketResearchGoldCentralBankPurchaseSurpriseDigestRow, ...],
    status: str,
) -> Decimal:
    return _decimal_count(sum(1 for row in rows if row.digest_status == status))


def _reason_signal_count(
    rows: tuple[MarketResearchGoldCentralBankPurchaseSurpriseDigestRow, ...],
    reason_code: str,
) -> Decimal:
    return _decimal_count(sum(1 for row in rows if reason_code in row.reason_codes))


def _reason_code_counts(
    rows: tuple[MarketResearchGoldCentralBankPurchaseSurpriseDigestRow, ...],
) -> tuple[MarketResearchGoldCentralBankPurchaseSurpriseDigestReasonCodeCount, ...]:
    signal_count = _decimal_count(len(rows))
    if not rows:
        return (
            MarketResearchGoldCentralBankPurchaseSurpriseDigestReasonCodeCount(
                reason_code=NO_INPUTS_REASON,
                count=ONE,
                signal_ratio=ZERO,
            ),
        )
    return tuple(
        MarketResearchGoldCentralBankPurchaseSurpriseDigestReasonCodeCount(
            reason_code=reason_code,
            count=count,
            signal_ratio=_ratio(count, signal_count),
        )
        for reason_code in REASON_CODE_SEQUENCE
        if reason_code != NO_INPUTS_REASON
        if (count := _reason_signal_count(rows, reason_code)) > ZERO
    )


def _normalize_signals(
    signals: Iterable[MarketResearchGoldCentralBankPurchaseSurpriseDigestSignal],
) -> tuple[MarketResearchGoldCentralBankPurchaseSurpriseDigestSignal, ...]:
    if isinstance(signals, (str, bytes)):
        raise ValueError("signals must be an iterable of digest signals")
    try:
        rows = tuple(signals)
    except TypeError as exc:
        raise ValueError("signals must be an iterable of digest signals") from exc
    seen: set[str] = set()
    for signal in rows:
        if type(signal) is not MarketResearchGoldCentralBankPurchaseSurpriseDigestSignal:
            raise ValueError(
                "signals must contain "
                "MarketResearchGoldCentralBankPurchaseSurpriseDigestSignal",
            )
        _require_hard_flags("signal", signal)
        if signal.surprise_key in seen:
            raise ValueError("duplicate surprise_key values are not supported")
        seen.add(signal.surprise_key)
    return rows


def _normalize_rows(
    value: object,
) -> tuple[MarketResearchGoldCentralBankPurchaseSurpriseDigestRow, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError("rows must contain digest rows")
    try:
        rows = tuple(value)  # type: ignore[arg-type]
    except TypeError as exc:
        raise ValueError("rows must contain digest rows") from exc
    for row in rows:
        if type(row) is not MarketResearchGoldCentralBankPurchaseSurpriseDigestRow:
            raise ValueError(
                "rows must contain "
                "MarketResearchGoldCentralBankPurchaseSurpriseDigestRow",
            )
        _require_hard_flags("row", row)
    expected = tuple(
        sorted(rows, key=lambda row: (_row_sort_value(row), row.surprise_key, row.condition_id)),
    )
    if rows != expected:
        raise ValueError("rows must use deterministic sort")
    if len({row.surprise_key for row in rows}) != len(rows):
        raise ValueError("duplicate surprise_key values are not supported")
    return rows


def _normalize_signal_config_versions(value: object) -> tuple[tuple[str, str], ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError("signal_config_versions must contain pairs")
    try:
        rows = tuple(tuple(item) for item in value)  # type: ignore[arg-type]
    except TypeError as exc:
        raise ValueError("signal_config_versions must contain pairs") from exc
    normalized: list[tuple[str, str]] = []
    for row in rows:
        if len(row) != 2:
            raise ValueError("signal_config_versions rows must be pairs")
        surprise_key, config_version = row
        _require_public_string("surprise_key", surprise_key)
        _require_public_string("signal_config_version", config_version)
        normalized.append((surprise_key, config_version))
    result = tuple(normalized)
    if result != tuple(sorted(result)):
        raise ValueError("signal_config_versions must use deterministic sort")
    if len({surprise_key for surprise_key, _ in result}) != len(result):
        raise ValueError("duplicate surprise_key values are not supported")
    return result


def _normalize_reason_code_counts(
    value: object,
) -> tuple[MarketResearchGoldCentralBankPurchaseSurpriseDigestReasonCodeCount, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError("reason_code_counts must contain reason code count rows")
    try:
        rows = tuple(value)  # type: ignore[arg-type]
    except TypeError as exc:
        raise ValueError("reason_code_counts must contain reason code count rows") from exc
    seen: set[str] = set()
    for row in rows:
        if type(row) is not MarketResearchGoldCentralBankPurchaseSurpriseDigestReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "MarketResearchGoldCentralBankPurchaseSurpriseDigestReasonCodeCount",
            )
        if row.reason_code in seen:
            raise ValueError("reason_code_counts must be unique")
        seen.add(row.reason_code)
    expected = tuple(
        item
        for reason_code in REASON_CODE_SEQUENCE
        for item in rows
        if item.reason_code == reason_code
    )
    if rows != expected:
        raise ValueError("reason_code_counts must use deterministic sort")
    return rows


def _normalize_reason_codes(
    value: object,
    *,
    sequence: tuple[str, ...],
) -> tuple[str, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError("reason_codes must contain reason strings")
    try:
        reason_codes = tuple(value)  # type: ignore[arg-type]
    except TypeError as exc:
        raise ValueError("reason_codes must contain reason strings") from exc
    if not reason_codes:
        raise ValueError("reason_codes must not be empty")
    for reason_code in reason_codes:
        if type(reason_code) is not str:
            raise ValueError("reason_code must be a string")
        if reason_code not in sequence:
            raise ValueError("reason_code must be known")
    if len(set(reason_codes)) != len(reason_codes):
        raise ValueError("reason_codes must be unique")
    if tuple(reason for reason in sequence if reason in reason_codes) != reason_codes:
        raise ValueError("reason_codes must use deterministic sort")
    return reason_codes


def _validate_row(row: MarketResearchGoldCentralBankPurchaseSurpriseDigestRow) -> None:
    expected_surprise_tonnage_abs = _quantize(
        abs(row.reported_purchase_tonnage - row.expected_purchase_tonnage),
    )
    if row.purchase_surprise_tonnage_abs != expected_surprise_tonnage_abs:
        raise ValueError("purchase_surprise_tonnage_abs must match purchase values")
    if row.purchase_surprise_direction != _row_purchase_surprise_direction(row):
        raise ValueError("purchase_surprise_direction must match purchase values")
    if row.final_confidence != _final_confidence(
        row.base_confidence,
        row.confidence_decay_factor,
    ):
        raise ValueError("final_confidence must match confidence decay")
    if row.reason_codes == (READY_REASON,):
        if row.digest_status != STATUS_READY:
            raise ValueError("ready rows must have ready status")
        if row.confidence_decay_factor != ZERO:
            raise ValueError("ready rows must not have confidence decay")
    elif row.digest_status == STATUS_READY:
        raise ValueError("ready status requires ready reason code")


def _validate_report(report: MarketResearchGoldCentralBankPurchaseSurpriseDigestReport) -> None:
    if report.signal_count != _decimal_count(len(report.rows)):
        raise ValueError("signal_count must match rows")
    if report.ready_signal_count != _status_count(report.rows, STATUS_READY):
        raise ValueError("ready_signal_count must match rows")
    if report.watch_signal_count != _status_count(report.rows, STATUS_WATCH):
        raise ValueError("watch_signal_count must match rows")
    if report.blocked_signal_count != _status_count(report.rows, STATUS_BLOCKED):
        raise ValueError("blocked_signal_count must match rows")
    reason_checks = (
        ("stale_report_signal_count", STALE_REPORT_SIGNAL_REASON),
        ("reporting_lag_signal_count", REPORTING_LAG_REASON),
        ("confirmation_source_gap_signal_count", CONFIRMATION_SOURCE_GAP_REASON),
        ("purchase_surprise_gap_signal_count", PURCHASE_SURPRISE_GAP_REASON),
        ("reserve_revision_gap_signal_count", RESERVE_REVISION_GAP_REASON),
        (
            "fx_reserve_share_pressure_gap_signal_count",
            FX_RESERVE_SHARE_PRESSURE_GAP_REASON,
        ),
        ("commodity_alignment_gap_signal_count", COMMODITY_ALIGNMENT_GAP_REASON),
    )
    for field_name, reason_code in reason_checks:
        if getattr(report, field_name) != _reason_signal_count(report.rows, reason_code):
            raise ValueError(f"{field_name} must match rows")
    if report.total_confidence_decay != _decimal_sum(
        row.confidence_decay_factor for row in report.rows
    ):
        raise ValueError("total_confidence_decay must match rows")
    if report.average_final_confidence != _ratio(
        _decimal_sum(row.final_confidence for row in report.rows),
        report.signal_count,
    ):
        raise ValueError("average_final_confidence must match rows")
    if report.average_purchase_surprise_tonnage_abs != _ratio(
        _decimal_sum(row.purchase_surprise_tonnage_abs for row in report.rows),
        report.signal_count,
    ):
        raise ValueError("average_purchase_surprise_tonnage_abs must match rows")
    if report.average_reserve_revision_tonnage_abs != _ratio(
        _decimal_sum(row.reserve_revision_tonnage_abs for row in report.rows),
        report.signal_count,
    ):
        raise ValueError("average_reserve_revision_tonnage_abs must match rows")
    if report.average_fx_reserve_share_pressure != _ratio(
        _decimal_sum(row.fx_reserve_share_pressure for row in report.rows),
        report.signal_count,
    ):
        raise ValueError("average_fx_reserve_share_pressure must match rows")
    if report.average_commodity_event_alignment_score != _ratio(
        _decimal_sum(row.commodity_event_alignment_score for row in report.rows),
        report.signal_count,
    ):
        raise ValueError("average_commodity_event_alignment_score must match rows")
    if report.max_observed_signal_age_seconds != max(
        (row.signal_age_seconds for row in report.rows),
        default=ZERO,
    ):
        raise ValueError("max_observed_signal_age_seconds must match rows")
    if report.digest_status != _report_status(report.rows):
        raise ValueError("digest_status must match rows")
    if report.recommended_next_step != NEXT_STEPS[report.digest_status]:
        raise ValueError("recommended_next_step must match digest_status")
    if len(report.signal_config_versions) != len(report.rows):
        raise ValueError("signal_config_versions must match rows")
    expected_signal_ids = tuple(sorted(row.surprise_key for row in report.rows))
    actual_signal_ids = tuple(
        surprise_key for surprise_key, _ in report.signal_config_versions
    )
    if actual_signal_ids != expected_signal_ids:
        raise ValueError("signal_config_versions must match rows")
    if report.reason_code_counts != _reason_code_counts(report.rows):
        raise ValueError("reason_code_counts must match rows")
    if report.reason_codes != tuple(item.reason_code for item in report.reason_code_counts):
        raise ValueError("reason_codes must match reason_code_counts")


def _row_purchase_surprise_direction(
    row: MarketResearchGoldCentralBankPurchaseSurpriseDigestRow,
) -> str:
    if row.reported_purchase_tonnage > row.expected_purchase_tonnage:
        return SURPRISE_DIRECTION_ABOVE
    if row.reported_purchase_tonnage < row.expected_purchase_tonnage:
        return SURPRISE_DIRECTION_BELOW
    return SURPRISE_DIRECTION_INLINE


def _decimal_count(value: int) -> Decimal:
    return Decimal(value).quantize(QUANT)


def _decimal_sum(values: Iterable[Decimal]) -> Decimal:
    total = ZERO
    for value in values:
        total += value
    return _quantize(total)


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return _quantize(numerator / denominator)


def _age_seconds(generated_at: datetime, observed_at: datetime) -> Decimal:
    delta = generated_at - observed_at
    seconds = Decimal(delta.days * 86400 + delta.seconds)
    subseconds = Decimal(delta.microseconds) / MICROSECONDS_PER_SECOND
    return _require_nonnegative_decimal("signal_age_seconds", seconds + subseconds)


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _quantize(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(QUANT)


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return _quantize(value)


def _require_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _require_positive_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_nonnegative_decimal(field_name, value)
    if normalized <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _require_nonnegative_count_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_nonnegative_decimal(field_name, value)
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{field_name} must be an integer Decimal")
    return normalized


def _require_positive_count_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_nonnegative_count_decimal(field_name, value)
    if normalized <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _require_ratio_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_nonnegative_decimal(field_name, value)
    if normalized > ONE:
        raise ValueError(f"{field_name} must be between zero and one")
    return normalized


def _require_canonical_string(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if value != value.strip() or not value:
        raise ValueError(f"{field_name} must be a canonical string")
    return value


def _require_public_string(field_name: str, value: object) -> str:
    normalized = _require_canonical_string(field_name, value)
    lowered = normalized.lower()
    if any(fragment in lowered for fragment in UNSAFE_TEXT_FRAGMENTS):
        raise ValueError(f"{field_name} must be safe public text")
    return normalized


def _require_status(field_name: str, value: object) -> str:
    normalized = _require_canonical_string(field_name, value)
    if normalized not in DIGEST_STATUSES:
        raise ValueError(f"{field_name} must be a known status")
    return normalized


def _require_surprise_direction(field_name: str, value: object) -> str:
    normalized = _require_canonical_string(field_name, value)
    if normalized not in SURPRISE_DIRECTIONS:
        raise ValueError(f"{field_name} must be a known surprise direction")
    return normalized


def _require_reason_code(field_name: str, value: object) -> str:
    normalized = _require_canonical_string(field_name, value)
    if normalized not in REASON_CODE_SEQUENCE:
        raise ValueError(f"{field_name} must be a known reason code")
    return normalized


def _require_redacted_reference(field_name: str, value: object) -> str:
    normalized = _require_canonical_string(field_name, value)
    if normalized.startswith("sha256:"):
        suffix = normalized.removeprefix("sha256:")
        if len(suffix) != 12 or not all(character in "0123456789abcdef" for character in suffix):
            raise ValueError(f"{field_name} must be a redacted reference")
        return normalized
    lowered = normalized.lower()
    if any(fragment in lowered for fragment in UNSAFE_TEXT_FRAGMENTS):
        raise ValueError(f"{field_name} must be redacted")
    return normalized


def _redacted_reference(value: str) -> str:
    lowered = value.lower()
    if not any(fragment in lowered for fragment in UNSAFE_TEXT_FRAGMENTS):
        return value
    return f"sha256:{sha256(value.encode('utf-8')).hexdigest()[:12]}"


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        flag = getattr(value, field_name, None)
        if type(flag) is not bool or flag is not True:
            raise ValueError(f"{label} {field_name} must be True")


def _json_ready(value: object) -> Any:
    if isinstance(value, Decimal):
        return format(_quantize(value), "f")
    if isinstance(value, datetime):
        return _as_utc("datetime", value).isoformat()
    if isinstance(value, tuple):
        return [_json_ready(item) for item in value]
    if isinstance(value, list):
        return [_json_ready(item) for item in value]
    if isinstance(value, dict):
        return {key: _json_ready(item) for key, item in value.items()}
    return value
