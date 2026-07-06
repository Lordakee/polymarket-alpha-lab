"""Paper/report-only event source dependency risk mapper v10."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Context, Decimal, localcontext
from typing import Any

from polymarket_alpha_lab.team_paper_guard import (
    json_ready_no_floats,
    reject_unsafe_surface_fields,
    require_paper_only_flags,
)


QUANTUM = Decimal("0.000001")
INTEGER_QUANTUM = Decimal("1")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
TWO = Decimal("2.000000")
THREE = Decimal("3.000000")
DECIMAL_CONTEXT = Context(prec=64)

MIN_INDEPENDENT_SOURCE_QUORUM = TWO
STRONG_INDEPENDENT_SOURCE_QUORUM = THREE
MIN_HEALTHY_SCORE = Decimal("0.700000")
RELIABILITY_WATCH_FLOOR = Decimal("0.800000")
FRESHNESS_WATCH_FLOOR = Decimal("0.700000")

DEPENDENCY_STATUSES = (
    "independent",
    "dependency_watch",
    "dependency_concentrated",
    "insufficient_sources",
)
CONFIRMATION_ROLES = (
    "official",
    "primary",
    "corroborating",
    "aggregator",
    "rumor",
)
UNSAFE_TEXT_FRAGMENTS = (
    "auth",
    "private_key",
    "wallet",
    "account",
    "balance",
    "order_id",
    "orderbook",
    "order_",
    "cancel_order",
    "replace_order",
    "signing",
    "secret",
    "password",
    "passwd",
    "api_key",
    "apikey",
    "access_key",
    "access_token",
    "bearer ",
    "://",
    "@",
)


@dataclass(frozen=True)
class StrategyEventSourceDependencyMapV10Source:
    source_id: str
    source_family: str
    upstream_source_ids: tuple[str, ...]
    reliability_score: Decimal
    freshness_score: Decimal
    confirmation_role: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("source_id", self.source_id)
        _require_canonical_string("source_family", self.source_family)
        object.__setattr__(
            self,
            "upstream_source_ids",
            _normalize_upstream_source_ids(self.upstream_source_ids),
        )
        object.__setattr__(
            self,
            "reliability_score",
            _probability("reliability_score", self.reliability_score),
        )
        object.__setattr__(
            self,
            "freshness_score",
            _probability("freshness_score", self.freshness_score),
        )
        _require_member("confirmation_role", self.confirmation_role, CONFIRMATION_ROLES)
        reject_unsafe_surface_fields("event source dependency source", self)
        require_paper_only_flags("event source dependency source", self)


@dataclass(frozen=True)
class StrategyEventSourceDependencyClusterV10:
    cluster_id: str
    source_ids: tuple[str, ...]
    source_families: tuple[str, ...]
    upstream_source_ids: tuple[str, ...]
    cluster_size: Decimal
    average_reliability_score: Decimal
    average_freshness_score: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("cluster_id", self.cluster_id)
        object.__setattr__(
            self,
            "source_ids",
            _normalize_canonical_string_tuple("source_ids", self.source_ids),
        )
        object.__setattr__(
            self,
            "source_families",
            _normalize_canonical_string_tuple("source_families", self.source_families),
        )
        object.__setattr__(
            self,
            "upstream_source_ids",
            _normalize_canonical_string_tuple(
                "upstream_source_ids",
                self.upstream_source_ids,
            ),
        )
        object.__setattr__(
            self,
            "cluster_size",
            _nonnegative_integer_decimal("cluster_size", self.cluster_size),
        )
        object.__setattr__(
            self,
            "average_reliability_score",
            _probability("average_reliability_score", self.average_reliability_score),
        )
        object.__setattr__(
            self,
            "average_freshness_score",
            _probability("average_freshness_score", self.average_freshness_score),
        )
        if self.cluster_size != _integer_decimal_from_count(len(self.source_ids)):
            raise ValueError("cluster_size must match source_ids")
        reject_unsafe_surface_fields("event source dependency cluster", self)
        require_paper_only_flags("event source dependency cluster", self)


@dataclass(frozen=True)
class StrategyEventSourceDependencyMapV10Result:
    dependency_status: str
    independent_source_count: Decimal
    dependency_clusters: tuple[StrategyEventSourceDependencyClusterV10, ...]
    risk_penalty: Decimal
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_member("dependency_status", self.dependency_status, DEPENDENCY_STATUSES)
        object.__setattr__(
            self,
            "independent_source_count",
            _nonnegative_integer_decimal(
                "independent_source_count",
                self.independent_source_count,
            ),
        )
        object.__setattr__(
            self,
            "dependency_clusters",
            _normalize_dependency_clusters(self.dependency_clusters),
        )
        object.__setattr__(
            self,
            "risk_penalty",
            _probability("risk_penalty", self.risk_penalty),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        _validate_result_shape(self)
        reject_unsafe_surface_fields("event source dependency result", self)
        require_paper_only_flags("event source dependency result", self)

    @property
    def payload(self) -> dict[str, Any]:
        return strategy_event_source_dependency_map_v10_payload(self)


def build_strategy_event_source_dependency_map_v10(
    sources: tuple[StrategyEventSourceDependencyMapV10Source, ...]
    | list[StrategyEventSourceDependencyMapV10Source],
    *,
    reason_codes: tuple[str, ...] = (),
) -> StrategyEventSourceDependencyMapV10Result:
    normalized_sources = _normalize_sources(sources)
    normalized_reason_codes = _normalize_reason_codes("reason_codes", reason_codes)
    if not normalized_sources:
        return StrategyEventSourceDependencyMapV10Result(
            dependency_status="insufficient_sources",
            independent_source_count=ZERO,
            dependency_clusters=(),
            risk_penalty=ONE,
            reason_codes=_dedupe(("no_sources_provided", *normalized_reason_codes)),
        )

    _validate_source_graph(normalized_sources)
    dependency_clusters = _dependency_clusters(normalized_sources)
    independent_source_count = _integer_decimal_from_count(len(dependency_clusters))
    dependency_status = _dependency_status(
        source_count=len(normalized_sources),
        dependency_clusters=dependency_clusters,
        sources=normalized_sources,
    )

    return StrategyEventSourceDependencyMapV10Result(
        dependency_status=dependency_status,
        independent_source_count=independent_source_count,
        dependency_clusters=dependency_clusters,
        risk_penalty=_risk_penalty(
            dependency_status=dependency_status,
            dependency_clusters=dependency_clusters,
            sources=normalized_sources,
        ),
        reason_codes=_reason_codes(
            dependency_status=dependency_status,
            dependency_clusters=dependency_clusters,
            sources=normalized_sources,
            independent_source_count=independent_source_count,
            existing=normalized_reason_codes,
        ),
    )


def strategy_event_source_dependency_map_v10_payload(
    report: StrategyEventSourceDependencyMapV10Result,
) -> dict[str, Any]:
    if type(report) is not StrategyEventSourceDependencyMapV10Result:
        raise ValueError("report must be a StrategyEventSourceDependencyMapV10Result")
    require_paper_only_flags("event source dependency result", report)
    reject_unsafe_surface_fields("event source dependency result", report)
    return json_ready_no_floats(
        {
            "dependency_status": report.dependency_status,
            "independent_source_count": report.independent_source_count,
            "dependency_clusters": tuple(
                {
                    "cluster_id": cluster.cluster_id,
                    "source_ids": cluster.source_ids,
                    "source_families": cluster.source_families,
                    "upstream_source_ids": cluster.upstream_source_ids,
                    "cluster_size": cluster.cluster_size,
                    "average_reliability_score": cluster.average_reliability_score,
                    "average_freshness_score": cluster.average_freshness_score,
                    "paper_only": cluster.paper_only,
                    "report_only": cluster.report_only,
                    "readonly": cluster.readonly,
                }
                for cluster in report.dependency_clusters
            ),
            "risk_penalty": report.risk_penalty,
            "reason_codes": report.reason_codes,
            "paper_only": report.paper_only,
            "report_only": report.report_only,
            "readonly": report.readonly,
        },
    )


def _dependency_clusters(
    sources: tuple[StrategyEventSourceDependencyMapV10Source, ...],
) -> tuple[StrategyEventSourceDependencyClusterV10, ...]:
    adjacency: dict[str, set[str]] = {source.source_id: set() for source in sources}
    by_family: dict[str, list[str]] = {}
    for source in sources:
        by_family.setdefault(source.source_family, []).append(source.source_id)
        for upstream_source_id in source.upstream_source_ids:
            adjacency[source.source_id].add(upstream_source_id)
            adjacency[upstream_source_id].add(source.source_id)

    for family_source_ids in by_family.values():
        if len(family_source_ids) <= 1:
            continue
        anchor = family_source_ids[0]
        for source_id in family_source_ids[1:]:
            adjacency[anchor].add(source_id)
            adjacency[source_id].add(anchor)

    source_by_id = {source.source_id: source for source in sources}
    visited: set[str] = set()
    clusters: list[StrategyEventSourceDependencyClusterV10] = []
    source_order = {source.source_id: index for index, source in enumerate(sources)}

    for source in sources:
        if source.source_id in visited:
            continue
        component = _connected_component(source.source_id, adjacency, visited)
        ordered_component = tuple(sorted(component, key=lambda item: source_order[item]))
        component_sources = tuple(source_by_id[source_id] for source_id in ordered_component)
        clusters.append(
            StrategyEventSourceDependencyClusterV10(
                cluster_id=f"cluster_{len(clusters) + 1}",
                source_ids=ordered_component,
                source_families=_unique(
                    tuple(item.source_family for item in component_sources),
                ),
                upstream_source_ids=_unique(
                    tuple(
                        upstream_source_id
                        for item in component_sources
                        for upstream_source_id in item.upstream_source_ids
                    ),
                ),
                cluster_size=_integer_decimal_from_count(len(component_sources)),
                average_reliability_score=_average_probability(
                    tuple(item.reliability_score for item in component_sources),
                ),
                average_freshness_score=_average_probability(
                    tuple(item.freshness_score for item in component_sources),
                ),
            ),
        )
    return tuple(clusters)


def _connected_component(
    start_source_id: str,
    adjacency: dict[str, set[str]],
    visited: set[str],
) -> tuple[str, ...]:
    stack = [start_source_id]
    component: list[str] = []
    while stack:
        source_id = stack.pop()
        if source_id in visited:
            continue
        visited.add(source_id)
        component.append(source_id)
        stack.extend(adjacency[source_id] - visited)
    return tuple(component)


def _dependency_status(
    *,
    source_count: int,
    dependency_clusters: tuple[StrategyEventSourceDependencyClusterV10, ...],
    sources: tuple[StrategyEventSourceDependencyMapV10Source, ...],
) -> str:
    independent_source_count = _integer_decimal_from_count(len(dependency_clusters))
    if source_count == 0 or (
        source_count == 1 and independent_source_count < MIN_INDEPENDENT_SOURCE_QUORUM
    ):
        return "insufficient_sources"
    if independent_source_count < MIN_INDEPENDENT_SOURCE_QUORUM:
        return "dependency_concentrated"
    if _has_dependency_cluster(dependency_clusters):
        return "dependency_watch"
    if _has_official_confirmation(sources):
        return "independent"
    return "dependency_watch"


def _risk_penalty(
    *,
    dependency_status: str,
    dependency_clusters: tuple[StrategyEventSourceDependencyClusterV10, ...],
    sources: tuple[StrategyEventSourceDependencyMapV10Source, ...],
) -> Decimal:
    if dependency_status == "independent":
        return ZERO
    if dependency_status == "insufficient_sources" and not sources:
        return ONE

    independent_source_count = _integer_decimal_from_count(len(dependency_clusters))
    penalty = ZERO
    if independent_source_count < MIN_INDEPENDENT_SOURCE_QUORUM:
        penalty += Decimal("0.500000")
    elif independent_source_count < STRONG_INDEPENDENT_SOURCE_QUORUM:
        penalty += Decimal("0.150000")
    if _has_shared_upstream_dependency(dependency_clusters):
        penalty += Decimal("0.250000")
    if _has_same_family_cluster(dependency_clusters):
        penalty += Decimal("0.150000")
    if _has_aggregator_confirmation(sources):
        penalty += Decimal("0.100000")
    penalty += _score_gap_penalty(
        tuple(source.reliability_score for source in sources),
        RELIABILITY_WATCH_FLOOR,
        Decimal("0.250000"),
    )
    penalty += _score_gap_penalty(
        tuple(source.freshness_score for source in sources),
        FRESHNESS_WATCH_FLOOR,
        Decimal("0.200000"),
    )
    return _cap_probability(penalty)


def _reason_codes(
    *,
    dependency_status: str,
    dependency_clusters: tuple[StrategyEventSourceDependencyClusterV10, ...],
    sources: tuple[StrategyEventSourceDependencyMapV10Source, ...],
    independent_source_count: Decimal,
    existing: tuple[str, ...],
) -> tuple[str, ...]:
    reasons: list[str] = []
    if independent_source_count >= MIN_INDEPENDENT_SOURCE_QUORUM:
        reasons.append("independent_source_quorum_met")
    else:
        reasons.append("insufficient_independent_sources")

    if _has_official_confirmation(sources):
        reasons.append("official_confirmation_present")
    if _has_shared_upstream_dependency(dependency_clusters):
        reasons.append("shared_upstream_dependency")
    elif not _has_dependency_cluster(dependency_clusters):
        reasons.append("no_shared_upstream_dependency")
    if _has_same_family_cluster(dependency_clusters):
        reasons.append("same_family_source_cluster")
    if _has_aggregator_confirmation(sources):
        reasons.append("aggregator_confirmation_present")
    if dependency_status == "dependency_concentrated":
        reasons.append("dependency_concentration_high")
    return _dedupe((*tuple(reasons), *existing))


def _validate_source_graph(
    sources: tuple[StrategyEventSourceDependencyMapV10Source, ...],
) -> None:
    source_ids = tuple(source.source_id for source in sources)
    if len(set(source_ids)) != len(source_ids):
        raise ValueError("source_id values must be unique")
    source_id_set = set(source_ids)
    for source in sources:
        for upstream_source_id in source.upstream_source_ids:
            if upstream_source_id == source.source_id:
                raise ValueError("source must not depend on itself")
            if upstream_source_id not in source_id_set:
                raise ValueError("unknown upstream_source_id")
    _reject_cycles(sources)


def _reject_cycles(
    sources: tuple[StrategyEventSourceDependencyMapV10Source, ...],
) -> None:
    graph = {
        source.source_id: tuple(source.upstream_source_ids)
        for source in sources
    }
    visiting: set[str] = set()
    visited: set[str] = set()

    def visit(source_id: str) -> None:
        if source_id in visited:
            return
        if source_id in visiting:
            raise ValueError("cyclic upstream dependency")
        visiting.add(source_id)
        for upstream_source_id in graph[source_id]:
            visit(upstream_source_id)
        visiting.remove(source_id)
        visited.add(source_id)

    for source_id in graph:
        visit(source_id)


def _score_gap_penalty(
    values: tuple[Decimal, ...],
    floor: Decimal,
    weight: Decimal,
) -> Decimal:
    if not values:
        return ZERO
    minimum_value = min(values)
    if minimum_value >= floor:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return _quantize((floor - minimum_value) * weight)


def _has_dependency_cluster(
    clusters: tuple[StrategyEventSourceDependencyClusterV10, ...],
) -> bool:
    return any(cluster.cluster_size > ONE for cluster in clusters)


def _has_shared_upstream_dependency(
    clusters: tuple[StrategyEventSourceDependencyClusterV10, ...],
) -> bool:
    return any(cluster.upstream_source_ids for cluster in clusters)


def _has_same_family_cluster(
    clusters: tuple[StrategyEventSourceDependencyClusterV10, ...],
) -> bool:
    return any(
        cluster.cluster_size > ONE and len(cluster.source_families) == 1
        for cluster in clusters
    )


def _has_official_confirmation(
    sources: tuple[StrategyEventSourceDependencyMapV10Source, ...],
) -> bool:
    return any(source.confirmation_role == "official" for source in sources)


def _has_aggregator_confirmation(
    sources: tuple[StrategyEventSourceDependencyMapV10Source, ...],
) -> bool:
    return any(source.confirmation_role == "aggregator" for source in sources)


def _normalize_sources(
    value: tuple[StrategyEventSourceDependencyMapV10Source, ...]
    | list[StrategyEventSourceDependencyMapV10Source],
) -> tuple[StrategyEventSourceDependencyMapV10Source, ...]:
    if type(value) not in (tuple, list):
        raise ValueError("sources must be a tuple or list")
    sources = tuple(value)
    for source in sources:
        if type(source) is not StrategyEventSourceDependencyMapV10Source:
            raise ValueError(
                "sources must contain StrategyEventSourceDependencyMapV10Source values",
            )
        require_paper_only_flags("event source dependency source", source)
        reject_unsafe_surface_fields("event source dependency source", source)
    return sources


def _normalize_dependency_clusters(
    value: object,
) -> tuple[StrategyEventSourceDependencyClusterV10, ...]:
    if type(value) is not tuple:
        raise ValueError("dependency_clusters must be a tuple")
    for cluster in value:
        if type(cluster) is not StrategyEventSourceDependencyClusterV10:
            raise ValueError(
                "dependency_clusters must contain StrategyEventSourceDependencyClusterV10 values",
            )
        require_paper_only_flags("event source dependency cluster", cluster)
        reject_unsafe_surface_fields("event source dependency cluster", cluster)
    return value


def _normalize_upstream_source_ids(value: object) -> tuple[str, ...]:
    upstream_source_ids = _normalize_canonical_string_tuple("upstream_source_ids", value)
    if len(set(upstream_source_ids)) != len(upstream_source_ids):
        raise ValueError("upstream_source_ids must be unique")
    return upstream_source_ids


def _normalize_canonical_string_tuple(name: str, value: object) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ValueError(f"{name} must be a tuple")
    for item in value:
        _require_canonical_string(name, item)
    return value


def _normalize_reason_codes(name: str, value: object) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ValueError(f"{name} must be a tuple")
    for reason_code in value:
        _require_canonical_string(name, reason_code)
    return _dedupe(value)


def _dedupe(values: tuple[str, ...]) -> tuple[str, ...]:
    result: list[str] = []
    seen_values: set[str] = set()
    for value in values:
        if value in seen_values:
            continue
        result.append(value)
        seen_values.add(value)
    return tuple(result)


def _unique(values: tuple[str, ...]) -> tuple[str, ...]:
    return _dedupe(values)


def _average_probability(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        raise ValueError("average_probability requires at least one value")
    with localcontext(DECIMAL_CONTEXT):
        return _quantize(sum(values, ZERO) / Decimal(len(values)))


def _probability(name: str, value: object) -> Decimal:
    decimal = _decimal(name, value)
    if decimal < ZERO or decimal > ONE:
        raise ValueError(f"{name} must be between 0 and 1")
    return decimal


def _nonnegative_integer_decimal(name: str, value: object) -> Decimal:
    decimal = _decimal(name, value)
    if decimal < ZERO:
        raise ValueError(f"{name} must be nonnegative")
    if decimal != decimal.quantize(INTEGER_QUANTUM):
        raise ValueError(f"{name} must be an integer Decimal")
    return decimal


def _integer_decimal_from_count(value: int) -> Decimal:
    return _quantize(Decimal(value))


def _decimal(name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{name} must be finite")
    return _quantize(value)


def _quantize(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(QUANTUM)


def _cap_probability(value: Decimal) -> Decimal:
    if value > ONE:
        return ONE
    if value < ZERO:
        return ZERO
    return _quantize(value)


def _validate_result_shape(result: StrategyEventSourceDependencyMapV10Result) -> None:
    if result.independent_source_count != _integer_decimal_from_count(
        len(result.dependency_clusters),
    ):
        raise ValueError("independent_source_count must match dependency_clusters")
    if result.dependency_status == "independent" and result.risk_penalty != ZERO:
        raise ValueError("risk_penalty must be zero when dependency_status is independent")


def _require_member(
    name: str,
    value: object,
    allowed_values: tuple[str, ...],
) -> None:
    if type(value) is not str or value not in allowed_values:
        joined_values = ", ".join(allowed_values)
        raise ValueError(f"{name} must be one of: {joined_values}")


def _require_canonical_string(name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{name} must be a canonical nonblank string")
    if not value or value.strip() != value:
        raise ValueError(f"{name} must be a canonical nonblank string")
    if "\n" in value or "\r" in value or "\t" in value:
        raise ValueError(f"{name} must be a canonical nonblank string")
    _reject_unsafe_text(name, value)


def _reject_unsafe_text(name: str, value: str) -> None:
    normalized = value.lower()
    if any(fragment in normalized for fragment in UNSAFE_TEXT_FRAGMENTS):
        raise ValueError(f"{name} must not contain unsafe live surface text")


__all__ = (
    "StrategyEventSourceDependencyMapV10Source",
    "StrategyEventSourceDependencyClusterV10",
    "StrategyEventSourceDependencyMapV10Result",
    "build_strategy_event_source_dependency_map_v10",
    "strategy_event_source_dependency_map_v10_payload",
)
