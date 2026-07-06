"""Pure Phase 1 crypto staking validator missed slots digest reducer."""

from __future__ import annotations

from dataclasses import dataclass, fields
from datetime import UTC, datetime
from decimal import Context, Decimal, InvalidOperation, ROUND_HALF_EVEN, localcontext
import re
from typing import Any


DEFAULT_MARKET_RESEARCH_CRYPTO_STAKING_VALIDATOR_MISSED_SLOTS_DIGEST_CONFIG_VERSION = (
    "market-research-crypto-staking-validator-missed-slots-digest-v0"
)

PASS_STATUS = "pass"
WATCH_STATUS = "watch"
BLOCKED_STATUS = "blocked"
DIGEST_STATUSES = (PASS_STATUS, WATCH_STATUS, BLOCKED_STATUS)
ROW_STATUSES = DIGEST_STATUSES

HIGH_COUNT_REASON = "crypto_staking_validator_missed_slots_high_count"
HIGH_RATE_REASON = "crypto_staking_validator_missed_slots_high_rate"
LOW_ATTESTATION_REASON = "crypto_staking_validator_missed_slots_low_attestation"
STALE_OBSERVATION_REASON = "crypto_staking_validator_missed_slots_stale_observation"
ROW_BLOCKED_REASON = "crypto_staking_validator_missed_slots_blocked"
ROW_WATCH_REASON = "crypto_staking_validator_missed_slots_watch"
ROW_CLEAR_REASON = "crypto_staking_validator_missed_slots_clear"

DIGEST_BLOCKED_REASON = "crypto_staking_validator_missed_slots_blocked_present"
DIGEST_WATCH_REASON = "crypto_staking_validator_missed_slots_watch_present"
DIGEST_HIGH_COUNT_REASON = "crypto_staking_validator_missed_slots_high_count_present"
DIGEST_HIGH_RATE_REASON = "crypto_staking_validator_missed_slots_high_rate_present"
DIGEST_LOW_ATTESTATION_REASON = (
    "crypto_staking_validator_missed_slots_low_attestation_present"
)
DIGEST_STALE_OBSERVATION_REASON = (
    "crypto_staking_validator_missed_slots_stale_observation_present"
)
DIGEST_CLEAR_REASON = "crypto_staking_validator_missed_slots_digest_clear"
DIGEST_EMPTY_REASON = "crypto_staking_validator_missed_slots_digest_empty"

ROW_REASON_CODES = (
    HIGH_COUNT_REASON,
    HIGH_RATE_REASON,
    LOW_ATTESTATION_REASON,
    STALE_OBSERVATION_REASON,
    ROW_BLOCKED_REASON,
    ROW_WATCH_REASON,
    ROW_CLEAR_REASON,
)
REPORT_REASON_CODES = (
    DIGEST_BLOCKED_REASON,
    DIGEST_WATCH_REASON,
    DIGEST_HIGH_COUNT_REASON,
    DIGEST_HIGH_RATE_REASON,
    DIGEST_LOW_ATTESTATION_REASON,
    DIGEST_STALE_OBSERVATION_REASON,
    DIGEST_CLEAR_REASON,
    DIGEST_EMPTY_REASON,
)
REPORT_TO_ROW_REASON = {
    DIGEST_BLOCKED_REASON: ROW_BLOCKED_REASON,
    DIGEST_WATCH_REASON: ROW_WATCH_REASON,
    DIGEST_HIGH_COUNT_REASON: HIGH_COUNT_REASON,
    DIGEST_HIGH_RATE_REASON: HIGH_RATE_REASON,
    DIGEST_LOW_ATTESTATION_REASON: LOW_ATTESTATION_REASON,
    DIGEST_STALE_OBSERVATION_REASON: STALE_OBSERVATION_REASON,
    DIGEST_CLEAR_REASON: ROW_CLEAR_REASON,
}
NEXT_STEP_BY_STATUS = {
    PASS_STATUS: "allow_report_only_crypto_staking_validator_missed_slots_digest",
    WATCH_STATUS: "monitor_report_only_crypto_staking_validator_missed_slots_digest",
    BLOCKED_STATUS: "block_report_only_crypto_staking_validator_missed_slots_digest",
}
STATUS_RANK = {
    BLOCKED_STATUS: Decimal("0.000000"),
    WATCH_STATUS: Decimal("1.000000"),
    PASS_STATUS: Decimal("2.000000"),
}

DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
QUANTUM = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
SIGNAL_DENOMINATOR = Decimal("4.000000")
MICROSECONDS_PER_MINUTE = Decimal("60000000.000000")
PHASE_FLAG_FIELDS = ("paper_only", "report_only", "readonly")
_CANONICAL_RE = re.compile(r"^[a-z0-9][a-z0-9_.-]*$")


__all__ = (
    "DEFAULT_MARKET_RESEARCH_CRYPTO_STAKING_VALIDATOR_MISSED_SLOTS_DIGEST_CONFIG_VERSION",
    "ROW_REASON_CODES",
    "REPORT_REASON_CODES",
    "MarketResearchCryptoStakingValidatorMissedSlotsDigestConfig",
    "MarketResearchCryptoStakingValidatorMissedSlotsObservation",
    "MarketResearchCryptoStakingValidatorMissedSlotsDigestRow",
    "MarketResearchCryptoStakingValidatorMissedSlotsReasonCodeCount",
    "MarketResearchCryptoStakingValidatorMissedSlotsDigestReport",
    "build_market_research_crypto_staking_validator_missed_slots_digest",
    "market_research_crypto_staking_validator_missed_slots_digest_payload",
)


class _NoSubclass:
    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if _NoSubclass not in cls.__bases__:
            raise TypeError(f"{cls.__name__} does not support subclassing")


@dataclass(frozen=True)
class MarketResearchCryptoStakingValidatorMissedSlotsDigestConfig(_NoSubclass):
    config_version: str = (
        DEFAULT_MARKET_RESEARCH_CRYPTO_STAKING_VALIDATOR_MISSED_SLOTS_DIGEST_CONFIG_VERSION
    )
    watch_missed_slot_count: Decimal = Decimal("2.000000")
    blocked_missed_slot_count: Decimal = Decimal("4.000000")
    watch_missed_slot_rate: Decimal = Decimal("0.200000")
    blocked_missed_slot_rate: Decimal = Decimal("0.400000")
    min_attestation_participation_rate: Decimal = Decimal("0.950000")
    stale_observation_minutes: Decimal = Decimal("120.000000")
    watch_signal_count: Decimal = Decimal("2.000000")
    blocked_signal_count: Decimal = Decimal("4.000000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, MarketResearchCryptoStakingValidatorMissedSlotsDigestConfig, "config")
        _require_canonical_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_MARKET_RESEARCH_CRYPTO_STAKING_VALIDATOR_MISSED_SLOTS_DIGEST_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "watch_missed_slot_count",
            "blocked_missed_slot_count",
            "watch_signal_count",
            "blocked_signal_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_positive_whole_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in ("watch_missed_slot_rate", "blocked_missed_slot_rate"):
            object.__setattr__(
                self,
                field_name,
                _require_ratio(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "min_attestation_participation_rate",
            _require_positive_ratio(
                "min_attestation_participation_rate",
                self.min_attestation_participation_rate,
            ),
        )
        object.__setattr__(
            self,
            "stale_observation_minutes",
            _require_positive_decimal(
                "stale_observation_minutes",
                self.stale_observation_minutes,
            ),
        )
        if self.watch_missed_slot_count > self.blocked_missed_slot_count:
            raise ValueError(
                "watch_missed_slot_count must not exceed blocked_missed_slot_count",
            )
        if self.watch_missed_slot_rate > self.blocked_missed_slot_rate:
            raise ValueError(
                "watch_missed_slot_rate must not exceed blocked_missed_slot_rate",
            )
        if self.watch_signal_count > self.blocked_signal_count:
            raise ValueError("watch_signal_count must not exceed blocked_signal_count")
        if self.blocked_signal_count > SIGNAL_DENOMINATOR:
            raise ValueError("blocked_signal_count must not exceed signal count")
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class MarketResearchCryptoStakingValidatorMissedSlotsObservation(_NoSubclass):
    source_id: str
    validator_id: str
    network: str
    epoch_id: str
    slot_window_start: datetime
    slot_window_end: datetime
    expected_slot_count: Decimal
    missed_slot_count: Decimal
    proposed_slot_count: Decimal
    attestation_participation_rate: Decimal
    observed_at: datetime
    upstream_reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, MarketResearchCryptoStakingValidatorMissedSlotsObservation, "observation")
        for field_name in ("source_id", "validator_id", "network", "epoch_id"):
            _require_canonical_string(field_name, getattr(self, field_name))
        object.__setattr__(
            self,
            "slot_window_start",
            _as_utc("slot_window_start", self.slot_window_start),
        )
        object.__setattr__(
            self,
            "slot_window_end",
            _as_utc("slot_window_end", self.slot_window_end),
        )
        if self.slot_window_end <= self.slot_window_start:
            raise ValueError("slot_window_end must be after slot_window_start")
        for field_name in (
            "expected_slot_count",
            "missed_slot_count",
            "proposed_slot_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_whole_decimal(field_name, getattr(self, field_name)),
            )
        if self.expected_slot_count <= ZERO:
            raise ValueError("expected_slot_count must be positive")
        object.__setattr__(
            self,
            "attestation_participation_rate",
            _require_ratio(
                "attestation_participation_rate",
                self.attestation_participation_rate,
            ),
        )
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        object.__setattr__(
            self,
            "upstream_reason_codes",
            _normalize_open_reason_codes(
                "upstream_reason_codes",
                self.upstream_reason_codes,
            ),
        )
        _validate_observation(self)
        _require_hard_flags("observation", self)


@dataclass(frozen=True)
class MarketResearchCryptoStakingValidatorMissedSlotsDigestRow(_NoSubclass):
    source_id: str
    validator_id: str
    network: str
    epoch_id: str
    slot_window_start: datetime
    slot_window_end: datetime
    window_duration_minutes: Decimal
    expected_slot_count: Decimal
    missed_slot_count: Decimal
    proposed_slot_count: Decimal
    missed_slot_rate: Decimal
    attestation_participation_rate: Decimal
    observed_at: datetime
    observation_lag_minutes: Decimal
    missed_slot_signal_count: Decimal
    missed_slot_risk_score: Decimal
    row_status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, MarketResearchCryptoStakingValidatorMissedSlotsDigestRow, "row")
        for field_name in ("source_id", "validator_id", "network", "epoch_id"):
            _require_canonical_string(field_name, getattr(self, field_name))
        object.__setattr__(
            self,
            "slot_window_start",
            _as_utc("slot_window_start", self.slot_window_start),
        )
        object.__setattr__(
            self,
            "slot_window_end",
            _as_utc("slot_window_end", self.slot_window_end),
        )
        if self.slot_window_end <= self.slot_window_start:
            raise ValueError("slot_window_end must be after slot_window_start")
        for field_name in (
            "window_duration_minutes",
            "observation_lag_minutes",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "expected_slot_count",
            "missed_slot_count",
            "proposed_slot_count",
            "missed_slot_signal_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_whole_decimal(field_name, getattr(self, field_name)),
            )
        if self.expected_slot_count <= ZERO:
            raise ValueError("expected_slot_count must be positive")
        for field_name in (
            "missed_slot_rate",
            "attestation_participation_rate",
            "missed_slot_risk_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio(field_name, getattr(self, field_name)),
            )
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        _require_member("row_status", self.row_status, ROW_STATUSES)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, ROW_REASON_CODES),
        )
        _validate_row(self)
        _require_hard_flags("row", self)


@dataclass(frozen=True)
class MarketResearchCryptoStakingValidatorMissedSlotsReasonCodeCount(_NoSubclass):
    reason_code: str
    count: Decimal
    row_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            MarketResearchCryptoStakingValidatorMissedSlotsReasonCodeCount,
            "reason_code_count",
        )
        _require_member("reason_code", self.reason_code, REPORT_REASON_CODES)
        object.__setattr__(
            self,
            "count",
            _require_positive_whole_decimal("reason_code_count count", self.count),
        )
        object.__setattr__(self, "row_ratio", _require_ratio("row_ratio", self.row_ratio))
        _require_hard_flags("reason_code_count", self)


@dataclass(frozen=True)
class MarketResearchCryptoStakingValidatorMissedSlotsDigestReport(_NoSubclass):
    generated_at: datetime
    config_version: str
    input_count: Decimal
    row_count: Decimal
    blocked_count: Decimal
    watch_count: Decimal
    pass_count: Decimal
    high_missed_slot_count: Decimal
    high_missed_slot_rate_count: Decimal
    low_attestation_count: Decimal
    stale_observation_count: Decimal
    total_missed_slot_count: Decimal
    max_missed_slot_rate: Decimal
    average_missed_slot_rate: Decimal
    max_missed_slot_risk_score: Decimal
    digest_status: str
    recommended_next_step: str
    rows: tuple[MarketResearchCryptoStakingValidatorMissedSlotsDigestRow, ...]
    reason_code_counts: tuple[
        MarketResearchCryptoStakingValidatorMissedSlotsReasonCodeCount,
        ...,
    ]
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, MarketResearchCryptoStakingValidatorMissedSlotsDigestReport, "report")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_MARKET_RESEARCH_CRYPTO_STAKING_VALIDATOR_MISSED_SLOTS_DIGEST_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "input_count",
            "row_count",
            "blocked_count",
            "watch_count",
            "pass_count",
            "high_missed_slot_count",
            "high_missed_slot_rate_count",
            "low_attestation_count",
            "stale_observation_count",
            "total_missed_slot_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_whole_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "max_missed_slot_rate",
            "average_missed_slot_rate",
            "max_missed_slot_risk_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio(field_name, getattr(self, field_name)),
            )
        _require_member("digest_status", self.digest_status, DIGEST_STATUSES)
        _require_canonical_string("recommended_next_step", self.recommended_next_step)
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(
                "reason_codes",
                self.reason_codes,
                REPORT_REASON_CODES,
            ),
        )
        _validate_report(self)
        _require_hard_flags("report", self)


_PUBLIC_DATACLASS_TYPES = (
    MarketResearchCryptoStakingValidatorMissedSlotsDigestConfig,
    MarketResearchCryptoStakingValidatorMissedSlotsObservation,
    MarketResearchCryptoStakingValidatorMissedSlotsDigestRow,
    MarketResearchCryptoStakingValidatorMissedSlotsReasonCodeCount,
    MarketResearchCryptoStakingValidatorMissedSlotsDigestReport,
)


def build_market_research_crypto_staking_validator_missed_slots_digest(
    observations: tuple[MarketResearchCryptoStakingValidatorMissedSlotsObservation, ...],
    *,
    config: MarketResearchCryptoStakingValidatorMissedSlotsDigestConfig,
    generated_at: datetime,
) -> MarketResearchCryptoStakingValidatorMissedSlotsDigestReport:
    if type(config) is not MarketResearchCryptoStakingValidatorMissedSlotsDigestConfig:
        raise ValueError(
            "config must be exactly "
            "MarketResearchCryptoStakingValidatorMissedSlotsDigestConfig",
        )
    _require_hard_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    normalized = _normalize_observations(observations)
    rows = tuple(
        sorted(
            (
                _row_from_observation(
                    observation,
                    config=config,
                    generated_at=generated_at_utc,
                )
                for observation in normalized
            ),
            key=_row_sort_value,
        ),
    )
    reason_codes = _report_reason_codes(rows)
    digest_status = _digest_status(rows)
    return MarketResearchCryptoStakingValidatorMissedSlotsDigestReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        input_count=_count_decimal(len(normalized)),
        row_count=_count_decimal(len(rows)),
        blocked_count=_status_count(rows, BLOCKED_STATUS),
        watch_count=_status_count(rows, WATCH_STATUS),
        pass_count=_status_count(rows, PASS_STATUS),
        high_missed_slot_count=_reason_count(rows, HIGH_COUNT_REASON),
        high_missed_slot_rate_count=_reason_count(rows, HIGH_RATE_REASON),
        low_attestation_count=_reason_count(rows, LOW_ATTESTATION_REASON),
        stale_observation_count=_reason_count(rows, STALE_OBSERVATION_REASON),
        total_missed_slot_count=_sum_decimal(row.missed_slot_count for row in rows),
        max_missed_slot_rate=_max_row_decimal(rows, "missed_slot_rate"),
        average_missed_slot_rate=_ratio(
            _sum_decimal(row.missed_slot_rate for row in rows),
            _count_decimal(len(rows)),
        ),
        max_missed_slot_risk_score=_max_row_decimal(rows, "missed_slot_risk_score"),
        digest_status=digest_status,
        recommended_next_step=NEXT_STEP_BY_STATUS[digest_status],
        rows=rows,
        reason_code_counts=_reason_code_counts(reason_codes, rows),
        reason_codes=reason_codes,
    )


def market_research_crypto_staking_validator_missed_slots_digest_payload(
    report: MarketResearchCryptoStakingValidatorMissedSlotsDigestReport,
) -> dict[str, Any]:
    if type(report) is not MarketResearchCryptoStakingValidatorMissedSlotsDigestReport:
        raise ValueError(
            "report must be exactly "
            "MarketResearchCryptoStakingValidatorMissedSlotsDigestReport",
        )
    _require_hard_flags("report", report)
    ready = _payload_value(report)
    if type(ready) is not dict:
        raise ValueError("report must reduce to a JSON object")
    return ready


def _row_from_observation(
    observation: MarketResearchCryptoStakingValidatorMissedSlotsObservation,
    *,
    config: MarketResearchCryptoStakingValidatorMissedSlotsDigestConfig,
    generated_at: datetime,
) -> MarketResearchCryptoStakingValidatorMissedSlotsDigestRow:
    missed_slot_rate = _ratio(observation.missed_slot_count, observation.expected_slot_count)
    observation_lag_minutes = _minutes_between(observation.observed_at, generated_at)
    signal_reasons = _signal_reason_codes(
        observation,
        missed_slot_rate=missed_slot_rate,
        observation_lag_minutes=observation_lag_minutes,
        config=config,
    )
    signal_count = _count_decimal(len(signal_reasons))
    row_status = _row_status(
        observation,
        missed_slot_rate=missed_slot_rate,
        signal_count=signal_count,
        config=config,
    )
    return MarketResearchCryptoStakingValidatorMissedSlotsDigestRow(
        source_id=observation.source_id,
        validator_id=observation.validator_id,
        network=observation.network,
        epoch_id=observation.epoch_id,
        slot_window_start=observation.slot_window_start,
        slot_window_end=observation.slot_window_end,
        window_duration_minutes=_minutes_between(
            observation.slot_window_start,
            observation.slot_window_end,
        ),
        expected_slot_count=observation.expected_slot_count,
        missed_slot_count=observation.missed_slot_count,
        proposed_slot_count=observation.proposed_slot_count,
        missed_slot_rate=missed_slot_rate,
        attestation_participation_rate=observation.attestation_participation_rate,
        observed_at=observation.observed_at,
        observation_lag_minutes=observation_lag_minutes,
        missed_slot_signal_count=signal_count,
        missed_slot_risk_score=_ratio(signal_count, SIGNAL_DENOMINATOR),
        row_status=row_status,
        reason_codes=_row_reason_codes(signal_reasons, row_status),
    )


def _signal_reason_codes(
    observation: MarketResearchCryptoStakingValidatorMissedSlotsObservation,
    *,
    missed_slot_rate: Decimal,
    observation_lag_minutes: Decimal,
    config: MarketResearchCryptoStakingValidatorMissedSlotsDigestConfig,
) -> tuple[str, ...]:
    reasons: list[str] = []
    if observation.missed_slot_count >= config.watch_missed_slot_count:
        reasons.append(HIGH_COUNT_REASON)
    if missed_slot_rate >= config.watch_missed_slot_rate:
        reasons.append(HIGH_RATE_REASON)
    if observation.attestation_participation_rate < config.min_attestation_participation_rate:
        reasons.append(LOW_ATTESTATION_REASON)
    if observation_lag_minutes > config.stale_observation_minutes:
        reasons.append(STALE_OBSERVATION_REASON)
    if not reasons:
        return ()
    return _normalize_reason_codes("reason_codes", tuple(reasons), ROW_REASON_CODES)


def _row_status(
    observation: MarketResearchCryptoStakingValidatorMissedSlotsObservation,
    *,
    missed_slot_rate: Decimal,
    signal_count: Decimal,
    config: MarketResearchCryptoStakingValidatorMissedSlotsDigestConfig,
) -> str:
    if (
        observation.missed_slot_count >= config.blocked_missed_slot_count
        or missed_slot_rate >= config.blocked_missed_slot_rate
        or signal_count >= config.blocked_signal_count
    ):
        return BLOCKED_STATUS
    if signal_count >= config.watch_signal_count:
        return WATCH_STATUS
    return PASS_STATUS


def _row_reason_codes(signal_reasons: tuple[str, ...], row_status: str) -> tuple[str, ...]:
    reasons = list(signal_reasons)
    if row_status == BLOCKED_STATUS:
        reasons.append(ROW_BLOCKED_REASON)
    elif row_status == WATCH_STATUS:
        reasons.append(ROW_WATCH_REASON)
    else:
        reasons.append(ROW_CLEAR_REASON)
    return _normalize_reason_codes("reason_codes", tuple(reasons), ROW_REASON_CODES)


def _digest_status(
    rows: tuple[MarketResearchCryptoStakingValidatorMissedSlotsDigestRow, ...],
) -> str:
    if not rows:
        return BLOCKED_STATUS
    if any(row.row_status == BLOCKED_STATUS for row in rows):
        return BLOCKED_STATUS
    if any(row.row_status == WATCH_STATUS for row in rows):
        return WATCH_STATUS
    return PASS_STATUS


def _report_reason_codes(
    rows: tuple[MarketResearchCryptoStakingValidatorMissedSlotsDigestRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return (DIGEST_EMPTY_REASON,)
    reasons: list[str] = []
    if any(row.row_status == BLOCKED_STATUS for row in rows):
        reasons.append(DIGEST_BLOCKED_REASON)
    if not any(row.row_status == BLOCKED_STATUS for row in rows) and any(
        row.row_status == WATCH_STATUS for row in rows
    ):
        reasons.append(DIGEST_WATCH_REASON)
    if _reason_count(rows, HIGH_COUNT_REASON) > ZERO:
        reasons.append(DIGEST_HIGH_COUNT_REASON)
    if _reason_count(rows, HIGH_RATE_REASON) > ZERO:
        reasons.append(DIGEST_HIGH_RATE_REASON)
    if _reason_count(rows, LOW_ATTESTATION_REASON) > ZERO:
        reasons.append(DIGEST_LOW_ATTESTATION_REASON)
    if _reason_count(rows, STALE_OBSERVATION_REASON) > ZERO:
        reasons.append(DIGEST_STALE_OBSERVATION_REASON)
    if not reasons:
        reasons.append(DIGEST_CLEAR_REASON)
    return tuple(reason for reason in REPORT_REASON_CODES if reason in reasons)


def _reason_code_counts(
    reason_codes: tuple[str, ...],
    rows: tuple[MarketResearchCryptoStakingValidatorMissedSlotsDigestRow, ...],
) -> tuple[MarketResearchCryptoStakingValidatorMissedSlotsReasonCodeCount, ...]:
    row_count = _count_decimal(len(rows))
    if reason_codes == (DIGEST_EMPTY_REASON,):
        return (
            MarketResearchCryptoStakingValidatorMissedSlotsReasonCodeCount(
                reason_code=DIGEST_EMPTY_REASON,
                count=ONE,
                row_ratio=ZERO,
            ),
        )
    return tuple(
        MarketResearchCryptoStakingValidatorMissedSlotsReasonCodeCount(
            reason_code=reason_code,
            count=_report_reason_row_count(reason_code, rows),
            row_ratio=_ratio(_report_reason_row_count(reason_code, rows), row_count),
        )
        for reason_code in reason_codes
    )


def _report_reason_row_count(
    reason_code: str,
    rows: tuple[MarketResearchCryptoStakingValidatorMissedSlotsDigestRow, ...],
) -> Decimal:
    return _reason_count(rows, REPORT_TO_ROW_REASON[reason_code])


def _validate_observation(
    observation: MarketResearchCryptoStakingValidatorMissedSlotsObservation,
) -> None:
    if (
        observation.proposed_slot_count
        != observation.expected_slot_count - observation.missed_slot_count
    ):
        raise ValueError("proposed_slot_count must match expected less missed")
    if observation.missed_slot_count > observation.expected_slot_count:
        raise ValueError("missed_slot_count must not exceed expected_slot_count")


def _validate_row(row: MarketResearchCryptoStakingValidatorMissedSlotsDigestRow) -> None:
    if row.proposed_slot_count != row.expected_slot_count - row.missed_slot_count:
        raise ValueError("proposed_slot_count must match expected less missed")
    if row.missed_slot_count > row.expected_slot_count:
        raise ValueError("missed_slot_count must not exceed expected_slot_count")
    if row.window_duration_minutes != _minutes_between(
        row.slot_window_start,
        row.slot_window_end,
    ):
        raise ValueError("window_duration_minutes must match slot window")
    if row.missed_slot_rate != _ratio(row.missed_slot_count, row.expected_slot_count):
        raise ValueError("missed_slot_rate must match missed slots")
    signal_reasons = tuple(
        reason
        for reason in row.reason_codes
        if reason not in (ROW_BLOCKED_REASON, ROW_WATCH_REASON, ROW_CLEAR_REASON)
    )
    if row.missed_slot_signal_count != _count_decimal(len(signal_reasons)):
        raise ValueError("missed_slot_signal_count must match reason_codes")
    if row.missed_slot_risk_score != _ratio(
        row.missed_slot_signal_count,
        SIGNAL_DENOMINATOR,
    ):
        raise ValueError("missed_slot_risk_score must match missed_slot_signal_count")
    if row.row_status != _status_from_reason_codes(row.reason_codes):
        raise ValueError("row_status must match reason_codes")


def _status_from_reason_codes(reason_codes: tuple[str, ...]) -> str:
    if reason_codes == (ROW_CLEAR_REASON,):
        return PASS_STATUS
    if ROW_BLOCKED_REASON in reason_codes and ROW_WATCH_REASON not in reason_codes:
        return BLOCKED_STATUS
    if ROW_WATCH_REASON in reason_codes and ROW_BLOCKED_REASON not in reason_codes:
        return WATCH_STATUS
    raise ValueError("reason_codes must match row_status")


def _validate_report(
    report: MarketResearchCryptoStakingValidatorMissedSlotsDigestReport,
) -> None:
    if report.input_count != _count_decimal(len(report.rows)):
        raise ValueError("input_count must match rows")
    if report.row_count != _count_decimal(len(report.rows)):
        raise ValueError("row_count must match rows")
    if report.blocked_count != _status_count(report.rows, BLOCKED_STATUS):
        raise ValueError("blocked_count must match rows")
    if report.watch_count != _status_count(report.rows, WATCH_STATUS):
        raise ValueError("watch_count must match rows")
    if report.pass_count != _status_count(report.rows, PASS_STATUS):
        raise ValueError("pass_count must match rows")
    if report.blocked_count + report.watch_count + report.pass_count != report.row_count:
        raise ValueError("status counts must match rows")
    if report.high_missed_slot_count != _reason_count(report.rows, HIGH_COUNT_REASON):
        raise ValueError("high_missed_slot_count must match rows")
    if report.high_missed_slot_rate_count != _reason_count(report.rows, HIGH_RATE_REASON):
        raise ValueError("high_missed_slot_rate_count must match rows")
    if report.low_attestation_count != _reason_count(report.rows, LOW_ATTESTATION_REASON):
        raise ValueError("low_attestation_count must match rows")
    if report.stale_observation_count != _reason_count(report.rows, STALE_OBSERVATION_REASON):
        raise ValueError("stale_observation_count must match rows")
    if report.total_missed_slot_count != _sum_decimal(
        row.missed_slot_count for row in report.rows
    ):
        raise ValueError("total_missed_slot_count must match rows")
    if report.max_missed_slot_rate != _max_row_decimal(report.rows, "missed_slot_rate"):
        raise ValueError("max_missed_slot_rate must match rows")
    if report.average_missed_slot_rate != _ratio(
        _sum_decimal(row.missed_slot_rate for row in report.rows),
        report.row_count,
    ):
        raise ValueError("average_missed_slot_rate must match rows")
    if report.max_missed_slot_risk_score != _max_row_decimal(
        report.rows,
        "missed_slot_risk_score",
    ):
        raise ValueError("max_missed_slot_risk_score must match rows")
    expected_reason_codes = _report_reason_codes(report.rows)
    if report.reason_codes != expected_reason_codes:
        raise ValueError("reason_codes must match rows")
    if report.reason_code_counts != _reason_code_counts(expected_reason_codes, report.rows):
        raise ValueError("reason_code_counts must summarize rows")
    if report.digest_status != _digest_status(report.rows):
        raise ValueError("digest_status must match rows")
    if report.recommended_next_step != NEXT_STEP_BY_STATUS[report.digest_status]:
        raise ValueError("recommended_next_step must match digest_status")


def _normalize_observations(
    observations: tuple[MarketResearchCryptoStakingValidatorMissedSlotsObservation, ...],
) -> tuple[MarketResearchCryptoStakingValidatorMissedSlotsObservation, ...]:
    if type(observations) is not tuple:
        raise ValueError("observations must be a tuple")
    seen_source_ids: set[str] = set()
    for observation in observations:
        if type(observation) is not MarketResearchCryptoStakingValidatorMissedSlotsObservation:
            raise ValueError(
                "observations must contain "
                "MarketResearchCryptoStakingValidatorMissedSlotsObservation",
            )
        _require_hard_flags("observation", observation)
        if observation.source_id in seen_source_ids:
            raise ValueError("observations must not contain duplicate source_id values")
        seen_source_ids.add(observation.source_id)
    return observations


def _normalize_rows(
    rows: object,
) -> tuple[MarketResearchCryptoStakingValidatorMissedSlotsDigestRow, ...]:
    if type(rows) is not tuple:
        raise ValueError("rows must be a tuple")
    seen_source_ids: set[str] = set()
    for row in rows:
        if type(row) is not MarketResearchCryptoStakingValidatorMissedSlotsDigestRow:
            raise ValueError(
                "rows must contain MarketResearchCryptoStakingValidatorMissedSlotsDigestRow",
            )
        _require_hard_flags("row", row)
        _validate_row(row)
        if row.source_id in seen_source_ids:
            raise ValueError("rows must not contain duplicate source_id values")
        seen_source_ids.add(row.source_id)
    return tuple(sorted(rows, key=_row_sort_value))


def _normalize_reason_code_counts(
    values: object,
) -> tuple[MarketResearchCryptoStakingValidatorMissedSlotsReasonCodeCount, ...]:
    if type(values) is not tuple:
        raise ValueError("reason_code_counts must be a tuple")
    seen_reason_codes: set[str] = set()
    for value in values:
        if type(value) is not MarketResearchCryptoStakingValidatorMissedSlotsReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "MarketResearchCryptoStakingValidatorMissedSlotsReasonCodeCount",
            )
        _require_hard_flags("reason_code_count", value)
        if value.reason_code in seen_reason_codes:
            raise ValueError("reason_code_counts must contain unique reason codes")
        seen_reason_codes.add(value.reason_code)
    return tuple(
        sorted(values, key=lambda value: REPORT_REASON_CODES.index(value.reason_code)),
    )


def _normalize_open_reason_codes(field_name: str, values: object) -> tuple[str, ...]:
    if type(values) is not tuple:
        raise ValueError(f"{field_name} must be a tuple")
    normalized: list[str] = []
    for value in values:
        _require_canonical_string("reason_code", value)
        if value not in normalized:
            normalized.append(value)
    return tuple(sorted(normalized))


def _normalize_reason_codes(
    field_name: str,
    values: object,
    allowed_values: tuple[str, ...],
) -> tuple[str, ...]:
    if type(values) is not tuple:
        raise ValueError(f"{field_name} must be a tuple")
    if not values:
        raise ValueError(f"{field_name} must not be empty")
    seen_reason_codes: set[str] = set()
    for value in values:
        _require_member("reason_code", value, allowed_values)
        if value in seen_reason_codes:
            raise ValueError(f"{field_name} must contain unique reason codes")
        seen_reason_codes.add(value)
    if tuple(reason for reason in allowed_values if reason in values) != values:
        raise ValueError(f"{field_name} must be deterministic")
    if allowed_values is ROW_REASON_CODES and ROW_CLEAR_REASON in values and len(values) != 1:
        raise ValueError(f"{field_name} must match row_status")
    if allowed_values is REPORT_REASON_CODES:
        if DIGEST_EMPTY_REASON in values and len(values) != 1:
            raise ValueError(f"{field_name} must match digest_status")
        if DIGEST_CLEAR_REASON in values and len(values) != 1:
            raise ValueError(f"{field_name} must match digest_status")
    return values


def _row_sort_value(
    row: MarketResearchCryptoStakingValidatorMissedSlotsDigestRow,
) -> tuple[Decimal, Decimal, str, str, str]:
    return (
        STATUS_RANK[row.row_status],
        -row.missed_slot_risk_score,
        row.validator_id,
        row.epoch_id,
        row.source_id,
    )


def _status_count(
    rows: tuple[MarketResearchCryptoStakingValidatorMissedSlotsDigestRow, ...],
    status: str,
) -> Decimal:
    return _count_decimal(sum(1 for row in rows if row.row_status == status))


def _reason_count(
    rows: tuple[MarketResearchCryptoStakingValidatorMissedSlotsDigestRow, ...],
    reason_code: str,
) -> Decimal:
    return _count_decimal(sum(1 for row in rows if reason_code in row.reason_codes))


def _max_row_decimal(
    rows: tuple[MarketResearchCryptoStakingValidatorMissedSlotsDigestRow, ...],
    field_name: str,
) -> Decimal:
    return max((getattr(row, field_name) for row in rows), default=ZERO).quantize(QUANTUM)


def _sum_decimal(values: object) -> Decimal:
    total = ZERO
    for value in values:
        total += value
    return total.quantize(QUANTUM)


def _count_decimal(value: int) -> Decimal:
    return Decimal(value).quantize(QUANTUM)


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return (numerator / denominator).quantize(QUANTUM)


def _minutes_between(start: datetime, end: datetime) -> Decimal:
    delta = end - start
    total_microseconds = (
        Decimal(delta.days) * Decimal("86400000000")
        + Decimal(delta.seconds) * Decimal("1000000")
        + Decimal(delta.microseconds)
    )
    with localcontext(DECIMAL_CONTEXT):
        return (total_microseconds / MICROSECONDS_PER_MINUTE).quantize(QUANTUM)


def _payload_value(value: object, field_name: str = "value") -> object:
    if _is_public_dataclass_instance(value):
        _revalidate_public_dataclass_for_payload(value)
        return {
            field.name: _payload_value(getattr(value, field.name), field.name)
            for field in fields(value)
        }
    if type(value) is datetime:
        return _payload_datetime(field_name, value)
    if isinstance(value, datetime):
        raise ValueError(f"{field_name} must be exactly datetime")
    if type(value) is Decimal:
        _require_six_decimal(field_name, value)
        return format(value, "f")
    if type(value) is tuple:
        return [_payload_value(item, field_name) for item in value]
    if type(value) in (list, dict, set):
        raise ValueError(f"{field_name} must remain constructor-normalized")
    if type(value) in (str, bool) or value is None:
        return value
    if type(value) is int:
        raise ValueError(f"{field_name} must use Decimal values")
    if isinstance(value, float):
        raise ValueError(f"{field_name} must not be a float")
    raise ValueError(f"{field_name} must be safe for payload serialization")


def _revalidate_public_dataclass_for_payload(value: object) -> None:
    _require_six_decimal_payload_values(value)
    if type(value) is MarketResearchCryptoStakingValidatorMissedSlotsDigestReport:
        for row in value.rows:
            _revalidate_public_dataclass_for_payload(row)
        for count in value.reason_code_counts:
            _revalidate_public_dataclass_for_payload(count)
        MarketResearchCryptoStakingValidatorMissedSlotsDigestReport(
            **_dataclass_field_values(value),
        )
        return
    if type(value) is MarketResearchCryptoStakingValidatorMissedSlotsDigestRow:
        MarketResearchCryptoStakingValidatorMissedSlotsDigestRow(
            **_dataclass_field_values(value),
        )
        return
    if type(value) is MarketResearchCryptoStakingValidatorMissedSlotsReasonCodeCount:
        MarketResearchCryptoStakingValidatorMissedSlotsReasonCodeCount(
            **_dataclass_field_values(value),
        )
        return
    if type(value) is MarketResearchCryptoStakingValidatorMissedSlotsObservation:
        MarketResearchCryptoStakingValidatorMissedSlotsObservation(
            **_dataclass_field_values(value),
        )
        return
    if type(value) is MarketResearchCryptoStakingValidatorMissedSlotsDigestConfig:
        MarketResearchCryptoStakingValidatorMissedSlotsDigestConfig(
            **_dataclass_field_values(value),
        )
        return
    raise ValueError(
        "payload value must be a public crypto staking missed slots dataclass",
    )


def _is_public_dataclass_instance(value: object) -> bool:
    return type(value) in _PUBLIC_DATACLASS_TYPES


def _dataclass_field_values(value: object) -> dict[str, object]:
    return {field.name: getattr(value, field.name) for field in fields(value)}


def _require_six_decimal_payload_values(value: object) -> None:
    if type(value) is Decimal:
        _require_six_decimal("value", value)
        return
    if _is_public_dataclass_instance(value):
        for field in fields(value):
            _require_six_decimal_payload_field(field.name, getattr(value, field.name))
        return
    if type(value) is tuple:
        for item in value:
            _require_six_decimal_payload_values(item)
        return
    if type(value) in (list, dict, set):
        raise ValueError("payload value must remain constructor-normalized")
    if type(value) in (str, bool, datetime) or value is None:
        return
    if type(value) is int:
        raise ValueError("value must use Decimal values")
    if isinstance(value, float):
        raise ValueError("value must not be a float")
    raise ValueError("payload value must be a public crypto staking missed slots dataclass")


def _require_six_decimal_payload_field(field_name: str, value: object) -> None:
    if type(value) is Decimal:
        _require_six_decimal(field_name, value)
        return
    if _is_public_dataclass_instance(value):
        _require_six_decimal_payload_values(value)
        return
    if type(value) is tuple:
        for item in value:
            _require_six_decimal_payload_field(field_name, item)
        return
    if type(value) in (list, dict, set):
        raise ValueError(f"{field_name} must remain constructor-normalized")
    if type(value) in (str, bool, datetime) or value is None:
        return
    if type(value) is int:
        raise ValueError(f"{field_name} must use Decimal values")
    if isinstance(value, float):
        raise ValueError(f"{field_name} must not be a float")
    raise ValueError(f"{field_name} must be safe for payload serialization")


def _payload_datetime(field_name: str, value: datetime) -> str:
    if value.tzinfo is not UTC or value.utcoffset() != ZERO_TIME_OFFSET:
        raise ValueError(f"{field_name} must be UTC")
    return value.isoformat()


def _require_six_decimal(field_name: str, value: Decimal) -> None:
    try:
        quantized = value.quantize(QUANTUM)
    except InvalidOperation as exc:
        raise ValueError(f"{field_name} must be six-decimal") from exc
    if value != quantized or value.as_tuple().exponent != QUANTUM.as_tuple().exponent:
        raise ValueError(f"{field_name} must be six-decimal")


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value or not _CANONICAL_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a canonical nonblank string")


def _require_member(field_name: str, value: object, allowed_values: tuple[str, ...]) -> str:
    _require_canonical_string(field_name, value)
    if value not in allowed_values:
        raise ValueError(f"{field_name} must contain a supported value")
    return value


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return value.quantize(QUANTUM)


def _require_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return decimal_value


def _require_positive_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return decimal_value


def _require_nonnegative_whole_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_nonnegative_decimal(field_name, value)
    if decimal_value != decimal_value.to_integral_value():
        raise ValueError(f"{field_name} must be whole")
    return decimal_value


def _require_positive_whole_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_nonnegative_whole_decimal(field_name, value)
    if decimal_value <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return decimal_value


def _require_ratio(field_name: str, value: object) -> Decimal:
    decimal_value = _require_nonnegative_decimal(field_name, value)
    if decimal_value > ONE:
        raise ValueError(f"{field_name} must be no greater than one")
    return decimal_value


def _require_positive_ratio(field_name: str, value: object) -> Decimal:
    decimal_value = _require_ratio(field_name, value)
    if decimal_value <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return decimal_value


def _require_hard_flags(field_name: str, value: object) -> None:
    for flag_name in PHASE_FLAG_FIELDS:
        if getattr(value, flag_name, None) is not True:
            raise ValueError(f"{field_name} {flag_name} must be True")


def _require_exact_type(value: object, expected_type: type[object], label: str) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{label} must be exactly {expected_type.__name__}")


ZERO_TIME_OFFSET = UTC.utcoffset(datetime(2026, 1, 1, tzinfo=UTC))
