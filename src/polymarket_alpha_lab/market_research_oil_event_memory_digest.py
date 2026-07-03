"""Pure report-only oil event memory digest reducer."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, localcontext
import hashlib
import re
from typing import Any


__all__ = (
    "MarketResearchOilEventMemoryDigestConfig",
    "MarketResearchOilEventMemoryDigestEvidence",
    "MarketResearchOilEventMemoryDigestEvidenceRow",
    "MarketResearchOilEventMemoryDigestReport",
    "build_market_research_oil_event_memory_digest",
    "market_research_oil_event_memory_digest_payload",
)


DEFAULT_MARKET_RESEARCH_OIL_EVENT_MEMORY_DIGEST_CONFIG_VERSION = (
    "market-research-oil-event-memory-digest-v1"
)

QUANTUM = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
DECIMAL_CONTEXT = Context(prec=64)
DIGEST_STATUSES = ("pass", "watch", "blocked")
EMAIL_PATTERN = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b")
URL_PATTERN = re.compile(r"\bhttps?://[^\s)>\]]+")
WALLET_PATTERN = re.compile(r"\b0x[a-fA-F0-9]{40}\b")


def _term(*parts: str) -> str:
    return "".join(parts)


SENSITIVE_REFERENCE_MARKERS = (
    _term("api", "_key="),
    _term("api", "key="),
    _term("au", "thor", "ization="),
    "bearer ",
    "password=",
    _term("priv", "ate_key="),
    _term("sec", "ret="),
    "signature=",
    _term("to", "ken="),
    _term("wal", "let="),
)
REFERENCE_HASH_TERMS = (
    _term("au", "th"),
    "bearer",
    _term("priv", "ate"),
    _term("wal", "let"),
)
PUBLIC_SURFACE_TERMS = (
    _term("au", "th"),
    "bearer",
    _term("bro", "ker"),
    _term("can", "cel"),
    _term("data", "base"),
    _term("live", " trading"),
    _term("or", "der"),
    _term("sec", "ret"),
    _term("sub", "mit"),
    _term("to", "ken"),
    _term("wal", "let"),
)


@dataclass(frozen=True)
class MarketResearchOilEventMemoryDigestConfig:
    config_version: str = DEFAULT_MARKET_RESEARCH_OIL_EVENT_MEMORY_DIGEST_CONFIG_VERSION
    max_inventory_age_hours: Decimal = Decimal("36.000000")
    min_catalyst_quality_score: Decimal = Decimal("0.700000")
    min_curve_signal_score: Decimal = Decimal("0.600000")
    min_demand_confirmation_score: Decimal = Decimal("0.550000")
    min_source_family_count: Decimal = Decimal("3.000000")
    max_stale_evidence_share: Decimal = Decimal("0.250000")
    max_volatility_liquidity_gap: Decimal = Decimal("0.300000")
    confidence_decay_per_stale_share: Decimal = Decimal("0.400000")
    confidence_decay_per_gap: Decimal = Decimal("0.250000")
    min_final_confidence: Decimal = Decimal("0.650000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, MarketResearchOilEventMemoryDigestConfig, "config")
        _require_canonical_string("config_version", self.config_version)
        if self.config_version != DEFAULT_MARKET_RESEARCH_OIL_EVENT_MEMORY_DIGEST_CONFIG_VERSION:
            raise ValueError("config_version must match the default version")
        for field_name in (
            "max_inventory_age_hours",
            "min_catalyst_quality_score",
            "min_curve_signal_score",
            "min_demand_confirmation_score",
            "min_source_family_count",
            "max_stale_evidence_share",
            "max_volatility_liquidity_gap",
            "confidence_decay_per_stale_share",
            "confidence_decay_per_gap",
            "min_final_confidence",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "min_catalyst_quality_score",
            "min_curve_signal_score",
            "min_demand_confirmation_score",
            "max_stale_evidence_share",
            "max_volatility_liquidity_gap",
            "confidence_decay_per_stale_share",
            "confidence_decay_per_gap",
            "min_final_confidence",
        ):
            _require_unit_interval(field_name, getattr(self, field_name))
        _require_positive_decimal("min_source_family_count", self.min_source_family_count)
        _require_hard_flags(self)


@dataclass(frozen=True)
class MarketResearchOilEventMemoryDigestEvidence:
    market_slug: str
    evidence_id: str
    source_family: str
    observed_at: datetime
    inventory_data_published_at: datetime
    opec_geopolitical_catalyst_quality: Decimal
    futures_curve_signal: Decimal
    demand_macro_confirmation: Decimal
    volatility_liquidity_gap: Decimal
    base_confidence: Decimal
    summary: str
    reference: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, MarketResearchOilEventMemoryDigestEvidence, "evidence")
        for field_name in (
            "market_slug",
            "evidence_id",
            "source_family",
            "summary",
            "reference",
        ):
            _require_canonical_string(field_name, getattr(self, field_name))
        object.__setattr__(
            self,
            "observed_at",
            _as_utc("observed_at", self.observed_at),
        )
        object.__setattr__(
            self,
            "inventory_data_published_at",
            _as_utc("inventory_data_published_at", self.inventory_data_published_at),
        )
        for field_name in (
            "opec_geopolitical_catalyst_quality",
            "futures_curve_signal",
            "demand_macro_confirmation",
            "volatility_liquidity_gap",
            "base_confidence",
        ):
            value = _normalize_nonnegative_decimal(field_name, getattr(self, field_name))
            _require_unit_interval(field_name, value)
            object.__setattr__(self, field_name, value)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes),
        )
        _require_hard_flags(self)


@dataclass(frozen=True)
class MarketResearchOilEventMemoryDigestEvidenceRow:
    market_slug: str
    evidence_id: str
    source_family: str
    observed_at: datetime
    inventory_data_published_at: datetime
    inventory_data_age_hours: Decimal
    opec_geopolitical_catalyst_quality: Decimal
    futures_curve_signal: Decimal
    demand_macro_confirmation: Decimal
    volatility_liquidity_gap: Decimal
    base_confidence: Decimal
    redacted_summary: str
    redacted_reference: str
    stale_evidence: bool
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, MarketResearchOilEventMemoryDigestEvidenceRow, "evidence row")
        for field_name in (
            "market_slug",
            "evidence_id",
            "source_family",
            "redacted_summary",
            "redacted_reference",
        ):
            _require_canonical_string(field_name, getattr(self, field_name))
        object.__setattr__(
            self,
            "observed_at",
            _as_utc("observed_at", self.observed_at),
        )
        object.__setattr__(
            self,
            "inventory_data_published_at",
            _as_utc("inventory_data_published_at", self.inventory_data_published_at),
        )
        for field_name in (
            "inventory_data_age_hours",
            "opec_geopolitical_catalyst_quality",
            "futures_curve_signal",
            "demand_macro_confirmation",
            "volatility_liquidity_gap",
            "base_confidence",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "opec_geopolitical_catalyst_quality",
            "futures_curve_signal",
            "demand_macro_confirmation",
            "volatility_liquidity_gap",
            "base_confidence",
        ):
            _require_unit_interval(field_name, getattr(self, field_name))
        if type(self.stale_evidence) is not bool:
            raise ValueError("stale_evidence must be a bool")
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes),
        )
        _require_hard_flags(self)


@dataclass(frozen=True)
class MarketResearchOilEventMemoryDigestReport:
    generated_at: datetime
    config_version: str
    digest_status: str
    evidence_count: Decimal
    source_family_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    blocked_count: Decimal
    stale_evidence_count: Decimal
    stale_evidence_share: Decimal
    max_inventory_data_age_hours: Decimal
    min_catalyst_quality_score: Decimal
    min_futures_curve_signal: Decimal
    min_demand_macro_confirmation: Decimal
    max_volatility_liquidity_gap: Decimal
    average_base_confidence: Decimal
    final_confidence: Decimal
    reason_codes: tuple[str, ...]
    evidence_rows: tuple[MarketResearchOilEventMemoryDigestEvidenceRow, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, MarketResearchOilEventMemoryDigestReport, "report")
        object.__setattr__(
            self,
            "generated_at",
            _as_utc("generated_at", self.generated_at),
        )
        _require_canonical_string("config_version", self.config_version)
        _require_digest_status("digest_status", self.digest_status)
        for field_name in (
            "evidence_count",
            "source_family_count",
            "pass_count",
            "watch_count",
            "blocked_count",
            "stale_evidence_count",
            "stale_evidence_share",
            "max_inventory_data_age_hours",
            "min_catalyst_quality_score",
            "min_futures_curve_signal",
            "min_demand_macro_confirmation",
            "max_volatility_liquidity_gap",
            "average_base_confidence",
            "final_confidence",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "stale_evidence_share",
            "min_catalyst_quality_score",
            "min_futures_curve_signal",
            "min_demand_macro_confirmation",
            "max_volatility_liquidity_gap",
            "average_base_confidence",
            "final_confidence",
        ):
            _require_unit_interval(field_name, getattr(self, field_name))
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes),
        )
        object.__setattr__(
            self,
            "evidence_rows",
            _normalize_evidence_rows(self.evidence_rows),
        )
        _validate_report_consistency(self)
        _require_hard_flags(self)


def build_market_research_oil_event_memory_digest(
    evidence: Iterable[MarketResearchOilEventMemoryDigestEvidence],
    *,
    config: MarketResearchOilEventMemoryDigestConfig,
    generated_at: datetime,
) -> MarketResearchOilEventMemoryDigestReport:
    if type(config) is not MarketResearchOilEventMemoryDigestConfig:
        raise ValueError("config must be a MarketResearchOilEventMemoryDigestConfig")
    _require_hard_flags(config)
    generated_at = _as_utc("generated_at", generated_at)
    normalized_evidence = _normalize_evidence(evidence)
    rows = tuple(
        sorted(
            (
                _evidence_row_from_evidence(item, config=config, generated_at=generated_at)
                for item in normalized_evidence
            ),
            key=_evidence_row_sort_key,
        ),
    )
    _require_unique_evidence_row_identities(rows)
    evidence_count = _count_decimal(len(rows))
    source_family_count = _count_decimal(
        len({row.source_family for row in rows}),
    )
    stale_evidence_count = _count_decimal(sum(1 for row in rows if row.stale_evidence))
    stale_evidence_share = _ratio(stale_evidence_count, evidence_count)
    average_base_confidence = _average(
        tuple(row.base_confidence for row in rows),
    )
    max_volatility_liquidity_gap = _max_or_zero(
        tuple(row.volatility_liquidity_gap for row in rows),
    )
    final_confidence = _final_confidence(
        average_base_confidence=average_base_confidence,
        stale_evidence_share=stale_evidence_share,
        max_volatility_liquidity_gap=max_volatility_liquidity_gap,
        config=config,
    )
    reason_codes = _report_reason_codes(
        rows,
        source_family_count=source_family_count,
        stale_evidence_share=stale_evidence_share,
        max_volatility_liquidity_gap=max_volatility_liquidity_gap,
        final_confidence=final_confidence,
        config=config,
    )
    digest_status = _digest_status(reason_codes)
    return MarketResearchOilEventMemoryDigestReport(
        generated_at=generated_at,
        config_version=config.config_version,
        digest_status=digest_status,
        evidence_count=evidence_count,
        source_family_count=source_family_count,
        pass_count=_status_count(digest_status, "pass"),
        watch_count=_status_count(digest_status, "watch"),
        blocked_count=_status_count(digest_status, "blocked", rows),
        stale_evidence_count=stale_evidence_count,
        stale_evidence_share=stale_evidence_share,
        max_inventory_data_age_hours=_max_or_zero(
            tuple(row.inventory_data_age_hours for row in rows),
        ),
        min_catalyst_quality_score=_min_or_zero(
            tuple(row.opec_geopolitical_catalyst_quality for row in rows),
        ),
        min_futures_curve_signal=_min_or_zero(
            tuple(row.futures_curve_signal for row in rows),
        ),
        min_demand_macro_confirmation=_min_or_zero(
            tuple(row.demand_macro_confirmation for row in rows),
        ),
        max_volatility_liquidity_gap=max_volatility_liquidity_gap,
        average_base_confidence=average_base_confidence,
        final_confidence=final_confidence,
        reason_codes=reason_codes,
        evidence_rows=rows,
    )


def market_research_oil_event_memory_digest_payload(
    report: MarketResearchOilEventMemoryDigestReport,
) -> dict[str, Any]:
    if type(report) is not MarketResearchOilEventMemoryDigestReport:
        raise ValueError("report must be a MarketResearchOilEventMemoryDigestReport")
    return _payload_value(report)


def _evidence_row_from_evidence(
    evidence: MarketResearchOilEventMemoryDigestEvidence,
    *,
    config: MarketResearchOilEventMemoryDigestConfig,
    generated_at: datetime,
) -> MarketResearchOilEventMemoryDigestEvidenceRow:
    inventory_data_age_hours = _hours_between(
        generated_at,
        evidence.inventory_data_published_at,
    )
    stale_evidence = (
        inventory_data_age_hours > config.max_inventory_age_hours
        or evidence.observed_at > generated_at
    )
    return MarketResearchOilEventMemoryDigestEvidenceRow(
        market_slug=evidence.market_slug,
        evidence_id=evidence.evidence_id,
        source_family=evidence.source_family,
        observed_at=evidence.observed_at,
        inventory_data_published_at=evidence.inventory_data_published_at,
        inventory_data_age_hours=inventory_data_age_hours,
        opec_geopolitical_catalyst_quality=(
            evidence.opec_geopolitical_catalyst_quality
        ),
        futures_curve_signal=evidence.futures_curve_signal,
        demand_macro_confirmation=evidence.demand_macro_confirmation,
        volatility_liquidity_gap=evidence.volatility_liquidity_gap,
        base_confidence=evidence.base_confidence,
        redacted_summary=_redact_text(evidence.summary),
        redacted_reference=_redact_reference(evidence.reference),
        stale_evidence=stale_evidence,
        reason_codes=evidence.reason_codes,
    )


def _report_reason_codes(
    rows: tuple[MarketResearchOilEventMemoryDigestEvidenceRow, ...],
    *,
    source_family_count: Decimal,
    stale_evidence_share: Decimal,
    max_volatility_liquidity_gap: Decimal,
    final_confidence: Decimal,
    config: MarketResearchOilEventMemoryDigestConfig,
) -> tuple[str, ...]:
    if not rows:
        return ("oil_event_memory_digest_empty",)
    reason_codes: list[str] = []
    for row in rows:
        reason_codes.extend(row.reason_codes)

    if any(row.stale_evidence for row in rows):
        reason_codes.append("inventory_data_stale")
    else:
        reason_codes.append("fresh_inventory_data")

    if any(
        row.opec_geopolitical_catalyst_quality < config.min_catalyst_quality_score
        for row in rows
    ):
        reason_codes.append("opec_geopolitical_catalyst_quality_weak")
    else:
        reason_codes.append("opec_geopolitical_catalyst_quality_confirmed")

    if any(row.futures_curve_signal < config.min_curve_signal_score for row in rows):
        reason_codes.append("futures_curve_signal_weak")
    else:
        reason_codes.append("futures_curve_signal_confirmed")

    if any(
        row.demand_macro_confirmation < config.min_demand_confirmation_score
        for row in rows
    ):
        reason_codes.append("demand_macro_confirmation_weak")
    else:
        reason_codes.append("demand_macro_confirmed")

    if source_family_count < config.min_source_family_count:
        reason_codes.append("source_family_diversity_gap")
    else:
        reason_codes.append("source_family_diversity_passed")

    if stale_evidence_share > config.max_stale_evidence_share:
        reason_codes.append("stale_evidence_share_exceeds_threshold")

    if max_volatility_liquidity_gap > config.max_volatility_liquidity_gap:
        reason_codes.append("volatility_liquidity_gap_exceeds_threshold")
    else:
        reason_codes.append("volatility_liquidity_gap_acceptable")

    if final_confidence < config.min_final_confidence:
        reason_codes.append("final_confidence_below_threshold")

    if not _has_blocking_reason(reason_codes):
        reason_codes.append("oil_event_memory_digest_passed")
    return _normalize_reason_codes(tuple(reason_codes))


def _digest_status(reason_codes: tuple[str, ...]) -> str:
    if reason_codes == ("oil_event_memory_digest_empty",):
        return "blocked"
    if _has_blocking_reason(reason_codes):
        return "blocked"
    return "pass"


def _has_blocking_reason(reason_codes: Iterable[str]) -> bool:
    blocking_reasons = {
        "demand_macro_confirmation_weak",
        "final_confidence_below_threshold",
        "futures_curve_signal_weak",
        "inventory_data_stale",
        "opec_geopolitical_catalyst_quality_weak",
        "source_family_diversity_gap",
        "stale_evidence_share_exceeds_threshold",
        "volatility_liquidity_gap_exceeds_threshold",
    }
    return any(reason_code in blocking_reasons for reason_code in reason_codes)


def _validate_report_consistency(report: MarketResearchOilEventMemoryDigestReport) -> None:
    rows = report.evidence_rows
    if report.evidence_count != _count_decimal(len(rows)):
        raise ValueError("evidence_count must match evidence_rows")
    if report.source_family_count != _count_decimal(len({row.source_family for row in rows})):
        raise ValueError("source_family_count must match evidence_rows")
    expected_pass_count = _status_count(report.digest_status, "pass")
    expected_watch_count = _status_count(report.digest_status, "watch")
    expected_blocked_count = _status_count(report.digest_status, "blocked", rows)
    if report.pass_count != expected_pass_count:
        raise ValueError("pass_count must match digest_status")
    if report.watch_count != expected_watch_count:
        raise ValueError("watch_count must match digest_status")
    if report.blocked_count != expected_blocked_count:
        raise ValueError("blocked_count must match digest_status")
    if report.pass_count + report.watch_count + report.blocked_count != _count_decimal(
        1 if rows else 0,
    ):
        raise ValueError("status counts must match digest rows")
    if report.stale_evidence_count != _count_decimal(
        sum(1 for row in rows if row.stale_evidence),
    ):
        raise ValueError("stale_evidence_count must match evidence_rows")
    if report.stale_evidence_share != _ratio(
        report.stale_evidence_count,
        report.evidence_count,
    ):
        raise ValueError("stale_evidence_share must match stale_evidence_count")
    if report.max_inventory_data_age_hours != _max_or_zero(
        tuple(row.inventory_data_age_hours for row in rows),
    ):
        raise ValueError("max_inventory_data_age_hours must match evidence_rows")
    if report.min_catalyst_quality_score != _min_or_zero(
        tuple(row.opec_geopolitical_catalyst_quality for row in rows),
    ):
        raise ValueError("min_catalyst_quality_score must match evidence_rows")
    if report.min_futures_curve_signal != _min_or_zero(
        tuple(row.futures_curve_signal for row in rows),
    ):
        raise ValueError("min_futures_curve_signal must match evidence_rows")
    if report.min_demand_macro_confirmation != _min_or_zero(
        tuple(row.demand_macro_confirmation for row in rows),
    ):
        raise ValueError("min_demand_macro_confirmation must match evidence_rows")
    if report.max_volatility_liquidity_gap != _max_or_zero(
        tuple(row.volatility_liquidity_gap for row in rows),
    ):
        raise ValueError("max_volatility_liquidity_gap must match evidence_rows")
    if report.average_base_confidence != _average(tuple(row.base_confidence for row in rows)):
        raise ValueError("average_base_confidence must match evidence_rows")
    expected_status = _digest_status(report.reason_codes)
    if report.digest_status != expected_status:
        raise ValueError("digest_status must match reason_codes")


def _normalize_evidence(
    evidence: Iterable[MarketResearchOilEventMemoryDigestEvidence],
) -> tuple[MarketResearchOilEventMemoryDigestEvidence, ...]:
    if isinstance(evidence, (str, bytes)) or not isinstance(evidence, Iterable):
        raise ValueError("evidence must be an iterable")
    normalized = tuple(evidence)
    for item in normalized:
        if type(item) is not MarketResearchOilEventMemoryDigestEvidence:
            raise ValueError(
                "evidence must contain MarketResearchOilEventMemoryDigestEvidence",
            )
        _require_hard_flags(item)
    return normalized


def _normalize_evidence_rows(
    rows: Iterable[MarketResearchOilEventMemoryDigestEvidenceRow],
) -> tuple[MarketResearchOilEventMemoryDigestEvidenceRow, ...]:
    if isinstance(rows, (str, bytes)) or not isinstance(rows, Iterable):
        raise ValueError("evidence_rows must be an iterable")
    normalized = tuple(rows)
    for row in normalized:
        if type(row) is not MarketResearchOilEventMemoryDigestEvidenceRow:
            raise ValueError(
                "evidence_rows must contain MarketResearchOilEventMemoryDigestEvidenceRow",
            )
        _require_hard_flags(row)
    _require_unique_evidence_row_identities(normalized)
    return tuple(sorted(normalized, key=_evidence_row_sort_key))


def _evidence_row_sort_key(
    row: MarketResearchOilEventMemoryDigestEvidenceRow,
) -> tuple[str, str, str]:
    return (row.market_slug, row.evidence_id, row.source_family)


def _require_unique_evidence_row_identities(
    rows: tuple[MarketResearchOilEventMemoryDigestEvidenceRow, ...],
) -> None:
    seen: set[tuple[str, str, str]] = set()
    for row in rows:
        identity = _evidence_row_sort_key(row)
        if identity in seen:
            raise ValueError("duplicate evidence row identity")
        seen.add(identity)


def _hours_between(later: datetime, earlier: datetime) -> Decimal:
    delta = later - earlier
    if delta.total_seconds() < 0:
        raise ValueError("inventory_data_published_at must not be after generated_at")
    seconds = Decimal(delta.days * 86400 + delta.seconds)
    if delta.microseconds:
        seconds += Decimal(delta.microseconds) / Decimal("1000000")
    return _quantize_decimal(seconds / Decimal("3600"))


def _final_confidence(
    *,
    average_base_confidence: Decimal,
    stale_evidence_share: Decimal,
    max_volatility_liquidity_gap: Decimal,
    config: MarketResearchOilEventMemoryDigestConfig,
) -> Decimal:
    decayed = (
        average_base_confidence
        - stale_evidence_share * config.confidence_decay_per_stale_share
        - max_volatility_liquidity_gap * config.confidence_decay_per_gap
    )
    if decayed < ZERO:
        return ZERO
    if decayed > ONE:
        return ONE
    return _quantize_decimal(decayed)


def _average(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return ZERO
    return _quantize_decimal(sum(values, ZERO) / _count_decimal(len(values)))


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO:
        return ZERO
    return _quantize_decimal(numerator / denominator)


def _min_or_zero(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return ZERO
    return min(values)


def _max_or_zero(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return ZERO
    return max(values)


def _status_count(
    status: str,
    candidate: str,
    rows: tuple[MarketResearchOilEventMemoryDigestEvidenceRow, ...] | None = None,
) -> Decimal:
    if status == "blocked" and not rows:
        return ZERO
    return _count_decimal(1 if status == candidate else 0)


def _count_decimal(value: int) -> Decimal:
    return _quantize_decimal(Decimal(value))


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


def _require_positive_decimal(field_name: str, value: Decimal) -> None:
    if value <= ZERO:
        raise ValueError(f"{field_name} must be positive")


def _require_unit_interval(field_name: str, value: Decimal) -> None:
    if value < ZERO or value > ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")


def _require_digest_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in DIGEST_STATUSES:
        raise ValueError(f"{field_name} must be pass, watch, or blocked")


def _normalize_reason_codes(reason_codes: Iterable[str]) -> tuple[str, ...]:
    if isinstance(reason_codes, (str, bytes)) or not isinstance(reason_codes, Iterable):
        raise ValueError("reason_codes must be an iterable")
    normalized: list[str] = []
    for reason_code in reason_codes:
        _require_canonical_string("reason_code", reason_code)
        if _contains_sensitive_marker(reason_code) or _contains_public_surface_term(reason_code):
            reason_code = _public_digest(reason_code)
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


def _redact_text(value: str) -> str:
    if _contains_sensitive_marker(value) or _contains_public_surface_term(value):
        return _public_digest(value)
    redacted = EMAIL_PATTERN.sub("[REDACTED_EMAIL]", value)
    redacted = URL_PATTERN.sub("[REDACTED_URL]", redacted)
    redacted = WALLET_PATTERN.sub("[REDACTED_ID]", redacted)
    return redacted


def _redact_reference(reference: str) -> str:
    lower = reference.lower()
    reference_prefix = lower.split("?", 1)[0]
    if any(term in lower for term in REFERENCE_HASH_TERMS):
        return _public_digest(reference)
    if any(marker in reference_prefix for marker in SENSITIVE_REFERENCE_MARKERS):
        return _public_digest(reference)
    if "?" in reference and any(marker in lower for marker in SENSITIVE_REFERENCE_MARKERS):
        return reference.split("?", 1)[0] + "?<redacted>"
    if any(marker in lower for marker in SENSITIVE_REFERENCE_MARKERS):
        return "<redacted>"
    return _redact_text(reference)


def _contains_public_surface_term(value: str) -> bool:
    lower = value.lower()
    return any(term in lower for term in PUBLIC_SURFACE_TERMS)


def _contains_sensitive_marker(value: str) -> bool:
    lower = value.lower()
    return any(marker in lower for marker in SENSITIVE_REFERENCE_MARKERS)


def _public_digest(value: str) -> str:
    return "sha256:" + hashlib.sha256(value.encode("utf-8")).hexdigest()


def _payload_value(value: object) -> Any:
    if isinstance(value, Decimal):
        return f"{value:.6f}"
    if type(value) is datetime:
        return value.isoformat()
    if type(value) is str:
        _require_safe_payload_string(value)
        if URL_PATTERN.search(value):
            return _public_digest(value)
        return value
    if is_dataclass(value) and not isinstance(value, type):
        _require_payload_dataclass(value)
        return {
            field.name: _payload_value(getattr(value, field.name))
            for field in fields(value)
        }
    if isinstance(value, tuple):
        return [_payload_value(item) for item in value]
    return value


def _require_payload_dataclass(value: object) -> None:
    if type(value) not in (
        MarketResearchOilEventMemoryDigestEvidenceRow,
        MarketResearchOilEventMemoryDigestReport,
    ):
        raise ValueError("payload contains unsupported dataclass")
    _require_hard_flags(value)


def _require_safe_payload_string(value: str) -> None:
    if _contains_sensitive_marker(value) or _contains_public_surface_term(value):
        raise ValueError("payload string has unsafe public surface")
