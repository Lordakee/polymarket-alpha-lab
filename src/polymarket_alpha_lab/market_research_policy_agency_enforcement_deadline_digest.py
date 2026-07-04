"""Pure Phase 1 policy agency enforcement deadline digest reducer."""

from __future__ import annotations

from dataclasses import asdict, dataclass, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
from typing import Any


DEFAULT_MARKET_RESEARCH_POLICY_AGENCY_ENFORCEMENT_DEADLINE_DIGEST_CONFIG_VERSION = (
    "market-research-policy-agency-enforcement-deadline-digest-v0"
)

STATUS_READY = "ready"
STATUS_WATCH = "watch"
STATUS_BLOCKED = "blocked"

REASON_PREFIX = "market_research_policy_agency_enforcement_deadline_digest_"
NO_INPUTS_REASON = f"{REASON_PREFIX}no_inputs"
READY_REASON = f"{REASON_PREFIX}ready"
LOW_CONFIRMATION_REASON = f"{REASON_PREFIX}low_confirmation"
MATERIAL_WATCH_REASON = f"{REASON_PREFIX}material_watch"
MATERIAL_BLOCK_REASON = f"{REASON_PREFIX}material_block"
PROBABILITY_SHIFT_REASON = f"{REASON_PREFIX}probability_shift"
IMMINENT_DEADLINE_REASON = f"{REASON_PREFIX}imminent_deadline"
MISSED_DEADLINE_REASON = f"{REASON_PREFIX}missed_deadline"
STALE_DEADLINE_NOTICE_REASON = f"{REASON_PREFIX}stale_deadline_notice"
THIN_SOURCES_REASON = f"{REASON_PREFIX}thin_sources"

REASON_CODE_SEQUENCE = (
    NO_INPUTS_REASON,
    MATERIAL_BLOCK_REASON,
    PROBABILITY_SHIFT_REASON,
    MISSED_DEADLINE_REASON,
    IMMINENT_DEADLINE_REASON,
    LOW_CONFIRMATION_REASON,
    MATERIAL_WATCH_REASON,
    STALE_DEADLINE_NOTICE_REASON,
    THIN_SOURCES_REASON,
    READY_REASON,
)
ROW_REASON_CODE_SEQUENCE = (
    MATERIAL_BLOCK_REASON,
    PROBABILITY_SHIFT_REASON,
    MISSED_DEADLINE_REASON,
    IMMINENT_DEADLINE_REASON,
    LOW_CONFIRMATION_REASON,
    MATERIAL_WATCH_REASON,
    READY_REASON,
    STALE_DEADLINE_NOTICE_REASON,
    THIN_SOURCES_REASON,
)

NEXT_STEPS = {
    STATUS_READY: (
        "allow_report_only_market_research_policy_agency_enforcement_deadline_digest"
    ),
    STATUS_WATCH: (
        "watch_report_only_market_research_policy_agency_enforcement_deadline_digest"
    ),
    STATUS_BLOCKED: (
        "block_report_only_market_research_policy_agency_enforcement_deadline_digest"
    ),
}

DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
QUANT = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
MICROSECONDS_PER_SECOND = Decimal("1000000")
PROBABILITY_SHIFT_THRESHOLD = Decimal("0.100000")

UNSAFE_TEXT_FRAGMENTS = (
    "auth",
    "broker",
    "signing",
    "submit",
    "cancel",
    "wal" "let",
    "account",
    "private",
    "secret",
    "token",
    "credential",
    "order",
)
PUBLIC_REFERENCE_FRAGMENTS = (
    "public",
    "deadline",
    "notice",
    "docket",
    "memo",
    "enforcement",
)


__all__ = (
    "DEFAULT_MARKET_RESEARCH_POLICY_AGENCY_ENFORCEMENT_DEADLINE_DIGEST_CONFIG_VERSION",
    "MarketResearchPolicyAgencyEnforcementDeadlineDigestConfig",
    "MarketResearchPolicyAgencyEnforcementDeadlineDigestInputRow",
    "MarketResearchPolicyAgencyEnforcementDeadlineDigestReasonCodeCount",
    "MarketResearchPolicyAgencyEnforcementDeadlineDigestReport",
    "MarketResearchPolicyAgencyEnforcementDeadlineDigestRow",
    "build_market_research_policy_agency_enforcement_deadline_digest",
    "market_research_policy_agency_enforcement_deadline_digest_payload",
)


@dataclass(frozen=True)
class MarketResearchPolicyAgencyEnforcementDeadlineDigestConfig:
    config_version: str = (
        DEFAULT_MARKET_RESEARCH_POLICY_AGENCY_ENFORCEMENT_DEADLINE_DIGEST_CONFIG_VERSION
    )
    fresh_deadline_notice_max_age_seconds: Decimal = Decimal("86400.000000")
    min_public_source_count: Decimal = Decimal("2")
    min_cross_source_confirmation: Decimal = Decimal("0.600000")
    materiality_watch_threshold: Decimal = Decimal("0.150000")
    materiality_block_threshold: Decimal = Decimal("0.350000")
    imminent_deadline_max_seconds: Decimal = Decimal("7200.000000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketResearchPolicyAgencyEnforcementDeadlineDigestConfig:
            raise TypeError(
                "MarketResearchPolicyAgencyEnforcementDeadlineDigestConfig does not "
                "support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not MarketResearchPolicyAgencyEnforcementDeadlineDigestConfig:
            raise ValueError(
                "config must be exactly "
                "MarketResearchPolicyAgencyEnforcementDeadlineDigestConfig",
            )
        _require_public_string("config_version", self.config_version)
        object.__setattr__(
            self,
            "fresh_deadline_notice_max_age_seconds",
            _require_nonnegative_decimal(
                "fresh_deadline_notice_max_age_seconds",
                self.fresh_deadline_notice_max_age_seconds,
            ),
        )
        object.__setattr__(
            self,
            "min_public_source_count",
            _require_nonnegative_count_decimal(
                "min_public_source_count",
                self.min_public_source_count,
            ),
        )
        for field_name in (
            "min_cross_source_confirmation",
            "materiality_watch_threshold",
            "materiality_block_threshold",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        if self.materiality_watch_threshold > self.materiality_block_threshold:
            raise ValueError(
                "materiality_block_threshold must be at least materiality_watch_threshold",
            )
        object.__setattr__(
            self,
            "imminent_deadline_max_seconds",
            _require_nonnegative_decimal(
                "imminent_deadline_max_seconds",
                self.imminent_deadline_max_seconds,
            ),
        )
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class MarketResearchPolicyAgencyEnforcementDeadlineDigestInputRow:
    research_key: str
    condition_id: str
    policy_area: str
    agency_name: str
    public_deadline_reference: str
    deadline_announced_at: datetime
    enforcement_deadline_at: datetime
    public_source_count: Decimal
    cross_source_confirmation: Decimal
    enforcement_materiality_score: Decimal
    market_probability_before: Decimal
    market_probability_after: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketResearchPolicyAgencyEnforcementDeadlineDigestInputRow:
            raise TypeError(
                "MarketResearchPolicyAgencyEnforcementDeadlineDigestInputRow does not "
                "support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not MarketResearchPolicyAgencyEnforcementDeadlineDigestInputRow:
            raise ValueError(
                "input row must be exactly "
                "MarketResearchPolicyAgencyEnforcementDeadlineDigestInputRow",
            )
        for field_name in (
            "research_key",
            "condition_id",
            "policy_area",
            "agency_name",
        ):
            _require_public_string(field_name, getattr(self, field_name))
        _require_reference("public_deadline_reference", self.public_deadline_reference)
        object.__setattr__(
            self,
            "deadline_announced_at",
            _as_utc("deadline_announced_at", self.deadline_announced_at),
        )
        object.__setattr__(
            self,
            "enforcement_deadline_at",
            _as_utc("enforcement_deadline_at", self.enforcement_deadline_at),
        )
        if self.enforcement_deadline_at < self.deadline_announced_at:
            raise ValueError(
                "enforcement_deadline_at must be on or after deadline_announced_at",
            )
        object.__setattr__(
            self,
            "public_source_count",
            _require_nonnegative_count_decimal(
                "public_source_count",
                self.public_source_count,
            ),
        )
        for field_name in (
            "cross_source_confirmation",
            "enforcement_materiality_score",
            "market_probability_before",
            "market_probability_after",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        _require_hard_flags("input row", self)


@dataclass(frozen=True)
class MarketResearchPolicyAgencyEnforcementDeadlineDigestRow:
    research_key: str
    condition_id: str
    policy_area: str
    agency_name: str
    deadline_announced_at: datetime
    enforcement_deadline_at: datetime
    deadline_notice_age_seconds: Decimal
    seconds_until_deadline: Decimal
    deadline_overdue_seconds: Decimal
    public_source_count: Decimal
    cross_source_confirmation: Decimal
    enforcement_materiality_score: Decimal
    market_probability_before: Decimal
    market_probability_after: Decimal
    probability_change: Decimal
    deadline_status: str
    redacted_deadline_reference: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketResearchPolicyAgencyEnforcementDeadlineDigestRow:
            raise TypeError(
                "MarketResearchPolicyAgencyEnforcementDeadlineDigestRow does not support "
                "subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not MarketResearchPolicyAgencyEnforcementDeadlineDigestRow:
            raise ValueError(
                "row must be exactly "
                "MarketResearchPolicyAgencyEnforcementDeadlineDigestRow",
            )
        for field_name in (
            "research_key",
            "condition_id",
            "policy_area",
            "agency_name",
        ):
            _require_public_string(field_name, getattr(self, field_name))
        object.__setattr__(
            self,
            "deadline_announced_at",
            _as_utc("deadline_announced_at", self.deadline_announced_at),
        )
        object.__setattr__(
            self,
            "enforcement_deadline_at",
            _as_utc("enforcement_deadline_at", self.enforcement_deadline_at),
        )
        for field_name in (
            "deadline_notice_age_seconds",
            "seconds_until_deadline",
            "deadline_overdue_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "public_source_count",
            _require_nonnegative_count_decimal(
                "public_source_count",
                self.public_source_count,
            ),
        )
        for field_name in (
            "cross_source_confirmation",
            "enforcement_materiality_score",
            "market_probability_before",
            "market_probability_after",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "probability_change",
            _require_probability_change("probability_change", self.probability_change),
        )
        _require_status("deadline_status", self.deadline_status)
        object.__setattr__(
            self,
            "redacted_deadline_reference",
            _require_redacted_reference(
                "redacted_deadline_reference",
                self.redacted_deadline_reference,
            ),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_row_reason_codes(self.reason_codes),
        )
        _validate_row(self)
        _require_hard_flags("row", self)


@dataclass(frozen=True)
class MarketResearchPolicyAgencyEnforcementDeadlineDigestReasonCodeCount:
    reason_code: str
    count: Decimal
    deadline_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketResearchPolicyAgencyEnforcementDeadlineDigestReasonCodeCount:
            raise TypeError(
                "MarketResearchPolicyAgencyEnforcementDeadlineDigestReasonCodeCount "
                "does not support subclassing",
            )

    def __post_init__(self) -> None:
        if (
            type(self)
            is not MarketResearchPolicyAgencyEnforcementDeadlineDigestReasonCodeCount
        ):
            raise ValueError(
                "reason code count must be exactly "
                "MarketResearchPolicyAgencyEnforcementDeadlineDigestReasonCodeCount",
            )
        _require_reason_code("reason_code", self.reason_code, REASON_CODE_SEQUENCE)
        object.__setattr__(
            self,
            "count",
            _require_nonnegative_count_decimal("count", self.count),
        )
        object.__setattr__(
            self,
            "deadline_ratio",
            _require_ratio_decimal("deadline_ratio", self.deadline_ratio),
        )
        _require_hard_flags("reason code count", self)


@dataclass(frozen=True)
class MarketResearchPolicyAgencyEnforcementDeadlineDigestReport:
    generated_at: datetime
    config_version: str
    digest_status: str
    next_step: str
    deadline_count: Decimal
    ready_deadline_count: Decimal
    watch_deadline_count: Decimal
    blocked_deadline_count: Decimal
    missed_deadline_count: Decimal
    imminent_deadline_count: Decimal
    material_deadline_count: Decimal
    stale_deadline_notice_count: Decimal
    thin_source_count: Decimal
    low_confirmation_count: Decimal
    probability_shift_count: Decimal
    average_materiality_score: Decimal
    min_seconds_until_deadline: Decimal
    max_deadline_notice_age_seconds: Decimal
    average_public_source_count: Decimal
    rows: tuple[MarketResearchPolicyAgencyEnforcementDeadlineDigestRow, ...]
    reason_code_counts: tuple[
        MarketResearchPolicyAgencyEnforcementDeadlineDigestReasonCodeCount,
        ...,
    ]
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketResearchPolicyAgencyEnforcementDeadlineDigestReport:
            raise TypeError(
                "MarketResearchPolicyAgencyEnforcementDeadlineDigestReport does not "
                "support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not MarketResearchPolicyAgencyEnforcementDeadlineDigestReport:
            raise ValueError(
                "report must be exactly "
                "MarketResearchPolicyAgencyEnforcementDeadlineDigestReport",
            )
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_string("config_version", self.config_version)
        _require_status("digest_status", self.digest_status)
        _require_public_string("next_step", self.next_step)
        for field_name in (
            "deadline_count",
            "ready_deadline_count",
            "watch_deadline_count",
            "blocked_deadline_count",
            "missed_deadline_count",
            "imminent_deadline_count",
            "material_deadline_count",
            "stale_deadline_notice_count",
            "thin_source_count",
            "low_confirmation_count",
            "probability_shift_count",
            "average_materiality_score",
            "min_seconds_until_deadline",
            "max_deadline_notice_age_seconds",
            "average_public_source_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
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
            _normalize_report_reason_codes(self.reason_codes),
        )
        _validate_report(self)
        _require_hard_flags("report", self)


def build_market_research_policy_agency_enforcement_deadline_digest(
    input_rows: list[MarketResearchPolicyAgencyEnforcementDeadlineDigestInputRow]
    | tuple[MarketResearchPolicyAgencyEnforcementDeadlineDigestInputRow, ...],
    *,
    config: MarketResearchPolicyAgencyEnforcementDeadlineDigestConfig | None = None,
    generated_at: datetime,
) -> MarketResearchPolicyAgencyEnforcementDeadlineDigestReport:
    cfg = config or MarketResearchPolicyAgencyEnforcementDeadlineDigestConfig()
    if type(cfg) is not MarketResearchPolicyAgencyEnforcementDeadlineDigestConfig:
        raise ValueError(
            "config must be a "
            "MarketResearchPolicyAgencyEnforcementDeadlineDigestConfig",
        )
    _require_hard_flags("config", cfg)
    report_time = _as_utc("generated_at", generated_at)
    normalized_rows = _normalize_input_rows(input_rows, report_time)
    built_rows = tuple(
        _build_row(row, config=cfg, generated_at=report_time)
        for row in normalized_rows
    )
    ranked_rows = _ranked_rows(built_rows)
    deadline_count = _count(len(ranked_rows))
    ready_deadline_count = _count(
        sum(1 for row in ranked_rows if row.deadline_status == STATUS_READY),
    )
    watch_deadline_count = _count(
        sum(1 for row in ranked_rows if row.deadline_status == STATUS_WATCH),
    )
    blocked_deadline_count = _count(
        sum(1 for row in ranked_rows if row.deadline_status == STATUS_BLOCKED),
    )
    reason_code_counts = _reason_code_counts(ranked_rows)
    reason_codes = tuple(row.reason_code for row in reason_code_counts)
    if not ranked_rows:
        reason_code_counts = (
            MarketResearchPolicyAgencyEnforcementDeadlineDigestReasonCodeCount(
                reason_code=NO_INPUTS_REASON,
                count=ONE,
                deadline_ratio=ONE,
            ),
        )
        reason_codes = (NO_INPUTS_REASON,)
    digest_status = _report_status(
        has_inputs=bool(ranked_rows),
        blocked_deadline_count=blocked_deadline_count,
        watch_deadline_count=watch_deadline_count,
    )
    return MarketResearchPolicyAgencyEnforcementDeadlineDigestReport(
        generated_at=report_time,
        config_version=cfg.config_version,
        digest_status=digest_status,
        next_step=NEXT_STEPS[digest_status],
        deadline_count=deadline_count,
        ready_deadline_count=ready_deadline_count,
        watch_deadline_count=watch_deadline_count,
        blocked_deadline_count=blocked_deadline_count,
        missed_deadline_count=_count(
            sum(1 for row in ranked_rows if MISSED_DEADLINE_REASON in row.reason_codes),
        ),
        imminent_deadline_count=_count(
            sum(
                1
                for row in ranked_rows
                if IMMINENT_DEADLINE_REASON in row.reason_codes
            ),
        ),
        material_deadline_count=_count(
            sum(
                1
                for row in ranked_rows
                if MATERIAL_BLOCK_REASON in row.reason_codes
                or MATERIAL_WATCH_REASON in row.reason_codes
            ),
        ),
        stale_deadline_notice_count=_count(
            sum(
                1
                for row in ranked_rows
                if STALE_DEADLINE_NOTICE_REASON in row.reason_codes
            ),
        ),
        thin_source_count=_count(
            sum(1 for row in ranked_rows if THIN_SOURCES_REASON in row.reason_codes),
        ),
        low_confirmation_count=_count(
            sum(1 for row in ranked_rows if LOW_CONFIRMATION_REASON in row.reason_codes),
        ),
        probability_shift_count=_count(
            sum(1 for row in ranked_rows if PROBABILITY_SHIFT_REASON in row.reason_codes),
        ),
        average_materiality_score=_ratio(
            _sum_decimal(row.enforcement_materiality_score for row in ranked_rows),
            deadline_count,
        ),
        min_seconds_until_deadline=min(
            (row.seconds_until_deadline for row in ranked_rows),
            default=ZERO,
        ),
        max_deadline_notice_age_seconds=max(
            (row.deadline_notice_age_seconds for row in ranked_rows),
            default=ZERO,
        ),
        average_public_source_count=_ratio(
            _sum_decimal(row.public_source_count for row in ranked_rows),
            deadline_count,
        ),
        rows=ranked_rows,
        reason_code_counts=reason_code_counts,
        reason_codes=reason_codes,
    )


def market_research_policy_agency_enforcement_deadline_digest_payload(
    report: MarketResearchPolicyAgencyEnforcementDeadlineDigestReport,
) -> dict[str, Any]:
    if type(report) is not MarketResearchPolicyAgencyEnforcementDeadlineDigestReport:
        raise ValueError(
            "report must be a "
            "MarketResearchPolicyAgencyEnforcementDeadlineDigestReport",
        )
    _require_hard_flags("report", report)
    _reject_unsafe_payload("report", report)
    payload = _json_ready(report)
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    _require_hard_flags("payload", _DictFlags(payload))
    _reject_unsafe_payload("payload", payload)
    return payload


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
    row: MarketResearchPolicyAgencyEnforcementDeadlineDigestInputRow,
    *,
    config: MarketResearchPolicyAgencyEnforcementDeadlineDigestConfig,
    generated_at: datetime,
) -> MarketResearchPolicyAgencyEnforcementDeadlineDigestRow:
    deadline_notice_age_seconds = _datetime_delta_seconds(
        generated_at,
        row.deadline_announced_at,
    )
    if row.enforcement_deadline_at >= generated_at:
        seconds_until_deadline = _datetime_delta_seconds(
            row.enforcement_deadline_at,
            generated_at,
        )
        deadline_overdue_seconds = ZERO
    else:
        seconds_until_deadline = ZERO
        deadline_overdue_seconds = _datetime_delta_seconds(
            generated_at,
            row.enforcement_deadline_at,
        )
    probability_change = _quantize(
        row.market_probability_after - row.market_probability_before,
    )
    reason_codes = _row_reason_codes(
        deadline_notice_age_seconds=deadline_notice_age_seconds,
        seconds_until_deadline=seconds_until_deadline,
        deadline_overdue_seconds=deadline_overdue_seconds,
        public_source_count=row.public_source_count,
        cross_source_confirmation=row.cross_source_confirmation,
        enforcement_materiality_score=row.enforcement_materiality_score,
        probability_change=probability_change,
        config=config,
    )
    return MarketResearchPolicyAgencyEnforcementDeadlineDigestRow(
        research_key=row.research_key,
        condition_id=row.condition_id,
        policy_area=row.policy_area,
        agency_name=row.agency_name,
        deadline_announced_at=row.deadline_announced_at,
        enforcement_deadline_at=row.enforcement_deadline_at,
        deadline_notice_age_seconds=deadline_notice_age_seconds,
        seconds_until_deadline=seconds_until_deadline,
        deadline_overdue_seconds=deadline_overdue_seconds,
        public_source_count=row.public_source_count,
        cross_source_confirmation=row.cross_source_confirmation,
        enforcement_materiality_score=row.enforcement_materiality_score,
        market_probability_before=row.market_probability_before,
        market_probability_after=row.market_probability_after,
        probability_change=probability_change,
        deadline_status=_row_status(reason_codes),
        redacted_deadline_reference=_redacted_reference(row.public_deadline_reference),
        reason_codes=reason_codes,
    )


def _normalize_input_rows(
    rows: object,
    generated_at: datetime,
) -> tuple[MarketResearchPolicyAgencyEnforcementDeadlineDigestInputRow, ...]:
    if type(rows) not in (list, tuple):
        raise ValueError("input rows must be a list or tuple")
    normalized = tuple(rows)
    seen: set[tuple[str, str]] = set()
    for row in normalized:
        if type(row) is not MarketResearchPolicyAgencyEnforcementDeadlineDigestInputRow:
            raise ValueError(
                "input rows must contain "
                "MarketResearchPolicyAgencyEnforcementDeadlineDigestInputRow",
            )
        _require_hard_flags("input row", row)
        if row.deadline_announced_at > generated_at:
            raise ValueError("deadline_announced_at must be on or before generated_at")
        key = (row.research_key, row.condition_id)
        if key in seen:
            raise ValueError("input rows must not contain duplicate research keys")
        seen.add(key)
    return normalized


def _row_reason_codes(
    *,
    deadline_notice_age_seconds: Decimal,
    seconds_until_deadline: Decimal,
    deadline_overdue_seconds: Decimal,
    public_source_count: Decimal,
    cross_source_confirmation: Decimal,
    enforcement_materiality_score: Decimal,
    probability_change: Decimal,
    config: MarketResearchPolicyAgencyEnforcementDeadlineDigestConfig,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    if enforcement_materiality_score >= config.materiality_block_threshold:
        reason_codes.append(MATERIAL_BLOCK_REASON)
    elif enforcement_materiality_score >= config.materiality_watch_threshold:
        reason_codes.append(MATERIAL_WATCH_REASON)
    if _abs_decimal(probability_change) >= PROBABILITY_SHIFT_THRESHOLD:
        reason_codes.append(PROBABILITY_SHIFT_REASON)
    if deadline_overdue_seconds > ZERO:
        reason_codes.append(MISSED_DEADLINE_REASON)
    elif seconds_until_deadline <= config.imminent_deadline_max_seconds:
        reason_codes.append(IMMINENT_DEADLINE_REASON)
    if cross_source_confirmation < config.min_cross_source_confirmation:
        reason_codes.append(LOW_CONFIRMATION_REASON)
    if deadline_notice_age_seconds > config.fresh_deadline_notice_max_age_seconds:
        reason_codes.append(STALE_DEADLINE_NOTICE_REASON)
    if public_source_count < config.min_public_source_count:
        reason_codes.append(THIN_SOURCES_REASON)
    if not reason_codes:
        reason_codes.append(READY_REASON)
    return tuple(
        reason_code
        for reason_code in ROW_REASON_CODE_SEQUENCE
        if reason_code in reason_codes
    )


def _row_status(reason_codes: tuple[str, ...]) -> str:
    if MATERIAL_BLOCK_REASON in reason_codes or MISSED_DEADLINE_REASON in reason_codes:
        return STATUS_BLOCKED
    if reason_codes == (READY_REASON,):
        return STATUS_READY
    return STATUS_WATCH


def _report_status(
    *,
    has_inputs: bool,
    blocked_deadline_count: Decimal,
    watch_deadline_count: Decimal,
) -> str:
    if not has_inputs or blocked_deadline_count > ZERO:
        return STATUS_BLOCKED
    if watch_deadline_count > ZERO:
        return STATUS_WATCH
    return STATUS_READY


def _ranked_rows(
    rows: tuple[MarketResearchPolicyAgencyEnforcementDeadlineDigestRow, ...],
) -> tuple[MarketResearchPolicyAgencyEnforcementDeadlineDigestRow, ...]:
    return tuple(
        sorted(
            rows,
            key=lambda row: (
                _status_rank(row.deadline_status),
                -row.enforcement_materiality_score,
                row.policy_area,
                row.research_key,
            ),
        ),
    )


def _status_rank(value: str) -> int:
    return {STATUS_BLOCKED: 0, STATUS_WATCH: 1, STATUS_READY: 2}[value]


def _reason_code_counts(
    rows: tuple[MarketResearchPolicyAgencyEnforcementDeadlineDigestRow, ...],
) -> tuple[MarketResearchPolicyAgencyEnforcementDeadlineDigestReasonCodeCount, ...]:
    total = _count(len(rows))
    counts: dict[str, Decimal] = {}
    for row in rows:
        for reason_code in row.reason_codes:
            counts[reason_code] = counts.get(reason_code, ZERO) + ONE
    return tuple(
        MarketResearchPolicyAgencyEnforcementDeadlineDigestReasonCodeCount(
            reason_code=reason_code,
            count=_count(counts[reason_code]),
            deadline_ratio=_ratio(counts[reason_code], total),
        )
        for reason_code in REASON_CODE_SEQUENCE
        if reason_code in counts
    )


def _normalize_rows(
    rows: object,
) -> tuple[MarketResearchPolicyAgencyEnforcementDeadlineDigestRow, ...]:
    if type(rows) is not tuple:
        raise ValueError("rows must be a tuple")
    for row in rows:
        if type(row) is not MarketResearchPolicyAgencyEnforcementDeadlineDigestRow:
            raise ValueError(
                "rows must contain "
                "MarketResearchPolicyAgencyEnforcementDeadlineDigestRow",
            )
        _require_hard_flags("row", row)
    if rows != _ranked_rows(rows):
        raise ValueError("rows must be sorted deterministically")
    return rows


def _normalize_reason_code_counts(
    rows: object,
) -> tuple[MarketResearchPolicyAgencyEnforcementDeadlineDigestReasonCodeCount, ...]:
    if type(rows) is not tuple:
        raise ValueError("reason_code_counts must be a tuple")
    previous_index = -1
    for row in rows:
        if type(row) is not MarketResearchPolicyAgencyEnforcementDeadlineDigestReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "MarketResearchPolicyAgencyEnforcementDeadlineDigestReasonCodeCount",
            )
        _require_hard_flags("reason code count", row)
        index = REASON_CODE_SEQUENCE.index(row.reason_code)
        if index <= previous_index:
            raise ValueError("reason_code_counts must be unique and sorted")
        previous_index = index
    return rows


def _normalize_row_reason_codes(value: tuple[str, ...]) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ValueError("reason_codes must be a tuple")
    for reason_code in value:
        _require_reason_code("reason_codes", reason_code, ROW_REASON_CODE_SEQUENCE)
    normalized = tuple(
        reason_code for reason_code in ROW_REASON_CODE_SEQUENCE if reason_code in value
    )
    if normalized != value:
        raise ValueError("reason_codes must be unique and sorted")
    if READY_REASON in value and len(value) != 1:
        raise ValueError("reason_codes cannot mix ready with risk reasons")
    return normalized


def _normalize_report_reason_codes(value: tuple[str, ...]) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ValueError("reason_codes must be a tuple")
    for reason_code in value:
        _require_reason_code("reason_codes", reason_code, REASON_CODE_SEQUENCE)
    normalized = tuple(
        reason_code for reason_code in REASON_CODE_SEQUENCE if reason_code in value
    )
    if normalized != value:
        raise ValueError("reason_codes must be unique and sorted")
    return normalized


def _validate_row(row: MarketResearchPolicyAgencyEnforcementDeadlineDigestRow) -> None:
    if row.enforcement_deadline_at < row.deadline_announced_at:
        raise ValueError(
            "enforcement_deadline_at must be on or after deadline_announced_at",
        )
    if row.seconds_until_deadline > ZERO and row.deadline_overdue_seconds > ZERO:
        raise ValueError(
            "seconds_until_deadline and deadline_overdue_seconds cannot both be positive",
        )
    expected_probability_change = _quantize(
        row.market_probability_after - row.market_probability_before,
    )
    if row.probability_change != expected_probability_change:
        raise ValueError("probability_change must match probability inputs")
    if row.deadline_status != _row_status(row.reason_codes):
        raise ValueError("deadline_status must match reason_codes")
    if not _is_redacted_reference(row.redacted_deadline_reference):
        raise ValueError("redacted_deadline_reference must be redacted or public")


def _validate_report(
    report: MarketResearchPolicyAgencyEnforcementDeadlineDigestReport,
) -> None:
    if report.next_step != NEXT_STEPS[report.digest_status]:
        raise ValueError("next_step must match digest_status")
    if report.deadline_count != _count(len(report.rows)):
        raise ValueError("deadline_count must match rows")
    expected_ready = _count(
        sum(1 for row in report.rows if row.deadline_status == STATUS_READY),
    )
    if report.ready_deadline_count != expected_ready:
        raise ValueError("ready_deadline_count must match rows")
    expected_watch = _count(
        sum(1 for row in report.rows if row.deadline_status == STATUS_WATCH),
    )
    if report.watch_deadline_count != expected_watch:
        raise ValueError("watch_deadline_count must match rows")
    expected_blocked = _count(
        sum(1 for row in report.rows if row.deadline_status == STATUS_BLOCKED),
    )
    if report.blocked_deadline_count != expected_blocked:
        raise ValueError("blocked_deadline_count must match rows")
    if report.missed_deadline_count != _count(
        sum(1 for row in report.rows if MISSED_DEADLINE_REASON in row.reason_codes),
    ):
        raise ValueError("missed_deadline_count must match rows")
    if report.imminent_deadline_count != _count(
        sum(1 for row in report.rows if IMMINENT_DEADLINE_REASON in row.reason_codes),
    ):
        raise ValueError("imminent_deadline_count must match rows")
    if report.material_deadline_count != _count(
        sum(
            1
            for row in report.rows
            if MATERIAL_BLOCK_REASON in row.reason_codes
            or MATERIAL_WATCH_REASON in row.reason_codes
        ),
    ):
        raise ValueError("material_deadline_count must match rows")
    if report.stale_deadline_notice_count != _count(
        sum(1 for row in report.rows if STALE_DEADLINE_NOTICE_REASON in row.reason_codes),
    ):
        raise ValueError("stale_deadline_notice_count must match rows")
    if report.thin_source_count != _count(
        sum(1 for row in report.rows if THIN_SOURCES_REASON in row.reason_codes),
    ):
        raise ValueError("thin_source_count must match rows")
    if report.low_confirmation_count != _count(
        sum(1 for row in report.rows if LOW_CONFIRMATION_REASON in row.reason_codes),
    ):
        raise ValueError("low_confirmation_count must match rows")
    if report.probability_shift_count != _count(
        sum(1 for row in report.rows if PROBABILITY_SHIFT_REASON in row.reason_codes),
    ):
        raise ValueError("probability_shift_count must match rows")
    if report.average_materiality_score != _ratio(
        _sum_decimal(row.enforcement_materiality_score for row in report.rows),
        report.deadline_count,
    ):
        raise ValueError("average_materiality_score must match rows")
    expected_min_seconds = min(
        (row.seconds_until_deadline for row in report.rows),
        default=ZERO,
    )
    if report.min_seconds_until_deadline != expected_min_seconds:
        raise ValueError("min_seconds_until_deadline must match rows")
    expected_max_age = max(
        (row.deadline_notice_age_seconds for row in report.rows),
        default=ZERO,
    )
    if report.max_deadline_notice_age_seconds != expected_max_age:
        raise ValueError("max_deadline_notice_age_seconds must match rows")
    if report.average_public_source_count != _ratio(
        _sum_decimal(row.public_source_count for row in report.rows),
        report.deadline_count,
    ):
        raise ValueError("average_public_source_count must match rows")
    expected_counts = _reason_code_counts(report.rows)
    expected_codes = tuple(row.reason_code for row in expected_counts)
    if not report.rows:
        expected_counts = (
            MarketResearchPolicyAgencyEnforcementDeadlineDigestReasonCodeCount(
                reason_code=NO_INPUTS_REASON,
                count=ONE,
                deadline_ratio=ONE,
            ),
        )
        expected_codes = (NO_INPUTS_REASON,)
    if report.reason_code_counts != expected_counts:
        raise ValueError("reason_code_counts must match rows")
    if report.reason_codes != expected_codes:
        raise ValueError("reason_codes must match reason_code_counts")
    expected_status = _report_status(
        has_inputs=bool(report.rows),
        blocked_deadline_count=report.blocked_deadline_count,
        watch_deadline_count=report.watch_deadline_count,
    )
    if report.digest_status != expected_status:
        raise ValueError("digest_status must match rows")


def _require_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in (STATUS_READY, STATUS_WATCH, STATUS_BLOCKED):
        raise ValueError(f"{field_name} must be a supported status")


def _require_reason_code(
    field_name: str,
    value: object,
    allowed_values: tuple[str, ...],
) -> None:
    if type(value) is not str or value not in allowed_values:
        raise ValueError(f"{field_name} must be a supported reason code")


def _require_public_string(field_name: str, value: object) -> str:
    if type(value) is not str or not value.strip() or value != value.strip():
        raise ValueError(f"{field_name} must be a non-empty string")
    _reject_unsafe_text(field_name, value)
    return value


def _require_reference(field_name: str, value: object) -> str:
    if type(value) is not str or not value.strip():
        raise ValueError(f"{field_name} must be a non-empty string")
    return value


def _require_redacted_reference(field_name: str, value: object) -> str:
    if type(value) is not str or not value.strip():
        raise ValueError(f"{field_name} must be a non-empty string")
    if not _is_redacted_reference(value):
        raise ValueError(f"{field_name} must be redacted or public")
    return value


def _reject_unsafe_text(field_name: str, value: str) -> None:
    lowered = value.lower()
    if any(fragment in lowered for fragment in UNSAFE_TEXT_FRAGMENTS):
        raise ValueError(f"{field_name} must not include sensitive or live-action text")


def _is_redacted_reference(value: str) -> bool:
    if value.startswith("sha256:") and len(value) == 19:
        return True
    lowered = value.lower()
    if any(fragment in lowered for fragment in UNSAFE_TEXT_FRAGMENTS):
        return False
    if "://" in lowered:
        return False
    return any(fragment in lowered for fragment in PUBLIC_REFERENCE_FRAGMENTS)


def _redacted_reference(value: str) -> str:
    if _is_redacted_reference(value):
        return value
    return f"sha256:{sha256(value.encode('utf-8')).hexdigest()[:12]}"


def _reject_unsafe_payload(label: str, value: object) -> None:
    text = repr(value).lower()
    for fragment in UNSAFE_TEXT_FRAGMENTS:
        if fragment in text:
            raise ValueError(f"{label} must not include unsafe text")
    if "://" in text:
        raise ValueError(f"{label} must not include unredacted references")


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if getattr(value, field_name, None) is not True:
            raise ValueError(f"{field_name} must be True for {label}")


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal or not value.is_finite():
        raise ValueError(f"{field_name} must be a finite Decimal")
    return _quantize(value)


def _require_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _require_nonnegative_count_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_nonnegative_decimal(field_name, value)
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{field_name} must be an integer Decimal count")
    return normalized


def _require_ratio_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < ZERO or normalized > ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return normalized


def _require_probability_change(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < -ONE or normalized > ONE:
        raise ValueError(f"{field_name} must be between -1 and 1")
    return normalized


def _datetime_delta_seconds(end: datetime, start: datetime) -> Decimal:
    delta = end - start
    total_microseconds = (
        Decimal(delta.days) * Decimal("86400000000")
        + Decimal(delta.seconds) * MICROSECONDS_PER_SECOND
        + Decimal(delta.microseconds)
    )
    return _quantize(total_microseconds / MICROSECONDS_PER_SECOND)


def _count(value: int) -> Decimal:
    return _quantize(Decimal(value))


def _sum_decimal(values: object) -> Decimal:
    total = ZERO
    for value in values:  # type: ignore[assignment]
        total += value
    return _quantize(total)


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO:
        return ZERO
    return _quantize(numerator / denominator)


def _abs_decimal(value: Decimal) -> Decimal:
    return -value if value < ZERO else value


def _quantize(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(QUANT)


def _json_ready(value: Any) -> Any:
    if value is None:
        return None
    if is_dataclass(value) and not isinstance(value, type):
        return _json_ready(asdict(value))
    if isinstance(value, Decimal):
        if not value.is_finite():
            raise ValueError("Decimal value must be finite")
        return str(value)
    if isinstance(value, datetime):
        return _as_utc("datetime", value).isoformat()
    if isinstance(value, float):
        raise ValueError("JSON value must not be a float")
    if isinstance(value, (str, int, bool)):
        return value
    if isinstance(value, dict):
        output: dict[str, Any] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            output[key] = _json_ready(item)
        return output
    if isinstance(value, (list, tuple)):
        return [_json_ready(item) for item in value]
    raise ValueError("value is not JSON serializable")
