"""Report-only backlog builder for research-team memory coverage gaps.

The module is deterministic and side-effect free. It accepts caller-supplied
coverage snapshots and returns a public, sanitized backlog report that can be
written by a local caller without exposing market, evidence, credential, wallet,
order, or trading surfaces.
"""

from __future__ import annotations

import hashlib
import json
import re
from collections import Counter
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import asdict, dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal, ROUND_HALF_UP
from typing import Any


__all__ = (
    "DEFAULT_RESEARCH_TEAM_MEMORY_COVERAGE_GAP_BACKLOG_CONFIG_VERSION",
    "ResearchTeamMemoryCoverageBacklogRow",
    "ResearchTeamMemoryCoverageGapBacklogConfig",
    "ResearchTeamMemoryCoverageGapBacklogReport",
    "ResearchTeamMemoryCoverageReasonCodeCount",
    "ResearchTeamMemoryCoverageSnapshot",
    "build_research_team_memory_coverage_gap_backlog_report",
    "research_team_memory_coverage_gap_backlog_digest",
    "research_team_memory_coverage_gap_backlog_report_payload",
)


DEFAULT_RESEARCH_TEAM_MEMORY_COVERAGE_GAP_BACKLOG_CONFIG_VERSION = (
    "research-team-memory-coverage-gap-backlog-v0"
)

_STATUSES = ("pass", "watch", "block")
_PHASE_FLAG_FIELDS = ("paper_only", "report_only", "readonly")
_PUBLIC_IDENTIFIER_RE = re.compile(r"[a-z][a-z0-9_]{2,63}")
_PUBLIC_LABEL_RE = re.compile(r"[a-z][a-z0-9_-]{2,127}")
_DIGEST_RE = re.compile(r"[0-9a-f]{64}")
_ZERO = Decimal("0")
_ONE = Decimal("1")
_QUANT = Decimal("0.000001")
_SECONDS_PER_DAY = Decimal("86400")

_UNSAFE_PUBLIC_TERMS = (
    "auth",
    "buy",
    "candidate",
    "dsn",
    "market",
    "order",
    "position",
    "question",
    "recommend",
    "ref",
    "sell",
    "slug",
    "source",
    "table",
    "text",
    "token",
    "trade",
    "url",
    "wallet",
)

_REASON_CODE_SEQUENCE = (
    "coverage_complete_pass",
    "coverage_gap_watch",
    "coverage_gap_block",
    "durable_memory_gap_watch",
    "stale_memory_watch",
    "missing_latest_memory_block",
    "empty_memory_scope_block",
    "empty_backlog_input_block",
)


class _FinalPublicDataclass:
    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        for base in cls.__bases__:
            if base is not _FinalPublicDataclass and issubclass(
                base,
                _FinalPublicDataclass,
            ):
                raise TypeError(f"{base.__name__} may not be subclassed")


@dataclass(frozen=True)
class ResearchTeamMemoryCoverageGapBacklogConfig(_FinalPublicDataclass):
    config_version: str = DEFAULT_RESEARCH_TEAM_MEMORY_COVERAGE_GAP_BACKLOG_CONFIG_VERSION
    pass_coverage_ratio: Decimal = Decimal("0.900000")
    watch_coverage_ratio: Decimal = Decimal("0.300000")
    min_durable_memory_count: Decimal = Decimal("1.000000")
    stale_memory_watch_days: Decimal = Decimal("14.000000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchTeamMemoryCoverageGapBacklogConfig, "config")
        _require_public_label("config_version", self.config_version)
        for field_name in ("pass_coverage_ratio", "watch_coverage_ratio"):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        if self.pass_coverage_ratio <= self.watch_coverage_ratio:
            raise ValueError("pass_coverage_ratio must be greater than watch_coverage_ratio")
        for field_name in ("min_durable_memory_count", "stale_memory_watch_days"):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_count_decimal(field_name, getattr(self, field_name)),
            )
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class ResearchTeamMemoryCoverageSnapshot(_FinalPublicDataclass):
    team_key: str
    memory_scope: str
    covered_topic_count: Decimal
    required_topic_count: Decimal
    durable_memory_count: Decimal
    stale_memory_count: Decimal
    latest_memory_at: datetime | None
    reason_codes: tuple[str, ...] = ()
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchTeamMemoryCoverageSnapshot, "snapshot")
        _require_public_identifier("team_key", self.team_key)
        _require_public_identifier("memory_scope", self.memory_scope)
        for field_name in (
            "covered_topic_count",
            "required_topic_count",
            "durable_memory_count",
            "stale_memory_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_count_decimal(field_name, getattr(self, field_name)),
            )
        if self.required_topic_count <= _ZERO:
            raise ValueError("required_topic_count must be positive")
        if self.covered_topic_count > self.required_topic_count:
            raise ValueError("covered_topic_count must not exceed required_topic_count")
        if self.stale_memory_count > self.covered_topic_count:
            raise ValueError("stale_memory_count must not exceed covered_topic_count")
        object.__setattr__(
            self,
            "latest_memory_at",
            _normalize_optional_datetime("latest_memory_at", self.latest_memory_at),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes, allow_empty=True),
        )
        _require_hard_flags("snapshot", self)


@dataclass(frozen=True)
class ResearchTeamMemoryCoverageBacklogRow(_FinalPublicDataclass):
    team_key: str
    memory_scope: str
    coverage_status: str
    covered_topic_count: Decimal
    required_topic_count: Decimal
    coverage_gap_count: Decimal
    durable_memory_count: Decimal
    stale_memory_count: Decimal
    latest_memory_at: datetime | None
    latest_memory_age_days: Decimal | None
    coverage_ratio: Decimal
    coverage_gap_ratio: Decimal
    backlog_priority_score: Decimal
    backlog_action: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchTeamMemoryCoverageBacklogRow, "row")
        _require_public_identifier("team_key", self.team_key)
        _require_public_identifier("memory_scope", self.memory_scope)
        _require_status("coverage_status", self.coverage_status)
        for field_name in (
            "covered_topic_count",
            "required_topic_count",
            "coverage_gap_count",
            "durable_memory_count",
            "stale_memory_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_count_decimal(field_name, getattr(self, field_name)),
            )
        if self.required_topic_count <= _ZERO:
            raise ValueError("required_topic_count must be positive")
        for field_name in (
            "coverage_ratio",
            "coverage_gap_ratio",
            "backlog_priority_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "latest_memory_at",
            _normalize_optional_datetime("latest_memory_at", self.latest_memory_at),
        )
        object.__setattr__(
            self,
            "latest_memory_age_days",
            _normalize_optional_nonnegative_decimal(
                "latest_memory_age_days",
                self.latest_memory_age_days,
            ),
        )
        _require_public_identifier("backlog_action", self.backlog_action)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes, allow_empty=False),
        )
        _validate_row_consistency(self)
        _require_hard_flags("row", self)


@dataclass(frozen=True)
class ResearchTeamMemoryCoverageReasonCodeCount(_FinalPublicDataclass):
    reason_code: str
    count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchTeamMemoryCoverageReasonCodeCount, "count")
        _require_public_identifier("reason_code", self.reason_code)
        if self.reason_code not in _REASON_CODE_SEQUENCE:
            raise ValueError("reason_code must be supported")
        object.__setattr__(
            self,
            "count",
            _require_positive_count_decimal("count", self.count),
        )
        _require_hard_flags("reason_code_count", self)


@dataclass(frozen=True)
class ResearchTeamMemoryCoverageGapBacklogReport(_FinalPublicDataclass):
    generated_at: datetime
    config_version: str
    local_supabase_summary: str
    team_scope_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    durable_gap_count: Decimal
    stale_gap_count: Decimal
    latest_missing_count: Decimal
    mean_backlog_priority_score: Decimal
    max_backlog_priority_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    reason_code_counts: tuple[ResearchTeamMemoryCoverageReasonCodeCount, ...]
    backlog_rows: tuple[ResearchTeamMemoryCoverageBacklogRow, ...]
    public_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchTeamMemoryCoverageGapBacklogReport, "report")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_label("config_version", self.config_version)
        _require_public_identifier("local_supabase_summary", self.local_supabase_summary)
        for field_name in (
            "team_scope_count",
            "pass_count",
            "watch_count",
            "block_count",
            "durable_gap_count",
            "stale_gap_count",
            "latest_missing_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_count_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "mean_backlog_priority_score",
            "max_backlog_priority_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        _require_status("status", self.status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes, allow_empty=False),
        )
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        object.__setattr__(self, "backlog_rows", _normalize_rows(self.backlog_rows))
        _validate_report_consistency(self)
        expected_digest = _report_digest_from_values(_report_values_without_digest(self))
        if self.public_digest:
            _require_sha256_digest("public_digest", self.public_digest)
            if self.public_digest != expected_digest:
                raise ValueError("public_digest must match report")
        else:
            object.__setattr__(self, "public_digest", expected_digest)
        _reject_unsafe_public_payload("report", self)
        _require_hard_flags("report", self)


def build_research_team_memory_coverage_gap_backlog_report(
    snapshots: Iterable[object],
    *,
    config: ResearchTeamMemoryCoverageGapBacklogConfig,
    generated_at: datetime,
) -> ResearchTeamMemoryCoverageGapBacklogReport:
    if type(config) is not ResearchTeamMemoryCoverageGapBacklogConfig:
        raise ValueError("config must be a ResearchTeamMemoryCoverageGapBacklogConfig")
    _require_hard_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    snapshot_items = _normalize_snapshots(snapshots)
    for item in snapshot_items:
        if item.latest_memory_at is not None and item.latest_memory_at > generated_at_utc:
            raise ValueError("latest_memory_at must not be after generated_at")

    rows = tuple(
        sorted(
            (
                _backlog_row_from_snapshot(
                    item,
                    config=config,
                    generated_at=generated_at_utc,
                )
                for item in snapshot_items
            ),
            key=lambda row: (row.team_key, row.memory_scope),
        ),
    )
    reason_codes = _report_reason_codes(rows)
    return ResearchTeamMemoryCoverageGapBacklogReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        local_supabase_summary="local_supabase_ready_public_digest_only",
        team_scope_count=_decimal_count(len(rows)),
        pass_count=_status_count(rows, "pass"),
        watch_count=_status_count(rows, "watch"),
        block_count=_status_count(rows, "block"),
        durable_gap_count=_decimal_count(
            sum(1 for row in rows if "durable_memory_gap_watch" in row.reason_codes),
        ),
        stale_gap_count=_decimal_count(
            sum(1 for row in rows if "stale_memory_watch" in row.reason_codes),
        ),
        latest_missing_count=_decimal_count(
            sum(1 for row in rows if "missing_latest_memory_block" in row.reason_codes),
        ),
        mean_backlog_priority_score=_average(
            tuple(row.backlog_priority_score for row in rows),
        ),
        max_backlog_priority_score=max(
            (row.backlog_priority_score for row in rows),
            default=_ZERO,
        ),
        status=_report_status(rows),
        reason_codes=reason_codes,
        reason_code_counts=_reason_code_counts(rows, reason_codes),
        backlog_rows=rows,
    )


def research_team_memory_coverage_gap_backlog_digest(
    report: ResearchTeamMemoryCoverageGapBacklogReport,
) -> str:
    if type(report) is not ResearchTeamMemoryCoverageGapBacklogReport:
        raise ValueError("report must be a ResearchTeamMemoryCoverageGapBacklogReport")
    _require_hard_flags("report", report)
    return report.public_digest


def research_team_memory_coverage_gap_backlog_report_payload(
    report: ResearchTeamMemoryCoverageGapBacklogReport,
) -> dict[str, Any]:
    if type(report) is not ResearchTeamMemoryCoverageGapBacklogReport:
        raise ValueError("report must be a ResearchTeamMemoryCoverageGapBacklogReport")
    _require_hard_flags("report", report)
    payload = _json_ready(report)
    _reject_unsafe_public_payload(
        "report_payload",
        payload,
        allow_json_containers=True,
    )
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    return payload


def _backlog_row_from_snapshot(
    snapshot: ResearchTeamMemoryCoverageSnapshot,
    *,
    config: ResearchTeamMemoryCoverageGapBacklogConfig,
    generated_at: datetime,
) -> ResearchTeamMemoryCoverageBacklogRow:
    coverage_ratio = _ratio(snapshot.covered_topic_count, snapshot.required_topic_count)
    coverage_gap_count = _quantize(
        snapshot.required_topic_count - snapshot.covered_topic_count,
    )
    coverage_gap_ratio = _ratio(coverage_gap_count, snapshot.required_topic_count)
    latest_memory_age_days = (
        None
        if snapshot.latest_memory_at is None
        else _age_days(generated_at, snapshot.latest_memory_at)
    )
    reason_codes = _row_reason_codes(
        coverage_ratio=coverage_ratio,
        durable_memory_count=snapshot.durable_memory_count,
        stale_memory_count=snapshot.stale_memory_count,
        latest_memory_age_days=latest_memory_age_days,
        input_reason_codes=snapshot.reason_codes,
        config=config,
    )
    return ResearchTeamMemoryCoverageBacklogRow(
        team_key=snapshot.team_key,
        memory_scope=snapshot.memory_scope,
        coverage_status=_row_status(reason_codes),
        covered_topic_count=snapshot.covered_topic_count,
        required_topic_count=snapshot.required_topic_count,
        coverage_gap_count=coverage_gap_count,
        durable_memory_count=snapshot.durable_memory_count,
        stale_memory_count=snapshot.stale_memory_count,
        latest_memory_at=snapshot.latest_memory_at,
        latest_memory_age_days=latest_memory_age_days,
        coverage_ratio=coverage_ratio,
        coverage_gap_ratio=coverage_gap_ratio,
        backlog_priority_score=_priority_score(
            coverage_gap_ratio=coverage_gap_ratio,
            durable_memory_count=snapshot.durable_memory_count,
            latest_memory_age_days=latest_memory_age_days,
            config=config,
        ),
        backlog_action=_backlog_action(reason_codes),
        reason_codes=reason_codes,
    )


def _row_reason_codes(
    *,
    coverage_ratio: Decimal,
    durable_memory_count: Decimal,
    stale_memory_count: Decimal,
    latest_memory_age_days: Decimal | None,
    input_reason_codes: tuple[str, ...],
    config: ResearchTeamMemoryCoverageGapBacklogConfig,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    if coverage_ratio < config.watch_coverage_ratio:
        reason_codes.append("coverage_gap_block")
    elif coverage_ratio < config.pass_coverage_ratio:
        reason_codes.append("coverage_gap_watch")
    else:
        reason_codes.append("coverage_complete_pass")
    if durable_memory_count < config.min_durable_memory_count:
        reason_codes.append("durable_memory_gap_watch")
    if stale_memory_count > _ZERO:
        reason_codes.append("stale_memory_watch")
    if latest_memory_age_days is None:
        reason_codes.append("missing_latest_memory_block")
    elif latest_memory_age_days >= config.stale_memory_watch_days:
        reason_codes.append("stale_memory_watch")
    reason_codes.extend(input_reason_codes)
    return _normalize_reason_codes(tuple(reason_codes), allow_empty=False)


def _row_status(reason_codes: tuple[str, ...]) -> str:
    if any(code.endswith("_block") for code in reason_codes):
        return "block"
    if any(code.endswith("_watch") for code in reason_codes):
        return "watch"
    return "pass"


def _backlog_action(reason_codes: tuple[str, ...]) -> str:
    status = _row_status(reason_codes)
    if status == "block":
        return "fill_gap"
    if status == "watch":
        return "update_gap"
    return "monitor_gap"


def _priority_score(
    *,
    coverage_gap_ratio: Decimal,
    durable_memory_count: Decimal,
    latest_memory_age_days: Decimal | None,
    config: ResearchTeamMemoryCoverageGapBacklogConfig,
) -> Decimal:
    durable_penalty = (
        _ZERO
        if durable_memory_count >= config.min_durable_memory_count
        else Decimal("0.250000")
    )
    age_penalty = (
        Decimal("0.250000")
        if latest_memory_age_days is None
        else min(
            _ratio(latest_memory_age_days, config.stale_memory_watch_days),
            Decimal("0.250000"),
        )
    )
    return _clamp_ratio(coverage_gap_ratio + durable_penalty + age_penalty)


def _report_status(rows: tuple[ResearchTeamMemoryCoverageBacklogRow, ...]) -> str:
    if not rows:
        return "block"
    if any(row.coverage_status == "block" for row in rows):
        return "block"
    if any(row.coverage_status == "watch" for row in rows):
        return "watch"
    return "pass"


def _report_reason_codes(
    rows: tuple[ResearchTeamMemoryCoverageBacklogRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return ("empty_backlog_input_block",)
    return _normalize_reason_codes(
        tuple(reason_code for row in rows for reason_code in row.reason_codes),
        allow_empty=False,
    )


def _reason_code_counts(
    rows: tuple[ResearchTeamMemoryCoverageBacklogRow, ...],
    reason_codes: tuple[str, ...],
) -> tuple[ResearchTeamMemoryCoverageReasonCodeCount, ...]:
    if not rows:
        return (
            ResearchTeamMemoryCoverageReasonCodeCount(
                reason_code="empty_backlog_input_block",
                count=_ONE.quantize(_QUANT),
            ),
        )
    counts = Counter(reason_code for row in rows for reason_code in row.reason_codes)
    return tuple(
        ResearchTeamMemoryCoverageReasonCodeCount(
            reason_code=reason_code,
            count=_decimal_count(counts[reason_code]),
        )
        for reason_code in reason_codes
    )


def _normalize_snapshots(
    snapshots: Iterable[object],
) -> tuple[ResearchTeamMemoryCoverageSnapshot, ...]:
    if isinstance(snapshots, (str, bytes)):
        raise ValueError("snapshots must be an iterable")
    try:
        values = tuple(snapshots)
    except TypeError as exc:
        raise ValueError("snapshots must be an iterable") from exc
    normalized: list[ResearchTeamMemoryCoverageSnapshot] = []
    seen: set[tuple[str, str]] = set()
    for value in values:
        if type(value) is not ResearchTeamMemoryCoverageSnapshot:
            raise ValueError("snapshots must contain ResearchTeamMemoryCoverageSnapshot")
        key = (value.team_key, value.memory_scope)
        if key in seen:
            raise ValueError("duplicate team_key and memory_scope")
        seen.add(key)
        normalized.append(value)
    return tuple(sorted(normalized, key=lambda item: (item.team_key, item.memory_scope)))


def _normalize_rows(
    rows: Sequence[ResearchTeamMemoryCoverageBacklogRow],
) -> tuple[ResearchTeamMemoryCoverageBacklogRow, ...]:
    if isinstance(rows, (str, bytes)) or not isinstance(rows, Sequence):
        raise ValueError("backlog_rows must be a sequence")
    normalized: list[ResearchTeamMemoryCoverageBacklogRow] = []
    seen: set[tuple[str, str]] = set()
    for row in rows:
        if type(row) is not ResearchTeamMemoryCoverageBacklogRow:
            raise ValueError("backlog_rows must contain ResearchTeamMemoryCoverageBacklogRow")
        key = (row.team_key, row.memory_scope)
        if key in seen:
            raise ValueError("duplicate team_key and memory_scope")
        seen.add(key)
        normalized.append(row)
    return tuple(sorted(normalized, key=lambda row: (row.team_key, row.memory_scope)))


def _normalize_reason_code_counts(
    counts: Sequence[ResearchTeamMemoryCoverageReasonCodeCount],
) -> tuple[ResearchTeamMemoryCoverageReasonCodeCount, ...]:
    if isinstance(counts, (str, bytes)) or not isinstance(counts, Sequence):
        raise ValueError("reason_code_counts must be a sequence")
    normalized: list[ResearchTeamMemoryCoverageReasonCodeCount] = []
    seen: set[str] = set()
    for count in counts:
        if type(count) is not ResearchTeamMemoryCoverageReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain ResearchTeamMemoryCoverageReasonCodeCount",
            )
        if count.reason_code in seen:
            raise ValueError("duplicate reason_code")
        seen.add(count.reason_code)
        normalized.append(count)
    return tuple(
        sorted(
            normalized,
            key=lambda item: _REASON_CODE_SEQUENCE.index(item.reason_code),
        ),
    )


def _normalize_reason_codes(
    reason_codes: Sequence[str],
    *,
    allow_empty: bool,
) -> tuple[str, ...]:
    if isinstance(reason_codes, (str, bytes)) or not isinstance(reason_codes, Sequence):
        raise ValueError("reason_codes must be a sequence")
    normalized: list[str] = []
    for reason_code in reason_codes:
        _require_public_identifier("reason_code", reason_code)
        if reason_code not in _REASON_CODE_SEQUENCE:
            raise ValueError("reason_code must be supported")
        if reason_code not in normalized:
            normalized.append(reason_code)
    if not normalized and not allow_empty:
        raise ValueError("reason_codes must not be empty")
    return tuple(code for code in _REASON_CODE_SEQUENCE if code in normalized)


def _validate_row_consistency(row: ResearchTeamMemoryCoverageBacklogRow) -> None:
    if row.coverage_gap_count != _quantize(
        row.required_topic_count - row.covered_topic_count,
    ):
        raise ValueError("coverage_gap_count must match required less covered")
    if row.coverage_ratio != _ratio(row.covered_topic_count, row.required_topic_count):
        raise ValueError("coverage_ratio must match covered over required")
    if row.coverage_gap_ratio != _ratio(row.coverage_gap_count, row.required_topic_count):
        raise ValueError("coverage_gap_ratio must match gap over required")
    if row.coverage_status != _row_status(row.reason_codes):
        raise ValueError("coverage_status must match reason_codes")
    if row.backlog_action != _backlog_action(row.reason_codes):
        raise ValueError("backlog_action must match reason_codes")


def _validate_report_consistency(
    report: ResearchTeamMemoryCoverageGapBacklogReport,
) -> None:
    rows = report.backlog_rows
    if report.team_scope_count != _decimal_count(len(rows)):
        raise ValueError("team_scope_count must match rows")
    for status, field_name in (
        ("pass", "pass_count"),
        ("watch", "watch_count"),
        ("block", "block_count"),
    ):
        if getattr(report, field_name) != _status_count(rows, status):
            raise ValueError(f"{field_name} must match rows")
    if report.durable_gap_count != _decimal_count(
        sum(1 for row in rows if "durable_memory_gap_watch" in row.reason_codes),
    ):
        raise ValueError("durable_gap_count must match rows")
    if report.stale_gap_count != _decimal_count(
        sum(1 for row in rows if "stale_memory_watch" in row.reason_codes),
    ):
        raise ValueError("stale_gap_count must match rows")
    if report.latest_missing_count != _decimal_count(
        sum(1 for row in rows if "missing_latest_memory_block" in row.reason_codes),
    ):
        raise ValueError("latest_missing_count must match rows")
    if report.mean_backlog_priority_score != _average(
        tuple(row.backlog_priority_score for row in rows),
    ):
        raise ValueError("mean_backlog_priority_score must match rows")
    if report.max_backlog_priority_score != max(
        (row.backlog_priority_score for row in rows),
        default=_ZERO,
    ):
        raise ValueError("max_backlog_priority_score must match rows")
    if report.status != _report_status(rows):
        raise ValueError("status must match rows")
    if report.reason_codes != _report_reason_codes(rows):
        raise ValueError("reason_codes must match rows")
    expected_counts = _reason_code_counts(rows, report.reason_codes)
    if report.reason_code_counts != expected_counts:
        raise ValueError("reason_code_counts must match rows")


def _require_exact_type(value: object, expected_type: type[object], label: str) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{label} must be exactly {expected_type.__name__}")


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


def _require_public_label(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not _PUBLIC_LABEL_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a public label")
    _reject_unsafe_public_string(field_name, value)
    return value


def _require_status(field_name: str, value: object) -> str:
    if type(value) is not str or value not in _STATUSES:
        raise ValueError(f"{field_name} must be pass, watch, or block")
    return value


def _require_sha256_digest(field_name: str, value: object) -> str:
    if type(value) is not str or not _DIGEST_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a lowercase sha256 digest")
    return value


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return _quantize(value)


def _require_nonnegative_count_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < _ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _require_positive_count_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_nonnegative_count_decimal(field_name, value)
    if normalized <= _ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _require_ratio_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < _ZERO or normalized > _ONE:
        raise ValueError(f"{field_name} must be between zero and one")
    return normalized


def _normalize_optional_nonnegative_decimal(
    field_name: str,
    value: object,
) -> Decimal | None:
    if value is None:
        return None
    return _require_nonnegative_count_decimal(field_name, value)


def _normalize_optional_datetime(field_name: str, value: object) -> datetime | None:
    if value is None:
        return None
    return _as_utc(field_name, value)


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _decimal_count(value: int) -> Decimal:
    if value < 0:
        raise ValueError("count must be nonnegative")
    return Decimal(value).quantize(_QUANT)


def _quantize(value: Decimal) -> Decimal:
    return value.quantize(_QUANT, rounding=ROUND_HALF_UP)


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator <= _ZERO:
        raise ValueError("ratio denominator must be positive")
    return _quantize(numerator / denominator)


def _average(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return _ZERO.quantize(_QUANT)
    return _quantize(sum(values, _ZERO) / Decimal(len(values)))


def _clamp_ratio(value: Decimal) -> Decimal:
    normalized = _quantize(value)
    if normalized < _ZERO:
        return _ZERO.quantize(_QUANT)
    if normalized > _ONE:
        return _ONE.quantize(_QUANT)
    return normalized


def _age_days(generated_at: datetime, observed_at: datetime) -> Decimal:
    delta = generated_at - observed_at
    if delta.total_seconds() < 0:
        raise ValueError("observed datetime must not be after generated_at")
    seconds = (
        Decimal(delta.days * 86400)
        + Decimal(delta.seconds)
        + (Decimal(delta.microseconds) / Decimal("1000000"))
    )
    return _quantize(seconds / _SECONDS_PER_DAY)


def _status_count(
    rows: tuple[ResearchTeamMemoryCoverageBacklogRow, ...],
    status: str,
) -> Decimal:
    return _decimal_count(sum(1 for row in rows if row.coverage_status == status))


def _report_values_without_digest(
    report: ResearchTeamMemoryCoverageGapBacklogReport,
) -> dict[str, object]:
    values = asdict(report)
    values.pop("public_digest", None)
    return values


def _report_digest_from_values(values: Mapping[str, object]) -> str:
    payload = _json_ready(values)
    _reject_unsafe_public_payload(
        "public_digest_payload",
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


def _reject_unsafe_public_string(field_name: str, value: str) -> None:
    lowered = value.lower()
    if "://" in lowered or "?" in lowered or "@" in lowered:
        raise ValueError(f"{field_name} has unsafe public value")
    if any(term in lowered for term in _UNSAFE_PUBLIC_TERMS):
        raise ValueError(f"{field_name} has unsafe public value")
