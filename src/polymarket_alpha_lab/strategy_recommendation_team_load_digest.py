"""Pure Phase 1 team-load digest for strategy recommendation review."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from typing import Any

from polymarket_alpha_lab.team_paper_guard import (
    json_ready_no_floats,
    require_paper_only_flags,
)


DEFAULT_STRATEGY_RECOMMENDATION_TEAM_LOAD_DIGEST_CONFIG_VERSION = (
    "strategy-recommendation-team-load-digest-v0"
)

COUNT_QUANTUM = Decimal("1")
RATIO_QUANTUM = Decimal("0.000001")
ZERO_COUNT = Decimal("0")
ZERO_RATIO = Decimal("0.000000")
ONE_RATIO = Decimal("1.000000")
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)

EVIDENCE_CONFLICT_STATUSES = ("none", "resolved", "unresolved")
STATUSES = ("pass", "watch", "blocked")
REASON_CODES = (
    "team_load_overdue_research_backlog",
    "team_load_unresolved_evidence_conflicts",
    "team_load_category_specialization_mismatch",
    "team_load_review_capacity_overloaded",
    "team_load_digest_empty",
    "team_load_review_ready",
)
BLOCKING_REASON_CODES = (
    "team_load_overdue_research_backlog",
    "team_load_unresolved_evidence_conflicts",
)
WATCH_REASON_CODES = (
    "team_load_category_specialization_mismatch",
    "team_load_review_capacity_overloaded",
)
STATUS_WEIGHT = {
    "blocked": Decimal("2"),
    "watch": Decimal("1"),
    "pass": Decimal("0"),
}
UNSAFE_SURFACE_FIELD_FRAGMENTS = (
    "api" + "_key",
    "private" + "_key",
    "wal" + "let",
    "bro" + "ker",
    "or" + "der",
    "sig" + "nature",
    "sig" + "ning",
    "credential",
)


@dataclass(frozen=True)
class StrategyRecommendationTeamLoadDigestConfig:
    config_version: str = DEFAULT_STRATEGY_RECOMMENDATION_TEAM_LOAD_DIGEST_CONFIG_VERSION
    overdue_research_blocked_threshold_count: Decimal = Decimal("1")
    unresolved_conflict_blocked_threshold_count: Decimal = Decimal("1")
    review_capacity_overload_threshold_count: Decimal = Decimal("1")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not StrategyRecommendationTeamLoadDigestConfig:
            raise ValueError("config must be a StrategyRecommendationTeamLoadDigestConfig")
        _require_canonical_string("config_version", self.config_version)
        for field_name in (
            "overdue_research_blocked_threshold_count",
            "unresolved_conflict_blocked_threshold_count",
            "review_capacity_overload_threshold_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_positive_count(field_name, getattr(self, field_name)),
        )
        require_paper_only_flags("config", self)
        _reject_unsafe_payload_paths("config", self)


@dataclass(frozen=True)
class StrategyRecommendationTeamLoadAssignment:
    team_id: str
    candidate_id: str
    market_category: str
    assigned_at: datetime
    research_due_at: datetime
    evidence_conflict_status: str
    team_specialization_categories: tuple[str, ...]
    team_review_capacity_count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not StrategyRecommendationTeamLoadAssignment:
            raise ValueError("assignment must be a StrategyRecommendationTeamLoadAssignment")
        for field_name in ("team_id", "candidate_id", "market_category"):
            _require_canonical_string(field_name, getattr(self, field_name))
        object.__setattr__(self, "assigned_at", _as_utc("assigned_at", self.assigned_at))
        object.__setattr__(
            self,
            "research_due_at",
            _as_utc("research_due_at", self.research_due_at),
        )
        _require_member(
            "evidence_conflict_status",
            self.evidence_conflict_status,
            EVIDENCE_CONFLICT_STATUSES,
        )
        object.__setattr__(
            self,
            "team_specialization_categories",
            _normalize_string_tuple(
                "team_specialization_categories",
                self.team_specialization_categories,
                allow_empty=False,
            ),
        )
        object.__setattr__(
            self,
            "team_review_capacity_count",
            _normalize_nonnegative_count(
                "team_review_capacity_count",
                self.team_review_capacity_count,
            ),
        )
        if self.research_due_at < self.assigned_at:
            raise ValueError("research_due_at must be >= assigned_at")
        require_paper_only_flags("assignment", self)
        _reject_unsafe_payload_paths("assignment", self)


@dataclass(frozen=True)
class StrategyRecommendationTeamLoadDigestReasonCodeCount:
    reason_code: str
    count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not StrategyRecommendationTeamLoadDigestReasonCodeCount:
            raise ValueError(
                "reason code count must be a "
                "StrategyRecommendationTeamLoadDigestReasonCodeCount",
            )
        _require_member("reason_code", self.reason_code, REASON_CODES)
        object.__setattr__(
            self,
            "count",
            _normalize_positive_count("count", self.count),
        )
        require_paper_only_flags("reason code count", self)
        _reject_unsafe_payload_paths("reason code count", self)


@dataclass(frozen=True)
class StrategyRecommendationTeamLoadDigestTeamRow:
    team_id: str
    status: str
    assigned_candidate_count: Decimal
    overdue_research_count: Decimal
    unresolved_evidence_conflict_count: Decimal
    category_specialization_fit_count: Decimal
    category_specialization_mismatch_count: Decimal
    category_specialization_fit_ratio: Decimal
    review_capacity_count: Decimal
    review_capacity_headroom_count: Decimal
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not StrategyRecommendationTeamLoadDigestTeamRow:
            raise ValueError("team row must be a StrategyRecommendationTeamLoadDigestTeamRow")
        _require_canonical_string("team_id", self.team_id)
        _require_member("status", self.status, STATUSES)
        for field_name in (
            "assigned_candidate_count",
            "overdue_research_count",
            "unresolved_evidence_conflict_count",
            "category_specialization_fit_count",
            "category_specialization_mismatch_count",
            "review_capacity_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_count(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "category_specialization_fit_ratio",
            _normalize_ratio(
                "category_specialization_fit_ratio",
                self.category_specialization_fit_ratio,
            ),
        )
        object.__setattr__(
            self,
            "review_capacity_headroom_count",
            _normalize_integral_count(
                "review_capacity_headroom_count",
                self.review_capacity_headroom_count,
            ),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes, allow_empty=False),
        )
        _validate_team_row(self)
        require_paper_only_flags("team row", self)
        _reject_unsafe_payload_paths("team row", self)


@dataclass(frozen=True)
class StrategyRecommendationTeamLoadDigestReport:
    generated_at: datetime
    config_version: str
    status: str
    team_count: Decimal
    assigned_candidate_count: Decimal
    overdue_research_count: Decimal
    unresolved_evidence_conflict_count: Decimal
    category_specialization_fit_count: Decimal
    category_specialization_mismatch_count: Decimal
    category_specialization_fit_ratio: Decimal
    review_capacity_count: Decimal
    review_capacity_headroom_count: Decimal
    team_rows: tuple[StrategyRecommendationTeamLoadDigestTeamRow, ...]
    reason_code_counts: tuple[StrategyRecommendationTeamLoadDigestReasonCodeCount, ...]
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not StrategyRecommendationTeamLoadDigestReport:
            raise ValueError("report must be a StrategyRecommendationTeamLoadDigestReport")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        _require_member("status", self.status, STATUSES)
        for field_name in (
            "team_count",
            "assigned_candidate_count",
            "overdue_research_count",
            "unresolved_evidence_conflict_count",
            "category_specialization_fit_count",
            "category_specialization_mismatch_count",
            "review_capacity_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_count(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "category_specialization_fit_ratio",
            _normalize_ratio(
                "category_specialization_fit_ratio",
                self.category_specialization_fit_ratio,
            ),
        )
        object.__setattr__(
            self,
            "review_capacity_headroom_count",
            _normalize_integral_count(
                "review_capacity_headroom_count",
                self.review_capacity_headroom_count,
            ),
        )
        object.__setattr__(self, "team_rows", _normalize_team_rows(self.team_rows))
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes, allow_empty=False),
        )
        _validate_report(self)
        require_paper_only_flags("report", self)
        _reject_unsafe_payload_paths("report", self)


def build_strategy_recommendation_team_load_digest(
    inputs: object,
    *,
    config: StrategyRecommendationTeamLoadDigestConfig,
    generated_at: datetime,
) -> StrategyRecommendationTeamLoadDigestReport:
    if type(config) is not StrategyRecommendationTeamLoadDigestConfig:
        raise ValueError("config must be a StrategyRecommendationTeamLoadDigestConfig")
    require_paper_only_flags("config", config)
    _reject_unsafe_payload_paths("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    rows = _normalize_inputs(inputs, generated_at_utc)
    team_rows = _team_rows(rows, config=config, generated_at=generated_at_utc)
    reason_codes = _report_reason_codes(team_rows)
    return StrategyRecommendationTeamLoadDigestReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        status=_status(reason_codes),
        team_count=_count(len(team_rows)),
        assigned_candidate_count=_count(len(rows)),
        overdue_research_count=_sum_decimal(
            row.overdue_research_count for row in team_rows
        ),
        unresolved_evidence_conflict_count=_sum_decimal(
            row.unresolved_evidence_conflict_count for row in team_rows
        ),
        category_specialization_fit_count=_sum_decimal(
            row.category_specialization_fit_count for row in team_rows
        ),
        category_specialization_mismatch_count=_sum_decimal(
            row.category_specialization_mismatch_count for row in team_rows
        ),
        category_specialization_fit_ratio=_ratio(
            _sum_decimal(row.category_specialization_fit_count for row in team_rows),
            _count(len(rows)),
            empty_value=ONE_RATIO,
        ),
        review_capacity_count=_sum_decimal(row.review_capacity_count for row in team_rows),
        review_capacity_headroom_count=_sum_decimal(
            row.review_capacity_headroom_count for row in team_rows
        ),
        team_rows=team_rows,
        reason_code_counts=_reason_code_counts(team_rows, reason_codes),
        reason_codes=reason_codes,
    )


def strategy_recommendation_team_load_digest_payload(value: object) -> dict[str, Any]:
    if isinstance(
        value,
        (
            StrategyRecommendationTeamLoadDigestReport,
            StrategyRecommendationTeamLoadDigestTeamRow,
            StrategyRecommendationTeamLoadDigestReasonCodeCount,
            StrategyRecommendationTeamLoadDigestConfig,
            StrategyRecommendationTeamLoadAssignment,
        ),
    ):
        require_paper_only_flags("team load digest payload", value)
    elif not isinstance(value, dict):
        raise ValueError(
            "value must be a team load digest report, row, count, config, "
            "assignment, or JSON object",
        )
    _reject_unsafe_payload_paths("team load digest payload", value)
    payload = json_ready_no_floats(value)
    if not isinstance(payload, dict):
        raise ValueError("team load digest payload must be a JSON object")
    _validate_payload_hard_flags(payload, "payload", require_current_flags=True)
    _reject_unsafe_payload_paths("team load digest payload", payload)
    return payload


def _team_rows(
    rows: tuple[StrategyRecommendationTeamLoadAssignment, ...],
    *,
    config: StrategyRecommendationTeamLoadDigestConfig,
    generated_at: datetime,
) -> tuple[StrategyRecommendationTeamLoadDigestTeamRow, ...]:
    by_team: dict[str, tuple[StrategyRecommendationTeamLoadAssignment, ...]] = {}
    for row in rows:
        by_team[row.team_id] = (*by_team.get(row.team_id, ()), row)
    team_rows = tuple(
        _team_row(team_id, team_items, config=config, generated_at=generated_at)
        for team_id, team_items in by_team.items()
    )
    return tuple(sorted(team_rows, key=_team_row_sort_key))


def _team_row(
    team_id: str,
    rows: tuple[StrategyRecommendationTeamLoadAssignment, ...],
    *,
    config: StrategyRecommendationTeamLoadDigestConfig,
    generated_at: datetime,
) -> StrategyRecommendationTeamLoadDigestTeamRow:
    overdue_count = _count(
        sum(1 for row in rows if row.research_due_at < generated_at),
    )
    unresolved_conflict_count = _count(
        sum(1 for row in rows if row.evidence_conflict_status == "unresolved"),
    )
    specialization_fit_count = _count(
        sum(1 for row in rows if row.market_category in row.team_specialization_categories),
    )
    assigned_candidate_count = _count(len(rows))
    specialization_mismatch_count = assigned_candidate_count - specialization_fit_count
    capacity_count = rows[0].team_review_capacity_count
    headroom_count = capacity_count - assigned_candidate_count
    reason_codes = _row_reason_codes(
        overdue_research_count=overdue_count,
        unresolved_evidence_conflict_count=unresolved_conflict_count,
        category_specialization_mismatch_count=specialization_mismatch_count,
        review_capacity_headroom_count=headroom_count,
        config=config,
    )
    return StrategyRecommendationTeamLoadDigestTeamRow(
        team_id=team_id,
        status=_status(reason_codes),
        assigned_candidate_count=assigned_candidate_count,
        overdue_research_count=overdue_count,
        unresolved_evidence_conflict_count=unresolved_conflict_count,
        category_specialization_fit_count=specialization_fit_count,
        category_specialization_mismatch_count=specialization_mismatch_count,
        category_specialization_fit_ratio=_ratio(
            specialization_fit_count,
            assigned_candidate_count,
            empty_value=ONE_RATIO,
        ),
        review_capacity_count=capacity_count,
        review_capacity_headroom_count=headroom_count,
        reason_codes=reason_codes,
    )


def _row_reason_codes(
    *,
    overdue_research_count: Decimal,
    unresolved_evidence_conflict_count: Decimal,
    category_specialization_mismatch_count: Decimal,
    review_capacity_headroom_count: Decimal,
    config: StrategyRecommendationTeamLoadDigestConfig,
) -> tuple[str, ...]:
    reasons: list[str] = []
    if overdue_research_count >= config.overdue_research_blocked_threshold_count:
        reasons.append("team_load_overdue_research_backlog")
    if (
        unresolved_evidence_conflict_count
        >= config.unresolved_conflict_blocked_threshold_count
    ):
        reasons.append("team_load_unresolved_evidence_conflicts")
    if category_specialization_mismatch_count > ZERO_COUNT:
        reasons.append("team_load_category_specialization_mismatch")
    if (
        review_capacity_headroom_count
        <= -config.review_capacity_overload_threshold_count
    ):
        reasons.append("team_load_review_capacity_overloaded")
    return tuple(reasons) if reasons else ("team_load_review_ready",)


def _report_reason_codes(
    rows: tuple[StrategyRecommendationTeamLoadDigestTeamRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return ("team_load_digest_empty",)
    row_codes = tuple(reason_code for row in rows for reason_code in row.reason_codes)
    codes = tuple(reason_code for reason_code in REASON_CODES if reason_code in row_codes)
    return codes if codes else ("team_load_review_ready",)


def _reason_code_counts(
    rows: tuple[StrategyRecommendationTeamLoadDigestTeamRow, ...],
    reason_codes: tuple[str, ...],
) -> tuple[StrategyRecommendationTeamLoadDigestReasonCodeCount, ...]:
    if reason_codes == ("team_load_digest_empty",):
        return (
            StrategyRecommendationTeamLoadDigestReasonCodeCount(
                reason_code="team_load_digest_empty",
                count=Decimal("1"),
            ),
        )
    return tuple(
        StrategyRecommendationTeamLoadDigestReasonCodeCount(
            reason_code=reason_code,
            count=_count(sum(1 for row in rows if reason_code in row.reason_codes)),
        )
        for reason_code in REASON_CODES
        if reason_code in reason_codes
    )


def _status(reason_codes: tuple[str, ...]) -> str:
    if any(reason_code in BLOCKING_REASON_CODES for reason_code in reason_codes):
        return "blocked"
    if any(reason_code in WATCH_REASON_CODES for reason_code in reason_codes):
        return "watch"
    return "pass"


def _team_row_sort_key(
    row: StrategyRecommendationTeamLoadDigestTeamRow,
) -> tuple[Decimal, Decimal, Decimal, Decimal, str]:
    return (
        -STATUS_WEIGHT[row.status],
        -row.overdue_research_count,
        -row.unresolved_evidence_conflict_count,
        row.review_capacity_headroom_count,
        row.team_id,
    )


def _normalize_inputs(
    value: object,
    generated_at: datetime,
) -> tuple[StrategyRecommendationTeamLoadAssignment, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("inputs must be a list or tuple")
    rows = tuple(value)
    candidate_ids: set[str] = set()
    team_metadata: dict[str, tuple[tuple[str, ...], Decimal]] = {}
    for row in rows:
        if type(row) is not StrategyRecommendationTeamLoadAssignment:
            raise ValueError("inputs must contain exact team load assignments")
        require_paper_only_flags("assignment", row)
        _reject_unsafe_payload_paths("assignment", row)
        if row.assigned_at > generated_at:
            raise ValueError("assigned_at must not be after generated_at")
        if row.candidate_id in candidate_ids:
            raise ValueError("inputs must not contain duplicate candidate assignments")
        candidate_ids.add(row.candidate_id)
        metadata = (row.team_specialization_categories, row.team_review_capacity_count)
        if row.team_id in team_metadata and team_metadata[row.team_id] != metadata:
            raise ValueError("team metadata must be consistent for each team_id")
        team_metadata[row.team_id] = metadata
    return tuple(
        sorted(
            rows,
            key=lambda row: (
                row.team_id,
                row.research_due_at,
                row.candidate_id,
            ),
        ),
    )


def _normalize_team_rows(
    value: object,
) -> tuple[StrategyRecommendationTeamLoadDigestTeamRow, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("team_rows must be a list or tuple")
    rows = tuple(value)
    seen: set[str] = set()
    for row in rows:
        if type(row) is not StrategyRecommendationTeamLoadDigestTeamRow:
            raise ValueError("team_rows must contain exact team rows")
        require_paper_only_flags("team row", row)
        if row.team_id in seen:
            raise ValueError("team_rows must not contain duplicate team_id values")
        seen.add(row.team_id)
    if tuple(sorted(rows, key=_team_row_sort_key)) != rows:
        raise ValueError("team_rows must use stable sort")
    return rows


def _normalize_reason_code_counts(
    value: object,
) -> tuple[StrategyRecommendationTeamLoadDigestReasonCodeCount, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("reason_code_counts must be a list or tuple")
    rows = tuple(value)
    seen: set[str] = set()
    for row in rows:
        if type(row) is not StrategyRecommendationTeamLoadDigestReasonCodeCount:
            raise ValueError("reason_code_counts must contain exact reason code counts")
        require_paper_only_flags("reason code count", row)
        if row.reason_code in seen:
            raise ValueError("reason_code_counts must not contain duplicate reason codes")
        seen.add(row.reason_code)
    if tuple(sorted(rows, key=lambda row: REASON_CODES.index(row.reason_code))) != rows:
        raise ValueError("reason_code_counts must use stable sort")
    return rows


def _validate_team_row(row: StrategyRecommendationTeamLoadDigestTeamRow) -> None:
    if (
        row.category_specialization_fit_count
        + row.category_specialization_mismatch_count
        != row.assigned_candidate_count
    ):
        raise ValueError("assigned_candidate_count must match specialization counts")
    if row.overdue_research_count > row.assigned_candidate_count:
        raise ValueError("overdue_research_count must not exceed assigned_candidate_count")
    if row.unresolved_evidence_conflict_count > row.assigned_candidate_count:
        raise ValueError(
            "unresolved_evidence_conflict_count must not exceed assigned_candidate_count",
        )
    if row.review_capacity_headroom_count != (
        row.review_capacity_count - row.assigned_candidate_count
    ):
        raise ValueError("review_capacity_headroom_count must match capacity minus load")
    expected_ratio = _ratio(
        row.category_specialization_fit_count,
        row.assigned_candidate_count,
        empty_value=ONE_RATIO,
    )
    if row.category_specialization_fit_ratio != expected_ratio:
        raise ValueError("category_specialization_fit_ratio must match counts")
    if row.status != _status(row.reason_codes):
        raise ValueError("status must match reason_codes")


def _validate_report(report: StrategyRecommendationTeamLoadDigestReport) -> None:
    if report.team_count != _count(len(report.team_rows)):
        raise ValueError("team_count must match team_rows")
    if report.assigned_candidate_count != _sum_decimal(
        row.assigned_candidate_count for row in report.team_rows
    ):
        raise ValueError("assigned_candidate_count must match team_rows")
    if report.overdue_research_count != _sum_decimal(
        row.overdue_research_count for row in report.team_rows
    ):
        raise ValueError("overdue_research_count must match team_rows")
    if report.unresolved_evidence_conflict_count != _sum_decimal(
        row.unresolved_evidence_conflict_count for row in report.team_rows
    ):
        raise ValueError("unresolved_evidence_conflict_count must match team_rows")
    if report.category_specialization_fit_count != _sum_decimal(
        row.category_specialization_fit_count for row in report.team_rows
    ):
        raise ValueError("category_specialization_fit_count must match team_rows")
    if report.category_specialization_mismatch_count != _sum_decimal(
        row.category_specialization_mismatch_count for row in report.team_rows
    ):
        raise ValueError("category_specialization_mismatch_count must match team_rows")
    if report.review_capacity_count != _sum_decimal(
        row.review_capacity_count for row in report.team_rows
    ):
        raise ValueError("review_capacity_count must match team_rows")
    if report.review_capacity_headroom_count != _sum_decimal(
        row.review_capacity_headroom_count for row in report.team_rows
    ):
        raise ValueError("review_capacity_headroom_count must match team_rows")
    expected_ratio = _ratio(
        report.category_specialization_fit_count,
        report.assigned_candidate_count,
        empty_value=ONE_RATIO,
    )
    if report.category_specialization_fit_ratio != expected_ratio:
        raise ValueError("category_specialization_fit_ratio must match counts")
    if report.reason_codes != _report_reason_codes(report.team_rows):
        raise ValueError("reason_codes must match team_rows")
    if report.reason_code_counts != _reason_code_counts(
        report.team_rows,
        report.reason_codes,
    ):
        raise ValueError("reason_code_counts must match reason_codes")
    if report.status != _status(report.reason_codes):
        raise ValueError("status must match reason_codes")


def _validate_payload_hard_flags(
    value: object,
    field_name: str,
    *,
    require_current_flags: bool,
) -> None:
    if isinstance(value, dict):
        has_any_flag = any(
            flag_name in value for flag_name in ("paper_only", "report_only", "readonly")
        )
        if require_current_flags or has_any_flag:
            for flag_name in ("paper_only", "report_only", "readonly"):
                if value.get(flag_name) is not True:
                    raise ValueError(f"{field_name} {flag_name} must be true")
        for key, item in value.items():
            _validate_payload_hard_flags(
                item,
                f"{field_name}.{key}",
                require_current_flags=False,
            )
    elif isinstance(value, list):
        for index, item in enumerate(value):
            _validate_payload_hard_flags(
                item,
                f"{field_name}.{index}",
                require_current_flags=False,
            )


def _reject_unsafe_payload_paths(label: str, value: object) -> None:
    for key in _iter_payload_keys(value):
        normalized_key = key.lower()
        if any(fragment in normalized_key for fragment in UNSAFE_SURFACE_FIELD_FRAGMENTS):
            raise ValueError(f"unsafe live surface field in {label}: {key}")


def _iter_payload_keys(value: object) -> tuple[str, ...]:
    if hasattr(value, "__dataclass_fields__") and not isinstance(value, type):
        keys: list[str] = []
        for field_name in value.__dataclass_fields__:  # type: ignore[attr-defined]
            keys.append(field_name)
            keys.extend(_iter_payload_keys(getattr(value, field_name)))
        return tuple(keys)
    if isinstance(value, dict):
        keys = []
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            keys.append(key)
            keys.extend(_iter_payload_keys(item))
        return tuple(keys)
    if isinstance(value, (list, tuple)):
        keys = []
        for item in value:
            keys.extend(_iter_payload_keys(item))
        return tuple(keys)
    return ()


def _sum_decimal(values: object) -> Decimal:
    total = ZERO_COUNT
    for value in values:  # type: ignore[union-attr]
        total += value
    return _normalize_integral_count("total", total)


def _ratio(numerator: Decimal, denominator: Decimal, *, empty_value: Decimal) -> Decimal:
    if denominator == ZERO_COUNT:
        return empty_value
    with localcontext(DECIMAL_CONTEXT):
        return _normalize_ratio("ratio", numerator / denominator)


def _count(value: int) -> Decimal:
    return Decimal(value).quantize(COUNT_QUANTUM)


def _normalize_positive_count(field_name: str, value: object) -> Decimal:
    normalized = _normalize_nonnegative_count(field_name, value)
    if normalized <= ZERO_COUNT:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _normalize_nonnegative_count(field_name: str, value: object) -> Decimal:
    normalized = _normalize_integral_count(field_name, value)
    if normalized < ZERO_COUNT:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _normalize_integral_count(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    quantized = value.quantize(COUNT_QUANTUM)
    if quantized != value:
        raise ValueError(f"{field_name} must be integral")
    return quantized


def _normalize_ratio(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    if value < ZERO_RATIO or value > ONE_RATIO:
        raise ValueError(f"{field_name} must be between 0 and 1")
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(RATIO_QUANTUM)


def _normalize_string_tuple(
    field_name: str,
    value: object,
    *,
    allow_empty: bool,
) -> tuple[str, ...]:
    if type(value) not in (list, tuple):
        raise ValueError(f"{field_name} must be a list or tuple")
    items = tuple(value)
    if not allow_empty and not items:
        raise ValueError(f"{field_name} must not be empty")
    for item in items:
        _require_canonical_string(field_name, item)
    if len(set(items)) != len(items):
        raise ValueError(f"{field_name} must be unique")
    if tuple(sorted(items)) != items:
        raise ValueError(f"{field_name} must be sorted")
    return items


def _normalize_reason_codes(
    value: object,
    *,
    allow_empty: bool,
) -> tuple[str, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("reason_codes must be a list or tuple")
    reason_codes = tuple(value)
    if not allow_empty and not reason_codes:
        raise ValueError("reason_codes must not be empty")
    for reason_code in reason_codes:
        _require_member("reason_codes", reason_code, REASON_CODES)
    if len(set(reason_codes)) != len(reason_codes):
        raise ValueError("reason_codes must be unique")
    if tuple(code for code in REASON_CODES if code in reason_codes) != reason_codes:
        raise ValueError("reason_codes must use stable sort")
    return reason_codes


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_member(field_name: str, value: object, allowed: tuple[str, ...]) -> None:
    if type(value) is not str or value not in allowed:
        raise ValueError(f"{field_name} must be one of: {', '.join(allowed)}")


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")


__all__ = (
    "DEFAULT_STRATEGY_RECOMMENDATION_TEAM_LOAD_DIGEST_CONFIG_VERSION",
    "EVIDENCE_CONFLICT_STATUSES",
    "REASON_CODES",
    "STATUSES",
    "StrategyRecommendationTeamLoadAssignment",
    "StrategyRecommendationTeamLoadDigestConfig",
    "StrategyRecommendationTeamLoadDigestReasonCodeCount",
    "StrategyRecommendationTeamLoadDigestReport",
    "StrategyRecommendationTeamLoadDigestTeamRow",
    "build_strategy_recommendation_team_load_digest",
    "strategy_recommendation_team_load_digest_payload",
)
