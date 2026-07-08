"""Pure report-only event-specific research team assignment reducer."""

from __future__ import annotations

from dataclasses import asdict, dataclass, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal
from hashlib import sha256
from typing import Any

from polymarket_alpha_lab.team_paper_guard import (
    json_ready_no_floats,
    require_paper_only_flags,
)
from polymarket_alpha_lab.team_taxonomy import TEAM_CATEGORIES, TEAM_IDS, require_team_id


DEFAULT_RESEARCH_EVENT_SPECIFIC_TEAM_ASSIGNMENT_CONFIG_VERSION = (
    "research-event-specific-team-assignment-report-v0"
)

QUANT = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")

PUBLIC_STATUSES = ("pass", "watch", "block")

NO_INPUTS_REASON = "research_event_specific_team_assignment_no_inputs"
CATEGORY_POLITICS_REASON = "research_event_specific_team_assignment_category_politics"
CATEGORY_CRYPTO_BTC_REASON = "research_event_specific_team_assignment_category_crypto_btc"
CATEGORY_CRYPTO_ETH_REASON = "research_event_specific_team_assignment_category_crypto_eth"
CATEGORY_MACRO_RATES_REASON = "research_event_specific_team_assignment_category_macro_rates"
CATEGORY_EQUITY_INDICES_REASON = (
    "research_event_specific_team_assignment_category_equity_indices"
)
CATEGORY_COMMODITIES_GOLD_REASON = (
    "research_event_specific_team_assignment_category_commodities_gold"
)
CATEGORY_COMMODITIES_OIL_REASON = (
    "research_event_specific_team_assignment_category_commodities_oil"
)
CATEGORY_SPORTS_SOCCER_REASON = (
    "research_event_specific_team_assignment_category_sports_soccer"
)
CATEGORY_SPORTS_BASKETBALL_REASON = (
    "research_event_specific_team_assignment_category_sports_basketball"
)
CATEGORY_SPORTS_OTHER_REASON = "research_event_specific_team_assignment_category_sports_other"
EVIDENCE_GAP_BLOCK_REASON = "research_event_specific_team_assignment_evidence_gap_block"
EVIDENCE_GAP_WATCH_REASON = "research_event_specific_team_assignment_evidence_gap_watch"
STALE_INFORMATION_BLOCK_REASON = (
    "research_event_specific_team_assignment_stale_information_block"
)
STALE_INFORMATION_WATCH_REASON = (
    "research_event_specific_team_assignment_stale_information_watch"
)
HIGH_TEAM_LOAD_WATCH_REASON = "research_event_specific_team_assignment_high_team_load_watch"
PASS_REASON = "research_event_specific_team_assignment_pass"
WATCH_REASON = "research_event_specific_team_assignment_watch"
BLOCK_REASON = "research_event_specific_team_assignment_block"

REASON_CODE_SEQUENCE = (
    CATEGORY_POLITICS_REASON,
    CATEGORY_CRYPTO_BTC_REASON,
    CATEGORY_CRYPTO_ETH_REASON,
    CATEGORY_MACRO_RATES_REASON,
    CATEGORY_EQUITY_INDICES_REASON,
    CATEGORY_COMMODITIES_GOLD_REASON,
    CATEGORY_COMMODITIES_OIL_REASON,
    CATEGORY_SPORTS_SOCCER_REASON,
    CATEGORY_SPORTS_BASKETBALL_REASON,
    CATEGORY_SPORTS_OTHER_REASON,
    EVIDENCE_GAP_BLOCK_REASON,
    EVIDENCE_GAP_WATCH_REASON,
    STALE_INFORMATION_BLOCK_REASON,
    STALE_INFORMATION_WATCH_REASON,
    HIGH_TEAM_LOAD_WATCH_REASON,
    NO_INPUTS_REASON,
    PASS_REASON,
    WATCH_REASON,
    BLOCK_REASON,
)

_CATEGORY_REASON_BY_ID = {
    "politics": CATEGORY_POLITICS_REASON,
    "finance.crypto.btc": CATEGORY_CRYPTO_BTC_REASON,
    "finance.crypto.eth": CATEGORY_CRYPTO_ETH_REASON,
    "finance.macro.rates": CATEGORY_MACRO_RATES_REASON,
    "finance.equity.indices": CATEGORY_EQUITY_INDICES_REASON,
    "finance.commodities.gold": CATEGORY_COMMODITIES_GOLD_REASON,
    "finance.commodities.oil": CATEGORY_COMMODITIES_OIL_REASON,
    "sports.soccer": CATEGORY_SPORTS_SOCCER_REASON,
    "sports.basketball": CATEGORY_SPORTS_BASKETBALL_REASON,
    "sports.other": CATEGORY_SPORTS_OTHER_REASON,
}


def _join_parts(*parts: str) -> str:
    return "".join(parts)


UNSAFE_PUBLIC_TEXT_FRAGMENTS = frozenset(
    (
        _join_parts("au", "th"),
        _join_parts("pri", "vate"),
        _join_parts("se", "cret"),
        _join_parts("to", "ken"),
        _join_parts("d", "sn"),
        _join_parts("ta", "ble"),
        _join_parts("mar", "ket_id"),
        _join_parts("mar", "ket_slug"),
        _join_parts("ques", "tion"),
        _join_parts("sou", "rce_ref"),
        _join_parts("sou", "rce_url"),
        _join_parts("sou", "rce_text"),
        _join_parts("raw", "_id"),
        _join_parts("raw", "-id"),
        _join_parts("raw", "-candidate"),
        _join_parts("wal", "let"),
        _join_parts("or", "der"),
        _join_parts("tra", "de"),
        _join_parts("b", "uy"),
        _join_parts("s", "ell"),
        _join_parts("pos", "ition"),
        _join_parts("rec", "ommend"),
    ),
)


@dataclass(frozen=True)
class ResearchEventSpecificTeamAssignmentConfig:
    config_version: str = DEFAULT_RESEARCH_EVENT_SPECIFIC_TEAM_ASSIGNMENT_CONFIG_VERSION
    category_fit_weight: Decimal = Decimal("0.450000")
    evidence_readiness_weight: Decimal = Decimal("0.250000")
    information_freshness_weight: Decimal = Decimal("0.200000")
    load_availability_weight: Decimal = Decimal("0.100000")
    evidence_gap_watch_threshold: Decimal = Decimal("0.500000")
    evidence_gap_block_threshold: Decimal = Decimal("0.800000")
    information_freshness_watch_threshold: Decimal = Decimal("0.500000")
    information_freshness_block_threshold: Decimal = Decimal("0.200000")
    team_load_watch_threshold: Decimal = Decimal("0.750000")
    max_support_team_count: Decimal = Decimal("2.000000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchEventSpecificTeamAssignmentConfig:
            raise TypeError(
                "ResearchEventSpecificTeamAssignmentConfig does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchEventSpecificTeamAssignmentConfig:
            raise ValueError(
                "config must be exactly ResearchEventSpecificTeamAssignmentConfig",
            )
        _require_public_string("config_version", self.config_version)
        for field_name in (
            "category_fit_weight",
            "evidence_readiness_weight",
            "information_freshness_weight",
            "load_availability_weight",
            "evidence_gap_watch_threshold",
            "evidence_gap_block_threshold",
            "information_freshness_watch_threshold",
            "information_freshness_block_threshold",
            "team_load_watch_threshold",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "max_support_team_count",
            _require_whole_nonnegative_decimal(
                "max_support_team_count",
                self.max_support_team_count,
            ),
        )
        if (
            self.category_fit_weight
            + self.evidence_readiness_weight
            + self.information_freshness_weight
            + self.load_availability_weight
        ) != ONE:
            raise ValueError("assignment weights must sum to 1.000000")
        if self.evidence_gap_watch_threshold >= self.evidence_gap_block_threshold:
            raise ValueError("evidence gap block threshold must exceed watch threshold")
        if (
            self.information_freshness_block_threshold
            >= self.information_freshness_watch_threshold
        ):
            raise ValueError("freshness watch threshold must exceed block threshold")
        require_paper_only_flags("config", self)


@dataclass(frozen=True)
class ResearchEventSpecificTeamAssignmentCandidate:
    candidate_reference: str
    event_category: str
    observed_at: datetime
    evidence_gap_score: Decimal
    information_freshness_score: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchEventSpecificTeamAssignmentCandidate:
            raise TypeError(
                "ResearchEventSpecificTeamAssignmentCandidate does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchEventSpecificTeamAssignmentCandidate:
            raise ValueError(
                "candidate must be exactly ResearchEventSpecificTeamAssignmentCandidate",
            )
        _require_private_reference("candidate_reference", self.candidate_reference)
        _require_category_id("event_category", self.event_category)
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in ("evidence_gap_score", "information_freshness_score"):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        require_paper_only_flags("candidate", self)


@dataclass(frozen=True)
class ResearchEventSpecificTeamLoad:
    team_id: str
    active_event_count: Decimal
    load_score: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchEventSpecificTeamLoad:
            raise TypeError("ResearchEventSpecificTeamLoad does not support subclassing")

    def __post_init__(self) -> None:
        if type(self) is not ResearchEventSpecificTeamLoad:
            raise ValueError("team load must be exactly ResearchEventSpecificTeamLoad")
        object.__setattr__(self, "team_id", require_team_id("team_id", self.team_id))
        object.__setattr__(
            self,
            "active_event_count",
            _require_whole_nonnegative_decimal(
                "active_event_count",
                self.active_event_count,
            ),
        )
        object.__setattr__(
            self,
            "load_score",
            _require_ratio_decimal("load_score", self.load_score),
        )
        require_paper_only_flags("team load", self)


@dataclass(frozen=True)
class ResearchEventSpecificTeamAssignmentRow:
    event_reference_digest: str
    event_category: str
    observed_at: datetime
    event_age_seconds: Decimal
    lead_team: str
    support_teams: tuple[str, ...]
    public_status: str
    category_fit_score: Decimal
    evidence_gap_score: Decimal
    evidence_readiness_score: Decimal
    information_freshness_score: Decimal
    lead_active_event_count: Decimal
    load_availability_score: Decimal
    assignment_score: Decimal
    safe_summary: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchEventSpecificTeamAssignmentRow:
            raise TypeError(
                "ResearchEventSpecificTeamAssignmentRow does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchEventSpecificTeamAssignmentRow:
            raise ValueError("row must be exactly ResearchEventSpecificTeamAssignmentRow")
        _require_digest("event_reference_digest", self.event_reference_digest)
        _require_category_id("event_category", self.event_category)
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        object.__setattr__(
            self,
            "event_age_seconds",
            _require_nonnegative_decimal("event_age_seconds", self.event_age_seconds),
        )
        object.__setattr__(self, "lead_team", require_team_id("lead_team", self.lead_team))
        object.__setattr__(
            self,
            "support_teams",
            _normalize_team_tuple("support_teams", self.support_teams),
        )
        _require_public_status("public_status", self.public_status)
        for field_name in (
            "category_fit_score",
            "evidence_gap_score",
            "evidence_readiness_score",
            "information_freshness_score",
            "load_availability_score",
            "assignment_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "lead_active_event_count",
            _require_whole_nonnegative_decimal(
                "lead_active_event_count",
                self.lead_active_event_count,
            ),
        )
        _require_public_text("safe_summary", self.safe_summary)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        _validate_row(self)
        require_paper_only_flags("row", self)


@dataclass(frozen=True)
class ResearchEventSpecificTeamAssignmentReasonCodeCount:
    reason_code: str
    count: Decimal
    event_ratio: Decimal

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchEventSpecificTeamAssignmentReasonCodeCount:
            raise TypeError(
                "ResearchEventSpecificTeamAssignmentReasonCodeCount does not support "
                "subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchEventSpecificTeamAssignmentReasonCodeCount:
            raise ValueError(
                "reason count must be exactly "
                "ResearchEventSpecificTeamAssignmentReasonCodeCount",
            )
        _require_reason_code("reason_code", self.reason_code)
        object.__setattr__(self, "count", _require_nonnegative_decimal("count", self.count))
        object.__setattr__(
            self,
            "event_ratio",
            _require_ratio_decimal("event_ratio", self.event_ratio),
        )


@dataclass(frozen=True)
class ResearchEventSpecificTeamAssignmentReport:
    generated_at: datetime
    config_version: str
    public_status: str
    input_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    average_assignment_score: Decimal
    rows: tuple[ResearchEventSpecificTeamAssignmentRow, ...]
    reason_code_counts: tuple[ResearchEventSpecificTeamAssignmentReasonCodeCount, ...]
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchEventSpecificTeamAssignmentReport:
            raise TypeError(
                "ResearchEventSpecificTeamAssignmentReport does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchEventSpecificTeamAssignmentReport:
            raise ValueError(
                "report must be exactly ResearchEventSpecificTeamAssignmentReport",
            )
        object.__setattr__(
            self,
            "generated_at",
            _as_utc("generated_at", self.generated_at),
        )
        _require_public_string("config_version", self.config_version)
        _require_public_status("public_status", self.public_status)
        for field_name in ("input_count", "pass_count", "watch_count", "block_count"):
            object.__setattr__(
                self,
                field_name,
                _require_whole_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "average_assignment_score",
            _require_ratio_decimal(
                "average_assignment_score",
                self.average_assignment_score,
            ),
        )
        object.__setattr__(self, "rows", _normalize_rows("rows", self.rows))
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(
                "reason_code_counts",
                self.reason_code_counts,
            ),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        _validate_report(self)
        require_paper_only_flags("report", self)


def build_research_event_specific_team_assignment_report(
    candidates: tuple[ResearchEventSpecificTeamAssignmentCandidate, ...],
    *,
    team_loads: tuple[ResearchEventSpecificTeamLoad, ...],
    config: ResearchEventSpecificTeamAssignmentConfig | None = None,
    generated_at: datetime,
) -> ResearchEventSpecificTeamAssignmentReport:
    cfg = config or ResearchEventSpecificTeamAssignmentConfig()
    if type(cfg) is not ResearchEventSpecificTeamAssignmentConfig:
        raise TypeError(
            "config must be exactly ResearchEventSpecificTeamAssignmentConfig",
        )
    require_paper_only_flags("config", cfg)
    generated_at_utc = _as_utc("generated_at", generated_at)
    candidate_rows = _normalize_candidates("candidates", candidates)
    load_by_team = _normalize_team_loads("team_loads", team_loads)

    if not candidate_rows:
        reason_counts = (
            ResearchEventSpecificTeamAssignmentReasonCodeCount(
                reason_code=NO_INPUTS_REASON,
                count=ONE,
                event_ratio=ZERO,
            ),
        )
        return ResearchEventSpecificTeamAssignmentReport(
            generated_at=generated_at_utc,
            config_version=cfg.config_version,
            public_status="block",
            input_count=ZERO,
            pass_count=ZERO,
            watch_count=ZERO,
            block_count=ZERO,
            average_assignment_score=ZERO,
            rows=(),
            reason_code_counts=reason_counts,
            reason_codes=(NO_INPUTS_REASON,),
        )

    rows = tuple(
        _assignment_row(
            candidate,
            load_by_team=load_by_team,
            config=cfg,
            generated_at=generated_at_utc,
        )
        for candidate in candidate_rows
    )
    sorted_rows = tuple(
        sorted(
            rows,
            key=lambda row: (
                _public_status_rank(row.public_status),
                row.event_reference_digest,
                row.event_category,
            ),
        ),
    )
    reason_counts = _reason_code_counts(sorted_rows)
    return ResearchEventSpecificTeamAssignmentReport(
        generated_at=generated_at_utc,
        config_version=cfg.config_version,
        public_status=_report_public_status(sorted_rows),
        input_count=_count_decimal(sorted_rows),
        pass_count=_sum_if(sorted_rows, lambda row: row.public_status == "pass"),
        watch_count=_sum_if(sorted_rows, lambda row: row.public_status == "watch"),
        block_count=_sum_if(sorted_rows, lambda row: row.public_status == "block"),
        average_assignment_score=_average(row.assignment_score for row in sorted_rows),
        rows=sorted_rows,
        reason_code_counts=reason_counts,
        reason_codes=tuple(item.reason_code for item in reason_counts),
    )


def research_event_specific_team_assignment_payload(report: object) -> dict[str, Any]:
    if type(report) is not ResearchEventSpecificTeamAssignmentReport:
        _reject_unsafe_public_payload(
            "research event specific team assignment report",
            report,
        )
        raise ValueError("report must be a ResearchEventSpecificTeamAssignmentReport")
    require_paper_only_flags("report", report)
    payload = json_ready_no_floats(report)
    _reject_unsafe_public_payload(
        "research event specific team assignment payload",
        payload,
    )
    if type(payload) is not dict:
        raise ValueError("payload must be a dict")
    return payload


def research_event_specific_team_assignment_digest(report: object) -> dict[str, Any]:
    payload = research_event_specific_team_assignment_payload(report)
    digest = {
        "generated_at": payload["generated_at"],
        "config_version": payload["config_version"],
        "public_status": payload["public_status"],
        "input_count": payload["input_count"],
        "pass_count": payload["pass_count"],
        "watch_count": payload["watch_count"],
        "block_count": payload["block_count"],
        "average_assignment_score": payload["average_assignment_score"],
        "row_count": str(len(payload["rows"])),
        "reason_codes": payload["reason_codes"],
        "allowed_public_statuses": ["pass", "watch", "block"],
        "paper_only": payload["paper_only"],
        "report_only": payload["report_only"],
        "readonly": payload["readonly"],
    }
    _reject_unsafe_public_payload(
        "research event specific team assignment digest",
        digest,
    )
    return digest


def _assignment_row(
    candidate: ResearchEventSpecificTeamAssignmentCandidate,
    *,
    load_by_team: dict[str, ResearchEventSpecificTeamLoad],
    config: ResearchEventSpecificTeamAssignmentConfig,
    generated_at: datetime,
) -> ResearchEventSpecificTeamAssignmentRow:
    fits, category_reason = _candidate_team_fits(candidate.event_category)
    scored = tuple(
        (
            team_id,
            fit_score,
            _team_load(team_id, load_by_team),
            _assignment_score(
                category_fit_score=fit_score,
                evidence_gap_score=candidate.evidence_gap_score,
                information_freshness_score=candidate.information_freshness_score,
                load_score=_team_load(team_id, load_by_team).load_score,
                config=config,
            ),
        )
        for team_id, fit_score in fits
    )
    lead_team, category_fit_score, lead_load, assignment_score = max(
        scored,
        key=lambda item: (item[3], item[1], _load_availability(item[2].load_score), _team_rank(item[0])),
    )
    support_teams = tuple(
        team_id
        for team_id, _fit, _load, _score in sorted(
            (item for item in scored if item[0] != lead_team),
            key=lambda item: (item[3], item[1], _load_availability(item[2].load_score), _team_rank(item[0])),
            reverse=True,
        )[: int(config.max_support_team_count)]
    )
    reason_codes = _row_reason_codes(
        category_reason=category_reason,
        evidence_gap_score=candidate.evidence_gap_score,
        information_freshness_score=candidate.information_freshness_score,
        load_score=lead_load.load_score,
        config=config,
    )
    public_status = _public_status_from_reason_codes(reason_codes)
    return ResearchEventSpecificTeamAssignmentRow(
        event_reference_digest=_digest_reference(candidate.candidate_reference),
        event_category=candidate.event_category,
        observed_at=candidate.observed_at,
        event_age_seconds=_age_seconds(generated_at, candidate.observed_at),
        lead_team=lead_team,
        support_teams=support_teams,
        public_status=public_status,
        category_fit_score=category_fit_score,
        evidence_gap_score=candidate.evidence_gap_score,
        evidence_readiness_score=_evidence_readiness(candidate.evidence_gap_score),
        information_freshness_score=candidate.information_freshness_score,
        lead_active_event_count=lead_load.active_event_count,
        load_availability_score=_load_availability(lead_load.load_score),
        assignment_score=assignment_score,
        safe_summary=_safe_summary(public_status, lead_team, candidate.event_category),
        reason_codes=reason_codes,
    )


def _candidate_team_fits(
    event_category: str,
) -> tuple[tuple[tuple[str, Decimal], ...], str]:
    if event_category == "politics":
        return (
            (("politics", ONE), ("macro_rates", Decimal("0.500000"))),
            CATEGORY_POLITICS_REASON,
        )
    if event_category == "finance.crypto.btc":
        return (
            (
                ("crypto_btc", ONE),
                ("crypto_eth", Decimal("0.750000")),
                ("macro_rates", Decimal("0.650000")),
            ),
            CATEGORY_CRYPTO_BTC_REASON,
        )
    if event_category == "finance.crypto.eth":
        return (
            (
                ("crypto_eth", ONE),
                ("crypto_btc", Decimal("0.750000")),
                ("macro_rates", Decimal("0.650000")),
            ),
            CATEGORY_CRYPTO_ETH_REASON,
        )
    if event_category == "finance.macro.rates":
        return (
            (
                ("macro_rates", ONE),
                ("equity_indices", Decimal("0.600000")),
                ("commodities_gold", Decimal("0.500000")),
            ),
            CATEGORY_MACRO_RATES_REASON,
        )
    if event_category == "finance.equity.indices":
        return (
            (
                ("equity_indices", ONE),
                ("macro_rates", Decimal("0.650000")),
                ("crypto_btc", Decimal("0.250000")),
            ),
            CATEGORY_EQUITY_INDICES_REASON,
        )
    if event_category == "finance.commodities.gold":
        return (
            (
                ("commodities_gold", ONE),
                ("macro_rates", Decimal("0.650000")),
                ("equity_indices", Decimal("0.450000")),
            ),
            CATEGORY_COMMODITIES_GOLD_REASON,
        )
    if event_category == "finance.commodities.oil":
        return (
            (
                ("commodities_oil", ONE),
                ("macro_rates", Decimal("0.600000")),
                ("commodities_gold", Decimal("0.400000")),
            ),
            CATEGORY_COMMODITIES_OIL_REASON,
        )
    if event_category == "sports.soccer":
        return (
            (
                ("sports_soccer", ONE),
                ("sports_other", Decimal("0.550000")),
                ("sports_basketball", Decimal("0.350000")),
            ),
            CATEGORY_SPORTS_SOCCER_REASON,
        )
    if event_category == "sports.basketball":
        return (
            (
                ("sports_basketball", ONE),
                ("sports_other", Decimal("0.550000")),
                ("sports_soccer", Decimal("0.350000")),
            ),
            CATEGORY_SPORTS_BASKETBALL_REASON,
        )
    return (
        (
            ("sports_other", ONE),
            ("sports_soccer", Decimal("0.400000")),
            ("sports_basketball", Decimal("0.400000")),
        ),
        CATEGORY_SPORTS_OTHER_REASON,
    )


def _assignment_score(
    *,
    category_fit_score: Decimal,
    evidence_gap_score: Decimal,
    information_freshness_score: Decimal,
    load_score: Decimal,
    config: ResearchEventSpecificTeamAssignmentConfig,
) -> Decimal:
    return _q(
        (category_fit_score * config.category_fit_weight)
        + (_evidence_readiness(evidence_gap_score) * config.evidence_readiness_weight)
        + (information_freshness_score * config.information_freshness_weight)
        + (_load_availability(load_score) * config.load_availability_weight),
    )


def _row_reason_codes(
    *,
    category_reason: str,
    evidence_gap_score: Decimal,
    information_freshness_score: Decimal,
    load_score: Decimal,
    config: ResearchEventSpecificTeamAssignmentConfig,
) -> tuple[str, ...]:
    codes = [category_reason]
    is_block = False
    is_watch = False
    if evidence_gap_score >= config.evidence_gap_block_threshold:
        codes.append(EVIDENCE_GAP_BLOCK_REASON)
        is_block = True
    elif evidence_gap_score >= config.evidence_gap_watch_threshold:
        codes.append(EVIDENCE_GAP_WATCH_REASON)
        is_watch = True
    if information_freshness_score <= config.information_freshness_block_threshold:
        codes.append(STALE_INFORMATION_BLOCK_REASON)
        is_block = True
    elif information_freshness_score <= config.information_freshness_watch_threshold:
        codes.append(STALE_INFORMATION_WATCH_REASON)
        is_watch = True
    if load_score >= config.team_load_watch_threshold:
        codes.append(HIGH_TEAM_LOAD_WATCH_REASON)
        is_watch = True
    if is_block:
        codes.append(BLOCK_REASON)
    elif is_watch:
        codes.append(WATCH_REASON)
    else:
        codes.append(PASS_REASON)
    return _normalize_reason_codes("reason_codes", tuple(codes))


def _safe_summary(public_status: str, lead_team: str, event_category: str) -> str:
    value = f"{public_status}: {lead_team} research team assigned for {event_category}"
    _require_public_text("safe_summary", value)
    return value


def _normalize_candidates(
    field_name: str,
    value: tuple[ResearchEventSpecificTeamAssignmentCandidate, ...],
) -> tuple[ResearchEventSpecificTeamAssignmentCandidate, ...]:
    if not isinstance(value, tuple):
        raise TypeError(f"{field_name} must be a tuple")
    seen: set[str] = set()
    values = []
    for item in value:
        if type(item) is not ResearchEventSpecificTeamAssignmentCandidate:
            raise ValueError(
                f"{field_name} must contain ResearchEventSpecificTeamAssignmentCandidate",
            )
        require_paper_only_flags("candidate", item)
        digest = _digest_reference(item.candidate_reference)
        if digest in seen:
            raise ValueError(f"{field_name} must not contain duplicate references")
        seen.add(digest)
        values.append(item)
    return tuple(sorted(values, key=lambda item: _digest_reference(item.candidate_reference)))


def _normalize_team_loads(
    field_name: str,
    value: tuple[ResearchEventSpecificTeamLoad, ...],
) -> dict[str, ResearchEventSpecificTeamLoad]:
    if not isinstance(value, tuple):
        raise TypeError(f"{field_name} must be a tuple")
    by_team: dict[str, ResearchEventSpecificTeamLoad] = {}
    for item in value:
        if type(item) is not ResearchEventSpecificTeamLoad:
            raise ValueError(f"{field_name} must contain ResearchEventSpecificTeamLoad")
        require_paper_only_flags("team load", item)
        if item.team_id in by_team:
            raise ValueError(f"{field_name} must contain unique teams")
        by_team[item.team_id] = item
    return by_team


def _team_load(
    team_id: str,
    load_by_team: dict[str, ResearchEventSpecificTeamLoad],
) -> ResearchEventSpecificTeamLoad:
    value = load_by_team.get(team_id)
    if value is not None:
        return value
    return ResearchEventSpecificTeamLoad(
        team_id=team_id,
        active_event_count=ZERO,
        load_score=ZERO,
    )


def _normalize_rows(
    field_name: str,
    value: tuple[ResearchEventSpecificTeamAssignmentRow, ...],
) -> tuple[ResearchEventSpecificTeamAssignmentRow, ...]:
    if not isinstance(value, tuple):
        raise TypeError(f"{field_name} must be a tuple")
    seen: set[str] = set()
    for row in value:
        if type(row) is not ResearchEventSpecificTeamAssignmentRow:
            raise ValueError(
                f"{field_name} must contain ResearchEventSpecificTeamAssignmentRow",
            )
        require_paper_only_flags("row", row)
        if row.event_reference_digest in seen:
            raise ValueError(f"{field_name} must contain unique digests")
        seen.add(row.event_reference_digest)
    return value


def _normalize_reason_code_counts(
    field_name: str,
    value: tuple[ResearchEventSpecificTeamAssignmentReasonCodeCount, ...],
) -> tuple[ResearchEventSpecificTeamAssignmentReasonCodeCount, ...]:
    if not isinstance(value, tuple):
        raise TypeError(f"{field_name} must be a tuple")
    seen: set[str] = set()
    for item in value:
        if type(item) is not ResearchEventSpecificTeamAssignmentReasonCodeCount:
            raise ValueError(
                f"{field_name} must contain ResearchEventSpecificTeamAssignmentReasonCodeCount",
            )
        if item.reason_code in seen:
            raise ValueError(f"{field_name} must contain unique reason codes")
        seen.add(item.reason_code)
    return value


def _normalize_team_tuple(field_name: str, value: tuple[str, ...]) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise TypeError(f"{field_name} must be a tuple")
    seen: set[str] = set()
    for team_id in value:
        require_team_id(field_name, team_id)
        if team_id in seen:
            raise ValueError(f"{field_name} must contain unique teams")
        seen.add(team_id)
    return value


def _normalize_reason_codes(field_name: str, value: tuple[str, ...]) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise TypeError(f"{field_name} must be a tuple")
    if not value:
        raise ValueError(f"{field_name} must not be empty")
    unique_values = frozenset(value)
    if len(unique_values) != len(value):
        raise ValueError(f"{field_name} contains duplicate reason_code values")
    for reason_code in value:
        _require_reason_code(field_name, reason_code)
    return tuple(reason_code for reason_code in REASON_CODE_SEQUENCE if reason_code in unique_values)


def _reason_code_counts(
    rows: tuple[ResearchEventSpecificTeamAssignmentRow, ...],
) -> tuple[ResearchEventSpecificTeamAssignmentReasonCodeCount, ...]:
    if not rows:
        return (
            ResearchEventSpecificTeamAssignmentReasonCodeCount(
                reason_code=NO_INPUTS_REASON,
                count=ONE,
                event_ratio=ZERO,
            ),
        )
    row_count = _count_decimal(rows)
    counts: dict[str, Decimal] = {}
    for row in rows:
        for reason_code in row.reason_codes:
            counts[reason_code] = counts.get(reason_code, ZERO) + ONE
    return tuple(
        ResearchEventSpecificTeamAssignmentReasonCodeCount(
            reason_code=reason_code,
            count=count,
            event_ratio=_ratio(count, row_count),
        )
        for reason_code, count in sorted(
            counts.items(),
            key=lambda item: REASON_CODE_SEQUENCE.index(item[0]),
        )
    )


def _report_public_status(rows: tuple[ResearchEventSpecificTeamAssignmentRow, ...]) -> str:
    if not rows:
        return "block"
    if any(row.public_status == "block" for row in rows):
        return "block"
    if any(row.public_status == "watch" for row in rows):
        return "watch"
    return "pass"


def _public_status_from_reason_codes(reason_codes: tuple[str, ...]) -> str:
    if BLOCK_REASON in reason_codes:
        return "block"
    if WATCH_REASON in reason_codes:
        return "watch"
    return "pass"


def _public_status_rank(public_status: str) -> int:
    return {"block": 0, "watch": 1, "pass": 2}[public_status]


def _evidence_readiness(evidence_gap_score: Decimal) -> Decimal:
    return _q(ONE - evidence_gap_score)


def _load_availability(load_score: Decimal) -> Decimal:
    return _q(ONE - load_score)


def _age_seconds(generated_at: datetime, observed_at: datetime) -> Decimal:
    delta = generated_at - observed_at
    value = Decimal(delta.days * 86400 + delta.seconds)
    if value < ZERO:
        raise ValueError("observed_at must be before or equal to generated_at")
    return _q(value)


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO:
        return ZERO
    return _q(numerator / denominator)


def _average(values: object) -> Decimal:
    collected = tuple(values)
    if not collected:
        return ZERO
    return _ratio(_sum_decimal(collected), Decimal(len(collected)))


def _sum_if(
    rows: tuple[ResearchEventSpecificTeamAssignmentRow, ...],
    predicate: object,
) -> Decimal:
    return _q(sum((ONE for row in rows if predicate(row)), ZERO))


def _sum_decimal(values: tuple[Decimal, ...]) -> Decimal:
    total = ZERO
    for value in values:
        total += value
    return _q(total)


def _count_decimal(values: tuple[object, ...]) -> Decimal:
    return _q(Decimal(len(values)))


def _q(value: Decimal) -> Decimal:
    return value.quantize(QUANT)


def _team_rank(team_id: str) -> Decimal:
    return _q(Decimal(len(TEAM_IDS) - TEAM_IDS.index(team_id)))


def _digest_reference(value: str) -> str:
    return f"sha256:{sha256(value.encode()).hexdigest()[:12]}"


def _as_utc(field_name: str, value: datetime) -> datetime:
    if type(value) is not datetime:
        raise TypeError(f"{field_name} must be exactly datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be UTC-aware")
    if value.microsecond != 0:
        raise ValueError(f"{field_name} must be a whole second")
    return value.astimezone(UTC)


def _require_decimal(field_name: str, value: Decimal) -> Decimal:
    if type(value) is not Decimal:
        raise TypeError(f"{field_name} must be exactly Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return value.quantize(QUANT)


def _require_nonnegative_decimal(field_name: str, value: Decimal) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return decimal_value


def _require_whole_nonnegative_decimal(field_name: str, value: Decimal) -> Decimal:
    decimal_value = _require_nonnegative_decimal(field_name, value)
    if decimal_value != decimal_value.to_integral_value():
        raise ValueError(f"{field_name} must be a whole Decimal")
    return decimal_value


def _require_ratio_decimal(field_name: str, value: Decimal) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value < ZERO or decimal_value > ONE:
        raise ValueError(f"{field_name} must be in the unit interval")
    return decimal_value


def _require_public_string(field_name: str, value: str) -> str:
    if type(value) is not str:
        raise TypeError(f"{field_name} must be exactly str")
    if not value or value != value.strip() or any(char.isspace() for char in value):
        raise ValueError(f"{field_name} must be canonical")
    return value


def _require_public_text(field_name: str, value: str) -> str:
    if type(value) is not str:
        raise TypeError(f"{field_name} must be exactly str")
    if not value or value != value.strip():
        raise ValueError(f"{field_name} must be canonical")
    lowered = value.casefold()
    if any(fragment in lowered for fragment in UNSAFE_PUBLIC_TEXT_FRAGMENTS):
        raise ValueError(f"{field_name} contains unsafe public text")
    return value


def _require_private_reference(field_name: str, value: str) -> str:
    if type(value) is not str:
        raise TypeError(f"{field_name} must be exactly str")
    if not value or value != value.strip() or any(char.isspace() for char in value):
        raise ValueError(f"{field_name} must be canonical")
    return value


def _require_category_id(field_name: str, value: str) -> str:
    _require_public_string(field_name, value)
    if value not in TEAM_CATEGORIES:
        raise ValueError(f"{field_name} must be a known event category")
    if value not in _CATEGORY_REASON_BY_ID:
        raise ValueError(f"{field_name} must be assignable")
    return value


def _require_reason_code(field_name: str, value: str) -> str:
    _require_public_string(field_name, value)
    if value not in REASON_CODE_SEQUENCE:
        raise ValueError(f"{field_name} contains unknown reason_code")
    return value


def _require_public_status(field_name: str, value: str) -> str:
    _require_public_string(field_name, value)
    if value not in PUBLIC_STATUSES:
        raise ValueError(f"{field_name} must be pass, watch, or block")
    return value


def _require_digest(field_name: str, value: str) -> str:
    _require_public_string(field_name, value)
    if not value.startswith("sha256:") or len(value) != 19:
        raise ValueError(f"{field_name} must be a short sha256 digest")
    return value


def _reject_unsafe_public_payload(label: str, value: object) -> None:
    if is_dataclass(value) and not isinstance(value, type):
        _reject_unsafe_public_payload(label, asdict(value))
        return
    if isinstance(value, dict):
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError(f"{label} keys must be strings")
            _require_public_text(f"{label} key", key)
            _reject_unsafe_public_payload(label, item)
        return
    if isinstance(value, (list, tuple)):
        for item in value:
            _reject_unsafe_public_payload(label, item)
        return
    if type(value) is str:
        _require_public_text(label, value)


def _validate_row(row: ResearchEventSpecificTeamAssignmentRow) -> None:
    if row.lead_team in row.support_teams:
        raise ValueError("lead_team must not appear in support_teams")
    expected_status = _public_status_from_reason_codes(row.reason_codes)
    if row.public_status != expected_status:
        raise ValueError("public_status must match reason_codes")
    if row.public_status == "pass" and PASS_REASON not in row.reason_codes:
        raise ValueError("pass rows must include pass reason")
    if row.public_status == "watch" and WATCH_REASON not in row.reason_codes:
        raise ValueError("watch rows must include watch reason")
    if row.public_status == "block" and BLOCK_REASON not in row.reason_codes:
        raise ValueError("block rows must include block reason")


def _validate_report(report: ResearchEventSpecificTeamAssignmentReport) -> None:
    if report.input_count != _count_decimal(report.rows):
        raise ValueError("input_count must match rows")
    if report.pass_count != _sum_if(report.rows, lambda row: row.public_status == "pass"):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _sum_if(report.rows, lambda row: row.public_status == "watch"):
        raise ValueError("watch_count must match rows")
    if report.block_count != _sum_if(report.rows, lambda row: row.public_status == "block"):
        raise ValueError("block_count must match rows")
    if report.public_status != _report_public_status(report.rows):
        raise ValueError("public_status must match rows")
    if report.average_assignment_score != _average(
        row.assignment_score for row in report.rows
    ):
        raise ValueError("average_assignment_score must match rows")
    if report.reason_codes != tuple(item.reason_code for item in report.reason_code_counts):
        raise ValueError("reason_codes must match reason_code_counts")
    if report.reason_code_counts != _reason_code_counts(report.rows):
        raise ValueError("reason_code_counts must match rows")


__all__ = (
    "DEFAULT_RESEARCH_EVENT_SPECIFIC_TEAM_ASSIGNMENT_CONFIG_VERSION",
    "ResearchEventSpecificTeamAssignmentCandidate",
    "ResearchEventSpecificTeamAssignmentConfig",
    "ResearchEventSpecificTeamAssignmentReasonCodeCount",
    "ResearchEventSpecificTeamAssignmentReport",
    "ResearchEventSpecificTeamAssignmentRow",
    "ResearchEventSpecificTeamLoad",
    "build_research_event_specific_team_assignment_report",
    "research_event_specific_team_assignment_digest",
    "research_event_specific_team_assignment_payload",
)
