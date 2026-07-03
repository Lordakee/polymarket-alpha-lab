"""Pure in-memory equity-index source reliability digest."""

from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass, fields, is_dataclass
from datetime import UTC, datetime, timedelta
from decimal import Decimal, InvalidOperation, localcontext
from typing import Any


ZERO = Decimal("0")
ONE = Decimal("1")
COUNT_QUANT = Decimal("1")
RATIO_QUANT = Decimal("0.000001")
SECONDS_PER_DAY = Decimal("86400")
MICROSECONDS_PER_SECOND = Decimal("1000000")
DEFAULT_MARKET_RESEARCH_EQUITY_INDEX_SOURCE_RELIABILITY_DIGEST_CONFIG_VERSION = (
    "market-research-equity-index-source-reliability-digest-v0"
)

RELIABILITY_STATUSES = ("pass", "watch", "blocked")

ROW_REASON_CODES = (
    "market_research_equity_index_source_reliability_digest_row_macro_calendar_stale",
    "market_research_equity_index_source_reliability_digest_row_low_earnings_breadth",
    "market_research_equity_index_source_reliability_digest_row_missing_index_confirmation",
    "market_research_equity_index_source_reliability_digest_row_missing_futures_confirmation",
    "market_research_equity_index_source_reliability_digest_row_high_volatility_regime",
    "market_research_equity_index_source_reliability_digest_row_low_source_family_diversity",
    "market_research_equity_index_source_reliability_digest_row_high_contradiction_rate",
    "market_research_equity_index_source_reliability_digest_row_slow_acknowledgement",
    "market_research_equity_index_source_reliability_digest_row_passed",
)

REPORT_REASON_CODES = (
    "market_research_equity_index_source_reliability_digest_empty",
    "market_research_equity_index_source_reliability_digest_macro_calendar_stale",
    "market_research_equity_index_source_reliability_digest_low_earnings_breadth",
    "market_research_equity_index_source_reliability_digest_missing_index_confirmation",
    "market_research_equity_index_source_reliability_digest_missing_futures_confirmation",
    "market_research_equity_index_source_reliability_digest_high_volatility_regime",
    "market_research_equity_index_source_reliability_digest_low_source_family_diversity",
    "market_research_equity_index_source_reliability_digest_high_contradiction_rate",
    "market_research_equity_index_source_reliability_digest_slow_acknowledgement",
    "market_research_equity_index_source_reliability_digest_passed",
)

_ROW_PENALTIES = {
    "market_research_equity_index_source_reliability_digest_row_macro_calendar_stale": Decimal(
        "0.180000",
    ),
    "market_research_equity_index_source_reliability_digest_row_low_earnings_breadth": Decimal(
        "0.100000",
    ),
    "market_research_equity_index_source_reliability_digest_row_missing_index_confirmation": Decimal(
        "0.150000",
    ),
    "market_research_equity_index_source_reliability_digest_row_missing_futures_confirmation": Decimal(
        "0.100000",
    ),
    "market_research_equity_index_source_reliability_digest_row_high_volatility_regime": Decimal(
        "0.120000",
    ),
    "market_research_equity_index_source_reliability_digest_row_low_source_family_diversity": Decimal(
        "0.100000",
    ),
    "market_research_equity_index_source_reliability_digest_row_high_contradiction_rate": Decimal(
        "0.300000",
    ),
    "market_research_equity_index_source_reliability_digest_row_slow_acknowledgement": Decimal(
        "0.100000",
    ),
}

_BLOCKED_IDENTIFIER_FRAGMENTS = (
    "0x",
    "@",
    "acc" "ount",
    "api" "_" "key",
    "au" "th",
    "bro" "ker",
    "can" "cel",
    "email",
    "live" "_" "trading",
    "ord" "er",
    "place" "_" "ord" "er",
    "pri" "vate",
    "pri" "vate" "_" "key",
    "se" "cret",
    "sig" "n",
    "sub" "mit",
    "token",
    "tra" "ding" "_" "advice",
    "wal" "let",
    "web" "3",
)

_PAYLOAD_OMIT_FIELDS = {
    "event_id",
    "index_symbol",
}


__all__ = (
    "DEFAULT_MARKET_RESEARCH_EQUITY_INDEX_SOURCE_RELIABILITY_DIGEST_CONFIG_VERSION",
    "MarketResearchEquityIndexSourceReliabilityDigestConfig",
    "MarketResearchEquityIndexSourceReliabilityObservation",
    "MarketResearchEquityIndexSourceReliabilityReasonCodeCount",
    "MarketResearchEquityIndexSourceReliabilityReport",
    "MarketResearchEquityIndexSourceReliabilityRow",
    "build_market_research_equity_index_source_reliability_digest",
    "market_research_equity_index_source_reliability_digest_payload",
)


@dataclass(frozen=True)
class MarketResearchEquityIndexSourceReliabilityDigestConfig:
    config_version: str = (
        DEFAULT_MARKET_RESEARCH_EQUITY_INDEX_SOURCE_RELIABILITY_DIGEST_CONFIG_VERSION
    )
    max_macro_calendar_age_seconds: Decimal = Decimal("7200.000000")
    min_earnings_source_count: Decimal = Decimal("2")
    min_index_confirmation_count: Decimal = Decimal("1")
    min_futures_confirmation_count: Decimal = Decimal("1")
    max_volatility_regime_score: Decimal = Decimal("0.700000")
    min_source_family_diversity_ratio: Decimal = Decimal("0.500000")
    max_contradiction_rate: Decimal = Decimal("0.250000")
    max_acknowledgement_lag_seconds: Decimal = Decimal("3600.000000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("config_version", self.config_version)
        object.__setattr__(
            self,
            "max_macro_calendar_age_seconds",
            _normalize_nonnegative_decimal(
                "max_macro_calendar_age_seconds",
                self.max_macro_calendar_age_seconds,
            ),
        )
        if self.max_macro_calendar_age_seconds <= ZERO:
            raise ValueError("max_macro_calendar_age_seconds must be positive")
        for field_name in (
            "min_earnings_source_count",
            "min_index_confirmation_count",
            "min_futures_confirmation_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_integral_decimal(
                    field_name,
                    getattr(self, field_name),
                ),
            )
        for field_name in (
            "max_volatility_regime_score",
            "min_source_family_diversity_ratio",
            "max_contradiction_rate",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "max_acknowledgement_lag_seconds",
            _normalize_nonnegative_decimal(
                "max_acknowledgement_lag_seconds",
                self.max_acknowledgement_lag_seconds,
            ),
        )
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class MarketResearchEquityIndexSourceReliabilityObservation:
    event_id: str
    index_symbol: str
    source_ref: str
    source_family: str
    observed_at: datetime
    macro_calendar_published_at: datetime
    resolved_at: datetime
    acknowledged_at: datetime
    earnings_source_count: Decimal
    index_confirmation_count: Decimal
    futures_confirmation_count: Decimal
    volatility_regime_score: Decimal
    contradiction_count: Decimal = ZERO
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        for field_name in ("event_id", "index_symbol", "source_ref", "source_family"):
            _require_canonical_string(field_name, getattr(self, field_name))
        _require_redacted_identifier("source_ref", self.source_ref)
        for field_name in (
            "observed_at",
            "macro_calendar_published_at",
            "resolved_at",
            "acknowledged_at",
        ):
            object.__setattr__(
                self,
                field_name,
                _as_utc(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "earnings_source_count",
            "index_confirmation_count",
            "futures_confirmation_count",
            "contradiction_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_integral_decimal(
                    field_name,
                    getattr(self, field_name),
                ),
            )
        object.__setattr__(
            self,
            "volatility_regime_score",
            _normalize_ratio("volatility_regime_score", self.volatility_regime_score),
        )
        _require_hard_flags("observation", self)


@dataclass(frozen=True)
class MarketResearchEquityIndexSourceReliabilityRow:
    event_id: str
    index_symbol: str
    source_count: Decimal
    source_family_count: Decimal
    macro_calendar_freshness_age_seconds: Decimal
    earnings_source_count: Decimal
    index_confirmation_count: Decimal
    futures_confirmation_count: Decimal
    confirmation_count: Decimal
    volatility_regime_score: Decimal
    source_family_diversity_ratio: Decimal
    contradiction_count: Decimal
    contradiction_rate: Decimal
    acknowledgement_lag_seconds: Decimal
    reliability_score: Decimal
    reliability_status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        for field_name in ("event_id", "index_symbol"):
            _require_canonical_string(field_name, getattr(self, field_name))
        for field_name in (
            "source_count",
            "source_family_count",
            "earnings_source_count",
            "index_confirmation_count",
            "futures_confirmation_count",
            "confirmation_count",
            "contradiction_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_integral_decimal(
                    field_name,
                    getattr(self, field_name),
                ),
            )
        for field_name in (
            "macro_calendar_freshness_age_seconds",
            "acknowledgement_lag_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "volatility_regime_score",
            "source_family_diversity_ratio",
            "contradiction_rate",
            "reliability_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        _require_reliability_status("reliability_status", self.reliability_status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, ROW_REASON_CODES),
        )
        _require_hard_flags("row", self)
        _validate_row(self)


@dataclass(frozen=True)
class MarketResearchEquityIndexSourceReliabilityReasonCodeCount:
    reason_code: str
    count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self.reason_code) is not str or self.reason_code not in REPORT_REASON_CODES:
            raise ValueError("reason_code must be a known report reason code")
        object.__setattr__(
            self,
            "count",
            _normalize_nonnegative_integral_decimal("count", self.count),
        )
        if self.count <= ZERO:
            raise ValueError("count must be positive")
        _require_hard_flags("reason_code_count", self)


@dataclass(frozen=True)
class MarketResearchEquityIndexSourceReliabilityReport:
    generated_at: datetime
    config_version: str
    reliability_status: str
    event_count: Decimal
    source_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    blocked_count: Decimal
    macro_calendar_freshness_age_seconds: Decimal
    average_earnings_source_count: Decimal
    average_confirmation_count: Decimal
    max_volatility_regime_score: Decimal
    source_family_diversity_ratio: Decimal
    contradiction_count: Decimal
    contradiction_rate: Decimal
    acknowledgement_lag_seconds: Decimal
    rows: tuple[MarketResearchEquityIndexSourceReliabilityRow, ...]
    reason_code_counts: tuple[
        MarketResearchEquityIndexSourceReliabilityReasonCodeCount,
        ...
    ]
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        _require_reliability_status("reliability_status", self.reliability_status)
        for field_name in (
            "event_count",
            "source_count",
            "pass_count",
            "watch_count",
            "blocked_count",
            "contradiction_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_integral_decimal(
                    field_name,
                    getattr(self, field_name),
                ),
            )
        for field_name in (
            "macro_calendar_freshness_age_seconds",
            "average_earnings_source_count",
            "average_confirmation_count",
            "acknowledgement_lag_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "max_volatility_regime_score",
            "source_family_diversity_ratio",
            "contradiction_rate",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
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
            _normalize_reason_codes(
                "reason_codes",
                self.reason_codes,
                REPORT_REASON_CODES,
            ),
        )
        _require_hard_flags("report", self)
        _validate_report(self)


def build_market_research_equity_index_source_reliability_digest(
    observations: tuple[MarketResearchEquityIndexSourceReliabilityObservation, ...],
    *,
    config: MarketResearchEquityIndexSourceReliabilityDigestConfig,
    generated_at: datetime,
) -> MarketResearchEquityIndexSourceReliabilityReport:
    if type(config) is not MarketResearchEquityIndexSourceReliabilityDigestConfig:
        raise ValueError(
            "config must be a MarketResearchEquityIndexSourceReliabilityDigestConfig",
        )
    _require_hard_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    rows_input = _normalize_observations(observations, generated_at=generated_at_utc)
    reliability_rows = _build_rows(
        rows_input,
        config=config,
        generated_at=generated_at_utc,
    )
    reason_codes = _report_reason_codes(reliability_rows)
    return MarketResearchEquityIndexSourceReliabilityReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        reliability_status=_status_from_reason_codes(reason_codes),
        event_count=_count(len(reliability_rows)),
        source_count=_count(len(rows_input)),
        pass_count=_count(
            sum(1 for row in reliability_rows if row.reliability_status == "pass"),
        ),
        watch_count=_count(
            sum(1 for row in reliability_rows if row.reliability_status == "watch"),
        ),
        blocked_count=_count(
            sum(1 for row in reliability_rows if row.reliability_status == "blocked"),
        ),
        macro_calendar_freshness_age_seconds=_max_row_decimal(
            reliability_rows,
            "macro_calendar_freshness_age_seconds",
        ),
        average_earnings_source_count=_average_row_decimal(
            reliability_rows,
            "earnings_source_count",
        ),
        average_confirmation_count=_average_confirmation_count(reliability_rows),
        max_volatility_regime_score=_max_row_decimal(
            reliability_rows,
            "volatility_regime_score",
        ),
        source_family_diversity_ratio=_source_family_diversity_ratio(rows_input),
        contradiction_count=sum(
            (row.contradiction_count for row in rows_input),
            ZERO,
        ).quantize(COUNT_QUANT),
        contradiction_rate=_ratio(
            sum((row.contradiction_count for row in rows_input), ZERO),
            _count(len(rows_input)),
        ),
        acknowledgement_lag_seconds=_max_row_decimal(
            reliability_rows,
            "acknowledgement_lag_seconds",
        ),
        rows=reliability_rows,
        reason_code_counts=_reason_code_counts(reason_codes),
        reason_codes=reason_codes,
    )


def market_research_equity_index_source_reliability_digest_payload(
    report: MarketResearchEquityIndexSourceReliabilityReport,
) -> dict[str, Any]:
    if type(report) is not MarketResearchEquityIndexSourceReliabilityReport:
        raise ValueError(
            "report must be a MarketResearchEquityIndexSourceReliabilityReport",
        )
    _require_hard_flags("report", report)
    return _payload_value(report, _RedactionMap())


def _build_rows(
    observations: tuple[MarketResearchEquityIndexSourceReliabilityObservation, ...],
    *,
    config: MarketResearchEquityIndexSourceReliabilityDigestConfig,
    generated_at: datetime,
) -> tuple[MarketResearchEquityIndexSourceReliabilityRow, ...]:
    groups: dict[tuple[str, str], list[MarketResearchEquityIndexSourceReliabilityObservation]]
    groups = defaultdict(list)
    for observation in observations:
        groups[(observation.event_id, observation.index_symbol)].append(observation)

    rows: list[MarketResearchEquityIndexSourceReliabilityRow] = []
    for (event_id, index_symbol), group_rows in sorted(groups.items()):
        event_rows = tuple(group_rows)
        source_refs = {row.source_ref for row in event_rows}
        source_families = {row.source_family for row in event_rows}
        source_count = _count(len(source_refs))
        source_family_count = _count(len(source_families))
        earnings_source_count = sum(
            (row.earnings_source_count for row in event_rows),
            ZERO,
        ).quantize(COUNT_QUANT)
        index_confirmation_count = sum(
            (row.index_confirmation_count for row in event_rows),
            ZERO,
        ).quantize(COUNT_QUANT)
        futures_confirmation_count = sum(
            (row.futures_confirmation_count for row in event_rows),
            ZERO,
        ).quantize(COUNT_QUANT)
        confirmation_count = (
            index_confirmation_count + futures_confirmation_count
        ).quantize(COUNT_QUANT)
        contradiction_count = sum(
            (row.contradiction_count for row in event_rows),
            ZERO,
        ).quantize(COUNT_QUANT)
        row_values = {
            "macro_calendar_freshness_age_seconds": _max_macro_calendar_age_seconds(
                event_rows,
                generated_at,
            ),
            "volatility_regime_score": max(
                (row.volatility_regime_score for row in event_rows),
                default=ZERO,
            ).quantize(RATIO_QUANT),
            "source_family_diversity_ratio": _ratio(
                source_family_count,
                source_count,
            ),
            "contradiction_rate": _ratio(contradiction_count, source_count),
            "acknowledgement_lag_seconds": _max_ack_lag_seconds(
                event_rows,
                generated_at,
            ),
        }
        reason_codes = _row_reason_codes(
            macro_calendar_freshness_age_seconds=row_values[
                "macro_calendar_freshness_age_seconds"
            ],
            earnings_source_count=earnings_source_count,
            index_confirmation_count=index_confirmation_count,
            futures_confirmation_count=futures_confirmation_count,
            volatility_regime_score=row_values["volatility_regime_score"],
            source_family_diversity_ratio=row_values["source_family_diversity_ratio"],
            contradiction_rate=row_values["contradiction_rate"],
            acknowledgement_lag_seconds=row_values["acknowledgement_lag_seconds"],
            config=config,
        )
        rows.append(
            MarketResearchEquityIndexSourceReliabilityRow(
                event_id=event_id,
                index_symbol=index_symbol,
                source_count=source_count,
                source_family_count=source_family_count,
                macro_calendar_freshness_age_seconds=row_values[
                    "macro_calendar_freshness_age_seconds"
                ],
                earnings_source_count=earnings_source_count,
                index_confirmation_count=index_confirmation_count,
                futures_confirmation_count=futures_confirmation_count,
                confirmation_count=confirmation_count,
                volatility_regime_score=row_values["volatility_regime_score"],
                source_family_diversity_ratio=row_values[
                    "source_family_diversity_ratio"
                ],
                contradiction_count=contradiction_count,
                contradiction_rate=row_values["contradiction_rate"],
                acknowledgement_lag_seconds=row_values["acknowledgement_lag_seconds"],
                reliability_score=_reliability_score(reason_codes),
                reliability_status=_status_from_reason_codes(reason_codes),
                reason_codes=reason_codes,
            ),
        )
    return tuple(
        sorted(
            rows,
            key=lambda row: (
                {"blocked": 0, "watch": 1, "pass": 2}[row.reliability_status],
                row.event_id,
                row.index_symbol,
            ),
        ),
    )


def _row_reason_codes(
    *,
    macro_calendar_freshness_age_seconds: Decimal,
    earnings_source_count: Decimal,
    index_confirmation_count: Decimal,
    futures_confirmation_count: Decimal,
    volatility_regime_score: Decimal,
    source_family_diversity_ratio: Decimal,
    contradiction_rate: Decimal,
    acknowledgement_lag_seconds: Decimal,
    config: MarketResearchEquityIndexSourceReliabilityDigestConfig,
) -> tuple[str, ...]:
    reasons: list[str] = []
    if macro_calendar_freshness_age_seconds > config.max_macro_calendar_age_seconds:
        reasons.append(
            "market_research_equity_index_source_reliability_digest_row_macro_calendar_stale",
        )
    if earnings_source_count <= config.min_earnings_source_count:
        reasons.append(
            "market_research_equity_index_source_reliability_digest_row_low_earnings_breadth",
        )
    if index_confirmation_count < config.min_index_confirmation_count:
        reasons.append(
            "market_research_equity_index_source_reliability_digest_row_missing_index_confirmation",
        )
    if futures_confirmation_count < config.min_futures_confirmation_count:
        reasons.append(
            "market_research_equity_index_source_reliability_digest_row_missing_futures_confirmation",
        )
    if volatility_regime_score > config.max_volatility_regime_score:
        reasons.append(
            "market_research_equity_index_source_reliability_digest_row_high_volatility_regime",
        )
    if source_family_diversity_ratio < config.min_source_family_diversity_ratio:
        reasons.append(
            "market_research_equity_index_source_reliability_digest_row_low_source_family_diversity",
        )
    if contradiction_rate > config.max_contradiction_rate:
        reasons.append(
            "market_research_equity_index_source_reliability_digest_row_high_contradiction_rate",
        )
    if acknowledgement_lag_seconds > config.max_acknowledgement_lag_seconds:
        reasons.append(
            "market_research_equity_index_source_reliability_digest_row_slow_acknowledgement",
        )
    return tuple(
        reasons
        or ("market_research_equity_index_source_reliability_digest_row_passed",)
    )


def _reliability_score(reason_codes: tuple[str, ...]) -> Decimal:
    if reason_codes == (
        "market_research_equity_index_source_reliability_digest_row_passed",
    ):
        return ONE.quantize(RATIO_QUANT)
    penalty = sum((_ROW_PENALTIES[reason] for reason in reason_codes), ZERO)
    score = max(ZERO, ONE - penalty)
    return score.quantize(RATIO_QUANT)


def _report_reason_codes(
    rows: tuple[MarketResearchEquityIndexSourceReliabilityRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return ("market_research_equity_index_source_reliability_digest_empty",)
    observed: set[str] = set()
    for row in rows:
        for reason_code in row.reason_codes:
            if reason_code.endswith("_row_passed"):
                continue
            observed.add(reason_code.replace("_row", ""))
    if not observed:
        return ("market_research_equity_index_source_reliability_digest_passed",)
    return tuple(reason_code for reason_code in REPORT_REASON_CODES if reason_code in observed)


def _reason_code_counts(
    reason_codes: tuple[str, ...],
) -> tuple[MarketResearchEquityIndexSourceReliabilityReasonCodeCount, ...]:
    counts = Counter(reason_codes)
    return tuple(
        MarketResearchEquityIndexSourceReliabilityReasonCodeCount(
            reason_code=reason_code,
            count=_count(count),
        )
        for reason_code, count in sorted(counts.items(), key=lambda item: (-item[1], item[0]))
    )


def _status_from_reason_codes(reason_codes: tuple[str, ...]) -> str:
    if (
        "market_research_equity_index_source_reliability_digest_empty" in reason_codes
        or any("high_contradiction_rate" in reason_code for reason_code in reason_codes)
    ):
        return "blocked"
    if reason_codes in (
        ("market_research_equity_index_source_reliability_digest_passed",),
        ("market_research_equity_index_source_reliability_digest_row_passed",),
    ):
        return "pass"
    return "watch"


def _max_macro_calendar_age_seconds(
    observations: tuple[MarketResearchEquityIndexSourceReliabilityObservation, ...],
    generated_at: datetime,
) -> Decimal:
    if not observations:
        return ZERO.quantize(RATIO_QUANT)
    max_age = max(
        _timedelta_seconds(generated_at - row.macro_calendar_published_at)
        for row in observations
    )
    return max(max_age, ZERO).quantize(RATIO_QUANT)


def _max_ack_lag_seconds(
    observations: tuple[MarketResearchEquityIndexSourceReliabilityObservation, ...],
    generated_at: datetime,
) -> Decimal:
    if not observations:
        return ZERO.quantize(RATIO_QUANT)
    max_lag = max(
        max(
            _timedelta_seconds(generated_at - row.acknowledged_at),
            _timedelta_seconds(row.acknowledged_at - row.resolved_at),
        )
        for row in observations
    )
    return max(max_lag, ZERO).quantize(RATIO_QUANT)


def _source_family_diversity_ratio(
    observations: tuple[MarketResearchEquityIndexSourceReliabilityObservation, ...],
) -> Decimal:
    if not observations:
        return ZERO.quantize(RATIO_QUANT)
    groups: dict[tuple[str, str], list[MarketResearchEquityIndexSourceReliabilityObservation]]
    groups = defaultdict(list)
    for observation in observations:
        groups[(observation.event_id, observation.index_symbol)].append(observation)
    ratios = tuple(
        _ratio(
            _count(len({row.source_family for row in group_rows})),
            _count(len({row.source_ref for row in group_rows})),
        )
        for group_rows in groups.values()
    )
    return min(ratios).quantize(RATIO_QUANT)


def _average_row_decimal(
    rows: tuple[MarketResearchEquityIndexSourceReliabilityRow, ...],
    field_name: str,
) -> Decimal:
    if not rows:
        return ZERO.quantize(RATIO_QUANT)
    total = sum((getattr(row, field_name) for row in rows), ZERO)
    return _ratio(total, _count(len(rows)))


def _average_confirmation_count(
    rows: tuple[MarketResearchEquityIndexSourceReliabilityRow, ...],
) -> Decimal:
    if not rows:
        return ZERO.quantize(RATIO_QUANT)
    per_event = tuple(_ratio(row.confirmation_count, row.source_count) for row in rows)
    return _ratio(sum(per_event, ZERO), _count(len(per_event)))


def _max_row_decimal(
    rows: tuple[MarketResearchEquityIndexSourceReliabilityRow, ...],
    field_name: str,
) -> Decimal:
    if not rows:
        return ZERO.quantize(RATIO_QUANT)
    return max((getattr(row, field_name) for row in rows), default=ZERO).quantize(
        RATIO_QUANT,
    )


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO:
        return ZERO.quantize(RATIO_QUANT)
    with localcontext() as context:
        context.prec = 28
        return (numerator / denominator).quantize(RATIO_QUANT)


def _timedelta_seconds(value: timedelta) -> Decimal:
    with localcontext() as context:
        context.prec = 28
        total_microseconds = (
            (Decimal(value.days) * SECONDS_PER_DAY * MICROSECONDS_PER_SECOND)
            + (Decimal(value.seconds) * MICROSECONDS_PER_SECOND)
            + Decimal(value.microseconds)
        )
        return (total_microseconds / MICROSECONDS_PER_SECOND).quantize(RATIO_QUANT)


def _count(value: int) -> Decimal:
    return Decimal(value).quantize(COUNT_QUANT)


def _normalize_observations(
    observations: object,
    *,
    generated_at: datetime,
) -> tuple[MarketResearchEquityIndexSourceReliabilityObservation, ...]:
    if type(observations) not in (list, tuple):
        raise ValueError("observations must be a list or tuple")
    normalized = tuple(observations)
    seen: set[tuple[str, str, str]] = set()
    for observation in normalized:
        if type(observation) is not MarketResearchEquityIndexSourceReliabilityObservation:
            raise ValueError(
                "observations must contain "
                "MarketResearchEquityIndexSourceReliabilityObservation values",
            )
        _require_hard_flags("observation", observation)
        key = (observation.event_id, observation.index_symbol, observation.source_ref)
        if key in seen:
            raise ValueError("source_ref values must be unique per event and index")
        seen.add(key)
        for field_name in (
            "observed_at",
            "macro_calendar_published_at",
            "resolved_at",
            "acknowledged_at",
        ):
            if getattr(observation, field_name) > generated_at:
                raise ValueError(f"{field_name} must not be in the future")
    return tuple(
        sorted(
            normalized,
            key=lambda row: (
                row.event_id,
                row.index_symbol,
                row.source_family,
                row.source_ref,
            ),
        ),
    )


def _normalize_rows(
    value: object,
) -> tuple[MarketResearchEquityIndexSourceReliabilityRow, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("rows must be a list or tuple")
    rows = tuple(value)
    keys: set[tuple[str, str]] = set()
    previous_key: tuple[int, str, str] | None = None
    status_weight = {"blocked": 0, "watch": 1, "pass": 2}
    for row in rows:
        if type(row) is not MarketResearchEquityIndexSourceReliabilityRow:
            raise ValueError(
                "rows must contain MarketResearchEquityIndexSourceReliabilityRow values",
            )
        _require_hard_flags("row", row)
        row_key = (row.event_id, row.index_symbol)
        if row_key in keys:
            raise ValueError("rows event_id and index_symbol values must be unique")
        key = (status_weight[row.reliability_status], row.event_id, row.index_symbol)
        if previous_key is not None and previous_key > key:
            raise ValueError("rows must use deterministic ordering")
        previous_key = key
        keys.add(row_key)
    return rows


def _normalize_reason_code_counts(
    value: object,
) -> tuple[MarketResearchEquityIndexSourceReliabilityReasonCodeCount, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("reason_code_counts must be a list or tuple")
    counts = tuple(value)
    seen: set[str] = set()
    previous_key: tuple[Decimal, str] | None = None
    for row in counts:
        if type(row) is not MarketResearchEquityIndexSourceReliabilityReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "MarketResearchEquityIndexSourceReliabilityReasonCodeCount values",
            )
        _require_hard_flags("reason_code_count", row)
        if row.reason_code in seen:
            raise ValueError("reason_code_counts must be unique")
        key = (-row.count, row.reason_code)
        if previous_key is not None and previous_key > key:
            raise ValueError("reason_code_counts must use deterministic ordering")
        previous_key = key
        seen.add(row.reason_code)
    return counts


def _normalize_reason_codes(
    field_name: str,
    value: object,
    allowed_reason_codes: tuple[str, ...],
) -> tuple[str, ...]:
    if type(value) not in (list, tuple):
        raise ValueError(f"{field_name} must be a list or tuple")
    reason_codes = tuple(value)
    if not reason_codes:
        raise ValueError(f"{field_name} must not be empty")
    for reason_code in reason_codes:
        if type(reason_code) is not str or reason_code not in allowed_reason_codes:
            raise ValueError(f"{field_name} must contain known reason codes")
    if len(set(reason_codes)) != len(reason_codes):
        raise ValueError(f"{field_name} must be unique")
    expected = tuple(
        reason_code for reason_code in allowed_reason_codes if reason_code in reason_codes
    )
    if reason_codes != expected:
        raise ValueError(f"{field_name} must use deterministic ordering")
    return reason_codes


def _normalize_ratio(field_name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(field_name, value, RATIO_QUANT)
    if normalized < ZERO or normalized > ONE:
        raise ValueError(f"{field_name} must be between zero and one")
    return normalized


def _normalize_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(field_name, value, RATIO_QUANT)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _normalize_nonnegative_integral_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(field_name, value, COUNT_QUANT)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    if normalized != value:
        raise ValueError(f"{field_name} must be an integer Decimal")
    return normalized


def _normalize_decimal(
    field_name: str,
    value: object,
    quantum: Decimal,
) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    try:
        return value.quantize(quantum)
    except InvalidOperation as exc:
        raise ValueError(f"{field_name} must be quantizable") from exc


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str or not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")


def _require_redacted_identifier(field_name: str, value: str) -> None:
    lowered = value.lower()
    if any(fragment in lowered for fragment in _BLOCKED_IDENTIFIER_FRAGMENTS):
        raise ValueError(f"{field_name} must be a redacted identifier")


def _require_reliability_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in RELIABILITY_STATUSES:
        raise ValueError(f"{field_name} must be pass, watch, or blocked")


def _require_hard_flags(label: str, value: object) -> None:
    if getattr(value, "paper_only", None) is not True:
        raise ValueError(f"{label} paper_only must be True")
    if getattr(value, "report_only", None) is not True:
        raise ValueError(f"{label} report_only must be True")
    if getattr(value, "readonly", None) is not True:
        raise ValueError(f"{label} readonly must be True")


def _validate_row(row: MarketResearchEquityIndexSourceReliabilityRow) -> None:
    if row.source_count <= ZERO:
        raise ValueError("source_count must be positive")
    if row.source_family_count <= ZERO:
        raise ValueError("source_family_count must be positive")
    if row.confirmation_count != (
        row.index_confirmation_count + row.futures_confirmation_count
    ):
        raise ValueError("confirmation_count must match index plus futures confirmations")
    if row.reason_codes == (
        "market_research_equity_index_source_reliability_digest_row_passed",
    ):
        if row.reliability_status != "pass":
            raise ValueError("passed row reason requires pass status")
        if row.reliability_score != ONE.quantize(RATIO_QUANT):
            raise ValueError("passed row reason requires full reliability score")
    elif (
        "market_research_equity_index_source_reliability_digest_row_high_contradiction_rate"
        in row.reason_codes
    ):
        if row.reliability_status != "blocked":
            raise ValueError("high contradiction row reason requires blocked status")
    elif row.reliability_status != "watch":
        raise ValueError("non-passed row reason requires watch status")


def _validate_report(report: MarketResearchEquityIndexSourceReliabilityReport) -> None:
    if report.event_count != _count(len(report.rows)):
        raise ValueError("event_count must match rows")
    if report.source_count != sum((row.source_count for row in report.rows), ZERO):
        raise ValueError("source_count must match rows")
    if report.event_count != (
        report.pass_count + report.watch_count + report.blocked_count
    ):
        raise ValueError("event_count must equal status counts")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")
    if report.reason_code_counts != _reason_code_counts(report.reason_codes):
        raise ValueError("reason_code_counts must match reason_codes")
    if report.reliability_status != _status_from_reason_codes(report.reason_codes):
        raise ValueError("reliability_status must match reason_codes")


class _RedactionMap:
    def __init__(self) -> None:
        self._values: dict[tuple[str, str], str] = {}
        self._counters: Counter[str] = Counter()

    def ref(self, kind: str, value: str) -> str:
        key = (kind, value)
        if key not in self._values:
            self._counters[kind] += 1
            self._values[key] = f"<redacted-{kind}-{self._counters[kind]:03d}>"
        return self._values[key]


def _payload_value(value: object, redactions: _RedactionMap) -> Any:
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, datetime):
        return value.isoformat()
    if is_dataclass(value) and not isinstance(value, type):
        payload: dict[str, Any] = {}
        field_names = {field.name for field in fields(value)}
        if "event_id" in field_names:
            payload["redacted_event_ref"] = redactions.ref(
                "event",
                str(getattr(value, "event_id")),
            )
        if "index_symbol" in field_names:
            payload["redacted_index_ref"] = redactions.ref(
                "index",
                str(getattr(value, "index_symbol")),
            )
        for field in fields(value):
            field_name = field.name
            if field_name in _PAYLOAD_OMIT_FIELDS:
                continue
            payload[field_name] = _payload_value(getattr(value, field_name), redactions)
        return payload
    if isinstance(value, tuple):
        return [_payload_value(item, redactions) for item in value]
    if isinstance(value, list):
        return [_payload_value(item, redactions) for item in value]
    if isinstance(value, dict):
        return {
            str(key): _payload_value(item, redactions)
            for key, item in sorted(value.items(), key=lambda item: str(item[0]))
        }
    return value
