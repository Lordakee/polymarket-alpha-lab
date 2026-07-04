"""Pure Phase 1 market research AI event memory reducer."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from hashlib import sha256


DEFAULT_MARKET_RESEARCH_AI_EVENT_MEMORY_DIGEST_CONFIG_VERSION = (
    "market-research-ai-event-memory-digest-v0"
)

STATUS_READY = "ready"
STATUS_WATCH = "watch"
STATUS_BLOCKED = "blocked"

NO_INPUTS_REASON = "market_research_ai_event_memory_digest_no_inputs"
READY_REASON = "market_research_ai_event_memory_digest_ready"
CONFIDENCE_GAP_REASON = "market_research_ai_event_memory_digest_confidence_gap"
MISSING_ANALOGS_REASON = (
    "market_research_ai_event_memory_digest_missing_event_analogs"
)
MISSING_SOURCES_REASON = "market_research_ai_event_memory_digest_missing_sources"
MODEL_CATALYST_REASON = "market_research_ai_event_memory_digest_model_launch_catalyst"
MODEL_CATALYST_GAP_REASON = (
    "market_research_ai_event_memory_digest_model_launch_catalyst_gap"
)
POLICY_CATALYST_REASON = (
    "market_research_ai_event_memory_digest_product_policy_catalyst"
)
STALE_SOURCES_REASON = "market_research_ai_event_memory_digest_stale_sources"
THIN_ANALOGS_REASON = "market_research_ai_event_memory_digest_thin_event_analogs"
THIN_SOURCES_REASON = "market_research_ai_event_memory_digest_thin_sources"

REASON_CODE_SEQUENCE = (
    CONFIDENCE_GAP_REASON,
    MISSING_ANALOGS_REASON,
    MISSING_SOURCES_REASON,
    MODEL_CATALYST_REASON,
    MODEL_CATALYST_GAP_REASON,
    NO_INPUTS_REASON,
    POLICY_CATALYST_REASON,
    READY_REASON,
    STALE_SOURCES_REASON,
    THIN_ANALOGS_REASON,
    THIN_SOURCES_REASON,
)
ROW_REASON_CODE_SEQUENCE = (
    CONFIDENCE_GAP_REASON,
    MISSING_ANALOGS_REASON,
    MISSING_SOURCES_REASON,
    MODEL_CATALYST_REASON,
    MODEL_CATALYST_GAP_REASON,
    POLICY_CATALYST_REASON,
    READY_REASON,
    STALE_SOURCES_REASON,
    THIN_ANALOGS_REASON,
    THIN_SOURCES_REASON,
)

DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
QUANT = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")

_STATUS_NEXT_STEPS = {
    STATUS_READY: "allow_report_only_market_research_ai_event_memory_digest",
    STATUS_WATCH: "watch_report_only_market_research_ai_event_memory_digest",
    STATUS_BLOCKED: "block_report_only_market_research_ai_event_memory_digest",
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
    "DEFAULT_MARKET_RESEARCH_AI_EVENT_MEMORY_DIGEST_CONFIG_VERSION",
    "MarketResearchAIEventMemoryDigestConfig",
    "MarketResearchAIEventMemoryDigestInputRow",
    "MarketResearchAIEventMemoryDigestReasonCodeCount",
    "MarketResearchAIEventMemoryDigestReport",
    "MarketResearchAIEventMemoryDigestRow",
    "build_market_research_ai_event_memory_digest",
)


@dataclass(frozen=True)
class MarketResearchAIEventMemoryDigestConfig:
    config_version: str = DEFAULT_MARKET_RESEARCH_AI_EVENT_MEMORY_DIGEST_CONFIG_VERSION
    fresh_source_max_age_seconds: Decimal = Decimal("21600.000000")
    min_source_count: Decimal = Decimal("2.000000")
    min_event_analog_count: Decimal = Decimal("2.000000")
    min_model_launch_catalyst_score: Decimal = Decimal("0.650000")
    min_product_policy_catalyst_score: Decimal = Decimal("0.600000")
    confidence_gap_threshold: Decimal = Decimal("0.250000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketResearchAIEventMemoryDigestConfig:
            raise TypeError(
                "MarketResearchAIEventMemoryDigestConfig does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not MarketResearchAIEventMemoryDigestConfig:
            raise ValueError(
                "config must be exactly MarketResearchAIEventMemoryDigestConfig",
            )
        _require_public_string("config_version", self.config_version)
        object.__setattr__(
            self,
            "fresh_source_max_age_seconds",
            _require_positive_decimal(
                "fresh_source_max_age_seconds",
                self.fresh_source_max_age_seconds,
            ),
        )
        for field_name in ("min_source_count", "min_event_analog_count"):
            object.__setattr__(
                self,
                field_name,
                _require_positive_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "min_model_launch_catalyst_score",
            "min_product_policy_catalyst_score",
            "confidence_gap_threshold",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class MarketResearchAIEventMemoryDigestInputRow:
    market_research_key: str
    ai_event_key: str
    ai_event_family: str
    ai_event_reference: str
    event_observed_at: datetime
    latest_source_observed_at: datetime | None
    latest_analog_observed_at: datetime | None
    source_count: Decimal
    stale_source_count: Decimal
    model_launch_catalyst_score: Decimal
    product_policy_catalyst_score: Decimal
    event_analog_count: Decimal
    confidence_score: Decimal
    confidence_gap_score: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketResearchAIEventMemoryDigestInputRow:
            raise TypeError(
                "MarketResearchAIEventMemoryDigestInputRow does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not MarketResearchAIEventMemoryDigestInputRow:
            raise ValueError(
                "input row must be exactly MarketResearchAIEventMemoryDigestInputRow",
            )
        _require_public_string("market_research_key", self.market_research_key)
        _require_public_string("ai_event_key", self.ai_event_key)
        _require_public_string("ai_event_family", self.ai_event_family)
        _require_reference("ai_event_reference", self.ai_event_reference)
        object.__setattr__(
            self,
            "event_observed_at",
            _as_utc("event_observed_at", self.event_observed_at),
        )
        object.__setattr__(
            self,
            "latest_source_observed_at",
            _as_optional_utc(
                "latest_source_observed_at",
                self.latest_source_observed_at,
            ),
        )
        object.__setattr__(
            self,
            "latest_analog_observed_at",
            _as_optional_utc(
                "latest_analog_observed_at",
                self.latest_analog_observed_at,
            ),
        )
        for field_name in ("source_count", "stale_source_count", "event_analog_count"):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        if self.stale_source_count > self.source_count:
            raise ValueError("stale_source_count must not exceed source_count")
        for field_name in (
            "model_launch_catalyst_score",
            "product_policy_catalyst_score",
            "confidence_score",
            "confidence_gap_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        _require_hard_flags("input row", self)


@dataclass(frozen=True)
class MarketResearchAIEventMemoryDigestRow:
    market_research_key: str
    ai_event_key: str
    ai_event_family: str
    memory_status: str
    event_observed_at: datetime
    latest_source_observed_at: datetime | None
    latest_analog_observed_at: datetime | None
    event_age_seconds: Decimal
    source_age_seconds: Decimal | None
    analog_age_seconds: Decimal | None
    source_count: Decimal
    stale_source_count: Decimal
    model_launch_catalyst_score: Decimal
    product_policy_catalyst_score: Decimal
    event_analog_count: Decimal
    confidence_score: Decimal
    confidence_gap_score: Decimal
    redacted_ai_event_reference: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketResearchAIEventMemoryDigestRow:
            raise TypeError(
                "MarketResearchAIEventMemoryDigestRow does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not MarketResearchAIEventMemoryDigestRow:
            raise ValueError("row must be exactly MarketResearchAIEventMemoryDigestRow")
        _require_public_string("market_research_key", self.market_research_key)
        _require_public_string("ai_event_key", self.ai_event_key)
        _require_public_string("ai_event_family", self.ai_event_family)
        if self.memory_status not in _STATUS_NEXT_STEPS:
            raise ValueError("memory_status must be ready, watch, or blocked")
        object.__setattr__(
            self,
            "event_observed_at",
            _as_utc("event_observed_at", self.event_observed_at),
        )
        object.__setattr__(
            self,
            "latest_source_observed_at",
            _as_optional_utc(
                "latest_source_observed_at",
                self.latest_source_observed_at,
            ),
        )
        object.__setattr__(
            self,
            "latest_analog_observed_at",
            _as_optional_utc(
                "latest_analog_observed_at",
                self.latest_analog_observed_at,
            ),
        )
        _require_nonnegative_decimal("event_age_seconds", self.event_age_seconds)
        if self.source_age_seconds is not None:
            _require_nonnegative_decimal("source_age_seconds", self.source_age_seconds)
        if self.analog_age_seconds is not None:
            _require_nonnegative_decimal("analog_age_seconds", self.analog_age_seconds)
        for field_name in ("source_count", "stale_source_count", "event_analog_count"):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        if self.stale_source_count > self.source_count:
            raise ValueError("stale_source_count must not exceed source_count")
        for field_name in (
            "model_launch_catalyst_score",
            "product_policy_catalyst_score",
            "confidence_score",
            "confidence_gap_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        _require_redacted_reference(
            "redacted_ai_event_reference",
            self.redacted_ai_event_reference,
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        if self.memory_status != _memory_status_from_reason_codes(self.reason_codes):
            raise ValueError("memory_status must match reason_codes")
        _require_hard_flags("row", self)


@dataclass(frozen=True)
class MarketResearchAIEventMemoryDigestReasonCodeCount:
    reason_code: str
    count: Decimal
    event_ratio: Decimal

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketResearchAIEventMemoryDigestReasonCodeCount:
            raise TypeError(
                "MarketResearchAIEventMemoryDigestReasonCodeCount does not support "
                "subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not MarketResearchAIEventMemoryDigestReasonCodeCount:
            raise ValueError(
                "reason code count must be exactly "
                "MarketResearchAIEventMemoryDigestReasonCodeCount",
            )
        _require_reason_code("reason_code", self.reason_code)
        object.__setattr__(
            self,
            "count",
            _require_nonnegative_decimal("count", self.count),
        )
        object.__setattr__(
            self,
            "event_ratio",
            _require_ratio_decimal("event_ratio", self.event_ratio),
        )


@dataclass(frozen=True)
class MarketResearchAIEventMemoryDigestReport:
    generated_at: datetime
    config_version: str
    digest_status: str
    recommended_next_step: str
    ai_event_count: Decimal
    ready_event_count: Decimal
    watch_event_count: Decimal
    blocked_event_count: Decimal
    model_launch_catalyst_count: Decimal
    product_policy_catalyst_count: Decimal
    stale_source_event_count: Decimal
    missing_source_event_count: Decimal
    thin_source_event_count: Decimal
    missing_analog_event_count: Decimal
    thin_analog_event_count: Decimal
    confidence_gap_event_count: Decimal
    source_count: Decimal
    stale_source_count: Decimal
    event_analog_count: Decimal
    source_freshness_ratio: Decimal
    event_analog_coverage_ratio: Decimal
    average_confidence_score: Decimal
    average_confidence_gap_score: Decimal
    max_source_age_seconds: Decimal
    rows: tuple[MarketResearchAIEventMemoryDigestRow, ...]
    reason_code_counts: tuple[MarketResearchAIEventMemoryDigestReasonCodeCount, ...]
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketResearchAIEventMemoryDigestReport:
            raise TypeError(
                "MarketResearchAIEventMemoryDigestReport does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not MarketResearchAIEventMemoryDigestReport:
            raise ValueError(
                "report must be exactly MarketResearchAIEventMemoryDigestReport",
            )
        object.__setattr__(
            self,
            "generated_at",
            _as_utc("generated_at", self.generated_at),
        )
        _require_public_string("config_version", self.config_version)
        if self.digest_status not in _STATUS_NEXT_STEPS:
            raise ValueError("digest_status must be ready, watch, or blocked")
        if self.recommended_next_step != _STATUS_NEXT_STEPS[self.digest_status]:
            raise ValueError("recommended_next_step must match digest_status")
        for field_name in (
            "ai_event_count",
            "ready_event_count",
            "watch_event_count",
            "blocked_event_count",
            "model_launch_catalyst_count",
            "product_policy_catalyst_count",
            "stale_source_event_count",
            "missing_source_event_count",
            "thin_source_event_count",
            "missing_analog_event_count",
            "thin_analog_event_count",
            "confidence_gap_event_count",
            "source_count",
            "stale_source_count",
            "event_analog_count",
            "max_source_age_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "source_freshness_ratio",
            "event_analog_coverage_ratio",
            "average_confidence_score",
            "average_confidence_gap_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        _require_row_tuple("rows", self.rows)
        _require_reason_count_tuple("reason_code_counts", self.reason_code_counts)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        if self.reason_codes != tuple(
            item.reason_code for item in self.reason_code_counts
        ):
            raise ValueError("reason_codes must match reason_code_counts")
        _require_hard_flags("report", self)


def build_market_research_ai_event_memory_digest(
    rows: tuple[MarketResearchAIEventMemoryDigestInputRow, ...],
    *,
    config: MarketResearchAIEventMemoryDigestConfig
    | None = None,
    generated_at: datetime,
) -> MarketResearchAIEventMemoryDigestReport:
    cfg = config or MarketResearchAIEventMemoryDigestConfig()
    if type(cfg) is not MarketResearchAIEventMemoryDigestConfig:
        raise TypeError(
            "config must be exactly MarketResearchAIEventMemoryDigestConfig",
        )
    observed_at = _as_utc("generated_at", generated_at)
    input_rows = _require_input_row_tuple("rows", rows)

    if not input_rows:
        reason_counts = (
            MarketResearchAIEventMemoryDigestReasonCodeCount(
                reason_code=NO_INPUTS_REASON,
                count=ONE,
                event_ratio=ZERO,
            ),
        )
        return MarketResearchAIEventMemoryDigestReport(
            generated_at=observed_at,
            config_version=cfg.config_version,
            digest_status=STATUS_BLOCKED,
            recommended_next_step=_STATUS_NEXT_STEPS[STATUS_BLOCKED],
            ai_event_count=ZERO,
            ready_event_count=ZERO,
            watch_event_count=ZERO,
            blocked_event_count=ZERO,
            model_launch_catalyst_count=ZERO,
            product_policy_catalyst_count=ZERO,
            stale_source_event_count=ZERO,
            missing_source_event_count=ZERO,
            thin_source_event_count=ZERO,
            missing_analog_event_count=ZERO,
            thin_analog_event_count=ZERO,
            confidence_gap_event_count=ZERO,
            source_count=ZERO,
            stale_source_count=ZERO,
            event_analog_count=ZERO,
            source_freshness_ratio=ZERO,
            event_analog_coverage_ratio=ZERO,
            average_confidence_score=ZERO,
            average_confidence_gap_score=ZERO,
            max_source_age_seconds=ZERO,
            rows=(),
            reason_code_counts=reason_counts,
            reason_codes=(NO_INPUTS_REASON,),
        )

    report_rows = tuple(
        _build_report_row(row, config=cfg, generated_at=observed_at)
        for row in input_rows
    )
    sorted_rows = tuple(
        sorted(
            report_rows,
            key=lambda row: (
                _status_rank(row.memory_status),
                row.ai_event_key,
                row.market_research_key,
            ),
        ),
    )
    reason_counts = _reason_code_counts(sorted_rows)
    reason_codes = tuple(item.reason_code for item in reason_counts)
    ai_event_count = _count_decimal(sorted_rows)
    ready_count = _sum_if(sorted_rows, lambda row: row.memory_status == STATUS_READY)
    watch_count = _sum_if(sorted_rows, lambda row: row.memory_status == STATUS_WATCH)
    blocked_count = _sum_if(sorted_rows, lambda row: row.memory_status == STATUS_BLOCKED)
    source_count = _sum_decimal(row.source_count for row in sorted_rows)
    stale_source_count = _sum_decimal(row.stale_source_count for row in sorted_rows)
    fresh_source_count = source_count - stale_source_count
    event_analog_count = _sum_decimal(row.event_analog_count for row in sorted_rows)
    source_age_values = tuple(
        row.source_age_seconds
        for row in sorted_rows
        if row.source_age_seconds is not None
    )
    max_source_age = max(source_age_values) if source_age_values else ZERO
    digest_status = _digest_status(sorted_rows)

    return MarketResearchAIEventMemoryDigestReport(
        generated_at=observed_at,
        config_version=cfg.config_version,
        digest_status=digest_status,
        recommended_next_step=_STATUS_NEXT_STEPS[digest_status],
        ai_event_count=ai_event_count,
        ready_event_count=ready_count,
        watch_event_count=watch_count,
        blocked_event_count=blocked_count,
        model_launch_catalyst_count=_sum_if(
            sorted_rows,
            lambda row: MODEL_CATALYST_REASON in row.reason_codes,
        ),
        product_policy_catalyst_count=_sum_if(
            sorted_rows,
            lambda row: POLICY_CATALYST_REASON in row.reason_codes,
        ),
        stale_source_event_count=_sum_if(
            sorted_rows,
            lambda row: STALE_SOURCES_REASON in row.reason_codes,
        ),
        missing_source_event_count=_sum_if(
            sorted_rows,
            lambda row: MISSING_SOURCES_REASON in row.reason_codes,
        ),
        thin_source_event_count=_sum_if(
            sorted_rows,
            lambda row: THIN_SOURCES_REASON in row.reason_codes,
        ),
        missing_analog_event_count=_sum_if(
            sorted_rows,
            lambda row: MISSING_ANALOGS_REASON in row.reason_codes,
        ),
        thin_analog_event_count=_sum_if(
            sorted_rows,
            lambda row: THIN_ANALOGS_REASON in row.reason_codes,
        ),
        confidence_gap_event_count=_sum_if(
            sorted_rows,
            lambda row: CONFIDENCE_GAP_REASON in row.reason_codes,
        ),
        source_count=source_count,
        stale_source_count=stale_source_count,
        event_analog_count=event_analog_count,
        source_freshness_ratio=_ratio(fresh_source_count, source_count),
        event_analog_coverage_ratio=_ratio(
            _sum_if(
                sorted_rows,
                lambda row: row.event_analog_count > ZERO,
            ),
            ai_event_count,
        ),
        average_confidence_score=_average(
            row.confidence_score for row in sorted_rows
        ),
        average_confidence_gap_score=_average(
            row.confidence_gap_score for row in sorted_rows
        ),
        max_source_age_seconds=max_source_age,
        rows=sorted_rows,
        reason_code_counts=reason_counts,
        reason_codes=reason_codes,
    )


def _build_report_row(
    row: MarketResearchAIEventMemoryDigestInputRow,
    *,
    config: MarketResearchAIEventMemoryDigestConfig,
    generated_at: datetime,
) -> MarketResearchAIEventMemoryDigestRow:
    event_age_seconds = _age_seconds(generated_at, row.event_observed_at)
    source_age_seconds = (
        None
        if row.latest_source_observed_at is None or row.source_count == ZERO
        else _age_seconds(generated_at, row.latest_source_observed_at)
    )
    analog_age_seconds = (
        None
        if row.latest_analog_observed_at is None or row.event_analog_count == ZERO
        else _age_seconds(generated_at, row.latest_analog_observed_at)
    )

    reasons: list[str] = []
    if row.confidence_gap_score >= config.confidence_gap_threshold:
        reasons.append(CONFIDENCE_GAP_REASON)
    if row.event_analog_count == ZERO:
        reasons.append(MISSING_ANALOGS_REASON)
    if row.latest_source_observed_at is None or row.source_count == ZERO:
        reasons.append(MISSING_SOURCES_REASON)
    if row.model_launch_catalyst_score >= config.min_model_launch_catalyst_score:
        reasons.append(MODEL_CATALYST_REASON)
    elif row.ai_event_family == "model_launch":
        reasons.append(MODEL_CATALYST_GAP_REASON)
    if row.product_policy_catalyst_score >= config.min_product_policy_catalyst_score:
        reasons.append(POLICY_CATALYST_REASON)
    if (
        source_age_seconds is not None
        and source_age_seconds > config.fresh_source_max_age_seconds
    ) or row.stale_source_count > ZERO:
        reasons.append(STALE_SOURCES_REASON)
    if row.event_analog_count < config.min_event_analog_count:
        reasons.append(THIN_ANALOGS_REASON)
    if row.source_count < config.min_source_count:
        reasons.append(THIN_SOURCES_REASON)
    if not reasons or reasons == [MODEL_CATALYST_REASON]:
        reasons.append(READY_REASON)

    reason_codes = _normalize_reason_codes("reason_codes", tuple(reasons))
    return MarketResearchAIEventMemoryDigestRow(
        market_research_key=row.market_research_key,
        ai_event_key=row.ai_event_key,
        ai_event_family=row.ai_event_family,
        memory_status=_memory_status_from_reason_codes(reason_codes),
        event_observed_at=row.event_observed_at,
        latest_source_observed_at=row.latest_source_observed_at,
        latest_analog_observed_at=row.latest_analog_observed_at,
        event_age_seconds=event_age_seconds,
        source_age_seconds=source_age_seconds,
        analog_age_seconds=analog_age_seconds,
        source_count=row.source_count,
        stale_source_count=row.stale_source_count,
        model_launch_catalyst_score=row.model_launch_catalyst_score,
        product_policy_catalyst_score=row.product_policy_catalyst_score,
        event_analog_count=row.event_analog_count,
        confidence_score=row.confidence_score,
        confidence_gap_score=row.confidence_gap_score,
        redacted_ai_event_reference=_redact_reference(row.ai_event_reference),
        reason_codes=reason_codes,
    )


def _digest_status(rows: tuple[MarketResearchAIEventMemoryDigestRow, ...]) -> str:
    if any(row.memory_status == STATUS_BLOCKED for row in rows):
        return STATUS_BLOCKED
    if any(row.memory_status == STATUS_WATCH for row in rows):
        return STATUS_WATCH
    return STATUS_READY


def _memory_status_from_reason_codes(reason_codes: tuple[str, ...]) -> str:
    if MISSING_SOURCES_REASON in reason_codes or MISSING_ANALOGS_REASON in reason_codes:
        return STATUS_BLOCKED
    if reason_codes == (READY_REASON,) or reason_codes == (
        MODEL_CATALYST_REASON,
        READY_REASON,
    ):
        return STATUS_READY
    return STATUS_WATCH


def _reason_code_counts(
    rows: tuple[MarketResearchAIEventMemoryDigestRow, ...],
) -> tuple[MarketResearchAIEventMemoryDigestReasonCodeCount, ...]:
    row_count = _count_decimal(rows)
    counts: dict[str, Decimal] = {}
    for row in rows:
        for reason_code in row.reason_codes:
            counts[reason_code] = counts.get(reason_code, ZERO) + ONE
    return tuple(
        MarketResearchAIEventMemoryDigestReasonCodeCount(
            reason_code=reason_code,
            count=count,
            event_ratio=_ratio(count, row_count),
        )
        for reason_code, count in sorted(
            counts.items(),
            key=lambda item: REASON_CODE_SEQUENCE.index(item[0]),
        )
    )


def _status_rank(status: str) -> int:
    return {STATUS_BLOCKED: 0, STATUS_WATCH: 1, STATUS_READY: 2}[status]


def _require_input_row_tuple(
    field_name: str,
    value: tuple[MarketResearchAIEventMemoryDigestInputRow, ...],
) -> tuple[MarketResearchAIEventMemoryDigestInputRow, ...]:
    if not isinstance(value, tuple):
        raise TypeError(f"{field_name} must be a tuple")
    for row in value:
        if type(row) is not MarketResearchAIEventMemoryDigestInputRow:
            raise ValueError(
                f"{field_name} must contain MarketResearchAIEventMemoryDigestInputRow",
            )
    return value


def _require_row_tuple(
    field_name: str,
    value: tuple[MarketResearchAIEventMemoryDigestRow, ...],
) -> None:
    if not isinstance(value, tuple):
        raise TypeError(f"{field_name} must be a tuple")
    for row in value:
        if type(row) is not MarketResearchAIEventMemoryDigestRow:
            raise ValueError(
                f"{field_name} must contain MarketResearchAIEventMemoryDigestRow",
            )


def _require_reason_count_tuple(
    field_name: str,
    value: tuple[MarketResearchAIEventMemoryDigestReasonCodeCount, ...],
) -> None:
    if not isinstance(value, tuple):
        raise TypeError(f"{field_name} must be a tuple")
    for item in value:
        if type(item) is not MarketResearchAIEventMemoryDigestReasonCodeCount:
            raise ValueError(
                f"{field_name} must contain "
                "MarketResearchAIEventMemoryDigestReasonCodeCount",
            )


def _require_public_string(field_name: str, value: str) -> str:
    if type(value) is not str:
        raise TypeError(f"{field_name} must be exactly str")
    if not value or value != value.strip() or any(char.isspace() for char in value):
        raise ValueError(f"{field_name} must be canonical")
    return value


def _require_reference(field_name: str, value: str) -> str:
    _require_public_string(field_name, value)
    if _is_redactable_reference(value):
        return value
    lowered = value.lower()
    if any(fragment in lowered for fragment in UNSAFE_TEXT_FRAGMENTS):
        raise ValueError(f"{field_name} contains unsafe text")
    return value


def _require_redacted_reference(field_name: str, value: str) -> str:
    _require_public_string(field_name, value)
    if value.startswith("sha256:") and len(value) == 19:
        return value
    _require_reference(field_name, value)
    return value


def _require_reason_code(field_name: str, value: str) -> str:
    _require_public_string(field_name, value)
    if value not in REASON_CODE_SEQUENCE:
        raise ValueError(f"{field_name} must be a known reason_code")
    return value


def _normalize_reason_codes(field_name: str, value: tuple[str, ...]) -> tuple[str, ...]:
    if not isinstance(value, tuple):
        raise TypeError(f"{field_name} must be a tuple")
    if not value:
        raise ValueError(f"{field_name} must not be empty")
    unique_values = frozenset(value)
    if len(unique_values) != len(value):
        raise ValueError(f"{field_name} contains duplicate reason_code values")
    for reason_code in value:
        if reason_code not in REASON_CODE_SEQUENCE:
            raise ValueError(f"{field_name} contains unknown reason_code")
    reason_sequence = (
        REASON_CODE_SEQUENCE if NO_INPUTS_REASON in value else ROW_REASON_CODE_SEQUENCE
    )
    return tuple(
        reason_code
        for reason_code in reason_sequence
        if reason_code in unique_values
    )


def _require_hard_flags(field_name: str, value: object) -> None:
    for flag_name in ("paper_only", "report_only", "readonly"):
        if getattr(value, flag_name) is not True:
            raise ValueError(f"{field_name} must keep {flag_name}=True")


def _as_optional_utc(field_name: str, value: datetime | None) -> datetime | None:
    if value is None:
        return None
    return _as_utc(field_name, value)


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
    return value.quantize(QUANT)


def _require_nonnegative_decimal(field_name: str, value: Decimal) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return decimal_value


def _require_positive_decimal(field_name: str, value: Decimal) -> Decimal:
    decimal_value = _require_nonnegative_decimal(field_name, value)
    if decimal_value <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return decimal_value


def _require_ratio_decimal(field_name: str, value: Decimal) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value < ZERO or decimal_value > ONE:
        raise ValueError(f"{field_name} must be in the unit interval")
    return decimal_value


def _redact_reference(value: str) -> str:
    lowered = value.lower()
    if any(fragment in lowered for fragment in UNSAFE_TEXT_FRAGMENTS):
        return f"sha256:{sha256(value.encode()).hexdigest()[:12]}"
    return value


def _is_redactable_reference(value: str) -> bool:
    return "://" in value or "?" in value


def _age_seconds(generated_at: datetime, observed_at: datetime) -> Decimal:
    delta = generated_at - observed_at
    value = Decimal(delta.days * 86400 + delta.seconds)
    if value < ZERO:
        raise ValueError("observed_at must be before or equal to generated_at")
    return _quantize(value)


def _count_decimal(values: tuple[object, ...]) -> Decimal:
    return _quantize(Decimal(len(values)))


def _sum_decimal(values: object) -> Decimal:
    total = ZERO
    for value in values:
        total += value
    return _quantize(total)


def _sum_if(
    rows: tuple[MarketResearchAIEventMemoryDigestRow, ...],
    predicate: object,
) -> Decimal:
    return _quantize(
        sum(
            (ONE for row in rows if predicate(row)),
            ZERO,
        ),
    )


def _average(values: object) -> Decimal:
    collected = tuple(values)
    if not collected:
        return ZERO
    return _ratio(_sum_decimal(collected), Decimal(len(collected)))


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return _quantize(numerator / denominator)


def _quantize(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(QUANT)
