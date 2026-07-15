from __future__ import annotations

from dataclasses import is_dataclass
from datetime import UTC, datetime, timedelta
from decimal import Decimal

from polymarket_alpha_lab.forecast_context_readiness_report import (
    ForecastContextReadinessConfig,
    ForecastContextReadinessInput,
    ForecastContextSource,
    build_forecast_context_readiness_report,
)
from polymarket_alpha_lab.information_freshness_refresh_sla_readiness_report import (
    InformationFreshnessRefreshSlaReadinessConfig,
    InformationFreshnessRefreshSlaReadinessItem,
    build_information_freshness_refresh_sla_readiness_report,
)
from polymarket_alpha_lab.manual_decision_go_no_go_gate_report import (
    ManualDecisionGoNoGoGateInput,
    build_manual_decision_go_no_go_gate_report,
)
from polymarket_alpha_lab.market_discovery_candidate_pool import (
    MarketDiscoveryCandidate,
    MarketDiscoveryCandidatePoolConfig,
    build_market_discovery_candidate_pool_readiness_report,
)
from polymarket_alpha_lab.portfolio_probability_event_readiness_report import (
    PortfolioProbabilityEventReadinessConfig,
    PortfolioProbabilityEventReadinessInput,
    build_portfolio_probability_event_readiness_report,
)
from polymarket_alpha_lab.probability_event_cost_adjusted_position_recommendation_report import (
    ProbabilityEventCostAdjustedPositionRecommendationInput,
    build_probability_event_cost_adjusted_position_recommendation_report,
)
from polymarket_alpha_lab.research_source_discovery_coverage_sla_report import (
    ResearchSourceDiscoveryCoverageSlaConfig,
    ResearchSourceDiscoveryCoverageSlaInput,
    build_research_source_discovery_coverage_sla_report,
)


GENERATED_AT = datetime(2026, 7, 12, 12, 0, tzinfo=UTC)
CAPTURED_AT = GENERATED_AT - timedelta(minutes=5)


def d(value: str) -> Decimal:
    return Decimal(value)


def assert_readonly_report(value: object) -> None:
    assert is_dataclass(value)
    assert getattr(value, "paper_only") is True
    assert getattr(value, "report_only") is True
    assert getattr(value, "readonly") is True


def assert_readonly_rows(rows: tuple[object, ...]) -> None:
    for row in rows:
        assert getattr(row, "paper_only") is True
        assert getattr(row, "report_only") is True
        assert getattr(row, "readonly") is True


def test_phase1_strategy_stack_happy_path_supports_manual_screening_flow() -> None:
    candidate_pool = build_market_discovery_candidate_pool_readiness_report(
        (
            MarketDiscoveryCandidate(
                market_id="market-fed-cut-july-2026",
                slug="fed-cut-july-2026",
                question="Will the Fed cut rates by July 2026?",
                category="macro",
                liquidity=d("5000.000000"),
                spread=d("0.015000"),
                end_time=GENERATED_AT + timedelta(days=30),
                data_freshness=d("30.000000"),
            ),
        ),
        config=MarketDiscoveryCandidatePoolConfig(),
        generated_at=GENERATED_AT,
    )
    assert candidate_pool.status == "ready"
    assert candidate_pool.ready_count == d("1.000000")
    assert candidate_pool.rows[0].slug == "fed-cut-july-2026"

    forecast_context = build_forecast_context_readiness_report(
        (
            ForecastContextReadinessInput(
                model_basis="llm_glm_v0",
                market_slug=candidate_pool.rows[0].slug,
                question=candidate_pool.rows[0].question,
                context_captured_at=CAPTURED_AT,
                sources=(
                    ForecastContextSource(
                        source_label="official_rules",
                        source_family="official_rules",
                        citation="official_rules_2026_07_12",
                        published_at=GENERATED_AT - timedelta(hours=2),
                        captured_at=CAPTURED_AT,
                    ),
                    ForecastContextSource(
                        source_label="market_snapshot",
                        source_family="market_data",
                        citation="polymarket_snapshot_2026_07_12_1155z",
                        published_at=GENERATED_AT - timedelta(minutes=10),
                        captured_at=CAPTURED_AT,
                        stance="market_data",
                    ),
                ),
                fallback_path="manual_low_confidence_review",
            ),
        ),
        generated_at=GENERATED_AT,
        config=ForecastContextReadinessConfig(),
    )
    assert forecast_context.status == "pass"
    assert forecast_context.rows[0].market_slug == candidate_pool.rows[0].slug
    assert forecast_context.rows[0].readiness_score == d("1.000000")

    source_coverage = build_research_source_discovery_coverage_sla_report(
        (
            ResearchSourceDiscoveryCoverageSlaInput(
                source_class="official",
                required_source_count=d("1.000000"),
                discovered_source_count=d("1.000000"),
                discovery_freshness_age_seconds=d("300.000000"),
                parse_ready_source_count=d("1.000000"),
                retry_backlog_count=d("0.000000"),
                manual_review_item_count=d("1.000000"),
                manual_review_capacity_count=d("5.000000"),
            ),
            ResearchSourceDiscoveryCoverageSlaInput(
                source_class="corroborating",
                required_source_count=d("1.000000"),
                discovered_source_count=d("1.000000"),
                discovery_freshness_age_seconds=d("120.000000"),
                parse_ready_source_count=d("1.000000"),
                retry_backlog_count=d("0.000000"),
                manual_review_item_count=d("1.000000"),
                manual_review_capacity_count=d("5.000000"),
            ),
        ),
        config=ResearchSourceDiscoveryCoverageSlaConfig(),
        generated_at=GENERATED_AT,
    )
    assert source_coverage.status == "pass"
    assert source_coverage.covered_source_class_count == d("2.000000")
    assert source_coverage.reason_codes == (
        "research_source_discovery_coverage_sla_clear",
    )

    freshness_sla = build_information_freshness_refresh_sla_readiness_report(
        (
            InformationFreshnessRefreshSlaReadinessItem(
                information_id="market-data-snapshot",
                information_surface="market_data",
                age_seconds=d("60.000000"),
                latency_seconds=d("5.000000"),
                upstream_refresh_sla_breached=False,
                required_for_recommendation=True,
            ),
            InformationFreshnessRefreshSlaReadinessItem(
                information_id="source-coverage-packet",
                information_surface="external_evidence",
                age_seconds=d("600.000000"),
                latency_seconds=d("30.000000"),
                upstream_refresh_sla_breached=False,
                required_for_recommendation=True,
            ),
            InformationFreshnessRefreshSlaReadinessItem(
                information_id="forecast-context-packet",
                information_surface="research_packet",
                age_seconds=d("900.000000"),
                latency_seconds=d("60.000000"),
                upstream_refresh_sla_breached=False,
                required_for_recommendation=True,
            ),
        ),
        config=InformationFreshnessRefreshSlaReadinessConfig(
            config_version="phase1-stack-smoke-freshness-v0",
            market_data_stale_after_seconds=d("120.000000"),
            external_evidence_stale_after_seconds=d("3600.000000"),
            research_packet_stale_after_seconds=d("7200.000000"),
            market_data_latency_sla_seconds=d("15.000000"),
            external_evidence_latency_sla_seconds=d("300.000000"),
            research_packet_latency_sla_seconds=d("900.000000"),
        ),
        generated_at=GENERATED_AT,
    )
    assert freshness_sla.readiness_status == "pass"
    assert freshness_sla.recommendation_gate == (
        "allow_report_only_information_freshness_readiness"
    )
    assert freshness_sla.blocking_required_information_count == d("0.000000")

    cost_adjusted_position = (
        build_probability_event_cost_adjusted_position_recommendation_report(
            ProbabilityEventCostAdjustedPositionRecommendationInput(
                event_id="fed-cut-july-2026",
                market_slug=candidate_pool.rows[0].slug,
                outcome_side="yes",
                forecast_probability=d("0.620000"),
                market_probability=d("0.540000"),
                taker_fee_probability=d("0.010000"),
                spread_probability=d("0.012000"),
                slippage_probability=d("0.003000"),
                settlement_delay_days=d("7.000000"),
                annual_capital_charge_probability=d("0.100000"),
                uncertainty_buffer_probability=d("0.020000"),
                manual_fraction_cap_probability=d("0.050000"),
            ),
        )
    )
    assert cost_adjusted_position.readiness_status == "pass"
    assert cost_adjusted_position.market_slug == candidate_pool.rows[0].slug
    assert cost_adjusted_position.recommended_position_fraction_probability == d(
        "0.050000",
    )
    assert cost_adjusted_position.manual_next_step == (
        "document_phase1_readonly_position_boundary"
    )

    portfolio_readiness = build_portfolio_probability_event_readiness_report(
        (
            PortfolioProbabilityEventReadinessInput(
                candidate_id="fed-cut-july-2026-yes",
                outcome_family="fed-july-cut",
                event_category="macro",
                correlation_cluster="fed-rates",
                yes_probability_exposure=d("25.000000"),
                no_probability_exposure=d("0.000000"),
                capital_lockup_usdc=d("10.000000"),
                time_to_resolution_days=d("7.000000"),
                expected_edge=cost_adjusted_position.margin_of_safety_probability,
                exit_liquidity_usdc=d("500.000000"),
            ),
            PortfolioProbabilityEventReadinessInput(
                candidate_id="btc-range-july-2026-no",
                outcome_family="btc-july-range",
                event_category="crypto",
                correlation_cluster="btc-spot",
                yes_probability_exposure=d("0.000000"),
                no_probability_exposure=d("25.000000"),
                capital_lockup_usdc=d("10.000000"),
                time_to_resolution_days=d("7.000000"),
                expected_edge=d("0.030000"),
                exit_liquidity_usdc=d("500.000000"),
            ),
            PortfolioProbabilityEventReadinessInput(
                candidate_id="nba-finals-july-2026-yes",
                outcome_family="nba-finals-july",
                event_category="sports",
                correlation_cluster="nba-playoffs",
                yes_probability_exposure=d("25.000000"),
                no_probability_exposure=d("0.000000"),
                capital_lockup_usdc=d("10.000000"),
                time_to_resolution_days=d("7.000000"),
                expected_edge=d("0.030000"),
                exit_liquidity_usdc=d("500.000000"),
            ),
        ),
        config=PortfolioProbabilityEventReadinessConfig(),
    )
    assert portfolio_readiness.readiness_status == "pass"
    assert portfolio_readiness.manual_next_step == "proceed_with_paper_portfolio_review"
    target_portfolio_row = next(
        row
        for row in portfolio_readiness.rows
        if row.candidate_id == "fed-cut-july-2026-yes"
    )
    assert target_portfolio_row.expected_edge == (
        cost_adjusted_position.margin_of_safety_probability
    )

    manual_go_no_go = build_manual_decision_go_no_go_gate_report(
        ManualDecisionGoNoGoGateInput(
            quality_index_ready=candidate_pool.status == "ready",
            decision_memo_ready=forecast_context.status == "pass",
            review_packet_index_ready=source_coverage.status == "pass",
            operator_safety_ready=freshness_sla.readiness_status == "pass",
            export_manifest_ready=cost_adjusted_position.readiness_status == "pass",
            manual_review_capacity_ready=True,
            liquidity_exit_ready=portfolio_readiness.readiness_status == "pass",
            resolution_rule_clarity_ready=True,
        ),
    )
    assert manual_go_no_go.ready_for_manual_decision is True
    assert manual_go_no_go.go_no_go_band == "go"
    assert manual_go_no_go.ready_ratio == d("1.000000")

    for report in (
        candidate_pool,
        forecast_context,
        source_coverage,
        freshness_sla,
        cost_adjusted_position,
        portfolio_readiness,
        manual_go_no_go,
    ):
        assert_readonly_report(report)

    assert_readonly_rows(candidate_pool.rows)
    assert_readonly_rows(forecast_context.rows)
    assert_readonly_rows(source_coverage.coverage_rows)
    assert_readonly_rows(freshness_sla.rows)
    assert_readonly_rows(portfolio_readiness.rows)
