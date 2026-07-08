"""Candidate packet backlog priority report."""

from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from dataclasses import asdict, dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal, ROUND_HALF_UP
import hashlib
import json
import re
from typing import Any


DEFAULT_RESEARCH_STRATEGY_CANDIDATE_PRIORITIZATION_BACKLOG_CONFIG_VERSION = (
    "research-strategy-candidate-prioritization-backlog-report"
)

STATUSES = ("pass", "watch", "block")

_QUANT = Decimal("0.000001")
_ZERO = Decimal("0.000000")
_ONE = Decimal("1.000000")
_PUBLIC_TEXT_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,127}$")
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
_HARD_FLAG_FIELDS = ("paper_only", "report_only", "readonly")
_UNSAFE_PUBLIC_TERMS = tuple(
    "".join(parts)
    for parts in (
        ("reco", "mmendation"),
        ("siz", "ing"),
        ("b", "uy"),
        ("s", "ell"),
        ("wa", "llet"),
        ("ord", "er"),
        ("li", "ve"),
        ("trad", "ing"),
        ("data", "base"),
        ("net", "work"),
        ("auth",),
        ("secret",),
        ("token",),
        ("mutation",),
    )
)
_REASON_CODE_SEQUENCE = (
    "candidate_prioritization_backlog_empty",
    "candidate_prioritization_backlog_evidence_gap_block",
    "candidate_prioritization_backlog_source_freshness_block",
    "candidate_prioritization_backlog_cost_sanity_block",
    "candidate_prioritization_backlog_domain_team_coverage_block",
    "candidate_prioritization_backlog_recheck_urgency_block",
    "candidate_prioritization_backlog_evidence_gap_watch",
    "candidate_prioritization_backlog_source_freshness_watch",
    "candidate_prioritization_backlog_cost_sanity_watch",
    "candidate_prioritization_backlog_domain_team_coverage_watch",
    "candidate_prioritization_backlog_recheck_urgency_watch",
    "candidate_prioritization_backlog_clear",
)


@dataclass(frozen=True)
class ResearchStrategyCandidatePrioritizationBacklogConfig:
    config_version: str = (
        DEFAULT_RESEARCH_STRATEGY_CANDIDATE_PRIORITIZATION_BACKLOG_CONFIG_VERSION
    )
    evidence_gap_watch_ratio: Decimal = Decimal("0.100000")
    evidence_gap_block_ratio: Decimal = Decimal("0.500000")
    source_freshness_watch_seconds: Decimal = Decimal("86400.000000")
    source_freshness_block_seconds: Decimal = Decimal("172800.000000")
    cost_sanity_gap_watch_ratio: Decimal = Decimal("0.100000")
    cost_sanity_gap_block_ratio: Decimal = Decimal("0.500000")
    domain_team_coverage_gap_watch_ratio: Decimal = Decimal("0.100000")
    domain_team_coverage_gap_block_ratio: Decimal = Decimal("0.500000")
    recheck_urgency_watch_seconds: Decimal = Decimal("86400.000000")
    recheck_urgency_block_seconds: Decimal = Decimal("172800.000000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchStrategyCandidatePrioritizationBacklogConfig:
            raise TypeError(
                "ResearchStrategyCandidatePrioritizationBacklogConfig does not "
                "support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchStrategyCandidatePrioritizationBacklogConfig:
            raise ValueError(
                "config must be exactly "
                "ResearchStrategyCandidatePrioritizationBacklogConfig",
            )
        _require_public_text("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_STRATEGY_CANDIDATE_PRIORITIZATION_BACKLOG_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "evidence_gap_watch_ratio",
            "evidence_gap_block_ratio",
            "cost_sanity_gap_watch_ratio",
            "cost_sanity_gap_block_ratio",
            "domain_team_coverage_gap_watch_ratio",
            "domain_team_coverage_gap_block_ratio",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "source_freshness_watch_seconds",
            "source_freshness_block_seconds",
            "recheck_urgency_watch_seconds",
            "recheck_urgency_block_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_positive_decimal(field_name, getattr(self, field_name)),
            )
        _validate_config(self)
        _require_hard_flags("config", self)
        _reject_unsafe_public_payload("config", self)


@dataclass(frozen=True)
class ResearchStrategyCandidatePrioritizationBacklogInput:
    candidate_packet_id: str
    team_id: str
    category_id: str
    candidate_slug: str
    queued_at: datetime
    last_rechecked_at: datetime | None
    required_evidence_count: Decimal
    verified_evidence_count: Decimal
    source_age_seconds: Decimal
    estimated_research_cost_units: Decimal
    max_sane_research_cost_units: Decimal
    required_domain_team_count: Decimal
    covered_domain_team_count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchStrategyCandidatePrioritizationBacklogInput:
            raise TypeError(
                "ResearchStrategyCandidatePrioritizationBacklogInput does not "
                "support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchStrategyCandidatePrioritizationBacklogInput:
            raise ValueError(
                "packet must be exactly "
                "ResearchStrategyCandidatePrioritizationBacklogInput",
            )
        for field_name in (
            "candidate_packet_id",
            "team_id",
            "category_id",
            "candidate_slug",
        ):
            _require_public_text(field_name, getattr(self, field_name))
        object.__setattr__(self, "queued_at", _as_utc("queued_at", self.queued_at))
        object.__setattr__(
            self,
            "last_rechecked_at",
            _as_optional_utc("last_rechecked_at", self.last_rechecked_at),
        )
        for field_name in (
            "required_evidence_count",
            "max_sane_research_cost_units",
            "required_domain_team_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_positive_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "verified_evidence_count",
            "source_age_seconds",
            "estimated_research_cost_units",
            "covered_domain_team_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        _validate_input(self)
        _require_hard_flags("packet", self)
        _reject_unsafe_public_payload("packet", self)


@dataclass(frozen=True)
class ResearchStrategyCandidatePrioritizationBacklogRow:
    backlog_rank: Decimal
    candidate_packet_id: str
    team_id: str
    category_id: str
    candidate_slug: str
    status: str
    backlog_priority_score: Decimal
    queued_at: datetime
    last_rechecked_at: datetime | None
    required_evidence_count: Decimal
    verified_evidence_count: Decimal
    evidence_gap_ratio: Decimal
    source_age_seconds: Decimal
    estimated_research_cost_units: Decimal
    max_sane_research_cost_units: Decimal
    cost_sanity_gap_ratio: Decimal
    required_domain_team_count: Decimal
    covered_domain_team_count: Decimal
    domain_team_coverage_gap_ratio: Decimal
    recheck_age_seconds: Decimal
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchStrategyCandidatePrioritizationBacklogRow:
            raise TypeError(
                "ResearchStrategyCandidatePrioritizationBacklogRow does not "
                "support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchStrategyCandidatePrioritizationBacklogRow:
            raise ValueError(
                "row must be exactly ResearchStrategyCandidatePrioritizationBacklogRow",
            )
        object.__setattr__(
            self,
            "backlog_rank",
            _normalize_positive_decimal("backlog_rank", self.backlog_rank),
        )
        for field_name in (
            "candidate_packet_id",
            "team_id",
            "category_id",
            "candidate_slug",
        ):
            _require_public_text(field_name, getattr(self, field_name))
        _require_status("status", self.status)
        object.__setattr__(
            self,
            "backlog_priority_score",
            _normalize_ratio("backlog_priority_score", self.backlog_priority_score),
        )
        object.__setattr__(self, "queued_at", _as_utc("queued_at", self.queued_at))
        object.__setattr__(
            self,
            "last_rechecked_at",
            _as_optional_utc("last_rechecked_at", self.last_rechecked_at),
        )
        for field_name in (
            "required_evidence_count",
            "max_sane_research_cost_units",
            "required_domain_team_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_positive_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "verified_evidence_count",
            "source_age_seconds",
            "estimated_research_cost_units",
            "covered_domain_team_count",
            "recheck_age_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "evidence_gap_ratio",
            "cost_sanity_gap_ratio",
            "domain_team_coverage_gap_ratio",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        _validate_row(self)
        _require_hard_flags("row", self)
        _reject_unsafe_public_payload("row", self)


@dataclass(frozen=True)
class ResearchStrategyCandidatePrioritizationBacklogReport:
    generated_at: datetime
    config_version: str
    status: str
    packet_count: Decimal
    block_packet_count: Decimal
    watch_packet_count: Decimal
    pass_packet_count: Decimal
    max_backlog_priority_score: Decimal
    max_evidence_gap_ratio: Decimal
    max_source_age_seconds: Decimal
    max_cost_sanity_gap_ratio: Decimal
    max_domain_team_coverage_gap_ratio: Decimal
    max_recheck_age_seconds: Decimal
    rows: tuple[ResearchStrategyCandidatePrioritizationBacklogRow, ...]
    reason_codes: tuple[str, ...]
    derived_validation_digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchStrategyCandidatePrioritizationBacklogReport:
            raise TypeError(
                "ResearchStrategyCandidatePrioritizationBacklogReport does not "
                "support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchStrategyCandidatePrioritizationBacklogReport:
            raise ValueError(
                "report must be exactly "
                "ResearchStrategyCandidatePrioritizationBacklogReport",
            )
        object.__setattr__(
            self,
            "generated_at",
            _as_generated_at_utc("generated_at", self.generated_at),
        )
        _require_public_text("config_version", self.config_version)
        _require_status("status", self.status)
        for field_name in (
            "packet_count",
            "block_packet_count",
            "watch_packet_count",
            "pass_packet_count",
            "max_source_age_seconds",
            "max_recheck_age_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "max_backlog_priority_score",
            "max_evidence_gap_ratio",
            "max_cost_sanity_gap_ratio",
            "max_domain_team_coverage_gap_ratio",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        _require_sha256("derived_validation_digest", self.derived_validation_digest)
        _require_hard_flags("report", self)
        _validate_report(self)
        _reject_unsafe_public_payload("report", self)
        expected_digest = _report_digest_from_values(_report_values_without_digest(self))
        if self.derived_validation_digest != expected_digest:
            raise ValueError("derived_validation_digest does not match report payload")


def build_research_strategy_candidate_prioritization_backlog_report(
    packets: Iterable[ResearchStrategyCandidatePrioritizationBacklogInput],
    *,
    config: ResearchStrategyCandidatePrioritizationBacklogConfig,
    generated_at: datetime,
) -> ResearchStrategyCandidatePrioritizationBacklogReport:
    if type(config) is not ResearchStrategyCandidatePrioritizationBacklogConfig:
        raise ValueError(
            "config must be a ResearchStrategyCandidatePrioritizationBacklogConfig",
        )
    _require_hard_flags("config", config)
    generated_at_utc = _as_generated_at_utc("generated_at", generated_at)
    inputs = _normalize_inputs(packets)
    _validate_input_times(inputs, generated_at_utc)
    base_rows = tuple(_row_from_packet(packet, config, generated_at_utc) for packet in inputs)
    rows = tuple(
        _with_backlog_rank(row, rank)
        for rank, row in enumerate(sorted(base_rows, key=_row_sort_key), start=1)
    )
    values: dict[str, object] = {
        "generated_at": generated_at_utc,
        "config_version": config.config_version,
        "status": _report_status(rows),
        "packet_count": _count(len(rows)),
        "block_packet_count": _status_count(rows, "block"),
        "watch_packet_count": _status_count(rows, "watch"),
        "pass_packet_count": _status_count(rows, "pass"),
        "max_backlog_priority_score": _max_ratio(
            tuple(row.backlog_priority_score for row in rows),
        ),
        "max_evidence_gap_ratio": _max_ratio(
            tuple(row.evidence_gap_ratio for row in rows),
        ),
        "max_source_age_seconds": _max_decimal(
            tuple(row.source_age_seconds for row in rows),
        ),
        "max_cost_sanity_gap_ratio": _max_ratio(
            tuple(row.cost_sanity_gap_ratio for row in rows),
        ),
        "max_domain_team_coverage_gap_ratio": _max_ratio(
            tuple(row.domain_team_coverage_gap_ratio for row in rows),
        ),
        "max_recheck_age_seconds": _max_decimal(
            tuple(row.recheck_age_seconds for row in rows),
        ),
        "rows": rows,
        "reason_codes": _report_reason_codes(rows),
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    return ResearchStrategyCandidatePrioritizationBacklogReport(
        **values,
        derived_validation_digest=_report_digest_from_values(values),
    )


def research_strategy_candidate_prioritization_backlog_report_payload(
    report: ResearchStrategyCandidatePrioritizationBacklogReport | Mapping[str, object],
) -> dict[str, object]:
    if type(report) is ResearchStrategyCandidatePrioritizationBacklogReport:
        _require_hard_flags("report", report)
        payload = _json_ready(asdict(report))
        _reject_unsafe_public_payload(
            "report payload",
            payload,
            allow_json_containers=True,
        )
        if type(payload) is not dict:
            raise ValueError("report payload must be a JSON object")
        expected_digest = _digest_from_payload(payload)
        if payload["derived_validation_digest"] != expected_digest:
            raise ValueError("derived_validation_digest does not match report payload")
        return payload
    if isinstance(report, Mapping):
        payload = _json_ready(report)
        if type(payload) is not dict:
            raise ValueError("report payload must be a JSON object")
        _reject_unsafe_public_payload(
            "report payload",
            payload,
            allow_json_containers=True,
        )
        _require_hard_flags("report payload", _MappingFlags(payload))
        expected_digest = _digest_from_payload(payload)
        if payload.get("derived_validation_digest") != expected_digest:
            raise ValueError("derived_validation_digest does not match report payload")
        return payload
    raise ValueError(
        "report must be a ResearchStrategyCandidatePrioritizationBacklogReport",
    )


def research_strategy_candidate_prioritization_backlog_report_digest(
    report: ResearchStrategyCandidatePrioritizationBacklogReport | Mapping[str, object],
) -> str:
    payload = research_strategy_candidate_prioritization_backlog_report_payload(report)
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


def _row_from_packet(
    packet: ResearchStrategyCandidatePrioritizationBacklogInput,
    config: ResearchStrategyCandidatePrioritizationBacklogConfig,
    generated_at: datetime,
) -> ResearchStrategyCandidatePrioritizationBacklogRow:
    evidence_gap_ratio = _ratio_gap(
        packet.required_evidence_count,
        packet.verified_evidence_count,
    )
    cost_sanity_gap_ratio = _cost_gap_ratio(
        packet.estimated_research_cost_units,
        packet.max_sane_research_cost_units,
    )
    domain_team_coverage_gap_ratio = _ratio_gap(
        packet.required_domain_team_count,
        packet.covered_domain_team_count,
    )
    recheck_anchor = packet.last_rechecked_at or packet.queued_at
    recheck_age_seconds = _age_seconds(recheck_anchor, generated_at)
    reason_codes = _row_reason_codes(
        evidence_gap_ratio=evidence_gap_ratio,
        source_age_seconds=packet.source_age_seconds,
        cost_sanity_gap_ratio=cost_sanity_gap_ratio,
        domain_team_coverage_gap_ratio=domain_team_coverage_gap_ratio,
        recheck_age_seconds=recheck_age_seconds,
        config=config,
    )
    return ResearchStrategyCandidatePrioritizationBacklogRow(
        backlog_rank=_ONE,
        candidate_packet_id=packet.candidate_packet_id,
        team_id=packet.team_id,
        category_id=packet.category_id,
        candidate_slug=packet.candidate_slug,
        status=_row_status(reason_codes),
        backlog_priority_score=_priority_score(
            evidence_gap_ratio=evidence_gap_ratio,
            source_age_seconds=packet.source_age_seconds,
            cost_sanity_gap_ratio=cost_sanity_gap_ratio,
            domain_team_coverage_gap_ratio=domain_team_coverage_gap_ratio,
            recheck_age_seconds=recheck_age_seconds,
            config=config,
        ),
        queued_at=packet.queued_at,
        last_rechecked_at=packet.last_rechecked_at,
        required_evidence_count=packet.required_evidence_count,
        verified_evidence_count=packet.verified_evidence_count,
        evidence_gap_ratio=evidence_gap_ratio,
        source_age_seconds=packet.source_age_seconds,
        estimated_research_cost_units=packet.estimated_research_cost_units,
        max_sane_research_cost_units=packet.max_sane_research_cost_units,
        cost_sanity_gap_ratio=cost_sanity_gap_ratio,
        required_domain_team_count=packet.required_domain_team_count,
        covered_domain_team_count=packet.covered_domain_team_count,
        domain_team_coverage_gap_ratio=domain_team_coverage_gap_ratio,
        recheck_age_seconds=recheck_age_seconds,
        reason_codes=reason_codes,
    )


def _with_backlog_rank(
    row: ResearchStrategyCandidatePrioritizationBacklogRow,
    rank: int,
) -> ResearchStrategyCandidatePrioritizationBacklogRow:
    return ResearchStrategyCandidatePrioritizationBacklogRow(
        backlog_rank=_count(rank),
        candidate_packet_id=row.candidate_packet_id,
        team_id=row.team_id,
        category_id=row.category_id,
        candidate_slug=row.candidate_slug,
        status=row.status,
        backlog_priority_score=row.backlog_priority_score,
        queued_at=row.queued_at,
        last_rechecked_at=row.last_rechecked_at,
        required_evidence_count=row.required_evidence_count,
        verified_evidence_count=row.verified_evidence_count,
        evidence_gap_ratio=row.evidence_gap_ratio,
        source_age_seconds=row.source_age_seconds,
        estimated_research_cost_units=row.estimated_research_cost_units,
        max_sane_research_cost_units=row.max_sane_research_cost_units,
        cost_sanity_gap_ratio=row.cost_sanity_gap_ratio,
        required_domain_team_count=row.required_domain_team_count,
        covered_domain_team_count=row.covered_domain_team_count,
        domain_team_coverage_gap_ratio=row.domain_team_coverage_gap_ratio,
        recheck_age_seconds=row.recheck_age_seconds,
        reason_codes=row.reason_codes,
    )


def _row_reason_codes(
    *,
    evidence_gap_ratio: Decimal,
    source_age_seconds: Decimal,
    cost_sanity_gap_ratio: Decimal,
    domain_team_coverage_gap_ratio: Decimal,
    recheck_age_seconds: Decimal,
    config: ResearchStrategyCandidatePrioritizationBacklogConfig,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    _append_threshold_reason(
        reason_codes,
        metric=evidence_gap_ratio,
        watch=config.evidence_gap_watch_ratio,
        block=config.evidence_gap_block_ratio,
        watch_code="candidate_prioritization_backlog_evidence_gap_watch",
        block_code="candidate_prioritization_backlog_evidence_gap_block",
    )
    _append_threshold_reason(
        reason_codes,
        metric=source_age_seconds,
        watch=config.source_freshness_watch_seconds,
        block=config.source_freshness_block_seconds,
        watch_code="candidate_prioritization_backlog_source_freshness_watch",
        block_code="candidate_prioritization_backlog_source_freshness_block",
    )
    _append_threshold_reason(
        reason_codes,
        metric=cost_sanity_gap_ratio,
        watch=config.cost_sanity_gap_watch_ratio,
        block=config.cost_sanity_gap_block_ratio,
        watch_code="candidate_prioritization_backlog_cost_sanity_watch",
        block_code="candidate_prioritization_backlog_cost_sanity_block",
    )
    _append_threshold_reason(
        reason_codes,
        metric=domain_team_coverage_gap_ratio,
        watch=config.domain_team_coverage_gap_watch_ratio,
        block=config.domain_team_coverage_gap_block_ratio,
        watch_code="candidate_prioritization_backlog_domain_team_coverage_watch",
        block_code="candidate_prioritization_backlog_domain_team_coverage_block",
    )
    _append_threshold_reason(
        reason_codes,
        metric=recheck_age_seconds,
        watch=config.recheck_urgency_watch_seconds,
        block=config.recheck_urgency_block_seconds,
        watch_code="candidate_prioritization_backlog_recheck_urgency_watch",
        block_code="candidate_prioritization_backlog_recheck_urgency_block",
    )
    if not reason_codes:
        reason_codes.append("candidate_prioritization_backlog_clear")
    return _normalize_reason_codes("reason_codes", tuple(reason_codes))


def _append_threshold_reason(
    reason_codes: list[str],
    *,
    metric: Decimal,
    watch: Decimal,
    block: Decimal,
    watch_code: str,
    block_code: str,
) -> None:
    if metric >= block:
        reason_codes.append(block_code)
        return
    if metric >= watch:
        reason_codes.append(watch_code)


def _row_status(reason_codes: tuple[str, ...]) -> str:
    if any(reason_code.endswith("_block") for reason_code in reason_codes):
        return "block"
    if any(reason_code.endswith("_watch") for reason_code in reason_codes):
        return "watch"
    return "pass"


def _report_status(
    rows: tuple[ResearchStrategyCandidatePrioritizationBacklogRow, ...],
) -> str:
    if any(row.status == "block" for row in rows):
        return "block"
    if any(row.status == "watch" for row in rows):
        return "watch"
    return "pass"


def _report_reason_codes(
    rows: tuple[ResearchStrategyCandidatePrioritizationBacklogRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return ("candidate_prioritization_backlog_empty",)
    reason_codes: list[str] = []
    for row in rows:
        reason_codes.extend(row.reason_codes)
    return _normalize_reason_codes("reason_codes", tuple(reason_codes))


def _priority_score(
    *,
    evidence_gap_ratio: Decimal,
    source_age_seconds: Decimal,
    cost_sanity_gap_ratio: Decimal,
    domain_team_coverage_gap_ratio: Decimal,
    recheck_age_seconds: Decimal,
    config: ResearchStrategyCandidatePrioritizationBacklogConfig,
) -> Decimal:
    return _max_ratio(
        (
            _ratio_to_cap(evidence_gap_ratio, config.evidence_gap_block_ratio),
            _ratio_to_cap(source_age_seconds, config.source_freshness_block_seconds),
            _ratio_to_cap(cost_sanity_gap_ratio, config.cost_sanity_gap_block_ratio),
            _ratio_to_cap(
                domain_team_coverage_gap_ratio,
                config.domain_team_coverage_gap_block_ratio,
            ),
            _ratio_to_cap(recheck_age_seconds, config.recheck_urgency_block_seconds),
        ),
    )


def _row_sort_key(row: ResearchStrategyCandidatePrioritizationBacklogRow) -> tuple[object, ...]:
    return (
        -_status_rank(row.status),
        -row.backlog_priority_score,
        -row.evidence_gap_ratio,
        -row.source_age_seconds,
        -row.cost_sanity_gap_ratio,
        -row.domain_team_coverage_gap_ratio,
        -row.recheck_age_seconds,
        row.candidate_packet_id,
    )


def _status_rank(status: str) -> int:
    if status == "block":
        return 2
    if status == "watch":
        return 1
    return 0


def _status_count(
    rows: tuple[ResearchStrategyCandidatePrioritizationBacklogRow, ...],
    status: str,
) -> Decimal:
    return _count(sum(1 for row in rows if row.status == status))


def _ratio_gap(required_count: Decimal, covered_count: Decimal) -> Decimal:
    if required_count <= _ZERO:
        raise ValueError("required_count must be positive")
    return _clamp_ratio((required_count - covered_count) / required_count)


def _cost_gap_ratio(estimated_units: Decimal, max_sane_units: Decimal) -> Decimal:
    if max_sane_units <= _ZERO:
        raise ValueError("max_sane_research_cost_units must be positive")
    return _clamp_ratio((estimated_units - max_sane_units) / max_sane_units)


def _ratio_to_cap(value: Decimal, cap: Decimal) -> Decimal:
    if cap <= _ZERO:
        raise ValueError("cap must be positive")
    return _clamp_ratio(value / cap)


def _normalize_inputs(
    packets: Iterable[ResearchStrategyCandidatePrioritizationBacklogInput],
) -> tuple[ResearchStrategyCandidatePrioritizationBacklogInput, ...]:
    if isinstance(packets, (str, bytes)) or not isinstance(packets, Iterable):
        raise ValueError("packets must be an iterable")
    normalized: list[ResearchStrategyCandidatePrioritizationBacklogInput] = []
    seen_packet_ids: set[str] = set()
    for packet in packets:
        if type(packet) is not ResearchStrategyCandidatePrioritizationBacklogInput:
            raise ValueError(
                "packets must contain "
                "ResearchStrategyCandidatePrioritizationBacklogInput",
            )
        if packet.candidate_packet_id in seen_packet_ids:
            raise ValueError("candidate_packet_id values must be unique")
        seen_packet_ids.add(packet.candidate_packet_id)
        normalized.append(packet)
    return tuple(
        sorted(
            normalized,
            key=lambda packet: (
                packet.candidate_packet_id,
                packet.team_id,
                packet.category_id,
            ),
        ),
    )


def _normalize_rows(
    rows: Sequence[ResearchStrategyCandidatePrioritizationBacklogRow],
) -> tuple[ResearchStrategyCandidatePrioritizationBacklogRow, ...]:
    if isinstance(rows, (str, bytes)) or not isinstance(rows, Sequence):
        raise ValueError("rows must be a sequence")
    normalized: list[ResearchStrategyCandidatePrioritizationBacklogRow] = []
    for row in rows:
        if type(row) is not ResearchStrategyCandidatePrioritizationBacklogRow:
            raise ValueError(
                "rows must contain "
                "ResearchStrategyCandidatePrioritizationBacklogRow",
            )
        normalized.append(row)
    return tuple(sorted(normalized, key=lambda row: row.backlog_rank))


def _validate_config(
    config: ResearchStrategyCandidatePrioritizationBacklogConfig,
) -> None:
    _require_watch_below_block(
        "evidence_gap_watch_ratio",
        config.evidence_gap_watch_ratio,
        "evidence_gap_block_ratio",
        config.evidence_gap_block_ratio,
    )
    _require_watch_below_block(
        "source_freshness_watch_seconds",
        config.source_freshness_watch_seconds,
        "source_freshness_block_seconds",
        config.source_freshness_block_seconds,
    )
    _require_watch_below_block(
        "cost_sanity_gap_watch_ratio",
        config.cost_sanity_gap_watch_ratio,
        "cost_sanity_gap_block_ratio",
        config.cost_sanity_gap_block_ratio,
    )
    _require_watch_below_block(
        "domain_team_coverage_gap_watch_ratio",
        config.domain_team_coverage_gap_watch_ratio,
        "domain_team_coverage_gap_block_ratio",
        config.domain_team_coverage_gap_block_ratio,
    )
    _require_watch_below_block(
        "recheck_urgency_watch_seconds",
        config.recheck_urgency_watch_seconds,
        "recheck_urgency_block_seconds",
        config.recheck_urgency_block_seconds,
    )


def _require_watch_below_block(
    watch_name: str,
    watch_value: Decimal,
    block_name: str,
    block_value: Decimal,
) -> None:
    if block_value <= watch_value:
        raise ValueError(f"{block_name} must exceed {watch_name}")


def _validate_input(
    packet: ResearchStrategyCandidatePrioritizationBacklogInput,
) -> None:
    if packet.verified_evidence_count > packet.required_evidence_count:
        raise ValueError("verified_evidence_count must not exceed required_evidence_count")
    if packet.covered_domain_team_count > packet.required_domain_team_count:
        raise ValueError(
            "covered_domain_team_count must not exceed required_domain_team_count",
        )

def _validate_input_times(
    packets: tuple[ResearchStrategyCandidatePrioritizationBacklogInput, ...],
    generated_at: datetime,
) -> None:
    for packet in packets:
        if packet.queued_at > generated_at:
            raise ValueError("queued_at must not be after generated_at")
        if packet.last_rechecked_at is not None and packet.last_rechecked_at > generated_at:
            raise ValueError("last_rechecked_at must not be after generated_at")


def _validate_row(row: ResearchStrategyCandidatePrioritizationBacklogRow) -> None:
    if row.verified_evidence_count > row.required_evidence_count:
        raise ValueError("verified_evidence_count must not exceed required_evidence_count")
    if row.covered_domain_team_count > row.required_domain_team_count:
        raise ValueError(
            "covered_domain_team_count must not exceed required_domain_team_count",
        )
    if row.evidence_gap_ratio != _ratio_gap(
        row.required_evidence_count,
        row.verified_evidence_count,
    ):
        raise ValueError("evidence_gap_ratio must match evidence counts")
    if row.cost_sanity_gap_ratio != _cost_gap_ratio(
        row.estimated_research_cost_units,
        row.max_sane_research_cost_units,
    ):
        raise ValueError("cost_sanity_gap_ratio must match cost inputs")
    if row.domain_team_coverage_gap_ratio != _ratio_gap(
        row.required_domain_team_count,
        row.covered_domain_team_count,
    ):
        raise ValueError(
            "domain_team_coverage_gap_ratio must match domain team counts",
        )
    if row.status != _row_status(row.reason_codes):
        raise ValueError("status must match reason_codes")


def _validate_report(report: ResearchStrategyCandidatePrioritizationBacklogReport) -> None:
    if report.packet_count != _count(len(report.rows)):
        raise ValueError("packet_count must match rows")
    if report.block_packet_count != _status_count(report.rows, "block"):
        raise ValueError("block_packet_count must match rows")
    if report.watch_packet_count != _status_count(report.rows, "watch"):
        raise ValueError("watch_packet_count must match rows")
    if report.pass_packet_count != _status_count(report.rows, "pass"):
        raise ValueError("pass_packet_count must match rows")
    if report.status != _report_status(report.rows):
        raise ValueError("status must match rows")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")
    expected_ranks = tuple(_count(rank) for rank in range(1, len(report.rows) + 1))
    if tuple(row.backlog_rank for row in report.rows) != expected_ranks:
        raise ValueError("backlog_rank values must be sequential")
    if report.max_backlog_priority_score != _max_ratio(
        tuple(row.backlog_priority_score for row in report.rows),
    ):
        raise ValueError("max_backlog_priority_score must match rows")
    if report.max_evidence_gap_ratio != _max_ratio(
        tuple(row.evidence_gap_ratio for row in report.rows),
    ):
        raise ValueError("max_evidence_gap_ratio must match rows")
    if report.max_source_age_seconds != _max_decimal(
        tuple(row.source_age_seconds for row in report.rows),
    ):
        raise ValueError("max_source_age_seconds must match rows")
    if report.max_cost_sanity_gap_ratio != _max_ratio(
        tuple(row.cost_sanity_gap_ratio for row in report.rows),
    ):
        raise ValueError("max_cost_sanity_gap_ratio must match rows")
    if report.max_domain_team_coverage_gap_ratio != _max_ratio(
        tuple(row.domain_team_coverage_gap_ratio for row in report.rows),
    ):
        raise ValueError("max_domain_team_coverage_gap_ratio must match rows")
    if report.max_recheck_age_seconds != _max_decimal(
        tuple(row.recheck_age_seconds for row in report.rows),
    ):
        raise ValueError("max_recheck_age_seconds must match rows")


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in _HARD_FLAG_FIELDS:
        if getattr(value, field_name, None) is not True:
            raise ValueError(f"{field_name} must be True for {label}")


def _require_public_text(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not _PUBLIC_TEXT_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a public identifier")
    _reject_unsafe_public_string(field_name, value)
    return value


def _require_status(field_name: str, value: object) -> str:
    if type(value) is not str or value not in STATUSES:
        raise ValueError(f"{field_name} must be one of pass, watch, block")
    return value


def _require_sha256(field_name: str, value: object) -> str:
    if type(value) is not str or not _SHA256_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a lowercase sha256 digest")
    return value


def _normalize_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return _quantize(value)


def _normalize_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized < _ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _normalize_positive_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_nonnegative_decimal(field_name, value)
    if normalized <= _ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _normalize_ratio(field_name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized < _ZERO or normalized > _ONE:
        raise ValueError(f"{field_name} must be between zero and one")
    return normalized


def _normalize_reason_codes(
    field_name: str,
    reason_codes: Sequence[str],
) -> tuple[str, ...]:
    if isinstance(reason_codes, (str, bytes)) or not isinstance(reason_codes, Sequence):
        raise ValueError(f"{field_name} must be a sequence")
    normalized: list[str] = []
    for reason_code in reason_codes:
        _require_public_text("reason_code", reason_code)
        if reason_code not in _REASON_CODE_SEQUENCE:
            raise ValueError("reason_code must be supported")
        if reason_code not in normalized:
            normalized.append(reason_code)
    return tuple(
        reason_code
        for reason_code in _REASON_CODE_SEQUENCE
        if reason_code in normalized
    )


def _count(value: int) -> Decimal:
    if value < 0:
        raise ValueError("count must be nonnegative")
    return Decimal(value).quantize(_QUANT)


def _max_ratio(values: tuple[Decimal, ...]) -> Decimal:
    return _normalize_ratio("max_ratio", max(values, default=_ZERO))


def _max_decimal(values: tuple[Decimal, ...]) -> Decimal:
    return _normalize_nonnegative_decimal("max_decimal", max(values, default=_ZERO))


def _clamp_ratio(value: Decimal) -> Decimal:
    normalized = _quantize(value)
    if normalized < _ZERO:
        return _ZERO
    if normalized > _ONE:
        return _ONE
    return normalized


def _quantize(value: Decimal) -> Decimal:
    return value.quantize(_QUANT, rounding=ROUND_HALF_UP)


def _age_seconds(earlier: datetime, later: datetime) -> Decimal:
    if later < earlier:
        raise ValueError("age seconds must be nonnegative")
    delta = later - earlier
    seconds = Decimal(delta.days * 86400 + delta.seconds)
    if delta.microseconds:
        seconds += Decimal(delta.microseconds) / Decimal("1000000")
    return _quantize(seconds)


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be UTC-aware")
    if value.utcoffset() != _ZERO_TIME_OFFSET:
        raise ValueError(f"{field_name} must be UTC-aware")
    return value.astimezone(UTC)


def _as_optional_utc(field_name: str, value: object) -> datetime | None:
    if value is None:
        return None
    return _as_utc(field_name, value)


def _as_generated_at_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be UTC")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be UTC")
    if value.utcoffset() != _ZERO_TIME_OFFSET:
        raise ValueError(f"{field_name} must be UTC")
    return value.astimezone(UTC)


_ZERO_TIME_OFFSET = datetime(2026, 1, 1, tzinfo=UTC).utcoffset()


def _report_values_without_digest(
    report: ResearchStrategyCandidatePrioritizationBacklogReport,
) -> dict[str, object]:
    values = asdict(report)
    values.pop("derived_validation_digest", None)
    return values


def _report_digest_from_values(values: Mapping[str, object]) -> str:
    payload = _json_ready(values)
    if type(payload) is not dict:
        raise ValueError("digest payload must be a JSON object")
    _reject_unsafe_public_payload(
        "digest payload",
        payload,
        allow_json_containers=True,
    )
    return _digest_from_unsigned_payload(payload)


def _digest_from_payload(payload: Mapping[str, object]) -> str:
    unsigned = dict(payload)
    unsigned.pop("derived_validation_digest", None)
    return _digest_from_unsigned_payload(unsigned)


def _digest_from_unsigned_payload(payload: Mapping[str, object]) -> str:
    canonical = json.dumps(payload, separators=(",", ":"), sort_keys=True)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


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
    if type(value) is int or isinstance(value, float):
        raise ValueError("numeric payload values must be Decimal strings")
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
    if (
        value is None
        or type(value) is bool
        or type(value) is Decimal
        or type(value) is datetime
    ):
        return
    raise ValueError(f"{current_path} is not a supported public payload value")


def _reject_unsafe_public_key(key: str, path: str) -> None:
    lowered = key.lower()
    if any(term in lowered for term in _UNSAFE_PUBLIC_TERMS):
        raise ValueError(f"{path}.{key} has unsafe public field")


def _reject_unsafe_public_string(field_name: str, value: str) -> None:
    lowered = value.lower()
    if "://" in lowered or "?" in lowered or "@" in lowered:
        raise ValueError(f"{field_name} has unsafe public value")
    if any(term in lowered for term in _UNSAFE_PUBLIC_TERMS):
        raise ValueError(f"{field_name} has unsafe public value")


__all__ = (
    "DEFAULT_RESEARCH_STRATEGY_CANDIDATE_PRIORITIZATION_BACKLOG_CONFIG_VERSION",
    "STATUSES",
    "ResearchStrategyCandidatePrioritizationBacklogConfig",
    "ResearchStrategyCandidatePrioritizationBacklogInput",
    "ResearchStrategyCandidatePrioritizationBacklogReport",
    "ResearchStrategyCandidatePrioritizationBacklogRow",
    "build_research_strategy_candidate_prioritization_backlog_report",
    "research_strategy_candidate_prioritization_backlog_report_digest",
    "research_strategy_candidate_prioritization_backlog_report_payload",
)
