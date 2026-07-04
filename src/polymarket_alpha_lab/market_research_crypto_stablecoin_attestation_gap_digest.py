"""Pure Phase 1 stablecoin reserve attestation gap digest reducer."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from typing import Any


DEFAULT_CRYPTO_STABLECOIN_ATTESTATION_GAP_DIGEST_CONFIG_VERSION = (
    "market-research-crypto-stablecoin-attestation-gap-digest-v0"
)

INPUT_REASONS = (
    "stablecoin_attestation_reported",
    "stablecoin_attestation_source_revision",
    "stablecoin_attestation_method_change",
    "stablecoin_supply_jump",
)
ROW_REASONS = (
    "stablecoin_attestation_gap_high",
    "stablecoin_attestation_gap_watch",
    "stablecoin_attestation_gap_low",
    "stablecoin_attestation_source_fresh",
    "stablecoin_attestation_source_stale",
    "stablecoin_attestation_window_fresh",
    "stablecoin_attestation_window_stale",
    "stablecoin_attestation_large_notional_gap",
    "stablecoin_attestation_high_confidence",
    "stablecoin_attestation_source_revision",
    "stablecoin_attestation_method_change",
    "stablecoin_supply_jump",
)
REPORT_REASONS = (
    "stablecoin_attestation_gap_digest_empty",
    "stablecoin_attestation_gap_high_present",
    "stablecoin_attestation_gap_watch_present",
    "stablecoin_attestation_gap_low_only",
    "stablecoin_attestation_source_stale_present",
    "stablecoin_attestation_window_stale_present",
    "stablecoin_attestation_large_notional_gap_present",
    "stablecoin_attestation_revision_present",
    "stablecoin_attestation_method_change_present",
    "stablecoin_supply_jump_present",
)
ROW_STATUSES = ("gap_risk_high", "gap_risk_watch", "gap_risk_low")
DIGEST_STATUSES = ("empty", "high_risk", "watch", "low_risk")
STATUS_RANK = {
    "gap_risk_high": Decimal("0.000000"),
    "gap_risk_watch": Decimal("1.000000"),
    "gap_risk_low": Decimal("2.000000"),
}

QUANT = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
SECONDS_PER_DAY = Decimal("86400.000000")
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)


@dataclass(frozen=True)
class StablecoinAttestationGapDigestConfig:
    config_version: str = DEFAULT_CRYPTO_STABLECOIN_ATTESTATION_GAP_DIGEST_CONFIG_VERSION
    watch_gap_ratio: Decimal = Decimal("0.010000")
    high_gap_ratio: Decimal = Decimal("0.050000")
    max_attestation_age_days: Decimal = Decimal("30.000000")
    max_source_age_seconds: Decimal = Decimal("900.000000")
    large_gap_usd: Decimal = Decimal("10000000.000000")
    high_confidence_threshold: Decimal = Decimal("0.800000")
    stale_confidence_cap: Decimal = Decimal("0.400000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, StablecoinAttestationGapDigestConfig, "config")
        object.__setattr__(
            self,
            "config_version",
            _require_text("config_version", self.config_version),
        )
        if self.config_version != DEFAULT_CRYPTO_STABLECOIN_ATTESTATION_GAP_DIGEST_CONFIG_VERSION:
            raise ValueError("config_version must be the configured version")
        for field_name in (
            "watch_gap_ratio",
            "high_gap_ratio",
            "high_confidence_threshold",
            "stale_confidence_cap",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio(field_name, getattr(self, field_name)),
            )
        if self.watch_gap_ratio > self.high_gap_ratio:
            raise ValueError("watch_gap_ratio must not exceed high_gap_ratio")
        for field_name in (
            "max_attestation_age_days",
            "max_source_age_seconds",
            "large_gap_usd",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        _require_hard_flags("stablecoin attestation gap config", self)


@dataclass(frozen=True)
class StablecoinReserveAttestationObservation:
    source_id: str
    issuer_id: str
    asset_symbol: str
    event_slug: str
    outstanding_supply_usd: Decimal
    attested_reserves_usd: Decimal
    attestation_as_of: datetime
    source_observed_at: datetime
    screening_confidence: Decimal
    upstream_reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, StablecoinReserveAttestationObservation, "observation")
        for field_name in ("source_id", "issuer_id", "asset_symbol", "event_slug"):
            object.__setattr__(
                self,
                field_name,
                _require_text(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "outstanding_supply_usd",
            _require_positive_decimal(
                "outstanding_supply_usd",
                self.outstanding_supply_usd,
            ),
        )
        object.__setattr__(
            self,
            "attested_reserves_usd",
            _require_nonnegative_decimal(
                "attested_reserves_usd",
                self.attested_reserves_usd,
            ),
        )
        object.__setattr__(
            self,
            "attestation_as_of",
            _as_utc("attestation_as_of", self.attestation_as_of),
        )
        object.__setattr__(
            self,
            "source_observed_at",
            _as_utc("source_observed_at", self.source_observed_at),
        )
        object.__setattr__(
            self,
            "screening_confidence",
            _require_ratio("screening_confidence", self.screening_confidence),
        )
        object.__setattr__(
            self,
            "upstream_reason_codes",
            _normalize_reasons(
                "upstream_reason_codes",
                self.upstream_reason_codes,
                INPUT_REASONS,
            ),
        )
        _require_hard_flags("stablecoin attestation observation", self)


@dataclass(frozen=True)
class StablecoinAttestationGapReasonCodeCount:
    reason_code: str
    row_count: Decimal
    row_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, StablecoinAttestationGapReasonCodeCount, "reason count")
        object.__setattr__(
            self,
            "reason_code",
            _require_member("reason_code", self.reason_code, REPORT_REASONS),
        )
        object.__setattr__(
            self,
            "row_count",
            _require_nonnegative_decimal("row_count", self.row_count),
        )
        object.__setattr__(self, "row_ratio", _require_ratio("row_ratio", self.row_ratio))
        _require_hard_flags("stablecoin attestation reason count", self)


@dataclass(frozen=True)
class StablecoinAttestationGapRow:
    source_id: str
    issuer_id: str
    asset_symbol: str
    event_slug: str
    outstanding_supply_usd: Decimal
    attested_reserves_usd: Decimal
    reserve_gap_usd: Decimal
    reserve_gap_ratio: Decimal
    reserve_coverage_ratio: Decimal
    attestation_as_of: datetime
    attestation_age_days: Decimal
    source_observed_at: datetime
    source_age_seconds: Decimal
    screening_confidence: Decimal
    confidence_cap: Decimal
    capped_screening_confidence: Decimal
    gap_status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, StablecoinAttestationGapRow, "row")
        for field_name in ("source_id", "issuer_id", "asset_symbol", "event_slug"):
            object.__setattr__(
                self,
                field_name,
                _require_text(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "outstanding_supply_usd",
            _require_positive_decimal(
                "outstanding_supply_usd",
                self.outstanding_supply_usd,
            ),
        )
        for field_name in (
            "attested_reserves_usd",
            "reserve_gap_usd",
            "reserve_coverage_ratio",
            "attestation_age_days",
            "source_age_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "reserve_gap_ratio",
            _require_ratio("reserve_gap_ratio", self.reserve_gap_ratio),
        )
        object.__setattr__(
            self,
            "attestation_as_of",
            _as_utc("attestation_as_of", self.attestation_as_of),
        )
        object.__setattr__(
            self,
            "source_observed_at",
            _as_utc("source_observed_at", self.source_observed_at),
        )
        for field_name in (
            "screening_confidence",
            "confidence_cap",
            "capped_screening_confidence",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "gap_status",
            _require_member("gap_status", self.gap_status, ROW_STATUSES),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reasons("reason_codes", self.reason_codes, ROW_REASONS),
        )
        _validate_row(self)
        _require_hard_flags("stablecoin attestation gap row", self)


@dataclass(frozen=True)
class StablecoinAttestationGapDigest:
    generated_at: datetime
    config_version: str
    digest_status: str
    reason_codes: tuple[str, ...]
    input_count: Decimal
    row_count: Decimal
    high_risk_count: Decimal
    watch_count: Decimal
    low_risk_count: Decimal
    stale_source_count: Decimal
    stale_attestation_count: Decimal
    total_reserve_gap_usd: Decimal
    max_reserve_gap_usd: Decimal
    max_reserve_gap_ratio: Decimal
    rows: tuple[StablecoinAttestationGapRow, ...]
    reason_code_counts: tuple[StablecoinAttestationGapReasonCodeCount, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, StablecoinAttestationGapDigest, "digest")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        object.__setattr__(
            self,
            "config_version",
            _require_text("config_version", self.config_version),
        )
        if self.config_version != DEFAULT_CRYPTO_STABLECOIN_ATTESTATION_GAP_DIGEST_CONFIG_VERSION:
            raise ValueError("config_version must be the configured version")
        object.__setattr__(
            self,
            "digest_status",
            _require_member("digest_status", self.digest_status, DIGEST_STATUSES),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reasons("reason_codes", self.reason_codes, REPORT_REASONS),
        )
        for field_name in (
            "input_count",
            "row_count",
            "high_risk_count",
            "watch_count",
            "low_risk_count",
            "stale_source_count",
            "stale_attestation_count",
            "total_reserve_gap_usd",
            "max_reserve_gap_usd",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "max_reserve_gap_ratio",
            _require_ratio("max_reserve_gap_ratio", self.max_reserve_gap_ratio),
        )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_counts(self.reason_code_counts),
        )
        _validate_digest(self)
        _require_hard_flags("stablecoin attestation gap digest", self)


def build_market_research_crypto_stablecoin_attestation_gap_digest(
    observations: Iterable[StablecoinReserveAttestationObservation],
    *,
    config: StablecoinAttestationGapDigestConfig,
    generated_at: datetime,
) -> StablecoinAttestationGapDigest:
    if type(config) is not StablecoinAttestationGapDigestConfig:
        raise ValueError("config must be a StablecoinAttestationGapDigestConfig")
    _require_hard_flags("stablecoin attestation gap config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    input_rows = _normalize_observations(observations)
    rows = tuple(
        sorted(
            (
                _row_from_observation(row, config=config, generated_at=generated_at_utc)
                for row in input_rows
            ),
            key=_row_sort_key,
        ),
    )
    reason_codes = _digest_reasons(rows)
    return StablecoinAttestationGapDigest(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        digest_status=_digest_status(rows),
        reason_codes=reason_codes,
        input_count=_count(len(input_rows)),
        row_count=_count(len(rows)),
        high_risk_count=_status_count(rows, "gap_risk_high"),
        watch_count=_status_count(rows, "gap_risk_watch"),
        low_risk_count=_status_count(rows, "gap_risk_low"),
        stale_source_count=_reason_count(rows, "stablecoin_attestation_source_stale"),
        stale_attestation_count=_reason_count(rows, "stablecoin_attestation_window_stale"),
        total_reserve_gap_usd=_sum_decimal(row.reserve_gap_usd for row in rows),
        max_reserve_gap_usd=max((row.reserve_gap_usd for row in rows), default=ZERO),
        max_reserve_gap_ratio=max((row.reserve_gap_ratio for row in rows), default=ZERO),
        rows=rows,
        reason_code_counts=_reason_counts(rows, reason_codes, _count(len(rows))),
    )


def market_research_crypto_stablecoin_attestation_gap_digest_payload(
    digest: StablecoinAttestationGapDigest,
) -> dict[str, Any]:
    if type(digest) is not StablecoinAttestationGapDigest:
        raise ValueError("digest must be a StablecoinAttestationGapDigest")
    value = _json_ready(digest)
    if type(value) is not dict:
        raise ValueError("digest must serialize to a JSON object")
    return value


def _row_from_observation(
    row: StablecoinReserveAttestationObservation,
    *,
    config: StablecoinAttestationGapDigestConfig,
    generated_at: datetime,
) -> StablecoinAttestationGapRow:
    source_age_seconds = _seconds_between(
        generated_at,
        row.source_observed_at,
        "source_observed_at",
    )
    attestation_age_days = _days_between(
        generated_at,
        row.attestation_as_of,
        "attestation_as_of",
    )
    reserve_gap_usd = _reserve_gap(row.outstanding_supply_usd, row.attested_reserves_usd)
    reserve_gap_ratio = _ratio(reserve_gap_usd, row.outstanding_supply_usd)
    source_fresh = source_age_seconds <= config.max_source_age_seconds
    attestation_fresh = attestation_age_days <= config.max_attestation_age_days
    status = _gap_status(
        reserve_gap_ratio,
        attestation_fresh=attestation_fresh,
        config=config,
    )
    confidence_cap = ONE if source_fresh and attestation_fresh else config.stale_confidence_cap
    return StablecoinAttestationGapRow(
        source_id=row.source_id,
        issuer_id=row.issuer_id,
        asset_symbol=row.asset_symbol,
        event_slug=row.event_slug,
        outstanding_supply_usd=row.outstanding_supply_usd,
        attested_reserves_usd=row.attested_reserves_usd,
        reserve_gap_usd=reserve_gap_usd,
        reserve_gap_ratio=reserve_gap_ratio,
        reserve_coverage_ratio=_ratio(
            row.attested_reserves_usd,
            row.outstanding_supply_usd,
        ),
        attestation_as_of=row.attestation_as_of,
        attestation_age_days=attestation_age_days,
        source_observed_at=row.source_observed_at,
        source_age_seconds=source_age_seconds,
        screening_confidence=row.screening_confidence,
        confidence_cap=confidence_cap,
        capped_screening_confidence=min(row.screening_confidence, confidence_cap),
        gap_status=status,
        reason_codes=_row_reasons(
            row.upstream_reason_codes,
            status=status,
            source_fresh=source_fresh,
            attestation_fresh=attestation_fresh,
            reserve_gap_usd=reserve_gap_usd,
            screening_confidence=row.screening_confidence,
            config=config,
        ),
    )


def _gap_status(
    reserve_gap_ratio: Decimal,
    *,
    attestation_fresh: bool,
    config: StablecoinAttestationGapDigestConfig,
) -> str:
    if reserve_gap_ratio >= config.high_gap_ratio:
        return "gap_risk_high"
    if reserve_gap_ratio >= config.watch_gap_ratio or not attestation_fresh:
        return "gap_risk_watch"
    return "gap_risk_low"


def _row_reasons(
    upstream_reason_codes: tuple[str, ...],
    *,
    status: str,
    source_fresh: bool,
    attestation_fresh: bool,
    reserve_gap_usd: Decimal,
    screening_confidence: Decimal,
    config: StablecoinAttestationGapDigestConfig,
) -> tuple[str, ...]:
    reasons = [_status_reason(status)]
    reasons.append(
        "stablecoin_attestation_source_fresh"
        if source_fresh
        else "stablecoin_attestation_source_stale",
    )
    reasons.append(
        "stablecoin_attestation_window_fresh"
        if attestation_fresh
        else "stablecoin_attestation_window_stale",
    )
    if reserve_gap_usd >= config.large_gap_usd and reserve_gap_usd > ZERO:
        reasons.append("stablecoin_attestation_large_notional_gap")
    if screening_confidence >= config.high_confidence_threshold:
        reasons.append("stablecoin_attestation_high_confidence")
    for reason_code in upstream_reason_codes:
        if reason_code != "stablecoin_attestation_reported":
            reasons.append(reason_code)
    return _normalize_reasons("reason_codes", tuple(reasons), ROW_REASONS)


def _status_reason(status: str) -> str:
    if status == "gap_risk_high":
        return "stablecoin_attestation_gap_high"
    if status == "gap_risk_watch":
        return "stablecoin_attestation_gap_watch"
    return "stablecoin_attestation_gap_low"


def _digest_status(rows: tuple[StablecoinAttestationGapRow, ...]) -> str:
    if not rows:
        return "empty"
    if any(row.gap_status == "gap_risk_high" for row in rows):
        return "high_risk"
    if any(row.gap_status == "gap_risk_watch" for row in rows):
        return "watch"
    return "low_risk"


def _digest_reasons(rows: tuple[StablecoinAttestationGapRow, ...]) -> tuple[str, ...]:
    if not rows:
        return ("stablecoin_attestation_gap_digest_empty",)
    reasons: list[str] = []
    if any(row.gap_status == "gap_risk_high" for row in rows):
        reasons.append("stablecoin_attestation_gap_high_present")
    if any(row.gap_status == "gap_risk_watch" for row in rows):
        reasons.append("stablecoin_attestation_gap_watch_present")
    if all(row.gap_status == "gap_risk_low" for row in rows):
        reasons.append("stablecoin_attestation_gap_low_only")
    if any("stablecoin_attestation_source_stale" in row.reason_codes for row in rows):
        reasons.append("stablecoin_attestation_source_stale_present")
    if any("stablecoin_attestation_window_stale" in row.reason_codes for row in rows):
        reasons.append("stablecoin_attestation_window_stale_present")
    if any("stablecoin_attestation_large_notional_gap" in row.reason_codes for row in rows):
        reasons.append("stablecoin_attestation_large_notional_gap_present")
    if any("stablecoin_attestation_source_revision" in row.reason_codes for row in rows):
        reasons.append("stablecoin_attestation_revision_present")
    if any("stablecoin_attestation_method_change" in row.reason_codes for row in rows):
        reasons.append("stablecoin_attestation_method_change_present")
    if any("stablecoin_supply_jump" in row.reason_codes for row in rows):
        reasons.append("stablecoin_supply_jump_present")
    return _normalize_reasons("reason_codes", tuple(reasons), REPORT_REASONS)


def _reason_counts(
    rows: tuple[StablecoinAttestationGapRow, ...],
    report_reasons: tuple[str, ...],
    row_count: Decimal,
) -> tuple[StablecoinAttestationGapReasonCodeCount, ...]:
    if not rows:
        return ()
    return tuple(
        StablecoinAttestationGapReasonCodeCount(
            reason_code=reason,
            row_count=_count(sum(1 for row in rows if _row_matches_report_reason(row, reason))),
            row_ratio=_ratio(
                _count(sum(1 for row in rows if _row_matches_report_reason(row, reason))),
                row_count,
            ),
        )
        for reason in report_reasons
    )


def _row_matches_report_reason(row: StablecoinAttestationGapRow, reason: str) -> bool:
    if reason == "stablecoin_attestation_gap_high_present":
        return row.gap_status == "gap_risk_high"
    if reason == "stablecoin_attestation_gap_watch_present":
        return row.gap_status == "gap_risk_watch"
    if reason == "stablecoin_attestation_gap_low_only":
        return row.gap_status == "gap_risk_low"
    if reason == "stablecoin_attestation_source_stale_present":
        return "stablecoin_attestation_source_stale" in row.reason_codes
    if reason == "stablecoin_attestation_window_stale_present":
        return "stablecoin_attestation_window_stale" in row.reason_codes
    if reason == "stablecoin_attestation_large_notional_gap_present":
        return "stablecoin_attestation_large_notional_gap" in row.reason_codes
    if reason == "stablecoin_attestation_revision_present":
        return "stablecoin_attestation_source_revision" in row.reason_codes
    if reason == "stablecoin_attestation_method_change_present":
        return "stablecoin_attestation_method_change" in row.reason_codes
    if reason == "stablecoin_supply_jump_present":
        return "stablecoin_supply_jump" in row.reason_codes
    return False


def _normalize_observations(
    observations: Iterable[StablecoinReserveAttestationObservation],
) -> tuple[StablecoinReserveAttestationObservation, ...]:
    if isinstance(observations, (str, bytes)) or not isinstance(observations, Iterable):
        raise ValueError("observations must contain stablecoin attestation observations")
    normalized = tuple(observations)
    seen: set[str] = set()
    for row in normalized:
        if type(row) is not StablecoinReserveAttestationObservation:
            raise ValueError(
                "observations must contain StablecoinReserveAttestationObservation",
            )
        _require_hard_flags("stablecoin attestation observation", row)
        if row.source_id in seen:
            raise ValueError("observations must not contain duplicate source_id values")
        seen.add(row.source_id)
    return normalized


def _normalize_rows(value: object) -> tuple[StablecoinAttestationGapRow, ...]:
    if isinstance(value, (str, bytes)) or not isinstance(value, Iterable):
        raise ValueError("rows must be a tuple of StablecoinAttestationGapRow")
    rows = tuple(value)
    for row in rows:
        if type(row) is not StablecoinAttestationGapRow:
            raise ValueError("rows must contain StablecoinAttestationGapRow")
        _require_hard_flags("stablecoin attestation gap row", row)
    if len({row.source_id for row in rows}) != len(rows):
        raise ValueError("rows must not contain duplicate source_id values")
    return tuple(sorted(rows, key=_row_sort_key))


def _normalize_reason_counts(value: object) -> tuple[StablecoinAttestationGapReasonCodeCount, ...]:
    if isinstance(value, (str, bytes)) or not isinstance(value, Iterable):
        raise ValueError("reason_code_counts must be a tuple")
    rows = tuple(value)
    for row in rows:
        if type(row) is not StablecoinAttestationGapReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain StablecoinAttestationGapReasonCodeCount",
            )
        _require_hard_flags("stablecoin attestation reason count", row)
    return tuple(sorted(rows, key=lambda row: REPORT_REASONS.index(row.reason_code)))


def _validate_row(row: StablecoinAttestationGapRow) -> None:
    if row.reserve_gap_usd != _reserve_gap(row.outstanding_supply_usd, row.attested_reserves_usd):
        raise ValueError("reserve_gap_usd must match supply and reserves")
    if row.reserve_gap_ratio != _ratio(row.reserve_gap_usd, row.outstanding_supply_usd):
        raise ValueError("reserve_gap_ratio must match reserve_gap_usd and supply")
    if row.reserve_coverage_ratio != _ratio(row.attested_reserves_usd, row.outstanding_supply_usd):
        raise ValueError("reserve_coverage_ratio must match reserves and supply")
    if row.capped_screening_confidence > row.confidence_cap:
        raise ValueError("capped_screening_confidence must not exceed confidence_cap")
    if _status_reason(row.gap_status) not in row.reason_codes:
        raise ValueError("gap_status must match reason_codes")


def _validate_digest(digest: StablecoinAttestationGapDigest) -> None:
    if digest.row_count != _count(len(digest.rows)):
        raise ValueError("row_count must match rows")
    if digest.high_risk_count != _status_count(digest.rows, "gap_risk_high"):
        raise ValueError("high_risk_count must match rows")
    if digest.watch_count != _status_count(digest.rows, "gap_risk_watch"):
        raise ValueError("watch_count must match rows")
    if digest.low_risk_count != _status_count(digest.rows, "gap_risk_low"):
        raise ValueError("low_risk_count must match rows")
    if digest.high_risk_count + digest.watch_count + digest.low_risk_count != digest.row_count:
        raise ValueError("status counts must match row_count")
    if digest.stale_source_count != _reason_count(
        digest.rows,
        "stablecoin_attestation_source_stale",
    ):
        raise ValueError("stale_source_count must match rows")
    if digest.stale_attestation_count != _reason_count(
        digest.rows,
        "stablecoin_attestation_window_stale",
    ):
        raise ValueError("stale_attestation_count must match rows")
    if digest.total_reserve_gap_usd != _sum_decimal(row.reserve_gap_usd for row in digest.rows):
        raise ValueError("total_reserve_gap_usd must match rows")
    if digest.max_reserve_gap_usd != max((row.reserve_gap_usd for row in digest.rows), default=ZERO):
        raise ValueError("max_reserve_gap_usd must match rows")
    if digest.max_reserve_gap_ratio != max(
        (row.reserve_gap_ratio for row in digest.rows),
        default=ZERO,
    ):
        raise ValueError("max_reserve_gap_ratio must match rows")
    if digest.digest_status != _digest_status(digest.rows):
        raise ValueError("digest_status must match rows")
    if digest.reason_codes != _digest_reasons(digest.rows):
        raise ValueError("reason_codes must match rows")


def _status_count(rows: tuple[StablecoinAttestationGapRow, ...], status: str) -> Decimal:
    return _count(sum(1 for row in rows if row.gap_status == status))


def _reason_count(rows: tuple[StablecoinAttestationGapRow, ...], reason_code: str) -> Decimal:
    return _count(sum(1 for row in rows if reason_code in row.reason_codes))


def _row_sort_key(row: StablecoinAttestationGapRow) -> tuple[Decimal, Decimal, Decimal, str, str, str]:
    return (
        STATUS_RANK[row.gap_status],
        -row.reserve_gap_ratio,
        -row.reserve_gap_usd,
        row.issuer_id,
        row.asset_symbol,
        row.source_id,
    )


def _reserve_gap(outstanding_supply_usd: Decimal, attested_reserves_usd: Decimal) -> Decimal:
    gap = outstanding_supply_usd - attested_reserves_usd
    if gap < ZERO:
        return ZERO
    return _quantize(gap)


def _seconds_between(later: datetime, earlier: datetime, earlier_name: str) -> Decimal:
    delta = later - earlier
    if delta.days < 0:
        raise ValueError(f"{earlier_name} must not be after generated_at")
    whole_seconds = Decimal(delta.days * 86400 + delta.seconds)
    fractional_seconds = Decimal(delta.microseconds) / Decimal("1000000")
    return _quantize(whole_seconds + fractional_seconds)


def _days_between(later: datetime, earlier: datetime, earlier_name: str) -> Decimal:
    return _ratio(_seconds_between(later, earlier, earlier_name), SECONDS_PER_DAY)


def _sum_decimal(values: Iterable[Decimal]) -> Decimal:
    total = ZERO
    for value in values:
        if type(value) is not Decimal:
            raise ValueError("values must be Decimals")
        total += value
    return _quantize(total)


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if type(numerator) is not Decimal or type(denominator) is not Decimal:
        raise ValueError("ratio values must be Decimals")
    if denominator == ZERO:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return _quantize(numerator / denominator)


def _count(value: int) -> Decimal:
    return _quantize(Decimal(value))


def _require_ratio(field_name: str, value: object) -> Decimal:
    decimal_value = _require_nonnegative_decimal(field_name, value)
    if decimal_value > ONE:
        raise ValueError(f"{field_name} must be no greater than one")
    return decimal_value


def _require_positive_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_nonnegative_decimal(field_name, value)
    if decimal_value <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return decimal_value


def _require_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return decimal_value


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return _quantize(value)


def _quantize(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(QUANT)


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be UTC-aware")
    return value.astimezone(UTC)


def _normalize_reasons(
    field_name: str,
    value: object,
    allowed: tuple[str, ...],
) -> tuple[str, ...]:
    if isinstance(value, (str, bytes)) or not isinstance(value, tuple):
        raise ValueError(f"{field_name} must be a tuple")
    reasons = tuple({_require_member(field_name, item, allowed) for item in value})
    return tuple(sorted(reasons, key=lambda item: allowed.index(item)))


def _require_member(field_name: str, value: object, allowed: tuple[str, ...]) -> str:
    text = _require_text(field_name, value)
    if text not in allowed:
        raise ValueError(f"{field_name} must be supported")
    return text


def _require_text(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be canonical nonempty text")
    return value


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if getattr(value, field_name, None) is not True:
            raise ValueError(f"{label} requires {field_name}=True")


def _require_exact_type(value: object, type_: type[object], label: str) -> None:
    if type(value) is not type_:
        raise ValueError(f"{label} must be exactly {type_.__name__}")


def _json_ready(value: Any) -> Any:
    if isinstance(value, Decimal):
        return str(value)
    if type(value) is datetime:
        return value.astimezone(UTC).isoformat()
    if is_dataclass(value) and not isinstance(value, type):
        return {field.name: _json_ready(getattr(value, field.name)) for field in fields(value)}
    if isinstance(value, tuple):
        return [_json_ready(item) for item in value]
    if isinstance(value, list):
        return [_json_ready(item) for item in value]
    if isinstance(value, dict):
        return {str(key): _json_ready(item) for key, item in value.items()}
    return value


__all__ = (
    "DEFAULT_CRYPTO_STABLECOIN_ATTESTATION_GAP_DIGEST_CONFIG_VERSION",
    "StablecoinAttestationGapDigest",
    "StablecoinAttestationGapDigestConfig",
    "StablecoinAttestationGapReasonCodeCount",
    "StablecoinAttestationGapRow",
    "StablecoinReserveAttestationObservation",
    "build_market_research_crypto_stablecoin_attestation_gap_digest",
    "market_research_crypto_stablecoin_attestation_gap_digest_payload",
)
