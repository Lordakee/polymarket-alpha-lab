from __future__ import annotations

import ast
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]
PHASE_2_MODULE_PATHS = tuple(
    sorted((REPO_ROOT / "src" / "polymarket_alpha_lab").glob("phase_2*.py")),
)

FORBIDDEN_RECOMMENDATION_IMPORT_PREFIXES = (
    "polymarket_alpha_lab.paper_strategy_selection_policy",
    "polymarket_alpha_lab.strategy_candidate_recommendation",
    "polymarket_alpha_lab.strategy_signal_adapter",
    "polymarket_alpha_lab.strategy_recommendation_bundle",
    "polymarket_alpha_lab.strategy_recommendation_explain",
    "polymarket_alpha_lab.strategy_recommendation_history",
    "polymarket_alpha_lab.strategy_recommendation_log",
)

FORBIDDEN_PACKAGE_ROOT_RECOMMENDATION_EXPORTS = (
    "PaperStrategyRecommendationBundleConfig",
    "PaperStrategyRecommendationBundleReport",
    "append_paper_strategy_recommendation_bundle_log",
    "build_paper_strategy_readiness_signals",
    "build_paper_strategy_recommendation_bundle_report",
    "read_paper_strategy_recommendation_bundle_log",
    "signals_from_calibration_gate_report",
    "signals_from_cost_health_gate_report",
    "signals_from_exposure_gate_report",
    "signals_from_liquidity_gate_report",
    "signals_from_market_context_freshness_report",
    "signals_from_settlement_freshness_gate_report",
)


def _module_name(module_path: Path) -> str:
    relative_path = module_path.relative_to(REPO_ROOT / "src").with_suffix("")
    return ".".join(relative_path.parts)


def _parse_module(module_path: Path) -> ast.AST:
    return ast.parse(module_path.read_text(encoding="utf-8"))


def _module_matches_prefix(module_name: str, prefix: str) -> bool:
    return module_name == prefix or module_name.startswith(f"{prefix}.")


def _absolute_import_from_module(imported_from: ast.ImportFrom) -> str:
    if imported_from.level == 0:
        return imported_from.module or ""
    assert imported_from.level == 1, ast.unparse(imported_from)
    if imported_from.module is None:
        return "polymarket_alpha_lab"
    return f"polymarket_alpha_lab.{imported_from.module}"


def assert_phase_2_tree_has_no_recommendation_imports(tree: ast.AST) -> None:
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                assert not any(
                    _module_matches_prefix(alias.name, forbidden)
                    for forbidden in FORBIDDEN_RECOMMENDATION_IMPORT_PREFIXES
                ), alias.name
        elif isinstance(node, ast.ImportFrom):
            imported_module = _absolute_import_from_module(node)
            assert not any(
                _module_matches_prefix(imported_module, forbidden)
                for forbidden in FORBIDDEN_RECOMMENDATION_IMPORT_PREFIXES
            ), imported_module
            if imported_module == "polymarket_alpha_lab":
                for alias in node.names:
                    assert alias.name not in FORBIDDEN_PACKAGE_ROOT_RECOMMENDATION_EXPORTS, (
                        imported_module,
                        alias.name,
                    )


def test_phase_2_modules_exist_for_recommendation_boundary_regression() -> None:
    assert PHASE_2_MODULE_PATHS


def test_phase_2_boundary_blocks_current_recommendation_modules() -> None:
    assert set(FORBIDDEN_RECOMMENDATION_IMPORT_PREFIXES) == {
        "polymarket_alpha_lab.paper_strategy_selection_policy",
        "polymarket_alpha_lab.strategy_candidate_recommendation",
        "polymarket_alpha_lab.strategy_signal_adapter",
        "polymarket_alpha_lab.strategy_recommendation_bundle",
        "polymarket_alpha_lab.strategy_recommendation_explain",
        "polymarket_alpha_lab.strategy_recommendation_history",
        "polymarket_alpha_lab.strategy_recommendation_log",
    }


@pytest.mark.parametrize(
    "module_path",
    PHASE_2_MODULE_PATHS,
    ids=_module_name,
)
def test_phase_2_modules_do_not_import_recommendation_layer(
    module_path: Path,
) -> None:
    assert_phase_2_tree_has_no_recommendation_imports(_parse_module(module_path))


@pytest.mark.parametrize(
    "bad_source",
    (
        pytest.param(
            "from polymarket_alpha_lab.strategy_candidate_recommendation import "
            "PaperStrategyCandidateRecommendationReport\n",
            id="candidate-recommendation-import",
        ),
        pytest.param(
            "import polymarket_alpha_lab.strategy_recommendation_bundle\n",
            id="bundle-module-import",
        ),
        pytest.param(
            "from polymarket_alpha_lab.strategy_recommendation_log import "
            "read_paper_strategy_recommendation_bundle_log\n",
            id="recommendation-log-import",
        ),
        pytest.param(
            "from polymarket_alpha_lab import "
            "build_paper_strategy_recommendation_bundle_report\n",
            id="package-root-recommendation-export-import",
        ),
    ),
)
def test_phase_2_recommendation_boundary_guard_rejects_recommendation_imports(
    bad_source: str,
) -> None:
    with pytest.raises(AssertionError):
        assert_phase_2_tree_has_no_recommendation_imports(ast.parse(bad_source))
