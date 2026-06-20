import ast
from pathlib import Path

import polymarket_alpha_lab.action_gated_strategy_recommendation_queue as module


EXPECTED_EXPORTS = (
    "PaperActionGatedStrategyRecommendationQueueConfig",
    "PaperActionGatedStrategyRecommendationQueueReport",
    "build_paper_action_gated_strategy_recommendation_queue_report",
)

ALLOWED_IMPORTS = {
    "__future__": {"annotations"},
    "collections.abc": {"Iterable"},
    "dataclasses": {"dataclass"},
    "datetime": {"UTC", "datetime"},
    "decimal": {"Decimal"},
    "typing": {"Any"},
    "polymarket_alpha_lab.candidate_assessment": {
        "PaperCandidateAssessmentConfig",
        "PaperCandidateAssessmentReport",
        "build_paper_candidate_assessment_report",
    },
    "polymarket_alpha_lab.paper_recommendation_cycle_action_gate": {
        "PaperRecommendationCycleActionGateReasonCodeCount",
        "PaperRecommendationCycleActionGateReport",
    },
    "polymarket_alpha_lab.project_screening": {
        "PaperProjectScreeningReport",
    },
    "polymarket_alpha_lab.strategy_readiness_state": {
        "PaperStrategyReadinessSignal",
        "PaperStrategyReadinessStateReport",
        "build_paper_strategy_readiness_state_report",
    },
    "polymarket_alpha_lab.strategy_recommendation_bundle": {
        "PaperStrategyRecommendationBundleConfig",
        "PaperStrategyRecommendationBundleReport",
        "build_paper_strategy_recommendation_bundle_report",
    },
    "polymarket_alpha_lab.strategy_recommendation_queue": {
        "PaperStrategyRecommendationQueueSummaryReport",
        "build_paper_strategy_recommendation_queue_summary_report",
    },
}


FORBIDDEN_TOKENS = (
    "py_clob_client",
    "ClobClient",
    "private_key",
    "api_key",
    "wallet",
    "allowance",
    "balance",
    "place_order",
    "submit_order",
    "cancel_order",
    "sign",
    "live",
    "requests.",
    "httpx.",
    "sqlalchemy",
    "psycopg",
    "supabase",
)


def test_action_gated_strategy_recommendation_queue_has_no_forbidden_surfaces():
    source = Path(module.__file__).read_text(encoding="utf-8")

    assert not any(token in source for token in FORBIDDEN_TOKENS)


def test_action_gated_strategy_recommendation_queue_exports_module_local_api():
    assert module.__all__ == EXPECTED_EXPORTS


def test_action_gated_strategy_recommendation_queue_imports_are_allowlisted():
    tree = ast.parse(Path(module.__file__).read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                assert alias.name in ALLOWED_IMPORTS, alias.name
                assert ALLOWED_IMPORTS[alias.name] is None
        elif isinstance(node, ast.ImportFrom):
            imported_module = node.module or ""
            assert node.level == 0
            assert imported_module in ALLOWED_IMPORTS, imported_module
            allowed_names = ALLOWED_IMPORTS[imported_module]
            assert allowed_names is not None
            for alias in node.names:
                assert alias.name in allowed_names, (imported_module, alias.name)
