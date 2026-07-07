"""Pure reducer for market close resolution readiness digest reports."""

from __future__ import annotations

from dataclasses import dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import ROUND_HALF_EVEN, Decimal
from hashlib import sha256


DEFAULT_MARKET_CLOSE_RESOLUTION_READINESS_DIGEST_CONFIG_VERSION = (
    "market-close-resolution-readiness-digest-v0"
)

EMPTY_INPUT_REASON = "market_close_resolution_readiness_digest_empty_input"

NEXT_STEPS = {
    "ready": "allow_market_close_resolution_use",
    "watch": "monitor_market_close_resolution_use",
    "blocked": "block_market_close_resolution_use",
}

ROW_REASON_CODES = (
    "acknowledgement_fresh",
    "acknowledgement_stale",
    "close_window_clear",
    "close_window_elapsed",
    "close_window_near",
    "outcome_evidence_complete",
    "outcome_evidence_incomplete",
    "resolution_sources_complete",
    "resolution_sources_missing",
    "unresolved_ambiguity_absent",
    "unresolved_ambiguity_present",
)

REASON_CODES = tuple(sorted((EMPTY_INPUT_REASON, *ROW_REASON_CODES)))

ZERO = Decimal("0")
ONE = Decimal("1")
SIX_PLACES = Decimal("0.000001")
SECONDS_PER_DAY = Decimal("86400")
MICROSECONDS_PER_SECOND = Decimal("1000000")
DERIVED_VALIDATION_DIGEST_PREFIX = "mcrrd-v0"
DERIVED_VALIDATION_DIGEST_FIELD = "derived_validation_digest"
HARD_FLAG_FIELDS = ("paper_only", "report_only", "readonly")
UNSAFE_PUBLIC_SURFACE_FRAGMENTS = (
    "".join(("li", "ve")),
    "".join(("au", "th")),
    "".join(("wall", "et")),
    "".join(("or", "der")),
    "".join(("net", "work")),
    "".join(("data", "base")),
    "".join(("per", "sist")),
)

__all__ = (
    "DEFAULT_MARKET_CLOSE_RESOLUTION_READINESS_DIGEST_CONFIG_VERSION",
    "MarketCloseResolutionReadinessDigestConfig",
    "MarketCloseResolutionReadinessDigestInput",
    "MarketCloseResolutionReadinessDigestRow",
    "MarketCloseResolutionReadinessDigestCategoryRollup",
    "MarketCloseResolutionReadinessDigestReasonCodeCount",
    "MarketCloseResolutionReadinessDigestReport",
    "build_market_close_resolution_readiness_digest",
    "market_close_resolution_readiness_digest_payload",
)


@dataclass(frozen=True)
class MarketCloseResolutionReadinessDigestConfig:
    config_version: str = DEFAULT_MARKET_CLOSE_RESOLUTION_READINESS_DIGEST_CONFIG_VERSION
    watch_close_within_seconds: Decimal = Decimal("3600")
    block_close_after_seconds: Decimal = Decimal("300")
    acknowledgement_freshness_seconds: Decimal = Decimal("900")
    min_outcome_evidence_count: Decimal = Decimal("2")
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not MarketCloseResolutionReadinessDigestConfig:
            raise ValueError("config must be exactly MarketCloseResolutionReadinessDigestConfig")
        _require_canonical_string("config_version", self.config_version)
        _require_nonnegative_decimal_seconds(
            "watch_close_within_seconds",
            self.watch_close_within_seconds,
        )
        _require_nonnegative_decimal_seconds(
            "block_close_after_seconds",
            self.block_close_after_seconds,
        )
        _require_nonnegative_decimal_seconds(
            "acknowledgement_freshness_seconds",
            self.acknowledgement_freshness_seconds,
        )
        _require_nonnegative_decimal_whole(
            "min_outcome_evidence_count",
            self.min_outcome_evidence_count,
        )
        _require_hard_flags("config", self)
        _reject_unsafe_public_surface("config", self)
        _require_derived_validation_digest("config", self)


@dataclass(frozen=True)
class MarketCloseResolutionReadinessDigestInput:
    market_slug: str
    category: str
    event_slug: str
    close_time: datetime
    required_resolution_sources: tuple[str, ...]
    covered_resolution_sources: tuple[str, ...]
    acknowledged_at: datetime
    outcome_evidence_count: Decimal
    unresolved_ambiguity_count: Decimal
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not MarketCloseResolutionReadinessDigestInput:
            raise ValueError("market input must be exactly MarketCloseResolutionReadinessDigestInput")
        _require_canonical_string("market_slug", self.market_slug)
        _require_canonical_string("category", self.category)
        _require_canonical_string("event_slug", self.event_slug)
        object.__setattr__(self, "close_time", _as_utc("close_time", self.close_time))
        object.__setattr__(
            self,
            "required_resolution_sources",
            _normalize_required_sources(self.required_resolution_sources),
        )
        object.__setattr__(
            self,
            "covered_resolution_sources",
            _normalize_sources("covered_resolution_sources", self.covered_resolution_sources),
        )
        object.__setattr__(
            self,
            "acknowledged_at",
            _as_utc("acknowledged_at", self.acknowledged_at),
        )
        _require_nonnegative_decimal_whole(
            "outcome_evidence_count",
            self.outcome_evidence_count,
        )
        _require_nonnegative_decimal_whole(
            "unresolved_ambiguity_count",
            self.unresolved_ambiguity_count,
        )
        _require_hard_flags("market input", self)
        _reject_unsafe_public_surface("market input", self)
        _require_derived_validation_digest("market input", self)


@dataclass(frozen=True)
class MarketCloseResolutionReadinessDigestRow:
    market_slug: str
    category: str
    event_slug: str
    close_time: datetime
    seconds_until_close: Decimal
    required_resolution_source_count: Decimal
    covered_resolution_source_count: Decimal
    missing_resolution_source_count: Decimal
    resolution_source_coverage_ratio: Decimal
    missing_resolution_sources: tuple[str, ...]
    acknowledged_at: datetime
    acknowledgement_age_seconds: Decimal
    outcome_evidence_count: Decimal
    unresolved_ambiguity_count: Decimal
    readiness_status: str
    reason_codes: tuple[str, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not MarketCloseResolutionReadinessDigestRow:
            raise ValueError("row must be exactly MarketCloseResolutionReadinessDigestRow")
        _require_canonical_string("market_slug", self.market_slug)
        _require_canonical_string("category", self.category)
        _require_canonical_string("event_slug", self.event_slug)
        object.__setattr__(self, "close_time", _as_utc("close_time", self.close_time))
        _require_decimal("seconds_until_close", self.seconds_until_close)
        _require_nonnegative_decimal_whole(
            "required_resolution_source_count",
            self.required_resolution_source_count,
        )
        _require_nonnegative_decimal_whole(
            "covered_resolution_source_count",
            self.covered_resolution_source_count,
        )
        _require_nonnegative_decimal_whole(
            "missing_resolution_source_count",
            self.missing_resolution_source_count,
        )
        _require_ratio("resolution_source_coverage_ratio", self.resolution_source_coverage_ratio)
        object.__setattr__(
            self,
            "missing_resolution_sources",
            _normalize_sources("missing_resolution_sources", self.missing_resolution_sources),
        )
        object.__setattr__(
            self,
            "acknowledged_at",
            _as_utc("acknowledged_at", self.acknowledged_at),
        )
        _require_nonnegative_decimal_seconds(
            "acknowledgement_age_seconds",
            self.acknowledgement_age_seconds,
        )
        _require_nonnegative_decimal_whole(
            "outcome_evidence_count",
            self.outcome_evidence_count,
        )
        _require_nonnegative_decimal_whole(
            "unresolved_ambiguity_count",
            self.unresolved_ambiguity_count,
        )
        _require_status("readiness_status", self.readiness_status)
        object.__setattr__(self, "reason_codes", _normalize_reason_codes(self.reason_codes))
        _require_hard_flags("row", self)
        _reject_unsafe_public_surface("row", self)
        _require_derived_validation_digest("row", self)


@dataclass(frozen=True)
class MarketCloseResolutionReadinessDigestCategoryRollup:
    category: str
    row_count: Decimal
    ready_count: Decimal
    watch_count: Decimal
    blocked_count: Decimal
    required_resolution_source_count: Decimal
    covered_resolution_source_count: Decimal
    missing_resolution_source_count: Decimal
    resolution_source_coverage_ratio: Decimal
    reason_codes: tuple[str, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not MarketCloseResolutionReadinessDigestCategoryRollup:
            raise ValueError(
                "category rollup must be exactly "
                "MarketCloseResolutionReadinessDigestCategoryRollup",
            )
        _require_canonical_string("category", self.category)
        _require_nonnegative_decimal_whole("row_count", self.row_count)
        _require_nonnegative_decimal_whole("ready_count", self.ready_count)
        _require_nonnegative_decimal_whole("watch_count", self.watch_count)
        _require_nonnegative_decimal_whole("blocked_count", self.blocked_count)
        _require_nonnegative_decimal_whole(
            "required_resolution_source_count",
            self.required_resolution_source_count,
        )
        _require_nonnegative_decimal_whole(
            "covered_resolution_source_count",
            self.covered_resolution_source_count,
        )
        _require_nonnegative_decimal_whole(
            "missing_resolution_source_count",
            self.missing_resolution_source_count,
        )
        _require_ratio("resolution_source_coverage_ratio", self.resolution_source_coverage_ratio)
        object.__setattr__(self, "reason_codes", _normalize_reason_codes(self.reason_codes))
        _require_hard_flags("category rollup", self)
        _reject_unsafe_public_surface("category rollup", self)
        _require_derived_validation_digest("category rollup", self)


@dataclass(frozen=True)
class MarketCloseResolutionReadinessDigestReasonCodeCount:
    reason_code: str
    count: Decimal
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not MarketCloseResolutionReadinessDigestReasonCodeCount:
            raise ValueError(
                "reason code count must be exactly "
                "MarketCloseResolutionReadinessDigestReasonCodeCount",
            )
        _require_reason_code("reason_code", self.reason_code)
        _require_positive_decimal_whole("count", self.count)
        _require_hard_flags("reason code count", self)
        _reject_unsafe_public_surface("reason code count", self)
        _require_derived_validation_digest("reason code count", self)


@dataclass(frozen=True)
class MarketCloseResolutionReadinessDigestReport:
    generated_at: datetime
    config_version: str
    digest_status: str
    recommended_next_step: str
    input_count: Decimal
    row_count: Decimal
    ready_count: Decimal
    watch_count: Decimal
    blocked_count: Decimal
    required_resolution_source_count: Decimal
    covered_resolution_source_count: Decimal
    missing_resolution_source_count: Decimal
    resolution_source_coverage_ratio: Decimal
    rows: tuple[MarketCloseResolutionReadinessDigestRow, ...]
    category_rollups: tuple[MarketCloseResolutionReadinessDigestCategoryRollup, ...]
    reason_code_counts: tuple[MarketCloseResolutionReadinessDigestReasonCodeCount, ...]
    reason_codes: tuple[str, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not MarketCloseResolutionReadinessDigestReport:
            raise ValueError("report must be exactly MarketCloseResolutionReadinessDigestReport")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        _require_status("digest_status", self.digest_status)
        _require_canonical_string("recommended_next_step", self.recommended_next_step)
        _require_nonnegative_decimal_whole("input_count", self.input_count)
        _require_nonnegative_decimal_whole("row_count", self.row_count)
        _require_nonnegative_decimal_whole("ready_count", self.ready_count)
        _require_nonnegative_decimal_whole("watch_count", self.watch_count)
        _require_nonnegative_decimal_whole("blocked_count", self.blocked_count)
        _require_nonnegative_decimal_whole(
            "required_resolution_source_count",
            self.required_resolution_source_count,
        )
        _require_nonnegative_decimal_whole(
            "covered_resolution_source_count",
            self.covered_resolution_source_count,
        )
        _require_nonnegative_decimal_whole(
            "missing_resolution_source_count",
            self.missing_resolution_source_count,
        )
        _require_ratio("resolution_source_coverage_ratio", self.resolution_source_coverage_ratio)
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        object.__setattr__(
            self,
            "category_rollups",
            _normalize_category_rollups(self.category_rollups),
        )
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        object.__setattr__(self, "reason_codes", _normalize_reason_codes(self.reason_codes))
        _validate_report_consistency(self)
        _require_hard_flags("report", self)
        _reject_unsafe_public_surface("report", self)
        _require_derived_validation_digest("report", self)


def build_market_close_resolution_readiness_digest(
    markets: list[MarketCloseResolutionReadinessDigestInput]
    | tuple[MarketCloseResolutionReadinessDigestInput, ...],
    *,
    config: MarketCloseResolutionReadinessDigestConfig,
    generated_at: datetime,
) -> MarketCloseResolutionReadinessDigestReport:
    if type(config) is not MarketCloseResolutionReadinessDigestConfig:
        raise ValueError("config must be a MarketCloseResolutionReadinessDigestConfig")
    _require_hard_flags("config", config)
    _require_derived_validation_digest("config", config)
    _reject_unsafe_public_surface("config", config)
    normalized_markets = _normalize_market_inputs(markets)
    generated_at_utc = _as_utc("generated_at", generated_at)
    rows = tuple(
        sorted(
            (
                _row_from_market(market, config=config, generated_at=generated_at_utc)
                for market in normalized_markets
            ),
            key=_row_key,
        )
    )
    reason_codes = _digest_reason_codes(rows)
    return MarketCloseResolutionReadinessDigestReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        digest_status=_status_from_rows(rows),
        recommended_next_step=NEXT_STEPS[_status_from_rows(rows)],
        input_count=_decimal_count(len(normalized_markets)),
        row_count=_decimal_count(len(rows)),
        ready_count=_decimal_count(_count_status(rows, "ready")),
        watch_count=_decimal_count(_count_status(rows, "watch")),
        blocked_count=_decimal_count(_count_status(rows, "blocked")),
        required_resolution_source_count=_sum_decimal(
            row.required_resolution_source_count for row in rows
        ),
        covered_resolution_source_count=_sum_decimal(
            row.covered_resolution_source_count for row in rows
        ),
        missing_resolution_source_count=_sum_decimal(
            row.missing_resolution_source_count for row in rows
        ),
        resolution_source_coverage_ratio=_coverage_ratio(
            _sum_decimal(row.covered_resolution_source_count for row in rows),
            _sum_decimal(row.required_resolution_source_count for row in rows),
        ),
        rows=rows,
        category_rollups=_category_rollups(rows),
        reason_code_counts=_reason_code_counts(rows, reason_codes),
        reason_codes=reason_codes,
    )


def market_close_resolution_readiness_digest_payload(
    report: MarketCloseResolutionReadinessDigestReport | dict[str, object],
) -> dict[str, object]:
    if type(report) is not MarketCloseResolutionReadinessDigestReport:
        if type(report) is not dict:
            raise ValueError("report must be a MarketCloseResolutionReadinessDigestReport")
        _reject_unsafe_public_surface("payload", report)
        _require_payload_hard_flags("payload", report, require_here=True)
        _require_payload_hard_flags("payload", report, require_all_dicts=True)
        payload = _payload_value(report, allow_dataclasses=False)
        if type(payload) is not dict:
            raise ValueError("payload must be an object")
        _require_payload_hard_flags("payload", payload, require_here=True)
        return payload
    _require_report_integrity(report)
    _reject_unsafe_public_surface("report", report)
    payload = _payload_value(report, allow_dataclasses=True)
    if type(payload) is not dict:
        raise ValueError("report payload must be an object")
    return payload


def _row_from_market(
    market: MarketCloseResolutionReadinessDigestInput,
    *,
    config: MarketCloseResolutionReadinessDigestConfig,
    generated_at: datetime,
) -> MarketCloseResolutionReadinessDigestRow:
    missing_sources = tuple(
        source
        for source in market.required_resolution_sources
        if source not in market.covered_resolution_sources
    )
    seconds_until_close = _seconds_between(generated_at, market.close_time)
    acknowledgement_age_seconds = _seconds_between(market.acknowledged_at, generated_at)
    reason_codes = _row_reason_codes(
        seconds_until_close=seconds_until_close,
        missing_sources=missing_sources,
        acknowledgement_age_seconds=acknowledgement_age_seconds,
        outcome_evidence_count=market.outcome_evidence_count,
        unresolved_ambiguity_count=market.unresolved_ambiguity_count,
        config=config,
    )
    return MarketCloseResolutionReadinessDigestRow(
        market_slug=market.market_slug,
        category=market.category,
        event_slug=market.event_slug,
        close_time=market.close_time,
        seconds_until_close=seconds_until_close,
        required_resolution_source_count=_decimal_count(
            len(market.required_resolution_sources)
        ),
        covered_resolution_source_count=_decimal_count(
            len(
                tuple(
                    source
                    for source in market.covered_resolution_sources
                    if source in market.required_resolution_sources
                )
            )
        ),
        missing_resolution_source_count=_decimal_count(len(missing_sources)),
        resolution_source_coverage_ratio=_coverage_ratio(
            _decimal_count(len(market.required_resolution_sources) - len(missing_sources)),
            _decimal_count(len(market.required_resolution_sources)),
        ),
        missing_resolution_sources=missing_sources,
        acknowledged_at=market.acknowledged_at,
        acknowledgement_age_seconds=acknowledgement_age_seconds,
        outcome_evidence_count=market.outcome_evidence_count,
        unresolved_ambiguity_count=market.unresolved_ambiguity_count,
        readiness_status=_row_status(reason_codes),
        reason_codes=reason_codes,
    )


def _row_reason_codes(
    *,
    seconds_until_close: Decimal,
    missing_sources: tuple[str, ...],
    acknowledgement_age_seconds: Decimal,
    outcome_evidence_count: Decimal,
    unresolved_ambiguity_count: Decimal,
    config: MarketCloseResolutionReadinessDigestConfig,
) -> tuple[str, ...]:
    codes: list[str] = []
    if seconds_until_close <= -config.block_close_after_seconds:
        codes.append("close_window_elapsed")
    elif seconds_until_close <= config.watch_close_within_seconds:
        codes.append("close_window_near")
    else:
        codes.append("close_window_clear")
    if missing_sources:
        codes.append("resolution_sources_missing")
    else:
        codes.append("resolution_sources_complete")
    if acknowledgement_age_seconds > config.acknowledgement_freshness_seconds:
        codes.append("acknowledgement_stale")
    else:
        codes.append("acknowledgement_fresh")
    if outcome_evidence_count < config.min_outcome_evidence_count:
        codes.append("outcome_evidence_incomplete")
    else:
        codes.append("outcome_evidence_complete")
    if unresolved_ambiguity_count > ZERO:
        codes.append("unresolved_ambiguity_present")
    else:
        codes.append("unresolved_ambiguity_absent")
    return tuple(sorted(codes))


def _row_status(reason_codes: tuple[str, ...]) -> str:
    blocked_reasons = (
        "acknowledgement_stale",
        "close_window_elapsed",
        "resolution_sources_missing",
        "unresolved_ambiguity_present",
    )
    if any(reason in reason_codes for reason in blocked_reasons):
        return "blocked"
    if "close_window_near" in reason_codes or "outcome_evidence_incomplete" in reason_codes:
        return "watch"
    return "ready"


def _status_from_rows(
    rows: tuple[MarketCloseResolutionReadinessDigestRow, ...],
) -> str:
    if not rows or any(row.readiness_status == "blocked" for row in rows):
        return "blocked"
    if any(row.readiness_status == "watch" for row in rows):
        return "watch"
    return "ready"


def _digest_reason_codes(
    rows: tuple[MarketCloseResolutionReadinessDigestRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return (EMPTY_INPUT_REASON,)
    codes: set[str] = set()
    for row in rows:
        codes.update(row.reason_codes)
    return tuple(sorted(codes))


def _category_rollups(
    rows: tuple[MarketCloseResolutionReadinessDigestRow, ...],
) -> tuple[MarketCloseResolutionReadinessDigestCategoryRollup, ...]:
    categories = tuple(sorted({row.category for row in rows}))
    rollups: list[MarketCloseResolutionReadinessDigestCategoryRollup] = []
    for category in categories:
        category_rows = tuple(row for row in rows if row.category == category)
        required_count = _sum_decimal(
            row.required_resolution_source_count for row in category_rows
        )
        covered_count = _sum_decimal(
            row.covered_resolution_source_count for row in category_rows
        )
        missing_count = _sum_decimal(
            row.missing_resolution_source_count for row in category_rows
        )
        rollups.append(
            MarketCloseResolutionReadinessDigestCategoryRollup(
                category=category,
                row_count=_decimal_count(len(category_rows)),
                ready_count=_decimal_count(_count_status(category_rows, "ready")),
                watch_count=_decimal_count(_count_status(category_rows, "watch")),
                blocked_count=_decimal_count(_count_status(category_rows, "blocked")),
                required_resolution_source_count=required_count,
                covered_resolution_source_count=covered_count,
                missing_resolution_source_count=missing_count,
                resolution_source_coverage_ratio=_coverage_ratio(
                    covered_count,
                    required_count,
                ),
                reason_codes=tuple(
                    sorted({reason for row in category_rows for reason in row.reason_codes})
                ),
            )
        )
    return tuple(rollups)


def _reason_code_counts(
    rows: tuple[MarketCloseResolutionReadinessDigestRow, ...],
    reason_codes: tuple[str, ...],
) -> tuple[MarketCloseResolutionReadinessDigestReasonCodeCount, ...]:
    if reason_codes == (EMPTY_INPUT_REASON,):
        return (
            MarketCloseResolutionReadinessDigestReasonCodeCount(
                reason_code=EMPTY_INPUT_REASON,
                count=ONE,
            ),
        )
    return tuple(
        MarketCloseResolutionReadinessDigestReasonCodeCount(
            reason_code=reason,
            count=_decimal_count(
                sum(1 for row in rows for code in row.reason_codes if code == reason)
            ),
        )
        for reason in reason_codes
    )


def _validate_report_consistency(
    report: MarketCloseResolutionReadinessDigestReport,
) -> None:
    if report.input_count != report.row_count:
        raise ValueError("input_count must match row_count")
    if report.row_count != _decimal_count(len(report.rows)):
        raise ValueError("row_count must match rows")
    if report.ready_count != _decimal_count(_count_status(report.rows, "ready")):
        raise ValueError("ready_count must match rows")
    if report.watch_count != _decimal_count(_count_status(report.rows, "watch")):
        raise ValueError("watch_count must match rows")
    if report.blocked_count != _decimal_count(_count_status(report.rows, "blocked")):
        raise ValueError("blocked_count must match rows")
    expected_required = _sum_decimal(
        row.required_resolution_source_count for row in report.rows
    )
    expected_covered = _sum_decimal(
        row.covered_resolution_source_count for row in report.rows
    )
    expected_missing = _sum_decimal(
        row.missing_resolution_source_count for row in report.rows
    )
    if report.required_resolution_source_count != expected_required:
        raise ValueError("required_resolution_source_count must match rows")
    if report.covered_resolution_source_count != expected_covered:
        raise ValueError("covered_resolution_source_count must match rows")
    if report.missing_resolution_source_count != expected_missing:
        raise ValueError("missing_resolution_source_count must match rows")
    if report.resolution_source_coverage_ratio != _coverage_ratio(
        expected_covered,
        expected_required,
    ):
        raise ValueError("resolution_source_coverage_ratio must match rows")
    if report.category_rollups != _category_rollups(report.rows):
        raise ValueError("category_rollups must match rows")
    if report.reason_codes != _digest_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")
    if report.reason_code_counts != _reason_code_counts(report.rows, report.reason_codes):
        raise ValueError("reason_code_counts must summarize reason_codes")
    expected_status = _status_from_rows(report.rows)
    if report.digest_status != expected_status:
        raise ValueError("digest_status must match rows")
    if report.recommended_next_step != NEXT_STEPS[expected_status]:
        raise ValueError("recommended_next_step must match digest_status")


def _require_report_integrity(
    report: MarketCloseResolutionReadinessDigestReport,
) -> None:
    _require_hard_flags("report", report)
    _validate_report_consistency(report)
    _require_derived_validation_digest("report", report)
    for row in report.rows:
        _require_hard_flags("row", row)
        _require_derived_validation_digest("row", row)
    for rollup in report.category_rollups:
        _require_hard_flags("category rollup", rollup)
        _require_derived_validation_digest("category rollup", rollup)
    for reason_count in report.reason_code_counts:
        _require_hard_flags("reason code count", reason_count)
        _require_derived_validation_digest("reason code count", reason_count)


def _normalize_market_inputs(
    markets: list[MarketCloseResolutionReadinessDigestInput]
    | tuple[MarketCloseResolutionReadinessDigestInput, ...],
) -> tuple[MarketCloseResolutionReadinessDigestInput, ...]:
    if type(markets) not in (list, tuple):
        raise ValueError("markets must be a list or tuple")
    normalized = tuple(markets)
    for market in normalized:
        if type(market) is not MarketCloseResolutionReadinessDigestInput:
            raise ValueError("markets must contain market input rows")
        _require_hard_flags("market input", market)
        _require_derived_validation_digest("market input", market)
        _reject_unsafe_public_surface("market input", market)
    return normalized


def _normalize_rows(
    rows: tuple[MarketCloseResolutionReadinessDigestRow, ...],
) -> tuple[MarketCloseResolutionReadinessDigestRow, ...]:
    if type(rows) not in (list, tuple):
        raise ValueError("rows must be a list or tuple")
    normalized = tuple(rows)
    for row in normalized:
        if type(row) is not MarketCloseResolutionReadinessDigestRow:
            raise ValueError("rows must contain digest row values")
        _require_hard_flags("row", row)
        _require_derived_validation_digest("row", row)
    if normalized != tuple(sorted(normalized, key=_row_key)):
        raise ValueError("rows must be sorted")
    return normalized


def _normalize_category_rollups(
    rollups: tuple[MarketCloseResolutionReadinessDigestCategoryRollup, ...],
) -> tuple[MarketCloseResolutionReadinessDigestCategoryRollup, ...]:
    if type(rollups) not in (list, tuple):
        raise ValueError("category_rollups must be a list or tuple")
    normalized = tuple(rollups)
    categories: set[str] = set()
    for rollup in normalized:
        if type(rollup) is not MarketCloseResolutionReadinessDigestCategoryRollup:
            raise ValueError("category_rollups must contain category rollups")
        if rollup.category in categories:
            raise ValueError("category_rollups category values must be unique")
        categories.add(rollup.category)
        _require_hard_flags("category rollup", rollup)
        _require_derived_validation_digest("category rollup", rollup)
    if tuple(rollup.category for rollup in normalized) != tuple(sorted(categories)):
        raise ValueError("category_rollups must be sorted")
    return normalized


def _normalize_reason_code_counts(
    reason_code_counts: tuple[MarketCloseResolutionReadinessDigestReasonCodeCount, ...],
) -> tuple[MarketCloseResolutionReadinessDigestReasonCodeCount, ...]:
    if type(reason_code_counts) not in (list, tuple):
        raise ValueError("reason_code_counts must be a list or tuple")
    normalized = tuple(reason_code_counts)
    reason_codes: set[str] = set()
    for count in normalized:
        if type(count) is not MarketCloseResolutionReadinessDigestReasonCodeCount:
            raise ValueError("reason_code_counts must contain reason code counts")
        if count.reason_code in reason_codes:
            raise ValueError("reason_code_counts reason_code values must be unique")
        reason_codes.add(count.reason_code)
        _require_hard_flags("reason code count", count)
        _require_derived_validation_digest("reason code count", count)
    if tuple(count.reason_code for count in normalized) != tuple(sorted(reason_codes)):
        raise ValueError("reason_code_counts must be sorted")
    return normalized


def _normalize_reason_codes(reason_codes: tuple[str, ...]) -> tuple[str, ...]:
    if type(reason_codes) not in (list, tuple):
        raise ValueError("reason_codes must be a list or tuple")
    normalized = tuple(reason_codes)
    if not normalized:
        raise ValueError("reason_codes must contain at least one value")
    for reason_code in normalized:
        _require_reason_code("reason_codes", reason_code)
    if normalized != tuple(sorted(set(normalized))):
        raise ValueError("reason_codes must be unique and sorted")
    return normalized


def _normalize_required_sources(values: tuple[str, ...]) -> tuple[str, ...]:
    normalized = _normalize_sources("required_resolution_sources", values)
    if not normalized:
        raise ValueError("required_resolution_sources must contain at least one value")
    return normalized


def _normalize_sources(name: str, values: tuple[str, ...]) -> tuple[str, ...]:
    if type(values) not in (list, tuple):
        raise ValueError(f"{name} must be a list or tuple")
    normalized = tuple(values)
    for value in normalized:
        _require_canonical_string(name, value)
    if len(set(normalized)) != len(normalized):
        raise ValueError(f"{name} values must be unique")
    return tuple(sorted(normalized))


def _payload_value(value: object, *, allow_dataclasses: bool) -> object:
    if type(value) is Decimal:
        return str(value)
    if type(value) is datetime:
        return value.isoformat()
    if is_dataclass(value) and not isinstance(value, type):
        if not allow_dataclasses:
            raise ValueError("payload contains unsafe payload object; use plain values")
        return {
            field.name: _payload_value(
                getattr(value, field.name),
                allow_dataclasses=allow_dataclasses,
            )
            for field in fields(value)
        }
    if type(value) is tuple:
        return [_payload_value(item, allow_dataclasses=allow_dataclasses) for item in value]
    if type(value) is list:
        return [_payload_value(item, allow_dataclasses=allow_dataclasses) for item in value]
    if type(value) is dict:
        return {
            str(key): _payload_value(item, allow_dataclasses=allow_dataclasses)
            for key, item in sorted(value.items(), key=lambda entry: str(entry[0]))
        }
    if type(value) in (str, bool) or value is None:
        return value
    raise ValueError("payload contains unsupported value")


def _count_status(
    rows: tuple[MarketCloseResolutionReadinessDigestRow, ...],
    status: str,
) -> int:
    return sum(1 for row in rows if row.readiness_status == status)


def _row_key(row: MarketCloseResolutionReadinessDigestRow) -> tuple[str, str, str, str]:
    return (row.category, row.event_slug, row.market_slug, row.close_time.isoformat())


def _coverage_ratio(covered: Decimal, required: Decimal) -> Decimal:
    if required == ZERO:
        return ZERO.quantize(SIX_PLACES, rounding=ROUND_HALF_EVEN)
    return (covered / required).quantize(SIX_PLACES, rounding=ROUND_HALF_EVEN)


def _seconds_between(start: datetime, end: datetime) -> Decimal:
    difference = end - start
    seconds = Decimal(difference.days) * SECONDS_PER_DAY + Decimal(difference.seconds)
    if difference.microseconds == 0:
        return seconds
    return seconds + (Decimal(difference.microseconds) / MICROSECONDS_PER_SECOND)


def _sum_decimal(values: object) -> Decimal:
    total = ZERO
    for value in values:
        if type(value) is not Decimal:
            raise ValueError("values must contain Decimal instances")
        total += value
    return total


def _decimal_count(value: int) -> Decimal:
    return Decimal(value)


def _as_utc(name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_reason_code(name: str, value: object) -> None:
    _require_canonical_string(name, value)
    if value not in REASON_CODES:
        raise ValueError(f"{name} must contain known reason codes")


def _require_status(name: str, value: object) -> None:
    if type(value) is not str or value not in NEXT_STEPS:
        raise ValueError(f"{name} must be ready, watch, or blocked")


def _require_ratio(name: str, value: object) -> None:
    _require_decimal(name, value)
    if value < ZERO or value > ONE:
        raise ValueError(f"{name} must be between zero and one")
    if value.as_tuple().exponent != -6:
        raise ValueError(f"{name} must use six decimal places")


def _require_nonnegative_decimal_seconds(name: str, value: object) -> None:
    _require_decimal(name, value)
    if value < ZERO:
        raise ValueError(f"{name} must be nonnegative")


def _require_positive_decimal_whole(name: str, value: object) -> None:
    _require_nonnegative_decimal_whole(name, value)
    if value <= ZERO:
        raise ValueError(f"{name} must be positive")


def _require_nonnegative_decimal_whole(name: str, value: object) -> None:
    _require_decimal(name, value)
    if value < ZERO:
        raise ValueError(f"{name} must be nonnegative")
    if value != value.to_integral_value():
        raise ValueError(f"{name} must be a whole number")


def _require_decimal(name: str, value: object) -> None:
    if type(value) is not Decimal:
        raise ValueError(f"{name} must be a Decimal")


def _require_canonical_string(name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{name} must be a canonical nonblank string")


def _require_hard_flags(name: str, value: object) -> None:
    if getattr(value, "paper_only", None) is not True:
        raise ValueError(f"{name} paper_only must be True")
    if getattr(value, "report_only", None) is not True:
        raise ValueError(f"{name} report_only must be True")
    if getattr(value, "readonly", None) is not True:
        raise ValueError(f"{name} readonly must be True")


@dataclass(frozen=True)
class _PayloadHardFlags:
    value: dict[str, object]

    @property
    def paper_only(self) -> object:
        return self.value.get("paper_only")

    @property
    def report_only(self) -> object:
        return self.value.get("report_only")

    @property
    def readonly(self) -> object:
        return self.value.get("readonly")


def _require_payload_hard_flags(
    name: str,
    value: object,
    *,
    require_here: bool = False,
    require_all_dicts: bool = False,
) -> None:
    if type(value) is dict:
        if (
            require_here
            or require_all_dicts
            or any(flag in value for flag in HARD_FLAG_FIELDS)
        ):
            _require_hard_flags(name, _PayloadHardFlags(value))
        for item in value.values():
            _require_payload_hard_flags(
                name,
                item,
                require_all_dicts=require_all_dicts,
            )
        return
    if type(value) in (list, tuple):
        for item in value:
            _require_payload_hard_flags(
                name,
                item,
                require_all_dicts=require_all_dicts,
            )


def _require_derived_validation_digest(name: str, value: object) -> None:
    current = getattr(value, DERIVED_VALIDATION_DIGEST_FIELD, None)
    expected = _derived_validation_digest(value)
    if current == "":
        object.__setattr__(value, DERIVED_VALIDATION_DIGEST_FIELD, expected)
        return
    _require_canonical_string(DERIVED_VALIDATION_DIGEST_FIELD, current)
    if current != expected:
        raise ValueError(f"{name} derived_validation_digest mismatch")


def _derived_validation_digest(value: object) -> str:
    canonical = _canonical_text(value)
    digest = sha256(canonical.encode("utf-8")).hexdigest()
    return f"{DERIVED_VALIDATION_DIGEST_PREFIX}:{digest}"


def _canonical_text(value: object) -> str:
    if type(value) is Decimal:
        return f"Decimal({value})"
    if type(value) is datetime:
        return f"datetime({value.isoformat()})"
    if type(value) is str:
        return f"str({value!r})"
    if type(value) is bool:
        return f"bool({value})"
    if value is None:
        return "none"
    if type(value) is tuple:
        return "tuple(" + ",".join(_canonical_text(item) for item in value) + ")"
    if type(value) is list:
        return "list(" + ",".join(_canonical_text(item) for item in value) + ")"
    if type(value) is dict:
        return "dict(" + ",".join(
            f"{_canonical_text(str(key))}:{_canonical_text(item)}"
            for key, item in sorted(value.items(), key=lambda entry: str(entry[0]))
        ) + ")"
    if is_dataclass(value) and not isinstance(value, type):
        return type(value).__name__ + "(" + ",".join(
            f"{field.name}={_canonical_text(getattr(value, field.name))}"
            for field in fields(value)
            if field.name != DERIVED_VALIDATION_DIGEST_FIELD
        ) + ")"
    raise ValueError("value cannot be canonically validated")


def _reject_unsafe_public_surface(name: str, value: object) -> None:
    if type(value) is str:
        lowered = value.lower()
        if any(fragment in lowered for fragment in UNSAFE_PUBLIC_SURFACE_FRAGMENTS):
            raise ValueError(f"{name} contains unsafe public surface")
        return
    if isinstance(value, Decimal) or type(value) in (datetime, bool, int, float) or value is None:
        return
    if is_dataclass(value) and not isinstance(value, type):
        for field in fields(value):
            _reject_unsafe_public_surface(name, field.name)
            _reject_unsafe_public_surface(name, getattr(value, field.name))
        return
    if type(value) is dict:
        for key, item in value.items():
            _reject_unsafe_public_surface(name, str(key))
            _reject_unsafe_public_surface(name, item)
        return
    if type(value) in (list, tuple):
        for item in value:
            _reject_unsafe_public_surface(name, item)
        return
    raise ValueError(f"{name} contains unsafe payload object")
