"""Deterministic paper-only domain authority memory report for research teams."""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable, Mapping
from dataclasses import asdict, dataclass, is_dataclass, replace
from datetime import UTC, datetime
from decimal import (
    Context,
    Decimal,
    DivisionByZero,
    InvalidOperation,
    Overflow,
    ROUND_HALF_EVEN,
    localcontext,
)
from hashlib import sha256
import json
import re
from typing import Any


DEFAULT_RESEARCH_TEAM_DOMAIN_SOURCE_AUTHORITY_MEMORY_CONFIG_VERSION = (
    "research-team-domain-source-authority-memory-report-v1"
)
RESEARCH_TEAM_DOMAIN_SOURCE_AUTHORITY_MEMORY_STATUSES = ("pass", "watch", "block")

QUANTUM = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
PUBLIC_LABEL_RE = re.compile(r"^[a-z0-9][a-z0-9_.-]{0,127}$")
HEX_CHARS = frozenset("0123456789abcdef")

REASON_SEQUENCE = (
    "source_authority_memory_coverage_block",
    "source_authority_score_block",
    "source_authority_memory_staleness_block",
    "source_authority_contradiction_block",
    "source_authority_memory_coverage_watch",
    "source_authority_score_watch",
    "source_authority_memory_staleness_watch",
    "source_authority_contradiction_watch",
    "source_authority_memory_pass",
)
EMPTY_REASON = "source_authority_memory_empty"
REPORT_MODE_BY_STATUS = {
    "pass": "paper_authority_memory_monitor",
    "watch": "paper_authority_memory_watch",
    "block": "paper_authority_memory_block",
}
STATUS_SORT_RANK = {"block": 0, "watch": 1, "pass": 2}

REPORT_PAYLOAD_KEYS = (
    "generated_at",
    "config_version",
    "input_count",
    "row_count",
    "pass_count",
    "watch_count",
    "block_count",
    "watch_block_ratio",
    "min_memory_coverage_ratio",
    "min_authority_score",
    "max_memory_age_seconds",
    "max_contradiction_ratio",
    "max_authority_pressure_score",
    "status",
    "report_mode",
    "reason_codes",
    "reason_code_counts",
    "rows",
    "derived_validation_digest",
    "paper_only",
    "report_only",
    "readonly",
)
ROW_PAYLOAD_KEYS = (
    "authority_rank",
    "domain_label",
    "team_label",
    "authority_family_label",
    "status",
    "authority_pressure_score",
    "authority_memory_count",
    "verified_authority_memory_count",
    "memory_coverage_ratio",
    "authority_score",
    "memory_age_seconds",
    "memory_staleness_ratio",
    "contradiction_ratio",
    "observed_at",
    "reason_codes",
    "derived_validation_digest",
    "paper_only",
    "report_only",
    "readonly",
)
REASON_COUNT_PAYLOAD_KEYS = (
    "reason_code",
    "count",
    "row_ratio",
    "paper_only",
    "report_only",
    "readonly",
)


def _join_parts(*parts: str) -> str:
    return "".join(parts)


def _fixed_decimal_context() -> Context:
    return Context(
        prec=64,
        rounding=ROUND_HALF_EVEN,
        Emin=-999999,
        Emax=999999,
        capitals=1,
        clamp=0,
        flags=[],
        traps=[DivisionByZero, InvalidOperation, Overflow],
    )


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
        _join_parts("acc", "ount"),
        _join_parts("ses", "sion"),
        _join_parts("pass", "word"),
        _join_parts("oau", "th"),
        _join_parts("bear", "er"),
        _join_parts("coo", "kie"),
        _join_parts("log", "in"),
        _join_parts("user", "name"),
        _join_parts("em", "ail"),
        _join_parts("pho", "ne"),
        _join_parts("ip", "_address"),
        _join_parts("mnemo", "nic"),
        _join_parts("seed", "_phrase"),
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
    "DEFAULT_RESEARCH_TEAM_DOMAIN_SOURCE_AUTHORITY_MEMORY_CONFIG_VERSION",
    "RESEARCH_TEAM_DOMAIN_SOURCE_AUTHORITY_MEMORY_STATUSES",
    "ResearchTeamDomainSourceAuthorityMemoryConfig",
    "ResearchTeamDomainSourceAuthorityMemoryInput",
    "ResearchTeamDomainSourceAuthorityMemoryReasonCodeCount",
    "ResearchTeamDomainSourceAuthorityMemoryReport",
    "ResearchTeamDomainSourceAuthorityMemoryRow",
    "build_research_team_domain_source_authority_memory_report",
    "research_team_domain_source_authority_memory_report_digest",
    "research_team_domain_source_authority_memory_report_payload",
    "validate_research_team_domain_source_authority_memory_report_digest",
)


class _FinalDataclassMeta(type):
    def __new__(
        metaclass,
        name: str,
        bases: tuple[type, ...],
        namespace: dict[str, object],
        **kwargs: object,
    ) -> type:
        root = globals().get("_FinalDataclass")
        if root is not None:
            for base in bases:
                if isinstance(base, metaclass) and base is not root:
                    raise TypeError(f"{base.__name__} subclass is not allowed")
        return super().__new__(metaclass, name, bases, namespace, **kwargs)


class _FinalDataclass(metaclass=_FinalDataclassMeta):
    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        for base in cls.__bases__:
            if base is not _FinalDataclass and issubclass(base, _FinalDataclass):
                raise TypeError(f"{base.__name__} subclass is not allowed")


@dataclass(frozen=True)
class ResearchTeamDomainSourceAuthorityMemoryConfig(_FinalDataclass):
    config_version: str = DEFAULT_RESEARCH_TEAM_DOMAIN_SOURCE_AUTHORITY_MEMORY_CONFIG_VERSION
    min_pass_memory_coverage_ratio: Decimal = Decimal("0.900000")
    min_watch_memory_coverage_ratio: Decimal = Decimal("0.700000")
    min_pass_authority_score: Decimal = Decimal("0.800000")
    min_watch_authority_score: Decimal = Decimal("0.600000")
    max_pass_memory_age_seconds: Decimal = Decimal("86400.000000")
    max_watch_memory_age_seconds: Decimal = Decimal("604800.000000")
    max_pass_contradiction_ratio: Decimal = Decimal("0.050000")
    max_watch_contradiction_ratio: Decimal = Decimal("0.200000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchTeamDomainSourceAuthorityMemoryConfig, "config")
        _require_public_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_TEAM_DOMAIN_SOURCE_AUTHORITY_MEMORY_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "min_pass_memory_coverage_ratio",
            "min_watch_memory_coverage_ratio",
            "min_pass_authority_score",
            "min_watch_authority_score",
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
        if self.min_pass_memory_coverage_ratio < self.min_watch_memory_coverage_ratio:
            raise ValueError(
                "min_watch_memory_coverage_ratio must not exceed "
                "min_pass_memory_coverage_ratio",
            )
        if self.min_pass_authority_score < self.min_watch_authority_score:
            raise ValueError(
                "min_watch_authority_score must not exceed min_pass_authority_score",
            )
        if self.max_pass_memory_age_seconds > self.max_watch_memory_age_seconds:
            raise ValueError(
                "max_watch_memory_age_seconds must be at least "
                "max_pass_memory_age_seconds",
            )
        if self.max_pass_contradiction_ratio > self.max_watch_contradiction_ratio:
            raise ValueError(
                "max_watch_contradiction_ratio must be at least "
                "max_pass_contradiction_ratio",
            )
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class ResearchTeamDomainSourceAuthorityMemoryInput(_FinalDataclass):
    domain_label: str
    team_label: str
    authority_family_label: str
    authority_memory_count: Decimal
    verified_authority_memory_count: Decimal
    authority_score: Decimal
    memory_age_seconds: Decimal
    contradiction_ratio: Decimal
    observed_at: datetime
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchTeamDomainSourceAuthorityMemoryInput, "input")
        for field_name in ("domain_label", "team_label", "authority_family_label"):
            _require_public_label(field_name, getattr(self, field_name))
        for field_name in (
            "authority_memory_count",
            "verified_authority_memory_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_count_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "memory_age_seconds",
            _require_nonnegative_decimal("memory_age_seconds", self.memory_age_seconds),
        )
        for field_name in ("authority_score", "contradiction_ratio"):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        if self.verified_authority_memory_count > self.authority_memory_count:
            raise ValueError(
                "verified_authority_memory_count must not exceed "
                "authority_memory_count",
            )
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        _require_hard_flags("input", self)


@dataclass(frozen=True)
class ResearchTeamDomainSourceAuthorityMemoryRow(_FinalDataclass):
    authority_rank: Decimal
    domain_label: str
    team_label: str
    authority_family_label: str
    status: str
    authority_pressure_score: Decimal
    authority_memory_count: Decimal
    verified_authority_memory_count: Decimal
    memory_coverage_ratio: Decimal
    authority_score: Decimal
    memory_age_seconds: Decimal
    memory_staleness_ratio: Decimal
    contradiction_ratio: Decimal
    observed_at: datetime
    reason_codes: tuple[str, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchTeamDomainSourceAuthorityMemoryRow, "row")
        object.__setattr__(
            self,
            "authority_rank",
            _require_count_decimal("authority_rank", self.authority_rank),
        )
        for field_name in ("domain_label", "team_label", "authority_family_label"):
            _require_public_label(field_name, getattr(self, field_name))
        _require_status("status", self.status)
        for field_name in (
            "authority_pressure_score",
            "memory_coverage_ratio",
            "authority_score",
            "memory_staleness_ratio",
            "contradiction_ratio",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "authority_memory_count",
            "verified_authority_memory_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_count_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "memory_age_seconds",
            _require_nonnegative_decimal("memory_age_seconds", self.memory_age_seconds),
        )
        if self.verified_authority_memory_count > self.authority_memory_count:
            raise ValueError(
                "verified_authority_memory_count must not exceed "
                "authority_memory_count",
            )
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        object.__setattr__(
            self,
            "reason_codes",
            _require_reason_codes(self.reason_codes, require_nonempty=True),
        )
        _require_hard_flags("row", self)
        _validate_row(self)
        _apply_or_verify_digest(self)


@dataclass(frozen=True)
class ResearchTeamDomainSourceAuthorityMemoryReasonCodeCount(_FinalDataclass):
    reason_code: str
    count: Decimal
    row_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchTeamDomainSourceAuthorityMemoryReasonCodeCount,
            "reason_code_count",
        )
        _require_public_string("reason_code", self.reason_code)
        if self.reason_code not in REASON_SEQUENCE:
            raise ValueError("reason_code must be known")
        object.__setattr__(self, "count", _require_count_decimal("count", self.count))
        object.__setattr__(
            self,
            "row_ratio",
            _require_ratio_decimal("row_ratio", self.row_ratio),
        )
        _require_hard_flags("reason_code_count", self)


@dataclass(frozen=True)
class ResearchTeamDomainSourceAuthorityMemoryReport(_FinalDataclass):
    generated_at: datetime
    config_version: str
    input_count: Decimal
    row_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    watch_block_ratio: Decimal
    min_memory_coverage_ratio: Decimal
    min_authority_score: Decimal
    max_memory_age_seconds: Decimal
    max_contradiction_ratio: Decimal
    max_authority_pressure_score: Decimal
    status: str
    report_mode: str
    reason_codes: tuple[str, ...]
    reason_code_counts: tuple[
        ResearchTeamDomainSourceAuthorityMemoryReasonCodeCount,
        ...,
    ]
    rows: tuple[ResearchTeamDomainSourceAuthorityMemoryRow, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchTeamDomainSourceAuthorityMemoryReport, "report")
        object.__setattr__(
            self,
            "generated_at",
            _as_generated_at_utc("generated_at", self.generated_at),
        )
        _require_public_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_TEAM_DOMAIN_SOURCE_AUTHORITY_MEMORY_CONFIG_VERSION
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
        for field_name in (
            "watch_block_ratio",
            "min_memory_coverage_ratio",
            "min_authority_score",
            "max_contradiction_ratio",
            "max_authority_pressure_score",
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


def build_research_team_domain_source_authority_memory_report(
    inputs: Iterable[ResearchTeamDomainSourceAuthorityMemoryInput],
    *,
    config: ResearchTeamDomainSourceAuthorityMemoryConfig,
    generated_at: datetime,
) -> ResearchTeamDomainSourceAuthorityMemoryReport:
    config = _normalize_config(config)
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
    return ResearchTeamDomainSourceAuthorityMemoryReport(
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
        min_authority_score=_min_decimal(tuple(row.authority_score for row in rows)),
        max_memory_age_seconds=_max_decimal(
            tuple(row.memory_age_seconds for row in rows),
        ),
        max_contradiction_ratio=_max_decimal(
            tuple(row.contradiction_ratio for row in rows),
        ),
        max_authority_pressure_score=_max_decimal(
            tuple(row.authority_pressure_score for row in rows),
        ),
        status=status,
        report_mode=REPORT_MODE_BY_STATUS[status],
        reason_codes=_report_reason_codes(rows),
        reason_code_counts=_reason_code_counts(rows),
        rows=rows,
    )


def research_team_domain_source_authority_memory_report_payload(
    report: ResearchTeamDomainSourceAuthorityMemoryReport | Mapping[str, object],
    *,
    validation_config: ResearchTeamDomainSourceAuthorityMemoryConfig | None = None,
) -> dict[str, object]:
    if type(report) is ResearchTeamDomainSourceAuthorityMemoryReport:
        _require_hard_flags("report", report)
        _verify_digest(report)
        for row in report.rows:
            _verify_digest(row)
        payload = _json_ready(asdict(report))
    elif isinstance(report, Mapping):
        payload = _copy_public_json_mapping(report)
    else:
        raise ValueError(
            "report must be a ResearchTeamDomainSourceAuthorityMemoryReport",
        )
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    _validate_public_payload(payload, validation_config=validation_config)
    return payload


def research_team_domain_source_authority_memory_report_digest(
    report: ResearchTeamDomainSourceAuthorityMemoryReport | Mapping[str, object],
    *,
    validation_config: ResearchTeamDomainSourceAuthorityMemoryConfig | None = None,
) -> str:
    payload = research_team_domain_source_authority_memory_report_payload(
        report,
        validation_config=validation_config,
    )
    digest = payload["derived_validation_digest"]
    if type(digest) is not str:
        raise ValueError("derived_validation_digest must be a string")
    return digest


def validate_research_team_domain_source_authority_memory_report_digest(
    report: ResearchTeamDomainSourceAuthorityMemoryReport | Mapping[str, object],
    *,
    validation_config: ResearchTeamDomainSourceAuthorityMemoryConfig | None = None,
) -> bool:
    payload = research_team_domain_source_authority_memory_report_payload(
        report,
        validation_config=validation_config,
    )
    return payload["derived_validation_digest"] == _digest_from_payload(payload)


def _row_from_input(
    item: ResearchTeamDomainSourceAuthorityMemoryInput,
    config: ResearchTeamDomainSourceAuthorityMemoryConfig,
) -> ResearchTeamDomainSourceAuthorityMemoryRow:
    memory_coverage_ratio = _ratio(
        item.verified_authority_memory_count,
        item.authority_memory_count,
    )
    memory_staleness_ratio = _bounded_ratio(
        item.memory_age_seconds,
        config.max_watch_memory_age_seconds,
    )
    pressure_components = (
        _inverse_threshold_pressure(
            memory_coverage_ratio,
            pass_value=config.min_pass_memory_coverage_ratio,
            watch_value=config.min_watch_memory_coverage_ratio,
        ),
        _inverse_threshold_pressure(
            item.authority_score,
            pass_value=config.min_pass_authority_score,
            watch_value=config.min_watch_authority_score,
        ),
        _threshold_pressure(
            item.memory_age_seconds,
            pass_value=config.max_pass_memory_age_seconds,
            watch_value=config.max_watch_memory_age_seconds,
        ),
        _threshold_pressure(
            item.contradiction_ratio,
            pass_value=config.max_pass_contradiction_ratio,
            watch_value=config.max_watch_contradiction_ratio,
        ),
    )
    status = _status_for(
        memory_coverage_ratio=memory_coverage_ratio,
        authority_score=item.authority_score,
        memory_age_seconds=item.memory_age_seconds,
        contradiction_ratio=item.contradiction_ratio,
        config=config,
    )
    return ResearchTeamDomainSourceAuthorityMemoryRow(
        authority_rank=ZERO,
        domain_label=item.domain_label,
        team_label=item.team_label,
        authority_family_label=item.authority_family_label,
        status=status,
        authority_pressure_score=_max_decimal(pressure_components),
        authority_memory_count=item.authority_memory_count,
        verified_authority_memory_count=item.verified_authority_memory_count,
        memory_coverage_ratio=memory_coverage_ratio,
        authority_score=item.authority_score,
        memory_age_seconds=item.memory_age_seconds,
        memory_staleness_ratio=memory_staleness_ratio,
        contradiction_ratio=item.contradiction_ratio,
        observed_at=item.observed_at,
        reason_codes=_reason_codes_for(
            memory_coverage_ratio=memory_coverage_ratio,
            authority_score=item.authority_score,
            memory_age_seconds=item.memory_age_seconds,
            contradiction_ratio=item.contradiction_ratio,
            status=status,
            config=config,
        ),
    )


def _with_rank(
    row: ResearchTeamDomainSourceAuthorityMemoryRow,
    rank: int,
) -> ResearchTeamDomainSourceAuthorityMemoryRow:
    return ResearchTeamDomainSourceAuthorityMemoryRow(
        authority_rank=_count(rank),
        domain_label=row.domain_label,
        team_label=row.team_label,
        authority_family_label=row.authority_family_label,
        status=row.status,
        authority_pressure_score=row.authority_pressure_score,
        authority_memory_count=row.authority_memory_count,
        verified_authority_memory_count=row.verified_authority_memory_count,
        memory_coverage_ratio=row.memory_coverage_ratio,
        authority_score=row.authority_score,
        memory_age_seconds=row.memory_age_seconds,
        memory_staleness_ratio=row.memory_staleness_ratio,
        contradiction_ratio=row.contradiction_ratio,
        observed_at=row.observed_at,
        reason_codes=row.reason_codes,
    )


def _status_for(
    *,
    memory_coverage_ratio: Decimal,
    authority_score: Decimal,
    memory_age_seconds: Decimal,
    contradiction_ratio: Decimal,
    config: ResearchTeamDomainSourceAuthorityMemoryConfig,
) -> str:
    if (
        memory_coverage_ratio < config.min_watch_memory_coverage_ratio
        or authority_score < config.min_watch_authority_score
        or memory_age_seconds > config.max_watch_memory_age_seconds
        or contradiction_ratio > config.max_watch_contradiction_ratio
    ):
        return "block"
    if (
        memory_coverage_ratio < config.min_pass_memory_coverage_ratio
        or authority_score < config.min_pass_authority_score
        or memory_age_seconds > config.max_pass_memory_age_seconds
        or contradiction_ratio > config.max_pass_contradiction_ratio
    ):
        return "watch"
    return "pass"


def _reason_codes_for(
    *,
    memory_coverage_ratio: Decimal,
    authority_score: Decimal,
    memory_age_seconds: Decimal,
    contradiction_ratio: Decimal,
    status: str,
    config: ResearchTeamDomainSourceAuthorityMemoryConfig,
) -> tuple[str, ...]:
    codes: list[str] = []
    if memory_coverage_ratio < config.min_watch_memory_coverage_ratio:
        codes.append("source_authority_memory_coverage_block")
    elif memory_coverage_ratio < config.min_pass_memory_coverage_ratio:
        codes.append("source_authority_memory_coverage_watch")
    if authority_score < config.min_watch_authority_score:
        codes.append("source_authority_score_block")
    elif authority_score < config.min_pass_authority_score:
        codes.append("source_authority_score_watch")
    if memory_age_seconds > config.max_watch_memory_age_seconds:
        codes.append("source_authority_memory_staleness_block")
    elif memory_age_seconds > config.max_pass_memory_age_seconds:
        codes.append("source_authority_memory_staleness_watch")
    if contradiction_ratio > config.max_watch_contradiction_ratio:
        codes.append("source_authority_contradiction_block")
    elif contradiction_ratio > config.max_pass_contradiction_ratio:
        codes.append("source_authority_contradiction_watch")
    if not codes and status == "pass":
        codes.append("source_authority_memory_pass")
    return _require_reason_codes(tuple(codes), require_nonempty=True)


def _row_sort_key(
    row: ResearchTeamDomainSourceAuthorityMemoryRow,
) -> tuple[int, Decimal, Decimal, str, str, str]:
    return (
        STATUS_SORT_RANK[row.status],
        row.authority_pressure_score.copy_negate(),
        row.memory_coverage_ratio,
        row.domain_label,
        row.team_label,
        row.authority_family_label,
    )


def _normalize_inputs(
    inputs: Iterable[ResearchTeamDomainSourceAuthorityMemoryInput],
) -> tuple[ResearchTeamDomainSourceAuthorityMemoryInput, ...]:
    if isinstance(inputs, (str, bytes)):
        raise ValueError("inputs must be an iterable")
    try:
        normalized = tuple(inputs)
    except TypeError as exc:
        raise ValueError("inputs must be an iterable") from exc
    seen_keys: set[tuple[str, str, str]] = set()
    normalized_items: list[ResearchTeamDomainSourceAuthorityMemoryInput] = []
    for item in normalized:
        _require_exact_type(item, ResearchTeamDomainSourceAuthorityMemoryInput, "input")
        item = ResearchTeamDomainSourceAuthorityMemoryInput(
            domain_label=item.domain_label,
            team_label=item.team_label,
            authority_family_label=item.authority_family_label,
            authority_memory_count=item.authority_memory_count,
            verified_authority_memory_count=item.verified_authority_memory_count,
            authority_score=item.authority_score,
            memory_age_seconds=item.memory_age_seconds,
            contradiction_ratio=item.contradiction_ratio,
            observed_at=item.observed_at,
            paper_only=item.paper_only,
            report_only=item.report_only,
            readonly=item.readonly,
        )
        key = (item.domain_label, item.team_label, item.authority_family_label)
        if key in seen_keys:
            raise ValueError("team-domain-authority labels must be unique")
        seen_keys.add(key)
        normalized_items.append(item)
    return tuple(normalized_items)


def _normalize_config(
    config: ResearchTeamDomainSourceAuthorityMemoryConfig,
) -> ResearchTeamDomainSourceAuthorityMemoryConfig:
    _require_exact_type(config, ResearchTeamDomainSourceAuthorityMemoryConfig, "config")
    return ResearchTeamDomainSourceAuthorityMemoryConfig(
        config_version=config.config_version,
        min_pass_memory_coverage_ratio=config.min_pass_memory_coverage_ratio,
        min_watch_memory_coverage_ratio=config.min_watch_memory_coverage_ratio,
        min_pass_authority_score=config.min_pass_authority_score,
        min_watch_authority_score=config.min_watch_authority_score,
        max_pass_memory_age_seconds=config.max_pass_memory_age_seconds,
        max_watch_memory_age_seconds=config.max_watch_memory_age_seconds,
        max_pass_contradiction_ratio=config.max_pass_contradiction_ratio,
        max_watch_contradiction_ratio=config.max_watch_contradiction_ratio,
        paper_only=config.paper_only,
        report_only=config.report_only,
        readonly=config.readonly,
    )


def _report_status(rows: tuple[ResearchTeamDomainSourceAuthorityMemoryRow, ...]) -> str:
    statuses = tuple(row.status for row in rows)
    if "block" in statuses:
        return "block"
    if "watch" in statuses:
        return "watch"
    return "pass"


def _report_reason_codes(
    rows: tuple[ResearchTeamDomainSourceAuthorityMemoryRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return (EMPTY_REASON,)
    seen = {code for row in rows for code in row.reason_codes}
    return tuple(code for code in REASON_SEQUENCE if code in seen)


def _reason_code_counts(
    rows: tuple[ResearchTeamDomainSourceAuthorityMemoryRow, ...],
) -> tuple[ResearchTeamDomainSourceAuthorityMemoryReasonCodeCount, ...]:
    if not rows:
        return ()
    counter: Counter[str] = Counter()
    for row in rows:
        counter.update(row.reason_codes)
    row_count = _count(len(rows))
    return tuple(
        ResearchTeamDomainSourceAuthorityMemoryReasonCodeCount(
            reason_code=code,
            count=_count(counter[code]),
            row_ratio=_ratio(_count(counter[code]), row_count),
        )
        for code in REASON_SEQUENCE
        if counter[code]
    )


def _status_count(
    rows: tuple[ResearchTeamDomainSourceAuthorityMemoryRow, ...],
    status: str,
) -> Decimal:
    return _count(sum(1 for row in rows if row.status == status))


def _require_exact_type(value: object, expected_type: type, label: str) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{label} must be a {expected_type.__name__}")


def _require_public_string(name: str, value: object) -> None:
    if type(value) is not str or not value:
        raise ValueError(f"{name} must be a non-empty string")


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
    return _quantize(name, _require_raw_decimal(name, value))


def _require_raw_decimal(name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{name} must be finite")
    if value.is_zero() and value.is_signed():
        raise ValueError(f"{name} must not use signed zero")
    return value


def _quantize(name: str, value: Decimal) -> Decimal:
    with localcontext(_fixed_decimal_context()):
        try:
            return value.quantize(QUANTUM)
        except InvalidOperation as exc:
            raise ValueError(f"{name} must be quantizable") from exc


def _require_nonnegative_decimal(name: str, value: object) -> Decimal:
    decimal_value = _require_raw_decimal(name, value)
    if decimal_value < ZERO:
        raise ValueError(f"{name} must be nonnegative")
    return _quantize(name, decimal_value)


def _require_count_decimal(name: str, value: object) -> Decimal:
    decimal_value = _require_raw_decimal(name, value)
    if decimal_value < ZERO:
        raise ValueError(f"{name} must be nonnegative")
    with localcontext(_fixed_decimal_context()):
        is_whole = decimal_value == decimal_value.to_integral_value()
    if not is_whole:
        raise ValueError(f"{name} must be a whole count")
    return _quantize(name, decimal_value)


def _require_ratio_decimal(name: str, value: object) -> Decimal:
    decimal_value = _require_raw_decimal(name, value)
    if decimal_value < ZERO or decimal_value > ONE:
        raise ValueError(f"{name} must be between 0 and 1")
    return _quantize(name, decimal_value)


def _count(value: int) -> Decimal:
    return _require_count_decimal("count", Decimal(value))


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    numerator = _require_nonnegative_decimal("numerator", numerator)
    denominator = _require_nonnegative_decimal("denominator", denominator)
    if denominator == ZERO:
        return ZERO
    with localcontext(_fixed_decimal_context()):
        return _require_ratio_decimal("ratio", numerator / denominator)


def _bounded_ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    numerator = _require_nonnegative_decimal("numerator", numerator)
    denominator = _require_nonnegative_decimal("denominator", denominator)
    if denominator == ZERO:
        return ZERO
    with localcontext(_fixed_decimal_context()):
        value = _require_decimal("bounded_ratio", numerator / denominator)
    if value > ONE:
        return ONE
    if value < ZERO:
        raise ValueError("bounded_ratio must be nonnegative")
    return value


def _subtract_decimal(left: Decimal, right: Decimal) -> Decimal:
    with localcontext(_fixed_decimal_context()):
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
    with localcontext(_fixed_decimal_context()):
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
    with localcontext(_fixed_decimal_context()):
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
    if value not in RESEARCH_TEAM_DOMAIN_SOURCE_AUTHORITY_MEMORY_STATUSES:
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
) -> tuple[ResearchTeamDomainSourceAuthorityMemoryReasonCodeCount, ...]:
    if not isinstance(values, (list, tuple)):
        raise ValueError("reason_code_counts must be a list or tuple")
    normalized = tuple(values)
    seen: set[str] = set()
    for item in normalized:
        _require_exact_type(
            item,
            ResearchTeamDomainSourceAuthorityMemoryReasonCodeCount,
            "reason_code_count",
        )
        if item.reason_code in seen:
            raise ValueError("reason_code_counts must be unique")
        seen.add(item.reason_code)
    return tuple(sorted(normalized, key=lambda item: REASON_SEQUENCE.index(item.reason_code)))


def _require_rows(
    rows: object,
) -> tuple[ResearchTeamDomainSourceAuthorityMemoryRow, ...]:
    if not isinstance(rows, (list, tuple)):
        raise ValueError("rows must be a list or tuple")
    normalized = tuple(rows)
    seen_keys: set[tuple[str, str, str]] = set()
    validated_rows: list[ResearchTeamDomainSourceAuthorityMemoryRow] = []
    for row in normalized:
        _require_exact_type(row, ResearchTeamDomainSourceAuthorityMemoryRow, "row")
        row = replace(row)
        key = (row.domain_label, row.team_label, row.authority_family_label)
        if key in seen_keys:
            raise ValueError("team-domain-authority labels must be unique")
        seen_keys.add(key)
        validated_rows.append(row)
    return tuple(sorted(validated_rows, key=_row_sort_key))


def _require_hard_flags(name: str, value: object) -> None:
    if getattr(value, "paper_only", None) is not True:
        raise ValueError(f"{name} paper_only must be True")
    if getattr(value, "report_only", None) is not True:
        raise ValueError(f"{name} report_only must be True")
    if getattr(value, "readonly", None) is not True:
        raise ValueError(f"{name} readonly must be True")


def _validate_row(row: ResearchTeamDomainSourceAuthorityMemoryRow) -> None:
    expected_coverage = _ratio(
        row.verified_authority_memory_count,
        row.authority_memory_count,
    )
    if row.memory_coverage_ratio != expected_coverage:
        raise ValueError("memory_coverage_ratio must match verified over total memory")
    if row.status == "pass" and row.authority_pressure_score != ZERO:
        raise ValueError("authority_pressure_score must be zero for pass rows")
    if row.status == "block" and row.authority_pressure_score != ONE:
        raise ValueError("authority_pressure_score must be one for block rows")
    pass_reasons = ("source_authority_memory_pass",)
    if row.reason_codes == pass_reasons:
        reason_status = "pass"
    elif pass_reasons[0] in row.reason_codes:
        raise ValueError("status must match reason code severity")
    elif any(code in REASON_SEQUENCE[:4] for code in row.reason_codes):
        reason_status = "block"
    else:
        reason_status = "watch"
    if row.status != reason_status:
        raise ValueError("status must match reason code severity")


def _validate_row_derived_values(
    row: ResearchTeamDomainSourceAuthorityMemoryRow,
    *,
    config: ResearchTeamDomainSourceAuthorityMemoryConfig,
) -> None:
    _validate_row(row)
    expected_staleness = _bounded_ratio(
        row.memory_age_seconds,
        config.max_watch_memory_age_seconds,
    )
    if row.memory_staleness_ratio != expected_staleness:
        raise ValueError("memory_staleness_ratio must match memory_age_seconds")
    expected_pressure = _max_decimal(
        (
            _inverse_threshold_pressure(
                row.memory_coverage_ratio,
                pass_value=config.min_pass_memory_coverage_ratio,
                watch_value=config.min_watch_memory_coverage_ratio,
            ),
            _inverse_threshold_pressure(
                row.authority_score,
                pass_value=config.min_pass_authority_score,
                watch_value=config.min_watch_authority_score,
            ),
            _threshold_pressure(
                row.memory_age_seconds,
                pass_value=config.max_pass_memory_age_seconds,
                watch_value=config.max_watch_memory_age_seconds,
            ),
            _threshold_pressure(
                row.contradiction_ratio,
                pass_value=config.max_pass_contradiction_ratio,
                watch_value=config.max_watch_contradiction_ratio,
            ),
        ),
    )
    if row.authority_pressure_score != expected_pressure:
        raise ValueError("authority_pressure_score must match row metrics")
    expected_status = _status_for(
        memory_coverage_ratio=row.memory_coverage_ratio,
        authority_score=row.authority_score,
        memory_age_seconds=row.memory_age_seconds,
        contradiction_ratio=row.contradiction_ratio,
        config=config,
    )
    if row.status != expected_status:
        raise ValueError("status must match row metrics")
    expected_reasons = _reason_codes_for(
        memory_coverage_ratio=row.memory_coverage_ratio,
        authority_score=row.authority_score,
        memory_age_seconds=row.memory_age_seconds,
        contradiction_ratio=row.contradiction_ratio,
        status=expected_status,
        config=config,
    )
    if row.reason_codes != expected_reasons:
        raise ValueError("reason_codes must match row metrics")


def _validate_report(report: ResearchTeamDomainSourceAuthorityMemoryReport) -> None:
    rows = report.rows
    for expected_rank, row in enumerate(rows, start=1):
        _require_hard_flags("row", row)
        _verify_digest(row)
        _validate_row(row)
        if row.authority_rank != _count(expected_rank):
            raise ValueError("authority_rank must match canonical row order")
        if row.observed_at > report.generated_at:
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
    if report.min_authority_score != _min_decimal(tuple(row.authority_score for row in rows)):
        raise ValueError("min_authority_score must match rows")
    if report.max_memory_age_seconds != _max_decimal(
        tuple(row.memory_age_seconds for row in rows),
    ):
        raise ValueError("max_memory_age_seconds must match rows")
    if report.max_contradiction_ratio != _max_decimal(
        tuple(row.contradiction_ratio for row in rows),
    ):
        raise ValueError("max_contradiction_ratio must match rows")
    if report.max_authority_pressure_score != _max_decimal(
        tuple(row.authority_pressure_score for row in rows),
    ):
        raise ValueError("max_authority_pressure_score must match rows")
    if report.status != _report_status(rows):
        raise ValueError("status must match rows")
    if report.reason_codes != _report_reason_codes(rows):
        raise ValueError("reason_codes must match rows")
    if report.reason_code_counts != _reason_code_counts(rows):
        raise ValueError("reason_code_counts must match rows")


def _apply_or_verify_digest(value: object) -> None:
    payload = _json_ready(asdict(value))
    if type(payload) is not dict:
        raise ValueError("payload must be a JSON object")
    expected = _digest_from_payload(payload)
    current = payload.get("derived_validation_digest")
    if current == "":
        object.__setattr__(value, "derived_validation_digest", expected)
        return
    if type(current) is not str:
        raise ValueError("derived_validation_digest must be a string")
    if current != expected:
        raise ValueError("derived_validation_digest does not match payload")


def _verify_digest(value: object) -> None:
    payload = _json_ready(asdict(value))
    if type(payload) is not dict:
        raise ValueError("payload must be a JSON object")
    if payload.get("derived_validation_digest") != _digest_from_payload(payload):
        raise ValueError("derived_validation_digest does not match payload")


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
        return str(value)
    if isinstance(value, datetime):
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("JSON datetime value must be UTC-aware")
        return value.astimezone(UTC).isoformat()
    if type(value) is float or type(value) is int:
        raise ValueError("JSON numeric values must use Decimal-derived strings")
    if type(value) is str or type(value) is bool:
        return value
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


def _copy_public_json_mapping(value: Mapping[str, object]) -> dict[str, object]:
    ready: dict[str, object] = {}
    for key, item in value.items():
        if type(key) is not str:
            raise ValueError("public payload object keys must be strings")
        ready[key] = _copy_public_json_value(item)
    return ready


def _copy_public_json_value(value: object) -> object:
    if value is None or type(value) is str or type(value) is bool:
        return value
    if type(value) is dict:
        return _copy_public_json_mapping(value)
    if type(value) is list:
        return [_copy_public_json_value(item) for item in value]
    if type(value) in (int, float) or isinstance(value, Decimal):
        raise ValueError(
            "public payload numeric values must use Decimal-derived strings",
        )
    if isinstance(value, datetime):
        raise ValueError("public payload datetime values must use ISO strings")
    if isinstance(value, Mapping):
        raise ValueError("nested public payload objects must use exact dictionaries")
    if isinstance(value, (list, tuple)):
        raise ValueError("public payload sequences must use exact lists")
    raise ValueError("public payload contains a non-JSON value")


def _validate_public_payload(
    payload: dict[str, object],
    *,
    validation_config: ResearchTeamDomainSourceAuthorityMemoryConfig | None,
) -> None:
    config = _public_validation_config(validation_config)
    report = _report_from_public_payload(payload, validation_config=config)
    canonical_payload = _json_ready(asdict(report))
    if canonical_payload != payload:
        raise ValueError("public payload schema values must be canonical")


def _public_validation_config(
    value: ResearchTeamDomainSourceAuthorityMemoryConfig | None,
) -> ResearchTeamDomainSourceAuthorityMemoryConfig:
    if value is None:
        return ResearchTeamDomainSourceAuthorityMemoryConfig()
    return _normalize_config(value)


def _report_from_public_payload(
    payload: dict[str, object],
    *,
    validation_config: ResearchTeamDomainSourceAuthorityMemoryConfig,
) -> ResearchTeamDomainSourceAuthorityMemoryReport:
    _require_payload_keys(payload, REPORT_PAYLOAD_KEYS)
    rows = tuple(
        _row_from_public_payload(row, validation_config=validation_config)
        for row in _require_payload_list("rows", payload["rows"])
    )
    reason_code_counts = tuple(
        _reason_count_from_public_payload(item)
        for item in _require_payload_list(
            "reason_code_counts",
            payload["reason_code_counts"],
        )
    )
    return ResearchTeamDomainSourceAuthorityMemoryReport(
        generated_at=_public_generated_at("generated_at", payload["generated_at"]),
        config_version=_public_config_version(payload["config_version"]),
        input_count=_public_count_decimal("input_count", payload["input_count"]),
        row_count=_public_count_decimal("row_count", payload["row_count"]),
        pass_count=_public_count_decimal("pass_count", payload["pass_count"]),
        watch_count=_public_count_decimal("watch_count", payload["watch_count"]),
        block_count=_public_count_decimal("block_count", payload["block_count"]),
        watch_block_ratio=_public_ratio_decimal(
            "watch_block_ratio",
            payload["watch_block_ratio"],
        ),
        min_memory_coverage_ratio=_public_ratio_decimal(
            "min_memory_coverage_ratio",
            payload["min_memory_coverage_ratio"],
        ),
        min_authority_score=_public_ratio_decimal(
            "min_authority_score",
            payload["min_authority_score"],
        ),
        max_memory_age_seconds=_public_nonnegative_decimal(
            "max_memory_age_seconds",
            payload["max_memory_age_seconds"],
        ),
        max_contradiction_ratio=_public_ratio_decimal(
            "max_contradiction_ratio",
            payload["max_contradiction_ratio"],
        ),
        max_authority_pressure_score=_public_ratio_decimal(
            "max_authority_pressure_score",
            payload["max_authority_pressure_score"],
        ),
        status=payload["status"],
        report_mode=payload["report_mode"],
        reason_codes=_require_public_reason_code_list(
            "reason_codes",
            payload["reason_codes"],
            allow_empty=False,
        ),
        reason_code_counts=reason_code_counts,
        rows=rows,
        derived_validation_digest=_public_digest(payload["derived_validation_digest"]),
        paper_only=payload["paper_only"],
        report_only=payload["report_only"],
        readonly=payload["readonly"],
    )


def _row_from_public_payload(
    row: object,
    *,
    validation_config: ResearchTeamDomainSourceAuthorityMemoryConfig,
) -> ResearchTeamDomainSourceAuthorityMemoryRow:
    if type(row) is not dict:
        raise ValueError("rows must contain JSON objects")
    _require_payload_keys(row, ROW_PAYLOAD_KEYS)
    normalized = ResearchTeamDomainSourceAuthorityMemoryRow(
        authority_rank=_public_count_decimal("authority_rank", row["authority_rank"]),
        domain_label=row["domain_label"],
        team_label=row["team_label"],
        authority_family_label=row["authority_family_label"],
        status=row["status"],
        authority_pressure_score=_public_ratio_decimal(
            "authority_pressure_score",
            row["authority_pressure_score"],
        ),
        authority_memory_count=_public_count_decimal(
            "authority_memory_count",
            row["authority_memory_count"],
        ),
        verified_authority_memory_count=_public_count_decimal(
            "verified_authority_memory_count",
            row["verified_authority_memory_count"],
        ),
        memory_coverage_ratio=_public_ratio_decimal(
            "memory_coverage_ratio",
            row["memory_coverage_ratio"],
        ),
        authority_score=_public_ratio_decimal("authority_score", row["authority_score"]),
        memory_age_seconds=_public_nonnegative_decimal(
            "memory_age_seconds",
            row["memory_age_seconds"],
        ),
        memory_staleness_ratio=_public_ratio_decimal(
            "memory_staleness_ratio",
            row["memory_staleness_ratio"],
        ),
        contradiction_ratio=_public_ratio_decimal(
            "contradiction_ratio",
            row["contradiction_ratio"],
        ),
        observed_at=_public_observed_at("observed_at", row["observed_at"]),
        reason_codes=_require_public_reason_code_list(
            "reason_codes",
            row["reason_codes"],
            allow_empty=False,
        ),
        derived_validation_digest=_public_digest(row["derived_validation_digest"]),
        paper_only=row["paper_only"],
        report_only=row["report_only"],
        readonly=row["readonly"],
    )
    _validate_row_derived_values(normalized, config=validation_config)
    return normalized


def _reason_count_from_public_payload(
    value: object,
) -> ResearchTeamDomainSourceAuthorityMemoryReasonCodeCount:
    if type(value) is not dict:
        raise ValueError("reason_code_counts must contain JSON objects")
    _require_payload_keys(value, REASON_COUNT_PAYLOAD_KEYS)
    return ResearchTeamDomainSourceAuthorityMemoryReasonCodeCount(
        reason_code=value["reason_code"],
        count=_public_count_decimal("count", value["count"]),
        row_ratio=_public_ratio_decimal("row_ratio", value["row_ratio"]),
        paper_only=value["paper_only"],
        report_only=value["report_only"],
        readonly=value["readonly"],
    )


def _require_payload_keys(
    payload: Mapping[str, object],
    allowed_keys: tuple[str, ...],
) -> None:
    keys = tuple(payload)
    if set(keys) != set(allowed_keys):
        raise ValueError("public aggregate labels contain unsafe fields")
    for key in keys:
        if _has_unsafe_public_fragment(key):
            raise ValueError("public aggregate labels contain unsafe fields")
    if keys != allowed_keys:
        raise ValueError("public payload schema must use canonical field order")


def _require_payload_list(name: str, value: object) -> list[object]:
    if type(value) is not list:
        raise ValueError(f"{name} must be a list")
    return value


def _public_config_version(value: object) -> str:
    _require_public_string("config_version", value)
    assert type(value) is str
    if value != DEFAULT_RESEARCH_TEAM_DOMAIN_SOURCE_AUTHORITY_MEMORY_CONFIG_VERSION:
        raise ValueError("config_version must be the supported config version")
    return value


def _public_decimal_value(name: str, value: object) -> Decimal:
    if type(value) is not str:
        raise ValueError(f"{name} numeric values must use Decimal-derived strings")
    try:
        return Decimal(value)
    except Exception as exc:
        raise ValueError(f"{name} numeric values must use Decimal-derived strings") from exc


def _public_count_decimal(name: str, value: object) -> Decimal:
    return _require_count_decimal(name, _public_decimal_value(name, value))


def _public_nonnegative_decimal(name: str, value: object) -> Decimal:
    return _require_nonnegative_decimal(name, _public_decimal_value(name, value))


def _public_ratio_decimal(name: str, value: object) -> Decimal:
    return _require_ratio_decimal(name, _public_decimal_value(name, value))


def _public_generated_at(name: str, value: object) -> datetime:
    return _as_generated_at_utc(name, _public_datetime_value(name, value))


def _public_observed_at(name: str, value: object) -> datetime:
    return _as_utc(name, _public_datetime_value(name, value))


def _public_datetime_value(name: str, value: object) -> datetime:
    if type(value) is not str:
        raise ValueError(f"{name} must be an ISO datetime string")
    try:
        return datetime.fromisoformat(value)
    except ValueError as exc:
        raise ValueError(f"{name} must be an ISO datetime string") from exc


def _public_digest(value: object) -> str:
    _require_public_digest(value)
    assert type(value) is str
    return value


def _require_public_digest(value: object) -> None:
    if type(value) is not str:
        raise ValueError("derived_validation_digest must be a string")
    if len(value) != 64 or any(char not in HEX_CHARS for char in value):
        raise ValueError("derived_validation_digest must be a sha256 hex digest")


def _require_public_reason_code_list(
    name: str,
    value: object,
    *,
    allow_empty: bool,
) -> tuple[str, ...]:
    if type(value) is not list:
        raise ValueError(f"{name} must be a list")
    if not allow_empty and not value:
        raise ValueError(f"{name} must be non-empty")
    normalized = tuple(value)
    if normalized == (EMPTY_REASON,):
        return normalized
    seen: set[str] = set()
    for code in normalized:
        _require_public_string("reason_code", code)
        if code not in REASON_SEQUENCE:
            raise ValueError("reason_code must be known")
        if code in seen:
            raise ValueError("reason_codes must be unique")
        seen.add(code)
    return tuple(code for code in REASON_SEQUENCE if code in seen)
