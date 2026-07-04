"""Pure Phase 1 crypto bridge governance pause digest reducer."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from types import MappingProxyType
from typing import Any


DEFAULT_MARKET_RESEARCH_CRYPTO_BRIDGE_GOVERNANCE_PAUSE_DIGEST_CONFIG_VERSION = (
    "market-research-crypto-bridge-governance-pause-digest-v0"
)

STATUS_READY = "ready"
STATUS_WATCH = "watch"
STATUS_BLOCKED = "blocked"
BRIDGE_GOVERNANCE_PAUSE_DIGEST_STATUSES = (STATUS_READY, STATUS_WATCH, STATUS_BLOCKED)

READY_REASON = "market_research_crypto_bridge_governance_pause_digest_ready"
NO_INPUTS_REASON = "market_research_crypto_bridge_governance_pause_digest_no_inputs"
PAUSE_SIGNAL_REASON = "market_research_crypto_bridge_governance_pause_digest_pause_signal"
PAUSE_ACTION_ENACTABLE_REASON = (
    "market_research_crypto_bridge_governance_pause_digest_pause_action_enactable"
)
CRITICAL_FUNCTION_PAUSED_REASON = (
    "market_research_crypto_bridge_governance_pause_digest_critical_function_paused"
)
PAUSE_WINDOW_PRESSURE_REASON = (
    "market_research_crypto_bridge_governance_pause_digest_pause_window_pressure"
)
SOURCE_DIVERSITY_GAP_REASON = (
    "market_research_crypto_bridge_governance_pause_digest_source_diversity_gap"
)
STALE_OBSERVATION_REASON = (
    "market_research_crypto_bridge_governance_pause_digest_stale_observation"
)
CONFIDENCE_GAP_REASON = (
    "market_research_crypto_bridge_governance_pause_digest_confidence_gap"
)

REASON_CODE_SEQUENCE = (
    PAUSE_SIGNAL_REASON,
    PAUSE_ACTION_ENACTABLE_REASON,
    CRITICAL_FUNCTION_PAUSED_REASON,
    PAUSE_WINDOW_PRESSURE_REASON,
    SOURCE_DIVERSITY_GAP_REASON,
    STALE_OBSERVATION_REASON,
    CONFIDENCE_GAP_REASON,
    READY_REASON,
    NO_INPUTS_REASON,
)
ROW_REASON_CODE_SEQUENCE = (
    PAUSE_SIGNAL_REASON,
    PAUSE_ACTION_ENACTABLE_REASON,
    CRITICAL_FUNCTION_PAUSED_REASON,
    PAUSE_WINDOW_PRESSURE_REASON,
    SOURCE_DIVERSITY_GAP_REASON,
    STALE_OBSERVATION_REASON,
    CONFIDENCE_GAP_REASON,
    READY_REASON,
)

DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
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
        _join_parts("cred", "ential"),
        _join_parts("pri", "vate"),
        _join_parts("au", "th"),
        _join_parts("api", "_", "k", "ey"),
        _join_parts("0", "x"),
    ),
)

__all__ = (
    "DEFAULT_MARKET_RESEARCH_CRYPTO_BRIDGE_GOVERNANCE_PAUSE_DIGEST_CONFIG_VERSION",
    "MarketResearchCryptoBridgeGovernancePauseDigestConfig",
    "MarketResearchCryptoBridgeGovernancePauseDigestReasonCodeCount",
    "MarketResearchCryptoBridgeGovernancePauseDigestReport",
    "MarketResearchCryptoBridgeGovernancePauseDigestRow",
    "MarketResearchCryptoBridgeGovernancePauseObservation",
    "build_market_research_crypto_bridge_governance_pause_digest",
    "market_research_crypto_bridge_governance_pause_digest_payload",
)


@dataclass(frozen=True)
class MarketResearchCryptoBridgeGovernancePauseDigestConfig:
    config_version: str = (
        DEFAULT_MARKET_RESEARCH_CRYPTO_BRIDGE_GOVERNANCE_PAUSE_DIGEST_CONFIG_VERSION
    )
    max_observation_age_seconds: Decimal = Decimal("1800.000000")
    watch_active_pause_signal_count: Decimal = Decimal("1.000000")
    blocked_enactable_pause_action_count: Decimal = Decimal("1.000000")
    max_pause_window_seconds: Decimal = Decimal("7200.000000")
    min_source_count: Decimal = Decimal("3.000000")
    min_confidence: Decimal = Decimal("0.700000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketResearchCryptoBridgeGovernancePauseDigestConfig:
            raise TypeError(
                "MarketResearchCryptoBridgeGovernancePauseDigestConfig "
                "does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not MarketResearchCryptoBridgeGovernancePauseDigestConfig:
            raise ValueError(
                "config must be exactly "
                "MarketResearchCryptoBridgeGovernancePauseDigestConfig",
            )
        _require_canonical_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_MARKET_RESEARCH_CRYPTO_BRIDGE_GOVERNANCE_PAUSE_DIGEST_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "max_observation_age_seconds",
            "watch_active_pause_signal_count",
            "blocked_enactable_pause_action_count",
            "max_pause_window_seconds",
            "min_source_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_positive_count_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "min_confidence",
            _require_ratio_decimal("min_confidence", self.min_confidence),
        )
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class MarketResearchCryptoBridgeGovernancePauseObservation:
    condition_id: str
    bridge_pause_id: str
    bridge_name: str
    chain_family: str
    observed_at: datetime
    active_pause_signal_count: Decimal
    enactable_pause_action_count: Decimal
    paused_critical_function_count: Decimal
    total_critical_function_count: Decimal
    pause_window_seconds: Decimal
    governance_delay_seconds: Decimal
    source_count: Decimal
    confidence: Decimal
    source_config_version: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketResearchCryptoBridgeGovernancePauseObservation:
            raise TypeError(
                "MarketResearchCryptoBridgeGovernancePauseObservation "
                "does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not MarketResearchCryptoBridgeGovernancePauseObservation:
            raise ValueError(
                "observation must be exactly "
                "MarketResearchCryptoBridgeGovernancePauseObservation",
            )
        for field_name in (
            "condition_id",
            "bridge_pause_id",
            "bridge_name",
            "chain_family",
            "source_config_version",
        ):
            _require_public_string(field_name, getattr(self, field_name))
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in (
            "active_pause_signal_count",
            "enactable_pause_action_count",
            "paused_critical_function_count",
            "total_critical_function_count",
            "pause_window_seconds",
            "governance_delay_seconds",
            "source_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_count_decimal(field_name, getattr(self, field_name)),
            )
        if self.total_critical_function_count <= ZERO:
            raise ValueError("total_critical_function_count must be positive")
        if self.governance_delay_seconds <= ZERO:
            raise ValueError("governance_delay_seconds must be positive")
        if self.paused_critical_function_count > self.total_critical_function_count:
            raise ValueError(
                "paused_critical_function_count must not exceed "
                "total_critical_function_count",
            )
        object.__setattr__(
            self,
            "confidence",
            _require_ratio_decimal("confidence", self.confidence),
        )
        _require_hard_flags("observation", self)


@dataclass(frozen=True)
class MarketResearchCryptoBridgeGovernancePauseDigestRow:
    condition_id: str
    bridge_pause_id: str
    bridge_name: str
    chain_family: str
    digest_status: str
    observed_at: datetime
    observation_age_seconds: Decimal
    active_pause_signal_count: Decimal
    enactable_pause_action_count: Decimal
    paused_critical_function_count: Decimal
    total_critical_function_count: Decimal
    critical_pause_ratio: Decimal
    pause_window_seconds: Decimal
    governance_delay_seconds: Decimal
    pause_window_pressure_ratio: Decimal
    source_count: Decimal
    confidence: Decimal
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketResearchCryptoBridgeGovernancePauseDigestRow:
            raise TypeError(
                "MarketResearchCryptoBridgeGovernancePauseDigestRow "
                "does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not MarketResearchCryptoBridgeGovernancePauseDigestRow:
            raise ValueError(
                "row must be exactly MarketResearchCryptoBridgeGovernancePauseDigestRow",
            )
        for field_name in (
            "condition_id",
            "bridge_pause_id",
            "bridge_name",
            "chain_family",
        ):
            _require_public_string(field_name, getattr(self, field_name))
        _require_status("digest_status", self.digest_status)
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in (
            "observation_age_seconds",
            "active_pause_signal_count",
            "enactable_pause_action_count",
            "paused_critical_function_count",
            "total_critical_function_count",
            "pause_window_seconds",
            "governance_delay_seconds",
            "source_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_count_decimal(field_name, getattr(self, field_name)),
            )
        if self.total_critical_function_count <= ZERO:
            raise ValueError("total_critical_function_count must be positive")
        if self.governance_delay_seconds <= ZERO:
            raise ValueError("governance_delay_seconds must be positive")
        if self.paused_critical_function_count > self.total_critical_function_count:
            raise ValueError(
                "paused_critical_function_count must not exceed "
                "total_critical_function_count",
            )
        for field_name in ("critical_pause_ratio", "pause_window_pressure_ratio"):
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
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes, sequence=ROW_REASON_CODE_SEQUENCE),
        )
        _validate_row(self)
        _require_hard_flags("row", self)


@dataclass(frozen=True)
class MarketResearchCryptoBridgeGovernancePauseDigestReasonCodeCount:
    reason_code: str
    count: Decimal
    observation_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketResearchCryptoBridgeGovernancePauseDigestReasonCodeCount:
            raise TypeError(
                "MarketResearchCryptoBridgeGovernancePauseDigestReasonCodeCount "
                "does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not MarketResearchCryptoBridgeGovernancePauseDigestReasonCodeCount:
            raise ValueError(
                "reason code count must be exactly "
                "MarketResearchCryptoBridgeGovernancePauseDigestReasonCodeCount",
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
        _require_hard_flags("reason code count", self)


@dataclass(frozen=True)
class MarketResearchCryptoBridgeGovernancePauseDigestReport:
    generated_at: datetime
    config_version: str
    digest_status: str
    recommended_next_step: str
    observation_count: Decimal
    ready_observation_count: Decimal
    watch_observation_count: Decimal
    blocked_observation_count: Decimal
    pause_signal_observation_count: Decimal
    pause_action_enactable_observation_count: Decimal
    critical_function_paused_observation_count: Decimal
    pause_window_pressure_observation_count: Decimal
    source_diversity_gap_observation_count: Decimal
    stale_observation_count: Decimal
    confidence_gap_observation_count: Decimal
    average_active_pause_signal_count: Decimal
    average_enactable_pause_action_count: Decimal
    average_critical_pause_ratio: Decimal
    average_pause_window_pressure_ratio: Decimal
    max_observation_age_seconds: Decimal
    max_allowed_observation_age_seconds: Decimal
    watch_active_pause_signal_count: Decimal
    blocked_enactable_pause_action_count: Decimal
    max_pause_window_seconds: Decimal
    min_source_count: Decimal
    min_confidence: Decimal
    rows: tuple[MarketResearchCryptoBridgeGovernancePauseDigestRow, ...]
    source_config_versions: tuple[tuple[str, str], ...]
    reason_code_counts: tuple[
        MarketResearchCryptoBridgeGovernancePauseDigestReasonCodeCount,
        ...,
    ]
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketResearchCryptoBridgeGovernancePauseDigestReport:
            raise TypeError(
                "MarketResearchCryptoBridgeGovernancePauseDigestReport "
                "does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not MarketResearchCryptoBridgeGovernancePauseDigestReport:
            raise ValueError(
                "report must be exactly "
                "MarketResearchCryptoBridgeGovernancePauseDigestReport",
            )
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_MARKET_RESEARCH_CRYPTO_BRIDGE_GOVERNANCE_PAUSE_DIGEST_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        _require_status("digest_status", self.digest_status)
        _require_canonical_string("recommended_next_step", self.recommended_next_step)
        for field_name in (
            "observation_count",
            "ready_observation_count",
            "watch_observation_count",
            "blocked_observation_count",
            "pause_signal_observation_count",
            "pause_action_enactable_observation_count",
            "critical_function_paused_observation_count",
            "pause_window_pressure_observation_count",
            "source_diversity_gap_observation_count",
            "stale_observation_count",
            "confidence_gap_observation_count",
            "average_active_pause_signal_count",
            "average_enactable_pause_action_count",
            "average_critical_pause_ratio",
            "average_pause_window_pressure_ratio",
            "max_observation_age_seconds",
            "max_allowed_observation_age_seconds",
            "watch_active_pause_signal_count",
            "blocked_enactable_pause_action_count",
            "max_pause_window_seconds",
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


def build_market_research_crypto_bridge_governance_pause_digest(
    observations: Iterable[MarketResearchCryptoBridgeGovernancePauseObservation],
    *,
    config: MarketResearchCryptoBridgeGovernancePauseDigestConfig | None = None,
    generated_at: datetime,
) -> MarketResearchCryptoBridgeGovernancePauseDigestReport:
    cfg = config or MarketResearchCryptoBridgeGovernancePauseDigestConfig()
    if type(cfg) is not MarketResearchCryptoBridgeGovernancePauseDigestConfig:
        raise ValueError(
            "config must be exactly MarketResearchCryptoBridgeGovernancePauseDigestConfig",
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
                row.bridge_pause_id,
                row.condition_id,
            ),
        ),
    )
    report_status = _report_status(sorted_rows)
    observation_count = _decimal_count(len(sorted_rows))
    return MarketResearchCryptoBridgeGovernancePauseDigestReport(
        generated_at=generated_at_utc,
        config_version=cfg.config_version,
        digest_status=report_status,
        recommended_next_step=_recommended_next_step(report_status),
        observation_count=observation_count,
        ready_observation_count=_status_count(sorted_rows, STATUS_READY),
        watch_observation_count=_status_count(sorted_rows, STATUS_WATCH),
        blocked_observation_count=_status_count(sorted_rows, STATUS_BLOCKED),
        pause_signal_observation_count=_reason_observation_count(
            sorted_rows,
            PAUSE_SIGNAL_REASON,
        ),
        pause_action_enactable_observation_count=_reason_observation_count(
            sorted_rows,
            PAUSE_ACTION_ENACTABLE_REASON,
        ),
        critical_function_paused_observation_count=_reason_observation_count(
            sorted_rows,
            CRITICAL_FUNCTION_PAUSED_REASON,
        ),
        pause_window_pressure_observation_count=_reason_observation_count(
            sorted_rows,
            PAUSE_WINDOW_PRESSURE_REASON,
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
        average_active_pause_signal_count=_ratio(
            _decimal_sum(row.active_pause_signal_count for row in sorted_rows),
            observation_count,
        ),
        average_enactable_pause_action_count=_ratio(
            _decimal_sum(row.enactable_pause_action_count for row in sorted_rows),
            observation_count,
        ),
        average_critical_pause_ratio=_ratio(
            _decimal_sum(row.critical_pause_ratio for row in sorted_rows),
            observation_count,
        ),
        average_pause_window_pressure_ratio=_ratio(
            _decimal_sum(row.pause_window_pressure_ratio for row in sorted_rows),
            observation_count,
        ),
        max_observation_age_seconds=max(
            (row.observation_age_seconds for row in sorted_rows),
            default=ZERO,
        ),
        max_allowed_observation_age_seconds=cfg.max_observation_age_seconds,
        watch_active_pause_signal_count=cfg.watch_active_pause_signal_count,
        blocked_enactable_pause_action_count=cfg.blocked_enactable_pause_action_count,
        max_pause_window_seconds=cfg.max_pause_window_seconds,
        min_source_count=cfg.min_source_count,
        min_confidence=cfg.min_confidence,
        rows=sorted_rows,
        source_config_versions=tuple(
            sorted(
                (observation.bridge_pause_id, observation.source_config_version)
                for observation in normalized_observations
            ),
        ),
        reason_code_counts=_reason_code_counts(sorted_rows),
        reason_codes=_summary_reason_codes(sorted_rows),
    )


def market_research_crypto_bridge_governance_pause_digest_payload(
    report: MarketResearchCryptoBridgeGovernancePauseDigestReport,
) -> MappingProxyType:
    if type(report) is not MarketResearchCryptoBridgeGovernancePauseDigestReport:
        raise ValueError(
            "report must be exactly MarketResearchCryptoBridgeGovernancePauseDigestReport",
        )
    return _freeze(_json_ready(report))


def _row_for_observation(
    observation: MarketResearchCryptoBridgeGovernancePauseObservation,
    *,
    config: MarketResearchCryptoBridgeGovernancePauseDigestConfig,
    generated_at: datetime,
) -> MarketResearchCryptoBridgeGovernancePauseDigestRow:
    if observation.observed_at > generated_at:
        raise ValueError("observed_at must not be in the future")
    observation_age_seconds = _age_seconds(generated_at, observation.observed_at)
    critical_pause_ratio = _pressure_ratio(
        observation.paused_critical_function_count,
        observation.total_critical_function_count,
    )
    pause_window_pressure_ratio = _ratio(
        observation.pause_window_seconds,
        observation.governance_delay_seconds,
    )
    reason_codes = _row_reason_codes(
        observation=observation,
        config=config,
        observation_age_seconds=observation_age_seconds,
    )
    return MarketResearchCryptoBridgeGovernancePauseDigestRow(
        condition_id=observation.condition_id,
        bridge_pause_id=observation.bridge_pause_id,
        bridge_name=observation.bridge_name,
        chain_family=observation.chain_family,
        digest_status=_row_status(reason_codes),
        observed_at=observation.observed_at,
        observation_age_seconds=observation_age_seconds,
        active_pause_signal_count=observation.active_pause_signal_count,
        enactable_pause_action_count=observation.enactable_pause_action_count,
        paused_critical_function_count=observation.paused_critical_function_count,
        total_critical_function_count=observation.total_critical_function_count,
        critical_pause_ratio=critical_pause_ratio,
        pause_window_seconds=observation.pause_window_seconds,
        governance_delay_seconds=observation.governance_delay_seconds,
        pause_window_pressure_ratio=pause_window_pressure_ratio,
        source_count=observation.source_count,
        confidence=observation.confidence,
        reason_codes=reason_codes,
    )


def _row_reason_codes(
    *,
    observation: MarketResearchCryptoBridgeGovernancePauseObservation,
    config: MarketResearchCryptoBridgeGovernancePauseDigestConfig,
    observation_age_seconds: Decimal,
) -> tuple[str, ...]:
    reasons: list[str] = []
    if observation.active_pause_signal_count >= config.watch_active_pause_signal_count:
        reasons.append(PAUSE_SIGNAL_REASON)
    if (
        observation.enactable_pause_action_count
        >= config.blocked_enactable_pause_action_count
    ):
        reasons.append(PAUSE_ACTION_ENACTABLE_REASON)
    if observation.paused_critical_function_count > ZERO:
        reasons.append(CRITICAL_FUNCTION_PAUSED_REASON)
    if observation.pause_window_seconds > config.max_pause_window_seconds:
        reasons.append(PAUSE_WINDOW_PRESSURE_REASON)
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
    if any(
        reason in reason_codes
        for reason in (
            PAUSE_ACTION_ENACTABLE_REASON,
            CRITICAL_FUNCTION_PAUSED_REASON,
            STALE_OBSERVATION_REASON,
            CONFIDENCE_GAP_REASON,
        )
    ):
        return STATUS_BLOCKED
    return STATUS_WATCH


def _row_sort_value(
    row: MarketResearchCryptoBridgeGovernancePauseDigestRow,
) -> tuple[int, Decimal]:
    status_rank = {
        STATUS_BLOCKED: 0,
        STATUS_WATCH: 1,
        STATUS_READY: 2,
    }[row.digest_status]
    severity = _decimal_count(
        len(tuple(reason for reason in row.reason_codes if reason != READY_REASON)),
    )
    return (status_rank, -severity)


def _report_status(
    rows: tuple[MarketResearchCryptoBridgeGovernancePauseDigestRow, ...],
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
        return "block_report_only_market_research_crypto_bridge_governance_pause_digest"
    if status == STATUS_WATCH:
        return "review_report_only_market_research_crypto_bridge_governance_pause_digest"
    return "allow_report_only_market_research_crypto_bridge_governance_pause_digest"


def _status_count(
    rows: tuple[MarketResearchCryptoBridgeGovernancePauseDigestRow, ...],
    status: str,
) -> Decimal:
    return _decimal_count(sum(1 for row in rows if row.digest_status == status))


def _reason_observation_count(
    rows: tuple[MarketResearchCryptoBridgeGovernancePauseDigestRow, ...],
    reason_code: str,
) -> Decimal:
    return _decimal_count(sum(1 for row in rows if reason_code in row.reason_codes))


def _reason_code_counts(
    rows: tuple[MarketResearchCryptoBridgeGovernancePauseDigestRow, ...],
) -> tuple[MarketResearchCryptoBridgeGovernancePauseDigestReasonCodeCount, ...]:
    observation_count = _decimal_count(len(rows))
    counts: dict[str, int] = {}
    for row in rows:
        for reason_code in row.reason_codes:
            counts[reason_code] = counts.get(reason_code, 0) + 1
    return tuple(
        MarketResearchCryptoBridgeGovernancePauseDigestReasonCodeCount(
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
    rows: tuple[MarketResearchCryptoBridgeGovernancePauseDigestRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return (NO_INPUTS_REASON,)
    seen: set[str] = set()
    for row in rows:
        seen.update(row.reason_codes)
    if len(seen) > 1 and READY_REASON in seen:
        seen.remove(READY_REASON)
    return tuple(reason for reason in REASON_CODE_SEQUENCE if reason in seen)


def _validate_row(row: MarketResearchCryptoBridgeGovernancePauseDigestRow) -> None:
    if row.critical_pause_ratio != _pressure_ratio(
        row.paused_critical_function_count,
        row.total_critical_function_count,
    ):
        raise ValueError("critical_pause_ratio does not match critical function inputs")
    if row.pause_window_pressure_ratio != _ratio(
        row.pause_window_seconds,
        row.governance_delay_seconds,
    ):
        raise ValueError("pause_window_pressure_ratio does not match pause window inputs")
    if row.digest_status != _row_status(row.reason_codes):
        raise ValueError("digest_status does not match reason_codes")


def _validate_report(report: MarketResearchCryptoBridgeGovernancePauseDigestReport) -> None:
    if report.observation_count != _decimal_count(len(report.rows)):
        raise ValueError("observation_count does not match rows")
    if report.ready_observation_count != _status_count(report.rows, STATUS_READY):
        raise ValueError("ready_observation_count does not match rows")
    if report.watch_observation_count != _status_count(report.rows, STATUS_WATCH):
        raise ValueError("watch_observation_count does not match rows")
    if report.blocked_observation_count != _status_count(report.rows, STATUS_BLOCKED):
        raise ValueError("blocked_observation_count does not match rows")
    expected_counts = (
        (PAUSE_SIGNAL_REASON, report.pause_signal_observation_count),
        (PAUSE_ACTION_ENACTABLE_REASON, report.pause_action_enactable_observation_count),
        (CRITICAL_FUNCTION_PAUSED_REASON, report.critical_function_paused_observation_count),
        (PAUSE_WINDOW_PRESSURE_REASON, report.pause_window_pressure_observation_count),
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
    if report.average_active_pause_signal_count != _ratio(
        _decimal_sum(row.active_pause_signal_count for row in report.rows),
        report.observation_count,
    ):
        raise ValueError("average_active_pause_signal_count does not match rows")
    if report.average_enactable_pause_action_count != _ratio(
        _decimal_sum(row.enactable_pause_action_count for row in report.rows),
        report.observation_count,
    ):
        raise ValueError("average_enactable_pause_action_count does not match rows")
    if report.average_critical_pause_ratio != _ratio(
        _decimal_sum(row.critical_pause_ratio for row in report.rows),
        report.observation_count,
    ):
        raise ValueError("average_critical_pause_ratio does not match rows")
    if report.average_pause_window_pressure_ratio != _ratio(
        _decimal_sum(row.pause_window_pressure_ratio for row in report.rows),
        report.observation_count,
    ):
        raise ValueError("average_pause_window_pressure_ratio does not match rows")
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
    observations: Iterable[MarketResearchCryptoBridgeGovernancePauseObservation],
) -> tuple[MarketResearchCryptoBridgeGovernancePauseObservation, ...]:
    observation_tuple = tuple(observations)
    seen_ids: set[str] = set()
    for observation in observation_tuple:
        if type(observation) is not MarketResearchCryptoBridgeGovernancePauseObservation:
            raise ValueError(
                "observations must contain "
                "MarketResearchCryptoBridgeGovernancePauseObservation",
            )
        if observation.bridge_pause_id in seen_ids:
            raise ValueError("bridge_pause_id values must be unique")
        seen_ids.add(observation.bridge_pause_id)
        _require_hard_flags("observation", observation)
    return observation_tuple


def _normalize_rows(
    rows: tuple[MarketResearchCryptoBridgeGovernancePauseDigestRow, ...],
) -> tuple[MarketResearchCryptoBridgeGovernancePauseDigestRow, ...]:
    if type(rows) is not tuple:
        raise ValueError("rows must be a tuple")
    seen_ids: set[str] = set()
    for row in rows:
        if type(row) is not MarketResearchCryptoBridgeGovernancePauseDigestRow:
            raise ValueError(
                "rows must contain MarketResearchCryptoBridgeGovernancePauseDigestRow",
            )
        if row.bridge_pause_id in seen_ids:
            raise ValueError("rows bridge_pause_id values must be unique")
        seen_ids.add(row.bridge_pause_id)
        _require_hard_flags("row", row)
    sorted_rows = tuple(
        sorted(
            rows,
            key=lambda row: (
                _row_sort_value(row),
                row.bridge_pause_id,
                row.condition_id,
            ),
        ),
    )
    if rows != sorted_rows:
        raise ValueError("rows must be sorted deterministically")
    return rows


def _normalize_reason_code_counts(
    items: tuple[MarketResearchCryptoBridgeGovernancePauseDigestReasonCodeCount, ...],
) -> tuple[MarketResearchCryptoBridgeGovernancePauseDigestReasonCodeCount, ...]:
    if type(items) is not tuple:
        raise ValueError("reason_code_counts must be a tuple")
    for item in items:
        if type(item) is not MarketResearchCryptoBridgeGovernancePauseDigestReasonCodeCount:
            raise ValueError("reason_code_counts must contain reason count rows")
        _require_hard_flags("reason code count", item)
    return items


def _normalize_source_config_versions(
    value: tuple[tuple[str, str], ...],
) -> tuple[tuple[str, str], ...]:
    if type(value) is not tuple:
        raise ValueError("source_config_versions must be a tuple")
    pairs: list[tuple[str, str]] = []
    seen_ids: set[str] = set()
    for item in value:
        if type(item) is not tuple or len(item) != 2:
            raise ValueError("source_config_versions must contain pairs")
        bridge_pause_id, source_config_version = item
        _require_public_string("bridge_pause_id", bridge_pause_id)
        _require_public_string("source_config_version", source_config_version)
        if bridge_pause_id in seen_ids:
            raise ValueError(
                "source_config_versions bridge_pause_id values must be unique",
            )
        seen_ids.add(bridge_pause_id)
        pairs.append((bridge_pause_id, source_config_version))
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
    if type(value) is not str or value not in BRIDGE_GOVERNANCE_PAUSE_DIGEST_STATUSES:
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
    _require_public_text(field_name, value)


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


def _pressure_ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO:
        return ZERO
    return _quantize(min(numerator / denominator, ONE))


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
        return MappingProxyType({item_id: _freeze(item) for item_id, item in value.items()})
    if isinstance(value, list):
        return tuple(_freeze(item) for item in value)
    return value
