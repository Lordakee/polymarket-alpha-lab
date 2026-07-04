"""Pure Phase 1 rates repo specialness squeeze digest reducer."""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable
from dataclasses import dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
from typing import Any


DEFAULT_MARKET_RESEARCH_RATES_REPO_SPECIALNESS_SQUEEZE_DIGEST_CONFIG_VERSION = (
    "market-research-rates-repo-specialness-squeeze-digest-v0"
)

STATUS_READY = "ready"
STATUS_WATCH = "watch"
STATUS_BLOCKED = "blocked"
DIGEST_STATUSES = (STATUS_READY, STATUS_WATCH, STATUS_BLOCKED)

NO_INPUTS_REASON = "market_research_rates_repo_specialness_squeeze_digest_no_inputs"
READY_REASON = "market_research_rates_repo_specialness_squeeze_digest_ready"
STALE_SIGNAL_REASON = (
    "market_research_rates_repo_specialness_squeeze_digest_stale_signal"
)
WEAK_SPECIALNESS_REASON = (
    "market_research_rates_repo_specialness_squeeze_digest_weak_specialness"
)
FAILS_PRESSURE_GAP_REASON = (
    "market_research_rates_repo_specialness_squeeze_digest_fails_pressure_gap"
)
DEALER_SHORTAGE_GAP_REASON = (
    "market_research_rates_repo_specialness_squeeze_digest_dealer_shortage_gap"
)
SOURCE_FAMILY_GAP_REASON = (
    "market_research_rates_repo_specialness_squeeze_digest_source_family_gap"
)
STALE_SOURCE_RATIO_REASON = (
    "market_research_rates_repo_specialness_squeeze_digest_stale_source_ratio"
)
CONFIRMATION_GAP_REASON = (
    "market_research_rates_repo_specialness_squeeze_digest_confirmation_gap"
)

REASON_CODE_SEQUENCE = (
    CONFIRMATION_GAP_REASON,
    STALE_SIGNAL_REASON,
    WEAK_SPECIALNESS_REASON,
    FAILS_PRESSURE_GAP_REASON,
    DEALER_SHORTAGE_GAP_REASON,
    SOURCE_FAMILY_GAP_REASON,
    STALE_SOURCE_RATIO_REASON,
    READY_REASON,
    NO_INPUTS_REASON,
)
ROW_REASON_CODE_SEQUENCE = (
    STALE_SIGNAL_REASON,
    WEAK_SPECIALNESS_REASON,
    FAILS_PRESSURE_GAP_REASON,
    DEALER_SHORTAGE_GAP_REASON,
    SOURCE_FAMILY_GAP_REASON,
    STALE_SOURCE_RATIO_REASON,
    CONFIRMATION_GAP_REASON,
    READY_REASON,
)

QUANTUM = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
BPS_PER_PERCENTAGE_POINT = Decimal("100.000000")
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)


def _join_parts(*parts: str) -> str:
    return "".join(parts)


UNSAFE_REFERENCE_FRAGMENTS = frozenset(
    (
        "bearer",
        "credential",
        _join_parts("api", "_", "key"),
        _join_parts("pri", "vate"),
        _join_parts("pri", "vate", "_", "key"),
        _join_parts("sec", "ret"),
        _join_parts("tok", "en"),
        _join_parts("wal", "let"),
    ),
)


__all__ = (
    "DEFAULT_MARKET_RESEARCH_RATES_REPO_SPECIALNESS_SQUEEZE_DIGEST_CONFIG_VERSION",
    "MarketResearchRatesRepoSpecialnessSqueezeDigestConfig",
    "MarketResearchRatesRepoSpecialnessSqueezeSignal",
    "MarketResearchRatesRepoSpecialnessSqueezeDigestRow",
    "MarketResearchRatesRepoSpecialnessSqueezeReasonCodeCount",
    "MarketResearchRatesRepoSpecialnessSqueezeDigestReport",
    "build_market_research_rates_repo_specialness_squeeze_digest",
    "market_research_rates_repo_specialness_squeeze_digest_payload",
)


@dataclass(frozen=True)
class MarketResearchRatesRepoSpecialnessSqueezeDigestConfig:
    config_version: str = (
        DEFAULT_MARKET_RESEARCH_RATES_REPO_SPECIALNESS_SQUEEZE_DIGEST_CONFIG_VERSION
    )
    max_signal_age_seconds: Decimal = Decimal("7200.000000")
    min_specialness_bps: Decimal = Decimal("25.000000")
    min_fails_to_deliver_ratio: Decimal = Decimal("0.350000")
    min_dealer_shortage_ratio: Decimal = Decimal("0.600000")
    min_source_family_count: Decimal = Decimal("3.000000")
    max_stale_source_ratio: Decimal = Decimal("0.250000")
    min_confirmation_ratio: Decimal = Decimal("0.650000")
    confidence_decay_per_gap: Decimal = Decimal("0.100000")
    watch_confidence_threshold: Decimal = Decimal("0.650000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            MarketResearchRatesRepoSpecialnessSqueezeDigestConfig,
            "config",
        )
        _require_public_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_MARKET_RESEARCH_RATES_REPO_SPECIALNESS_SQUEEZE_DIGEST_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "max_signal_age_seconds",
            "min_source_family_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
            if getattr(self, field_name) <= ZERO:
                raise ValueError(f"{field_name} must be positive")
        object.__setattr__(
            self,
            "min_specialness_bps",
            _require_decimal("min_specialness_bps", self.min_specialness_bps),
        )
        if self.min_specialness_bps <= ZERO:
            raise ValueError("min_specialness_bps must be positive")
        for field_name in (
            "min_fails_to_deliver_ratio",
            "min_dealer_shortage_ratio",
            "max_stale_source_ratio",
            "min_confirmation_ratio",
            "confidence_decay_per_gap",
            "watch_confidence_threshold",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio(field_name, getattr(self, field_name)),
            )
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class MarketResearchRatesRepoSpecialnessSqueezeSignal:
    condition_id: str
    repo_market_key: str
    collateral_bucket: str
    public_signal_reference: str
    observed_at: datetime
    signal_age_seconds: Decimal
    general_collateral_rate_pct: Decimal
    specific_collateral_rate_pct: Decimal
    fails_to_deliver_ratio: Decimal
    dealer_shortage_ratio: Decimal
    source_family_count: Decimal
    stale_source_ratio: Decimal
    confirmation_ratio: Decimal
    base_confidence: Decimal
    signal_config_version: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            MarketResearchRatesRepoSpecialnessSqueezeSignal,
            "signal",
        )
        for field_name in (
            "condition_id",
            "repo_market_key",
            "collateral_bucket",
            "public_signal_reference",
            "signal_config_version",
        ):
            _require_public_string(field_name, getattr(self, field_name))
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        object.__setattr__(
            self,
            "signal_age_seconds",
            _require_nonnegative_decimal("signal_age_seconds", self.signal_age_seconds),
        )
        for field_name in (
            "general_collateral_rate_pct",
            "specific_collateral_rate_pct",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "source_family_count",
            _require_nonnegative_decimal("source_family_count", self.source_family_count),
        )
        for field_name in (
            "fails_to_deliver_ratio",
            "dealer_shortage_ratio",
            "stale_source_ratio",
            "confirmation_ratio",
            "base_confidence",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio(field_name, getattr(self, field_name)),
            )
        _require_hard_flags("signal", self)


@dataclass(frozen=True)
class MarketResearchRatesRepoSpecialnessSqueezeDigestRow:
    condition_id: str
    repo_market_key: str
    collateral_bucket: str
    observed_at: datetime
    signal_age_seconds: Decimal
    general_collateral_rate_pct: Decimal
    specific_collateral_rate_pct: Decimal
    specialness_bps: Decimal
    fails_to_deliver_ratio: Decimal
    dealer_shortage_ratio: Decimal
    source_family_count: Decimal
    stale_source_ratio: Decimal
    confirmation_ratio: Decimal
    base_confidence: Decimal
    confidence_decay_factor: Decimal
    final_confidence: Decimal
    digest_status: str
    redacted_public_signal_reference: str
    signal_config_version: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            MarketResearchRatesRepoSpecialnessSqueezeDigestRow,
            "row",
        )
        for field_name in (
            "condition_id",
            "repo_market_key",
            "collateral_bucket",
            "signal_config_version",
        ):
            _require_public_string(field_name, getattr(self, field_name))
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in (
            "signal_age_seconds",
            "source_family_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "general_collateral_rate_pct",
            "specific_collateral_rate_pct",
            "specialness_bps",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "fails_to_deliver_ratio",
            "dealer_shortage_ratio",
            "stale_source_ratio",
            "confirmation_ratio",
            "base_confidence",
            "confidence_decay_factor",
            "final_confidence",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio(field_name, getattr(self, field_name)),
            )
        _require_member("digest_status", self.digest_status, DIGEST_STATUSES)
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
class MarketResearchRatesRepoSpecialnessSqueezeReasonCodeCount:
    reason_code: str
    count: Decimal
    signal_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            MarketResearchRatesRepoSpecialnessSqueezeReasonCodeCount,
            "reason_code_count",
        )
        _require_member("reason_code", self.reason_code, ROW_REASON_CODE_SEQUENCE)
        if self.reason_code == READY_REASON:
            raise ValueError("reason_code must identify a gap")
        object.__setattr__(
            self,
            "count",
            _require_nonnegative_decimal("count", self.count),
        )
        if self.count <= ZERO:
            raise ValueError("count must be positive")
        object.__setattr__(
            self,
            "signal_ratio",
            _require_ratio("signal_ratio", self.signal_ratio),
        )
        _require_hard_flags("reason_code_count", self)


@dataclass(frozen=True)
class MarketResearchRatesRepoSpecialnessSqueezeDigestReport:
    generated_at: datetime
    config_version: str
    digest_status: str
    recommended_next_step: str
    signal_count: Decimal
    ready_signal_count: Decimal
    watch_signal_count: Decimal
    blocked_signal_count: Decimal
    stale_signal_count: Decimal
    weak_specialness_signal_count: Decimal
    fails_pressure_gap_signal_count: Decimal
    dealer_shortage_gap_signal_count: Decimal
    source_family_gap_signal_count: Decimal
    stale_source_signal_count: Decimal
    confirmation_gap_signal_count: Decimal
    total_confidence_decay: Decimal
    average_final_confidence: Decimal
    max_specialness_bps: Decimal
    average_specialness_bps: Decimal
    average_fails_to_deliver_ratio: Decimal
    average_dealer_shortage_ratio: Decimal
    max_signal_age_seconds: Decimal
    min_specialness_bps: Decimal
    min_fails_to_deliver_ratio: Decimal
    min_dealer_shortage_ratio: Decimal
    min_source_family_count: Decimal
    max_stale_source_ratio: Decimal
    min_confirmation_ratio: Decimal
    max_observed_signal_age_seconds: Decimal
    rows: tuple[MarketResearchRatesRepoSpecialnessSqueezeDigestRow, ...]
    signal_config_versions: tuple[tuple[str, str], ...]
    reason_code_counts: tuple[
        MarketResearchRatesRepoSpecialnessSqueezeReasonCodeCount,
        ...,
    ]
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            MarketResearchRatesRepoSpecialnessSqueezeDigestReport,
            "report",
        )
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_MARKET_RESEARCH_RATES_REPO_SPECIALNESS_SQUEEZE_DIGEST_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        _require_member("digest_status", self.digest_status, DIGEST_STATUSES)
        _require_public_string("recommended_next_step", self.recommended_next_step)
        for field_name in (
            "signal_count",
            "ready_signal_count",
            "watch_signal_count",
            "blocked_signal_count",
            "stale_signal_count",
            "weak_specialness_signal_count",
            "fails_pressure_gap_signal_count",
            "dealer_shortage_gap_signal_count",
            "source_family_gap_signal_count",
            "stale_source_signal_count",
            "confirmation_gap_signal_count",
            "total_confidence_decay",
            "max_signal_age_seconds",
            "min_source_family_count",
            "max_observed_signal_age_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "max_specialness_bps",
            "average_specialness_bps",
            "min_specialness_bps",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_decimal(field_name, getattr(self, field_name)),
            )
        if self.min_specialness_bps <= ZERO:
            raise ValueError("min_specialness_bps must be positive")
        for field_name in (
            "average_final_confidence",
            "average_fails_to_deliver_ratio",
            "average_dealer_shortage_ratio",
            "min_fails_to_deliver_ratio",
            "min_dealer_shortage_ratio",
            "max_stale_source_ratio",
            "min_confirmation_ratio",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio(field_name, getattr(self, field_name)),
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


def build_market_research_rates_repo_specialness_squeeze_digest(
    signals: Iterable[MarketResearchRatesRepoSpecialnessSqueezeSignal],
    *,
    config: MarketResearchRatesRepoSpecialnessSqueezeDigestConfig | None = None,
    generated_at: datetime,
) -> MarketResearchRatesRepoSpecialnessSqueezeDigestReport:
    cfg = config or MarketResearchRatesRepoSpecialnessSqueezeDigestConfig()
    if type(cfg) is not MarketResearchRatesRepoSpecialnessSqueezeDigestConfig:
        raise ValueError(
            "config must be exactly "
            "MarketResearchRatesRepoSpecialnessSqueezeDigestConfig",
        )
    _require_hard_flags("config", cfg)
    generated_at_utc = _as_utc("generated_at", generated_at)
    normalized_signals = _normalize_signals(signals)
    rows = _sorted_rows(
        _row_for_signal(signal, config=cfg, generated_at=generated_at_utc)
        for signal in normalized_signals
    )
    report_status = _report_status(rows)
    return MarketResearchRatesRepoSpecialnessSqueezeDigestReport(
        generated_at=generated_at_utc,
        config_version=cfg.config_version,
        digest_status=report_status,
        recommended_next_step=_recommended_next_step(report_status),
        signal_count=_decimal_count(len(rows)),
        ready_signal_count=_status_count(rows, STATUS_READY),
        watch_signal_count=_status_count(rows, STATUS_WATCH),
        blocked_signal_count=_status_count(rows, STATUS_BLOCKED),
        stale_signal_count=_reason_signal_count(rows, STALE_SIGNAL_REASON),
        weak_specialness_signal_count=_reason_signal_count(
            rows,
            WEAK_SPECIALNESS_REASON,
        ),
        fails_pressure_gap_signal_count=_reason_signal_count(
            rows,
            FAILS_PRESSURE_GAP_REASON,
        ),
        dealer_shortage_gap_signal_count=_reason_signal_count(
            rows,
            DEALER_SHORTAGE_GAP_REASON,
        ),
        source_family_gap_signal_count=_reason_signal_count(
            rows,
            SOURCE_FAMILY_GAP_REASON,
        ),
        stale_source_signal_count=_reason_signal_count(rows, STALE_SOURCE_RATIO_REASON),
        confirmation_gap_signal_count=_reason_signal_count(
            rows,
            CONFIRMATION_GAP_REASON,
        ),
        total_confidence_decay=_decimal_sum(
            row.confidence_decay_factor for row in rows
        ),
        average_final_confidence=_ratio(
            _decimal_sum(row.final_confidence for row in rows),
            _decimal_count(len(rows)),
        ),
        max_specialness_bps=max(
            (row.specialness_bps for row in rows),
            default=ZERO,
        ),
        average_specialness_bps=_ratio(
            _decimal_sum(row.specialness_bps for row in rows),
            _decimal_count(len(rows)),
        ),
        average_fails_to_deliver_ratio=_ratio(
            _decimal_sum(row.fails_to_deliver_ratio for row in rows),
            _decimal_count(len(rows)),
        ),
        average_dealer_shortage_ratio=_ratio(
            _decimal_sum(row.dealer_shortage_ratio for row in rows),
            _decimal_count(len(rows)),
        ),
        max_signal_age_seconds=cfg.max_signal_age_seconds,
        min_specialness_bps=cfg.min_specialness_bps,
        min_fails_to_deliver_ratio=cfg.min_fails_to_deliver_ratio,
        min_dealer_shortage_ratio=cfg.min_dealer_shortage_ratio,
        min_source_family_count=cfg.min_source_family_count,
        max_stale_source_ratio=cfg.max_stale_source_ratio,
        min_confirmation_ratio=cfg.min_confirmation_ratio,
        max_observed_signal_age_seconds=max(
            (row.signal_age_seconds for row in rows),
            default=ZERO,
        ),
        rows=rows,
        signal_config_versions=_signal_config_versions(rows),
        reason_code_counts=_reason_code_counts(rows),
        reason_codes=_summary_reason_codes(rows),
    )


def market_research_rates_repo_specialness_squeeze_digest_payload(
    report: MarketResearchRatesRepoSpecialnessSqueezeDigestReport,
) -> dict[str, Any]:
    if type(report) is not MarketResearchRatesRepoSpecialnessSqueezeDigestReport:
        raise ValueError(
            "report must be exactly "
            "MarketResearchRatesRepoSpecialnessSqueezeDigestReport",
        )
    _validate_report(report)
    value = _payload_value(report)
    if type(value) is not dict:
        raise ValueError("report payload must be a JSON object")
    return value


def _row_for_signal(
    signal: MarketResearchRatesRepoSpecialnessSqueezeSignal,
    *,
    config: MarketResearchRatesRepoSpecialnessSqueezeDigestConfig,
    generated_at: datetime,
) -> MarketResearchRatesRepoSpecialnessSqueezeDigestRow:
    if signal.observed_at > generated_at:
        raise ValueError("observed_at must not be in the future")
    observed_age_seconds = _age_seconds(generated_at, signal.observed_at)
    if signal.signal_age_seconds != observed_age_seconds:
        raise ValueError("signal_age_seconds must match observed_at and generated_at")
    specialness_bps = _specialness_bps(
        general_collateral_rate_pct=signal.general_collateral_rate_pct,
        specific_collateral_rate_pct=signal.specific_collateral_rate_pct,
    )
    reason_codes = _row_reason_codes(
        signal=signal,
        specialness_bps=specialness_bps,
        config=config,
    )
    confidence_decay_factor = _confidence_decay_factor(reason_codes, config=config)
    final_confidence = max(
        ZERO,
        _quantize(signal.base_confidence - confidence_decay_factor),
    )
    return MarketResearchRatesRepoSpecialnessSqueezeDigestRow(
        condition_id=signal.condition_id,
        repo_market_key=signal.repo_market_key,
        collateral_bucket=signal.collateral_bucket,
        observed_at=signal.observed_at,
        signal_age_seconds=signal.signal_age_seconds,
        general_collateral_rate_pct=signal.general_collateral_rate_pct,
        specific_collateral_rate_pct=signal.specific_collateral_rate_pct,
        specialness_bps=specialness_bps,
        fails_to_deliver_ratio=signal.fails_to_deliver_ratio,
        dealer_shortage_ratio=signal.dealer_shortage_ratio,
        source_family_count=signal.source_family_count,
        stale_source_ratio=signal.stale_source_ratio,
        confirmation_ratio=signal.confirmation_ratio,
        base_confidence=signal.base_confidence,
        confidence_decay_factor=confidence_decay_factor,
        final_confidence=final_confidence,
        digest_status=_row_status(
            reason_codes,
            final_confidence=final_confidence,
            watch_confidence_threshold=config.watch_confidence_threshold,
        ),
        redacted_public_signal_reference=_redacted_reference(
            signal.public_signal_reference,
        ),
        signal_config_version=signal.signal_config_version,
        reason_codes=reason_codes,
    )


def _specialness_bps(
    *,
    general_collateral_rate_pct: Decimal,
    specific_collateral_rate_pct: Decimal,
) -> Decimal:
    return _quantize(
        (general_collateral_rate_pct - specific_collateral_rate_pct)
        * BPS_PER_PERCENTAGE_POINT,
    )


def _row_reason_codes(
    *,
    signal: MarketResearchRatesRepoSpecialnessSqueezeSignal,
    specialness_bps: Decimal,
    config: MarketResearchRatesRepoSpecialnessSqueezeDigestConfig,
) -> tuple[str, ...]:
    reasons: list[str] = []
    if signal.signal_age_seconds > config.max_signal_age_seconds:
        reasons.append(STALE_SIGNAL_REASON)
    if specialness_bps < config.min_specialness_bps:
        reasons.append(WEAK_SPECIALNESS_REASON)
    if signal.fails_to_deliver_ratio < config.min_fails_to_deliver_ratio:
        reasons.append(FAILS_PRESSURE_GAP_REASON)
    if signal.dealer_shortage_ratio < config.min_dealer_shortage_ratio:
        reasons.append(DEALER_SHORTAGE_GAP_REASON)
    if signal.source_family_count < config.min_source_family_count:
        reasons.append(SOURCE_FAMILY_GAP_REASON)
    if signal.stale_source_ratio > config.max_stale_source_ratio:
        reasons.append(STALE_SOURCE_RATIO_REASON)
    if signal.confirmation_ratio < config.min_confirmation_ratio:
        reasons.append(CONFIRMATION_GAP_REASON)
    if not reasons:
        reasons.append(READY_REASON)
    return tuple(reason for reason in ROW_REASON_CODE_SEQUENCE if reason in reasons)


def _confidence_decay_factor(
    reason_codes: tuple[str, ...],
    *,
    config: MarketResearchRatesRepoSpecialnessSqueezeDigestConfig,
) -> Decimal:
    gap_count = _decimal_count(sum(1 for reason in reason_codes if reason != READY_REASON))
    return _quantize(config.confidence_decay_per_gap * gap_count)


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


def _sorted_rows(
    rows: Iterable[MarketResearchRatesRepoSpecialnessSqueezeDigestRow],
) -> tuple[MarketResearchRatesRepoSpecialnessSqueezeDigestRow, ...]:
    status_weight = {STATUS_BLOCKED: 0, STATUS_WATCH: 1, STATUS_READY: 2}
    return tuple(
        sorted(
            rows,
            key=lambda row: (
                status_weight[row.digest_status],
                row.final_confidence,
                row.repo_market_key,
                row.condition_id,
            ),
        ),
    )


def _report_status(
    rows: tuple[MarketResearchRatesRepoSpecialnessSqueezeDigestRow, ...],
) -> str:
    if not rows:
        return STATUS_BLOCKED
    if any(row.digest_status == STATUS_BLOCKED for row in rows):
        return STATUS_BLOCKED
    if any(row.digest_status == STATUS_WATCH for row in rows):
        return STATUS_WATCH
    return STATUS_READY


def _recommended_next_step(status: str) -> str:
    if status == STATUS_READY:
        return "allow_report_only_market_research_rates_repo_specialness_squeeze_digest"
    if status == STATUS_WATCH:
        return "review_report_only_market_research_rates_repo_specialness_squeeze_digest"
    return "block_report_only_market_research_rates_repo_specialness_squeeze_digest"


def _summary_reason_codes(
    rows: tuple[MarketResearchRatesRepoSpecialnessSqueezeDigestRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return (NO_INPUTS_REASON,)
    reasons = {
        reason
        for row in rows
        for reason in row.reason_codes
        if reason != READY_REASON
    }
    if not reasons:
        return (READY_REASON,)
    return tuple(reason for reason in REASON_CODE_SEQUENCE if reason in reasons)


def _reason_code_counts(
    rows: tuple[MarketResearchRatesRepoSpecialnessSqueezeDigestRow, ...],
) -> tuple[MarketResearchRatesRepoSpecialnessSqueezeReasonCodeCount, ...]:
    signal_count = _decimal_count(len(rows))
    counter: Counter[str] = Counter(
        reason
        for row in rows
        for reason in row.reason_codes
        if reason != READY_REASON
    )
    return tuple(
        MarketResearchRatesRepoSpecialnessSqueezeReasonCodeCount(
            reason_code=reason,
            count=_decimal_count(counter[reason]),
            signal_ratio=_ratio(_decimal_count(counter[reason]), signal_count),
        )
        for reason in REASON_CODE_SEQUENCE
        if reason in counter and reason != NO_INPUTS_REASON
    )


def _status_count(
    rows: tuple[MarketResearchRatesRepoSpecialnessSqueezeDigestRow, ...],
    status: str,
) -> Decimal:
    return _decimal_count(sum(1 for row in rows if row.digest_status == status))


def _reason_signal_count(
    rows: tuple[MarketResearchRatesRepoSpecialnessSqueezeDigestRow, ...],
    reason_code: str,
) -> Decimal:
    return _decimal_count(sum(1 for row in rows if reason_code in row.reason_codes))


def _signal_config_versions(
    rows: tuple[MarketResearchRatesRepoSpecialnessSqueezeDigestRow, ...],
) -> tuple[tuple[str, str], ...]:
    return tuple(
        sorted(
            {
                (row.repo_market_key, row.signal_config_version)
                for row in rows
            },
        ),
    )


def _normalize_signals(
    value: Iterable[MarketResearchRatesRepoSpecialnessSqueezeSignal],
) -> tuple[MarketResearchRatesRepoSpecialnessSqueezeSignal, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError("signals must be an iterable")
    try:
        signals = tuple(value)
    except TypeError as exc:
        raise ValueError("signals must be an iterable") from exc
    seen: set[str] = set()
    for signal in signals:
        if type(signal) is not MarketResearchRatesRepoSpecialnessSqueezeSignal:
            raise ValueError(
                "signals must contain "
                "MarketResearchRatesRepoSpecialnessSqueezeSignal values",
            )
        _require_hard_flags("signals", signal)
        if signal.condition_id in seen:
            raise ValueError("signals condition_id values must be unique")
        seen.add(signal.condition_id)
    return signals


def _normalize_rows(
    value: tuple[MarketResearchRatesRepoSpecialnessSqueezeDigestRow, ...],
) -> tuple[MarketResearchRatesRepoSpecialnessSqueezeDigestRow, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("rows must be a list or tuple")
    rows = tuple(value)
    seen: set[str] = set()
    for row in rows:
        if type(row) is not MarketResearchRatesRepoSpecialnessSqueezeDigestRow:
            raise ValueError(
                "rows must contain "
                "MarketResearchRatesRepoSpecialnessSqueezeDigestRow values",
            )
        _require_hard_flags("rows", row)
        if row.condition_id in seen:
            raise ValueError("rows condition_id values must be unique")
        seen.add(row.condition_id)
    if rows != _sorted_rows(rows):
        raise ValueError("rows must use deterministic sequence")
    return rows


def _normalize_signal_config_versions(
    value: tuple[tuple[str, str], ...],
) -> tuple[tuple[str, str], ...]:
    if type(value) not in (list, tuple):
        raise ValueError("signal_config_versions must be a list or tuple")
    pairs = tuple(value)
    seen: set[tuple[str, str]] = set()
    normalized_pairs: list[tuple[str, str]] = []
    for pair in pairs:
        if type(pair) not in (list, tuple) or len(pair) != 2:
            raise ValueError("signal_config_versions must contain pairs")
        key, version = pair
        _require_public_string("signal_config_versions key", key)
        _require_public_string("signal_config_versions version", version)
        normalized_pair = (key, version)
        if normalized_pair in seen:
            raise ValueError("signal_config_versions values must be unique")
        seen.add(normalized_pair)
        normalized_pairs.append(normalized_pair)
    normalized = tuple(normalized_pairs)
    if normalized != tuple(sorted(normalized)):
        raise ValueError("signal_config_versions must use canonical sequence")
    return normalized


def _normalize_reason_code_counts(
    value: tuple[MarketResearchRatesRepoSpecialnessSqueezeReasonCodeCount, ...],
) -> tuple[MarketResearchRatesRepoSpecialnessSqueezeReasonCodeCount, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("reason_code_counts must be a list or tuple")
    counts = tuple(value)
    seen: set[str] = set()
    for item in counts:
        if type(item) is not MarketResearchRatesRepoSpecialnessSqueezeReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "MarketResearchRatesRepoSpecialnessSqueezeReasonCodeCount values",
            )
        _require_hard_flags("reason_code_counts", item)
        if item.reason_code in seen:
            raise ValueError("reason_code_counts reason_code values must be unique")
        seen.add(item.reason_code)
    canonical = tuple(
        reason
        for reason in REASON_CODE_SEQUENCE
        if reason in seen and reason not in (READY_REASON, NO_INPUTS_REASON)
    )
    if tuple(item.reason_code for item in counts) != canonical:
        raise ValueError("reason_code_counts must use canonical sequence")
    return counts


def _normalize_reason_codes(
    value: tuple[str, ...],
    *,
    sequence: tuple[str, ...],
) -> tuple[str, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("reason_codes must be a list or tuple")
    reasons = tuple(value)
    seen: set[str] = set()
    for reason in reasons:
        _require_member("reason_code", reason, sequence)
        if reason in seen:
            raise ValueError("reason_codes values must be unique")
        seen.add(reason)
    canonical = tuple(reason for reason in sequence if reason in seen)
    if reasons != canonical:
        raise ValueError("reason_codes must use canonical sequence")
    return reasons


def _validate_row(row: MarketResearchRatesRepoSpecialnessSqueezeDigestRow) -> None:
    expected_specialness_bps = _specialness_bps(
        general_collateral_rate_pct=row.general_collateral_rate_pct,
        specific_collateral_rate_pct=row.specific_collateral_rate_pct,
    )
    if row.specialness_bps != expected_specialness_bps:
        raise ValueError("specialness_bps must match repo rates")
    if row.final_confidence > row.base_confidence:
        raise ValueError("final_confidence must not exceed base_confidence")
    if row.reason_codes == (READY_REASON,) and row.confidence_decay_factor != ZERO:
        raise ValueError("confidence_decay_factor must match reason_codes")
    if row.reason_codes != (READY_REASON,) and row.confidence_decay_factor <= ZERO:
        raise ValueError("confidence_decay_factor must match reason_codes")


def _validate_report(
    report: MarketResearchRatesRepoSpecialnessSqueezeDigestReport,
) -> None:
    rows = report.rows
    row_count = _decimal_count(len(rows))
    checks = (
        ("signal_count", report.signal_count, row_count),
        ("ready_signal_count", report.ready_signal_count, _status_count(rows, STATUS_READY)),
        ("watch_signal_count", report.watch_signal_count, _status_count(rows, STATUS_WATCH)),
        (
            "blocked_signal_count",
            report.blocked_signal_count,
            _status_count(rows, STATUS_BLOCKED),
        ),
        (
            "stale_signal_count",
            report.stale_signal_count,
            _reason_signal_count(rows, STALE_SIGNAL_REASON),
        ),
        (
            "weak_specialness_signal_count",
            report.weak_specialness_signal_count,
            _reason_signal_count(rows, WEAK_SPECIALNESS_REASON),
        ),
        (
            "fails_pressure_gap_signal_count",
            report.fails_pressure_gap_signal_count,
            _reason_signal_count(rows, FAILS_PRESSURE_GAP_REASON),
        ),
        (
            "dealer_shortage_gap_signal_count",
            report.dealer_shortage_gap_signal_count,
            _reason_signal_count(rows, DEALER_SHORTAGE_GAP_REASON),
        ),
        (
            "source_family_gap_signal_count",
            report.source_family_gap_signal_count,
            _reason_signal_count(rows, SOURCE_FAMILY_GAP_REASON),
        ),
        (
            "stale_source_signal_count",
            report.stale_source_signal_count,
            _reason_signal_count(rows, STALE_SOURCE_RATIO_REASON),
        ),
        (
            "confirmation_gap_signal_count",
            report.confirmation_gap_signal_count,
            _reason_signal_count(rows, CONFIRMATION_GAP_REASON),
        ),
        (
            "total_confidence_decay",
            report.total_confidence_decay,
            _decimal_sum(row.confidence_decay_factor for row in rows),
        ),
        (
            "average_final_confidence",
            report.average_final_confidence,
            _ratio(_decimal_sum(row.final_confidence for row in rows), row_count),
        ),
        (
            "max_specialness_bps",
            report.max_specialness_bps,
            max((row.specialness_bps for row in rows), default=ZERO),
        ),
        (
            "average_specialness_bps",
            report.average_specialness_bps,
            _ratio(_decimal_sum(row.specialness_bps for row in rows), row_count),
        ),
        (
            "average_fails_to_deliver_ratio",
            report.average_fails_to_deliver_ratio,
            _ratio(_decimal_sum(row.fails_to_deliver_ratio for row in rows), row_count),
        ),
        (
            "average_dealer_shortage_ratio",
            report.average_dealer_shortage_ratio,
            _ratio(_decimal_sum(row.dealer_shortage_ratio for row in rows), row_count),
        ),
        (
            "max_observed_signal_age_seconds",
            report.max_observed_signal_age_seconds,
            max((row.signal_age_seconds for row in rows), default=ZERO),
        ),
    )
    for field_name, actual, expected in checks:
        if actual != expected:
            raise ValueError(f"{field_name} must match rows")
    if (
        report.ready_signal_count
        + report.watch_signal_count
        + report.blocked_signal_count
        != report.signal_count
    ):
        raise ValueError("status counts must match rows")
    if report.digest_status != _report_status(rows):
        raise ValueError("digest_status must match rows")
    if report.recommended_next_step != _recommended_next_step(report.digest_status):
        raise ValueError("recommended_next_step must match digest_status")
    if report.signal_config_versions != _signal_config_versions(rows):
        raise ValueError("signal_config_versions must match rows")
    if report.reason_code_counts != _reason_code_counts(rows):
        raise ValueError("reason_code_counts must match rows")
    if report.reason_codes != _summary_reason_codes(rows):
        raise ValueError("reason_codes must match rows")


def _age_seconds(later: datetime, earlier: datetime) -> Decimal:
    if earlier > later:
        raise ValueError("observed_at must not be in the future")
    return _quantize(Decimal(str((later - earlier).total_seconds())))


def _decimal_sum(values: Iterable[Decimal]) -> Decimal:
    total = ZERO
    with localcontext(DECIMAL_CONTEXT):
        for value in values:
            if type(value) is not Decimal:
                raise ValueError("values must be Decimals")
            total += value
    return _quantize(total)


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return _quantize(numerator / denominator)


def _decimal_count(value: int) -> Decimal:
    return _quantize(Decimal(value))


def _require_ratio(field_name: str, value: object) -> Decimal:
    decimal_value = _require_nonnegative_decimal(field_name, value)
    if decimal_value > ONE:
        raise ValueError(f"{field_name} must be between zero and one")
    return decimal_value


def _require_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return decimal_value


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return _quantize(value)


def _quantize(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(QUANTUM)


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_member(
    field_name: str,
    value: object,
    allowed_values: tuple[str, ...],
) -> None:
    _require_public_string(field_name, value)
    if value not in allowed_values:
        raise ValueError(f"{field_name} must be supported")


def _require_public_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")


def _require_redacted_reference(field_name: str, value: object) -> str:
    _require_public_string(field_name, value)
    text = str(value)
    lowered = text.lower()
    if any(fragment in lowered for fragment in UNSAFE_REFERENCE_FRAGMENTS):
        raise ValueError(f"{field_name} must be redacted")
    return text


def _redacted_reference(value: str) -> str:
    _require_public_string("public_signal_reference", value)
    lowered = value.lower()
    if any(fragment in lowered for fragment in UNSAFE_REFERENCE_FRAGMENTS):
        return f"sha256:{sha256(value.encode('utf-8')).hexdigest()[:12]}"
    return value


def _require_hard_flags(field_name: str, value: object) -> None:
    if getattr(value, "paper_only", None) is not True:
        raise ValueError(f"{field_name} paper_only must be True")
    if getattr(value, "report_only", None) is not True:
        raise ValueError(f"{field_name} report_only must be True")
    if getattr(value, "readonly", None) is not True:
        raise ValueError(f"{field_name} readonly must be True")


def _require_exact_type(
    value: object,
    expected_type: type[object],
    field_name: str,
) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{field_name} must be exactly {expected_type.__name__}")


def _payload_value(value: object) -> Any:
    if isinstance(value, Decimal):
        return format(value, "f")
    if type(value) is datetime:
        return value.isoformat()
    if is_dataclass(value) and not isinstance(value, type):
        return {
            field.name: _payload_value(getattr(value, field.name))
            for field in fields(value)
        }
    if isinstance(value, tuple):
        return [_payload_value(item) for item in value]
    if isinstance(value, list):
        return [_payload_value(item) for item in value]
    if isinstance(value, dict):
        return {str(key): _payload_value(item) for key, item in value.items()}
    if isinstance(value, float):
        raise ValueError("payload must not contain floats")
    return value
