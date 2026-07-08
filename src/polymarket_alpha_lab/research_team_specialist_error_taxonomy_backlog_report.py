"""Pure aggregate report for specialist error taxonomy backlog pressure."""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable, Mapping
from dataclasses import asdict, dataclass, is_dataclass
from datetime import UTC, datetime, timedelta
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
import json
import re
from typing import Any


DEFAULT_RESEARCH_TEAM_SPECIALIST_ERROR_TAXONOMY_BACKLOG_REPORT_CONFIG_VERSION = (
    "research-team-specialist-error-taxonomy-backlog-report-v1"
)
SPECIALIST_ERROR_TAXONOMY_BACKLOG_STATUSES = ("pass", "watch", "block")

QUANTUM = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
PUBLIC_LABEL_RE = re.compile(r"^[a-z0-9][a-z0-9_.-]{0,127}$")
HEX_CHARS = frozenset("0123456789abcdef")

UNRESOLVED_BLOCK_REASON = "specialist_error_taxonomy_unresolved_categories_block"
STALE_BLOCK_REASON = "specialist_error_taxonomy_stale_calibration_feedback_block"
DOMAIN_BLOCK_REASON = "specialist_error_taxonomy_impacted_domain_count_block"
CAPACITY_BLOCK_REASON = "specialist_error_taxonomy_reviewer_capacity_block"
WRITEBACK_BLOCK_REASON = "specialist_error_taxonomy_memory_writeback_lag_block"
ESCALATION_BLOCK_REASON = "specialist_error_taxonomy_manual_escalation_urgency_block"
UNRESOLVED_WATCH_REASON = "specialist_error_taxonomy_unresolved_categories_watch"
STALE_WATCH_REASON = "specialist_error_taxonomy_stale_calibration_feedback_watch"
DOMAIN_WATCH_REASON = "specialist_error_taxonomy_impacted_domain_count_watch"
CAPACITY_WATCH_REASON = "specialist_error_taxonomy_reviewer_capacity_watch"
WRITEBACK_WATCH_REASON = "specialist_error_taxonomy_memory_writeback_lag_watch"
ESCALATION_WATCH_REASON = "specialist_error_taxonomy_manual_escalation_urgency_watch"
CLEAR_REASON = "specialist_error_taxonomy_backlog_clear"
EMPTY_REASON = "specialist_error_taxonomy_backlog_empty"

REASON_SEQUENCE = (
    UNRESOLVED_BLOCK_REASON,
    STALE_BLOCK_REASON,
    DOMAIN_BLOCK_REASON,
    CAPACITY_BLOCK_REASON,
    WRITEBACK_BLOCK_REASON,
    ESCALATION_BLOCK_REASON,
    UNRESOLVED_WATCH_REASON,
    STALE_WATCH_REASON,
    DOMAIN_WATCH_REASON,
    CAPACITY_WATCH_REASON,
    WRITEBACK_WATCH_REASON,
    ESCALATION_WATCH_REASON,
    CLEAR_REASON,
)
REASON_RANK = {reason_code: index for index, reason_code in enumerate(REASON_SEQUENCE)}
MANUAL_ESCALATION_BY_STATUS = {
    "pass": "paper_manual_escalation_monitor",
    "watch": "paper_manual_escalation_watch",
    "block": "paper_manual_escalation_block",
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
)
UNSAFE_PUBLIC_FRAGMENTS = (
    "candidate",
    "market_id",
    "market_slug",
    "slug",
    "question",
    "source_url",
    "source_text",
    "source",
    "dsn",
    "table",
    "token",
    "secret",
    "private",
    "credential",
    "://",
    "raw",
)

__all__ = (
    "DEFAULT_RESEARCH_TEAM_SPECIALIST_ERROR_TAXONOMY_BACKLOG_REPORT_CONFIG_VERSION",
    "SPECIALIST_ERROR_TAXONOMY_BACKLOG_STATUSES",
    "ResearchTeamSpecialistErrorTaxonomyBacklogConfig",
    "ResearchTeamSpecialistErrorTaxonomyBacklogInput",
    "ResearchTeamSpecialistErrorTaxonomyBacklogReasonCodeCount",
    "ResearchTeamSpecialistErrorTaxonomyBacklogReport",
    "ResearchTeamSpecialistErrorTaxonomyBacklogRow",
    "build_research_team_specialist_error_taxonomy_backlog_report",
    "research_team_specialist_error_taxonomy_backlog_report_digest",
    "research_team_specialist_error_taxonomy_backlog_report_payload",
)


class _FinalDataclass:
    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        for base in cls.__bases__:
            if base is not _FinalDataclass and issubclass(base, _FinalDataclass):
                raise TypeError(f"{base.__name__} subclass is not allowed")


@dataclass(frozen=True)
class ResearchTeamSpecialistErrorTaxonomyBacklogConfig(_FinalDataclass):
    config_version: str = (
        DEFAULT_RESEARCH_TEAM_SPECIALIST_ERROR_TAXONOMY_BACKLOG_REPORT_CONFIG_VERSION
    )
    max_pass_unresolved_error_category_count: Decimal = Decimal("0.000000")
    max_watch_unresolved_error_category_count: Decimal = Decimal("3.000000")
    max_pass_stale_calibration_feedback_count: Decimal = Decimal("0.000000")
    max_watch_stale_calibration_feedback_count: Decimal = Decimal("2.000000")
    max_pass_impacted_domain_count: Decimal = Decimal("1.000000")
    max_watch_impacted_domain_count: Decimal = Decimal("3.000000")
    min_pass_available_reviewer_capacity_count: Decimal = Decimal("2.000000")
    min_watch_available_reviewer_capacity_count: Decimal = Decimal("1.000000")
    max_pass_memory_writeback_lag_seconds: Decimal = Decimal("86400.000000")
    max_watch_memory_writeback_lag_seconds: Decimal = Decimal("604800.000000")
    max_pass_manual_escalation_urgency_score: Decimal = Decimal("0.500000")
    max_watch_manual_escalation_urgency_score: Decimal = Decimal("0.800000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchTeamSpecialistErrorTaxonomyBacklogConfig,
            "config",
        )
        _require_public_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_TEAM_SPECIALIST_ERROR_TAXONOMY_BACKLOG_REPORT_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "max_pass_unresolved_error_category_count",
            "max_watch_unresolved_error_category_count",
            "max_pass_stale_calibration_feedback_count",
            "max_watch_stale_calibration_feedback_count",
            "max_pass_impacted_domain_count",
            "max_watch_impacted_domain_count",
            "min_pass_available_reviewer_capacity_count",
            "min_watch_available_reviewer_capacity_count",
            "max_pass_memory_writeback_lag_seconds",
            "max_watch_memory_writeback_lag_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_count_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "max_pass_manual_escalation_urgency_score",
            "max_watch_manual_escalation_urgency_score",
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
class ResearchTeamSpecialistErrorTaxonomyBacklogInput(_FinalDataclass):
    specialist_label: str
    error_category_label: str
    unresolved_error_category_count: Decimal
    stale_calibration_feedback_count: Decimal
    impacted_domain_count: Decimal
    available_reviewer_capacity_count: Decimal
    memory_writeback_lag_seconds: Decimal
    manual_escalation_urgency_score: Decimal
    observed_at: datetime
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchTeamSpecialistErrorTaxonomyBacklogInput,
            "input",
        )
        _require_public_label("specialist_label", self.specialist_label)
        _require_public_label("error_category_label", self.error_category_label)
        for field_name in (
            "unresolved_error_category_count",
            "stale_calibration_feedback_count",
            "impacted_domain_count",
            "available_reviewer_capacity_count",
            "memory_writeback_lag_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_count_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "manual_escalation_urgency_score",
            _require_ratio_decimal(
                "manual_escalation_urgency_score",
                self.manual_escalation_urgency_score,
            ),
        )
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        _require_hard_flags("input", self)
        _reject_unsafe_public_payload("input", self)


@dataclass(frozen=True)
class ResearchTeamSpecialistErrorTaxonomyBacklogRow(_FinalDataclass):
    backlog_rank: Decimal
    specialist_label: str
    error_category_label: str
    status: str
    backlog_pressure_score: Decimal
    unresolved_error_category_count: Decimal
    stale_calibration_feedback_count: Decimal
    impacted_domain_count: Decimal
    available_reviewer_capacity_count: Decimal
    reviewer_capacity_gap_count: Decimal
    reviewer_capacity_gap_ratio: Decimal
    memory_writeback_lag_seconds: Decimal
    manual_escalation_urgency_score: Decimal
    observed_at: datetime
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchTeamSpecialistErrorTaxonomyBacklogRow,
            "row",
        )
        object.__setattr__(self, "backlog_rank", _require_count_decimal("backlog_rank", self.backlog_rank))
        _require_public_label("specialist_label", self.specialist_label)
        _require_public_label("error_category_label", self.error_category_label)
        _require_status("status", self.status)
        for field_name in (
            "unresolved_error_category_count",
            "stale_calibration_feedback_count",
            "impacted_domain_count",
            "available_reviewer_capacity_count",
            "reviewer_capacity_gap_count",
            "memory_writeback_lag_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_count_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "backlog_pressure_score",
            "reviewer_capacity_gap_ratio",
            "manual_escalation_urgency_score",
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
class ResearchTeamSpecialistErrorTaxonomyBacklogReasonCodeCount(_FinalDataclass):
    reason_code: str
    count: Decimal
    row_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchTeamSpecialistErrorTaxonomyBacklogReasonCodeCount,
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
class ResearchTeamSpecialistErrorTaxonomyBacklogReport(_FinalDataclass):
    generated_at: datetime
    config_version: str
    input_count: Decimal
    backlog_item_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    backlog_ratio: Decimal
    total_unresolved_error_category_count: Decimal
    total_stale_calibration_feedback_count: Decimal
    total_impacted_domain_count: Decimal
    total_available_reviewer_capacity_count: Decimal
    min_available_reviewer_capacity_count: Decimal
    max_memory_writeback_lag_seconds: Decimal
    max_manual_escalation_urgency_score: Decimal
    max_backlog_pressure_score: Decimal
    status: str
    manual_escalation_urgency: str
    reason_codes: tuple[str, ...]
    reason_code_counts: tuple[
        ResearchTeamSpecialistErrorTaxonomyBacklogReasonCodeCount,
        ...,
    ]
    rows: tuple[ResearchTeamSpecialistErrorTaxonomyBacklogRow, ...]
    derived_validation_digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchTeamSpecialistErrorTaxonomyBacklogReport,
            "report",
        )
        object.__setattr__(
            self,
            "generated_at",
            _as_generated_at_utc("generated_at", self.generated_at),
        )
        _require_public_string("config_version", self.config_version)
        for field_name in (
            "input_count",
            "backlog_item_count",
            "pass_count",
            "watch_count",
            "block_count",
            "total_unresolved_error_category_count",
            "total_stale_calibration_feedback_count",
            "total_impacted_domain_count",
            "total_available_reviewer_capacity_count",
            "min_available_reviewer_capacity_count",
            "max_memory_writeback_lag_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_count_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "backlog_ratio",
            "max_manual_escalation_urgency_score",
            "max_backlog_pressure_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        _require_status("status", self.status)
        _require_public_string("manual_escalation_urgency", self.manual_escalation_urgency)
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


def build_research_team_specialist_error_taxonomy_backlog_report(
    inputs: Iterable[ResearchTeamSpecialistErrorTaxonomyBacklogInput],
    *,
    config: ResearchTeamSpecialistErrorTaxonomyBacklogConfig,
    generated_at: datetime,
) -> ResearchTeamSpecialistErrorTaxonomyBacklogReport:
    _require_exact_type(
        config,
        ResearchTeamSpecialistErrorTaxonomyBacklogConfig,
        "config",
    )
    _require_hard_flags("config", config)
    generated_at_utc = _as_generated_at_utc("generated_at", generated_at)
    input_rows = _normalize_inputs(inputs)
    base_rows = tuple(_row_from_input(item, config) for item in input_rows)
    rows = tuple(
        _with_rank(row, rank)
        for rank, row in enumerate(sorted(base_rows, key=_row_sort_key), start=1)
    )
    status = _report_status(rows)
    backlog_count = _count(sum(1 for row in rows if row.status in ("watch", "block")))
    values: dict[str, object] = {
        "generated_at": generated_at_utc,
        "config_version": config.config_version,
        "input_count": _count(len(rows)),
        "backlog_item_count": backlog_count,
        "pass_count": _status_count(rows, "pass"),
        "watch_count": _status_count(rows, "watch"),
        "block_count": _status_count(rows, "block"),
        "backlog_ratio": _ratio(backlog_count, _count(len(rows))),
        "total_unresolved_error_category_count": _sum_row_decimal(
            rows,
            "unresolved_error_category_count",
        ),
        "total_stale_calibration_feedback_count": _sum_row_decimal(
            rows,
            "stale_calibration_feedback_count",
        ),
        "total_impacted_domain_count": _sum_row_decimal(rows, "impacted_domain_count"),
        "total_available_reviewer_capacity_count": _sum_row_decimal(
            rows,
            "available_reviewer_capacity_count",
        ),
        "min_available_reviewer_capacity_count": _min_decimal(
            tuple(row.available_reviewer_capacity_count for row in rows),
        ),
        "max_memory_writeback_lag_seconds": _max_decimal(
            tuple(row.memory_writeback_lag_seconds for row in rows),
        ),
        "max_manual_escalation_urgency_score": _max_decimal(
            tuple(row.manual_escalation_urgency_score for row in rows),
        ),
        "max_backlog_pressure_score": _max_decimal(
            tuple(row.backlog_pressure_score for row in rows),
        ),
        "status": status,
        "manual_escalation_urgency": MANUAL_ESCALATION_BY_STATUS[status],
        "reason_codes": _report_reason_codes(rows),
        "reason_code_counts": _reason_code_counts(rows),
        "rows": rows,
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    return ResearchTeamSpecialistErrorTaxonomyBacklogReport(
        **values,
        derived_validation_digest=_digest_from_values(values),
    )


def research_team_specialist_error_taxonomy_backlog_report_payload(
    report: ResearchTeamSpecialistErrorTaxonomyBacklogReport | Mapping[str, object],
) -> dict[str, object]:
    if type(report) is ResearchTeamSpecialistErrorTaxonomyBacklogReport:
        _require_hard_flags("report", report)
        payload = _json_ready(asdict(report))
    elif isinstance(report, Mapping):
        payload = _json_ready(report)
    else:
        raise ValueError(
            "report must be a ResearchTeamSpecialistErrorTaxonomyBacklogReport",
        )
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    _require_hard_flags("report payload", _MappingFlags(payload))
    _reject_unsafe_public_payload("report payload", payload, allow_json_containers=True)
    expected_digest = _digest_from_payload(payload)
    if payload.get("derived_validation_digest") != expected_digest:
        raise ValueError("derived_validation_digest does not match report payload")
    return payload


def research_team_specialist_error_taxonomy_backlog_report_digest(
    report: ResearchTeamSpecialistErrorTaxonomyBacklogReport | Mapping[str, object],
) -> str:
    payload = research_team_specialist_error_taxonomy_backlog_report_payload(report)
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
    item: ResearchTeamSpecialistErrorTaxonomyBacklogInput,
    config: ResearchTeamSpecialistErrorTaxonomyBacklogConfig,
) -> ResearchTeamSpecialistErrorTaxonomyBacklogRow:
    reason_codes = _row_reason_codes(item=item, config=config)
    reviewer_capacity_gap_count = _positive_gap(
        config.min_pass_available_reviewer_capacity_count,
        item.available_reviewer_capacity_count,
    )
    return ResearchTeamSpecialistErrorTaxonomyBacklogRow(
        backlog_rank=ONE,
        specialist_label=item.specialist_label,
        error_category_label=item.error_category_label,
        status=_status_from_reason_codes(reason_codes),
        backlog_pressure_score=_backlog_pressure_score(
            item=item,
            reviewer_capacity_gap_count=reviewer_capacity_gap_count,
            config=config,
        ),
        unresolved_error_category_count=item.unresolved_error_category_count,
        stale_calibration_feedback_count=item.stale_calibration_feedback_count,
        impacted_domain_count=item.impacted_domain_count,
        available_reviewer_capacity_count=item.available_reviewer_capacity_count,
        reviewer_capacity_gap_count=reviewer_capacity_gap_count,
        reviewer_capacity_gap_ratio=_ratio(
            reviewer_capacity_gap_count,
            config.min_pass_available_reviewer_capacity_count,
        ),
        memory_writeback_lag_seconds=item.memory_writeback_lag_seconds,
        manual_escalation_urgency_score=item.manual_escalation_urgency_score,
        observed_at=item.observed_at,
        reason_codes=reason_codes,
    )


def _with_rank(
    row: ResearchTeamSpecialistErrorTaxonomyBacklogRow,
    rank: int,
) -> ResearchTeamSpecialistErrorTaxonomyBacklogRow:
    return ResearchTeamSpecialistErrorTaxonomyBacklogRow(
        backlog_rank=_count(rank),
        specialist_label=row.specialist_label,
        error_category_label=row.error_category_label,
        status=row.status,
        backlog_pressure_score=row.backlog_pressure_score,
        unresolved_error_category_count=row.unresolved_error_category_count,
        stale_calibration_feedback_count=row.stale_calibration_feedback_count,
        impacted_domain_count=row.impacted_domain_count,
        available_reviewer_capacity_count=row.available_reviewer_capacity_count,
        reviewer_capacity_gap_count=row.reviewer_capacity_gap_count,
        reviewer_capacity_gap_ratio=row.reviewer_capacity_gap_ratio,
        memory_writeback_lag_seconds=row.memory_writeback_lag_seconds,
        manual_escalation_urgency_score=row.manual_escalation_urgency_score,
        observed_at=row.observed_at,
        reason_codes=row.reason_codes,
    )


def _row_reason_codes(
    *,
    item: ResearchTeamSpecialistErrorTaxonomyBacklogInput,
    config: ResearchTeamSpecialistErrorTaxonomyBacklogConfig,
) -> tuple[str, ...]:
    reasons: list[str] = []
    _append_high_threshold_reason(
        reasons,
        metric=item.unresolved_error_category_count,
        watch=config.max_pass_unresolved_error_category_count,
        block=config.max_watch_unresolved_error_category_count,
        watch_code=UNRESOLVED_WATCH_REASON,
        block_code=UNRESOLVED_BLOCK_REASON,
    )
    _append_high_threshold_reason(
        reasons,
        metric=item.stale_calibration_feedback_count,
        watch=config.max_pass_stale_calibration_feedback_count,
        block=config.max_watch_stale_calibration_feedback_count,
        watch_code=STALE_WATCH_REASON,
        block_code=STALE_BLOCK_REASON,
    )
    _append_high_threshold_reason(
        reasons,
        metric=item.impacted_domain_count,
        watch=config.max_pass_impacted_domain_count,
        block=config.max_watch_impacted_domain_count,
        watch_code=DOMAIN_WATCH_REASON,
        block_code=DOMAIN_BLOCK_REASON,
    )
    _append_low_threshold_reason(
        reasons,
        metric=item.available_reviewer_capacity_count,
        watch=config.min_pass_available_reviewer_capacity_count,
        block=config.min_watch_available_reviewer_capacity_count,
        watch_code=CAPACITY_WATCH_REASON,
        block_code=CAPACITY_BLOCK_REASON,
    )
    _append_high_threshold_reason(
        reasons,
        metric=item.memory_writeback_lag_seconds,
        watch=config.max_pass_memory_writeback_lag_seconds,
        block=config.max_watch_memory_writeback_lag_seconds,
        watch_code=WRITEBACK_WATCH_REASON,
        block_code=WRITEBACK_BLOCK_REASON,
    )
    _append_high_threshold_reason(
        reasons,
        metric=item.manual_escalation_urgency_score,
        watch=config.max_pass_manual_escalation_urgency_score,
        block=config.max_watch_manual_escalation_urgency_score,
        watch_code=ESCALATION_WATCH_REASON,
        block_code=ESCALATION_BLOCK_REASON,
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


def _backlog_pressure_score(
    *,
    item: ResearchTeamSpecialistErrorTaxonomyBacklogInput,
    reviewer_capacity_gap_count: Decimal,
    config: ResearchTeamSpecialistErrorTaxonomyBacklogConfig,
) -> Decimal:
    return _max_decimal(
        (
            _high_threshold_pressure(
                item.unresolved_error_category_count,
                config.max_pass_unresolved_error_category_count,
                config.max_watch_unresolved_error_category_count,
            ),
            _high_threshold_pressure(
                item.stale_calibration_feedback_count,
                config.max_pass_stale_calibration_feedback_count,
                config.max_watch_stale_calibration_feedback_count,
            ),
            _high_threshold_pressure(
                item.impacted_domain_count,
                config.max_pass_impacted_domain_count,
                config.max_watch_impacted_domain_count,
            ),
            _ratio(
                reviewer_capacity_gap_count,
                config.min_pass_available_reviewer_capacity_count,
            ),
            _high_threshold_pressure(
                item.memory_writeback_lag_seconds,
                config.max_pass_memory_writeback_lag_seconds,
                config.max_watch_memory_writeback_lag_seconds,
            ),
            _high_threshold_pressure(
                item.manual_escalation_urgency_score,
                config.max_pass_manual_escalation_urgency_score,
                config.max_watch_manual_escalation_urgency_score,
            ),
        ),
    )


def _high_threshold_pressure(value: Decimal, pass_limit: Decimal, block_limit: Decimal) -> Decimal:
    if value <= pass_limit:
        return ZERO
    if block_limit == pass_limit:
        return ONE
    return _clamp_ratio((value - pass_limit) / (block_limit - pass_limit))


def _positive_gap(required: Decimal, actual: Decimal) -> Decimal:
    if actual >= required:
        return ZERO
    return _quantize(required - actual)


def _normalize_inputs(
    inputs: Iterable[ResearchTeamSpecialistErrorTaxonomyBacklogInput],
) -> tuple[ResearchTeamSpecialistErrorTaxonomyBacklogInput, ...]:
    if isinstance(inputs, (str, bytes)):
        raise ValueError("inputs must be an iterable of backlog inputs")
    normalized: list[ResearchTeamSpecialistErrorTaxonomyBacklogInput] = []
    seen_keys: set[tuple[str, str]] = set()
    for item in inputs:
        _require_exact_type(
            item,
            ResearchTeamSpecialistErrorTaxonomyBacklogInput,
            "input",
        )
        _require_hard_flags("input", item)
        key = (item.specialist_label, item.error_category_label)
        if key in seen_keys:
            raise ValueError("specialist error category labels must be unique")
        seen_keys.add(key)
        normalized.append(item)
    return tuple(normalized)


def _row_sort_key(row: ResearchTeamSpecialistErrorTaxonomyBacklogRow) -> tuple[object, ...]:
    return (
        STATUS_RANK[row.status],
        -row.backlog_pressure_score,
        row.specialist_label,
        row.error_category_label,
    )


def _status_count(
    rows: tuple[ResearchTeamSpecialistErrorTaxonomyBacklogRow, ...],
    status: str,
) -> Decimal:
    return _count(sum(1 for row in rows if row.status == status))


def _report_status(rows: tuple[ResearchTeamSpecialistErrorTaxonomyBacklogRow, ...]) -> str:
    if any(row.status == "block" for row in rows):
        return "block"
    if any(row.status == "watch" for row in rows):
        return "watch"
    return "pass"


def _report_reason_codes(
    rows: tuple[ResearchTeamSpecialistErrorTaxonomyBacklogRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return (EMPTY_REASON,)
    codes = {
        reason
        for row in rows
        for reason in row.reason_codes
        if reason != CLEAR_REASON
    }
    if not codes:
        return (CLEAR_REASON,)
    return tuple(reason for reason in REASON_SEQUENCE if reason in codes)


def _reason_code_counts(
    rows: tuple[ResearchTeamSpecialistErrorTaxonomyBacklogRow, ...],
) -> tuple[ResearchTeamSpecialistErrorTaxonomyBacklogReasonCodeCount, ...]:
    if not rows:
        return ()
    counts: Counter[str] = Counter(
        reason for row in rows for reason in row.reason_codes
    )
    total = _count(len(rows))
    return tuple(
        ResearchTeamSpecialistErrorTaxonomyBacklogReasonCodeCount(
            reason_code=reason,
            count=_count(counts[reason]),
            row_ratio=_ratio(_count(counts[reason]), total),
        )
        for reason in REASON_SEQUENCE
        if counts[reason] > 0
    )


def _sum_row_decimal(
    rows: tuple[ResearchTeamSpecialistErrorTaxonomyBacklogRow, ...],
    field_name: str,
) -> Decimal:
    total = ZERO
    for row in rows:
        total += getattr(row, field_name)
    return _quantize(total)


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
    if value < ZERO:
        return ZERO
    if value > ONE:
        return ONE
    return _quantize(value)


def _validate_config_thresholds(
    config: ResearchTeamSpecialistErrorTaxonomyBacklogConfig,
) -> None:
    if (
        config.max_pass_unresolved_error_category_count
        > config.max_watch_unresolved_error_category_count
    ):
        raise ValueError(
            "max_watch_unresolved_error_category_count must be at least pass",
        )
    if (
        config.max_pass_stale_calibration_feedback_count
        > config.max_watch_stale_calibration_feedback_count
    ):
        raise ValueError(
            "max_watch_stale_calibration_feedback_count must be at least pass",
        )
    if config.max_pass_impacted_domain_count > config.max_watch_impacted_domain_count:
        raise ValueError("max_watch_impacted_domain_count must be at least pass")
    if (
        config.min_watch_available_reviewer_capacity_count
        > config.min_pass_available_reviewer_capacity_count
    ):
        raise ValueError(
            "min_watch_available_reviewer_capacity_count must not exceed pass",
        )
    if (
        config.max_pass_memory_writeback_lag_seconds
        > config.max_watch_memory_writeback_lag_seconds
    ):
        raise ValueError("max_watch_memory_writeback_lag_seconds must be at least pass")
    if (
        config.max_pass_manual_escalation_urgency_score
        > config.max_watch_manual_escalation_urgency_score
    ):
        raise ValueError(
            "max_watch_manual_escalation_urgency_score must be at least pass",
        )


def _validate_report(report: ResearchTeamSpecialistErrorTaxonomyBacklogReport) -> None:
    rows = report.rows
    if report.input_count != _count(len(rows)):
        raise ValueError("input_count must match rows")
    if report.backlog_item_count != _count(
        sum(1 for row in rows if row.status in ("watch", "block")),
    ):
        raise ValueError("backlog_item_count must match rows")
    if report.pass_count != _status_count(rows, "pass"):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _status_count(rows, "watch"):
        raise ValueError("watch_count must match rows")
    if report.block_count != _status_count(rows, "block"):
        raise ValueError("block_count must match rows")
    if report.backlog_ratio != _ratio(report.backlog_item_count, report.input_count):
        raise ValueError("backlog_ratio must match rows")
    if report.total_unresolved_error_category_count != _sum_row_decimal(
        rows,
        "unresolved_error_category_count",
    ):
        raise ValueError("total_unresolved_error_category_count must match rows")
    if report.total_stale_calibration_feedback_count != _sum_row_decimal(
        rows,
        "stale_calibration_feedback_count",
    ):
        raise ValueError("total_stale_calibration_feedback_count must match rows")
    if report.total_impacted_domain_count != _sum_row_decimal(
        rows,
        "impacted_domain_count",
    ):
        raise ValueError("total_impacted_domain_count must match rows")
    if report.total_available_reviewer_capacity_count != _sum_row_decimal(
        rows,
        "available_reviewer_capacity_count",
    ):
        raise ValueError("total_available_reviewer_capacity_count must match rows")
    if report.min_available_reviewer_capacity_count != _min_decimal(
        tuple(row.available_reviewer_capacity_count for row in rows),
    ):
        raise ValueError("min_available_reviewer_capacity_count must match rows")
    if report.max_memory_writeback_lag_seconds != _max_decimal(
        tuple(row.memory_writeback_lag_seconds for row in rows),
    ):
        raise ValueError("max_memory_writeback_lag_seconds must match rows")
    if report.max_manual_escalation_urgency_score != _max_decimal(
        tuple(row.manual_escalation_urgency_score for row in rows),
    ):
        raise ValueError("max_manual_escalation_urgency_score must match rows")
    if report.max_backlog_pressure_score != _max_decimal(
        tuple(row.backlog_pressure_score for row in rows),
    ):
        raise ValueError("max_backlog_pressure_score must match rows")
    if report.status != _report_status(rows):
        raise ValueError("status must match rows")
    if report.manual_escalation_urgency != MANUAL_ESCALATION_BY_STATUS[report.status]:
        raise ValueError("manual_escalation_urgency must match status")
    if report.reason_codes != _report_reason_codes(rows):
        raise ValueError("reason_codes must match rows")
    if report.reason_code_counts != _reason_code_counts(rows):
        raise ValueError("reason_code_counts must match rows")


def _require_rows(
    rows: tuple[ResearchTeamSpecialistErrorTaxonomyBacklogRow, ...],
) -> tuple[ResearchTeamSpecialistErrorTaxonomyBacklogRow, ...]:
    if type(rows) is not tuple:
        raise ValueError("rows must be a tuple")
    for row in rows:
        _require_exact_type(row, ResearchTeamSpecialistErrorTaxonomyBacklogRow, "row")
        _require_hard_flags("row", row)
    if rows != tuple(sorted(rows, key=_row_sort_key)):
        raise ValueError("rows must be sorted deterministically")
    if tuple(row.backlog_rank for row in rows) != tuple(
        _count(rank) for rank in range(1, len(rows) + 1)
    ):
        raise ValueError("backlog_rank values must be sequential")
    return rows


def _require_reason_code_counts(
    counts: tuple[ResearchTeamSpecialistErrorTaxonomyBacklogReasonCodeCount, ...],
) -> tuple[ResearchTeamSpecialistErrorTaxonomyBacklogReasonCodeCount, ...]:
    if type(counts) is not tuple:
        raise ValueError("reason_code_counts must be a tuple")
    previous_rank = -1
    for item in counts:
        _require_exact_type(
            item,
            ResearchTeamSpecialistErrorTaxonomyBacklogReasonCodeCount,
            "reason_code_count",
        )
        _require_hard_flags("reason_code_count", item)
        rank = REASON_RANK[item.reason_code]
        if rank <= previous_rank:
            raise ValueError("reason_code_counts must be sorted and unique")
        previous_rank = rank
    return counts


def _require_report_reason_codes(reason_codes: tuple[str, ...]) -> tuple[str, ...]:
    if type(reason_codes) is not tuple:
        raise ValueError("reason_codes must be a tuple")
    if not reason_codes:
        raise ValueError("reason_codes must not be empty")
    if reason_codes == (EMPTY_REASON,):
        return reason_codes
    return _require_reason_codes(reason_codes, require_nonempty=True)


def _require_reason_codes(
    reason_codes: tuple[str, ...],
    *,
    require_nonempty: bool,
) -> tuple[str, ...]:
    if type(reason_codes) is not tuple:
        raise ValueError("reason_codes must be a tuple")
    if require_nonempty and not reason_codes:
        raise ValueError("reason_codes must not be empty")
    previous_rank = -1
    for reason_code in reason_codes:
        _require_reason_code("reason_code", reason_code)
        rank = REASON_RANK[reason_code]
        if rank <= previous_rank:
            raise ValueError("reason_codes must be sorted and unique")
        previous_rank = rank
    return reason_codes


def _require_reason_code(name: str, value: object) -> None:
    _require_public_string(name, value)
    if value not in REASON_RANK:
        raise ValueError(f"{name} is not supported")


def _require_status(name: str, value: object) -> None:
    if type(value) is not str or value not in SPECIALIST_ERROR_TAXONOMY_BACKLOG_STATUSES:
        raise ValueError(f"{name} must be one of pass/watch/block")


def _require_exact_type(value: object, expected_type: type, name: str) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{name} must be exactly {expected_type.__name__}")


def _require_hard_flags(name: str, value: object) -> None:
    if getattr(value, "paper_only", None) is not True:
        raise ValueError(f"{name} paper_only must be True")
    if getattr(value, "report_only", None) is not True:
        raise ValueError(f"{name} report_only must be True")
    if getattr(value, "readonly", None) is not True:
        raise ValueError(f"{name} readonly must be True")


def _require_public_string(name: str, value: object) -> str:
    if type(value) is not str or not PUBLIC_LABEL_RE.fullmatch(value):
        raise ValueError(f"{name} must be a public aggregate label")
    return value


def _require_public_label(name: str, value: object) -> str:
    label = _require_public_string(name, value)
    normalized = label.lower()
    if any(fragment in normalized for fragment in PUBLIC_LABEL_BLOCK_FRAGMENTS):
        raise ValueError(f"{name} must be a public aggregate label")
    return label


def _require_count_decimal(name: str, value: object) -> Decimal:
    normalized = _require_nonnegative_decimal(name, value)
    if normalized != normalized.quantize(Decimal("1"), rounding=ROUND_HALF_EVEN):
        raise ValueError(f"{name} must be a whole Decimal")
    return normalized


def _require_nonnegative_decimal(name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(name, value)
    if normalized < ZERO:
        raise ValueError(f"{name} must be nonnegative")
    return normalized


def _require_ratio_decimal(name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(name, value)
    if normalized < ZERO or normalized > ONE:
        raise ValueError(f"{name} must be between 0 and 1")
    return normalized


def _normalize_decimal(name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{name} must be finite")
    return _quantize(value)


def _quantize(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(QUANTUM)


def _count(value: int) -> Decimal:
    return _quantize(Decimal(value))


def _as_utc(name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{name} must be UTC-aware")
    if value.utcoffset() != timedelta(0):
        raise ValueError(f"{name} must be UTC-aware")
    return value.astimezone(UTC)


def _as_generated_at_utc(name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{name} must be UTC")
    if value.utcoffset() != timedelta(0):
        raise ValueError(f"{name} must be UTC")
    return value.astimezone(UTC)


def _require_sha256(name: str, value: object) -> None:
    if type(value) is not str or len(value) != 64:
        raise ValueError(f"{name} must be a SHA-256 digest")
    if any(character not in HEX_CHARS for character in value):
        raise ValueError(f"{name} must be a SHA-256 digest")


def _report_values_without_digest(
    report: ResearchTeamSpecialistErrorTaxonomyBacklogReport,
) -> dict[str, object]:
    values = asdict(report)
    values.pop("derived_validation_digest")
    return values


def _digest_from_values(values: Mapping[str, object]) -> str:
    payload = _json_ready(values)
    if type(payload) is not dict:
        raise ValueError("digest payload must be a JSON object")
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    return sha256(encoded).hexdigest()


def _digest_from_payload(payload: Mapping[str, object]) -> str:
    unsigned = dict(payload)
    unsigned.pop("derived_validation_digest", None)
    encoded = json.dumps(unsigned, sort_keys=True, separators=(",", ":")).encode()
    return sha256(encoded).hexdigest()


def _json_ready(value: Any) -> Any:
    if value is None:
        return None
    if is_dataclass(value) and not isinstance(value, type):
        return _json_ready(asdict(value))
    if isinstance(value, Decimal):
        if not value.is_finite():
            raise ValueError("JSON Decimal value must be finite")
        return str(_quantize(value))
    if isinstance(value, datetime):
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("JSON datetime value must be timezone-aware")
        return value.astimezone(UTC).isoformat()
    if type(value) is bool or type(value) is str:
        return value
    if type(value) is int:
        raise ValueError("JSON value must use Decimal-derived string values")
    if type(value) is float:
        raise ValueError("JSON value must not be a float")
    if isinstance(value, Mapping):
        ready: dict[str, Any] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            ready[key] = _json_ready(item)
        return ready
    if isinstance(value, (list, tuple)):
        return [_json_ready(item) for item in value]
    raise ValueError("value is not JSON serializable")


def _reject_unsafe_public_payload(
    label: str,
    value: object,
    *,
    allow_json_containers: bool = False,
) -> None:
    if is_dataclass(value) and not isinstance(value, type):
        _reject_unsafe_public_payload(
            label,
            asdict(value),
            allow_json_containers=allow_json_containers,
        )
        return
    if isinstance(value, Mapping):
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("public payload keys must be strings")
            if _contains_unsafe_fragment(key):
                raise ValueError(f"unsafe field in {label}")
            _reject_unsafe_public_payload(
                label,
                item,
                allow_json_containers=allow_json_containers,
            )
        return
    if isinstance(value, (list, tuple)):
        for item in value:
            _reject_unsafe_public_payload(
                label,
                item,
                allow_json_containers=allow_json_containers,
            )
        return
    if type(value) is str and _contains_unsafe_fragment(value):
        raise ValueError(f"unsafe value in {label}")
    if not allow_json_containers and type(value) is float:
        raise ValueError(f"unsafe numeric type in {label}")


def _contains_unsafe_fragment(value: str) -> bool:
    normalized = value.lower()
    return any(fragment in normalized for fragment in UNSAFE_PUBLIC_FRAGMENTS)
