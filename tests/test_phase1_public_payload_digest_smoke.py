from __future__ import annotations

import hashlib
import json
from dataclasses import replace
from datetime import UTC, datetime
from decimal import Decimal

import pytest

from polymarket_alpha_lab.manual_operator_packet_final_boundary_report import (
    ManualOperatorPacketFinalBoundaryInput,
    build_manual_operator_packet_final_boundary_report,
    manual_operator_packet_final_boundary_report_payload,
)
from polymarket_alpha_lab.operator_final_go_no_go_packet_readiness_report import (
    OperatorFinalGoNoGoPacketReadinessInput,
    build_operator_final_go_no_go_packet_readiness_report,
    operator_final_go_no_go_packet_readiness_report_payload,
)
from polymarket_alpha_lab.portfolio_probability_event_readiness_report import (
    PortfolioProbabilityEventReadinessConfig,
    PortfolioProbabilityEventReadinessInput,
    build_portfolio_probability_event_readiness_report,
    portfolio_probability_event_readiness_report_payload,
)
from polymarket_alpha_lab.probability_event_cost_adjusted_position_recommendation_report import (
    ProbabilityEventCostAdjustedPositionRecommendationInput,
    build_probability_event_cost_adjusted_position_recommendation_report,
    probability_event_cost_adjusted_position_recommendation_report_payload,
)
from polymarket_alpha_lab.probability_event_screen_supabase_contract_report import (
    ProbabilityEventScreenSupabaseContractInput,
    build_probability_event_screen_supabase_contract_report,
    validate_probability_event_screen_supabase_contract_public_payload,
)
from polymarket_alpha_lab.source_scraping_tool_coverage_readiness_report import (
    SourceScrapingToolCoverageReadinessInput,
    build_source_scraping_tool_coverage_readiness_report,
)
from polymarket_alpha_lab.strategy_fee_adjusted_position_sizing_gate_v2 import (
    StrategyFeeAdjustedPositionSizingGateV2Candidate,
    StrategyFeeAdjustedPositionSizingGateV2Config,
    build_strategy_fee_adjusted_position_sizing_gate_v2_report,
    strategy_fee_adjusted_position_sizing_gate_v2_payload,
)


GENERATED_AT = datetime(2026, 7, 6, 12, 0, tzinfo=UTC)
OBSERVED_AT = datetime(2026, 7, 6, 11, 59, 30, tzinfo=UTC)


def d(value: str) -> Decimal:
    return Decimal(value)


def digest_payload(value: object) -> str:
    return hashlib.sha256(
        json.dumps(
            value,
            ensure_ascii=True,
            separators=(",", ":"),
            sort_keys=True,
        ).encode("utf-8"),
    ).hexdigest()


def audit_entry(
    *,
    entry_id: str = "operator_journal_decision_001",
    previous_entry_digest: str = "0" * 64,
    decision_log_digest: str = "1" * 64,
    reviewer_attestation_digest: str = "2" * 64,
    source_packet_digest: str = "3" * 64,
    public_payload_digest: str = "4" * 64,
) -> dict[str, str]:
    entry = {
        "decision_log_digest": decision_log_digest,
        "entry_id": entry_id,
        "previous_entry_digest": previous_entry_digest,
        "public_payload_digest": public_payload_digest,
        "reviewer_attestation_digest": reviewer_attestation_digest,
        "source_packet_digest": source_packet_digest,
    }
    return {**entry, "entry_digest": digest_payload(entry)}


def test_manual_operator_packet_public_digest_rejects_forged_status_reason_action() -> None:
    report = build_manual_operator_packet_final_boundary_report(
        ManualOperatorPacketFinalBoundaryInput(
            team_owner="macro_rates",
            source_quality_status="pass",
            memory_policy_status="pass",
            forecast_vs_price_edge_status="watch",
            costs_status="pass",
            liquidity_status="pass",
            resolution_risk_status="pass",
            selected_side="yes",
            reason_codes=("forecast_edge_requires_manual_review",),
            manual_next_step="paper_review_check_forecast_edge",
        ),
    )
    payload = manual_operator_packet_final_boundary_report_payload(report)

    for forged in (
        {**payload, "final_status": "pass"},
        {**payload, "reason_codes": ["manual_operator_packet_final_boundary_pass"]},
        {**payload, "manual_next_step": "paper_review_read_final_boundary_report"},
    ):
        with pytest.raises(ValueError, match="derived_validation_digest"):
            manual_operator_packet_final_boundary_report_payload(forged)


def test_operator_final_go_no_go_public_digest_rejects_forged_status_reason_action() -> None:
    report = build_operator_final_go_no_go_packet_readiness_report(
        OperatorFinalGoNoGoPacketReadinessInput(
            all_required_gates_passed=True,
            manual_attestation_present=True,
            latest_packet_digest_present=True,
            cost_recheck_passed=True,
            source_freshness_passed=True,
            memory_policy_passed=True,
            audit_chain_entries=(audit_entry(),),
            expected_source_packet_digest="3" * 64,
            expected_public_payload_digest="4" * 64,
        ),
    )
    payload = operator_final_go_no_go_packet_readiness_report_payload(report)

    for forged in (
        {**payload, "go_no_go_status": "no_go"},
        {**payload, "reason_codes": ["manual_attestation_missing"]},
        {**payload, "manual_next_step": "resolve_blockers_before_final_review"},
    ):
        with pytest.raises(ValueError, match="payload_digest"):
            operator_final_go_no_go_packet_readiness_report_payload(forged)


def test_portfolio_readiness_public_digest_rejects_forged_status_reason_action() -> None:
    report = build_portfolio_probability_event_readiness_report(
        tuple(
            PortfolioProbabilityEventReadinessInput(
                candidate_id=f"candidate-{index}",
                outcome_family=f"outcome-{index}",
                event_category=f"category-{index}",
                correlation_cluster=f"cluster-{index}",
                yes_probability_exposure=d("10.000000"),
                no_probability_exposure=d("0.000000"),
                capital_lockup_usdc=d("10.000000"),
                time_to_resolution_days=d("1.000000"),
                expected_edge=d("0.100000"),
                exit_liquidity_usdc=d("200.000000"),
            )
            for index in range(3)
        ),
        config=PortfolioProbabilityEventReadinessConfig(),
    )
    payload = portfolio_probability_event_readiness_report_payload(report)

    for forged in (
        {**payload, "readiness_status": "blocked"},
        {**payload, "reason_codes": ["same_outcome_dependency_block"]},
        {
            **payload,
            "manual_next_step": "do_not_allocate_until_portfolio_blockers_clear",
        },
    ):
        with pytest.raises(
            ValueError,
            match="payload_digest|readiness_status|reason_codes|manual_next_step",
        ):
            portfolio_probability_event_readiness_report_payload(forged)


def test_source_coverage_public_digest_rejects_forged_status_reason_action() -> None:
    report = build_source_scraping_tool_coverage_readiness_report(
        SourceScrapingToolCoverageReadinessInput(
            agent_reach_available=True,
            scrapling_available=True,
            official_api_available=True,
            browser_capture_available=True,
            source_snapshot_digest_present=True,
            fallback_path_count=d("2"),
            source_freshness_score=d("1.000000"),
            source_family_diversity_score=d("1.000000"),
            capture_completeness_score=d("1.000000"),
        ),
    )

    for field_name, forged_value in (
        ("coverage_status", "blocked"),
        ("reason_codes", ("source_snapshot_digest_missing",)),
        ("manual_next_step", "Add a public source snapshot digest before readiness review."),
    ):
        with pytest.raises(
            ValueError,
            match="payload_digest|coverage_status|reason_codes|manual_next_step",
        ):
            replace(report, **{field_name: forged_value})


def test_supabase_contract_public_digest_rejects_forged_status_reason_action() -> None:
    report = build_probability_event_screen_supabase_contract_report(
        ProbabilityEventScreenSupabaseContractInput(
            table_contract_ready=True,
            required_columns_present=True,
            jsonb_payload_ready=True,
            redacted_payload_ready=True,
            local_dsn_validated=True,
            remote_host_blocked=True,
            migration_revision_current=True,
        ),
    )
    payload = report.public_payload

    forged_reason_codes = tuple(
        "local_dsn_not_validated" if reason_code == "local_dsn_validated" else reason_code
        for reason_code in payload["reason_codes"]
    )
    for forged in (
        {**payload, "persistence_ready": False},
        {**payload, "reason_codes": forged_reason_codes},
        {**payload, "local_dsn_validated": False},
    ):
        with pytest.raises(ValueError, match="digest"):
            validate_probability_event_screen_supabase_contract_public_payload(forged)


def test_cost_adjusted_position_payload_digest_rejects_forged_status_reason_action() -> None:
    report = build_probability_event_cost_adjusted_position_recommendation_report(
        ProbabilityEventCostAdjustedPositionRecommendationInput(
            event_id="event-001",
            market_slug="fomc-july-2026",
            outcome_side="yes",
            forecast_probability=d("0.620000"),
            market_probability=d("0.540000"),
            taker_fee_probability=d("0.010000"),
            spread_probability=d("0.012000"),
            slippage_probability=d("0.003000"),
            settlement_delay_days=d("37.000000"),
            annual_capital_charge_probability=d("0.100000"),
            uncertainty_buffer_probability=d("0.020000"),
            manual_fraction_cap_probability=d("0.050000"),
        ),
    )
    payload = probability_event_cost_adjusted_position_recommendation_report_payload(report)

    for field_name, forged_value in (
        ("readiness_status", "pass"),
        ("reason_codes", ("cost_adjusted_expected_value_positive",)),
        ("manual_next_step", "document_phase1_readonly_position_boundary"),
    ):
        forged_report = build_probability_event_cost_adjusted_position_recommendation_report(
            ProbabilityEventCostAdjustedPositionRecommendationInput(
                event_id="event-001",
                market_slug="fomc-july-2026",
                outcome_side="yes",
                forecast_probability=d("0.620000"),
                market_probability=d("0.540000"),
                taker_fee_probability=d("0.010000"),
                spread_probability=d("0.012000"),
                slippage_probability=d("0.003000"),
                settlement_delay_days=d("37.000000"),
                annual_capital_charge_probability=d("0.100000"),
                uncertainty_buffer_probability=d("0.020000"),
                manual_fraction_cap_probability=d("0.050000"),
            ),
        )
        object.__setattr__(forged_report, field_name, forged_value)
        object.__setattr__(forged_report, "payload_digest", payload["payload_digest"])
        with pytest.raises(ValueError, match=f"{field_name}|payload_digest"):
            probability_event_cost_adjusted_position_recommendation_report_payload(
                forged_report,
            )


def test_fee_adjusted_position_derived_digest_rejects_forged_status_reason_action() -> None:
    config = StrategyFeeAdjustedPositionSizingGateV2Config(
        config_version="strategy-fee-adjusted-position-sizing-gate-v2",
        portfolio_nav_usdc=d("1000.000000"),
        max_allocation_fraction_of_nav=d("0.100000"),
        edge_allocation_unit=d("0.100000"),
        min_cost_adjusted_edge=d("0.010000"),
        min_confidence_score=d("0.500000"),
        max_liquidity_take_share=d("0.250000"),
        max_depth_take_share=d("0.250000"),
        max_category_exposure_share=d("0.300000"),
        max_settlement_lockup_share=d("0.200000"),
        settlement_delay_penalty_rate=d("0.002000"),
        settlement_lockup_days_weight=d("0.100000"),
        min_position_size_usdc=d("5.000000"),
    )
    candidate = StrategyFeeAdjustedPositionSizingGateV2Candidate(
        candidate_id="candidate-alpha",
        market_slug="market-alpha",
        category="elections-category",
        question="Will alpha happen?",
        outcome="yes",
        observed_at=OBSERVED_AT,
        forecast_probability=d("0.700000"),
        market_probability=d("0.600000"),
        taker_fee_rate=d("0.020000"),
        spread_probability=d("0.010000"),
        expected_slippage_probability=d("0.003000"),
        available_liquidity_usdc=d("300.000000"),
        available_depth_shares=d("400.000000"),
        confidence_score=d("0.800000"),
        current_category_exposure_usdc=d("250.000000"),
        settlement_delay_days=d("2.000000"),
        reason_codes=("seed",),
    )
    report = build_strategy_fee_adjusted_position_sizing_gate_v2_report(
        (candidate,),
        config=config,
        generated_at=GENERATED_AT,
    )
    row = report.rows[0]
    for field_name, forged_value in (
        ("gate_status", "blocked"),
        ("risk_label", "high_sizing_risk"),
        ("reason_codes", ("edge_not_positive_after_costs",)),
    ):
        with pytest.raises(ValueError, match="derived_validation_digest"):
            replace(row, **{field_name: forged_value})
