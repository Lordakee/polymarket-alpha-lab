"""Pure report reducer for domain specialist roster coverage."""

from __future__ import annotations

import json
from dataclasses import InitVar, asdict, dataclass, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
from typing import Any


DEFAULT_RESEARCH_DOMAIN_SPECIALIST_TEAM_ROSTER_CONFIG_VERSION = (
    "research-domain-specialist-team-roster-v0"
)

STATUS_PASS = "pass"
STATUS_WATCH = "watch"
STATUS_BLOCK = "block"

DOMAIN_SEQUENCE = (
    "basketball",
    "soccer",
    "crypto",
    "equities",
    "gold",
    "other",
    "politics",
)

REASON_PREFIX = "research_domain_specialist_team_roster_"
ACTIVE_GAP_REASON = f"{REASON_PREFIX}active_gap"
BLOCK_GAP_REASON = f"{REASON_PREFIX}block_gap"
SPECIALIST_GAP_REASON = f"{REASON_PREFIX}specialist_gap"
SKILL_GAP_REASON = f"{REASON_PREFIX}skill_gap"
BACKLOG_PRESSURE_REASON = f"{REASON_PREFIX}backlog_pressure"
LOAD_PRESSURE_REASON = f"{REASON_PREFIX}load_pressure"
WATCH_GAP_REASON = f"{REASON_PREFIX}watch_gap"
PASS_REASON = f"{REASON_PREFIX}pass"

REASON_CODE_SEQUENCE = (
    ACTIVE_GAP_REASON,
    BLOCK_GAP_REASON,
    SPECIALIST_GAP_REASON,
    SKILL_GAP_REASON,
    BACKLOG_PRESSURE_REASON,
    LOAD_PRESSURE_REASON,
    WATCH_GAP_REASON,
    PASS_REASON,
)

NEXT_STEPS = {
    STATUS_PASS: "pass_report_only_domain_specialist_roster",
    STATUS_WATCH: "watch_report_only_domain_specialist_roster",
    STATUS_BLOCK: "block_report_only_domain_specialist_roster",
}

DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
QUANT = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")


@dataclass(frozen=True)
class ResearchDomainSpecialistTeamRosterConfig:
    config_version: str = DEFAULT_RESEARCH_DOMAIN_SPECIALIST_TEAM_ROSTER_CONFIG_VERSION
    min_specialists_per_domain: Decimal = Decimal("2")
    min_active_researchers_per_domain: Decimal = Decimal("1")
    max_assignments_per_specialist: Decimal = Decimal("4.000000")
    max_review_backlog_per_domain: Decimal = Decimal("3")
    watch_gap_threshold: Decimal = Decimal("1")
    block_gap_threshold: Decimal = Decimal("2")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchDomainSpecialistTeamRosterConfig:
            raise TypeError(
                "ResearchDomainSpecialistTeamRosterConfig does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchDomainSpecialistTeamRosterConfig:
            raise ValueError(
                "config must be exactly ResearchDomainSpecialistTeamRosterConfig",
            )
        _require_public_string("config_version", self.config_version)
        for field_name in (
            "min_specialists_per_domain",
            "min_active_researchers_per_domain",
            "max_review_backlog_per_domain",
            "watch_gap_threshold",
            "block_gap_threshold",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_count_decimal(
                    field_name,
                    getattr(self, field_name),
                ),
            )
        object.__setattr__(
            self,
            "max_assignments_per_specialist",
            _require_nonnegative_decimal(
                "max_assignments_per_specialist",
                self.max_assignments_per_specialist,
            ),
        )
        if self.watch_gap_threshold > self.block_gap_threshold:
            raise ValueError("block_gap_threshold must be at least watch_gap_threshold")
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class ResearchDomainSpecialistTeamRosterInputRow:
    team_key: str
    domain: str
    specialist_count: Decimal
    active_researcher_count: Decimal
    weekly_research_slots: Decimal
    assigned_topic_count: Decimal
    review_backlog_count: Decimal
    skill_gap_count: Decimal
    last_roster_reviewed_at: datetime
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchDomainSpecialistTeamRosterInputRow:
            raise TypeError(
                "ResearchDomainSpecialistTeamRosterInputRow does not support "
                "subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchDomainSpecialistTeamRosterInputRow:
            raise ValueError(
                "input row must be exactly ResearchDomainSpecialistTeamRosterInputRow",
            )
        _require_public_string("team_key", self.team_key)
        _require_domain("domain", self.domain)
        for field_name in (
            "specialist_count",
            "active_researcher_count",
            "assigned_topic_count",
            "review_backlog_count",
            "skill_gap_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_count_decimal(
                    field_name,
                    getattr(self, field_name),
                ),
            )
        object.__setattr__(
            self,
            "weekly_research_slots",
            _require_nonnegative_decimal(
                "weekly_research_slots",
                self.weekly_research_slots,
            ),
        )
        object.__setattr__(
            self,
            "last_roster_reviewed_at",
            _as_utc("last_roster_reviewed_at", self.last_roster_reviewed_at),
        )
        _require_hard_flags("input row", self)


@dataclass(frozen=True)
class ResearchDomainSpecialistTeamRosterRow:
    team_key: str
    domain: str
    specialist_count: Decimal
    active_researcher_count: Decimal
    weekly_research_slots: Decimal
    assigned_topic_count: Decimal
    review_backlog_count: Decimal
    skill_gap_count: Decimal
    last_roster_reviewed_at: datetime
    required_specialist_gap: Decimal
    active_researcher_gap: Decimal
    total_gap_count: Decimal
    assignments_per_specialist: Decimal
    coverage_status: str
    reassignment_hint: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True
    validation_config: InitVar[ResearchDomainSpecialistTeamRosterConfig | None] = None

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchDomainSpecialistTeamRosterRow:
            raise TypeError(
                "ResearchDomainSpecialistTeamRosterRow does not support subclassing",
            )

    def __post_init__(
        self,
        validation_config: ResearchDomainSpecialistTeamRosterConfig | None,
    ) -> None:
        if type(self) is not ResearchDomainSpecialistTeamRosterRow:
            raise ValueError("row must be exactly ResearchDomainSpecialistTeamRosterRow")
        _require_public_string("team_key", self.team_key)
        _require_domain("domain", self.domain)
        for field_name in (
            "specialist_count",
            "active_researcher_count",
            "assigned_topic_count",
            "review_backlog_count",
            "skill_gap_count",
            "required_specialist_gap",
            "active_researcher_gap",
            "total_gap_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_count_decimal(
                    field_name,
                    getattr(self, field_name),
                ),
            )
        for field_name in ("weekly_research_slots", "assignments_per_specialist"):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "last_roster_reviewed_at",
            _as_utc("last_roster_reviewed_at", self.last_roster_reviewed_at),
        )
        _require_status("coverage_status", self.coverage_status)
        _require_hint("reassignment_hint", self.reassignment_hint)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes),
        )
        _validate_row(self, config=validation_config)
        _require_hard_flags("row", self)


@dataclass(frozen=True)
class ResearchDomainSpecialistTeamRosterReasonCodeCount:
    reason_code: str
    count: Decimal
    domain_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchDomainSpecialistTeamRosterReasonCodeCount:
            raise TypeError(
                "ResearchDomainSpecialistTeamRosterReasonCodeCount does not support "
                "subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchDomainSpecialistTeamRosterReasonCodeCount:
            raise ValueError(
                "reason code count must be exactly "
                "ResearchDomainSpecialistTeamRosterReasonCodeCount",
            )
        _require_reason_code("reason_code", self.reason_code)
        object.__setattr__(
            self,
            "count",
            _require_nonnegative_count_decimal("count", self.count),
        )
        object.__setattr__(
            self,
            "domain_ratio",
            _require_ratio_decimal("domain_ratio", self.domain_ratio),
        )
        _require_hard_flags("reason code count", self)


@dataclass(frozen=True)
class ResearchDomainSpecialistTeamRosterReport:
    generated_at: datetime
    config_version: str
    roster_status: str
    next_step: str
    domain_count: Decimal
    pass_domain_count: Decimal
    watch_domain_count: Decimal
    block_domain_count: Decimal
    gap_domain_count: Decimal
    total_specialist_count: Decimal
    total_active_researcher_count: Decimal
    total_gap_count: Decimal
    average_gap_count: Decimal
    max_assignments_per_specialist_seen: Decimal
    rows: tuple[ResearchDomainSpecialistTeamRosterRow, ...]
    reason_code_counts: tuple[ResearchDomainSpecialistTeamRosterReasonCodeCount, ...]
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchDomainSpecialistTeamRosterReport:
            raise TypeError(
                "ResearchDomainSpecialistTeamRosterReport does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchDomainSpecialistTeamRosterReport:
            raise ValueError(
                "report must be exactly ResearchDomainSpecialistTeamRosterReport",
            )
        object.__setattr__(
            self,
            "generated_at",
            _as_utc("generated_at", self.generated_at),
        )
        _require_public_string("config_version", self.config_version)
        _require_status("roster_status", self.roster_status)
        _require_public_string("next_step", self.next_step)
        for field_name in (
            "domain_count",
            "pass_domain_count",
            "watch_domain_count",
            "block_domain_count",
            "gap_domain_count",
            "total_specialist_count",
            "total_active_researcher_count",
            "total_gap_count",
            "average_gap_count",
            "max_assignments_per_specialist_seen",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        if type(self.rows) is not tuple:
            raise ValueError("rows must be a tuple")
        for row in self.rows:
            if type(row) is not ResearchDomainSpecialistTeamRosterRow:
                raise ValueError(
                    "rows must contain ResearchDomainSpecialistTeamRosterRow",
                )
            _require_hard_flags("row", row)
        if type(self.reason_code_counts) is not tuple:
            raise ValueError("reason_code_counts must be a tuple")
        for row in self.reason_code_counts:
            if type(row) is not ResearchDomainSpecialistTeamRosterReasonCodeCount:
                raise ValueError(
                    "reason_code_counts must contain "
                    "ResearchDomainSpecialistTeamRosterReasonCodeCount",
                )
            _require_hard_flags("reason code count", row)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_report_reason_codes(self.reason_codes),
        )
        _validate_report(self)
        _require_hard_flags("report", self)


def build_research_domain_specialist_team_roster_report(
    input_rows: list[ResearchDomainSpecialistTeamRosterInputRow]
    | tuple[ResearchDomainSpecialistTeamRosterInputRow, ...],
    *,
    config: ResearchDomainSpecialistTeamRosterConfig | None = None,
    generated_at: datetime,
) -> ResearchDomainSpecialistTeamRosterReport:
    cfg = config or ResearchDomainSpecialistTeamRosterConfig()
    if type(cfg) is not ResearchDomainSpecialistTeamRosterConfig:
        raise ValueError("config must be a ResearchDomainSpecialistTeamRosterConfig")
    _require_hard_flags("config", cfg)
    report_time = _as_utc("generated_at", generated_at)
    inputs = _normalize_input_rows(input_rows, generated_at=report_time)
    by_domain = {row.domain: row for row in inputs}
    donor_domain = _best_donor_domain(inputs, config=cfg)
    built_rows = tuple(
        _build_row(
            by_domain.get(domain) or _empty_input_row(domain, generated_at=report_time),
            config=cfg,
            donor_domain=donor_domain,
        )
        for domain in DOMAIN_SEQUENCE
    )
    ranked_rows = _ranked_rows(built_rows)
    domain_count = _count(len(ranked_rows))
    pass_domain_count = _count(
        sum(1 for row in ranked_rows if row.coverage_status == STATUS_PASS),
    )
    watch_domain_count = _count(
        sum(1 for row in ranked_rows if row.coverage_status == STATUS_WATCH),
    )
    block_domain_count = _count(
        sum(1 for row in ranked_rows if row.coverage_status == STATUS_BLOCK),
    )
    reason_code_counts = _reason_code_counts(ranked_rows)
    roster_status = _report_status(
        block_domain_count=block_domain_count,
        watch_domain_count=watch_domain_count,
    )
    return ResearchDomainSpecialistTeamRosterReport(
        generated_at=report_time,
        config_version=cfg.config_version,
        roster_status=roster_status,
        next_step=NEXT_STEPS[roster_status],
        domain_count=domain_count,
        pass_domain_count=pass_domain_count,
        watch_domain_count=watch_domain_count,
        block_domain_count=block_domain_count,
        gap_domain_count=_count(
            sum(1 for row in ranked_rows if row.total_gap_count > ZERO),
        ),
        total_specialist_count=_sum_decimal(
            row.specialist_count for row in ranked_rows
        ),
        total_active_researcher_count=_sum_decimal(
            row.active_researcher_count for row in ranked_rows
        ),
        total_gap_count=_sum_decimal(row.total_gap_count for row in ranked_rows),
        average_gap_count=_ratio(
            _sum_decimal(row.total_gap_count for row in ranked_rows),
            domain_count,
        ),
        max_assignments_per_specialist_seen=max(
            (row.assignments_per_specialist for row in ranked_rows),
            default=ZERO,
        ),
        rows=ranked_rows,
        reason_code_counts=reason_code_counts,
        reason_codes=tuple(row.reason_code for row in reason_code_counts),
    )


def research_domain_specialist_team_roster_report_payload(
    report: ResearchDomainSpecialistTeamRosterReport,
) -> dict[str, Any]:
    if type(report) is not ResearchDomainSpecialistTeamRosterReport:
        raise ValueError(
            "report must be a ResearchDomainSpecialistTeamRosterReport",
        )
    _require_hard_flags("report", report)
    payload = _json_ready(report)
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    _require_hard_flags("payload", _DictFlags(payload))
    _reject_unsafe_payload(payload)
    return payload


def research_domain_specialist_team_roster_report_digest(
    report: ResearchDomainSpecialistTeamRosterReport,
) -> str:
    payload = research_domain_specialist_team_roster_report_payload(report)
    encoded = json.dumps(
        payload,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return sha256(encoded).hexdigest()


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


def _build_row(
    row: ResearchDomainSpecialistTeamRosterInputRow,
    *,
    config: ResearchDomainSpecialistTeamRosterConfig,
    donor_domain: str | None,
) -> ResearchDomainSpecialistTeamRosterRow:
    required_specialist_gap = _positive_gap(
        config.min_specialists_per_domain,
        row.specialist_count,
    )
    active_researcher_gap = _positive_gap(
        config.min_active_researchers_per_domain,
        row.active_researcher_count,
    )
    assignments_per_specialist = _ratio(
        row.assigned_topic_count,
        row.specialist_count,
    )
    total_gap_count = _quantize(
        required_specialist_gap + active_researcher_gap + row.skill_gap_count,
    )
    reason_codes = _row_reason_codes(
        required_specialist_gap=required_specialist_gap,
        active_researcher_gap=active_researcher_gap,
        skill_gap_count=row.skill_gap_count,
        review_backlog_count=row.review_backlog_count,
        assignments_per_specialist=assignments_per_specialist,
        config=config,
    )
    coverage_status = _row_status(reason_codes)
    return ResearchDomainSpecialistTeamRosterRow(
        team_key=row.team_key,
        domain=row.domain,
        specialist_count=row.specialist_count,
        active_researcher_count=row.active_researcher_count,
        weekly_research_slots=row.weekly_research_slots,
        assigned_topic_count=row.assigned_topic_count,
        review_backlog_count=row.review_backlog_count,
        skill_gap_count=row.skill_gap_count,
        last_roster_reviewed_at=row.last_roster_reviewed_at,
        required_specialist_gap=required_specialist_gap,
        active_researcher_gap=active_researcher_gap,
        total_gap_count=total_gap_count,
        assignments_per_specialist=assignments_per_specialist,
        coverage_status=coverage_status,
        reassignment_hint=_reassignment_hint(
            coverage_status=coverage_status,
            domain=row.domain,
            donor_domain=donor_domain,
        ),
        reason_codes=reason_codes,
        validation_config=config,
    )


def _normalize_input_rows(
    rows: list[ResearchDomainSpecialistTeamRosterInputRow]
    | tuple[ResearchDomainSpecialistTeamRosterInputRow, ...],
    *,
    generated_at: datetime,
) -> tuple[ResearchDomainSpecialistTeamRosterInputRow, ...]:
    if type(rows) not in (list, tuple):
        raise ValueError("input rows must be a list or tuple")
    normalized = tuple(rows)
    seen: set[str] = set()
    for row in normalized:
        if type(row) is not ResearchDomainSpecialistTeamRosterInputRow:
            raise ValueError(
                "input rows must contain ResearchDomainSpecialistTeamRosterInputRow",
            )
        _require_hard_flags("input row", row)
        if row.last_roster_reviewed_at > generated_at:
            raise ValueError("last_roster_reviewed_at must be on or before generated_at")
        if row.domain in seen:
            raise ValueError("input rows must not contain duplicate domains")
        seen.add(row.domain)
    return normalized


def _empty_input_row(
    domain: str,
    *,
    generated_at: datetime,
) -> ResearchDomainSpecialistTeamRosterInputRow:
    return ResearchDomainSpecialistTeamRosterInputRow(
        team_key=f"research.{domain}.specialists",
        domain=domain,
        specialist_count=ZERO,
        active_researcher_count=ZERO,
        weekly_research_slots=ZERO,
        assigned_topic_count=ZERO,
        review_backlog_count=ZERO,
        skill_gap_count=ZERO,
        last_roster_reviewed_at=generated_at,
    )


def _row_reason_codes(
    *,
    required_specialist_gap: Decimal,
    active_researcher_gap: Decimal,
    skill_gap_count: Decimal,
    review_backlog_count: Decimal,
    assignments_per_specialist: Decimal,
    config: ResearchDomainSpecialistTeamRosterConfig,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    largest_gap = max(required_specialist_gap, active_researcher_gap, skill_gap_count)
    if active_researcher_gap > ZERO:
        reason_codes.append(ACTIVE_GAP_REASON)
    if largest_gap >= config.block_gap_threshold:
        reason_codes.append(BLOCK_GAP_REASON)
    if required_specialist_gap > ZERO:
        reason_codes.append(SPECIALIST_GAP_REASON)
    if skill_gap_count > ZERO:
        reason_codes.append(SKILL_GAP_REASON)
    if review_backlog_count > config.max_review_backlog_per_domain:
        reason_codes.append(BACKLOG_PRESSURE_REASON)
    if assignments_per_specialist > config.max_assignments_per_specialist:
        reason_codes.append(LOAD_PRESSURE_REASON)
    if ZERO < largest_gap < config.block_gap_threshold:
        reason_codes.append(WATCH_GAP_REASON)
    if not reason_codes:
        reason_codes.append(PASS_REASON)
    return tuple(
        reason_code
        for reason_code in REASON_CODE_SEQUENCE
        if reason_code in reason_codes
    )


def _row_status(reason_codes: tuple[str, ...]) -> str:
    if ACTIVE_GAP_REASON in reason_codes or BLOCK_GAP_REASON in reason_codes:
        return STATUS_BLOCK
    if reason_codes == (PASS_REASON,):
        return STATUS_PASS
    return STATUS_WATCH


def _report_status(
    *,
    block_domain_count: Decimal,
    watch_domain_count: Decimal,
) -> str:
    if block_domain_count > ZERO:
        return STATUS_BLOCK
    if watch_domain_count > ZERO:
        return STATUS_WATCH
    return STATUS_PASS


def _ranked_rows(
    rows: tuple[ResearchDomainSpecialistTeamRosterRow, ...],
) -> tuple[ResearchDomainSpecialistTeamRosterRow, ...]:
    return tuple(
        sorted(
            rows,
            key=lambda row: (
                _status_rank(row.coverage_status),
                _domain_rank(row.domain),
            ),
        ),
    )


def _status_rank(value: str) -> int:
    return {STATUS_BLOCK: 0, STATUS_WATCH: 1, STATUS_PASS: 2}[value]


def _domain_rank(domain: str) -> int:
    return DOMAIN_SEQUENCE.index(domain)


def _reason_code_counts(
    rows: tuple[ResearchDomainSpecialistTeamRosterRow, ...],
) -> tuple[ResearchDomainSpecialistTeamRosterReasonCodeCount, ...]:
    total = _count(len(rows))
    counts: dict[str, Decimal] = {}
    for row in rows:
        for reason_code in row.reason_codes:
            counts[reason_code] = counts.get(reason_code, ZERO) + ONE
    return tuple(
        ResearchDomainSpecialistTeamRosterReasonCodeCount(
            reason_code=reason_code,
            count=_count(counts[reason_code]),
            domain_ratio=_ratio(counts[reason_code], total),
        )
        for reason_code in REASON_CODE_SEQUENCE
        if reason_code in counts
    )


def _best_donor_domain(
    rows: tuple[ResearchDomainSpecialistTeamRosterInputRow, ...],
    *,
    config: ResearchDomainSpecialistTeamRosterConfig,
) -> str | None:
    candidates: list[tuple[Decimal, Decimal, Decimal, str]] = []
    for row in rows:
        specialist_surplus = _positive_gap(
            row.specialist_count,
            config.min_specialists_per_domain,
        )
        active_surplus = _positive_gap(
            row.active_researcher_count,
            config.min_active_researchers_per_domain,
        )
        if specialist_surplus > ZERO:
            candidates.append(
                (
                    specialist_surplus,
                    active_surplus,
                    row.weekly_research_slots,
                    row.domain,
                ),
            )
    if not candidates:
        return None
    return max(
        candidates,
        key=lambda candidate: (
            candidate[0],
            candidate[1],
            candidate[2],
            -_domain_rank(candidate[3]),
        ),
    )[3]


def _reassignment_hint(
    *,
    coverage_status: str,
    domain: str,
    donor_domain: str | None,
) -> str:
    if coverage_status == STATUS_PASS:
        return "maintain_report_only_research_capacity"
    if donor_domain is None or donor_domain == domain:
        return "add_report_only_research_capacity"
    return f"shift_report_only_research_capacity_from_{donor_domain}_to_{domain}"


def _validate_row(
    row: ResearchDomainSpecialistTeamRosterRow,
    *,
    config: ResearchDomainSpecialistTeamRosterConfig | None,
) -> None:
    cfg = config or ResearchDomainSpecialistTeamRosterConfig()
    if type(cfg) is not ResearchDomainSpecialistTeamRosterConfig:
        raise ValueError(
            "validation_config must be a ResearchDomainSpecialistTeamRosterConfig",
        )
    expected_required_gap = _positive_gap(
        cfg.min_specialists_per_domain,
        row.specialist_count,
    )
    if row.required_specialist_gap != expected_required_gap:
        raise ValueError("required_specialist_gap must match row inputs")
    expected_active_gap = _positive_gap(
        cfg.min_active_researchers_per_domain,
        row.active_researcher_count,
    )
    if row.active_researcher_gap != expected_active_gap:
        raise ValueError("active_researcher_gap must match row inputs")
    expected_total_gap = _quantize(
        row.required_specialist_gap + row.active_researcher_gap + row.skill_gap_count,
    )
    if row.total_gap_count != expected_total_gap:
        raise ValueError("total_gap_count must match row inputs")
    expected_assignments = _ratio(row.assigned_topic_count, row.specialist_count)
    if row.assignments_per_specialist != expected_assignments:
        raise ValueError("assignments_per_specialist must match row inputs")
    expected_reason_codes = _row_reason_codes(
        required_specialist_gap=row.required_specialist_gap,
        active_researcher_gap=row.active_researcher_gap,
        skill_gap_count=row.skill_gap_count,
        review_backlog_count=row.review_backlog_count,
        assignments_per_specialist=row.assignments_per_specialist,
        config=cfg,
    )
    if row.reason_codes != expected_reason_codes:
        raise ValueError("reason_codes must match row inputs")
    if row.coverage_status != _row_status(row.reason_codes):
        raise ValueError("coverage_status must match reason_codes")


def _validate_report(report: ResearchDomainSpecialistTeamRosterReport) -> None:
    if report.next_step != NEXT_STEPS[report.roster_status]:
        raise ValueError("next_step must match roster_status")
    if report.rows != _ranked_rows(report.rows):
        raise ValueError("rows must be sorted deterministically")
    if report.domain_count != _count(len(report.rows)):
        raise ValueError("domain_count must match rows")
    if report.pass_domain_count != _count(
        sum(1 for row in report.rows if row.coverage_status == STATUS_PASS),
    ):
        raise ValueError("pass_domain_count must match rows")
    if report.watch_domain_count != _count(
        sum(1 for row in report.rows if row.coverage_status == STATUS_WATCH),
    ):
        raise ValueError("watch_domain_count must match rows")
    if report.block_domain_count != _count(
        sum(1 for row in report.rows if row.coverage_status == STATUS_BLOCK),
    ):
        raise ValueError("block_domain_count must match rows")
    if report.gap_domain_count != _count(
        sum(1 for row in report.rows if row.total_gap_count > ZERO),
    ):
        raise ValueError("gap_domain_count must match rows")
    if report.total_specialist_count != _sum_decimal(
        row.specialist_count for row in report.rows
    ):
        raise ValueError("total_specialist_count must match rows")
    if report.total_active_researcher_count != _sum_decimal(
        row.active_researcher_count for row in report.rows
    ):
        raise ValueError("total_active_researcher_count must match rows")
    if report.total_gap_count != _sum_decimal(row.total_gap_count for row in report.rows):
        raise ValueError("total_gap_count must match rows")
    if report.average_gap_count != _ratio(report.total_gap_count, report.domain_count):
        raise ValueError("average_gap_count must match rows")
    if report.max_assignments_per_specialist_seen != max(
        (row.assignments_per_specialist for row in report.rows),
        default=ZERO,
    ):
        raise ValueError("max_assignments_per_specialist_seen must match rows")
    expected_counts = _reason_code_counts(report.rows)
    if report.reason_code_counts != expected_counts:
        raise ValueError("reason_code_counts must match rows")
    if report.reason_codes != tuple(row.reason_code for row in expected_counts):
        raise ValueError("reason_codes must match reason_code_counts")
    expected_status = _report_status(
        block_domain_count=report.block_domain_count,
        watch_domain_count=report.watch_domain_count,
    )
    if report.roster_status != expected_status:
        raise ValueError("roster_status must match rows")


def _normalize_reason_codes(value: tuple[str, ...]) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ValueError("reason_codes must be a tuple")
    for reason_code in value:
        _require_reason_code("reason_codes", reason_code)
    normalized = tuple(
        reason_code for reason_code in REASON_CODE_SEQUENCE if reason_code in value
    )
    if normalized != value:
        raise ValueError("reason_codes must be unique and sorted")
    if PASS_REASON in value and len(value) != 1:
        raise ValueError("reason_codes cannot mix pass with gap reasons")
    return normalized


def _normalize_report_reason_codes(value: tuple[str, ...]) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ValueError("reason_codes must be a tuple")
    for reason_code in value:
        _require_reason_code("reason_codes", reason_code)
    normalized = tuple(
        reason_code for reason_code in REASON_CODE_SEQUENCE if reason_code in value
    )
    if normalized != value:
        raise ValueError("reason_codes must be unique and sorted")
    return normalized


def _require_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in (STATUS_PASS, STATUS_WATCH, STATUS_BLOCK):
        raise ValueError(f"{field_name} must be a supported status")


def _require_reason_code(field_name: str, value: object) -> None:
    if type(value) is not str or value not in REASON_CODE_SEQUENCE:
        raise ValueError(f"{field_name} must be a supported reason code")


def _require_domain(field_name: str, value: object) -> None:
    if type(value) is not str or value not in DOMAIN_SEQUENCE:
        raise ValueError(f"{field_name} must be a supported domain")


def _require_hint(field_name: str, value: object) -> None:
    _require_public_string(field_name, value)
    if value in (
        "maintain_report_only_research_capacity",
        "add_report_only_research_capacity",
    ):
        return
    prefix = "shift_report_only_research_capacity_from_"
    if type(value) is str and value.startswith(prefix):
        rest = value.removeprefix(prefix)
        parts = rest.split("_to_")
        if len(parts) == 2 and parts[0] in DOMAIN_SEQUENCE and parts[1] in DOMAIN_SEQUENCE:
            return
    raise ValueError(f"{field_name} must be a supported report-only hint")


def _require_public_string(field_name: str, value: object) -> str:
    if type(value) is not str or not value.strip() or value != value.strip():
        raise ValueError(f"{field_name} must be a non-empty string")
    _reject_unsafe_text(field_name, value)
    return value


def _require_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal or not value.is_finite() or value < ZERO:
        raise ValueError(f"{field_name} must be a nonnegative Decimal")
    return _quantize(value)


def _require_nonnegative_count_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_nonnegative_decimal(field_name, value)
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{field_name} must be a whole-count Decimal")
    return normalized


def _require_ratio_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_nonnegative_decimal(field_name, value)
    if normalized > ONE:
        raise ValueError(f"{field_name} must be a Decimal ratio")
    return normalized


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime or value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be a timezone-aware datetime")
    return value.astimezone(UTC)


def _require_hard_flags(field_name: str, value: object) -> None:
    for flag_name in ("paper_only", "report_only", "readonly"):
        if getattr(value, flag_name, None) is not True:
            raise ValueError(f"{field_name} must be {flag_name}")


def _positive_gap(required_value: Decimal, actual_value: Decimal) -> Decimal:
    gap = required_value - actual_value
    if gap <= ZERO:
        return ZERO
    return _quantize(gap)


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return _quantize(numerator / denominator)


def _sum_decimal(values: Any) -> Decimal:
    total = ZERO
    for value in values:
        total += value
    return _quantize(total)


def _count(value: object) -> Decimal:
    if type(value) is int:
        return _quantize(Decimal(value))
    return _require_nonnegative_count_decimal("count", value)


def _quantize(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(QUANT)


def _json_ready(value: Any) -> Any:
    if is_dataclass(value) and not isinstance(value, type):
        return _json_ready(asdict(value))
    if value is None:
        return None
    if isinstance(value, Decimal):
        if type(value) is not Decimal or not value.is_finite():
            raise ValueError("payload Decimal values must be finite")
        return str(value)
    if isinstance(value, datetime):
        return _as_utc("payload datetime", value).isoformat()
    if type(value) is str or type(value) is bool:
        return value
    if type(value) is int or type(value) is float:
        raise ValueError("payload numeric values must use Decimal strings")
    if isinstance(value, dict):
        ready: dict[str, Any] = {}
        for item_key, item_value in value.items():
            if type(item_key) is not str:
                raise ValueError("payload keys must be strings")
            ready[item_key] = _json_ready(item_value)
        return ready
    if isinstance(value, (list, tuple)):
        return [_json_ready(item) for item in value]
    raise ValueError("payload values must be JSON serializable")


def _reject_unsafe_payload(value: Any) -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            _reject_unsafe_text("payload key", key)
            _reject_unsafe_payload(item)
        return
    if isinstance(value, list):
        for item in value:
            _reject_unsafe_payload(item)
        return
    if type(value) is str:
        _reject_unsafe_text("payload value", value)
        return
    if type(value) is int and not isinstance(value, bool):
        raise ValueError("payload must not contain integer values")
    if type(value) is float or isinstance(value, Decimal):
        raise ValueError("payload must serialize numeric values")


def _reject_unsafe_text(field_name: str, value: str) -> None:
    lowered = value.lower()
    unsafe_fragments = (
        "wal" + "let",
        "au" + "th",
        "bro" + "ker",
        "ord" + "er",
        "sign" + "ing",
        "private" + "_" + "key",
        "api" + "_" + "key",
        "sec" + "ret",
        "cre" + "dential",
        "pos" + "ition",
        "tra" + "de",
        "b" + "et",
        "sta" + "ke",
        "ht" + "tp",
        "sock" + "et",
        "data" + "base",
    )
    for fragment in unsafe_fragments:
        if fragment in lowered:
            raise ValueError(f"{field_name} must not include unsafe text")
    if "://" in lowered:
        raise ValueError(f"{field_name} must not include external references")
