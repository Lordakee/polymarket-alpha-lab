"""Pure Phase 1 energy power price negative spike digest reducer."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from typing import Any


DEFAULT_MARKET_RESEARCH_ENERGY_POWER_PRICE_NEGATIVE_SPIKE_DIGEST_CONFIG_VERSION = (
    "market-research-energy-power-price-negative-spike-digest-v0"
)

STATUS_READY = "ready"
STATUS_WATCH = "watch"
STATUS_BLOCKED = "blocked"
STATUSES = (STATUS_READY, STATUS_WATCH, STATUS_BLOCKED)

REASON_PREFIX = "market_research_energy_power_price_negative_spike_digest_"
NEGATIVE_PRICE_SPIKE_REASON = f"{REASON_PREFIX}negative_price_spike"
SHARP_PRICE_DROP_REASON = f"{REASON_PREFIX}sharp_price_drop"
HIGH_RENEWABLE_SHARE_REASON = f"{REASON_PREFIX}high_renewable_share"
SOURCE_DIVERSITY_GAP_REASON = f"{REASON_PREFIX}source_diversity_gap"
STALE_OBSERVATION_REASON = f"{REASON_PREFIX}stale_observation"
CONFIDENCE_GAP_REASON = f"{REASON_PREFIX}confidence_gap"
READY_REASON = f"{REASON_PREFIX}ready"
NO_INPUTS_REASON = f"{REASON_PREFIX}no_inputs"

ROW_REASON_CODE_SEQUENCE = (
    NEGATIVE_PRICE_SPIKE_REASON,
    SHARP_PRICE_DROP_REASON,
    HIGH_RENEWABLE_SHARE_REASON,
    SOURCE_DIVERSITY_GAP_REASON,
    STALE_OBSERVATION_REASON,
    CONFIDENCE_GAP_REASON,
    READY_REASON,
)
REPORT_REASON_CODE_SEQUENCE = (*ROW_REASON_CODE_SEQUENCE, NO_INPUTS_REASON)

DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
QUANT = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
SECONDS_PER_DAY = Decimal("86400.000000")
MICROSECONDS_PER_SECOND = Decimal("1000000.000000")


__all__ = (
    "DEFAULT_MARKET_RESEARCH_ENERGY_POWER_PRICE_NEGATIVE_SPIKE_DIGEST_CONFIG_VERSION",
    "MarketResearchEnergyPowerPriceNegativeSpikeDigestConfig",
    "MarketResearchEnergyPowerPriceNegativeSpikeDigestObservation",
    "MarketResearchEnergyPowerPriceNegativeSpikeDigestReasonCodeCount",
    "MarketResearchEnergyPowerPriceNegativeSpikeDigestReport",
    "MarketResearchEnergyPowerPriceNegativeSpikeDigestRow",
    "build_market_research_energy_power_price_negative_spike_digest",
    "market_research_energy_power_price_negative_spike_digest_payload",
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
class MarketResearchEnergyPowerPriceNegativeSpikeDigestConfig(_FinalPublicDataclass):
    config_version: str = (
        DEFAULT_MARKET_RESEARCH_ENERGY_POWER_PRICE_NEGATIVE_SPIKE_DIGEST_CONFIG_VERSION
    )
    max_observation_age_seconds: Decimal = Decimal("1800.000000")
    min_source_count: Decimal = Decimal("3.000000")
    watch_negative_price_mwh: Decimal = Decimal("10.000000")
    blocked_negative_price_mwh: Decimal = Decimal("50.000000")
    sharp_price_drop_mwh: Decimal = Decimal("35.000000")
    high_renewable_share: Decimal = Decimal("0.700000")
    min_confidence: Decimal = Decimal("0.700000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            MarketResearchEnergyPowerPriceNegativeSpikeDigestConfig,
            "config",
        )
        _require_canonical_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_MARKET_RESEARCH_ENERGY_POWER_PRICE_NEGATIVE_SPIKE_DIGEST_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in ("max_observation_age_seconds", "min_source_count"):
            object.__setattr__(
                self,
                field_name,
                _require_positive_count_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "watch_negative_price_mwh",
            "blocked_negative_price_mwh",
            "sharp_price_drop_mwh",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in ("high_renewable_share", "min_confidence"):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        if self.watch_negative_price_mwh > self.blocked_negative_price_mwh:
            raise ValueError(
                "watch_negative_price_mwh must not exceed blocked_negative_price_mwh",
            )
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class MarketResearchEnergyPowerPriceNegativeSpikeDigestObservation(_FinalPublicDataclass):
    condition_id: str
    spike_id: str
    grid_region: str
    observed_at: datetime
    source_count: Decimal
    settlement_price_mwh: Decimal
    prior_price_mwh: Decimal
    day_ahead_price_mwh: Decimal
    renewable_share: Decimal
    load_mw: Decimal
    confidence: Decimal
    source_config_version: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            MarketResearchEnergyPowerPriceNegativeSpikeDigestObservation,
            "observation",
        )
        for field_name in (
            "condition_id",
            "spike_id",
            "grid_region",
            "source_config_version",
        ):
            _require_canonical_string(field_name, getattr(self, field_name))
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        object.__setattr__(
            self,
            "source_count",
            _require_nonnegative_count_decimal("source_count", self.source_count),
        )
        for field_name in (
            "settlement_price_mwh",
            "prior_price_mwh",
            "day_ahead_price_mwh",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_decimal_measure(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "renewable_share",
            _require_ratio_decimal("renewable_share", self.renewable_share),
        )
        object.__setattr__(
            self,
            "load_mw",
            _require_nonnegative_decimal("load_mw", self.load_mw),
        )
        object.__setattr__(
            self,
            "confidence",
            _require_ratio_decimal("confidence", self.confidence),
        )
        _require_hard_flags("observation", self)


@dataclass(frozen=True)
class MarketResearchEnergyPowerPriceNegativeSpikeDigestRow(_FinalPublicDataclass):
    condition_id: str
    spike_id: str
    grid_region: str
    spike_status: str
    observed_at: datetime
    observation_age_seconds: Decimal
    source_count: Decimal
    settlement_price_mwh: Decimal
    prior_price_mwh: Decimal
    day_ahead_price_mwh: Decimal
    negative_price_abs: Decimal
    blocked_negative_price_mwh: Decimal
    price_drop_mwh: Decimal
    renewable_share: Decimal
    load_mw: Decimal
    confidence: Decimal
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            MarketResearchEnergyPowerPriceNegativeSpikeDigestRow,
            "row",
        )
        for field_name in ("condition_id", "spike_id", "grid_region"):
            _require_canonical_string(field_name, getattr(self, field_name))
        _require_status("spike_status", self.spike_status)
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in ("observation_age_seconds", "source_count"):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_count_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "settlement_price_mwh",
            "prior_price_mwh",
            "day_ahead_price_mwh",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_decimal_measure(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "negative_price_abs",
            "blocked_negative_price_mwh",
            "price_drop_mwh",
            "load_mw",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in ("renewable_share", "confidence"):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "reason_codes",
            _require_canonical_reason_codes(
                "reason_codes",
                self.reason_codes,
                ROW_REASON_CODE_SEQUENCE,
            ),
        )
        _validate_row(self)
        _require_hard_flags("row", self)


@dataclass(frozen=True)
class MarketResearchEnergyPowerPriceNegativeSpikeDigestReasonCodeCount(
    _FinalPublicDataclass,
):
    reason_code: str
    count: Decimal
    observation_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            MarketResearchEnergyPowerPriceNegativeSpikeDigestReasonCodeCount,
            "reason_code_count",
        )
        _require_reason_code("reason_code", self.reason_code)
        object.__setattr__(
            self,
            "count",
            _require_positive_count_decimal("count", self.count),
        )
        object.__setattr__(
            self,
            "observation_ratio",
            _require_ratio_decimal("observation_ratio", self.observation_ratio),
        )
        _require_hard_flags("reason_code_count", self)


@dataclass(frozen=True)
class MarketResearchEnergyPowerPriceNegativeSpikeDigestReport(_FinalPublicDataclass):
    generated_at: datetime
    config_version: str
    digest_status: str
    recommended_next_step: str
    observation_count: Decimal
    ready_observation_count: Decimal
    watch_observation_count: Decimal
    blocked_observation_count: Decimal
    negative_spike_count: Decimal
    sharp_price_drop_count: Decimal
    high_renewable_share_count: Decimal
    source_diversity_gap_count: Decimal
    stale_observation_count: Decimal
    confidence_gap_count: Decimal
    average_settlement_price_mwh: Decimal
    average_price_drop_mwh: Decimal
    max_negative_price_abs: Decimal
    max_price_drop_mwh: Decimal
    max_observation_age_seconds: Decimal
    min_source_count: Decimal
    watch_negative_price_mwh: Decimal
    blocked_negative_price_mwh: Decimal
    sharp_price_drop_mwh: Decimal
    high_renewable_share: Decimal
    min_confidence: Decimal
    rows: tuple[MarketResearchEnergyPowerPriceNegativeSpikeDigestRow, ...]
    source_config_versions: tuple[tuple[str, str, str], ...]
    reason_code_counts: tuple[
        MarketResearchEnergyPowerPriceNegativeSpikeDigestReasonCodeCount,
        ...,
    ]
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            MarketResearchEnergyPowerPriceNegativeSpikeDigestReport,
            "report",
        )
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_MARKET_RESEARCH_ENERGY_POWER_PRICE_NEGATIVE_SPIKE_DIGEST_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        _require_status("digest_status", self.digest_status)
        _require_canonical_string("recommended_next_step", self.recommended_next_step)
        for field_name in (
            "observation_count",
            "ready_observation_count",
            "watch_observation_count",
            "blocked_observation_count",
            "negative_spike_count",
            "sharp_price_drop_count",
            "high_renewable_share_count",
            "source_diversity_gap_count",
            "stale_observation_count",
            "confidence_gap_count",
            "max_observation_age_seconds",
            "min_source_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_count_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "average_settlement_price_mwh",
            "average_price_drop_mwh",
            "max_negative_price_abs",
            "max_price_drop_mwh",
            "watch_negative_price_mwh",
            "blocked_negative_price_mwh",
            "sharp_price_drop_mwh",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name))
                if field_name != "average_settlement_price_mwh"
                else _require_decimal_measure(field_name, getattr(self, field_name)),
            )
        for field_name in ("high_renewable_share", "min_confidence"):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(self, "rows", _require_canonical_rows(self.rows))
        object.__setattr__(
            self,
            "source_config_versions",
            _require_source_config_versions(self.source_config_versions),
        )
        object.__setattr__(
            self,
            "reason_code_counts",
            _require_canonical_reason_code_counts(self.reason_code_counts),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _require_canonical_reason_codes(
                "reason_codes",
                self.reason_codes,
                REPORT_REASON_CODE_SEQUENCE,
            ),
        )
        _validate_report(self)
        _require_hard_flags("report", self)


_PUBLIC_DATACLASS_TYPES = (
    MarketResearchEnergyPowerPriceNegativeSpikeDigestConfig,
    MarketResearchEnergyPowerPriceNegativeSpikeDigestObservation,
    MarketResearchEnergyPowerPriceNegativeSpikeDigestRow,
    MarketResearchEnergyPowerPriceNegativeSpikeDigestReasonCodeCount,
    MarketResearchEnergyPowerPriceNegativeSpikeDigestReport,
)


def build_market_research_energy_power_price_negative_spike_digest(
    observations: Iterable[MarketResearchEnergyPowerPriceNegativeSpikeDigestObservation],
    *,
    config: MarketResearchEnergyPowerPriceNegativeSpikeDigestConfig | None = None,
    generated_at: datetime,
) -> MarketResearchEnergyPowerPriceNegativeSpikeDigestReport:
    cfg = config or MarketResearchEnergyPowerPriceNegativeSpikeDigestConfig()
    if type(cfg) is not MarketResearchEnergyPowerPriceNegativeSpikeDigestConfig:
        raise ValueError(
            "config must be exactly "
            "MarketResearchEnergyPowerPriceNegativeSpikeDigestConfig",
        )
    _require_hard_flags("config", cfg)
    generated_at_utc = _as_utc("generated_at", generated_at)
    normalized_observations = _normalize_observations(observations)
    rows = tuple(
        sorted(
            (
                _row_for_observation(
                    observation,
                    config=cfg,
                    generated_at=generated_at_utc,
                )
                for observation in normalized_observations
            ),
            key=_row_sort_key,
        ),
    )
    report_status = _report_status(rows)
    return MarketResearchEnergyPowerPriceNegativeSpikeDigestReport(
        generated_at=generated_at_utc,
        config_version=cfg.config_version,
        digest_status=report_status,
        recommended_next_step=_recommended_next_step(report_status, rows),
        observation_count=_count_decimal(len(rows)),
        ready_observation_count=_status_count(rows, STATUS_READY),
        watch_observation_count=_status_count(rows, STATUS_WATCH),
        blocked_observation_count=_status_count(rows, STATUS_BLOCKED),
        negative_spike_count=_reason_row_count(rows, NEGATIVE_PRICE_SPIKE_REASON),
        sharp_price_drop_count=_reason_row_count(rows, SHARP_PRICE_DROP_REASON),
        high_renewable_share_count=_reason_row_count(rows, HIGH_RENEWABLE_SHARE_REASON),
        source_diversity_gap_count=_reason_row_count(rows, SOURCE_DIVERSITY_GAP_REASON),
        stale_observation_count=_reason_row_count(rows, STALE_OBSERVATION_REASON),
        confidence_gap_count=_reason_row_count(rows, CONFIDENCE_GAP_REASON),
        average_settlement_price_mwh=_average(row.settlement_price_mwh for row in rows),
        average_price_drop_mwh=_average(row.price_drop_mwh for row in rows),
        max_negative_price_abs=max((row.negative_price_abs for row in rows), default=ZERO),
        max_price_drop_mwh=max((row.price_drop_mwh for row in rows), default=ZERO),
        max_observation_age_seconds=cfg.max_observation_age_seconds,
        min_source_count=cfg.min_source_count,
        watch_negative_price_mwh=cfg.watch_negative_price_mwh,
        blocked_negative_price_mwh=cfg.blocked_negative_price_mwh,
        sharp_price_drop_mwh=cfg.sharp_price_drop_mwh,
        high_renewable_share=cfg.high_renewable_share,
        min_confidence=cfg.min_confidence,
        rows=rows,
        source_config_versions=tuple(
            sorted(
                (
                    observation.spike_id,
                    observation.condition_id,
                    observation.source_config_version,
                )
                for observation in normalized_observations
            ),
        ),
        reason_code_counts=_reason_code_counts(rows),
        reason_codes=_summary_reason_codes(rows),
    )


def market_research_energy_power_price_negative_spike_digest_payload(
    report: MarketResearchEnergyPowerPriceNegativeSpikeDigestReport,
) -> dict[str, Any]:
    if type(report) is not MarketResearchEnergyPowerPriceNegativeSpikeDigestReport:
        raise ValueError(
            "report must be exactly MarketResearchEnergyPowerPriceNegativeSpikeDigestReport",
        )
    _require_payload_safe_value("report", report)
    return _payload_value(report)


def _row_for_observation(
    observation: MarketResearchEnergyPowerPriceNegativeSpikeDigestObservation,
    *,
    config: MarketResearchEnergyPowerPriceNegativeSpikeDigestConfig,
    generated_at: datetime,
) -> MarketResearchEnergyPowerPriceNegativeSpikeDigestRow:
    if observation.observed_at > generated_at:
        raise ValueError("observed_at must not be in the future")
    observation_age_seconds = _age_seconds(generated_at, observation.observed_at)
    negative_price_abs = _negative_price_abs(observation.settlement_price_mwh)
    price_drop_mwh = _nonnegative_delta(
        observation.prior_price_mwh,
        observation.settlement_price_mwh,
    )
    reason_codes = _row_reason_codes(
        observation=observation,
        config=config,
        observation_age_seconds=observation_age_seconds,
        negative_price_abs=negative_price_abs,
        price_drop_mwh=price_drop_mwh,
    )
    return MarketResearchEnergyPowerPriceNegativeSpikeDigestRow(
        condition_id=observation.condition_id,
        spike_id=observation.spike_id,
        grid_region=observation.grid_region,
        spike_status=_row_status(
            reason_codes,
            negative_price_abs=negative_price_abs,
            config=config,
        ),
        observed_at=observation.observed_at,
        observation_age_seconds=observation_age_seconds,
        source_count=observation.source_count,
        settlement_price_mwh=observation.settlement_price_mwh,
        prior_price_mwh=observation.prior_price_mwh,
        day_ahead_price_mwh=observation.day_ahead_price_mwh,
        negative_price_abs=negative_price_abs,
        blocked_negative_price_mwh=config.blocked_negative_price_mwh,
        price_drop_mwh=price_drop_mwh,
        renewable_share=observation.renewable_share,
        load_mw=observation.load_mw,
        confidence=observation.confidence,
        reason_codes=reason_codes,
    )


def _row_reason_codes(
    *,
    observation: MarketResearchEnergyPowerPriceNegativeSpikeDigestObservation,
    config: MarketResearchEnergyPowerPriceNegativeSpikeDigestConfig,
    observation_age_seconds: Decimal,
    negative_price_abs: Decimal,
    price_drop_mwh: Decimal,
) -> tuple[str, ...]:
    reasons: list[str] = []
    if negative_price_abs >= config.watch_negative_price_mwh:
        reasons.append(NEGATIVE_PRICE_SPIKE_REASON)
    if price_drop_mwh >= config.sharp_price_drop_mwh:
        reasons.append(SHARP_PRICE_DROP_REASON)
    if observation.renewable_share >= config.high_renewable_share:
        reasons.append(HIGH_RENEWABLE_SHARE_REASON)
    if observation.source_count < config.min_source_count:
        reasons.append(SOURCE_DIVERSITY_GAP_REASON)
    if observation_age_seconds > config.max_observation_age_seconds:
        reasons.append(STALE_OBSERVATION_REASON)
    if observation.confidence < config.min_confidence:
        reasons.append(CONFIDENCE_GAP_REASON)
    if not reasons:
        reasons.append(READY_REASON)
    return tuple(reason for reason in ROW_REASON_CODE_SEQUENCE if reason in reasons)


def _row_status(
    reason_codes: tuple[str, ...],
    *,
    negative_price_abs: Decimal,
    config: MarketResearchEnergyPowerPriceNegativeSpikeDigestConfig,
) -> str:
    if reason_codes == (READY_REASON,):
        return STATUS_READY
    if negative_price_abs >= config.blocked_negative_price_mwh:
        return STATUS_BLOCKED
    if any(
        reason in reason_codes
        for reason in (
            SHARP_PRICE_DROP_REASON,
            STALE_OBSERVATION_REASON,
            CONFIDENCE_GAP_REASON,
        )
    ):
        return STATUS_BLOCKED
    return STATUS_WATCH


def _row_status_from_row(
    row: MarketResearchEnergyPowerPriceNegativeSpikeDigestRow,
) -> str:
    if row.reason_codes == (READY_REASON,):
        return STATUS_READY
    if row.negative_price_abs >= row.blocked_negative_price_mwh:
        return STATUS_BLOCKED
    if any(
        reason in row.reason_codes
        for reason in (
            SHARP_PRICE_DROP_REASON,
            STALE_OBSERVATION_REASON,
            CONFIDENCE_GAP_REASON,
        )
    ):
        return STATUS_BLOCKED
    return row.spike_status


def _row_sort_key(
    row: MarketResearchEnergyPowerPriceNegativeSpikeDigestRow,
) -> tuple[int, Decimal, Decimal, Decimal, str, str]:
    status_rank = {
        STATUS_BLOCKED: 0,
        STATUS_WATCH: 1,
        STATUS_READY: 2,
    }[row.spike_status]
    severity = _count_decimal(
        len(tuple(reason for reason in row.reason_codes if reason != READY_REASON)),
    )
    return (
        status_rank,
        -severity,
        -row.negative_price_abs,
        -row.price_drop_mwh,
        row.spike_id,
        row.condition_id,
    )


def _report_status(
    rows: tuple[MarketResearchEnergyPowerPriceNegativeSpikeDigestRow, ...],
) -> str:
    if not rows:
        return STATUS_BLOCKED
    if any(row.spike_status == STATUS_BLOCKED for row in rows):
        return STATUS_BLOCKED
    if any(row.spike_status == STATUS_WATCH for row in rows):
        return STATUS_WATCH
    return STATUS_READY


def _recommended_next_step(
    status: str,
    rows: tuple[MarketResearchEnergyPowerPriceNegativeSpikeDigestRow, ...],
) -> str:
    if not rows:
        return "hold_report_only_market_research_energy_power_price_negative_spike_digest"
    if status == STATUS_BLOCKED:
        return "block_report_only_market_research_energy_power_price_negative_spike_digest"
    if status == STATUS_WATCH:
        return "review_report_only_market_research_energy_power_price_negative_spike_digest"
    return "allow_report_only_market_research_energy_power_price_negative_spike_digest"


def _status_count(
    rows: tuple[MarketResearchEnergyPowerPriceNegativeSpikeDigestRow, ...],
    status: str,
) -> Decimal:
    return _count_decimal(sum(1 for row in rows if row.spike_status == status))


def _reason_row_count(
    rows: tuple[MarketResearchEnergyPowerPriceNegativeSpikeDigestRow, ...],
    reason_code: str,
) -> Decimal:
    return _count_decimal(sum(1 for row in rows if reason_code in row.reason_codes))


def _reason_code_counts(
    rows: tuple[MarketResearchEnergyPowerPriceNegativeSpikeDigestRow, ...],
) -> tuple[MarketResearchEnergyPowerPriceNegativeSpikeDigestReasonCodeCount, ...]:
    if not rows:
        return ()
    observation_count = _count_decimal(len(rows))
    counts: dict[str, int] = {}
    for row in rows:
        for reason_code in row.reason_codes:
            counts[reason_code] = counts.get(reason_code, 0) + 1
    return tuple(
        MarketResearchEnergyPowerPriceNegativeSpikeDigestReasonCodeCount(
            reason_code=reason_code,
            count=_count_decimal(counts[reason_code]),
            observation_ratio=_ratio(
                _count_decimal(counts[reason_code]),
                observation_count,
            ),
        )
        for reason_code in REPORT_REASON_CODE_SEQUENCE
        if reason_code in counts
    )


def _summary_reason_codes(
    rows: tuple[MarketResearchEnergyPowerPriceNegativeSpikeDigestRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return (NO_INPUTS_REASON,)
    seen: set[str] = set()
    for row in rows:
        seen.update(row.reason_codes)
    if len(seen) > 1 and READY_REASON in seen:
        seen.remove(READY_REASON)
    return tuple(reason for reason in REPORT_REASON_CODE_SEQUENCE if reason in seen)


def _validate_row(row: MarketResearchEnergyPowerPriceNegativeSpikeDigestRow) -> None:
    if row.negative_price_abs != _negative_price_abs(row.settlement_price_mwh):
        raise ValueError("negative_price_abs must match settlement_price_mwh")
    if row.price_drop_mwh != _nonnegative_delta(
        row.prior_price_mwh,
        row.settlement_price_mwh,
    ):
        raise ValueError("price_drop_mwh must match price inputs")
    if row.reason_codes == (READY_REASON,) and row.spike_status != STATUS_READY:
        raise ValueError("spike_status must match reason_codes")
    if row.reason_codes != (READY_REASON,) and row.spike_status == STATUS_READY:
        raise ValueError("spike_status must match reason_codes")
    if _row_status_from_row(row) == STATUS_BLOCKED and row.spike_status != STATUS_BLOCKED:
        raise ValueError("spike_status must match reason_codes")


def _validate_report(report: MarketResearchEnergyPowerPriceNegativeSpikeDigestReport) -> None:
    if report.observation_count != _count_decimal(len(report.rows)):
        raise ValueError("observation_count must match rows")
    if report.ready_observation_count != _status_count(report.rows, STATUS_READY):
        raise ValueError("ready_observation_count must match rows")
    if report.watch_observation_count != _status_count(report.rows, STATUS_WATCH):
        raise ValueError("watch_observation_count must match rows")
    if report.blocked_observation_count != _status_count(report.rows, STATUS_BLOCKED):
        raise ValueError("blocked_observation_count must match rows")
    expected_counts = (
        (NEGATIVE_PRICE_SPIKE_REASON, report.negative_spike_count),
        (SHARP_PRICE_DROP_REASON, report.sharp_price_drop_count),
        (HIGH_RENEWABLE_SHARE_REASON, report.high_renewable_share_count),
        (SOURCE_DIVERSITY_GAP_REASON, report.source_diversity_gap_count),
        (STALE_OBSERVATION_REASON, report.stale_observation_count),
        (CONFIDENCE_GAP_REASON, report.confidence_gap_count),
    )
    for reason_code, expected_count in expected_counts:
        if expected_count != _reason_row_count(report.rows, reason_code):
            raise ValueError(f"{reason_code} count must match rows")
    if report.average_settlement_price_mwh != _average(
        row.settlement_price_mwh for row in report.rows
    ):
        raise ValueError("average_settlement_price_mwh must match rows")
    if report.average_price_drop_mwh != _average(row.price_drop_mwh for row in report.rows):
        raise ValueError("average_price_drop_mwh must match rows")
    if report.max_negative_price_abs != max(
        (row.negative_price_abs for row in report.rows),
        default=ZERO,
    ):
        raise ValueError("max_negative_price_abs must match rows")
    if report.max_price_drop_mwh != max(
        (row.price_drop_mwh for row in report.rows),
        default=ZERO,
    ):
        raise ValueError("max_price_drop_mwh must match rows")
    if report.digest_status != _report_status(report.rows):
        raise ValueError("digest_status must match rows")
    if report.recommended_next_step != _recommended_next_step(
        report.digest_status,
        report.rows,
    ):
        raise ValueError("recommended_next_step must match rows")
    if report.reason_code_counts != _reason_code_counts(report.rows):
        raise ValueError("reason_code_counts must match rows")
    if report.reason_codes != _summary_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")


def _normalize_observations(
    value: Iterable[MarketResearchEnergyPowerPriceNegativeSpikeDigestObservation],
) -> tuple[MarketResearchEnergyPowerPriceNegativeSpikeDigestObservation, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError("observations must be an iterable")
    try:
        observations = tuple(value)
    except TypeError as exc:
        raise ValueError("observations must be an iterable") from exc
    for observation in observations:
        if type(observation) is not MarketResearchEnergyPowerPriceNegativeSpikeDigestObservation:
            raise ValueError(
                "observations must contain "
                "MarketResearchEnergyPowerPriceNegativeSpikeDigestObservation values",
            )
        _require_hard_flags("observations", observation)
    return observations


def _require_canonical_rows(
    value: tuple[MarketResearchEnergyPowerPriceNegativeSpikeDigestRow, ...],
) -> tuple[MarketResearchEnergyPowerPriceNegativeSpikeDigestRow, ...]:
    if type(value) is not tuple:
        raise ValueError("rows must be a tuple")
    seen: set[tuple[str, str]] = set()
    for row in value:
        if type(row) is not MarketResearchEnergyPowerPriceNegativeSpikeDigestRow:
            raise ValueError(
                "rows must contain MarketResearchEnergyPowerPriceNegativeSpikeDigestRow values",
            )
        _require_hard_flags("rows", row)
        key = (row.condition_id, row.spike_id)
        if key in seen:
            raise ValueError("rows identifiers must be unique")
        seen.add(key)
    if value != tuple(sorted(value, key=_row_sort_key)):
        raise ValueError("rows must use deterministic sequence")
    return value


def _require_source_config_versions(
    value: tuple[tuple[str, str, str], ...],
) -> tuple[tuple[str, str, str], ...]:
    if type(value) is not tuple:
        raise ValueError("source_config_versions must be a tuple")
    seen: set[str] = set()
    for item in value:
        if type(item) is not tuple or len(item) != 3:
            raise ValueError("source_config_versions must contain tuple triples")
        spike_id, condition_id, source_config_version = item
        source_key = f"{condition_id}::{spike_id}"
        _require_canonical_string("source_config_versions spike_id", spike_id)
        _require_canonical_string("source_config_versions condition_id", condition_id)
        _require_canonical_string(
            "source_config_versions source_config_version",
            source_config_version,
        )
        if source_key in seen:
            raise ValueError("source_config_versions source keys must be unique")
        seen.add(source_key)
    if value != tuple(sorted(value)):
        raise ValueError("source_config_versions must use canonical sequence")
    return value


def _require_canonical_reason_code_counts(
    value: tuple[
        MarketResearchEnergyPowerPriceNegativeSpikeDigestReasonCodeCount,
        ...,
    ],
) -> tuple[MarketResearchEnergyPowerPriceNegativeSpikeDigestReasonCodeCount, ...]:
    if type(value) is not tuple:
        raise ValueError("reason_code_counts must be a tuple")
    seen: set[str] = set()
    for count in value:
        if type(count) is not MarketResearchEnergyPowerPriceNegativeSpikeDigestReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "MarketResearchEnergyPowerPriceNegativeSpikeDigestReasonCodeCount values",
            )
        _require_hard_flags("reason_code_counts", count)
        if count.reason_code in seen:
            raise ValueError("reason_code_counts reason_code values must be unique")
        seen.add(count.reason_code)
    expected_sequence = tuple(reason for reason in REPORT_REASON_CODE_SEQUENCE if reason in seen)
    if tuple(count.reason_code for count in value) != expected_sequence:
        raise ValueError("reason_code_counts must use canonical sequence")
    return value


def _require_canonical_reason_codes(
    field_name: str,
    value: tuple[str, ...],
    allowed_sequence: tuple[str, ...],
) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ValueError(f"{field_name} must be a tuple")
    if not value:
        raise ValueError(f"{field_name} must not be empty")
    seen: set[str] = set()
    for reason_code in value:
        _require_canonical_string(field_name, reason_code)
        if reason_code not in allowed_sequence:
            raise ValueError(f"{field_name} must contain known reason codes")
        if reason_code in seen:
            raise ValueError(f"{field_name} must be unique")
        seen.add(reason_code)
    expected_sequence = tuple(reason for reason in allowed_sequence if reason in seen)
    if value != expected_sequence:
        raise ValueError(f"{field_name} must use canonical sequence")
    return value


def _require_reason_code(field_name: str, value: object) -> None:
    _require_canonical_string(field_name, value)
    if value not in REPORT_REASON_CODE_SEQUENCE:
        raise ValueError(f"{field_name} must contain known reason codes")


def _require_status(field_name: str, value: object) -> None:
    _require_canonical_string(field_name, value)
    if value not in STATUSES:
        raise ValueError(f"{field_name} must be ready, watch, or blocked")


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return value


def _require_decimal_measure(field_name: str, value: object) -> Decimal:
    return _quantize_decimal(_require_decimal(field_name, value))


def _require_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal_measure(field_name, value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _require_ratio_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal_measure(field_name, value)
    if normalized < ZERO or normalized > ONE:
        raise ValueError(f"{field_name} must be between zero and one")
    return normalized


def _require_nonnegative_count_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_nonnegative_decimal(field_name, value)
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{field_name} must be integral")
    return normalized


def _require_positive_count_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_nonnegative_count_decimal(field_name, value)
    if normalized <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _count_decimal(value: int) -> Decimal:
    return _quantize_decimal(Decimal(value))


def _quantize_decimal(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(QUANT)


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO:
        return ZERO
    return _quantize_decimal(numerator / denominator)


def _average(values: Iterable[Decimal]) -> Decimal:
    normalized_values = tuple(values)
    if not normalized_values:
        return ZERO
    return _quantize_decimal(
        sum(normalized_values, ZERO) / _count_decimal(len(normalized_values)),
    )


def _negative_price_abs(value: Decimal) -> Decimal:
    if value >= ZERO:
        return ZERO
    return _quantize_decimal(-value)


def _nonnegative_delta(start_value: Decimal, end_value: Decimal) -> Decimal:
    delta = _quantize_decimal(start_value - end_value)
    if delta < ZERO:
        return ZERO
    return delta


def _age_seconds(generated_at: datetime, observed_at: datetime) -> Decimal:
    delta = generated_at - observed_at
    return _quantize_decimal(
        Decimal(delta.days) * SECONDS_PER_DAY
        + Decimal(delta.seconds)
        + (Decimal(delta.microseconds) / MICROSECONDS_PER_SECOND),
    )


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_hard_flags(field_name: str, value: object) -> None:
    if getattr(value, "paper_only", None) is not True:
        raise ValueError(f"{field_name} paper_only must be True")
    if getattr(value, "report_only", None) is not True:
        raise ValueError(f"{field_name} report_only must be True")
    if getattr(value, "readonly", None) is not True:
        raise ValueError(f"{field_name} readonly must be True")


def _require_exact_type(value: object, type_: type[object], field_name: str) -> None:
    if type(value) is not type_:
        raise ValueError(f"{field_name} must be exactly {type_.__name__}")


def _require_payload_safe_value(field_name: str, value: object) -> None:
    if isinstance(value, Decimal):
        _require_decimal(field_name, value)
        if value != _quantize_decimal(value):
            raise ValueError(f"{field_name} must be quantized to six decimals")
        return
    if isinstance(value, datetime):
        _as_utc(field_name, value)
        if value.tzinfo is not UTC:
            raise ValueError(f"{field_name} must be normalized to UTC")
        return
    if is_dataclass(value) and not isinstance(value, type):
        if type(value) not in _PUBLIC_DATACLASS_TYPES:
            raise ValueError(f"{field_name} must be a known public dataclass")
        _require_hard_flags(field_name, value)
        for field in fields(value):
            _require_payload_safe_value(
                f"{field_name}.{field.name}",
                getattr(value, field.name),
            )
        _reconstruct_public_dataclass(field_name, value)
        return
    if type(value) is tuple:
        for index, item in enumerate(value):
            _require_payload_safe_value(f"{field_name}[{index}]", item)
        return
    if type(value) in (list, dict, set):
        raise ValueError(f"{field_name} must remain constructor-normalized")


def _reconstruct_public_dataclass(field_name: str, value: object) -> None:
    type_ = type(value)
    try:
        type_(**{field.name: getattr(value, field.name) for field in fields(value)})
    except (ArithmeticError, TypeError, ValueError) as exc:
        raise ValueError(f"{field_name} must remain constructor-valid") from exc


def _payload_value(value: object) -> Any:
    if isinstance(value, Decimal):
        return f"{value:.6f}"
    if type(value) is datetime:
        return value.isoformat()
    if is_dataclass(value) and not isinstance(value, type):
        return {
            field.name: _payload_value(getattr(value, field.name))
            for field in fields(value)
        }
    if isinstance(value, tuple):
        return [_payload_value(item) for item in value]
    return value
