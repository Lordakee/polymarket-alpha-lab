from __future__ import annotations

import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
PHASE1_MODULE_INDEX_PATH = REPO_ROOT / "docs/index/phase1-module-index.md"

EXPECTED_CHANGED_MODULE_TEST_PAIRS = (
    ("category_playbook_category_threshold_domain_policy_readiness", "test_category_playbook_category_threshold_domain_policy_readiness"),
    ("cli", "test_cli_report_discovery"),
    ("crypto_btc_forecast_service", "test_crypto_btc_forecast_service"),
    ("forecast_context_readiness_report", "test_forecast_context_readiness_report"),
    ("information_freshness_refresh_sla_readiness_report", "test_information_freshness_refresh_sla_readiness_report"),
    ("input_failure_degradation_readiness_report", "test_input_failure_degradation_readiness_report"),
    ("manual_operator_decision_packet", "test_manual_operator_decision_packet"),
    ("market_discovery_candidate_pool", "test_market_discovery_candidate_pool"),
    ("operator_final_go_no_go_packet_readiness_report", "test_operator_final_go_no_go_packet_readiness_report"),
    ("outcome_resolution_evidence_readiness_report", "test_outcome_resolution_evidence_readiness_report"),
    ("portfolio_probability_event_readiness_report", "test_portfolio_probability_event_readiness_report"),
    ("post_settlement_calibration_experience_feedback_report", "test_post_settlement_calibration_experience_feedback_report"),
    ("probability_event_cost_adjusted_position_recommendation_report", "test_probability_event_cost_adjusted_position_recommendation_report"),
    ("probability_event_market_signal_risk_readiness_report", "test_probability_event_market_signal_risk_readiness_report"),
    ("probability_event_recommendation_rank_explainability_report", "test_probability_event_recommendation_rank_explainability_report"),
    ("report_discovery", "test_cli_report_discovery"),
    ("source_scraping_tool_coverage_readiness_report", "test_source_scraping_tool_coverage_readiness_report"),
    ("specialist_team_routing_taxonomy_readiness_report", "test_specialist_team_routing_taxonomy_readiness_report"),
    ("strategy_phase1_readiness_aggregator", "test_strategy_phase1_readiness_aggregator"),
    ("supabase_local_dsn", "test_supabase_local_dsn"),
    ("team_evaluation_attempt_latest_read", "test_team_evaluation_attempt_latest_read"),
)
EXPECTED_CHANGED_MODULE_TEST_PATHS = frozenset(
    (
        Path(f"src/polymarket_alpha_lab/{module_name}.py"),
        Path(f"tests/{test_name}.py"),
    )
    for module_name, test_name in EXPECTED_CHANGED_MODULE_TEST_PAIRS
)

MODULE_TEST_ROW_PATTERN = re.compile(
    r"^\|\s*`(?P<module>src/polymarket_alpha_lab/[^`]+\.py)`\s*"
    r"\|\s*`(?P<test>tests/[^`]+\.py)`\s*\|",
    re.MULTILINE,
)


def _listed_module_and_test_paths(index_text: str) -> tuple[tuple[Path, Path], ...]:
    return tuple(
        (Path(match.group("module")), Path(match.group("test")))
        for match in MODULE_TEST_ROW_PATTERN.finditer(index_text)
    )


def test_phase1_module_index_lists_existing_modules_and_tests() -> None:
    assert PHASE1_MODULE_INDEX_PATH.is_file()

    listed_pairs = _listed_module_and_test_paths(
        PHASE1_MODULE_INDEX_PATH.read_text(encoding="utf-8"),
    )
    assert listed_pairs, "Phase 1 module index must list module/test rows"

    missing_paths = tuple(
        path
        for pair in listed_pairs
        for path in pair
        if not (REPO_ROOT / path).is_file()
    )

    assert missing_paths == (), (
        "Phase 1 module index lists paths that do not exist:\n"
        + "\n".join(f"- {path}" for path in missing_paths)
    )


def test_phase1_module_index_covers_every_changed_module_and_direct_test() -> None:
    assert len(EXPECTED_CHANGED_MODULE_TEST_PATHS) == 21
    listed_pairs = frozenset(
        _listed_module_and_test_paths(PHASE1_MODULE_INDEX_PATH.read_text(encoding="utf-8")),
    )

    missing_pairs = EXPECTED_CHANGED_MODULE_TEST_PATHS - listed_pairs
    assert missing_pairs == frozenset(), (
        "Phase 1 module index omits changed module/test rows:\n"
        + "\n".join(f"- {module} -> {test}" for module, test in sorted(missing_pairs))
    )
