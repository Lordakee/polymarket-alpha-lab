"""Pure in-memory outcome-evidence quality digest reducer."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal, ROUND_HALF_EVEN
from typing import Any


__all__ = (
    "MarketOutcomeEvidenceObservation",
    "MarketOutcomeEvidenceQualityConfig",
    "MarketOutcomeEvidenceQualityReasonCodeCount",
    "MarketOutcomeEvidenceQualityRow",
    "MarketOutcomeEvidenceQualityCategoryRollup",
    "MarketOutcomeEvidenceQualityDigest",
    "build_market_outcome_evidence_quality_digest",
    "market_outcome_evidence_quality_digest_to_json_payload",
    "validate_market_outcome_evidence_quality_digest_public_payload",
)


RATIO_QUANTUM = Decimal("0.000001")
ZERO = Decimal("0")
ONE = Decimal("1")

QUALITY_STATUSES = (
    "high_quality",
    "missing_authoritative_source",
    "source_disagreement",
    "stale_evidence",
    "stale_acknowledgement",
    "unresolved_ambiguity",
)

SENSITIVE_TEXT_FRAGMENTS = (
    "bearer ",
    "password=",
    "token=",
)

UNSAFE_PUBLIC_SURFACE_FRAGMENTS = (
    "api" + "_" + "key",
    "authorization",
    "bro" + "ker",
    "credential",
    "data" + "base",
    "dsn",
    "financial" + "_" + "advice",
    "live" + "_" + "trading",
    "live " + "trading",
    "net" + "work",
    "ord" + "er",
    "per" + "sist",
    "private" + "_" + "key",
    "secret" + "_" + "key",
    "sign" + "_" + "transaction",
    "wal" + "let",
)


@dataclass(frozen=True)
class MarketOutcomeEvidenceQualityConfig:
    config_version: str
    max_evidence_age_seconds: Decimal
    max_acknowledgement_age_seconds: Decimal
    authoritative_source_kinds: tuple[str, ...]
    min_source_agreement_ratio: Decimal
    max_unresolved_ambiguity_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "MarketOutcomeEvidenceQualityConfig does not support subclassing",
        )

    def __post_init__(self) -> None:
        _require_canonical_string("config_version", self.config_version)
        _require_nonnegative_decimal(
            "max_evidence_age_seconds",
            self.max_evidence_age_seconds,
        )
        _require_nonnegative_decimal(
            "max_acknowledgement_age_seconds",
            self.max_acknowledgement_age_seconds,
        )
        object.__setattr__(
            self,
            "authoritative_source_kinds",
            _normalize_string_tuple(
                "authoritative_source_kinds",
                self.authoritative_source_kinds,
            ),
        )
        if not self.authoritative_source_kinds:
            raise ValueError("authoritative_source_kinds must be nonempty")
        _require_probability_decimal(
            "min_source_agreement_ratio",
            self.min_source_agreement_ratio,
        )
        _require_probability_decimal(
            "max_unresolved_ambiguity_ratio",
            self.max_unresolved_ambiguity_ratio,
        )
        _require_hard_flags(self)


@dataclass(frozen=True)
class MarketOutcomeEvidenceObservation:
    market_slug: str
    category_id: str
    evidence_id: str
    source_id: str
    source_kind: str
    observed_outcome: str
    evidence_observed_at: datetime
    acknowledged_at: datetime | None
    unresolved_ambiguity: bool
    reason_codes: tuple[str, ...] = ()
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "MarketOutcomeEvidenceObservation does not support subclassing",
        )

    def __post_init__(self) -> None:
        for field_name in (
            "market_slug",
            "category_id",
            "evidence_id",
            "source_id",
            "source_kind",
            "observed_outcome",
        ):
            _require_canonical_string(field_name, getattr(self, field_name))
        object.__setattr__(
            self,
            "evidence_observed_at",
            _as_utc("evidence_observed_at", self.evidence_observed_at),
        )
        object.__setattr__(
            self,
            "acknowledged_at",
            _as_optional_utc("acknowledged_at", self.acknowledged_at),
        )
        if type(self.unresolved_ambiguity) is not bool:
            raise ValueError("unresolved_ambiguity must be a bool")
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_string_tuple("reason_codes", self.reason_codes),
        )
        _require_hard_flags(self)


@dataclass(frozen=True)
class MarketOutcomeEvidenceQualityReasonCodeCount:
    reason_code: str
    market_count: Decimal
    market_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "MarketOutcomeEvidenceQualityReasonCodeCount does not support subclassing",
        )

    def __post_init__(self) -> None:
        _require_canonical_string("reason_code", self.reason_code)
        _require_nonnegative_decimal("market_count", self.market_count)
        _require_probability_decimal("market_ratio", self.market_ratio)
        _require_hard_flags(self)


@dataclass(frozen=True)
class MarketOutcomeEvidenceQualityRow:
    market_slug: str
    category_id: str
    evidence_count: Decimal
    source_count: Decimal
    authoritative_source_count: Decimal
    authoritative_source_present: bool
    unique_outcome_count: Decimal
    source_agreement_ratio: Decimal
    source_agreement_present: bool
    latest_evidence_observed_at: datetime
    latest_evidence_age_seconds: Decimal
    evidence_fresh: bool
    latest_acknowledged_at: datetime | None
    latest_acknowledgement_age_seconds: Decimal | None
    acknowledgement_fresh: bool
    unresolved_ambiguity_count: Decimal
    unresolved_ambiguity_ratio: Decimal
    quality_status: str
    evidence_ids: tuple[str, ...]
    source_ids: tuple[str, ...]
    observed_outcomes: tuple[str, ...]
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "MarketOutcomeEvidenceQualityRow does not support subclassing",
        )

    def __post_init__(self) -> None:
        _require_canonical_string("market_slug", self.market_slug)
        _require_canonical_string("category_id", self.category_id)
        for field_name in (
            "evidence_count",
            "source_count",
            "authoritative_source_count",
            "unique_outcome_count",
            "latest_evidence_age_seconds",
            "unresolved_ambiguity_count",
        ):
            _require_nonnegative_decimal(field_name, getattr(self, field_name))
        _require_probability_decimal(
            "source_agreement_ratio",
            self.source_agreement_ratio,
        )
        _require_probability_decimal(
            "unresolved_ambiguity_ratio",
            self.unresolved_ambiguity_ratio,
        )
        object.__setattr__(
            self,
            "latest_evidence_observed_at",
            _as_utc("latest_evidence_observed_at", self.latest_evidence_observed_at),
        )
        object.__setattr__(
            self,
            "latest_acknowledged_at",
            _as_optional_utc("latest_acknowledged_at", self.latest_acknowledged_at),
        )
        if self.latest_acknowledgement_age_seconds is not None:
            _require_nonnegative_decimal(
                "latest_acknowledgement_age_seconds",
                self.latest_acknowledgement_age_seconds,
            )
        for field_name in (
            "authoritative_source_present",
            "source_agreement_present",
            "evidence_fresh",
            "acknowledgement_fresh",
        ):
            if type(getattr(self, field_name)) is not bool:
                raise ValueError(f"{field_name} must be a bool")
        if self.quality_status not in QUALITY_STATUSES:
            raise ValueError("quality_status must be a known quality status")
        object.__setattr__(
            self,
            "evidence_ids",
            _normalize_string_tuple("evidence_ids", self.evidence_ids),
        )
        object.__setattr__(
            self,
            "source_ids",
            _normalize_string_tuple("source_ids", self.source_ids),
        )
        object.__setattr__(
            self,
            "observed_outcomes",
            _normalize_string_tuple("observed_outcomes", self.observed_outcomes),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_string_tuple("reason_codes", self.reason_codes),
        )
        _validate_row_consistency(self)
        _require_hard_flags(self)


@dataclass(frozen=True)
class MarketOutcomeEvidenceQualityCategoryRollup:
    category_id: str
    market_count: Decimal
    evidence_count: Decimal
    high_quality_market_count: Decimal
    high_quality_market_ratio: Decimal
    missing_authoritative_source_market_count: Decimal
    source_disagreement_market_count: Decimal
    stale_evidence_market_count: Decimal
    stale_acknowledgement_market_count: Decimal
    unresolved_ambiguity_market_count: Decimal
    reason_code_counts: tuple[MarketOutcomeEvidenceQualityReasonCodeCount, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "MarketOutcomeEvidenceQualityCategoryRollup does not support subclassing",
        )

    def __post_init__(self) -> None:
        _require_canonical_string("category_id", self.category_id)
        for field_name in (
            "market_count",
            "evidence_count",
            "high_quality_market_count",
            "missing_authoritative_source_market_count",
            "source_disagreement_market_count",
            "stale_evidence_market_count",
            "stale_acknowledgement_market_count",
            "unresolved_ambiguity_market_count",
        ):
            _require_nonnegative_decimal(field_name, getattr(self, field_name))
        _require_probability_decimal(
            "high_quality_market_ratio",
            self.high_quality_market_ratio,
        )
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        _require_hard_flags(self)


@dataclass(frozen=True)
class MarketOutcomeEvidenceQualityDigest:
    generated_at: datetime
    config_version: str
    market_count: Decimal
    category_count: Decimal
    evidence_count: Decimal
    high_quality_market_count: Decimal
    missing_authoritative_source_market_count: Decimal
    source_disagreement_market_count: Decimal
    stale_evidence_market_count: Decimal
    stale_acknowledgement_market_count: Decimal
    unresolved_ambiguity_market_count: Decimal
    rows: tuple[MarketOutcomeEvidenceQualityRow, ...]
    category_rollups: tuple[MarketOutcomeEvidenceQualityCategoryRollup, ...]
    reason_code_counts: tuple[MarketOutcomeEvidenceQualityReasonCodeCount, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "MarketOutcomeEvidenceQualityDigest does not support subclassing",
        )

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "generated_at",
            _as_utc("generated_at", self.generated_at),
        )
        _require_canonical_string("config_version", self.config_version)
        for field_name in (
            "market_count",
            "category_count",
            "evidence_count",
            "high_quality_market_count",
            "missing_authoritative_source_market_count",
            "source_disagreement_market_count",
            "stale_evidence_market_count",
            "stale_acknowledgement_market_count",
            "unresolved_ambiguity_market_count",
        ):
            _require_nonnegative_decimal(field_name, getattr(self, field_name))
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
        _require_hard_flags(self)
        if self.derived_validation_digest == "":
            object.__setattr__(
                self,
                "derived_validation_digest",
                _report_derived_validation_digest(self),
            )
        else:
            object.__setattr__(
                self,
                "derived_validation_digest",
                _require_sha256_digest(
                    "derived_validation_digest",
                    self.derived_validation_digest,
                ),
            )
        _validate_digest_consistency(self)


def build_market_outcome_evidence_quality_digest(
    evidence: (
        list[MarketOutcomeEvidenceObservation]
        | tuple[MarketOutcomeEvidenceObservation, ...]
    ),
    *,
    config: MarketOutcomeEvidenceQualityConfig,
    generated_at: datetime,
) -> MarketOutcomeEvidenceQualityDigest:
    if type(config) is not MarketOutcomeEvidenceQualityConfig:
        raise ValueError("config must be a MarketOutcomeEvidenceQualityConfig")
    generated_at_utc = _as_utc("generated_at", generated_at)
    evidence_items = _normalize_evidence(evidence)

    grouped: dict[tuple[str, str], list[MarketOutcomeEvidenceObservation]] = {}
    for item in evidence_items:
        grouped.setdefault((item.category_id, item.market_slug), []).append(item)

    rows = tuple(
        _build_market_row(
            category_id=category_id,
            market_slug=market_slug,
            evidence=tuple(items),
            config=config,
            generated_at_utc=generated_at_utc,
        )
        for (category_id, market_slug), items in sorted(grouped.items())
    )
    category_rollups = _build_category_rollups(rows)

    return MarketOutcomeEvidenceQualityDigest(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        market_count=_decimal_count(len(rows)),
        category_count=_decimal_count(len(category_rollups)),
        evidence_count=_decimal_count(len(evidence_items)),
        high_quality_market_count=_status_count(rows, "high_quality"),
        missing_authoritative_source_market_count=_status_count(
            rows,
            "missing_authoritative_source",
        ),
        source_disagreement_market_count=_status_count(rows, "source_disagreement"),
        stale_evidence_market_count=_status_count(rows, "stale_evidence"),
        stale_acknowledgement_market_count=_status_count(
            rows,
            "stale_acknowledgement",
        ),
        unresolved_ambiguity_market_count=_status_count(rows, "unresolved_ambiguity"),
        rows=rows,
        category_rollups=category_rollups,
        reason_code_counts=_build_reason_code_counts(rows),
    )


def market_outcome_evidence_quality_digest_to_json_payload(
    report: MarketOutcomeEvidenceQualityDigest,
) -> dict[str, Any]:
    if type(report) is not MarketOutcomeEvidenceQualityDigest:
        raise ValueError("report must be a MarketOutcomeEvidenceQualityDigest")
    revalidated_report = _revalidate_digest(report)
    payload = _report_public_payload_for_digest(revalidated_report)
    payload["derived_validation_digest"] = revalidated_report.derived_validation_digest
    if not isinstance(payload, dict):
        raise ValueError("report payload must be a JSON object")
    validate_market_outcome_evidence_quality_digest_public_payload(payload)
    return payload


def validate_market_outcome_evidence_quality_digest_public_payload(
    payload: dict[str, Any],
) -> bool:
    if type(payload) is not dict:
        raise ValueError("payload must be a dict")
    _reject_unsafe_public_payload("market outcome evidence quality payload", payload)
    _require_public_payload_flags(payload)
    _reject_public_numeric_values(payload)
    digest_value = _payload_required_string(payload, "derived_validation_digest")
    _require_sha256_digest("derived_validation_digest", digest_value)
    if digest_value != _public_payload_derived_validation_digest(payload):
        raise ValueError("derived_validation_digest must match public payload")
    return True


def _build_market_row(
    *,
    category_id: str,
    market_slug: str,
    evidence: tuple[MarketOutcomeEvidenceObservation, ...],
    config: MarketOutcomeEvidenceQualityConfig,
    generated_at_utc: datetime,
) -> MarketOutcomeEvidenceQualityRow:
    ordered = tuple(sorted(evidence, key=lambda item: (item.evidence_id, item.source_id)))
    evidence_count = len(ordered)
    source_ids = tuple(sorted({item.source_id for item in ordered}))
    observed_outcomes = tuple(sorted({item.observed_outcome for item in ordered}))
    authoritative_source_count = sum(
        1 for item in ordered if item.source_kind in config.authoritative_source_kinds
    )
    agreement_ratio = _source_agreement_ratio(ordered)
    ambiguity_count = sum(1 for item in ordered if item.unresolved_ambiguity)
    ambiguity_ratio = _ratio(ambiguity_count, evidence_count)
    latest_evidence_observed_at = max(item.evidence_observed_at for item in ordered)
    latest_evidence_age_seconds = _age_seconds(
        generated_at_utc=generated_at_utc,
        observed_at=latest_evidence_observed_at,
        field_name="latest_evidence_age_seconds",
    )
    acknowledged_items = tuple(
        item.acknowledged_at for item in ordered if item.acknowledged_at is not None
    )
    latest_acknowledged_at = max(acknowledged_items) if acknowledged_items else None
    latest_acknowledgement_age_seconds = (
        _age_seconds(
            generated_at_utc=generated_at_utc,
            observed_at=latest_acknowledged_at,
            field_name="latest_acknowledgement_age_seconds",
        )
        if latest_acknowledged_at is not None
        else None
    )
    authoritative_source_present = authoritative_source_count > 0
    source_agreement_present = agreement_ratio >= config.min_source_agreement_ratio
    evidence_fresh = latest_evidence_age_seconds <= config.max_evidence_age_seconds
    acknowledgement_fresh = (
        latest_acknowledgement_age_seconds is not None
        and latest_acknowledgement_age_seconds
        <= config.max_acknowledgement_age_seconds
    )
    ambiguity_clear = ambiguity_ratio <= config.max_unresolved_ambiguity_ratio
    quality_status = _quality_status(
        authoritative_source_present=authoritative_source_present,
        source_agreement_present=source_agreement_present,
        evidence_fresh=evidence_fresh,
        acknowledgement_fresh=acknowledgement_fresh,
        ambiguity_clear=ambiguity_clear,
    )

    reason_codes = _row_reason_codes(
        authoritative_source_present=authoritative_source_present,
        source_agreement_present=source_agreement_present,
        evidence_fresh=evidence_fresh,
        acknowledgement_fresh=acknowledgement_fresh,
        latest_acknowledged_at=latest_acknowledged_at,
        ambiguity_clear=ambiguity_clear,
        quality_status=quality_status,
        input_reason_codes=tuple(
            reason_code for item in ordered for reason_code in item.reason_codes
        ),
    )

    return MarketOutcomeEvidenceQualityRow(
        market_slug=market_slug,
        category_id=category_id,
        evidence_count=_decimal_count(evidence_count),
        source_count=_decimal_count(len(source_ids)),
        authoritative_source_count=_decimal_count(authoritative_source_count),
        authoritative_source_present=authoritative_source_present,
        unique_outcome_count=_decimal_count(len(observed_outcomes)),
        source_agreement_ratio=agreement_ratio,
        source_agreement_present=source_agreement_present,
        latest_evidence_observed_at=latest_evidence_observed_at,
        latest_evidence_age_seconds=latest_evidence_age_seconds,
        evidence_fresh=evidence_fresh,
        latest_acknowledged_at=latest_acknowledged_at,
        latest_acknowledgement_age_seconds=latest_acknowledgement_age_seconds,
        acknowledgement_fresh=acknowledgement_fresh,
        unresolved_ambiguity_count=_decimal_count(ambiguity_count),
        unresolved_ambiguity_ratio=ambiguity_ratio,
        quality_status=quality_status,
        evidence_ids=tuple(item.evidence_id for item in ordered),
        source_ids=source_ids,
        observed_outcomes=observed_outcomes,
        reason_codes=reason_codes,
    )


def _source_agreement_ratio(
    evidence: tuple[MarketOutcomeEvidenceObservation, ...],
) -> Decimal:
    counts: dict[str, int] = {}
    for item in evidence:
        counts[item.observed_outcome] = counts.get(item.observed_outcome, 0) + 1
    return _ratio(max(counts.values()), len(evidence))


def _quality_status(
    *,
    authoritative_source_present: bool,
    source_agreement_present: bool,
    evidence_fresh: bool,
    acknowledgement_fresh: bool,
    ambiguity_clear: bool,
) -> str:
    if not ambiguity_clear:
        return "unresolved_ambiguity"
    if not authoritative_source_present:
        return "missing_authoritative_source"
    if not source_agreement_present:
        return "source_disagreement"
    if not evidence_fresh:
        return "stale_evidence"
    if not acknowledgement_fresh:
        return "stale_acknowledgement"
    return "high_quality"


def _row_reason_codes(
    *,
    authoritative_source_present: bool,
    source_agreement_present: bool,
    evidence_fresh: bool,
    acknowledgement_fresh: bool,
    latest_acknowledged_at: datetime | None,
    ambiguity_clear: bool,
    quality_status: str,
    input_reason_codes: tuple[str, ...],
) -> tuple[str, ...]:
    reason_codes = [
        "has_authoritative_source"
        if authoritative_source_present
        else "missing_authoritative_source",
        "sources_agree" if source_agreement_present else "sources_disagree",
        "evidence_fresh" if evidence_fresh else "evidence_stale",
        "ambiguity_clear" if ambiguity_clear else "unresolved_ambiguity",
    ]
    if latest_acknowledged_at is None:
        reason_codes.append("acknowledgement_missing")
    else:
        reason_codes.append(
            "acknowledgement_fresh"
            if acknowledgement_fresh
            else "acknowledgement_stale",
        )
    if quality_status == "high_quality":
        reason_codes.append("high_quality_evidence")
    for reason_code in input_reason_codes:
        reason_codes.append(f"input_{reason_code}")
    return tuple(sorted(set(reason_codes)))


def _build_category_rollups(
    rows: tuple[MarketOutcomeEvidenceQualityRow, ...],
) -> tuple[MarketOutcomeEvidenceQualityCategoryRollup, ...]:
    grouped: dict[str, list[MarketOutcomeEvidenceQualityRow]] = {}
    for row in rows:
        grouped.setdefault(row.category_id, []).append(row)

    rollups: list[MarketOutcomeEvidenceQualityCategoryRollup] = []
    for category_id in sorted(grouped):
        category_rows = tuple(grouped[category_id])
        market_count = len(category_rows)
        high_quality_count = sum(
            1 for row in category_rows if row.quality_status == "high_quality"
        )
        rollups.append(
            MarketOutcomeEvidenceQualityCategoryRollup(
                category_id=category_id,
                market_count=_decimal_count(market_count),
                evidence_count=sum(
                    (row.evidence_count for row in category_rows),
                    ZERO,
                ),
                high_quality_market_count=_decimal_count(high_quality_count),
                high_quality_market_ratio=_ratio(high_quality_count, market_count),
                missing_authoritative_source_market_count=_status_count(
                    category_rows,
                    "missing_authoritative_source",
                ),
                source_disagreement_market_count=_status_count(
                    category_rows,
                    "source_disagreement",
                ),
                stale_evidence_market_count=_status_count(
                    category_rows,
                    "stale_evidence",
                ),
                stale_acknowledgement_market_count=_status_count(
                    category_rows,
                    "stale_acknowledgement",
                ),
                unresolved_ambiguity_market_count=_status_count(
                    category_rows,
                    "unresolved_ambiguity",
                ),
                reason_code_counts=_build_reason_code_counts(category_rows),
            ),
        )
    return tuple(rollups)


def _build_reason_code_counts(
    rows: tuple[MarketOutcomeEvidenceQualityRow, ...],
) -> tuple[MarketOutcomeEvidenceQualityReasonCodeCount, ...]:
    if not rows:
        return ()
    counts: dict[str, int] = {}
    for row in rows:
        for reason_code in row.reason_codes:
            counts[reason_code] = counts.get(reason_code, 0) + 1
    return tuple(
        MarketOutcomeEvidenceQualityReasonCodeCount(
            reason_code=reason_code,
            market_count=_decimal_count(counts[reason_code]),
            market_ratio=_ratio(counts[reason_code], len(rows)),
        )
        for reason_code in sorted(counts)
    )


def _status_count(
    rows: tuple[MarketOutcomeEvidenceQualityRow, ...],
    status: str,
) -> Decimal:
    return _decimal_count(sum(1 for row in rows if row.quality_status == status))


def _normalize_evidence(
    evidence: (
        list[MarketOutcomeEvidenceObservation]
        | tuple[MarketOutcomeEvidenceObservation, ...]
    ),
) -> tuple[MarketOutcomeEvidenceObservation, ...]:
    if type(evidence) not in (list, tuple):
        raise ValueError("evidence must be a list or tuple")
    items = tuple(evidence)
    for item in items:
        if type(item) is not MarketOutcomeEvidenceObservation:
            raise ValueError(
                "evidence must contain MarketOutcomeEvidenceObservation values",
            )
        _require_hard_flags(item)
    return items


def _normalize_rows(
    rows: tuple[MarketOutcomeEvidenceQualityRow, ...],
) -> tuple[MarketOutcomeEvidenceQualityRow, ...]:
    if type(rows) is not tuple:
        raise ValueError("rows must be a tuple")
    for row in rows:
        if type(row) is not MarketOutcomeEvidenceQualityRow:
            raise ValueError("rows must contain MarketOutcomeEvidenceQualityRow values")
        _require_hard_flags(row)
    sorted_rows = tuple(sorted(rows, key=lambda row: (row.category_id, row.market_slug)))
    if rows != sorted_rows:
        raise ValueError("rows must be sorted by category_id and market_slug")
    return rows


def _normalize_category_rollups(
    rows: tuple[MarketOutcomeEvidenceQualityCategoryRollup, ...],
) -> tuple[MarketOutcomeEvidenceQualityCategoryRollup, ...]:
    if type(rows) is not tuple:
        raise ValueError("category_rollups must be a tuple")
    for row in rows:
        if type(row) is not MarketOutcomeEvidenceQualityCategoryRollup:
            raise ValueError(
                "category_rollups must contain "
                "MarketOutcomeEvidenceQualityCategoryRollup values",
            )
        _require_hard_flags(row)
    sorted_rows = tuple(sorted(rows, key=lambda row: row.category_id))
    if rows != sorted_rows:
        raise ValueError("category_rollups must be sorted by category_id")
    return rows


def _normalize_reason_code_counts(
    rows: tuple[MarketOutcomeEvidenceQualityReasonCodeCount, ...],
) -> tuple[MarketOutcomeEvidenceQualityReasonCodeCount, ...]:
    if type(rows) is not tuple:
        raise ValueError("reason_code_counts must be a tuple")
    for row in rows:
        if type(row) is not MarketOutcomeEvidenceQualityReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "MarketOutcomeEvidenceQualityReasonCodeCount values",
            )
        _require_hard_flags(row)
    sorted_rows = tuple(sorted(rows, key=lambda row: row.reason_code))
    if rows != sorted_rows:
        raise ValueError("reason_code_counts must be sorted by reason_code")
    return rows


def _validate_row_consistency(row: MarketOutcomeEvidenceQualityRow) -> None:
    if row.evidence_count <= ZERO:
        raise ValueError("evidence_count must be positive for market rows")
    if row.authoritative_source_count > row.evidence_count:
        raise ValueError("authoritative_source_count must not exceed evidence_count")
    if row.unresolved_ambiguity_count > row.evidence_count:
        raise ValueError("unresolved_ambiguity_count must not exceed evidence_count")
    if row.source_count > row.evidence_count:
        raise ValueError("source_count must not exceed evidence_count")
    if row.unique_outcome_count > row.evidence_count:
        raise ValueError("unique_outcome_count must not exceed evidence_count")
    if row.authoritative_source_present != (row.authoritative_source_count > ZERO):
        raise ValueError("authoritative_source_present must match source count")
    if row.evidence_count != _decimal_count(len(row.evidence_ids)):
        raise ValueError("evidence_ids must match evidence_count")
    if row.source_count != _decimal_count(len(row.source_ids)):
        raise ValueError("source_ids must match source_count")
    if row.unique_outcome_count != _decimal_count(len(row.observed_outcomes)):
        raise ValueError("observed_outcomes must match unique_outcome_count")
    if (
        row.latest_acknowledged_at is None
        and row.latest_acknowledgement_age_seconds is not None
    ):
        raise ValueError(
            "latest_acknowledgement_age_seconds must be absent without acknowledgement",
        )
    if (
        row.latest_acknowledged_at is not None
        and row.latest_acknowledgement_age_seconds is None
    ):
        raise ValueError(
            "latest_acknowledgement_age_seconds is required with acknowledgement",
        )


def _validate_digest_consistency(
    report: MarketOutcomeEvidenceQualityDigest,
) -> None:
    if report.market_count != _decimal_count(len(report.rows)):
        raise ValueError("market_count must match rows")
    if report.category_count != _decimal_count(len(report.category_rollups)):
        raise ValueError("category_count must match category_rollups")
    if report.evidence_count != sum((row.evidence_count for row in report.rows), ZERO):
        raise ValueError("evidence_count must match rows")
    if report.high_quality_market_count != _status_count(report.rows, "high_quality"):
        raise ValueError("high_quality_market_count must match rows")
    if report.missing_authoritative_source_market_count != _status_count(
        report.rows,
        "missing_authoritative_source",
    ):
        raise ValueError("missing_authoritative_source_market_count must match rows")
    if report.source_disagreement_market_count != _status_count(
        report.rows,
        "source_disagreement",
    ):
        raise ValueError("source_disagreement_market_count must match rows")
    if report.stale_evidence_market_count != _status_count(
        report.rows,
        "stale_evidence",
    ):
        raise ValueError("stale_evidence_market_count must match rows")
    if report.stale_acknowledgement_market_count != _status_count(
        report.rows,
        "stale_acknowledgement",
    ):
        raise ValueError("stale_acknowledgement_market_count must match rows")
    if report.unresolved_ambiguity_market_count != _status_count(
        report.rows,
        "unresolved_ambiguity",
    ):
        raise ValueError("unresolved_ambiguity_market_count must match rows")
    if report.category_rollups != _build_category_rollups(report.rows):
        raise ValueError("category_rollups must match rows")
    if report.reason_code_counts != _build_reason_code_counts(report.rows):
        raise ValueError("reason_code_counts must match rows")
    if report.derived_validation_digest != _report_derived_validation_digest(report):
        raise ValueError("derived_validation_digest must match report fields")


def _revalidate_digest(
    report: MarketOutcomeEvidenceQualityDigest,
) -> MarketOutcomeEvidenceQualityDigest:
    return MarketOutcomeEvidenceQualityDigest(
        generated_at=report.generated_at,
        config_version=report.config_version,
        market_count=report.market_count,
        category_count=report.category_count,
        evidence_count=report.evidence_count,
        high_quality_market_count=report.high_quality_market_count,
        missing_authoritative_source_market_count=(
            report.missing_authoritative_source_market_count
        ),
        source_disagreement_market_count=report.source_disagreement_market_count,
        stale_evidence_market_count=report.stale_evidence_market_count,
        stale_acknowledgement_market_count=report.stale_acknowledgement_market_count,
        unresolved_ambiguity_market_count=report.unresolved_ambiguity_market_count,
        rows=report.rows,
        category_rollups=report.category_rollups,
        reason_code_counts=report.reason_code_counts,
        derived_validation_digest=report.derived_validation_digest,
        paper_only=report.paper_only,
        report_only=report.report_only,
        readonly=report.readonly,
    )


def _report_derived_validation_digest(
    report: MarketOutcomeEvidenceQualityDigest,
) -> str:
    return _public_payload_derived_validation_digest(_report_public_payload_for_digest(report))


def _report_public_payload_for_digest(
    report: MarketOutcomeEvidenceQualityDigest,
) -> dict[str, Any]:
    payload = _json_value(report)
    if not isinstance(payload, dict):
        raise ValueError("report payload must be a JSON object")
    payload.pop("derived_validation_digest", None)
    return payload


def _public_payload_derived_validation_digest(payload: dict[str, Any]) -> str:
    digest_payload = dict(payload)
    digest_payload.pop("derived_validation_digest", None)
    encoded_payload = json.dumps(
        digest_payload,
        sort_keys=True,
        separators=(",", ":"),
    )
    return hashlib.sha256(encoded_payload.encode("utf-8")).hexdigest()


def _require_sha256_digest(field_name: str, value: Any) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if len(value) != 64 or any(character not in "0123456789abcdef" for character in value):
        raise ValueError(f"{field_name} must be a lowercase sha256 hex digest")
    return value


def _payload_required_string(payload: dict[str, Any], field_name: str) -> str:
    if field_name not in payload:
        raise ValueError(f"{field_name} is required")
    value = payload[field_name]
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    return value


def _require_public_payload_flags(payload: dict[str, Any]) -> None:
    for flag_name in ("paper_only", "report_only", "readonly"):
        if payload.get(flag_name) is not True:
            raise ValueError(f"{flag_name} must be True")
    _require_nested_public_payload_flags(payload)


def _require_nested_public_payload_flags(value: Any) -> None:
    if isinstance(value, dict):
        flag_names = ("paper_only", "report_only", "readonly")
        if any(flag_name in value for flag_name in flag_names):
            for flag_name in flag_names:
                if value.get(flag_name) is not True:
                    raise ValueError(f"{flag_name} must be True")
        for item in value.values():
            _require_nested_public_payload_flags(item)
    elif isinstance(value, list):
        for item in value:
            _require_nested_public_payload_flags(item)


def _reject_public_numeric_values(value: Any) -> None:
    if type(value) in (int, float) or type(value) is Decimal:
        raise ValueError("public payload numeric values must be Decimal strings")
    if isinstance(value, dict):
        for item in value.values():
            _reject_public_numeric_values(item)
    elif isinstance(value, list):
        for item in value:
            _reject_public_numeric_values(item)


def _reject_unsafe_public_payload(label: str, value: Any) -> None:
    for public_text in _public_payload_strings(value):
        _reject_sensitive_text(public_text)
        lowered = public_text.lower()
        if any(fragment in lowered for fragment in UNSAFE_PUBLIC_SURFACE_FRAGMENTS):
            raise ValueError(f"unsafe surface value in {label}")


def _public_payload_strings(value: Any) -> tuple[str, ...]:
    if isinstance(value, dict):
        texts: list[str] = []
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("public payload object keys must be strings")
            texts.append(key)
            texts.extend(_public_payload_strings(item))
        return tuple(texts)
    if isinstance(value, list):
        texts = []
        for item in value:
            texts.extend(_public_payload_strings(item))
        return tuple(texts)
    if type(value) is str:
        return (value,)
    return ()


def _ratio(numerator: int, denominator: int) -> Decimal:
    if denominator <= 0:
        raise ValueError("ratio denominator must be positive")
    return (Decimal(numerator) / Decimal(denominator)).quantize(
        RATIO_QUANTUM,
        rounding=ROUND_HALF_EVEN,
    )


def _decimal_count(value: int) -> Decimal:
    if type(value) is not int or value < 0:
        raise ValueError("count value must be a nonnegative integer")
    return Decimal(value)


def _age_seconds(
    *,
    generated_at_utc: datetime,
    observed_at: datetime,
    field_name: str,
) -> Decimal:
    delta = generated_at_utc - observed_at
    if delta.days < 0:
        raise ValueError(f"{field_name} must be nonnegative")
    if delta.microseconds != 0:
        raise ValueError(f"{field_name} must be whole seconds")
    return Decimal(delta.days * 86400 + delta.seconds)


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _as_optional_utc(field_name: str, value: object) -> datetime | None:
    if value is None:
        return None
    return _as_utc(field_name, value)


def _require_canonical_string(field_name: str, value: Any) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")


def _normalize_string_tuple(field_name: str, value: object) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ValueError(f"{field_name} must be a tuple")
    items: list[str] = []
    for item in value:
        _require_canonical_string(field_name, item)
        if item not in items:
            items.append(item)
    return tuple(items)


def _require_nonnegative_decimal(field_name: str, value: Any) -> None:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    if value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")


def _require_probability_decimal(field_name: str, value: Any) -> None:
    _require_nonnegative_decimal(field_name, value)
    if value > ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    if value != value.quantize(RATIO_QUANTUM, rounding=ROUND_HALF_EVEN):
        raise ValueError(f"{field_name} must use 0.000001 precision")


def _require_hard_flags(value: Any) -> None:
    if getattr(value, "paper_only", None) is not True:
        raise ValueError("paper_only must be True")
    if getattr(value, "report_only", None) is not True:
        raise ValueError("report_only must be True")
    if getattr(value, "readonly", None) is not True:
        raise ValueError("readonly must be True")


def _json_value(value: Any) -> Any:
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, datetime):
        return value.isoformat()
    if is_dataclass(value) and not isinstance(value, type):
        return {
            field.name: _json_value(getattr(value, field.name))
            for field in fields(value)
        }
    if isinstance(value, tuple):
        return [_json_value(item) for item in value]
    if isinstance(value, list):
        return [_json_value(item) for item in value]
    if isinstance(value, dict):
        return {key: _json_value(item) for key, item in value.items()}
    if type(value) is str:
        _reject_sensitive_text(value)
    return value


def _reject_sensitive_text(value: str) -> None:
    normalized = value.lower()
    if any(fragment in normalized for fragment in SENSITIVE_TEXT_FRAGMENTS):
        raise ValueError("sensitive public string is not allowed")
