"""Public-safe specialist team coverage map report reducer."""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable, Mapping
from dataclasses import asdict, dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, InvalidOperation, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
import json
import re
from typing import Any

from polymarket_alpha_lab.team_paper_guard import require_paper_only_flags


DEFAULT_RESEARCH_TEAM_SPECIALIST_COVERAGE_MAP_REPORT_CONFIG_VERSION = (
    "research-team-specialist-coverage-map-report-v0"
)
COVERAGE_MAP_STATUSES = ("pass", "watch", "block")
COVERAGE_MAP_DOMAINS = (
    "politics",
    "crypto",
    "equities",
    "commodities",
    "football",
    "basketball",
    "other",
)

QUANTUM = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
SECONDS_PER_HOUR = Decimal("3600.000000")
MICROSECONDS_PER_SECOND = Decimal("1000000")
PUBLIC_LABEL_RE = re.compile(r"^[a-z0-9][a-z0-9_.-]{0,127}$")
HEX_CHARS = frozenset("0123456789abcdef")

PAPER_ACTION_BY_STATUS = {
    "pass": "paper_specialist_coverage_map_monitor",
    "watch": "paper_specialist_coverage_map_watch",
    "block": "paper_specialist_coverage_map_block",
}

REPORT_REASON_BY_STATUS = {
    "pass": "specialist_coverage_report_pass",
    "watch": "specialist_coverage_report_watch",
    "block": "specialist_coverage_report_block",
}

MISSING_BLOCK_REASON = "specialist_coverage_missing_block"
DEPTH_BLOCK_REASON = "specialist_coverage_depth_block"
MEMORY_STALE_BLOCK_REASON = "specialist_coverage_memory_stale_block"
OVERLOAD_BLOCK_REASON = "specialist_coverage_overload_block"
CALIBRATION_BLOCK_REASON = "specialist_coverage_calibration_block"
CONFIDENCE_BLOCK_REASON = "specialist_coverage_confidence_block"
DEPTH_WATCH_REASON = "specialist_coverage_depth_watch"
MEMORY_STALE_WATCH_REASON = "specialist_coverage_memory_stale_watch"
OVERLOAD_WATCH_REASON = "specialist_coverage_overload_watch"
CALIBRATION_WATCH_REASON = "specialist_coverage_calibration_watch"
CONFIDENCE_WATCH_REASON = "specialist_coverage_confidence_watch"
PASS_REASON = "specialist_coverage_clear"

BLOCK_REASON_CODES = (
    MISSING_BLOCK_REASON,
    DEPTH_BLOCK_REASON,
    MEMORY_STALE_BLOCK_REASON,
    OVERLOAD_BLOCK_REASON,
    CALIBRATION_BLOCK_REASON,
    CONFIDENCE_BLOCK_REASON,
)
WATCH_REASON_CODES = (
    DEPTH_WATCH_REASON,
    MEMORY_STALE_WATCH_REASON,
    OVERLOAD_WATCH_REASON,
    CALIBRATION_WATCH_REASON,
    CONFIDENCE_WATCH_REASON,
)
ROW_REASON_CODES = BLOCK_REASON_CODES + WATCH_REASON_CODES + (PASS_REASON,)
REPORT_REASON_CODES = (
    REPORT_REASON_BY_STATUS["pass"],
    REPORT_REASON_BY_STATUS["watch"],
    REPORT_REASON_BY_STATUS["block"],
    *ROW_REASON_CODES,
)


def _join_parts(*parts: str) -> str:
    return "".join(parts)


UNSAFE_LABEL_FRAGMENTS = frozenset(
    (
        "candidate",
        _join_parts("mar", "ket"),
        "slug",
        "question",
        "raw",
        "http",
        "url",
        "dsn",
        _join_parts("tab", "le"),
        "token",
        "secret",
        "credential",
        "auth",
        "api_key",
        "database",
        "network",
        "request",
        "endpoint",
        "execute",
        "execution",
        "sizing",
        "recommend",
        _join_parts("wal", "let"),
        _join_parts("ord", "er"),
        _join_parts("tra", "de"),
        "trading",
        _join_parts("li", "ve"),
        _join_parts("b", "uy"),
        _join_parts("s", "ell"),
    ),
)
UNSAFE_PAYLOAD_KEYS = frozenset(
    (
        "candidate_id",
        "candidate_key",
        "market_id",
        "market_slug",
        "condition_id",
        "question",
        "source_url",
        "source_text",
        "raw_source",
        "dsn",
        "table",
        "token",
        "secret",
        "credential",
        "api_key",
        "auth",
        "auth_header",
        "authorization",
        "authorization_header",
        "database",
        "network",
        "request",
        "endpoint",
        "execution",
        "execution_endpoint",
        "wallet",
        "order",
        "order_ticket",
        "trade",
        "trading",
        "sizing",
        "recommend",
        "recommendation",
        "live",
        "live_trading",
    ),
)
UNSAFE_PAYLOAD_VALUE_FRAGMENTS = frozenset(
    (
        "candidate",
        _join_parts("mar", "ket"),
        "slug",
        "question",
        "https://",
        "http://",
        "source_url",
        "source_text",
        "postgres://",
        "dsn",
        _join_parts("tab", "le"),
        "token",
        "secret",
        "credential",
        "api_key",
        "auth",
        "database",
        "network",
        "request",
        "endpoint",
        "execute",
        "execution",
        _join_parts("wal", "let"),
        _join_parts("ord", "er"),
        _join_parts("tra", "de"),
        "trading",
        "sizing",
        "recommend",
        _join_parts(" li", "ve "),
        "live_",
        "live-",
        _join_parts("b", "uy"),
        _join_parts("s", "ell"),
    ),
)

REPORT_PUBLIC_SCHEMA = frozenset(
    (
        "generated_at",
        "config_version",
        "domain_count",
        "covered_domain_count",
        "missing_domain_count",
        "pass_count",
        "watch_count",
        "block_count",
        "coverage_gap_domain_count",
        "stale_memory_domain_count",
        "overloaded_domain_count",
        "weak_calibration_domain_count",
        "max_memory_age_hours",
        "max_assigned_packet_count",
        "max_calibration_error_score",
        "min_coverage_confidence_score",
        "status",
        "paper_queue_action",
        "reason_codes",
        "reason_code_counts",
        "rows",
        "derived_validation_digest",
        "paper_only",
        "report_only",
        "readonly",
    )
)
ROW_PUBLIC_SCHEMA = frozenset(
    (
        "domain_label",
        "specialist_team_label",
        "coverage_status",
        "generated_at",
        "observed_at",
        "observation_age_seconds",
        "memory_refreshed_at",
        "memory_age_hours",
        "active_specialist_count",
        "backup_specialist_count",
        "assigned_packet_count",
        "calibration_error_score",
        "coverage_confidence_score",
        "reason_codes",
        "paper_only",
        "report_only",
        "readonly",
    )
)
REASON_CODE_COUNT_PUBLIC_SCHEMA = frozenset(
    (
        "reason_code",
        "count",
        "domain_ratio",
        "paper_only",
        "report_only",
        "readonly",
    )
)

__all__ = (
    "DEFAULT_RESEARCH_TEAM_SPECIALIST_COVERAGE_MAP_REPORT_CONFIG_VERSION",
    "COVERAGE_MAP_STATUSES",
    "COVERAGE_MAP_DOMAINS",
    "ResearchTeamSpecialistCoverageMapConfig",
    "ResearchTeamSpecialistCoverageMapInput",
    "ResearchTeamSpecialistCoverageMapReasonCodeCount",
    "ResearchTeamSpecialistCoverageMapReport",
    "ResearchTeamSpecialistCoverageMapRow",
    "build_research_team_specialist_coverage_map_report",
    "research_team_specialist_coverage_map_report_digest",
    "research_team_specialist_coverage_map_report_payload",
)


class _FinalDataclass:
    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        for base in cls.__bases__:
            if base is not _FinalDataclass and issubclass(base, _FinalDataclass):
                raise TypeError(f"{base.__name__} subclass is not allowed")


@dataclass(frozen=True)
class ResearchTeamSpecialistCoverageMapConfig(_FinalDataclass):
    config_version: str = (
        DEFAULT_RESEARCH_TEAM_SPECIALIST_COVERAGE_MAP_REPORT_CONFIG_VERSION
    )
    min_pass_active_specialist_count: Decimal = Decimal("2.000000")
    min_watch_active_specialist_count: Decimal = Decimal("1.000000")
    max_pass_memory_age_hours: Decimal = Decimal("24.000000")
    max_watch_memory_age_hours: Decimal = Decimal("72.000000")
    max_pass_assigned_packet_count: Decimal = Decimal("8.000000")
    max_watch_assigned_packet_count: Decimal = Decimal("16.000000")
    max_pass_calibration_error_score: Decimal = Decimal("0.100000")
    max_watch_calibration_error_score: Decimal = Decimal("0.250000")
    min_pass_coverage_confidence_score: Decimal = Decimal("0.800000")
    min_watch_coverage_confidence_score: Decimal = Decimal("0.500000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchTeamSpecialistCoverageMapConfig, "config")
        _require_public_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_TEAM_SPECIALIST_COVERAGE_MAP_REPORT_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "min_pass_active_specialist_count",
            "min_watch_active_specialist_count",
            "max_pass_assigned_packet_count",
            "max_watch_assigned_packet_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "max_pass_memory_age_hours",
            "max_watch_memory_age_hours",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "max_pass_calibration_error_score",
            "max_watch_calibration_error_score",
            "min_pass_coverage_confidence_score",
            "min_watch_coverage_confidence_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        _validate_config(self)
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class ResearchTeamSpecialistCoverageMapInput(_FinalDataclass):
    domain_label: str
    specialist_team_label: str
    observed_at: datetime
    memory_refreshed_at: datetime
    active_specialist_count: Decimal
    backup_specialist_count: Decimal
    assigned_packet_count: Decimal
    calibration_error_score: Decimal
    coverage_confidence_score: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchTeamSpecialistCoverageMapInput, "input")
        _require_domain_label(self.domain_label)
        _require_public_label("specialist_team_label", self.specialist_team_label)
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        object.__setattr__(
            self,
            "memory_refreshed_at",
            _as_utc("memory_refreshed_at", self.memory_refreshed_at),
        )
        for field_name in (
            "active_specialist_count",
            "backup_specialist_count",
            "assigned_packet_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "calibration_error_score",
            "coverage_confidence_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        _require_hard_flags("input", self)


@dataclass(frozen=True)
class ResearchTeamSpecialistCoverageMapRow(_FinalDataclass):
    domain_label: str
    specialist_team_label: str
    coverage_status: str
    generated_at: datetime
    observed_at: datetime
    observation_age_seconds: Decimal
    memory_refreshed_at: datetime
    memory_age_hours: Decimal
    active_specialist_count: Decimal
    backup_specialist_count: Decimal
    assigned_packet_count: Decimal
    calibration_error_score: Decimal
    coverage_confidence_score: Decimal
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchTeamSpecialistCoverageMapRow, "row")
        _require_domain_label(self.domain_label)
        _require_public_label("specialist_team_label", self.specialist_team_label)
        _require_status("coverage_status", self.coverage_status)
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        object.__setattr__(
            self,
            "memory_refreshed_at",
            _as_utc("memory_refreshed_at", self.memory_refreshed_at),
        )
        for field_name in ("observation_age_seconds", "memory_age_hours"):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "active_specialist_count",
            "backup_specialist_count",
            "assigned_packet_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "calibration_error_score",
            "coverage_confidence_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "reason_codes",
            _require_reason_codes(self.reason_codes),
        )
        _validate_row(self)
        _require_hard_flags("row", self)
        _reject_unsafe_public_payload("row", self)


@dataclass(frozen=True)
class ResearchTeamSpecialistCoverageMapReasonCodeCount(_FinalDataclass):
    reason_code: str
    count: Decimal
    domain_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchTeamSpecialistCoverageMapReasonCodeCount,
            "reason_code_count",
        )
        _require_public_string("reason_code", self.reason_code)
        if self.reason_code not in ROW_REASON_CODES:
            raise ValueError("reason_code must be supported")
        object.__setattr__(self, "count", _require_nonnegative_decimal("count", self.count))
        object.__setattr__(
            self,
            "domain_ratio",
            _require_ratio_decimal("domain_ratio", self.domain_ratio),
        )
        _require_hard_flags("reason_code_count", self)
        _reject_unsafe_public_payload("reason_code_count", self)


@dataclass(frozen=True)
class ResearchTeamSpecialistCoverageMapReport(_FinalDataclass):
    generated_at: datetime
    config_version: str
    domain_count: Decimal
    covered_domain_count: Decimal
    missing_domain_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    coverage_gap_domain_count: Decimal
    stale_memory_domain_count: Decimal
    overloaded_domain_count: Decimal
    weak_calibration_domain_count: Decimal
    max_memory_age_hours: Decimal
    max_assigned_packet_count: Decimal
    max_calibration_error_score: Decimal
    min_coverage_confidence_score: Decimal
    status: str
    paper_queue_action: str
    reason_codes: tuple[str, ...]
    reason_code_counts: tuple[ResearchTeamSpecialistCoverageMapReasonCodeCount, ...]
    rows: tuple[ResearchTeamSpecialistCoverageMapRow, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchTeamSpecialistCoverageMapReport, "report")
        object.__setattr__(
            self,
            "generated_at",
            _as_utc("generated_at", self.generated_at),
        )
        _require_public_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_TEAM_SPECIALIST_COVERAGE_MAP_REPORT_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "domain_count",
            "covered_domain_count",
            "missing_domain_count",
            "pass_count",
            "watch_count",
            "block_count",
            "coverage_gap_domain_count",
            "stale_memory_domain_count",
            "overloaded_domain_count",
            "weak_calibration_domain_count",
            "max_memory_age_hours",
            "max_assigned_packet_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "max_calibration_error_score",
            "min_coverage_confidence_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        _require_status("status", self.status)
        _require_public_string("paper_queue_action", self.paper_queue_action)
        if self.paper_queue_action != PAPER_ACTION_BY_STATUS[self.status]:
            raise ValueError("paper_queue_action must match status")
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
        _require_hard_flags("report", self)
        _reject_unsafe_public_payload("report", self)
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
        _validate_report(self)


def build_research_team_specialist_coverage_map_report(
    inputs: Iterable[ResearchTeamSpecialistCoverageMapInput],
    *,
    config: ResearchTeamSpecialistCoverageMapConfig,
    generated_at: datetime,
) -> ResearchTeamSpecialistCoverageMapReport:
    _require_exact_type(config, ResearchTeamSpecialistCoverageMapConfig, "config")
    _require_hard_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    input_rows = _normalize_inputs(inputs)
    rows_by_domain: dict[str, ResearchTeamSpecialistCoverageMapRow] = {}
    for item in input_rows:
        rows_by_domain[item.domain_label] = _row_from_input(
            item,
            config=config,
            generated_at=generated_at_utc,
        )
    rows = tuple(
        rows_by_domain.get(domain_label)
        or _missing_row(domain_label, generated_at=generated_at_utc)
        for domain_label in COVERAGE_MAP_DOMAINS
    )
    status = _report_status(rows)
    return ResearchTeamSpecialistCoverageMapReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        domain_count=_count(len(rows)),
        covered_domain_count=_count(len(input_rows)),
        missing_domain_count=_reason_domain_count(rows, MISSING_BLOCK_REASON),
        pass_count=_status_count(rows, "pass"),
        watch_count=_status_count(rows, "watch"),
        block_count=_status_count(rows, "block"),
        coverage_gap_domain_count=_reason_domain_count(
            rows,
            MISSING_BLOCK_REASON,
            DEPTH_BLOCK_REASON,
            DEPTH_WATCH_REASON,
        ),
        stale_memory_domain_count=_reason_domain_count(
            rows,
            MEMORY_STALE_BLOCK_REASON,
            MEMORY_STALE_WATCH_REASON,
        ),
        overloaded_domain_count=_reason_domain_count(
            rows,
            OVERLOAD_BLOCK_REASON,
            OVERLOAD_WATCH_REASON,
        ),
        weak_calibration_domain_count=_reason_domain_count(
            rows,
            CALIBRATION_BLOCK_REASON,
            CALIBRATION_WATCH_REASON,
        ),
        max_memory_age_hours=_max_decimal(tuple(row.memory_age_hours for row in rows)),
        max_assigned_packet_count=_max_decimal(
            tuple(row.assigned_packet_count for row in rows),
        ),
        max_calibration_error_score=_max_decimal(
            tuple(row.calibration_error_score for row in rows),
        ),
        min_coverage_confidence_score=_min_decimal(
            tuple(row.coverage_confidence_score for row in rows),
        ),
        status=status,
        paper_queue_action=PAPER_ACTION_BY_STATUS[status],
        reason_codes=_report_reason_codes(rows),
        reason_code_counts=_reason_code_counts(rows),
        rows=rows,
    )


def research_team_specialist_coverage_map_report_payload(
    report: ResearchTeamSpecialistCoverageMapReport | Mapping[str, object],
) -> dict[str, object]:
    if type(report) is ResearchTeamSpecialistCoverageMapReport:
        _require_hard_flags("report", report)
        _reject_unsafe_public_payload("report", report)
        if report.derived_validation_digest != _derived_validation_digest(report):
            raise ValueError("derived_validation_digest does not match report payload")
        payload = _json_ready(asdict(report))
    elif isinstance(report, Mapping):
        _reject_public_numeric_values(report)
        payload = _json_ready(report)
    else:
        raise ValueError("report must be a ResearchTeamSpecialistCoverageMapReport")
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    _require_hard_flags("report payload", _PayloadFlags(payload))
    supplied_digest = payload.get("derived_validation_digest")
    if type(supplied_digest) is not str:
        raise ValueError("derived_validation_digest is required")
    _require_sha256("derived_validation_digest", supplied_digest)
    if supplied_digest != _payload_validation_digest(payload):
        raise ValueError("derived_validation_digest does not match report payload")
    _reject_public_numeric_values(payload)
    _reject_unsafe_public_payload("report payload", payload, allow_json_containers=True)
    _validate_public_payload(payload)
    return payload


def research_team_specialist_coverage_map_report_digest(
    report: ResearchTeamSpecialistCoverageMapReport | Mapping[str, object],
) -> str:
    payload = research_team_specialist_coverage_map_report_payload(report)
    digest = payload["derived_validation_digest"]
    if type(digest) is not str:
        raise ValueError("derived_validation_digest must be a string")
    return digest


@dataclass(frozen=True)
class _PayloadFlags:
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
    item: ResearchTeamSpecialistCoverageMapInput,
    *,
    config: ResearchTeamSpecialistCoverageMapConfig,
    generated_at: datetime,
) -> ResearchTeamSpecialistCoverageMapRow:
    if item.observed_at > generated_at:
        raise ValueError("observed_at must not be in the future")
    if item.memory_refreshed_at > generated_at:
        raise ValueError("memory_refreshed_at must not be in the future")
    memory_age_hours = _hours_between(generated_at, item.memory_refreshed_at)
    reason_codes = _row_reason_codes(
        item=item,
        memory_age_hours=memory_age_hours,
        config=config,
    )
    return ResearchTeamSpecialistCoverageMapRow(
        domain_label=item.domain_label,
        specialist_team_label=item.specialist_team_label,
        coverage_status=_row_status(reason_codes),
        generated_at=generated_at,
        observed_at=item.observed_at,
        observation_age_seconds=_seconds_between(generated_at, item.observed_at),
        memory_refreshed_at=item.memory_refreshed_at,
        memory_age_hours=memory_age_hours,
        active_specialist_count=item.active_specialist_count,
        backup_specialist_count=item.backup_specialist_count,
        assigned_packet_count=item.assigned_packet_count,
        calibration_error_score=item.calibration_error_score,
        coverage_confidence_score=item.coverage_confidence_score,
        reason_codes=reason_codes,
    )


def _missing_row(
    domain_label: str,
    *,
    generated_at: datetime,
) -> ResearchTeamSpecialistCoverageMapRow:
    return ResearchTeamSpecialistCoverageMapRow(
        domain_label=domain_label,
        specialist_team_label="unassigned",
        coverage_status="block",
        generated_at=generated_at,
        observed_at=generated_at,
        observation_age_seconds=ZERO,
        memory_refreshed_at=generated_at,
        memory_age_hours=ZERO,
        active_specialist_count=ZERO,
        backup_specialist_count=ZERO,
        assigned_packet_count=ZERO,
        calibration_error_score=ZERO,
        coverage_confidence_score=ZERO,
        reason_codes=(MISSING_BLOCK_REASON,),
    )


def _row_reason_codes(
    *,
    item: ResearchTeamSpecialistCoverageMapInput,
    memory_age_hours: Decimal,
    config: ResearchTeamSpecialistCoverageMapConfig,
) -> tuple[str, ...]:
    reasons: list[str] = []
    _append_low_threshold_reason(
        reasons,
        metric=item.active_specialist_count,
        watch=config.min_pass_active_specialist_count,
        block=config.min_watch_active_specialist_count,
        watch_code=DEPTH_WATCH_REASON,
        block_code=DEPTH_BLOCK_REASON,
    )
    _append_high_threshold_reason(
        reasons,
        metric=memory_age_hours,
        watch=config.max_pass_memory_age_hours,
        block=config.max_watch_memory_age_hours,
        watch_code=MEMORY_STALE_WATCH_REASON,
        block_code=MEMORY_STALE_BLOCK_REASON,
    )
    _append_high_threshold_reason(
        reasons,
        metric=item.assigned_packet_count,
        watch=config.max_pass_assigned_packet_count,
        block=config.max_watch_assigned_packet_count,
        watch_code=OVERLOAD_WATCH_REASON,
        block_code=OVERLOAD_BLOCK_REASON,
    )
    _append_high_threshold_reason(
        reasons,
        metric=item.calibration_error_score,
        watch=config.max_pass_calibration_error_score,
        block=config.max_watch_calibration_error_score,
        watch_code=CALIBRATION_WATCH_REASON,
        block_code=CALIBRATION_BLOCK_REASON,
    )
    _append_low_threshold_reason(
        reasons,
        metric=item.coverage_confidence_score,
        watch=config.min_pass_coverage_confidence_score,
        block=config.min_watch_coverage_confidence_score,
        watch_code=CONFIDENCE_WATCH_REASON,
        block_code=CONFIDENCE_BLOCK_REASON,
    )
    if not reasons:
        reasons.append(PASS_REASON)
    return _require_reason_codes(tuple(reasons))


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
        return
    if metric > watch:
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
        return
    if metric < watch:
        reasons.append(watch_code)


def _row_status(reason_codes: tuple[str, ...]) -> str:
    if any(reason_code in BLOCK_REASON_CODES for reason_code in reason_codes):
        return "block"
    if any(reason_code in WATCH_REASON_CODES for reason_code in reason_codes):
        return "watch"
    return "pass"


def _report_status(rows: tuple[ResearchTeamSpecialistCoverageMapRow, ...]) -> str:
    if any(row.coverage_status == "block" for row in rows):
        return "block"
    if any(row.coverage_status == "watch" for row in rows):
        return "watch"
    return "pass"


def _status_count(
    rows: tuple[ResearchTeamSpecialistCoverageMapRow, ...],
    status: str,
) -> Decimal:
    return _count(sum(row.coverage_status == status for row in rows))


def _reason_domain_count(
    rows: tuple[ResearchTeamSpecialistCoverageMapRow, ...],
    *reason_codes: str,
) -> Decimal:
    return _count(
        sum(any(reason_code in row.reason_codes for reason_code in reason_codes) for row in rows),
    )


def _report_reason_codes(
    rows: tuple[ResearchTeamSpecialistCoverageMapRow, ...],
) -> tuple[str, ...]:
    status = _report_status(rows)
    row_reasons = frozenset(
        reason_code
        for row in rows
        for reason_code in row.reason_codes
        if reason_code != PASS_REASON
    )
    reasons = [REPORT_REASON_BY_STATUS[status]]
    reasons.extend(reason_code for reason_code in ROW_REASON_CODES if reason_code in row_reasons)
    return tuple(reasons)


def _reason_code_counts(
    rows: tuple[ResearchTeamSpecialistCoverageMapRow, ...],
) -> tuple[ResearchTeamSpecialistCoverageMapReasonCodeCount, ...]:
    counter = Counter(reason_code for row in rows for reason_code in row.reason_codes)
    total = _count(len(rows))
    return tuple(
        ResearchTeamSpecialistCoverageMapReasonCodeCount(
            reason_code=reason_code,
            count=_count(counter[reason_code]),
            domain_ratio=_ratio(_count(counter[reason_code]), total),
        )
        for reason_code in ROW_REASON_CODES
        if counter[reason_code]
    )


def _normalize_inputs(
    inputs: Iterable[ResearchTeamSpecialistCoverageMapInput],
) -> tuple[ResearchTeamSpecialistCoverageMapInput, ...]:
    if isinstance(inputs, (str, bytes)):
        raise ValueError("inputs must be an iterable")
    try:
        items = tuple(inputs)
    except TypeError as exc:
        raise ValueError("inputs must be an iterable") from exc
    seen: set[str] = set()
    for item in items:
        if type(item) is not ResearchTeamSpecialistCoverageMapInput:
            raise ValueError("inputs must contain ResearchTeamSpecialistCoverageMapInput")
        _require_hard_flags("input", item)
        if item.domain_label in seen:
            raise ValueError("domain_label values must be unique")
        seen.add(item.domain_label)
    return items


def _require_rows(
    rows: tuple[ResearchTeamSpecialistCoverageMapRow, ...],
) -> tuple[ResearchTeamSpecialistCoverageMapRow, ...]:
    if not isinstance(rows, tuple):
        raise ValueError("rows must be a tuple")
    normalized = tuple(rows)
    if tuple(row.domain_label for row in normalized) != COVERAGE_MAP_DOMAINS:
        raise ValueError("rows must cover all required domains in order")
    seen: set[str] = set()
    for row in normalized:
        if type(row) is not ResearchTeamSpecialistCoverageMapRow:
            raise ValueError("rows must contain ResearchTeamSpecialistCoverageMapRow")
        _require_hard_flags("row", row)
        if row.domain_label in seen:
            raise ValueError("rows must contain unique domain_label values")
        seen.add(row.domain_label)
    return normalized


def _require_reason_code_counts(
    counts: tuple[ResearchTeamSpecialistCoverageMapReasonCodeCount, ...],
) -> tuple[ResearchTeamSpecialistCoverageMapReasonCodeCount, ...]:
    if not isinstance(counts, tuple):
        raise ValueError("reason_code_counts must be a tuple")
    normalized = tuple(counts)
    expected = tuple(
        sorted(normalized, key=lambda item: ROW_REASON_CODES.index(item.reason_code)),
    )
    if normalized != expected:
        raise ValueError("reason_code_counts must be sorted deterministically")
    seen: set[str] = set()
    for item in normalized:
        if type(item) is not ResearchTeamSpecialistCoverageMapReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "ResearchTeamSpecialistCoverageMapReasonCodeCount",
            )
        _require_hard_flags("reason_code_count", item)
        if item.reason_code in seen:
            raise ValueError("reason_code_counts must be unique")
        seen.add(item.reason_code)
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
        if reason_code not in REPORT_REASON_CODES:
            raise ValueError("reason_code must be supported")
    if len(set(normalized)) != len(normalized):
        raise ValueError("reason_codes must be unique")
    if normalized[0] not in REPORT_REASON_BY_STATUS.values():
        raise ValueError("reason_codes must begin with report status reason")
    expected = tuple(
        reason_code
        for reason_code in (
            normalized[0],
            *ROW_REASON_CODES,
        )
        if reason_code in normalized
    )
    if normalized != expected:
        raise ValueError("reason_codes must be sorted deterministically")
    return normalized


def _require_reason_codes(reason_codes: tuple[str, ...]) -> tuple[str, ...]:
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
        if reason_code not in ROW_REASON_CODES:
            raise ValueError("reason_code must be supported")
    if len(set(normalized)) != len(normalized):
        raise ValueError("reason_codes must be unique")
    expected = tuple(reason_code for reason_code in ROW_REASON_CODES if reason_code in normalized)
    if normalized != expected:
        raise ValueError("reason_codes must be sorted deterministically")
    if PASS_REASON in normalized and len(normalized) != 1:
        raise ValueError("pass reason_codes must not be mixed with coverage reasons")
    return normalized


def _validate_config(config: ResearchTeamSpecialistCoverageMapConfig) -> None:
    if config.min_watch_active_specialist_count > config.min_pass_active_specialist_count:
        raise ValueError(
            "min_watch_active_specialist_count must not exceed "
            "min_pass_active_specialist_count",
        )
    if config.max_pass_memory_age_hours > config.max_watch_memory_age_hours:
        raise ValueError(
            "max_watch_memory_age_hours must be at least max_pass_memory_age_hours",
        )
    if config.max_pass_assigned_packet_count > config.max_watch_assigned_packet_count:
        raise ValueError(
            "max_watch_assigned_packet_count must be at least "
            "max_pass_assigned_packet_count",
        )
    if config.max_pass_calibration_error_score > config.max_watch_calibration_error_score:
        raise ValueError(
            "max_watch_calibration_error_score must be at least "
            "max_pass_calibration_error_score",
        )
    if (
        config.min_watch_coverage_confidence_score
        > config.min_pass_coverage_confidence_score
    ):
        raise ValueError(
            "min_watch_coverage_confidence_score must not exceed "
            "min_pass_coverage_confidence_score",
        )


def _validate_row(row: ResearchTeamSpecialistCoverageMapRow) -> None:
    if row.observed_at > row.generated_at:
        raise ValueError("observed_at must not be in the future")
    if row.memory_refreshed_at > row.generated_at:
        raise ValueError("memory_refreshed_at must not be in the future")
    if row.observation_age_seconds != _seconds_between(row.generated_at, row.observed_at):
        raise ValueError("observation_age_seconds must match generated_at and observed_at")
    if row.memory_age_hours != _hours_between(row.generated_at, row.memory_refreshed_at):
        raise ValueError("memory_age_hours must match generated_at and memory_refreshed_at")
    if row.coverage_status != _row_status(row.reason_codes):
        raise ValueError("coverage_status must match reason_codes")


def _validate_report(report: ResearchTeamSpecialistCoverageMapReport) -> None:
    rows = report.rows
    checks = {
        "domain_count": _count(len(rows)),
        "covered_domain_count": _count(
            sum(MISSING_BLOCK_REASON not in row.reason_codes for row in rows),
        ),
        "missing_domain_count": _reason_domain_count(rows, MISSING_BLOCK_REASON),
        "pass_count": _status_count(rows, "pass"),
        "watch_count": _status_count(rows, "watch"),
        "block_count": _status_count(rows, "block"),
        "coverage_gap_domain_count": _reason_domain_count(
            rows,
            MISSING_BLOCK_REASON,
            DEPTH_BLOCK_REASON,
            DEPTH_WATCH_REASON,
        ),
        "stale_memory_domain_count": _reason_domain_count(
            rows,
            MEMORY_STALE_BLOCK_REASON,
            MEMORY_STALE_WATCH_REASON,
        ),
        "overloaded_domain_count": _reason_domain_count(
            rows,
            OVERLOAD_BLOCK_REASON,
            OVERLOAD_WATCH_REASON,
        ),
        "weak_calibration_domain_count": _reason_domain_count(
            rows,
            CALIBRATION_BLOCK_REASON,
            CALIBRATION_WATCH_REASON,
        ),
        "max_memory_age_hours": _max_decimal(tuple(row.memory_age_hours for row in rows)),
        "max_assigned_packet_count": _max_decimal(
            tuple(row.assigned_packet_count for row in rows),
        ),
        "max_calibration_error_score": _max_decimal(
            tuple(row.calibration_error_score for row in rows),
        ),
        "min_coverage_confidence_score": _min_decimal(
            tuple(row.coverage_confidence_score for row in rows),
        ),
    }
    for field_name, expected in checks.items():
        if getattr(report, field_name) != expected:
            raise ValueError(f"{field_name} must match rows")
    if report.status != _report_status(rows):
        raise ValueError("status must match rows")
    if report.paper_queue_action != PAPER_ACTION_BY_STATUS[report.status]:
        raise ValueError("paper_queue_action must match status")
    if report.reason_codes != _report_reason_codes(rows):
        raise ValueError("reason_codes must match rows")
    if report.reason_code_counts != _reason_code_counts(rows):
        raise ValueError("reason_code_counts must match rows")


def _require_exact_type(value: object, expected_type: type[object], label: str) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{label} must be a {expected_type.__name__}")


def _require_hard_flags(label: str, value: object) -> None:
    require_paper_only_flags(label, value)


def _require_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in COVERAGE_MAP_STATUSES:
        raise ValueError(f"{field_name} must be one of pass, watch, block")


def _require_domain_label(value: object) -> None:
    _require_public_label("domain_label", value)
    if value not in COVERAGE_MAP_DOMAINS:
        raise ValueError("domain_label must be a supported coverage domain")


def _require_public_label(field_name: str, value: object) -> None:
    _require_public_string(field_name, value)
    if not PUBLIC_LABEL_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a public lowercase label")


def _require_public_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical non-empty string")
    if any(character.isspace() for character in value):
        raise ValueError(f"{field_name} must not contain whitespace")
    _reject_unsafe_public_text(field_name, value)


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


def _require_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be non-negative")
    return _quantize(normalized)


def _require_ratio_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_nonnegative_decimal(field_name, value)
    if normalized > ONE:
        raise ValueError(f"{field_name} must be no greater than 1")
    return normalized


def _quantize(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(QUANTUM)


def _count(value: int) -> Decimal:
    return Decimal(value).quantize(QUANTUM)


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return _quantize(numerator / denominator)


def _seconds_between(later: datetime, earlier: datetime) -> Decimal:
    if earlier > later:
        raise ValueError("datetime values must not be in the future")
    delta = later - earlier
    micros = (
        Decimal(delta.days) * Decimal("86400000000")
        + Decimal(delta.seconds) * Decimal("1000000")
        + Decimal(delta.microseconds)
    )
    return _quantize(micros / MICROSECONDS_PER_SECOND)


def _hours_between(later: datetime, earlier: datetime) -> Decimal:
    return _quantize(_seconds_between(later, earlier) / SECONDS_PER_HOUR)


def _max_decimal(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return ZERO
    return _quantize(max(values))


def _min_decimal(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return ZERO
    return _quantize(min(values))


def _require_sha256(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a sha256 hex digest")
    if len(value) != 64 or any(character not in HEX_CHARS for character in value):
        raise ValueError(f"{field_name} must be a sha256 hex digest")


def _validate_public_payload(payload: dict[str, object]) -> None:
    _require_exact_public_schema("report payload", payload, REPORT_PUBLIC_SCHEMA)
    rows = tuple(
        _row_from_public_payload(index, row)
        for index, row in enumerate(
            _require_public_object_list("report payload.rows", payload["rows"]),
        )
    )
    reason_code_counts = tuple(
        _reason_code_count_from_public_payload(index, item)
        for index, item in enumerate(
            _require_public_object_list(
                "report payload.reason_code_counts",
                payload["reason_code_counts"],
            ),
        )
    )
    report = ResearchTeamSpecialistCoverageMapReport(
        generated_at=_public_datetime("report payload.generated_at", payload["generated_at"]),
        config_version=_public_string(
            "report payload.config_version",
            payload["config_version"],
        ),
        domain_count=_public_decimal("report payload.domain_count", payload["domain_count"]),
        covered_domain_count=_public_decimal(
            "report payload.covered_domain_count",
            payload["covered_domain_count"],
        ),
        missing_domain_count=_public_decimal(
            "report payload.missing_domain_count",
            payload["missing_domain_count"],
        ),
        pass_count=_public_decimal("report payload.pass_count", payload["pass_count"]),
        watch_count=_public_decimal("report payload.watch_count", payload["watch_count"]),
        block_count=_public_decimal("report payload.block_count", payload["block_count"]),
        coverage_gap_domain_count=_public_decimal(
            "report payload.coverage_gap_domain_count",
            payload["coverage_gap_domain_count"],
        ),
        stale_memory_domain_count=_public_decimal(
            "report payload.stale_memory_domain_count",
            payload["stale_memory_domain_count"],
        ),
        overloaded_domain_count=_public_decimal(
            "report payload.overloaded_domain_count",
            payload["overloaded_domain_count"],
        ),
        weak_calibration_domain_count=_public_decimal(
            "report payload.weak_calibration_domain_count",
            payload["weak_calibration_domain_count"],
        ),
        max_memory_age_hours=_public_decimal(
            "report payload.max_memory_age_hours",
            payload["max_memory_age_hours"],
        ),
        max_assigned_packet_count=_public_decimal(
            "report payload.max_assigned_packet_count",
            payload["max_assigned_packet_count"],
        ),
        max_calibration_error_score=_public_decimal(
            "report payload.max_calibration_error_score",
            payload["max_calibration_error_score"],
        ),
        min_coverage_confidence_score=_public_decimal(
            "report payload.min_coverage_confidence_score",
            payload["min_coverage_confidence_score"],
        ),
        status=_public_string("report payload.status", payload["status"]),
        paper_queue_action=_public_string(
            "report payload.paper_queue_action",
            payload["paper_queue_action"],
        ),
        reason_codes=_public_string_tuple(
            "report payload.reason_codes",
            payload["reason_codes"],
        ),
        reason_code_counts=reason_code_counts,
        rows=rows,
        derived_validation_digest=_public_string(
            "report payload.derived_validation_digest",
            payload["derived_validation_digest"],
        ),
        paper_only=payload["paper_only"],
        report_only=payload["report_only"],
        readonly=payload["readonly"],
    )
    canonical_payload = _json_ready(asdict(report))
    if canonical_payload != payload:
        raise ValueError("report payload does not match exact public schema")


def _row_from_public_payload(
    index: int,
    payload: dict[str, object],
) -> ResearchTeamSpecialistCoverageMapRow:
    label = f"report payload.rows[{index}]"
    _require_exact_public_schema(label, payload, ROW_PUBLIC_SCHEMA)
    return ResearchTeamSpecialistCoverageMapRow(
        domain_label=_public_string(f"{label}.domain_label", payload["domain_label"]),
        specialist_team_label=_public_string(
            f"{label}.specialist_team_label",
            payload["specialist_team_label"],
        ),
        coverage_status=_public_string(
            f"{label}.coverage_status",
            payload["coverage_status"],
        ),
        generated_at=_public_datetime(f"{label}.generated_at", payload["generated_at"]),
        observed_at=_public_datetime(f"{label}.observed_at", payload["observed_at"]),
        observation_age_seconds=_public_decimal(
            f"{label}.observation_age_seconds",
            payload["observation_age_seconds"],
        ),
        memory_refreshed_at=_public_datetime(
            f"{label}.memory_refreshed_at",
            payload["memory_refreshed_at"],
        ),
        memory_age_hours=_public_decimal(
            f"{label}.memory_age_hours",
            payload["memory_age_hours"],
        ),
        active_specialist_count=_public_decimal(
            f"{label}.active_specialist_count",
            payload["active_specialist_count"],
        ),
        backup_specialist_count=_public_decimal(
            f"{label}.backup_specialist_count",
            payload["backup_specialist_count"],
        ),
        assigned_packet_count=_public_decimal(
            f"{label}.assigned_packet_count",
            payload["assigned_packet_count"],
        ),
        calibration_error_score=_public_decimal(
            f"{label}.calibration_error_score",
            payload["calibration_error_score"],
        ),
        coverage_confidence_score=_public_decimal(
            f"{label}.coverage_confidence_score",
            payload["coverage_confidence_score"],
        ),
        reason_codes=_public_string_tuple(
            f"{label}.reason_codes",
            payload["reason_codes"],
        ),
        paper_only=payload["paper_only"],
        report_only=payload["report_only"],
        readonly=payload["readonly"],
    )


def _reason_code_count_from_public_payload(
    index: int,
    payload: dict[str, object],
) -> ResearchTeamSpecialistCoverageMapReasonCodeCount:
    label = f"report payload.reason_code_counts[{index}]"
    _require_exact_public_schema(label, payload, REASON_CODE_COUNT_PUBLIC_SCHEMA)
    return ResearchTeamSpecialistCoverageMapReasonCodeCount(
        reason_code=_public_string(f"{label}.reason_code", payload["reason_code"]),
        count=_public_decimal(f"{label}.count", payload["count"]),
        domain_ratio=_public_decimal(f"{label}.domain_ratio", payload["domain_ratio"]),
        paper_only=payload["paper_only"],
        report_only=payload["report_only"],
        readonly=payload["readonly"],
    )


def _require_exact_public_schema(
    label: str,
    payload: Mapping[str, object],
    expected_fields: frozenset[str],
) -> None:
    if frozenset(payload) != expected_fields:
        raise ValueError(f"{label} does not match exact public schema")


def _require_public_object_list(
    label: str,
    value: object,
) -> list[dict[str, object]]:
    if type(value) is not list:
        raise ValueError(f"{label} does not match exact public schema")
    for item in value:
        if type(item) is not dict:
            raise ValueError(f"{label} does not match exact public schema")
    return value


def _public_string(label: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{label} does not match exact public schema")
    return value


def _public_string_tuple(label: str, value: object) -> tuple[str, ...]:
    if type(value) is not list or any(type(item) is not str for item in value):
        raise ValueError(f"{label} does not match exact public schema")
    return tuple(value)


def _public_decimal(label: str, value: object) -> Decimal:
    if type(value) is not str:
        raise ValueError(f"{label} does not match exact public schema")
    try:
        return Decimal(value)
    except InvalidOperation as exc:
        raise ValueError(f"{label} does not match exact public schema") from exc


def _public_datetime(label: str, value: object) -> datetime:
    if type(value) is not str:
        raise ValueError(f"{label} does not match exact public schema")
    try:
        return datetime.fromisoformat(value)
    except ValueError as exc:
        raise ValueError(f"{label} does not match exact public schema") from exc


def _derived_validation_digest(report: ResearchTeamSpecialistCoverageMapReport) -> str:
    values = asdict(report)
    values.pop("derived_validation_digest")
    return _digest_from_values(values)


def _digest_from_values(values: Mapping[str, object]) -> str:
    payload = _json_ready(values)
    if type(payload) is not dict:
        raise ValueError("digest payload must be a JSON object")
    return _payload_validation_digest(payload)


def _payload_validation_digest(payload: Mapping[str, object]) -> str:
    unsigned = dict(payload)
    unsigned.pop("derived_validation_digest", None)
    encoded = json.dumps(unsigned, sort_keys=True, separators=(",", ":")).encode()
    return sha256(encoded).hexdigest()


def _json_ready(value: Any) -> Any:
    if value is None:
        return None
    if is_dataclass(value) and not isinstance(value, type):
        return _json_ready(asdict(value))
    if type(value) is Decimal:
        if not value.is_finite():
            raise ValueError("Decimal value must be finite")
        return str(value.quantize(QUANTUM))
    if type(value) is datetime:
        return _as_utc("datetime", value).isoformat()
    if type(value) is bool or type(value) is str:
        return value
    if type(value) in (int, float):
        raise ValueError("public payload must not contain numeric values")
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


def _reject_public_numeric_values(value: object) -> None:
    if type(value) in (int, float):
        raise ValueError("public payload must not contain numeric values")
    if isinstance(value, Mapping):
        for item in value.values():
            _reject_public_numeric_values(item)
    elif isinstance(value, (list, tuple)):
        for item in value:
            _reject_public_numeric_values(item)


def _reject_unsafe_public_payload(
    label: str,
    value: object,
    *,
    allow_json_containers: bool = False,
) -> None:
    if is_dataclass(value) and not isinstance(value, type):
        for field in fields(value):
            _reject_unsafe_public_text(label, field.name)
            _reject_unsafe_public_payload(
                f"{label}.{field.name}",
                getattr(value, field.name),
                allow_json_containers=allow_json_containers,
            )
        return
    if isinstance(value, Mapping):
        if not allow_json_containers:
            raise ValueError(f"{label} must not contain raw mappings")
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("public payload keys must be strings")
            if key in UNSAFE_PAYLOAD_KEYS:
                raise ValueError("unsafe public payload key")
            _reject_unsafe_public_text(label, key)
            _reject_unsafe_public_payload(
                f"{label}.{key}",
                item,
                allow_json_containers=allow_json_containers,
            )
        return
    if isinstance(value, (list, tuple)):
        if not allow_json_containers and isinstance(value, list):
            raise ValueError(f"{label} must not contain raw lists")
        for item in value:
            _reject_unsafe_public_payload(
                label,
                item,
                allow_json_containers=allow_json_containers,
            )
        return
    if type(value) is str:
        _reject_unsafe_public_text(label, value)


def _reject_unsafe_public_text(label: str, value: str) -> None:
    lowered = value.lower()
    if label == "specialist_team_label" or label.endswith(".specialist_team_label"):
        if any(fragment in lowered for fragment in UNSAFE_LABEL_FRAGMENTS):
            raise ValueError(f"{label} contains unsafe public text")
        return
    if value in UNSAFE_PAYLOAD_KEYS:
        raise ValueError(f"{label} contains unsafe public text")
    if any(fragment in lowered for fragment in UNSAFE_PAYLOAD_VALUE_FRAGMENTS):
        raise ValueError(f"{label} contains unsafe public text")
