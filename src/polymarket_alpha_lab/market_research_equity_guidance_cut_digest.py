"""Pure Phase 1 equity guidance cut digest reducer."""

from __future__ import annotations

from dataclasses import dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
from typing import Any, Iterable


DEFAULT_MARKET_RESEARCH_EQUITY_GUIDANCE_CUT_DIGEST_CONFIG_VERSION = (
    "market-research-equity-guidance-cut-digest-v0"
)

STATUS_READY = "ready"
STATUS_WATCH = "watch"
STATUS_BLOCKED = "blocked"
DIGEST_STATUSES = (STATUS_READY, STATUS_WATCH, STATUS_BLOCKED)

REASON_PREFIX = "market_research_equity_guidance_cut_digest_"
NO_INPUTS_REASON = f"{REASON_PREFIX}no_inputs"
READY_REASON = f"{REASON_PREFIX}ready"
MATERIAL_GUIDANCE_CUT_REASON = f"{REASON_PREFIX}material_guidance_cut"
NEGATIVE_GUIDANCE_CUT_REASON = f"{REASON_PREFIX}negative_guidance_cut"
CONSENSUS_GAP_REASON = f"{REASON_PREFIX}consensus_gap"
PRICE_REACTION_PRESSURE_REASON = f"{REASON_PREFIX}price_reaction_pressure"
THIN_SOURCES_REASON = f"{REASON_PREFIX}thin_sources"
MISSING_ACKNOWLEDGEMENT_REASON = f"{REASON_PREFIX}missing_acknowledgement"
SLOW_ACKNOWLEDGEMENT_REASON = f"{REASON_PREFIX}slow_acknowledgement"
LOW_CONFIDENCE_REASON = f"{REASON_PREFIX}low_confidence"
STALE_OBSERVATION_REASON = f"{REASON_PREFIX}stale_observation"

REASON_CODE_SEQUENCE = (
    MATERIAL_GUIDANCE_CUT_REASON,
    NEGATIVE_GUIDANCE_CUT_REASON,
    CONSENSUS_GAP_REASON,
    PRICE_REACTION_PRESSURE_REASON,
    THIN_SOURCES_REASON,
    MISSING_ACKNOWLEDGEMENT_REASON,
    READY_REASON,
    SLOW_ACKNOWLEDGEMENT_REASON,
    LOW_CONFIDENCE_REASON,
    STALE_OBSERVATION_REASON,
    NO_INPUTS_REASON,
)
ROW_REASON_CODE_SEQUENCE = (
    MATERIAL_GUIDANCE_CUT_REASON,
    NEGATIVE_GUIDANCE_CUT_REASON,
    CONSENSUS_GAP_REASON,
    PRICE_REACTION_PRESSURE_REASON,
    THIN_SOURCES_REASON,
    MISSING_ACKNOWLEDGEMENT_REASON,
    READY_REASON,
    SLOW_ACKNOWLEDGEMENT_REASON,
    LOW_CONFIDENCE_REASON,
    STALE_OBSERVATION_REASON,
)

NEXT_STEPS = {
    STATUS_READY: "allow_report_only_market_research_equity_guidance_cut_digest",
    STATUS_WATCH: "review_report_only_market_research_equity_guidance_cut_digest",
    STATUS_BLOCKED: "block_report_only_market_research_equity_guidance_cut_digest",
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
        _join_parts("sig", "ning"),
        _join_parts("sub", "mit"),
        _join_parts("can", "cel"),
        _join_parts("wal", "let"),
        _join_parts("acc", "ount"),
        _join_parts("net", "work"),
        _join_parts("data", "base"),
        _join_parts("per", "sist"),
        _join_parts("pay", "load"),
        _join_parts("sec", "ret"),
        _join_parts("to", "ken"),
        _join_parts("pri", "vate"),
    ),
)

__all__ = (
    "DEFAULT_MARKET_RESEARCH_EQUITY_GUIDANCE_CUT_DIGEST_CONFIG_VERSION",
    "MarketResearchEquityGuidanceCutDigestConfig",
    "MarketResearchEquityGuidanceCutDigestReasonCodeCount",
    "MarketResearchEquityGuidanceCutDigestReport",
    "MarketResearchEquityGuidanceCutDigestRow",
    "MarketResearchEquityGuidanceCutObservation",
    "build_market_research_equity_guidance_cut_digest",
    "market_research_equity_guidance_cut_digest_payload",
)


@dataclass(frozen=True)
class MarketResearchEquityGuidanceCutDigestConfig:
    config_version: str = (
        DEFAULT_MARKET_RESEARCH_EQUITY_GUIDANCE_CUT_DIGEST_CONFIG_VERSION
    )
    max_observation_age_seconds: Decimal = Decimal("7200.000000")
    min_source_count: Decimal = Decimal("2.000000")
    material_guidance_cut_ratio: Decimal = Decimal("0.050000")
    material_consensus_gap_ratio: Decimal = Decimal("0.030000")
    min_guidance_confidence: Decimal = Decimal("0.650000")
    material_price_reaction_abs: Decimal = Decimal("0.020000")
    max_acknowledgement_lag_seconds: Decimal = Decimal("1800.000000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketResearchEquityGuidanceCutDigestConfig:
            raise TypeError(
                "MarketResearchEquityGuidanceCutDigestConfig does not "
                "support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not MarketResearchEquityGuidanceCutDigestConfig:
            raise ValueError(
                "config must be exactly "
                "MarketResearchEquityGuidanceCutDigestConfig",
            )
        _require_canonical_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_MARKET_RESEARCH_EQUITY_GUIDANCE_CUT_DIGEST_CONFIG_VERSION
        ):
            raise ValueError("config_version must be supported")
        object.__setattr__(
            self,
            "max_observation_age_seconds",
            _require_positive_decimal(
                "max_observation_age_seconds",
                self.max_observation_age_seconds,
            ),
        )
        object.__setattr__(
            self,
            "min_source_count",
            _require_positive_count_decimal("min_source_count", self.min_source_count),
        )
        for field_name in (
            "material_guidance_cut_ratio",
            "material_consensus_gap_ratio",
            "min_guidance_confidence",
            "material_price_reaction_abs",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        if self.material_guidance_cut_ratio <= ZERO:
            raise ValueError("material_guidance_cut_ratio must be positive")
        if self.material_consensus_gap_ratio <= ZERO:
            raise ValueError("material_consensus_gap_ratio must be positive")
        if self.material_price_reaction_abs <= ZERO:
            raise ValueError("material_price_reaction_abs must be positive")
        object.__setattr__(
            self,
            "max_acknowledgement_lag_seconds",
            _require_positive_decimal(
                "max_acknowledgement_lag_seconds",
                self.max_acknowledgement_lag_seconds,
            ),
        )
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class MarketResearchEquityGuidanceCutObservation:
    research_key: str
    condition_id: str
    equity_symbol: str
    guidance_event_key: str
    guidance_reference: str
    observed_at: datetime
    acknowledged_at: datetime | None
    source_count: Decimal
    previous_guidance_eps: Decimal
    current_guidance_eps: Decimal
    consensus_eps: Decimal
    guidance_confidence: Decimal
    price_reaction: Decimal
    source_config_version: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketResearchEquityGuidanceCutObservation:
            raise TypeError(
                "MarketResearchEquityGuidanceCutObservation does not "
                "support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not MarketResearchEquityGuidanceCutObservation:
            raise ValueError(
                "observation must be exactly "
                "MarketResearchEquityGuidanceCutObservation",
            )
        _require_public_string("research_key", self.research_key)
        _require_public_string("condition_id", self.condition_id)
        _require_equity_symbol("equity_symbol", self.equity_symbol)
        _require_public_string("guidance_event_key", self.guidance_event_key)
        _require_reference("guidance_reference", self.guidance_reference)
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        object.__setattr__(
            self,
            "acknowledged_at",
            _as_optional_utc("acknowledged_at", self.acknowledged_at),
        )
        object.__setattr__(
            self,
            "source_count",
            _require_nonnegative_count_decimal("source_count", self.source_count),
        )
        for field_name in (
            "previous_guidance_eps",
            "current_guidance_eps",
            "consensus_eps",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "guidance_confidence",
            _require_ratio_decimal("guidance_confidence", self.guidance_confidence),
        )
        object.__setattr__(
            self,
            "price_reaction",
            _require_signed_ratio_decimal("price_reaction", self.price_reaction),
        )
        _require_public_string("source_config_version", self.source_config_version)
        _require_hard_flags("observation", self)


@dataclass(frozen=True)
class MarketResearchEquityGuidanceCutDigestRow:
    research_key: str
    condition_id: str
    equity_symbol: str
    guidance_event_key: str
    digest_status: str
    observed_at: datetime
    acknowledged_at: datetime | None
    observation_age_seconds: Decimal
    acknowledgement_lag_seconds: Decimal | None
    previous_guidance_eps: Decimal
    current_guidance_eps: Decimal
    consensus_eps: Decimal
    guidance_cut_abs: Decimal
    guidance_cut_ratio: Decimal
    consensus_gap_ratio: Decimal
    source_count: Decimal
    guidance_confidence: Decimal
    price_reaction: Decimal
    price_reaction_abs: Decimal
    redacted_guidance_reference: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketResearchEquityGuidanceCutDigestRow:
            raise TypeError(
                "MarketResearchEquityGuidanceCutDigestRow does not support "
                "subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not MarketResearchEquityGuidanceCutDigestRow:
            raise ValueError(
                "row must be exactly "
                "MarketResearchEquityGuidanceCutDigestRow",
            )
        _require_public_string("research_key", self.research_key)
        _require_public_string("condition_id", self.condition_id)
        _require_equity_symbol("equity_symbol", self.equity_symbol)
        _require_public_string("guidance_event_key", self.guidance_event_key)
        _require_status("digest_status", self.digest_status)
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        object.__setattr__(
            self,
            "acknowledged_at",
            _as_optional_utc("acknowledged_at", self.acknowledged_at),
        )
        for field_name in (
            "observation_age_seconds",
            "guidance_cut_abs",
            "source_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_count_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "acknowledgement_lag_seconds",
            _require_optional_nonnegative_decimal(
                "acknowledgement_lag_seconds",
                self.acknowledgement_lag_seconds,
            ),
        )
        for field_name in (
            "previous_guidance_eps",
            "current_guidance_eps",
            "consensus_eps",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "guidance_cut_ratio",
            "consensus_gap_ratio",
            "guidance_confidence",
            "price_reaction_abs",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "price_reaction",
            _require_signed_ratio_decimal("price_reaction", self.price_reaction),
        )
        _require_redacted_reference(
            "redacted_guidance_reference",
            self.redacted_guidance_reference,
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes, order=ROW_REASON_CODE_SEQUENCE),
        )
        _validate_row(self)
        _require_hard_flags("row", self)


@dataclass(frozen=True)
class MarketResearchEquityGuidanceCutDigestReasonCodeCount:
    reason_code: str
    count: Decimal
    event_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketResearchEquityGuidanceCutDigestReasonCodeCount:
            raise TypeError(
                "MarketResearchEquityGuidanceCutDigestReasonCodeCount does "
                "not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not MarketResearchEquityGuidanceCutDigestReasonCodeCount:
            raise ValueError(
                "reason code count must be exactly "
                "MarketResearchEquityGuidanceCutDigestReasonCodeCount",
            )
        _require_reason_code("reason_code", self.reason_code)
        object.__setattr__(
            self,
            "count",
            _require_positive_count_decimal("count", self.count),
        )
        object.__setattr__(
            self,
            "event_ratio",
            _require_ratio_decimal("event_ratio", self.event_ratio),
        )
        _require_hard_flags("reason code count", self)


@dataclass(frozen=True)
class MarketResearchEquityGuidanceCutDigestReport:
    generated_at: datetime
    config_version: str
    digest_status: str
    recommended_next_step: str
    event_count: Decimal
    ready_event_count: Decimal
    watch_event_count: Decimal
    blocked_event_count: Decimal
    material_guidance_cut_count: Decimal
    negative_guidance_cut_count: Decimal
    consensus_gap_count: Decimal
    thin_source_count: Decimal
    low_confidence_count: Decimal
    missing_acknowledgement_count: Decimal
    slow_acknowledgement_count: Decimal
    stale_observation_count: Decimal
    price_reaction_pressure_count: Decimal
    average_guidance_cut_ratio: Decimal
    max_guidance_cut_ratio: Decimal
    average_source_count: Decimal
    average_guidance_confidence: Decimal
    max_observation_age_seconds: Decimal
    max_allowed_observation_age_seconds: Decimal
    min_source_count: Decimal
    material_guidance_cut_ratio: Decimal
    material_consensus_gap_ratio: Decimal
    min_guidance_confidence: Decimal
    material_price_reaction_abs: Decimal
    max_acknowledgement_lag_seconds: Decimal
    rows: tuple[MarketResearchEquityGuidanceCutDigestRow, ...]
    source_config_versions: tuple[tuple[str, str], ...]
    reason_code_counts: tuple[
        MarketResearchEquityGuidanceCutDigestReasonCodeCount,
        ...,
    ]
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketResearchEquityGuidanceCutDigestReport:
            raise TypeError(
                "MarketResearchEquityGuidanceCutDigestReport does not "
                "support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not MarketResearchEquityGuidanceCutDigestReport:
            raise ValueError(
                "report must be exactly "
                "MarketResearchEquityGuidanceCutDigestReport",
            )
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        _require_status("digest_status", self.digest_status)
        _require_canonical_string("recommended_next_step", self.recommended_next_step)
        for field_name in (
            "event_count",
            "ready_event_count",
            "watch_event_count",
            "blocked_event_count",
            "material_guidance_cut_count",
            "negative_guidance_cut_count",
            "consensus_gap_count",
            "thin_source_count",
            "low_confidence_count",
            "missing_acknowledgement_count",
            "slow_acknowledgement_count",
            "stale_observation_count",
            "price_reaction_pressure_count",
            "max_observation_age_seconds",
            "max_allowed_observation_age_seconds",
            "min_source_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_count_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "average_guidance_cut_ratio",
            "max_guidance_cut_ratio",
            "average_guidance_confidence",
            "material_guidance_cut_ratio",
            "material_consensus_gap_ratio",
            "min_guidance_confidence",
            "material_price_reaction_abs",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "average_source_count",
            _require_nonnegative_count_decimal(
                "average_source_count",
                self.average_source_count,
            ),
        )
        object.__setattr__(
            self,
            "max_acknowledgement_lag_seconds",
            _require_positive_decimal(
                "max_acknowledgement_lag_seconds",
                self.max_acknowledgement_lag_seconds,
            ),
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
            _normalize_reason_codes(self.reason_codes, order=REASON_CODE_SEQUENCE),
        )
        _validate_report(self)
        _require_hard_flags("report", self)


_PUBLIC_DATACLASS_TYPES = (
    MarketResearchEquityGuidanceCutDigestConfig,
    MarketResearchEquityGuidanceCutDigestReasonCodeCount,
    MarketResearchEquityGuidanceCutDigestReport,
    MarketResearchEquityGuidanceCutDigestRow,
    MarketResearchEquityGuidanceCutObservation,
)


def build_market_research_equity_guidance_cut_digest(
    observations: Iterable[MarketResearchEquityGuidanceCutObservation],
    *,
    config: MarketResearchEquityGuidanceCutDigestConfig | None = None,
    generated_at: datetime,
) -> MarketResearchEquityGuidanceCutDigestReport:
    cfg = MarketResearchEquityGuidanceCutDigestConfig() if config is None else config
    if type(cfg) is not MarketResearchEquityGuidanceCutDigestConfig:
        raise ValueError(
            "config must be exactly "
            "MarketResearchEquityGuidanceCutDigestConfig",
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
    sorted_rows = _sort_rows(rows)
    event_count = _decimal_count(len(sorted_rows))
    report_status = _report_status(sorted_rows)
    return MarketResearchEquityGuidanceCutDigestReport(
        generated_at=generated_at_utc,
        config_version=cfg.config_version,
        digest_status=report_status,
        recommended_next_step=NEXT_STEPS[report_status],
        event_count=event_count,
        ready_event_count=_status_count(sorted_rows, STATUS_READY),
        watch_event_count=_status_count(sorted_rows, STATUS_WATCH),
        blocked_event_count=_status_count(sorted_rows, STATUS_BLOCKED),
        material_guidance_cut_count=_reason_event_count(
            sorted_rows,
            MATERIAL_GUIDANCE_CUT_REASON,
        ),
        negative_guidance_cut_count=_reason_event_count(
            sorted_rows,
            NEGATIVE_GUIDANCE_CUT_REASON,
        ),
        consensus_gap_count=_reason_event_count(sorted_rows, CONSENSUS_GAP_REASON),
        thin_source_count=_reason_event_count(sorted_rows, THIN_SOURCES_REASON),
        low_confidence_count=_reason_event_count(sorted_rows, LOW_CONFIDENCE_REASON),
        missing_acknowledgement_count=_reason_event_count(
            sorted_rows,
            MISSING_ACKNOWLEDGEMENT_REASON,
        ),
        slow_acknowledgement_count=_reason_event_count(
            sorted_rows,
            SLOW_ACKNOWLEDGEMENT_REASON,
        ),
        stale_observation_count=_reason_event_count(sorted_rows, STALE_OBSERVATION_REASON),
        price_reaction_pressure_count=_reason_event_count(
            sorted_rows,
            PRICE_REACTION_PRESSURE_REASON,
        ),
        average_guidance_cut_ratio=_ratio(
            _decimal_sum(row.guidance_cut_ratio for row in sorted_rows),
            event_count,
        ),
        max_guidance_cut_ratio=max(
            (row.guidance_cut_ratio for row in sorted_rows),
            default=ZERO,
        ),
        average_source_count=_ratio(
            _decimal_sum(row.source_count for row in sorted_rows),
            event_count,
        ),
        average_guidance_confidence=_ratio(
            _decimal_sum(row.guidance_confidence for row in sorted_rows),
            event_count,
        ),
        max_observation_age_seconds=max(
            (row.observation_age_seconds for row in sorted_rows),
            default=ZERO,
        ),
        max_allowed_observation_age_seconds=cfg.max_observation_age_seconds,
        min_source_count=cfg.min_source_count,
        material_guidance_cut_ratio=cfg.material_guidance_cut_ratio,
        material_consensus_gap_ratio=cfg.material_consensus_gap_ratio,
        min_guidance_confidence=cfg.min_guidance_confidence,
        material_price_reaction_abs=cfg.material_price_reaction_abs,
        max_acknowledgement_lag_seconds=cfg.max_acknowledgement_lag_seconds,
        rows=sorted_rows,
        source_config_versions=tuple(
            sorted(
                (observation.research_key, observation.source_config_version)
                for observation in normalized_observations
            ),
        ),
        reason_code_counts=_reason_code_counts(sorted_rows),
        reason_codes=_summary_reason_codes(sorted_rows),
    )


def market_research_equity_guidance_cut_digest_payload(
    report: MarketResearchEquityGuidanceCutDigestReport,
) -> dict[str, Any]:
    if type(report) is not MarketResearchEquityGuidanceCutDigestReport:
        raise ValueError(
            "report must be a "
            "MarketResearchEquityGuidanceCutDigestReport",
        )
    _require_payload_safe_value("report", report)
    return _payload_value(report)


def _row_for_observation(
    observation: MarketResearchEquityGuidanceCutObservation,
    *,
    config: MarketResearchEquityGuidanceCutDigestConfig,
    generated_at: datetime,
) -> MarketResearchEquityGuidanceCutDigestRow:
    if observation.observed_at > generated_at:
        raise ValueError("observed_at must not be in the future")
    observation_age_seconds = _seconds_between(observation.observed_at, generated_at)
    acknowledgement_lag_seconds = (
        None
        if observation.acknowledged_at is None
        else _seconds_between(observation.observed_at, observation.acknowledged_at)
    )
    guidance_cut_abs = _guidance_cut_abs(
        observation.previous_guidance_eps,
        observation.current_guidance_eps,
    )
    guidance_cut_ratio = _safe_ratio(
        guidance_cut_abs,
        _decimal_abs(observation.previous_guidance_eps),
    )
    consensus_gap_ratio = _safe_ratio(
        _decimal_abs(observation.current_guidance_eps - observation.consensus_eps),
        _decimal_abs(observation.consensus_eps),
    )
    price_reaction_abs = _decimal_abs(observation.price_reaction)
    reason_codes = _row_reason_codes(
        observation=observation,
        config=config,
        observation_age_seconds=observation_age_seconds,
        acknowledgement_lag_seconds=acknowledgement_lag_seconds,
        guidance_cut_ratio=guidance_cut_ratio,
        consensus_gap_ratio=consensus_gap_ratio,
        price_reaction_abs=price_reaction_abs,
    )
    return MarketResearchEquityGuidanceCutDigestRow(
        research_key=observation.research_key,
        condition_id=observation.condition_id,
        equity_symbol=observation.equity_symbol,
        guidance_event_key=observation.guidance_event_key,
        digest_status=_row_status(reason_codes),
        observed_at=observation.observed_at,
        acknowledged_at=observation.acknowledged_at,
        observation_age_seconds=observation_age_seconds,
        acknowledgement_lag_seconds=acknowledgement_lag_seconds,
        previous_guidance_eps=observation.previous_guidance_eps,
        current_guidance_eps=observation.current_guidance_eps,
        consensus_eps=observation.consensus_eps,
        guidance_cut_abs=guidance_cut_abs,
        guidance_cut_ratio=guidance_cut_ratio,
        consensus_gap_ratio=consensus_gap_ratio,
        source_count=observation.source_count,
        guidance_confidence=observation.guidance_confidence,
        price_reaction=observation.price_reaction,
        price_reaction_abs=price_reaction_abs,
        redacted_guidance_reference=_redacted_reference(observation.guidance_reference),
        reason_codes=reason_codes,
    )


def _row_reason_codes(
    *,
    observation: MarketResearchEquityGuidanceCutObservation,
    config: MarketResearchEquityGuidanceCutDigestConfig,
    observation_age_seconds: Decimal,
    acknowledgement_lag_seconds: Decimal | None,
    guidance_cut_ratio: Decimal,
    consensus_gap_ratio: Decimal,
    price_reaction_abs: Decimal,
) -> tuple[str, ...]:
    reasons: list[str] = []
    if guidance_cut_ratio >= config.material_guidance_cut_ratio:
        reasons.append(MATERIAL_GUIDANCE_CUT_REASON)
    if guidance_cut_ratio >= config.material_guidance_cut_ratio:
        reasons.append(NEGATIVE_GUIDANCE_CUT_REASON)
    if consensus_gap_ratio >= config.material_consensus_gap_ratio:
        reasons.append(CONSENSUS_GAP_REASON)
    if price_reaction_abs >= config.material_price_reaction_abs:
        reasons.append(PRICE_REACTION_PRESSURE_REASON)
    if observation.source_count < config.min_source_count:
        reasons.append(THIN_SOURCES_REASON)
    if acknowledgement_lag_seconds is None:
        reasons.append(MISSING_ACKNOWLEDGEMENT_REASON)
    elif acknowledgement_lag_seconds > config.max_acknowledgement_lag_seconds:
        reasons.append(SLOW_ACKNOWLEDGEMENT_REASON)
    if observation.guidance_confidence < config.min_guidance_confidence:
        reasons.append(LOW_CONFIDENCE_REASON)
    if observation_age_seconds > config.max_observation_age_seconds:
        reasons.append(STALE_OBSERVATION_REASON)
    if not reasons:
        reasons.append(READY_REASON)
    return tuple(reason for reason in ROW_REASON_CODE_SEQUENCE if reason in reasons)


def _row_status(reason_codes: tuple[str, ...]) -> str:
    if reason_codes == (READY_REASON,):
        return STATUS_READY
    if any(
        reason in reason_codes
        for reason in (
            NEGATIVE_GUIDANCE_CUT_REASON,
            CONSENSUS_GAP_REASON,
            PRICE_REACTION_PRESSURE_REASON,
            MISSING_ACKNOWLEDGEMENT_REASON,
            LOW_CONFIDENCE_REASON,
            STALE_OBSERVATION_REASON,
        )
    ):
        return STATUS_BLOCKED
    return STATUS_WATCH


def _row_sort_value(
    row: MarketResearchEquityGuidanceCutDigestRow,
) -> tuple[int, Decimal, Decimal]:
    status_rank = {
        STATUS_BLOCKED: 0,
        STATUS_WATCH: 1,
        STATUS_READY: 2,
    }[row.digest_status]
    severity = _decimal_count(
        len(tuple(reason for reason in row.reason_codes if reason != READY_REASON)),
    )
    return (status_rank, -severity, -row.guidance_cut_ratio)


def _sort_rows(
    rows: tuple[MarketResearchEquityGuidanceCutDigestRow, ...],
) -> tuple[MarketResearchEquityGuidanceCutDigestRow, ...]:
    return tuple(
        sorted(
            rows,
            key=lambda row: (
                _row_sort_value(row),
                row.equity_symbol,
                row.guidance_event_key,
                row.research_key,
            ),
        ),
    )


def _report_status(
    rows: tuple[MarketResearchEquityGuidanceCutDigestRow, ...],
) -> str:
    if not rows:
        return STATUS_BLOCKED
    if any(row.digest_status == STATUS_BLOCKED for row in rows):
        return STATUS_BLOCKED
    if any(row.digest_status == STATUS_WATCH for row in rows):
        return STATUS_WATCH
    return STATUS_READY


def _status_count(
    rows: tuple[MarketResearchEquityGuidanceCutDigestRow, ...],
    status: str,
) -> Decimal:
    return _decimal_count(sum(1 for row in rows if row.digest_status == status))


def _reason_event_count(
    rows: tuple[MarketResearchEquityGuidanceCutDigestRow, ...],
    reason_code: str,
) -> Decimal:
    return _decimal_count(sum(1 for row in rows if reason_code in row.reason_codes))


def _reason_code_counts(
    rows: tuple[MarketResearchEquityGuidanceCutDigestRow, ...],
) -> tuple[MarketResearchEquityGuidanceCutDigestReasonCodeCount, ...]:
    event_count = _decimal_count(len(rows))
    if not rows:
        return (
            MarketResearchEquityGuidanceCutDigestReasonCodeCount(
                reason_code=NO_INPUTS_REASON,
                count=ONE,
                event_ratio=ZERO,
            ),
        )
    counts: dict[str, int] = {}
    for row in rows:
        for reason_code in row.reason_codes:
            counts[reason_code] = counts.get(reason_code, 0) + 1
    return tuple(
        MarketResearchEquityGuidanceCutDigestReasonCodeCount(
            reason_code=reason_code,
            count=_decimal_count(counts[reason_code]),
            event_ratio=_ratio(_decimal_count(counts[reason_code]), event_count),
        )
        for reason_code in REASON_CODE_SEQUENCE
        if reason_code in counts
    )


def _summary_reason_codes(
    rows: tuple[MarketResearchEquityGuidanceCutDigestRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return (NO_INPUTS_REASON,)
    seen: set[str] = set()
    for row in rows:
        seen.update(row.reason_codes)
    if len(seen) > 1 and READY_REASON in seen:
        seen.remove(READY_REASON)
    return tuple(reason for reason in REASON_CODE_SEQUENCE if reason in seen)


def _validate_row(row: MarketResearchEquityGuidanceCutDigestRow) -> None:
    if row.guidance_cut_abs != _guidance_cut_abs(
        row.previous_guidance_eps,
        row.current_guidance_eps,
    ):
        raise ValueError("guidance_cut_abs does not match guidance values")
    if row.guidance_cut_ratio != _safe_ratio(
        row.guidance_cut_abs,
        _decimal_abs(row.previous_guidance_eps),
    ):
        raise ValueError("guidance_cut_ratio does not match guidance values")
    if row.consensus_gap_ratio != _safe_ratio(
        _decimal_abs(row.current_guidance_eps - row.consensus_eps),
        _decimal_abs(row.consensus_eps),
    ):
        raise ValueError("consensus_gap_ratio does not match consensus values")
    if row.price_reaction_abs != _decimal_abs(row.price_reaction):
        raise ValueError("price_reaction_abs does not match price_reaction")
    if row.digest_status != _row_status(row.reason_codes):
        raise ValueError("digest_status does not match reason_codes")


def _validate_report(report: MarketResearchEquityGuidanceCutDigestReport) -> None:
    if report.event_count != _decimal_count(len(report.rows)):
        raise ValueError("event_count does not match rows")
    for status, field_name in (
        (STATUS_READY, "ready_event_count"),
        (STATUS_WATCH, "watch_event_count"),
        (STATUS_BLOCKED, "blocked_event_count"),
    ):
        if getattr(report, field_name) != _status_count(report.rows, status):
            raise ValueError(f"{field_name} does not match rows")
    for reason_code, field_name in (
        (MATERIAL_GUIDANCE_CUT_REASON, "material_guidance_cut_count"),
        (NEGATIVE_GUIDANCE_CUT_REASON, "negative_guidance_cut_count"),
        (CONSENSUS_GAP_REASON, "consensus_gap_count"),
        (THIN_SOURCES_REASON, "thin_source_count"),
        (LOW_CONFIDENCE_REASON, "low_confidence_count"),
        (MISSING_ACKNOWLEDGEMENT_REASON, "missing_acknowledgement_count"),
        (SLOW_ACKNOWLEDGEMENT_REASON, "slow_acknowledgement_count"),
        (STALE_OBSERVATION_REASON, "stale_observation_count"),
        (PRICE_REACTION_PRESSURE_REASON, "price_reaction_pressure_count"),
    ):
        if getattr(report, field_name) != _reason_event_count(report.rows, reason_code):
            raise ValueError(f"{field_name} does not match rows")
    if report.digest_status != _report_status(report.rows):
        raise ValueError("digest_status does not match rows")
    if report.recommended_next_step != NEXT_STEPS[report.digest_status]:
        raise ValueError("recommended_next_step does not match digest_status")
    if report.average_guidance_cut_ratio != _ratio(
        _decimal_sum(row.guidance_cut_ratio for row in report.rows),
        report.event_count,
    ):
        raise ValueError("average_guidance_cut_ratio does not match rows")
    if report.max_guidance_cut_ratio != max(
        (row.guidance_cut_ratio for row in report.rows),
        default=ZERO,
    ):
        raise ValueError("max_guidance_cut_ratio does not match rows")
    if report.average_source_count != _ratio(
        _decimal_sum(row.source_count for row in report.rows),
        report.event_count,
    ):
        raise ValueError("average_source_count does not match rows")
    if report.average_guidance_confidence != _ratio(
        _decimal_sum(row.guidance_confidence for row in report.rows),
        report.event_count,
    ):
        raise ValueError("average_guidance_confidence does not match rows")
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
    observations: Iterable[MarketResearchEquityGuidanceCutObservation],
) -> tuple[MarketResearchEquityGuidanceCutObservation, ...]:
    observation_tuple = tuple(observations)
    seen_keys: set[str] = set()
    for observation in observation_tuple:
        if type(observation) is not MarketResearchEquityGuidanceCutObservation:
            raise ValueError(
                "observations must contain "
                "MarketResearchEquityGuidanceCutObservation",
            )
        if observation.research_key in seen_keys:
            raise ValueError("research_key values must be unique")
        seen_keys.add(observation.research_key)
        _require_hard_flags("observation", observation)
    return observation_tuple


def _normalize_rows(
    rows: tuple[MarketResearchEquityGuidanceCutDigestRow, ...],
) -> tuple[MarketResearchEquityGuidanceCutDigestRow, ...]:
    if type(rows) is not tuple:
        raise ValueError("rows must be a tuple")
    for row in rows:
        if type(row) is not MarketResearchEquityGuidanceCutDigestRow:
            raise ValueError(
                "rows must contain "
                "MarketResearchEquityGuidanceCutDigestRow",
            )
        _require_hard_flags("row", row)
    if rows != _sort_rows(rows):
        raise ValueError("rows must be deterministic")
    return rows


def _normalize_reason_code_counts(
    items: tuple[MarketResearchEquityGuidanceCutDigestReasonCodeCount, ...],
) -> tuple[MarketResearchEquityGuidanceCutDigestReasonCodeCount, ...]:
    if type(items) is not tuple:
        raise ValueError("reason_code_counts must be a tuple")
    seen_reason_codes: set[str] = set()
    for item in items:
        if type(item) is not MarketResearchEquityGuidanceCutDigestReasonCodeCount:
            raise ValueError("reason_code_counts must contain reason count rows")
        if item.reason_code in seen_reason_codes:
            raise ValueError("reason_code_counts reason_code values must be unique")
        seen_reason_codes.add(item.reason_code)
        _require_hard_flags("reason code count", item)
    normalized = tuple(
        item
        for reason_code in REASON_CODE_SEQUENCE
        for item in items
        if item.reason_code == reason_code
    )
    if normalized != items:
        raise ValueError("reason_code_counts must be deterministic")
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
        research_key, source_config_version = item
        _require_public_string("research_key", research_key)
        _require_public_string("source_config_version", source_config_version)
        if research_key in seen_keys:
            raise ValueError("source_config_versions research_key values must be unique")
        seen_keys.add(research_key)
        pairs.append((research_key, source_config_version))
    if tuple(pairs) != tuple(sorted(pairs)):
        raise ValueError("source_config_versions must be deterministic")
    return tuple(pairs)


def _normalize_reason_codes(
    value: tuple[str, ...],
    *,
    order: tuple[str, ...],
) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ValueError("reason_codes must be a tuple")
    seen: set[str] = set()
    for reason_code in value:
        _require_reason_code("reason_code", reason_code)
        if reason_code in seen:
            raise ValueError("reason_codes must be unique")
        seen.add(reason_code)
    normalized = tuple(reason_code for reason_code in order if reason_code in seen)
    if normalized != value:
        raise ValueError("reason_codes must be deterministic")
    return normalized


def _require_status(field_name: str, value: str) -> None:
    if type(value) is not str or value not in DIGEST_STATUSES:
        raise ValueError(f"{field_name} must be a supported status")


def _require_reason_code(field_name: str, value: str) -> None:
    if type(value) is not str or value not in REASON_CODE_SEQUENCE:
        raise ValueError(f"{field_name} must be a supported reason code")


def _require_canonical_string(field_name: str, value: object) -> str:
    if type(value) is not str or not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical string")
    return value


def _require_public_string(field_name: str, value: object) -> str:
    text = _require_canonical_string(field_name, value)
    lowered = text.lower()
    if any(fragment in lowered for fragment in UNSAFE_TEXT_FRAGMENTS):
        raise ValueError(f"{field_name} must be redacted")
    return text


def _require_equity_symbol(field_name: str, value: object) -> str:
    text = _require_public_string(field_name, value)
    if text != text.upper() or not text.replace(".", "").isalnum():
        raise ValueError(f"{field_name} must be an uppercase public equity symbol")
    return text


def _require_reference(field_name: str, value: object) -> str:
    text = _require_canonical_string(field_name, value)
    lowered = text.lower()
    if "secret" in lowered or "token" in lowered:
        raise ValueError(f"{field_name} must be redacted")
    return text


def _require_redacted_reference(field_name: str, value: object) -> str:
    text = _require_canonical_string(field_name, value)
    lowered = text.lower()
    if "://" in lowered or "?" in lowered:
        raise ValueError(f"{field_name} must be redacted")
    if any(fragment in lowered for fragment in UNSAFE_TEXT_FRAGMENTS):
        raise ValueError(f"{field_name} must be redacted")
    return text


def _require_hard_flags(field_name: str, value: object) -> None:
    for flag in ("paper_only", "report_only", "readonly"):
        if getattr(value, flag, None) is not True:
            raise ValueError(f"{field_name} {flag} must be True")


def _require_positive_count_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_nonnegative_count_decimal(field_name, value)
    if decimal_value <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return decimal_value


def _require_nonnegative_count_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return decimal_value


def _require_positive_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return decimal_value


def _require_optional_nonnegative_decimal(
    field_name: str,
    value: object,
) -> Decimal | None:
    if value is None:
        return None
    decimal_value = _require_decimal(field_name, value)
    if decimal_value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return decimal_value


def _require_ratio_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value < ZERO or decimal_value > ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return decimal_value


def _require_signed_ratio_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value < -ONE or decimal_value > ONE:
        raise ValueError(f"{field_name} must be between -1 and 1")
    return decimal_value


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal or not value.is_finite():
        raise ValueError(f"{field_name} must be a finite Decimal")
    return _quantize(value)


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _as_optional_utc(field_name: str, value: object) -> datetime | None:
    if value is None:
        return None
    return _as_utc(field_name, value)


def _seconds_between(start: datetime, end: datetime) -> Decimal:
    if end < start:
        raise ValueError("datetime interval must be nonnegative")
    delta = end - start
    return _quantize(
        Decimal(delta.days * 86400 + delta.seconds)
        + (Decimal(delta.microseconds) / MICROSECONDS_PER_SECOND),
    )


def _redacted_reference(value: str) -> str:
    lowered = value.lower()
    if "://" in lowered or "?" in lowered:
        return f"sha256:{sha256(value.encode()).hexdigest()[:12]}"
    if any(fragment in lowered for fragment in UNSAFE_TEXT_FRAGMENTS):
        return f"sha256:{sha256(value.encode()).hexdigest()[:12]}"
    return value


def _decimal_abs(value: Decimal) -> Decimal:
    return _quantize(abs(value))


def _guidance_cut_abs(previous_guidance_eps: Decimal, current_guidance_eps: Decimal) -> Decimal:
    if current_guidance_eps >= previous_guidance_eps:
        return ZERO
    return _decimal_abs(previous_guidance_eps - current_guidance_eps)


def _decimal_count(value: int) -> Decimal:
    return _quantize(Decimal(value))


def _decimal_sum(values: Iterable[Decimal]) -> Decimal:
    total = ZERO
    for value in values:
        total += value
    return _quantize(total)


def _safe_ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO:
        if numerator == ZERO:
            return ZERO
        return ONE
    return _ratio(numerator, denominator)


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO:
        return ZERO
    return _quantize(numerator / denominator)


def _quantize(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(QUANT)


def _require_payload_safe_value(field_name: str, value: object) -> None:
    if type(value) is Decimal:
        normalized = _require_decimal(field_name, value)
        if normalized != value:
            raise ValueError(f"{field_name} must be quantized to six decimals")
        return
    if type(value) is datetime:
        _as_utc(field_name, value)
        if value.tzinfo is not UTC:
            raise ValueError(f"{field_name} must be normalized to UTC")
        return
    if is_dataclass(value) and not isinstance(value, type):
        if type(value) not in _PUBLIC_DATACLASS_TYPES:
            raise ValueError(f"{field_name} must be a supported public dataclass")
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
    if type(value) in (str, bool) or value is None:
        return
    if type(value) in (list, dict, set):
        raise ValueError(f"{field_name} must remain constructor-normalized")
    raise ValueError(f"{field_name} must be safe for payload serialization")


def _reconstruct_public_dataclass(field_name: str, value: object) -> None:
    type_ = type(value)
    try:
        type_(**{field.name: getattr(value, field.name) for field in fields(value)})
    except (ArithmeticError, TypeError, ValueError) as exc:
        raise ValueError(f"{field_name} must remain constructor-valid") from exc


def _payload_value(value: Any) -> Any:
    if type(value) is Decimal:
        return f"{value:.6f}"
    if type(value) is datetime:
        return value.astimezone(UTC).isoformat()
    if is_dataclass(value) and not isinstance(value, type):
        return {
            field.name: _payload_value(getattr(value, field.name))
            for field in fields(value)
        }
    if type(value) is tuple:
        return [_payload_value(item) for item in value]
    if type(value) is list:
        return [_payload_value(item) for item in value]
    if type(value) is dict:
        return {key: _payload_value(item) for key, item in value.items()}
    return value
