"""Pure report-only crypto ETF approval delay digest reducer."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from typing import Any


__all__ = (
    "DEFAULT_MARKET_RESEARCH_CRYPTO_ETF_APPROVAL_DELAY_DIGEST_CONFIG_VERSION",
    "CryptoEtfApprovalDelayDigestConfig",
    "CryptoEtfApprovalDelayObservation",
    "CryptoEtfApprovalDelayDigestRow",
    "CryptoEtfApprovalDelayReasonCodeCount",
    "CryptoEtfApprovalDelayDigestReport",
    "build_market_research_crypto_etf_approval_delay_digest",
    "market_research_crypto_etf_approval_delay_digest_payload",
)


DEFAULT_MARKET_RESEARCH_CRYPTO_ETF_APPROVAL_DELAY_DIGEST_CONFIG_VERSION = (
    "market-research-crypto-etf-approval-delay-digest-v0"
)

QUANTUM = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
NEAR_DEADLINE_DAYS = Decimal("14.000000")
DELAYED_AMENDMENT_DAYS = Decimal("30.000000")
COMMENT_PRESSURE_Z_SCORE = Decimal("2.000000")
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)

DELAY_DIRECTION = "approval_delay"
ROUTINE_DIRECTION = "approval_routine"
DELAY_DIRECTIONS = (DELAY_DIRECTION, ROUTINE_DIRECTION)

BLOCKED_STATUS = "blocked"
WATCH_STATUS = "watch"
PASS_STATUS = "pass"
DELAY_STATUSES = (BLOCKED_STATUS, WATCH_STATUS, PASS_STATUS)
STATUS_RANK = {
    BLOCKED_STATUS: Decimal("0.000000"),
    WATCH_STATUS: Decimal("1.000000"),
    PASS_STATUS: Decimal("2.000000"),
}

RECOMMENDED_NEXT_STEPS = {
    BLOCKED_STATUS: (
        "block_report_only_market_research_crypto_etf_approval_delay_digest"
    ),
    WATCH_STATUS: (
        "monitor_report_only_market_research_crypto_etf_approval_delay_digest"
    ),
    PASS_STATUS: (
        "allow_report_only_market_research_crypto_etf_approval_delay_digest"
    ),
}


@dataclass(frozen=True)
class CryptoEtfApprovalDelayDigestConfig:
    config_version: str = (
        DEFAULT_MARKET_RESEARCH_CRYPTO_ETF_APPROVAL_DELAY_DIGEST_CONFIG_VERSION
    )
    watch_delay_probability: Decimal = Decimal("0.400000")
    blocked_delay_probability: Decimal = Decimal("0.700000")
    max_source_age_seconds: Decimal = Decimal("1800.000000")
    stale_confidence_cap: Decimal = Decimal("0.300000")
    routine_confidence_cap: Decimal = Decimal("0.650000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, CryptoEtfApprovalDelayDigestConfig, "config")
        _require_canonical_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_MARKET_RESEARCH_CRYPTO_ETF_APPROVAL_DELAY_DIGEST_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "watch_delay_probability",
            "blocked_delay_probability",
            "max_source_age_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in ("stale_confidence_cap", "routine_confidence_cap"):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        if self.watch_delay_probability > self.blocked_delay_probability:
            raise ValueError(
                "watch_delay_probability must not exceed blocked_delay_probability",
            )
        _require_hard_flags(self)


@dataclass(frozen=True)
class CryptoEtfApprovalDelayObservation:
    source_id: str
    proposal_id: str
    issuer_name: str
    asset_symbol: str
    review_stage: str
    days_until_deadline: Decimal
    delay_probability: Decimal
    comment_volume_z_score: Decimal
    amendment_age_days: Decimal
    source_confidence: Decimal
    observed_at: datetime
    upstream_reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, CryptoEtfApprovalDelayObservation, "observation")
        for field_name in (
            "source_id",
            "proposal_id",
            "issuer_name",
            "asset_symbol",
            "review_stage",
        ):
            _require_canonical_string(field_name, getattr(self, field_name))
        for field_name in (
            "days_until_deadline",
            "comment_volume_z_score",
            "amendment_age_days",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "delay_probability",
            _normalize_probability("delay_probability", self.delay_probability),
        )
        object.__setattr__(
            self,
            "source_confidence",
            _normalize_probability("source_confidence", self.source_confidence),
        )
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        object.__setattr__(
            self,
            "upstream_reason_codes",
            _normalize_reason_codes(self.upstream_reason_codes),
        )
        _require_hard_flags(self)


@dataclass(frozen=True)
class CryptoEtfApprovalDelayDigestRow:
    source_id: str
    proposal_id: str
    issuer_name: str
    asset_symbol: str
    review_stage: str
    days_until_deadline: Decimal
    delay_probability: Decimal
    comment_volume_z_score: Decimal
    amendment_age_days: Decimal
    source_confidence: Decimal
    observed_at: datetime
    source_age_seconds: Decimal
    confidence_cap: Decimal
    capped_confidence: Decimal
    delay_direction: str
    delay_status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, CryptoEtfApprovalDelayDigestRow, "row")
        for field_name in (
            "source_id",
            "proposal_id",
            "issuer_name",
            "asset_symbol",
            "review_stage",
        ):
            _require_canonical_string(field_name, getattr(self, field_name))
        for field_name in (
            "days_until_deadline",
            "comment_volume_z_score",
            "amendment_age_days",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "delay_probability",
            _normalize_probability("delay_probability", self.delay_probability),
        )
        object.__setattr__(
            self,
            "source_confidence",
            _normalize_probability("source_confidence", self.source_confidence),
        )
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        object.__setattr__(
            self,
            "source_age_seconds",
            _normalize_nonnegative_decimal("source_age_seconds", self.source_age_seconds),
        )
        for field_name in ("confidence_cap", "capped_confidence"):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        _require_member("delay_direction", self.delay_direction, DELAY_DIRECTIONS)
        _require_member("delay_status", self.delay_status, DELAY_STATUSES)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes),
        )
        _validate_row(self)
        _require_hard_flags(self)


@dataclass(frozen=True)
class CryptoEtfApprovalDelayReasonCodeCount:
    reason_code: str
    count: Decimal
    row_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            CryptoEtfApprovalDelayReasonCodeCount,
            "reason_code_count",
        )
        _require_canonical_string("reason_code", self.reason_code)
        object.__setattr__(self, "count", _normalize_nonnegative_decimal("count", self.count))
        object.__setattr__(
            self,
            "row_ratio",
            _normalize_probability("row_ratio", self.row_ratio),
        )
        _require_hard_flags(self)


@dataclass(frozen=True)
class CryptoEtfApprovalDelayDigestReport:
    generated_at: datetime
    config_version: str
    input_count: Decimal
    row_count: Decimal
    blocked_delay_count: Decimal
    watch_delay_count: Decimal
    routine_count: Decimal
    stale_source_count: Decimal
    near_deadline_count: Decimal
    max_delay_probability: Decimal
    average_delay_probability: Decimal
    digest_status: str
    recommended_next_step: str
    rows: tuple[CryptoEtfApprovalDelayDigestRow, ...]
    reason_codes: tuple[str, ...]
    reason_code_counts: tuple[CryptoEtfApprovalDelayReasonCodeCount, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, CryptoEtfApprovalDelayDigestReport, "report")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_MARKET_RESEARCH_CRYPTO_ETF_APPROVAL_DELAY_DIGEST_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "input_count",
            "row_count",
            "blocked_delay_count",
            "watch_delay_count",
            "routine_count",
            "stale_source_count",
            "near_deadline_count",
            "max_delay_probability",
            "average_delay_probability",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        _require_member("digest_status", self.digest_status, DELAY_STATUSES)
        _require_canonical_string("recommended_next_step", self.recommended_next_step)
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        object.__setattr__(self, "reason_codes", _normalize_reason_codes(self.reason_codes))
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        _validate_report(self)
        _require_hard_flags(self)


def build_market_research_crypto_etf_approval_delay_digest(
    inputs: Iterable[CryptoEtfApprovalDelayObservation],
    *,
    config: CryptoEtfApprovalDelayDigestConfig,
    generated_at: datetime,
) -> CryptoEtfApprovalDelayDigestReport:
    if type(config) is not CryptoEtfApprovalDelayDigestConfig:
        raise ValueError("config must be exactly CryptoEtfApprovalDelayDigestConfig")
    _require_hard_flags(config)
    generated_at = _as_utc("generated_at", generated_at)
    normalized = _normalize_inputs(inputs)
    rows = tuple(
        sorted(
            (
                _row_from_observation(
                    value,
                    config=config,
                    generated_at=generated_at,
                )
                for value in normalized
            ),
            key=_row_sort_key,
        ),
    )
    reason_codes = _report_reason_codes(rows)
    row_count = _count_decimal(len(rows))
    return CryptoEtfApprovalDelayDigestReport(
        generated_at=generated_at,
        config_version=config.config_version,
        input_count=_count_decimal(len(normalized)),
        row_count=row_count,
        blocked_delay_count=_status_count(rows, BLOCKED_STATUS),
        watch_delay_count=_status_count(rows, WATCH_STATUS),
        routine_count=_status_count(rows, PASS_STATUS),
        stale_source_count=_reason_count(rows, "source_stale"),
        near_deadline_count=_reason_count(rows, "deadline_near"),
        max_delay_probability=_max_row_decimal(rows, "delay_probability"),
        average_delay_probability=_ratio(
            _sum_decimal(row.delay_probability for row in rows),
            row_count,
        ),
        digest_status=_digest_status(rows),
        recommended_next_step=RECOMMENDED_NEXT_STEPS[_digest_status(rows)],
        rows=rows,
        reason_codes=reason_codes,
        reason_code_counts=_reason_code_counts(reason_codes, rows),
    )


def market_research_crypto_etf_approval_delay_digest_payload(
    report: CryptoEtfApprovalDelayDigestReport,
) -> dict[str, Any]:
    if type(report) is not CryptoEtfApprovalDelayDigestReport:
        raise ValueError("report must be exactly CryptoEtfApprovalDelayDigestReport")
    return _payload_value(report)


def _row_from_observation(
    value: CryptoEtfApprovalDelayObservation,
    *,
    config: CryptoEtfApprovalDelayDigestConfig,
    generated_at: datetime,
) -> CryptoEtfApprovalDelayDigestRow:
    source_age_seconds = _seconds_between(generated_at, value.observed_at)
    source_fresh = source_age_seconds <= config.max_source_age_seconds
    status = _delay_status(value.delay_probability, config=config)
    direction = DELAY_DIRECTION if status != PASS_STATUS else ROUTINE_DIRECTION
    confidence_cap = _confidence_cap(
        status=status,
        source_fresh=source_fresh,
        config=config,
    )
    return CryptoEtfApprovalDelayDigestRow(
        source_id=value.source_id,
        proposal_id=value.proposal_id,
        issuer_name=value.issuer_name,
        asset_symbol=value.asset_symbol,
        review_stage=value.review_stage,
        days_until_deadline=value.days_until_deadline,
        delay_probability=value.delay_probability,
        comment_volume_z_score=value.comment_volume_z_score,
        amendment_age_days=value.amendment_age_days,
        source_confidence=value.source_confidence,
        observed_at=value.observed_at,
        source_age_seconds=source_age_seconds,
        confidence_cap=confidence_cap,
        capped_confidence=min(value.source_confidence, confidence_cap),
        delay_direction=direction,
        delay_status=status,
        reason_codes=_row_reason_codes(
            value.upstream_reason_codes,
            value=value,
            status=status,
            source_fresh=source_fresh,
        ),
    )


def _delay_status(
    delay_probability: Decimal,
    *,
    config: CryptoEtfApprovalDelayDigestConfig,
) -> str:
    if delay_probability >= config.blocked_delay_probability:
        return BLOCKED_STATUS
    if delay_probability >= config.watch_delay_probability:
        return WATCH_STATUS
    return PASS_STATUS


def _confidence_cap(
    *,
    status: str,
    source_fresh: bool,
    config: CryptoEtfApprovalDelayDigestConfig,
) -> Decimal:
    caps = [ONE]
    if status == PASS_STATUS:
        caps.append(config.routine_confidence_cap)
    if not source_fresh:
        caps.append(config.stale_confidence_cap)
    return _quantize_decimal(min(caps))


def _row_reason_codes(
    upstream_reason_codes: tuple[str, ...],
    *,
    value: CryptoEtfApprovalDelayObservation,
    status: str,
    source_fresh: bool,
) -> tuple[str, ...]:
    reason_codes = list(upstream_reason_codes)
    if status == BLOCKED_STATUS:
        reason_codes.append("approval_delay_blocked")
    elif status == WATCH_STATUS:
        reason_codes.append("approval_delay_watch")
    else:
        reason_codes.append("approval_delay_calm")
    reason_codes.append("source_fresh" if source_fresh else "source_stale")
    if value.days_until_deadline <= NEAR_DEADLINE_DAYS:
        reason_codes.append("deadline_near")
    if value.amendment_age_days >= DELAYED_AMENDMENT_DAYS:
        reason_codes.append("delayed_amendment_cycle")
    if value.comment_volume_z_score >= COMMENT_PRESSURE_Z_SCORE:
        reason_codes.append("comment_volume_pressure")
    return _normalize_reason_codes(tuple(reason_codes))


def _report_reason_codes(
    rows: tuple[CryptoEtfApprovalDelayDigestRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return ("crypto_etf_approval_delay_digest_empty",)
    reason_codes: list[str] = []
    for row in rows:
        reason_codes.extend(row.reason_codes)
    return _normalize_reason_codes(tuple(reason_codes))


def _reason_code_counts(
    reason_codes: tuple[str, ...],
    rows: tuple[CryptoEtfApprovalDelayDigestRow, ...],
) -> tuple[CryptoEtfApprovalDelayReasonCodeCount, ...]:
    row_count = _count_decimal(len(rows))
    if reason_codes == ("crypto_etf_approval_delay_digest_empty",):
        return (
            CryptoEtfApprovalDelayReasonCodeCount(
                reason_code="crypto_etf_approval_delay_digest_empty",
                count=ONE,
                row_ratio=ZERO,
            ),
        )
    return tuple(
        CryptoEtfApprovalDelayReasonCodeCount(
            reason_code=reason_code,
            count=_reason_count(rows, reason_code),
            row_ratio=_ratio(_reason_count(rows, reason_code), row_count),
        )
        for reason_code in reason_codes
    )


def _normalize_inputs(
    inputs: Iterable[CryptoEtfApprovalDelayObservation],
) -> tuple[CryptoEtfApprovalDelayObservation, ...]:
    if isinstance(inputs, (str, bytes)) or not isinstance(inputs, Iterable):
        raise ValueError("inputs must be an iterable")
    normalized = tuple(inputs)
    seen: set[str] = set()
    for value in normalized:
        if type(value) is not CryptoEtfApprovalDelayObservation:
            raise ValueError("inputs must contain CryptoEtfApprovalDelayObservation")
        _require_hard_flags(value)
        key = value.source_id
        if key in seen:
            raise ValueError("inputs must not contain duplicate source_id")
        seen.add(key)
    return normalized


def _normalize_rows(
    rows: Iterable[CryptoEtfApprovalDelayDigestRow],
) -> tuple[CryptoEtfApprovalDelayDigestRow, ...]:
    if isinstance(rows, (str, bytes)) or not isinstance(rows, Iterable):
        raise ValueError("rows must be an iterable")
    normalized = tuple(rows)
    for row in normalized:
        if type(row) is not CryptoEtfApprovalDelayDigestRow:
            raise ValueError("rows must contain CryptoEtfApprovalDelayDigestRow")
        _require_hard_flags(row)
    return tuple(sorted(normalized, key=_row_sort_key))


def _normalize_reason_code_counts(
    values: Iterable[CryptoEtfApprovalDelayReasonCodeCount],
) -> tuple[CryptoEtfApprovalDelayReasonCodeCount, ...]:
    if isinstance(values, (str, bytes)) or not isinstance(values, Iterable):
        raise ValueError("reason_code_counts must be an iterable")
    normalized = tuple(values)
    for value in normalized:
        if type(value) is not CryptoEtfApprovalDelayReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain CryptoEtfApprovalDelayReasonCodeCount",
            )
        _require_hard_flags(value)
    return tuple(sorted(normalized, key=lambda value: value.reason_code))


def _validate_row(row: CryptoEtfApprovalDelayDigestRow) -> None:
    if row.capped_confidence > row.confidence_cap:
        raise ValueError("capped_confidence must not exceed confidence_cap")
    if row.delay_status == PASS_STATUS and row.delay_direction != ROUTINE_DIRECTION:
        raise ValueError("delay_direction must match delay_status")
    if row.delay_status != PASS_STATUS and row.delay_direction != DELAY_DIRECTION:
        raise ValueError("delay_direction must match delay_status")


def _validate_report(report: CryptoEtfApprovalDelayDigestReport) -> None:
    if report.row_count != _count_decimal(len(report.rows)):
        raise ValueError("row_count must match rows")
    if report.input_count != report.row_count:
        raise ValueError("input_count must match row_count")
    if (
        report.blocked_delay_count
        + report.watch_delay_count
        + report.routine_count
        != report.row_count
    ):
        raise ValueError("status counts must match row_count")
    if report.stale_source_count != _reason_count(report.rows, "source_stale"):
        raise ValueError("stale_source_count must match rows")
    if report.near_deadline_count != _reason_count(report.rows, "deadline_near"):
        raise ValueError("near_deadline_count must match rows")
    if report.max_delay_probability != _max_row_decimal(report.rows, "delay_probability"):
        raise ValueError("max_delay_probability must match rows")
    if report.average_delay_probability != _ratio(
        _sum_decimal(row.delay_probability for row in report.rows),
        report.row_count,
    ):
        raise ValueError("average_delay_probability must match rows")
    if report.digest_status != _digest_status(report.rows):
        raise ValueError("digest_status must match rows")
    if report.recommended_next_step != RECOMMENDED_NEXT_STEPS[report.digest_status]:
        raise ValueError("recommended_next_step must match digest_status")


def _digest_status(rows: tuple[CryptoEtfApprovalDelayDigestRow, ...]) -> str:
    if not rows:
        return BLOCKED_STATUS
    if any(row.delay_status == BLOCKED_STATUS for row in rows):
        return BLOCKED_STATUS
    if any(row.delay_status == WATCH_STATUS for row in rows):
        return WATCH_STATUS
    return PASS_STATUS


def _status_count(rows: tuple[CryptoEtfApprovalDelayDigestRow, ...], status: str) -> Decimal:
    return _count_decimal(sum(1 for row in rows if row.delay_status == status))


def _reason_count(rows: tuple[CryptoEtfApprovalDelayDigestRow, ...], reason_code: str) -> Decimal:
    return _count_decimal(sum(1 for row in rows if reason_code in row.reason_codes))


def _max_row_decimal(
    rows: tuple[CryptoEtfApprovalDelayDigestRow, ...],
    field_name: str,
) -> Decimal:
    if not rows:
        return ZERO
    return max(getattr(row, field_name) for row in rows)


def _sum_decimal(values: Iterable[Decimal]) -> Decimal:
    total = ZERO
    for value in values:
        total += value
    return _quantize_decimal(total)


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO:
        return ZERO
    return _quantize_decimal(numerator / denominator)


def _seconds_between(later: datetime, earlier: datetime) -> Decimal:
    delta = later - earlier
    if delta.days < 0:
        raise ValueError("observed_at must not be after generated_at")
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


def _require_member(field_name: str, value: object, allowed: tuple[str, ...]) -> None:
    if type(value) is not str or value not in allowed:
        raise ValueError(f"{field_name} must be one of {allowed}")


def _normalize_reason_codes(reason_codes: Iterable[str]) -> tuple[str, ...]:
    if isinstance(reason_codes, (str, bytes)) or not isinstance(reason_codes, Iterable):
        raise ValueError("reason_codes must be an iterable")
    normalized: list[str] = []
    for reason_code in reason_codes:
        _require_canonical_string("reason_code", reason_code)
        if reason_code not in normalized:
            normalized.append(reason_code)
    return tuple(sorted(normalized))


def _require_hard_flags(value: object) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if getattr(value, field_name, None) is not True:
            raise ValueError(f"{field_name} must be True")


def _require_exact_type(value: object, type_: type[object], label: str) -> None:
    if type(value) is not type_:
        raise ValueError(f"{label} must be exactly {type_.__name__}")


def _row_sort_key(
    row: CryptoEtfApprovalDelayDigestRow,
) -> tuple[Decimal, Decimal, Decimal, str, str]:
    return (
        STATUS_RANK[row.delay_status],
        -row.delay_probability,
        row.days_until_deadline,
        row.proposal_id,
        row.source_id,
    )


def _payload_value(value: object) -> Any:
    if isinstance(value, Decimal):
        return f"{value:.6f}"
    if type(value) is datetime:
        return value.isoformat()
    if is_dataclass(value) and not isinstance(value, type):
        return {field.name: _payload_value(getattr(value, field.name)) for field in fields(value)}
    if isinstance(value, tuple):
        return [_payload_value(item) for item in value]
    return value
