"""Pure Phase 1 gold vault flow research reducer."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
from typing import Any


DEFAULT_MARKET_RESEARCH_GOLD_VAULT_FLOW_DIGEST_CONFIG_VERSION = (
    "market-research-gold-vault-flow-digest-v0"
)

STATUS_READY = "ready"
STATUS_WATCH = "watch"
STATUS_BLOCKED = "blocked"
DIGEST_STATUSES = (STATUS_READY, STATUS_WATCH, STATUS_BLOCKED)

REASON_PREFIX = "market_research_gold_vault_flow_digest_"
NO_INPUTS_REASON = f"{REASON_PREFIX}no_inputs"
READY_REASON = f"{REASON_PREFIX}ready"
STALE_VAULT_FLOW_SIGNAL_REASON = f"{REASON_PREFIX}stale_vault_flow_signal"
THIN_CONFIRMATION_REASON = f"{REASON_PREFIX}thin_confirmation"
LOW_FLOW_TONNAGE_REASON = f"{REASON_PREFIX}low_flow_tonnage"
INVENTORY_PRESSURE_GAP_REASON = f"{REASON_PREFIX}inventory_pressure_gap"
DELIVERY_ALIGNMENT_GAP_REASON = f"{REASON_PREFIX}delivery_alignment_gap"
STALE_SOURCE_RATIO_REASON = f"{REASON_PREFIX}stale_source_ratio"

REASON_CODE_SEQUENCE = (
    INVENTORY_PRESSURE_GAP_REASON,
    STALE_VAULT_FLOW_SIGNAL_REASON,
    THIN_CONFIRMATION_REASON,
    LOW_FLOW_TONNAGE_REASON,
    DELIVERY_ALIGNMENT_GAP_REASON,
    STALE_SOURCE_RATIO_REASON,
    READY_REASON,
    NO_INPUTS_REASON,
)
ROW_REASON_CODE_SEQUENCE = (
    STALE_VAULT_FLOW_SIGNAL_REASON,
    THIN_CONFIRMATION_REASON,
    LOW_FLOW_TONNAGE_REASON,
    INVENTORY_PRESSURE_GAP_REASON,
    DELIVERY_ALIGNMENT_GAP_REASON,
    STALE_SOURCE_RATIO_REASON,
    READY_REASON,
)
NEXT_STEPS = {
    STATUS_READY: "allow_report_only_market_research_gold_vault_flow_digest",
    STATUS_WATCH: "monitor_report_only_market_research_gold_vault_flow_digest",
    STATUS_BLOCKED: "block_report_only_market_research_gold_vault_flow_digest",
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
        _join_parts("wal", "let"),
        _join_parts("bro", "ker"),
        _join_parts("or", "der"),
        _join_parts("sub", "mit"),
        _join_parts("can", "cel"),
        _join_parts("rep", "lace"),
        _join_parts("ex", "change"),
        _join_parts("sig", "ning"),
        _join_parts("tra", "de"),
        _join_parts("trad", "ing"),
        _join_parts("net", "work"),
        _join_parts("data", "base"),
        _join_parts("per", "sist"),
        _join_parts("sec", "ret"),
        _join_parts("to", "ken"),
        _join_parts("pri", "vate"),
        _join_parts("acc", "ount"),
        _join_parts("ad", "vice"),
    ),
)

PUBLIC_LABEL_CHARS = frozenset("abcdefghijklmnopqrstuvwxyz0123456789._-")

__all__ = (
    "DEFAULT_MARKET_RESEARCH_GOLD_VAULT_FLOW_DIGEST_CONFIG_VERSION",
    "MarketResearchGoldVaultFlowDigestConfig",
    "MarketResearchGoldVaultFlowDigestReasonCodeCount",
    "MarketResearchGoldVaultFlowDigestReport",
    "MarketResearchGoldVaultFlowDigestRow",
    "MarketResearchGoldVaultFlowDigestSignal",
    "build_market_research_gold_vault_flow_digest",
    "market_research_gold_vault_flow_digest_payload",
)


@dataclass(frozen=True)
class MarketResearchGoldVaultFlowDigestConfig:
    config_version: str = DEFAULT_MARKET_RESEARCH_GOLD_VAULT_FLOW_DIGEST_CONFIG_VERSION
    max_flow_age_seconds: Decimal = Decimal("7200.000000")
    min_flow_tonnage_abs: Decimal = Decimal("3.000000")
    min_confirmation_source_count: Decimal = Decimal("2.000000")
    min_inventory_pressure_score: Decimal = Decimal("0.550000")
    min_delivery_alignment_score: Decimal = Decimal("0.500000")
    max_stale_source_ratio: Decimal = Decimal("0.250000")
    watch_confidence_threshold: Decimal = Decimal("0.650000")
    confidence_decay_per_gap: Decimal = Decimal("0.100000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketResearchGoldVaultFlowDigestConfig:
            raise TypeError(
                "MarketResearchGoldVaultFlowDigestConfig does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not MarketResearchGoldVaultFlowDigestConfig:
            raise ValueError(
                "config must be exactly MarketResearchGoldVaultFlowDigestConfig",
            )
        _require_canonical_string("config_version", self.config_version)
        if self.config_version != DEFAULT_MARKET_RESEARCH_GOLD_VAULT_FLOW_DIGEST_CONFIG_VERSION:
            raise ValueError("config_version must be the supported config version")
        for field_name in ("max_flow_age_seconds", "min_flow_tonnage_abs"):
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
            "min_inventory_pressure_score",
            "min_delivery_alignment_score",
            "max_stale_source_ratio",
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
class MarketResearchGoldVaultFlowDigestSignal:
    vault_flow_key: str
    condition_id: str
    vault_venue: str
    flow_direction: str
    public_signal_reference: str
    observed_at: datetime
    flow_tonnage_abs: Decimal
    confirmation_source_count: Decimal
    inventory_pressure_score: Decimal
    delivery_alignment_score: Decimal
    stale_source_ratio: Decimal
    base_confidence: Decimal
    signal_config_version: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketResearchGoldVaultFlowDigestSignal:
            raise TypeError(
                "MarketResearchGoldVaultFlowDigestSignal does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not MarketResearchGoldVaultFlowDigestSignal:
            raise ValueError(
                "signal must be exactly MarketResearchGoldVaultFlowDigestSignal",
            )
        for field_name in (
            "vault_flow_key",
            "condition_id",
            "vault_venue",
            "signal_config_version",
        ):
            _require_public_string(field_name, getattr(self, field_name))
        _require_flow_direction("flow_direction", self.flow_direction)
        _require_canonical_string("public_signal_reference", self.public_signal_reference)
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        object.__setattr__(
            self,
            "flow_tonnage_abs",
            _require_nonnegative_decimal("flow_tonnage_abs", self.flow_tonnage_abs),
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
            "inventory_pressure_score",
            "delivery_alignment_score",
            "stale_source_ratio",
            "base_confidence",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        _require_hard_flags("signal", self)


@dataclass(frozen=True)
class MarketResearchGoldVaultFlowDigestRow:
    vault_flow_key: str
    condition_id: str
    vault_venue: str
    flow_direction: str
    digest_status: str
    observed_at: datetime
    signal_age_seconds: Decimal
    flow_tonnage_abs: Decimal
    confirmation_source_count: Decimal
    inventory_pressure_score: Decimal
    delivery_alignment_score: Decimal
    stale_source_ratio: Decimal
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
        if cls is not MarketResearchGoldVaultFlowDigestRow:
            raise TypeError(
                "MarketResearchGoldVaultFlowDigestRow does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not MarketResearchGoldVaultFlowDigestRow:
            raise ValueError("row must be exactly MarketResearchGoldVaultFlowDigestRow")
        for field_name in ("vault_flow_key", "condition_id", "vault_venue"):
            _require_public_string(field_name, getattr(self, field_name))
        _require_flow_direction("flow_direction", self.flow_direction)
        _require_status("digest_status", self.digest_status)
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        object.__setattr__(
            self,
            "signal_age_seconds",
            _require_nonnegative_count_decimal(
                "signal_age_seconds",
                self.signal_age_seconds,
            ),
        )
        object.__setattr__(
            self,
            "flow_tonnage_abs",
            _require_nonnegative_decimal("flow_tonnage_abs", self.flow_tonnage_abs),
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
            "inventory_pressure_score",
            "delivery_alignment_score",
            "stale_source_ratio",
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
            "redacted_public_signal_reference",
            _require_redacted_reference(
                "redacted_public_signal_reference",
                self.redacted_public_signal_reference,
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
class MarketResearchGoldVaultFlowDigestReasonCodeCount:
    reason_code: str
    count: Decimal
    signal_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketResearchGoldVaultFlowDigestReasonCodeCount:
            raise TypeError(
                "MarketResearchGoldVaultFlowDigestReasonCodeCount does not support "
                "subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not MarketResearchGoldVaultFlowDigestReasonCodeCount:
            raise ValueError(
                "reason count must be exactly "
                "MarketResearchGoldVaultFlowDigestReasonCodeCount",
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
class MarketResearchGoldVaultFlowDigestReport:
    generated_at: datetime
    config_version: str
    digest_status: str
    recommended_next_step: str
    signal_count: Decimal
    ready_signal_count: Decimal
    watch_signal_count: Decimal
    blocked_signal_count: Decimal
    stale_vault_flow_signal_count: Decimal
    thin_confirmation_signal_count: Decimal
    low_flow_tonnage_signal_count: Decimal
    inventory_pressure_gap_signal_count: Decimal
    delivery_alignment_gap_signal_count: Decimal
    stale_source_signal_count: Decimal
    total_confidence_decay: Decimal
    average_final_confidence: Decimal
    average_flow_tonnage_abs: Decimal
    average_inventory_pressure_score: Decimal
    average_delivery_alignment_score: Decimal
    max_flow_age_seconds: Decimal
    min_flow_tonnage_abs: Decimal
    min_confirmation_source_count: Decimal
    min_inventory_pressure_score: Decimal
    min_delivery_alignment_score: Decimal
    max_stale_source_ratio: Decimal
    max_observed_signal_age_seconds: Decimal
    rows: tuple[MarketResearchGoldVaultFlowDigestRow, ...]
    signal_config_versions: tuple[tuple[str, str], ...]
    reason_code_counts: tuple[MarketResearchGoldVaultFlowDigestReasonCodeCount, ...]
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketResearchGoldVaultFlowDigestReport:
            raise TypeError(
                "MarketResearchGoldVaultFlowDigestReport does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not MarketResearchGoldVaultFlowDigestReport:
            raise ValueError(
                "report must be exactly MarketResearchGoldVaultFlowDigestReport",
            )
        object.__setattr__(
            self,
            "generated_at",
            _as_utc("generated_at", self.generated_at),
        )
        _require_canonical_string("config_version", self.config_version)
        if self.config_version != DEFAULT_MARKET_RESEARCH_GOLD_VAULT_FLOW_DIGEST_CONFIG_VERSION:
            raise ValueError("config_version must be the supported config version")
        _require_status("digest_status", self.digest_status)
        _require_canonical_string("recommended_next_step", self.recommended_next_step)
        for field_name in (
            "signal_count",
            "ready_signal_count",
            "watch_signal_count",
            "blocked_signal_count",
            "stale_vault_flow_signal_count",
            "thin_confirmation_signal_count",
            "low_flow_tonnage_signal_count",
            "inventory_pressure_gap_signal_count",
            "delivery_alignment_gap_signal_count",
            "stale_source_signal_count",
            "min_confirmation_source_count",
            "max_observed_signal_age_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_count_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "average_flow_tonnage_abs",
            "max_flow_age_seconds",
            "min_flow_tonnage_abs",
            "total_confidence_decay",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "average_final_confidence",
            "average_inventory_pressure_score",
            "average_delivery_alignment_score",
            "min_inventory_pressure_score",
            "min_delivery_alignment_score",
            "max_stale_source_ratio",
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


def build_market_research_gold_vault_flow_digest(
    signals: Iterable[MarketResearchGoldVaultFlowDigestSignal],
    *,
    config: MarketResearchGoldVaultFlowDigestConfig | None = None,
    generated_at: datetime,
) -> MarketResearchGoldVaultFlowDigestReport:
    cfg = config or MarketResearchGoldVaultFlowDigestConfig()
    if type(cfg) is not MarketResearchGoldVaultFlowDigestConfig:
        raise ValueError("config must be exactly MarketResearchGoldVaultFlowDigestConfig")
    _require_hard_flags("config", cfg)
    generated_at_utc = _as_utc("generated_at", generated_at)
    normalized_signals = _normalize_signals(signals)
    rows = tuple(
        sorted(
            (
                _row_for_signal(signal, config=cfg, generated_at=generated_at_utc)
                for signal in normalized_signals
            ),
            key=lambda row: (_row_sort_value(row), row.vault_flow_key, row.condition_id),
        ),
    )
    report_status = _report_status(rows)
    signal_count = _decimal_count(len(rows))
    reason_code_counts = _reason_code_counts(rows)
    return MarketResearchGoldVaultFlowDigestReport(
        generated_at=generated_at_utc,
        config_version=cfg.config_version,
        digest_status=report_status,
        recommended_next_step=NEXT_STEPS[report_status],
        signal_count=signal_count,
        ready_signal_count=_status_count(rows, STATUS_READY),
        watch_signal_count=_status_count(rows, STATUS_WATCH),
        blocked_signal_count=_status_count(rows, STATUS_BLOCKED),
        stale_vault_flow_signal_count=_reason_signal_count(
            rows,
            STALE_VAULT_FLOW_SIGNAL_REASON,
        ),
        thin_confirmation_signal_count=_reason_signal_count(
            rows,
            THIN_CONFIRMATION_REASON,
        ),
        low_flow_tonnage_signal_count=_reason_signal_count(
            rows,
            LOW_FLOW_TONNAGE_REASON,
        ),
        inventory_pressure_gap_signal_count=_reason_signal_count(
            rows,
            INVENTORY_PRESSURE_GAP_REASON,
        ),
        delivery_alignment_gap_signal_count=_reason_signal_count(
            rows,
            DELIVERY_ALIGNMENT_GAP_REASON,
        ),
        stale_source_signal_count=_reason_signal_count(
            rows,
            STALE_SOURCE_RATIO_REASON,
        ),
        total_confidence_decay=_decimal_sum(
            row.confidence_decay_factor for row in rows
        ),
        average_final_confidence=_ratio(
            _decimal_sum(row.final_confidence for row in rows),
            signal_count,
        ),
        average_flow_tonnage_abs=_ratio(
            _decimal_sum(row.flow_tonnage_abs for row in rows),
            signal_count,
        ),
        average_inventory_pressure_score=_ratio(
            _decimal_sum(row.inventory_pressure_score for row in rows),
            signal_count,
        ),
        average_delivery_alignment_score=_ratio(
            _decimal_sum(row.delivery_alignment_score for row in rows),
            signal_count,
        ),
        max_flow_age_seconds=cfg.max_flow_age_seconds,
        min_flow_tonnage_abs=cfg.min_flow_tonnage_abs,
        min_confirmation_source_count=cfg.min_confirmation_source_count,
        min_inventory_pressure_score=cfg.min_inventory_pressure_score,
        min_delivery_alignment_score=cfg.min_delivery_alignment_score,
        max_stale_source_ratio=cfg.max_stale_source_ratio,
        max_observed_signal_age_seconds=max(
            (row.signal_age_seconds for row in rows),
            default=ZERO,
        ),
        rows=rows,
        signal_config_versions=tuple(
            sorted(
                (
                    signal.vault_flow_key,
                    signal.signal_config_version,
                )
                for signal in normalized_signals
            ),
        ),
        reason_code_counts=reason_code_counts,
        reason_codes=tuple(item.reason_code for item in reason_code_counts),
    )


def market_research_gold_vault_flow_digest_payload(
    report: MarketResearchGoldVaultFlowDigestReport,
) -> dict[str, Any]:
    if type(report) is not MarketResearchGoldVaultFlowDigestReport:
        raise ValueError("report must be exactly MarketResearchGoldVaultFlowDigestReport")
    _require_hard_flags("report", report)
    value = _json_ready(asdict(report))
    if type(value) is not dict:
        raise ValueError("value must be a dict")
    return value


def _row_for_signal(
    signal: MarketResearchGoldVaultFlowDigestSignal,
    *,
    config: MarketResearchGoldVaultFlowDigestConfig,
    generated_at: datetime,
) -> MarketResearchGoldVaultFlowDigestRow:
    if signal.observed_at > generated_at:
        raise ValueError("observed_at must not be in the future")
    signal_age_seconds = _age_seconds(generated_at, signal.observed_at)
    reason_codes = _row_reason_codes(
        signal=signal,
        config=config,
        signal_age_seconds=signal_age_seconds,
    )
    confidence_decay_factor = _confidence_decay_factor(reason_codes, config=config)
    final_confidence = _final_confidence(signal.base_confidence, confidence_decay_factor)
    return MarketResearchGoldVaultFlowDigestRow(
        vault_flow_key=signal.vault_flow_key,
        condition_id=signal.condition_id,
        vault_venue=signal.vault_venue,
        flow_direction=signal.flow_direction,
        digest_status=_row_status(
            reason_codes,
            final_confidence=final_confidence,
            watch_confidence_threshold=config.watch_confidence_threshold,
        ),
        observed_at=signal.observed_at,
        signal_age_seconds=signal_age_seconds,
        flow_tonnage_abs=signal.flow_tonnage_abs,
        confirmation_source_count=signal.confirmation_source_count,
        inventory_pressure_score=signal.inventory_pressure_score,
        delivery_alignment_score=signal.delivery_alignment_score,
        stale_source_ratio=signal.stale_source_ratio,
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
    signal: MarketResearchGoldVaultFlowDigestSignal,
    config: MarketResearchGoldVaultFlowDigestConfig,
    signal_age_seconds: Decimal,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    if signal_age_seconds > config.max_flow_age_seconds:
        reason_codes.append(STALE_VAULT_FLOW_SIGNAL_REASON)
    if signal.confirmation_source_count < config.min_confirmation_source_count:
        reason_codes.append(THIN_CONFIRMATION_REASON)
    if signal.flow_tonnage_abs < config.min_flow_tonnage_abs:
        reason_codes.append(LOW_FLOW_TONNAGE_REASON)
    if signal.inventory_pressure_score < config.min_inventory_pressure_score:
        reason_codes.append(INVENTORY_PRESSURE_GAP_REASON)
    if signal.delivery_alignment_score < config.min_delivery_alignment_score:
        reason_codes.append(DELIVERY_ALIGNMENT_GAP_REASON)
    if signal.stale_source_ratio > config.max_stale_source_ratio:
        reason_codes.append(STALE_SOURCE_RATIO_REASON)
    if not reason_codes:
        return (READY_REASON,)
    return tuple(code for code in ROW_REASON_CODE_SEQUENCE if code in reason_codes)


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


def _report_status(rows: tuple[MarketResearchGoldVaultFlowDigestRow, ...]) -> str:
    if not rows:
        return STATUS_BLOCKED
    if any(row.digest_status == STATUS_BLOCKED for row in rows):
        return STATUS_BLOCKED
    if any(row.digest_status == STATUS_WATCH for row in rows):
        return STATUS_WATCH
    return STATUS_READY


def _row_sort_value(row: MarketResearchGoldVaultFlowDigestRow) -> Decimal:
    if row.digest_status == STATUS_BLOCKED:
        return ZERO
    if row.digest_status == STATUS_WATCH:
        return ONE
    return Decimal("2.000000")


def _status_count(
    rows: tuple[MarketResearchGoldVaultFlowDigestRow, ...],
    status: str,
) -> Decimal:
    return _decimal_count(sum(1 for row in rows if row.digest_status == status))


def _reason_signal_count(
    rows: tuple[MarketResearchGoldVaultFlowDigestRow, ...],
    reason_code: str,
) -> Decimal:
    return _decimal_count(sum(1 for row in rows if reason_code in row.reason_codes))


def _reason_code_counts(
    rows: tuple[MarketResearchGoldVaultFlowDigestRow, ...],
) -> tuple[MarketResearchGoldVaultFlowDigestReasonCodeCount, ...]:
    signal_count = _decimal_count(len(rows))
    if not rows:
        return (
            MarketResearchGoldVaultFlowDigestReasonCodeCount(
                reason_code=NO_INPUTS_REASON,
                count=ONE,
                signal_ratio=ZERO,
            ),
        )
    return tuple(
        MarketResearchGoldVaultFlowDigestReasonCodeCount(
            reason_code=reason_code,
            count=count,
            signal_ratio=_ratio(count, signal_count),
        )
        for reason_code in REASON_CODE_SEQUENCE
        if reason_code != NO_INPUTS_REASON
        if (count := _reason_signal_count(rows, reason_code)) > ZERO
    )


def _confidence_decay_factor(
    reason_codes: tuple[str, ...],
    *,
    config: MarketResearchGoldVaultFlowDigestConfig,
) -> Decimal:
    gap_count = sum(1 for reason_code in reason_codes if reason_code != READY_REASON)
    value = _quantize(config.confidence_decay_per_gap * _decimal_count(gap_count))
    if value > ONE:
        return ONE
    return value


def _final_confidence(base_confidence: Decimal, confidence_decay_factor: Decimal) -> Decimal:
    value = _quantize(base_confidence - confidence_decay_factor)
    if value < ZERO:
        return ZERO
    return _require_ratio_decimal("final_confidence", value)


def _normalize_signals(
    signals: Iterable[MarketResearchGoldVaultFlowDigestSignal],
) -> tuple[MarketResearchGoldVaultFlowDigestSignal, ...]:
    if isinstance(signals, (str, bytes)):
        raise ValueError("signals must be an iterable of digest signals")
    try:
        rows = tuple(signals)
    except TypeError as exc:
        raise ValueError("signals must be an iterable of digest signals") from exc
    seen: set[str] = set()
    for signal in rows:
        if type(signal) is not MarketResearchGoldVaultFlowDigestSignal:
            raise ValueError(
                "signals must contain MarketResearchGoldVaultFlowDigestSignal",
            )
        _require_hard_flags("signal", signal)
        if signal.vault_flow_key in seen:
            raise ValueError("signals must not contain duplicate vault_flow_key values")
        seen.add(signal.vault_flow_key)
    return rows


def _normalize_rows(
    value: object,
) -> tuple[MarketResearchGoldVaultFlowDigestRow, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("rows must be a list or tuple")
    rows = tuple(value)
    for row in rows:
        if type(row) is not MarketResearchGoldVaultFlowDigestRow:
            raise ValueError("rows must contain MarketResearchGoldVaultFlowDigestRow")
        _require_hard_flags("row", row)
    expected = tuple(
        sorted(
            rows,
            key=lambda row: (_row_sort_value(row), row.vault_flow_key, row.condition_id),
        ),
    )
    if rows != expected:
        raise ValueError("rows must use deterministic sort")
    if len({row.vault_flow_key for row in rows}) != len(rows):
        raise ValueError("rows must use unique vault_flow_key values")
    return rows


def _normalize_reason_code_counts(
    value: object,
) -> tuple[MarketResearchGoldVaultFlowDigestReasonCodeCount, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("reason_code_counts must be a list or tuple")
    rows = tuple(value)
    seen: set[str] = set()
    for row in rows:
        if type(row) is not MarketResearchGoldVaultFlowDigestReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "MarketResearchGoldVaultFlowDigestReasonCodeCount",
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


def _normalize_signal_config_versions(value: object) -> tuple[tuple[str, str], ...]:
    if type(value) not in (list, tuple):
        raise ValueError("signal_config_versions must be a list or tuple")
    rows = tuple(value)
    normalized: list[tuple[str, str]] = []
    for row in rows:
        if type(row) not in (list, tuple) or len(row) != 2:
            raise ValueError("signal_config_versions rows must be pairs")
        vault_flow_key, config_version = row
        _require_public_string("vault_flow_key", vault_flow_key)
        _require_public_string("signal_config_version", config_version)
        normalized.append((vault_flow_key, config_version))
    result = tuple(normalized)
    if result != tuple(sorted(result)):
        raise ValueError("signal_config_versions must use deterministic sort")
    if len({vault_flow_key for vault_flow_key, _ in result}) != len(result):
        raise ValueError("signal_config_versions must be unique")
    return result


def _normalize_reason_codes(
    value: object,
    *,
    sequence: tuple[str, ...],
) -> tuple[str, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("reason_codes must be a list or tuple")
    reason_codes = tuple(value)
    if not reason_codes:
        raise ValueError("reason_codes must not be empty")
    for reason_code in reason_codes:
        if reason_code not in sequence:
            raise ValueError("reason_code must be known")
    if len(set(reason_codes)) != len(reason_codes):
        raise ValueError("reason_codes must be unique")
    if tuple(code for code in sequence if code in reason_codes) != reason_codes:
        raise ValueError("reason_codes must use deterministic sort")
    return reason_codes


def _validate_row(row: MarketResearchGoldVaultFlowDigestRow) -> None:
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


def _validate_report(report: MarketResearchGoldVaultFlowDigestReport) -> None:
    if report.signal_count != _decimal_count(len(report.rows)):
        raise ValueError("signal_count must match rows")
    if report.ready_signal_count != _status_count(report.rows, STATUS_READY):
        raise ValueError("ready_signal_count must match rows")
    if report.watch_signal_count != _status_count(report.rows, STATUS_WATCH):
        raise ValueError("watch_signal_count must match rows")
    if report.blocked_signal_count != _status_count(report.rows, STATUS_BLOCKED):
        raise ValueError("blocked_signal_count must match rows")
    reason_checks = (
        ("stale_vault_flow_signal_count", STALE_VAULT_FLOW_SIGNAL_REASON),
        ("thin_confirmation_signal_count", THIN_CONFIRMATION_REASON),
        ("low_flow_tonnage_signal_count", LOW_FLOW_TONNAGE_REASON),
        ("inventory_pressure_gap_signal_count", INVENTORY_PRESSURE_GAP_REASON),
        ("delivery_alignment_gap_signal_count", DELIVERY_ALIGNMENT_GAP_REASON),
        ("stale_source_signal_count", STALE_SOURCE_RATIO_REASON),
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
    if report.average_flow_tonnage_abs != _ratio(
        _decimal_sum(row.flow_tonnage_abs for row in report.rows),
        report.signal_count,
    ):
        raise ValueError("average_flow_tonnage_abs must match rows")
    if report.average_inventory_pressure_score != _ratio(
        _decimal_sum(row.inventory_pressure_score for row in report.rows),
        report.signal_count,
    ):
        raise ValueError("average_inventory_pressure_score must match rows")
    if report.average_delivery_alignment_score != _ratio(
        _decimal_sum(row.delivery_alignment_score for row in report.rows),
        report.signal_count,
    ):
        raise ValueError("average_delivery_alignment_score must match rows")
    if report.max_observed_signal_age_seconds != max(
        (row.signal_age_seconds for row in report.rows),
        default=ZERO,
    ):
        raise ValueError("max_observed_signal_age_seconds must match rows")
    if report.signal_config_versions and len(report.signal_config_versions) != len(
        report.rows,
    ):
        raise ValueError("signal_config_versions must match rows")
    if report.reason_code_counts != _reason_code_counts(report.rows):
        raise ValueError("reason_code_counts must match rows")
    if report.reason_codes != tuple(item.reason_code for item in report.reason_code_counts):
        raise ValueError("reason_codes must match reason_code_counts")
    if report.digest_status != _report_status(report.rows):
        raise ValueError("digest_status must match rows")
    if report.recommended_next_step != NEXT_STEPS[report.digest_status]:
        raise ValueError("recommended_next_step must match digest_status")


def _quantize(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(QUANT)


def _decimal_count(value: int) -> Decimal:
    return _quantize(Decimal(value))


def _decimal_sum(values: Iterable[Decimal]) -> Decimal:
    total = ZERO
    for value in values:
        total = _quantize(total + value)
    return total


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return _quantize(numerator / denominator)


def _age_seconds(generated_at: datetime, observed_at: datetime) -> Decimal:
    delta = generated_at - observed_at
    return _quantize(
        Decimal(delta.days) * Decimal("86400")
        + Decimal(delta.seconds)
        + Decimal(delta.microseconds) / MICROSECONDS_PER_SECOND,
    )


def _redacted_reference(value: str) -> str:
    if not _reference_needs_redaction(value):
        return value
    return "sha256:" + sha256(value.encode("utf-8")).hexdigest()[:12]


def _reference_needs_redaction(value: str) -> bool:
    lowered = value.lower()
    if "://" in lowered:
        return True
    return any(fragment in lowered for fragment in UNSAFE_TEXT_FRAGMENTS)


def _json_ready(value: Any) -> Any:
    if value is None:
        return None
    if type(value) is Decimal:
        if not value.is_finite():
            raise ValueError("JSON Decimal value must be finite")
        return format(value, "f")
    if type(value) is datetime:
        return _as_utc("datetime", value).isoformat()
    if type(value) in (str, bool):
        return value
    if type(value) is int or type(value) is float:
        raise ValueError("JSON value must not be a public numeric primitive")
    if isinstance(value, dict):
        ready: dict[str, Any] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON keys must be strings")
            ready[key] = _json_ready(item)
        return ready
    if isinstance(value, (list, tuple)):
        return [_json_ready(item) for item in value]
    raise ValueError("value is not JSON serializable")


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone aware")
    return value.astimezone(UTC)


def _require_positive_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_nonnegative_decimal(field_name, value)
    if normalized <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _require_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    if value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return _quantize(value)


def _require_positive_count_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_nonnegative_count_decimal(field_name, value)
    if normalized <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _require_nonnegative_count_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_nonnegative_decimal(field_name, value)
    if normalized != normalized.to_integral_value().quantize(QUANT):
        raise ValueError(f"{field_name} must be integral")
    return normalized


def _require_ratio_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    if value < ZERO or value > ONE:
        raise ValueError(f"{field_name} must be in the inclusive 0 to 1 range")
    return _quantize(value)


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")


def _require_public_string(field_name: str, value: object) -> None:
    _require_canonical_string(field_name, value)
    assert type(value) is str
    lowered = value.lower()
    if any(fragment in lowered for fragment in UNSAFE_TEXT_FRAGMENTS):
        raise ValueError(f"{field_name} must not include unsafe text")
    if any(char not in PUBLIC_LABEL_CHARS for char in lowered):
        raise ValueError(f"{field_name} must be identifier-like")


def _require_flow_direction(field_name: str, value: object) -> None:
    if type(value) is not str or value not in ("inflow", "outflow"):
        raise ValueError(f"{field_name} must be inflow or outflow")


def _require_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in DIGEST_STATUSES:
        raise ValueError(f"{field_name} must be a valid digest status")


def _require_reason_code(field_name: str, value: object) -> None:
    if type(value) is not str or value not in REASON_CODE_SEQUENCE:
        raise ValueError(f"{field_name} must be a known reason code")


def _require_redacted_reference(field_name: str, value: object) -> str:
    _require_canonical_string(field_name, value)
    assert type(value) is str
    if _reference_needs_redaction(value) and not value.startswith("sha256:"):
        raise ValueError(f"{field_name} must be redacted")
    return value


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if getattr(value, field_name) is not True:
            raise ValueError(f"{field_name} must be True for {label}")
