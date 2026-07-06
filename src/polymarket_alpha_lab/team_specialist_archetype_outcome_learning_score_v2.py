"""Phase 1 paper-only specialist archetype outcome learning score report."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import asdict, dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_UP, localcontext
import hashlib
import json
import re
from typing import Any


DEFAULT_TEAM_SPECIALIST_ARCHETYPE_OUTCOME_LEARNING_SCORE_V2_CONFIG_VERSION = (
    "team-specialist-archetype-outcome-learning-score-v2"
)

QUANTUM = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
DECIMAL_CONTEXT = Context(prec=64)
SECONDS_PER_DAY = Decimal("86400")

_PUBLIC_IDENTIFIER_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,127}$")
_DIGEST_RE = re.compile(r"^[0-9a-f]{64}$")
_PHASE_FLAG_FIELDS = frozenset(("paper_only", "report_only", "readonly"))
_LEARNING_STATUSES = frozenset(("pass", "watch", "blocked"))
_UNSAFE_PUBLIC_TERMS = (
    "live",
    "auth",
    "wallet",
    "order",
    "network",
    "database",
    "persist",
    "signing",
    "mutation",
    "buy",
    "sell",
    "trade",
)
_REASON_CODE_SEQUENCE = (
    "empty_observations",
    "recent_learning_boost",
    "poor_outcome_penalty",
    "positive_outcome_learning",
    "outcome_learning_watch",
    "outcome_learning_blocked",
)


@dataclass(frozen=True)
class TeamSpecialistArchetypeOutcomeLearningScoreConfig:
    config_version: str = (
        DEFAULT_TEAM_SPECIALIST_ARCHETYPE_OUTCOME_LEARNING_SCORE_V2_CONFIG_VERSION
    )
    min_pass_score: Decimal = Decimal("0.650000")
    min_watch_score: Decimal = Decimal("0.450000")
    poor_outcome_threshold: Decimal = Decimal("0.350000")
    poor_outcome_penalty_per_observation: Decimal = Decimal("0.125000")
    recent_learning_window_days: Decimal = Decimal("7.000000")
    recent_learning_boost_per_observation: Decimal = Decimal("0.050000")
    max_recent_learning_boost: Decimal = Decimal("0.150000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not TeamSpecialistArchetypeOutcomeLearningScoreConfig:
            raise TypeError(
                "TeamSpecialistArchetypeOutcomeLearningScoreConfig does not "
                "support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not TeamSpecialistArchetypeOutcomeLearningScoreConfig:
            raise ValueError(
                "config must be exactly "
                "TeamSpecialistArchetypeOutcomeLearningScoreConfig",
            )
        _require_public_identifier("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_TEAM_SPECIALIST_ARCHETYPE_OUTCOME_LEARNING_SCORE_V2_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "min_pass_score",
            "min_watch_score",
            "poor_outcome_threshold",
            "poor_outcome_penalty_per_observation",
            "recent_learning_boost_per_observation",
            "max_recent_learning_boost",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "recent_learning_window_days",
            _require_nonnegative_decimal(
                "recent_learning_window_days",
                self.recent_learning_window_days,
            ),
        )
        if self.min_watch_score > self.min_pass_score:
            raise ValueError("min_watch_score must not exceed min_pass_score")
        _require_hard_flags("config", self)
        _reject_unsafe_public_payload("config", self)


@dataclass(frozen=True)
class TeamSpecialistArchetypeOutcomeObservation:
    observation_id: str
    specialist_id: str
    archetype: str
    evaluated_at: datetime
    resolved_at: datetime
    outcome_score: Decimal
    learning_applied_at: datetime | None = None
    public_note: str | None = None
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not TeamSpecialistArchetypeOutcomeObservation:
            raise TypeError(
                "TeamSpecialistArchetypeOutcomeObservation does not support "
                "subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not TeamSpecialistArchetypeOutcomeObservation:
            raise ValueError(
                "observation must be exactly "
                "TeamSpecialistArchetypeOutcomeObservation",
            )
        for field_name in ("observation_id", "specialist_id", "archetype"):
            _require_public_identifier(field_name, getattr(self, field_name))
        object.__setattr__(self, "evaluated_at", _as_utc("evaluated_at", self.evaluated_at))
        object.__setattr__(self, "resolved_at", _as_utc("resolved_at", self.resolved_at))
        if self.resolved_at < self.evaluated_at:
            raise ValueError("resolved_at must not be before evaluated_at")
        object.__setattr__(
            self,
            "outcome_score",
            _require_ratio_decimal("outcome_score", self.outcome_score),
        )
        object.__setattr__(
            self,
            "learning_applied_at",
            _normalize_optional_datetime(
                "learning_applied_at",
                self.learning_applied_at,
            ),
        )
        if self.learning_applied_at is not None and self.learning_applied_at < self.resolved_at:
            raise ValueError("learning_applied_at must not be before resolved_at")
        object.__setattr__(
            self,
            "public_note",
            _normalize_optional_public_text("public_note", self.public_note),
        )
        _require_hard_flags("observation", self)
        _reject_unsafe_public_payload("observation", self)


@dataclass(frozen=True)
class TeamSpecialistArchetypeOutcomeLearningPublicPayloadItem:
    key: str
    value: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not TeamSpecialistArchetypeOutcomeLearningPublicPayloadItem:
            raise TypeError(
                "TeamSpecialistArchetypeOutcomeLearningPublicPayloadItem does "
                "not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not TeamSpecialistArchetypeOutcomeLearningPublicPayloadItem:
            raise ValueError(
                "public payload item must be exactly "
                "TeamSpecialistArchetypeOutcomeLearningPublicPayloadItem",
            )
        _require_public_identifier("key", self.key)
        object.__setattr__(self, "value", _require_public_text("value", self.value))
        _require_hard_flags("public payload item", self)
        _reject_unsafe_public_payload("public payload item", self)


@dataclass(frozen=True)
class TeamSpecialistArchetypeOutcomeLearningScoreRow:
    specialist_id: str
    archetype: str
    observation_count: Decimal
    average_outcome_score: Decimal
    poor_outcome_count: Decimal
    poor_outcome_penalty: Decimal
    recent_learning_count: Decimal
    recent_learning_boost: Decimal
    archetype_outcome_learning_score: Decimal
    learning_status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not TeamSpecialistArchetypeOutcomeLearningScoreRow:
            raise TypeError(
                "TeamSpecialistArchetypeOutcomeLearningScoreRow does not "
                "support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not TeamSpecialistArchetypeOutcomeLearningScoreRow:
            raise ValueError(
                "row must be exactly TeamSpecialistArchetypeOutcomeLearningScoreRow",
            )
        _require_public_identifier("specialist_id", self.specialist_id)
        _require_public_identifier("archetype", self.archetype)
        for field_name in (
            "observation_count",
            "poor_outcome_count",
            "recent_learning_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_count_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "average_outcome_score",
            "poor_outcome_penalty",
            "recent_learning_boost",
            "archetype_outcome_learning_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        _require_learning_status("learning_status", self.learning_status)
        object.__setattr__(self, "reason_codes", _normalize_reason_codes(self.reason_codes))
        _validate_row_consistency(self)
        _require_hard_flags("row", self)
        _reject_unsafe_public_payload("row", self)


@dataclass(frozen=True)
class TeamSpecialistArchetypeOutcomeLearningScoreReport:
    generated_at: datetime
    config_version: str
    row_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    blocked_count: Decimal
    average_archetype_outcome_learning_score: Decimal
    max_poor_outcome_penalty: Decimal
    status: str
    reason_codes: tuple[str, ...]
    rows: tuple[TeamSpecialistArchetypeOutcomeLearningScoreRow, ...]
    public_payload: tuple[TeamSpecialistArchetypeOutcomeLearningPublicPayloadItem, ...]
    derived_validation_digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not TeamSpecialistArchetypeOutcomeLearningScoreReport:
            raise TypeError(
                "TeamSpecialistArchetypeOutcomeLearningScoreReport does not "
                "support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not TeamSpecialistArchetypeOutcomeLearningScoreReport:
            raise ValueError(
                "report must be exactly "
                "TeamSpecialistArchetypeOutcomeLearningScoreReport",
            )
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_identifier("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_TEAM_SPECIALIST_ARCHETYPE_OUTCOME_LEARNING_SCORE_V2_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in ("row_count", "pass_count", "watch_count", "blocked_count"):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_count_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "average_archetype_outcome_learning_score",
            "max_poor_outcome_penalty",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        _require_learning_status("status", self.status)
        object.__setattr__(self, "reason_codes", _normalize_reason_codes(self.reason_codes))
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        object.__setattr__(
            self,
            "public_payload",
            _normalize_public_payload(self.public_payload),
        )
        _require_sha256_digest("derived_validation_digest", self.derived_validation_digest)
        _validate_report_consistency(self)
        _require_hard_flags("report", self)
        _reject_unsafe_public_payload("report", self)
        expected_digest = _report_digest_from_values(_report_values_without_digest(self))
        if self.derived_validation_digest != expected_digest:
            raise ValueError("derived_validation_digest does not match report payload")


def build_team_specialist_archetype_outcome_learning_score_v2_report(
    observations: Sequence[TeamSpecialistArchetypeOutcomeObservation],
    *,
    generated_at: datetime,
    config: TeamSpecialistArchetypeOutcomeLearningScoreConfig | None = None,
    public_payload: Sequence[TeamSpecialistArchetypeOutcomeLearningPublicPayloadItem] = (),
) -> TeamSpecialistArchetypeOutcomeLearningScoreReport:
    """Build a local report-only score for specialist/archetype outcome learning."""

    if config is None:
        config = TeamSpecialistArchetypeOutcomeLearningScoreConfig()
    if type(config) is not TeamSpecialistArchetypeOutcomeLearningScoreConfig:
        raise ValueError(
            "config must be TeamSpecialistArchetypeOutcomeLearningScoreConfig",
        )
    generated_at = _as_utc("generated_at", generated_at)
    normalized_observations = _normalize_observations(observations)
    for observation in normalized_observations:
        _require_not_future("evaluated_at", observation.evaluated_at, generated_at)
        _require_not_future("resolved_at", observation.resolved_at, generated_at)
        if observation.learning_applied_at is not None:
            _require_not_future(
                "learning_applied_at",
                observation.learning_applied_at,
                generated_at,
            )
    payload_items = _normalize_public_payload(public_payload)
    rows = _build_rows(normalized_observations, generated_at=generated_at, config=config)
    values: dict[str, object] = {
        "generated_at": generated_at,
        "config_version": config.config_version,
        "row_count": _count_decimal(len(rows)),
        "pass_count": _status_count(rows, "pass"),
        "watch_count": _status_count(rows, "watch"),
        "blocked_count": _status_count(rows, "blocked"),
        "average_archetype_outcome_learning_score": _average(
            tuple(row.archetype_outcome_learning_score for row in rows),
        ),
        "max_poor_outcome_penalty": max(
            (row.poor_outcome_penalty for row in rows),
            default=ZERO,
        ),
        "status": _report_status(rows),
        "reason_codes": _report_reason_codes(rows),
        "rows": rows,
        "public_payload": payload_items,
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    return TeamSpecialistArchetypeOutcomeLearningScoreReport(
        **values,
        derived_validation_digest=_report_digest_from_values(values),
    )


def team_specialist_archetype_outcome_learning_score_v2_payload(
    value: TeamSpecialistArchetypeOutcomeLearningScoreReport | Mapping[str, object],
) -> dict[str, object]:
    if type(value) is TeamSpecialistArchetypeOutcomeLearningScoreReport:
        _validate_report_consistency(value)
        _require_hard_flags("report", value)
        _reject_unsafe_public_payload("report", value)
        expected_digest = _report_digest_from_values(_report_values_without_digest(value))
        if value.derived_validation_digest != expected_digest:
            raise ValueError("derived_validation_digest does not match report payload")
        payload = _json_ready(asdict(value))
    elif isinstance(value, Mapping):
        payload = _json_ready(value)
    else:
        raise ValueError(
            "value must be TeamSpecialistArchetypeOutcomeLearningScoreReport or payload",
        )
    if type(payload) is not dict:
        raise ValueError("payload must be a dict")
    _validate_public_payload(payload)
    _reject_unsafe_public_payload(
        "team specialist archetype outcome learning payload",
        payload,
        allow_json_containers=True,
    )
    return payload


def _build_rows(
    observations: tuple[TeamSpecialistArchetypeOutcomeObservation, ...],
    *,
    generated_at: datetime,
    config: TeamSpecialistArchetypeOutcomeLearningScoreConfig,
) -> tuple[TeamSpecialistArchetypeOutcomeLearningScoreRow, ...]:
    grouped: dict[tuple[str, str], list[TeamSpecialistArchetypeOutcomeObservation]] = {}
    for observation in observations:
        grouped.setdefault(
            (observation.specialist_id, observation.archetype),
            [],
        ).append(observation)
    rows = tuple(
        _row_for_group(
            specialist_id=specialist_id,
            archetype=archetype,
            observations=tuple(group),
            generated_at=generated_at,
            config=config,
        )
        for (specialist_id, archetype), group in sorted(grouped.items())
    )
    return tuple(sorted(rows, key=_row_sort_key))


def _row_for_group(
    *,
    specialist_id: str,
    archetype: str,
    observations: tuple[TeamSpecialistArchetypeOutcomeObservation, ...],
    generated_at: datetime,
    config: TeamSpecialistArchetypeOutcomeLearningScoreConfig,
) -> TeamSpecialistArchetypeOutcomeLearningScoreRow:
    observation_count = _count_decimal(len(observations))
    poor_count = _count_decimal(
        sum(1 for observation in observations if observation.outcome_score <= config.poor_outcome_threshold),
    )
    recent_count = _count_decimal(
        sum(
            1
            for observation in observations
            if observation.learning_applied_at is not None
            and _days_between(generated_at, observation.learning_applied_at)
            <= config.recent_learning_window_days
        ),
    )
    average_outcome_score = _average(
        tuple(observation.outcome_score for observation in observations),
    )
    poor_outcome_penalty = _clamp_ratio(
        poor_count * config.poor_outcome_penalty_per_observation,
    )
    recent_learning_boost = _clamp_ratio(
        min(
            _divide_decimal(
                recent_count * config.recent_learning_boost_per_observation,
                observation_count,
            ),
            config.max_recent_learning_boost,
        ),
    )
    archetype_score = _clamp_ratio(
        average_outcome_score - poor_outcome_penalty + recent_learning_boost,
    )
    learning_status = _row_status(archetype_score, config)
    return TeamSpecialistArchetypeOutcomeLearningScoreRow(
        specialist_id=specialist_id,
        archetype=archetype,
        observation_count=observation_count,
        average_outcome_score=average_outcome_score,
        poor_outcome_count=poor_count,
        poor_outcome_penalty=poor_outcome_penalty,
        recent_learning_count=recent_count,
        recent_learning_boost=recent_learning_boost,
        archetype_outcome_learning_score=archetype_score,
        learning_status=learning_status,
        reason_codes=_row_reason_codes(
            learning_status=learning_status,
            recent_learning_boost=recent_learning_boost,
            poor_outcome_penalty=poor_outcome_penalty,
        ),
    )


def _row_status(
    archetype_score: Decimal,
    config: TeamSpecialistArchetypeOutcomeLearningScoreConfig,
) -> str:
    if archetype_score >= config.min_pass_score:
        return "pass"
    if archetype_score >= config.min_watch_score:
        return "watch"
    return "blocked"


def _row_reason_codes(
    *,
    learning_status: str,
    recent_learning_boost: Decimal,
    poor_outcome_penalty: Decimal,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    if recent_learning_boost > ZERO:
        reason_codes.append("recent_learning_boost")
    if poor_outcome_penalty > ZERO:
        reason_codes.append("poor_outcome_penalty")
    if learning_status == "pass":
        reason_codes.append("positive_outcome_learning")
    elif learning_status == "watch":
        reason_codes.append("outcome_learning_watch")
    else:
        reason_codes.append("outcome_learning_blocked")
    return _normalize_reason_codes(tuple(reason_codes))


def _report_status(rows: tuple[TeamSpecialistArchetypeOutcomeLearningScoreRow, ...]) -> str:
    if any(row.learning_status == "blocked" for row in rows):
        return "blocked"
    if any(row.learning_status == "watch" for row in rows) or not rows:
        return "watch"
    return "pass"


def _report_reason_codes(
    rows: tuple[TeamSpecialistArchetypeOutcomeLearningScoreRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return ("empty_observations",)
    observed: list[str] = []
    for row in rows:
        observed.extend(row.reason_codes)
    return _normalize_reason_codes(tuple(observed))


def _status_count(
    rows: tuple[TeamSpecialistArchetypeOutcomeLearningScoreRow, ...],
    status: str,
) -> Decimal:
    return _count_decimal(sum(1 for row in rows if row.learning_status == status))


def _row_sort_key(row: TeamSpecialistArchetypeOutcomeLearningScoreRow) -> tuple[str, str]:
    return (row.specialist_id, row.archetype)


def _validate_row_consistency(row: TeamSpecialistArchetypeOutcomeLearningScoreRow) -> None:
    if row.poor_outcome_count > row.observation_count:
        raise ValueError("poor_outcome_count must not exceed observation_count")
    if row.recent_learning_count > row.observation_count:
        raise ValueError("recent_learning_count must not exceed observation_count")
    if row.learning_status == "pass" and "positive_outcome_learning" not in row.reason_codes:
        raise ValueError("pass rows must include positive_outcome_learning")
    if row.learning_status == "watch" and "outcome_learning_watch" not in row.reason_codes:
        raise ValueError("watch rows must include outcome_learning_watch")
    if row.learning_status == "blocked" and "outcome_learning_blocked" not in row.reason_codes:
        raise ValueError("blocked rows must include outcome_learning_blocked")
    if row.poor_outcome_penalty > ZERO and "poor_outcome_penalty" not in row.reason_codes:
        raise ValueError("poor outcome penalties must include poor_outcome_penalty")
    if row.recent_learning_boost > ZERO and "recent_learning_boost" not in row.reason_codes:
        raise ValueError("recent learning boosts must include recent_learning_boost")


def _validate_report_consistency(
    report: TeamSpecialistArchetypeOutcomeLearningScoreReport,
) -> None:
    if report.row_count != _count_decimal(len(report.rows)):
        raise ValueError("row_count must match rows")
    if report.pass_count != _status_count(report.rows, "pass"):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _status_count(report.rows, "watch"):
        raise ValueError("watch_count must match rows")
    if report.blocked_count != _status_count(report.rows, "blocked"):
        raise ValueError("blocked_count must match rows")
    if report.average_archetype_outcome_learning_score != _average(
        tuple(row.archetype_outcome_learning_score for row in report.rows),
    ):
        raise ValueError("average_archetype_outcome_learning_score must match rows")
    expected_max_penalty = max(
        (row.poor_outcome_penalty for row in report.rows),
        default=ZERO,
    )
    if report.max_poor_outcome_penalty != expected_max_penalty:
        raise ValueError("max_poor_outcome_penalty must match rows")
    if report.status != _report_status(report.rows):
        raise ValueError("status must match rows")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")


def _normalize_observations(
    observations: Sequence[TeamSpecialistArchetypeOutcomeObservation],
) -> tuple[TeamSpecialistArchetypeOutcomeObservation, ...]:
    if isinstance(observations, (str, bytes)) or not isinstance(observations, Sequence):
        raise ValueError("observations must be a sequence")
    normalized: list[TeamSpecialistArchetypeOutcomeObservation] = []
    seen: set[str] = set()
    for observation in observations:
        if type(observation) is not TeamSpecialistArchetypeOutcomeObservation:
            raise ValueError(
                "observations must contain "
                "TeamSpecialistArchetypeOutcomeObservation",
            )
        _require_hard_flags("observation", observation)
        if observation.observation_id in seen:
            raise ValueError("duplicate observation_id")
        seen.add(observation.observation_id)
        normalized.append(observation)
    return tuple(
        sorted(
            normalized,
            key=lambda observation: (
                observation.specialist_id,
                observation.archetype,
                observation.resolved_at,
                observation.observation_id,
            ),
        ),
    )


def _normalize_rows(
    rows: Sequence[TeamSpecialistArchetypeOutcomeLearningScoreRow],
) -> tuple[TeamSpecialistArchetypeOutcomeLearningScoreRow, ...]:
    if isinstance(rows, (str, bytes)) or not isinstance(rows, Sequence):
        raise ValueError("rows must be a sequence")
    normalized: list[TeamSpecialistArchetypeOutcomeLearningScoreRow] = []
    for row in rows:
        if type(row) is not TeamSpecialistArchetypeOutcomeLearningScoreRow:
            raise ValueError(
                "rows must contain TeamSpecialistArchetypeOutcomeLearningScoreRow",
            )
        _require_hard_flags("row", row)
        normalized.append(row)
    return tuple(sorted(normalized, key=_row_sort_key))


def _normalize_public_payload(
    public_payload: Sequence[TeamSpecialistArchetypeOutcomeLearningPublicPayloadItem],
) -> tuple[TeamSpecialistArchetypeOutcomeLearningPublicPayloadItem, ...]:
    if isinstance(public_payload, (str, bytes)) or not isinstance(public_payload, Sequence):
        raise ValueError("public_payload must be a sequence")
    normalized: list[TeamSpecialistArchetypeOutcomeLearningPublicPayloadItem] = []
    for item in public_payload:
        if type(item) is not TeamSpecialistArchetypeOutcomeLearningPublicPayloadItem:
            raise ValueError(
                "public_payload items must be "
                "TeamSpecialistArchetypeOutcomeLearningPublicPayloadItem",
            )
        _require_hard_flags("public payload item", item)
        normalized.append(item)
    return tuple(sorted(normalized, key=lambda item: item.key))


def _validate_public_payload(payload: dict[str, object]) -> None:
    _require_payload_flags(payload, "payload")
    _payload_required_string(payload, "generated_at")
    config_version = _payload_required_string(payload, "config_version")
    if config_version != DEFAULT_TEAM_SPECIALIST_ARCHETYPE_OUTCOME_LEARNING_SCORE_V2_CONFIG_VERSION:
        raise ValueError("config_version must be the supported config version")
    row_count = _payload_required_decimal(payload, "row_count")
    pass_count = _payload_required_decimal(payload, "pass_count")
    watch_count = _payload_required_decimal(payload, "watch_count")
    blocked_count = _payload_required_decimal(payload, "blocked_count")
    average_score = _payload_required_decimal(
        payload,
        "average_archetype_outcome_learning_score",
    )
    max_penalty = _payload_required_decimal(payload, "max_poor_outcome_penalty")
    status = _payload_required_string(payload, "status")
    _require_learning_status("status", status)
    reason_codes = _payload_required_string_list(payload, "reason_codes")
    _normalize_reason_codes(tuple(reason_codes))
    rows = _payload_required_list(payload, "rows")
    public_payload = _payload_required_list(payload, "public_payload")
    for item in public_payload:
        if type(item) is not dict:
            raise ValueError("public_payload items must be dicts")
        _require_payload_flags(item, "public_payload")
        _require_public_identifier("key", _payload_required_string(item, "key"))
        _require_public_text("value", _payload_required_string(item, "value"))
    row_payloads = tuple(_validated_row_payload(row) for row in rows)
    if row_count != _count_decimal(len(row_payloads)):
        raise ValueError("row_count must match rows")
    if pass_count != _payload_status_count(row_payloads, "pass"):
        raise ValueError("pass_count must match rows")
    if watch_count != _payload_status_count(row_payloads, "watch"):
        raise ValueError("watch_count must match rows")
    if blocked_count != _payload_status_count(row_payloads, "blocked"):
        raise ValueError("blocked_count must match rows")
    if average_score != _average(
        tuple(row["archetype_outcome_learning_score"] for row in row_payloads),
    ):
        raise ValueError("average_archetype_outcome_learning_score must match rows")
    expected_max_penalty = max(
        (row["poor_outcome_penalty"] for row in row_payloads),
        default=ZERO,
    )
    if max_penalty != expected_max_penalty:
        raise ValueError("max_poor_outcome_penalty must match rows")
    expected_status = _payload_report_status(row_payloads)
    if status != expected_status:
        raise ValueError("status must match rows")
    expected_reason_codes = _payload_report_reason_codes(row_payloads)
    if tuple(reason_codes) != expected_reason_codes:
        raise ValueError("reason_codes must match rows")
    digest_value = _payload_required_string(payload, "derived_validation_digest")
    _require_sha256_digest("derived_validation_digest", digest_value)
    if digest_value != _public_payload_derived_validation_digest(payload):
        raise ValueError("derived_validation_digest does not match public payload")


def _validated_row_payload(row: object) -> dict[str, Decimal | str | tuple[str, ...]]:
    if type(row) is not dict:
        raise ValueError("rows must contain dicts")
    _require_payload_flags(row, "row")
    specialist_id = _payload_required_string(row, "specialist_id")
    archetype = _payload_required_string(row, "archetype")
    _require_public_identifier("specialist_id", specialist_id)
    _require_public_identifier("archetype", archetype)
    observation_count = _payload_required_decimal(row, "observation_count")
    average_outcome_score = _payload_required_decimal(row, "average_outcome_score")
    poor_outcome_count = _payload_required_decimal(row, "poor_outcome_count")
    poor_outcome_penalty = _payload_required_decimal(row, "poor_outcome_penalty")
    recent_learning_count = _payload_required_decimal(row, "recent_learning_count")
    recent_learning_boost = _payload_required_decimal(row, "recent_learning_boost")
    archetype_score = _payload_required_decimal(
        row,
        "archetype_outcome_learning_score",
    )
    learning_status = _payload_required_string(row, "learning_status")
    _require_learning_status("learning_status", learning_status)
    reason_codes = tuple(_payload_required_string_list(row, "reason_codes"))
    _normalize_reason_codes(reason_codes)
    candidate = {
        "specialist_id": specialist_id,
        "archetype": archetype,
        "observation_count": observation_count,
        "average_outcome_score": average_outcome_score,
        "poor_outcome_count": poor_outcome_count,
        "poor_outcome_penalty": poor_outcome_penalty,
        "recent_learning_count": recent_learning_count,
        "recent_learning_boost": recent_learning_boost,
        "archetype_outcome_learning_score": archetype_score,
        "learning_status": learning_status,
        "reason_codes": reason_codes,
    }
    dataclass_row = TeamSpecialistArchetypeOutcomeLearningScoreRow(**candidate)
    _validate_row_consistency(dataclass_row)
    return candidate


def _payload_report_status(
    rows: tuple[dict[str, Decimal | str | tuple[str, ...]], ...],
) -> str:
    if any(row["learning_status"] == "blocked" for row in rows):
        return "blocked"
    if any(row["learning_status"] == "watch" for row in rows) or not rows:
        return "watch"
    return "pass"


def _payload_report_reason_codes(
    rows: tuple[dict[str, Decimal | str | tuple[str, ...]], ...],
) -> tuple[str, ...]:
    if not rows:
        return ("empty_observations",)
    reason_codes: list[str] = []
    for row in rows:
        reason_codes.extend(row["reason_codes"])  # type: ignore[arg-type]
    return _normalize_reason_codes(tuple(reason_codes))


def _payload_status_count(
    rows: tuple[dict[str, Decimal | str | tuple[str, ...]], ...],
    status: str,
) -> Decimal:
    return _count_decimal(sum(1 for row in rows if row["learning_status"] == status))


def _payload_required_string(payload: Mapping[str, object], field_name: str) -> str:
    value = payload.get(field_name)
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    return value


def _payload_required_decimal(payload: Mapping[str, object], field_name: str) -> Decimal:
    value = payload.get(field_name)
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a Decimal string")
    try:
        decimal_value = Decimal(value)
    except Exception as exc:
        raise ValueError(f"{field_name} must be a Decimal string") from exc
    normalized = _require_decimal(field_name, decimal_value)
    if str(normalized) != value:
        raise ValueError(f"{field_name} must be a canonical Decimal string")
    return normalized


def _payload_required_list(payload: Mapping[str, object], field_name: str) -> list[object]:
    value = payload.get(field_name)
    if type(value) is not list:
        raise ValueError(f"{field_name} must be a list")
    return value


def _payload_required_string_list(
    payload: Mapping[str, object],
    field_name: str,
) -> list[str]:
    value = _payload_required_list(payload, field_name)
    normalized: list[str] = []
    for item in value:
        if type(item) is not str:
            raise ValueError(f"{field_name} must contain strings")
        normalized.append(item)
    return normalized


def _require_payload_flags(payload: Mapping[str, object], label: str) -> None:
    for field_name in _PHASE_FLAG_FIELDS:
        if payload.get(field_name) is not True:
            raise ValueError(f"{field_name} must be True for {label}")


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in _PHASE_FLAG_FIELDS:
        if getattr(value, field_name) is not True:
            raise ValueError(f"{field_name} must be True for {label}")


def _require_public_identifier(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not _PUBLIC_IDENTIFIER_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a public identifier")
    _reject_unsafe_public_string(field_name, value)
    return value


def _require_public_text(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if value.strip() != value or not value:
        raise ValueError(f"{field_name} must be non-empty public text")
    if len(value) > 512:
        raise ValueError(f"{field_name} must not exceed 512 characters")
    _reject_unsafe_public_string(field_name, value)
    return value


def _normalize_optional_public_text(field_name: str, value: object) -> str | None:
    if value is None:
        return None
    return _require_public_text(field_name, value)


def _reject_unsafe_public_string(field_name: str, value: str) -> None:
    lowered = value.lower()
    if "://" in lowered or "?" in lowered or "@" in lowered:
        raise ValueError(f"{field_name} has unsafe public value")
    if any(term in lowered for term in _UNSAFE_PUBLIC_TERMS):
        raise ValueError(f"{field_name} has unsafe public value")


def _require_learning_status(field_name: str, value: object) -> str:
    if type(value) is not str or value not in _LEARNING_STATUSES:
        raise ValueError(f"{field_name} must be a known learning status")
    return value


def _require_sha256_digest(field_name: str, value: object) -> str:
    if type(value) is not str or not _DIGEST_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a lowercase sha256 digest")
    return value


def _require_ratio_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < ZERO or normalized > ONE:
        raise ValueError(f"{field_name} must be between zero and one")
    return normalized


def _require_nonnegative_count_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < ZERO or normalized != normalized.to_integral_value():
        raise ValueError(f"{field_name} must be a whole nonnegative Decimal")
    return normalized


def _require_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    if value.as_tuple().exponent < QUANTUM.as_tuple().exponent:
        raise ValueError(f"{field_name} must not exceed six decimal places")
    return _quantize(value)


def _count_decimal(value: int) -> Decimal:
    if value < 0:
        raise ValueError("count must be nonnegative")
    return Decimal(value).quantize(QUANTUM)


def _average(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return _quantize(sum(values, ZERO) / Decimal(len(values)))


def _divide_decimal(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator <= ZERO:
        raise ValueError("denominator must be positive")
    with localcontext(DECIMAL_CONTEXT):
        return _quantize(numerator / denominator)


def _clamp_ratio(value: Decimal) -> Decimal:
    normalized = _quantize(value)
    if normalized < ZERO:
        return ZERO
    if normalized > ONE:
        return ONE
    return normalized


def _quantize(value: Decimal) -> Decimal:
    return value.quantize(QUANTUM, rounding=ROUND_HALF_UP)


def _normalize_reason_codes(reason_codes: Sequence[str]) -> tuple[str, ...]:
    if isinstance(reason_codes, (str, bytes)) or not isinstance(reason_codes, Sequence):
        raise ValueError("reason_codes must be a sequence")
    normalized: list[str] = []
    for reason_code in reason_codes:
        _require_public_identifier("reason_code", reason_code)
        if reason_code not in _REASON_CODE_SEQUENCE:
            raise ValueError("reason_code must be supported")
        if reason_code not in normalized:
            normalized.append(reason_code)
    return tuple(
        reason_code
        for reason_code in _REASON_CODE_SEQUENCE
        if reason_code in normalized
    )


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _normalize_optional_datetime(field_name: str, value: object) -> datetime | None:
    if value is None:
        return None
    return _as_utc(field_name, value)


def _require_not_future(field_name: str, value: datetime, generated_at: datetime) -> None:
    if value > generated_at:
        raise ValueError(f"{field_name} must not be after generated_at")


def _days_between(generated_at: datetime, observed_at: datetime) -> Decimal:
    seconds = Decimal(str((generated_at - observed_at).total_seconds()))
    if seconds < ZERO:
        raise ValueError("observed_at must not be after generated_at")
    with localcontext(DECIMAL_CONTEXT):
        return _quantize(seconds / SECONDS_PER_DAY)


def _report_values_without_digest(
    report: TeamSpecialistArchetypeOutcomeLearningScoreReport,
) -> dict[str, object]:
    values = asdict(report)
    values.pop("derived_validation_digest", None)
    return values


def _report_digest_from_values(values: Mapping[str, object]) -> str:
    payload = _json_ready(values)
    _reject_unsafe_public_payload(
        "derived_validation_digest payload",
        payload,
        allow_json_containers=True,
    )
    canonical = json.dumps(
        payload,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _public_payload_derived_validation_digest(payload: Mapping[str, object]) -> str:
    digest_payload = dict(payload)
    digest_payload.pop("derived_validation_digest", None)
    return _report_digest_from_values(digest_payload)


def _json_ready(value: Any) -> Any:
    if value is None:
        return None
    if is_dataclass(value) and not isinstance(value, type):
        return _json_ready(asdict(value))
    if type(value) is Decimal:
        if not value.is_finite():
            raise ValueError("Decimal payload value must be finite")
        return str(value)
    if type(value) is datetime:
        return _as_utc("datetime payload value", value).isoformat()
    if type(value) is bool or type(value) is str:
        return value
    if type(value) is int or isinstance(value, float):
        raise ValueError("numeric payload values must be Decimal strings")
    if isinstance(value, Mapping):
        ready: dict[str, Any] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            ready[key] = _json_ready(item)
        return ready
    if isinstance(value, (list, tuple)):
        return [_json_ready(item) for item in value]
    raise ValueError("payload value is not JSON serializable")


def _reject_unsafe_public_payload(
    label: str,
    value: object,
    path: str = "",
    *,
    allow_json_containers: bool = False,
) -> None:
    current_path = path or label
    if is_dataclass(value) and not isinstance(value, type):
        for field in fields(value):
            _reject_unsafe_public_key(field.name, current_path)
            _reject_unsafe_public_payload(
                label,
                getattr(value, field.name),
                field.name if not path else f"{path}.{field.name}",
                allow_json_containers=allow_json_containers,
            )
        return
    if isinstance(value, Mapping):
        if not allow_json_containers:
            raise ValueError(f"{current_path} must remain constructor-normalized")
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            _reject_unsafe_public_key(key, current_path)
            _reject_unsafe_public_payload(
                label,
                item,
                key if not path else f"{path}.{key}",
                allow_json_containers=True,
            )
        return
    if isinstance(value, (list, tuple)):
        if type(value) is list and not allow_json_containers:
            raise ValueError(f"{current_path} must remain constructor-normalized")
        for index, item in enumerate(value):
            _reject_unsafe_public_payload(
                label,
                item,
                f"{current_path}[{index}]",
                allow_json_containers=allow_json_containers,
            )
        return
    if type(value) is str:
        _reject_unsafe_public_string(current_path, value)
        return
    if (
        value is None
        or type(value) is bool
        or type(value) is Decimal
        or type(value) is datetime
    ):
        return
    raise ValueError(f"{current_path} is not a supported public payload value")


def _reject_unsafe_public_key(key: str, path: str) -> None:
    lowered = key.lower()
    if any(term in lowered for term in _UNSAFE_PUBLIC_TERMS):
        raise ValueError(f"{path}.{key} has unsafe public field")


__all__ = (
    "DEFAULT_TEAM_SPECIALIST_ARCHETYPE_OUTCOME_LEARNING_SCORE_V2_CONFIG_VERSION",
    "TeamSpecialistArchetypeOutcomeLearningPublicPayloadItem",
    "TeamSpecialistArchetypeOutcomeLearningScoreConfig",
    "TeamSpecialistArchetypeOutcomeLearningScoreReport",
    "TeamSpecialistArchetypeOutcomeLearningScoreRow",
    "TeamSpecialistArchetypeOutcomeObservation",
    "build_team_specialist_archetype_outcome_learning_score_v2_report",
    "team_specialist_archetype_outcome_learning_score_v2_payload",
)
