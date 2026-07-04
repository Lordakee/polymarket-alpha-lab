"""Pure Phase 1 information velocity digest."""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable
from dataclasses import asdict, dataclass, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from typing import Any

from polymarket_alpha_lab.team_paper_guard import require_paper_only_flags


__all__ = (
    "DEFAULT_STRATEGY_TEAM_INFORMATION_VELOCITY_DIGEST_CONFIG_VERSION",
    "REDACTED_PUBLIC_REFERENCE",
    "StrategyTeamInformationVelocityDigestConfig",
    "StrategyTeamInformationVelocityDigestReasonCodeCount",
    "StrategyTeamInformationVelocityDigestReport",
    "StrategyTeamInformationVelocityDigestRow",
    "StrategyTeamInformationVelocityInput",
    "build_strategy_team_information_velocity_digest",
    "strategy_team_information_velocity_digest_payload",
)


DEFAULT_STRATEGY_TEAM_INFORMATION_VELOCITY_DIGEST_CONFIG_VERSION = (
    "strategy-team-information-velocity-digest-v0"
)
REDACTED_PUBLIC_REFERENCE = "[redacted-reference]"
PUBLIC_REFERENCE_FIELD = "public_reference"

STATUSES = ("accelerate", "maintain", "pause")
REPORT_STATUSES = ("accelerate", "watch", "pause")
NEXT_STEP_BY_STATUS = {
    "accelerate": "accelerate_paper_research_coverage",
    "watch": "review_information_velocity_watch_items",
    "pause": "pause_paper_research_coverage",
}
STATUS_WEIGHT = {
    "accelerate": Decimal("0.000000"),
    "maintain": Decimal("1.000000"),
    "pause": Decimal("2.000000"),
}

EVIDENCE_FRESH_REASON = "evidence_fresh"
EVIDENCE_STALE_WATCH_REASON = "evidence_stale_watch"
EVIDENCE_STALE_PAUSE_REASON = "evidence_stale_pause"
VELOCITY_ACCELERATE_REASON = "information_velocity_accelerate"
VELOCITY_HIGH_REASON = "information_velocity_high"
VELOCITY_LOW_REASON = "information_velocity_low"
VELOCITY_MAINTAIN_REASON = "information_velocity_maintain"
VELOCITY_PAUSE_REASON = "information_velocity_pause"
VELOCITY_WATCH_REASON = "information_velocity_watch"
SOURCE_DEPTH_LOW_REASON = "source_depth_low"
SOURCE_DEPTH_SUFFICIENT_REASON = "source_depth_sufficient"
REPORT_ACCELERATE_REASON = "strategy_team_information_velocity_accelerate"
REPORT_WATCH_REASON = "strategy_team_information_velocity_watch"
REPORT_PAUSE_REASON = "strategy_team_information_velocity_pause"
EMPTY_REASON = "strategy_team_information_velocity_digest_empty"
CADENCE_CURRENT_REASON = "update_cadence_current"
CADENCE_SLOW_PAUSE_REASON = "update_cadence_slow_pause"
CADENCE_SLOW_WATCH_REASON = "update_cadence_slow_watch"

ROW_REASON_CODES = (
    EVIDENCE_FRESH_REASON,
    EVIDENCE_STALE_PAUSE_REASON,
    EVIDENCE_STALE_WATCH_REASON,
    VELOCITY_ACCELERATE_REASON,
    VELOCITY_HIGH_REASON,
    VELOCITY_LOW_REASON,
    VELOCITY_MAINTAIN_REASON,
    VELOCITY_PAUSE_REASON,
    VELOCITY_WATCH_REASON,
    SOURCE_DEPTH_LOW_REASON,
    SOURCE_DEPTH_SUFFICIENT_REASON,
    CADENCE_CURRENT_REASON,
    CADENCE_SLOW_PAUSE_REASON,
    CADENCE_SLOW_WATCH_REASON,
)
REPORT_REASON_CODES = tuple(
    sorted(
        (
            *ROW_REASON_CODES,
            REPORT_ACCELERATE_REASON,
            REPORT_WATCH_REASON,
            REPORT_PAUSE_REASON,
            EMPTY_REASON,
        ),
    ),
)
PAUSE_REASON_CODES = frozenset(
    (
        EVIDENCE_STALE_PAUSE_REASON,
        VELOCITY_LOW_REASON,
        CADENCE_SLOW_PAUSE_REASON,
    ),
)

QUANTUM = Decimal("0.000001")
COUNT_QUANTUM = Decimal("1.000000")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
SECONDS_PER_DAY = Decimal("86400")
MICROSECONDS_PER_SECOND = Decimal("1000000")
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
VELOCITY_WEIGHT = Decimal("0.400000")
CADENCE_WEIGHT = Decimal("0.250000")
FRESHNESS_WEIGHT = Decimal("0.250000")
SOURCE_DEPTH_WEIGHT = Decimal("0.100000")
PHASE_FLAG_FIELDS = frozenset(("paper_only", "report_only", "readonly"))
BOUNDARY_STATEMENT = "Paper-only readonly information velocity report."


def _join_parts(*parts: str) -> str:
    return "".join(parts)


UNSAFE_TEXT_FRAGMENTS = frozenset(
    (
        _join_parts("api", "_key"),
        _join_parts("au", "th"),
        _join_parts("bear", "er"),
        _join_parts("bro", "ker"),
        _join_parts("can", "cel"),
        _join_parts("cre", "dential"),
        _join_parts("ex", "change_mutation"),
        _join_parts("live", "_tra", "ding"),
        _join_parts("ord", "er"),
        _join_parts("pass", "word"),
        _join_parts("pri", "vate"),
        _join_parts("pri", "vate_key"),
        _join_parts("re", "place"),
        _join_parts("sec", "ret"),
        _join_parts("si", "gn"),
        _join_parts("si", "gning"),
        _join_parts("to", "ken"),
        _join_parts("wal", "let"),
    ),
)


@dataclass(frozen=True)
class StrategyTeamInformationVelocityDigestConfig:
    config_version: str = DEFAULT_STRATEGY_TEAM_INFORMATION_VELOCITY_DIGEST_CONFIG_VERSION
    target_update_count: Decimal = Decimal("6.000000")
    watch_update_count: Decimal = Decimal("2.000000")
    maximum_current_cadence_seconds: Decimal = Decimal("3600.000000")
    watch_cadence_seconds: Decimal = Decimal("7200.000000")
    maximum_fresh_evidence_age_seconds: Decimal = Decimal("1800.000000")
    watch_evidence_age_seconds: Decimal = Decimal("7200.000000")
    minimum_distinct_source_count: Decimal = Decimal("2.000000")
    accelerate_information_velocity_score: Decimal = Decimal("0.750000")
    watch_information_velocity_score: Decimal = Decimal("0.400000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("config_version", self.config_version)
        for field_name in (
            "target_update_count",
            "maximum_current_cadence_seconds",
            "watch_cadence_seconds",
            "maximum_fresh_evidence_age_seconds",
            "watch_evidence_age_seconds",
            "minimum_distinct_source_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_positive_count(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "watch_update_count",
            _normalize_nonnegative_count("watch_update_count", self.watch_update_count),
        )
        for field_name in (
            "accelerate_information_velocity_score",
            "watch_information_velocity_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        if self.watch_update_count > self.target_update_count:
            raise ValueError("watch_update_count must not exceed target_update_count")
        _require_at_most(
            "maximum_current_cadence_seconds",
            self.maximum_current_cadence_seconds,
            self.watch_cadence_seconds,
        )
        _require_at_most(
            "maximum_fresh_evidence_age_seconds",
            self.maximum_fresh_evidence_age_seconds,
            self.watch_evidence_age_seconds,
        )
        if (
            self.watch_information_velocity_score
            > self.accelerate_information_velocity_score
        ):
            raise ValueError(
                "watch_information_velocity_score must not exceed "
                "accelerate_information_velocity_score",
            )
        require_paper_only_flags("StrategyTeamInformationVelocityDigestConfig", self)


@dataclass(frozen=True)
class StrategyTeamInformationVelocityInput:
    team_id: str
    category_id: str
    coverage_window_started_at: datetime
    latest_evidence_at: datetime
    update_count: Decimal
    evidence_item_count: Decimal
    distinct_source_count: Decimal
    public_reference: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("team_id", self.team_id)
        _require_canonical_string("category_id", self.category_id)
        object.__setattr__(
            self,
            "coverage_window_started_at",
            _as_utc("coverage_window_started_at", self.coverage_window_started_at),
        )
        object.__setattr__(
            self,
            "latest_evidence_at",
            _as_utc("latest_evidence_at", self.latest_evidence_at),
        )
        if self.coverage_window_started_at > self.latest_evidence_at:
            raise ValueError("coverage_window_started_at must not be after latest_evidence_at")
        for field_name in (
            "update_count",
            "evidence_item_count",
            "distinct_source_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_count(field_name, getattr(self, field_name)),
            )
        _require_reference_string("public_reference", self.public_reference)
        object.__setattr__(
            self,
            "public_reference",
            _redact_public_reference(self.public_reference),
        )
        require_paper_only_flags("StrategyTeamInformationVelocityInput", self)


@dataclass(frozen=True)
class StrategyTeamInformationVelocityDigestRow:
    rank: Decimal
    team_id: str
    category_id: str
    velocity_status: str
    information_velocity_score: Decimal
    coverage_window_started_at: datetime
    latest_evidence_at: datetime
    update_count: Decimal
    evidence_item_count: Decimal
    distinct_source_count: Decimal
    window_age_seconds: Decimal
    update_cadence_seconds: Decimal
    evidence_age_seconds: Decimal
    redacted_public_reference: str
    reason_codes: tuple[str, ...]
    boundary_statement: str = BOUNDARY_STATEMENT
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "rank", _normalize_positive_count("rank", self.rank))
        _require_canonical_string("team_id", self.team_id)
        _require_canonical_string("category_id", self.category_id)
        _require_member("velocity_status", self.velocity_status, STATUSES)
        object.__setattr__(
            self,
            "information_velocity_score",
            _normalize_ratio(
                "information_velocity_score",
                self.information_velocity_score,
            ),
        )
        object.__setattr__(
            self,
            "coverage_window_started_at",
            _as_utc("coverage_window_started_at", self.coverage_window_started_at),
        )
        object.__setattr__(
            self,
            "latest_evidence_at",
            _as_utc("latest_evidence_at", self.latest_evidence_at),
        )
        if self.coverage_window_started_at > self.latest_evidence_at:
            raise ValueError("coverage_window_started_at must not be after latest_evidence_at")
        for field_name in (
            "update_count",
            "evidence_item_count",
            "distinct_source_count",
            "window_age_seconds",
            "update_cadence_seconds",
            "evidence_age_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_count(field_name, getattr(self, field_name)),
            )
        _require_canonical_string(
            "redacted_public_reference",
            self.redacted_public_reference,
        )
        if _contains_unsafe_text(self.redacted_public_reference):
            raise ValueError("redacted_public_reference is unsafe")
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(
                "reason_codes",
                self.reason_codes,
                ROW_REASON_CODES,
            ),
        )
        _require_boundary_statement(self.boundary_statement)
        if self.velocity_status != _status_from_reason_codes(self.reason_codes):
            raise ValueError("velocity_status must match reason_codes")
        require_paper_only_flags("StrategyTeamInformationVelocityDigestRow", self)


@dataclass(frozen=True)
class StrategyTeamInformationVelocityDigestReasonCodeCount:
    reason_code: str
    count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_reason_code("reason_code", self.reason_code, REPORT_REASON_CODES)
        object.__setattr__(self, "count", _normalize_nonnegative_count("count", self.count))
        require_paper_only_flags(
            "StrategyTeamInformationVelocityDigestReasonCodeCount",
            self,
        )


@dataclass(frozen=True)
class StrategyTeamInformationVelocityDigestReport:
    generated_at: datetime
    config_version: str
    team_category_count: Decimal
    team_count: Decimal
    category_count: Decimal
    accelerate_count: Decimal
    maintain_count: Decimal
    pause_count: Decimal
    max_information_velocity_score: Decimal
    average_information_velocity_score: Decimal
    digest_status: str
    next_step: str
    accelerated_team_category_ids: tuple[str, ...]
    reason_codes: tuple[str, ...]
    reason_code_counts: tuple[StrategyTeamInformationVelocityDigestReasonCodeCount, ...]
    rows: tuple[StrategyTeamInformationVelocityDigestRow, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        for field_name in (
            "team_category_count",
            "team_count",
            "category_count",
            "accelerate_count",
            "maintain_count",
            "pause_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_count(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "max_information_velocity_score",
            "average_information_velocity_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        _require_member("digest_status", self.digest_status, REPORT_STATUSES)
        _require_canonical_string("next_step", self.next_step)
        object.__setattr__(
            self,
            "accelerated_team_category_ids",
            _normalize_team_category_ids(self.accelerated_team_category_ids),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(
                "reason_codes",
                self.reason_codes,
                REPORT_REASON_CODES,
            ),
        )
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        _validate_report(self)
        require_paper_only_flags("StrategyTeamInformationVelocityDigestReport", self)


def build_strategy_team_information_velocity_digest(
    input_rows: Iterable[StrategyTeamInformationVelocityInput],
    *,
    config: StrategyTeamInformationVelocityDigestConfig,
    generated_at: datetime,
) -> StrategyTeamInformationVelocityDigestReport:
    if type(config) is not StrategyTeamInformationVelocityDigestConfig:
        raise ValueError("config must be a StrategyTeamInformationVelocityDigestConfig")
    require_paper_only_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    rows = _normalize_inputs(input_rows, generated_at=generated_at_utc)
    unranked_rows = tuple(
        _digest_row(row, config=config, generated_at=generated_at_utc)
        for row in rows
    )
    digest_rows = tuple(
        _ranked_row(row, rank=index)
        for index, row in enumerate(sorted(unranked_rows, key=_row_sort_key), start=1)
    )
    digest_status = _digest_status(digest_rows)
    return StrategyTeamInformationVelocityDigestReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        team_category_count=_count(len(digest_rows)),
        team_count=_count(len({row.team_id for row in digest_rows})),
        category_count=_count(len({row.category_id for row in digest_rows})),
        accelerate_count=_status_count(digest_rows, "accelerate"),
        maintain_count=_status_count(digest_rows, "maintain"),
        pause_count=_status_count(digest_rows, "pause"),
        max_information_velocity_score=_max_information_velocity_score(digest_rows),
        average_information_velocity_score=_average_information_velocity_score(
            digest_rows,
        ),
        digest_status=digest_status,
        next_step=NEXT_STEP_BY_STATUS[digest_status],
        accelerated_team_category_ids=tuple(
            f"{row.team_id}:{row.category_id}"
            for row in digest_rows
            if row.velocity_status == "accelerate"
        ),
        reason_codes=_report_reason_codes(digest_rows, status=digest_status),
        reason_code_counts=_reason_code_counts(digest_rows, status=digest_status),
        rows=digest_rows,
    )


def strategy_team_information_velocity_digest_payload(
    report: StrategyTeamInformationVelocityDigestReport | dict[str, Any],
) -> dict[str, Any]:
    if type(report) is StrategyTeamInformationVelocityDigestReport:
        require_paper_only_flags("report", report)
        _reject_unsafe_public_values("report", report)
        payload = _json_ready(report)
    elif type(report) is dict:
        _reject_flag_downgrades("payload", report)
        _reject_unsafe_public_values("payload", report)
        payload = _json_ready(report)
    else:
        raise ValueError("report must be a StrategyTeamInformationVelocityDigestReport")
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    _reject_flag_downgrades("payload", payload)
    require_paper_only_flags("payload", _DictFlags(payload))
    _reject_unsafe_public_values("payload", payload)
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


def _digest_row(
    row: StrategyTeamInformationVelocityInput,
    *,
    config: StrategyTeamInformationVelocityDigestConfig,
    generated_at: datetime,
) -> StrategyTeamInformationVelocityDigestRow:
    window_age_seconds = _age_seconds(row.coverage_window_started_at, generated_at)
    evidence_age_seconds = _age_seconds(row.latest_evidence_at, generated_at)
    update_cadence_seconds = _update_cadence_seconds(
        window_age_seconds,
        row.update_count,
    )
    information_velocity_score = _information_velocity_score(
        row,
        update_cadence_seconds=update_cadence_seconds,
        evidence_age_seconds=evidence_age_seconds,
        config=config,
    )
    reason_codes = _row_reason_codes(
        row,
        update_cadence_seconds=update_cadence_seconds,
        evidence_age_seconds=evidence_age_seconds,
        information_velocity_score=information_velocity_score,
        config=config,
    )
    return StrategyTeamInformationVelocityDigestRow(
        rank=COUNT_QUANTUM,
        team_id=row.team_id,
        category_id=row.category_id,
        velocity_status=_row_status(reason_codes, information_velocity_score, config),
        information_velocity_score=information_velocity_score,
        coverage_window_started_at=row.coverage_window_started_at,
        latest_evidence_at=row.latest_evidence_at,
        update_count=row.update_count,
        evidence_item_count=row.evidence_item_count,
        distinct_source_count=row.distinct_source_count,
        window_age_seconds=window_age_seconds,
        update_cadence_seconds=update_cadence_seconds,
        evidence_age_seconds=evidence_age_seconds,
        redacted_public_reference=row.public_reference,
        reason_codes=reason_codes,
    )


def _ranked_row(
    row: StrategyTeamInformationVelocityDigestRow,
    *,
    rank: int,
) -> StrategyTeamInformationVelocityDigestRow:
    return StrategyTeamInformationVelocityDigestRow(
        rank=_count(rank),
        team_id=row.team_id,
        category_id=row.category_id,
        velocity_status=row.velocity_status,
        information_velocity_score=row.information_velocity_score,
        coverage_window_started_at=row.coverage_window_started_at,
        latest_evidence_at=row.latest_evidence_at,
        update_count=row.update_count,
        evidence_item_count=row.evidence_item_count,
        distinct_source_count=row.distinct_source_count,
        window_age_seconds=row.window_age_seconds,
        update_cadence_seconds=row.update_cadence_seconds,
        evidence_age_seconds=row.evidence_age_seconds,
        redacted_public_reference=row.redacted_public_reference,
        reason_codes=row.reason_codes,
        boundary_statement=row.boundary_statement,
    )


def _information_velocity_score(
    row: StrategyTeamInformationVelocityInput,
    *,
    update_cadence_seconds: Decimal,
    evidence_age_seconds: Decimal,
    config: StrategyTeamInformationVelocityDigestConfig,
) -> Decimal:
    update_velocity_score = _ratio(
        min(row.update_count, config.target_update_count),
        config.target_update_count,
    )
    cadence_score = _remaining_ratio(
        update_cadence_seconds,
        config.watch_cadence_seconds,
    )
    freshness_score = _remaining_ratio(
        evidence_age_seconds,
        config.watch_evidence_age_seconds,
    )
    source_depth_score = _ratio(
        min(row.distinct_source_count, config.minimum_distinct_source_count),
        config.minimum_distinct_source_count,
    )
    with localcontext(DECIMAL_CONTEXT):
        return _normalize_ratio(
            "information_velocity_score",
            (update_velocity_score * VELOCITY_WEIGHT)
            + (cadence_score * CADENCE_WEIGHT)
            + (freshness_score * FRESHNESS_WEIGHT)
            + (source_depth_score * SOURCE_DEPTH_WEIGHT),
        )


def _row_reason_codes(
    row: StrategyTeamInformationVelocityInput,
    *,
    update_cadence_seconds: Decimal,
    evidence_age_seconds: Decimal,
    information_velocity_score: Decimal,
    config: StrategyTeamInformationVelocityDigestConfig,
) -> tuple[str, ...]:
    reason_codes = [
        _velocity_reason(row.update_count, config),
        _cadence_reason(update_cadence_seconds, config),
        _evidence_reason(evidence_age_seconds, config),
        (
            SOURCE_DEPTH_SUFFICIENT_REASON
            if row.distinct_source_count >= config.minimum_distinct_source_count
            else SOURCE_DEPTH_LOW_REASON
        ),
    ]
    reason_codes.append(
        _status_reason(
            _row_status(
                _normalize_reason_codes(
                    "reason_codes",
                    tuple(reason_codes),
                    ROW_REASON_CODES,
                ),
                information_velocity_score,
                config,
            ),
        ),
    )
    return _normalize_reason_codes("reason_codes", tuple(reason_codes), ROW_REASON_CODES)


def _velocity_reason(
    update_count: Decimal,
    config: StrategyTeamInformationVelocityDigestConfig,
) -> str:
    if update_count >= config.target_update_count:
        return VELOCITY_HIGH_REASON
    if update_count >= config.watch_update_count:
        return VELOCITY_WATCH_REASON
    return VELOCITY_LOW_REASON


def _cadence_reason(
    update_cadence_seconds: Decimal,
    config: StrategyTeamInformationVelocityDigestConfig,
) -> str:
    if update_cadence_seconds <= config.maximum_current_cadence_seconds:
        return CADENCE_CURRENT_REASON
    if update_cadence_seconds <= config.watch_cadence_seconds:
        return CADENCE_SLOW_WATCH_REASON
    return CADENCE_SLOW_PAUSE_REASON


def _evidence_reason(
    evidence_age_seconds: Decimal,
    config: StrategyTeamInformationVelocityDigestConfig,
) -> str:
    if evidence_age_seconds <= config.maximum_fresh_evidence_age_seconds:
        return EVIDENCE_FRESH_REASON
    if evidence_age_seconds <= config.watch_evidence_age_seconds:
        return EVIDENCE_STALE_WATCH_REASON
    return EVIDENCE_STALE_PAUSE_REASON


def _row_status(
    reason_codes: tuple[str, ...],
    information_velocity_score: Decimal,
    config: StrategyTeamInformationVelocityDigestConfig,
) -> str:
    if any(reason_code in PAUSE_REASON_CODES for reason_code in reason_codes):
        return "pause"
    if information_velocity_score >= config.accelerate_information_velocity_score:
        return "accelerate"
    if information_velocity_score >= config.watch_information_velocity_score:
        return "maintain"
    return "pause"


def _status_reason(status: str) -> str:
    if status == "accelerate":
        return VELOCITY_ACCELERATE_REASON
    if status == "maintain":
        return VELOCITY_MAINTAIN_REASON
    return VELOCITY_PAUSE_REASON


def _status_from_reason_codes(reason_codes: tuple[str, ...]) -> str:
    status_reasons = tuple(
        reason_code
        for reason_code in reason_codes
        if reason_code
        in (
            VELOCITY_ACCELERATE_REASON,
            VELOCITY_MAINTAIN_REASON,
            VELOCITY_PAUSE_REASON,
        )
    )
    if len(status_reasons) != 1:
        raise ValueError("reason_codes must contain one velocity status reason")
    if status_reasons[0] == VELOCITY_ACCELERATE_REASON:
        return "accelerate"
    if status_reasons[0] == VELOCITY_MAINTAIN_REASON:
        return "maintain"
    return "pause"


def _digest_status(rows: tuple[StrategyTeamInformationVelocityDigestRow, ...]) -> str:
    if not rows:
        return "pause"
    if any(row.velocity_status == "accelerate" for row in rows):
        return "accelerate"
    if all(row.velocity_status == "pause" for row in rows):
        return "pause"
    return "watch"


def _report_reason_codes(
    rows: tuple[StrategyTeamInformationVelocityDigestRow, ...],
    *,
    status: str,
) -> tuple[str, ...]:
    if not rows:
        return (EMPTY_REASON,)
    reason_codes = [_report_status_reason(status)]
    for row in rows:
        reason_codes.extend(row.reason_codes)
    return _normalize_reason_codes("reason_codes", tuple(reason_codes), REPORT_REASON_CODES)


def _report_status_reason(status: str) -> str:
    if status == "accelerate":
        return REPORT_ACCELERATE_REASON
    if status == "watch":
        return REPORT_WATCH_REASON
    return REPORT_PAUSE_REASON


def _reason_code_counts(
    rows: tuple[StrategyTeamInformationVelocityDigestRow, ...],
    *,
    status: str,
) -> tuple[StrategyTeamInformationVelocityDigestReasonCodeCount, ...]:
    if not rows:
        return (
            StrategyTeamInformationVelocityDigestReasonCodeCount(
                reason_code=EMPTY_REASON,
                count=ZERO,
            ),
        )
    counter: Counter[str] = Counter()
    counter.update((_report_status_reason(status),))
    for row in rows:
        counter.update(row.reason_codes)
    return tuple(
        StrategyTeamInformationVelocityDigestReasonCodeCount(
            reason_code=reason_code,
            count=_count(count),
        )
        for reason_code, count in sorted(counter.items(), key=lambda item: (-item[1], item[0]))
    )


def _normalize_inputs(
    input_rows: Iterable[StrategyTeamInformationVelocityInput],
    *,
    generated_at: datetime,
) -> tuple[StrategyTeamInformationVelocityInput, ...]:
    if isinstance(input_rows, (str, bytes)):
        raise ValueError("input_rows must be an iterable")
    try:
        rows = tuple(input_rows)
    except TypeError as exc:
        raise ValueError("input_rows must be an iterable") from exc
    seen: set[tuple[str, str]] = set()
    for row in rows:
        if type(row) is not StrategyTeamInformationVelocityInput:
            raise ValueError(
                "input_rows must contain StrategyTeamInformationVelocityInput values",
            )
        require_paper_only_flags("input", row)
        if row.latest_evidence_at > generated_at:
            raise ValueError("latest_evidence_at must not be after generated_at")
        if row.coverage_window_started_at > generated_at:
            raise ValueError("coverage_window_started_at must not be after generated_at")
        key = (row.team_id, row.category_id)
        if key in seen:
            raise ValueError("input_rows must not contain duplicate team and category values")
        seen.add(key)
    return rows


def _normalize_rows(
    rows: object,
) -> tuple[StrategyTeamInformationVelocityDigestRow, ...]:
    if isinstance(rows, (str, bytes)):
        raise ValueError("rows must be an iterable")
    try:
        values = tuple(rows)  # type: ignore[arg-type]
    except TypeError as exc:
        raise ValueError("rows must be an iterable") from exc
    seen: set[tuple[str, str]] = set()
    for row in values:
        if type(row) is not StrategyTeamInformationVelocityDigestRow:
            raise ValueError(
                "rows must contain StrategyTeamInformationVelocityDigestRow values",
            )
        require_paper_only_flags("row", row)
        key = (row.team_id, row.category_id)
        if key in seen:
            raise ValueError("rows must not contain duplicate team and category values")
        seen.add(key)
    if values != tuple(sorted(values, key=_row_sort_key)):
        raise ValueError("rows must be deterministic")
    expected_ranks = tuple(_count(index) for index in range(1, len(values) + 1))
    if tuple(row.rank for row in values) != expected_ranks:
        raise ValueError("rows must use sequential ranks")
    return values


def _normalize_reason_code_counts(
    rows: object,
) -> tuple[StrategyTeamInformationVelocityDigestReasonCodeCount, ...]:
    if isinstance(rows, (str, bytes)):
        raise ValueError("reason_code_counts must be an iterable")
    try:
        values = tuple(rows)  # type: ignore[arg-type]
    except TypeError as exc:
        raise ValueError("reason_code_counts must be an iterable") from exc
    seen: set[str] = set()
    previous_key: tuple[Decimal, str] | None = None
    for row in values:
        if type(row) is not StrategyTeamInformationVelocityDigestReasonCodeCount:
            raise ValueError("reason_code_counts must contain reason count rows")
        require_paper_only_flags("reason_code_count", row)
        if row.reason_code in seen:
            raise ValueError("reason_code_counts must be unique")
        key = (-row.count, row.reason_code)
        if previous_key is not None and previous_key > key:
            raise ValueError("reason_code_counts must be deterministic")
        previous_key = key
        seen.add(row.reason_code)
    return values


def _normalize_team_category_ids(value: object) -> tuple[str, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("accelerated_team_category_ids must be a list or tuple")
    team_category_ids = tuple(value)
    seen: set[str] = set()
    for team_category_id in team_category_ids:
        _require_canonical_string("accelerated_team_category_ids", team_category_id)
        if team_category_id in seen:
            raise ValueError("accelerated_team_category_ids must be unique")
        seen.add(team_category_id)
    return team_category_ids


def _validate_report(report: StrategyTeamInformationVelocityDigestReport) -> None:
    rows = report.rows
    if report.team_category_count != _count(len(rows)):
        raise ValueError("team_category_count must match rows")
    if report.team_count != _count(len({row.team_id for row in rows})):
        raise ValueError("team_count must match rows")
    if report.category_count != _count(len({row.category_id for row in rows})):
        raise ValueError("category_count must match rows")
    for field_name, status in (
        ("accelerate_count", "accelerate"),
        ("maintain_count", "maintain"),
        ("pause_count", "pause"),
    ):
        if getattr(report, field_name) != _status_count(rows, status):
            raise ValueError(f"{field_name} must match rows")
    if report.max_information_velocity_score != _max_information_velocity_score(rows):
        raise ValueError("max_information_velocity_score must match rows")
    if report.average_information_velocity_score != _average_information_velocity_score(
        rows,
    ):
        raise ValueError("average_information_velocity_score must match rows")
    if report.digest_status != _digest_status(rows):
        raise ValueError("digest_status must match rows")
    if report.next_step != NEXT_STEP_BY_STATUS[report.digest_status]:
        raise ValueError("next_step must match digest_status")
    if report.accelerated_team_category_ids != tuple(
        f"{row.team_id}:{row.category_id}"
        for row in rows
        if row.velocity_status == "accelerate"
    ):
        raise ValueError("accelerated_team_category_ids must match rows")
    if report.reason_codes != _report_reason_codes(rows, status=report.digest_status):
        raise ValueError("reason_codes must match rows")
    if report.reason_code_counts != _reason_code_counts(rows, status=report.digest_status):
        raise ValueError("reason_code_counts must match rows")


def _row_sort_key(
    row: StrategyTeamInformationVelocityDigestRow,
) -> tuple[Decimal, Decimal, Decimal, str, str]:
    return (
        STATUS_WEIGHT[row.velocity_status],
        -row.information_velocity_score,
        -row.update_count,
        row.category_id,
        row.team_id,
    )


def _status_count(
    rows: tuple[StrategyTeamInformationVelocityDigestRow, ...],
    status: str,
) -> Decimal:
    return _count(sum(1 for row in rows if row.velocity_status == status))


def _max_information_velocity_score(
    rows: tuple[StrategyTeamInformationVelocityDigestRow, ...],
) -> Decimal:
    if not rows:
        return ZERO
    return _normalize_ratio(
        "max_information_velocity_score",
        max(row.information_velocity_score for row in rows),
    )


def _average_information_velocity_score(
    rows: tuple[StrategyTeamInformationVelocityDigestRow, ...],
) -> Decimal:
    if not rows:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return _normalize_ratio(
            "average_information_velocity_score",
            sum(row.information_velocity_score for row in rows) / Decimal(len(rows)),
        )


def _update_cadence_seconds(window_age_seconds: Decimal, update_count: Decimal) -> Decimal:
    if update_count <= ZERO:
        return window_age_seconds
    return _normalize_nonnegative_count("update_cadence_seconds", window_age_seconds / update_count)


def _age_seconds(observed_at: datetime, generated_at: datetime) -> Decimal:
    delta = _as_utc("generated_at", generated_at) - _as_utc("observed_at", observed_at)
    seconds = (
        Decimal(delta.days) * SECONDS_PER_DAY
        + Decimal(delta.seconds)
        + (Decimal(delta.microseconds) / MICROSECONDS_PER_SECOND)
    )
    age_seconds = _normalize_nonnegative_count("age_seconds", seconds)
    if age_seconds < ZERO:
        raise ValueError("observed_at must not be after generated_at")
    return age_seconds


def _remaining_ratio(value: Decimal, limit: Decimal) -> Decimal:
    if value >= limit:
        return ZERO
    return _normalize_ratio("remaining_ratio", ONE - _ratio(value, limit))


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator <= ZERO:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return _normalize_ratio("ratio", numerator / denominator)


def _count(value: int) -> Decimal:
    return Decimal(value).quantize(COUNT_QUANTUM)


def _normalize_positive_count(field_name: str, value: object) -> Decimal:
    normalized = _normalize_nonnegative_count(field_name, value)
    if normalized <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _normalize_nonnegative_count(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    with localcontext(DECIMAL_CONTEXT):
        quantized = value.quantize(QUANTUM)
    if quantized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return quantized


def _normalize_ratio(field_name: str, value: object) -> Decimal:
    normalized = _normalize_nonnegative_count(field_name, value)
    if normalized > ONE:
        raise ValueError(f"{field_name} must be between zero and one")
    return normalized


def _require_at_most(field_name: str, low_value: Decimal, high_value: Decimal) -> None:
    if low_value > high_value:
        raise ValueError(f"{field_name} must not exceed watch threshold")


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be exactly datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a non-empty canonical string")
    if any(character.isspace() for character in value):
        raise ValueError(f"{field_name} must not contain whitespace")
    if _contains_unsafe_text(value):
        raise ValueError(f"{field_name} is unsafe")


def _require_reference_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a non-empty canonical string")
    if any(character.isspace() for character in value):
        raise ValueError(f"{field_name} must not contain whitespace")


def _require_member(field_name: str, value: object, allowed_values: tuple[str, ...]) -> None:
    if type(value) is not str or value not in allowed_values:
        raise ValueError(f"{field_name} must be one of {allowed_values}")


def _require_boundary_statement(value: object) -> None:
    if value != BOUNDARY_STATEMENT:
        raise ValueError("boundary_statement must match readonly report text")


def _require_reason_code(
    field_name: str,
    value: object,
    allowed_values: tuple[str, ...],
) -> None:
    if type(value) is not str or value not in allowed_values:
        raise ValueError(f"{field_name} must be a known reason code")


def _normalize_reason_codes(
    field_name: str,
    value: object,
    allowed_values: tuple[str, ...],
) -> tuple[str, ...]:
    if type(value) not in (list, tuple):
        raise ValueError(f"{field_name} must be a list or tuple")
    reason_codes = tuple(value)
    if not reason_codes:
        raise ValueError(f"{field_name} must not be empty")
    normalized: list[str] = []
    for reason_code in reason_codes:
        _require_reason_code(field_name, reason_code, allowed_values)
        if reason_code not in normalized:
            normalized.append(reason_code)
    return tuple(sorted(normalized))


def _redact_public_reference(value: str) -> str:
    if _contains_unsafe_text(value) or "://" in value or "?" in value:
        return REDACTED_PUBLIC_REFERENCE
    return value


def _contains_unsafe_text(value: str) -> bool:
    lowered = value.lower()
    return any(fragment in lowered for fragment in UNSAFE_TEXT_FRAGMENTS)


def _json_ready(value: Any, path: str = "") -> Any:
    if value is None:
        return None
    if is_dataclass(value) and not isinstance(value, type):
        return {
            key: _json_ready(nested_value, key if not path else f"{path}.{key}")
            for key, nested_value in asdict(value).items()
            if key != PUBLIC_REFERENCE_FIELD
        }
    if isinstance(value, Decimal):
        if type(value) is not Decimal:
            raise ValueError(f"{path or 'value'} must be a Decimal")
        if not value.is_finite():
            raise ValueError(f"{path or 'value'} must be finite")
        return str(value)
    if isinstance(value, datetime):
        if type(value) is not datetime:
            raise ValueError(f"{path or 'value'} must be exactly datetime")
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError(f"{path or 'value'} must be timezone-aware")
        return value.astimezone(UTC).isoformat()
    if isinstance(value, float):
        raise ValueError(f"{path or 'value'} must not be a float")
    if type(value) is int:
        raise ValueError(f"{path or 'value'} must use Decimal-derived string values")
    if type(value) in (str, bool):
        return value
    if isinstance(value, dict):
        ready: dict[str, Any] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            if key == PUBLIC_REFERENCE_FIELD:
                raise ValueError("payload contains unsafe reference field")
            if _contains_unsafe_text(key):
                raise ValueError("payload contains unsafe key")
            item_path = key if not path else f"{path}.{key}"
            ready[key] = _json_ready(item, item_path)
        return ready
    if isinstance(value, (list, tuple)):
        return [
            _json_ready(item, f"{path}[{index}]" if path else f"value[{index}]")
            for index, item in enumerate(value)
        ]
    raise ValueError(f"{path or 'value'} is not JSON serializable")


def _reject_flag_downgrades(label: str, value: object, path: str = "") -> None:
    if is_dataclass(value) and not isinstance(value, type):
        _reject_flag_downgrades(label, asdict(value), path)
        return
    if isinstance(value, dict):
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            item_path = key if not path else f"{path}.{key}"
            if key in PHASE_FLAG_FIELDS and item is not True:
                raise ValueError(f"{item_path} must be True for {label}")
            _reject_flag_downgrades(label, item, item_path)
        return
    if isinstance(value, (list, tuple)):
        for index, item in enumerate(value):
            item_path = f"{path}[{index}]" if path else f"{label}[{index}]"
            _reject_flag_downgrades(label, item, item_path)


def _reject_unsafe_public_values(label: str, value: object, path: str = "") -> None:
    if is_dataclass(value) and not isinstance(value, type):
        _reject_unsafe_public_values(label, asdict(value), path)
        return
    if type(value) is str:
        if _contains_unsafe_text(value):
            raise ValueError(f"{path or label} has unsafe value")
        return
    if isinstance(value, dict):
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            if key == PUBLIC_REFERENCE_FIELD:
                raise ValueError("payload contains unsafe reference field")
            if _contains_unsafe_text(key):
                raise ValueError("payload contains unsafe key")
            item_path = key if not path else f"{path}.{key}"
            _reject_unsafe_public_values(label, item, item_path)
        return
    if isinstance(value, (list, tuple)):
        for index, item in enumerate(value):
            item_path = f"{path}[{index}]" if path else f"{label}[{index}]"
            _reject_unsafe_public_values(label, item, item_path)
