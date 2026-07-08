"""Public-safe aggregate specialist memory conflict queue report."""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable
from dataclasses import dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
import json
from typing import Any

from polymarket_alpha_lab.team_paper_guard import require_paper_only_flags


__all__ = (
    "DEFAULT_RESEARCH_TEAM_MEMORY_CONFLICT_QUEUE_REPORT_CONFIG_VERSION",
    "ResearchTeamMemoryConflictQueueConfig",
    "ResearchTeamMemoryConflictQueueInput",
    "ResearchTeamMemoryConflictQueueReasonCodeCount",
    "ResearchTeamMemoryConflictQueueReport",
    "ResearchTeamMemoryConflictQueueRow",
    "build_research_team_memory_conflict_queue_report",
    "research_team_memory_conflict_queue_report_payload",
)


DEFAULT_RESEARCH_TEAM_MEMORY_CONFLICT_QUEUE_REPORT_CONFIG_VERSION = (
    "research-team-memory-conflict-queue-report-v0"
)

COUNT_QUANTUM = Decimal("1")
RATIO_QUANTUM = Decimal("0.000001")
ZERO_COUNT = Decimal("0")
ZERO_RATIO = Decimal("0.000000")
ONE_RATIO = Decimal("1.000000")
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
STATUSES = ("pass", "watch", "block")
STATUS_WEIGHT = {
    "block": Decimal("2.000000"),
    "watch": Decimal("1.000000"),
    "pass": Decimal("0.000000"),
}
PAPER_ACTION_BY_STATUS = {
    "pass": "paper_memory_conflict_queue_monitor",
    "watch": "paper_memory_conflict_queue_watch",
    "block": "paper_memory_conflict_queue_block",
}

PASS_ROW_REASON_CODE = "memory_conflict_queue_clear"
EMPTY_REPORT_REASON_CODE = "memory_conflict_queue_empty"
BLOCK_REASON_CODES = (
    "contradictory_lessons_block",
    "stale_calibrations_block",
    "unresolved_review_notes_block",
    "domain_escalation_fit_block",
    "queue_age_block",
    "queue_urgency_block",
)
WATCH_REASON_CODES = (
    "contradictory_lessons_watch",
    "stale_calibrations_watch",
    "unresolved_review_notes_watch",
    "domain_escalation_fit_watch",
    "queue_age_watch",
    "queue_urgency_watch",
)
ROW_REASON_CODES = BLOCK_REASON_CODES + WATCH_REASON_CODES + (PASS_ROW_REASON_CODE,)
REPORT_REASON_PRIORITY = BLOCK_REASON_CODES + WATCH_REASON_CODES
HEX_CHARS = frozenset("0123456789abcdef")
UNSAFE_PUBLIC_FRAGMENTS = frozenset(
    (
        "event",
        "mar" + "ket",
        "sou" + "rce",
        "wa" + "llet",
        "auth",
        "ord" + "er",
        "tra" + "de",
        "li" + "ve",
        "data" + "base",
        "net" + "work",
        "broker",
        "execution",
        "persist",
        "mutation",
        "account",
        "private_key",
        "signing",
        "position",
        "buy",
        "sell",
        "recom" + "mendation",
        "siz" + "ing",
    ),
)


class _FinalPublicDataclass:
    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        for base in cls.__bases__:
            if base is not _FinalPublicDataclass and issubclass(
                base,
                _FinalPublicDataclass,
            ):
                raise ValueError(f"{base.__name__} subclass is not allowed")


@dataclass(frozen=True)
class ResearchTeamMemoryConflictQueueConfig(_FinalPublicDataclass):
    config_version: str = DEFAULT_RESEARCH_TEAM_MEMORY_CONFLICT_QUEUE_REPORT_CONFIG_VERSION
    watch_contradictory_lesson_count: Decimal = Decimal("1")
    block_contradictory_lesson_count: Decimal = Decimal("3")
    watch_stale_calibration_count: Decimal = Decimal("1")
    block_stale_calibration_count: Decimal = Decimal("3")
    watch_unresolved_review_note_count: Decimal = Decimal("1")
    block_unresolved_review_note_count: Decimal = Decimal("2")
    watch_domain_escalation_fit_score: Decimal = Decimal("0.500000")
    block_domain_escalation_fit_score: Decimal = Decimal("0.850000")
    watch_queue_age_hours: Decimal = Decimal("24.000000")
    block_queue_age_hours: Decimal = Decimal("72.000000")
    watch_queue_urgency_score: Decimal = Decimal("0.350000")
    block_queue_urgency_score: Decimal = Decimal("0.750000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchTeamMemoryConflictQueueConfig, "config")
        _require_public_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_TEAM_MEMORY_CONFLICT_QUEUE_REPORT_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "watch_contradictory_lesson_count",
            "block_contradictory_lesson_count",
            "watch_stale_calibration_count",
            "block_stale_calibration_count",
            "watch_unresolved_review_note_count",
            "block_unresolved_review_note_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_count_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "watch_domain_escalation_fit_score",
            "block_domain_escalation_fit_score",
            "watch_queue_urgency_score",
            "block_queue_urgency_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in ("watch_queue_age_hours", "block_queue_age_hours"):
            object.__setattr__(
                self,
                field_name,
                _require_positive_decimal(field_name, getattr(self, field_name)),
            )
        _validate_config(self)
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class ResearchTeamMemoryConflictQueueInput(_FinalPublicDataclass):
    specialist_key: str
    aggregate_label: str
    contradictory_lesson_count: Decimal
    stale_calibration_count: Decimal
    unresolved_review_note_count: Decimal
    domain_escalation_fit_score: Decimal
    queue_age_hours: Decimal
    observed_at: datetime
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchTeamMemoryConflictQueueInput, "input")
        _require_safe_label("specialist_key", self.specialist_key)
        _require_safe_label("aggregate_label", self.aggregate_label)
        for field_name in (
            "contradictory_lesson_count",
            "stale_calibration_count",
            "unresolved_review_note_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_count_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "domain_escalation_fit_score",
            _require_ratio_decimal(
                "domain_escalation_fit_score",
                self.domain_escalation_fit_score,
            ),
        )
        object.__setattr__(
            self,
            "queue_age_hours",
            _require_nonnegative_decimal("queue_age_hours", self.queue_age_hours),
        )
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        _require_hard_flags("input", self)


@dataclass(frozen=True)
class ResearchTeamMemoryConflictQueueRow(_FinalPublicDataclass):
    specialist_key: str
    aggregate_label: str
    conflict_status: str
    contradictory_lesson_count: Decimal
    stale_calibration_count: Decimal
    unresolved_review_note_count: Decimal
    domain_escalation_fit_score: Decimal
    queue_age_hours: Decimal
    queue_urgency_score: Decimal
    observed_at: datetime
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchTeamMemoryConflictQueueRow, "row")
        _require_safe_label("specialist_key", self.specialist_key)
        _require_safe_label("aggregate_label", self.aggregate_label)
        _require_status("conflict_status", self.conflict_status)
        for field_name in (
            "contradictory_lesson_count",
            "stale_calibration_count",
            "unresolved_review_note_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_count_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in ("domain_escalation_fit_score", "queue_urgency_score"):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "queue_age_hours",
            _require_nonnegative_decimal("queue_age_hours", self.queue_age_hours),
        )
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        object.__setattr__(
            self,
            "reason_codes",
            _require_reason_codes(self.reason_codes, require_nonempty=True),
        )
        _validate_row(self)
        _require_hard_flags("row", self)


@dataclass(frozen=True)
class ResearchTeamMemoryConflictQueueReasonCodeCount(_FinalPublicDataclass):
    reason_code: str
    count: Decimal
    memory_conflict_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchTeamMemoryConflictQueueReasonCodeCount,
            "reason_code_count",
        )
        _require_public_string("reason_code", self.reason_code)
        object.__setattr__(self, "count", _require_count_decimal("count", self.count))
        object.__setattr__(
            self,
            "memory_conflict_ratio",
            _require_ratio_decimal("memory_conflict_ratio", self.memory_conflict_ratio),
        )
        _require_hard_flags("reason_code_count", self)


@dataclass(frozen=True)
class ResearchTeamMemoryConflictQueueReport(_FinalPublicDataclass):
    generated_at: datetime
    config_version: str
    memory_conflict_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    contradictory_lesson_total: Decimal
    stale_calibration_total: Decimal
    unresolved_review_note_total: Decimal
    domain_escalation_fit_count: Decimal
    max_queue_urgency_score: Decimal
    oldest_queue_age_hours: Decimal
    status: str
    paper_queue_action: str
    reason_codes: tuple[str, ...]
    reason_code_counts: tuple[ResearchTeamMemoryConflictQueueReasonCodeCount, ...]
    rows: tuple[ResearchTeamMemoryConflictQueueRow, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchTeamMemoryConflictQueueReport, "report")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_TEAM_MEMORY_CONFLICT_QUEUE_REPORT_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "memory_conflict_count",
            "pass_count",
            "watch_count",
            "block_count",
            "contradictory_lesson_total",
            "stale_calibration_total",
            "unresolved_review_note_total",
            "domain_escalation_fit_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_count_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in ("max_queue_urgency_score", "oldest_queue_age_hours"):
            if field_name.endswith("_score"):
                normalized = _require_ratio_decimal(field_name, getattr(self, field_name))
            else:
                normalized = _require_nonnegative_decimal(
                    field_name,
                    getattr(self, field_name),
                )
            object.__setattr__(self, field_name, normalized)
        _require_status("status", self.status)
        _require_public_string("paper_queue_action", self.paper_queue_action)
        if self.paper_queue_action != PAPER_ACTION_BY_STATUS[self.status]:
            raise ValueError("paper_queue_action must match status")
        object.__setattr__(
            self,
            "reason_codes",
            _require_report_reason_codes(self.reason_codes),
        )
        object.__setattr__(
            self,
            "reason_code_counts",
            _require_reason_code_counts(self.reason_code_counts),
        )
        object.__setattr__(self, "rows", _require_rows(self.rows))
        if self.derived_validation_digest:
            _require_sha256("derived_validation_digest", self.derived_validation_digest)
            if self.derived_validation_digest != _derived_validation_digest(self):
                raise ValueError("derived_validation_digest does not match report payload")
        else:
            object.__setattr__(
                self,
                "derived_validation_digest",
                _derived_validation_digest(self),
            )
        _validate_report_materialized_fields(self)
        _reject_unsafe_public_payload("report", self)
        _require_hard_flags("report", self)


def build_research_team_memory_conflict_queue_report(
    memory_conflicts: Iterable[ResearchTeamMemoryConflictQueueInput],
    *,
    config: ResearchTeamMemoryConflictQueueConfig,
    generated_at: datetime,
) -> ResearchTeamMemoryConflictQueueReport:
    if type(config) is not ResearchTeamMemoryConflictQueueConfig:
        raise ValueError("config must be a ResearchTeamMemoryConflictQueueConfig")
    _require_hard_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    inputs = _normalize_inputs(memory_conflicts)
    rows = tuple(
        sorted(
            (
                _row_from_input(item, config=config, generated_at=generated_at_utc)
                for item in inputs
            ),
            key=_row_sort_key,
        ),
    )
    status = _rollup_status(tuple(row.conflict_status for row in rows))
    return ResearchTeamMemoryConflictQueueReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        memory_conflict_count=_count(len(rows)),
        pass_count=_status_count(rows, "pass"),
        watch_count=_status_count(rows, "watch"),
        block_count=_status_count(rows, "block"),
        contradictory_lesson_total=_sum_counts(
            tuple(row.contradictory_lesson_count for row in rows),
        ),
        stale_calibration_total=_sum_counts(
            tuple(row.stale_calibration_count for row in rows),
        ),
        unresolved_review_note_total=_sum_counts(
            tuple(row.unresolved_review_note_count for row in rows),
        ),
        domain_escalation_fit_count=_count(
            sum(
                1
                for row in rows
                if row.domain_escalation_fit_score
                >= config.watch_domain_escalation_fit_score
            ),
        ),
        max_queue_urgency_score=_max_decimal(
            tuple(row.queue_urgency_score for row in rows),
        ),
        oldest_queue_age_hours=_max_decimal(tuple(row.queue_age_hours for row in rows)),
        status=status,
        paper_queue_action=PAPER_ACTION_BY_STATUS[status],
        reason_codes=_report_reason_codes(rows),
        reason_code_counts=_reason_code_counts(rows),
        rows=rows,
    )


def research_team_memory_conflict_queue_report_payload(
    report: ResearchTeamMemoryConflictQueueReport | dict[str, Any],
) -> dict[str, Any]:
    if type(report) is ResearchTeamMemoryConflictQueueReport:
        _require_hard_flags("report", report)
        _reject_unsafe_public_payload("report", report)
        if report.derived_validation_digest != _derived_validation_digest(report):
            raise ValueError("derived_validation_digest does not match report payload")
        _validate_report_materialized_fields(report)
        payload = _json_ready(report)
        if type(payload) is not dict:
            raise ValueError("report payload must be an object")
        _reject_unsafe_public_payload("payload", payload)
        _reject_public_numeric_values(payload)
        return payload
    if type(report) is dict:
        _reject_unsafe_public_payload("payload", report)
        _reject_public_numeric_values(report)
        payload = _json_ready(report)
        if type(payload) is not dict:
            raise ValueError("report payload must be an object")
        _require_hard_flags("payload", _PayloadFlags(payload))
        if "derived_validation_digest" not in payload:
            raise ValueError("derived_validation_digest is required")
        supplied_digest = payload["derived_validation_digest"]
        _require_sha256("derived_validation_digest", supplied_digest)
        if supplied_digest != _payload_validation_digest(payload):
            raise ValueError("derived_validation_digest does not match report payload")
        return payload
    raise ValueError("report must be a ResearchTeamMemoryConflictQueueReport")


@dataclass(frozen=True)
class _PayloadFlags:
    value: dict[str, Any]

    @property
    def paper_only(self) -> object:
        if "paper_only" not in self.value:
            return None
        return self.value["paper_only"]

    @property
    def report_only(self) -> object:
        if "report_only" not in self.value:
            return None
        return self.value["report_only"]

    @property
    def readonly(self) -> object:
        if "readonly" not in self.value:
            return None
        return self.value["readonly"]


def _normalize_inputs(
    memory_conflicts: Iterable[ResearchTeamMemoryConflictQueueInput],
) -> tuple[ResearchTeamMemoryConflictQueueInput, ...]:
    if isinstance(memory_conflicts, (str, bytes)):
        raise ValueError("memory_conflicts must be an iterable")
    try:
        items = tuple(memory_conflicts)
    except TypeError as exc:
        raise ValueError("memory_conflicts must be an iterable") from exc
    seen: set[tuple[str, str]] = set()
    for item in items:
        if type(item) is not ResearchTeamMemoryConflictQueueInput:
            raise ValueError(
                "memory_conflicts must contain ResearchTeamMemoryConflictQueueInput",
            )
        _require_hard_flags("input", item)
        key = (item.specialist_key, item.aggregate_label)
        if key in seen:
            raise ValueError("memory_conflicts must contain unique aggregate labels")
        seen.add(key)
    return items


def _row_from_input(
    item: ResearchTeamMemoryConflictQueueInput,
    *,
    config: ResearchTeamMemoryConflictQueueConfig,
    generated_at: datetime,
) -> ResearchTeamMemoryConflictQueueRow:
    if item.observed_at > generated_at:
        raise ValueError("observed_at must not be in the future")
    queue_urgency_score = _queue_urgency_score(item, config)
    reason_codes = _row_reason_codes(
        item,
        config=config,
        queue_urgency_score=queue_urgency_score,
    )
    return ResearchTeamMemoryConflictQueueRow(
        specialist_key=item.specialist_key,
        aggregate_label=item.aggregate_label,
        conflict_status=_row_status(reason_codes),
        contradictory_lesson_count=item.contradictory_lesson_count,
        stale_calibration_count=item.stale_calibration_count,
        unresolved_review_note_count=item.unresolved_review_note_count,
        domain_escalation_fit_score=item.domain_escalation_fit_score,
        queue_age_hours=item.queue_age_hours,
        queue_urgency_score=queue_urgency_score,
        observed_at=item.observed_at,
        reason_codes=reason_codes,
    )


def _queue_urgency_score(
    item: ResearchTeamMemoryConflictQueueInput,
    config: ResearchTeamMemoryConflictQueueConfig,
) -> Decimal:
    age_pressure = _ratio_capped(item.queue_age_hours, config.block_queue_age_hours)
    return _max_decimal((item.domain_escalation_fit_score, age_pressure))


def _row_reason_codes(
    item: ResearchTeamMemoryConflictQueueInput,
    *,
    config: ResearchTeamMemoryConflictQueueConfig,
    queue_urgency_score: Decimal,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    if item.contradictory_lesson_count >= config.block_contradictory_lesson_count:
        reason_codes.append("contradictory_lessons_block")
    elif item.contradictory_lesson_count >= config.watch_contradictory_lesson_count:
        reason_codes.append("contradictory_lessons_watch")

    if item.stale_calibration_count >= config.block_stale_calibration_count:
        reason_codes.append("stale_calibrations_block")
    elif item.stale_calibration_count >= config.watch_stale_calibration_count:
        reason_codes.append("stale_calibrations_watch")

    if item.unresolved_review_note_count >= config.block_unresolved_review_note_count:
        reason_codes.append("unresolved_review_notes_block")
    elif item.unresolved_review_note_count >= config.watch_unresolved_review_note_count:
        reason_codes.append("unresolved_review_notes_watch")

    if item.domain_escalation_fit_score >= config.block_domain_escalation_fit_score:
        reason_codes.append("domain_escalation_fit_block")
    elif item.domain_escalation_fit_score >= config.watch_domain_escalation_fit_score:
        reason_codes.append("domain_escalation_fit_watch")

    if item.queue_age_hours >= config.block_queue_age_hours:
        reason_codes.append("queue_age_block")
    elif item.queue_age_hours >= config.watch_queue_age_hours:
        reason_codes.append("queue_age_watch")

    if queue_urgency_score >= config.block_queue_urgency_score:
        reason_codes.append("queue_urgency_block")
    elif queue_urgency_score >= config.watch_queue_urgency_score:
        reason_codes.append("queue_urgency_watch")

    if not reason_codes:
        reason_codes.append(PASS_ROW_REASON_CODE)
    return tuple(reason_codes)


def _row_status(reason_codes: tuple[str, ...]) -> str:
    if any(reason_code in BLOCK_REASON_CODES for reason_code in reason_codes):
        return "block"
    if any(reason_code in WATCH_REASON_CODES for reason_code in reason_codes):
        return "watch"
    return "pass"


def _rollup_status(statuses: tuple[str, ...]) -> str:
    if any(status == "block" for status in statuses):
        return "block"
    if any(status == "watch" for status in statuses):
        return "watch"
    return "pass"


def _report_reason_codes(
    rows: tuple[ResearchTeamMemoryConflictQueueRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return (EMPTY_REPORT_REASON_CODE,)
    status = _rollup_status(tuple(row.conflict_status for row in rows))
    reason_codes = [
        f"memory_conflict_queue_{'clear' if status == 'pass' else status}",
    ]
    row_reasons = frozenset(
        reason_code
        for row in rows
        for reason_code in row.reason_codes
        if reason_code != PASS_ROW_REASON_CODE
    )
    for reason_code in REPORT_REASON_PRIORITY:
        if reason_code in row_reasons:
            reason_codes.append(reason_code)
    return tuple(reason_codes)


def _reason_code_counts(
    rows: tuple[ResearchTeamMemoryConflictQueueRow, ...],
) -> tuple[ResearchTeamMemoryConflictQueueReasonCodeCount, ...]:
    if not rows:
        return ()
    counter: Counter[str] = Counter()
    for row in rows:
        counter.update(row.reason_codes)
    denominator = _count(len(rows))
    priority = {
        reason_code: index
        for index, reason_code in enumerate(
            (PASS_ROW_REASON_CODE,) + BLOCK_REASON_CODES + WATCH_REASON_CODES,
        )
    }
    return tuple(
        ResearchTeamMemoryConflictQueueReasonCodeCount(
            reason_code=reason_code,
            count=count,
            memory_conflict_ratio=_ratio(count, denominator),
        )
        for count, reason_code in sorted(
            ((_count(count), reason_code) for reason_code, count in counter.items()),
            key=lambda item: (
                -item[0],
                priority[item[1]] if item[1] in priority else 999,
                item[1],
            ),
        )
    )


def _row_sort_key(
    row: ResearchTeamMemoryConflictQueueRow,
) -> tuple[Decimal, Decimal, str, str]:
    return (
        -STATUS_WEIGHT[row.conflict_status],
        -_row_severity_score(row),
        row.specialist_key,
        row.aggregate_label,
    )


def _row_severity_score(row: ResearchTeamMemoryConflictQueueRow) -> Decimal:
    severity = STATUS_WEIGHT[row.conflict_status]
    severity += row.queue_urgency_score
    severity += _ratio_capped(row.contradictory_lesson_count, Decimal("10"))
    severity += _ratio_capped(row.stale_calibration_count, Decimal("10"))
    severity += _ratio_capped(row.unresolved_review_note_count, Decimal("10"))
    return _quantize_ratio(severity)


def _status_count(
    rows: tuple[ResearchTeamMemoryConflictQueueRow, ...],
    status: str,
) -> Decimal:
    return _count(sum(1 for row in rows if row.conflict_status == status))


def _validate_config(config: ResearchTeamMemoryConflictQueueConfig) -> None:
    if (
        config.block_contradictory_lesson_count
        < config.watch_contradictory_lesson_count
    ):
        raise ValueError(
            "block_contradictory_lesson_count must be at least "
            "watch_contradictory_lesson_count",
        )
    if config.block_stale_calibration_count < config.watch_stale_calibration_count:
        raise ValueError(
            "block_stale_calibration_count must be at least "
            "watch_stale_calibration_count",
        )
    if (
        config.block_unresolved_review_note_count
        < config.watch_unresolved_review_note_count
    ):
        raise ValueError(
            "block_unresolved_review_note_count must be at least "
            "watch_unresolved_review_note_count",
        )
    if (
        config.block_domain_escalation_fit_score
        < config.watch_domain_escalation_fit_score
    ):
        raise ValueError(
            "block_domain_escalation_fit_score must be at least "
            "watch_domain_escalation_fit_score",
        )
    if config.block_queue_age_hours < config.watch_queue_age_hours:
        raise ValueError("block_queue_age_hours must be at least watch_queue_age_hours")
    if config.block_queue_urgency_score < config.watch_queue_urgency_score:
        raise ValueError(
            "block_queue_urgency_score must be at least watch_queue_urgency_score",
        )


def _validate_row(row: ResearchTeamMemoryConflictQueueRow) -> None:
    if row.conflict_status != _row_status(row.reason_codes):
        raise ValueError("conflict_status must match reason_codes")
    if row.conflict_status == "pass" and row.reason_codes != (PASS_ROW_REASON_CODE,):
        raise ValueError("pass rows require memory_conflict_queue_clear")
    if row.conflict_status != "pass" and PASS_ROW_REASON_CODE in row.reason_codes:
        raise ValueError("queued rows must not contain clear reason_codes")


def _validate_report_materialized_fields(
    report: ResearchTeamMemoryConflictQueueReport,
) -> None:
    rows = report.rows
    checks = {
        "memory_conflict_count": _count(len(rows)),
        "pass_count": _status_count(rows, "pass"),
        "watch_count": _status_count(rows, "watch"),
        "block_count": _status_count(rows, "block"),
        "contradictory_lesson_total": _sum_counts(
            tuple(row.contradictory_lesson_count for row in rows),
        ),
        "stale_calibration_total": _sum_counts(
            tuple(row.stale_calibration_count for row in rows),
        ),
        "unresolved_review_note_total": _sum_counts(
            tuple(row.unresolved_review_note_count for row in rows),
        ),
        "domain_escalation_fit_count": _count(
            sum(
                1
                for row in rows
                if "domain_escalation_fit_block" in row.reason_codes
                or "domain_escalation_fit_watch" in row.reason_codes
            ),
        ),
        "max_queue_urgency_score": _max_decimal(
            tuple(row.queue_urgency_score for row in rows),
        ),
        "oldest_queue_age_hours": _max_decimal(tuple(row.queue_age_hours for row in rows)),
    }
    for field_name, expected in checks.items():
        if getattr(report, field_name) != expected:
            raise ValueError(f"{field_name} must match rows")
    expected_status = _rollup_status(tuple(row.conflict_status for row in rows))
    if report.status != expected_status:
        raise ValueError("status must match rows")
    if report.paper_queue_action != PAPER_ACTION_BY_STATUS[report.status]:
        raise ValueError("paper_queue_action must match status")
    if report.reason_codes != _report_reason_codes(rows):
        raise ValueError("reason_codes must match rows")
    if report.reason_code_counts != _reason_code_counts(rows):
        raise ValueError("reason_code_counts must match rows")


def _require_rows(
    rows: tuple[ResearchTeamMemoryConflictQueueRow, ...],
) -> tuple[ResearchTeamMemoryConflictQueueRow, ...]:
    if isinstance(rows, (str, bytes)):
        raise ValueError("rows must be an iterable")
    try:
        normalized = tuple(rows)
    except TypeError as exc:
        raise ValueError("rows must be an iterable") from exc
    seen: set[tuple[str, str]] = set()
    for row in normalized:
        if type(row) is not ResearchTeamMemoryConflictQueueRow:
            raise ValueError("rows must contain ResearchTeamMemoryConflictQueueRow")
        _require_hard_flags("row", row)
        key = (row.specialist_key, row.aggregate_label)
        if key in seen:
            raise ValueError("rows must contain unique aggregate labels")
        seen.add(key)
    if normalized != tuple(sorted(normalized, key=_row_sort_key)):
        raise ValueError("rows must be sorted by status and aggregate label")
    return normalized


def _require_reason_code_counts(
    rows: tuple[ResearchTeamMemoryConflictQueueReasonCodeCount, ...],
) -> tuple[ResearchTeamMemoryConflictQueueReasonCodeCount, ...]:
    if isinstance(rows, (str, bytes)):
        raise ValueError("reason_code_counts must be an iterable")
    try:
        normalized = tuple(rows)
    except TypeError as exc:
        raise ValueError("reason_code_counts must be an iterable") from exc
    for row in normalized:
        if type(row) is not ResearchTeamMemoryConflictQueueReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "ResearchTeamMemoryConflictQueueReasonCodeCount",
            )
        _require_hard_flags("reason_code_count", row)
    if len({row.reason_code for row in normalized}) != len(normalized):
        raise ValueError("reason_code_counts reason_code values must be unique")
    return normalized


def _require_exact_type(value: object, expected_type: type[object], label: str) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{label} must be a {expected_type.__name__}")


def _require_hard_flags(label: str, value: object) -> None:
    require_paper_only_flags(label, value)


def _require_safe_label(field_name: str, value: object) -> None:
    _require_public_string(field_name, value)
    allowed = set("abcdefghijklmnopqrstuvwxyz0123456789_")
    if any(character not in allowed for character in value):
        raise ValueError(f"{field_name} must be lowercase snake case")


def _require_public_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical non-empty string")
    if any(character.isspace() for character in value):
        raise ValueError(f"{field_name} must not contain whitespace")
    _reject_unsafe_public_text(field_name, value)


def _require_reason_codes(
    reason_codes: tuple[str, ...],
    *,
    require_nonempty: bool,
) -> tuple[str, ...]:
    if isinstance(reason_codes, (str, bytes)):
        raise ValueError("reason_codes must be an iterable")
    try:
        normalized = tuple(reason_codes)
    except TypeError as exc:
        raise ValueError("reason_codes must be an iterable") from exc
    if require_nonempty and not normalized:
        raise ValueError("reason_codes must be non-empty")
    for reason_code in normalized:
        _require_public_string("reason_code", reason_code)
        if reason_code.lower() != reason_code:
            raise ValueError("reason_code must be lowercase")
        if reason_code not in ROW_REASON_CODES:
            raise ValueError("reason_code must be supported")
    if len(set(normalized)) != len(normalized):
        raise ValueError("reason_codes must be unique")
    return normalized


def _require_report_reason_codes(reason_codes: tuple[str, ...]) -> tuple[str, ...]:
    if isinstance(reason_codes, (str, bytes)):
        raise ValueError("reason_codes must be an iterable")
    try:
        normalized = tuple(reason_codes)
    except TypeError as exc:
        raise ValueError("reason_codes must be an iterable") from exc
    if not normalized:
        raise ValueError("reason_codes must be non-empty")
    for reason_code in normalized:
        _require_public_string("reason_code", reason_code)
        if not (
            reason_code in REPORT_REASON_PRIORITY
            or reason_code in {EMPTY_REPORT_REASON_CODE}
            or reason_code.startswith("memory_conflict_queue_")
        ):
            raise ValueError("reason_code must be supported")
    if len(set(normalized)) != len(normalized):
        raise ValueError("reason_codes must be unique")
    return normalized


def _require_status(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if value not in STATUSES:
        raise ValueError(f"{field_name} must be one of pass, watch, block")


def _as_utc(field_name: str, value: datetime) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if value.is_nan() or value.is_infinite():
        raise ValueError(f"{field_name} must be finite")
    return value


def _require_count_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < ZERO_COUNT:
        raise ValueError(f"{field_name} must be non-negative")
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{field_name} must be integral")
    return normalized.quantize(COUNT_QUANTUM)


def _require_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < ZERO_COUNT:
        raise ValueError(f"{field_name} must be non-negative")
    return _quantize_ratio(normalized)


def _require_positive_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_nonnegative_decimal(field_name, value)
    if normalized <= ZERO_RATIO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _require_ratio_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_nonnegative_decimal(field_name, value)
    if normalized > ONE_RATIO:
        raise ValueError(f"{field_name} must be no greater than 1")
    return normalized


def _quantize_ratio(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(RATIO_QUANTUM)


def _count(value: int) -> Decimal:
    return Decimal(value).quantize(COUNT_QUANTUM)


def _sum_counts(values: tuple[Decimal, ...]) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        total = sum(values, ZERO_COUNT)
    return total.quantize(COUNT_QUANTUM)


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO_COUNT:
        return ZERO_RATIO
    with localcontext(DECIMAL_CONTEXT):
        return (numerator / denominator).quantize(RATIO_QUANTUM)


def _ratio_capped(numerator: Decimal, denominator: Decimal) -> Decimal:
    value = _ratio(numerator, denominator)
    if value > ONE_RATIO:
        return ONE_RATIO
    return value


def _max_decimal(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return ZERO_RATIO
    return max(values).quantize(RATIO_QUANTUM)


def _require_sha256(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a sha256 hex digest")
    if len(value) != 64 or any(character not in HEX_CHARS for character in value):
        raise ValueError(f"{field_name} must be a sha256 hex digest")


def _derived_validation_digest(
    report: ResearchTeamMemoryConflictQueueReport,
) -> str:
    payload = _json_ready_without_digest(report)
    return _payload_validation_digest(payload)


def _payload_validation_digest(payload: dict[str, Any]) -> str:
    digest_payload = _strip_digest(payload)
    canonical = json.dumps(digest_payload, sort_keys=True, separators=(",", ":"))
    return sha256(canonical.encode("utf-8")).hexdigest()


def _strip_digest(value: Any) -> Any:
    if isinstance(value, dict):
        return {
            key: _strip_digest(item)
            for key, item in sorted(value.items())
            if key != "derived_validation_digest"
        }
    if isinstance(value, list):
        return [_strip_digest(item) for item in value]
    return value


def _json_ready_without_digest(
    report: ResearchTeamMemoryConflictQueueReport,
) -> dict[str, Any]:
    payload = _json_ready(report)
    if type(payload) is not dict:
        raise ValueError("report payload must be an object")
    payload.pop("derived_validation_digest", None)
    return payload


def _json_ready(value: object) -> Any:
    if is_dataclass(value) and not isinstance(value, type):
        return {field.name: _json_ready(getattr(value, field.name)) for field in fields(value)}
    if type(value) is datetime:
        return _as_utc("datetime", value).isoformat()
    if type(value) is Decimal:
        return str(value)
    if type(value) is tuple:
        return [_json_ready(item) for item in value]
    if type(value) is list:
        return [_json_ready(item) for item in value]
    if type(value) is dict:
        return {str(key): _json_ready(item) for key, item in value.items()}
    if type(value) in (str, bool) or value is None:
        return value
    raise ValueError(f"unsupported payload value type: {type(value).__name__}")


def _reject_public_numeric_values(value: object) -> None:
    if type(value) in (int, float):
        raise ValueError("public payload numeric values must be Decimal-derived strings")
    if isinstance(value, dict):
        for item in value.values():
            _reject_public_numeric_values(item)
    elif isinstance(value, (list, tuple)):
        for item in value:
            _reject_public_numeric_values(item)


def _reject_unsafe_public_payload(label: str, value: object) -> None:
    if is_dataclass(value) and not isinstance(value, type):
        for field in fields(value):
            _reject_unsafe_public_text(f"{label}.{field.name}", field.name)
            _reject_unsafe_public_payload(
                f"{label}.{field.name}",
                getattr(value, field.name),
            )
        return
    if isinstance(value, dict):
        for key, item in value.items():
            _reject_unsafe_public_text(f"{label}.key", str(key))
            _reject_unsafe_public_payload(f"{label}.{key}", item)
        return
    if isinstance(value, (list, tuple)):
        for item in value:
            _reject_unsafe_public_payload(label, item)
        return
    if type(value) is str:
        _reject_unsafe_public_text(label, value)


def _reject_unsafe_public_text(field_name: str, value: str) -> None:
    lowered = value.lower()
    if any(fragment in lowered for fragment in UNSAFE_PUBLIC_FRAGMENTS):
        raise ValueError(f"unsafe public value for {field_name}")
    if "://" in lowered:
        raise ValueError(f"unsafe public value for {field_name}")
    if "@" in lowered:
        raise ValueError(f"unsafe public value for {field_name}")
