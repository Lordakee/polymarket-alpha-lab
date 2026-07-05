"""Pure research contradiction priority digest for Phase 1 diagnostics."""

from __future__ import annotations

from dataclasses import dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from typing import Any


DEFAULT_MARKET_RESEARCH_CONTRADICTION_PRIORITY_CONFIG_VERSION = (
    "market-research-contradiction-priority-v0"
)

REASON_PREFIX = "market_research_contradiction_priority_digest_"
NO_INPUTS_REASON = f"{REASON_PREFIX}no_inputs"
EMPTY_REASON = f"{REASON_PREFIX}empty"
CONTRADICTION_COUNT_REASON = f"{REASON_PREFIX}contradiction_count_present"
SOURCE_SPREAD_REASON = f"{REASON_PREFIX}source_reliability_spread_elevated"
EVIDENCE_RECENT_REASON = f"{REASON_PREFIX}evidence_recent"
MARKET_MOVED_REASON = f"{REASON_PREFIX}market_moved_after_contradiction"
NO_CONTRADICTIONS_REASON = f"{REASON_PREFIX}no_contradictions_observed"
HIGH_PRIORITY_REASON = f"{REASON_PREFIX}high_priority_contradiction_review"
MEDIUM_PRIORITY_REASON = f"{REASON_PREFIX}medium_priority_contradiction_review"
LOW_PRIORITY_REASON = f"{REASON_PREFIX}low_priority_contradiction_review"

ROW_PRIORITY_STATUSES = ("low", "medium", "high")
REPORT_PRIORITY_STATUSES = ("blocked", "low", "medium", "high")
ROW_PRIORITY_SORT = {"high": 0, "medium": 1, "low": 2}
ROW_REASON_CODE_SEQUENCE = (
    CONTRADICTION_COUNT_REASON,
    SOURCE_SPREAD_REASON,
    EVIDENCE_RECENT_REASON,
    MARKET_MOVED_REASON,
    NO_CONTRADICTIONS_REASON,
    HIGH_PRIORITY_REASON,
    MEDIUM_PRIORITY_REASON,
    LOW_PRIORITY_REASON,
)
REPORT_REASON_CODE_SEQUENCE = (
    CONTRADICTION_COUNT_REASON,
    SOURCE_SPREAD_REASON,
    EVIDENCE_RECENT_REASON,
    MARKET_MOVED_REASON,
    NO_CONTRADICTIONS_REASON,
    HIGH_PRIORITY_REASON,
    MEDIUM_PRIORITY_REASON,
    LOW_PRIORITY_REASON,
    NO_INPUTS_REASON,
    EMPTY_REASON,
)

DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
QUANTUM = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
DEFAULT_RECENCY_WINDOW_HOURS = Decimal("72.000000")
DEFAULT_MOVEMENT_THRESHOLD = Decimal("0.050000")
DEFAULT_RELIABILITY_SPREAD_THRESHOLD = Decimal("0.250000")
DEFAULT_HIGH_PRIORITY_SCORE_THRESHOLD = Decimal("7.000000")
DEFAULT_MEDIUM_PRIORITY_SCORE_THRESHOLD = Decimal("3.000000")
VERY_RECENT_WINDOW_HOURS = Decimal("24.000000")
REDACTED_SOURCE_REFERENCE = "<redacted-source-reference>"

__all__ = (
    "DEFAULT_MARKET_RESEARCH_CONTRADICTION_PRIORITY_CONFIG_VERSION",
    "MarketResearchContradictionObservation",
    "MarketResearchContradictionPriorityConfig",
    "MarketResearchContradictionPriorityDigest",
    "MarketResearchContradictionPriorityDigestReasonCodeCount",
    "MarketResearchContradictionPriorityRow",
    "build_market_research_contradiction_priority_digest",
    "market_research_contradiction_priority_digest_payload",
)


class _FinalPublicDataclass:
    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        for base in cls.__bases__:
            if base is not _FinalPublicDataclass and issubclass(
                base,
                _FinalPublicDataclass,
            ):
                raise TypeError(f"{base.__name__} does not support subclassing")


@dataclass(frozen=True)
class MarketResearchContradictionPriorityConfig(_FinalPublicDataclass):
    config_version: str = DEFAULT_MARKET_RESEARCH_CONTRADICTION_PRIORITY_CONFIG_VERSION
    recency_watch_window_hours: Decimal = DEFAULT_RECENCY_WINDOW_HOURS
    movement_watch_threshold: Decimal = DEFAULT_MOVEMENT_THRESHOLD
    reliability_spread_watch_threshold: Decimal = DEFAULT_RELIABILITY_SPREAD_THRESHOLD
    high_priority_score_threshold: Decimal = DEFAULT_HIGH_PRIORITY_SCORE_THRESHOLD
    medium_priority_score_threshold: Decimal = DEFAULT_MEDIUM_PRIORITY_SCORE_THRESHOLD
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            MarketResearchContradictionPriorityConfig,
            "config",
        )
        _require_canonical_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_MARKET_RESEARCH_CONTRADICTION_PRIORITY_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        object.__setattr__(
            self,
            "recency_watch_window_hours",
            _require_nonnegative_count_decimal(
                "recency_watch_window_hours",
                self.recency_watch_window_hours,
            ),
        )
        object.__setattr__(
            self,
            "movement_watch_threshold",
            _require_probability_decimal(
                "movement_watch_threshold",
                self.movement_watch_threshold,
            ),
        )
        object.__setattr__(
            self,
            "reliability_spread_watch_threshold",
            _require_probability_decimal(
                "reliability_spread_watch_threshold",
                self.reliability_spread_watch_threshold,
            ),
        )
        object.__setattr__(
            self,
            "high_priority_score_threshold",
            _require_nonnegative_decimal(
                "high_priority_score_threshold",
                self.high_priority_score_threshold,
            ),
        )
        object.__setattr__(
            self,
            "medium_priority_score_threshold",
            _require_nonnegative_decimal(
                "medium_priority_score_threshold",
                self.medium_priority_score_threshold,
            ),
        )
        if self.high_priority_score_threshold < self.medium_priority_score_threshold:
            raise ValueError(
                "high_priority_score_threshold must be >= "
                "medium_priority_score_threshold",
            )
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class MarketResearchContradictionObservation(_FinalPublicDataclass):
    condition_id: str
    contradiction_count: Decimal
    min_source_reliability: Decimal
    max_source_reliability: Decimal
    evidence_observed_at: datetime
    market_probability_at_contradiction: Decimal
    current_market_probability: Decimal
    source_reference: str = REDACTED_SOURCE_REFERENCE
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            MarketResearchContradictionObservation,
            "observation",
        )
        _require_canonical_string("condition_id", self.condition_id)
        object.__setattr__(
            self,
            "contradiction_count",
            _require_nonnegative_count_decimal(
                "contradiction_count",
                self.contradiction_count,
            ),
        )
        object.__setattr__(
            self,
            "min_source_reliability",
            _require_probability_decimal(
                "min_source_reliability",
                self.min_source_reliability,
            ),
        )
        object.__setattr__(
            self,
            "max_source_reliability",
            _require_probability_decimal(
                "max_source_reliability",
                self.max_source_reliability,
            ),
        )
        if self.max_source_reliability < self.min_source_reliability:
            raise ValueError("max_source_reliability must be >= min_source_reliability")
        object.__setattr__(
            self,
            "evidence_observed_at",
            _as_utc("evidence_observed_at", self.evidence_observed_at),
        )
        object.__setattr__(
            self,
            "market_probability_at_contradiction",
            _require_probability_decimal(
                "market_probability_at_contradiction",
                self.market_probability_at_contradiction,
            ),
        )
        object.__setattr__(
            self,
            "current_market_probability",
            _require_probability_decimal(
                "current_market_probability",
                self.current_market_probability,
            ),
        )
        _require_canonical_string("source_reference", self.source_reference)
        object.__setattr__(self, "source_reference", REDACTED_SOURCE_REFERENCE)
        _require_hard_flags("observation", self)


@dataclass(frozen=True)
class MarketResearchContradictionPriorityRow(_FinalPublicDataclass):
    condition_id: str
    contradiction_count: Decimal
    min_source_reliability: Decimal
    max_source_reliability: Decimal
    source_reliability_spread: Decimal
    evidence_observed_at: datetime
    evidence_age_hours: Decimal
    market_probability_at_contradiction: Decimal
    current_market_probability: Decimal
    market_movement_since_contradiction: Decimal
    source_reference: str
    priority_score: Decimal
    priority_status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, MarketResearchContradictionPriorityRow, "row")
        _require_canonical_string("condition_id", self.condition_id)
        object.__setattr__(
            self,
            "contradiction_count",
            _require_nonnegative_count_decimal(
                "contradiction_count",
                self.contradiction_count,
            ),
        )
        for field_name in (
            "min_source_reliability",
            "max_source_reliability",
            "source_reliability_spread",
            "market_probability_at_contradiction",
            "current_market_probability",
            "market_movement_since_contradiction",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_probability_decimal(field_name, getattr(self, field_name)),
            )
        if self.max_source_reliability < self.min_source_reliability:
            raise ValueError("max_source_reliability must be >= min_source_reliability")
        if self.source_reliability_spread != _decimal_difference(
            self.max_source_reliability,
            self.min_source_reliability,
        ):
            raise ValueError("source_reliability_spread must match reliability range")
        object.__setattr__(
            self,
            "evidence_observed_at",
            _as_utc("evidence_observed_at", self.evidence_observed_at),
        )
        object.__setattr__(
            self,
            "evidence_age_hours",
            _require_nonnegative_count_decimal(
                "evidence_age_hours",
                self.evidence_age_hours,
            ),
        )
        if self.market_movement_since_contradiction != _absolute_decimal_difference(
            self.current_market_probability,
            self.market_probability_at_contradiction,
        ):
            raise ValueError(
                "market_movement_since_contradiction must match market probabilities",
            )
        _require_canonical_string("source_reference", self.source_reference)
        object.__setattr__(self, "source_reference", REDACTED_SOURCE_REFERENCE)
        object.__setattr__(
            self,
            "priority_score",
            _require_nonnegative_decimal("priority_score", self.priority_score),
        )
        _require_row_priority_status("priority_status", self.priority_status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(
                self.reason_codes,
                ROW_REASON_CODE_SEQUENCE,
                context="row",
            ),
        )
        _validate_row(self)
        _require_hard_flags("row", self)


@dataclass(frozen=True)
class MarketResearchContradictionPriorityDigestReasonCodeCount(_FinalPublicDataclass):
    reason_code: str
    count: Decimal
    market_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            MarketResearchContradictionPriorityDigestReasonCodeCount,
            "reason_code_count",
        )
        _require_report_reason_code("reason_code", self.reason_code)
        object.__setattr__(
            self,
            "count",
            _require_positive_count_decimal("count", self.count),
        )
        object.__setattr__(
            self,
            "market_ratio",
            _require_probability_decimal("market_ratio", self.market_ratio),
        )
        _require_hard_flags("reason_code_count", self)


@dataclass(frozen=True)
class MarketResearchContradictionPriorityDigest(_FinalPublicDataclass):
    generated_at: datetime
    config_version: str
    priority_status: str
    total_market_count: Decimal
    high_priority_count: Decimal
    medium_priority_count: Decimal
    low_priority_count: Decimal
    max_priority_score: Decimal
    average_priority_score: Decimal
    reason_codes: tuple[str, ...]
    reason_code_counts: tuple[
        MarketResearchContradictionPriorityDigestReasonCodeCount,
        ...,
    ]
    rows: tuple[MarketResearchContradictionPriorityRow, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, MarketResearchContradictionPriorityDigest, "digest")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_MARKET_RESEARCH_CONTRADICTION_PRIORITY_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        _require_report_priority_status("priority_status", self.priority_status)
        for field_name in (
            "total_market_count",
            "high_priority_count",
            "medium_priority_count",
            "low_priority_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_count_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "max_priority_score",
            _require_nonnegative_decimal("max_priority_score", self.max_priority_score),
        )
        object.__setattr__(
            self,
            "average_priority_score",
            _require_nonnegative_decimal(
                "average_priority_score",
                self.average_priority_score,
            ),
        )
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
                self.reason_codes,
                REPORT_REASON_CODE_SEQUENCE,
                context="digest",
            ),
        )
        _validate_digest_consistency(self)
        _require_hard_flags("digest", self)


_PUBLIC_DATACLASS_TYPES = (
    MarketResearchContradictionObservation,
    MarketResearchContradictionPriorityConfig,
    MarketResearchContradictionPriorityDigest,
    MarketResearchContradictionPriorityDigestReasonCodeCount,
    MarketResearchContradictionPriorityRow,
)


def build_market_research_contradiction_priority_digest(
    observations: tuple[MarketResearchContradictionObservation, ...]
    | list[MarketResearchContradictionObservation],
    *,
    config: MarketResearchContradictionPriorityConfig,
    generated_at: datetime,
) -> MarketResearchContradictionPriorityDigest:
    if type(config) is not MarketResearchContradictionPriorityConfig:
        raise ValueError("config must be a MarketResearchContradictionPriorityConfig")
    _require_hard_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    normalized = _normalize_observations(observations)
    rows = _sorted_rows(
        tuple(
            _priority_row(
                observation,
                config=config,
                generated_at=generated_at_utc,
            )
            for observation in normalized
        ),
    )
    reason_codes = _digest_reason_codes(rows)
    total_market_count = _decimal_count(len(rows))

    return MarketResearchContradictionPriorityDigest(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        priority_status=_digest_priority_status(rows),
        total_market_count=total_market_count,
        high_priority_count=_status_count(rows, "high"),
        medium_priority_count=_status_count(rows, "medium"),
        low_priority_count=_status_count(rows, "low"),
        max_priority_score=_max_priority_score(rows),
        average_priority_score=_average_priority_score(rows),
        reason_codes=reason_codes,
        reason_code_counts=_reason_code_counts(
            rows,
            reason_codes,
            total_market_count,
        ),
        rows=rows,
    )


def market_research_contradiction_priority_digest_payload(
    digest: MarketResearchContradictionPriorityDigest,
) -> dict[str, Any]:
    if type(digest) is not MarketResearchContradictionPriorityDigest:
        raise ValueError("digest must be a MarketResearchContradictionPriorityDigest")
    _require_payload_safe_value("digest", digest)
    return _payload_value(digest)


def _priority_row(
    observation: MarketResearchContradictionObservation,
    *,
    config: MarketResearchContradictionPriorityConfig,
    generated_at: datetime,
) -> MarketResearchContradictionPriorityRow:
    if observation.evidence_observed_at > generated_at:
        raise ValueError("evidence_observed_at must not be after generated_at")
    reliability_spread = _decimal_difference(
        observation.max_source_reliability,
        observation.min_source_reliability,
    )
    market_movement = _absolute_decimal_difference(
        observation.current_market_probability,
        observation.market_probability_at_contradiction,
    )
    evidence_age_hours = _elapsed_whole_hours(
        start=observation.evidence_observed_at,
        end=generated_at,
    )
    priority_score = _priority_score(
        contradiction_count=observation.contradiction_count,
        reliability_spread=reliability_spread,
        evidence_age_hours=evidence_age_hours,
        market_movement=market_movement,
    )
    priority_status = _row_priority_status(priority_score, config=config)

    return MarketResearchContradictionPriorityRow(
        condition_id=observation.condition_id,
        contradiction_count=observation.contradiction_count,
        min_source_reliability=observation.min_source_reliability,
        max_source_reliability=observation.max_source_reliability,
        source_reliability_spread=reliability_spread,
        evidence_observed_at=observation.evidence_observed_at,
        evidence_age_hours=evidence_age_hours,
        market_probability_at_contradiction=observation.market_probability_at_contradiction,
        current_market_probability=observation.current_market_probability,
        market_movement_since_contradiction=market_movement,
        source_reference=observation.source_reference,
        priority_score=priority_score,
        priority_status=priority_status,
        reason_codes=_row_reason_codes(
            observation=observation,
            reliability_spread=reliability_spread,
            evidence_age_hours=evidence_age_hours,
            market_movement=market_movement,
            priority_status=priority_status,
            config=config,
        ),
    )


def _priority_score(
    *,
    contradiction_count: Decimal,
    reliability_spread: Decimal,
    evidence_age_hours: Decimal,
    market_movement: Decimal,
) -> Decimal:
    if contradiction_count == ZERO:
        return ZERO
    fresh_evidence_bonus = (
        Decimal("2.000000") if evidence_age_hours <= VERY_RECENT_WINDOW_HOURS else ZERO
    )
    with localcontext(DECIMAL_CONTEXT):
        score = (
            contradiction_count
            + (reliability_spread * Decimal("3.000000"))
            + (market_movement * Decimal("4.000000"))
            + fresh_evidence_bonus
        )
        return _q(score)


def _row_priority_status(
    priority_score: Decimal,
    *,
    config: MarketResearchContradictionPriorityConfig,
) -> str:
    if priority_score >= config.high_priority_score_threshold:
        return "high"
    if priority_score >= config.medium_priority_score_threshold:
        return "medium"
    return "low"


def _row_reason_codes(
    *,
    observation: MarketResearchContradictionObservation,
    reliability_spread: Decimal,
    evidence_age_hours: Decimal,
    market_movement: Decimal,
    priority_status: str,
    config: MarketResearchContradictionPriorityConfig,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    if observation.contradiction_count > ZERO:
        reason_codes.append(CONTRADICTION_COUNT_REASON)
        if reliability_spread >= config.reliability_spread_watch_threshold:
            reason_codes.append(SOURCE_SPREAD_REASON)
        if evidence_age_hours <= config.recency_watch_window_hours:
            reason_codes.append(EVIDENCE_RECENT_REASON)
        if market_movement >= config.movement_watch_threshold:
            reason_codes.append(MARKET_MOVED_REASON)
    else:
        reason_codes.append(NO_CONTRADICTIONS_REASON)
    if priority_status == "high":
        reason_codes.append(HIGH_PRIORITY_REASON)
    elif priority_status == "medium":
        reason_codes.append(MEDIUM_PRIORITY_REASON)
    else:
        reason_codes.append(LOW_PRIORITY_REASON)
    return tuple(
        reason_code
        for reason_code in ROW_REASON_CODE_SEQUENCE
        if reason_code in reason_codes
    )


def _digest_priority_status(
    rows: tuple[MarketResearchContradictionPriorityRow, ...],
) -> str:
    if not rows:
        return "blocked"
    if any(row.priority_status == "high" for row in rows):
        return "high"
    if any(row.priority_status == "medium" for row in rows):
        return "medium"
    return "low"


def _digest_reason_codes(
    rows: tuple[MarketResearchContradictionPriorityRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return (NO_INPUTS_REASON, EMPTY_REASON)
    present = {reason_code for row in rows for reason_code in row.reason_codes}
    return tuple(
        reason_code
        for reason_code in REPORT_REASON_CODE_SEQUENCE
        if reason_code in present
    )


def _reason_code_counts(
    rows: tuple[MarketResearchContradictionPriorityRow, ...],
    reason_codes: tuple[str, ...],
    total_market_count: Decimal,
) -> tuple[MarketResearchContradictionPriorityDigestReasonCodeCount, ...]:
    if not rows:
        return (
            MarketResearchContradictionPriorityDigestReasonCodeCount(
                reason_code=NO_INPUTS_REASON,
                count=ONE,
                market_ratio=ZERO,
            ),
            MarketResearchContradictionPriorityDigestReasonCodeCount(
                reason_code=EMPTY_REASON,
                count=ONE,
                market_ratio=ZERO,
            ),
        )
    return tuple(
        MarketResearchContradictionPriorityDigestReasonCodeCount(
            reason_code=reason_code,
            count=_reason_count(rows, reason_code),
            market_ratio=_ratio(_reason_count(rows, reason_code), total_market_count),
        )
        for reason_code in reason_codes
    )


def _status_count(
    rows: tuple[MarketResearchContradictionPriorityRow, ...],
    status: str,
) -> Decimal:
    return _decimal_count(sum(1 for row in rows if row.priority_status == status))


def _reason_count(
    rows: tuple[MarketResearchContradictionPriorityRow, ...],
    reason_code: str,
) -> Decimal:
    return _decimal_count(sum(1 for row in rows if reason_code in row.reason_codes))


def _max_priority_score(rows: tuple[MarketResearchContradictionPriorityRow, ...]) -> Decimal:
    return max((row.priority_score for row in rows), default=ZERO)


def _average_priority_score(
    rows: tuple[MarketResearchContradictionPriorityRow, ...],
) -> Decimal:
    if not rows:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return _q(
            sum((row.priority_score for row in rows), ZERO)
            / _decimal_count(len(rows)),
        )


def _normalize_observations(
    observations: tuple[MarketResearchContradictionObservation, ...]
    | list[MarketResearchContradictionObservation],
) -> tuple[MarketResearchContradictionObservation, ...]:
    if type(observations) not in (list, tuple):
        raise ValueError(
            "observations must be a list or tuple of MarketResearchContradictionObservation",
        )
    normalized = tuple(observations)
    seen_condition_ids: set[str] = set()
    for observation in normalized:
        if type(observation) is not MarketResearchContradictionObservation:
            raise ValueError(
                "observations must contain MarketResearchContradictionObservation values",
            )
        _require_hard_flags("observation", observation)
        if observation.condition_id in seen_condition_ids:
            raise ValueError("observations must contain unique condition_id values")
        seen_condition_ids.add(observation.condition_id)
    return normalized


def _normalize_rows(
    rows: tuple[MarketResearchContradictionPriorityRow, ...],
) -> tuple[MarketResearchContradictionPriorityRow, ...]:
    if type(rows) is not tuple:
        raise ValueError("rows must be a tuple")
    seen_condition_ids: set[str] = set()
    for row in rows:
        if type(row) is not MarketResearchContradictionPriorityRow:
            raise ValueError(
                "rows must contain MarketResearchContradictionPriorityRow values",
            )
        _require_hard_flags("row", row)
        if row.condition_id in seen_condition_ids:
            raise ValueError("rows must contain unique condition_id values")
        seen_condition_ids.add(row.condition_id)
    if rows != _sorted_rows(rows):
        raise ValueError("rows must use deterministic sequence")
    return rows


def _normalize_reason_code_counts(
    value: tuple[MarketResearchContradictionPriorityDigestReasonCodeCount, ...],
) -> tuple[MarketResearchContradictionPriorityDigestReasonCodeCount, ...]:
    if type(value) is not tuple:
        raise ValueError("reason_code_counts must be a tuple")
    seen_reason_codes: set[str] = set()
    for reason_count in value:
        if type(reason_count) is not MarketResearchContradictionPriorityDigestReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "MarketResearchContradictionPriorityDigestReasonCodeCount values",
            )
        _require_hard_flags("reason_code_count", reason_count)
        if reason_count.reason_code in seen_reason_codes:
            raise ValueError("reason_code_counts must contain unique reason_code values")
        seen_reason_codes.add(reason_count.reason_code)
    if value != _sorted_reason_code_counts(value):
        raise ValueError("reason_code_counts must use deterministic sequence")
    return value


def _normalize_reason_codes(
    value: tuple[str, ...],
    sequence: tuple[str, ...],
    *,
    context: str,
) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ValueError("reason_codes must be a tuple")
    if not value:
        raise ValueError("reason_codes must not be empty")
    seen_reason_codes: set[str] = set()
    for reason_code in value:
        _require_report_reason_code("reason_codes", reason_code)
        if reason_code in seen_reason_codes:
            raise ValueError("reason_codes must be unique")
        seen_reason_codes.add(reason_code)
    if context == "row" and (
        NO_INPUTS_REASON in seen_reason_codes or EMPTY_REASON in seen_reason_codes
    ):
        raise ValueError("reason_codes must not include empty input reasons for rows")
    if NO_INPUTS_REASON in seen_reason_codes and EMPTY_REASON not in seen_reason_codes:
        raise ValueError("reason_codes must include empty with no_inputs")
    if EMPTY_REASON in seen_reason_codes and NO_INPUTS_REASON not in seen_reason_codes:
        raise ValueError("reason_codes must include no_inputs with empty")
    deterministic = tuple(
        reason_code for reason_code in sequence if reason_code in seen_reason_codes
    )
    if value != deterministic:
        raise ValueError("reason_codes must use deterministic sequence")
    return value


def _row_sort_key(
    row: MarketResearchContradictionPriorityRow,
) -> tuple[int, Decimal, Decimal, str]:
    return (
        ROW_PRIORITY_SORT[row.priority_status],
        -row.priority_score,
        row.evidence_age_hours,
        row.condition_id,
    )


def _sorted_rows(
    rows: tuple[MarketResearchContradictionPriorityRow, ...],
) -> tuple[MarketResearchContradictionPriorityRow, ...]:
    return tuple(sorted(rows, key=_row_sort_key))


def _sorted_reason_code_counts(
    counts: tuple[MarketResearchContradictionPriorityDigestReasonCodeCount, ...],
) -> tuple[MarketResearchContradictionPriorityDigestReasonCodeCount, ...]:
    return tuple(sorted(counts, key=lambda item: _reason_rank(item.reason_code)))


def _reason_rank(reason_code: str) -> int:
    if reason_code not in REPORT_REASON_CODE_SEQUENCE:
        raise ValueError("reason_code must be supported")
    return REPORT_REASON_CODE_SEQUENCE.index(reason_code)


def _validate_row(row: MarketResearchContradictionPriorityRow) -> None:
    expected_priority_score = _priority_score(
        contradiction_count=row.contradiction_count,
        reliability_spread=row.source_reliability_spread,
        evidence_age_hours=row.evidence_age_hours,
        market_movement=row.market_movement_since_contradiction,
    )
    if row.priority_score != expected_priority_score:
        raise ValueError("priority_score must match row inputs")
    priority_reasons = {
        HIGH_PRIORITY_REASON,
        MEDIUM_PRIORITY_REASON,
        LOW_PRIORITY_REASON,
    }
    present_priority_reasons = tuple(
        reason_code for reason_code in row.reason_codes if reason_code in priority_reasons
    )
    if len(present_priority_reasons) != 1:
        raise ValueError("reason_codes must include exactly one priority reason")
    expected_priority_reason = {
        "high": HIGH_PRIORITY_REASON,
        "medium": MEDIUM_PRIORITY_REASON,
        "low": LOW_PRIORITY_REASON,
    }[row.priority_status]
    if present_priority_reasons != (expected_priority_reason,):
        raise ValueError("reason_codes must match priority_status")
    if row.contradiction_count == ZERO:
        if CONTRADICTION_COUNT_REASON in row.reason_codes:
            raise ValueError("reason_codes must match contradiction_count")
        if NO_CONTRADICTIONS_REASON not in row.reason_codes:
            raise ValueError("reason_codes must match contradiction_count")
    else:
        if CONTRADICTION_COUNT_REASON not in row.reason_codes:
            raise ValueError("reason_codes must match contradiction_count")
        if NO_CONTRADICTIONS_REASON in row.reason_codes:
            raise ValueError("reason_codes must match contradiction_count")


def _validate_digest_consistency(
    digest: MarketResearchContradictionPriorityDigest,
) -> None:
    rows = digest.rows
    if digest.total_market_count != _decimal_count(len(rows)):
        raise ValueError("total_market_count must match rows")
    if digest.high_priority_count != _status_count(rows, "high"):
        raise ValueError("high_priority_count must match rows")
    if digest.medium_priority_count != _status_count(rows, "medium"):
        raise ValueError("medium_priority_count must match rows")
    if digest.low_priority_count != _status_count(rows, "low"):
        raise ValueError("low_priority_count must match rows")
    if digest.high_priority_count + digest.medium_priority_count + digest.low_priority_count != _decimal_count(
        len(rows),
    ):
        raise ValueError("priority counts must match rows")
    if digest.priority_status != _digest_priority_status(rows):
        raise ValueError("priority_status must match rows")
    if digest.max_priority_score != _max_priority_score(rows):
        raise ValueError("max_priority_score must match rows")
    if digest.average_priority_score != _average_priority_score(rows):
        raise ValueError("average_priority_score must match rows")
    expected_reason_codes = _digest_reason_codes(rows)
    expected_reason_counts = _reason_code_counts(
        rows,
        expected_reason_codes,
        digest.total_market_count,
    )
    if digest.reason_code_counts != expected_reason_counts:
        raise ValueError("reason_code_counts must match rows")
    if digest.reason_codes != tuple(
        reason_count.reason_code for reason_count in digest.reason_code_counts
    ):
        raise ValueError("reason_codes must match reason_code_counts")
    if digest.reason_codes != expected_reason_codes:
        raise ValueError("reason_codes must match rows")


def _elapsed_whole_hours(*, start: datetime, end: datetime) -> Decimal:
    if end < start:
        raise ValueError("evidence_observed_at must not be after generated_at")
    delta = end - start
    whole_seconds = (delta.days * 86400) + delta.seconds
    return _decimal_count(whole_seconds // 3600)


def _decimal_difference(maximum: Decimal, minimum: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return _q(maximum - minimum)


def _absolute_decimal_difference(left: Decimal, right: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        difference = left - right
        if difference < ZERO:
            difference = -difference
        return _q(difference)


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return _require_probability_decimal("market_ratio", numerator / denominator)


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_exact_type(value: object, expected_type: type[object], label: str) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{label} must be exactly {expected_type.__name__}")


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
    return _q(value)


def _require_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return decimal_value


def _require_nonnegative_count_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_nonnegative_decimal(field_name, value)
    if value != value.to_integral_value():
        raise ValueError(f"{field_name} must be a whole-count Decimal")
    return decimal_value


def _require_positive_count_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_nonnegative_count_decimal(field_name, value)
    if decimal_value == ZERO:
        raise ValueError(f"{field_name} must be positive")
    return decimal_value


def _require_probability_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_nonnegative_decimal(field_name, value)
    if decimal_value > ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return decimal_value


def _decimal_count(value: int) -> Decimal:
    if type(value) is not int or value < 0:
        raise ValueError("count must be a nonnegative int")
    return _q(Decimal(value))


def _q(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(QUANTUM)


def _require_row_priority_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in ROW_PRIORITY_STATUSES:
        raise ValueError(f"{field_name} must be low, medium, or high")


def _require_report_priority_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in REPORT_PRIORITY_STATUSES:
        raise ValueError(f"{field_name} must be blocked, low, medium, or high")


def _require_report_reason_code(field_name: str, value: object) -> None:
    if type(value) is not str or value not in REPORT_REASON_CODE_SEQUENCE:
        raise ValueError(f"{field_name} must be a supported reason code")


def _require_hard_flags(context: str, value: object) -> None:
    for flag_name in ("paper_only", "report_only", "readonly"):
        if getattr(value, flag_name, None) is not True:
            raise ValueError(f"{context} {flag_name} must be True")


def _require_payload_safe_value(field_name: str, value: object) -> None:
    if type(value) is Decimal:
        if not value.is_finite():
            raise ValueError(f"{field_name} must be finite")
        if value != _q(value):
            raise ValueError(f"{field_name} must be quantized to six decimals")
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


def _payload_value(value: Any) -> Any:
    if type(value) is Decimal:
        return format(_q(value), "f")
    if type(value) is datetime:
        return _as_utc("datetime", value).isoformat()
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
        return {name: _payload_value(item) for name, item in value.items()}
    if type(value) is float:
        raise ValueError("payload value must not be a float")
    if type(value) in (str, bool) or value is None:
        return value
    raise ValueError("digest values must be payload serializable")
