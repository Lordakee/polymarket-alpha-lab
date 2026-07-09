"""Pure report-only quality audit for specialist research team memory."""

from __future__ import annotations

from dataclasses import dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
import json
from typing import Any


DEFAULT_RESEARCH_TEAM_MEMORY_QUALITY_AUDIT_CONFIG_VERSION = (
    "research-team-memory-quality-audit-v0"
)

STATUS_PASS = "pass"
STATUS_WATCH = "watch"
STATUS_BLOCK = "block"

NO_INPUTS_REASON = "research_team_memory_quality_audit_no_inputs"
PASS_REASON = "research_team_memory_quality_audit_pass"
WATCH_CONFLICT_REASON = "research_team_memory_quality_audit_watch_conflict"
WATCH_COVERAGE_REASON = "research_team_memory_quality_audit_watch_coverage"
WATCH_QUALITY_REASON = "research_team_memory_quality_audit_watch_quality"
WATCH_STALE_REASON = "research_team_memory_quality_audit_watch_stale"
BLOCK_CONFLICT_REASON = "research_team_memory_quality_audit_block_conflict"
BLOCK_COVERAGE_REASON = "research_team_memory_quality_audit_block_coverage"
BLOCK_QUALITY_REASON = "research_team_memory_quality_audit_block_quality"
BLOCK_STALE_REASON = "research_team_memory_quality_audit_block_stale"

REASON_CODE_SEQUENCE = (
    BLOCK_CONFLICT_REASON,
    BLOCK_COVERAGE_REASON,
    BLOCK_QUALITY_REASON,
    BLOCK_STALE_REASON,
    NO_INPUTS_REASON,
    PASS_REASON,
    WATCH_CONFLICT_REASON,
    WATCH_COVERAGE_REASON,
    WATCH_QUALITY_REASON,
    WATCH_STALE_REASON,
)
ROW_REASON_CODE_SEQUENCE = (
    BLOCK_CONFLICT_REASON,
    BLOCK_COVERAGE_REASON,
    BLOCK_QUALITY_REASON,
    BLOCK_STALE_REASON,
    PASS_REASON,
    WATCH_CONFLICT_REASON,
    WATCH_COVERAGE_REASON,
    WATCH_QUALITY_REASON,
    WATCH_STALE_REASON,
)

DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
QUANT = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")

_STATUS_RANK = {STATUS_BLOCK: 0, STATUS_WATCH: 1, STATUS_PASS: 2}


def _join_parts(*parts: str) -> str:
    return "".join(parts)


_UNSAFE_PUBLIC_FRAGMENTS = frozenset(
    (
        _join_parts("raw_", "candidate"),
        _join_parts("candidate", "_id"),
        _join_parts("market", "_id"),
        _join_parts("market", "_slug"),
        _join_parts("question"),
        _join_parts("source", "_ref"),
        _join_parts("source", "_url"),
        _join_parts("source", "_text"),
        _join_parts("dsn"),
        _join_parts("table"),
        _join_parts("to", "ken"),
        _join_parts("wal", "let"),
        _join_parts("au", "th"),
        _join_parts("ord", "er"),
        _join_parts("tra", "de"),
        _join_parts("pos", "ition"),
        _join_parts("b", "uy"),
        _join_parts("s", "ell"),
        _join_parts("rec", "ommend"),
        _join_parts("sub", "mit"),
        "://",
    ),
)

_STATUS_SUMMARIES = {
    STATUS_PASS: "Memory quality is usable for review with routine maintenance.",
    STATUS_WATCH: (
        "Review quality, coverage, conflict, or freshness gaps before wider reuse."
    ),
    STATUS_BLOCK: (
        "Pause automated reuse until quality, coverage, conflict, and freshness gaps "
        "are reviewed by a human."
    ),
}


__all__ = (
    "DEFAULT_RESEARCH_TEAM_MEMORY_QUALITY_AUDIT_CONFIG_VERSION",
    "ResearchTeamMemoryQualityAuditConfig",
    "ResearchTeamMemoryQualityAuditInputRow",
    "ResearchTeamMemoryQualityAuditReasonCodeCount",
    "ResearchTeamMemoryQualityAuditReport",
    "ResearchTeamMemoryQualityAuditRow",
    "build_research_team_memory_quality_audit_report",
    "research_team_memory_quality_audit_report_digest",
    "research_team_memory_quality_audit_report_payload",
)


@dataclass(frozen=True)
class ResearchTeamMemoryQualityAuditConfig:
    config_version: str = DEFAULT_RESEARCH_TEAM_MEMORY_QUALITY_AUDIT_CONFIG_VERSION
    pass_quality_score: Decimal = Decimal("0.800000")
    watch_quality_score: Decimal = Decimal("0.600000")
    pass_coverage_ratio: Decimal = Decimal("0.800000")
    watch_coverage_ratio: Decimal = Decimal("0.600000")
    pass_conflict_ratio: Decimal = Decimal("0.100000")
    block_conflict_ratio: Decimal = Decimal("0.300000")
    pass_update_lag_seconds: Decimal = Decimal("1209600.000000")
    block_update_lag_seconds: Decimal = Decimal("2419200.000000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchTeamMemoryQualityAuditConfig:
            raise TypeError(
                "ResearchTeamMemoryQualityAuditConfig does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchTeamMemoryQualityAuditConfig:
            raise ValueError(
                "config must be exactly ResearchTeamMemoryQualityAuditConfig",
            )
        _require_public_string("config_version", self.config_version)
        for field_name in (
            "pass_quality_score",
            "watch_quality_score",
            "pass_coverage_ratio",
            "watch_coverage_ratio",
            "pass_conflict_ratio",
            "block_conflict_ratio",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in ("pass_update_lag_seconds", "block_update_lag_seconds"):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        if self.pass_quality_score <= self.watch_quality_score:
            raise ValueError("pass_quality_score must be greater than watch_quality_score")
        if self.pass_coverage_ratio <= self.watch_coverage_ratio:
            raise ValueError(
                "pass_coverage_ratio must be greater than watch_coverage_ratio",
            )
        if self.pass_conflict_ratio >= self.block_conflict_ratio:
            raise ValueError("pass_conflict_ratio must be below block_conflict_ratio")
        if self.pass_update_lag_seconds >= self.block_update_lag_seconds:
            raise ValueError(
                "pass_update_lag_seconds must be below block_update_lag_seconds",
            )
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class ResearchTeamMemoryQualityAuditInputRow:
    team_key: str
    specialist_key: str
    memory_scope: str
    quality_score: Decimal
    coverage_ratio: Decimal
    conflict_ratio: Decimal
    update_lag_seconds: Decimal
    reviewed_item_count: Decimal
    stale_item_count: Decimal
    conflict_item_count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchTeamMemoryQualityAuditInputRow:
            raise TypeError(
                "ResearchTeamMemoryQualityAuditInputRow does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchTeamMemoryQualityAuditInputRow:
            raise ValueError(
                "input row must be exactly ResearchTeamMemoryQualityAuditInputRow",
            )
        _require_public_string("team_key", self.team_key)
        _require_public_string("specialist_key", self.specialist_key)
        _require_public_string("memory_scope", self.memory_scope)
        for field_name in ("quality_score", "coverage_ratio", "conflict_ratio"):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "update_lag_seconds",
            _require_nonnegative_decimal("update_lag_seconds", self.update_lag_seconds),
        )
        for field_name in (
            "reviewed_item_count",
            "stale_item_count",
            "conflict_item_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_whole_decimal(field_name, getattr(self, field_name)),
            )
        if self.stale_item_count > self.reviewed_item_count:
            raise ValueError("stale_item_count must not exceed reviewed_item_count")
        if self.conflict_item_count > self.reviewed_item_count:
            raise ValueError("conflict_item_count must not exceed reviewed_item_count")
        _require_hard_flags("input row", self)


@dataclass(frozen=True)
class ResearchTeamMemoryQualityAuditRow:
    team_key: str
    specialist_key: str
    memory_scope: str
    public_status: str
    quality_score: Decimal
    coverage_ratio: Decimal
    conflict_ratio: Decimal
    update_lag_seconds: Decimal
    reviewed_item_count: Decimal
    stale_item_count: Decimal
    conflict_item_count: Decimal
    quality_gap: Decimal
    coverage_gap: Decimal
    conflict_excess_ratio: Decimal
    update_lag_excess_seconds: Decimal
    human_improvement_summary: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchTeamMemoryQualityAuditRow:
            raise TypeError(
                "ResearchTeamMemoryQualityAuditRow does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchTeamMemoryQualityAuditRow:
            raise ValueError("row must be exactly ResearchTeamMemoryQualityAuditRow")
        _require_public_string("team_key", self.team_key)
        _require_public_string("specialist_key", self.specialist_key)
        _require_public_string("memory_scope", self.memory_scope)
        _require_public_status("public_status", self.public_status)
        for field_name in (
            "quality_score",
            "coverage_ratio",
            "conflict_ratio",
            "quality_gap",
            "coverage_gap",
            "conflict_excess_ratio",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in ("update_lag_seconds", "update_lag_excess_seconds"):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "reviewed_item_count",
            "stale_item_count",
            "conflict_item_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_whole_decimal(field_name, getattr(self, field_name)),
            )
        if self.stale_item_count > self.reviewed_item_count:
            raise ValueError("stale_item_count must not exceed reviewed_item_count")
        if self.conflict_item_count > self.reviewed_item_count:
            raise ValueError("conflict_item_count must not exceed reviewed_item_count")
        _require_public_sentence("human_improvement_summary", self.human_improvement_summary)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        if self.public_status != _public_status_from_reason_codes(self.reason_codes):
            raise ValueError("public_status must match reason_codes")
        _require_hard_flags("row", self)


@dataclass(frozen=True)
class ResearchTeamMemoryQualityAuditReasonCodeCount:
    reason_code: str
    count: Decimal
    row_ratio: Decimal

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchTeamMemoryQualityAuditReasonCodeCount:
            raise TypeError(
                "ResearchTeamMemoryQualityAuditReasonCodeCount does not support "
                "subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchTeamMemoryQualityAuditReasonCodeCount:
            raise ValueError(
                "reason count must be exactly ResearchTeamMemoryQualityAuditReasonCodeCount",
            )
        _require_reason_code("reason_code", self.reason_code)
        object.__setattr__(
            self,
            "count",
            _require_nonnegative_decimal("count", self.count),
        )
        object.__setattr__(
            self,
            "row_ratio",
            _require_ratio_decimal("row_ratio", self.row_ratio),
        )


@dataclass(frozen=True)
class ResearchTeamMemoryQualityAuditReport:
    generated_at: datetime
    config_version: str
    report_status: str
    audited_team_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    average_quality_score: Decimal
    average_coverage_ratio: Decimal
    average_conflict_ratio: Decimal
    average_update_lag_seconds: Decimal
    stale_team_count: Decimal
    conflict_team_count: Decimal
    rows: tuple[ResearchTeamMemoryQualityAuditRow, ...]
    reason_code_counts: tuple[ResearchTeamMemoryQualityAuditReasonCodeCount, ...]
    reason_codes: tuple[str, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchTeamMemoryQualityAuditReport:
            raise TypeError(
                "ResearchTeamMemoryQualityAuditReport does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchTeamMemoryQualityAuditReport:
            raise ValueError("report must be exactly ResearchTeamMemoryQualityAuditReport")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_string("config_version", self.config_version)
        _require_public_status("report_status", self.report_status)
        for field_name in (
            "audited_team_count",
            "pass_count",
            "watch_count",
            "block_count",
            "stale_team_count",
            "conflict_team_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_whole_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "average_quality_score",
            "average_coverage_ratio",
            "average_conflict_ratio",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "average_update_lag_seconds",
            _require_nonnegative_decimal(
                "average_update_lag_seconds",
                self.average_update_lag_seconds,
            ),
        )
        object.__setattr__(self, "rows", _require_row_tuple("rows", self.rows))
        object.__setattr__(
            self,
            "reason_code_counts",
            _require_reason_count_tuple("reason_code_counts", self.reason_code_counts),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        if self.reason_codes != tuple(item.reason_code for item in self.reason_code_counts):
            raise ValueError("reason_codes must match reason_code_counts")
        if self.report_status != _report_status(self.rows):
            raise ValueError("report_status must match rows")
        _require_hard_flags("report", self)
        _require_or_set_digest(self)


def build_research_team_memory_quality_audit_report(
    rows: tuple[ResearchTeamMemoryQualityAuditInputRow, ...],
    *,
    config: ResearchTeamMemoryQualityAuditConfig | None = None,
    generated_at: datetime,
) -> ResearchTeamMemoryQualityAuditReport:
    cfg = config or ResearchTeamMemoryQualityAuditConfig()
    if type(cfg) is not ResearchTeamMemoryQualityAuditConfig:
        raise TypeError("config must be exactly ResearchTeamMemoryQualityAuditConfig")
    generated_at_utc = _as_utc("generated_at", generated_at)
    input_rows = _require_input_row_tuple("rows", rows)

    if not input_rows:
        reason_counts = (
            ResearchTeamMemoryQualityAuditReasonCodeCount(
                reason_code=NO_INPUTS_REASON,
                count=ONE,
                row_ratio=ZERO,
            ),
        )
        return ResearchTeamMemoryQualityAuditReport(
            generated_at=generated_at_utc,
            config_version=cfg.config_version,
            report_status=STATUS_BLOCK,
            audited_team_count=ZERO,
            pass_count=ZERO,
            watch_count=ZERO,
            block_count=ZERO,
            average_quality_score=ZERO,
            average_coverage_ratio=ZERO,
            average_conflict_ratio=ZERO,
            average_update_lag_seconds=ZERO,
            stale_team_count=ZERO,
            conflict_team_count=ZERO,
            rows=(),
            reason_code_counts=reason_counts,
            reason_codes=(NO_INPUTS_REASON,),
        )

    audit_rows = tuple(_build_row(row, config=cfg) for row in input_rows)
    sorted_rows = tuple(
        sorted(
            audit_rows,
            key=lambda row: (
                _STATUS_RANK[row.public_status],
                row.team_key,
                row.specialist_key,
                row.memory_scope,
            ),
        ),
    )
    reason_counts = _reason_code_counts(sorted_rows)
    reason_codes = tuple(item.reason_code for item in reason_counts)
    audited_count = _count_decimal(sorted_rows)

    return ResearchTeamMemoryQualityAuditReport(
        generated_at=generated_at_utc,
        config_version=cfg.config_version,
        report_status=_report_status(sorted_rows),
        audited_team_count=audited_count,
        pass_count=_sum_if(sorted_rows, lambda row: row.public_status == STATUS_PASS),
        watch_count=_sum_if(sorted_rows, lambda row: row.public_status == STATUS_WATCH),
        block_count=_sum_if(sorted_rows, lambda row: row.public_status == STATUS_BLOCK),
        average_quality_score=_average(row.quality_score for row in sorted_rows),
        average_coverage_ratio=_average(row.coverage_ratio for row in sorted_rows),
        average_conflict_ratio=_average(row.conflict_ratio for row in sorted_rows),
        average_update_lag_seconds=_average(
            (row.update_lag_seconds for row in sorted_rows),
        ),
        stale_team_count=_sum_if(
            sorted_rows,
            lambda row: WATCH_STALE_REASON in row.reason_codes
            or BLOCK_STALE_REASON in row.reason_codes,
        ),
        conflict_team_count=_sum_if(
            sorted_rows,
            lambda row: WATCH_CONFLICT_REASON in row.reason_codes
            or BLOCK_CONFLICT_REASON in row.reason_codes,
        ),
        rows=sorted_rows,
        reason_code_counts=reason_counts,
        reason_codes=reason_codes,
    )


def research_team_memory_quality_audit_report_payload(
    report: ResearchTeamMemoryQualityAuditReport,
) -> dict[str, Any]:
    if type(report) is not ResearchTeamMemoryQualityAuditReport:
        raise TypeError("report must be exactly ResearchTeamMemoryQualityAuditReport")
    _require_hard_flags("report", report)
    _require_or_set_digest(report)
    payload = _payload_value(report)
    if not isinstance(payload, dict):
        raise ValueError("report payload must be a JSON object")
    _verify_public_digest(payload)
    return payload


def research_team_memory_quality_audit_report_digest(
    report: ResearchTeamMemoryQualityAuditReport,
) -> dict[str, Any]:
    payload = research_team_memory_quality_audit_report_payload(report)
    return {
        "generated_at": payload["generated_at"],
        "config_version": payload["config_version"],
        "report_status": payload["report_status"],
        "audited_team_count": payload["audited_team_count"],
        "pass_count": payload["pass_count"],
        "watch_count": payload["watch_count"],
        "block_count": payload["block_count"],
        "reason_codes": payload["reason_codes"],
        "derived_validation_digest": payload["derived_validation_digest"],
    }


def _build_row(
    row: ResearchTeamMemoryQualityAuditInputRow,
    *,
    config: ResearchTeamMemoryQualityAuditConfig,
) -> ResearchTeamMemoryQualityAuditRow:
    quality_gap = _positive_gap(config.pass_quality_score, row.quality_score)
    coverage_gap = _positive_gap(config.pass_coverage_ratio, row.coverage_ratio)
    conflict_excess = _positive_gap(row.conflict_ratio, config.pass_conflict_ratio)
    update_lag_excess = _positive_gap(
        row.update_lag_seconds,
        config.pass_update_lag_seconds,
    )

    reasons: list[str] = []
    if row.conflict_ratio >= config.block_conflict_ratio:
        reasons.append(BLOCK_CONFLICT_REASON)
    elif row.conflict_ratio > config.pass_conflict_ratio:
        reasons.append(WATCH_CONFLICT_REASON)

    if row.coverage_ratio < config.watch_coverage_ratio:
        reasons.append(BLOCK_COVERAGE_REASON)
    elif row.coverage_ratio < config.pass_coverage_ratio:
        reasons.append(WATCH_COVERAGE_REASON)

    if row.quality_score < config.watch_quality_score:
        reasons.append(BLOCK_QUALITY_REASON)
    elif row.quality_score < config.pass_quality_score:
        reasons.append(WATCH_QUALITY_REASON)

    if row.update_lag_seconds >= config.block_update_lag_seconds:
        reasons.append(BLOCK_STALE_REASON)
    elif row.update_lag_seconds > config.pass_update_lag_seconds:
        reasons.append(WATCH_STALE_REASON)

    if not reasons:
        reasons.append(PASS_REASON)

    reason_codes = _normalize_reason_codes("reason_codes", tuple(reasons))
    public_status = _public_status_from_reason_codes(reason_codes)
    return ResearchTeamMemoryQualityAuditRow(
        team_key=row.team_key,
        specialist_key=row.specialist_key,
        memory_scope=row.memory_scope,
        public_status=public_status,
        quality_score=row.quality_score,
        coverage_ratio=row.coverage_ratio,
        conflict_ratio=row.conflict_ratio,
        update_lag_seconds=row.update_lag_seconds,
        reviewed_item_count=row.reviewed_item_count,
        stale_item_count=row.stale_item_count,
        conflict_item_count=row.conflict_item_count,
        quality_gap=quality_gap,
        coverage_gap=coverage_gap,
        conflict_excess_ratio=conflict_excess,
        update_lag_excess_seconds=update_lag_excess,
        human_improvement_summary=_STATUS_SUMMARIES[public_status],
        reason_codes=reason_codes,
    )


def _reason_code_counts(
    rows: tuple[ResearchTeamMemoryQualityAuditRow, ...],
) -> tuple[ResearchTeamMemoryQualityAuditReasonCodeCount, ...]:
    row_count = _count_decimal(rows)
    counts: dict[str, Decimal] = {}
    for row in rows:
        for reason_code in row.reason_codes:
            counts[reason_code] = counts.get(reason_code, ZERO) + ONE
    return tuple(
        ResearchTeamMemoryQualityAuditReasonCodeCount(
            reason_code=reason_code,
            count=count,
            row_ratio=_ratio(count, row_count),
        )
        for reason_code, count in sorted(
            counts.items(),
            key=lambda item: REASON_CODE_SEQUENCE.index(item[0]),
        )
    )


def _report_status(rows: tuple[ResearchTeamMemoryQualityAuditRow, ...]) -> str:
    if not rows:
        return STATUS_BLOCK
    if any(row.public_status == STATUS_BLOCK for row in rows):
        return STATUS_BLOCK
    if any(row.public_status == STATUS_WATCH for row in rows):
        return STATUS_WATCH
    return STATUS_PASS


def _public_status_from_reason_codes(reason_codes: tuple[str, ...]) -> str:
    if any(
        reason_code.startswith("research_team_memory_quality_audit_block")
        for reason_code in reason_codes
    ):
        return STATUS_BLOCK
    if reason_codes == (PASS_REASON,):
        return STATUS_PASS
    return STATUS_WATCH


def _require_input_row_tuple(
    field_name: str,
    value: tuple[ResearchTeamMemoryQualityAuditInputRow, ...],
) -> tuple[ResearchTeamMemoryQualityAuditInputRow, ...]:
    if not isinstance(value, tuple):
        raise TypeError(f"{field_name} must be a tuple")
    for row in value:
        if type(row) is not ResearchTeamMemoryQualityAuditInputRow:
            raise ValueError(
                f"{field_name} must contain ResearchTeamMemoryQualityAuditInputRow",
            )
    return value


def _require_row_tuple(
    field_name: str,
    value: tuple[ResearchTeamMemoryQualityAuditRow, ...],
) -> tuple[ResearchTeamMemoryQualityAuditRow, ...]:
    if not isinstance(value, tuple):
        raise TypeError(f"{field_name} must be a tuple")
    for row in value:
        if type(row) is not ResearchTeamMemoryQualityAuditRow:
            raise ValueError(
                f"{field_name} must contain ResearchTeamMemoryQualityAuditRow",
            )
    return value


def _require_reason_count_tuple(
    field_name: str,
    value: tuple[ResearchTeamMemoryQualityAuditReasonCodeCount, ...],
) -> tuple[ResearchTeamMemoryQualityAuditReasonCodeCount, ...]:
    if not isinstance(value, tuple):
        raise TypeError(f"{field_name} must be a tuple")
    for item in value:
        if type(item) is not ResearchTeamMemoryQualityAuditReasonCodeCount:
            raise ValueError(
                f"{field_name} must contain ResearchTeamMemoryQualityAuditReasonCodeCount",
            )
    return value


def _require_public_string(field_name: str, value: str) -> str:
    if type(value) is not str:
        raise TypeError(f"{field_name} must be exactly str")
    if not value or value != value.strip() or any(char.isspace() for char in value):
        raise ValueError(f"{field_name} must be canonical")
    lowered = value.lower()
    if any(fragment in lowered for fragment in _UNSAFE_PUBLIC_FRAGMENTS):
        raise ValueError(f"{field_name} must be public")
    return value


def _require_public_sentence(field_name: str, value: str) -> str:
    if type(value) is not str:
        raise TypeError(f"{field_name} must be exactly str")
    lowered = value.lower()
    if any(fragment in lowered for fragment in _UNSAFE_PUBLIC_FRAGMENTS):
        raise ValueError(f"{field_name} must be public")
    return value


def _require_public_status(field_name: str, value: str) -> str:
    _require_public_string(field_name, value)
    if value not in (STATUS_PASS, STATUS_WATCH, STATUS_BLOCK):
        raise ValueError(f"{field_name} must be pass, watch, or block")
    return value


def _require_reason_code(field_name: str, value: str) -> str:
    _require_public_string(field_name, value)
    if value not in REASON_CODE_SEQUENCE:
        raise ValueError(f"{field_name} must be a known reason_code")
    return value


def _normalize_reason_codes(field_name: str, value: tuple[str, ...]) -> tuple[str, ...]:
    if not isinstance(value, tuple):
        raise TypeError(f"{field_name} must be a tuple")
    if not value:
        raise ValueError(f"{field_name} must not be empty")
    unique_values = frozenset(value)
    if len(unique_values) != len(value):
        raise ValueError(f"{field_name} contains duplicate reason_code values")
    for reason_code in value:
        _require_reason_code(field_name, reason_code)
    reason_sequence = (
        REASON_CODE_SEQUENCE if NO_INPUTS_REASON in value else ROW_REASON_CODE_SEQUENCE
    )
    return tuple(
        reason_code for reason_code in reason_sequence if reason_code in unique_values
    )


def _require_hard_flags(field_name: str, value: object) -> None:
    for flag_name in ("paper_only", "report_only", "readonly"):
        if getattr(value, flag_name) is not True:
            raise ValueError(f"{field_name} must keep {flag_name}=True")


def _require_or_set_digest(report: ResearchTeamMemoryQualityAuditReport) -> None:
    if type(report.derived_validation_digest) is not str:
        raise TypeError("derived_validation_digest must be exactly str")
    expected = _report_payload_digest(report)
    if report.derived_validation_digest == "":
        object.__setattr__(report, "derived_validation_digest", expected)
        return
    if report.derived_validation_digest != expected:
        raise ValueError("derived_validation_digest must match public payload")


def _report_payload_digest(report: ResearchTeamMemoryQualityAuditReport) -> str:
    payload = _payload_value(report)
    if not isinstance(payload, dict):
        raise ValueError("report payload must be a JSON object")
    payload.pop("derived_validation_digest", None)
    return _canonical_digest(payload)


def _verify_public_digest(payload: dict[str, Any]) -> None:
    digest = payload.get("derived_validation_digest")
    if type(digest) is not str:
        raise TypeError("derived_validation_digest must be exactly str")
    unsigned_payload = dict(payload)
    unsigned_payload.pop("derived_validation_digest", None)
    if digest != _canonical_digest(unsigned_payload):
        raise ValueError("derived_validation_digest must match public payload")


def _canonical_digest(payload: dict[str, Any]) -> str:
    encoded = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")
    return sha256(encoded).hexdigest()


def _as_utc(field_name: str, value: datetime) -> datetime:
    if type(value) is not datetime:
        raise TypeError(f"{field_name} must be exactly datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be UTC-aware")
    if value.microsecond != 0:
        raise ValueError(f"{field_name} must be a whole second")
    return value.astimezone(UTC)


def _require_decimal(field_name: str, value: Decimal) -> Decimal:
    if type(value) is not Decimal:
        raise TypeError(f"{field_name} must be exactly Decimal")
    return _quantize(value)


def _require_nonnegative_decimal(field_name: str, value: Decimal) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return decimal_value


def _require_nonnegative_whole_decimal(field_name: str, value: Decimal) -> Decimal:
    decimal_value = _require_nonnegative_decimal(field_name, value)
    if decimal_value != decimal_value.to_integral_value():
        raise ValueError(f"{field_name} must be whole")
    return decimal_value


def _require_ratio_decimal(field_name: str, value: Decimal) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value < ZERO or decimal_value > ONE:
        raise ValueError(f"{field_name} must be in the unit interval")
    return decimal_value


def _positive_gap(left: Decimal, right: Decimal) -> Decimal:
    gap = left - right
    if gap < ZERO:
        return ZERO
    return _quantize(gap)


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO:
        return ZERO
    return _quantize(numerator / denominator)


def _average(values: object) -> Decimal:
    items = tuple(values)
    if not items:
        return ZERO
    return _ratio(_sum_decimal(items), _count_decimal(items))


def _count_decimal(values: tuple[object, ...]) -> Decimal:
    return _quantize(Decimal(len(values)))


def _sum_decimal(values: tuple[Decimal, ...]) -> Decimal:
    total = ZERO
    for value in values:
        total += value
    return _quantize(total)


def _sum_if(
    rows: tuple[ResearchTeamMemoryQualityAuditRow, ...],
    predicate: object,
) -> Decimal:
    return _quantize(sum((ONE for row in rows if predicate(row)), ZERO))


def _quantize(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(QUANT)


def _payload_value(value: object) -> object:
    if is_dataclass(value) and not isinstance(value, type):
        return {
            field.name: _payload_value(getattr(value, field.name))
            for field in fields(value)
        }
    if isinstance(value, tuple):
        return [_payload_value(item) for item in value]
    if type(value) is Decimal:
        return str(value)
    if type(value) is datetime:
        return value.astimezone(UTC).isoformat().replace("+00:00", "Z")
    return value
