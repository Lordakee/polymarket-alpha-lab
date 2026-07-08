"""Public-safe specialist team memory consolidation queue report."""

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
    "DEFAULT_RESEARCH_TEAM_MEMORY_CONSOLIDATION_QUEUE_REPORT_CONFIG_VERSION",
    "ResearchTeamMemoryConsolidationQueueConfig",
    "ResearchTeamMemoryConsolidationQueueInput",
    "ResearchTeamMemoryConsolidationQueueReasonCodeCount",
    "ResearchTeamMemoryConsolidationQueueReport",
    "ResearchTeamMemoryConsolidationQueueRow",
    "build_research_team_memory_consolidation_queue_report",
    "research_team_memory_consolidation_queue_report_payload",
)


DEFAULT_RESEARCH_TEAM_MEMORY_CONSOLIDATION_QUEUE_REPORT_CONFIG_VERSION = (
    "research-team-memory-consolidation-queue-report-v0"
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
    "pass": "paper_memory_consolidation_monitor",
    "watch": "paper_memory_consolidation_watch",
    "block": "paper_memory_consolidation_block",
}
PASS_ROW_REASON_CODE = "memory_consolidation_clear"
EMPTY_REPORT_REASON_CODE = "memory_consolidation_queue_empty"
BLOCK_REASON_CODES = (
    "sample_count_block",
    "calibration_drift_block",
    "stale_memory_block",
    "evidence_gap_block",
    "domain_coverage_block",
)
WATCH_REASON_CODES = (
    "sample_count_watch",
    "calibration_drift_watch",
    "stale_memory_watch",
    "evidence_gap_watch",
    "domain_coverage_watch",
)
ROW_REASON_CODES = BLOCK_REASON_CODES + WATCH_REASON_CODES + (PASS_ROW_REASON_CODE,)
REPORT_REASON_PRIORITY = BLOCK_REASON_CODES + WATCH_REASON_CODES
HEX_CHARS = frozenset("0123456789abcdef")
UNSAFE_PUBLIC_FRAGMENTS = frozenset(
    (
        "event",
        "market",
        "source",
        "wallet",
        "auth",
        "order",
        "trade",
        "live",
        "database",
        "network",
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
class ResearchTeamMemoryConsolidationQueueConfig(_FinalPublicDataclass):
    config_version: str = (
        DEFAULT_RESEARCH_TEAM_MEMORY_CONSOLIDATION_QUEUE_REPORT_CONFIG_VERSION
    )
    watch_min_sample_count: Decimal = Decimal("30")
    block_min_sample_count: Decimal = Decimal("10")
    watch_calibration_drift: Decimal = Decimal("0.050000")
    block_calibration_drift: Decimal = Decimal("0.120000")
    watch_stale_memory_hours: Decimal = Decimal("48.000000")
    block_stale_memory_hours: Decimal = Decimal("168.000000")
    watch_evidence_gap_ratio: Decimal = Decimal("0.100000")
    block_evidence_gap_ratio: Decimal = Decimal("0.250000")
    watch_min_domain_coverage_ratio: Decimal = Decimal("0.650000")
    block_min_domain_coverage_ratio: Decimal = Decimal("0.400000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchTeamMemoryConsolidationQueueConfig,
            "config",
        )
        _require_public_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_TEAM_MEMORY_CONSOLIDATION_QUEUE_REPORT_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in ("watch_min_sample_count", "block_min_sample_count"):
            object.__setattr__(
                self,
                field_name,
                _require_count_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "watch_calibration_drift",
            "block_calibration_drift",
            "watch_evidence_gap_ratio",
            "block_evidence_gap_ratio",
            "watch_min_domain_coverage_ratio",
            "block_min_domain_coverage_ratio",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in ("watch_stale_memory_hours", "block_stale_memory_hours"):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        _validate_config(self)
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class ResearchTeamMemoryConsolidationQueueInput(_FinalPublicDataclass):
    team_key: str
    aggregate_sample_count: Decimal
    calibration_drift: Decimal
    stale_memory_hours: Decimal
    evidence_gap_ratio: Decimal
    domain_coverage_ratio: Decimal
    observed_at: datetime
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchTeamMemoryConsolidationQueueInput, "input")
        _require_safe_team_key("team_key", self.team_key)
        object.__setattr__(
            self,
            "aggregate_sample_count",
            _require_count_decimal("aggregate_sample_count", self.aggregate_sample_count),
        )
        object.__setattr__(
            self,
            "calibration_drift",
            _require_signed_ratio_decimal("calibration_drift", self.calibration_drift),
        )
        object.__setattr__(
            self,
            "stale_memory_hours",
            _require_nonnegative_decimal("stale_memory_hours", self.stale_memory_hours),
        )
        for field_name in ("evidence_gap_ratio", "domain_coverage_ratio"):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        _require_hard_flags("input", self)


@dataclass(frozen=True)
class ResearchTeamMemoryConsolidationQueueRow(_FinalPublicDataclass):
    team_key: str
    memory_status: str
    aggregate_sample_count: Decimal
    calibration_drift: Decimal
    stale_memory_hours: Decimal
    evidence_gap_ratio: Decimal
    domain_coverage_ratio: Decimal
    observed_at: datetime
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchTeamMemoryConsolidationQueueRow, "row")
        _require_safe_team_key("team_key", self.team_key)
        _require_status("memory_status", self.memory_status)
        object.__setattr__(
            self,
            "aggregate_sample_count",
            _require_count_decimal("aggregate_sample_count", self.aggregate_sample_count),
        )
        object.__setattr__(
            self,
            "calibration_drift",
            _require_signed_ratio_decimal("calibration_drift", self.calibration_drift),
        )
        object.__setattr__(
            self,
            "stale_memory_hours",
            _require_nonnegative_decimal("stale_memory_hours", self.stale_memory_hours),
        )
        for field_name in ("evidence_gap_ratio", "domain_coverage_ratio"):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
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
class ResearchTeamMemoryConsolidationQueueReasonCodeCount(_FinalPublicDataclass):
    reason_code: str
    count: Decimal
    memory_task_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchTeamMemoryConsolidationQueueReasonCodeCount,
            "reason_code_count",
        )
        _require_public_string("reason_code", self.reason_code)
        object.__setattr__(self, "count", _require_count_decimal("count", self.count))
        object.__setattr__(
            self,
            "memory_task_ratio",
            _require_ratio_decimal("memory_task_ratio", self.memory_task_ratio),
        )
        _require_hard_flags("reason_code_count", self)


@dataclass(frozen=True)
class ResearchTeamMemoryConsolidationQueueReport(_FinalPublicDataclass):
    generated_at: datetime
    config_version: str
    memory_task_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    min_sample_count: Decimal
    max_calibration_drift: Decimal
    max_stale_memory_hours: Decimal
    max_evidence_gap_ratio: Decimal
    min_domain_coverage_ratio: Decimal
    status: str
    paper_queue_action: str
    reason_codes: tuple[str, ...]
    reason_code_counts: tuple[ResearchTeamMemoryConsolidationQueueReasonCodeCount, ...]
    rows: tuple[ResearchTeamMemoryConsolidationQueueRow, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchTeamMemoryConsolidationQueueReport, "report")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_TEAM_MEMORY_CONSOLIDATION_QUEUE_REPORT_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "memory_task_count",
            "pass_count",
            "watch_count",
            "block_count",
            "min_sample_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_count_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "max_calibration_drift",
            _require_ratio_decimal("max_calibration_drift", self.max_calibration_drift),
        )
        for field_name in (
            "max_stale_memory_hours",
            "max_evidence_gap_ratio",
            "min_domain_coverage_ratio",
        ):
            if field_name.endswith("_ratio"):
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


def build_research_team_memory_consolidation_queue_report(
    memory_items: Iterable[ResearchTeamMemoryConsolidationQueueInput],
    *,
    config: ResearchTeamMemoryConsolidationQueueConfig,
    generated_at: datetime,
) -> ResearchTeamMemoryConsolidationQueueReport:
    if type(config) is not ResearchTeamMemoryConsolidationQueueConfig:
        raise ValueError("config must be a ResearchTeamMemoryConsolidationQueueConfig")
    _require_hard_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    inputs = _normalize_inputs(memory_items)
    rows = tuple(
        sorted(
            (
                _row_from_input(item, config=config, generated_at=generated_at_utc)
                for item in inputs
            ),
            key=_row_sort_key,
        ),
    )
    status = _rollup_status(tuple(row.memory_status for row in rows))
    return ResearchTeamMemoryConsolidationQueueReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        memory_task_count=_count(len(rows)),
        pass_count=_status_count(rows, "pass"),
        watch_count=_status_count(rows, "watch"),
        block_count=_status_count(rows, "block"),
        min_sample_count=_min_decimal(
            tuple(row.aggregate_sample_count for row in rows),
            count=True,
        ),
        max_calibration_drift=_max_decimal(
            tuple(_abs_decimal(row.calibration_drift) for row in rows),
        ),
        max_stale_memory_hours=_max_decimal(
            tuple(row.stale_memory_hours for row in rows),
        ),
        max_evidence_gap_ratio=_max_decimal(
            tuple(row.evidence_gap_ratio for row in rows),
        ),
        min_domain_coverage_ratio=_min_decimal(
            tuple(row.domain_coverage_ratio for row in rows),
        ),
        status=status,
        paper_queue_action=PAPER_ACTION_BY_STATUS[status],
        reason_codes=_report_reason_codes(rows),
        reason_code_counts=_reason_code_counts(rows),
        rows=rows,
    )


def research_team_memory_consolidation_queue_report_payload(
    report: ResearchTeamMemoryConsolidationQueueReport | dict[str, Any],
) -> dict[str, Any]:
    if type(report) is ResearchTeamMemoryConsolidationQueueReport:
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
        supplied_digest = payload.get("derived_validation_digest")
        if type(supplied_digest) is not str:
            raise ValueError("derived_validation_digest is required")
        _require_sha256("derived_validation_digest", supplied_digest)
        if supplied_digest != _payload_validation_digest(payload):
            raise ValueError("derived_validation_digest does not match report payload")
        return payload
    raise ValueError("report must be a ResearchTeamMemoryConsolidationQueueReport")


@dataclass(frozen=True)
class _PayloadFlags:
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


def _normalize_inputs(
    memory_items: Iterable[ResearchTeamMemoryConsolidationQueueInput],
) -> tuple[ResearchTeamMemoryConsolidationQueueInput, ...]:
    if isinstance(memory_items, (str, bytes)):
        raise ValueError("memory_items must be an iterable")
    try:
        items = tuple(memory_items)
    except TypeError as exc:
        raise ValueError("memory_items must be an iterable") from exc
    seen: set[str] = set()
    for item in items:
        if type(item) is not ResearchTeamMemoryConsolidationQueueInput:
            raise ValueError(
                "memory_items must contain ResearchTeamMemoryConsolidationQueueInput",
            )
        _require_hard_flags("input", item)
        if item.team_key in seen:
            raise ValueError("team_key values must be unique")
        seen.add(item.team_key)
    return items


def _row_from_input(
    item: ResearchTeamMemoryConsolidationQueueInput,
    *,
    config: ResearchTeamMemoryConsolidationQueueConfig,
    generated_at: datetime,
) -> ResearchTeamMemoryConsolidationQueueRow:
    if item.observed_at > generated_at:
        raise ValueError("observed_at must not be in the future")
    reason_codes = _row_reason_codes(item, config=config)
    return ResearchTeamMemoryConsolidationQueueRow(
        team_key=item.team_key,
        memory_status=_row_status(reason_codes),
        aggregate_sample_count=item.aggregate_sample_count,
        calibration_drift=item.calibration_drift,
        stale_memory_hours=item.stale_memory_hours,
        evidence_gap_ratio=item.evidence_gap_ratio,
        domain_coverage_ratio=item.domain_coverage_ratio,
        observed_at=item.observed_at,
        reason_codes=reason_codes,
    )


def _row_reason_codes(
    item: ResearchTeamMemoryConsolidationQueueInput,
    *,
    config: ResearchTeamMemoryConsolidationQueueConfig,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    abs_drift = _abs_decimal(item.calibration_drift)
    if item.aggregate_sample_count < config.block_min_sample_count:
        reason_codes.append("sample_count_block")
    elif item.aggregate_sample_count < config.watch_min_sample_count:
        reason_codes.append("sample_count_watch")

    if abs_drift >= config.block_calibration_drift:
        reason_codes.append("calibration_drift_block")
    elif abs_drift >= config.watch_calibration_drift:
        reason_codes.append("calibration_drift_watch")

    if item.stale_memory_hours >= config.block_stale_memory_hours:
        reason_codes.append("stale_memory_block")
    elif item.stale_memory_hours >= config.watch_stale_memory_hours:
        reason_codes.append("stale_memory_watch")

    if item.evidence_gap_ratio >= config.block_evidence_gap_ratio:
        reason_codes.append("evidence_gap_block")
    elif item.evidence_gap_ratio >= config.watch_evidence_gap_ratio:
        reason_codes.append("evidence_gap_watch")

    if item.domain_coverage_ratio < config.block_min_domain_coverage_ratio:
        reason_codes.append("domain_coverage_block")
    elif item.domain_coverage_ratio < config.watch_min_domain_coverage_ratio:
        reason_codes.append("domain_coverage_watch")

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
    rows: tuple[ResearchTeamMemoryConsolidationQueueRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return (EMPTY_REPORT_REASON_CODE,)
    status = _rollup_status(tuple(row.memory_status for row in rows))
    reason_codes = [
        f"memory_consolidation_queue_{'clear' if status == 'pass' else status}",
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
    rows: tuple[ResearchTeamMemoryConsolidationQueueRow, ...],
) -> tuple[ResearchTeamMemoryConsolidationQueueReasonCodeCount, ...]:
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
        ResearchTeamMemoryConsolidationQueueReasonCodeCount(
            reason_code=reason_code,
            count=count,
            memory_task_ratio=_ratio(count, denominator),
        )
        for count, reason_code in sorted(
            ((_count(count), reason_code) for reason_code, count in counter.items()),
            key=lambda item: (-item[0], priority.get(item[1], 999), item[1]),
        )
    )


def _row_sort_key(
    row: ResearchTeamMemoryConsolidationQueueRow,
) -> tuple[Decimal, Decimal, str]:
    return (
        -STATUS_WEIGHT[row.memory_status],
        -_row_severity_score(row),
        row.team_key,
    )


def _row_severity_score(row: ResearchTeamMemoryConsolidationQueueRow) -> Decimal:
    severity = STATUS_WEIGHT[row.memory_status]
    severity += _abs_decimal(row.calibration_drift)
    severity += row.evidence_gap_ratio
    severity += ONE_RATIO - row.domain_coverage_ratio
    return severity


def _status_count(
    rows: tuple[ResearchTeamMemoryConsolidationQueueRow, ...],
    status: str,
) -> Decimal:
    return _count(sum(1 for row in rows if row.memory_status == status))


def _validate_config(config: ResearchTeamMemoryConsolidationQueueConfig) -> None:
    if config.block_min_sample_count > config.watch_min_sample_count:
        raise ValueError("block_min_sample_count must not exceed watch_min_sample_count")
    if config.block_calibration_drift < config.watch_calibration_drift:
        raise ValueError("block_calibration_drift must be at least watch_calibration_drift")
    if config.block_stale_memory_hours < config.watch_stale_memory_hours:
        raise ValueError("block_stale_memory_hours must be at least watch_stale_memory_hours")
    if config.block_evidence_gap_ratio < config.watch_evidence_gap_ratio:
        raise ValueError("block_evidence_gap_ratio must be at least watch_evidence_gap_ratio")
    if config.block_min_domain_coverage_ratio > config.watch_min_domain_coverage_ratio:
        raise ValueError(
            "block_min_domain_coverage_ratio must not exceed "
            "watch_min_domain_coverage_ratio",
        )


def _validate_row(row: ResearchTeamMemoryConsolidationQueueRow) -> None:
    if row.memory_status != _row_status(row.reason_codes):
        raise ValueError("memory_status must match reason_codes")
    if row.memory_status == "pass" and row.reason_codes != (PASS_ROW_REASON_CODE,):
        raise ValueError("pass rows require memory_consolidation_clear")
    if row.memory_status != "pass" and PASS_ROW_REASON_CODE in row.reason_codes:
        raise ValueError("queued rows must not contain clear reason_codes")


def _validate_report_materialized_fields(
    report: ResearchTeamMemoryConsolidationQueueReport,
) -> None:
    rows = report.rows
    checks = {
        "memory_task_count": _count(len(rows)),
        "pass_count": _status_count(rows, "pass"),
        "watch_count": _status_count(rows, "watch"),
        "block_count": _status_count(rows, "block"),
        "min_sample_count": _min_decimal(
            tuple(row.aggregate_sample_count for row in rows),
            count=True,
        ),
        "max_calibration_drift": _max_decimal(
            tuple(_abs_decimal(row.calibration_drift) for row in rows),
        ),
        "max_stale_memory_hours": _max_decimal(
            tuple(row.stale_memory_hours for row in rows),
        ),
        "max_evidence_gap_ratio": _max_decimal(
            tuple(row.evidence_gap_ratio for row in rows),
        ),
        "min_domain_coverage_ratio": _min_decimal(
            tuple(row.domain_coverage_ratio for row in rows),
        ),
    }
    for field_name, expected in checks.items():
        if getattr(report, field_name) != expected:
            raise ValueError(f"{field_name} must match rows")
    expected_status = _rollup_status(tuple(row.memory_status for row in rows))
    if report.status != expected_status:
        raise ValueError("status must match rows")
    if report.paper_queue_action != PAPER_ACTION_BY_STATUS[report.status]:
        raise ValueError("paper_queue_action must match status")
    if report.reason_codes != _report_reason_codes(rows):
        raise ValueError("reason_codes must match rows")
    if report.reason_code_counts != _reason_code_counts(rows):
        raise ValueError("reason_code_counts must match rows")


def _require_rows(
    rows: tuple[ResearchTeamMemoryConsolidationQueueRow, ...],
) -> tuple[ResearchTeamMemoryConsolidationQueueRow, ...]:
    if isinstance(rows, (str, bytes)):
        raise ValueError("rows must be an iterable")
    try:
        normalized = tuple(rows)
    except TypeError as exc:
        raise ValueError("rows must be an iterable") from exc
    seen: set[str] = set()
    for row in normalized:
        if type(row) is not ResearchTeamMemoryConsolidationQueueRow:
            raise ValueError("rows must contain ResearchTeamMemoryConsolidationQueueRow")
        _require_hard_flags("row", row)
        if row.team_key in seen:
            raise ValueError("rows must contain unique team_key values")
        seen.add(row.team_key)
    if normalized != tuple(sorted(normalized, key=_row_sort_key)):
        raise ValueError("rows must be sorted by status and team_key")
    return normalized


def _require_reason_code_counts(
    rows: tuple[ResearchTeamMemoryConsolidationQueueReasonCodeCount, ...],
) -> tuple[ResearchTeamMemoryConsolidationQueueReasonCodeCount, ...]:
    if isinstance(rows, (str, bytes)):
        raise ValueError("reason_code_counts must be an iterable")
    try:
        normalized = tuple(rows)
    except TypeError as exc:
        raise ValueError("reason_code_counts must be an iterable") from exc
    for row in normalized:
        if type(row) is not ResearchTeamMemoryConsolidationQueueReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "ResearchTeamMemoryConsolidationQueueReasonCodeCount",
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


def _require_safe_team_key(field_name: str, value: object) -> None:
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
            or reason_code.startswith("memory_consolidation_queue_")
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


def _require_ratio_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_nonnegative_decimal(field_name, value)
    if normalized > ONE_RATIO:
        raise ValueError(f"{field_name} must be no greater than 1")
    return normalized


def _require_signed_ratio_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < -ONE_RATIO or normalized > ONE_RATIO:
        raise ValueError(f"{field_name} must be between -1 and 1")
    return _quantize_ratio(normalized)


def _quantize_ratio(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(RATIO_QUANTUM)


def _count(value: int) -> Decimal:
    return Decimal(value).quantize(COUNT_QUANTUM)


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO_COUNT:
        return ZERO_RATIO
    with localcontext(DECIMAL_CONTEXT):
        return (numerator / denominator).quantize(RATIO_QUANTUM)


def _abs_decimal(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return abs(value).quantize(RATIO_QUANTUM)


def _max_decimal(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return ZERO_RATIO
    return max(values).quantize(RATIO_QUANTUM)


def _min_decimal(values: tuple[Decimal, ...], *, count: bool = False) -> Decimal:
    if not values:
        return ZERO_COUNT if count else ZERO_RATIO
    value = min(values)
    return value.quantize(COUNT_QUANTUM if count else RATIO_QUANTUM)


def _require_sha256(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a sha256 hex digest")
    if len(value) != 64 or any(character not in HEX_CHARS for character in value):
        raise ValueError(f"{field_name} must be a sha256 hex digest")


def _derived_validation_digest(
    report: ResearchTeamMemoryConsolidationQueueReport,
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


def _json_ready_without_digest(report: ResearchTeamMemoryConsolidationQueueReport) -> dict[str, Any]:
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
            _reject_unsafe_public_payload(field.name, getattr(value, field.name))
        return
    if isinstance(value, dict):
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError(f"{label} contains unsafe public key")
            _reject_unsafe_public_text("public key", key)
            _reject_unsafe_public_payload(key, item)
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
        raise ValueError(f"{field_name} contains unsafe public text")
