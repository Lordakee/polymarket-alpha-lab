from __future__ import annotations

from dataclasses import FrozenInstanceError, fields, replace
from decimal import Decimal

import pytest

from polymarket_alpha_lab.strategy_event_source_dependency_map_v10 import (
    StrategyEventSourceDependencyClusterV10,
    StrategyEventSourceDependencyMapV10Result,
    StrategyEventSourceDependencyMapV10Source,
    build_strategy_event_source_dependency_map_v10,
    strategy_event_source_dependency_map_v10_payload,
)


def d(value: str) -> Decimal:
    return Decimal(value)


def source(
    *,
    source_id: str = "official_release",
    source_family: str = "official",
    upstream_source_ids: tuple[str, ...] = (),
    reliability_score: Decimal = d("0.950000"),
    freshness_score: Decimal = d("0.900000"),
    confirmation_role: str = "official",
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> StrategyEventSourceDependencyMapV10Source:
    return StrategyEventSourceDependencyMapV10Source(
        source_id=source_id,
        source_family=source_family,
        upstream_source_ids=upstream_source_ids,
        reliability_score=reliability_score,
        freshness_score=freshness_score,
        confirmation_role=confirmation_role,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def field_values(instance):
    return {field.name: getattr(instance, field.name) for field in fields(instance)}


def test_distinct_families_with_official_confirmation_are_independent_readonly():
    result = build_strategy_event_source_dependency_map_v10(
        (
            source(source_id="official_release", source_family="official"),
            source(
                source_id="court_docket",
                source_family="court_records",
                reliability_score=d("0.900000"),
                freshness_score=d("0.850000"),
                confirmation_role="primary",
            ),
            source(
                source_id="local_reporter",
                source_family="local_reporting",
                reliability_score=d("0.800000"),
                freshness_score=d("0.750000"),
                confirmation_role="corroborating",
            ),
        ),
        reason_codes=("research_packet_ready",),
    )

    assert type(result) is StrategyEventSourceDependencyMapV10Result
    assert result.dependency_status == "independent"
    assert result.independent_source_count == d("3.000000")
    assert result.risk_penalty == d("0.000000")
    assert result.reason_codes == (
        "independent_source_quorum_met",
        "official_confirmation_present",
        "no_shared_upstream_dependency",
        "research_packet_ready",
    )
    assert result.paper_only is True
    assert result.report_only is True
    assert result.readonly is True
    assert tuple(cluster.cluster_size for cluster in result.dependency_clusters) == (
        d("1.000000"),
        d("1.000000"),
        d("1.000000"),
    )


def test_shared_upstream_collapses_sources_into_one_dependency_cluster():
    result = build_strategy_event_source_dependency_map_v10(
        (
            source(
                source_id="wire_story",
                source_family="wire",
                reliability_score=d("0.900000"),
                freshness_score=d("0.800000"),
                confirmation_role="primary",
            ),
            source(
                source_id="news_article",
                source_family="news",
                upstream_source_ids=("wire_story",),
                reliability_score=d("0.800000"),
                freshness_score=d("0.700000"),
                confirmation_role="corroborating",
            ),
            source(
                source_id="social_summary",
                source_family="social",
                upstream_source_ids=("wire_story",),
                reliability_score=d("0.700000"),
                freshness_score=d("0.600000"),
                confirmation_role="aggregator",
            ),
        ),
    )

    assert result.dependency_status == "dependency_concentrated"
    assert result.independent_source_count == d("1.000000")
    assert result.risk_penalty >= d("0.500000")
    assert result.reason_codes == (
        "insufficient_independent_sources",
        "shared_upstream_dependency",
        "aggregator_confirmation_present",
        "dependency_concentration_high",
    )
    assert result.dependency_clusters == (
        StrategyEventSourceDependencyClusterV10(
            cluster_id="cluster_1",
            source_ids=("wire_story", "news_article", "social_summary"),
            source_families=("wire", "news", "social"),
            upstream_source_ids=("wire_story",),
            cluster_size=d("3.000000"),
            average_reliability_score=d("0.800000"),
            average_freshness_score=d("0.700000"),
        ),
    )


def test_same_family_sources_count_as_one_independent_source_with_watch_status():
    result = build_strategy_event_source_dependency_map_v10(
        (
            source(
                source_id="paper_a",
                source_family="newswire",
                reliability_score=d("0.900000"),
                freshness_score=d("0.900000"),
                confirmation_role="primary",
            ),
            source(
                source_id="paper_b",
                source_family="newswire",
                reliability_score=d("0.850000"),
                freshness_score=d("0.850000"),
                confirmation_role="corroborating",
            ),
            source(
                source_id="official_notice",
                source_family="official",
                reliability_score=d("0.950000"),
                freshness_score=d("0.900000"),
                confirmation_role="official",
            ),
        ),
    )

    assert result.dependency_status == "dependency_watch"
    assert result.independent_source_count == d("2.000000")
    assert result.risk_penalty > d("0.000000")
    assert "same_family_source_cluster" in result.reason_codes
    assert tuple(cluster.cluster_size for cluster in result.dependency_clusters) == (
        d("2.000000"),
        d("1.000000"),
    )


def test_empty_sources_are_insufficient_and_max_penalty():
    result = build_strategy_event_source_dependency_map_v10(())

    assert result.dependency_status == "insufficient_sources"
    assert result.independent_source_count == d("0.000000")
    assert result.dependency_clusters == ()
    assert result.risk_penalty == d("1.000000")
    assert result.reason_codes == ("no_sources_provided",)


def test_payload_is_json_ready_and_contains_no_decimal_objects():
    result = build_strategy_event_source_dependency_map_v10(
        (
            source(source_id="official_release", source_family="official"),
            source(
                source_id="court_docket",
                source_family="court_records",
                confirmation_role="primary",
            ),
        ),
    )
    payload = strategy_event_source_dependency_map_v10_payload(result)

    assert payload == result.payload
    assert payload["dependency_status"] == "independent"
    assert payload["independent_source_count"] == "2.000000"
    assert payload["risk_penalty"] == "0.000000"
    assert payload["dependency_clusters"][0]["cluster_size"] == "1.000000"
    assert payload["dependency_clusters"][0]["average_reliability_score"] == "0.950000"
    assert payload["reason_codes"] == [
        "independent_source_quorum_met",
        "official_confirmation_present",
        "no_shared_upstream_dependency",
    ]
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert not any(isinstance(value, Decimal) for value in payload.values())
    assert not any(
        isinstance(item, Decimal)
        for cluster in payload["dependency_clusters"]
        for item in cluster.values()
    )


def test_inputs_require_decimal_values_canonical_ids_and_known_roles():
    with pytest.raises(ValueError, match="reliability_score must be a Decimal"):
        source(reliability_score=0.9)
    with pytest.raises(ValueError, match="freshness_score must be between 0 and 1"):
        source(freshness_score=d("1.000001"))
    with pytest.raises(ValueError, match="source_id must be a canonical nonblank string"):
        source(source_id=" bad ")
    with pytest.raises(ValueError, match="confirmation_role must be one of"):
        source(confirmation_role="trading_signal")
    with pytest.raises(ValueError, match="source_id must not contain unsafe live surface text"):
        source(source_id="wallet_reference")
    with pytest.raises(ValueError, match="reason_codes must be a tuple"):
        build_strategy_event_source_dependency_map_v10((), reason_codes=["manual"])


def test_rejects_duplicate_unknown_self_and_cyclic_dependencies():
    with pytest.raises(ValueError, match="source_id values must be unique"):
        build_strategy_event_source_dependency_map_v10(
            (
                source(source_id="duplicate"),
                source(source_id="duplicate", source_family="court_records"),
            ),
        )
    with pytest.raises(ValueError, match="unknown upstream_source_id"):
        build_strategy_event_source_dependency_map_v10(
            (source(source_id="news_article", upstream_source_ids=("wire_story",)),),
        )
    with pytest.raises(ValueError, match="must not depend on itself"):
        build_strategy_event_source_dependency_map_v10(
            (source(source_id="wire_story", upstream_source_ids=("wire_story",)),),
        )
    with pytest.raises(ValueError, match="cyclic upstream dependency"):
        build_strategy_event_source_dependency_map_v10(
            (
                source(source_id="a", source_family="official", upstream_source_ids=("b",)),
                source(source_id="b", source_family="court", upstream_source_ids=("a",)),
            ),
        )


def test_dataclasses_are_frozen_and_require_paper_report_readonly_flags():
    value = source()
    result = build_strategy_event_source_dependency_map_v10((value,))
    rebuilt = StrategyEventSourceDependencyMapV10Result(**field_values(result))

    assert rebuilt == result
    with pytest.raises(FrozenInstanceError):
        value.source_id = "other"
    with pytest.raises(FrozenInstanceError):
        result.dependency_status = "independent"
    with pytest.raises(ValueError, match="paper_only must be True"):
        source(paper_only=False)
    with pytest.raises(ValueError, match="readonly must be True"):
        build_strategy_event_source_dependency_map_v10((source(readonly=False),))


def test_payload_rejects_unsafe_or_non_report_result_objects():
    unsafe = object.__new__(StrategyEventSourceDependencyMapV10Result)
    object.__setattr__(unsafe, "paper_only", False)
    object.__setattr__(unsafe, "report_only", True)
    object.__setattr__(unsafe, "readonly", True)

    with pytest.raises(
        ValueError,
        match="report must be a StrategyEventSourceDependencyMapV10Result",
    ):
        strategy_event_source_dependency_map_v10_payload(object())
    with pytest.raises(ValueError, match="paper_only must be True"):
        strategy_event_source_dependency_map_v10_payload(unsafe)


def test_replace_revalidates_result_shape():
    result = build_strategy_event_source_dependency_map_v10((source(),))

    with pytest.raises(ValueError, match="dependency_status"):
        replace(result, dependency_status="trade_now")
    with pytest.raises(ValueError, match="risk_penalty"):
        replace(result, risk_penalty=d("1.500000"))
