"""Pure paper-only research information timeliness scoring."""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, InvalidOperation, ROUND_HALF_EVEN, localcontext
from typing import Any


DEFAULT_RESEARCH_INFORMATION_TIMELINESS_SCORE_CONFIG_VERSION = (
    "research-information-timeliness-score-v1"
)

VALUE_QUANTUM = Decimal("0.000001")
COUNT_QUANTUM = Decimal("1")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
MICROSECONDS_PER_HOUR = Decimal("3600000000")
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
DERIVED_VALIDATION_DIGEST_FIELD = "derived_validation_digest"
LOWER_HEX_DIGITS = frozenset("0123456789abcdef")

PASS_TIMELINESS_STATUS = "pass"
WATCH_TIMELINESS_STATUS = "watch"
BLOCK_TIMELINESS_STATUS = "block"
TIMELINESS_STATUSES = (
    PASS_TIMELINESS_STATUS,
    WATCH_TIMELINESS_STATUS,
    BLOCK_TIMELINESS_STATUS,
)

REASON_CODES = (
    "deadline_compressed",
    "deadline_elapsed",
    "deadline_open",
    "finalization_compressed",
    "finalization_elapsed",
    "finalization_open",
    "source_newest_blocked",
    "source_newest_fresh",
    "source_newest_stale",
    "source_quorum_clean",
    "source_quorum_stale",
    "timeliness_block",
    "timeliness_pass",
    "timeliness_watch",
)

SENSITIVE_TEXT_FRAGMENTS = (
    "://",
    "sec" + "ret",
    "tok" + "en",
    "api" + "_key",
    "priv" + "ate",
    "bear" + "er ",
    "pass" + "word",
    "seed" + "_phrase",
    "bu" + "y",
    "se" + "ll",
    "reco" + "mmendation",
    "posi" + "tion sizing",
)
UNSAFE_FIELD_FRAGMENTS = (
    "cand" + "idate",
    "mar" + "ket",
    "sl" + "ug",
    "ques" + "tion",
    "source" + "_ref",
    "source" + "_ur" + "l",
    "ur" + "l",
    "ds" + "n",
    "ta" + "ble",
    "aut" + "h",
    "wal" + "let",
    "account",
    "balance",
    "ord" + "er",
    "can" + "cel",
    "re" + "place",
    "si" + "gn",
    "exchange" + "_mutation",
    "bro" + "ker",
    "net" + "work",
    "data" + "base",
    "per" + "sist",
    "tra" + "de",
    "bu" + "y",
    "se" + "ll",
    "reco" + "mmend",
    "posi" + "tion",
)


@dataclass(frozen=True)
class ResearchInformationTimelinessScoreConfig:
    config_version: str = DEFAULT_RESEARCH_INFORMATION_TIMELINESS_SCORE_CONFIG_VERSION
    pass_timeliness_score: Decimal = Decimal("0.800000")
    watch_timeliness_score: Decimal = Decimal("0.500000")
    deadline_watch_window_hours: Decimal = Decimal("24.000000")
    finalization_watch_window_hours: Decimal = Decimal("6.000000")
    source_recency_weight: Decimal = Decimal("0.650000")
    source_quorum_weight: Decimal = Decimal("0.250000")
    event_window_weight: Decimal = Decimal("0.100000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_INFORMATION_TIMELINESS_SCORE_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "pass_timeliness_score",
            "watch_timeliness_score",
            "source_recency_weight",
            "source_quorum_weight",
            "event_window_weight",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "deadline_watch_window_hours",
            "finalization_watch_window_hours",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_positive_value(field_name, getattr(self, field_name)),
            )
        if self.pass_timeliness_score < self.watch_timeliness_score:
            raise ValueError(
                "pass_timeliness_score must be at least watch_timeliness_score",
            )
        weight_sum = _q(
            self.source_recency_weight
            + self.source_quorum_weight
            + self.event_window_weight,
        )
        if weight_sum != ONE:
            raise ValueError("config weights must sum to 1.000000")
        _require_paper_flags("config", self)
        _reject_unsafe_public_payload("config", self)


@dataclass(frozen=True)
class ResearchInformationTimelinessSourceObservation:
    observed_at: datetime
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        _require_paper_flags("source observation", self)
        _reject_unsafe_public_payload("source observation", self)


@dataclass(frozen=True)
class ResearchInformationTimelinessScoreInput:
    source_observations: tuple[ResearchInformationTimelinessSourceObservation, ...]
    event_deadline_at: datetime
    event_finalization_at: datetime
    source_stale_after_hours: Decimal
    source_block_after_hours: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "source_observations",
            _normalize_source_observations(self.source_observations),
        )
        object.__setattr__(
            self,
            "event_deadline_at",
            _as_utc("event_deadline_at", self.event_deadline_at),
        )
        object.__setattr__(
            self,
            "event_finalization_at",
            _as_utc("event_finalization_at", self.event_finalization_at),
        )
        if self.event_finalization_at < self.event_deadline_at:
            raise ValueError("event_finalization_at must not be before event_deadline_at")
        object.__setattr__(
            self,
            "source_stale_after_hours",
            _normalize_positive_value(
                "source_stale_after_hours",
                self.source_stale_after_hours,
            ),
        )
        object.__setattr__(
            self,
            "source_block_after_hours",
            _normalize_positive_value(
                "source_block_after_hours",
                self.source_block_after_hours,
            ),
        )
        if self.source_block_after_hours <= self.source_stale_after_hours:
            raise ValueError("source_block_after_hours must exceed source_stale_after_hours")
        _require_paper_flags("input", self)
        _reject_unsafe_public_payload("input", self)


@dataclass(frozen=True)
class ResearchInformationTimelinessScoreReport:
    config_version: str
    pass_timeliness_score: Decimal
    watch_timeliness_score: Decimal
    deadline_watch_window_hours: Decimal
    finalization_watch_window_hours: Decimal
    source_recency_weight: Decimal
    source_quorum_weight: Decimal
    event_window_weight: Decimal
    generated_at: datetime
    source_count: Decimal
    source_observed_at_values: tuple[datetime, ...]
    newest_source_observed_at: datetime
    oldest_source_observed_at: datetime
    newest_source_age_hours: Decimal
    oldest_source_age_hours: Decimal
    stale_source_count: Decimal
    stale_source_ratio: Decimal
    source_stale_after_hours: Decimal
    source_block_after_hours: Decimal
    event_deadline_at: datetime
    event_finalization_at: datetime
    deadline_window_hours: Decimal
    finalization_window_hours: Decimal
    source_recency_score: Decimal
    source_quorum_score: Decimal
    event_window_score: Decimal
    timeliness_score: Decimal
    timeliness_status: str
    reason_codes: tuple[str, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_INFORMATION_TIMELINESS_SCORE_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "pass_timeliness_score",
            "watch_timeliness_score",
            "source_recency_weight",
            "source_quorum_weight",
            "event_window_weight",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "deadline_watch_window_hours",
            "finalization_watch_window_hours",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_positive_value(field_name, getattr(self, field_name)),
            )
        if self.pass_timeliness_score < self.watch_timeliness_score:
            raise ValueError(
                "pass_timeliness_score must be at least watch_timeliness_score",
            )
        if _q(
            self.source_recency_weight
            + self.source_quorum_weight
            + self.event_window_weight,
        ) != ONE:
            raise ValueError("report weights must sum to 1.000000")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        object.__setattr__(
            self,
            "source_observed_at_values",
            _normalize_datetime_tuple(
                "source_observed_at_values",
                self.source_observed_at_values,
            ),
        )
        object.__setattr__(
            self,
            "newest_source_observed_at",
            _as_utc("newest_source_observed_at", self.newest_source_observed_at),
        )
        object.__setattr__(
            self,
            "oldest_source_observed_at",
            _as_utc("oldest_source_observed_at", self.oldest_source_observed_at),
        )
        object.__setattr__(
            self,
            "event_deadline_at",
            _as_utc("event_deadline_at", self.event_deadline_at),
        )
        object.__setattr__(
            self,
            "event_finalization_at",
            _as_utc("event_finalization_at", self.event_finalization_at),
        )
        for field_name in (
            "source_count",
            "stale_source_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_count(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "newest_source_age_hours",
            "oldest_source_age_hours",
            "source_stale_after_hours",
            "source_block_after_hours",
            "deadline_window_hours",
            "finalization_window_hours",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_value(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "stale_source_ratio",
            "source_recency_score",
            "source_quorum_score",
            "event_window_score",
            "timeliness_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        if self.source_stale_after_hours <= ZERO:
            raise ValueError("source_stale_after_hours must be above zero")
        if self.source_block_after_hours <= self.source_stale_after_hours:
            raise ValueError("source_block_after_hours must exceed source_stale_after_hours")
        object.__setattr__(
            self,
            "timeliness_status",
            _normalize_choice(
                "timeliness_status",
                self.timeliness_status,
                TIMELINESS_STATUSES,
            ),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        object.__setattr__(
            self,
            DERIVED_VALIDATION_DIGEST_FIELD,
            _normalize_digest(
                DERIVED_VALIDATION_DIGEST_FIELD,
                self.derived_validation_digest,
            ),
        )
        _require_paper_flags("report", self)
        _reject_unsafe_public_payload("report", self)
        _validate_report_derived_values(self)
        _validate_report_derived_digest(self)

    @property
    def payload(self) -> dict[str, Any]:
        return research_information_timeliness_score_payload(self)


def score_research_information_timeliness(
    input_row: ResearchInformationTimelinessScoreInput,
    *,
    config: ResearchInformationTimelinessScoreConfig | None = None,
    generated_at: datetime,
) -> ResearchInformationTimelinessScoreReport:
    if type(input_row) is not ResearchInformationTimelinessScoreInput:
        raise ValueError("input_row must be a ResearchInformationTimelinessScoreInput")
    cfg = config or ResearchInformationTimelinessScoreConfig()
    if type(cfg) is not ResearchInformationTimelinessScoreConfig:
        raise ValueError("config must be a ResearchInformationTimelinessScoreConfig")

    normalized_generated_at = _as_utc("generated_at", generated_at)
    for observation in input_row.source_observations:
        if observation.observed_at > normalized_generated_at:
            raise ValueError("source observed_at must not be after generated_at")

    source_observed_at_values = tuple(
        sorted(observation.observed_at for observation in input_row.source_observations),
    )
    source_ages = tuple(
        _duration_hours(normalized_generated_at, observed_at)
        for observed_at in source_observed_at_values
    )
    source_count = _decimal_count(len(source_observed_at_values))
    newest_source_observed_at = source_observed_at_values[-1]
    oldest_source_observed_at = source_observed_at_values[0]
    newest_source_age_hours = source_ages[-1]
    oldest_source_age_hours = source_ages[0]
    stale_source_count = _decimal_count(
        sum(
            1
            for source_age in source_ages
            if source_age >= input_row.source_stale_after_hours
        ),
    )
    stale_source_ratio = _bounded_ratio(stale_source_count, source_count)
    source_recency_score = _q(
        ONE
        - _bounded_ratio(
            newest_source_age_hours,
            input_row.source_block_after_hours,
        ),
    )
    source_quorum_score = _q(ONE - stale_source_ratio)
    deadline_window_hours = _window_hours(
        input_row.event_deadline_at,
        normalized_generated_at,
    )
    finalization_window_hours = _window_hours(
        input_row.event_finalization_at,
        normalized_generated_at,
    )
    event_window_score = min(
        _bounded_ratio(deadline_window_hours, cfg.deadline_watch_window_hours),
        _bounded_ratio(
            finalization_window_hours,
            cfg.finalization_watch_window_hours,
        ),
    )
    timeliness_score = _q(
        (source_recency_score * cfg.source_recency_weight)
        + (source_quorum_score * cfg.source_quorum_weight)
        + (event_window_score * cfg.event_window_weight),
    )
    timeliness_status = _timeliness_status(
        timeliness_score=timeliness_score,
        newest_source_age_hours=newest_source_age_hours,
        source_block_after_hours=input_row.source_block_after_hours,
        deadline_elapsed=input_row.event_deadline_at <= normalized_generated_at,
        finalization_elapsed=input_row.event_finalization_at <= normalized_generated_at,
        pass_timeliness_score=cfg.pass_timeliness_score,
        watch_timeliness_score=cfg.watch_timeliness_score,
    )
    report_values: dict[str, Any] = {
        "config_version": cfg.config_version,
        "pass_timeliness_score": cfg.pass_timeliness_score,
        "watch_timeliness_score": cfg.watch_timeliness_score,
        "deadline_watch_window_hours": cfg.deadline_watch_window_hours,
        "finalization_watch_window_hours": cfg.finalization_watch_window_hours,
        "source_recency_weight": cfg.source_recency_weight,
        "source_quorum_weight": cfg.source_quorum_weight,
        "event_window_weight": cfg.event_window_weight,
        "generated_at": normalized_generated_at,
        "source_count": source_count,
        "source_observed_at_values": source_observed_at_values,
        "newest_source_observed_at": newest_source_observed_at,
        "oldest_source_observed_at": oldest_source_observed_at,
        "newest_source_age_hours": newest_source_age_hours,
        "oldest_source_age_hours": oldest_source_age_hours,
        "stale_source_count": stale_source_count,
        "stale_source_ratio": stale_source_ratio,
        "source_stale_after_hours": input_row.source_stale_after_hours,
        "source_block_after_hours": input_row.source_block_after_hours,
        "event_deadline_at": input_row.event_deadline_at,
        "event_finalization_at": input_row.event_finalization_at,
        "deadline_window_hours": deadline_window_hours,
        "finalization_window_hours": finalization_window_hours,
        "source_recency_score": source_recency_score,
        "source_quorum_score": source_quorum_score,
        "event_window_score": event_window_score,
        "timeliness_score": timeliness_score,
        "timeliness_status": timeliness_status,
        "reason_codes": _reason_codes(
            timeliness_status=timeliness_status,
            newest_source_age_hours=newest_source_age_hours,
            source_stale_after_hours=input_row.source_stale_after_hours,
            source_block_after_hours=input_row.source_block_after_hours,
            stale_source_count=stale_source_count,
            deadline_window_hours=deadline_window_hours,
            finalization_window_hours=finalization_window_hours,
            deadline_watch_window_hours=cfg.deadline_watch_window_hours,
            finalization_watch_window_hours=cfg.finalization_watch_window_hours,
            deadline_elapsed=input_row.event_deadline_at <= normalized_generated_at,
            finalization_elapsed=input_row.event_finalization_at
            <= normalized_generated_at,
        ),
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    return ResearchInformationTimelinessScoreReport(
        **report_values,
        derived_validation_digest=_derived_validation_digest(report_values),
    )


def research_information_timeliness_score_payload(
    report: ResearchInformationTimelinessScoreReport | dict[str, Any],
) -> dict[str, Any]:
    if type(report) is ResearchInformationTimelinessScoreReport:
        _require_paper_flags("report", report)
        _reject_unsafe_public_payload("report", report)
        payload = _json_ready(report)
    elif type(report) is dict:
        _reject_unsafe_public_payload("payload", report)
        _validate_public_payload_decimal_strings(report)
        payload = _json_ready(report)
    else:
        raise ValueError("report must be a ResearchInformationTimelinessScoreReport")
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    _require_paper_flags("payload", _DictFlags(payload))
    _reject_unsafe_public_payload("payload", payload)
    _validate_public_payload_temporal_strings(payload)
    _validate_public_payload_derived_digest(payload)
    _validate_public_payload_semantics(payload)
    return payload


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


PUBLIC_PAYLOAD_FIELDS = (
    "config_version",
    "pass_timeliness_score",
    "watch_timeliness_score",
    "deadline_watch_window_hours",
    "finalization_watch_window_hours",
    "source_recency_weight",
    "source_quorum_weight",
    "event_window_weight",
    "generated_at",
    "source_count",
    "source_observed_at_values",
    "newest_source_observed_at",
    "oldest_source_observed_at",
    "newest_source_age_hours",
    "oldest_source_age_hours",
    "stale_source_count",
    "stale_source_ratio",
    "source_stale_after_hours",
    "source_block_after_hours",
    "event_deadline_at",
    "event_finalization_at",
    "deadline_window_hours",
    "finalization_window_hours",
    "source_recency_score",
    "source_quorum_score",
    "event_window_score",
    "timeliness_score",
    "timeliness_status",
    "reason_codes",
    DERIVED_VALIDATION_DIGEST_FIELD,
    "paper_only",
    "report_only",
    "readonly",
)
PUBLIC_COUNT_DECIMAL_STRING_FIELDS = frozenset(
    (
        "source_count",
        "stale_source_count",
    ),
)
PUBLIC_VALUE_DECIMAL_STRING_FIELDS = frozenset(
    (
        "newest_source_age_hours",
        "oldest_source_age_hours",
        "source_stale_after_hours",
        "source_block_after_hours",
        "deadline_watch_window_hours",
        "finalization_watch_window_hours",
        "deadline_window_hours",
        "finalization_window_hours",
    ),
)
PUBLIC_PROBABILITY_DECIMAL_STRING_FIELDS = frozenset(
    (
        "stale_source_ratio",
        "pass_timeliness_score",
        "watch_timeliness_score",
        "source_recency_weight",
        "source_quorum_weight",
        "event_window_weight",
        "source_recency_score",
        "source_quorum_score",
        "event_window_score",
        "timeliness_score",
    ),
)
PUBLIC_DATETIME_STRING_FIELDS = frozenset(
    (
        "generated_at",
        "newest_source_observed_at",
        "oldest_source_observed_at",
        "event_deadline_at",
        "event_finalization_at",
    ),
)


def _timeliness_status(
    *,
    timeliness_score: Decimal,
    newest_source_age_hours: Decimal,
    source_block_after_hours: Decimal,
    deadline_elapsed: bool,
    finalization_elapsed: bool,
    pass_timeliness_score: Decimal,
    watch_timeliness_score: Decimal,
) -> str:
    if finalization_elapsed:
        return BLOCK_TIMELINESS_STATUS
    if newest_source_age_hours >= source_block_after_hours:
        return BLOCK_TIMELINESS_STATUS
    if timeliness_score < watch_timeliness_score:
        return BLOCK_TIMELINESS_STATUS
    if deadline_elapsed:
        return WATCH_TIMELINESS_STATUS
    if timeliness_score < pass_timeliness_score:
        return WATCH_TIMELINESS_STATUS
    return PASS_TIMELINESS_STATUS


def _reason_codes(
    *,
    timeliness_status: str,
    newest_source_age_hours: Decimal,
    source_stale_after_hours: Decimal,
    source_block_after_hours: Decimal,
    stale_source_count: Decimal,
    deadline_window_hours: Decimal,
    finalization_window_hours: Decimal,
    deadline_watch_window_hours: Decimal,
    finalization_watch_window_hours: Decimal,
    deadline_elapsed: bool,
    finalization_elapsed: bool,
) -> tuple[str, ...]:
    codes = (
        _deadline_reason_code(
            deadline_window_hours,
            deadline_watch_window_hours,
            deadline_elapsed,
        ),
        _finalization_reason_code(
            finalization_window_hours,
            finalization_watch_window_hours,
            finalization_elapsed,
        ),
        _source_newest_reason_code(
            newest_source_age_hours,
            source_stale_after_hours,
            source_block_after_hours,
        ),
        (
            "source_quorum_stale"
            if stale_source_count > ZERO
            else "source_quorum_clean"
        ),
        f"timeliness_{timeliness_status}",
    )
    return _normalize_reason_codes("reason_codes", tuple(sorted(codes)))


def _deadline_reason_code(
    deadline_window_hours: Decimal,
    deadline_watch_window_hours: Decimal,
    deadline_elapsed: bool,
) -> str:
    if deadline_elapsed:
        return "deadline_elapsed"
    if deadline_window_hours < deadline_watch_window_hours:
        return "deadline_compressed"
    return "deadline_open"


def _finalization_reason_code(
    finalization_window_hours: Decimal,
    finalization_watch_window_hours: Decimal,
    finalization_elapsed: bool,
) -> str:
    if finalization_elapsed:
        return "finalization_elapsed"
    if finalization_window_hours < finalization_watch_window_hours:
        return "finalization_compressed"
    return "finalization_open"


def _source_newest_reason_code(
    newest_source_age_hours: Decimal,
    source_stale_after_hours: Decimal,
    source_block_after_hours: Decimal,
) -> str:
    if newest_source_age_hours >= source_block_after_hours:
        return "source_newest_blocked"
    if newest_source_age_hours >= source_stale_after_hours:
        return "source_newest_stale"
    return "source_newest_fresh"


def _validate_report_derived_values(
    report: ResearchInformationTimelinessScoreReport,
) -> None:
    if report.source_count != _decimal_count(len(report.source_observed_at_values)):
        raise ValueError("report derived validation failed")
    if report.source_observed_at_values[-1] != report.newest_source_observed_at:
        raise ValueError("report derived validation failed")
    if report.source_observed_at_values[0] != report.oldest_source_observed_at:
        raise ValueError("report derived validation failed")
    if report.newest_source_age_hours != _duration_hours(
        report.generated_at,
        report.newest_source_observed_at,
    ):
        raise ValueError("report derived validation failed")
    if report.oldest_source_age_hours != _duration_hours(
        report.generated_at,
        report.oldest_source_observed_at,
    ):
        raise ValueError("report derived validation failed")
    expected_stale_count = _decimal_count(
        sum(
            1
            for observed_at in report.source_observed_at_values
            if _duration_hours(report.generated_at, observed_at)
            >= report.source_stale_after_hours
        ),
    )
    if report.stale_source_count != expected_stale_count:
        raise ValueError("report derived validation failed")
    if report.stale_source_ratio != _bounded_ratio(
        report.stale_source_count,
        report.source_count,
    ):
        raise ValueError("report derived validation failed")
    if report.source_recency_score != _q(
        ONE
        - _bounded_ratio(
            report.newest_source_age_hours,
            report.source_block_after_hours,
        ),
    ):
        raise ValueError("report derived validation failed")
    if report.source_quorum_score != _q(ONE - report.stale_source_ratio):
        raise ValueError("report derived validation failed")
    if report.deadline_window_hours != _window_hours(
        report.event_deadline_at,
        report.generated_at,
    ):
        raise ValueError("report derived validation failed")
    if report.finalization_window_hours != _window_hours(
        report.event_finalization_at,
        report.generated_at,
    ):
        raise ValueError("report derived validation failed")
    expected_event_window_score = min(
        _bounded_ratio(
            report.deadline_window_hours,
            report.deadline_watch_window_hours,
        ),
        _bounded_ratio(
            report.finalization_window_hours,
            report.finalization_watch_window_hours,
        ),
    )
    if report.event_window_score != expected_event_window_score:
        raise ValueError("report derived validation failed")
    expected_timeliness_score = _q(
        (report.source_recency_score * report.source_recency_weight)
        + (report.source_quorum_score * report.source_quorum_weight)
        + (report.event_window_score * report.event_window_weight),
    )
    if report.timeliness_score != expected_timeliness_score:
        raise ValueError("report derived validation failed")
    expected_status = _status_from_report(report)
    if report.timeliness_status != expected_status:
        raise ValueError("report timeliness_status must match")
    if report.reason_codes != _reason_codes_from_report(report):
        raise ValueError("report reason_codes must match")


def _status_from_report(report: ResearchInformationTimelinessScoreReport) -> str:
    return _timeliness_status(
        timeliness_score=report.timeliness_score,
        newest_source_age_hours=report.newest_source_age_hours,
        source_block_after_hours=report.source_block_after_hours,
        deadline_elapsed=report.event_deadline_at <= report.generated_at,
        finalization_elapsed=report.event_finalization_at <= report.generated_at,
        pass_timeliness_score=report.pass_timeliness_score,
        watch_timeliness_score=report.watch_timeliness_score,
    )


def _reason_codes_from_report(
    report: ResearchInformationTimelinessScoreReport,
) -> tuple[str, ...]:
    return _reason_codes(
        timeliness_status=report.timeliness_status,
        newest_source_age_hours=report.newest_source_age_hours,
        source_stale_after_hours=report.source_stale_after_hours,
        source_block_after_hours=report.source_block_after_hours,
        stale_source_count=report.stale_source_count,
        deadline_window_hours=report.deadline_window_hours,
        finalization_window_hours=report.finalization_window_hours,
        deadline_watch_window_hours=report.deadline_watch_window_hours,
        finalization_watch_window_hours=report.finalization_watch_window_hours,
        deadline_elapsed=report.event_deadline_at <= report.generated_at,
        finalization_elapsed=report.event_finalization_at <= report.generated_at,
    )


def _validate_report_derived_digest(
    report: ResearchInformationTimelinessScoreReport,
) -> None:
    expected_digest = _derived_validation_digest(_report_digest_values(report))
    if report.derived_validation_digest != expected_digest:
        raise ValueError("report derived_validation_digest must match")


def _report_digest_values(report: ResearchInformationTimelinessScoreReport) -> dict[str, Any]:
    return {
        "config_version": report.config_version,
        "pass_timeliness_score": report.pass_timeliness_score,
        "watch_timeliness_score": report.watch_timeliness_score,
        "deadline_watch_window_hours": report.deadline_watch_window_hours,
        "finalization_watch_window_hours": report.finalization_watch_window_hours,
        "source_recency_weight": report.source_recency_weight,
        "source_quorum_weight": report.source_quorum_weight,
        "event_window_weight": report.event_window_weight,
        "generated_at": report.generated_at,
        "source_count": report.source_count,
        "source_observed_at_values": report.source_observed_at_values,
        "newest_source_observed_at": report.newest_source_observed_at,
        "oldest_source_observed_at": report.oldest_source_observed_at,
        "newest_source_age_hours": report.newest_source_age_hours,
        "oldest_source_age_hours": report.oldest_source_age_hours,
        "stale_source_count": report.stale_source_count,
        "stale_source_ratio": report.stale_source_ratio,
        "source_stale_after_hours": report.source_stale_after_hours,
        "source_block_after_hours": report.source_block_after_hours,
        "event_deadline_at": report.event_deadline_at,
        "event_finalization_at": report.event_finalization_at,
        "deadline_window_hours": report.deadline_window_hours,
        "finalization_window_hours": report.finalization_window_hours,
        "source_recency_score": report.source_recency_score,
        "source_quorum_score": report.source_quorum_score,
        "event_window_score": report.event_window_score,
        "timeliness_score": report.timeliness_score,
        "timeliness_status": report.timeliness_status,
        "reason_codes": report.reason_codes,
        "paper_only": report.paper_only,
        "report_only": report.report_only,
        "readonly": report.readonly,
    }


def _validate_public_payload_derived_digest(payload: dict[str, Any]) -> None:
    if frozenset(payload) != frozenset(PUBLIC_PAYLOAD_FIELDS):
        raise ValueError("payload fields must match")
    provided_digest = _normalize_digest(
        DERIVED_VALIDATION_DIGEST_FIELD,
        payload[DERIVED_VALIDATION_DIGEST_FIELD],
    )
    if provided_digest != _derived_validation_digest(payload):
        raise ValueError("payload derived validation failed")


def _validate_public_payload_semantics(payload: dict[str, Any]) -> None:
    ResearchInformationTimelinessScoreReport(
        config_version=_payload_string("config_version", payload),
        pass_timeliness_score=_payload_decimal(
            "pass_timeliness_score",
            payload,
            VALUE_QUANTUM,
        ),
        watch_timeliness_score=_payload_decimal(
            "watch_timeliness_score",
            payload,
            VALUE_QUANTUM,
        ),
        deadline_watch_window_hours=_payload_decimal(
            "deadline_watch_window_hours",
            payload,
            VALUE_QUANTUM,
        ),
        finalization_watch_window_hours=_payload_decimal(
            "finalization_watch_window_hours",
            payload,
            VALUE_QUANTUM,
        ),
        source_recency_weight=_payload_decimal(
            "source_recency_weight",
            payload,
            VALUE_QUANTUM,
        ),
        source_quorum_weight=_payload_decimal(
            "source_quorum_weight",
            payload,
            VALUE_QUANTUM,
        ),
        event_window_weight=_payload_decimal(
            "event_window_weight",
            payload,
            VALUE_QUANTUM,
        ),
        generated_at=_payload_datetime("generated_at", payload),
        source_count=_payload_decimal("source_count", payload, COUNT_QUANTUM),
        source_observed_at_values=_payload_datetime_tuple(
            "source_observed_at_values",
            payload,
        ),
        newest_source_observed_at=_payload_datetime(
            "newest_source_observed_at",
            payload,
        ),
        oldest_source_observed_at=_payload_datetime(
            "oldest_source_observed_at",
            payload,
        ),
        newest_source_age_hours=_payload_decimal(
            "newest_source_age_hours",
            payload,
            VALUE_QUANTUM,
        ),
        oldest_source_age_hours=_payload_decimal(
            "oldest_source_age_hours",
            payload,
            VALUE_QUANTUM,
        ),
        stale_source_count=_payload_decimal(
            "stale_source_count",
            payload,
            COUNT_QUANTUM,
        ),
        stale_source_ratio=_payload_decimal(
            "stale_source_ratio",
            payload,
            VALUE_QUANTUM,
        ),
        source_stale_after_hours=_payload_decimal(
            "source_stale_after_hours",
            payload,
            VALUE_QUANTUM,
        ),
        source_block_after_hours=_payload_decimal(
            "source_block_after_hours",
            payload,
            VALUE_QUANTUM,
        ),
        event_deadline_at=_payload_datetime("event_deadline_at", payload),
        event_finalization_at=_payload_datetime("event_finalization_at", payload),
        deadline_window_hours=_payload_decimal(
            "deadline_window_hours",
            payload,
            VALUE_QUANTUM,
        ),
        finalization_window_hours=_payload_decimal(
            "finalization_window_hours",
            payload,
            VALUE_QUANTUM,
        ),
        source_recency_score=_payload_decimal(
            "source_recency_score",
            payload,
            VALUE_QUANTUM,
        ),
        source_quorum_score=_payload_decimal(
            "source_quorum_score",
            payload,
            VALUE_QUANTUM,
        ),
        event_window_score=_payload_decimal(
            "event_window_score",
            payload,
            VALUE_QUANTUM,
        ),
        timeliness_score=_payload_decimal("timeliness_score", payload, VALUE_QUANTUM),
        timeliness_status=_payload_string("timeliness_status", payload),
        reason_codes=_payload_string_tuple("reason_codes", payload),
        derived_validation_digest=_payload_string(
            DERIVED_VALIDATION_DIGEST_FIELD,
            payload,
        ),
        paper_only=_payload_bool("paper_only", payload),
        report_only=_payload_bool("report_only", payload),
        readonly=_payload_bool("readonly", payload),
    )


def _payload_string(field_name: str, payload: dict[str, Any]) -> str:
    value = payload[field_name]
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    return value


def _payload_bool(field_name: str, payload: dict[str, Any]) -> bool:
    value = payload[field_name]
    if type(value) is not bool:
        raise ValueError(f"{field_name} must be a bool")
    return value


def _payload_decimal(
    field_name: str,
    payload: dict[str, Any],
    quantum: Decimal,
) -> Decimal:
    return _require_decimal_string(field_name, payload[field_name], quantum)


def _payload_datetime(field_name: str, payload: dict[str, Any]) -> datetime:
    return _require_utc_datetime_string(field_name, payload[field_name])


def _payload_datetime_tuple(field_name: str, payload: dict[str, Any]) -> tuple[datetime, ...]:
    values = payload[field_name]
    if not isinstance(values, list):
        raise ValueError(f"{field_name} must be a list")
    return tuple(_require_utc_datetime_string(field_name, value) for value in values)


def _payload_string_tuple(field_name: str, payload: dict[str, Any]) -> tuple[str, ...]:
    values = payload[field_name]
    if not isinstance(values, list):
        raise ValueError(f"{field_name} must be a list")
    if any(type(value) is not str for value in values):
        raise ValueError(f"{field_name} must contain strings")
    return tuple(values)


def _validate_public_payload_decimal_strings(payload: dict[str, Any]) -> None:
    for field_name in PUBLIC_VALUE_DECIMAL_STRING_FIELDS:
        if field_name in payload:
            _require_decimal_string(field_name, payload[field_name], VALUE_QUANTUM)
    for field_name in PUBLIC_PROBABILITY_DECIMAL_STRING_FIELDS:
        if field_name in payload:
            normalized = _require_decimal_string(
                field_name,
                payload[field_name],
                VALUE_QUANTUM,
            )
            if normalized < ZERO or normalized > ONE:
                raise ValueError(f"{field_name} Decimal-string must be between zero and one")
    for field_name in PUBLIC_COUNT_DECIMAL_STRING_FIELDS:
        if field_name in payload:
            _require_decimal_string(field_name, payload[field_name], COUNT_QUANTUM)


def _validate_public_payload_temporal_strings(payload: dict[str, Any]) -> None:
    for field_name in PUBLIC_DATETIME_STRING_FIELDS:
        if field_name in payload:
            _require_utc_datetime_string(field_name, payload[field_name])
    if "source_observed_at_values" not in payload:
        return
    values = payload["source_observed_at_values"]
    if not isinstance(values, list):
        raise ValueError("source_observed_at_values must be a list")
    observed_at_values = tuple(
        _require_utc_datetime_string("source_observed_at_values", value)
        for value in values
    )
    if tuple(sorted(observed_at_values)) != observed_at_values:
        raise ValueError("source_observed_at_values must be sorted")


def _require_decimal_string(
    field_name: str,
    value: object,
    quantum: Decimal,
) -> Decimal:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a Decimal-string")
    try:
        decimal_value = Decimal(value)
    except InvalidOperation as exc:
        raise ValueError(f"{field_name} must be a Decimal-string") from exc
    normalized = _normalize_decimal(field_name, decimal_value, quantum)
    if str(normalized) != value:
        raise ValueError(f"{field_name} Decimal-string precision must match")
    return normalized


def _require_utc_datetime_string(field_name: str, value: object) -> datetime:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a datetime string")
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError as exc:
        raise ValueError(f"{field_name} must be a datetime string") from exc
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    normalized = parsed.astimezone(UTC)
    if normalized.isoformat() != value:
        raise ValueError(f"{field_name} must be a UTC datetime string")
    return normalized


def _derived_validation_digest(value: dict[str, Any]) -> str:
    ready = _json_ready(value)
    if type(ready) is not dict:
        raise ValueError("derived validation values must be a JSON object")
    digest_values = {
        key: ready[key]
        for key in PUBLIC_PAYLOAD_FIELDS
        if key != DERIVED_VALIDATION_DIGEST_FIELD
    }
    encoded = json.dumps(
        digest_values,
        allow_nan=False,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    )
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def _normalize_source_observations(
    values: object,
) -> tuple[ResearchInformationTimelinessSourceObservation, ...]:
    if isinstance(values, (str, bytes)):
        raise ValueError("source_observations must be an iterable")
    try:
        observations = tuple(values)  # type: ignore[arg-type]
    except TypeError as exc:
        raise ValueError("source_observations must be an iterable") from exc
    if not observations:
        raise ValueError("source_observations must not be empty")
    for observation in observations:
        if type(observation) is not ResearchInformationTimelinessSourceObservation:
            raise ValueError(
                "source_observations must contain "
                "ResearchInformationTimelinessSourceObservation values",
            )
    return tuple(sorted(observations, key=lambda observation: observation.observed_at))


def _normalize_datetime_tuple(field_name: str, values: object) -> tuple[datetime, ...]:
    if isinstance(values, (str, bytes)):
        raise ValueError(f"{field_name} must be an iterable")
    try:
        datetimes = tuple(values)  # type: ignore[arg-type]
    except TypeError as exc:
        raise ValueError(f"{field_name} must be an iterable") from exc
    if not datetimes:
        raise ValueError(f"{field_name} must not be empty")
    normalized = tuple(_as_utc(field_name, value) for value in datetimes)
    if tuple(sorted(normalized)) != normalized:
        raise ValueError(f"{field_name} must be sorted")
    return normalized


def _duration_hours(later: datetime, earlier: datetime) -> Decimal:
    delta = later - earlier
    total_microseconds = Decimal(
        (delta.days * 86400000000)
        + (delta.seconds * 1000000)
        + delta.microseconds,
    )
    with localcontext(DECIMAL_CONTEXT):
        return (total_microseconds / MICROSECONDS_PER_HOUR).quantize(VALUE_QUANTUM)


def _window_hours(target_at: datetime, generated_at: datetime) -> Decimal:
    window_hours = _duration_hours(target_at, generated_at)
    if window_hours < ZERO:
        return ZERO
    return window_hours


def _bounded_ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator <= ZERO:
        raise ValueError("denominator must be above zero")
    with localcontext(DECIMAL_CONTEXT):
        ratio = numerator / denominator
    if ratio < ZERO:
        return ZERO
    if ratio > ONE:
        return ONE
    return _q(ratio)


def _decimal_count(value: int) -> Decimal:
    return Decimal(value).quantize(COUNT_QUANTUM)


def _q(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(VALUE_QUANTUM)


def _normalize_probability(field_name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(field_name, value, VALUE_QUANTUM)
    if normalized < ZERO or normalized > ONE:
        raise ValueError(f"{field_name} must be between zero and one")
    return normalized


def _normalize_nonnegative_value(field_name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(field_name, value, VALUE_QUANTUM)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _normalize_positive_value(field_name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(field_name, value, VALUE_QUANTUM)
    if normalized <= ZERO:
        raise ValueError(f"{field_name} must be above zero")
    return normalized


def _normalize_nonnegative_count(field_name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(field_name, value, COUNT_QUANTUM)
    if normalized < Decimal("0"):
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _normalize_decimal(field_name: str, value: object, quantum: Decimal) -> Decimal:
    if not isinstance(value, Decimal):
        raise ValueError(f"{field_name} must be a Decimal")
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be exactly Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    with localcontext(DECIMAL_CONTEXT):
        normalized = value.quantize(quantum)
    if normalized != value:
        raise ValueError(f"{field_name} precision is too granular")
    return normalized


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str or value.strip() != value or not value:
        raise ValueError(f"{field_name} must be a nonblank trimmed string")
    if _contains_sensitive_text(value) or _has_unsafe_surface_fragment(value):
        raise ValueError(f"{field_name} has unsafe value")


def _normalize_choice(field_name: str, value: object, allowed_values: tuple[str, ...]) -> str:
    _require_canonical_string(field_name, value)
    if value not in allowed_values:
        raise ValueError(f"{field_name} must be one of the allowed values")
    return value


def _normalize_digest(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if value == "":
        return value
    if len(value) != 64 or any(character not in LOWER_HEX_DIGITS for character in value):
        raise ValueError(f"{field_name} must be lowercase sha256 hex")
    return value


def _normalize_reason_codes(field_name: str, value: object) -> tuple[str, ...]:
    if not isinstance(value, tuple):
        raise ValueError(f"{field_name} must be a tuple")
    normalized: list[str] = []
    for item in value:
        _require_canonical_string(field_name, item)
        if item not in REASON_CODES:
            raise ValueError(f"{field_name} contains an unsupported reason code")
        normalized.append(item)
    if tuple(sorted(normalized)) != tuple(normalized):
        raise ValueError(f"{field_name} must be sorted")
    if len(set(normalized)) != len(normalized):
        raise ValueError(f"{field_name} must be unique")
    return tuple(normalized)


def _require_paper_flags(label: str, value: object) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if getattr(value, field_name, None) is not True:
            raise ValueError(f"{label} {field_name} must be True")


def _json_ready(value: Any) -> Any:
    if isinstance(value, Decimal):
        if type(value) is not Decimal:
            raise ValueError("JSON Decimal value must be exactly Decimal")
        if not value.is_finite():
            raise ValueError("JSON Decimal value must be finite")
        return str(value)
    if isinstance(value, datetime):
        if type(value) is not datetime:
            raise ValueError("JSON datetime value must be a datetime")
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("JSON datetime value must be timezone-aware")
        return value.astimezone(UTC).isoformat()
    if is_dataclass(value) and not isinstance(value, type):
        return _json_ready(asdict(value))
    if value is None:
        return None
    if type(value) is bool:
        return value
    if isinstance(value, float):
        raise ValueError("JSON value must not be a float")
    if type(value) is int:
        raise ValueError("JSON numeric value must use Decimal")
    if type(value) is str:
        return value
    if isinstance(value, tuple):
        return [_json_ready(item) for item in value]
    if isinstance(value, list):
        return [_json_ready(item) for item in value]
    if isinstance(value, dict):
        ready: dict[str, Any] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            ready[key] = _json_ready(item)
        return ready
    raise ValueError("value is not JSON serializable")


def _reject_unsafe_public_payload(label: str, value: object, path: str = "") -> None:
    if is_dataclass(value) and not isinstance(value, type):
        _reject_unsafe_public_payload(label, asdict(value), path)
        return
    if type(value) is str:
        if _contains_sensitive_text(value) or _has_unsafe_surface_fragment(value):
            raise ValueError(f"{path or label} has sensitive or unsafe value")
        return
    if isinstance(value, Decimal):
        if type(value) is not Decimal:
            raise ValueError(f"{path or label} must be exactly Decimal")
        if not value.is_finite():
            raise ValueError(f"{path or label} must be finite")
        return
    if isinstance(value, datetime):
        if type(value) is not datetime:
            raise ValueError(f"{path or label} must be a datetime")
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError(f"{path or label} must be timezone-aware")
        return
    if value is None or type(value) is bool:
        return
    if isinstance(value, float):
        raise ValueError(f"{path or label} must not be a float")
    if type(value) is int:
        raise ValueError(f"{path or label} must use Decimal-derived string values")
    if isinstance(value, dict):
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            item_path = key if not path else f"{path}.{key}"
            if _has_unsafe_surface_fragment(key):
                raise ValueError(f"unsafe field in {label}: {key}")
            if key in {"paper_only", "report_only", "readonly"} and item is not True:
                raise ValueError(f"{item_path} must be True")
            _reject_unsafe_public_payload(label, item, item_path)
        return
    if isinstance(value, (list, tuple)):
        for index, item in enumerate(value):
            item_path = f"{path}[{index}]" if path else f"{label}[{index}]"
            _reject_unsafe_public_payload(label, item, item_path)
        return
    raise ValueError("value is not JSON serializable")


def _contains_sensitive_text(value: str) -> bool:
    normalized = value.lower()
    return any(fragment in normalized for fragment in SENSITIVE_TEXT_FRAGMENTS)


def _has_unsafe_surface_fragment(value: str) -> bool:
    normalized = value.lower()
    return any(fragment in normalized for fragment in UNSAFE_FIELD_FRAGMENTS)


__all__ = (
    "DEFAULT_RESEARCH_INFORMATION_TIMELINESS_SCORE_CONFIG_VERSION",
    "TIMELINESS_STATUSES",
    "ResearchInformationTimelinessScoreConfig",
    "ResearchInformationTimelinessSourceObservation",
    "ResearchInformationTimelinessScoreInput",
    "ResearchInformationTimelinessScoreReport",
    "score_research_information_timeliness",
    "research_information_timeliness_score_payload",
)
