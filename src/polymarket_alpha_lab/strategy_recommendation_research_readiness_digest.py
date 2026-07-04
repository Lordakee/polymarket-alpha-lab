"""Pure Phase 1 research-readiness digest for strategy candidates."""

from __future__ import annotations

from dataclasses import asdict, dataclass, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from typing import Any

from polymarket_alpha_lab.team_paper_guard import (
    UNSAFE_SURFACE_FIELD_FRAGMENTS,
    reject_unsafe_surface_fields,
    require_paper_only_flags,
)


DEFAULT_STRATEGY_RECOMMENDATION_RESEARCH_READINESS_DIGEST_CONFIG_VERSION = (
    "strategy-recommendation-research-readiness-digest-v0"
)

READINESS_STATUSES = ("research_ready", "needs_review", "blocked")
REASON_CODES = (
    "readiness_empty_candidates",
    "readiness_source_quorum_met",
    "readiness_source_quorum_gap",
    "readiness_evidence_fresh",
    "readiness_evidence_stale",
    "readiness_rationale_complete",
    "readiness_rationale_incomplete",
    "readiness_resolution_criteria_covered",
    "readiness_resolution_criteria_missing",
    "readiness_team_memory_feedback_available",
    "readiness_team_memory_feedback_missing",
)
CRITERION_COUNT = Decimal("5")
ZERO = Decimal("0")
ONE = Decimal("1")
RATIO_QUANTUM = Decimal("0.000001")
SECONDS_QUANTUM = Decimal("0.000001")
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
PHASE_FLAG_FIELDS = ("paper_only", "report_only", "readonly")
SENSITIVE_PUBLIC_TEXT_FRAGMENTS = (
    "://",
    "api_key",
    "bearer ",
    "secret-",
    "secret_",
    "secret=",
)


@dataclass(frozen=True)
class StrategyRecommendationResearchReadinessDigestConfig:
    config_version: str = (
        DEFAULT_STRATEGY_RECOMMENDATION_RESEARCH_READINESS_DIGEST_CONFIG_VERSION
    )
    minimum_source_count: Decimal = Decimal("2")
    max_evidence_age_seconds: Decimal = Decimal("172800")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("config_version", self.config_version)
        object.__setattr__(
            self,
            "minimum_source_count",
            _normalize_decimal_whole_count(
                "minimum_source_count",
                self.minimum_source_count,
            ),
        )
        if self.minimum_source_count <= ZERO:
            raise ValueError("minimum_source_count must be positive")
        object.__setattr__(
            self,
            "max_evidence_age_seconds",
            _normalize_decimal_seconds(
                "max_evidence_age_seconds",
                self.max_evidence_age_seconds,
            ),
        )
        if self.max_evidence_age_seconds <= ZERO:
            raise ValueError("max_evidence_age_seconds must be positive")
        require_paper_only_flags(
            "StrategyRecommendationResearchReadinessDigestConfig",
            self,
        )


@dataclass(frozen=True)
class StrategyRecommendationResearchReadinessCandidate:
    candidate_id: str
    market_slug: str
    outcome_name: str
    source_count: Decimal
    evidence_collected_at: datetime
    rationale_summary: str
    rationale_evidence: str
    rationale_risk_notes: str
    resolution_criteria: str
    resolution_source_name: str
    team_memory_feedback_refs: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        for field_name in ("candidate_id", "market_slug", "outcome_name"):
            _require_canonical_string(field_name, getattr(self, field_name))
        object.__setattr__(
            self,
            "source_count",
            _normalize_decimal_whole_count("source_count", self.source_count),
        )
        object.__setattr__(
            self,
            "evidence_collected_at",
            _as_utc("evidence_collected_at", self.evidence_collected_at),
        )
        for field_name in (
            "rationale_summary",
            "rationale_evidence",
            "rationale_risk_notes",
            "resolution_criteria",
            "resolution_source_name",
        ):
            _require_string(field_name, getattr(self, field_name))
            object.__setattr__(self, field_name, getattr(self, field_name).strip())
        object.__setattr__(
            self,
            "team_memory_feedback_refs",
            _normalize_string_tuple(
                "team_memory_feedback_refs",
                self.team_memory_feedback_refs,
                allow_empty=True,
            ),
        )
        require_paper_only_flags(
            "StrategyRecommendationResearchReadinessCandidate",
            self,
        )


@dataclass(frozen=True)
class StrategyRecommendationResearchReadinessDigestRow:
    candidate_id: str
    market_slug: str
    outcome_name: str
    readiness_status: str
    generated_at: datetime
    source_count: Decimal
    minimum_source_count: Decimal
    source_gap_count: Decimal
    evidence_collected_at: datetime
    evidence_age_seconds: Decimal
    criterion_count: Decimal
    satisfied_criterion_count: Decimal
    issue_count: Decimal
    readiness_ratio: Decimal
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        for field_name in ("candidate_id", "market_slug", "outcome_name"):
            _require_canonical_string(field_name, getattr(self, field_name))
        _require_member("readiness_status", self.readiness_status, READINESS_STATUSES)
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        object.__setattr__(
            self,
            "evidence_collected_at",
            _as_utc("evidence_collected_at", self.evidence_collected_at),
        )
        for field_name in (
            "source_count",
            "minimum_source_count",
            "source_gap_count",
            "criterion_count",
            "satisfied_criterion_count",
            "issue_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_decimal_whole_count(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "evidence_age_seconds",
            _normalize_decimal_seconds(
                "evidence_age_seconds",
                self.evidence_age_seconds,
            ),
        )
        object.__setattr__(
            self,
            "readiness_ratio",
            _normalize_ratio("readiness_ratio", self.readiness_ratio),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes, allow_empty=False),
        )
        _validate_row_consistency(self)
        require_paper_only_flags(
            "StrategyRecommendationResearchReadinessDigestRow",
            self,
        )


@dataclass(frozen=True)
class StrategyRecommendationResearchReadinessDigestReport:
    generated_at: datetime
    config_version: str
    digest_status: str
    candidate_count: Decimal
    ready_candidate_count: Decimal
    needs_review_candidate_count: Decimal
    blocked_candidate_count: Decimal
    ready_candidate_ratio: Decimal | None
    needs_review_candidate_ratio: Decimal | None
    blocked_candidate_ratio: Decimal | None
    source_quorum_met_count: Decimal
    source_quorum_gap_count: Decimal
    fresh_evidence_count: Decimal
    stale_evidence_count: Decimal
    complete_rationale_count: Decimal
    incomplete_rationale_count: Decimal
    resolution_criteria_covered_count: Decimal
    resolution_criteria_missing_count: Decimal
    team_memory_feedback_available_count: Decimal
    team_memory_feedback_missing_count: Decimal
    rows: tuple[StrategyRecommendationResearchReadinessDigestRow, ...]
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        _require_member("digest_status", self.digest_status, READINESS_STATUSES)
        for field_name in (
            "candidate_count",
            "ready_candidate_count",
            "needs_review_candidate_count",
            "blocked_candidate_count",
            "source_quorum_met_count",
            "source_quorum_gap_count",
            "fresh_evidence_count",
            "stale_evidence_count",
            "complete_rationale_count",
            "incomplete_rationale_count",
            "resolution_criteria_covered_count",
            "resolution_criteria_missing_count",
            "team_memory_feedback_available_count",
            "team_memory_feedback_missing_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_decimal_whole_count(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "ready_candidate_ratio",
            "needs_review_candidate_ratio",
            "blocked_candidate_ratio",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_optional_ratio(field_name, getattr(self, field_name)),
            )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes, allow_empty=False),
        )
        _validate_report_consistency(self)
        require_paper_only_flags(
            "StrategyRecommendationResearchReadinessDigestReport",
            self,
        )


def build_strategy_recommendation_research_readiness_digest(
    candidates: list[StrategyRecommendationResearchReadinessCandidate]
    | tuple[StrategyRecommendationResearchReadinessCandidate, ...],
    *,
    config: StrategyRecommendationResearchReadinessDigestConfig,
    generated_at: datetime,
) -> StrategyRecommendationResearchReadinessDigestReport:
    if type(config) is not StrategyRecommendationResearchReadinessDigestConfig:
        raise ValueError(
            "config must be a StrategyRecommendationResearchReadinessDigestConfig",
        )
    require_paper_only_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    normalized_candidates = _normalize_candidates(candidates)
    rows = _build_rows(
        normalized_candidates,
        config=config,
        generated_at=generated_at_utc,
    )
    ready_candidate_count = _status_count(rows, "research_ready")
    needs_review_candidate_count = _status_count(rows, "needs_review")
    blocked_candidate_count = _status_count(rows, "blocked")
    candidate_count = Decimal(len(rows))

    return StrategyRecommendationResearchReadinessDigestReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        digest_status=_digest_status(rows),
        candidate_count=candidate_count,
        ready_candidate_count=ready_candidate_count,
        needs_review_candidate_count=needs_review_candidate_count,
        blocked_candidate_count=blocked_candidate_count,
        ready_candidate_ratio=_ratio_or_none(ready_candidate_count, candidate_count),
        needs_review_candidate_ratio=_ratio_or_none(
            needs_review_candidate_count,
            candidate_count,
        ),
        blocked_candidate_ratio=_ratio_or_none(
            blocked_candidate_count,
            candidate_count,
        ),
        source_quorum_met_count=_criterion_count(rows, "readiness_source_quorum_met"),
        source_quorum_gap_count=_criterion_count(rows, "readiness_source_quorum_gap"),
        fresh_evidence_count=_criterion_count(rows, "readiness_evidence_fresh"),
        stale_evidence_count=_criterion_count(rows, "readiness_evidence_stale"),
        complete_rationale_count=_criterion_count(
            rows,
            "readiness_rationale_complete",
        ),
        incomplete_rationale_count=_criterion_count(
            rows,
            "readiness_rationale_incomplete",
        ),
        resolution_criteria_covered_count=_criterion_count(
            rows,
            "readiness_resolution_criteria_covered",
        ),
        resolution_criteria_missing_count=_criterion_count(
            rows,
            "readiness_resolution_criteria_missing",
        ),
        team_memory_feedback_available_count=_criterion_count(
            rows,
            "readiness_team_memory_feedback_available",
        ),
        team_memory_feedback_missing_count=_criterion_count(
            rows,
            "readiness_team_memory_feedback_missing",
        ),
        rows=rows,
        reason_codes=_report_reason_codes(rows),
    )


def strategy_recommendation_research_readiness_digest_payload(
    report: StrategyRecommendationResearchReadinessDigestReport,
) -> dict[str, Any]:
    if type(report) is not StrategyRecommendationResearchReadinessDigestReport:
        raise ValueError(
            "report must be a StrategyRecommendationResearchReadinessDigestReport",
        )
    require_paper_only_flags(
        "StrategyRecommendationResearchReadinessDigestReport",
        report,
    )
    _reject_flag_downgrades("strategy research readiness digest report", report)
    reject_unsafe_surface_fields("strategy research readiness digest report", report)
    reject_unsafe_surface_fields(
        "strategy research readiness digest report",
        vars(report),
    )
    _reject_unsafe_public_text_values(
        "strategy research readiness digest report",
        report,
    )
    payload = _json_ready(asdict(report))
    if type(payload) is not dict:
        raise ValueError("digest payload must be a JSON object")
    return payload


def _build_rows(
    candidates: tuple[StrategyRecommendationResearchReadinessCandidate, ...],
    *,
    config: StrategyRecommendationResearchReadinessDigestConfig,
    generated_at: datetime,
) -> tuple[StrategyRecommendationResearchReadinessDigestRow, ...]:
    rows = tuple(
        _build_row(candidate, config=config, generated_at=generated_at)
        for candidate in candidates
    )
    return tuple(sorted(rows, key=_row_sort_key))


def _build_row(
    candidate: StrategyRecommendationResearchReadinessCandidate,
    *,
    config: StrategyRecommendationResearchReadinessDigestConfig,
    generated_at: datetime,
) -> StrategyRecommendationResearchReadinessDigestRow:
    if candidate.evidence_collected_at > generated_at:
        raise ValueError("evidence_collected_at must not be after generated_at")
    source_gap_count = max(config.minimum_source_count - candidate.source_count, ZERO)
    source_quorum_met = source_gap_count == ZERO
    evidence_age_seconds = _seconds_between(
        earlier=candidate.evidence_collected_at,
        later=generated_at,
    )
    evidence_fresh = evidence_age_seconds <= config.max_evidence_age_seconds
    rationale_complete = all(
        _has_text(value)
        for value in (
            candidate.rationale_summary,
            candidate.rationale_evidence,
            candidate.rationale_risk_notes,
        )
    )
    resolution_criteria_covered = (
        _has_text(candidate.resolution_criteria)
        and _has_text(candidate.resolution_source_name)
    )
    team_memory_feedback_available = bool(candidate.team_memory_feedback_refs)
    reason_codes = _row_reason_codes(
        source_quorum_met=source_quorum_met,
        evidence_fresh=evidence_fresh,
        rationale_complete=rationale_complete,
        resolution_criteria_covered=resolution_criteria_covered,
        team_memory_feedback_available=team_memory_feedback_available,
    )
    satisfied_criterion_count = Decimal(
        sum(
            (
                source_quorum_met,
                evidence_fresh,
                rationale_complete,
                resolution_criteria_covered,
                team_memory_feedback_available,
            ),
        ),
    )
    issue_count = CRITERION_COUNT - satisfied_criterion_count
    readiness_status = "research_ready" if issue_count == ZERO else "needs_review"

    return StrategyRecommendationResearchReadinessDigestRow(
        candidate_id=candidate.candidate_id,
        market_slug=candidate.market_slug,
        outcome_name=candidate.outcome_name,
        readiness_status=readiness_status,
        generated_at=generated_at,
        source_count=candidate.source_count,
        minimum_source_count=config.minimum_source_count,
        source_gap_count=source_gap_count,
        evidence_collected_at=candidate.evidence_collected_at,
        evidence_age_seconds=evidence_age_seconds,
        criterion_count=CRITERION_COUNT,
        satisfied_criterion_count=satisfied_criterion_count,
        issue_count=issue_count,
        readiness_ratio=_ratio_or_none(satisfied_criterion_count, CRITERION_COUNT),
        reason_codes=reason_codes,
    )


def _row_reason_codes(
    *,
    source_quorum_met: bool,
    evidence_fresh: bool,
    rationale_complete: bool,
    resolution_criteria_covered: bool,
    team_memory_feedback_available: bool,
) -> tuple[str, ...]:
    return (
        "readiness_source_quorum_met"
        if source_quorum_met
        else "readiness_source_quorum_gap",
        "readiness_evidence_fresh"
        if evidence_fresh
        else "readiness_evidence_stale",
        "readiness_rationale_complete"
        if rationale_complete
        else "readiness_rationale_incomplete",
        "readiness_resolution_criteria_covered"
        if resolution_criteria_covered
        else "readiness_resolution_criteria_missing",
        "readiness_team_memory_feedback_available"
        if team_memory_feedback_available
        else "readiness_team_memory_feedback_missing",
    )


def _digest_status(
    rows: tuple[StrategyRecommendationResearchReadinessDigestRow, ...],
) -> str:
    if not rows:
        return "blocked"
    if any(row.readiness_status == "blocked" for row in rows):
        return "blocked"
    if any(row.readiness_status == "needs_review" for row in rows):
        return "needs_review"
    return "research_ready"


def _report_reason_codes(
    rows: tuple[StrategyRecommendationResearchReadinessDigestRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return ("readiness_empty_candidates",)
    present = {code for row in rows for code in row.reason_codes}
    return tuple(code for code in REASON_CODES if code in present)


def _status_count(
    rows: tuple[StrategyRecommendationResearchReadinessDigestRow, ...],
    status: str,
) -> Decimal:
    return Decimal(sum(1 for row in rows if row.readiness_status == status))


def _criterion_count(
    rows: tuple[StrategyRecommendationResearchReadinessDigestRow, ...],
    reason_code: str,
) -> Decimal:
    return Decimal(sum(1 for row in rows if reason_code in row.reason_codes))


def _normalize_candidates(
    candidates: list[StrategyRecommendationResearchReadinessCandidate]
    | tuple[StrategyRecommendationResearchReadinessCandidate, ...],
) -> tuple[StrategyRecommendationResearchReadinessCandidate, ...]:
    if type(candidates) not in (list, tuple):
        raise ValueError("candidates must be a list or tuple")
    normalized = tuple(candidates)
    for candidate in normalized:
        if type(candidate) is not StrategyRecommendationResearchReadinessCandidate:
            raise ValueError(
                "candidates must contain "
                "StrategyRecommendationResearchReadinessCandidate values",
            )
        require_paper_only_flags("candidate", candidate)
    return normalized


def _normalize_rows(
    rows: object,
) -> tuple[StrategyRecommendationResearchReadinessDigestRow, ...]:
    if type(rows) not in (list, tuple):
        raise ValueError("rows must be a list or tuple")
    normalized = tuple(rows)
    for row in normalized:
        if type(row) is not StrategyRecommendationResearchReadinessDigestRow:
            raise ValueError(
                "rows must contain StrategyRecommendationResearchReadinessDigestRow values",
            )
        require_paper_only_flags("row", row)
    sorted_rows = tuple(sorted(normalized, key=_row_sort_key))
    if normalized != sorted_rows:
        raise ValueError("rows must use deterministic sequence")
    return normalized


def _validate_row_consistency(
    row: StrategyRecommendationResearchReadinessDigestRow,
) -> None:
    if row.source_count < row.minimum_source_count and row.source_gap_count == ZERO:
        raise ValueError("source_gap_count must reflect source_count")
    if row.source_count >= row.minimum_source_count and row.source_gap_count != ZERO:
        raise ValueError("source_gap_count must be zero when quorum is met")
    if row.satisfied_criterion_count + row.issue_count != row.criterion_count:
        raise ValueError("criterion_count must match satisfied and issue counts")
    if row.criterion_count != CRITERION_COUNT:
        raise ValueError("criterion_count must match readiness criteria")
    if row.readiness_ratio != _ratio_or_none(
        row.satisfied_criterion_count,
        row.criterion_count,
    ):
        raise ValueError("readiness_ratio must match satisfied criteria")
    if row.readiness_status == "research_ready" and row.issue_count != ZERO:
        raise ValueError("research_ready rows must have no issues")
    if row.readiness_status != "research_ready" and row.issue_count == ZERO:
        raise ValueError("non-ready rows must have issues")


def _validate_report_consistency(
    report: StrategyRecommendationResearchReadinessDigestReport,
) -> None:
    if (
        report.ready_candidate_count
        + report.needs_review_candidate_count
        + report.blocked_candidate_count
        != report.candidate_count
    ):
        raise ValueError("candidate_count must match status counts")
    if report.candidate_count != Decimal(len(report.rows)):
        raise ValueError("candidate_count must match rows")
    expected_status = _digest_status(report.rows)
    if report.digest_status != expected_status:
        raise ValueError("digest_status must match rows")
    for field_name, status in (
        ("ready_candidate_count", "research_ready"),
        ("needs_review_candidate_count", "needs_review"),
        ("blocked_candidate_count", "blocked"),
    ):
        if getattr(report, field_name) != _status_count(report.rows, status):
            raise ValueError(f"{field_name} must match rows")
    for field_name, numerator in (
        ("ready_candidate_ratio", report.ready_candidate_count),
        ("needs_review_candidate_ratio", report.needs_review_candidate_count),
        ("blocked_candidate_ratio", report.blocked_candidate_count),
    ):
        if getattr(report, field_name) != _ratio_or_none(numerator, report.candidate_count):
            raise ValueError(f"{field_name} must match candidate_count")
    for field_name, reason_code in (
        ("source_quorum_met_count", "readiness_source_quorum_met"),
        ("source_quorum_gap_count", "readiness_source_quorum_gap"),
        ("fresh_evidence_count", "readiness_evidence_fresh"),
        ("stale_evidence_count", "readiness_evidence_stale"),
        ("complete_rationale_count", "readiness_rationale_complete"),
        ("incomplete_rationale_count", "readiness_rationale_incomplete"),
        (
            "resolution_criteria_covered_count",
            "readiness_resolution_criteria_covered",
        ),
        (
            "resolution_criteria_missing_count",
            "readiness_resolution_criteria_missing",
        ),
        (
            "team_memory_feedback_available_count",
            "readiness_team_memory_feedback_available",
        ),
        (
            "team_memory_feedback_missing_count",
            "readiness_team_memory_feedback_missing",
        ),
    ):
        if getattr(report, field_name) != _criterion_count(report.rows, reason_code):
            raise ValueError(f"{field_name} must match rows")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")


def _row_sort_key(
    row: StrategyRecommendationResearchReadinessDigestRow,
) -> tuple[str, str, str]:
    return (row.candidate_id, row.market_slug, row.outcome_name)


def _ratio_or_none(numerator: Decimal, denominator: Decimal) -> Decimal | None:
    if denominator == ZERO:
        return None
    with localcontext(DECIMAL_CONTEXT):
        return _quantize_ratio(numerator / denominator)


def _normalize_optional_ratio(field_name: str, value: object) -> Decimal | None:
    if value is None:
        return None
    return _normalize_ratio(field_name, value)


def _normalize_ratio(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    normalized = _quantize_ratio(value)
    if normalized < ZERO or normalized > ONE:
        raise ValueError(f"{field_name} must be between zero and one")
    return normalized


def _normalize_decimal_whole_count(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    if value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    if value != value.to_integral_value():
        raise ValueError(f"{field_name} must be a whole-number Decimal")
    return value


def _normalize_decimal_seconds(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    if value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(SECONDS_QUANTUM)


def _quantize_ratio(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(RATIO_QUANTUM)


def _seconds_between(*, earlier: datetime, later: datetime) -> Decimal:
    delta = later - earlier
    with localcontext(DECIMAL_CONTEXT):
        return Decimal(str(delta.total_seconds())).quantize(SECONDS_QUANTUM)


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.tzinfo.utcoffset(value) is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_member(field_name: str, value: object, allowed: tuple[str, ...]) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if value not in allowed:
        raise ValueError(f"{field_name} must be one of {allowed}")


def _require_canonical_string(field_name: str, value: object) -> None:
    _require_string(field_name, value)
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")


def _require_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    _reject_unsafe_text(field_name, value)


def _normalize_string_tuple(
    field_name: str,
    values: object,
    *,
    allow_empty: bool,
) -> tuple[str, ...]:
    if isinstance(values, (str, bytes)):
        raise ValueError(f"{field_name} must be an iterable")
    try:
        normalized = tuple(values)  # type: ignore[arg-type]
    except TypeError as exc:
        raise ValueError(f"{field_name} must be an iterable") from exc
    if not allow_empty and not normalized:
        raise ValueError(f"{field_name} must not be empty")
    for value in normalized:
        _require_canonical_string(field_name, value)
    if len(set(normalized)) != len(normalized):
        raise ValueError(f"{field_name} must not contain duplicates")
    return tuple(sorted(normalized))


def _normalize_reason_codes(
    values: object,
    *,
    allow_empty: bool,
) -> tuple[str, ...]:
    if isinstance(values, (str, bytes)):
        raise ValueError("reason_codes must be an iterable")
    try:
        codes = tuple(values)  # type: ignore[arg-type]
    except TypeError as exc:
        raise ValueError("reason_codes must be an iterable") from exc
    if not allow_empty and not codes:
        raise ValueError("reason_codes must not be empty")
    for code in codes:
        _require_canonical_string("reason_codes", code)
        if code not in REASON_CODES:
            raise ValueError("reason_codes must contain known values")
    if len(set(codes)) != len(codes):
        raise ValueError("reason_codes must not contain duplicates")
    stable = tuple(code for code in REASON_CODES if code in codes)
    if codes != stable:
        raise ValueError("reason_codes must use deterministic sequence")
    return codes


def _has_text(value: str) -> bool:
    return value.strip() != ""


def _reject_flag_downgrades(label: str, value: object) -> None:
    if is_dataclass(value) and not isinstance(value, type):
        _reject_flag_downgrades(label, asdict(value))
        return
    if isinstance(value, dict):
        for field_name in PHASE_FLAG_FIELDS:
            if field_name in value and value[field_name] is not True:
                raise ValueError(f"{field_name} must be True for {label}")
        for item in value.values():
            _reject_flag_downgrades(label, item)
        return
    if isinstance(value, (list, tuple)):
        for item in value:
            _reject_flag_downgrades(label, item)


def _reject_unsafe_public_text_values(label: str, value: object) -> None:
    if is_dataclass(value) and not isinstance(value, type):
        _reject_unsafe_public_text_values(label, asdict(value))
        return
    if type(value) is str:
        _reject_unsafe_text(label, value)
        return
    if isinstance(value, dict):
        for item in value.values():
            _reject_unsafe_public_text_values(label, item)
        return
    if isinstance(value, (list, tuple)):
        for item in value:
            _reject_unsafe_public_text_values(label, item)


def _reject_unsafe_text(field_name: str, value: str) -> None:
    normalized = value.lower()
    if any(fragment in normalized for fragment in UNSAFE_SURFACE_FIELD_FRAGMENTS):
        raise ValueError(f"{field_name} contains unsafe surface text")
    if any(fragment in normalized for fragment in SENSITIVE_PUBLIC_TEXT_FRAGMENTS):
        raise ValueError(f"{field_name} contains unsafe public text")


def _json_ready(value: object) -> Any:
    if value is None:
        return None
    if isinstance(value, Decimal):
        if not value.is_finite():
            raise ValueError("JSON Decimal value must be finite")
        return str(value)
    if isinstance(value, datetime):
        utc_value = _as_utc("datetime", value)
        iso_value = utc_value.isoformat()
        if iso_value.endswith("+00:00"):
            return f"{iso_value[:-6]}Z"
        return iso_value
    if isinstance(value, float):
        raise ValueError("JSON value must not be a float")
    if isinstance(value, (str, bool)):
        return value
    if isinstance(value, dict):
        return _json_dict(value)
    if isinstance(value, (list, tuple)):
        return [_json_ready(item) for item in value]
    raise ValueError("value is not JSON serializable")


def _json_dict(value: dict[Any, Any]) -> dict[str, Any]:
    ready: dict[str, Any] = {}
    for key, item in value.items():
        if type(key) is not str:
            raise ValueError("JSON object keys must be strings")
        ready[key] = _json_ready(item)
    return ready


__all__ = (
    "DEFAULT_STRATEGY_RECOMMENDATION_RESEARCH_READINESS_DIGEST_CONFIG_VERSION",
    "StrategyRecommendationResearchReadinessCandidate",
    "StrategyRecommendationResearchReadinessDigestConfig",
    "StrategyRecommendationResearchReadinessDigestReport",
    "StrategyRecommendationResearchReadinessDigestRow",
    "build_strategy_recommendation_research_readiness_digest",
    "strategy_recommendation_research_readiness_digest_payload",
)
