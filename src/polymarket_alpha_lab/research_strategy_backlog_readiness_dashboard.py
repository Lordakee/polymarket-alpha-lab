"""Public, report-only readiness dashboard for strategy research backlog candidates."""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from typing import Any

from polymarket_alpha_lab.team_paper_guard import (
    reject_unsafe_surface_fields,
    require_paper_only_flags,
)


DEFAULT_RESEARCH_STRATEGY_BACKLOG_READINESS_DASHBOARD_CONFIG_VERSION = (
    "research-strategy-backlog-readiness-dashboard-v0"
)

PUBLIC_STATUSES = ("pass", "watch", "block")
REVIEW_STATUSES = ("complete", "in_progress", "pending", "missing")
POSTMORTEM_STATUSES = ("complete", "pending", "missing")
HUMAN_NEXT_STEPS = {
    "pass": "ready_for_human_review",
    "watch": "needs_manual_research_update",
    "block": "blocked_until_manual_clearance",
}
PASS_REASON = "backlog_all_pass"
WATCH_REASON = "backlog_watch_present"
BLOCK_REASON = "backlog_block_present"
EMPTY_REASON = "backlog_empty"
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
SCORE_QUANTUM = Decimal("0.000001")
COUNT_QUANTUM = Decimal("1")
ZERO = Decimal("0")
ONE = Decimal("1")
VALIDATION_DIGEST_ALGORITHM = "sha256"
HEX_DIGITS = frozenset("0123456789abcdef")
PRIVATE_HASH_PERSON = "research_strategy_backlog_readiness_candidate"
UNSAFE_PUBLIC_KEY_FRAGMENTS = (
    "candidate_id",
    "market_id",
    "market_slug",
    "slug",
    "question",
    "source_ref",
    "source_url",
    "source_text",
    "url",
    "dsn",
    "table",
)
UNSAFE_PUBLIC_VALUE_FRAGMENTS = (
    "raw-candidate-id",
    "market-id",
    "market_id",
    "market slug",
    "market_slug",
    "http://",
    "https://",
    "postgres://",
    "dsn=",
    "token=",
    "secret=",
    "api_key=",
    "source ref",
    "source_ref",
    "source text",
    "source_text",
    " buy",
    "buy ",
    " sell",
    "sell ",
    "trade",
)
COUNT_PAYLOAD_FIELDS = frozenset(
    (
        "candidate_count",
        "pass_count",
        "watch_count",
        "block_count",
        "hard_flag_count",
        "reviewed_count",
        "postmortem_complete_count",
        "evidence_item_count",
        "evidence_family_count",
        "team_count",
        "covered_team_count",
        "review_age_seconds",
        "count",
    ),
)


class _FinalPublicDataclass:
    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        for base in cls.__bases__:
            if base is not _FinalPublicDataclass and issubclass(
                base,
                _FinalPublicDataclass,
            ):
                raise TypeError(f"{base.__name__} may not be subclassed")


@dataclass(frozen=True)
class ResearchStrategyBacklogReadinessDashboardConfig(_FinalPublicDataclass):
    config_version: str = (
        DEFAULT_RESEARCH_STRATEGY_BACKLOG_READINESS_DASHBOARD_CONFIG_VERSION
    )
    evidence_quality_watch_floor: Decimal = Decimal("0.800000")
    evidence_quality_block_floor: Decimal = Decimal("0.500000")
    evidence_item_watch_floor: Decimal = Decimal("3")
    evidence_family_watch_floor: Decimal = Decimal("2")
    cost_drag_watch: Decimal = Decimal("0.070000")
    cost_drag_block: Decimal = Decimal("0.150000")
    team_coverage_watch_floor: Decimal = Decimal("0.800000")
    team_coverage_block_floor: Decimal = Decimal("0.500000")
    review_stale_watch_seconds: Decimal = Decimal("86400")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchStrategyBacklogReadinessDashboardConfig,
            "config",
        )
        _require_canonical_string("config_version", self.config_version)
        for field_name in (
            "evidence_quality_watch_floor",
            "evidence_quality_block_floor",
            "cost_drag_watch",
            "cost_drag_block",
            "team_coverage_watch_floor",
            "team_coverage_block_floor",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_score_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "evidence_item_watch_floor",
            "evidence_family_watch_floor",
            "review_stale_watch_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_whole_decimal(field_name, getattr(self, field_name)),
            )
        if self.evidence_quality_block_floor > self.evidence_quality_watch_floor:
            raise ValueError(
                "evidence_quality_block_floor must not exceed evidence_quality_watch_floor",
            )
        if self.team_coverage_block_floor > self.team_coverage_watch_floor:
            raise ValueError(
                "team_coverage_block_floor must not exceed team_coverage_watch_floor",
            )
        if self.cost_drag_watch > self.cost_drag_block:
            raise ValueError("cost_drag_watch must not exceed cost_drag_block")
        require_paper_only_flags("ResearchStrategyBacklogReadinessDashboardConfig", self)


@dataclass(frozen=True)
class ResearchStrategyBacklogReadinessCandidate(_FinalPublicDataclass):
    private_ref: str
    private_context: tuple[str, ...]
    evidence_quality_score: Decimal
    evidence_item_count: Decimal
    evidence_family_count: Decimal
    cost_drag_score: Decimal
    team_coverage_score: Decimal
    team_count: Decimal
    covered_team_count: Decimal
    review_status: str
    review_age_seconds: Decimal
    postmortem_status: str
    hard_flag_codes: tuple[str, ...] = ()
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchStrategyBacklogReadinessCandidate, "candidate")
        _require_private_string("private_ref", self.private_ref)
        object.__setattr__(
            self,
            "private_context",
            _normalize_private_context(self.private_context),
        )
        for field_name in (
            "evidence_quality_score",
            "cost_drag_score",
            "team_coverage_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_score_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "evidence_item_count",
            "evidence_family_count",
            "team_count",
            "covered_team_count",
            "review_age_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_whole_decimal(field_name, getattr(self, field_name)),
            )
        if self.covered_team_count > self.team_count:
            raise ValueError("covered_team_count must not exceed team_count")
        _require_member("review_status", self.review_status, REVIEW_STATUSES)
        _require_member("postmortem_status", self.postmortem_status, POSTMORTEM_STATUSES)
        object.__setattr__(
            self,
            "hard_flag_codes",
            _normalize_public_codes("hard_flag_codes", self.hard_flag_codes, allow_empty=True),
        )
        require_paper_only_flags("ResearchStrategyBacklogReadinessCandidate", self)


@dataclass(frozen=True)
class ResearchStrategyBacklogReadinessDashboardRow(_FinalPublicDataclass):
    public_candidate_ref: str
    public_status: str
    evidence_quality_score: Decimal
    evidence_item_count: Decimal
    evidence_family_count: Decimal
    cost_drag_score: Decimal
    team_coverage_score: Decimal
    team_count: Decimal
    covered_team_count: Decimal
    review_status: str
    review_age_seconds: Decimal
    postmortem_status: str
    hard_flag_count: Decimal
    readiness_score: Decimal
    human_next_step: str
    reason_codes: tuple[str, ...]
    validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchStrategyBacklogReadinessDashboardRow,
            "row",
        )
        _require_public_ref("public_candidate_ref", self.public_candidate_ref)
        _require_member("public_status", self.public_status, PUBLIC_STATUSES)
        for field_name in (
            "evidence_quality_score",
            "cost_drag_score",
            "team_coverage_score",
            "readiness_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_score_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "evidence_item_count",
            "evidence_family_count",
            "team_count",
            "covered_team_count",
            "review_age_seconds",
            "hard_flag_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_whole_decimal(field_name, getattr(self, field_name)),
            )
        if self.covered_team_count > self.team_count:
            raise ValueError("covered_team_count must not exceed team_count")
        _require_member("review_status", self.review_status, REVIEW_STATUSES)
        _require_member("postmortem_status", self.postmortem_status, POSTMORTEM_STATUSES)
        _require_canonical_string("human_next_step", self.human_next_step)
        if self.human_next_step != HUMAN_NEXT_STEPS[self.public_status]:
            raise ValueError("human_next_step must match public_status")
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_public_codes("reason_codes", self.reason_codes, allow_empty=False),
        )
        if self.public_status != _row_status_from_reason_codes(self.reason_codes):
            raise ValueError("public_status must match reason_codes")
        _reject_unsafe_public_payload("row", self)
        require_paper_only_flags("ResearchStrategyBacklogReadinessDashboardRow", self)
        object.__setattr__(
            self,
            "validation_digest",
            _normalize_validation_digest(
                "validation_digest",
                self.validation_digest,
                _row_validation_digest(
                    public_candidate_ref=self.public_candidate_ref,
                    public_status=self.public_status,
                    evidence_quality_score=self.evidence_quality_score,
                    evidence_item_count=self.evidence_item_count,
                    evidence_family_count=self.evidence_family_count,
                    cost_drag_score=self.cost_drag_score,
                    team_coverage_score=self.team_coverage_score,
                    team_count=self.team_count,
                    covered_team_count=self.covered_team_count,
                    review_status=self.review_status,
                    review_age_seconds=self.review_age_seconds,
                    postmortem_status=self.postmortem_status,
                    hard_flag_count=self.hard_flag_count,
                    readiness_score=self.readiness_score,
                    human_next_step=self.human_next_step,
                    reason_codes=self.reason_codes,
                ),
            ),
        )


@dataclass(frozen=True)
class ResearchStrategyBacklogReadinessDashboardReasonCodeCount(_FinalPublicDataclass):
    reason_code: str
    count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchStrategyBacklogReadinessDashboardReasonCodeCount,
            "reason_code_count",
        )
        object.__setattr__(
            self,
            "reason_code",
            _normalize_public_code("reason_code", self.reason_code),
        )
        object.__setattr__(
            self,
            "count",
            _require_positive_whole_decimal("count", self.count),
        )
        _reject_unsafe_public_payload("reason_code_count", self)
        require_paper_only_flags(
            "ResearchStrategyBacklogReadinessDashboardReasonCodeCount",
            self,
        )


@dataclass(frozen=True)
class ResearchStrategyBacklogReadinessDashboardReport(_FinalPublicDataclass):
    generated_at: datetime
    config_version: str
    public_status: str
    candidate_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    hard_flag_count: Decimal
    reviewed_count: Decimal
    postmortem_complete_count: Decimal
    mean_evidence_quality_score: Decimal
    mean_cost_drag_score: Decimal
    mean_team_coverage_score: Decimal
    rows: tuple[ResearchStrategyBacklogReadinessDashboardRow, ...]
    reason_code_counts: tuple[
        ResearchStrategyBacklogReadinessDashboardReasonCodeCount,
        ...
    ]
    reason_codes: tuple[str, ...]
    validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchStrategyBacklogReadinessDashboardReport,
            "report",
        )
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        _require_member("public_status", self.public_status, PUBLIC_STATUSES)
        for field_name in (
            "candidate_count",
            "pass_count",
            "watch_count",
            "block_count",
            "hard_flag_count",
            "reviewed_count",
            "postmortem_complete_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_whole_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "mean_evidence_quality_score",
            "mean_cost_drag_score",
            "mean_team_coverage_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_score_decimal(field_name, getattr(self, field_name)),
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
            _normalize_public_codes("reason_codes", self.reason_codes, allow_empty=False),
        )
        _validate_report_consistency(self)
        _reject_unsafe_public_payload("report", self)
        require_paper_only_flags("ResearchStrategyBacklogReadinessDashboardReport", self)
        object.__setattr__(
            self,
            "validation_digest",
            _normalize_validation_digest(
                "validation_digest",
                self.validation_digest,
                _report_validation_digest(
                    generated_at=self.generated_at,
                    config_version=self.config_version,
                    public_status=self.public_status,
                    candidate_count=self.candidate_count,
                    pass_count=self.pass_count,
                    watch_count=self.watch_count,
                    block_count=self.block_count,
                    hard_flag_count=self.hard_flag_count,
                    reviewed_count=self.reviewed_count,
                    postmortem_complete_count=self.postmortem_complete_count,
                    mean_evidence_quality_score=self.mean_evidence_quality_score,
                    mean_cost_drag_score=self.mean_cost_drag_score,
                    mean_team_coverage_score=self.mean_team_coverage_score,
                    rows=self.rows,
                    reason_code_counts=self.reason_code_counts,
                    reason_codes=self.reason_codes,
                ),
            ),
        )


def build_research_strategy_backlog_readiness_dashboard(
    candidates: Iterable[ResearchStrategyBacklogReadinessCandidate],
    *,
    config: ResearchStrategyBacklogReadinessDashboardConfig,
    generated_at: datetime,
) -> ResearchStrategyBacklogReadinessDashboardReport:
    if type(config) is not ResearchStrategyBacklogReadinessDashboardConfig:
        raise ValueError(
            "config must be a ResearchStrategyBacklogReadinessDashboardConfig",
        )
    require_paper_only_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    normalized_candidates = _normalize_candidates(candidates)
    indexed_candidates = tuple(
        enumerate(sorted(normalized_candidates, key=_candidate_private_sort_key), start=1),
    )
    rows = tuple(
        sorted(
            (
                _row_from_candidate(
                    index=index,
                    candidate=candidate,
                    config=config,
                )
                for index, candidate in indexed_candidates
            ),
            key=_row_sort_key,
        ),
    )
    reason_codes = _report_reason_codes(rows)
    return ResearchStrategyBacklogReadinessDashboardReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        public_status=_report_public_status(rows),
        candidate_count=_decimal_count(len(rows)),
        pass_count=_status_count(rows, "pass"),
        watch_count=_status_count(rows, "watch"),
        block_count=_status_count(rows, "block"),
        hard_flag_count=sum((row.hard_flag_count for row in rows), ZERO),
        reviewed_count=_decimal_count(
            sum(1 for row in rows if row.review_status == "complete"),
        ),
        postmortem_complete_count=_decimal_count(
            sum(1 for row in rows if row.postmortem_status == "complete"),
        ),
        mean_evidence_quality_score=_mean_score(
            tuple(row.evidence_quality_score for row in rows),
        ),
        mean_cost_drag_score=_mean_score(tuple(row.cost_drag_score for row in rows)),
        mean_team_coverage_score=_mean_score(
            tuple(row.team_coverage_score for row in rows),
        ),
        rows=rows,
        reason_code_counts=_reason_code_counts(rows, reason_codes),
        reason_codes=reason_codes,
    )


def research_strategy_backlog_readiness_dashboard_payload(
    report: ResearchStrategyBacklogReadinessDashboardReport | dict[str, Any],
) -> dict[str, Any]:
    if type(report) is ResearchStrategyBacklogReadinessDashboardReport:
        _validate_report_runtime(report)
        _reject_unsafe_public_payload(
            "research strategy backlog readiness dashboard report",
            report,
        )
        payload = _json_ready_public_payload(asdict(report), allow_decimal=True)
    elif type(report) is dict:
        _reject_unsafe_public_payload(
            "research strategy backlog readiness dashboard payload",
            report,
        )
        payload = _json_ready_public_payload(report, allow_decimal=False)
    else:
        raise ValueError(
            "report must be a ResearchStrategyBacklogReadinessDashboardReport",
        )
    if type(payload) is not dict:
        raise ValueError("dashboard payload must be a JSON object")
    _reject_unsafe_public_payload(
        "research strategy backlog readiness dashboard payload",
        payload,
    )
    _validate_payload_digest(payload)
    _validate_payload_report_consistency(payload)
    return payload


def research_strategy_backlog_readiness_dashboard_digest(
    report: ResearchStrategyBacklogReadinessDashboardReport | dict[str, Any],
) -> str:
    payload = research_strategy_backlog_readiness_dashboard_payload(report)
    return _payload_required_digest(payload, "validation_digest")


def _row_from_candidate(
    *,
    index: int,
    candidate: ResearchStrategyBacklogReadinessCandidate,
    config: ResearchStrategyBacklogReadinessDashboardConfig,
) -> ResearchStrategyBacklogReadinessDashboardRow:
    reason_codes = _row_reason_codes(candidate, config=config)
    public_status = _row_status_from_reason_codes(reason_codes)
    return ResearchStrategyBacklogReadinessDashboardRow(
        public_candidate_ref=_public_candidate_ref(index, candidate),
        public_status=public_status,
        evidence_quality_score=candidate.evidence_quality_score,
        evidence_item_count=candidate.evidence_item_count,
        evidence_family_count=candidate.evidence_family_count,
        cost_drag_score=candidate.cost_drag_score,
        team_coverage_score=candidate.team_coverage_score,
        team_count=candidate.team_count,
        covered_team_count=candidate.covered_team_count,
        review_status=candidate.review_status,
        review_age_seconds=candidate.review_age_seconds,
        postmortem_status=candidate.postmortem_status,
        hard_flag_count=_decimal_count(len(candidate.hard_flag_codes)),
        readiness_score=_readiness_score(candidate),
        human_next_step=HUMAN_NEXT_STEPS[public_status],
        reason_codes=reason_codes,
    )


def _row_reason_codes(
    candidate: ResearchStrategyBacklogReadinessCandidate,
    *,
    config: ResearchStrategyBacklogReadinessDashboardConfig,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    if candidate.hard_flag_codes:
        reason_codes.append("hard_flags_present")
        reason_codes.extend(candidate.hard_flag_codes)
    if candidate.evidence_quality_score < config.evidence_quality_block_floor:
        reason_codes.append("evidence_quality_block")
    elif candidate.evidence_quality_score < config.evidence_quality_watch_floor:
        reason_codes.append("evidence_quality_watch")
    if candidate.evidence_item_count < config.evidence_item_watch_floor:
        reason_codes.append("evidence_count_watch")
    if candidate.evidence_family_count < config.evidence_family_watch_floor:
        reason_codes.append("evidence_family_watch")
    if candidate.cost_drag_score >= config.cost_drag_block:
        reason_codes.append("cost_drag_block")
    elif candidate.cost_drag_score >= config.cost_drag_watch:
        reason_codes.append("cost_drag_watch")
    if candidate.team_coverage_score < config.team_coverage_block_floor:
        reason_codes.append("team_coverage_block")
    elif candidate.team_coverage_score < config.team_coverage_watch_floor:
        reason_codes.append("team_coverage_watch")
    if candidate.review_status == "missing":
        reason_codes.append("review_missing")
    elif candidate.review_status != "complete":
        reason_codes.append("review_watch")
    if candidate.review_age_seconds >= config.review_stale_watch_seconds:
        reason_codes.append("review_stale_watch")
    if candidate.postmortem_status == "missing":
        reason_codes.append("postmortem_missing")
    elif candidate.postmortem_status == "pending":
        reason_codes.append("postmortem_pending")
    return tuple(dict.fromkeys(reason_codes)) or ("readiness_pass",)


def _row_status_from_reason_codes(reason_codes: tuple[str, ...]) -> str:
    if "hard_flags_present" in reason_codes or any(
        reason_code.endswith("_block") or reason_code.endswith("_missing")
        for reason_code in reason_codes
    ):
        return "block"
    if reason_codes != ("readiness_pass",):
        return "watch"
    return "pass"


def _readiness_score(candidate: ResearchStrategyBacklogReadinessCandidate) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        quality = candidate.evidence_quality_score
        cost = ONE - candidate.cost_drag_score
        coverage = candidate.team_coverage_score
        review = ONE if candidate.review_status == "complete" else Decimal("0.500000")
        postmortem = (
            ONE if candidate.postmortem_status == "complete" else Decimal("0.500000")
        )
        hard_flag_penalty = min(ONE, Decimal(len(candidate.hard_flag_codes)) * Decimal("0.250000"))
        score = (
            (quality * Decimal("0.350000"))
            + (cost * Decimal("0.200000"))
            + (coverage * Decimal("0.250000"))
            + (review * Decimal("0.100000"))
            + (postmortem * Decimal("0.100000"))
            - hard_flag_penalty
        )
        if score < ZERO:
            score = ZERO
        if score > ONE:
            score = ONE
        return _quantize_score(score)


def _report_public_status(
    rows: tuple[ResearchStrategyBacklogReadinessDashboardRow, ...],
) -> str:
    if not rows:
        return "block"
    statuses = tuple(row.public_status for row in rows)
    if "block" in statuses:
        return "block"
    if "watch" in statuses:
        return "watch"
    return "pass"


def _report_reason_codes(
    rows: tuple[ResearchStrategyBacklogReadinessDashboardRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return (EMPTY_REASON,)
    status = _report_public_status(rows)
    if status == "pass":
        return (PASS_REASON,)
    prefix = BLOCK_REASON if status == "block" else WATCH_REASON
    row_reasons = tuple(
        sorted(
            {
                reason_code
                for row in rows
                for reason_code in row.reason_codes
                if reason_code != "readiness_pass"
            },
        ),
    )
    return (prefix,) + row_reasons


def _reason_code_counts(
    rows: tuple[ResearchStrategyBacklogReadinessDashboardRow, ...],
    report_reason_codes: tuple[str, ...],
) -> tuple[ResearchStrategyBacklogReadinessDashboardReasonCodeCount, ...]:
    counts: dict[str, Decimal] = {reason_code: ZERO for reason_code in report_reason_codes}
    for row in rows:
        for reason_code in row.reason_codes:
            counts[reason_code] = counts.get(reason_code, ZERO) + ONE
    return tuple(
        ResearchStrategyBacklogReadinessDashboardReasonCodeCount(
            reason_code=reason_code,
            count=count if count > ZERO else ONE,
        )
        for reason_code, count in sorted(counts.items())
    )


def _validate_report_consistency(
    report: ResearchStrategyBacklogReadinessDashboardReport,
) -> None:
    if report.candidate_count != _decimal_count(len(report.rows)):
        raise ValueError("candidate_count must match rows")
    if report.pass_count != _status_count(report.rows, "pass"):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _status_count(report.rows, "watch"):
        raise ValueError("watch_count must match rows")
    if report.block_count != _status_count(report.rows, "block"):
        raise ValueError("block_count must match rows")
    if report.candidate_count != report.pass_count + report.watch_count + report.block_count:
        raise ValueError("candidate_count must match status counts")
    if report.public_status != _report_public_status(report.rows):
        raise ValueError("public_status must match rows")
    if report.hard_flag_count != sum((row.hard_flag_count for row in report.rows), ZERO):
        raise ValueError("hard_flag_count must match rows")
    if report.reviewed_count != _decimal_count(
        sum(1 for row in report.rows if row.review_status == "complete"),
    ):
        raise ValueError("reviewed_count must match rows")
    if report.postmortem_complete_count != _decimal_count(
        sum(1 for row in report.rows if row.postmortem_status == "complete"),
    ):
        raise ValueError("postmortem_complete_count must match rows")
    if report.mean_evidence_quality_score != _mean_score(
        tuple(row.evidence_quality_score for row in report.rows),
    ):
        raise ValueError("mean_evidence_quality_score must match rows")
    if report.mean_cost_drag_score != _mean_score(
        tuple(row.cost_drag_score for row in report.rows),
    ):
        raise ValueError("mean_cost_drag_score must match rows")
    if report.mean_team_coverage_score != _mean_score(
        tuple(row.team_coverage_score for row in report.rows),
    ):
        raise ValueError("mean_team_coverage_score must match rows")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")
    if report.reason_code_counts != _reason_code_counts(report.rows, report.reason_codes):
        raise ValueError("reason_code_counts must summarize rows")


def _validate_report_runtime(report: ResearchStrategyBacklogReadinessDashboardReport) -> None:
    require_paper_only_flags("ResearchStrategyBacklogReadinessDashboardReport", report)
    _as_utc("generated_at", report.generated_at)
    _require_canonical_string("config_version", report.config_version)
    _require_member("public_status", report.public_status, PUBLIC_STATUSES)
    _normalize_rows(report.rows)
    _normalize_reason_code_counts(report.reason_code_counts)
    _normalize_public_codes("reason_codes", report.reason_codes, allow_empty=False)
    for row in report.rows:
        _validate_row_runtime(row)
    _validate_report_consistency(report)
    if report.validation_digest != _report_validation_digest(
        generated_at=report.generated_at,
        config_version=report.config_version,
        public_status=report.public_status,
        candidate_count=report.candidate_count,
        pass_count=report.pass_count,
        watch_count=report.watch_count,
        block_count=report.block_count,
        hard_flag_count=report.hard_flag_count,
        reviewed_count=report.reviewed_count,
        postmortem_complete_count=report.postmortem_complete_count,
        mean_evidence_quality_score=report.mean_evidence_quality_score,
        mean_cost_drag_score=report.mean_cost_drag_score,
        mean_team_coverage_score=report.mean_team_coverage_score,
        rows=report.rows,
        reason_code_counts=report.reason_code_counts,
        reason_codes=report.reason_codes,
    ):
        raise ValueError("validation_digest must match report")


def _validate_row_runtime(row: ResearchStrategyBacklogReadinessDashboardRow) -> None:
    require_paper_only_flags("ResearchStrategyBacklogReadinessDashboardRow", row)
    _require_public_ref("public_candidate_ref", row.public_candidate_ref)
    _require_member("public_status", row.public_status, PUBLIC_STATUSES)
    _normalize_public_codes("reason_codes", row.reason_codes, allow_empty=False)
    if row.validation_digest != _row_validation_digest(
        public_candidate_ref=row.public_candidate_ref,
        public_status=row.public_status,
        evidence_quality_score=row.evidence_quality_score,
        evidence_item_count=row.evidence_item_count,
        evidence_family_count=row.evidence_family_count,
        cost_drag_score=row.cost_drag_score,
        team_coverage_score=row.team_coverage_score,
        team_count=row.team_count,
        covered_team_count=row.covered_team_count,
        review_status=row.review_status,
        review_age_seconds=row.review_age_seconds,
        postmortem_status=row.postmortem_status,
        hard_flag_count=row.hard_flag_count,
        readiness_score=row.readiness_score,
        human_next_step=row.human_next_step,
        reason_codes=row.reason_codes,
    ):
        raise ValueError("validation_digest must match row")


def _validate_payload_digest(payload: dict[str, Any]) -> None:
    rows = _payload_rows(payload)
    expected_row_digests = tuple(_payload_row_digest(row) for row in rows)
    for row, expected_digest in zip(rows, expected_row_digests, strict=True):
        if _payload_required_digest(row, "validation_digest") != expected_digest:
            raise ValueError("validation_digest must match payload row")
    if _payload_required_digest(payload, "validation_digest") != _payload_report_digest(
        payload,
        expected_row_digests,
    ):
        raise ValueError("validation_digest must match payload")


def _validate_payload_report_consistency(
    payload: dict[str, Any],
) -> None:
    rows = _payload_rows(payload)
    if _payload_required_count_decimal(payload, "candidate_count") != _decimal_count(len(rows)):
        raise ValueError("candidate_count must match payload rows")
    for status, field_name in (
        ("pass", "pass_count"),
        ("watch", "watch_count"),
        ("block", "block_count"),
    ):
        if _payload_required_count_decimal(payload, field_name) != _payload_status_count(
            rows,
            status,
        ):
            raise ValueError(f"{field_name} must match payload rows")
    public_status = _payload_required_member(payload, "public_status", PUBLIC_STATUSES)
    if public_status != _payload_public_status(rows):
        raise ValueError("public_status must match payload rows")


def _payload_row_digest(row: dict[str, Any]) -> str:
    _require_payload_flags(row)
    return _hash_parts(
        (
            VALIDATION_DIGEST_ALGORITHM,
            "research_strategy_backlog_readiness_dashboard_row",
            _payload_required_public_ref(row, "public_candidate_ref"),
            _payload_required_member(row, "public_status", PUBLIC_STATUSES),
            _payload_required_score_string(row, "evidence_quality_score"),
            _payload_required_count_string(row, "evidence_item_count"),
            _payload_required_count_string(row, "evidence_family_count"),
            _payload_required_score_string(row, "cost_drag_score"),
            _payload_required_score_string(row, "team_coverage_score"),
            _payload_required_count_string(row, "team_count"),
            _payload_required_count_string(row, "covered_team_count"),
            _payload_required_member(row, "review_status", REVIEW_STATUSES),
            _payload_required_count_string(row, "review_age_seconds"),
            _payload_required_member(row, "postmortem_status", POSTMORTEM_STATUSES),
            _payload_required_count_string(row, "hard_flag_count"),
            _payload_required_score_string(row, "readiness_score"),
            _payload_required_string(row, "human_next_step"),
            _string_sequence_payload(_payload_required_string_sequence(row, "reason_codes")),
            "paper_only=True",
            "report_only=True",
            "readonly=True",
        ),
    )


def _payload_report_digest(
    payload: dict[str, Any],
    row_digests: tuple[str, ...],
) -> str:
    reason_code_counts = _payload_reason_code_counts(payload)
    return _hash_parts(
        (
            VALIDATION_DIGEST_ALGORITHM,
            "research_strategy_backlog_readiness_dashboard_report",
            _payload_required_datetime_string(payload, "generated_at"),
            _payload_required_string(payload, "config_version"),
            _payload_required_member(payload, "public_status", PUBLIC_STATUSES),
            _payload_required_count_string(payload, "candidate_count"),
            _payload_required_count_string(payload, "pass_count"),
            _payload_required_count_string(payload, "watch_count"),
            _payload_required_count_string(payload, "block_count"),
            _payload_required_count_string(payload, "hard_flag_count"),
            _payload_required_count_string(payload, "reviewed_count"),
            _payload_required_count_string(payload, "postmortem_complete_count"),
            _payload_required_score_string(payload, "mean_evidence_quality_score"),
            _payload_required_score_string(payload, "mean_cost_drag_score"),
            _payload_required_score_string(payload, "mean_team_coverage_score"),
            _string_sequence_payload(row_digests),
            _string_sequence_payload(
                tuple(
                    f"{item['reason_code']}={item['count']}"
                    for item in reason_code_counts
                ),
            ),
            _string_sequence_payload(_payload_required_string_sequence(payload, "reason_codes")),
            "paper_only=True",
            "report_only=True",
            "readonly=True",
        ),
    )


def _row_validation_digest(
    *,
    public_candidate_ref: str,
    public_status: str,
    evidence_quality_score: Decimal,
    evidence_item_count: Decimal,
    evidence_family_count: Decimal,
    cost_drag_score: Decimal,
    team_coverage_score: Decimal,
    team_count: Decimal,
    covered_team_count: Decimal,
    review_status: str,
    review_age_seconds: Decimal,
    postmortem_status: str,
    hard_flag_count: Decimal,
    readiness_score: Decimal,
    human_next_step: str,
    reason_codes: tuple[str, ...],
) -> str:
    return _hash_parts(
        (
            VALIDATION_DIGEST_ALGORITHM,
            "research_strategy_backlog_readiness_dashboard_row",
            public_candidate_ref,
            public_status,
            _score_payload(evidence_quality_score),
            _count_payload(evidence_item_count),
            _count_payload(evidence_family_count),
            _score_payload(cost_drag_score),
            _score_payload(team_coverage_score),
            _count_payload(team_count),
            _count_payload(covered_team_count),
            review_status,
            _count_payload(review_age_seconds),
            postmortem_status,
            _count_payload(hard_flag_count),
            _score_payload(readiness_score),
            human_next_step,
            _string_sequence_payload(reason_codes),
            "paper_only=True",
            "report_only=True",
            "readonly=True",
        ),
    )


def _report_validation_digest(
    *,
    generated_at: datetime,
    config_version: str,
    public_status: str,
    candidate_count: Decimal,
    pass_count: Decimal,
    watch_count: Decimal,
    block_count: Decimal,
    hard_flag_count: Decimal,
    reviewed_count: Decimal,
    postmortem_complete_count: Decimal,
    mean_evidence_quality_score: Decimal,
    mean_cost_drag_score: Decimal,
    mean_team_coverage_score: Decimal,
    rows: tuple[ResearchStrategyBacklogReadinessDashboardRow, ...],
    reason_code_counts: tuple[ResearchStrategyBacklogReadinessDashboardReasonCodeCount, ...],
    reason_codes: tuple[str, ...],
) -> str:
    return _hash_parts(
        (
            VALIDATION_DIGEST_ALGORITHM,
            "research_strategy_backlog_readiness_dashboard_report",
            _datetime_payload(generated_at),
            config_version,
            public_status,
            _count_payload(candidate_count),
            _count_payload(pass_count),
            _count_payload(watch_count),
            _count_payload(block_count),
            _count_payload(hard_flag_count),
            _count_payload(reviewed_count),
            _count_payload(postmortem_complete_count),
            _score_payload(mean_evidence_quality_score),
            _score_payload(mean_cost_drag_score),
            _score_payload(mean_team_coverage_score),
            _string_sequence_payload(tuple(row.validation_digest for row in rows)),
            _string_sequence_payload(
                tuple(
                    f"{item.reason_code}={_count_payload(item.count)}"
                    for item in reason_code_counts
                ),
            ),
            _string_sequence_payload(reason_codes),
            "paper_only=True",
            "report_only=True",
            "readonly=True",
        ),
    )


def _public_candidate_ref(
    index: int,
    candidate: ResearchStrategyBacklogReadinessCandidate,
) -> str:
    digest = _hash_parts(
        (
            PRIVATE_HASH_PERSON,
            candidate.private_ref,
            _string_sequence_payload(candidate.private_context),
        ),
    )
    return f"candidate_sha256:{index:06d}:{digest}"


def _candidate_private_sort_key(
    candidate: ResearchStrategyBacklogReadinessCandidate,
) -> tuple[str, tuple[str, ...]]:
    return (candidate.private_ref, candidate.private_context)


def _normalize_candidates(
    value: Iterable[ResearchStrategyBacklogReadinessCandidate],
) -> tuple[ResearchStrategyBacklogReadinessCandidate, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError("candidates must be an iterable")
    try:
        rows = tuple(value)
    except TypeError as exc:
        raise ValueError("candidates must be an iterable") from exc
    seen_refs: set[str] = set()
    for row in rows:
        if type(row) is not ResearchStrategyBacklogReadinessCandidate:
            raise ValueError(
                "candidates must contain ResearchStrategyBacklogReadinessCandidate",
            )
        require_paper_only_flags("candidate", row)
        if row.private_ref in seen_refs:
            raise ValueError("candidate private_ref values must be unique")
        seen_refs.add(row.private_ref)
    return rows


def _normalize_rows(
    value: object,
) -> tuple[ResearchStrategyBacklogReadinessDashboardRow, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("rows must be a list or tuple")
    rows = tuple(value)
    previous_ref: str | None = None
    for row in rows:
        if type(row) is not ResearchStrategyBacklogReadinessDashboardRow:
            raise ValueError("rows must contain dashboard rows")
        require_paper_only_flags("row", row)
        if previous_ref is not None and row.public_candidate_ref <= previous_ref:
            raise ValueError("rows must be deterministic by public_candidate_ref")
        previous_ref = row.public_candidate_ref
    return rows


def _normalize_reason_code_counts(
    value: object,
) -> tuple[ResearchStrategyBacklogReadinessDashboardReasonCodeCount, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("reason_code_counts must be a list or tuple")
    rows = tuple(value)
    previous_code: str | None = None
    for row in rows:
        if type(row) is not ResearchStrategyBacklogReadinessDashboardReasonCodeCount:
            raise ValueError("reason_code_counts must contain reason code counts")
        require_paper_only_flags("reason_code_count", row)
        if previous_code is not None and row.reason_code <= previous_code:
            raise ValueError("reason_code_counts must be sorted by reason_code")
        previous_code = row.reason_code
    return rows


def _payload_rows(payload: dict[str, Any]) -> tuple[dict[str, Any], ...]:
    value = payload.get("rows")
    if not isinstance(value, list):
        raise ValueError("rows must be a list")
    rows: list[dict[str, Any]] = []
    previous_ref: str | None = None
    for row in value:
        if type(row) is not dict:
            raise ValueError("rows must contain JSON objects")
        public_ref = _payload_required_public_ref(row, "public_candidate_ref")
        if previous_ref is not None and public_ref <= previous_ref:
            raise ValueError("rows must be deterministic by public_candidate_ref")
        previous_ref = public_ref
        rows.append(row)
    return tuple(rows)


def _payload_reason_code_counts(payload: dict[str, Any]) -> tuple[dict[str, str], ...]:
    value = payload.get("reason_code_counts")
    if not isinstance(value, list):
        raise ValueError("reason_code_counts must be a list")
    rows: list[dict[str, str]] = []
    previous_code: str | None = None
    for row in value:
        if type(row) is not dict:
            raise ValueError("reason_code_counts must contain JSON objects")
        reason_code = _payload_required_string(row, "reason_code")
        count = _payload_required_count_string(row, "count")
        if previous_code is not None and reason_code <= previous_code:
            raise ValueError("reason_code_counts must be sorted by reason_code")
        previous_code = reason_code
        rows.append({"reason_code": reason_code, "count": count})
    return tuple(rows)


def _payload_public_status(rows: tuple[dict[str, Any], ...]) -> str:
    if not rows:
        return "block"
    statuses = tuple(_payload_required_member(row, "public_status", PUBLIC_STATUSES) for row in rows)
    if "block" in statuses:
        return "block"
    if "watch" in statuses:
        return "watch"
    return "pass"


def _payload_status_count(rows: tuple[dict[str, Any], ...], status: str) -> Decimal:
    return _decimal_count(
        sum(
            1
            for row in rows
            if _payload_required_member(row, "public_status", PUBLIC_STATUSES) == status
        ),
    )


def _status_count(
    rows: tuple[ResearchStrategyBacklogReadinessDashboardRow, ...],
    status: str,
) -> Decimal:
    return _decimal_count(sum(1 for row in rows if row.public_status == status))


def _mean_score(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return ZERO.quantize(SCORE_QUANTUM)
    with localcontext(DECIMAL_CONTEXT):
        return _quantize_score(sum(values, ZERO) / Decimal(len(values)))


def _decimal_count(value: int) -> Decimal:
    if type(value) is not int:
        raise ValueError("count input must be an int")
    if value < 0:
        raise ValueError("count input must be nonnegative")
    return Decimal(value).quantize(COUNT_QUANTUM)


def _json_ready_public_payload(value: Any, *, allow_decimal: bool) -> Any:
    if value is None:
        return None
    if type(value) is Decimal:
        if not allow_decimal:
            raise ValueError("JSON numeric value must use Decimal-derived strings")
        return _score_payload(value)
    if isinstance(value, Decimal):
        raise ValueError("JSON numeric value must use exact Decimal values")
    if isinstance(value, datetime):
        return _datetime_payload(value)
    if type(value) is bool:
        return value
    if type(value) in (int, float):
        raise ValueError("JSON numeric value must use Decimal-derived strings")
    if type(value) is str:
        return value
    if isinstance(value, dict):
        ready: dict[str, Any] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            ready[key] = _json_ready_public_payload_field(
                key,
                item,
                allow_decimal=allow_decimal,
            )
        return ready
    if isinstance(value, (list, tuple)):
        return [_json_ready_public_payload(item, allow_decimal=allow_decimal) for item in value]
    raise ValueError("value is not JSON serializable")


def _json_ready_public_payload_field(
    field_name: str,
    value: Any,
    *,
    allow_decimal: bool,
) -> Any:
    if type(value) is Decimal:
        if not allow_decimal:
            raise ValueError("JSON numeric value must use Decimal-derived strings")
        if field_name in COUNT_PAYLOAD_FIELDS:
            return _count_payload(value)
        return _score_payload(value)
    return _json_ready_public_payload(value, allow_decimal=allow_decimal)


def _reject_unsafe_public_payload(label: str, value: object) -> None:
    reject_unsafe_surface_fields(label, value)
    _reject_unsafe_keys(label, value)
    _reject_unsafe_values(label, value)


def _reject_unsafe_keys(label: str, value: object) -> None:
    if hasattr(value, "__dataclass_fields__") and not isinstance(value, type):
        _reject_unsafe_keys(label, asdict(value))
        return
    if isinstance(value, dict):
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            normalized_key = key.lower()
            if any(fragment in normalized_key for fragment in UNSAFE_PUBLIC_KEY_FRAGMENTS):
                raise ValueError(f"unsafe public field in {label}: {key}")
            _reject_unsafe_keys(label, item)
        return
    if isinstance(value, (list, tuple)):
        for item in value:
            _reject_unsafe_keys(label, item)


def _reject_unsafe_values(label: str, value: object) -> None:
    if hasattr(value, "__dataclass_fields__") and not isinstance(value, type):
        _reject_unsafe_values(label, asdict(value))
        return
    if type(value) is str:
        normalized_value = value.lower()
        if any(fragment in normalized_value for fragment in UNSAFE_PUBLIC_VALUE_FRAGMENTS):
            raise ValueError(f"unsafe public value in {label}")
        return
    if isinstance(value, dict):
        for item in value.values():
            _reject_unsafe_values(label, item)
        return
    if isinstance(value, (list, tuple)):
        for item in value:
            _reject_unsafe_values(label, item)


def _normalize_private_context(value: object) -> tuple[str, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError("private_context must be a tuple of strings")
    try:
        rows = tuple(value)  # type: ignore[arg-type]
    except TypeError as exc:
        raise ValueError("private_context must be a tuple of strings") from exc
    for row in rows:
        _require_private_string("private_context", row)
    return rows


def _normalize_public_codes(
    field_name: str,
    value: object,
    *,
    allow_empty: bool,
) -> tuple[str, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError(f"{field_name} must be a tuple of public codes")
    try:
        rows = tuple(value)  # type: ignore[arg-type]
    except TypeError as exc:
        raise ValueError(f"{field_name} must be a tuple of public codes") from exc
    if not rows and not allow_empty:
        raise ValueError(f"{field_name} must contain at least one value")
    normalized: list[str] = []
    for row in rows:
        code = _normalize_public_code(field_name, row)
        if code not in normalized:
            normalized.append(code)
    return tuple(normalized)


def _normalize_public_code(field_name: str, value: object) -> str:
    _require_canonical_string(field_name, value)
    _reject_unsafe_values(field_name, value)
    return value


def _normalize_validation_digest(
    field_name: str,
    value: object,
    expected_digest: str,
) -> str:
    if value == "":
        return expected_digest
    digest = _require_validation_digest(field_name, value)
    if digest != expected_digest:
        raise ValueError(f"{field_name} must match derived values")
    return digest


def _require_validation_digest(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a validation digest")
    if len(value) != 64 or any(character not in HEX_DIGITS for character in value):
        raise ValueError(f"{field_name} must be a lowercase sha256 hex digest")
    return value


def _require_payload_flags(payload: dict[str, Any]) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if payload.get(field_name) is not True:
            raise ValueError(f"{field_name} must be True")


def _payload_required_digest(payload: dict[str, Any], field_name: str) -> str:
    return _require_validation_digest(field_name, payload.get(field_name))


def _payload_required_public_ref(payload: dict[str, Any], field_name: str) -> str:
    return _require_public_ref(field_name, payload.get(field_name))


def _payload_required_member(
    payload: dict[str, Any],
    field_name: str,
    allowed_values: tuple[str, ...],
) -> str:
    value = _payload_required_string(payload, field_name)
    _require_member(field_name, value, allowed_values)
    return value


def _payload_required_string(payload: dict[str, Any], field_name: str) -> str:
    value = payload.get(field_name)
    _require_canonical_string(field_name, value)
    _reject_unsafe_values(field_name, value)
    return value


def _payload_required_string_sequence(
    payload: dict[str, Any],
    field_name: str,
) -> tuple[str, ...]:
    value = payload.get(field_name)
    if not isinstance(value, list):
        raise ValueError(f"{field_name} must be a list of canonical strings")
    return _normalize_public_codes(field_name, value, allow_empty=False)


def _payload_required_count_decimal(payload: dict[str, Any], field_name: str) -> Decimal:
    return Decimal(_payload_required_count_string(payload, field_name))


def _payload_required_count_string(payload: dict[str, Any], field_name: str) -> str:
    value = payload.get(field_name)
    if type(value) is not str:
        raise ValueError(f"{field_name} must use Decimal-derived string values")
    try:
        decimal_value = Decimal(value)
    except Exception as exc:
        raise ValueError(f"{field_name} must use Decimal-derived string values") from exc
    decimal_value = _require_nonnegative_whole_decimal(field_name, decimal_value)
    canonical = _count_payload(decimal_value)
    if value != canonical:
        raise ValueError(f"{field_name} must be a canonical count string")
    return canonical


def _payload_required_score_string(payload: dict[str, Any], field_name: str) -> str:
    value = payload.get(field_name)
    if type(value) is not str:
        raise ValueError(f"{field_name} must use Decimal-derived string values")
    try:
        decimal_value = Decimal(value)
    except Exception as exc:
        raise ValueError(f"{field_name} must use Decimal-derived string values") from exc
    decimal_value = _require_score_decimal(field_name, decimal_value)
    canonical = _score_payload(decimal_value)
    if value != canonical:
        raise ValueError(f"{field_name} must be a canonical score string")
    return canonical


def _payload_required_datetime_string(payload: dict[str, Any], field_name: str) -> str:
    value = payload.get(field_name)
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a datetime string")
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError as exc:
        raise ValueError(f"{field_name} must be a datetime string") from exc
    canonical = _datetime_payload(parsed)
    if value != canonical:
        raise ValueError(f"{field_name} must be a canonical UTC datetime string")
    return canonical


def _hash_parts(parts: tuple[str, ...]) -> str:
    rendered = json.dumps(parts, separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha256(rendered.encode("utf-8")).hexdigest()


def _datetime_payload(value: datetime) -> str:
    return _as_utc("datetime", value).isoformat()


def _count_payload(value: Decimal) -> str:
    normalized = _require_nonnegative_whole_decimal("count", value)
    return str(normalized)


def _score_payload(value: Decimal) -> str:
    return str(_require_score_decimal("score", value))


def _string_sequence_payload(values: tuple[str, ...]) -> str:
    return "\x1f".join(values)


def _row_sort_key(
    row: ResearchStrategyBacklogReadinessDashboardRow,
) -> str:
    return row.public_candidate_ref


def _require_exact_type(value: object, expected_type: type[object], label: str) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{label} must be exactly {expected_type.__name__}")


def _require_public_ref(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a public reference")
    parts = value.split(":")
    if len(parts) != 3 or parts[0] != "candidate_sha256":
        raise ValueError(f"{field_name} must be a candidate_sha256 public reference")
    index, digest = parts[1], parts[2]
    if len(index) != 6 or not index.isdigit() or index == "000000":
        raise ValueError(f"{field_name} must include a deterministic public sequence")
    if len(digest) != 64 or any(character not in HEX_DIGITS for character in digest):
        raise ValueError(f"{field_name} must include a sha256 digest")
    return value


def _require_member(
    field_name: str,
    value: object,
    allowed_values: tuple[str, ...],
) -> None:
    if type(value) is not str or value not in allowed_values:
        raise ValueError(f"{field_name} must be one of {', '.join(allowed_values)}")


def _require_private_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a nonblank string")


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value or value.lower() != value:
        raise ValueError(f"{field_name} must be a canonical string")
    allowed_chars = set("abcdefghijklmnopqrstuvwxyz0123456789._:-=>")
    if any(character not in allowed_chars for character in value):
        raise ValueError(f"{field_name} must be a canonical string")


def _require_score_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    if value < ZERO or value > ONE:
        raise ValueError(f"{field_name} must be between zero and one")
    return _quantize_score(value)


def _require_nonnegative_whole_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    if value < ZERO or value != value.to_integral_value():
        raise ValueError(f"{field_name} must be a nonnegative whole Decimal")
    return value.quantize(COUNT_QUANTUM)


def _require_positive_whole_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_nonnegative_whole_decimal(field_name, value)
    if normalized <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _quantize_score(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(SCORE_QUANTUM)


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.tzinfo.utcoffset(value) is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


__all__ = (
    "DEFAULT_RESEARCH_STRATEGY_BACKLOG_READINESS_DASHBOARD_CONFIG_VERSION",
    "ResearchStrategyBacklogReadinessCandidate",
    "ResearchStrategyBacklogReadinessDashboardConfig",
    "ResearchStrategyBacklogReadinessDashboardReasonCodeCount",
    "ResearchStrategyBacklogReadinessDashboardReport",
    "ResearchStrategyBacklogReadinessDashboardRow",
    "build_research_strategy_backlog_readiness_dashboard",
    "research_strategy_backlog_readiness_dashboard_digest",
    "research_strategy_backlog_readiness_dashboard_payload",
)
