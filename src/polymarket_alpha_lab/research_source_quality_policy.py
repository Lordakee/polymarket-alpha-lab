"""Pure source-quality scoring policy for caller-supplied research evidence.

The module is deterministic and side-effect free. Callers provide typed evidence
rows; the policy returns report-only scores, statuses, and reason codes.
"""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable
from dataclasses import dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation
from typing import Any


__all__ = (
    "ResearchSourceQualityConfig",
    "ResearchSourceQualityEvidenceRow",
    "ResearchSourceQualityReasonCodeCount",
    "ResearchSourceQualityReport",
    "ResearchSourceQualityScoreRow",
    "build_research_source_quality_report",
    "research_source_quality_report_payload",
)


DEFAULT_CONFIG_VERSION = "research-source-quality-policy-v0"
STATUSES = ("pass", "watch", "blocked")
SOURCE_TYPES = ("primary", "secondary")
DIRECTNESS_SCORES = {
    "direct": Decimal("1.000000"),
    "indirect": Decimal("0.600000"),
    "context": Decimal("0.300000"),
}
ZERO = Decimal("0")
ONE = Decimal("1")
RATIO_QUANTUM = Decimal("0.000001")
DEFAULT_PASS_QUALITY_SCORE = Decimal("0.700000")
DEFAULT_WATCH_QUALITY_SCORE = Decimal("0.400000")


class _Missing:
    pass


_MISSING = _Missing()


@dataclass(frozen=True)
class ResearchSourceQualityConfig:
    config_version: str = DEFAULT_CONFIG_VERSION
    fresh_age_seconds: Decimal = Decimal("3600")
    stale_age_seconds: Decimal = Decimal("86400")
    min_source_count: Decimal = Decimal("2")
    min_source_family_count: Decimal = Decimal("2")
    pass_quality_score: Decimal = DEFAULT_PASS_QUALITY_SCORE
    watch_quality_score: Decimal = DEFAULT_WATCH_QUALITY_SCORE
    recency_weight: Decimal = Decimal("0.350000")
    diversity_weight: Decimal = Decimal("0.250000")
    directness_weight: Decimal = Decimal("0.200000")
    primary_source_weight: Decimal = Decimal("0.200000")
    missing_source_penalty: Decimal = Decimal("0.250000")
    conflict_flag_penalty: Decimal = Decimal("0.150000")
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
        for field_name in ("min_source_count", "min_source_family_count"):
            object.__setattr__(
                self,
                field_name,
                _require_positive_whole_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "pass_quality_score",
            "watch_quality_score",
            "recency_weight",
            "diversity_weight",
            "directness_weight",
            "primary_source_weight",
            "missing_source_penalty",
            "conflict_flag_penalty",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_probability_decimal(field_name, getattr(self, field_name)),
            )
        if self.pass_quality_score <= self.watch_quality_score:
            raise ValueError("pass_quality_score must be greater than watch_quality_score")
        component_weight_sum = _quantize(
            self.recency_weight
            + self.diversity_weight
            + self.directness_weight
            + self.primary_source_weight,
        )
        if component_weight_sum != ONE:
            raise ValueError(
                "recency_weight, diversity_weight, directness_weight, "
                "and primary_source_weight must sum to 1",
            )
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class ResearchSourceQualityEvidenceRow:
    claim_id: str
    evidence_id: str
    source_id: str | None
    source_family: str | None
    source_type: str
    directness: str
    observed_at: datetime
    conflict_flag: bool = False
    reason_codes: tuple[str, ...] = ()
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("claim_id", self.claim_id)
        _require_canonical_string("evidence_id", self.evidence_id)
        object.__setattr__(
            self,
            "source_id",
            _require_optional_canonical_string("source_id", self.source_id),
        )
        object.__setattr__(
            self,
            "source_family",
            _require_optional_canonical_string("source_family", self.source_family),
        )
        _require_enum("source_type", self.source_type, SOURCE_TYPES)
        _require_enum("directness", self.directness, tuple(DIRECTNESS_SCORES))
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        if type(self.conflict_flag) is not bool:
            raise ValueError("conflict_flag must be a bool")
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, allow_empty=True),
        )
        _require_hard_flags("evidence", self)


@dataclass(frozen=True)
class ResearchSourceQualityScoreRow:
    claim_id: str
    evidence_count: Decimal
    source_count: Decimal
    source_family_count: Decimal
    latest_observed_at: datetime
    latest_source_age_seconds: Decimal
    recency_score: Decimal
    diversity_score: Decimal
    directness_score: Decimal
    primary_source_score: Decimal
    missing_source_count: Decimal
    conflict_flag_count: Decimal
    missing_source_penalty_score: Decimal
    conflict_flag_penalty_score: Decimal
    quality_score: Decimal
    evidence_ids: tuple[str, ...]
    source_ids: tuple[str, ...]
    source_families: tuple[str, ...]
    status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("claim_id", self.claim_id)
        for field_name in (
            "evidence_count",
            "source_count",
            "source_family_count",
            "missing_source_count",
            "conflict_flag_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_whole_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "latest_observed_at",
            _as_utc("latest_observed_at", self.latest_observed_at),
        )
        object.__setattr__(
            self,
            "latest_source_age_seconds",
            _require_nonnegative_decimal(
                "latest_source_age_seconds",
                self.latest_source_age_seconds,
            ),
        )
        for field_name in (
            "recency_score",
            "diversity_score",
            "directness_score",
            "primary_source_score",
            "missing_source_penalty_score",
            "conflict_flag_penalty_score",
            "quality_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_probability_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in ("evidence_ids", "source_ids", "source_families"):
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
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, allow_empty=False),
        )
        _require_hard_flags("row", self)
        _validate_score_row_consistency(self)


@dataclass(frozen=True)
class ResearchSourceQualityReasonCodeCount:
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
            _require_positive_whole_decimal("count", self.count),
        )
        _require_hard_flags("reason_code_count", self)


@dataclass(frozen=True)
class ResearchSourceQualityReport:
    generated_at: datetime
    config_version: str
    claim_count: Decimal
    evidence_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    blocked_count: Decimal
    average_quality_score: Decimal | None
    status: str
    rows: tuple[ResearchSourceQualityScoreRow, ...]
    reason_code_counts: tuple[ResearchSourceQualityReasonCodeCount, ...]
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        for field_name in (
            "claim_count",
            "evidence_count",
            "pass_count",
            "watch_count",
            "blocked_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_whole_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "average_quality_score",
            _require_optional_probability_decimal(
                "average_quality_score",
                self.average_quality_score,
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
        _validate_report_consistency(self)


def build_research_source_quality_report(
    evidence_rows: Iterable[object],
    *,
    config: ResearchSourceQualityConfig,
    generated_at: datetime,
) -> ResearchSourceQualityReport:
    if type(config) is not ResearchSourceQualityConfig:
        raise ValueError("config must be a ResearchSourceQualityConfig")
    _require_hard_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    evidence_items = _normalize_evidence_rows(evidence_rows)
    for item in evidence_items:
        _reject_future_observed_at(item, generated_at_utc)

    grouped: dict[str, list[ResearchSourceQualityEvidenceRow]] = {}
    for item in evidence_items:
        grouped.setdefault(item.claim_id, []).append(item)

    rows = tuple(
        _score_row_from_claim(
            claim_id=claim_id,
            evidence_rows=tuple(grouped[claim_id]),
            config=config,
            generated_at=generated_at_utc,
        )
        for claim_id in sorted(grouped)
    )
    reason_codes = _summary_reason_codes(rows)

    return ResearchSourceQualityReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        claim_count=_decimal_count(len(rows)),
        evidence_count=sum((row.evidence_count for row in rows), ZERO),
        pass_count=_decimal_count(_status_count(rows, "pass")),
        watch_count=_decimal_count(_status_count(rows, "watch")),
        blocked_count=_decimal_count(_status_count(rows, "blocked")),
        average_quality_score=_average_quality_score(rows),
        status=_summary_status(reason_codes),
        rows=rows,
        reason_code_counts=_reason_code_counts(rows, reason_codes),
        reason_codes=reason_codes,
    )


def research_source_quality_report_payload(
    report: ResearchSourceQualityReport,
) -> dict[str, Any]:
    if type(report) is not ResearchSourceQualityReport:
        raise ValueError("report must be a ResearchSourceQualityReport")
    _require_hard_flags("report", report)
    payload = _payload_value(report)
    if not isinstance(payload, dict):
        raise ValueError("report payload must be a JSON object")
    return payload


def _score_row_from_claim(
    *,
    claim_id: str,
    evidence_rows: tuple[ResearchSourceQualityEvidenceRow, ...],
    config: ResearchSourceQualityConfig,
    generated_at: datetime,
) -> ResearchSourceQualityScoreRow:
    sorted_rows = tuple(
        sorted(
            evidence_rows,
            key=lambda item: (
                item.evidence_id,
                item.source_id or "",
                item.source_family or "",
            ),
        ),
    )
    latest = max(sorted_rows, key=lambda item: item.observed_at)
    latest_age = _age_seconds(generated_at, latest.observed_at)
    age_scores = tuple(
        _recency_score(
            _age_seconds(generated_at, item.observed_at),
            fresh_age_seconds=config.fresh_age_seconds,
            stale_age_seconds=config.stale_age_seconds,
        )
        for item in sorted_rows
    )
    recency_score = _average_decimal(age_scores)
    source_ids = tuple(sorted({item.source_id for item in sorted_rows if item.source_id}))
    source_families = tuple(
        sorted({item.source_family for item in sorted_rows if item.source_family}),
    )
    source_count = len(source_ids)
    source_family_count = len(source_families)
    diversity_score = _diversity_score(
        source_count=source_count,
        source_family_count=source_family_count,
        config=config,
    )
    directness_score = _average_decimal(
        tuple(DIRECTNESS_SCORES[item.directness] for item in sorted_rows),
    )
    primary_source_score = _quantize(
        Decimal(sum(1 for item in sorted_rows if item.source_type == "primary"))
        / Decimal(len(sorted_rows)),
    )
    missing_source_count = sum(
        1 for item in sorted_rows if item.source_id is None or item.source_family is None
    )
    conflict_flag_count = sum(1 for item in sorted_rows if item.conflict_flag)
    missing_penalty_score = _bounded_penalty(
        config.missing_source_penalty,
        missing_source_count,
    )
    conflict_penalty_score = _bounded_penalty(
        config.conflict_flag_penalty,
        conflict_flag_count,
    )
    quality_score = _quality_score(
        recency_score=recency_score,
        diversity_score=diversity_score,
        directness_score=directness_score,
        primary_source_score=primary_source_score,
        missing_source_penalty_score=missing_penalty_score,
        conflict_flag_penalty_score=conflict_penalty_score,
        config=config,
    )
    stale_count = sum(
        1
        for item in sorted_rows
        if _age_seconds(generated_at, item.observed_at) >= config.stale_age_seconds
    )
    source_diversity_met = (
        Decimal(source_count) >= config.min_source_count
        and Decimal(source_family_count) >= config.min_source_family_count
    )
    status = _row_status(
        quality_score=quality_score,
        source_diversity_met=source_diversity_met,
        missing_source_count=missing_source_count,
        conflict_flag_count=conflict_flag_count,
        primary_source_score=primary_source_score,
        config=config,
    )
    reason_codes = _row_reason_codes(
        status=status,
        stale_count=stale_count,
        source_diversity_met=source_diversity_met,
        directness_score=directness_score,
        missing_source_count=missing_source_count,
        conflict_flag_count=conflict_flag_count,
        primary_source_score=primary_source_score,
        input_reason_codes=tuple(
            reason_code for item in sorted_rows for reason_code in item.reason_codes
        ),
    )

    return ResearchSourceQualityScoreRow(
        claim_id=claim_id,
        evidence_count=_decimal_count(len(sorted_rows)),
        source_count=_decimal_count(source_count),
        source_family_count=_decimal_count(source_family_count),
        latest_observed_at=latest.observed_at,
        latest_source_age_seconds=latest_age,
        recency_score=recency_score,
        diversity_score=diversity_score,
        directness_score=directness_score,
        primary_source_score=primary_source_score,
        missing_source_count=_decimal_count(missing_source_count),
        conflict_flag_count=_decimal_count(conflict_flag_count),
        missing_source_penalty_score=missing_penalty_score,
        conflict_flag_penalty_score=conflict_penalty_score,
        quality_score=quality_score,
        evidence_ids=tuple(item.evidence_id for item in sorted_rows),
        source_ids=source_ids,
        source_families=source_families,
        status=status,
        reason_codes=reason_codes,
    )


def _normalize_evidence_rows(
    evidence_rows: Iterable[object],
) -> tuple[ResearchSourceQualityEvidenceRow, ...]:
    if isinstance(evidence_rows, (str, bytes)):
        raise ValueError("evidence_rows must be an iterable")
    try:
        values = tuple(evidence_rows)
    except TypeError as exc:
        raise ValueError("evidence_rows must be an iterable") from exc
    return tuple(_coerce_evidence_row(value) for value in values)


def _coerce_evidence_row(value: object) -> ResearchSourceQualityEvidenceRow:
    if type(value) is ResearchSourceQualityEvidenceRow:
        _require_hard_flags("evidence", value)
        return value
    _require_hard_flags("evidence", value)
    return ResearchSourceQualityEvidenceRow(
        claim_id=_field_value(value, "claim_id"),
        evidence_id=_field_value(value, "evidence_id"),
        source_id=_field_value(value, "source_id"),
        source_family=_field_value(value, "source_family"),
        source_type=_field_value(value, "source_type"),
        directness=_field_value(value, "directness"),
        observed_at=_field_value(value, "observed_at"),
        conflict_flag=_field_value(value, "conflict_flag", default=False),
        reason_codes=_field_value(value, "reason_codes", default=()),
        paper_only=_field_value(value, "paper_only"),
        report_only=_field_value(value, "report_only"),
        readonly=_field_value(value, "readonly"),
    )


def _recency_score(
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


def _diversity_score(
    *,
    source_count: int,
    source_family_count: int,
    config: ResearchSourceQualityConfig,
) -> Decimal:
    source_ratio = min(ONE, Decimal(source_count) / config.min_source_count)
    family_ratio = min(ONE, Decimal(source_family_count) / config.min_source_family_count)
    return _quantize((source_ratio + family_ratio) / Decimal("2"))


def _quality_score(
    *,
    recency_score: Decimal,
    diversity_score: Decimal,
    directness_score: Decimal,
    primary_source_score: Decimal,
    missing_source_penalty_score: Decimal,
    conflict_flag_penalty_score: Decimal,
    config: ResearchSourceQualityConfig,
) -> Decimal:
    raw_score = (
        (recency_score * config.recency_weight)
        + (diversity_score * config.diversity_weight)
        + (directness_score * config.directness_weight)
        + (primary_source_score * config.primary_source_weight)
        - missing_source_penalty_score
        - conflict_flag_penalty_score
    )
    return _quantize(max(ZERO, min(ONE, raw_score)))


def _bounded_penalty(penalty: Decimal, count: int) -> Decimal:
    return _quantize(min(ONE, penalty * Decimal(count)))


def _row_status(
    *,
    quality_score: Decimal,
    source_diversity_met: bool,
    missing_source_count: int,
    conflict_flag_count: int,
    primary_source_score: Decimal,
    config: ResearchSourceQualityConfig,
) -> str:
    if quality_score < config.watch_quality_score:
        return "blocked"
    if quality_score < config.pass_quality_score:
        return "watch"
    if not source_diversity_met:
        return "watch"
    if missing_source_count or conflict_flag_count or primary_source_score == ZERO:
        return "watch"
    return "pass"


def _row_reason_codes(
    *,
    status: str,
    stale_count: int,
    source_diversity_met: bool,
    directness_score: Decimal,
    missing_source_count: int,
    conflict_flag_count: int,
    primary_source_score: Decimal,
    input_reason_codes: tuple[str, ...],
) -> tuple[str, ...]:
    reason_codes: set[str] = {f"research_source_quality_{status}"}
    reason_codes.add("stale_sources" if stale_count else "fresh_sources")
    reason_codes.add(
        "diverse_sources" if source_diversity_met else "not_enough_source_diversity",
    )
    if source_diversity_met and directness_score >= Decimal("0.750000"):
        reason_codes.add("direct_source_support")
    reason_codes.add(
        "primary_source_support"
        if primary_source_score > ZERO
        else "secondary_or_missing_primary_sources",
    )
    if missing_source_count:
        reason_codes.add("missing_sources_present")
    if conflict_flag_count:
        reason_codes.add("conflict_flags_present")
    for reason_code in input_reason_codes:
        reason_codes.add(f"input_{reason_code}")
    return tuple(sorted(reason_codes))


def _summary_reason_codes(
    rows: tuple[ResearchSourceQualityScoreRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return ("no_research_evidence",)
    if any(row.status == "blocked" for row in rows):
        return tuple(sorted({code for row in rows for code in row.reason_codes}))
    if all(row.status == "pass" for row in rows):
        return ("research_source_quality_pass",)
    return tuple(sorted({code for row in rows for code in row.reason_codes}))


def _summary_status(reason_codes: tuple[str, ...]) -> str:
    if reason_codes == ("no_research_evidence",):
        return "blocked"
    if "research_source_quality_blocked" in reason_codes:
        return "blocked"
    if "research_source_quality_watch" in reason_codes:
        return "watch"
    return "pass"


def _reason_code_counts(
    rows: tuple[ResearchSourceQualityScoreRow, ...],
    reason_codes: tuple[str, ...],
) -> tuple[ResearchSourceQualityReasonCodeCount, ...]:
    if not rows:
        return (
            ResearchSourceQualityReasonCodeCount(
                reason_code=reason_codes[0],
                count=ONE,
            ),
        )
    counts: Counter[str] = Counter()
    for row in rows:
        counts.update(row.reason_codes)
    return tuple(
        ResearchSourceQualityReasonCodeCount(
            reason_code=reason_code,
            count=_decimal_count(count),
        )
        for reason_code, count in sorted(counts.items(), key=lambda item: item[0])
    )


def _average_quality_score(
    rows: tuple[ResearchSourceQualityScoreRow, ...],
) -> Decimal | None:
    if not rows:
        return None
    return _average_decimal(tuple(row.quality_score for row in rows))


def _average_decimal(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        raise ValueError("values must be nonempty")
    return _quantize(sum(values, ZERO) / Decimal(len(values)))


def _age_seconds(generated_at: datetime, observed_at: datetime) -> Decimal:
    delta = generated_at - observed_at
    return (
        Decimal(delta.days * 86_400)
        + Decimal(delta.seconds)
        + (Decimal(delta.microseconds) / Decimal("1000000"))
    )


def _reject_future_observed_at(
    item: ResearchSourceQualityEvidenceRow,
    generated_at: datetime,
) -> None:
    if item.observed_at > generated_at:
        raise ValueError("observed_at must not be after generated_at")


def _status_count(rows: tuple[ResearchSourceQualityScoreRow, ...], status: str) -> int:
    return sum(1 for row in rows if row.status == status)


def _normalize_rows(
    rows: tuple[ResearchSourceQualityScoreRow, ...],
) -> tuple[ResearchSourceQualityScoreRow, ...]:
    if type(rows) is not tuple:
        raise ValueError("rows must be a tuple")
    for row in rows:
        if type(row) is not ResearchSourceQualityScoreRow:
            raise ValueError("rows must contain ResearchSourceQualityScoreRow values")
        _require_hard_flags("row", row)
    sorted_rows = tuple(sorted(rows, key=lambda row: row.claim_id))
    if rows != sorted_rows:
        raise ValueError("rows must be sorted by claim_id")
    return rows


def _normalize_reason_code_counts(
    counts: tuple[ResearchSourceQualityReasonCodeCount, ...],
) -> tuple[ResearchSourceQualityReasonCodeCount, ...]:
    if type(counts) is not tuple:
        raise ValueError("reason_code_counts must be a tuple")
    for count in counts:
        if type(count) is not ResearchSourceQualityReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "ResearchSourceQualityReasonCodeCount values",
            )
        _require_hard_flags("reason_code_count", count)
    sorted_counts = tuple(sorted(counts, key=lambda count: count.reason_code))
    if counts != sorted_counts:
        raise ValueError("reason_code_counts must be sorted by reason_code")
    return counts


def _validate_score_row_consistency(row: ResearchSourceQualityScoreRow) -> None:
    if row.evidence_count <= ZERO:
        raise ValueError("evidence_count must be positive")
    if row.source_count > row.evidence_count:
        raise ValueError("source_count must not exceed evidence_count")
    if row.source_family_count > row.evidence_count:
        raise ValueError("source_family_count must not exceed evidence_count")
    if row.missing_source_count > row.evidence_count:
        raise ValueError("missing_source_count must not exceed evidence_count")
    if row.conflict_flag_count > row.evidence_count:
        raise ValueError("conflict_flag_count must not exceed evidence_count")
    if row.evidence_count != _decimal_count(len(row.evidence_ids)):
        raise ValueError("evidence_ids must match evidence_count")
    if row.source_count != _decimal_count(len(row.source_ids)):
        raise ValueError("source_ids must match source_count")
    if row.source_family_count != _decimal_count(len(row.source_families)):
        raise ValueError("source_families must match source_family_count")
    if row.status == "pass" and row.quality_score < DEFAULT_PASS_QUALITY_SCORE:
        raise ValueError("quality_score must support pass status")
    if row.status == "watch" and (
        row.quality_score < DEFAULT_WATCH_QUALITY_SCORE
        or row.quality_score >= DEFAULT_PASS_QUALITY_SCORE
        and "not_enough_source_diversity" not in row.reason_codes
    ):
        raise ValueError("quality_score must support watch status")
    if row.status == "blocked" and row.quality_score >= DEFAULT_WATCH_QUALITY_SCORE:
        raise ValueError("quality_score must support blocked status")


def _validate_report_consistency(report: ResearchSourceQualityReport) -> None:
    if report.claim_count != _decimal_count(len(report.rows)):
        raise ValueError("claim_count must match rows")
    if report.evidence_count != sum((row.evidence_count for row in report.rows), ZERO):
        raise ValueError("evidence_count must match rows")
    if report.pass_count != _decimal_count(_status_count(report.rows, "pass")):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _decimal_count(_status_count(report.rows, "watch")):
        raise ValueError("watch_count must match rows")
    if report.blocked_count != _decimal_count(_status_count(report.rows, "blocked")):
        raise ValueError("blocked_count must match rows")
    if report.average_quality_score != _average_quality_score(report.rows):
        raise ValueError("average_quality_score must match rows")
    if report.reason_codes != _summary_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")
    if report.status != _summary_status(report.reason_codes):
        raise ValueError("status must match reason_codes")


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


def _payload_value(value: object) -> object:
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, datetime):
        return value.isoformat()
    if is_dataclass(value) and not isinstance(value, type):
        return {field.name: _payload_value(getattr(value, field.name)) for field in fields(value)}
    if isinstance(value, tuple):
        return [_payload_value(item) for item in value]
    if isinstance(value, list):
        return [_payload_value(item) for item in value]
    if isinstance(value, dict):
        return {str(key): _payload_value(item) for key, item in value.items()}
    return value


def _as_utc(field_name: str, value: datetime) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


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


def _require_positive_whole_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_positive_decimal(field_name, value)
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{field_name} must be a whole count")
    return normalized


def _require_nonnegative_whole_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_nonnegative_decimal(field_name, value)
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{field_name} must be a whole count")
    return normalized


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


def _require_optional_canonical_string(field_name: str, value: object) -> str | None:
    if value is None:
        return None
    _require_canonical_string(field_name, value)
    return value


def _require_enum(field_name: str, value: object, allowed: tuple[str, ...]) -> None:
    if type(value) is not str or value not in allowed:
        raise ValueError(f"{field_name} must be one of {allowed}")


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


def _require_reason_code(field_name: str, value: object) -> None:
    _require_canonical_string(field_name, value)
    allowed = "abcdefghijklmnopqrstuvwxyz0123456789_"
    if any(character not in allowed for character in value):
        raise ValueError(f"{field_name} must contain deterministic code text")


def _require_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in STATUSES:
        raise ValueError(f"{field_name} must be a known status")


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if _field_value(value, field_name) is not True:
            raise ValueError(f"{label} {field_name} must be True")
