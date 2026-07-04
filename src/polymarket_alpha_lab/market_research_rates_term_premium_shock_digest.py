"""Pure Phase 1 rates term-premium shock digest reducer."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, InvalidOperation, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
from typing import Any


DEFAULT_MARKET_RESEARCH_RATES_TERM_PREMIUM_SHOCK_DIGEST_CONFIG_VERSION = (
    "market-research-rates-term-premium-shock-digest-v0"
)

STATUS_READY = "ready"
STATUS_WATCH = "watch"
STATUS_BLOCKED = "blocked"
SCREENING_STATUSES = (STATUS_READY, STATUS_WATCH, STATUS_BLOCKED)

REASON_PREFIX = "market_research_rates_term_premium_shock_digest_"
NO_INPUTS_REASON = f"{REASON_PREFIX}no_inputs"
READY_REASON = f"{REASON_PREFIX}ready"
TERM_PREMIUM_SHOCK_REASON = f"{REASON_PREFIX}term_premium_shock"
LONG_END_YIELD_SHOCK_REASON = f"{REASON_PREFIX}long_end_yield_shock"
CURVE_STEEPENER_SHOCK_REASON = f"{REASON_PREFIX}curve_steepener_shock"
AUCTION_TAIL_SHOCK_REASON = f"{REASON_PREFIX}auction_tail_shock"
PROBABILITY_REPRICING_REASON = f"{REASON_PREFIX}probability_repricing"
STALE_OBSERVATION_REASON = f"{REASON_PREFIX}stale_observation"
THIN_SOURCES_REASON = f"{REASON_PREFIX}thin_sources"
THIN_LIQUIDITY_REASON = f"{REASON_PREFIX}thin_liquidity"

SHOCK_REASONS = (
    TERM_PREMIUM_SHOCK_REASON,
    LONG_END_YIELD_SHOCK_REASON,
    CURVE_STEEPENER_SHOCK_REASON,
    AUCTION_TAIL_SHOCK_REASON,
    PROBABILITY_REPRICING_REASON,
)
TOTAL_SHOCK_REASON_COUNT = Decimal("5.000000")

ROW_REASON_CODE_SEQUENCE = (
    TERM_PREMIUM_SHOCK_REASON,
    LONG_END_YIELD_SHOCK_REASON,
    CURVE_STEEPENER_SHOCK_REASON,
    AUCTION_TAIL_SHOCK_REASON,
    PROBABILITY_REPRICING_REASON,
    STALE_OBSERVATION_REASON,
    THIN_SOURCES_REASON,
    THIN_LIQUIDITY_REASON,
    READY_REASON,
)
REASON_CODE_SEQUENCE = ROW_REASON_CODE_SEQUENCE + (NO_INPUTS_REASON,)

NEXT_STEPS = {
    STATUS_READY: "allow_report_only_rates_term_premium_shock_screening",
    STATUS_WATCH: "review_report_only_rates_term_premium_shock_candidates",
    STATUS_BLOCKED: "block_report_only_rates_term_premium_shock_screening",
}

DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
QUANT = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
MICROSECONDS_PER_SECOND = Decimal("1000000")


def _join_parts(*parts: str) -> str:
    return "".join(parts)


UNSAFE_PUBLIC_TEXT_FRAGMENTS = frozenset(
    (
        _join_parts("au", "th"),
        _join_parts("wal", "let"),
        _join_parts("acc", "ount"),
        _join_parts("pri", "vate"),
        _join_parts("sec", "ret"),
        _join_parts("to", "ken"),
        _join_parts("sig", "ning"),
        _join_parts("sub", "mit"),
        _join_parts("can", "cel"),
        _join_parts("data", "base"),
        _join_parts("per", "sist"),
        _join_parts("pay", "load"),
    ),
)

__all__ = (
    "DEFAULT_MARKET_RESEARCH_RATES_TERM_PREMIUM_SHOCK_DIGEST_CONFIG_VERSION",
    "MarketResearchRatesTermPremiumShockDigestConfig",
    "MarketResearchRatesTermPremiumShockDigestInputRow",
    "MarketResearchRatesTermPremiumShockDigestReasonCodeCount",
    "MarketResearchRatesTermPremiumShockDigestReport",
    "MarketResearchRatesTermPremiumShockDigestRow",
    "build_market_research_rates_term_premium_shock_digest",
    "market_research_rates_term_premium_shock_digest_payload",
)


@dataclass(frozen=True)
class MarketResearchRatesTermPremiumShockDigestConfig:
    config_version: str = (
        DEFAULT_MARKET_RESEARCH_RATES_TERM_PREMIUM_SHOCK_DIGEST_CONFIG_VERSION
    )
    fresh_observation_max_age_seconds: Decimal = Decimal("86400.000000")
    term_premium_change_bp_threshold: Decimal = Decimal("15.000000")
    long_end_yield_change_bp_threshold: Decimal = Decimal("20.000000")
    curve_steepening_bp_threshold: Decimal = Decimal("12.000000")
    auction_tail_bp_threshold: Decimal = Decimal("3.000000")
    probability_repricing_threshold: Decimal = Decimal("0.080000")
    min_source_count: Decimal = Decimal("2.000000")
    min_liquidity_usd: Decimal = Decimal("100.000000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketResearchRatesTermPremiumShockDigestConfig:
            raise TypeError(
                "MarketResearchRatesTermPremiumShockDigestConfig does not support "
                "subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not MarketResearchRatesTermPremiumShockDigestConfig:
            raise ValueError(
                "config must be exactly MarketResearchRatesTermPremiumShockDigestConfig",
            )
        _require_canonical_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_MARKET_RESEARCH_RATES_TERM_PREMIUM_SHOCK_DIGEST_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "fresh_observation_max_age_seconds",
            "term_premium_change_bp_threshold",
            "long_end_yield_change_bp_threshold",
            "curve_steepening_bp_threshold",
            "auction_tail_bp_threshold",
            "probability_repricing_threshold",
            "min_liquidity_usd",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_positive_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "min_source_count",
            _require_positive_count_decimal("min_source_count", self.min_source_count),
        )
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class MarketResearchRatesTermPremiumShockDigestInputRow:
    research_key: str
    condition_id: str
    market_slug: str
    evidence_reference: str
    observed_at: datetime
    source_count: Decimal
    market_liquidity_usd: Decimal
    term_premium_change_bp: Decimal
    ten_year_yield_change_bp: Decimal
    thirty_year_yield_change_bp: Decimal
    curve_steepening_bp: Decimal
    auction_tail_bp: Decimal
    market_probability_before: Decimal
    market_probability_after: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketResearchRatesTermPremiumShockDigestInputRow:
            raise TypeError(
                "MarketResearchRatesTermPremiumShockDigestInputRow does not support "
                "subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not MarketResearchRatesTermPremiumShockDigestInputRow:
            raise ValueError(
                "input row must be exactly "
                "MarketResearchRatesTermPremiumShockDigestInputRow",
            )
        _require_public_identifier("research_key", self.research_key)
        _require_public_identifier("condition_id", self.condition_id)
        _require_public_identifier("market_slug", self.market_slug)
        _require_reference("evidence_reference", self.evidence_reference)
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        object.__setattr__(
            self,
            "source_count",
            _require_nonnegative_count_decimal("source_count", self.source_count),
        )
        object.__setattr__(
            self,
            "market_liquidity_usd",
            _require_nonnegative_decimal(
                "market_liquidity_usd",
                self.market_liquidity_usd,
            ),
        )
        for field_name in (
            "term_premium_change_bp",
            "ten_year_yield_change_bp",
            "thirty_year_yield_change_bp",
            "curve_steepening_bp",
            "auction_tail_bp",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_finite_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in ("market_probability_before", "market_probability_after"):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        _require_hard_flags("input row", self)


@dataclass(frozen=True)
class MarketResearchRatesTermPremiumShockDigestRow:
    research_key: str
    condition_id: str
    market_slug: str
    screening_status: str
    observed_at: datetime
    observation_age_seconds: Decimal
    source_count: Decimal
    market_liquidity_usd: Decimal
    term_premium_change_bp: Decimal
    term_premium_change_abs_bp: Decimal
    ten_year_yield_change_bp: Decimal
    thirty_year_yield_change_bp: Decimal
    long_end_yield_change_abs_bp: Decimal
    curve_steepening_bp: Decimal
    auction_tail_bp: Decimal
    market_probability_before: Decimal
    market_probability_after: Decimal
    market_probability_delta: Decimal
    shock_factor_count: Decimal
    shock_score: Decimal
    redacted_evidence_reference: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketResearchRatesTermPremiumShockDigestRow:
            raise TypeError(
                "MarketResearchRatesTermPremiumShockDigestRow does not support "
                "subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not MarketResearchRatesTermPremiumShockDigestRow:
            raise ValueError(
                "row must be exactly MarketResearchRatesTermPremiumShockDigestRow",
            )
        _require_public_identifier("research_key", self.research_key)
        _require_public_identifier("condition_id", self.condition_id)
        _require_public_identifier("market_slug", self.market_slug)
        _require_screening_status("screening_status", self.screening_status)
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        object.__setattr__(
            self,
            "observation_age_seconds",
            _require_nonnegative_decimal(
                "observation_age_seconds",
                self.observation_age_seconds,
            ),
        )
        object.__setattr__(
            self,
            "source_count",
            _require_nonnegative_count_decimal("source_count", self.source_count),
        )
        object.__setattr__(
            self,
            "market_liquidity_usd",
            _require_nonnegative_decimal(
                "market_liquidity_usd",
                self.market_liquidity_usd,
            ),
        )
        for field_name in (
            "term_premium_change_bp",
            "term_premium_change_abs_bp",
            "ten_year_yield_change_bp",
            "thirty_year_yield_change_bp",
            "long_end_yield_change_abs_bp",
            "curve_steepening_bp",
            "auction_tail_bp",
            "market_probability_delta",
            "shock_factor_count",
            "shock_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_finite_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in ("market_probability_before", "market_probability_after"):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "redacted_evidence_reference",
            _require_redacted_reference(
                "redacted_evidence_reference",
                self.redacted_evidence_reference,
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
class MarketResearchRatesTermPremiumShockDigestReasonCodeCount:
    reason_code: str
    count: Decimal
    candidate_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketResearchRatesTermPremiumShockDigestReasonCodeCount:
            raise TypeError(
                "MarketResearchRatesTermPremiumShockDigestReasonCodeCount does not "
                "support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not MarketResearchRatesTermPremiumShockDigestReasonCodeCount:
            raise ValueError(
                "reason count must be exactly "
                "MarketResearchRatesTermPremiumShockDigestReasonCodeCount",
            )
        _require_reason_code("reason_code", self.reason_code)
        object.__setattr__(
            self,
            "count",
            _require_positive_count_decimal("count", self.count),
        )
        object.__setattr__(
            self,
            "candidate_ratio",
            _require_ratio_decimal("candidate_ratio", self.candidate_ratio),
        )
        _require_hard_flags("reason count", self)


@dataclass(frozen=True)
class MarketResearchRatesTermPremiumShockDigestReport:
    generated_at: datetime
    config_version: str
    digest_status: str
    recommended_next_step: str
    candidate_count: Decimal
    ready_candidate_count: Decimal
    high_risk_candidate_count: Decimal
    blocked_candidate_count: Decimal
    term_premium_shock_count: Decimal
    long_end_yield_shock_count: Decimal
    curve_steepener_shock_count: Decimal
    auction_tail_shock_count: Decimal
    probability_repricing_count: Decimal
    stale_observation_count: Decimal
    thin_source_count: Decimal
    thin_liquidity_count: Decimal
    average_shock_score: Decimal
    max_shock_score: Decimal
    max_term_premium_abs_bp: Decimal
    average_source_count: Decimal
    rows: tuple[MarketResearchRatesTermPremiumShockDigestRow, ...]
    reason_code_counts: tuple[MarketResearchRatesTermPremiumShockDigestReasonCodeCount, ...]
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketResearchRatesTermPremiumShockDigestReport:
            raise TypeError(
                "MarketResearchRatesTermPremiumShockDigestReport does not support "
                "subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not MarketResearchRatesTermPremiumShockDigestReport:
            raise ValueError(
                "report must be exactly MarketResearchRatesTermPremiumShockDigestReport",
            )
        object.__setattr__(
            self,
            "generated_at",
            _as_utc("generated_at", self.generated_at),
        )
        _require_canonical_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_MARKET_RESEARCH_RATES_TERM_PREMIUM_SHOCK_DIGEST_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        _require_screening_status("digest_status", self.digest_status)
        _require_canonical_string("recommended_next_step", self.recommended_next_step)
        for field_name in (
            "candidate_count",
            "ready_candidate_count",
            "high_risk_candidate_count",
            "blocked_candidate_count",
            "term_premium_shock_count",
            "long_end_yield_shock_count",
            "curve_steepener_shock_count",
            "auction_tail_shock_count",
            "probability_repricing_count",
            "stale_observation_count",
            "thin_source_count",
            "thin_liquidity_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_count_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "average_shock_score",
            "max_shock_score",
            "max_term_premium_abs_bp",
            "average_source_count",
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


def build_market_research_rates_term_premium_shock_digest(
    input_rows: list[MarketResearchRatesTermPremiumShockDigestInputRow]
    | tuple[MarketResearchRatesTermPremiumShockDigestInputRow, ...],
    *,
    config: MarketResearchRatesTermPremiumShockDigestConfig,
    generated_at: datetime,
) -> MarketResearchRatesTermPremiumShockDigestReport:
    if type(config) is not MarketResearchRatesTermPremiumShockDigestConfig:
        raise ValueError(
            "config must be a MarketResearchRatesTermPremiumShockDigestConfig",
        )
    _require_hard_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    source_rows = _normalize_input_rows(input_rows, generated_at_utc)
    rows = tuple(
        _build_row(source_row, config=config, generated_at=generated_at_utc)
        for source_row in source_rows
    )
    ranked_rows = _ranked_rows(rows)
    reason_code_counts = _reason_code_counts(ranked_rows)
    reason_codes = tuple(item.reason_code for item in reason_code_counts)
    if not ranked_rows:
        reason_code_counts = (
            MarketResearchRatesTermPremiumShockDigestReasonCodeCount(
                reason_code=NO_INPUTS_REASON,
                count=ONE,
                candidate_ratio=ONE,
            ),
        )
        reason_codes = (NO_INPUTS_REASON,)

    candidate_count = _count(len(ranked_rows))
    ready_candidate_count = _count(
        sum(1 for row in ranked_rows if row.screening_status == STATUS_READY),
    )
    high_risk_candidate_count = _count(
        sum(1 for row in ranked_rows if row.screening_status == STATUS_WATCH),
    )
    blocked_candidate_count = _count(
        sum(1 for row in ranked_rows if row.screening_status == STATUS_BLOCKED),
    )
    digest_status = _report_status(
        has_inputs=bool(ranked_rows),
        blocked_candidate_count=blocked_candidate_count,
        high_risk_candidate_count=high_risk_candidate_count,
    )

    return MarketResearchRatesTermPremiumShockDigestReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        digest_status=digest_status,
        recommended_next_step=NEXT_STEPS[digest_status],
        candidate_count=candidate_count,
        ready_candidate_count=ready_candidate_count,
        high_risk_candidate_count=high_risk_candidate_count,
        blocked_candidate_count=blocked_candidate_count,
        term_premium_shock_count=_reason_count(
            ranked_rows,
            TERM_PREMIUM_SHOCK_REASON,
        ),
        long_end_yield_shock_count=_reason_count(
            ranked_rows,
            LONG_END_YIELD_SHOCK_REASON,
        ),
        curve_steepener_shock_count=_reason_count(
            ranked_rows,
            CURVE_STEEPENER_SHOCK_REASON,
        ),
        auction_tail_shock_count=_reason_count(ranked_rows, AUCTION_TAIL_SHOCK_REASON),
        probability_repricing_count=_reason_count(
            ranked_rows,
            PROBABILITY_REPRICING_REASON,
        ),
        stale_observation_count=_reason_count(ranked_rows, STALE_OBSERVATION_REASON),
        thin_source_count=_reason_count(ranked_rows, THIN_SOURCES_REASON),
        thin_liquidity_count=_reason_count(ranked_rows, THIN_LIQUIDITY_REASON),
        average_shock_score=_ratio(
            _sum_decimal(row.shock_score for row in ranked_rows),
            candidate_count,
        ),
        max_shock_score=max((row.shock_score for row in ranked_rows), default=ZERO),
        max_term_premium_abs_bp=max(
            (row.term_premium_change_abs_bp for row in ranked_rows),
            default=ZERO,
        ),
        average_source_count=_ratio(
            _sum_decimal(row.source_count for row in ranked_rows),
            candidate_count,
        ),
        rows=ranked_rows,
        reason_code_counts=reason_code_counts,
        reason_codes=reason_codes,
    )


def market_research_rates_term_premium_shock_digest_payload(
    report: MarketResearchRatesTermPremiumShockDigestReport,
) -> dict[str, Any]:
    if type(report) is not MarketResearchRatesTermPremiumShockDigestReport:
        raise ValueError(
            "report must be a MarketResearchRatesTermPremiumShockDigestReport",
        )
    _require_hard_flags("report", report)
    return _json_ready(asdict(report))


def _normalize_input_rows(
    input_rows: object,
    generated_at: datetime,
) -> tuple[MarketResearchRatesTermPremiumShockDigestInputRow, ...]:
    if type(input_rows) not in (list, tuple):
        raise ValueError("input rows must be a list or tuple")
    normalized = tuple(input_rows)
    seen: set[tuple[str, str, str]] = set()
    for input_row in normalized:
        if type(input_row) is not MarketResearchRatesTermPremiumShockDigestInputRow:
            raise ValueError(
                "input rows must contain "
                "MarketResearchRatesTermPremiumShockDigestInputRow values",
            )
        _require_hard_flags("input row", input_row)
        key = (input_row.research_key, input_row.condition_id, input_row.market_slug)
        if key in seen:
            raise ValueError("input rows must use unique research condition market keys")
        seen.add(key)
        if input_row.observed_at > generated_at:
            raise ValueError("observed_at cannot be after generated_at")
    return normalized


def _build_row(
    input_row: MarketResearchRatesTermPremiumShockDigestInputRow,
    *,
    config: MarketResearchRatesTermPremiumShockDigestConfig,
    generated_at: datetime,
) -> MarketResearchRatesTermPremiumShockDigestRow:
    observation_age_seconds = _seconds_between(input_row.observed_at, generated_at)
    term_premium_change_abs_bp = abs(input_row.term_premium_change_bp)
    long_end_yield_change_abs_bp = max(
        abs(input_row.ten_year_yield_change_bp),
        abs(input_row.thirty_year_yield_change_bp),
    )
    market_probability_delta = _probability_delta(
        input_row.market_probability_after - input_row.market_probability_before,
    )
    reason_codes = _row_reason_codes(
        source_count=input_row.source_count,
        market_liquidity_usd=input_row.market_liquidity_usd,
        term_premium_change_abs_bp=term_premium_change_abs_bp,
        long_end_yield_change_abs_bp=long_end_yield_change_abs_bp,
        curve_steepening_bp=input_row.curve_steepening_bp,
        auction_tail_bp=input_row.auction_tail_bp,
        market_probability_delta=market_probability_delta,
        observation_age_seconds=observation_age_seconds,
        config=config,
    )
    shock_factor_count = _count(
        sum(1 for reason_code in reason_codes if reason_code in SHOCK_REASONS),
    )
    shock_score = _ratio(shock_factor_count, TOTAL_SHOCK_REASON_COUNT)
    return MarketResearchRatesTermPremiumShockDigestRow(
        research_key=input_row.research_key,
        condition_id=input_row.condition_id,
        market_slug=input_row.market_slug,
        screening_status=_row_status(reason_codes),
        observed_at=input_row.observed_at,
        observation_age_seconds=observation_age_seconds,
        source_count=input_row.source_count,
        market_liquidity_usd=input_row.market_liquidity_usd,
        term_premium_change_bp=input_row.term_premium_change_bp,
        term_premium_change_abs_bp=term_premium_change_abs_bp,
        ten_year_yield_change_bp=input_row.ten_year_yield_change_bp,
        thirty_year_yield_change_bp=input_row.thirty_year_yield_change_bp,
        long_end_yield_change_abs_bp=long_end_yield_change_abs_bp,
        curve_steepening_bp=input_row.curve_steepening_bp,
        auction_tail_bp=input_row.auction_tail_bp,
        market_probability_before=input_row.market_probability_before,
        market_probability_after=input_row.market_probability_after,
        market_probability_delta=market_probability_delta,
        shock_factor_count=shock_factor_count,
        shock_score=shock_score,
        redacted_evidence_reference=_redacted_reference(input_row.evidence_reference),
        reason_codes=reason_codes,
    )


def _row_reason_codes(
    *,
    source_count: Decimal,
    market_liquidity_usd: Decimal,
    term_premium_change_abs_bp: Decimal,
    long_end_yield_change_abs_bp: Decimal,
    curve_steepening_bp: Decimal,
    auction_tail_bp: Decimal,
    market_probability_delta: Decimal,
    observation_age_seconds: Decimal,
    config: MarketResearchRatesTermPremiumShockDigestConfig,
) -> tuple[str, ...]:
    reasons: list[str] = []
    if term_premium_change_abs_bp >= config.term_premium_change_bp_threshold:
        reasons.append(TERM_PREMIUM_SHOCK_REASON)
    if long_end_yield_change_abs_bp >= config.long_end_yield_change_bp_threshold:
        reasons.append(LONG_END_YIELD_SHOCK_REASON)
    if abs(curve_steepening_bp) >= config.curve_steepening_bp_threshold:
        reasons.append(CURVE_STEEPENER_SHOCK_REASON)
    if abs(auction_tail_bp) >= config.auction_tail_bp_threshold:
        reasons.append(AUCTION_TAIL_SHOCK_REASON)
    if abs(market_probability_delta) >= config.probability_repricing_threshold:
        reasons.append(PROBABILITY_REPRICING_REASON)
    if observation_age_seconds > config.fresh_observation_max_age_seconds:
        reasons.append(STALE_OBSERVATION_REASON)
    if source_count < config.min_source_count:
        reasons.append(THIN_SOURCES_REASON)
    if market_liquidity_usd < config.min_liquidity_usd:
        reasons.append(THIN_LIQUIDITY_REASON)
    if not reasons:
        reasons.append(READY_REASON)
    return _normalize_row_reason_codes(tuple(reasons))


def _row_status(reason_codes: tuple[str, ...]) -> str:
    if (
        STALE_OBSERVATION_REASON in reason_codes
        or THIN_SOURCES_REASON in reason_codes
        or THIN_LIQUIDITY_REASON in reason_codes
    ):
        return STATUS_BLOCKED
    if reason_codes == (READY_REASON,):
        return STATUS_READY
    return STATUS_WATCH


def _report_status(
    *,
    has_inputs: bool,
    blocked_candidate_count: Decimal,
    high_risk_candidate_count: Decimal,
) -> str:
    if not has_inputs or blocked_candidate_count > ZERO:
        return STATUS_BLOCKED
    if high_risk_candidate_count > ZERO:
        return STATUS_WATCH
    return STATUS_READY


def _ranked_rows(
    rows: tuple[MarketResearchRatesTermPremiumShockDigestRow, ...],
) -> tuple[MarketResearchRatesTermPremiumShockDigestRow, ...]:
    return tuple(sorted(rows, key=_row_sort_key))


def _row_sort_key(
    row: MarketResearchRatesTermPremiumShockDigestRow,
) -> tuple[int, Decimal, str, str, str]:
    return (
        {STATUS_BLOCKED: 0, STATUS_WATCH: 1, STATUS_READY: 2}[row.screening_status],
        -row.shock_score,
        row.market_slug,
        row.condition_id,
        row.research_key,
    )


def _reason_code_counts(
    rows: tuple[MarketResearchRatesTermPremiumShockDigestRow, ...],
) -> tuple[MarketResearchRatesTermPremiumShockDigestReasonCodeCount, ...]:
    counts: dict[str, int] = {}
    for row in rows:
        for reason_code in row.reason_codes:
            counts[reason_code] = counts[reason_code] + 1 if reason_code in counts else 1
    candidate_count = _count(len(rows))
    return tuple(
        MarketResearchRatesTermPremiumShockDigestReasonCodeCount(
            reason_code=reason_code,
            count=_count(counts[reason_code]),
            candidate_ratio=_ratio(_count(counts[reason_code]), candidate_count),
        )
        for reason_code in REASON_CODE_SEQUENCE
        if reason_code in counts
    )


def _reason_count(
    rows: tuple[MarketResearchRatesTermPremiumShockDigestRow, ...],
    reason_code: str,
) -> Decimal:
    return _count(sum(1 for row in rows if reason_code in row.reason_codes))


def _normalize_rows(
    rows: object,
) -> tuple[MarketResearchRatesTermPremiumShockDigestRow, ...]:
    if type(rows) not in (list, tuple):
        raise ValueError("rows must be a list or tuple")
    normalized = tuple(rows)
    seen: set[tuple[str, str, str]] = set()
    previous_key: tuple[int, Decimal, str, str, str] | None = None
    for row in normalized:
        if type(row) is not MarketResearchRatesTermPremiumShockDigestRow:
            raise ValueError(
                "rows must contain MarketResearchRatesTermPremiumShockDigestRow",
            )
        _require_hard_flags("row", row)
        identity = (row.research_key, row.condition_id, row.market_slug)
        if identity in seen:
            raise ValueError("rows must use unique research condition market keys")
        seen.add(identity)
        key = _row_sort_key(row)
        if previous_key is not None and key <= previous_key:
            raise ValueError("rows must be sorted by unique screening and market keys")
        previous_key = key
    return normalized


def _normalize_reason_code_counts(
    values: object,
) -> tuple[MarketResearchRatesTermPremiumShockDigestReasonCodeCount, ...]:
    if type(values) not in (list, tuple):
        raise ValueError("reason_code_counts must be a list or tuple")
    counts = tuple(values)
    previous_rank = -1
    for count in counts:
        if type(count) is not MarketResearchRatesTermPremiumShockDigestReasonCodeCount:
            raise ValueError("reason_code_counts must contain reason count rows")
        _require_hard_flags("reason count", count)
        rank = _reason_code_rank(count.reason_code)
        if rank <= previous_rank:
            raise ValueError("reason_code_counts must be sorted by unique reason_code")
        previous_rank = rank
    return counts


def _normalize_row_reason_codes(values: object) -> tuple[str, ...]:
    reason_codes = _normalize_reason_codes(values)
    if not reason_codes:
        raise ValueError("reason_codes must not be empty")
    previous_rank = -1
    for reason_code in reason_codes:
        rank = _row_reason_code_rank(reason_code)
        if rank <= previous_rank:
            raise ValueError("reason_codes must be sorted by unique reason code")
        previous_rank = rank
    if READY_REASON in reason_codes and len(reason_codes) != 1:
        raise ValueError("reason_codes ready cannot be combined")
    if NO_INPUTS_REASON in reason_codes:
        raise ValueError("reason_codes no_inputs is report-only")
    return reason_codes


def _normalize_report_reason_codes(values: object) -> tuple[str, ...]:
    reason_codes = _normalize_reason_codes(values)
    if not reason_codes:
        raise ValueError("reason_codes must not be empty")
    previous_rank = -1
    for reason_code in reason_codes:
        rank = _reason_code_rank(reason_code)
        if rank <= previous_rank:
            raise ValueError("reason_codes must be sorted by unique reason code")
        previous_rank = rank
    if NO_INPUTS_REASON in reason_codes and len(reason_codes) != 1:
        raise ValueError("reason_codes no_inputs cannot be combined")
    return reason_codes


def _normalize_reason_codes(values: object) -> tuple[str, ...]:
    if type(values) not in (list, tuple):
        raise ValueError("reason_codes must be a list or tuple")
    reason_codes = tuple(values)
    for reason_code in reason_codes:
        _require_reason_code("reason_codes", reason_code)
    if len(reason_codes) != len(frozenset(reason_codes)):
        raise ValueError("reason_codes must be unique")
    return reason_codes


def _validate_row(row: MarketResearchRatesTermPremiumShockDigestRow) -> None:
    if row.term_premium_change_abs_bp != abs(row.term_premium_change_bp):
        raise ValueError("term_premium_change_abs_bp must match absolute change")
    expected_long_end_abs = max(
        abs(row.ten_year_yield_change_bp),
        abs(row.thirty_year_yield_change_bp),
    )
    if row.long_end_yield_change_abs_bp != expected_long_end_abs:
        raise ValueError("long_end_yield_change_abs_bp must match long-end yields")
    expected_probability_delta = _probability_delta(
        row.market_probability_after - row.market_probability_before,
    )
    if row.market_probability_delta != expected_probability_delta:
        raise ValueError("market_probability_delta must match probability fields")
    expected_shock_factor_count = _count(
        sum(1 for reason_code in row.reason_codes if reason_code in SHOCK_REASONS),
    )
    if row.shock_factor_count != expected_shock_factor_count:
        raise ValueError("shock_factor_count must match shock reason codes")
    if row.shock_score != _ratio(row.shock_factor_count, TOTAL_SHOCK_REASON_COUNT):
        raise ValueError("shock_score must match shock_factor_count")
    if row.screening_status != _row_status(row.reason_codes):
        raise ValueError("screening_status must match reason_codes")


def _validate_report(report: MarketResearchRatesTermPremiumShockDigestReport) -> None:
    if report.candidate_count != _count(len(report.rows)):
        raise ValueError("candidate_count must match rows")
    if report.ready_candidate_count != _count(
        sum(1 for row in report.rows if row.screening_status == STATUS_READY),
    ):
        raise ValueError("ready_candidate_count must match rows")
    if report.high_risk_candidate_count != _count(
        sum(1 for row in report.rows if row.screening_status == STATUS_WATCH),
    ):
        raise ValueError("high_risk_candidate_count must match rows")
    if report.blocked_candidate_count != _count(
        sum(1 for row in report.rows if row.screening_status == STATUS_BLOCKED),
    ):
        raise ValueError("blocked_candidate_count must match rows")
    expected_counts = _reason_code_counts(report.rows)
    if not report.rows:
        expected_counts = (
            MarketResearchRatesTermPremiumShockDigestReasonCodeCount(
                reason_code=NO_INPUTS_REASON,
                count=ONE,
                candidate_ratio=ONE,
            ),
        )
    if report.reason_code_counts != expected_counts:
        raise ValueError("reason_code_counts must match rows")
    if report.reason_codes != tuple(item.reason_code for item in report.reason_code_counts):
        raise ValueError("reason_codes must match reason_code_counts")
    expected_status = _report_status(
        has_inputs=bool(report.rows),
        blocked_candidate_count=report.blocked_candidate_count,
        high_risk_candidate_count=report.high_risk_candidate_count,
    )
    if report.digest_status != expected_status:
        raise ValueError("digest_status must match row statuses")
    if report.recommended_next_step != NEXT_STEPS[report.digest_status]:
        raise ValueError("recommended_next_step must match digest_status")
    _validate_report_reason_metric(
        report,
        "term_premium_shock_count",
        TERM_PREMIUM_SHOCK_REASON,
    )
    _validate_report_reason_metric(
        report,
        "long_end_yield_shock_count",
        LONG_END_YIELD_SHOCK_REASON,
    )
    _validate_report_reason_metric(
        report,
        "curve_steepener_shock_count",
        CURVE_STEEPENER_SHOCK_REASON,
    )
    _validate_report_reason_metric(
        report,
        "auction_tail_shock_count",
        AUCTION_TAIL_SHOCK_REASON,
    )
    _validate_report_reason_metric(
        report,
        "probability_repricing_count",
        PROBABILITY_REPRICING_REASON,
    )
    _validate_report_reason_metric(
        report,
        "stale_observation_count",
        STALE_OBSERVATION_REASON,
    )
    _validate_report_reason_metric(report, "thin_source_count", THIN_SOURCES_REASON)
    _validate_report_reason_metric(
        report,
        "thin_liquidity_count",
        THIN_LIQUIDITY_REASON,
    )
    if report.average_shock_score != _ratio(
        _sum_decimal(row.shock_score for row in report.rows),
        report.candidate_count,
    ):
        raise ValueError("average_shock_score must match rows")
    if report.max_shock_score != max(
        (row.shock_score for row in report.rows),
        default=ZERO,
    ):
        raise ValueError("max_shock_score must match rows")
    if report.max_term_premium_abs_bp != max(
        (row.term_premium_change_abs_bp for row in report.rows),
        default=ZERO,
    ):
        raise ValueError("max_term_premium_abs_bp must match rows")
    if report.average_source_count != _ratio(
        _sum_decimal(row.source_count for row in report.rows),
        report.candidate_count,
    ):
        raise ValueError("average_source_count must match rows")


def _validate_report_reason_metric(
    report: MarketResearchRatesTermPremiumShockDigestReport,
    field_name: str,
    reason_code: str,
) -> None:
    if getattr(report, field_name) != _reason_count(report.rows, reason_code):
        raise ValueError(f"{field_name} must match rows")


def _require_reason_code(field_name: str, value: object) -> str:
    _require_canonical_string(field_name, value)
    if value not in REASON_CODE_SEQUENCE:
        raise ValueError(f"{field_name} must be a supported reason code")
    return value


def _row_reason_code_rank(reason_code: str) -> int:
    if reason_code not in ROW_REASON_CODE_SEQUENCE:
        raise ValueError("reason_codes must be row-supported reason codes")
    return ROW_REASON_CODE_SEQUENCE.index(reason_code)


def _reason_code_rank(reason_code: str) -> int:
    if reason_code not in REASON_CODE_SEQUENCE:
        raise ValueError("reason_code must be supported")
    return REASON_CODE_SEQUENCE.index(reason_code)


def _require_screening_status(field_name: str, value: object) -> str:
    _require_canonical_string(field_name, value)
    if value not in SCREENING_STATUSES:
        raise ValueError(f"{field_name} must be ready, watch, or blocked")
    return value


def _require_public_identifier(field_name: str, value: object) -> str:
    _require_canonical_string(field_name, value)
    lowered = value.lower()
    if any(fragment in lowered for fragment in UNSAFE_PUBLIC_TEXT_FRAGMENTS):
        raise ValueError(f"{field_name} must be a public identifier")
    if any(character.isspace() for character in value):
        raise ValueError(f"{field_name} must be a public identifier")
    return value


def _require_reference(field_name: str, value: object) -> str:
    _require_canonical_string(field_name, value)
    if any(ord(character) < 32 for character in value):
        raise ValueError(f"{field_name} must be printable")
    return value


def _require_canonical_string(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value:
        raise ValueError(f"{field_name} must not be empty")
    if value.strip() != value:
        raise ValueError(f"{field_name} must not have surrounding whitespace")
    return value


def _require_redacted_reference(field_name: str, value: object) -> str:
    _require_canonical_string(field_name, value)
    if len(value) != 71 or not value.startswith("sha256:"):
        raise ValueError(f"{field_name} must be redacted")
    digest = value.removeprefix("sha256:")
    if any(character not in "0123456789abcdef" for character in digest):
        raise ValueError(f"{field_name} must be redacted")
    return value


def _redacted_reference(value: str) -> str:
    return f"sha256:{sha256(value.encode('utf-8')).hexdigest()}"


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _seconds_between(start: datetime, end: datetime) -> Decimal:
    if end < start:
        raise ValueError("datetime end cannot be before start")
    delta = end - start
    total_microseconds = (
        Decimal(delta.days) * Decimal("86400") * MICROSECONDS_PER_SECOND
        + Decimal(delta.seconds) * MICROSECONDS_PER_SECOND
        + Decimal(delta.microseconds)
    )
    return _finite_decimal(total_microseconds / MICROSECONDS_PER_SECOND)


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return _quantize(value)


def _require_finite_decimal(field_name: str, value: object) -> Decimal:
    return _require_decimal(field_name, value)


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


def _require_nonnegative_count_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_nonnegative_decimal(field_name, value)
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{field_name} must be a whole-count Decimal")
    return normalized


def _require_positive_count_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_positive_decimal(field_name, value)
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{field_name} must be a whole-count Decimal")
    return normalized


def _require_ratio_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < ZERO or normalized > ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return normalized


def _probability_delta(value: Decimal) -> Decimal:
    normalized = _finite_decimal(value)
    if normalized < Decimal("-1.000000") or normalized > ONE:
        raise ValueError("market_probability_delta must be between -1 and 1")
    return normalized


def _count(value: int) -> Decimal:
    return _quantize(Decimal(value))


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO:
        return ZERO
    return _finite_decimal(numerator / denominator)


def _sum_decimal(values: object) -> Decimal:
    total = ZERO
    for value in values:
        total = _finite_decimal(total + value)
    return total


def _finite_decimal(value: Decimal) -> Decimal:
    if not value.is_finite():
        raise ValueError("decimal value must be finite")
    return _quantize(value)


def _quantize(value: Decimal) -> Decimal:
    try:
        with localcontext(DECIMAL_CONTEXT):
            return value.quantize(QUANT)
    except InvalidOperation as exc:
        raise ValueError("Decimal value must be quantizable") from exc


def _require_hard_flags(label: str, value: object) -> None:
    for flag_name in ("paper_only", "report_only", "readonly"):
        if getattr(value, flag_name, None) is not True:
            raise ValueError(f"{label} {flag_name} must be True")


def _json_ready(value: object) -> Any:
    if type(value) is Decimal:
        return format(value, "f")
    if type(value) is datetime:
        return value.isoformat()
    if type(value) is str:
        _require_payload_string(value)
        return value
    if type(value) is bool or value is None:
        return value
    if type(value) in (list, tuple):
        return [_json_ready(item) for item in value]
    if type(value) is dict:
        result: dict[str, Any] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("payload keys must be strings")
            _require_payload_string(key)
            result[key] = _json_ready(item)
        return result
    if type(value) is float:
        raise ValueError("payload must not contain float values")
    if type(value) is int:
        raise ValueError("payload numerics must be Decimal-derived strings")
    raise ValueError("payload contains unsupported value")


def _require_payload_string(value: str) -> None:
    lowered = value.lower()
    for fragment in UNSAFE_PUBLIC_TEXT_FRAGMENTS:
        if fragment in lowered and not value.startswith("sha256:"):
            raise ValueError("payload contains unsafe public text")
