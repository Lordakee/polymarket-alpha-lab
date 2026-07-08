"""Pure report-only reducer for aggregate source signal collection gaps."""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable
from dataclasses import asdict, dataclass, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
import json
import re
from typing import Any


DEFAULT_RESEARCH_SOURCE_SIGNAL_COLLECTION_GAP_REPORT_CONFIG_VERSION = (
    "source-signal-collection-gap-report-v0"
)

QUANTUM = Decimal("0.000001")
COUNT_QUANTUM = Decimal("1")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)

DEFAULT_REQUIRED_DOMAIN_KEYS = ("authority", "event", "resolution")
STATUSES = ("pass", "watch", "block")
STATUS_RANK = {
    "block": Decimal("0"),
    "watch": Decimal("1"),
    "pass": Decimal("2"),
}

PASS_REASON = "source_signal_collection_gap_passed"
REASON_CODE_ORDER = (
    "source_signal_collection_authority_gap_block",
    "source_signal_collection_authority_gap_watch",
    "source_signal_collection_freshness_gap_block",
    "source_signal_collection_freshness_gap_watch",
    "source_signal_collection_independence_gap_block",
    "source_signal_collection_independence_gap_watch",
    "source_signal_collection_corroboration_gap_block",
    "source_signal_collection_corroboration_gap_watch",
    "source_signal_collection_contradiction_exposure_block",
    "source_signal_collection_contradiction_exposure_watch",
    "source_signal_collection_domain_coverage_gap_block",
    "source_signal_collection_domain_coverage_gap_watch",
    "source_signal_collection_gap_block",
    "source_signal_collection_gap_watch",
    PASS_REASON,
)

PUBLIC_IDENTIFIER_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,127}$")
DIGEST_RE = re.compile(r"^[0-9a-f]{64}$")
UNSAFE_PUBLIC_FRAGMENTS = (
    "://",
    "www.",
    "raw",
    "url",
    "source_text",
    "candidate",
    "market_id",
    "market_slug",
    "slug",
    "question",
    "dsn",
    "table",
    "wallet",
    "order",
    "network",
    "database",
    "token",
    "auth_token",
    "authentication",
    "authorization",
    "credential",
    "secret",
    "password",
    "private_key",
    "api_key",
    "trade",
    "trading",
)


@dataclass(frozen=True)
class ResearchSourceSignalCollectionGapReportConfig:
    config_version: str = DEFAULT_RESEARCH_SOURCE_SIGNAL_COLLECTION_GAP_REPORT_CONFIG_VERSION
    required_domain_keys: tuple[str, ...] = DEFAULT_REQUIRED_DOMAIN_KEYS
    min_authoritative_signal_count: Decimal = Decimal("1")
    min_authority_score: Decimal = Decimal("0.700000")
    max_fresh_signal_age_seconds: Decimal = Decimal("7200.000000")
    min_independent_family_count: Decimal = Decimal("2")
    min_corroborating_signal_count: Decimal = Decimal("2")
    watch_collection_gap_score: Decimal = Decimal("0.350000")
    block_collection_gap_score: Decimal = Decimal("0.700000")
    watch_contradiction_exposure: Decimal = Decimal("0.350000")
    block_contradiction_exposure: Decimal = Decimal("0.700000")
    authority_gap_weight: Decimal = Decimal("0.200000")
    freshness_gap_weight: Decimal = Decimal("0.200000")
    independence_gap_weight: Decimal = Decimal("0.200000")
    corroboration_gap_weight: Decimal = Decimal("0.150000")
    contradiction_exposure_weight: Decimal = Decimal("0.150000")
    domain_coverage_gap_weight: Decimal = Decimal("0.100000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchSourceSignalCollectionGapReportConfig:
            raise TypeError(
                "ResearchSourceSignalCollectionGapReportConfig does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchSourceSignalCollectionGapReportConfig:
            raise ValueError(
                "config must be exactly ResearchSourceSignalCollectionGapReportConfig",
            )
        if (
            self.config_version
            != DEFAULT_RESEARCH_SOURCE_SIGNAL_COLLECTION_GAP_REPORT_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        _require_public_identifier("config_version", self.config_version)
        object.__setattr__(
            self,
            "required_domain_keys",
            _normalize_required_domain_keys(self.required_domain_keys),
        )
        for field_name in (
            "min_authoritative_signal_count",
            "min_independent_family_count",
            "min_corroborating_signal_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_positive_count(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "max_fresh_signal_age_seconds",
            _normalize_positive_decimal(
                "max_fresh_signal_age_seconds",
                self.max_fresh_signal_age_seconds,
            ),
        )
        for field_name in (
            "min_authority_score",
            "watch_collection_gap_score",
            "block_collection_gap_score",
            "watch_contradiction_exposure",
            "block_contradiction_exposure",
            "authority_gap_weight",
            "freshness_gap_weight",
            "independence_gap_weight",
            "corroboration_gap_weight",
            "contradiction_exposure_weight",
            "domain_coverage_gap_weight",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        if self.block_collection_gap_score <= self.watch_collection_gap_score:
            raise ValueError(
                "block_collection_gap_score must exceed watch_collection_gap_score",
            )
        if self.block_contradiction_exposure <= self.watch_contradiction_exposure:
            raise ValueError(
                "block_contradiction_exposure must exceed watch_contradiction_exposure",
            )
        if (
            self.authority_gap_weight
            + self.freshness_gap_weight
            + self.independence_gap_weight
            + self.corroboration_gap_weight
            + self.contradiction_exposure_weight
            + self.domain_coverage_gap_weight
        ) != ONE:
            raise ValueError("weights must sum to one")
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class ResearchSourceSignalCollectionObservation:
    collection_scope_id: str
    authority_tier: str
    family_key: str
    domain_key: str
    observed_at: datetime
    authority_score: Decimal
    corroborates_scope: bool
    contradiction_exposure: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchSourceSignalCollectionObservation:
            raise TypeError(
                "ResearchSourceSignalCollectionObservation does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchSourceSignalCollectionObservation:
            raise ValueError(
                "observation must be exactly ResearchSourceSignalCollectionObservation",
            )
        _require_public_identifier("collection_scope_id", self.collection_scope_id)
        _require_public_identifier("authority_tier", self.authority_tier)
        _require_public_identifier("family_key", self.family_key)
        _require_public_identifier("domain_key", self.domain_key)
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        object.__setattr__(
            self,
            "authority_score",
            _normalize_probability("authority_score", self.authority_score),
        )
        if type(self.corroborates_scope) is not bool:
            raise ValueError("corroborates_scope must be a bool")
        object.__setattr__(
            self,
            "contradiction_exposure",
            _normalize_probability(
                "contradiction_exposure",
                self.contradiction_exposure,
            ),
        )
        _require_hard_flags("observation", self)


@dataclass(frozen=True)
class ResearchSourceSignalCollectionGapReportRow:
    collection_scope_id: str
    signal_count: Decimal
    authoritative_signal_count: Decimal
    fresh_signal_count: Decimal
    independent_family_count: Decimal
    corroborating_signal_count: Decimal
    covered_domain_count: Decimal
    authority_gap_ratio: Decimal
    freshness_gap_ratio: Decimal
    independence_gap_ratio: Decimal
    corroboration_gap_ratio: Decimal
    contradiction_exposure: Decimal
    domain_coverage_ratio: Decimal
    domain_coverage_gap_ratio: Decimal
    collection_gap_score: Decimal
    max_signal_age_seconds: Decimal
    status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchSourceSignalCollectionGapReportRow:
            raise TypeError(
                "ResearchSourceSignalCollectionGapReportRow does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchSourceSignalCollectionGapReportRow:
            raise ValueError("row must be exactly ResearchSourceSignalCollectionGapReportRow")
        _require_public_identifier("collection_scope_id", self.collection_scope_id)
        for field_name in (
            "signal_count",
            "authoritative_signal_count",
            "fresh_signal_count",
            "independent_family_count",
            "corroborating_signal_count",
            "covered_domain_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_count(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "authority_gap_ratio",
            "freshness_gap_ratio",
            "independence_gap_ratio",
            "corroboration_gap_ratio",
            "contradiction_exposure",
            "domain_coverage_ratio",
            "domain_coverage_gap_ratio",
            "collection_gap_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "max_signal_age_seconds",
            _normalize_nonnegative_decimal(
                "max_signal_age_seconds",
                self.max_signal_age_seconds,
            ),
        )
        _require_member("status", self.status, STATUSES)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        _require_hard_flags("row", self)


@dataclass(frozen=True)
class ResearchSourceSignalCollectionGapReasonCodeCount:
    reason_code: str
    count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchSourceSignalCollectionGapReasonCodeCount:
            raise TypeError(
                "ResearchSourceSignalCollectionGapReasonCodeCount does not "
                "support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchSourceSignalCollectionGapReasonCodeCount:
            raise ValueError(
                "reason count must be exactly "
                "ResearchSourceSignalCollectionGapReasonCodeCount",
            )
        _require_reason_code("reason_code", self.reason_code)
        object.__setattr__(self, "count", _normalize_positive_count("count", self.count))
        _require_hard_flags("reason count", self)


@dataclass(frozen=True)
class ResearchSourceSignalCollectionGapReport:
    generated_at: datetime
    config_version: str
    scope_count: Decimal
    signal_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    max_collection_gap_score: Decimal
    average_collection_gap_score: Decimal
    max_contradiction_exposure: Decimal
    min_domain_coverage_ratio: Decimal
    status: str
    reason_codes: tuple[str, ...]
    reason_code_counts: tuple[ResearchSourceSignalCollectionGapReasonCodeCount, ...]
    rows: tuple[ResearchSourceSignalCollectionGapReportRow, ...]
    derived_validation_digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchSourceSignalCollectionGapReport:
            raise TypeError(
                "ResearchSourceSignalCollectionGapReport does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchSourceSignalCollectionGapReport:
            raise ValueError("report must be exactly ResearchSourceSignalCollectionGapReport")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_identifier("config_version", self.config_version)
        for field_name in (
            "scope_count",
            "signal_count",
            "pass_count",
            "watch_count",
            "block_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_count(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "max_collection_gap_score",
            "average_collection_gap_score",
            "max_contradiction_exposure",
            "min_domain_coverage_ratio",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        _require_member("status", self.status, STATUSES)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        _require_digest("derived_validation_digest", self.derived_validation_digest)
        _require_hard_flags("report", self)
        _validate_report_consistency(self)
        _verify_report_digest(self)

    @property
    def payload(self) -> dict[str, Any]:
        return research_source_signal_collection_gap_report_payload(self)


def build_research_source_signal_collection_gap_report(
    observations: Iterable[ResearchSourceSignalCollectionObservation],
    *,
    config: ResearchSourceSignalCollectionGapReportConfig,
    generated_at: datetime,
) -> ResearchSourceSignalCollectionGapReport:
    if type(config) is not ResearchSourceSignalCollectionGapReportConfig:
        raise ValueError(
            "config must be exactly ResearchSourceSignalCollectionGapReportConfig",
        )
    generated_at = _as_utc("generated_at", generated_at)
    normalized_observations = _normalize_observations(observations)
    grouped: dict[str, list[ResearchSourceSignalCollectionObservation]] = {}
    for observation in normalized_observations:
        if observation.observed_at > generated_at:
            raise ValueError("observed_at cannot be after generated_at")
        grouped.setdefault(observation.collection_scope_id, []).append(observation)

    rows = tuple(
        sorted(
            (
                _row_from_scope(
                    scope_id,
                    tuple(scope_observations),
                    generated_at=generated_at,
                    config=config,
                )
                for scope_id, scope_observations in grouped.items()
            ),
            key=_row_sort_key,
        ),
    )
    reason_codes = _report_reason_codes(rows)
    reason_code_counts = _reason_code_counts(rows)
    scope_count = _count_decimal(len(rows))
    signal_count = sum((row.signal_count for row in rows), COUNT_QUANTUM * 0)
    pass_count = _count_decimal(sum(1 for row in rows if row.status == "pass"))
    watch_count = _count_decimal(sum(1 for row in rows if row.status == "watch"))
    block_count = _count_decimal(sum(1 for row in rows if row.status == "block"))
    status = _report_status(block_count, watch_count)
    max_gap = max((row.collection_gap_score for row in rows), default=ZERO)
    average_gap = _average_decimal(
        tuple(row.collection_gap_score for row in rows),
        default=ZERO,
    )
    max_contradiction = max((row.contradiction_exposure for row in rows), default=ZERO)
    min_domain_coverage = min((row.domain_coverage_ratio for row in rows), default=ZERO)
    unsigned_payload = _json_ready(
        {
            "generated_at": generated_at,
            "config_version": config.config_version,
            "scope_count": scope_count,
            "signal_count": signal_count,
            "pass_count": pass_count,
            "watch_count": watch_count,
            "block_count": block_count,
            "max_collection_gap_score": max_gap,
            "average_collection_gap_score": average_gap,
            "max_contradiction_exposure": max_contradiction,
            "min_domain_coverage_ratio": min_domain_coverage,
            "status": status,
            "reason_codes": reason_codes,
            "reason_code_counts": reason_code_counts,
            "rows": rows,
            "paper_only": True,
            "report_only": True,
            "readonly": True,
        },
    )
    return ResearchSourceSignalCollectionGapReport(
        generated_at=generated_at,
        config_version=config.config_version,
        scope_count=scope_count,
        signal_count=signal_count,
        pass_count=pass_count,
        watch_count=watch_count,
        block_count=block_count,
        max_collection_gap_score=max_gap,
        average_collection_gap_score=average_gap,
        max_contradiction_exposure=max_contradiction,
        min_domain_coverage_ratio=min_domain_coverage,
        status=status,
        reason_codes=reason_codes,
        reason_code_counts=reason_code_counts,
        rows=rows,
        derived_validation_digest=_digest_payload(unsigned_payload),
        paper_only=True,
        report_only=True,
        readonly=True,
    )


def research_source_signal_collection_gap_report_payload(
    report: ResearchSourceSignalCollectionGapReport,
) -> dict[str, Any]:
    if type(report) is not ResearchSourceSignalCollectionGapReport:
        raise ValueError("report must be exactly ResearchSourceSignalCollectionGapReport")
    payload = _json_ready(asdict(report))
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    validate_research_source_signal_collection_gap_public_payload(payload)
    return payload


def research_source_signal_collection_gap_report_digest(
    report: ResearchSourceSignalCollectionGapReport,
) -> str:
    payload = research_source_signal_collection_gap_report_payload(report)
    digest = payload["derived_validation_digest"]
    if type(digest) is not str:
        raise ValueError("derived_validation_digest must be a string")
    return digest


def validate_research_source_signal_collection_gap_public_payload(
    payload: dict[str, Any],
) -> bool:
    if type(payload) is not dict:
        raise ValueError("payload must be a JSON object")
    _validate_public_payload(payload)
    return True


def _row_from_scope(
    scope_id: str,
    observations: tuple[ResearchSourceSignalCollectionObservation, ...],
    *,
    generated_at: datetime,
    config: ResearchSourceSignalCollectionGapReportConfig,
) -> ResearchSourceSignalCollectionGapReportRow:
    signal_count = _count_decimal(len(observations))
    ages = tuple(_age_seconds(generated_at, item.observed_at) for item in observations)
    max_age = max(ages)
    authoritative_count = _count_decimal(
        sum(1 for item in observations if item.authority_score >= config.min_authority_score),
    )
    fresh_count = _count_decimal(
        sum(1 for age in ages if age <= config.max_fresh_signal_age_seconds),
    )
    independent_count = _count_decimal(len({item.family_key for item in observations}))
    corroborating_count = _count_decimal(
        sum(1 for item in observations if item.corroborates_scope),
    )
    covered_domain_count = _count_decimal(len({item.domain_key for item in observations}))
    required_domain_count = _count_decimal(len(config.required_domain_keys))
    authority_gap = _gap_ratio(config.min_authoritative_signal_count, authoritative_count)
    freshness_gap = _safe_ratio(signal_count - fresh_count, signal_count)
    independence_gap = _gap_ratio(config.min_independent_family_count, independent_count)
    corroboration_gap = _gap_ratio(
        config.min_corroborating_signal_count,
        corroborating_count,
    )
    contradiction_exposure = max(item.contradiction_exposure for item in observations)
    domain_coverage = min(_safe_ratio(covered_domain_count, required_domain_count), ONE)
    domain_coverage_gap = _normalize_probability(
        "domain_coverage_gap_ratio",
        ONE - domain_coverage,
    )
    collection_gap_score = _normalize_probability(
        "collection_gap_score",
        (
            config.authority_gap_weight * authority_gap
            + config.freshness_gap_weight * freshness_gap
            + config.independence_gap_weight * independence_gap
            + config.corroboration_gap_weight * corroboration_gap
            + config.contradiction_exposure_weight * contradiction_exposure
            + config.domain_coverage_gap_weight * domain_coverage_gap
        ),
    )
    reason_codes = _row_reason_codes(
        authoritative_count=authoritative_count,
        fresh_count=fresh_count,
        independent_count=independent_count,
        corroborating_count=corroborating_count,
        covered_domain_count=covered_domain_count,
        contradiction_exposure=contradiction_exposure,
        collection_gap_score=collection_gap_score,
        config=config,
    )
    status = "pass"
    if "source_signal_collection_gap_block" in reason_codes:
        status = "block"
    elif "source_signal_collection_gap_watch" in reason_codes:
        status = "watch"
    return ResearchSourceSignalCollectionGapReportRow(
        collection_scope_id=scope_id,
        signal_count=signal_count,
        authoritative_signal_count=authoritative_count,
        fresh_signal_count=fresh_count,
        independent_family_count=independent_count,
        corroborating_signal_count=corroborating_count,
        covered_domain_count=covered_domain_count,
        authority_gap_ratio=authority_gap,
        freshness_gap_ratio=freshness_gap,
        independence_gap_ratio=independence_gap,
        corroboration_gap_ratio=corroboration_gap,
        contradiction_exposure=contradiction_exposure,
        domain_coverage_ratio=domain_coverage,
        domain_coverage_gap_ratio=domain_coverage_gap,
        collection_gap_score=collection_gap_score,
        max_signal_age_seconds=max_age,
        status=status,
        reason_codes=reason_codes,
        paper_only=True,
        report_only=True,
        readonly=True,
    )


def _row_reason_codes(
    *,
    authoritative_count: Decimal,
    fresh_count: Decimal,
    independent_count: Decimal,
    corroborating_count: Decimal,
    covered_domain_count: Decimal,
    contradiction_exposure: Decimal,
    collection_gap_score: Decimal,
    config: ResearchSourceSignalCollectionGapReportConfig,
) -> tuple[str, ...]:
    reasons: list[str] = []
    has_block = False
    has_watch = False
    if authoritative_count <= COUNT_QUANTUM * 0:
        reasons.append("source_signal_collection_authority_gap_block")
        has_block = True
    elif authoritative_count < config.min_authoritative_signal_count:
        reasons.append("source_signal_collection_authority_gap_watch")
        has_watch = True
    if fresh_count <= COUNT_QUANTUM * 0:
        reasons.append("source_signal_collection_freshness_gap_block")
        has_block = True
    if independent_count <= COUNT_QUANTUM * 0:
        reasons.append("source_signal_collection_independence_gap_block")
        has_block = True
    elif independent_count < config.min_independent_family_count:
        reasons.append("source_signal_collection_independence_gap_watch")
        has_watch = True
    if corroborating_count <= COUNT_QUANTUM * 0:
        reasons.append("source_signal_collection_corroboration_gap_block")
        has_block = True
    elif corroborating_count < config.min_corroborating_signal_count:
        reasons.append("source_signal_collection_corroboration_gap_watch")
        has_watch = True
    if contradiction_exposure >= config.block_contradiction_exposure:
        reasons.append("source_signal_collection_contradiction_exposure_block")
        has_block = True
    elif contradiction_exposure >= config.watch_contradiction_exposure:
        reasons.append("source_signal_collection_contradiction_exposure_watch")
        has_watch = True
    required_domain_count = _count_decimal(len(config.required_domain_keys))
    if covered_domain_count <= COUNT_QUANTUM * 0:
        reasons.append("source_signal_collection_domain_coverage_gap_block")
        has_block = True
    elif covered_domain_count < required_domain_count:
        reasons.append("source_signal_collection_domain_coverage_gap_watch")
        has_watch = True
    if collection_gap_score >= config.block_collection_gap_score:
        has_block = True
    elif collection_gap_score >= config.watch_collection_gap_score:
        has_watch = True
    if has_block:
        reasons.append("source_signal_collection_gap_block")
    elif has_watch:
        reasons.append("source_signal_collection_gap_watch")
    else:
        reasons.append(PASS_REASON)
    return _ordered_reason_codes(reasons)


def _row_sort_key(
    row: ResearchSourceSignalCollectionGapReportRow,
) -> tuple[Decimal, Decimal, str]:
    return (STATUS_RANK[row.status], -row.collection_gap_score, row.collection_scope_id)


def _report_reason_codes(
    rows: tuple[ResearchSourceSignalCollectionGapReportRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return (PASS_REASON,)
    return _ordered_reason_codes(reason for row in rows for reason in row.reason_codes)


def _reason_code_counts(
    rows: tuple[ResearchSourceSignalCollectionGapReportRow, ...],
) -> tuple[ResearchSourceSignalCollectionGapReasonCodeCount, ...]:
    counts = Counter(reason for row in rows for reason in row.reason_codes)
    return tuple(
        ResearchSourceSignalCollectionGapReasonCodeCount(
            reason_code=reason,
            count=_count_decimal(counts[reason]),
        )
        for reason in REASON_CODE_ORDER
        if counts[reason] > 0
    )


def _report_status(block_count: Decimal, watch_count: Decimal) -> str:
    if block_count > COUNT_QUANTUM * 0:
        return "block"
    if watch_count > COUNT_QUANTUM * 0:
        return "watch"
    return "pass"


def _validate_report_consistency(report: ResearchSourceSignalCollectionGapReport) -> None:
    if report.scope_count != _count_decimal(len(report.rows)):
        raise ValueError("scope_count must match row count")
    if report.signal_count != sum((row.signal_count for row in report.rows), COUNT_QUANTUM * 0):
        raise ValueError("signal_count must match rows")
    if report.pass_count != _count_decimal(sum(1 for row in report.rows if row.status == "pass")):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _count_decimal(sum(1 for row in report.rows if row.status == "watch")):
        raise ValueError("watch_count must match rows")
    if report.block_count != _count_decimal(sum(1 for row in report.rows if row.status == "block")):
        raise ValueError("block_count must match rows")
    if report.status != _report_status(report.block_count, report.watch_count):
        raise ValueError("status must match aggregate row statuses")
    if report.max_collection_gap_score != max(
        (row.collection_gap_score for row in report.rows),
        default=ZERO,
    ):
        raise ValueError("max_collection_gap_score must match rows")
    if report.average_collection_gap_score != _average_decimal(
        tuple(row.collection_gap_score for row in report.rows),
        default=ZERO,
    ):
        raise ValueError("average_collection_gap_score must match rows")
    if report.max_contradiction_exposure != max(
        (row.contradiction_exposure for row in report.rows),
        default=ZERO,
    ):
        raise ValueError("max_contradiction_exposure must match rows")
    if report.min_domain_coverage_ratio != min(
        (row.domain_coverage_ratio for row in report.rows),
        default=ZERO,
    ):
        raise ValueError("min_domain_coverage_ratio must match rows")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")


def _verify_report_digest(report: ResearchSourceSignalCollectionGapReport) -> None:
    payload = _json_ready(asdict(report))
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    unsigned_payload = dict(payload)
    unsigned_payload.pop("derived_validation_digest", None)
    if _digest_payload(unsigned_payload) != report.derived_validation_digest:
        raise ValueError("derived_validation_digest does not match report payload")


def _validate_public_payload(payload: dict[str, Any]) -> None:
    _reject_public_numerics(payload)
    _reject_unsafe_public_payload("public payload", payload)
    _require_hard_flags("public payload", _DictFlags(payload))
    digest = payload.get("derived_validation_digest")
    _require_digest("derived_validation_digest", digest)
    unsigned_payload = dict(payload)
    unsigned_payload.pop("derived_validation_digest", None)
    if _digest_payload(unsigned_payload) != digest:
        raise ValueError("derived_validation_digest does not match public payload")


@dataclass(frozen=True)
class _DictFlags:
    value: dict[str, Any]

    @property
    def paper_only(self) -> object:
        return self.value.get("paper_only")

    @property
    def report_only(self) -> object:
        return self.value.get("report_only")

    @property
    def readonly(self) -> object:
        return self.value.get("readonly")


def _normalize_observations(
    observations: Iterable[ResearchSourceSignalCollectionObservation],
) -> tuple[ResearchSourceSignalCollectionObservation, ...]:
    if isinstance(observations, (str, bytes)):
        raise ValueError(
            "observations must be an iterable of "
            "ResearchSourceSignalCollectionObservation",
        )
    normalized: list[ResearchSourceSignalCollectionObservation] = []
    for observation in observations:
        if type(observation) is not ResearchSourceSignalCollectionObservation:
            raise ValueError(
                "observations must contain exactly "
                "ResearchSourceSignalCollectionObservation",
            )
        normalized.append(observation)
    return tuple(normalized)


def _normalize_rows(
    rows: tuple[ResearchSourceSignalCollectionGapReportRow, ...],
) -> tuple[ResearchSourceSignalCollectionGapReportRow, ...]:
    if type(rows) is not tuple:
        raise ValueError("rows must be a tuple")
    for row in rows:
        if type(row) is not ResearchSourceSignalCollectionGapReportRow:
            raise ValueError(
                "rows must contain exactly ResearchSourceSignalCollectionGapReportRow",
            )
    return rows


def _normalize_reason_code_counts(
    reason_code_counts: tuple[ResearchSourceSignalCollectionGapReasonCodeCount, ...],
) -> tuple[ResearchSourceSignalCollectionGapReasonCodeCount, ...]:
    if type(reason_code_counts) is not tuple:
        raise ValueError("reason_code_counts must be a tuple")
    for reason_count in reason_code_counts:
        if type(reason_count) is not ResearchSourceSignalCollectionGapReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain exactly "
                "ResearchSourceSignalCollectionGapReasonCodeCount",
            )
    return reason_code_counts


def _normalize_required_domain_keys(value: object) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ValueError("required_domain_keys must be a tuple")
    if not value:
        raise ValueError("required_domain_keys must be non-empty")
    normalized: list[str] = []
    for domain_key in value:
        normalized.append(_require_public_identifier("required_domain_keys", domain_key))
    if len(set(normalized)) != len(normalized):
        raise ValueError("required_domain_keys must be unique")
    return tuple(normalized)


def _normalize_reason_codes(field_name: str, value: object) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ValueError(f"{field_name} must be a tuple")
    normalized = tuple(_require_reason_code(field_name, reason) for reason in value)
    if len(set(normalized)) != len(normalized):
        raise ValueError(f"{field_name} must be unique")
    return normalized


def _ordered_reason_codes(reasons: Iterable[str]) -> tuple[str, ...]:
    present = frozenset(reasons)
    unknown = present.difference(REASON_CODE_ORDER)
    if unknown:
        raise ValueError("unknown reason code")
    return tuple(reason for reason in REASON_CODE_ORDER if reason in present)


def _require_reason_code(field_name: str, value: object) -> str:
    value = _require_public_identifier(field_name, value)
    if value not in REASON_CODE_ORDER:
        raise ValueError(f"{field_name} must be a supported reason code")
    return value


def _require_public_identifier(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    lowered = value.lower()
    if any(fragment in lowered for fragment in UNSAFE_PUBLIC_FRAGMENTS):
        raise ValueError(f"unsafe public value for {field_name}")
    if not PUBLIC_IDENTIFIER_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a public identifier")
    return value


def _require_member(field_name: str, value: object, allowed_values: tuple[str, ...]) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if value not in allowed_values:
        raise ValueError(f"{field_name} must be one of {allowed_values}")
    return value


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if type(getattr(value, field_name, None)) is not bool:
            raise ValueError(f"{field_name} must be a bool for {label}")
        if getattr(value, field_name) is not True:
            raise ValueError(f"{field_name} must be True for {label}")


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be exactly datetime")
    if value.tzinfo is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    if value.utcoffset() is None:
        raise ValueError(f"{field_name} utcoffset must not be None")
    return value.astimezone(UTC)


def _age_seconds(generated_at: datetime, observed_at: datetime) -> Decimal:
    delta = generated_at - observed_at
    return _normalize_nonnegative_decimal(
        "max_signal_age_seconds",
        Decimal(delta.days * 86400 + delta.seconds)
        + (Decimal(delta.microseconds) / Decimal("1000000")),
    )


def _normalize_probability(field_name: str, value: object) -> Decimal:
    decimal_value = _require_exact_decimal(field_name, value)
    if decimal_value < ZERO or decimal_value > ONE:
        raise ValueError(f"{field_name} must be between zero and one")
    return _quantize(decimal_value, QUANTUM)


def _normalize_positive_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_exact_decimal(field_name, value)
    if decimal_value <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return _quantize(decimal_value, QUANTUM)


def _normalize_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_exact_decimal(field_name, value)
    if decimal_value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return _quantize(decimal_value, QUANTUM)


def _normalize_positive_count(field_name: str, value: object) -> Decimal:
    decimal_value = _require_exact_decimal(field_name, value)
    if decimal_value <= COUNT_QUANTUM * 0:
        raise ValueError(f"{field_name} must be positive")
    return _quantize(decimal_value, COUNT_QUANTUM)


def _normalize_nonnegative_count(field_name: str, value: object) -> Decimal:
    decimal_value = _require_exact_decimal(field_name, value)
    if decimal_value < COUNT_QUANTUM * 0:
        raise ValueError(f"{field_name} must be nonnegative")
    return _quantize(decimal_value, COUNT_QUANTUM)


def _require_exact_decimal(field_name: str, value: object) -> Decimal:
    if not isinstance(value, Decimal):
        raise ValueError(f"{field_name} must be a Decimal")
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be exactly Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return value


def _count_decimal(value: int) -> Decimal:
    return Decimal(value).quantize(COUNT_QUANTUM)


def _average_decimal(values: tuple[Decimal, ...], *, default: Decimal) -> Decimal:
    if not values:
        return default
    with localcontext(DECIMAL_CONTEXT):
        return _quantize(sum(values, ZERO) / _count_decimal(len(values)), QUANTUM)


def _safe_ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == COUNT_QUANTUM * 0:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return _quantize(numerator / denominator, QUANTUM)


def _gap_ratio(required: Decimal, actual: Decimal) -> Decimal:
    if actual >= required:
        return ZERO
    return _safe_ratio(required - actual, required)


def _quantize(value: Decimal, quantum: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(quantum)


def _digest_payload(payload: dict[str, Any]) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    return sha256(encoded).hexdigest()


def _require_digest(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not DIGEST_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a lowercase sha256 hex digest")
    return value


def _json_ready(value: object) -> Any:
    if is_dataclass(value) and not isinstance(value, type):
        return _json_ready(asdict(value))
    if isinstance(value, dict):
        return {str(key): _json_ready(item) for key, item in value.items()}
    if isinstance(value, (tuple, list)):
        return [_json_ready(item) for item in value]
    if type(value) is Decimal:
        return format(value, "f")
    if type(value) is datetime:
        return value.isoformat()
    if type(value) in (str, bool) or value is None:
        return value
    raise ValueError("value is not JSON serializable")


def _reject_public_numerics(value: object) -> None:
    if type(value) in (float, int):
        raise ValueError("public payload numerics must be Decimal-derived strings")
    if isinstance(value, dict):
        for item in value.values():
            _reject_public_numerics(item)
        return
    if isinstance(value, list):
        for item in value:
            _reject_public_numerics(item)


def _reject_unsafe_public_payload(label: str, value: object) -> None:
    if is_dataclass(value) and not isinstance(value, type):
        _reject_unsafe_public_payload(label, asdict(value))
        return
    if type(value) is str:
        lowered = value.lower()
        if any(fragment in lowered for fragment in UNSAFE_PUBLIC_FRAGMENTS):
            raise ValueError(f"unsafe public value in {label}")
        return
    if isinstance(value, dict):
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            lowered_key = key.lower()
            forbidden_keys = (
                "raw",
                "url",
                "source_text",
                "candidate",
                "market_id",
                "market_slug",
                "slug",
                "question",
                "dsn",
                "table",
                "wallet",
                "order",
                "network",
                "database",
                "token",
                "auth_token",
                "authentication",
                "authorization",
                "credential",
                "secret",
                "private_key",
                "api_key",
                "trade",
                "trading",
            )
            if any(fragment in lowered_key for fragment in forbidden_keys):
                raise ValueError(f"unsafe public field in {label}: {key}")
            _reject_unsafe_public_payload(label, item)
        return
    if isinstance(value, list):
        for item in value:
            _reject_unsafe_public_payload(label, item)


__all__ = (
    "DEFAULT_RESEARCH_SOURCE_SIGNAL_COLLECTION_GAP_REPORT_CONFIG_VERSION",
    "STATUSES",
    "ResearchSourceSignalCollectionGapReportConfig",
    "ResearchSourceSignalCollectionObservation",
    "ResearchSourceSignalCollectionGapReportRow",
    "ResearchSourceSignalCollectionGapReasonCodeCount",
    "ResearchSourceSignalCollectionGapReport",
    "build_research_source_signal_collection_gap_report",
    "research_source_signal_collection_gap_report_payload",
    "research_source_signal_collection_gap_report_digest",
    "validate_research_source_signal_collection_gap_public_payload",
)
