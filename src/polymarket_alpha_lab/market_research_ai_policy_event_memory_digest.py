"""Pure Phase 1 market research AI-policy event memory reducer."""

from __future__ import annotations

from dataclasses import asdict, dataclass, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
from typing import Any

from polymarket_alpha_lab.team_paper_guard import require_paper_only_flags


DEFAULT_MARKET_RESEARCH_AI_POLICY_EVENT_MEMORY_DIGEST_CONFIG_VERSION = (
    "market-research-ai-policy-event-memory-digest-v0"
)

STATUS_READY = "ready"
STATUS_WATCH = "watch"
STATUS_BLOCKED = "blocked"
MEMORY_STATUSES = (STATUS_READY, STATUS_WATCH, STATUS_BLOCKED)

NO_INPUTS_REASON = "market_research_ai_policy_event_memory_digest_no_inputs"
READY_REASON = "market_research_ai_policy_event_memory_digest_ready"
ALIGNMENT_GAP_REASON = "market_research_ai_policy_event_memory_digest_alignment_gap"
CALENDAR_FAR_REASON = "market_research_ai_policy_event_memory_digest_calendar_far"
CONFIDENCE_DECAY_BLOCK_REASON = (
    "market_research_ai_policy_event_memory_digest_confidence_decay_block"
)
CONFIDENCE_DECAY_WATCH_REASON = (
    "market_research_ai_policy_event_memory_digest_confidence_decay_watch"
)
MISSING_SIGNAL_REASON = (
    "market_research_ai_policy_event_memory_digest_missing_company_agency_signal"
)
MISSING_REGULATOR_SOURCE_REASON = (
    "market_research_ai_policy_event_memory_digest_missing_regulator_source"
)
POLICY_DRAFT_UNDERSPECIFIED_REASON = (
    "market_research_ai_policy_event_memory_digest_policy_draft_underspecified"
)
SOURCE_FAMILY_THIN_REASON = (
    "market_research_ai_policy_event_memory_digest_source_family_thin"
)
STALE_EVIDENCE_REASON = "market_research_ai_policy_event_memory_digest_stale_evidence"
STALE_REGULATOR_SOURCE_REASON = (
    "market_research_ai_policy_event_memory_digest_stale_regulator_source"
)
VOLATILITY_LIQUIDITY_GAP_REASON = (
    "market_research_ai_policy_event_memory_digest_volatility_liquidity_gap"
)

REASON_CODE_SEQUENCE = (
    NO_INPUTS_REASON,
    ALIGNMENT_GAP_REASON,
    CALENDAR_FAR_REASON,
    CONFIDENCE_DECAY_BLOCK_REASON,
    CONFIDENCE_DECAY_WATCH_REASON,
    MISSING_SIGNAL_REASON,
    MISSING_REGULATOR_SOURCE_REASON,
    POLICY_DRAFT_UNDERSPECIFIED_REASON,
    READY_REASON,
    SOURCE_FAMILY_THIN_REASON,
    STALE_EVIDENCE_REASON,
    STALE_REGULATOR_SOURCE_REASON,
    VOLATILITY_LIQUIDITY_GAP_REASON,
)
ROW_REASON_CODE_SEQUENCE = (
    ALIGNMENT_GAP_REASON,
    CALENDAR_FAR_REASON,
    CONFIDENCE_DECAY_BLOCK_REASON,
    CONFIDENCE_DECAY_WATCH_REASON,
    MISSING_SIGNAL_REASON,
    MISSING_REGULATOR_SOURCE_REASON,
    POLICY_DRAFT_UNDERSPECIFIED_REASON,
    READY_REASON,
    SOURCE_FAMILY_THIN_REASON,
    STALE_EVIDENCE_REASON,
    STALE_REGULATOR_SOURCE_REASON,
    VOLATILITY_LIQUIDITY_GAP_REASON,
)

DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
QUANT = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
MICROSECONDS_PER_SECOND = Decimal("1000000")

_STATUS_NEXT_STEPS = {
    STATUS_READY: "allow_report_only_market_research_ai_policy_event_memory_digest",
    STATUS_WATCH: "watch_report_only_market_research_ai_policy_event_memory_digest",
    STATUS_BLOCKED: "block_report_only_market_research_ai_policy_event_memory_digest",
}

def _join_parts(*parts: str) -> str:
    return "".join(parts)


UNSAFE_TEXT_FRAGMENTS = frozenset(
    (
        _join_parts("au", "th"),
        _join_parts("bro", "ker"),
        _join_parts("sig", "ning"),
        _join_parts("sub", "mit"),
        _join_parts("can", "cel"),
        _join_parts("wal", "let"),
        _join_parts("acc", "ount"),
        _join_parts("ad", "vice"),
        _join_parts("net", "work"),
        _join_parts("data", "base"),
        _join_parts("pay", "load"),
        _join_parts("sec", "ret"),
        _join_parts("to", "ken"),
        _join_parts("pri", "vate"),
    ),
)


__all__ = (
    "DEFAULT_MARKET_RESEARCH_AI_POLICY_EVENT_MEMORY_DIGEST_CONFIG_VERSION",
    "MarketResearchAIPolicyEventMemoryDigestConfig",
    "MarketResearchAIPolicyEventMemoryDigestInputRow",
    "MarketResearchAIPolicyEventMemoryDigestReasonCodeCount",
    "MarketResearchAIPolicyEventMemoryDigestReport",
    "MarketResearchAIPolicyEventMemoryDigestRow",
    "build_market_research_ai_policy_event_memory_digest",
    "market_research_ai_policy_event_memory_digest_payload",
)


@dataclass(frozen=True)
class MarketResearchAIPolicyEventMemoryDigestConfig:
    config_version: str = (
        DEFAULT_MARKET_RESEARCH_AI_POLICY_EVENT_MEMORY_DIGEST_CONFIG_VERSION
    )
    fresh_regulator_source_max_age_seconds: Decimal = Decimal("43200.000000")
    min_policy_draft_specificity_score: Decimal = Decimal("0.650000")
    legislative_calendar_window_seconds: Decimal = Decimal("604800.000000")
    min_company_agency_alignment_score: Decimal = Decimal("0.600000")
    min_source_family_count: Decimal = Decimal("2")
    stale_evidence_threshold: Decimal = Decimal("1")
    volatility_liquidity_gap_threshold: Decimal = Decimal("0.250000")
    confidence_decay_watch_threshold: Decimal = Decimal("0.150000")
    confidence_decay_block_threshold: Decimal = Decimal("0.350000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketResearchAIPolicyEventMemoryDigestConfig:
            raise TypeError(
                "MarketResearchAIPolicyEventMemoryDigestConfig does not support "
                "subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not MarketResearchAIPolicyEventMemoryDigestConfig:
            raise ValueError(
                "config must be exactly MarketResearchAIPolicyEventMemoryDigestConfig",
            )
        _require_public_string("config_version", self.config_version)
        for field_name in (
            "fresh_regulator_source_max_age_seconds",
            "legislative_calendar_window_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_positive_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in ("min_source_family_count", "stale_evidence_threshold"):
            object.__setattr__(
                self,
                field_name,
                _require_positive_count_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "min_policy_draft_specificity_score",
            "min_company_agency_alignment_score",
            "volatility_liquidity_gap_threshold",
            "confidence_decay_watch_threshold",
            "confidence_decay_block_threshold",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        if self.confidence_decay_watch_threshold > self.confidence_decay_block_threshold:
            raise ValueError(
                "confidence_decay_watch_threshold must not exceed "
                "confidence_decay_block_threshold",
            )
        require_paper_only_flags("config", self)


@dataclass(frozen=True)
class MarketResearchAIPolicyEventMemoryDigestInputRow:
    market_research_key: str
    ai_policy_event_key: str
    regulator_family: str
    ai_policy_reference: str
    regulator_source_observed_at: datetime | None
    policy_draft_observed_at: datetime
    legislative_calendar_at: datetime
    company_signal_observed_at: datetime | None
    agency_signal_observed_at: datetime | None
    regulator_source_count: Decimal
    source_family_count: Decimal
    stale_evidence_count: Decimal
    policy_draft_specificity_score: Decimal
    legislative_calendar_proximity_score: Decimal
    company_agency_alignment_score: Decimal
    volatility_score: Decimal
    liquidity_score: Decimal
    volatility_liquidity_gap_score: Decimal
    starting_confidence_score: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketResearchAIPolicyEventMemoryDigestInputRow:
            raise TypeError(
                "MarketResearchAIPolicyEventMemoryDigestInputRow does not support "
                "subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not MarketResearchAIPolicyEventMemoryDigestInputRow:
            raise ValueError(
                "input row must be exactly "
                "MarketResearchAIPolicyEventMemoryDigestInputRow",
            )
        _require_public_string("market_research_key", self.market_research_key)
        _require_public_string("ai_policy_event_key", self.ai_policy_event_key)
        _require_public_string("regulator_family", self.regulator_family)
        _require_reference("ai_policy_reference", self.ai_policy_reference)
        object.__setattr__(
            self,
            "regulator_source_observed_at",
            _as_optional_utc(
                "regulator_source_observed_at",
                self.regulator_source_observed_at,
            ),
        )
        object.__setattr__(
            self,
            "policy_draft_observed_at",
            _as_utc("policy_draft_observed_at", self.policy_draft_observed_at),
        )
        object.__setattr__(
            self,
            "legislative_calendar_at",
            _as_utc("legislative_calendar_at", self.legislative_calendar_at),
        )
        object.__setattr__(
            self,
            "company_signal_observed_at",
            _as_optional_utc(
                "company_signal_observed_at",
                self.company_signal_observed_at,
            ),
        )
        object.__setattr__(
            self,
            "agency_signal_observed_at",
            _as_optional_utc("agency_signal_observed_at", self.agency_signal_observed_at),
        )
        if self.policy_draft_observed_at > self.legislative_calendar_at:
            raise ValueError(
                "policy_draft_observed_at must not be after legislative_calendar_at",
            )
        if (
            self.regulator_source_observed_at is not None
            and self.policy_draft_observed_at > self.regulator_source_observed_at
        ):
            raise ValueError(
                "policy_draft_observed_at must not be after regulator_source_observed_at",
            )
        for field_name in (
            "regulator_source_count",
            "source_family_count",
            "stale_evidence_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_count_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "policy_draft_specificity_score",
            "legislative_calendar_proximity_score",
            "company_agency_alignment_score",
            "volatility_score",
            "liquidity_score",
            "volatility_liquidity_gap_score",
            "starting_confidence_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        require_paper_only_flags("input row", self)


@dataclass(frozen=True)
class MarketResearchAIPolicyEventMemoryDigestRow:
    market_research_key: str
    ai_policy_event_key: str
    regulator_family: str
    memory_status: str
    regulator_source_observed_at: datetime | None
    policy_draft_observed_at: datetime
    legislative_calendar_at: datetime
    company_signal_observed_at: datetime | None
    agency_signal_observed_at: datetime | None
    regulator_source_age_seconds: Decimal | None
    policy_draft_age_seconds: Decimal
    legislative_calendar_seconds: Decimal
    company_signal_age_seconds: Decimal | None
    agency_signal_age_seconds: Decimal | None
    regulator_source_count: Decimal
    source_family_count: Decimal
    stale_evidence_count: Decimal
    policy_draft_specificity_score: Decimal
    legislative_calendar_proximity_score: Decimal
    company_agency_alignment_score: Decimal
    volatility_score: Decimal
    liquidity_score: Decimal
    volatility_liquidity_gap_score: Decimal
    starting_confidence_score: Decimal
    final_confidence_score: Decimal
    confidence_decay_score: Decimal
    redacted_ai_policy_reference: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketResearchAIPolicyEventMemoryDigestRow:
            raise TypeError(
                "MarketResearchAIPolicyEventMemoryDigestRow does not support "
                "subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not MarketResearchAIPolicyEventMemoryDigestRow:
            raise ValueError(
                "row must be exactly MarketResearchAIPolicyEventMemoryDigestRow",
            )
        _require_public_string("market_research_key", self.market_research_key)
        _require_public_string("ai_policy_event_key", self.ai_policy_event_key)
        _require_public_string("regulator_family", self.regulator_family)
        _require_memory_status("memory_status", self.memory_status)
        object.__setattr__(
            self,
            "regulator_source_observed_at",
            _as_optional_utc(
                "regulator_source_observed_at",
                self.regulator_source_observed_at,
            ),
        )
        object.__setattr__(
            self,
            "policy_draft_observed_at",
            _as_utc("policy_draft_observed_at", self.policy_draft_observed_at),
        )
        object.__setattr__(
            self,
            "legislative_calendar_at",
            _as_utc("legislative_calendar_at", self.legislative_calendar_at),
        )
        object.__setattr__(
            self,
            "company_signal_observed_at",
            _as_optional_utc(
                "company_signal_observed_at",
                self.company_signal_observed_at,
            ),
        )
        object.__setattr__(
            self,
            "agency_signal_observed_at",
            _as_optional_utc("agency_signal_observed_at", self.agency_signal_observed_at),
        )
        object.__setattr__(
            self,
            "regulator_source_age_seconds",
            _require_optional_nonnegative_decimal(
                "regulator_source_age_seconds",
                self.regulator_source_age_seconds,
            ),
        )
        for field_name in (
            "policy_draft_age_seconds",
            "legislative_calendar_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in ("company_signal_age_seconds", "agency_signal_age_seconds"):
            object.__setattr__(
                self,
                field_name,
                _require_optional_nonnegative_decimal(
                    field_name,
                    getattr(self, field_name),
                ),
            )
        for field_name in (
            "regulator_source_count",
            "source_family_count",
            "stale_evidence_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_count_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "policy_draft_specificity_score",
            "legislative_calendar_proximity_score",
            "company_agency_alignment_score",
            "volatility_score",
            "liquidity_score",
            "volatility_liquidity_gap_score",
            "starting_confidence_score",
            "final_confidence_score",
            "confidence_decay_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "redacted_ai_policy_reference",
            _require_redacted_reference(
                "redacted_ai_policy_reference",
                self.redacted_ai_policy_reference,
            ),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_row_reason_codes(self.reason_codes),
        )
        _validate_digest_row(self)
        require_paper_only_flags("row", self)


@dataclass(frozen=True)
class MarketResearchAIPolicyEventMemoryDigestReasonCodeCount:
    reason_code: str
    count: Decimal
    event_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketResearchAIPolicyEventMemoryDigestReasonCodeCount:
            raise TypeError(
                "MarketResearchAIPolicyEventMemoryDigestReasonCodeCount does not "
                "support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not MarketResearchAIPolicyEventMemoryDigestReasonCodeCount:
            raise ValueError(
                "reason count must be exactly "
                "MarketResearchAIPolicyEventMemoryDigestReasonCodeCount",
            )
        _require_reason_code("reason_code", self.reason_code)
        object.__setattr__(
            self,
            "count",
            _require_nonnegative_count_decimal("count", self.count),
        )
        object.__setattr__(
            self,
            "event_ratio",
            _require_ratio_decimal("event_ratio", self.event_ratio),
        )
        require_paper_only_flags("reason count", self)


@dataclass(frozen=True)
class MarketResearchAIPolicyEventMemoryDigestReport:
    generated_at: datetime
    config_version: str
    digest_status: str
    recommended_next_step: str
    ai_policy_event_count: Decimal
    ready_event_count: Decimal
    watch_event_count: Decimal
    blocked_event_count: Decimal
    fresh_regulator_source_event_count: Decimal
    stale_regulator_source_event_count: Decimal
    missing_regulator_source_event_count: Decimal
    specific_policy_draft_event_count: Decimal
    near_legislative_calendar_event_count: Decimal
    aligned_company_agency_event_count: Decimal
    diverse_source_family_event_count: Decimal
    stale_evidence_event_count: Decimal
    volatility_liquidity_gap_event_count: Decimal
    total_stale_evidence_count: Decimal
    average_starting_confidence_score: Decimal
    average_final_confidence_score: Decimal
    average_confidence_decay_score: Decimal
    max_regulator_source_age_seconds: Decimal
    source_family_diversity_ratio: Decimal
    rows: tuple[MarketResearchAIPolicyEventMemoryDigestRow, ...]
    reason_code_counts: tuple[MarketResearchAIPolicyEventMemoryDigestReasonCodeCount, ...]
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketResearchAIPolicyEventMemoryDigestReport:
            raise TypeError(
                "MarketResearchAIPolicyEventMemoryDigestReport does not support "
                "subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not MarketResearchAIPolicyEventMemoryDigestReport:
            raise ValueError(
                "report must be exactly MarketResearchAIPolicyEventMemoryDigestReport",
            )
        object.__setattr__(
            self,
            "generated_at",
            _as_utc("generated_at", self.generated_at),
        )
        _require_public_string("config_version", self.config_version)
        _require_memory_status("digest_status", self.digest_status)
        if self.recommended_next_step != _STATUS_NEXT_STEPS[self.digest_status]:
            raise ValueError("recommended_next_step must match digest_status")
        for field_name in (
            "ai_policy_event_count",
            "ready_event_count",
            "watch_event_count",
            "blocked_event_count",
            "fresh_regulator_source_event_count",
            "stale_regulator_source_event_count",
            "missing_regulator_source_event_count",
            "specific_policy_draft_event_count",
            "near_legislative_calendar_event_count",
            "aligned_company_agency_event_count",
            "diverse_source_family_event_count",
            "stale_evidence_event_count",
            "volatility_liquidity_gap_event_count",
            "total_stale_evidence_count",
            "max_regulator_source_age_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_count_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "average_starting_confidence_score",
            "average_final_confidence_score",
            "average_confidence_decay_score",
            "source_family_diversity_ratio",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(self, "rows", _normalize_digest_rows(self.rows))
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes),
        )
        _validate_report(self)
        require_paper_only_flags("report", self)


def market_research_ai_policy_event_memory_digest_payload(
    report: MarketResearchAIPolicyEventMemoryDigestReport,
) -> dict[str, Any]:
    if type(report) is not MarketResearchAIPolicyEventMemoryDigestReport:
        raise ValueError(
            "report must be a MarketResearchAIPolicyEventMemoryDigestReport",
        )
    require_paper_only_flags("report", report)
    _reject_unsafe_payload("report", report)
    payload = _json_ready(report)
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    require_paper_only_flags("payload", _DictFlags(payload))
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


def build_market_research_ai_policy_event_memory_digest(
    input_rows: list[MarketResearchAIPolicyEventMemoryDigestInputRow]
    | tuple[MarketResearchAIPolicyEventMemoryDigestInputRow, ...],
    *,
    config: MarketResearchAIPolicyEventMemoryDigestConfig,
    generated_at: datetime,
) -> MarketResearchAIPolicyEventMemoryDigestReport:
    if type(config) is not MarketResearchAIPolicyEventMemoryDigestConfig:
        raise ValueError(
            "config must be a MarketResearchAIPolicyEventMemoryDigestConfig",
        )
    require_paper_only_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    rows = tuple(
        _build_digest_row(input_row, config=config, generated_at=generated_at_utc)
        for input_row in _normalize_input_rows(input_rows, generated_at_utc)
    )
    ordered_rows = _ordered_digest_rows(rows)
    if ordered_rows:
        reason_code_counts = _reason_code_counts(ordered_rows)
        reason_codes = tuple(row.reason_code for row in reason_code_counts)
    else:
        reason_code_counts = (
            MarketResearchAIPolicyEventMemoryDigestReasonCodeCount(
                reason_code=NO_INPUTS_REASON,
                count=ONE,
                event_ratio=ZERO,
            ),
        )
        reason_codes = (NO_INPUTS_REASON,)

    ai_policy_event_count = _count(len(ordered_rows))
    ready_event_count = _count(
        sum(1 for row in ordered_rows if row.memory_status == STATUS_READY),
    )
    watch_event_count = _count(
        sum(1 for row in ordered_rows if row.memory_status == STATUS_WATCH),
    )
    blocked_event_count = _count(
        sum(1 for row in ordered_rows if row.memory_status == STATUS_BLOCKED),
    )
    regulator_source_age_values = tuple(
        row.regulator_source_age_seconds
        for row in ordered_rows
        if row.regulator_source_age_seconds is not None
    )
    digest_status = _report_status(
        blocked_event_count=blocked_event_count,
        watch_event_count=watch_event_count,
        has_inputs=bool(ordered_rows),
    )

    return MarketResearchAIPolicyEventMemoryDigestReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        digest_status=digest_status,
        recommended_next_step=_STATUS_NEXT_STEPS[digest_status],
        ai_policy_event_count=ai_policy_event_count,
        ready_event_count=ready_event_count,
        watch_event_count=watch_event_count,
        blocked_event_count=blocked_event_count,
        fresh_regulator_source_event_count=_count(
            sum(
                1
                for row in ordered_rows
                if (
                    row.regulator_source_age_seconds is not None
                    and row.regulator_source_age_seconds
                    <= config.fresh_regulator_source_max_age_seconds
                )
            ),
        ),
        stale_regulator_source_event_count=_count(
            sum(
                1
                for row in ordered_rows
                if STALE_REGULATOR_SOURCE_REASON in row.reason_codes
            ),
        ),
        missing_regulator_source_event_count=_count(
            sum(
                1
                for row in ordered_rows
                if MISSING_REGULATOR_SOURCE_REASON in row.reason_codes
            ),
        ),
        specific_policy_draft_event_count=_count(
            sum(
                1
                for row in ordered_rows
                if row.policy_draft_specificity_score
                >= config.min_policy_draft_specificity_score
            ),
        ),
        near_legislative_calendar_event_count=_count(
            sum(
                1
                for row in ordered_rows
                if row.legislative_calendar_seconds
                <= config.legislative_calendar_window_seconds
            ),
        ),
        aligned_company_agency_event_count=_count(
            sum(
                1
                for row in ordered_rows
                if row.company_agency_alignment_score
                >= config.min_company_agency_alignment_score
            ),
        ),
        diverse_source_family_event_count=_count(
            sum(
                1
                for row in ordered_rows
                if row.source_family_count >= config.min_source_family_count
            ),
        ),
        stale_evidence_event_count=_count(
            sum(1 for row in ordered_rows if STALE_EVIDENCE_REASON in row.reason_codes),
        ),
        volatility_liquidity_gap_event_count=_count(
            sum(
                1
                for row in ordered_rows
                if VOLATILITY_LIQUIDITY_GAP_REASON in row.reason_codes
            ),
        ),
        total_stale_evidence_count=_sum_decimal(
            row.stale_evidence_count for row in ordered_rows
        ),
        average_starting_confidence_score=_average(
            row.starting_confidence_score for row in ordered_rows
        ),
        average_final_confidence_score=_average(
            row.final_confidence_score for row in ordered_rows
        ),
        average_confidence_decay_score=_average(
            row.confidence_decay_score for row in ordered_rows
        ),
        max_regulator_source_age_seconds=(
            max(regulator_source_age_values) if regulator_source_age_values else ZERO
        ),
        source_family_diversity_ratio=_ratio(
            _count(
                sum(
                    1
                    for row in ordered_rows
                    if row.source_family_count >= config.min_source_family_count
                ),
            ),
            ai_policy_event_count,
        ),
        rows=ordered_rows,
        reason_code_counts=reason_code_counts,
        reason_codes=reason_codes,
    )


def _normalize_input_rows(
    input_rows: object,
    generated_at: datetime,
) -> tuple[MarketResearchAIPolicyEventMemoryDigestInputRow, ...]:
    if type(input_rows) not in (list, tuple):
        raise ValueError("input rows must be a list or tuple")
    normalized = tuple(input_rows)
    for input_row in normalized:
        if type(input_row) is not MarketResearchAIPolicyEventMemoryDigestInputRow:
            raise ValueError(
                "input rows must contain "
                "MarketResearchAIPolicyEventMemoryDigestInputRow values",
            )
        require_paper_only_flags("input row", input_row)
        for field_name in (
            "regulator_source_observed_at",
            "policy_draft_observed_at",
            "company_signal_observed_at",
            "agency_signal_observed_at",
        ):
            observed_at = getattr(input_row, field_name)
            if observed_at is not None and observed_at > generated_at:
                raise ValueError(f"{field_name} cannot be after generated_at")
    return normalized


def _build_digest_row(
    input_row: MarketResearchAIPolicyEventMemoryDigestInputRow,
    *,
    config: MarketResearchAIPolicyEventMemoryDigestConfig,
    generated_at: datetime,
) -> MarketResearchAIPolicyEventMemoryDigestRow:
    regulator_source_age_seconds = (
        None
        if input_row.regulator_source_observed_at is None
        or input_row.regulator_source_count == ZERO
        else _seconds_between(input_row.regulator_source_observed_at, generated_at)
    )
    policy_draft_age_seconds = _seconds_between(
        input_row.policy_draft_observed_at,
        generated_at,
    )
    legislative_calendar_seconds = abs(
        _seconds_between(generated_at, input_row.legislative_calendar_at),
    )
    company_signal_age_seconds = (
        None
        if input_row.company_signal_observed_at is None
        else _seconds_between(input_row.company_signal_observed_at, generated_at)
    )
    agency_signal_age_seconds = (
        None
        if input_row.agency_signal_observed_at is None
        else _seconds_between(input_row.agency_signal_observed_at, generated_at)
    )
    final_confidence_score = _final_confidence_score(input_row, config=config)
    confidence_decay_score = _quantize(
        max(ZERO, input_row.starting_confidence_score - final_confidence_score),
    )
    reason_codes = _row_reason_codes(
        input_row,
        config=config,
        regulator_source_age_seconds=regulator_source_age_seconds,
        legislative_calendar_seconds=legislative_calendar_seconds,
        confidence_decay_score=confidence_decay_score,
    )

    return MarketResearchAIPolicyEventMemoryDigestRow(
        market_research_key=input_row.market_research_key,
        ai_policy_event_key=input_row.ai_policy_event_key,
        regulator_family=input_row.regulator_family,
        memory_status=_row_status(reason_codes),
        regulator_source_observed_at=input_row.regulator_source_observed_at,
        policy_draft_observed_at=input_row.policy_draft_observed_at,
        legislative_calendar_at=input_row.legislative_calendar_at,
        company_signal_observed_at=input_row.company_signal_observed_at,
        agency_signal_observed_at=input_row.agency_signal_observed_at,
        regulator_source_age_seconds=regulator_source_age_seconds,
        policy_draft_age_seconds=policy_draft_age_seconds,
        legislative_calendar_seconds=legislative_calendar_seconds,
        company_signal_age_seconds=company_signal_age_seconds,
        agency_signal_age_seconds=agency_signal_age_seconds,
        regulator_source_count=input_row.regulator_source_count,
        source_family_count=input_row.source_family_count,
        stale_evidence_count=input_row.stale_evidence_count,
        policy_draft_specificity_score=input_row.policy_draft_specificity_score,
        legislative_calendar_proximity_score=(
            input_row.legislative_calendar_proximity_score
        ),
        company_agency_alignment_score=input_row.company_agency_alignment_score,
        volatility_score=input_row.volatility_score,
        liquidity_score=input_row.liquidity_score,
        volatility_liquidity_gap_score=input_row.volatility_liquidity_gap_score,
        starting_confidence_score=input_row.starting_confidence_score,
        final_confidence_score=final_confidence_score,
        confidence_decay_score=confidence_decay_score,
        redacted_ai_policy_reference=_redacted_reference(input_row.ai_policy_reference),
        reason_codes=reason_codes,
    )


def _row_reason_codes(
    input_row: MarketResearchAIPolicyEventMemoryDigestInputRow,
    *,
    config: MarketResearchAIPolicyEventMemoryDigestConfig,
    regulator_source_age_seconds: Decimal | None,
    legislative_calendar_seconds: Decimal,
    confidence_decay_score: Decimal,
) -> tuple[str, ...]:
    reasons: list[str] = []
    if input_row.company_agency_alignment_score < config.min_company_agency_alignment_score:
        reasons.append(ALIGNMENT_GAP_REASON)
    if legislative_calendar_seconds > config.legislative_calendar_window_seconds:
        reasons.append(CALENDAR_FAR_REASON)
    if confidence_decay_score >= config.confidence_decay_block_threshold:
        reasons.append(CONFIDENCE_DECAY_BLOCK_REASON)
    elif confidence_decay_score >= config.confidence_decay_watch_threshold:
        reasons.append(CONFIDENCE_DECAY_WATCH_REASON)
    if (
        input_row.company_signal_observed_at is None
        or input_row.agency_signal_observed_at is None
    ):
        reasons.append(MISSING_SIGNAL_REASON)
    if regulator_source_age_seconds is None:
        reasons.append(MISSING_REGULATOR_SOURCE_REASON)
    if (
        input_row.policy_draft_specificity_score
        < config.min_policy_draft_specificity_score
    ):
        reasons.append(POLICY_DRAFT_UNDERSPECIFIED_REASON)
    if input_row.source_family_count < config.min_source_family_count:
        reasons.append(SOURCE_FAMILY_THIN_REASON)
    if input_row.stale_evidence_count >= config.stale_evidence_threshold:
        reasons.append(STALE_EVIDENCE_REASON)
    if (
        regulator_source_age_seconds is not None
        and regulator_source_age_seconds
        > config.fresh_regulator_source_max_age_seconds
    ):
        reasons.append(STALE_REGULATOR_SOURCE_REASON)
    if input_row.volatility_liquidity_gap_score >= config.volatility_liquidity_gap_threshold:
        reasons.append(VOLATILITY_LIQUIDITY_GAP_REASON)
    if not reasons:
        reasons.append(READY_REASON)
    return _normalize_row_reason_codes(tuple(reasons))


def _final_confidence_score(
    input_row: MarketResearchAIPolicyEventMemoryDigestInputRow,
    *,
    config: MarketResearchAIPolicyEventMemoryDigestConfig,
) -> Decimal:
    base_score = _average(
        (
            input_row.policy_draft_specificity_score,
            input_row.legislative_calendar_proximity_score,
            input_row.company_agency_alignment_score,
        ),
    )
    stale_penalty = _quantize(input_row.stale_evidence_count * Decimal("0.030000"))
    gap_penalty = _quantize(input_row.volatility_liquidity_gap_score * Decimal("0.200000"))
    source_family_penalty = (
        ZERO
        if input_row.source_family_count >= config.min_source_family_count
        else Decimal("0.050000")
    )
    missing_source_penalty = (
        Decimal("0.060000")
        if input_row.regulator_source_observed_at is None
        or input_row.regulator_source_count == ZERO
        else ZERO
    )
    missing_signal_penalty = (
        Decimal("0.040000")
        if input_row.company_signal_observed_at is None
        or input_row.agency_signal_observed_at is None
        else ZERO
    )
    return _quantize(
        base_score
        - stale_penalty
        - gap_penalty
        - source_family_penalty
        - missing_source_penalty
        - missing_signal_penalty,
    )


def _row_status(reason_codes: tuple[str, ...]) -> str:
    if (
        MISSING_REGULATOR_SOURCE_REASON in reason_codes
        or CONFIDENCE_DECAY_BLOCK_REASON in reason_codes
    ):
        return STATUS_BLOCKED
    if reason_codes == (READY_REASON,):
        return STATUS_READY
    return STATUS_WATCH


def _report_status(
    *,
    blocked_event_count: Decimal,
    watch_event_count: Decimal,
    has_inputs: bool,
) -> str:
    if not has_inputs or blocked_event_count > ZERO:
        return STATUS_BLOCKED
    if watch_event_count > ZERO:
        return STATUS_WATCH
    return STATUS_READY


def _ordered_digest_rows(
    rows: tuple[MarketResearchAIPolicyEventMemoryDigestRow, ...],
) -> tuple[MarketResearchAIPolicyEventMemoryDigestRow, ...]:
    status_rank = {STATUS_BLOCKED: 0, STATUS_WATCH: 1, STATUS_READY: 2}
    return tuple(
        sorted(
            rows,
            key=lambda row: (
                status_rank[row.memory_status],
                row.ai_policy_event_key,
                row.market_research_key,
            ),
        ),
    )


def _reason_code_counts(
    rows: tuple[MarketResearchAIPolicyEventMemoryDigestRow, ...],
) -> tuple[MarketResearchAIPolicyEventMemoryDigestReasonCodeCount, ...]:
    row_count = _count(len(rows))
    counts: dict[str, Decimal] = {}
    for row in rows:
        for reason_code in row.reason_codes:
            counts[reason_code] = counts.get(reason_code, ZERO) + ONE
    return tuple(
        MarketResearchAIPolicyEventMemoryDigestReasonCodeCount(
            reason_code=reason_code,
            count=counts[reason_code],
            event_ratio=_ratio(counts[reason_code], row_count),
        )
        for reason_code in REASON_CODE_SEQUENCE
        if reason_code in counts
    )


def _normalize_digest_rows(
    rows: object,
) -> tuple[MarketResearchAIPolicyEventMemoryDigestRow, ...]:
    if type(rows) not in (list, tuple):
        raise ValueError("rows must be a list or tuple")
    normalized = tuple(rows)
    previous_key: tuple[int, str, str] | None = None
    status_rank = {STATUS_BLOCKED: 0, STATUS_WATCH: 1, STATUS_READY: 2}
    for row in normalized:
        if type(row) is not MarketResearchAIPolicyEventMemoryDigestRow:
            raise ValueError(
                "rows must contain MarketResearchAIPolicyEventMemoryDigestRow values",
            )
        require_paper_only_flags("row", row)
        key = (
            status_rank[row.memory_status],
            row.ai_policy_event_key,
            row.market_research_key,
        )
        if previous_key is not None and key <= previous_key:
            raise ValueError("rows must be sorted by unique status and event keys")
        previous_key = key
    return normalized


def _normalize_reason_code_counts(
    values: object,
) -> tuple[MarketResearchAIPolicyEventMemoryDigestReasonCodeCount, ...]:
    if type(values) not in (list, tuple):
        raise ValueError("reason_code_counts must be a list or tuple")
    counts = tuple(values)
    previous_order = -1
    for count in counts:
        if type(count) is not MarketResearchAIPolicyEventMemoryDigestReasonCodeCount:
            raise ValueError("reason_code_counts must contain reason count rows")
        require_paper_only_flags("reason_code_counts", count)
        order = _reason_code_order(count.reason_code)
        if order <= previous_order:
            raise ValueError("reason_code_counts must be sorted by unique reason_code")
        previous_order = order
    return counts


def _normalize_row_reason_codes(values: object) -> tuple[str, ...]:
    reason_codes = _normalize_reason_codes(values)
    if not reason_codes:
        raise ValueError("reason_codes must not be empty")
    previous_order = -1
    for reason_code in reason_codes:
        order = _row_reason_code_order(reason_code)
        if order <= previous_order:
            raise ValueError("reason_codes must be sorted by unique reason code")
        previous_order = order
    return reason_codes


def _normalize_reason_codes(values: object) -> tuple[str, ...]:
    if type(values) not in (list, tuple):
        raise ValueError("reason_codes must be a list or tuple")
    normalized = tuple(values)
    for reason_code in normalized:
        _require_reason_code("reason_codes", reason_code)
    if len(normalized) != len(frozenset(normalized)):
        raise ValueError("reason_codes must be unique")
    return normalized


def _validate_digest_row(row: MarketResearchAIPolicyEventMemoryDigestRow) -> None:
    if row.regulator_source_observed_at is None:
        if row.regulator_source_age_seconds is not None:
            raise ValueError(
                "regulator_source_age_seconds must be None when source is missing",
            )
    elif row.regulator_source_count > ZERO and row.regulator_source_age_seconds is None:
        raise ValueError(
            "regulator_source_age_seconds must be present when source is present",
        )
    if row.regulator_source_count == ZERO and MISSING_REGULATOR_SOURCE_REASON not in row.reason_codes:
        raise ValueError("reason_codes must include missing regulator source")
    expected_status = _row_status(row.reason_codes)
    if row.memory_status != expected_status:
        raise ValueError("memory_status must match reason_codes")


def _validate_report(report: MarketResearchAIPolicyEventMemoryDigestReport) -> None:
    row_count = _count(len(report.rows))
    ready_count = _count(
        sum(1 for row in report.rows if row.memory_status == STATUS_READY),
    )
    watch_count = _count(
        sum(1 for row in report.rows if row.memory_status == STATUS_WATCH),
    )
    blocked_count = _count(
        sum(1 for row in report.rows if row.memory_status == STATUS_BLOCKED),
    )
    if report.ai_policy_event_count != row_count:
        raise ValueError("ai_policy_event_count must match rows")
    if report.ready_event_count != ready_count:
        raise ValueError("ready_event_count must match rows")
    if report.watch_event_count != watch_count:
        raise ValueError("watch_event_count must match rows")
    if report.blocked_event_count != blocked_count:
        raise ValueError("blocked_event_count must match rows")
    if report.reason_codes != tuple(
        count.reason_code for count in report.reason_code_counts
    ):
        raise ValueError("reason_codes must match reason_code_counts")
    expected_count_codes = _reason_code_counts(report.rows)
    if report.rows:
        if report.reason_code_counts != expected_count_codes:
            raise ValueError("reason_code_counts must match row reason_codes")
    elif report.reason_codes != (NO_INPUTS_REASON,):
        raise ValueError("reason_codes must contain no-inputs reason for empty reports")
    expected_status = _report_status(
        blocked_event_count=report.blocked_event_count,
        watch_event_count=report.watch_event_count,
        has_inputs=bool(report.rows),
    )
    if report.digest_status != expected_status:
        raise ValueError("digest_status must match row statuses")


def _reject_unsafe_payload(label: str, value: object, path: str = "") -> None:
    if is_dataclass(value) and not isinstance(value, type):
        _reject_unsafe_payload(label, asdict(value), path)
        return
    if type(value) is str:
        _reject_unsafe_text(path or label, value)
        return
    if isinstance(value, Decimal):
        if type(value) is not Decimal or not value.is_finite():
            raise ValueError(f"{path or label} must be finite Decimal")
        return
    if isinstance(value, datetime):
        _as_utc(path or label, value)
        return
    if value is None or type(value) is bool:
        return
    if type(value) is int:
        raise ValueError(f"{path or label} must use Decimal-derived string values")
    if isinstance(value, float):
        raise ValueError(f"{path or label} must not be a float")
    if isinstance(value, dict):
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            nested_path = key if not path else f"{path}.{key}"
            if key in {"paper_only", "report_only", "readonly"} and item is not True:
                raise ValueError(f"{nested_path} must be True")
            _reject_unsafe_text(nested_path, key)
            _reject_unsafe_payload(label, item, nested_path)
        return
    if isinstance(value, (list, tuple)):
        for index, item in enumerate(value):
            nested_path = f"{path}[{index}]" if path else f"{label}[{index}]"
            _reject_unsafe_payload(label, item, nested_path)
        return
    raise ValueError("value is not JSON serializable")


def _reject_unsafe_text(field_name: str, value: str) -> None:
    lowered = value.lower()
    if "://" in lowered or any(
        fragment in lowered for fragment in UNSAFE_TEXT_FRAGMENTS
    ):
        raise ValueError(f"{field_name} has unsafe value")


def _json_ready(value: Any) -> Any:
    if value is None:
        return None
    if is_dataclass(value) and not isinstance(value, type):
        return _json_ready(asdict(value))
    if isinstance(value, Decimal):
        if type(value) is not Decimal or not value.is_finite():
            raise ValueError("JSON Decimal value must be finite")
        return str(value)
    if isinstance(value, datetime):
        return _as_utc("datetime", value).isoformat()
    if isinstance(value, float):
        raise ValueError("JSON value must not be a float")
    if type(value) is int:
        raise ValueError("JSON numeric value must use Decimal")
    if type(value) in (str, bool):
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


def _require_memory_status(field_name: str, value: object) -> str:
    if type(value) is not str or value not in MEMORY_STATUSES:
        raise ValueError(f"{field_name} must be one of {MEMORY_STATUSES}")
    return value


def _require_canonical_string(field_name: str, value: object) -> str:
    if type(value) is not str or not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a non-empty canonical string")
    return value


def _require_public_string(field_name: str, value: object) -> str:
    text = _require_canonical_string(field_name, value)
    lowered = text.lower()
    if any(fragment in lowered for fragment in UNSAFE_TEXT_FRAGMENTS):
        raise ValueError(f"{field_name} must not include sensitive or live-action text")
    return text


def _require_reference(field_name: str, value: object) -> str:
    text = _require_canonical_string(field_name, value)
    if _is_sensitive_reference(text):
        return text
    _require_public_string(field_name, text)
    return text


def _require_redacted_reference(field_name: str, value: object) -> str:
    text = _require_canonical_string(field_name, value)
    if _is_sensitive_reference(text):
        raise ValueError(f"{field_name} must be redacted")
    return text


def _require_reason_code(field_name: str, value: object) -> str:
    if type(value) is not str or value not in REASON_CODE_SEQUENCE:
        raise ValueError(f"{field_name} must be a known reason code")
    return value


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal or not value.is_finite():
        raise ValueError(f"{field_name} must be a finite Decimal")
    return _quantize_decimal(value)


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


def _require_optional_nonnegative_decimal(
    field_name: str,
    value: object,
) -> Decimal | None:
    if value is None:
        return None
    return _require_nonnegative_decimal(field_name, value)


def _require_nonnegative_count_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_nonnegative_decimal(field_name, value)
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{field_name} must be an integer Decimal count")
    return normalized


def _require_positive_count_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_nonnegative_count_decimal(field_name, value)
    if normalized <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _require_ratio_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < ZERO or normalized > ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return normalized


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _as_optional_utc(field_name: str, value: object) -> datetime | None:
    if value is None:
        return None
    return _as_utc(field_name, value)


def _seconds_between(start: datetime, end: datetime) -> Decimal:
    delta = end - start
    total_microseconds = (
        Decimal(delta.days) * Decimal("86400000000")
        + Decimal(delta.seconds) * Decimal("1000000")
        + Decimal(delta.microseconds)
    )
    return _quantize_decimal(total_microseconds / MICROSECONDS_PER_SECOND)


def _count(value: int) -> Decimal:
    return _quantize_decimal(Decimal(value))


def _sum_decimal(values: object) -> Decimal:
    total = ZERO
    for value in values:  # type: ignore[assignment]
        total += value
    return _quantize_decimal(total)


def _average(values: object) -> Decimal:
    items = tuple(values)  # type: ignore[arg-type]
    if not items:
        return ZERO
    return _ratio(_sum_decimal(items), _count(len(items)))


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO:
        return ZERO
    return _quantize(numerator / denominator)


def _quantize(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        normalized = value.quantize(QUANT)
    if normalized < ZERO:
        return ZERO
    if normalized > ONE:
        return ONE
    return normalized


def _quantize_decimal(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(QUANT)


def _redacted_reference(reference: str) -> str:
    if not _is_sensitive_reference(reference):
        return reference
    digest = sha256(reference.encode("utf-8")).hexdigest()[:12]
    return f"sha256:{digest}"


def _is_sensitive_reference(reference: str) -> bool:
    lowered = reference.lower()
    return any(fragment in lowered for fragment in UNSAFE_TEXT_FRAGMENTS) or "://" in lowered


def _reason_code_order(reason_code: str) -> int:
    try:
        return REASON_CODE_SEQUENCE.index(reason_code)
    except ValueError as exc:
        raise ValueError("reason_code must be a known reason code") from exc


def _row_reason_code_order(reason_code: str) -> int:
    try:
        return ROW_REASON_CODE_SEQUENCE.index(reason_code)
    except ValueError as exc:
        raise ValueError("reason_codes must contain row reason codes") from exc
