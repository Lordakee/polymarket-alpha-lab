"""Deterministic paper-only source resolution memory ladder report."""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable, Mapping
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, InvalidOperation, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
import json
import re


DEFAULT_RESEARCH_TEAM_DOMAIN_SOURCE_RESOLUTION_MEMORY_LADDER_CONFIG_VERSION = (
    "research-team-domain-source-resolution-memory-ladder-report-v1"
)
RESEARCH_TEAM_DOMAIN_SOURCE_RESOLUTION_MEMORY_LADDER_STATUSES = (
    "pass",
    "watch",
    "block",
)

QUANTUM = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
PUBLIC_LABEL_RE = re.compile(r"^[a-z0-9][a-z0-9_.-]{0,127}$")
HEX_CHARS = frozenset("0123456789abcdef")

REASON_SEQUENCE = (
    "source_resolution_memory_coverage_block",
    "source_resolution_score_block",
    "source_resolution_memory_staleness_block",
    "source_resolution_ladder_depth_block",
    "source_resolution_contradiction_block",
    "source_resolution_memory_coverage_watch",
    "source_resolution_score_watch",
    "source_resolution_memory_staleness_watch",
    "source_resolution_ladder_depth_watch",
    "source_resolution_contradiction_watch",
    "source_resolution_memory_ladder_pass",
)
EMPTY_REASON = "source_resolution_memory_ladder_empty"
REPORT_MODE_BY_STATUS = {
    "pass": "paper_source_resolution_memory_ladder_monitor",
    "watch": "paper_source_resolution_memory_ladder_watch",
    "block": "paper_source_resolution_memory_ladder_block",
}
STATUS_SORT_RANK = {"block": 0, "watch": 1, "pass": 2}

REPORT_PAYLOAD_KEYS = frozenset(
    (
        "generated_at",
        "config_version",
        "input_count",
        "row_count",
        "pass_count",
        "watch_count",
        "block_count",
        "watch_block_ratio",
        "min_memory_coverage_ratio",
        "min_ladder_depth_ratio",
        "min_source_resolution_score",
        "min_resolution_memory_ladder_score",
        "max_memory_age_seconds",
        "max_contradiction_ratio",
        "max_memory_ladder_pressure_score",
        "status",
        "report_mode",
        "reason_codes",
        "reason_code_counts",
        "rows",
        "derived_validation_digest",
        "paper_only",
        "report_only",
        "readonly",
    ),
)
ROW_PAYLOAD_KEYS = frozenset(
    (
        "resolution_rank",
        "domain_label",
        "team_label",
        "source_family_label",
        "status",
        "memory_ladder_pressure_score",
        "resolution_memory_count",
        "verified_resolution_memory_count",
        "memory_coverage_ratio",
        "source_resolution_score",
        "memory_age_seconds",
        "memory_staleness_ratio",
        "ladder_depth_count",
        "ladder_depth_ratio",
        "contradiction_ratio",
        "resolution_memory_ladder_score",
        "observed_at",
        "reason_codes",
        "derived_validation_digest",
        "paper_only",
        "report_only",
        "readonly",
    ),
)
REASON_COUNT_PAYLOAD_KEYS = frozenset(
    ("reason_code", "count", "row_ratio", "paper_only", "report_only", "readonly"),
)


def _join_parts(*parts: str) -> str:
    return "".join(parts)


UNSAFE_PUBLIC_FRAGMENTS = frozenset(
    (
        "candidate",
        "market",
        "question",
        _join_parts("raw", "_source"),
        _join_parts("source", "_url"),
        _join_parts("source", "url"),
        _join_parts("source", "_text"),
        _join_parts("source", "text"),
        _join_parts("d", "sn"),
        _join_parts("table", "_name"),
        _join_parts("table", "name"),
        _join_parts("to", "ken"),
        "secret",
        "credential",
        "api_key",
        "private_key",
        "sizing",
        "recommendation",
        _join_parts("wal", "let"),
        _join_parts("or", "der"),
        _join_parts("tra", "de"),
        _join_parts("tra", "ding"),
        _join_parts("li", "ve"),
        _join_parts("data", "base"),
        _join_parts("net", "work"),
        "://",
    ),
)

__all__ = (
    "DEFAULT_RESEARCH_TEAM_DOMAIN_SOURCE_RESOLUTION_MEMORY_LADDER_CONFIG_VERSION",
    "RESEARCH_TEAM_DOMAIN_SOURCE_RESOLUTION_MEMORY_LADDER_STATUSES",
    "ResearchTeamDomainSourceResolutionMemoryLadderConfig",
    "ResearchTeamDomainSourceResolutionMemoryLadderInput",
    "ResearchTeamDomainSourceResolutionMemoryLadderReasonCodeCount",
    "ResearchTeamDomainSourceResolutionMemoryLadderReport",
    "ResearchTeamDomainSourceResolutionMemoryLadderRow",
    "build_research_team_domain_source_resolution_memory_ladder_report",
    "research_team_domain_source_resolution_memory_ladder_report_digest",
    "research_team_domain_source_resolution_memory_ladder_report_payload",
    "validate_research_team_domain_source_resolution_memory_ladder_report_digest",
)


class _FinalDataclass:
    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        for base in cls.__bases__:
            if base is not _FinalDataclass and issubclass(base, _FinalDataclass):
                raise TypeError(f"{base.__name__} subclass is not allowed")


@dataclass(frozen=True)
class ResearchTeamDomainSourceResolutionMemoryLadderConfig(_FinalDataclass):
    config_version: str = (
        DEFAULT_RESEARCH_TEAM_DOMAIN_SOURCE_RESOLUTION_MEMORY_LADDER_CONFIG_VERSION
    )
    min_pass_memory_coverage_ratio: Decimal = Decimal("0.900000")
    min_watch_memory_coverage_ratio: Decimal = Decimal("0.700000")
    min_pass_source_resolution_score: Decimal = Decimal("0.800000")
    min_watch_source_resolution_score: Decimal = Decimal("0.600000")
    max_pass_memory_age_seconds: Decimal = Decimal("86400.000000")
    max_watch_memory_age_seconds: Decimal = Decimal("604800.000000")
    target_ladder_depth_count: Decimal = Decimal("3.000000")
    min_pass_ladder_depth_ratio: Decimal = Decimal("0.900000")
    min_watch_ladder_depth_ratio: Decimal = Decimal("0.700000")
    max_pass_contradiction_ratio: Decimal = Decimal("0.050000")
    max_watch_contradiction_ratio: Decimal = Decimal("0.200000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchTeamDomainSourceResolutionMemoryLadderConfig,
            "config",
        )
        _require_public_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_TEAM_DOMAIN_SOURCE_RESOLUTION_MEMORY_LADDER_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "min_pass_memory_coverage_ratio",
            "min_watch_memory_coverage_ratio",
            "min_pass_source_resolution_score",
            "min_watch_source_resolution_score",
            "min_pass_ladder_depth_ratio",
            "min_watch_ladder_depth_ratio",
            "max_pass_contradiction_ratio",
            "max_watch_contradiction_ratio",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "max_pass_memory_age_seconds",
            "max_watch_memory_age_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "target_ladder_depth_count",
            _require_positive_decimal(
                "target_ladder_depth_count",
                self.target_ladder_depth_count,
            ),
        )
        if self.min_pass_memory_coverage_ratio < self.min_watch_memory_coverage_ratio:
            raise ValueError(
                "min_watch_memory_coverage_ratio must not exceed "
                "min_pass_memory_coverage_ratio",
            )
        if (
            self.min_pass_source_resolution_score
            < self.min_watch_source_resolution_score
        ):
            raise ValueError(
                "min_watch_source_resolution_score must not exceed "
                "min_pass_source_resolution_score",
            )
        if self.max_pass_memory_age_seconds > self.max_watch_memory_age_seconds:
            raise ValueError(
                "max_watch_memory_age_seconds must be at least "
                "max_pass_memory_age_seconds",
            )
        if self.min_pass_ladder_depth_ratio < self.min_watch_ladder_depth_ratio:
            raise ValueError(
                "min_watch_ladder_depth_ratio must not exceed "
                "min_pass_ladder_depth_ratio",
            )
        if self.max_pass_contradiction_ratio > self.max_watch_contradiction_ratio:
            raise ValueError(
                "max_watch_contradiction_ratio must be at least "
                "max_pass_contradiction_ratio",
            )
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class ResearchTeamDomainSourceResolutionMemoryLadderInput(_FinalDataclass):
    domain_label: str
    team_label: str
    source_family_label: str
    resolution_memory_count: Decimal
    verified_resolution_memory_count: Decimal
    source_resolution_score: Decimal
    memory_age_seconds: Decimal
    ladder_depth_count: Decimal
    contradiction_ratio: Decimal
    observed_at: datetime
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchTeamDomainSourceResolutionMemoryLadderInput,
            "input",
        )
        for field_name in ("domain_label", "team_label", "source_family_label"):
            _require_public_label(field_name, getattr(self, field_name))
        for field_name in (
            "resolution_memory_count",
            "verified_resolution_memory_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_whole_decimal(
                    field_name,
                    getattr(self, field_name),
                ),
            )
        for field_name in ("memory_age_seconds", "ladder_depth_count"):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in ("source_resolution_score", "contradiction_ratio"):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        if self.verified_resolution_memory_count > self.resolution_memory_count:
            raise ValueError(
                "verified_resolution_memory_count must not exceed "
                "resolution_memory_count",
            )
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        _require_hard_flags("input", self)


@dataclass(frozen=True)
class ResearchTeamDomainSourceResolutionMemoryLadderRow(_FinalDataclass):
    resolution_rank: Decimal
    domain_label: str
    team_label: str
    source_family_label: str
    status: str
    memory_ladder_pressure_score: Decimal
    resolution_memory_count: Decimal
    verified_resolution_memory_count: Decimal
    memory_coverage_ratio: Decimal
    source_resolution_score: Decimal
    memory_age_seconds: Decimal
    memory_staleness_ratio: Decimal
    ladder_depth_count: Decimal
    ladder_depth_ratio: Decimal
    contradiction_ratio: Decimal
    resolution_memory_ladder_score: Decimal
    observed_at: datetime
    reason_codes: tuple[str, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchTeamDomainSourceResolutionMemoryLadderRow, "row")
        object.__setattr__(
            self,
            "resolution_rank",
            _require_nonnegative_whole_decimal(
                "resolution_rank",
                self.resolution_rank,
            ),
        )
        for field_name in ("domain_label", "team_label", "source_family_label"):
            _require_public_label(field_name, getattr(self, field_name))
        _require_status("status", self.status)
        for field_name in (
            "memory_ladder_pressure_score",
            "memory_coverage_ratio",
            "source_resolution_score",
            "memory_staleness_ratio",
            "ladder_depth_ratio",
            "contradiction_ratio",
            "resolution_memory_ladder_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "resolution_memory_count",
            "verified_resolution_memory_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_whole_decimal(
                    field_name,
                    getattr(self, field_name),
                ),
            )
        for field_name in ("memory_age_seconds", "ladder_depth_count"):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        if self.verified_resolution_memory_count > self.resolution_memory_count:
            raise ValueError(
                "verified_resolution_memory_count must not exceed "
                "resolution_memory_count",
            )
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        object.__setattr__(
            self,
            "reason_codes",
            _require_reason_codes(self.reason_codes, require_nonempty=True),
        )
        _require_hard_flags("row", self)
        _apply_or_verify_digest(self)
        _validate_row(self)


@dataclass(frozen=True)
class ResearchTeamDomainSourceResolutionMemoryLadderReasonCodeCount(_FinalDataclass):
    reason_code: str
    count: Decimal
    row_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchTeamDomainSourceResolutionMemoryLadderReasonCodeCount,
            "reason_code_count",
        )
        _require_public_string("reason_code", self.reason_code)
        if self.reason_code not in REASON_SEQUENCE:
            raise ValueError("reason_code must be known")
        object.__setattr__(
            self,
            "count",
            _require_nonnegative_whole_decimal("count", self.count),
        )
        object.__setattr__(
            self,
            "row_ratio",
            _require_ratio_decimal("row_ratio", self.row_ratio),
        )
        _require_hard_flags("reason_code_count", self)


@dataclass(frozen=True)
class ResearchTeamDomainSourceResolutionMemoryLadderReport(_FinalDataclass):
    generated_at: datetime
    config_version: str
    input_count: Decimal
    row_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    watch_block_ratio: Decimal
    min_memory_coverage_ratio: Decimal
    min_ladder_depth_ratio: Decimal
    min_source_resolution_score: Decimal
    min_resolution_memory_ladder_score: Decimal
    max_memory_age_seconds: Decimal
    max_contradiction_ratio: Decimal
    max_memory_ladder_pressure_score: Decimal
    status: str
    report_mode: str
    reason_codes: tuple[str, ...]
    reason_code_counts: tuple[
        ResearchTeamDomainSourceResolutionMemoryLadderReasonCodeCount,
        ...,
    ]
    rows: tuple[ResearchTeamDomainSourceResolutionMemoryLadderRow, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchTeamDomainSourceResolutionMemoryLadderReport,
            "report",
        )
        object.__setattr__(
            self,
            "generated_at",
            _as_generated_at_utc("generated_at", self.generated_at),
        )
        _require_public_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_TEAM_DOMAIN_SOURCE_RESOLUTION_MEMORY_LADDER_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "input_count",
            "row_count",
            "pass_count",
            "watch_count",
            "block_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_whole_decimal(
                    field_name,
                    getattr(self, field_name),
                ),
            )
        object.__setattr__(
            self,
            "max_memory_age_seconds",
            _require_nonnegative_decimal(
                "max_memory_age_seconds",
                self.max_memory_age_seconds,
            ),
        )
        for field_name in (
            "watch_block_ratio",
            "min_memory_coverage_ratio",
            "min_ladder_depth_ratio",
            "min_source_resolution_score",
            "min_resolution_memory_ladder_score",
            "max_contradiction_ratio",
            "max_memory_ladder_pressure_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        _require_status("status", self.status)
        _require_public_string("report_mode", self.report_mode)
        if self.report_mode != REPORT_MODE_BY_STATUS[self.status]:
            raise ValueError("report_mode must match status")
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
        _require_hard_flags("report", self)
        _validate_report(self)
        _apply_or_verify_digest(self)


def build_research_team_domain_source_resolution_memory_ladder_report(
    inputs: Iterable[ResearchTeamDomainSourceResolutionMemoryLadderInput],
    *,
    config: ResearchTeamDomainSourceResolutionMemoryLadderConfig,
    generated_at: datetime,
) -> ResearchTeamDomainSourceResolutionMemoryLadderReport:
    _require_exact_type(
        config,
        ResearchTeamDomainSourceResolutionMemoryLadderConfig,
        "config",
    )
    _require_hard_flags("config", config)
    generated_at_utc = _as_generated_at_utc("generated_at", generated_at)
    input_rows = _normalize_inputs(inputs)
    for item in input_rows:
        if item.observed_at > generated_at_utc:
            raise ValueError("observed_at must not be after generated_at")
    base_rows = tuple(_row_from_input(item, config) for item in input_rows)
    rows = tuple(
        _with_rank(row, rank)
        for rank, row in enumerate(sorted(base_rows, key=_row_sort_key), start=1)
    )
    status = _report_status(rows)
    watch_block_count = _count(sum(1 for row in rows if row.status in ("watch", "block")))
    return ResearchTeamDomainSourceResolutionMemoryLadderReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        input_count=_count(len(rows)),
        row_count=_count(len(rows)),
        pass_count=_status_count(rows, "pass"),
        watch_count=_status_count(rows, "watch"),
        block_count=_status_count(rows, "block"),
        watch_block_ratio=_ratio(watch_block_count, _count(len(rows))),
        min_memory_coverage_ratio=_min_decimal(
            tuple(row.memory_coverage_ratio for row in rows),
        ),
        min_ladder_depth_ratio=_min_decimal(
            tuple(row.ladder_depth_ratio for row in rows),
        ),
        min_source_resolution_score=_min_decimal(
            tuple(row.source_resolution_score for row in rows),
        ),
        min_resolution_memory_ladder_score=_min_decimal(
            tuple(row.resolution_memory_ladder_score for row in rows),
        ),
        max_memory_age_seconds=_max_decimal(
            tuple(row.memory_age_seconds for row in rows),
        ),
        max_contradiction_ratio=_max_decimal(
            tuple(row.contradiction_ratio for row in rows),
        ),
        max_memory_ladder_pressure_score=_max_decimal(
            tuple(row.memory_ladder_pressure_score for row in rows),
        ),
        status=status,
        report_mode=REPORT_MODE_BY_STATUS[status],
        reason_codes=_report_reason_codes(rows),
        reason_code_counts=_reason_code_counts(rows),
        rows=rows,
    )


def research_team_domain_source_resolution_memory_ladder_report_payload(
    report: ResearchTeamDomainSourceResolutionMemoryLadderReport | Mapping[str, object],
) -> dict[str, object]:
    if type(report) is ResearchTeamDomainSourceResolutionMemoryLadderReport:
        _require_hard_flags("report", report)
        _verify_digest(report)
        for row in report.rows:
            _verify_digest(row)
        payload = _json_ready(asdict(report))
    elif isinstance(report, Mapping):
        payload = dict(report)
    else:
        raise ValueError(
            "report must be a ResearchTeamDomainSourceResolutionMemoryLadderReport",
        )
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    _require_hard_flags("report payload", _MappingFlags(payload))
    _validate_public_payload(payload)
    expected_digest = _digest_from_payload(payload)
    if payload.get("derived_validation_digest") != expected_digest:
        raise ValueError("derived_validation_digest does not match report payload")
    return payload


def research_team_domain_source_resolution_memory_ladder_report_digest(
    report: ResearchTeamDomainSourceResolutionMemoryLadderReport | Mapping[str, object],
) -> str:
    payload = research_team_domain_source_resolution_memory_ladder_report_payload(report)
    digest = payload["derived_validation_digest"]
    if type(digest) is not str:
        raise ValueError("derived_validation_digest must be a string")
    return digest


def validate_research_team_domain_source_resolution_memory_ladder_report_digest(
    report: ResearchTeamDomainSourceResolutionMemoryLadderReport | Mapping[str, object],
) -> bool:
    payload = research_team_domain_source_resolution_memory_ladder_report_payload(report)
    return payload["derived_validation_digest"] == _digest_from_payload(payload)


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
    item: ResearchTeamDomainSourceResolutionMemoryLadderInput,
    config: ResearchTeamDomainSourceResolutionMemoryLadderConfig,
) -> ResearchTeamDomainSourceResolutionMemoryLadderRow:
    memory_coverage_ratio = _ratio(
        item.verified_resolution_memory_count,
        item.resolution_memory_count,
    )
    memory_staleness_ratio = _bounded_ratio(
        item.memory_age_seconds,
        config.max_watch_memory_age_seconds,
    )
    ladder_depth_ratio = _bounded_ratio(
        item.ladder_depth_count,
        config.target_ladder_depth_count,
    )
    resolution_memory_ladder_score = _resolution_memory_ladder_score(
        memory_coverage_ratio=memory_coverage_ratio,
        source_resolution_score=item.source_resolution_score,
        memory_staleness_ratio=memory_staleness_ratio,
        ladder_depth_ratio=ladder_depth_ratio,
        contradiction_ratio=item.contradiction_ratio,
    )
    memory_ladder_pressure_score = _memory_ladder_pressure_score(
        memory_coverage_ratio=memory_coverage_ratio,
        source_resolution_score=item.source_resolution_score,
        memory_age_seconds=item.memory_age_seconds,
        ladder_depth_ratio=ladder_depth_ratio,
        contradiction_ratio=item.contradiction_ratio,
        config=config,
    )
    status = _status_for(
        memory_coverage_ratio=memory_coverage_ratio,
        source_resolution_score=item.source_resolution_score,
        memory_age_seconds=item.memory_age_seconds,
        ladder_depth_ratio=ladder_depth_ratio,
        contradiction_ratio=item.contradiction_ratio,
        config=config,
    )
    return ResearchTeamDomainSourceResolutionMemoryLadderRow(
        resolution_rank=ZERO,
        domain_label=item.domain_label,
        team_label=item.team_label,
        source_family_label=item.source_family_label,
        status=status,
        memory_ladder_pressure_score=memory_ladder_pressure_score,
        resolution_memory_count=item.resolution_memory_count,
        verified_resolution_memory_count=item.verified_resolution_memory_count,
        memory_coverage_ratio=memory_coverage_ratio,
        source_resolution_score=item.source_resolution_score,
        memory_age_seconds=item.memory_age_seconds,
        memory_staleness_ratio=memory_staleness_ratio,
        ladder_depth_count=item.ladder_depth_count,
        ladder_depth_ratio=ladder_depth_ratio,
        contradiction_ratio=item.contradiction_ratio,
        resolution_memory_ladder_score=resolution_memory_ladder_score,
        observed_at=item.observed_at,
        reason_codes=_reason_codes_for(
            memory_coverage_ratio=memory_coverage_ratio,
            source_resolution_score=item.source_resolution_score,
            memory_age_seconds=item.memory_age_seconds,
            ladder_depth_ratio=ladder_depth_ratio,
            contradiction_ratio=item.contradiction_ratio,
            status=status,
            config=config,
        ),
    )


def _with_rank(
    row: ResearchTeamDomainSourceResolutionMemoryLadderRow,
    rank: int,
) -> ResearchTeamDomainSourceResolutionMemoryLadderRow:
    return ResearchTeamDomainSourceResolutionMemoryLadderRow(
        resolution_rank=_count(rank),
        domain_label=row.domain_label,
        team_label=row.team_label,
        source_family_label=row.source_family_label,
        status=row.status,
        memory_ladder_pressure_score=row.memory_ladder_pressure_score,
        resolution_memory_count=row.resolution_memory_count,
        verified_resolution_memory_count=row.verified_resolution_memory_count,
        memory_coverage_ratio=row.memory_coverage_ratio,
        source_resolution_score=row.source_resolution_score,
        memory_age_seconds=row.memory_age_seconds,
        memory_staleness_ratio=row.memory_staleness_ratio,
        ladder_depth_count=row.ladder_depth_count,
        ladder_depth_ratio=row.ladder_depth_ratio,
        contradiction_ratio=row.contradiction_ratio,
        resolution_memory_ladder_score=row.resolution_memory_ladder_score,
        observed_at=row.observed_at,
        reason_codes=row.reason_codes,
    )


def _status_for(
    *,
    memory_coverage_ratio: Decimal,
    source_resolution_score: Decimal,
    memory_age_seconds: Decimal,
    ladder_depth_ratio: Decimal,
    contradiction_ratio: Decimal,
    config: ResearchTeamDomainSourceResolutionMemoryLadderConfig,
) -> str:
    if (
        memory_coverage_ratio < config.min_watch_memory_coverage_ratio
        or source_resolution_score < config.min_watch_source_resolution_score
        or memory_age_seconds > config.max_watch_memory_age_seconds
        or ladder_depth_ratio < config.min_watch_ladder_depth_ratio
        or contradiction_ratio > config.max_watch_contradiction_ratio
    ):
        return "block"
    if (
        memory_coverage_ratio < config.min_pass_memory_coverage_ratio
        or source_resolution_score < config.min_pass_source_resolution_score
        or memory_age_seconds > config.max_pass_memory_age_seconds
        or ladder_depth_ratio < config.min_pass_ladder_depth_ratio
        or contradiction_ratio > config.max_pass_contradiction_ratio
    ):
        return "watch"
    return "pass"


def _resolution_memory_ladder_score(
    *,
    memory_coverage_ratio: Decimal,
    source_resolution_score: Decimal,
    memory_staleness_ratio: Decimal,
    ladder_depth_ratio: Decimal,
    contradiction_ratio: Decimal,
) -> Decimal:
    return _mean_ratio(
        (
            memory_coverage_ratio,
            source_resolution_score,
            _subtract_decimal(ONE, memory_staleness_ratio),
            ladder_depth_ratio,
            _subtract_decimal(ONE, contradiction_ratio),
        ),
    )


def _memory_ladder_pressure_score(
    *,
    memory_coverage_ratio: Decimal,
    source_resolution_score: Decimal,
    memory_age_seconds: Decimal,
    ladder_depth_ratio: Decimal,
    contradiction_ratio: Decimal,
    config: ResearchTeamDomainSourceResolutionMemoryLadderConfig,
) -> Decimal:
    return _max_decimal(
        (
            _inverse_threshold_pressure(
                memory_coverage_ratio,
                pass_value=config.min_pass_memory_coverage_ratio,
                watch_value=config.min_watch_memory_coverage_ratio,
            ),
            _inverse_threshold_pressure(
                source_resolution_score,
                pass_value=config.min_pass_source_resolution_score,
                watch_value=config.min_watch_source_resolution_score,
            ),
            _threshold_pressure(
                memory_age_seconds,
                pass_value=config.max_pass_memory_age_seconds,
                watch_value=config.max_watch_memory_age_seconds,
            ),
            _inverse_threshold_pressure(
                ladder_depth_ratio,
                pass_value=config.min_pass_ladder_depth_ratio,
                watch_value=config.min_watch_ladder_depth_ratio,
            ),
            _threshold_pressure(
                contradiction_ratio,
                pass_value=config.max_pass_contradiction_ratio,
                watch_value=config.max_watch_contradiction_ratio,
            ),
        ),
    )


def _reason_codes_for(
    *,
    memory_coverage_ratio: Decimal,
    source_resolution_score: Decimal,
    memory_age_seconds: Decimal,
    ladder_depth_ratio: Decimal,
    contradiction_ratio: Decimal,
    status: str,
    config: ResearchTeamDomainSourceResolutionMemoryLadderConfig,
) -> tuple[str, ...]:
    codes: list[str] = []
    if memory_coverage_ratio < config.min_watch_memory_coverage_ratio:
        codes.append("source_resolution_memory_coverage_block")
    elif memory_coverage_ratio < config.min_pass_memory_coverage_ratio:
        codes.append("source_resolution_memory_coverage_watch")
    if source_resolution_score < config.min_watch_source_resolution_score:
        codes.append("source_resolution_score_block")
    elif source_resolution_score < config.min_pass_source_resolution_score:
        codes.append("source_resolution_score_watch")
    if memory_age_seconds > config.max_watch_memory_age_seconds:
        codes.append("source_resolution_memory_staleness_block")
    elif memory_age_seconds > config.max_pass_memory_age_seconds:
        codes.append("source_resolution_memory_staleness_watch")
    if ladder_depth_ratio < config.min_watch_ladder_depth_ratio:
        codes.append("source_resolution_ladder_depth_block")
    elif ladder_depth_ratio < config.min_pass_ladder_depth_ratio:
        codes.append("source_resolution_ladder_depth_watch")
    if contradiction_ratio > config.max_watch_contradiction_ratio:
        codes.append("source_resolution_contradiction_block")
    elif contradiction_ratio > config.max_pass_contradiction_ratio:
        codes.append("source_resolution_contradiction_watch")
    if not codes and status == "pass":
        codes.append("source_resolution_memory_ladder_pass")
    return _require_reason_codes(tuple(codes), require_nonempty=True)


def _row_sort_key(
    row: ResearchTeamDomainSourceResolutionMemoryLadderRow,
) -> tuple[int, Decimal, Decimal, Decimal, str, str, str]:
    return (
        STATUS_SORT_RANK[row.status],
        -row.memory_ladder_pressure_score,
        row.resolution_memory_ladder_score,
        row.memory_coverage_ratio,
        row.domain_label,
        row.team_label,
        row.source_family_label,
    )


def _normalize_inputs(
    inputs: Iterable[ResearchTeamDomainSourceResolutionMemoryLadderInput],
) -> tuple[ResearchTeamDomainSourceResolutionMemoryLadderInput, ...]:
    if isinstance(inputs, (str, bytes)):
        raise ValueError("inputs must be an iterable")
    try:
        normalized = tuple(inputs)
    except TypeError as exc:
        raise ValueError("inputs must be an iterable") from exc
    seen_keys: set[tuple[str, str, str]] = set()
    for item in normalized:
        _require_exact_type(
            item,
            ResearchTeamDomainSourceResolutionMemoryLadderInput,
            "input",
        )
        _require_hard_flags("input", item)
        key = (item.domain_label, item.team_label, item.source_family_label)
        if key in seen_keys:
            raise ValueError("team-domain-source labels must be unique")
        seen_keys.add(key)
    return normalized


def _report_status(
    rows: tuple[ResearchTeamDomainSourceResolutionMemoryLadderRow, ...],
) -> str:
    statuses = tuple(row.status for row in rows)
    if "block" in statuses:
        return "block"
    if "watch" in statuses:
        return "watch"
    return "pass"


def _report_reason_codes(
    rows: tuple[ResearchTeamDomainSourceResolutionMemoryLadderRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return (EMPTY_REASON,)
    seen = {code for row in rows for code in row.reason_codes}
    return tuple(code for code in REASON_SEQUENCE if code in seen)


def _reason_code_counts(
    rows: tuple[ResearchTeamDomainSourceResolutionMemoryLadderRow, ...],
) -> tuple[ResearchTeamDomainSourceResolutionMemoryLadderReasonCodeCount, ...]:
    if not rows:
        return ()
    counter: Counter[str] = Counter()
    for row in rows:
        counter.update(row.reason_codes)
    row_count = _count(len(rows))
    return tuple(
        ResearchTeamDomainSourceResolutionMemoryLadderReasonCodeCount(
            reason_code=code,
            count=_count(counter[code]),
            row_ratio=_ratio(_count(counter[code]), row_count),
        )
        for code in REASON_SEQUENCE
        if counter[code]
    )


def _status_count(
    rows: tuple[ResearchTeamDomainSourceResolutionMemoryLadderRow, ...],
    status: str,
) -> Decimal:
    return _count(sum(1 for row in rows if row.status == status))


def _require_exact_type(value: object, expected_type: type, label: str) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{label} must be a {expected_type.__name__}")


def _require_public_string(name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{name} must be exactly str")
    if not value or value.strip() != value:
        raise ValueError(f"{name} must be a canonical non-empty string")
    if any(character in value for character in ("\n", "\r", "\t")):
        raise ValueError(f"{name} must be single line")


def _require_public_label(name: str, value: object) -> None:
    _require_public_string(name, value)
    assert type(value) is str
    if PUBLIC_LABEL_RE.fullmatch(value) is None:
        raise ValueError(f"{name} must be public aggregate labels")
    if _has_unsafe_public_fragment(value):
        raise ValueError(f"{name} must be public aggregate labels")


def _has_unsafe_public_fragment(value: str) -> bool:
    normalized = value.lower()
    return any(fragment in normalized for fragment in UNSAFE_PUBLIC_FRAGMENTS)


def _require_decimal(name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{name} must be finite")
    with localcontext(DECIMAL_CONTEXT):
        normalized = value.quantize(QUANTUM)
    if normalized == ZERO:
        return ZERO
    return normalized


def _require_nonnegative_decimal(name: str, value: object) -> Decimal:
    normalized = _require_decimal(name, value)
    if normalized < ZERO:
        raise ValueError(f"{name} must be nonnegative")
    return normalized


def _require_positive_decimal(name: str, value: object) -> Decimal:
    normalized = _require_decimal(name, value)
    if normalized <= ZERO:
        raise ValueError(f"{name} must be positive")
    return normalized


def _require_count_decimal(name: str, value: object) -> Decimal:
    return _require_nonnegative_decimal(name, value)


def _require_nonnegative_whole_decimal(name: str, value: object) -> Decimal:
    normalized = _require_nonnegative_decimal(name, value)
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{name} must be a nonnegative whole Decimal")
    return normalized


def _require_ratio_decimal(name: str, value: object) -> Decimal:
    normalized = _require_decimal(name, value)
    if normalized < ZERO or normalized > ONE:
        raise ValueError(f"{name} must be between 0 and 1")
    return normalized


def _count(value: int) -> Decimal:
    return _require_count_decimal("count", Decimal(value))


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    numerator = _require_nonnegative_decimal("numerator", numerator)
    denominator = _require_nonnegative_decimal("denominator", denominator)
    if denominator == ZERO:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return _require_ratio_decimal("ratio", numerator / denominator)


def _bounded_ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    numerator = _require_nonnegative_decimal("numerator", numerator)
    denominator = _require_positive_decimal("denominator", denominator)
    with localcontext(DECIMAL_CONTEXT):
        value = _require_decimal("bounded_ratio", numerator / denominator)
    if value > ONE:
        return ONE
    if value < ZERO:
        raise ValueError("bounded_ratio must be nonnegative")
    return value


def _mean_ratio(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        total = sum((_require_ratio_decimal("mean_ratio", value) for value in values), ZERO)
        return _require_ratio_decimal("mean_ratio", total / Decimal(len(values)))


def _subtract_decimal(left: Decimal, right: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return _require_decimal("difference", left - right)


def _threshold_pressure(
    value: Decimal,
    *,
    pass_value: Decimal,
    watch_value: Decimal,
) -> Decimal:
    if value <= pass_value:
        return ZERO
    if value >= watch_value:
        return ONE
    with localcontext(DECIMAL_CONTEXT):
        return _require_ratio_decimal(
            "threshold_pressure",
            (value - pass_value) / (watch_value - pass_value),
        )


def _inverse_threshold_pressure(
    value: Decimal,
    *,
    pass_value: Decimal,
    watch_value: Decimal,
) -> Decimal:
    if value >= pass_value:
        return ZERO
    if value <= watch_value:
        return ONE
    with localcontext(DECIMAL_CONTEXT):
        return _require_ratio_decimal(
            "inverse_threshold_pressure",
            (pass_value - value) / (pass_value - watch_value),
        )


def _min_decimal(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return ZERO
    return min(values)


def _max_decimal(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return ZERO
    return max(values)


def _as_utc(name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{name} must be UTC-aware")
    return value.astimezone(UTC)


def _as_generated_at_utc(name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{name} must be UTC")
    if value.utcoffset() != ZERO_SECONDS:
        raise ValueError(f"{name} must be UTC")
    return value.astimezone(UTC)


ZERO_SECONDS = datetime(2026, 1, 1, tzinfo=UTC).utcoffset()


def _require_status(name: str, value: object) -> None:
    if (
        type(value) is not str
        or value not in RESEARCH_TEAM_DOMAIN_SOURCE_RESOLUTION_MEMORY_LADDER_STATUSES
    ):
        raise ValueError(f"{name} must be pass, watch, or block")


def _require_reason_codes(
    value: object,
    *,
    require_nonempty: bool,
) -> tuple[str, ...]:
    if not isinstance(value, (list, tuple)):
        raise ValueError("reason_codes must be a list or tuple")
    normalized = tuple(value)
    if require_nonempty and not normalized:
        raise ValueError("reason_codes must be non-empty")
    seen: set[str] = set()
    for code in normalized:
        _require_public_string("reason_code", code)
        if code not in REASON_SEQUENCE:
            raise ValueError("reason_code must be known")
        if code in seen:
            raise ValueError("reason_codes must be unique")
        seen.add(code)
    return tuple(code for code in REASON_SEQUENCE if code in seen)


def _require_report_reason_codes(value: object) -> tuple[str, ...]:
    if not isinstance(value, (list, tuple)):
        raise ValueError("reason_codes must be a list or tuple")
    normalized = tuple(value)
    if normalized == (EMPTY_REASON,):
        return normalized
    return _require_reason_codes(normalized, require_nonempty=True)


def _require_reason_code_counts(
    values: object,
) -> tuple[ResearchTeamDomainSourceResolutionMemoryLadderReasonCodeCount, ...]:
    if not isinstance(values, (list, tuple)):
        raise ValueError("reason_code_counts must be a list or tuple")
    normalized = tuple(values)
    seen: set[str] = set()
    for item in normalized:
        _require_exact_type(
            item,
            ResearchTeamDomainSourceResolutionMemoryLadderReasonCodeCount,
            "reason_code_count",
        )
        if item.reason_code in seen:
            raise ValueError("reason_code_counts must be unique")
        seen.add(item.reason_code)
    return tuple(sorted(normalized, key=lambda item: REASON_SEQUENCE.index(item.reason_code)))


def _require_rows(
    rows: object,
) -> tuple[ResearchTeamDomainSourceResolutionMemoryLadderRow, ...]:
    if not isinstance(rows, (list, tuple)):
        raise ValueError("rows must be a list or tuple")
    normalized = tuple(rows)
    seen_keys: set[tuple[str, str, str]] = set()
    for row in normalized:
        _require_exact_type(row, ResearchTeamDomainSourceResolutionMemoryLadderRow, "row")
        key = (row.domain_label, row.team_label, row.source_family_label)
        if key in seen_keys:
            raise ValueError("team-domain-source labels must be unique")
        seen_keys.add(key)
    return tuple(sorted(normalized, key=_row_sort_key))


def _require_hard_flags(name: str, value: object) -> None:
    if getattr(value, "paper_only", None) is not True:
        raise ValueError(f"{name} paper_only must be True")
    if getattr(value, "report_only", None) is not True:
        raise ValueError(f"{name} report_only must be True")
    if getattr(value, "readonly", None) is not True:
        raise ValueError(f"{name} readonly must be True")


def _validate_row(row: ResearchTeamDomainSourceResolutionMemoryLadderRow) -> None:
    expected_coverage = _ratio(
        row.verified_resolution_memory_count,
        row.resolution_memory_count,
    )
    if row.memory_coverage_ratio != expected_coverage:
        raise ValueError("memory_coverage_ratio must match verified over total memory")
    expected_score = _resolution_memory_ladder_score(
        memory_coverage_ratio=expected_coverage,
        source_resolution_score=row.source_resolution_score,
        memory_staleness_ratio=row.memory_staleness_ratio,
        ladder_depth_ratio=row.ladder_depth_ratio,
        contradiction_ratio=row.contradiction_ratio,
    )
    if row.resolution_memory_ladder_score != expected_score:
        raise ValueError("resolution_memory_ladder_score must match row inputs")
    if (
        (row.status == "pass" and row.memory_ladder_pressure_score != ZERO)
        or (row.status == "watch" and row.memory_ladder_pressure_score == ZERO)
        or (row.status == "block" and row.memory_ladder_pressure_score != ONE)
    ):
        raise ValueError("status must match row inputs")
    block_reason_codes = frozenset(REASON_SEQUENCE[:5])
    watch_reason_codes = frozenset(REASON_SEQUENCE[5:10])
    row_reason_codes = frozenset(row.reason_codes)
    if row.status == "pass" and row.reason_codes != (
        "source_resolution_memory_ladder_pass",
    ):
        raise ValueError("reason_codes must match row inputs")
    if row.status == "watch" and (
        not row_reason_codes
        or not row_reason_codes.issubset(watch_reason_codes)
    ):
        raise ValueError("reason_codes must match row inputs")
    if row.status == "block" and (
        not row_reason_codes.intersection(block_reason_codes)
        or "source_resolution_memory_ladder_pass" in row_reason_codes
    ):
        raise ValueError("reason_codes must match row inputs")


def _validate_report(report: ResearchTeamDomainSourceResolutionMemoryLadderReport) -> None:
    rows = report.rows
    expected_ranks = tuple(_count(index) for index in range(1, len(rows) + 1))
    if tuple(row.resolution_rank for row in rows) != expected_ranks:
        raise ValueError("resolution_rank must match row order")
    if any(row.observed_at > report.generated_at for row in rows):
        raise ValueError("observed_at must not be after generated_at")
    if report.input_count != _count(len(rows)) or report.row_count != _count(len(rows)):
        raise ValueError("row_count must match rows")
    if report.pass_count != _status_count(rows, "pass"):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _status_count(rows, "watch"):
        raise ValueError("watch_count must match rows")
    if report.block_count != _status_count(rows, "block"):
        raise ValueError("block_count must match rows")
    watch_block_count = _count(sum(1 for row in rows if row.status in ("watch", "block")))
    if report.watch_block_ratio != _ratio(watch_block_count, _count(len(rows))):
        raise ValueError("watch_block_ratio must match rows")
    if report.min_memory_coverage_ratio != _min_decimal(
        tuple(row.memory_coverage_ratio for row in rows),
    ):
        raise ValueError("min_memory_coverage_ratio must match rows")
    if report.min_ladder_depth_ratio != _min_decimal(
        tuple(row.ladder_depth_ratio for row in rows),
    ):
        raise ValueError("min_ladder_depth_ratio must match rows")
    if report.min_source_resolution_score != _min_decimal(
        tuple(row.source_resolution_score for row in rows),
    ):
        raise ValueError("min_source_resolution_score must match rows")
    if report.min_resolution_memory_ladder_score != _min_decimal(
        tuple(row.resolution_memory_ladder_score for row in rows),
    ):
        raise ValueError("min_resolution_memory_ladder_score must match rows")
    if report.max_memory_age_seconds != _max_decimal(
        tuple(row.memory_age_seconds for row in rows),
    ):
        raise ValueError("max_memory_age_seconds must match rows")
    if report.max_contradiction_ratio != _max_decimal(
        tuple(row.contradiction_ratio for row in rows),
    ):
        raise ValueError("max_contradiction_ratio must match rows")
    if report.max_memory_ladder_pressure_score != _max_decimal(
        tuple(row.memory_ladder_pressure_score for row in rows),
    ):
        raise ValueError("max_memory_ladder_pressure_score must match rows")
    if report.status != _report_status(rows):
        raise ValueError("status must match rows")
    if report.reason_codes != _report_reason_codes(rows):
        raise ValueError("reason_codes must match rows")
    if report.reason_code_counts != _reason_code_counts(rows):
        raise ValueError("reason_code_counts must match rows")


def _apply_or_verify_digest(
    value: (
        ResearchTeamDomainSourceResolutionMemoryLadderRow
        | ResearchTeamDomainSourceResolutionMemoryLadderReport
    ),
) -> None:
    current = value.derived_validation_digest
    payload = _json_ready(asdict(value))
    if type(payload) is not dict:
        raise ValueError("digest payload must be a JSON object")
    expected = _digest_from_payload(payload)
    if current:
        _require_sha256_digest("derived_validation_digest", current)
        if current != expected:
            raise ValueError("derived_validation_digest does not match report payload")
    else:
        object.__setattr__(value, "derived_validation_digest", expected)


def _verify_digest(
    value: (
        ResearchTeamDomainSourceResolutionMemoryLadderRow
        | ResearchTeamDomainSourceResolutionMemoryLadderReport
    ),
) -> None:
    payload = _json_ready(asdict(value))
    if type(payload) is not dict:
        raise ValueError("digest payload must be a JSON object")
    expected = _digest_from_payload(payload)
    if value.derived_validation_digest != expected:
        raise ValueError("derived_validation_digest does not match report payload")


def _digest_from_payload(payload: Mapping[str, object]) -> str:
    unsigned = dict(payload)
    unsigned.pop("derived_validation_digest", None)
    encoded = json.dumps(unsigned, sort_keys=True, separators=(",", ":")).encode()
    return sha256(encoded).hexdigest()


def _require_sha256_digest(name: str, value: object) -> None:
    if type(value) is not str or len(value) != 64:
        raise ValueError(f"{name} must be a sha256 digest")
    if any(char not in HEX_CHARS for char in value):
        raise ValueError(f"{name} must be a sha256 digest")


def _json_ready(value: object) -> object:
    if type(value) is Decimal:
        return format(_require_decimal("decimal", value), "f")
    if type(value) is datetime:
        return _as_utc("datetime", value).isoformat()
    if isinstance(value, tuple):
        return [_json_ready(item) for item in value]
    if isinstance(value, list):
        return [_json_ready(item) for item in value]
    if isinstance(value, Mapping):
        return {str(key): _json_ready(item) for key, item in value.items()}
    return value


def _validate_public_payload(payload: dict[str, object]) -> None:
    _validate_public_tree(payload)
    _require_payload_keys("report payload", payload, REPORT_PAYLOAD_KEYS)
    _require_hard_flags("report payload", _MappingFlags(payload))
    _require_status("status", payload.get("status"))
    if payload.get("report_mode") != REPORT_MODE_BY_STATUS[payload["status"]]:
        raise ValueError("report_mode must match status")
    _require_sha256_digest(
        "derived_validation_digest",
        payload.get("derived_validation_digest"),
    )
    rows = payload.get("rows")
    if not isinstance(rows, list):
        raise ValueError("rows must be a list")
    for row in rows:
        if type(row) is not dict:
            raise ValueError("rows must contain objects")
        _require_payload_keys("row payload", row, ROW_PAYLOAD_KEYS)
        _require_status("row status", row.get("status"))
        _require_sha256_digest(
            "row derived_validation_digest",
            row.get("derived_validation_digest"),
        )
        _require_hard_flags("row payload", _MappingFlags(row))
        if row["derived_validation_digest"] != _digest_from_payload(row):
            raise ValueError("derived_validation_digest does not match row payload")
    reason_code_counts = payload.get("reason_code_counts")
    if not isinstance(reason_code_counts, list):
        raise ValueError("reason_code_counts must be a list")
    for item in reason_code_counts:
        if type(item) is not dict:
            raise ValueError("reason_code_counts must contain objects")
        _require_payload_keys(
            "reason_code_count payload",
            item,
            REASON_COUNT_PAYLOAD_KEYS,
        )
        _require_hard_flags("reason_code_count payload", _MappingFlags(item))
    _validate_decimal_string_fields(payload)
    _report_from_public_payload(payload)


def _validate_public_tree(value: object) -> None:
    if type(value) is dict:
        for key, item in value.items():
            _require_public_label("payload key", key)
            _validate_public_tree(item)
        return
    if type(value) is list:
        for item in value:
            _validate_public_tree(item)
        return
    if type(value) is bool or value is None:
        return
    if type(value) is str:
        if _has_unsafe_public_fragment(value):
            raise ValueError("public aggregate labels must not expose raw identifiers")
        return
    if isinstance(value, Decimal) or type(value) in (int, float):
        raise ValueError("numeric payload values must be decimal strings")
    raise ValueError("public payload values must be JSON primitives")


def _require_payload_keys(
    name: str,
    payload: Mapping[str, object],
    expected_keys: frozenset[str],
) -> None:
    if frozenset(payload.keys()) != expected_keys:
        raise ValueError(f"{name} keys must match report schema")


def _validate_decimal_string_fields(payload: dict[str, object]) -> None:
    for key, value in payload.items():
        if key in {"paper_only", "report_only", "readonly"}:
            continue
        if key.endswith(("_count", "_ratio", "_score", "_seconds", "_rank")):
            _require_decimal_string(key, value)
    for row in payload["rows"]:
        assert type(row) is dict
        for key, value in row.items():
            if key in {"paper_only", "report_only", "readonly"}:
                continue
            if key.endswith(("_count", "_ratio", "_score", "_seconds", "_rank")):
                _require_decimal_string(key, value)
    for item in payload["reason_code_counts"]:
        assert type(item) is dict
        _require_decimal_string("count", item["count"])
        _require_decimal_string("row_ratio", item["row_ratio"])


def _require_decimal_string(name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{name} numeric payload values must be decimal strings")
    try:
        normalized = _require_decimal(name, Decimal(value))
    except (InvalidOperation, ValueError) as exc:
        raise ValueError(f"{name} must be a canonical decimal string") from exc
    if value != format(normalized, "f"):
        raise ValueError(f"{name} must be a canonical decimal string")


def _report_from_public_payload(
    payload: dict[str, object],
) -> ResearchTeamDomainSourceResolutionMemoryLadderReport:
    rows_value = payload["rows"]
    reason_counts_value = payload["reason_code_counts"]
    assert type(rows_value) is list
    assert type(reason_counts_value) is list
    rows = tuple(_row_from_public_payload(item) for item in rows_value)
    reason_code_counts = tuple(
        _reason_count_from_public_payload(item) for item in reason_counts_value
    )
    return ResearchTeamDomainSourceResolutionMemoryLadderReport(
        generated_at=_public_utc_datetime(payload, "generated_at"),
        config_version=_public_string(payload, "config_version"),
        input_count=_public_decimal(payload, "input_count"),
        row_count=_public_decimal(payload, "row_count"),
        pass_count=_public_decimal(payload, "pass_count"),
        watch_count=_public_decimal(payload, "watch_count"),
        block_count=_public_decimal(payload, "block_count"),
        watch_block_ratio=_public_decimal(payload, "watch_block_ratio"),
        min_memory_coverage_ratio=_public_decimal(
            payload,
            "min_memory_coverage_ratio",
        ),
        min_ladder_depth_ratio=_public_decimal(payload, "min_ladder_depth_ratio"),
        min_source_resolution_score=_public_decimal(
            payload,
            "min_source_resolution_score",
        ),
        min_resolution_memory_ladder_score=_public_decimal(
            payload,
            "min_resolution_memory_ladder_score",
        ),
        max_memory_age_seconds=_public_decimal(payload, "max_memory_age_seconds"),
        max_contradiction_ratio=_public_decimal(
            payload,
            "max_contradiction_ratio",
        ),
        max_memory_ladder_pressure_score=_public_decimal(
            payload,
            "max_memory_ladder_pressure_score",
        ),
        status=_public_string(payload, "status"),
        report_mode=_public_string(payload, "report_mode"),
        reason_codes=_public_string_tuple(payload, "reason_codes"),
        reason_code_counts=reason_code_counts,
        rows=rows,
        derived_validation_digest=_public_string(
            payload,
            "derived_validation_digest",
        ),
        paper_only=_public_bool(payload, "paper_only"),
        report_only=_public_bool(payload, "report_only"),
        readonly=_public_bool(payload, "readonly"),
    )


def _row_from_public_payload(
    payload: object,
) -> ResearchTeamDomainSourceResolutionMemoryLadderRow:
    if type(payload) is not dict:
        raise ValueError("rows must contain objects")
    return ResearchTeamDomainSourceResolutionMemoryLadderRow(
        resolution_rank=_public_decimal(payload, "resolution_rank"),
        domain_label=_public_string(payload, "domain_label"),
        team_label=_public_string(payload, "team_label"),
        source_family_label=_public_string(payload, "source_family_label"),
        status=_public_string(payload, "status"),
        memory_ladder_pressure_score=_public_decimal(
            payload,
            "memory_ladder_pressure_score",
        ),
        resolution_memory_count=_public_decimal(
            payload,
            "resolution_memory_count",
        ),
        verified_resolution_memory_count=_public_decimal(
            payload,
            "verified_resolution_memory_count",
        ),
        memory_coverage_ratio=_public_decimal(payload, "memory_coverage_ratio"),
        source_resolution_score=_public_decimal(
            payload,
            "source_resolution_score",
        ),
        memory_age_seconds=_public_decimal(payload, "memory_age_seconds"),
        memory_staleness_ratio=_public_decimal(
            payload,
            "memory_staleness_ratio",
        ),
        ladder_depth_count=_public_decimal(payload, "ladder_depth_count"),
        ladder_depth_ratio=_public_decimal(payload, "ladder_depth_ratio"),
        contradiction_ratio=_public_decimal(payload, "contradiction_ratio"),
        resolution_memory_ladder_score=_public_decimal(
            payload,
            "resolution_memory_ladder_score",
        ),
        observed_at=_public_utc_datetime(payload, "observed_at"),
        reason_codes=_public_string_tuple(payload, "reason_codes"),
        derived_validation_digest=_public_string(
            payload,
            "derived_validation_digest",
        ),
        paper_only=_public_bool(payload, "paper_only"),
        report_only=_public_bool(payload, "report_only"),
        readonly=_public_bool(payload, "readonly"),
    )


def _reason_count_from_public_payload(
    payload: object,
) -> ResearchTeamDomainSourceResolutionMemoryLadderReasonCodeCount:
    if type(payload) is not dict:
        raise ValueError("reason_code_counts must contain objects")
    return ResearchTeamDomainSourceResolutionMemoryLadderReasonCodeCount(
        reason_code=_public_string(payload, "reason_code"),
        count=_public_decimal(payload, "count"),
        row_ratio=_public_decimal(payload, "row_ratio"),
        paper_only=_public_bool(payload, "paper_only"),
        report_only=_public_bool(payload, "report_only"),
        readonly=_public_bool(payload, "readonly"),
    )


def _public_string(payload: Mapping[str, object], key: str) -> str:
    value = payload.get(key)
    if type(value) is not str:
        raise ValueError(f"{key} must be exactly str")
    return value


def _public_bool(payload: Mapping[str, object], key: str) -> bool:
    value = payload.get(key)
    if type(value) is not bool:
        raise ValueError(f"{key} must be a bool")
    return value


def _public_decimal(payload: Mapping[str, object], key: str) -> Decimal:
    value = payload.get(key)
    _require_decimal_string(key, value)
    assert type(value) is str
    return Decimal(value)


def _public_string_tuple(
    payload: Mapping[str, object],
    key: str,
) -> tuple[str, ...]:
    value = payload.get(key)
    if type(value) is not list:
        raise ValueError(f"{key} must be a list")
    for item in value:
        if type(item) is not str:
            raise ValueError(f"{key} must contain strings")
    return tuple(value)


def _public_utc_datetime(
    payload: Mapping[str, object],
    key: str,
) -> datetime:
    value = _public_string(payload, key)
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError as exc:
        raise ValueError(f"{key} must be a canonical UTC datetime") from exc
    normalized = _as_generated_at_utc(key, parsed)
    if value != normalized.isoformat():
        raise ValueError(f"{key} must be a canonical UTC datetime")
    return normalized
