"""Pure Phase 1 AI safety policy digest reducer."""

from __future__ import annotations

from dataclasses import InitVar, asdict, dataclass, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
from typing import Any


DEFAULT_MARKET_RESEARCH_AI_SAFETY_POLICY_DIGEST_CONFIG_VERSION = (
    "market-research-ai-safety-policy-digest-v0"
)

STATUS_READY = "ready"
STATUS_WATCH = "watch"
STATUS_BLOCKED = "blocked"

REASON_PREFIX = "market_research_ai_safety_policy_digest_"
NO_INPUTS_REASON = f"{REASON_PREFIX}no_inputs"
READY_REASON = f"{REASON_PREFIX}ready"
LOW_AGREEMENT_REASON = f"{REASON_PREFIX}low_agreement"
MATERIAL_WATCH_REASON = f"{REASON_PREFIX}material_watch"
MATERIAL_BLOCK_REASON = f"{REASON_PREFIX}material_block"
MISSING_REVIEW_REASON = f"{REASON_PREFIX}missing_review"
PROBABILITY_SHIFT_REASON = f"{REASON_PREFIX}probability_shift"
SLOW_REVIEW_REASON = f"{REASON_PREFIX}slow_review"
STALE_POLICY_REASON = f"{REASON_PREFIX}stale_policy"
THIN_SOURCES_REASON = f"{REASON_PREFIX}thin_sources"

REASON_CODE_SEQUENCE = (
    NO_INPUTS_REASON,
    MATERIAL_BLOCK_REASON,
    MISSING_REVIEW_REASON,
    PROBABILITY_SHIFT_REASON,
    LOW_AGREEMENT_REASON,
    MATERIAL_WATCH_REASON,
    SLOW_REVIEW_REASON,
    STALE_POLICY_REASON,
    THIN_SOURCES_REASON,
    READY_REASON,
)
ROW_REASON_CODE_SEQUENCE = (
    LOW_AGREEMENT_REASON,
    MATERIAL_BLOCK_REASON,
    MATERIAL_WATCH_REASON,
    MISSING_REVIEW_REASON,
    PROBABILITY_SHIFT_REASON,
    READY_REASON,
    SLOW_REVIEW_REASON,
    STALE_POLICY_REASON,
    THIN_SOURCES_REASON,
)

NEXT_STEPS = {
    STATUS_READY: "allow_report_only_market_research_ai_safety_policy_digest",
    STATUS_WATCH: "watch_report_only_market_research_ai_safety_policy_digest",
    STATUS_BLOCKED: "block_report_only_market_research_ai_safety_policy_digest",
}

DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
QUANT = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
MICROSECONDS_PER_SECOND = Decimal("1000000")
PROBABILITY_SHIFT_THRESHOLD = Decimal("0.100000")

_PUBLIC_REFERENCE_FRAGMENTS = ("public", "memo", "bulletin", "notice", "release")


@dataclass(frozen=True)
class MarketResearchAiSafetyPolicyDigestConfig:
    config_version: str = DEFAULT_MARKET_RESEARCH_AI_SAFETY_POLICY_DIGEST_CONFIG_VERSION
    fresh_policy_max_age_seconds: Decimal = Decimal("86400.000000")
    min_public_source_count: Decimal = Decimal("2")
    min_cross_source_agreement: Decimal = Decimal("0.600000")
    materiality_watch_threshold: Decimal = Decimal("0.150000")
    materiality_block_threshold: Decimal = Decimal("0.350000")
    max_review_lag_seconds: Decimal = Decimal("7200.000000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketResearchAiSafetyPolicyDigestConfig:
            raise TypeError(
                "MarketResearchAiSafetyPolicyDigestConfig does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not MarketResearchAiSafetyPolicyDigestConfig:
            raise ValueError(
                "config must be exactly MarketResearchAiSafetyPolicyDigestConfig",
            )
        _require_public_string("config_version", self.config_version)
        object.__setattr__(
            self,
            "fresh_policy_max_age_seconds",
            _require_nonnegative_decimal(
                "fresh_policy_max_age_seconds",
                self.fresh_policy_max_age_seconds,
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
            "min_cross_source_agreement",
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
            "max_review_lag_seconds",
            _require_nonnegative_decimal(
                "max_review_lag_seconds",
                self.max_review_lag_seconds,
            ),
        )
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class MarketResearchAiSafetyPolicyDigestInputRow:
    research_key: str
    condition_id: str
    policy_area: str
    public_policy_reference: str
    policy_observed_at: datetime
    reviewed_at: datetime | None
    public_source_count: Decimal
    cross_source_agreement: Decimal
    impact_materiality_score: Decimal
    market_probability_before: Decimal
    market_probability_after: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketResearchAiSafetyPolicyDigestInputRow:
            raise TypeError(
                "MarketResearchAiSafetyPolicyDigestInputRow does not support "
                "subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not MarketResearchAiSafetyPolicyDigestInputRow:
            raise ValueError(
                "input row must be exactly MarketResearchAiSafetyPolicyDigestInputRow",
            )
        for field_name in ("research_key", "condition_id", "policy_area"):
            _require_public_string(field_name, getattr(self, field_name))
        _require_reference("public_policy_reference", self.public_policy_reference)
        object.__setattr__(
            self,
            "policy_observed_at",
            _as_utc("policy_observed_at", self.policy_observed_at),
        )
        object.__setattr__(
            self,
            "reviewed_at",
            _optional_utc("reviewed_at", self.reviewed_at),
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
            "cross_source_agreement",
            "impact_materiality_score",
            "market_probability_before",
            "market_probability_after",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        if self.reviewed_at is not None and self.reviewed_at < self.policy_observed_at:
            raise ValueError("reviewed_at must be on or after policy_observed_at")
        _require_hard_flags("input row", self)


@dataclass(frozen=True)
class MarketResearchAiSafetyPolicyDigestRow:
    research_key: str
    condition_id: str
    policy_area: str
    policy_observed_at: datetime
    reviewed_at: datetime | None
    policy_age_seconds: Decimal
    review_lag_seconds: Decimal | None
    public_source_count: Decimal
    cross_source_agreement: Decimal
    impact_materiality_score: Decimal
    market_probability_before: Decimal
    market_probability_after: Decimal
    probability_change: Decimal
    policy_status: str
    redacted_policy_reference: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True
    validation_config: InitVar[MarketResearchAiSafetyPolicyDigestConfig | None] = None

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketResearchAiSafetyPolicyDigestRow:
            raise TypeError(
                "MarketResearchAiSafetyPolicyDigestRow does not support subclassing",
            )

    def __post_init__(
        self,
        validation_config: MarketResearchAiSafetyPolicyDigestConfig | None,
    ) -> None:
        if type(self) is not MarketResearchAiSafetyPolicyDigestRow:
            raise ValueError("row must be exactly MarketResearchAiSafetyPolicyDigestRow")
        for field_name in ("research_key", "condition_id", "policy_area"):
            _require_public_string(field_name, getattr(self, field_name))
        object.__setattr__(
            self,
            "policy_observed_at",
            _as_utc("policy_observed_at", self.policy_observed_at),
        )
        object.__setattr__(
            self,
            "reviewed_at",
            _optional_utc("reviewed_at", self.reviewed_at),
        )
        object.__setattr__(
            self,
            "policy_age_seconds",
            _require_nonnegative_decimal("policy_age_seconds", self.policy_age_seconds),
        )
        object.__setattr__(
            self,
            "review_lag_seconds",
            _require_optional_nonnegative_decimal(
                "review_lag_seconds",
                self.review_lag_seconds,
            ),
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
            "cross_source_agreement",
            "impact_materiality_score",
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
        _require_status("policy_status", self.policy_status)
        object.__setattr__(
            self,
            "redacted_policy_reference",
            _require_redacted_reference(
                "redacted_policy_reference",
                self.redacted_policy_reference,
            ),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_row_reason_codes(self.reason_codes),
        )
        _validate_row(self, config=validation_config)
        _require_hard_flags("row", self)


@dataclass(frozen=True)
class MarketResearchAiSafetyPolicyDigestReasonCodeCount:
    reason_code: str
    count: Decimal
    policy_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketResearchAiSafetyPolicyDigestReasonCodeCount:
            raise TypeError(
                "MarketResearchAiSafetyPolicyDigestReasonCodeCount does not support "
                "subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not MarketResearchAiSafetyPolicyDigestReasonCodeCount:
            raise ValueError(
                "reason code count must be exactly "
                "MarketResearchAiSafetyPolicyDigestReasonCodeCount",
            )
        _require_reason_code("reason_code", self.reason_code, REASON_CODE_SEQUENCE)
        object.__setattr__(
            self,
            "count",
            _require_nonnegative_decimal("count", self.count),
        )
        object.__setattr__(
            self,
            "policy_ratio",
            _require_ratio_decimal("policy_ratio", self.policy_ratio),
        )
        _require_hard_flags("reason code count", self)


@dataclass(frozen=True)
class MarketResearchAiSafetyPolicyDigestReport:
    generated_at: datetime
    config_version: str
    digest_status: str
    next_step: str
    policy_count: Decimal
    ready_policy_count: Decimal
    watch_policy_count: Decimal
    blocked_policy_count: Decimal
    material_policy_count: Decimal
    stale_policy_count: Decimal
    thin_source_count: Decimal
    low_agreement_count: Decimal
    missing_review_count: Decimal
    slow_review_count: Decimal
    average_materiality_score: Decimal
    max_policy_age_seconds: Decimal
    average_public_source_count: Decimal
    rows: tuple[MarketResearchAiSafetyPolicyDigestRow, ...]
    reason_code_counts: tuple[MarketResearchAiSafetyPolicyDigestReasonCodeCount, ...]
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketResearchAiSafetyPolicyDigestReport:
            raise TypeError(
                "MarketResearchAiSafetyPolicyDigestReport does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not MarketResearchAiSafetyPolicyDigestReport:
            raise ValueError(
                "report must be exactly MarketResearchAiSafetyPolicyDigestReport",
            )
        object.__setattr__(
            self,
            "generated_at",
            _as_utc("generated_at", self.generated_at),
        )
        _require_public_string("config_version", self.config_version)
        _require_status("digest_status", self.digest_status)
        _require_public_string("next_step", self.next_step)
        for field_name in (
            "policy_count",
            "ready_policy_count",
            "watch_policy_count",
            "blocked_policy_count",
            "material_policy_count",
            "stale_policy_count",
            "thin_source_count",
            "low_agreement_count",
            "missing_review_count",
            "slow_review_count",
            "average_materiality_score",
            "max_policy_age_seconds",
            "average_public_source_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        if type(self.rows) is not tuple:
            raise ValueError("rows must be a tuple")
        for row in self.rows:
            if type(row) is not MarketResearchAiSafetyPolicyDigestRow:
                raise ValueError(
                    "rows must contain MarketResearchAiSafetyPolicyDigestRow",
                )
            _require_hard_flags("row", row)
        if type(self.reason_code_counts) is not tuple:
            raise ValueError("reason_code_counts must be a tuple")
        for row in self.reason_code_counts:
            if type(row) is not MarketResearchAiSafetyPolicyDigestReasonCodeCount:
                raise ValueError(
                    "reason_code_counts must contain "
                    "MarketResearchAiSafetyPolicyDigestReasonCodeCount",
                )
            _require_hard_flags("reason code count", row)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_report_reason_codes(self.reason_codes),
        )
        _validate_report(self)
        _require_hard_flags("report", self)


def build_market_research_ai_safety_policy_digest(
    input_rows: list[MarketResearchAiSafetyPolicyDigestInputRow]
    | tuple[MarketResearchAiSafetyPolicyDigestInputRow, ...],
    *,
    config: MarketResearchAiSafetyPolicyDigestConfig | None = None,
    generated_at: datetime,
) -> MarketResearchAiSafetyPolicyDigestReport:
    cfg = config or MarketResearchAiSafetyPolicyDigestConfig()
    if type(cfg) is not MarketResearchAiSafetyPolicyDigestConfig:
        raise ValueError("config must be a MarketResearchAiSafetyPolicyDigestConfig")
    _require_hard_flags("config", cfg)
    report_time = _as_utc("generated_at", generated_at)
    rows = _normalize_input_rows(input_rows, report_time)
    built_rows = tuple(_build_row(row, config=cfg, generated_at=report_time) for row in rows)
    ranked_rows = _ranked_rows(built_rows)
    policy_count = _count(len(ranked_rows))
    ready_policy_count = _count(
        sum(1 for row in ranked_rows if row.policy_status == STATUS_READY),
    )
    watch_policy_count = _count(
        sum(1 for row in ranked_rows if row.policy_status == STATUS_WATCH),
    )
    blocked_policy_count = _count(
        sum(1 for row in ranked_rows if row.policy_status == STATUS_BLOCKED),
    )
    reason_code_counts = _reason_code_counts(ranked_rows)
    reason_codes = tuple(row.reason_code for row in reason_code_counts)
    if not ranked_rows:
        reason_code_counts = (
            MarketResearchAiSafetyPolicyDigestReasonCodeCount(
                reason_code=NO_INPUTS_REASON,
                count=ONE,
                policy_ratio=ONE,
            ),
        )
        reason_codes = (NO_INPUTS_REASON,)
    digest_status = _report_status(
        has_inputs=bool(ranked_rows),
        blocked_policy_count=blocked_policy_count,
        watch_policy_count=watch_policy_count,
    )
    return MarketResearchAiSafetyPolicyDigestReport(
        generated_at=report_time,
        config_version=cfg.config_version,
        digest_status=digest_status,
        next_step=NEXT_STEPS[digest_status],
        policy_count=policy_count,
        ready_policy_count=ready_policy_count,
        watch_policy_count=watch_policy_count,
        blocked_policy_count=blocked_policy_count,
        material_policy_count=_count(
            sum(
                1
                for row in ranked_rows
                if MATERIAL_BLOCK_REASON in row.reason_codes
                or MATERIAL_WATCH_REASON in row.reason_codes
            ),
        ),
        stale_policy_count=_count(
            sum(1 for row in ranked_rows if STALE_POLICY_REASON in row.reason_codes),
        ),
        thin_source_count=_count(
            sum(1 for row in ranked_rows if THIN_SOURCES_REASON in row.reason_codes),
        ),
        low_agreement_count=_count(
            sum(1 for row in ranked_rows if LOW_AGREEMENT_REASON in row.reason_codes),
        ),
        missing_review_count=_count(
            sum(1 for row in ranked_rows if MISSING_REVIEW_REASON in row.reason_codes),
        ),
        slow_review_count=_count(
            sum(1 for row in ranked_rows if SLOW_REVIEW_REASON in row.reason_codes),
        ),
        average_materiality_score=_ratio(
            _sum_decimal(row.impact_materiality_score for row in ranked_rows),
            policy_count,
        ),
        max_policy_age_seconds=max(
            (row.policy_age_seconds for row in ranked_rows),
            default=ZERO,
        ),
        average_public_source_count=_ratio(
            _sum_decimal(row.public_source_count for row in ranked_rows),
            policy_count,
        ),
        rows=ranked_rows,
        reason_code_counts=reason_code_counts,
        reason_codes=reason_codes,
    )


def market_research_ai_safety_policy_digest_payload(
    report: MarketResearchAiSafetyPolicyDigestReport,
) -> dict[str, Any]:
    if type(report) is not MarketResearchAiSafetyPolicyDigestReport:
        raise ValueError(
            "report must be a MarketResearchAiSafetyPolicyDigestReport",
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
    row: MarketResearchAiSafetyPolicyDigestInputRow,
    *,
    config: MarketResearchAiSafetyPolicyDigestConfig,
    generated_at: datetime,
) -> MarketResearchAiSafetyPolicyDigestRow:
    policy_age_seconds = _datetime_delta_seconds(generated_at, row.policy_observed_at)
    review_lag_seconds = (
        None
        if row.reviewed_at is None
        else _datetime_delta_seconds(row.reviewed_at, row.policy_observed_at)
    )
    probability_change = _quantize(
        row.market_probability_after - row.market_probability_before,
    )
    reason_codes = _row_reason_codes(
        policy_age_seconds=policy_age_seconds,
        review_lag_seconds=review_lag_seconds,
        public_source_count=row.public_source_count,
        cross_source_agreement=row.cross_source_agreement,
        impact_materiality_score=row.impact_materiality_score,
        probability_change=probability_change,
        config=config,
    )
    policy_status = _row_status(reason_codes)
    return MarketResearchAiSafetyPolicyDigestRow(
        research_key=row.research_key,
        condition_id=row.condition_id,
        policy_area=row.policy_area,
        policy_observed_at=row.policy_observed_at,
        reviewed_at=row.reviewed_at,
        policy_age_seconds=policy_age_seconds,
        review_lag_seconds=review_lag_seconds,
        public_source_count=row.public_source_count,
        cross_source_agreement=row.cross_source_agreement,
        impact_materiality_score=row.impact_materiality_score,
        market_probability_before=row.market_probability_before,
        market_probability_after=row.market_probability_after,
        probability_change=probability_change,
        policy_status=policy_status,
        redacted_policy_reference=_redacted_reference(row.public_policy_reference),
        reason_codes=reason_codes,
        validation_config=config,
    )


def _normalize_input_rows(
    rows: list[MarketResearchAiSafetyPolicyDigestInputRow]
    | tuple[MarketResearchAiSafetyPolicyDigestInputRow, ...],
    generated_at: datetime,
) -> tuple[MarketResearchAiSafetyPolicyDigestInputRow, ...]:
    if type(rows) not in (list, tuple):
        raise ValueError("input rows must be a list or tuple")
    normalized = tuple(rows)
    seen: set[tuple[str, str]] = set()
    for row in normalized:
        if type(row) is not MarketResearchAiSafetyPolicyDigestInputRow:
            raise ValueError(
                "input rows must contain MarketResearchAiSafetyPolicyDigestInputRow",
            )
        _require_hard_flags("input row", row)
        if row.policy_observed_at > generated_at:
            raise ValueError("policy_observed_at must be on or before generated_at")
        key = (row.research_key, row.condition_id)
        if key in seen:
            raise ValueError("input rows must not contain duplicate research keys")
        seen.add(key)
    return normalized


def _row_reason_codes(
    *,
    policy_age_seconds: Decimal,
    review_lag_seconds: Decimal | None,
    public_source_count: Decimal,
    cross_source_agreement: Decimal,
    impact_materiality_score: Decimal,
    probability_change: Decimal,
    config: MarketResearchAiSafetyPolicyDigestConfig,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    if cross_source_agreement < config.min_cross_source_agreement:
        reason_codes.append(LOW_AGREEMENT_REASON)
    if impact_materiality_score >= config.materiality_block_threshold:
        reason_codes.append(MATERIAL_BLOCK_REASON)
    elif impact_materiality_score >= config.materiality_watch_threshold:
        reason_codes.append(MATERIAL_WATCH_REASON)
    if review_lag_seconds is None:
        reason_codes.append(MISSING_REVIEW_REASON)
    if _abs_decimal(probability_change) >= PROBABILITY_SHIFT_THRESHOLD:
        reason_codes.append(PROBABILITY_SHIFT_REASON)
    if review_lag_seconds is not None and review_lag_seconds > config.max_review_lag_seconds:
        reason_codes.append(SLOW_REVIEW_REASON)
    if policy_age_seconds > config.fresh_policy_max_age_seconds:
        reason_codes.append(STALE_POLICY_REASON)
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
    if MISSING_REVIEW_REASON in reason_codes or MATERIAL_BLOCK_REASON in reason_codes:
        return STATUS_BLOCKED
    if reason_codes == (READY_REASON,):
        return STATUS_READY
    return STATUS_WATCH


def _report_status(
    *,
    has_inputs: bool,
    blocked_policy_count: Decimal,
    watch_policy_count: Decimal,
) -> str:
    if not has_inputs or blocked_policy_count > ZERO:
        return STATUS_BLOCKED
    if watch_policy_count > ZERO:
        return STATUS_WATCH
    return STATUS_READY


def _ranked_rows(
    rows: tuple[MarketResearchAiSafetyPolicyDigestRow, ...],
) -> tuple[MarketResearchAiSafetyPolicyDigestRow, ...]:
    return tuple(
        sorted(
            rows,
            key=lambda row: (
                _status_rank(row.policy_status),
                -row.impact_materiality_score,
                row.policy_area,
                row.research_key,
            ),
        ),
    )


def _status_rank(value: str) -> int:
    return {STATUS_BLOCKED: 0, STATUS_WATCH: 1, STATUS_READY: 2}[value]


def _reason_code_counts(
    rows: tuple[MarketResearchAiSafetyPolicyDigestRow, ...],
) -> tuple[MarketResearchAiSafetyPolicyDigestReasonCodeCount, ...]:
    total = _count(len(rows))
    counts: dict[str, Decimal] = {}
    for row in rows:
        for reason_code in row.reason_codes:
            counts[reason_code] = counts.get(reason_code, ZERO) + ONE
    return tuple(
        MarketResearchAiSafetyPolicyDigestReasonCodeCount(
            reason_code=reason_code,
            count=_count(counts[reason_code]),
            policy_ratio=_ratio(counts[reason_code], total),
        )
        for reason_code in REASON_CODE_SEQUENCE
        if reason_code in counts
    )


def _validate_row(
    row: MarketResearchAiSafetyPolicyDigestRow,
    *,
    config: MarketResearchAiSafetyPolicyDigestConfig | None,
) -> None:
    if config is None:
        config = MarketResearchAiSafetyPolicyDigestConfig()
    if type(config) is not MarketResearchAiSafetyPolicyDigestConfig:
        raise ValueError(
            "validation_config must be a MarketResearchAiSafetyPolicyDigestConfig",
        )
    expected_reason_codes = _row_reason_codes(
        policy_age_seconds=row.policy_age_seconds,
        review_lag_seconds=row.review_lag_seconds,
        public_source_count=row.public_source_count,
        cross_source_agreement=row.cross_source_agreement,
        impact_materiality_score=row.impact_materiality_score,
        probability_change=row.probability_change,
        config=config,
    )
    if row.reason_codes != expected_reason_codes:
        raise ValueError("reason_codes must match row inputs")
    expected_probability_change = _quantize(
        row.market_probability_after - row.market_probability_before,
    )
    if row.probability_change != expected_probability_change:
        raise ValueError("probability_change must match probability inputs")
    if row.reviewed_at is None:
        expected_lag = None
    else:
        expected_lag = _datetime_delta_seconds(
            row.reviewed_at,
            row.policy_observed_at,
        )
    if row.review_lag_seconds != expected_lag:
        raise ValueError(
            "review_lag_seconds must match reviewed_at and policy_observed_at",
        )
    if row.policy_status != _row_status(row.reason_codes):
        raise ValueError("policy_status must match reason_codes")
    if not _is_redacted_reference(row.redacted_policy_reference):
        raise ValueError("redacted_policy_reference must be redacted or public")


def _validate_report(report: MarketResearchAiSafetyPolicyDigestReport) -> None:
    if report.next_step != NEXT_STEPS[report.digest_status]:
        raise ValueError("next_step must match digest_status")
    if report.rows != _ranked_rows(report.rows):
        raise ValueError("rows must be sorted deterministically")
    if report.policy_count != _count(len(report.rows)):
        raise ValueError("policy_count must match rows")
    expected_ready = _count(
        sum(1 for row in report.rows if row.policy_status == STATUS_READY),
    )
    if report.ready_policy_count != expected_ready:
        raise ValueError("ready_policy_count must match rows")
    expected_watch = _count(
        sum(1 for row in report.rows if row.policy_status == STATUS_WATCH),
    )
    if report.watch_policy_count != expected_watch:
        raise ValueError("watch_policy_count must match rows")
    expected_blocked = _count(
        sum(1 for row in report.rows if row.policy_status == STATUS_BLOCKED),
    )
    if report.blocked_policy_count != expected_blocked:
        raise ValueError("blocked_policy_count must match rows")
    if report.material_policy_count != _count(
        sum(
            1
            for row in report.rows
            if MATERIAL_BLOCK_REASON in row.reason_codes
            or MATERIAL_WATCH_REASON in row.reason_codes
        ),
    ):
        raise ValueError("material_policy_count must match rows")
    if report.stale_policy_count != _count(
        sum(1 for row in report.rows if STALE_POLICY_REASON in row.reason_codes),
    ):
        raise ValueError("stale_policy_count must match rows")
    if report.thin_source_count != _count(
        sum(1 for row in report.rows if THIN_SOURCES_REASON in row.reason_codes),
    ):
        raise ValueError("thin_source_count must match rows")
    if report.low_agreement_count != _count(
        sum(1 for row in report.rows if LOW_AGREEMENT_REASON in row.reason_codes),
    ):
        raise ValueError("low_agreement_count must match rows")
    if report.missing_review_count != _count(
        sum(1 for row in report.rows if MISSING_REVIEW_REASON in row.reason_codes),
    ):
        raise ValueError("missing_review_count must match rows")
    if report.slow_review_count != _count(
        sum(1 for row in report.rows if SLOW_REVIEW_REASON in row.reason_codes),
    ):
        raise ValueError("slow_review_count must match rows")
    if report.average_materiality_score != _ratio(
        _sum_decimal(row.impact_materiality_score for row in report.rows),
        report.policy_count,
    ):
        raise ValueError("average_materiality_score must match rows")
    expected_max_age = max(
        (row.policy_age_seconds for row in report.rows),
        default=ZERO,
    )
    if report.max_policy_age_seconds != expected_max_age:
        raise ValueError("max_policy_age_seconds must match rows")
    if report.average_public_source_count != _ratio(
        _sum_decimal(row.public_source_count for row in report.rows),
        report.policy_count,
    ):
        raise ValueError("average_public_source_count must match rows")
    expected_counts = _reason_code_counts(report.rows)
    expected_codes = tuple(row.reason_code for row in expected_counts)
    if not report.rows:
        expected_counts = (
            MarketResearchAiSafetyPolicyDigestReasonCodeCount(
                reason_code=NO_INPUTS_REASON,
                count=ONE,
                policy_ratio=ONE,
            ),
        )
        expected_codes = (NO_INPUTS_REASON,)
    if report.reason_code_counts != expected_counts:
        raise ValueError("reason_code_counts must match rows")
    if report.reason_codes != expected_codes:
        raise ValueError("reason_codes must match reason_code_counts")
    expected_status = _report_status(
        has_inputs=bool(report.rows),
        blocked_policy_count=report.blocked_policy_count,
        watch_policy_count=report.watch_policy_count,
    )
    if report.digest_status != expected_status:
        raise ValueError("digest_status must match rows")


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


def _is_redacted_reference(value: str) -> bool:
    if value.startswith("sha256:") and len(value) == 19:
        return True
    lowered = value.lower()
    return all(fragment in lowered for fragment in ("public",)) and any(
        fragment in lowered for fragment in _PUBLIC_REFERENCE_FRAGMENTS
    )


def _redacted_reference(value: str) -> str:
    if _is_redacted_reference(value):
        return value
    return f"sha256:{sha256(value.encode('utf-8')).hexdigest()[:12]}"


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


def _optional_utc(field_name: str, value: object) -> datetime | None:
    if value is None:
        return None
    return _as_utc(field_name, value)


def _require_finite_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return _quantize(value)


def _require_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_finite_decimal(field_name, value)
    if decimal_value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return decimal_value


def _require_optional_nonnegative_decimal(
    field_name: str,
    value: object,
) -> Decimal | None:
    if value is None:
        return None
    return _require_nonnegative_decimal(field_name, value)


def _require_nonnegative_count_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_nonnegative_decimal(field_name, value)
    if decimal_value != decimal_value.to_integral_value():
        raise ValueError(f"{field_name} must be a whole-number Decimal")
    return _quantize(decimal_value)


def _require_ratio_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_nonnegative_decimal(field_name, value)
    if decimal_value > ONE:
        raise ValueError(f"{field_name} must be in the closed unit interval")
    return decimal_value


def _require_probability_change(field_name: str, value: object) -> Decimal:
    decimal_value = _require_finite_decimal(field_name, value)
    if decimal_value < -ONE or decimal_value > ONE:
        raise ValueError(f"{field_name} must be in the closed signed unit interval")
    return decimal_value


def _datetime_delta_seconds(later: datetime, earlier: datetime) -> Decimal:
    delta = later - earlier
    total_microseconds = (
        Decimal(delta.days * 86400 + delta.seconds) * MICROSECONDS_PER_SECOND
        + Decimal(delta.microseconds)
    )
    return _quantize(total_microseconds / MICROSECONDS_PER_SECOND)


def _quantize(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(QUANT)


def _abs_decimal(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return abs(value).quantize(QUANT)


def _count(value: int | Decimal) -> Decimal:
    if type(value) is int:
        return _quantize(Decimal(value))
    if type(value) is Decimal:
        return _quantize(value)
    raise ValueError("count value must be an int or Decimal")


def _sum_decimal(values: object) -> Decimal:
    total = ZERO
    for value in values:  # type: ignore[union-attr]
        if type(value) is not Decimal:
            raise ValueError("sum values must be Decimal")
        total += value
    return _quantize(total)


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return (numerator / denominator).quantize(QUANT)


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
    if isinstance(value, float):
        raise ValueError("JSON value must not be a float")
    if type(value) is int:
        raise ValueError(f"{path or label} must use Decimal-derived string values")
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
    unsafe_fragments = (
        _join_parts("au", "th"),
        _join_parts("cred", "ential"),
        _join_parts("hid", "den"),
        _join_parts("wal", "let"),
        _join_parts("acc", "ount"),
        _join_parts("bro", "ker"),
        _join_parts("ord", "er"),
        _join_parts("can", "cel"),
        _join_parts("repl", "ace"),
        "sign",
        _join_parts("priv", "ate"),
        _join_parts("api", "_key"),
        _join_parts("sec", "ret"),
        _join_parts("tok", "en"),
        _join_parts("cli", "ent"),
        _join_parts("data", "base"),
        _join_parts("net", "work"),
        _join_parts("li", "ve"),
    )
    if any(fragment in lowered for fragment in unsafe_fragments):
        raise ValueError(f"{field_name} has unsafe value")


def _join_parts(*parts: str) -> str:
    return "".join(parts)


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


__all__ = (
    "DEFAULT_MARKET_RESEARCH_AI_SAFETY_POLICY_DIGEST_CONFIG_VERSION",
    "MarketResearchAiSafetyPolicyDigestConfig",
    "MarketResearchAiSafetyPolicyDigestInputRow",
    "MarketResearchAiSafetyPolicyDigestReasonCodeCount",
    "MarketResearchAiSafetyPolicyDigestReport",
    "MarketResearchAiSafetyPolicyDigestRow",
    "build_market_research_ai_safety_policy_digest",
    "market_research_ai_safety_policy_digest_payload",
)
