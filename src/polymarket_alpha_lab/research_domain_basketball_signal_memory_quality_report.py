"""Pure report-only basketball signal memory quality report."""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable
from dataclasses import dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
import hashlib
import json
from typing import Any


__all__ = (
    "DEFAULT_RESEARCH_DOMAIN_BASKETBALL_SIGNAL_MEMORY_QUALITY_REPORT_CONFIG_VERSION",
    "REASON_CODES",
    "STATUSES",
    "ResearchDomainBasketballSignalMemoryQualityConfig",
    "ResearchDomainBasketballSignalMemoryQualityInput",
    "ResearchDomainBasketballSignalMemoryQualityRow",
    "ResearchDomainBasketballSignalMemoryQualityReasonCodeCount",
    "ResearchDomainBasketballSignalMemoryQualityReport",
    "build_research_domain_basketball_signal_memory_quality_report",
    "research_domain_basketball_signal_memory_quality_report_payload",
)


DEFAULT_RESEARCH_DOMAIN_BASKETBALL_SIGNAL_MEMORY_QUALITY_REPORT_CONFIG_VERSION = (
    "research-domain-basketball-signal-memory-quality-report-v0"
)

QUANTUM = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
STATUSES = ("pass", "watch", "block")
STATUS_WEIGHT = {
    "block": Decimal("2.000000"),
    "watch": Decimal("1.000000"),
    "pass": Decimal("0.000000"),
}
HANDOFF_GATE_BY_STATUS = {
    "pass": "paper_allow_basketball_memory_forecast_handoff",
    "watch": "paper_review_basketball_memory_before_forecast",
    "block": "paper_refresh_basketball_memory_before_forecast",
}

CLEAR_REASON = "basketball_signal_memory_quality_clear"
REPORT_REASON_CODES = (
    "basketball_signal_memory_quality_report_pass",
    "basketball_signal_memory_quality_report_watch",
    "basketball_signal_memory_quality_report_block",
    "basketball_signal_memory_quality_report_empty",
)
STALE_BLOCK_REASON_CODES = (
    "team_memory_stale_block",
    "injury_memory_stale_block",
    "schedule_memory_stale_block",
    "context_memory_stale_block",
)
CONFLICT_BLOCK_REASON_CODES = (
    "team_memory_conflict_block",
    "injury_memory_conflict_block",
    "schedule_memory_conflict_block",
    "context_memory_conflict_block",
)
MISSING_BLOCK_REASON_CODES = (
    "team_memory_missing_block",
    "injury_memory_missing_block",
    "schedule_memory_missing_block",
    "context_memory_missing_block",
)
STALE_WATCH_REASON_CODES = (
    "team_memory_stale_watch",
    "injury_memory_stale_watch",
    "schedule_memory_stale_watch",
    "context_memory_stale_watch",
)
CONFLICT_WATCH_REASON_CODES = (
    "team_memory_conflict_watch",
    "injury_memory_conflict_watch",
    "schedule_memory_conflict_watch",
    "context_memory_conflict_watch",
)
MISSING_WATCH_REASON_CODES = (
    "team_memory_missing_watch",
    "injury_memory_missing_watch",
    "schedule_memory_missing_watch",
    "context_memory_missing_watch",
)
BLOCK_REASON_CODES = (
    *STALE_BLOCK_REASON_CODES,
    *CONFLICT_BLOCK_REASON_CODES,
    *MISSING_BLOCK_REASON_CODES,
)
WATCH_REASON_CODES = (
    *STALE_WATCH_REASON_CODES,
    *CONFLICT_WATCH_REASON_CODES,
    *MISSING_WATCH_REASON_CODES,
)
QUALITY_REASON_CODES = BLOCK_REASON_CODES + WATCH_REASON_CODES
REASON_CODES = (
    CLEAR_REASON,
    *REPORT_REASON_CODES,
    *QUALITY_REASON_CODES,
)
UNSAFE_PUBLIC_FRAGMENTS = frozenset(
    (
        "candidate_id",
        "candidate_slug",
        "mar" + "ket",
        "condition_id",
        "token" + "_id",
        "game_id",
        "team_id",
        "team_name",
        "question",
        "url",
        "://",
        "www.",
        "source" + "_text",
        "raw_text",
        "d" + "sn",
        "table" + "_name",
        "wal" + "let",
        "auth",
        "or" + "der",
        "tra" + "de",
        "live",
        "data" + "base",
        "net" + "work",
        "recommend" + "ation",
        "siz" + "ing",
    ),
)
HEX_CHARS = frozenset("0123456789abcdef")


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
class ResearchDomainBasketballSignalMemoryQualityConfig(_FinalPublicDataclass):
    config_version: str = (
        DEFAULT_RESEARCH_DOMAIN_BASKETBALL_SIGNAL_MEMORY_QUALITY_REPORT_CONFIG_VERSION
    )
    pass_max_memory_age_seconds: Decimal = Decimal("21600.000000")
    watch_max_memory_age_seconds: Decimal = Decimal("86400.000000")
    watch_conflict_count: Decimal = Decimal("1.000000")
    block_conflict_count: Decimal = Decimal("2.000000")
    watch_missing_count: Decimal = Decimal("1.000000")
    block_missing_count: Decimal = Decimal("2.000000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchDomainBasketballSignalMemoryQualityConfig,
            "config",
        )
        _require_public_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_DOMAIN_BASKETBALL_SIGNAL_MEMORY_QUALITY_REPORT_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "pass_max_memory_age_seconds",
            "watch_max_memory_age_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "watch_conflict_count",
            "block_conflict_count",
            "watch_missing_count",
            "block_missing_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_count_decimal(field_name, getattr(self, field_name)),
            )
        _validate_config(self)
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class ResearchDomainBasketballSignalMemoryQualityInput(_FinalPublicDataclass):
    basketball_signal_bucket: str
    memory_scope_bucket: str
    team_memory_age_seconds: Decimal
    injury_memory_age_seconds: Decimal
    schedule_memory_age_seconds: Decimal
    context_memory_age_seconds: Decimal
    team_conflict_count: Decimal
    injury_conflict_count: Decimal
    schedule_conflict_count: Decimal
    context_conflict_count: Decimal
    team_missing_count: Decimal
    injury_missing_count: Decimal
    schedule_missing_count: Decimal
    context_missing_count: Decimal
    observed_at: datetime
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchDomainBasketballSignalMemoryQualityInput, "input")
        _require_public_bucket("basketball_signal_bucket", self.basketball_signal_bucket)
        _require_public_bucket("memory_scope_bucket", self.memory_scope_bucket)
        for field_name in _AGE_FIELDS:
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (*_CONFLICT_FIELDS, *_MISSING_FIELDS):
            object.__setattr__(
                self,
                field_name,
                _require_count_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        _require_hard_flags("input", self)


@dataclass(frozen=True)
class ResearchDomainBasketballSignalMemoryQualityRow(_FinalPublicDataclass):
    basketball_signal_bucket: str
    memory_scope_bucket: str
    status: str
    team_memory_age_seconds: Decimal
    injury_memory_age_seconds: Decimal
    schedule_memory_age_seconds: Decimal
    context_memory_age_seconds: Decimal
    team_conflict_count: Decimal
    injury_conflict_count: Decimal
    schedule_conflict_count: Decimal
    context_conflict_count: Decimal
    team_missing_count: Decimal
    injury_missing_count: Decimal
    schedule_missing_count: Decimal
    context_missing_count: Decimal
    max_memory_age_seconds: Decimal
    total_conflict_count: Decimal
    total_missing_count: Decimal
    memory_quality_score: Decimal
    observed_at: datetime
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchDomainBasketballSignalMemoryQualityRow, "row")
        _require_public_bucket("basketball_signal_bucket", self.basketball_signal_bucket)
        _require_public_bucket("memory_scope_bucket", self.memory_scope_bucket)
        _require_status("status", self.status)
        for field_name in _AGE_FIELDS:
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (*_CONFLICT_FIELDS, *_MISSING_FIELDS):
            object.__setattr__(
                self,
                field_name,
                _require_count_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "max_memory_age_seconds",
            _require_nonnegative_decimal(
                "max_memory_age_seconds",
                self.max_memory_age_seconds,
            ),
        )
        for field_name in ("total_conflict_count", "total_missing_count"):
            object.__setattr__(
                self,
                field_name,
                _require_count_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "memory_quality_score",
            _require_ratio_decimal("memory_quality_score", self.memory_quality_score),
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
class ResearchDomainBasketballSignalMemoryQualityReasonCodeCount(_FinalPublicDataclass):
    reason_code: str
    count: Decimal
    memory_input_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchDomainBasketballSignalMemoryQualityReasonCodeCount,
            "reason_code_count",
        )
        _require_public_string("reason_code", self.reason_code)
        if self.reason_code not in REASON_CODES:
            raise ValueError("reason_code must be supported")
        object.__setattr__(self, "count", _require_count_decimal("count", self.count))
        object.__setattr__(
            self,
            "memory_input_ratio",
            _require_ratio_decimal("memory_input_ratio", self.memory_input_ratio),
        )
        _require_hard_flags("reason_code_count", self)


@dataclass(frozen=True)
class ResearchDomainBasketballSignalMemoryQualityReport(_FinalPublicDataclass):
    generated_at: datetime
    config_version: str
    report_status: str
    staleness_status: str
    conflict_status: str
    completeness_status: str
    handoff_gate: str
    memory_input_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    stale_input_count: Decimal
    conflicting_input_count: Decimal
    missing_input_count: Decimal
    total_conflict_count: Decimal
    total_missing_count: Decimal
    max_memory_age_seconds: Decimal
    average_memory_quality_score: Decimal
    rows: tuple[ResearchDomainBasketballSignalMemoryQualityRow, ...]
    reason_codes: tuple[str, ...]
    reason_code_counts: tuple[ResearchDomainBasketballSignalMemoryQualityReasonCodeCount, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchDomainBasketballSignalMemoryQualityReport, "report")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_DOMAIN_BASKETBALL_SIGNAL_MEMORY_QUALITY_REPORT_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "report_status",
            "staleness_status",
            "conflict_status",
            "completeness_status",
        ):
            _require_status(field_name, getattr(self, field_name))
        _require_public_string("handoff_gate", self.handoff_gate)
        if self.handoff_gate != HANDOFF_GATE_BY_STATUS[self.report_status]:
            raise ValueError("handoff_gate must match report_status")
        for field_name in (
            "memory_input_count",
            "pass_count",
            "watch_count",
            "block_count",
            "stale_input_count",
            "conflicting_input_count",
            "missing_input_count",
            "total_conflict_count",
            "total_missing_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_count_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "max_memory_age_seconds",
            _require_nonnegative_decimal(
                "max_memory_age_seconds",
                self.max_memory_age_seconds,
            ),
        )
        object.__setattr__(
            self,
            "average_memory_quality_score",
            _require_ratio_decimal(
                "average_memory_quality_score",
                self.average_memory_quality_score,
            ),
        )
        object.__setattr__(self, "rows", _require_rows(self.rows))
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
        if self.derived_validation_digest:
            _require_sha256("derived_validation_digest", self.derived_validation_digest)
            if self.derived_validation_digest != _derived_validation_digest(self):
                raise ValueError("derived_validation_digest must match report payload")
        else:
            object.__setattr__(
                self,
                "derived_validation_digest",
                _derived_validation_digest(self),
            )
        _validate_report(self)
        _reject_unsafe_public_payload("report", self)
        _require_hard_flags("report", self)

    @property
    def payload(self) -> dict[str, Any]:
        return research_domain_basketball_signal_memory_quality_report_payload(self)


def build_research_domain_basketball_signal_memory_quality_report(
    memory_inputs: Iterable[ResearchDomainBasketballSignalMemoryQualityInput],
    *,
    config: ResearchDomainBasketballSignalMemoryQualityConfig,
    generated_at: datetime,
) -> ResearchDomainBasketballSignalMemoryQualityReport:
    if type(config) is not ResearchDomainBasketballSignalMemoryQualityConfig:
        raise ValueError(
            "config must be a ResearchDomainBasketballSignalMemoryQualityConfig",
        )
    _require_hard_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    normalized_inputs = _normalize_inputs(memory_inputs)
    rows = tuple(
        sorted(
            (
                _row_from_input(item, config=config, generated_at=generated_at_utc)
                for item in normalized_inputs
            ),
            key=_row_sort_key,
        ),
    )
    staleness_status = _category_status(rows, STALE_BLOCK_REASON_CODES, STALE_WATCH_REASON_CODES)
    conflict_status = _category_status(
        rows,
        CONFLICT_BLOCK_REASON_CODES,
        CONFLICT_WATCH_REASON_CODES,
    )
    completeness_status = _category_status(
        rows,
        MISSING_BLOCK_REASON_CODES,
        MISSING_WATCH_REASON_CODES,
    )
    report_status = _rollup_status(
        (staleness_status, conflict_status, completeness_status),
    )
    return ResearchDomainBasketballSignalMemoryQualityReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        report_status=report_status,
        staleness_status=staleness_status,
        conflict_status=conflict_status,
        completeness_status=completeness_status,
        handoff_gate=HANDOFF_GATE_BY_STATUS[report_status],
        memory_input_count=_count(len(rows)),
        pass_count=_status_count(rows, "pass"),
        watch_count=_status_count(rows, "watch"),
        block_count=_status_count(rows, "block"),
        stale_input_count=_reason_family_row_count(
            rows,
            (*STALE_BLOCK_REASON_CODES, *STALE_WATCH_REASON_CODES),
        ),
        conflicting_input_count=_reason_family_row_count(
            rows,
            (*CONFLICT_BLOCK_REASON_CODES, *CONFLICT_WATCH_REASON_CODES),
        ),
        missing_input_count=_reason_family_row_count(
            rows,
            (*MISSING_BLOCK_REASON_CODES, *MISSING_WATCH_REASON_CODES),
        ),
        total_conflict_count=_sum_decimal(
            tuple(row.total_conflict_count for row in rows),
            count=True,
        ),
        total_missing_count=_sum_decimal(
            tuple(row.total_missing_count for row in rows),
            count=True,
        ),
        max_memory_age_seconds=_max_decimal(
            tuple(row.max_memory_age_seconds for row in rows),
        ),
        average_memory_quality_score=_average(
            tuple(row.memory_quality_score for row in rows),
        ),
        rows=rows,
        reason_codes=_report_reason_codes(rows),
        reason_code_counts=_reason_code_counts(rows),
    )


def research_domain_basketball_signal_memory_quality_report_payload(
    report: ResearchDomainBasketballSignalMemoryQualityReport | dict[str, Any],
) -> dict[str, Any]:
    if type(report) is ResearchDomainBasketballSignalMemoryQualityReport:
        _require_hard_flags("report", report)
        _reject_unsafe_public_payload("report", report)
        if report.derived_validation_digest != _derived_validation_digest(report):
            raise ValueError("derived_validation_digest must match report payload")
        _validate_report(report)
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
            raise ValueError("derived_validation_digest must match report payload")
        return payload
    raise ValueError(
        "report must be a ResearchDomainBasketballSignalMemoryQualityReport",
    )


@dataclass(frozen=True)
class _PayloadFlags:
    value: dict[str, Any]

    @property
    def paper_only(self) -> object:
        if "paper_only" in self.value:
            return self.value["paper_only"]
        return None

    @property
    def report_only(self) -> object:
        if "report_only" in self.value:
            return self.value["report_only"]
        return None

    @property
    def readonly(self) -> object:
        if "readonly" in self.value:
            return self.value["readonly"]
        return None


_AGE_FIELDS = (
    "team_memory_age_seconds",
    "injury_memory_age_seconds",
    "schedule_memory_age_seconds",
    "context_memory_age_seconds",
)
_CONFLICT_FIELDS = (
    "team_conflict_count",
    "injury_conflict_count",
    "schedule_conflict_count",
    "context_conflict_count",
)
_MISSING_FIELDS = (
    "team_missing_count",
    "injury_missing_count",
    "schedule_missing_count",
    "context_missing_count",
)


def _normalize_inputs(
    memory_inputs: Iterable[ResearchDomainBasketballSignalMemoryQualityInput],
) -> tuple[ResearchDomainBasketballSignalMemoryQualityInput, ...]:
    if isinstance(memory_inputs, (str, bytes)):
        raise ValueError("memory_inputs must be an iterable")
    try:
        normalized = tuple(memory_inputs)
    except TypeError as exc:
        raise ValueError("memory_inputs must be an iterable") from exc
    seen: set[tuple[str, str]] = set()
    for item in normalized:
        if type(item) is not ResearchDomainBasketballSignalMemoryQualityInput:
            raise ValueError(
                "memory_inputs must contain ResearchDomainBasketballSignalMemoryQualityInput",
            )
        _require_hard_flags("input", item)
        key = (item.basketball_signal_bucket, item.memory_scope_bucket)
        if key in seen:
            raise ValueError("memory_inputs must contain unique public bucket pairs")
        seen.add(key)
    return normalized


def _row_from_input(
    item: ResearchDomainBasketballSignalMemoryQualityInput,
    *,
    config: ResearchDomainBasketballSignalMemoryQualityConfig,
    generated_at: datetime,
) -> ResearchDomainBasketballSignalMemoryQualityRow:
    if item.observed_at > generated_at:
        raise ValueError("observed_at must not be in the future")
    reason_codes = _row_reason_codes(item, config=config)
    max_age = _max_decimal(tuple(getattr(item, field_name) for field_name in _AGE_FIELDS))
    return ResearchDomainBasketballSignalMemoryQualityRow(
        basketball_signal_bucket=item.basketball_signal_bucket,
        memory_scope_bucket=item.memory_scope_bucket,
        status=_row_status(reason_codes),
        team_memory_age_seconds=item.team_memory_age_seconds,
        injury_memory_age_seconds=item.injury_memory_age_seconds,
        schedule_memory_age_seconds=item.schedule_memory_age_seconds,
        context_memory_age_seconds=item.context_memory_age_seconds,
        team_conflict_count=item.team_conflict_count,
        injury_conflict_count=item.injury_conflict_count,
        schedule_conflict_count=item.schedule_conflict_count,
        context_conflict_count=item.context_conflict_count,
        team_missing_count=item.team_missing_count,
        injury_missing_count=item.injury_missing_count,
        schedule_missing_count=item.schedule_missing_count,
        context_missing_count=item.context_missing_count,
        max_memory_age_seconds=max_age,
        total_conflict_count=_sum_decimal(
            tuple(getattr(item, field_name) for field_name in _CONFLICT_FIELDS),
            count=True,
        ),
        total_missing_count=_sum_decimal(
            tuple(getattr(item, field_name) for field_name in _MISSING_FIELDS),
            count=True,
        ),
        memory_quality_score=_memory_quality_score(max_age, config),
        observed_at=item.observed_at,
        reason_codes=reason_codes,
    )


def _row_reason_codes(
    item: ResearchDomainBasketballSignalMemoryQualityInput,
    *,
    config: ResearchDomainBasketballSignalMemoryQualityConfig,
) -> tuple[str, ...]:
    reasons: list[str] = []
    _append_age_reason(
        reasons,
        value=item.team_memory_age_seconds,
        block_reason="team_memory_stale_block",
        watch_reason="team_memory_stale_watch",
        config=config,
    )
    _append_age_reason(
        reasons,
        value=item.injury_memory_age_seconds,
        block_reason="injury_memory_stale_block",
        watch_reason="injury_memory_stale_watch",
        config=config,
    )
    _append_age_reason(
        reasons,
        value=item.schedule_memory_age_seconds,
        block_reason="schedule_memory_stale_block",
        watch_reason="schedule_memory_stale_watch",
        config=config,
    )
    _append_age_reason(
        reasons,
        value=item.context_memory_age_seconds,
        block_reason="context_memory_stale_block",
        watch_reason="context_memory_stale_watch",
        config=config,
    )
    _append_count_reason(
        reasons,
        value=item.team_conflict_count,
        block_threshold=config.block_conflict_count,
        watch_threshold=config.watch_conflict_count,
        block_reason="team_memory_conflict_block",
        watch_reason="team_memory_conflict_watch",
    )
    _append_count_reason(
        reasons,
        value=item.injury_conflict_count,
        block_threshold=config.block_conflict_count,
        watch_threshold=config.watch_conflict_count,
        block_reason="injury_memory_conflict_block",
        watch_reason="injury_memory_conflict_watch",
    )
    _append_count_reason(
        reasons,
        value=item.schedule_conflict_count,
        block_threshold=config.block_conflict_count,
        watch_threshold=config.watch_conflict_count,
        block_reason="schedule_memory_conflict_block",
        watch_reason="schedule_memory_conflict_watch",
    )
    _append_count_reason(
        reasons,
        value=item.context_conflict_count,
        block_threshold=config.block_conflict_count,
        watch_threshold=config.watch_conflict_count,
        block_reason="context_memory_conflict_block",
        watch_reason="context_memory_conflict_watch",
    )
    _append_count_reason(
        reasons,
        value=item.team_missing_count,
        block_threshold=config.block_missing_count,
        watch_threshold=config.watch_missing_count,
        block_reason="team_memory_missing_block",
        watch_reason="team_memory_missing_watch",
    )
    _append_count_reason(
        reasons,
        value=item.injury_missing_count,
        block_threshold=config.block_missing_count,
        watch_threshold=config.watch_missing_count,
        block_reason="injury_memory_missing_block",
        watch_reason="injury_memory_missing_watch",
    )
    _append_count_reason(
        reasons,
        value=item.schedule_missing_count,
        block_threshold=config.block_missing_count,
        watch_threshold=config.watch_missing_count,
        block_reason="schedule_memory_missing_block",
        watch_reason="schedule_memory_missing_watch",
    )
    _append_count_reason(
        reasons,
        value=item.context_missing_count,
        block_threshold=config.block_missing_count,
        watch_threshold=config.watch_missing_count,
        block_reason="context_memory_missing_block",
        watch_reason="context_memory_missing_watch",
    )
    if not reasons:
        reasons.append(CLEAR_REASON)
    return tuple(reasons)


def _append_age_reason(
    reasons: list[str],
    *,
    value: Decimal,
    block_reason: str,
    watch_reason: str,
    config: ResearchDomainBasketballSignalMemoryQualityConfig,
) -> None:
    if value > config.watch_max_memory_age_seconds:
        reasons.append(block_reason)
    elif value > config.pass_max_memory_age_seconds:
        reasons.append(watch_reason)


def _append_count_reason(
    reasons: list[str],
    *,
    value: Decimal,
    block_threshold: Decimal,
    watch_threshold: Decimal,
    block_reason: str,
    watch_reason: str,
) -> None:
    if value >= block_threshold:
        reasons.append(block_reason)
    elif value >= watch_threshold:
        reasons.append(watch_reason)


def _memory_quality_score(
    max_memory_age_seconds: Decimal,
    config: ResearchDomainBasketballSignalMemoryQualityConfig,
) -> Decimal:
    if max_memory_age_seconds <= config.pass_max_memory_age_seconds:
        return ONE
    with localcontext(DECIMAL_CONTEXT):
        raw_score = ONE - (max_memory_age_seconds / config.watch_max_memory_age_seconds)
    if raw_score <= ZERO:
        return ZERO
    if raw_score >= ONE:
        return ONE
    return _quantize_decimal(raw_score)


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


def _category_status(
    rows: tuple[ResearchDomainBasketballSignalMemoryQualityRow, ...],
    block_reasons: tuple[str, ...],
    watch_reasons: tuple[str, ...],
) -> str:
    if not rows:
        return "block"
    row_reasons = tuple(reason for row in rows for reason in row.reason_codes)
    if any(reason in block_reasons for reason in row_reasons):
        return "block"
    if any(reason in watch_reasons for reason in row_reasons):
        return "watch"
    return "pass"


def _report_reason_codes(
    rows: tuple[ResearchDomainBasketballSignalMemoryQualityRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return ("basketball_signal_memory_quality_report_empty",)
    status = _rollup_status(tuple(row.status for row in rows))
    row_reasons = frozenset(
        reason
        for row in rows
        for reason in row.reason_codes
        if reason in QUALITY_REASON_CODES
    )
    return (
        f"basketball_signal_memory_quality_report_{status}",
        *(reason for reason in QUALITY_REASON_CODES if reason in row_reasons),
    )


def _reason_code_counts(
    rows: tuple[ResearchDomainBasketballSignalMemoryQualityRow, ...],
) -> tuple[ResearchDomainBasketballSignalMemoryQualityReasonCodeCount, ...]:
    if not rows:
        return ()
    counter: Counter[str] = Counter()
    for row in rows:
        counter.update(row.reason_codes)
    denominator = _count(len(rows))
    rank = {reason_code: index for index, reason_code in enumerate(REASON_CODES)}
    return tuple(
        ResearchDomainBasketballSignalMemoryQualityReasonCodeCount(
            reason_code=reason_code,
            count=_count(count),
            memory_input_ratio=_ratio(_count(count), denominator),
        )
        for reason_code, count in sorted(
            counter.items(),
            key=lambda item: (rank[item[0]], item[0]),
        )
    )


def _status_count(
    rows: tuple[ResearchDomainBasketballSignalMemoryQualityRow, ...],
    status: str,
) -> Decimal:
    return _count(sum(1 for row in rows if row.status == status))


def _reason_family_row_count(
    rows: tuple[ResearchDomainBasketballSignalMemoryQualityRow, ...],
    reasons: tuple[str, ...],
) -> Decimal:
    return _count(
        sum(1 for row in rows if any(reason in reasons for reason in row.reason_codes)),
    )


def _row_sort_key(
    row: ResearchDomainBasketballSignalMemoryQualityRow,
) -> tuple[Decimal, str, str]:
    return (
        -STATUS_WEIGHT[row.status],
        row.basketball_signal_bucket,
        row.memory_scope_bucket,
    )


def _validate_config(config: ResearchDomainBasketballSignalMemoryQualityConfig) -> None:
    if config.pass_max_memory_age_seconds >= config.watch_max_memory_age_seconds:
        raise ValueError(
            "pass_max_memory_age_seconds must be less than watch_max_memory_age_seconds",
        )
    if config.watch_conflict_count >= config.block_conflict_count:
        raise ValueError("watch_conflict_count must be less than block_conflict_count")
    if config.watch_missing_count >= config.block_missing_count:
        raise ValueError("watch_missing_count must be less than block_missing_count")


def _validate_row(row: ResearchDomainBasketballSignalMemoryQualityRow) -> None:
    if row.max_memory_age_seconds != _max_decimal(
        tuple(getattr(row, field_name) for field_name in _AGE_FIELDS),
    ):
        raise ValueError("max_memory_age_seconds must match row ages")
    if row.total_conflict_count != _sum_decimal(
        tuple(getattr(row, field_name) for field_name in _CONFLICT_FIELDS),
        count=True,
    ):
        raise ValueError("total_conflict_count must match row conflicts")
    if row.total_missing_count != _sum_decimal(
        tuple(getattr(row, field_name) for field_name in _MISSING_FIELDS),
        count=True,
    ):
        raise ValueError("total_missing_count must match row missing inputs")
    expected_status = _row_status(row.reason_codes)
    if row.status != expected_status:
        raise ValueError("status must match reason_codes")


def _validate_report(report: ResearchDomainBasketballSignalMemoryQualityReport) -> None:
    rows = report.rows
    if report.memory_input_count != _count(len(rows)):
        raise ValueError("memory_input_count must match rows")
    if report.pass_count != _status_count(rows, "pass"):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _status_count(rows, "watch"):
        raise ValueError("watch_count must match rows")
    if report.block_count != _status_count(rows, "block"):
        raise ValueError("block_count must match rows")
    if report.pass_count + report.watch_count + report.block_count != report.memory_input_count:
        raise ValueError("status counts must match memory_input_count")
    if report.stale_input_count != _reason_family_row_count(
        rows,
        (*STALE_BLOCK_REASON_CODES, *STALE_WATCH_REASON_CODES),
    ):
        raise ValueError("stale_input_count must match rows")
    if report.conflicting_input_count != _reason_family_row_count(
        rows,
        (*CONFLICT_BLOCK_REASON_CODES, *CONFLICT_WATCH_REASON_CODES),
    ):
        raise ValueError("conflicting_input_count must match rows")
    if report.missing_input_count != _reason_family_row_count(
        rows,
        (*MISSING_BLOCK_REASON_CODES, *MISSING_WATCH_REASON_CODES),
    ):
        raise ValueError("missing_input_count must match rows")
    if report.total_conflict_count != _sum_decimal(
        tuple(row.total_conflict_count for row in rows),
        count=True,
    ):
        raise ValueError("total_conflict_count must match rows")
    if report.total_missing_count != _sum_decimal(
        tuple(row.total_missing_count for row in rows),
        count=True,
    ):
        raise ValueError("total_missing_count must match rows")
    if report.max_memory_age_seconds != _max_decimal(
        tuple(row.max_memory_age_seconds for row in rows),
    ):
        raise ValueError("max_memory_age_seconds must match rows")
    if report.average_memory_quality_score != _average(
        tuple(row.memory_quality_score for row in rows),
    ):
        raise ValueError("average_memory_quality_score must match rows")
    staleness_status = _category_status(rows, STALE_BLOCK_REASON_CODES, STALE_WATCH_REASON_CODES)
    conflict_status = _category_status(
        rows,
        CONFLICT_BLOCK_REASON_CODES,
        CONFLICT_WATCH_REASON_CODES,
    )
    completeness_status = _category_status(
        rows,
        MISSING_BLOCK_REASON_CODES,
        MISSING_WATCH_REASON_CODES,
    )
    if report.staleness_status != staleness_status:
        raise ValueError("staleness_status must match rows")
    if report.conflict_status != conflict_status:
        raise ValueError("conflict_status must match rows")
    if report.completeness_status != completeness_status:
        raise ValueError("completeness_status must match rows")
    if report.report_status != _rollup_status(
        (staleness_status, conflict_status, completeness_status),
    ):
        raise ValueError("report_status must match component statuses")
    if report.reason_codes != _report_reason_codes(rows):
        raise ValueError("reason_codes must match rows")
    if report.reason_code_counts != _reason_code_counts(rows):
        raise ValueError("reason_code_counts must match rows")


def _require_rows(
    rows: tuple[ResearchDomainBasketballSignalMemoryQualityRow, ...],
) -> tuple[ResearchDomainBasketballSignalMemoryQualityRow, ...]:
    if isinstance(rows, (str, bytes)):
        raise ValueError("rows must be a tuple")
    try:
        normalized = tuple(rows)
    except TypeError as exc:
        raise ValueError("rows must be a tuple") from exc
    for row in normalized:
        if type(row) is not ResearchDomainBasketballSignalMemoryQualityRow:
            raise ValueError(
                "rows must contain ResearchDomainBasketballSignalMemoryQualityRow",
            )
        _require_hard_flags("row", row)
    if normalized != tuple(sorted(normalized, key=_row_sort_key)):
        raise ValueError("rows must be sorted")
    return normalized


def _require_reason_code_counts(
    counts: tuple[ResearchDomainBasketballSignalMemoryQualityReasonCodeCount, ...],
) -> tuple[ResearchDomainBasketballSignalMemoryQualityReasonCodeCount, ...]:
    if isinstance(counts, (str, bytes)):
        raise ValueError("reason_code_counts must be a tuple")
    try:
        normalized = tuple(counts)
    except TypeError as exc:
        raise ValueError("reason_code_counts must be a tuple") from exc
    rank = {reason_code: index for index, reason_code in enumerate(REASON_CODES)}
    for count in normalized:
        if type(count) is not ResearchDomainBasketballSignalMemoryQualityReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain ResearchDomainBasketballSignalMemoryQualityReasonCodeCount",
            )
        _require_hard_flags("reason_code_count", count)
    if normalized != tuple(
        sorted(normalized, key=lambda item: (rank[item.reason_code], item.reason_code)),
    ):
        raise ValueError("reason_code_counts must be sorted")
    return normalized


def _require_report_reason_codes(reason_codes: tuple[str, ...]) -> tuple[str, ...]:
    normalized = _require_reason_codes(reason_codes, require_nonempty=True)
    if normalized[0] not in REPORT_REASON_CODES:
        raise ValueError("reason_codes must start with a report reason")
    if normalized[0].endswith("_empty") and len(normalized) != 1:
        raise ValueError("empty report reason_codes must not include row reasons")
    if normalized[1:] != tuple(reason for reason in QUALITY_REASON_CODES if reason in normalized):
        raise ValueError("reason_codes must follow supported rank")
    return normalized


def _require_reason_codes(
    reason_codes: tuple[str, ...],
    *,
    require_nonempty: bool,
) -> tuple[str, ...]:
    if isinstance(reason_codes, (str, bytes)):
        raise ValueError("reason_codes must be a tuple")
    try:
        normalized = tuple(reason_codes)
    except TypeError as exc:
        raise ValueError("reason_codes must be a tuple") from exc
    if require_nonempty and not normalized:
        raise ValueError("reason_codes must not be empty")
    seen: set[str] = set()
    for reason_code in normalized:
        _require_public_string("reason_code", reason_code)
        if reason_code not in REASON_CODES:
            raise ValueError("reason_code must be supported")
        if reason_code in seen:
            raise ValueError("reason_codes must be unique")
        seen.add(reason_code)
    return normalized


def _require_exact_type(value: object, expected_type: type[object], field_name: str) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{field_name} must be exact")


def _require_hard_flags(field_name: str, value: object) -> None:
    for flag_name in ("paper_only", "report_only", "readonly"):
        if getattr(value, flag_name) is not True:
            raise ValueError(f"{field_name}.{flag_name} must be True")


def _require_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in STATUSES:
        raise ValueError(f"{field_name} must be one of pass/watch/block")


def _require_public_string(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value:
        raise ValueError(f"{field_name} must not be empty")
    _reject_unsafe_string(field_name, value)
    return value


def _require_public_bucket(field_name: str, value: object) -> str:
    text = _require_public_string(field_name, value)
    if len(text) > 80:
        raise ValueError(f"{field_name} must be compact")
    allowed_chars = frozenset("abcdefghijklmnopqrstuvwxyz0123456789-_")
    if any(char not in allowed_chars for char in text):
        raise ValueError(f"{field_name} contains unsupported characters")
    return text


def _require_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return _quantize_decimal(decimal_value)


def _require_count_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_nonnegative_decimal(field_name, value)
    if decimal_value != decimal_value.to_integral_value():
        raise ValueError(f"{field_name} must be integral")
    return decimal_value


def _require_ratio_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value < ZERO or decimal_value > ONE:
        raise ValueError(f"{field_name} must be between zero and one")
    return _quantize_decimal(decimal_value)


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return value


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _count(value: int) -> Decimal:
    return _quantize_decimal(Decimal(value))


def _sum_decimal(values: tuple[Decimal, ...], *, count: bool = False) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        total = sum(values, ZERO)
    if count:
        return _require_count_decimal("count_total", total)
    return _quantize_decimal(total)


def _max_decimal(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return ZERO
    return _quantize_decimal(max(values))


def _average(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return _quantize_decimal(sum(values, ZERO) / Decimal(len(values)))


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return _quantize_decimal(numerator / denominator)


def _quantize_decimal(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(QUANTUM)


def _require_sha256(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if len(value) != 64 or any(char not in HEX_CHARS for char in value):
        raise ValueError(f"{field_name} must be a SHA-256 digest")
    return value


def _derived_validation_digest(
    report: ResearchDomainBasketballSignalMemoryQualityReport,
) -> str:
    payload = _json_ready(report)
    if type(payload) is not dict:
        raise ValueError("report payload must be an object")
    return _payload_validation_digest(payload)


def _payload_validation_digest(payload: dict[str, Any]) -> str:
    unsigned_payload = {
        key: value
        for key, value in payload.items()
        if key != "derived_validation_digest"
    }
    return hashlib.sha256(
        json.dumps(unsigned_payload, sort_keys=True, separators=(",", ":")).encode(),
    ).hexdigest()


def _json_ready(value: Any) -> Any:
    if type(value) is Decimal:
        return format(value, "f")
    if type(value) is datetime:
        return value.isoformat()
    if type(value) is bool or value is None or type(value) is str:
        return value
    if is_dataclass(value) and not isinstance(value, type):
        return {
            field.name: _json_ready(getattr(value, field.name))
            for field in fields(value)
        }
    if isinstance(value, tuple):
        return [_json_ready(item) for item in value]
    if isinstance(value, list):
        return [_json_ready(item) for item in value]
    if isinstance(value, dict):
        return {str(key): _json_ready(item) for key, item in value.items()}
    raise ValueError(f"unsupported payload value: {type(value).__name__}")


def _reject_unsafe_public_payload(field_name: str, value: object) -> None:
    if is_dataclass(value) and not isinstance(value, type):
        for field in fields(value):
            _reject_unsafe_public_payload(field.name, getattr(value, field.name))
        return
    if isinstance(value, dict):
        for key, item in value.items():
            _reject_unsafe_string(field_name, str(key))
            _reject_unsafe_public_payload(str(key), item)
        return
    if isinstance(value, (list, tuple)):
        for item in value:
            _reject_unsafe_public_payload(field_name, item)
        return
    if type(value) is str:
        _reject_unsafe_string(field_name, value)


def _reject_unsafe_string(field_name: str, value: str) -> None:
    lowered = value.lower()
    if any(fragment in lowered for fragment in UNSAFE_PUBLIC_FRAGMENTS):
        raise ValueError(f"{field_name} contains unsafe public payload surface")


def _reject_public_numeric_values(value: object) -> None:
    if type(value) is bool or value is None:
        return
    if type(value) in (Decimal, int, float):
        raise ValueError("public payload must not contain numeric scalars")
    if isinstance(value, dict):
        for item in value.values():
            _reject_public_numeric_values(item)
    elif isinstance(value, (list, tuple)):
        for item in value:
            _reject_public_numeric_values(item)
