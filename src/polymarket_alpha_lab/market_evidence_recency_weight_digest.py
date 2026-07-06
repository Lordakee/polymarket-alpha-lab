"""Pure in-memory market evidence recency weighting digest.

This module reduces caller-supplied market research evidence into a
deterministic diagnostics report. It is report-only and paper-only with no
external side effects, account handling, execution path, or recommendation.
"""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable
from dataclasses import dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation
from hashlib import sha256
from json import dumps
from typing import Any


__all__ = (
    "MarketEvidenceRecencyWeightConfig",
    "MarketEvidenceRecencyWeightDigest",
    "MarketEvidenceRecencyWeightObservation",
    "MarketEvidenceRecencyWeightReasonCodeCount",
    "MarketEvidenceRecencyWeightRow",
    "build_market_evidence_recency_weight_digest",
    "market_evidence_recency_weight_digest_payload",
)


DEFAULT_CONFIG_VERSION = "market-evidence-recency-weight-digest-v0"
STATUSES = ("pass", "watch", "blocked")
ZERO = Decimal("0")
ONE = Decimal("1")
RATIO_QUANTUM = Decimal("0.000001")
REDACTED_REFERENCE = "[redacted_reference]"
DERIVED_VALIDATION_DIGEST_FIELD = "derived_validation_digest"
PHASE_FLAG_FIELDS = ("paper_only", "report_only", "readonly")
UNSAFE_TEXT_FRAGMENTS = tuple(
    "".join(parts)
    for parts in (
        ("li", "ve"),
        ("au", "th"),
        ("wal", "let"),
        ("bro", "ker"),
        ("or", "der"),
        ("can", "cel"),
        ("ex", "change"),
        ("mut", "ation"),
        ("sig", "ning"),
        ("tra", "de"),
        ("ad", "vice"),
        ("net", "work"),
        ("data", "base"),
        ("per", "sist"),
        ("creden", "tial"),
        ("api", "_key"),
        ("private", "_key"),
        ("ses", "sion"),
        ("sec", "ret"),
        ("to", "ken"),
    )
)


class _Missing:
    pass


_MISSING = _Missing()


@dataclass(frozen=True)
class MarketEvidenceRecencyWeightConfig:
    config_version: str = DEFAULT_CONFIG_VERSION
    fresh_age_seconds: Decimal = Decimal("3600")
    stale_age_seconds: Decimal = Decimal("86400")
    min_source_reliability_weight: Decimal = Decimal("0.250000")
    min_weighted_freshness_score: Decimal = Decimal("0.700000")
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
            "min_source_reliability_weight",
            _require_probability_decimal(
                "min_source_reliability_weight",
                self.min_source_reliability_weight,
            ),
        )
        object.__setattr__(
            self,
            "min_weighted_freshness_score",
            _require_probability_decimal(
                "min_weighted_freshness_score",
                self.min_weighted_freshness_score,
            ),
        )
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class MarketEvidenceRecencyWeightObservation:
    market_slug: str
    evidence_id: str
    source_id: str
    source_family: str
    source_reliability_weight: Decimal
    evidence_observed_at: datetime
    supports_outcome: str
    contradicts_current_summary: bool
    reference: str
    reason_codes: tuple[str, ...] = ()
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("market_slug", self.market_slug)
        for field_name in ("evidence_id", "source_id", "source_family"):
            _require_optional_public_string(field_name, getattr(self, field_name))
        for field_name in ("reference",):
            if type(getattr(self, field_name)) is not str:
                raise ValueError(f"{field_name} must be a string")
        object.__setattr__(self, "reference", _redact_reference(self.reference))
        for field_name in ("supports_outcome",):
            _require_canonical_string(field_name, getattr(self, field_name))
        object.__setattr__(
            self,
            "source_reliability_weight",
            _require_probability_decimal(
                "source_reliability_weight",
                self.source_reliability_weight,
            ),
        )
        object.__setattr__(
            self,
            "evidence_observed_at",
            _as_utc("evidence_observed_at", self.evidence_observed_at),
        )
        if type(self.contradicts_current_summary) is not bool:
            raise ValueError("contradicts_current_summary must be a bool")
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, allow_empty=True),
        )
        _require_hard_flags("observation", self)


@dataclass(frozen=True)
class MarketEvidenceRecencyWeightRow:
    market_slug: str
    evidence_count: Decimal
    source_count: Decimal
    latest_evidence_observed_at: datetime | None
    latest_evidence_age_seconds: Decimal | None
    latest_source_reliability_weight: Decimal | None
    average_source_reliability_weight: Decimal | None
    stale_evidence_count: Decimal
    contradiction_count: Decimal
    weighted_freshness_score: Decimal
    evidence_ids: tuple[str, ...]
    source_ids: tuple[str, ...]
    source_families: tuple[str, ...]
    supports_outcomes: tuple[str, ...]
    redacted_references: tuple[str, ...]
    status: str
    reason_codes: tuple[str, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("market_slug", self.market_slug)
        for field_name in (
            "evidence_count",
            "source_count",
            "stale_evidence_count",
            "contradiction_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "latest_evidence_observed_at",
            _as_optional_utc(
                "latest_evidence_observed_at",
                self.latest_evidence_observed_at,
            ),
        )
        object.__setattr__(
            self,
            "latest_evidence_age_seconds",
            _require_optional_nonnegative_decimal(
                "latest_evidence_age_seconds",
                self.latest_evidence_age_seconds,
            ),
        )
        for field_name in (
            "latest_source_reliability_weight",
            "average_source_reliability_weight",
            "weighted_freshness_score",
        ):
            value = getattr(self, field_name)
            normalized = (
                _require_probability_decimal(field_name, value)
                if value is not None
                else None
            )
            object.__setattr__(self, field_name, normalized)
        for field_name in (
            "evidence_ids",
            "source_ids",
            "source_families",
            "supports_outcomes",
            "redacted_references",
            "reason_codes",
        ):
            object.__setattr__(
                self,
                field_name,
                (
                    _normalize_reason_codes(
                        field_name,
                        getattr(self, field_name),
                        allow_empty=True,
                    )
                    if field_name == "reason_codes"
                    else _normalize_redacted_references(
                        field_name,
                        getattr(self, field_name),
                    )
                    if field_name == "redacted_references"
                    else _normalize_string_tuple(
                        field_name,
                        getattr(self, field_name),
                        allow_empty=True,
                    )
                ),
            )
        _require_status("status", self.status)
        _require_hard_flags("row", self)
        _validate_row_consistency(self)
        object.__setattr__(
            self,
            DERIVED_VALIDATION_DIGEST_FIELD,
            _validate_derived_validation_digest(
                "row",
                self,
                self.derived_validation_digest,
            ),
        )


@dataclass(frozen=True)
class MarketEvidenceRecencyWeightReasonCodeCount:
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
            _require_positive_decimal("count", self.count),
        )
        _require_hard_flags("reason_code_count", self)


@dataclass(frozen=True)
class MarketEvidenceRecencyWeightDigest:
    generated_at: datetime
    config_version: str
    market_count: Decimal
    evidence_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    blocked_count: Decimal
    stale_evidence_count: Decimal
    contradiction_count: Decimal
    average_weighted_freshness_score: Decimal | None
    status: str
    rows: tuple[MarketEvidenceRecencyWeightRow, ...]
    reason_code_counts: tuple[MarketEvidenceRecencyWeightReasonCodeCount, ...]
    reason_codes: tuple[str, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        for field_name in (
            "market_count",
            "evidence_count",
            "pass_count",
            "watch_count",
            "blocked_count",
            "stale_evidence_count",
            "contradiction_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "average_weighted_freshness_score",
            _require_optional_probability_decimal(
                "average_weighted_freshness_score",
                self.average_weighted_freshness_score,
            ),
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
            _normalize_reason_codes("reason_codes", self.reason_codes, allow_empty=False),
        )
        _require_hard_flags("report", self)
        _validate_digest_consistency(self)
        object.__setattr__(
            self,
            DERIVED_VALIDATION_DIGEST_FIELD,
            _validate_derived_validation_digest(
                "report",
                self,
                self.derived_validation_digest,
            ),
        )


def build_market_evidence_recency_weight_digest(
    observations: Iterable[object],
    *,
    config: MarketEvidenceRecencyWeightConfig,
    generated_at: datetime,
) -> MarketEvidenceRecencyWeightDigest:
    if type(config) is not MarketEvidenceRecencyWeightConfig:
        raise ValueError("config must be a MarketEvidenceRecencyWeightConfig")
    _require_hard_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    evidence_items = _normalize_observations(observations)
    for item in evidence_items:
        _reject_future_observed_at(item, generated_at_utc)

    grouped: dict[str, list[MarketEvidenceRecencyWeightObservation]] = {}
    for item in evidence_items:
        grouped.setdefault(item.market_slug, []).append(item)

    rows = tuple(
        _row_from_market(
            market_slug=market_slug,
            observations=tuple(grouped[market_slug]),
            config=config,
            generated_at=generated_at_utc,
        )
        for market_slug in sorted(grouped)
    )
    reason_codes = _summary_reason_codes(rows)

    return MarketEvidenceRecencyWeightDigest(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        market_count=_decimal_count(len(rows)),
        evidence_count=sum((row.evidence_count for row in rows), ZERO),
        pass_count=_decimal_count(_status_count(rows, "pass")),
        watch_count=_decimal_count(_status_count(rows, "watch")),
        blocked_count=_decimal_count(_status_count(rows, "blocked")),
        stale_evidence_count=sum((row.stale_evidence_count for row in rows), ZERO),
        contradiction_count=sum((row.contradiction_count for row in rows), ZERO),
        average_weighted_freshness_score=_average_score(rows),
        status=_summary_status(reason_codes),
        rows=rows,
        reason_code_counts=_reason_code_counts(rows, reason_codes),
        reason_codes=reason_codes,
    )


def market_evidence_recency_weight_digest_payload(
    report: MarketEvidenceRecencyWeightDigest | dict[str, Any],
) -> dict[str, Any]:
    if type(report) is MarketEvidenceRecencyWeightDigest:
        _require_hard_flags("report", report)
        payload = _payload_value(report)
    elif type(report) is dict:
        payload = report
    else:
        raise ValueError("report must be a MarketEvidenceRecencyWeightDigest")
    if not isinstance(payload, dict):
        raise ValueError("report payload must be a JSON object")
    _reject_unsafe_public_payload("payload", payload)
    _require_public_derived_validation_digest("payload", payload)
    return payload


def _row_from_market(
    *,
    market_slug: str,
    observations: tuple[MarketEvidenceRecencyWeightObservation, ...],
    config: MarketEvidenceRecencyWeightConfig,
    generated_at: datetime,
) -> MarketEvidenceRecencyWeightRow:
    present = tuple(
        sorted(
            (item for item in observations if _has_evidence_payload(item)),
            key=lambda item: (item.evidence_id, item.source_id),
        ),
    )
    if not present:
        return MarketEvidenceRecencyWeightRow(
            market_slug=market_slug,
            evidence_count=ZERO,
            source_count=ZERO,
            latest_evidence_observed_at=None,
            latest_evidence_age_seconds=None,
            latest_source_reliability_weight=None,
            average_source_reliability_weight=None,
            stale_evidence_count=ZERO,
            contradiction_count=ZERO,
            weighted_freshness_score=ZERO,
            evidence_ids=(),
            source_ids=(),
            source_families=(),
            supports_outcomes=(),
            redacted_references=(),
            status="blocked",
            reason_codes=("missing_market_evidence",),
        )

    scored = tuple(
        (
            item,
            _age_seconds(generated_at, item.evidence_observed_at),
            _freshness_multiplier(
                _age_seconds(generated_at, item.evidence_observed_at),
                config=config,
            ),
        )
        for item in present
    )
    latest_item, latest_age, latest_multiplier = min(scored, key=lambda value: value[1])
    stale_count = sum(1 for _, age, _ in scored if age > config.stale_age_seconds)
    contradiction_count = sum(1 for item, _, _ in scored if item.contradicts_current_summary)
    average_reliability = _quantize(
        sum((item.source_reliability_weight for item, _, _ in scored), ZERO)
        / Decimal(len(scored)),
    )
    weighted_freshness_score = _quantize(
        latest_item.source_reliability_weight
        * _age_weight(
            latest_age,
            fresh_age_seconds=config.fresh_age_seconds,
            stale_age_seconds=config.stale_age_seconds,
        )
        * (ONE if stale_count == 0 else Decimal("0.700000")),
    )
    reason_codes = _row_reason_codes(
        weighted_freshness_score=weighted_freshness_score,
        lowest_reliability=min(item.source_reliability_weight for item, _, _ in scored),
        stale_count=stale_count,
        contradiction_count=contradiction_count,
        input_reason_codes=tuple(
            reason_code for item, _, _ in scored for reason_code in item.reason_codes
        ),
        config=config,
    )

    return MarketEvidenceRecencyWeightRow(
        market_slug=market_slug,
        evidence_count=_decimal_count(len(scored)),
        source_count=_decimal_count(len({item.source_id for item, _, _ in scored})),
        latest_evidence_observed_at=latest_item.evidence_observed_at,
        latest_evidence_age_seconds=latest_age,
        latest_source_reliability_weight=latest_item.source_reliability_weight,
        average_source_reliability_weight=average_reliability,
        stale_evidence_count=_decimal_count(stale_count),
        contradiction_count=_decimal_count(contradiction_count),
        weighted_freshness_score=weighted_freshness_score,
        evidence_ids=tuple(item.evidence_id for item, _, _ in scored),
        source_ids=tuple(sorted({item.source_id for item, _, _ in scored})),
        source_families=tuple(sorted({item.source_family for item, _, _ in scored})),
        supports_outcomes=tuple(sorted({item.supports_outcome for item, _, _ in scored})),
        redacted_references=tuple(
            sorted({_redact_reference(item.reference) for item, _, _ in scored})
        ),
        status=_row_status(reason_codes),
        reason_codes=reason_codes,
    )


def _normalize_observations(
    observations: Iterable[object],
) -> tuple[MarketEvidenceRecencyWeightObservation, ...]:
    if isinstance(observations, (str, bytes)):
        raise ValueError("observations must be an iterable")
    try:
        values = tuple(observations)
    except TypeError as exc:
        raise ValueError("observations must be an iterable") from exc
    return tuple(_coerce_observation(value) for value in values)


def _coerce_observation(value: object) -> MarketEvidenceRecencyWeightObservation:
    if type(value) is MarketEvidenceRecencyWeightObservation:
        _require_hard_flags("observation", value)
        return value
    _require_hard_flags("observation", value)
    return MarketEvidenceRecencyWeightObservation(
        market_slug=_field_value(value, "market_slug"),
        evidence_id=_field_value(value, "evidence_id"),
        source_id=_field_value(value, "source_id"),
        source_family=_field_value(value, "source_family"),
        source_reliability_weight=_field_value(value, "source_reliability_weight"),
        evidence_observed_at=_field_value(value, "evidence_observed_at"),
        supports_outcome=_field_value(value, "supports_outcome"),
        contradicts_current_summary=_field_value(value, "contradicts_current_summary"),
        reference=_field_value(value, "reference"),
        reason_codes=_field_value(value, "reason_codes", default=()),
        paper_only=_field_value(value, "paper_only"),
        report_only=_field_value(value, "report_only"),
        readonly=_field_value(value, "readonly"),
    )


def _has_evidence_payload(item: MarketEvidenceRecencyWeightObservation) -> bool:
    return bool(item.evidence_id and item.source_id and item.source_family)


def _validate_derived_validation_digest(
    label: str,
    value: object,
    supplied_digest: object,
) -> str:
    expected_digest = _derived_validation_digest(value)
    if supplied_digest == "":
        return expected_digest
    _require_sha256_digest(DERIVED_VALIDATION_DIGEST_FIELD, supplied_digest)
    if supplied_digest != expected_digest:
        raise ValueError(f"{DERIVED_VALIDATION_DIGEST_FIELD} must match {label} fields")
    return supplied_digest


def _derived_validation_digest(value: object) -> str:
    digest_payload = _digest_ready(value)
    encoded = dumps(
        digest_payload,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return sha256(encoded).hexdigest()


def _digest_ready(value: object) -> object:
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, datetime):
        return value.isoformat()
    if is_dataclass(value) and not isinstance(value, type):
        return {
            field.name: _digest_ready(getattr(value, field.name))
            for field in fields(value)
            if field.name != DERIVED_VALIDATION_DIGEST_FIELD
        }
    if isinstance(value, tuple):
        return [_digest_ready(item) for item in value]
    if isinstance(value, list):
        return [_digest_ready(item) for item in value]
    if isinstance(value, dict):
        return {
            key: _digest_ready(item)
            for key, item in value.items()
            if key != DERIVED_VALIDATION_DIGEST_FIELD
        }
    return value


def _row_reason_codes(
    *,
    weighted_freshness_score: Decimal,
    lowest_reliability: Decimal,
    stale_count: int,
    contradiction_count: int,
    input_reason_codes: tuple[str, ...],
    config: MarketEvidenceRecencyWeightConfig,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    reason_codes.append(
        "evidence_recency_weight_pass"
        if weighted_freshness_score >= config.min_weighted_freshness_score
        else "evidence_recency_weight_watch",
    )
    reason_codes.append("evidence_stale" if stale_count else "evidence_recent")
    reason_codes.append(
        "low_source_reliability"
        if lowest_reliability <= config.min_source_reliability_weight
        else "reliable_sources",
    )
    reason_codes.append(
        "contradiction_present" if contradiction_count else "no_contradictions",
    )
    for reason_code in input_reason_codes:
        reason_codes.append(f"input_{reason_code}")
    return tuple(sorted(set(reason_codes)))


def _row_status(reason_codes: tuple[str, ...]) -> str:
    if "missing_market_evidence" in reason_codes:
        return "blocked"
    if "evidence_recency_weight_watch" in reason_codes:
        return "watch"
    if "evidence_stale" in reason_codes:
        return "watch"
    if "low_source_reliability" in reason_codes:
        return "watch"
    if "contradiction_present" in reason_codes:
        return "watch"
    return "pass"


def _summary_reason_codes(
    rows: tuple[MarketEvidenceRecencyWeightRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return ("no_market_evidence",)
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
        return ("evidence_recency_weight_pass",)
    return tuple(
        sorted(
            {
                reason_code
                for row in rows
                for reason_code in row.reason_codes
                if reason_code != "evidence_recent"
            },
        ),
    )


def _summary_status(reason_codes: tuple[str, ...]) -> str:
    if reason_codes in (("no_market_evidence",), ("missing_market_evidence",)):
        return "blocked"
    if "missing_market_evidence" in reason_codes:
        return "blocked"
    if "evidence_recency_weight_watch" in reason_codes:
        return "watch"
    if "evidence_stale" in reason_codes:
        return "watch"
    if "low_source_reliability" in reason_codes:
        return "watch"
    if "contradiction_present" in reason_codes:
        return "watch"
    return "pass"


def _reason_code_counts(
    rows: tuple[MarketEvidenceRecencyWeightRow, ...],
    reason_codes: tuple[str, ...],
) -> tuple[MarketEvidenceRecencyWeightReasonCodeCount, ...]:
    if not rows:
        return (
            MarketEvidenceRecencyWeightReasonCodeCount(
                reason_code=reason_codes[0],
                count=ONE,
            ),
        )
    counts: Counter[str] = Counter()
    for row in rows:
        counts.update(row.reason_codes)
    return tuple(
        MarketEvidenceRecencyWeightReasonCodeCount(
            reason_code=reason_code,
            count=_decimal_count(count),
        )
        for reason_code, count in sorted(counts.items(), key=lambda item: item[0])
    )


def _average_score(
    rows: tuple[MarketEvidenceRecencyWeightRow, ...],
) -> Decimal | None:
    scored_rows = tuple(row for row in rows if row.evidence_count > ZERO)
    if not scored_rows:
        return None
    return _quantize(
        sum((row.weighted_freshness_score for row in scored_rows), ZERO)
        / Decimal(len(scored_rows)),
    )


def _freshness_multiplier(
    age_seconds: Decimal,
    *,
    config: MarketEvidenceRecencyWeightConfig,
) -> Decimal:
    if age_seconds <= config.fresh_age_seconds:
        return ONE
    if age_seconds >= config.stale_age_seconds:
        return ZERO
    age_span = config.stale_age_seconds - config.fresh_age_seconds
    remaining = config.stale_age_seconds - age_seconds
    return _quantize(remaining / age_span)


def _age_weight(
    age_seconds: Decimal,
    *,
    fresh_age_seconds: Decimal,
    stale_age_seconds: Decimal,
) -> Decimal:
    if age_seconds <= fresh_age_seconds:
        return ONE
    if age_seconds >= stale_age_seconds:
        return ZERO
    return _quantize(ONE - (age_seconds / stale_age_seconds))


def _age_seconds(generated_at: datetime, observed_at: datetime) -> Decimal:
    delta = generated_at - observed_at
    return (
        Decimal(delta.days * 86_400)
        + Decimal(delta.seconds)
        + (Decimal(delta.microseconds) / Decimal("1000000"))
    )


def _reject_future_observed_at(
    item: MarketEvidenceRecencyWeightObservation,
    generated_at: datetime,
) -> None:
    if item.evidence_observed_at > generated_at:
        raise ValueError("evidence_observed_at must not be after generated_at")


def _status_count(rows: tuple[MarketEvidenceRecencyWeightRow, ...], status: str) -> int:
    return sum(1 for row in rows if row.status == status)


def _normalize_rows(
    rows: tuple[MarketEvidenceRecencyWeightRow, ...],
) -> tuple[MarketEvidenceRecencyWeightRow, ...]:
    if type(rows) is not tuple:
        raise ValueError("rows must be a tuple")
    for row in rows:
        if type(row) is not MarketEvidenceRecencyWeightRow:
            raise ValueError("rows must contain MarketEvidenceRecencyWeightRow values")
        _require_hard_flags("row", row)
    sorted_rows = tuple(sorted(rows, key=lambda row: row.market_slug))
    if rows != sorted_rows:
        raise ValueError("rows must be sorted by market_slug")
    return rows


def _normalize_reason_code_counts(
    rows: tuple[MarketEvidenceRecencyWeightReasonCodeCount, ...],
) -> tuple[MarketEvidenceRecencyWeightReasonCodeCount, ...]:
    if type(rows) is not tuple:
        raise ValueError("reason_code_counts must be a tuple")
    for row in rows:
        if type(row) is not MarketEvidenceRecencyWeightReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "MarketEvidenceRecencyWeightReasonCodeCount values",
            )
        _require_hard_flags("reason_code_count", row)
    sorted_rows = tuple(sorted(rows, key=lambda row: row.reason_code))
    if rows != sorted_rows:
        raise ValueError("reason_code_counts must be sorted by reason_code")
    return rows


def _validate_row_consistency(row: MarketEvidenceRecencyWeightRow) -> None:
    if row.evidence_count == ZERO:
        if row.status != "blocked":
            raise ValueError("status must be blocked when evidence_count is zero")
        if row.reason_codes != ("missing_market_evidence",):
            raise ValueError("reason_codes must identify missing market evidence")
        if row.latest_evidence_observed_at is not None:
            raise ValueError("latest_evidence_observed_at must be absent without evidence")
        if row.latest_evidence_age_seconds is not None:
            raise ValueError("latest_evidence_age_seconds must be absent without evidence")
        return
    if row.source_count > row.evidence_count:
        raise ValueError("source_count must not exceed evidence_count")
    if row.stale_evidence_count > row.evidence_count:
        raise ValueError("stale_evidence_count must not exceed evidence_count")
    if row.contradiction_count > row.evidence_count:
        raise ValueError("contradiction_count must not exceed evidence_count")
    if row.latest_evidence_observed_at is None:
        raise ValueError("latest_evidence_observed_at is required with evidence")
    if row.latest_evidence_age_seconds is None:
        raise ValueError("latest_evidence_age_seconds is required with evidence")
    if row.latest_source_reliability_weight is None:
        raise ValueError("latest_source_reliability_weight is required with evidence")
    if row.average_source_reliability_weight is None:
        raise ValueError("average_source_reliability_weight is required with evidence")
    if row.evidence_count != _decimal_count(len(row.evidence_ids)):
        raise ValueError("evidence_ids must match evidence_count")
    if row.source_count != _decimal_count(len(row.source_ids)):
        raise ValueError("source_ids must match source_count")


def _validate_digest_consistency(report: MarketEvidenceRecencyWeightDigest) -> None:
    if report.market_count != _decimal_count(len(report.rows)):
        raise ValueError("market_count must match rows")
    if report.evidence_count != sum((row.evidence_count for row in report.rows), ZERO):
        raise ValueError("evidence_count must match rows")
    if report.pass_count != _decimal_count(_status_count(report.rows, "pass")):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _decimal_count(_status_count(report.rows, "watch")):
        raise ValueError("watch_count must match rows")
    if report.blocked_count != _decimal_count(_status_count(report.rows, "blocked")):
        raise ValueError("blocked_count must match rows")
    if report.stale_evidence_count != sum(
        (row.stale_evidence_count for row in report.rows),
        ZERO,
    ):
        raise ValueError("stale_evidence_count must match rows")
    if report.contradiction_count != sum(
        (row.contradiction_count for row in report.rows),
        ZERO,
    ):
        raise ValueError("contradiction_count must match rows")
    if report.average_weighted_freshness_score != _average_score(report.rows):
        raise ValueError("average_weighted_freshness_score must match rows")
    if report.status != _summary_status(report.reason_codes):
        raise ValueError("status must match reason_codes")
    if report.reason_codes != _summary_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")


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
        if type(value) is not Decimal:
            raise ValueError("value must be a Decimal")
        if not value.is_finite():
            raise ValueError("value must be finite")
        return str(value)
    if isinstance(value, datetime):
        if type(value) is not datetime:
            raise ValueError("value must be a datetime")
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("value must be timezone-aware")
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
    if type(value) in (float, int):
        raise ValueError("value must use Decimal-string serialization")
    return value


def _reject_unsafe_public_payload(label: str, value: object, path: str = "") -> None:
    location = path or label
    if type(value) is dict:
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError(f"{location} keys must be strings")
            if _contains_unsafe_text(key):
                raise ValueError(f"{location} has unsafe key")
            item_path = key if not path else f"{path}.{key}"
            if key in PHASE_FLAG_FIELDS and item is not True:
                raise ValueError(f"{item_path} must be True")
            _reject_unsafe_public_payload(label, item, item_path)
        return
    if type(value) is list:
        for index, item in enumerate(value):
            item_path = f"{path}[{index}]" if path else f"{label}[{index}]"
            _reject_unsafe_public_payload(label, item, item_path)
        return
    if type(value) in (Decimal, float, int):
        raise ValueError(f"{location} must use Decimal-string serialization")
    if type(value) is str and _contains_unsafe_text(value):
        raise ValueError(f"{location} has unsafe value")


def _require_public_derived_validation_digest(label: str, payload: dict[str, Any]) -> None:
    supplied_digest = payload.get(DERIVED_VALIDATION_DIGEST_FIELD)
    _require_sha256_digest(DERIVED_VALIDATION_DIGEST_FIELD, supplied_digest)
    if supplied_digest != _derived_validation_digest(payload):
        raise ValueError(f"{DERIVED_VALIDATION_DIGEST_FIELD} must match public payload")

    rows = payload.get("rows", [])
    if type(rows) is not list:
        raise ValueError("rows must be a list")
    for index, row in enumerate(rows):
        if type(row) is not dict:
            raise ValueError("rows must contain objects")
        row_label = f"{label}.rows[{index}]"
        row_digest = row.get(DERIVED_VALIDATION_DIGEST_FIELD)
        _require_sha256_digest(DERIVED_VALIDATION_DIGEST_FIELD, row_digest)
        if row_digest != _derived_validation_digest(row):
            raise ValueError(f"{DERIVED_VALIDATION_DIGEST_FIELD} must match {row_label}")


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
    if _contains_unsafe_text(value):
        raise ValueError(f"{field_name} must not contain unsafe text")


def _contains_unsafe_text(value: str) -> bool:
    lowered = value.lower()
    return any(fragment in lowered for fragment in UNSAFE_TEXT_FRAGMENTS)


def _require_optional_public_string(field_name: str, value: object) -> None:
    if type(value) is not str or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical string")
    if value and _contains_unsafe_text(value):
        raise ValueError(f"{field_name} must not contain unsafe text")


def _require_reference_string(field_name: str, value: object) -> None:
    if type(value) is not str or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical string")


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


def _normalize_reason_codes(
    field_name: str,
    values: object,
    *,
    allow_empty: bool,
) -> tuple[str, ...]:
    if type(values) is not tuple:
        raise ValueError(f"{field_name} must be a tuple")
    normalized: list[str] = []
    for value in values:
        _require_reason_code(field_name, value)
        normalized.append(value)
    if not allow_empty and not normalized:
        raise ValueError(f"{field_name} must be nonempty")
    return tuple(sorted(set(normalized)))


def _normalize_redacted_references(
    field_name: str,
    values: object,
) -> tuple[str, ...]:
    if type(values) is not tuple:
        raise ValueError(f"{field_name} must be a tuple")
    return tuple(
        sorted(
            {
                _redact_reference(value)
                for value in values
                if _require_reference_string(field_name, value) is None
            },
        ),
    )


def _require_reason_code(field_name: str, value: object) -> None:
    _require_canonical_string(field_name, value)
    allowed = "abcdefghijklmnopqrstuvwxyz0123456789_"
    if any(character not in allowed for character in value):
        raise ValueError(f"{field_name} must contain deterministic code text")


def _require_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in STATUSES:
        raise ValueError(f"{field_name} must be a known status")


def _require_hard_flags(label: str, value: object) -> None:
    for flag in PHASE_FLAG_FIELDS:
        flag_value = _field_value(value, flag)
        if type(flag_value) is not bool or flag_value is not True:
            raise ValueError(f"{label}.{flag} must be True")


def _require_sha256_digest(field_name: str, value: object) -> None:
    _require_canonical_string(field_name, value)
    if len(value) != 64 or any(character not in "0123456789abcdef" for character in value):
        raise ValueError(f"{field_name} must be a sha256 hex digest")
