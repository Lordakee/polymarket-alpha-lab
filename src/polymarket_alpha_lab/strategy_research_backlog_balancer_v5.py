"""Pure paper/report research backlog balancer v5."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any

from polymarket_alpha_lab.team_paper_guard import (
    json_ready_no_floats,
    reject_unsafe_surface_fields,
    require_paper_only_flags,
)
from polymarket_alpha_lab.team_taxonomy import require_category_id, require_team_id


DEFAULT_STRATEGY_RESEARCH_BACKLOG_BALANCER_V5_CONFIG_VERSION = (
    "strategy_research_backlog_balancer_v5.1"
)

RESEARCH_BUCKETS = frozenset(("research_now", "research_later", "defer", "drop"))
DECIMAL_QUANTUM = Decimal("0.0001")
ZERO = Decimal("0")
ONE = Decimal("1")


@dataclass(frozen=True)
class StrategyResearchBacklogBalancerV5Config:
    config_version: str = DEFAULT_STRATEGY_RESEARCH_BACKLOG_BALANCER_V5_CONFIG_VERSION
    min_market_ev: Decimal = Decimal("0.0500")
    min_source_freshness_score: Decimal = Decimal("0.4000")
    research_now_score_threshold: Decimal = Decimal("1.0000")
    research_later_score_threshold: Decimal = Decimal("0.5000")
    market_ev_weight: Decimal = Decimal("2.0000")
    source_freshness_weight: Decimal = Decimal("0.2500")
    deadline_pressure_weight: Decimal = Decimal("0.4000")
    team_specialization_weight: Decimal = Decimal("0.2500")
    empty_backlog_bonus: Decimal = Decimal("0.1750")
    research_now_capacity_full_penalty: Decimal = Decimal("0.1075")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("config_version", self.config_version)
        for field_name in (
            "min_market_ev",
            "min_source_freshness_score",
            "research_now_score_threshold",
            "research_later_score_threshold",
            "market_ev_weight",
            "source_freshness_weight",
            "deadline_pressure_weight",
            "team_specialization_weight",
            "empty_backlog_bonus",
            "research_now_capacity_full_penalty",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        if self.research_now_score_threshold < self.research_later_score_threshold:
            raise ValueError(
                "research_now_score_threshold must be at least research_later_score_threshold",
            )
        require_paper_only_flags("StrategyResearchBacklogBalancerV5Config", self)


@dataclass(frozen=True)
class StrategyResearchBacklogTeamStateV5:
    team_id: str
    backlog_item_count: Decimal
    backlog_capacity_count: Decimal
    active_research_now_count: Decimal
    max_research_now_count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "team_id", require_team_id("team_id", self.team_id))
        for field_name in (
            "backlog_item_count",
            "backlog_capacity_count",
            "active_research_now_count",
            "max_research_now_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        if self.backlog_capacity_count <= ZERO:
            raise ValueError("backlog_capacity_count must be positive")
        if self.max_research_now_count <= ZERO:
            raise ValueError("max_research_now_count must be positive")
        if self.active_research_now_count > self.max_research_now_count:
            raise ValueError(
                "active_research_now_count must not exceed max_research_now_count",
            )
        require_paper_only_flags("StrategyResearchBacklogTeamStateV5", self)


@dataclass(frozen=True)
class StrategyResearchBacklogTeamSpecializationV5:
    team_id: str
    specialization_score: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "team_id", require_team_id("team_id", self.team_id))
        object.__setattr__(
            self,
            "specialization_score",
            _require_unit_interval_decimal(
                "specialization_score",
                self.specialization_score,
            ),
        )
        require_paper_only_flags("StrategyResearchBacklogTeamSpecializationV5", self)


@dataclass(frozen=True)
class StrategyResearchBacklogCandidateV5:
    market_slug: str
    question: str
    category_id: str
    market_ev: Decimal
    source_freshness_score: Decimal
    deadline_pressure_score: Decimal
    team_specializations: tuple[StrategyResearchBacklogTeamSpecializationV5, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("market_slug", self.market_slug)
        _require_nonempty_string("question", self.question)
        object.__setattr__(
            self,
            "category_id",
            require_category_id("category_id", self.category_id),
        )
        object.__setattr__(
            self,
            "market_ev",
            _require_nonnegative_decimal("market_ev", self.market_ev),
        )
        for field_name in ("source_freshness_score", "deadline_pressure_score"):
            object.__setattr__(
                self,
                field_name,
                _require_unit_interval_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "team_specializations",
            _normalize_specializations(self.team_specializations),
        )
        require_paper_only_flags("StrategyResearchBacklogCandidateV5", self)


@dataclass(frozen=True)
class StrategyResearchBacklogBalancerV5Row:
    market_slug: str
    question: str
    category_id: str
    research_bucket: str
    owner_team: str
    priority_score: Decimal
    market_ev: Decimal
    source_freshness_score: Decimal
    deadline_pressure_score: Decimal
    owner_specialization_score: Decimal
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("market_slug", self.market_slug)
        _require_nonempty_string("question", self.question)
        object.__setattr__(
            self,
            "category_id",
            require_category_id("category_id", self.category_id),
        )
        if type(self.research_bucket) is not str or self.research_bucket not in RESEARCH_BUCKETS:
            raise ValueError("research_bucket must be a known research bucket")
        object.__setattr__(self, "owner_team", require_team_id("owner_team", self.owner_team))
        for field_name in (
            "priority_score",
            "market_ev",
            "source_freshness_score",
            "deadline_pressure_score",
            "owner_specialization_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes),
        )
        require_paper_only_flags("StrategyResearchBacklogBalancerV5Row", self)


@dataclass(frozen=True)
class StrategyResearchBacklogBalancerV5Report:
    generated_at: datetime
    config_version: str
    candidate_count: Decimal
    research_now_count: Decimal
    research_later_count: Decimal
    defer_count: Decimal
    drop_count: Decimal
    top_priority_score: Decimal
    average_priority_score: Decimal
    research_now: tuple[StrategyResearchBacklogBalancerV5Row, ...]
    research_later: tuple[StrategyResearchBacklogBalancerV5Row, ...]
    defer: tuple[StrategyResearchBacklogBalancerV5Row, ...]
    drop: tuple[StrategyResearchBacklogBalancerV5Row, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        for field_name in (
            "candidate_count",
            "research_now_count",
            "research_later_count",
            "defer_count",
            "drop_count",
            "top_priority_score",
            "average_priority_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in ("research_now", "research_later", "defer", "drop"):
            object.__setattr__(
                self,
                field_name,
                _normalize_rows(getattr(self, field_name)),
            )
        if self.candidate_count != _decimal_len(self.all_rows):
            raise ValueError("candidate_count must equal total row count")
        if self.research_now_count != _decimal_len(self.research_now):
            raise ValueError("research_now_count must equal research_now row count")
        if self.research_later_count != _decimal_len(self.research_later):
            raise ValueError("research_later_count must equal research_later row count")
        if self.defer_count != _decimal_len(self.defer):
            raise ValueError("defer_count must equal defer row count")
        if self.drop_count != _decimal_len(self.drop):
            raise ValueError("drop_count must equal drop row count")
        require_paper_only_flags("StrategyResearchBacklogBalancerV5Report", self)

    @property
    def all_rows(self) -> tuple[StrategyResearchBacklogBalancerV5Row, ...]:
        return self.research_now + self.research_later + self.defer + self.drop


def build_strategy_research_backlog_balancer_v5_report(
    candidates: tuple[StrategyResearchBacklogCandidateV5, ...]
    | list[StrategyResearchBacklogCandidateV5],
    *,
    team_backlogs: tuple[StrategyResearchBacklogTeamStateV5, ...]
    | list[StrategyResearchBacklogTeamStateV5],
    config: StrategyResearchBacklogBalancerV5Config,
    generated_at: datetime,
) -> StrategyResearchBacklogBalancerV5Report:
    if type(config) is not StrategyResearchBacklogBalancerV5Config:
        raise ValueError("config must be a StrategyResearchBacklogBalancerV5Config")
    require_paper_only_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    normalized_candidates = _normalize_candidates(candidates)
    team_backlogs_by_id = _team_backlogs_by_id(team_backlogs)

    rows = tuple(
        sorted(
            (
                _balanced_row(
                    candidate,
                    team_backlogs_by_id=team_backlogs_by_id,
                    config=config,
                )
                for candidate in normalized_candidates
            ),
            key=_row_sort_key,
        ),
    )

    research_now = tuple(row for row in rows if row.research_bucket == "research_now")
    research_later = tuple(row for row in rows if row.research_bucket == "research_later")
    defer = tuple(row for row in rows if row.research_bucket == "defer")
    drop = tuple(row for row in rows if row.research_bucket == "drop")

    return StrategyResearchBacklogBalancerV5Report(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        candidate_count=_decimal_len(rows),
        research_now_count=_decimal_len(research_now),
        research_later_count=_decimal_len(research_later),
        defer_count=_decimal_len(defer),
        drop_count=_decimal_len(drop),
        top_priority_score=_top_priority_score(rows),
        average_priority_score=_average_priority_score(rows),
        research_now=research_now,
        research_later=research_later,
        defer=defer,
        drop=drop,
    )


def strategy_research_backlog_balancer_v5_payload(value: object) -> dict[str, Any]:
    if isinstance(
        value,
        (
            StrategyResearchBacklogBalancerV5Report,
            StrategyResearchBacklogBalancerV5Row,
            StrategyResearchBacklogCandidateV5,
            StrategyResearchBacklogTeamSpecializationV5,
            StrategyResearchBacklogTeamStateV5,
            StrategyResearchBacklogBalancerV5Config,
        ),
    ):
        require_paper_only_flags("strategy research backlog balancer v5 payload", value)
    elif not isinstance(value, dict):
        raise ValueError(
            "value must be a strategy research backlog balancer v5 report, row, input, or JSON object",
        )

    reject_unsafe_surface_fields("strategy research backlog balancer v5 payload", value)
    payload = json_ready_no_floats(value)
    if not isinstance(payload, dict):
        raise ValueError("strategy research backlog balancer v5 payload must be a JSON object")
    _require_payload_flags(payload)
    reject_unsafe_surface_fields("strategy research backlog balancer v5 payload", payload)
    return payload


def _balanced_row(
    candidate: StrategyResearchBacklogCandidateV5,
    *,
    team_backlogs_by_id: dict[str, StrategyResearchBacklogTeamStateV5],
    config: StrategyResearchBacklogBalancerV5Config,
) -> StrategyResearchBacklogBalancerV5Row:
    owner_specialization = _owner_specialization(candidate.team_specializations)
    if owner_specialization.team_id not in team_backlogs_by_id:
        raise ValueError("team_backlogs must include every owner team")
    team_state = team_backlogs_by_id[owner_specialization.team_id]
    priority_score = _priority_score(
        candidate,
        owner_specialization=owner_specialization,
        team_state=team_state,
        config=config,
    )
    research_bucket, reason_codes = _research_bucket_and_reasons(
        candidate,
        owner_specialization=owner_specialization,
        team_state=team_state,
        priority_score=priority_score,
        config=config,
    )
    return StrategyResearchBacklogBalancerV5Row(
        market_slug=candidate.market_slug,
        question=candidate.question,
        category_id=candidate.category_id,
        research_bucket=research_bucket,
        owner_team=owner_specialization.team_id,
        priority_score=priority_score,
        market_ev=candidate.market_ev,
        source_freshness_score=candidate.source_freshness_score,
        deadline_pressure_score=candidate.deadline_pressure_score,
        owner_specialization_score=owner_specialization.specialization_score,
        reason_codes=reason_codes,
    )


def _priority_score(
    candidate: StrategyResearchBacklogCandidateV5,
    *,
    owner_specialization: StrategyResearchBacklogTeamSpecializationV5,
    team_state: StrategyResearchBacklogTeamStateV5,
    config: StrategyResearchBacklogBalancerV5Config,
) -> Decimal:
    score = (
        (candidate.market_ev * config.market_ev_weight)
        + (candidate.source_freshness_score * config.source_freshness_weight)
        + (candidate.deadline_pressure_score * config.deadline_pressure_weight)
        + (owner_specialization.specialization_score * config.team_specialization_weight)
    )
    if team_state.backlog_item_count == ZERO:
        score += config.empty_backlog_bonus
    if team_state.active_research_now_count >= team_state.max_research_now_count:
        score -= config.research_now_capacity_full_penalty
    if score < ZERO:
        return ZERO.quantize(DECIMAL_QUANTUM)
    return score.quantize(DECIMAL_QUANTUM)


def _research_bucket_and_reasons(
    candidate: StrategyResearchBacklogCandidateV5,
    *,
    owner_specialization: StrategyResearchBacklogTeamSpecializationV5,
    team_state: StrategyResearchBacklogTeamStateV5,
    priority_score: Decimal,
    config: StrategyResearchBacklogBalancerV5Config,
) -> tuple[str, tuple[str, ...]]:
    if candidate.market_ev < config.min_market_ev:
        return "drop", ("market_ev_below_threshold", "drop_low_ev")
    if candidate.source_freshness_score < config.min_source_freshness_score:
        return "defer", (
            "source_freshness_below_threshold",
            "defer_until_sources_refresh",
        )

    reason_codes = _positive_reason_codes(
        candidate,
        owner_specialization=owner_specialization,
        team_state=team_state,
    )
    if team_state.active_research_now_count >= team_state.max_research_now_count:
        reason_codes = reason_codes + ("team_research_now_capacity_full",)
    if team_state.backlog_item_count >= team_state.backlog_capacity_count:
        reason_codes = reason_codes + ("team_backlog_capacity_full",)

    if (
        priority_score >= config.research_now_score_threshold
        and team_state.active_research_now_count < team_state.max_research_now_count
        and team_state.backlog_item_count < team_state.backlog_capacity_count
    ):
        return "research_now", reason_codes
    if priority_score >= config.research_later_score_threshold:
        return "research_later", reason_codes + ("research_later_threshold_met",)
    return "defer", reason_codes + ("priority_score_below_research_later_threshold",)


def _positive_reason_codes(
    candidate: StrategyResearchBacklogCandidateV5,
    *,
    owner_specialization: StrategyResearchBacklogTeamSpecializationV5,
    team_state: StrategyResearchBacklogTeamStateV5,
) -> tuple[str, ...]:
    reason_codes = [
        "high_market_ev",
        "fresh_sources",
    ]
    if candidate.deadline_pressure_score >= Decimal("0.7000"):
        reason_codes.append("deadline_pressure")
    if owner_specialization.specialization_score >= Decimal("0.7000"):
        reason_codes.append("team_specialization_fit")
    if team_state.backlog_item_count < team_state.backlog_capacity_count:
        reason_codes.append("team_backlog_capacity_available")
    return tuple(reason_codes)


def _owner_specialization(
    specializations: tuple[StrategyResearchBacklogTeamSpecializationV5, ...],
) -> StrategyResearchBacklogTeamSpecializationV5:
    return sorted(
        specializations,
        key=lambda row: (-row.specialization_score, row.team_id),
    )[0]


def _normalize_candidates(
    candidates: tuple[StrategyResearchBacklogCandidateV5, ...]
    | list[StrategyResearchBacklogCandidateV5],
) -> tuple[StrategyResearchBacklogCandidateV5, ...]:
    if type(candidates) not in (list, tuple):
        raise ValueError("candidates must be a list or tuple")
    normalized = tuple(candidates)
    seen_market_slugs: set[str] = set()
    for candidate in normalized:
        if type(candidate) is not StrategyResearchBacklogCandidateV5:
            raise ValueError("candidates must contain StrategyResearchBacklogCandidateV5")
        require_paper_only_flags("candidate", candidate)
        if candidate.market_slug in seen_market_slugs:
            raise ValueError("market_slug values must be unique")
        seen_market_slugs.add(candidate.market_slug)
    return normalized


def _team_backlogs_by_id(
    team_backlogs: tuple[StrategyResearchBacklogTeamStateV5, ...]
    | list[StrategyResearchBacklogTeamStateV5],
) -> dict[str, StrategyResearchBacklogTeamStateV5]:
    if type(team_backlogs) not in (list, tuple):
        raise ValueError("team_backlogs must be a list or tuple")
    by_id: dict[str, StrategyResearchBacklogTeamStateV5] = {}
    for team_state in tuple(team_backlogs):
        if type(team_state) is not StrategyResearchBacklogTeamStateV5:
            raise ValueError("team_backlogs must contain StrategyResearchBacklogTeamStateV5")
        require_paper_only_flags("team_state", team_state)
        if team_state.team_id in by_id:
            raise ValueError("team_id values must be unique")
        by_id[team_state.team_id] = team_state
    return by_id


def _normalize_specializations(
    specializations: tuple[StrategyResearchBacklogTeamSpecializationV5, ...],
) -> tuple[StrategyResearchBacklogTeamSpecializationV5, ...]:
    if type(specializations) is not tuple or not specializations:
        raise ValueError("team_specializations must be a non-empty tuple")
    normalized = tuple(specializations)
    seen_team_ids: set[str] = set()
    for specialization in normalized:
        if type(specialization) is not StrategyResearchBacklogTeamSpecializationV5:
            raise ValueError(
                "team_specializations must contain StrategyResearchBacklogTeamSpecializationV5",
            )
        require_paper_only_flags("team_specialization", specialization)
        if specialization.team_id in seen_team_ids:
            raise ValueError("team_specialization team_id values must be unique")
        seen_team_ids.add(specialization.team_id)
    return tuple(
        sorted(
            normalized,
            key=lambda row: (-row.specialization_score, row.team_id),
        ),
    )


def _normalize_rows(
    rows: tuple[StrategyResearchBacklogBalancerV5Row, ...],
) -> tuple[StrategyResearchBacklogBalancerV5Row, ...]:
    if type(rows) is not tuple:
        raise ValueError("rows must be tuples")
    for row in rows:
        if type(row) is not StrategyResearchBacklogBalancerV5Row:
            raise ValueError("rows must contain StrategyResearchBacklogBalancerV5Row")
        require_paper_only_flags("row", row)
    return tuple(sorted(rows, key=_row_sort_key))


def _normalize_reason_codes(reason_codes: tuple[str, ...]) -> tuple[str, ...]:
    if type(reason_codes) is not tuple or not reason_codes:
        raise ValueError("reason_codes must be a non-empty tuple")
    for reason_code in reason_codes:
        _require_canonical_string("reason_code", reason_code)
    return reason_codes


def _row_sort_key(row: StrategyResearchBacklogBalancerV5Row) -> tuple[int, Decimal, str]:
    bucket_weight = {
        "research_now": 0,
        "research_later": 1,
        "defer": 2,
        "drop": 3,
    }[row.research_bucket]
    return (bucket_weight, -row.priority_score, row.market_slug)


def _top_priority_score(
    rows: tuple[StrategyResearchBacklogBalancerV5Row, ...],
) -> Decimal:
    if not rows:
        return ZERO.quantize(DECIMAL_QUANTUM)
    return max(row.priority_score for row in rows).quantize(DECIMAL_QUANTUM)


def _average_priority_score(
    rows: tuple[StrategyResearchBacklogBalancerV5Row, ...],
) -> Decimal:
    if not rows:
        return ZERO.quantize(DECIMAL_QUANTUM)
    return (
        sum((row.priority_score for row in rows), ZERO) / _decimal_len(rows)
    ).quantize(DECIMAL_QUANTUM)


def _decimal_len(values: tuple[object, ...]) -> Decimal:
    return Decimal(len(values)).quantize(DECIMAL_QUANTUM)


def _require_payload_flags(payload: dict[str, Any]) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if payload.get(field_name) is not True:
            raise ValueError(f"{field_name} must be True for payload")


def _require_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    if value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return value.quantize(DECIMAL_QUANTUM)


def _require_unit_interval_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_nonnegative_decimal(field_name, value)
    if normalized > ONE:
        raise ValueError(f"{field_name} must be at most 1")
    return normalized


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str or not value or value.strip() != value or value.lower() != value:
        raise ValueError(f"{field_name} must be a canonical string")
    allowed_chars = set("abcdefghijklmnopqrstuvwxyz0123456789._-")
    if any(char not in allowed_chars for char in value):
        raise ValueError(f"{field_name} must be a canonical string")


def _require_nonempty_string(field_name: str, value: object) -> None:
    if type(value) is not str or not value.strip():
        raise ValueError(f"{field_name} must be a non-empty string")


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


__all__ = (
    "DEFAULT_STRATEGY_RESEARCH_BACKLOG_BALANCER_V5_CONFIG_VERSION",
    "StrategyResearchBacklogBalancerV5Config",
    "StrategyResearchBacklogBalancerV5Report",
    "StrategyResearchBacklogBalancerV5Row",
    "StrategyResearchBacklogCandidateV5",
    "StrategyResearchBacklogTeamSpecializationV5",
    "StrategyResearchBacklogTeamStateV5",
    "build_strategy_research_backlog_balancer_v5_report",
    "strategy_research_backlog_balancer_v5_payload",
)
