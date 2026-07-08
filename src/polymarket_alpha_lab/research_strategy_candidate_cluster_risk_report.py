"""Pure readonly cluster risk report for research candidates."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal
from hashlib import sha256


DEFAULT_RESEARCH_STRATEGY_CANDIDATE_CLUSTER_RISK_REPORT_CONFIG_VERSION = (
    "research-strategy-candidate-cluster-risk-report-v0"
)

PASS_REASON = "research_strategy_candidate_cluster_risk_passed"
EMPTY_REASON = "research_strategy_candidate_cluster_risk_empty_candidate_set"
DOMAIN_WATCH_REASON = (
    "research_strategy_candidate_cluster_risk_domain_concentration_watch"
)
DOMAIN_BLOCK_REASON = (
    "research_strategy_candidate_cluster_risk_domain_concentration_block"
)
SHARED_WATCH_REASON = "research_strategy_candidate_cluster_risk_shared_catalyst_watch"
SHARED_BLOCK_REASON = "research_strategy_candidate_cluster_risk_shared_catalyst_block"
SOURCE_WATCH_REASON = "research_strategy_candidate_cluster_risk_source_overlap_watch"
SOURCE_BLOCK_REASON = "research_strategy_candidate_cluster_risk_source_overlap_block"
SETTLEMENT_WATCH_REASON = (
    "research_strategy_candidate_cluster_risk_settlement_ambiguity_watch"
)
SETTLEMENT_BLOCK_REASON = (
    "research_strategy_candidate_cluster_risk_settlement_ambiguity_block"
)
LIQUIDITY_WATCH_REASON = "research_strategy_candidate_cluster_risk_liquidity_cost_watch"
LIQUIDITY_BLOCK_REASON = "research_strategy_candidate_cluster_risk_liquidity_cost_block"

STATUSES = ("pass", "watch", "block")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
SIX_PLACES = Decimal("0.000001")
SAFE_MARKERS = ("redacted", "anon", "masked", "synthetic", "sample")
RAW_REFERENCE_MARKERS = (
    "0x",
    "@",
    "market",
    "event",
    "slug",
    "id_",
    "_id",
    "http",
    "www",
    "email",
    "raw",
)
UNSAFE_BUCKET_MARKERS = (
    "0x",
    "@",
    "http",
    "www",
    "raw",
    "slug",
    "li" + "ve",
    "au" + "th",
    "or" + "der",
    "tra" + "de",
    "exec" + "ution",
    "wal" + "let",
    "secret",
    "key",
)


__all__ = (
    "DEFAULT_RESEARCH_STRATEGY_CANDIDATE_CLUSTER_RISK_REPORT_CONFIG_VERSION",
    "ResearchStrategyCandidateClusterRiskAggregate",
    "ResearchStrategyCandidateClusterRiskCandidate",
    "ResearchStrategyCandidateClusterRiskConfig",
    "ResearchStrategyCandidateClusterRiskReasonCodeCount",
    "ResearchStrategyCandidateClusterRiskReport",
    "build_research_strategy_candidate_cluster_risk_report",
    "research_strategy_candidate_cluster_risk_report_payload",
)


@dataclass(frozen=True)
class ResearchStrategyCandidateClusterRiskConfig:
    config_version: str = (
        DEFAULT_RESEARCH_STRATEGY_CANDIDATE_CLUSTER_RISK_REPORT_CONFIG_VERSION
    )
    watch_domain_concentration_ratio: Decimal = Decimal("0.500000")
    block_domain_concentration_ratio: Decimal = Decimal("0.750000")
    watch_shared_catalyst_ratio: Decimal = Decimal("0.500000")
    block_shared_catalyst_ratio: Decimal = Decimal("0.750000")
    watch_source_overlap_ratio: Decimal = Decimal("0.500000")
    block_source_overlap_ratio: Decimal = Decimal("0.750000")
    watch_settlement_ambiguity_score: Decimal = Decimal("0.300000")
    block_settlement_ambiguity_score: Decimal = Decimal("0.600000")
    watch_liquidity_cost_pressure_score: Decimal = Decimal("0.300000")
    block_liquidity_cost_pressure_score: Decimal = Decimal("0.600000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not ResearchStrategyCandidateClusterRiskConfig:
            raise ValueError(
                "config must be exactly ResearchStrategyCandidateClusterRiskConfig",
            )
        _require_canonical_string("config_version", self.config_version)
        _require_public_bucket("config_version", self.config_version)
        for field_name in (
            "watch_domain_concentration_ratio",
            "block_domain_concentration_ratio",
            "watch_shared_catalyst_ratio",
            "block_shared_catalyst_ratio",
            "watch_source_overlap_ratio",
            "block_source_overlap_ratio",
            "watch_settlement_ambiguity_score",
            "block_settlement_ambiguity_score",
            "watch_liquidity_cost_pressure_score",
            "block_liquidity_cost_pressure_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio(field_name, getattr(self, field_name)),
            )
        _require_threshold_pair(
            "domain_concentration_ratio",
            self.watch_domain_concentration_ratio,
            self.block_domain_concentration_ratio,
        )
        _require_threshold_pair(
            "shared_catalyst_ratio",
            self.watch_shared_catalyst_ratio,
            self.block_shared_catalyst_ratio,
        )
        _require_threshold_pair(
            "source_overlap_ratio",
            self.watch_source_overlap_ratio,
            self.block_source_overlap_ratio,
        )
        _require_threshold_pair(
            "settlement_ambiguity_score",
            self.watch_settlement_ambiguity_score,
            self.block_settlement_ambiguity_score,
        )
        _require_threshold_pair(
            "liquidity_cost_pressure_score",
            self.watch_liquidity_cost_pressure_score,
            self.block_liquidity_cost_pressure_score,
        )
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class ResearchStrategyCandidateClusterRiskCandidate:
    candidate_reference: str
    domain_bucket: str
    catalyst_bucket: str
    source_family_buckets: tuple[str, ...]
    settlement_ambiguity_score: Decimal
    liquidity_cost_pressure_score: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not ResearchStrategyCandidateClusterRiskCandidate:
            raise ValueError(
                "candidate must be exactly ResearchStrategyCandidateClusterRiskCandidate",
            )
        _require_canonical_string("candidate_reference", self.candidate_reference)
        _require_public_safe_reference("candidate_reference", self.candidate_reference)
        _require_canonical_string("domain_bucket", self.domain_bucket)
        _require_public_bucket("domain_bucket", self.domain_bucket)
        _require_canonical_string("catalyst_bucket", self.catalyst_bucket)
        _require_public_bucket("catalyst_bucket", self.catalyst_bucket)
        object.__setattr__(
            self,
            "source_family_buckets",
            _normalize_public_buckets(
                "source_family_buckets",
                self.source_family_buckets,
            ),
        )
        object.__setattr__(
            self,
            "settlement_ambiguity_score",
            _require_ratio(
                "settlement_ambiguity_score",
                self.settlement_ambiguity_score,
            ),
        )
        object.__setattr__(
            self,
            "liquidity_cost_pressure_score",
            _require_ratio(
                "liquidity_cost_pressure_score",
                self.liquidity_cost_pressure_score,
            ),
        )
        _require_hard_flags("candidate", self)


@dataclass(frozen=True)
class ResearchStrategyCandidateClusterRiskAggregate:
    dimension_name: str
    metric_value: Decimal
    risk_status: str
    reason_code: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not ResearchStrategyCandidateClusterRiskAggregate:
            raise ValueError(
                "aggregate must be exactly ResearchStrategyCandidateClusterRiskAggregate",
            )
        _require_canonical_string("dimension_name", self.dimension_name)
        _require_public_bucket("dimension_name", self.dimension_name)
        object.__setattr__(
            self,
            "metric_value",
            _require_ratio("metric_value", self.metric_value),
        )
        _require_status("risk_status", self.risk_status)
        _require_reason_code("reason_code", self.reason_code)
        _validate_aggregate_consistency(self)
        _require_hard_flags("aggregate", self)


@dataclass(frozen=True)
class ResearchStrategyCandidateClusterRiskReasonCodeCount:
    reason_code: str
    count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not ResearchStrategyCandidateClusterRiskReasonCodeCount:
            raise ValueError(
                "reason_code_count must be exactly "
                "ResearchStrategyCandidateClusterRiskReasonCodeCount",
            )
        _require_reason_code("reason_code", self.reason_code)
        object.__setattr__(
            self,
            "count",
            _require_positive_count_decimal("count", self.count),
        )
        _require_hard_flags("reason_code_count", self)


@dataclass(frozen=True)
class ResearchStrategyCandidateClusterRiskReport:
    generated_at: datetime
    config_version: str
    cluster_risk_status: str
    candidate_count: Decimal
    pass_dimension_count: Decimal
    watch_dimension_count: Decimal
    block_dimension_count: Decimal
    top_domain_concentration_ratio: Decimal
    top_shared_catalyst_ratio: Decimal
    top_source_overlap_ratio: Decimal
    average_settlement_ambiguity_score: Decimal
    average_liquidity_cost_pressure_score: Decimal
    aggregate_rows: tuple[ResearchStrategyCandidateClusterRiskAggregate, ...]
    reason_code_counts: tuple[ResearchStrategyCandidateClusterRiskReasonCodeCount, ...]
    reason_codes: tuple[str, ...]
    payload_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not ResearchStrategyCandidateClusterRiskReport:
            raise ValueError(
                "report must be exactly ResearchStrategyCandidateClusterRiskReport",
            )
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        _require_public_bucket("config_version", self.config_version)
        _require_status("cluster_risk_status", self.cluster_risk_status)
        for field_name in (
            "candidate_count",
            "pass_dimension_count",
            "watch_dimension_count",
            "block_dimension_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_count_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "top_domain_concentration_ratio",
            "top_shared_catalyst_ratio",
            "top_source_overlap_ratio",
            "average_settlement_ambiguity_score",
            "average_liquidity_cost_pressure_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "aggregate_rows",
            _normalize_aggregate_rows(self.aggregate_rows),
        )
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        _require_canonical_string("payload_digest", self.payload_digest, allow_empty=True)
        _validate_report_consistency(self)
        expected_digest = _payload_digest_for_report(self)
        if self.payload_digest:
            if self.payload_digest != expected_digest:
                raise ValueError("payload_digest must match report payload")
        else:
            object.__setattr__(self, "payload_digest", expected_digest)
        _require_hard_flags("report", self)


def build_research_strategy_candidate_cluster_risk_report(
    candidates: list[ResearchStrategyCandidateClusterRiskCandidate]
    | tuple[ResearchStrategyCandidateClusterRiskCandidate, ...],
    *,
    config: ResearchStrategyCandidateClusterRiskConfig,
    generated_at: datetime,
) -> ResearchStrategyCandidateClusterRiskReport:
    if type(config) is not ResearchStrategyCandidateClusterRiskConfig:
        raise ValueError("config must be a ResearchStrategyCandidateClusterRiskConfig")
    _require_hard_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    normalized_candidates = tuple(
        sorted(
            _normalize_input_candidates(candidates),
            key=lambda row: row.candidate_reference,
        ),
    )
    metric_values = _metric_values(normalized_candidates)
    aggregate_rows = _aggregate_rows(metric_values, config=config)
    reason_codes = _report_reason_codes(normalized_candidates, aggregate_rows)
    cluster_risk_status = _report_status(normalized_candidates, aggregate_rows)

    return ResearchStrategyCandidateClusterRiskReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        cluster_risk_status=cluster_risk_status,
        candidate_count=_count_decimal(len(normalized_candidates)),
        pass_dimension_count=_count_matching(aggregate_rows, "pass"),
        watch_dimension_count=_count_matching(aggregate_rows, "watch"),
        block_dimension_count=_count_matching(aggregate_rows, "block"),
        top_domain_concentration_ratio=metric_values["domain_concentration"],
        top_shared_catalyst_ratio=metric_values["shared_catalyst"],
        top_source_overlap_ratio=metric_values["source_overlap"],
        average_settlement_ambiguity_score=metric_values["settlement_ambiguity"],
        average_liquidity_cost_pressure_score=metric_values["liquidity_cost"],
        aggregate_rows=aggregate_rows,
        reason_code_counts=_reason_code_counts_for_report(
            normalized_candidates,
            aggregate_rows,
        ),
        reason_codes=reason_codes,
    )


def research_strategy_candidate_cluster_risk_report_payload(
    report: ResearchStrategyCandidateClusterRiskReport,
) -> dict[str, object]:
    if type(report) is not ResearchStrategyCandidateClusterRiskReport:
        raise ValueError(
            "report must be a ResearchStrategyCandidateClusterRiskReport",
        )
    _require_hard_flags("report", report)
    _validate_report_consistency(report)
    if report.payload_digest != _payload_digest_for_report(report):
        raise ValueError("payload_digest must match report payload")
    payload = _report_payload_without_digest(report)
    payload["payload_digest"] = report.payload_digest
    payload["paper_only"] = report.paper_only
    payload["report_only"] = report.report_only
    payload["readonly"] = report.readonly
    return payload


def _report_payload_without_digest(
    report: ResearchStrategyCandidateClusterRiskReport,
) -> dict[str, object]:
    return {
        "generated_at": _datetime_payload(report.generated_at),
        "config_version": report.config_version,
        "cluster_risk_status": report.cluster_risk_status,
        "candidate_count": _decimal_payload(report.candidate_count),
        "pass_dimension_count": _decimal_payload(report.pass_dimension_count),
        "watch_dimension_count": _decimal_payload(report.watch_dimension_count),
        "block_dimension_count": _decimal_payload(report.block_dimension_count),
        "top_domain_concentration_ratio": _decimal_payload(
            report.top_domain_concentration_ratio,
        ),
        "top_shared_catalyst_ratio": _decimal_payload(
            report.top_shared_catalyst_ratio,
        ),
        "top_source_overlap_ratio": _decimal_payload(report.top_source_overlap_ratio),
        "average_settlement_ambiguity_score": _decimal_payload(
            report.average_settlement_ambiguity_score,
        ),
        "average_liquidity_cost_pressure_score": _decimal_payload(
            report.average_liquidity_cost_pressure_score,
        ),
        "aggregate_rows": [_aggregate_payload(row) for row in report.aggregate_rows],
        "reason_code_counts": [
            _reason_code_count_payload(row) for row in report.reason_code_counts
        ],
        "reason_codes": list(report.reason_codes),
    }


def _aggregate_payload(
    aggregate: ResearchStrategyCandidateClusterRiskAggregate,
) -> dict[str, object]:
    if type(aggregate) is not ResearchStrategyCandidateClusterRiskAggregate:
        raise ValueError("aggregate must be a ResearchStrategyCandidateClusterRiskAggregate")
    _require_hard_flags("aggregate", aggregate)
    return {
        "dimension_name": aggregate.dimension_name,
        "metric_value": _decimal_payload(aggregate.metric_value),
        "risk_status": aggregate.risk_status,
        "reason_code": aggregate.reason_code,
        "paper_only": aggregate.paper_only,
        "report_only": aggregate.report_only,
        "readonly": aggregate.readonly,
    }


def _reason_code_count_payload(
    count: ResearchStrategyCandidateClusterRiskReasonCodeCount,
) -> dict[str, object]:
    if type(count) is not ResearchStrategyCandidateClusterRiskReasonCodeCount:
        raise ValueError(
            "reason_code_count must be a ResearchStrategyCandidateClusterRiskReasonCodeCount",
        )
    _require_hard_flags("reason_code_count", count)
    return {
        "reason_code": count.reason_code,
        "count": _decimal_payload(count.count),
        "paper_only": count.paper_only,
        "report_only": count.report_only,
        "readonly": count.readonly,
    }


def _metric_values(
    candidates: tuple[ResearchStrategyCandidateClusterRiskCandidate, ...],
) -> dict[str, Decimal]:
    return {
        "domain_concentration": _top_share(tuple(row.domain_bucket for row in candidates)),
        "shared_catalyst": _top_share(tuple(row.catalyst_bucket for row in candidates)),
        "source_overlap": _top_source_share(candidates),
        "settlement_ambiguity": _average(
            tuple(row.settlement_ambiguity_score for row in candidates),
        ),
        "liquidity_cost": _average(
            tuple(row.liquidity_cost_pressure_score for row in candidates),
        ),
    }


def _aggregate_rows(
    metrics: dict[str, Decimal],
    *,
    config: ResearchStrategyCandidateClusterRiskConfig,
) -> tuple[ResearchStrategyCandidateClusterRiskAggregate, ...]:
    return (
        _aggregate_row(
            "domain_concentration",
            metrics["domain_concentration"],
            config.watch_domain_concentration_ratio,
            config.block_domain_concentration_ratio,
            DOMAIN_WATCH_REASON,
            DOMAIN_BLOCK_REASON,
        ),
        _aggregate_row(
            "shared_catalyst",
            metrics["shared_catalyst"],
            config.watch_shared_catalyst_ratio,
            config.block_shared_catalyst_ratio,
            SHARED_WATCH_REASON,
            SHARED_BLOCK_REASON,
        ),
        _aggregate_row(
            "source_overlap",
            metrics["source_overlap"],
            config.watch_source_overlap_ratio,
            config.block_source_overlap_ratio,
            SOURCE_WATCH_REASON,
            SOURCE_BLOCK_REASON,
        ),
        _aggregate_row(
            "settlement_ambiguity",
            metrics["settlement_ambiguity"],
            config.watch_settlement_ambiguity_score,
            config.block_settlement_ambiguity_score,
            SETTLEMENT_WATCH_REASON,
            SETTLEMENT_BLOCK_REASON,
        ),
        _aggregate_row(
            "liquidity_cost_pressure",
            metrics["liquidity_cost"],
            config.watch_liquidity_cost_pressure_score,
            config.block_liquidity_cost_pressure_score,
            LIQUIDITY_WATCH_REASON,
            LIQUIDITY_BLOCK_REASON,
        ),
    )


def _aggregate_row(
    dimension_name: str,
    metric_value: Decimal,
    watch_threshold: Decimal,
    block_threshold: Decimal,
    watch_reason: str,
    block_reason: str,
) -> ResearchStrategyCandidateClusterRiskAggregate:
    risk_status = _metric_status(metric_value, watch_threshold, block_threshold)
    if risk_status == "block":
        reason_code = block_reason
    elif risk_status == "watch":
        reason_code = watch_reason
    else:
        reason_code = PASS_REASON
    return ResearchStrategyCandidateClusterRiskAggregate(
        dimension_name=dimension_name,
        metric_value=metric_value,
        risk_status=risk_status,
        reason_code=reason_code,
    )


def _metric_status(
    metric_value: Decimal,
    watch_threshold: Decimal,
    block_threshold: Decimal,
) -> str:
    if metric_value >= block_threshold:
        return "block"
    if metric_value >= watch_threshold:
        return "watch"
    return "pass"


def _report_status(
    candidates: tuple[ResearchStrategyCandidateClusterRiskCandidate, ...],
    aggregate_rows: tuple[ResearchStrategyCandidateClusterRiskAggregate, ...],
) -> str:
    if not candidates:
        return "watch"
    if any(row.risk_status == "block" for row in aggregate_rows):
        return "block"
    if any(row.risk_status == "watch" for row in aggregate_rows):
        return "watch"
    return "pass"


def _report_reason_codes(
    candidates: tuple[ResearchStrategyCandidateClusterRiskCandidate, ...],
    aggregate_rows: tuple[ResearchStrategyCandidateClusterRiskAggregate, ...],
) -> tuple[str, ...]:
    if not candidates:
        return (EMPTY_REASON,)
    reason_codes = tuple(
        row.reason_code for row in aggregate_rows if row.reason_code != PASS_REASON
    )
    if not reason_codes:
        return (PASS_REASON,)
    return tuple(sorted(set(reason_codes)))


def _reason_code_counts_for_report(
    candidates: tuple[ResearchStrategyCandidateClusterRiskCandidate, ...],
    aggregate_rows: tuple[ResearchStrategyCandidateClusterRiskAggregate, ...],
) -> tuple[ResearchStrategyCandidateClusterRiskReasonCodeCount, ...]:
    if not candidates:
        return _reason_code_counts((EMPTY_REASON,))
    reason_codes = tuple(row.reason_code for row in aggregate_rows)
    if all(reason_code == PASS_REASON for reason_code in reason_codes):
        return _reason_code_counts(reason_codes)
    return _reason_code_counts(
        tuple(reason_code for reason_code in reason_codes if reason_code != PASS_REASON),
    )


def _reason_code_counts(
    reason_codes: tuple[str, ...],
) -> tuple[ResearchStrategyCandidateClusterRiskReasonCodeCount, ...]:
    return tuple(
        ResearchStrategyCandidateClusterRiskReasonCodeCount(
            reason_code=reason_code,
            count=_count_decimal(sum(1 for item in reason_codes if item == reason_code)),
        )
        for reason_code in sorted(set(reason_codes))
    )


def _count_matching(
    aggregate_rows: tuple[ResearchStrategyCandidateClusterRiskAggregate, ...],
    status: str,
) -> Decimal:
    return _count_decimal(sum(1 for row in aggregate_rows if row.risk_status == status))


def _top_share(values: tuple[str, ...]) -> Decimal:
    if not values:
        return ZERO
    counts = tuple(values.count(value) for value in set(values))
    return (Decimal(max(counts)) / Decimal(len(values))).quantize(SIX_PLACES)


def _top_source_share(
    candidates: tuple[ResearchStrategyCandidateClusterRiskCandidate, ...],
) -> Decimal:
    if not candidates:
        return ZERO
    source_families = sorted(
        {
            source_family
            for candidate in candidates
            for source_family in candidate.source_family_buckets
        },
    )
    if not source_families:
        return ZERO
    top_count = max(
        sum(1 for candidate in candidates if source_family in candidate.source_family_buckets)
        for source_family in source_families
    )
    return (Decimal(top_count) / Decimal(len(candidates))).quantize(SIX_PLACES)


def _average(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return ZERO
    return (sum(values, ZERO) / Decimal(len(values))).quantize(SIX_PLACES)


def _normalize_input_candidates(
    candidates: list[ResearchStrategyCandidateClusterRiskCandidate]
    | tuple[ResearchStrategyCandidateClusterRiskCandidate, ...],
) -> tuple[ResearchStrategyCandidateClusterRiskCandidate, ...]:
    if type(candidates) not in (list, tuple):
        raise ValueError("candidates must be a list or tuple")
    normalized_candidates = tuple(candidates)
    seen_references: set[str] = set()
    for candidate in normalized_candidates:
        if type(candidate) is not ResearchStrategyCandidateClusterRiskCandidate:
            raise ValueError(
                "candidates must contain ResearchStrategyCandidateClusterRiskCandidate",
            )
        _require_hard_flags("candidate", candidate)
        if candidate.candidate_reference in seen_references:
            raise ValueError("candidate_reference values must be unique")
        seen_references.add(candidate.candidate_reference)
    return normalized_candidates


def _normalize_aggregate_rows(
    aggregate_rows: tuple[ResearchStrategyCandidateClusterRiskAggregate, ...],
) -> tuple[ResearchStrategyCandidateClusterRiskAggregate, ...]:
    if type(aggregate_rows) not in (list, tuple):
        raise ValueError("aggregate_rows must be a list or tuple")
    rows = tuple(aggregate_rows)
    if len(rows) != 5:
        raise ValueError("aggregate_rows must contain five dimensions")
    expected_dimensions = (
        "domain_concentration",
        "shared_catalyst",
        "source_overlap",
        "settlement_ambiguity",
        "liquidity_cost_pressure",
    )
    for row in rows:
        if type(row) is not ResearchStrategyCandidateClusterRiskAggregate:
            raise ValueError("aggregate_rows must contain aggregate rows")
        _require_hard_flags("aggregate", row)
    if tuple(row.dimension_name for row in rows) != expected_dimensions:
        raise ValueError("aggregate_rows must use the canonical dimension sequence")
    return rows


def _normalize_reason_code_counts(
    reason_code_counts: tuple[ResearchStrategyCandidateClusterRiskReasonCodeCount, ...],
) -> tuple[ResearchStrategyCandidateClusterRiskReasonCodeCount, ...]:
    if type(reason_code_counts) not in (list, tuple):
        raise ValueError("reason_code_counts must be a list or tuple")
    counts = tuple(reason_code_counts)
    seen_reason_codes: set[str] = set()
    for count in counts:
        if type(count) is not ResearchStrategyCandidateClusterRiskReasonCodeCount:
            raise ValueError("reason_code_counts must contain reason count rows")
        _require_hard_flags("reason_code_count", count)
        if count.reason_code in seen_reason_codes:
            raise ValueError("reason_code_counts reason_code values must be unique")
        seen_reason_codes.add(count.reason_code)
    if tuple(count.reason_code for count in counts) != tuple(
        sorted(count.reason_code for count in counts),
    ):
        raise ValueError("reason_code_counts must be sorted by reason_code")
    return counts


def _normalize_reason_codes(
    field_name: str,
    reason_codes: tuple[str, ...],
) -> tuple[str, ...]:
    if type(reason_codes) not in (list, tuple):
        raise ValueError(f"{field_name} must be a list or tuple")
    normalized_reason_codes = tuple(reason_codes)
    if not normalized_reason_codes:
        raise ValueError(f"{field_name} is required")
    seen_reason_codes: set[str] = set()
    for reason_code in normalized_reason_codes:
        _require_reason_code(field_name, reason_code)
        if reason_code in seen_reason_codes:
            raise ValueError(f"{field_name} values must be unique")
        seen_reason_codes.add(reason_code)
    if normalized_reason_codes != tuple(sorted(normalized_reason_codes)):
        raise ValueError(f"{field_name} must be sorted")
    return normalized_reason_codes


def _normalize_public_buckets(
    field_name: str,
    values: tuple[str, ...],
) -> tuple[str, ...]:
    if type(values) not in (list, tuple):
        raise ValueError(f"{field_name} must be a list or tuple")
    buckets = tuple(values)
    seen_buckets: set[str] = set()
    for bucket in buckets:
        _require_canonical_string(field_name, bucket)
        _require_public_bucket(field_name, bucket)
        if bucket in seen_buckets:
            raise ValueError(f"{field_name} values must be unique")
        seen_buckets.add(bucket)
    if buckets != tuple(sorted(buckets)):
        raise ValueError(f"{field_name} must be sorted")
    return buckets


def _validate_aggregate_consistency(
    aggregate: ResearchStrategyCandidateClusterRiskAggregate,
) -> None:
    if aggregate.risk_status == "pass":
        expected_reason = PASS_REASON
    elif aggregate.risk_status == "watch":
        expected_reason = _watch_reason_for_dimension(aggregate.dimension_name)
    else:
        expected_reason = _block_reason_for_dimension(aggregate.dimension_name)
    if aggregate.reason_code != expected_reason:
        raise ValueError("aggregate reason_code must match risk_status")


def _validate_report_consistency(
    report: ResearchStrategyCandidateClusterRiskReport,
) -> None:
    if report.candidate_count == ZERO:
        expected_status = "watch"
        expected_reason_codes = (EMPTY_REASON,)
    elif report.block_dimension_count > ZERO:
        expected_status = "block"
        expected_reason_codes = tuple(
            sorted(
                {
                    row.reason_code
                    for row in report.aggregate_rows
                    if row.reason_code != PASS_REASON
                },
            ),
        )
    elif report.watch_dimension_count > ZERO:
        expected_status = "watch"
        expected_reason_codes = tuple(
            sorted(
                {
                    row.reason_code
                    for row in report.aggregate_rows
                    if row.reason_code != PASS_REASON
                },
            ),
        )
    else:
        expected_status = "pass"
        expected_reason_codes = (PASS_REASON,)
    if report.cluster_risk_status != expected_status:
        raise ValueError("cluster_risk_status must match aggregate rows")
    if report.reason_codes != expected_reason_codes:
        raise ValueError("reason_codes must match aggregate rows")
    if report.pass_dimension_count != _count_matching(report.aggregate_rows, "pass"):
        raise ValueError("pass_dimension_count must match aggregate rows")
    if report.watch_dimension_count != _count_matching(report.aggregate_rows, "watch"):
        raise ValueError("watch_dimension_count must match aggregate rows")
    if report.block_dimension_count != _count_matching(report.aggregate_rows, "block"):
        raise ValueError("block_dimension_count must match aggregate rows")
    if report.reason_code_counts != _reason_code_counts_from_report(report):
        raise ValueError("reason_code_counts must match aggregate rows")
    metric_map = {row.dimension_name: row.metric_value for row in report.aggregate_rows}
    if report.top_domain_concentration_ratio != metric_map["domain_concentration"]:
        raise ValueError("top_domain_concentration_ratio must match aggregate rows")
    if report.top_shared_catalyst_ratio != metric_map["shared_catalyst"]:
        raise ValueError("top_shared_catalyst_ratio must match aggregate rows")
    if report.top_source_overlap_ratio != metric_map["source_overlap"]:
        raise ValueError("top_source_overlap_ratio must match aggregate rows")
    if report.average_settlement_ambiguity_score != metric_map["settlement_ambiguity"]:
        raise ValueError("average_settlement_ambiguity_score must match aggregate rows")
    if report.average_liquidity_cost_pressure_score != metric_map["liquidity_cost_pressure"]:
        raise ValueError("average_liquidity_cost_pressure_score must match aggregate rows")


def _reason_code_counts_from_report(
    report: ResearchStrategyCandidateClusterRiskReport,
) -> tuple[ResearchStrategyCandidateClusterRiskReasonCodeCount, ...]:
    if report.candidate_count == ZERO:
        return _reason_code_counts((EMPTY_REASON,))
    if report.reason_codes == (PASS_REASON,):
        return _reason_code_counts(tuple(row.reason_code for row in report.aggregate_rows))
    return _reason_code_counts(
        tuple(
            row.reason_code
            for row in report.aggregate_rows
            if row.reason_code != PASS_REASON
        ),
    )


def _watch_reason_for_dimension(dimension_name: str) -> str:
    mapping = {
        "domain_concentration": DOMAIN_WATCH_REASON,
        "shared_catalyst": SHARED_WATCH_REASON,
        "source_overlap": SOURCE_WATCH_REASON,
        "settlement_ambiguity": SETTLEMENT_WATCH_REASON,
        "liquidity_cost_pressure": LIQUIDITY_WATCH_REASON,
    }
    if dimension_name not in mapping:
        raise ValueError("dimension_name must be a known cluster risk dimension")
    return mapping[dimension_name]


def _block_reason_for_dimension(dimension_name: str) -> str:
    mapping = {
        "domain_concentration": DOMAIN_BLOCK_REASON,
        "shared_catalyst": SHARED_BLOCK_REASON,
        "source_overlap": SOURCE_BLOCK_REASON,
        "settlement_ambiguity": SETTLEMENT_BLOCK_REASON,
        "liquidity_cost_pressure": LIQUIDITY_BLOCK_REASON,
    }
    if dimension_name not in mapping:
        raise ValueError("dimension_name must be a known cluster risk dimension")
    return mapping[dimension_name]


def _payload_digest_for_report(report: ResearchStrategyCandidateClusterRiskReport) -> str:
    encoded = json.dumps(
        _report_payload_without_digest(report),
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return "sha256:" + sha256(encoded).hexdigest()


def _datetime_payload(value: datetime) -> str:
    return _as_utc("generated_at", value).isoformat()


def _decimal_payload(value: Decimal) -> str:
    if type(value) is not Decimal:
        raise ValueError("payload numeric values must be Decimal")
    return format(value, "f")


def _as_utc(field_name: str, value: datetime) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_ratio(field_name: str, value: Decimal) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value < ZERO or decimal_value > ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return decimal_value.quantize(SIX_PLACES)


def _require_decimal(field_name: str, value: Decimal) -> Decimal:
    if type(value) is Decimal:
        if not value.is_finite():
            raise ValueError(f"{field_name} must be finite")
        return value
    if isinstance(value, Decimal):
        raise ValueError(f"{field_name} must be exactly Decimal")
    raise ValueError(f"{field_name} must be a Decimal")


def _count_decimal(value: int) -> Decimal:
    if isinstance(value, bool) or type(value) is not int or value < 0:
        raise ValueError("internal count must be a nonnegative int")
    return Decimal(value).quantize(SIX_PLACES)


def _require_nonnegative_count_decimal(field_name: str, value: Decimal) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return decimal_value.quantize(SIX_PLACES)


def _require_positive_count_decimal(field_name: str, value: Decimal) -> Decimal:
    decimal_value = _require_nonnegative_count_decimal(field_name, value)
    if decimal_value <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return decimal_value


def _require_threshold_pair(
    field_suffix: str,
    watch_threshold: Decimal,
    block_threshold: Decimal,
) -> None:
    if block_threshold <= watch_threshold:
        raise ValueError(f"block_{field_suffix} must exceed watch_{field_suffix}")


def _require_status(field_name: str, value: str) -> None:
    if value not in STATUSES:
        raise ValueError(f"{field_name} must be pass, watch, or block")


def _require_reason_code(field_name: str, value: str) -> None:
    _require_canonical_string(field_name, value)
    _require_public_bucket(field_name, value)
    allowed_reasons = (
        PASS_REASON,
        EMPTY_REASON,
        DOMAIN_WATCH_REASON,
        DOMAIN_BLOCK_REASON,
        SHARED_WATCH_REASON,
        SHARED_BLOCK_REASON,
        SOURCE_WATCH_REASON,
        SOURCE_BLOCK_REASON,
        SETTLEMENT_WATCH_REASON,
        SETTLEMENT_BLOCK_REASON,
        LIQUIDITY_WATCH_REASON,
        LIQUIDITY_BLOCK_REASON,
    )
    if value not in allowed_reasons:
        raise ValueError(f"{field_name} must be a known cluster risk reason")


def _require_canonical_string(
    field_name: str,
    value: str,
    *,
    allow_empty: bool = False,
) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not allow_empty and not value:
        raise ValueError(f"{field_name} is required")
    if value != value.strip() or any(character in value for character in "\n\r\t"):
        raise ValueError(f"{field_name} must be canonical")


def _require_public_safe_reference(field_name: str, value: str) -> None:
    lowered = value.lower()
    if not any(marker in lowered for marker in SAFE_MARKERS):
        raise ValueError(f"{field_name} must be public-safe")
    if any(marker in lowered for marker in RAW_REFERENCE_MARKERS):
        raise ValueError(f"{field_name} must be public-safe")
    _require_public_bucket(field_name, value)


def _require_public_bucket(field_name: str, value: str) -> None:
    lowered = value.lower()
    if any(marker in lowered for marker in UNSAFE_BUCKET_MARKERS):
        raise ValueError(f"unsafe public bucket in {field_name}")


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if getattr(value, field_name) is not True:
            raise ValueError(f"{label} {field_name} must be True")
