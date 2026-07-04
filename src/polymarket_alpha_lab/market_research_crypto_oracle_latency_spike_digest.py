"""Pure Phase 1 crypto oracle latency spike research reducer."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal, ROUND_HALF_EVEN
from types import MappingProxyType
from typing import Any


DEFAULT_MARKET_RESEARCH_CRYPTO_ORACLE_LATENCY_SPIKE_DIGEST_CONFIG_VERSION = (
    "market-research-crypto-oracle-latency-spike-digest-v0"
)

STATUS_READY = "ready"
STATUS_WATCH = "watch"
STATUS_BLOCKED = "blocked"
ORACLE_LATENCY_SPIKE_DIGEST_STATUSES = (STATUS_READY, STATUS_WATCH, STATUS_BLOCKED)

READY_REASON = "market_research_crypto_oracle_latency_spike_digest_ready"
NO_INPUTS_REASON = "market_research_crypto_oracle_latency_spike_digest_no_inputs"
LATENCY_SPIKE_REASON = (
    "market_research_crypto_oracle_latency_spike_digest_latency_spike"
)
P95_LATENCY_SPIKE_REASON = (
    "market_research_crypto_oracle_latency_spike_digest_p95_latency_spike"
)
PUBLISH_LAG_REASON = "market_research_crypto_oracle_latency_spike_digest_publish_lag"
CONFIRM_LAG_REASON = "market_research_crypto_oracle_latency_spike_digest_confirm_lag"
ROUND_GAP_REASON = "market_research_crypto_oracle_latency_spike_digest_round_gap"
SOURCE_DIVERSITY_GAP_REASON = (
    "market_research_crypto_oracle_latency_spike_digest_source_diversity_gap"
)
STALE_OBSERVATION_REASON = (
    "market_research_crypto_oracle_latency_spike_digest_stale_observation"
)
CONFIDENCE_GAP_REASON = (
    "market_research_crypto_oracle_latency_spike_digest_confidence_gap"
)

REASON_CODE_SEQUENCE = (
    LATENCY_SPIKE_REASON,
    P95_LATENCY_SPIKE_REASON,
    PUBLISH_LAG_REASON,
    CONFIRM_LAG_REASON,
    ROUND_GAP_REASON,
    SOURCE_DIVERSITY_GAP_REASON,
    STALE_OBSERVATION_REASON,
    CONFIDENCE_GAP_REASON,
    READY_REASON,
    NO_INPUTS_REASON,
)
ROW_REASON_CODE_SEQUENCE = (
    LATENCY_SPIKE_REASON,
    P95_LATENCY_SPIKE_REASON,
    PUBLISH_LAG_REASON,
    CONFIRM_LAG_REASON,
    ROUND_GAP_REASON,
    SOURCE_DIVERSITY_GAP_REASON,
    STALE_OBSERVATION_REASON,
    CONFIDENCE_GAP_REASON,
    READY_REASON,
)

QUANT = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
MICROSECONDS_PER_SECOND = Decimal("1000000")


def _join_parts(*parts: str) -> str:
    return "".join(parts)


UNSAFE_TEXT_FRAGMENTS = frozenset(
    (
        _join_parts("mar", "ket", "_", "slug"),
        _join_parts("ques", "tion"),
        _join_parts("wa", "llet"),
        _join_parts("or", "der"),
        _join_parts("to", "ken"),
        _join_parts("sec", "ret"),
        _join_parts("pri", "vate"),
        _join_parts("0", "x"),
    ),
)

__all__ = (
    "DEFAULT_MARKET_RESEARCH_CRYPTO_ORACLE_LATENCY_SPIKE_DIGEST_CONFIG_VERSION",
    "MarketResearchCryptoOracleLatencySpikeDigestConfig",
    "MarketResearchCryptoOracleLatencySpikeDigestReasonCodeCount",
    "MarketResearchCryptoOracleLatencySpikeDigestReport",
    "MarketResearchCryptoOracleLatencySpikeDigestRow",
    "MarketResearchCryptoOracleLatencySpikeObservation",
    "build_market_research_crypto_oracle_latency_spike_digest",
    "market_research_crypto_oracle_latency_spike_digest_payload",
)


@dataclass(frozen=True)
class MarketResearchCryptoOracleLatencySpikeDigestConfig:
    config_version: str = (
        DEFAULT_MARKET_RESEARCH_CRYPTO_ORACLE_LATENCY_SPIKE_DIGEST_CONFIG_VERSION
    )
    max_observation_age_seconds: Decimal = Decimal("1800.000000")
    watch_latency_spike_ratio: Decimal = Decimal("0.500000")
    blocked_latency_spike_ratio: Decimal = Decimal("1.500000")
    max_publish_lag_seconds: Decimal = Decimal("300.000000")
    max_confirm_lag_seconds: Decimal = Decimal("600.000000")
    max_round_gap_ratio: Decimal = Decimal("0.250000")
    min_source_count: Decimal = Decimal("3.000000")
    min_confidence: Decimal = Decimal("0.700000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketResearchCryptoOracleLatencySpikeDigestConfig:
            raise TypeError(
                "MarketResearchCryptoOracleLatencySpikeDigestConfig "
                "does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not MarketResearchCryptoOracleLatencySpikeDigestConfig:
            raise ValueError(
                "config must be exactly MarketResearchCryptoOracleLatencySpikeDigestConfig",
            )
        _require_canonical_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_MARKET_RESEARCH_CRYPTO_ORACLE_LATENCY_SPIKE_DIGEST_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the configured version")
        for field_name in (
            "max_observation_age_seconds",
            "watch_latency_spike_ratio",
            "blocked_latency_spike_ratio",
            "max_publish_lag_seconds",
            "max_confirm_lag_seconds",
            "min_source_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_positive_count_decimal(field_name, getattr(self, field_name)),
            )
        if self.watch_latency_spike_ratio > self.blocked_latency_spike_ratio:
            raise ValueError("watch_latency_spike_ratio must not exceed blocked threshold")
        for field_name in ("max_round_gap_ratio", "min_confidence"):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class MarketResearchCryptoOracleLatencySpikeObservation:
    condition_id: str
    oracle_key: str
    asset_symbol: str
    observed_at: datetime
    published_at: datetime
    confirmed_at: datetime
    observed_latency_seconds: Decimal
    baseline_latency_seconds: Decimal
    p95_latency_seconds: Decimal
    baseline_p95_latency_seconds: Decimal
    round_gap_ratio: Decimal
    source_count: Decimal
    confidence: Decimal
    source_config_version: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketResearchCryptoOracleLatencySpikeObservation:
            raise TypeError(
                "MarketResearchCryptoOracleLatencySpikeObservation "
                "does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not MarketResearchCryptoOracleLatencySpikeObservation:
            raise ValueError(
                "observation must be exactly "
                "MarketResearchCryptoOracleLatencySpikeObservation",
            )
        for field_name in (
            "condition_id",
            "oracle_key",
            "asset_symbol",
            "source_config_version",
        ):
            _require_public_string(field_name, getattr(self, field_name))
        for field_name in ("observed_at", "published_at", "confirmed_at"):
            object.__setattr__(self, field_name, _as_utc(field_name, getattr(self, field_name)))
        for field_name in (
            "observed_latency_seconds",
            "baseline_latency_seconds",
            "p95_latency_seconds",
            "baseline_p95_latency_seconds",
            "source_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_count_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in ("round_gap_ratio", "confidence"):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        _require_hard_flags("observation", self)


@dataclass(frozen=True)
class MarketResearchCryptoOracleLatencySpikeDigestRow:
    condition_id: str
    oracle_key: str
    asset_symbol: str
    digest_status: str
    observed_at: datetime
    published_at: datetime
    confirmed_at: datetime
    observation_age_seconds: Decimal
    publish_lag_seconds: Decimal
    confirm_lag_seconds: Decimal
    observed_latency_seconds: Decimal
    baseline_latency_seconds: Decimal
    latency_spike_ratio: Decimal
    p95_latency_seconds: Decimal
    baseline_p95_latency_seconds: Decimal
    p95_latency_spike_ratio: Decimal
    round_gap_ratio: Decimal
    source_count: Decimal
    confidence: Decimal
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketResearchCryptoOracleLatencySpikeDigestRow:
            raise TypeError(
                "MarketResearchCryptoOracleLatencySpikeDigestRow "
                "does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not MarketResearchCryptoOracleLatencySpikeDigestRow:
            raise ValueError(
                "row must be exactly MarketResearchCryptoOracleLatencySpikeDigestRow",
            )
        for field_name in ("condition_id", "oracle_key", "asset_symbol"):
            _require_public_string(field_name, getattr(self, field_name))
        _require_status("digest_status", self.digest_status)
        for field_name in ("observed_at", "published_at", "confirmed_at"):
            object.__setattr__(self, field_name, _as_utc(field_name, getattr(self, field_name)))
        for field_name in (
            "observation_age_seconds",
            "publish_lag_seconds",
            "confirm_lag_seconds",
            "observed_latency_seconds",
            "baseline_latency_seconds",
            "latency_spike_ratio",
            "p95_latency_seconds",
            "baseline_p95_latency_seconds",
            "p95_latency_spike_ratio",
            "source_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_count_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in ("round_gap_ratio", "confidence"):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes, sequence=ROW_REASON_CODE_SEQUENCE),
        )
        _validate_row(self)
        _require_hard_flags("row", self)


@dataclass(frozen=True)
class MarketResearchCryptoOracleLatencySpikeDigestReasonCodeCount:
    reason_code: str
    count: Decimal
    observation_ratio: Decimal

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketResearchCryptoOracleLatencySpikeDigestReasonCodeCount:
            raise TypeError(
                "MarketResearchCryptoOracleLatencySpikeDigestReasonCodeCount "
                "does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not MarketResearchCryptoOracleLatencySpikeDigestReasonCodeCount:
            raise ValueError(
                "reason code count must be exactly "
                "MarketResearchCryptoOracleLatencySpikeDigestReasonCodeCount",
            )
        _require_reason_code("reason_code", self.reason_code)
        object.__setattr__(
            self,
            "count",
            _require_nonnegative_count_decimal("count", self.count),
        )
        object.__setattr__(
            self,
            "observation_ratio",
            _require_ratio_decimal("observation_ratio", self.observation_ratio),
        )


@dataclass(frozen=True)
class MarketResearchCryptoOracleLatencySpikeDigestReport:
    generated_at: datetime
    config_version: str
    digest_status: str
    recommended_next_step: str
    observation_count: Decimal
    ready_observation_count: Decimal
    watch_observation_count: Decimal
    blocked_observation_count: Decimal
    latency_spike_observation_count: Decimal
    p95_latency_spike_observation_count: Decimal
    publish_lag_observation_count: Decimal
    confirm_lag_observation_count: Decimal
    round_gap_observation_count: Decimal
    source_diversity_gap_observation_count: Decimal
    stale_observation_count: Decimal
    confidence_gap_observation_count: Decimal
    average_latency_spike_ratio: Decimal
    average_p95_latency_spike_ratio: Decimal
    average_round_gap_ratio: Decimal
    average_publish_lag_seconds: Decimal
    average_confirm_lag_seconds: Decimal
    max_observation_age_seconds: Decimal
    max_allowed_observation_age_seconds: Decimal
    watch_latency_spike_ratio: Decimal
    blocked_latency_spike_ratio: Decimal
    max_publish_lag_seconds: Decimal
    max_confirm_lag_seconds: Decimal
    max_round_gap_ratio: Decimal
    min_source_count: Decimal
    min_confidence: Decimal
    rows: tuple[MarketResearchCryptoOracleLatencySpikeDigestRow, ...]
    source_config_versions: tuple[tuple[str, str], ...]
    reason_code_counts: tuple[MarketResearchCryptoOracleLatencySpikeDigestReasonCodeCount, ...]
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketResearchCryptoOracleLatencySpikeDigestReport:
            raise TypeError(
                "MarketResearchCryptoOracleLatencySpikeDigestReport "
                "does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not MarketResearchCryptoOracleLatencySpikeDigestReport:
            raise ValueError(
                "report must be exactly MarketResearchCryptoOracleLatencySpikeDigestReport",
            )
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        _require_status("digest_status", self.digest_status)
        _require_canonical_string("recommended_next_step", self.recommended_next_step)
        for field_name in (
            "observation_count",
            "ready_observation_count",
            "watch_observation_count",
            "blocked_observation_count",
            "latency_spike_observation_count",
            "p95_latency_spike_observation_count",
            "publish_lag_observation_count",
            "confirm_lag_observation_count",
            "round_gap_observation_count",
            "source_diversity_gap_observation_count",
            "stale_observation_count",
            "confidence_gap_observation_count",
            "average_latency_spike_ratio",
            "average_p95_latency_spike_ratio",
            "average_publish_lag_seconds",
            "average_confirm_lag_seconds",
            "max_observation_age_seconds",
            "max_allowed_observation_age_seconds",
            "watch_latency_spike_ratio",
            "blocked_latency_spike_ratio",
            "max_publish_lag_seconds",
            "max_confirm_lag_seconds",
            "min_source_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_count_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "average_round_gap_ratio",
            "max_round_gap_ratio",
            "min_confidence",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        object.__setattr__(
            self,
            "source_config_versions",
            _normalize_source_config_versions(self.source_config_versions),
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


def build_market_research_crypto_oracle_latency_spike_digest(
    observations: Iterable[MarketResearchCryptoOracleLatencySpikeObservation],
    *,
    config: MarketResearchCryptoOracleLatencySpikeDigestConfig | None = None,
    generated_at: datetime,
) -> MarketResearchCryptoOracleLatencySpikeDigestReport:
    cfg = config or MarketResearchCryptoOracleLatencySpikeDigestConfig()
    if type(cfg) is not MarketResearchCryptoOracleLatencySpikeDigestConfig:
        raise ValueError(
            "config must be exactly MarketResearchCryptoOracleLatencySpikeDigestConfig",
        )
    generated_at_utc = _as_utc("generated_at", generated_at)
    normalized_observations = _normalize_observations(observations)
    rows = tuple(
        _row_for_observation(observation, config=cfg, generated_at=generated_at_utc)
        for observation in normalized_observations
    )
    sorted_rows = tuple(
        sorted(
            rows,
            key=lambda row: (
                _row_sort_value(row),
                row.oracle_key,
                row.condition_id,
            ),
        ),
    )
    observation_count = _decimal_count(len(sorted_rows))
    report_status = _report_status(sorted_rows)
    return MarketResearchCryptoOracleLatencySpikeDigestReport(
        generated_at=generated_at_utc,
        config_version=cfg.config_version,
        digest_status=report_status,
        recommended_next_step=_recommended_next_step(report_status),
        observation_count=observation_count,
        ready_observation_count=_status_count(sorted_rows, STATUS_READY),
        watch_observation_count=_status_count(sorted_rows, STATUS_WATCH),
        blocked_observation_count=_status_count(sorted_rows, STATUS_BLOCKED),
        latency_spike_observation_count=_reason_observation_count(
            sorted_rows,
            LATENCY_SPIKE_REASON,
        ),
        p95_latency_spike_observation_count=_reason_observation_count(
            sorted_rows,
            P95_LATENCY_SPIKE_REASON,
        ),
        publish_lag_observation_count=_reason_observation_count(
            sorted_rows,
            PUBLISH_LAG_REASON,
        ),
        confirm_lag_observation_count=_reason_observation_count(
            sorted_rows,
            CONFIRM_LAG_REASON,
        ),
        round_gap_observation_count=_reason_observation_count(
            sorted_rows,
            ROUND_GAP_REASON,
        ),
        source_diversity_gap_observation_count=_reason_observation_count(
            sorted_rows,
            SOURCE_DIVERSITY_GAP_REASON,
        ),
        stale_observation_count=_reason_observation_count(
            sorted_rows,
            STALE_OBSERVATION_REASON,
        ),
        confidence_gap_observation_count=_reason_observation_count(
            sorted_rows,
            CONFIDENCE_GAP_REASON,
        ),
        average_latency_spike_ratio=_ratio(
            _decimal_sum(row.latency_spike_ratio for row in sorted_rows),
            observation_count,
        ),
        average_p95_latency_spike_ratio=_ratio(
            _decimal_sum(row.p95_latency_spike_ratio for row in sorted_rows),
            observation_count,
        ),
        average_round_gap_ratio=_ratio(
            _decimal_sum(row.round_gap_ratio for row in sorted_rows),
            observation_count,
        ),
        average_publish_lag_seconds=_ratio(
            _decimal_sum(row.publish_lag_seconds for row in sorted_rows),
            observation_count,
        ),
        average_confirm_lag_seconds=_ratio(
            _decimal_sum(row.confirm_lag_seconds for row in sorted_rows),
            observation_count,
        ),
        max_observation_age_seconds=max(
            (row.observation_age_seconds for row in sorted_rows),
            default=ZERO,
        ),
        max_allowed_observation_age_seconds=cfg.max_observation_age_seconds,
        watch_latency_spike_ratio=cfg.watch_latency_spike_ratio,
        blocked_latency_spike_ratio=cfg.blocked_latency_spike_ratio,
        max_publish_lag_seconds=cfg.max_publish_lag_seconds,
        max_confirm_lag_seconds=cfg.max_confirm_lag_seconds,
        max_round_gap_ratio=cfg.max_round_gap_ratio,
        min_source_count=cfg.min_source_count,
        min_confidence=cfg.min_confidence,
        rows=sorted_rows,
        source_config_versions=tuple(
            sorted(
                (observation.oracle_key, observation.source_config_version)
                for observation in normalized_observations
            ),
        ),
        reason_code_counts=_reason_code_counts(sorted_rows),
        reason_codes=_summary_reason_codes(sorted_rows),
    )


def market_research_crypto_oracle_latency_spike_digest_payload(
    report: MarketResearchCryptoOracleLatencySpikeDigestReport,
) -> MappingProxyType:
    if type(report) is not MarketResearchCryptoOracleLatencySpikeDigestReport:
        raise ValueError(
            "report must be exactly MarketResearchCryptoOracleLatencySpikeDigestReport",
        )
    return _freeze(_json_ready(report))


def _row_for_observation(
    observation: MarketResearchCryptoOracleLatencySpikeObservation,
    *,
    config: MarketResearchCryptoOracleLatencySpikeDigestConfig,
    generated_at: datetime,
) -> MarketResearchCryptoOracleLatencySpikeDigestRow:
    for field_name in ("observed_at", "published_at", "confirmed_at"):
        if getattr(observation, field_name) > generated_at:
            raise ValueError(f"{field_name} must not be in the future")
    observation_age_seconds = _age_seconds(generated_at, observation.observed_at)
    publish_lag_seconds = _age_seconds(generated_at, observation.published_at)
    confirm_lag_seconds = _age_seconds(generated_at, observation.confirmed_at)
    latency_spike_ratio = _spike_ratio(
        observation.observed_latency_seconds,
        observation.baseline_latency_seconds,
    )
    p95_latency_spike_ratio = _spike_ratio(
        observation.p95_latency_seconds,
        observation.baseline_p95_latency_seconds,
    )
    reason_codes = _row_reason_codes(
        observation=observation,
        config=config,
        observation_age_seconds=observation_age_seconds,
        publish_lag_seconds=publish_lag_seconds,
        confirm_lag_seconds=confirm_lag_seconds,
        latency_spike_ratio=latency_spike_ratio,
        p95_latency_spike_ratio=p95_latency_spike_ratio,
    )
    return MarketResearchCryptoOracleLatencySpikeDigestRow(
        condition_id=observation.condition_id,
        oracle_key=observation.oracle_key,
        asset_symbol=observation.asset_symbol,
        digest_status=_row_status(
            reason_codes=reason_codes,
            latency_spike_ratio=latency_spike_ratio,
            p95_latency_spike_ratio=p95_latency_spike_ratio,
            config=config,
        ),
        observed_at=observation.observed_at,
        published_at=observation.published_at,
        confirmed_at=observation.confirmed_at,
        observation_age_seconds=observation_age_seconds,
        publish_lag_seconds=publish_lag_seconds,
        confirm_lag_seconds=confirm_lag_seconds,
        observed_latency_seconds=observation.observed_latency_seconds,
        baseline_latency_seconds=observation.baseline_latency_seconds,
        latency_spike_ratio=latency_spike_ratio,
        p95_latency_seconds=observation.p95_latency_seconds,
        baseline_p95_latency_seconds=observation.baseline_p95_latency_seconds,
        p95_latency_spike_ratio=p95_latency_spike_ratio,
        round_gap_ratio=observation.round_gap_ratio,
        source_count=observation.source_count,
        confidence=observation.confidence,
        reason_codes=reason_codes,
    )


def _row_reason_codes(
    *,
    observation: MarketResearchCryptoOracleLatencySpikeObservation,
    config: MarketResearchCryptoOracleLatencySpikeDigestConfig,
    observation_age_seconds: Decimal,
    publish_lag_seconds: Decimal,
    confirm_lag_seconds: Decimal,
    latency_spike_ratio: Decimal,
    p95_latency_spike_ratio: Decimal,
) -> tuple[str, ...]:
    reasons: list[str] = []
    if latency_spike_ratio >= config.watch_latency_spike_ratio:
        reasons.append(LATENCY_SPIKE_REASON)
    if p95_latency_spike_ratio >= config.watch_latency_spike_ratio:
        reasons.append(P95_LATENCY_SPIKE_REASON)
    if publish_lag_seconds > config.max_publish_lag_seconds:
        reasons.append(PUBLISH_LAG_REASON)
    if confirm_lag_seconds > config.max_confirm_lag_seconds:
        reasons.append(CONFIRM_LAG_REASON)
    if observation.round_gap_ratio > config.max_round_gap_ratio:
        reasons.append(ROUND_GAP_REASON)
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
    *,
    reason_codes: tuple[str, ...],
    latency_spike_ratio: Decimal,
    p95_latency_spike_ratio: Decimal,
    config: MarketResearchCryptoOracleLatencySpikeDigestConfig,
) -> str:
    if reason_codes == (READY_REASON,):
        return STATUS_READY
    if (
        latency_spike_ratio >= config.blocked_latency_spike_ratio
        or p95_latency_spike_ratio >= config.blocked_latency_spike_ratio
        or any(
            reason in reason_codes
            for reason in (
                PUBLISH_LAG_REASON,
                CONFIRM_LAG_REASON,
                ROUND_GAP_REASON,
                SOURCE_DIVERSITY_GAP_REASON,
                STALE_OBSERVATION_REASON,
                CONFIDENCE_GAP_REASON,
            )
        )
    ):
        return STATUS_BLOCKED
    return STATUS_WATCH


def _row_sort_value(row: MarketResearchCryptoOracleLatencySpikeDigestRow) -> tuple[int, Decimal]:
    status_rank = {
        STATUS_BLOCKED: 0,
        STATUS_WATCH: 1,
        STATUS_READY: 2,
    }[row.digest_status]
    severity = _decimal_count(
        len(tuple(reason for reason in row.reason_codes if reason != READY_REASON)),
    )
    return (status_rank, -severity)


def _report_status(rows: tuple[MarketResearchCryptoOracleLatencySpikeDigestRow, ...]) -> str:
    if not rows:
        return STATUS_WATCH
    if any(row.digest_status == STATUS_BLOCKED for row in rows):
        return STATUS_BLOCKED
    if any(row.digest_status == STATUS_WATCH for row in rows):
        return STATUS_WATCH
    return STATUS_READY


def _recommended_next_step(status: str) -> str:
    if status == STATUS_BLOCKED:
        return "block_report_only_market_research_crypto_oracle_latency_spike_digest"
    if status == STATUS_WATCH:
        return "review_report_only_market_research_crypto_oracle_latency_spike_digest"
    return "allow_report_only_market_research_crypto_oracle_latency_spike_digest"


def _status_count(
    rows: tuple[MarketResearchCryptoOracleLatencySpikeDigestRow, ...],
    status: str,
) -> Decimal:
    return _decimal_count(sum(1 for row in rows if row.digest_status == status))


def _reason_observation_count(
    rows: tuple[MarketResearchCryptoOracleLatencySpikeDigestRow, ...],
    reason_code: str,
) -> Decimal:
    return _decimal_count(sum(1 for row in rows if reason_code in row.reason_codes))


def _reason_code_counts(
    rows: tuple[MarketResearchCryptoOracleLatencySpikeDigestRow, ...],
) -> tuple[MarketResearchCryptoOracleLatencySpikeDigestReasonCodeCount, ...]:
    observation_count = _decimal_count(len(rows))
    counts: dict[str, int] = {}
    for row in rows:
        for reason_code in row.reason_codes:
            counts[reason_code] = counts.get(reason_code, 0) + 1
    return tuple(
        MarketResearchCryptoOracleLatencySpikeDigestReasonCodeCount(
            reason_code=reason_code,
            count=_decimal_count(counts[reason_code]),
            observation_ratio=_ratio(
                _decimal_count(counts[reason_code]),
                observation_count,
            ),
        )
        for reason_code in REASON_CODE_SEQUENCE
        if reason_code in counts
    )


def _summary_reason_codes(
    rows: tuple[MarketResearchCryptoOracleLatencySpikeDigestRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return (NO_INPUTS_REASON,)
    seen: set[str] = set()
    for row in rows:
        seen.update(row.reason_codes)
    if len(seen) > 1 and READY_REASON in seen:
        seen.remove(READY_REASON)
    return tuple(reason for reason in REASON_CODE_SEQUENCE if reason in seen)


def _validate_row(row: MarketResearchCryptoOracleLatencySpikeDigestRow) -> None:
    if row.latency_spike_ratio != _spike_ratio(
        row.observed_latency_seconds,
        row.baseline_latency_seconds,
    ):
        raise ValueError("latency_spike_ratio does not match latency inputs")
    if row.p95_latency_spike_ratio != _spike_ratio(
        row.p95_latency_seconds,
        row.baseline_p95_latency_seconds,
    ):
        raise ValueError("p95_latency_spike_ratio does not match latency inputs")


def _validate_report(report: MarketResearchCryptoOracleLatencySpikeDigestReport) -> None:
    if report.observation_count != _decimal_count(len(report.rows)):
        raise ValueError("observation_count does not match rows")
    if report.ready_observation_count != _status_count(report.rows, STATUS_READY):
        raise ValueError("ready_observation_count does not match rows")
    if report.watch_observation_count != _status_count(report.rows, STATUS_WATCH):
        raise ValueError("watch_observation_count does not match rows")
    if report.blocked_observation_count != _status_count(report.rows, STATUS_BLOCKED):
        raise ValueError("blocked_observation_count does not match rows")
    expected_counts = (
        (LATENCY_SPIKE_REASON, report.latency_spike_observation_count),
        (P95_LATENCY_SPIKE_REASON, report.p95_latency_spike_observation_count),
        (PUBLISH_LAG_REASON, report.publish_lag_observation_count),
        (CONFIRM_LAG_REASON, report.confirm_lag_observation_count),
        (ROUND_GAP_REASON, report.round_gap_observation_count),
        (SOURCE_DIVERSITY_GAP_REASON, report.source_diversity_gap_observation_count),
        (STALE_OBSERVATION_REASON, report.stale_observation_count),
        (CONFIDENCE_GAP_REASON, report.confidence_gap_observation_count),
    )
    for reason_code, count in expected_counts:
        if count != _reason_observation_count(report.rows, reason_code):
            raise ValueError("reason observation count does not match rows")
    if report.digest_status != _report_status(report.rows):
        raise ValueError("digest_status does not match rows")
    if report.recommended_next_step != _recommended_next_step(report.digest_status):
        raise ValueError("recommended_next_step does not match digest_status")
    if report.average_latency_spike_ratio != _ratio(
        _decimal_sum(row.latency_spike_ratio for row in report.rows),
        report.observation_count,
    ):
        raise ValueError("average_latency_spike_ratio does not match rows")
    if report.average_p95_latency_spike_ratio != _ratio(
        _decimal_sum(row.p95_latency_spike_ratio for row in report.rows),
        report.observation_count,
    ):
        raise ValueError("average_p95_latency_spike_ratio does not match rows")
    if report.average_round_gap_ratio != _ratio(
        _decimal_sum(row.round_gap_ratio for row in report.rows),
        report.observation_count,
    ):
        raise ValueError("average_round_gap_ratio does not match rows")
    if report.average_publish_lag_seconds != _ratio(
        _decimal_sum(row.publish_lag_seconds for row in report.rows),
        report.observation_count,
    ):
        raise ValueError("average_publish_lag_seconds does not match rows")
    if report.average_confirm_lag_seconds != _ratio(
        _decimal_sum(row.confirm_lag_seconds for row in report.rows),
        report.observation_count,
    ):
        raise ValueError("average_confirm_lag_seconds does not match rows")
    if report.max_observation_age_seconds != max(
        (row.observation_age_seconds for row in report.rows),
        default=ZERO,
    ):
        raise ValueError("max_observation_age_seconds does not match rows")
    if report.reason_code_counts != _reason_code_counts(report.rows):
        raise ValueError("reason_code_counts do not match rows")
    if report.reason_codes != _summary_reason_codes(report.rows):
        raise ValueError("reason_codes do not match rows")


def _normalize_observations(
    observations: Iterable[MarketResearchCryptoOracleLatencySpikeObservation],
) -> tuple[MarketResearchCryptoOracleLatencySpikeObservation, ...]:
    observation_tuple = tuple(observations)
    seen_keys: set[str] = set()
    for observation in observation_tuple:
        if type(observation) is not MarketResearchCryptoOracleLatencySpikeObservation:
            raise ValueError(
                "observations must contain "
                "MarketResearchCryptoOracleLatencySpikeObservation",
            )
        if observation.oracle_key in seen_keys:
            raise ValueError("oracle_key values must be unique")
        seen_keys.add(observation.oracle_key)
        _require_hard_flags("observation", observation)
    return observation_tuple


def _normalize_rows(
    rows: tuple[MarketResearchCryptoOracleLatencySpikeDigestRow, ...],
) -> tuple[MarketResearchCryptoOracleLatencySpikeDigestRow, ...]:
    if type(rows) is not tuple:
        raise ValueError("rows must be a tuple")
    for row in rows:
        if type(row) is not MarketResearchCryptoOracleLatencySpikeDigestRow:
            raise ValueError(
                "rows must contain MarketResearchCryptoOracleLatencySpikeDigestRow",
            )
        _require_hard_flags("row", row)
    return rows


def _normalize_reason_code_counts(
    items: tuple[MarketResearchCryptoOracleLatencySpikeDigestReasonCodeCount, ...],
) -> tuple[MarketResearchCryptoOracleLatencySpikeDigestReasonCodeCount, ...]:
    if type(items) is not tuple:
        raise ValueError("reason_code_counts must be a tuple")
    for item in items:
        if type(item) is not MarketResearchCryptoOracleLatencySpikeDigestReasonCodeCount:
            raise ValueError("reason_code_counts must contain reason count rows")
    return items


def _normalize_source_config_versions(
    value: tuple[tuple[str, str], ...],
) -> tuple[tuple[str, str], ...]:
    if type(value) is not tuple:
        raise ValueError("source_config_versions must be a tuple")
    pairs: list[tuple[str, str]] = []
    seen_keys: set[str] = set()
    for item in value:
        if type(item) is not tuple or len(item) != 2:
            raise ValueError("source_config_versions must contain pairs")
        oracle_key, source_config_version = item
        _require_public_string("oracle_key", oracle_key)
        _require_public_string("source_config_version", source_config_version)
        if oracle_key in seen_keys:
            raise ValueError("source_config_versions oracle_key values must be unique")
        seen_keys.add(oracle_key)
        pairs.append((oracle_key, source_config_version))
    return tuple(pairs)


def _normalize_reason_codes(
    value: tuple[str, ...],
    *,
    sequence: tuple[str, ...],
) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ValueError("reason_codes must be a tuple")
    seen: set[str] = set()
    for reason_code in value:
        _require_reason_code("reason_code", reason_code)
        if reason_code in seen:
            raise ValueError("reason_codes must be unique")
        seen.add(reason_code)
    normalized = tuple(reason_code for reason_code in sequence if reason_code in seen)
    if normalized != value:
        raise ValueError("reason_codes must be deterministic")
    return normalized


def _require_status(field_name: str, value: str) -> None:
    if type(value) is not str or value not in ORACLE_LATENCY_SPIKE_DIGEST_STATUSES:
        raise ValueError(f"{field_name} must be a valid status")


def _require_reason_code(field_name: str, value: str) -> None:
    if type(value) is not str or value not in REASON_CODE_SEQUENCE:
        raise ValueError(f"{field_name} must be a valid reason code")


def _require_hard_flags(field_name: str, value: object) -> None:
    for flag_name in ("paper_only", "report_only", "readonly"):
        if getattr(value, flag_name, None) is not True:
            raise ValueError(f"{field_name} must keep {flag_name}=True")


def _require_canonical_string(field_name: str, value: str) -> None:
    if type(value) is not str or not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical string")
    _require_safe_text(field_name, value)


def _require_public_string(field_name: str, value: str) -> None:
    _require_canonical_string(field_name, value)
    if "\n" in value or "\r" in value:
        raise ValueError(f"{field_name} must be single-line")


def _require_safe_text(field_name: str, value: str) -> None:
    lowered = value.lower()
    if any(fragment in lowered for fragment in UNSAFE_TEXT_FRAGMENTS):
        raise ValueError(f"{field_name} must be redacted")


def _require_nonnegative_count_decimal(field_name: str, value: Decimal) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be Decimal")
    if not value.is_finite() or value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return _quantize(value)


def _require_positive_count_decimal(field_name: str, value: Decimal) -> Decimal:
    value = _require_nonnegative_count_decimal(field_name, value)
    if value <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return value


def _require_ratio_decimal(field_name: str, value: Decimal) -> Decimal:
    value = _require_nonnegative_count_decimal(field_name, value)
    if value > ONE:
        raise ValueError(f"{field_name} must be between zero and one")
    return value


def _as_utc(field_name: str, value: datetime) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be datetime")
    if value.tzinfo is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    offset = value.utcoffset()
    if offset is None:
        raise ValueError(f"{field_name} must have a valid UTC offset")
    return value.astimezone(UTC)


def _age_seconds(newer: datetime, older: datetime) -> Decimal:
    delta = newer - older
    return _quantize(
        Decimal(delta.days * 86400)
        + (Decimal(delta.seconds) * ONE)
        + (Decimal(delta.microseconds) / MICROSECONDS_PER_SECOND),
    )


def _spike_ratio(current: Decimal, baseline: Decimal) -> Decimal:
    if baseline == ZERO:
        if current == ZERO:
            return ZERO
        return ONE
    return _ratio(current - baseline, baseline)


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    numerator = _require_nonnegative_count_decimal("numerator", numerator)
    denominator = _require_nonnegative_count_decimal("denominator", denominator)
    if denominator == ZERO:
        return ZERO
    return _quantize(numerator / denominator)


def _decimal_sum(values: Iterable[Decimal]) -> Decimal:
    total = ZERO
    for value in values:
        total += value
    return _quantize(total)


def _decimal_count(value: int) -> Decimal:
    return _quantize(Decimal(value))


def _quantize(value: Decimal) -> Decimal:
    return value.quantize(QUANT, rounding=ROUND_HALF_EVEN)


def _json_ready(value: Any) -> Any:
    if is_dataclass(value):
        return {
            field.name: _json_ready(getattr(value, field.name))
            for field in fields(value)
        }
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, Decimal):
        return format(value, "f")
    if isinstance(value, tuple):
        return [_json_ready(item) for item in value]
    if isinstance(value, bool) or value is None or isinstance(value, str):
        return value
    if isinstance(value, MappingProxyType):
        return {key: _json_ready(item) for key, item in value.items()}
    raise ValueError("value is not payload-safe")


def _freeze(value: Any) -> Any:
    if isinstance(value, dict):
        frozen = {key: _freeze(item) for key, item in value.items()}
        frozen["payload_kind"] = "market_research_crypto_oracle_latency_spike_digest"
        return MappingProxyType(frozen)
    if isinstance(value, list):
        return tuple(_freeze(item) for item in value)
    return value
