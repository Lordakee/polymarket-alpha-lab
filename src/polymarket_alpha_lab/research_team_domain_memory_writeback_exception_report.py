"""Pure report-only domain memory writeback exception aggregation."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import asdict, dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, localcontext
import hashlib
import json
import re
from typing import Any


DEFAULT_RESEARCH_TEAM_DOMAIN_MEMORY_WRITEBACK_EXCEPTION_REPORT_CONFIG_VERSION = (
    "research-team-domain-memory-writeback-exception-report-v0"
)

_DECIMAL_CONTEXT = Context(prec=64)
_QUANTUM = Decimal("0.000001")
_ZERO = Decimal("0.000000")
_ONE = Decimal("1.000000")
_STATUSES = ("pass", "watch", "block")
_STATUS_WEIGHT = {"block": 0, "watch": 1, "pass": 2}
_PUBLIC_IDENTIFIER_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,127}$")
_DIGEST_RE = re.compile(r"^[0-9a-f]{64}$")
_REASON_CODE_ORDER = (
    "missing_writeback",
    "stale_writeback_age",
    "unresolved_outcome_link",
    "calibration_feedback_backlog",
    "manual_review_urgency",
)
_EMPTY_REASON = "no_domain_memory_writeback_exceptions_detected"
_BOUNDARY_STATEMENT = (
    "Phase 1 pure in-memory paper-only report-only readonly domain memory "
    "writeback exception report."
)
_UNSAFE_PUBLIC_FIELD_FRAGMENTS = (
    "candidate_id",
    "market_id",
    "market_slug",
    "question",
    "source_url",
    "source_text",
    "dsn",
    "table",
    "token",
    "auth",
    "wallet",
    "order",
    "live",
    "trade",
    "sizing",
    "recommendation",
)
_UNSAFE_PUBLIC_VALUE_FRAGMENTS = (
    "candidate:",
    "market:",
    "question:",
    "source_url",
    "source_text",
    "http://",
    "https://",
    "postgres://",
    "postgresql://",
    "dsn=",
    "token=",
    "private_key",
)


@dataclass(frozen=True)
class ResearchTeamDomainMemoryWritebackExceptionReportConfig:
    config_version: str = (
        DEFAULT_RESEARCH_TEAM_DOMAIN_MEMORY_WRITEBACK_EXCEPTION_REPORT_CONFIG_VERSION
    )
    stale_writeback_watch_after_seconds: Decimal = Decimal("86400.000000")
    stale_writeback_block_after_seconds: Decimal = Decimal("172800.000000")
    calibration_feedback_watch_threshold: Decimal = Decimal("1")
    calibration_feedback_block_threshold: Decimal = Decimal("3")
    manual_review_watch_urgency: Decimal = Decimal("0.500000")
    manual_review_block_urgency: Decimal = Decimal("0.800000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchTeamDomainMemoryWritebackExceptionReportConfig:
            raise TypeError(
                "ResearchTeamDomainMemoryWritebackExceptionReportConfig does not "
                "support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchTeamDomainMemoryWritebackExceptionReportConfig:
            raise ValueError("config must be exactly the supported config dataclass")
        _require_public_identifier("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_TEAM_DOMAIN_MEMORY_WRITEBACK_EXCEPTION_REPORT_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "stale_writeback_watch_after_seconds",
            "stale_writeback_block_after_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_positive_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "calibration_feedback_watch_threshold",
            "calibration_feedback_block_threshold",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_positive_count_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in ("manual_review_watch_urgency", "manual_review_block_urgency"):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        if self.stale_writeback_block_after_seconds <= self.stale_writeback_watch_after_seconds:
            raise ValueError(
                "stale_writeback_block_after_seconds must exceed "
                "stale_writeback_watch_after_seconds",
            )
        if (
            self.calibration_feedback_block_threshold
            < self.calibration_feedback_watch_threshold
        ):
            raise ValueError(
                "calibration_feedback_block_threshold must be at least "
                "calibration_feedback_watch_threshold",
            )
        if self.manual_review_block_urgency <= self.manual_review_watch_urgency:
            raise ValueError(
                "manual_review_block_urgency must exceed manual_review_watch_urgency",
            )
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class ResearchTeamDomainMemoryWritebackSnapshot:
    team_id: str
    domain_id: str
    case_key: str
    observed_at: datetime
    writeback_at: datetime | None
    outcome_link_resolved: bool
    calibration_feedback_backlog_count: Decimal
    manual_review_urgency: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchTeamDomainMemoryWritebackSnapshot:
            raise TypeError(
                "ResearchTeamDomainMemoryWritebackSnapshot does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchTeamDomainMemoryWritebackSnapshot:
            raise ValueError("snapshot must be exactly ResearchTeamDomainMemoryWritebackSnapshot")
        _require_public_identifier("team_id", self.team_id)
        _require_public_identifier("domain_id", self.domain_id)
        _require_nonempty_string("case_key", self.case_key)
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        object.__setattr__(
            self,
            "writeback_at",
            _as_optional_utc("writeback_at", self.writeback_at),
        )
        if self.writeback_at is not None and self.writeback_at < self.observed_at:
            raise ValueError("writeback_at must not be before observed_at")
        _require_bool("outcome_link_resolved", self.outcome_link_resolved)
        object.__setattr__(
            self,
            "calibration_feedback_backlog_count",
            _require_nonnegative_count_decimal(
                "calibration_feedback_backlog_count",
                self.calibration_feedback_backlog_count,
            ),
        )
        object.__setattr__(
            self,
            "manual_review_urgency",
            _require_ratio_decimal("manual_review_urgency", self.manual_review_urgency),
        )
        _require_hard_flags("snapshot", self)


@dataclass(frozen=True)
class ResearchTeamDomainMemoryWritebackExceptionRow:
    team_id: str
    domain_id: str
    memory_case_ref: str
    status: str
    observed_at: datetime
    writeback_at: datetime | None
    writeback_age_seconds: Decimal
    missing_writeback: bool
    stale_writeback_age: bool
    unresolved_outcome_link: bool
    calibration_feedback_backlog_count: Decimal
    manual_review_urgency: Decimal
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchTeamDomainMemoryWritebackExceptionRow:
            raise TypeError(
                "ResearchTeamDomainMemoryWritebackExceptionRow does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchTeamDomainMemoryWritebackExceptionRow:
            raise ValueError("row must be exactly ResearchTeamDomainMemoryWritebackExceptionRow")
        _require_public_identifier("team_id", self.team_id)
        _require_public_identifier("domain_id", self.domain_id)
        _require_memory_case_ref(self.memory_case_ref)
        _require_status("status", self.status)
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        object.__setattr__(
            self,
            "writeback_at",
            _as_optional_utc("writeback_at", self.writeback_at),
        )
        object.__setattr__(
            self,
            "writeback_age_seconds",
            _require_nonnegative_decimal("writeback_age_seconds", self.writeback_age_seconds),
        )
        for field_name in (
            "missing_writeback",
            "stale_writeback_age",
            "unresolved_outcome_link",
        ):
            _require_bool(field_name, getattr(self, field_name))
        object.__setattr__(
            self,
            "calibration_feedback_backlog_count",
            _require_nonnegative_count_decimal(
                "calibration_feedback_backlog_count",
                self.calibration_feedback_backlog_count,
            ),
        )
        object.__setattr__(
            self,
            "manual_review_urgency",
            _require_ratio_decimal("manual_review_urgency", self.manual_review_urgency),
        )
        object.__setattr__(self, "reason_codes", _normalize_reason_codes(self.reason_codes))
        _validate_row_consistency(self)
        _require_hard_flags("row", self)
        _reject_unsafe_public_payload("row", self)


@dataclass(frozen=True)
class ResearchTeamDomainMemoryWritebackTeamDomainRollup:
    team_id: str
    domain_id: str
    status: str
    row_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    missing_writeback_count: Decimal
    stale_writeback_count: Decimal
    unresolved_outcome_link_count: Decimal
    calibration_feedback_backlog_count: Decimal
    manual_review_urgent_count: Decimal
    max_writeback_age_seconds: Decimal
    max_manual_review_urgency: Decimal
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchTeamDomainMemoryWritebackTeamDomainRollup:
            raise TypeError(
                "ResearchTeamDomainMemoryWritebackTeamDomainRollup does not support "
                "subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchTeamDomainMemoryWritebackTeamDomainRollup:
            raise ValueError("rollup must be exactly the supported rollup dataclass")
        _require_public_identifier("team_id", self.team_id)
        _require_public_identifier("domain_id", self.domain_id)
        _require_status("status", self.status)
        for field_name in (
            "row_count",
            "pass_count",
            "watch_count",
            "block_count",
            "missing_writeback_count",
            "stale_writeback_count",
            "unresolved_outcome_link_count",
            "calibration_feedback_backlog_count",
            "manual_review_urgent_count",
            "max_writeback_age_seconds",
            "max_manual_review_urgency",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(self, "reason_codes", _normalize_reason_codes(self.reason_codes))
        _validate_rollup_consistency(self)
        _require_hard_flags("rollup", self)
        _reject_unsafe_public_payload("rollup", self)


@dataclass(frozen=True)
class ResearchTeamDomainMemoryWritebackExceptionReport:
    generated_at: datetime
    config_version: str
    status: str
    input_count: Decimal
    row_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    missing_writeback_count: Decimal
    stale_writeback_count: Decimal
    unresolved_outcome_link_count: Decimal
    calibration_feedback_backlog_count: Decimal
    manual_review_urgent_count: Decimal
    team_domain_rollup_count: Decimal
    max_writeback_age_seconds: Decimal
    max_manual_review_urgency: Decimal
    reason_codes: tuple[str, ...]
    rows: tuple[ResearchTeamDomainMemoryWritebackExceptionRow, ...]
    team_domain_rollups: tuple[ResearchTeamDomainMemoryWritebackTeamDomainRollup, ...]
    derived_validation_digest: str
    boundary_statement: str = _BOUNDARY_STATEMENT
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchTeamDomainMemoryWritebackExceptionReport:
            raise TypeError(
                "ResearchTeamDomainMemoryWritebackExceptionReport does not support "
                "subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchTeamDomainMemoryWritebackExceptionReport:
            raise ValueError("report must be exactly the supported report dataclass")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_identifier("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_TEAM_DOMAIN_MEMORY_WRITEBACK_EXCEPTION_REPORT_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        _require_status("status", self.status)
        for field_name in (
            "input_count",
            "row_count",
            "pass_count",
            "watch_count",
            "block_count",
            "missing_writeback_count",
            "stale_writeback_count",
            "unresolved_outcome_link_count",
            "calibration_feedback_backlog_count",
            "manual_review_urgent_count",
            "team_domain_rollup_count",
            "max_writeback_age_seconds",
            "max_manual_review_urgency",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(self, "reason_codes", _normalize_reason_codes(self.reason_codes))
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        object.__setattr__(
            self,
            "team_domain_rollups",
            _normalize_rollups(self.team_domain_rollups),
        )
        _require_sha256_digest("derived_validation_digest", self.derived_validation_digest)
        if self.boundary_statement != _BOUNDARY_STATEMENT:
            raise ValueError("boundary_statement must match report-only scope")
        _validate_report_consistency(self)
        _require_hard_flags("report", self)
        _reject_unsafe_public_payload("report", self)
        expected_digest = _report_digest_from_values(_report_values_without_digest(self))
        if self.derived_validation_digest != expected_digest:
            raise ValueError("derived_validation_digest does not match report payload")

    @property
    def payload(self) -> dict[str, object]:
        payload = _json_ready(asdict(self))
        _reject_unsafe_public_payload("payload", payload, allow_json_containers=True)
        if type(payload) is not dict:
            raise ValueError("payload must be a dict")
        return payload


def build_research_team_domain_memory_writeback_exception_report(
    snapshots: Sequence[ResearchTeamDomainMemoryWritebackSnapshot],
    *,
    generated_at: datetime,
    config: ResearchTeamDomainMemoryWritebackExceptionReportConfig | None = None,
) -> ResearchTeamDomainMemoryWritebackExceptionReport:
    """Build a deterministic local report-only domain memory writeback snapshot."""

    if config is None:
        config = ResearchTeamDomainMemoryWritebackExceptionReportConfig()
    if type(config) is not ResearchTeamDomainMemoryWritebackExceptionReportConfig:
        raise ValueError(
            "config must be a ResearchTeamDomainMemoryWritebackExceptionReportConfig",
        )
    _require_hard_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    normalized_snapshots = _normalize_snapshots(snapshots, generated_at=generated_at_utc)
    rows = tuple(
        sorted(
            (
                _row_from_snapshot(
                    snapshot,
                    generated_at=generated_at_utc,
                    config=config,
                )
                for snapshot in normalized_snapshots
            ),
            key=_row_sort_key,
        )
    )
    rollups = _team_domain_rollups(rows)
    values: dict[str, object] = {
        "generated_at": generated_at_utc,
        "config_version": config.config_version,
        "status": _aggregate_status(rows),
        "input_count": _decimal_count(len(normalized_snapshots)),
        "row_count": _decimal_count(len(rows)),
        "pass_count": _status_count(rows, "pass"),
        "watch_count": _status_count(rows, "watch"),
        "block_count": _status_count(rows, "block"),
        "missing_writeback_count": _reason_count(rows, "missing_writeback"),
        "stale_writeback_count": _reason_count(rows, "stale_writeback_age"),
        "unresolved_outcome_link_count": _reason_count(rows, "unresolved_outcome_link"),
        "calibration_feedback_backlog_count": _reason_count(
            rows,
            "calibration_feedback_backlog",
        ),
        "manual_review_urgent_count": _reason_count(rows, "manual_review_urgency"),
        "team_domain_rollup_count": _decimal_count(len(rollups)),
        "max_writeback_age_seconds": _max_row_decimal(rows, "writeback_age_seconds"),
        "max_manual_review_urgency": _max_row_decimal(rows, "manual_review_urgency"),
        "reason_codes": _report_reason_codes(rows),
        "rows": rows,
        "team_domain_rollups": rollups,
        "boundary_statement": _BOUNDARY_STATEMENT,
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    return ResearchTeamDomainMemoryWritebackExceptionReport(
        **values,
        derived_validation_digest=_report_digest_from_values(values),
    )


def _row_from_snapshot(
    snapshot: ResearchTeamDomainMemoryWritebackSnapshot,
    *,
    generated_at: datetime,
    config: ResearchTeamDomainMemoryWritebackExceptionReportConfig,
) -> ResearchTeamDomainMemoryWritebackExceptionRow:
    missing_writeback = snapshot.writeback_at is None
    writeback_age_seconds = (
        _ZERO
        if snapshot.writeback_at is None
        else _seconds_between(generated_at, snapshot.writeback_at, "writeback_at")
    )
    stale_writeback_age = (
        snapshot.writeback_at is not None
        and writeback_age_seconds >= config.stale_writeback_watch_after_seconds
    )
    reason_codes = _row_reason_codes(
        missing_writeback=missing_writeback,
        stale_writeback_age=stale_writeback_age,
        outcome_link_resolved=snapshot.outcome_link_resolved,
        calibration_feedback_backlog_count=snapshot.calibration_feedback_backlog_count,
        manual_review_urgency=snapshot.manual_review_urgency,
        config=config,
    )
    return ResearchTeamDomainMemoryWritebackExceptionRow(
        team_id=snapshot.team_id,
        domain_id=snapshot.domain_id,
        memory_case_ref=_memory_case_ref(snapshot.case_key),
        status=_row_status(
            missing_writeback=missing_writeback,
            outcome_link_resolved=snapshot.outcome_link_resolved,
            writeback_age_seconds=writeback_age_seconds,
            calibration_feedback_backlog_count=snapshot.calibration_feedback_backlog_count,
            manual_review_urgency=snapshot.manual_review_urgency,
            config=config,
        ),
        observed_at=snapshot.observed_at,
        writeback_at=snapshot.writeback_at,
        writeback_age_seconds=writeback_age_seconds,
        missing_writeback=missing_writeback,
        stale_writeback_age=stale_writeback_age,
        unresolved_outcome_link=not snapshot.outcome_link_resolved,
        calibration_feedback_backlog_count=snapshot.calibration_feedback_backlog_count,
        manual_review_urgency=snapshot.manual_review_urgency,
        reason_codes=reason_codes,
    )


def _row_reason_codes(
    *,
    missing_writeback: bool,
    stale_writeback_age: bool,
    outcome_link_resolved: bool,
    calibration_feedback_backlog_count: Decimal,
    manual_review_urgency: Decimal,
    config: ResearchTeamDomainMemoryWritebackExceptionReportConfig,
) -> tuple[str, ...]:
    present: set[str] = set()
    if missing_writeback:
        present.add("missing_writeback")
    if stale_writeback_age:
        present.add("stale_writeback_age")
    if not outcome_link_resolved:
        present.add("unresolved_outcome_link")
    if calibration_feedback_backlog_count >= config.calibration_feedback_watch_threshold:
        present.add("calibration_feedback_backlog")
    if manual_review_urgency >= config.manual_review_watch_urgency:
        present.add("manual_review_urgency")
    return tuple(code for code in _REASON_CODE_ORDER if code in present)


def _row_status(
    *,
    missing_writeback: bool,
    outcome_link_resolved: bool,
    writeback_age_seconds: Decimal,
    calibration_feedback_backlog_count: Decimal,
    manual_review_urgency: Decimal,
    config: ResearchTeamDomainMemoryWritebackExceptionReportConfig,
) -> str:
    if (
        missing_writeback
        or not outcome_link_resolved
        or writeback_age_seconds >= config.stale_writeback_block_after_seconds
        or calibration_feedback_backlog_count >= config.calibration_feedback_block_threshold
        or manual_review_urgency >= config.manual_review_block_urgency
    ):
        return "block"
    if (
        writeback_age_seconds >= config.stale_writeback_watch_after_seconds
        or calibration_feedback_backlog_count >= config.calibration_feedback_watch_threshold
        or manual_review_urgency >= config.manual_review_watch_urgency
    ):
        return "watch"
    return "pass"


def _team_domain_rollups(
    rows: tuple[ResearchTeamDomainMemoryWritebackExceptionRow, ...],
) -> tuple[ResearchTeamDomainMemoryWritebackTeamDomainRollup, ...]:
    groups: dict[tuple[str, str], list[ResearchTeamDomainMemoryWritebackExceptionRow]] = {}
    for row in rows:
        groups.setdefault((row.team_id, row.domain_id), []).append(row)
    rollups = []
    for (team_id, domain_id), group_rows in sorted(groups.items()):
        scoped_rows = tuple(sorted(group_rows, key=_row_sort_key))
        rollups.append(
            ResearchTeamDomainMemoryWritebackTeamDomainRollup(
                team_id=team_id,
                domain_id=domain_id,
                status=_aggregate_status(scoped_rows),
                row_count=_decimal_count(len(scoped_rows)),
                pass_count=_status_count(scoped_rows, "pass"),
                watch_count=_status_count(scoped_rows, "watch"),
                block_count=_status_count(scoped_rows, "block"),
                missing_writeback_count=_reason_count(scoped_rows, "missing_writeback"),
                stale_writeback_count=_reason_count(scoped_rows, "stale_writeback_age"),
                unresolved_outcome_link_count=_reason_count(
                    scoped_rows,
                    "unresolved_outcome_link",
                ),
                calibration_feedback_backlog_count=_reason_count(
                    scoped_rows,
                    "calibration_feedback_backlog",
                ),
                manual_review_urgent_count=_reason_count(
                    scoped_rows,
                    "manual_review_urgency",
                ),
                max_writeback_age_seconds=_max_row_decimal(
                    scoped_rows,
                    "writeback_age_seconds",
                ),
                max_manual_review_urgency=_max_row_decimal(scoped_rows, "manual_review_urgency"),
                reason_codes=_report_reason_codes(scoped_rows),
            )
        )
    return tuple(sorted(rollups, key=_rollup_sort_key))


def _normalize_snapshots(
    snapshots: Sequence[ResearchTeamDomainMemoryWritebackSnapshot],
    *,
    generated_at: datetime,
) -> tuple[ResearchTeamDomainMemoryWritebackSnapshot, ...]:
    if not isinstance(snapshots, Sequence) or isinstance(snapshots, (str, bytes)):
        raise ValueError("snapshots must be a sequence")
    normalized: list[ResearchTeamDomainMemoryWritebackSnapshot] = []
    seen: set[tuple[str, str, str]] = set()
    for snapshot in snapshots:
        if type(snapshot) is not ResearchTeamDomainMemoryWritebackSnapshot:
            raise ValueError("snapshots must contain ResearchTeamDomainMemoryWritebackSnapshot")
        _require_hard_flags("snapshot", snapshot)
        _reject_future_timestamp("observed_at", snapshot.observed_at, generated_at)
        if snapshot.writeback_at is not None:
            _reject_future_timestamp("writeback_at", snapshot.writeback_at, generated_at)
        key = (snapshot.team_id, snapshot.domain_id, snapshot.case_key)
        if key in seen:
            raise ValueError("snapshots must use deterministic unique team/domain/case keys")
        seen.add(key)
        normalized.append(snapshot)
    return tuple(sorted(normalized, key=lambda item: (item.team_id, item.domain_id, item.case_key)))


def _normalize_rows(
    rows: object,
) -> tuple[ResearchTeamDomainMemoryWritebackExceptionRow, ...]:
    if type(rows) is not tuple:
        raise ValueError("rows must be a tuple")
    normalized = tuple(rows)
    for row in normalized:
        if type(row) is not ResearchTeamDomainMemoryWritebackExceptionRow:
            raise ValueError("rows must contain ResearchTeamDomainMemoryWritebackExceptionRow")
        _require_hard_flags("row", row)
    if normalized != tuple(sorted(normalized, key=_row_sort_key)):
        raise ValueError("rows must be deterministically sorted")
    return normalized


def _normalize_rollups(
    rollups: object,
) -> tuple[ResearchTeamDomainMemoryWritebackTeamDomainRollup, ...]:
    if type(rollups) is not tuple:
        raise ValueError("team_domain_rollups must be a tuple")
    normalized = tuple(rollups)
    for rollup in normalized:
        if type(rollup) is not ResearchTeamDomainMemoryWritebackTeamDomainRollup:
            raise ValueError(
                "team_domain_rollups must contain "
                "ResearchTeamDomainMemoryWritebackTeamDomainRollup",
            )
        _require_hard_flags("rollup", rollup)
    if normalized != tuple(sorted(normalized, key=_rollup_sort_key)):
        raise ValueError("team_domain_rollups must be deterministically sorted")
    return normalized


def _row_sort_key(
    row: ResearchTeamDomainMemoryWritebackExceptionRow,
) -> tuple[int, str, str, str]:
    return (_STATUS_WEIGHT[row.status], row.team_id, row.domain_id, row.memory_case_ref)


def _rollup_sort_key(
    rollup: ResearchTeamDomainMemoryWritebackTeamDomainRollup,
) -> tuple[int, Decimal, Decimal, str, str]:
    return (
        _STATUS_WEIGHT[rollup.status],
        -rollup.block_count,
        -rollup.watch_count,
        rollup.team_id,
        rollup.domain_id,
    )


def _aggregate_status(rows: tuple[ResearchTeamDomainMemoryWritebackExceptionRow, ...]) -> str:
    if any(row.status == "block" for row in rows):
        return "block"
    if any(row.status == "watch" for row in rows):
        return "watch"
    return "pass"


def _report_reason_codes(
    rows: tuple[ResearchTeamDomainMemoryWritebackExceptionRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return (_EMPTY_REASON,)
    present: set[str] = set()
    for row in rows:
        present.update(row.reason_codes)
    if not present:
        return (_EMPTY_REASON,)
    return tuple(code for code in _REASON_CODE_ORDER if code in present)


def _status_count(
    rows: tuple[ResearchTeamDomainMemoryWritebackExceptionRow, ...],
    status: str,
) -> Decimal:
    return _decimal_count(sum(1 for row in rows if row.status == status))


def _reason_count(
    rows: tuple[ResearchTeamDomainMemoryWritebackExceptionRow, ...],
    reason_code: str,
) -> Decimal:
    return _decimal_count(sum(1 for row in rows if reason_code in row.reason_codes))


def _max_row_decimal(
    rows: tuple[object, ...],
    field_name: str,
) -> Decimal:
    return max((getattr(row, field_name) for row in rows), default=_ZERO)


def _validate_row_consistency(row: ResearchTeamDomainMemoryWritebackExceptionRow) -> None:
    expected_missing = row.writeback_at is None
    if row.missing_writeback is not expected_missing:
        raise ValueError("missing_writeback must match writeback_at")
    if row.stale_writeback_age and row.writeback_at is None:
        raise ValueError("stale_writeback_age requires writeback_at")
    expected_reasons: set[str] = set()
    if row.missing_writeback:
        expected_reasons.add("missing_writeback")
    if row.stale_writeback_age:
        expected_reasons.add("stale_writeback_age")
    if row.unresolved_outcome_link:
        expected_reasons.add("unresolved_outcome_link")
    if row.status == "pass" and expected_reasons:
        raise ValueError("pass rows must not carry blocking writeback reason codes")


def _validate_rollup_consistency(
    rollup: ResearchTeamDomainMemoryWritebackTeamDomainRollup,
) -> None:
    if rollup.row_count != _add_decimal(
        rollup.pass_count,
        rollup.watch_count,
        rollup.block_count,
    ):
        raise ValueError("rollup row_count must match status counts")
    expected_status = "block" if rollup.block_count > _ZERO else "watch" if rollup.watch_count > _ZERO else "pass"
    if rollup.status != expected_status:
        raise ValueError("rollup status must match status counts")


def _validate_report_consistency(
    report: ResearchTeamDomainMemoryWritebackExceptionReport,
) -> None:
    if report.row_count != _decimal_count(len(report.rows)):
        raise ValueError("row_count must match rows")
    if report.input_count != report.row_count:
        raise ValueError("input_count must match row_count for this report-only reducer")
    if report.row_count != _add_decimal(report.pass_count, report.watch_count, report.block_count):
        raise ValueError("row_count must match status counts")
    if report.pass_count != _status_count(report.rows, "pass"):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _status_count(report.rows, "watch"):
        raise ValueError("watch_count must match rows")
    if report.block_count != _status_count(report.rows, "block"):
        raise ValueError("block_count must match rows")
    if report.status != _aggregate_status(report.rows):
        raise ValueError("status must match rows")
    expected_reason_counts = {
        "missing_writeback_count": "missing_writeback",
        "stale_writeback_count": "stale_writeback_age",
        "unresolved_outcome_link_count": "unresolved_outcome_link",
        "calibration_feedback_backlog_count": "calibration_feedback_backlog",
        "manual_review_urgent_count": "manual_review_urgency",
    }
    for field_name, reason_code in expected_reason_counts.items():
        if getattr(report, field_name) != _reason_count(report.rows, reason_code):
            raise ValueError(f"{field_name} must match rows")
    if report.team_domain_rollup_count != _decimal_count(len(report.team_domain_rollups)):
        raise ValueError("team_domain_rollup_count must match team_domain_rollups")
    if report.max_writeback_age_seconds != _max_row_decimal(report.rows, "writeback_age_seconds"):
        raise ValueError("max_writeback_age_seconds must match rows")
    if report.max_manual_review_urgency != _max_row_decimal(report.rows, "manual_review_urgency"):
        raise ValueError("max_manual_review_urgency must match rows")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")


def _report_values_without_digest(
    report: ResearchTeamDomainMemoryWritebackExceptionReport,
) -> dict[str, object]:
    values = asdict(report)
    values.pop("derived_validation_digest", None)
    return values


def _report_digest_from_values(values: Mapping[str, object]) -> str:
    payload = _json_ready(values)
    _reject_unsafe_public_payload("digest payload", payload, allow_json_containers=True)
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
    if any(fragment in lowered for fragment in _UNSAFE_PUBLIC_FIELD_FRAGMENTS):
        raise ValueError(f"{path}.{key} has unsafe public field")


def _reject_unsafe_public_string(path: str, value: str) -> None:
    lowered = value.lower()
    if any(fragment in lowered for fragment in _UNSAFE_PUBLIC_VALUE_FRAGMENTS):
        raise ValueError(f"{path} has unsafe public value")


def _require_hard_flags(label: str, value: object) -> None:
    if getattr(value, "paper_only") is not True:
        raise ValueError(f"paper_only must be True for {label}")
    if getattr(value, "report_only") is not True:
        raise ValueError(f"report_only must be True for {label}")
    if getattr(value, "readonly") is not True:
        raise ValueError(f"readonly must be True for {label}")


def _require_public_identifier(field_name: str, value: object) -> str:
    if type(value) is not str or not _PUBLIC_IDENTIFIER_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a public identifier")
    return value


def _require_nonempty_string(field_name: str, value: object) -> str:
    if type(value) is not str or not value.strip():
        raise ValueError(f"{field_name} must be a non-empty string")
    return value


def _require_memory_case_ref(value: object) -> None:
    if type(value) is not str:
        raise ValueError("memory_case_ref must be a public reference")
    if not re.fullmatch(r"memory_case_[0-9a-f]{16}", value):
        raise ValueError("memory_case_ref must be a redacted public reference")


def _require_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in _STATUSES:
        raise ValueError(f"{field_name} must be one of pass/watch/block")


def _require_bool(field_name: str, value: object) -> None:
    if type(value) is not bool:
        raise ValueError(f"{field_name} must be a bool")


def _require_sha256_digest(field_name: str, value: object) -> None:
    if type(value) is not str or not _DIGEST_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a SHA-256 hex digest")


def _normalize_reason_codes(value: object) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ValueError("reason_codes must be a tuple")
    normalized: list[str] = []
    seen: set[str] = set()
    allowed = set(_REASON_CODE_ORDER) | {_EMPTY_REASON}
    for item in value:
        if type(item) is not str or item not in allowed:
            raise ValueError("reason_codes must contain supported reason codes")
        if item in seen:
            raise ValueError("reason_codes must be unique")
        seen.add(item)
        normalized.append(item)
    if _EMPTY_REASON in seen and len(seen) > 1:
        raise ValueError("empty reason code must not be mixed with exception reasons")
    expected_order = tuple(code for code in (*_REASON_CODE_ORDER, _EMPTY_REASON) if code in seen)
    if tuple(normalized) != expected_order:
        raise ValueError("reason_codes must be deterministically ordered")
    return tuple(normalized)


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _as_optional_utc(field_name: str, value: object) -> datetime | None:
    if value is None:
        return None
    return _as_utc(field_name, value)


def _reject_future_timestamp(field_name: str, value: datetime, generated_at: datetime) -> None:
    if value > generated_at:
        raise ValueError(f"{field_name} must not be after generated_at")


def _seconds_between(later: datetime, earlier: datetime, earlier_name: str) -> Decimal:
    if earlier > later:
        raise ValueError(f"{earlier_name} must not be after generated_at")
    return _quantize(Decimal(str((later - earlier).total_seconds())))


def _require_positive_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized <= _ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _require_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized < _ZERO:
        raise ValueError(f"{field_name} must be non-negative")
    return normalized


def _require_ratio_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized < _ZERO or normalized > _ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return normalized


def _require_positive_count_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_nonnegative_count_decimal(field_name, value)
    if normalized <= _ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _require_nonnegative_count_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_nonnegative_decimal(field_name, value)
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{field_name} must be an integer count")
    return normalized


def _normalize_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return _quantize(value)


def _quantize(value: Decimal) -> Decimal:
    with localcontext(_DECIMAL_CONTEXT):
        return value.quantize(_QUANTUM)


def _decimal_count(value: int) -> Decimal:
    return _quantize(Decimal(value))


def _add_decimal(*values: Decimal) -> Decimal:
    return _quantize(sum(values, _ZERO))


def _memory_case_ref(case_key: str) -> str:
    digest = hashlib.sha256(case_key.encode("utf-8")).hexdigest()[:16]
    return f"memory_case_{digest}"


__all__ = (
    "DEFAULT_RESEARCH_TEAM_DOMAIN_MEMORY_WRITEBACK_EXCEPTION_REPORT_CONFIG_VERSION",
    "ResearchTeamDomainMemoryWritebackExceptionReport",
    "ResearchTeamDomainMemoryWritebackExceptionReportConfig",
    "ResearchTeamDomainMemoryWritebackExceptionRow",
    "ResearchTeamDomainMemoryWritebackSnapshot",
    "ResearchTeamDomainMemoryWritebackTeamDomainRollup",
    "build_research_team_domain_memory_writeback_exception_report",
)
