"""Pure report-only policy for planning local team-memory retrieval.

Callers provide already-redacted memory-retrieval needs. This module only scores
whether the research team has enough local memory coverage to proceed; it never
connects to an external service or storage backend.
"""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable
from dataclasses import asdict, dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation
from typing import Any


__all__ = (
    "DEFAULT_RESEARCH_TEAM_MEMORY_RETRIEVAL_POLICY_CONFIG_VERSION",
    "ResearchTeamMemoryRetrievalNeed",
    "ResearchTeamMemoryRetrievalPolicyConfig",
    "ResearchTeamMemoryRetrievalPolicyReasonCodeCount",
    "ResearchTeamMemoryRetrievalPolicyReport",
    "ResearchTeamMemoryRetrievalScoreRow",
    "build_research_team_memory_retrieval_policy_report",
    "research_team_memory_retrieval_policy_payload",
)


DEFAULT_RESEARCH_TEAM_MEMORY_RETRIEVAL_POLICY_CONFIG_VERSION = (
    "research-team-memory-retrieval-policy-v0"
)
RETRIEVAL_LANES = (
    "domain",
    "event_type",
    "similar_history",
    "calibration_review",
    "conflict_case",
)
STATUSES = ("pass", "watch", "block")
ZERO = Decimal("0")
ONE = Decimal("1")
RATIO_QUANTUM = Decimal("0.000001")
DEFAULT_PASS_READINESS_SCORE = Decimal("0.800000")
DEFAULT_WATCH_READINESS_SCORE = Decimal("0.550000")
LANE_WEIGHT_BY_FIELD = {
    "domain": "domain_lane_weight",
    "event_type": "event_type_lane_weight",
    "similar_history": "similar_history_lane_weight",
    "calibration_review": "calibration_review_lane_weight",
    "conflict_case": "conflict_case_lane_weight",
}
UNSAFE_PUBLIC_TERMS = (
    "dsn",
    "database_url",
    "postgres://",
    "postgresql://",
    "supabase.co",
    "raw_source",
    "raw-source",
    "raw source",
    "source_id",
    "source-id",
    "market_id",
    "market-id",
    "market_slug",
    "market-slug",
    "market-",
    "token",
    "secret",
    "api_key",
    "authorization",
    "bearer",
)


@dataclass(frozen=True)
class ResearchTeamMemoryRetrievalPolicyConfig:
    config_version: str = DEFAULT_RESEARCH_TEAM_MEMORY_RETRIEVAL_POLICY_CONFIG_VERSION
    pass_readiness_score: Decimal = DEFAULT_PASS_READINESS_SCORE
    watch_readiness_score: Decimal = DEFAULT_WATCH_READINESS_SCORE
    coverage_weight: Decimal = Decimal("0.500000")
    freshness_weight: Decimal = Decimal("0.250000")
    semantic_similarity_weight: Decimal = Decimal("0.250000")
    domain_lane_weight: Decimal = Decimal("0.200000")
    event_type_lane_weight: Decimal = Decimal("0.200000")
    similar_history_lane_weight: Decimal = Decimal("0.200000")
    calibration_review_lane_weight: Decimal = Decimal("0.200000")
    conflict_case_lane_weight: Decimal = Decimal("0.200000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchTeamMemoryRetrievalPolicyConfig, "config")
        _require_public_identifier("config_version", self.config_version)
        if self.config_version != DEFAULT_RESEARCH_TEAM_MEMORY_RETRIEVAL_POLICY_CONFIG_VERSION:
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "pass_readiness_score",
            "watch_readiness_score",
            "coverage_weight",
            "freshness_weight",
            "semantic_similarity_weight",
            "domain_lane_weight",
            "event_type_lane_weight",
            "similar_history_lane_weight",
            "calibration_review_lane_weight",
            "conflict_case_lane_weight",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_probability_decimal(field_name, getattr(self, field_name)),
            )
        if self.pass_readiness_score <= self.watch_readiness_score:
            raise ValueError("pass_readiness_score must exceed watch_readiness_score")
        score_weight_sum = _quantize(
            self.coverage_weight
            + self.freshness_weight
            + self.semantic_similarity_weight,
        )
        if score_weight_sum != ONE:
            raise ValueError(
                "coverage_weight, freshness_weight, and "
                "semantic_similarity_weight must sum to 1",
            )
        lane_weight_sum = _quantize(
            self.domain_lane_weight
            + self.event_type_lane_weight
            + self.similar_history_lane_weight
            + self.calibration_review_lane_weight
            + self.conflict_case_lane_weight,
        )
        if lane_weight_sum != ONE:
            raise ValueError("retrieval lane weights must sum to 1")
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class ResearchTeamMemoryRetrievalNeed:
    brief_id: str
    retrieval_lane: str
    query_intent_id: str
    retrieval_goal: str
    required_memory_count: Decimal
    available_memory_count: Decimal
    freshness_score: Decimal
    semantic_similarity_score: Decimal
    redaction_confirmed: bool = True
    reason_codes: tuple[str, ...] = ()
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchTeamMemoryRetrievalNeed, "need")
        for field_name in ("brief_id", "query_intent_id"):
            _require_public_identifier(field_name, getattr(self, field_name))
            _reject_unsafe_public_text(field_name, getattr(self, field_name))
        _require_enum("retrieval_lane", self.retrieval_lane, RETRIEVAL_LANES)
        object.__setattr__(
            self,
            "retrieval_goal",
            _require_public_text("retrieval_goal", self.retrieval_goal),
        )
        for field_name in ("required_memory_count", "available_memory_count"):
            object.__setattr__(
                self,
                field_name,
                (
                    _require_positive_whole_decimal
                    if field_name == "required_memory_count"
                    else _require_nonnegative_whole_decimal
                )(field_name, getattr(self, field_name)),
            )
        for field_name in ("freshness_score", "semantic_similarity_score"):
            object.__setattr__(
                self,
                field_name,
                _require_probability_decimal(field_name, getattr(self, field_name)),
            )
        if type(self.redaction_confirmed) is not bool:
            raise ValueError("redaction_confirmed must be a bool")
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, allow_empty=True),
        )
        _require_hard_flags("need", self)


@dataclass(frozen=True)
class ResearchTeamMemoryRetrievalScoreRow:
    brief_id: str
    required_lane_count: Decimal
    planned_lane_count: Decimal
    missing_lane_count: Decimal
    total_required_memory_count: Decimal
    total_available_memory_count: Decimal
    domain_memory_count: Decimal
    event_type_memory_count: Decimal
    similar_history_memory_count: Decimal
    calibration_review_memory_count: Decimal
    conflict_case_memory_count: Decimal
    domain_lane_score: Decimal
    event_type_lane_score: Decimal
    similar_history_lane_score: Decimal
    calibration_review_lane_score: Decimal
    conflict_case_lane_score: Decimal
    memory_readiness_score: Decimal
    pass_readiness_score: Decimal
    watch_readiness_score: Decimal
    status: str
    retrieval_lanes: tuple[str, ...]
    query_intent_ids: tuple[str, ...]
    reason_codes: tuple[str, ...]
    redaction_issue_count: Decimal = ZERO
    domain_lane_weight: Decimal = Decimal("0.200000")
    event_type_lane_weight: Decimal = Decimal("0.200000")
    similar_history_lane_weight: Decimal = Decimal("0.200000")
    calibration_review_lane_weight: Decimal = Decimal("0.200000")
    conflict_case_lane_weight: Decimal = Decimal("0.200000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchTeamMemoryRetrievalScoreRow, "row")
        _require_public_identifier("brief_id", self.brief_id)
        for field_name in (
            "required_lane_count",
            "planned_lane_count",
            "missing_lane_count",
            "total_required_memory_count",
            "total_available_memory_count",
            "domain_memory_count",
            "event_type_memory_count",
            "similar_history_memory_count",
            "calibration_review_memory_count",
            "conflict_case_memory_count",
            "redaction_issue_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_whole_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "domain_lane_score",
            "event_type_lane_score",
            "similar_history_lane_score",
            "calibration_review_lane_score",
            "conflict_case_lane_score",
            "memory_readiness_score",
            "pass_readiness_score",
            "watch_readiness_score",
            "domain_lane_weight",
            "event_type_lane_weight",
            "similar_history_lane_weight",
            "calibration_review_lane_weight",
            "conflict_case_lane_weight",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_probability_decimal(field_name, getattr(self, field_name)),
            )
        if self.pass_readiness_score <= self.watch_readiness_score:
            raise ValueError("pass_readiness_score must exceed watch_readiness_score")
        lane_weight_sum = _quantize(
            self.domain_lane_weight
            + self.event_type_lane_weight
            + self.similar_history_lane_weight
            + self.calibration_review_lane_weight
            + self.conflict_case_lane_weight,
        )
        if lane_weight_sum != ONE:
            raise ValueError("retrieval lane weights must sum to 1")
        _require_status("status", self.status)
        object.__setattr__(
            self,
            "retrieval_lanes",
            _normalize_lane_tuple("retrieval_lanes", self.retrieval_lanes),
        )
        object.__setattr__(
            self,
            "query_intent_ids",
            _normalize_public_identifier_tuple("query_intent_ids", self.query_intent_ids),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, allow_empty=False),
        )
        _require_hard_flags("row", self)
        _validate_score_row_consistency(self)


@dataclass(frozen=True)
class ResearchTeamMemoryRetrievalPolicyReasonCodeCount:
    reason_code: str
    count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchTeamMemoryRetrievalPolicyReasonCodeCount,
            "reason_code_count",
        )
        _require_reason_code("reason_code", self.reason_code)
        object.__setattr__(
            self,
            "count",
            _require_positive_whole_decimal("count", self.count),
        )
        _require_hard_flags("reason_code_count", self)


@dataclass(frozen=True)
class ResearchTeamMemoryRetrievalPolicyReport:
    generated_at: datetime
    config_version: str
    brief_count: Decimal
    need_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    average_memory_readiness_score: Decimal | None
    status: str
    rows: tuple[ResearchTeamMemoryRetrievalScoreRow, ...]
    reason_code_counts: tuple[ResearchTeamMemoryRetrievalPolicyReasonCodeCount, ...]
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchTeamMemoryRetrievalPolicyReport, "report")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_identifier("config_version", self.config_version)
        for field_name in (
            "brief_count",
            "need_count",
            "pass_count",
            "watch_count",
            "block_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_whole_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "average_memory_readiness_score",
            _require_optional_probability_decimal(
                "average_memory_readiness_score",
                self.average_memory_readiness_score,
            ),
        )
        _require_status("status", self.status)
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, allow_empty=False),
        )
        _require_hard_flags("report", self)
        _validate_report_consistency(self)


def build_research_team_memory_retrieval_policy_report(
    memory_needs: Iterable[object],
    *,
    config: ResearchTeamMemoryRetrievalPolicyConfig,
    generated_at: datetime,
) -> ResearchTeamMemoryRetrievalPolicyReport:
    if type(config) is not ResearchTeamMemoryRetrievalPolicyConfig:
        raise ValueError("config must be a ResearchTeamMemoryRetrievalPolicyConfig")
    _require_hard_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    needs = _normalize_needs(memory_needs)
    grouped: dict[str, list[ResearchTeamMemoryRetrievalNeed]] = {}
    for item in needs:
        grouped.setdefault(item.brief_id, []).append(item)

    rows = tuple(
        _score_row_from_brief(
            brief_id=brief_id,
            needs=tuple(grouped[brief_id]),
            config=config,
        )
        for brief_id in sorted(grouped)
    )
    reason_codes = _summary_reason_codes(rows)

    return ResearchTeamMemoryRetrievalPolicyReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        brief_count=_decimal_count(len(rows)),
        need_count=_decimal_count(len(needs)),
        pass_count=_decimal_count(_status_count(rows, "pass")),
        watch_count=_decimal_count(_status_count(rows, "watch")),
        block_count=_decimal_count(_status_count(rows, "block")),
        average_memory_readiness_score=_average_memory_readiness_score(rows),
        status=_summary_status(reason_codes),
        rows=rows,
        reason_code_counts=_reason_code_counts(rows, reason_codes),
        reason_codes=reason_codes,
    )


def research_team_memory_retrieval_policy_payload(
    report: ResearchTeamMemoryRetrievalPolicyReport,
) -> dict[str, Any]:
    if type(report) is not ResearchTeamMemoryRetrievalPolicyReport:
        raise ValueError("report must be a ResearchTeamMemoryRetrievalPolicyReport")
    _require_hard_flags("report", report)
    payload = _payload_value(report)
    if not isinstance(payload, dict):
        raise ValueError("report payload must be a JSON object")
    _reject_unsafe_public_payload(payload)
    return payload


def _score_row_from_brief(
    *,
    brief_id: str,
    needs: tuple[ResearchTeamMemoryRetrievalNeed, ...],
    config: ResearchTeamMemoryRetrievalPolicyConfig,
) -> ResearchTeamMemoryRetrievalScoreRow:
    by_lane: dict[str, ResearchTeamMemoryRetrievalNeed] = {}
    for item in sorted(needs, key=lambda need: (need.retrieval_lane, need.query_intent_id)):
        if item.retrieval_lane in by_lane:
            raise ValueError("duplicate retrieval_lane for brief_id")
        by_lane[item.retrieval_lane] = item

    lane_scores = {
        lane: _lane_score(by_lane[lane], config) if lane in by_lane else ZERO
        for lane in RETRIEVAL_LANES
    }
    missing_lanes = tuple(lane for lane in RETRIEVAL_LANES if lane not in by_lane)
    readiness_score = _memory_readiness_score(lane_scores, config)
    redaction_issue_count = sum(1 for item in needs if not item.redaction_confirmed)
    status = _row_status(
        readiness_score=readiness_score,
        missing_lane_count=len(missing_lanes),
        redaction_issue_count=redaction_issue_count,
        config=config,
    )

    return ResearchTeamMemoryRetrievalScoreRow(
        brief_id=brief_id,
        required_lane_count=_decimal_count(len(RETRIEVAL_LANES)),
        planned_lane_count=_decimal_count(len(by_lane)),
        missing_lane_count=_decimal_count(len(missing_lanes)),
        total_required_memory_count=sum(
            (item.required_memory_count for item in needs),
            ZERO,
        ),
        total_available_memory_count=sum(
            (item.available_memory_count for item in needs),
            ZERO,
        ),
        domain_memory_count=_available_memory_count(by_lane, "domain"),
        event_type_memory_count=_available_memory_count(by_lane, "event_type"),
        similar_history_memory_count=_available_memory_count(by_lane, "similar_history"),
        calibration_review_memory_count=_available_memory_count(
            by_lane,
            "calibration_review",
        ),
        conflict_case_memory_count=_available_memory_count(by_lane, "conflict_case"),
        domain_lane_score=lane_scores["domain"],
        event_type_lane_score=lane_scores["event_type"],
        similar_history_lane_score=lane_scores["similar_history"],
        calibration_review_lane_score=lane_scores["calibration_review"],
        conflict_case_lane_score=lane_scores["conflict_case"],
        memory_readiness_score=readiness_score,
        pass_readiness_score=config.pass_readiness_score,
        watch_readiness_score=config.watch_readiness_score,
        status=status,
        retrieval_lanes=tuple(sorted(by_lane)),
        query_intent_ids=tuple(sorted(item.query_intent_id for item in needs)),
        reason_codes=_row_reason_codes(
            status=status,
            missing_lanes=missing_lanes,
            redaction_issue_count=redaction_issue_count,
            input_reason_codes=tuple(
                reason_code for item in needs for reason_code in item.reason_codes
            ),
        ),
        redaction_issue_count=_decimal_count(redaction_issue_count),
        domain_lane_weight=config.domain_lane_weight,
        event_type_lane_weight=config.event_type_lane_weight,
        similar_history_lane_weight=config.similar_history_lane_weight,
        calibration_review_lane_weight=config.calibration_review_lane_weight,
        conflict_case_lane_weight=config.conflict_case_lane_weight,
    )


def _lane_score(
    need: ResearchTeamMemoryRetrievalNeed,
    config: ResearchTeamMemoryRetrievalPolicyConfig,
) -> Decimal:
    coverage_score = _coverage_score(
        need.available_memory_count,
        need.required_memory_count,
    )
    return _quantize(
        coverage_score * config.coverage_weight
        + need.freshness_score * config.freshness_weight
        + need.semantic_similarity_score * config.semantic_similarity_weight,
    )


def _coverage_score(available_count: Decimal, required_count: Decimal) -> Decimal:
    if required_count <= ZERO:
        raise ValueError("required_count must be positive")
    return _quantize(min(available_count / required_count, ONE))


def _memory_readiness_score(
    lane_scores: dict[str, Decimal],
    config: ResearchTeamMemoryRetrievalPolicyConfig,
) -> Decimal:
    return _quantize(
        sum(
            lane_scores[lane] * getattr(config, LANE_WEIGHT_BY_FIELD[lane])
            for lane in RETRIEVAL_LANES
        ),
    )


def _available_memory_count(
    by_lane: dict[str, ResearchTeamMemoryRetrievalNeed],
    lane: str,
) -> Decimal:
    if lane not in by_lane:
        return ZERO
    return by_lane[lane].available_memory_count


def _row_status(
    *,
    readiness_score: Decimal,
    missing_lane_count: int,
    redaction_issue_count: int,
    config: ResearchTeamMemoryRetrievalPolicyConfig,
) -> str:
    if missing_lane_count > 0 or redaction_issue_count > 0:
        return "block"
    if readiness_score >= config.pass_readiness_score:
        return "pass"
    if readiness_score >= config.watch_readiness_score:
        return "watch"
    return "block"


def _row_reason_codes(
    *,
    status: str,
    missing_lanes: tuple[str, ...],
    redaction_issue_count: int,
    input_reason_codes: tuple[str, ...],
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    if not missing_lanes:
        reason_codes.extend(
            (
                "all_memory_lanes_planned",
                "calibration_reviews_available",
                "conflict_cases_available",
                "local_memory_queries_planned",
            ),
        )
    for lane in missing_lanes:
        reason_codes.append(f"missing_{lane}_memory")
    if redaction_issue_count:
        reason_codes.append("memory_redaction_not_confirmed")
    reason_codes.extend(f"input_{reason_code}" for reason_code in input_reason_codes)
    reason_codes.append(f"research_team_memory_retrieval_{status}")
    return _normalize_reason_codes("reason_codes", tuple(reason_codes), allow_empty=False)


def _summary_reason_codes(
    rows: tuple[ResearchTeamMemoryRetrievalScoreRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return ("no_memory_retrieval_needs",)
    if any(row.status == "block" for row in rows):
        return ("research_team_memory_retrieval_block",)
    if any(row.status == "watch" for row in rows):
        return ("research_team_memory_retrieval_watch",)
    return ("research_team_memory_retrieval_pass",)


def _summary_status(reason_codes: tuple[str, ...]) -> str:
    if "research_team_memory_retrieval_block" in reason_codes:
        return "block"
    if "research_team_memory_retrieval_watch" in reason_codes:
        return "watch"
    if "research_team_memory_retrieval_pass" in reason_codes:
        return "pass"
    return "block"


def _status_count(rows: tuple[ResearchTeamMemoryRetrievalScoreRow, ...], status: str) -> int:
    return sum(1 for row in rows if row.status == status)


def _average_memory_readiness_score(
    rows: tuple[ResearchTeamMemoryRetrievalScoreRow, ...],
) -> Decimal | None:
    if not rows:
        return None
    return _quantize(
        sum((row.memory_readiness_score for row in rows), ZERO) / Decimal(len(rows)),
    )


def _reason_code_counts(
    rows: tuple[ResearchTeamMemoryRetrievalScoreRow, ...],
    summary_reason_codes: tuple[str, ...],
) -> tuple[ResearchTeamMemoryRetrievalPolicyReasonCodeCount, ...]:
    counter: Counter[str] = Counter(summary_reason_codes)
    for row in rows:
        counter.update(row.reason_codes)
    return tuple(
        ResearchTeamMemoryRetrievalPolicyReasonCodeCount(
            reason_code=reason_code,
            count=_decimal_count(counter[reason_code]),
        )
        for reason_code in sorted(counter)
    )


def _normalize_needs(
    memory_needs: Iterable[object],
) -> tuple[ResearchTeamMemoryRetrievalNeed, ...]:
    if isinstance(memory_needs, (str, bytes)):
        raise ValueError("memory_needs must be an iterable")
    try:
        values = tuple(memory_needs)
    except TypeError as exc:
        raise ValueError("memory_needs must be an iterable") from exc
    return tuple(_coerce_need(value) for value in values)


def _coerce_need(value: object) -> ResearchTeamMemoryRetrievalNeed:
    if type(value) is ResearchTeamMemoryRetrievalNeed:
        return value
    if is_dataclass(value):
        try:
            return ResearchTeamMemoryRetrievalNeed(
                brief_id=getattr(value, "brief_id"),
                retrieval_lane=getattr(value, "retrieval_lane"),
                query_intent_id=getattr(value, "query_intent_id"),
                retrieval_goal=getattr(value, "retrieval_goal"),
                required_memory_count=getattr(value, "required_memory_count"),
                available_memory_count=getattr(value, "available_memory_count"),
                freshness_score=getattr(value, "freshness_score"),
                semantic_similarity_score=getattr(value, "semantic_similarity_score"),
                redaction_confirmed=getattr(value, "redaction_confirmed"),
                reason_codes=getattr(value, "reason_codes"),
                paper_only=getattr(value, "paper_only"),
                report_only=getattr(value, "report_only"),
                readonly=getattr(value, "readonly"),
            )
        except AttributeError as exc:
            raise ValueError("memory_needs must contain compatible dataclass rows") from exc
    raise ValueError("memory_needs must contain ResearchTeamMemoryRetrievalNeed")


def _normalize_rows(
    rows: object,
) -> tuple[ResearchTeamMemoryRetrievalScoreRow, ...]:
    if type(rows) is not tuple:
        raise ValueError("rows must be a tuple")
    for row in rows:
        if type(row) is not ResearchTeamMemoryRetrievalScoreRow:
            raise ValueError("rows must contain ResearchTeamMemoryRetrievalScoreRow")
    return tuple(sorted(rows, key=lambda row: row.brief_id))


def _normalize_reason_code_counts(
    values: object,
) -> tuple[ResearchTeamMemoryRetrievalPolicyReasonCodeCount, ...]:
    if type(values) is not tuple:
        raise ValueError("reason_code_counts must be a tuple")
    for value in values:
        if type(value) is not ResearchTeamMemoryRetrievalPolicyReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "ResearchTeamMemoryRetrievalPolicyReasonCodeCount",
            )
    return tuple(sorted(values, key=lambda item: item.reason_code))


def _normalize_public_identifier_tuple(
    field_name: str,
    values: object,
) -> tuple[str, ...]:
    if type(values) is not tuple:
        raise ValueError(f"{field_name} must be a tuple")
    normalized: list[str] = []
    for value in values:
        _require_public_identifier(field_name, value)
        _reject_unsafe_public_text(field_name, value)
        normalized.append(value)
    return tuple(sorted(set(normalized)))


def _normalize_lane_tuple(field_name: str, values: object) -> tuple[str, ...]:
    if type(values) is not tuple:
        raise ValueError(f"{field_name} must be a tuple")
    normalized: list[str] = []
    for value in values:
        _require_enum(field_name, value, RETRIEVAL_LANES)
        normalized.append(value)
    return tuple(sorted(set(normalized)))


def _normalize_reason_codes(
    field_name: str,
    values: object,
    *,
    allow_empty: bool,
) -> tuple[str, ...]:
    if type(values) is not tuple:
        raise ValueError(f"{field_name} must be a tuple")
    normalized: list[str] = []
    for value in values:
        _require_reason_code(field_name, value)
        normalized.append(value)
    if not allow_empty and not normalized:
        raise ValueError(f"{field_name} must be nonempty")
    return tuple(sorted(set(normalized)))


def _validate_score_row_consistency(
    row: ResearchTeamMemoryRetrievalScoreRow,
) -> None:
    if row.required_lane_count != _decimal_count(len(RETRIEVAL_LANES)):
        raise ValueError("required_lane_count must match policy retrieval lanes")
    if row.planned_lane_count != _decimal_count(len(row.retrieval_lanes)):
        raise ValueError("planned_lane_count must match retrieval_lanes")
    if row.missing_lane_count != row.required_lane_count - row.planned_lane_count:
        raise ValueError("missing_lane_count must match retrieval_lanes")
    if row.total_available_memory_count != (
        row.domain_memory_count
        + row.event_type_memory_count
        + row.similar_history_memory_count
        + row.calibration_review_memory_count
        + row.conflict_case_memory_count
    ):
        raise ValueError("total_available_memory_count must match lane memory counts")
    expected_score = _quantize(
        row.domain_lane_score * row.domain_lane_weight
        + row.event_type_lane_score * row.event_type_lane_weight
        + row.similar_history_lane_score * row.similar_history_lane_weight
        + row.calibration_review_lane_score * row.calibration_review_lane_weight
        + row.conflict_case_lane_score * row.conflict_case_lane_weight,
    )
    if row.memory_readiness_score != expected_score:
        raise ValueError("memory_readiness_score must match lane scores")
    expected_status = _manual_row_status(row)
    if row.status != expected_status:
        raise ValueError("status must match memory_readiness_score")
    if (
        row.redaction_issue_count > ZERO
        and "memory_redaction_not_confirmed" not in row.reason_codes
    ):
        raise ValueError("reason_codes must include redaction issue")
    if f"research_team_memory_retrieval_{row.status}" not in row.reason_codes:
        raise ValueError("reason_codes must include row status")


def _manual_row_status(row: ResearchTeamMemoryRetrievalScoreRow) -> str:
    if row.missing_lane_count > ZERO or _manual_redaction_issue_count(row) > ZERO:
        return "block"
    if row.memory_readiness_score >= row.pass_readiness_score:
        return "pass"
    if row.memory_readiness_score >= row.watch_readiness_score:
        return "watch"
    return "block"


def _manual_redaction_issue_count(row: ResearchTeamMemoryRetrievalScoreRow) -> Decimal:
    if row.redaction_issue_count > ZERO:
        return row.redaction_issue_count
    if "memory_redaction_not_confirmed" in row.reason_codes:
        return ONE
    return ZERO


def _validate_report_consistency(
    report: ResearchTeamMemoryRetrievalPolicyReport,
) -> None:
    rows = report.rows
    if report.brief_count != _decimal_count(len(rows)):
        raise ValueError("brief_count must match rows")
    if report.need_count != sum((row.planned_lane_count for row in rows), ZERO):
        raise ValueError("need_count must match rows")
    if report.pass_count != _decimal_count(_status_count(rows, "pass")):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _decimal_count(_status_count(rows, "watch")):
        raise ValueError("watch_count must match rows")
    if report.block_count != _decimal_count(_status_count(rows, "block")):
        raise ValueError("block_count must match rows")
    if report.average_memory_readiness_score != _average_memory_readiness_score(rows):
        raise ValueError("average_memory_readiness_score must match rows")
    if report.status != _summary_status(report.reason_codes):
        raise ValueError("status must match reason_codes")
    if report.reason_codes != _summary_reason_codes(rows):
        raise ValueError("reason_codes must match rows")
    if report.reason_code_counts != _reason_code_counts(rows, report.reason_codes):
        raise ValueError("reason_code_counts must match rows")
    if rows != tuple(sorted(rows, key=lambda row: row.brief_id)):
        raise ValueError("rows must be sorted by brief_id")


def _payload_value(value: Any) -> Any:
    if isinstance(value, Decimal):
        return str(value)
    if type(value) is datetime:
        return value.isoformat()
    if is_dataclass(value):
        return _payload_value(asdict(value))
    if isinstance(value, dict):
        return {key: _payload_value(item) for key, item in value.items()}
    if isinstance(value, tuple | list):
        return [_payload_value(item) for item in value]
    return value


def _reject_unsafe_public_payload(value: object) -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            if not isinstance(key, str):
                raise ValueError("payload keys must be strings")
            _reject_unsafe_public_text("payload", key)
            _reject_unsafe_public_payload(item)
    elif isinstance(value, list):
        for item in value:
            _reject_unsafe_public_payload(item)
    elif isinstance(value, str):
        _reject_unsafe_public_text("payload", value)


def _reject_unsafe_public_text(field_name: str, value: str) -> None:
    lowered = value.lower()
    if any(term in lowered for term in UNSAFE_PUBLIC_TERMS):
        raise ValueError(f"{field_name} contains unsafe public payload text")


def _require_exact_type(value: object, expected_type: type[object], field_name: str) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{field_name} must be exactly {expected_type.__name__}")


def _require_hard_flags(field_name: str, value: object) -> None:
    for flag in ("paper_only", "report_only", "readonly"):
        if getattr(value, flag, None) is not True:
            raise ValueError(f"{field_name}.{flag} must be True")
    if is_dataclass(value):
        field_names = {field.name for field in fields(value)}
        for flag in ("paper_only", "report_only", "readonly"):
            if flag not in field_names:
                raise ValueError(f"{field_name}.{flag} must be a dataclass field")


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    try:
        return +value
    except InvalidOperation as exc:
        raise ValueError(f"{field_name} must be finite") from exc


def _require_positive_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _require_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _require_probability_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < ZERO or normalized > ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return _quantize(normalized)


def _require_optional_probability_decimal(
    field_name: str,
    value: object,
) -> Decimal | None:
    if value is None:
        return None
    return _require_probability_decimal(field_name, value)


def _require_positive_whole_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_positive_decimal(field_name, value)
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{field_name} must be a whole count")
    return normalized


def _require_nonnegative_whole_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_nonnegative_decimal(field_name, value)
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{field_name} must be a whole count")
    return normalized


def _decimal_count(value: int) -> Decimal:
    if type(value) is not int:
        raise ValueError("count source must be an int")
    if value < 0:
        raise ValueError("count source must be nonnegative")
    return Decimal(value)


def _quantize(value: Decimal) -> Decimal:
    return value.quantize(RATIO_QUANTUM)


def _require_public_identifier(field_name: str, value: object) -> None:
    if type(value) is not str or not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a nonempty canonical string")
    if not all(character.isalnum() or character in "._-" for character in value):
        raise ValueError(f"{field_name} must be a public identifier")


def _require_public_text(field_name: str, value: object) -> str:
    if type(value) is not str or not value or value.strip() != value:
        raise ValueError(f"{field_name} must be nonempty public text")
    if any(ord(character) < 32 for character in value):
        raise ValueError(f"{field_name} must not contain control characters")
    _reject_unsafe_public_text(field_name, value)
    return value


def _require_enum(field_name: str, value: object, allowed: tuple[str, ...]) -> None:
    if type(value) is not str or value not in allowed:
        raise ValueError(f"{field_name} must be one of {allowed}")


def _require_status(field_name: str, value: object) -> None:
    _require_enum(field_name, value, STATUSES)


def _require_reason_code(field_name: str, value: object) -> None:
    _require_public_identifier(field_name, value)
    if not value.islower() or any(character == "-" for character in value):
        raise ValueError(f"{field_name} must be snake_case")
    _reject_unsafe_public_text(field_name, value)
