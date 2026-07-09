"""Pure aggregate report for cross-specialist error memory pressure."""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable, Mapping
from dataclasses import asdict, dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
import json
import re
from typing import Any


DEFAULT_RESEARCH_TEAM_CROSS_SPECIALIST_ERROR_MEMORY_REPORT_CONFIG_VERSION = (
    "research-team-cross-specialist-error-memory-report-v1"
)
CROSS_SPECIALIST_ERROR_MEMORY_REPORT_STATUSES = ("pass", "watch", "block")

QUANTUM = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
PUBLIC_LABEL_RE = re.compile(r"^[a-z0-9][a-z0-9_.-]{0,127}$")
HEX_CHARS = frozenset("0123456789abcdef")

SHARED_BLOCK_REASON = "cross_specialist_shared_error_count_block"
UNRESOLVED_BLOCK_REASON = "cross_specialist_unresolved_repeat_count_block"
OVERLAP_BLOCK_REASON = "cross_specialist_overlap_ratio_block"
AGREEMENT_BLOCK_REASON = "cross_specialist_agreement_gap_block"
MEMORY_AGE_BLOCK_REASON = "cross_specialist_memory_age_block"
PLAYBOOK_BLOCK_REASON = "cross_specialist_playbook_coverage_block"
SHARED_WATCH_REASON = "cross_specialist_shared_error_count_watch"
UNRESOLVED_WATCH_REASON = "cross_specialist_unresolved_repeat_count_watch"
OVERLAP_WATCH_REASON = "cross_specialist_overlap_ratio_watch"
AGREEMENT_WATCH_REASON = "cross_specialist_agreement_gap_watch"
MEMORY_AGE_WATCH_REASON = "cross_specialist_memory_age_watch"
PLAYBOOK_WATCH_REASON = "cross_specialist_playbook_coverage_watch"
CLEAR_REASON = "cross_specialist_error_memory_clear"
EMPTY_REASON = "cross_specialist_error_memory_empty"

REASON_SEQUENCE = (
    SHARED_BLOCK_REASON,
    UNRESOLVED_BLOCK_REASON,
    OVERLAP_BLOCK_REASON,
    AGREEMENT_BLOCK_REASON,
    MEMORY_AGE_BLOCK_REASON,
    PLAYBOOK_BLOCK_REASON,
    SHARED_WATCH_REASON,
    UNRESOLVED_WATCH_REASON,
    OVERLAP_WATCH_REASON,
    AGREEMENT_WATCH_REASON,
    MEMORY_AGE_WATCH_REASON,
    PLAYBOOK_WATCH_REASON,
    CLEAR_REASON,
)
REASON_RANK = {reason_code: index for index, reason_code in enumerate(REASON_SEQUENCE)}
PAPER_REVIEW_URGENCY_BY_STATUS = {
    "pass": "paper_cross_specialist_memory_monitor",
    "watch": "paper_cross_specialist_memory_watch",
    "block": "paper_cross_specialist_memory_block",
}
STATUS_RANK = {"block": 0, "watch": 1, "pass": 2}

PUBLIC_LABEL_BLOCK_FRAGMENTS = (
    "http",
    "url",
    "://",
    "@",
    "dsn",
    "source",
    "private",
    "secret",
    "token",
    "table",
    "wallet",
    "order",
    "trade",
)
UNSAFE_PUBLIC_FRAGMENTS = (
    "candidate",
    "market",
    "slug",
    "question",
    "source_url",
    "source_text",
    "source",
    "url",
    "dsn",
    "table",
    "token",
    "secret",
    "private",
    "credential",
    "auth",
    "wallet",
    "order",
    "trade",
    "trading",
    "live_trading",
    "recommend",
    "sizing",
    "size",
    "route",
    "routing",
    "execute",
    "execution",
    "position",
    "stake",
    "bet",
    "place",
    "://",
    "raw",
)
UNSAFE_PUBLIC_KEY_FRAGMENTS = UNSAFE_PUBLIC_FRAGMENTS + (
    "db",
    "database",
    "network",
    "recommendation",
    "sizing",
    "size",
    "route",
    "routing",
    "execute",
    "execution",
    "position",
    "stake",
    "bet",
    "place",
)

__all__ = (
    "DEFAULT_RESEARCH_TEAM_CROSS_SPECIALIST_ERROR_MEMORY_REPORT_CONFIG_VERSION",
    "CROSS_SPECIALIST_ERROR_MEMORY_REPORT_STATUSES",
    "ResearchTeamCrossSpecialistErrorMemoryConfig",
    "ResearchTeamCrossSpecialistErrorMemoryInput",
    "ResearchTeamCrossSpecialistErrorMemoryReasonCodeCount",
    "ResearchTeamCrossSpecialistErrorMemoryReport",
    "ResearchTeamCrossSpecialistErrorMemoryRow",
    "build_research_team_cross_specialist_error_memory_report",
    "research_team_cross_specialist_error_memory_report_digest",
    "research_team_cross_specialist_error_memory_report_payload",
)


class _FinalDataclass:
    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        for base in cls.__bases__:
            if base is not _FinalDataclass and issubclass(base, _FinalDataclass):
                raise TypeError(f"{base.__name__} subclass is not allowed")


@dataclass(frozen=True)
class ResearchTeamCrossSpecialistErrorMemoryConfig(_FinalDataclass):
    config_version: str = (
        DEFAULT_RESEARCH_TEAM_CROSS_SPECIALIST_ERROR_MEMORY_REPORT_CONFIG_VERSION
    )
    max_pass_shared_error_count: Decimal = Decimal("0.000000")
    max_watch_shared_error_count: Decimal = Decimal("3.000000")
    max_pass_unresolved_repeat_count: Decimal = Decimal("0.000000")
    max_watch_unresolved_repeat_count: Decimal = Decimal("2.000000")
    max_pass_cross_specialist_overlap_ratio: Decimal = Decimal("0.250000")
    max_watch_cross_specialist_overlap_ratio: Decimal = Decimal("0.600000")
    max_pass_specialist_agreement_gap_score: Decimal = Decimal("0.250000")
    max_watch_specialist_agreement_gap_score: Decimal = Decimal("0.600000")
    max_pass_memory_age_seconds: Decimal = Decimal("86400.000000")
    max_watch_memory_age_seconds: Decimal = Decimal("604800.000000")
    min_pass_corrective_playbook_coverage_ratio: Decimal = Decimal("0.800000")
    min_watch_corrective_playbook_coverage_ratio: Decimal = Decimal("0.500000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchTeamCrossSpecialistErrorMemoryConfig, "config")
        _require_public_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_TEAM_CROSS_SPECIALIST_ERROR_MEMORY_REPORT_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "max_pass_shared_error_count",
            "max_watch_shared_error_count",
            "max_pass_unresolved_repeat_count",
            "max_watch_unresolved_repeat_count",
            "max_pass_memory_age_seconds",
            "max_watch_memory_age_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_count_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "max_pass_cross_specialist_overlap_ratio",
            "max_watch_cross_specialist_overlap_ratio",
            "max_pass_specialist_agreement_gap_score",
            "max_watch_specialist_agreement_gap_score",
            "min_pass_corrective_playbook_coverage_ratio",
            "min_watch_corrective_playbook_coverage_ratio",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        _validate_config_thresholds(self)
        _require_hard_flags("config", self)
        _reject_unsafe_public_payload("config", self)


@dataclass(frozen=True)
class ResearchTeamCrossSpecialistErrorMemoryInput(_FinalDataclass):
    team_label: str
    primary_specialist_label: str
    comparison_specialist_label: str
    error_pattern_label: str
    shared_error_count: Decimal
    unresolved_repeat_count: Decimal
    cross_specialist_overlap_ratio: Decimal
    specialist_agreement_gap_score: Decimal
    memory_age_seconds: Decimal
    corrective_playbook_coverage_ratio: Decimal
    observed_at: datetime
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchTeamCrossSpecialistErrorMemoryInput, "input")
        for field_name in (
            "team_label",
            "primary_specialist_label",
            "comparison_specialist_label",
            "error_pattern_label",
        ):
            _require_public_label(field_name, getattr(self, field_name))
        if self.primary_specialist_label == self.comparison_specialist_label:
            raise ValueError("specialist labels must differ")
        for field_name in (
            "shared_error_count",
            "unresolved_repeat_count",
            "memory_age_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_count_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "cross_specialist_overlap_ratio",
            "specialist_agreement_gap_score",
            "corrective_playbook_coverage_ratio",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        _require_hard_flags("input", self)
        _reject_unsafe_public_payload("input", self)


@dataclass(frozen=True)
class ResearchTeamCrossSpecialistErrorMemoryRow(_FinalDataclass):
    memory_rank: Decimal
    team_label: str
    primary_specialist_label: str
    comparison_specialist_label: str
    error_pattern_label: str
    status: str
    error_memory_pressure_score: Decimal
    shared_error_count: Decimal
    unresolved_repeat_count: Decimal
    cross_specialist_overlap_ratio: Decimal
    specialist_agreement_gap_score: Decimal
    memory_age_seconds: Decimal
    corrective_playbook_coverage_ratio: Decimal
    observed_at: datetime
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchTeamCrossSpecialistErrorMemoryRow, "row")
        object.__setattr__(
            self,
            "memory_rank",
            _require_count_decimal("memory_rank", self.memory_rank),
        )
        for field_name in (
            "team_label",
            "primary_specialist_label",
            "comparison_specialist_label",
            "error_pattern_label",
        ):
            _require_public_label(field_name, getattr(self, field_name))
        if self.primary_specialist_label == self.comparison_specialist_label:
            raise ValueError("specialist labels must differ")
        _require_status("status", self.status)
        for field_name in (
            "shared_error_count",
            "unresolved_repeat_count",
            "memory_age_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_count_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "error_memory_pressure_score",
            "cross_specialist_overlap_ratio",
            "specialist_agreement_gap_score",
            "corrective_playbook_coverage_ratio",
        ):
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
        if self.status != _status_from_reason_codes(self.reason_codes):
            raise ValueError("status must match reason_codes")
        _require_hard_flags("row", self)
        _reject_unsafe_public_payload("row", self)


@dataclass(frozen=True)
class ResearchTeamCrossSpecialistErrorMemoryReasonCodeCount(_FinalDataclass):
    reason_code: str
    count: Decimal
    row_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchTeamCrossSpecialistErrorMemoryReasonCodeCount,
            "reason_code_count",
        )
        _require_reason_code("reason_code", self.reason_code)
        object.__setattr__(self, "count", _require_count_decimal("count", self.count))
        object.__setattr__(
            self,
            "row_ratio",
            _require_ratio_decimal("row_ratio", self.row_ratio),
        )
        if self.count <= ZERO:
            raise ValueError("count must be positive")
        _require_hard_flags("reason_code_count", self)
        _reject_unsafe_public_payload("reason_code_count", self)


@dataclass(frozen=True)
class ResearchTeamCrossSpecialistErrorMemoryReport(_FinalDataclass):
    generated_at: datetime
    config_version: str
    input_count: Decimal
    active_memory_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    active_memory_ratio: Decimal
    total_shared_error_count: Decimal
    total_unresolved_repeat_count: Decimal
    average_cross_specialist_overlap_ratio: Decimal
    average_specialist_agreement_gap_score: Decimal
    min_corrective_playbook_coverage_ratio: Decimal
    max_memory_age_seconds: Decimal
    max_error_memory_pressure_score: Decimal
    status: str
    paper_review_urgency: str
    reason_codes: tuple[str, ...]
    reason_code_counts: tuple[ResearchTeamCrossSpecialistErrorMemoryReasonCodeCount, ...]
    rows: tuple[ResearchTeamCrossSpecialistErrorMemoryRow, ...]
    derived_validation_digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchTeamCrossSpecialistErrorMemoryReport, "report")
        object.__setattr__(
            self,
            "generated_at",
            _as_generated_at_utc("generated_at", self.generated_at),
        )
        _require_public_string("config_version", self.config_version)
        for field_name in (
            "input_count",
            "active_memory_count",
            "pass_count",
            "watch_count",
            "block_count",
            "total_shared_error_count",
            "total_unresolved_repeat_count",
            "max_memory_age_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_count_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "active_memory_ratio",
            "average_cross_specialist_overlap_ratio",
            "average_specialist_agreement_gap_score",
            "min_corrective_playbook_coverage_ratio",
            "max_error_memory_pressure_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        _require_status("status", self.status)
        _require_public_string("paper_review_urgency", self.paper_review_urgency)
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
        _require_sha256("derived_validation_digest", self.derived_validation_digest)
        _require_hard_flags("report", self)
        _validate_report(self)
        _reject_unsafe_public_payload("report", self)
        expected_digest = _digest_from_values(_report_values_without_digest(self))
        if self.derived_validation_digest != expected_digest:
            raise ValueError("derived_validation_digest does not match report payload")


def build_research_team_cross_specialist_error_memory_report(
    inputs: Iterable[ResearchTeamCrossSpecialistErrorMemoryInput],
    *,
    config: ResearchTeamCrossSpecialistErrorMemoryConfig,
    generated_at: datetime,
) -> ResearchTeamCrossSpecialistErrorMemoryReport:
    _require_exact_type(config, ResearchTeamCrossSpecialistErrorMemoryConfig, "config")
    _require_hard_flags("config", config)
    generated_at_utc = _as_generated_at_utc("generated_at", generated_at)
    input_rows = _normalize_inputs(inputs)
    base_rows = tuple(_row_from_input(item, config) for item in input_rows)
    rows = tuple(
        _with_rank(row, rank)
        for rank, row in enumerate(sorted(base_rows, key=_row_sort_key), start=1)
    )
    status = _report_status(rows)
    active_count = _count(sum(1 for row in rows if row.status in ("watch", "block")))
    values: dict[str, object] = {
        "generated_at": generated_at_utc,
        "config_version": config.config_version,
        "input_count": _count(len(rows)),
        "active_memory_count": active_count,
        "pass_count": _status_count(rows, "pass"),
        "watch_count": _status_count(rows, "watch"),
        "block_count": _status_count(rows, "block"),
        "active_memory_ratio": _ratio(active_count, _count(len(rows))),
        "total_shared_error_count": _sum_row_decimal(rows, "shared_error_count"),
        "total_unresolved_repeat_count": _sum_row_decimal(
            rows,
            "unresolved_repeat_count",
        ),
        "average_cross_specialist_overlap_ratio": _average_decimal(
            tuple(row.cross_specialist_overlap_ratio for row in rows),
        ),
        "average_specialist_agreement_gap_score": _average_decimal(
            tuple(row.specialist_agreement_gap_score for row in rows),
        ),
        "min_corrective_playbook_coverage_ratio": _min_decimal(
            tuple(row.corrective_playbook_coverage_ratio for row in rows),
        ),
        "max_memory_age_seconds": _max_decimal(
            tuple(row.memory_age_seconds for row in rows),
        ),
        "max_error_memory_pressure_score": _max_decimal(
            tuple(row.error_memory_pressure_score for row in rows),
        ),
        "status": status,
        "paper_review_urgency": PAPER_REVIEW_URGENCY_BY_STATUS[status],
        "reason_codes": _report_reason_codes(rows),
        "reason_code_counts": _reason_code_counts(rows),
        "rows": rows,
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    return ResearchTeamCrossSpecialistErrorMemoryReport(
        **values,
        derived_validation_digest=_digest_from_values(values),
    )


def research_team_cross_specialist_error_memory_report_payload(
    report: ResearchTeamCrossSpecialistErrorMemoryReport | Mapping[str, object],
) -> dict[str, object]:
    if type(report) is ResearchTeamCrossSpecialistErrorMemoryReport:
        _require_hard_flags("report", report)
        payload = _json_ready(asdict(report))
    elif isinstance(report, Mapping):
        payload = _json_ready(report)
    else:
        raise ValueError("report must be a ResearchTeamCrossSpecialistErrorMemoryReport")
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    _require_hard_flags("report payload", _MappingFlags(payload))
    _reject_unsafe_public_payload("report payload", payload, allow_json_containers=True)
    expected_digest = _digest_from_payload(payload)
    if payload.get("derived_validation_digest") != expected_digest:
        raise ValueError("derived_validation_digest does not match report payload")
    return payload


def research_team_cross_specialist_error_memory_report_digest(
    report: ResearchTeamCrossSpecialistErrorMemoryReport | Mapping[str, object],
) -> str:
    payload = research_team_cross_specialist_error_memory_report_payload(report)
    digest = payload["derived_validation_digest"]
    if type(digest) is not str:
        raise ValueError("derived_validation_digest must be a string")
    return digest


@dataclass(frozen=True)
class _MappingFlags:
    value: Mapping[str, object]

    @property
    def paper_only(self) -> object:
        return self.value.get("paper_only")

    @property
    def report_only(self) -> object:
        return self.value.get("report_only")

    @property
    def readonly(self) -> object:
        return self.value.get("readonly")


def _row_from_input(
    item: ResearchTeamCrossSpecialistErrorMemoryInput,
    config: ResearchTeamCrossSpecialistErrorMemoryConfig,
) -> ResearchTeamCrossSpecialistErrorMemoryRow:
    reason_codes = _row_reason_codes(item=item, config=config)
    return ResearchTeamCrossSpecialistErrorMemoryRow(
        memory_rank=ONE,
        team_label=item.team_label,
        primary_specialist_label=item.primary_specialist_label,
        comparison_specialist_label=item.comparison_specialist_label,
        error_pattern_label=item.error_pattern_label,
        status=_status_from_reason_codes(reason_codes),
        error_memory_pressure_score=_error_memory_pressure_score(
            item=item,
            config=config,
        ),
        shared_error_count=item.shared_error_count,
        unresolved_repeat_count=item.unresolved_repeat_count,
        cross_specialist_overlap_ratio=item.cross_specialist_overlap_ratio,
        specialist_agreement_gap_score=item.specialist_agreement_gap_score,
        memory_age_seconds=item.memory_age_seconds,
        corrective_playbook_coverage_ratio=item.corrective_playbook_coverage_ratio,
        observed_at=item.observed_at,
        reason_codes=reason_codes,
    )


def _with_rank(
    row: ResearchTeamCrossSpecialistErrorMemoryRow,
    rank: int,
) -> ResearchTeamCrossSpecialistErrorMemoryRow:
    return ResearchTeamCrossSpecialistErrorMemoryRow(
        memory_rank=_count(rank),
        team_label=row.team_label,
        primary_specialist_label=row.primary_specialist_label,
        comparison_specialist_label=row.comparison_specialist_label,
        error_pattern_label=row.error_pattern_label,
        status=row.status,
        error_memory_pressure_score=row.error_memory_pressure_score,
        shared_error_count=row.shared_error_count,
        unresolved_repeat_count=row.unresolved_repeat_count,
        cross_specialist_overlap_ratio=row.cross_specialist_overlap_ratio,
        specialist_agreement_gap_score=row.specialist_agreement_gap_score,
        memory_age_seconds=row.memory_age_seconds,
        corrective_playbook_coverage_ratio=row.corrective_playbook_coverage_ratio,
        observed_at=row.observed_at,
        reason_codes=row.reason_codes,
    )


def _row_reason_codes(
    *,
    item: ResearchTeamCrossSpecialistErrorMemoryInput,
    config: ResearchTeamCrossSpecialistErrorMemoryConfig,
) -> tuple[str, ...]:
    reasons: list[str] = []
    _append_high_threshold_reason(
        reasons,
        metric=item.shared_error_count,
        watch=config.max_pass_shared_error_count,
        block=config.max_watch_shared_error_count,
        watch_code=SHARED_WATCH_REASON,
        block_code=SHARED_BLOCK_REASON,
    )
    _append_high_threshold_reason(
        reasons,
        metric=item.unresolved_repeat_count,
        watch=config.max_pass_unresolved_repeat_count,
        block=config.max_watch_unresolved_repeat_count,
        watch_code=UNRESOLVED_WATCH_REASON,
        block_code=UNRESOLVED_BLOCK_REASON,
    )
    _append_high_threshold_reason(
        reasons,
        metric=item.cross_specialist_overlap_ratio,
        watch=config.max_pass_cross_specialist_overlap_ratio,
        block=config.max_watch_cross_specialist_overlap_ratio,
        watch_code=OVERLAP_WATCH_REASON,
        block_code=OVERLAP_BLOCK_REASON,
    )
    _append_high_threshold_reason(
        reasons,
        metric=item.specialist_agreement_gap_score,
        watch=config.max_pass_specialist_agreement_gap_score,
        block=config.max_watch_specialist_agreement_gap_score,
        watch_code=AGREEMENT_WATCH_REASON,
        block_code=AGREEMENT_BLOCK_REASON,
    )
    _append_high_threshold_reason(
        reasons,
        metric=item.memory_age_seconds,
        watch=config.max_pass_memory_age_seconds,
        block=config.max_watch_memory_age_seconds,
        watch_code=MEMORY_AGE_WATCH_REASON,
        block_code=MEMORY_AGE_BLOCK_REASON,
    )
    _append_low_threshold_reason(
        reasons,
        metric=item.corrective_playbook_coverage_ratio,
        watch=config.min_pass_corrective_playbook_coverage_ratio,
        block=config.min_watch_corrective_playbook_coverage_ratio,
        watch_code=PLAYBOOK_WATCH_REASON,
        block_code=PLAYBOOK_BLOCK_REASON,
    )
    if not reasons:
        reasons.append(CLEAR_REASON)
    return tuple(reason for reason in REASON_SEQUENCE if reason in set(reasons))


def _append_high_threshold_reason(
    reasons: list[str],
    *,
    metric: Decimal,
    watch: Decimal,
    block: Decimal,
    watch_code: str,
    block_code: str,
) -> None:
    if metric > block:
        reasons.append(block_code)
    elif metric > watch:
        reasons.append(watch_code)


def _append_low_threshold_reason(
    reasons: list[str],
    *,
    metric: Decimal,
    watch: Decimal,
    block: Decimal,
    watch_code: str,
    block_code: str,
) -> None:
    if metric < block:
        reasons.append(block_code)
    elif metric < watch:
        reasons.append(watch_code)


def _status_from_reason_codes(reason_codes: tuple[str, ...]) -> str:
    if any(reason.endswith("_block") for reason in reason_codes):
        return "block"
    if any(reason.endswith("_watch") for reason in reason_codes):
        return "watch"
    return "pass"


def _error_memory_pressure_score(
    *,
    item: ResearchTeamCrossSpecialistErrorMemoryInput,
    config: ResearchTeamCrossSpecialistErrorMemoryConfig,
) -> Decimal:
    return _max_decimal(
        (
            _high_threshold_pressure(
                item.shared_error_count,
                config.max_pass_shared_error_count,
                config.max_watch_shared_error_count,
            ),
            _high_threshold_pressure(
                item.unresolved_repeat_count,
                config.max_pass_unresolved_repeat_count,
                config.max_watch_unresolved_repeat_count,
            ),
            _high_threshold_pressure(
                item.cross_specialist_overlap_ratio,
                config.max_pass_cross_specialist_overlap_ratio,
                config.max_watch_cross_specialist_overlap_ratio,
            ),
            _high_threshold_pressure(
                item.specialist_agreement_gap_score,
                config.max_pass_specialist_agreement_gap_score,
                config.max_watch_specialist_agreement_gap_score,
            ),
            _high_threshold_pressure(
                item.memory_age_seconds,
                config.max_pass_memory_age_seconds,
                config.max_watch_memory_age_seconds,
            ),
            _low_threshold_pressure(
                item.corrective_playbook_coverage_ratio,
                config.min_pass_corrective_playbook_coverage_ratio,
                config.min_watch_corrective_playbook_coverage_ratio,
            ),
        ),
    )


def _high_threshold_pressure(value: Decimal, pass_limit: Decimal, block_limit: Decimal) -> Decimal:
    if value <= pass_limit:
        return ZERO
    if block_limit == pass_limit:
        return ONE
    return _clamp_ratio((value - pass_limit) / (block_limit - pass_limit))


def _low_threshold_pressure(value: Decimal, pass_floor: Decimal, block_floor: Decimal) -> Decimal:
    if value >= pass_floor:
        return ZERO
    if pass_floor == block_floor:
        return ONE
    return _clamp_ratio((pass_floor - value) / (pass_floor - block_floor))


def _normalize_inputs(
    inputs: Iterable[ResearchTeamCrossSpecialistErrorMemoryInput],
) -> tuple[ResearchTeamCrossSpecialistErrorMemoryInput, ...]:
    if isinstance(inputs, (str, bytes)):
        raise ValueError("inputs must be an iterable of cross specialist inputs")
    normalized: list[ResearchTeamCrossSpecialistErrorMemoryInput] = []
    seen_keys: set[tuple[str, str, str, str]] = set()
    for item in inputs:
        _require_exact_type(item, ResearchTeamCrossSpecialistErrorMemoryInput, "input")
        _require_hard_flags("input", item)
        key = (
            item.team_label,
            item.primary_specialist_label,
            item.comparison_specialist_label,
            item.error_pattern_label,
        )
        if key in seen_keys:
            raise ValueError("cross specialist labels must be unique")
        seen_keys.add(key)
        normalized.append(item)
    return tuple(
        sorted(
            normalized,
            key=lambda item: (
                item.team_label,
                item.primary_specialist_label,
                item.comparison_specialist_label,
                item.error_pattern_label,
                item.observed_at,
            ),
        ),
    )


def _require_rows(
    rows: tuple[ResearchTeamCrossSpecialistErrorMemoryRow, ...],
) -> tuple[ResearchTeamCrossSpecialistErrorMemoryRow, ...]:
    if not isinstance(rows, tuple):
        raise ValueError("rows must be a tuple")
    for row in rows:
        _require_exact_type(row, ResearchTeamCrossSpecialistErrorMemoryRow, "row")
        _require_hard_flags("row", row)
    return tuple(sorted(rows, key=lambda row: row.memory_rank))


def _require_reason_code_counts(
    counts: tuple[ResearchTeamCrossSpecialistErrorMemoryReasonCodeCount, ...],
) -> tuple[ResearchTeamCrossSpecialistErrorMemoryReasonCodeCount, ...]:
    if not isinstance(counts, tuple):
        raise ValueError("reason_code_counts must be a tuple")
    for count in counts:
        _require_exact_type(
            count,
            ResearchTeamCrossSpecialistErrorMemoryReasonCodeCount,
            "reason_code_count",
        )
        _require_hard_flags("reason_code_count", count)
    return tuple(sorted(counts, key=lambda item: REASON_RANK[item.reason_code]))


def _row_sort_key(row: ResearchTeamCrossSpecialistErrorMemoryRow) -> tuple[object, ...]:
    return (
        STATUS_RANK[row.status],
        -row.error_memory_pressure_score,
        -row.shared_error_count,
        -row.unresolved_repeat_count,
        row.team_label,
        row.primary_specialist_label,
        row.comparison_specialist_label,
        row.error_pattern_label,
    )


def _status_count(
    rows: tuple[ResearchTeamCrossSpecialistErrorMemoryRow, ...],
    status: str,
) -> Decimal:
    return _count(sum(1 for row in rows if row.status == status))


def _report_status(rows: tuple[ResearchTeamCrossSpecialistErrorMemoryRow, ...]) -> str:
    if any(row.status == "block" for row in rows):
        return "block"
    if any(row.status == "watch" for row in rows):
        return "watch"
    return "pass"


def _report_reason_codes(
    rows: tuple[ResearchTeamCrossSpecialistErrorMemoryRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return (EMPTY_REASON,)
    observed = {reason_code for row in rows for reason_code in row.reason_codes}
    return tuple(reason_code for reason_code in REASON_SEQUENCE if reason_code in observed)


def _reason_code_counts(
    rows: tuple[ResearchTeamCrossSpecialistErrorMemoryRow, ...],
) -> tuple[ResearchTeamCrossSpecialistErrorMemoryReasonCodeCount, ...]:
    if not rows:
        return ()
    row_count = _count(len(rows))
    counts = Counter(reason_code for row in rows for reason_code in row.reason_codes)
    return tuple(
        ResearchTeamCrossSpecialistErrorMemoryReasonCodeCount(
            reason_code=reason_code,
            count=_count(counts[reason_code]),
            row_ratio=_ratio(_count(counts[reason_code]), row_count),
        )
        for reason_code in REASON_SEQUENCE
        if counts[reason_code] > 0
    )


def _sum_row_decimal(
    rows: tuple[ResearchTeamCrossSpecialistErrorMemoryRow, ...],
    field_name: str,
) -> Decimal:
    return _quantize(sum((getattr(row, field_name) for row in rows), ZERO))


def _average_decimal(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return ZERO
    return _quantize(sum(values, ZERO) / _count(len(values)))


def _min_decimal(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return ZERO
    return _quantize(min(values))


def _max_decimal(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return ZERO
    return _quantize(max(values))


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO:
        return ZERO
    return _clamp_ratio(numerator / denominator)


def _clamp_ratio(value: Decimal) -> Decimal:
    normalized = _quantize(value)
    if normalized < ZERO:
        return ZERO
    if normalized > ONE:
        return ONE
    return normalized


def _count(value: int) -> Decimal:
    if type(value) is not int or value < 0:
        raise ValueError("count source must be a nonnegative integer")
    return _quantize(Decimal(value))


def _require_count_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _require_ratio_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < ZERO or normalized > ONE:
        raise ValueError(f"{field_name} must be between zero and one")
    return normalized


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return _quantize(value)


def _quantize(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(QUANTUM)


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be UTC-aware")
    return value.astimezone(UTC)


def _as_generated_at_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() != ZERO_TIMEDELTA:
        raise ValueError(f"{field_name} must be UTC")
    return value.astimezone(UTC)


ZERO_TIMEDELTA = datetime(2000, 1, 1, tzinfo=UTC).utcoffset()


def _require_status(field_name: str, value: object) -> str:
    if type(value) is not str or value not in CROSS_SPECIALIST_ERROR_MEMORY_REPORT_STATUSES:
        raise ValueError(f"{field_name} must be pass, watch, or block")
    return value


def _require_reason_code(field_name: str, value: object, *, allow_empty: bool = False) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if value == EMPTY_REASON and allow_empty:
        return value
    if value not in REASON_RANK:
        raise ValueError(f"{field_name} must be a supported reason code")
    return value


def _require_reason_codes(
    reason_codes: tuple[str, ...],
    *,
    require_nonempty: bool,
) -> tuple[str, ...]:
    if not isinstance(reason_codes, tuple):
        raise ValueError("reason_codes must be a tuple")
    if require_nonempty and not reason_codes:
        raise ValueError("reason_codes must be nonempty")
    for reason_code in reason_codes:
        _require_reason_code("reason_code", reason_code)
    return tuple(reason for reason in REASON_SEQUENCE if reason in set(reason_codes))


def _require_report_reason_codes(reason_codes: tuple[str, ...]) -> tuple[str, ...]:
    if not isinstance(reason_codes, tuple) or not reason_codes:
        raise ValueError("reason_codes must be a nonempty tuple")
    for reason_code in reason_codes:
        _require_reason_code("reason_code", reason_code, allow_empty=True)
    if EMPTY_REASON in reason_codes and len(reason_codes) != 1:
        raise ValueError("empty reason code must stand alone")
    return (
        (EMPTY_REASON,)
        if reason_codes == (EMPTY_REASON,)
        else tuple(reason for reason in REASON_SEQUENCE if reason in set(reason_codes))
    )


def _require_sha256(field_name: str, value: object) -> str:
    if type(value) is not str or len(value) != 64 or any(ch not in HEX_CHARS for ch in value):
        raise ValueError(f"{field_name} must be a lowercase sha256 digest")
    return value


def _require_public_string(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be nonempty public text")
    _reject_unsafe_public_string(field_name, value)
    return value


def _require_public_label(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not PUBLIC_LABEL_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a public aggregate label")
    lowered = value.lower()
    if any(fragment in lowered for fragment in PUBLIC_LABEL_BLOCK_FRAGMENTS):
        raise ValueError(f"{field_name} must be a public aggregate label")
    return value


def _require_exact_type(value: object, expected_type: type[object], label: str) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{label} must be exactly {expected_type.__name__}")


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if getattr(value, field_name) is not True:
            raise ValueError(f"{field_name} must be True for {label}")


def _validate_config_thresholds(
    config: ResearchTeamCrossSpecialistErrorMemoryConfig,
) -> None:
    for pass_field, watch_field in (
        ("max_pass_shared_error_count", "max_watch_shared_error_count"),
        ("max_pass_unresolved_repeat_count", "max_watch_unresolved_repeat_count"),
        (
            "max_pass_cross_specialist_overlap_ratio",
            "max_watch_cross_specialist_overlap_ratio",
        ),
        (
            "max_pass_specialist_agreement_gap_score",
            "max_watch_specialist_agreement_gap_score",
        ),
        ("max_pass_memory_age_seconds", "max_watch_memory_age_seconds"),
    ):
        if getattr(config, pass_field) > getattr(config, watch_field):
            raise ValueError(f"{watch_field} must be at least {pass_field}")
    if (
        config.min_watch_corrective_playbook_coverage_ratio
        > config.min_pass_corrective_playbook_coverage_ratio
    ):
        raise ValueError(
            "min_watch_corrective_playbook_coverage_ratio must not exceed "
            "min_pass_corrective_playbook_coverage_ratio",
        )


def _validate_report(report: ResearchTeamCrossSpecialistErrorMemoryReport) -> None:
    rows = report.rows
    expected_input_count = _count(len(rows))
    expected_active_count = _count(sum(1 for row in rows if row.status in ("watch", "block")))
    expected_status = _report_status(rows)
    expected_reason_code_counts = _reason_code_counts(rows)
    checks = {
        "input_count": expected_input_count,
        "active_memory_count": expected_active_count,
        "pass_count": _status_count(rows, "pass"),
        "watch_count": _status_count(rows, "watch"),
        "block_count": _status_count(rows, "block"),
        "active_memory_ratio": _ratio(expected_active_count, expected_input_count),
        "total_shared_error_count": _sum_row_decimal(rows, "shared_error_count"),
        "total_unresolved_repeat_count": _sum_row_decimal(rows, "unresolved_repeat_count"),
        "average_cross_specialist_overlap_ratio": _average_decimal(
            tuple(row.cross_specialist_overlap_ratio for row in rows),
        ),
        "average_specialist_agreement_gap_score": _average_decimal(
            tuple(row.specialist_agreement_gap_score for row in rows),
        ),
        "min_corrective_playbook_coverage_ratio": _min_decimal(
            tuple(row.corrective_playbook_coverage_ratio for row in rows),
        ),
        "max_memory_age_seconds": _max_decimal(tuple(row.memory_age_seconds for row in rows)),
        "max_error_memory_pressure_score": _max_decimal(
            tuple(row.error_memory_pressure_score for row in rows),
        ),
    }
    for field_name, expected in checks.items():
        if getattr(report, field_name) != expected:
            raise ValueError(f"{field_name} must match rows")
    if report.status != expected_status:
        raise ValueError("status must match rows")
    if report.paper_review_urgency != PAPER_REVIEW_URGENCY_BY_STATUS[expected_status]:
        raise ValueError("paper_review_urgency must match status")
    if report.reason_codes != _report_reason_codes(rows):
        raise ValueError("reason_codes must match rows")
    if report.reason_code_counts != expected_reason_code_counts:
        raise ValueError("reason_code_counts must match rows")
    for index, row in enumerate(rows, start=1):
        if row.memory_rank != _count(index):
            raise ValueError("row memory_rank must be sequential")


def _report_values_without_digest(
    report: ResearchTeamCrossSpecialistErrorMemoryReport,
) -> dict[str, object]:
    values = asdict(report)
    values.pop("derived_validation_digest", None)
    return values


def _digest_from_payload(payload: Mapping[str, object]) -> str:
    unsigned = dict(payload)
    unsigned.pop("derived_validation_digest", None)
    return _digest_from_values(unsigned)


def _digest_from_values(values: Mapping[str, object]) -> str:
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
    return sha256(canonical.encode("utf-8")).hexdigest()


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
    if type(value) is int:
        raise ValueError("numeric payload values must be Decimal strings")
    if isinstance(value, float):
        raise ValueError("numeric payload values must not be float")
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
    if type(value) is Decimal:
        if not value.is_finite():
            raise ValueError(f"{current_path} must be finite")
        return
    if type(value) is datetime or value is None or type(value) is bool:
        return
    if isinstance(value, float):
        raise ValueError(f"{current_path} must not be a float")
    if type(value) is int:
        raise ValueError(f"{current_path} must use Decimal-derived string values")
    raise ValueError(f"{current_path} is not a supported public payload value")


def _reject_unsafe_public_key(key: str, path: str) -> None:
    lowered = key.lower()
    if any(fragment in lowered for fragment in UNSAFE_PUBLIC_KEY_FRAGMENTS):
        raise ValueError(f"{path}.{key} has unsafe public field")


def _reject_unsafe_public_string(field_name: str, value: str) -> None:
    lowered = value.lower()
    if any(fragment in lowered for fragment in UNSAFE_PUBLIC_FRAGMENTS):
        raise ValueError(f"{field_name} has unsafe public value")
