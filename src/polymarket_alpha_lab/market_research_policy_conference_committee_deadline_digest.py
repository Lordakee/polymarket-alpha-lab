"""Pure Phase 1 policy conference committee deadline digest reducer."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import asdict, dataclass, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from typing import Any


DEFAULT_MARKET_RESEARCH_POLICY_CONFERENCE_COMMITTEE_DEADLINE_DIGEST_CONFIG_VERSION = (
    "market-research-policy-conference-committee-deadline-digest-v0"
)

STATUS_READY = "ready"
STATUS_WATCH = "watch"
STATUS_BLOCKED = "blocked"
DIGEST_STATUSES = (STATUS_READY, STATUS_WATCH, STATUS_BLOCKED)

REASON_PREFIX = "market_research_policy_conference_committee_deadline_digest_"
HIGH_AMENDMENT_CONFLICT_REASON = f"{REASON_PREFIX}high_amendment_conflict"
HIGH_MARKET_RELEVANCE_REASON = f"{REASON_PREFIX}high_market_relevance"
NEAR_DEADLINE_REASON = f"{REASON_PREFIX}near_deadline"
STALE_ACTION_REASON = f"{REASON_PREFIX}stale_action"
THIN_SOURCES_REASON = f"{REASON_PREFIX}thin_sources"
CONFIDENCE_GAP_REASON = f"{REASON_PREFIX}confidence_gap"
PAST_DEADLINE_REASON = f"{REASON_PREFIX}past_deadline"
READY_REASON = f"{REASON_PREFIX}ready"
NO_INPUTS_REASON = f"{REASON_PREFIX}no_inputs"

REASON_CODE_SEQUENCE = (
    HIGH_AMENDMENT_CONFLICT_REASON,
    HIGH_MARKET_RELEVANCE_REASON,
    NEAR_DEADLINE_REASON,
    STALE_ACTION_REASON,
    THIN_SOURCES_REASON,
    CONFIDENCE_GAP_REASON,
    PAST_DEADLINE_REASON,
    READY_REASON,
    NO_INPUTS_REASON,
)
ROW_REASON_CODE_SEQUENCE = (
    HIGH_AMENDMENT_CONFLICT_REASON,
    HIGH_MARKET_RELEVANCE_REASON,
    NEAR_DEADLINE_REASON,
    STALE_ACTION_REASON,
    THIN_SOURCES_REASON,
    CONFIDENCE_GAP_REASON,
    PAST_DEADLINE_REASON,
    READY_REASON,
)

NEXT_STEPS = {
    STATUS_READY: (
        "allow_report_only_market_research_policy_conference_committee_deadline_digest"
    ),
    STATUS_WATCH: (
        "watch_report_only_market_research_policy_conference_committee_deadline_digest"
    ),
    STATUS_BLOCKED: (
        "block_report_only_market_research_policy_conference_committee_deadline_digest"
    ),
}

DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
QUANT = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
MICROSECONDS_PER_SECOND = Decimal("1000000")
BAD_PUBLIC_TEXT_PARTS = (
    "0x",
    "://",
    "@",
    "".join(("cre", "dential")),
    "".join(("pri", "vate")),
    "".join(("sec", "ret")),
    "".join(("tok", "en")),
)


__all__ = (
    "DEFAULT_MARKET_RESEARCH_POLICY_CONFERENCE_COMMITTEE_DEADLINE_DIGEST_CONFIG_VERSION",
    "MarketResearchPolicyConferenceCommitteeDeadlineDigestConfig",
    "MarketResearchPolicyConferenceCommitteeDeadlineDigestReasonCodeCount",
    "MarketResearchPolicyConferenceCommitteeDeadlineDigestReport",
    "MarketResearchPolicyConferenceCommitteeDeadlineDigestRow",
    "MarketResearchPolicyConferenceCommitteeDeadlineInputRow",
    "build_market_research_policy_conference_committee_deadline_digest",
    "market_research_policy_conference_committee_deadline_digest_payload",
)


@dataclass(frozen=True)
class MarketResearchPolicyConferenceCommitteeDeadlineDigestConfig:
    config_version: str = (
        DEFAULT_MARKET_RESEARCH_POLICY_CONFERENCE_COMMITTEE_DEADLINE_DIGEST_CONFIG_VERSION
    )
    near_deadline_seconds: Decimal = Decimal("172800.000000")
    stale_action_seconds: Decimal = Decimal("86400.000000")
    min_source_count: Decimal = Decimal("2.000000")
    min_independent_source_count: Decimal = Decimal("2.000000")
    min_confidence: Decimal = Decimal("0.700000")
    high_amendment_conflict_threshold: Decimal = Decimal("0.600000")
    high_market_relevance_threshold: Decimal = Decimal("0.600000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketResearchPolicyConferenceCommitteeDeadlineDigestConfig:
            raise TypeError(
                "MarketResearchPolicyConferenceCommitteeDeadlineDigestConfig "
                "does not support subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            MarketResearchPolicyConferenceCommitteeDeadlineDigestConfig,
            "config",
        )
        _require_canonical_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_MARKET_RESEARCH_POLICY_CONFERENCE_COMMITTEE_DEADLINE_DIGEST_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "near_deadline_seconds",
            "stale_action_seconds",
            "min_source_count",
            "min_independent_source_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_positive_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "min_confidence",
            "high_amendment_conflict_threshold",
            "high_market_relevance_threshold",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class MarketResearchPolicyConferenceCommitteeDeadlineInputRow:
    research_key: str
    condition_id: str
    bill_key: str
    committee_key: str
    chamber_pair: str
    deadline_rule_key: str
    conference_deadline_at: datetime
    last_committee_action_at: datetime
    source_count: Decimal
    independent_source_count: Decimal
    confidence: Decimal
    amendment_conflict_score: Decimal
    market_relevance_score: Decimal
    source_config_version: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketResearchPolicyConferenceCommitteeDeadlineInputRow:
            raise TypeError(
                "MarketResearchPolicyConferenceCommitteeDeadlineInputRow "
                "does not support subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            MarketResearchPolicyConferenceCommitteeDeadlineInputRow,
            "input row",
        )
        for field_name in (
            "research_key",
            "condition_id",
            "bill_key",
            "committee_key",
            "chamber_pair",
            "deadline_rule_key",
            "source_config_version",
        ):
            _require_public_string(field_name, getattr(self, field_name))
        object.__setattr__(
            self,
            "conference_deadline_at",
            _as_utc("conference_deadline_at", self.conference_deadline_at),
        )
        object.__setattr__(
            self,
            "last_committee_action_at",
            _as_utc("last_committee_action_at", self.last_committee_action_at),
        )
        for field_name in ("source_count", "independent_source_count"):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_count_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "confidence",
            "amendment_conflict_score",
            "market_relevance_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        if self.independent_source_count > self.source_count:
            raise ValueError("independent_source_count must not exceed source_count")
        _require_hard_flags("input row", self)


@dataclass(frozen=True)
class MarketResearchPolicyConferenceCommitteeDeadlineDigestRow:
    research_key: str
    condition_id: str
    bill_key: str
    committee_key: str
    chamber_pair: str
    deadline_rule_key: str
    deadline_status: str
    conference_deadline_at: datetime
    last_committee_action_at: datetime
    seconds_until_deadline: Decimal
    action_age_seconds: Decimal
    source_count: Decimal
    independent_source_count: Decimal
    confidence: Decimal
    amendment_conflict_score: Decimal
    market_relevance_score: Decimal
    source_config_version: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketResearchPolicyConferenceCommitteeDeadlineDigestRow:
            raise TypeError(
                "MarketResearchPolicyConferenceCommitteeDeadlineDigestRow "
                "does not support subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            MarketResearchPolicyConferenceCommitteeDeadlineDigestRow,
            "row",
        )
        for field_name in (
            "research_key",
            "condition_id",
            "bill_key",
            "committee_key",
            "chamber_pair",
            "deadline_rule_key",
            "source_config_version",
        ):
            _require_public_string(field_name, getattr(self, field_name))
        _require_status("deadline_status", self.deadline_status)
        for field_name in ("conference_deadline_at", "last_committee_action_at"):
            object.__setattr__(self, field_name, _as_utc(field_name, getattr(self, field_name)))
        object.__setattr__(
            self,
            "seconds_until_deadline",
            _require_decimal("seconds_until_deadline", self.seconds_until_deadline),
        )
        object.__setattr__(
            self,
            "action_age_seconds",
            _require_nonnegative_decimal("action_age_seconds", self.action_age_seconds),
        )
        for field_name in ("source_count", "independent_source_count"):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_count_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "confidence",
            "amendment_conflict_score",
            "market_relevance_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        if self.independent_source_count > self.source_count:
            raise ValueError("independent_source_count must not exceed source_count")
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes, sequence=ROW_REASON_CODE_SEQUENCE),
        )
        _validate_row(self)
        _require_hard_flags("row", self)


@dataclass(frozen=True)
class MarketResearchPolicyConferenceCommitteeDeadlineDigestReasonCodeCount:
    reason_code: str
    count: Decimal
    row_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketResearchPolicyConferenceCommitteeDeadlineDigestReasonCodeCount:
            raise TypeError(
                "MarketResearchPolicyConferenceCommitteeDeadlineDigestReasonCodeCount "
                "does not support subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            MarketResearchPolicyConferenceCommitteeDeadlineDigestReasonCodeCount,
            "reason code count",
        )
        _require_reason_code("reason_code", self.reason_code)
        object.__setattr__(
            self,
            "count",
            _require_nonnegative_count_decimal("count", self.count),
        )
        object.__setattr__(
            self,
            "row_ratio",
            _require_ratio_decimal("row_ratio", self.row_ratio),
        )
        _require_hard_flags("reason code count", self)


@dataclass(frozen=True)
class MarketResearchPolicyConferenceCommitteeDeadlineDigestReport:
    generated_at: datetime
    config_version: str
    digest_status: str
    recommended_next_step: str
    input_count: Decimal
    row_count: Decimal
    ready_count: Decimal
    watch_count: Decimal
    blocked_count: Decimal
    high_amendment_conflict_count: Decimal
    high_market_relevance_count: Decimal
    near_deadline_count: Decimal
    stale_action_count: Decimal
    thin_source_count: Decimal
    confidence_gap_count: Decimal
    past_deadline_count: Decimal
    average_confidence: Decimal
    average_amendment_conflict_score: Decimal
    average_market_relevance_score: Decimal
    average_source_count: Decimal
    average_independent_source_count: Decimal
    minimum_seconds_until_deadline: Decimal
    rows: tuple[MarketResearchPolicyConferenceCommitteeDeadlineDigestRow, ...]
    source_config_versions: tuple[tuple[str, str], ...]
    reason_code_counts: tuple[
        MarketResearchPolicyConferenceCommitteeDeadlineDigestReasonCodeCount,
        ...,
    ]
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketResearchPolicyConferenceCommitteeDeadlineDigestReport:
            raise TypeError(
                "MarketResearchPolicyConferenceCommitteeDeadlineDigestReport "
                "does not support subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            MarketResearchPolicyConferenceCommitteeDeadlineDigestReport,
            "report",
        )
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_MARKET_RESEARCH_POLICY_CONFERENCE_COMMITTEE_DEADLINE_DIGEST_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        _require_status("digest_status", self.digest_status)
        _require_canonical_string("recommended_next_step", self.recommended_next_step)
        for field_name in (
            "input_count",
            "row_count",
            "ready_count",
            "watch_count",
            "blocked_count",
            "high_amendment_conflict_count",
            "high_market_relevance_count",
            "near_deadline_count",
            "stale_action_count",
            "thin_source_count",
            "confidence_gap_count",
            "past_deadline_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_count_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "average_confidence",
            "average_amendment_conflict_score",
            "average_market_relevance_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "average_source_count",
            "average_independent_source_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "minimum_seconds_until_deadline",
            _require_decimal(
                "minimum_seconds_until_deadline",
                self.minimum_seconds_until_deadline,
            ),
        )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        object.__setattr__(
            self,
            "source_config_versions",
            _normalize_source_config_versions(self.source_config_versions),
        )
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes, sequence=REASON_CODE_SEQUENCE),
        )
        _validate_report(self)
        _require_hard_flags("report", self)


def build_market_research_policy_conference_committee_deadline_digest(
    input_rows: Iterable[MarketResearchPolicyConferenceCommitteeDeadlineInputRow],
    *,
    config: MarketResearchPolicyConferenceCommitteeDeadlineDigestConfig,
    generated_at: datetime,
) -> MarketResearchPolicyConferenceCommitteeDeadlineDigestReport:
    if type(config) is not MarketResearchPolicyConferenceCommitteeDeadlineDigestConfig:
        raise ValueError(
            "config must be exactly "
            "MarketResearchPolicyConferenceCommitteeDeadlineDigestConfig",
        )
    _require_hard_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    normalized_rows = _normalize_input_rows(input_rows, generated_at_utc)
    rows = _sorted_rows(
        tuple(
            _row_for_input(row, config=config, generated_at=generated_at_utc)
            for row in normalized_rows
        ),
    )
    row_count = _count(len(rows))
    reason_code_counts = _reason_code_counts(rows, row_count)
    reason_codes = tuple(item.reason_code for item in reason_code_counts)
    if not rows:
        reason_code_counts = (
            MarketResearchPolicyConferenceCommitteeDeadlineDigestReasonCodeCount(
                reason_code=NO_INPUTS_REASON,
                count=ONE,
                row_ratio=ZERO,
            ),
        )
        reason_codes = (NO_INPUTS_REASON,)

    ready_count = _status_count(rows, STATUS_READY)
    watch_count = _status_count(rows, STATUS_WATCH)
    blocked_count = _status_count(rows, STATUS_BLOCKED)
    digest_status = _report_status(
        has_inputs=bool(rows),
        blocked_count=blocked_count,
        watch_count=watch_count,
    )

    return MarketResearchPolicyConferenceCommitteeDeadlineDigestReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        digest_status=digest_status,
        recommended_next_step=NEXT_STEPS[digest_status],
        input_count=_count(len(normalized_rows)),
        row_count=row_count,
        ready_count=ready_count,
        watch_count=watch_count,
        blocked_count=blocked_count,
        high_amendment_conflict_count=_reason_row_count(
            rows,
            HIGH_AMENDMENT_CONFLICT_REASON,
        ),
        high_market_relevance_count=_reason_row_count(
            rows,
            HIGH_MARKET_RELEVANCE_REASON,
        ),
        near_deadline_count=_reason_row_count(rows, NEAR_DEADLINE_REASON),
        stale_action_count=_reason_row_count(rows, STALE_ACTION_REASON),
        thin_source_count=_reason_row_count(rows, THIN_SOURCES_REASON),
        confidence_gap_count=_reason_row_count(rows, CONFIDENCE_GAP_REASON),
        past_deadline_count=_reason_row_count(rows, PAST_DEADLINE_REASON),
        average_confidence=_ratio(
            _decimal_sum(row.confidence for row in rows),
            row_count,
        ),
        average_amendment_conflict_score=_ratio(
            _decimal_sum(row.amendment_conflict_score for row in rows),
            row_count,
        ),
        average_market_relevance_score=_ratio(
            _decimal_sum(row.market_relevance_score for row in rows),
            row_count,
        ),
        average_source_count=_ratio(
            _decimal_sum(row.source_count for row in rows),
            row_count,
        ),
        average_independent_source_count=_ratio(
            _decimal_sum(row.independent_source_count for row in rows),
            row_count,
        ),
        minimum_seconds_until_deadline=min(
            (row.seconds_until_deadline for row in rows),
            default=ZERO,
        ),
        rows=rows,
        source_config_versions=_source_config_versions(normalized_rows),
        reason_code_counts=reason_code_counts,
        reason_codes=reason_codes,
    )


def market_research_policy_conference_committee_deadline_digest_payload(
    report: MarketResearchPolicyConferenceCommitteeDeadlineDigestReport,
) -> dict[str, Any]:
    if type(report) is not MarketResearchPolicyConferenceCommitteeDeadlineDigestReport:
        raise ValueError(
            "report must be exactly "
            "MarketResearchPolicyConferenceCommitteeDeadlineDigestReport",
        )
    _require_hard_flags("report", report)
    return _json_ready(asdict(report))


def _row_for_input(
    row: MarketResearchPolicyConferenceCommitteeDeadlineInputRow,
    *,
    config: MarketResearchPolicyConferenceCommitteeDeadlineDigestConfig,
    generated_at: datetime,
) -> MarketResearchPolicyConferenceCommitteeDeadlineDigestRow:
    _require_not_future("last_committee_action_at", row.last_committee_action_at, generated_at)
    seconds_until_deadline = _seconds_between(row.conference_deadline_at, generated_at)
    action_age_seconds = _seconds_between(generated_at, row.last_committee_action_at)
    reason_codes = _row_reason_codes(
        seconds_until_deadline=seconds_until_deadline,
        action_age_seconds=action_age_seconds,
        source_count=row.source_count,
        independent_source_count=row.independent_source_count,
        confidence=row.confidence,
        amendment_conflict_score=row.amendment_conflict_score,
        market_relevance_score=row.market_relevance_score,
        config=config,
    )
    return MarketResearchPolicyConferenceCommitteeDeadlineDigestRow(
        research_key=row.research_key,
        condition_id=row.condition_id,
        bill_key=row.bill_key,
        committee_key=row.committee_key,
        chamber_pair=row.chamber_pair,
        deadline_rule_key=row.deadline_rule_key,
        deadline_status=_row_status(reason_codes),
        conference_deadline_at=row.conference_deadline_at,
        last_committee_action_at=row.last_committee_action_at,
        seconds_until_deadline=seconds_until_deadline,
        action_age_seconds=action_age_seconds,
        source_count=row.source_count,
        independent_source_count=row.independent_source_count,
        confidence=row.confidence,
        amendment_conflict_score=row.amendment_conflict_score,
        market_relevance_score=row.market_relevance_score,
        source_config_version=row.source_config_version,
        reason_codes=reason_codes,
    )


def _row_reason_codes(
    *,
    seconds_until_deadline: Decimal,
    action_age_seconds: Decimal,
    source_count: Decimal,
    independent_source_count: Decimal,
    confidence: Decimal,
    amendment_conflict_score: Decimal,
    market_relevance_score: Decimal,
    config: MarketResearchPolicyConferenceCommitteeDeadlineDigestConfig,
) -> tuple[str, ...]:
    reasons: list[str] = []
    if amendment_conflict_score >= config.high_amendment_conflict_threshold:
        reasons.append(HIGH_AMENDMENT_CONFLICT_REASON)
    if market_relevance_score >= config.high_market_relevance_threshold:
        reasons.append(HIGH_MARKET_RELEVANCE_REASON)
    if ZERO <= seconds_until_deadline <= config.near_deadline_seconds:
        reasons.append(NEAR_DEADLINE_REASON)
    if action_age_seconds > config.stale_action_seconds:
        reasons.append(STALE_ACTION_REASON)
    if (
        source_count < config.min_source_count
        or independent_source_count < config.min_independent_source_count
    ):
        reasons.append(THIN_SOURCES_REASON)
    if confidence < config.min_confidence:
        reasons.append(CONFIDENCE_GAP_REASON)
    if seconds_until_deadline < ZERO:
        reasons.append(PAST_DEADLINE_REASON)
    if not reasons:
        reasons.append(READY_REASON)
    return _normalize_reason_codes(reasons, sequence=ROW_REASON_CODE_SEQUENCE)


def _row_status(reason_codes: tuple[str, ...]) -> str:
    if reason_codes == (READY_REASON,):
        return STATUS_READY
    if any(
        reason_code in reason_codes
        for reason_code in (
            STALE_ACTION_REASON,
            THIN_SOURCES_REASON,
            CONFIDENCE_GAP_REASON,
            PAST_DEADLINE_REASON,
        )
    ):
        return STATUS_BLOCKED
    return STATUS_WATCH


def _report_status(
    *,
    has_inputs: bool,
    blocked_count: Decimal,
    watch_count: Decimal,
) -> str:
    if not has_inputs or blocked_count > ZERO:
        return STATUS_BLOCKED
    if watch_count > ZERO:
        return STATUS_WATCH
    return STATUS_READY


def _sorted_rows(
    rows: tuple[MarketResearchPolicyConferenceCommitteeDeadlineDigestRow, ...],
) -> tuple[MarketResearchPolicyConferenceCommitteeDeadlineDigestRow, ...]:
    return tuple(
        sorted(
            rows,
            key=lambda row: (
                _status_rank(row.deadline_status),
                _blocked_reason_rank(row.reason_codes),
                row.seconds_until_deadline,
                -row.amendment_conflict_score,
                -row.market_relevance_score,
                row.bill_key,
                row.research_key,
            ),
        ),
    )


def _blocked_reason_rank(reason_codes: tuple[str, ...]) -> int:
    if PAST_DEADLINE_REASON in reason_codes:
        return 0
    if STALE_ACTION_REASON in reason_codes:
        return 1
    if THIN_SOURCES_REASON in reason_codes:
        return 2
    if CONFIDENCE_GAP_REASON in reason_codes:
        return 3
    return 4


def _status_rank(status: str) -> int:
    if status == STATUS_BLOCKED:
        return 0
    if status == STATUS_WATCH:
        return 1
    if status == STATUS_READY:
        return 2
    raise ValueError("deadline_status must be supported")


def _normalize_input_rows(
    input_rows: Iterable[MarketResearchPolicyConferenceCommitteeDeadlineInputRow],
    generated_at: datetime,
) -> tuple[MarketResearchPolicyConferenceCommitteeDeadlineInputRow, ...]:
    if isinstance(input_rows, (str, bytes)):
        raise ValueError("input_rows must be an iterable of input rows")
    try:
        rows = tuple(input_rows)
    except TypeError as exc:
        raise ValueError("input_rows must be an iterable of input rows") from exc
    seen_condition_ids: set[str] = set()
    for row in rows:
        if type(row) is not MarketResearchPolicyConferenceCommitteeDeadlineInputRow:
            raise ValueError(
                "input_rows must contain "
                "MarketResearchPolicyConferenceCommitteeDeadlineInputRow values",
            )
        _require_hard_flags("input row", row)
        _require_not_future("last_committee_action_at", row.last_committee_action_at, generated_at)
        if row.condition_id in seen_condition_ids:
            raise ValueError("condition_id values must be unique")
        seen_condition_ids.add(row.condition_id)
    return rows


def _normalize_rows(
    rows: Iterable[MarketResearchPolicyConferenceCommitteeDeadlineDigestRow],
) -> tuple[MarketResearchPolicyConferenceCommitteeDeadlineDigestRow, ...]:
    if isinstance(rows, (str, bytes)):
        raise ValueError("rows must be an iterable")
    try:
        normalized = tuple(rows)
    except TypeError as exc:
        raise ValueError("rows must be an iterable") from exc
    for row in normalized:
        if type(row) is not MarketResearchPolicyConferenceCommitteeDeadlineDigestRow:
            raise ValueError(
                "rows must contain "
                "MarketResearchPolicyConferenceCommitteeDeadlineDigestRow values",
            )
        _require_hard_flags("row", row)
    if normalized != _sorted_rows(normalized):
        raise ValueError("rows must use deterministic deadline sort")
    return normalized


def _normalize_source_config_versions(
    values: Iterable[tuple[str, str]],
) -> tuple[tuple[str, str], ...]:
    if isinstance(values, (str, bytes)):
        raise ValueError("source_config_versions must be an iterable")
    try:
        normalized = tuple(tuple(item) for item in values)
    except TypeError as exc:
        raise ValueError("source_config_versions must be an iterable") from exc
    if normalized != tuple(sorted(normalized)):
        raise ValueError("source_config_versions must be sorted")
    seen: set[str] = set()
    for item in normalized:
        if len(item) != 2:
            raise ValueError("source_config_versions entries must have two values")
        condition_id, config_version = item
        _require_public_string("source_config_versions", condition_id)
        _require_public_string("source_config_versions", config_version)
        if condition_id in seen:
            raise ValueError("source_config_versions must have unique condition ids")
        seen.add(condition_id)
    return normalized


def _normalize_reason_code_counts(
    values: Iterable[MarketResearchPolicyConferenceCommitteeDeadlineDigestReasonCodeCount],
) -> tuple[MarketResearchPolicyConferenceCommitteeDeadlineDigestReasonCodeCount, ...]:
    if isinstance(values, (str, bytes)):
        raise ValueError("reason_code_counts must be an iterable")
    try:
        normalized = tuple(values)
    except TypeError as exc:
        raise ValueError("reason_code_counts must be an iterable") from exc
    for item in normalized:
        if type(item) is not MarketResearchPolicyConferenceCommitteeDeadlineDigestReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "MarketResearchPolicyConferenceCommitteeDeadlineDigestReasonCodeCount values",
            )
        _require_hard_flags("reason code count", item)
    if normalized != tuple(sorted(normalized, key=lambda item: _reason_rank(item.reason_code))):
        raise ValueError("reason_code_counts must use deterministic reason code sort")
    return normalized


def _normalize_reason_codes(
    values: Iterable[str],
    *,
    sequence: tuple[str, ...],
) -> tuple[str, ...]:
    if isinstance(values, (str, bytes)):
        raise ValueError("reason_codes must be an iterable")
    try:
        normalized = tuple(values)
    except TypeError as exc:
        raise ValueError("reason_codes must be an iterable") from exc
    if not normalized:
        raise ValueError("reason_codes must include at least one code")
    if len(set(normalized)) != len(normalized):
        raise ValueError("reason_codes must not contain duplicates")
    for reason_code in normalized:
        _require_reason_code("reason_codes", reason_code)
        if reason_code not in sequence:
            raise ValueError("reason_codes include an unsupported code")
    return tuple(sorted(normalized, key=lambda reason_code: sequence.index(reason_code)))


def _validate_row(row: MarketResearchPolicyConferenceCommitteeDeadlineDigestRow) -> None:
    if row.deadline_status != _row_status(row.reason_codes):
        raise ValueError("deadline_status must match reason_codes")
    if (row.seconds_until_deadline < ZERO) != (PAST_DEADLINE_REASON in row.reason_codes):
        raise ValueError("reason_codes must match deadline timing")
    if NEAR_DEADLINE_REASON in row.reason_codes and row.seconds_until_deadline < ZERO:
        raise ValueError("reason_codes must not mark past deadlines near")
    if READY_REASON in row.reason_codes and row.reason_codes != (READY_REASON,):
        raise ValueError("reason_codes must not mix ready with other codes")


def _validate_report(report: MarketResearchPolicyConferenceCommitteeDeadlineDigestReport) -> None:
    if report.recommended_next_step != NEXT_STEPS[report.digest_status]:
        raise ValueError("recommended_next_step must match digest_status")
    if report.input_count != report.row_count:
        raise ValueError("input_count must match row_count")
    if report.row_count != _count(len(report.rows)):
        raise ValueError("row_count must match rows")
    if report.ready_count != _status_count(report.rows, STATUS_READY):
        raise ValueError("ready_count must match rows")
    if report.watch_count != _status_count(report.rows, STATUS_WATCH):
        raise ValueError("watch_count must match rows")
    if report.blocked_count != _status_count(report.rows, STATUS_BLOCKED):
        raise ValueError("blocked_count must match rows")
    if report.high_amendment_conflict_count != _reason_row_count(
        report.rows,
        HIGH_AMENDMENT_CONFLICT_REASON,
    ):
        raise ValueError("high_amendment_conflict_count must match rows")
    if report.high_market_relevance_count != _reason_row_count(
        report.rows,
        HIGH_MARKET_RELEVANCE_REASON,
    ):
        raise ValueError("high_market_relevance_count must match rows")
    if report.near_deadline_count != _reason_row_count(report.rows, NEAR_DEADLINE_REASON):
        raise ValueError("near_deadline_count must match rows")
    if report.stale_action_count != _reason_row_count(report.rows, STALE_ACTION_REASON):
        raise ValueError("stale_action_count must match rows")
    if report.thin_source_count != _reason_row_count(report.rows, THIN_SOURCES_REASON):
        raise ValueError("thin_source_count must match rows")
    if report.confidence_gap_count != _reason_row_count(report.rows, CONFIDENCE_GAP_REASON):
        raise ValueError("confidence_gap_count must match rows")
    if report.past_deadline_count != _reason_row_count(report.rows, PAST_DEADLINE_REASON):
        raise ValueError("past_deadline_count must match rows")
    if report.average_confidence != _ratio(
        _decimal_sum(row.confidence for row in report.rows),
        report.row_count,
    ):
        raise ValueError("average_confidence must match rows")
    if report.average_amendment_conflict_score != _ratio(
        _decimal_sum(row.amendment_conflict_score for row in report.rows),
        report.row_count,
    ):
        raise ValueError("average_amendment_conflict_score must match rows")
    if report.average_market_relevance_score != _ratio(
        _decimal_sum(row.market_relevance_score for row in report.rows),
        report.row_count,
    ):
        raise ValueError("average_market_relevance_score must match rows")
    if report.average_source_count != _ratio(
        _decimal_sum(row.source_count for row in report.rows),
        report.row_count,
    ):
        raise ValueError("average_source_count must match rows")
    if report.average_independent_source_count != _ratio(
        _decimal_sum(row.independent_source_count for row in report.rows),
        report.row_count,
    ):
        raise ValueError("average_independent_source_count must match rows")
    if report.minimum_seconds_until_deadline != min(
        (row.seconds_until_deadline for row in report.rows),
        default=ZERO,
    ):
        raise ValueError("minimum_seconds_until_deadline must match rows")
    expected_status = _report_status(
        has_inputs=bool(report.rows),
        blocked_count=report.blocked_count,
        watch_count=report.watch_count,
    )
    if report.digest_status != expected_status:
        raise ValueError("digest_status must match rows")
    if report.source_config_versions != _source_config_versions(report.rows):
        raise ValueError("source_config_versions must match rows")
    if report.reason_code_counts != _expected_reason_code_counts(report.rows):
        raise ValueError("reason_code_counts must match rows")
    if report.reason_codes != tuple(item.reason_code for item in report.reason_code_counts):
        raise ValueError("reason_codes must match reason_code_counts")


def _expected_reason_code_counts(
    rows: tuple[MarketResearchPolicyConferenceCommitteeDeadlineDigestRow, ...],
) -> tuple[MarketResearchPolicyConferenceCommitteeDeadlineDigestReasonCodeCount, ...]:
    if not rows:
        return (
            MarketResearchPolicyConferenceCommitteeDeadlineDigestReasonCodeCount(
                reason_code=NO_INPUTS_REASON,
                count=ONE,
                row_ratio=ZERO,
            ),
        )
    return _reason_code_counts(rows, _count(len(rows)))


def _reason_code_counts(
    rows: tuple[MarketResearchPolicyConferenceCommitteeDeadlineDigestRow, ...],
    row_count: Decimal,
) -> tuple[MarketResearchPolicyConferenceCommitteeDeadlineDigestReasonCodeCount, ...]:
    return tuple(
        MarketResearchPolicyConferenceCommitteeDeadlineDigestReasonCodeCount(
            reason_code=reason_code,
            count=count,
            row_ratio=_ratio(count, row_count),
        )
        for reason_code, count in sorted(
            (
                (
                    reason_code,
                    _reason_row_count(rows, reason_code),
                )
                for reason_code in REASON_CODE_SEQUENCE
                if any(reason_code in row.reason_codes for row in rows)
            ),
            key=lambda item: _reason_rank(item[0]),
        )
    )


def _reason_row_count(
    rows: tuple[MarketResearchPolicyConferenceCommitteeDeadlineDigestRow, ...],
    reason_code: str,
) -> Decimal:
    return _count(sum(1 for row in rows if reason_code in row.reason_codes))


def _status_count(
    rows: tuple[MarketResearchPolicyConferenceCommitteeDeadlineDigestRow, ...],
    status: str,
) -> Decimal:
    return _count(sum(1 for row in rows if row.deadline_status == status))


def _source_config_versions(
    rows: Iterable[
        MarketResearchPolicyConferenceCommitteeDeadlineInputRow
        | MarketResearchPolicyConferenceCommitteeDeadlineDigestRow
    ],
) -> tuple[tuple[str, str], ...]:
    versions = {row.condition_id: row.source_config_version for row in rows}
    return tuple(sorted(versions.items()))


def _decimal_sum(values: Iterable[Decimal]) -> Decimal:
    total = ZERO
    for value in values:
        total = _quantize_decimal(total + value)
    return total


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO:
        return ZERO
    return _quantize_decimal(numerator / denominator)


def _count(value: int) -> Decimal:
    return _quantize_decimal(Decimal(value))


def _seconds_between(later: datetime, earlier: datetime) -> Decimal:
    delta = later - earlier
    total_microseconds = Decimal(delta.days * 86400 + delta.seconds) * MICROSECONDS_PER_SECOND
    total_microseconds += Decimal(delta.microseconds)
    return _quantize_decimal(total_microseconds / MICROSECONDS_PER_SECOND)


def _require_not_future(field_name: str, value: datetime, generated_at: datetime) -> None:
    if value > generated_at:
        raise ValueError(f"{field_name} must not be future")


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must include timezone")
    return value.astimezone(UTC)


def _require_exact_type(value: object, expected_type: type[object], label: str) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{label} must be exactly {expected_type.__name__}")


def _require_status(field_name: str, value: object) -> None:
    if value not in DIGEST_STATUSES:
        raise ValueError(f"{field_name} must be a supported status")


def _require_public_string(field_name: str, value: object) -> None:
    _require_canonical_string(field_name, value)
    lowered = value.lower()
    if any(part in lowered for part in BAD_PUBLIC_TEXT_PARTS):
        raise ValueError(f"{field_name} must be public and redacted")


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be non-empty and trimmed")
    if any(character.isspace() for character in value):
        raise ValueError(f"{field_name} must not contain whitespace")


def _require_reason_code(field_name: str, value: object) -> None:
    _require_canonical_string(field_name, value)
    if value not in REASON_CODE_SEQUENCE:
        raise ValueError(f"{field_name} must be a known reason code")


def _reason_rank(reason_code: str) -> int:
    if reason_code not in REASON_CODE_SEQUENCE:
        raise ValueError("reason_code must be known")
    return REASON_CODE_SEQUENCE.index(reason_code)


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return _quantize_decimal(value)


def _require_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return decimal_value


def _require_positive_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return decimal_value


def _require_nonnegative_count_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_nonnegative_decimal(field_name, value)
    if decimal_value != decimal_value.to_integral_value():
        raise ValueError(f"{field_name} must be a whole count")
    return decimal_value


def _require_ratio_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value < ZERO or decimal_value > ONE:
        raise ValueError(f"{field_name} must be between zero and one")
    return decimal_value


def _quantize_decimal(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(QUANT)


def _require_hard_flags(label: str, value: object) -> None:
    if getattr(value, "paper_only", None) is not True:
        raise ValueError(f"{label} paper_only must be True")
    if getattr(value, "report_only", None) is not True:
        raise ValueError(f"{label} report_only must be True")
    if getattr(value, "readonly", None) is not True:
        raise ValueError(f"{label} readonly must be True")


def _json_ready(value: Any) -> Any:
    if value is None:
        return None
    if is_dataclass(value) and not isinstance(value, type):
        return _json_ready(asdict(value))
    if isinstance(value, Decimal):
        if not value.is_finite():
            raise ValueError("JSON Decimal value must be finite")
        return str(_quantize_decimal(value))
    if isinstance(value, datetime):
        if type(value) is not datetime:
            raise ValueError("JSON datetime value must be exact")
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("JSON datetime value must include timezone")
        return value.astimezone(UTC).isoformat()
    if type(value) is bool:
        return value
    if type(value) is int:
        raise ValueError("JSON numeric values must use Decimal-derived strings")
    if isinstance(value, float):
        raise ValueError("JSON value must not be a float")
    if type(value) is str:
        return value
    if isinstance(value, dict):
        ready: dict[str, Any] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            ready[key] = _json_ready(item)
        return ready
    if isinstance(value, (list, tuple)):
        return [_json_ready(item) for item in value]
    raise ValueError("value is not JSON serializable")
