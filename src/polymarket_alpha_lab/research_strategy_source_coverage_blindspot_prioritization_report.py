"""Pure report-only reducer for strategy source coverage blindspots."""

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


DEFAULT_RESEARCH_STRATEGY_SOURCE_COVERAGE_BLINDSPOT_PRIORITIZATION_CONFIG_VERSION = (
    "strategy-source-coverage-blindspot-prioritization-report-v0"
)

QUANTUM = Decimal("0.000001")
COUNT_QUANTUM = Decimal("1")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)

STATUSES = ("pass", "watch", "block")
STATUS_RANK = {
    "block": Decimal("0"),
    "watch": Decimal("1"),
    "pass": Decimal("2"),
}
PASS_REASON = "strategy_source_coverage_blindspot_prioritization_passed"
REASON_CODE_ORDER = (
    "missing_source_family_coverage_block",
    "missing_source_family_coverage_watch",
    "corroboration_gap_block",
    "corroboration_gap_watch",
    "source_family_staleness_block",
    "manual_research_priority_block",
    "manual_research_priority_watch",
    PASS_REASON,
)
PUBLIC_IDENTIFIER_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,127}$")
DIGEST_RE = re.compile(r"^[0-9a-f]{64}$")
UNSAFE_PUBLIC_FRAGMENTS = (
    "://",
    "www.",
    "raw",
    "candidate",
    "market_id",
    "slug",
    "question",
    "url",
    "source_text",
    "dsn",
    "table",
    "token",
    "wallet",
    "order",
    "trade",
    "trading",
    "sizing",
    "recommend",
    "database",
    "network",
    "auth",
    "secret",
    "password",
    "private_key",
    "api_key",
)


@dataclass(frozen=True)
class ResearchStrategySourceCoverageBlindspotPrioritizationConfig:
    config_version: str = (
        DEFAULT_RESEARCH_STRATEGY_SOURCE_COVERAGE_BLINDSPOT_PRIORITIZATION_CONFIG_VERSION
    )
    min_family_coverage_ratio: Decimal = Decimal("0.750000")
    block_family_coverage_below_ratio: Decimal = Decimal("0.250000")
    min_corroborating_family_count: Decimal = Decimal("2")
    watch_priority_score: Decimal = Decimal("0.300000")
    block_priority_score: Decimal = Decimal("0.650000")
    max_source_age_seconds: Decimal = Decimal("10800.000000")
    coverage_gap_weight: Decimal = Decimal("0.450000")
    corroboration_gap_weight: Decimal = Decimal("0.350000")
    freshness_gap_weight: Decimal = Decimal("0.200000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchStrategySourceCoverageBlindspotPrioritizationConfig:
            raise TypeError(
                "ResearchStrategySourceCoverageBlindspotPrioritizationConfig does not "
                "support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchStrategySourceCoverageBlindspotPrioritizationConfig:
            raise ValueError(
                "config must be exactly "
                "ResearchStrategySourceCoverageBlindspotPrioritizationConfig",
            )
        if (
            self.config_version
            != DEFAULT_RESEARCH_STRATEGY_SOURCE_COVERAGE_BLINDSPOT_PRIORITIZATION_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        _require_public_identifier("config_version", self.config_version)
        for field_name in (
            "min_family_coverage_ratio",
            "block_family_coverage_below_ratio",
            "watch_priority_score",
            "block_priority_score",
            "coverage_gap_weight",
            "corroboration_gap_weight",
            "freshness_gap_weight",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "min_corroborating_family_count",
            _normalize_positive_count(
                "min_corroborating_family_count",
                self.min_corroborating_family_count,
            ),
        )
        object.__setattr__(
            self,
            "max_source_age_seconds",
            _normalize_positive_decimal(
                "max_source_age_seconds",
                self.max_source_age_seconds,
            ),
        )
        if self.block_family_coverage_below_ratio >= self.min_family_coverage_ratio:
            raise ValueError(
                "block_family_coverage_below_ratio must be below "
                "min_family_coverage_ratio",
            )
        if self.block_priority_score <= self.watch_priority_score:
            raise ValueError("block_priority_score must exceed watch_priority_score")
        if (
            self.coverage_gap_weight
            + self.corroboration_gap_weight
            + self.freshness_gap_weight
        ) != ONE:
            raise ValueError("weights must sum to one")
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class ResearchStrategySourceCoverageBlindspotObservation:
    strategy_lane: str
    source_family: str
    observed_at: datetime
    expected_source_count: Decimal
    covered_source_count: Decimal
    corroborating_family_count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchStrategySourceCoverageBlindspotObservation:
            raise TypeError(
                "ResearchStrategySourceCoverageBlindspotObservation does not support "
                "subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchStrategySourceCoverageBlindspotObservation:
            raise ValueError(
                "observation must be exactly "
                "ResearchStrategySourceCoverageBlindspotObservation",
            )
        _require_public_identifier("strategy_lane", self.strategy_lane)
        _require_public_identifier("source_family", self.source_family)
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        object.__setattr__(
            self,
            "expected_source_count",
            _normalize_positive_count("expected_source_count", self.expected_source_count),
        )
        object.__setattr__(
            self,
            "covered_source_count",
            _normalize_nonnegative_count("covered_source_count", self.covered_source_count),
        )
        object.__setattr__(
            self,
            "corroborating_family_count",
            _normalize_nonnegative_count(
                "corroborating_family_count",
                self.corroborating_family_count,
            ),
        )
        if self.covered_source_count > self.expected_source_count:
            raise ValueError("covered_source_count must not exceed expected_source_count")
        _require_hard_flags("observation", self)


@dataclass(frozen=True)
class ResearchStrategySourceCoverageBlindspotPrioritizationRow:
    strategy_lane: str
    source_family: str
    priority_rank: Decimal
    expected_source_count: Decimal
    covered_source_count: Decimal
    missing_source_count: Decimal
    coverage_ratio: Decimal
    coverage_shortfall_ratio: Decimal
    corroborating_family_count: Decimal
    corroboration_gap_count: Decimal
    corroboration_gap_ratio: Decimal
    source_age_seconds: Decimal
    freshness_gap_ratio: Decimal
    priority_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchStrategySourceCoverageBlindspotPrioritizationRow:
            raise TypeError(
                "ResearchStrategySourceCoverageBlindspotPrioritizationRow does not "
                "support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchStrategySourceCoverageBlindspotPrioritizationRow:
            raise ValueError(
                "row must be exactly "
                "ResearchStrategySourceCoverageBlindspotPrioritizationRow",
            )
        _require_public_identifier("strategy_lane", self.strategy_lane)
        _require_public_identifier("source_family", self.source_family)
        for field_name in (
            "priority_rank",
            "expected_source_count",
            "covered_source_count",
            "missing_source_count",
            "corroborating_family_count",
            "corroboration_gap_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_count(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "source_age_seconds",
            _normalize_nonnegative_decimal("source_age_seconds", self.source_age_seconds),
        )
        for field_name in (
            "coverage_ratio",
            "coverage_shortfall_ratio",
            "corroboration_gap_ratio",
            "freshness_gap_ratio",
            "priority_score",
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
        _require_hard_flags("row", self)


@dataclass(frozen=True)
class ResearchStrategySourceCoverageBlindspotPrioritizationReasonCodeCount:
    reason_code: str
    count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchStrategySourceCoverageBlindspotPrioritizationReasonCodeCount:
            raise TypeError(
                "ResearchStrategySourceCoverageBlindspotPrioritizationReasonCodeCount "
                "does not support subclassing",
            )

    def __post_init__(self) -> None:
        if (
            type(self)
            is not ResearchStrategySourceCoverageBlindspotPrioritizationReasonCodeCount
        ):
            raise ValueError(
                "reason count must be exactly "
                "ResearchStrategySourceCoverageBlindspotPrioritizationReasonCodeCount",
            )
        _require_reason_code("reason_code", self.reason_code)
        object.__setattr__(self, "count", _normalize_positive_count("count", self.count))
        _require_hard_flags("reason count", self)


@dataclass(frozen=True)
class ResearchStrategySourceCoverageBlindspotPrioritizationReport:
    generated_at: datetime
    config_version: str
    observation_count: Decimal
    blindspot_row_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    max_missing_source_count: Decimal
    max_corroboration_gap_count: Decimal
    max_source_age_seconds: Decimal
    max_priority_score: Decimal
    average_priority_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    reason_code_counts: tuple[
        ResearchStrategySourceCoverageBlindspotPrioritizationReasonCodeCount,
        ...,
    ]
    blindspot_rows: tuple[
        ResearchStrategySourceCoverageBlindspotPrioritizationRow,
        ...,
    ]
    derived_validation_digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchStrategySourceCoverageBlindspotPrioritizationReport:
            raise TypeError(
                "ResearchStrategySourceCoverageBlindspotPrioritizationReport does not "
                "support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchStrategySourceCoverageBlindspotPrioritizationReport:
            raise ValueError(
                "report must be exactly "
                "ResearchStrategySourceCoverageBlindspotPrioritizationReport",
            )
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_identifier("config_version", self.config_version)
        for field_name in (
            "observation_count",
            "blindspot_row_count",
            "pass_count",
            "watch_count",
            "block_count",
            "max_missing_source_count",
            "max_corroboration_gap_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_count(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "max_source_age_seconds",
            _normalize_nonnegative_decimal(
                "max_source_age_seconds",
                self.max_source_age_seconds,
            ),
        )
        for field_name in ("max_priority_score", "average_priority_score"):
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
        object.__setattr__(
            self,
            "blindspot_rows",
            _normalize_blindspot_rows(self.blindspot_rows),
        )
        _require_digest("derived_validation_digest", self.derived_validation_digest)
        _require_hard_flags("report", self)
        _verify_report_digest(self)
        _validate_report_consistency(self)

    @property
    def payload(self) -> dict[str, Any]:
        return research_strategy_source_coverage_blindspot_prioritization_payload(self)


def build_research_strategy_source_coverage_blindspot_prioritization_report(
    observations: Iterable[ResearchStrategySourceCoverageBlindspotObservation],
    *,
    config: ResearchStrategySourceCoverageBlindspotPrioritizationConfig,
    generated_at: datetime,
) -> ResearchStrategySourceCoverageBlindspotPrioritizationReport:
    if type(config) is not ResearchStrategySourceCoverageBlindspotPrioritizationConfig:
        raise ValueError(
            "config must be exactly "
            "ResearchStrategySourceCoverageBlindspotPrioritizationConfig",
        )
    generated_at = _as_utc("generated_at", generated_at)
    normalized_observations = _normalize_observations(observations)
    _require_unique_observations(normalized_observations)
    rows = tuple(
        _row_from_observation(
            observation,
            generated_at=generated_at,
            config=config,
        )
        for observation in normalized_observations
    )
    pass_count = _count_decimal(sum(1 for row in rows if row.status == "pass"))
    watch_count = _count_decimal(sum(1 for row in rows if row.status == "watch"))
    block_count = _count_decimal(sum(1 for row in rows if row.status == "block"))
    status = _report_status(block_count, watch_count)
    blindspot_rows = tuple(
        ResearchStrategySourceCoverageBlindspotPrioritizationRow(
            strategy_lane=row.strategy_lane,
            source_family=row.source_family,
            priority_rank=_count_decimal(index),
            expected_source_count=row.expected_source_count,
            covered_source_count=row.covered_source_count,
            missing_source_count=row.missing_source_count,
            coverage_ratio=row.coverage_ratio,
            coverage_shortfall_ratio=row.coverage_shortfall_ratio,
            corroborating_family_count=row.corroborating_family_count,
            corroboration_gap_count=row.corroboration_gap_count,
            corroboration_gap_ratio=row.corroboration_gap_ratio,
            source_age_seconds=row.source_age_seconds,
            freshness_gap_ratio=row.freshness_gap_ratio,
            priority_score=row.priority_score,
            status=row.status,
            reason_codes=row.reason_codes,
            paper_only=True,
            report_only=True,
            readonly=True,
        )
        for index, row in enumerate(
            sorted(
                (row for row in rows if row.status != "pass"),
                key=_row_sort_key,
            ),
            start=1,
        )
    )
    reason_codes = _report_reason_codes(rows)
    reason_code_counts = _reason_code_counts(rows)
    observation_count = _count_decimal(len(rows))
    blindspot_row_count = _count_decimal(len(blindspot_rows))
    max_missing = max(
        (row.missing_source_count for row in blindspot_rows),
        default=COUNT_QUANTUM * 0,
    )
    max_corroboration = max(
        (row.corroboration_gap_count for row in blindspot_rows),
        default=COUNT_QUANTUM * 0,
    )
    max_age = max((row.source_age_seconds for row in blindspot_rows), default=ZERO)
    max_priority = max((row.priority_score for row in blindspot_rows), default=ZERO)
    average_priority = _average_decimal(
        tuple(row.priority_score for row in blindspot_rows),
        default=ZERO,
    )
    unsigned_payload = _json_ready(
        {
            "generated_at": generated_at,
            "config_version": config.config_version,
            "observation_count": observation_count,
            "blindspot_row_count": blindspot_row_count,
            "pass_count": pass_count,
            "watch_count": watch_count,
            "block_count": block_count,
            "max_missing_source_count": max_missing,
            "max_corroboration_gap_count": max_corroboration,
            "max_source_age_seconds": max_age,
            "max_priority_score": max_priority,
            "average_priority_score": average_priority,
            "status": status,
            "reason_codes": reason_codes,
            "reason_code_counts": reason_code_counts,
            "blindspot_rows": blindspot_rows,
            "paper_only": True,
            "report_only": True,
            "readonly": True,
        },
    )
    return ResearchStrategySourceCoverageBlindspotPrioritizationReport(
        generated_at=generated_at,
        config_version=config.config_version,
        observation_count=observation_count,
        blindspot_row_count=blindspot_row_count,
        pass_count=pass_count,
        watch_count=watch_count,
        block_count=block_count,
        max_missing_source_count=max_missing,
        max_corroboration_gap_count=max_corroboration,
        max_source_age_seconds=max_age,
        max_priority_score=max_priority,
        average_priority_score=average_priority,
        status=status,
        reason_codes=reason_codes,
        reason_code_counts=reason_code_counts,
        blindspot_rows=blindspot_rows,
        derived_validation_digest=_digest_payload(unsigned_payload),
        paper_only=True,
        report_only=True,
        readonly=True,
    )


def research_strategy_source_coverage_blindspot_prioritization_payload(
    report: ResearchStrategySourceCoverageBlindspotPrioritizationReport,
) -> dict[str, Any]:
    if type(report) is not ResearchStrategySourceCoverageBlindspotPrioritizationReport:
        raise ValueError(
            "report must be exactly "
            "ResearchStrategySourceCoverageBlindspotPrioritizationReport",
        )
    payload = _json_ready(asdict(report))
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    _validate_public_payload(payload)
    return payload


def research_strategy_source_coverage_blindspot_prioritization_digest(
    report: ResearchStrategySourceCoverageBlindspotPrioritizationReport,
) -> str:
    payload = research_strategy_source_coverage_blindspot_prioritization_payload(report)
    digest = payload["derived_validation_digest"]
    if type(digest) is not str:
        raise ValueError("derived_validation_digest must be a string")
    return digest


def _row_from_observation(
    observation: ResearchStrategySourceCoverageBlindspotObservation,
    *,
    generated_at: datetime,
    config: ResearchStrategySourceCoverageBlindspotPrioritizationConfig,
) -> ResearchStrategySourceCoverageBlindspotPrioritizationRow:
    if observation.observed_at > generated_at:
        raise ValueError("observed_at cannot be after generated_at")
    source_age_seconds = _age_seconds(generated_at, observation.observed_at)
    missing_source_count = observation.expected_source_count - observation.covered_source_count
    coverage_ratio = _safe_ratio(
        observation.covered_source_count,
        observation.expected_source_count,
    )
    coverage_shortfall_ratio = _normalize_probability(
        "coverage_shortfall_ratio",
        ONE - coverage_ratio,
    )
    corroboration_gap_count = max(
        config.min_corroborating_family_count
        - observation.corroborating_family_count,
        COUNT_QUANTUM * 0,
    )
    corroboration_gap_ratio = _safe_ratio(
        corroboration_gap_count,
        config.min_corroborating_family_count,
    )
    freshness_gap_ratio = _freshness_gap_ratio(source_age_seconds, config)
    priority_score = _normalize_probability(
        "priority_score",
        (
            config.coverage_gap_weight * coverage_shortfall_ratio
            + config.corroboration_gap_weight * corroboration_gap_ratio
            + config.freshness_gap_weight * freshness_gap_ratio
        ),
    )
    reason_codes = _row_reason_codes(
        coverage_ratio=coverage_ratio,
        corroboration_gap_count=corroboration_gap_count,
        freshness_gap_ratio=freshness_gap_ratio,
        priority_score=priority_score,
        config=config,
    )
    status = "pass"
    if "manual_research_priority_block" in reason_codes:
        status = "block"
    elif "manual_research_priority_watch" in reason_codes:
        status = "watch"
    return ResearchStrategySourceCoverageBlindspotPrioritizationRow(
        strategy_lane=observation.strategy_lane,
        source_family=observation.source_family,
        priority_rank=COUNT_QUANTUM * 0,
        expected_source_count=observation.expected_source_count,
        covered_source_count=observation.covered_source_count,
        missing_source_count=missing_source_count,
        coverage_ratio=coverage_ratio,
        coverage_shortfall_ratio=coverage_shortfall_ratio,
        corroborating_family_count=observation.corroborating_family_count,
        corroboration_gap_count=corroboration_gap_count,
        corroboration_gap_ratio=corroboration_gap_ratio,
        source_age_seconds=source_age_seconds,
        freshness_gap_ratio=freshness_gap_ratio,
        priority_score=priority_score,
        status=status,
        reason_codes=reason_codes,
        paper_only=True,
        report_only=True,
        readonly=True,
    )


def _row_reason_codes(
    *,
    coverage_ratio: Decimal,
    corroboration_gap_count: Decimal,
    freshness_gap_ratio: Decimal,
    priority_score: Decimal,
    config: ResearchStrategySourceCoverageBlindspotPrioritizationConfig,
) -> tuple[str, ...]:
    reasons: list[str] = []
    has_block = False
    has_watch = False
    if coverage_ratio < config.block_family_coverage_below_ratio:
        reasons.append("missing_source_family_coverage_block")
        has_block = True
    elif coverage_ratio < config.min_family_coverage_ratio:
        reasons.append("missing_source_family_coverage_watch")
        has_watch = True
    if corroboration_gap_count >= config.min_corroborating_family_count:
        reasons.append("corroboration_gap_block")
        has_block = True
    elif corroboration_gap_count > COUNT_QUANTUM * 0:
        reasons.append("corroboration_gap_watch")
        has_watch = True
    if freshness_gap_ratio == ONE:
        reasons.append("source_family_staleness_block")
        has_block = True
    if priority_score >= config.block_priority_score:
        reasons.append("manual_research_priority_block")
        has_block = True
    elif priority_score >= config.watch_priority_score:
        reasons.append("manual_research_priority_watch")
        has_watch = True
    if not has_block and not has_watch:
        reasons.append(PASS_REASON)
    elif has_block and "manual_research_priority_block" not in reasons:
        reasons.append("manual_research_priority_block")
    elif has_watch and "manual_research_priority_watch" not in reasons:
        reasons.append("manual_research_priority_watch")
    return _ordered_reason_codes(reasons)


def _row_sort_key(
    row: ResearchStrategySourceCoverageBlindspotPrioritizationRow,
) -> tuple[Decimal, Decimal, Decimal, Decimal, str, str]:
    return (
        STATUS_RANK[row.status],
        -row.priority_score,
        -row.missing_source_count,
        -row.corroboration_gap_count,
        row.strategy_lane,
        row.source_family,
    )


def _report_reason_codes(
    rows: tuple[ResearchStrategySourceCoverageBlindspotPrioritizationRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return (PASS_REASON,)
    return _ordered_reason_codes(reason for row in rows for reason in row.reason_codes)


def _reason_code_counts(
    rows: tuple[ResearchStrategySourceCoverageBlindspotPrioritizationRow, ...],
) -> tuple[ResearchStrategySourceCoverageBlindspotPrioritizationReasonCodeCount, ...]:
    counts = Counter(reason for row in rows for reason in row.reason_codes)
    return tuple(
        ResearchStrategySourceCoverageBlindspotPrioritizationReasonCodeCount(
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


def _validate_report_consistency(
    report: ResearchStrategySourceCoverageBlindspotPrioritizationReport,
) -> None:
    if report.blindspot_row_count != _count_decimal(len(report.blindspot_rows)):
        raise ValueError("blindspot_row_count must match row count")
    if report.status != _report_status(report.block_count, report.watch_count):
        raise ValueError("status must match aggregate row statuses")
    if report.pass_count + report.watch_count + report.block_count != report.observation_count:
        raise ValueError("status counts must match observation_count")
    if report.blindspot_row_count != report.watch_count + report.block_count:
        raise ValueError("blindspot_row_count must match watch and block counts")
    if report.blindspot_rows:
        if report.max_missing_source_count != max(
            row.missing_source_count for row in report.blindspot_rows
        ):
            raise ValueError("max_missing_source_count must match rows")
        if report.max_corroboration_gap_count != max(
            row.corroboration_gap_count for row in report.blindspot_rows
        ):
            raise ValueError("max_corroboration_gap_count must match rows")
        if report.max_source_age_seconds != max(
            row.source_age_seconds for row in report.blindspot_rows
        ):
            raise ValueError("max_source_age_seconds must match rows")
        if report.max_priority_score != max(
            row.priority_score for row in report.blindspot_rows
        ):
            raise ValueError("max_priority_score must match rows")


def _verify_report_digest(
    report: ResearchStrategySourceCoverageBlindspotPrioritizationReport,
) -> None:
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
    observations: Iterable[ResearchStrategySourceCoverageBlindspotObservation],
) -> tuple[ResearchStrategySourceCoverageBlindspotObservation, ...]:
    if isinstance(observations, (str, bytes)):
        raise ValueError(
            "observations must be an iterable of "
            "ResearchStrategySourceCoverageBlindspotObservation",
        )
    normalized: list[ResearchStrategySourceCoverageBlindspotObservation] = []
    for observation in observations:
        if type(observation) is not ResearchStrategySourceCoverageBlindspotObservation:
            raise ValueError(
                "observations must contain exactly "
                "ResearchStrategySourceCoverageBlindspotObservation",
            )
        normalized.append(observation)
    return tuple(normalized)


def _require_unique_observations(
    observations: tuple[ResearchStrategySourceCoverageBlindspotObservation, ...],
) -> None:
    keys = tuple((observation.strategy_lane, observation.source_family) for observation in observations)
    if len(set(keys)) != len(keys):
        raise ValueError("observations must be unique by strategy_lane and source_family")


def _normalize_blindspot_rows(
    rows: tuple[ResearchStrategySourceCoverageBlindspotPrioritizationRow, ...],
) -> tuple[ResearchStrategySourceCoverageBlindspotPrioritizationRow, ...]:
    if type(rows) is not tuple:
        raise ValueError("blindspot_rows must be a tuple")
    for row in rows:
        if type(row) is not ResearchStrategySourceCoverageBlindspotPrioritizationRow:
            raise ValueError(
                "blindspot_rows must contain exactly "
                "ResearchStrategySourceCoverageBlindspotPrioritizationRow",
            )
    return rows


def _normalize_reason_code_counts(
    reason_code_counts: tuple[
        ResearchStrategySourceCoverageBlindspotPrioritizationReasonCodeCount,
        ...,
    ],
) -> tuple[
    ResearchStrategySourceCoverageBlindspotPrioritizationReasonCodeCount,
    ...,
]:
    if type(reason_code_counts) is not tuple:
        raise ValueError("reason_code_counts must be a tuple")
    for reason_count in reason_code_counts:
        if (
            type(reason_count)
            is not ResearchStrategySourceCoverageBlindspotPrioritizationReasonCodeCount
        ):
            raise ValueError(
                "reason_code_counts must contain exactly "
                "ResearchStrategySourceCoverageBlindspotPrioritizationReasonCodeCount",
            )
    return reason_code_counts


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
        "source_age_seconds",
        Decimal(delta.days * 86400 + delta.seconds)
        + (Decimal(delta.microseconds) / Decimal("1000000")),
    )


def _freshness_gap_ratio(
    source_age_seconds: Decimal,
    config: ResearchStrategySourceCoverageBlindspotPrioritizationConfig,
) -> Decimal:
    if source_age_seconds >= config.max_source_age_seconds:
        return ONE
    return _safe_ratio(source_age_seconds, config.max_source_age_seconds)


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
                "candidate",
                "market_id",
                "slug",
                "question",
                "url",
                "source_text",
                "dsn",
                "table",
                "token",
                "wallet",
                "order",
                "trade",
                "sizing",
                "recommend",
                "database",
                "network",
                "auth",
            )
            if any(fragment in lowered_key for fragment in forbidden_keys):
                raise ValueError(f"unsafe public field in {label}: {key}")
            _reject_unsafe_public_payload(label, item)
        return
    if isinstance(value, list):
        for item in value:
            _reject_unsafe_public_payload(label, item)
