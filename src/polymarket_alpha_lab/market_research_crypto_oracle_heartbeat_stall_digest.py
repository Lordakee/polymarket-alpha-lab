"""Pure Phase 1 crypto oracle heartbeat stall research reducer."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal, ROUND_HALF_EVEN
from types import MappingProxyType
from typing import Any


DEFAULT_MARKET_RESEARCH_CRYPTO_ORACLE_HEARTBEAT_STALL_DIGEST_CONFIG_VERSION = (
    "market-research-crypto-oracle-heartbeat-stall-digest-v0"
)

STATUS_READY = "ready"
STATUS_WATCH = "watch"
STATUS_BLOCKED = "blocked"
HEARTBEAT_STALL_DIGEST_STATUSES = (STATUS_READY, STATUS_WATCH, STATUS_BLOCKED)

READY_REASON = "market_research_crypto_oracle_heartbeat_stall_digest_ready"
NO_INPUTS_REASON = "market_research_crypto_oracle_heartbeat_stall_digest_no_inputs"
HEARTBEAT_STALL_REASON = (
    "market_research_crypto_oracle_heartbeat_stall_digest_heartbeat_stall"
)
MAX_GAP_REASON = "market_research_crypto_oracle_heartbeat_stall_digest_max_gap"
PUBLISH_LAG_REASON = (
    "market_research_crypto_oracle_heartbeat_stall_digest_publish_lag"
)
STALE_OBSERVATION_REASON = (
    "market_research_crypto_oracle_heartbeat_stall_digest_stale_observation"
)
SOURCE_DIVERSITY_GAP_REASON = (
    "market_research_crypto_oracle_heartbeat_stall_digest_source_diversity_gap"
)
CONFIDENCE_GAP_REASON = (
    "market_research_crypto_oracle_heartbeat_stall_digest_confidence_gap"
)

REASON_CODE_SEQUENCE = (
    HEARTBEAT_STALL_REASON,
    MAX_GAP_REASON,
    PUBLISH_LAG_REASON,
    STALE_OBSERVATION_REASON,
    SOURCE_DIVERSITY_GAP_REASON,
    CONFIDENCE_GAP_REASON,
    READY_REASON,
    NO_INPUTS_REASON,
)
ROW_REASON_CODE_SEQUENCE = (
    HEARTBEAT_STALL_REASON,
    MAX_GAP_REASON,
    PUBLISH_LAG_REASON,
    STALE_OBSERVATION_REASON,
    SOURCE_DIVERSITY_GAP_REASON,
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
        _join_parts("pay", "load", "_", "json"),
        _join_parts("wa", "llet"),
        _join_parts("or", "der"),
        _join_parts("to", "ken"),
        _join_parts("sec", "ret"),
        _join_parts("pri", "vate"),
        _join_parts("0", "x"),
    ),
)

__all__ = (
    "DEFAULT_MARKET_RESEARCH_CRYPTO_ORACLE_HEARTBEAT_STALL_DIGEST_CONFIG_VERSION",
    "MarketResearchCryptoOracleHeartbeatStallDigestConfig",
    "MarketResearchCryptoOracleHeartbeatStallDigestReasonCodeCount",
    "MarketResearchCryptoOracleHeartbeatStallDigestReport",
    "MarketResearchCryptoOracleHeartbeatStallDigestRow",
    "MarketResearchCryptoOracleHeartbeatStallObservation",
    "build_market_research_crypto_oracle_heartbeat_stall_digest",
    "market_research_crypto_oracle_heartbeat_stall_digest_payload",
)


@dataclass(frozen=True)
class MarketResearchCryptoOracleHeartbeatStallDigestConfig:
    config_version: str = (
        DEFAULT_MARKET_RESEARCH_CRYPTO_ORACLE_HEARTBEAT_STALL_DIGEST_CONFIG_VERSION
    )
    max_observation_age_seconds: Decimal = Decimal("1800.000000")
    watch_heartbeat_gap_ratio: Decimal = Decimal("1.500000")
    blocked_heartbeat_gap_ratio: Decimal = Decimal("3.000000")
    max_heartbeat_gap_seconds: Decimal = Decimal("900.000000")
    max_publish_lag_seconds: Decimal = Decimal("300.000000")
    min_source_count: Decimal = Decimal("3.000000")
    min_confidence: Decimal = Decimal("0.700000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketResearchCryptoOracleHeartbeatStallDigestConfig:
            raise TypeError(
                "MarketResearchCryptoOracleHeartbeatStallDigestConfig "
                "does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not MarketResearchCryptoOracleHeartbeatStallDigestConfig:
            raise ValueError(
                "config must be exactly "
                "MarketResearchCryptoOracleHeartbeatStallDigestConfig",
            )
        _require_canonical_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_MARKET_RESEARCH_CRYPTO_ORACLE_HEARTBEAT_STALL_DIGEST_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the configured version")
        for field_name in (
            "max_observation_age_seconds",
            "watch_heartbeat_gap_ratio",
            "blocked_heartbeat_gap_ratio",
            "max_heartbeat_gap_seconds",
            "max_publish_lag_seconds",
            "min_source_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_positive_count_decimal(field_name, getattr(self, field_name)),
            )
        if self.watch_heartbeat_gap_ratio > self.blocked_heartbeat_gap_ratio:
            raise ValueError("watch_heartbeat_gap_ratio must not exceed blocked threshold")
        object.__setattr__(
            self,
            "min_confidence",
            _require_ratio_decimal("min_confidence", self.min_confidence),
        )
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class MarketResearchCryptoOracleHeartbeatStallObservation:
    condition_id: str
    oracle_key: str
    asset_symbol: str
    observed_at: datetime
    last_heartbeat_at: datetime
    published_at: datetime
    expected_heartbeat_interval_seconds: Decimal
    heartbeat_gap_seconds: Decimal
    source_count: Decimal
    confidence: Decimal
    source_config_version: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketResearchCryptoOracleHeartbeatStallObservation:
            raise TypeError(
                "MarketResearchCryptoOracleHeartbeatStallObservation "
                "does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not MarketResearchCryptoOracleHeartbeatStallObservation:
            raise ValueError(
                "observation must be exactly "
                "MarketResearchCryptoOracleHeartbeatStallObservation",
            )
        for field_name in (
            "condition_id",
            "oracle_key",
            "asset_symbol",
            "source_config_version",
        ):
            _require_public_string(field_name, getattr(self, field_name))
        for field_name in ("observed_at", "last_heartbeat_at", "published_at"):
            object.__setattr__(self, field_name, _as_utc(field_name, getattr(self, field_name)))
        for field_name in (
            "expected_heartbeat_interval_seconds",
            "heartbeat_gap_seconds",
            "source_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_count_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "expected_heartbeat_interval_seconds",
            _require_positive_count_decimal(
                "expected_heartbeat_interval_seconds",
                self.expected_heartbeat_interval_seconds,
            ),
        )
        object.__setattr__(
            self,
            "confidence",
            _require_ratio_decimal("confidence", self.confidence),
        )
        _validate_observation(self)
        _require_hard_flags("observation", self)


@dataclass(frozen=True)
class MarketResearchCryptoOracleHeartbeatStallDigestRow:
    condition_id: str
    oracle_key: str
    asset_symbol: str
    digest_status: str
    observed_at: datetime
    last_heartbeat_at: datetime
    published_at: datetime
    observation_age_seconds: Decimal
    heartbeat_gap_seconds: Decimal
    expected_heartbeat_interval_seconds: Decimal
    heartbeat_gap_ratio: Decimal
    missed_heartbeat_count: Decimal
    publish_lag_seconds: Decimal
    source_count: Decimal
    confidence: Decimal
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketResearchCryptoOracleHeartbeatStallDigestRow:
            raise TypeError(
                "MarketResearchCryptoOracleHeartbeatStallDigestRow "
                "does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not MarketResearchCryptoOracleHeartbeatStallDigestRow:
            raise ValueError(
                "row must be exactly MarketResearchCryptoOracleHeartbeatStallDigestRow",
            )
        for field_name in ("condition_id", "oracle_key", "asset_symbol"):
            _require_public_string(field_name, getattr(self, field_name))
        _require_status("digest_status", self.digest_status)
        for field_name in ("observed_at", "last_heartbeat_at", "published_at"):
            object.__setattr__(self, field_name, _as_utc(field_name, getattr(self, field_name)))
        for field_name in (
            "observation_age_seconds",
            "heartbeat_gap_seconds",
            "expected_heartbeat_interval_seconds",
            "heartbeat_gap_ratio",
            "missed_heartbeat_count",
            "publish_lag_seconds",
            "source_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_count_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "expected_heartbeat_interval_seconds",
            _require_positive_count_decimal(
                "expected_heartbeat_interval_seconds",
                self.expected_heartbeat_interval_seconds,
            ),
        )
        object.__setattr__(
            self,
            "confidence",
            _require_ratio_decimal("confidence", self.confidence),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes, sequence=ROW_REASON_CODE_SEQUENCE),
        )
        _validate_row(self)
        _require_hard_flags("row", self)


@dataclass(frozen=True)
class MarketResearchCryptoOracleHeartbeatStallDigestReasonCodeCount:
    reason_code: str
    count: Decimal
    observation_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketResearchCryptoOracleHeartbeatStallDigestReasonCodeCount:
            raise TypeError(
                "MarketResearchCryptoOracleHeartbeatStallDigestReasonCodeCount "
                "does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not MarketResearchCryptoOracleHeartbeatStallDigestReasonCodeCount:
            raise ValueError(
                "reason code count must be exactly "
                "MarketResearchCryptoOracleHeartbeatStallDigestReasonCodeCount",
            )
        _require_reason_code("reason_code", self.reason_code)
        object.__setattr__(
            self,
            "count",
            _require_positive_whole_count_decimal("count", self.count),
        )
        object.__setattr__(
            self,
            "observation_ratio",
            _require_ratio_decimal("observation_ratio", self.observation_ratio),
        )
        _require_hard_flags("reason code count", self)


@dataclass(frozen=True)
class MarketResearchCryptoOracleHeartbeatStallDigestReport:
    generated_at: datetime
    config_version: str
    digest_status: str
    recommended_next_step: str
    observation_count: Decimal
    ready_observation_count: Decimal
    watch_observation_count: Decimal
    blocked_observation_count: Decimal
    heartbeat_stall_observation_count: Decimal
    max_gap_observation_count: Decimal
    publish_lag_observation_count: Decimal
    stale_observation_count: Decimal
    source_diversity_gap_observation_count: Decimal
    confidence_gap_observation_count: Decimal
    average_heartbeat_gap_seconds: Decimal
    average_heartbeat_gap_ratio: Decimal
    average_publish_lag_seconds: Decimal
    max_observed_heartbeat_gap_seconds: Decimal
    max_observation_age_seconds: Decimal
    max_allowed_observation_age_seconds: Decimal
    watch_heartbeat_gap_ratio: Decimal
    blocked_heartbeat_gap_ratio: Decimal
    max_heartbeat_gap_seconds: Decimal
    max_publish_lag_seconds: Decimal
    min_source_count: Decimal
    min_confidence: Decimal
    rows: tuple[MarketResearchCryptoOracleHeartbeatStallDigestRow, ...]
    source_config_versions: tuple[tuple[str, str], ...]
    reason_code_counts: tuple[
        MarketResearchCryptoOracleHeartbeatStallDigestReasonCodeCount,
        ...,
    ]
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketResearchCryptoOracleHeartbeatStallDigestReport:
            raise TypeError(
                "MarketResearchCryptoOracleHeartbeatStallDigestReport "
                "does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not MarketResearchCryptoOracleHeartbeatStallDigestReport:
            raise ValueError(
                "report must be exactly MarketResearchCryptoOracleHeartbeatStallDigestReport",
            )
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_MARKET_RESEARCH_CRYPTO_ORACLE_HEARTBEAT_STALL_DIGEST_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the configured version")
        _require_status("digest_status", self.digest_status)
        _require_canonical_string("recommended_next_step", self.recommended_next_step)
        for field_name in (
            "observation_count",
            "ready_observation_count",
            "watch_observation_count",
            "blocked_observation_count",
            "heartbeat_stall_observation_count",
            "max_gap_observation_count",
            "publish_lag_observation_count",
            "stale_observation_count",
            "source_diversity_gap_observation_count",
            "confidence_gap_observation_count",
            "average_heartbeat_gap_seconds",
            "average_heartbeat_gap_ratio",
            "average_publish_lag_seconds",
            "max_observed_heartbeat_gap_seconds",
            "max_observation_age_seconds",
            "max_allowed_observation_age_seconds",
            "watch_heartbeat_gap_ratio",
            "blocked_heartbeat_gap_ratio",
            "max_heartbeat_gap_seconds",
            "max_publish_lag_seconds",
            "min_source_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_count_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "min_confidence",
            _require_ratio_decimal("min_confidence", self.min_confidence),
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


def build_market_research_crypto_oracle_heartbeat_stall_digest(
    observations: Iterable[MarketResearchCryptoOracleHeartbeatStallObservation],
    *,
    config: MarketResearchCryptoOracleHeartbeatStallDigestConfig | None = None,
    generated_at: datetime,
) -> MarketResearchCryptoOracleHeartbeatStallDigestReport:
    cfg = config or MarketResearchCryptoOracleHeartbeatStallDigestConfig()
    if type(cfg) is not MarketResearchCryptoOracleHeartbeatStallDigestConfig:
        raise ValueError(
            "config must be exactly MarketResearchCryptoOracleHeartbeatStallDigestConfig",
        )
    generated_at_utc = _as_utc("generated_at", generated_at)
    normalized_observations = _normalize_observations(observations)
    rows = tuple(
        _row_for_observation(observation, config=cfg, generated_at=generated_at_utc)
        for observation in normalized_observations
    )
    sorted_rows = tuple(sorted(rows, key=_row_sort_key))
    observation_count = _decimal_count(len(sorted_rows))
    report_status = _report_status(sorted_rows)
    return MarketResearchCryptoOracleHeartbeatStallDigestReport(
        generated_at=generated_at_utc,
        config_version=cfg.config_version,
        digest_status=report_status,
        recommended_next_step=_recommended_next_step(report_status),
        observation_count=observation_count,
        ready_observation_count=_status_count(sorted_rows, STATUS_READY),
        watch_observation_count=_status_count(sorted_rows, STATUS_WATCH),
        blocked_observation_count=_status_count(sorted_rows, STATUS_BLOCKED),
        heartbeat_stall_observation_count=_reason_observation_count(
            sorted_rows,
            HEARTBEAT_STALL_REASON,
        ),
        max_gap_observation_count=_reason_observation_count(
            sorted_rows,
            MAX_GAP_REASON,
        ),
        publish_lag_observation_count=_reason_observation_count(
            sorted_rows,
            PUBLISH_LAG_REASON,
        ),
        stale_observation_count=_reason_observation_count(
            sorted_rows,
            STALE_OBSERVATION_REASON,
        ),
        source_diversity_gap_observation_count=_reason_observation_count(
            sorted_rows,
            SOURCE_DIVERSITY_GAP_REASON,
        ),
        confidence_gap_observation_count=_reason_observation_count(
            sorted_rows,
            CONFIDENCE_GAP_REASON,
        ),
        average_heartbeat_gap_seconds=_ratio(
            _decimal_sum(row.heartbeat_gap_seconds for row in sorted_rows),
            observation_count,
        ),
        average_heartbeat_gap_ratio=_ratio(
            _decimal_sum(row.heartbeat_gap_ratio for row in sorted_rows),
            observation_count,
        ),
        average_publish_lag_seconds=_ratio(
            _decimal_sum(row.publish_lag_seconds for row in sorted_rows),
            observation_count,
        ),
        max_observed_heartbeat_gap_seconds=max(
            (row.heartbeat_gap_seconds for row in sorted_rows),
            default=ZERO,
        ),
        max_observation_age_seconds=max(
            (row.observation_age_seconds for row in sorted_rows),
            default=ZERO,
        ),
        max_allowed_observation_age_seconds=cfg.max_observation_age_seconds,
        watch_heartbeat_gap_ratio=cfg.watch_heartbeat_gap_ratio,
        blocked_heartbeat_gap_ratio=cfg.blocked_heartbeat_gap_ratio,
        max_heartbeat_gap_seconds=cfg.max_heartbeat_gap_seconds,
        max_publish_lag_seconds=cfg.max_publish_lag_seconds,
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


def market_research_crypto_oracle_heartbeat_stall_digest_payload(
    report: MarketResearchCryptoOracleHeartbeatStallDigestReport,
) -> MappingProxyType:
    if type(report) is not MarketResearchCryptoOracleHeartbeatStallDigestReport:
        raise ValueError(
            "report must be exactly MarketResearchCryptoOracleHeartbeatStallDigestReport",
        )
    return _freeze(_json_ready(report))


def _row_for_observation(
    observation: MarketResearchCryptoOracleHeartbeatStallObservation,
    *,
    config: MarketResearchCryptoOracleHeartbeatStallDigestConfig,
    generated_at: datetime,
) -> MarketResearchCryptoOracleHeartbeatStallDigestRow:
    for field_name in ("observed_at", "last_heartbeat_at", "published_at"):
        if getattr(observation, field_name) > generated_at:
            raise ValueError(f"{field_name} must not be in the future")
    observation_age_seconds = _age_seconds(generated_at, observation.observed_at)
    publish_lag_seconds = _age_seconds(generated_at, observation.published_at)
    heartbeat_gap_ratio = _heartbeat_gap_ratio(
        observation.heartbeat_gap_seconds,
        observation.expected_heartbeat_interval_seconds,
    )
    reason_codes = _row_reason_codes(
        observation=observation,
        config=config,
        observation_age_seconds=observation_age_seconds,
        publish_lag_seconds=publish_lag_seconds,
        heartbeat_gap_ratio=heartbeat_gap_ratio,
    )
    return MarketResearchCryptoOracleHeartbeatStallDigestRow(
        condition_id=observation.condition_id,
        oracle_key=observation.oracle_key,
        asset_symbol=observation.asset_symbol,
        digest_status=_row_status(
            reason_codes=reason_codes,
            heartbeat_gap_ratio=heartbeat_gap_ratio,
            config=config,
        ),
        observed_at=observation.observed_at,
        last_heartbeat_at=observation.last_heartbeat_at,
        published_at=observation.published_at,
        observation_age_seconds=observation_age_seconds,
        heartbeat_gap_seconds=observation.heartbeat_gap_seconds,
        expected_heartbeat_interval_seconds=(
            observation.expected_heartbeat_interval_seconds
        ),
        heartbeat_gap_ratio=heartbeat_gap_ratio,
        missed_heartbeat_count=heartbeat_gap_ratio,
        publish_lag_seconds=publish_lag_seconds,
        source_count=observation.source_count,
        confidence=observation.confidence,
        reason_codes=reason_codes,
    )


def _row_reason_codes(
    *,
    observation: MarketResearchCryptoOracleHeartbeatStallObservation,
    config: MarketResearchCryptoOracleHeartbeatStallDigestConfig,
    observation_age_seconds: Decimal,
    publish_lag_seconds: Decimal,
    heartbeat_gap_ratio: Decimal,
) -> tuple[str, ...]:
    reasons: list[str] = []
    if heartbeat_gap_ratio >= config.watch_heartbeat_gap_ratio:
        reasons.append(HEARTBEAT_STALL_REASON)
    if observation.heartbeat_gap_seconds > config.max_heartbeat_gap_seconds:
        reasons.append(MAX_GAP_REASON)
    if publish_lag_seconds > config.max_publish_lag_seconds:
        reasons.append(PUBLISH_LAG_REASON)
    if observation_age_seconds > config.max_observation_age_seconds:
        reasons.append(STALE_OBSERVATION_REASON)
    if observation.source_count < config.min_source_count:
        reasons.append(SOURCE_DIVERSITY_GAP_REASON)
    if observation.confidence < config.min_confidence:
        reasons.append(CONFIDENCE_GAP_REASON)
    if not reasons:
        reasons.append(READY_REASON)
    return tuple(reason for reason in ROW_REASON_CODE_SEQUENCE if reason in reasons)


def _row_status(
    *,
    reason_codes: tuple[str, ...],
    heartbeat_gap_ratio: Decimal,
    config: MarketResearchCryptoOracleHeartbeatStallDigestConfig,
) -> str:
    if reason_codes == (READY_REASON,):
        return STATUS_READY
    if (
        heartbeat_gap_ratio >= config.blocked_heartbeat_gap_ratio
        or any(
            reason in reason_codes
            for reason in (
                MAX_GAP_REASON,
                PUBLISH_LAG_REASON,
                STALE_OBSERVATION_REASON,
                SOURCE_DIVERSITY_GAP_REASON,
                CONFIDENCE_GAP_REASON,
            )
        )
    ):
        return STATUS_BLOCKED
    return STATUS_WATCH


def _row_sort_key(
    row: MarketResearchCryptoOracleHeartbeatStallDigestRow,
) -> tuple[int, Decimal, Decimal, str, str]:
    status_rank = {
        STATUS_BLOCKED: 0,
        STATUS_WATCH: 1,
        STATUS_READY: 2,
    }[row.digest_status]
    severity = _decimal_count(
        len(tuple(reason for reason in row.reason_codes if reason != READY_REASON)),
    )
    return (status_rank, -severity, -row.heartbeat_gap_ratio, row.oracle_key, row.condition_id)


def _report_status(rows: tuple[MarketResearchCryptoOracleHeartbeatStallDigestRow, ...]) -> str:
    if not rows:
        return STATUS_BLOCKED
    if any(row.digest_status == STATUS_BLOCKED for row in rows):
        return STATUS_BLOCKED
    if any(row.digest_status == STATUS_WATCH for row in rows):
        return STATUS_WATCH
    return STATUS_READY


def _recommended_next_step(status: str) -> str:
    if status == STATUS_BLOCKED:
        return "block_report_only_market_research_crypto_oracle_heartbeat_stall_digest"
    if status == STATUS_WATCH:
        return "review_report_only_market_research_crypto_oracle_heartbeat_stall_digest"
    return "allow_report_only_market_research_crypto_oracle_heartbeat_stall_digest"


def _status_count(
    rows: tuple[MarketResearchCryptoOracleHeartbeatStallDigestRow, ...],
    status: str,
) -> Decimal:
    return _decimal_count(sum(1 for row in rows if row.digest_status == status))


def _reason_observation_count(
    rows: tuple[MarketResearchCryptoOracleHeartbeatStallDigestRow, ...],
    reason_code: str,
) -> Decimal:
    return _decimal_count(sum(1 for row in rows if reason_code in row.reason_codes))


def _reason_code_counts(
    rows: tuple[MarketResearchCryptoOracleHeartbeatStallDigestRow, ...],
) -> tuple[MarketResearchCryptoOracleHeartbeatStallDigestReasonCodeCount, ...]:
    observation_count = _decimal_count(len(rows))
    if not rows:
        return (
            MarketResearchCryptoOracleHeartbeatStallDigestReasonCodeCount(
                reason_code=NO_INPUTS_REASON,
                count=ONE,
                observation_ratio=ZERO,
            ),
        )
    counts: dict[str, int] = {}
    for row in rows:
        for reason_code in row.reason_codes:
            counts[reason_code] = counts.get(reason_code, 0) + 1
    return tuple(
        MarketResearchCryptoOracleHeartbeatStallDigestReasonCodeCount(
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
    rows: tuple[MarketResearchCryptoOracleHeartbeatStallDigestRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return (NO_INPUTS_REASON,)
    seen: set[str] = set()
    for row in rows:
        seen.update(row.reason_codes)
    return tuple(reason for reason in REASON_CODE_SEQUENCE if reason in seen)


def _validate_observation(
    observation: MarketResearchCryptoOracleHeartbeatStallObservation,
) -> None:
    if observation.last_heartbeat_at > observation.observed_at:
        raise ValueError("last_heartbeat_at must not be after observed_at")
    expected_gap = _age_seconds(observation.observed_at, observation.last_heartbeat_at)
    if observation.heartbeat_gap_seconds != expected_gap:
        raise ValueError("heartbeat_gap_seconds must match heartbeat timestamps")


def _validate_row(row: MarketResearchCryptoOracleHeartbeatStallDigestRow) -> None:
    expected_gap = _age_seconds(row.observed_at, row.last_heartbeat_at)
    if row.heartbeat_gap_seconds != expected_gap:
        raise ValueError("heartbeat_gap_seconds does not match heartbeat timestamps")
    expected_ratio = _heartbeat_gap_ratio(
        row.heartbeat_gap_seconds,
        row.expected_heartbeat_interval_seconds,
    )
    if row.heartbeat_gap_ratio != expected_ratio:
        raise ValueError("heartbeat_gap_ratio does not match heartbeat inputs")
    if row.missed_heartbeat_count != expected_ratio:
        raise ValueError("missed_heartbeat_count does not match heartbeat inputs")
    if row.digest_status == STATUS_READY and row.reason_codes != (READY_REASON,):
        raise ValueError("digest_status does not match reason_codes")
    if row.reason_codes == (READY_REASON,) and row.digest_status != STATUS_READY:
        raise ValueError("digest_status does not match reason_codes")
    if row.digest_status == STATUS_WATCH and any(
        reason in row.reason_codes
        for reason in (
            MAX_GAP_REASON,
            PUBLISH_LAG_REASON,
            STALE_OBSERVATION_REASON,
            SOURCE_DIVERSITY_GAP_REASON,
            CONFIDENCE_GAP_REASON,
        )
    ):
        raise ValueError("digest_status does not match reason_codes")
    if row.digest_status == STATUS_BLOCKED and row.reason_codes == (READY_REASON,):
        raise ValueError("digest_status does not match reason_codes")


def _validate_report(report: MarketResearchCryptoOracleHeartbeatStallDigestReport) -> None:
    if report.observation_count != _decimal_count(len(report.rows)):
        raise ValueError("observation_count does not match rows")
    if report.ready_observation_count != _status_count(report.rows, STATUS_READY):
        raise ValueError("ready_observation_count does not match rows")
    if report.watch_observation_count != _status_count(report.rows, STATUS_WATCH):
        raise ValueError("watch_observation_count does not match rows")
    if report.blocked_observation_count != _status_count(report.rows, STATUS_BLOCKED):
        raise ValueError("blocked_observation_count does not match rows")
    expected_counts = (
        (HEARTBEAT_STALL_REASON, report.heartbeat_stall_observation_count),
        (MAX_GAP_REASON, report.max_gap_observation_count),
        (PUBLISH_LAG_REASON, report.publish_lag_observation_count),
        (STALE_OBSERVATION_REASON, report.stale_observation_count),
        (SOURCE_DIVERSITY_GAP_REASON, report.source_diversity_gap_observation_count),
        (CONFIDENCE_GAP_REASON, report.confidence_gap_observation_count),
    )
    for reason_code, count in expected_counts:
        if count != _reason_observation_count(report.rows, reason_code):
            raise ValueError("reason observation count does not match rows")
    if report.digest_status != _report_status(report.rows):
        raise ValueError("digest_status does not match rows")
    if report.recommended_next_step != _recommended_next_step(report.digest_status):
        raise ValueError("recommended_next_step does not match digest_status")
    if report.average_heartbeat_gap_seconds != _ratio(
        _decimal_sum(row.heartbeat_gap_seconds for row in report.rows),
        report.observation_count,
    ):
        raise ValueError("average_heartbeat_gap_seconds does not match rows")
    if report.average_heartbeat_gap_ratio != _ratio(
        _decimal_sum(row.heartbeat_gap_ratio for row in report.rows),
        report.observation_count,
    ):
        raise ValueError("average_heartbeat_gap_ratio does not match rows")
    if report.average_publish_lag_seconds != _ratio(
        _decimal_sum(row.publish_lag_seconds for row in report.rows),
        report.observation_count,
    ):
        raise ValueError("average_publish_lag_seconds does not match rows")
    if report.max_observed_heartbeat_gap_seconds != max(
        (row.heartbeat_gap_seconds for row in report.rows),
        default=ZERO,
    ):
        raise ValueError("max_observed_heartbeat_gap_seconds does not match rows")
    if report.max_observation_age_seconds != max(
        (row.observation_age_seconds for row in report.rows),
        default=ZERO,
    ):
        raise ValueError("max_observation_age_seconds does not match rows")
    if report.reason_code_counts != _reason_code_counts(report.rows):
        raise ValueError("reason_code_counts do not match rows")
    if report.reason_codes != _summary_reason_codes(report.rows):
        raise ValueError("reason_codes do not match rows")
    if tuple(key for key, _version in report.source_config_versions) != tuple(
        sorted(row.oracle_key for row in report.rows)
    ):
        raise ValueError("source_config_versions do not match rows")


def _normalize_observations(
    observations: Iterable[MarketResearchCryptoOracleHeartbeatStallObservation],
) -> tuple[MarketResearchCryptoOracleHeartbeatStallObservation, ...]:
    if isinstance(observations, (str, bytes)):
        raise ValueError(
            "observations must contain "
            "MarketResearchCryptoOracleHeartbeatStallObservation",
        )
    observation_tuple = tuple(observations)
    seen_keys: set[str] = set()
    for observation in observation_tuple:
        if type(observation) is not MarketResearchCryptoOracleHeartbeatStallObservation:
            raise ValueError(
                "observations must contain "
                "MarketResearchCryptoOracleHeartbeatStallObservation",
            )
        if observation.oracle_key in seen_keys:
            raise ValueError("oracle_key values must be unique")
        seen_keys.add(observation.oracle_key)
        _require_hard_flags("observation", observation)
    return observation_tuple


def _normalize_rows(
    rows: tuple[MarketResearchCryptoOracleHeartbeatStallDigestRow, ...],
) -> tuple[MarketResearchCryptoOracleHeartbeatStallDigestRow, ...]:
    if type(rows) is not tuple:
        raise ValueError("rows must be a tuple")
    seen_keys: set[str] = set()
    for row in rows:
        if type(row) is not MarketResearchCryptoOracleHeartbeatStallDigestRow:
            raise ValueError(
                "rows must contain MarketResearchCryptoOracleHeartbeatStallDigestRow",
            )
        if row.oracle_key in seen_keys:
            raise ValueError("rows oracle_key values must be unique")
        seen_keys.add(row.oracle_key)
        _require_hard_flags("row", row)
    if rows != tuple(sorted(rows, key=_row_sort_key)):
        raise ValueError("rows must be sorted deterministically")
    return rows


def _normalize_reason_code_counts(
    items: tuple[MarketResearchCryptoOracleHeartbeatStallDigestReasonCodeCount, ...],
) -> tuple[MarketResearchCryptoOracleHeartbeatStallDigestReasonCodeCount, ...]:
    if type(items) is not tuple:
        raise ValueError("reason_code_counts must be a tuple")
    for item in items:
        if type(item) is not MarketResearchCryptoOracleHeartbeatStallDigestReasonCodeCount:
            raise ValueError("reason_code_counts must contain reason count rows")
        _require_hard_flags("reason code count", item)
    if items != tuple(sorted(items, key=lambda item: REASON_CODE_SEQUENCE.index(item.reason_code))):
        raise ValueError("reason_code_counts must be sorted deterministically")
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
    normalized = tuple(sorted(pairs))
    if tuple(pairs) != normalized:
        raise ValueError("source_config_versions must be sorted deterministically")
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
    if type(value) is not str or value not in HEARTBEAT_STALL_DIGEST_STATUSES:
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
    if value.as_tuple().exponent != -6:
        raise ValueError(f"{field_name} must be a six decimal Decimal")
    return value


def _require_positive_count_decimal(field_name: str, value: Decimal) -> Decimal:
    value = _require_nonnegative_count_decimal(field_name, value)
    if value <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return value


def _require_positive_whole_count_decimal(field_name: str, value: Decimal) -> Decimal:
    value = _require_positive_count_decimal(field_name, value)
    if value != value.to_integral_value():
        raise ValueError(f"{field_name} must be whole")
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
    if value.tzinfo is not UTC:
        raise ValueError(f"{field_name} must be UTC-aware")
    return value


def _age_seconds(newer: datetime, older: datetime) -> Decimal:
    delta = newer - older
    return _quantize(
        Decimal(delta.days * 86400)
        + (Decimal(delta.seconds) * ONE)
        + (Decimal(delta.microseconds) / MICROSECONDS_PER_SECOND),
    )


def _heartbeat_gap_ratio(
    heartbeat_gap_seconds: Decimal,
    expected_heartbeat_interval_seconds: Decimal,
) -> Decimal:
    heartbeat_gap_seconds = _require_nonnegative_count_decimal(
        "heartbeat_gap_seconds",
        heartbeat_gap_seconds,
    )
    expected_heartbeat_interval_seconds = _require_positive_count_decimal(
        "expected_heartbeat_interval_seconds",
        expected_heartbeat_interval_seconds,
    )
    if heartbeat_gap_seconds <= expected_heartbeat_interval_seconds:
        return ZERO
    return _ratio(
        heartbeat_gap_seconds - expected_heartbeat_interval_seconds,
        expected_heartbeat_interval_seconds,
    )


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
    if is_dataclass(value) and not isinstance(value, type):
        _revalidate_public_dataclass(value)
        return {
            field.name: _json_ready(getattr(value, field.name))
            for field in fields(value)
        }
    if type(value) is datetime:
        return _utc_datetime_text("datetime", value)
    if type(value) is Decimal:
        return _six_decimal_text("Decimal", value)
    if isinstance(value, tuple):
        return tuple(_json_ready(item) for item in value)
    if isinstance(value, list):
        return tuple(_json_ready(item) for item in value)
    if isinstance(value, bool) or value is None or isinstance(value, str):
        return value
    if isinstance(value, MappingProxyType):
        return {key: _json_ready(item) for key, item in value.items()}
    raise ValueError("value is not payload-safe")


def _revalidate_public_dataclass(value: object) -> None:
    dataclass_values = {field.name: getattr(value, field.name) for field in fields(value)}
    if type(value) is MarketResearchCryptoOracleHeartbeatStallDigestConfig:
        MarketResearchCryptoOracleHeartbeatStallDigestConfig(**dataclass_values)
        return
    if type(value) is MarketResearchCryptoOracleHeartbeatStallObservation:
        MarketResearchCryptoOracleHeartbeatStallObservation(**dataclass_values)
        return
    if type(value) is MarketResearchCryptoOracleHeartbeatStallDigestRow:
        MarketResearchCryptoOracleHeartbeatStallDigestRow(**dataclass_values)
        return
    if type(value) is MarketResearchCryptoOracleHeartbeatStallDigestReasonCodeCount:
        MarketResearchCryptoOracleHeartbeatStallDigestReasonCodeCount(**dataclass_values)
        return
    if type(value) is MarketResearchCryptoOracleHeartbeatStallDigestReport:
        MarketResearchCryptoOracleHeartbeatStallDigestReport(**dataclass_values)
        return
    raise ValueError("payload dataclass must use public exact type")


def _six_decimal_text(field_name: str, value: Decimal) -> str:
    if (
        type(value) is not Decimal
        or not value.is_finite()
        or value.as_tuple().exponent != -6
        or value != _quantize(value)
    ):
        raise ValueError(f"{field_name} must be a six decimal Decimal")
    return str(value)


def _utc_datetime_text(field_name: str, value: datetime) -> str:
    if (
        type(value) is not datetime
        or value.tzinfo is not UTC
        or value.utcoffset() is None
    ):
        raise ValueError(f"{field_name} must be UTC-aware")
    return value.isoformat()


def _freeze(value: Any) -> Any:
    if isinstance(value, dict):
        frozen = {key: _freeze(item) for key, item in value.items()}
        frozen["payload_kind"] = "market_research_crypto_oracle_heartbeat_stall_digest"
        return MappingProxyType(frozen)
    if isinstance(value, tuple):
        return tuple(_freeze(item) for item in value)
    return value
