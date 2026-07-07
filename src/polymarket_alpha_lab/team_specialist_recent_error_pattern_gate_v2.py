"""Readonly Phase 1 gate for recent specialist error patterns."""

from __future__ import annotations

from dataclasses import asdict, dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, localcontext
from hashlib import sha256
import json
from typing import Any

from polymarket_alpha_lab.team_taxonomy import require_team_category_pair, require_team_id


DEFAULT_TEAM_SPECIALIST_RECENT_ERROR_PATTERN_GATE_V2_CONFIG_VERSION = (
    "team-specialist-recent-error-pattern-gate-v2"
)
DECIMAL_CONTEXT = Context(prec=64)
COUNT_QUANTUM = Decimal("1")
SCORE_QUANTUM = Decimal("0.000001")
SECONDS_QUANTUM = Decimal("0.000001")
ZERO_COUNT = Decimal("0").quantize(COUNT_QUANTUM)
ZERO_SCORE = Decimal("0").quantize(SCORE_QUANTUM)
ZERO_SECONDS = Decimal("0").quantize(SECONDS_QUANTUM)
ONE_SCORE = Decimal("1").quantize(SCORE_QUANTUM)
GATE_STATUSES = ("pass", "watch", "blocked")
ROW_SORT_STATUSES = ("blocked", "watch", "pass")
ROW_REASON_CODES = (
    "recent_repeated_error_pattern",
    "brier_like_error_blocked",
    "brier_like_error_watch",
    "miss_count_blocked",
    "miss_count_watch",
    "contradiction_mishandling_blocked",
    "contradiction_mishandling_watch",
    "source_family_weakness_blocked",
    "source_family_weakness_watch",
    "resolution_lag_blocked",
    "resolution_lag_watch",
    "recent_error_pattern_clear",
)
REPORT_REASON_CODES = (
    "no_recent_error_patterns_supplied",
    "blocked_recent_error_patterns_present",
    "watch_recent_error_patterns_present",
    "recent_error_patterns_clear",
    "brier_like_error_patterns_present",
    "miss_count_patterns_present",
    "contradiction_mishandling_patterns_present",
    "source_family_weakness_patterns_present",
    "resolution_lag_patterns_present",
)
PHASE_FLAG_FIELDS = ("paper_only", "report_only", "readonly")
UNSAFE_PUBLIC_TERMS = (
    "live",
    "auth",
    "wallet",
    "order",
    "network",
    "database",
    "db",
    "persist",
    "signing",
    "mutation",
    "buy",
    "sell",
    "trade",
)

__all__ = (
    "DEFAULT_TEAM_SPECIALIST_RECENT_ERROR_PATTERN_GATE_V2_CONFIG_VERSION",
    "TeamSpecialistRecentErrorPatternGateV2Config",
    "TeamSpecialistRecentErrorPatternGateV2Observation",
    "TeamSpecialistRecentErrorPatternGateV2Row",
    "TeamSpecialistRecentErrorPatternGateV2Report",
    "build_team_specialist_recent_error_pattern_gate_v2",
    "team_specialist_recent_error_pattern_gate_v2_payload",
)


@dataclass(frozen=True)
class TeamSpecialistRecentErrorPatternGateV2Config:
    config_version: str = (
        DEFAULT_TEAM_SPECIALIST_RECENT_ERROR_PATTERN_GATE_V2_CONFIG_VERSION
    )
    recent_window_seconds: Decimal = Decimal("2592000.000000")
    watch_recent_pattern_count: Decimal = Decimal("2")
    blocked_recent_pattern_count: Decimal = Decimal("3")
    watch_brier_like_error: Decimal = Decimal("0.200000")
    blocked_brier_like_error: Decimal = Decimal("0.300000")
    watch_miss_count: Decimal = Decimal("2")
    blocked_miss_count: Decimal = Decimal("3")
    watch_contradiction_mishandled_count: Decimal = Decimal("1")
    blocked_contradiction_mishandled_count: Decimal = Decimal("2")
    watch_source_family_weakness: Decimal = Decimal("0.500000")
    blocked_source_family_weakness: Decimal = Decimal("0.700000")
    watch_resolution_lag_seconds: Decimal = Decimal("172800.000000")
    blocked_resolution_lag_seconds: Decimal = Decimal("604800.000000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_public_string("config_version", self.config_version)
        object.__setattr__(
            self,
            "recent_window_seconds",
            _normalize_positive_seconds(
                "recent_window_seconds",
                self.recent_window_seconds,
            ),
        )
        for field_name in (
            "watch_recent_pattern_count",
            "blocked_recent_pattern_count",
            "watch_miss_count",
            "blocked_miss_count",
            "watch_contradiction_mishandled_count",
            "blocked_contradiction_mishandled_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_count(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "watch_brier_like_error",
            "blocked_brier_like_error",
            "watch_source_family_weakness",
            "blocked_source_family_weakness",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_score(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "watch_resolution_lag_seconds",
            "blocked_resolution_lag_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_seconds(field_name, getattr(self, field_name)),
            )
        _validate_config(self)
        _require_hard_flags("TeamSpecialistRecentErrorPatternGateV2Config", self)
        _reject_unsafe_public_payload(
            "TeamSpecialistRecentErrorPatternGateV2Config",
            self,
        )


@dataclass(frozen=True)
class TeamSpecialistRecentErrorPatternGateV2Observation:
    error_id: str
    team_id: str
    category_id: str
    specialist_id: str
    event_archetype: str
    evaluated_at: datetime
    brier_like_error: Decimal
    miss_count: Decimal
    contradiction_mishandled_count: Decimal
    source_family_weakness_score: Decimal
    resolution_lag_seconds: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_public_string("error_id", self.error_id)
        object.__setattr__(self, "team_id", require_team_id("team_id", self.team_id))
        require_team_category_pair(
            "team_id",
            self.team_id,
            "category_id",
            self.category_id,
        )
        _require_public_string("category_id", self.category_id)
        _require_public_string("specialist_id", self.specialist_id)
        _require_public_string("event_archetype", self.event_archetype)
        object.__setattr__(self, "evaluated_at", _as_utc("evaluated_at", self.evaluated_at))
        object.__setattr__(
            self,
            "brier_like_error",
            _normalize_score("brier_like_error", self.brier_like_error),
        )
        for field_name in ("miss_count", "contradiction_mishandled_count"):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_count(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "source_family_weakness_score",
            _normalize_score(
                "source_family_weakness_score",
                self.source_family_weakness_score,
            ),
        )
        object.__setattr__(
            self,
            "resolution_lag_seconds",
            _normalize_nonnegative_seconds(
                "resolution_lag_seconds",
                self.resolution_lag_seconds,
            ),
        )
        _require_hard_flags("TeamSpecialistRecentErrorPatternGateV2Observation", self)
        _reject_unsafe_public_payload(
            "TeamSpecialistRecentErrorPatternGateV2Observation",
            self,
        )


@dataclass(frozen=True)
class TeamSpecialistRecentErrorPatternGateV2Row:
    team_id: str
    category_id: str
    specialist_id: str
    event_archetype: str
    gate_status: str
    source_error_count: Decimal
    recent_error_count: Decimal
    latest_recent_error_age_seconds: Decimal | None
    oldest_recent_error_age_seconds: Decimal | None
    max_brier_like_error: Decimal
    total_miss_count: Decimal
    contradiction_mishandled_count: Decimal
    max_source_family_weakness_score: Decimal
    max_resolution_lag_seconds: Decimal
    contributing_error_ids: tuple[str, ...]
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "team_id", require_team_id("team_id", self.team_id))
        require_team_category_pair(
            "team_id",
            self.team_id,
            "category_id",
            self.category_id,
        )
        _require_public_string("category_id", self.category_id)
        _require_public_string("specialist_id", self.specialist_id)
        _require_public_string("event_archetype", self.event_archetype)
        _require_member("gate_status", self.gate_status, GATE_STATUSES)
        for field_name in (
            "source_error_count",
            "recent_error_count",
            "total_miss_count",
            "contradiction_mishandled_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_count(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "latest_recent_error_age_seconds",
            "oldest_recent_error_age_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_optional_nonnegative_seconds(
                    field_name,
                    getattr(self, field_name),
                ),
            )
        for field_name in (
            "max_brier_like_error",
            "max_source_family_weakness_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_score(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "max_resolution_lag_seconds",
            _normalize_nonnegative_seconds(
                "max_resolution_lag_seconds",
                self.max_resolution_lag_seconds,
            ),
        )
        object.__setattr__(
            self,
            "contributing_error_ids",
            _normalize_error_ids(self.contributing_error_ids),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, ROW_REASON_CODES),
        )
        _require_hard_flags("TeamSpecialistRecentErrorPatternGateV2Row", self)
        _reject_unsafe_public_payload(
            "TeamSpecialistRecentErrorPatternGateV2Row",
            self,
        )
        _validate_row(self)


@dataclass(frozen=True)
class TeamSpecialistRecentErrorPatternGateV2Report:
    generated_at: datetime
    config_version: str
    gate_status: str
    source_error_count: Decimal
    row_count: Decimal
    team_count: Decimal
    specialist_count: Decimal
    event_archetype_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    blocked_count: Decimal
    repeated_pattern_count: Decimal
    brier_like_error_pattern_count: Decimal
    miss_count_pattern_count: Decimal
    contradiction_mishandling_pattern_count: Decimal
    source_family_weakness_pattern_count: Decimal
    resolution_lag_pattern_count: Decimal
    rows: tuple[TeamSpecialistRecentErrorPatternGateV2Row, ...]
    reason_codes: tuple[str, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_string("config_version", self.config_version)
        _require_member("gate_status", self.gate_status, GATE_STATUSES)
        for field_name in (
            "source_error_count",
            "row_count",
            "team_count",
            "specialist_count",
            "event_archetype_count",
            "pass_count",
            "watch_count",
            "blocked_count",
            "repeated_pattern_count",
            "brier_like_error_pattern_count",
            "miss_count_pattern_count",
            "contradiction_mishandling_pattern_count",
            "source_family_weakness_pattern_count",
            "resolution_lag_pattern_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_count(field_name, getattr(self, field_name)),
            )
        object.__setattr__(self, "rows", _normalize_report_rows(self.rows))
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(
                "reason_codes",
                self.reason_codes,
                REPORT_REASON_CODES,
            ),
        )
        _require_hard_flags("TeamSpecialistRecentErrorPatternGateV2Report", self)
        _reject_unsafe_public_payload(
            "TeamSpecialistRecentErrorPatternGateV2Report",
            self,
        )
        _validate_report(self)
        expected_digest = _report_digest(self)
        if self.derived_validation_digest:
            _require_digest_string(
                "derived_validation_digest",
                self.derived_validation_digest,
            )
            if self.derived_validation_digest != expected_digest:
                raise ValueError("derived_validation_digest must match report contents")
        object.__setattr__(self, "derived_validation_digest", expected_digest)


def build_team_specialist_recent_error_pattern_gate_v2(
    observations: object,
    *,
    config: TeamSpecialistRecentErrorPatternGateV2Config | None = None,
    generated_at: datetime,
) -> TeamSpecialistRecentErrorPatternGateV2Report:
    if config is None:
        config = TeamSpecialistRecentErrorPatternGateV2Config()
    if type(config) is not TeamSpecialistRecentErrorPatternGateV2Config:
        raise ValueError(
            "config must be a TeamSpecialistRecentErrorPatternGateV2Config",
        )
    _require_hard_flags("TeamSpecialistRecentErrorPatternGateV2Config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    source_rows = _normalize_observations(observations)
    report_rows = tuple(
        sorted(
            (
                _row_for_group(group_rows, config=config, generated_at=generated_at_utc)
                for group_rows in _group_observations(source_rows)
            ),
            key=_row_sort_key,
        ),
    )
    blocked_count = _status_count(report_rows, "blocked")
    watch_count = _status_count(report_rows, "watch")

    return TeamSpecialistRecentErrorPatternGateV2Report(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        gate_status=_gate_status(blocked_count, watch_count),
        source_error_count=_count(len(source_rows)),
        row_count=_count(len(report_rows)),
        team_count=_count(len({row.team_id for row in report_rows})),
        specialist_count=_count(len({row.specialist_id for row in report_rows})),
        event_archetype_count=_count(
            len({row.event_archetype for row in report_rows}),
        ),
        pass_count=_status_count(report_rows, "pass"),
        watch_count=watch_count,
        blocked_count=blocked_count,
        repeated_pattern_count=_reason_count(
            report_rows,
            ("recent_repeated_error_pattern",),
        ),
        brier_like_error_pattern_count=_reason_count(
            report_rows,
            ("brier_like_error_blocked", "brier_like_error_watch"),
        ),
        miss_count_pattern_count=_reason_count(
            report_rows,
            ("miss_count_blocked", "miss_count_watch"),
        ),
        contradiction_mishandling_pattern_count=_reason_count(
            report_rows,
            (
                "contradiction_mishandling_blocked",
                "contradiction_mishandling_watch",
            ),
        ),
        source_family_weakness_pattern_count=_reason_count(
            report_rows,
            ("source_family_weakness_blocked", "source_family_weakness_watch"),
        ),
        resolution_lag_pattern_count=_reason_count(
            report_rows,
            ("resolution_lag_blocked", "resolution_lag_watch"),
        ),
        rows=report_rows,
        reason_codes=_report_reason_codes(report_rows, len(source_rows)),
    )


def team_specialist_recent_error_pattern_gate_v2_payload(
    report: TeamSpecialistRecentErrorPatternGateV2Report | dict[str, Any],
) -> dict[str, Any]:
    if type(report) is TeamSpecialistRecentErrorPatternGateV2Report:
        _require_hard_flags("report", report)
        _reject_unsafe_public_payload("recent error pattern report", report)
        payload = _json_ready(report)
    elif type(report) is dict:
        _reject_unsafe_public_payload("recent error pattern payload", report)
        _require_hard_flags("payload", _DictFlags(report))
        payload = _json_ready(report)
        if type(payload) is not dict:
            raise ValueError("report payload must be a JSON object")
        _require_hard_flags("payload", _DictFlags(payload))
        _validate_payload_digest(payload)
    else:
        raise ValueError(
            "report must be a TeamSpecialistRecentErrorPatternGateV2Report",
        )
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    _reject_unsafe_public_payload("recent error pattern payload", payload)
    _require_hard_flags("payload", _DictFlags(payload))
    _validate_payload_digest(payload)
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


def _normalize_observations(
    value: object,
) -> tuple[TeamSpecialistRecentErrorPatternGateV2Observation, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("observations must be a list or tuple")
    rows = tuple(value)
    seen_ids: set[str] = set()
    for row in rows:
        if type(row) is not TeamSpecialistRecentErrorPatternGateV2Observation:
            raise ValueError(
                "observations must contain "
                "TeamSpecialistRecentErrorPatternGateV2Observation values",
            )
        _require_hard_flags("TeamSpecialistRecentErrorPatternGateV2Observation", row)
        if row.error_id in seen_ids:
            raise ValueError("duplicate error_id values are not allowed")
        seen_ids.add(row.error_id)
    return rows


def _group_observations(
    rows: tuple[TeamSpecialistRecentErrorPatternGateV2Observation, ...],
) -> tuple[tuple[TeamSpecialistRecentErrorPatternGateV2Observation, ...], ...]:
    groups: dict[
        tuple[str, str, str, str],
        list[TeamSpecialistRecentErrorPatternGateV2Observation],
    ] = {}
    for row in rows:
        key = (row.team_id, row.category_id, row.specialist_id, row.event_archetype)
        groups.setdefault(key, []).append(row)
    return tuple(tuple(group_rows) for _, group_rows in sorted(groups.items()))


def _row_for_group(
    rows: tuple[TeamSpecialistRecentErrorPatternGateV2Observation, ...],
    *,
    config: TeamSpecialistRecentErrorPatternGateV2Config,
    generated_at: datetime,
) -> TeamSpecialistRecentErrorPatternGateV2Row:
    if not rows:
        raise ValueError("group rows must not be empty")
    recent_rows = tuple(
        (row, _age_seconds(row.evaluated_at, generated_at))
        for row in rows
        if _age_seconds(row.evaluated_at, generated_at) <= config.recent_window_seconds
    )
    recent_observations = tuple(item[0] for item in recent_rows)
    recent_ages = tuple(item[1] for item in recent_rows)
    recent_count = _count(len(recent_observations))
    max_brier_like_error = _max_score(
        tuple(row.brier_like_error for row in recent_observations),
    )
    total_miss_count = _sum_counts(tuple(row.miss_count for row in recent_observations))
    contradiction_mishandled_count = _sum_counts(
        tuple(row.contradiction_mishandled_count for row in recent_observations),
    )
    max_source_family_weakness_score = _max_score(
        tuple(row.source_family_weakness_score for row in recent_observations),
    )
    max_resolution_lag_seconds = _max_seconds(
        tuple(row.resolution_lag_seconds for row in recent_observations),
    )
    gate_status = _row_gate_status(
        recent_count=recent_count,
        max_brier_like_error=max_brier_like_error,
        total_miss_count=total_miss_count,
        contradiction_mishandled_count=contradiction_mishandled_count,
        max_source_family_weakness_score=max_source_family_weakness_score,
        max_resolution_lag_seconds=max_resolution_lag_seconds,
        config=config,
    )
    reason_codes = _row_reason_codes(
        gate_status=gate_status,
        max_brier_like_error=max_brier_like_error,
        total_miss_count=total_miss_count,
        contradiction_mishandled_count=contradiction_mishandled_count,
        max_source_family_weakness_score=max_source_family_weakness_score,
        max_resolution_lag_seconds=max_resolution_lag_seconds,
        config=config,
    )

    first_row = rows[0]
    return TeamSpecialistRecentErrorPatternGateV2Row(
        team_id=first_row.team_id,
        category_id=first_row.category_id,
        specialist_id=first_row.specialist_id,
        event_archetype=first_row.event_archetype,
        gate_status=gate_status,
        source_error_count=_count(len(rows)),
        recent_error_count=recent_count,
        latest_recent_error_age_seconds=_optional_min_seconds(recent_ages),
        oldest_recent_error_age_seconds=_optional_max_seconds(recent_ages),
        max_brier_like_error=max_brier_like_error,
        total_miss_count=total_miss_count,
        contradiction_mishandled_count=contradiction_mishandled_count,
        max_source_family_weakness_score=max_source_family_weakness_score,
        max_resolution_lag_seconds=max_resolution_lag_seconds,
        contributing_error_ids=tuple(sorted(row.error_id for row in recent_observations)),
        reason_codes=reason_codes,
    )


def _row_gate_status(
    *,
    recent_count: Decimal,
    max_brier_like_error: Decimal,
    total_miss_count: Decimal,
    contradiction_mishandled_count: Decimal,
    max_source_family_weakness_score: Decimal,
    max_resolution_lag_seconds: Decimal,
    config: TeamSpecialistRecentErrorPatternGateV2Config,
) -> str:
    if recent_count >= config.blocked_recent_pattern_count and _has_blocked_metric(
        max_brier_like_error=max_brier_like_error,
        total_miss_count=total_miss_count,
        contradiction_mishandled_count=contradiction_mishandled_count,
        max_source_family_weakness_score=max_source_family_weakness_score,
        max_resolution_lag_seconds=max_resolution_lag_seconds,
        config=config,
    ):
        return "blocked"
    if recent_count >= config.watch_recent_pattern_count and _has_watch_metric(
        max_brier_like_error=max_brier_like_error,
        total_miss_count=total_miss_count,
        contradiction_mishandled_count=contradiction_mishandled_count,
        max_source_family_weakness_score=max_source_family_weakness_score,
        max_resolution_lag_seconds=max_resolution_lag_seconds,
        config=config,
    ):
        return "watch"
    return "pass"


def _has_blocked_metric(
    *,
    max_brier_like_error: Decimal,
    total_miss_count: Decimal,
    contradiction_mishandled_count: Decimal,
    max_source_family_weakness_score: Decimal,
    max_resolution_lag_seconds: Decimal,
    config: TeamSpecialistRecentErrorPatternGateV2Config,
) -> bool:
    return (
        max_brier_like_error >= config.blocked_brier_like_error
        or total_miss_count >= config.blocked_miss_count
        or contradiction_mishandled_count >= config.blocked_contradiction_mishandled_count
        or max_source_family_weakness_score >= config.blocked_source_family_weakness
        or max_resolution_lag_seconds >= config.blocked_resolution_lag_seconds
    )


def _has_watch_metric(
    *,
    max_brier_like_error: Decimal,
    total_miss_count: Decimal,
    contradiction_mishandled_count: Decimal,
    max_source_family_weakness_score: Decimal,
    max_resolution_lag_seconds: Decimal,
    config: TeamSpecialistRecentErrorPatternGateV2Config,
) -> bool:
    return (
        max_brier_like_error >= config.watch_brier_like_error
        or total_miss_count >= config.watch_miss_count
        or contradiction_mishandled_count >= config.watch_contradiction_mishandled_count
        or max_source_family_weakness_score >= config.watch_source_family_weakness
        or max_resolution_lag_seconds >= config.watch_resolution_lag_seconds
    )


def _row_reason_codes(
    *,
    gate_status: str,
    max_brier_like_error: Decimal,
    total_miss_count: Decimal,
    contradiction_mishandled_count: Decimal,
    max_source_family_weakness_score: Decimal,
    max_resolution_lag_seconds: Decimal,
    config: TeamSpecialistRecentErrorPatternGateV2Config,
) -> tuple[str, ...]:
    if gate_status == "pass":
        return ("recent_error_pattern_clear",)

    codes = ["recent_repeated_error_pattern"]
    codes.extend(
        _metric_reason(
            value=max_brier_like_error,
            watch_threshold=config.watch_brier_like_error,
            blocked_threshold=config.blocked_brier_like_error,
            watch_reason="brier_like_error_watch",
            blocked_reason="brier_like_error_blocked",
        ),
    )
    codes.extend(
        _metric_reason(
            value=total_miss_count,
            watch_threshold=config.watch_miss_count,
            blocked_threshold=config.blocked_miss_count,
            watch_reason="miss_count_watch",
            blocked_reason="miss_count_blocked",
        ),
    )
    codes.extend(
        _metric_reason(
            value=contradiction_mishandled_count,
            watch_threshold=config.watch_contradiction_mishandled_count,
            blocked_threshold=config.blocked_contradiction_mishandled_count,
            watch_reason="contradiction_mishandling_watch",
            blocked_reason="contradiction_mishandling_blocked",
        ),
    )
    codes.extend(
        _metric_reason(
            value=max_source_family_weakness_score,
            watch_threshold=config.watch_source_family_weakness,
            blocked_threshold=config.blocked_source_family_weakness,
            watch_reason="source_family_weakness_watch",
            blocked_reason="source_family_weakness_blocked",
        ),
    )
    codes.extend(
        _metric_reason(
            value=max_resolution_lag_seconds,
            watch_threshold=config.watch_resolution_lag_seconds,
            blocked_threshold=config.blocked_resolution_lag_seconds,
            watch_reason="resolution_lag_watch",
            blocked_reason="resolution_lag_blocked",
        ),
    )
    return tuple(code for code in ROW_REASON_CODES if code in codes)


def _metric_reason(
    *,
    value: Decimal,
    watch_threshold: Decimal,
    blocked_threshold: Decimal,
    watch_reason: str,
    blocked_reason: str,
) -> tuple[str, ...]:
    if value >= blocked_threshold:
        return (blocked_reason,)
    if value >= watch_threshold:
        return (watch_reason,)
    return ()


def _row_sort_key(
    row: TeamSpecialistRecentErrorPatternGateV2Row,
) -> tuple[int, str, str, str, str]:
    return (
        ROW_SORT_STATUSES.index(row.gate_status),
        row.team_id,
        row.category_id,
        row.specialist_id,
        row.event_archetype,
    )


def _gate_status(blocked_count: Decimal, watch_count: Decimal) -> str:
    if blocked_count > ZERO_COUNT:
        return "blocked"
    if watch_count > ZERO_COUNT:
        return "watch"
    return "pass"


def _status_count(
    rows: tuple[TeamSpecialistRecentErrorPatternGateV2Row, ...],
    gate_status: str,
) -> Decimal:
    return _count(sum(1 for row in rows if row.gate_status == gate_status))


def _reason_count(
    rows: tuple[TeamSpecialistRecentErrorPatternGateV2Row, ...],
    reason_codes: tuple[str, ...],
) -> Decimal:
    return _count(
        sum(
            1
            for row in rows
            if any(reason_code in row.reason_codes for reason_code in reason_codes)
        ),
    )


def _report_reason_codes(
    rows: tuple[TeamSpecialistRecentErrorPatternGateV2Row, ...],
    source_row_count: int,
) -> tuple[str, ...]:
    if source_row_count == 0:
        return ("no_recent_error_patterns_supplied",)
    if all(row.gate_status == "pass" for row in rows):
        return ("recent_error_patterns_clear",)
    codes: list[str] = []
    if any(row.gate_status == "blocked" for row in rows):
        codes.append("blocked_recent_error_patterns_present")
    if any(row.gate_status == "watch" for row in rows):
        codes.append("watch_recent_error_patterns_present")
    if _any_reason(rows, ("brier_like_error_blocked", "brier_like_error_watch")):
        codes.append("brier_like_error_patterns_present")
    if _any_reason(rows, ("miss_count_blocked", "miss_count_watch")):
        codes.append("miss_count_patterns_present")
    if _any_reason(
        rows,
        (
            "contradiction_mishandling_blocked",
            "contradiction_mishandling_watch",
        ),
    ):
        codes.append("contradiction_mishandling_patterns_present")
    if _any_reason(
        rows,
        ("source_family_weakness_blocked", "source_family_weakness_watch"),
    ):
        codes.append("source_family_weakness_patterns_present")
    if _any_reason(rows, ("resolution_lag_blocked", "resolution_lag_watch")):
        codes.append("resolution_lag_patterns_present")
    return tuple(code for code in REPORT_REASON_CODES if code in codes)


def _any_reason(
    rows: tuple[TeamSpecialistRecentErrorPatternGateV2Row, ...],
    reason_codes: tuple[str, ...],
) -> bool:
    return any(
        reason_code in row.reason_codes
        for row in rows
        for reason_code in reason_codes
    )


def _normalize_report_rows(
    value: object,
) -> tuple[TeamSpecialistRecentErrorPatternGateV2Row, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("rows must be a list or tuple")
    rows = tuple(value)
    seen_keys: set[tuple[str, str, str, str]] = set()
    for row in rows:
        if type(row) is not TeamSpecialistRecentErrorPatternGateV2Row:
            raise ValueError(
                "rows must contain TeamSpecialistRecentErrorPatternGateV2Row values",
            )
        _require_hard_flags("TeamSpecialistRecentErrorPatternGateV2Row", row)
        key = (row.team_id, row.category_id, row.specialist_id, row.event_archetype)
        if key in seen_keys:
            raise ValueError("duplicate row identities are not allowed")
        seen_keys.add(key)
    if rows != tuple(sorted(rows, key=_row_sort_key)):
        raise ValueError("rows must be deterministically sorted")
    return rows


def _validate_config(config: TeamSpecialistRecentErrorPatternGateV2Config) -> None:
    if config.watch_recent_pattern_count <= ZERO_COUNT:
        raise ValueError("watch_recent_pattern_count must be positive")
    if config.blocked_recent_pattern_count < config.watch_recent_pattern_count:
        raise ValueError(
            "blocked_recent_pattern_count must not be below watch_recent_pattern_count",
        )
    _require_ordered_threshold(
        "brier_like_error",
        config.watch_brier_like_error,
        config.blocked_brier_like_error,
    )
    _require_ordered_threshold(
        "miss_count",
        config.watch_miss_count,
        config.blocked_miss_count,
    )
    _require_ordered_threshold(
        "contradiction_mishandled_count",
        config.watch_contradiction_mishandled_count,
        config.blocked_contradiction_mishandled_count,
    )
    _require_ordered_threshold(
        "source_family_weakness",
        config.watch_source_family_weakness,
        config.blocked_source_family_weakness,
    )
    _require_ordered_threshold(
        "resolution_lag_seconds",
        config.watch_resolution_lag_seconds,
        config.blocked_resolution_lag_seconds,
    )


def _require_ordered_threshold(
    label: str,
    watch_threshold: Decimal,
    blocked_threshold: Decimal,
) -> None:
    if blocked_threshold < watch_threshold:
        raise ValueError(f"blocked {label} threshold must not be below watch threshold")


def _validate_row(row: TeamSpecialistRecentErrorPatternGateV2Row) -> None:
    if row.recent_error_count > row.source_error_count:
        raise ValueError("recent_error_count must not exceed source_error_count")
    if _count(len(row.contributing_error_ids)) != row.recent_error_count:
        raise ValueError("contributing_error_ids must match recent_error_count")
    if row.recent_error_count == ZERO_COUNT:
        if row.latest_recent_error_age_seconds is not None:
            raise ValueError("latest_recent_error_age_seconds must be empty")
        if row.oldest_recent_error_age_seconds is not None:
            raise ValueError("oldest_recent_error_age_seconds must be empty")
    else:
        if row.latest_recent_error_age_seconds is None:
            raise ValueError("latest_recent_error_age_seconds must be present")
        if row.oldest_recent_error_age_seconds is None:
            raise ValueError("oldest_recent_error_age_seconds must be present")
        if row.latest_recent_error_age_seconds > row.oldest_recent_error_age_seconds:
            raise ValueError("latest recent age must not exceed oldest recent age")
    if row.gate_status == "pass":
        if row.reason_codes != ("recent_error_pattern_clear",):
            raise ValueError("pass rows must use clear reason code")
    elif "recent_repeated_error_pattern" not in row.reason_codes:
        raise ValueError("watch and blocked rows must mark repeated pattern")


def _validate_report(report: TeamSpecialistRecentErrorPatternGateV2Report) -> None:
    rows = report.rows
    if report.row_count != _count(len(rows)):
        raise ValueError("row_count must match rows")
    if report.source_error_count != _sum_counts(
        tuple(row.source_error_count for row in rows),
    ):
        raise ValueError("source_error_count must match rows")
    if report.team_count != _count(len({row.team_id for row in rows})):
        raise ValueError("team_count must match rows")
    if report.specialist_count != _count(len({row.specialist_id for row in rows})):
        raise ValueError("specialist_count must match rows")
    if report.event_archetype_count != _count(
        len({row.event_archetype for row in rows}),
    ):
        raise ValueError("event_archetype_count must match rows")
    expected_counts = {
        "pass_count": _status_count(rows, "pass"),
        "watch_count": _status_count(rows, "watch"),
        "blocked_count": _status_count(rows, "blocked"),
        "repeated_pattern_count": _reason_count(
            rows,
            ("recent_repeated_error_pattern",),
        ),
        "brier_like_error_pattern_count": _reason_count(
            rows,
            ("brier_like_error_blocked", "brier_like_error_watch"),
        ),
        "miss_count_pattern_count": _reason_count(
            rows,
            ("miss_count_blocked", "miss_count_watch"),
        ),
        "contradiction_mishandling_pattern_count": _reason_count(
            rows,
            (
                "contradiction_mishandling_blocked",
                "contradiction_mishandling_watch",
            ),
        ),
        "source_family_weakness_pattern_count": _reason_count(
            rows,
            ("source_family_weakness_blocked", "source_family_weakness_watch"),
        ),
        "resolution_lag_pattern_count": _reason_count(
            rows,
            ("resolution_lag_blocked", "resolution_lag_watch"),
        ),
    }
    for field_name, expected in expected_counts.items():
        if getattr(report, field_name) != expected:
            raise ValueError(f"{field_name} must match rows")
    if report.gate_status != _gate_status(report.blocked_count, report.watch_count):
        raise ValueError("gate_status must match rows")
    if report.reason_codes != _report_reason_codes(rows, int(report.source_error_count)):
        raise ValueError("reason_codes must match rows")


def _validate_payload_digest(payload: dict[str, Any]) -> None:
    digest = payload.get("derived_validation_digest")
    if type(digest) is not str:
        raise ValueError("derived_validation_digest must be present")
    _require_digest_string("derived_validation_digest", digest)
    expected = _digest_for_json_payload(payload)
    if digest != expected:
        raise ValueError("derived_validation_digest must match report contents")


def _report_digest(report: TeamSpecialistRecentErrorPatternGateV2Report) -> str:
    payload = {
        field.name: getattr(report, field.name)
        for field in fields(report)
        if field.name != "derived_validation_digest"
    }
    return _digest_for_json_payload(_json_ready(payload))


def _digest_for_json_payload(payload: dict[str, Any]) -> str:
    payload_without_digest = {
        key: value for key, value in payload.items() if key != "derived_validation_digest"
    }
    canonical_payload = json.dumps(
        payload_without_digest,
        sort_keys=True,
        separators=(",", ":"),
    )
    return sha256(canonical_payload.encode("utf-8")).hexdigest()


def _optional_min_seconds(values: tuple[Decimal, ...]) -> Decimal | None:
    if not values:
        return None
    return min(values)


def _optional_max_seconds(values: tuple[Decimal, ...]) -> Decimal | None:
    if not values:
        return None
    return max(values)


def _max_score(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return ZERO_SCORE
    return max(values)


def _max_seconds(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return ZERO_SECONDS
    return max(values)


def _sum_counts(values: tuple[Decimal, ...]) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return sum(values, ZERO_COUNT).quantize(COUNT_QUANTUM)


def _age_seconds(value: datetime, generated_at: datetime) -> Decimal:
    if value > generated_at:
        return ZERO_SECONDS
    return _seconds_decimal((generated_at - value).total_seconds())


def _seconds_decimal(value: float) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return Decimal(str(value)).quantize(SECONDS_QUANTUM)


def _count(value: int) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return Decimal(value).quantize(COUNT_QUANTUM)


def _normalize_score(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value).quantize(SCORE_QUANTUM)
    if normalized < ZERO_SCORE:
        raise ValueError(f"{field_name} must be nonnegative")
    if normalized > ONE_SCORE:
        raise ValueError(f"{field_name} must be at most 1")
    return normalized


def _normalize_positive_seconds(field_name: str, value: object) -> Decimal:
    normalized = _normalize_nonnegative_seconds(field_name, value)
    if normalized <= ZERO_SECONDS:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _normalize_nonnegative_seconds(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value).quantize(SECONDS_QUANTUM)
    if normalized < ZERO_SECONDS:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _normalize_optional_nonnegative_seconds(
    field_name: str,
    value: object,
) -> Decimal | None:
    if value is None:
        return None
    return _normalize_nonnegative_seconds(field_name, value)


def _normalize_nonnegative_count(field_name: str, value: object) -> Decimal:
    decimal = _require_decimal(field_name, value)
    normalized = decimal.quantize(COUNT_QUANTUM)
    if normalized < ZERO_COUNT:
        raise ValueError(f"{field_name} must be nonnegative")
    if normalized != decimal:
        raise ValueError(f"{field_name} must be a whole number")
    return normalized


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be exactly Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return value


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _normalize_error_ids(value: object) -> tuple[str, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("contributing_error_ids must be a list or tuple")
    error_ids = tuple(value)
    for error_id in error_ids:
        _require_public_string("contributing_error_ids", error_id)
    if len(set(error_ids)) != len(error_ids):
        raise ValueError("contributing_error_ids must be unique")
    if tuple(sorted(error_ids)) != error_ids:
        raise ValueError("contributing_error_ids must be deterministic")
    return error_ids


def _normalize_reason_codes(
    field_name: str,
    value: object,
    allowed: tuple[str, ...],
) -> tuple[str, ...]:
    if type(value) not in (list, tuple):
        raise ValueError(f"{field_name} must be a list or tuple")
    codes = tuple(value)
    if not codes:
        raise ValueError(f"{field_name} must not be empty")
    for code in codes:
        _require_member(field_name, code, allowed)
    if len(set(codes)) != len(codes):
        raise ValueError(f"{field_name} must be unique")
    if tuple(code for code in allowed if code in codes) != codes:
        raise ValueError(f"{field_name} must be deterministic")
    return codes


def _require_public_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value:
        raise ValueError(f"{field_name} must not be empty")
    if value.strip() != value:
        raise ValueError(f"{field_name} must be canonical")
    if "\n" in value or "\r" in value or "\t" in value:
        raise ValueError(f"{field_name} must be single line")
    if _has_unsafe_public_term(value):
        raise ValueError(f"unsafe public value in {field_name}")


def _require_digest_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if len(value) != 64:
        raise ValueError(f"{field_name} must be a sha256 hex digest")
    if any(character not in "0123456789abcdef" for character in value):
        raise ValueError(f"{field_name} must be a sha256 hex digest")


def _require_member(field_name: str, value: object, members: tuple[str, ...]) -> None:
    _require_public_string(field_name, value)
    if value not in members:
        raise ValueError(f"{field_name} must be one of {', '.join(members)}")


def _require_hard_flags(field_name: str, value: object) -> None:
    if getattr(value, "paper_only", None) is not True:
        raise ValueError(f"{field_name} paper_only must be True")
    if getattr(value, "report_only", None) is not True:
        raise ValueError(f"{field_name} report_only must be True")
    if getattr(value, "readonly", None) is not True:
        raise ValueError(f"{field_name} readonly must be True")


def _reject_unsafe_public_payload(label: str, value: object, path: str = "") -> None:
    if is_dataclass(value) and not isinstance(value, type):
        _reject_unsafe_public_payload(label, asdict(value), path)
        return
    if type(value) is str:
        if _has_unsafe_public_term(value):
            raise ValueError(f"{path or label} has unsafe public value")
        if "://" in value or "?" in value:
            raise ValueError(f"{path or label} has unsafe public value")
        return
    if type(value) is Decimal:
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
        raise ValueError("JSON value must not be a float")
    if type(value) is int:
        raise ValueError(f"{path or label} must use Decimal-derived string values")
    if isinstance(value, dict):
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            nested_path = key if not path else f"{path}.{key}"
            if _has_unsafe_public_term(key):
                raise ValueError(f"unsafe public field in {label}: {key}")
            if key in PHASE_FLAG_FIELDS and item is not True:
                raise ValueError(f"{nested_path} must be True")
            _reject_unsafe_public_payload(label, item, nested_path)
        return
    if isinstance(value, (list, tuple)):
        for index, item in enumerate(value):
            nested_path = f"{path}[{index}]" if path else f"{label}[{index}]"
            _reject_unsafe_public_payload(label, item, nested_path)
        return
    raise ValueError("value is not JSON serializable")


def _has_unsafe_public_term(value: str) -> bool:
    normalized = value.lower()
    return any(term in normalized for term in UNSAFE_PUBLIC_TERMS)


def _json_ready(value: Any) -> Any:
    if value is None:
        return None
    if is_dataclass(value) and not isinstance(value, type):
        return _json_ready(asdict(value))
    if type(value) is Decimal:
        if not value.is_finite():
            raise ValueError("JSON Decimal value must be finite")
        return str(value)
    if isinstance(value, datetime):
        if type(value) is not datetime:
            raise ValueError("JSON datetime value must be a datetime")
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("JSON datetime value must be timezone-aware")
        return value.astimezone(UTC).isoformat()
    if isinstance(value, float):
        raise ValueError("JSON value must not be a float")
    if type(value) is int:
        raise ValueError("JSON numeric values must be Decimal-derived strings")
    if type(value) is dict:
        return {key: _json_ready(item) for key, item in value.items()}
    if type(value) in (list, tuple):
        return [_json_ready(item) for item in value]
    if type(value) in (str, bool):
        return value
    raise ValueError("value is not JSON serializable")
