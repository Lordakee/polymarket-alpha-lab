"""Pure in-memory ranker for research packet source rechecks."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import asdict, dataclass, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, localcontext
from hashlib import sha256
from typing import Any


DEFAULT_RESEARCH_PACKET_SOURCE_RECHECK_PRIORITY_RANKER_V2_CONFIG_VERSION = (
    "research-packet-source-recheck-priority-ranker-v2"
)

_DECIMAL_CONTEXT = Context(prec=64)
_QUANTUM = Decimal("0.000001")
_ZERO = Decimal("0.000000")
_ONE = Decimal("1.000000")
_ONE_HUNDRED = Decimal("100.000000")
_SECONDS_PER_DAY = Decimal("86400")
_MICROSECONDS_PER_SECOND = Decimal("1000000")
_DIGEST_FIELD = "derived_validation_digest"

_STATUS_VALUES = ("blocked", "watch", "clear")
_REPORT_STATUS_VALUES = ("empty", "blocked", "watch", "clear")
_STATUS_SORT = {"blocked": 0, "watch": 1, "clear": 2}

_REASON_EMPTY = "empty_source_recheck_priority_inputs"
_REASON_SOURCE_AGE_MISSING = "source_age_missing"
_REASON_SOURCE_AGE_BLOCKED = "source_age_blocked"
_REASON_SOURCE_AGE_WATCH = "source_age_watch"
_REASON_OFFICIAL_SOURCE_ABSENT = "official_source_absent"
_REASON_CONTRADICTION_BLOCKED = "contradiction_severity_blocked"
_REASON_CONTRADICTION_WATCH = "contradiction_severity_watch"
_REASON_PROBABILITY_MOVE_BLOCKED = "market_probability_move_blocked"
_REASON_PROBABILITY_MOVE_WATCH = "market_probability_move_watch"
_REASON_CLOSE_URGENCY_BLOCKED = "close_urgency_blocked"
_REASON_CLOSE_URGENCY_WATCH = "close_urgency_watch"
_REASON_RELIABILITY_BLOCKED = "prior_source_reliability_blocked"
_REASON_RELIABILITY_WATCH = "prior_source_reliability_watch"
_REASON_CLAMPED = "priority_score_clamped"
_REASON_CLEAR = "source_recheck_priority_clear"

ROW_REASON_CODES = (
    _REASON_SOURCE_AGE_MISSING,
    _REASON_SOURCE_AGE_BLOCKED,
    _REASON_SOURCE_AGE_WATCH,
    _REASON_OFFICIAL_SOURCE_ABSENT,
    _REASON_CONTRADICTION_BLOCKED,
    _REASON_CONTRADICTION_WATCH,
    _REASON_PROBABILITY_MOVE_BLOCKED,
    _REASON_PROBABILITY_MOVE_WATCH,
    _REASON_CLOSE_URGENCY_BLOCKED,
    _REASON_CLOSE_URGENCY_WATCH,
    _REASON_RELIABILITY_BLOCKED,
    _REASON_RELIABILITY_WATCH,
    _REASON_CLAMPED,
    _REASON_CLEAR,
)
REPORT_REASON_CODES = (_REASON_EMPTY,) + ROW_REASON_CODES

_BLOCKED_REASON_CODES = frozenset(
    (
        _REASON_SOURCE_AGE_MISSING,
        _REASON_SOURCE_AGE_BLOCKED,
        _REASON_CONTRADICTION_BLOCKED,
        _REASON_PROBABILITY_MOVE_BLOCKED,
        _REASON_CLOSE_URGENCY_BLOCKED,
        _REASON_RELIABILITY_BLOCKED,
    ),
)

_REASON_SCORE = {
    _REASON_SOURCE_AGE_MISSING: Decimal("25.000000"),
    _REASON_SOURCE_AGE_BLOCKED: Decimal("25.000000"),
    _REASON_SOURCE_AGE_WATCH: Decimal("10.000000"),
    _REASON_OFFICIAL_SOURCE_ABSENT: Decimal("15.000000"),
    _REASON_CONTRADICTION_BLOCKED: Decimal("35.000000"),
    _REASON_CONTRADICTION_WATCH: Decimal("15.000000"),
    _REASON_PROBABILITY_MOVE_BLOCKED: Decimal("20.000000"),
    _REASON_PROBABILITY_MOVE_WATCH: Decimal("10.000000"),
    _REASON_CLOSE_URGENCY_BLOCKED: Decimal("10.000000"),
    _REASON_CLOSE_URGENCY_WATCH: Decimal("5.000000"),
    _REASON_RELIABILITY_BLOCKED: Decimal("20.000000"),
    _REASON_RELIABILITY_WATCH: Decimal("10.000000"),
}

_UNSAFE_PUBLIC_SURFACE_FRAGMENTS = (
    "".join(("li", "ve")),
    "".join(("au", "th")),
    "".join(("wall", "et")),
    "".join(("acc", "ount")),
    "".join(("bro", "ker")),
    "".join(("or", "der")),
    "".join(("sub", "mit")),
    "".join(("can", "cel")),
    "".join(("sign", "ing")),
    "".join(("net", "work")),
    "".join(("data", "base")),
    "".join(("per", "sist")),
)


__all__ = (
    "DEFAULT_RESEARCH_PACKET_SOURCE_RECHECK_PRIORITY_RANKER_V2_CONFIG_VERSION",
    "ResearchPacketSourceRecheckPriorityRankerV2Config",
    "ResearchPacketSourceRecheckPriorityCandidateV2",
    "ResearchPacketSourceRecheckPriorityRowV2",
    "ResearchPacketSourceRecheckPriorityReportV2",
    "build_research_packet_source_recheck_priority_ranker_v2",
    "research_packet_source_recheck_priority_ranker_v2_payload",
    "validate_research_packet_source_recheck_priority_ranker_v2_payload",
)


@dataclass(frozen=True)
class ResearchPacketSourceRecheckPriorityRankerV2Config:
    config_version: str = (
        DEFAULT_RESEARCH_PACKET_SOURCE_RECHECK_PRIORITY_RANKER_V2_CONFIG_VERSION
    )
    source_age_watch_seconds: Decimal = Decimal("3600.000000")
    source_age_blocked_seconds: Decimal = Decimal("7200.000000")
    contradiction_severity_watch: Decimal = Decimal("0.250000")
    contradiction_severity_blocked: Decimal = Decimal("0.500000")
    market_probability_move_watch: Decimal = Decimal("0.050000")
    market_probability_move_blocked: Decimal = Decimal("0.150000")
    close_urgency_blocked_seconds: Decimal = Decimal("3600.000000")
    close_urgency_watch_seconds: Decimal = Decimal("21600.000000")
    prior_source_reliability_blocked_ceiling: Decimal = Decimal("0.300000")
    prior_source_reliability_watch_ceiling: Decimal = Decimal("0.600000")
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchPacketSourceRecheckPriorityRankerV2Config does not support subclassing",
        )

    def __post_init__(self) -> None:
        _require_exact_type(
            "config",
            self,
            ResearchPacketSourceRecheckPriorityRankerV2Config,
        )
        _require_canonical_string("config_version", self.config_version)
        for field_name in (
            "source_age_watch_seconds",
            "source_age_blocked_seconds",
            "close_urgency_blocked_seconds",
            "close_urgency_watch_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "contradiction_severity_watch",
            "contradiction_severity_blocked",
            "market_probability_move_watch",
            "market_probability_move_blocked",
            "prior_source_reliability_blocked_ceiling",
            "prior_source_reliability_watch_ceiling",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        if self.source_age_blocked_seconds < self.source_age_watch_seconds:
            raise ValueError(
                "source_age_blocked_seconds must cover source_age_watch_seconds",
            )
        if self.contradiction_severity_blocked < self.contradiction_severity_watch:
            raise ValueError(
                "contradiction_severity_blocked must cover contradiction_severity_watch",
            )
        if self.market_probability_move_blocked < self.market_probability_move_watch:
            raise ValueError(
                "market_probability_move_blocked must cover market_probability_move_watch",
            )
        if self.close_urgency_blocked_seconds > self.close_urgency_watch_seconds:
            raise ValueError(
                "close_urgency_blocked_seconds must not exceed close_urgency_watch_seconds",
            )
        if (
            self.prior_source_reliability_blocked_ceiling
            > self.prior_source_reliability_watch_ceiling
        ):
            raise ValueError(
                "prior_source_reliability_blocked_ceiling must not exceed "
                "prior_source_reliability_watch_ceiling",
            )
        _require_hard_flags(self)
        _reject_unsafe_public_surface("config", self)
        _require_or_set_digest(self)


@dataclass(frozen=True)
class ResearchPacketSourceRecheckPriorityCandidateV2:
    packet_id: str
    team_id: str
    market_id: str
    source_id: str
    source_family: str
    source_observed_at: datetime | None
    official_source_present: bool
    contradiction_severity: Decimal
    market_probability_move_magnitude: Decimal
    market_close_at: datetime
    prior_source_reliability: Decimal
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchPacketSourceRecheckPriorityCandidateV2 does not support subclassing",
        )

    def __post_init__(self) -> None:
        _require_exact_type(
            "candidate",
            self,
            ResearchPacketSourceRecheckPriorityCandidateV2,
        )
        for field_name in (
            "packet_id",
            "team_id",
            "market_id",
            "source_id",
            "source_family",
        ):
            _require_canonical_string(field_name, getattr(self, field_name))
        object.__setattr__(
            self,
            "source_observed_at",
            _optional_as_utc("source_observed_at", self.source_observed_at),
        )
        object.__setattr__(
            self,
            "market_close_at",
            _as_utc("market_close_at", self.market_close_at),
        )
        if type(self.official_source_present) is not bool:
            raise ValueError("official_source_present must be a bool")
        for field_name in (
            "contradiction_severity",
            "market_probability_move_magnitude",
            "prior_source_reliability",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        _require_hard_flags(self)
        _reject_unsafe_public_surface("candidate", self)
        _require_or_set_digest(self)


@dataclass(frozen=True)
class ResearchPacketSourceRecheckPriorityRowV2:
    priority_rank: Decimal
    packet_id: str
    team_id: str
    market_id: str
    source_id: str
    source_family: str
    priority_status: str
    priority_score: Decimal
    source_observed_at: datetime | None
    source_age_seconds: Decimal | None
    source_age_priority_seconds: Decimal
    official_source_present: bool
    contradiction_severity: Decimal
    market_probability_move_magnitude: Decimal
    market_close_at: datetime
    seconds_until_close: Decimal
    prior_source_reliability: Decimal
    reason_codes: tuple[str, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchPacketSourceRecheckPriorityRowV2 does not support subclassing",
        )

    def __post_init__(self) -> None:
        _require_exact_type("row", self, ResearchPacketSourceRecheckPriorityRowV2)
        object.__setattr__(
            self,
            "priority_rank",
            _normalize_positive_count("priority_rank", self.priority_rank),
        )
        for field_name in (
            "packet_id",
            "team_id",
            "market_id",
            "source_id",
            "source_family",
        ):
            _require_canonical_string(field_name, getattr(self, field_name))
        if self.priority_status not in _STATUS_VALUES:
            raise ValueError("priority_status must be supported")
        object.__setattr__(
            self,
            "priority_score",
            _normalize_priority_score("priority_score", self.priority_score),
        )
        object.__setattr__(
            self,
            "source_observed_at",
            _optional_as_utc("source_observed_at", self.source_observed_at),
        )
        object.__setattr__(
            self,
            "source_age_seconds",
            _normalize_optional_nonnegative_decimal(
                "source_age_seconds",
                self.source_age_seconds,
            ),
        )
        object.__setattr__(
            self,
            "source_age_priority_seconds",
            _normalize_nonnegative_decimal(
                "source_age_priority_seconds",
                self.source_age_priority_seconds,
            ),
        )
        if type(self.official_source_present) is not bool:
            raise ValueError("official_source_present must be a bool")
        for field_name in (
            "contradiction_severity",
            "market_probability_move_magnitude",
            "prior_source_reliability",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "market_close_at",
            _as_utc("market_close_at", self.market_close_at),
        )
        object.__setattr__(
            self,
            "seconds_until_close",
            _normalize_nonnegative_decimal("seconds_until_close", self.seconds_until_close),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes, ROW_REASON_CODES),
        )
        _validate_row_consistency(self)
        _require_hard_flags(self)
        _reject_unsafe_public_surface("row", self)
        _require_or_set_digest(self)


@dataclass(frozen=True)
class ResearchPacketSourceRecheckPriorityReportV2:
    generated_at: datetime
    config_version: str
    candidate_count: Decimal
    row_count: Decimal
    blocked_count: Decimal
    watch_count: Decimal
    clear_count: Decimal
    recheck_count: Decimal
    priority_ratio: Decimal
    official_source_absent_count: Decimal
    source_age_pressure_count: Decimal
    contradiction_pressure_count: Decimal
    market_probability_move_pressure_count: Decimal
    close_urgency_count: Decimal
    low_reliability_count: Decimal
    max_priority_score: Decimal
    max_source_age_seconds: Decimal | None
    max_contradiction_severity: Decimal
    max_market_probability_move_magnitude: Decimal
    nearest_close_time_seconds: Decimal
    min_prior_source_reliability: Decimal | None
    status: str
    reason_codes: tuple[str, ...]
    rows: tuple[ResearchPacketSourceRecheckPriorityRowV2, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchPacketSourceRecheckPriorityReportV2 does not support subclassing",
        )

    def __post_init__(self) -> None:
        _require_exact_type("report", self, ResearchPacketSourceRecheckPriorityReportV2)
        object.__setattr__(
            self,
            "generated_at",
            _as_utc("generated_at", self.generated_at),
        )
        _require_canonical_string("config_version", self.config_version)
        for field_name in (
            "candidate_count",
            "row_count",
            "blocked_count",
            "watch_count",
            "clear_count",
            "recheck_count",
            "official_source_absent_count",
            "source_age_pressure_count",
            "contradiction_pressure_count",
            "market_probability_move_pressure_count",
            "close_urgency_count",
            "low_reliability_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_count(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "priority_ratio",
            _normalize_ratio("priority_ratio", self.priority_ratio),
        )
        object.__setattr__(
            self,
            "max_priority_score",
            _normalize_priority_score("max_priority_score", self.max_priority_score),
        )
        object.__setattr__(
            self,
            "max_source_age_seconds",
            _normalize_optional_nonnegative_decimal(
                "max_source_age_seconds",
                self.max_source_age_seconds,
            ),
        )
        for field_name in (
            "max_contradiction_severity",
            "max_market_probability_move_magnitude",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "nearest_close_time_seconds",
            _normalize_nonnegative_decimal(
                "nearest_close_time_seconds",
                self.nearest_close_time_seconds,
            ),
        )
        object.__setattr__(
            self,
            "min_prior_source_reliability",
            _normalize_optional_ratio(
                "min_prior_source_reliability",
                self.min_prior_source_reliability,
            ),
        )
        if self.status not in _REPORT_STATUS_VALUES:
            raise ValueError("status must be supported")
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes, REPORT_REASON_CODES),
        )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        _validate_report_consistency(self)
        _require_hard_flags(self)
        _reject_unsafe_public_surface("report", self)
        _require_or_set_digest(self)


def build_research_packet_source_recheck_priority_ranker_v2(
    candidates: Iterable[ResearchPacketSourceRecheckPriorityCandidateV2],
    *,
    config: ResearchPacketSourceRecheckPriorityRankerV2Config,
    generated_at: datetime,
) -> ResearchPacketSourceRecheckPriorityReportV2:
    if type(config) is not ResearchPacketSourceRecheckPriorityRankerV2Config:
        raise ValueError(
            "config must be a ResearchPacketSourceRecheckPriorityRankerV2Config",
        )
    _require_hard_flags(config)
    _reject_unsafe_public_surface("config", config)
    _require_or_set_digest(config)
    generated_at = _as_utc("generated_at", generated_at)
    values = _normalize_candidates(candidates)
    _validate_candidate_times(values, generated_at)
    unranked_rows = tuple(
        _row_from_candidate(value, config=config, generated_at=generated_at)
        for value in values
    )
    ranked_rows = tuple(sorted(unranked_rows, key=_row_sort_key))
    rows = tuple(
        _row_with_rank(row, _decimal_count(index))
        for index, row in enumerate(ranked_rows, start=1)
    )
    return ResearchPacketSourceRecheckPriorityReportV2(
        generated_at=generated_at,
        config_version=config.config_version,
        candidate_count=_decimal_count(len(values)),
        row_count=_decimal_count(len(rows)),
        blocked_count=_status_count(rows, "blocked"),
        watch_count=_status_count(rows, "watch"),
        clear_count=_status_count(rows, "clear"),
        recheck_count=_status_count(rows, "blocked") + _status_count(rows, "watch"),
        priority_ratio=_ratio(
            _status_count(rows, "blocked") + _status_count(rows, "watch"),
            _decimal_count(len(rows)),
        ),
        official_source_absent_count=_reason_count(rows, _REASON_OFFICIAL_SOURCE_ABSENT),
        source_age_pressure_count=_count_reasons(
            rows,
            (
                _REASON_SOURCE_AGE_MISSING,
                _REASON_SOURCE_AGE_BLOCKED,
                _REASON_SOURCE_AGE_WATCH,
            ),
        ),
        contradiction_pressure_count=_count_reasons(
            rows,
            (_REASON_CONTRADICTION_BLOCKED, _REASON_CONTRADICTION_WATCH),
        ),
        market_probability_move_pressure_count=_count_reasons(
            rows,
            (_REASON_PROBABILITY_MOVE_BLOCKED, _REASON_PROBABILITY_MOVE_WATCH),
        ),
        close_urgency_count=_count_reasons(
            rows,
            (_REASON_CLOSE_URGENCY_BLOCKED, _REASON_CLOSE_URGENCY_WATCH),
        ),
        low_reliability_count=_count_reasons(
            rows,
            (_REASON_RELIABILITY_BLOCKED, _REASON_RELIABILITY_WATCH),
        ),
        max_priority_score=_max_decimal(
            (row.priority_score for row in rows),
            default=_ZERO,
        ),
        max_source_age_seconds=_max_optional_decimal(
            row.source_age_seconds for row in rows
        ),
        max_contradiction_severity=_max_decimal(
            (row.contradiction_severity for row in rows),
            default=_ZERO,
        ),
        max_market_probability_move_magnitude=_max_decimal(
            (row.market_probability_move_magnitude for row in rows),
            default=_ZERO,
        ),
        nearest_close_time_seconds=_min_decimal(
            (row.seconds_until_close for row in rows),
            default=_ZERO,
        ),
        min_prior_source_reliability=_min_optional_decimal(
            row.prior_source_reliability for row in rows
        ),
        status=_report_status(rows),
        reason_codes=_report_reason_codes(rows),
        rows=rows,
    )


def research_packet_source_recheck_priority_ranker_v2_payload(
    report: ResearchPacketSourceRecheckPriorityReportV2,
) -> dict[str, Any]:
    if type(report) is not ResearchPacketSourceRecheckPriorityReportV2:
        raise ValueError("report must be a ResearchPacketSourceRecheckPriorityReportV2")
    _require_hard_flags(report)
    _reject_unsafe_public_surface("report", report)
    _require_or_set_digest(report)
    for row in report.rows:
        _require_hard_flags(row)
        _reject_unsafe_public_surface("row", row)
        _require_or_set_digest(row)
    payload = _payload_value(report)
    if not isinstance(payload, dict):
        raise ValueError("public payload must be a JSON object")
    validate_research_packet_source_recheck_priority_ranker_v2_payload(payload)
    return payload


def validate_research_packet_source_recheck_priority_ranker_v2_payload(
    payload: object,
) -> bool:
    if not isinstance(payload, dict):
        raise ValueError("public payload must be a JSON object")
    _reject_unsafe_public_surface("public payload", payload)
    _require_public_payload_values(payload)
    _validate_payload_digest_tree(payload)
    return True


def _row_from_candidate(
    value: ResearchPacketSourceRecheckPriorityCandidateV2,
    *,
    config: ResearchPacketSourceRecheckPriorityRankerV2Config,
    generated_at: datetime,
) -> ResearchPacketSourceRecheckPriorityRowV2:
    source_age_seconds = (
        None
        if value.source_observed_at is None
        else _seconds_between(value.source_observed_at, generated_at)
    )
    source_age_priority_seconds = (
        config.source_age_blocked_seconds
        if source_age_seconds is None
        else source_age_seconds
    )
    seconds_until_close = _nonnegative_seconds_between(generated_at, value.market_close_at)
    reason_codes = _reason_codes_for_candidate(
        value,
        source_age_seconds=source_age_seconds,
        seconds_until_close=seconds_until_close,
        config=config,
    )
    priority_score = _priority_score(reason_codes)
    return ResearchPacketSourceRecheckPriorityRowV2(
        priority_rank=_ONE_HUNDRED,
        packet_id=value.packet_id,
        team_id=value.team_id,
        market_id=value.market_id,
        source_id=value.source_id,
        source_family=value.source_family,
        priority_status=_row_status(reason_codes),
        priority_score=priority_score,
        source_observed_at=value.source_observed_at,
        source_age_seconds=source_age_seconds,
        source_age_priority_seconds=source_age_priority_seconds,
        official_source_present=value.official_source_present,
        contradiction_severity=value.contradiction_severity,
        market_probability_move_magnitude=value.market_probability_move_magnitude,
        market_close_at=value.market_close_at,
        seconds_until_close=seconds_until_close,
        prior_source_reliability=value.prior_source_reliability,
        reason_codes=reason_codes,
    )


def _row_with_rank(
    row: ResearchPacketSourceRecheckPriorityRowV2,
    priority_rank: Decimal,
) -> ResearchPacketSourceRecheckPriorityRowV2:
    return ResearchPacketSourceRecheckPriorityRowV2(
        priority_rank=priority_rank,
        packet_id=row.packet_id,
        team_id=row.team_id,
        market_id=row.market_id,
        source_id=row.source_id,
        source_family=row.source_family,
        priority_status=row.priority_status,
        priority_score=row.priority_score,
        source_observed_at=row.source_observed_at,
        source_age_seconds=row.source_age_seconds,
        source_age_priority_seconds=row.source_age_priority_seconds,
        official_source_present=row.official_source_present,
        contradiction_severity=row.contradiction_severity,
        market_probability_move_magnitude=row.market_probability_move_magnitude,
        market_close_at=row.market_close_at,
        seconds_until_close=row.seconds_until_close,
        prior_source_reliability=row.prior_source_reliability,
        reason_codes=row.reason_codes,
    )


def _reason_codes_for_candidate(
    value: ResearchPacketSourceRecheckPriorityCandidateV2,
    *,
    source_age_seconds: Decimal | None,
    seconds_until_close: Decimal,
    config: ResearchPacketSourceRecheckPriorityRankerV2Config,
) -> tuple[str, ...]:
    reasons: list[str] = []
    if source_age_seconds is None:
        reasons.append(_REASON_SOURCE_AGE_MISSING)
    elif source_age_seconds >= config.source_age_blocked_seconds:
        reasons.append(_REASON_SOURCE_AGE_BLOCKED)
    elif source_age_seconds >= config.source_age_watch_seconds:
        reasons.append(_REASON_SOURCE_AGE_WATCH)

    if not value.official_source_present:
        reasons.append(_REASON_OFFICIAL_SOURCE_ABSENT)

    if value.contradiction_severity >= config.contradiction_severity_blocked:
        reasons.append(_REASON_CONTRADICTION_BLOCKED)
    elif value.contradiction_severity >= config.contradiction_severity_watch:
        reasons.append(_REASON_CONTRADICTION_WATCH)

    if value.market_probability_move_magnitude >= config.market_probability_move_blocked:
        reasons.append(_REASON_PROBABILITY_MOVE_BLOCKED)
    elif value.market_probability_move_magnitude >= config.market_probability_move_watch:
        reasons.append(_REASON_PROBABILITY_MOVE_WATCH)

    if seconds_until_close <= config.close_urgency_blocked_seconds:
        reasons.append(_REASON_CLOSE_URGENCY_BLOCKED)
    elif seconds_until_close <= config.close_urgency_watch_seconds:
        reasons.append(_REASON_CLOSE_URGENCY_WATCH)

    if value.prior_source_reliability <= config.prior_source_reliability_blocked_ceiling:
        reasons.append(_REASON_RELIABILITY_BLOCKED)
    elif value.prior_source_reliability <= config.prior_source_reliability_watch_ceiling:
        reasons.append(_REASON_RELIABILITY_WATCH)

    if not reasons:
        return (_REASON_CLEAR,)
    if _unclamped_priority_score(tuple(reasons)) > _ONE_HUNDRED:
        reasons.append(_REASON_CLAMPED)
    return tuple(reasons)


def _normalize_candidates(
    values: Iterable[ResearchPacketSourceRecheckPriorityCandidateV2],
) -> tuple[ResearchPacketSourceRecheckPriorityCandidateV2, ...]:
    if isinstance(values, (str, bytes)):
        raise ValueError("candidates must be an iterable")
    try:
        normalized = tuple(values)
    except TypeError as exc:
        raise ValueError("candidates must be an iterable") from exc
    seen_keys: set[tuple[str, str, str]] = set()
    for value in normalized:
        if type(value) is not ResearchPacketSourceRecheckPriorityCandidateV2:
            raise ValueError(
                "candidates must contain ResearchPacketSourceRecheckPriorityCandidateV2 "
                "values",
            )
        _require_hard_flags(value)
        _reject_unsafe_public_surface("candidate", value)
        _require_or_set_digest(value)
        key = _candidate_identity(value)
        if key in seen_keys:
            raise ValueError("candidates must not contain duplicate source keys")
        seen_keys.add(key)
    return normalized


def _normalize_rows(
    values: Iterable[ResearchPacketSourceRecheckPriorityRowV2],
) -> tuple[ResearchPacketSourceRecheckPriorityRowV2, ...]:
    if isinstance(values, (str, bytes)):
        raise ValueError("rows must contain ResearchPacketSourceRecheckPriorityRowV2 values")
    try:
        rows = tuple(values)
    except TypeError as exc:
        raise ValueError(
            "rows must contain ResearchPacketSourceRecheckPriorityRowV2 values",
        ) from exc
    for row in rows:
        if type(row) is not ResearchPacketSourceRecheckPriorityRowV2:
            raise ValueError(
                "rows must contain ResearchPacketSourceRecheckPriorityRowV2 values",
            )
        _require_hard_flags(row)
        _reject_unsafe_public_surface("row", row)
        _require_or_set_digest(row)
    if len(set(_row_identity(row) for row in rows)) != len(rows):
        raise ValueError("rows must be unique")
    if rows != tuple(sorted(rows, key=_row_sort_key)):
        raise ValueError("rows must use deterministic sort")
    expected_ranks = tuple(_decimal_count(index) for index in range(1, len(rows) + 1))
    if tuple(row.priority_rank for row in rows) != expected_ranks:
        raise ValueError("priority_rank values must be contiguous")
    return rows


def _validate_candidate_times(
    values: tuple[ResearchPacketSourceRecheckPriorityCandidateV2, ...],
    generated_at: datetime,
) -> None:
    for value in values:
        if (
            value.source_observed_at is not None
            and _seconds_between(value.source_observed_at, generated_at) < _ZERO
        ):
            raise ValueError("source_observed_at must not be after generated_at")


def _validate_row_consistency(row: ResearchPacketSourceRecheckPriorityRowV2) -> None:
    if row.priority_score != _priority_score(row.reason_codes):
        raise ValueError("priority_score must match reason_codes")
    if row.priority_status != _row_status(row.reason_codes):
        raise ValueError("priority_status must match reason_codes")
    if row.source_age_seconds is None and _REASON_SOURCE_AGE_MISSING not in row.reason_codes:
        raise ValueError("source_age_seconds missing rows must include source_age_missing")
    if (
        row.source_age_seconds is not None
        and _REASON_SOURCE_AGE_MISSING in row.reason_codes
    ):
        raise ValueError("source_age_seconds present rows must not include source_age_missing")
    if not row.official_source_present and _REASON_OFFICIAL_SOURCE_ABSENT not in row.reason_codes:
        raise ValueError("official_source_present false rows must include absent reason")
    if row.official_source_present and _REASON_OFFICIAL_SOURCE_ABSENT in row.reason_codes:
        raise ValueError("official_source_present true rows must not include absent reason")


def _validate_report_consistency(
    report: ResearchPacketSourceRecheckPriorityReportV2,
) -> None:
    if report.row_count != _decimal_count(len(report.rows)):
        raise ValueError("row_count must match rows")
    if report.candidate_count != report.row_count:
        raise ValueError("candidate_count must match rows")
    if report.blocked_count != _status_count(report.rows, "blocked"):
        raise ValueError("blocked_count must match rows")
    if report.watch_count != _status_count(report.rows, "watch"):
        raise ValueError("watch_count must match rows")
    if report.clear_count != _status_count(report.rows, "clear"):
        raise ValueError("clear_count must match rows")
    if report.recheck_count != report.blocked_count + report.watch_count:
        raise ValueError("recheck_count must match rows")
    if report.priority_ratio != _ratio(report.recheck_count, report.row_count):
        raise ValueError("priority_ratio must match rows")
    if report.official_source_absent_count != _reason_count(
        report.rows,
        _REASON_OFFICIAL_SOURCE_ABSENT,
    ):
        raise ValueError("official_source_absent_count must match rows")
    if report.source_age_pressure_count != _count_reasons(
        report.rows,
        (
            _REASON_SOURCE_AGE_MISSING,
            _REASON_SOURCE_AGE_BLOCKED,
            _REASON_SOURCE_AGE_WATCH,
        ),
    ):
        raise ValueError("source_age_pressure_count must match rows")
    if report.contradiction_pressure_count != _count_reasons(
        report.rows,
        (_REASON_CONTRADICTION_BLOCKED, _REASON_CONTRADICTION_WATCH),
    ):
        raise ValueError("contradiction_pressure_count must match rows")
    if report.market_probability_move_pressure_count != _count_reasons(
        report.rows,
        (_REASON_PROBABILITY_MOVE_BLOCKED, _REASON_PROBABILITY_MOVE_WATCH),
    ):
        raise ValueError("market_probability_move_pressure_count must match rows")
    if report.close_urgency_count != _count_reasons(
        report.rows,
        (_REASON_CLOSE_URGENCY_BLOCKED, _REASON_CLOSE_URGENCY_WATCH),
    ):
        raise ValueError("close_urgency_count must match rows")
    if report.low_reliability_count != _count_reasons(
        report.rows,
        (_REASON_RELIABILITY_BLOCKED, _REASON_RELIABILITY_WATCH),
    ):
        raise ValueError("low_reliability_count must match rows")
    if report.max_priority_score != _max_decimal(
        (row.priority_score for row in report.rows),
        default=_ZERO,
    ):
        raise ValueError("max_priority_score must match rows")
    if report.max_source_age_seconds != _max_optional_decimal(
        row.source_age_seconds for row in report.rows
    ):
        raise ValueError("max_source_age_seconds must match rows")
    if report.max_contradiction_severity != _max_decimal(
        (row.contradiction_severity for row in report.rows),
        default=_ZERO,
    ):
        raise ValueError("max_contradiction_severity must match rows")
    if report.max_market_probability_move_magnitude != _max_decimal(
        (row.market_probability_move_magnitude for row in report.rows),
        default=_ZERO,
    ):
        raise ValueError("max_market_probability_move_magnitude must match rows")
    if report.nearest_close_time_seconds != _min_decimal(
        (row.seconds_until_close for row in report.rows),
        default=_ZERO,
    ):
        raise ValueError("nearest_close_time_seconds must match rows")
    if report.min_prior_source_reliability != _min_optional_decimal(
        row.prior_source_reliability for row in report.rows
    ):
        raise ValueError("min_prior_source_reliability must match rows")
    if report.status != _report_status(report.rows):
        raise ValueError("status must match rows")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")


def _row_sort_key(
    row: ResearchPacketSourceRecheckPriorityRowV2,
) -> tuple[int, Decimal, Decimal, Decimal, Decimal, Decimal, Decimal, str, str, str]:
    return (
        _STATUS_SORT[row.priority_status],
        -row.priority_score,
        row.seconds_until_close,
        -row.contradiction_severity,
        -row.market_probability_move_magnitude,
        -row.source_age_priority_seconds,
        row.prior_source_reliability,
        row.packet_id,
        row.market_id,
        row.source_id,
    )


def _candidate_identity(
    value: ResearchPacketSourceRecheckPriorityCandidateV2,
) -> tuple[str, str, str]:
    return (value.packet_id, value.market_id, value.source_id)


def _row_identity(row: ResearchPacketSourceRecheckPriorityRowV2) -> tuple[str, str, str]:
    return (row.packet_id, row.market_id, row.source_id)


def _status_count(
    rows: tuple[ResearchPacketSourceRecheckPriorityRowV2, ...],
    status: str,
) -> Decimal:
    return _decimal_count(sum(1 for row in rows if row.priority_status == status))


def _reason_count(
    rows: tuple[ResearchPacketSourceRecheckPriorityRowV2, ...],
    reason_code: str,
) -> Decimal:
    return _decimal_count(sum(1 for row in rows if reason_code in row.reason_codes))


def _count_reasons(
    rows: tuple[ResearchPacketSourceRecheckPriorityRowV2, ...],
    reason_codes: tuple[str, ...],
) -> Decimal:
    return _decimal_count(
        sum(1 for row in rows if any(code in row.reason_codes for code in reason_codes)),
    )


def _report_status(rows: tuple[ResearchPacketSourceRecheckPriorityRowV2, ...]) -> str:
    if not rows:
        return "empty"
    if any(row.priority_status == "blocked" for row in rows):
        return "blocked"
    if any(row.priority_status == "watch" for row in rows):
        return "watch"
    return "clear"


def _report_reason_codes(
    rows: tuple[ResearchPacketSourceRecheckPriorityRowV2, ...],
) -> tuple[str, ...]:
    if not rows:
        return (_REASON_EMPTY,)
    reason_codes = tuple(
        reason_code
        for reason_code in ROW_REASON_CODES
        if reason_code != _REASON_CLEAR
        and any(reason_code in row.reason_codes for row in rows)
    )
    if reason_codes:
        return reason_codes
    return (_REASON_CLEAR,)


def _row_status(reason_codes: tuple[str, ...]) -> str:
    if any(reason_code in _BLOCKED_REASON_CODES for reason_code in reason_codes):
        return "blocked"
    if reason_codes == (_REASON_CLEAR,):
        return "clear"
    return "watch"


def _priority_score(reason_codes: Iterable[str]) -> Decimal:
    unclamped = _unclamped_priority_score(tuple(reason_codes))
    if unclamped > _ONE_HUNDRED:
        return _ONE_HUNDRED
    return _quantize(unclamped)


def _unclamped_priority_score(reason_codes: tuple[str, ...]) -> Decimal:
    total = _ZERO
    for reason_code in reason_codes:
        total += _REASON_SCORE.get(reason_code, _ZERO)
    return _quantize(total)


def _nonnegative_seconds_between(start: datetime, end: datetime) -> Decimal:
    seconds = _seconds_between(start, end)
    if seconds < _ZERO:
        return _ZERO
    return seconds


def _seconds_between(start: datetime, end: datetime) -> Decimal:
    delta = end - start
    whole_seconds = Decimal(delta.days) * _SECONDS_PER_DAY + Decimal(delta.seconds)
    microseconds = Decimal(delta.microseconds) / _MICROSECONDS_PER_SECOND
    with localcontext(_DECIMAL_CONTEXT):
        return _quantize(whole_seconds + microseconds)


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == _ZERO:
        return _ZERO
    with localcontext(_DECIMAL_CONTEXT):
        return _quantize(numerator / denominator)


def _decimal_count(value: int) -> Decimal:
    return _quantize(Decimal(value))


def _max_decimal(values: Iterable[Decimal], *, default: Decimal) -> Decimal:
    items = tuple(values)
    if not items:
        return default
    return max(items)


def _min_decimal(values: Iterable[Decimal], *, default: Decimal) -> Decimal:
    items = tuple(values)
    if not items:
        return default
    return min(items)


def _max_optional_decimal(values: Iterable[Decimal | None]) -> Decimal | None:
    items = tuple(value for value in values if value is not None)
    if not items:
        return None
    return max(items)


def _min_optional_decimal(values: Iterable[Decimal | None]) -> Decimal | None:
    items = tuple(value for value in values if value is not None)
    if not items:
        return None
    return min(items)


def _normalize_reason_codes(
    value: Iterable[str],
    allowed: tuple[str, ...],
) -> tuple[str, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError("reason_codes must be an iterable of strings")
    try:
        normalized = tuple(value)
    except TypeError as exc:
        raise ValueError("reason_codes must be an iterable of strings") from exc
    if not normalized:
        raise ValueError("reason_codes must contain at least one value")
    if len(set(normalized)) != len(normalized):
        raise ValueError("reason_codes must not contain duplicates")
    for reason_code in normalized:
        _require_canonical_string("reason_codes", reason_code)
        if reason_code not in allowed:
            raise ValueError("reason_codes contains an unknown value")
    return normalized


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a non-empty canonical string")


def _require_exact_type(field_name: str, value: object, expected_type: type) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{field_name} must be a {expected_type.__name__}")


def _require_hard_flags(value: object) -> None:
    if getattr(value, "paper_only", None) is not True:
        raise ValueError("paper_only must be True")
    if getattr(value, "report_only", None) is not True:
        raise ValueError("report_only must be True")
    if getattr(value, "readonly", None) is not True:
        raise ValueError("readonly must be True")


def _normalize_positive_count(field_name: str, value: object) -> Decimal:
    normalized = _normalize_count(field_name, value)
    if normalized <= _ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _normalize_count(field_name: str, value: object) -> Decimal:
    normalized = _normalize_nonnegative_decimal(field_name, value)
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{field_name} must be a whole Decimal")
    return normalized


def _normalize_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized < _ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _normalize_optional_nonnegative_decimal(
    field_name: str,
    value: object,
) -> Decimal | None:
    if value is None:
        return None
    return _normalize_nonnegative_decimal(field_name, value)


def _normalize_ratio(field_name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized < _ZERO or normalized > _ONE:
        raise ValueError(f"{field_name} must be between zero and one")
    return normalized


def _normalize_optional_ratio(field_name: str, value: object) -> Decimal | None:
    if value is None:
        return None
    return _normalize_ratio(field_name, value)


def _normalize_priority_score(field_name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized < _ZERO or normalized > _ONE_HUNDRED:
        raise ValueError(f"{field_name} must be between zero and one hundred")
    return normalized


def _normalize_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return _quantize(value)


def _quantize(value: Decimal) -> Decimal:
    with localcontext(_DECIMAL_CONTEXT):
        return value.quantize(_QUANTUM)


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _optional_as_utc(field_name: str, value: object) -> datetime | None:
    if value is None:
        return None
    return _as_utc(field_name, value)


def _payload_value(value: object) -> object:
    if isinstance(value, Decimal):
        if type(value) is not Decimal:
            raise ValueError("payload Decimal values must be exactly Decimal")
        if not value.is_finite():
            raise ValueError("payload Decimal values must be finite")
        return str(value)
    if isinstance(value, datetime):
        if type(value) is not datetime:
            raise ValueError("payload datetime values must be exactly datetime")
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("payload datetime values must be timezone-aware")
        return value.astimezone(UTC).isoformat()
    if is_dataclass(value) and not isinstance(value, type):
        return _payload_value(asdict(value))
    if value is None:
        return None
    if type(value) is bool:
        return value
    if type(value) in (float, int):
        raise ValueError("payload numeric values must use Decimal")
    if type(value) is str:
        return value
    if isinstance(value, tuple):
        return [_payload_value(item) for item in value]
    if isinstance(value, list):
        return [_payload_value(item) for item in value]
    if isinstance(value, dict):
        ready: dict[str, Any] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("public payload object keys must be strings")
            ready[key] = _payload_value(item)
        return ready
    raise ValueError("value is not public payload serializable")


def _reject_unsafe_public_surface(label: str, value: object, path: str = "") -> None:
    if is_dataclass(value) and not isinstance(value, type):
        _reject_unsafe_public_surface(label, asdict(value), path)
        return
    if type(value) is str:
        if _has_unsafe_surface_fragment(value):
            raise ValueError(f"{path or label} has unsafe public value")
        return
    if isinstance(value, dict):
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("public payload object keys must be strings")
            nested_path = key if not path else f"{path}.{key}"
            if _has_unsafe_surface_fragment(key):
                raise ValueError(f"unsafe public surface field in {label}: {key}")
            _reject_unsafe_public_surface(label, item, nested_path)
        return
    if isinstance(value, (list, tuple)):
        for index, item in enumerate(value):
            nested_path = f"{path}[{index}]" if path else f"{label}[{index}]"
            _reject_unsafe_public_surface(label, item, nested_path)


def _has_unsafe_surface_fragment(value: str) -> bool:
    normalized = value.lower()
    return any(fragment in normalized for fragment in _UNSAFE_PUBLIC_SURFACE_FRAGMENTS)


def _require_public_payload_values(value: object, path: str = "payload") -> None:
    if type(value) in (float, int):
        raise ValueError(f"{path} must use Decimal-derived string values")
    if type(value) is bool or value is None or type(value) is str:
        return
    if isinstance(value, dict):
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("public payload object keys must be strings")
            item_path = f"{path}.{key}"
            if key in {"paper_only", "report_only", "readonly"} and item is not True:
                raise ValueError(f"{key} must be True for readonly public payload")
            _require_public_payload_values(item, item_path)
        return
    if isinstance(value, list):
        for index, item in enumerate(value):
            _require_public_payload_values(item, f"{path}[{index}]")
        return
    raise ValueError(f"{path} is not public payload serializable")


def _require_or_set_digest(value: object) -> None:
    current = getattr(value, _DIGEST_FIELD, None)
    if type(current) is not str:
        raise ValueError("derived_validation_digest must be a string")
    expected = _digest_for_value(value)
    if current == "":
        object.__setattr__(value, _DIGEST_FIELD, expected)
        return
    if not _is_digest(current):
        raise ValueError("derived_validation_digest must be a sha256 hex digest")
    if current != expected:
        raise ValueError(
            "derived_validation_digest mismatch for priority_rank priority_score payload",
        )


def _digest_for_value(value: object) -> str:
    digest_value = _canonical_digest_value(_payload_value(value))
    return sha256(repr(digest_value).encode("utf-8")).hexdigest()


def _canonical_digest_value(value: object) -> object:
    if isinstance(value, dict):
        return tuple(
            (key, _canonical_digest_value(item))
            for key, item in sorted(value.items())
            if key != _DIGEST_FIELD
        )
    if isinstance(value, list):
        return tuple(_canonical_digest_value(item) for item in value)
    return value


def _validate_payload_digest_tree(value: object) -> None:
    if isinstance(value, dict):
        digest = value.get(_DIGEST_FIELD)
        if digest is not None:
            if type(digest) is not str or not _is_digest(digest):
                raise ValueError("derived_validation_digest must be a sha256 hex digest")
            expected = sha256(
                repr(_canonical_digest_value(value)).encode("utf-8"),
            ).hexdigest()
            if digest != expected:
                raise ValueError("derived_validation_digest mismatch")
        for item in value.values():
            _validate_payload_digest_tree(item)
        return
    if isinstance(value, list):
        for item in value:
            _validate_payload_digest_tree(item)


def _is_digest(value: str) -> bool:
    if len(value) != 64:
        return False
    return all(character in "0123456789abcdef" for character in value)
