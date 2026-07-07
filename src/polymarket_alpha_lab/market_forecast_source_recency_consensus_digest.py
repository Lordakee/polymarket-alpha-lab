"""Pure in-memory market forecast source recency consensus digest.

This reducer turns caller-supplied forecast source rows into a deterministic
diagnostic report. It is paper-only, report-only, readonly, and does not save
state or reach outside the supplied inputs.
"""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable
from dataclasses import dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation
from hashlib import sha256
import json
from typing import Any


__all__ = (
    "MarketForecastSourceRecencyConsensusConfig",
    "MarketForecastSourceRecencyConsensusDigest",
    "MarketForecastSourceRecencyConsensusReasonCodeCount",
    "MarketForecastSourceRecencyConsensusRow",
    "MarketForecastSourceRecencyConsensusSource",
    "build_market_forecast_source_recency_consensus_digest",
    "market_forecast_source_recency_consensus_digest_payload",
)


DEFAULT_CONFIG_VERSION = "market-forecast-source-recency-consensus-digest-v0"
STATUSES = ("pass", "watch", "blocked")
SOURCE_ROLES = ("primary", "secondary", "proxy")
ZERO = Decimal("0")
ONE = Decimal("1")
RATIO_QUANTUM = Decimal("0.000001")
REDACTED_REFERENCE = "[redacted_reference]"


def _join_parts(*parts: str) -> str:
    return "".join(parts)


UNSAFE_SURFACE_FRAGMENTS = frozenset(
    (
        _join_parts("li", "ve"),
        _join_parts("au", "th"),
        _join_parts("wal", "let"),
        _join_parts("ord", "er"),
        _join_parts("net", "work"),
        _join_parts("data", "base"),
        _join_parts("per", "sist"),
        _join_parts("bro", "ker"),
        _join_parts("sig", "ning"),
        _join_parts("tra", "de"),
        "account",
        "balance",
        "cancel",
        "client",
        "private_key",
        "secret",
        "submit",
        "token=",
    ),
)


class _Missing:
    pass


_MISSING = _Missing()


@dataclass(frozen=True)
class MarketForecastSourceRecencyConsensusConfig:
    config_version: str = DEFAULT_CONFIG_VERSION
    fresh_age_seconds: Decimal = Decimal("3600")
    stale_age_seconds: Decimal = Decimal("86400")
    min_independent_source_families: Decimal = Decimal("2")
    min_consensus_ratio: Decimal = Decimal("0.666667")
    max_probability_dispersion: Decimal = Decimal("0.150000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("config_version", self.config_version)
        object.__setattr__(
            self,
            "fresh_age_seconds",
            _require_positive_decimal("fresh_age_seconds", self.fresh_age_seconds),
        )
        object.__setattr__(
            self,
            "stale_age_seconds",
            _require_positive_decimal("stale_age_seconds", self.stale_age_seconds),
        )
        if self.stale_age_seconds <= self.fresh_age_seconds:
            raise ValueError("stale_age_seconds must be greater than fresh_age_seconds")
        object.__setattr__(
            self,
            "min_independent_source_families",
            _require_positive_count_decimal(
                "min_independent_source_families",
                self.min_independent_source_families,
            ),
        )
        object.__setattr__(
            self,
            "min_consensus_ratio",
            _require_probability_decimal("min_consensus_ratio", self.min_consensus_ratio),
        )
        object.__setattr__(
            self,
            "max_probability_dispersion",
            _require_probability_decimal(
                "max_probability_dispersion",
                self.max_probability_dispersion,
            ),
        )
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class MarketForecastSourceRecencyConsensusSource:
    market_slug: str
    forecast_id: str
    source_id: str
    source_family: str
    source_role: str
    source_observed_at: datetime | None
    forecast_probability: Decimal | None
    consensus_probability: Decimal | None
    source_weight: Decimal
    reference: str
    reason_codes: tuple[str, ...] = ()
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        for field_name in (
            "market_slug",
            "forecast_id",
            "source_role",
        ):
            _require_canonical_string(field_name, getattr(self, field_name))
        if self.source_role not in SOURCE_ROLES:
            raise ValueError("source_role must be a known source role")
        for field_name in ("source_id", "source_family"):
            _require_optional_canonical_string(field_name, getattr(self, field_name))
        if type(self.reference) is not str:
            raise ValueError("reference must be a string")
        object.__setattr__(
            self,
            "source_observed_at",
            _as_optional_utc("source_observed_at", self.source_observed_at),
        )
        object.__setattr__(
            self,
            "forecast_probability",
            _require_optional_probability_decimal(
                "forecast_probability",
                self.forecast_probability,
            ),
        )
        object.__setattr__(
            self,
            "consensus_probability",
            _require_optional_probability_decimal(
                "consensus_probability",
                self.consensus_probability,
            ),
        )
        object.__setattr__(
            self,
            "source_weight",
            _require_nonnegative_decimal("source_weight", self.source_weight),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_string_tuple("reason_codes", self.reason_codes, allow_empty=True),
        )
        _require_hard_flags("source", self)
        _validate_source_shape(self)


@dataclass(frozen=True)
class MarketForecastSourceRecencyConsensusRow:
    market_slug: str
    forecast_id: str
    source_count: Decimal
    independent_source_family_count: Decimal
    latest_source_observed_at: datetime | None
    latest_source_age_seconds: Decimal | None
    stale_source_count: Decimal
    consensus_source_count: Decimal
    consensus_ratio: Decimal
    average_forecast_probability: Decimal | None
    consensus_probability: Decimal | None
    probability_dispersion: Decimal | None
    source_ids: tuple[str, ...]
    source_families: tuple[str, ...]
    source_roles: tuple[str, ...]
    redacted_references: tuple[str, ...]
    status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        for field_name in ("market_slug", "forecast_id"):
            _require_canonical_string(field_name, getattr(self, field_name))
        for field_name in (
            "source_count",
            "independent_source_family_count",
            "stale_source_count",
            "consensus_source_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_count_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "latest_source_observed_at",
            _as_optional_utc("latest_source_observed_at", self.latest_source_observed_at),
        )
        object.__setattr__(
            self,
            "latest_source_age_seconds",
            _require_optional_nonnegative_decimal(
                "latest_source_age_seconds",
                self.latest_source_age_seconds,
            ),
        )
        object.__setattr__(
            self,
            "consensus_ratio",
            _require_probability_decimal("consensus_ratio", self.consensus_ratio),
        )
        for field_name in (
            "average_forecast_probability",
            "consensus_probability",
            "probability_dispersion",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_optional_probability_decimal(
                    field_name,
                    getattr(self, field_name),
                ),
            )
        for field_name in (
            "source_ids",
            "source_families",
            "source_roles",
            "redacted_references",
            "reason_codes",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_string_tuple(
                    field_name,
                    getattr(self, field_name),
                    allow_empty=True,
                ),
            )
        _require_status("status", self.status)
        _require_hard_flags("row", self)
        _validate_row_consistency(self)


@dataclass(frozen=True)
class MarketForecastSourceRecencyConsensusReasonCodeCount:
    reason_code: str
    count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("reason_code", self.reason_code)
        object.__setattr__(
            self,
            "count",
            _require_positive_count_decimal("count", self.count),
        )
        _require_hard_flags("reason_code_count", self)


@dataclass(frozen=True)
class MarketForecastSourceRecencyConsensusDigest:
    generated_at: datetime
    config_version: str
    market_count: Decimal
    source_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    blocked_count: Decimal
    stale_source_count: Decimal
    consensus_source_count: Decimal
    average_consensus_ratio: Decimal | None
    average_probability_dispersion: Decimal | None
    status: str
    rows: tuple[MarketForecastSourceRecencyConsensusRow, ...]
    reason_code_counts: tuple[MarketForecastSourceRecencyConsensusReasonCodeCount, ...]
    reason_codes: tuple[str, ...]
    derived_validation_digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        for field_name in (
            "market_count",
            "source_count",
            "pass_count",
            "watch_count",
            "blocked_count",
            "stale_source_count",
            "consensus_source_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_count_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "average_consensus_ratio",
            "average_probability_dispersion",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_optional_probability_decimal(field_name, getattr(self, field_name)),
            )
        _require_status("status", self.status)
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_string_tuple("reason_codes", self.reason_codes, allow_empty=False),
        )
        _require_sha256_hex("derived_validation_digest", self.derived_validation_digest)
        _require_hard_flags("report", self)
        _validate_digest_consistency(self)


def build_market_forecast_source_recency_consensus_digest(
    sources: Iterable[object],
    *,
    config: MarketForecastSourceRecencyConsensusConfig,
    generated_at: datetime,
) -> MarketForecastSourceRecencyConsensusDigest:
    if type(config) is not MarketForecastSourceRecencyConsensusConfig:
        raise ValueError("config must be a MarketForecastSourceRecencyConsensusConfig")
    _require_hard_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    source_items = _normalize_sources(sources)
    for item in source_items:
        _reject_future_source_observed_at(item, generated_at_utc)

    grouped: dict[tuple[str, str], list[MarketForecastSourceRecencyConsensusSource]] = {}
    for item in source_items:
        grouped.setdefault((item.market_slug, item.forecast_id), []).append(item)

    rows = tuple(
        _row_from_group(
            market_slug=market_slug,
            forecast_id=forecast_id,
            sources=tuple(grouped[(market_slug, forecast_id)]),
            config=config,
            generated_at=generated_at_utc,
        )
        for market_slug, forecast_id in sorted(grouped)
    )
    reason_codes = _summary_reason_codes(rows)

    report_values = {
        "generated_at": generated_at_utc,
        "config_version": config.config_version,
        "market_count": _decimal_count(len(rows)),
        "source_count": sum((row.source_count for row in rows), ZERO),
        "pass_count": _decimal_count(_status_count(rows, "pass")),
        "watch_count": _decimal_count(_status_count(rows, "watch")),
        "blocked_count": _decimal_count(_status_count(rows, "blocked")),
        "stale_source_count": sum((row.stale_source_count for row in rows), ZERO),
        "consensus_source_count": sum((row.consensus_source_count for row in rows), ZERO),
        "average_consensus_ratio": _average_consensus_ratio(rows),
        "average_probability_dispersion": _average_probability_dispersion(rows),
        "status": _summary_status(reason_codes),
        "rows": rows,
        "reason_code_counts": _reason_code_counts(rows, reason_codes),
        "reason_codes": reason_codes,
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    report_values["derived_validation_digest"] = _derived_validation_digest_for(
        report_values,
    )
    return MarketForecastSourceRecencyConsensusDigest(**report_values)


def market_forecast_source_recency_consensus_digest_payload(
    report: MarketForecastSourceRecencyConsensusDigest | dict[str, Any],
) -> dict[str, Any]:
    label = "forecast source recency consensus digest payload"
    if type(report) is not MarketForecastSourceRecencyConsensusDigest:
        if type(report) is not dict:
            raise ValueError(
                "report must be a MarketForecastSourceRecencyConsensusDigest or payload dict",
            )
        _validate_public_payload(label, report)
        payload = _payload_value(report)
        _validate_public_payload(label, payload)
        if not isinstance(payload, dict):
            raise ValueError("report payload must be a JSON object")
        return payload
    _require_hard_flags("report", report)
    payload = _payload_value(report)
    if not isinstance(payload, dict):
        raise ValueError("report payload must be a JSON object")
    _validate_public_payload(label, payload)
    return payload


def _row_from_group(
    *,
    market_slug: str,
    forecast_id: str,
    sources: tuple[MarketForecastSourceRecencyConsensusSource, ...],
    config: MarketForecastSourceRecencyConsensusConfig,
    generated_at: datetime,
) -> MarketForecastSourceRecencyConsensusRow:
    present = tuple(
        sorted(
            (item for item in sources if _has_source_payload(item)),
            key=lambda item: (item.source_id, item.source_family, item.source_role),
        ),
    )
    if not present:
        return MarketForecastSourceRecencyConsensusRow(
            market_slug=market_slug,
            forecast_id=forecast_id,
            source_count=ZERO,
            independent_source_family_count=ZERO,
            latest_source_observed_at=None,
            latest_source_age_seconds=None,
            stale_source_count=ZERO,
            consensus_source_count=ZERO,
            consensus_ratio=ZERO,
            average_forecast_probability=None,
            consensus_probability=tuple(sources)[0].consensus_probability if sources else None,
            probability_dispersion=None,
            source_ids=(),
            source_families=(),
            source_roles=(),
            redacted_references=(),
            status="blocked",
            reason_codes=("missing_forecast_sources",),
        )

    scored = tuple(
        (
            item,
            _age_seconds(generated_at, item.source_observed_at),
        )
        for item in present
        if item.source_observed_at is not None
    )
    latest_item, latest_age = min(scored, key=lambda value: value[1])
    stale_count = sum(1 for _, age in scored if age > config.stale_age_seconds)
    probabilities = tuple(item.forecast_probability for item in present)
    if any(value is None for value in probabilities):
        raise ValueError("forecast_probability is required for present sources")
    consensus_probability = present[0].consensus_probability
    if consensus_probability is None:
        raise ValueError("consensus_probability is required for present sources")
    if any(item.consensus_probability != consensus_probability for item in present):
        raise ValueError("consensus_probability must be stable within a forecast")

    probability_values = tuple(
        value for value in probabilities if value is not None
    )
    average_forecast_probability = _quantize(
        sum(probability_values, ZERO) / Decimal(len(probability_values)),
    )
    deltas = tuple(abs(value - consensus_probability) for value in probability_values)
    probability_dispersion = _quantize(max(deltas))
    consensus_count = sum(
        1 for delta in deltas if delta <= config.max_probability_dispersion
    )
    reason_codes = _row_reason_codes(
        source_count=len(present),
        independent_source_family_count=len({item.source_family for item in present}),
        stale_count=stale_count,
        consensus_ratio=_quantize(Decimal(consensus_count) / Decimal(len(present))),
        probability_dispersion=probability_dispersion,
        input_reason_codes=tuple(
            reason_code for item in present for reason_code in item.reason_codes
        ),
        config=config,
    )

    return MarketForecastSourceRecencyConsensusRow(
        market_slug=market_slug,
        forecast_id=forecast_id,
        source_count=_decimal_count(len(present)),
        independent_source_family_count=_decimal_count(
            len({item.source_family for item in present}),
        ),
        latest_source_observed_at=latest_item.source_observed_at,
        latest_source_age_seconds=latest_age,
        stale_source_count=_decimal_count(stale_count),
        consensus_source_count=_decimal_count(consensus_count),
        consensus_ratio=_quantize(Decimal(consensus_count) / Decimal(len(present))),
        average_forecast_probability=average_forecast_probability,
        consensus_probability=consensus_probability,
        probability_dispersion=probability_dispersion,
        source_ids=tuple(item.source_id for item in present),
        source_families=tuple(sorted({item.source_family for item in present})),
        source_roles=tuple(sorted({item.source_role for item in present})),
        redacted_references=tuple(
            sorted({_redact_reference(item.reference) for item in present})
        ),
        status=_row_status(reason_codes),
        reason_codes=reason_codes,
    )


def _normalize_sources(
    sources: Iterable[object],
) -> tuple[MarketForecastSourceRecencyConsensusSource, ...]:
    if isinstance(sources, (str, bytes)):
        raise ValueError("sources must be an iterable")
    try:
        values = tuple(sources)
    except TypeError as exc:
        raise ValueError("sources must be an iterable") from exc
    return tuple(_coerce_source(value) for value in values)


def _coerce_source(value: object) -> MarketForecastSourceRecencyConsensusSource:
    if type(value) is MarketForecastSourceRecencyConsensusSource:
        _require_hard_flags("source", value)
        return value
    _require_hard_flags("source", value)
    return MarketForecastSourceRecencyConsensusSource(
        market_slug=_field_value(value, "market_slug"),
        forecast_id=_field_value(value, "forecast_id"),
        source_id=_field_value(value, "source_id"),
        source_family=_field_value(value, "source_family"),
        source_role=_field_value(value, "source_role"),
        source_observed_at=_field_value(value, "source_observed_at"),
        forecast_probability=_field_value(value, "forecast_probability"),
        consensus_probability=_field_value(value, "consensus_probability"),
        source_weight=_field_value(value, "source_weight"),
        reference=_field_value(value, "reference"),
        reason_codes=_field_value(value, "reason_codes", default=()),
        paper_only=_field_value(value, "paper_only"),
        report_only=_field_value(value, "report_only"),
        readonly=_field_value(value, "readonly"),
    )


def _has_source_payload(item: MarketForecastSourceRecencyConsensusSource) -> bool:
    return bool(
        item.source_id
        and item.source_family
        and item.source_observed_at is not None
        and item.forecast_probability is not None
    )


def _row_reason_codes(
    *,
    source_count: int,
    independent_source_family_count: int,
    stale_count: int,
    consensus_ratio: Decimal,
    probability_dispersion: Decimal,
    input_reason_codes: tuple[str, ...],
    config: MarketForecastSourceRecencyConsensusConfig,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    passes = (
        source_count > 0
        and independent_source_family_count >= int(config.min_independent_source_families)
        and stale_count == 0
        and consensus_ratio >= config.min_consensus_ratio
        and probability_dispersion <= config.max_probability_dispersion
    )
    reason_codes.append(
        "forecast_source_recency_consensus_pass"
        if passes
        else "forecast_source_recency_consensus_watch",
    )
    reason_codes.append(
        "forecast_sources_independent"
        if independent_source_family_count >= int(config.min_independent_source_families)
        else "forecast_sources_insufficient_independence",
    )
    reason_codes.append("forecast_sources_stale" if stale_count else "forecast_sources_current")
    reason_codes.append(
        "forecast_sources_in_consensus"
        if consensus_ratio >= config.min_consensus_ratio
        else "forecast_sources_below_consensus",
    )
    reason_codes.append(
        "probability_dispersion_high"
        if probability_dispersion > config.max_probability_dispersion
        else "probability_dispersion_ok",
    )
    for reason_code in input_reason_codes:
        reason_codes.append(f"input_{reason_code}")
    if passes:
        return (
            "forecast_sources_current",
            "forecast_sources_independent",
            "forecast_sources_in_consensus",
            "forecast_source_recency_consensus_pass",
        )
    return tuple(sorted(set(reason_codes)))


def _row_status(reason_codes: tuple[str, ...]) -> str:
    if "missing_forecast_sources" in reason_codes:
        return "blocked"
    if "forecast_source_recency_consensus_watch" in reason_codes:
        return "watch"
    return "pass"


def _summary_reason_codes(
    rows: tuple[MarketForecastSourceRecencyConsensusRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return ("no_forecast_sources",)
    if any(row.status == "blocked" for row in rows):
        return tuple(
            sorted(
                {
                    reason_code
                    for row in rows
                    for reason_code in row.reason_codes
                    if row.status == "blocked" or reason_code.startswith("input_")
                },
            ),
        )
    if all(row.status == "pass" for row in rows):
        return ("forecast_source_recency_consensus_pass",)
    return tuple(
        sorted(
            {
                reason_code
                for row in rows
                for reason_code in row.reason_codes
                if reason_code not in ("forecast_sources_independent",)
            },
        ),
    )


def _summary_status(reason_codes: tuple[str, ...]) -> str:
    if reason_codes in (("no_forecast_sources",), ("missing_forecast_sources",)):
        return "blocked"
    if "missing_forecast_sources" in reason_codes:
        return "blocked"
    if "forecast_source_recency_consensus_watch" in reason_codes:
        return "watch"
    return "pass"


def _reason_code_counts(
    rows: tuple[MarketForecastSourceRecencyConsensusRow, ...],
    reason_codes: tuple[str, ...],
) -> tuple[MarketForecastSourceRecencyConsensusReasonCodeCount, ...]:
    if not rows:
        return (
            MarketForecastSourceRecencyConsensusReasonCodeCount(
                reason_code=reason_codes[0],
                count=ONE,
            ),
        )
    counts: Counter[str] = Counter()
    for row in rows:
        counts.update(row.reason_codes)
    return tuple(
        MarketForecastSourceRecencyConsensusReasonCodeCount(
            reason_code=reason_code,
            count=_decimal_count(count),
        )
        for reason_code, count in sorted(counts.items(), key=lambda item: item[0])
    )


def _average_consensus_ratio(
    rows: tuple[MarketForecastSourceRecencyConsensusRow, ...],
) -> Decimal | None:
    scored_rows = tuple(row for row in rows if row.source_count > ZERO)
    if not scored_rows:
        return None
    return _quantize(
        sum((row.consensus_ratio for row in scored_rows), ZERO)
        / Decimal(len(scored_rows)),
    )


def _average_probability_dispersion(
    rows: tuple[MarketForecastSourceRecencyConsensusRow, ...],
) -> Decimal | None:
    scored_rows = tuple(
        row for row in rows if row.probability_dispersion is not None
    )
    if not scored_rows:
        return None
    return _quantize(
        sum((row.probability_dispersion for row in scored_rows), ZERO)
        / Decimal(len(scored_rows)),
    )


def _age_seconds(generated_at: datetime, observed_at: datetime | None) -> Decimal:
    if observed_at is None:
        raise ValueError("source_observed_at is required")
    delta = generated_at - observed_at
    return (
        Decimal(delta.days * 86_400)
        + Decimal(delta.seconds)
        + (Decimal(delta.microseconds) / Decimal("1000000"))
    )


def _reject_future_source_observed_at(
    item: MarketForecastSourceRecencyConsensusSource,
    generated_at: datetime,
) -> None:
    if item.source_observed_at is not None and item.source_observed_at > generated_at:
        raise ValueError("source_observed_at must not be after generated_at")


def _status_count(
    rows: tuple[MarketForecastSourceRecencyConsensusRow, ...],
    status: str,
) -> int:
    return sum(1 for row in rows if row.status == status)


def _normalize_rows(
    rows: tuple[MarketForecastSourceRecencyConsensusRow, ...],
) -> tuple[MarketForecastSourceRecencyConsensusRow, ...]:
    if type(rows) is not tuple:
        raise ValueError("rows must be a tuple")
    for row in rows:
        if type(row) is not MarketForecastSourceRecencyConsensusRow:
            raise ValueError(
                "rows must contain MarketForecastSourceRecencyConsensusRow values",
            )
        _require_hard_flags("row", row)
    sorted_rows = tuple(sorted(rows, key=lambda row: (row.market_slug, row.forecast_id)))
    if rows != sorted_rows:
        raise ValueError("rows must be sorted by market_slug and forecast_id")
    return rows


def _normalize_reason_code_counts(
    rows: tuple[MarketForecastSourceRecencyConsensusReasonCodeCount, ...],
) -> tuple[MarketForecastSourceRecencyConsensusReasonCodeCount, ...]:
    if type(rows) is not tuple:
        raise ValueError("reason_code_counts must be a tuple")
    for row in rows:
        if type(row) is not MarketForecastSourceRecencyConsensusReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "MarketForecastSourceRecencyConsensusReasonCodeCount values",
            )
        _require_hard_flags("reason_code_count", row)
    sorted_rows = tuple(sorted(rows, key=lambda row: row.reason_code))
    if rows != sorted_rows:
        raise ValueError("reason_code_counts must be sorted by reason_code")
    return rows


def _validate_source_shape(item: MarketForecastSourceRecencyConsensusSource) -> None:
    if item.source_weight == ZERO and _has_source_payload(item):
        raise ValueError("source_weight must be positive for present sources")
    if item.source_weight > ONE:
        raise ValueError("source_weight must be between 0 and 1")
    if bool(item.source_id) != bool(item.source_family):
        raise ValueError("source_id and source_family must be supplied together")
    if item.forecast_probability is not None and item.source_observed_at is None:
        raise ValueError("source_observed_at is required with forecast_probability")


def _validate_row_consistency(row: MarketForecastSourceRecencyConsensusRow) -> None:
    if row.source_count == ZERO:
        if row.status != "blocked":
            raise ValueError("status must be blocked when source_count is zero")
        if row.reason_codes != ("missing_forecast_sources",):
            raise ValueError("reason_codes must identify missing forecast sources")
        if row.latest_source_observed_at is not None:
            raise ValueError("latest_source_observed_at must be absent without sources")
        if row.latest_source_age_seconds is not None:
            raise ValueError("latest_source_age_seconds must be absent without sources")
        return
    if row.independent_source_family_count > row.source_count:
        raise ValueError("independent_source_family_count must not exceed source_count")
    if row.stale_source_count > row.source_count:
        raise ValueError("stale_source_count must not exceed source_count")
    if row.consensus_source_count > row.source_count:
        raise ValueError("consensus_source_count must not exceed source_count")
    if row.latest_source_observed_at is None:
        raise ValueError("latest_source_observed_at is required with sources")
    if row.latest_source_age_seconds is None:
        raise ValueError("latest_source_age_seconds is required with sources")
    if row.average_forecast_probability is None:
        raise ValueError("average_forecast_probability is required with sources")
    if row.consensus_probability is None:
        raise ValueError("consensus_probability is required with sources")
    if row.probability_dispersion is None:
        raise ValueError("probability_dispersion is required with sources")
    if row.source_count != _decimal_count(len(row.source_ids)):
        raise ValueError("source_ids must match source_count")
    if row.independent_source_family_count != _decimal_count(len(row.source_families)):
        raise ValueError("source_families must match independent_source_family_count")
    expected_consensus_ratio = _quantize(row.consensus_source_count / row.source_count)
    if row.consensus_ratio != expected_consensus_ratio:
        raise ValueError("consensus_ratio must match consensus_source_count and source_count")
    if row.status != _row_status(row.reason_codes):
        raise ValueError("status must match reason_codes")


def _validate_digest_consistency(report: MarketForecastSourceRecencyConsensusDigest) -> None:
    if report.market_count != _decimal_count(len(report.rows)):
        raise ValueError("market_count must match rows")
    if report.source_count != sum((row.source_count for row in report.rows), ZERO):
        raise ValueError("source_count must match rows")
    if report.pass_count != _decimal_count(_status_count(report.rows, "pass")):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _decimal_count(_status_count(report.rows, "watch")):
        raise ValueError("watch_count must match rows")
    if report.blocked_count != _decimal_count(_status_count(report.rows, "blocked")):
        raise ValueError("blocked_count must match rows")
    if report.stale_source_count != sum(
        (row.stale_source_count for row in report.rows),
        ZERO,
    ):
        raise ValueError("stale_source_count must match rows")
    if report.consensus_source_count != sum(
        (row.consensus_source_count for row in report.rows),
        ZERO,
    ):
        raise ValueError("consensus_source_count must match rows")
    if report.average_consensus_ratio != _average_consensus_ratio(report.rows):
        raise ValueError("average_consensus_ratio must match rows")
    if report.average_probability_dispersion != _average_probability_dispersion(report.rows):
        raise ValueError("average_probability_dispersion must match rows")
    if report.status != _summary_status(report.reason_codes):
        raise ValueError("status must match reason_codes")
    if report.reason_codes != _summary_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")
    if report.reason_code_counts != _reason_code_counts(report.rows, report.reason_codes):
        raise ValueError("reason_code_counts must match rows")
    if report.derived_validation_digest != _expected_derived_validation_digest(report):
        raise ValueError("derived_validation_digest must match report values")


def _field_value(value: object, field_name: str, *, default: object = _MISSING) -> object:
    if is_dataclass(value):
        for field in fields(value):
            if field.name == field_name:
                return getattr(value, field_name)
    if hasattr(value, field_name):
        return getattr(value, field_name)
    if default is not _MISSING:
        return default
    raise ValueError(f"{field_name} is required")


def _redact_reference(reference: str) -> str:
    if not reference:
        return ""
    return REDACTED_REFERENCE


def _payload_value(value: object) -> object:
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, datetime):
        return value.isoformat()
    if is_dataclass(value) and not isinstance(value, type):
        return {
            field.name: _payload_value(getattr(value, field.name))
            for field in fields(value)
        }
    if isinstance(value, tuple):
        return [_payload_value(item) for item in value]
    if isinstance(value, list):
        return [_payload_value(item) for item in value]
    if isinstance(value, dict):
        return {str(key): _payload_value(item) for key, item in value.items()}
    return value


def _expected_derived_validation_digest(
    report: MarketForecastSourceRecencyConsensusDigest,
) -> str:
    return _derived_validation_digest_for(
        {
            field.name: getattr(report, field.name)
            for field in fields(report)
            if field.name != "derived_validation_digest"
        },
    )


def _derived_validation_digest_for(values: dict[str, object]) -> str:
    encoded = json.dumps(
        _payload_value(values),
        sort_keys=True,
        separators=(",", ":"),
    )
    return sha256(encoded.encode("utf-8")).hexdigest()


def _validate_public_payload(label: str, payload: object) -> None:
    if type(payload) is not dict:
        raise ValueError(f"{label} must be a JSON object")
    _require_payload_flags(label, payload)
    _reject_unsafe_public_surfaces(label, payload)
    _reject_public_numeric_primitives(label, payload)
    _reject_public_datetime_values(label, payload)
    _reject_public_non_json_values(label, payload)


def _require_payload_flags(label: str, payload: dict[str, Any]) -> None:
    for flag_name in ("paper_only", "report_only", "readonly"):
        if payload.get(flag_name) is not True:
            raise ValueError(f"{label}.{flag_name} must be True")


def _reject_unsafe_public_surfaces(label: str, payload: object) -> None:
    for path, value in _iter_public_payload_values(payload):
        if _has_unsafe_surface_fragment(path) or (
            type(value) is str and _has_unsafe_surface_fragment(value)
        ):
            raise ValueError(f"unsafe surface in {label}: {path}")


def _reject_public_numeric_primitives(label: str, payload: object) -> None:
    for path, value in _iter_public_payload_values(payload):
        if type(value) in (int, float):
            raise ValueError(
                f"public numeric values must be Decimal strings in {label}: {path}",
            )


def _reject_public_non_json_values(label: str, payload: object) -> None:
    for path, value in _iter_public_payload_values(payload):
        if (
            value is not None
            and type(value) not in (dict, list, str, bool, int, float)
        ):
            raise ValueError(f"public payload values must be JSON-safe in {label}: {path}")


def _reject_public_datetime_values(label: str, payload: object) -> None:
    for path, value in _iter_public_payload_values(payload):
        if isinstance(value, datetime):
            if type(value) is not datetime:
                raise ValueError(f"{path} must be a datetime")
            if value.tzinfo is None or value.utcoffset() is None:
                raise ValueError(f"{path} must be timezone-aware")


def _iter_public_payload_values(
    value: object,
    path: str = "payload",
) -> tuple[tuple[str, object], ...]:
    values: list[tuple[str, object]] = []
    if isinstance(value, dict):
        for key, item in value.items():
            key_text = str(key)
            item_path = f"{path}.{key_text}"
            values.append((item_path, item))
            values.extend(_iter_public_payload_values(item, item_path))
    elif isinstance(value, (list, tuple)):
        for index, item in enumerate(value):
            item_path = f"{path}[{index}]"
            values.append((item_path, item))
            values.extend(_iter_public_payload_values(item, item_path))
    return tuple(values)


def _has_unsafe_surface_fragment(value: str) -> bool:
    lowered = value.lower()
    return any(fragment in lowered for fragment in UNSAFE_SURFACE_FRAGMENTS)


def _as_utc(field_name: str, value: datetime) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _as_optional_utc(field_name: str, value: datetime | None) -> datetime | None:
    if value is None:
        return None
    return _as_utc(field_name, value)


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    try:
        return +value
    except InvalidOperation as exc:
        raise ValueError(f"{field_name} must be finite") from exc


def _require_positive_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _require_positive_count_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_positive_decimal(field_name, value)
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{field_name} must be an integer count")
    return normalized


def _require_nonnegative_count_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_nonnegative_decimal(field_name, value)
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{field_name} must be an integer count")
    return normalized


def _require_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _require_optional_nonnegative_decimal(
    field_name: str,
    value: object,
) -> Decimal | None:
    if value is None:
        return None
    return _require_nonnegative_decimal(field_name, value)


def _require_probability_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < ZERO or normalized > ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return _quantize(normalized)


def _require_optional_probability_decimal(
    field_name: str,
    value: object,
) -> Decimal | None:
    if value is None:
        return None
    return _require_probability_decimal(field_name, value)


def _decimal_count(value: int) -> Decimal:
    if type(value) is not int:
        raise ValueError("count source must be an int")
    if value < 0:
        raise ValueError("count source must be nonnegative")
    return Decimal(value)


def _quantize(value: Decimal) -> Decimal:
    return value.quantize(RATIO_QUANTUM)


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str or not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a nonempty canonical string")


def _require_optional_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if value and value.strip() != value:
        raise ValueError(f"{field_name} must be canonical when supplied")


def _normalize_string_tuple(
    field_name: str,
    values: object,
    *,
    allow_empty: bool,
) -> tuple[str, ...]:
    if type(values) is not tuple:
        raise ValueError(f"{field_name} must be a tuple")
    normalized: list[str] = []
    for value in values:
        _require_canonical_string(field_name, value)
        normalized.append(value)
    if not allow_empty and not normalized:
        raise ValueError(f"{field_name} must be nonempty")
    return tuple(normalized)


def _require_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in STATUSES:
        raise ValueError(f"{field_name} must be a known status")


def _require_hard_flags(label: str, value: object) -> None:
    for flag in ("paper_only", "report_only", "readonly"):
        flag_value = _field_value(value, flag)
        if type(flag_value) is not bool or flag_value is not True:
            raise ValueError(f"{label}.{flag} must be True")


def _require_sha256_hex(field_name: str, value: object) -> None:
    if (
        type(value) is not str
        or len(value) != 64
        or any(character not in "0123456789abcdef" for character in value)
    ):
        raise ValueError(f"{field_name} must be a sha256 hex digest")
