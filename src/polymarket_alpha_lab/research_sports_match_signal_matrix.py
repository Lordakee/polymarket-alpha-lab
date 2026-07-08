"""Pure local sports match signal matrix for human research prioritization."""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable
from dataclasses import dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
import json
from typing import Any


__all__ = (
    "DEFAULT_RESEARCH_SPORTS_MATCH_SIGNAL_MATRIX_CONFIG_VERSION",
    "ResearchSportsMatchSignalMatrixConfig",
    "ResearchSportsMatchSignalMatrixObservation",
    "ResearchSportsMatchSignalMatrixReasonCodeCount",
    "ResearchSportsMatchSignalMatrixReport",
    "ResearchSportsMatchSignalMatrixRow",
    "build_research_sports_match_signal_matrix_report",
    "research_sports_match_signal_matrix_payload",
)


DEFAULT_RESEARCH_SPORTS_MATCH_SIGNAL_MATRIX_CONFIG_VERSION = (
    "research-sports-match-signal-matrix-v0"
)
DIGEST_PREFIX = "sports-match-signal-matrix-v0:"
QUANTUM = Decimal("0.000001")
COUNT_QUANTUM = Decimal("1.000000")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
SUPPORT_CREDIT_PER_SIGNAL = Decimal("0.001750")
MAX_SUPPORT_CREDIT_SIGNALS = Decimal("4.000000")
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
STATUSES = ("pass", "watch", "block")
TEAM_SIDES = ("home", "away", "neutral")
STATUS_WEIGHT = {
    "block": Decimal("2.000000"),
    "watch": Decimal("1.000000"),
    "pass": Decimal("0.000000"),
}
PHASE_FLAG_FIELDS = ("paper_only", "report_only", "readonly")
NO_INPUTS_REASON = "sports_match_signal_matrix_no_inputs"


@dataclass(frozen=True)
class ResearchSportsMatchSignalMatrixConfig:
    config_version: str = DEFAULT_RESEARCH_SPORTS_MATCH_SIGNAL_MATRIX_CONFIG_VERSION
    form_weight: Decimal = Decimal("0.300000")
    schedule_weight: Decimal = Decimal("0.250000")
    injury_weight: Decimal = Decimal("0.300000")
    freshness_weight: Decimal = Decimal("0.100000")
    conflict_weight: Decimal = Decimal("0.050000")
    watch_priority_threshold: Decimal = Decimal("0.350000")
    block_priority_threshold: Decimal = Decimal("0.650000")
    schedule_stress_watch: Decimal = Decimal("0.550000")
    schedule_stress_block: Decimal = Decimal("0.800000")
    injury_impact_watch: Decimal = Decimal("0.300000")
    injury_impact_block: Decimal = Decimal("0.600000")
    conflict_watch: Decimal = Decimal("0.250000")
    conflict_block: Decimal = Decimal("0.500000")
    fresh_information_max_age_seconds: Decimal = Decimal("7200.000000")
    stale_information_block_age_seconds: Decimal = Decimal("43200.000000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchSportsMatchSignalMatrixConfig:
            raise TypeError(
                "ResearchSportsMatchSignalMatrixConfig does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchSportsMatchSignalMatrixConfig:
            raise ValueError(
                "config must be exactly ResearchSportsMatchSignalMatrixConfig",
            )
        _require_public_string("config_version", self.config_version)
        if self.config_version != DEFAULT_RESEARCH_SPORTS_MATCH_SIGNAL_MATRIX_CONFIG_VERSION:
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "form_weight",
            "schedule_weight",
            "injury_weight",
            "freshness_weight",
            "conflict_weight",
            "watch_priority_threshold",
            "block_priority_threshold",
            "schedule_stress_watch",
            "schedule_stress_block",
            "injury_impact_watch",
            "injury_impact_block",
            "conflict_watch",
            "conflict_block",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "fresh_information_max_age_seconds",
            "stale_information_block_age_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_positive_decimal(field_name, getattr(self, field_name)),
            )
        _require_at_most(
            "watch_priority_threshold",
            self.watch_priority_threshold,
            self.block_priority_threshold,
        )
        _require_at_most(
            "schedule_stress_watch",
            self.schedule_stress_watch,
            self.schedule_stress_block,
        )
        _require_at_most(
            "injury_impact_watch",
            self.injury_impact_watch,
            self.injury_impact_block,
        )
        _require_at_most("conflict_watch", self.conflict_watch, self.conflict_block)
        if (
            self.fresh_information_max_age_seconds
            >= self.stale_information_block_age_seconds
        ):
            raise ValueError(
                "stale_information_block_age_seconds must exceed "
                "fresh_information_max_age_seconds",
            )
        _require_hard_flags("config", self)
        _reject_unsafe_public_payload("config", self)


@dataclass(frozen=True)
class ResearchSportsMatchSignalMatrixObservation:
    match_key: str
    league: str
    team_label: str
    opponent_label: str
    team_side: str
    observed_at: datetime
    team_form_score: Decimal
    schedule_stress_score: Decimal
    injury_impact_score: Decimal
    signal_conflict_ratio: Decimal
    supporting_signal_count: Decimal
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchSportsMatchSignalMatrixObservation:
            raise TypeError(
                "ResearchSportsMatchSignalMatrixObservation does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchSportsMatchSignalMatrixObservation:
            raise ValueError(
                "observation must be exactly ResearchSportsMatchSignalMatrixObservation",
            )
        for field_name in ("match_key", "league", "team_label", "opponent_label"):
            _require_public_string(field_name, getattr(self, field_name))
        _require_member("team_side", self.team_side, TEAM_SIDES)
        object.__setattr__(
            self,
            "observed_at",
            _as_utc("observed_at", self.observed_at),
        )
        for field_name in (
            "team_form_score",
            "schedule_stress_score",
            "injury_impact_score",
            "signal_conflict_ratio",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "supporting_signal_count",
            _normalize_nonnegative_decimal(
                "supporting_signal_count",
                self.supporting_signal_count,
            ),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes),
        )
        _require_hard_flags("observation", self)
        _reject_unsafe_public_payload("observation", self)


@dataclass(frozen=True)
class ResearchSportsMatchSignalMatrixRow:
    match_key: str
    league: str
    team_label: str
    opponent_label: str
    team_side: str
    observed_at: datetime
    information_age_seconds: Decimal
    team_form_score: Decimal
    schedule_stress_score: Decimal
    injury_impact_score: Decimal
    signal_conflict_ratio: Decimal
    supporting_signal_count: Decimal
    freshness_score: Decimal
    research_priority_score: Decimal
    status: str
    public_status: str
    hard_flag: bool
    reason_codes: tuple[str, ...]
    digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchSportsMatchSignalMatrixRow:
            raise TypeError(
                "ResearchSportsMatchSignalMatrixRow does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchSportsMatchSignalMatrixRow:
            raise ValueError("row must be exactly ResearchSportsMatchSignalMatrixRow")
        for field_name in ("match_key", "league", "team_label", "opponent_label"):
            _require_public_string(field_name, getattr(self, field_name))
        _require_member("team_side", self.team_side, TEAM_SIDES)
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in (
            "team_form_score",
            "schedule_stress_score",
            "injury_impact_score",
            "signal_conflict_ratio",
            "freshness_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "information_age_seconds",
            "supporting_signal_count",
            "research_priority_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        _require_status("status", self.status)
        _require_status("public_status", self.public_status)
        if self.status != self.public_status:
            raise ValueError("public_status must match status")
        if type(self.hard_flag) is not bool:
            raise ValueError("hard_flag must be a bool")
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes),
        )
        _require_hard_flags("row", self)
        _reject_unsafe_public_payload("row", self)
        expected_digest = _row_digest(self)
        if self.digest:
            _require_digest("digest", self.digest)
            if self.digest != expected_digest:
                raise ValueError("row digest mismatch")
        else:
            object.__setattr__(self, "digest", expected_digest)


@dataclass(frozen=True)
class ResearchSportsMatchSignalMatrixReasonCodeCount:
    reason_code: str
    count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchSportsMatchSignalMatrixReasonCodeCount:
            raise TypeError(
                "ResearchSportsMatchSignalMatrixReasonCodeCount does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchSportsMatchSignalMatrixReasonCodeCount:
            raise ValueError(
                "reason_code_count must be exactly "
                "ResearchSportsMatchSignalMatrixReasonCodeCount",
            )
        _require_public_string("reason_code", self.reason_code)
        object.__setattr__(
            self,
            "count",
            _normalize_positive_decimal("count", self.count),
        )
        _require_hard_flags("reason_code_count", self)
        _reject_unsafe_public_payload("reason_code_count", self)


@dataclass(frozen=True)
class ResearchSportsMatchSignalMatrixReport:
    generated_at: datetime
    config_version: str
    subject_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    hard_flag_count: Decimal
    stale_information_count: Decimal
    injury_concern_count: Decimal
    schedule_congestion_count: Decimal
    conflict_count: Decimal
    average_research_priority_score: Decimal
    max_research_priority_score: Decimal
    average_information_age_seconds: Decimal
    status: str
    reason_codes: tuple[str, ...]
    reason_code_counts: tuple[ResearchSportsMatchSignalMatrixReasonCodeCount, ...]
    rows: tuple[ResearchSportsMatchSignalMatrixRow, ...]
    digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchSportsMatchSignalMatrixReport:
            raise TypeError(
                "ResearchSportsMatchSignalMatrixReport does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchSportsMatchSignalMatrixReport:
            raise ValueError("report must be exactly ResearchSportsMatchSignalMatrixReport")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_string("config_version", self.config_version)
        for field_name in (
            "subject_count",
            "pass_count",
            "watch_count",
            "block_count",
            "hard_flag_count",
            "stale_information_count",
            "injury_concern_count",
            "schedule_congestion_count",
            "conflict_count",
            "average_research_priority_score",
            "max_research_priority_score",
            "average_information_age_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        _require_status("status", self.status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_report_reason_codes(self.reason_codes),
        )
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        _validate_report(self)
        _require_hard_flags("report", self)
        _reject_unsafe_public_payload("report", self)
        expected_digest = _report_digest(self)
        if self.digest:
            _require_digest("digest", self.digest)
            if self.digest != expected_digest:
                raise ValueError("report digest mismatch")
        else:
            object.__setattr__(self, "digest", expected_digest)


_PUBLIC_DATACLASS_TYPES = (
    ResearchSportsMatchSignalMatrixConfig,
    ResearchSportsMatchSignalMatrixObservation,
    ResearchSportsMatchSignalMatrixReasonCodeCount,
    ResearchSportsMatchSignalMatrixReport,
    ResearchSportsMatchSignalMatrixRow,
)


def build_research_sports_match_signal_matrix_report(
    observations: Iterable[ResearchSportsMatchSignalMatrixObservation],
    *,
    config: ResearchSportsMatchSignalMatrixConfig,
    generated_at: datetime,
) -> ResearchSportsMatchSignalMatrixReport:
    if type(config) is not ResearchSportsMatchSignalMatrixConfig:
        raise ValueError("config must be a ResearchSportsMatchSignalMatrixConfig")
    _require_hard_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    inputs = _normalize_inputs(observations)
    rows = tuple(
        sorted(
            (
                _build_row(row, config=config, generated_at=generated_at_utc)
                for row in inputs
            ),
            key=_row_sort_key,
        ),
    )
    return ResearchSportsMatchSignalMatrixReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        subject_count=_count(len(rows)),
        pass_count=_status_count(rows, "pass"),
        watch_count=_status_count(rows, "watch"),
        block_count=_status_count(rows, "block"),
        hard_flag_count=_count(sum(1 for row in rows if row.hard_flag)),
        stale_information_count=_count(
            sum(1 for row in rows if _has_reason_prefix(row, "information_age_")),
        ),
        injury_concern_count=_count(
            sum(1 for row in rows if _has_reason_prefix(row, "injury_signal_") and not _has_reason(row, "injury_signal_clear")),
        ),
        schedule_congestion_count=_count(
            sum(1 for row in rows if _has_reason_prefix(row, "schedule_signal_") and not _has_reason(row, "schedule_signal_clear")),
        ),
        conflict_count=_count(
            sum(1 for row in rows if _has_reason_prefix(row, "conflict_signal_")),
        ),
        average_research_priority_score=_mean(
            tuple(row.research_priority_score for row in rows),
        ),
        max_research_priority_score=_max_decimal(
            tuple(row.research_priority_score for row in rows),
        ),
        average_information_age_seconds=_mean(
            tuple(row.information_age_seconds for row in rows),
        ),
        status=_rollup_status(tuple(row.status for row in rows)),
        reason_codes=_rollup_reason_codes(rows),
        reason_code_counts=_reason_code_counts(rows),
        rows=rows,
    )


def research_sports_match_signal_matrix_payload(
    report: ResearchSportsMatchSignalMatrixReport,
) -> dict[str, Any]:
    if type(report) is not ResearchSportsMatchSignalMatrixReport:
        raise ValueError("report must be a ResearchSportsMatchSignalMatrixReport")
    _require_payload_safe_value("report", report)
    _reject_unsafe_public_payload("report", report)
    payload = _json_ready(report)
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    _require_hard_flags("payload", _DictFlags(payload))
    _reject_unsafe_public_payload("payload", payload)
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


def _build_row(
    observation: ResearchSportsMatchSignalMatrixObservation,
    *,
    config: ResearchSportsMatchSignalMatrixConfig,
    generated_at: datetime,
) -> ResearchSportsMatchSignalMatrixRow:
    information_age_seconds = _information_age_seconds(observation.observed_at, generated_at)
    freshness_score = _freshness_score(information_age_seconds, config)
    research_priority_score = _research_priority_score(
        observation,
        freshness_score=freshness_score,
        config=config,
    )
    hard_flag = _hard_flag(
        observation,
        information_age_seconds=information_age_seconds,
        config=config,
    )
    status = _row_status(
        observation,
        information_age_seconds=information_age_seconds,
        research_priority_score=research_priority_score,
        hard_flag=hard_flag,
        config=config,
    )
    reason_codes = _row_reason_codes(
        observation,
        information_age_seconds=information_age_seconds,
        status=status,
        config=config,
    )
    return ResearchSportsMatchSignalMatrixRow(
        match_key=observation.match_key,
        league=observation.league,
        team_label=observation.team_label,
        opponent_label=observation.opponent_label,
        team_side=observation.team_side,
        observed_at=observation.observed_at,
        information_age_seconds=information_age_seconds,
        team_form_score=observation.team_form_score,
        schedule_stress_score=observation.schedule_stress_score,
        injury_impact_score=observation.injury_impact_score,
        signal_conflict_ratio=observation.signal_conflict_ratio,
        supporting_signal_count=observation.supporting_signal_count,
        freshness_score=freshness_score,
        research_priority_score=research_priority_score,
        status=status,
        public_status=status,
        hard_flag=hard_flag,
        reason_codes=reason_codes,
    )


def _research_priority_score(
    observation: ResearchSportsMatchSignalMatrixObservation,
    *,
    freshness_score: Decimal,
    config: ResearchSportsMatchSignalMatrixConfig,
) -> Decimal:
    form_gap = _quantize(ONE - observation.team_form_score)
    freshness_gap = _quantize(ONE - freshness_score)
    support_credit = _quantize(
        min(observation.supporting_signal_count, MAX_SUPPORT_CREDIT_SIGNALS)
        * SUPPORT_CREDIT_PER_SIGNAL,
    )
    weighted_score = _quantize(
        form_gap * config.form_weight
        + observation.schedule_stress_score * config.schedule_weight
        + observation.injury_impact_score * config.injury_weight
        + freshness_gap * config.freshness_weight
        + observation.signal_conflict_ratio * config.conflict_weight
        - support_credit,
    )
    return max(weighted_score, ZERO)


def _freshness_score(
    information_age_seconds: Decimal,
    config: ResearchSportsMatchSignalMatrixConfig,
) -> Decimal:
    if information_age_seconds <= config.fresh_information_max_age_seconds:
        return ONE
    if information_age_seconds >= config.stale_information_block_age_seconds:
        return ZERO
    stale_range = _quantize(
        config.stale_information_block_age_seconds
        - config.fresh_information_max_age_seconds,
    )
    stale_delta = _quantize(
        information_age_seconds - config.fresh_information_max_age_seconds,
    )
    return _quantize(ONE - stale_delta / stale_range)


def _hard_flag(
    observation: ResearchSportsMatchSignalMatrixObservation,
    *,
    information_age_seconds: Decimal,
    config: ResearchSportsMatchSignalMatrixConfig,
) -> bool:
    return (
        observation.schedule_stress_score >= config.schedule_stress_block
        or observation.injury_impact_score >= config.injury_impact_block
        or observation.signal_conflict_ratio >= config.conflict_block
        or information_age_seconds >= config.stale_information_block_age_seconds
    )


def _row_status(
    observation: ResearchSportsMatchSignalMatrixObservation,
    *,
    information_age_seconds: Decimal,
    research_priority_score: Decimal,
    hard_flag: bool,
    config: ResearchSportsMatchSignalMatrixConfig,
) -> str:
    if hard_flag or research_priority_score >= config.block_priority_threshold:
        return "block"
    if (
        research_priority_score >= config.watch_priority_threshold
        or observation.schedule_stress_score >= config.schedule_stress_watch
        or observation.injury_impact_score >= config.injury_impact_watch
        or observation.signal_conflict_ratio >= config.conflict_watch
        or information_age_seconds > config.fresh_information_max_age_seconds
    ):
        return "watch"
    return "pass"


def _row_reason_codes(
    observation: ResearchSportsMatchSignalMatrixObservation,
    *,
    information_age_seconds: Decimal,
    status: str,
    config: ResearchSportsMatchSignalMatrixConfig,
) -> tuple[str, ...]:
    reason_codes = list(observation.reason_codes)
    if information_age_seconds >= config.stale_information_block_age_seconds:
        reason_codes.append("information_age_block")
    elif information_age_seconds > config.fresh_information_max_age_seconds:
        reason_codes.append("information_age_watch")
    else:
        reason_codes.append("fresh_information")
    if observation.schedule_stress_score >= config.schedule_stress_block:
        reason_codes.append("schedule_signal_block")
    elif observation.schedule_stress_score >= config.schedule_stress_watch:
        reason_codes.append("schedule_signal_watch")
    else:
        reason_codes.append("schedule_signal_clear")
    if observation.injury_impact_score >= config.injury_impact_block:
        reason_codes.append("injury_signal_block")
    elif observation.injury_impact_score >= config.injury_impact_watch:
        reason_codes.append("injury_signal_watch")
    else:
        reason_codes.append("injury_signal_clear")
    if observation.signal_conflict_ratio >= config.conflict_block:
        reason_codes.append("conflict_signal_block")
    elif observation.signal_conflict_ratio >= config.conflict_watch:
        reason_codes.append("conflict_signal_watch")
    reason_codes.append(f"sports_match_signal_matrix_{status}")
    return _normalize_reason_codes(tuple(sorted(set(reason_codes))))


def _information_age_seconds(observed_at: datetime, generated_at: datetime) -> Decimal:
    seconds = Decimal(str((generated_at - _as_utc("observed_at", observed_at)).total_seconds()))
    age_seconds = _quantize(seconds)
    if age_seconds < ZERO:
        raise ValueError("observed_at must not be after generated_at")
    return age_seconds


def _normalize_inputs(
    observations: Iterable[ResearchSportsMatchSignalMatrixObservation],
) -> tuple[ResearchSportsMatchSignalMatrixObservation, ...]:
    if isinstance(observations, (str, bytes)):
        raise ValueError("observations must be an iterable")
    try:
        rows = tuple(observations)
    except TypeError as exc:
        raise ValueError("observations must be an iterable") from exc
    seen_keys: set[str] = set()
    for row in rows:
        if type(row) is not ResearchSportsMatchSignalMatrixObservation:
            raise ValueError(
                "observations must contain ResearchSportsMatchSignalMatrixObservation values",
            )
        _require_hard_flags("observation", row)
        if row.match_key in seen_keys:
            raise ValueError("observations must not contain duplicate match_key values")
        seen_keys.add(row.match_key)
    return rows


def _normalize_rows(
    rows: Iterable[ResearchSportsMatchSignalMatrixRow],
) -> tuple[ResearchSportsMatchSignalMatrixRow, ...]:
    if isinstance(rows, (str, bytes)):
        raise ValueError("rows must be an iterable")
    try:
        values = tuple(rows)
    except TypeError as exc:
        raise ValueError("rows must be an iterable") from exc
    seen_keys: set[str] = set()
    for row in values:
        if type(row) is not ResearchSportsMatchSignalMatrixRow:
            raise ValueError(
                "rows must contain ResearchSportsMatchSignalMatrixRow values",
            )
        _require_hard_flags("row", row)
        if row.match_key in seen_keys:
            raise ValueError("rows must not contain duplicate match_key values")
        seen_keys.add(row.match_key)
    if values != tuple(sorted(values, key=_row_sort_key)):
        raise ValueError("rows must use canonical sequence")
    return values


def _normalize_reason_code_counts(
    rows: Iterable[ResearchSportsMatchSignalMatrixReasonCodeCount],
) -> tuple[ResearchSportsMatchSignalMatrixReasonCodeCount, ...]:
    if isinstance(rows, (str, bytes)):
        raise ValueError("reason_code_counts must be an iterable")
    try:
        values = tuple(rows)
    except TypeError as exc:
        raise ValueError("reason_code_counts must be an iterable") from exc
    seen_codes: set[str] = set()
    for row in values:
        if type(row) is not ResearchSportsMatchSignalMatrixReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "ResearchSportsMatchSignalMatrixReasonCodeCount values",
            )
        if row.reason_code in seen_codes:
            raise ValueError("reason_code_counts must not contain duplicate reason_code values")
        seen_codes.add(row.reason_code)
    if values != tuple(sorted(values, key=lambda item: (-item.count, item.reason_code))):
        raise ValueError("reason_code_counts must be sorted by count then reason_code")
    return values


def _row_sort_key(row: ResearchSportsMatchSignalMatrixRow) -> tuple[Decimal, Decimal, str, str]:
    return (
        -STATUS_WEIGHT[row.status],
        -row.research_priority_score,
        row.match_key,
        row.team_label,
    )


def _status_count(
    rows: tuple[ResearchSportsMatchSignalMatrixRow, ...],
    status: str,
) -> Decimal:
    return _count(sum(1 for row in rows if row.status == status))


def _rollup_status(statuses: tuple[str, ...]) -> str:
    if not statuses:
        return "block"
    if "block" in statuses:
        return "block"
    if "watch" in statuses:
        return "watch"
    return "pass"


def _rollup_reason_codes(
    rows: tuple[ResearchSportsMatchSignalMatrixRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return (NO_INPUTS_REASON,)
    status = _rollup_status(tuple(row.status for row in rows))
    reason_codes = [f"sports_match_signal_matrix_{status}"]
    row_reason_codes = frozenset(
        reason_code
        for row in rows
        for reason_code in row.reason_codes
    )
    for reason_code in (
        "information_age_block",
        "information_age_watch",
        "schedule_signal_block",
        "schedule_signal_watch",
        "injury_signal_block",
        "injury_signal_watch",
        "conflict_signal_block",
        "conflict_signal_watch",
    ):
        if reason_code in row_reason_codes:
            reason_codes.append(reason_code)
    return tuple(reason_codes)


def _reason_code_counts(
    rows: tuple[ResearchSportsMatchSignalMatrixRow, ...],
) -> tuple[ResearchSportsMatchSignalMatrixReasonCodeCount, ...]:
    if not rows:
        return (
            ResearchSportsMatchSignalMatrixReasonCodeCount(
                reason_code=NO_INPUTS_REASON,
                count=COUNT_QUANTUM,
            ),
        )
    counter: Counter[str] = Counter()
    for row in rows:
        counter.update(row.reason_codes)
    return tuple(
        ResearchSportsMatchSignalMatrixReasonCodeCount(
            reason_code=reason_code,
            count=_count(count),
        )
        for reason_code, count in sorted(counter.items(), key=lambda item: (-item[1], item[0]))
    )


def _validate_report(report: ResearchSportsMatchSignalMatrixReport) -> None:
    rows = report.rows
    if report.subject_count != _count(len(rows)):
        raise ValueError("subject_count must match rows")
    if report.pass_count != _status_count(rows, "pass"):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _status_count(rows, "watch"):
        raise ValueError("watch_count must match rows")
    if report.block_count != _status_count(rows, "block"):
        raise ValueError("block_count must match rows")
    if report.hard_flag_count != _count(sum(1 for row in rows if row.hard_flag)):
        raise ValueError("hard_flag_count must match rows")
    if report.stale_information_count != _count(
        sum(1 for row in rows if _has_reason_prefix(row, "information_age_")),
    ):
        raise ValueError("stale_information_count must match rows")
    if report.injury_concern_count != _count(
        sum(
            1
            for row in rows
            if _has_reason_prefix(row, "injury_signal_")
            and not _has_reason(row, "injury_signal_clear")
        ),
    ):
        raise ValueError("injury_concern_count must match rows")
    if report.schedule_congestion_count != _count(
        sum(
            1
            for row in rows
            if _has_reason_prefix(row, "schedule_signal_")
            and not _has_reason(row, "schedule_signal_clear")
        ),
    ):
        raise ValueError("schedule_congestion_count must match rows")
    if report.conflict_count != _count(
        sum(1 for row in rows if _has_reason_prefix(row, "conflict_signal_")),
    ):
        raise ValueError("conflict_count must match rows")
    if report.average_research_priority_score != _mean(
        tuple(row.research_priority_score for row in rows),
    ):
        raise ValueError("average_research_priority_score must match rows")
    if report.max_research_priority_score != _max_decimal(
        tuple(row.research_priority_score for row in rows),
    ):
        raise ValueError("max_research_priority_score must match rows")
    if report.average_information_age_seconds != _mean(
        tuple(row.information_age_seconds for row in rows),
    ):
        raise ValueError("average_information_age_seconds must match rows")
    if report.status != _rollup_status(tuple(row.status for row in rows)):
        raise ValueError("status must match rows")
    if report.reason_codes != _rollup_reason_codes(rows):
        raise ValueError("reason_codes must match rows")
    if report.reason_code_counts != _reason_code_counts(rows):
        raise ValueError("reason_code_counts must match rows")


def _has_reason(row: ResearchSportsMatchSignalMatrixRow, reason_code: str) -> bool:
    return reason_code in row.reason_codes


def _has_reason_prefix(row: ResearchSportsMatchSignalMatrixRow, reason_prefix: str) -> bool:
    return any(reason_code.startswith(reason_prefix) for reason_code in row.reason_codes)


def _require_payload_safe_value(label: str, value: object) -> None:
    if is_dataclass(value) and not isinstance(value, type):
        if type(value) not in _PUBLIC_DATACLASS_TYPES:
            raise ValueError(f"{label} contains unsupported dataclass")
        for field in fields(value):
            _require_payload_safe_value(f"{label}.{field.name}", getattr(value, field.name))
        _rebuild_public_dataclass(label, value)
        return
    if type(value) is Decimal:
        _require_six_decimal_decimal(label, value)
        return
    if type(value) is datetime:
        _require_utc_datetime(label, value)
        return
    if type(value) is tuple:
        for index, item in enumerate(value):
            _require_payload_safe_value(f"{label}[{index}]", item)
        return
    if value is None or type(value) in (bool, str):
        if type(value) is str:
            _require_public_string(label, value)
        return
    if type(value) in (int, float) or isinstance(value, (list, dict, set)):
        raise ValueError(f"{label} must come from public dataclass fields")
    raise ValueError(f"{label} contains unsupported value")


def _rebuild_public_dataclass(label: str, value: object) -> None:
    kwargs = {field.name: getattr(value, field.name) for field in fields(value)}
    try:
        type(value)(**kwargs)
    except Exception as exc:
        raise ValueError(f"{label} failed payload revalidation: {exc}") from exc


def _json_ready(value: Any) -> Any:
    if type(value) is Decimal:
        _require_six_decimal_decimal("JSON Decimal value", value)
        return format(value, "f")
    if type(value) is datetime:
        _require_utc_datetime("JSON datetime value", value)
        return value.isoformat()
    if is_dataclass(value) and not isinstance(value, type):
        _require_payload_safe_value("JSON value", value)
        return {
            field.name: _json_ready(getattr(value, field.name))
            for field in fields(value)
        }
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
    if type(value) is tuple:
        return [_json_ready(item) for item in value]
    if isinstance(value, (list, dict, set)):
        raise ValueError("JSON value must come from public dataclass fields")
    raise ValueError("value is not JSON serializable")


def _row_digest(row: ResearchSportsMatchSignalMatrixRow) -> str:
    return _digest_from_public_value(row)


def _report_digest(report: ResearchSportsMatchSignalMatrixReport) -> str:
    return _digest_from_public_value(report)


def _digest_from_public_value(value: object) -> str:
    canonical_payload = _digest_ready(value)
    encoded = json.dumps(canonical_payload, sort_keys=True, separators=(",", ":"))
    return f"{DIGEST_PREFIX}{sha256(encoded.encode('utf-8')).hexdigest()}"


def _digest_ready(value: object) -> object:
    if type(value) is Decimal:
        _require_six_decimal_decimal("digest Decimal value", value)
        return format(value, "f")
    if type(value) is datetime:
        _require_utc_datetime("digest datetime value", value)
        return value.isoformat()
    if is_dataclass(value) and not isinstance(value, type):
        return {
            field.name: _digest_ready(getattr(value, field.name))
            for field in fields(value)
            if field.name != "digest"
        }
    if type(value) is tuple:
        return [_digest_ready(item) for item in value]
    if value is None or type(value) in (bool, str):
        return value
    raise ValueError("value is not digest serializable")


def _reject_unsafe_public_payload(label: str, value: object, path: str = "") -> None:
    if is_dataclass(value) and not isinstance(value, type):
        if type(value) not in _PUBLIC_DATACLASS_TYPES:
            raise ValueError(f"{path or label} contains unsupported dataclass")
        for field in fields(value):
            item_path = field.name if not path else f"{path}.{field.name}"
            _reject_unsafe_public_payload(label, getattr(value, field.name), item_path)
        return
    if type(value) is str:
        if _has_unsafe_fragment(value):
            raise ValueError(f"{path or label} has unsafe or sensitive value")
        return
    if type(value) is Decimal:
        _require_six_decimal_decimal(path or label, value)
        return
    if type(value) is datetime:
        _require_utc_datetime(path or label, value)
        return
    if value is None or type(value) is bool:
        return
    if isinstance(value, float):
        raise ValueError("JSON value must not be a float")
    if type(value) is int:
        raise ValueError(f"{path or label} must use Decimal values")
    if type(value) is dict:
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            item_path = key if not path else f"{path}.{key}"
            if _has_unsafe_fragment(key):
                raise ValueError(f"unsafe or sensitive field in {label}: {key}")
            if key in PHASE_FLAG_FIELDS and item is not True:
                raise ValueError(f"{item_path} must be True")
            _reject_unsafe_public_payload(label, item, item_path)
        return
    if type(value) in (list, tuple):
        for index, item in enumerate(value):
            item_path = f"{path}[{index}]" if path else f"{label}[{index}]"
            _reject_unsafe_public_payload(label, item, item_path)
        return
    raise ValueError("value is not JSON serializable")


def _unsafe_fragments() -> tuple[str, ...]:
    return (
        "raw" + "_" + "candidate",
        "raw" + " " + "candidate",
        "candidate" + "_" + "id",
        "candidate" + " " + "id",
        "market" + "_" + "id",
        "market" + " " + "id",
        "market" + "_" + "slug",
        "market" + " " + "slug",
        "ques" + "tion",
        "source" + "_" + "ref",
        "source" + " " + "ref",
        "source" + "_" + "url",
        "source" + " " + "url",
        "source" + "_" + "text",
        "source" + " " + "text",
        "d" + "sn",
        "tab" + "le",
        "tok" + "en",
        "wal" + "let",
        "au" + "th",
        "or" + "der",
        "tr" + "ade",
        "pos" + "ition",
        "b" + "uy",
        "se" + "ll",
        "recom" + "mendation",
        "://",
        "www.",
    )


def _has_unsafe_fragment(value: str) -> bool:
    normalized = value.lower()
    return any(fragment in normalized for fragment in _unsafe_fragments())


def _as_utc(field_name: str, value: datetime) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_utc_datetime(field_name: str, value: datetime) -> None:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is not UTC or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be UTC-aware")


def _normalize_decimal(field_name: str, value: Decimal) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return _quantize(value)


def _normalize_nonnegative_decimal(field_name: str, value: Decimal) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _normalize_positive_decimal(field_name: str, value: Decimal) -> Decimal:
    normalized = _normalize_nonnegative_decimal(field_name, value)
    if normalized <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _normalize_ratio_decimal(field_name: str, value: Decimal) -> Decimal:
    normalized = _normalize_nonnegative_decimal(field_name, value)
    if normalized > ONE:
        raise ValueError(f"{field_name} must be a ratio")
    return normalized


def _require_six_decimal_decimal(field_name: str, value: Decimal) -> None:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    if value.as_tuple().exponent != -6:
        raise ValueError(f"{field_name} must use six decimal places")


def _normalize_reason_codes(reason_codes: Iterable[str]) -> tuple[str, ...]:
    if isinstance(reason_codes, (str, bytes)):
        raise ValueError("reason_codes must be an iterable")
    try:
        values = tuple(reason_codes)
    except TypeError as exc:
        raise ValueError("reason_codes must be an iterable") from exc
    if not values:
        raise ValueError("reason_codes must not be empty")
    for reason_code in values:
        _require_public_string("reason_codes", reason_code)
    normalized = tuple(sorted(values))
    if values != normalized:
        raise ValueError("reason_codes must use canonical sequence")
    if len(set(normalized)) != len(normalized):
        raise ValueError("reason_codes must not contain duplicates")
    return normalized


def _normalize_report_reason_codes(reason_codes: Iterable[str]) -> tuple[str, ...]:
    if isinstance(reason_codes, (str, bytes)):
        raise ValueError("reason_codes must be an iterable")
    try:
        values = tuple(reason_codes)
    except TypeError as exc:
        raise ValueError("reason_codes must be an iterable") from exc
    if not values:
        raise ValueError("reason_codes must not be empty")
    for reason_code in values:
        _require_public_string("reason_codes", reason_code)
    if len(set(values)) != len(values):
        raise ValueError("reason_codes must not contain duplicates")
    return values


def _count(value: int) -> Decimal:
    return Decimal(value).quantize(COUNT_QUANTUM)


def _mean(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return ZERO
    return _quantize(sum(values, ZERO) / _count(len(values)))


def _max_decimal(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return ZERO
    return max(values)


def _quantize(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(QUANTUM)


def _require_at_most(field_name: str, lower: Decimal, upper: Decimal) -> None:
    if lower > upper:
        raise ValueError(f"{field_name} must be less than or equal to paired threshold")


def _require_public_string(field_name: str, value: str) -> None:
    if type(value) is not str or not value:
        raise ValueError(f"{field_name} must be a non-empty string")
    if value.strip() != value:
        raise ValueError(f"{field_name} must be canonical")
    if _has_unsafe_fragment(value):
        raise ValueError(f"{field_name} has unsafe or sensitive value")


def _require_status(field_name: str, value: str) -> None:
    if value not in STATUSES:
        raise ValueError(f"{field_name} must be pass, watch, or block")


def _require_member(field_name: str, value: str, members: tuple[str, ...]) -> None:
    if value not in members:
        raise ValueError(f"{field_name} must be a known value")


def _require_digest(field_name: str, value: str) -> None:
    _require_public_string(field_name, value)
    if not value.startswith(DIGEST_PREFIX) or len(value) != len(DIGEST_PREFIX) + 64:
        raise ValueError(f"{field_name} must use the digest format")


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in PHASE_FLAG_FIELDS:
        if getattr(value, field_name, None) is not True:
            raise ValueError(f"{field_name} must be True for {label}")
