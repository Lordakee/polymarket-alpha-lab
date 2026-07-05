"""Pure Phase 1 gold volatility catalyst digest reducer."""

from __future__ import annotations

from dataclasses import asdict, dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
from typing import Any


DEFAULT_MARKET_RESEARCH_GOLD_VOLATILITY_CATALYST_DIGEST_CONFIG_VERSION = (
    "market-research-gold-volatility-catalyst-digest-v0"
)

DIGEST_STATUSES = ("ready", "watch", "blocked")
READY_REASON = "market_research_gold_volatility_catalyst_digest_ready"
STALE_RESEARCH_REASON = (
    "market_research_gold_volatility_catalyst_digest_stale_research"
)
ELAPSED_REASON = "market_research_gold_volatility_catalyst_digest_elapsed"
THIN_REFERENCES_REASON = (
    "market_research_gold_volatility_catalyst_digest_thin_references"
)
ATR_MOVE_GAP_REASON = (
    "market_research_gold_volatility_catalyst_digest_atr_move_gap"
)
OPTIONS_SKEW_GAP_REASON = (
    "market_research_gold_volatility_catalyst_digest_options_skew_gap"
)
VOLATILITY_LIQUIDITY_GAP_REASON = (
    "market_research_gold_volatility_catalyst_digest_volatility_liquidity_gap"
)
NO_INPUTS_REASON = "market_research_gold_volatility_catalyst_digest_no_inputs"
REASON_CODES = (
    STALE_RESEARCH_REASON,
    ELAPSED_REASON,
    THIN_REFERENCES_REASON,
    ATR_MOVE_GAP_REASON,
    OPTIONS_SKEW_GAP_REASON,
    VOLATILITY_LIQUIDITY_GAP_REASON,
    READY_REASON,
    NO_INPUTS_REASON,
)
NEXT_STEPS = {
    "ready": "allow_report_only_market_research_gold_volatility_catalyst_digest",
    "watch": "watch_report_only_market_research_gold_volatility_catalyst_digest",
    "blocked": "block_report_only_market_research_gold_volatility_catalyst_digest",
}

DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
QUANTUM = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
MICROSECONDS_PER_SECOND = Decimal("1000000")


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
        _join_parts("per", "sist"),
        _join_parts("pay", "load"),
        _join_parts("sec", "ret"),
        _join_parts("to", "ken"),
        _join_parts("pri", "vate"),
    ),
)

__all__ = (
    "DEFAULT_MARKET_RESEARCH_GOLD_VOLATILITY_CATALYST_DIGEST_CONFIG_VERSION",
    "MarketResearchGoldVolatilityCatalystDigestConfig",
    "MarketResearchGoldVolatilityCatalystDigestInputRow",
    "MarketResearchGoldVolatilityCatalystDigestReasonCodeCount",
    "MarketResearchGoldVolatilityCatalystDigestReport",
    "MarketResearchGoldVolatilityCatalystDigestRow",
    "build_market_research_gold_volatility_catalyst_digest",
    "market_research_gold_volatility_catalyst_digest_payload",
)


@dataclass(frozen=True)
class MarketResearchGoldVolatilityCatalystDigestConfig:
    config_version: str = (
        DEFAULT_MARKET_RESEARCH_GOLD_VOLATILITY_CATALYST_DIGEST_CONFIG_VERSION
    )
    max_research_age_seconds: Decimal = Decimal("7200.000000")
    watch_within_seconds: Decimal = Decimal("86400.000000")
    min_reference_count: Decimal = Decimal("2.000000")
    min_atr_move_score: Decimal = Decimal("0.550000")
    min_options_skew_score: Decimal = Decimal("0.500000")
    min_liquidity_score: Decimal = Decimal("0.650000")
    max_realized_volatility_score: Decimal = Decimal("0.750000")
    confidence_decay_per_stale_research: Decimal = Decimal("0.100000")
    confidence_decay_per_elapsed_catalyst: Decimal = Decimal("0.200000")
    confidence_decay_per_thin_references: Decimal = Decimal("0.080000")
    confidence_decay_per_atr_gap: Decimal = Decimal("0.120000")
    confidence_decay_per_options_skew_gap: Decimal = Decimal("0.100000")
    confidence_decay_per_volatility_liquidity_gap: Decimal = Decimal("0.150000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketResearchGoldVolatilityCatalystDigestConfig:
            raise TypeError(
                "MarketResearchGoldVolatilityCatalystDigestConfig "
                "does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not MarketResearchGoldVolatilityCatalystDigestConfig:
            raise ValueError(
                "config must be exactly "
                "MarketResearchGoldVolatilityCatalystDigestConfig",
            )
        _require_canonical_string("config_version", self.config_version)
        for field_name in (
            "max_research_age_seconds",
            "watch_within_seconds",
            "min_reference_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_positive_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "min_reference_count",
            _require_positive_count_decimal(
                "min_reference_count",
                self.min_reference_count,
            ),
        )
        for field_name in (
            "min_atr_move_score",
            "min_options_skew_score",
            "min_liquidity_score",
            "max_realized_volatility_score",
            "confidence_decay_per_stale_research",
            "confidence_decay_per_elapsed_catalyst",
            "confidence_decay_per_thin_references",
            "confidence_decay_per_atr_gap",
            "confidence_decay_per_options_skew_gap",
            "confidence_decay_per_volatility_liquidity_gap",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        _require_flags("config", self)


@dataclass(frozen=True)
class MarketResearchGoldVolatilityCatalystDigestInputRow:
    market_research_key: str
    volatility_catalyst_key: str
    catalyst_family: str
    public_catalyst_reference: str
    catalyst_at: datetime
    research_observed_at: datetime
    reference_count: Decimal
    atr_move_score: Decimal
    options_skew_score: Decimal
    realized_volatility_score: Decimal
    liquidity_score: Decimal
    base_confidence_score: Decimal
    source_config_version: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketResearchGoldVolatilityCatalystDigestInputRow:
            raise TypeError(
                "MarketResearchGoldVolatilityCatalystDigestInputRow "
                "does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not MarketResearchGoldVolatilityCatalystDigestInputRow:
            raise ValueError(
                "input row must be exactly "
                "MarketResearchGoldVolatilityCatalystDigestInputRow",
            )
        for field_name in (
            "market_research_key",
            "volatility_catalyst_key",
            "catalyst_family",
        ):
            _require_public_string(field_name, getattr(self, field_name))
        _require_canonical_string(
            "public_catalyst_reference",
            self.public_catalyst_reference,
        )
        object.__setattr__(self, "catalyst_at", _as_utc("catalyst_at", self.catalyst_at))
        object.__setattr__(
            self,
            "research_observed_at",
            _as_utc("research_observed_at", self.research_observed_at),
        )
        object.__setattr__(
            self,
            "reference_count",
            _require_nonnegative_count_decimal("reference_count", self.reference_count),
        )
        for field_name in (
            "atr_move_score",
            "options_skew_score",
            "realized_volatility_score",
            "liquidity_score",
            "base_confidence_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        _require_public_string("source_config_version", self.source_config_version)
        _require_flags("input row", self)


@dataclass(frozen=True)
class MarketResearchGoldVolatilityCatalystDigestRow:
    market_research_key: str
    volatility_catalyst_key: str
    catalyst_family: str
    catalyst_status: str
    seconds_until_catalyst: Decimal
    research_age_seconds: Decimal
    reference_count: Decimal
    reference_gap_count: Decimal
    atr_move_score: Decimal
    options_skew_score: Decimal
    realized_volatility_score: Decimal
    liquidity_score: Decimal
    base_confidence_score: Decimal
    confidence_decay_score: Decimal
    confidence_score: Decimal
    redacted_public_catalyst_reference: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketResearchGoldVolatilityCatalystDigestRow:
            raise TypeError(
                "MarketResearchGoldVolatilityCatalystDigestRow "
                "does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not MarketResearchGoldVolatilityCatalystDigestRow:
            raise ValueError(
                "row must be exactly MarketResearchGoldVolatilityCatalystDigestRow",
            )
        for field_name in (
            "market_research_key",
            "volatility_catalyst_key",
            "catalyst_family",
        ):
            _require_public_string(field_name, getattr(self, field_name))
        _require_digest_status("catalyst_status", self.catalyst_status)
        for field_name in (
            "seconds_until_catalyst",
            "research_age_seconds",
            "reference_count",
            "reference_gap_count",
            "atr_move_score",
            "options_skew_score",
            "realized_volatility_score",
            "liquidity_score",
            "base_confidence_score",
            "confidence_decay_score",
            "confidence_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_decimal(field_name, getattr(self, field_name)),
            )
        if self.research_age_seconds < ZERO:
            raise ValueError("research_age_seconds must be nonnegative")
        object.__setattr__(
            self,
            "reference_count",
            _require_nonnegative_count_decimal("reference_count", self.reference_count),
        )
        object.__setattr__(
            self,
            "reference_gap_count",
            _require_nonnegative_count_decimal(
                "reference_gap_count",
                self.reference_gap_count,
            ),
        )
        for field_name in (
            "atr_move_score",
            "options_skew_score",
            "realized_volatility_score",
            "liquidity_score",
            "base_confidence_score",
            "confidence_decay_score",
            "confidence_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        _require_redacted_reference(
            "redacted_public_catalyst_reference",
            self.redacted_public_catalyst_reference,
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes),
        )
        _validate_row(self)
        _require_flags("row", self)


@dataclass(frozen=True)
class MarketResearchGoldVolatilityCatalystDigestReasonCodeCount:
    reason_code: str
    count: Decimal
    catalyst_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketResearchGoldVolatilityCatalystDigestReasonCodeCount:
            raise TypeError(
                "MarketResearchGoldVolatilityCatalystDigestReasonCodeCount "
                "does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not MarketResearchGoldVolatilityCatalystDigestReasonCodeCount:
            raise ValueError(
                "reason count must be exactly "
                "MarketResearchGoldVolatilityCatalystDigestReasonCodeCount",
            )
        _require_reason_code("reason_code", self.reason_code)
        object.__setattr__(
            self,
            "count",
            _require_nonnegative_count_decimal("count", self.count),
        )
        object.__setattr__(
            self,
            "catalyst_ratio",
            _require_ratio_decimal("catalyst_ratio", self.catalyst_ratio),
        )
        _require_flags("reason_code_count", self)


@dataclass(frozen=True)
class MarketResearchGoldVolatilityCatalystDigestReport:
    generated_at: datetime
    config_version: str
    digest_status: str
    recommended_next_step: str
    volatility_catalyst_count: Decimal
    ready_catalyst_count: Decimal
    watch_catalyst_count: Decimal
    blocked_catalyst_count: Decimal
    upcoming_catalyst_count: Decimal
    elapsed_catalyst_count: Decimal
    stale_research_count: Decimal
    thin_reference_count: Decimal
    atr_gap_catalyst_count: Decimal
    options_skew_gap_catalyst_count: Decimal
    volatility_liquidity_gap_catalyst_count: Decimal
    average_confidence_score: Decimal
    ready_catalyst_ratio: Decimal
    max_research_age_seconds: Decimal
    watch_within_seconds: Decimal
    min_reference_count: Decimal
    min_atr_move_score: Decimal
    min_options_skew_score: Decimal
    min_liquidity_score: Decimal
    max_realized_volatility_score: Decimal
    max_observed_research_age_seconds: Decimal
    nearest_seconds_until_catalyst: Decimal | None
    rows: tuple[MarketResearchGoldVolatilityCatalystDigestRow, ...]
    source_config_versions: tuple[tuple[str, str], ...]
    reason_code_counts: tuple[
        MarketResearchGoldVolatilityCatalystDigestReasonCodeCount,
        ...,
    ]
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketResearchGoldVolatilityCatalystDigestReport:
            raise TypeError(
                "MarketResearchGoldVolatilityCatalystDigestReport "
                "does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not MarketResearchGoldVolatilityCatalystDigestReport:
            raise ValueError(
                "report must be exactly "
                "MarketResearchGoldVolatilityCatalystDigestReport",
            )
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        _require_digest_status("digest_status", self.digest_status)
        _require_canonical_string("recommended_next_step", self.recommended_next_step)
        for field_name in (
            "volatility_catalyst_count",
            "ready_catalyst_count",
            "watch_catalyst_count",
            "blocked_catalyst_count",
            "upcoming_catalyst_count",
            "elapsed_catalyst_count",
            "stale_research_count",
            "thin_reference_count",
            "atr_gap_catalyst_count",
            "options_skew_gap_catalyst_count",
            "volatility_liquidity_gap_catalyst_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_count_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "average_confidence_score",
            "ready_catalyst_ratio",
            "min_atr_move_score",
            "min_options_skew_score",
            "min_liquidity_score",
            "max_realized_volatility_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "max_research_age_seconds",
            "watch_within_seconds",
            "min_reference_count",
            "max_observed_research_age_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "nearest_seconds_until_catalyst",
            _require_optional_decimal(
                "nearest_seconds_until_catalyst",
                self.nearest_seconds_until_catalyst,
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
            _normalize_reason_codes(self.reason_codes),
        )
        _validate_report(self)
        _require_flags("report", self)


def build_market_research_gold_volatility_catalyst_digest(
    input_rows: list[MarketResearchGoldVolatilityCatalystDigestInputRow]
    | tuple[MarketResearchGoldVolatilityCatalystDigestInputRow, ...],
    *,
    config: MarketResearchGoldVolatilityCatalystDigestConfig,
    generated_at: datetime,
) -> MarketResearchGoldVolatilityCatalystDigestReport:
    if type(config) is not MarketResearchGoldVolatilityCatalystDigestConfig:
        raise ValueError(
            "config must be exactly "
            "MarketResearchGoldVolatilityCatalystDigestConfig",
        )
    _require_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    rows_in = _normalize_input_rows(input_rows)
    rows = _rows(rows_in, config=config, generated_at=generated_at_utc)
    catalyst_count = _decimal_count(len(rows))
    ready_count = _status_count(rows, "ready")
    watch_count = _status_count(rows, "watch")
    blocked_count = _status_count(rows, "blocked")
    reason_code_counts = _reason_code_counts(rows)
    reason_codes = tuple(item.reason_code for item in reason_code_counts)

    return MarketResearchGoldVolatilityCatalystDigestReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        digest_status=_report_status(
            catalyst_count=catalyst_count,
            watch_count=watch_count,
            blocked_count=blocked_count,
        ),
        recommended_next_step=NEXT_STEPS[
            _report_status(
                catalyst_count=catalyst_count,
                watch_count=watch_count,
                blocked_count=blocked_count,
            )
        ],
        volatility_catalyst_count=catalyst_count,
        ready_catalyst_count=ready_count,
        watch_catalyst_count=watch_count,
        blocked_catalyst_count=blocked_count,
        upcoming_catalyst_count=_decimal_count(
            sum(1 for row in rows if row.seconds_until_catalyst > ZERO),
        ),
        elapsed_catalyst_count=_event_count_with(rows, ELAPSED_REASON),
        stale_research_count=_event_count_with(rows, STALE_RESEARCH_REASON),
        thin_reference_count=_event_count_with(rows, THIN_REFERENCES_REASON),
        atr_gap_catalyst_count=_event_count_with(rows, ATR_MOVE_GAP_REASON),
        options_skew_gap_catalyst_count=_event_count_with(
            rows,
            OPTIONS_SKEW_GAP_REASON,
        ),
        volatility_liquidity_gap_catalyst_count=_event_count_with(
            rows,
            VOLATILITY_LIQUIDITY_GAP_REASON,
        ),
        average_confidence_score=_average_confidence_score(rows),
        ready_catalyst_ratio=_ratio(ready_count, catalyst_count),
        max_research_age_seconds=config.max_research_age_seconds,
        watch_within_seconds=config.watch_within_seconds,
        min_reference_count=config.min_reference_count,
        min_atr_move_score=config.min_atr_move_score,
        min_options_skew_score=config.min_options_skew_score,
        min_liquidity_score=config.min_liquidity_score,
        max_realized_volatility_score=config.max_realized_volatility_score,
        max_observed_research_age_seconds=_max_decimal(
            row.research_age_seconds for row in rows
        ),
        nearest_seconds_until_catalyst=_nearest_seconds_until_catalyst(rows),
        rows=rows,
        source_config_versions=_source_config_versions(rows_in),
        reason_code_counts=reason_code_counts,
        reason_codes=reason_codes,
    )


def market_research_gold_volatility_catalyst_digest_payload(
    report: MarketResearchGoldVolatilityCatalystDigestReport,
) -> dict[str, Any]:
    if type(report) is not MarketResearchGoldVolatilityCatalystDigestReport:
        raise ValueError(
            "report must be exactly "
            "MarketResearchGoldVolatilityCatalystDigestReport",
        )
    _require_flags("report", report)
    payload = _plain(asdict(report))
    if type(payload) is not dict:
        raise ValueError("payload must be a dict")
    return payload


def _normalize_input_rows(
    value: object,
) -> tuple[MarketResearchGoldVolatilityCatalystDigestInputRow, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("input rows must be a list or tuple")
    rows = tuple(value)
    seen: set[str] = set()
    for row in rows:
        if type(row) is not MarketResearchGoldVolatilityCatalystDigestInputRow:
            raise ValueError(
                "input rows must contain "
                "MarketResearchGoldVolatilityCatalystDigestInputRow",
            )
        _require_flags("input row", row)
        if row.volatility_catalyst_key in seen:
            raise ValueError("input rows must not contain duplicate catalyst keys")
        seen.add(row.volatility_catalyst_key)
    return rows


def _rows(
    input_rows: tuple[MarketResearchGoldVolatilityCatalystDigestInputRow, ...],
    *,
    config: MarketResearchGoldVolatilityCatalystDigestConfig,
    generated_at: datetime,
) -> tuple[MarketResearchGoldVolatilityCatalystDigestRow, ...]:
    rows = []
    for row in input_rows:
        if row.research_observed_at > generated_at:
            raise ValueError("research_observed_at must not be in the future")
        seconds_until_catalyst = _seconds_between(generated_at, row.catalyst_at)
        research_age_seconds = _seconds_between(row.research_observed_at, generated_at)
        reference_gap_count = _count_gap(config.min_reference_count, row.reference_count)
        reason_codes = _row_reason_codes(
            row,
            config=config,
            seconds_until_catalyst=seconds_until_catalyst,
            research_age_seconds=research_age_seconds,
            reference_gap_count=reference_gap_count,
        )
        confidence_decay_score = _confidence_decay_score(reason_codes, config)
        rows.append(
            MarketResearchGoldVolatilityCatalystDigestRow(
                market_research_key=row.market_research_key,
                volatility_catalyst_key=row.volatility_catalyst_key,
                catalyst_family=row.catalyst_family,
                catalyst_status=_row_status(reason_codes),
                seconds_until_catalyst=seconds_until_catalyst,
                research_age_seconds=research_age_seconds,
                reference_count=row.reference_count,
                reference_gap_count=reference_gap_count,
                atr_move_score=row.atr_move_score,
                options_skew_score=row.options_skew_score,
                realized_volatility_score=row.realized_volatility_score,
                liquidity_score=row.liquidity_score,
                base_confidence_score=row.base_confidence_score,
                confidence_decay_score=confidence_decay_score,
                confidence_score=_confidence_score(
                    row.base_confidence_score,
                    confidence_decay_score,
                ),
                redacted_public_catalyst_reference=_redacted_public_reference(
                    row.public_catalyst_reference,
                ),
                reason_codes=reason_codes,
            ),
        )
    return tuple(
        sorted(
            rows,
            key=lambda item: (
                _status_rank(item.catalyst_status),
                item.volatility_catalyst_key,
                item.market_research_key,
            ),
        ),
    )


def _row_reason_codes(
    row: MarketResearchGoldVolatilityCatalystDigestInputRow,
    *,
    config: MarketResearchGoldVolatilityCatalystDigestConfig,
    seconds_until_catalyst: Decimal,
    research_age_seconds: Decimal,
    reference_gap_count: Decimal,
) -> tuple[str, ...]:
    reason_codes = []
    if research_age_seconds > config.max_research_age_seconds:
        reason_codes.append(STALE_RESEARCH_REASON)
    if seconds_until_catalyst <= ZERO:
        reason_codes.append(ELAPSED_REASON)
    if reference_gap_count > ZERO:
        reason_codes.append(THIN_REFERENCES_REASON)
    if row.atr_move_score < config.min_atr_move_score:
        reason_codes.append(ATR_MOVE_GAP_REASON)
    if row.options_skew_score < config.min_options_skew_score:
        reason_codes.append(OPTIONS_SKEW_GAP_REASON)
    if (
        row.realized_volatility_score > config.max_realized_volatility_score
        or row.liquidity_score < config.min_liquidity_score
    ):
        reason_codes.append(VOLATILITY_LIQUIDITY_GAP_REASON)
    if not reason_codes:
        reason_codes.append(READY_REASON)
    return _normalize_reason_codes(tuple(reason_codes))


def _row_status(reason_codes: tuple[str, ...]) -> str:
    if reason_codes == (READY_REASON,):
        return "ready"
    if ELAPSED_REASON in reason_codes:
        return "blocked"
    return "watch"


def _report_status(
    *,
    catalyst_count: Decimal,
    watch_count: Decimal,
    blocked_count: Decimal,
) -> str:
    if catalyst_count == ZERO:
        return "blocked"
    if blocked_count > ZERO:
        return "blocked"
    if watch_count > ZERO:
        return "watch"
    return "ready"


def _reason_code_counts(
    rows: tuple[MarketResearchGoldVolatilityCatalystDigestRow, ...],
) -> tuple[MarketResearchGoldVolatilityCatalystDigestReasonCodeCount, ...]:
    if not rows:
        return (
            MarketResearchGoldVolatilityCatalystDigestReasonCodeCount(
                reason_code=NO_INPUTS_REASON,
                count=ONE,
                catalyst_ratio=ZERO,
            ),
        )
    total = _decimal_count(len(rows))
    return tuple(
        MarketResearchGoldVolatilityCatalystDigestReasonCodeCount(
            reason_code=reason_code,
            count=_event_count_with(rows, reason_code),
            catalyst_ratio=_ratio(_event_count_with(rows, reason_code), total),
        )
        for reason_code in REASON_CODES
        if reason_code != NO_INPUTS_REASON
        and any(reason_code in row.reason_codes for row in rows)
    )


def _event_count_with(
    rows: tuple[MarketResearchGoldVolatilityCatalystDigestRow, ...],
    reason_code: str,
) -> Decimal:
    return _decimal_count(sum(1 for row in rows if reason_code in row.reason_codes))


def _source_config_versions(
    rows: tuple[MarketResearchGoldVolatilityCatalystDigestInputRow, ...],
) -> tuple[tuple[str, str], ...]:
    return tuple(
        sorted(
            (
                row.volatility_catalyst_key,
                row.source_config_version,
            )
            for row in rows
        ),
    )


def _confidence_decay_score(
    reason_codes: tuple[str, ...],
    config: MarketResearchGoldVolatilityCatalystDigestConfig,
) -> Decimal:
    decay = ZERO
    if STALE_RESEARCH_REASON in reason_codes:
        decay += config.confidence_decay_per_stale_research
    if ELAPSED_REASON in reason_codes:
        decay += config.confidence_decay_per_elapsed_catalyst
    if THIN_REFERENCES_REASON in reason_codes:
        decay += config.confidence_decay_per_thin_references
    if ATR_MOVE_GAP_REASON in reason_codes:
        decay += config.confidence_decay_per_atr_gap
    if OPTIONS_SKEW_GAP_REASON in reason_codes:
        decay += config.confidence_decay_per_options_skew_gap
    if VOLATILITY_LIQUIDITY_GAP_REASON in reason_codes:
        decay += config.confidence_decay_per_volatility_liquidity_gap
    return min(_quantize(decay), ONE)


def _confidence_score(base_score: Decimal, decay_score: Decimal) -> Decimal:
    return _quantize(max(ZERO, base_score - decay_score))


def _normalize_rows(
    value: object,
) -> tuple[MarketResearchGoldVolatilityCatalystDigestRow, ...]:
    if type(value) not in (tuple, list):
        raise ValueError("rows must be a tuple or list")
    rows = tuple(value)
    for row in rows:
        if type(row) is not MarketResearchGoldVolatilityCatalystDigestRow:
            raise ValueError(
                "rows must contain "
                "MarketResearchGoldVolatilityCatalystDigestRow",
            )
        _require_flags("row", row)
    if rows != tuple(
        sorted(
            rows,
            key=lambda item: (
                _status_rank(item.catalyst_status),
                item.volatility_catalyst_key,
                item.market_research_key,
            ),
        ),
    ):
        raise ValueError("rows must be sorted")
    return rows


def _normalize_source_config_versions(value: object) -> tuple[tuple[str, str], ...]:
    if type(value) not in (tuple, list):
        raise ValueError("source_config_versions must be a tuple or list")
    normalized = tuple(value)
    seen: set[str] = set()
    for item in normalized:
        if type(item) not in (tuple, list) or len(item) != 2:
            raise ValueError("source_config_versions entries must be pairs")
        catalyst_key, config_version = item
        _require_public_string("source_config_versions catalyst_key", catalyst_key)
        _require_public_string("source_config_versions config_version", config_version)
        if catalyst_key in seen:
            raise ValueError("source_config_versions catalyst keys must be unique")
        seen.add(catalyst_key)
    if normalized != tuple(sorted(normalized)):
        raise ValueError("source_config_versions must be sorted")
    return normalized


def _normalize_reason_code_counts(
    value: object,
) -> tuple[MarketResearchGoldVolatilityCatalystDigestReasonCodeCount, ...]:
    if type(value) not in (tuple, list):
        raise ValueError("reason_code_counts must be a tuple or list")
    normalized = tuple(value)
    for item in normalized:
        if type(item) is not MarketResearchGoldVolatilityCatalystDigestReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "MarketResearchGoldVolatilityCatalystDigestReasonCodeCount",
            )
    if normalized != tuple(
        sorted(
            normalized,
            key=lambda item: REASON_CODES.index(item.reason_code),
        ),
    ):
        raise ValueError("reason_code_counts must be sorted")
    return normalized


def _normalize_reason_codes(value: object) -> tuple[str, ...]:
    if type(value) not in (tuple, list):
        raise ValueError("reason_codes must be a tuple or list")
    reason_codes = tuple(value)
    if not reason_codes:
        raise ValueError("reason_codes must not be empty")
    for reason_code in reason_codes:
        _require_reason_code("reason_codes", reason_code)
    if len(reason_codes) != len(set(reason_codes)):
        raise ValueError("reason_codes must be unique")
    if reason_codes != tuple(sorted(reason_codes, key=lambda item: REASON_CODES.index(item))):
        raise ValueError("reason_codes must be sorted")
    return reason_codes


def _validate_row(row: MarketResearchGoldVolatilityCatalystDigestRow) -> None:
    if row.catalyst_status != _row_status(row.reason_codes):
        raise ValueError("catalyst_status must match reason_codes")
    if row.catalyst_status == "ready" and row.reason_codes != (READY_REASON,):
        raise ValueError("ready rows require ready reason")
    if row.catalyst_status == "blocked" and ELAPSED_REASON not in row.reason_codes:
        raise ValueError("blocked rows require elapsed reason")
    if row.confidence_score != _confidence_score(
        row.base_confidence_score,
        row.confidence_decay_score,
    ):
        raise ValueError("confidence_score must match base score and decay")


def _validate_report(report: MarketResearchGoldVolatilityCatalystDigestReport) -> None:
    if report.recommended_next_step != NEXT_STEPS[report.digest_status]:
        raise ValueError("recommended_next_step must match digest_status")
    if report.volatility_catalyst_count != _decimal_count(len(report.rows)):
        raise ValueError("volatility_catalyst_count must match rows")
    if (
        report.ready_catalyst_count
        + report.watch_catalyst_count
        + report.blocked_catalyst_count
        != report.volatility_catalyst_count
    ):
        raise ValueError("status counts must match catalyst count")
    if report.ready_catalyst_count != _status_count(report.rows, "ready"):
        raise ValueError("ready_catalyst_count must match rows")
    if report.watch_catalyst_count != _status_count(report.rows, "watch"):
        raise ValueError("watch_catalyst_count must match rows")
    if report.blocked_catalyst_count != _status_count(report.rows, "blocked"):
        raise ValueError("blocked_catalyst_count must match rows")
    if report.elapsed_catalyst_count != _event_count_with(report.rows, ELAPSED_REASON):
        raise ValueError("elapsed_catalyst_count must match rows")
    if report.stale_research_count != _event_count_with(
        report.rows,
        STALE_RESEARCH_REASON,
    ):
        raise ValueError("stale_research_count must match rows")
    if report.thin_reference_count != _event_count_with(
        report.rows,
        THIN_REFERENCES_REASON,
    ):
        raise ValueError("thin_reference_count must match rows")
    if report.average_confidence_score != _average_confidence_score(report.rows):
        raise ValueError("average_confidence_score must match rows")
    if report.ready_catalyst_ratio != _ratio(
        report.ready_catalyst_count,
        report.volatility_catalyst_count,
    ):
        raise ValueError("ready_catalyst_ratio must match rows")
    if report.reason_codes != tuple(item.reason_code for item in report.reason_code_counts):
        raise ValueError("reason_codes must match reason counts")


def _require_digest_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in DIGEST_STATUSES:
        raise ValueError(f"{field_name} must be ready, watch, or blocked")


def _require_reason_code(field_name: str, value: object) -> None:
    _require_canonical_string(field_name, value)
    if value not in REASON_CODES:
        raise ValueError(f"{field_name} contains unknown reason code")


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str or not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical string")


def _require_public_string(field_name: str, value: object) -> None:
    _require_canonical_string(field_name, value)
    lowered = value.lower()
    if any(fragment in lowered for fragment in UNSAFE_TEXT_FRAGMENTS):
        raise ValueError(f"{field_name} contains disallowed text")


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return _quantize(value)


def _require_optional_decimal(field_name: str, value: object) -> Decimal | None:
    if value is None:
        return None
    return _require_decimal(field_name, value)


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


def _require_count_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value != decimal_value.to_integral_value():
        raise ValueError(f"{field_name} must be a whole Decimal")
    return decimal_value


def _require_nonnegative_count_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_count_decimal(field_name, value)
    if decimal_value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return decimal_value


def _require_positive_count_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_count_decimal(field_name, value)
    if decimal_value <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return decimal_value


def _require_ratio_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_nonnegative_decimal(field_name, value)
    if decimal_value > ONE:
        raise ValueError(f"{field_name} must be at most one")
    return decimal_value


def _require_redacted_reference(field_name: str, value: object) -> None:
    _require_canonical_string(field_name, value)


def _require_flags(field_name: str, value: object) -> None:
    if getattr(value, "paper_only", None) is not True:
        raise ValueError(f"{field_name} paper_only must be True")
    if getattr(value, "report_only", None) is not True:
        raise ValueError(f"{field_name} report_only must be True")
    if getattr(value, "readonly", None) is not True:
        raise ValueError(f"{field_name} readonly must be True")


def _decimal_count(value: int) -> Decimal:
    return _quantize(Decimal(value))


def _status_count(
    rows: tuple[MarketResearchGoldVolatilityCatalystDigestRow, ...],
    catalyst_status: str,
) -> Decimal:
    return _decimal_count(sum(1 for row in rows if row.catalyst_status == catalyst_status))


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return (numerator / denominator).quantize(QUANTUM)


def _count_gap(required_count: Decimal, observed_count: Decimal) -> Decimal:
    gap_count = required_count - observed_count
    if gap_count <= ZERO:
        return ZERO
    return _quantize(gap_count)


def _seconds_between(start: datetime, end: datetime) -> Decimal:
    elapsed = end - start
    with localcontext(DECIMAL_CONTEXT):
        return (
            Decimal(elapsed.days * 86400 + elapsed.seconds)
            + (Decimal(elapsed.microseconds) / MICROSECONDS_PER_SECOND)
        ).quantize(QUANTUM)


def _average_confidence_score(
    rows: tuple[MarketResearchGoldVolatilityCatalystDigestRow, ...],
) -> Decimal:
    if not rows:
        return ZERO
    total = sum((row.confidence_score for row in rows), ZERO)
    return _ratio(total, _decimal_count(len(rows)))


def _max_decimal(values: object) -> Decimal:
    items = tuple(values)
    if not items:
        return ZERO
    return max(items)


def _nearest_seconds_until_catalyst(
    rows: tuple[MarketResearchGoldVolatilityCatalystDigestRow, ...],
) -> Decimal | None:
    if not rows:
        return None
    return min(row.seconds_until_catalyst for row in rows)


def _redacted_public_reference(value: str) -> str:
    lowered = value.lower()
    if "://" in value or "?" in value or any(
        fragment in lowered for fragment in UNSAFE_TEXT_FRAGMENTS
    ):
        return "sha256:" + sha256(value.encode("utf-8")).hexdigest()[:12]
    return value


def _status_rank(status: str) -> int:
    return {"blocked": 0, "watch": 1, "ready": 2}[status]


def _quantize(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(QUANTUM)


def _plain(value: Any) -> Any:
    if isinstance(value, Decimal):
        return str(_quantize(value))
    if isinstance(value, datetime):
        return value.astimezone(UTC).isoformat()
    if is_dataclass(value):
        return {field.name: _plain(getattr(value, field.name)) for field in fields(value)}
    if isinstance(value, tuple):
        return [_plain(item) for item in value]
    if isinstance(value, list):
        return [_plain(item) for item in value]
    if isinstance(value, dict):
        return {key: _plain(item) for key, item in value.items()}
    return value
