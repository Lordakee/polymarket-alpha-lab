"""Pure report-only policy for routing candidate events to research domains."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation
from typing import Any


__all__ = (
    "ResearchEventDomainAssignmentCandidate",
    "ResearchEventDomainAssignmentConfig",
    "ResearchEventDomainAssignmentReasonCodeCount",
    "ResearchEventDomainAssignmentReport",
    "ResearchEventDomainAssignmentRow",
    "build_research_event_domain_assignment_report",
    "research_event_domain_assignment_report_payload",
)


DEFAULT_CONFIG_VERSION = "research-event-domain-assignment-policy-v0"

STATUS_PASS = "pass"
STATUS_WATCH = "watch"
STATUS_BLOCK = "block"
STATUSES = (STATUS_PASS, STATUS_WATCH, STATUS_BLOCK)

DOMAIN_POLITICS = "politics"
DOMAIN_BTC = "btc"
DOMAIN_STOCK_INDICES = "stock_indices"
DOMAIN_GOLD = "gold"
DOMAIN_FOOTBALL = "football"
DOMAIN_BASKETBALL = "basketball"
DOMAIN_UNASSIGNED = "unassigned"
DOMAIN_SEQUENCE = (
    DOMAIN_POLITICS,
    DOMAIN_BTC,
    DOMAIN_STOCK_INDICES,
    DOMAIN_GOLD,
    DOMAIN_FOOTBALL,
    DOMAIN_BASKETBALL,
)

TEAM_BY_DOMAIN = {
    DOMAIN_POLITICS: "politics_research_team",
    DOMAIN_BTC: "btc_research_team",
    DOMAIN_STOCK_INDICES: "stock_index_research_team",
    DOMAIN_GOLD: "gold_research_team",
    DOMAIN_FOOTBALL: "football_research_team",
    DOMAIN_BASKETBALL: "basketball_research_team",
    DOMAIN_UNASSIGNED: "manual_research_triage",
}

DOMAIN_SIGNALS = {
    DOMAIN_POLITICS: (
        "bill",
        "cabinet",
        "congress",
        "court",
        "election",
        "governor",
        "law",
        "policy",
        "poll",
        "president",
        "senate",
        "vote",
    ),
    DOMAIN_BTC: (
        "bitcoin",
        "blockchain",
        "btc",
        "crypto",
        "etf",
        "halving",
        "satoshi",
    ),
    DOMAIN_STOCK_INDICES: (
        "dow",
        "equity",
        "index",
        "nasdaq",
        "russell",
        "sp500",
        "s&p",
        "stock",
    ),
    DOMAIN_GOLD: (
        "bullion",
        "gold",
        "metals",
        "precious",
        "xau",
    ),
    DOMAIN_FOOTBALL: (
        "champions",
        "fifa",
        "football",
        "goal",
        "la_liga",
        "mls",
        "premier",
        "soccer",
        "uefa",
        "world_cup",
    ),
    DOMAIN_BASKETBALL: (
        "basketball",
        "euroleague",
        "nba",
        "ncaa_basketball",
        "rebounds",
        "wnba",
    ),
}

ZERO = Decimal("0")
ONE = Decimal("1")
RATIO_QUANTUM = Decimal("0.000001")

REASON_PREFIX = "research_event_domain_assignment_"
NO_CANDIDATES_REASON = f"{REASON_PREFIX}no_candidates"
PASS_REASON = f"{REASON_PREFIX}pass"
WATCH_REASON = f"{REASON_PREFIX}watch"
BLOCK_REASON = f"{REASON_PREFIX}block"
CLEAR_ROUTE_REASON = f"{REASON_PREFIX}clear_route"
LOW_CONFIDENCE_REASON = f"{REASON_PREFIX}low_confidence"
AMBIGUOUS_DOMAIN_REASON = f"{REASON_PREFIX}ambiguous_domain"
HIGH_AMBIGUITY_REASON = f"{REASON_PREFIX}high_ambiguity"
MANUAL_REVIEW_REASON = f"{REASON_PREFIX}manual_review_requested"
NO_DOMAIN_REASON = f"{REASON_PREFIX}no_domain_match"
DOMAIN_REASON_BY_DOMAIN = {
    domain: f"{REASON_PREFIX}domain_{domain}" for domain in DOMAIN_SEQUENCE
}

ROW_REASON_CODE_SEQUENCE = (
    BLOCK_REASON,
    WATCH_REASON,
    PASS_REASON,
    NO_DOMAIN_REASON,
    HIGH_AMBIGUITY_REASON,
    LOW_CONFIDENCE_REASON,
    AMBIGUOUS_DOMAIN_REASON,
    MANUAL_REVIEW_REASON,
    CLEAR_ROUTE_REASON,
    *tuple(DOMAIN_REASON_BY_DOMAIN[domain] for domain in DOMAIN_SEQUENCE),
)
REPORT_REASON_CODE_SEQUENCE = (
    NO_CANDIDATES_REASON,
    *ROW_REASON_CODE_SEQUENCE,
)

NO_EXTRA_REVIEW = f"{REASON_PREFIX}no_extra_review"
TEAM_LEAD_REVIEW = f"{REASON_PREFIX}team_lead_review"
CONFIRM_DOMAIN_BOUNDARY = f"{REASON_PREFIX}confirm_domain_boundary"
ADD_PUBLIC_CONTEXT = f"{REASON_PREFIX}add_public_context"
MANUAL_TRIAGE_REQUIRED = f"{REASON_PREFIX}manual_triage_required"
SUPPLY_PUBLIC_DOMAIN_SIGNAL = f"{REASON_PREFIX}supply_public_domain_signal"
RESOLVE_DOMAIN_CONFLICT = f"{REASON_PREFIX}resolve_domain_conflict"
REVIEW_REQUIREMENT_SEQUENCE = (
    MANUAL_TRIAGE_REQUIRED,
    SUPPLY_PUBLIC_DOMAIN_SIGNAL,
    RESOLVE_DOMAIN_CONFLICT,
    TEAM_LEAD_REVIEW,
    CONFIRM_DOMAIN_BOUNDARY,
    ADD_PUBLIC_CONTEXT,
    NO_EXTRA_REVIEW,
)

NEXT_STEPS = {
    STATUS_PASS: "publish_report_only_domain_routes",
    STATUS_WATCH: "queue_report_only_domain_route_review",
    STATUS_BLOCK: "hold_report_only_domain_route_assignment",
}


@dataclass(frozen=True)
class ResearchEventDomainAssignmentConfig:
    config_version: str = DEFAULT_CONFIG_VERSION
    pass_confidence_score: Decimal = Decimal("0.700000")
    watch_confidence_score: Decimal = Decimal("0.350000")
    max_pass_ambiguity_score: Decimal = Decimal("0.250000")
    block_ambiguity_score: Decimal = Decimal("0.850000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchEventDomainAssignmentConfig:
            raise TypeError(
                "ResearchEventDomainAssignmentConfig does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchEventDomainAssignmentConfig:
            raise ValueError(
                "config must be exactly ResearchEventDomainAssignmentConfig",
            )
        _require_public_text("config_version", self.config_version)
        for field_name in (
            "pass_confidence_score",
            "watch_confidence_score",
            "max_pass_ambiguity_score",
            "block_ambiguity_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        if self.pass_confidence_score <= self.watch_confidence_score:
            raise ValueError(
                "pass_confidence_score must be greater than watch_confidence_score",
            )
        if self.max_pass_ambiguity_score >= self.block_ambiguity_score:
            raise ValueError(
                "block_ambiguity_score must be greater than max_pass_ambiguity_score",
            )
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class ResearchEventDomainAssignmentCandidate:
    event_key: str
    public_title: str
    public_summary: str
    public_tags: tuple[str, ...]
    domain_confidence_score: Decimal | None = None
    ambiguity_score: Decimal | None = None
    manual_review_requested: bool = False
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchEventDomainAssignmentCandidate:
            raise TypeError(
                "ResearchEventDomainAssignmentCandidate does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchEventDomainAssignmentCandidate:
            raise ValueError(
                "candidate must be exactly ResearchEventDomainAssignmentCandidate",
            )
        for field_name in ("event_key", "public_title", "public_summary"):
            _require_public_text(field_name, getattr(self, field_name))
        object.__setattr__(
            self,
            "public_tags",
            _normalize_public_text_tuple("public_tags", self.public_tags),
        )
        object.__setattr__(
            self,
            "domain_confidence_score",
            _require_optional_ratio_decimal(
                "domain_confidence_score",
                self.domain_confidence_score,
            ),
        )
        object.__setattr__(
            self,
            "ambiguity_score",
            _require_optional_ratio_decimal("ambiguity_score", self.ambiguity_score),
        )
        if type(self.manual_review_requested) is not bool:
            raise ValueError("manual_review_requested must be a bool")
        _require_hard_flags("candidate", self)


@dataclass(frozen=True)
class ResearchEventDomainAssignmentRow:
    event_key: str
    public_title: str
    assigned_domain: str
    assigned_team: str
    policy_status: str
    domain_confidence_score: Decimal | None
    ambiguity_score: Decimal | None
    matched_signal_count: Decimal
    competing_domain_count: Decimal
    route_reasons: tuple[str, ...]
    review_requirements: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchEventDomainAssignmentRow:
            raise TypeError(
                "ResearchEventDomainAssignmentRow does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchEventDomainAssignmentRow:
            raise ValueError("row must be exactly ResearchEventDomainAssignmentRow")
        _require_public_text("event_key", self.event_key)
        _require_public_text("public_title", self.public_title)
        _require_domain("assigned_domain", self.assigned_domain)
        _require_public_text("assigned_team", self.assigned_team)
        _require_status("policy_status", self.policy_status)
        object.__setattr__(
            self,
            "domain_confidence_score",
            _require_optional_ratio_decimal(
                "domain_confidence_score",
                self.domain_confidence_score,
            ),
        )
        object.__setattr__(
            self,
            "ambiguity_score",
            _require_optional_ratio_decimal("ambiguity_score", self.ambiguity_score),
        )
        for field_name in ("matched_signal_count", "competing_domain_count"):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_whole_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "route_reasons",
            _normalize_reason_codes(
                "route_reasons",
                self.route_reasons,
                ROW_REASON_CODE_SEQUENCE,
            ),
        )
        object.__setattr__(
            self,
            "review_requirements",
            _normalize_reason_codes(
                "review_requirements",
                self.review_requirements,
                REVIEW_REQUIREMENT_SEQUENCE,
            ),
        )
        _require_hard_flags("row", self)
        _validate_row_consistency(self)


@dataclass(frozen=True)
class ResearchEventDomainAssignmentReasonCodeCount:
    reason_code: str
    count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchEventDomainAssignmentReasonCodeCount:
            raise TypeError(
                "ResearchEventDomainAssignmentReasonCodeCount does not support "
                "subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchEventDomainAssignmentReasonCodeCount:
            raise ValueError(
                "reason code count must be exactly "
                "ResearchEventDomainAssignmentReasonCodeCount",
            )
        _require_reason_code("reason_code", self.reason_code, REPORT_REASON_CODE_SEQUENCE)
        object.__setattr__(
            self,
            "count",
            _require_positive_whole_decimal("count", self.count),
        )
        _require_hard_flags("reason code count", self)


@dataclass(frozen=True)
class ResearchEventDomainAssignmentReport:
    generated_at: datetime
    config_version: str
    policy_status: str
    next_step: str
    candidate_count: Decimal
    assigned_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    review_required_count: Decimal
    rows: tuple[ResearchEventDomainAssignmentRow, ...]
    reason_code_counts: tuple[ResearchEventDomainAssignmentReasonCodeCount, ...]
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchEventDomainAssignmentReport:
            raise TypeError(
                "ResearchEventDomainAssignmentReport does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchEventDomainAssignmentReport:
            raise ValueError(
                "report must be exactly ResearchEventDomainAssignmentReport",
            )
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_text("config_version", self.config_version)
        _require_status("policy_status", self.policy_status)
        _require_public_text("next_step", self.next_step)
        for field_name in (
            "candidate_count",
            "assigned_count",
            "pass_count",
            "watch_count",
            "block_count",
            "review_required_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_whole_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(
                "reason_codes",
                self.reason_codes,
                REPORT_REASON_CODE_SEQUENCE,
            ),
        )
        _require_hard_flags("report", self)
        _validate_report_consistency(self)


def build_research_event_domain_assignment_report(
    candidates: list[ResearchEventDomainAssignmentCandidate]
    | tuple[ResearchEventDomainAssignmentCandidate, ...],
    *,
    config: ResearchEventDomainAssignmentConfig | None = None,
    generated_at: datetime,
) -> ResearchEventDomainAssignmentReport:
    cfg = config or ResearchEventDomainAssignmentConfig()
    if type(cfg) is not ResearchEventDomainAssignmentConfig:
        raise ValueError("config must be a ResearchEventDomainAssignmentConfig")
    _require_hard_flags("config", cfg)
    report_time = _as_utc("generated_at", generated_at)
    candidate_rows = _normalize_candidates(candidates)
    built_rows = tuple(_build_row(candidate, config=cfg) for candidate in candidate_rows)
    rows = _ranked_rows(built_rows)
    reason_code_counts = _reason_code_counts(rows)
    reason_codes = tuple(item.reason_code for item in reason_code_counts)
    if not rows:
        reason_code_counts = (
            ResearchEventDomainAssignmentReasonCodeCount(
                reason_code=NO_CANDIDATES_REASON,
                count=ONE,
            ),
        )
        reason_codes = (NO_CANDIDATES_REASON,)
    policy_status = _report_status(
        has_candidates=bool(rows),
        watch_count=_count(_status_count(rows, STATUS_WATCH)),
        block_count=_count(_status_count(rows, STATUS_BLOCK)),
    )
    return ResearchEventDomainAssignmentReport(
        generated_at=report_time,
        config_version=cfg.config_version,
        policy_status=policy_status,
        next_step=NEXT_STEPS[policy_status],
        candidate_count=_count(len(rows)),
        assigned_count=_count(
            sum(1 for row in rows if row.assigned_domain != DOMAIN_UNASSIGNED),
        ),
        pass_count=_count(_status_count(rows, STATUS_PASS)),
        watch_count=_count(_status_count(rows, STATUS_WATCH)),
        block_count=_count(_status_count(rows, STATUS_BLOCK)),
        review_required_count=_count(
            sum(1 for row in rows if row.review_requirements != (NO_EXTRA_REVIEW,)),
        ),
        rows=rows,
        reason_code_counts=reason_code_counts,
        reason_codes=reason_codes,
    )


def research_event_domain_assignment_report_payload(
    report: ResearchEventDomainAssignmentReport,
) -> dict[str, Any]:
    if type(report) is not ResearchEventDomainAssignmentReport:
        raise ValueError("report must be a ResearchEventDomainAssignmentReport")
    _require_hard_flags("report", report)
    payload = _json_ready(report)
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    _reject_unsafe_public_payload(payload)
    return payload


def _build_row(
    candidate: ResearchEventDomainAssignmentCandidate,
    *,
    config: ResearchEventDomainAssignmentConfig,
) -> ResearchEventDomainAssignmentRow:
    domain_matches = {
        domain: _matched_signals(candidate, domain) for domain in DOMAIN_SEQUENCE
    }
    best_domain, best_matches = _best_domain(domain_matches)
    competing_domain_count = sum(
        1
        for domain, matches in domain_matches.items()
        if domain != best_domain and matches
    )
    total_matched_signal_count = sum(len(matches) for matches in domain_matches.values())
    assigned_domain = best_domain if best_matches else DOMAIN_UNASSIGNED
    computed_confidence = (
        None
        if total_matched_signal_count == 0
        else _ratio(Decimal(len(best_matches)), Decimal(total_matched_signal_count))
    )
    domain_confidence_score = (
        candidate.domain_confidence_score
        if candidate.domain_confidence_score is not None
        else computed_confidence
    )
    ambiguity_score = (
        candidate.ambiguity_score
        if candidate.ambiguity_score is not None
        else _computed_ambiguity_score(competing_domain_count, total_matched_signal_count)
    )
    policy_status = _row_status(
        assigned_domain=assigned_domain,
        domain_confidence_score=domain_confidence_score,
        ambiguity_score=ambiguity_score,
        competing_domain_count=competing_domain_count,
        manual_review_requested=candidate.manual_review_requested,
        config=config,
    )
    route_reasons = _row_reason_codes(
        assigned_domain=assigned_domain,
        policy_status=policy_status,
        domain_confidence_score=domain_confidence_score,
        ambiguity_score=ambiguity_score,
        competing_domain_count=competing_domain_count,
        manual_review_requested=candidate.manual_review_requested,
        config=config,
    )
    review_requirements = _review_requirements(route_reasons, policy_status)
    return ResearchEventDomainAssignmentRow(
        event_key=candidate.event_key,
        public_title=candidate.public_title,
        assigned_domain=assigned_domain,
        assigned_team=TEAM_BY_DOMAIN[assigned_domain],
        policy_status=policy_status,
        domain_confidence_score=domain_confidence_score,
        ambiguity_score=ambiguity_score,
        matched_signal_count=_count(len(best_matches)),
        competing_domain_count=_count(competing_domain_count),
        route_reasons=route_reasons,
        review_requirements=review_requirements,
    )


def _normalize_candidates(
    candidates: list[ResearchEventDomainAssignmentCandidate]
    | tuple[ResearchEventDomainAssignmentCandidate, ...],
) -> tuple[ResearchEventDomainAssignmentCandidate, ...]:
    if type(candidates) not in (list, tuple):
        raise ValueError("candidates must be a list or tuple")
    normalized = tuple(candidates)
    seen: set[str] = set()
    for candidate in normalized:
        if type(candidate) is not ResearchEventDomainAssignmentCandidate:
            raise ValueError(
                "candidates must contain ResearchEventDomainAssignmentCandidate",
            )
        _require_hard_flags("candidate", candidate)
        if candidate.event_key in seen:
            raise ValueError("candidates must not contain duplicate event_key values")
        seen.add(candidate.event_key)
    return normalized


def _matched_signals(
    candidate: ResearchEventDomainAssignmentCandidate,
    domain: str,
) -> tuple[str, ...]:
    text = " ".join(
        (
            candidate.public_title.lower(),
            candidate.public_summary.lower(),
            " ".join(tag.lower() for tag in candidate.public_tags),
        ),
    )
    return tuple(
        signal for signal in DOMAIN_SIGNALS[domain] if _signal_matches(signal, text)
    )


def _signal_matches(signal: str, text: str) -> bool:
    needle = signal.replace("_", " ")
    return signal in text or needle in text


def _best_domain(
    domain_matches: dict[str, tuple[str, ...]],
) -> tuple[str, tuple[str, ...]]:
    domain = min(
        DOMAIN_SEQUENCE,
        key=lambda item: (-len(domain_matches[item]), DOMAIN_SEQUENCE.index(item)),
    )
    return domain, domain_matches[domain]


def _computed_ambiguity_score(
    competing_domain_count: int,
    total_matched_signal_count: int,
) -> Decimal | None:
    if total_matched_signal_count == 0:
        return ONE
    if competing_domain_count == 0:
        return ZERO
    return _ratio(Decimal(competing_domain_count), Decimal(len(DOMAIN_SEQUENCE)))


def _row_status(
    *,
    assigned_domain: str,
    domain_confidence_score: Decimal | None,
    ambiguity_score: Decimal | None,
    competing_domain_count: int,
    manual_review_requested: bool,
    config: ResearchEventDomainAssignmentConfig,
) -> str:
    if assigned_domain == DOMAIN_UNASSIGNED:
        return STATUS_BLOCK
    if ambiguity_score is not None and ambiguity_score >= config.block_ambiguity_score:
        return STATUS_BLOCK
    if domain_confidence_score is None:
        return STATUS_BLOCK
    if domain_confidence_score < config.watch_confidence_score:
        return STATUS_BLOCK
    if manual_review_requested:
        return STATUS_WATCH
    if domain_confidence_score < config.pass_confidence_score:
        return STATUS_WATCH
    if ambiguity_score is not None and ambiguity_score > config.max_pass_ambiguity_score:
        return STATUS_WATCH
    if competing_domain_count:
        return STATUS_WATCH
    return STATUS_PASS


def _row_reason_codes(
    *,
    assigned_domain: str,
    policy_status: str,
    domain_confidence_score: Decimal | None,
    ambiguity_score: Decimal | None,
    competing_domain_count: int,
    manual_review_requested: bool,
    config: ResearchEventDomainAssignmentConfig,
) -> tuple[str, ...]:
    reasons: set[str] = {f"{REASON_PREFIX}{policy_status}"}
    if assigned_domain == DOMAIN_UNASSIGNED:
        reasons.add(NO_DOMAIN_REASON)
    else:
        reasons.add(DOMAIN_REASON_BY_DOMAIN[assigned_domain])
    if domain_confidence_score is None or domain_confidence_score < config.pass_confidence_score:
        reasons.add(LOW_CONFIDENCE_REASON)
    if ambiguity_score is not None and ambiguity_score >= config.block_ambiguity_score:
        reasons.add(HIGH_AMBIGUITY_REASON)
    if competing_domain_count or (
        ambiguity_score is not None and ambiguity_score > config.max_pass_ambiguity_score
    ):
        reasons.add(AMBIGUOUS_DOMAIN_REASON)
    if manual_review_requested:
        reasons.add(MANUAL_REVIEW_REASON)
    if (
        assigned_domain != DOMAIN_UNASSIGNED
        and reasons == {PASS_REASON, DOMAIN_REASON_BY_DOMAIN[assigned_domain]}
    ):
        reasons.add(CLEAR_ROUTE_REASON)
    return tuple(reason for reason in ROW_REASON_CODE_SEQUENCE if reason in reasons)


def _review_requirements(
    route_reasons: tuple[str, ...],
    policy_status: str,
) -> tuple[str, ...]:
    requirements: set[str] = set()
    if policy_status == STATUS_PASS:
        requirements.add(NO_EXTRA_REVIEW)
    if policy_status == STATUS_WATCH:
        requirements.add(TEAM_LEAD_REVIEW)
    if policy_status == STATUS_BLOCK:
        requirements.add(MANUAL_TRIAGE_REQUIRED)
    if NO_DOMAIN_REASON in route_reasons:
        requirements.add(SUPPLY_PUBLIC_DOMAIN_SIGNAL)
    if AMBIGUOUS_DOMAIN_REASON in route_reasons or HIGH_AMBIGUITY_REASON in route_reasons:
        requirements.add(CONFIRM_DOMAIN_BOUNDARY)
        requirements.add(RESOLVE_DOMAIN_CONFLICT)
    if LOW_CONFIDENCE_REASON in route_reasons:
        requirements.add(ADD_PUBLIC_CONTEXT)
    return tuple(
        requirement
        for requirement in REVIEW_REQUIREMENT_SEQUENCE
        if requirement in requirements
    )


def _ranked_rows(
    rows: tuple[ResearchEventDomainAssignmentRow, ...],
) -> tuple[ResearchEventDomainAssignmentRow, ...]:
    return tuple(
        sorted(
            rows,
            key=lambda row: (
                _status_rank(row.policy_status),
                _domain_rank(row.assigned_domain),
                row.event_key,
            ),
        ),
    )


def _status_rank(value: str) -> int:
    return {STATUS_BLOCK: 0, STATUS_WATCH: 1, STATUS_PASS: 2}[value]


def _domain_rank(value: str) -> int:
    if value == DOMAIN_UNASSIGNED:
        return len(DOMAIN_SEQUENCE)
    return DOMAIN_SEQUENCE.index(value)


def _reason_code_counts(
    rows: tuple[ResearchEventDomainAssignmentRow, ...],
) -> tuple[ResearchEventDomainAssignmentReasonCodeCount, ...]:
    counts: Counter[str] = Counter()
    for row in rows:
        counts.update(row.route_reasons)
    return tuple(
        ResearchEventDomainAssignmentReasonCodeCount(
            reason_code=reason_code,
            count=_count(counts[reason_code]),
        )
        for reason_code in REPORT_REASON_CODE_SEQUENCE
        if reason_code in counts
    )


def _report_status(
    *,
    has_candidates: bool,
    watch_count: Decimal,
    block_count: Decimal,
) -> str:
    if not has_candidates or block_count > ZERO:
        return STATUS_BLOCK
    if watch_count > ZERO:
        return STATUS_WATCH
    return STATUS_PASS


def _status_count(rows: tuple[ResearchEventDomainAssignmentRow, ...], status: str) -> int:
    return sum(1 for row in rows if row.policy_status == status)


def _normalize_rows(
    rows: tuple[ResearchEventDomainAssignmentRow, ...],
) -> tuple[ResearchEventDomainAssignmentRow, ...]:
    if type(rows) is not tuple:
        raise ValueError("rows must be a tuple")
    for row in rows:
        if type(row) is not ResearchEventDomainAssignmentRow:
            raise ValueError("rows must contain ResearchEventDomainAssignmentRow values")
        _require_hard_flags("row", row)
    if rows != _ranked_rows(rows):
        raise ValueError("rows must be sorted deterministically")
    return rows


def _normalize_reason_code_counts(
    counts: tuple[ResearchEventDomainAssignmentReasonCodeCount, ...],
) -> tuple[ResearchEventDomainAssignmentReasonCodeCount, ...]:
    if type(counts) is not tuple:
        raise ValueError("reason_code_counts must be a tuple")
    for count in counts:
        if type(count) is not ResearchEventDomainAssignmentReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "ResearchEventDomainAssignmentReasonCodeCount values",
            )
        _require_hard_flags("reason code count", count)
    expected_order = tuple(
        reason_code
        for reason_code in REPORT_REASON_CODE_SEQUENCE
        if any(count.reason_code == reason_code for count in counts)
    )
    if tuple(count.reason_code for count in counts) != expected_order:
        raise ValueError("reason_code_counts must be sorted by reason code sequence")
    return counts


def _validate_row_consistency(row: ResearchEventDomainAssignmentRow) -> None:
    if row.assigned_team != TEAM_BY_DOMAIN[row.assigned_domain]:
        raise ValueError("assigned_team must match assigned_domain")
    if row.assigned_domain == DOMAIN_UNASSIGNED:
        if row.policy_status != STATUS_BLOCK:
            raise ValueError("unassigned rows must block")
        if NO_DOMAIN_REASON not in row.route_reasons:
            raise ValueError("unassigned rows must include no domain reason")
    if row.policy_status == STATUS_PASS:
        if row.domain_confidence_score is None or row.domain_confidence_score < Decimal(
            "0.700000",
        ):
            raise ValueError("domain_confidence_score must support pass status")
        if row.competing_domain_count != ZERO:
            raise ValueError("pass rows must not have competing domains")
        if row.review_requirements != (NO_EXTRA_REVIEW,):
            raise ValueError("pass rows must not require extra review")
    if row.policy_status in (STATUS_WATCH, STATUS_BLOCK):
        if row.review_requirements == (NO_EXTRA_REVIEW,):
            raise ValueError("non-pass rows must require review")
    if f"{REASON_PREFIX}{row.policy_status}" not in row.route_reasons:
        raise ValueError("route_reasons must include status reason")


def _validate_report_consistency(report: ResearchEventDomainAssignmentReport) -> None:
    if report.next_step != NEXT_STEPS[report.policy_status]:
        raise ValueError("next_step must match policy_status")
    if report.candidate_count != _count(len(report.rows)):
        raise ValueError("candidate_count must match rows")
    if report.assigned_count != _count(
        sum(1 for row in report.rows if row.assigned_domain != DOMAIN_UNASSIGNED),
    ):
        raise ValueError("assigned_count must match rows")
    if report.pass_count != _count(_status_count(report.rows, STATUS_PASS)):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _count(_status_count(report.rows, STATUS_WATCH)):
        raise ValueError("watch_count must match rows")
    if report.block_count != _count(_status_count(report.rows, STATUS_BLOCK)):
        raise ValueError("block_count must match rows")
    if report.review_required_count != _count(
        sum(1 for row in report.rows if row.review_requirements != (NO_EXTRA_REVIEW,)),
    ):
        raise ValueError("review_required_count must match rows")
    expected_counts = _reason_code_counts(report.rows)
    expected_codes = tuple(count.reason_code for count in expected_counts)
    if not report.rows:
        expected_counts = (
            ResearchEventDomainAssignmentReasonCodeCount(
                reason_code=NO_CANDIDATES_REASON,
                count=ONE,
            ),
        )
        expected_codes = (NO_CANDIDATES_REASON,)
    if report.reason_code_counts != expected_counts:
        raise ValueError("reason_code_counts must match rows")
    if report.reason_codes != expected_codes:
        raise ValueError("reason_codes must match reason_code_counts")
    expected_status = _report_status(
        has_candidates=bool(report.rows),
        watch_count=report.watch_count,
        block_count=report.block_count,
    )
    if report.policy_status != expected_status:
        raise ValueError("policy_status must match rows")


def _normalize_public_text_tuple(field_name: str, value: object) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ValueError(f"{field_name} must be a tuple")
    normalized = tuple(_require_public_text(field_name, item) for item in value)
    return tuple(sorted(set(normalized)))


def _normalize_reason_codes(
    field_name: str,
    value: object,
    allowed_values: tuple[str, ...],
) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ValueError(f"{field_name} must be a tuple")
    for reason_code in value:
        _require_reason_code(field_name, reason_code, allowed_values)
    normalized = tuple(reason_code for reason_code in allowed_values if reason_code in value)
    if normalized != value:
        raise ValueError(f"{field_name} must be unique and sorted")
    return normalized


def _require_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in STATUSES:
        raise ValueError(f"{field_name} must be a supported status")


def _require_domain(field_name: str, value: object) -> None:
    allowed = DOMAIN_SEQUENCE + (DOMAIN_UNASSIGNED,)
    if type(value) is not str or value not in allowed:
        raise ValueError(f"{field_name} must be a supported domain")


def _require_reason_code(
    field_name: str,
    value: object,
    allowed_values: tuple[str, ...],
) -> None:
    if type(value) is not str or value not in allowed_values:
        raise ValueError(f"{field_name} must be a supported reason code")


def _require_public_text(field_name: str, value: object) -> str:
    if type(value) is not str or not value.strip() or value != value.strip():
        raise ValueError(f"{field_name} must be a non-empty public string")
    _reject_unsafe_text(field_name, value)
    return value


def _reject_unsafe_text(field_name: str, value: str) -> None:
    lowered = value.lower()
    forbidden_fragments = (
        "://",
        "condition_id",
        "market_id",
        "source_id",
        "raw_id",
        "slug:",
        "token_id",
    )
    if any(fragment in lowered for fragment in forbidden_fragments):
        raise ValueError(f"{field_name} must not include private routing references")


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    try:
        return +value
    except InvalidOperation as exc:
        raise ValueError(f"{field_name} must be finite") from exc


def _require_ratio_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < ZERO or normalized > ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return _quantize(normalized)


def _require_optional_ratio_decimal(
    field_name: str,
    value: object,
) -> Decimal | None:
    if value is None:
        return None
    return _require_ratio_decimal(field_name, value)


def _require_nonnegative_whole_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{field_name} must be a whole count")
    return normalized


def _require_positive_whole_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_nonnegative_whole_decimal(field_name, value)
    if normalized <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _require_hard_flags(field_name: str, value: object) -> None:
    for flag_name in ("paper_only", "report_only", "readonly"):
        if getattr(value, flag_name, None) is not True:
            raise ValueError(f"{field_name} must be {flag_name}")


def _as_utc(field_name: str, value: datetime) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _count(value: int) -> Decimal:
    if type(value) is not int:
        raise ValueError("count value must be an int")
    if value < 0:
        raise ValueError("count value must be nonnegative")
    return Decimal(value)


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator <= ZERO:
        return ZERO
    return _quantize(numerator / denominator)


def _quantize(value: Decimal) -> Decimal:
    return value.quantize(RATIO_QUANTUM)


def _json_ready(value: object) -> object:
    if isinstance(value, Decimal):
        if not value.is_finite():
            raise ValueError("payload Decimal values must be finite")
        return str(value)
    if isinstance(value, datetime):
        return _as_utc("payload datetime", value).isoformat()
    if is_dataclass(value) and not isinstance(value, type):
        return {field.name: _json_ready(getattr(value, field.name)) for field in fields(value)}
    if isinstance(value, tuple):
        return [_json_ready(item) for item in value]
    if isinstance(value, list):
        return [_json_ready(item) for item in value]
    if isinstance(value, dict):
        return {str(key): _json_ready(item) for key, item in value.items()}
    if type(value) is float:
        raise ValueError("payload must not contain float values")
    if type(value) is int:
        raise ValueError("payload must not contain integer values")
    return value


def _reject_unsafe_public_payload(value: object) -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("payload keys must be strings")
            lowered_key = key.lower()
            if (
                "raw" in lowered_key
                or "market" in lowered_key
                or "source" in lowered_key
            ):
                raise ValueError("payload must not expose private routing fields")
            _reject_unsafe_text("payload key", key)
            _reject_unsafe_public_payload(item)
        return
    if isinstance(value, list):
        for item in value:
            _reject_unsafe_public_payload(item)
        return
    if isinstance(value, str):
        _reject_unsafe_text("payload value", value)
        return
    if isinstance(value, Decimal):
        raise ValueError("payload must serialize Decimal values")
    if type(value) is float:
        raise ValueError("payload must not contain float values")
    if type(value) is int:
        raise ValueError("payload must not contain integer values")
