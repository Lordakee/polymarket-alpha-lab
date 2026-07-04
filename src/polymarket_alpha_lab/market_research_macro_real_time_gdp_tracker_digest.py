"""Pure Phase 1 real-time GDP tracker digest reducer."""

from __future__ import annotations

from dataclasses import asdict, dataclass, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, InvalidOperation, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
from typing import Any


DEFAULT_MARKET_RESEARCH_MACRO_REAL_TIME_GDP_TRACKER_DIGEST_CONFIG_VERSION = (
    "market-research-macro-real-time-gdp-tracker-digest-v0"
)

STATUS_READY = "ready"
STATUS_WATCH = "watch"
STATUS_BLOCKED = "blocked"
TRACKER_STATUSES = (STATUS_READY, STATUS_WATCH, STATUS_BLOCKED)

REASON_PREFIX = "market_research_macro_real_time_gdp_tracker_digest_"
NO_INPUTS_REASON = f"{REASON_PREFIX}no_inputs"
READY_REASON = f"{REASON_PREFIX}ready"
MATERIAL_GROWTH_GAP_REASON = f"{REASON_PREFIX}material_growth_gap"
MATERIAL_REVISION_REASON = f"{REASON_PREFIX}material_revision"
PROBABILITY_REPRICING_REASON = f"{REASON_PREFIX}probability_repricing"
MISSING_ACKNOWLEDGEMENT_REASON = f"{REASON_PREFIX}missing_acknowledgement"
SLOW_ACKNOWLEDGEMENT_REASON = f"{REASON_PREFIX}slow_acknowledgement"
STALE_TRACKER_REASON = f"{REASON_PREFIX}stale_tracker"
THIN_SOURCES_REASON = f"{REASON_PREFIX}thin_sources"

REASON_CODE_SEQUENCE = (
    MATERIAL_GROWTH_GAP_REASON,
    MATERIAL_REVISION_REASON,
    PROBABILITY_REPRICING_REASON,
    MISSING_ACKNOWLEDGEMENT_REASON,
    SLOW_ACKNOWLEDGEMENT_REASON,
    STALE_TRACKER_REASON,
    THIN_SOURCES_REASON,
    READY_REASON,
    NO_INPUTS_REASON,
)
ROW_REASON_CODE_SEQUENCE = (
    MATERIAL_GROWTH_GAP_REASON,
    MATERIAL_REVISION_REASON,
    PROBABILITY_REPRICING_REASON,
    MISSING_ACKNOWLEDGEMENT_REASON,
    SLOW_ACKNOWLEDGEMENT_REASON,
    STALE_TRACKER_REASON,
    THIN_SOURCES_REASON,
    READY_REASON,
)

NEXT_STEPS = {
    STATUS_READY: "allow_report_only_market_research_macro_real_time_gdp_tracker_digest",
    STATUS_WATCH: "watch_report_only_market_research_macro_real_time_gdp_tracker_digest",
    STATUS_BLOCKED: "block_report_only_market_research_macro_real_time_gdp_tracker_digest",
}

DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
QUANT = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
MICROSECONDS_PER_SECOND = Decimal("1000000")


def _join_parts(*parts: str) -> str:
    return "".join(parts)


UNSAFE_TEXT_FRAGMENTS = frozenset(
    (
        _join_parts("wal", "let"),
        _join_parts("bro", "ker"),
        _join_parts("or", "der"),
        _join_parts("can", "cel"),
        _join_parts("re", "place"),
        _join_parts("ex", "change"),
        _join_parts("au", "th"),
        _join_parts("tok", "en"),
        _join_parts("sec", "ret"),
        _join_parts("data", "base"),
        _join_parts("priv", "ate"),
        _join_parts("sign", "ing"),
        _join_parts("acc", "ount"),
        _join_parts("sub", "mit"),
    ),
)

__all__ = (
    "DEFAULT_MARKET_RESEARCH_MACRO_REAL_TIME_GDP_TRACKER_DIGEST_CONFIG_VERSION",
    "MarketResearchMacroRealTimeGdpTrackerDigestConfig",
    "MarketResearchMacroRealTimeGdpTrackerDigestInputRow",
    "MarketResearchMacroRealTimeGdpTrackerDigestReasonCodeCount",
    "MarketResearchMacroRealTimeGdpTrackerDigestReport",
    "MarketResearchMacroRealTimeGdpTrackerDigestRow",
    "build_market_research_macro_real_time_gdp_tracker_digest",
    "market_research_macro_real_time_gdp_tracker_digest_payload",
)


@dataclass(frozen=True)
class MarketResearchMacroRealTimeGdpTrackerDigestConfig:
    config_version: str = DEFAULT_MARKET_RESEARCH_MACRO_REAL_TIME_GDP_TRACKER_DIGEST_CONFIG_VERSION
    fresh_tracker_max_age_seconds: Decimal = Decimal("7200.000000")
    material_growth_gap_threshold: Decimal = Decimal("0.400000")
    material_revision_threshold: Decimal = Decimal("0.300000")
    probability_repricing_threshold: Decimal = Decimal("0.100000")
    min_source_count: Decimal = Decimal("2.000000")
    max_acknowledgement_lag_seconds: Decimal = Decimal("1800.000000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketResearchMacroRealTimeGdpTrackerDigestConfig:
            raise TypeError(
                "MarketResearchMacroRealTimeGdpTrackerDigestConfig does not support "
                "subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not MarketResearchMacroRealTimeGdpTrackerDigestConfig:
            raise ValueError(
                "config must be exactly MarketResearchMacroRealTimeGdpTrackerDigestConfig",
            )
        _require_canonical_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_MARKET_RESEARCH_MACRO_REAL_TIME_GDP_TRACKER_DIGEST_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "fresh_tracker_max_age_seconds",
            "material_growth_gap_threshold",
            "material_revision_threshold",
            "probability_repricing_threshold",
            "max_acknowledgement_lag_seconds",
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
class MarketResearchMacroRealTimeGdpTrackerDigestInputRow:
    research_key: str
    condition_id: str
    tracker_key: str
    tracker_reference: str
    observed_at: datetime
    acknowledged_at: datetime | None
    source_count: Decimal
    annualized_real_gdp_growth: Decimal
    consensus_real_gdp_growth: Decimal
    prior_tracker_growth: Decimal
    market_probability_before: Decimal
    market_probability_after: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketResearchMacroRealTimeGdpTrackerDigestInputRow:
            raise TypeError(
                "MarketResearchMacroRealTimeGdpTrackerDigestInputRow does not support "
                "subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not MarketResearchMacroRealTimeGdpTrackerDigestInputRow:
            raise ValueError(
                "input row must be exactly "
                "MarketResearchMacroRealTimeGdpTrackerDigestInputRow",
            )
        for field_name in ("research_key", "condition_id", "tracker_key"):
            _require_public_string(field_name, getattr(self, field_name))
        _require_reference("tracker_reference", self.tracker_reference)
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        object.__setattr__(
            self,
            "acknowledged_at",
            _as_optional_utc("acknowledged_at", self.acknowledged_at),
        )
        if self.acknowledged_at is not None and self.acknowledged_at < self.observed_at:
            raise ValueError("acknowledged_at must not precede observed_at")
        object.__setattr__(
            self,
            "source_count",
            _require_nonnegative_count_decimal("source_count", self.source_count),
        )
        for field_name in (
            "annualized_real_gdp_growth",
            "consensus_real_gdp_growth",
            "prior_tracker_growth",
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
class MarketResearchMacroRealTimeGdpTrackerDigestRow:
    research_key: str
    condition_id: str
    tracker_key: str
    tracker_status: str
    observed_at: datetime
    acknowledged_at: datetime | None
    tracker_age_seconds: Decimal
    acknowledgement_lag_seconds: Decimal | None
    source_count: Decimal
    annualized_real_gdp_growth: Decimal
    consensus_real_gdp_growth: Decimal
    prior_tracker_growth: Decimal
    tracker_gap: Decimal
    tracker_gap_abs: Decimal
    tracker_revision: Decimal
    tracker_revision_abs: Decimal
    market_probability_before: Decimal
    market_probability_after: Decimal
    probability_delta: Decimal
    redacted_tracker_reference: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketResearchMacroRealTimeGdpTrackerDigestRow:
            raise TypeError(
                "MarketResearchMacroRealTimeGdpTrackerDigestRow does not support "
                "subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not MarketResearchMacroRealTimeGdpTrackerDigestRow:
            raise ValueError("row must be exactly MarketResearchMacroRealTimeGdpTrackerDigestRow")
        for field_name in ("research_key", "condition_id", "tracker_key"):
            _require_public_string(field_name, getattr(self, field_name))
        _require_tracker_status("tracker_status", self.tracker_status)
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        object.__setattr__(
            self,
            "acknowledged_at",
            _as_optional_utc("acknowledged_at", self.acknowledged_at),
        )
        if self.acknowledged_at is not None and self.acknowledged_at < self.observed_at:
            raise ValueError("acknowledged_at must not precede observed_at")
        object.__setattr__(
            self,
            "tracker_age_seconds",
            _require_nonnegative_decimal("tracker_age_seconds", self.tracker_age_seconds),
        )
        if self.acknowledgement_lag_seconds is not None:
            object.__setattr__(
                self,
                "acknowledgement_lag_seconds",
                _require_nonnegative_decimal(
                    "acknowledgement_lag_seconds",
                    self.acknowledgement_lag_seconds,
                ),
            )
        object.__setattr__(
            self,
            "source_count",
            _require_nonnegative_count_decimal("source_count", self.source_count),
        )
        for field_name in (
            "annualized_real_gdp_growth",
            "consensus_real_gdp_growth",
            "prior_tracker_growth",
            "tracker_gap",
            "tracker_gap_abs",
            "tracker_revision",
            "tracker_revision_abs",
            "probability_delta",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_finite_decimal(field_name, getattr(self, field_name)),
            )
        if self.tracker_gap_abs < ZERO:
            raise ValueError("tracker_gap_abs must be nonnegative")
        if self.tracker_revision_abs < ZERO:
            raise ValueError("tracker_revision_abs must be nonnegative")
        for field_name in ("market_probability_before", "market_probability_after"):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        _require_redacted_reference("redacted_tracker_reference", self.redacted_tracker_reference)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes, ROW_REASON_CODE_SEQUENCE),
        )
        _validate_row_consistency(self)
        _require_hard_flags("row", self)


@dataclass(frozen=True)
class MarketResearchMacroRealTimeGdpTrackerDigestReasonCodeCount:
    reason_code: str
    count: Decimal
    tracker_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketResearchMacroRealTimeGdpTrackerDigestReasonCodeCount:
            raise TypeError(
                "MarketResearchMacroRealTimeGdpTrackerDigestReasonCodeCount does not "
                "support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not MarketResearchMacroRealTimeGdpTrackerDigestReasonCodeCount:
            raise ValueError(
                "reason count must be exactly "
                "MarketResearchMacroRealTimeGdpTrackerDigestReasonCodeCount",
            )
        _require_known_reason_code("reason_code", self.reason_code)
        object.__setattr__(
            self,
            "count",
            _require_nonnegative_count_decimal("count", self.count),
        )
        object.__setattr__(
            self,
            "tracker_ratio",
            _require_ratio_decimal("tracker_ratio", self.tracker_ratio),
        )
        _require_hard_flags("reason count", self)


@dataclass(frozen=True)
class MarketResearchMacroRealTimeGdpTrackerDigestReport:
    generated_at: datetime
    config_version: str
    digest_status: str
    recommended_next_step: str
    reason_codes: tuple[str, ...]
    tracker_count: Decimal
    ready_tracker_count: Decimal
    watch_tracker_count: Decimal
    blocked_tracker_count: Decimal
    material_growth_gap_count: Decimal
    material_revision_count: Decimal
    stale_tracker_count: Decimal
    thin_source_count: Decimal
    missing_acknowledgement_count: Decimal
    slow_acknowledgement_count: Decimal
    probability_repricing_count: Decimal
    average_tracker_gap_abs: Decimal
    max_tracker_age_seconds: Decimal
    average_source_count: Decimal
    rows: tuple[MarketResearchMacroRealTimeGdpTrackerDigestRow, ...]
    reason_code_counts: tuple[MarketResearchMacroRealTimeGdpTrackerDigestReasonCodeCount, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketResearchMacroRealTimeGdpTrackerDigestReport:
            raise TypeError(
                "MarketResearchMacroRealTimeGdpTrackerDigestReport does not support "
                "subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not MarketResearchMacroRealTimeGdpTrackerDigestReport:
            raise ValueError(
                "report must be exactly MarketResearchMacroRealTimeGdpTrackerDigestReport",
            )
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_MARKET_RESEARCH_MACRO_REAL_TIME_GDP_TRACKER_DIGEST_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        _require_tracker_status("digest_status", self.digest_status)
        if self.recommended_next_step != NEXT_STEPS[self.digest_status]:
            raise ValueError("recommended_next_step must match digest_status")
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes, REASON_CODE_SEQUENCE),
        )
        for field_name in (
            "tracker_count",
            "ready_tracker_count",
            "watch_tracker_count",
            "blocked_tracker_count",
            "material_growth_gap_count",
            "material_revision_count",
            "stale_tracker_count",
            "thin_source_count",
            "missing_acknowledgement_count",
            "slow_acknowledgement_count",
            "probability_repricing_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_count_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "average_tracker_gap_abs",
            "max_tracker_age_seconds",
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
        _validate_report_consistency(self)
        _require_hard_flags("report", self)


def build_market_research_macro_real_time_gdp_tracker_digest(
    rows: tuple[object, ...],
    *,
    config: MarketResearchMacroRealTimeGdpTrackerDigestConfig | None = None,
    generated_at: datetime,
) -> MarketResearchMacroRealTimeGdpTrackerDigestReport:
    if config is None:
        config = MarketResearchMacroRealTimeGdpTrackerDigestConfig()
    if type(config) is not MarketResearchMacroRealTimeGdpTrackerDigestConfig:
        raise ValueError(
            "config must be exactly MarketResearchMacroRealTimeGdpTrackerDigestConfig",
        )
    generated_at_utc = _as_utc("generated_at", generated_at)
    source_rows = _normalize_input_rows(rows)
    digest_rows = tuple(
        _build_digest_row(source, config=config, generated_at=generated_at_utc)
        for source in source_rows
    )
    sorted_rows = tuple(sorted(digest_rows, key=_row_sort_key))
    reason_counts = _build_reason_code_counts(sorted_rows)
    tracker_count = _decimal_count(sorted_rows)
    ready_count = _decimal_count(
        row for row in sorted_rows if row.tracker_status == STATUS_READY
    )
    watch_count = _decimal_count(
        row for row in sorted_rows if row.tracker_status == STATUS_WATCH
    )
    blocked_count = _decimal_count(
        row for row in sorted_rows if row.tracker_status == STATUS_BLOCKED
    )
    digest_status = _digest_status(blocked_count, watch_count)
    reason_codes = _digest_reason_codes(sorted_rows)
    if not sorted_rows:
        reason_codes = (NO_INPUTS_REASON,)
    return MarketResearchMacroRealTimeGdpTrackerDigestReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        digest_status=digest_status,
        recommended_next_step=NEXT_STEPS[digest_status],
        reason_codes=reason_codes,
        tracker_count=tracker_count,
        ready_tracker_count=ready_count,
        watch_tracker_count=watch_count,
        blocked_tracker_count=blocked_count,
        material_growth_gap_count=_reason_count(sorted_rows, MATERIAL_GROWTH_GAP_REASON),
        material_revision_count=_reason_count(sorted_rows, MATERIAL_REVISION_REASON),
        stale_tracker_count=_reason_count(sorted_rows, STALE_TRACKER_REASON),
        thin_source_count=_reason_count(sorted_rows, THIN_SOURCES_REASON),
        missing_acknowledgement_count=_reason_count(
            sorted_rows,
            MISSING_ACKNOWLEDGEMENT_REASON,
        ),
        slow_acknowledgement_count=_reason_count(sorted_rows, SLOW_ACKNOWLEDGEMENT_REASON),
        probability_repricing_count=_reason_count(
            sorted_rows,
            PROBABILITY_REPRICING_REASON,
        ),
        average_tracker_gap_abs=_average(tuple(row.tracker_gap_abs for row in sorted_rows)),
        max_tracker_age_seconds=max(
            (row.tracker_age_seconds for row in sorted_rows),
            default=ZERO,
        ),
        average_source_count=_average(tuple(row.source_count for row in sorted_rows)),
        rows=sorted_rows,
        reason_code_counts=reason_counts,
    )


def market_research_macro_real_time_gdp_tracker_digest_payload(
    report: MarketResearchMacroRealTimeGdpTrackerDigestReport,
) -> dict[str, Any]:
    if type(report) is not MarketResearchMacroRealTimeGdpTrackerDigestReport:
        raise ValueError(
            "report must be exactly MarketResearchMacroRealTimeGdpTrackerDigestReport",
        )
    _validate_payload_flags(report)
    payload = _payload_value(report)
    if type(payload) is not dict:
        raise ValueError("payload must be a JSON object")
    return payload


def _build_digest_row(
    source: MarketResearchMacroRealTimeGdpTrackerDigestInputRow,
    *,
    config: MarketResearchMacroRealTimeGdpTrackerDigestConfig,
    generated_at: datetime,
) -> MarketResearchMacroRealTimeGdpTrackerDigestRow:
    if source.observed_at > generated_at:
        raise ValueError("observed_at must not be after generated_at")
    tracker_age_seconds = _seconds_between(source.observed_at, generated_at)
    acknowledgement_lag_seconds = None
    if source.acknowledged_at is not None:
        acknowledgement_lag_seconds = _seconds_between(
            source.observed_at,
            source.acknowledged_at,
        )
    tracker_gap = _quantize(source.annualized_real_gdp_growth - source.consensus_real_gdp_growth)
    tracker_gap_abs = _quantize(abs(tracker_gap))
    tracker_revision = _quantize(source.annualized_real_gdp_growth - source.prior_tracker_growth)
    tracker_revision_abs = _quantize(abs(tracker_revision))
    probability_delta = _quantize(
        source.market_probability_after - source.market_probability_before,
    )
    reasons: list[str] = []
    if tracker_gap_abs >= config.material_growth_gap_threshold:
        reasons.append(MATERIAL_GROWTH_GAP_REASON)
    if tracker_revision_abs >= config.material_revision_threshold:
        reasons.append(MATERIAL_REVISION_REASON)
    if abs(probability_delta) >= config.probability_repricing_threshold:
        reasons.append(PROBABILITY_REPRICING_REASON)
    if source.acknowledged_at is None:
        reasons.append(MISSING_ACKNOWLEDGEMENT_REASON)
    elif acknowledgement_lag_seconds is not None and (
        acknowledgement_lag_seconds > config.max_acknowledgement_lag_seconds
    ):
        reasons.append(SLOW_ACKNOWLEDGEMENT_REASON)
    if tracker_age_seconds > config.fresh_tracker_max_age_seconds:
        reasons.append(STALE_TRACKER_REASON)
    if source.source_count < config.min_source_count:
        reasons.append(THIN_SOURCES_REASON)
    if not reasons:
        reasons.append(READY_REASON)
    reason_codes = _normalize_reason_codes(tuple(reasons), ROW_REASON_CODE_SEQUENCE)
    return MarketResearchMacroRealTimeGdpTrackerDigestRow(
        research_key=source.research_key,
        condition_id=source.condition_id,
        tracker_key=source.tracker_key,
        tracker_status=_row_status(reason_codes),
        observed_at=source.observed_at,
        acknowledged_at=source.acknowledged_at,
        tracker_age_seconds=tracker_age_seconds,
        acknowledgement_lag_seconds=acknowledgement_lag_seconds,
        source_count=source.source_count,
        annualized_real_gdp_growth=source.annualized_real_gdp_growth,
        consensus_real_gdp_growth=source.consensus_real_gdp_growth,
        prior_tracker_growth=source.prior_tracker_growth,
        tracker_gap=tracker_gap,
        tracker_gap_abs=tracker_gap_abs,
        tracker_revision=tracker_revision,
        tracker_revision_abs=tracker_revision_abs,
        market_probability_before=source.market_probability_before,
        market_probability_after=source.market_probability_after,
        probability_delta=probability_delta,
        redacted_tracker_reference=_redact_reference(source.tracker_reference),
        reason_codes=reason_codes,
    )


def _row_status(reason_codes: tuple[str, ...]) -> str:
    if MISSING_ACKNOWLEDGEMENT_REASON in reason_codes:
        return STATUS_BLOCKED
    if reason_codes == (READY_REASON,):
        return STATUS_READY
    return STATUS_WATCH


def _digest_status(blocked_count: Decimal, watch_count: Decimal) -> str:
    if blocked_count > ZERO:
        return STATUS_BLOCKED
    if watch_count > ZERO:
        return STATUS_WATCH
    return STATUS_READY


def _row_sort_key(
    row: MarketResearchMacroRealTimeGdpTrackerDigestRow,
) -> tuple[int, Decimal, str, str]:
    rank = {
        STATUS_BLOCKED: 0,
        STATUS_WATCH: 1,
        STATUS_READY: 2,
    }[row.tracker_status]
    return (rank, -row.tracker_gap_abs, row.tracker_key, row.research_key)


def _digest_reason_codes(
    rows: tuple[MarketResearchMacroRealTimeGdpTrackerDigestRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return (NO_INPUTS_REASON,)
    seen: set[str] = set()
    for row in rows:
        seen.update(row.reason_codes)
    if seen == {READY_REASON}:
        return (READY_REASON,)
    seen.discard(READY_REASON)
    return tuple(reason for reason in REASON_CODE_SEQUENCE if reason in seen)


def _build_reason_code_counts(
    rows: tuple[MarketResearchMacroRealTimeGdpTrackerDigestRow, ...],
) -> tuple[MarketResearchMacroRealTimeGdpTrackerDigestReasonCodeCount, ...]:
    total = _decimal_count(rows)
    if total == ZERO:
        return ()
    counts: list[MarketResearchMacroRealTimeGdpTrackerDigestReasonCodeCount] = []
    for reason_code in REASON_CODE_SEQUENCE:
        if reason_code in (READY_REASON, NO_INPUTS_REASON):
            continue
        count = _reason_count(rows, reason_code)
        if count > ZERO:
            counts.append(
                MarketResearchMacroRealTimeGdpTrackerDigestReasonCodeCount(
                    reason_code=reason_code,
                    count=count,
                    tracker_ratio=_ratio(count, total),
                ),
            )
    return tuple(counts)


def _reason_count(
    rows: tuple[MarketResearchMacroRealTimeGdpTrackerDigestRow, ...],
    reason_code: str,
) -> Decimal:
    return _decimal_count(row for row in rows if reason_code in row.reason_codes)


def _normalize_input_rows(
    rows: tuple[object, ...],
) -> tuple[MarketResearchMacroRealTimeGdpTrackerDigestInputRow, ...]:
    if type(rows) is not tuple:
        raise ValueError("rows must be a tuple")
    normalized: list[MarketResearchMacroRealTimeGdpTrackerDigestInputRow] = []
    for row in rows:
        if type(row) is not MarketResearchMacroRealTimeGdpTrackerDigestInputRow:
            raise ValueError(
                "input row must be exactly "
                "MarketResearchMacroRealTimeGdpTrackerDigestInputRow",
            )
        normalized.append(row)
    return tuple(normalized)


def _normalize_rows(
    rows: tuple[MarketResearchMacroRealTimeGdpTrackerDigestRow, ...],
) -> tuple[MarketResearchMacroRealTimeGdpTrackerDigestRow, ...]:
    if type(rows) is not tuple:
        raise ValueError("rows must be a tuple")
    normalized: list[MarketResearchMacroRealTimeGdpTrackerDigestRow] = []
    for row in rows:
        if type(row) is not MarketResearchMacroRealTimeGdpTrackerDigestRow:
            raise ValueError("row must be exactly MarketResearchMacroRealTimeGdpTrackerDigestRow")
        normalized.append(row)
    return tuple(sorted(normalized, key=_row_sort_key))


def _normalize_reason_code_counts(
    counts: tuple[MarketResearchMacroRealTimeGdpTrackerDigestReasonCodeCount, ...],
) -> tuple[MarketResearchMacroRealTimeGdpTrackerDigestReasonCodeCount, ...]:
    if type(counts) is not tuple:
        raise ValueError("reason_code_counts must be a tuple")
    normalized: list[MarketResearchMacroRealTimeGdpTrackerDigestReasonCodeCount] = []
    for count in counts:
        if type(count) is not MarketResearchMacroRealTimeGdpTrackerDigestReasonCodeCount:
            raise ValueError(
                "reason count must be exactly "
                "MarketResearchMacroRealTimeGdpTrackerDigestReasonCodeCount",
            )
        normalized.append(count)
    return tuple(
        sorted(
            normalized,
            key=lambda item: (REASON_CODE_SEQUENCE.index(item.reason_code), item.reason_code),
        ),
    )


def _validate_row_consistency(
    row: MarketResearchMacroRealTimeGdpTrackerDigestRow,
) -> None:
    if _quantize(abs(row.tracker_gap)) != row.tracker_gap_abs:
        raise ValueError("tracker_gap_abs must match tracker_gap")
    if _quantize(abs(row.tracker_revision)) != row.tracker_revision_abs:
        raise ValueError("tracker_revision_abs must match tracker_revision")
    expected_probability_delta = _quantize(
        row.market_probability_after - row.market_probability_before,
    )
    if row.probability_delta != expected_probability_delta:
        raise ValueError("probability_delta must match market probabilities")
    if row.tracker_status != _row_status(row.reason_codes):
        raise ValueError("tracker_status must match reason_codes")


def _validate_report_consistency(
    report: MarketResearchMacroRealTimeGdpTrackerDigestReport,
) -> None:
    if (
        report.ready_tracker_count
        + report.watch_tracker_count
        + report.blocked_tracker_count
        != report.tracker_count
    ):
        raise ValueError("status counts must sum to tracker_count")
    if report.tracker_count != _decimal_count(report.rows):
        raise ValueError("tracker_count must equal row count")
    expected_status = _digest_status(
        _decimal_count(row for row in report.rows if row.tracker_status == STATUS_BLOCKED),
        _decimal_count(row for row in report.rows if row.tracker_status == STATUS_WATCH),
    )
    if report.digest_status != expected_status:
        raise ValueError("digest_status must summarize rows")
    expected_reasons = _digest_reason_codes(report.rows)
    if report.reason_codes != expected_reasons:
        raise ValueError("reason_codes must summarize rows")


def _normalize_reason_codes(
    reason_codes: tuple[str, ...],
    sequence: tuple[str, ...],
) -> tuple[str, ...]:
    if type(reason_codes) is not tuple:
        raise ValueError("reason_codes must be a tuple")
    seen: set[str] = set()
    for reason_code in reason_codes:
        _require_known_reason_code("reason_code", reason_code)
        if reason_code in seen:
            raise ValueError("reason_codes must not contain duplicates")
        if reason_code not in sequence:
            raise ValueError("reason_code is not valid for this scope")
        seen.add(reason_code)
    normalized = tuple(reason_code for reason_code in sequence if reason_code in seen)
    if normalized != reason_codes:
        raise ValueError("reason_codes must be deterministic")
    return normalized


def _require_known_reason_code(field_name: str, value: str) -> None:
    _require_canonical_string(field_name, value)
    if value not in REASON_CODE_SEQUENCE:
        raise ValueError(f"{field_name} must be a known reason code")


def _require_tracker_status(field_name: str, value: str) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a plain string")
    if value not in TRACKER_STATUSES:
        raise ValueError(f"{field_name} must be one of {TRACKER_STATUSES}")


def _require_public_string(field_name: str, value: str) -> None:
    _require_canonical_string(field_name, value)
    _reject_unsafe_text(field_name, value)


def _require_reference(field_name: str, value: str) -> None:
    _require_canonical_string(field_name, value)
    _reject_unsafe_text(field_name, value)


def _require_redacted_reference(field_name: str, value: str) -> None:
    _require_canonical_string(field_name, value)
    if value.startswith("public-"):
        _reject_unsafe_text(field_name, value)
        return
    if value.startswith("sha256:") and len(value) == len("sha256:") + 12:
        suffix = value.removeprefix("sha256:")
        if all(character in "0123456789abcdef" for character in suffix):
            return
    raise ValueError(f"{field_name} must be redacted")


def _require_canonical_string(field_name: str, value: str) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a plain string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be non-empty canonical text")


def _reject_unsafe_text(field_name: str, value: str) -> None:
    lowered = value.lower()
    if any(fragment in lowered for fragment in UNSAFE_TEXT_FRAGMENTS):
        raise ValueError(f"{field_name} contains unsafe text")


def _require_hard_flags(label: str, value: object) -> None:
    if (
        getattr(value, "paper_only", None) is not True
        or getattr(value, "report_only", None) is not True
        or getattr(value, "readonly", None) is not True
    ):
        raise ValueError(f"{label} paper_only/report_only/readonly must be True")


def _validate_payload_flags(
    report: MarketResearchMacroRealTimeGdpTrackerDigestReport,
) -> None:
    _require_hard_flags("report", report)
    for row in report.rows:
        _require_hard_flags("row", row)
    for count in report.reason_code_counts:
        _require_hard_flags("reason count", count)


def _as_utc(field_name: str, value: datetime) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be exactly datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _as_optional_utc(field_name: str, value: datetime | None) -> datetime | None:
    if value is None:
        return None
    return _as_utc(field_name, value)


def _require_decimal(field_name: str, value: Decimal) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be exactly Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return _quantize(value)


def _require_finite_decimal(field_name: str, value: Decimal) -> Decimal:
    return _require_decimal(field_name, value)


def _require_nonnegative_decimal(field_name: str, value: Decimal) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _require_positive_decimal(field_name: str, value: Decimal) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _require_nonnegative_count_decimal(field_name: str, value: Decimal) -> Decimal:
    normalized = _require_nonnegative_decimal(field_name, value)
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{field_name} must be a whole-count Decimal")
    return normalized


def _require_positive_count_decimal(field_name: str, value: Decimal) -> Decimal:
    normalized = _require_nonnegative_count_decimal(field_name, value)
    if normalized <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _require_ratio_decimal(field_name: str, value: Decimal) -> Decimal:
    normalized = _require_nonnegative_decimal(field_name, value)
    if normalized > ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return normalized


def _quantize(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        try:
            return value.quantize(QUANT)
        except InvalidOperation as exc:
            raise ValueError("decimal value could not be quantized") from exc


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return _quantize(numerator / denominator)


def _average(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return ZERO
    return _ratio(sum(values, ZERO), _decimal_count(values))


def _decimal_count(values: object) -> Decimal:
    return _quantize(Decimal(sum(1 for _ in values)))  # type: ignore[union-attr]


def _seconds_between(start: datetime, end: datetime) -> Decimal:
    delta = end - start
    total = (
        Decimal(delta.days * 86400 + delta.seconds)
        + (Decimal(delta.microseconds) / MICROSECONDS_PER_SECOND)
    )
    return _require_nonnegative_decimal("seconds", total)


def _redact_reference(value: str) -> str:
    if value.startswith("public-"):
        return value
    digest = sha256(value.encode("utf-8")).hexdigest()[:12]
    return f"sha256:{digest}"


def _payload_value(value: object) -> Any:
    if value is None:
        return None
    if is_dataclass(value) and not isinstance(value, type):
        return _payload_value(asdict(value))
    if type(value) is Decimal:
        return _format_decimal(value)
    if type(value) is datetime:
        return _as_utc("datetime", value).isoformat()
    if type(value) is float:
        raise ValueError("payload values must not be floats")
    if type(value) is int:
        raise ValueError("payload numeric values must be Decimal-derived strings")
    if type(value) in (str, bool):
        return value
    if type(value) is dict:
        payload: dict[str, Any] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("payload keys must be strings")
            payload[key] = _payload_value(item)
        return payload
    if type(value) in (tuple, list):
        return [_payload_value(item) for item in value]
    raise ValueError("payload contains an unsupported value")


def _format_decimal(value: Decimal) -> str:
    return format(_require_decimal("payload decimal", value), "f")
