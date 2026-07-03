"""Pure in-memory team memory source recheck cadence queue reports."""

from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from typing import Any

from polymarket_alpha_lab.team_paper_guard import (
    UNSAFE_SURFACE_FIELD_FRAGMENTS,
    json_ready_no_floats,
    reject_unsafe_surface_fields,
    require_paper_only_flags,
)
from polymarket_alpha_lab.team_taxonomy import require_team_id


DEFAULT_TEAM_MEMORY_SOURCE_RECHECK_CADENCE_QUEUE_CONFIG_VERSION = (
    "team-memory-source-recheck-cadence-queue-v0"
)

OVERDUE_REASON = "team_memory_source_recheck_cadence_overdue"
MISSING_OWNER_REASON = "team_memory_source_recheck_missing_owner"
FAMILY_CONCENTRATION_REASON = "team_memory_source_recheck_family_concentration"
REPEATED_MISSES_REASON = "team_memory_source_recheck_repeated_misses"
REVIEWER_ACK_LAG_REASON = "team_memory_source_recheck_reviewer_ack_lag"
CLEAR_REASON = "team_memory_source_recheck_cadence_clear"

REASON_CODES = (
    OVERDUE_REASON,
    MISSING_OWNER_REASON,
    FAMILY_CONCENTRATION_REASON,
    REPEATED_MISSES_REASON,
    REVIEWER_ACK_LAG_REASON,
    CLEAR_REASON,
)
QUEUE_ROW_STATUSES = ("watch", "blocked")
FAMILY_STATUSES = ("ready", "watch")
REPORT_STATUSES = ("ready", "watch", "blocked")
BLOCKING_REASONS = (
    MISSING_OWNER_REASON,
    REPEATED_MISSES_REASON,
    REVIEWER_ACK_LAG_REASON,
)
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
QUANT = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
SECONDS_PER_DAY = Decimal("86400")
MICROSECONDS_PER_SECOND = Decimal("1000000")


def _join_parts(*parts: str) -> str:
    return "".join(parts)


EXTRA_UNSAFE_TEXT_FRAGMENTS = frozenset(
    (
        _join_parts("ad", "vice"),
        _join_parts("bro", "ker"),
        _join_parts("can", "cel"),
        _join_parts("li", "ve"),
        _join_parts("net", "work"),
        _join_parts("ord", "er"),
        _join_parts("sign", "ing"),
        _join_parts("sub", "mit"),
    ),
)


@dataclass(frozen=True)
class TeamMemorySourceRecheckCadenceQueueConfig:
    config_version: str = DEFAULT_TEAM_MEMORY_SOURCE_RECHECK_CADENCE_QUEUE_CONFIG_VERSION
    min_overdue_age_seconds: Decimal = ZERO
    max_reviewer_ack_lag_seconds: Decimal = Decimal("3600.000000")
    repeated_miss_threshold_count: Decimal = Decimal("2.000000")
    source_family_concentration_ratio: Decimal = Decimal("0.500000")
    source_family_concentration_min_count: Decimal = Decimal("2.000000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("config_version", self.config_version)
        object.__setattr__(
            self,
            "min_overdue_age_seconds",
            _require_nonnegative_decimal("min_overdue_age_seconds", self.min_overdue_age_seconds),
        )
        object.__setattr__(
            self,
            "max_reviewer_ack_lag_seconds",
            _require_positive_decimal(
                "max_reviewer_ack_lag_seconds",
                self.max_reviewer_ack_lag_seconds,
            ),
        )
        object.__setattr__(
            self,
            "repeated_miss_threshold_count",
            _require_positive_count_decimal(
                "repeated_miss_threshold_count",
                self.repeated_miss_threshold_count,
            ),
        )
        object.__setattr__(
            self,
            "source_family_concentration_ratio",
            _require_positive_ratio_decimal(
                "source_family_concentration_ratio",
                self.source_family_concentration_ratio,
            ),
        )
        object.__setattr__(
            self,
            "source_family_concentration_min_count",
            _require_positive_count_decimal(
                "source_family_concentration_min_count",
                self.source_family_concentration_min_count,
            ),
        )
        require_paper_only_flags("config", self)


@dataclass(frozen=True)
class TeamMemorySourceRecheckCadenceCandidate:
    team_id: str
    source_id: str
    source_family: str
    recheck_due_at: datetime
    owner_id: str | None = None
    consecutive_miss_count: Decimal = ZERO
    reviewer_ack_requested_at: datetime | None = None
    reviewer_acknowledged_at: datetime | None = None
    source_config_version: str = DEFAULT_TEAM_MEMORY_SOURCE_RECHECK_CADENCE_QUEUE_CONFIG_VERSION
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "team_id", require_team_id("team_id", self.team_id))
        _require_public_string("source_id", self.source_id)
        _require_public_string("source_family", self.source_family)
        object.__setattr__(
            self,
            "recheck_due_at",
            _as_utc("recheck_due_at", self.recheck_due_at),
        )
        if self.owner_id is not None:
            _require_public_string("owner_id", self.owner_id)
        object.__setattr__(
            self,
            "consecutive_miss_count",
            _require_count_decimal("consecutive_miss_count", self.consecutive_miss_count),
        )
        if self.reviewer_ack_requested_at is not None:
            object.__setattr__(
                self,
                "reviewer_ack_requested_at",
                _as_utc("reviewer_ack_requested_at", self.reviewer_ack_requested_at),
            )
        if self.reviewer_acknowledged_at is not None:
            object.__setattr__(
                self,
                "reviewer_acknowledged_at",
                _as_utc("reviewer_acknowledged_at", self.reviewer_acknowledged_at),
            )
        _validate_ack_shape(self)
        _require_canonical_string("source_config_version", self.source_config_version)
        require_paper_only_flags("candidate", self)


@dataclass(frozen=True)
class TeamMemorySourceRecheckCadenceQueueRow:
    team_id: str
    source_id: str
    source_family: str
    owner_id: str | None
    queue_status: str
    priority_rank: Decimal
    recheck_due_at: datetime
    overdue_age_seconds: Decimal
    consecutive_miss_count: Decimal
    reviewer_ack_lag_seconds: Decimal | None
    source_family_queue_ratio: Decimal
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "team_id", require_team_id("team_id", self.team_id))
        _require_public_string("source_id", self.source_id)
        _require_public_string("source_family", self.source_family)
        if self.owner_id is not None:
            _require_public_string("owner_id", self.owner_id)
        _require_queue_row_status("queue_status", self.queue_status)
        object.__setattr__(
            self,
            "priority_rank",
            _require_positive_count_decimal("priority_rank", self.priority_rank),
        )
        object.__setattr__(
            self,
            "recheck_due_at",
            _as_utc("recheck_due_at", self.recheck_due_at),
        )
        object.__setattr__(
            self,
            "overdue_age_seconds",
            _require_nonnegative_decimal("overdue_age_seconds", self.overdue_age_seconds),
        )
        object.__setattr__(
            self,
            "consecutive_miss_count",
            _require_count_decimal("consecutive_miss_count", self.consecutive_miss_count),
        )
        object.__setattr__(
            self,
            "reviewer_ack_lag_seconds",
            _normalize_optional_decimal(
                "reviewer_ack_lag_seconds",
                self.reviewer_ack_lag_seconds,
            ),
        )
        object.__setattr__(
            self,
            "source_family_queue_ratio",
            _require_ratio_decimal("source_family_queue_ratio", self.source_family_queue_ratio),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes, allow_clear=False),
        )
        _validate_queue_row(self)
        require_paper_only_flags("queue row", self)


@dataclass(frozen=True)
class TeamMemorySourceRecheckCadenceQueueFamilyRow:
    source_family: str
    queued_source_count: Decimal
    queued_source_ratio: Decimal
    team_count: Decimal
    family_status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_public_string("source_family", self.source_family)
        object.__setattr__(
            self,
            "queued_source_count",
            _require_positive_count_decimal("queued_source_count", self.queued_source_count),
        )
        object.__setattr__(
            self,
            "queued_source_ratio",
            _require_ratio_decimal("queued_source_ratio", self.queued_source_ratio),
        )
        object.__setattr__(
            self,
            "team_count",
            _require_positive_count_decimal("team_count", self.team_count),
        )
        _require_family_status("family_status", self.family_status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes, allow_clear=True),
        )
        _validate_family_row(self)
        require_paper_only_flags("source family row", self)


@dataclass(frozen=True)
class TeamMemorySourceRecheckCadenceQueueReasonCodeCount:
    reason_code: str
    queue_row_count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_reason_code("reason_code", self.reason_code)
        object.__setattr__(
            self,
            "queue_row_count",
            _require_count_decimal("queue_row_count", self.queue_row_count),
        )
        require_paper_only_flags("reason code count", self)


@dataclass(frozen=True)
class TeamMemorySourceRecheckCadenceQueueReport:
    generated_at: datetime
    config_version: str
    queue_status: str
    candidate_count: Decimal
    queued_source_count: Decimal
    blocked_source_count: Decimal
    watch_source_count: Decimal
    overdue_source_count: Decimal
    missing_owner_count: Decimal
    concentrated_family_count: Decimal
    repeated_miss_count: Decimal
    reviewer_ack_lag_count: Decimal
    max_overdue_age_seconds: Decimal | None
    max_reviewer_ack_lag_seconds: Decimal | None
    queue_rows: tuple[TeamMemorySourceRecheckCadenceQueueRow, ...]
    source_family_rows: tuple[TeamMemorySourceRecheckCadenceQueueFamilyRow, ...]
    reason_code_counts: tuple[TeamMemorySourceRecheckCadenceQueueReasonCodeCount, ...]
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        _require_report_status("queue_status", self.queue_status)
        for field_name in (
            "candidate_count",
            "queued_source_count",
            "blocked_source_count",
            "watch_source_count",
            "overdue_source_count",
            "missing_owner_count",
            "concentrated_family_count",
            "repeated_miss_count",
            "reviewer_ack_lag_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_count_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "max_overdue_age_seconds",
            _normalize_optional_decimal(
                "max_overdue_age_seconds",
                self.max_overdue_age_seconds,
            ),
        )
        object.__setattr__(
            self,
            "max_reviewer_ack_lag_seconds",
            _normalize_optional_decimal(
                "max_reviewer_ack_lag_seconds",
                self.max_reviewer_ack_lag_seconds,
            ),
        )
        object.__setattr__(self, "queue_rows", _normalize_queue_rows(self.queue_rows))
        object.__setattr__(
            self,
            "source_family_rows",
            _normalize_source_family_rows(self.source_family_rows),
        )
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes, allow_clear=True),
        )
        _validate_report(self)
        require_paper_only_flags("report", self)


@dataclass(frozen=True)
class _QueueDraft:
    candidate: TeamMemorySourceRecheckCadenceCandidate
    overdue_age_seconds: Decimal
    reviewer_ack_lag_seconds: Decimal | None
    source_family_queue_ratio: Decimal
    reason_codes: tuple[str, ...]


def build_team_memory_source_recheck_cadence_queue_report(
    candidates: list[TeamMemorySourceRecheckCadenceCandidate]
    | tuple[TeamMemorySourceRecheckCadenceCandidate, ...],
    *,
    config: TeamMemorySourceRecheckCadenceQueueConfig,
    generated_at: datetime,
) -> TeamMemorySourceRecheckCadenceQueueReport:
    if type(config) is not TeamMemorySourceRecheckCadenceQueueConfig:
        raise ValueError("config must be a TeamMemorySourceRecheckCadenceQueueConfig")
    require_paper_only_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    normalized_candidates = _normalize_candidates(candidates, generated_at=generated_at_utc)
    queue_rows = _queue_rows(
        normalized_candidates,
        config=config,
        generated_at=generated_at_utc,
    )
    source_family_rows = _source_family_rows(
        queue_rows,
        config=config,
    )
    reason_codes = _report_reason_codes(queue_rows)

    return TeamMemorySourceRecheckCadenceQueueReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        queue_status=_report_status(queue_rows),
        candidate_count=_decimal_count(len(normalized_candidates)),
        queued_source_count=_decimal_count(len(queue_rows)),
        blocked_source_count=_decimal_count(
            sum(1 for row in queue_rows if row.queue_status == "blocked"),
        ),
        watch_source_count=_decimal_count(
            sum(1 for row in queue_rows if row.queue_status == "watch"),
        ),
        overdue_source_count=_decimal_count(
            _count_rows_with_reason(queue_rows, OVERDUE_REASON),
        ),
        missing_owner_count=_decimal_count(
            _count_rows_with_reason(queue_rows, MISSING_OWNER_REASON),
        ),
        concentrated_family_count=_decimal_count(
            _count_family_rows_with_reason(source_family_rows, FAMILY_CONCENTRATION_REASON),
        ),
        repeated_miss_count=_decimal_count(
            _count_rows_with_reason(queue_rows, REPEATED_MISSES_REASON),
        ),
        reviewer_ack_lag_count=_decimal_count(
            _count_rows_with_reason(queue_rows, REVIEWER_ACK_LAG_REASON),
        ),
        max_overdue_age_seconds=_max_row_decimal(queue_rows, "overdue_age_seconds"),
        max_reviewer_ack_lag_seconds=_max_optional_row_decimal(
            queue_rows,
            "reviewer_ack_lag_seconds",
        ),
        queue_rows=queue_rows,
        source_family_rows=source_family_rows,
        reason_code_counts=_reason_code_counts_for_rows(queue_rows),
        reason_codes=reason_codes,
    )


def team_memory_source_recheck_cadence_queue_report_payload(
    report: TeamMemorySourceRecheckCadenceQueueReport,
) -> dict[str, Any]:
    if type(report) is not TeamMemorySourceRecheckCadenceQueueReport:
        raise ValueError("report must be a TeamMemorySourceRecheckCadenceQueueReport")
    require_paper_only_flags("report", report)
    payload = json_ready_no_floats(report)
    reject_unsafe_surface_fields("team memory source recheck cadence queue payload", payload)
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    return payload


def _queue_rows(
    candidates: tuple[TeamMemorySourceRecheckCadenceCandidate, ...],
    *,
    config: TeamMemorySourceRecheckCadenceQueueConfig,
    generated_at: datetime,
) -> tuple[TeamMemorySourceRecheckCadenceQueueRow, ...]:
    base_drafts: list[_QueueDraft] = []
    for candidate in candidates:
        overdue_age_seconds = _overdue_age_seconds(generated_at, candidate.recheck_due_at)
        reviewer_ack_lag_seconds = _reviewer_ack_lag_seconds(candidate, generated_at)
        reason_codes = _candidate_reason_codes(
            candidate=candidate,
            overdue_age_seconds=overdue_age_seconds,
            reviewer_ack_lag_seconds=reviewer_ack_lag_seconds,
            config=config,
        )
        if reason_codes:
            base_drafts.append(
                _QueueDraft(
                    candidate=candidate,
                    overdue_age_seconds=overdue_age_seconds,
                    reviewer_ack_lag_seconds=reviewer_ack_lag_seconds,
                    source_family_queue_ratio=ZERO,
                    reason_codes=reason_codes,
                ),
            )

    family_counts = _source_family_counts(tuple(base_drafts))
    total_count = _decimal_count(len(base_drafts))
    concentrated_families = _concentrated_families(
        family_counts,
        total_count=total_count,
        config=config,
    )
    final_drafts = tuple(
        _draft_with_family_metrics(
            draft,
            family_counts=family_counts,
            total_count=total_count,
            concentrated_families=concentrated_families,
        )
        for draft in base_drafts
    )
    sorted_drafts = tuple(sorted(final_drafts, key=_draft_sort_key))

    return tuple(
        TeamMemorySourceRecheckCadenceQueueRow(
            team_id=draft.candidate.team_id,
            source_id=draft.candidate.source_id,
            source_family=draft.candidate.source_family,
            owner_id=draft.candidate.owner_id,
            queue_status=_queue_row_status(draft.reason_codes),
            priority_rank=_decimal_count(index),
            recheck_due_at=draft.candidate.recheck_due_at,
            overdue_age_seconds=draft.overdue_age_seconds,
            consecutive_miss_count=draft.candidate.consecutive_miss_count,
            reviewer_ack_lag_seconds=draft.reviewer_ack_lag_seconds,
            source_family_queue_ratio=draft.source_family_queue_ratio,
            reason_codes=draft.reason_codes,
        )
        for index, draft in enumerate(sorted_drafts, start=1)
    )


def _candidate_reason_codes(
    *,
    candidate: TeamMemorySourceRecheckCadenceCandidate,
    overdue_age_seconds: Decimal,
    reviewer_ack_lag_seconds: Decimal | None,
    config: TeamMemorySourceRecheckCadenceQueueConfig,
) -> tuple[str, ...]:
    reasons: list[str] = []
    if overdue_age_seconds > config.min_overdue_age_seconds:
        reasons.append(OVERDUE_REASON)
    if candidate.owner_id is None:
        reasons.append(MISSING_OWNER_REASON)
    if candidate.consecutive_miss_count >= config.repeated_miss_threshold_count:
        reasons.append(REPEATED_MISSES_REASON)
    if (
        reviewer_ack_lag_seconds is not None
        and reviewer_ack_lag_seconds > config.max_reviewer_ack_lag_seconds
    ):
        reasons.append(REVIEWER_ACK_LAG_REASON)
    return tuple(reasons)


def _draft_with_family_metrics(
    draft: _QueueDraft,
    *,
    family_counts: dict[str, Decimal],
    total_count: Decimal,
    concentrated_families: frozenset[str],
) -> _QueueDraft:
    source_family = draft.candidate.source_family
    reason_codes = draft.reason_codes
    if source_family in concentrated_families:
        reason_codes = _canonical_reason_codes(
            (*reason_codes, FAMILY_CONCENTRATION_REASON),
            allow_clear=False,
        )
    return _QueueDraft(
        candidate=draft.candidate,
        overdue_age_seconds=draft.overdue_age_seconds,
        reviewer_ack_lag_seconds=draft.reviewer_ack_lag_seconds,
        source_family_queue_ratio=_ratio(family_counts.get(source_family, ZERO), total_count),
        reason_codes=reason_codes,
    )


def _source_family_rows(
    queue_rows: tuple[TeamMemorySourceRecheckCadenceQueueRow, ...],
    *,
    config: TeamMemorySourceRecheckCadenceQueueConfig,
) -> tuple[TeamMemorySourceRecheckCadenceQueueFamilyRow, ...]:
    if not queue_rows:
        return ()
    total_count = _decimal_count(len(queue_rows))
    family_counts: dict[str, Decimal] = {}
    family_teams: dict[str, set[str]] = {}
    for row in queue_rows:
        family_counts[row.source_family] = family_counts.get(row.source_family, ZERO) + ONE
        family_teams.setdefault(row.source_family, set()).add(row.team_id)

    concentrated_families = _concentrated_families(
        family_counts,
        total_count=total_count,
        config=config,
    )
    rows = []
    for source_family, queued_source_count in sorted(family_counts.items()):
        is_concentrated = source_family in concentrated_families
        rows.append(
            TeamMemorySourceRecheckCadenceQueueFamilyRow(
                source_family=source_family,
                queued_source_count=queued_source_count,
                queued_source_ratio=_ratio(queued_source_count, total_count),
                team_count=_decimal_count(len(family_teams[source_family])),
                family_status="watch" if is_concentrated else "ready",
                reason_codes=(
                    (FAMILY_CONCENTRATION_REASON,)
                    if is_concentrated
                    else (CLEAR_REASON,)
                ),
            ),
        )
    return tuple(rows)


def _source_family_counts(drafts: tuple[_QueueDraft, ...]) -> dict[str, Decimal]:
    counts: dict[str, Decimal] = {}
    for draft in drafts:
        source_family = draft.candidate.source_family
        counts[source_family] = counts.get(source_family, ZERO) + ONE
    return counts


def _concentrated_families(
    family_counts: dict[str, Decimal],
    *,
    total_count: Decimal,
    config: TeamMemorySourceRecheckCadenceQueueConfig,
) -> frozenset[str]:
    if total_count == ZERO:
        return frozenset()
    return frozenset(
        source_family
        for source_family, source_count in family_counts.items()
        if source_count >= config.source_family_concentration_min_count
        and _ratio(source_count, total_count) >= config.source_family_concentration_ratio
    )


def _draft_sort_key(draft: _QueueDraft) -> tuple[Decimal, int, int, Decimal, Decimal, str, str, str]:
    return (
        -draft.overdue_age_seconds,
        0 if MISSING_OWNER_REASON in draft.reason_codes else 1,
        0 if FAMILY_CONCENTRATION_REASON in draft.reason_codes else 1,
        -draft.candidate.consecutive_miss_count,
        -_decimal_or_zero(draft.reviewer_ack_lag_seconds),
        draft.candidate.team_id,
        draft.candidate.source_family,
        draft.candidate.source_id,
    )


def _row_sort_key(
    row: TeamMemorySourceRecheckCadenceQueueRow,
) -> tuple[Decimal, int, int, Decimal, Decimal, str, str, str]:
    return (
        -row.overdue_age_seconds,
        0 if MISSING_OWNER_REASON in row.reason_codes else 1,
        0 if FAMILY_CONCENTRATION_REASON in row.reason_codes else 1,
        -row.consecutive_miss_count,
        -_decimal_or_zero(row.reviewer_ack_lag_seconds),
        row.team_id,
        row.source_family,
        row.source_id,
    )


def _queue_row_status(reason_codes: tuple[str, ...]) -> str:
    if any(reason_code in BLOCKING_REASONS for reason_code in reason_codes):
        return "blocked"
    return "watch"


def _report_status(queue_rows: tuple[TeamMemorySourceRecheckCadenceQueueRow, ...]) -> str:
    if any(row.queue_status == "blocked" for row in queue_rows):
        return "blocked"
    if queue_rows:
        return "watch"
    return "ready"


def _report_reason_codes(
    queue_rows: tuple[TeamMemorySourceRecheckCadenceQueueRow, ...],
) -> tuple[str, ...]:
    if not queue_rows:
        return (CLEAR_REASON,)
    flattened = tuple(
        reason_code
        for row in queue_rows
        for reason_code in row.reason_codes
    )
    return _canonical_reason_codes(flattened, allow_clear=False)


def _reason_code_counts_for_rows(
    queue_rows: tuple[TeamMemorySourceRecheckCadenceQueueRow, ...],
) -> tuple[TeamMemorySourceRecheckCadenceQueueReasonCodeCount, ...]:
    if not queue_rows:
        return (
            TeamMemorySourceRecheckCadenceQueueReasonCodeCount(
                reason_code=CLEAR_REASON,
                queue_row_count=ZERO,
            ),
        )
    flattened = tuple(
        reason_code
        for row in queue_rows
        for reason_code in row.reason_codes
    )
    return tuple(
        TeamMemorySourceRecheckCadenceQueueReasonCodeCount(
            reason_code=reason_code,
            queue_row_count=_decimal_count(
                sum(1 for item in flattened if item == reason_code),
            ),
        )
        for reason_code in sorted(set(flattened))
    )


def _normalize_candidates(
    value: object,
    *,
    generated_at: datetime,
) -> tuple[TeamMemorySourceRecheckCadenceCandidate, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("candidates must be a list or tuple")
    candidates = tuple(value)
    seen_keys: set[tuple[str, str]] = set()
    for candidate in candidates:
        if type(candidate) is not TeamMemorySourceRecheckCadenceCandidate:
            raise ValueError("candidates must contain TeamMemorySourceRecheckCadenceCandidate")
        require_paper_only_flags("candidate", candidate)
        if (
            candidate.reviewer_ack_requested_at is not None
            and candidate.reviewer_ack_requested_at > generated_at
        ):
            raise ValueError("reviewer_ack_requested_at must not be in the future")
        if (
            candidate.reviewer_acknowledged_at is not None
            and candidate.reviewer_acknowledged_at > generated_at
        ):
            raise ValueError("reviewer_acknowledged_at must not be in the future")
        key = (candidate.team_id, candidate.source_id)
        if key in seen_keys:
            raise ValueError("source_id values must be unique per team")
        seen_keys.add(key)
    return candidates


def _normalize_queue_rows(
    value: object,
) -> tuple[TeamMemorySourceRecheckCadenceQueueRow, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("queue_rows must be a list or tuple")
    rows = tuple(value)
    seen_keys: set[tuple[str, str]] = set()
    for row in rows:
        if type(row) is not TeamMemorySourceRecheckCadenceQueueRow:
            raise ValueError("queue_rows must contain queue row values")
        require_paper_only_flags("queue row", row)
        key = (row.team_id, row.source_id)
        if key in seen_keys:
            raise ValueError("queue_rows must be unique by team and source")
        seen_keys.add(key)
    if rows != tuple(sorted(rows, key=_row_sort_key)):
        raise ValueError("queue_rows must be sorted deterministically")
    expected_ranks = tuple(_decimal_count(index) for index in range(1, len(rows) + 1))
    if tuple(row.priority_rank for row in rows) != expected_ranks:
        raise ValueError("priority_rank must match queue row sequence")
    return rows


def _normalize_source_family_rows(
    value: object,
) -> tuple[TeamMemorySourceRecheckCadenceQueueFamilyRow, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("source_family_rows must be a list or tuple")
    rows = tuple(value)
    seen_source_families: set[str] = set()
    for row in rows:
        if type(row) is not TeamMemorySourceRecheckCadenceQueueFamilyRow:
            raise ValueError("source_family_rows must contain source family row values")
        require_paper_only_flags("source family row", row)
        if row.source_family in seen_source_families:
            raise ValueError("source_family_rows must be unique by source family")
        seen_source_families.add(row.source_family)
    if rows != tuple(sorted(rows, key=lambda row: row.source_family)):
        raise ValueError("source_family_rows must be sorted by source family")
    return rows


def _normalize_reason_code_counts(
    value: object,
) -> tuple[TeamMemorySourceRecheckCadenceQueueReasonCodeCount, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("reason_code_counts must be a list or tuple")
    counts = tuple(value)
    seen_reason_codes: set[str] = set()
    for count in counts:
        if type(count) is not TeamMemorySourceRecheckCadenceQueueReasonCodeCount:
            raise ValueError("reason_code_counts must contain reason count values")
        require_paper_only_flags("reason code count", count)
        if count.reason_code in seen_reason_codes:
            raise ValueError("reason_code_counts must be unique by reason code")
        seen_reason_codes.add(count.reason_code)
    if tuple(count.reason_code for count in counts) != tuple(
        sorted(count.reason_code for count in counts),
    ):
        raise ValueError("reason_code_counts must be sorted by reason code")
    return counts


def _normalize_reason_codes(
    value: object,
    *,
    allow_clear: bool,
) -> tuple[str, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("reason_codes must be a list or tuple")
    reason_codes = tuple(value)
    if not reason_codes:
        raise ValueError("reason_codes must not be empty")
    for reason_code in reason_codes:
        _require_reason_code("reason_codes", reason_code)
    if CLEAR_REASON in reason_codes and reason_codes != (CLEAR_REASON,):
        raise ValueError("clear reason cannot be combined")
    if CLEAR_REASON in reason_codes and not allow_clear:
        raise ValueError("clear reason is not valid here")
    if len(set(reason_codes)) != len(reason_codes):
        raise ValueError("reason_codes must be unique")
    if _canonical_reason_codes(reason_codes, allow_clear=allow_clear) != reason_codes:
        raise ValueError("reason_codes must be deterministic")
    return reason_codes


def _canonical_reason_codes(
    reason_codes: tuple[str, ...],
    *,
    allow_clear: bool,
) -> tuple[str, ...]:
    allowed_codes = REASON_CODES if allow_clear else REASON_CODES[:-1]
    return tuple(reason_code for reason_code in allowed_codes if reason_code in reason_codes)


def _validate_ack_shape(candidate: TeamMemorySourceRecheckCadenceCandidate) -> None:
    if (
        candidate.reviewer_ack_requested_at is None
        and candidate.reviewer_acknowledged_at is not None
    ):
        raise ValueError("reviewer_acknowledged_at requires reviewer_ack_requested_at")
    if (
        candidate.reviewer_ack_requested_at is not None
        and candidate.reviewer_acknowledged_at is not None
        and candidate.reviewer_acknowledged_at < candidate.reviewer_ack_requested_at
    ):
        raise ValueError("reviewer_acknowledged_at must not be before request time")


def _validate_queue_row(row: TeamMemorySourceRecheckCadenceQueueRow) -> None:
    if row.queue_status != _queue_row_status(row.reason_codes):
        raise ValueError("queue_status must match reason_codes")
    if OVERDUE_REASON in row.reason_codes and row.overdue_age_seconds <= ZERO:
        raise ValueError("overdue reason requires positive overdue age")
    if MISSING_OWNER_REASON in row.reason_codes and row.owner_id is not None:
        raise ValueError("missing owner reason requires absent owner_id")
    if MISSING_OWNER_REASON not in row.reason_codes and row.owner_id is None:
        raise ValueError("absent owner_id requires missing owner reason")
    if REPEATED_MISSES_REASON in row.reason_codes and row.consecutive_miss_count <= ZERO:
        raise ValueError("repeated misses reason requires miss count")
    if REVIEWER_ACK_LAG_REASON in row.reason_codes and row.reviewer_ack_lag_seconds is None:
        raise ValueError("reviewer lag reason requires lag seconds")
    if FAMILY_CONCENTRATION_REASON in row.reason_codes and row.source_family_queue_ratio <= ZERO:
        raise ValueError("family concentration reason requires source family ratio")


def _validate_family_row(row: TeamMemorySourceRecheckCadenceQueueFamilyRow) -> None:
    expected_status = (
        "watch" if FAMILY_CONCENTRATION_REASON in row.reason_codes else "ready"
    )
    if row.family_status != expected_status:
        raise ValueError("family_status must match reason_codes")
    if row.family_status == "ready" and row.reason_codes != (CLEAR_REASON,):
        raise ValueError("ready source family rows require clear reason")
    if row.family_status == "watch" and row.reason_codes != (FAMILY_CONCENTRATION_REASON,):
        raise ValueError("watch source family rows require concentration reason")
    if row.team_count > row.queued_source_count:
        raise ValueError("team_count cannot exceed queued_source_count")


def _validate_report(report: TeamMemorySourceRecheckCadenceQueueReport) -> None:
    if report.queued_source_count != _decimal_count(len(report.queue_rows)):
        raise ValueError("queued_source_count must match queue_rows")
    if report.candidate_count < report.queued_source_count:
        raise ValueError("candidate_count cannot be below queued_source_count")
    if report.blocked_source_count != _decimal_count(
        sum(1 for row in report.queue_rows if row.queue_status == "blocked"),
    ):
        raise ValueError("blocked_source_count must match queue_rows")
    if report.watch_source_count != _decimal_count(
        sum(1 for row in report.queue_rows if row.queue_status == "watch"),
    ):
        raise ValueError("watch_source_count must match queue_rows")
    if report.overdue_source_count != _decimal_count(
        _count_rows_with_reason(report.queue_rows, OVERDUE_REASON),
    ):
        raise ValueError("overdue_source_count must match queue_rows")
    if report.missing_owner_count != _decimal_count(
        _count_rows_with_reason(report.queue_rows, MISSING_OWNER_REASON),
    ):
        raise ValueError("missing_owner_count must match queue_rows")
    if report.concentrated_family_count != _decimal_count(
        _count_family_rows_with_reason(report.source_family_rows, FAMILY_CONCENTRATION_REASON),
    ):
        raise ValueError("concentrated_family_count must match source_family_rows")
    if report.repeated_miss_count != _decimal_count(
        _count_rows_with_reason(report.queue_rows, REPEATED_MISSES_REASON),
    ):
        raise ValueError("repeated_miss_count must match queue_rows")
    if report.reviewer_ack_lag_count != _decimal_count(
        _count_rows_with_reason(report.queue_rows, REVIEWER_ACK_LAG_REASON),
    ):
        raise ValueError("reviewer_ack_lag_count must match queue_rows")
    if report.max_overdue_age_seconds != _max_row_decimal(
        report.queue_rows,
        "overdue_age_seconds",
    ):
        raise ValueError("max_overdue_age_seconds must match queue_rows")
    if report.max_reviewer_ack_lag_seconds != _max_optional_row_decimal(
        report.queue_rows,
        "reviewer_ack_lag_seconds",
    ):
        raise ValueError("max_reviewer_ack_lag_seconds must match queue_rows")
    if report.queue_status != _report_status(report.queue_rows):
        raise ValueError("queue_status must match queue_rows")
    if report.reason_codes != _report_reason_codes(report.queue_rows):
        raise ValueError("reason_codes must match queue_rows")
    if report.reason_code_counts != _reason_code_counts_for_rows(report.queue_rows):
        raise ValueError("reason_code_counts must summarize queue_rows")
    _validate_source_family_rows_match_queue_rows(report)


def _validate_source_family_rows_match_queue_rows(
    report: TeamMemorySourceRecheckCadenceQueueReport,
) -> None:
    if not report.queue_rows:
        if report.source_family_rows:
            raise ValueError("source_family_rows require queue_rows")
        return
    families_from_rows = tuple(sorted({row.source_family for row in report.queue_rows}))
    if tuple(row.source_family for row in report.source_family_rows) != families_from_rows:
        raise ValueError("source_family_rows must match queue_rows")
    total_count = _decimal_count(len(report.queue_rows))
    for family_row in report.source_family_rows:
        related_rows = tuple(
            row for row in report.queue_rows if row.source_family == family_row.source_family
        )
        if family_row.queued_source_count != _decimal_count(len(related_rows)):
            raise ValueError("source_family queued_source_count must match queue_rows")
        if family_row.queued_source_ratio != _ratio(family_row.queued_source_count, total_count):
            raise ValueError("source_family queued_source_ratio must match queue_rows")
        if family_row.team_count != _decimal_count(len({row.team_id for row in related_rows})):
            raise ValueError("source_family team_count must match queue_rows")
        for row in related_rows:
            if row.source_family_queue_ratio != family_row.queued_source_ratio:
                raise ValueError("queue row source_family_queue_ratio must match family row")


def _reviewer_ack_lag_seconds(
    candidate: TeamMemorySourceRecheckCadenceCandidate,
    generated_at: datetime,
) -> Decimal | None:
    if candidate.reviewer_ack_requested_at is None:
        return None
    end_at = candidate.reviewer_acknowledged_at or generated_at
    return _elapsed_seconds(candidate.reviewer_ack_requested_at, end_at)


def _overdue_age_seconds(generated_at: datetime, recheck_due_at: datetime) -> Decimal:
    if recheck_due_at >= generated_at:
        return ZERO
    return _elapsed_seconds(recheck_due_at, generated_at)


def _elapsed_seconds(start_at: datetime, end_at: datetime) -> Decimal:
    delta = _as_utc("end_at", end_at) - _as_utc("start_at", start_at)
    age_seconds = (
        Decimal(delta.days) * SECONDS_PER_DAY
        + Decimal(delta.seconds)
        + (Decimal(delta.microseconds) / MICROSECONDS_PER_SECOND)
    )
    if age_seconds < ZERO:
        raise ValueError("age seconds must be nonnegative")
    return age_seconds.quantize(QUANT)


def _count_rows_with_reason(
    rows: tuple[TeamMemorySourceRecheckCadenceQueueRow, ...],
    reason_code: str,
) -> int:
    return sum(1 for row in rows if reason_code in row.reason_codes)


def _count_family_rows_with_reason(
    rows: tuple[TeamMemorySourceRecheckCadenceQueueFamilyRow, ...],
    reason_code: str,
) -> int:
    return sum(1 for row in rows if reason_code in row.reason_codes)


def _max_row_decimal(
    rows: tuple[TeamMemorySourceRecheckCadenceQueueRow, ...],
    field_name: str,
) -> Decimal | None:
    if not rows:
        return None
    return max(getattr(row, field_name) for row in rows)


def _max_optional_row_decimal(
    rows: tuple[TeamMemorySourceRecheckCadenceQueueRow, ...],
    field_name: str,
) -> Decimal | None:
    values = tuple(
        getattr(row, field_name)
        for row in rows
        if getattr(row, field_name) is not None
    )
    return max(values) if values else None


def _decimal_or_zero(value: Decimal | None) -> Decimal:
    return ZERO if value is None else value


def _decimal_count(value: int) -> Decimal:
    return Decimal(value).quantize(QUANT)


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return (numerator / denominator).quantize(QUANT)


def _normalize_optional_decimal(field_name: str, value: object) -> Decimal | None:
    if value is None:
        return None
    return _require_nonnegative_decimal(field_name, value)


def _require_positive_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_nonnegative_decimal(field_name, value)
    if decimal_value <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return decimal_value


def _require_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    decimal_value = value.quantize(QUANT)
    if decimal_value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return decimal_value


def _require_count_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_nonnegative_decimal(field_name, value)
    if decimal_value != decimal_value.to_integral_value():
        raise ValueError(f"{field_name} must be a whole count")
    return decimal_value


def _require_positive_count_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_count_decimal(field_name, value)
    if decimal_value <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return decimal_value


def _require_ratio_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_nonnegative_decimal(field_name, value)
    if decimal_value > ONE:
        raise ValueError(f"{field_name} must be at most one")
    return decimal_value


def _require_positive_ratio_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_ratio_decimal(field_name, value)
    if decimal_value <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return decimal_value


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_queue_row_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in QUEUE_ROW_STATUSES:
        raise ValueError(f"{field_name} must be watch or blocked")


def _require_family_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in FAMILY_STATUSES:
        raise ValueError(f"{field_name} must be ready or watch")


def _require_report_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in REPORT_STATUSES:
        raise ValueError(f"{field_name} must be ready, watch, or blocked")


def _require_reason_code(field_name: str, value: object) -> None:
    if type(value) is not str or value not in REASON_CODES:
        raise ValueError(f"{field_name} must be a known reason code")


def _require_public_string(field_name: str, value: object) -> None:
    _require_canonical_string(field_name, value)
    lowered = value.lower()
    if any(
        fragment in lowered
        for fragment in UNSAFE_SURFACE_FIELD_FRAGMENTS | EXTRA_UNSAFE_TEXT_FRAGMENTS
    ):
        raise ValueError(f"{field_name} contains unsafe text")


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value:
        raise ValueError(f"{field_name} must not be empty")
    if value.strip() != value:
        raise ValueError(f"{field_name} must be stripped")
    if "\n" in value or "\r" in value or "\t" in value:
        raise ValueError(f"{field_name} must be single line")


__all__ = (
    "DEFAULT_TEAM_MEMORY_SOURCE_RECHECK_CADENCE_QUEUE_CONFIG_VERSION",
    "TeamMemorySourceRecheckCadenceCandidate",
    "TeamMemorySourceRecheckCadenceQueueConfig",
    "TeamMemorySourceRecheckCadenceQueueFamilyRow",
    "TeamMemorySourceRecheckCadenceQueueReasonCodeCount",
    "TeamMemorySourceRecheckCadenceQueueReport",
    "TeamMemorySourceRecheckCadenceQueueRow",
    "build_team_memory_source_recheck_cadence_queue_report",
    "team_memory_source_recheck_cadence_queue_report_payload",
)
