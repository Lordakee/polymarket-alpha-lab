"""Pure Phase 1 crypto bridge finality dispute market research reducer."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from types import MappingProxyType
from typing import Any


DEFAULT_MARKET_RESEARCH_CRYPTO_BRIDGE_FINALITY_DISPUTE_DIGEST_CONFIG_VERSION = (
    "market-research-crypto-bridge-finality-dispute-digest-v0"
)

STATUS_READY = "ready"
STATUS_WATCH = "watch"
STATUS_BLOCKED = "blocked"
BRIDGE_FINALITY_DISPUTE_DIGEST_STATUSES = (
    STATUS_READY,
    STATUS_WATCH,
    STATUS_BLOCKED,
)

READY_REASON = "market_research_crypto_bridge_finality_dispute_digest_ready"
NO_INPUTS_REASON = "market_research_crypto_bridge_finality_dispute_digest_no_inputs"
FINALITY_LAG_REASON = (
    "market_research_crypto_bridge_finality_dispute_digest_finality_lag"
)
FINALITY_EXPANSION_REASON = (
    "market_research_crypto_bridge_finality_dispute_digest_finality_expansion"
)
DISPUTE_WINDOW_REASON = (
    "market_research_crypto_bridge_finality_dispute_digest_dispute_window"
)
CHALLENGE_PRESSURE_REASON = (
    "market_research_crypto_bridge_finality_dispute_digest_challenge_pressure"
)
SOURCE_DIVERSITY_GAP_REASON = (
    "market_research_crypto_bridge_finality_dispute_digest_source_diversity_gap"
)
STALE_OBSERVATION_REASON = (
    "market_research_crypto_bridge_finality_dispute_digest_stale_observation"
)
CONFIDENCE_GAP_REASON = (
    "market_research_crypto_bridge_finality_dispute_digest_confidence_gap"
)

REASON_CODE_SEQUENCE = (
    FINALITY_LAG_REASON,
    FINALITY_EXPANSION_REASON,
    DISPUTE_WINDOW_REASON,
    CHALLENGE_PRESSURE_REASON,
    SOURCE_DIVERSITY_GAP_REASON,
    STALE_OBSERVATION_REASON,
    CONFIDENCE_GAP_REASON,
    READY_REASON,
    NO_INPUTS_REASON,
)
ROW_REASON_CODE_SEQUENCE = (
    FINALITY_LAG_REASON,
    FINALITY_EXPANSION_REASON,
    DISPUTE_WINDOW_REASON,
    CHALLENGE_PRESSURE_REASON,
    SOURCE_DIVERSITY_GAP_REASON,
    STALE_OBSERVATION_REASON,
    CONFIDENCE_GAP_REASON,
    READY_REASON,
)
BLOCKING_REASON_CODES = (
    FINALITY_LAG_REASON,
    DISPUTE_WINDOW_REASON,
    CHALLENGE_PRESSURE_REASON,
    STALE_OBSERVATION_REASON,
    CONFIDENCE_GAP_REASON,
)

DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
QUANT = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
TWO = Decimal("2.000000")
MICROSECONDS_PER_SECOND = Decimal("1000000")


def _join_parts(*parts: str) -> str:
    return "".join(parts)


UNSAFE_TEXT_FRAGMENTS = frozenset(
    (
        _join_parts("mar", "ket", "_", "slug"),
        _join_parts("ques", "tion"),
        _join_parts("wa", "llet"),
        _join_parts("or", "der"),
        _join_parts("au", "th"),
        _join_parts("to", "ken"),
        _join_parts("sec", "ret"),
        _join_parts("pri", "vate"),
        _join_parts("acc", "ount"),
        _join_parts("tra", "de"),
        _join_parts("0", "x"),
    ),
)

__all__ = (
    "DEFAULT_MARKET_RESEARCH_CRYPTO_BRIDGE_FINALITY_DISPUTE_DIGEST_CONFIG_VERSION",
    "MarketResearchCryptoBridgeFinalityDisputeDigestConfig",
    "MarketResearchCryptoBridgeFinalityDisputeDigestReasonCodeCount",
    "MarketResearchCryptoBridgeFinalityDisputeDigestReport",
    "MarketResearchCryptoBridgeFinalityDisputeDigestRow",
    "MarketResearchCryptoBridgeFinalityDisputeObservation",
    "build_market_research_crypto_bridge_finality_dispute_digest",
    "market_research_crypto_bridge_finality_dispute_digest_payload",
)


@dataclass(frozen=True)
class MarketResearchCryptoBridgeFinalityDisputeDigestConfig:
    config_version: str = (
        DEFAULT_MARKET_RESEARCH_CRYPTO_BRIDGE_FINALITY_DISPUTE_DIGEST_CONFIG_VERSION
    )
    max_observation_age_seconds: Decimal = Decimal("1800.000000")
    max_finality_lag_seconds: Decimal = Decimal("900.000000")
    max_finality_expansion_ratio: Decimal = Decimal("0.500000")
    max_dispute_window_seconds: Decimal = Decimal("3600.000000")
    max_challenge_ratio: Decimal = Decimal("0.050000")
    min_source_count: Decimal = Decimal("3.000000")
    min_confidence: Decimal = Decimal("0.700000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketResearchCryptoBridgeFinalityDisputeDigestConfig:
            raise TypeError(
                "MarketResearchCryptoBridgeFinalityDisputeDigestConfig "
                "does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not MarketResearchCryptoBridgeFinalityDisputeDigestConfig:
            raise ValueError(
                "config must be exactly "
                "MarketResearchCryptoBridgeFinalityDisputeDigestConfig",
            )
        _require_canonical_string("config_version", self.config_version)
        for field_name in (
            "max_observation_age_seconds",
            "max_finality_lag_seconds",
            "max_dispute_window_seconds",
            "min_source_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_positive_count_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "max_finality_expansion_ratio",
            "max_challenge_ratio",
            "min_confidence",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class MarketResearchCryptoBridgeFinalityDisputeObservation:
    condition_id: str
    bridge_finality_key: str
    bridge_name: str
    source_chain: str
    destination_chain: str
    observed_at: datetime
    finality_lag_seconds: Decimal
    baseline_finality_seconds: Decimal
    dispute_window_seconds: Decimal
    challenged_transfer_count: Decimal
    finalized_transfer_count: Decimal
    source_count: Decimal
    confidence: Decimal
    source_config_version: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketResearchCryptoBridgeFinalityDisputeObservation:
            raise TypeError(
                "MarketResearchCryptoBridgeFinalityDisputeObservation "
                "does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not MarketResearchCryptoBridgeFinalityDisputeObservation:
            raise ValueError(
                "observation must be exactly "
                "MarketResearchCryptoBridgeFinalityDisputeObservation",
            )
        for field_name in (
            "condition_id",
            "bridge_finality_key",
            "source_chain",
            "destination_chain",
            "source_config_version",
        ):
            _require_public_string(field_name, getattr(self, field_name))
        _require_canonical_string("bridge_name", self.bridge_name)
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in (
            "finality_lag_seconds",
            "baseline_finality_seconds",
            "dispute_window_seconds",
            "challenged_transfer_count",
            "finalized_transfer_count",
            "source_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_count_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "confidence",
            _require_ratio_decimal("confidence", self.confidence),
        )
        _validate_observation(self)
        _require_hard_flags("observation", self)


@dataclass(frozen=True)
class MarketResearchCryptoBridgeFinalityDisputeDigestRow:
    condition_id: str
    bridge_finality_key: str
    bridge_name: str
    source_chain: str
    destination_chain: str
    digest_status: str
    observed_at: datetime
    observation_age_seconds: Decimal
    finality_lag_seconds: Decimal
    baseline_finality_seconds: Decimal
    finality_expansion_ratio: Decimal
    dispute_window_seconds: Decimal
    challenged_transfer_count: Decimal
    finalized_transfer_count: Decimal
    challenge_ratio: Decimal
    source_count: Decimal
    confidence: Decimal
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketResearchCryptoBridgeFinalityDisputeDigestRow:
            raise TypeError(
                "MarketResearchCryptoBridgeFinalityDisputeDigestRow "
                "does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not MarketResearchCryptoBridgeFinalityDisputeDigestRow:
            raise ValueError(
                "row must be exactly MarketResearchCryptoBridgeFinalityDisputeDigestRow",
            )
        for field_name in (
            "condition_id",
            "bridge_finality_key",
            "source_chain",
            "destination_chain",
        ):
            _require_public_string(field_name, getattr(self, field_name))
        _require_canonical_string("bridge_name", self.bridge_name)
        _require_status("digest_status", self.digest_status)
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in (
            "observation_age_seconds",
            "finality_lag_seconds",
            "baseline_finality_seconds",
            "dispute_window_seconds",
            "challenged_transfer_count",
            "finalized_transfer_count",
            "source_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_count_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "finality_expansion_ratio",
            _require_nonnegative_count_decimal(
                "finality_expansion_ratio",
                self.finality_expansion_ratio,
            ),
        )
        for field_name in ("challenge_ratio", "confidence"):
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
class MarketResearchCryptoBridgeFinalityDisputeDigestReasonCodeCount:
    reason_code: str
    count: Decimal
    observation_ratio: Decimal

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketResearchCryptoBridgeFinalityDisputeDigestReasonCodeCount:
            raise TypeError(
                "MarketResearchCryptoBridgeFinalityDisputeDigestReasonCodeCount "
                "does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not MarketResearchCryptoBridgeFinalityDisputeDigestReasonCodeCount:
            raise ValueError(
                "reason code count must be exactly "
                "MarketResearchCryptoBridgeFinalityDisputeDigestReasonCodeCount",
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
class MarketResearchCryptoBridgeFinalityDisputeDigestReport:
    generated_at: datetime
    config_version: str
    digest_status: str
    recommended_next_step: str
    observation_count: Decimal
    ready_observation_count: Decimal
    watch_observation_count: Decimal
    blocked_observation_count: Decimal
    finality_lag_observation_count: Decimal
    finality_expansion_observation_count: Decimal
    dispute_window_observation_count: Decimal
    challenge_pressure_observation_count: Decimal
    source_diversity_gap_observation_count: Decimal
    stale_observation_count: Decimal
    confidence_gap_observation_count: Decimal
    average_finality_lag_seconds: Decimal
    average_finality_expansion_ratio: Decimal
    average_challenge_ratio: Decimal
    observed_max_finality_lag_seconds: Decimal
    observed_max_dispute_window_seconds: Decimal
    max_observation_age_seconds: Decimal
    max_allowed_observation_age_seconds: Decimal
    max_allowed_finality_lag_seconds: Decimal
    max_allowed_finality_expansion_ratio: Decimal
    max_allowed_dispute_window_seconds: Decimal
    max_allowed_challenge_ratio: Decimal
    min_source_count: Decimal
    min_confidence: Decimal
    rows: tuple[MarketResearchCryptoBridgeFinalityDisputeDigestRow, ...]
    source_config_versions: tuple[tuple[str, str], ...]
    reason_code_counts: tuple[
        MarketResearchCryptoBridgeFinalityDisputeDigestReasonCodeCount,
        ...,
    ]
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketResearchCryptoBridgeFinalityDisputeDigestReport:
            raise TypeError(
                "MarketResearchCryptoBridgeFinalityDisputeDigestReport "
                "does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not MarketResearchCryptoBridgeFinalityDisputeDigestReport:
            raise ValueError(
                "report must be exactly "
                "MarketResearchCryptoBridgeFinalityDisputeDigestReport",
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
            "finality_lag_observation_count",
            "finality_expansion_observation_count",
            "dispute_window_observation_count",
            "challenge_pressure_observation_count",
            "source_diversity_gap_observation_count",
            "stale_observation_count",
            "confidence_gap_observation_count",
            "average_finality_lag_seconds",
            "average_finality_expansion_ratio",
            "observed_max_finality_lag_seconds",
            "observed_max_dispute_window_seconds",
            "max_observation_age_seconds",
            "max_allowed_observation_age_seconds",
            "max_allowed_finality_lag_seconds",
            "max_allowed_dispute_window_seconds",
            "min_source_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_count_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "average_challenge_ratio",
            "max_allowed_finality_expansion_ratio",
            "max_allowed_challenge_ratio",
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


def build_market_research_crypto_bridge_finality_dispute_digest(
    observations: Iterable[MarketResearchCryptoBridgeFinalityDisputeObservation],
    *,
    config: MarketResearchCryptoBridgeFinalityDisputeDigestConfig | None = None,
    generated_at: datetime,
) -> MarketResearchCryptoBridgeFinalityDisputeDigestReport:
    cfg = config or MarketResearchCryptoBridgeFinalityDisputeDigestConfig()
    if type(cfg) is not MarketResearchCryptoBridgeFinalityDisputeDigestConfig:
        raise ValueError(
            "config must be exactly "
            "MarketResearchCryptoBridgeFinalityDisputeDigestConfig",
        )
    generated_at_utc = _as_utc("generated_at", generated_at)
    normalized_observations = _normalize_observations(observations)
    rows = tuple(
        _row_for_observation(
            observation,
            config=cfg,
            generated_at=generated_at_utc,
        )
        for observation in normalized_observations
    )
    sorted_rows = tuple(
        sorted(
            rows,
            key=lambda row: (
                _row_status_rank(row),
                -_row_severity(row),
                row.bridge_finality_key,
                row.condition_id,
            ),
        ),
    )
    report_status = _report_status(sorted_rows)
    observation_count = _decimal_count(len(sorted_rows))
    return MarketResearchCryptoBridgeFinalityDisputeDigestReport(
        generated_at=generated_at_utc,
        config_version=cfg.config_version,
        digest_status=report_status,
        recommended_next_step=_recommended_next_step(report_status),
        observation_count=observation_count,
        ready_observation_count=_status_count(sorted_rows, STATUS_READY),
        watch_observation_count=_status_count(sorted_rows, STATUS_WATCH),
        blocked_observation_count=_status_count(sorted_rows, STATUS_BLOCKED),
        finality_lag_observation_count=_reason_observation_count(
            sorted_rows,
            FINALITY_LAG_REASON,
        ),
        finality_expansion_observation_count=_reason_observation_count(
            sorted_rows,
            FINALITY_EXPANSION_REASON,
        ),
        dispute_window_observation_count=_reason_observation_count(
            sorted_rows,
            DISPUTE_WINDOW_REASON,
        ),
        challenge_pressure_observation_count=_reason_observation_count(
            sorted_rows,
            CHALLENGE_PRESSURE_REASON,
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
        average_finality_lag_seconds=_ratio(
            _decimal_sum(row.finality_lag_seconds for row in sorted_rows),
            observation_count,
        ),
        average_finality_expansion_ratio=_ratio(
            _decimal_sum(row.finality_expansion_ratio for row in sorted_rows),
            observation_count,
        ),
        average_challenge_ratio=_ratio(
            _decimal_sum(row.challenge_ratio for row in sorted_rows),
            observation_count,
        ),
        observed_max_finality_lag_seconds=max(
            (row.finality_lag_seconds for row in sorted_rows),
            default=ZERO,
        ),
        observed_max_dispute_window_seconds=max(
            (row.dispute_window_seconds for row in sorted_rows),
            default=ZERO,
        ),
        max_observation_age_seconds=max(
            (row.observation_age_seconds for row in sorted_rows),
            default=ZERO,
        ),
        max_allowed_observation_age_seconds=cfg.max_observation_age_seconds,
        max_allowed_finality_lag_seconds=cfg.max_finality_lag_seconds,
        max_allowed_finality_expansion_ratio=cfg.max_finality_expansion_ratio,
        max_allowed_dispute_window_seconds=cfg.max_dispute_window_seconds,
        max_allowed_challenge_ratio=cfg.max_challenge_ratio,
        min_source_count=cfg.min_source_count,
        min_confidence=cfg.min_confidence,
        rows=sorted_rows,
        source_config_versions=tuple(
            sorted(
                (
                    observation.bridge_finality_key,
                    observation.source_config_version,
                )
                for observation in normalized_observations
            ),
        ),
        reason_code_counts=_reason_code_counts(sorted_rows),
        reason_codes=_summary_reason_codes(sorted_rows),
    )


def market_research_crypto_bridge_finality_dispute_digest_payload(
    report: MarketResearchCryptoBridgeFinalityDisputeDigestReport,
) -> MappingProxyType[str, Any]:
    if type(report) is not MarketResearchCryptoBridgeFinalityDisputeDigestReport:
        raise ValueError(
            "report must be exactly "
            "MarketResearchCryptoBridgeFinalityDisputeDigestReport",
        )
    payload = {
        "payload_kind": "market_research_crypto_bridge_finality_dispute_digest",
        **_json_ready(report),
    }
    frozen = _freeze(payload)
    _reject_unsafe_payload(frozen)
    return frozen


def _row_for_observation(
    observation: MarketResearchCryptoBridgeFinalityDisputeObservation,
    *,
    config: MarketResearchCryptoBridgeFinalityDisputeDigestConfig,
    generated_at: datetime,
) -> MarketResearchCryptoBridgeFinalityDisputeDigestRow:
    if observation.observed_at > generated_at:
        raise ValueError("observed_at must not be in the future")
    observation_age_seconds = _age_seconds(generated_at, observation.observed_at)
    finality_expansion_ratio = _expansion_ratio(
        observation.finality_lag_seconds,
        observation.baseline_finality_seconds,
    )
    challenge_ratio = _ratio(
        observation.challenged_transfer_count,
        observation.finalized_transfer_count,
    )
    reason_codes = _row_reason_codes(
        observation=observation,
        config=config,
        observation_age_seconds=observation_age_seconds,
        finality_expansion_ratio=finality_expansion_ratio,
        challenge_ratio=challenge_ratio,
    )
    return MarketResearchCryptoBridgeFinalityDisputeDigestRow(
        condition_id=observation.condition_id,
        bridge_finality_key=observation.bridge_finality_key,
        bridge_name=observation.bridge_name,
        source_chain=observation.source_chain,
        destination_chain=observation.destination_chain,
        digest_status=_row_status(reason_codes),
        observed_at=observation.observed_at,
        observation_age_seconds=observation_age_seconds,
        finality_lag_seconds=observation.finality_lag_seconds,
        baseline_finality_seconds=observation.baseline_finality_seconds,
        finality_expansion_ratio=finality_expansion_ratio,
        dispute_window_seconds=observation.dispute_window_seconds,
        challenged_transfer_count=observation.challenged_transfer_count,
        finalized_transfer_count=observation.finalized_transfer_count,
        challenge_ratio=challenge_ratio,
        source_count=observation.source_count,
        confidence=observation.confidence,
        reason_codes=reason_codes,
    )


def _row_reason_codes(
    *,
    observation: MarketResearchCryptoBridgeFinalityDisputeObservation,
    config: MarketResearchCryptoBridgeFinalityDisputeDigestConfig,
    observation_age_seconds: Decimal,
    finality_expansion_ratio: Decimal,
    challenge_ratio: Decimal,
) -> tuple[str, ...]:
    reasons: list[str] = []
    if observation.finality_lag_seconds > config.max_finality_lag_seconds:
        reasons.append(FINALITY_LAG_REASON)
    if finality_expansion_ratio > config.max_finality_expansion_ratio:
        reasons.append(FINALITY_EXPANSION_REASON)
    if observation.dispute_window_seconds > config.max_dispute_window_seconds:
        reasons.append(DISPUTE_WINDOW_REASON)
    if challenge_ratio > config.max_challenge_ratio:
        reasons.append(CHALLENGE_PRESSURE_REASON)
    if observation.source_count < config.min_source_count:
        reasons.append(SOURCE_DIVERSITY_GAP_REASON)
    if observation_age_seconds > config.max_observation_age_seconds:
        reasons.append(STALE_OBSERVATION_REASON)
    if observation.confidence < config.min_confidence:
        reasons.append(CONFIDENCE_GAP_REASON)
    if not reasons:
        reasons.append(READY_REASON)
    return tuple(reason for reason in ROW_REASON_CODE_SEQUENCE if reason in reasons)


def _row_status(reason_codes: tuple[str, ...]) -> str:
    if reason_codes == (READY_REASON,):
        return STATUS_READY
    if any(reason in reason_codes for reason in BLOCKING_REASON_CODES):
        return STATUS_BLOCKED
    return STATUS_WATCH


def _report_status(
    rows: tuple[MarketResearchCryptoBridgeFinalityDisputeDigestRow, ...],
) -> str:
    if not rows:
        return STATUS_WATCH
    if any(row.digest_status == STATUS_BLOCKED for row in rows):
        return STATUS_BLOCKED
    if any(row.digest_status == STATUS_WATCH for row in rows):
        return STATUS_WATCH
    return STATUS_READY


def _recommended_next_step(status: str) -> str:
    if status == STATUS_BLOCKED:
        return "block_report_only_market_research_crypto_bridge_finality_dispute_digest"
    if status == STATUS_WATCH:
        return "review_report_only_market_research_crypto_bridge_finality_dispute_digest"
    return "allow_report_only_market_research_crypto_bridge_finality_dispute_digest"


def _status_count(
    rows: tuple[MarketResearchCryptoBridgeFinalityDisputeDigestRow, ...],
    status: str,
) -> Decimal:
    return _decimal_count(sum(row.digest_status == status for row in rows))


def _reason_observation_count(
    rows: tuple[MarketResearchCryptoBridgeFinalityDisputeDigestRow, ...],
    reason_code: str,
) -> Decimal:
    return _decimal_count(sum(reason_code in row.reason_codes for row in rows))


def _reason_code_counts(
    rows: tuple[MarketResearchCryptoBridgeFinalityDisputeDigestRow, ...],
) -> tuple[MarketResearchCryptoBridgeFinalityDisputeDigestReasonCodeCount, ...]:
    observation_count = _decimal_count(len(rows))
    counts: dict[str, Decimal] = {}
    for row in rows:
        for reason_code in row.reason_codes:
            counts[reason_code] = _quantize(counts.get(reason_code, ZERO) + ONE)
    return tuple(
        MarketResearchCryptoBridgeFinalityDisputeDigestReasonCodeCount(
            reason_code=reason_code,
            count=counts[reason_code],
            observation_ratio=_ratio(counts[reason_code], observation_count),
        )
        for reason_code in REASON_CODE_SEQUENCE
        if reason_code in counts
    )


def _summary_reason_codes(
    rows: tuple[MarketResearchCryptoBridgeFinalityDisputeDigestRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return (NO_INPUTS_REASON,)
    seen: set[str] = set()
    for row in rows:
        seen.update(row.reason_codes)
    if len(seen) > len((READY_REASON,)) and READY_REASON in seen:
        seen.remove(READY_REASON)
    return tuple(reason for reason in REASON_CODE_SEQUENCE if reason in seen)


def _row_status_rank(
    row: MarketResearchCryptoBridgeFinalityDisputeDigestRow,
) -> Decimal:
    if row.digest_status == STATUS_BLOCKED:
        return ZERO
    if row.digest_status == STATUS_WATCH:
        return ONE
    return TWO


def _row_severity(row: MarketResearchCryptoBridgeFinalityDisputeDigestRow) -> Decimal:
    return _decimal_count(sum(reason != READY_REASON for reason in row.reason_codes))


def _validate_observation(
    observation: MarketResearchCryptoBridgeFinalityDisputeObservation,
) -> None:
    if observation.challenged_transfer_count > observation.finalized_transfer_count:
        raise ValueError(
            "challenged_transfer_count must not exceed finalized_transfer_count",
        )


def _validate_row(row: MarketResearchCryptoBridgeFinalityDisputeDigestRow) -> None:
    if row.challenged_transfer_count > row.finalized_transfer_count:
        raise ValueError(
            "challenged_transfer_count must not exceed finalized_transfer_count",
        )
    if row.finality_expansion_ratio != _expansion_ratio(
        row.finality_lag_seconds,
        row.baseline_finality_seconds,
    ):
        raise ValueError("finality_expansion_ratio does not match finality inputs")
    if row.challenge_ratio != _ratio(
        row.challenged_transfer_count,
        row.finalized_transfer_count,
    ):
        raise ValueError("challenge_ratio does not match transfer inputs")
    if row.digest_status != _row_status(row.reason_codes):
        raise ValueError("digest_status does not match reason_codes")


def _validate_report(report: MarketResearchCryptoBridgeFinalityDisputeDigestReport) -> None:
    rows = report.rows
    if report.observation_count != _decimal_count(len(rows)):
        raise ValueError("observation_count does not match rows")
    if report.ready_observation_count != _status_count(rows, STATUS_READY):
        raise ValueError("ready_observation_count does not match rows")
    if report.watch_observation_count != _status_count(rows, STATUS_WATCH):
        raise ValueError("watch_observation_count does not match rows")
    if report.blocked_observation_count != _status_count(rows, STATUS_BLOCKED):
        raise ValueError("blocked_observation_count does not match rows")
    expected_counts = (
        (FINALITY_LAG_REASON, report.finality_lag_observation_count),
        (FINALITY_EXPANSION_REASON, report.finality_expansion_observation_count),
        (DISPUTE_WINDOW_REASON, report.dispute_window_observation_count),
        (CHALLENGE_PRESSURE_REASON, report.challenge_pressure_observation_count),
        (SOURCE_DIVERSITY_GAP_REASON, report.source_diversity_gap_observation_count),
        (STALE_OBSERVATION_REASON, report.stale_observation_count),
        (CONFIDENCE_GAP_REASON, report.confidence_gap_observation_count),
    )
    for reason_code, count in expected_counts:
        if count != _reason_observation_count(rows, reason_code):
            raise ValueError("reason observation count does not match rows")
    if report.digest_status != _report_status(rows):
        raise ValueError("digest_status does not match rows")
    if report.recommended_next_step != _recommended_next_step(report.digest_status):
        raise ValueError("recommended_next_step does not match digest_status")
    if report.average_finality_lag_seconds != _ratio(
        _decimal_sum(row.finality_lag_seconds for row in rows),
        report.observation_count,
    ):
        raise ValueError("average_finality_lag_seconds does not match rows")
    if report.average_finality_expansion_ratio != _ratio(
        _decimal_sum(row.finality_expansion_ratio for row in rows),
        report.observation_count,
    ):
        raise ValueError("average_finality_expansion_ratio does not match rows")
    if report.average_challenge_ratio != _ratio(
        _decimal_sum(row.challenge_ratio for row in rows),
        report.observation_count,
    ):
        raise ValueError("average_challenge_ratio does not match rows")
    if report.observed_max_finality_lag_seconds != max(
        (row.finality_lag_seconds for row in rows),
        default=ZERO,
    ):
        raise ValueError("observed_max_finality_lag_seconds does not match rows")
    if report.observed_max_dispute_window_seconds != max(
        (row.dispute_window_seconds for row in rows),
        default=ZERO,
    ):
        raise ValueError("observed_max_dispute_window_seconds does not match rows")
    if report.max_observation_age_seconds != max(
        (row.observation_age_seconds for row in rows),
        default=ZERO,
    ):
        raise ValueError("max_observation_age_seconds does not match rows")
    if report.reason_code_counts != _reason_code_counts(rows):
        raise ValueError("reason_code_counts do not match rows")
    if report.reason_codes != _summary_reason_codes(rows):
        raise ValueError("reason_codes do not match rows")


def _normalize_observations(
    observations: Iterable[MarketResearchCryptoBridgeFinalityDisputeObservation],
) -> tuple[MarketResearchCryptoBridgeFinalityDisputeObservation, ...]:
    if isinstance(observations, (str, bytes)):
        raise ValueError("observations must be an iterable of observation rows")
    observation_tuple = tuple(observations)
    seen_keys: set[str] = set()
    for observation in observation_tuple:
        if type(observation) is not MarketResearchCryptoBridgeFinalityDisputeObservation:
            raise ValueError(
                "observations must contain "
                "MarketResearchCryptoBridgeFinalityDisputeObservation",
            )
        if observation.bridge_finality_key in seen_keys:
            raise ValueError("bridge_finality_key values must be unique")
        seen_keys.add(observation.bridge_finality_key)
        _require_hard_flags("observation", observation)
    return observation_tuple


def _normalize_rows(
    rows: tuple[MarketResearchCryptoBridgeFinalityDisputeDigestRow, ...],
) -> tuple[MarketResearchCryptoBridgeFinalityDisputeDigestRow, ...]:
    if type(rows) is not tuple:
        raise ValueError("rows must be a tuple")
    for row in rows:
        if type(row) is not MarketResearchCryptoBridgeFinalityDisputeDigestRow:
            raise ValueError(
                "rows must contain MarketResearchCryptoBridgeFinalityDisputeDigestRow",
            )
        _require_hard_flags("row", row)
    return rows


def _normalize_reason_code_counts(
    items: tuple[
        MarketResearchCryptoBridgeFinalityDisputeDigestReasonCodeCount,
        ...,
    ],
) -> tuple[MarketResearchCryptoBridgeFinalityDisputeDigestReasonCodeCount, ...]:
    if type(items) is not tuple:
        raise ValueError("reason_code_counts must be a tuple")
    for item in items:
        if type(item) is not MarketResearchCryptoBridgeFinalityDisputeDigestReasonCodeCount:
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
        if type(item) is not tuple or len(item) != len(("key", "version")):
            raise ValueError("source_config_versions must contain pairs")
        bridge_finality_key, source_config_version = item
        _require_public_string("bridge_finality_key", bridge_finality_key)
        _require_public_string("source_config_version", source_config_version)
        if bridge_finality_key in seen_keys:
            raise ValueError(
                "source_config_versions bridge_finality_key values must be unique",
            )
        seen_keys.add(bridge_finality_key)
        pairs.append((bridge_finality_key, source_config_version))
    normalized = tuple(sorted(pairs))
    if normalized != value:
        raise ValueError("source_config_versions must be deterministic")
    return value


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
    if type(value) is not str or value not in BRIDGE_FINALITY_DISPUTE_DIGEST_STATUSES:
        raise ValueError(f"{field_name} must be a supported status")


def _require_reason_code(field_name: str, value: str) -> None:
    if type(value) is not str or value not in REASON_CODE_SEQUENCE:
        raise ValueError(f"{field_name} must be a supported reason code")


def _require_canonical_string(field_name: str, value: str) -> None:
    if type(value) is not str or not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical string")
    _require_public_text(field_name, value)


def _require_public_string(field_name: str, value: str) -> None:
    _require_canonical_string(field_name, value)
    if any(character.isspace() for character in value):
        raise ValueError(f"{field_name} must not contain whitespace")


def _require_public_text(field_name: str, value: str) -> None:
    lowered = value.lower()
    if any(fragment in lowered for fragment in UNSAFE_TEXT_FRAGMENTS):
        raise ValueError(f"{field_name} must be redacted")


def _require_hard_flags(field_name: str, value: object) -> None:
    for flag in ("paper_only", "report_only", "readonly"):
        if getattr(value, flag, None) is not True:
            raise ValueError(f"{field_name} {flag} must be True")


def _require_positive_count_decimal(field_name: str, value: Decimal) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return decimal_value


def _require_nonnegative_count_decimal(field_name: str, value: Decimal) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return decimal_value


def _require_ratio_decimal(field_name: str, value: Decimal) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value < ZERO or decimal_value > ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return decimal_value


def _require_decimal(field_name: str, value: Decimal) -> Decimal:
    if type(value) is not Decimal or not value.is_finite():
        raise ValueError(f"{field_name} must be a finite Decimal")
    return _quantize(value)


def _as_utc(field_name: str, value: datetime) -> datetime:
    if type(value) is not datetime or value.tzinfo is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    if value.utcoffset() is None:
        raise ValueError(f"{field_name} must have a non-None UTC offset")
    return value.astimezone(UTC)


def _age_seconds(generated_at: datetime, observed_at: datetime) -> Decimal:
    delta = generated_at - observed_at
    return _quantize(
        Decimal(delta.days * 86400 + delta.seconds)
        + (Decimal(delta.microseconds) / MICROSECONDS_PER_SECOND),
    )


def _expansion_ratio(current: Decimal, baseline: Decimal) -> Decimal:
    if baseline == ZERO:
        return ZERO
    ratio = current / baseline - ONE
    if ratio <= ZERO:
        return ZERO
    return _quantize(ratio)


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
    return _quantize(numerator / denominator)


def _quantize(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(QUANT)


def _json_ready(value: object) -> Any:
    if isinstance(value, Decimal):
        return f"{value:.6f}"
    if type(value) is datetime:
        return value.isoformat()
    if is_dataclass(value) and not isinstance(value, type):
        return {field.name: _json_ready(getattr(value, field.name)) for field in fields(value)}
    if type(value) is tuple:
        return [_json_ready(item) for item in value]
    return value


def _freeze(value: object) -> Any:
    if isinstance(value, dict):
        return MappingProxyType({key: _freeze(item) for key, item in value.items()})
    if isinstance(value, list):
        return tuple(_freeze(item) for item in value)
    return value


def _reject_unsafe_payload(value: object) -> None:
    if isinstance(value, MappingProxyType):
        for key, item in value.items():
            _require_public_text("payload key", key)
            _reject_unsafe_payload(item)
        return
    if isinstance(value, dict):
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("payload keys must be strings")
            _require_public_text("payload key", key)
            _reject_unsafe_payload(item)
        return
    if isinstance(value, tuple):
        for item in value:
            _reject_unsafe_payload(item)
        return
    if isinstance(value, str):
        _require_public_text("payload value", value)
        return
    if isinstance(value, Decimal):
        raise ValueError("payload must serialize Decimal values")
    if isinstance(value, float):
        raise ValueError("payload must not contain float values")
    if isinstance(value, int) and not isinstance(value, bool):
        raise ValueError("payload must not contain integer values")
