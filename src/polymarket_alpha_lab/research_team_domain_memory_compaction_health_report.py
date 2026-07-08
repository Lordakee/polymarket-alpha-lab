"""Pure report-only reducer for team domain memory compaction health."""

from __future__ import annotations

from dataclasses import dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, localcontext
from hashlib import sha256
import json
from typing import Any, Iterable


DEFAULT_RESEARCH_TEAM_DOMAIN_MEMORY_COMPACTION_HEALTH_REPORT_CONFIG_VERSION = (
    "research-team-domain-memory-compaction-health-report-v0"
)
DOMAIN_MEMORY_COMPACTION_HEALTH_STATUSES = ("pass", "watch", "block")
DOMAIN_MEMORY_COMPACTION_HEALTH_REASON_CODES = (
    "no_domain_memory_compaction_health_inputs",
    "calibration_feedback_block",
    "domain_memory_compaction_health_block",
    "domain_memory_compaction_health_watch",
    "domain_memory_compaction_health_pass",
    "memory_compaction_stale_block",
    "memory_compaction_watch_age",
    "memory_conflict_carry_forward_block",
    "memory_conflict_carry_forward_watch",
    "memory_retrieval_coverage_block",
    "memory_retrieval_coverage_watch",
)

_DIGEST_FIELD = "derived_validation_digest"
_QUANTUM = Decimal("0.000001")
_COUNT_QUANTUM = Decimal("1")
_ZERO = Decimal("0.000000")
_ZERO_COUNT = Decimal("0")
_ONE = Decimal("1.000000")
_DECIMAL_CONTEXT = Context(prec=64)
_SECONDS_PER_DAY = Decimal("86400")
_MICROSECONDS_PER_SECOND = Decimal("1000000")
_STATUS_RANK = {"block": 0, "watch": 1, "pass": 2}
_ROW_REASON_PRIORITY = DOMAIN_MEMORY_COMPACTION_HEALTH_REASON_CODES[1:]
_REPORT_REASON_PRIORITY = (
    "calibration_feedback_block",
    "domain_memory_compaction_health_block",
    "domain_memory_compaction_health_watch",
    "memory_compaction_stale_block",
    "memory_compaction_watch_age",
    "memory_conflict_carry_forward_block",
    "memory_conflict_carry_forward_watch",
    "memory_retrieval_coverage_block",
    "memory_retrieval_coverage_watch",
)
_UNSAFE_PUBLIC_LABEL_FRAGMENTS = frozenset(
    (
        "candidate" "_" "id",
        "market" "_" "id",
        "market" "_" "slug",
        "ques" "tion",
        "src" "_" "url",
        "src" "_" "text",
        "source" "_" "url",
        "source" "_" "text",
        "d" "sn",
        "table" "_" "name",
        "private" "_" "tok" "en",
        "wal" "let",
        "acc" "ount",
        "or" "der",
        "private" "_" "key",
        "api" "_" "key",
        "sec" "ret",
        "cl" "ob",
        "au" "th",
        "net" "work",
        "reco" "mmend",
        "siz" "ing",
        "ad" "vice",
        "tr" "ade",
        "li" "ve",
        "tr" "ading",
    ),
)

__all__ = (
    "DEFAULT_RESEARCH_TEAM_DOMAIN_MEMORY_COMPACTION_HEALTH_REPORT_CONFIG_VERSION",
    "DOMAIN_MEMORY_COMPACTION_HEALTH_STATUSES",
    "DOMAIN_MEMORY_COMPACTION_HEALTH_REASON_CODES",
    "ResearchTeamDomainMemoryCompactionHealthConfig",
    "ResearchTeamDomainMemoryCompactionHealthInput",
    "ResearchTeamDomainMemoryCompactionHealthReport",
    "ResearchTeamDomainMemoryCompactionHealthRow",
    "build_research_team_domain_memory_compaction_health_report",
    "research_team_domain_memory_compaction_health_report_payload",
)


@dataclass(frozen=True)
class ResearchTeamDomainMemoryCompactionHealthConfig:
    config_version: str = (
        DEFAULT_RESEARCH_TEAM_DOMAIN_MEMORY_COMPACTION_HEALTH_REPORT_CONFIG_VERSION
    )
    recent_memory_seconds: Decimal = Decimal("604800.000000")
    stale_memory_seconds: Decimal = Decimal("2592000.000000")
    calibration_watch_threshold: Decimal = Decimal("0.550000")
    retrieval_pass_threshold: Decimal = Decimal("0.800000")
    retrieval_watch_threshold: Decimal = Decimal("0.500000")
    health_pass_threshold: Decimal = Decimal("0.800000")
    health_watch_threshold: Decimal = Decimal("0.500000")
    freshness_weight: Decimal = Decimal("0.250000")
    conflict_weight: Decimal = Decimal("0.250000")
    calibration_weight: Decimal = Decimal("0.250000")
    retrieval_weight: Decimal = Decimal("0.250000")
    conflict_penalty: Decimal = Decimal("0.250000")
    blocking_conflict_count: Decimal = Decimal("3")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchTeamDomainMemoryCompactionHealthConfig does not support subclassing",
        )

    def __post_init__(self) -> None:
        _require_exact_type(
            "config",
            self,
            ResearchTeamDomainMemoryCompactionHealthConfig,
        )
        _require_canonical_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_TEAM_DOMAIN_MEMORY_COMPACTION_HEALTH_REPORT_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported version")
        for field_name in ("recent_memory_seconds", "stale_memory_seconds"):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        if self.recent_memory_seconds <= _ZERO:
            raise ValueError("recent_memory_seconds must be positive")
        if self.stale_memory_seconds <= self.recent_memory_seconds:
            raise ValueError("stale_memory_seconds must exceed recent_memory_seconds")
        for field_name in (
            "calibration_watch_threshold",
            "retrieval_pass_threshold",
            "retrieval_watch_threshold",
            "health_pass_threshold",
            "health_watch_threshold",
            "freshness_weight",
            "conflict_weight",
            "calibration_weight",
            "retrieval_weight",
            "conflict_penalty",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        if self.retrieval_pass_threshold < self.retrieval_watch_threshold:
            raise ValueError("retrieval_pass_threshold must be at least watch threshold")
        if self.health_pass_threshold < self.health_watch_threshold:
            raise ValueError("health_pass_threshold must be at least watch threshold")
        if (
            _quantize(
                self.freshness_weight
                + self.conflict_weight
                + self.calibration_weight
                + self.retrieval_weight,
            )
            != _ONE
        ):
            raise ValueError("health weights must sum to one")
        object.__setattr__(
            self,
            "blocking_conflict_count",
            _normalize_count("blocking_conflict_count", self.blocking_conflict_count),
        )
        if self.blocking_conflict_count <= _ZERO_COUNT:
            raise ValueError("blocking_conflict_count must be positive")
        _require_hard_flags(self)
        _reject_unsafe_public_surface("config", self)


@dataclass(frozen=True)
class ResearchTeamDomainMemoryCompactionHealthInput:
    team_domain: str
    compacted_memory_count: Decimal
    latest_compacted_memory_at: datetime
    carry_forward_conflict_count: Decimal
    calibration_feedback_score: Decimal
    retrieval_coverage_ratio: Decimal
    redaction_confirmed: bool = True
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchTeamDomainMemoryCompactionHealthInput does not support subclassing",
        )

    def __post_init__(self) -> None:
        _require_exact_type(
            "input",
            self,
            ResearchTeamDomainMemoryCompactionHealthInput,
        )
        _require_public_label("team_domain", self.team_domain)
        for field_name in ("compacted_memory_count", "carry_forward_conflict_count"):
            object.__setattr__(
                self,
                field_name,
                _normalize_count(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "latest_compacted_memory_at",
            _as_utc("latest_compacted_memory_at", self.latest_compacted_memory_at),
        )
        for field_name in ("calibration_feedback_score", "retrieval_coverage_ratio"):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        if self.redaction_confirmed is not True:
            raise ValueError("redaction_confirmed must be True")
        _require_hard_flags(self)
        _reject_unsafe_public_surface("input", self)


@dataclass(frozen=True)
class ResearchTeamDomainMemoryCompactionHealthRow:
    team_domain: str
    compacted_memory_count: Decimal
    latest_compacted_memory_at: datetime
    memory_age_seconds: Decimal
    freshness_score: Decimal
    carry_forward_conflict_count: Decimal
    conflict_carry_forward_score: Decimal
    calibration_feedback_score: Decimal
    retrieval_coverage_ratio: Decimal
    domain_compaction_health_score: Decimal
    row_status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchTeamDomainMemoryCompactionHealthRow does not support subclassing",
        )

    def __post_init__(self) -> None:
        _require_exact_type("row", self, ResearchTeamDomainMemoryCompactionHealthRow)
        _require_public_label("team_domain", self.team_domain)
        for field_name in ("compacted_memory_count", "carry_forward_conflict_count"):
            object.__setattr__(
                self,
                field_name,
                _normalize_count(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "latest_compacted_memory_at",
            _as_utc("latest_compacted_memory_at", self.latest_compacted_memory_at),
        )
        object.__setattr__(
            self,
            "memory_age_seconds",
            _normalize_nonnegative_decimal("memory_age_seconds", self.memory_age_seconds),
        )
        for field_name in (
            "freshness_score",
            "conflict_carry_forward_score",
            "calibration_feedback_score",
            "retrieval_coverage_ratio",
            "domain_compaction_health_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        _require_status("row_status", self.row_status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes_preserving_sequence(self.reason_codes),
        )
        _validate_row_consistency(self)
        _require_hard_flags(self)
        _reject_unsafe_public_surface("row", self)


@dataclass(frozen=True)
class ResearchTeamDomainMemoryCompactionHealthReport:
    generated_at: datetime
    config_version: str
    status: str
    row_count: Decimal
    domain_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    fresh_domain_count: Decimal
    conflict_free_domain_count: Decimal
    calibrated_domain_count: Decimal
    retrieval_ready_domain_count: Decimal
    average_domain_compaction_health_score: Decimal
    rows: tuple[ResearchTeamDomainMemoryCompactionHealthRow, ...]
    reason_codes: tuple[str, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchTeamDomainMemoryCompactionHealthReport does not support subclassing",
        )

    def __post_init__(self) -> None:
        _require_exact_type("report", self, ResearchTeamDomainMemoryCompactionHealthReport)
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        _require_status("status", self.status)
        for field_name in (
            "row_count",
            "domain_count",
            "pass_count",
            "watch_count",
            "block_count",
            "fresh_domain_count",
            "conflict_free_domain_count",
            "calibrated_domain_count",
            "retrieval_ready_domain_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_count(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "average_domain_compaction_health_score",
            _normalize_ratio(
                "average_domain_compaction_health_score",
                self.average_domain_compaction_health_score,
            ),
        )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes_preserving_sequence(self.reason_codes),
        )
        _validate_report_consistency(self)
        _require_hard_flags(self)
        _reject_unsafe_public_surface("report", self)
        _require_or_set_digest(self)

    @property
    def payload(self) -> dict[str, Any]:
        payload = _payload_value(self)
        if type(payload) is not dict:
            raise ValueError("payload must be a JSON object")
        _reject_unsafe_public_surface("payload", payload)
        _require_hard_flags(_DictFlags(payload))
        _validate_payload_digest(payload)
        return payload


def build_research_team_domain_memory_compaction_health_report(
    inputs: Iterable[ResearchTeamDomainMemoryCompactionHealthInput],
    *,
    generated_at: datetime,
    config: ResearchTeamDomainMemoryCompactionHealthConfig | None = None,
) -> ResearchTeamDomainMemoryCompactionHealthReport:
    if config is None:
        config = ResearchTeamDomainMemoryCompactionHealthConfig()
    _require_exact_type("config", config, ResearchTeamDomainMemoryCompactionHealthConfig)
    _require_hard_flags(config)
    generated_at = _as_utc("generated_at", generated_at)
    normalized = _normalize_inputs(inputs)
    for value in normalized:
        if _seconds_between(value.latest_compacted_memory_at, generated_at) < _ZERO:
            raise ValueError("generated_at must be at or after latest_compacted_memory_at")
    rows = tuple(
        sorted(
            (_row_from_input(value, generated_at, config) for value in normalized),
            key=_row_sort_key,
        ),
    )
    return ResearchTeamDomainMemoryCompactionHealthReport(
        generated_at=generated_at,
        config_version=config.config_version,
        status=_report_status(rows),
        row_count=_decimal_count(len(rows)),
        domain_count=_decimal_count(len({row.team_domain for row in rows})),
        pass_count=_status_count(rows, "pass"),
        watch_count=_status_count(rows, "watch"),
        block_count=_status_count(rows, "block"),
        fresh_domain_count=_count_if(
            rows,
            lambda row: row.memory_age_seconds <= config.recent_memory_seconds,
        ),
        conflict_free_domain_count=_count_if(
            rows,
            lambda row: row.carry_forward_conflict_count == _ZERO_COUNT,
        ),
        calibrated_domain_count=_count_if(
            rows,
            lambda row: row.calibration_feedback_score >= config.calibration_watch_threshold,
        ),
        retrieval_ready_domain_count=_count_if(
            rows,
            lambda row: row.retrieval_coverage_ratio >= config.retrieval_watch_threshold,
        ),
        average_domain_compaction_health_score=_average_score(
            tuple(row.domain_compaction_health_score for row in rows),
        ),
        rows=rows,
        reason_codes=_report_reason_codes(rows),
    )


def research_team_domain_memory_compaction_health_report_payload(
    report: ResearchTeamDomainMemoryCompactionHealthReport | dict[str, Any],
) -> dict[str, Any]:
    if type(report) is ResearchTeamDomainMemoryCompactionHealthReport:
        _require_hard_flags(report)
        _reject_unsafe_public_surface("report", report)
        return report.payload
    if type(report) is dict:
        _reject_unsafe_public_surface("payload", report)
        payload = _payload_value(report)
        if type(payload) is not dict:
            raise ValueError("payload must be a JSON object")
        _require_hard_flags(_DictFlags(payload))
        _validate_payload_digest(payload)
        return payload
    raise ValueError(
        "report must be a ResearchTeamDomainMemoryCompactionHealthReport or payload",
    )


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


def _row_from_input(
    value: ResearchTeamDomainMemoryCompactionHealthInput,
    generated_at: datetime,
    config: ResearchTeamDomainMemoryCompactionHealthConfig,
) -> ResearchTeamDomainMemoryCompactionHealthRow:
    memory_age_seconds = _seconds_between(value.latest_compacted_memory_at, generated_at)
    freshness_score = _freshness_score(memory_age_seconds, config)
    conflict_score = _conflict_score(value.carry_forward_conflict_count, config)
    health_score = _health_score(
        freshness_score=freshness_score,
        conflict_score=conflict_score,
        calibration_score=value.calibration_feedback_score,
        retrieval_score=value.retrieval_coverage_ratio,
        config=config,
    )
    reason_codes = _row_reason_codes(
        memory_age_seconds=memory_age_seconds,
        conflict_count=value.carry_forward_conflict_count,
        calibration_score=value.calibration_feedback_score,
        retrieval_score=value.retrieval_coverage_ratio,
        health_score=health_score,
        config=config,
    )
    return ResearchTeamDomainMemoryCompactionHealthRow(
        team_domain=value.team_domain,
        compacted_memory_count=value.compacted_memory_count,
        latest_compacted_memory_at=value.latest_compacted_memory_at,
        memory_age_seconds=memory_age_seconds,
        freshness_score=freshness_score,
        carry_forward_conflict_count=value.carry_forward_conflict_count,
        conflict_carry_forward_score=conflict_score,
        calibration_feedback_score=value.calibration_feedback_score,
        retrieval_coverage_ratio=value.retrieval_coverage_ratio,
        domain_compaction_health_score=health_score,
        row_status=_status_from_reason_codes(reason_codes),
        reason_codes=reason_codes,
    )


def _freshness_score(
    memory_age_seconds: Decimal,
    config: ResearchTeamDomainMemoryCompactionHealthConfig,
) -> Decimal:
    if memory_age_seconds <= config.recent_memory_seconds:
        return _ONE
    if memory_age_seconds >= config.stale_memory_seconds:
        return _ZERO
    with localcontext(_DECIMAL_CONTEXT):
        return _quantize(_ONE - (memory_age_seconds / config.stale_memory_seconds))


def _conflict_score(
    conflict_count: Decimal,
    config: ResearchTeamDomainMemoryCompactionHealthConfig,
) -> Decimal:
    with localcontext(_DECIMAL_CONTEXT):
        score = _quantize(_ONE - (conflict_count * config.conflict_penalty))
    if score < _ZERO:
        return _ZERO
    return score


def _health_score(
    *,
    freshness_score: Decimal,
    conflict_score: Decimal,
    calibration_score: Decimal,
    retrieval_score: Decimal,
    config: ResearchTeamDomainMemoryCompactionHealthConfig,
) -> Decimal:
    with localcontext(_DECIMAL_CONTEXT):
        return _quantize(
            (freshness_score * config.freshness_weight)
            + (conflict_score * config.conflict_weight)
            + (calibration_score * config.calibration_weight)
            + (retrieval_score * config.retrieval_weight),
        )


def _row_reason_codes(
    *,
    memory_age_seconds: Decimal,
    conflict_count: Decimal,
    calibration_score: Decimal,
    retrieval_score: Decimal,
    health_score: Decimal,
    config: ResearchTeamDomainMemoryCompactionHealthConfig,
) -> tuple[str, ...]:
    reasons: list[str] = []
    if calibration_score < config.calibration_watch_threshold:
        reasons.append("calibration_feedback_block")
    if health_score < config.health_watch_threshold:
        reasons.append("domain_memory_compaction_health_block")
    elif health_score < config.health_pass_threshold:
        reasons.append("domain_memory_compaction_health_watch")
    else:
        reasons.append("domain_memory_compaction_health_pass")
    if memory_age_seconds >= config.stale_memory_seconds:
        reasons.append("memory_compaction_stale_block")
    elif memory_age_seconds > config.recent_memory_seconds:
        reasons.append("memory_compaction_watch_age")
    if conflict_count >= config.blocking_conflict_count:
        reasons.append("memory_conflict_carry_forward_block")
    elif conflict_count > _ZERO_COUNT:
        reasons.append("memory_conflict_carry_forward_watch")
    if retrieval_score < config.retrieval_watch_threshold:
        reasons.append("memory_retrieval_coverage_block")
    elif retrieval_score < config.retrieval_pass_threshold:
        reasons.append("memory_retrieval_coverage_watch")
    return tuple(reason for reason in _ROW_REASON_PRIORITY if reason in reasons)


def _status_from_reason_codes(reason_codes: tuple[str, ...]) -> str:
    if "domain_memory_compaction_health_block" in reason_codes:
        return "block"
    if "domain_memory_compaction_health_watch" in reason_codes:
        return "watch"
    return "pass"


def _report_status(rows: tuple[ResearchTeamDomainMemoryCompactionHealthRow, ...]) -> str:
    if not rows:
        return "block"
    if any(row.row_status == "block" for row in rows):
        return "block"
    if any(row.row_status == "watch" for row in rows):
        return "watch"
    return "pass"


def _report_reason_codes(
    rows: tuple[ResearchTeamDomainMemoryCompactionHealthRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return ("no_domain_memory_compaction_health_inputs",)
    present = frozenset(
        reason_code
        for row in rows
        for reason_code in row.reason_codes
        if reason_code != "domain_memory_compaction_health_pass"
    )
    if not present:
        return ("domain_memory_compaction_health_pass",)
    return tuple(reason_code for reason_code in _REPORT_REASON_PRIORITY if reason_code in present)


def _normalize_inputs(
    values: Iterable[ResearchTeamDomainMemoryCompactionHealthInput],
) -> tuple[ResearchTeamDomainMemoryCompactionHealthInput, ...]:
    if isinstance(values, (str, bytes)):
        raise ValueError("inputs must be an iterable")
    try:
        normalized = tuple(values)
    except TypeError as exc:
        raise ValueError("inputs must be an iterable") from exc
    seen_domains: set[str] = set()
    for value in normalized:
        _require_exact_type("input", value, ResearchTeamDomainMemoryCompactionHealthInput)
        _require_hard_flags(value)
        _reject_unsafe_public_surface("input", value)
        if value.team_domain in seen_domains:
            raise ValueError("inputs must use unique team_domain labels")
        seen_domains.add(value.team_domain)
    return normalized


def _normalize_rows(
    values: Iterable[ResearchTeamDomainMemoryCompactionHealthRow],
) -> tuple[ResearchTeamDomainMemoryCompactionHealthRow, ...]:
    if isinstance(values, (str, bytes)):
        raise ValueError("rows must contain ResearchTeamDomainMemoryCompactionHealthRow values")
    try:
        rows = tuple(values)
    except TypeError as exc:
        raise ValueError(
            "rows must contain ResearchTeamDomainMemoryCompactionHealthRow values",
        ) from exc
    for row in rows:
        _require_exact_type("row", row, ResearchTeamDomainMemoryCompactionHealthRow)
        _require_hard_flags(row)
        _reject_unsafe_public_surface("row", row)
    if rows != tuple(sorted(rows, key=_row_sort_key)):
        raise ValueError("rows must use deterministic sort")
    if len(set(row.team_domain for row in rows)) != len(rows):
        raise ValueError("rows must be unique")
    return rows


def _validate_row_consistency(
    row: ResearchTeamDomainMemoryCompactionHealthRow,
) -> None:
    if row.row_status != _status_from_reason_codes(row.reason_codes):
        raise ValueError("row_status must match reason_codes")


def _validate_report_consistency(
    report: ResearchTeamDomainMemoryCompactionHealthReport,
) -> None:
    if report.row_count != _decimal_count(len(report.rows)):
        raise ValueError("row_count must match rows")
    if report.domain_count != _decimal_count(len({row.team_domain for row in report.rows})):
        raise ValueError("domain_count must match rows")
    if report.pass_count != _status_count(report.rows, "pass"):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _status_count(report.rows, "watch"):
        raise ValueError("watch_count must match rows")
    if report.block_count != _status_count(report.rows, "block"):
        raise ValueError("block_count must match rows")
    if report.status != _report_status(report.rows):
        raise ValueError("status must match rows")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")
    if report.rows != tuple(sorted(report.rows, key=_row_sort_key)):
        raise ValueError("rows must be sorted")
    if report.average_domain_compaction_health_score != _average_score(
        tuple(row.domain_compaction_health_score for row in report.rows),
    ):
        raise ValueError("average_domain_compaction_health_score must match rows")


def _row_sort_key(
    row: ResearchTeamDomainMemoryCompactionHealthRow,
) -> tuple[int, Decimal, Decimal, Decimal, str]:
    return (
        _STATUS_RANK[row.row_status],
        row.domain_compaction_health_score,
        row.retrieval_coverage_ratio,
        -row.memory_age_seconds,
        row.team_domain,
    )


def _status_count(
    rows: tuple[ResearchTeamDomainMemoryCompactionHealthRow, ...],
    status: str,
) -> Decimal:
    return _decimal_count(sum(1 for row in rows if row.row_status == status))


def _count_if(
    rows: tuple[ResearchTeamDomainMemoryCompactionHealthRow, ...],
    predicate: Any,
) -> Decimal:
    return _decimal_count(sum(1 for row in rows if predicate(row)))


def _average_score(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return _ZERO
    with localcontext(_DECIMAL_CONTEXT):
        return _quantize(sum(values, _ZERO) / _decimal_count(len(values)))


def _seconds_between(start: datetime, end: datetime) -> Decimal:
    delta = end - start
    whole_seconds = Decimal(delta.days) * _SECONDS_PER_DAY + Decimal(delta.seconds)
    microseconds = Decimal(delta.microseconds) / _MICROSECONDS_PER_SECOND
    with localcontext(_DECIMAL_CONTEXT):
        return _quantize(whole_seconds + microseconds)


def _decimal_count(value: int) -> Decimal:
    return Decimal(value).quantize(_COUNT_QUANTUM)


def _normalize_reason_codes_preserving_sequence(value: Iterable[str]) -> tuple[str, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError("reason_codes must be an iterable of strings")
    try:
        normalized = tuple(value)
    except TypeError as exc:
        raise ValueError("reason_codes must be an iterable of strings") from exc
    if not normalized:
        raise ValueError("reason_codes must contain at least one value")
    if len(set(normalized)) != len(normalized):
        raise ValueError("reason_codes must not contain duplicates")
    for reason_code in normalized:
        _require_canonical_string("reason_codes", reason_code)
        if reason_code not in DOMAIN_MEMORY_COMPACTION_HEALTH_REASON_CODES:
            raise ValueError("reason_codes contains an unsupported value")
    return normalized


def _require_public_label(field_name: str, value: object) -> None:
    _require_canonical_string(field_name, value)
    lowered = value.lower()
    if any(fragment in lowered for fragment in _UNSAFE_PUBLIC_LABEL_FRAGMENTS):
        raise ValueError(f"{field_name} must be public-safe")


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")


def _require_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in DOMAIN_MEMORY_COMPACTION_HEALTH_STATUSES:
        raise ValueError(f"{field_name} must be pass, watch, or block")


def _normalize_count(field_name: str, value: object) -> Decimal:
    normalized = _normalize_decimal_with_quantum(field_name, value, _COUNT_QUANTUM)
    if normalized < _ZERO_COUNT:
        raise ValueError(f"{field_name} must be nonnegative")
    if normalized != value:
        raise ValueError(f"{field_name} must be a whole Decimal")
    return normalized


def _normalize_ratio(field_name: str, value: object) -> Decimal:
    normalized = _normalize_nonnegative_decimal(field_name, value)
    if normalized > _ONE:
        raise ValueError(f"{field_name} must be at most one")
    return normalized


def _normalize_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_decimal_with_quantum(field_name, value, _QUANTUM)
    if normalized < _ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _normalize_decimal_with_quantum(
    field_name: str,
    value: object,
    quantum: Decimal,
) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    with localcontext(_DECIMAL_CONTEXT):
        normalized = value.quantize(quantum)
    if normalized != value:
        if quantum == _COUNT_QUANTUM:
            raise ValueError(f"{field_name} must be a whole Decimal")
        raise ValueError(f"{field_name} must be quantized to 0.000001")
    return normalized


def _quantize(value: Decimal) -> Decimal:
    with localcontext(_DECIMAL_CONTEXT):
        return value.quantize(_QUANTUM)


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_exact_type(label: str, value: object, expected_type: type[object]) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{label} must be a {expected_type.__name__}")


def _require_hard_flags(value: object) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if getattr(value, field_name) is not True:
            raise ValueError(f"{field_name} must be True")


def _reject_unsafe_public_surface(label: str, value: object) -> None:
    for item in _surface_items(value):
        lowered = item.lower()
        if any(fragment in lowered for fragment in _UNSAFE_PUBLIC_LABEL_FRAGMENTS):
            raise ValueError(f"unsafe public-safe label in {label}")


def _surface_items(value: object) -> tuple[str, ...]:
    if is_dataclass(value) and not isinstance(value, type):
        items: list[str] = []
        for field in fields(value):
            items.append(field.name)
            items.extend(_surface_items(getattr(value, field.name)))
        return tuple(items)
    if isinstance(value, dict):
        items = []
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("public payload keys must be strings")
            items.append(key)
            items.extend(_surface_items(item))
        return tuple(items)
    if isinstance(value, (list, tuple)):
        items = []
        for item in value:
            items.extend(_surface_items(item))
        return tuple(items)
    if type(value) is str:
        return (value,)
    return ()


def _require_or_set_digest(value: object) -> None:
    current = getattr(value, _DIGEST_FIELD)
    if type(current) is not str:
        raise ValueError("derived_validation_digest must be a string")
    expected = _derived_digest(value)
    if current == "":
        object.__setattr__(value, _DIGEST_FIELD, expected)
        return
    if current != expected or not _is_sha256_hex(current):
        raise ValueError("derived_validation_digest does not match derived payload")


def _validate_payload_digest(payload: dict[str, Any]) -> None:
    current = payload.get(_DIGEST_FIELD)
    if type(current) is not str:
        raise ValueError("derived_validation_digest must be present")
    if current != _derived_digest(payload) or not _is_sha256_hex(current):
        raise ValueError("derived_validation_digest does not match derived payload")


def _derived_digest(value: object) -> str:
    canonical = _canonical_digest_value(value)
    encoded = json.dumps(canonical, separators=(",", ":"), sort_keys=True).encode("utf-8")
    return sha256(encoded).hexdigest()


def _is_sha256_hex(value: str) -> bool:
    return len(value) == 64 and all(character in "0123456789abcdef" for character in value)


def _canonical_digest_value(value: object) -> object:
    if value is None:
        return None
    if is_dataclass(value) and not isinstance(value, type):
        return {
            field.name: _canonical_digest_value(getattr(value, field.name))
            for field in fields(value)
            if field.name != _DIGEST_FIELD
        }
    if isinstance(value, Decimal):
        if not value.is_finite():
            raise ValueError("digest Decimal value must be finite")
        return str(value)
    if type(value) is datetime:
        return value.astimezone(UTC).isoformat()
    if type(value) in (str, bool):
        return value
    if isinstance(value, tuple):
        return [_canonical_digest_value(item) for item in value]
    if isinstance(value, list):
        return [_canonical_digest_value(item) for item in value]
    if isinstance(value, dict):
        result: dict[str, object] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("public payload keys must be strings")
            if key != _DIGEST_FIELD:
                result[key] = _canonical_digest_value(item)
        return result
    raise ValueError("unsupported digest value")


def _payload_value(value: object) -> Any:
    if value is None:
        return None
    if is_dataclass(value) and not isinstance(value, type):
        return {field.name: _payload_value(getattr(value, field.name)) for field in fields(value)}
    if isinstance(value, Decimal):
        if not value.is_finite():
            raise ValueError("public payload Decimal value must be finite")
        return str(value)
    if type(value) is datetime:
        return value.astimezone(UTC).isoformat()
    if type(value) in (str, bool):
        return value
    if isinstance(value, tuple):
        return [_payload_value(item) for item in value]
    if isinstance(value, list):
        return [_payload_value(item) for item in value]
    if isinstance(value, dict):
        result: dict[str, object] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("public payload keys must be strings")
            result[key] = _payload_value(item)
        return result
    raise ValueError("unsupported payload value")
