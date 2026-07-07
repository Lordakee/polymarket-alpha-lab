"""Pure specialist playbook readiness score report."""

from __future__ import annotations

from dataclasses import asdict, dataclass, is_dataclass
from decimal import Decimal, ROUND_HALF_UP
import hashlib
import json

from polymarket_alpha_lab.strategy_team_taxonomy import (
    STRATEGY_TEAM_IDS,
    require_strategy_team_id,
)
from polymarket_alpha_lab.team_paper_guard import require_paper_only_flags


DEFAULT_TEAM_MEMORY_SPECIALIST_PLAYBOOK_SCORE_CONFIG_VERSION = (
    "team-memory-specialist-playbook-score-v1"
)

_ZERO = Decimal("0.000000")
_HALF = Decimal("0.500000")
_ONE = Decimal("1.000000")
_QUANT = Decimal("0.000001")
_ROW_STATUSES = frozenset(("memory_ready", "watch", "block"))
_REPORT_STATUSES = frozenset(("empty", "memory_ready", "watch", "block"))
_TEAM_SORT_INDEX = {
    team_id: index for index, team_id in enumerate(STRATEGY_TEAM_IDS)
}

_READY_REASON = "team_memory_specialist_playbook_ready"
_SETTLED_SAMPLE_REASON = (
    "team_memory_specialist_settled_sample_count_insufficient"
)
_RECENT_SAMPLE_REASON = "team_memory_specialist_recent_sample_count_insufficient"
_CALIBRATION_REASON = "team_memory_specialist_calibration_error_high"
_SOURCE_RELIABILITY_REASON = "team_memory_specialist_source_reliability_low"
_STALE_PLAYBOOK_REASON = "team_memory_specialist_playbook_revision_stale"
_UNRESOLVED_FAILURE_REASON = (
    "team_memory_specialist_unresolved_failures_present"
)
_ROW_REASON_ORDER = (
    _SETTLED_SAMPLE_REASON,
    _RECENT_SAMPLE_REASON,
    _CALIBRATION_REASON,
    _SOURCE_RELIABILITY_REASON,
    _STALE_PLAYBOOK_REASON,
    _UNRESOLVED_FAILURE_REASON,
    _READY_REASON,
)
_ROW_REASON_CODES = frozenset(_ROW_REASON_ORDER)
_PUBLIC_CLASS_NAMES = frozenset(
    (
        "TeamMemorySpecialistPlaybookScoreConfig",
        "TeamMemorySpecialistPlaybookScoreObservation",
        "TeamMemorySpecialistPlaybookScoreReasonCodeCount",
        "TeamMemorySpecialistPlaybookScoreReport",
        "TeamMemorySpecialistPlaybookScoreRow",
    ),
)
_UNSAFE_TERM_PARTS = (
    ("li", "ve"),
    ("au", "th"),
    ("wal", "let"),
    ("acco", "unt"),
    ("private", "_key"),
    ("or", "der"),
    ("cancel",),
    ("replace",),
    ("sig", "ning"),
    ("ex", "change"),
    ("muta", "tion"),
    ("net", "work"),
    ("data", "base"),
    ("per", "sist"),
    ("b", "uy"),
    ("se", "ll"),
    ("tra", "de"),
)
_UNSAFE_TERMS = tuple("".join(parts) for parts in _UNSAFE_TERM_PARTS)


class _FinalPublicDataclass:
    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls.__module__ != __name__ or cls.__name__ not in _PUBLIC_CLASS_NAMES:
            raise TypeError(f"{cls.__name__} does not support subclassing")


@dataclass(frozen=True)
class TeamMemorySpecialistPlaybookScoreConfig(_FinalPublicDataclass):
    config_version: str = DEFAULT_TEAM_MEMORY_SPECIALIST_PLAYBOOK_SCORE_CONFIG_VERSION
    min_memory_ready_settled_sample_count: Decimal = Decimal("50.000000")
    min_memory_ready_recent_sample_count: Decimal = Decimal("10.000000")
    max_memory_ready_calibration_error: Decimal = Decimal("0.050000")
    max_watch_calibration_error: Decimal = Decimal("0.150000")
    min_memory_ready_source_reliability_score: Decimal = Decimal("0.800000")
    min_watch_source_reliability_score: Decimal = Decimal("0.600000")
    max_memory_ready_playbook_revision_age_days: Decimal = Decimal("30.000000")
    max_watch_playbook_revision_age_days: Decimal = Decimal("90.000000")
    max_unresolved_failure_count: Decimal = Decimal("0.000000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, TeamMemorySpecialistPlaybookScoreConfig, "config")
        object.__setattr__(
            self,
            "config_version",
            _require_public_string("config_version", self.config_version),
        )
        for field_name in (
            "min_memory_ready_settled_sample_count",
            "min_memory_ready_recent_sample_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_positive_count(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "max_memory_ready_calibration_error",
            "max_watch_calibration_error",
            "min_memory_ready_source_reliability_score",
            "min_watch_source_reliability_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "max_memory_ready_playbook_revision_age_days",
            "max_watch_playbook_revision_age_days",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_positive_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "max_unresolved_failure_count",
            _normalize_count(
                "max_unresolved_failure_count",
                self.max_unresolved_failure_count,
            ),
        )
        _validate_config(self)
        require_paper_only_flags("specialist playbook score config", self)
        _reject_unsafe_public_payload("specialist playbook score config", asdict(self))


@dataclass(frozen=True)
class TeamMemorySpecialistPlaybookScoreObservation(_FinalPublicDataclass):
    team_id: str
    settled_sample_count: Decimal
    recent_sample_count: Decimal
    calibration_error: Decimal
    source_reliability_score: Decimal
    playbook_revision_age_days: Decimal
    unresolved_failure_count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            TeamMemorySpecialistPlaybookScoreObservation,
            "observation",
        )
        object.__setattr__(
            self,
            "team_id",
            require_strategy_team_id("team_id", self.team_id),
        )
        for field_name in (
            "settled_sample_count",
            "recent_sample_count",
            "unresolved_failure_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_count(field_name, getattr(self, field_name)),
            )
        for field_name in ("calibration_error", "source_reliability_score"):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "playbook_revision_age_days",
            _normalize_nonnegative_decimal(
                "playbook_revision_age_days",
                self.playbook_revision_age_days,
            ),
        )
        if self.recent_sample_count > self.settled_sample_count:
            raise ValueError("recent_sample_count must not exceed settled_sample_count")
        require_paper_only_flags("specialist playbook score observation", self)
        _reject_unsafe_public_payload(
            "specialist playbook score observation",
            asdict(self),
        )


@dataclass(frozen=True)
class TeamMemorySpecialistPlaybookScoreRow(_FinalPublicDataclass):
    team_id: str
    settled_sample_count: Decimal
    recent_sample_count: Decimal
    calibration_error: Decimal
    source_reliability_score: Decimal
    playbook_revision_age_days: Decimal
    unresolved_failure_count: Decimal
    settled_sample_score: Decimal
    recent_sample_score: Decimal
    calibration_score: Decimal
    revision_freshness_score: Decimal
    playbook_readiness_score: Decimal
    memory_status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, TeamMemorySpecialistPlaybookScoreRow, "row")
        object.__setattr__(
            self,
            "team_id",
            require_strategy_team_id("team_id", self.team_id),
        )
        for field_name in (
            "settled_sample_count",
            "recent_sample_count",
            "unresolved_failure_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_count(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "calibration_error",
            "source_reliability_score",
            "settled_sample_score",
            "recent_sample_score",
            "calibration_score",
            "revision_freshness_score",
            "playbook_readiness_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "playbook_revision_age_days",
            _normalize_nonnegative_decimal(
                "playbook_revision_age_days",
                self.playbook_revision_age_days,
            ),
        )
        _require_member("memory_status", self.memory_status, _ROW_STATUSES)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(
                self.reason_codes,
                allow_empty=False,
                order="row",
            ),
        )
        if self.recent_sample_count > self.settled_sample_count:
            raise ValueError("recent_sample_count must not exceed settled_sample_count")
        _validate_row(self)
        require_paper_only_flags("specialist playbook score row", self)
        _reject_unsafe_public_payload("specialist playbook score row", asdict(self))


@dataclass(frozen=True)
class TeamMemorySpecialistPlaybookScoreReasonCodeCount(_FinalPublicDataclass):
    reason_code: str
    count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            TeamMemorySpecialistPlaybookScoreReasonCodeCount,
            "reason_count",
        )
        _require_reason_code(self.reason_code)
        object.__setattr__(self, "count", _normalize_count("count", self.count))
        require_paper_only_flags("specialist playbook score reason count", self)
        _reject_unsafe_public_payload(
            "specialist playbook score reason count",
            asdict(self),
        )


@dataclass(frozen=True)
class TeamMemorySpecialistPlaybookScoreReport(_FinalPublicDataclass):
    config_version: str
    team_count: Decimal
    memory_ready_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    average_playbook_readiness_score: Decimal
    min_playbook_readiness_score: Decimal
    report_status: str
    reason_codes: tuple[str, ...]
    reason_code_counts: tuple[TeamMemorySpecialistPlaybookScoreReasonCodeCount, ...]
    rows: tuple[TeamMemorySpecialistPlaybookScoreRow, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, TeamMemorySpecialistPlaybookScoreReport, "report")
        object.__setattr__(
            self,
            "config_version",
            _require_public_string("config_version", self.config_version),
        )
        for field_name in (
            "team_count",
            "memory_ready_count",
            "watch_count",
            "block_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_count(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "average_playbook_readiness_score",
            "min_playbook_readiness_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        _require_member("report_status", self.report_status, _REPORT_STATUSES)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(
                self.reason_codes,
                allow_empty=True,
                order="sorted",
            ),
        )
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        _validate_report(self)
        require_paper_only_flags("specialist playbook score report", self)
        if self.derived_validation_digest == "":
            object.__setattr__(self, "derived_validation_digest", _report_digest(self))
        else:
            object.__setattr__(
                self,
                "derived_validation_digest",
                _normalize_digest(self.derived_validation_digest),
            )
        _validate_report_digest(self)
        _reject_unsafe_public_payload("specialist playbook score report", asdict(self))

    @property
    def payload(self) -> dict[str, object]:
        payload = _json_ready_no_numbers(asdict(self))
        if type(payload) is not dict:
            raise ValueError("payload must be a dict")
        _reject_unsafe_public_payload("specialist playbook score report payload", payload)
        return payload


def build_team_memory_specialist_playbook_score_report(
    observations: tuple[TeamMemorySpecialistPlaybookScoreObservation, ...]
    | list[TeamMemorySpecialistPlaybookScoreObservation],
    *,
    config: TeamMemorySpecialistPlaybookScoreConfig,
) -> TeamMemorySpecialistPlaybookScoreReport:
    if type(config) is not TeamMemorySpecialistPlaybookScoreConfig:
        raise ValueError(
            "config must be a TeamMemorySpecialistPlaybookScoreConfig",
        )
    require_paper_only_flags("specialist playbook score config", config)
    _reject_unsafe_public_payload("specialist playbook score config", asdict(config))
    normalized = _normalize_observations(observations)
    rows = tuple(
        _row_for_observation(observation, config=config)
        for observation in sorted(normalized, key=_observation_sort_key)
    )
    reason_code_counts = _reason_code_counts(rows)
    readiness_scores = tuple(row.playbook_readiness_score for row in rows)
    return TeamMemorySpecialistPlaybookScoreReport(
        config_version=config.config_version,
        team_count=_decimal_count(len(rows)),
        memory_ready_count=_status_count(rows, "memory_ready"),
        watch_count=_status_count(rows, "watch"),
        block_count=_status_count(rows, "block"),
        average_playbook_readiness_score=_average(readiness_scores),
        min_playbook_readiness_score=min(readiness_scores) if readiness_scores else _ZERO,
        report_status=_report_status(rows),
        reason_codes=tuple(count.reason_code for count in reason_code_counts),
        reason_code_counts=reason_code_counts,
        rows=rows,
    )


def _row_for_observation(
    observation: TeamMemorySpecialistPlaybookScoreObservation,
    *,
    config: TeamMemorySpecialistPlaybookScoreConfig,
) -> TeamMemorySpecialistPlaybookScoreRow:
    settled_sample_score = _sample_score(
        observation.settled_sample_count,
        config.min_memory_ready_settled_sample_count,
    )
    recent_sample_score = _sample_score(
        observation.recent_sample_count,
        config.min_memory_ready_recent_sample_count,
    )
    calibration_score = _clamp_ratio(_ONE - observation.calibration_error)
    revision_freshness_score = _revision_freshness_score(
        observation.playbook_revision_age_days,
        config,
    )
    unresolved_failure_score = (
        _ONE if observation.unresolved_failure_count == _ZERO else _ZERO
    )
    playbook_readiness_score = _clamp_ratio(
        min(
            settled_sample_score,
            recent_sample_score,
            calibration_score,
            observation.source_reliability_score,
            revision_freshness_score,
            unresolved_failure_score,
        ),
    )
    reason_codes = _row_reason_codes(observation, config)
    return TeamMemorySpecialistPlaybookScoreRow(
        team_id=observation.team_id,
        settled_sample_count=observation.settled_sample_count,
        recent_sample_count=observation.recent_sample_count,
        calibration_error=observation.calibration_error,
        source_reliability_score=observation.source_reliability_score,
        playbook_revision_age_days=observation.playbook_revision_age_days,
        unresolved_failure_count=observation.unresolved_failure_count,
        settled_sample_score=settled_sample_score,
        recent_sample_score=recent_sample_score,
        calibration_score=calibration_score,
        revision_freshness_score=revision_freshness_score,
        playbook_readiness_score=playbook_readiness_score,
        memory_status=_row_status(observation, config, reason_codes),
        reason_codes=reason_codes,
    )


def _row_reason_codes(
    observation: TeamMemorySpecialistPlaybookScoreObservation,
    config: TeamMemorySpecialistPlaybookScoreConfig,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    if observation.settled_sample_count < config.min_memory_ready_settled_sample_count:
        reason_codes.append(_SETTLED_SAMPLE_REASON)
    if observation.recent_sample_count < config.min_memory_ready_recent_sample_count:
        reason_codes.append(_RECENT_SAMPLE_REASON)
    if observation.calibration_error > config.max_memory_ready_calibration_error:
        reason_codes.append(_CALIBRATION_REASON)
    if (
        observation.source_reliability_score
        < config.min_memory_ready_source_reliability_score
    ):
        reason_codes.append(_SOURCE_RELIABILITY_REASON)
    if (
        observation.playbook_revision_age_days
        > config.max_memory_ready_playbook_revision_age_days
    ):
        reason_codes.append(_STALE_PLAYBOOK_REASON)
    if observation.unresolved_failure_count > _ZERO:
        reason_codes.append(_UNRESOLVED_FAILURE_REASON)
    if not reason_codes:
        reason_codes.append(_READY_REASON)
    return tuple(reason_codes)


def _row_status(
    observation: TeamMemorySpecialistPlaybookScoreObservation,
    config: TeamMemorySpecialistPlaybookScoreConfig,
    reason_codes: tuple[str, ...],
) -> str:
    if (
        observation.calibration_error > config.max_watch_calibration_error
        or observation.source_reliability_score
        < config.min_watch_source_reliability_score
        or observation.playbook_revision_age_days
        > config.max_watch_playbook_revision_age_days
        or observation.unresolved_failure_count > config.max_unresolved_failure_count
    ):
        return "block"
    if reason_codes == (_READY_REASON,):
        return "memory_ready"
    return "watch"


def _sample_score(count: Decimal, ready_count: Decimal) -> Decimal:
    return _clamp_ratio(count / ready_count)


def _revision_freshness_score(
    playbook_revision_age_days: Decimal,
    config: TeamMemorySpecialistPlaybookScoreConfig,
) -> Decimal:
    if playbook_revision_age_days <= config.max_memory_ready_playbook_revision_age_days:
        return _ONE
    if playbook_revision_age_days <= config.max_watch_playbook_revision_age_days:
        return _HALF
    return _ZERO


def _normalize_observations(
    observations: tuple[TeamMemorySpecialistPlaybookScoreObservation, ...]
    | list[TeamMemorySpecialistPlaybookScoreObservation],
) -> tuple[TeamMemorySpecialistPlaybookScoreObservation, ...]:
    if type(observations) not in (tuple, list):
        raise ValueError("observations must be a tuple or list")
    normalized = tuple(observations)
    seen: set[str] = set()
    for observation in normalized:
        if type(observation) is not TeamMemorySpecialistPlaybookScoreObservation:
            raise ValueError(
                "observations must contain "
                "TeamMemorySpecialistPlaybookScoreObservation items",
            )
        require_paper_only_flags("specialist playbook score observation", observation)
        if observation.team_id in seen:
            raise ValueError("duplicate team_id")
        seen.add(observation.team_id)
    return normalized


def _validate_config(config: TeamMemorySpecialistPlaybookScoreConfig) -> None:
    if config.max_watch_calibration_error < config.max_memory_ready_calibration_error:
        raise ValueError(
            "max_watch_calibration_error must be >= "
            "max_memory_ready_calibration_error",
        )
    if (
        config.min_watch_source_reliability_score
        > config.min_memory_ready_source_reliability_score
    ):
        raise ValueError(
            "min_watch_source_reliability_score must be <= "
            "min_memory_ready_source_reliability_score",
        )
    if (
        config.max_watch_playbook_revision_age_days
        < config.max_memory_ready_playbook_revision_age_days
    ):
        raise ValueError(
            "max_watch_playbook_revision_age_days must be >= "
            "max_memory_ready_playbook_revision_age_days",
        )


def _validate_row(row: TeamMemorySpecialistPlaybookScoreRow) -> None:
    if row.memory_status == "memory_ready" and row.reason_codes != (_READY_REASON,):
        raise ValueError("memory_ready rows must only carry the ready reason code")
    if row.memory_status != "memory_ready" and _READY_REASON in row.reason_codes:
        raise ValueError("ready reason code is only valid for memory_ready rows")


def _validate_report(report: TeamMemorySpecialistPlaybookScoreReport) -> None:
    if report.team_count != _decimal_count(len(report.rows)):
        raise ValueError("team_count does not match rows")
    if tuple(sorted(report.rows, key=_row_sort_key)) != report.rows:
        raise ValueError("rows must be sorted by canonical team taxonomy")
    if len({row.team_id for row in report.rows}) != len(report.rows):
        raise ValueError("rows contain duplicate team_id")
    expected_counts = {
        "memory_ready_count": _status_count(report.rows, "memory_ready"),
        "watch_count": _status_count(report.rows, "watch"),
        "block_count": _status_count(report.rows, "block"),
    }
    for field_name, expected in expected_counts.items():
        if getattr(report, field_name) != expected:
            raise ValueError(f"{field_name} does not match rows")
    readiness_scores = tuple(row.playbook_readiness_score for row in report.rows)
    if report.average_playbook_readiness_score != _average(readiness_scores):
        raise ValueError("average_playbook_readiness_score does not match rows")
    expected_min_score = min(readiness_scores) if readiness_scores else _ZERO
    if report.min_playbook_readiness_score != expected_min_score:
        raise ValueError("min_playbook_readiness_score does not match rows")
    if report.report_status != _report_status(report.rows):
        raise ValueError("report_status does not match rows")
    if report.reason_code_counts != _reason_code_counts(report.rows):
        raise ValueError("reason_code_counts do not match rows")
    expected_reason_codes = tuple(
        count.reason_code for count in report.reason_code_counts
    )
    if report.reason_codes != expected_reason_codes:
        raise ValueError("reason_codes do not match reason_code_counts")


def _validate_report_digest(
    report: TeamMemorySpecialistPlaybookScoreReport,
) -> None:
    if report.derived_validation_digest != _report_digest(report):
        raise ValueError("derived_validation_digest does not match report payload")


def _report_digest(report: TeamMemorySpecialistPlaybookScoreReport) -> str:
    payload = _json_ready_no_numbers(asdict(report))
    if type(payload) is not dict:
        raise ValueError("report payload must be a dict")
    payload = dict(payload)
    payload["derived_validation_digest"] = ""
    _reject_unsafe_public_payload("specialist playbook score report digest", payload)
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def _reason_code_counts(
    rows: tuple[TeamMemorySpecialistPlaybookScoreRow, ...],
) -> tuple[TeamMemorySpecialistPlaybookScoreReasonCodeCount, ...]:
    counts: dict[str, int] = {}
    for row in rows:
        for reason_code in row.reason_codes:
            counts[reason_code] = counts.get(reason_code, 0) + 1
    return tuple(
        TeamMemorySpecialistPlaybookScoreReasonCodeCount(
            reason_code=reason_code,
            count=_decimal_count(counts[reason_code]),
        )
        for reason_code in sorted(counts)
    )


def _normalize_reason_code_counts(
    value: tuple[TeamMemorySpecialistPlaybookScoreReasonCodeCount, ...]
    | list[TeamMemorySpecialistPlaybookScoreReasonCodeCount],
) -> tuple[TeamMemorySpecialistPlaybookScoreReasonCodeCount, ...]:
    if type(value) not in (tuple, list):
        raise ValueError("reason_code_counts must be a tuple or list")
    counts = tuple(value)
    for count in counts:
        if type(count) is not TeamMemorySpecialistPlaybookScoreReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "TeamMemorySpecialistPlaybookScoreReasonCodeCount items",
            )
        require_paper_only_flags("specialist playbook score reason count", count)
    if tuple(sorted(counts, key=lambda count: count.reason_code)) != counts:
        raise ValueError("reason_code_counts must be sorted by reason_code")
    if len({count.reason_code for count in counts}) != len(counts):
        raise ValueError("reason_code_counts contain duplicates")
    return counts


def _normalize_rows(
    value: tuple[TeamMemorySpecialistPlaybookScoreRow, ...]
    | list[TeamMemorySpecialistPlaybookScoreRow],
) -> tuple[TeamMemorySpecialistPlaybookScoreRow, ...]:
    if type(value) not in (tuple, list):
        raise ValueError("rows must be a tuple or list")
    rows = tuple(value)
    for row in rows:
        if type(row) is not TeamMemorySpecialistPlaybookScoreRow:
            raise ValueError(
                "rows must contain TeamMemorySpecialistPlaybookScoreRow items",
            )
        require_paper_only_flags("specialist playbook score row", row)
    return rows


def _normalize_reason_codes(
    value: tuple[str, ...] | list[str],
    *,
    allow_empty: bool,
    order: str,
) -> tuple[str, ...]:
    if type(value) not in (tuple, list):
        raise ValueError("reason_codes must be a tuple or list")
    reason_codes = tuple(value)
    if not allow_empty and not reason_codes:
        raise ValueError("reason_codes must not be empty")
    for reason_code in reason_codes:
        _require_reason_code(reason_code)
    if len(set(reason_codes)) != len(reason_codes):
        raise ValueError("reason_codes must not contain duplicates")
    if reason_codes == (_READY_REASON,):
        return reason_codes
    if order == "row" and _READY_REASON in reason_codes:
        raise ValueError("ready reason code must not be combined")
    if order == "row":
        expected = tuple(
            reason_code
            for reason_code in _ROW_REASON_ORDER
            if reason_code in reason_codes
        )
    elif order == "sorted":
        expected = tuple(sorted(reason_codes))
    else:
        raise ValueError("reason_codes order must be row or sorted")
    if reason_codes != expected:
        raise ValueError("reason_codes must be in canonical order")
    return reason_codes


def _require_reason_code(value: str) -> None:
    _require_public_string("reason_code", value)
    if value not in _ROW_REASON_CODES:
        raise ValueError(f"unknown reason_code: {value}")


def _require_member(name: str, value: str, allowed: frozenset[str]) -> None:
    _require_public_string(name, value)
    if value not in allowed:
        raise ValueError(f"{name} must be one of {sorted(allowed)}")


def _require_exact_type(value: object, expected_type: type, label: str) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{label} must be exactly {expected_type.__name__}")


def _require_public_string(name: str, value: object) -> str:
    if type(value) is not str or value == "" or value.strip() != value:
        raise ValueError(f"{name} must be a non-empty canonical string")
    return value


def _normalize_digest(value: str) -> str:
    if type(value) is not str or len(value) != 64:
        raise ValueError("derived_validation_digest must be a sha256 hex digest")
    try:
        int(value, 16)
    except ValueError as exc:
        raise ValueError(
            "derived_validation_digest must be a sha256 hex digest",
        ) from exc
    return value.lower()


def _normalize_positive_count(name: str, value: Decimal) -> Decimal:
    normalized = _normalize_count(name, value)
    if normalized <= _ZERO:
        raise ValueError(f"{name} must be positive")
    return normalized


def _normalize_count(name: str, value: Decimal) -> Decimal:
    _require_decimal(name, value)
    if value < _ZERO:
        raise ValueError(f"{name} must be nonnegative")
    if value != value.to_integral_value():
        raise ValueError(f"{name} must be integral")
    return value.quantize(_QUANT, rounding=ROUND_HALF_UP)


def _normalize_positive_decimal(name: str, value: Decimal) -> Decimal:
    normalized = _normalize_decimal(name, value)
    if normalized <= _ZERO:
        raise ValueError(f"{name} must be positive")
    return normalized


def _normalize_nonnegative_decimal(name: str, value: Decimal) -> Decimal:
    normalized = _normalize_decimal(name, value)
    if normalized < _ZERO:
        raise ValueError(f"{name} must be nonnegative")
    return normalized


def _normalize_ratio(name: str, value: Decimal) -> Decimal:
    normalized = _normalize_decimal(name, value)
    if normalized < _ZERO or normalized > _ONE:
        raise ValueError(f"{name} must be between 0 and 1")
    return normalized


def _normalize_decimal(name: str, value: Decimal) -> Decimal:
    _require_decimal(name, value)
    return value.quantize(_QUANT, rounding=ROUND_HALF_UP)


def _require_decimal(name: str, value: Decimal) -> None:
    if type(value) is not Decimal:
        raise ValueError(f"{name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{name} must be finite")


def _clamp_ratio(value: Decimal) -> Decimal:
    normalized = _normalize_decimal("ratio", value)
    if normalized < _ZERO:
        return _ZERO
    if normalized > _ONE:
        return _ONE
    return normalized


def _decimal_count(value: int) -> Decimal:
    return Decimal(value).quantize(_QUANT)


def _status_count(
    rows: tuple[TeamMemorySpecialistPlaybookScoreRow, ...],
    status: str,
) -> Decimal:
    return _decimal_count(sum(1 for row in rows if row.memory_status == status))


def _average(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return _ZERO
    return _clamp_ratio(sum(values) / Decimal(len(values)))


def _report_status(rows: tuple[TeamMemorySpecialistPlaybookScoreRow, ...]) -> str:
    if not rows:
        return "empty"
    if any(row.memory_status == "block" for row in rows):
        return "block"
    if any(row.memory_status == "watch" for row in rows):
        return "watch"
    return "memory_ready"


def _observation_sort_key(
    observation: TeamMemorySpecialistPlaybookScoreObservation,
) -> tuple[int, str]:
    return _team_sort_key(observation.team_id)


def _row_sort_key(row: TeamMemorySpecialistPlaybookScoreRow) -> tuple[int, str]:
    return _team_sort_key(row.team_id)


def _team_sort_key(team_id: str) -> tuple[int, str]:
    normalized_team_id = require_strategy_team_id("team_id", team_id)
    return (_TEAM_SORT_INDEX[normalized_team_id], normalized_team_id)


def _reject_unsafe_public_payload(label: str, payload: object) -> None:
    for item in _iter_public_strings(payload):
        lowered = item.lower()
        if any(term in lowered for term in _UNSAFE_TERMS):
            raise ValueError(f"unsafe public payload entry in {label}")


def _iter_public_strings(value: object) -> tuple[str, ...]:
    if is_dataclass(value) and not isinstance(value, type):
        return _iter_public_strings(asdict(value))
    if isinstance(value, dict):
        items: list[str] = []
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            items.append(key)
            items.extend(_iter_public_strings(item))
        return tuple(items)
    if type(value) is str:
        return (value,)
    if isinstance(value, (list, tuple)):
        items = []
        for item in value:
            items.extend(_iter_public_strings(item))
        return tuple(items)
    return ()


def _json_ready_no_numbers(value: object) -> object:
    if value is None:
        return None
    if is_dataclass(value) and not isinstance(value, type):
        return _json_ready_no_numbers(asdict(value))
    if isinstance(value, Decimal):
        if not value.is_finite():
            raise ValueError("JSON Decimal value must be finite")
        return str(value)
    if isinstance(value, float) or type(value) is int:
        raise ValueError("JSON value must not be a runtime number")
    if isinstance(value, (str, bool)):
        return value
    if isinstance(value, dict):
        ready: dict[str, object] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            ready[key] = _json_ready_no_numbers(item)
        return ready
    if isinstance(value, (list, tuple)):
        return [_json_ready_no_numbers(item) for item in value]
    raise ValueError("value is not JSON serializable")


__all__ = (
    "DEFAULT_TEAM_MEMORY_SPECIALIST_PLAYBOOK_SCORE_CONFIG_VERSION",
    "TeamMemorySpecialistPlaybookScoreConfig",
    "TeamMemorySpecialistPlaybookScoreObservation",
    "TeamMemorySpecialistPlaybookScoreReasonCodeCount",
    "TeamMemorySpecialistPlaybookScoreReport",
    "TeamMemorySpecialistPlaybookScoreRow",
    "build_team_memory_specialist_playbook_score_report",
)
