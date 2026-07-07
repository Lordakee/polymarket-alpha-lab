"""Report-only priority scoring for specialist memory refresh."""

from __future__ import annotations

from dataclasses import dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
import json
import re
from typing import Any, Iterable


DEFAULT_TEAM_SPECIALIST_MEMORY_REFRESH_PRIORITY_CONFIG_VERSION = (
    "team-specialist-memory-refresh-priority-v1"
)

DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
SIX = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")

STATUS_PASS = "pass"
STATUS_WATCH = "watch"
STATUS_BLOCK = "block"
MEMORY_REFRESH_STATUSES = (STATUS_PASS, STATUS_WATCH, STATUS_BLOCK)

ROW_REASON_CODES = (
    "memory_refresh_pass",
    "memory_refresh_watch",
    "memory_refresh_block",
    "stale_memory_watch",
    "stale_memory_limit",
    "unresolved_feedback_watch",
    "unresolved_feedback_limit",
    "memory_age_watch",
    "memory_age_limit",
    "accuracy_watch",
    "accuracy_limit",
    "coverage_gap_watch",
    "coverage_gap_limit",
    "refresh_priority_score_watch",
    "refresh_priority_score_limit",
)
REPORT_REASON_CODES = (
    "memory_refresh_pass",
    "memory_refresh_watch",
    "memory_refresh_block",
    "memory_refresh_empty",
)
UNSAFE_PUBLIC_TEXT_TOKENS = frozenset(
    {
        "auth",
        "buy",
        "candidate",
        "dsn",
        "market",
        "order",
        "question",
        "recommendation",
        "ref",
        "refs",
        "sell",
        "secret",
        "slug",
        "source",
        "sources",
        "table",
        "tables",
        "text",
        "token",
        "trade",
        "url",
        "urls",
        "wallet",
    },
)
UNSAFE_PUBLIC_TEXT_PHRASES = (
    "http://",
    "https://",
    "position sizing",
    "position-sizing",
)
PUBLIC_TOKEN_RE = re.compile(r"[a-z0-9]+")

__all__ = (
    "DEFAULT_TEAM_SPECIALIST_MEMORY_REFRESH_PRIORITY_CONFIG_VERSION",
    "MEMORY_REFRESH_STATUSES",
    "TeamSpecialistMemoryRefreshPriorityConfig",
    "TeamSpecialistMemoryRefreshPriorityInput",
    "TeamSpecialistMemoryRefreshPriorityRow",
    "TeamSpecialistMemoryRefreshPriorityReport",
    "build_team_specialist_memory_refresh_priority",
    "team_specialist_memory_refresh_priority_payload",
    "validate_team_specialist_memory_refresh_priority_payload",
)


class _FinalPublicDataclass:
    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if not cls.__name__.startswith("TeamSpecialistMemoryRefreshPriority"):
            raise TypeError("public dataclasses do not support subclassing")


@dataclass(frozen=True)
class TeamSpecialistMemoryRefreshPriorityConfig(_FinalPublicDataclass):
    config_version: str = DEFAULT_TEAM_SPECIALIST_MEMORY_REFRESH_PRIORITY_CONFIG_VERSION
    stale_memory_weight: Decimal = Decimal("0.300000")
    unresolved_feedback_weight: Decimal = Decimal("0.250000")
    memory_age_weight: Decimal = Decimal("0.200000")
    accuracy_risk_weight: Decimal = Decimal("0.150000")
    coverage_gap_weight: Decimal = Decimal("0.100000")
    max_average_memory_age_days: Decimal = Decimal("30.000000")
    stale_memory_watch_ratio: Decimal = Decimal("0.250000")
    stale_memory_block_ratio: Decimal = Decimal("0.500000")
    unresolved_feedback_watch_count: Decimal = Decimal("1.000000")
    unresolved_feedback_block_count: Decimal = Decimal("3.000000")
    average_memory_age_watch_days: Decimal = Decimal("14.000000")
    average_memory_age_block_days: Decimal = Decimal("30.000000")
    recent_accuracy_watch_floor: Decimal = Decimal("0.700000")
    recent_accuracy_block_floor: Decimal = Decimal("0.500000")
    coverage_gap_watch_score: Decimal = Decimal("0.500000")
    coverage_gap_block_score: Decimal = Decimal("0.850000")
    watch_score_floor: Decimal = Decimal("0.300000")
    block_score_floor: Decimal = Decimal("0.700000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, TeamSpecialistMemoryRefreshPriorityConfig, "config")
        object.__setattr__(
            self,
            "config_version",
            _require_public_string("config_version", self.config_version),
        )
        for field_name in (
            "stale_memory_weight",
            "unresolved_feedback_weight",
            "memory_age_weight",
            "accuracy_risk_weight",
            "coverage_gap_weight",
            "stale_memory_watch_ratio",
            "stale_memory_block_ratio",
            "recent_accuracy_watch_floor",
            "recent_accuracy_block_floor",
            "coverage_gap_watch_score",
            "coverage_gap_block_score",
            "watch_score_floor",
            "block_score_floor",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "unresolved_feedback_watch_count",
            "unresolved_feedback_block_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_count_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "max_average_memory_age_days",
            "average_memory_age_watch_days",
            "average_memory_age_block_days",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_positive_decimal(field_name, getattr(self, field_name)),
            )
        _require_decimal_equal(
            "refresh priority weights",
            self.stale_memory_weight
            + self.unresolved_feedback_weight
            + self.memory_age_weight
            + self.accuracy_risk_weight
            + self.coverage_gap_weight,
            ONE,
        )
        if self.stale_memory_watch_ratio > self.stale_memory_block_ratio:
            raise ValueError("stale_memory_watch_ratio must be at most stale_memory_block_ratio")
        if self.unresolved_feedback_watch_count > self.unresolved_feedback_block_count:
            raise ValueError(
                "unresolved_feedback_watch_count must be at most unresolved_feedback_block_count",
            )
        if self.average_memory_age_watch_days > self.average_memory_age_block_days:
            raise ValueError(
                "average_memory_age_watch_days must be at most average_memory_age_block_days",
            )
        if self.recent_accuracy_block_floor > self.recent_accuracy_watch_floor:
            raise ValueError(
                "recent_accuracy_block_floor must be at most recent_accuracy_watch_floor",
            )
        if self.coverage_gap_watch_score > self.coverage_gap_block_score:
            raise ValueError("coverage_gap_watch_score must be at most coverage_gap_block_score")
        if self.watch_score_floor > self.block_score_floor:
            raise ValueError("watch_score_floor must be at most block_score_floor")
        _require_hard_flags("config", self)
        _reject_unsafe_public_payload("config", _payload_value(self))


@dataclass(frozen=True)
class TeamSpecialistMemoryRefreshPriorityInput(_FinalPublicDataclass):
    team_id: str
    specialist_id: str
    memory_item_count: Decimal
    stale_memory_count: Decimal
    unresolved_feedback_count: Decimal
    average_memory_age_days: Decimal
    recent_accuracy_score: Decimal
    coverage_gap_score: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, TeamSpecialistMemoryRefreshPriorityInput, "input")
        for field_name in ("team_id", "specialist_id"):
            object.__setattr__(
                self,
                field_name,
                _require_public_string(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "memory_item_count",
            "stale_memory_count",
            "unresolved_feedback_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_count_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "average_memory_age_days",
            _require_nonnegative_decimal(
                "average_memory_age_days",
                self.average_memory_age_days,
            ),
        )
        for field_name in ("recent_accuracy_score", "coverage_gap_score"):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        if self.stale_memory_count > self.memory_item_count:
            raise ValueError("stale_memory_count must be at most memory_item_count")
        _require_hard_flags("input", self)
        _reject_unsafe_public_payload("input", _payload_value(self))


@dataclass(frozen=True)
class TeamSpecialistMemoryRefreshPriorityRow(_FinalPublicDataclass):
    rank: Decimal
    team_id: str
    specialist_id: str
    memory_item_count: Decimal
    stale_memory_count: Decimal
    stale_memory_ratio: Decimal
    unresolved_feedback_count: Decimal
    unresolved_feedback_score: Decimal
    average_memory_age_days: Decimal
    memory_age_risk_score: Decimal
    recent_accuracy_score: Decimal
    accuracy_risk_score: Decimal
    coverage_gap_score: Decimal
    refresh_priority_score: Decimal
    refresh_status: str
    reason_codes: tuple[str, ...]
    derived_validation_digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, TeamSpecialistMemoryRefreshPriorityRow, "row")
        object.__setattr__(self, "rank", _require_positive_count_decimal("rank", self.rank))
        for field_name in ("team_id", "specialist_id"):
            object.__setattr__(
                self,
                field_name,
                _require_public_string(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "memory_item_count",
            "stale_memory_count",
            "unresolved_feedback_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_count_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "average_memory_age_days",
            _require_nonnegative_decimal(
                "average_memory_age_days",
                self.average_memory_age_days,
            ),
        )
        for field_name in (
            "stale_memory_ratio",
            "unresolved_feedback_score",
            "memory_age_risk_score",
            "recent_accuracy_score",
            "accuracy_risk_score",
            "coverage_gap_score",
            "refresh_priority_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "refresh_status",
            _require_status("refresh_status", self.refresh_status),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _require_reason_codes("reason_codes", self.reason_codes, ROW_REASON_CODES),
        )
        _require_digest("derived_validation_digest", self.derived_validation_digest)
        if self.stale_memory_count > self.memory_item_count:
            raise ValueError("stale_memory_count must be at most memory_item_count")
        _require_hard_flags("row", self)
        _validate_row(self)
        _reject_unsafe_public_payload("row", _payload_value(self))
        _require_matching_digest(_payload_value(self))


@dataclass(frozen=True)
class TeamSpecialistMemoryRefreshPriorityReport(_FinalPublicDataclass):
    generated_at: datetime
    config_version: str
    status: str
    row_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    average_refresh_priority_score: Decimal
    top_refresh_priority_score: Decimal
    rows: tuple[TeamSpecialistMemoryRefreshPriorityRow, ...]
    reason_codes: tuple[str, ...]
    derived_validation_digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, TeamSpecialistMemoryRefreshPriorityReport, "report")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        object.__setattr__(
            self,
            "config_version",
            _require_public_string("config_version", self.config_version),
        )
        object.__setattr__(self, "status", _require_status("status", self.status))
        for field_name in ("row_count", "pass_count", "watch_count", "block_count"):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_count_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "average_refresh_priority_score",
            "top_refresh_priority_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(self, "rows", _require_rows(self.rows))
        object.__setattr__(
            self,
            "reason_codes",
            _require_reason_codes("reason_codes", self.reason_codes, REPORT_REASON_CODES),
        )
        _require_digest("derived_validation_digest", self.derived_validation_digest)
        _require_hard_flags("report", self)
        _reject_unsafe_public_payload("report", _payload_value(self))
        _validate_report(self)
        _require_matching_digest(_payload_value(self))

    @property
    def payload(self) -> dict[str, Any]:
        return team_specialist_memory_refresh_priority_payload(self)


def build_team_specialist_memory_refresh_priority(
    inputs: Iterable[TeamSpecialistMemoryRefreshPriorityInput],
    *,
    config: TeamSpecialistMemoryRefreshPriorityConfig | None = None,
    generated_at: datetime,
) -> TeamSpecialistMemoryRefreshPriorityReport:
    cfg = config or TeamSpecialistMemoryRefreshPriorityConfig()
    if type(cfg) is not TeamSpecialistMemoryRefreshPriorityConfig:
        raise ValueError("config must be exactly TeamSpecialistMemoryRefreshPriorityConfig")
    _require_hard_flags("config", cfg)
    generated_at_utc = _as_utc("generated_at", generated_at)
    normalized = _normalize_inputs(inputs)
    rows_without_rank = tuple(
        sorted(
            (_row_for_input(item, cfg) for item in normalized),
            key=lambda row: (-row.refresh_priority_score, row.team_id, row.specialist_id),
        ),
    )
    rows = tuple(_row_with_rank(row, index) for index, row in enumerate(rows_without_rank, start=1))
    status = _report_status(rows)
    values: dict[str, Any] = {
        "generated_at": generated_at_utc,
        "config_version": cfg.config_version,
        "status": status,
        "row_count": _count_decimal(len(rows)),
        "pass_count": _status_count(rows, STATUS_PASS),
        "watch_count": _status_count(rows, STATUS_WATCH),
        "block_count": _status_count(rows, STATUS_BLOCK),
        "average_refresh_priority_score": _average(row.refresh_priority_score for row in rows),
        "top_refresh_priority_score": max(
            (row.refresh_priority_score for row in rows),
            default=ZERO,
        ),
        "rows": rows,
        "reason_codes": _report_reason_codes(rows, status),
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    payload = _payload_value(values)
    if type(payload) is not dict:
        raise ValueError("payload must be a dict")
    values["derived_validation_digest"] = _derived_validation_digest(payload)
    return TeamSpecialistMemoryRefreshPriorityReport(**values)


def team_specialist_memory_refresh_priority_payload(
    report: TeamSpecialistMemoryRefreshPriorityReport,
) -> dict[str, Any]:
    if type(report) is not TeamSpecialistMemoryRefreshPriorityReport:
        raise ValueError("report must be exactly TeamSpecialistMemoryRefreshPriorityReport")
    _require_hard_flags("report", report)
    payload = _payload_value(report)
    if type(payload) is not dict:
        raise ValueError("payload must be a dict")
    _reject_unsafe_public_payload("payload", payload)
    _require_matching_digest(payload)
    return payload


def validate_team_specialist_memory_refresh_priority_payload(payload: dict[str, Any]) -> bool:
    if type(payload) is not dict:
        raise ValueError("public payload must be a dict")
    _reject_unsafe_public_payload("payload", payload)
    _require_matching_digest(payload)
    return True


def _row_for_input(
    item: TeamSpecialistMemoryRefreshPriorityInput,
    config: TeamSpecialistMemoryRefreshPriorityConfig,
) -> TeamSpecialistMemoryRefreshPriorityRow:
    stale_memory_ratio = _stale_memory_ratio(item.stale_memory_count, item.memory_item_count)
    unresolved_feedback_score = _unresolved_feedback_score(
        item.unresolved_feedback_count,
        config.unresolved_feedback_block_count,
    )
    memory_age_risk_score = _risk_ratio(
        item.average_memory_age_days,
        config.max_average_memory_age_days,
    )
    accuracy_risk_score = _clamp_ratio(ONE - item.recent_accuracy_score)
    refresh_priority_score = _refresh_priority_score(
        stale_memory_ratio=stale_memory_ratio,
        unresolved_feedback_score=unresolved_feedback_score,
        memory_age_risk_score=memory_age_risk_score,
        accuracy_risk_score=accuracy_risk_score,
        coverage_gap_score=item.coverage_gap_score,
        config=config,
    )
    refresh_status = _row_status(
        stale_memory_ratio=stale_memory_ratio,
        unresolved_feedback_count=item.unresolved_feedback_count,
        average_memory_age_days=item.average_memory_age_days,
        recent_accuracy_score=item.recent_accuracy_score,
        coverage_gap_score=item.coverage_gap_score,
        refresh_priority_score=refresh_priority_score,
        config=config,
    )
    values: dict[str, Any] = {
        "rank": Decimal("1.000000"),
        "team_id": item.team_id,
        "specialist_id": item.specialist_id,
        "memory_item_count": item.memory_item_count,
        "stale_memory_count": item.stale_memory_count,
        "stale_memory_ratio": stale_memory_ratio,
        "unresolved_feedback_count": item.unresolved_feedback_count,
        "unresolved_feedback_score": unresolved_feedback_score,
        "average_memory_age_days": item.average_memory_age_days,
        "memory_age_risk_score": memory_age_risk_score,
        "recent_accuracy_score": item.recent_accuracy_score,
        "accuracy_risk_score": accuracy_risk_score,
        "coverage_gap_score": item.coverage_gap_score,
        "refresh_priority_score": refresh_priority_score,
        "refresh_status": refresh_status,
        "reason_codes": _row_reason_codes(
            stale_memory_ratio=stale_memory_ratio,
            unresolved_feedback_count=item.unresolved_feedback_count,
            average_memory_age_days=item.average_memory_age_days,
            recent_accuracy_score=item.recent_accuracy_score,
            coverage_gap_score=item.coverage_gap_score,
            refresh_priority_score=refresh_priority_score,
            refresh_status=refresh_status,
            config=config,
        ),
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    payload = _payload_value(values)
    if type(payload) is not dict:
        raise ValueError("payload must be a dict")
    values["derived_validation_digest"] = _derived_validation_digest(payload)
    return TeamSpecialistMemoryRefreshPriorityRow(**values)


def _row_with_rank(
    row: TeamSpecialistMemoryRefreshPriorityRow,
    rank: int,
) -> TeamSpecialistMemoryRefreshPriorityRow:
    values = _row_digest_parts(row)
    values["rank"] = _count_decimal(rank)
    payload = _payload_value(values)
    if type(payload) is not dict:
        raise ValueError("payload must be a dict")
    values["derived_validation_digest"] = _derived_validation_digest(payload)
    return TeamSpecialistMemoryRefreshPriorityRow(**values)


def _refresh_priority_score(
    *,
    stale_memory_ratio: Decimal,
    unresolved_feedback_score: Decimal,
    memory_age_risk_score: Decimal,
    accuracy_risk_score: Decimal,
    coverage_gap_score: Decimal,
    config: TeamSpecialistMemoryRefreshPriorityConfig,
) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return _clamp_ratio(
            stale_memory_ratio * config.stale_memory_weight
            + unresolved_feedback_score * config.unresolved_feedback_weight
            + memory_age_risk_score * config.memory_age_weight
            + accuracy_risk_score * config.accuracy_risk_weight
            + coverage_gap_score * config.coverage_gap_weight,
        )


def _row_status(
    *,
    stale_memory_ratio: Decimal,
    unresolved_feedback_count: Decimal,
    average_memory_age_days: Decimal,
    recent_accuracy_score: Decimal,
    coverage_gap_score: Decimal,
    refresh_priority_score: Decimal,
    config: TeamSpecialistMemoryRefreshPriorityConfig,
) -> str:
    if (
        stale_memory_ratio >= config.stale_memory_block_ratio
        or unresolved_feedback_count >= config.unresolved_feedback_block_count
        or average_memory_age_days >= config.average_memory_age_block_days
        or recent_accuracy_score <= config.recent_accuracy_block_floor
        or coverage_gap_score >= config.coverage_gap_block_score
        or refresh_priority_score >= config.block_score_floor
    ):
        return STATUS_BLOCK
    if (
        stale_memory_ratio >= config.stale_memory_watch_ratio
        or unresolved_feedback_count >= config.unresolved_feedback_watch_count
        or average_memory_age_days >= config.average_memory_age_watch_days
        or recent_accuracy_score <= config.recent_accuracy_watch_floor
        or coverage_gap_score >= config.coverage_gap_watch_score
        or refresh_priority_score >= config.watch_score_floor
    ):
        return STATUS_WATCH
    return STATUS_PASS


def _row_reason_codes(
    *,
    stale_memory_ratio: Decimal,
    unresolved_feedback_count: Decimal,
    average_memory_age_days: Decimal,
    recent_accuracy_score: Decimal,
    coverage_gap_score: Decimal,
    refresh_priority_score: Decimal,
    refresh_status: str,
    config: TeamSpecialistMemoryRefreshPriorityConfig,
) -> tuple[str, ...]:
    codes = [f"memory_refresh_{refresh_status}"]
    if stale_memory_ratio >= config.stale_memory_block_ratio:
        codes.append("stale_memory_limit")
    elif stale_memory_ratio >= config.stale_memory_watch_ratio:
        codes.append("stale_memory_watch")
    if unresolved_feedback_count >= config.unresolved_feedback_block_count:
        codes.append("unresolved_feedback_limit")
    elif unresolved_feedback_count >= config.unresolved_feedback_watch_count:
        codes.append("unresolved_feedback_watch")
    if average_memory_age_days >= config.average_memory_age_block_days:
        codes.append("memory_age_limit")
    elif average_memory_age_days >= config.average_memory_age_watch_days:
        codes.append("memory_age_watch")
    if recent_accuracy_score <= config.recent_accuracy_block_floor:
        codes.append("accuracy_limit")
    elif recent_accuracy_score <= config.recent_accuracy_watch_floor:
        codes.append("accuracy_watch")
    if coverage_gap_score >= config.coverage_gap_block_score:
        codes.append("coverage_gap_limit")
    elif coverage_gap_score >= config.coverage_gap_watch_score:
        codes.append("coverage_gap_watch")
    if refresh_priority_score >= config.block_score_floor:
        codes.append("refresh_priority_score_limit")
    elif refresh_priority_score >= config.watch_score_floor:
        codes.append("refresh_priority_score_watch")
    return tuple(code for code in ROW_REASON_CODES if code in codes)


def _report_status(rows: tuple[TeamSpecialistMemoryRefreshPriorityRow, ...]) -> str:
    if not rows:
        return STATUS_WATCH
    if any(row.refresh_status == STATUS_BLOCK for row in rows):
        return STATUS_BLOCK
    if any(row.refresh_status == STATUS_WATCH for row in rows):
        return STATUS_WATCH
    return STATUS_PASS


def _report_reason_codes(
    rows: tuple[TeamSpecialistMemoryRefreshPriorityRow, ...],
    status: str,
) -> tuple[str, ...]:
    if not rows:
        return ("memory_refresh_empty",)
    return (f"memory_refresh_{status}",)


def _normalize_inputs(
    inputs: Iterable[TeamSpecialistMemoryRefreshPriorityInput],
) -> tuple[TeamSpecialistMemoryRefreshPriorityInput, ...]:
    try:
        items = tuple(inputs)
    except TypeError as exc:
        raise ValueError("inputs must be iterable") from exc
    seen: set[tuple[str, str]] = set()
    for item in items:
        if type(item) is not TeamSpecialistMemoryRefreshPriorityInput:
            raise ValueError("inputs must contain TeamSpecialistMemoryRefreshPriorityInput values")
        _require_hard_flags("input", item)
        key = (item.team_id, item.specialist_id)
        if key in seen:
            raise ValueError("inputs must contain unique team and specialist ids")
        seen.add(key)
    return items


def _validate_row(row: TeamSpecialistMemoryRefreshPriorityRow) -> None:
    expected_ratio = _stale_memory_ratio(row.stale_memory_count, row.memory_item_count)
    _require_decimal_equal("stale_memory_ratio", row.stale_memory_ratio, expected_ratio)


def _validate_report(report: TeamSpecialistMemoryRefreshPriorityReport) -> None:
    rows = report.rows
    _require_decimal_equal("row_count", report.row_count, _count_decimal(len(rows)))
    _require_decimal_equal("pass_count", report.pass_count, _status_count(rows, STATUS_PASS))
    _require_decimal_equal("watch_count", report.watch_count, _status_count(rows, STATUS_WATCH))
    _require_decimal_equal("block_count", report.block_count, _status_count(rows, STATUS_BLOCK))
    _require_decimal_equal(
        "average_refresh_priority_score",
        report.average_refresh_priority_score,
        _average(row.refresh_priority_score for row in rows),
    )
    _require_decimal_equal(
        "top_refresh_priority_score",
        report.top_refresh_priority_score,
        max((row.refresh_priority_score for row in rows), default=ZERO),
    )
    if report.status != _report_status(rows):
        raise ValueError("status must equal derived report status")
    if report.reason_codes != _report_reason_codes(rows, report.status):
        raise ValueError("reason_codes must equal derived report reason codes")
    expected_ranks = tuple(_count_decimal(index) for index in range(1, len(rows) + 1))
    if tuple(row.rank for row in rows) != expected_ranks:
        raise ValueError("row ranks must be sequential")


def _status_count(
    rows: tuple[TeamSpecialistMemoryRefreshPriorityRow, ...],
    status: str,
) -> Decimal:
    return _count_decimal(sum(row.refresh_status == status for row in rows))


def _average(values: Iterable[Decimal]) -> Decimal:
    items = tuple(values)
    if not items:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return _six(sum(items, ZERO) / Decimal(len(items)))


def _stale_memory_ratio(stale_memory_count: Decimal, memory_item_count: Decimal) -> Decimal:
    if memory_item_count == ZERO:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return _clamp_ratio(stale_memory_count / memory_item_count)


def _unresolved_feedback_score(
    unresolved_feedback_count: Decimal,
    unresolved_feedback_block_count: Decimal,
) -> Decimal:
    if unresolved_feedback_block_count == ZERO:
        return ONE if unresolved_feedback_count > ZERO else ZERO
    return _risk_ratio(unresolved_feedback_count, unresolved_feedback_block_count)


def _risk_ratio(value: Decimal, limit: Decimal) -> Decimal:
    if limit == ZERO:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return _clamp_ratio(value / limit)


def _payload_value(value: object) -> object:
    if is_dataclass(value) and not isinstance(value, type):
        return {field.name: _payload_value(getattr(value, field.name)) for field in fields(value)}
    if type(value) is Decimal:
        if not value.is_finite():
            raise ValueError("public payload Decimal must be finite")
        return str(value)
    if type(value) is datetime:
        return _as_utc("public payload datetime", value).isoformat()
    if type(value) is dict:
        return {key: _payload_value(item) for key, item in value.items()}
    if type(value) is tuple:
        return [_payload_value(item) for item in value]
    if type(value) is list:
        return [_payload_value(item) for item in value]
    if type(value) in (str, bool):
        return value
    raise ValueError("public payload contains unsupported value")


def _reject_unsafe_public_payload(label: str, value: object) -> None:
    if type(value) is dict:
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError(f"{label} contains unsafe public surface")
            _require_safe_public_text(label, key)
            _reject_unsafe_public_payload(label, item)
        return
    if type(value) is list:
        for item in value:
            _reject_unsafe_public_payload(label, item)
        return
    if type(value) is str:
        _require_safe_public_text(label, value)
        return
    if type(value) is bool:
        return
    raise ValueError("public payload contains unsupported value")


def _require_safe_public_text(name: str, value: str) -> None:
    lower = value.lower()
    if any(phrase in lower for phrase in UNSAFE_PUBLIC_TEXT_PHRASES):
        raise ValueError(f"{name} contains unsafe public surface")
    tokens = set(PUBLIC_TOKEN_RE.findall(lower))
    if tokens & UNSAFE_PUBLIC_TEXT_TOKENS:
        raise ValueError(f"{name} contains unsafe public surface")


def _derived_validation_digest(payload: dict[str, Any]) -> str:
    material = {key: value for key, value in payload.items() if key != "derived_validation_digest"}
    _reject_unsafe_public_payload("derived_validation_digest", material)
    return sha256(
        json.dumps(material, sort_keys=True, separators=(",", ":")).encode("utf-8"),
    ).hexdigest()


def _require_matching_digest(payload: dict[str, Any]) -> None:
    if "derived_validation_digest" not in payload:
        raise ValueError("derived_validation_digest is required")
    _require_digest("derived_validation_digest", payload["derived_validation_digest"])
    if payload["derived_validation_digest"] != _derived_validation_digest(payload):
        raise ValueError("derived_validation_digest does not match report payload")


def _row_digest_parts(row: TeamSpecialistMemoryRefreshPriorityRow) -> dict[str, object]:
    return {
        field.name: getattr(row, field.name)
        for field in fields(row)
        if field.name != "derived_validation_digest"
    }


def _require_exact_type(value: object, expected_type: type[object], name: str) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{name} must be exactly {expected_type.__name__}")


def _require_public_string(name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{name} must be a string")
    if not value:
        raise ValueError(f"{name} must be non-empty")
    _require_safe_public_text(name, value)
    return value


def _require_decimal(name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{name} must be finite")
    return _six(value)


def _require_ratio_decimal(name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(name, value)
    if decimal_value < ZERO or decimal_value > ONE:
        raise ValueError(f"{name} must be between 0 and 1")
    return decimal_value


def _require_nonnegative_decimal(name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(name, value)
    if decimal_value < ZERO:
        raise ValueError(f"{name} must be nonnegative")
    return decimal_value


def _require_positive_decimal(name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(name, value)
    if decimal_value <= ZERO:
        raise ValueError(f"{name} must be positive")
    return decimal_value


def _require_nonnegative_count_decimal(name: str, value: object) -> Decimal:
    decimal_value = _require_nonnegative_decimal(name, value)
    if decimal_value != decimal_value.to_integral_value():
        raise ValueError(f"{name} must be a whole count")
    return decimal_value


def _require_positive_count_decimal(name: str, value: object) -> Decimal:
    decimal_value = _require_positive_decimal(name, value)
    if decimal_value != decimal_value.to_integral_value():
        raise ValueError(f"{name} must be a whole count")
    return decimal_value


def _require_decimal_equal(name: str, actual: Decimal, expected: Decimal) -> None:
    if actual != _six(expected):
        raise ValueError(f"{name} must equal derived value")


def _count_decimal(value: int) -> Decimal:
    return Decimal(value).quantize(SIX)


def _six(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(SIX)


def _clamp_ratio(value: Decimal) -> Decimal:
    if value < ZERO:
        return ZERO
    if value > ONE:
        return ONE
    return _six(value)


def _as_utc(name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{name} must be a datetime")
    if value.tzinfo is None or value.tzinfo.utcoffset(value) is None:
        raise ValueError(f"{name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_status(name: str, value: object) -> str:
    if type(value) is not str or value not in MEMORY_REFRESH_STATUSES:
        raise ValueError(f"{name} must be one of {MEMORY_REFRESH_STATUSES}")
    return value


def _require_reason_codes(
    name: str,
    value: object,
    allowed: tuple[str, ...],
) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ValueError(f"{name} must be a tuple")
    if not value:
        raise ValueError(f"{name} must not be empty")
    normalized: list[str] = []
    for item in value:
        if type(item) is not str or item not in allowed:
            raise ValueError(f"{name} contains an unsupported reason code")
        normalized.append(item)
    return tuple(normalized)


def _require_rows(value: object) -> tuple[TeamSpecialistMemoryRefreshPriorityRow, ...]:
    if type(value) is not tuple:
        raise ValueError("rows must be a tuple")
    for item in value:
        if type(item) is not TeamSpecialistMemoryRefreshPriorityRow:
            raise ValueError("rows must contain TeamSpecialistMemoryRefreshPriorityRow values")
        _require_hard_flags("row", item)
        _require_matching_digest(_payload_value(item))
    return value


def _require_digest(name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{name} must be a string")
    if len(value) != 64 or any(char not in "0123456789abcdef" for char in value):
        raise ValueError(f"{name} must be a sha256 hex digest")
    return value


def _require_hard_flags(name: str, value: object) -> None:
    if getattr(value, "paper_only", None) is not True:
        raise ValueError(f"{name} paper_only must be True")
    if getattr(value, "report_only", None) is not True:
        raise ValueError(f"{name} report_only must be True")
    if getattr(value, "readonly", None) is not True:
        raise ValueError(f"{name} readonly must be True")
