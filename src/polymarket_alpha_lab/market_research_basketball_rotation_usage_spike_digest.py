"""Pure Phase 1 basketball rotation usage spike digest reducer."""

from __future__ import annotations

from dataclasses import dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from typing import Any


DEFAULT_MARKET_RESEARCH_BASKETBALL_ROTATION_USAGE_SPIKE_DIGEST_CONFIG_VERSION = (
    "market-research-basketball-rotation-usage-spike-digest-v0"
)

STATUS_READY = "ready"
STATUS_WATCH = "watch"
STATUS_BLOCKED = "blocked"
STATUSES = (STATUS_READY, STATUS_WATCH, STATUS_BLOCKED)

REASON_PREFIX = "market_research_basketball_rotation_usage_spike_digest_"
MINUTES_SPIKE_REASON = f"{REASON_PREFIX}minutes_spike"
USAGE_RATE_SPIKE_REASON = f"{REASON_PREFIX}usage_rate_spike"
COMBINED_SPIKE_REASON = f"{REASON_PREFIX}combined_spike"
SOURCE_GAP_REASON = f"{REASON_PREFIX}source_gap"
STALE_OBSERVATION_REASON = f"{REASON_PREFIX}stale_observation"
CONFIDENCE_GAP_REASON = f"{REASON_PREFIX}confidence_gap"
READY_REASON = f"{REASON_PREFIX}ready"
NO_INPUTS_REASON = f"{REASON_PREFIX}no_inputs"

ROW_REASON_CODE_SEQUENCE = (
    MINUTES_SPIKE_REASON,
    USAGE_RATE_SPIKE_REASON,
    COMBINED_SPIKE_REASON,
    SOURCE_GAP_REASON,
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
PHASE_FLAG_FIELDS = ("paper_only", "report_only", "readonly")


def _piece(*parts: str) -> str:
    return "".join(parts)


UNSAFE_TEXT_FRAGMENTS = frozenset(
    (
        _piece("mar", "ket_", "slug"),
        _piece("ques", "tion"),
        _piece("payload_", "json"),
        _piece("b", "uy"),
        _piece("s", "ell"),
        _piece("tr", "ade"),
        _piece("wa", "llet"),
        _piece("ord", "er"),
        _piece("pos", "ition"),
        _piece("au", "th"),
        _piece("can", "cel"),
        _piece("ex", "change"),
        _piece("mut", "ation"),
        _piece("re", "place"),
        _piece("sec", "ret"),
        _piece("pri", "vate_", "key"),
        _piece("api", "_", "key"),
        _piece("to", "ken"),
    ),
)

__all__ = (
    "DEFAULT_MARKET_RESEARCH_BASKETBALL_ROTATION_USAGE_SPIKE_DIGEST_CONFIG_VERSION",
    "MarketResearchBasketballRotationUsageSpikeDigestConfig",
    "MarketResearchBasketballRotationUsageSpikeDigestObservation",
    "MarketResearchBasketballRotationUsageSpikeDigestReasonCodeCount",
    "MarketResearchBasketballRotationUsageSpikeDigestReport",
    "MarketResearchBasketballRotationUsageSpikeDigestRow",
    "build_market_research_basketball_rotation_usage_spike_digest",
    "market_research_basketball_rotation_usage_spike_digest_payload",
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
class MarketResearchBasketballRotationUsageSpikeDigestConfig(_FinalPublicDataclass):
    config_version: str = (
        DEFAULT_MARKET_RESEARCH_BASKETBALL_ROTATION_USAGE_SPIKE_DIGEST_CONFIG_VERSION
    )
    max_observation_age_seconds: Decimal = Decimal("1800.000000")
    min_source_count: Decimal = Decimal("2.000000")
    watch_minutes_delta: Decimal = Decimal("6.000000")
    blocked_minutes_delta: Decimal = Decimal("10.000000")
    watch_usage_rate_delta: Decimal = Decimal("0.040000")
    blocked_usage_rate_delta: Decimal = Decimal("0.080000")
    min_confidence: Decimal = Decimal("0.700000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            MarketResearchBasketballRotationUsageSpikeDigestConfig,
            "config",
        )
        _require_canonical_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_MARKET_RESEARCH_BASKETBALL_ROTATION_USAGE_SPIKE_DIGEST_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in ("max_observation_age_seconds", "min_source_count"):
            _require_positive_count_decimal(field_name, getattr(self, field_name))
        for field_name in ("watch_minutes_delta", "blocked_minutes_delta"):
            _require_positive_decimal(field_name, getattr(self, field_name))
        for field_name in (
            "watch_usage_rate_delta",
            "blocked_usage_rate_delta",
            "min_confidence",
        ):
            _require_ratio_decimal(field_name, getattr(self, field_name))
        if self.watch_minutes_delta > self.blocked_minutes_delta:
            raise ValueError("watch_minutes_delta must not exceed blocked_minutes_delta")
        if self.watch_usage_rate_delta > self.blocked_usage_rate_delta:
            raise ValueError(
                "watch_usage_rate_delta must not exceed blocked_usage_rate_delta",
            )
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class MarketResearchBasketballRotationUsageSpikeDigestObservation(
    _FinalPublicDataclass,
):
    condition_id: str
    signal_id: str
    event_id: str
    team_id: str
    player_id: str
    observed_at: datetime
    baseline_minutes: Decimal
    projected_minutes: Decimal
    baseline_usage_rate: Decimal
    projected_usage_rate: Decimal
    source_count: Decimal
    confidence: Decimal
    source_config_version: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            MarketResearchBasketballRotationUsageSpikeDigestObservation,
            "observation",
        )
        for field_name in (
            "condition_id",
            "signal_id",
            "event_id",
            "team_id",
            "player_id",
            "source_config_version",
        ):
            _require_public_string(field_name, getattr(self, field_name))
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in ("baseline_minutes", "projected_minutes"):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in ("baseline_usage_rate", "projected_usage_rate", "confidence"):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "source_count",
            _require_nonnegative_count_decimal("source_count", self.source_count),
        )
        _require_hard_flags("observation", self)


@dataclass(frozen=True)
class MarketResearchBasketballRotationUsageSpikeDigestRow(_FinalPublicDataclass):
    condition_id: str
    signal_id: str
    event_id: str
    team_id: str
    player_id: str
    spike_status: str
    observed_at: datetime
    observation_age_seconds: Decimal
    baseline_minutes: Decimal
    projected_minutes: Decimal
    minutes_delta: Decimal
    minutes_spike_delta: Decimal
    baseline_usage_rate: Decimal
    projected_usage_rate: Decimal
    usage_rate_delta: Decimal
    usage_rate_spike_delta: Decimal
    source_count: Decimal
    confidence: Decimal
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            MarketResearchBasketballRotationUsageSpikeDigestRow,
            "row",
        )
        for field_name in (
            "condition_id",
            "signal_id",
            "event_id",
            "team_id",
            "player_id",
        ):
            _require_public_string(field_name, getattr(self, field_name))
        _require_status("spike_status", self.spike_status)
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in (
            "observation_age_seconds",
            "baseline_minutes",
            "projected_minutes",
            "minutes_spike_delta",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "minutes_delta",
            _require_signed_decimal("minutes_delta", self.minutes_delta),
        )
        for field_name in (
            "baseline_usage_rate",
            "projected_usage_rate",
            "usage_rate_spike_delta",
            "confidence",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "usage_rate_delta",
            _require_signed_ratio_decimal("usage_rate_delta", self.usage_rate_delta),
        )
        object.__setattr__(
            self,
            "source_count",
            _require_nonnegative_count_decimal("source_count", self.source_count),
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
class MarketResearchBasketballRotationUsageSpikeDigestReasonCodeCount(
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
            MarketResearchBasketballRotationUsageSpikeDigestReasonCodeCount,
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
class MarketResearchBasketballRotationUsageSpikeDigestReport(_FinalPublicDataclass):
    generated_at: datetime
    config_version: str
    digest_status: str
    recommended_next_step: str
    observation_count: Decimal
    ready_observation_count: Decimal
    watch_observation_count: Decimal
    blocked_observation_count: Decimal
    minutes_spike_count: Decimal
    usage_rate_spike_count: Decimal
    combined_spike_count: Decimal
    source_gap_count: Decimal
    stale_observation_count: Decimal
    confidence_gap_count: Decimal
    average_minutes_spike_delta: Decimal
    average_usage_rate_spike_delta: Decimal
    max_minutes_spike_delta: Decimal
    max_usage_rate_spike_delta: Decimal
    max_observation_age_seconds: Decimal
    min_source_count: Decimal
    watch_minutes_delta: Decimal
    blocked_minutes_delta: Decimal
    watch_usage_rate_delta: Decimal
    blocked_usage_rate_delta: Decimal
    min_confidence: Decimal
    rows: tuple[MarketResearchBasketballRotationUsageSpikeDigestRow, ...]
    source_config_versions: tuple[tuple[str, str], ...]
    reason_code_counts: tuple[
        MarketResearchBasketballRotationUsageSpikeDigestReasonCodeCount,
        ...,
    ]
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            MarketResearchBasketballRotationUsageSpikeDigestReport,
            "report",
        )
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_MARKET_RESEARCH_BASKETBALL_ROTATION_USAGE_SPIKE_DIGEST_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        _require_status("digest_status", self.digest_status)
        _require_canonical_string("recommended_next_step", self.recommended_next_step)
        for field_name in (
            "observation_count",
            "ready_observation_count",
            "watch_observation_count",
            "blocked_observation_count",
            "minutes_spike_count",
            "usage_rate_spike_count",
            "combined_spike_count",
            "source_gap_count",
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
            "average_minutes_spike_delta",
            "max_minutes_spike_delta",
            "watch_minutes_delta",
            "blocked_minutes_delta",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "average_usage_rate_spike_delta",
            "max_usage_rate_spike_delta",
            "watch_usage_rate_delta",
            "blocked_usage_rate_delta",
            "min_confidence",
        ):
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
    MarketResearchBasketballRotationUsageSpikeDigestConfig,
    MarketResearchBasketballRotationUsageSpikeDigestObservation,
    MarketResearchBasketballRotationUsageSpikeDigestRow,
    MarketResearchBasketballRotationUsageSpikeDigestReasonCodeCount,
    MarketResearchBasketballRotationUsageSpikeDigestReport,
)


def build_market_research_basketball_rotation_usage_spike_digest(
    observations: tuple[MarketResearchBasketballRotationUsageSpikeDigestObservation, ...],
    *,
    config: MarketResearchBasketballRotationUsageSpikeDigestConfig | None = None,
    generated_at: datetime,
) -> MarketResearchBasketballRotationUsageSpikeDigestReport:
    cfg = config or MarketResearchBasketballRotationUsageSpikeDigestConfig()
    if type(cfg) is not MarketResearchBasketballRotationUsageSpikeDigestConfig:
        raise ValueError(
            "config must be exactly "
            "MarketResearchBasketballRotationUsageSpikeDigestConfig",
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
    return MarketResearchBasketballRotationUsageSpikeDigestReport(
        generated_at=generated_at_utc,
        config_version=cfg.config_version,
        digest_status=report_status,
        recommended_next_step=_recommended_next_step(report_status, rows),
        observation_count=_count_decimal(len(rows)),
        ready_observation_count=_status_count(rows, STATUS_READY),
        watch_observation_count=_status_count(rows, STATUS_WATCH),
        blocked_observation_count=_status_count(rows, STATUS_BLOCKED),
        minutes_spike_count=_reason_row_count(rows, MINUTES_SPIKE_REASON),
        usage_rate_spike_count=_reason_row_count(rows, USAGE_RATE_SPIKE_REASON),
        combined_spike_count=_reason_row_count(rows, COMBINED_SPIKE_REASON),
        source_gap_count=_reason_row_count(rows, SOURCE_GAP_REASON),
        stale_observation_count=_reason_row_count(rows, STALE_OBSERVATION_REASON),
        confidence_gap_count=_reason_row_count(rows, CONFIDENCE_GAP_REASON),
        average_minutes_spike_delta=_average(row.minutes_spike_delta for row in rows),
        average_usage_rate_spike_delta=_average(row.usage_rate_spike_delta for row in rows),
        max_minutes_spike_delta=max(
            (row.minutes_spike_delta for row in rows),
            default=ZERO,
        ),
        max_usage_rate_spike_delta=max(
            (row.usage_rate_spike_delta for row in rows),
            default=ZERO,
        ),
        max_observation_age_seconds=cfg.max_observation_age_seconds,
        min_source_count=cfg.min_source_count,
        watch_minutes_delta=cfg.watch_minutes_delta,
        blocked_minutes_delta=cfg.blocked_minutes_delta,
        watch_usage_rate_delta=cfg.watch_usage_rate_delta,
        blocked_usage_rate_delta=cfg.blocked_usage_rate_delta,
        min_confidence=cfg.min_confidence,
        rows=rows,
        source_config_versions=tuple(
            sorted(
                (
                    observation.signal_id,
                    observation.source_config_version,
                )
                for observation in normalized_observations
            ),
        ),
        reason_code_counts=_reason_code_counts(rows),
        reason_codes=_summary_reason_codes(rows),
    )


def market_research_basketball_rotation_usage_spike_digest_payload(
    report: MarketResearchBasketballRotationUsageSpikeDigestReport,
) -> dict[str, Any]:
    if type(report) is not MarketResearchBasketballRotationUsageSpikeDigestReport:
        raise ValueError(
            "report must be exactly MarketResearchBasketballRotationUsageSpikeDigestReport",
        )
    _require_payload_safe_value("report", report)
    payload = _payload_value(report)
    if type(payload) is not dict:
        raise ValueError("payload must be an object")
    return payload


def _row_for_observation(
    observation: MarketResearchBasketballRotationUsageSpikeDigestObservation,
    *,
    config: MarketResearchBasketballRotationUsageSpikeDigestConfig,
    generated_at: datetime,
) -> MarketResearchBasketballRotationUsageSpikeDigestRow:
    if observation.observed_at > generated_at:
        raise ValueError("observed_at must not be in the future")
    observation_age_seconds = _age_seconds(generated_at, observation.observed_at)
    minutes_delta = _quantize_decimal(
        observation.projected_minutes - observation.baseline_minutes,
    )
    usage_rate_delta = _quantize_decimal(
        observation.projected_usage_rate - observation.baseline_usage_rate,
    )
    minutes_spike_delta = _positive_delta(minutes_delta)
    usage_rate_spike_delta = _positive_delta(usage_rate_delta)
    reason_codes = _row_reason_codes(
        observation=observation,
        config=config,
        observation_age_seconds=observation_age_seconds,
        minutes_spike_delta=minutes_spike_delta,
        usage_rate_spike_delta=usage_rate_spike_delta,
    )
    return MarketResearchBasketballRotationUsageSpikeDigestRow(
        condition_id=observation.condition_id,
        signal_id=observation.signal_id,
        event_id=observation.event_id,
        team_id=observation.team_id,
        player_id=observation.player_id,
        spike_status=_row_status(
            reason_codes,
            config=config,
            minutes_spike_delta=minutes_spike_delta,
            usage_rate_spike_delta=usage_rate_spike_delta,
        ),
        observed_at=observation.observed_at,
        observation_age_seconds=observation_age_seconds,
        baseline_minutes=observation.baseline_minutes,
        projected_minutes=observation.projected_minutes,
        minutes_delta=minutes_delta,
        minutes_spike_delta=minutes_spike_delta,
        baseline_usage_rate=observation.baseline_usage_rate,
        projected_usage_rate=observation.projected_usage_rate,
        usage_rate_delta=usage_rate_delta,
        usage_rate_spike_delta=usage_rate_spike_delta,
        source_count=observation.source_count,
        confidence=observation.confidence,
        reason_codes=reason_codes,
    )


def _row_reason_codes(
    *,
    observation: MarketResearchBasketballRotationUsageSpikeDigestObservation,
    config: MarketResearchBasketballRotationUsageSpikeDigestConfig,
    observation_age_seconds: Decimal,
    minutes_spike_delta: Decimal,
    usage_rate_spike_delta: Decimal,
) -> tuple[str, ...]:
    reasons: list[str] = []
    if minutes_spike_delta >= config.watch_minutes_delta:
        reasons.append(MINUTES_SPIKE_REASON)
    if usage_rate_spike_delta >= config.watch_usage_rate_delta:
        reasons.append(USAGE_RATE_SPIKE_REASON)
    if (
        minutes_spike_delta >= config.watch_minutes_delta
        and usage_rate_spike_delta >= config.watch_usage_rate_delta
    ):
        reasons.append(COMBINED_SPIKE_REASON)
    if observation.source_count < config.min_source_count:
        reasons.append(SOURCE_GAP_REASON)
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
    config: MarketResearchBasketballRotationUsageSpikeDigestConfig,
    minutes_spike_delta: Decimal,
    usage_rate_spike_delta: Decimal,
) -> str:
    if reason_codes == (READY_REASON,):
        return STATUS_READY
    if (
        minutes_spike_delta >= config.blocked_minutes_delta
        or usage_rate_spike_delta >= config.blocked_usage_rate_delta
        or COMBINED_SPIKE_REASON in reason_codes
        or STALE_OBSERVATION_REASON in reason_codes
        or CONFIDENCE_GAP_REASON in reason_codes
    ):
        return STATUS_BLOCKED
    return STATUS_WATCH


def _row_sort_key(
    row: MarketResearchBasketballRotationUsageSpikeDigestRow,
) -> tuple[int, Decimal, Decimal, Decimal, str, str]:
    rank = {
        STATUS_BLOCKED: 0,
        STATUS_WATCH: 1,
        STATUS_READY: 2,
    }[row.spike_status]
    severity = _count_decimal(
        len(tuple(reason for reason in row.reason_codes if reason != READY_REASON)),
    )
    return (
        rank,
        -severity,
        -row.minutes_spike_delta,
        -row.usage_rate_spike_delta,
        row.player_id,
        row.signal_id,
    )


def _report_status(
    rows: tuple[MarketResearchBasketballRotationUsageSpikeDigestRow, ...],
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
    rows: tuple[MarketResearchBasketballRotationUsageSpikeDigestRow, ...],
) -> str:
    if not rows:
        return "hold_report_only_market_research_basketball_rotation_usage_spike_digest"
    if status == STATUS_BLOCKED:
        return "block_report_only_market_research_basketball_rotation_usage_spike_digest"
    if status == STATUS_WATCH:
        return "review_report_only_market_research_basketball_rotation_usage_spike_digest"
    return "allow_report_only_market_research_basketball_rotation_usage_spike_digest"


def _status_count(
    rows: tuple[MarketResearchBasketballRotationUsageSpikeDigestRow, ...],
    status: str,
) -> Decimal:
    return _count_decimal(sum(1 for row in rows if row.spike_status == status))


def _reason_row_count(
    rows: tuple[MarketResearchBasketballRotationUsageSpikeDigestRow, ...],
    reason_code: str,
) -> Decimal:
    return _count_decimal(sum(1 for row in rows if reason_code in row.reason_codes))


def _reason_code_counts(
    rows: tuple[MarketResearchBasketballRotationUsageSpikeDigestRow, ...],
) -> tuple[MarketResearchBasketballRotationUsageSpikeDigestReasonCodeCount, ...]:
    if not rows:
        return (
            MarketResearchBasketballRotationUsageSpikeDigestReasonCodeCount(
                reason_code=NO_INPUTS_REASON,
                count=ONE,
                observation_ratio=ZERO,
            ),
        )
    observation_count = _count_decimal(len(rows))
    counts: dict[str, int] = {}
    for row in rows:
        for reason_code in row.reason_codes:
            counts[reason_code] = counts.get(reason_code, 0) + 1
    return tuple(
        MarketResearchBasketballRotationUsageSpikeDigestReasonCodeCount(
            reason_code=reason_code,
            count=_count_decimal(counts[reason_code]),
            observation_ratio=_ratio(_count_decimal(counts[reason_code]), observation_count),
        )
        for reason_code in REPORT_REASON_CODE_SEQUENCE
        if reason_code in counts
    )


def _summary_reason_codes(
    rows: tuple[MarketResearchBasketballRotationUsageSpikeDigestRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return (NO_INPUTS_REASON,)
    seen: set[str] = set()
    for row in rows:
        seen.update(row.reason_codes)
    if len(seen) > 1 and READY_REASON in seen:
        seen.remove(READY_REASON)
    return tuple(reason for reason in REPORT_REASON_CODE_SEQUENCE if reason in seen)


def _validate_row(row: MarketResearchBasketballRotationUsageSpikeDigestRow) -> None:
    if row.minutes_delta != _quantize_decimal(row.projected_minutes - row.baseline_minutes):
        raise ValueError("minutes_delta must match minutes inputs")
    if row.minutes_spike_delta != _positive_delta(row.minutes_delta):
        raise ValueError("minutes_spike_delta must match minutes_delta")
    if row.usage_rate_delta != _quantize_decimal(
        row.projected_usage_rate - row.baseline_usage_rate,
    ):
        raise ValueError("usage_rate_delta must match usage rate inputs")
    if row.usage_rate_spike_delta != _positive_delta(row.usage_rate_delta):
        raise ValueError("usage_rate_spike_delta must match usage_rate_delta")
    if row.spike_status == STATUS_READY and row.reason_codes != (READY_REASON,):
        raise ValueError("spike_status must match reason_codes")
    if row.spike_status != STATUS_READY and READY_REASON in row.reason_codes:
        raise ValueError("spike_status must match reason_codes")
    has_minutes = MINUTES_SPIKE_REASON in row.reason_codes
    has_usage = USAGE_RATE_SPIKE_REASON in row.reason_codes
    has_combined = COMBINED_SPIKE_REASON in row.reason_codes
    if has_combined != (has_minutes and has_usage):
        raise ValueError("combined reason must match spike reasons")


def _validate_report(report: MarketResearchBasketballRotationUsageSpikeDigestReport) -> None:
    if report.observation_count != _count_decimal(len(report.rows)):
        raise ValueError("observation_count must match rows")
    if report.ready_observation_count != _status_count(report.rows, STATUS_READY):
        raise ValueError("ready_observation_count must match rows")
    if report.watch_observation_count != _status_count(report.rows, STATUS_WATCH):
        raise ValueError("watch_observation_count must match rows")
    if report.blocked_observation_count != _status_count(report.rows, STATUS_BLOCKED):
        raise ValueError("blocked_observation_count must match rows")
    if (
        report.ready_observation_count
        + report.watch_observation_count
        + report.blocked_observation_count
        != report.observation_count
    ):
        raise ValueError("status counts must match rows")
    expected_counts = (
        (MINUTES_SPIKE_REASON, report.minutes_spike_count),
        (USAGE_RATE_SPIKE_REASON, report.usage_rate_spike_count),
        (COMBINED_SPIKE_REASON, report.combined_spike_count),
        (SOURCE_GAP_REASON, report.source_gap_count),
        (STALE_OBSERVATION_REASON, report.stale_observation_count),
        (CONFIDENCE_GAP_REASON, report.confidence_gap_count),
    )
    for reason_code, expected_count in expected_counts:
        if expected_count != _reason_row_count(report.rows, reason_code):
            raise ValueError(f"{reason_code} count must match rows")
    if report.average_minutes_spike_delta != _average(
        row.minutes_spike_delta for row in report.rows
    ):
        raise ValueError("average_minutes_spike_delta must match rows")
    if report.average_usage_rate_spike_delta != _average(
        row.usage_rate_spike_delta for row in report.rows
    ):
        raise ValueError("average_usage_rate_spike_delta must match rows")
    if report.max_minutes_spike_delta != max(
        (row.minutes_spike_delta for row in report.rows),
        default=ZERO,
    ):
        raise ValueError("max_minutes_spike_delta must match rows")
    if report.max_usage_rate_spike_delta != max(
        (row.usage_rate_spike_delta for row in report.rows),
        default=ZERO,
    ):
        raise ValueError("max_usage_rate_spike_delta must match rows")
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
    for row in report.rows:
        if row.observed_at > report.generated_at:
            raise ValueError("row observed_at must not be in the future")


def _normalize_observations(
    value: tuple[MarketResearchBasketballRotationUsageSpikeDigestObservation, ...],
) -> tuple[MarketResearchBasketballRotationUsageSpikeDigestObservation, ...]:
    if type(value) is not tuple:
        raise ValueError("observations must be a tuple")
    seen_signal_ids: set[str] = set()
    observations: list[MarketResearchBasketballRotationUsageSpikeDigestObservation] = []
    for observation in value:
        if type(observation) is not MarketResearchBasketballRotationUsageSpikeDigestObservation:
            raise ValueError(
                "observations must contain "
                "MarketResearchBasketballRotationUsageSpikeDigestObservation values",
            )
        _require_payload_safe_value("observation", observation)
        if observation.signal_id in seen_signal_ids:
            raise ValueError("observations must use unique signal_id values")
        seen_signal_ids.add(observation.signal_id)
        observations.append(
            MarketResearchBasketballRotationUsageSpikeDigestObservation(
                **{
                    field.name: getattr(observation, field.name)
                    for field in fields(observation)
                },
            ),
        )
    return tuple(observations)


def _require_canonical_rows(
    value: tuple[MarketResearchBasketballRotationUsageSpikeDigestRow, ...],
) -> tuple[MarketResearchBasketballRotationUsageSpikeDigestRow, ...]:
    if type(value) is not tuple:
        raise ValueError("rows must be a tuple")
    seen_signal_ids: set[str] = set()
    for row in value:
        if type(row) is not MarketResearchBasketballRotationUsageSpikeDigestRow:
            raise ValueError(
                "rows must contain MarketResearchBasketballRotationUsageSpikeDigestRow values",
            )
        _require_hard_flags("rows", row)
        if row.signal_id in seen_signal_ids:
            raise ValueError("rows must use unique signal_id values")
        seen_signal_ids.add(row.signal_id)
    if value != tuple(sorted(value, key=_row_sort_key)):
        raise ValueError("rows must use deterministic sequence")
    return value


def _require_source_config_versions(
    value: tuple[tuple[str, str], ...],
) -> tuple[tuple[str, str], ...]:
    if type(value) is not tuple:
        raise ValueError("source_config_versions must be a tuple")
    seen_signal_ids: set[str] = set()
    for item in value:
        if type(item) is not tuple or len(item) != 2:
            raise ValueError("source_config_versions must contain tuple pair values")
        signal_id, source_config_version = item
        _require_public_string("source_config_versions signal_id", signal_id)
        _require_public_string(
            "source_config_versions source_config_version",
            source_config_version,
        )
        if signal_id in seen_signal_ids:
            raise ValueError("source_config_versions signal_id values must be unique")
        seen_signal_ids.add(signal_id)
    if value != tuple(sorted(value)):
        raise ValueError("source_config_versions must use canonical sequence")
    return value


def _require_canonical_reason_code_counts(
    value: tuple[
        MarketResearchBasketballRotationUsageSpikeDigestReasonCodeCount,
        ...,
    ],
) -> tuple[MarketResearchBasketballRotationUsageSpikeDigestReasonCodeCount, ...]:
    if type(value) is not tuple:
        raise ValueError("reason_code_counts must be a tuple")
    seen: set[str] = set()
    for count in value:
        if type(count) is not MarketResearchBasketballRotationUsageSpikeDigestReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "MarketResearchBasketballRotationUsageSpikeDigestReasonCodeCount values",
            )
        _require_hard_flags("reason_code_counts", count)
        if count.reason_code in seen:
            raise ValueError("reason_code_counts reason_code values must be unique")
        seen.add(count.reason_code)
    expected = tuple(reason for reason in REPORT_REASON_CODE_SEQUENCE if reason in seen)
    if tuple(count.reason_code for count in value) != expected:
        raise ValueError("reason_code_counts must use canonical sequence")
    return value


def _require_canonical_reason_codes(
    field_name: str,
    value: tuple[str, ...],
    sequence: tuple[str, ...],
) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ValueError(f"{field_name} must be a tuple")
    if not value:
        raise ValueError(f"{field_name} must not be empty")
    for reason_code in value:
        _require_reason_code(field_name, reason_code)
        if reason_code not in sequence:
            raise ValueError(f"{field_name} must contain known reason codes")
    expected = tuple(reason for reason in sequence if reason in set(value))
    if value != expected:
        raise ValueError(f"{field_name} must use canonical sequence")
    if len(set(value)) != len(value):
        raise ValueError(f"{field_name} must be unique")
    return value


def _average(values: Any) -> Decimal:
    normalized_values = tuple(values)
    if not normalized_values:
        return ZERO
    return _ratio(sum(normalized_values, ZERO), _count_decimal(len(normalized_values)))


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO:
        return ZERO
    return _quantize_decimal(numerator / denominator)


def _positive_delta(value: Decimal) -> Decimal:
    if value <= ZERO:
        return ZERO
    return _quantize_decimal(value)


def _age_seconds(later: datetime, earlier: datetime) -> Decimal:
    delta = later - earlier
    return _quantize_decimal(
        Decimal(delta.days) * SECONDS_PER_DAY
        + Decimal(delta.seconds)
        + (Decimal(delta.microseconds) / MICROSECONDS_PER_SECOND),
    )


def _count_decimal(value: int) -> Decimal:
    return _quantize_decimal(Decimal(value))


def _require_positive_count_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_nonnegative_count_decimal(field_name, value)
    if normalized <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _require_nonnegative_count_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_nonnegative_decimal(field_name, value)
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{field_name} must be integral")
    return normalized


def _require_positive_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_nonnegative_decimal(field_name, value)
    if normalized <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _require_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_six_place_decimal(field_name, value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _require_signed_decimal(field_name: str, value: object) -> Decimal:
    return _require_six_place_decimal(field_name, value)


def _require_ratio_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_nonnegative_decimal(field_name, value)
    if normalized > ONE:
        raise ValueError(f"{field_name} must be between zero and one")
    return normalized


def _require_signed_ratio_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_six_place_decimal(field_name, value)
    if normalized < -ONE or normalized > ONE:
        raise ValueError(f"{field_name} must be between negative one and one")
    return normalized


def _require_six_place_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    if value.as_tuple().exponent != -6:
        raise ValueError(f"{field_name} must be an exact six-place Decimal")
    if value == ZERO and value.is_signed():
        raise ValueError(f"{field_name} must be canonical")
    if value != _quantize_decimal(value):
        raise ValueError(f"{field_name} must be quantized to six decimals")
    return value


def _quantize_decimal(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        normalized = value.quantize(QUANT)
    if not normalized.is_finite():
        raise ValueError("decimal value must be finite")
    if normalized == ZERO:
        return ZERO
    return normalized


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")


def _require_public_string(field_name: str, value: object) -> None:
    _require_canonical_string(field_name, value)
    lowered = value.lower()
    if any(fragment in lowered for fragment in UNSAFE_TEXT_FRAGMENTS):
        raise ValueError(f"{field_name} must be redacted safe")


def _require_status(field_name: str, value: object) -> None:
    _require_canonical_string(field_name, value)
    if value not in STATUSES:
        raise ValueError(f"{field_name} must be ready, watch, or blocked")


def _require_reason_code(field_name: str, value: object) -> None:
    _require_canonical_string(field_name, value)
    if value not in REPORT_REASON_CODE_SEQUENCE:
        raise ValueError(f"{field_name} must contain known reason codes")


def _require_hard_flags(field_name: str, value: object) -> None:
    for flag_name in PHASE_FLAG_FIELDS:
        if getattr(value, flag_name, None) is not True:
            raise ValueError(f"{field_name} {flag_name} must be True")


def _require_exact_type(value: object, type_: type[object], field_name: str) -> None:
    if type(value) is not type_:
        raise ValueError(f"{field_name} must be exactly {type_.__name__}")


def _require_payload_safe_value(field_name: str, value: object) -> None:
    if isinstance(value, Decimal):
        _require_six_place_decimal(field_name, value)
        return
    if type(value) is datetime:
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
