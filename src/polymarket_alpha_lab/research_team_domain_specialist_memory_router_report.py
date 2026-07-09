"""Pure report-only team-domain specialist memory router."""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable, Mapping
from dataclasses import asdict, dataclass, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
import json
from typing import Any

from polymarket_alpha_lab.team_paper_guard import require_paper_only_flags


DEFAULT_RESEARCH_TEAM_DOMAIN_SPECIALIST_MEMORY_ROUTER_CONFIG_VERSION = (
    "research-team-domain-specialist-memory-router-report-v0"
)

STATUS_PASS = "pass"
STATUS_WATCH = "watch"
STATUS_BLOCK = "block"
TEAM_DOMAIN_SPECIALIST_MEMORY_ROUTER_STATUSES = (
    STATUS_PASS,
    STATUS_WATCH,
    STATUS_BLOCK,
)

ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
QUANTUM = Decimal("0.000001")
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
HEX_CHARS = frozenset("0123456789abcdef")
SECONDS_PER_DAY = Decimal("86400.000000")

SPECIALIST_MEMORY_BLOCK_REASON = (
    "team_domain_specialist_memory_router_specialist_memory_block"
)
DOMAIN_FIT_BLOCK_REASON = "team_domain_specialist_memory_router_domain_fit_block"
MEMORY_AGE_BLOCK_REASON = "team_domain_specialist_memory_router_memory_age_block"
CONFLICT_BLOCK_REASON = "team_domain_specialist_memory_router_conflict_block"
REVIEW_PRESSURE_BLOCK_REASON = (
    "team_domain_specialist_memory_router_review_pressure_block"
)
SPECIALIST_MEMORY_WATCH_REASON = (
    "team_domain_specialist_memory_router_specialist_memory_watch"
)
DOMAIN_FIT_WATCH_REASON = "team_domain_specialist_memory_router_domain_fit_watch"
MEMORY_AGE_WATCH_REASON = "team_domain_specialist_memory_router_memory_age_watch"
CONFLICT_WATCH_REASON = "team_domain_specialist_memory_router_conflict_watch"
REVIEW_PRESSURE_WATCH_REASON = (
    "team_domain_specialist_memory_router_review_pressure_watch"
)
CLEAR_REASON = "team_domain_specialist_memory_router_clear"
EMPTY_REASON = "team_domain_specialist_memory_router_empty"

ROW_REASON_SEQUENCE = (
    SPECIALIST_MEMORY_BLOCK_REASON,
    DOMAIN_FIT_BLOCK_REASON,
    MEMORY_AGE_BLOCK_REASON,
    CONFLICT_BLOCK_REASON,
    REVIEW_PRESSURE_BLOCK_REASON,
    SPECIALIST_MEMORY_WATCH_REASON,
    DOMAIN_FIT_WATCH_REASON,
    MEMORY_AGE_WATCH_REASON,
    CONFLICT_WATCH_REASON,
    REVIEW_PRESSURE_WATCH_REASON,
    CLEAR_REASON,
)
REPORT_REASON_SEQUENCE = (EMPTY_REASON,) + ROW_REASON_SEQUENCE

PAPER_ACTION_BY_STATUS = {
    STATUS_PASS: "paper_memory_route_pass",
    STATUS_WATCH: "paper_memory_route_watch",
    STATUS_BLOCK: "paper_memory_route_block",
}

MEMORY_GAP_WEIGHT = Decimal("0.150000")
DOMAIN_GAP_WEIGHT = Decimal("0.150000")
AGE_PRESSURE_WEIGHT = Decimal("0.300000")
CONFLICT_WEIGHT = Decimal("0.150000")
REVIEW_PRESSURE_WEIGHT = Decimal("0.250000")


def _join(*parts: str) -> str:
    return "".join(parts)


PUBLIC_LABEL_CHARS = frozenset("abcdefghijklmnopqrstuvwxyz0123456789_.-")
UNSAFE_PUBLIC_PARTS = frozenset(
    (
        _join("ra", "w"),
        _join("can", "didate"),
        _join("mar", "ket"),
        _join("s", "lug"),
        _join("ques", "tion"),
        _join("source", "_", "u", "r", "l"),
        _join("source", "_", "text"),
        _join("h", "t", "t", "p", "://"),
        _join("h", "t", "t", "p", "s", "://"),
        _join("d", "s", "n"),
        _join("ta", "ble"),
        _join("to", "ken"),
        _join("wal", "let"),
        _join("or", "der"),
        _join("tra", "de"),
        _join("li", "ve"),
        _join("siz", "ing"),
        _join("reco", "mmendation"),
        _join("sec", "ret"),
        _join("cred", "ential"),
        _join("priv", "ate"),
        _join("data", "base"),
        _join("net", "work"),
        _join("au", "th"),
        _join("b", "uy"),
        _join("s", "ell"),
    ),
)

__all__ = (
    "DEFAULT_RESEARCH_TEAM_DOMAIN_SPECIALIST_MEMORY_ROUTER_CONFIG_VERSION",
    "TEAM_DOMAIN_SPECIALIST_MEMORY_ROUTER_STATUSES",
    "ResearchTeamDomainSpecialistMemoryRouterConfig",
    "ResearchTeamDomainSpecialistMemoryRouterInput",
    "ResearchTeamDomainSpecialistMemoryRouterReasonCodeCount",
    "ResearchTeamDomainSpecialistMemoryRouterReport",
    "ResearchTeamDomainSpecialistMemoryRouterRow",
    "build_research_team_domain_specialist_memory_router_report",
    "research_team_domain_specialist_memory_router_report_digest",
    "research_team_domain_specialist_memory_router_report_payload",
)


class _FinalData:
    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        for base in cls.__bases__:
            if base is not _FinalData and issubclass(base, _FinalData):
                raise TypeError(f"{base.__name__} subclass is not allowed")


@dataclass(frozen=True)
class ResearchTeamDomainSpecialistMemoryRouterConfig(_FinalData):
    config_version: str = (
        DEFAULT_RESEARCH_TEAM_DOMAIN_SPECIALIST_MEMORY_ROUTER_CONFIG_VERSION
    )
    min_pass_specialist_memory_score: Decimal = Decimal("0.750000")
    min_watch_specialist_memory_score: Decimal = Decimal("0.500000")
    min_pass_domain_fit_score: Decimal = Decimal("0.750000")
    min_watch_domain_fit_score: Decimal = Decimal("0.500000")
    max_pass_memory_age_seconds: Decimal = Decimal("7776000.000000")
    max_watch_memory_age_seconds: Decimal = Decimal("15552000.000000")
    max_pass_conflict_score: Decimal = Decimal("0.250000")
    max_watch_conflict_score: Decimal = Decimal("0.500000")
    max_pass_review_pressure_score: Decimal = Decimal("0.500000")
    max_watch_review_pressure_score: Decimal = Decimal("0.850000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchTeamDomainSpecialistMemoryRouterConfig,
            "config",
        )
        object.__setattr__(
            self,
            "config_version",
            _require_public_label("config_version", self.config_version),
        )
        if (
            self.config_version
            != DEFAULT_RESEARCH_TEAM_DOMAIN_SPECIALIST_MEMORY_ROUTER_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "min_pass_specialist_memory_score",
            "min_watch_specialist_memory_score",
            "min_pass_domain_fit_score",
            "min_watch_domain_fit_score",
            "max_pass_conflict_score",
            "max_watch_conflict_score",
            "max_pass_review_pressure_score",
            "max_watch_review_pressure_score",
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
                _require_positive_decimal(field_name, getattr(self, field_name)),
            )
        if (
            self.min_watch_specialist_memory_score
            > self.min_pass_specialist_memory_score
        ):
            raise ValueError(
                "min_watch_specialist_memory_score must not exceed pass",
            )
        if self.min_watch_domain_fit_score > self.min_pass_domain_fit_score:
            raise ValueError("min_watch_domain_fit_score must not exceed pass")
        if self.max_watch_memory_age_seconds < self.max_pass_memory_age_seconds:
            raise ValueError("max_watch_memory_age_seconds must be at least pass")
        if self.max_pass_conflict_score > self.max_watch_conflict_score:
            raise ValueError("max_pass_conflict_score must not exceed watch")
        if self.max_pass_review_pressure_score > self.max_watch_review_pressure_score:
            raise ValueError("max_pass_review_pressure_score must not exceed watch")
        _require_hard_flags("config", self)
        _reject_unsafe_public_payload("config", self)


@dataclass(frozen=True)
class ResearchTeamDomainSpecialistMemoryRouterInput(_FinalData):
    memory_key: str
    team_label: str
    domain_label: str
    specialist_label: str
    specialist_memory_score: Decimal
    domain_fit_score: Decimal
    conflict_score: Decimal
    review_pressure_score: Decimal
    observed_at: datetime
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchTeamDomainSpecialistMemoryRouterInput,
            "input",
        )
        _require_memory_key("memory_key", self.memory_key)
        for field_name in ("team_label", "domain_label", "specialist_label"):
            object.__setattr__(
                self,
                field_name,
                _require_public_label(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "specialist_memory_score",
            "domain_fit_score",
            "conflict_score",
            "review_pressure_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        _require_hard_flags("input", self)


@dataclass(frozen=True)
class ResearchTeamDomainSpecialistMemoryRouterRow(_FinalData):
    route_rank: Decimal
    memory_ref: str
    team_label: str
    domain_label: str
    specialist_label: str
    observed_at: datetime
    memory_age_seconds: Decimal
    specialist_memory_score: Decimal
    domain_fit_score: Decimal
    memory_gap_score: Decimal
    domain_gap_score: Decimal
    age_pressure_score: Decimal
    conflict_score: Decimal
    review_pressure_score: Decimal
    router_priority_score: Decimal
    status: str
    paper_route_action: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchTeamDomainSpecialistMemoryRouterRow, "row")
        object.__setattr__(
            self,
            "route_rank",
            _require_count_decimal("route_rank", self.route_rank),
        )
        object.__setattr__(
            self,
            "memory_ref",
            _require_memory_ref("memory_ref", self.memory_ref),
        )
        for field_name in ("team_label", "domain_label", "specialist_label"):
            object.__setattr__(
                self,
                field_name,
                _require_public_label(field_name, getattr(self, field_name)),
            )
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        object.__setattr__(
            self,
            "memory_age_seconds",
            _require_nonnegative_decimal("memory_age_seconds", self.memory_age_seconds),
        )
        for field_name in (
            "specialist_memory_score",
            "domain_fit_score",
            "memory_gap_score",
            "domain_gap_score",
            "age_pressure_score",
            "conflict_score",
            "review_pressure_score",
            "router_priority_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(self, "status", _require_status("status", self.status))
        object.__setattr__(
            self,
            "paper_route_action",
            _require_public_label("paper_route_action", self.paper_route_action),
        )
        if self.paper_route_action != PAPER_ACTION_BY_STATUS[self.status]:
            raise ValueError("paper_route_action must match status")
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes, ROW_REASON_SEQUENCE),
        )
        _validate_row(self)
        _require_hard_flags("row", self)
        _reject_unsafe_public_payload("row", self)


@dataclass(frozen=True)
class ResearchTeamDomainSpecialistMemoryRouterReasonCodeCount(_FinalData):
    reason_code: str
    count: Decimal
    memory_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchTeamDomainSpecialistMemoryRouterReasonCodeCount,
            "reason_code_count",
        )
        object.__setattr__(
            self,
            "reason_code",
            _require_reason_code("reason_code", self.reason_code, ROW_REASON_SEQUENCE),
        )
        object.__setattr__(self, "count", _require_count_decimal("count", self.count))
        object.__setattr__(
            self,
            "memory_ratio",
            _require_ratio_decimal("memory_ratio", self.memory_ratio),
        )
        _require_hard_flags("reason_code_count", self)
        _reject_unsafe_public_payload("reason_code_count", self)


@dataclass(frozen=True)
class ResearchTeamDomainSpecialistMemoryRouterReport(_FinalData):
    generated_at: datetime
    config_version: str
    memory_count: Decimal
    routed_memory_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    max_router_priority_score: Decimal
    avg_router_priority_score: Decimal
    min_specialist_memory_score: Decimal
    min_domain_fit_score: Decimal
    max_conflict_score: Decimal
    max_review_pressure_score: Decimal
    status: str
    paper_route_action: str
    reason_codes: tuple[str, ...]
    reason_code_counts: tuple[
        ResearchTeamDomainSpecialistMemoryRouterReasonCodeCount,
        ...,
    ]
    rows: tuple[ResearchTeamDomainSpecialistMemoryRouterRow, ...]
    derived_validation_digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchTeamDomainSpecialistMemoryRouterReport, "report")
        object.__setattr__(
            self,
            "generated_at",
            _as_utc("generated_at", self.generated_at),
        )
        object.__setattr__(
            self,
            "config_version",
            _require_public_label("config_version", self.config_version),
        )
        if (
            self.config_version
            != DEFAULT_RESEARCH_TEAM_DOMAIN_SPECIALIST_MEMORY_ROUTER_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "memory_count",
            "routed_memory_count",
            "pass_count",
            "watch_count",
            "block_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_count_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "max_router_priority_score",
            "avg_router_priority_score",
            "min_specialist_memory_score",
            "min_domain_fit_score",
            "max_conflict_score",
            "max_review_pressure_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(self, "status", _require_status("status", self.status))
        object.__setattr__(
            self,
            "paper_route_action",
            _require_public_label("paper_route_action", self.paper_route_action),
        )
        if self.paper_route_action != PAPER_ACTION_BY_STATUS[self.status]:
            raise ValueError("paper_route_action must match status")
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes, REPORT_REASON_SEQUENCE),
        )
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        _require_sha256_digest(
            "derived_validation_digest",
            self.derived_validation_digest,
        )
        _require_hard_flags("report", self)
        _validate_report(self)
        _reject_unsafe_public_payload("report", self)
        if self.derived_validation_digest != _digest_from_values(
            _report_values_without_digest(self),
        ):
            raise ValueError("derived_validation_digest does not match report payload")


def build_research_team_domain_specialist_memory_router_report(
    inputs: Iterable[ResearchTeamDomainSpecialistMemoryRouterInput],
    *,
    config: ResearchTeamDomainSpecialistMemoryRouterConfig,
    generated_at: datetime,
) -> ResearchTeamDomainSpecialistMemoryRouterReport:
    _require_exact_type(
        config,
        ResearchTeamDomainSpecialistMemoryRouterConfig,
        "config",
    )
    _require_hard_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    normalized_inputs = _normalize_inputs(inputs)
    base_rows = tuple(
        _row_from_input(item, config=config, generated_at=generated_at_utc)
        for item in normalized_inputs
    )
    rows = tuple(
        _with_rank(row, rank)
        for rank, row in enumerate(sorted(base_rows, key=_row_sort_key), start=1)
    )
    status = _report_status(rows)
    values: dict[str, object] = {
        "generated_at": generated_at_utc,
        "config_version": config.config_version,
        "memory_count": _count(len(rows)),
        "routed_memory_count": _count(len(rows)),
        "pass_count": _status_count(rows, STATUS_PASS),
        "watch_count": _status_count(rows, STATUS_WATCH),
        "block_count": _status_count(rows, STATUS_BLOCK),
        "max_router_priority_score": _max_decimal(
            tuple(row.router_priority_score for row in rows),
        ),
        "avg_router_priority_score": _avg_decimal(
            tuple(row.router_priority_score for row in rows),
        ),
        "min_specialist_memory_score": _min_ratio(
            tuple(row.specialist_memory_score for row in rows),
        ),
        "min_domain_fit_score": _min_ratio(tuple(row.domain_fit_score for row in rows)),
        "max_conflict_score": _max_decimal(tuple(row.conflict_score for row in rows)),
        "max_review_pressure_score": _max_decimal(
            tuple(row.review_pressure_score for row in rows),
        ),
        "status": status,
        "paper_route_action": PAPER_ACTION_BY_STATUS[status],
        "reason_codes": _report_reason_codes(rows),
        "reason_code_counts": _reason_code_counts(rows),
        "rows": rows,
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    return ResearchTeamDomainSpecialistMemoryRouterReport(
        **values,
        derived_validation_digest=_digest_from_values(values),
    )


def research_team_domain_specialist_memory_router_report_payload(
    report: ResearchTeamDomainSpecialistMemoryRouterReport | Mapping[str, object],
) -> dict[str, object]:
    if type(report) is ResearchTeamDomainSpecialistMemoryRouterReport:
        _require_hard_flags("report", report)
        payload = _json_ready(asdict(report))
    elif isinstance(report, Mapping):
        payload = _json_ready(report)
    else:
        raise ValueError(
            "report must be a ResearchTeamDomainSpecialistMemoryRouterReport",
        )
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    _require_hard_flags("report payload", _MappingFlags(payload))
    expected_digest = _digest_from_payload(payload)
    if payload.get("derived_validation_digest") != expected_digest:
        raise ValueError("derived_validation_digest does not match report payload")
    _reject_unsafe_public_payload("report payload", payload, allow_json_containers=True)
    return payload


def research_team_domain_specialist_memory_router_report_digest(
    report: ResearchTeamDomainSpecialistMemoryRouterReport | Mapping[str, object],
) -> str:
    payload = research_team_domain_specialist_memory_router_report_payload(report)
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
    item: ResearchTeamDomainSpecialistMemoryRouterInput,
    *,
    config: ResearchTeamDomainSpecialistMemoryRouterConfig,
    generated_at: datetime,
) -> ResearchTeamDomainSpecialistMemoryRouterRow:
    age_seconds = _memory_age_seconds(generated_at, item.observed_at)
    memory_gap_score = _clamp_ratio(ONE - item.specialist_memory_score)
    domain_gap_score = _clamp_ratio(ONE - item.domain_fit_score)
    age_pressure_score = _age_pressure_score(age_seconds, config)
    reason_codes = _row_reason_codes(item=item, age_seconds=age_seconds, config=config)
    status = _status_from_reason_codes(reason_codes)
    return ResearchTeamDomainSpecialistMemoryRouterRow(
        route_rank=ONE,
        memory_ref=_memory_ref(item.memory_key),
        team_label=item.team_label,
        domain_label=item.domain_label,
        specialist_label=item.specialist_label,
        observed_at=item.observed_at,
        memory_age_seconds=age_seconds,
        specialist_memory_score=item.specialist_memory_score,
        domain_fit_score=item.domain_fit_score,
        memory_gap_score=memory_gap_score,
        domain_gap_score=domain_gap_score,
        age_pressure_score=age_pressure_score,
        conflict_score=item.conflict_score,
        review_pressure_score=item.review_pressure_score,
        router_priority_score=_router_priority_score(
            memory_gap_score=memory_gap_score,
            domain_gap_score=domain_gap_score,
            age_pressure_score=age_pressure_score,
            conflict_score=item.conflict_score,
            review_pressure_score=item.review_pressure_score,
        ),
        status=status,
        paper_route_action=PAPER_ACTION_BY_STATUS[status],
        reason_codes=reason_codes,
    )


def _with_rank(
    row: ResearchTeamDomainSpecialistMemoryRouterRow,
    rank: int,
) -> ResearchTeamDomainSpecialistMemoryRouterRow:
    return ResearchTeamDomainSpecialistMemoryRouterRow(
        route_rank=_count(rank),
        memory_ref=row.memory_ref,
        team_label=row.team_label,
        domain_label=row.domain_label,
        specialist_label=row.specialist_label,
        observed_at=row.observed_at,
        memory_age_seconds=row.memory_age_seconds,
        specialist_memory_score=row.specialist_memory_score,
        domain_fit_score=row.domain_fit_score,
        memory_gap_score=row.memory_gap_score,
        domain_gap_score=row.domain_gap_score,
        age_pressure_score=row.age_pressure_score,
        conflict_score=row.conflict_score,
        review_pressure_score=row.review_pressure_score,
        router_priority_score=row.router_priority_score,
        status=row.status,
        paper_route_action=row.paper_route_action,
        reason_codes=row.reason_codes,
    )


def _row_reason_codes(
    *,
    item: ResearchTeamDomainSpecialistMemoryRouterInput,
    age_seconds: Decimal,
    config: ResearchTeamDomainSpecialistMemoryRouterConfig,
) -> tuple[str, ...]:
    reasons: list[str] = []
    _append_low_reason(
        reasons,
        metric=item.specialist_memory_score,
        pass_line=config.min_pass_specialist_memory_score,
        watch_line=config.min_watch_specialist_memory_score,
        watch_code=SPECIALIST_MEMORY_WATCH_REASON,
        block_code=SPECIALIST_MEMORY_BLOCK_REASON,
    )
    _append_low_reason(
        reasons,
        metric=item.domain_fit_score,
        pass_line=config.min_pass_domain_fit_score,
        watch_line=config.min_watch_domain_fit_score,
        watch_code=DOMAIN_FIT_WATCH_REASON,
        block_code=DOMAIN_FIT_BLOCK_REASON,
    )
    _append_high_reason(
        reasons,
        metric=age_seconds,
        pass_line=config.max_pass_memory_age_seconds,
        watch_line=config.max_watch_memory_age_seconds,
        watch_code=MEMORY_AGE_WATCH_REASON,
        block_code=MEMORY_AGE_BLOCK_REASON,
    )
    _append_high_reason(
        reasons,
        metric=item.conflict_score,
        pass_line=config.max_pass_conflict_score,
        watch_line=config.max_watch_conflict_score,
        watch_code=CONFLICT_WATCH_REASON,
        block_code=CONFLICT_BLOCK_REASON,
    )
    _append_high_reason(
        reasons,
        metric=item.review_pressure_score,
        pass_line=config.max_pass_review_pressure_score,
        watch_line=config.max_watch_review_pressure_score,
        watch_code=REVIEW_PRESSURE_WATCH_REASON,
        block_code=REVIEW_PRESSURE_BLOCK_REASON,
    )
    return _normalize_reason_codes(tuple(reasons) or (CLEAR_REASON,), ROW_REASON_SEQUENCE)


def _append_low_reason(
    reasons: list[str],
    *,
    metric: Decimal,
    pass_line: Decimal,
    watch_line: Decimal,
    watch_code: str,
    block_code: str,
) -> None:
    if metric < watch_line:
        reasons.append(block_code)
        return
    if metric < pass_line:
        reasons.append(watch_code)


def _append_high_reason(
    reasons: list[str],
    *,
    metric: Decimal,
    pass_line: Decimal,
    watch_line: Decimal,
    watch_code: str,
    block_code: str,
) -> None:
    if metric > watch_line:
        reasons.append(block_code)
        return
    if metric > pass_line:
        reasons.append(watch_code)


def _router_priority_score(
    *,
    memory_gap_score: Decimal,
    domain_gap_score: Decimal,
    age_pressure_score: Decimal,
    conflict_score: Decimal,
    review_pressure_score: Decimal,
) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return _clamp_ratio(
            memory_gap_score * MEMORY_GAP_WEIGHT
            + domain_gap_score * DOMAIN_GAP_WEIGHT
            + age_pressure_score * AGE_PRESSURE_WEIGHT
            + conflict_score * CONFLICT_WEIGHT
            + review_pressure_score * REVIEW_PRESSURE_WEIGHT,
        )


def _age_pressure_score(
    age_seconds: Decimal,
    config: ResearchTeamDomainSpecialistMemoryRouterConfig,
) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        span = config.max_watch_memory_age_seconds - config.max_pass_memory_age_seconds
        if span <= ZERO:
            return ONE
        if age_seconds <= config.max_pass_memory_age_seconds:
            return ZERO
        return _clamp_ratio((age_seconds - config.max_pass_memory_age_seconds) / span)


def _memory_age_seconds(generated_at: datetime, observed_at: datetime) -> Decimal:
    if observed_at > generated_at:
        raise ValueError("observed_at must not be after generated_at")
    seconds = Decimal(str((generated_at - observed_at).total_seconds()))
    return _quantize(seconds)


def _memory_ref(memory_key: str) -> str:
    return f"memory_ref_{sha256(memory_key.encode('utf-8')).hexdigest()}"


def _status_from_reason_codes(reason_codes: tuple[str, ...]) -> str:
    if any(reason_code.endswith("_block") for reason_code in reason_codes):
        return STATUS_BLOCK
    if any(reason_code.endswith("_watch") for reason_code in reason_codes):
        return STATUS_WATCH
    return STATUS_PASS


def _report_status(
    rows: tuple[ResearchTeamDomainSpecialistMemoryRouterRow, ...],
) -> str:
    if any(row.status == STATUS_BLOCK for row in rows):
        return STATUS_BLOCK
    if any(row.status == STATUS_WATCH for row in rows):
        return STATUS_WATCH
    return STATUS_PASS


def _report_reason_codes(
    rows: tuple[ResearchTeamDomainSpecialistMemoryRouterRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return (EMPTY_REASON,)
    seen = frozenset(reason_code for row in rows for reason_code in row.reason_codes)
    return tuple(reason_code for reason_code in ROW_REASON_SEQUENCE if reason_code in seen)


def _reason_code_counts(
    rows: tuple[ResearchTeamDomainSpecialistMemoryRouterRow, ...],
) -> tuple[ResearchTeamDomainSpecialistMemoryRouterReasonCodeCount, ...]:
    if not rows:
        return ()
    counts = Counter(reason_code for row in rows for reason_code in row.reason_codes)
    total = _count(len(rows))
    return tuple(
        ResearchTeamDomainSpecialistMemoryRouterReasonCodeCount(
            reason_code=reason_code,
            count=_count(counts[reason_code]),
            memory_ratio=_safe_divide(_count(counts[reason_code]), total),
        )
        for reason_code in ROW_REASON_SEQUENCE
        if counts[reason_code]
    )


def _row_sort_key(
    row: ResearchTeamDomainSpecialistMemoryRouterRow,
) -> tuple[int, Decimal, str, str, str]:
    return (
        _status_rank(row.status),
        -row.router_priority_score,
        row.team_label,
        row.domain_label,
        row.memory_ref,
    )


def _status_rank(status: str) -> int:
    return {STATUS_BLOCK: 0, STATUS_WATCH: 1, STATUS_PASS: 2}[status]


def _normalize_inputs(
    value: Iterable[ResearchTeamDomainSpecialistMemoryRouterInput],
) -> tuple[ResearchTeamDomainSpecialistMemoryRouterInput, ...]:
    if isinstance(value, (str, bytes, Mapping)):
        raise ValueError("inputs must be an iterable of memory router inputs")
    try:
        rows = tuple(value)
    except TypeError as exc:
        raise ValueError("inputs must be an iterable of memory router inputs") from exc
    seen_keys: set[str] = set()
    for row in rows:
        if type(row) is not ResearchTeamDomainSpecialistMemoryRouterInput:
            raise ValueError("inputs must contain memory router inputs")
        _require_hard_flags("input", row)
        if row.memory_key in seen_keys:
            raise ValueError("memory_key values must be unique")
        seen_keys.add(row.memory_key)
    return tuple(sorted(rows, key=lambda row: _memory_ref(row.memory_key)))


def _normalize_rows(
    value: object,
) -> tuple[ResearchTeamDomainSpecialistMemoryRouterRow, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("rows must be a list or tuple")
    rows = tuple(value)
    seen_refs: set[str] = set()
    for row in rows:
        if type(row) is not ResearchTeamDomainSpecialistMemoryRouterRow:
            raise ValueError("rows must contain memory router rows")
        _require_hard_flags("row", row)
        if row.memory_ref in seen_refs:
            raise ValueError("memory_ref values must be unique")
        seen_refs.add(row.memory_ref)
    expected = tuple(
        _with_rank(row, rank)
        for rank, row in enumerate(sorted(rows, key=_row_sort_key), start=1)
    )
    if rows != expected:
        raise ValueError("rows must be deterministic")
    return rows


def _normalize_reason_code_counts(
    value: object,
) -> tuple[ResearchTeamDomainSpecialistMemoryRouterReasonCodeCount, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("reason_code_counts must be a list or tuple")
    rows = tuple(value)
    seen: set[str] = set()
    for row in rows:
        if type(row) is not ResearchTeamDomainSpecialistMemoryRouterReasonCodeCount:
            raise ValueError("reason_code_counts must contain reason counts")
        _require_hard_flags("reason_code_count", row)
        if row.reason_code in seen:
            raise ValueError("reason_code values must be unique")
        seen.add(row.reason_code)
    expected = tuple(
        row for reason_code in ROW_REASON_SEQUENCE for row in rows
        if row.reason_code == reason_code
    )
    if rows != expected:
        raise ValueError("reason_code_counts must be deterministic")
    return rows


def _normalize_reason_codes(
    value: object,
    sequence: tuple[str, ...],
) -> tuple[str, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("reason_codes must be a list or tuple")
    reason_codes = tuple(value)
    if not reason_codes:
        raise ValueError("reason_codes must not be empty")
    for reason_code in reason_codes:
        _require_reason_code("reason_code", reason_code, sequence)
    if len(set(reason_codes)) != len(reason_codes):
        raise ValueError("reason_codes must be unique")
    expected = tuple(reason_code for reason_code in sequence if reason_code in reason_codes)
    if reason_codes != expected:
        raise ValueError("reason_codes must be deterministic")
    return reason_codes


def _validate_row(row: ResearchTeamDomainSpecialistMemoryRouterRow) -> None:
    if row.memory_gap_score != _clamp_ratio(ONE - row.specialist_memory_score):
        raise ValueError("memory_gap_score must match specialist_memory_score")
    if row.domain_gap_score != _clamp_ratio(ONE - row.domain_fit_score):
        raise ValueError("domain_gap_score must match domain_fit_score")
    if row.router_priority_score != _router_priority_score(
        memory_gap_score=row.memory_gap_score,
        domain_gap_score=row.domain_gap_score,
        age_pressure_score=row.age_pressure_score,
        conflict_score=row.conflict_score,
        review_pressure_score=row.review_pressure_score,
    ):
        raise ValueError("router_priority_score must match component scores")
    if row.status != _status_from_reason_codes(row.reason_codes):
        raise ValueError("status must match reason_codes")


def _validate_report(report: ResearchTeamDomainSpecialistMemoryRouterReport) -> None:
    if report.memory_count != _count(len(report.rows)):
        raise ValueError("memory_count must match rows")
    if report.routed_memory_count != _count(len(report.rows)):
        raise ValueError("routed_memory_count must match rows")
    if report.pass_count != _status_count(report.rows, STATUS_PASS):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _status_count(report.rows, STATUS_WATCH):
        raise ValueError("watch_count must match rows")
    if report.block_count != _status_count(report.rows, STATUS_BLOCK):
        raise ValueError("block_count must match rows")
    if report.max_router_priority_score != _max_decimal(
        tuple(row.router_priority_score for row in report.rows),
    ):
        raise ValueError("max_router_priority_score must match rows")
    if report.avg_router_priority_score != _avg_decimal(
        tuple(row.router_priority_score for row in report.rows),
    ):
        raise ValueError("avg_router_priority_score must match rows")
    if report.min_specialist_memory_score != _min_ratio(
        tuple(row.specialist_memory_score for row in report.rows),
    ):
        raise ValueError("min_specialist_memory_score must match rows")
    if report.min_domain_fit_score != _min_ratio(
        tuple(row.domain_fit_score for row in report.rows),
    ):
        raise ValueError("min_domain_fit_score must match rows")
    if report.max_conflict_score != _max_decimal(
        tuple(row.conflict_score for row in report.rows),
    ):
        raise ValueError("max_conflict_score must match rows")
    if report.max_review_pressure_score != _max_decimal(
        tuple(row.review_pressure_score for row in report.rows),
    ):
        raise ValueError("max_review_pressure_score must match rows")
    if report.status != _report_status(report.rows):
        raise ValueError("status must match rows")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")
    if report.reason_code_counts != _reason_code_counts(report.rows):
        raise ValueError("reason_code_counts must match rows")


def _status_count(
    rows: tuple[ResearchTeamDomainSpecialistMemoryRouterRow, ...],
    status: str,
) -> Decimal:
    return _count(sum(1 for row in rows if row.status == status))


def _max_decimal(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return ZERO
    return _quantize(max(values))


def _min_ratio(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return ZERO
    return _clamp_ratio(min(values))


def _avg_decimal(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return _quantize(sum(values, ZERO) / Decimal(len(values)))


def _safe_divide(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator <= ZERO:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return _clamp_ratio(numerator / denominator)


def _clamp_ratio(value: Decimal) -> Decimal:
    normalized = _quantize(value)
    if normalized < ZERO:
        return ZERO
    if normalized > ONE:
        return ONE
    return normalized


def _count(value: int) -> Decimal:
    return Decimal(value).quantize(QUANTUM)


def _quantize(value: Decimal) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError("value must be a Decimal")
    if not value.is_finite():
        raise ValueError("value must be finite")
    return value.quantize(QUANTUM)


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_exact_type(value: object, expected_type: type[object], label: str) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{label} must be exactly {expected_type.__name__}")


def _require_hard_flags(label: str, value: object) -> None:
    require_paper_only_flags(label, value)


def _require_memory_key(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be canonical")


def _require_memory_ref(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    prefix = "memory_ref_"
    if not value.startswith(prefix):
        raise ValueError(f"{field_name} must be a memory ref")
    digest = value[len(prefix):]
    _require_sha256_digest(field_name, digest)
    return value


def _require_public_label(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be canonical")
    if any(character not in PUBLIC_LABEL_CHARS for character in value):
        raise ValueError(f"{field_name} must be public")
    lowered = value.lower()
    if lowered != value:
        raise ValueError(f"{field_name} must be canonical")
    if any(part in lowered for part in UNSAFE_PUBLIC_PARTS):
        raise ValueError(f"{field_name} must be public")
    return value


def _require_reason_code(
    field_name: str,
    value: object,
    sequence: tuple[str, ...],
) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if value not in sequence:
        raise ValueError(f"{field_name} must be known")
    _require_public_label(field_name, value)
    return value


def _require_status(field_name: str, value: object) -> str:
    if type(value) is not str or value not in TEAM_DOMAIN_SPECIALIST_MEMORY_ROUTER_STATUSES:
        raise ValueError(f"{field_name} must be pass, watch, or block")
    return value


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return value.quantize(QUANTUM)


def _require_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _require_positive_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _require_count_decimal(field_name: str, value: object) -> Decimal:
    return _require_nonnegative_decimal(field_name, value)


def _require_ratio_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < ZERO or normalized > ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return normalized


def _require_sha256_digest(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a lowercase sha256 digest")
    if len(value) != 64:
        raise ValueError(f"{field_name} must be a lowercase sha256 digest")
    if any(character not in HEX_CHARS for character in value):
        raise ValueError(f"{field_name} must be a lowercase sha256 digest")


def _report_values_without_digest(
    report: ResearchTeamDomainSpecialistMemoryRouterReport,
) -> dict[str, object]:
    values = asdict(report)
    values.pop("derived_validation_digest", None)
    return values


def _digest_from_values(values: Mapping[str, object]) -> str:
    payload = _json_ready(values)
    if type(payload) is not dict:
        raise ValueError("digest payload must be a JSON object")
    _reject_unsafe_public_payload("digest payload", payload, allow_json_containers=True)
    return _canonical_digest(payload)


def _digest_from_payload(payload: dict[str, object]) -> str:
    unsigned = dict(payload)
    unsigned.pop("derived_validation_digest", None)
    return _canonical_digest(unsigned)


def _canonical_digest(payload: dict[str, object]) -> str:
    encoded = json.dumps(
        payload,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return sha256(encoded).hexdigest()


def _json_ready(value: Any) -> Any:
    if is_dataclass(value) and not isinstance(value, type):
        return _json_ready(asdict(value))
    if isinstance(value, Decimal):
        if type(value) is not Decimal:
            raise ValueError("JSON Decimal value must be exactly Decimal")
        if not value.is_finite():
            raise ValueError("JSON Decimal value must be finite")
        return str(value.quantize(QUANTUM))
    if isinstance(value, datetime):
        if type(value) is not datetime:
            raise ValueError("JSON datetime value must be a datetime")
        if value.tzinfo is None:
            raise ValueError("JSON datetime value must be timezone-aware")
        return value.astimezone(UTC).isoformat()
    if value is None:
        return None
    if type(value) is bool:
        return value
    if isinstance(value, float):
        raise ValueError("JSON value must not be a float")
    if type(value) is int:
        raise ValueError("JSON numeric value must use Decimal")
    if type(value) is str:
        return value
    if isinstance(value, tuple):
        return [_json_ready(item) for item in value]
    if isinstance(value, list):
        return [_json_ready(item) for item in value]
    if isinstance(value, Mapping):
        ready: dict[str, object] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            ready[key] = _json_ready(item)
        return ready
    raise ValueError("value is not JSON serializable")


def _reject_unsafe_public_payload(
    label: str,
    value: object,
    *,
    allow_json_containers: bool = False,
    path: str = "",
) -> None:
    if is_dataclass(value) and not isinstance(value, type):
        _reject_unsafe_public_payload(
            label,
            asdict(value),
            allow_json_containers=allow_json_containers,
            path=path,
        )
        return
    if type(value) is str:
        lowered = value.lower()
        if any(part in lowered for part in UNSAFE_PUBLIC_PARTS):
            raise ValueError(f"{path or label} contains unsafe public payload")
        return
    if isinstance(value, Decimal):
        if type(value) is not Decimal:
            raise ValueError(f"{path or label} must be exactly Decimal")
        if not value.is_finite():
            raise ValueError(f"{path or label} must be finite")
        return
    if isinstance(value, datetime):
        if type(value) is not datetime:
            raise ValueError(f"{path or label} must be a datetime")
        if value.tzinfo is None:
            raise ValueError(f"{path or label} must be timezone-aware")
        return
    if value is None or type(value) is bool:
        return
    if isinstance(value, float):
        raise ValueError(f"{path or label} must not be a float")
    if type(value) is int:
        raise ValueError(f"{path or label} must use Decimal")
    if isinstance(value, Mapping):
        if not allow_json_containers and type(value) is not dict:
            raise ValueError(f"{path or label} must be a dict")
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            item_path = key if not path else f"{path}.{key}"
            if any(part in key.lower() for part in UNSAFE_PUBLIC_PARTS):
                raise ValueError(f"{item_path} contains unsafe public payload")
            if key in {"paper_only", "report_only", "readonly"} and item is not True:
                raise ValueError(f"{item_path} must be True")
            _reject_unsafe_public_payload(
                label,
                item,
                allow_json_containers=allow_json_containers,
                path=item_path,
            )
        return
    if isinstance(value, (list, tuple)):
        if not allow_json_containers and type(value) is not tuple:
            raise ValueError(f"{path or label} must be a tuple")
        for index, item in enumerate(value):
            item_path = f"{path}[{index}]" if path else f"{label}[{index}]"
            _reject_unsafe_public_payload(
                label,
                item,
                allow_json_containers=allow_json_containers,
                path=item_path,
            )
        return
    raise ValueError(f"{path or label} is not public payload")
