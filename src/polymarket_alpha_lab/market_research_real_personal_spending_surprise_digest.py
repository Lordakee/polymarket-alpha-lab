"""Pure report-only real personal spending surprise digest reducer."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, localcontext
from typing import Any


__all__ = (
    "DEFAULT_MARKET_RESEARCH_REAL_PERSONAL_SPENDING_SURPRISE_DIGEST_CONFIG_VERSION",
    "MarketResearchRealPersonalSpendingSurpriseDigestConfig",
    "RealPersonalSpendingSurpriseObservation",
    "RealPersonalSpendingSurpriseDigestRow",
    "RealPersonalSpendingSurpriseReasonCodeCount",
    "RealPersonalSpendingSurpriseDigestReport",
    "build_market_research_real_personal_spending_surprise_digest",
    "market_research_real_personal_spending_surprise_digest_payload",
)


DEFAULT_MARKET_RESEARCH_REAL_PERSONAL_SPENDING_SURPRISE_DIGEST_CONFIG_VERSION = (
    "market-research-real-personal-spending-surprise-digest-v0"
)
QUANTUM = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
DECIMAL_CONTEXT = Context(prec=64)

MATERIAL_SURPRISE_STATUS = "material_surprise"
INLINE_STATUS = "inline"
SURPRISE_STATUSES = (MATERIAL_SURPRISE_STATUS, INLINE_STATUS)
DIGEST_STATUSES = ("pass", "watch", "blocked")
STATUS_RANK = {
    MATERIAL_SURPRISE_STATUS: 0,
    INLINE_STATUS: 1,
}
UPSTREAM_REASON_CODES = (
    "bea_release",
    "spending_watch",
    "watchlist",
)
ROW_REASON_CODES = (
    "bea_release",
    "real_personal_spending_inline",
    "real_personal_spending_material_surprise",
    "source_fresh",
    "source_stale",
    "spending_watch",
    "surprise_direction_downside",
    "surprise_direction_inline",
    "surprise_direction_upside",
    "watchlist",
)
REPORT_REASON_CODES = (
    *ROW_REASON_CODES,
    "real_personal_spending_surprise_digest_empty",
)


def _join_parts(*parts: str) -> str:
    return "".join(parts)


UNSAFE_TEXT_FRAGMENTS = frozenset(
    (
        _join_parts("au", "th"),
        _join_parts("can", "cel"),
        _join_parts("cred", "ential"),
        _join_parts("data", "base"),
        _join_parts("ex", "change"),
        _join_parts("key"),
        _join_parts("net", "work"),
        _join_parts("ord", "er"),
        _join_parts("per", "sist"),
        _join_parts("pri", "vate"),
        _join_parts("sec", "ret"),
        _join_parts("sig", "n"),
        _join_parts("sub", "mit"),
        _join_parts("to", "ken"),
        _join_parts("wal", "let"),
        "http://",
        "https://",
    ),
)


@dataclass(frozen=True)
class MarketResearchRealPersonalSpendingSurpriseDigestConfig:
    config_version: str = (
        DEFAULT_MARKET_RESEARCH_REAL_PERSONAL_SPENDING_SURPRISE_DIGEST_CONFIG_VERSION
    )
    min_abs_surprise: Decimal = Decimal("0.003000")
    min_abs_surprise_ratio: Decimal = Decimal("0.250000")
    max_source_age_seconds: Decimal = Decimal("300.000000")
    stale_confidence_cap: Decimal = Decimal("0.250000")
    inline_confidence_cap: Decimal = Decimal("0.500000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            MarketResearchRealPersonalSpendingSurpriseDigestConfig,
            "config",
        )
        _require_canonical_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_MARKET_RESEARCH_REAL_PERSONAL_SPENDING_SURPRISE_DIGEST_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "min_abs_surprise",
            "min_abs_surprise_ratio",
            "max_source_age_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in ("stale_confidence_cap", "inline_confidence_cap"):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class RealPersonalSpendingSurpriseObservation:
    market_slug: str
    question: str
    actual_change_pct: Decimal
    consensus_change_pct: Decimal
    previous_change_pct: Decimal
    release_observed_at: datetime
    base_confidence: Decimal
    release_reference: str
    upstream_reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, RealPersonalSpendingSurpriseObservation, "observation")
        for field_name in ("market_slug", "question", "release_reference"):
            _require_safe_public_text(field_name, getattr(self, field_name))
        for field_name in (
            "actual_change_pct",
            "consensus_change_pct",
            "previous_change_pct",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "release_observed_at",
            _as_utc("release_observed_at", self.release_observed_at),
        )
        object.__setattr__(
            self,
            "base_confidence",
            _normalize_probability("base_confidence", self.base_confidence),
        )
        object.__setattr__(
            self,
            "upstream_reason_codes",
            _normalize_reason_codes(
                "upstream_reason_codes",
                self.upstream_reason_codes,
                UPSTREAM_REASON_CODES,
            ),
        )
        _require_hard_flags("observation", self)


@dataclass(frozen=True)
class RealPersonalSpendingSurpriseDigestRow:
    market_slug: str
    question: str
    actual_change_pct: Decimal
    consensus_change_pct: Decimal
    previous_change_pct: Decimal
    surprise_delta: Decimal
    surprise_ratio: Decimal
    absolute_surprise_ratio: Decimal
    release_observed_at: datetime
    source_age_seconds: Decimal
    base_confidence: Decimal
    confidence_cap: Decimal
    capped_confidence: Decimal
    surprise_status: str
    release_reference: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, RealPersonalSpendingSurpriseDigestRow, "row")
        for field_name in ("market_slug", "question", "release_reference"):
            _require_safe_public_text(field_name, getattr(self, field_name))
        for field_name in (
            "actual_change_pct",
            "consensus_change_pct",
            "previous_change_pct",
            "surprise_delta",
            "surprise_ratio",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in ("absolute_surprise_ratio", "source_age_seconds"):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in ("base_confidence", "confidence_cap", "capped_confidence"):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "release_observed_at",
            _as_utc("release_observed_at", self.release_observed_at),
        )
        _require_surprise_status("surprise_status", self.surprise_status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, ROW_REASON_CODES),
        )
        _validate_row_consistency(self)
        _require_hard_flags("row", self)


@dataclass(frozen=True)
class RealPersonalSpendingSurpriseReasonCodeCount:
    reason_code: str
    count: Decimal
    row_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            RealPersonalSpendingSurpriseReasonCodeCount,
            "reason code count",
        )
        _require_member("reason_code", self.reason_code, REPORT_REASON_CODES)
        object.__setattr__(
            self,
            "count",
            _normalize_nonnegative_count_decimal("count", self.count),
        )
        object.__setattr__(
            self,
            "row_ratio",
            _normalize_probability("row_ratio", self.row_ratio),
        )
        _require_hard_flags("reason code count", self)


@dataclass(frozen=True)
class RealPersonalSpendingSurpriseDigestReport:
    generated_at: datetime
    config_version: str
    input_count: Decimal
    row_count: Decimal
    material_surprise_count: Decimal
    upside_surprise_count: Decimal
    downside_surprise_count: Decimal
    inline_count: Decimal
    stale_source_count: Decimal
    max_absolute_surprise_ratio: Decimal
    digest_status: str
    recommended_next_step: str
    reason_codes: tuple[str, ...]
    reason_code_counts: tuple[RealPersonalSpendingSurpriseReasonCodeCount, ...]
    rows: tuple[RealPersonalSpendingSurpriseDigestRow, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, RealPersonalSpendingSurpriseDigestReport, "report")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_MARKET_RESEARCH_REAL_PERSONAL_SPENDING_SURPRISE_DIGEST_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "input_count",
            "row_count",
            "material_surprise_count",
            "upside_surprise_count",
            "downside_surprise_count",
            "inline_count",
            "stale_source_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_count_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "max_absolute_surprise_ratio",
            _normalize_nonnegative_decimal(
                "max_absolute_surprise_ratio",
                self.max_absolute_surprise_ratio,
            ),
        )
        _require_member("digest_status", self.digest_status, DIGEST_STATUSES)
        _require_canonical_string("recommended_next_step", self.recommended_next_step)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, REPORT_REASON_CODES),
        )
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        _validate_report_consistency(self)
        _require_hard_flags("report", self)


def build_market_research_real_personal_spending_surprise_digest(
    observations: Iterable[RealPersonalSpendingSurpriseObservation],
    *,
    config: MarketResearchRealPersonalSpendingSurpriseDigestConfig,
    generated_at: datetime,
) -> RealPersonalSpendingSurpriseDigestReport:
    if type(config) is not MarketResearchRealPersonalSpendingSurpriseDigestConfig:
        raise ValueError(
            "config must be a MarketResearchRealPersonalSpendingSurpriseDigestConfig",
        )
    generated_at = _as_utc("generated_at", generated_at)
    _require_hard_flags("config", config)
    normalized = _normalize_observations(observations)
    rows = tuple(
        sorted(
            (
                _row_from_observation(value, config=config, generated_at=generated_at)
                for value in normalized
            ),
            key=_row_sort_key,
        ),
    )
    reason_codes = _report_reason_codes(rows)
    digest_status = _digest_status(rows)
    return RealPersonalSpendingSurpriseDigestReport(
        generated_at=generated_at,
        config_version=config.config_version,
        input_count=_count_decimal(len(normalized)),
        row_count=_count_decimal(len(rows)),
        material_surprise_count=_status_count(rows, MATERIAL_SURPRISE_STATUS),
        upside_surprise_count=_reason_count(rows, "surprise_direction_upside"),
        downside_surprise_count=_reason_count(rows, "surprise_direction_downside"),
        inline_count=_status_count(rows, INLINE_STATUS),
        stale_source_count=_reason_count(rows, "source_stale"),
        max_absolute_surprise_ratio=_max_row_decimal(rows, "absolute_surprise_ratio"),
        digest_status=digest_status,
        recommended_next_step=_recommended_next_step(digest_status),
        reason_codes=reason_codes,
        reason_code_counts=_reason_code_counts(reason_codes, rows),
        rows=rows,
    )


def market_research_real_personal_spending_surprise_digest_payload(
    report: RealPersonalSpendingSurpriseDigestReport,
) -> dict[str, Any]:
    if type(report) is not RealPersonalSpendingSurpriseDigestReport:
        raise ValueError(
            "report must be a RealPersonalSpendingSurpriseDigestReport",
        )
    return _payload_value(report)


def _row_from_observation(
    value: RealPersonalSpendingSurpriseObservation,
    *,
    config: MarketResearchRealPersonalSpendingSurpriseDigestConfig,
    generated_at: datetime,
) -> RealPersonalSpendingSurpriseDigestRow:
    surprise_delta = _quantize_decimal(value.actual_change_pct - value.consensus_change_pct)
    surprise_ratio = _surprise_ratio(surprise_delta, value.consensus_change_pct)
    absolute_surprise_ratio = _quantize_decimal(abs(surprise_ratio))
    source_age_seconds = _seconds_between(generated_at, value.release_observed_at)
    source_fresh = source_age_seconds <= config.max_source_age_seconds
    material = (
        abs(surprise_delta) >= config.min_abs_surprise
        and absolute_surprise_ratio >= config.min_abs_surprise_ratio
    )
    status = MATERIAL_SURPRISE_STATUS if material else INLINE_STATUS
    confidence_cap = _confidence_cap(
        status=status,
        source_fresh=source_fresh,
        config=config,
    )
    reason_codes = _row_reason_codes(
        value.upstream_reason_codes,
        status=status,
        surprise_delta=surprise_delta,
        source_fresh=source_fresh,
    )
    return RealPersonalSpendingSurpriseDigestRow(
        market_slug=value.market_slug,
        question=value.question,
        actual_change_pct=value.actual_change_pct,
        consensus_change_pct=value.consensus_change_pct,
        previous_change_pct=value.previous_change_pct,
        surprise_delta=surprise_delta,
        surprise_ratio=surprise_ratio,
        absolute_surprise_ratio=absolute_surprise_ratio,
        release_observed_at=value.release_observed_at,
        source_age_seconds=source_age_seconds,
        base_confidence=value.base_confidence,
        confidence_cap=confidence_cap,
        capped_confidence=min(value.base_confidence, confidence_cap),
        surprise_status=status,
        release_reference=value.release_reference,
        reason_codes=reason_codes,
    )


def _surprise_ratio(surprise_delta: Decimal, consensus_change_pct: Decimal) -> Decimal:
    denominator = abs(consensus_change_pct)
    if denominator == ZERO:
        if surprise_delta == ZERO:
            return _quantize_decimal(ZERO)
        return _quantize_decimal(ONE if surprise_delta > ZERO else -ONE)
    return _quantize_decimal(surprise_delta / denominator)


def _confidence_cap(
    *,
    status: str,
    source_fresh: bool,
    config: MarketResearchRealPersonalSpendingSurpriseDigestConfig,
) -> Decimal:
    caps = [ONE]
    if status == INLINE_STATUS:
        caps.append(config.inline_confidence_cap)
    if not source_fresh:
        caps.append(config.stale_confidence_cap)
    return _quantize_decimal(min(caps))


def _row_reason_codes(
    upstream_reason_codes: tuple[str, ...],
    *,
    status: str,
    surprise_delta: Decimal,
    source_fresh: bool,
) -> tuple[str, ...]:
    reason_codes = list(upstream_reason_codes)
    if status == MATERIAL_SURPRISE_STATUS:
        reason_codes.append("real_personal_spending_material_surprise")
        if surprise_delta > ZERO:
            reason_codes.append("surprise_direction_upside")
        elif surprise_delta < ZERO:
            reason_codes.append("surprise_direction_downside")
        else:
            reason_codes.append("surprise_direction_inline")
    else:
        reason_codes.append("real_personal_spending_inline")
        reason_codes.append("surprise_direction_inline")
    reason_codes.append("source_fresh" if source_fresh else "source_stale")
    canonical_reason_codes = tuple(
        reason_code for reason_code in ROW_REASON_CODES if reason_code in set(reason_codes)
    )
    return _normalize_reason_codes("reason_codes", canonical_reason_codes, ROW_REASON_CODES)


def _normalize_observations(
    observations: Iterable[RealPersonalSpendingSurpriseObservation],
) -> tuple[RealPersonalSpendingSurpriseObservation, ...]:
    if isinstance(observations, (str, bytes)) or not isinstance(observations, Iterable):
        raise ValueError("observations must be an iterable")
    normalized = tuple(observations)
    for value in normalized:
        if type(value) is not RealPersonalSpendingSurpriseObservation:
            raise ValueError(
                "observations must contain RealPersonalSpendingSurpriseObservation",
            )
        _require_hard_flags("observation", value)
    return normalized


def _normalize_rows(
    rows: Iterable[RealPersonalSpendingSurpriseDigestRow],
) -> tuple[RealPersonalSpendingSurpriseDigestRow, ...]:
    if isinstance(rows, (str, bytes)) or not isinstance(rows, Iterable):
        raise ValueError("rows must be an iterable")
    normalized = tuple(rows)
    for row in normalized:
        if type(row) is not RealPersonalSpendingSurpriseDigestRow:
            raise ValueError("rows must contain RealPersonalSpendingSurpriseDigestRow")
        _require_hard_flags("row", row)
    expected = tuple(sorted(normalized, key=_row_sort_key))
    if normalized != expected:
        raise ValueError("rows must use deterministic ordering")
    return normalized


def _normalize_reason_code_counts(
    values: Iterable[RealPersonalSpendingSurpriseReasonCodeCount],
) -> tuple[RealPersonalSpendingSurpriseReasonCodeCount, ...]:
    if isinstance(values, (str, bytes)) or not isinstance(values, Iterable):
        raise ValueError("reason_code_counts must contain reason code counts")
    normalized = tuple(values)
    for value in normalized:
        if type(value) is not RealPersonalSpendingSurpriseReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "RealPersonalSpendingSurpriseReasonCodeCount",
            )
        _require_hard_flags("reason code count", value)
    expected = tuple(
        sorted(normalized, key=lambda value: REPORT_REASON_CODES.index(value.reason_code)),
    )
    if normalized != expected:
        raise ValueError("reason_code_counts must use deterministic ordering")
    return normalized


def _validate_row_consistency(row: RealPersonalSpendingSurpriseDigestRow) -> None:
    expected_delta = _quantize_decimal(row.actual_change_pct - row.consensus_change_pct)
    if row.surprise_delta != expected_delta:
        raise ValueError("surprise_delta must match actual and consensus values")
    if row.surprise_ratio != _surprise_ratio(row.surprise_delta, row.consensus_change_pct):
        raise ValueError("surprise_ratio must match surprise_delta and consensus")
    if row.absolute_surprise_ratio != _quantize_decimal(abs(row.surprise_ratio)):
        raise ValueError("absolute_surprise_ratio must match surprise_ratio")
    if row.capped_confidence > row.confidence_cap:
        raise ValueError("capped_confidence must not exceed confidence_cap")
    expected_reason = {
        MATERIAL_SURPRISE_STATUS: "real_personal_spending_material_surprise",
        INLINE_STATUS: "real_personal_spending_inline",
    }[row.surprise_status]
    if expected_reason not in row.reason_codes:
        raise ValueError("surprise_status must match reason_codes")
    has_material_reason = (
        "real_personal_spending_material_surprise" in row.reason_codes
    )
    has_inline_reason = "real_personal_spending_inline" in row.reason_codes
    if sum((has_material_reason, has_inline_reason)) != 1:
        raise ValueError("reason_codes must match surprise_status")
    if has_material_reason != (row.surprise_status == MATERIAL_SURPRISE_STATUS):
        raise ValueError("reason_codes must match surprise_status")
    if has_inline_reason != (row.surprise_status == INLINE_STATUS):
        raise ValueError("reason_codes must match surprise_status")
    direction_reasons = (
        "surprise_direction_downside",
        "surprise_direction_inline",
        "surprise_direction_upside",
    )
    if sum(reason_code in row.reason_codes for reason_code in direction_reasons) != 1:
        raise ValueError("reason_codes must contain one surprise direction")
    if row.surprise_status == INLINE_STATUS:
        expected_direction_reason = "surprise_direction_inline"
    elif row.surprise_delta > ZERO:
        expected_direction_reason = "surprise_direction_upside"
    elif row.surprise_delta < ZERO:
        expected_direction_reason = "surprise_direction_downside"
    else:
        expected_direction_reason = "surprise_direction_inline"
    if expected_direction_reason not in row.reason_codes:
        raise ValueError("reason_codes must match surprise_delta")
    if sum(
        reason_code in row.reason_codes
        for reason_code in ("source_fresh", "source_stale")
    ) != 1:
        raise ValueError("reason_codes must contain one source freshness state")


def _validate_report_consistency(report: RealPersonalSpendingSurpriseDigestReport) -> None:
    if report.row_count != _count_decimal(len(report.rows)):
        raise ValueError("row_count must match rows")
    if report.input_count != report.row_count:
        raise ValueError("input_count must match rows")
    if report.material_surprise_count != _status_count(
        report.rows,
        MATERIAL_SURPRISE_STATUS,
    ):
        raise ValueError("material_surprise_count must match rows")
    if report.inline_count != _status_count(report.rows, INLINE_STATUS):
        raise ValueError("inline_count must match rows")
    if report.material_surprise_count + report.inline_count != report.row_count:
        raise ValueError("status counts must match row_count")
    if report.upside_surprise_count != _reason_count(
        report.rows,
        "surprise_direction_upside",
    ):
        raise ValueError("upside_surprise_count must match rows")
    if report.downside_surprise_count != _reason_count(
        report.rows,
        "surprise_direction_downside",
    ):
        raise ValueError("downside_surprise_count must match rows")
    if report.stale_source_count != _reason_count(report.rows, "source_stale"):
        raise ValueError("stale_source_count must match rows")
    if report.max_absolute_surprise_ratio != _max_row_decimal(
        report.rows,
        "absolute_surprise_ratio",
    ):
        raise ValueError("max_absolute_surprise_ratio must match rows")
    if report.digest_status != _digest_status(report.rows):
        raise ValueError("digest_status must match rows")
    if report.recommended_next_step != _recommended_next_step(report.digest_status):
        raise ValueError("recommended_next_step must match digest_status")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")
    if report.reason_code_counts != _reason_code_counts(
        report.reason_codes,
        report.rows,
    ):
        raise ValueError("reason_code_counts must match reason_codes")


def _report_reason_codes(
    rows: tuple[RealPersonalSpendingSurpriseDigestRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return ("real_personal_spending_surprise_digest_empty",)
    reason_codes = {reason_code for row in rows for reason_code in row.reason_codes}
    return _normalize_reason_codes(
        "reason_codes",
        tuple(reason_code for reason_code in REPORT_REASON_CODES if reason_code in reason_codes),
        REPORT_REASON_CODES,
    )


def _reason_code_counts(
    reason_codes: tuple[str, ...],
    rows: tuple[RealPersonalSpendingSurpriseDigestRow, ...],
) -> tuple[RealPersonalSpendingSurpriseReasonCodeCount, ...]:
    row_count = _count_decimal(len(rows))
    if reason_codes == ("real_personal_spending_surprise_digest_empty",):
        return (
            RealPersonalSpendingSurpriseReasonCodeCount(
                reason_code="real_personal_spending_surprise_digest_empty",
                count=ONE,
                row_ratio=ZERO,
            ),
        )
    return tuple(
        RealPersonalSpendingSurpriseReasonCodeCount(
            reason_code=reason_code,
            count=_reason_count(rows, reason_code),
            row_ratio=_ratio(_reason_count(rows, reason_code), row_count),
        )
        for reason_code in reason_codes
    )


def _digest_status(rows: tuple[RealPersonalSpendingSurpriseDigestRow, ...]) -> str:
    if not rows:
        return "blocked"
    if any("source_stale" in row.reason_codes for row in rows):
        return "blocked"
    if any(row.surprise_status == MATERIAL_SURPRISE_STATUS for row in rows):
        return "watch"
    return "pass"


def _recommended_next_step(status: str) -> str:
    if status == "pass":
        return "allow_report_only_real_personal_spending_surprise_screening"
    if status == "watch":
        return "monitor_report_only_real_personal_spending_surprise_screening"
    return "block_report_only_real_personal_spending_surprise_screening"


def _status_count(
    rows: tuple[RealPersonalSpendingSurpriseDigestRow, ...],
    status: str,
) -> Decimal:
    return _count_decimal(sum(1 for row in rows if row.surprise_status == status))


def _reason_count(
    rows: tuple[RealPersonalSpendingSurpriseDigestRow, ...],
    reason_code: str,
) -> Decimal:
    return _count_decimal(sum(1 for row in rows if reason_code in row.reason_codes))


def _max_row_decimal(
    rows: tuple[RealPersonalSpendingSurpriseDigestRow, ...],
    field_name: str,
) -> Decimal:
    if not rows:
        return _quantize_decimal(ZERO)
    return max(getattr(row, field_name) for row in rows)


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return _quantize_decimal(numerator / denominator)


def _seconds_between(later: datetime, earlier: datetime) -> Decimal:
    delta = later - earlier
    if delta.days < 0:
        raise ValueError("release_observed_at must not be after generated_at")
    whole_seconds = Decimal(delta.days * 86400 + delta.seconds)
    fractional_seconds = Decimal(delta.microseconds) / Decimal("1000000")
    return _quantize_decimal(whole_seconds + fractional_seconds)


def _count_decimal(value: int) -> Decimal:
    return _quantize_decimal(Decimal(value))


def _normalize_probability(field_name: str, value: object) -> Decimal:
    normalized = _normalize_nonnegative_decimal(field_name, value)
    if normalized > ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return normalized


def _normalize_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _normalize_nonnegative_count_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_nonnegative_decimal(field_name, value)
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{field_name} must be integral")
    return normalized


def _normalize_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return _quantize_decimal(value)


def _quantize_decimal(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(QUANTUM)


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be UTC-aware")
    return value.astimezone(UTC)


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")


def _require_safe_public_text(field_name: str, value: object) -> None:
    _require_canonical_string(field_name, value)
    lowered = value.lower()
    if any(fragment in lowered for fragment in UNSAFE_TEXT_FRAGMENTS):
        raise ValueError(f"{field_name} must be public and redacted")


def _require_surprise_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in SURPRISE_STATUSES:
        raise ValueError(f"{field_name} must be material_surprise or inline")


def _require_member(
    field_name: str,
    value: object,
    allowed: tuple[str, ...],
) -> None:
    if type(value) is not str or value not in allowed:
        raise ValueError(f"{field_name} must be a supported value")


def _normalize_reason_codes(
    field_name: str,
    reason_codes: Iterable[str],
    allowed: tuple[str, ...],
) -> tuple[str, ...]:
    if isinstance(reason_codes, (str, bytes)) or not isinstance(reason_codes, Iterable):
        raise ValueError(f"{field_name} must be an iterable")
    normalized = tuple(reason_codes)
    for reason_code in normalized:
        _require_canonical_string("reason_code", reason_code)
        if reason_code not in allowed:
            raise ValueError(f"{field_name} must be supported reason codes")
    if len(set(normalized)) != len(normalized):
        raise ValueError(f"{field_name} must be unique")
    expected = tuple(reason_code for reason_code in allowed if reason_code in normalized)
    if normalized != expected:
        raise ValueError(f"{field_name} must use deterministic ordering")
    return normalized


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if getattr(value, field_name, None) is not True:
            raise ValueError(f"{label} {field_name} must be True")


def _require_exact_type(value: object, type_: type[object], label: str) -> None:
    if type(value) is not type_:
        raise ValueError(f"{label} must be exactly {type_.__name__}")


def _row_sort_key(
    row: RealPersonalSpendingSurpriseDigestRow,
) -> tuple[Decimal, Decimal, str, str, str, datetime, Decimal, Decimal, Decimal]:
    return (
        Decimal(STATUS_RANK[row.surprise_status]),
        -row.absolute_surprise_ratio,
        row.market_slug,
        row.question,
        row.release_reference,
        row.release_observed_at,
        row.actual_change_pct,
        row.consensus_change_pct,
        row.previous_change_pct,
    )


def _payload_value(value: object) -> Any:
    if isinstance(value, Decimal):
        return f"{value:.6f}"
    if type(value) is datetime:
        return value.isoformat()
    if is_dataclass(value) and not isinstance(value, type):
        return {
            field.name: _payload_value(getattr(value, field.name))
            for field in fields(value)
        }
    if isinstance(value, tuple):
        return [_payload_value(item) for item in value]
    return value
