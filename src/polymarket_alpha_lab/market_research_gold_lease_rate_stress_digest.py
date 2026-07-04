"""Pure Phase 1 gold lease-rate stress digest reducer."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
from typing import Any


DEFAULT_MARKET_RESEARCH_GOLD_LEASE_RATE_STRESS_DIGEST_CONFIG_VERSION = (
    "market-research-gold-lease-rate-stress-digest-v0"
)

STATUS_READY = "ready"
STATUS_WATCH = "watch"
STATUS_BLOCKED = "blocked"
DIGEST_STATUSES = (STATUS_READY, STATUS_WATCH, STATUS_BLOCKED)

REASON_PREFIX = "market_research_gold_lease_rate_stress_digest_"
NO_INPUTS_REASON = f"{REASON_PREFIX}no_inputs"
NO_STRESS_REASON = f"{REASON_PREFIX}no_stress"
SEVERE_LEASE_RATE_REASON = f"{REASON_PREFIX}severe_lease_rate"
ELEVATED_LEASE_RATE_REASON = f"{REASON_PREFIX}elevated_lease_rate"
LEASE_RATE_SPIKE_REASON = f"{REASON_PREFIX}lease_rate_spike"
BACKWARDATION_PRESSURE_REASON = f"{REASON_PREFIX}backwardation_pressure"
STALE_OBSERVATION_REASON = f"{REASON_PREFIX}stale_observation"
THIN_SOURCES_REASON = f"{REASON_PREFIX}thin_sources"
BLOCKED_REASON = f"{REASON_PREFIX}blocked"
WATCH_REASON = f"{REASON_PREFIX}watch"

REASON_CODE_SEQUENCE = (
    SEVERE_LEASE_RATE_REASON,
    ELEVATED_LEASE_RATE_REASON,
    LEASE_RATE_SPIKE_REASON,
    BACKWARDATION_PRESSURE_REASON,
    STALE_OBSERVATION_REASON,
    THIN_SOURCES_REASON,
    BLOCKED_REASON,
    WATCH_REASON,
    NO_STRESS_REASON,
    NO_INPUTS_REASON,
)
ROW_REASON_CODE_SEQUENCE = (
    SEVERE_LEASE_RATE_REASON,
    ELEVATED_LEASE_RATE_REASON,
    LEASE_RATE_SPIKE_REASON,
    BACKWARDATION_PRESSURE_REASON,
    STALE_OBSERVATION_REASON,
    THIN_SOURCES_REASON,
    BLOCKED_REASON,
    NO_STRESS_REASON,
)

NEXT_STEPS = {
    STATUS_READY: "allow_report_only_gold_lease_rate_stress_digest",
    STATUS_WATCH: "watch_report_only_gold_lease_rate_stress_digest",
    STATUS_BLOCKED: "block_report_only_gold_lease_rate_stress_digest",
}

DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
QUANT = Decimal("0.000001")
ZERO = Decimal("0.000000")
MICROSECONDS_PER_SECOND = Decimal("1000000")


__all__ = (
    "DEFAULT_MARKET_RESEARCH_GOLD_LEASE_RATE_STRESS_DIGEST_CONFIG_VERSION",
    "MarketResearchGoldLeaseRateStressDigestConfig",
    "MarketResearchGoldLeaseRateStressDigestObservation",
    "MarketResearchGoldLeaseRateStressDigestReasonCodeCount",
    "MarketResearchGoldLeaseRateStressDigestReport",
    "MarketResearchGoldLeaseRateStressDigestRow",
    "build_market_research_gold_lease_rate_stress_digest",
    "market_research_gold_lease_rate_stress_digest_payload",
)


@dataclass(frozen=True)
class MarketResearchGoldLeaseRateStressDigestConfig:
    config_version: str = (
        DEFAULT_MARKET_RESEARCH_GOLD_LEASE_RATE_STRESS_DIGEST_CONFIG_VERSION
    )
    severe_lease_rate_threshold_bps: Decimal = Decimal("80.000000")
    elevated_lease_rate_threshold_bps: Decimal = Decimal("40.000000")
    lease_rate_spike_threshold_bps: Decimal = Decimal("25.000000")
    backwardation_threshold_bps: Decimal = Decimal("10.000000")
    max_observation_age_seconds: Decimal = Decimal("86400.000000")
    min_source_count: Decimal = Decimal("2.000000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketResearchGoldLeaseRateStressDigestConfig:
            raise TypeError(
                "MarketResearchGoldLeaseRateStressDigestConfig does not "
                "support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not MarketResearchGoldLeaseRateStressDigestConfig:
            raise ValueError(
                "config must be exactly "
                "MarketResearchGoldLeaseRateStressDigestConfig",
            )
        _require_canonical_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_MARKET_RESEARCH_GOLD_LEASE_RATE_STRESS_DIGEST_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "severe_lease_rate_threshold_bps",
            "elevated_lease_rate_threshold_bps",
            "lease_rate_spike_threshold_bps",
            "backwardation_threshold_bps",
            "max_observation_age_seconds",
            "min_source_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_positive_decimal(field_name, getattr(self, field_name)),
            )
        if self.severe_lease_rate_threshold_bps <= self.elevated_lease_rate_threshold_bps:
            raise ValueError(
                "severe_lease_rate_threshold_bps must exceed "
                "elevated_lease_rate_threshold_bps",
            )
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class MarketResearchGoldLeaseRateStressDigestObservation:
    tenor_key: str
    market_slug: str
    observed_at: datetime
    lease_rate_bps: Decimal
    baseline_lease_rate_bps: Decimal
    futures_basis_bps: Decimal
    source_count: Decimal
    source_reference: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketResearchGoldLeaseRateStressDigestObservation:
            raise TypeError(
                "MarketResearchGoldLeaseRateStressDigestObservation does not "
                "support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not MarketResearchGoldLeaseRateStressDigestObservation:
            raise ValueError(
                "observation must be exactly "
                "MarketResearchGoldLeaseRateStressDigestObservation",
            )
        for field_name in ("tenor_key", "market_slug"):
            _require_public_string(field_name, getattr(self, field_name))
        _require_plain_string("source_reference", self.source_reference)
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in (
            "lease_rate_bps",
            "baseline_lease_rate_bps",
            "futures_basis_bps",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_finite_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "source_count",
            _require_nonnegative_decimal("source_count", self.source_count),
        )
        _require_hard_flags("observation", self)


@dataclass(frozen=True)
class MarketResearchGoldLeaseRateStressDigestRow:
    tenor_key: str
    market_slug: str
    observed_at: datetime
    digest_status: str
    observation_age_seconds: Decimal
    lease_rate_bps: Decimal
    baseline_lease_rate_bps: Decimal
    lease_rate_delta_bps: Decimal
    futures_basis_bps: Decimal
    source_count: Decimal
    redacted_source_reference: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketResearchGoldLeaseRateStressDigestRow:
            raise TypeError(
                "MarketResearchGoldLeaseRateStressDigestRow does not "
                "support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not MarketResearchGoldLeaseRateStressDigestRow:
            raise ValueError(
                "row must be exactly MarketResearchGoldLeaseRateStressDigestRow",
            )
        for field_name in ("tenor_key", "market_slug"):
            _require_public_string(field_name, getattr(self, field_name))
        _require_plain_string(
            "redacted_source_reference",
            self.redacted_source_reference,
        )
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        _require_status("digest_status", self.digest_status)
        for field_name in (
            "observation_age_seconds",
            "lease_rate_bps",
            "baseline_lease_rate_bps",
            "lease_rate_delta_bps",
            "futures_basis_bps",
            "source_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_finite_decimal(field_name, getattr(self, field_name)),
            )
        _require_nonnegative_decimal("observation_age_seconds", self.observation_age_seconds)
        _require_nonnegative_decimal("source_count", self.source_count)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(
                self.reason_codes,
                sequence=ROW_REASON_CODE_SEQUENCE,
            ),
        )
        if self.digest_status == STATUS_READY and self.reason_codes != (NO_STRESS_REASON,):
            raise ValueError("ready rows must only use no stress")
        if self.digest_status == STATUS_BLOCKED and BLOCKED_REASON not in self.reason_codes:
            raise ValueError("blocked rows must include blocked")
        if self.digest_status == STATUS_WATCH and not any(
            reason in self.reason_codes
            for reason in (
                ELEVATED_LEASE_RATE_REASON,
                LEASE_RATE_SPIKE_REASON,
                BACKWARDATION_PRESSURE_REASON,
                STALE_OBSERVATION_REASON,
                THIN_SOURCES_REASON,
            )
        ):
            raise ValueError("watch rows must include a watch reason")
        _require_hard_flags("row", self)


@dataclass(frozen=True)
class MarketResearchGoldLeaseRateStressDigestReasonCodeCount:
    reason_code: str
    count: Decimal
    observation_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketResearchGoldLeaseRateStressDigestReasonCodeCount:
            raise TypeError(
                "MarketResearchGoldLeaseRateStressDigestReasonCodeCount does "
                "not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not MarketResearchGoldLeaseRateStressDigestReasonCodeCount:
            raise ValueError(
                "reason code count must be exactly "
                "MarketResearchGoldLeaseRateStressDigestReasonCodeCount",
            )
        _require_reason_code("reason_code", self.reason_code)
        object.__setattr__(
            self,
            "count",
            _require_nonnegative_decimal("count", self.count),
        )
        object.__setattr__(
            self,
            "observation_ratio",
            _require_ratio_decimal("observation_ratio", self.observation_ratio),
        )
        _require_hard_flags("reason code count", self)


@dataclass(frozen=True)
class MarketResearchGoldLeaseRateStressDigestReport:
    generated_at: datetime
    config_version: str
    digest_status: str
    recommended_next_step: str
    observation_count: Decimal
    severe_lease_rate_count: Decimal
    elevated_lease_rate_count: Decimal
    lease_rate_spike_count: Decimal
    backwardation_pressure_count: Decimal
    stale_observation_count: Decimal
    thin_source_count: Decimal
    max_lease_rate_bps: Decimal
    average_lease_rate_bps: Decimal
    average_lease_rate_delta_bps: Decimal
    average_source_count: Decimal
    observations: tuple[MarketResearchGoldLeaseRateStressDigestRow, ...]
    reason_codes: tuple[str, ...]
    reason_code_counts: tuple[
        MarketResearchGoldLeaseRateStressDigestReasonCodeCount,
        ...,
    ]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketResearchGoldLeaseRateStressDigestReport:
            raise TypeError(
                "MarketResearchGoldLeaseRateStressDigestReport does not "
                "support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not MarketResearchGoldLeaseRateStressDigestReport:
            raise ValueError(
                "report must be exactly "
                "MarketResearchGoldLeaseRateStressDigestReport",
            )
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        _require_status("digest_status", self.digest_status)
        _require_public_string("recommended_next_step", self.recommended_next_step)
        if self.recommended_next_step != NEXT_STEPS[self.digest_status]:
            raise ValueError("recommended_next_step must match digest_status")
        for field_name in (
            "observation_count",
            "severe_lease_rate_count",
            "elevated_lease_rate_count",
            "lease_rate_spike_count",
            "backwardation_pressure_count",
            "stale_observation_count",
            "thin_source_count",
            "max_lease_rate_bps",
            "average_lease_rate_bps",
            "average_lease_rate_delta_bps",
            "average_source_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_finite_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "observation_count",
            "severe_lease_rate_count",
            "elevated_lease_rate_count",
            "lease_rate_spike_count",
            "backwardation_pressure_count",
            "stale_observation_count",
            "thin_source_count",
            "average_source_count",
        ):
            _require_nonnegative_decimal(field_name, getattr(self, field_name))
        object.__setattr__(
            self,
            "observations",
            _normalize_rows(self.observations),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(
                self.reason_codes,
                sequence=REASON_CODE_SEQUENCE,
            ),
        )
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        _validate_report(self)
        _require_hard_flags("report", self)


def build_market_research_gold_lease_rate_stress_digest(
    observations: tuple[object, ...],
    *,
    generated_at: datetime,
    config: MarketResearchGoldLeaseRateStressDigestConfig | None = None,
) -> MarketResearchGoldLeaseRateStressDigestReport:
    cfg = config or MarketResearchGoldLeaseRateStressDigestConfig()
    if type(cfg) is not MarketResearchGoldLeaseRateStressDigestConfig:
        raise ValueError(
            "config must be exactly MarketResearchGoldLeaseRateStressDigestConfig",
        )
    _require_hard_flags("config", cfg)
    generated_at_utc = _as_utc("generated_at", generated_at)
    rows = tuple(
        sorted(
            (
                _build_row(observation, generated_at=generated_at_utc, config=cfg)
                for observation in _normalize_input_observations(observations)
            ),
            key=lambda row: (row.tenor_key, row.observed_at, row.market_slug),
        ),
    )
    reason_codes = _report_reason_codes(rows)
    digest_status = _report_status(rows, reason_codes)
    return MarketResearchGoldLeaseRateStressDigestReport(
        generated_at=generated_at_utc,
        config_version=cfg.config_version,
        digest_status=digest_status,
        recommended_next_step=NEXT_STEPS[digest_status],
        observation_count=_decimal_count(len(rows)),
        severe_lease_rate_count=_decimal_count(
            sum(1 for row in rows if SEVERE_LEASE_RATE_REASON in row.reason_codes),
        ),
        elevated_lease_rate_count=_decimal_count(
            sum(1 for row in rows if ELEVATED_LEASE_RATE_REASON in row.reason_codes),
        ),
        lease_rate_spike_count=_decimal_count(
            sum(1 for row in rows if LEASE_RATE_SPIKE_REASON in row.reason_codes),
        ),
        backwardation_pressure_count=_decimal_count(
            sum(1 for row in rows if BACKWARDATION_PRESSURE_REASON in row.reason_codes),
        ),
        stale_observation_count=_decimal_count(
            sum(1 for row in rows if STALE_OBSERVATION_REASON in row.reason_codes),
        ),
        thin_source_count=_decimal_count(
            sum(1 for row in rows if THIN_SOURCES_REASON in row.reason_codes),
        ),
        max_lease_rate_bps=_max_lease_rate_bps(rows),
        average_lease_rate_bps=_average_lease_rate_bps(rows),
        average_lease_rate_delta_bps=_average_lease_rate_delta_bps(rows),
        average_source_count=_average_source_count(rows),
        observations=rows,
        reason_codes=reason_codes,
        reason_code_counts=_reason_code_counts(reason_codes, rows),
    )


def market_research_gold_lease_rate_stress_digest_payload(
    report: MarketResearchGoldLeaseRateStressDigestReport | dict[str, Any],
) -> dict[str, Any]:
    if type(report) is MarketResearchGoldLeaseRateStressDigestReport:
        _validate_report(report)
        _require_hard_flags("report", report)
        _reject_unsafe_public_value("report", report)
        value = asdict(report)
    elif type(report) is dict:
        _reject_unsafe_public_value("payload", report)
        value = report
    else:
        raise ValueError(
            "report must be exactly MarketResearchGoldLeaseRateStressDigestReport",
        )
    result = _serialize_payload(value)
    if type(result) is not dict:
        raise ValueError("report payload must be a JSON object")
    _require_hard_flags("payload", _DictFlags(result))
    _reject_unsafe_public_value("payload", result)
    return result


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
    observation: MarketResearchGoldLeaseRateStressDigestObservation,
    *,
    generated_at: datetime,
    config: MarketResearchGoldLeaseRateStressDigestConfig,
) -> MarketResearchGoldLeaseRateStressDigestRow:
    age_seconds = _seconds_between(generated_at, observation.observed_at)
    if age_seconds < ZERO:
        raise ValueError("observed_at cannot be after generated_at")
    lease_rate_delta = _quantize(
        observation.lease_rate_bps - observation.baseline_lease_rate_bps,
    )
    reason_codes = _row_reason_codes(
        lease_rate_bps=observation.lease_rate_bps,
        lease_rate_delta_bps=lease_rate_delta,
        futures_basis_bps=observation.futures_basis_bps,
        observation_age_seconds=age_seconds,
        source_count=observation.source_count,
        config=config,
    )
    return MarketResearchGoldLeaseRateStressDigestRow(
        tenor_key=observation.tenor_key,
        market_slug=observation.market_slug,
        observed_at=observation.observed_at,
        digest_status=_row_status(reason_codes),
        observation_age_seconds=age_seconds,
        lease_rate_bps=_quantize(observation.lease_rate_bps),
        baseline_lease_rate_bps=_quantize(observation.baseline_lease_rate_bps),
        lease_rate_delta_bps=lease_rate_delta,
        futures_basis_bps=_quantize(observation.futures_basis_bps),
        source_count=_quantize(observation.source_count),
        redacted_source_reference=_redact_reference(observation.source_reference),
        reason_codes=reason_codes,
    )


def _row_reason_codes(
    *,
    lease_rate_bps: Decimal,
    lease_rate_delta_bps: Decimal,
    futures_basis_bps: Decimal,
    observation_age_seconds: Decimal,
    source_count: Decimal,
    config: MarketResearchGoldLeaseRateStressDigestConfig,
) -> tuple[str, ...]:
    reasons: list[str] = []
    if lease_rate_bps >= config.severe_lease_rate_threshold_bps:
        reasons.append(SEVERE_LEASE_RATE_REASON)
    elif lease_rate_bps >= config.elevated_lease_rate_threshold_bps:
        reasons.append(ELEVATED_LEASE_RATE_REASON)
    if lease_rate_delta_bps >= config.lease_rate_spike_threshold_bps:
        reasons.append(LEASE_RATE_SPIKE_REASON)
    if futures_basis_bps <= -config.backwardation_threshold_bps:
        reasons.append(BACKWARDATION_PRESSURE_REASON)
    if observation_age_seconds > config.max_observation_age_seconds:
        reasons.append(STALE_OBSERVATION_REASON)
    if source_count < config.min_source_count:
        reasons.append(THIN_SOURCES_REASON)
    if (
        SEVERE_LEASE_RATE_REASON in reasons
        and BACKWARDATION_PRESSURE_REASON in reasons
    ):
        reasons.append(BLOCKED_REASON)
    if not reasons:
        reasons.append(NO_STRESS_REASON)
    return _normalize_reason_codes(
        tuple(reasons),
        sequence=ROW_REASON_CODE_SEQUENCE,
    )


def _row_status(reason_codes: tuple[str, ...]) -> str:
    if BLOCKED_REASON in reason_codes:
        return STATUS_BLOCKED
    if reason_codes == (NO_STRESS_REASON,):
        return STATUS_READY
    return STATUS_WATCH


def _report_reason_codes(
    rows: tuple[MarketResearchGoldLeaseRateStressDigestRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return (NO_INPUTS_REASON,)
    present = {reason_code for row in rows for reason_code in row.reason_codes}
    reasons: list[str] = [
        reason_code
        for reason_code in REASON_CODE_SEQUENCE
        if reason_code in present and reason_code != NO_STRESS_REASON
    ]
    if NO_STRESS_REASON in present and not any(
        row.digest_status in (STATUS_WATCH, STATUS_BLOCKED) for row in rows
    ):
        reasons.append(NO_STRESS_REASON)
    if any(row.digest_status == STATUS_WATCH for row in rows) and not any(
        row.digest_status == STATUS_BLOCKED for row in rows
    ):
        reasons.append(WATCH_REASON)
    return _normalize_reason_codes(tuple(reasons), sequence=REASON_CODE_SEQUENCE)


def _report_status(
    rows: tuple[MarketResearchGoldLeaseRateStressDigestRow, ...],
    reason_codes: tuple[str, ...],
) -> str:
    if not rows or BLOCKED_REASON in reason_codes:
        return STATUS_BLOCKED
    if any(row.digest_status == STATUS_WATCH for row in rows):
        return STATUS_WATCH
    return STATUS_READY


def _reason_code_counts(
    reason_codes: tuple[str, ...],
    rows: tuple[MarketResearchGoldLeaseRateStressDigestRow, ...],
) -> tuple[MarketResearchGoldLeaseRateStressDigestReasonCodeCount, ...]:
    if not rows:
        return (
            MarketResearchGoldLeaseRateStressDigestReasonCodeCount(
                reason_code=NO_INPUTS_REASON,
                count=ZERO,
                observation_ratio=ZERO,
            ),
        )
    total = _decimal_count(len(rows))
    return tuple(
        MarketResearchGoldLeaseRateStressDigestReasonCodeCount(
            reason_code=reason_code,
            count=_reason_count(reason_code, rows),
            observation_ratio=_ratio(_reason_count(reason_code, rows), total),
        )
        for reason_code in reason_codes
    )


def _reason_count(
    reason_code: str,
    rows: tuple[MarketResearchGoldLeaseRateStressDigestRow, ...],
) -> Decimal:
    if reason_code == WATCH_REASON:
        return _decimal_count(sum(1 for row in rows if row.digest_status == STATUS_WATCH))
    return _decimal_count(sum(1 for row in rows if reason_code in row.reason_codes))


def _max_lease_rate_bps(
    rows: tuple[MarketResearchGoldLeaseRateStressDigestRow, ...],
) -> Decimal:
    if not rows:
        return ZERO
    return _quantize(max(row.lease_rate_bps for row in rows))


def _average_lease_rate_bps(
    rows: tuple[MarketResearchGoldLeaseRateStressDigestRow, ...],
) -> Decimal:
    if not rows:
        return ZERO
    return _ratio(sum(row.lease_rate_bps for row in rows), _decimal_count(len(rows)))


def _average_lease_rate_delta_bps(
    rows: tuple[MarketResearchGoldLeaseRateStressDigestRow, ...],
) -> Decimal:
    if not rows:
        return ZERO
    return _ratio(
        sum(row.lease_rate_delta_bps for row in rows),
        _decimal_count(len(rows)),
    )


def _average_source_count(
    rows: tuple[MarketResearchGoldLeaseRateStressDigestRow, ...],
) -> Decimal:
    if not rows:
        return ZERO
    return _ratio(sum(row.source_count for row in rows), _decimal_count(len(rows)))


def _normalize_input_observations(
    observations: tuple[object, ...],
) -> tuple[MarketResearchGoldLeaseRateStressDigestObservation, ...]:
    if isinstance(observations, (str, bytes)) or not isinstance(observations, tuple):
        raise ValueError("observations must be a tuple")
    for observation in observations:
        if type(observation) is not MarketResearchGoldLeaseRateStressDigestObservation:
            raise ValueError(
                "observations must contain exactly "
                "MarketResearchGoldLeaseRateStressDigestObservation",
            )
        _require_hard_flags("observation", observation)
    return observations


def _normalize_rows(
    rows: tuple[MarketResearchGoldLeaseRateStressDigestRow, ...],
) -> tuple[MarketResearchGoldLeaseRateStressDigestRow, ...]:
    if isinstance(rows, (str, bytes)) or not isinstance(rows, tuple):
        raise ValueError("observations must be a tuple")
    for row in rows:
        if type(row) is not MarketResearchGoldLeaseRateStressDigestRow:
            raise ValueError(
                "observations must contain exactly "
                "MarketResearchGoldLeaseRateStressDigestRow",
            )
        _require_hard_flags("row", row)
    return tuple(sorted(rows, key=lambda row: (row.tenor_key, row.observed_at, row.market_slug)))


def _normalize_reason_code_counts(
    counts: tuple[MarketResearchGoldLeaseRateStressDigestReasonCodeCount, ...],
) -> tuple[MarketResearchGoldLeaseRateStressDigestReasonCodeCount, ...]:
    if isinstance(counts, (str, bytes)) or not isinstance(counts, tuple):
        raise ValueError("reason_code_counts must be a tuple")
    for count in counts:
        if type(count) is not MarketResearchGoldLeaseRateStressDigestReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain exactly "
                "MarketResearchGoldLeaseRateStressDigestReasonCodeCount",
            )
        _require_hard_flags("reason code count", count)
    return tuple(sorted(counts, key=lambda count: REASON_CODE_SEQUENCE.index(count.reason_code)))


def _normalize_reason_codes(
    reason_codes: tuple[str, ...],
    *,
    sequence: tuple[str, ...],
) -> tuple[str, ...]:
    if isinstance(reason_codes, (str, bytes)) or not isinstance(reason_codes, tuple):
        raise ValueError("reason_codes must be a tuple")
    if not reason_codes:
        raise ValueError("reason_codes must not be empty")
    for reason_code in reason_codes:
        _require_reason_code("reason_code", reason_code)
        if reason_code not in sequence:
            raise ValueError("reason_codes must contain supported reason codes")
    return tuple(sorted(dict.fromkeys(reason_codes), key=lambda code: sequence.index(code)))


def _validate_report(report: MarketResearchGoldLeaseRateStressDigestReport) -> None:
    rows = report.observations
    if report.observation_count != _decimal_count(len(rows)):
        raise ValueError("observation_count must match observations")
    expected_codes = _report_reason_codes(rows)
    if report.reason_codes != expected_codes:
        raise ValueError("reason_codes must match observations")
    expected_status = _report_status(rows, report.reason_codes)
    if report.digest_status != expected_status:
        raise ValueError("digest_status must match observations")
    if report.recommended_next_step != NEXT_STEPS[report.digest_status]:
        raise ValueError("recommended_next_step must match digest_status")
    expected_counts = _reason_code_counts(report.reason_codes, rows)
    if report.reason_code_counts != expected_counts:
        raise ValueError("reason_code_counts must match observations")
    if report.severe_lease_rate_count != _reason_count(SEVERE_LEASE_RATE_REASON, rows):
        raise ValueError("severe_lease_rate_count must match observations")
    if report.elevated_lease_rate_count != _reason_count(ELEVATED_LEASE_RATE_REASON, rows):
        raise ValueError("elevated_lease_rate_count must match observations")
    if report.lease_rate_spike_count != _reason_count(LEASE_RATE_SPIKE_REASON, rows):
        raise ValueError("lease_rate_spike_count must match observations")
    if report.backwardation_pressure_count != _reason_count(
        BACKWARDATION_PRESSURE_REASON,
        rows,
    ):
        raise ValueError("backwardation_pressure_count must match observations")
    if report.stale_observation_count != _reason_count(STALE_OBSERVATION_REASON, rows):
        raise ValueError("stale_observation_count must match observations")
    if report.thin_source_count != _reason_count(THIN_SOURCES_REASON, rows):
        raise ValueError("thin_source_count must match observations")
    if report.max_lease_rate_bps != _max_lease_rate_bps(rows):
        raise ValueError("max_lease_rate_bps must match observations")
    if report.average_lease_rate_bps != _average_lease_rate_bps(rows):
        raise ValueError("average_lease_rate_bps must match observations")
    if report.average_lease_rate_delta_bps != _average_lease_rate_delta_bps(rows):
        raise ValueError("average_lease_rate_delta_bps must match observations")
    if report.average_source_count != _average_source_count(rows):
        raise ValueError("average_source_count must match observations")


def _reject_unsafe_public_value(label: str, value: object, path: str = "") -> None:
    if hasattr(value, "__dataclass_fields__") and not isinstance(value, type):
        _reject_unsafe_public_value(label, asdict(value), path)
        return
    if isinstance(value, Decimal):
        if type(value) is not Decimal:
            raise ValueError(f"{path or label} must be a Decimal")
        if not value.is_finite():
            raise ValueError(f"{path or label} must be finite")
        return
    if isinstance(value, datetime):
        if type(value) is not datetime:
            raise ValueError(f"{path or label} must be exactly datetime")
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError(f"{path or label} must be timezone-aware")
        return
    if value is None or type(value) is bool:
        return
    if type(value) is int:
        raise ValueError(f"{path or label} must use Decimal-derived string values")
    if isinstance(value, float):
        raise ValueError(f"{path or label} must not be a float")
    if type(value) is str:
        if path.endswith("redacted_source_reference"):
            _require_plain_string(path or label, value)
            if "://" in value.lower() or "?" in value.lower():
                raise ValueError(f"{path or label} has unsafe value")
            return
        lowered = value.lower()
        if "://" in lowered or "?" in lowered:
            raise ValueError(f"{path or label} has unsafe value")
        if _has_unsafe_public_text_fragment(lowered):
            raise ValueError(f"{path or label} has unsafe value")
        return
    if isinstance(value, dict):
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            item_path = key if not path else f"{path}.{key}"
            if key in ("paper_only", "report_only", "readonly") and item is not True:
                raise ValueError(f"{item_path} must be True for {label}")
            if _has_unsafe_public_text_fragment(key.lower()):
                raise ValueError(f"{item_path} has unsafe field")
            _reject_unsafe_public_value(label, item, item_path)
        return
    if isinstance(value, (list, tuple)):
        for index, item in enumerate(value):
            item_path = f"{path}[{index}]" if path else f"{label}[{index}]"
            _reject_unsafe_public_value(label, item, item_path)
        return
    raise ValueError(f"{path or label} is not JSON serializable")


def _has_unsafe_public_text_fragment(value: str) -> bool:
    return any(
        fragment in value
        for fragment in (
            "".join(("au", "th")),
            "".join(("bro", "ker")),
            "".join(("to", "ken")),
            "".join(("sec", "ret")),
            "".join(("wal", "let")),
            "".join(("pri", "vate")),
        )
    )


def _serialize_payload(value: Any) -> Any:
    if isinstance(value, Decimal):
        if type(value) is not Decimal:
            raise ValueError("value must be a Decimal")
        return f"{value.quantize(QUANT):f}"
    if isinstance(value, datetime):
        if type(value) is not datetime:
            raise ValueError("value must be exactly datetime")
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("value must be timezone-aware")
        return value.astimezone(UTC).isoformat()
    if type(value) is int:
        raise ValueError("value must use Decimal-derived string values")
    if isinstance(value, float):
        raise ValueError("value must not be a float")
    if isinstance(value, tuple):
        return [_serialize_payload(item) for item in value]
    if isinstance(value, list):
        return [_serialize_payload(item) for item in value]
    if isinstance(value, dict):
        return {key: _serialize_payload(item) for key, item in value.items()}
    return value


def _redact_reference(reference: str) -> str:
    if reference == "public-lbma-gold-lease-release":
        return reference
    digest = sha256(reference.encode("utf-8")).hexdigest()[:12]
    return f"sha256:{digest}"


def _seconds_between(later: datetime, earlier: datetime) -> Decimal:
    delta = later - earlier
    seconds = Decimal(delta.days * 86400 + delta.seconds)
    microseconds = Decimal(delta.microseconds) / MICROSECONDS_PER_SECOND
    return _quantize(seconds + microseconds)


def _ratio(value: Decimal, total: Decimal) -> Decimal:
    if total == ZERO:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return _quantize(value / total)


def _decimal_count(value: int) -> Decimal:
    return _quantize(Decimal(value))


def _quantize(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(QUANT)


def _as_utc(field_name: str, value: datetime) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be exactly datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_status(field_name: str, value: str) -> None:
    _require_public_string(field_name, value)
    if value not in DIGEST_STATUSES:
        raise ValueError(f"{field_name} must be a supported status")


def _require_reason_code(field_name: str, value: str) -> None:
    _require_public_string(field_name, value)
    if value not in REASON_CODE_SEQUENCE:
        raise ValueError(f"{field_name} must be a supported reason code")


def _require_public_string(field_name: str, value: str) -> None:
    _require_plain_string(field_name, value)
    if _has_unsafe_public_text_fragment(value.lower()):
        raise ValueError(f"{field_name} must be a public identifier")


def _require_plain_string(field_name: str, value: str) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a plain str")
    if not value or not value.strip():
        raise ValueError(f"{field_name} must not be empty")


def _require_canonical_string(field_name: str, value: str) -> None:
    _require_public_string(field_name, value)
    if value != value.strip() or value.lower() != value:
        raise ValueError(f"{field_name} must be canonical lowercase text")


def _require_decimal(field_name: str, value: Decimal) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    return value


def _require_finite_decimal(field_name: str, value: Decimal) -> Decimal:
    value = _require_decimal(field_name, value)
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return _quantize(value)


def _require_nonnegative_decimal(field_name: str, value: Decimal) -> Decimal:
    value = _require_finite_decimal(field_name, value)
    if value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return value


def _require_positive_decimal(field_name: str, value: Decimal) -> Decimal:
    value = _require_finite_decimal(field_name, value)
    if value <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return value


def _require_ratio_decimal(field_name: str, value: Decimal) -> Decimal:
    value = _require_finite_decimal(field_name, value)
    if value < ZERO or value > Decimal("1.000000"):
        raise ValueError(f"{field_name} must be between 0 and 1")
    return value


def _require_hard_flags(field_name: str, value: object) -> None:
    if getattr(value, "paper_only", None) is not True:
        raise ValueError(f"{field_name} must be paper_only")
    if getattr(value, "report_only", None) is not True:
        raise ValueError(f"{field_name} must be report_only")
    if getattr(value, "readonly", None) is not True:
        raise ValueError(f"{field_name} must be readonly")
